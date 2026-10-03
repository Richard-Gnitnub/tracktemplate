"""Construct the finite reference-only solid-jaw key analytically.

The dimensional relationships are informed by Templot5 revision 556b,
dxf_unit.pas::create_3d_key_block(False, False). Source dimensions are
supplied by a provenance-bearing definition, never embedded here.
Source first-to-third face diagonals are retained explicitly.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from dataclasses import dataclass, fields
from fractions import Fraction


@dataclass(frozen=True)
class ChairKeyParameters:
    """Exact full-size lengths in mm, plus a dimensionless fish ratio.

    Pad length and taper are explicit source model-fit choices.
    Deformation is the source assembly overlap, not prototype geometry.
    No manufacturing compensation or loose-jaw variant is supported.
    """

    key_length_mm: Fraction
    key_pad_length_mm: Fraction
    key_pad_taper_mm: Fraction
    key_deformation_mm: Fraction
    outer_jaw_face_mm: Fraction
    rail_head_width_mm: Fraction
    rail_web_width_mm: Fraction
    rail_web_top_depth_mm: Fraction
    rail_web_bottom_depth_mm: Fraction
    rail_fish_ratio: Fraction
    rail_depth_mm: Fraction
    seat_thickness_mm: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            minimum = 0 if field.name == "key_deformation_mm" else 1
            if value < 0 or (minimum and value == 0):
                raise ValueError(field.name + " is outside its domain")
        if self.key_pad_length_mm >= self.key_length_mm:
            raise ValueError("key pad must be shorter than the key")
        width = (self.rail_head_width_mm - self.rail_web_width_mm) / 2
        if not 0 < self.key_pad_taper_mm < width:
            raise ValueError("key taper must be inside the head/web gap")
        if self.outer_jaw_face_mm <= self.rail_head_width_mm:
            raise ValueError("outer jaw must be outside the key apex")
        if self.rail_web_bottom_depth_mm <= self.rail_web_top_depth_mm:
            raise ValueError("rail web depths must be ordered")
        fish_depth = self.rail_head_width_mm / (2 * self.rail_fish_ratio)
        if self.rail_web_top_depth_mm <= fish_depth:
            raise ValueError("key apex must be below the rail top")
        if self.rail_depth_mm <= self.rail_web_bottom_depth_mm + fish_depth:
            raise ValueError("key bottom must be above the rail seat")

    def source_to_chair(self, point):
        """Apply the accepted proper source-to-chair frame transform."""
        x, y, z = point
        return (
            -x,
            -y - self.rail_head_width_mm / 2,
            z + self.rail_depth_mm + self.seat_thickness_mm,
        )


@dataclass(frozen=True)
class ChairKeyGeometry:
    """Named planar boundary and independent exact volume, not a mesh."""

    parameters: ChairKeyParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: Fraction
    landmarks: tuple


def _difference(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _outward_faces(vertices, faces):
    """Orient declared faces about an interior point and prove closure.

    This analytical orientation step reconciles source face winding;
    it does not heal, reorder or infer topology from a host shape.
    """
    centre = tuple(
        sum(point[axis] for point in vertices.values()) / len(vertices)
        for axis in range(3)
    )
    outward = []
    edges = {}
    for name, ids in faces:
        points = [vertices[identity] for identity in ids]
        origin = points[0]
        normal = _cross(
            _difference(points[1], origin), _difference(points[2], origin)
        )
        if not any(normal):
            raise ValueError(name + " is degenerate")
        interior = _dot(normal, _difference(centre, origin))
        if interior == 0:
            raise ValueError(name + " has no strict interior")
        if interior > 0:
            ids = tuple(reversed(ids))
            normal = tuple(-value for value in normal)
        if any(_dot(normal, _difference(p, origin)) for p in points):
            raise ValueError(name + " is not planar")
        if any(
            _dot(normal, _difference(p, origin)) > 0
            for p in vertices.values()
        ):
            raise ValueError(name + " does not bound a convex key")
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges[(a, b)] = edges.get((a, b), 0) + 1
        outward.append((name, ids))
    if any(n != 1 or edges.get((b, a)) != 1
           for (a, b), n in edges.items()):
        raise ValueError("key boundary is not an oriented closed manifold")
    return tuple(outward)


def construct_chair_key(parameters):
    """Construct only the non-check-rail, solid-jaw reference key.

    Preserve source triangulation on the four nonplanar taper faces.
    Join coplanar end pieces and split long boundaries at pad vertices.
    The result has 20 vertices, 36 edges and 18 planar faces. Invalid
    parameters raise before host work. All arithmetic remains exact.
    """
    if not isinstance(parameters, ChairKeyParameters):
        raise TypeError("parameters must be ChairKeyParameters")
    p = parameters
    length, pad = p.key_length_mm, p.key_pad_length_mm
    head, web, fish = (
        p.rail_head_width_mm, p.rail_web_width_mm, p.rail_fish_ratio
    )
    height = p.rail_depth_mm + p.seat_thickness_mm
    top = height - p.rail_web_top_depth_mm + head / (2 * fish)
    bottom = height - p.rail_web_bottom_depth_mm - head / (2 * fish)
    upper = height - p.rail_web_top_depth_mm + web / (2 * fish)
    lower = height - p.rail_web_bottom_depth_mm - web / (2 * fish)
    back = p.outer_jaw_face_mm + p.key_deformation_mm - head / 2
    ridge = head / 2
    vertices = {}
    for section, x, end in (
        ("negative-end", -length / 2, True),
        ("negative-pad", -pad / 2, False),
        ("positive-pad", pad / 2, False),
        ("positive-end", length / 2, True),
    ):
        inner = web / 2 + (p.key_pad_taper_mm if end else 0)
        values = (
            ("back-top", back, upper), ("apex", ridge, top),
            ("web-top", inner, upper), ("web-bottom", inner, lower),
            ("toe", ridge, bottom), ("back-bottom", back, bottom),
        )
        for name, y, z in values:
            if end or not name.startswith("back-"):
                vertices[section + "-" + name] = (x, y, z)

    def ids(section, names):
        return tuple(section + "-" + name for name in names)

    faces = [
        ("back", (
            "negative-end-back-top", "positive-end-back-top",
            "positive-end-back-bottom", "negative-end-back-bottom",
        )),
    ]
    profile = (
        "back-top", "apex", "web-top", "web-bottom", "toe", "back-bottom"
    )
    for side in ("negative", "positive"):
        faces.append((side + "-end", ids(side + "-end", profile)))
    sections = ("negative-end", "negative-pad", "positive-pad", "positive-end")
    for name, a, b in zip(
        ("negative-web-taper", "web-pad", "positive-web-taper"),
        sections, sections[1:],
    ):
        faces.append((name, (
            a + "-web-top", b + "-web-top",
            b + "-web-bottom", a + "-web-bottom",
        )))
    for name, back_id, front_id, web_id in (
        ("top", "back-top", "apex", "web-top"),
        ("bottom", "back-bottom", "toe", "web-bottom"),
    ):
        faces.append((name + "-back", (
            "negative-end-" + back_id, "positive-end-" + back_id,
            *(section + "-" + front_id for section in reversed(sections)),
        )))
        faces.append((name + "-pad", (
            "negative-pad-" + front_id, "positive-pad-" + front_id,
            "positive-pad-" + web_id, "negative-pad-" + web_id,
        )))
        for side in ("negative", "positive"):
            outer, inner = side + "-end-", side + "-pad-"
            a, b = outer + front_id, inner + front_id
            c, d = inner + web_id, outer + web_id
            faces.extend((
                (side + "-" + name + "-ridge", (a, b, c)),
                (side + "-" + name + "-web", (a, c, d)),
            ))
    faces = _outward_faces(vertices, faces)
    width = (head - web) / 2
    rear_width = p.outer_jaw_face_mm + p.key_deformation_mm - head
    apex_height, web_height = top - bottom, upper - lower
    volume = (
        length * rear_width * (upper - bottom + apex_height) / 2
        + pad * width * (apex_height + web_height) / 2
        + (length - pad) / 6 * (
            width * (2 * apex_height + web_height)
            + (width - p.key_pad_taper_mm) * (apex_height + 2 * web_height)
        )
    )
    bounds = tuple(
        operation(point[axis] for point in vertices.values())
        for operation in (min, max) for axis in range(3)
    )
    zero = Fraction(0)
    landmarks = (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero, height)),
        ("gauge-face-at-seat", (zero, -head / 2, p.seat_thickness_mm)),
        ("key-apex-centre", (zero, ridge, top)),
        ("key-toe-centre", (zero, ridge, bottom)),
        ("key-pad-centre", (zero, web / 2, (upper + lower) / 2)),
        ("key-back-centre", (zero, back, (upper + bottom) / 2)),
        ("outer-jaw-datum", (
            zero, p.outer_jaw_face_mm - head / 2, (upper + bottom) / 2
        )),
    )
    return ChairKeyGeometry(
        parameters=p, vertices=tuple((k, *v) for k, v in vertices.items()),
        faces=faces, bounds_mm=bounds, volume_mm3=volume,
        landmarks=landmarks,
    )
