"""Prove retained P placement on a copied C10 crossover.

Reuse native component comparisons and source-state witnesses from the
accepted P and crossover proofs. Keep the source, exclusions and geometry
unchanged. This proof supplies no fit or production acceptance.
"""

from collections import Counter
import datetime
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import sys
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def _load_helper(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


p = _load_helper(
    "_crossover_p_components", "freecad_validate_phase9b_catalogue_p_placement.py",
)
xo = _load_helper(
    "_crossover_p_source", "freecad_validate_phase9b_crossover_reference_preview.py",
)
adapter = p.adapter
lifecycle = p.lifecycle
catalogue = p.catalogue
combined = p.combined
helpers = p.helpers
SENTINEL = "Phase 9B catalogue P crossover FreeCAD validation passed"


def _context(module, document):
    return p.existing_binding._source_context(
        module, document, "XO-001", "P", entity_kind="crossover",
    )


def _expected_frames(module, context):
    """Evaluate both constituent frames from independent rail sections."""
    _signature, analysis, _settings, plan, rails, _timbers = context
    positions = sorted(
        (item for item in analysis["positions"]
         if type(item["chair_code"]) is int and item["chair_code"] == 2),
        key=lambda item: item["stable_chair_position_identity"],
    )
    assert len(analysis["positions"]) == 355 and len(positions) == 28
    assert Counter(item["parent_turnout_identity"] for item in positions) == {
        "XO-001-A001": 14, "XO-001-B001": 14,
    }
    datums = {item["base_z"] for item in plan["instances"]}
    assert datums == {0.8}
    rail_map = {item["stable_identity"]: item for item in rails}
    frames = []
    for item in positions:
        assert item["assignment_status"] == module.CHAIR_ASSIGNMENT_CONFIRMED
        assert item["assignment_complete_in_current_stage"]
        assert not item["deliberate_omission"]
        assert not item["special_assignment_deferred"]
        assert item["parent_crossover_identity"] == "XO-001"
        assert item["key_direction_sign"] == 0
        centre, tangent = item["centre_point"], item["local_rail_tangent"]
        rail = rail_map[item["rail_identity"]]
        assert rail["parent_turnout_identity"] == item["parent_turnout_identity"]
        sides = []
        for face in ("gauge_face_points", "outer_face_points"):
            _index, _fraction, point = helpers._face_crossing(
                centre, tangent, rail[face],
            )
            sides.append(
                -Fraction(tangent[1]) * (point[0] - Fraction(centre[0]))
                + Fraction(tangent[0]) * (point[1] - Fraction(centre[1]))
            )
        assert sides[0] * sides[1] < 0
        sign = 1 if sides[0] > 0 else -1
        length = math.hypot(*tangent)
        y_axis = (sign * tangent[1] / length, -sign * tangent[0] / length)
        frames.append(SimpleNamespace(
            position_id=item["stable_chair_position_identity"],
            rail_id=item["rail_identity"], timber_id=item["timber_identity"],
            parent_id=item["parent_turnout_identity"],
            origin_mm=(*centre, next(iter(datums))),
            x_axis=(y_axis[1], -y_axis[0]), y_axis=y_axis,
        ))
    return tuple(frames)


def _legacy_partition(module, context):
    """Keep the existing S1/S1J route's complete current partition."""
    _signature, analysis, _settings, plan, rails, timbers = context
    first, second, excluded = p.existing_binding._select_s1_s1j_positions(
        module, analysis, plan,
    )
    selected = []
    for code, placements in ((1, first), (7, second)):
        placements, excluded, _records = p.existing_binding._recover_positions(
            module, analysis, plan, rails, timbers, placements, excluded, code,
        )
        selected.extend(placements)
    assert len(selected) == 135 and len(excluded) == 220
    return tuple(selected), excluded


def _assert_preview(result, document, reference, frames, context):
    """Compare every retained component at every independent position."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert tuple(obj.Name for obj in document.Objects) == p.LAYER_NAMES
    assert result["component_count"] == 22
    assert result["placement_count"] == 28 and result["layer_count"] == 24
    assert result["solid_count"] == 644
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["scale_denominator"] == "76.2"
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert result["source_model_sha256"] == adapter._P_MODEL_SHA256
    excluded = result["excluded_source_components"]
    assert len(excluded) == 1 and excluded[0]["source_name"] == "display_rail"
    _signature, analysis, _settings, plan, _rails, _timbers = context
    source = result["source_receipt"]
    assert source["crossover_id"] == "XO-001"
    assert source["source_kind"] == "crossover" and "turnout_id" not in source
    assert source["timber_context"] == "current B4 resolved timbers"
    assert source["analysis_position_count"] == 355
    assert source["selected_p_count"] == len(source["selected_positions"]) == 28
    assert len(source["remaining_positions"]) == 327
    assert source["original_analytical_exclusions"] == plan["analytical_only"]
    selected = {item["position_id"] for item in source["selected_positions"]}
    remaining = {item["position_id"] for item in source["remaining_positions"]}
    assert not selected & remaining
    assert selected | remaining == {
        item["stable_chair_position_identity"] for item in analysis["positions"]
    }
    assert selected == {frame.position_id for frame in frames}
    for item in source["selected_positions"]:
        assert item["key_direction_sign"] == 0
        assert item["key_orientation"] == (
            "requires a configurable key-direction policy"
        )
        assert item["original_exclusion"] in plan["analytical_only"]
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        context[0].encode("utf-8"),
    ).hexdigest()
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    for obj in document.Objects[:2]:
        assert not obj.Shape.Solids and not obj.Shape.Faces
    comparisons = []
    for obj, component, name in zip(
        document.Objects[2:], result["components"], p.COMPONENT_NAMES,
    ):
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
        assert component["source_name"] == obj.Name == name
        assert tuple(component["source_identity"]) == (
            result["source_model_sha256"], name,
        )
        children = obj.Shape.childShapes()
        assert len(children) == len(frames)
        comparisons.append({
            "name": name,
            "positions": [p._compare_component(child, reference[name], frame)
                          for child, frame in zip(children, frames)],
        })
    assert len(result["placements"]) == len(frames)
    for actual, frame in zip(result["placements"], frames):
        for field in ("position_id", "rail_id", "timber_id"):
            assert actual[field] == getattr(frame, field)
        for field in ("origin_mm", "x_axis", "y_axis"):
            assert tuple(actual[field]) == getattr(frame, field)
        assert len(actual["components"]) == 22
    assert result["solid_count"] == sum(len(obj.Shape.Solids)
                                        for obj in document.Objects)
    assert all(item["chair_code"] != 2 for item in plan["instances"])
    return comparisons


def _analysis_refusals(module, command, source, fixture, path, run_dir):
    """Use copied negative witnesses before capturing GUI source state."""
    refusals = {}
    for name in ("missing", "stale", "stale-b4"):
        target = run_dir / (name + ".FCStd")
        shutil.copy2(fixture, target)
        negative = App.openDocument(str(target))
        if name == "missing":
            settings = module._chair_settings_object(
                negative, "crossover", "XO-001",
            )
            setattr(settings, module.CHAIR_ANALYSIS_RESULT_PROPERTY, "")
        elif name == "stale":
            module.invalidate_chair_analysis(
                negative, "crossover", "XO-001", remove_display=True,
            )
        else:
            config = module.crossover_config_by_id(negative, "XO-001")
            config["b4_result"]["resolution_signature"] = "invalid-P-witness"
            settings = module._chair_settings_object(
                negative, "crossover", "XO-001",
            )
            setattr(settings, module.CROSSOVER_CONFIGURATION_PROPERTY,
                    json.dumps(config, sort_keys=True))
            module.analyse_entity_chair_positions(
                negative, "crossover", "XO-001",
            )
        registry = dict(App.listDocuments())
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid crossover analysis created a preview",
        )):
            refusals[name] = catalogue._reject(
                lambda: command(negative, "XO-001", path), ValueError,
            )
        if name == "stale-b4":
            assert "Current applied B4" in refusals[name]
        assert App.listDocuments() == registry
        App.closeDocument(negative.Name)
    App.setActiveDocument(source.Name)
    combined._settle(source)
    xo._active(source)
    return refusals


def validate():
    """Keep complete native/GUI receipts with exact source identities."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_CATALOGUE_P_CROSSOVER_RUN_DIR",
        ROOT / "benchmark-output/catalogue-p-crossover" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = catalogue.helpers._document_state()
    try:
        prepared = p.prepare_catalogue_chair(path, "P", run="basic-04")
        case = next(item for item in catalogue._cases(path) if item[0] == "P")
        copies = run_dir / "native-copies"
        copies.mkdir()
        original = catalogue._reference(case, copies)
        reference = {name: shape for name, _label, shape, _matrix in original
                     if name != "display_rail"}
        assert tuple(reference) == p.COMPONENT_NAMES
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == p.PROFILE
        receipt.update(profile=p.PROFILE, routing=routing)
        module = session.module
        command = session.preview_private_catalogue_p_crossover_chairs
        target = run_dir / "XO-001.FCStd"
        shutil.copy2(fixture, target)
        source = App.openDocument(str(target))
        source.UndoMode = 1
        receipt["analysis_refusals"] = _analysis_refusals(
            module, command, source, fixture, path, run_dir,
        )
        foreign = App.newDocument("CataloguePCrossoverUnrelatedWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign.recompute()
        combined._settle(foreign)
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if gui:
            gui.getMainWindow().resize(1600, 1000)
            gui.Selection.addSelection(source.Objects[0])
        combined._settle(source)
        context = _context(module, source)
        frames = _expected_frames(module, context)
        partition = _legacy_partition(module, context)
        # Complete lazy group Shape access and pending redraws first.
        xo._state(module, source)
        combined._settle(source)
        source_state = xo._state(module, source)
        foreign_state = combined._foreign_state(foreign)
        combined._settle(source)
        assert xo._state(module, source) == source_state
        registry = dict(App.listDocuments())
        identities = {(doc.Name, obj.Name): obj for doc in registry.values()
                      for obj in doc.Objects}
        shapes = {key: obj.Shape for key, obj in identities.items()
                  if "Shape" in obj.PropertiesList}
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        receipt.update(source_before=source_state, foreign_before=foreign_state)

        def unchanged(stage, active):
            receipt["last_preservation_stage"] = stage
            assert xo._state(module, source) == source_state, stage
            assert combined._foreign_state(foreign) == foreign_state, stage
            assert App.listDocuments() == dict(
                registry, **({active.Name: active}
                             if active.Name not in registry else {}),
            ), stage
            for name, document in registry.items():
                assert App.getDocument(name) is document, stage
            for (name, obj_name), obj in identities.items():
                assert App.getDocument(name).getObject(obj_name) is obj, stage
            for key, shape in shapes.items():
                assert identities[key].Shape.isSame(shape), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        arguments = (source, "XO-001", path)
        started = time.perf_counter()
        with patch.object(App, "openDocument", side_effect=AssertionError(
            "Product restored an external source document",
        )):
            result = command(*arguments)
        receipt["elapsed_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        receipt["comparisons"] = _assert_preview(
            result, preview, reference, frames, context,
        )
        unchanged("created", preview)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        _assert_preview(result, preview, reference, frames, context)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            for obj in preview.Objects:
                assert obj.ViewObject.Visibility
                gui.Selection.clearSelection()
                gui.Selection.addSelection(obj)
                assert gui.Selection.getSelection() == [obj]
                obj.ViewObject.Visibility = False
                combined._settle(preview)
                assert not obj.ViewObject.Visibility
                obj.ViewObject.Visibility = True
                combined._settle(preview)
                assert obj.ViewObject.Visibility
            gui.Selection.clearSelection()
            receipt["images"] = {}
            view = gui.getDocument(preview.Name).activeView()
            animation = view.isAnimationEnabled()
            try:
                # Capture final camera positions without a pending rotation.
                view.setAnimationEnabled(False)
                assert not view.isAnimationEnabled()
                for label, parent in (
                    ("a", "XO-001-A001"), ("b", "XO-001-B001"),
                ):
                    views = run_dir / "views" / label
                    views.mkdir(parents=True)
                    values = tuple(f for f in frames if f.parent_id == parent)
                    receipt["images"][label] = helpers._images(
                        preview, values, views,
                    )
            finally:
                view.setAnimationEnabled(animation)
            assert view.isAnimationEnabled() == animation
            receipt["camera_animation_restored"] = True
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        combined._settle(source)
        unchanged("test-owned close", source)
        invalid = run_dir / "changed-catalogue.json"
        invalid.write_bytes(path.read_bytes() + b"\n")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid catalogue created a document",
        )):
            receipt["catalogue_refusal"] = catalogue._reject(
                lambda: command(source, "XO-001", invalid), ValueError,
            )
        unchanged("early refusal", source)
        original_top = module._chair_physical_top_z
        create = adapter.create_private_catalogue_p_preview

        def stale_during_build(*args):
            def changed_source():
                assert App.ActiveDocument not in (source, foreign)
                assert len(App.ActiveDocument.Objects) == 24
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *values: original_top(*values) + 1e-8,
                ):
                    args[-1]()
            return create(*args[:-1], changed_source)

        with patch.object(session, "_private_catalogue_p_preview_factory",
                          side_effect=stale_during_build):
            receipt["late_source_refusal"] = helpers._reject(
                lambda: command(*arguments), "source changed",
            )
        unchanged("late source rollback", source)
        original_check = adapter._same_presented_shape

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 24
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            receipt["stored_shape_refusal"] = catalogue._reject(
                lambda: command(*arguments), ValueError,
            )
        unchanged("stored shape rollback", source)
        p.verify_catalogue_sources(prepared)
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert _context(module, source) == context
        assert _legacy_partition(module, context) == partition
        receipt.update(source_after=xo._state(module, source),
                       foreign_after=combined._foreign_state(foreign),
                       source_bindings_unchanged=True,
                       fixture_sha256=xo.FIXTURE_SHA256,
                       transaction_rollback="PASS",
                       legacy_exclusions_unchanged=True)
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        catalogue.helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    assert catalogue.helpers._document_state() == initial
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
