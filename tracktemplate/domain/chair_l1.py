"""Construct the bounded reference-only L1 body from explicit inputs.

Templot5 556b source: chairs_unit.pas:952-966,1211-1230,1436-1461;
dxf_unit.pas:3451-3664,3915-3950,4289-4404,5753-5761,6029-6032.
Shared S1 primitives retain exact sampling, frame and KEY construction.
The L1 outer jaw has three closed parts that meet only along edges.
No fusion, physical-fit claim or manufacturing policy is supplied.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from collections import Counter, deque
from dataclasses import dataclass, fields, replace
from fractions import Fraction

from tracktemplate.domain.chair_assembly import (
    CHAIR_ASSEMBLY_ROLES,
    ChairAssemblyGeometry,
)
from tracktemplate.domain.chair_base import (
    ChairBaseGeometry,
    ChairBaseParameters,
    construct_chair_base,
)
from tracktemplate.domain.chair_inner_jaw import (
    ChairInnerJawGeometry,
    ChairInnerJawParameters,
    _faces as _inner_faces,
    _polygon_area,
    construct_chair_inner_jaw,
)
from tracktemplate.domain.chair_key import ChairKeyGeometry
from tracktemplate.domain.chair_outer_jaw import (
    ChairOuterJawGeometry,
    _cross,
    _dot,
    _normal,
    _number,
    _sines,
    _subtract,
)
from tracktemplate.domain.chair_seat import (
    ChairSeatGeometry,
    ChairSeatParameters,
    construct_chair_seat,
)


_COMMON_LANDMARKS = (
    "base-origin", "rail-seat-centre", "rail-top-centre",
    "gauge-face-at-seat",
)


def _positive_fields(parameters):
    for field in fields(parameters):
        value = getattr(parameters, field.name)
        if not isinstance(value, Fraction):
            raise TypeError(field.name + " must be an exact Fraction")
        if value <= 0:
            raise ValueError(field.name + " must be positive")


@dataclass(frozen=True)
class ChairL1BaseParameters(ChairBaseParameters):
    """The shared fourteen lengths with the L1 equal-height roof rule."""

    def __post_init__(self):
        _positive_fields(self)
        if max(self.inner_corner_radius_mm, self.outer_corner_radius_mm,
               self.plinth_side_inset_mm) >= self.chair_half_width_mm:
            raise ValueError("radii and side inset must be inside half width")
        midpoint = self.outline_midpoint_offset_mm
        if (self.inner_corner_radius_mm + midpoint
                >= self.chair_inner_length_mm
                or self.outer_corner_radius_mm + midpoint
                >= self.chair_outer_length_mm):
            raise ValueError("midpoints must be strictly between the corners")
        if self.plinth_end_inset_mm >= min(
            self.chair_inner_length_mm, self.chair_outer_length_mm,
        ):
            raise ValueError("end inset must be inside both source extents")
        if self.plinth_thickness_mm != self.edge_thickness_mm:
            raise ValueError("L1 plinth and edge heights must agree")
        if self.seat_thickness_mm <= self.edge_thickness_mm:
            raise ValueError("L1 seat must be above the equal-height roof")


@dataclass(frozen=True)
class ChairL1SeatParameters(ChairSeatParameters):
    """The shared twelve lengths; chair width is the S1 seat reference.

    This width is deliberately not the wider L1 base width. Both lower
    levels are the L1 edge height, as dxf_unit.pas:6029-6032 specifies.
    """

    def __post_init__(self):
        _positive_fields(self)
        if not (self.outline_inset_mm < self.side_spacing_mm
                < self.chair_half_width_mm):
            raise ValueError("seat inset and side spacing are out of order")
        if not (self.edge_thickness_mm == self.plinth_thickness_mm
                < self.seat_thickness_mm):
            raise ValueError("L1 seat must be above equal edge/plinth levels")
        if self.under_key_half_width_mm >= min(
            self.seat_top_half_width_mm,
            self.chair_half_width_mm - self.side_spacing_mm,
        ):
            raise ValueError("under-key top must fit inside both seat widths")
        if self.outer_jaw_face_mm <= (
            self.rail_head_width_mm + self.rail_foot_width_mm
        ) / 2:
            raise ValueError("outer jaw must lie beyond the rail foot")


@dataclass(frozen=True)
class ChairL1OuterJawParameters:
    """Fifteen exact full-size mm lengths for the three-part outer jaw.

    Top depth is behind the jaw face. Edge depth is from the source
    gauge face. Bevel widths are S1 references, not L1 base dimensions.
    Strict inequalities establish separate bodies, not physical fit.
    """

    top_height_mm: Fraction
    edge_height_mm: Fraction
    top_half_width_mm: Fraction
    top_depth_mm: Fraction
    top_corner_radius_mm: Fraction
    edge_side_clearance_mm: Fraction
    edge_depth_mm: Fraction
    edge_corner_radius_mm: Fraction
    bevel_seat_half_width_mm: Fraction
    bevel_tip_half_width_mm: Fraction
    plinth_thickness_mm: Fraction
    seat_thickness_mm: Fraction
    outer_jaw_face_mm: Fraction
    rail_head_width_mm: Fraction
    rail_depth_mm: Fraction

    def __post_init__(self):
        _positive_fields(self)
        if not (self.top_height_mm > self.seat_thickness_mm
                > self.edge_height_mm == self.plinth_thickness_mm):
            raise ValueError(
                "L1 heights must satisfy top > seat > edge=plinth"
            )
        if not (self.top_half_width_mm < self.bevel_seat_half_width_mm
                < self.edge_half_width_mm < self.bevel_tip_half_width_mm):
            raise ValueError("L1 section and bevel widths are out of order")
        for width, depth, radius in (
            (self.top_half_width_mm, self.top_depth_mm,
             self.top_corner_radius_mm),
            (self.edge_half_width_mm,
             self.edge_depth_mm - self.outer_jaw_face_mm,
             self.edge_corner_radius_mm),
        ):
            if min(width, depth) <= radius:
                raise ValueError("L1 corner must be inside its section")
        body_at_seat = self.top_half_width_mm + (
            self.edge_half_width_mm - self.top_half_width_mm
        ) * (self.top_height_mm - self.seat_thickness_mm) / (
            self.top_height_mm - self.edge_height_mm
        )
        if self.bevel_seat_half_width_mm <= body_at_seat:
            raise ValueError("L1 bevel must be outside the body side plane")

    @property
    def edge_half_width_mm(self):
        """Derive the source width exactly; it need not be a decimal."""
        return self.top_half_width_mm + (
            self.bevel_seat_half_width_mm - self.top_half_width_mm
        ) * (self.top_height_mm - self.edge_height_mm) / (
            self.top_height_mm - self.seat_thickness_mm
        ) - self.edge_side_clearance_mm

    def source_to_chair(self, point):
        """Apply the shared proper source-frame transform in mm."""
        x, y, z = point
        return (-x, -y - self.rail_head_width_mm / 2,
                z + self.rail_depth_mm + self.seat_thickness_mm)


@dataclass(frozen=True)
class ChairL1OuterJawGeometry(ChairOuterJawGeometry):
    """Three named closed parts; coincident part vertices stay distinct."""

    parts: tuple


@dataclass(frozen=True)
class ChairL1InnerJawParameters(ChairInnerJawParameters):
    """Shared S1 reference profile plus explicit L1 sampling controls.

    The two additional lengths are full-size mm. The fillet factor is
    dimensionless source-derived model geometry, not a prototype fact.
    """

    chair_inner_length_mm: Fraction
    inner_outline_inset_mm: Fraction
    plinth_fillet_factor: Fraction

    def __post_init__(self):
        super().__post_init__()
        if self.clamp_limit_mm() <= self.plinth_depth_mm:
            raise ValueError("L1 clamp must be beyond the plinth depth")

    def clamp_limit_mm(self):
        """Return the explicit source-space cap on selected samples."""
        return self.chair_inner_length_mm - self.inner_outline_inset_mm

    def _profile(self, stage):
        a, r, f, c, d = super()._profile(stage)
        if stage == "plinth":
            f *= self.plinth_fillet_factor
        return a, r, f, c, d


def construct_chair_l1_base(parameters):
    """Keep all source roof partitions at the explicit L1 equal height."""
    if not isinstance(parameters, ChairL1BaseParameters):
        raise TypeError("parameters must be ChairL1BaseParameters")
    return construct_chair_base(parameters)


def construct_chair_l1_seat(parameters):
    """Use the shared seat construction with explicit L1 lower levels."""
    if not isinstance(parameters, ChairL1SeatParameters):
        raise TypeError("parameters must be ChairL1SeatParameters")
    return construct_chair_seat(parameters)


def _orient_boundary(vertices, faces):
    """Check and orient one declared closed shell without host repair."""
    if len(set(vertices.values())) != len(vertices):
        raise ValueError("distinct L1 part vertices collapsed")
    edges = {}
    for index, (name, ids) in enumerate(faces):
        if len(ids) < 3 or len(set(ids)) != len(ids):
            raise ValueError(name + ": repeated face vertex")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges.setdefault(tuple(sorted((a, b))), []).append((index, a, b))
    if any(len(rows) != 2 for rows in edges.values()):
        raise ValueError("L1 part must pair every edge into one closed shell")
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
                    raise ValueError("L1 boundary orientation conflicts")
            else:
                orientations[other[0]] = sense
                pending.append(other[0])
    if (len(orientations) != len(faces)
            or len(vertices) - len(edges) + len(faces) != 2):
        raise ValueError("L1 part must have one connected spherical boundary")
    oriented = tuple(
        (name, ids if orientations[i] == 1 else tuple(reversed(ids)))
        for i, (name, ids) in enumerate(faces)
    )
    incidence, volume = Counter(), _number(0)
    for name, ids in oriented:
        points = [vertices[identity] for identity in ids]
        normal = _normal(points)
        if all(value == 0 for value in normal):
            raise ValueError(name + ": degenerate face")
        if any(_dot(normal, _subtract(point, points[0])) != 0
               for point in points):
            raise ValueError(name + ": nonplanar face")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            incidence[a, b] += 1
        for i in range(1, len(points) - 1):
            volume += _dot(points[0], _cross(points[i], points[i + 1])) / 6
    if any(count != 1 or incidence[b, a] != 1
           for (a, b), count in incidence.items()) or volume == 0:
        raise ValueError("L1 part must have a nonzero oriented volume")
    if volume < 0:
        oriented = tuple(
            (name, tuple(reversed(ids))) for name, ids in oriented
        )
        volume = -volume
    return oriented, volume


def _bounds(vertices):
    return tuple(operation(point[axis] for point in vertices.values())
                 for operation in (min, max) for axis in range(3))


def _common_landmarks(parameters):
    p, zero = parameters, Fraction(0)
    return (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.seat_thickness_mm + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
    )


def _outer_section(width, rear, radius, face):
    points = [(_number(-width), _number(-face)),
              (_number(width), _number(-face))]
    sines = _sines()
    for sign in (1, -1):
        for index in range(7):
            x = width - radius + radius * sines[6 - index]
            y = -rear + radius - radius * sines[index]
            if sign == -1:
                x = -width + radius - radius * sines[index]
                y = -rear + radius - radius * sines[6 - index]
            points.append((x, y))
    return tuple(points)


def _outer_area(width, depth, radius):
    return 2 * width * depth - 2 * radius * radius * (1 - 3 * _sines()[1])


def construct_chair_l1_outer_jaw(parameters):
    """Keep the two-section jaw and both closed bevel tetrahedra separate.

    Source dxf_unit.pas:3636-3651 supplies four faces per bevel. The
    source width correction places each seat apex outside the jaw side
    plane. Their common edge is not a surface to remove or fuse.
    """
    if not isinstance(parameters, ChairL1OuterJawParameters):
        raise TypeError("parameters must be ChairL1OuterJawParameters")
    p = parameters
    profiles = (
        ("top", p.top_height_mm, p.top_half_width_mm,
         p.outer_jaw_face_mm + p.top_depth_mm, p.top_corner_radius_mm),
        ("edge", p.edge_height_mm, p.edge_half_width_mm,
         p.edge_depth_mm, p.edge_corner_radius_mm),
    )
    vertices, sections = {}, []
    for stage, height, width, rear, radius in profiles:
        ring = _outer_section(width, rear, radius, p.outer_jaw_face_mm)
        z = _number(height - p.rail_depth_mm - p.seat_thickness_mm)
        source = tuple(("{}-{:02d}".format(stage, index), x, y, z)
                       for index, (x, y) in enumerate(ring))
        sections.append((stage, source))
        for name, *point in source:
            vertices[name] = p.source_to_chair(point)
        if -_polygon_area(ring) != _outer_area(
            width, rear - p.outer_jaw_face_mm, radius,
        ):
            raise ValueError(stage + ": L1 section area disagrees")
    faces = [("top-cap", tuple("top-{:02d}".format(i) for i in range(16))),
             ("edge-cap", tuple("edge-{:02d}".format(i)
                                for i in reversed(range(16))))]
    for i in range(16):
        j = (i + 1) % 16
        faces.append(("top-to-edge-{:02d}".format(i), (
            "top-{:02d}".format(i), "top-{:02d}".format(j),
            "edge-{:02d}".format(j), "edge-{:02d}".format(i),
        )))
    faces, boundary_volume = _orient_boundary(vertices, faces)
    start = (p.top_half_width_mm, p.top_depth_mm, p.top_corner_radius_mm)
    end = (p.edge_half_width_mm, p.edge_depth_mm - p.outer_jaw_face_mm,
           p.edge_corner_radius_mm)
    middle = tuple((a + b) / 2 for a, b in zip(start, end))
    volume = (p.top_height_mm - p.edge_height_mm) * (
        _outer_area(*start) + 4 * _outer_area(*middle) + _outer_area(*end)
    ) / 6
    if volume != boundary_volume:
        raise ValueError("L1 outer boundary and integrated volume disagree")
    landmarks = _common_landmarks(p)
    body = ChairOuterJawGeometry(
        p, tuple((name, *point) for name, point in vertices.items()),
        faces, _bounds(vertices), volume, landmarks, tuple(sections),
    )
    parts = [("body", body)]
    for side, sign, front, rear in (
        ("negative", -1, "edge-01", "edge-02"),
        ("positive", 1, "edge-00", "edge-15"),
    ):
        prefix = "bevel-" + side + "-"
        points = {
            prefix + "front": vertices[front],
            prefix + "rear": vertices[rear],
            prefix + "seat": tuple(map(_number, (
                sign * p.bevel_seat_half_width_mm,
                p.outer_jaw_face_mm - p.rail_head_width_mm / 2,
                p.seat_thickness_mm,
            ))),
            prefix + "tip": tuple(map(_number, (
                sign * p.bevel_tip_half_width_mm,
                p.outer_jaw_face_mm - p.rail_head_width_mm / 2,
                p.plinth_thickness_mm,
            ))),
        }
        local_faces = tuple(
            (prefix + name, tuple(prefix + item for item in ids))
            for name, ids in (
                ("base", ("front", "tip", "rear")),
                ("inside", ("front", "seat", "rear")),
                ("visible", ("seat", "tip", "rear")),
                ("rear", ("tip", "seat", "front")),
            )
        )
        local_faces, local_volume = _orient_boundary(points, local_faces)
        expected_volume = (
            (p.bevel_tip_half_width_mm - p.edge_half_width_mm)
            * (p.seat_thickness_mm - p.edge_height_mm)
            * (p.edge_depth_mm - p.edge_corner_radius_mm
               - p.outer_jaw_face_mm) / 6
        )
        if local_volume != expected_volume:
            raise ValueError("L1 bevel tetrahedron volume disagrees")
        part = ChairOuterJawGeometry(
            p, tuple((name, *point) for name, point in points.items()),
            local_faces, _bounds(points), local_volume, landmarks, (),
        )
        parts.append(("bevel-" + side, part))
    all_vertices = tuple(row for _name, part in parts for row in part.vertices)
    all_faces = tuple(row for _name, part in parts for row in part.faces)
    return ChairL1OuterJawGeometry(
        p, all_vertices, all_faces,
        _bounds({name: tuple(point) for name, *point in all_vertices}),
        sum(part.volume_mm3 for _name, part in parts), landmarks,
        tuple(sections), tuple(parts),
    )


def _triangulated_band_volume(upper, lower, height):
    """Integrate the source first-to-third diagonal through its midpoint."""
    middle = []
    for i in range(len(upper)):
        j = (i + 1) % len(upper)
        middle.extend((
            tuple((a + b) / 2 for a, b in zip(upper[i], lower[i])),
            tuple((a + b) / 2 for a, b in zip(upper[i], lower[j])),
        ))
    return height * (
        _polygon_area(upper) + 4 * _polygon_area(middle)
        + _polygon_area(lower)
    ) / 6


def construct_chair_l1_inner_jaw(parameters):
    """Apply explicit L1 sample clipping to the shared inner-jaw rule.

    Only plinth samples 9 through 33 are capped. Unchanged corner arcs
    retain their source extents. Every lower-band quadrilateral uses the
    source first-to-third diagonal; no smooth clipping surface is fitted.
    """
    if not isinstance(parameters, ChairL1InnerJawParameters):
        raise TypeError("parameters must be ChairL1InnerJawParameters")
    p = parameters
    raw = construct_chair_inner_jaw(p)
    sections = list(raw.source_sections_mm)
    raw_plinth = sections[4][1]
    limit = _number(p.clamp_limit_mm())
    plinth = tuple(
        (name, x, min(y, limit) if 9 <= i <= 33 else y, z)
        for i, (name, x, y, z) in enumerate(raw_plinth)
    )
    sections[4] = ("plinth", plinth)
    vertices = {name: tuple(point) for name, *point in raw.vertices}
    for name, *point in plinth:
        vertices[name] = p.source_to_chair(point)
    faces = []
    for name, ids in _inner_faces():
        if name.startswith("seat-to-plinth-") and len(ids) == 4:
            faces.extend((
                (name + "-triangle-0", (ids[0], ids[1], ids[2])),
                (name + "-triangle-1", (ids[0], ids[2], ids[3])),
            ))
        else:
            faces.append((name, ids))
    faces, boundary_volume = _orient_boundary(vertices, faces)
    upper = tuple((x, y) for _name, x, y, _z in sections[3][1])
    old_lower = tuple((x, y) for _name, x, y, _z in raw_plinth)
    lower = tuple((x, y) for _name, x, y, _z in plinth)
    height = p.seat_thickness_mm - p.plinth_thickness_mm
    volume = raw.volume_mm3 - _triangulated_band_volume(
        upper, old_lower, height,
    ) + _triangulated_band_volume(upper, lower, height)
    if volume != boundary_volume:
        raise ValueError("L1 inner boundary and integrated volume disagree")
    return replace(
        raw,
        vertices=tuple((name, *point) for name, point in vertices.items()),
        faces=faces, bounds_mm=_bounds(vertices), volume_mm3=volume,
        source_sections_mm=tuple(sections),
    )


def assemble_l1_chair_components(components):
    """Compose five semantic components with explicit family invariants.

    Inner-jaw widths refer to the S1 source profile, not the actual L1
    outer sections. The rail-seat width also remains an S1 reference.
    Separate solids and their reference overlaps are retained.
    """
    expected_types = (
        ChairBaseGeometry, ChairSeatGeometry, ChairKeyGeometry,
        ChairL1OuterJawGeometry, ChairInnerJawGeometry,
    )
    parameter_types = (
        ChairL1BaseParameters, ChairL1SeatParameters, None,
        ChairL1OuterJawParameters, ChairL1InnerJawParameters,
    )
    if not isinstance(components, tuple) or len(components) != 5:
        raise ValueError("L1 assembly requires exactly five named components")
    for item, role, expected, parameter_type in zip(
        components, CHAIR_ASSEMBLY_ROLES, expected_types, parameter_types,
    ):
        if (not isinstance(item, tuple) or len(item) != 2
                or item[0] != role or not isinstance(item[1], expected)
                or (parameter_type is not None and not isinstance(
                    item[1].parameters, parameter_type,
                ))):
            raise ValueError(
                "L1 assembly component role, order or type differs"
            )
    geometries = tuple(item[1] for item in components)
    parameters = tuple(g.parameters for g in geometries)
    for name in (
        "edge_thickness_mm", "plinth_thickness_mm", "seat_thickness_mm",
        "rail_head_width_mm", "rail_foot_width_mm", "rail_web_width_mm",
        "rail_depth_mm", "outer_jaw_face_mm",
    ):
        values = [getattr(p, name) for p in parameters if hasattr(p, name)]
        if any(value != values[0] for value in values[1:]):
            raise ValueError("L1 assembly shared input differs: " + name)
    base, seat, _key, outer, inner = parameters
    for name in ("chair_half_width_mm", "outer_corner_radius_mm",
                 "chair_inner_length_mm"):
        if getattr(base, name) != getattr(inner, name):
            raise ValueError(
                "L1 inner jaw references a different base: " + name
            )
    if outer.edge_height_mm != base.edge_thickness_mm:
        raise ValueError("L1 outer jaw references a different edge height")
    if outer.bevel_seat_half_width_mm != inner.outer_seat_half_width_mm:
        raise ValueError("L1 jaws reference different S1 seat widths")
    if seat.under_key_half_width_mm != inner.outer_seat_half_width_mm:
        raise ValueError("L1 seat references a different S1 jaw seat width")
    landmarks = dict(geometries[0].landmarks)
    for geometry in geometries[1:]:
        other = dict(geometry.landmarks)
        if any(other.get(name) != landmarks[name]
               for name in _COMMON_LANDMARKS):
            raise ValueError("L1 assembly landmark frame differs")
    bounds = tuple(
        (min if index < 3 else max)(g.bounds_mm[index] for g in geometries)
        for index in range(6)
    )
    return ChairAssemblyGeometry(
        components, bounds, sum(g.volume_mm3 for g in geometries),
        tuple((name, landmarks[name]) for name in _COMMON_LANDMARKS),
    )
