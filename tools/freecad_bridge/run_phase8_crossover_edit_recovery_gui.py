#!/usr/bin/env python3
"""Check B16 crossover edit recovery with live chair display in FreeCAD GUI."""

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
    "phase8-crossover-edit-recovery-gui-runs"
)
SENTINEL = "PHASE8_CROSSOVER_EDIT_RECOVERY_GUI_PASS"


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import b14_recipe
from tools.freecad_bridge import crossover_timber_recipe as recipe
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
)
from tracktemplate.compatibility.crossover_preflight import (
    CrossoverPreflightAdapter,
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
edit_binding = getattr(module.edit_rea_c10_crossover, "__self__", None)
if (not isinstance(edit_binding, CrossoverPreflightAdapter)
        or edit_binding.module is not module
        or getattr(module.edit_rea_c10_crossover, "__func__", None)
        is not CrossoverPreflightAdapter.edit):
    raise RuntimeError("The GUI edit action is not routed through B16")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(item) for item in active_document.UndoNames],
        "redo_names": [str(item) for item in active_document.RedoNames],
    }


def state(active_document):
    ordinary = ordinary_track_document_snapshot(module, active_document)
    timber = recipe.document_snapshot(module, active_document, "XO-001")
    group = dict(timber["objects"]["ModelRailwayCurve"])
    if group["type_id"] != "App::DocumentObjectGroup":
        raise RuntimeError("The model group type changed")
    group.pop("shape", None)
    reopen_semantic = dict(timber)
    reopen_semantic["objects"] = dict(timber["objects"])
    reopen_semantic["objects"]["ModelRailwayCurve"] = group
    return {
        "ordinary_sha256": ordinary["semantic_sha256"],
        "ordinary_semantic": ordinary["semantic"],
        "timber_sha256": recipe.digest(timber),
        "timber_semantic": timber,
        "reopen_semantic": reopen_semantic,
        "object_names": sorted(str(obj.Name) for obj in active_document.Objects),
        "group_members": {
            str(obj.Name): [str(member.Name) for member in obj.Group]
            for obj in active_document.Objects
            if "Group" in (getattr(obj, "PropertiesList", ()) or ())
        },
        "visibility": {
            str(obj.Name): bool(obj.ViewObject.Visibility)
            for obj in active_document.Objects
            if getattr(obj, "ViewObject", None) is not None
        },
        "history": history(active_document),
    }


def require_same_document(actual, expected, label, *, reopen=False):
    for key in (
        "ordinary_sha256",
        "ordinary_semantic",
        "object_names",
        "group_members",
    ):
        if actual[key] != expected[key]:
            raise RuntimeError("{} changed copied document {}".format(label, key))
    if reopen:
        if actual["reopen_semantic"] != expected["reopen_semantic"]:
            raise RuntimeError("{} changed crossover persistence".format(label))
    elif actual["timber_semantic"] != expected["timber_semantic"]:
        raise RuntimeError("{} changed crossover state".format(label))
    if actual["visibility"] != expected["visibility"]:
        names = sorted(
            name for name in (
                set(actual["visibility"]) | set(expected["visibility"])
            )
            if actual["visibility"].get(name)
            != expected["visibility"].get(name)
        )
        raise RuntimeError("{} changed GUI visibility: {}".format(label, names))


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


def run_confirmation(action, fault_text=None):
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
                      and "Crossover creation error" in title
                      and fault_text in message
                      and not seen["failures"]):
                    path = pathlib.Path(
                        TRACKTEMPLATE_PHASE8_VISUAL_DIR
                    ) / "edit-failure-dialog.png"
                    if not widget.grab().save(str(path), "PNG"):
                        raise RuntimeError("Qt could not capture edit failure")
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
        raise RuntimeError("Crossover edit dialogs changed: {}".format(seen))
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
    base = state(document)
    if len(base["object_names"]) != 9 or base["history"]["undo_count"]:
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
    created_dialog = run_confirmation(panel.create_crossover)
    panel.refresh_crossovers("XO-001")
    created = state(document)
    if (len(created["object_names"]) != 18
            or created["history"]["undo_count"] != 1):
        raise RuntimeError("The fixed GUI XO-001 creation changed")

    panel.apply_b4_button.click()
    panel.refresh_crossovers("XO-001")
    b4_config = panel.current_config()
    if not isinstance((b4_config or {}).get("b4_result"), dict):
        raise RuntimeError("The GUI did not store a B4 result")
    if module._crossover_b4_object(document, "XO-001") is None:
        raise RuntimeError("The GUI did not create B4 display geometry")

    panel.chair_analysis_panel.run_analysis()
    panel.refresh_crossovers("XO-001")
    pre_edit_config = panel.current_config()
    if (not isinstance(pre_edit_config, dict)
            or not pre_edit_config.get("chair_analysis_signature")):
        raise RuntimeError("The GUI did not retain chair analysis")
    pre_edit_chair = chair_display(document)
    chair_roles = {item["role"] for item in pre_edit_chair.values()}
    if (module.CHAIR_ANALYSIS_GROUP_ROLE not in chair_roles
            or module.CHAIR_POSITION_MARKER_ROLE not in chair_roles
            or not any(
                item["role"] == module.CHAIR_POSITION_MARKER_ROLE
                and item["visible"]
                and item["shape"] is not None
                for item in pre_edit_chair.values()
            )):
        raise RuntimeError("The GUI lacks a visible real chair display")
    pre_edit = state(document)
    pre_edit_b4 = module._crossover_b4_object(document, "XO-001")
    pre_edit_b4_visible = bool(
        pre_edit_b4.ViewObject.Visibility
    ) if pre_edit_b4 is not None else False
    if (pre_edit_b4 is None
            or not pre_edit_b4_visible
            or len(pre_edit["object_names"]) <= 20):
        raise RuntimeError("The pre-edit B4/chair display changed")
    before_visuals = [
        capture_panel("xo-001-before-edit-panel.png"),
        capture_top("xo-001-before-edit-top-view.png"),
    ]

    panel.begin_crossover_edit()
    if panel.editing_crossover_id != "XO-001":
        raise RuntimeError("The GUI did not enter XO-001 edit mode")
    panel.chainage_box.setValue(746.299)
    preview = panel.preview_geometry()
    if preview is None:
        raise RuntimeError(
            "The changed-toe GUI edit preview failed: {}".format(
                panel.diagnostics.toPlainText()
            )
        )
    after_preview = state(document)
    require_same_document(after_preview, pre_edit, "Edit preview")
    if after_preview["history"] != pre_edit["history"]:
        raise RuntimeError("Edit preview changed Undo/Redo history")
    preview_visual = capture_panel("xo-001-edit-preview-panel.png")

    original_tagger = module.tag_generated_object
    fault_text = "Phase 8 injected crossover edit template-tag failure"
    fault = {"calls": 0}

    def failing_tagger(obj, role, template_set_id):
        if role == module.CROSSOVER_TEMPLATE_ROLE:
            fault["calls"] += 1
            raise RuntimeError(fault_text)
        return original_tagger(obj, role, template_set_id)

    module.tag_generated_object = failing_tagger
    try:
        failed_dialog = run_confirmation(
            panel.create_crossover, fault_text=fault_text
        )
    finally:
        module.tag_generated_object = original_tagger
    if fault["calls"] != 1:
        raise RuntimeError("The GUI edit did not reach the injected tag")
    failed = state(document)
    require_same_document(failed, pre_edit, "Aborted crossover edit")
    if (failed["history"] != pre_edit["history"]
            or chair_display(document) != pre_edit_chair
            or panel.editing_crossover_id != "XO-001"):
        raise RuntimeError("The aborted edit lost display or Undo state")
    failure_visual = capture_top("xo-001-after-failed-edit-top-view.png")

    edit_dialog = run_confirmation(panel.create_crossover)
    panel.refresh_crossovers("XO-001")
    edited_config = panel.current_config()
    edited = state(document)
    if (edited_config is None
            or edited_config.get("crossover_id") != "XO-001"
            or int(edited_config.get("edit_revision") or 0) != 1
            or abs(float(edited_config.get("toe_chainage_a") or 0)
                   - 746.299) > 1.0e-9
            or edited_config.get("b4_result")
            or edited_config.get("chair_analysis_signature")):
        raise RuntimeError("The accepted edit did not invalidate old analysis")
    if (module._crossover_b4_object(document, "XO-001") is not None
            or chair_display(document)
            or len(edited["object_names"]) != 18
            or edited["history"]["undo_count"]
            != pre_edit["history"]["undo_count"] + 1
            or edited["history"]["redo_count"] != 0):
        raise RuntimeError("The accepted edit retained old display or history")
    edited_visuals = [
        capture_panel("xo-001-after-edit-panel.png"),
        capture_top("xo-001-after-edit-top-view.png"),
    ]

    document.undo()
    document.recompute()
    undone = state(document)
    require_same_document(undone, pre_edit, "Crossover edit Undo")
    if (undone["history"]["undo_count"]
            != pre_edit["history"]["undo_count"]
            or undone["history"]["redo_count"] != 1
            or chair_display(document) != pre_edit_chair):
        raise RuntimeError("Edit Undo did not restore the old display")
    undo_visual = capture_top("xo-001-after-undo-top-view.png")

    document.redo()
    document.recompute()
    redone = state(document)
    require_same_document(redone, edited, "Crossover edit Redo")
    if (redone["history"]["undo_count"]
            != pre_edit["history"]["undo_count"] + 1
            or redone["history"]["redo_count"] != 0
            or chair_display(document)):
        raise RuntimeError("Edit Redo did not restore edited state")

    manager.close()
    QtWidgets.QApplication.processEvents()
    before_save = state(document)
    require_same_document(before_save, edited, "Closing edit panel")
    document.save()
    saved_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(saved_path)
    reopened = state(document)
    require_same_document(
        reopened, before_save, "Copied FCStd save/reopen", reopen=True
    )
    if (reopened["history"]["undo_count"]
            or reopened["history"]["redo_count"]
            or chair_display(document)
            or module._crossover_b4_object(document, "XO-001") is not None):
        raise RuntimeError("Edited crossover changed on save/reopen")
    reopened_visual = capture_top(
        "xo-001-reopened-after-edit-top-view.png", panel_open=False
    )

    print(json.dumps({
        "sentinel": "PHASE8_CROSSOVER_EDIT_RECOVERY_GUI_PROBE_PASS",
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
        "creation_confirmation": created_dialog["question"],
        "pre_edit": {
            "object_count": len(pre_edit["object_names"]),
            "timber_sha256": pre_edit["timber_sha256"],
            "history": pre_edit["history"],
            "chair_display": pre_edit_chair,
            "b4_visible": pre_edit_b4_visible,
            "visuals": before_visuals,
        },
        "preview": {
            "toe_chainage_a_mm": float(preview["toe_chainage_a"]),
            "state_unchanged": True,
            "visual": preview_visual,
        },
        "failure": {
            "dialog": failed_dialog["failure"],
            "tag_calls": fault["calls"],
            "state_unchanged": True,
            "visual": failure_visual,
        },
        "edit": {
            "confirmation": edit_dialog["question"],
            "object_count": len(edited["object_names"]),
            "timber_sha256": edited["timber_sha256"],
            "history": edited["history"],
            "edit_revision": int(edited_config["edit_revision"]),
            "toe_chainage_a_mm": float(edited_config["toe_chainage_a"]),
            "old_display_removed": True,
            "visuals": edited_visuals,
        },
        "undo": {
            "object_count": len(undone["object_names"]),
            "timber_sha256": undone["timber_sha256"],
            "history": undone["history"],
            "old_display_restored": True,
            "visual": undo_visual,
        },
        "redo": {
            "object_count": len(redone["object_names"]),
            "timber_sha256": redone["timber_sha256"],
            "history": redone["history"],
            "old_display_absent": True,
        },
        "save_reopen": {
            "path": saved_path,
            "object_count": len(reopened["object_names"]),
            "timber_sha256": reopened["timber_sha256"],
            "history": reopened["history"],
            "visual": reopened_visual,
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
        ROOT / "tools/freecad_bridge/ordinary_track_recipe.py",
        pathlib.Path(__file__).resolve(),
        ROOT / "tools/freecad_bridge/run-phase8-crossover-edit-recovery-gui",
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
    raise RuntimeError('The edit GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != "PHASE8_CROSSOVER_EDIT_RECOVERY_GUI_PROBE_PASS":
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"):
        raise RuntimeError("The real GUI proof used another FreeCAD profile")
    if (probe["pre_edit"]["b4_visible"] is not True
            or probe["preview"]["state_unchanged"] is not True
            or probe["failure"]["state_unchanged"] is not True
            or probe["failure"]["tag_calls"] != 1
            or probe["edit"]["old_display_removed"] is not True
            or probe["undo"]["old_display_restored"] is not True
            or probe["redo"]["old_display_absent"] is not True
            or probe["edit"]["edit_revision"] != 1
            or probe["edit"]["object_count"] != 18
            or probe["save_reopen"]["object_count"] != 18):
        raise RuntimeError("The GUI edit recovery contract changed")
    return [
        *probe["pre_edit"]["visuals"],
        probe["preview"]["visual"],
        probe["failure"]["dialog"]["visual"],
        probe["failure"]["visual"],
        *probe["edit"]["visuals"],
        probe["undo"]["visual"],
        probe["save_reopen"]["visual"],
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
        raise SystemExit("The isolated edit GUI proof requires port 19875")
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
    document_path = run_dir / "crossover-edit-recovery.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-crossover-edit-display-recovery-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "fixed curved XO-001 GUI edit with B4 and chair display, "
            "injected edit failure, one Undo/Redo and copied save/reopen"
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
    raise RuntimeError('The edit GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 crossover edit recovery real GUI", args.timeout,
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
        print("Phase 8 crossover edit GUI evidence: {}".format(run_dir), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
