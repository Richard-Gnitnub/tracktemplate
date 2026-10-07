"""Prove finite rail-face relations for the reference research assembly.

The equations follow Templot5 revision 556b dxf_unit.pas::fish_calcs
(lines 13654-13662), the solid-jaw key and the S1 inner-jaw grip.
Every dimension comes from the supplied components. No rail profile or
clearance value is embedded here. The planes omit corner radii and do
not define a complete rail contour, rail solid or physical-stock fit.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors
Copyright (C) 2026 TrackTemplate contributors
"""

from dataclasses import dataclass
from fractions import Fraction

from tracktemplate.domain.chair_assembly import (
    ChairAssemblyGeometry,
    assemble_chair_components,
)


CHAIR_RAIL_INTERFACE_RULE_ID = "tracktemplate.chair.rail-interface-proof.v1"


@dataclass(frozen=True)
class ChairRailProfile:
    """Exact full-size reference lengths in mm and dimensionless fish ratio.

    Source model-fit choices and built-in printing allowances remain
    part of these reference inputs. They are not prototype measurements.
    """

    rail_head_width_mm: Fraction
    rail_foot_width_mm: Fraction
    rail_web_width_mm: Fraction
    rail_depth_mm: Fraction
    rail_web_top_depth_mm: Fraction
    rail_web_bottom_depth_mm: Fraction
    rail_fish_ratio: Fraction
    seat_thickness_mm: Fraction
    rail_foot_depth_mm: Fraction
    rail_web_face_top_from_rail_bottom_mm: Fraction
    rail_web_face_bottom_from_rail_bottom_mm: Fraction


@dataclass(frozen=True)
class ChairRailFaceRelation:
    """One named face or endpoint pair on one infinite reference plane.

    In the accepted chair frame, a*x + b*y + c*z - offset = residual.
    The three coefficients are dimensionless, without normalisation.
    Offsets, coordinates and residuals are mm, not normal distances.
    Full-size and model points have the same origin and axes. Their
    coefficients agree; model lengths divide by the explicit scale.
    Plane coincidence alone proves neither contact area nor clearance.
    """

    relation_id: str
    component_role: str
    face_id: object
    plane_id: str
    vertex_ids: tuple
    plane_coefficients: tuple
    plane_offset_mm: Fraction
    points_mm: tuple
    residuals_mm: tuple
    model_plane_offset_mm: Fraction
    model_points_mm: tuple
    model_residuals_mm: tuple


@dataclass(frozen=True)
class ChairRailInterfaceProof:
    """Derived exact equalities, never an accepted rail-fit decision."""

    profile: ChairRailProfile
    relations: tuple
    scale_denominator: Fraction
    rule_id: str = CHAIR_RAIL_INTERFACE_RULE_ID


def _profile(components):
    key = components["key"].parameters
    seat = components["rail-seat"].parameters
    inner = components["inner-jaw"].parameters
    fish = key.rail_fish_ratio
    depth = key.rail_depth_mm
    web_top = depth - key.rail_web_top_depth_mm
    web_bottom = depth - key.rail_web_bottom_depth_mm
    derived = {
        "rail_foot_depth_mm": (
            web_bottom - seat.rail_foot_width_mm / (2 * fish)
        ),
        "rail_web_face_top_from_rail_bottom_mm": (
            web_top + key.rail_web_width_mm / (2 * fish)
        ),
        "rail_web_face_bottom_from_rail_bottom_mm": (
            web_bottom - key.rail_web_width_mm / (2 * fish)
        ),
    }
    for name, expected in derived.items():
        if getattr(inner, name) != expected:
            raise ValueError(
                "rail interface derived quantity differs: " + name
            )
    return ChairRailProfile(
        rail_head_width_mm=key.rail_head_width_mm,
        rail_foot_width_mm=seat.rail_foot_width_mm,
        rail_web_width_mm=key.rail_web_width_mm,
        rail_depth_mm=depth,
        rail_web_top_depth_mm=key.rail_web_top_depth_mm,
        rail_web_bottom_depth_mm=key.rail_web_bottom_depth_mm,
        rail_fish_ratio=fish,
        seat_thickness_mm=seat.seat_thickness_mm,
        **derived,
    )


def _planes(profile):
    p = profile
    zero, one = Fraction(0), Fraction(1)
    slope = one / p.rail_fish_ratio
    height = p.seat_thickness_mm + p.rail_depth_mm
    under_head = height - p.rail_web_top_depth_mm
    upper_foot = height - p.rail_web_bottom_depth_mm
    return {
        "rail-bottom": ((zero, zero, one), p.seat_thickness_mm),
        "field-web": ((zero, one, zero), p.rail_web_width_mm / 2),
        "gauge-web": ((zero, one, zero), -p.rail_web_width_mm / 2),
        "field-under-head": ((zero, -slope, one), under_head),
        "gauge-under-head": ((zero, slope, one), under_head),
        "field-foot-upper": ((zero, slope, one), upper_foot),
        "gauge-foot-upper": ((zero, -slope, one), upper_foot),
        "gauge-foot-side": ((zero, one, zero), -p.rail_foot_width_mm / 2),
    }


def _residuals(points, coefficients, offset):
    return tuple(
        sum((coefficient * coordinate for coefficient, coordinate
             in zip(coefficients, point)), Fraction(0)) - offset
        for point in points
    )


def _relation(specification, components, planes, scale):
    identity, role, face_id, plane_id = specification
    geometry = components[role]
    if face_id is None:
        vertex_ids = ("grip-negative-top-web", "grip-positive-top-web")
    else:
        vertex_ids = dict(geometry.faces)[face_id]
    vertices = {name: (x, y, z) for name, x, y, z in geometry.vertices}
    points = tuple(vertices[name] for name in vertex_ids)
    coefficients, offset = planes[plane_id]
    residuals = _residuals(points, coefficients, offset)
    for name, residual in zip(vertex_ids, residuals):
        if residual != 0:
            raise ValueError(
                "rail interface plane differs: " + identity + "/" + name
            )
    model_points = tuple(tuple(value / scale for value in point)
                         for point in points)
    model_offset = offset / scale
    model_residuals = _residuals(model_points, coefficients, model_offset)
    if any(residual != 0 for residual in model_residuals):
        raise ValueError("model rail interface plane differs: " + identity)
    return ChairRailFaceRelation(
        relation_id=identity, component_role=role, face_id=face_id,
        plane_id=plane_id, vertex_ids=vertex_ids,
        plane_coefficients=coefficients, plane_offset_mm=offset,
        points_mm=points, residuals_mm=residuals,
        model_plane_offset_mm=model_offset, model_points_mm=model_points,
        model_residuals_mm=model_residuals,
    )


def prove_chair_rail_interface(full_size_geometry, scale_denominator):
    """Check profile consistency and nine finite source-face relations.

    The source rail-top transform is X=-x, Y=-y-head_width/2,
    Z=z+rail_depth+seat_thickness. The existing component boundaries
    already use this accepted chair frame. Their shared quantities and
    landmarks must agree. Three separately supplied inner-jaw heights
    must equal the rail fish equations without a comparison tolerance.

    This operation preserves all components. It adds no rail solid,
    corner radius, clearance, manufacturing correction or new profile.
    It accepts only the explicit Fraction(381, 5) model denominator.
    """
    if not isinstance(full_size_geometry, ChairAssemblyGeometry):
        raise TypeError("full_size_geometry must be a ChairAssemblyGeometry")
    if not isinstance(scale_denominator, Fraction):
        raise TypeError("scale_denominator must be an exact Fraction")
    if scale_denominator != Fraction(381, 5):
        raise ValueError("only the explicit 4 mm/ft comparison is supported")
    assemble_chair_components(full_size_geometry.components)
    components = dict(full_size_geometry.components)
    profile = _profile(components)
    planes = _planes(profile)
    specifications = (
        ("seat-bottom", "rail-seat", "seat-top", "rail-bottom"),
        ("key-web", "key", "web-pad", "field-web"),
        ("key-under-head", "key", "top-pad", "field-under-head"),
        ("key-foot", "key", "bottom-pad", "field-foot-upper"),
        ("inner-web-upper", "inner-jaw", "grip-back-upper", "gauge-web"),
        ("inner-web-lower", "inner-jaw", "grip-back-lower", "gauge-web"),
        ("inner-foot", "inner-jaw", "grip-bottom", "gauge-foot-upper"),
        ("inner-under-head-edge", "inner-jaw", None, "gauge-under-head"),
        ("inner-foot-side", "inner-jaw", "lower-mid-to-seat-00",
         "gauge-foot-side"),
    )
    return ChairRailInterfaceProof(
        profile=profile,
        relations=tuple(_relation(spec, components, planes, scale_denominator)
                        for spec in specifications),
        scale_denominator=scale_denominator,
    )
