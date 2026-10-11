#!/usr/bin/env python3
"""Prove the nominal gross plan face in FreeCAD with synthetic data."""

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
    ChairBaseNominalParameters,
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
            assert document_state() == before
            assert Path.cwd() == directory
            assert filesystem_state(directory) == files_before
            os.chdir(initial_directory)
        print("TRACKTEMPLATE_CHAIR_BASE_NOMINAL=" + json.dumps({
            "profile": qualification["compatibility_evaluation"][
                "matched_profile_id"
            ],
            "synthetic_geometry": first,
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
