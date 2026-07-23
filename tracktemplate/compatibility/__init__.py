"""Explicit product compatibility boundaries used during migration."""

from .transition_workflow import (
    TransitionWorkflowError,
    load_modular_transition_workflow_session,
)


__all__ = (
    "TransitionWorkflowError",
    "load_modular_transition_workflow_session",
)
