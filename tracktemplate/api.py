"""Narrow migration façade for Track Template.

Phase 2 exposes only the development-checkpoint identity.  The selected
transition calculations are added here only after the Phase 3 parity gate.
"""

from tracktemplate import DEVELOPMENT_CHECKPOINT


__all__ = ("DEVELOPMENT_CHECKPOINT",)
