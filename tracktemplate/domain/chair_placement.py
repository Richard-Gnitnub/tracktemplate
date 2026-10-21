"""Place model-mm S1 and S1J references in an existing analytical frame.

The chair-local origin is the rail-section centre at the base mounting
plane. Its +X runs along the rail, +Y points from gauge to field, and +Z
points up. Placement applies only a proper planar rotation and translation;
it adds no scale, reflection, embedding allowance or fit compensation.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
import math
from numbers import Real
import sys


# Unit-vector construction and two-product sums incur floating-point
# roundoff. This dimensionless guard allows 32 machine epsilons; it is
# unrelated to railway dimensions, physical fit or OCCT tolerances.
_FRAME_ROUNDOFF = 32 * sys.float_info.epsilon


def _identity(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be a nonempty identity")
    return value


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(name + " must be a finite real number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(name + " must be a finite real number") from error
    if not math.isfinite(result):
        raise ValueError(name + " must be a finite real number")
    return result


def _coordinates(value, count, name):
    if not isinstance(value, (tuple, list)) or len(value) != count:
        raise ValueError(name + " has the wrong coordinate count")
    return tuple(_finite_number(item, name) for item in value)


@dataclass(frozen=True)
class S1Placement:
    """Immutable proper planar placement, with a model-mm origin and +Z up.

    Axes contain dimensionless XY components. Invalid identities, nonfinite
    coordinates, scale, skew and reflected frames raise ValueError.
    """

    position_id: str
    rail_id: str
    timber_id: str
    origin_mm: tuple[float, float, float]
    x_axis: tuple[float, float]
    y_axis: tuple[float, float]

    def __post_init__(self):
        for name in ("position_id", "rail_id", "timber_id"):
            _identity(getattr(self, name), name)
        origin = _coordinates(self.origin_mm, 3, "origin_mm")
        x_axis = _coordinates(self.x_axis, 2, "x_axis")
        y_axis = _coordinates(self.y_axis, 2, "y_axis")
        dot = x_axis[0] * y_axis[0] + x_axis[1] * y_axis[1]
        determinant = x_axis[0] * y_axis[1] - x_axis[1] * y_axis[0]
        if (
            abs(math.hypot(*x_axis) - 1) > _FRAME_ROUNDOFF
            or abs(math.hypot(*y_axis) - 1) > _FRAME_ROUNDOFF
            or abs(dot) > _FRAME_ROUNDOFF
            or abs(determinant - 1) > _FRAME_ROUNDOFF
        ):
            raise ValueError("S1 placement axes must form a proper unit frame")
        object.__setattr__(self, "origin_mm", origin)
        object.__setattr__(self, "x_axis", x_axis)
        object.__setattr__(self, "y_axis", y_axis)

    def transform_point(self, point3):
        """Return one chair-local model-mm point in world model mm.

        Reject invalid input and numerical overflow with ValueError.
        """
        x, y, z = _coordinates(point3, 3, "point3")
        result = (
            self.origin_mm[0] + x * self.x_axis[0] + y * self.y_axis[0],
            self.origin_mm[1] + x * self.x_axis[1] + y * self.y_axis[1],
            self.origin_mm[2] + z,
        )
        if not all(math.isfinite(value) for value in result):
            raise ValueError("S1 transformed point is not finite")
        return result


def _prepare_placements(records, chair_code, placement_type, family):
    """Freeze supported plan instances in stable position-identity order.

    The caller supplies selected records of one family from the analysed plan.
    Its centre_point and base_z already contain the intended model-mm
    translation. Legacy local_y_axis points opposite canonical +X, while
    outward_axis is canonical +Y. No source record is changed.

    Empty input, duplicate identities, missing data, unsupported chair codes
    and invalid coordinates or frames raise ValueError.
    """
    try:
        iterator = iter(records)
    except TypeError as error:
        raise ValueError(f"{family} placement records must be iterable") from error
    result = []
    identities = set()
    for record in iterator:
        if not isinstance(record, Mapping):
            raise ValueError(f"{family} placement record must be a mapping")
        code = record.get("chair_code")
        if (isinstance(code, bool) or not isinstance(code, int)
                or code != chair_code):
            raise ValueError(
                f"{family} placement requires integer chair_code {chair_code}"
            )
        position_id = _identity(
            record.get("chair_position_identity"), "position_id",
        )
        if position_id in identities:
            raise ValueError(f"{family} placement position identity is duplicated")
        centre = _coordinates(record.get("centre_point"), 2, "centre_point")
        local_y = _coordinates(record.get("local_y_axis"), 2, "local_y_axis")
        placement = placement_type(
            position_id=position_id,
            rail_id=record.get("rail_identity"),
            timber_id=record.get("timber_identity"),
            origin_mm=(*centre, record.get("base_z")),
            x_axis=(-local_y[0], -local_y[1]),
            y_axis=record.get("outward_axis"),
        )
        identities.add(position_id)
        result.append(placement)
    if not result:
        raise ValueError(f"{family} placement records must not be empty")
    return tuple(sorted(result, key=lambda item: item.position_id))


@dataclass(frozen=True)
class S1JPlacement(S1Placement):
    """A joint-chair family tag on the same proper model-mm frame."""


def prepare_s1_placements(records):
    """Freeze only integer-code-1 records in stable position order."""
    return _prepare_placements(records, 1, S1Placement, "S1")


def prepare_s1j_placements(records):
    """Freeze only integer-code-7 records in stable position order.

    The frame and model-mm datum retain the same analytical meaning as
    the S1 route. No unresolved position is given a replacement frame.
    """
    return _prepare_placements(records, 7, S1JPlacement, "S1J")


def _cross(first, second):
    return first[0] * second[1] - first[1] * second[0]


def _normal_face_intersection(centre, normal, points, name):
    """Find one exact crossing of a closed-segment face polyline.

    Fractions represent the supplied binary64 coordinates exactly.
    Adjacent segments meeting on the line count as one crossing. Other
    repeated crossings and coincident segments have ambiguous topology.
    """
    if not isinstance(points, (tuple, list)) or len(points) < 2:
        raise ValueError(name + " needs at least two points")
    coordinates = [
        tuple(Fraction(value) for value in _coordinates(point, 2, name))
        for point in points
    ]
    crossing = None
    segments = []
    for index, (first, second) in enumerate(zip(
        coordinates, coordinates[1:],
    )):
        direction = (second[0] - first[0], second[1] - first[1])
        if direction == (0, 0):
            raise ValueError(name + " contains a degenerate segment")
        offset = (first[0] - centre[0], first[1] - centre[1])
        denominator = _cross(normal, direction)
        if denominator == 0:
            if _cross(offset, normal) == 0:
                raise ValueError(name + " contains a coincident segment")
            continue
        fraction = _cross(offset, normal) / denominator
        if not 0 <= fraction <= 1:
            continue
        parameter = _cross(offset, direction) / denominator
        point = (
            centre[0] + parameter * normal[0],
            centre[1] + parameter * normal[1],
        )
        if crossing is not None:
            previous = segments[-1]
            if (
                point != crossing[0]
                or previous["index"] + 1 != index
                or previous["fraction_exact"] != "1"
                or fraction != 0
            ):
                raise ValueError(name + " has multiple intersections")
        crossing = point, parameter
        segments.append({"index": index, "fraction_exact": str(fraction)})
    if crossing is None:
        raise ValueError(name + " has no normal-line intersection")
    point, parameter = crossing
    if parameter == 0:
        raise ValueError(name + " passes through the chair centre")
    return parameter, {
        "point_mm_exact": [str(value) for value in point],
        "normal_parameter_mm_exact": str(parameter),
        "segments": segments,
    }


def recover_reference_frame(
    centre_point, local_rail_tangent, gauge_face_points, outer_face_points,
):
    """Derive a private reference frame from explicit rail-face crossings.

    Inputs are a model-mm XY centre, its existing dimensionless unit rail
    tangent and two named face polylines in model mm. Intersect the normal
    line through that centre with each face. Exactly one crossing on each
    side establishes which side faces the gauge. No nearest-point normal,
    tolerance widening, centre movement or source mutation is used.

    Return proper planar ``x_axis`` and ``y_axis`` tuples and a JSON-safe
    ``witness``. +Y points from gauge to field; +Z points up. The existing
    unit-vector roundoff allowance applies only to the input/output axes.
    Intersection predicates use exact fractions of the supplied floats.
    Rational strings retain exact points, segment fractions and parameters
    along the original tangent-normal vector without decimal rounding.

    Raise ValueError for malformed, nonfinite or nonunit inputs,
    degenerate/coincident segments, absent or ambiguous crossings, a face
    through the centre, or faces that do not straddle the centre.
    """
    centre = _coordinates(centre_point, 2, "centre_point")
    tangent = _coordinates(local_rail_tangent, 2, "local_rail_tangent")
    magnitude = math.hypot(*tangent)
    if abs(magnitude - 1) > _FRAME_ROUNDOFF:
        raise ValueError("Reference recovery requires a unit rail tangent")
    exact_centre = tuple(Fraction(value) for value in centre)
    normal = (-Fraction(tangent[1]), Fraction(tangent[0]))
    gauge, gauge_witness = _normal_face_intersection(
        exact_centre, normal, gauge_face_points, "Gauge face",
    )
    outer, outer_witness = _normal_face_intersection(
        exact_centre, normal, outer_face_points, "Outer face",
    )
    if (gauge > 0) == (outer > 0):
        raise ValueError("Rail faces do not straddle the chair centre")
    sign = 1 if gauge > 0 else -1
    y_axis = (sign * tangent[1] / magnitude,
              -sign * tangent[0] / magnitude)
    x_axis = (y_axis[1], -y_axis[0])
    return {
        "x_axis": x_axis,
        "y_axis": y_axis,
        "witness": {
            "method": "accepted-tangent-normal-intersection-v1",
            "centre_point_mm": list(centre),
            "local_rail_tangent": list(tangent),
            "gauge_face": gauge_witness,
            "outer_face": outer_witness,
        },
    }
