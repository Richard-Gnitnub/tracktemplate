#!/usr/bin/env python3
"""Validate the representative Phase 5 multi-object GUI proof contract."""

import ast
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase5_transition_representative_workload as workload  # noqa: E402
from tracktemplate.application import transition_state  # noqa: E402
from tracktemplate.domain.alignment import GEOMETRY_TOLERANCE  # noqa: E402


def _call_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        _call_name(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }


def _validate_workload():
    states = workload.initial_states()
    assert workload.OBJECT_COUNT == 2
    assert workload.PREVIEW_SEGMENT_COUNT == 32
    assert len(states) == workload.OBJECT_COUNT
    assert tuple(
        state.intent.transition_id
        for state in states
    ) == (
        "SET-001/curve-track/2/transition/entry",
        "SET-001/curve-track/2/transition/exit",
    )
    assert tuple(
        state.intent.end_name
        for state in states
    ) == ("Entry", "Exit")
    assert all(
        state.intent.track_name == "Track 2"
        for state in states
    )
    assert all(
        transition_state.transition_analysis_status(state) == "current"
        for state in states
    )
    assert states == workload.initial_states()
    assert math.isclose(
        states[0].analysis.transition_length_mm,
        workload.ENTRY_TRANSITION_LENGTH_MM,
        rel_tol=0.0,
        abs_tol=GEOMETRY_TOLERANCE,
    )
    assert math.isclose(
        states[1].analysis.transition_length_mm,
        workload.EXIT_TRANSITION_LENGTH_MM,
        rel_tol=0.0,
        abs_tol=GEOMETRY_TOLERANCE,
    )
    assert workload.edited_exit_intent().transition_id == (
        states[1].intent.transition_id
    )
    assert workload.edited_exit_intent().end_name == "Exit"
    assert workload.failed_exit_intent().transition_id == (
        states[1].intent.transition_id
    )
    assert "smallest complete multi-object workload" in (
        workload.WORKLOAD_RATIONALE
    )
    assert "not a whole-layout capacity" in workload.WORKLOAD_SCOPE_LIMIT

    for end_name, transition_length_mm in (
        ("Unknown", 300.0),
        ("Entry", 0.0),
        ("Entry", float("nan")),
        ("Entry", True),
    ):
        try:
            workload.state_for_end(end_name, transition_length_mm)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Expected representative-workload input rejection"
            )


def _validate_gui_and_runner_contract():
    gui_proof = (
        ROOT
        / "tests"
        / "freecad_gui_validate_phase5_transition_multi_object_edit.py"
    )
    runner = (
        ROOT
        / "tools"
        / "freecad_bridge"
        / "run_phase5_transition_viewprovider.py"
    )
    assert gui_proof.is_file()
    assert runner.is_file()

    gui_calls = _calls(gui_proof)
    assert "store.create_many" in gui_calls
    assert "QtTest.QTest.mouseMove" in gui_calls
    assert "QtTest.QTest.mouseClick" in gui_calls
    assert "QtTest.QTest.keyClick" in gui_calls
    assert "QtTest.QTest.keyClicks" in gui_calls
    assert "editor.TransitionParameterEditorDialog" in gui_calls
    assert "command.edit_transition_intent" not in gui_calls
    assert "document.undo" in gui_calls
    assert "document.redo" in gui_calls
    assert "document.saveAs" in gui_calls
    assert "App.openDocument" in gui_calls
    assert "adapter.read_transition_objects" in gui_calls
    assert (
        "attachment.TransitionCoinDocumentAttachmentFixture"
        in gui_calls
    )
    assert "document_attachment.refresh_transition" in gui_calls
    assert "document_attachment.dispose" in gui_calls
    assert "Gui.Selection.addSelection" not in gui_calls

    gui_text = gui_proof.read_text(encoding="utf-8")
    assert (
        "TRACKTEMPLATE_PHASE5_MULTI_OBJECT_EDIT_GUI="
        in gui_text
    )
    assert "EXPECTED_ACTIVE_NODE_COUNT = 14" in gui_text
    assert "injected representative multi-object refresh failure" in (
        gui_text
    )
    assert "_assert_only_selected_regenerated(" in gui_text
    assert "_assert_record_unchanged(" in gui_text
    assert '"after_undo"' in gui_text
    assert '"after_redo"' in gui_text
    assert '"transactional_failure_recovered": True' in gui_text
    assert '"editor_input": "qt-keyboard-and-mouse"' in gui_text
    assert '"editor_no_selection_rejected": True' in gui_text
    assert '"editor_noop_history_delta": 0' in gui_text
    assert '"editor_selected_state_visible": True' in gui_text
    assert '"editor_edited_state_visible": True' in gui_text
    assert '"editor_failure_diagnostic_visible": True' in gui_text
    assert '"mapping_preserved": True' in gui_text
    assert '"sibling_state_preserved": all(' in gui_text
    assert '"sibling_state_stages": tuple(' in gui_text
    assert (
        '"reopened_attachment": reopened_attachment'
        in gui_text
    )
    assert '"attachment_count": workload.OBJECT_COUNT' in gui_text
    assert '"dispose_returned_transition_ids": dispose_result' in (
        gui_text
    )
    assert '"explicit_post_open": True' in gui_text
    assert '"independent_refresh": True' in gui_text
    assert '"empty_switch_children_retained": (' in gui_text
    assert '"selection_mappings_preserved": True' in gui_text
    assert (
        '"sibling_cache_request_trap": "remained-missing"'
        in gui_text
    )
    assert '"stored_state_unchanged": True' in gui_text
    assert '"all_caches_discarded": True' in gui_text
    assert '"all_selection_roots_cleared": True' in gui_text
    assert '"all_host_proxies_restored": True' in gui_text

    runner_text = runner.read_text(encoding="utf-8")
    assert (
        "freecad_gui_validate_phase5_transition_multi_object_edit.py"
        in runner_text
    )
    assert "MULTI_OBJECT_SENTINEL" in runner_text
    assert '"active_coin_scene_node_count"' in runner_text
    assert '"cache_invalidation"' in runner_text
    assert '"sibling_state_stages"' in runner_text
    assert '"transactional_failure_recovered"' in runner_text
    assert '"reopened_attachment"' in runner_text
    assert '"attachment_order"' in runner_text
    assert '"dispose_returned_transition_ids"' in runner_text
    assert '"empty_switch_children_retained"' in runner_text
    assert '"independent_refresh"' in runner_text
    assert '"selection_mappings_preserved"' in runner_text
    assert '"sibling_cache_request_trap"' in runner_text
    assert '"all_caches_discarded"' in runner_text
    assert '"all_selection_roots_cleared"' in runner_text
    assert '"all_host_proxies_restored"' in runner_text
    assert '"representative_multi_object_result"' in runner_text
    assert '"editor_route"' in runner_text
    assert '"editor_selected_image"' in runner_text
    assert '"editor_edited_image"' in runner_text


def _validate_scope_and_documentation():
    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/presentation/__init__.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "phase5_transition_representative_workload" not in text
        assert "multi_object_edit" not in text

    validation = (ROOT / "reference" / "VALIDATION.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT
        / "reference"
        / "history"
        / "phase-closeouts"
        / "PHASE5_CLOSEOUT.md"
    ).read_text(encoding="utf-8")
    assert (
        "representative Entry/Exit multi-object editing workload"
        in validation
    )
    assert (
        "saved/reopened representative Entry/Exit\n"
        "attachment product boundary"
        in validation
    )
    assert (
        "## Representative multi-object selection and edit tranche"
        in evidence
    )
    assert (
        "## Representative save/reopen attachment tranche"
        in evidence
    )
    assert "No renderer or Phase 5 exit is accepted" in evidence


def validate():
    _validate_workload()
    _validate_gui_and_runner_contract()
    _validate_scope_and_documentation()
    print(
        "Phase 5 representative multi-object edit validation passed"
    )


if __name__ == "__main__":
    validate()
