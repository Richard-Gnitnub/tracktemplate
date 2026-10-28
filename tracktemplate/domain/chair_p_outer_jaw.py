"""Construct the fixed private P outer jaw and spacer from explicit inputs.

Relationships follow Templot5 556b dxf_unit.pas:2642-2843,
create_3d_P_outer_jaw_block with dd_str empty and loose_pin false. The
source 0-2 diagonal preserves both nonplanar jaw-end quadrilaterals.
No source dimensions, fit allowance, host geometry or file is retained.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from collections import Counter, deque
from dataclasses import dataclass, fields
from fractions import Fraction


@dataclass(frozen=True)
class ChairPOuterJawParameters:
    """Thirteen exact full-size mm lengths and one positive fish ratio.

    The finite source branch has a wider, deeper jaw bottom and a spacer
    above the plinth. The groove dimensions follow the source half-width
    and midpoint relationships. Strict inequalities preserve this
    topology; they establish no physical-fit or prototype acceptance.
    """

    jaw_top_half_width_mm: Fraction
    jaw_bottom_half_width_mm: Fraction
    jaw_top_depth_mm: Fraction
    jaw_bottom_depth_mm: Fraction
    jaw_top_slope_mm: Fraction
    plinth_thickness_mm: Fraction
    seat_thickness_mm: Fraction
    rail_depth_mm: Fraction
    rail_head_width_mm: Fraction
    rail_foot_width_mm: Fraction
    rail_web_width_mm: Fraction
    rail_web_top_from_top_mm: Fraction
    rail_web_bottom_from_top_mm: Fraction
    rail_fish_ratio: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            if value <= 0:
                raise ValueError(field.name + " must be positive")
        if (self.jaw_bottom_half_width_mm <= self.jaw_top_half_width_mm
                or self.jaw_bottom_depth_mm <= self.jaw_top_depth_mm):
            raise ValueError("P jaw bottom must be wider and deeper than top")
        if self.rail_foot_width_mm <= self.rail_web_width_mm:
            raise ValueError("P spacer requires a foot wider than the web")
        if not (self.rail_web_top_from_top_mm
                < self.rail_web_bottom_from_top_mm < self.rail_depth_mm):
            raise ValueError("P jaw rail web levels must be ordered")
        if self.seat_thickness_mm <= self.plinth_thickness_mm:
            raise ValueError("P jaw seat must be above the plinth")
        spacer_top = (-self.rail_web_top_from_top_mm
                      + self.rail_foot_width_mm / (2 * self.rail_fish_ratio))
        spacer_bottom = (
            -self.rail_web_bottom_from_top_mm
            - self.rail_foot_width_mm / (2 * self.rail_fish_ratio)
        )
        base = (-self.rail_depth_mm - self.seat_thickness_mm
                + self.plinth_thickness_mm)
        if base >= spacer_bottom:
            raise ValueError("P jaw plinth must be below the spacer bottom")
        if self.jaw_top_slope_mm >= spacer_top - base:
            raise ValueError("P jaw front top must be above its plinth")

    def source_to_chair(self, point):
        """Map a source point by a proper half-turn and datum translation.

        Source coordinates use rail-top Z and gauge-face Y. The chair
        frame has mounting Z=0 and rail-centred Y. Input coordinates
        must be three exact Fraction lengths in full-size millimetres.
        """
        if (not isinstance(point, (tuple, list)) or len(point) != 3
                or any(not isinstance(value, Fraction) for value in point)):
            raise ValueError("P jaw source point needs three exact Fractions")
        x, y, z = point
        return (-x, -y - self.rail_head_width_mm / 2,
                z + self.rail_depth_mm + self.seat_thickness_mm)


@dataclass(frozen=True)
class ChairPOuterJawPartGeometry:
    """One exact closed boundary and its unchanged source face inventory.

    Vertices and landmarks use the proper full-size chair frame. Faces
    are outward planar polygons. source_faces keep the source statement
    order and raw polygon corners, before edge subdivision or the two
    source jaw-end diagonals. The two records describe the same surface.
    """

    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: Fraction
    landmarks: tuple
    source_faces: tuple


@dataclass(frozen=True)
class ChairPOuterJawGeometry:
    """Two separately closed named parts, without a fused-casting claim."""

    parameters: ChairPOuterJawParameters
    parts: tuple
    bounds_mm: tuple
    volume_mm3: Fraction
    landmarks: tuple


def _subtract(first, second):
    return tuple(a - b for a, b in zip(first, second))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(first, second):
    return sum(a * b for a, b in zip(first, second))


def _normal(points):
    products = [_cross(a, b) for a, b in
                zip(points, points[1:] + points[:1])]
    return tuple(sum(point[axis] for point in products) for axis in range(3))


def _closed_boundary(vertices, faces):
    """Orient this declared exact surface; refuse gaps or degeneration."""
    if len(set(vertices.values())) != len(vertices):
        raise ValueError("P jaw boundary vertices collapsed")
    edges = {}
    for index, (name, ids) in enumerate(faces):
        if len(ids) < 3 or len(set(ids)) != len(ids):
            raise ValueError(name + ": repeated face vertex")
        for first, second in zip(ids, ids[1:] + ids[:1]):
            edges.setdefault(tuple(sorted((first, second))), []).append(
                (index, first, second)
            )
    if any(len(uses) != 2 for uses in edges.values()):
        raise ValueError("P jaw must pair every boundary edge")
    orientations, pending = {0: 1}, deque([0])
    while pending:
        index = pending.popleft()
        ids = faces[index][1]
        for first, second in zip(ids, ids[1:] + ids[:1]):
            other = next(row for row in edges[tuple(sorted((first, second)))]
                         if row[0] != index)
            sense = (-orientations[index] if (first, second) == other[1:]
                     else orientations[index])
            if other[0] in orientations:
                if orientations[other[0]] != sense:
                    raise ValueError("P jaw boundary orientation conflicts")
            else:
                orientations[other[0]] = sense
                pending.append(other[0])
    if (len(orientations) != len(faces)
            or len(vertices) - len(edges) + len(faces) != 2):
        raise ValueError("P jaw part must be one connected closed boundary")
    oriented = tuple(
        (name, ids if orientations[index] == 1 else tuple(reversed(ids)))
        for index, (name, ids) in enumerate(faces)
    )
    incidence, volume = Counter(), Fraction(0)
    for name, ids in oriented:
        points = tuple(vertices[key] for key in ids)
        normal = _normal(points)
        if normal == (0, 0, 0):
            raise ValueError(name + ": degenerate face")
        if any(_dot(normal, _subtract(point, points[0])) != 0
               for point in points):
            raise ValueError(name + ": nonplanar face")
        incidence.update(zip(ids, ids[1:] + ids[:1]))
        volume += sum(_dot(points[0], _cross(points[index], points[index + 1]))
                      / 6 for index in range(1, len(points) - 1))
    if (volume == 0 or any(count != 1 or incidence[b, a] != 1
                          for (a, b), count in incidence.items())):
        raise ValueError("P jaw part must enclose a nonzero volume")
    if volume < 0:
        oriented = tuple((name, tuple(reversed(ids)))
                         for name, ids in oriented)
        volume = -volume
    return oriented, volume


def _bounds(points):
    return tuple(operation(point[axis] for point in points)
                 for operation in (min, max) for axis in range(3))


def _source_points(p):
    """Evaluate the fixed source branch with exact rational arithmetic."""
    x1, x4 = p.jaw_top_half_width_mm, p.jaw_bottom_half_width_mm
    y1 = -(p.rail_head_width_mm + p.rail_foot_width_mm) / 2
    y2 = -(p.rail_head_width_mm + p.rail_web_width_mm) / 2
    y3, y4 = y1 - p.jaw_top_depth_mm, y1 - p.jaw_bottom_depth_mm
    z2 = (-p.rail_web_top_from_top_mm
          + p.rail_web_width_mm / (2 * p.rail_fish_ratio))
    z3 = (-p.rail_web_bottom_from_top_mm
          - p.rail_web_width_mm / (2 * p.rail_fish_ratio))
    z1 = z2 - (y1 - y2) / p.rail_fish_ratio
    z4 = z3 + (y1 - y2) / p.rail_fish_ratio
    z5 = -p.rail_depth_mm - p.seat_thickness_mm + p.plinth_thickness_mm
    slope = (x4 - x1) / (z4 - z1)
    x2, x3, x5 = (x1 + (z - z1) * slope for z in (z2, z3, z5))
    z6 = z1 - p.jaw_top_slope_mm
    xg, yg = x1 / 2, (y1 + y2) / 2
    zg, zf, zero = (z1 + z2) / 2, (z3 + z4) / 2, Fraction(0)
    # Lowercase letters are the east or central source points; uppercase
    # letters preserve their west partners. These IDs stay family-local.
    points = {
        "a": (x1, y1, z1), "b": (x2, y2, z2), "c": (x3, y2, z3),
        "d": (x4, y1, z4), "e": (xg, y2, z2), "f": (xg, y2, z3),
        "g": (xg, y1, z1), "h": (xg, y1, z4),
        "i": (zero, yg, zg), "j": (zero, yg, zf),
        "k": (zero, y1, z1), "l": (zero, y1, z4),
        "m": (x5, y1, z5), "n": (x5, y4, z5), "o": (x1, y3, z6),
    }
    points.update({name.upper(): (-point[0], point[1], point[2])
                   for name, point in tuple(points.items()) if point[0] != 0})
    return points


def construct_chair_p_outer_jaw(parameters):
    """Return both fixed PJAW parts without source files or host work.

    Preserve all 21 semantic source polygons and every source point.
    Split only the two nonplanar body ends on the source 0-2 diagonal;
    the other boundaries stay planar polygons. Subdivide the spacer
    front edge at its existing groove points to pair the source edges.
    No tolerance, healing, new point, Boolean operation or fusion is used.
    """
    if not isinstance(parameters, ChairPOuterJawParameters):
        raise TypeError("parameters must be ChairPOuterJawParameters")
    p = ChairPOuterJawParameters(**{
        field.name: getattr(parameters, field.name)
        for field in fields(ChairPOuterJawParameters)
    })
    source = _source_points(p)
    points = {name: p.source_to_chair(point) for name, point in source.items()}
    orders = (
        "ABCD", "abcd", "adDA", "bcfe", "BCFE",
        "efji", "EFji", "abeg", "ABEG", "eikg", "EikG",
        "dcfh", "DCFH", "fjlh", "FjlH", "AMNO", "amno",
        "aAOo", "mMNn", "amMA", "onNO",
    )
    zero = Fraction(0)
    landmarks = (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.rail_depth_mm + p.seat_thickness_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
    )
    parts = []
    for role, indices in (("spacer", range(15)), ("body", range(15, 21))):
        source_faces, faces = [], []
        for index in indices:
            name, ids = f"{role}-source-{index:02d}", tuple(orders[index])
            source_faces.append((name, ids))
            if index == 2:
                # Existing front groove points split the original top
                # and bottom edges; the complete surface is unchanged.
                faces.append((name, tuple("adhlHDAGkg")))
            elif index in (15, 16):
                faces.extend(((name + "-a", ids[:3]),
                              (name + "-b", (ids[0], ids[2], ids[3]))))
            else:
                faces.append((name, ids))
        used = {key for _name, ids in faces for key in ids}
        vertices = {key: point for key, point in points.items() if key in used}
        oriented, volume = _closed_boundary(vertices, faces)
        parts.append((role, ChairPOuterJawPartGeometry(
            tuple((key, *point) for key, point in vertices.items()),
            oriented, _bounds(tuple(vertices.values())), volume, landmarks,
            tuple(source_faces),
        )))
    return ChairPOuterJawGeometry(
        p, tuple(parts), _bounds(tuple(points.values())),
        sum(part.volume_mm3 for _role, part in parts), landmarks,
    )
