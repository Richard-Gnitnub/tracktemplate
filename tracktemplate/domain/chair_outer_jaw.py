"""Construct the complete finite reference-only solid S1 outer jaw.

Relationships follow Templot5 revision 556b dxf_unit.pas, procedure
create_s1_outer_jaw_block. Lengths stay neutral definition inputs.
Fixed 15-degree chord sections,
complete caps and both side bevels remain derived analytical geometry.
No source mark grid, smooth loft or manufacturing correction applies.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from collections import Counter
from dataclasses import dataclass, fields
from fractions import Fraction
from math import isfinite, isqrt


_ROOT_DENOMINATOR = 10 ** 60
_STAGES = ("top", "mid", "seat", "plinth")
_PROFILE_FIELDS = (
    "depth_mm", "half_rib_space_mm", "rib_width_mm", "rib_depth_mm",
    "rib_radius_mm", "fillet_radius_mm",
)


def _root_interval(value):
    lower = Fraction(isqrt(value * _ROOT_DENOMINATOR ** 2),
                     _ROOT_DENOMINATOR)
    return lower, lower + Fraction(1, _ROOT_DENOMINATOR)


@dataclass(frozen=True, eq=False)
class _Algebraic:
    """Private exact derived value in Q(sqrt(2), sqrt(3)).

    Four Fraction coefficients multiply 1, sqrt(2), sqrt(3), sqrt(6).
    This finite representation is not a canonical or interchange schema.
    Only rational division is needed for the fixed chord construction.
    """

    coefficients: tuple

    def __post_init__(self):
        if (not isinstance(self.coefficients, tuple)
                or len(self.coefficients) != 4
                or any(not isinstance(v, Fraction)
                       for v in self.coefficients)):
            raise TypeError("four exact Fraction coefficients are required")

    def __add__(self, other):
        other = _number(other)
        return _Algebraic(tuple(a + b for a, b in
                                zip(self.coefficients, other.coefficients)))

    __radd__ = __add__

    def __neg__(self):
        return _Algebraic(tuple(-v for v in self.coefficients))

    def __sub__(self, other):
        return self + (-_number(other))

    def __rsub__(self, other):
        return _number(other) + (-self)

    def __mul__(self, other):
        other = _number(other)
        result = [Fraction(0)] * 4
        for i, a in enumerate(self.coefficients):
            if not a:
                continue
            for j, b in enumerate(other.coefficients):
                if b:
                    common = i & j
                    factor = (2 if common & 1 else 1)
                    factor *= 3 if common & 2 else 1
                    result[i ^ j] += a * b * factor
        return _Algebraic(tuple(result))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not isinstance(other, (int, Fraction)):
            raise TypeError("only exact rational division is supported")
        return _Algebraic(tuple(v / other for v in self.coefficients))

    def __eq__(self, other):
        if not isinstance(other, (_Algebraic, int, Fraction)):
            return NotImplemented
        return self.coefficients == _number(other).coefficients

    def __hash__(self):
        if not any(self.coefficients[1:]):
            return hash(self.coefficients[0])
        return hash(self.coefficients)

    def interval(self):
        """Return rational enclosures; no rounding of canonical inputs."""
        lower = upper = self.coefficients[0]
        for coefficient, value in zip(self.coefficients[1:], (2, 3, 6)):
            if coefficient:
                low, high = _root_interval(value)
                lower += coefficient * (low if coefficient > 0 else high)
                upper += coefficient * (high if coefficient > 0 else low)
        return lower, upper

    def sign(self):
        """Certify sign or refuse; exact zero uses coefficient identity."""
        if not any(self.coefficients):
            return 0
        lower, upper = self.interval()
        if lower > 0:
            return 1
        if upper < 0:
            return -1
        raise ValueError("algebraic sign is unresolved by the exact enclosure")

    def __lt__(self, other):
        return (self - other).sign() < 0

    def __le__(self, other):
        return (self - other).sign() <= 0

    def __gt__(self, other):
        return (self - other).sign() > 0

    def __ge__(self, other):
        return (self - other).sign() >= 0

    def __abs__(self):
        return -self if self.sign() < 0 else self

    def __float__(self):
        lower, upper = self.interval()
        low, high = float(lower), float(upper)
        if not isfinite(low) or not isfinite(high) or low != high:
            raise ValueError("algebraic host conversion is not certified")
        return low


def _number(value):
    if isinstance(value, _Algebraic):
        return value
    if not isinstance(value, (int, Fraction)):
        raise TypeError(
            "an exact rational or private algebraic value is needed"
        )
    return _Algebraic((Fraction(value), Fraction(0), Fraction(0), Fraction(0)))


def _radical(index):
    values = [Fraction(0)] * 4
    values[index] = Fraction(1)
    return _Algebraic(tuple(values))


def _sines():
    """Return the seven exact, inclusive quarter-circle sample values."""
    return (
        _number(0), (_radical(3) - _radical(1)) / 4,
        _number(Fraction(1, 2)), _radical(1) / 2, _radical(2) / 2,
        (_radical(3) + _radical(1)) / 4, _number(1),
    )


@dataclass(frozen=True)
class ChairOuterJawParameters:
    """Thirty-three explicit full-size lengths in mm, as exact Fractions.

    The finite solid-jaw rule contains no loose pin or manufacturing
    variant. Heights and section inequalities exclude collapsed topology;
    they are mathematical domain constraints, not physical fit limits.
    """

    top_height_mm: Fraction
    mid_height_mm: Fraction
    top_depth_mm: Fraction
    top_half_rib_space_mm: Fraction
    top_rib_width_mm: Fraction
    top_rib_depth_mm: Fraction
    top_rib_radius_mm: Fraction
    top_fillet_radius_mm: Fraction
    mid_depth_mm: Fraction
    mid_half_rib_space_mm: Fraction
    mid_rib_width_mm: Fraction
    mid_rib_depth_mm: Fraction
    mid_rib_radius_mm: Fraction
    mid_fillet_radius_mm: Fraction
    seat_depth_mm: Fraction
    seat_half_rib_space_mm: Fraction
    seat_rib_width_mm: Fraction
    seat_rib_depth_mm: Fraction
    seat_rib_radius_mm: Fraction
    seat_fillet_radius_mm: Fraction
    plinth_depth_mm: Fraction
    plinth_half_rib_space_mm: Fraction
    plinth_rib_width_mm: Fraction
    plinth_rib_depth_mm: Fraction
    plinth_rib_radius_mm: Fraction
    plinth_fillet_radius_mm: Fraction
    chair_half_width_mm: Fraction
    outer_corner_radius_mm: Fraction
    plinth_thickness_mm: Fraction
    seat_thickness_mm: Fraction
    outer_jaw_face_mm: Fraction
    rail_head_width_mm: Fraction
    rail_depth_mm: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            if value <= 0:
                raise ValueError(field.name + " must be positive")
        if not (self.top_height_mm > self.mid_height_mm
                > self.seat_thickness_mm > self.plinth_thickness_mm):
            raise ValueError(
                "section heights must satisfy top > mid > seat > plinth"
            )
        for stage in _STAGES:
            _d, h, w, b, r, f = self.profile(stage)
            if not (h > f and w > 2 * r and b > r + f):
                raise ValueError(stage + ": collapsed or intersecting section")
        span = self.chair_half_width_mm - self.outer_corner_radius_mm
        plinth_width = self.plinth_half_rib_space_mm + self.plinth_rib_width_mm
        if span <= plinth_width:
            raise ValueError(
                "both bevel tips must be outside the plinth width"
            )

    def profile(self, stage):
        """Return one stage's d,h,w,b,r,f lengths in full-size mm."""
        if stage not in _STAGES:
            raise ValueError("unsupported outer-jaw stage")
        return tuple(getattr(self, stage + "_" + name)
                     for name in _PROFILE_FIELDS)

    def source_to_chair(self, point):
        """Apply the accepted proper frame transform without a source grid."""
        x, y, z = point
        return (-x, -y - self.rail_head_width_mm / 2,
                z + self.rail_depth_mm + self.seat_thickness_mm)


@dataclass(frozen=True)
class ChairOuterJawGeometry:
    """Complete derived boundary with exact algebraic coordinates/volume."""

    parameters: ChairOuterJawParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: _Algebraic
    landmarks: tuple
    source_sections_mm: tuple


def _section(profile, face):
    """Construct the clockwise 44-point source chord boundary exactly."""
    d, h, w, b, r, f = profile
    rib_y = -face - d - b + r
    fillet_y = -face - d - f
    sines = _sines()
    points = [(_number(-h - w), _number(-face)),
              (_number(h + w), _number(-face))]
    arcs = (
        (h + w - r, rib_y, r, 0),
        (h + r, rib_y, r, 1),
        (h - f, fillet_y, f, 2),
        (-h + f, fillet_y, f, 3),
        (-h - r, rib_y, r, 0),
        (-h - w + r, rib_y, r, 1),
    )
    for x, y, radius, quadrant in arcs:
        for n in range(7):
            sine, cosine = sines[n], sines[6 - n]
            dx, dy = ((cosine, -sine), (-sine, -cosine),
                      (cosine, sine), (-sine, cosine))[quadrant]
            points.append((x + radius * dx, y + radius * dy))
    return tuple(points)


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


def _area(profile):
    """Independent cap partition: five quads and six corner fans."""
    d, h, w, b, r, f = profile
    return 2 * h * d + 2 * w * (d + b) + (
        2 * f * f - 4 * r * r
    ) * (1 - 3 * _sines()[1])


def _bevel_faces(vertices, side, shared):
    tip = "bevel-" + side + "-tip"
    seat, front, rear = shared
    result = []
    for label, ids, opposite in (
        ("visible", (tip, seat, rear), front),
        ("base", (tip, front, rear), seat),
        ("rear", (tip, front, seat), rear),
    ):
        points = [vertices[name] for name in ids]
        direction = _dot(_normal(points),
                         _subtract(vertices[opposite], points[0]))
        if direction == 0:
            raise ValueError("collapsed side bevel")
        if direction > 0:
            ids = tuple(reversed(ids))
        result.append(("bevel-" + side + "-" + label, ids))
    return result


def _check_boundary(vertices, faces):
    """Check the concave body's planar, connected and oriented boundary."""
    if len(set(vertices.values())) != 178:
        raise ValueError("distinct outer-jaw vertices collapsed")
    edges = Counter()
    adjacency = {name: set() for name in vertices}
    volume = _number(0)
    for name, ids in faces:
        points = [vertices[identity] for identity in ids]
        normal = _normal(points)
        if all(value == 0 for value in normal):
            raise ValueError(name + ": degenerate face")
        if any(_dot(normal, _subtract(point, points[0])) != 0
               for point in points):
            raise ValueError(name + ": nonplanar face")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges[a, b] += 1
            adjacency[a].add(b)
            adjacency[b].add(a)
        for i in range(1, len(ids) - 1):
            volume += _dot(points[0], _cross(points[i], points[i + 1])) / 6
    if (len(faces) != 140 or len(edges) != 632
            or any(count != 1 or edges[b, a] != 1
                   for (a, b), count in edges.items())
            or len(vertices) - len(edges) // 2 + len(faces) != 2):
        raise ValueError("outer jaw must pair 316 edges into one closed shell")
    reached, pending = set(), [next(iter(vertices))]
    while pending:
        identity = pending.pop()
        if identity not in reached:
            reached.add(identity)
            pending.extend(adjacency[identity] - reached)
    if reached != set(vertices) or volume <= 0:
        raise ValueError("outer jaw must have one outward connected boundary")
    return volume


def construct_chair_outer_jaw(parameters):
    """Construct only the complete finite solid-jaw body, without a host.

    Section inequalities survive linear interpolation. They establish
    simple cap partitions throughout each band. Bevel tips lie outside
    the lower body's side planes; only their shared triangles are removed.
    """
    if not isinstance(parameters, ChairOuterJawParameters):
        raise TypeError("parameters must be ChairOuterJawParameters")
    p = parameters
    heights = (p.top_height_mm, p.mid_height_mm,
               p.seat_thickness_mm, p.plinth_thickness_mm)
    vertices, sections = {}, []
    for stage, height in zip(_STAGES, heights):
        ring = _section(p.profile(stage), p.outer_jaw_face_mm)
        z = _number(height - p.rail_depth_mm - p.seat_thickness_mm)
        source = tuple(("{}-{:02d}".format(stage, i), x, y, z)
                       for i, (x, y) in enumerate(ring))
        sections.append((stage, source))
        for name, *point in source:
            vertices[name] = p.source_to_chair(point)
        area = -sum(a[0] * b[1] - b[0] * a[1]
                    for a, b in zip(ring, ring[1:] + ring[:1])) / 2
        if area != _area(p.profile(stage)) or area <= 0:
            raise ValueError(stage + ": source cap partition disagrees")
    span = p.chair_half_width_mm - p.outer_corner_radius_mm
    for side, x in (("negative", -span), ("positive", span)):
        vertices["bevel-" + side + "-tip"] = tuple(map(_number, (
            x, p.outer_jaw_face_mm - p.rail_head_width_mm / 2,
            p.plinth_thickness_mm,
        )))
    faces = [
        ("top-cap", tuple("top-{:02d}".format(i)
                          for i in reversed(range(44)))),
        ("plinth-cap", tuple("plinth-{:02d}".format(i) for i in range(44))),
    ]
    for upper, lower in zip(_STAGES, _STAGES[1:]):
        for i in range(44):
            j = (i + 1) % 44
            ids = ("{}-{:02d}".format(upper, i),
                   "{}-{:02d}".format(upper, j),
                   "{}-{:02d}".format(lower, j),
                   "{}-{:02d}".format(lower, i))
            if upper == "seat" and i == 1:
                ids = ("seat-01", "seat-02", "plinth-02")
            elif upper == "seat" and i == 43:
                ids = ("seat-43", "seat-00", "plinth-43")
            face_id = "{}-to-{}-side-{:02d}".format(upper, lower, i)
            faces.append((face_id, ids))
    faces.extend(_bevel_faces(vertices, "negative",
                              ("seat-01", "plinth-01", "plinth-02")))
    faces.extend(_bevel_faces(vertices, "positive",
                              ("seat-00", "plinth-00", "plinth-43")))
    boundary_volume = _check_boundary(vertices, faces)
    volume = _number(0)
    for i in range(3):
        start, end = p.profile(_STAGES[i]), p.profile(_STAGES[i + 1])
        middle = tuple((a + b) / 2 for a, b in zip(start, end))
        volume += (heights[i] - heights[i + 1]) * (
            _area(start) + 4 * _area(middle) + _area(end)
        ) / 6
    d, h, w, b, r, _f = p.profile("plinth")
    bevel_height = p.seat_thickness_mm - p.plinth_thickness_mm
    volume += (span - h - w) * bevel_height * (d + b - r) / 3
    if volume != boundary_volume:
        raise ValueError("outer-jaw boundary and independent volume disagree")
    zero = Fraction(0)
    landmarks = [
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.seat_thickness_mm + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
    ]
    landmarks.extend(
        ("outer-jaw-" + stage + "-front-centre",
         (zero, p.outer_jaw_face_mm - p.rail_head_width_mm / 2, height))
        for stage, height in zip(_STAGES, heights)
    )
    landmarks.extend(
        ("outer-jaw-" + side + "-bevel-tip",
         vertices["bevel-" + side + "-tip"])
        for side in ("negative", "positive")
    )
    bounds = tuple(operation(point[axis] for point in vertices.values())
                   for operation in (min, max) for axis in range(3))
    return ChairOuterJawGeometry(
        p, tuple((name, *point) for name, point in vertices.items()),
        tuple(faces), bounds, volume, tuple(landmarks), tuple(sections),
    )
