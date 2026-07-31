#!/usr/bin/env python3
"""Validate the internal Phase 5 transition edit-command seam."""

from dataclasses import FrozenInstanceError, replace
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.application import transition_edit as command  # noqa: E402


class _RecordingEditPort:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def apply_transition_edit(self, previous_state, replacement_state):
        self.calls.append((previous_state, replacement_state))
        if self.failure is not None:
            raise self.failure


def _analysed():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:edit-command",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            300.0,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 edit command",
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _edited_intent(state, transition_length_mm=340.0):
    intent = state.intent
    return replace(
        intent,
        target_signed_offset_mm=api.transition_start_signed_offset(
            intent.circle_centre_y_mm,
            intent.radius_mm,
            transition_length_mm,
        ),
    )


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _validate_changed_and_noop_paths():
    initial = _analysed()
    port = _RecordingEditPort()
    result = command.edit_transition_intent(
        initial,
        _edited_intent(initial),
        port,
    )

    assert result.changed is True
    assert result.previous_state is initial
    assert result.state is port.calls[0][1]
    assert port.calls == [(initial, result.state)]
    assert api.transition_analysis_status(result.state) == "current"
    assert result.state.intent.transition_id == initial.intent.transition_id
    assert result.state.analysis.analysis_signature != (
        initial.analysis.analysis_signature
    )
    assert math.isclose(
        result.state.analysis.transition_length_mm,
        340.0,
        rel_tol=0.0,
        abs_tol=1.0e-7,
    )

    try:
        result.changed = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("TransitionEditResult is not immutable")

    noop_port = _RecordingEditPort()
    noop = command.edit_transition_intent(
        initial,
        initial.intent,
        noop_port,
    )
    assert noop.changed is False
    assert noop.previous_state is initial
    assert noop.state is initial
    assert noop_port.calls == []

    label_port = _RecordingEditPort()
    label_result = command.edit_transition_intent(
        initial,
        replace(initial.intent, track_name="Renamed transition"),
        label_port,
    )
    assert label_result.changed is True
    assert label_result.state.analysis is initial.analysis
    assert len(label_port.calls) == 1


def _validate_fail_closed_paths():
    initial = _analysed()
    port = _RecordingEditPort()
    _expect_state_error(
        lambda: command.edit_transition_intent(
            initial,
            replace(
                initial.intent,
                transition_id="transition:phase5:different",
            ),
            port,
        ),
        "stable-identity-change",
    )
    assert port.calls == []

    failure = RuntimeError("injected edit-port failure")
    failing_port = _RecordingEditPort(failure)
    try:
        command.edit_transition_intent(
            initial,
            _edited_intent(initial),
            failing_port,
        )
    except RuntimeError as error:
        assert error is failure
    else:
        raise AssertionError("Expected the edit-port failure")
    assert len(failing_port.calls) == 1
    assert initial == _analysed()

    for state, intent, edit_port in (
        (object(), initial.intent, port),
        (initial, object(), port),
        (initial, initial.intent, object()),
    ):
        try:
            command.edit_transition_intent(state, intent, edit_port)
        except TypeError:
            pass
        else:
            raise AssertionError("Expected an invalid command input to fail")


def _validate_internal_boundary():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules["tracktemplate.application.transition_edit"]
    assert module["layer"] == "application"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "dataclasses",
        "math",
        "tracktemplate.application.transition_state",
        "tracktemplate.domain.alignment",
        "tracktemplate.domain.transition",
    ]

    for relative in ("tracktemplate/api.py", "TrackTemplate.FCMacro"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "edit_transition_intent" not in source
        assert "TransitionEditResult" not in source


def validate():
    _validate_changed_and_noop_paths()
    _validate_fail_closed_paths()
    _validate_internal_boundary()
    print("Phase 5 transition edit-command validation passed")


if __name__ == "__main__":
    validate()
