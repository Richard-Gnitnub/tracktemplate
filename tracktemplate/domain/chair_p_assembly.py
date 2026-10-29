"""Compose the three proven P components in their common chair frame.

The outer-jaw component retains its spacer and body as separate solids.
There is no key, inner jaw, fixing, fusion or physical-fit qualification.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from fractions import Fraction

from tracktemplate.domain.chair_base import (
    ChairBaseGeometry,
    ChairBaseParameters,
)
from tracktemplate.domain.chair_p_outer_jaw import (
    ChairPOuterJawGeometry,
    ChairPOuterJawParameters,
)
from tracktemplate.domain.chair_p_seat import (
    ChairPSeatGeometry,
    ChairPSeatParameters,
)


CHAIR_P_ASSEMBLY_ROLES = ("base-plinth", "rail-seat", "outer-jaw")
_GEOMETRY_TYPES = (
    ChairBaseGeometry, ChairPSeatGeometry, ChairPOuterJawGeometry,
)
_PARAMETER_TYPES = (
    ChairBaseParameters, ChairPSeatParameters, ChairPOuterJawParameters,
)
_SHARED_PARAMETERS = (
    "rail_head_width_mm", "rail_depth_mm", "seat_thickness_mm",
    "edge_thickness_mm", "plinth_thickness_mm", "rail_foot_width_mm",
)


@dataclass(frozen=True)
class ChairPAssemblyGeometry:
    """Three components and four bodies in full-size millimetres.

    The exact volume sum preserves the seat's recorded Decimal value.
    This is a sum of component volumes, not the volume of a union.
    """

    components: tuple
    table_centre_from_inner_end_mm: Fraction
    bounds_mm: tuple
    component_volume_sum_mm3: Fraction
    landmarks: tuple


def validate_p_chair_parameters(
    base, seat, jaw, *, table_centre_from_inner_end_mm,
):
    """Refuse inconsistent source interfaces before geometry construction.

    The table/end relationship follows Templot5 556b dxf_unit.pas:5582
    and math_unit.pas:29142. The explicit end distance has package-owned
    lineage; the base's modified source length already includes opening.
    Widths for the base, slide-seat and jaw have distinct meanings.
    """
    parameters = (base, seat, jaw)
    if any(not isinstance(value, kind) for value, kind in
           zip(parameters, _PARAMETER_TYPES)):
        raise TypeError("P assembly needs its three finite parameter types")
    if not isinstance(table_centre_from_inner_end_mm, Fraction):
        raise TypeError("table/end distance must be an exact Fraction")
    if table_centre_from_inner_end_mm <= 0:
        raise ValueError("table/end distance must be positive")
    for name in _SHARED_PARAMETERS:
        values = [getattr(p, name) for p in parameters if hasattr(p, name)]
        if any(value != values[0] for value in values[1:]):
            raise ValueError("P assembly shared input differs: " + name)
    if base.chair_inner_length_mm != (
        seat.table_centre_from_gauge_face_mm + table_centre_from_inner_end_mm
    ):
        raise ValueError("P table centre and source inner-end length differ")


def assemble_p_chair_components(
    components, *, table_centre_from_inner_end_mm,
):
    """Retain three ordered components without moving or joining geometry.

    Parameters agree exactly. The seat records common landmarks in its
    existing isolated 80-digit Decimal representation; compare that same
    representation without introducing a geometric tolerance. Bounds and
    volume aggregation do not depend on the caller's Decimal context.
    """
    if not isinstance(components, tuple) or len(components) != 3:
        raise ValueError("P assembly requires exactly three named components")
    for item, role, kind in zip(
        components, CHAIR_P_ASSEMBLY_ROLES, _GEOMETRY_TYPES,
    ):
        if (not isinstance(item, tuple) or len(item) != 2
                or item[0] != role or not isinstance(item[1], kind)):
            raise ValueError(
                "P assembly component role, order or type differs"
            )
    geometries = tuple(item[1] for item in components)
    parameters = tuple(g.parameters for g in geometries)
    validate_p_chair_parameters(
        *parameters,
        table_centre_from_inner_end_mm=table_centre_from_inner_end_mm,
    )
    p = parameters[0]
    zero = Fraction(0)
    landmarks = (
        ("base-origin", (zero, zero, zero)),
        ("rail-seat-centre", (zero, zero, p.seat_thickness_mm)),
        ("rail-top-centre", (zero, zero,
                             p.seat_thickness_mm + p.rail_depth_mm)),
        ("gauge-face-at-seat", (zero, -p.rail_head_width_mm / 2,
                                p.seat_thickness_mm)),
    )
    for geometry in geometries:
        expected = landmarks
        if isinstance(geometry, ChairPSeatGeometry):
            with localcontext(Context(prec=80)):
                expected = tuple((name, tuple(
                    Decimal(value.numerator) / Decimal(value.denominator)
                    for value in point
                )) for name, point in landmarks)
        actual = dict(geometry.landmarks)
        if any(actual.get(name) != point for name, point in expected):
            raise ValueError("P assembly landmark frame differs")
    bounds = tuple(
        (min if index < 3 else max)(g.bounds_mm[index] for g in geometries)
        for index in range(6)
    )
    return ChairPAssemblyGeometry(
        components=components,
        table_centre_from_inner_end_mm=table_centre_from_inner_end_mm,
        bounds_mm=bounds,
        component_volume_sum_mm3=sum(
            (Fraction(g.volume_mm3) for g in geometries), Fraction(0),
        ),
        landmarks=landmarks,
    )
