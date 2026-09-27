#!/usr/bin/env python3
"""Run the paired native/modular core-layout export GUI workflow."""

import argparse
import datetime
import json
import pathlib
import shutil
import subprocess
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase7-core-layout-export-workflow-runs"
)
DEFAULT_BRIDGE_PORT = 19875
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)
from tools.freecad_bridge.phase3_transition_workflow_recipe import (  # noqa: E402
    LEGACY_ROUTE,
    MODULAR_ROUTE,
    ROUTES,
)
from tools.semantic_compare import compare_structures, semantic_digest  # noqa: E402
from tracktemplate.compatibility.b15_workflow_host import (  # noqa: E402
    CALLER_ROUTES as LEGACY_CALLER_ROUTES,
    FUNCTION_NAMES as LEGACY_FUNCTION_NAMES,
)
from tracktemplate.compatibility.transition_workflow import (  # noqa: E402
    PRODUCT_CALLER_ROUTES,
    PRODUCT_FUNCTION_NAMES,
)


B15_MACRO = PROJECT_ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
DRIVER_PATH = (
    PROJECT_ROOT
    / "tools"
    / "freecad_bridge"
    / "probes"
    / "b14_ordinary_create_export_driver.py"
)
LOADER_PATH = (
    PROJECT_ROOT
    / "tools"
    / "freecad_bridge"
    / "probes"
    / "load_phase3_transition_workflow.py"
)
FINISHER_PATH = (
    PROJECT_ROOT
    / "tools"
    / "freecad_bridge"
    / "probes"
    / "finish_phase7_core_layout_export_workflow.py"
)
WRAPPER_PATH = (
    PROJECT_ROOT
    / "tools"
    / "freecad_bridge"
    / "run-phase7-core-layout-export-workflow"
)
PRODUCT_SOURCE_PATHS = tuple(
    sorted((PROJECT_ROOT / "tracktemplate").rglob("*.py"))
)
SOURCE_PATHS = (
    PROJECT_ROOT / "AdvancedTurnout.FCMacro",
    B15_MACRO,
    PROJECT_ROOT / "TrackTemplate.FCMacro",
    PROJECT_ROOT / "reference" / "contracts" / "phase1-compatibility.json",
    PROJECT_ROOT / "reference" / "contracts" / "phase1-transition-pilot.json",
    PROJECT_ROOT / "tools" / "phase3_transition_pilot.py",
    PROJECT_ROOT / "tools" / "semantic_compare.py",
    *PRODUCT_SOURCE_PATHS,
    PROJECT_ROOT / "tools" / "freecad_bridge" / "b14_recipe.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "freecad-cli",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "freecad_export_metrics.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "launch-freecad",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "ordinary_track_edit_recipe.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "ordinary_track_export_recipe.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "ordinary_track_recipe.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "orchestration.py",
    PROJECT_ROOT
    / "tools"
    / "freecad_bridge"
    / "phase3_transition_workflow_recipe.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
    PROJECT_ROOT / "tools" / "freecad_bridge" / "run-isolated",
    LOADER_PATH,
    DRIVER_PATH,
    FINISHER_PATH,
    pathlib.Path(__file__).resolve(),
    WRAPPER_PATH,
)
QUALIFIED_PROFILE_IDS = {
    "linux-x86_64-flatpak-freecad-1.1.1",
    "linux-x86_64-flatpak-freecad-1.1.3",
    "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
    "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2",
}
ROUTE_ENVELOPES = {
    LEGACY_ROUTE: {
        "schema_version": 1,
        "function_names": list(LEGACY_FUNCTION_NAMES),
        "caller_names": [item[0] for item in LEGACY_CALLER_ROUTES],
    },
    MODULAR_ROUTE: {
        "schema_version": 16,
        "function_names": list(PRODUCT_FUNCTION_NAMES),
        "caller_names": [item[0] for item in PRODUCT_CALLER_ROUTES],
    },
}


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Could not close core-layout export documents: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _new_run_directory(requested, label):
    root = RUN_ROOT.resolve()
    if requested is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        run_directory = root / "{}-{}".format(stamp, label)
    else:
        run_directory = requested.resolve()
        try:
            run_directory.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "Core-layout export run directories must remain under {}".format(
                    root
                )
            ) from error
    if run_directory.exists():
        raise SystemExit(
            "Core-layout export run directory already exists: {}".format(
                run_directory
            )
        )
    run_directory.mkdir(parents=True)
    return run_directory


def _embedded_workflow_source(route, document_path):
    sources = (
        (
            "TRACKTEMPLATE_PHASE3_ROUTE = {!r}\n"
            "TRACKTEMPLATE_EXPECTED_WORKFLOW_DOCUMENT = {!r}\n"
        ).format(route, str(pathlib.Path(document_path).resolve())),
        LOADER_PATH.read_text(encoding="utf-8"),
        "_PHASE7_EXPORT_BINDING_BEFORE = "
        "_PHASE3_SESSION.module.__dict__['run_production_export']\n",
        DRIVER_PATH.read_text(encoding="utf-8"),
        FINISHER_PATH.read_text(encoding="utf-8"),
    )
    return "\n".join(sources)


def _source_hashes():
    return {
        str(path.relative_to(PROJECT_ROOT)): sha256(path)
        for path in SOURCE_PATHS
    }


def _validate_source_hashes(expected, state, route):
    actual = state.get("source_sha256")
    actual_after = state.get("source_sha256_after")
    if (
        not isinstance(actual, dict)
        or actual != expected
        or actual_after != expected
    ):
        raise RuntimeError(
            "The core-layout export {} route source map drifted.".format(
                route
            )
        )


def _validate_cleanup(state, route):
    cleanup_error = str(state.get("cleanup_error") or "")
    if cleanup_error:
        raise RuntimeError(
            "The core-layout export {} route cleanup failed: {}".format(
                route,
                cleanup_error,
            )
        )
    cleanup = state.get("cleanup")
    if (
        not isinstance(cleanup, dict)
        or not isinstance(cleanup.get("closed"), list)
        or cleanup.get("remaining") != []
    ):
        raise RuntimeError(
            "The core-layout export {} route lacks clean shutdown evidence."
            .format(route)
        )


def _validate_routed_report(report, route):
    routing = report.get("routing") or {}
    expected_envelope = ROUTE_ENVELOPES.get(route)
    export_routing = report.get("core_layout_export_routing") or {}
    if (
        expected_envelope is None
        or report.get("development_checkpoint") != "10.2A8A7B16"
        or report.get("matched_profile_id") not in QUALIFIED_PROFILE_IDS
        or routing.get("schema_version")
        != expected_envelope["schema_version"]
        or routing.get("route") != route
        or routing.get("function_names")
        != expected_envelope["function_names"]
        or routing.get("caller_names")
        != expected_envelope["caller_names"]
        or report.get("active_route_after_workflow") != route
        or report.get("workflow_version") != "10.2A8A7B15"
        or report.get("binding_identity_preserved") is not True
        or report.get(
            "core_layout_export_binding_identity_preserved"
        ) is not True
        or export_routing.get("route") != route
        or export_routing.get("host_binding_name")
        != "run_production_export"
        or export_routing.get("mixed_route") is not False
    ):
        raise RuntimeError("The routed core-layout export evidence drifted.")
    if route == MODULAR_ROUTE and (
        export_routing.get("contract_id")
        != "tracktemplate:phase7:core-layout-export:1"
        or export_routing.get("command_name") != "run_core_layout_export"
    ):
        raise RuntimeError("The modular core-layout export contract drifted.")
    if route == LEGACY_ROUTE and (
        export_routing.get("command_name") != "run_production_export"
        or export_routing.get("comparison_route_available") is not True
    ):
        raise RuntimeError("The legacy core-layout export contract drifted.")
    contract = report.get("recipe_contract")
    if not isinstance(contract, dict):
        raise RuntimeError("The core-layout export report has no stable contract.")
    return contract


def _run_route(args, base_path):
    from freecad_cli.client import FreeCADClient

    source_sha256_before = sha256(base_path)
    source_hashes_before = _source_hashes()
    run_directory = _new_run_directory(args.run_dir, args.route)
    document_path = run_directory / "phase7-core-layout-export.FCStd"
    shutil.copy2(base_path, document_path)
    result_path = run_directory / "run.json"

    token_path = (
        PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    )
    if not token_path.is_file():
        raise SystemExit(
            "Bridge token not found; launch the dedicated FreeCAD session first"
        )
    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    state = {
        "run_started_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "recipe_id": "phase7-b16-core-layout-export-workflow-v1",
        "route": args.route,
        "development_checkpoint": "10.2A8A7B16",
        "source_sha256": source_hashes_before,
        "source_fixture": str(base_path),
        "source_fixture_bytes": base_path.stat().st_size,
        "source_fixture_sha256": source_sha256_before,
        "run_document": str(document_path),
        "cache_state": (
            "fresh isolated FreeCAD GUI process; copied fixed fixture; "
            "persistent isolated preferences; OS file cache uncontrolled"
        ),
        "performance_qualification": (
            "Correctness and output-equivalence evidence only; timing and "
            "resource values are descriptive"
        ),
    }
    try:
        state["session_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT
            / "tools"
            / "freecad_bridge"
            / "probes"
            / "session_snapshot.py",
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError(
                "The core-layout export workflow requires an empty session"
            )

        state["opened"] = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('Core-layout export requires no open document')
document = App.openDocument({document_path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(document_path=str(document_path))))

        workflow_job = submit_and_wait(
            client,
            _embedded_workflow_source(args.route, document_path),
            "Phase 7 core-layout export {} route".format(args.route),
            args.timeout,
        )
        report = parse_json_output(workflow_job)
        state["workflow"] = report
        contract = _validate_routed_report(report, args.route)
        state["workflow_contract_sha256"] = semantic_digest(contract)
        state["recipe_orchestrator_elapsed_seconds"] = workflow_job.get(
            "orchestrator_elapsed_seconds"
        )
        state["run_document_sha256"] = sha256(document_path)
        state["session_after_recipe"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT
            / "tools"
            / "freecad_bridge"
            / "probes"
            / "session_snapshot.py",
        ))
        state["source_fixture_sha256_after"] = sha256(base_path)
        if state["source_fixture_sha256_after"] != source_sha256_before:
            raise RuntimeError(
                "The core-layout export workflow modified its source fixture"
            )
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        primary_failure = sys.exc_info()[0] is not None
        final_failure = None
        try:
            state["cleanup"] = _close_all_documents(client)
        except Exception as cleanup_error:
            state["cleanup_error"] = "{}: {}".format(
                type(cleanup_error).__name__, cleanup_error
            )
        try:
            _validate_cleanup(state, args.route)
        except RuntimeError as error:
            final_failure = error
            state["status"] = "failed"
            if not state.get("error"):
                state["error"] = "{}: {}".format(type(error).__name__, error)
        state["source_sha256_after"] = _source_hashes()
        try:
            _validate_source_hashes(
                source_hashes_before,
                state,
                args.route,
            )
        except RuntimeError as error:
            if final_failure is None:
                final_failure = error
            state["status"] = "failed"
            state["source_map_error"] = "{}: {}".format(
                type(error).__name__,
                error,
            )
            if not state.get("error"):
                state["error"] = state["source_map_error"]
        state["run_finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            "Phase 7 core-layout export route evidence: {}".format(
                run_directory
            ),
            flush=True,
        )
        if final_failure is not None and not primary_failure:
            raise final_failure

    _load_completed_route(
        result_path,
        args.route,
        source_hashes_before,
    )


def _load_completed_route(path, route, expected_sources):
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("status") != "completed" or state.get("route") != route:
        raise RuntimeError(
            "The core-layout export {} route did not complete.".format(route)
        )
    _validate_routed_report(state.get("workflow") or {}, route)
    _validate_cleanup(state, route)
    _validate_source_hashes(expected_sources, state, route)
    return state


def _run_pair(args, base_path):
    source_sha256_before = sha256(base_path)
    source_hashes_before = _source_hashes()
    pair_directory = _new_run_directory(args.run_dir, "pair")
    result_path = pair_directory / "comparison.json"
    state = {
        "schema_version": 1,
        "series_id": "phase7-b16-core-layout-export-workflow-parity-v1",
        "started_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "source_fixture": str(base_path),
        "source_fixture_sha256": source_sha256_before,
        "source_sha256": source_hashes_before,
        "process_isolation": "one fresh isolated FreeCAD GUI process per route",
        "route_order": [LEGACY_ROUTE, MODULAR_ROUTE],
        "routes": {},
    }
    try:
        runs = {}
        for route in ROUTES:
            run_directory = pair_directory / route
            command = [
                str(
                    PROJECT_ROOT
                    / "tools"
                    / "freecad_bridge"
                    / "run-isolated"
                ),
                "/usr/bin/env",
                "TRACKTEMPLATE_BRIDGE_PORT={}".format(args.port),
                "PYTHONPATH={}".format(TOOL_ROOT / "src"),
                "/usr/bin/python3",
                str(pathlib.Path(__file__).resolve()),
                "--route",
                route,
                "--base",
                str(base_path),
                "--run-dir",
                str(run_directory),
                "--port",
                str(args.port),
                "--timeout",
                str(args.timeout),
            ]
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(
                    "The core-layout export {} route exited with status {}."
                    .format(route, completed.returncode)
                )
            runs[route] = _load_completed_route(
                run_directory / "run.json",
                route,
                source_hashes_before,
            )
            if _source_hashes() != source_hashes_before:
                raise RuntimeError(
                    "The core-layout export source map changed after the {} "
                    "route.".format(route)
                )

        comparison = compare_structures(
            runs[LEGACY_ROUTE]["workflow"]["recipe_contract"],
            runs[MODULAR_ROUTE]["workflow"]["recipe_contract"],
        )
        if not comparison["equal"]:
            raise RuntimeError(
                "Core-layout export workflow parity failed at {} path(s)."
                .format(comparison["difference_count"])
            )
        state["comparison"] = comparison
        for route in ROUTES:
            state["routes"][route] = {
                "run_json": str(pair_directory / route / "run.json"),
                "workflow_contract_sha256": runs[route][
                    "workflow_contract_sha256"
                ],
                "core_layout_export_routing": runs[route]["workflow"][
                    "core_layout_export_routing"
                ],
            }
        state["source_fixture_sha256_after"] = sha256(base_path)
        if state["source_fixture_sha256_after"] != source_sha256_before:
            raise RuntimeError(
                "The core-layout export pair modified its source fixture"
            )
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        primary_failure = sys.exc_info()[0] is not None
        source_failure = None
        state["source_sha256_after"] = _source_hashes()
        if state["source_sha256_after"] != source_hashes_before:
            source_failure = RuntimeError(
                "The core-layout export pair source map changed during the run."
            )
            state["status"] = "failed"
            state["source_map_error"] = "{}: {}".format(
                type(source_failure).__name__,
                source_failure,
            )
            if not state.get("error"):
                state["error"] = state["source_map_error"]
        state["finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            "Phase 7 core-layout export workflow pair: {}".format(
                pair_directory
            ),
            flush=True,
        )
        if source_failure is not None and not primary_failure:
            raise source_failure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=(
            PROJECT_ROOT
            / "benchmark-output"
            / "freecad-bridge"
            / "fixtures"
            / "b14-default-base-regenerated.FCStd"
        ),
    )
    parser.add_argument("--run-dir", type=pathlib.Path)
    parser.add_argument("--port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()

    if args.port != DEFAULT_BRIDGE_PORT:
        raise SystemExit(
            "Phase 7 core-layout export requires bridge port {}; "
            "nondefault ports are not isolated.".format(DEFAULT_BRIDGE_PORT)
        )

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit(
            "B14 plain-line fixture not found: {}".format(base_path)
        )
    if args.route:
        _run_route(args, base_path)
    else:
        _run_pair(args, base_path)


if __name__ == "__main__":
    main()
