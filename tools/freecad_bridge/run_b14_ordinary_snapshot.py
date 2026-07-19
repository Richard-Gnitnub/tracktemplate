#!/usr/bin/env python3
"""Capture a read-only Phase 1 oracle from one or more B14 base fixtures."""

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
    raise RuntimeError('Could not close ordinary-track documents: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        action="append",
        type=pathlib.Path,
        help="B14 default-base FCStd; repeat to prove semantic equivalence",
    )
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--load-timeout", type=float, default=300.0)
    args = parser.parse_args()

    supplied_bases = args.base or [
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "fixtures"
        / "b14-default-base.FCStd"
    ]
    base_paths = [path.resolve() for path in supplied_bases]
    missing = [str(path) for path in base_paths if not path.is_file()]
    if missing:
        raise SystemExit("B14 ordinary-track fixture not found: {}".format(", ".join(missing)))

    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "ordinary-runs"
        / run_stamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
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
        "recipe_id": "phase1-b14-ordinary-track-document-oracle-v1",
        "mode": "read-only copied fixture snapshot; no document save",
        "macro": "AdvancedTurnout.FCMacro",
        "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "fixtures": [],
    }
    try:
        state["session_before"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The ordinary-track oracle requires an empty isolated session")

        load_job = submit_and_wait(
            client,
            (
                PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b14.py"
            ).read_text(encoding="utf-8"),
            "load B14",
            args.load_timeout,
        )
        state["macro_load"] = parse_json_output(load_job)

        for index, base_path in enumerate(base_paths, start=1):
            copied_path = run_dir / "base-{:02d}.FCStd".format(index)
            shutil.copy2(base_path, copied_path)
            opened = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('Ordinary-track fixture capture requires no open document')
document = App.openDocument({document_path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(document_path=str(copied_path))))
            snapshot = parse_json_output(execute_file(
                client,
                PROJECT_ROOT
                / "tools"
                / "freecad_bridge"
                / "probes"
                / "snapshot_b14_ordinary_track.py",
            ))
            closed = _close_all_documents(client)
            state["fixtures"].append({
                "source": str(base_path),
                "source_bytes": base_path.stat().st_size,
                "source_sha256": sha256(base_path),
                "copied_document": str(copied_path),
                "opened": opened,
                "snapshot": snapshot,
                "closed": closed,
            })

        semantic_hashes = sorted({
            item["snapshot"]["semantic_sha256"] for item in state["fixtures"]
        })
        if len(semantic_hashes) != 1:
            raise RuntimeError(
                "Supplied B14 fixtures are not ordinary-track semantically equivalent: {}".format(
                    semantic_hashes
                )
            )
        state["semantic_sha256"] = semantic_hashes[0]
        state["binary_hashes_are_distinct"] = len({
            item["source_sha256"] for item in state["fixtures"]
        }) > 1
        state["session_after"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_after"].get("documents"):
            raise RuntimeError("Ordinary-track capture leaked an open document")
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
        print("Ordinary-track evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
