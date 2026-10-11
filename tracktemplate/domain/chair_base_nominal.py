"""Derive a nominal base-plan outline from explicit exact dimensions.

The right-handed geometric frame has its origin at the bounding
rectangle's centre. All points have Z=0. This frame establishes no rail,
seat or mounting datum and no relation to a canonical chair placement.
The gross outline has four lines and four circular quarter arcs. Optional
circular apertures give a separate net plan. Neither calculation supplies
thickness, a source grid, manufacturing allowance or source data.
"""

from dataclasses import dataclass, fields
from fractions import Fraction


@dataclass(frozen=True)
class ChairBaseNominalParameters:
    """Required full-size millimetre lengths, checked before calculation.

    Corner names identify the geometric rectangle's X/Y extremes only.
    No corner is implicitly identified with a railway side or datum.
    """

    x_span_mm: Fraction
    y_span_mm: Fraction
    bottom_left_radius_mm: Fraction
    bottom_right_radius_mm: Fraction
    top_right_radius_mm: Fraction
    top_left_radius_mm: Fraction


@dataclass(frozen=True)
class ChairBaseNominalLine:
    """One directed straight boundary segment in full-size millimetres."""

    segment_id: str
    start_mm: tuple
    end_mm: tuple


@dataclass(frozen=True)
class ChairBaseNominalArc:
    """One counter-clockwise circular quarter arc about the +Z axis.

    Angles are exact turns from +X towards +Y. Each end angle exceeds
    its start angle by one quarter turn. No angular sampling is used.
    """

    segment_id: str
    start_mm: tuple
    end_mm: tuple
    centre_mm: tuple
    radius_mm: Fraction
    start_angle_turns: Fraction
    end_angle_turns: Fraction


@dataclass(frozen=True)
class ChairBaseNominalGeometry:
    """Derived outline and exact coefficients of its analytical metrics.

    Area and perimeter each equal the constant plus pi times its
    coefficient. Bounds are xmin, ymin, zmin, xmax, ymax, zmax in mm.
    Segments start along the bottom and proceed counter-clockwise.
    """

    parameters: ChairBaseNominalParameters
    segments: tuple
    bounds_mm: tuple
    area_constant_mm2: Fraction
    area_pi_coefficient_mm2: Fraction
    perimeter_constant_mm: Fraction
    perimeter_pi_coefficient_mm: Fraction


@dataclass(frozen=True)
class ChairBaseNominalAperture:
    """One identified circular opening in the geometric XY plane, in mm."""

    aperture_id: str
    centre_mm: tuple
    radius_mm: Fraction


@dataclass(frozen=True)
class ChairBaseApertureGeometry:
    """Gross outline and strictly internal, separate circular openings.

    Apertures retain input identity and order. Area excludes the openings;
    perimeter includes their circular boundaries. Both metrics use exact
    constant-plus-pi coefficients, as in the gross outline record.
    """

    outline: ChairBaseNominalGeometry
    apertures: tuple
    area_constant_mm2: Fraction
    area_pi_coefficient_mm2: Fraction
    perimeter_constant_mm: Fraction
    perimeter_pi_coefficient_mm: Fraction


def _validate_parameters(parameters):
    if not isinstance(parameters, ChairBaseNominalParameters):
        raise TypeError("parameters must be ChairBaseNominalParameters")
    for field in fields(parameters):
        value = getattr(parameters, field.name)
        if not isinstance(value, Fraction):
            raise TypeError(field.name + " must be an exact Fraction")
        if value <= 0:
            raise ValueError(field.name + " must be positive")
    pairs = (
        ("bottom", parameters.bottom_left_radius_mm,
         parameters.bottom_right_radius_mm, parameters.x_span_mm),
        ("top", parameters.top_left_radius_mm,
         parameters.top_right_radius_mm, parameters.x_span_mm),
        ("left", parameters.bottom_left_radius_mm,
         parameters.top_left_radius_mm, parameters.y_span_mm),
        ("right", parameters.bottom_right_radius_mm,
         parameters.top_right_radius_mm, parameters.y_span_mm),
    )
    for name, first, second, span in pairs:
        if first + second >= span:
            raise ValueError(name + " straight segment must have length > 0")


def compute_chair_base_nominal_geometry(parameters):
    """Validate inputs and derive an exact, host-independent plan outline.

    Reject non-Fraction, nonpositive or overlapping/degenerate inputs.
    Every call checks the complete parameter record. The result supplies
    no production admission, prototype accuracy or physical-fit claim.
    """
    _validate_parameters(parameters)
    p = parameters
    left, right = -p.x_span_mm / 2, p.x_span_mm / 2
    bottom, top = -p.y_span_mm / 2, p.y_span_mm / 2
    bl = p.bottom_left_radius_mm
    br = p.bottom_right_radius_mm
    tr = p.top_right_radius_mm
    tl = p.top_left_radius_mm
    zero = Fraction(0)

    def point(x, y):
        return x, y, zero

    points = (
        point(left + bl, bottom), point(right - br, bottom),
        point(right, bottom + br), point(right, top - tr),
        point(right - tr, top), point(left + tl, top),
        point(left, top - tl), point(left, bottom + bl),
    )
    corners = (
        ("bottom-right", point(right - br, bottom + br), br,
         Fraction(3, 4), Fraction(1)),
        ("top-right", point(right - tr, top - tr), tr,
         Fraction(0), Fraction(1, 4)),
        ("top-left", point(left + tl, top - tl), tl,
         Fraction(1, 4), Fraction(1, 2)),
        ("bottom-left", point(left + bl, bottom + bl), bl,
         Fraction(1, 2), Fraction(3, 4)),
    )
    segments = []
    for index, (side, corner) in enumerate(zip(
        ("bottom", "right", "top", "left"), corners,
    )):
        start = 2 * index
        segments.append(ChairBaseNominalLine(
            side, points[start], points[start + 1],
        ))
        name, centre, radius, first_angle, last_angle = corner
        segments.append(ChairBaseNominalArc(
            name, points[start + 1], points[(start + 2) % 8],
            centre, radius, first_angle, last_angle,
        ))

    radii = bl, br, tr, tl
    radius_sum = sum(radii)
    radius_squares = sum(radius ** 2 for radius in radii)
    return ChairBaseNominalGeometry(
        p, tuple(segments), (left, bottom, zero, right, top, zero),
        p.x_span_mm * p.y_span_mm - radius_squares,
        radius_squares / 4,
        2 * (p.x_span_mm + p.y_span_mm) - 2 * radius_sum,
        radius_sum / 2,
    )


def _distance_squared(first, second):
    return sum((a - b) ** 2 for a, b in zip(first, second))


def _validate_aperture(aperture):
    if not isinstance(aperture, ChairBaseNominalAperture):
        raise TypeError("aperture must be ChairBaseNominalAperture")
    if not isinstance(aperture.aperture_id, str):
        raise TypeError("aperture_id must be a string")
    if not aperture.aperture_id.strip():
        raise ValueError("aperture_id must not be empty")
    centre = aperture.centre_mm
    if not isinstance(centre, tuple) or len(centre) != 3:
        raise TypeError("centre_mm must be a three-Fraction tuple")
    if not all(isinstance(value, Fraction) for value in centre):
        raise TypeError("centre_mm must contain exact Fractions")
    if centre[2] != 0:
        raise ValueError("centre_mm must have Z=0")
    if not isinstance(aperture.radius_mm, Fraction):
        raise TypeError("radius_mm must be an exact Fraction")
    if aperture.radius_mm <= 0:
        raise ValueError("radius_mm must be positive")


def _clears_segment(aperture, segment):
    centre = aperture.centre_mm
    radius = aperture.radius_mm
    if isinstance(segment, ChairBaseNominalLine):
        direction = tuple(b - a for a, b in zip(
            segment.start_mm, segment.end_mm,
        ))
        offset = tuple(a - b for a, b in zip(centre, segment.start_mm))
        projection = sum(a * b for a, b in zip(offset, direction))
        projection /= sum(value ** 2 for value in direction)
        projection = min(Fraction(1), max(Fraction(0), projection))
        nearest = tuple(a + projection * b for a, b in zip(
            segment.start_mm, direction,
        ))
        return _distance_squared(centre, nearest) > radius ** 2

    offset = tuple(a - b for a, b in zip(centre, segment.centre_mm))
    in_quadrant = all(
        sum(value * (point - origin) for value, point, origin in zip(
            offset, endpoint, segment.centre_mm,
        )) >= 0
        for endpoint in (segment.start_mm, segment.end_mm)
    )
    if in_quadrant:
        # The radial nearest point lies on this quarter arc. The centre
        # must be on its inner side; square only a positive clearance.
        return radius < segment.radius_mm and (
            sum(value ** 2 for value in offset)
            < (segment.radius_mm - radius) ** 2
        )
    return all(
        _distance_squared(centre, endpoint) > radius ** 2
        for endpoint in (segment.start_mm, segment.end_mm)
    )


def compute_chair_base_aperture_geometry(parameters, apertures):
    """Derive a net plan from exact, strictly internal circular apertures.

    Require an immutable tuple of uniquely identified Fraction records.
    Reject contact with the outline or another aperture, and any overlap.
    Empty input preserves gross metrics. No numerical or fit tolerance
    applies: all containment and separation comparisons are exact.
    """
    outline = compute_chair_base_nominal_geometry(parameters)
    if not isinstance(apertures, tuple):
        raise TypeError("apertures must be an immutable tuple")
    seen = set()
    left, bottom, _zmin, right, top, _zmax = outline.bounds_mm
    for index, aperture in enumerate(apertures):
        _validate_aperture(aperture)
        if aperture.aperture_id in seen:
            raise ValueError("aperture_id must be unique")
        seen.add(aperture.aperture_id)
        x, y, _z = aperture.centre_mm
        if not (left < x < right and bottom < y < top) or not all(
            _clears_segment(aperture, segment)
            for segment in outline.segments
        ):
            raise ValueError(
                aperture.aperture_id + " must lie strictly inside outline"
            )
        for preceding in apertures[:index]:
            if _distance_squared(
                aperture.centre_mm, preceding.centre_mm,
            ) <= (aperture.radius_mm + preceding.radius_mm) ** 2:
                raise ValueError("apertures must not touch or overlap")
    radius_sum = sum(item.radius_mm for item in apertures)
    radius_squares = sum(item.radius_mm ** 2 for item in apertures)
    return ChairBaseApertureGeometry(
        outline, apertures,
        outline.area_constant_mm2,
        outline.area_pi_coefficient_mm2 - radius_squares,
        outline.perimeter_constant_mm,
        outline.perimeter_pi_coefficient_mm + 2 * radius_sum,
    )
