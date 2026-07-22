"""Narrow migration façade for Track Template.

Phase 3 exposes the mechanically extracted transition calculations through
the temporary all-three-name B15 comparison and rollback boundary.
"""

from tracktemplate import DEVELOPMENT_CHECKPOINT
from tracktemplate.domain.alignment import (
    clothoid_entry_displacement,
    solve_transition_length,
    transition_start_signed_offset,
)


__all__ = (
    "DEVELOPMENT_CHECKPOINT",
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)
