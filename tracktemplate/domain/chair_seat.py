"""Analytical rail seat for the bounded reference-only research proof.

The parameterised construction is source-informed by Templot5 556b,
``dxf_unit.pas::create_S1_S1J_L1_CC_seat_block`` and its STL diagonal.
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors.
Copyright (C) 2026 TrackTemplateMacro contributors.
SPDX-License-Identifier: GPL-3.0-or-later

No upstream dimensional collection is embedded here. Inputs and results
use full-size millimetres in the accepted right-handed chair frame.
This rule excludes filler, special-chair branches and manufacturing
corrections. It constructs a seat component, not an assembled chair.
"""

from dataclasses import dataclass, fields
from fractions import Fraction


@dataclass(frozen=True)
class ChairSeatParameters:
    """Explicit exact lengths; source/model-fit lineage stays in the package."""

    chair_half_width_mm: Fraction
    seat_top_half_width_mm: Fraction
    outline_inset_mm: Fraction
    side_spacing_mm: Fraction
    seat_thickness_mm: Fraction
    edge_thickness_mm: Fraction
    plinth_thickness_mm: Fraction
    outer_jaw_face_mm: Fraction
    rail_head_width_mm: Fraction
    rail_foot_width_mm: Fraction
    rail_depth_mm: Fraction
    under_key_half_width_mm: Fraction

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if not isinstance(value, Fraction) or value <= 0:
                raise ValueError(item.name + " must be a positive Fraction")
        if not (
            self.outline_inset_mm < self.side_spacing_mm
            < self.chair_half_width_mm
        ):
            raise ValueError("seat inset and side spacing are out of order")
        if not (
            self.edge_thickness_mm < self.plinth_thickness_mm
            < self.seat_thickness_mm
        ):
            raise ValueError("seat, plinth and edge levels are out of order")
        if self.under_key_half_width_mm >= min(
            self.seat_top_half_width_mm,
            self.chair_half_width_mm - self.side_spacing_mm,
        ):
            raise ValueError("under-key top must fit inside both seat widths")
        if self.outer_jaw_face_mm <= (
            self.rail_head_width_mm + self.rail_foot_width_mm
        ) / 2:
            raise ValueError("outer jaw must lie beyond the rail foot")

    def source_to_chair(self, point):
        """Map full-size rail-top coordinates by a proper 180-degree turn.

        Source +Y points towards the gauge side. Both horizontal axes
        reverse, preserving handedness. Rail depth cancels from the seat
        levels, but remains necessary to locate the source rail-top datum.
        """
        if len(point) != 3 or any(
            not isinstance(value, Fraction) for value in point
        ):
            raise ValueError("source point must contain three Fractions")
        x, y, z = point
        return (
            -x,
            -y - self.rail_head_width_mm / 2,
            z + self.rail_depth_mm + self.seat_thickness_mm,
        )


@dataclass(frozen=True)
class ChairSeatGeometry:
    """Disposable analytical geometry with semantic names, never Part data."""

    parameters: ChairSeatParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: Fraction
    landmarks: tuple


def _difference(left, right):
    return tuple(a - b for a, b in zip(left, right))


def _cross(left, right):
    a, b, c = left
    x, y, z = right
    return (b * z - c * y, c * x - a * z, a * y - b * x)


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def _require_convex_faces(vertices, faces):
    """Reject folded, degenerate or nonplanar parameter combinations."""
    for name, indices in faces:
        points = [vertices[index] for index in indices]
        origin = points[0]
        normal = _cross(
            _difference(points[1], origin),
            _difference(points[2], origin),
        )
        if not any(normal):
            raise ValueError(name + " is degenerate")
        if any(_dot(normal, _difference(p, origin)) for p in points):
            raise ValueError(name + " is not planar")
        if any(
            _dot(normal, _difference(p, origin)) > 0
            for p in vertices.values()
        ):
            raise ValueError(name + " does not bound a convex seat")


def construct_chair_seat(parameters):
    """Construct the supported seat analytically, without host or IO work.

    Fractions preserve declared quantities exactly. The two under-key
    sides retain the source diagonal from top/foot to bottom/outer.
    Coplanar top triangles become one hexagonal face. No mesh is imported.
    Invalid parameter combinations raise ValueError before host work.
    """
    if not isinstance(parameters, ChairSeatParameters):
        raise TypeError("parameters must be ChairSeatParameters")
    p = parameters
    a = p.chair_half_width_mm - p.outline_inset_mm
    t = p.seat_top_half_width_mm
    b = p.chair_half_width_mm - p.side_spacing_mm
    j = p.under_key_half_width_mm
    f = p.rail_foot_width_mm
    outer_y = p.outer_jaw_face_mm - p.rail_head_width_mm / 2
    s, e, plinth = (
        p.seat_thickness_mm, p.edge_thickness_mm, p.plinth_thickness_mm
    )
    vertices = {
        "top-gauge-negative": (-t, -f / 2, s),
        "top-gauge-positive": (t, -f / 2, s),
        "top-foot-positive": (t, f / 2, s),
        "top-outer-positive": (j, outer_y, s),
        "top-outer-negative": (-j, outer_y, s),
        "top-foot-negative": (-t, f / 2, s),
        "bottom-gauge-negative": (-a, -f / 2, e),
        "bottom-gauge-positive": (a, -f / 2, e),
        "bottom-foot-positive": (a, f / 2, e),
        "bottom-outer-positive": (b, outer_y, plinth),
        "bottom-outer-negative": (-b, outer_y, plinth),
        "bottom-foot-negative": (-a, f / 2, e),
    }
    names = tuple(vertices)
    indexed_faces = (
        ("seat-top", (0, 1, 2, 3, 4, 5)),
        ("rail-bottom", (6, 11, 8, 7)),
        ("key-bottom", (11, 10, 9, 8)),
        ("outer-interface", (3, 9, 10, 4)),
        ("gauge-interface", (0, 6, 7, 1)),
        ("positive-rail-end", (1, 7, 8, 2)),
        ("negative-rail-end", (0, 5, 11, 6)),
        ("positive-key-lower", (2, 8, 9)),
        ("positive-key-upper", (2, 9, 3)),
        ("negative-key-upper", (5, 4, 10)),
        ("negative-key-lower", (5, 10, 11)),
    )
    faces = tuple(
        (name, tuple(names[index] for index in indices))
        for name, indices in indexed_faces
    )
    _require_convex_faces(vertices, faces)
    h, k = s - e, s - plinth
    length = outer_y - f / 2
    volume = f * (a + t) * h + length / 3 * (
        (a + t + b) * h + (t + b + j) * k
    )
    bounds = tuple(
        operation(point[axis] for point in vertices.values())
        for operation in (min, max) for axis in range(3)
    )
    zero = Fraction(0)
    landmarks = (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, s)),
        ("rail-top-centre", (zero, zero, s + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2, s)),
        ("outer-support-centre", (zero, outer_y, s)),
    )
    return ChairSeatGeometry(
        parameters=p,
        vertices=tuple((name, *point) for name, point in vertices.items()),
        faces=faces,
        bounds_mm=bounds,
        volume_mm3=volume,
        landmarks=landmarks,
    )
