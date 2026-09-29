#!/usr/bin/env python3
"""Prove one copied TO-001 host-integration lifecycle in a real FreeCAD GUI."""

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
    "phase8-turnout-host-integration-recovery-gui-runs"
)
SENTINEL = "PHASE8_TURNOUT_HOST_INTEGRATION_RECOVERY_GUI_PASS"
PROBE_SENTINEL = "PHASE8_TURNOUT_HOST_INTEGRATION_RECOVERY_GUI_PROBE_PASS"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import turnout_recipe
from tracktemplate.compatibility.b15_workflow_host import (
    EXPECTED_WORKFLOW_VERSION,
)
from tracktemplate.compatibility.turnout_host_integration_recovery import (
    TurnoutHostIntegrationRecoveryAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
identifier = turnout_recipe.TURNOUT_ID
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
        is not TurnoutHostIntegrationRecoveryAdapter.create
        or getattr(module.remove_turnout_host_integration, "__self__", None)
        is not adapter
        or getattr(module.remove_turnout_host_integration, "__func__", None)
        is not TurnoutHostIntegrationRecoveryAdapter.remove):
    raise RuntimeError("The turnout host actions are not routed through B16")
for action_name, target in (
    ("integrate_selected_turnout", "create_turnout_host_integration"),
    ("remove_selected_integration", "remove_turnout_host_integration"),
):
    method = module.TurnoutManagerDialog.__dict__.get(action_name)
    if getattr(method, "_whole_workflow_benchmark_wrapper", False):
        if (getattr(method, "_whole_workflow_wrapper_version", None)
                != EXPECTED_WORKFLOW_VERSION):
            raise RuntimeError("The inherited turnout GUI wrapper changed")
        method = getattr(method, "_whole_workflow_original", None)
    code = getattr(method, "__code__", None)
    if (code is None
            or getattr(method, "__globals__", None) is not module.__dict__
            or target not in code.co_names):
        raise RuntimeError("The turnout manager caller changed: " + action_name)


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(item) for item in active_document.UndoNames],
        "redo_names": [str(item) for item in active_document.RedoNames],
    }


def state(active_document):
    config = module.turnout_config_by_id(active_document, identifier)
    if not isinstance(config, dict):
        raise RuntimeError("The fixed TO-001 turnout is unavailable")
    settings = module.settings_for_template_set(
        active_document, str(config.get("template_set_id") or "")
    )
    if settings is None:
        raise RuntimeError("The production catalogue settings are unavailable")
    index = module.read_production_record_index(settings)
    if not isinstance(index, dict) or index.get("schema_version") != 2:
        raise RuntimeError("The persistent production index is unavailable")
    records = list(index.get("records") or [])
    bindings = {}
    for record in records:
        record_id = str(record.get("record_id") or "")
        source_name = str(record.get("source_name") or "")
        source = active_document.getObject(source_name)
        if not record_id or source is None:
            raise RuntimeError("A production record lost its source object")
        ids = json.loads(str(getattr(source, "ProductionRecordIDsJSON", "[]")))
        if record_id not in ids:
            raise RuntimeError("A production record lost its source binding")
        bindings[record_id] = source_name
    objects = {}
    for obj in active_document.Objects:
        view = getattr(obj, "ViewObject", None)
        shape = getattr(obj, "Shape", None)
        objects[str(obj.Name)] = {
            "type_id": str(obj.TypeId),
            "role": module.object_string_property(obj, "GeneratedRole", ""),
            "visible": (
                bool(view.Visibility)
                if view is not None and hasattr(view, "Visibility") else None
            ),
            "has_shape": shape is not None and not shape.isNull(),
        }
    chairs = {}
    for obj in module._chair_analysis_display_objects(
        active_document, "turnout", identifier
    ):
        chairs[str(obj.Name)] = {
            "role": module.object_string_property(obj, "GeneratedRole", ""),
            "visible": bool(obj.ViewObject.Visibility),
            "has_shape": (
                hasattr(obj, "Shape") and not obj.Shape.isNull()
            ),
        }
    return {
        "config": config,
        "integration": module.turnout_integration_by_id(
            active_document, identifier
        ),
        "index": index,
        "index_count": len(records),
        "record_ids": sorted(bindings),
        "record_bindings": bindings,
        "objects": objects,
        "chairs": chairs,
        "history": history(active_document),
    }


def same_document(actual, expected, label):
    for key in expected:
        if key != "history" and actual[key] != expected[key]:
            raise RuntimeError("{} changed {}".format(label, key))


def same_history(actual, expected, label):
    if actual["history"] != expected["history"]:
        raise RuntimeError("{} changed Undo history".format(label))


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


def capture_top(filename, manager_open=True):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    if manager_open:
        manager.hide()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(path), 1600, 1000, "Current")
    if manager_open:
        manager.show()
    return image_checked(path)


def run_dialogs(action, question_title=None, result_title=None,
                error_text=None, image_name=None):
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
                if (yes is not None and question_title is not None
                        and question_title in title):
                    seen["questions"].append({
                        "title": title, "message": message,
                    })
                    yes.click()
                elif (result_title is not None and result_title in title
                      and (error_text is None or error_text in message)):
                    visual = None
                    if image_name is not None:
                        path = pathlib.Path(
                            TRACKTEMPLATE_PHASE8_VISUAL_DIR
                        ) / image_name
                        if not widget.grab().save(str(path), "PNG"):
                            raise RuntimeError("Qt could not capture error dialog")
                        visual = image_checked(path)
                    seen["results"].append({
                        "title": title, "message": message, "visual": visual,
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
            or seen["unexpected"] or seen["monitor_errors"]):
        raise RuntimeError("Turnout GUI dialogs changed: {}".format(seen))
    return {
        "question": seen["questions"][0] if seen["questions"] else None,
        "result": seen["results"][0] if seen["results"] else None,
    }


def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The turnout GUI choice is absent: " + value)
    combo.setCurrentIndex(index)


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
    choose(manager.handing_combo, module.TURNOUT_HAND_LEFT)
    choose(manager.orientation_combo, module.TURNOUT_ORIENTATION_FACING)
    manager.chainage_box.setValue(turnout_recipe.TURNOUT_CHAINAGE_MM)
    manager.gauge_box.setValue(turnout_recipe.TRACK_GAUGE_MM)
    manager.flangeway_box.setValue(turnout_recipe.FLANGEWAY_MM)
    creation = run_dialogs(
        manager.create_turnout, result_title="REA C10 turnout created"
    )
    manager.refresh_turnouts(selected_id=identifier)
    if manager.current_turnout_config()["turnout_id"] != identifier:
        raise RuntimeError("The manager did not select TO-001")
    run_dialogs(manager.chair_analysis_panel.run_analysis)
    manager.refresh_turnouts(selected_id=identifier)
    before = state(document)
    if (before["index_count"] != 10 or len(before["chairs"]) != 2
            or before["integration"] is not None
            or not any(item["visible"] and item["has_shape"]
                       for item in before["chairs"].values())):
        raise RuntimeError("The GUI lacks copied turnout chair evidence")
    if (not manager.integrate_button.isEnabled()
            or manager.remove_integration_button.isEnabled()):
        raise RuntimeError("The turnout manager offered the wrong actions")
    before_visuals = [
        capture_manager("to-001-before-integration-manager.png"),
        capture_top("to-001-before-integration-top.png"),
    ]

    original_builder = module.build_turnout_host_integration
    build_fault = "Phase 8 injected turnout build failure"
    calls = {"builder": 0}

    def failing_builder(*args, **kwargs):
        calls["builder"] += 1
        raise RuntimeError(build_fault)

    module.build_turnout_host_integration = failing_builder
    try:
        rejected_create = run_dialogs(
            manager.integrate_selected_turnout,
            question_title="Integrate turnout into host template",
            result_title="Turnout integration error",
            error_text=build_fault,
            image_name="to-001-rejected-create-dialog.png",
        )
    finally:
        module.build_turnout_host_integration = original_builder
    if calls["builder"] != 1:
        raise RuntimeError("The GUI Create did not reach the injected build")
    after_rejected_create = state(document)
    same_document(after_rejected_create, before, "Rejected Create")
    same_history(after_rejected_create, before, "Rejected Create")
    rejected_create_visual = capture_top("to-001-rejected-create-top.png")

    rejected_remove = run_dialogs(
        manager.remove_selected_integration,
        question_title="Remove host integration",
        result_title="Integration removal error",
        error_text="no host-template integration to remove",
        image_name="to-001-rejected-remove-dialog.png",
    )
    after_rejected_remove = state(document)
    same_document(after_rejected_remove, before, "Rejected Remove")
    same_history(after_rejected_remove, before, "Rejected Remove")

    create_dialogs = run_dialogs(
        manager.integrate_selected_turnout,
        question_title="Integrate turnout into host template",
        result_title="Turnout integrated",
    )
    manager.refresh_turnouts(selected_id=identifier)
    integrated = state(document)
    integration = integrated["integration"]
    if not isinstance(integration, dict):
        raise RuntimeError("The GUI did not persist integration identity")
    if (manager.integrate_button.isEnabled()
            or not manager.remove_integration_button.isEnabled()):
        raise RuntimeError("The integrated turnout GUI controls changed")
    removed_ids = set(before["record_ids"]) - set(integrated["record_ids"])
    added_ids = set(integrated["record_ids"]) - set(before["record_ids"])
    rebound_ids = {
        record_id for record_id in set(before["record_ids"]) &
        set(integrated["record_ids"])
        if (before["record_bindings"][record_id]
            != integrated["record_bindings"][record_id])
    }
    logical_removed_ids = set(integration["removed_record_ids"])
    logical_integrated_ids = set(integration["integrated_record_ids"])
    names = set(integration["integration_object_names"])
    if (integrated["index_count"] != 8
            or len(logical_removed_ids) != 4
            or len(logical_integrated_ids) != 2
            or removed_ids != logical_removed_ids - logical_integrated_ids
            or added_ids != logical_integrated_ids - logical_removed_ids
            or rebound_ids != logical_integrated_ids &
            set(before["record_ids"])
            or len(names) != 5
            or names - set(integrated["objects"])
            or {integrated["record_bindings"][record_id]
                for record_id in logical_integrated_ids} - names
            or integrated["chairs"]
            or integrated["history"]["undo_count"]
            != before["history"]["undo_count"] + 1
            or integrated["history"]["redo_count"]):
        raise RuntimeError("GUI Create did not replace records atomically")
    source_names = set(integration["source_visibility"])
    source_names.update(integration["turnout_visibility"])
    if not source_names or any(
        integrated["objects"][name]["visible"] is not False
        for name in source_names
    ):
        raise RuntimeError("GUI Create did not hide source templates")
    integrated_visuals = [
        capture_manager("to-001-integrated-manager.png"),
        capture_top("to-001-integrated-top.png"),
    ]

    document.undo()
    document.recompute()
    undone_create = state(document)
    same_document(undone_create, before, "Create Undo")
    if (undone_create["history"]["undo_count"]
            != before["history"]["undo_count"]
            or undone_create["history"]["redo_count"] != 1):
        raise RuntimeError("Create Undo changed history")
    undo_create_visual = capture_top("to-001-create-undo-top.png")
    document.redo()
    document.recompute()
    redone_create = state(document)
    same_document(redone_create, integrated, "Create Redo")
    same_history(redone_create, integrated, "Create Redo")

    manager.close()
    QtWidgets.QApplication.processEvents()
    document.save()
    saved_integrated = state(document)
    saved_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(saved_path)
    document.UndoMode = 1
    reopened_integrated = state(document)
    same_document(reopened_integrated, saved_integrated, "Integrated reopen")
    if (reopened_integrated["history"]["undo_count"]
            or reopened_integrated["history"]["redo_count"]):
        raise RuntimeError("Integrated reopen retained session history")
    reopened_integrated_visual = capture_top(
        "to-001-reopened-integrated-top.png", manager_open=False
    )

    manager = module.TurnoutManagerDialog(document)
    manager.show()
    manager.mode_tabs.setCurrentIndex(0)
    manager.refresh_turnouts(selected_id=identifier)
    QtWidgets.QApplication.processEvents()
    original_writer = module._turnout_write_production_records
    write_fault = "Phase 8 injected turnout removal record-write failure"
    calls["writer"] = 0

    def failing_writer(*args, **kwargs):
        calls["writer"] += 1
        original_writer(*args, **kwargs)
        raise RuntimeError(write_fault)

    module._turnout_write_production_records = failing_writer
    try:
        rejected_write = run_dialogs(
            manager.remove_selected_integration,
            question_title="Remove host integration",
            result_title="Integration removal error",
            error_text=write_fault,
            image_name="to-001-rejected-record-write-dialog.png",
        )
    finally:
        module._turnout_write_production_records = original_writer
    if calls["writer"] != 1:
        raise RuntimeError("The GUI Remove did not reach the record write")
    after_rejected_write = state(document)
    same_document(after_rejected_write, reopened_integrated,
                  "Rejected Remove record write")
    same_history(after_rejected_write, reopened_integrated,
                 "Rejected Remove record write")
    rejected_write_visual = capture_top("to-001-rejected-record-write-top.png")

    remove_dialogs = run_dialogs(
        manager.remove_selected_integration,
        question_title="Remove host integration",
        result_title="Host integration removed",
    )
    manager.refresh_turnouts(selected_id=identifier)
    removed = state(document)
    if (removed["integration"] is not None
            or removed["index_count"] != 10
            or set(removed["record_ids"]) != set(before["record_ids"])
            or removed["record_bindings"] != before["record_bindings"]
            or names & set(removed["objects"])
            or removed["history"]["undo_count"] != 1
            or removed["history"]["redo_count"]):
        raise RuntimeError("GUI Remove did not restore production records")
    if any(
        removed["objects"][name]["visible"]
        != before["objects"][name]["visible"]
        for name in source_names
    ):
        raise RuntimeError("GUI Remove did not restore source visibility")
    removed_visuals = [
        capture_manager("to-001-removed-manager.png"),
        capture_top("to-001-removed-top.png"),
    ]

    document.undo()
    document.recompute()
    undone_remove = state(document)
    same_document(undone_remove, reopened_integrated, "Remove Undo")
    if (undone_remove["history"]["undo_count"]
            or undone_remove["history"]["redo_count"] != 1):
        raise RuntimeError("Remove Undo changed history")
    undo_remove_visual = capture_top("to-001-remove-undo-top.png")
    document.redo()
    document.recompute()
    redone_remove = state(document)
    same_document(redone_remove, removed, "Remove Redo")
    same_history(redone_remove, removed, "Remove Redo")
    redo_remove_visual = capture_top("to-001-remove-redo-top.png")

    manager.close()
    QtWidgets.QApplication.processEvents()
    document.save()
    saved_removed = state(document)
    App.closeDocument(str(document.Name))
    document = App.openDocument(saved_path)
    document.UndoMode = 1
    reopened_removed = state(document)
    same_document(reopened_removed, saved_removed, "Removed reopen")
    if (reopened_removed["history"]["undo_count"]
            or reopened_removed["history"]["redo_count"]):
        raise RuntimeError("Removed reopen retained session history")
    reopened_removed_visual = capture_top(
        "to-001-reopened-removed-top.png", manager_open=False
    )
    print(json.dumps({
        "sentinel": "PHASE8_TURNOUT_HOST_INTEGRATION_RECOVERY_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "route": routing["route"],
        "selected_binding": type(adapter).__name__,
        "host_identity": selection["identity"],
        "creation": creation["result"],
        "before": {
            "object_count": len(before["objects"]),
            "record_count": before["index_count"],
            "chair_count": len(before["chairs"]),
            "history": before["history"],
            "visuals": before_visuals,
        },
        "rejected_create": {
            "dialog": rejected_create["result"],
            "builder_calls": calls["builder"],
            "state_unchanged": True,
            "visual": rejected_create_visual,
        },
        "rejected_remove": {
            "dialog": rejected_remove["result"],
            "state_unchanged": True,
        },
        "integrated": {
            "dialogs": create_dialogs,
            "object_count": len(integrated["objects"]),
            "record_count": integrated["index_count"],
            "removed_record_ids": sorted(integration["removed_record_ids"]),
            "integrated_record_ids": sorted(integration["integrated_record_ids"]),
            "dropped_record_ids": sorted(removed_ids),
            "rebound_record_ids": sorted(rebound_ids),
            "integration_objects": sorted(names),
            "source_visibility": {
                name: integrated["objects"][name]["visible"]
                for name in sorted(source_names)
            },
            "history": integrated["history"],
            "visuals": integrated_visuals,
        },
        "create_undo": {
            "chair_count": len(undone_create["chairs"]),
            "record_count": undone_create["index_count"],
            "history": undone_create["history"],
            "visual": undo_create_visual,
        },
        "create_redo": {
            "record_count": redone_create["index_count"],
            "history": redone_create["history"],
        },
        "reopened_integrated": {
            "record_count": reopened_integrated["index_count"],
            "visual": reopened_integrated_visual,
        },
        "rejected_record_write": {
            "dialog": rejected_write["result"],
            "writer_calls": calls["writer"],
            "state_unchanged": True,
            "visual": rejected_write_visual,
        },
        "removed": {
            "dialogs": remove_dialogs,
            "object_count": len(removed["objects"]),
            "record_count": removed["index_count"],
            "restored_record_ids": sorted(integration["removed_record_ids"]),
            "history": removed["history"],
            "visuals": removed_visuals,
        },
        "remove_undo": {
            "record_count": undone_remove["index_count"],
            "history": undone_remove["history"],
            "visual": undo_remove_visual,
        },
        "remove_redo": {
            "record_count": redone_remove["index_count"],
            "history": redone_remove["history"],
            "visual": redo_remove_visual,
        },
        "reopened_removed": {
            "record_count": reopened_removed["index_count"],
            "visual": reopened_removed_visual,
        },
    }, sort_keys=True))
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
        pathlib.Path(__file__).resolve(),
        ROOT / "tools/freecad_bridge/"
        "run-phase8-turnout-host-integration-recovery-gui",
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
    raise RuntimeError('The turnout GUI proof left documents open')
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != PROBE_SENTINEL:
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id") != PROFILE
            or probe.get("route") != "modular"
            or probe.get("selected_binding")
            != "TurnoutHostIntegrationRecoveryAdapter"
            or probe["before"]["record_count"] != 10
            or probe["before"]["chair_count"] != 2
            or probe["rejected_create"]["builder_calls"] != 1
            or probe["rejected_create"]["state_unchanged"] is not True
            or probe["rejected_remove"]["state_unchanged"] is not True
            or probe["integrated"]["record_count"] != 8
            or len(probe["integrated"]["integration_objects"]) != 5
            or len(probe["integrated"]["removed_record_ids"]) != 4
            or len(probe["integrated"]["integrated_record_ids"]) != 2
            or probe["create_undo"]["record_count"] != 10
            or probe["create_redo"]["record_count"] != 8
            or probe["reopened_integrated"]["record_count"] != 8
            or probe["rejected_record_write"]["writer_calls"] != 1
            or probe["rejected_record_write"]["state_unchanged"] is not True
            or probe["removed"]["record_count"] != 10
            or probe["remove_undo"]["record_count"] != 8
            or probe["remove_redo"]["record_count"] != 10
            or probe["reopened_removed"]["record_count"] != 10):
        raise RuntimeError("The turnout GUI lifecycle contract changed")
    return [
        *probe["before"]["visuals"],
        probe["rejected_create"]["dialog"]["visual"],
        probe["rejected_create"]["visual"],
        probe["rejected_remove"]["dialog"]["visual"],
        *probe["integrated"]["visuals"],
        probe["create_undo"]["visual"],
        probe["reopened_integrated"]["visual"],
        probe["rejected_record_write"]["dialog"]["visual"],
        probe["rejected_record_write"]["visual"],
        *probe["removed"]["visuals"],
        probe["remove_undo"]["visual"],
        probe["remove_redo"]["visual"],
        probe["reopened_removed"]["visual"],
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base", type=pathlib.Path,
        default=ROOT / "benchmark-output/freecad-bridge/fixtures/"
        "b14-default-base-regenerated.FCStd",
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated turnout GUI proof requires port 19875")
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
    document_path = run_dir / "turnout-host-integration-recovery.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-turnout-host-integration-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "copied curved TO-001 turnout manager integration and production "
            "records, rejected GUI actions, one Undo/Redo per command and "
            "copied FCStd save/reopen"
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
    raise RuntimeError('The turnout GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 turnout host integration real GUI", args.timeout,
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
        print("Phase 8 turnout integration GUI evidence: {}".format(
            run_dir
        ), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
