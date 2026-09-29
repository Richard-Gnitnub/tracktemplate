#!/usr/bin/env python3
"""Check B16 crossover host integration recovery in a real FreeCAD GUI."""

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
    "phase8-crossover-host-integration-recovery-gui-runs"
)
SENTINEL = "PHASE8_CROSSOVER_HOST_INTEGRATION_RECOVERY_GUI_PASS"


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import b14_recipe
from tools.freecad_bridge import crossover_timber_recipe as recipe
from tracktemplate.compatibility.b15_workflow_host import (
    EXPECTED_WORKFLOW_VERSION,
)
from tracktemplate.compatibility.crossover_host_integration_recovery import (
    CrossoverHostIntegrationRecoveryAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied crossover fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")
adapter = getattr(module.create_crossover_host_integration, "__self__", None)
if (not isinstance(adapter, CrossoverHostIntegrationRecoveryAdapter)
        or adapter.module is not module
        or getattr(module.create_crossover_host_integration, "__func__", None)
        is not CrossoverHostIntegrationRecoveryAdapter.create
        or getattr(module.remove_crossover_host_integration, "__self__", None)
        is not adapter
        or getattr(module.remove_crossover_host_integration, "__func__", None)
        is not CrossoverHostIntegrationRecoveryAdapter.remove):
    raise RuntimeError("The GUI integration actions are not routed through B16")
panel_type = module.CrossoverManagerPanel
for action_name, target in (
    ("integrate_selected_crossover", "create_crossover_host_integration"),
    ("remove_selected_integration", "remove_crossover_host_integration"),
):
    method = panel_type.__dict__.get(action_name)
    if getattr(method, "_whole_workflow_benchmark_wrapper", False):
        if (getattr(method, "_whole_workflow_wrapper_version", None)
                != EXPECTED_WORKFLOW_VERSION):
            raise RuntimeError("The inherited GUI panel wrapper changed")
        method = getattr(method, "_whole_workflow_original", None)
    code = getattr(method, "__code__", None)
    if (code is None
            or getattr(method, "__globals__", None) is not module.__dict__
            or target not in code.co_names):
        raise RuntimeError("The GUI panel integration caller changed")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(item) for item in active_document.UndoNames],
        "redo_names": [str(item) for item in active_document.RedoNames],
    }


def chair_display(active_document):
    objects = module._chair_analysis_display_objects(
        active_document, "crossover", "XO-001"
    )
    return {
        str(obj.Name): {
            "role": module.object_string_property(obj, "GeneratedRole", ""),
            "visible": bool(obj.ViewObject.Visibility),
            "shape": recipe.shape_summary(getattr(obj, "Shape", None)),
        }
        for obj in objects
    }


def state(active_document):
    config = module.crossover_config_by_id(active_document, "XO-001")
    if not isinstance(config, dict):
        raise RuntimeError("The fixed XO-001 crossover is unavailable")
    settings = module.settings_for_template_set(
        active_document, str(config.get("template_set_id") or "")
    )
    if settings is None:
        raise RuntimeError("The production catalogue settings are unavailable")
    index = module.read_production_record_index(settings)
    if not isinstance(index, dict):
        raise RuntimeError("The persistent production index is unavailable")
    records = list(index.get("records") or [])
    names = sorted(str(obj.Name) for obj in active_document.Objects)
    result = dict(config.get("integration_result") or {})
    return {
        "object_names": names,
        "chair_display": chair_display(active_document),
        "integration_names": sorted(
            str(obj.Name) for obj in module._crossover_integration_objects(
                active_document, "XO-001"
            )
        ),
        "integration_active": bool(config.get("integration_active")),
        "integration_status": str(config.get("integration_status") or ""),
        "effective_status": module.crossover_host_integration_effective_status(
            active_document, config
        ),
        "integration_result": result,
        "b4_signature": str(config.get("b4_signature") or ""),
        "chair_signature": str(config.get("chair_analysis_signature") or ""),
        "index": index,
        "index_count": len(records),
        "index_ids": sorted(
            str(record.get("record_id") or "") for record in records
        ),
        "visibility": {
            str(obj.Name): bool(obj.ViewObject.Visibility)
            for obj in active_document.Objects
            if getattr(obj, "ViewObject", None) is not None
        },
        "history": history(active_document),
    }


def require_same_state(actual, expected, label):
    for key in expected:
        if key == "history":
            continue
        if actual[key] != expected[key]:
            raise RuntimeError("{} changed {}".format(label, key))


def image_checked(path):
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("The GUI image is absent or invalid: {}".format(path))
    return str(path)


def capture_panel(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    manager.show()
    manager.mode_tabs.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()
    if not panel.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture the crossover panel")
    return image_checked(path)


def capture_top(filename, panel_open=True):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    if panel_open:
        manager.hide()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(path), 1600, 1000, "Current")
    if panel_open:
        manager.show()
    return image_checked(path)


def run_confirmation(action, expected_title, fault_text=None, image_name=None):
    seen = {
        "active": True, "questions": [], "failures": [],
        "unexpected": [], "monitor_errors": [],
    }

    def monitor():
        if not seen["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                    continue
                title = str(widget.windowTitle())
                message = "{}\n{}".format(
                    widget.text(), widget.informativeText()
                )
                yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                if yes is not None and not seen["questions"]:
                    seen["questions"].append(message)
                    yes.click()
                elif (fault_text is not None
                      and expected_title in title
                      and fault_text in message
                      and not seen["failures"]):
                    path = pathlib.Path(
                        TRACKTEMPLATE_PHASE8_VISUAL_DIR
                    ) / image_name
                    if not widget.grab().save(str(path), "PNG"):
                        raise RuntimeError("Qt could not capture integration error")
                    seen["failures"].append({
                        "title": title,
                        "message": message,
                        "visual": image_checked(path),
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
    expected_failures = 1 if fault_text is not None else 0
    if (len(seen["questions"]) != 1
            or len(seen["failures"]) != expected_failures
            or seen["unexpected"] or seen["monitor_errors"]):
        raise RuntimeError("Crossover integration dialogs changed: {}".format(seen))
    return {
        "question": seen["questions"][0],
        "failure": seen["failures"][0] if seen["failures"] else None,
    }


def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The crossover GUI choice is absent: " + value)
    combo.setCurrentIndex(index)


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
    choose(panel.arrangement_combo, module.CROSSOVER_ARRANGEMENT_FACING)
    choose(panel.handing_combo, module.CROSSOVER_HAND_AUTO)
    panel.gauge_box.setValue(16.5)
    panel.flangeway_box.setValue(1.0)
    panel.minimum_radius_box.setValue(600.0)
    panel.chainage_box.setValue(746.298)
    if panel.preview_geometry() is None:
        raise RuntimeError("The fixed XO-001 GUI creation preview failed")
    creation = run_confirmation(
        panel.create_crossover, "Crossover creation error"
    )
    panel.refresh_crossovers("XO-001")
    if len(document.Objects) != 18 or history(document)["undo_count"] != 1:
        raise RuntimeError("The fixed GUI XO-001 creation changed")

    panel.apply_b4_button.click()
    panel.refresh_crossovers("XO-001")
    b4_config = panel.current_config()
    if not isinstance((b4_config or {}).get("b4_result"), dict):
        raise RuntimeError("The GUI did not store a B4 result")
    panel.chair_analysis_panel.run_analysis()
    panel.refresh_crossovers("XO-001")
    before = state(document)
    roles = {item["role"] for item in before["chair_display"].values()}
    if (len(before["object_names"]) != 22
            or before["index_count"] != 8
            or len(before["chair_display"]) != 2
            or module.CHAIR_ANALYSIS_GROUP_ROLE not in roles
            or module.CHAIR_POSITION_MARKER_ROLE not in roles
            or not any(
                item["role"] == module.CHAIR_POSITION_MARKER_ROLE
                and item["visible"] and item["shape"] is not None
                for item in before["chair_display"].values()
            )
            or not before["chair_signature"]):
        raise RuntimeError("The GUI lacks fixed B4 and visible chair evidence")
    before_visuals = [
        capture_panel("xo-001-before-integration-panel.png"),
        capture_top("xo-001-before-integration-top-view.png"),
    ]

    original_builder = module.build_crossover_host_integration
    fault_text = "Phase 8 injected host integration preflight failure"
    calls = {"builder": 0}

    def failing_builder(active_document, crossover_id):
        calls["builder"] += 1
        raise RuntimeError(fault_text)

    module.build_crossover_host_integration = failing_builder
    try:
        rejected_create = run_confirmation(
            panel.integrate_selected_crossover,
            "Crossover host-integration error",
            fault_text=fault_text,
            image_name="xo-001-rejected-integration-dialog.png",
        )
    finally:
        module.build_crossover_host_integration = original_builder
    if calls["builder"] != 1:
        raise RuntimeError("The GUI create did not reach its preflight")
    after_rejected_create = state(document)
    require_same_state(after_rejected_create, before, "Rejected integration")
    if after_rejected_create["history"] != before["history"]:
        raise RuntimeError("Rejected integration changed Undo history")
    rejected_create_visual = capture_top(
        "xo-001-after-rejected-integration-top-view.png"
    )

    rejected_remove = run_confirmation(
        panel.remove_selected_integration,
        "Remove host integration error",
        fault_text="has no host integration to remove",
        image_name="xo-001-rejected-removal-dialog.png",
    )
    after_rejected_remove = state(document)
    require_same_state(after_rejected_remove, before, "Rejected removal")
    if after_rejected_remove["history"] != before["history"]:
        raise RuntimeError("Rejected removal changed Undo history")
    rejected_remove_visual = capture_top(
        "xo-001-after-rejected-removal-top-view.png"
    )

    integrated_confirmation = run_confirmation(
        panel.integrate_selected_crossover,
        "Crossover host-integration error",
    )
    integrated_diagnostics = str(panel.diagnostics.toPlainText())
    panel.refresh_crossovers("XO-001")
    integrated = state(document)
    source_ids = set(str(item) for item in (
        integrated["integration_result"].get("source_record_ids") or []
    ))
    integrated_records = [
        record for record in integrated["index"]["records"]
        if str(record.get("source_name") or "")
        in integrated["integration_names"]
    ]
    if (len(integrated["object_names"]) != 26
            or integrated["index_count"] != 7
            or len(integrated["integration_names"]) != 6
            or len(integrated_records) != 3
            or {str(record.get("role") or "") for record in integrated_records}
            != {
                module.CROSSOVER_INTEGRATED_TEMPLATE_ROLE,
                module.CROSSOVER_INTEGRATED_OUTLINE_ROLE,
                module.CROSSOVER_INTEGRATED_TIMBER_ROLE,
            }
            or not source_ids
            or source_ids & set(integrated["index_ids"])
            or not integrated["integration_active"]
            or integrated["effective_status"]
            != module.CROSSOVER_INTEGRATION_STATUS_ACTIVE
            or integrated["chair_display"]
            or integrated["history"]["undo_count"]
            != before["history"]["undo_count"] + 1
            or integrated["history"]["redo_count"]):
        raise RuntimeError("GUI integration did not replace records atomically")
    if (module.CROSSOVER_INTEGRATION_STATUS_ACTIVE
            not in integrated_diagnostics
            or "Production ready: No" not in integrated_diagnostics):
        raise RuntimeError("The GUI integration diagnostics changed")
    integrated_visuals = [
        capture_panel("xo-001-integrated-panel.png"),
        capture_top("xo-001-integrated-top-view.png"),
    ]

    document.undo()
    document.recompute()
    undone_create = state(document)
    require_same_state(undone_create, before, "Integration Undo")
    if (undone_create["history"]["undo_count"]
            != before["history"]["undo_count"]
            or undone_create["history"]["redo_count"] != 1):
        raise RuntimeError("Integration Undo changed history")
    undo_create_visual = capture_top("xo-001-integration-undo-top-view.png")

    document.redo()
    document.recompute()
    redone_create = state(document)
    require_same_state(redone_create, integrated, "Integration Redo")
    if (redone_create["history"]["undo_count"]
            != integrated["history"]["undo_count"]
            or redone_create["history"]["redo_count"]):
        raise RuntimeError("Integration Redo changed history")

    manager.close()
    QtWidgets.QApplication.processEvents()
    before_integrated_save = state(document)
    require_same_state(
        before_integrated_save, integrated, "Closing integration panel"
    )
    document.save()
    integrated_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(integrated_path)
    document.UndoMode = 1
    reopened_integrated = state(document)
    require_same_state(
        reopened_integrated, before_integrated_save,
        "Integrated copied FCStd save/reopen",
    )
    if (reopened_integrated["history"]["undo_count"]
            or reopened_integrated["history"]["redo_count"]):
        raise RuntimeError("Integrated reopen retained prior session history")
    reopened_integrated_visual = capture_top(
        "xo-001-reopened-integrated-top-view.png", panel_open=False
    )

    manager = module.TurnoutManagerDialog(document)
    manager.show()
    manager.mode_tabs.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()
    panel = manager.crossover_panel
    panel.refresh_crossovers("XO-001")
    removed_confirmation = run_confirmation(
        panel.remove_selected_integration, "Remove host integration error"
    )
    removed_diagnostics = str(panel.diagnostics.toPlainText())
    panel.refresh_crossovers("XO-001")
    removed = state(document)
    if (len(removed["object_names"]) != 20
            or removed["index_count"] != 8
            or removed["integration_names"]
            or removed["integration_active"]
            or not source_ids <= set(removed["index_ids"])
            or removed["chair_display"]
            or removed["history"]["undo_count"] != 1
            or removed["history"]["redo_count"]):
        raise RuntimeError("GUI removal did not restore production records")
    if (module.CROSSOVER_INTEGRATION_STATUS_READY
            not in removed_diagnostics
            or "Production ready: No" not in removed_diagnostics):
        raise RuntimeError("The GUI removal diagnostics changed")
    removed_visuals = [
        capture_panel("xo-001-removed-integration-panel.png"),
        capture_top("xo-001-removed-integration-top-view.png"),
    ]

    document.undo()
    document.recompute()
    undone_remove = state(document)
    require_same_state(
        undone_remove, reopened_integrated, "Removal Undo"
    )
    if (undone_remove["history"]["undo_count"]
            or undone_remove["history"]["redo_count"] != 1):
        raise RuntimeError("Removal Undo changed history")
    undo_remove_visual = capture_top("xo-001-removal-undo-top-view.png")

    document.redo()
    document.recompute()
    redone_remove = state(document)
    require_same_state(redone_remove, removed, "Removal Redo")
    if (redone_remove["history"]["undo_count"] != 1
            or redone_remove["history"]["redo_count"]):
        raise RuntimeError("Removal Redo changed history")
    redo_remove_visual = capture_top("xo-001-removal-redo-top-view.png")

    manager.close()
    QtWidgets.QApplication.processEvents()
    before_removed_save = state(document)
    require_same_state(before_removed_save, removed, "Closing removal panel")
    document.save()
    App.closeDocument(str(document.Name))
    document = App.openDocument(integrated_path)
    reopened_removed = state(document)
    require_same_state(
        reopened_removed, before_removed_save,
        "Removed copied FCStd save/reopen",
    )
    if (reopened_removed["history"]["undo_count"]
            or reopened_removed["history"]["redo_count"]):
        raise RuntimeError("Removed reopen retained prior session history")
    reopened_removed_visual = capture_top(
        "xo-001-reopened-removed-top-view.png", panel_open=False
    )

    print(json.dumps({
        "sentinel": "PHASE8_CROSSOVER_HOST_INTEGRATION_RECOVERY_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "routing": {
            "route": routing["route"],
            "schema_version": routing["schema_version"],
        },
        "selected_binding": type(adapter).__name__,
        "hosts": {
            "a": selection["host_a_identity"],
            "b": selection["host_b_identity"],
        },
        "creation_confirmation": creation["question"],
        "before": {
            "object_count": len(before["object_names"]),
            "index_count": before["index_count"],
            "chair_display": before["chair_display"],
            "history": before["history"],
            "visuals": before_visuals,
        },
        "rejected_create": {
            "dialog": rejected_create["failure"],
            "builder_calls": calls["builder"],
            "state_unchanged": True,
            "visual": rejected_create_visual,
        },
        "rejected_remove": {
            "dialog": rejected_remove["failure"],
            "state_unchanged": True,
            "visual": rejected_remove_visual,
        },
        "integrated": {
            "confirmation": integrated_confirmation["question"],
            "diagnostics": integrated_diagnostics,
            "object_count": len(integrated["object_names"]),
            "index_count": integrated["index_count"],
            "integrated_record_count": len(integrated_records),
            "source_record_ids": sorted(source_ids),
            "integration_objects": integrated["integration_names"],
            "effective_status": integrated["effective_status"],
            "history": integrated["history"],
            "visuals": integrated_visuals,
        },
        "integration_undo": {
            "object_count": len(undone_create["object_names"]),
            "index_count": undone_create["index_count"],
            "chair_display_restored": True,
            "history": undone_create["history"],
            "visual": undo_create_visual,
        },
        "integration_redo": {
            "object_count": len(redone_create["object_names"]),
            "index_count": redone_create["index_count"],
            "history": redone_create["history"],
        },
        "reopened_integrated": {
            "object_count": len(reopened_integrated["object_names"]),
            "index_count": reopened_integrated["index_count"],
            "history": reopened_integrated["history"],
            "visual": reopened_integrated_visual,
        },
        "removed": {
            "confirmation": removed_confirmation["question"],
            "diagnostics": removed_diagnostics,
            "object_count": len(removed["object_names"]),
            "index_count": removed["index_count"],
            "restored_record_ids": sorted(source_ids),
            "history": removed["history"],
            "visuals": removed_visuals,
        },
        "removal_undo": {
            "object_count": len(undone_remove["object_names"]),
            "index_count": undone_remove["index_count"],
            "history": undone_remove["history"],
            "visual": undo_remove_visual,
        },
        "removal_redo": {
            "object_count": len(redone_remove["object_names"]),
            "index_count": redone_remove["index_count"],
            "history": redone_remove["history"],
            "visual": redo_remove_visual,
        },
        "reopened_removed": {
            "object_count": len(reopened_removed["object_names"]),
            "index_count": reopened_removed["index_count"],
            "history": reopened_removed["history"],
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
        ROOT / "tools/freecad_bridge/b14_recipe.py",
        ROOT / "tools/freecad_bridge/crossover_timber_recipe.py",
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
    raise RuntimeError('The integration GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != (
        "PHASE8_CROSSOVER_HOST_INTEGRATION_RECOVERY_GUI_PROBE_PASS"
    ):
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"):
        raise RuntimeError("The real GUI proof used another FreeCAD profile")
    if (probe["selected_binding"]
            != "CrossoverHostIntegrationRecoveryAdapter"
            or probe["rejected_create"]["state_unchanged"] is not True
            or probe["rejected_create"]["builder_calls"] != 1
            or probe["rejected_remove"]["state_unchanged"] is not True
            or probe["before"]["object_count"] != 22
            or probe["before"]["index_count"] != 8
            or probe["integrated"]["object_count"] != 26
            or probe["integrated"]["index_count"] != 7
            or probe["integrated"]["integrated_record_count"] != 3
            or probe["integration_undo"]["chair_display_restored"] is not True
            or probe["integration_undo"]["index_count"] != 8
            or probe["integration_redo"]["index_count"] != 7
            or probe["reopened_integrated"]["index_count"] != 7
            or probe["removed"]["object_count"] != 20
            or probe["removed"]["index_count"] != 8
            or probe["removal_undo"]["index_count"] != 7
            or probe["removal_redo"]["index_count"] != 8
            or probe["reopened_removed"]["index_count"] != 8):
        raise RuntimeError("The GUI integration lifecycle contract changed")
    return [
        *probe["before"]["visuals"],
        probe["rejected_create"]["dialog"]["visual"],
        probe["rejected_create"]["visual"],
        probe["rejected_remove"]["dialog"]["visual"],
        probe["rejected_remove"]["visual"],
        *probe["integrated"]["visuals"],
        probe["integration_undo"]["visual"],
        probe["reopened_integrated"]["visual"],
        *probe["removed"]["visuals"],
        probe["removal_undo"]["visual"],
        probe["removal_redo"]["visual"],
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
        raise SystemExit("The isolated integration GUI proof requires port 19875")
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
    document_path = run_dir / "crossover-host-integration-recovery.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-crossover-host-integration-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "fixed curved XO-001 host integration and production records, "
            "rejected actions, one Undo/Redo per operation and copied reopen"
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
    raise RuntimeError('The integration GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 crossover host integration real GUI", args.timeout,
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
            "Phase 8 crossover integration GUI evidence: {}".format(run_dir),
            flush=True,
        )
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
