"""Prove P placement after canonical GUI radius changes.

Native execution consumes hash-bound GUI-generated fixture copies. GUI
execution uses the actual radius dialog and Generate/Replace, then checks
product-owned XO-001, B4 and analysis recalculation without test repair.
Neither route qualifies whole-preview host admission, fit or production.
"""

from collections import Counter
import copy
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import sys
import traceback
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide6 import QtCore, QtWidgets

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
_spec = importlib.util.spec_from_file_location(
    "_p_curvature_existing_proof",
    ROOT / "tests/freecad_validate_phase9b_catalogue_p_crossover.py",
)
previous = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(previous)
assert previous.ROOT == ROOT
p = previous.p
catalogue = previous.catalogue
lifecycle = previous.lifecycle
combined = previous.combined

from p_curvature_source_oracle import (  # noqa: E402
    assert_recalculated, expected_p_frames, validate_p_frames,
)

SENTINEL = "Phase 9B P curvature recalculation FreeCAD validation passed"
CASES = (("reference-600", 600.0, 355), ("changed-900", 900.0, 354),
         ("returned-600", 600.0, 355))
SOURCE_OPTIONS = (
    "host_a_object", "host_b_object", "reference_chainage", "arrangement",
    "handing", "track_gauge", "flangeway", "minimum_requested_radius",
    "toe_chainage_a", "template_set_id", "shared_timber_settings",
    "b3_settings", "b4_settings", "chair_analysis_settings",
)


def _write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _digest(value):
    encoded = json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _frames(module, context, count):
    """Give the oracle identities, never analysis coordinates or angles."""
    _signature, analysis, _settings, plan, rails, timbers = context
    assert len(analysis["positions"]) == count
    selected = [
        item for item in analysis["positions"]
        if type(item["chair_code"]) is int and item["chair_code"] == 2
    ]
    assert len(selected) == 28
    assert Counter(item["parent_turnout_identity"] for item in selected) == {
        "XO-001-A001": 14, "XO-001-B001": 14,
    }
    bindings = []
    for item in selected:
        assert item["assignment_status"] == module.CHAIR_ASSIGNMENT_CONFIRMED
        assert item["assignment_complete_in_current_stage"]
        assert not item["deliberate_omission"]
        assert not item["special_assignment_deferred"]
        assert item["parent_crossover_identity"] == "XO-001"
        assert item["key_direction_sign"] == 0
        bindings.append({
            "position_id": item["stable_chair_position_identity"],
            "rail_id": item["rail_identity"],
            "timber_id": item["timber_identity"],
            "parent_id": item["parent_turnout_identity"],
        })
    assert {item["base_z"] for item in plan["instances"]} == {0.8}
    return expected_p_frames(rails, timbers, bindings, base_z_mm=0.8)


def _stale_controls(before, after):
    """Deliberately stale results must fail before fresh materialisation."""
    assert len(assert_recalculated(before, after)["changed_centre_ids"]) == 28
    assert len(assert_recalculated(before, after)["changed_axis_ids"]) == 28
    outcomes = {}
    for field in ("origin_mm", "axes"):
        stale = tuple(replace(
            new, **({"origin_mm": old.origin_mm} if field == "origin_mm"
                    else {"x_axis": old.x_axis, "y_axis": old.y_axis}),
        ) for old, new in zip(before, after))
        try:
            validate_p_frames(stale, after)
        except AssertionError as error:
            outcomes[field] = str(error)
        else:
            raise AssertionError("Stale control accepted: " + field)
    return outcomes


def _generate(module, document, radius_mm, directory):
    """Operate the real dialog; change only radius and explicit Replace."""
    record = {name: [] for name in ("inputs", "replace", "success", "errors")}
    seen = set()

    def monitor():
        try:
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if not widget.isVisible() or id(widget) in seen:
                    continue
                if isinstance(widget, module.CurveInputDialog):
                    seen.add(id(widget))
                    before = copy.deepcopy(widget.values())
                    assert before[0] == 600 and before[2:4] == (90, 32)
                    assert not before[15]["enabled"]
                    widget.radius_box.setValue(radius_mm)
                    index = widget.output_mode_box.findText(
                        module.OUTPUT_REPLACE,
                    )
                    assert index >= 0
                    widget.output_mode_box.setCurrentIndex(index)
                    after = copy.deepcopy(widget.values())
                    assert after[1] == radius_mm
                    assert len(before) == len(after) == 18
                    assert all(a == b for i, (a, b) in enumerate(
                        zip(before, after),
                    ) if i not in (1, 17))
                    record["inputs"].append({
                        "before": before, "after": after,
                    })
                    assert widget.grab().save(str(
                        directory / "radius-input.png",
                    ))
                    boxes = widget.findChildren(QtWidgets.QDialogButtonBox)
                    buttons = [box.button(
                        QtWidgets.QDialogButtonBox.StandardButton.Ok,
                    ) for box in boxes]
                    buttons = [button for button in buttons
                               if button is not None]
                    assert len(buttons) == 1
                    buttons[0].click()
                elif isinstance(widget, QtWidgets.QMessageBox):
                    seen.add(id(widget))
                    message = {"title": widget.windowTitle(),
                               "text": widget.text()}
                    if "Replace generated templates" in widget.windowTitle():
                        record["replace"].append(message)
                        widget.button(
                            QtWidgets.QMessageBox.StandardButton.Yes,
                        ).click()
                    elif ("Curve and straight-track outputs created "
                          "successfully" in widget.text()):
                        record["success"].append(message)
                        widget.accept()
                    else:
                        raise AssertionError(message)
        except BaseException:
            record["errors"].append(traceback.format_exc())
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if (isinstance(widget, QtWidgets.QDialog)
                        and widget.isVisible()):
                    widget.reject()

    App.setActiveDocument(document.Name)
    timer = QtCore.QTimer()
    timer.timeout.connect(monitor)
    timer.start(25)
    try:
        module.run_macro()
    finally:
        timer.stop()
        timer.timeout.disconnect(monitor)
        timer.deleteLater()
        _write(directory / "generate.json", record)
    assert not record["errors"], record["errors"]
    assert all(len(record[key]) == 1
               for key in ("inputs", "replace", "success"))
    assert module.quantity_value(module.latest_generated_settings(document),
                                 "CurveRadius", -1) == radius_mm
    assert module.crossover_config_by_id(document, "XO-001") is not None
    return record


def _recreate(module, command, source, config, path):
    """Keep railway options and toe A fixed; let the original solver own B."""
    hosts = [source.getObject(config[key])
             for key in ("host_a_object", "host_b_object")]
    assert all(hosts)
    arguments = (source, *hosts, config["reference_chainage"],
                 config["arrangement"], config["handing"],
                 config["track_gauge"],
                 config["flangeway"], config["minimum_requested_radius"])
    solved = module.solve_rea_c10_crossover_geometry(*arguments)
    fresh = module.create_rea_c10_crossover(*arguments, pre_solved=solved)
    assert fresh["crossover_id"] == "XO-001"
    assert fresh["toe_chainage_a"] == config["toe_chainage_a"] == 746.298
    assert (fresh["minimum_resulting_radius"]
            >= config["minimum_requested_radius"])
    refusals = {}
    for stage in ("missing-b4", "missing-analysis"):
        registry = dict(App.listDocuments())
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Incomplete canonical source created a preview",
        )):
            refusals[stage] = catalogue._reject(
                lambda: command(source, "XO-001", path), ValueError,
            )
        assert App.listDocuments() == registry
        if stage == "missing-b4":
            b4 = module.apply_crossover_b4_timbering(
                source, "XO-001", config["shared_timber_settings"],
                config["b3_settings"], config["b4_settings"],
            )
            assert b4["cache_reused"] is False
    analysis = module.analyse_entity_chair_positions(
        source, "crossover", "XO-001",
        settings=config["chair_analysis_settings"],
    )
    assert analysis["cache_reused"] is False
    return {"toe_a_mm": fresh["toe_chainage_a"],
            "toe_b_mm": fresh["toe_chainage_b"],
            "minimum_resulting_radius_mm": fresh["minimum_resulting_radius"],
            "missing_source_refusals": refusals, "fresh_b4_and_analysis": True}


def _current_dependencies(module, source, original):
    """Inspect automatic results without rebuilding or refreshing them."""
    current = module.crossover_config_by_id(source, "XO-001")
    assert current is not None
    assert all(current[key] == original[key] for key in SOURCE_OPTIONS)
    assert current["b4_result"]
    context = previous._context(module, source)
    assert context[1]["positions"]
    return {"same_crossover_identity": "XO-001",
            "same_options": True, "current_b4_and_analysis": True,
            "source_context_sha256": _digest(context),
            "manual_recreation_or_analysis": False}


def _source_state(module, source, count, *, negative_controls=False):
    """Keep the original complete witness with this fixed case's count."""
    helper = previous.xo.helpers
    assert previous.xo._state.__globals__["helpers"] is helper
    continuity = helper.continuity
    assert helper._state.__globals__["continuity"] is continuity
    original = dict(continuity.CASES)
    assert count in {case[2] for case in CASES}
    try:
        with patch.dict(continuity.CASES, {"crossover": ("XO-001", count)}):
            state = previous.xo._state(module, source)
            if negative_controls:
                negatives = continuity._negative_witnesses(state["decisions"])
                assert len(negatives) == len(set(negatives)) == 9
                return negatives
            return state
    finally:
        assert continuity.CASES == original


def _refresh_native_transport(module, source):
    """Refresh analysis after copied transport changes exact rail inputs.

    FCStd transport is fixture preparation, not a persistence qualification.
    Preserve the original stale guard and all reopened railway inputs.
    """
    config = copy.deepcopy(module.crossover_config_by_id(source, "XO-001"))
    settings = module.normalise_chair_analysis_settings(
        config["chair_analysis_settings"],
    )
    rails = module.chair_rail_records_for_entity(source, "crossover", config)
    timbers = module.chair_timber_records_for_entity(
        source, "crossover", config,
    )
    before = copy.deepcopy((rails, timbers, settings, config["b4_result"],
                            {key: config[key] for key in SOURCE_OPTIONS}))
    rejection = catalogue._reject(
        lambda: previous._context(module, source), ValueError,
    )
    assert "Chair analysis is stale" in rejection
    result = module.analyse_entity_chair_positions(
        source, "crossover", "XO-001", settings=settings,
    )
    assert result["cache_reused"] is False
    context = previous._context(module, source)
    fresh = module.crossover_config_by_id(source, "XO-001")
    after = (context[4], context[5], context[2], fresh["b4_result"],
             {key: fresh[key] for key in SOURCE_OPTIONS})
    assert after == before
    return {"stale_source_rejection": rejection,
            "stored_signature_before": config["chair_analysis_signature"],
            "fresh_signature": result["geometry_signature"],
            "fresh_analysis_cache_reused": False,
            "source_guard_after": "PASS",
            "rails_timbers_settings_options_b4_unchanged": True,
            "source_basis_sha256": _digest(before),
            "scope": "Fresh analysis on disposable native transport only"}


def _guard(module, source, foreign, gui, count):
    """Retain the accepted exact source, foreign and object-state guard."""
    _source_state(module, source, count)
    combined._settle(source)
    state = _source_state(module, source, count)
    negatives = _source_state(module, source, count, negative_controls=True)
    foreign_state = combined._foreign_state(foreign)
    registry = dict(App.listDocuments())
    identities = {(doc.Name, obj.Name): obj for doc in registry.values()
                  for obj in doc.Objects}
    shapes = {key: obj.Shape for key, obj in identities.items()
              if "Shape" in obj.PropertiesList}
    selection = lifecycle._selection_snapshot(App, gui)
    preselection = lifecycle._preselection_snapshot(App, gui)

    def unchanged(stage, active):
        assert _source_state(module, source, count) == state, stage
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
        assert lifecycle._preselection_snapshot(
            App, gui,
        ) == preselection, stage
        catalogue.helpers._active_document_state(active)

    return unchanged, selection, preselection, _digest(state), negatives


def _canonical_record(module, source, original, radius):
    current = module.crossover_config_by_id(source, "XO-001")
    assert all(current[key] == original[key] for key in SOURCE_OPTIONS)
    assert current["minimum_requested_radius"] == 600.0
    assert (current["minimum_resulting_radius"]
            >= current["minimum_requested_radius"])
    assert module.quantity_value(module.latest_generated_settings(source),
                                 "CurveRadius", -1) == radius
    return {"unchanged_options": {key: current[key] for key in SOURCE_OPTIONS},
            "toe_b_mm": current["toe_chainage_b"],
            "minimum_resulting_radius_mm": current["minimum_resulting_radius"]}


def _assert_preview(result, document, reference, frames, context):
    """Compare all 616 components and the current complete partition."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert tuple(obj.Name for obj in document.Objects) == p.LAYER_NAMES
    assert result["component_count"] == 22 and result["placement_count"] == 28
    assert result["layer_count"] == 24 and result["solid_count"] == 644
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["source_model_sha256"] == previous.adapter._P_MODEL_SHA256
    assert result["scale_denominator"] == "76.2"
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    excluded = result["excluded_source_components"]
    assert [item["source_name"] for item in excluded] == ["display_rail"]
    _signature, analysis, _settings, plan, _rails, _timbers = context
    source = result["source_receipt"]
    assert source["crossover_id"] == "XO-001"
    assert source["source_kind"] == "crossover" and "turnout_id" not in source
    assert source["timber_context"] == "current B4 resolved timbers"
    assert source["analysis_position_count"] == len(analysis["positions"])
    assert (source["selected_p_count"]
            == len(source["selected_positions"]) == 28)
    assert (len(source["remaining_positions"])
            == len(analysis["positions"]) - 28)
    assert source["original_analytical_exclusions"] == plan["analytical_only"]
    selected = {item["position_id"] for item in source["selected_positions"]}
    remaining = {item["position_id"] for item in source["remaining_positions"]}
    assert not selected & remaining
    assert selected | remaining == {
        item["stable_chair_position_identity"]
        for item in analysis["positions"]
    }
    assert selected == {frame.position_id for frame in frames}
    signature = hashlib.sha256(context[0].encode()).hexdigest()
    assert source["source_context_signature"] == "sha256:" + signature
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    for item in source["selected_positions"]:
        assert item["key_direction_sign"] == 0
        assert item["key_orientation"] == (
            "requires a configurable key-direction policy"
        )
        assert item["original_exclusion"] in plan["analytical_only"]
    comparison = validate_p_frames(result["placements"], frames)
    assert [item["position_id"] for item in result["placements"]] == [
        frame.position_id for frame in frames
    ]
    assert len(result["components"]) == 22
    for obj in document.Objects[:2]:
        assert not obj.Shape.Solids and not obj.Shape.Faces
    components = []
    for obj, component, name in zip(document.Objects[2:], result["components"],
                                    p.COMPONENT_NAMES):
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
        assert component["source_name"] == obj.Name == name
        assert tuple(component["source_identity"]) == (
            result["source_model_sha256"], name,
        )
        children = obj.Shape.childShapes()
        assert len(children) == len(frames)
        components.append({"name": name, "positions": [
            p._compare_component(child, reference[name], frame)
            for child, frame in zip(children, frames)
        ]})
    assert all(len(item["components"]) == 22 for item in result["placements"])
    assert result["solid_count"] == sum(
        len(obj.Shape.Solids) for obj in document.Objects
    )
    return {"frames": comparison, "components": components}


def _change_back(document, reference, original, current):
    """Use the existing dimensional contract across regenerated solutions.

    The 32-epsilon frame guard remains a same-raw-source arithmetic check.
    Separately regenerated source endpoints can round differently; report
    those angular residuals without granting an angular fit allowance.
    """
    assert [(f.position_id, f.rail_id, f.timber_id) for f in current] == [
        (f.position_id, f.rail_id, f.timber_id) for f in original
    ]
    checks = [p._compare_component(child, reference[obj.Name], frame)
              for obj in document.Objects[2:]
              for child, frame in zip(obj.Shape.childShapes(), original)]
    assert len(checks) == 28 * 22
    return {"component_count": len(checks),
            "maximum_vertex_residual_mm": max(
                c["vertex_residual_mm"] for c in checks),
            "coordinate_contract_mm": p.EPSILON_MM,
            "maximum_source_axis_residual": max(
                math.dist(getattr(a, name), getattr(b, name))
                for a, b in zip(original, current)
                for name in ("x_axis", "y_axis")),
            "physical_fit": "NOT_PROVED"}


def _inspect(document, frames, directory, detailed):
    """Reuse the real-GL capture and all-layer visibility witnesses."""
    for obj in document.Objects:
        assert obj.ViewObject.Visibility
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        assert Gui.Selection.getSelection() == [obj]
        obj.ViewObject.Visibility = False
        combined._settle(document)
        assert not obj.ViewObject.Visibility
        obj.ViewObject.Visibility = True
        combined._settle(document)
        assert obj.ViewObject.Visibility
    Gui.Selection.clearSelection()
    targets = [frame for frame in frames if any(
        "-" + code + ":" in frame.position_id for code in ("s1", "s7")
    )] if detailed else [frames[0]]
    assert len(targets) == (8 if detailed else 1)
    view = Gui.getDocument(document.Name).activeView()
    animation = view.isAnimationEnabled()
    images = []
    try:
        view.setAnimationEnabled(False)
        for index, frame in enumerate(targets):
            target = directory / ("view-" + str(index))
            target.mkdir()
            files = previous.helpers._images(document, (frame,), target)
            images.append({"position_id": frame.position_id,
                           "directory": str(target), "files": files})
    finally:
        view.setAnimationEnabled(animation)
    assert view.isAnimationEnabled() == animation
    return images


def _rollback(module, session, source, path, unchanged, preview):
    """Reuse the accepted late source-change rollback control once."""
    top = module._chair_physical_top_z
    create = previous.adapter.create_private_catalogue_p_preview

    def stale_during_build(*args):
        def changed_source():
            assert App.ActiveDocument is not source
            assert len(App.ActiveDocument.Objects) == 24
            with patch.object(module, "_chair_physical_top_z",
                              side_effect=lambda *values: top(*values) + 1e-8):
                args[-1]()
        return create(*args[:-1], changed_source)

    with patch.object(session, "_private_catalogue_p_preview_factory",
                      side_effect=stale_during_build):
        rejected = previous.helpers._reject(
            lambda: session.preview_private_catalogue_p_crossover_chairs(
                source, "XO-001", path,
            ), "source changed",
        )
    unchanged("late source rollback", preview)
    return rejected


def validate():
    """Run the frozen proof in an empty qualified native or real-GUI host."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    gui = Gui if App.GuiUp else None
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"])
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    assert catalogue._hash(fixture) == previous.xo.FIXTURE_SHA256
    run_dir = Path(os.environ["TRACKTEMPLATE_P_CURVATURE_RUN_DIR"])
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(gui), "cases": [],
               "physical_fit": "NOT_PROVED",
               "automatic_regeneration": bool(gui)}
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
        foreign = App.newDocument("PCurvatureUnrelatedWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(
            2, 3, 4,
        )
        foreign.recompute()
        combined._settle(foreign)
        foreign_state = combined._foreign_state(foreign)
        transport = None
        if not gui:
            packet = Path(os.environ["TRACKTEMPLATE_P_CURVATURE_INPUTS"])
            transport = json.loads(packet.read_text())
            assert transport["status"] == "PASS"
            receipt["native_input_transport"] = {
                "path": str(packet), "sha256": catalogue._hash(packet),
            }
        source, config = None, None
        old_previews, verifiers, original_frames = [], [], None
        for label, radius, count in CASES:
            directory = run_dir / label
            directory.mkdir()
            item = {"label": label, "radius_mm": radius,
                    "analysis_count": count}
            receipt["cases"].append(item)
            if gui and source is not None:
                Gui.Selection.clearSelection()
                App.setActiveDocument(source.Name)
                combined._settle(source)
                frozen = [combined._foreign_state(doc)
                          for doc in old_previews]
                item["canonical_input"] = _generate(
                    module, source, radius, directory,
                )
                item["old_source_refusal"] = catalogue._reject(
                    verifiers[-1], ValueError,
                )
                item["dependent_recalculation"] = _current_dependencies(
                    module, source, config,
                )
                assert [combined._foreign_state(doc)
                        for doc in old_previews] == frozen
                assert combined._foreign_state(foreign) == foreign_state
                item["old_previews_static"] = True
            else:
                input_path = fixture
                if label != CASES[0][0]:
                    record = next(c for c in transport["cases"]
                                  if c["label"] == label)
                    input_path = Path(record["fcstd"])
                    assert (catalogue._hash(input_path)
                            == record["fcstd_sha256"])
                target = directory / "XO-001.FCStd"
                shutil.copy2(input_path, target)
                source = App.openDocument(str(target))
                source.UndoMode = 1
                if label == CASES[0][0]:
                    config = copy.deepcopy(module.crossover_config_by_id(
                        source, "XO-001",
                    ))
                else:
                    item["native_transport_refresh"] = (
                        _refresh_native_transport(module, source)
                    )
            item["canonical"] = _canonical_record(
                module, source, config, radius,
            )
            context = previous._context(module, source)
            frames = _frames(module, context, count)
            _write(directory / "source-context.json", context)
            _write(directory / "source-frames.json",
                   [asdict(f) for f in frames])
            if original_frames is None:
                original_frames = frames
            elif label == "changed-900":
                item["test_first_stale_controls"] = _stale_controls(
                    original_frames, frames,
                )
                item["recalculated"] = assert_recalculated(
                    original_frames, frames,
                )
            if gui:
                source.saveAs(str(directory / "XO-001.FCStd"))
                Gui.getMainWindow().resize(1600, 1000)
                Gui.Selection.addSelection(source.Objects[0])
            App.setActiveDocument(source.Name)
            combined._settle(source)
            unchanged, selection, preselection, state_hash, negatives = _guard(
                module, source, foreign, gui, count,
            )
            item["source_state_sha256"] = state_hash
            item["source_guard_negative_witnesses"] = negatives
            create = session._private_catalogue_p_preview_factory

            def capture_verifier(*args):
                verifiers.append(args[-1])
                return create(*args)

            with (
                patch.object(session, "_private_catalogue_p_preview_factory",
                             capture_verifier),
                patch.object(App, "openDocument", side_effect=AssertionError(
                    "Product restored external source",
                )),
            ):
                result = command(source, "XO-001", path)
            preview = App.getDocument(result["document_name"])
            item["preview"] = result
            item["comparisons"] = _assert_preview(
                result, preview, reference, frames, context,
            )
            unchanged("created", preview)
            shapes = tuple(obj.Shape for obj in preview.Objects)
            assert preview.UndoCount == 1
            preview.undo()
            assert not preview.Objects
            preview.redo()
            assert tuple(obj.Name for obj in preview.Objects) == p.LAYER_NAMES
            assert all(p.catalogue_adapter._same_presented_shape(
                obj.Shape, shape,
            ) for obj, shape in zip(preview.Objects, shapes))
            unchanged("Undo/Redo", preview)
            item["undo_redo"] = "PASS"
            if label == "changed-900":
                item["late_source_rollback"] = _rollback(
                    module, session, source, path, unchanged, preview,
                )
            if label == "returned-600":
                item["change_back"] = _change_back(
                    preview, reference, original_frames, frames,
                )
            if gui:
                item["images"] = _inspect(
                    preview, frames, directory, label == "changed-900",
                )
                lifecycle._restore_selection(App, gui, selection)
                lifecycle._restore_preselection(App, gui, preselection)
                unchanged("GUI inspection", preview)
            assert previous._context(module, source) == context
            assert combined._foreign_state(foreign) == foreign_state
            old_previews.append(preview)
            item["fcstd"] = str(directory / "XO-001.FCStd")
            item["fcstd_sha256"] = catalogue._hash(Path(item["fcstd"]))
            _write(run_dir / "progress.json", receipt)
            print("P_CURVATURE_CASE_PASS", label, flush=True)
        p.verify_catalogue_sources(prepared)
        assert catalogue._hash(fixture) == previous.xo.FIXTURE_SHA256
        receipt["fixture_unchanged"] = True
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        catalogue.helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        _write(run_dir / "result.json", receipt)
    assert catalogue.helpers._document_state() == initial
    receipt["status"] = "PASS"
    _write(run_dir / "result.json", receipt)
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
