#!/usr/bin/env python3
"""Prove synthetic nominal faces, bores and their connected open assembly."""

from dataclasses import replace
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import uuid

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_base_nominal_exact as native,
)
from tracktemplate.domain.chair_base_nominal import (  # noqa: E402
    ChairBaseNominalAperture,
    ChairBaseNominalParameters,
    ChairBaseNominalHoleParameters,
    compute_chair_base_nominal_underside_geometry,
)


def synthetic_parameters(scale=Fraction(1)):
    """Supply unequal synthetic corner radii, without prototype dimensions."""
    return ChairBaseNominalParameters(
        x_span_mm=20 * scale,
        y_span_mm=30 * scale,
        bottom_left_radius_mm=scale,
        bottom_right_radius_mm=2 * scale,
        top_right_radius_mm=3 * scale,
        top_left_radius_mm=4 * scale,
    )


def synthetic_apertures(scale=Fraction(1)):
    """Supply three distinct invented holes, without drawing dimensions."""
    return tuple(
        ChairBaseNominalAperture(
            aperture_id=aperture_id,
            centre_mm=tuple(Fraction(value) * scale for value in centre),
            radius_mm=radius * scale,
        )
        for aperture_id, centre, radius in (
            ("small", (-4, -6, 0), Fraction(1, 2)),
            ("medium", (3, 5, 0), Fraction(1)),
            ("large", (4, -5, 0), Fraction(3, 2)),
        )
    )


def document_state():
    """Capture document identities, object state and witness content."""
    return (
        App.ActiveDocument.Name if App.ActiveDocument else None,
        tuple(
            (name, tuple(
                (obj.Name, obj.TypeId, tuple(obj.State),
                 getattr(obj, "Evidence", None))
                for obj in document.Objects
            ))
            for name, document in sorted(App.listDocuments().items())
        ),
    )


def filesystem_state(directory):
    """Observe names and contents in the isolated working directory."""
    return tuple(
        (path.name, path.read_bytes()) for path in sorted(directory.iterdir())
    )


def assert_point(actual, expected, epsilon=1e-7):
    assert math.dist(tuple(actual), expected) <= epsilon


def check_face(parameters, scale=1.0):
    """Measure the native face against independent elementary geometry."""
    face = native.construct_chair_base_nominal_face(parameters)
    assert not face.isNull() and face.isValid()
    assert face.ShapeType == "Face"
    assert (
        len(face.Vertexes), len(face.Edges), len(face.Wires),
        len(face.Faces), len(face.Shells), len(face.Solids),
    ) == (8, 8, 1, 1, 0, 0)
    assert face.OuterWire.isClosed() and face.OuterWire.isValid()
    assert isinstance(face.Surface, Part.Plane)
    assert_point(face.normalAt(0, 0), (0, 0, 1))
    assert abs(face.Volume) <= 1e-7

    bounds = face.BoundBox
    expected_bounds = (-10, -15, 0, 10, 15, 0)
    measured_bounds = (
        bounds.XMin, bounds.YMin, bounds.ZMin,
        bounds.XMax, bounds.YMax, bounds.ZMax,
    )
    for actual, expected in zip(measured_bounds, expected_bounds):
        assert abs(actual - expected * scale) <= 1e-7

    # Remove four corner squares, then restore four quarter-discs.
    expected_area = (20 * 30 - (1 - math.pi / 4) * 30) * scale**2
    expected_perimeter = (2 * (20 + 30) + (math.pi / 2 - 2) * 10) * scale
    assert abs(face.Area - expected_area) <= expected_perimeter * 1e-7
    assert abs(face.Length - expected_perimeter) <= 8e-7

    lines = [edge for edge in face.Edges if isinstance(edge.Curve, Part.Line)]
    arcs = [edge for edge in face.Edges if isinstance(edge.Curve, Part.Circle)]
    assert len(lines) == len(arcs) == 4
    expected_lines = (
        ((-9, -15, 0), (8, -15, 0), (1, 0, 0)),
        ((10, -13, 0), (10, 12, 0), (0, 1, 0)),
        ((7, 15, 0), (-6, 15, 0), (-1, 0, 0)),
        ((-10, 11, 0), (-10, -14, 0), (0, -1, 0)),
    )
    for start, end, direction in expected_lines:
        start = tuple(value * scale for value in start)
        end = tuple(value * scale for value in end)
        matches = [edge for edge in lines if math.dist(
            tuple(edge.valueAt(edge.FirstParameter)), start,
        ) <= 1e-7]
        assert len(matches) == 1
        edge = matches[0]
        lines.remove(edge)
        assert_point(edge.valueAt(edge.LastParameter), end)
        assert_point(edge.tangentAt(edge.FirstParameter), direction)
        assert_point(edge.tangentAt(edge.LastParameter), direction)
        assert abs(edge.Length - math.dist(start, end)) <= 1e-7
    assert not lines

    expected_arcs = (
        (1, (-9, -14, 0), (-10, -14, 0), (-9, -15, 0),
         (0, -1, 0), (1, 0, 0)),
        (2, (8, -13, 0), (8, -15, 0), (10, -13, 0),
         (1, 0, 0), (0, 1, 0)),
        (3, (7, 12, 0), (10, 12, 0), (7, 15, 0),
         (0, 1, 0), (-1, 0, 0)),
        (4, (-6, 11, 0), (-6, 15, 0), (-10, 11, 0),
         (-1, 0, 0), (0, -1, 0)),
    )
    for (radius, centre, start, end,
         start_tangent, end_tangent) in expected_arcs:
        matches = [edge for edge in arcs if abs(
            edge.Curve.Radius - radius * scale,
        ) <= 1e-7]
        assert len(matches) == 1
        edge = matches[0]
        arcs.remove(edge)
        assert_point(edge.Curve.Center, tuple(v * scale for v in centre))
        assert_point(edge.valueAt(edge.FirstParameter),
                     tuple(v * scale for v in start))
        assert_point(edge.valueAt(edge.LastParameter),
                     tuple(v * scale for v in end))
        sweep = edge.LastParameter - edge.FirstParameter
        assert abs(sweep - math.pi / 2) < 1e-12
        assert abs(edge.Length - math.pi * radius * scale / 2) <= 1e-7
        assert_point(edge.tangentAt(edge.FirstParameter), start_tangent)
        assert_point(edge.tangentAt(edge.LastParameter), end_tangent)
    assert not arcs
    return face


def assert_recoverable(error):
    diagnostic = error.diagnostic()
    assert diagnostic["recoverable"] is True
    assert diagnostic["document_mutation"] is False
    assert diagnostic["filesystem_mutation"] is False


def check_rejections(parameters):
    """Reject invalid lengths before any call to the native constructor."""
    invalid = (
        replace(parameters, x_span_mm=Fraction(0)),
        replace(parameters, bottom_left_radius_mm=Fraction(0)),
        replace(parameters, bottom_left_radius_mm=Fraction(18)),
        replace(parameters, x_span_mm=20.0),
        object(),
    )
    original = native._make_face

    def forbidden_face(_geometry):
        raise AssertionError("invalid nominal input reached native builder")

    native._make_face = forbidden_face
    try:
        for bad in invalid:
            for operation in (
                native.construct_chair_base_nominal_face,
                native.validate_chair_base_nominal_exact_geometry,
            ):
                try:
                    operation(bad)
                except (TypeError, ValueError):
                    pass
                else:
                    raise AssertionError("invalid nominal input was accepted")
    finally:
        native._make_face = original


def check_native_failures(parameters):
    """Reject failed, displaced and reversed native construction results."""
    original = native._make_face

    def fail_kernel(_geometry):
        raise Part.OCCError("injected nominal base construction failure")

    def displace_face(geometry):
        face = original(geometry)
        face.translate(App.Vector(1, 0, 0))
        return face

    def reverse_face(geometry):
        face = original(geometry)
        face.reverse()
        return face

    try:
        for replacement in (fail_kernel, displace_face, reverse_face):
            native._make_face = replacement
            for operation in (
                native.construct_chair_base_nominal_face,
                native.validate_chair_base_nominal_exact_geometry,
            ):
                try:
                    operation(parameters)
                except native.ChairBaseNominalExactGeometryError as error:
                    assert_recoverable(error)
                    if replacement is fail_kernel:
                        assert error.code == (
                            "nominal-kernel-construction-failed"
                        )
                        assert isinstance(error.__cause__, Part.OCCError)
                else:
                    raise AssertionError("invalid native face was accepted")
    finally:
        native._make_face = original


def check_aperture_face(parameters, apertures, scale=1.0):
    """Check removed circular material and independent net measurements."""
    face = native.construct_chair_base_aperture_face(parameters, apertures)
    assert not face.isNull() and face.isValid()
    assert face.ShapeType == "Face"
    assert (
        len(face.Vertexes), len(face.Edges), len(face.Wires),
        len(face.Faces), len(face.Shells), len(face.Solids),
    ) == (11, 11, 4, 1, 0, 0)
    assert isinstance(face.Surface, Part.Plane)
    assert_point(face.normalAt(0, 0), (0, 0, 1))
    assert abs(face.Volume) <= 1e-7
    assert len(face.OuterWire.Edges) == 8
    assert all(wire.isClosed() and wire.isValid() for wire in face.Wires)

    # Gross area is 570 + 15*pi/2; the three discs total 7*pi/2.
    # Gross perimeter is 80 + 5*pi; circle lengths add 6*pi.
    expected_area = (570 + 4 * math.pi) * scale**2
    expected_perimeter = (80 + 11 * math.pi) * scale
    assert abs(face.Area - expected_area) <= expected_perimeter * 1e-7
    assert abs(face.Length - expected_perimeter) <= 11e-7
    bounds = face.BoundBox
    for actual, expected in zip(
        (bounds.XMin, bounds.YMin, bounds.ZMin,
         bounds.XMax, bounds.YMax, bounds.ZMax),
        (-10, -15, 0, 10, 15, 0),
    ):
        assert abs(actual - expected * scale) <= 1e-7

    circles = [wire.Edges[0] for wire in face.Wires
               if len(wire.Edges) == 1]
    assert len(circles) == 3
    for centre, radius in (
        ((-4, -6, 0), 0.5), ((3, 5, 0), 1.0), ((4, -5, 0), 1.5),
    ):
        centre = tuple(value * scale for value in centre)
        radius *= scale
        matches = [edge for edge in circles if (
            isinstance(edge.Curve, Part.Circle)
            and math.dist(tuple(edge.Curve.Center), centre) <= 1e-7
        )]
        assert len(matches) == 1
        circle = matches[0]
        circles.remove(circle)
        assert len(circle.Vertexes) == 1 and circle.isClosed()
        assert abs(circle.Curve.Radius - radius) <= 1e-7
        assert abs(circle.Length - 2 * math.pi * radius) <= 1e-7
        sweep = circle.LastParameter - circle.FirstParameter
        assert abs(sweep - 2 * math.pi) <= 1e-12
        assert not face.isInside(App.Vector(*centre), 1e-7, True)
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            inner = App.Vector(
                centre[0] + dx * radius / 2,
                centre[1] + dy * radius / 2, 0,
            )
            outer = App.Vector(
                centre[0] + dx * radius * 1.1,
                centre[1] + dy * radius * 1.1, 0,
            )
            assert not face.isInside(inner, 1e-7, True)
            assert face.isInside(outer, 1e-7, True)
    assert not circles
    assert face.isInside(App.Vector(0, 0, 0), 1e-7, True)
    assert not face.isInside(
        App.Vector(-9.9 * scale, 14.9 * scale, 0), 1e-7, True,
    )
    return face


def check_aperture_rejections(parameters, apertures):
    """Reject invalid aperture inputs before native shape construction."""
    first = apertures[0]
    invalid = (
        list(apertures),
        (first, first),
        (replace(first, radius_mm=Fraction(0)),),
        (replace(first, radius_mm=0.5),),
        (replace(first, centre_mm=(Fraction(0),) * 2),),
        (replace(first, centre_mm=(Fraction(0), Fraction(0), Fraction(1))),),
        (replace(first, centre_mm=(Fraction(0), Fraction(-29, 2),
                                   Fraction(0))),),
        (first, replace(first, aperture_id="overlap")),
    )
    original = native._make_aperture_face

    def forbidden_face(_geometry):
        raise AssertionError("invalid aperture reached native builder")

    native._make_aperture_face = forbidden_face
    try:
        for bad in invalid:
            for operation in (
                native.construct_chair_base_aperture_face,
                native.validate_chair_base_aperture_exact_geometry,
            ):
                try:
                    operation(parameters, bad)
                except (TypeError, ValueError):
                    pass
                else:
                    raise AssertionError("invalid aperture was accepted")
    finally:
        native._make_aperture_face = original


def check_aperture_native_failures(parameters, apertures):
    """Detect absent, displaced, resized, filled and reversed apertures."""
    original = native._make_aperture_face

    def fail_kernel(_geometry):
        raise Part.OCCError("injected aperture construction failure")

    def omit_aperture(geometry):
        return original(replace(geometry, apertures=geometry.apertures[1:]))

    def shift_aperture(geometry):
        first, *others = geometry.apertures
        x, y, z = first.centre_mm
        shifted = replace(first, centre_mm=(x + Fraction(1, 4), y, z))
        return original(replace(geometry, apertures=(shifted, *others)))

    def resize_aperture(geometry):
        first, *others = geometry.apertures
        resized = replace(first, radius_mm=first.radius_mm + Fraction(1, 4))
        return original(replace(geometry, apertures=(resized, *others)))

    def fill_apertures(geometry):
        return original(replace(geometry, apertures=()))

    def reverse_face(geometry):
        face = original(geometry)
        face.reverse()
        return face

    try:
        for replacement in (
            fail_kernel, omit_aperture, shift_aperture, resize_aperture,
            fill_apertures, reverse_face,
        ):
            native._make_aperture_face = replacement
            for operation in (
                native.construct_chair_base_aperture_face,
                native.validate_chair_base_aperture_exact_geometry,
            ):
                try:
                    operation(parameters, apertures)
                except native.ChairBaseNominalExactGeometryError as error:
                    assert_recoverable(error)
                    if replacement is fail_kernel:
                        assert isinstance(error.__cause__, Part.OCCError)
                else:
                    raise AssertionError("invalid aperture face accepted")
    finally:
        native._make_aperture_face = original


def check_apertures(parameters, gross_measurements):
    """Prove deterministic aperture output and unchanged empty-input result."""
    apertures = synthetic_apertures()
    first = native.validate_chair_base_aperture_exact_geometry(
        parameters, apertures,
    )
    second = native.validate_chair_base_aperture_exact_geometry(
        parameters, apertures,
    )
    assert first == second
    assert first["valid"] and first["closed"]
    assert first["aperture_count"] == 3
    assert [item["aperture_id"] for item in first["apertures"]] == [
        "small", "medium", "large",
    ]
    for item, centre, radius in zip(
        first["apertures"], ((-4, -6, 0), (3, 5, 0), (4, -5, 0)),
        (0.5, 1, 1.5),
    ):
        assert_point(item["centre_mm"], centre)
        assert abs(item["radius_mm"] - radius) <= 1e-7
        assert abs(item["perimeter_mm"] - 2 * math.pi * radius) <= 1e-7
    face = check_aperture_face(parameters, apertures)
    assert first["area_mm2"] == face.Area
    assert first["perimeter_mm"] == face.Length
    assert (
        first["vertex_count"], first["edge_count"], first["wire_count"],
        first["face_count"], first["shell_count"], first["solid_count"],
    ) == (11, 11, 4, 1, 0, 0)
    assert_point(first["normal"], (0, 0, 1))
    assert first["numerical_length_budget_mm"] == 1e-7
    assert first["maximum_bounds_residual_mm"] <= 1e-7
    tolerance = first["maximum_kernel_tolerance_mm"]
    assert tolerance <= 1e-7 or math.isclose(
        tolerance, 1e-7, rel_tol=1e-12, abs_tol=0,
    )
    for key in (
        "production_geometry_authorized", "document_mutation",
        "filesystem_mutation",
    ):
        assert first[key] is False

    empty = native.validate_chair_base_aperture_exact_geometry(parameters, ())
    assert empty["aperture_count"] == 0 and empty["apertures"] == []
    for key in (
        "vertex_count", "edge_count", "wire_count", "face_count",
        "shell_count", "solid_count", "bounds_mm", "area_mm2",
        "perimeter_mm", "normal",
    ):
        assert empty[key] == gross_measurements[key]
    empty_face = native.construct_chair_base_aperture_face(parameters, ())
    assert empty_face.isInside(App.Vector(-4, -6, 0), 1e-7, True)
    for scale in (Fraction(1, 5), Fraction(7, 2)):
        check_aperture_face(
            synthetic_parameters(scale), synthetic_apertures(scale),
            float(scale),
        )
    check_aperture_rejections(parameters, apertures)
    check_aperture_native_failures(parameters, apertures)
    return first


def synthetic_hole_parameters(scale=Fraction(1)):
    """Supply a hand-solvable synthetic tapered hole, not source data."""
    return ChairBaseNominalHoleParameters(
        2*scale, Fraction(17, 2)*scale, 8*scale, scale,
    )


def check_hole_shell(parameters, scale=1.0):
    """Measure the shell using independently derived synthetic constants."""
    shell = native.construct_chair_base_nominal_hole_shell(parameters)
    assert shell.ShapeType == "Shell" and shell.isValid()
    assert not shell.isClosed()
    assert tuple(len(getattr(shell, name)) for name in (
        "Vertexes", "Edges", "Wires", "Faces", "Shells", "Solids",
    )) == (3, 5, 2, 2, 1, 0)
    wall, = (f for f in shell.Faces if isinstance(f.Surface, Part.Cone))
    rounding, = (f for f in shell.Faces if isinstance(f.Surface, Part.Toroid))
    assert abs(wall.Surface.Radius - 2*scale) <= 1e-7
    assert abs(wall.Surface.SemiAngle - math.atan(3/4)) <= 1e-12
    assert abs(rounding.Surface.MajorRadius - 8.5*scale) <= 1e-7
    assert abs(rounding.Surface.MinorRadius - scale) <= 1e-7
    assert_point(rounding.Surface.Center, (0, 0, 7*scale))
    box = shell.optimalBoundingBox(False, False)
    assert_point((box.XMin, box.YMin, box.ZMin), (-8.5*scale, -8.5*scale, 0))
    assert_point((box.XMax, box.YMax, box.ZMax),
                 (8.5*scale, 8.5*scale, 8*scale))
    alpha = math.atan(4/3)
    areas = (92.15*math.pi, 2*math.pi*(8.5*alpha-0.4))
    for face, area in zip((wall, rounding), areas):
        assert abs(face.Area-area*scale**2) <= face.Length*1e-7
    assert abs(shell.Area-math.pi*(91.35+17*alpha)*scale**2) <= (
        shell.Length*1e-7
    )
    for radius, z, expected_owners in (
        (2, 0, (wall,)), (7.7, 7.6, (wall, rounding)),
        (8.5, 8, (rounding,)),
    ):
        ring, = (edge for edge in shell.Edges if (
            isinstance(edge.Curve, Part.Circle)
            and math.dist(tuple(edge.Curve.Center), (0, 0, z*scale)) <= 1e-7
        ))
        assert abs(ring.Curve.Radius-radius*scale) <= 1e-7
        assert abs(ring.Length-2*math.pi*radius*scale) <= 1e-7
        owners = [face for face in shell.Faces
                  if any(ring.isSame(edge) for edge in face.Edges)]
        assert len(owners) == len(expected_owners)
        assert all(any(face.isSame(owner) for owner in owners)
                   for face in expected_owners)
    # Independent meridian parameterisation tests interior points as well
    # as both boundaries and the common tangent, away from the seam.
    samples = [(wall, 2, 0, -.8, .6),
               (wall, 4.85, 3.8, -.8, .6),
               (wall, 7.7, 7.6, -.8, .6)]
    for psi in (0, alpha/2, alpha):
        samples.append((rounding, 8.5-math.sin(psi),
                        7+math.cos(psi), -math.sin(psi), math.cos(psi)))
    for face, radius, z, radial_normal, normal_z in samples:
        for theta in (.3, 1.8, 3.2, 5.1):
            c, s = math.cos(theta), math.sin(theta)
            point = App.Vector(radius*c*scale, radius*s*scale, z*scale)
            u, v = face.Surface.parameter(point)
            assert_point(face.valueAt(u, v), tuple(point))
            assert_point(face.normalAt(u, v),
                         (radial_normal*c, radial_normal*s, normal_z))
    return shell


def check_hole_failures(parameters):
    """Reject invalid input and injected native faults without mutation."""
    original = native._make_hole_shell
    operations = (native.construct_chair_base_nominal_hole_shell,
                  native.validate_chair_base_nominal_hole_exact_geometry)

    def forbidden(_profile):
        raise AssertionError("invalid parameters reached native construction")

    native._make_hole_shell = forbidden
    try:
        for invalid, error_type in (
            (None, TypeError),
            (replace(parameters, lower_radius_mm=2.0), TypeError),
            (replace(parameters, round_radius_mm=Fraction(0)), ValueError),
            (replace(parameters, top_height_mm=Fraction(1)), ValueError),
            (replace(parameters, mouth_radius_mm=Fraction(3)), ValueError),
        ):
            for operation in operations:
                try:
                    operation(invalid)
                except error_type:
                    pass
                else:
                    raise AssertionError("invalid hole parameters accepted")
    finally:
        native._make_hole_shell = original

    def fail_kernel(_profile):
        raise Part.OCCError("injected nominal hole failure")

    def reverse_normals(profile):
        shell = original(profile)
        shell.reverse()
        return shell

    def grow_tolerance(profile):
        shell = original(profile)
        shell.fixTolerance(1e-4)
        return shell

    def wrong_dimensions(profile):
        shell = original(profile)
        shell.translate(App.Vector(0, 0, 1))
        return shell

    try:
        for replacement in (
            lambda _profile: Part.Shape(),
            lambda _profile: Part.makeCone(2, 8, 8),
            fail_kernel, reverse_normals, grow_tolerance, wrong_dimensions,
        ):
            native._make_hole_shell = replacement
            for operation in operations:
                try:
                    operation(parameters)
                except native.ChairBaseNominalExactGeometryError as error:
                    assert_recoverable(error)
                    if replacement is fail_kernel:
                        assert isinstance(error.__cause__, Part.OCCError)
                else:
                    raise AssertionError("invalid native hole accepted")
    finally:
        native._make_hole_shell = original


def check_holes():
    """Prove fresh, deterministic, scaled and recoverable hole construction."""
    parameters = synthetic_hole_parameters()
    first = native.validate_chair_base_nominal_hole_exact_geometry(parameters)
    assert first == native.validate_chair_base_nominal_hole_exact_geometry(
        parameters,
    )
    assert first["valid"] and not first["closed"]
    assert first["solid_count"] == 0
    assert first["normal_side"] == "into-bore"
    assert [(item["surface_id"], item["surface_kind"])
            for item in first["faces"]] == [
        ("wall", "cone"), ("mouth-round", "torus"),
    ]
    assert first["numerical_length_budget_mm"] == 1e-7
    assert first["maximum_kernel_tolerance_mm"] <= 1e-7
    for key in ("production_geometry_authorized", "document_mutation",
                "filesystem_mutation"):
        assert first[key] is False
    for scale in (Fraction(1), Fraction(1, 5), Fraction(7, 2)):
        check_hole_shell(synthetic_hole_parameters(scale), float(scale))
    # Semantic surface matching is independent of a shell's face order.
    shell = native.construct_chair_base_nominal_hole_shell(parameters)
    reversed_order = Part.makeShell(list(reversed(shell.Faces)))
    profile = native.compute_chair_base_nominal_hole_profile(parameters)
    assert native._measure_hole_shell(reversed_order, profile) == first
    check_hole_failures(parameters)
    return first


def synthetic_underside_inputs(scale=Fraction(1), offset=(0, 0)):
    """Place three equal synthetic bores in a larger invented outline."""
    apertures = tuple(ChairBaseNominalAperture(
        name, (Fraction(x + offset[0]) * scale,
               Fraction(y + offset[1]) * scale, Fraction(0)), 2 * scale,
    ) for name, x, y in (("first", -40, -60), ("second", 30, 50),
                         ("third", 40, -50)))
    return (synthetic_parameters(10 * scale), apertures,
            synthetic_hole_parameters(scale))


def check_underside_shell(inputs, scale=1.0):
    """Check independent areas, translated surfaces and shared-edge uses."""
    shell = native.construct_chair_base_nominal_underside_shell(*inputs)
    assert shell.ShapeType == "Shell" and shell.isValid()
    assert not shell.isClosed()
    assert tuple(len(getattr(shell, name)) for name in (
        "Vertexes", "Edges", "Wires", "Faces", "Shells", "Solids",
    )) == (17, 23, 10, 7, 1, 0)
    underside, = (face for face in shell.Faces
                  if isinstance(face.Surface, Part.Plane))
    assert_point(underside.normalAt(0, 0), (0, 0, -1))
    assert len(underside.Wires) == 4 and underside.OuterWire.isClosed()
    alpha = math.atan(4 / 3)
    expected_area = (57000 + math.pi * (1012.05 + 51 * alpha)) * scale**2
    assert abs(shell.Area - expected_area) <= shell.Length * 1e-7
    assert abs(underside.Area - (57000 + 738 * math.pi) * scale**2) <= (
        underside.Length * 1e-7
    )
    box = shell.optimalBoundingBox(False, False)
    assert_point((box.XMin, box.YMin, box.ZMin),
                 (-100 * scale, -150 * scale, 0))
    assert_point((box.XMax, box.YMax, box.ZMax),
                 (100 * scale, 150 * scale, 8 * scale))
    free, seams, joins, total_uses = [], 0, 0, 0
    for edge in shell.Edges:
        uses = [(index, occurrence.Orientation)
                for index, face in enumerate(shell.Faces)
                for wire in face.Wires for occurrence in wire.OrderedEdges
                if occurrence.isSame(edge)]
        total_uses += len(uses)
        if len(uses) == 1:
            free.append(edge)
        else:
            assert len(uses) == 2
            assert {orientation for _index, orientation in uses} == {
                "Forward", "Reversed",
            }
            if uses[0][0] == uses[1][0]:
                seams += 1
            else:
                joins += 1
    assert (len(free), seams, joins, total_uses) == (11, 6, 6, 35)
    assert abs(sum(edge.Length for edge in free)
               - (800 + 101 * math.pi) * scale) <= 11e-7
    expected_free = list(underside.OuterWire.Edges)
    for aperture in inputs[1]:
        x, y, _z = map(float, aperture.centre_mm)
        wall, = (face for face in shell.Faces if (
            isinstance(face.Surface, Part.Cone)
            and math.dist(tuple(face.Surface.Center), (x, y, 0)) <= 1e-7
        ))
        rounding, = (face for face in shell.Faces if (
            isinstance(face.Surface, Part.Toroid)
            and math.dist(tuple(face.Surface.Center), (x, y, 7 * scale))
            <= 1e-7
        ))
        assert abs(wall.Area - 92.15 * math.pi * scale**2) <= (
            wall.Length * 1e-7
        )
        round_area = 2 * math.pi * (8.5 * alpha - .4) * scale**2
        assert abs(rounding.Area - round_area) <= rounding.Length * 1e-7
        for radius, z, owners in (
            (2, 0, (underside, wall)),
            (7.7, 7.6, (wall, rounding)),
            (8.5, 8, (rounding,)),
        ):
            ring, = (edge for edge in shell.Edges if (
                isinstance(edge.Curve, Part.Circle)
                and math.dist(tuple(edge.Curve.Center), (x, y, z * scale))
                <= 1e-7
            ))
            assert abs(ring.Curve.Radius - radius * scale) <= 1e-7
            actual = [face for face in shell.Faces
                      if any(ring.isSame(edge) for edge in face.Edges)]
            assert len(actual) == len(owners)
            assert all(any(face.isSame(owner) for face in actual)
                       for owner in owners)
            if z == 8:
                assert ring.isClosed()
                expected_free.append(ring)
        for face, radius, z, normal_r, normal_z in (
            (wall, 4.85, 3.8, -.8, .6),
            (rounding, 8.5 - 1 / math.sqrt(5), 7 + 2 / math.sqrt(5),
             -1 / math.sqrt(5), 2 / math.sqrt(5)),
        ):
            for angle in (1.3, 4.1):
                c, s = math.cos(angle), math.sin(angle)
                point = App.Vector(x + radius * c * scale,
                                   y + radius * s * scale, z * scale)
                u, v = face.Surface.parameter(point)
                assert_point(face.valueAt(u, v), tuple(point))
                assert_point(face.normalAt(u, v),
                             (normal_r * c, normal_r * s, normal_z))
    assert all(any(edge.isSame(expected) for edge in free)
               for expected in expected_free)
    return shell


def check_underside_failures(inputs):
    """Reject unsupported composition and native faults without mutation."""
    base, apertures, hole = inputs
    original = native._make_underside_shell
    operations = (native.construct_chair_base_nominal_underside_shell,
                  native.validate_chair_base_nominal_underside_exact_geometry)

    def forbidden(_geometry):
        raise AssertionError("invalid assembly reached native construction")

    native._make_underside_shell = forbidden
    try:
        touching = tuple(ChairBaseNominalAperture(
            str(index), (Fraction(x), Fraction(0), Fraction(0)), Fraction(2),
        ) for index, x in enumerate((0, 17)))
        for invalid, error_type in (
            ((None, apertures, hole), TypeError),
            ((base, (), hole), ValueError),
            ((base, list(apertures), hole), TypeError),
            ((base, touching, hole), ValueError),
            ((base, (replace(apertures[0], radius_mm=Fraction(3)),), hole),
             ValueError),
            ((base, (replace(apertures[0], centre_mm=(Fraction(0), Fraction(0),
                                                     Fraction(1))),), hole),
             ValueError),
        ):
            for operation in operations:
                try:
                    operation(*invalid)
                except error_type:
                    pass
                else:
                    raise AssertionError("invalid assembly input accepted")
    finally:
        native._make_underside_shell = original

    def fail_kernel(_geometry):
        raise Part.OCCError("injected underside assembly failure")

    def disconnected(_geometry):
        # makeShell can join coincident independent edges. The construction
        # guard must reject that repair rather than accept its valid result.
        plane = native.construct_chair_base_aperture_face(base, apertures)
        plane.reverse()
        faces = [plane]
        for aperture in apertures:
            bore = native.construct_chair_base_nominal_hole_shell(hole)
            bore.translate(App.Vector(*map(float, aperture.centre_mm)))
            faces.extend(bore.Faces)
        return native._make_identity_preserving_shell(faces)

    def reverse_plane(geometry):
        faces = original(geometry).Faces
        for face in faces:
            if isinstance(face.Surface, Part.Plane):
                face.reverse()
        return Part.makeShell(faces)

    def displaced(geometry):
        shell = original(geometry)
        shell.translate(App.Vector(1, 0, 0))
        return shell

    def grown_tolerance(geometry):
        shell = original(geometry)
        shell.fixTolerance(1e-4)
        return shell

    try:
        for replacement in (
            lambda _geometry: Part.Shape(),
            lambda geometry: Part.makeCompound([original(geometry)]),
            fail_kernel, disconnected, reverse_plane, displaced,
            grown_tolerance,
        ):
            native._make_underside_shell = replacement
            for operation in operations:
                try:
                    operation(*inputs)
                except native.ChairBaseNominalExactGeometryError as error:
                    assert_recoverable(error)
                    if replacement is fail_kernel:
                        assert isinstance(error.__cause__, Part.OCCError)
                else:
                    raise AssertionError("invalid native assembly accepted")
    finally:
        native._make_underside_shell = original

    make_shell = Part.makeShell
    geometry = compute_chair_base_nominal_underside_geometry(*inputs)
    existing = original(geometry)

    def measure_existing(*_inputs):
        return native._measure_underside_shell(existing, geometry)

    def rebuilt(faces):
        return make_shell(faces).copy()

    def reoriented(faces):
        shell = make_shell(faces)
        shell.reverse()
        return shell

    try:
        for replacement in (rebuilt, reoriented):
            Part.makeShell = replacement
            for operation in operations + (measure_existing,):
                try:
                    operation(*inputs)
                except native.ChairBaseNominalExactGeometryError as error:
                    assert_recoverable(error)
                    assert error.code == "underside-construction-changed"
                else:
                    raise AssertionError("changed shell construction accepted")
    finally:
        Part.makeShell = make_shell


def check_undersides():
    """Check repeatability, identity order, scales and recoverable failures."""
    inputs = synthetic_underside_inputs()
    validate = native.validate_chair_base_nominal_underside_exact_geometry
    first = validate(*inputs)
    assert first == validate(*inputs)
    assert first["connected"] and not first["closed"]
    assert [hole["aperture_id"] for hole in first["holes"]] == [
        "first", "second", "third",
    ]
    assert first["free_boundary_loop_count"] == 4
    assert first["free_boundary_edge_count"] == 11
    assert first["periodic_seam_count"] == first["shared_junction_count"] == 6
    assert first["numerical_length_budget_mm"] == 1e-7
    tolerance = first["maximum_kernel_tolerance_mm"]
    assert tolerance <= 1e-7 or math.isclose(tolerance, 1e-7, rel_tol=1e-12)
    for key in ("production_geometry_authorized", "document_mutation",
                "filesystem_mutation"):
        assert first[key] is False
    for scale in (Fraction(1), Fraction(1, 5), Fraction(7, 2)):
        check_underside_shell(synthetic_underside_inputs(scale), float(scale))
    check_underside_shell(synthetic_underside_inputs(offset=(1, 2)))
    shell = native.construct_chair_base_nominal_underside_shell(*inputs)
    reordered = native._measure_underside_shell(
        Part.makeShell(list(reversed(shell.Faces))),
        compute_chair_base_nominal_underside_geometry(*inputs),
    )
    assert reordered["holes"] == first["holes"]
    assert reordered["underside"] == first["underside"]
    assert reordered["bounds_mm"] == first["bounds_mm"]
    changed_order = validate(
        inputs[0], inputs[1][2:] + inputs[1][:2], inputs[2],
    )
    assert changed_order["holes"] == first["holes"][2:] + first["holes"][:2]
    single = native.validate_chair_base_nominal_underside_exact_geometry(
        inputs[0], inputs[1][:1], inputs[2],
    )
    assert (single["face_count"], single["free_boundary_loop_count"],
            single["shared_junction_count"]) == (3, 2, 2)
    check_underside_failures(inputs)
    return first


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    initial = document_state()
    initial_directory = Path.cwd()
    witness = App.newDocument("NominalBaseWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Nominal face and failure must preserve this"
        witness.recompute()
        before = document_state()
        with TemporaryDirectory(prefix="tracktemplate-nominal-base-") as name:
            directory = Path(name)
            witness_path = directory / "witness.bin"
            witness_path.write_bytes(b"preserve nominal witness")
            os.chdir(directory)
            files_before = filesystem_state(directory)
            parameters = synthetic_parameters()
            first = native.validate_chair_base_nominal_exact_geometry(
                parameters,
            )
            second = native.validate_chair_base_nominal_exact_geometry(
                parameters,
            )
            assert first == second
            assert first["valid"] and first["closed"]
            assert (
                first["vertex_count"], first["edge_count"],
                first["wire_count"], first["face_count"],
                first["shell_count"], first["solid_count"],
            ) == (8, 8, 1, 1, 0, 0)
            face = check_face(parameters)
            assert first["area_mm2"] == face.Area
            assert first["perimeter_mm"] == face.Length
            assert_point(first["normal"], (0, 0, 1))
            assert first["numerical_length_budget_mm"] == 1e-7
            tolerance = first["maximum_kernel_tolerance_mm"]
            assert tolerance <= 1e-7 or math.isclose(
                tolerance, 1e-7, rel_tol=1e-12, abs_tol=0,
            )
            assert first["maximum_bounds_residual_mm"] <= 1e-7
            assert first["production_geometry_authorized"] is False
            assert first["document_mutation"] is False
            assert first["filesystem_mutation"] is False
            for scale in (Fraction(1, 5), Fraction(7, 2)):
                check_face(synthetic_parameters(scale), float(scale))
            check_rejections(parameters)
            check_native_failures(parameters)
            aperture_measurements = check_apertures(parameters, first)
            hole_measurements = check_holes()
            underside_measurements = check_undersides()
            assert document_state() == before
            assert Path.cwd() == directory
            assert filesystem_state(directory) == files_before
            os.chdir(initial_directory)
        print("TRACKTEMPLATE_CHAIR_BASE_NOMINAL=" + json.dumps({
            "profile": qualification["compatibility_evaluation"][
                "matched_profile_id"
            ],
            "synthetic_geometry": first,
            "synthetic_aperture_geometry": aperture_measurements,
            "synthetic_hole_geometry": hole_measurements,
            "synthetic_underside_geometry": underside_measurements,
            "shared_lower_edges_and_connected_open_shell": True,
            "connected_open_wall_and_tangent_round": True,
            "circular_apertures_remove_material": True,
            "empty_apertures_preserve_gross_geometry": True,
            "independent_native_geometry_checks": True,
            "repeat_and_scale": True,
            "invalid_input_rejected_before_geometry": True,
            "invalid_native_results_rejected": True,
            "document_and_working_directory_preserved": True,
        }, sort_keys=True))
    finally:
        os.chdir(initial_directory)
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("Phase 9B nominal chair-base FreeCAD validation passed")


# FreeCADCmd executes scripts with their filename as __name__.
main()
