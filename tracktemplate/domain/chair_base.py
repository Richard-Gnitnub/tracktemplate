"""Construct the finite reference-only S1 base and plinth analytically.

Relationships follow Templot5 revision 556b calc_fill_chair_outline and
_3d_chair_outline/_3d_chair_plinth. Dimensions remain definition inputs.
The declared identity placement retains source sampling and mark encoding;
it does not define a general production profile or placement rule.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from collections import Counter
from dataclasses import dataclass, fields
from fractions import Fraction
from math import isqrt


# Source control_room.pas:498-499, integer mark encoding, not physical limits.
_SOURCE_MARK_MIN = -(2 ** 30)
_SOURCE_MARK_MAX = 2 ** 30 - 1
_ROOT_DENOMINATOR = 10 ** 60


@dataclass(frozen=True)
class ChairBaseParameters:
    """Fourteen explicit full-size lengths in mm, as exact Fractions.

    Midpoint offset and mark quantum describe reference encoding, not
    prototype facts, fit clearance or manufacturing compensation.
    Only the unrotated identity source placement and no-slot body apply.
    """

    chair_half_width_mm: Fraction
    chair_inner_length_mm: Fraction
    chair_outer_length_mm: Fraction
    inner_corner_radius_mm: Fraction
    outer_corner_radius_mm: Fraction
    plinth_side_inset_mm: Fraction
    plinth_end_inset_mm: Fraction
    edge_thickness_mm: Fraction
    plinth_thickness_mm: Fraction
    outline_midpoint_offset_mm: Fraction
    source_mark_quantum_mm: Fraction
    rail_head_width_mm: Fraction
    rail_depth_mm: Fraction
    seat_thickness_mm: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            if value <= 0:
                raise ValueError(field.name + " must be positive")
        width = self.chair_half_width_mm
        if max(self.inner_corner_radius_mm, self.outer_corner_radius_mm,
               self.plinth_side_inset_mm) >= width:
            raise ValueError("radii and side inset must be inside half width")
        midpoint = self.outline_midpoint_offset_mm
        if (self.inner_corner_radius_mm + midpoint
                >= self.chair_inner_length_mm
                or self.outer_corner_radius_mm + midpoint
                >= self.chair_outer_length_mm):
            raise ValueError("midpoints must be strictly between the corners")
        if self.plinth_end_inset_mm >= min(
            self.chair_inner_length_mm, self.chair_outer_length_mm
        ):
            raise ValueError("end inset must be inside both source extents")
        if self.plinth_thickness_mm <= self.edge_thickness_mm:
            raise ValueError("plinth top must be above the outline edge")

    def source_to_chair(self, point):
        """Apply the accepted proper transform after source XY encoding."""
        x, y, z = point
        return (-x, -y - self.rail_head_width_mm / 2,
                z + self.rail_depth_mm + self.seat_thickness_mm)


@dataclass(frozen=True)
class ChairBaseGeometry:
    """Derived named boundary; source records are not canonical inputs.

    Rounding margins are dimensionless distances inside source grid cells.
    The sampled, encoded boundary is distinct from ideal circular radii.
    """

    parameters: ChairBaseParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: Fraction
    landmarks: tuple
    source_outline_mm: tuple
    source_plinth_mm: tuple
    rounding_margins: tuple


def _root_interval(value):
    lower = Fraction(isqrt(value * _ROOT_DENOMINATOR ** 2),
                     _ROOT_DENOMINATOR)
    return lower, lower + Fraction(1, _ROOT_DENOMINATOR)


def _affine_interval(offset, coefficient, interval):
    values = tuple(offset + coefficient * point for point in interval)
    return min(values), max(values)


def _sines():
    """Enclose sine at the seven fixed 15-degree source samples exactly."""
    two, three, six = (_root_interval(n) for n in (2, 3, 6))
    return (
        (Fraction(0), Fraction(0)),
        ((six[0] - two[1]) / 4, (six[1] - two[0]) / 4),
        (Fraction(1, 2), Fraction(1, 2)),
        (two[0] / 2, two[1] / 2),
        (three[0] / 2, three[1] / 2),
        ((six[0] + two[0]) / 4, (six[1] + two[1]) / 4),
        (Fraction(1), Fraction(1)),
    )


def _quantize(interval, quantum, name):
    """Refuse clamping and any exact or unresolved half-grid decision."""
    lower, upper = (value / quantum for value in interval)
    if not _SOURCE_MARK_MIN < lower <= upper < _SOURCE_MARK_MAX:
        raise ValueError(name + ": source mark range would require clamping")
    shifted = lower + Fraction(1, 2)
    nearest = shifted.numerator // shifted.denominator
    margin = min(lower - nearest + Fraction(1, 2),
                 nearest + Fraction(1, 2) - upper)
    if margin <= 0:
        raise ValueError(name + ": ambiguous source mark rounding")
    return nearest * quantum, margin


def _source_points(p):
    c = p.chair_half_width_mm
    inner, outer = p.chair_inner_length_mm, p.chair_outer_length_mm
    ri, ro = p.inner_corner_radius_mm, p.outer_corner_radius_mm
    middle = p.outline_midpoint_offset_mm
    sines = _sines()

    def exact(x, y):
        return ((x, x), (y, y))

    def arc(x, y, rx, ry, index_x, index_y):
        return (_affine_interval(x, rx, sines[index_x]),
                _affine_interval(y, ry, sines[index_y]))

    outline = [exact(-c, -outer + ro), exact(-c, -middle),
               exact(-c, middle), exact(-c, inner - ri)]
    outline.extend(arc(-c + ri, inner - ri, -ri, ri, 6 - n, n)
                   for n in range(1, 7))
    outline.extend(arc(c - ri, inner - ri, ri, ri, n, 6 - n)
                   for n in range(7))
    outline.extend((exact(c, middle), exact(c, -middle),
                    exact(c, -outer + ro)))
    outline.extend(arc(c - ro, -outer + ro, ro, -ro, 6 - n, n)
                   for n in range(1, 7))
    outline.extend(arc(-c + ro, -outer + ro, -ro, -ro, n, 6 - n)
                   for n in range(6))
    left, right = -c + p.plinth_side_inset_mm, c - p.plinth_side_inset_mm
    low, high = -outer + p.plinth_end_inset_mm, inner - p.plinth_end_inset_mm
    plinth = [exact(left, low), exact(left, high),
              exact(right, high), exact(right, low)]
    margins = []

    def encode(name, point):
        coordinates = []
        for axis, interval in zip("xy", point):
            value, margin = _quantize(interval, p.source_mark_quantum_mm,
                                      name + "." + axis)
            coordinates.append(value)
            margins.append((name + "." + axis, margin))
        return name, *coordinates

    ring = tuple(encode("p{:02d}".format(i), point)
                 for i, point in enumerate(outline))
    top = tuple(encode(name, point) for name, point in zip("abcd", plinth))
    return ring, top, tuple(margins)


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _normal(points):
    crosses = [_cross(a, b) for a, b in
               zip(points, points[1:] + points[:1])]
    return tuple(sum(item[axis] for item in crosses) for axis in range(3))


def _orient_and_check(vertices, faces):
    if len(set(vertices.values())) != 68:
        raise ValueError("source encoding collapsed distinct body vertices")
    centre = tuple(sum(point[axis] for point in vertices.values()) / 68
                   for axis in range(3))
    result = []
    edges = Counter()
    for name, ids in faces:
        points = [vertices[key] for key in ids]
        normal = _normal(points)
        direction = _dot(normal, _subtract(points[0], centre))
        if direction == 0:
            raise ValueError(name + ": degenerate boundary face")
        if direction < 0:
            ids = tuple(reversed(ids))
            points.reverse()
            normal = tuple(-value for value in normal)
        if any(_dot(normal, _subtract(point, points[0])) != 0
               for point in points):
            raise ValueError(name + ": nonplanar boundary face")
        if any(_dot(normal, _subtract(point, points[0])) > 0
               for point in vertices.values()):
            raise ValueError(name + ": outside the finite convex body")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges[a, b] += 1
        result.append((name, ids))
    if (len(edges) != 256 or any(count != 1 or edges[b, a] != 1
                                 for (a, b), count in edges.items())
            or len(vertices) - len(edges) // 2 + len(result) != 2):
        raise ValueError("boundary must pair 128 edges into one closed shell")
    return tuple(result)


def construct_chair_base(parameters):
    """Construct the complete fixed no-slot reference body, without a host."""
    if not isinstance(parameters, ChairBaseParameters):
        raise TypeError("parameters must be ChairBaseParameters")
    p = parameters
    ring, rectangle, margins = _source_points(p)
    vertices = {}
    source_base_z = -p.rail_depth_mm - p.seat_thickness_mm
    for prefix, level in (("b", Fraction(0)), ("e", p.edge_thickness_mm)):
        for name, x, y in ring:
            vertices[prefix + name[1:]] = p.source_to_chair(
                (x, y, source_base_z + level)
            )
    for name, x, y in rectangle:
        vertices[name] = p.source_to_chair(
            (x, y, source_base_z + p.plinth_thickness_mm)
        )
    faces = []
    for i in range(32):
        j = (i + 1) % 32
        faces.append(("side-{:02d}".format(i),
                      ("b{:02d}".format(i), "b{:02d}".format(j),
                       "e{:02d}".format(j), "e{:02d}".format(i))))
    roof = []
    for start, apex in ((3, "b"), (10, "c"), (19, "d"), (26, "a")):
        for i in range(start, start + 6):
            roof.append(("roof-{:02d}".format(i),
                         ("e{:02d}".format(i),
                          "e{:02d}".format((i + 1) % 32), apex)))
    roof.extend((
        ("roof-near", ("e00", "e01", "e02", "e03", "b", "a")),
        ("roof-inner", ("e09", "e10", "c", "b")),
        ("roof-far", ("e16", "e17", "e18", "e19", "d", "c")),
        ("roof-outer", ("e25", "e26", "a", "d")),
        ("plinth-top", ("a", "b", "c", "d")),
    ))
    faces.extend(roof)
    faces.append(("source-underside", tuple("b{:02d}".format(i)
                                           for i in range(32))))
    faces = _orient_and_check(vertices, faces)

    # Roof projection partitions the source underside; integrate its heights.
    area = Fraction(0)
    volume = Fraction(0)
    for name, ids in roof:
        origin = vertices[ids[0]]
        for i in range(1, len(ids) - 1):
            a, b = vertices[ids[i]], vertices[ids[i + 1]]
            triangle_area = abs(_cross(_subtract(a, origin),
                                       _subtract(b, origin))[2]) / 2
            area += triangle_area
            volume += triangle_area * (origin[2] + a[2] + b[2]) / 3
    footprint = abs(_normal([vertices["b{:02d}".format(i)]
                             for i in range(32)])[2]) / 2
    boundary_volume = Fraction(0)
    for name, ids in faces:
        origin = vertices[ids[0]]
        for i in range(1, len(ids) - 1):
            boundary_volume += _dot(origin, _cross(
                vertices[ids[i]], vertices[ids[i + 1]])) / 6
    if area != footprint or volume <= 0 or volume != boundary_volume:
        raise ValueError("source roof/underside partition or volume disagrees")
    zero = Fraction(0)
    top_centre = tuple(sum(vertices[name][axis] for name in "abcd") / 4
                       for axis in range(3))

    def midpoint(left, right):
        return tuple((a + b) / 2
                     for a, b in zip(vertices[left], vertices[right]))

    landmarks = (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.seat_thickness_mm + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
        ("plinth-top-centre", top_centre),
        ("base-inner-end-midpoint", midpoint("e09", "e10")),
        ("base-outer-end-midpoint", midpoint("e25", "e26")),
    )
    bounds = tuple(operation(point[axis] for point in vertices.values())
                   for operation in (min, max) for axis in range(3))
    return ChairBaseGeometry(
        p, tuple((name, *point) for name, point in vertices.items()), faces,
        bounds, volume, landmarks, ring, rectangle, margins,
    )
