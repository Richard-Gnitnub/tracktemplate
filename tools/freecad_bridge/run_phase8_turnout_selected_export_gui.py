#!/usr/bin/env python3
"""Exercise copied TO-001 selected export in the qualified FreeCAD GUI."""

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
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
LOADER = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = (
    ROOT / "benchmark-output/freecad-bridge/"
    "phase8-turnout-selected-export-gui-runs"
)
SENTINEL = "PHASE8_TURNOUT_SELECTED_EXPORT_GUI_PASS"
PROBE_SENTINEL = "PHASE8_TURNOUT_SELECTED_EXPORT_GUI_PROBE_PASS"


GUI_PROBE = r'''
import csv
import json
import pathlib
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import turnout_recipe
from tracktemplate.compatibility.turnout_host_integration_recovery import (
    TurnoutHostIntegrationRecoveryAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied TO-001 fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")
adapter = getattr(module.create_turnout_host_integration, "__self__", None)
if (not isinstance(adapter, TurnoutHostIntegrationRecoveryAdapter)
        or adapter.module is not module
        or getattr(module.create_turnout_host_integration, "__func__", None)
        is not TurnoutHostIntegrationRecoveryAdapter.create):
    raise RuntimeError("The host-integration action is not routed through B16")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(value) for value in active_document.UndoNames],
    }


def index_state(active_document):
    config = module.turnout_config_by_id(active_document, "TO-001")
    if not isinstance(config, dict):
        raise RuntimeError("The fixed TO-001 configuration is unavailable")
    set_id = str(config.get("template_set_id") or "")
    settings = module.settings_for_template_set(active_document, set_id)
    index = module.read_production_record_index(settings)
    if not isinstance(index, dict):
        raise RuntimeError("The persistent production index is unavailable")
    return {
        "set_id": set_id,
        "config": config,
        "integration": module.turnout_integration_by_id(
            active_document, "TO-001"
        ),
        "index": index,
        "object_names": sorted(str(obj.Name) for obj in active_document.Objects),
        "history": history(active_document),
    }


def image_checked(path):
    path = pathlib.Path(path)
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("The GUI image is absent or invalid: {}".format(path))
    return str(path)


def capture_widget(widget, filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    QtWidgets.QApplication.processEvents()
    if not widget.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture {}".format(filename))
    return image_checked(path)


def capture_top(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(path), 1600, 1000, "Current")
    return image_checked(path)


def run_action_dialogs(action, question_title=None, result_title=None):
    seen = {
        "questions": [], "results": [], "unexpected": [],
        "monitor_errors": [], "active": True,
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
                yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                message = "{}\n{}".format(
                    widget.text(), widget.informativeText()
                )
                if (question_title is not None
                        and question_title in title and yes is not None):
                    seen["questions"].append({
                        "title": title, "message": message,
                    })
                    yes.click()
                elif result_title is not None and result_title in title:
                    seen["results"].append({
                        "title": title, "message": message,
                    })
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
            or seen["unexpected"]
            or seen["monitor_errors"]):
        raise RuntimeError("The TO-001 action dialogs changed: {}".format(
            seen
        ))
    return {
        "question": seen["questions"][0] if seen["questions"] else None,
        "result": seen["results"][0] if seen["results"] else None,
    }


def export_dialog_action(dialog):
    seen = {
        "confirmations": [], "summaries": [], "unexpected": [],
        "monitor_errors": [], "active": True,
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
                item = {
                    "title": title,
                    "text": str(widget.text()),
                    "information": str(widget.informativeText()),
                    "details": str(widget.detailedText()),
                }
                if "Confirm selected production export" in title:
                    item["visual"] = capture_widget(
                        widget, "to-001-selected-export-confirmation.png"
                    )
                    seen["confirmations"].append(item)
                    yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                    if yes is None:
                        raise RuntimeError("Selected export has no Yes action")
                    yes.click()
                elif "Production export complete" in title:
                    item["visual"] = capture_widget(
                        widget, "to-001-selected-export-summary.png"
                    )
                    seen["summaries"].append(item)
                    widget.accept()
                else:
                    seen["unexpected"].append(item)
                    widget.reject()
        except Exception as error:
            seen["monitor_errors"].append(
                "{}: {}".format(type(error).__name__, error)
            )
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    QtCore.QTimer.singleShot(0, monitor)
    try:
        dialog.export_button.click()
    finally:
        seen["active"] = False
    if (len(seen["confirmations"]) != 1
            or len(seen["summaries"]) != 1
            or seen["unexpected"] or seen["monitor_errors"]):
        raise RuntimeError("The selected export dialogs changed: {}".format(seen))
    return seen


def exercise_selected_export(dialog):
    try:
        if dialog.current_set_id() != reopened["set_id"]:
            raise RuntimeError("The selected export template set changed")
        scope_index = dialog.scope_box.findText(
            module.SELECTED_EXPORT_SCOPE_OBJECTS
        )
        if scope_index < 0:
            raise RuntimeError("Selected FreeCAD objects scope is absent")
        dialog._loading_export_controls = True
        try:
            dialog.scope_box.setCurrentIndex(scope_index)
            dialog.output_box.setText(TRACKTEMPLATE_PHASE8_OUTPUT_DIR)
            for key, box in dialog.format_boxes.items():
                box.setChecked(key == module.EXPORT_FORMAT_SVG)
            dialog.export_each_section_box.setChecked(True)
            dialog.combined_box.setChecked(False)
            dialog.manifest_box.setChecked(True)
            dialog.overwrite_box.setChecked(False)
            dialog.probe_box.setChecked(True)
        finally:
            dialog._loading_export_controls = False
        dialog.refresh_preview()
        if (dialog.scope.get("selected_objects")
                or len(dialog.preview_records) != 8
                or dialog.matching_records
                or dialog.export_records
                or dialog.plan
                or [issue.get("issue_code") for issue in dialog.issues]
                != ["NO_SELECTED_PRODUCTION_ITEMS"]):
            raise RuntimeError("The highlighted-row candidate state changed")
        id_column = module.SELECTED_EXPORT_RECORD_FIELDS.index(
            "Production-record ID"
        )
        outline_rows = [
            row for row in range(dialog.records_table.rowCount())
            if (dialog.records_table.item(row, id_column) is not None
                and dialog.records_table.item(row, id_column).text()
                == outline_id)
        ]
        if len(outline_rows) != 1:
            raise RuntimeError("The integrated outline row is not unique")
        dialog.records_table.selectRow(outline_rows[0])
        if dialog._highlighted_record_ids() != {outline_id}:
            raise RuntimeError("The integrated outline row was not highlighted")
        dialog.refresh_preview()
        expanded_ids = {
            str(record.get("record_id") or "")
            for record in dialog.matching_records
        }
        if (expanded_ids != integrated_ids
                or {str(record.get("category") or "")
                    for record in dialog.matching_records}
                != {module.EXPORT_CATEGORY_SOLID,
                    module.EXPORT_CATEGORY_CUTTING}
                or {str(record.get("route_id") or "")
                    for record in dialog.matching_records} != {""}
                or {str(record.get("source_name") or "")
                    for record in dialog.matching_records}
                != {outline_name, solid_name}
                or dialog._highlighted_record_ids() != expanded_ids):
            raise RuntimeError("The highlighted TO-001 pair changed")
        dialog.refresh_preview()
        if (dialog._highlighted_record_ids() != expanded_ids
                or set(dialog.scope.get("highlighted_record_ids") or [])
                != expanded_ids):
            raise RuntimeError("The highlighted-row scope did not stabilise")
        plan = dialog.plan or {}
        tasks = list(plan.get("tasks") or [])
        selected_ids = {
            str(record.get("record_id") or "")
            for record in dialog.export_records
        }
        blocking = module.preflight_blocking_report(dialog.issues)
        issue_codes = [
            str(issue.get("issue_code") or "") for issue in dialog.issues
        ]
        if (selected_ids != {outline_id}
                or len(dialog.matching_records) != 2
                or len(tasks) != 1
                or str(tasks[0].get("format") or "") != "svg"
                or str(tasks[0].get("records", [{}])[0].get("record_id")
                       or "") != outline_id
                or not plan.get("manifest_path")
                or blocking
                or dialog.export_button.text()
                != "Export 2 highlighted rows"
                or not dialog.export_button.isEnabled()):
            raise RuntimeError("Selected export preflight changed: {}".format({
                "ids": sorted(selected_ids),
                "highlighted_ids": sorted(dialog._highlighted_record_ids()),
                "tasks": len(tasks),
                "issues": issue_codes,
                "blocking": blocking,
                "summary": dialog.summary_label.text(),
            }))
        preview = {
            "scope": dialog.scope,
            "highlighted_ids": sorted(dialog._highlighted_record_ids()),
            "matching_record_ids": sorted(expanded_ids),
            "record_ids": sorted(selected_ids),
            "plan_paths": sorted(
                [str(task.get("path") or "") for task in tasks]
                + [str(plan.get("manifest_path"))]
            ),
            "issue_codes": issue_codes,
            "issues": dialog.issues,
            "summary": str(dialog.summary_label.text()),
            "action": str(dialog.export_button.text()),
            "visual": capture_widget(
                dialog, "to-001-selected-export-preflight.png"
            ),
        }
        before_export = index_state(document)
        dialogs = export_dialog_action(dialog)
        after_export = index_state(document)
        if (after_export["index"] != before_export["index"]
                or after_export["config"] != before_export["config"]
                or after_export["integration"]
                != before_export["integration"]
                or after_export["object_names"]
                != before_export["object_names"]
                or after_export["history"] != before_export["history"]):
            raise RuntimeError("Selected export changed the copied document")
    finally:
        dialog.close()
        Gui.Selection.clearSelection()
        QtWidgets.QApplication.processEvents()

    return {
        "preview": preview,
        "before_export": before_export,
        "after_export": after_export,
        "dialogs": dialogs,
        "plan": plan,
        "tasks": tasks,
    }


def run_main_button_export():
    state = {
        "parent_count": 0,
        "button_clicks": 0,
        "child_count": 0,
        "result": None,
        "error": None,
    }
    parent_holder = {}

    def reject_visible_dialogs():
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                widget.reject()

    def operate_child():
        try:
            children = [
                widget for widget in QtWidgets.QApplication.topLevelWidgets()
                if isinstance(widget, module.SelectedProductionExportDialog)
                and widget.isVisible()
            ]
            if len(children) != 1:
                raise RuntimeError(
                    "Main selected-export button opened {} children".format(
                        len(children)
                    )
                )
            child = children[0]
            parent = parent_holder["dialog"]
            if child.parent() is not parent or not child.isModal():
                raise RuntimeError(
                    "Main selected-export child lost modal parent ownership"
                )
            state["child_count"] += 1
            state["child_title"] = str(child.windowTitle())
            state["child_modal"] = bool(child.isModal())
            state["child_parent_main"] = child.parent() is parent
            state["result"] = exercise_selected_export(child)
        except Exception:
            state["error"] = traceback.format_exc()
            reject_visible_dialogs()

    def operate_parent():
        try:
            parents = [
                widget for widget in QtWidgets.QApplication.topLevelWidgets()
                if isinstance(widget, module.CurveInputDialog)
                and widget.isVisible()
            ]
            if len(parents) != 1:
                raise RuntimeError(
                    "B16 workflow opened {} main dialogs".format(
                        len(parents)
                    )
                )
            parent = parents[0]
            parent_holder["dialog"] = parent
            state["parent_count"] += 1
            button = parent.selected_export_button
            if not button.isVisible() or not button.isEnabled():
                raise RuntimeError("Main selected-export button is unavailable")
            state["parent_title"] = str(parent.windowTitle())
            state["button_text"] = str(button.text())
            scroll = button.parent()
            while (scroll is not None
                   and not isinstance(scroll, QtWidgets.QScrollArea)):
                scroll = scroll.parent()
            if scroll is not None:
                scroll.ensureWidgetVisible(button)
            QtWidgets.QApplication.processEvents()
            state["parent_visual"] = capture_widget(
                parent, "to-001-main-selected-export-panel.png"
            )
            state["main_visual"] = capture_widget(
                button, "to-001-main-selected-export-button.png"
            )
            QtCore.QTimer.singleShot(0, operate_child)
            state["button_clicks"] += 1
            button.click()
            parent.reject()
        except Exception:
            state["error"] = traceback.format_exc()
            reject_visible_dialogs()

    def timeout():
        if state["result"] is None and state["error"] is None:
            state["error"] = "Main selected-export route timed out"
            reject_visible_dialogs()

    deadline = QtCore.QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(timeout)
    QtCore.QTimer.singleShot(0, operate_parent)
    deadline.start(300000)
    try:
        _PHASE3_SESSION.launch_workflow()
    finally:
        deadline.stop()
    if state["error"] is not None:
        raise RuntimeError(state["error"])
    if (state["parent_count"] != 1
            or state["button_clicks"] != 1
            or state["child_count"] != 1
            or state["result"] is None):
        raise RuntimeError("Main selected-export route was incomplete")
    route = {
        key: value for key, value in state.items()
        if key not in {"result", "error"}
    }
    return {"route": route, "result": state["result"]}


manager = module.TurnoutManagerDialog(document)
manager.show()
manager.mode_tabs.setCurrentIndex(0)
QtWidgets.QApplication.processEvents()

try:
    if len(document.Objects) != 9 or history(document)["undo_count"]:
        raise RuntimeError("The copied B14 fixture changed")
    document.UndoMode = 1
    manager.refresh_hosts()
    selection = turnout_recipe.select_turnout_host(
        manager.hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    manager.host_combo.setCurrentIndex(selection["index"])
    for combo, value in (
        (manager.handing_combo, module.TURNOUT_HAND_LEFT),
        (manager.orientation_combo, module.TURNOUT_ORIENTATION_FACING),
    ):
        index = combo.findText(value)
        if index < 0:
            raise RuntimeError("The fixed TO-001 GUI choice is absent")
        combo.setCurrentIndex(index)
    manager.gauge_box.setValue(turnout_recipe.TRACK_GAUGE_MM)
    manager.flangeway_box.setValue(turnout_recipe.FLANGEWAY_MM)
    manager.chainage_box.setValue(turnout_recipe.TURNOUT_CHAINAGE_MM)
    creation = run_action_dialogs(
        manager.create_turnout, result_title="REA C10 turnout created"
    )
    manager.refresh_turnouts(selected_id="TO-001")
    if manager.current_turnout_config()["turnout_id"] != "TO-001":
        raise RuntimeError("The manager did not select TO-001")
    manager.chair_analysis_panel.run_analysis()
    manager.refresh_turnouts(selected_id="TO-001")
    before_integration = index_state(document)
    if (len(before_integration["index"].get("records") or []) != 10
            or before_integration["integration"] is not None
            or not manager.integrate_button.isEnabled()):
        raise RuntimeError("The copied TO-001 chair baseline changed")
    integration_dialogs = run_action_dialogs(
        manager.integrate_selected_turnout,
        question_title="Integrate turnout into host template",
        result_title="Turnout integrated",
    )
    manager.refresh_turnouts(selected_id="TO-001")
    integrated = index_state(document)
    records = list(integrated["index"].get("records") or [])
    integration = integrated["integration"]
    if (not isinstance(integration, dict)
            or len(records) != 8
            or len(integration.get("integration_object_names") or []) != 5
            or len(integration.get("integrated_record_ids") or []) != 2
            or integrated["history"]["undo_count"]
            != before_integration["history"]["undo_count"] + 1
            or manager.integrate_button.isEnabled()
            or not manager.remove_integration_button.isEnabled()):
        raise RuntimeError("The integrated TO-001 record lifecycle changed")
    integrated_ids = set(integration["integrated_record_ids"])
    integrated_records = [
        record for record in records
        if str(record.get("record_id") or "") in integrated_ids
    ]
    if (len(integrated_records) != 2
            or {str(record.get("category") or "")
                for record in integrated_records}
            != {module.EXPORT_CATEGORY_SOLID,
                module.EXPORT_CATEGORY_CUTTING}):
        raise RuntimeError("The integrated TO-001 pair changed")
    outline_record = next(
        record for record in integrated_records
        if record.get("category") == module.EXPORT_CATEGORY_CUTTING
    )
    solid_record = next(
        record for record in integrated_records
        if record.get("category") == module.EXPORT_CATEGORY_SOLID
    )
    outline_id = str(outline_record.get("record_id") or "")
    solid_id = str(solid_record.get("record_id") or "")
    outline_name = str(outline_record.get("source_name") or "")
    solid_name = str(solid_record.get("source_name") or "")
    names = set(integration["integration_object_names"])
    outline = document.getObject(outline_name)
    solid = document.getObject(solid_name)
    if (not outline_id or not solid_id
            or not outline_name or not solid_name
            or {outline_name, solid_name} - names
            or outline is None or solid is None
            or module.object_string_property(
                outline, "GeneratedRole", ""
            ) != module.TURNOUT_INTEGRATED_OUTLINE_ROLE
            or module.object_string_property(
                solid, "GeneratedRole", ""
            ) != module.TURNOUT_INTEGRATED_TEMPLATE_ROLE):
        raise RuntimeError("The TO-001 pair lacks integration identity")
    manager.close()
    QtWidgets.QApplication.processEvents()
    integrated_visual = capture_top("to-001-integrated-top-view.png")

    document.save()
    copied_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(copied_path)
    document.UndoMode = 1
    reopened = index_state(document)
    if (reopened["index"] != integrated["index"]
            or reopened["object_names"] != integrated["object_names"]
            or reopened["config"] != integrated["config"]
            or reopened["integration"] != integrated["integration"]
            or reopened["history"]["undo_count"]):
        raise RuntimeError("Copied TO-001 record identity changed on reopen")
    reopened_visual = capture_top("to-001-reopened-top-view.png")

    outline = document.getObject(outline_name)
    solid = document.getObject(solid_name)
    if (outline is None or solid is None
            or module.object_string_property(
                outline, "GeneratedRole", ""
            ) != module.TURNOUT_INTEGRATED_OUTLINE_ROLE
            or module.object_string_property(
                solid, "GeneratedRole", ""
            ) != module.TURNOUT_INTEGRATED_TEMPLATE_ROLE
            or outline_id not in module.selected_export_object_record_ids(
                outline
            )
            or solid_id not in module.selected_export_object_record_ids(
                solid
            )):
        raise RuntimeError("The reopened integrated pair lost its binding")
    Gui.Selection.clearSelection()
    if module.selected_export_selection_snapshot(
            document, reopened["set_id"]):
        raise RuntimeError("The highlighted-row route needs no FreeCAD selection")

    if TRACKTEMPLATE_PHASE8_ENTRYPOINT == "main-button":
        main_result = run_main_button_export()
        route = main_result["route"]
        result = main_result["result"]
    elif TRACKTEMPLATE_PHASE8_ENTRYPOINT == "direct":
        dialog = module.SelectedProductionExportDialog(document)
        dialog.setModal(True)
        dialog.show()
        QtWidgets.QApplication.processEvents()
        result = exercise_selected_export(dialog)
        route = {"entrypoint": "direct", "child_count": 1}
    else:
        raise RuntimeError("Unknown selected-export entrypoint")
    preview = result["preview"]
    before_export = result["before_export"]
    after_export = result["after_export"]
    dialogs = result["dialogs"]
    plan = result["plan"]
    tasks = result["tasks"]

    confirmation = dialogs["confirmations"][0]
    summary = dialogs["summaries"][0]
    output_dir = pathlib.Path(TRACKTEMPLATE_PHASE8_OUTPUT_DIR)
    svg_path = pathlib.Path(tasks[0]["path"])
    manifest_path = pathlib.Path(plan["manifest_path"])
    files = sorted(path.name for path in output_dir.iterdir())
    if (files != sorted([svg_path.name, manifest_path.name])
            or not svg_path.is_file() or svg_path.stat().st_size == 0
            or not manifest_path.is_file()
            or manifest_path.stat().st_size == 0):
        raise RuntimeError("Selected export did not stage two private files")
    bounds = module.validate_svg_export_bounds(str(svg_path))
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != tuple(
                module.EXPORT_MANIFEST_FIELDS):
            raise RuntimeError("Selected export manifest fields changed")
        manifest = list(reader)
    successful = [
        row for row in manifest
        if row.get("Export status") == "Success"
    ]
    skipped = [
        row for row in manifest
        if row.get("Export status") == "Skipped"
    ]
    if (len(manifest) != 2
            or len(successful) != 1
            or len(skipped) != 1
            or successful[0].get("Generated object name") != outline_name
            or successful[0].get("Generated object role")
            != outline_record["role"]
            or skipped[0].get("Generated object name") != solid_name
            or skipped[0].get("Generated object role")
            != solid_record["role"]
            or successful[0].get("Export format") != "SVG"
            or successful[0].get("Template-set identifier")
            != reopened["set_id"]
            or successful[0].get("Export filename") != svg_path.name
            or successful[0].get("Full export path") != str(svg_path)
            or "Successful files: 2" not in summary["information"]
            or "Failed files: 0" not in summary["information"]
            or "Formats produced: SVG" not in summary["information"]
            or "Manifest: {}".format(manifest_path)
            not in summary["information"]
            or "Production records selected for this operation: 2"
            not in confirmation["information"]
            or "Records with compatible selected formats: 1"
            not in confirmation["information"]
            or "Files to produce: 2" not in confirmation["information"]
            or str(output_dir) not in confirmation["information"]):
        raise RuntimeError("Selected export manifest or summary changed")

    print(json.dumps({
        "sentinel": "PHASE8_TURNOUT_SELECTED_EXPORT_GUI_PROBE_PASS",
        "entrypoint": TRACKTEMPLATE_PHASE8_ENTRYPOINT,
        "entrypoint_route": route,
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "routing": {
            "route": routing["route"],
            "schema_version": routing["schema_version"],
        },
        "host": selection["identity"],
        "creation": creation,
        "integration_dialogs": integration_dialogs,
        "integration": integration,
        "index_count_before": len(before_integration["index"]["records"]),
        "index_count_integrated": len(integrated["index"]["records"]),
        "integrated_record_ids": sorted(integrated_ids),
        "integrated_record_sources": {
            outline_id: outline_name,
            solid_id: solid_name,
        },
        "outline_record_id": outline_id,
        "outline_name": outline_name,
        "solid_record_id": solid_id,
        "solid_name": solid_name,
        "integration_history": integrated["history"],
        "reopened_history": reopened["history"],
        "export_history_before": before_export["history"],
        "export_history_after": after_export["history"],
        "selection_route": "highlighted paired production-record rows",
        "preview": preview,
        "confirmation": confirmation,
        "summary": summary,
        "svg_bounds": bounds,
        "manifest_success": successful[0],
        "manifest_skipped": skipped[0],
        "output_files": [str(svg_path), str(manifest_path)],
        "visuals": [integrated_visual, reopened_visual],
    }, sort_keys=True, default=lambda value: sorted(value)))
finally:
    manager.close()
    QtWidgets.QApplication.processEvents()
'''


def _source_hashes():
    paths = [
        ROOT / "AdvancedTurnout.FCMacro",
        ROOT / "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
        ROOT / "TrackTemplate.FCMacro",
        CONTRACT,
        LOADER,
        ROOT / "tools/freecad_bridge/turnout_recipe.py",
        ROOT / "tools/freecad_bridge/"
        "run-phase8-turnout-selected-export-gui",
        pathlib.Path(__file__).resolve(),
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
    raise RuntimeError('The selected export GUI proof left documents open')
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != PROBE_SENTINEL:
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"):
        raise RuntimeError("The real GUI proof used another FreeCAD profile")
    if (probe.get("routing")
            != {"route": "modular", "schema_version": 16}
            or probe.get("index_count_before") != 10
            or probe.get("index_count_integrated") != 8
            or len(probe.get("integrated_record_ids") or []) != 2
            or set(probe.get("integrated_record_sources") or {})
            != set(probe.get("integrated_record_ids") or [])
            or probe.get("preview", {}).get("record_ids")
            != [probe.get("outline_record_id")]
            or len(probe.get("output_files") or []) != 2):
        raise RuntimeError("The selected export GUI contract changed")
    route = probe.get("entrypoint_route") or {}
    if probe.get("entrypoint") == "main-button":
        if (route.get("parent_count") != 1
                or route.get("button_clicks") != 1
                or route.get("child_count") != 1
                or route.get("child_modal") is not True
                or route.get("child_parent_main") is not True
                or route.get("button_text") != "Export selected items..."
                or not route.get("main_visual")
                or not route.get("parent_visual")):
            raise RuntimeError("The main button route lost its child dialog")
    elif probe.get("entrypoint") != "direct":
        raise RuntimeError("The selected export entrypoint changed")
    visuals = [
        *probe["visuals"],
        probe["preview"]["visual"],
        probe["confirmation"]["visual"],
        probe["summary"]["visual"],
    ]
    if probe["entrypoint"] == "main-button":
        visuals.extend((route["parent_visual"], route["main_visual"]))
    return visuals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base", type=pathlib.Path,
        default=ROOT / "benchmark-output/freecad-bridge/fixtures/"
        "b14-default-base-regenerated.FCStd",
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument(
        "--entrypoint", choices=("direct", "main-button"),
        default="direct",
    )
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated GUI proof requires port 19875")
    base = args.base.resolve()
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not base.is_file() or not token.is_file():
        raise SystemExit("The B14 fixture or isolated bridge token is absent")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    fixture_hash = sha256(base)
    if fixture_hash != contract["fixture"]["sha256"]:
        raise SystemExit("The fixed B14 fixture identity drifted")
    source_hashes = _source_hashes()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "turnout-selected-export.FCStd"
    output_dir = run_dir / "private-development-output"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-turnout-highlighted-export-gui-v1",
        "entrypoint": args.entrypoint,
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "output_directory": str(output_dir),
        "output_status": "Private development evidence only; no clearance",
        "scope": (
            "fixed curved TO-001, B16 host integration, copied reopen, "
            "highlighted integrated cutting profile SVG and manifest"
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
    raise RuntimeError('The selected export GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_ENTRYPOINT = {!r}\n".format(
                args.entrypoint
            )
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(
                str(run_dir)
            )
            + "TRACKTEMPLATE_PHASE8_OUTPUT_DIR = {!r}\n".format(
                str(output_dir)
            )
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 turnout selected export real GUI", args.timeout,
        )
        state["probe"] = parse_json_output(job)
        visuals = _check_probe(state["probe"])
        state["visual_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in visuals
        }
        state["output_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in state["probe"]["output_files"]
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
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != fixture_hash
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError(
                "The GUI proof changed its source or fixture"
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
        print(
            "Phase 8 turnout selected export GUI evidence: {}".format(
                run_dir
            ),
            flush=True,
        )
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
