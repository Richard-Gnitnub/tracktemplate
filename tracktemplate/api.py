"""Narrow migration façade for Track Template.

Phase 3 exposes the mechanically extracted transition calculations through
the temporary all-three-name B15 comparison and rollback boundary. Phase 4
adds the bounded canonical transition-state application contract.
"""

from tracktemplate import DEVELOPMENT_CHECKPOINT
from tracktemplate.application.transition_state import (
    TRANSITION_STATE_SCHEMA_VERSION,
    TransitionAnalysis,
    TransitionState,
    TransitionStateError,
    analyse_transition_state,
    replace_transition_intent,
    transition_analysis_signature,
    transition_analysis_status,
    transition_state_from_json,
    transition_state_to_json,
)
from tracktemplate.domain.alignment import (
    clothoid_entry_displacement,
    solve_transition_length,
    transition_start_signed_offset,
)
from tracktemplate.domain.transition import TransitionIntent


__all__ = (
    "DEVELOPMENT_CHECKPOINT",
    "TRANSITION_STATE_SCHEMA_VERSION",
    "TransitionIntent",
    "TransitionAnalysis",
    "TransitionState",
    "TransitionStateError",
    "analyse_transition_state",
    "replace_transition_intent",
    "transition_analysis_signature",
    "transition_analysis_status",
    "transition_state_from_json",
    "transition_state_to_json",
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)
