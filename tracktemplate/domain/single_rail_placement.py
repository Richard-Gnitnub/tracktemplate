"""Place retained S1, S1J and L1 components in the qualified RH C10 frame.

Source-informed adaptation of Templot 556b chairs_unit.pas:920-965,
math_unit.pas:24152-24237,28271-28559,31377-31479,31685-31736 and
dxf_unit.pas:8543-8571,11902-12067, GPL-3.0-or-later. See NOTICE.md
and reference/PROVENANCE.md. Geometry and physical-fit policy stay unchanged.
"""

from dataclasses import dataclass
import math

from tracktemplate.domain.chair_placement import (
    S1Placement,
    _coordinates,
    _finite_number,
)


@dataclass(frozen=True)
class SingleRailPlacement(S1Placement):
    """One fixed body frame and the retained source-indexed fixing frames."""

    family: str
    fixing_frames: tuple[S1Placement, ...]

    def __post_init__(self):
        super().__post_init__()
        if (self.family not in ("S1", "S1J", "L1")
                or not isinstance(self.fixing_frames, tuple)
                or len(self.fixing_frames) != (4 if self.family == "L1" else 3)):
            raise ValueError("Single rails require a family and its fixing count")
        if any(type(frame) is not S1Placement
               or (frame.position_id, frame.rail_id, frame.timber_id)
               != (self.position_id, self.rail_id, self.timber_id)
               for frame in self.fixing_frames):
            raise ValueError("Single-rail component frames must share one owner")
        object.__setattr__(self, "fixing_frames", tuple(S1Placement(
            frame.position_id, frame.rail_id, frame.timber_id,
            frame.origin_mm, frame.x_axis, frame.y_axis,
        ) for frame in self.fixing_frames))


def prepare_single_rail_placements(values):
    """Revalidate nested frames and reject partial or duplicate owners."""
    if not isinstance(values, tuple) or not values:
        raise ValueError("Single-rail placements must be a nonempty tuple")
    if any(type(value) is not SingleRailPlacement for value in values):
        raise TypeError("Single rails require SingleRailPlacement records")
    result = tuple(SingleRailPlacement(
        value.position_id, value.rail_id, value.timber_id,
        value.origin_mm, value.x_axis, value.y_axis,
        value.family, value.fixing_frames,
    ) for value in values)
    if len({value.position_id for value in result}) != len(result):
        raise ValueError("Single-rail placement identities are duplicated")
    return tuple(sorted(result, key=lambda value: value.position_id))


def place_single_rail(
    position_id, rail_id, timber_id, host_point_mm, travel_heading_rad,
    base_z_mm, *, family, source_rail_code, source_angle_rad, source_gauge_y_mm,
):
    """Compose source insertions with a canonical host frame in mm/radians.

    Source gauge Y is measured from the main gauge face before the RH
    reflection. The source angle is evaluated at the nominal timber station.
    Fixed body, jaw, seat and key insertions use that same angle. Source
    midpoint displacement does not change their rail sampling station.
    Retained native XY is (-source_x, -source_y-0.45), mounting Z=0.
    Fixings keep their indices and zero local head angle, as in the retained
    models. Global Templot fixing-angle and random export parity are excluded.
    The caller qualifies the source context; this function admits no hosts.
    """
    point = _coordinates(host_point_mm, 2, "host_point_mm")
    heading = _finite_number(travel_heading_rad, "travel_heading_rad")
    base_z = _finite_number(base_z_mm, "base_z_mm")
    angle = _finite_number(source_angle_rad, "source_angle_rad")
    gauge_y = _finite_number(source_gauge_y_mm, "source_gauge_y_mm")
    if (family not in ("S1", "S1J", "L1")
            or type(source_rail_code) is not int
            or source_rail_code not in (1, 2, 3, 4)
            or (source_rail_code in (1, 3)
                and (angle != 0 or gauge_y != (0 if source_rail_code == 1 else 16.5)))
            or (source_rail_code in (2, 4)
                and (not 0 < angle < math.pi / 2 or gauge_y <= 0))):
        raise ValueError("Single rails require the qualified RH C10 source pose")
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

    # Frozen 4 mm/ft source dimensions, not inferred retained bounding boxes.
    inner, outer = (3.5 / 3, 7 / 3) if family == "L1" else (5.25 / 3, 9.25 / 3)
    half_pitch = 3.75 / 3 if family == "L1" else 2 / 3
    centres = [(-half_pitch, inner - 1.75 / 3),
               (half_pitch, inner - 1.75 / 3)]
    centres.extend((x, -outer + 1.75 / 3) for x in (
        (-half_pitch, half_pitch) if family == "L1" else (0.0,)
    ))
    cosine, sine = math.cos(angle), math.sin(angle)
    delta = (outer - inner) / 2 * sine * {1: 0, 2: -1, 3: 0, 4: 1}[source_rail_code]
    anchor = (delta * cosine, -gauge_y - delta * sine)
    reversed_rail = source_rail_code in (3, 4)
    sign = -1 if reversed_rail else 1
    body = frame(math.pi - angle if reversed_rail else -angle,
                 (anchor[0] + sign * 0.45 * sine,
                  anchor[1] + sign * 0.45 * cosine))
    fixings = []
    for x, y in centres:
        source_y = -y if reversed_rail else y
        target = ((x + delta) * cosine - source_y * sine,
                  -(x + delta) * sine - source_y * cosine - gauge_y)
        fixings.append(frame(math.pi, (target[0] - x, target[1] - y - 0.45)))
    return SingleRailPlacement(
        body.position_id, body.rail_id, body.timber_id,
        body.origin_mm, body.x_axis, body.y_axis, family, tuple(fixings),
    )
