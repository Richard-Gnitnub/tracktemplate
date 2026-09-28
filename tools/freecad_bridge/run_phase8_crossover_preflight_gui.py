#!/usr/bin/env python3
"""Check the B16 crossover radius preflight in a real FreeCAD GUI."""

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
CONTRACT_PATH = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
FIXTURE_PATH = ROOT / "benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd"
LOADER_PATH = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = ROOT / "benchmark-output/freecad-bridge/phase8-crossover-preflight-gui-runs"
SENTINEL = "PHASE8_CROSSOVER_PREFLIGHT_GUI_PASS"


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge import b14_recipe
from tools.freecad_bridge.ordinary_track_recipe import ordinary_track_document_snapshot


module = _PHASE3_SESSION.module
document = App.ActiveDocument
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied fixture in a real GUI first")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if _PHASE3_ROUTING.get("route") != "modular":
    raise RuntimeError("The B16 product route is not active")

manager = module.TurnoutManagerDialog(document)
manager.show()
QtWidgets.QApplication.processEvents()
panel = manager.crossover_panel
panel.refresh_hosts()
selection = b14_recipe.select_crossover_hosts(
    panel.hosts,
    module.object_string_property,
    module._integer_object_property,
)
panel.host_a_combo.setCurrentIndex(selection["a"])
panel.host_b_combo.setCurrentIndex(selection["b"])


def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The inherited GUI choice is absent: " + value)
    combo.setCurrentIndex(index)


choose(panel.arrangement_combo, module.CROSSOVER_ARRANGEMENT_FACING)
choose(panel.handing_combo, module.CROSSOVER_HAND_AUTO)
panel.gauge_box.setValue(16.5)
panel.flangeway_box.setValue(1.0)
panel.minimum_radius_box.setValue(600.0)


def history():
    return {
        "undo_count": int(document.UndoCount),
        "redo_count": int(document.RedoCount),
        "undo_names": [str(value) for value in document.UndoNames],
        "redo_names": [str(value) for value in document.RedoNames],
    }


def state():
    semantic = ordinary_track_document_snapshot(module, document)
    return {
        "semantic_sha256": semantic["semantic_sha256"],
        "object_names": [str(obj.Name) for obj in document.Objects],
        "history": history(),
        "crossover_configs": module.existing_crossover_configs(document),
    }


def save_visual(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    panel.show()
    manager.show()
    QtWidgets.QApplication.processEvents()
    if not panel.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture crossover diagnostics")
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("Crossover GUI image is absent or invalid")
    return str(path)


def confirm_create(action):
    observed = {"active": True, "questions": [], "unexpected": []}

    def monitor():
        if not observed["active"]:
            return
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                continue
            message = "{}\n{}".format(widget.text(), widget.informativeText())
            yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
            if yes is None:
                observed["unexpected"].append(message)
                widget.accept()
            elif not observed["questions"]:
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


try:
    before = state()
    if len(before["object_names"]) != 9 or before["history"]["undo_count"]:
        raise RuntimeError("The copied crossover fixture is not at its base state")

    panel.chainage_box.setValue(500.0)
    rejected = panel.preview_geometry()
    rejection_text = str(panel.diagnostics.toPlainText())
    if rejected is not None or not all(
        item in rejection_text for item in (
            "REJECTED", "Host Track B", "540.848", "600.000",
            "Connector solver status: accepted",
        )
    ):
        raise RuntimeError("The 500 mm GUI preview did not name the limiting Host B radius")
    after_preview = state()
    if after_preview != before:
        raise RuntimeError("Rejected GUI preview changed objects, persistence or history")
    rejected_visual = save_visual("rejected-500-mm-panel.png")
    panel.create_crossover()
    after_create_attempt = state()
    if after_create_attempt != before:
        raise RuntimeError("Rejected GUI create changed objects, persistence or history")

    panel.chainage_box.setValue(746.298)
    accepted = panel.preview_geometry()
    if accepted is None:
        raise RuntimeError("The 746.298 mm GUI preview was rejected: {}".format(panel.diagnostics.toPlainText()))
    preflight = dict(accepted.get("complete_radius_preflight") or {})
    if not preflight.get("accepted") or len(str(preflight.get("input_signature") or "")) != 64:
        raise RuntimeError("The accepted GUI preview has no complete signed radius result")
    positive_text = str(panel.diagnostics.toPlainText())
    if "Complete crossover minimum radius" not in positive_text:
        raise RuntimeError("The accepted GUI preview did not show the full radius decision")
    preview_visual = save_visual("accepted-746-mm-preview.png")
    confirmation = confirm_create(panel.create_crossover)
    configs = module.existing_crossover_configs(document)
    if len(configs) != 1 or configs[0].get("crossover_id") != "XO-001":
        raise RuntimeError("The accepted GUI action did not create XO-001")
    config = configs[0]
    if abs(float(config["toe_chainage_a"]) - 746.298) > 1.0e-9:
        raise RuntimeError("The created crossover has another Host A chainage")
    if float(config["minimum_resulting_radius"]) < 600.0:
        raise RuntimeError("The created crossover violated its minimum radius")
    created = state()
    if len(created["object_names"]) <= len(before["object_names"]):
        raise RuntimeError("The accepted GUI crossover has no managed objects")
    if created["history"]["undo_count"] != 1:
        raise RuntimeError("GUI crossover creation did not make one transaction")
    created_visual = save_visual("created-crossover-panel.png")

    panel.begin_crossover_edit()
    if panel.editing_crossover_id != "XO-001":
        raise RuntimeError("The crossover manager did not enter edit mode")
    panel.chainage_box.setValue(500.0)
    edit_preview = panel.preview_geometry()
    edit_rejection_text = str(panel.diagnostics.toPlainText())
    if edit_preview is not None or "Host Track B" not in edit_rejection_text:
        raise RuntimeError("The invalid crossover edit passed GUI preview")
    after_edit_preview = state()
    if after_edit_preview != created:
        raise RuntimeError("Rejected GUI edit preview changed XO-001 or history")
    edit_visual = save_visual("rejected-edit-500-mm-panel.png")
    panel.create_crossover()
    if state() != created:
        raise RuntimeError("Rejected GUI edit changed XO-001 or history")
    panel.cancel_crossover_edit()

    print(json.dumps({
        "sentinel": "PHASE8_CROSSOVER_PREFLIGHT_GUI_PROBE_PASS",
        "profile": _PHASE3_QUALIFICATION["compatibility_evaluation"]["matched_profile_id"],
        "host_a_identity": selection["host_a_identity"],
        "host_b_identity": selection["host_b_identity"],
        "negative": {
            "diagnostic": rejection_text,
            "base_semantic_sha256": before["semantic_sha256"],
            "after_preview_semantic_sha256": after_preview["semantic_sha256"],
            "after_create_semantic_sha256": after_create_attempt["semantic_sha256"],
            "history": before["history"],
            "visual": rejected_visual,
        },
        "positive": {
            "diagnostic": positive_text,
            "toe_chainage_a_mm": float(accepted["toe_chainage_a"]),
            "toe_chainage_b_mm": float(accepted["toe_chainage_b"]),
            "preflight": preflight,
            "connector_minimum_radius_mm": accepted["connector"].get("minimum_radius"),
            "built_turnout_a_minimum_radius_mm": config["turnout_a_config"]["turnout_minimum_radius_sampled"],
            "built_turnout_b_minimum_radius_mm": config["turnout_b_config"]["turnout_minimum_radius_sampled"],
            "built_connector_minimum_radius_mm": config["connector_minimum_radius"],
            "built_complete_minimum_radius_mm": config["minimum_resulting_radius"],
            "confirmation": confirmation,
            "preview_visual": preview_visual,
            "created_visual": created_visual,
            "history": created["history"],
        },
        "edit_negative": {
            "diagnostic": edit_rejection_text,
            "semantic_sha256": after_edit_preview["semantic_sha256"],
            "history": after_edit_preview["history"],
            "visual": edit_visual,
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
        LOADER_PATH,
        pathlib.Path(__file__).resolve(),
        ROOT / "tools/freecad_bridge/run-phase8-crossover-preflight-gui",
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
if App.listDocuments():
    raise RuntimeError('The crossover GUI proof left documents open')
print(json.dumps({'closed': closed, 'remaining': []}, sort_keys=True))
"""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=pathlib.Path, default=FIXTURE_PATH)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated crossover GUI proof requires port 19875")
    base = args.base.resolve()
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not base.is_file() or not token.is_file():
        raise SystemExit("The copied fixture or isolated bridge token is absent")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    if sha256(base) != contract["fixture"]["sha256"]:
        raise SystemExit("The fixed crossover fixture identity drifted")
    source_hashes = _source_hashes()
    fixture_hash = sha256(base)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "phase8-crossover-preflight.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-crossover-complete-radius-preflight-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": "development-only curved-host crossover preview, create and rejected edit",
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
    raise RuntimeError('The crossover proof requires an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER_PATH.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 crossover radius real GUI", args.timeout,
        )
        proof = parse_json_output(job)
        if proof.get("sentinel") != "PHASE8_CROSSOVER_PREFLIGHT_GUI_PROBE_PASS":
            raise RuntimeError("The GUI probe did not return its success sentinel")
        state["probe"] = proof
        expected = contract["witnesses"][1]
        positive = proof["positive"]
        tolerance = contract["request"]["comparison_tolerance_mm"]
        preflight = positive["preflight"]
        for actual_key, wanted_key in (
            ("turnout_a_minimum_radius_mm", "turnout_a_mapped_minimum_radius_mm"),
            ("turnout_b_minimum_radius_mm", "turnout_b_mapped_minimum_radius_mm"),
            ("connector_minimum_radius_mm", "connector_minimum_radius_mm"),
            ("complete_minimum_radius_mm", "complete_minimum_radius_mm"),
        ):
            if abs(float(preflight[actual_key]) - float(expected[wanted_key])) > tolerance:
                raise RuntimeError("The accepted GUI preflight radius differs from the oracle: " + actual_key)
        for side in ("a", "b"):
            actual = positive["built_turnout_{}_minimum_radius_mm".format(side)]
            wanted = expected["turnout_{}_mapped_minimum_radius_mm".format(side)]
            if abs(float(actual) - float(wanted)) > tolerance:
                raise RuntimeError("The accepted GUI Host {} radius differs from the oracle".format(side.upper()))
            if abs(float(actual) - float(preflight["turnout_{}_minimum_radius_mm".format(side)])) > tolerance:
                raise RuntimeError("The accepted GUI Host {} exact build differs from preflight".format(side.upper()))
        for actual_key, wanted_key in (
            ("built_connector_minimum_radius_mm", "connector_minimum_radius_mm"),
            ("built_complete_minimum_radius_mm", "complete_minimum_radius_mm"),
        ):
            if abs(float(positive[actual_key]) - float(expected[wanted_key])) > tolerance:
                raise RuntimeError("The accepted GUI radius differs from the oracle: " + actual_key)
        for built_key, preflight_key in (
            ("built_connector_minimum_radius_mm", "connector_minimum_radius_mm"),
            ("built_complete_minimum_radius_mm", "complete_minimum_radius_mm"),
        ):
            if abs(float(positive[built_key]) - float(preflight[preflight_key])) > tolerance:
                raise RuntimeError("The accepted GUI exact build differs from preflight: " + built_key)
        visuals = [
            proof["negative"]["visual"],
            proof["positive"]["preview_visual"],
            proof["positive"]["created_visual"],
            proof["edit_negative"]["visual"],
        ]
        state["visual_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in visuals
        }
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
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != fixture_hash
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError("The crossover proof changed its source or fixture")
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault("error", "{}: {}".format(type(cleanup_failure).__name__, cleanup_failure))
        state["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("Phase 8 crossover GUI evidence: {}".format(run_dir), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
