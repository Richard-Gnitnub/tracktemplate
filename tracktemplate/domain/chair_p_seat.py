"""Construct one finite reference-only P slide-seat from explicit lengths.

Templot5 556b ``dxf_unit.pas::create_P_seat_block`` supplies the profile
relationships and fixed 24 chords around the half-circle. No source
dimension, smooth arc, jaw, placement or manufacturing allowance is
embedded. The neutral inputs use full-size millimetres; the derived
coordinates use the existing right-handed chair frame.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from dataclasses import dataclass, fields
from decimal import Context, Decimal, DecimalException, localcontext
from fractions import Fraction


@dataclass(frozen=True)
class ChairPSeatParameters:
    """Nine required exact lengths for the source narrowing-neck branch.

    The table centre is measured from the source gauge-face datum. Its
    position and the neck offset are explicit inputs with package-owned
    lineage. The strict inequalities preserve topology, not rail fit.
    """

    seat_top_half_width_mm: Fraction
    table_radius_mm: Fraction
    table_centre_from_gauge_face_mm: Fraction
    table_neck_offset_mm: Fraction
    seat_thickness_mm: Fraction
    edge_thickness_mm: Fraction
    rail_head_width_mm: Fraction
    rail_foot_width_mm: Fraction
    rail_depth_mm: Fraction

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, Fraction):
                raise TypeError(field.name + " must be an exact Fraction")
            if value <= 0:
                raise ValueError(field.name + " must be positive")
        if self.seat_thickness_mm <= self.edge_thickness_mm:
            raise ValueError("seat must be above the edge level")
        if self.seat_top_half_width_mm <= self.table_radius_mm:
            raise ValueError("seat half width must exceed the table radius")
        foot_offset = (
            self.rail_foot_width_mm - self.rail_head_width_mm
        ) / 2
        if self.table_centre_from_gauge_face_mm <= (
            foot_offset + self.table_neck_offset_mm
        ):
            raise ValueError("table centre must lie beyond the neck")

    def source_to_chair(self, point):
        """Map three full-size Fraction coordinates by a proper half-turn."""
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
class ChairPSeatGeometry:
    """Disposable named geometry; irrational coordinates are approximated.

    Decimal coordinates and volume are calculated in an isolated
    80-digit context. Source outline rows are (source_id, x_mm, y_mm).
    The 31-point outline has 24 fixed arc chords. Each cap is one
    concave polygon; the 31 side faces preserve every source segment.
    """

    parameters: ChairPSeatParameters
    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: Decimal
    landmarks: tuple
    source_outline_mm: tuple


def _decimal(value):
    return Decimal(value.numerator) / Decimal(value.denominator)


def _quarter_sines():
    """Derive the fixed 7.5-degree samples from nested square roots."""
    root2, root3, root6 = (Decimal(n).sqrt() for n in (2, 3, 6))
    sin15 = (root6 - root2) / 4
    cos15 = (root6 + root2) / 4
    return (
        Decimal(0), ((1 - cos15) / 2).sqrt(), sin15,
        ((1 - root2 / 2) / 2).sqrt(), Decimal("0.5"),
        ((1 - sin15) / 2).sqrt(), root2 / 2,
        ((1 + sin15) / 2).sqrt(), root3 / 2,
        ((1 + root2 / 2) / 2).sqrt(), cos15,
        ((1 + cos15) / 2).sqrt(), Decimal(1),
    )


def _turn(first, second, third):
    return ((second[0] - first[0]) * (third[1] - first[1])
            - (second[1] - first[1]) * (third[0] - first[0]))


def _intersects(a, b, c, d):
    if any(max(a[axis], b[axis]) < min(c[axis], d[axis])
           or max(c[axis], d[axis]) < min(a[axis], b[axis])
           for axis in (0, 1)):
        return False
    return (_turn(a, b, c) * _turn(a, b, d) <= 0
            and _turn(c, d, a) * _turn(c, d, b) <= 0)


def _require_outline(points):
    """Reject intersections or any collapse of the 31 source corners."""
    if len(set(points)) != 31:
        raise ValueError("P slide-seat outline loses distinct vertices")
    count = len(points)
    for index, point in enumerate(points):
        turn = _turn(points[index - 1], point, points[(index + 1) % count])
        # Only source p03 and p29 are inward neck corners.
        if not (turn > 0 if index in (1, 27) else turn < 0):
            raise ValueError(
                "P slide-seat corner exceeds calculation precision"
            )
        following = points[(index + 1) % count]
        for other in range(index + 2, count):
            if index == 0 and other == count - 1:
                continue
            if _intersects(
                point, following, points[other], points[(other + 1) % count],
            ):
                raise ValueError("P slide-seat outline intersects itself")


def construct_chair_p_seat(parameters):
    """Construct a closed faceted prism without host, file or state work.

    Exact input differences precede isolated Decimal conversion. Refuse
    lost ordering, coincident corners or arithmetic range failure; no
    healing, tolerance growth or topology substitution is performed.
    Returned faces have outward winding in the chair frame.
    """
    if not isinstance(parameters, ChairPSeatParameters):
        raise TypeError("parameters must be ChairPSeatParameters")
    p = parameters
    foot = (p.rail_foot_width_mm - p.rail_head_width_mm) / 2
    neck = foot + p.table_neck_offset_mm
    try:
        with localcontext(Context(prec=80)):
            width = _decimal(p.seat_top_half_width_mm)
            radius = _decimal(p.table_radius_mm)
            centre = _decimal(p.table_centre_from_gauge_face_mm)
            foot_y, neck_y = _decimal(foot), _decimal(neck)
            seat = _decimal(p.seat_thickness_mm)
            edge = _decimal(p.edge_thickness_mm)
            if not (width > radius and centre > neck_y and seat > edge):
                raise ValueError("P slide-seat exceeds calculation precision")
            outline = [("p02", -width, foot_y), ("p03", -radius, neck_y)]
            sines = _quarter_sines()
            for index in range(25):
                cosine = sines[abs(12 - index)]
                if index > 12:
                    cosine = -cosine
                sine = sines[min(index, 24 - index)]
                outline.append((
                    "p{:02d}".format(index + 4),
                    -radius * cosine, centre + radius * sine,
                ))
            bottom_y = _decimal(foot - p.rail_foot_width_mm)
            outline.extend((
                ("p29", radius, neck_y), ("p30", width, foot_y),
                ("p33", width, bottom_y), ("p34", -width, bottom_y),
            ))
            _require_outline(tuple(row[1:] for row in outline))
            head_half = _decimal(p.rail_head_width_mm / 2)
            vertices = tuple(
                (level + "-" + name, -x, -y - head_half, z)
                for level, z in (("top", seat), ("bottom", edge))
                for name, x, y in outline
            )
            _require_outline(tuple(row[1:3] for row in vertices[:31]))
            # The source outline is clockwise. The proper XY half-turn
            # preserves its winding; only the upper cap is reversed.
            top = tuple("top-" + row[0] for row in outline)
            bottom = tuple("bottom-" + row[0] for row in outline)
            faces = [("seat-top", tuple(reversed(top))),
                     ("seat-bottom", bottom)]
            for index, (name, _x, _y) in enumerate(outline):
                following = (index + 1) % len(outline)
                faces.append((
                    "side-" + name + "-" + outline[following][0],
                    (bottom[index], top[index], top[following],
                     bottom[following]),
                ))
            # Shoelace area follows the actual faceted outline, not a
            # smooth half-circle approximation.
            area = -sum(
                a[1] * b[2] - b[1] * a[2]
                for a, b in zip(outline, outline[1:] + outline[:1])
            ) / 2
            volume = area * _decimal(
                p.seat_thickness_mm - p.edge_thickness_mm
            )
            bounds = tuple(
                operation(row[axis] for row in vertices)
                for operation in (min, max) for axis in (1, 2, 3)
            )
            zero = Decimal(0)
            landmarks = (
                ("base-origin", (zero, zero, zero)),
                ("rail-seat-centre", (zero, zero, seat)),
                ("rail-top-centre", (
                    zero, zero, _decimal(
                        p.seat_thickness_mm + p.rail_depth_mm
                    ),
                )),
                ("gauge-face-at-seat", (zero, -head_half, seat)),
                ("table-centre-at-seat", (
                    zero, -centre - head_half, seat,
                )),
            )
            if not volume.is_finite() or volume <= 0 or any(
                not value.is_finite()
                for row in vertices for value in row[1:]
            ) or any(not value.is_finite()
                     for _name, point in landmarks for value in point):
                raise ValueError("P slide-seat exceeds calculation range")
            return ChairPSeatGeometry(
                p, vertices, tuple(faces), bounds, volume, landmarks,
                tuple(outline),
            )
    except DecimalException as error:
        raise ValueError("P slide-seat exceeds calculation range") from error
