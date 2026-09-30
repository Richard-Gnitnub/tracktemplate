#!/usr/bin/env python3
"""Prove straight-host XO-001 B4 recovery in a qualified real GUI."""

import argparse
import datetime
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".devtools/freecad-cli/src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


PORT = 19875
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE_RECIPE = "phase8-b14-straight-host-source-v1"
SOURCE_WITNESS = (
    "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
)
SOURCE_DOCUMENT_SEMANTIC = (
    "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
)
HEADLESS_SENTINEL = (
    "Phase 8 straight-host crossover B4 FreeCAD validation passed"
)
PROBE_SENTINEL = "PHASE8_STRAIGHT_CROSSOVER_B4_GUI_PROBE_PASS"
SENTINEL = "PHASE8_STRAIGHT_CROSSOVER_B4_GUI_PASS"
CONTRACT_PATH = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
LOADER_PATH = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = (
    ROOT / "benchmark-output/freecad-bridge/"
    "phase8-straight-crossover-b4-gui-runs"
)
SOURCE_PATHS = (
    ROOT / "AdvancedTurnout.FCMacro",
    ROOT / (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ),
    ROOT / "TrackTemplate.FCMacro",
    CONTRACT_PATH,
    ROOT / "reference/contracts/phase1-compatibility.json",
    ROOT / "reference/contracts/phase1-transition-pilot.json",
    ROOT / "tools/phase3_transition_pilot.py",
    ROOT / "tools/freecad_bridge/run-isolated",
    ROOT / "tools/freecad_bridge/launch-freecad",
    ROOT / "tools/freecad_bridge/orchestration.py",
    ROOT / "tools/freecad_bridge/b14_recipe.py",
    ROOT / "tools/freecad_bridge/ordinary_track_recipe.py",
    ROOT / "tools/freecad_bridge/crossover_timber_recipe.py",
    ROOT / "tools/freecad_bridge/compare_phase8_straight_crossover_b4_modes.py",
    ROOT / "tools/freecad_bridge/run_b14_straight_station.py",
    ROOT / "tools/freecad_bridge/probes/b14_straight_station_driver.py",
    LOADER_PATH,
    *sorted((ROOT / "tracktemplate").rglob("*.py")),
    pathlib.Path(__file__).resolve(),
    ROOT / "tools/freecad_bridge/run-phase8-straight-crossover-b4-gui",
    ROOT / "tests/freecad_validate_phase8_straight_crossover_b4.py",
)


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge.b14_recipe import host_identity
from tools.freecad_bridge import crossover_timber_recipe as recipe
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
)
from tracktemplate.compatibility.crossover_b4_recovery import (
    CrossoverB4RecoveryAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
if (document is None or not document.FileName
        or Gui.activeDocument() is None):
    raise RuntimeError("Open the copied straight-host fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")
b4_adapter = getattr(module.apply_crossover_b4_timbering, "__self__", None)
panel_apply = module.CrossoverManagerPanel.__dict__.get("apply_b4_timbering")
if getattr(panel_apply, "_whole_workflow_benchmark_wrapper", False):
    if str(getattr(panel_apply, "_whole_workflow_wrapper_version", "")) != "10.2A8A7B15":
        raise RuntimeError("The inherited B4 panel wrapper version changed")
    panel_apply = getattr(panel_apply, "_whole_workflow_original", None)
if (not isinstance(b4_adapter, CrossoverB4RecoveryAdapter)
        or b4_adapter.module is not module
        or b4_adapter.original_apply.__globals__ is not module.__dict__
        or getattr(panel_apply, "__globals__", None) is not module.__dict__
        or "apply_crossover_b4_timbering" not in
        getattr(getattr(panel_apply, "__code__", None), "co_names", ())):
    raise RuntimeError("The B4 GUI action is not routed through B16 recovery")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(value) for value in active_document.UndoNames],
        "redo_names": [str(value) for value in active_document.RedoNames],
    }


def state(active_document):
    ordinary = ordinary_track_document_snapshot(module, active_document)
    timber = recipe.document_snapshot(module, active_document, "XO-001")
    # A group Shape is derived from its children and GUI visibility on reopen.
    group = dict(timber["objects"]["ModelRailwayCurve"])
    if group["type_id"] != "App::DocumentObjectGroup":
        raise RuntimeError("The model group type changed")
    group.pop("shape", None)
    reopen_semantic = dict(timber)
    reopen_semantic["objects"] = dict(timber["objects"])
    reopen_semantic["objects"]["ModelRailwayCurve"] = group
    return {
        "ordinary_semantic_sha256": ordinary["semantic_sha256"],
        "timber_semantic_sha256": recipe.digest(timber),
        "reopen_semantic_sha256": recipe.digest(reopen_semantic),
        "object_names": [str(obj.Name) for obj in active_document.Objects],
        "history": history(active_document),
        "ordinary_semantic": ordinary["semantic"],
        "timber_semantic": timber,
        "reopen_semantic": reopen_semantic,
    }


def require_same_semantics(
    actual, expected, label, *, allow_derived_group_shape=False,
):
    for key in (
        "ordinary_semantic_sha256", "timber_semantic_sha256",
        "object_names", "ordinary_semantic", "timber_semantic",
    ):
        if actual[key] != expected[key]:
            if (allow_derived_group_shape
                    and key in ("timber_semantic_sha256", "timber_semantic")
                    and actual["reopen_semantic"]
                    == expected["reopen_semantic"]):
                continue
            detail = ""
            if key == "timber_semantic_sha256":
                before = expected["timber_semantic"]
                after = actual["timber_semantic"]
                fields = sorted(
                    name for name in set(before) | set(after)
                    if before.get(name) != after.get(name)
                )
                detail = " (fields: {})".format(fields)
                if "config" in fields:
                    config_fields = sorted(
                        name for name in set(before["config"]) | set(after["config"])
                        if before["config"].get(name) != after["config"].get(name)
                    )
                    detail += " (config: {})".format(config_fields)
                if "objects" in fields:
                    object_fields = {
                        name: sorted(
                            field for field in (
                                set(before["objects"].get(name) or {})
                                | set(after["objects"].get(name) or {})
                            )
                            if (before["objects"].get(name) or {}).get(field)
                            != (after["objects"].get(name) or {}).get(field)
                        )
                        for name in (
                            set(before["objects"]) | set(after["objects"])
                        )
                        if before["objects"].get(name) != after["objects"].get(name)
                    }
                    detail += " (objects: {})".format(object_fields)
            raise RuntimeError(
                "{} changed the copied document: {}{}".format(
                    label, key, detail,
                )
            )


def b4_persistence(active_document):
    settings = [
        obj for obj in active_document.Objects
        if module.object_string_property(obj, "GeneratedRole", "")
        == module.CROSSOVER_SETTINGS_ROLE
        and module.object_string_property(
            obj, module.CROSSOVER_ID_PROPERTY, ""
        ) == "XO-001"
    ]
    if len(settings) != 1:
        raise RuntimeError("The selected crossover has no unique settings object")
    obj = settings[0]
    config = json.loads(module.object_string_property(
        obj, module.CROSSOVER_CONFIGURATION_PROPERTY, ""
    ))
    result = json.loads(module.object_string_property(
        obj, module.CROSSOVER_B4_RESULT_PROPERTY, ""
    ))
    analysis = json.loads(module.object_string_property(
        obj, module.CROSSOVER_TIMBER_ANALYSIS_RESULT_PROPERTY, ""
    ))
    nested = result.get("resolved_analysis")
    signature = str((nested or {}).get("geometry_signature") or "")
    if (not isinstance(nested, dict) or not signature
            or nested.get("analysis_basis")
            != "Effective automatically resolved timber arrangement"
            or nested != analysis
            or config.get("b4_result") != result
            or config.get("timber_analysis_signature") != signature
            or module.object_string_property(
                obj, module.CROSSOVER_TIMBER_ANALYSIS_SIGNATURE_PROPERTY, ""
            ) != signature):
        raise RuntimeError(
            "B4 resolved diagnostics differ across the stored result, "
            "configuration and analysis properties"
        )
    return {
        "result": result,
        "analysis": nested,
        "signature": signature,
        "analysis_sha256": recipe.digest(nested),
    }


def production_state(active_document):
    settings = module.settings_for_template_set(active_document, "SET-001")
    if settings is None:
        raise RuntimeError("The SET-001 production settings object is absent")
    index = module.read_production_record_index(settings)
    if (index is None or index.get("schema_version") != 2
            or index.get("template_set_id") != "SET-001"):
        raise RuntimeError("The SET-001 production index changed")
    records = index["records"]
    crossover = [
        item for item in records if item.get("route_id") == "XO-001"
    ]
    if (len(records) != 16 or len(crossover) != 4
            or len({item["record_id"] for item in records}) != 16):
        raise RuntimeError("The straight XO-001 production records changed")
    for item in crossover:
        source = active_document.getObject(item["source_name"])
        if (item.get("source_binding_type") != "direct"
                or source is None
                or item["record_id"] not in json.loads(
                    module.object_string_property(
                        source, "ProductionRecordIDsJSON", ""
                    )
                )):
            raise RuntimeError("An XO-001 production binding changed")
    stable_index = {
        key: value for key, value in index.items()
        if key not in {"macro_version", "created_at"}
    }
    return stable_index, crossover


def image_checked(path):
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("The GUI screenshot is absent or invalid: {}".format(path))
    return str(path)


def capture_panel(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    manager.show()
    manager.mode_tabs.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()
    if not panel.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture the crossover panel")
    return image_checked(path)


def capture_top(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    manager.hide()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(path), 1600, 1000, "Current")
    manager.show()
    return image_checked(path)


def confirm_creation(action):
    observed = {"active": True, "questions": [], "unexpected": []}

    def monitor():
        if not observed["active"]:
            return
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                continue
            message = "{}\n{}".format(widget.text(), widget.informativeText())
            yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
            if yes is not None and not observed["questions"]:
                observed["questions"].append(message)
                yes.click()
            else:
                observed["unexpected"].append(message)
                widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        observed["active"] = False
    if len(observed["questions"]) != 1 or observed["unexpected"]:
        raise RuntimeError("Crossover creation dialogs changed: {}".format(observed))
    return observed["questions"][0]


def capture_error_dialog(action, fault_text):
    observed = {
        "active": True, "seen": set(), "dialogs": [],
        "unexpected": [], "monitor_errors": [],
    }

    def monitor():
        if not observed["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                    continue
                identity = id(widget)
                if identity in observed["seen"]:
                    continue
                observed["seen"].add(identity)
                title = str(widget.windowTitle())
                message = "{}\n{}".format(widget.text(), widget.informativeText())
                if "Automatic timber-resolution error" not in title or fault_text not in message:
                    observed["unexpected"].append({"title": title, "message": message})
                else:
                    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / "straight-first-tag-failure-dialog.png"
                    if not widget.grab().save(str(path), "PNG"):
                        raise RuntimeError("Qt could not capture the B4 failure dialog")
                    observed["dialogs"].append({
                        "title": title, "message": message,
                        "visual": image_checked(path),
                    })
                widget.accept()
        except Exception as error:
            observed["monitor_errors"].append(
                "{}: {}".format(type(error).__name__, error)
            )
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        observed["active"] = False
    if (observed["monitor_errors"] or observed["unexpected"]
            or len(observed["dialogs"]) != 1):
        raise RuntimeError("B4 first-tag failure GUI dialog changed: {}".format(observed))
    return observed["dialogs"][0]


manager = module.TurnoutManagerDialog(document)
manager.show()
manager.mode_tabs.setCurrentIndex(1)
QtWidgets.QApplication.processEvents()
panel = manager.crossover_panel

try:
    base = state(document)
    if (len(base["object_names"]) != 23
            or base["ordinary_semantic_sha256"]
            != "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
            or base["history"]["undo_count"]):
        raise RuntimeError("The copied straight-host fixture changed")

    panel.refresh_hosts()
    identities = [
        host_identity(
            host, module.object_string_property,
            module._integer_object_property,
        )
        for host in panel.hosts
    ]

    def select_host(track_number):
        matches = [
            index for index, identity in enumerate(identities)
            if identity["template_set_id"] == "SET-001"
            and identity["route_id"] == "straight-phase1-curve-entrance"
            and identity["track_number"] == track_number
            and identity["generated_role"] == "StraightTrackCentreline"
        ]
        if len(matches) != 1:
            raise RuntimeError("The straight host identity changed")
        return matches[0]

    a_index = select_host(1)
    b_index = select_host(2)
    selected_a = identities[a_index]
    selected_b = identities[b_index]
    if (selected_a["object_name"]
            != "RailwayStraightTrackCentreline_R01_T01"
            or selected_b["object_name"]
            != "RailwayStraightTrackCentreline_R01_T02"):
        raise RuntimeError("The GUI selected another straight-host pair")
    panel.host_a_combo.setCurrentIndex(a_index)
    panel.host_b_combo.setCurrentIndex(b_index)
    for combo, value in (
        (panel.arrangement_combo, module.CROSSOVER_ARRANGEMENT_FACING),
        (panel.handing_combo, module.CROSSOVER_HAND_AUTO),
    ):
        index = combo.findText(value)
        if index < 0:
            raise RuntimeError("The crossover GUI choice is absent: " + value)
        combo.setCurrentIndex(index)
    panel.gauge_box.setValue(16.5)
    panel.flangeway_box.setValue(1.0)
    panel.minimum_radius_box.setValue(600.0)
    panel.chainage_box.setValue(580.134)
    if abs(float(panel.chainage_box.value()) - 580.134) > 1.0e-9:
        raise RuntimeError("The GUI did not retain the fixed toe chainage")
    preview = panel.preview_geometry()
    if preview is None:
        raise RuntimeError("The straight XO-001 GUI preview was rejected")
    confirmation = confirm_creation(panel.create_crossover)
    panel.refresh_crossovers("XO-001")
    config = panel.current_config()
    if config is None or config.get("crossover_id") != "XO-001":
        raise RuntimeError("The GUI did not select the created XO-001")
    if (config.get("host_a_object") != selected_a["object_name"]
            or config.get("host_b_object") != selected_b["object_name"]
            or abs(float(config.get("toe_chainage_a") or 0) - 580.134)
            > 1.0e-9):
        raise RuntimeError("The GUI created XO-001 on other hosts or toe")
    before = state(document)
    before_index, before_bindings = production_state(document)
    if (len(before["object_names"]) != 32
            or before["history"]["undo_count"] != 1
            or before["history"]["redo_count"] != 0):
        raise RuntimeError("The straight crossover creation state changed")
    before_visual = capture_panel("straight-xo-001-before-b4-panel.png")

    original_tagger = module.tag_generated_object
    fault = {"calls": 0}
    fault_text = "Phase 8 injected B4 first-tag failure"

    def failing_tagger(obj, role, template_set_id):
        if role == module.CROSSOVER_B4_ROLE:
            fault["calls"] += 1
            raise RuntimeError(fault_text)
        return original_tagger(obj, role, template_set_id)

    module.tag_generated_object = failing_tagger
    try:
        error_dialog = capture_error_dialog(
            panel.apply_b4_button.click, fault_text
        )
    finally:
        module.tag_generated_object = original_tagger
    if fault["calls"] != 1:
        raise RuntimeError("The GUI action did not reach exactly one first B4 tag")
    aborted = state(document)
    require_same_semantics(aborted, before, "The aborted B4 command")
    if aborted["history"] != before["history"]:
        raise RuntimeError("The aborted B4 command changed Undo/Redo history")
    if production_state(document) != (before_index, before_bindings):
        raise RuntimeError("The aborted B4 command changed production bindings")
    if document.getObject("CrossoverB4Timbering_XO_001") is not None:
        raise RuntimeError("The aborted B4 command retained an untagged Part object")
    panel.refresh_crossovers("XO-001")
    if panel.current_config().get("b4_result"):
        raise RuntimeError("The failed B4 command persisted a result")
    after_failure_visual = capture_panel("straight-xo-001-after-failure-panel.png")

    panel.apply_b4_button.click()
    panel.refresh_crossovers("XO-001")
    config = panel.current_config()
    result = config.get("b4_result") if config else None
    if not isinstance(result, dict) or not result:
        raise RuntimeError("The GUI B4 apply did not store a result")
    applied = state(document)
    applied_index, applied_bindings = production_state(document)
    if (len(applied["object_names"]) != 34
            or applied["history"]["undo_count"] != 2
            or applied["history"]["redo_count"] != 0
            or (applied_index, applied_bindings)
            != (before_index, before_bindings)):
        raise RuntimeError("The successful B4 command did not make one Undo unit")
    b4_obj = module._crossover_b4_object(document, "XO-001")
    if b4_obj is None or str(b4_obj.Name) != "CrossoverB4Timbering_XO_001":
        raise RuntimeError("The successful B4 object is absent or renamed")
    result_summary = recipe.result_snapshot(module, result)
    shape = recipe.shape_summary(b4_obj.Shape)
    if (result_summary["counts"]["effective_timber_count"] != 82
            or result_summary["counts"]["shared_timber_count"] != 18
            or result_summary["counts"]["unresolved_count"] != 0
            or result_summary["counts"]["remaining_production_conflicts"] != 0
            or result_summary["stable_record_sha256"]
            != "fadb190ade28ccd26ea85c8016b5476e40506e1b980280ad2ad116bb945c6133"
            or shape is None or shape["edges"] != 1216):
        raise RuntimeError("The straight XO-001 B4 railway result changed")
    applied_persistence = b4_persistence(document)
    if applied_persistence["result"] != result:
        raise RuntimeError("The panel result differs from raw B4 persistence")
    applied_visuals = [
        capture_panel("straight-xo-001-applied-b4-panel.png"),
        capture_top("straight-xo-001-applied-b4-top-view.png"),
    ]

    reused = module.apply_crossover_b4_timbering(document, "XO-001")
    if (reused.get("cache_reused") is not True
            or reused.get("resolved_analysis")
            != applied_persistence["analysis"]):
        raise RuntimeError("Unchanged B4 reuse lost resolved diagnostics")
    require_same_semantics(state(document), applied, "Unchanged B4 reuse")
    if (history(document) != applied["history"]
            or b4_persistence(document) != applied_persistence
            or production_state(document)
            != (before_index, before_bindings)):
        raise RuntimeError("Unchanged B4 reuse modified document or history")

    shape_brep = b4_obj.Shape.exportBrepToString()
    solver = module.resolve_crossover_b4_timbering
    shape_builder = module._shared_timber_shape_from_records
    display_calls = {"solver": 0, "shape": 0}

    def counted_solver(*args, **kwargs):
        display_calls["solver"] += 1
        return solver(*args, **kwargs)

    def counted_shape(*args, **kwargs):
        display_calls["shape"] += 1
        return shape_builder(*args, **kwargs)

    module.resolve_crossover_b4_timbering = counted_solver
    module._shared_timber_shape_from_records = counted_shape
    try:
        for visible in (False, True):
            panel.show_b4_checkbox.setChecked(visible)
            QtWidgets.QApplication.processEvents()
            if bool(b4_obj.ViewObject.Visibility) != visible:
                raise RuntimeError("The B4 checkbox did not change visibility")
            panel.apply_b4_button.click()
            panel.refresh_crossovers("XO-001")
            if (bool(b4_obj.ViewObject.Visibility) != visible
                    or panel.show_b4_checkbox.isChecked() != visible
                    or panel.current_config().get("crossover_id") != "XO-001"):
                raise RuntimeError("The B4 panel lost live visibility or selection")
            if (module._crossover_b4_object(document, "XO-001") is not b4_obj
                    or b4_obj.Shape.exportBrepToString() != shape_brep
                    or b4_persistence(document) != applied_persistence
                    or history(document) != applied["history"]):
                raise RuntimeError("Display-only B4 Apply changed product state")
        if display_calls != {"solver": 0, "shape": 0}:
            raise RuntimeError("Display-only B4 Apply rebuilt calculation or shape")
    finally:
        module.resolve_crossover_b4_timbering = solver
        module._shared_timber_shape_from_records = shape_builder
    if state(document)["timber_semantic_sha256"] != applied[
        "timber_semantic_sha256"
    ]:
        raise RuntimeError("B4 show/hide round trip changed the document")

    document.undo()
    document.recompute()
    undone = state(document)
    require_same_semantics(undone, before, "B4 Undo")
    if (undone["history"]["undo_count"] != 1
            or undone["history"]["redo_count"] != 1
            or module._crossover_b4_object(document, "XO-001") is not None
            or production_state(document)
            != (before_index, before_bindings)):
        raise RuntimeError("B4 Undo did not restore the selected crossover")
    document.redo()
    document.recompute()
    redone = state(document)
    require_same_semantics(redone, applied, "B4 Redo")
    if (redone["history"]["undo_count"] != 2
            or redone["history"]["redo_count"] != 0):
        raise RuntimeError("B4 Redo changed history")
    redone_persistence = b4_persistence(document)
    if (redone_persistence != applied_persistence
            or production_state(document)
            != (before_index, before_bindings)):
        raise RuntimeError("B4 Redo changed stored resolved diagnostics")

    panel.show_b4_checkbox.setChecked(False)
    QtWidgets.QApplication.processEvents()
    if (bool(b4_obj.ViewObject.Visibility)
            or history(document) != redone["history"]
            or b4_persistence(document) != applied_persistence):
        raise RuntimeError("B4 visibility-only save setup changed product state")
    hidden_before_capture = state(document)
    hidden_visual = capture_top("straight-xo-001-hidden-b4-top-view.png")
    manager.close()
    QtWidgets.QApplication.processEvents()
    hidden_saved = state(document)
    if (history(document) != redone["history"]
            or b4_persistence(document) != applied_persistence):
        raise RuntimeError("Closing the B4 panel changed stored result or history")
    view_capture_changed_objects = sorted(
        name for name in (
            set(hidden_before_capture["timber_semantic"]["objects"])
            | set(hidden_saved["timber_semantic"]["objects"])
        )
        if (hidden_before_capture["timber_semantic"]["objects"].get(name)
            != hidden_saved["timber_semantic"]["objects"].get(name))
    )
    document.save()
    saved_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(saved_path)
    reopened = state(document)
    require_same_semantics(
        reopened, hidden_saved, "Copied FCStd save/reopen",
        allow_derived_group_shape=True,
    )
    reopened_b4 = module._crossover_b4_object(document, "XO-001")
    if reopened_b4 is None or bool(reopened_b4.ViewObject.Visibility):
        raise RuntimeError("B4 visibility changed after save/reopen")
    reopened_persistence = b4_persistence(document)
    reopened_index, reopened_bindings = production_state(document)
    if (reopened_persistence != applied_persistence
            or (reopened_index, reopened_bindings)
            != (before_index, before_bindings)):
        raise RuntimeError("B4 save/reopen changed stored resolved diagnostics")
    if (reopened["history"]["undo_count"] != 0
            or reopened["history"]["redo_count"] != 0):
        raise RuntimeError("The reopened document retained prior session history")
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    reopened_visual = (
        pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR)
        / "straight-xo-001-reopened-b4-top-view.png"
    )
    view.saveImage(str(reopened_visual), 1600, 1000, "Current")
    image_checked(reopened_visual)

    print(json.dumps({
        "sentinel": "PHASE8_STRAIGHT_CROSSOVER_B4_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "routing": {"route": routing["route"], "schema_version": routing["schema_version"]},
        "selected_binding": type(b4_adapter).__name__,
        "host_a_identity": selected_a,
        "host_b_identity": selected_b,
        "source": {
            "object_count": len(base["object_names"]),
            "ordinary_semantic_sha256": base["ordinary_semantic_sha256"],
        },
        "creation_confirmation": confirmation,
        "before": {
            "object_count": len(before["object_names"]),
            "ordinary_semantic_sha256": before["ordinary_semantic_sha256"],
            "timber_semantic_sha256": before["timber_semantic_sha256"],
            "production_index": before_index,
            "production_bindings": before_bindings,
            "history": before["history"],
            "visual": before_visual,
        },
        "failure": {
            "dialog": error_dialog,
            "first_tag_calls": fault["calls"],
            "object_count": len(aborted["object_names"]),
            "ordinary_semantic_sha256": aborted["ordinary_semantic_sha256"],
            "timber_semantic_sha256": aborted["timber_semantic_sha256"],
            "history": aborted["history"],
            "after_visual": after_failure_visual,
        },
        "applied": {
            "object_count": len(applied["object_names"]),
            "ordinary_semantic_sha256": applied["ordinary_semantic_sha256"],
            "timber_semantic_sha256": applied["timber_semantic_sha256"],
            "history": applied["history"],
            "result": result_summary,
            "full_ordered_records": recipe.stable(
                result["resolved_timbers"]
            ),
            "stable_ordered_records": [
                module._b4_stable_record(item)
                for item in result["resolved_timbers"]
            ],
            "inherited_findings": recipe.stable(
                result["inherited_analysis"]["findings"]
            ),
            "resolved_findings": recipe.stable(
                result["resolved_analysis"]["findings"]
            ),
            "unresolved": recipe.stable(result["unresolved"]),
            "resolved_analysis": {
                "geometry_signature": applied_persistence["signature"],
                "analysis_basis": applied_persistence["analysis"]["analysis_basis"],
                "sha256": applied_persistence["analysis_sha256"],
                "stored_views_match": True,
                "full": applied_persistence["analysis"],
            },
            "shape": shape,
            "production_index": applied_index,
            "production_bindings": applied_bindings,
            "visuals": applied_visuals,
        },
        "unchanged_reuse": {
            "cache_reused": True,
            "resolved_analysis_sha256": recipe.digest(
                reused["resolved_analysis"]
            ),
            "document_and_history_unchanged": True,
        },
        "display_only": {
            "solver_calls": display_calls["solver"],
            "shape_calls": display_calls["shape"],
            "history_unchanged": True,
            "persistence_unchanged": True,
            "checkbox_matches_visibility": True,
            "reopened_hidden": True,
            "hidden_timber_semantic_sha256": hidden_saved[
                "timber_semantic_sha256"
            ],
            "hidden_reopen_semantic_sha256": hidden_saved[
                "reopen_semantic_sha256"
            ],
            "view_capture_changed_objects": view_capture_changed_objects,
            "hidden_visual": hidden_visual,
        },
        "undo": {
            "object_count": len(undone["object_names"]),
            "timber_semantic_sha256": undone["timber_semantic_sha256"],
            "history": undone["history"],
        },
        "redo": {
            "object_count": len(redone["object_names"]),
            "timber_semantic_sha256": redone["timber_semantic_sha256"],
            "history": redone["history"],
            "resolved_analysis_sha256": redone_persistence[
                "analysis_sha256"
            ],
        },
        "save_reopen": {
            "path": saved_path,
            "object_count": len(reopened["object_names"]),
            "timber_semantic_sha256": reopened["timber_semantic_sha256"],
            "reopen_semantic_sha256": reopened["reopen_semantic_sha256"],
            "history": reopened["history"],
            "resolved_analysis_sha256": reopened_persistence[
                "analysis_sha256"
            ],
            "production_index": reopened_index,
            "production_bindings": reopened_bindings,
            "visual": str(reopened_visual),
        },
    }, sort_keys=True))
finally:
    manager.close()
    QtWidgets.QApplication.processEvents()
'''


def _source_hashes():
    return {str(path.relative_to(ROOT)): sha256(path) for path in SOURCE_PATHS}


def _close_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for name in list(App.listDocuments()):
    App.closeDocument(name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('The B4 GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe, headless):
    if probe.get("sentinel") != PROBE_SENTINEL:
        raise RuntimeError("The real GUI probe did not return its PASS sentinel")
    if probe.get("matched_profile_id") != PROFILE:
        raise RuntimeError("The real GUI proof used a different qualified host")
    if (probe.get("routing") != {"route": "modular", "schema_version": 16}
            or probe.get("selected_binding")
            != "CrossoverB4RecoveryAdapter"
            or probe.get("host_a_identity", {}).get("object_name")
            != "RailwayStraightTrackCentreline_R01_T01"
            or probe.get("host_b_identity", {}).get("object_name")
            != "RailwayStraightTrackCentreline_R01_T02"
            or probe["source"]["object_count"] != 23
            or probe["source"]["ordinary_semantic_sha256"]
            != SOURCE_DOCUMENT_SEMANTIC):
        raise RuntimeError("The real GUI straight-host route changed")
    expected = headless["comparison"]["B16"]
    if probe["applied"]["result"] != expected["core"]:
        raise RuntimeError("GUI B4 records differ from B14/B15/B16 comparison")
    for field in (
        "full_ordered_records", "stable_ordered_records",
        "inherited_findings", "resolved_findings", "unresolved",
    ):
        if probe["applied"][field] != expected[field]:
            raise RuntimeError(
                "GUI B4 {} differ from the compared result".format(field)
            )
    if probe["applied"]["shape"] != expected["b4_object"]["shape"]["summary"]:
        raise RuntimeError("GUI B4 shape differs from the compared result")
    if (probe["applied"]["production_index"]
            != expected["production_index"]
            or probe["applied"]["production_bindings"]
            != expected["production_bindings"]
            or probe["before"]["production_index"]
            != expected["production_index"]
            or probe["before"]["production_bindings"]
            != expected["production_bindings"]
            or probe["save_reopen"]["production_index"]
            != expected["production_index"]
            or probe["save_reopen"]["production_bindings"]
            != expected["production_bindings"]):
        raise RuntimeError("GUI B4 changed compared production bindings")
    before = probe["before"]
    failure = probe["failure"]
    applied = probe["applied"]
    diagnostics = applied["resolved_analysis"]
    signature = diagnostics["geometry_signature"]
    digest = diagnostics["sha256"]
    full_analysis = diagnostics.get("full")
    if (not signature or len(digest) != 64
            or not isinstance(full_analysis, dict)
            or recipe.digest(full_analysis) != digest
            or full_analysis.get("geometry_signature") != signature
            or not isinstance(
                full_analysis.get("performance_timings_ms"), dict
            )
            or diagnostics["analysis_basis"]
            != "Effective automatically resolved timber arrangement"
            or diagnostics["stored_views_match"] is not True
            or probe["unchanged_reuse"]["cache_reused"] is not True
            or probe["unchanged_reuse"][
                "document_and_history_unchanged"
            ] is not True
            or probe["unchanged_reuse"]["resolved_analysis_sha256"]
            != digest
            or probe["redo"]["resolved_analysis_sha256"] != digest
            or probe["save_reopen"]["resolved_analysis_sha256"] != digest):
        raise RuntimeError("B4 resolved diagnostics were not stable in the GUI lifecycle")
    display = probe["display_only"]
    if (display["solver_calls"] != 0 or display["shape_calls"] != 0
            or display["history_unchanged"] is not True
            or display["persistence_unchanged"] is not True
            or display["checkbox_matches_visibility"] is not True
            or display["reopened_hidden"] is not True):
        raise RuntimeError("The GUI B4 visibility-only route changed calculation")
    if (before["object_count"] != 32
            or failure["object_count"] != 32
            or applied["object_count"] != 34
            or probe["undo"]["object_count"] != 32
            or probe["redo"]["object_count"] != 34
            or probe["save_reopen"]["object_count"] != 34
            or failure["first_tag_calls"] != 1):
        raise RuntimeError("Straight XO-001 B4 object lifecycle changed")
    if (failure["ordinary_semantic_sha256"] != before["ordinary_semantic_sha256"]
            or failure["timber_semantic_sha256"] != before["timber_semantic_sha256"]
            or failure["history"] != before["history"]
            or probe["undo"]["timber_semantic_sha256"] != before["timber_semantic_sha256"]
            or probe["redo"]["timber_semantic_sha256"] != applied["timber_semantic_sha256"]
            or probe["save_reopen"]["reopen_semantic_sha256"]
            != display["hidden_reopen_semantic_sha256"]):
        raise RuntimeError("B4 failure, Undo/Redo or save/reopen changed canonical state")
    return [
        before["visual"], failure["dialog"]["visual"],
        failure["after_visual"], *applied["visuals"],
        display["hidden_visual"], probe["save_reopen"]["visual"],
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-receipt", type=pathlib.Path, required=True,
        help="completed phase8-straight-host B14 source receipt",
    )
    parser.add_argument(
        "--headless-receipt", type=pathlib.Path, required=True,
        help="PASS straight XO-001 B14/B15/B16 B4 comparison receipt",
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated straight B4 GUI proof requires port 19875")
    source_receipt_path = args.source_receipt.resolve()
    headless_receipt_path = args.headless_receipt.resolve()
    if not source_receipt_path.is_file() or not headless_receipt_path.is_file():
        raise SystemExit("A B14 source or B4 headless receipt is absent")
    source_receipt = json.loads(
        source_receipt_path.read_text(encoding="utf-8")
    )
    if (source_receipt.get("recipe_id") != SOURCE_RECIPE
            or source_receipt.get("scenario") != "phase8-straight-host"
            or source_receipt.get("status") != "completed"
            or source_receipt.get("comparison_witness_sha256")
            != SOURCE_WITNESS
            or source_receipt.get("source_fixture_sha256_after")
            != source_receipt.get("source_fixture_sha256")
            or source_receipt["recipe"]["scenarios"][-1]["snapshot"][
                "semantic_sha256"
            ] != SOURCE_WITNESS
            or source_receipt["recipe"]["save_reopen"][
                "semantic_sha256"
            ] != SOURCE_WITNESS):
        raise SystemExit("The B14 straight-host source receipt is not accepted")
    base = pathlib.Path(source_receipt["run_document"]).resolve()
    if (not base.is_file()
            or sha256(base) != source_receipt.get("run_document_sha256")):
        raise SystemExit("The generated straight-host FCStd identity drifted")
    fixture_hash = sha256(base)
    headless = json.loads(headless_receipt_path.read_text(encoding="utf-8"))
    if (headless.get("status") != "PASS"
            or headless.get("sentinel") != HEADLESS_SENTINEL
            or headless.get("host_profile_id") != PROFILE
            or pathlib.Path(headless.get("source_fixture", "")).resolve()
            != base
            or headless.get("source_fixture_sha256") != fixture_hash
            or headless.get("source_fixture_sha256_after") != fixture_hash
            or pathlib.Path(headless.get("source_receipt", "")).resolve()
            != source_receipt_path
            or headless.get("source_receipt_sha256")
            != sha256(source_receipt_path)
            or headless.get("source_document_semantic_sha256")
            != SOURCE_DOCUMENT_SEMANTIC
            or headless["comparison"]["B14"]
            != headless["comparison"]["B15"]
            or headless["comparison"]["B15"]
            != headless["comparison"]["B16"]):
        raise SystemExit("The straight B4 comparison receipt is not accepted")
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not token.is_file():
        raise SystemExit("The isolated FreeCAD bridge token is absent")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    source_hashes = _source_hashes()
    source_receipt_hash = sha256(source_receipt_path)
    headless_receipt_hash = sha256(headless_receipt_path)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "straight-xo-001-b4.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-straight-crossover-b4-real-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_receipt": str(source_receipt_path),
        "source_receipt_sha256": source_receipt_hash,
        "headless_receipt": str(headless_receipt_path),
        "headless_receipt_sha256": headless_receipt_hash,
        "source_document_semantic_sha256": SOURCE_DOCUMENT_SEMANTIC,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "one B16 XO-001 on the B14-generated straight hosts; "
            "B4 first-tag rollback, apply, reuse, visibility, Undo/Redo, "
            "copied FCStd save/reopen and production bindings"
        ),
    }
    client = FreeCADClient(
        host="127.0.0.1", port=PORT, timeout=30.0,
        token=token.read_text(encoding="utf-8").strip(),
    )
    try:
        if not client.ping():
            raise RuntimeError("The isolated FreeCAD bridge did not answer ping")
        state["session_before"] = parse_json_output(execute_file(
            client, ROOT / "tools/freecad_bridge/probes/session_snapshot.py"
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The isolated FreeCAD session is not empty")
        state["opened"] = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('The straight B4 GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER_PATH.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 straight crossover B4 real GUI", args.timeout,
        )
        state["probe"] = parse_json_output(job)
        visuals = _check_probe(state["probe"], headless)
        if any(pathlib.Path(path).parent != run_dir for path in visuals):
            raise RuntimeError("The GUI probe returned an external image")
        state["visual_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in visuals
        }
        state["run_document_sha256"] = sha256(document_path)
        state["status"] = "PASS"
    except (Exception, SystemExit) as error:
        state["status"] = "FAIL"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        primary_failure = sys.exc_info()[0] is not None
        cleanup_failure = None
        try:
            state["cleanup"] = _close_documents(client)
        except Exception as error:
            cleanup_failure = error
            state["cleanup_error"] = "{}: {}".format(type(error).__name__, error)
        state["source_fixture_sha256_after"] = sha256(base)
        state["source_receipt_sha256_after"] = sha256(
            source_receipt_path
        )
        state["headless_receipt_sha256_after"] = sha256(
            headless_receipt_path
        )
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != fixture_hash
                or state["source_receipt_sha256_after"]
                != source_receipt_hash
                or state["headless_receipt_sha256_after"]
                != headless_receipt_hash
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError(
                "The B4 proof changed a source, receipt or fixture"
            )
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault(
                "error", "{}: {}".format(type(cleanup_failure).__name__, cleanup_failure)
            )
        state["retained_logs"] = {}
        for name in ("FreeCAD.log", "isolated-launcher.log"):
            source = ROOT / "benchmark-output/freecad-bridge" / name
            if source.is_file():
                try:
                    retained = run_dir / name
                    shutil.copy2(source, retained)
                    state["retained_logs"][name] = {
                        "path": str(retained), "sha256": sha256(retained),
                    }
                except Exception as error:
                    cleanup_failure = error
                    state["status"] = "FAIL"
                    state["log_retention_error"] = "{}: {}".format(
                        type(error).__name__, error
                    )
                    state.setdefault("error", state["log_retention_error"])
        state["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("Phase 8 straight B4 GUI evidence: {}".format(
            run_dir
        ), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
