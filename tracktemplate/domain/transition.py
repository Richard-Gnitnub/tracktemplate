"""Canonical FreeCAD-independent intent for one transition calculation."""

from dataclasses import dataclass
import math


__all__ = ("TransitionIntent",)


def _finite_float(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a finite number".format(name))
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("{} must be a finite number".format(name)) from error
    if not math.isfinite(result):
        raise ValueError("{} must be a finite number".format(name))
    return result


@dataclass(frozen=True)
class TransitionIntent:
    """Durable parametric intent for the bounded transition-length slice.

    Length fields are millimetres in canonical local left-turn model space.
    ``total_angle_rad`` is in radians. Diagnostic labels preserve the
    accepted solver messages but do not identify the railway entity.
    """

    transition_id: str
    circle_centre_y_mm: float
    radius_mm: float
    target_signed_offset_mm: float
    total_angle_rad: float
    track_name: str
    end_name: str

    def __post_init__(self):
        if not isinstance(self.transition_id, str) or not self.transition_id.strip():
            raise ValueError("transition_id must be a non-empty stable string")
        for name in ("track_name", "end_name"):
            if not isinstance(getattr(self, name), str):
                raise ValueError("{} must be text".format(name))
        for name in (
            "circle_centre_y_mm",
            "radius_mm",
            "target_signed_offset_mm",
            "total_angle_rad",
        ):
            object.__setattr__(self, name, _finite_float(name, getattr(self, name)))
