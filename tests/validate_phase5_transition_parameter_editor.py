#!/usr/bin/env python3
"""Validate the bounded Phase 5 transition-parameter editor contract."""

from dataclasses import FrozenInstanceError
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tools import phase5_transition_representative_workload as workload  # noqa: E402
from tracktemplate.application import transition_edit as command  # noqa: E402
from tracktemplate.ui import transition_parameter_editor as editor  # noqa: E402


class _RecordingEditPort:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def apply_transition_edit(self, previous_state, replacement_state):
        self.calls.append((previous_state, replacement_state))
        if self.failure is not None:
            raise self.failure


def _expect_error(action, error_type):
    try:
        action()
    except error_type as error:
        return error
    raise AssertionError("Expected {}".format(error_type.__name__))


def _validate_length_command():
    initial = workload.initial_states()[1]
    port = _RecordingEditPort()
    result = command.edit_transition_length_mm(
        initial,
        workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
        port,
    )

    assert result.changed is True
    assert result.previous_state is initial
    assert result.state.intent.transition_id == initial.intent.transition_id
    assert len(port.calls) == 1
    assert math.isclose(
        result.state.analysis.transition_length_mm,
        workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
        rel_tol=0.0,
        abs_tol=1.0e-7,
    )

    noop_port = _RecordingEditPort()
    noop = command.edit_transition_length_mm(
        initial,
        initial.analysis.transition_length_mm,
        noop_port,
    )
    assert noop.changed is False
    assert noop.state is initial
    assert noop_port.calls == []
    _expect_error(
        lambda: command.edit_transition_length_mm(
            initial,
            initial.analysis.transition_length_mm,
            object(),
        ),
        TypeError,
    )

    for value in (True, "360", -1.0, float("nan"), float("inf")):
        invalid_port = _RecordingEditPort()
        _expect_error(
            lambda candidate=value, edit_port=invalid_port: (
                command.edit_transition_length_mm(
                    initial,
                    candidate,
                    edit_port,
                )
            ),
            ValueError,
        )
        assert invalid_port.calls == []

    unachievable_port = _RecordingEditPort()
    _expect_error(
        lambda: command.edit_transition_length_mm(
            initial,
            3000.0,
            unachievable_port,
        ),
        ValueError,
    )
    assert unachievable_port.calls == []

    failure = RuntimeError("injected parameter-editor port failure")
    failing_port = _RecordingEditPort(failure)
    observed = _expect_error(
        lambda: command.edit_transition_length_mm(
            initial,
            workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
            failing_port,
        ),
        RuntimeError,
    )
    assert observed is failure
    assert len(failing_port.calls) == 1


def _validate_selection_controller():
    initial = workload.initial_states()[1]
    port = _RecordingEditPort()
    selected = editor.SelectedTransition(initial, port)
    current = [selected]
    controller = editor.TransitionParameterEditorController(
        lambda: current[0]
    )

    assert controller.selected() is selected
    result = controller.edit_selected(
        initial,
        workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
    )
    assert result.changed is True
    assert len(port.calls) == 1

    try:
        selected.state = result.state
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("SelectedTransition is not immutable")

    before_wrong_identity = len(port.calls)
    error = _expect_error(
        lambda: controller.edit_selected(
            workload.initial_states()[0],
            workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
        ),
        editor.TransitionParameterSelectionError,
    )
    assert "changed" in str(error).lower()
    assert len(port.calls) == before_wrong_identity

    current[0] = editor.SelectedTransition(
        workload.state_for_end("Exit", 390.0),
        port,
    )
    error = _expect_error(
        lambda: controller.edit_selected(
            initial,
            workload.EDITED_EXIT_TRANSITION_LENGTH_MM,
        ),
        editor.TransitionParameterSelectionError,
    )
    assert "changed" in str(error).lower()
    assert len(port.calls) == before_wrong_identity

    current[0] = None
    error = _expect_error(
        controller.selected,
        editor.TransitionParameterSelectionError,
    )
    assert "select one" in str(error).lower()
    assert len(port.calls) == before_wrong_identity

    _expect_error(
        lambda: editor.SelectedTransition(initial, object()),
        TypeError,
    )
    _expect_error(
        lambda: editor.TransitionParameterEditorController(object()),
        TypeError,
    )
    invalid_controller = editor.TransitionParameterEditorController(
        lambda: object()
    )
    _expect_error(invalid_controller.selected, TypeError)


def _validate_ui_and_dependency_boundary():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    ui_module = modules[
        "tracktemplate.ui.transition_parameter_editor"
    ]
    assert ui_module["layer"] == "ui"
    assert ui_module["warning_signals"] == []
    assert ui_module["imports"] == [
        "dataclasses",
        "tracktemplate.application.transition_edit",
        "tracktemplate.application.transition_state",
    ]

    source = (
        ROOT
        / "tracktemplate"
        / "ui"
        / "transition_parameter_editor.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import FreeCAD",
        "import FreeCADGui",
        "import PySide",
        "import Part",
        "from pivy",
    ):
        assert forbidden not in source
    for required in (
        "QDialog",
        "QLineEdit",
        "QPushButton",
        "Transition length (mm)",
        "Selected transition",
        "Edit not applied",
    ):
        assert required in source

    public_source = (ROOT / "tracktemplate" / "api.py").read_text(
        encoding="utf-8"
    )
    assert "edit_transition_length_mm" not in public_source
    assert "TransitionParameterEditorDialog" not in public_source
    launcher_source = (ROOT / "TrackTemplate.FCMacro").read_text(
        encoding="utf-8"
    )
    assert "edit_transition_length_mm" not in launcher_source
    assert "TransitionParameterEditorDialog" in launcher_source
    assert launcher_source.count("activate_transition_editing(") == 1

    validation = (ROOT / "reference" / "VALIDATION.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT / "reference" / "current" / "PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert "fail-closed selection controller" in validation
    assert "Real Qt keyboard input" in validation
    assert "## User-facing transition parameter editor tranche" in evidence
    assert "Phase 5 remains 0/4" in evidence
    assert "PR-14 remains Open/Remove with **Partial** control" in evidence


def validate():
    _validate_length_command()
    _validate_selection_controller()
    _validate_ui_and_dependency_boundary()
    print("Phase 5 transition-parameter editor validation passed")


if __name__ == "__main__":
    validate()
