#!/usr/bin/env python3
"""Run the bounded B14 ordinary-track edit and rollback recipe."""

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


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Could not close ordinary-track edit documents: {}'.format(remaining))
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
        raise SystemExit("B14 ordinary-track fixture not found: {}".format(base_path))
    source_sha256_before = sha256(base_path)

    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "ordinary-edit-runs"
        / run_stamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "b14-ordinary-edit.FCStd"
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
        "recipe_id": "phase1-b14-ordinary-track-edit-rollback-v1",
        "macro": "AdvancedTurnout.FCMacro",
        "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "source_fixture": str(base_path),
        "source_fixture_bytes": base_path.stat().st_size,
        "source_fixture_sha256": source_sha256_before,
        "run_document": str(document_path),
        "cache_state": "fresh FreeCAD process; copied document; OS file cache uncontrolled",
    }
    try:
        state["session_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The ordinary-track edit recipe requires an empty session")

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
    raise RuntimeError('Ordinary-track editing requires no open document')
document = App.openDocument({document_path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(document_path=str(document_path))))

        edit_job = submit_and_wait(
            client,
            (
                PROJECT_ROOT
                / "tools"
                / "freecad_bridge"
                / "probes"
                / "b14_ordinary_edit_driver.py"
            ).read_text(encoding="utf-8"),
            "B14 ordinary-track edit/rollback",
            args.timeout,
        )
        state["recipe"] = parse_json_output(edit_job)
        state["recipe_orchestrator_elapsed_seconds"] = edit_job.get(
            "orchestrator_elapsed_seconds"
        )
        state["run_document_sha256"] = sha256(document_path)
        state["session_after_recipe"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        source_sha256_after = sha256(base_path)
        state["source_fixture_sha256_after"] = source_sha256_after
        if source_sha256_after != source_sha256_before:
            raise RuntimeError("The edit recipe modified its source fixture")
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
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Ordinary-track edit evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
