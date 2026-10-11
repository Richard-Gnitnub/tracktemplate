"""Derive a nominal base-plan outline from explicit exact dimensions.

The right-handed geometric frame has its origin at the bounding
rectangle's centre. All points have Z=0. This frame establishes no rail,
seat or mounting datum and no relation to a canonical chair placement.
The outline has four lines and four circular quarter arcs. It contains
no holes, thickness, source grid, manufacturing allowance or source data.
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
