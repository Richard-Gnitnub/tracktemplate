#!/usr/bin/env python3
"""Prove the selected B16 turnout toe range in real inherited GUI controls."""

import argparse
import ast
import datetime
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".devtools" / "freecad-cli" / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


DEFAULT_PORT = 19875
B15_PATH = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
CONTRACT_PATH = ROOT / "reference/contracts/phase1-transition-pilot.json"
LOADER_PATH = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = ROOT / "benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs"
SOURCE_PATHS = (
    ROOT / "AdvancedTurnout.FCMacro",
    B15_PATH,
    ROOT / "TrackTemplate.FCMacro",
    ROOT / "reference/contracts/phase1-compatibility.json",
    CONTRACT_PATH,
    ROOT / "tools/phase3_transition_pilot.py",
    ROOT / "tools/freecad_bridge/run-isolated",
    ROOT / "tools/freecad_bridge/launch-freecad",
    ROOT / "tools/freecad_bridge/orchestration.py",
    ROOT / "tools/freecad_bridge/turnout_recipe.py",
    LOADER_PATH,
    *sorted((ROOT / "tracktemplate").rglob("*.py")),
    pathlib.Path(__file__).resolve(),
    ROOT / "tools/freecad_bridge/run-phase8-turnout-toe-gui",
)


GUI_PROBE = r'''
import json
import sys

import FreeCAD as App
from PySide6 import QtWidgets

from tools.freecad_bridge.turnout_recipe import select_turnout_host
from tracktemplate.domain import turnout as domain_turnout

module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
selected = domain_turnout.turnout_valid_toe_range
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if module.turnout_valid_toe_range is not selected:
    raise RuntimeError("The B16 turnout toe binding is not the selected domain function")
if (routing.get("route") != "modular" or routing.get("schema_version") != 16
        or len(routing.get("function_names", ())) != 25
        or len(routing.get("caller_names", ())) != 40):
    raise RuntimeError("The inherited B16 public routing envelope changed")

callers = {
    "_build_curve_inheriting_c10_turnout": module._build_curve_inheriting_c10_turnout,
    "_crossover_solve_toe_b": module._crossover_solve_toe_b,
    "solve_rea_c10_crossover_geometry": module.solve_rea_c10_crossover_geometry,
    "CrossoverManagerPanel.update_chainage_range": module.CrossoverManagerPanel.update_chainage_range,
    "TurnoutManagerDialog.update_host_summary": module.TurnoutManagerDialog.update_host_summary,
}
for name, caller in callers.items():
    if (caller.__globals__ is not module.__dict__
            or caller.__globals__["turnout_valid_toe_range"] is not selected
            or "turnout_valid_toe_range" not in caller.__code__.co_names):
        raise RuntimeError("The inherited turnout caller is not routed: " + name)

document = App.ActiveDocument
if document is None or not document.FileName:
    raise RuntimeError("Open the copied saved fixture before the turnout GUI probe")
manager = module.TurnoutManagerDialog(document)
manager.show()
QtWidgets.QApplication.processEvents()
selection = select_turnout_host(
    manager.hosts, module.object_string_property, module._integer_object_property
)
manager.host_combo.setCurrentIndex(selection["index"])
host = manager.hosts[selection["index"]]
panel = manager.crossover_panel
panel.refresh_hosts()
panel_matches = [
    index for index, candidate in enumerate(panel.hosts)
    if candidate.Name == host.Name
]
if len(panel_matches) != 1:
    raise RuntimeError("The crossover panel did not retain the selected host")
panel.host_a_combo.setCurrentIndex(panel_matches[0])

def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The inherited GUI choice is absent: " + value)
    combo.setCurrentIndex(index)

def observed_calls(action):
    calls = []
    active = []
    def profile(frame, event, value):
        if frame.f_code is selected.__code__:
            if event == "call":
                item = {
                    "host_length": frame.f_locals["host_length"],
                    "dimensions": {
                        key: frame.f_locals["dimensions"][key]
                        for key in ("module_start_x", "module_end_x")
                    },
                    "orientation": str(frame.f_locals["orientation"]),
                }
                calls.append(item)
                active.append(item)
            elif event == "return" and active:
                item = active.pop()
                item["returned"] = list(value) if value is not None else None
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        action()
    finally:
        sys.setprofile(previous)
    return calls

def require_call(calls, total, dimensions, orientation, expected):
    matching = [
        call for call in calls
        if call["host_length"] == total
        and call["dimensions"] == {
            key: dimensions[key] for key in ("module_start_x", "module_end_x")
        }
        and call["orientation"] == orientation
        and call.get("returned") == list(expected)
    ]
    if not matching:
        raise RuntimeError("The GUI method did not call and return from the selected domain function")

def require_range(box, expected):
    actual = [float(box.minimum()), float(box.maximum())]
    tolerance = 0.5 * 10.0 ** (-int(box.decimals())) + 1.0e-7
    if any(abs(a - b) > tolerance for a, b in zip(actual, expected)):
        raise RuntimeError("The inherited GUI range differs from the domain range: {} != {}".format(actual, expected))
    return actual

cases = []
try:
    for name, orientation, arrangement in (
        ("facing", module.TURNOUT_ORIENTATION_FACING, module.CROSSOVER_ARRANGEMENT_FACING),
        ("trailing", module.TURNOUT_ORIENTATION_TRAILING, module.CROSSOVER_ARRANGEMENT_TRAILING),
    ):
        choose(manager.orientation_combo, orientation)
        manager_data = module.turnout_host_alignment(host)
        manager_dimensions = module.rea_c10_dimensions(
            manager.gauge_box.value(), manager.flangeway_box.value()
        )
        manager_expected = selected(manager_data["total"], manager_dimensions, orientation)
        if manager_expected[1] < manager_expected[0]:
            raise RuntimeError("The controlled fixture has no valid turnout range")
        manager_calls = observed_calls(manager.update_host_summary)
        require_call(manager_calls, manager_data["total"], manager_dimensions, orientation, manager_expected)
        manager_range = require_range(manager.chainage_box, manager_expected)
        summary = str(manager.host_summary.text())
        if "{:.3f} to {:.3f} mm".format(*manager_expected) not in summary:
            raise RuntimeError("The real turnout manager summary lost the toe range")

        choose(panel.arrangement_combo, arrangement)
        panel_data = module.turnout_host_alignment(host)
        panel_dimensions = module.rea_c10_dimensions(
            panel.gauge_box.value(), panel.flangeway_box.value()
        )
        panel_expected = selected(panel_data["total"], panel_dimensions, orientation)
        if panel_expected[1] < panel_expected[0]:
            raise RuntimeError("The controlled fixture has no valid crossover range")
        diagnostics_before = str(panel.diagnostics.toPlainText())
        panel_calls = observed_calls(panel.update_chainage_range)
        require_call(panel_calls, panel_data["total"], panel_dimensions, orientation, panel_expected)
        panel_range = require_range(panel.chainage_box, panel_expected)
        if str(panel.diagnostics.toPlainText()) != diagnostics_before:
            raise RuntimeError("The real crossover panel reported a new range error")

        cases.append({
            "orientation": name,
            "turnout": {
                "host_length": manager_data["total"],
                "dimensions": {key: manager_dimensions[key] for key in ("module_start_x", "module_end_x")},
                "domain_range": list(manager_expected),
                "gui_range": manager_range,
                "widget_decimals": int(manager.chainage_box.decimals()),
                "selected_function_calls": manager_calls,
                "summary": summary,
            },
            "crossover": {
                "host_length": panel_data["total"],
                "dimensions": {key: panel_dimensions[key] for key in ("module_start_x", "module_end_x")},
                "domain_range": list(panel_expected),
                "gui_range": panel_range,
                "widget_decimals": int(panel.chainage_box.decimals()),
                "selected_function_calls": panel_calls,
            },
        })
finally:
    manager.close()
    QtWidgets.QApplication.processEvents()

print(json.dumps({
    "sentinel": "PHASE8_TURNOUT_TOE_GUI_PASS",
    "development_checkpoint": "10.2A8A7B16",
    "inherited_host_version": str(module.MACRO_VERSION_NUMBER),
    "matched_profile_id": _PHASE3_QUALIFICATION["compatibility_evaluation"]["matched_profile_id"],
    "routing": {
        "route": routing["route"],
        "schema_version": routing["schema_version"],
        "function_names": routing["function_names"],
        "caller_names": routing["caller_names"],
    },
    "selected_binding": "tracktemplate.domain.turnout.turnout_valid_toe_range",
    "caller_names": list(callers),
    "host_identity": selection["identity"],
    "cases": cases,
}, sort_keys=True))
'''


def _source_hashes():
    return {str(path.relative_to(ROOT)): sha256(path) for path in SOURCE_PATHS}


def _frozen_oracle(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TURNOUT_ORIENTATION_TRAILING"
            for target in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in (
            "_turnout_orientation_sign", "turnout_valid_toe_range"
        ):
            selected.append(node)
    if len(selected) != 3:
        raise RuntimeError("The frozen turnout oracle AST does not have three exact definitions")
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    namespace = {}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["turnout_valid_toe_range"]


def _compare_oracles(report, contract):
    if report.get("sentinel") != "PHASE8_TURNOUT_TOE_GUI_PASS":
        raise RuntimeError("The real GUI probe did not return its PASS sentinel")
    if report.get("matched_profile_id") != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2":
        raise RuntimeError("The real GUI probe used a different qualified host profile")
    oracles = {}
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        path = ROOT / source["path"]
        if sha256(path) != source["sha256"]:
            raise RuntimeError("The frozen {} source identity drifted".format(label))
        oracles[label] = _frozen_oracle(path)
    cases = report.get("cases")
    if not isinstance(cases, list) or [item.get("orientation") for item in cases] != ["facing", "trailing"]:
        raise RuntimeError("The real GUI proof did not cover facing and trailing")
    frozen_results = []
    for case in cases:
        for control in ("turnout", "crossover"):
            item = case[control]
            arguments = (
                item["host_length"],
                item["dimensions"],
                "Facing in host travel direction" if case["orientation"] == "facing"
                else "Trailing against host travel direction",
            )
            observed = item["gui_range"]
            for label, oracle in oracles.items():
                expected = list(oracle(*arguments))
                tolerance = 0.5 * 10.0 ** (-int(item["widget_decimals"])) + 1.0e-7
                if (item["domain_range"] != expected
                        or any(abs(a - b) > tolerance for a, b in zip(observed, expected))):
                    raise RuntimeError("{} {} {} GUI/domain range differs from frozen {}".format(case["orientation"], control, observed, label))
                frozen_results.append({
                    "orientation": case["orientation"], "control": control,
                    "oracle": label, "range": expected,
                })
    return frozen_results


def _close_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for name in list(App.listDocuments()):
    App.closeDocument(name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Turnout toe GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=pathlib.Path, default=(
        ROOT / "benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd"
    ))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()
    if args.port != DEFAULT_PORT:
        raise SystemExit("Phase 8 turnout toe GUI proof requires bridge port 19875")
    base = args.base.resolve()
    if not base.is_file():
        raise SystemExit("B14 default-base fixture is absent: {}".format(base))
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not token.is_file():
        raise SystemExit("The isolated FreeCAD bridge token is absent")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    source_hashes = _source_hashes()
    base_hash = sha256(base)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "phase8-turnout-toe.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-turnout-toe-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": base_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": "development-only GUI correctness and frozen B14/B15 parity",
    }
    client = FreeCADClient(
        host="127.0.0.1", port=DEFAULT_PORT, timeout=30.0,
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
    raise RuntimeError('Turnout toe GUI proof requires an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + LOADER_PATH.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 turnout toe real GUI",
            args.timeout,
        )
        state["probe"] = parse_json_output(job)
        state["frozen_oracle_comparison"] = _compare_oracles(state["probe"], contract)
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
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != base_hash
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError("The proof source or fixture changed during the run")
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault("error", "{}: {}".format(type(cleanup_failure).__name__, cleanup_failure))
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
                    state["log_retention_error"] = "{}: {}".format(type(error).__name__, error)
                    state.setdefault("error", state["log_retention_error"])
        state["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("Phase 8 turnout toe GUI evidence: {}".format(run_dir), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print("PHASE8_TURNOUT_TOE_GUI_PASS", flush=True)


if __name__ == "__main__":
    main()
