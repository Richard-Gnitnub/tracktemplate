#!/usr/bin/env python3
"""Run the Phase 5 ViewProvider proof after the real GUI becomes ready."""

import json
import pathlib
import sys
import time


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
GUI_PROOF = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_validate_phase5_transition_coin_viewprovider.py"
)
SENTINEL = "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI="
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
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
        line[len(SENTINEL):]
        for line in output.splitlines()
        if line.startswith(SENTINEL)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Phase 5 GUI proof emitted {} sentinels".format(len(matches))
        )
    return json.loads(matches[0])


def main():
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
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

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
                "Phase 5 GUI proof requires an empty isolated session"
            )
        result = execute_file(client, GUI_PROOF)
        payload = _sentinel_payload(result)
        if (
            payload.get("freecad_version") != "1.1.1"
            or payload.get("document_object_count") != 1
            or payload.get("document_object_type")
            != "App::FeaturePython"
            or payload.get("part_shape_created") is not False
            or payload.get("display_modes_added") != 1
            or payload.get("root_children_added") != 0
            or payload.get("visible_red_pixels", 0) < 100
            or payload.get("selection_input") != "qt-mouse-click"
            or payload.get("pick_callback_count", 0) < 1
            or payload.get("selection_event", {}).get("subelement")
            != "TransitionPreviewCentreline"
            or payload.get("pointer_target", {}).get("class_name")
            != "QOpenGLWidget"
            or payload.get("edit_command_route")
            != "internal-application-command"
            or payload.get("edit_undo_units") != 1
            or payload.get("edit_noop_history_delta") != 0
            or payload.get("undo_restored_initial") is not True
            or payload.get("redo_restored_edit") is not True
            or payload.get("edit_failure_recovered") is not True
            or payload.get("preview_cache_retained") is not True
            or payload.get("preview_cache_reuse_proved") is not True
            or payload.get("preview_cache_reuse_count", 0) < 1
            or payload.get("preview_cache_failure_recovered") is not True
            or payload.get("preview_cache_discarded") is not True
            or payload.get("change_back_undo_units") != 1
            or payload.get("change_back_restored_initial") is not True
            or payload.get("change_back_undo_restored_edit") is not True
            or payload.get("change_back_redo_restored_initial") is not True
            or payload.get("persisted_schema_changed") is not False
            or payload.get("save_route_exercised") is not False
        ):
            raise RuntimeError(
                "Phase 5 GUI proof returned an invalid result"
            )
        print(
            SENTINEL
            + json.dumps(
                {
                    "gui_ready": ready,
                    "result": payload,
                },
                sort_keys=True,
            )
        )
    finally:
        cleanup = _close_all_documents(client)
        if cleanup.get("remaining"):
            raise RuntimeError(
                "Phase 5 GUI proof leaked a FreeCAD document"
            )


if __name__ == "__main__":
    main()
