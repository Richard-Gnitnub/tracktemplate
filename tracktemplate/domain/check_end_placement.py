"""Place retained check-end components in the qualified RH C10 context.

Source-informed adaptation of Templot 556b math_unit.pas:26696-26820,
30140-30369,31622-31824 and dxf_unit.pas:7046-7126,8543-8571,
11880-12078, under GPL-3.0-or-later. See NOTICE.md and
reference/PROVENANCE.md. No geometry or physical-fit policy is created.
"""

from dataclasses import dataclass
import math

from tracktemplate.domain.chair_placement import (
    S1Placement,
    _coordinates,
    _finite_number,
)


# Frozen source fixed-flare mode at 4 mm/ft. These are model mm/radians,
# not independent prototype values or newly accepted tolerances.
_SCALE = 1 / 3
_FLARE = 49 * _SCALE / 64
_OUTLONG = 9.25 * _SCALE


@dataclass(frozen=True)
class CheckEndPlacement(S1Placement):
    """Body, check seat/key and four fixing frames for one retained family."""

    family: str
    check_frame: S1Placement
    fixing_frames: tuple[S1Placement, ...]

    def __post_init__(self):
        super().__post_init__()
        if (self.family not in ("CCL", "CCR")
                or not isinstance(self.fixing_frames, tuple)
                or len(self.fixing_frames) != 4):
            raise ValueError("Check ends require one family and four fixings")
        frames = (self.check_frame, *self.fixing_frames)
        if any(type(frame) is not S1Placement
               or (frame.position_id, frame.rail_id, frame.timber_id)
               != (self.position_id, self.rail_id, self.timber_id)
               for frame in frames):
            raise ValueError("Check-end component frames must share one owner")
        frames = tuple(S1Placement(
            frame.position_id, frame.rail_id, frame.timber_id,
            frame.origin_mm, frame.x_axis, frame.y_axis,
        ) for frame in frames)
        object.__setattr__(self, "check_frame", frames[0])
        object.__setattr__(self, "fixing_frames", frames[1:])


def prepare_check_end_placements(values):
    """Reconstruct all nested frames and reject partial or duplicate owners."""
    if not isinstance(values, tuple) or not values:
        raise ValueError("Check-end placements must be a nonempty tuple")
    if any(type(value) is not CheckEndPlacement for value in values):
        raise TypeError("Check ends require CheckEndPlacement records")
    result = tuple(CheckEndPlacement(
        value.position_id, value.rail_id, value.timber_id,
        value.origin_mm, value.x_axis, value.y_axis,
        value.family, value.check_frame, value.fixing_frames,
    ) for value in values)
    if len({value.position_id for value in result}) != len(result):
        raise ValueError("Check-end placement identities are duplicated")
    return tuple(sorted(result, key=lambda value: value.position_id))


def place_check_end(
    position_id, rail_id, timber_id, host_point_mm, travel_heading_rad,
    base_z_mm, *, side, family, source_angle_rad, source_gauge_y_mm,
):
    """Apply proper component transforms to unchanged CCL/CCR B-reps.

    Inputs use model mm and radians, in the square uncurved timber frame.
    The caller qualifies the source branch at its station and the finite
    RH C10 source/host context. This function composes proper frames for
    positive acute turnout-side angles; it does not admit source contexts.
    Native XY is
    (-source_x, -source_y-0.45); native Z starts at the mounting plane.
    Common host rotation also rotates fixed-zero fixing parts. Complete
    Templot pad fixing-angle or random export parity is not claimed.
    """
    point = _coordinates(host_point_mm, 2, "host_point_mm")
    heading = _finite_number(travel_heading_rad, "travel_heading_rad")
    base_z = _finite_number(base_z_mm, "base_z_mm")
    angle = _finite_number(source_angle_rad, "source_angle_rad")
    gauge_y = _finite_number(source_gauge_y_mm, "source_gauge_y_mm")
    if (family not in ("CCL", "CCR") or side not in ("MS", "TS")
            or (side == "MS" and (angle != 0 or gauge_y != 0))
            or (side == "TS" and (not 0 < angle < math.pi / 2
                                  or gauge_y <= 0))):
        raise ValueError("Check ends require the qualified RH C10 source pose")
    tangent = (math.cos(heading), math.sin(heading))
    normal = (-tangent[1], tangent[0])

    def frame(local_angle, origin):
        cosine, sine = math.cos(local_angle), math.sin(local_angle)
        return S1Placement(
            position_id, rail_id, timber_id,
            (point[0] + origin[0] * tangent[0]
             + (origin[1] + 8.25) * normal[0],
             point[1] + origin[0] * tangent[1]
             + (origin[1] + 8.25) * normal[1], base_z),
            (cosine * tangent[0] + sine * normal[0],
             cosine * tangent[1] + sine * normal[1]),
            (-sine * tangent[0] + cosine * normal[0],
             -sine * tangent[1] + cosine * normal[1]),
        )

    cosine, sine = math.cos(angle), math.sin(angle)
    flare_angle = math.atan(1 / 18)
    inlong = _OUTLONG + 1 + _FLARE + 4 * _SCALE * math.sin(flare_angle)
    fixing_centres = (
        (-2 * _SCALE, inlong - 1.75 * _SCALE),
        (2 * _SCALE, inlong - 1.75 * _SCALE),
        (-2 * _SCALE, -_OUTLONG + 1.75 * _SCALE),
        (2 * _SCALE, -_OUTLONG + 1.75 * _SCALE),
    )
    shift = (_OUTLONG - inlong) / 2 * sine
    anchor = (shift * cosine, -gauge_y - shift * sine)
    body_angle = 0.0 if side == "MS" else math.pi - angle
    origin = ((0.0, 0.45) if side == "MS" else
              (anchor[0] - 0.45 * sine, anchor[1] - 0.45 * cosine))
    body = frame(body_angle, origin)
    check = body
    if side == "TS":
        # The retained MS recipe shifts each check seat/key by half the
        # flare vector. Rail 4 omits that shift; remove it before applying
        # the common source frame. The component rotation is unchanged.
        sign = -1 if family == "CCL" else 1
        dx = -sign * _FLARE * math.cos(flare_angle) / 2
        dy = -_FLARE * math.sin(flare_angle) / 2
        check = frame(body_angle, (origin[0] + dx * cosine + dy * sine,
                                   origin[1] - dx * sine + dy * cosine))
    fixings = []
    for x, y in fixing_centres:
        centre = ((x, -y) if side == "MS" else
                  (cosine * x + sine * y + anchor[0],
                   -sine * x + cosine * y + anchor[1]))
        fixings.append(frame(math.pi, (centre[0] - x,
                                      centre[1] - y - 0.45)))
    return CheckEndPlacement(
        body.position_id, body.rail_id, body.timber_id,
        body.origin_mm, body.x_axis, body.y_axis,
        family, check, tuple(fixings),
    )
