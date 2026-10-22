"""Prove private L1 preview creation and recovery in the qualified host.

Reuse the retained model and complete native/view state helpers. Explicit
private inputs stay local. No placement, fit or production acceptance follows.
"""

import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_reference_preview as adapter,
)
from tracktemplate.application.chair_model_research import (  # noqa: E402
    prepare_chair_l1_model_research,
)


SENTINEL = "Phase 9B L1 reference preview FreeCAD validation passed"
LAYER_NAMES = (
    "L1BasePlinth", "L1RailSeat", "L1CentralKey", "L1OuterJaw", "L1InnerJaw",
)


def _helpers():
    """Reuse existing state guards without executing the old model proof."""
    spec = importlib.util.spec_from_file_location(
        "_l1_reference_model_helpers",
        ROOT / "tests/freecad_validate_phase9b_chair_l1_model.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


helpers = _helpers()


def _assert_preview(result, document, model):
    """Check derived geometry against canonical component identities."""
    assert result["contract_id"] == "tracktemplate.private-l1-reference-preview.v1"
    assert not document.FileName and document.Temporary is False
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["package_signature"] == model.package.content_signature
    assert result["manifest_signature"] == model.manifest_signature
    assert result["request_signature"] == model.request_signature
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["key_placement"] == "central-reference-only"
    assert result["length_unit"] == "mm" and result["length_basis"] == "model"
    assert result["scale_denominator"] == "76.2"
    assert result["placement"] == "same-chair-origin-and-axes-central-key"
    assert (result["component_count"], result["solid_count"],
            result["layer_count"]) == (5, 7, 5)
    assert "placement_count" not in result
    assert tuple(item["name"] for item in result["layers"]) == LAYER_NAMES
    observed = []
    for obj, component in zip(document.Objects, model.components):
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
        assert "Private L1 reference" in obj.Label
        observed.append(adapter._measure_component(
            obj.Shape, component, component.role,
            l1_outer=component.role == "outer-jaw",
        ))
    assert tuple(item["component_id"] for item in observed) == tuple(
        component.component_id for component in model.components
    )
    assert tuple(item["solid_count"] for item in observed) == (1, 1, 1, 3, 1)
    assert tuple(item["piece_id"] for item in observed[3]["pieces"]) == (
        "body", "bevel-negative", "bevel-positive",
    )
    assert "one model at its origin" in document.Label
    return observed


def validate():
    """Keep raw success or failure evidence for this bounded command."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_L1_REFERENCE_PREVIEW_RUN_DIR",
        ROOT / "benchmark-output" / "l1-reference-preview" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = helpers._document_state()
    receipt["active_documents"] = []
    try:
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        receipt["profile"] = launcher["FOUNDATION_RESULT"]["matched_profile_id"]
        assert receipt["profile"] == helpers.PROFILE_ID
        receipt["routing"] = routing
        source = helpers._preview.continuity._prepare_case(
            session.module, run_dir, "turnout",
        )
        foreign = App.newDocument("UnrelatedL1PreviewWitness")
        keep = foreign.addObject("Part::Feature", "Keep")
        keep.Shape = Part.makeBox(2, 3, 4)
        keep.Label = "Keep this unrelated document"
        foreign.recompute()
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if App.GuiUp:
            Gui.getMainWindow().resize(1600, 1000)
            Gui.Selection.addSelection(source.Objects[0])
        helpers._settle()
        # Its first group Shape read changes a child native archive.
        # Complete that observation before guarding all native bytes.
        source_before = helpers._preview._state(session.module, source)
        helpers._settle()
        original = helpers._document_state()
        registry = dict(App.listDocuments())
        identities = {(doc.Name, obj.Name): obj for doc in registry.values()
                      for obj in doc.Objects}
        shapes = {(doc.Name, obj.Name): obj.Shape for doc in registry.values()
                  for obj in doc.Objects if "Shape" in obj.PropertiesList}
        selection = adapter._selection_snapshot(App, gui)
        preselection = adapter._preselection_snapshot(App, gui)
        assert helpers._preview._state(session.module, source) == source_before
        assert helpers._document_state() == original
        receipt["source_before"] = source_before
        receipt["protected_before"] = original

        def unchanged(stage, *, selected=True):
            current = helpers._document_state()
            protected = [item for item in current["documents"]
                         if item["name"] in registry]
            receipt["state_check_stage"] = stage
            receipt["protected_after"] = current
            assert protected == original["documents"], stage
            assert helpers._preview._state(session.module, source) == (
                source_before
            ), stage
            for name, doc in registry.items():
                assert App.getDocument(name) is doc, (stage, name)
            for (name, object_name), obj in identities.items():
                assert App.getDocument(name).getObject(object_name) is obj
            for (name, object_name), shape in shapes.items():
                assert App.getDocument(name).getObject(object_name).Shape.isSame(
                    shape,
                )
            if selected:
                assert adapter._selection_snapshot(App, gui) == selection
                assert adapter._preselection_snapshot(App, gui) == preselection

        _record, _manifest, package, text, input_hashes = helpers._inputs()
        request = copy.deepcopy(helpers.REQUEST)
        model = prepare_chair_l1_model_research(package, text, request)
        command = session.preview_l1_reference_chair
        result = command(package, text, request)
        receipt["preview"] = result
        preview = App.getDocument(result["document_name"])
        receipt["active_documents"].append(dict(
            stage="created", **helpers._active_document_state(preview),
        ))
        receipt["stored_components"] = _assert_preview(result, preview, model)
        assert App.listDocuments() == dict(registry, **{preview.Name: preview})
        unchanged("successful creation")
        original_shapes = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert tuple(obj.Name for obj in preview.Objects) == LAYER_NAMES
        assert all(obj.Shape.isSame(shape) for obj, shape in zip(
            preview.Objects, original_shapes,
        ))
        _assert_preview(result, preview, model)
        receipt["active_documents"].append(dict(
            stage="undo-redo", **helpers._active_document_state(preview),
        ))
        unchanged("undo and redo")
        receipt["undo_redo"] = "PASS"
        if App.GuiUp:
            for obj in preview.Objects:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(obj)
                assert Gui.Selection.getSelection() == [obj]
                obj.ViewObject.Visibility = False
                helpers._settle()
                assert not obj.ViewObject.Visibility
                obj.ViewObject.Visibility = True
                helpers._settle()
                assert obj.ViewObject.Visibility
            Gui.Selection.clearSelection()
            placement = SimpleNamespace(origin_mm=(0, 0, 0), position_id="L1")
            receipt["images"] = helpers._images(preview, [placement], run_dir)
            adapter._restore_selection(App, gui, selection)
            adapter._restore_preselection(App, gui, preselection)
            unchanged("component inspection")
            receipt["visibility_selection"] = "PASS"
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        adapter._restore_selection(App, gui, selection)
        adapter._restore_preselection(App, gui, preselection)
        helpers._settle()
        receipt["active_documents"].append(dict(
            stage="closed", **helpers._active_document_state(source),
        ))
        assert helpers._document_state() == original
        unchanged("preview closed")

        receipt["refusals"] = {}
        bad_request = dict(request, scale_denominator="100")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid preparation created a document",
        )):
            try:
                command(package, text, bad_request)
            except ValueError as error:
                receipt["refusals"]["invalid-request"] = str(error)
            else:
                raise AssertionError("Invalid model request was accepted")
            with patch.object(adapter, "_construct_components",
                              side_effect=RuntimeError("construction witness")):
                receipt["refusals"]["construction"] = helpers._preview._reject(
                    lambda: command(package, text, request),
                    "construction witness",
                )
        unchanged("early refusals")
        assert helpers._document_state() == original
        measure = adapter._measure_component

        def fail_stored(*args, **kwargs):
            if len(App.listDocuments()) > len(registry):
                receipt["rollback_owned_document"] = App.ActiveDocument.Name
                raise RuntimeError("stored geometry witness")
            return measure(*args, **kwargs)

        with patch.object(adapter, "_measure_component", fail_stored):
            receipt["refusals"]["stored-geometry"] = helpers._preview._reject(
                lambda: command(package, text, request),
                "stored geometry witness",
            )
        helpers._settle()
        receipt["active_documents"].append(dict(
            stage="rollback", **helpers._active_document_state(source),
        ))
        assert App.listDocuments() == registry
        assert helpers._document_state() == original
        unchanged("late rollback")

        construct = adapter._construct_components

        def change_request(*args, **kwargs):
            layers = construct(*args, **kwargs)
            request["scale_denominator"] = "100"
            return layers

        try:
            with patch.object(adapter, "_construct_components", change_request):
                try:
                    command(package, text, request)
                except ValueError as error:
                    receipt["refusals"]["late-input-change"] = str(error)
                else:
                    raise AssertionError("Changed input reached commit")
        finally:
            request.clear()
            request.update(helpers.REQUEST)
        helpers._settle()
        assert App.listDocuments() == registry
        assert helpers._document_state() == original
        unchanged("late input change")
        assert request == helpers.REQUEST
        assert prepare_chair_l1_model_research(package, text, request) == model
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
                   for path, digest in input_hashes.items())
        receipt.update(input_sha256=input_hashes, source_unchanged=True,
                       foreign_unchanged=True, transaction_rollback="PASS",
                       production_geometry_authorized=False,
                       track_placements_added=0)
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    try:
        assert helpers._document_state() == initial
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
        raise
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
