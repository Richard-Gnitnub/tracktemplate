#!/usr/bin/env python3
"""Run the bounded B14 standalone-turnout lifecycle recipe."""

import argparse
import datetime
import json
import pathlib
import shutil
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
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
from tools.freecad_bridge.run_b14_crossover import capture_visual_evidence  # noqa: E402


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Could not close standalone-turnout recipe documents: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=(
            PROJECT_ROOT
            / "benchmark-output"
            / "freecad-bridge"
            / "fixtures"
            / "b14-default-base.FCStd"
        ),
    )
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("B14 plain-line fixture not found: {}".format(base_path))
    source_sha256_before = sha256(base_path)

    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "turnout-runs"
        / run_stamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "b14-standalone-turnout.FCStd"
    shutil.copy2(base_path, document_path)
    result_path = run_dir / "run.json"

    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    state = {
        "run_started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recipe_id": "phase1-b14-standalone-turnout-lifecycle-v1",
        "macro": "AdvancedTurnout.FCMacro",
        "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "source_fixture": str(base_path),
        "source_fixture_bytes": base_path.stat().st_size,
        "source_fixture_sha256": source_sha256_before,
        "run_document": str(document_path),
        "cache_state": (
            "fresh FreeCAD process; copied document; isolated profile; "
            "operating-system file cache uncontrolled"
        ),
    }
    try:
        state["session_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The standalone-turnout recipe requires an empty session")

        load_job = submit_and_wait(
            client,
            (
                PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b14.py"
            ).read_text(encoding="utf-8"),
            "load B14",
            300.0,
        )
        state["macro_load"] = parse_json_output(load_job)
        state["opened"] = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('Standalone-turnout generation requires no open document')
document = App.openDocument({document_path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(document_path=str(document_path))))
        state["base_validation"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "validate_b14_base.py",
        ))
        state["manager_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "show_trackwork_manager.py",
        ))

        recipe_job = submit_and_wait(
            client,
            (
                PROJECT_ROOT
                / "tools"
                / "freecad_bridge"
                / "probes"
                / "b14_turnout_driver.py"
            ).read_text(encoding="utf-8"),
            "B14 standalone turnout lifecycle",
            args.timeout,
        )
        state["recipe"] = parse_json_output(recipe_job)
        state["recipe_orchestrator_elapsed_seconds"] = recipe_job.get(
            "orchestrator_elapsed_seconds"
        )
        state["run_document_sha256"] = sha256(document_path)
        state["manager_after"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "show_trackwork_manager.py",
        ))
        state["visual_evidence"] = capture_visual_evidence(client, run_dir)
        state["session_after_recipe"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        source_sha256_after = sha256(base_path)
        state["source_fixture_sha256_after"] = source_sha256_after
        if source_sha256_after != source_sha256_before:
            raise RuntimeError("The standalone-turnout recipe modified its source fixture")
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
        state["run_finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        copied_logs = []
        for source_name in ("FreeCAD.log", "isolated-launcher.log"):
            source_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / source_name
            if source_path.is_file():
                destination = run_dir / source_name
                shutil.copy2(source_path, destination)
                copied_logs.append(str(destination))
        state["copied_logs"] = copied_logs
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Standalone-turnout evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
