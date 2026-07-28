"""Internal application command for the bounded transition editing fixture."""

from dataclasses import dataclass

from tracktemplate.application.transition_state import (
    TransitionState,
    analyse_transition_state,
    replace_transition_intent,
)
from tracktemplate.domain.transition import TransitionIntent


__all__ = (
    "TransitionEditResult",
    "edit_transition_intent",
)


@dataclass(frozen=True)
class TransitionEditResult:
    """Outcome of one validated, stable-identity transition intent edit."""

    previous_state: TransitionState
    state: TransitionState
    changed: bool

    def __post_init__(self):
        if not isinstance(self.previous_state, TransitionState):
            raise TypeError("previous_state must be a TransitionState")
        if not isinstance(self.state, TransitionState):
            raise TypeError("state must be a TransitionState")
        if not isinstance(self.changed, bool):
            raise TypeError("changed must be a bool")


def edit_transition_intent(state, intent, edit_port):
    """Validate and apply one complete intent replacement through ``edit_port``."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(intent, TransitionIntent):
        raise TypeError("intent must be a TransitionIntent")
    apply_edit = getattr(edit_port, "apply_transition_edit", None)
    if not callable(apply_edit):
        raise TypeError(
            "edit_port must provide apply_transition_edit(previous, replacement)"
        )

    if intent == state.intent:
        return TransitionEditResult(
            previous_state=state,
            state=state,
            changed=False,
        )

    replacement = analyse_transition_state(
        replace_transition_intent(state, intent)
    )
    apply_edit(state, replacement)
    return TransitionEditResult(
        previous_state=state,
        state=replacement,
        changed=True,
    )
