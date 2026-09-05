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
MULTI_OBJECT_GUI_PROOF = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_validate_phase5_transition_multi_object_edit.py"
)
LIFECYCLE_GUI_PROOF = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_validate_phase5_transition_editing_lifecycle.py"
)
SENTINEL = "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI="
MULTI_OBJECT_SENTINEL = (
    "TRACKTEMPLATE_PHASE5_MULTI_OBJECT_EDIT_GUI="
)
LIFECYCLE_SENTINEL = (
    "TRACKTEMPLATE_PHASE5_TRANSITION_EDITING_LIFECYCLE_GUI="
)
QUALIFIED_PROFILES_BY_FREECAD_VERSION = {
    "1.1.1": {"linux-x86_64-flatpak-freecad-1.1.1"},
    "1.1.3": {
        "linux-x86_64-flatpak-freecad-1.1.3",
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
    },
}
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))
sys.path.append("/usr/lib/python3/dist-packages")

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


def _sentinel_payload(result, sentinel=SENTINEL):
    output = str(result.get("output") or "")
    matches = [
        line[len(sentinel):]
        for line in output.splitlines()
        if line.startswith(sentinel)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Phase 5 GUI proof emitted {} {!r} sentinels".format(
                len(matches),
                sentinel,
            )
        )
    return json.loads(matches[0])


def _qualified_version(payload):
    return payload.get("freecad_version") in (
        QUALIFIED_PROFILES_BY_FREECAD_VERSION
    )


def _qualified_profile(payload):
    return payload.get("exact_qualified_profile") in (
        QUALIFIED_PROFILES_BY_FREECAD_VERSION.get(
            payload.get("freecad_version"),
            set(),
        )
    )


def _validate_lifecycle_payload(payload):
    expected_ids = [
        "SET-001/curve-track/2/transition/entry",
        "SET-001/curve-track/2/transition/exit",
    ]
    required_true = (
        "active_children_cleared",
        "caches_discarded",
        "canonical_restored_before_save",
        "deactivated",
        "deactivated_then_closed",
        "display_mode_property_unchanged",
        "duplicate_active_blocked",
        "duplicate_invocation_blocked",
        "editor_visible",
        "explicit_activation",
        "proxies_restored",
        "reopened",
        "reopened_deactivated",
        "reopened_new_scene_nodes",
        "residual_not_accumulated",
        "same_document_reactivation_blocked",
        "save_auto_deactivated",
        "schema_unchanged",
        "selection_cleared",
        "sibling_selection_preserved",
        "stored_state_unchanged_after_deactivation",
        "switch_selection_restored",
        "undo_redo_preserved",
    )
    scene_image = pathlib.Path(str(payload.get("scene_image", "")))
    editor_image = pathlib.Path(str(payload.get("editor_image", "")))
    if (
        not _qualified_profile(payload)
        or payload.get("attachment_count") != 2
        or payload.get("composition_boundary")
        != "tracktemplate.transition-editing-lifecycle.development.v1"
        or payload.get("transition_ids") != expected_ids
        or payload.get("residual_empty_child_count") != 2
        or payload.get("reopened_attachment_count") != 2
        or payload.get("reopened_editor_length") != "420.000"
        or payload.get("reopened_editor_selected_transition")
        != expected_ids[1]
        or payload.get("part_shape_created") is not False
        or payload.get("remaining_documents") != []
        or any(payload.get(name) is not True for name in required_true)
        or not scene_image.is_file()
        or not editor_image.is_file()
    ):
        raise RuntimeError(
            "Phase 5 transition-editing lifecycle proof returned an "
            "invalid result"
        )


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
            not _qualified_version(payload)
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
            or payload.get("save_route_exercised") is not True
            or payload.get("reopened_attachment_boundary")
            != (
                "tracktemplate.transition-coin-document-attachment."
                "fixture.v1"
            )
            or payload.get("reopened_attachment_count") != 1
            or payload.get("reopened_attachment_disposed") is not True
            or payload.get("reopened_attachment_explicit_post_open")
            is not True
            or payload.get("reopened_attachment_failure_recovered")
            is not True
            or payload.get("reopened_attachment_history_delta") != 0
            or payload.get("reopened_attachment_order") != [
                "transition:phase5:viewprovider-gui"
            ]
            or payload.get("reopened_attachment_refresh_reused")
            is not True
            or payload.get("reopened_object_count") != 1
            or payload.get("reopened_object_identity_preserved") is not True
            or payload.get("reopened_canonical_state_equal") is not True
            or payload.get("reopened_schema_unchanged") is not True
            or payload.get("reopened_derived_state_persisted") is not False
            or payload.get("reopened_cache_started_missing") is not True
            or payload.get("reopened_cache_rebuilt") is not True
            or payload.get("reopened_cache_is_new") is not True
            or payload.get("reopened_preview_equivalent") is not True
            or payload.get("reopened_empty_switch_child_retained")
            is not True
            or payload.get("reopened_stored_state_unchanged") is not True
            or payload.get("reopened_viewprovider_rebuilt") is not True
            or payload.get("reopened_viewprovider_is_new") is not True
            or payload.get("reopened_visible_red_pixels", 0) < 100
        ):
            raise RuntimeError(
                "Phase 5 GUI proof returned an invalid result"
            )
        multi_object_result = execute_file(
            client,
            MULTI_OBJECT_GUI_PROOF,
        )
        multi_object_payload = _sentinel_payload(
            multi_object_result,
            MULTI_OBJECT_SENTINEL,
        )
        reopened_attachment = multi_object_payload.get(
            "reopened_attachment",
            {},
        )
        editor_selected_image = pathlib.Path(str(
            multi_object_payload.get("editor_selected_image", "")
        ))
        editor_edited_image = pathlib.Path(str(
            multi_object_payload.get("editor_edited_image", "")
        ))
        representative_order = [
            "SET-001/curve-track/2/transition/entry",
            "SET-001/curve-track/2/transition/exit",
        ]
        if (
            not _qualified_version(multi_object_payload)
            or multi_object_payload.get("workload_id")
            != (
                "phase5-qualified-plain-line-one-secondary-track-"
                "entry-exit-v1"
            )
            or multi_object_payload.get("family_id")
            != "plain-line-spacing-matched-transition-intent"
            or multi_object_payload.get("document_object_count") != 2
            or multi_object_payload.get("logical_layer_count") != 2
            or multi_object_payload.get(
                "active_coin_scene_node_count"
            ) != 14
            or multi_object_payload.get("part_shape_created") is not False
            or multi_object_payload.get("selection_input")
            != "qt-mouse-click"
            or multi_object_payload.get("pick_callback_count", 0) < 1
            or multi_object_payload.get("selected_end") != "Exit"
            or multi_object_payload.get("selected_transition_id")
            != "SET-001/curve-track/2/transition/exit"
            or multi_object_payload.get(
                "selection_event",
                {},
            ).get("subelement") != "TransitionPreviewCentreline"
            or multi_object_payload.get(
                "pointer_target",
                {},
            ).get("class_name") != "QOpenGLWidget"
            or multi_object_payload.get("mapping_preserved") is not True
            or multi_object_payload.get("edit_command_route")
            != "internal-application-command"
            or multi_object_payload.get("editor_control")
            != "transition-length-mm"
            or multi_object_payload.get("editor_edited_state_visible")
            is not True
            or multi_object_payload.get(
                "editor_failure_diagnostic_visible"
            ) is not True
            or multi_object_payload.get("editor_initial_length_text")
            != "420.000"
            or multi_object_payload.get("editor_input")
            != "qt-keyboard-and-mouse"
            or multi_object_payload.get("editor_no_selection_rejected")
            is not True
            or multi_object_payload.get("editor_noop_history_delta") != 0
            or multi_object_payload.get("editor_parent")
            != "FreeCAD-main-window"
            or multi_object_payload.get("editor_route")
            != (
                "user-interface-controller-to-internal-application-command"
            )
            or multi_object_payload.get("editor_selected_state_visible")
            is not True
            or editor_selected_image == editor_edited_image
            or not editor_selected_image.is_file()
            or not editor_edited_image.is_file()
            or multi_object_payload.get("edit_undo_units") != 1
            or multi_object_payload.get("undo_restored_initial") is not True
            or multi_object_payload.get("redo_restored_edit") is not True
            or multi_object_payload.get(
                "sibling_state_preserved"
            ) is not True
            or multi_object_payload.get(
                "sibling_state_stages"
            ) != [
                "initial",
                "after_edit",
                "after_undo",
                "after_redo",
                "after_failed_edit",
            ]
            or multi_object_payload.get(
                "transactional_failure_recovered"
            ) is not True
            or multi_object_payload.get(
                "failure_history_preserved"
            ) is not True
            or reopened_attachment.get(
                "active_coin_scene_node_count"
            ) != 14
            or reopened_attachment.get("attachment_boundary")
            != (
                "tracktemplate.transition-coin-document-attachment."
                "fixture.v1"
            )
            or reopened_attachment.get("attachment_count") != 2
            or reopened_attachment.get("attachment_order")
            != representative_order
            or reopened_attachment.get("cache_is_new_count") != 2
            or reopened_attachment.get("derived_state_persisted")
            is not False
            or reopened_attachment.get("disposed") is not True
            or reopened_attachment.get(
                "dispose_returned_transition_ids"
            )
            != representative_order
            or reopened_attachment.get("document_object_count") != 2
            or reopened_attachment.get(
                "empty_switch_children_retained"
            ) != 2
            or reopened_attachment.get("explicit_post_open")
            is not True
            or reopened_attachment.get("history_delta") != 0
            or reopened_attachment.get("independent_refresh")
            is not True
            or reopened_attachment.get("logical_layer_count") != 2
            or reopened_attachment.get("part_shape_created")
            is not False
            or reopened_attachment.get("preview_equivalent_count") != 2
            or reopened_attachment.get("save_route_exercised")
            is not True
            or reopened_attachment.get("schema_unchanged") is not True
            or reopened_attachment.get(
                "selection_mappings_preserved"
            ) is not True
            or reopened_attachment.get(
                "sibling_cache_request_trap"
            ) != "remained-missing"
            or reopened_attachment.get("stored_state_unchanged")
            is not True
            or reopened_attachment.get("all_caches_discarded")
            is not True
            or reopened_attachment.get(
                "all_selection_roots_cleared"
            ) is not True
            or reopened_attachment.get("all_host_proxies_restored")
            is not True
            or reopened_attachment.get("visible_red_pixels", 0) < 100
            or multi_object_payload.get(
                "cache_invalidation",
                {},
            ).get("selected_deltas") != {
                "regenerations": 5,
                "requests": 5,
                "reuses": 0,
            }
            or multi_object_payload.get(
                "cache_invalidation",
                {},
            ).get("sibling_deltas") != {
                "regenerations": 0,
                "requests": 0,
                "reuses": 0,
            }
            or multi_object_payload.get("cleanup") != {
                "discarded_cache_count": 2,
                "disposed_proxy_count": 2,
                "object_count_before_close": 2,
                "remaining_documents": [],
            }
            or not multi_object_payload.get("rationale")
            or not multi_object_payload.get("representative_scope")
        ):
            raise RuntimeError(
                "Phase 5 multi-object GUI proof returned an invalid result"
            )
        lifecycle_result = execute_file(
            client,
            LIFECYCLE_GUI_PROOF,
        )
        lifecycle_payload = _sentinel_payload(
            lifecycle_result,
            LIFECYCLE_SENTINEL,
        )
        _validate_lifecycle_payload(lifecycle_payload)
        print(
            SENTINEL
            + json.dumps(
                {
                    "gui_ready": ready,
                    "representative_multi_object_result": (
                        multi_object_payload
                    ),
                    "result": payload,
                    "transition_editing_lifecycle_result": (
                        lifecycle_payload
                    ),
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
