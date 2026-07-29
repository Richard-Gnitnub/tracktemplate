#!/usr/bin/env python3
"""Run one Phase 5 Coin performance sample in an isolated FreeCAD GUI."""

import argparse
import datetime
import json
import pathlib
import sys
import time


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
GUI_PROBE = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_profile_phase5_transition_coin_performance.py"
)
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools import phase5_transition_performance as profile  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
)


def _wait_for_gui(client, timeout_seconds=60.0):
    started = time.monotonic()
    last_state = None
    while time.monotonic() - started < timeout_seconds:
        last_state = parse_json_output(execute(client, """
import json
import FreeCADGui as Gui
try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets
main_window = Gui.getMainWindow()
splash_visible = any(
    isinstance(widget, QtWidgets.QSplashScreen) and widget.isVisible()
    for widget in QtWidgets.QApplication.topLevelWidgets()
)
print(json.dumps({
    'main_window_visible': bool(
        main_window is not None and main_window.isVisible()
    ),
    'splash_visible': splash_visible,
}, sort_keys=True))
"""))
        if (
            last_state.get("main_window_visible") is True
            and last_state.get("splash_visible") is False
        ):
            return last_state
        time.sleep(0.25)
    raise TimeoutError(
        "FreeCAD GUI did not become ready: {!r}".format(last_state)
    )


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
print(json.dumps({
    'closed': closed,
    'remaining': sorted(App.listDocuments()),
}, sort_keys=True))
"""))


def _sentinel_payload(result):
    output = str(result.get("output") or "")
    matches = [
        line[len(profile.SAMPLE_SENTINEL):]
        for line in output.splitlines()
        if line.startswith(profile.SAMPLE_SENTINEL)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Phase 5 performance probe emitted {} sentinels.".format(
                len(matches)
            )
        )
    return json.loads(matches[0])


def _run_directory(requested):
    root = profile.RUN_ROOT.resolve()
    run_dir = requested.resolve()
    try:
        run_dir.relative_to(root)
    except ValueError as error:
        raise SystemExit(
            "Phase 5 sample output must remain under {}.".format(root)
        ) from error
    if run_dir.exists():
        raise SystemExit(
            "Phase 5 sample directory already exists: {}".format(run_dir)
        )
    run_dir.mkdir(parents=True)
    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=pathlib.Path)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    run_dir = _run_directory(args.run_dir)
    result_path = run_dir / "sample.json"
    token_path = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "rpc-token"
    )
    if not token_path.is_file():
        raise SystemExit(
            "Bridge token not found; launch the isolated GUI first"
        )
    client = FreeCADClient(
        host="127.0.0.1",
        port=19875,
        timeout=args.timeout,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    sample = {
        "schema_version": 1,
        "profile_id": profile.SAMPLE_PROFILE_ID,
        "status": "failed",
    }
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    started = time.monotonic()
    try:
        ready = _wait_for_gui(client)
        session = parse_json_output(execute_file(
            client,
            PROJECT_ROOT
            / "tools"
            / "freecad_bridge"
            / "probes"
            / "session_snapshot.py",
        ))
        if session.get("documents"):
            raise RuntimeError(
                "Phase 5 performance sample requires an empty session"
            )
        result = execute_file(client, GUI_PROBE)
        sample = _sentinel_payload(result)
        sample["host"] = {
            "gui_ready": ready,
            "orchestrator_elapsed_seconds": time.monotonic() - started,
            "session_before": session,
            "started_utc": started_utc,
        }
        profile._validate_sample(sample)
    except (Exception, SystemExit) as error:
        sample["status"] = "failed"
        sample["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        cleanup = _close_all_documents(client)
        sample.setdefault("host", {})
        sample["host"]["closed_documents"] = cleanup
        sample["host"]["finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(sample, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            profile.SAMPLE_SENTINEL
            + json.dumps(
                {
                    "path": str(result_path),
                    "status": sample.get("status"),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if cleanup.get("remaining"):
            raise RuntimeError(
                "Phase 5 performance sample leaked a FreeCAD document"
            )


if __name__ == "__main__":
    main()
