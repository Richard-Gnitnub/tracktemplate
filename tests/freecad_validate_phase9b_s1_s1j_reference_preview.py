"""Prove one private S1/S1J snapshot and atomic recovery on a copied C10.

Run in an empty qualified host. Reuse the retained full-state comparator
and image helper without repeating their unchanged mutation controls.
Private inputs and images remain local evidence, with no production,
physical-fit, persistence, rights or Phase 9B acceptance.
"""

import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import time
import traceback
from unittest.mock import patch

import FreeCAD as App

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_reference_preview as adapter,
)
from tracktemplate.application.chair_model_research import (  # noqa: E402
    prepare_chair_model_research,
    prepare_chair_s1j_model_research,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_reference_preview as binding,
)


SENTINEL = "Phase 9B combined S1/S1J preview FreeCAD validation passed"
LAYER_NAMES = (
    "ReferenceRails", "ReferenceTimbers",
    "S1BasePlinth", "S1RailSeat", "S1CentralKey", "S1OuterJaw", "S1InnerJaw",
    "S1JBasePlinth", "S1JRailSeat", "S1JCentralKey",
    "S1JOuterJaw", "S1JInnerJaw",
)


def _helpers():
    """Load existing proof helpers without triggering that proof."""
    spec = importlib.util.spec_from_file_location(
        "_combined_preview_helpers",
        ROOT / "tests/freecad_validate_phase9b_s1_reference_preview.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


helpers = _helpers()


def _settle(document):
    """Finish pending redraws before guarding complete native GUI state."""
    if App.GuiUp:
        from PySide import QtWidgets

        Gui.getDocument(document.Name).activeView().redraw()
        for _iteration in range(5):
            Gui.updateGui()
            QtWidgets.QApplication.processEvents()


def _foreign_state(document):
    """Keep complete native and GUI content of the unrelated witness."""
    result = {
        "name": document.Name, "label": document.Label,
        "filename": document.FileName,
        "undo": document.UndoCount, "redo": document.RedoCount,
        "objects": tuple((obj.Name, obj.TypeId) for obj in document.Objects),
        "content": tuple((obj.Name, helpers._archive_state(
            obj.dumpContent(),
        )) for obj in document.Objects),
    }
    if App.GuiUp:
        result.update({
            "gui_modified": Gui.getDocument(document.Name).Modified,
            "camera": Gui.getDocument(document.Name).activeView().getCamera(),
            "views": tuple((obj.Name, helpers._archive_state(
                obj.ViewObject.dumpContent(),
            )) for obj in document.Objects),
        })
    return result


def _assert_placements(measured, placements):
    """Compare every stable identity and full-precision source frame."""
    assert len(measured) == len(placements)
    for observed, expected in zip(measured, placements):
        assert observed["position_id"] == expected.position_id
        assert observed["rail_id"] == expected.rail_id
        assert observed["timber_id"] == expected.timber_id
        assert tuple(observed["origin_mm"]) == expected.origin_mm
        assert tuple(observed["x_axis"]) == expected.x_axis
        assert tuple(observed["y_axis"]) == expected.y_axis
        assert len(observed["components"]) == 5


def _assert_result(result, document, models, placements, contexts):
    """Check the partition, identities, signatures and twelve layers."""
    assert App.ActiveDocument is document
    assert not document.FileName and document.Temporary is False
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["placement_count"] == 41 and result["layer_count"] == 12
    assert tuple(item["name"] for item in result["layers"]) == LAYER_NAMES
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["key_placement"] == "central-reference-only"
    assert result["length_unit"] == "mm"
    assert result["length_basis"] == "model"
    assert tuple(item["family"] for item in result["families"]) == (
        "S1", "S1J",
    )
    selected_ids = set()
    for family, model, family_placements, measured in zip(
        ("S1", "S1J"), models, placements, result["families"],
    ):
        assert measured["package_signature"] == model.package.content_signature
        assert measured["manifest_signature"] == model.manifest_signature
        assert measured["request_signature"] == model.request_signature
        assert measured["placement_count"] == len(family_placements)
        _assert_placements(measured["placements"], family_placements)
        identities = {item.position_id for item in family_placements}
        assert selected_ids.isdisjoint(identities)
        selected_ids.update(identities)
        layers = [obj for obj in document.Objects
                  if obj.Name.startswith(family) and (
                      family == "S1J" or not obj.Name.startswith("S1J")
                  )]
        assert len(layers) == 5
        assert all(len(obj.Shape.Solids) == len(family_placements)
                   for obj in layers)
    assert len(placements[0]) == 37 and len(placements[1]) == 4
    assert all(obj.TypeId == "Part::Feature" for obj in document.Objects)
    assert all("GeneratedBy" not in obj.PropertiesList
               for obj in document.Objects)
    assert all(not obj.Shape.Faces and not obj.Shape.Solids
               for obj in document.Objects[:2])
    source = result["source_receipt"]
    assert len(contexts) == 2 and contexts[0][0] == contexts[1][0]
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        contexts[0][0].encode("utf-8"),
    ).hexdigest()
    assert source["source_analysis_signature"] == contexts[0][1][
        "geometry_signature"
    ]
    for field, expected in (
        ("analysis_position_count", 168), ("selected_s1_count", 37),
        ("confirmed_s1_count", 54), ("unresolved_confirmed_s1_count", 17),
        ("selected_s1j_count", 4), ("confirmed_s1j_count", 5),
        ("unresolved_confirmed_s1j_count", 1), ("selected_count", 41),
        ("confirmed_count", 59), ("unresolved_confirmed_count", 18),
    ):
        assert source[field] == expected, (field, source[field])
    excluded = source["excluded_positions"]
    excluded_ids = [item["position_id"] for item in excluded]
    assert len(excluded_ids) == len(set(excluded_ids)) == 127
    assert excluded_ids == sorted(excluded_ids)
    assert selected_ids.isdisjoint(excluded_ids)
    assert selected_ids | set(excluded_ids) == {
        item["stable_chair_position_identity"]
        for item in contexts[0][1]["positions"]
    }
    analytical = {item["chair_position_identity"]: item["reason"]
                  for item in contexts[0][3]["analytical_only"]}
    for item in excluded:
        if item["position_id"] in analytical:
            assert item["reason"] == analytical[item["position_id"]]
    for label in ("41/59", "18 unresolved", "37/54 S1", "4/5 S1J"):
        assert label in document.Label, document.Label


def validate():
    """Retain native and GUI proof of the combined command, including FAIL."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_COMBINED_PREVIEW_RUN_DIR",
        ROOT / "benchmark-output" / "combined-reference-preview" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp),
               "families": ["S1", "S1J"],
               "reused_helper_sha256": hashlib.sha256(
                   Path(helpers.__file__).read_bytes(),
               ).hexdigest()}
    try:
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        module = session.module
        command = session.preview_s1_s1j_reference_chairs
        receipt["profile"] = launcher["FOUNDATION_RESULT"][
            "matched_profile_id"
        ]
        receipt["routing"] = routing
        source = helpers.continuity._prepare_case(module, run_dir, "turnout")
        foreign = App.newDocument("UnrelatedCombinedWitness")
        keep = foreign.addObject("App::FeaturePython", "Keep")
        keep.Label = "Keep this unrelated document"
        foreign.recompute()
        _settle(foreign)
        App.setActiveDocument(source.Name)
        if App.GuiUp:
            Gui.getMainWindow().resize(1600, 1000)
            Gui.Selection.addSelection(source.Objects[0])
        _settle(source)
        gui = Gui if App.GuiUp else None
        selection = adapter._selection_snapshot(App, gui)
        preselection = adapter._preselection_snapshot(App, gui)
        original = helpers._state(module, source)
        original_foreign = _foreign_state(foreign)
        receipt["source_before"] = original
        receipt["foreign_before"] = original_foreign
        source_objects = {obj.Name: obj for obj in source.Objects}
        source_shapes = {obj.Name: obj.Shape for obj in source.Objects
                         if "Shape" in obj.PropertiesList}
        registry = dict(App.listDocuments())

        def unchanged(stage, *, check_selection=True):
            receipt["state_check_stage"] = stage
            receipt["source_after"] = helpers._state(module, source)
            receipt["foreign_after"] = _foreign_state(foreign)
            assert receipt["source_after"] == original, stage
            assert receipt["foreign_after"] == original_foreign, stage
            assert App.getDocument(foreign.Name) is foreign
            assert foreign.getObject(keep.Name) is keep
            for name, obj in source_objects.items():
                assert source.getObject(name) is obj, (stage, name)
            for name, shape in source_shapes.items():
                assert source.getObject(name).Shape.isSame(shape), (
                    stage, name,
                )
            if check_selection:
                assert adapter._selection_snapshot(App, gui) == selection
                assert adapter._preselection_snapshot(App, gui) == preselection

        packages = (helpers._inputs("S1"), helpers._inputs("S1J"))
        models = (
            prepare_chair_model_research(*packages[0], helpers.REQUEST),
            prepare_chair_s1j_model_research(*packages[1], helpers.REQUEST),
        )
        _signature, analysis, _settings, plan = binding._source_context(
            module, source, "TO-001", "S1/S1J",
        )
        placements = (
            binding._select_positions(module, analysis, plan)[0],
            binding._select_s1j_positions(module, analysis, plan)[0],
        )
        arguments = (source, "TO-001", *packages[0], *packages[1],
                     helpers.REQUEST)
        contexts = []
        read_context = binding._source_context

        def observe_context(*args, **kwargs):
            current = read_context(*args, **kwargs)
            contexts.append(current)
            return current

        started = time.perf_counter()
        with patch.object(binding, "_source_context", observe_context):
            result = command(*arguments)
        receipt["construction_seconds"] = time.perf_counter() - started
        receipt["preview"] = result
        preview = App.getDocument(result["document_name"])
        _assert_result(result, preview, models, placements, contexts)
        assert App.listDocuments() == dict(registry, **{preview.Name: preview})
        unchanged("successful combined creation")
        receipt["common_context"] = {
            "observations": len(contexts), "identical": True,
            "signature": result["source_receipt"]["source_context_signature"],
        }
        before_shapes = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert tuple(obj.Name for obj in preview.Objects) == LAYER_NAMES
        assert all(obj.Shape.isSame(shape) for obj, shape in zip(
            preview.Objects, before_shapes,
        ))
        unchanged("one combined undo and redo")
        receipt["undo_redo"] = "PASS"
        if App.GuiUp:
            receipt["images"] = {}
            for family, family_placements in zip(("S1", "S1J"), placements):
                image_dir = run_dir / family.lower()
                image_dir.mkdir()
                receipt["images"][family] = [
                    str(Path(family.lower()) / name)
                    for name in helpers._images(
                        preview, family_placements, image_dir,
                    )
                ]
            unchanged("combined viewport captures", check_selection=False)
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        adapter._restore_selection(App, gui, selection)
        adapter._restore_preselection(App, gui, preselection)
        unchanged("combined document close")

        create = adapter.create_s1_s1j_reference_preview
        roles = module._turnout_objects_by_role(source, "TO-001")
        context_shapes = tuple(roles[role].Shape.copy() for role in (
            module.TURNOUT_RAIL_ROLE, module.TURNOUT_TIMBER_ROLE,
        ))
        receipt["before_document_rejections"] = {}
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid second-family preparation created a document",
        )):
            try:
                command(source, "TO-001", *packages[0], *packages[0],
                        helpers.REQUEST)
            except ValueError as error:
                receipt["before_document_rejections"]["package"] = str(error)
            else:
                raise AssertionError("S1 package accepted for S1J")
            try:
                create(*packages[0], *packages[1], helpers.REQUEST,
                       placements[0], placements[0], context_shapes,
                       result["source_receipt"], lambda: None)
            except TypeError as error:
                assert "S1JPlacement" in str(error), str(error)
                receipt["before_document_rejections"]["placement"] = str(error)
            else:
                raise AssertionError("S1 placements accepted for S1J")

            build_layers = adapter._build_layers
            prepared = []

            def fail_second_geometry(*args):
                prepared.append(args[0].package.content_signature)
                if len(prepared) == 2:
                    raise RuntimeError("Second-family preparation witness")
                return build_layers(*args)

            with patch.object(adapter, "_build_layers", fail_second_geometry):
                receipt["before_document_rejections"]["geometry"] = (
                    helpers._reject(lambda: command(*arguments),
                                    "Second-family preparation witness")
                )
            assert prepared == [model.package.content_signature
                                for model in models]
        assert App.listDocuments() == registry
        assert App.ActiveDocument is source
        unchanged("second-family preparation failures")

        original_top = module._chair_physical_top_z

        def stale_during_build(*args):
            def changed_source():
                pending = App.ActiveDocument
                assert pending is not source and pending is not foreign
                assert tuple(obj.Name for obj in pending.Objects) == (
                    LAYER_NAMES
                )
                receipt["rollback_owned_document"] = pending.Name
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *values: original_top(*values) + 1e-8,
                ):
                    args[-1]()

            return create(*args[:-1], changed_source)

        with patch.object(session, "_s1_s1j_reference_preview_factory",
                          side_effect=stale_during_build):
            receipt["subprecision_rejection"] = helpers._reject(
                lambda: command(*arguments), "source changed",
            )
        assert App.listDocuments() == registry
        assert App.ActiveDocument is source
        unchanged("late changed-source rollback")
        receipt["transaction_failure_cleanup"] = "PASS"

        receipt["analysis_rejections"] = {}
        for case in ("missing", "stale"):
            target = run_dir / (case + ".FCStd")
            shutil.copy2(source.FileName, target)
            negative = App.openDocument(str(target))
            if case == "missing":
                settings_object = module._chair_settings_object(
                    negative, "turnout", "TO-001",
                )
                setattr(settings_object, module.CHAIR_ANALYSIS_RESULT_PROPERTY,
                        "")
            else:
                module.invalidate_chair_analysis(
                    negative, "turnout", "TO-001", remove_display=True,
                )
            before_documents = App.listDocuments()
            try:
                command(negative, "TO-001", *packages[0], *packages[1],
                        helpers.REQUEST)
            except ValueError as error:
                receipt["analysis_rejections"][case] = str(error)
            else:
                raise AssertionError("Invalid analysis accepted: " + case)
            assert App.listDocuments() == before_documents
            App.closeDocument(negative.Name)
        App.setActiveDocument(source.Name)
        adapter._restore_selection(App, gui, selection)
        adapter._restore_preselection(App, gui, preselection)
        assert App.listDocuments() == registry
        unchanged("missing and stale analysis rejection")
        receipt["source_unchanged"] = True
        receipt["foreign_unchanged"] = True
        receipt["status"] = "PASS"
    except BaseException:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        (run_dir / "result.json").write_text(
            json.dumps(receipt, allow_nan=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
    print(SENTINEL)
    return receipt


if __name__ in {
    "__main__", "freecad_validate_phase9b_s1_s1j_reference_preview",
}:
    validate()
