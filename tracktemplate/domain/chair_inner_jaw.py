"""Construct the finite reference-only solid S1 inner jaw analytically.

Relationships follow Templot5 revision 556b dxf_unit.pas procedure
create_S1_SC_L1_CC_inner_jaw_block, with all five variant flags false.
Named definition inputs control the five chord sections, grip and bevels.
The collapsed stand and source diagonals are explicit topology, not a
smooth loft. No source grid or manufacturing correction applies.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from collections import Counter, deque
from dataclasses import dataclass, fields
from fractions import Fraction

from tracktemplate.domain.chair_outer_jaw import _number, _sines


_STAGES = ("stand", "upper-mid", "lower-mid", "seat", "plinth")


@dataclass(frozen=True)
class ChairInnerJawParameters:
    """Thirty-five full-size mm lengths and two dimensionless slopes.

    Every input is an exact Fraction. Derived widths can be recurring
    rationals; they never become rounded canonical quantity strings.
    Strict inequalities define topology, not physical rail-fit limits.
    """

    chair_half_width_mm: Fraction
    outer_corner_radius_mm: Fraction
    plinth_thickness_mm: Fraction
    seat_thickness_mm: Fraction
    rail_head_width_mm: Fraction
    rail_foot_width_mm: Fraction
    rail_web_width_mm: Fraction
    rail_depth_mm: Fraction
    rail_web_face_top_from_rail_bottom_mm: Fraction
    rail_web_face_bottom_from_rail_bottom_mm: Fraction
    rail_foot_depth_mm: Fraction
    outer_top_half_width_mm: Fraction
    outer_top_height_mm: Fraction
    outer_mid_half_width_mm: Fraction
    outer_mid_height_mm: Fraction
    outer_seat_half_width_mm: Fraction
    outer_plinth_half_width_mm: Fraction
    top_to_mid_side_slope: Fraction
    mid_to_seat_side_slope: Fraction
    grip_width_reference_height_mm: Fraction
    stand_height_mm: Fraction
    lower_mid_rib_radius_mm: Fraction
    insert_depth_mm: Fraction
    upper_mid_depth_mm: Fraction
    lower_mid_depth_mm: Fraction
    seat_depth_mm: Fraction
    plinth_depth_mm: Fraction
    stand_fillet_radius_mm: Fraction
    stand_corner_radius_mm: Fraction
    upper_mid_fillet_radius_mm: Fraction
    upper_mid_corner_radius_mm: Fraction
    lower_mid_fillet_radius_mm: Fraction
    lower_mid_corner_radius_mm: Fraction
    seat_fillet_radius_mm: Fraction
    seat_corner_radius_mm: Fraction
    plinth_fillet_radius_mm: Fraction
    plinth_corner_radius_mm: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            if value <= 0:
                raise ValueError(field.name + " must be positive")
        heights = (self._grip_top(), *self._heights())
        if any(a <= b for a, b in zip(heights, heights[1:])):
            raise ValueError(
                "heights must satisfy grip > stand > upper-mid "
                "> lower-mid > seat > plinth"
            )
        if self._grip_width() <= 0:
            raise ValueError("grip-top half-width must be positive")
        web = -(self.rail_head_width_mm - self.rail_web_width_mm) / 2
        if not web < -self.insert_depth_mm < self._foot_offset():
            raise ValueError("grip planes must satisfy web < insert < foot")
        span = self.chair_half_width_mm - self.outer_corner_radius_mm
        if span <= self.outer_plinth_half_width_mm:
            raise ValueError("bevel tips must be outside the plinth width")
        for stage in _STAGES:
            a, r, f, c, d = self._profile(stage)
            if not (a > 0 and r > 0 and a - r > c + f):
                raise ValueError(stage + ": collapsed or intersecting section")
            if stage != "stand" and d - c <= self._foot_offset():
                raise ValueError(stage + ": section must extend past foot")

    def _grip_top(self):
        return (self.seat_thickness_mm
                + self.rail_web_face_top_from_rail_bottom_mm)

    def _grip_width(self):
        # Nominal reference height determines width, not actual grip Z.
        return self.outer_top_half_width_mm + (
            self.outer_top_height_mm - self.grip_width_reference_height_mm
        ) / self.top_to_mid_side_slope

    def _foot_offset(self):
        return (self.rail_foot_width_mm - self.rail_head_width_mm) / 2

    def _heights(self):
        return (
            self.stand_height_mm,
            self.seat_thickness_mm
            + self.rail_web_face_bottom_from_rail_bottom_mm,
            self.seat_thickness_mm + self.rail_foot_depth_mm,
            self.seat_thickness_mm, self.plinth_thickness_mm,
        )

    def _widths(self):
        stand, upper, lower, _seat, _plinth = self._heights()
        return (
            self.outer_top_half_width_mm
            + (self.outer_top_height_mm - stand) / self.top_to_mid_side_slope,
            self.outer_top_half_width_mm
            + (self.outer_top_height_mm - upper) / self.top_to_mid_side_slope,
            self.outer_mid_half_width_mm
            + (self.outer_mid_height_mm - lower) / self.mid_to_seat_side_slope,
            self.outer_seat_half_width_mm, self.outer_plinth_half_width_mm,
        )

    def _profile(self, stage):
        index = _STAGES.index(stage)
        widths = self._widths()
        a = widths[index]
        side = widths[2] - self.lower_mid_rib_radius_mm
        prefix = stage.replace("-", "_")
        f = getattr(self, prefix + "_fillet_radius_mm")
        c = getattr(self, prefix + "_corner_radius_mm")
        # Source overwrites stand Y after sampling; its depth is not data.
        d = (Fraction(0) if stage == "stand"
             else getattr(self, prefix + "_depth_mm"))
        return a, a - side, f, c, d

    def source_to_chair(self, point):
        """Apply the accepted proper frame transform in full-size mm."""
        x, y, z = point
        return (-x, -y - self.rail_head_width_mm / 2,
                z + self.rail_depth_mm + self.seat_thickness_mm)


@dataclass(frozen=True)
class ChairInnerJawGeometry:
    """Derived exact boundary; canonical definitions retain only inputs."""

    parameters: ChairInnerJawParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: object
    landmarks: tuple
    source_sections_mm: tuple


def _sine(index, quarter):
    index %= 24
    if index <= 6:
        return quarter[index]
    if index <= 12:
        return quarter[12 - index]
    if index <= 18:
        return -quarter[index - 12]
    return -quarter[24 - index]


def _section(profile, foot_offset, collapsed=False):
    """Return all 41 fixed source samples, including declared aliases."""
    a, r, f, c, d = map(_number, profile)
    foot_offset = _number(foot_offset)
    points = {0: (-a, foot_offset), 1: (a, foot_offset)}
    quarter = _sines()
    quadrants = (
        (2, (a - c, d - c), c, 0, 1),
        (9, (r + f, d + f), f, -6, -1),
        (15, (_number(0), d + f), r, 0, 1),
        (21, (_number(0), d + f), r, 6, 1),
        (27, (-r - f, d + f), f, 0, -1),
        (34, (-a + c, d - c), c, 6, 1),
    )
    for offset, centre, radius, start, sense in quadrants:
        for i in range(7):
            angle = start + sense * i
            point = (
                centre[0] + radius * _sine(angle + 6, quarter),
                centre[1] + radius * _sine(angle, quarter),
            )
            identity = offset + i
            if identity in points and points[identity] != point:
                raise ValueError("source quadrant endpoints disagree")
            points[identity] = point
    if collapsed:
        points = {i: (x, foot_offset) for i, (x, _y) in points.items()}
        if points[2] != points[1] or points[40] != points[0]:
            raise ValueError("declared stand aliases disagree")
    return tuple(points[i] for i in range(41))


def _identity(stage, index):
    if stage == "stand":
        index = {2: 1, 40: 0}.get(index, index)
    return "{}-{:02d}".format(stage, index)


def _faces():
    """Declare source faces with exact shared interfaces removed."""
    faces = [
        ("plinth-cap", tuple(_identity("plinth", i)
                             for i in reversed(range(41)))),
    ]
    for upper, lower in zip(_STAGES, _STAGES[1:]):
        for i in range(41):
            # The first two front panels are internal grip interfaces.
            if i == 0 and upper in ("stand", "upper-mid"):
                continue
            j = (i + 1) % 41
            ids = (_identity(upper, i), _identity(upper, j),
                   _identity(lower, j), _identity(lower, i))
            face_id = "{}-to-{}-{:02d}".format(upper, lower, i)
            if upper == "stand":
                # Nonplanar source quads use the first-to-third diagonal.
                triangles = ((ids[0], ids[1], ids[2]),
                             (ids[0], ids[2], ids[3]))
                for part, triangle in enumerate(triangles):
                    if len(set(triangle)) == 3:
                        faces.append((face_id + "-triangle-" + str(part),
                                      triangle))
            else:
                if upper == "seat" and i == 1:
                    ids = ("seat-01", "seat-02", "plinth-02")
                elif upper == "seat" and i == 40:
                    ids = ("seat-40", "seat-00", "plinth-40")
                faces.append((face_id, ids))
    for side, seat, front, rear in (
        ("negative", "seat-01", "plinth-01", "plinth-02"),
        ("positive", "seat-00", "plinth-00", "plinth-40"),
    ):
        tip = "bevel-" + side + "-tip"
        faces.extend((
            ("bevel-" + side + "-visible", (tip, seat, rear)),
            ("bevel-" + side + "-rear", (tip, front, seat)),
            ("bevel-" + side + "-base", (tip, front, rear)),
        ))
    faces.extend(_grip_faces())
    return faces


def _grip_faces():
    ntw, ntf, nsw, nuw = (
        "grip-negative-" + suffix for suffix in
        ("top-web", "top-front", "stand-web", "upper-mid-web")
    )
    ptw, ptf, psw, puw = (
        "grip-positive-" + suffix for suffix in
        ("top-web", "top-front", "stand-web", "upper-mid-web")
    )
    ns, ps = "stand-01", "stand-00"
    nu, pu = "upper-mid-01", "upper-mid-00"
    nl, pl = "lower-mid-01", "lower-mid-00"
    faces = [("grip-top", (ntw, ntf, ptf, ptw))]
    knife = tuple(dict.fromkeys(_identity("stand", i) for i in range(1, 41)))
    # Split only the first source triangle at every knife-edge sample.
    for i, (a, b) in enumerate(zip(knife, knife[1:])):
        faces.append(("grip-front-upper-triangle-{:02d}".format(i),
                      (ntf, a, b)))
    faces.append(("grip-front-upper-triangle-38", (ntf, ps, ptf)))
    faces.extend((
        ("grip-back-upper", (ntw, nsw, psw, ptw)),
        ("grip-back-lower", (nsw, nuw, puw, psw)),
        ("grip-bottom", (nuw, nl, pl, puw)),
        ("grip-negative-upper", (ntw, ntf, ns, nsw)),
        ("grip-negative-middle", (nsw, ns, nu, nuw)),
        ("grip-negative-lower", (nuw, nu, nl)),
        ("grip-positive-upper", (ptw, ptf, ps, psw)),
        ("grip-positive-middle", (psw, ps, pu, puw)),
        ("grip-positive-lower", (puw, pu, pl)),
    ))
    return faces


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum((x * y for x, y in zip(a, b)), _number(0))


def _orient_and_check(vertices, faces):
    """Orient the proven concave boundary from its outward bottom cap."""
    if len(vertices) != 213 or len(set(vertices.values())) != 213:
        raise ValueError("distinct inner-jaw vertices collapsed")
    if len(faces) != 256 or len({name for name, _ids in faces}) != 256:
        raise ValueError("inner jaw requires 256 distinct face identities")
    edges = {}
    for number, (name, ids) in enumerate(faces):
        if len(ids) < 3 or len(set(ids)) != len(ids):
            raise ValueError(name + ": repeated face vertex")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges.setdefault(tuple(sorted((a, b))), []).append((number, a, b))
    if len(edges) != 467 or any(len(rows) != 2 for rows in edges.values()):
        raise ValueError("inner jaw must pair 467 edges into one closed shell")
    orientations, pending = {0: 1}, deque([0])
    while pending:
        here = pending.popleft()
        ids = faces[here][1]
        for a, b in zip(ids, ids[1:] + ids[:1]):
            other = next(row for row in edges[tuple(sorted((a, b)))]
                         if row[0] != here)
            sense = (-orientations[here] if (a, b) == other[1:]
                     else orientations[here])
            if other[0] in orientations:
                if orientations[other[0]] != sense:
                    raise ValueError("inner-jaw face orientation conflicts")
            else:
                orientations[other[0]] = sense
                pending.append(other[0])
    if len(orientations) != len(faces):
        raise ValueError("inner jaw must have one connected boundary")
    oriented = tuple(
        (name, ids if orientations[i] == 1 else tuple(reversed(ids)))
        for i, (name, ids) in enumerate(faces)
    )
    incidence, volume = Counter(), _number(0)
    for name, ids in oriented:
        points = [vertices[identity] for identity in ids]
        normal = tuple(sum(
            (_cross(a, b)[axis] for a, b in
             zip(points, points[1:] + points[:1])), _number(0),
        ) for axis in range(3))
        if all(value == 0 for value in normal):
            raise ValueError(name + ": degenerate face")
        if any(_dot(normal, _subtract(point, points[0])) != 0
               for point in points):
            raise ValueError(name + ": nonplanar face")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            incidence[a, b] += 1
        for i in range(1, len(points) - 1):
            volume += _dot(points[0], _cross(points[i], points[i + 1])) / 6
    if (any(count != 1 or incidence[b, a] != 1
            for (a, b), count in incidence.items())
            or len(vertices) - len(edges) + len(oriented) != 2
            or volume <= 0):
        raise ValueError("inner jaw must have one outward closed boundary")
    return oriented, volume


def _polygon_area(points):
    return sum((a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1])),
               _number(0)) / 2


def _profile_area(profile, foot_offset):
    a, r, f, c, d = profile
    sine = _sines()[1]
    return (2 * a * (d - foot_offset)
            + 2 * (f * f - c * c) * (1 - 3 * sine)
            + 2 * r * f + 6 * r * r * sine)


def _grip_interval(height, a, b, da, db):
    """Exact integral of a rectangular section with affine dimensions."""
    return height * (2 * a * da + 2 * (a + b) * (da + db) + 2 * b * db) / 6


def _integrated_volume(parameters, rings):
    """Integrate cut sections independently of boundary tetrahedra."""
    p = parameters
    heights, widths = p._heights(), p._widths()
    upper, lower = rings[0], rings[1]
    middle = []
    for i in range(41):
        j = (i + 1) % 41
        # Two intersections per quad preserve its first-to-third diagonal.
        middle.extend((
            tuple((a + b) / 2 for a, b in zip(upper[i], lower[i])),
            tuple((a + b) / 2 for a, b in zip(upper[i], lower[j])),
        ))
    volume = (heights[0] - heights[1]) * (
        4 * _polygon_area(middle) + _polygon_area(lower)
    ) / 6
    for i in range(1, 4):
        start, end = p._profile(_STAGES[i]), p._profile(_STAGES[i + 1])
        mid = tuple((a + b) / 2 for a, b in zip(start, end))
        volume += (heights[i] - heights[i + 1]) * (
            _profile_area(start, p._foot_offset())
            + 4 * _profile_area(mid, p._foot_offset())
            + _profile_area(end, p._foot_offset())
        ) / 6
    web = -(p.rail_head_width_mm - p.rail_web_width_mm) / 2
    front_depth = p._foot_offset() - web
    volume += _grip_interval(
        p._grip_top() - heights[0], p._grip_width(), widths[0],
        -p.insert_depth_mm - web, front_depth,
    )
    volume += _grip_interval(
        heights[0] - heights[1], widths[0], widths[1],
        front_depth, front_depth,
    )
    volume += _grip_interval(
        heights[1] - heights[2], widths[1], widths[2],
        front_depth, Fraction(0),
    )
    span = p.chair_half_width_mm - p.outer_corner_radius_mm
    volume += (span - widths[4]) * (heights[3] - heights[4]) * (
        p.plinth_depth_mm - p.plinth_corner_radius_mm - p._foot_offset()
    ) / 3
    return volume


def _landmarks(parameters, vertices):
    p, zero = parameters, Fraction(0)
    landmarks = [
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.seat_thickness_mm + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
    ]
    landmarks.extend(
        ("inner-jaw-" + stage + "-front-centre",
         (zero, -p.rail_foot_width_mm / 2, height))
        for stage, height in zip(_STAGES, p._heights())
    )
    landmarks.extend((
        ("inner-jaw-grip-top-front-centre",
         (zero, p.insert_depth_mm - p.rail_head_width_mm / 2, p._grip_top())),
        ("inner-jaw-grip-top-web-centre",
         (zero, -p.rail_web_width_mm / 2, p._grip_top())),
        ("inner-jaw-grip-bottom-web-centre",
         (zero, -p.rail_web_width_mm / 2, p._heights()[1])),
    ))
    landmarks.extend(
        ("inner-jaw-" + side + "-bevel-tip",
         vertices["bevel-" + side + "-tip"])
        for side in ("negative", "positive")
    )
    return tuple(landmarks)


def construct_chair_inner_jaw(parameters):
    """Construct the complete supported inner jaw without host objects.

    Exact stage inequalities establish simple sections and disjoint
    height bands. Body and grip interiors lie on opposite sides of the
    foot plane. Bevels lie outside the lower body's support planes.
    Shared interfaces alone are removed from this proven partition.
    """
    if not isinstance(parameters, ChairInnerJawParameters):
        raise TypeError("parameters must be ChairInnerJawParameters")
    p = parameters
    vertices, sections, rings = {}, [], []
    for stage, height in zip(_STAGES, p._heights()):
        ring = _section(p._profile(stage), p._foot_offset(), stage == "stand")
        rings.append(ring)
        if stage != "stand":
            area = _polygon_area(ring)
            if area <= 0 or area != _profile_area(p._profile(stage),
                                                 p._foot_offset()):
                raise ValueError(stage + ": source cap partition disagrees")
        z = _number(height - p.rail_depth_mm - p.seat_thickness_mm)
        source = tuple(("{}-{:02d}".format(stage, i), x, y, z)
                       for i, (x, y) in enumerate(ring))
        sections.append((stage, source))
        for i, (name, *point) in enumerate(source):
            if stage != "stand" or i not in (2, 40):
                vertices[name] = p.source_to_chair(point)
    span = p.chair_half_width_mm - p.outer_corner_radius_mm
    web = -(p.rail_head_width_mm - p.rail_web_width_mm) / 2
    heights, widths = p._heights(), p._widths()
    for sign, side in ((1, "negative"), (-1, "positive")):
        additions = (
            ("bevel-" + side + "-tip", sign * span,
             p._foot_offset(), p.plinth_thickness_mm),
            ("grip-" + side + "-top-web", sign * p._grip_width(),
             web, p._grip_top()),
            ("grip-" + side + "-top-front", sign * p._grip_width(),
             -p.insert_depth_mm, p._grip_top()),
            ("grip-" + side + "-stand-web", sign * widths[0],
             web, heights[0]),
            ("grip-" + side + "-upper-mid-web", sign * widths[1],
             web, heights[1]),
        )
        for name, x, y, height in additions:
            source_point = tuple(map(_number, (
                x, y, height - p.rail_depth_mm - p.seat_thickness_mm,
            )))
            vertices[name] = p.source_to_chair(source_point)
    faces, boundary_volume = _orient_and_check(vertices, _faces())
    volume = _integrated_volume(p, rings)
    if volume != boundary_volume:
        raise ValueError("inner-jaw boundary and independent volume disagree")
    bounds = tuple(operation(point[axis] for point in vertices.values())
                   for operation in (min, max) for axis in range(3))
    return ChairInnerJawGeometry(
        p, tuple((name, *point) for name, point in vertices.items()),
        faces, bounds, volume, _landmarks(p, vertices), tuple(sections),
    )
