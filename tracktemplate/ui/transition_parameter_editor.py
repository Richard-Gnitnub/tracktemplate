"""Transient dialog for editing one selected transition length."""

from dataclasses import dataclass

from tracktemplate.application.transition_edit import (
    edit_transition_length_mm,
)
from tracktemplate.application.transition_state import (
    TransitionState,
    transition_analysis_status,
)


__all__ = (
    "SelectedTransition",
    "TransitionParameterEditorController",
    "TransitionParameterEditorDialog",
    "TransitionParameterSelectionError",
)


class TransitionParameterSelectionError(ValueError):
    """Report a selection state that cannot authorise an edit."""


@dataclass(frozen=True)
class SelectedTransition:
    """Current canonical state and edit port for one selected transition."""

    state: TransitionState
    edit_port: object

    def __post_init__(self):
        if not isinstance(self.state, TransitionState):
            raise TypeError("state must be a TransitionState")
        if not callable(
            getattr(self.edit_port, "apply_transition_edit", None)
        ):
            raise TypeError(
                "edit_port must provide apply_transition_edit(previous, replacement)"
            )
        if transition_analysis_status(self.state) != "current":
            raise ValueError("state must have a current transition analysis")


class TransitionParameterEditorController:
    """Resolve the current selection and route one fail-closed edit."""

    def __init__(self, selection_reader):
        if not callable(selection_reader):
            raise TypeError("selection_reader must be callable")
        self._selection_reader = selection_reader

    def selected(self):
        """Return exactly one current editable transition selection."""
        selected = self._selection_reader()
        if selected is None:
            raise TransitionParameterSelectionError(
                "Select one transition preview before editing."
            )
        if not isinstance(selected, SelectedTransition):
            raise TypeError(
                "selection_reader must return SelectedTransition or None"
            )
        return selected

    def edit_selected(self, expected_state, transition_length_mm):
        """Edit only if the selected canonical state is still current."""
        if not isinstance(expected_state, TransitionState):
            raise TypeError("expected_state must be a TransitionState")
        selected = self.selected()
        if selected.state != expected_state:
            raise TransitionParameterSelectionError(
                "The selected transition changed; no edit was applied."
            )
        return edit_transition_length_mm(
            selected.state,
            transition_length_mm,
            selected.edit_port,
        )


class TransitionParameterEditorDialog:
    """Simple modeless Qt dialog with visible selection and edit status."""

    def __init__(self, controller, qt_widgets, parent=None):
        if not isinstance(
            controller,
            TransitionParameterEditorController,
        ):
            raise TypeError(
                "controller must be a TransitionParameterEditorController"
            )
        self.controller = controller
        self.selected_transition_id = None
        self._selected_state = None
        self._loaded_length_mm = None
        self._loaded_length_text = ""
        self.last_result = None
        self.last_error = None

        self.dialog = qt_widgets.QDialog(parent)
        self.dialog.setWindowTitle("TrackTemplate transition editor")
        self.dialog.resize(560, 220)
        layout = qt_widgets.QVBoxLayout(self.dialog)

        layout.addWidget(qt_widgets.QLabel("Selected transition"))
        self.selected_identity_label = qt_widgets.QLabel("")
        self.selected_identity_label.setObjectName(
            "TrackTemplateSelectedTransition"
        )
        self.selected_identity_label.setWordWrap(True)
        layout.addWidget(self.selected_identity_label)

        layout.addWidget(qt_widgets.QLabel("Transition length (mm)"))
        self.length_edit = qt_widgets.QLineEdit()
        self.length_edit.setObjectName("TrackTemplateTransitionLength")
        layout.addWidget(self.length_edit)

        button_layout = qt_widgets.QHBoxLayout()
        self.apply_button = qt_widgets.QPushButton("Apply")
        self.apply_button.setObjectName("TrackTemplateApplyTransitionEdit")
        self.close_button = qt_widgets.QPushButton("Close")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.status_label = qt_widgets.QLabel("")
        self.status_label.setObjectName("TrackTemplateTransitionEditStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.apply_button.clicked.connect(self._on_apply)
        self.close_button.clicked.connect(self._on_close)
        self.refresh_selection()

    @staticmethod
    def _format_length(length_mm):
        return "{:.3f}".format(length_mm)

    def refresh_selection(self):
        """Refresh visible state without retaining a host or document object."""
        try:
            selected = self.controller.selected()
        except (TypeError, ValueError, RuntimeError) as error:
            self._show_selection_error(error)
            return False

        self.selected_transition_id = selected.state.intent.transition_id
        self._selected_state = selected.state
        self._loaded_length_mm = selected.state.analysis.transition_length_mm
        self.selected_identity_label.setText(self.selected_transition_id)
        self._loaded_length_text = self._format_length(
            self._loaded_length_mm
        )
        self.length_edit.setText(self._loaded_length_text)
        self.apply_button.setEnabled(True)
        self.status_label.setText("Ready to edit the selected transition.")
        self.last_error = None
        return True

    def _show_selection_error(self, error):
        self.selected_transition_id = None
        self._selected_state = None
        self._loaded_length_mm = None
        self._loaded_length_text = ""
        self.selected_identity_label.setText("None")
        self.length_edit.clear()
        self.apply_button.setEnabled(False)
        self.status_label.setText("Edit not applied: {}".format(error))
        self.last_result = None
        self.last_error = error

    def _on_apply(self, _checked=False):
        try:
            raw_value = self.length_edit.text().strip()
            if raw_value == self._loaded_length_text:
                value = self._loaded_length_mm
            else:
                value = float(raw_value)
            result = self.controller.edit_selected(
                self._selected_state,
                value,
            )
        except TransitionParameterSelectionError as error:
            self._show_selection_error(error)
            return None
        except (TypeError, ValueError, RuntimeError) as error:
            self.last_result = None
            self.last_error = error
            self.status_label.setText("Edit not applied: {}".format(error))
            return None

        self.last_result = result
        self.last_error = None
        self._selected_state = result.state
        self._loaded_length_mm = result.state.analysis.transition_length_mm
        self._loaded_length_text = self._format_length(
            self._loaded_length_mm
        )
        self.length_edit.setText(self._loaded_length_text)
        if result.changed:
            message = "Edited transition {} to {} mm.".format(
                result.state.intent.transition_id,
                self.length_edit.text(),
            )
        else:
            message = "No transition change was required."
        self.status_label.setText(message)
        return result

    def _on_close(self, _checked=False):
        self.dialog.close()

    def show(self):
        """Show and raise the modeless editor dialog."""
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def close(self):
        """Close the transient dialog."""
        self.dialog.close()
