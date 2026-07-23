"""Narrow migration façade for Track Template.

Phase 3 exposed the mechanically extracted transition calculations and proved
them through a temporary B15 comparison route. Phase 4 retains only the
modular façade and adds bounded canonical transition-state and neutral
chair-package contracts.
"""

from tracktemplate import DEVELOPMENT_CHECKPOINT
from tracktemplate.application.chair_definition import (
    CHAIR_DEFINITION_FRAME_ID,
    CHAIR_DEFINITION_LENGTH_UNIT,
    CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED,
    CHAIR_DEFINITION_SCHEMA_VERSION,
    ChairDefinitionError,
    ChairDefinitionPackage,
    chair_definition_manifest_signature,
    chair_definition_package_from_json,
    chair_definition_package_status,
    chair_definition_package_to_json,
    verify_chair_definition_manifest,
)
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
    "CHAIR_DEFINITION_SCHEMA_VERSION",
    "CHAIR_DEFINITION_FRAME_ID",
    "CHAIR_DEFINITION_LENGTH_UNIT",
    "CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED",
    "ChairDefinitionError",
    "ChairDefinitionPackage",
    "chair_definition_manifest_signature",
    "chair_definition_package_from_json",
    "chair_definition_package_status",
    "chair_definition_package_to_json",
    "verify_chair_definition_manifest",
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
