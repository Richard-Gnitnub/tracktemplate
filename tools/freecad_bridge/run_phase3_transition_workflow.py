#!/usr/bin/env python3
"""Run one routed Phase 3 workflow in a dedicated FreeCAD GUI process."""

import argparse
import datetime
import json
import pathlib
import shutil
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase3-transition-workflow-runs"
)
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)
from tools.freecad_bridge.phase3_transition_workflow_recipe import (  # noqa: E402
    DRIVER_PATHS,
    ROUTES,
    WORKFLOWS,
    workflow_equivalence_contract,
)
from tools.semantic_compare import semantic_digest  # noqa: E402


B15_MACRO = PROJECT_ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Could not close Phase 3 workflow documents: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _run_directory(requested, workflow, route):
    root = RUN_ROOT.resolve()
    if requested is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        run_dir = root / "{}-{}-{}".format(stamp, workflow, route)
    else:
        run_dir = requested.resolve()
        try:
            run_dir.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "Phase 3 run directories must remain under {}".format(root)
            ) from error
    if run_dir.exists():
        raise SystemExit("Phase 3 run directory already exists: {}".format(run_dir))
    run_dir.mkdir(parents=True)
    return run_dir


def _embedded_workflow_source(route, driver_path):
    prefix = (
        "TRACKTEMPLATE_PHASE3_ROUTE = {!r}\n".format(route)
    )
    source_paths = (
        PROJECT_ROOT
        / "tools"
        / "freecad_bridge"
        / "probes"
        / "load_phase3_transition_workflow.py",
        driver_path,
        PROJECT_ROOT
        / "tools"
        / "freecad_bridge"
        / "probes"
        / "finish_phase3_transition_workflow.py",
    )
    return prefix + "\n".join(
        path.read_text(encoding="utf-8") for path in source_paths
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=ROUTES, required=True)
    parser.add_argument("--workflow", choices=WORKFLOWS, required=True)
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
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("B14 plain-line fixture not found: {}".format(base_path))
    source_sha256_before = sha256(base_path)
    run_dir = _run_directory(args.run_dir, args.workflow, args.route)
    document_path = run_dir / "phase3-{}.FCStd".format(args.workflow)
    shutil.copy2(base_path, document_path)
    result_path = run_dir / "run.json"

    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")
    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    driver_path = PROJECT_ROOT / DRIVER_PATHS[args.workflow]
    state = {
        "run_started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recipe_id": "phase3-b16-transition-routed-workflow-v1",
        "workflow": args.workflow,
        "calculation_route": args.route,
        "development_checkpoint": "10.2A8A7B16",
        "b14_macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "b15_macro_sha256": sha256(B15_MACRO),
        "b16_launcher_sha256": sha256(PROJECT_ROOT / "TrackTemplate.FCMacro"),
        "source_fixture": str(base_path),
        "source_fixture_bytes": base_path.stat().st_size,
        "source_fixture_sha256": source_sha256_before,
        "run_document": str(document_path),
        "cache_state": (
            "fresh isolated FreeCAD GUI process; copied fixed fixture; "
            "persistent isolated preferences; OS file cache uncontrolled"
        ),
        "performance_qualification": (
            "Correctness/oracle run with deep validation; timings are raw "
            "observations, not the contracted Phase 3 performance profile"
        ),
    }
    try:
        state["session_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The Phase 3 workflow requires an empty session")

        state["opened"] = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('Phase 3 routed workflow requires no open document')
document = App.openDocument({document_path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(document_path=str(document_path))))

        workflow_job = submit_and_wait(
            client,
            _embedded_workflow_source(args.route, driver_path),
            "Phase 3 {} {} route".format(args.workflow, args.route),
            args.timeout,
        )
        state["transition_workflow"] = parse_json_output(workflow_job)
        state["recipe_orchestrator_elapsed_seconds"] = workflow_job.get(
            "orchestrator_elapsed_seconds"
        )
        routed = state["transition_workflow"]
        if (
            routed.get("development_checkpoint") != "10.2A8A7B16"
            or routed.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.1"
            or (routed.get("routing") or {}).get("route") != args.route
            or routed.get("active_route_after_workflow") != args.route
            or routed.get("workflow_version") != "10.2A8A7B15"
            or routed.get("binding_identity_preserved") is not True
        ):
            raise RuntimeError("The routed B16 workflow evidence drifted")
        workflow_contract = workflow_equivalence_contract(
            args.workflow,
            routed.get("recipe"),
        )
        state["workflow_contract_sha256"] = semantic_digest(workflow_contract)
        state["run_document_sha256"] = sha256(document_path)
        state["session_after_recipe"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        state["source_fixture_sha256_after"] = sha256(base_path)
        if state["source_fixture_sha256_after"] != source_sha256_before:
            raise RuntimeError("The Phase 3 workflow modified its source fixture")
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        try:
            state["cleanup"] = _close_all_documents(client)
        except Exception as cleanup_error:
            state["cleanup_error"] = "{}: {}".format(
                type(cleanup_error).__name__, cleanup_error
            )
        state["run_finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Phase 3 routed workflow evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
