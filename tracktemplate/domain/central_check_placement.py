"""Place retained central CC components using Templot 556b conventions.

Source-informed adaptation of math_unit.pas:24152-24407,31690-31917
and dxf_unit.pas:8543-8571,11880-11910, under GPL-3.0-or-later.
See NOTICE.md and reference/PROVENANCE.md. This finite private convention
provides no physical-fit, production or rights acceptance.
"""

from dataclasses import dataclass
import math

from tracktemplate.domain.chair_placement import (
    S1Placement,
    _coordinates,
    _finite_number,
)


# Retained CC/context-native-02, source model mm. The four source centres
# keep their original order; each has boss, ferrule, pan and head parts.
_FIXING_CENTRES_MM = ((-2 / 3, 3.5), (2 / 3, 3.5),
                      (-2 / 3, -2.5), (2 / 3, -2.5))


@dataclass(frozen=True)
class CentralCheckPlacement(S1Placement):
    """One body frame and four proper fixing frames, all in model mm.

    The source fixes boss orientation independently of chair rotation.
    Head rotation stays deterministically zero; random export parity is
    not claimed. Each fixing frame applies to four unchanged components.
    """

    fixing_frames: tuple[S1Placement, ...]

    def __post_init__(self):
        super().__post_init__()
        frames = self.fixing_frames
        if (not isinstance(frames, tuple) or len(frames) != 4
                or any(type(frame) is not S1Placement for frame in frames)
                or any((frame.position_id, frame.rail_id, frame.timber_id)
                       != (self.position_id, self.rail_id, self.timber_id)
                       for frame in frames)):
            raise ValueError("Central CC requires four matching fixing frames")
        # Revalidate nested records: frozen dataclasses alone are not an
        # admission boundary. All four parts retain the same owner ID.
        object.__setattr__(self, "fixing_frames", tuple(S1Placement(
            frame.position_id, frame.rail_id, frame.timber_id,
            frame.origin_mm, frame.x_axis, frame.y_axis,
        ) for frame in frames))


def prepare_central_check_placements(values):
    """Freeze complete CC records without losing their four fixing frames.

    The shared single-frame validator cannot reconstruct this richer
    record. Revalidate every nested frame and reject duplicate owners.
    """
    if not isinstance(values, tuple) or not values:
        raise ValueError("Central CC placements must be a nonempty tuple")
    if any(type(value) is not CentralCheckPlacement for value in values):
        raise TypeError("Central CC requires CentralCheckPlacement records")
    result = tuple(CentralCheckPlacement(
        value.position_id, value.rail_id, value.timber_id,
        value.origin_mm, value.x_axis, value.y_axis, value.fixing_frames,
    ) for value in values)
    if len({value.position_id for value in result}) != len(result):
        raise ValueError("Central CC placement identities are duplicated")
    return tuple(sorted(result, key=lambda value: value.position_id))


def place_central_check(
    position_id, rail_id, timber_id, host_point_mm, travel_heading_rad,
    base_z_mm, *, side, source_angle_rad, source_gauge_y_mm,
):
    """Map the frozen RH C10 CC reference through its common host frame.

    Source X is relative to the square timber station; source Y starts at
    the main gauge face. Retained XY is (-source_x, -source_y-0.45).
    Retained Z already starts at the mounting plane. Inputs use model mm
    and radians. The caller qualifies the complete C10 source context.
    No sampled rail tangent, deformation or fit compensation is applied.
    """
    point = _coordinates(host_point_mm, 2, "host_point_mm")
    heading = _finite_number(travel_heading_rad, "travel_heading_rad")
    base_z = _finite_number(base_z_mm, "base_z_mm")
    angle = _finite_number(source_angle_rad, "source_angle_rad")
    gauge_y = _finite_number(source_gauge_y_mm, "source_gauge_y_mm")
    if (side not in ("MS", "TS")
            or (side == "MS" and (angle != 0 or gauge_y != 0))
            or (side == "TS" and (angle != math.atan(0.1) or gauge_y <= 0))):
        raise ValueError("Central CC requires the qualified RH C10 source pose")
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
    shift = -0.5 * sine
    anchor = (shift * cosine, -gauge_y - shift * sine)
    body = (frame(0.0, (0.0, 0.45)) if side == "MS" else
            frame(math.pi - angle,
                  (anchor[0] - 0.45 * sine,
                   anchor[1] - 0.45 * cosine)))
    fixings = []
    for x, y in _FIXING_CENTRES_MM:
        centre = ((x, -y) if side == "MS" else
                  (cosine * x + sine * y + anchor[0],
                   -sine * x + cosine * y + anchor[1]))
        fixings.append(frame(math.pi, (centre[0] - x,
                                      centre[1] - y - 0.45)))
    return CentralCheckPlacement(
        body.position_id, body.rail_id, body.timber_id, body.origin_mm,
        body.x_axis, body.y_axis, tuple(fixings),
    )
