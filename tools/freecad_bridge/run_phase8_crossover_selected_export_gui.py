#!/usr/bin/env python3
"""Exercise copied XO-001 selected export in the qualified FreeCAD GUI."""

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
    "phase8-crossover-selected-export-gui-runs"
)
SENTINEL = "PHASE8_CROSSOVER_SELECTED_EXPORT_GUI_PASS"
PROBE_SENTINEL = "PHASE8_CROSSOVER_SELECTED_EXPORT_GUI_PROBE_PASS"


GUI_PROBE = r'''
import csv
import json
import pathlib
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import b14_recipe
from tracktemplate.compatibility.crossover_host_integration_recovery import (
    CrossoverHostIntegrationRecoveryAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied XO-001 fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")
adapter = getattr(module.create_crossover_host_integration, "__self__", None)
if (not isinstance(adapter, CrossoverHostIntegrationRecoveryAdapter)
        or adapter.module is not module
        or getattr(module.create_crossover_host_integration, "__func__", None)
        is not CrossoverHostIntegrationRecoveryAdapter.create):
    raise RuntimeError("The host-integration action is not routed through B16")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(value) for value in active_document.UndoNames],
    }


def index_state(active_document):
    config = module.crossover_config_by_id(active_document, "XO-001")
    if not isinstance(config, dict):
        raise RuntimeError("The fixed XO-001 configuration is unavailable")
    set_id = str(config.get("template_set_id") or "")
    settings = module.settings_for_template_set(active_document, set_id)
    index = module.read_production_record_index(settings)
    if not isinstance(index, dict):
        raise RuntimeError("The persistent production index is unavailable")
    return {
        "set_id": set_id,
        "config": config,
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


def confirm_action(action, expected_title):
    seen = {
        "questions": [], "unexpected": [], "monitor_errors": [],
        "active": True,
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
                if expected_title in title and yes is not None:
                    seen["questions"].append({
                        "title": title,
                        "message": "{}\n{}".format(
                            widget.text(), widget.informativeText()
                        ),
                    })
                    yes.click()
                else:
                    seen["unexpected"].append(title)
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
    if (len(seen["questions"]) != 1 or seen["unexpected"]
            or seen["monitor_errors"]):
        raise RuntimeError("The XO-001 confirmation changed: {}".format(seen))
    return seen["questions"][0]


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
                        widget, "xo-001-selected-export-confirmation.png"
                    )
                    seen["confirmations"].append(item)
                    yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                    if yes is None:
                        raise RuntimeError("Selected export has no Yes action")
                    yes.click()
                elif "Production export complete" in title:
                    item["visual"] = capture_widget(
                        widget, "xo-001-selected-export-summary.png"
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
        if not dialog.probe_box.isChecked():
            raise RuntimeError("Mandatory exporter probes are not enabled")
        refresh_checks = []

        def check_preselection(label):
            if (dialog.scope.get("selected_objects") != preselected_objects
                    or dialog._highlighted_record_ids()
                    or dialog.scope.get("highlighted_record_ids")
                    or not dialog.probe_box.isChecked()):
                raise RuntimeError(
                    "Preselected scope changed during {}".format(label)
                )
            refresh_checks.append({
                "label": label,
                "selected_objects": dialog.scope["selected_objects"],
                "probe_documents": len(probe_documents),
            })

        if TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "preselected":
            check_preselection("dialog construction")
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
        if TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "highlighted":
            if (dialog.scope.get("selected_objects")
                    or len(dialog.preview_records) != 7
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
        elif TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "preselected":
            check_preselection("configured preview")
            dialog.refresh_preview()
            check_preselection("repeated preview")
            set_scope_index = dialog.scope_box.findText(
                module.SELECTED_EXPORT_SCOPE_TEMPLATE_SET
            )
            if set_scope_index < 0:
                raise RuntimeError("Template-set export scope is absent")
            dialog.scope_box.setCurrentIndex(set_scope_index)
            dialog.scope_box.setCurrentIndex(scope_index)
            check_preselection("scope round-trip")
            dialog.manifest_box.setChecked(False)
            dialog.manifest_box.setChecked(True)
            check_preselection("manifest control round-trip")
            if any(after["probe_documents"] <= before["probe_documents"]
                   for before, after in zip(
                       refresh_checks, refresh_checks[1:]
                   )):
                raise RuntimeError("A refreshed preview bypassed its probes")
        else:
            raise RuntimeError("Unknown selected-export selection route")
        expanded_ids = {
            str(record.get("record_id") or "")
            for record in dialog.matching_records
        }
        if (len(expanded_ids) != 2
                or outline_id not in expanded_ids
                or {str(record.get("category") or "")
                    for record in dialog.matching_records}
                != {module.EXPORT_CATEGORY_SOLID,
                    module.EXPORT_CATEGORY_CUTTING}
                or {str(record.get("route_id") or "")
                    for record in dialog.matching_records} != {"XO-001"}):
            raise RuntimeError("The selected outline representations changed")
        dialog.refresh_preview()
        if TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "highlighted":
            expected_action = "Export 2 highlighted rows"
            if (dialog._highlighted_record_ids() != expanded_ids
                    or set(dialog.scope.get("highlighted_record_ids") or [])
                    != expanded_ids):
                raise RuntimeError("The highlighted-row scope did not stabilise")
        else:
            expected_action = "Export all matching records"
            check_preselection("final preview")
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
        chair_issues = [
            issue for issue in dialog.issues
            if issue.get("issue_code")
            == "CROSSOVER_CHAIR_VALIDATION_OUTSTANDING"
        ]
        if (selected_ids != {outline_id}
                or len(dialog.matching_records) != 2
                or len(tasks) != 1
                or str(tasks[0].get("format") or "") != "svg"
                or str(tasks[0].get("records", [{}])[0].get("record_id")
                       or "") != outline_id
                or not plan.get("manifest_path")
                or blocking
                or len(chair_issues) != 1
                or chair_issues[0].get("severity") != "Warning"
                or chair_issues[0].get("blocks_export") is not False
                or dialog.export_button.text() != expected_action
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
            "refresh_checks": refresh_checks,
            "mandatory_probes_enabled": bool(dialog.probe_box.isChecked()),
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
                dialog, "xo-001-selected-export-preflight.png"
            ),
        }
        before_export = index_state(document)
        probe_count_before_export = len(probe_documents)
        dialogs = export_dialog_action(dialog)
        after_export = index_state(document)
        if (not dialog.probe_box.isChecked()
                or len(probe_documents) <= probe_count_before_export):
            raise RuntimeError("Selected export bypassed its mandatory probes")
        if (after_export["index"] != before_export["index"]
                or after_export["config"] != before_export["config"]
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
        "entrypoint": "main-button",
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
                parent, "xo-001-main-selected-export-panel.png"
            )
            state["main_visual"] = capture_widget(
                button, "xo-001-main-selected-export-button.png"
            )
            if module.selected_export_selection_snapshot(
                    document, reopened["set_id"]) != preselected_objects:
                raise RuntimeError("Main dialog changed the admitted selection")
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
manager.mode_tabs.setCurrentIndex(1)
QtWidgets.QApplication.processEvents()
panel = manager.crossover_panel

try:
    if len(document.Objects) != 9 or history(document)["undo_count"]:
        raise RuntimeError("The copied B14 fixture changed")
    panel.refresh_hosts()
    selection = b14_recipe.select_crossover_hosts(
        panel.hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    panel.host_a_combo.setCurrentIndex(selection["a"])
    panel.host_b_combo.setCurrentIndex(selection["b"])
    for combo, value in (
        (panel.arrangement_combo, module.CROSSOVER_ARRANGEMENT_FACING),
        (panel.handing_combo, module.CROSSOVER_HAND_AUTO),
    ):
        index = combo.findText(value)
        if index < 0:
            raise RuntimeError("The fixed XO-001 GUI choice is absent")
        combo.setCurrentIndex(index)
    panel.gauge_box.setValue(16.5)
    panel.flangeway_box.setValue(1.0)
    panel.minimum_radius_box.setValue(600.0)
    panel.chainage_box.setValue(746.298)
    if panel.preview_geometry() is None:
        raise RuntimeError("The fixed XO-001 creation preview failed")
    creation = confirm_action(
        panel.create_crossover, "Create managed crossover geometry"
    )
    panel.refresh_crossovers("XO-001")
    panel.apply_b4_button.click()
    panel.refresh_crossovers("XO-001")
    panel.chair_analysis_panel.run_analysis()
    panel.refresh_crossovers("XO-001")
    before_integration = index_state(document)
    if (len(before_integration["index"].get("records") or []) != 8
            or len(before_integration["object_names"]) != 22):
        raise RuntimeError("The copied XO-001 B4/chair baseline changed")
    integration = confirm_action(
        panel.integrate_selected_crossover,
        "Integrate crossover with host templates",
    )
    diagnostics = str(panel.diagnostics.toPlainText())
    integrated = index_state(document)
    records = list(integrated["index"].get("records") or [])
    outline_role = module.CROSSOVER_INTEGRATED_OUTLINE_ROLE
    outline_records = [
        record for record in records
        if str(record.get("role") or "") == outline_role
    ]
    if (len(records) != 7 or len(outline_records) != 1
            or len(integrated["object_names"]) != 26
            or integrated["history"]["undo_count"]
            != before_integration["history"]["undo_count"] + 1
            or not integrated["config"].get("integration_active")
            or "Production ready: No" not in diagnostics):
        raise RuntimeError("The integrated XO-001 record lifecycle changed")
    outline_record = outline_records[0]
    outline_id = str(outline_record.get("record_id") or "")
    outline_name = str(outline_record.get("source_name") or "")
    if not outline_id or not outline_name:
        raise RuntimeError("The integrated outline lacks stable identity")
    manager.close()
    QtWidgets.QApplication.processEvents()
    integrated_visual = capture_top("xo-001-integrated-top-view.png")

    document.save()
    copied_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(copied_path)
    document.UndoMode = 1
    reopened = index_state(document)
    if (reopened["index"] != integrated["index"]
            or reopened["object_names"] != integrated["object_names"]
            or reopened["config"].get("integration_result")
            != integrated["config"].get("integration_result")
            or reopened["history"]["undo_count"]):
        raise RuntimeError("Copied XO-001 record identity changed on reopen")
    reopened_visual = capture_top("xo-001-reopened-top-view.png")

    outline = document.getObject(outline_name)
    if outline is None:
        raise RuntimeError("The reopened integrated outline is absent")
    Gui.Selection.clearSelection()
    if TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "preselected":
        Gui.Selection.addSelection(outline)
    preselected_objects = module.selected_export_selection_snapshot(
        document, reopened["set_id"]
    )
    if TRACKTEMPLATE_PHASE8_SELECTION_ROUTE == "preselected":
        if (len(preselected_objects) != 1
                or preselected_objects[0].get("name") != outline_name
                or outline_id not in preselected_objects[0].get("record_ids", [])
                or preselected_objects[0].get("generated_role") != outline_role):
            raise RuntimeError("The preselected outline lost its record identity")
    elif preselected_objects:
        raise RuntimeError("The highlighted-row route needs no FreeCAD selection")

    before_dialog = index_state(document)
    probe_documents = []
    original_create_probe = module._create_isolated_preflight_document
    original_close_probe = module._close_isolated_preflight_document

    def observe_create_probe():
        probe_document = original_create_probe()
        probe_documents.append({
            "name": str(probe_document.Name),
            "created": str(probe_document.Name) in App.listDocuments(),
            "closed": False,
        })
        return probe_document

    def observe_close_probe(probe_document, original_document_name=""):
        name = str(probe_document.Name)
        original_close_probe(probe_document, original_document_name)
        entry = next(item for item in probe_documents if item["name"] == name)
        entry["closed"] = name not in App.listDocuments()
        entry["source_active"] = (
            App.ActiveDocument is not None
            and str(App.ActiveDocument.Name) == str(document.Name)
        )

    module._create_isolated_preflight_document = observe_create_probe
    module._close_isolated_preflight_document = observe_close_probe
    try:
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
    finally:
        module._create_isolated_preflight_document = original_create_probe
        module._close_isolated_preflight_document = original_close_probe
    preview = result["preview"]
    before_export = result["before_export"]
    after_export = result["after_export"]
    dialogs = result["dialogs"]
    plan = result["plan"]
    tasks = result["tasks"]
    if (not probe_documents
            or any(not item["created"] or not item["closed"]
                   or not item.get("source_active")
                   for item in probe_documents)
            or set(App.listDocuments()) != {str(document.Name)}):
        raise RuntimeError("Mandatory exporter probes did not run and close")
    if after_export != before_dialog:
        raise RuntimeError("Selected export or its preview changed the document")

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
    solid_records = [
        record for record in records
        if str(record.get("record_id") or "")
        in preview["matching_record_ids"]
        and record.get("category") == module.EXPORT_CATEGORY_SOLID
    ]
    if (len(manifest) != 2
            or len(successful) != 1
            or len(skipped) != 1
            or len(solid_records) != 1
            or successful[0].get("Generated object name") != outline_name
            or successful[0].get("Generated object role")
            != module.CROSSOVER_INTEGRATED_OUTLINE_ROLE
            or successful[0].get("Export format") != "SVG"
            or successful[0].get("Template-set identifier")
            != reopened["set_id"]
            or successful[0].get("Export filename") != svg_path.name
            or successful[0].get("Full export path") != str(svg_path)
            or skipped[0].get("Generated object name")
            != solid_records[0].get("source_name")
            or skipped[0].get("Generated object role")
            != solid_records[0].get("role")
            or skipped[0].get("Template-set identifier")
            != reopened["set_id"]
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
        "sentinel": "PHASE8_CROSSOVER_SELECTED_EXPORT_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "routing": {
            "route": routing["route"],
            "schema_version": routing["schema_version"],
        },
        "hosts": {
            "a": selection["host_a_identity"],
            "b": selection["host_b_identity"],
        },
        "creation": creation,
        "integration": integration,
        "integration_diagnostics": diagnostics,
        "index_count_before": len(before_integration["index"]["records"]),
        "index_count_integrated": len(integrated["index"]["records"]),
        "integrated_record_ids": sorted(
            str(record.get("record_id") or "") for record in records
        ),
        "outline_record_id": outline_id,
        "outline_name": outline_name,
        "integration_history": integrated["history"],
        "reopened_history": reopened["history"],
        "export_history_before": before_export["history"],
        "export_history_after": after_export["history"],
        "selection_route": TRACKTEMPLATE_PHASE8_SELECTION_ROUTE,
        "entrypoint": route,
        "admitted_selection": preselected_objects,
        "probe_documents": probe_documents,
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
        ROOT / "tools/freecad_bridge/b14_recipe.py",
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


def _check_probe(probe, selection_route, entrypoint):
    if probe.get("sentinel") != PROBE_SENTINEL:
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"):
        raise RuntimeError("The real GUI proof used another FreeCAD profile")
    if (probe.get("routing")
            != {"route": "modular", "schema_version": 16}
            or probe.get("index_count_before") != 8
            or probe.get("index_count_integrated") != 7
            or probe.get("preview", {}).get("record_ids")
            != [probe.get("outline_record_id")]
            or probe.get("selection_route") != selection_route
            or probe.get("entrypoint", {}).get("entrypoint") != entrypoint
            or probe.get("preview", {}).get("mandatory_probes_enabled")
            is not True
            or not probe.get("probe_documents")
            or len(probe.get("output_files") or []) != 2):
        raise RuntimeError("The selected export GUI contract changed")
    if selection_route == "preselected" and (
            len(probe.get("admitted_selection") or []) != 1
            or probe["preview"].get("highlighted_ids")
            or len(probe["preview"].get("refresh_checks") or []) != 6):
        raise RuntimeError("The preselected export route was not exercised")
    route = probe["entrypoint"]
    if entrypoint == "main-button" and (
            route.get("button_clicks") != 1
            or route.get("child_modal") is not True
            or route.get("child_parent_main") is not True):
        raise RuntimeError("The main export button route was not exercised")
    visuals = [
        *probe["visuals"],
        probe["preview"]["visual"],
        probe["confirmation"]["visual"],
        probe["summary"]["visual"],
    ]
    if entrypoint == "main-button":
        visuals.extend([route["parent_visual"], route["main_visual"]])
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
        "--selection-route", choices=("highlighted", "preselected"),
        default="highlighted",
    )
    parser.add_argument(
        "--entrypoint", choices=("direct", "main-button"), default="direct",
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
    document_path = run_dir / "crossover-selected-export.FCStd"
    output_dir = run_dir / "private-development-output"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-crossover-selected-export-gui-v2",
        "selection_route": args.selection_route,
        "entrypoint": args.entrypoint,
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "output_directory": str(output_dir),
        "output_status": "Private development evidence only; no clearance",
        "scope": (
            "fixed curved XO-001, B16 host integration, copied reopen, "
            "{} integrated cutting profile SVG and manifest via {}"
        ).format(args.selection_route, args.entrypoint),
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
        submitted_code = (
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(
                str(run_dir)
            )
            + "TRACKTEMPLATE_PHASE8_OUTPUT_DIR = {!r}\n".format(
                str(output_dir)
            )
            + "TRACKTEMPLATE_PHASE8_SELECTION_ROUTE = {!r}\n".format(
                args.selection_route
            )
            + "TRACKTEMPLATE_PHASE8_ENTRYPOINT = {!r}\n".format(
                args.entrypoint
            )
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE
        )
        submitted_path = run_dir / "submitted-code.py"
        submitted_path.write_text(submitted_code, encoding="utf-8")
        state["submitted_code"] = {
            "path": str(submitted_path), "sha256": sha256(submitted_path),
        }
        job = submit_and_wait(
            client, submitted_code,
            "Phase 8 crossover selected export real GUI", args.timeout,
        )
        raw_response = run_dir / "raw-response.json"
        raw_response.write_text(
            json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        state["raw_response"] = {
            "path": str(raw_response), "sha256": sha256(raw_response),
        }
        state["probe"] = parse_json_output(job)
        visuals = _check_probe(
            state["probe"], args.selection_route, args.entrypoint,
        )
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
            "Phase 8 crossover selected export GUI evidence: {}".format(
                run_dir
            ),
            flush=True,
        )
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
