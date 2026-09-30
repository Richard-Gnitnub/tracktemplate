#!/usr/bin/env python3
"""Prove one copied straight-host TO-001 lifecycle in the real FreeCAD GUI."""

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
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


PORT = 19875
SOURCE_RECIPE = "phase8-b14-straight-host-source-v1"
SOURCE_SEMANTIC_SHA256 = (
    "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
)
CONTRACT = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
LOADER = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = (
    ROOT / "benchmark-output/freecad-bridge/"
    "phase8-straight-host-turnout-gui-runs"
)
SENTINEL = "PHASE8_STRAIGHT_HOST_TURNOUT_GUI_PASS"
PROBE_SENTINEL = "PHASE8_STRAIGHT_HOST_TURNOUT_GUI_PROBE_PASS"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"


GUI_PROBE = r'''
import copy
import importlib.util
import json
import pathlib
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
identifier = "TO-001"
host_name = "RailwayStraightTrackCentreline_R01_T01"
route_id = "straight-phase1-curve-entrance"
toe_mm = 580.134
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied straight-host fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")


def history(active_document):
    return {
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(name) for name in active_document.UndoNames],
        "redo_names": [str(name) for name in active_document.RedoNames],
    }


def state(active_document):
    snapshot = ordinary_track_document_snapshot(module, active_document)
    settings = module.settings_for_template_set(active_document, "SET-001")
    if settings is None:
        raise RuntimeError("The copied source lost SET-001 settings")
    index = module.read_production_record_index(settings)
    if index is None or index.get("schema_version") != 2:
        raise RuntimeError("The copied source lost its production index")
    return {
        "semantic_sha256": snapshot["semantic_sha256"],
        "semantic": snapshot["semantic"],
        "object_names": sorted(str(obj.Name) for obj in active_document.Objects),
        "config": module.turnout_config_by_id(active_document, identifier),
        "records": index["records"],
        "history": history(active_document),
    }


def same_document(actual, expected, label):
    for key in (
        "semantic_sha256", "semantic", "object_names", "config", "records",
    ):
        if actual[key] != expected[key]:
            raise RuntimeError("{} changed copied document {}".format(label, key))


def same_history(actual, expected, label):
    if actual["history"] != expected["history"]:
        raise RuntimeError("{} changed Undo history".format(label))


def same_removed_source(actual, expected):
    """Permit only the B14-to-B15 record-index writer version change."""
    for key in ("object_names", "config", "records"):
        if actual[key] != expected[key]:
            raise RuntimeError("Remove changed source {}".format(key))
    original = copy.deepcopy(expected["semantic"])
    removed = copy.deepcopy(actual["semantic"])
    path = ("persistence", "settings", "values", "ProductionRecordIndexJSON")
    original_index = original
    removed_index = removed
    for key in path:
        original_index = original_index[key]
        removed_index = removed_index[key]
    original_version = original_index["macro_version"]
    removed_version = removed_index["macro_version"]
    if (original_version !=
            "10.2A8A7B14 WHOLE WORKFLOW BENCHMARK AND TEMPLOT STYLE 2D CHAIRS"
            or removed_version != str(module.MACRO_VERSION)):
        raise RuntimeError("Remove changed the known version boundary")
    original_index["macro_version"] = removed_version
    if original != removed:
        raise RuntimeError("Remove changed source semantics beyond version")
    return {
        "source_index_version": original_version,
        "removed_index_version": removed_version,
    }


def image_checked(path):
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("The GUI image is absent or invalid: " + str(path))
    return str(path)


def capture_manager(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    manager.show()
    manager.mode_tabs.setCurrentIndex(0)
    QtWidgets.QApplication.processEvents()
    if not manager.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture the turnout manager")
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


def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The inherited GUI choice is absent: " + value)
    combo.setCurrentIndex(index)


def run_dialogs(action, question_title=None, result_title=None,
                result_text=None, visual_prefix=None):
    seen = {
        "active": True, "questions": [], "results": [],
        "unexpected": [], "monitor_errors": [],
    }

    def monitor():
        if not seen["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if (not isinstance(widget, QtWidgets.QMessageBox)
                        or not widget.isVisible()):
                    continue
                title = str(widget.windowTitle())
                message = "{}\n{}".format(
                    widget.text(), widget.informativeText()
                )
                yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                item = {"title": title, "message": message}
                if visual_prefix is not None:
                    item["details"] = str(widget.detailedText())
                    item["visual"] = capture_widget(
                        widget, visual_prefix + ("-confirmation.png"
                        if yes is not None else "-summary.png"),
                    )
                if (question_title is not None and question_title in title
                        and yes is not None):
                    seen["questions"].append(item)
                    yes.click()
                elif (result_title is not None and result_title in title
                      and (result_text is None or result_text in message)):
                    seen["results"].append(item)
                    widget.accept()
                else:
                    seen["unexpected"].append({
                        "title": title, "message": message,
                    })
                    widget.reject()
        except Exception as error:
            seen["monitor_errors"].append(
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
        seen["active"] = False
    if (len(seen["questions"]) != int(question_title is not None)
            or len(seen["results"]) != int(result_title is not None)
            or seen["unexpected"] or seen["monitor_errors"]):
        raise RuntimeError("Straight turnout GUI dialogs changed: {}".format(
            seen
        ))
    return {key: value for key, value in seen.items() if key != "active"}


def capture_widget(widget, filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    QtWidgets.QApplication.processEvents()
    if not widget.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture " + filename)
    return image_checked(path)


def selected_export_from_main():
    """Use the main button and highlighted rows without object selection."""
    helper_path = (_PHASE3_REPOSITORY_ROOT
                   / "tests/freecad_validate_phase8_straight_host_turnout.py")
    spec = importlib.util.spec_from_file_location(
        "_straight_turnout_export_witness", helper_path,
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    if helper.ROOT != _PHASE3_REPOSITORY_ROOT:
        raise RuntimeError("The export witness came from another checkout")
    catalogue, outline, solid = helper._selected_pair(module, document)
    outline_id = outline["record_id"]
    pair_ids = {outline_id, solid["record_id"]}
    output = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / "selected-export"
    output.mkdir(exist_ok=False)
    baseline = helper._state(document)
    Gui.Selection.clearSelection()
    if module.selected_export_selection_snapshot(document, "SET-001"):
        raise RuntimeError("The highlighted-row proof has a FreeCAD selection")
    result = {
        "parent_count": 0, "button_clicks": 0, "child_count": 0,
        "error": None, "output": None,
    }
    parent_holder = {}

    def reject_dialogs():
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                widget.reject()

    def operate_child():
        child = None
        try:
            children = [
                item for item in QtWidgets.QApplication.topLevelWidgets()
                if isinstance(item, module.SelectedProductionExportDialog)
                and item.isVisible()
            ]
            if len(children) != 1:
                raise RuntimeError("The main button did not open one child")
            child = children[0]
            result["child_count"] += 1
            if child.parent() is not parent_holder["dialog"] or not child.isModal():
                raise RuntimeError("The export child lost modal parent ownership")
            result["child_modal"] = True
            result["child_parent_main"] = True
            child._loading_export_controls = True
            try:
                choose(child.scope_box, module.SELECTED_EXPORT_SCOPE_OBJECTS)
                child.output_box.setText(str(output))
                for key, box in child.format_boxes.items():
                    box.setChecked(key == module.EXPORT_FORMAT_SVG)
                child.export_each_section_box.setChecked(True)
                child.combined_box.setChecked(False)
                child.manifest_box.setChecked(True)
                child.overwrite_box.setChecked(False)
                child.probe_box.setChecked(True)
            finally:
                child._loading_export_controls = False
            child.refresh_preview()
            if (child.scope.get("selected_objects")
                    or len(child.preview_records) != len(catalogue)
                    or child.matching_records or child.export_records
                    or child.plan
                    or [issue["issue_code"] for issue in child.issues]
                    != ["NO_SELECTED_PRODUCTION_ITEMS"]):
                raise RuntimeError("The unselected export preview changed")
            column = module.SELECTED_EXPORT_RECORD_FIELDS.index(
                "Production-record ID"
            )
            rows = [row for row in range(child.records_table.rowCount())
                    if child.records_table.item(row, column) is not None
                    and child.records_table.item(row, column).text() == outline_id]
            if len(rows) != 1:
                raise RuntimeError("The straight TO-001 outline row is not unique")
            child.records_table.selectRow(rows[0])
            if child._highlighted_record_ids() != {outline_id}:
                raise RuntimeError("The TO-001 outline row was not highlighted")
            child.refresh_preview()
            child.refresh_preview()
            plan = child.plan or {}
            result["preview"] = {
                "issues": child.issues,
                "highlighted_ids": sorted(child._highlighted_record_ids()),
                "matching_ids": [item["record_id"]
                                 for item in child.matching_records],
                "record_ids": [item["record_id"] for item in child.export_records],
                "summary": str(child.summary_label.text()),
                "visual": capture_widget(
                    child, "straight-turnout-export-preflight.png",
                ),
            }
            if (child._highlighted_record_ids() != pair_ids
                    or set(child.scope.get("highlighted_record_ids") or []) != pair_ids
                    or {item["record_id"] for item in child.matching_records} != pair_ids
                    or {item["route_id"] for item in child.matching_records} != {route_id}
                    or result["preview"]["record_ids"] != [outline_id]
                    or len(plan.get("tasks") or []) != 1
                    or plan["tasks"][0]["format"] != "svg"
                    or not plan.get("manifest_path")
                    or module.preflight_blocking_report(child.issues)
                    or not child.export_button.isEnabled()
                    or child.export_button.text() != "Export 2 highlighted rows"):
                raise RuntimeError("The straight export preflight changed: "
                                   + str(result["preview"]))
            if helper._state(document) != baseline:
                raise RuntimeError("The export preview changed document or Undo")
            result["dialogs"] = run_dialogs(
                child.export_button.click,
                question_title="Confirm selected production export",
                result_title="Production export complete",
                result_text="Successful files: 2",
                visual_prefix="straight-turnout-export",
            )
            summary = result["dialogs"]["results"][0]["message"]
            confirmation = result["dialogs"]["questions"][0]["message"]
            if ("Failed files: 0" not in summary
                    or "Formats produced: SVG" not in summary
                    or "Production records selected for this operation: 2"
                    not in confirmation
                    or "Records with compatible selected formats: 1"
                    not in confirmation
                    or "Files to produce: 2" not in confirmation):
                raise RuntimeError("The export confirmation or summary changed")
            result["output"] = helper._selected_export_output(
                module, output, plan, outline, solid,
            )
            if helper._state(document) != baseline:
                raise RuntimeError("The export changed document or Undo history")
            result["document_and_undo_unchanged"] = True
        except Exception:
            result["error"] = traceback.format_exc()
            reject_dialogs()
        finally:
            if child is not None:
                child.close()

    def operate_parent():
        try:
            parents = [item for item in QtWidgets.QApplication.topLevelWidgets()
                       if isinstance(item, module.CurveInputDialog)
                       and item.isVisible()]
            if len(parents) != 1:
                raise RuntimeError("The B16 workflow did not open one main dialog")
            parent = parents[0]
            parent_holder["dialog"] = parent
            result["parent_count"] += 1
            button = parent.selected_export_button
            if not button.isVisible() or not button.isEnabled():
                raise RuntimeError("The main export button is unavailable")
            result["button_text"] = str(button.text())
            scroll = button.parent()
            while scroll is not None and not isinstance(scroll, QtWidgets.QScrollArea):
                scroll = scroll.parent()
            if scroll is not None:
                scroll.ensureWidgetVisible(button)
            result["parent_visual"] = capture_widget(
                parent, "straight-turnout-main-export.png",
            )
            QtCore.QTimer.singleShot(0, operate_child)
            result["button_clicks"] += 1
            button.click()
            parent.reject()
        except Exception:
            result["error"] = traceback.format_exc()
            reject_dialogs()

    def timeout():
        if result["output"] is None and result["error"] is None:
            result["error"] = "The main export route timed out"
            reject_dialogs()

    deadline = QtCore.QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(timeout)
    manager.hide()
    QtCore.QTimer.singleShot(0, operate_parent)
    deadline.start(300000)
    try:
        _PHASE3_SESSION.launch_workflow()
    finally:
        deadline.stop()
        (output.parent / "selected-export-proof.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manager.show()
    if result["error"] is not None:
        raise RuntimeError(result["error"])
    if (result["parent_count"] != 1 or result["button_clicks"] != 1
            or result["child_count"] != 1 or result["output"] is None):
        raise RuntimeError("The main export route was incomplete")
    return result


manager = module.TurnoutManagerDialog(document)
manager.show()
manager.mode_tabs.setCurrentIndex(0)
QtWidgets.QApplication.processEvents()
try:
    document.UndoMode = 1
    before = state(document)
    if (len(before["object_names"]) != 23 or len(before["records"]) != 12
            or before["config"] is not None
            or before["history"]["undo_count"]):
        raise RuntimeError("The copied straight-host source changed")
    manager.refresh_hosts()
    matches = [
        index for index, host in enumerate(manager.hosts)
        if host.Name == host_name
        and module.object_string_property(host, "TemplateSetID", "")
        == "SET-001"
        and module.object_string_property(host, "RouteID", "") == route_id
        and module.object_string_property(host, "GeneratedRole", "")
        == "StraightTrackCentreline"
        and module._integer_object_property(host, "TrackNumber", 0) == 1
    ]
    if len(matches) != 1:
        raise RuntimeError("The GUI did not find the selected straight host")
    manager.host_combo.setCurrentIndex(matches[0])
    choose(manager.handing_combo, module.TURNOUT_HAND_LEFT)
    choose(manager.orientation_combo, module.TURNOUT_ORIENTATION_FACING)
    manager.gauge_box.setValue(16.5)
    manager.flangeway_box.setValue(1.0)
    host = manager.current_host()
    host_data = module.turnout_host_alignment(host)
    minimum, maximum = module.turnout_valid_toe_range(
        host_data["total"], module.rea_c10_dimensions(16.5, 1.0),
        module.TURNOUT_ORIENTATION_FACING,
    )
    if not minimum < toe_mm < maximum:
        raise RuntimeError("The selected straight toe is outside valid range")
    manager.chainage_box.setValue(toe_mm)
    if float(manager.chainage_box.value()) != toe_mm:
        raise RuntimeError("The GUI changed the selected straight toe")
    before_visual = capture_manager("straight-turnout-before-manager.png")

    create_dialog = run_dialogs(
        manager.create_turnout, result_title="REA C10 turnout created",
        result_text="Created TO-001",
    )
    manager.refresh_turnouts(selected_id=identifier)
    created = state(document)
    if (len(created["object_names"]) != 31
            or len(created["records"]) != 18
            or created["config"] is None
            or created["config"]["host_object"] != host_name
            or created["config"]["route_id"] != route_id
            or created["config"]["toe_chainage"] != toe_mm
            or created["history"]["undo_count"] != 1
            or created["history"]["redo_count"]):
        raise RuntimeError("GUI Create did not persist straight TO-001")
    source_record_ids = [item["record_id"] for item in before["records"]]
    created_record_ids = [item["record_id"] for item in created["records"]]
    if created_record_ids[:12] != source_record_ids:
        raise RuntimeError("GUI Create reordered the source production records")
    created_roles = {
        module.object_string_property(obj, "GeneratedRole", ""): obj.Name
        for obj in document.Objects
        if module.object_string_property(obj, "TurnoutID", "") == identifier
    }
    if len(created_roles) != 8:
        raise RuntimeError("GUI Create lost turnout object identity")
    created_visuals = [
        capture_manager("straight-turnout-created-manager.png"),
        capture_top("straight-turnout-created-top.png"),
    ]

    rejected_dialog = run_dialogs(
        manager.create_turnout, result_title="Turnout creation error",
        result_text="overlaps TO-001",
    )
    rejected = state(document)
    same_document(rejected, created, "Rejected overlapping Create")
    same_history(rejected, created, "Rejected overlapping Create")

    selected_export = selected_export_from_main()
    same_document(state(document), created, "Selected export")
    same_history(state(document), created, "Selected export")

    manager.refresh_turnouts(selected_id=identifier)
    manager.begin_edit_turnout()
    if manager.editing_turnout_id != identifier:
        raise RuntimeError("The manager did not enter TO-001 edit mode")
    choose(manager.handing_combo, module.TURNOUT_HAND_RIGHT)
    manager.update_host_summary()
    edit_dialogs = run_dialogs(
        manager.apply_turnout_edit,
        question_title="Apply turnout changes",
        result_title="REA C10 turnout updated",
        result_text="Updated TO-001",
    )
    edited = state(document)
    if (len(edited["object_names"]) != 31
            or edited["config"]["handing"] != module.TURNOUT_HAND_RIGHT
            or edited["config"]["host_object"] != host_name
            or edited["history"]["undo_count"] != 2
            or edited["history"]["redo_count"]
            or edited["semantic_sha256"] == created["semantic_sha256"]):
        raise RuntimeError("GUI Edit did not retain straight TO-001 identity")
    edited_record_ids = [item["record_id"] for item in edited["records"]]
    if edited_record_ids != created_record_ids:
        raise RuntimeError("GUI Edit changed production record IDs or order")
    edited_roles = {
        module.object_string_property(obj, "GeneratedRole", ""): obj.Name
        for obj in document.Objects
        if module.object_string_property(obj, "TurnoutID", "") == identifier
    }
    if edited_roles != created_roles:
        raise RuntimeError("GUI Edit changed turnout object names")
    edited_visuals = [
        capture_manager("straight-turnout-edited-manager.png"),
        capture_top("straight-turnout-edited-top.png"),
    ]

    document.undo()
    document.recompute()
    edit_undone = state(document)
    same_document(edit_undone, created, "Edit Undo")
    if edit_undone["history"]["undo_count"] != 1:
        raise RuntimeError("Edit Undo changed transaction count")
    document.redo()
    document.recompute()
    edit_redone = state(document)
    same_document(edit_redone, edited, "Edit Redo")
    same_history(edit_redone, edited, "Edit Redo")

    manager.refresh_turnouts(selected_id=identifier)
    manager.begin_edit_turnout()
    choose(manager.handing_combo, module.TURNOUT_HAND_LEFT)
    manager.update_host_summary()
    original_tagger = module.tag_generated_object
    fault_calls = {"count": 0}
    fault_text = "Phase 8 injected straight-turnout edit failure"

    def failing_tagger(*args, **kwargs):
        fault_calls["count"] += 1
        raise RuntimeError(fault_text)

    module.tag_generated_object = failing_tagger
    try:
        fault_dialogs = run_dialogs(
            manager.apply_turnout_edit,
            question_title="Apply turnout changes",
            result_title="Turnout edit error",
            result_text=fault_text,
        )
    finally:
        module.tag_generated_object = original_tagger
    if fault_calls["count"] != 1:
        raise RuntimeError("The edit fault did not reach its first object tag")
    aborted = state(document)
    same_document(aborted, edited, "Aborted Edit")
    same_history(aborted, edited, "Aborted Edit")
    manager.cancel_turnout_edit()
    manager.close()
    QtWidgets.QApplication.processEvents()

    document.save()
    saved = state(document)
    saved_path = str(document.FileName)
    App.closeDocument(document.Name)
    document = App.openDocument(saved_path)
    reopened = state(document)
    same_document(reopened, saved, "Edited save/reopen")
    if reopened["history"]["undo_count"]:
        raise RuntimeError("Edited reopen retained Undo history")
    manager = module.TurnoutManagerDialog(document)
    manager.refresh_turnouts(selected_id=identifier)
    reopened_visual = capture_top("straight-turnout-reopened-top.png")

    remove_dialog = run_dialogs(
        manager.remove_turnout, question_title="Remove turnout",
    )
    removed = state(document)
    if (len(removed["object_names"]) != 23
            or len(removed["records"]) != 12
            or removed["config"] is not None
            or removed["history"]["undo_count"] != 1):
        raise RuntimeError("GUI Remove did not restore source identities")
    if [item["record_id"] for item in removed["records"]] != source_record_ids:
        raise RuntimeError("GUI Remove changed source production record IDs")
    remove_version_rebind = same_removed_source(removed, before)
    removed_visual = capture_top("straight-turnout-removed-top.png")

    document.undo()
    document.recompute()
    remove_undone = state(document)
    same_document(remove_undone, reopened, "Remove Undo")
    document.redo()
    document.recompute()
    remove_redone = state(document)
    same_document(remove_redone, removed, "Remove Redo")
    manager.close()
    QtWidgets.QApplication.processEvents()
    document.save()
    removed_saved = state(document)
    App.closeDocument(document.Name)
    document = App.openDocument(saved_path)
    removed_reopened = state(document)
    same_document(removed_reopened, removed_saved, "Removed save/reopen")
    if removed_reopened["history"]["undo_count"]:
        raise RuntimeError("Removed reopen retained Undo history")

    print(json.dumps({
        "sentinel": "PHASE8_STRAIGHT_HOST_TURNOUT_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "host_name": host_name,
        "route_id": route_id,
        "toe_mm": toe_mm,
        "source_object_count": len(before["object_names"]),
        "source_record_count": len(before["records"]),
        "created_object_count": len(created["object_names"]),
        "created_record_count": len(created["records"]),
        "edited_record_ids": edited_record_ids,
        "created_record_ids": created_record_ids,
        "removed_object_count": len(removed["object_names"]),
        "removed_record_count": len(removed["records"]),
        "remove_version_rebind": remove_version_rebind,
        "created_semantic_sha256": created["semantic_sha256"],
        "edited_semantic_sha256": edited["semantic_sha256"],
        "reopened_semantic_sha256": reopened["semantic_sha256"],
        "removed_semantic_sha256": removed["semantic_sha256"],
        "removed_reopened_semantic_sha256": (
            removed_reopened["semantic_sha256"]
        ),
        "created_history": created["history"],
        "edited_history": edited["history"],
        "removed_history": removed["history"],
        "fault_calls": fault_calls["count"],
        "selected_export": selected_export,
        "dialogs": {
            "create": create_dialog,
            "rejected": rejected_dialog,
            "edit": edit_dialogs,
            "fault": fault_dialogs,
            "remove": remove_dialog,
        },
        "visuals": [
            before_visual, *created_visuals, *edited_visuals,
            reopened_visual, removed_visual,
        ],
    }, sort_keys=True))
finally:
    try:
        manager.close()
    except Exception:
        pass
    QtWidgets.QApplication.processEvents()
'''


def _source_hashes():
    paths = [
        ROOT / "AdvancedTurnout.FCMacro",
        ROOT / "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
        ROOT / "TrackTemplate.FCMacro",
        LOADER,
        ROOT / "tools/freecad_bridge/run_b14_straight_station.py",
        ROOT / "tools/freecad_bridge/probes/b14_straight_station_driver.py",
        pathlib.Path(__file__).resolve(),
        ROOT / "tools/freecad_bridge/run-phase8-straight-host-turnout-gui",
        ROOT / "tests/freecad_validate_phase8_straight_host_turnout.py",
        ROOT / "tools/freecad_bridge/ordinary_track_export_recipe.py",
        *sorted((ROOT / "tracktemplate").rglob("*.py")),
    ]
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def _close_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for name in list(App.listDocuments()):
    App.closeDocument(name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('The GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != PROBE_SENTINEL:
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if probe.get("matched_profile_id") != PROFILE:
        raise RuntimeError("The GUI proof used another FreeCAD profile")
    if (probe.get("host_name")
            != "RailwayStraightTrackCentreline_R01_T01"
            or probe.get("route_id") != "straight-phase1-curve-entrance"
            or probe.get("toe_mm") != 580.134
            or probe.get("source_object_count") != 23
            or probe.get("source_record_count") != 12
            or probe.get("created_object_count") != 31
            or probe.get("created_record_count") != 18
            or probe.get("removed_object_count") != 23
            or probe.get("removed_record_count") != 12
            or probe.get("fault_calls") != 1
            or probe["created_semantic_sha256"]
            == probe["edited_semantic_sha256"]
            or probe["edited_semantic_sha256"]
            != probe["reopened_semantic_sha256"]
            or probe["removed_semantic_sha256"]
            != probe["removed_reopened_semantic_sha256"]):
        raise RuntimeError("The GUI lifecycle proof changed")
    export = probe["selected_export"]
    if (export["parent_count"] != 1 or export["button_clicks"] != 1
            or export["child_count"] != 1
            or export["child_modal"] is not True
            or export["child_parent_main"] is not True
            or export["document_and_undo_unchanged"] is not True
            or export["button_text"] != "Export selected items..."
            or len(export["output"]["artifacts"]["files"]) != 2):
        raise RuntimeError("The main selected-export proof changed")
    return [
        *probe["visuals"], export["parent_visual"],
        export["preview"]["visual"],
        export["dialogs"]["questions"][0]["visual"],
        export["dialogs"]["results"][0]["visual"],
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-receipt", type=pathlib.Path, required=True,
        help="PASS receipt from run-b14-straight-station --scenario phase8-straight-host",
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated GUI proof requires port 19875")
    receipt_path = args.source_receipt.resolve()
    if not receipt_path.is_file():
        raise SystemExit("The B14 source-generation receipt is absent")
    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (source_receipt.get("recipe_id") != SOURCE_RECIPE
            or source_receipt.get("scenario") != "phase8-straight-host"
            or source_receipt.get("status") != "completed"
            or source_receipt.get("comparison_witness_sha256")
            != SOURCE_SEMANTIC_SHA256
            or source_receipt.get("source_fixture_sha256_after")
            != source_receipt.get("source_fixture_sha256")
            or source_receipt["recipe"]["scenarios"][-1]["snapshot"][
                "semantic_sha256"
            ] != SOURCE_SEMANTIC_SHA256
            or source_receipt["recipe"]["save_reopen"][
                "semantic_sha256"
            ] != SOURCE_SEMANTIC_SHA256):
        raise SystemExit("The B14 straight-host source receipt is not accepted")
    base = pathlib.Path(source_receipt["run_document"]).resolve()
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not base.is_file() or not token.is_file():
        raise SystemExit("The source fixture or isolated bridge token is absent")
    if sha256(base) != source_receipt.get("run_document_sha256"):
        raise SystemExit("The generated B14 straight-host FCStd identity drifted")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    source_hashes = _source_hashes()
    fixture_hash = sha256(base)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "straight-host-turnout.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-straight-host-turnout-real-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_receipt": str(receipt_path),
        "source_receipt_sha256": sha256(receipt_path),
        "source_semantic_sha256": SOURCE_SEMANTIC_SHA256,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "one straight-host TO-001 manager Create/Edit/Remove; rejection, "
            "aborted edit, Undo/Redo, copied FCStd save/reopen and "
            "main-button highlighted-row private SVG/CSV export"
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
    raise RuntimeError('The straight-host GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 straight-host turnout real GUI", args.timeout,
        )
        state["probe"] = parse_json_output(job)
        visuals = _check_probe(state["probe"])
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
            state["cleanup_error"] = "{}: {}".format(
                type(error).__name__, error
            )
        state["source_fixture_sha256_after"] = sha256(base)
        state["source_receipt_sha256_after"] = sha256(receipt_path)
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != fixture_hash
                or state["source_receipt_sha256_after"]
                != state["source_receipt_sha256"]
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError(
                "The GUI proof changed a source or the source fixture"
            )
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault("error", "{}: {}".format(
                type(cleanup_failure).__name__, cleanup_failure
            ))
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
        state["finished_utc"] = (
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Phase 8 straight-host turnout GUI evidence: {}".format(
            run_dir
        ), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
