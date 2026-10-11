"""Construct transient base-plan faces from explicit nominal lengths.

This internal development primitive supplies no chair definition or rail datum.
It creates no document object, file, solid, plinth or production output.
Optional apertures describe one plane, not three-dimensional hole walls.
The existing numerical checks do not establish a physical fit tolerance.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_seat_exact import (
    KERNEL_TOLERANCE_MM,
    NUMERICAL_LENGTH_TOLERANCE_MM,
)
from tracktemplate.domain.chair_base_nominal import (
    ChairBaseNominalArc,
    compute_chair_base_aperture_geometry,
    compute_chair_base_nominal_geometry,
)


class ChairBaseNominalExactGeometryError(RuntimeError):
    """Report a recoverable construction failure without external mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return a neutral diagnostic for the explicit validation boundary."""
        return {
            "code": self.code,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
            "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairBaseNominalExactGeometryError(code, message)


def _vector(point):
    values = tuple(float(value) for value in point)
    _require(
        all(math.isfinite(value) for value in values),
        "non-finite-host-coordinate", "coordinate is not finite in the host",
    )
    return App.Vector(*values)


def _make_face(geometry):
    """Build ordered straight edges and exact circle arcs without healing."""
    edges = []
    for segment in geometry.segments:
        if isinstance(segment, ChairBaseNominalArc):
            edge = Part.makeCircle(
                float(segment.radius_mm), _vector(segment.centre_mm),
                App.Vector(0, 0, 1), float(segment.start_angle_turns * 360),
                float(segment.end_angle_turns * 360),
            )
        else:
            edge = Part.makeLine(
                _vector(segment.start_mm), _vector(segment.end_mm),
            )
        _require(
            not edge.isNull() and edge.isValid(),
            "invalid-nominal-edge", segment.segment_id,
        )
        edges.append(edge)
    wire = Part.Wire(edges)
    _require(
        wire.isClosed() and wire.isValid(),
        "invalid-nominal-wire", "expected a closed valid gross outline",
    )
    return Part.Face(wire)


def _measure_face(face, geometry):
    """Check the exact boundary against its analytical construction records."""
    epsilon = NUMERICAL_LENGTH_TOLERANCE_MM
    _require(
        not face.isNull() and face.ShapeType == "Face" and face.isValid()
        and (len(face.Vertexes), len(face.Edges), len(face.Wires),
             len(face.Faces), len(face.Shells), len(face.Solids))
        == (8, 8, 1, 1, 0, 0) and face.OuterWire.isClosed(),
        "unexpected-nominal-topology",
        "expected eight edges in one planar face with no solid",
    )
    _require(
        isinstance(face.Surface, Part.Plane)
        and math.dist(tuple(face.normalAt(0, 0)), (0, 0, 1)) <= epsilon,
        "nominal-face-orientation", "expected a plane with positive Z normal",
    )
    tolerance = face.getTolerance(1)
    _require(
        tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            tolerance, KERNEL_TOLERANCE_MM, rel_tol=1e-12, abs_tol=0,
        ),
        "nominal-tolerance-growth",
        "kernel tolerance grew during construction",
    )
    unmatched = list(face.Edges)
    edge_measurements = []
    matched_edges = []
    for segment in geometry.segments:
        start = tuple(map(float, segment.start_mm))
        end = tuple(map(float, segment.end_mm))
        candidates = [edge for edge in unmatched if (
            math.dist(tuple(edge.valueAt(edge.FirstParameter)), start)
            <= epsilon
            and math.dist(tuple(edge.valueAt(edge.LastParameter)), end)
            <= epsilon
        )]
        _require(
            len(candidates) == 1, "nominal-edge-endpoint-mismatch",
            segment.segment_id,
        )
        edge = candidates[0]
        unmatched.remove(edge)
        matched_edges.append(edge)
        residual = max(
            math.dist(tuple(edge.valueAt(edge.FirstParameter)), start),
            math.dist(tuple(edge.valueAt(edge.LastParameter)), end),
        )
        if isinstance(segment, ChairBaseNominalArc):
            _require(
                isinstance(edge.Curve, Part.Circle),
                "nominal-curve-kind-mismatch", segment.segment_id,
            )
            radius = float(segment.radius_mm)
            expected_length = math.pi * radius / 2
            _require(
                abs(edge.Curve.Radius - radius) <= epsilon
                and math.dist(tuple(edge.Curve.Center), tuple(map(
                    float, segment.centre_mm,
                ))) <= epsilon
                and abs(edge.Length - expected_length) <= epsilon,
                "nominal-circle-mismatch", segment.segment_id,
            )
            kind = "circle"
        else:
            _require(
                isinstance(edge.Curve, Part.Line),
                "nominal-curve-kind-mismatch", segment.segment_id,
            )
            _require(
                abs(edge.Length - math.dist(start, end)) <= epsilon,
                "nominal-line-length-mismatch", segment.segment_id,
            )
            kind = "line"
        edge_measurements.append({
            "segment_id": segment.segment_id, "curve_kind": kind,
            "length_mm": edge.Length, "endpoint_residual_mm": residual,
        })
    for index, edge in enumerate(matched_edges):
        following = matched_edges[(index + 1) % len(matched_edges)]
        # Unit tangent agreement is tested as a positional difference over
        # one millimetre, using the existing numerical length check.
        _require(
            math.dist(tuple(edge.tangentAt(edge.LastParameter)), tuple(
                following.tangentAt(following.FirstParameter),
            )) <= epsilon,
            "nominal-tangent-mismatch", geometry.segments[index].segment_id,
        )
    box = face.BoundBox
    bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
    residual = max(
        abs(a - float(b)) for a, b in zip(bounds, geometry.bounds_mm)
    )
    _require(
        residual <= epsilon, "nominal-bounds-mismatch",
        "native bounds differ from the nominal plan",
    )
    expected_area = (float(geometry.area_constant_mm2)
                     + math.pi * float(geometry.area_pi_coefficient_mm2))
    expected_perimeter = (
        float(geometry.perimeter_constant_mm)
        + math.pi * float(geometry.perimeter_pi_coefficient_mm)
    )
    area_budget = max(face.Length * epsilon, abs(expected_area) * 1e-12)
    _require(
        math.isfinite(expected_area) and math.isfinite(face.Area)
        and face.Area > 0 and math.isfinite(area_budget)
        and abs(face.Area - expected_area) <= area_budget,
        "nominal-area-mismatch",
        "native area differs from the analytical plan",
    )
    _require(
        math.isfinite(expected_perimeter) and math.isfinite(face.Length)
        and abs(face.Length - expected_perimeter) <= len(face.Edges) * epsilon,
        "nominal-perimeter-mismatch",
        "native perimeter differs from the analytical plan",
    )
    return {
        "frame_id": "geometric-base-plan-centre",
        "length_unit": "mm", "length_basis": "full-size",
        "freecad_version": ".".join(App.Version()[:3]),
        "opencascade_version": Part.OCC_VERSION,
        "vertex_count": 8, "edge_count": 8, "wire_count": 1,
        "face_count": 1, "solid_count": 0, "shell_count": 0,
        "valid": True, "closed": True, "normal": (0.0, 0.0, 1.0),
        "bounds_mm": bounds, "area_mm2": face.Area,
        "perimeter_mm": face.Length, "edges": edge_measurements,
        "maximum_bounds_residual_mm": residual,
        "numerical_length_budget_mm": epsilon,
        "numerical_area_budget_mm2": area_budget,
        "maximum_kernel_tolerance_mm": tolerance,
        "production_geometry_authorized": False,
        "document_mutation": False, "filesystem_mutation": False,
    }


def _construct_and_measure(parameters):
    geometry = compute_chair_base_nominal_geometry(parameters)
    try:
        face = _make_face(geometry)
        return face, _measure_face(face, geometry)
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairBaseNominalExactGeometryError(
            "nominal-kernel-construction-failed", str(error),
        ) from error


def construct_chair_base_nominal_face(parameters):
    """Validate explicit lengths and return one transient, checked plan face.

    This adapter helper is not a production package or output admission route.
    The caller owns its input provenance and any later display or disposal.
    """
    face, _measurements = _construct_and_measure(parameters)
    return face


def validate_chair_base_nominal_exact_geometry(parameters):
    """Construct a fresh face and return neutral numerical measurements."""
    _face, measurements = _construct_and_measure(parameters)
    return measurements


def _make_aperture_face(geometry):
    """Add clockwise circular inner wires to the gross outline plane."""
    gross = _make_face(geometry.outline)
    wires = [gross.OuterWire]
    for aperture in geometry.apertures:
        edge = Part.makeCircle(
            float(aperture.radius_mm), _vector(aperture.centre_mm),
            App.Vector(0, 0, 1),
        )
        wire = Part.Wire([edge])
        wire.reverse()
        _require(
            wire.isClosed() and wire.isValid(),
            "invalid-aperture-wire", aperture.aperture_id,
        )
        wires.append(wire)
    return Part.Face(wires)


def _measure_aperture_face(face, geometry):
    """Check the outer boundary, each aperture and the net planar region."""
    epsilon = NUMERICAL_LENGTH_TOLERANCE_MM
    count = len(geometry.apertures)
    _require(
        not face.isNull() and face.ShapeType == "Face" and face.isValid()
        and (len(face.Vertexes), len(face.Edges), len(face.Wires),
             len(face.Faces), len(face.Shells), len(face.Solids))
        == (8 + count, 8 + count, 1 + count, 1, 0, 0)
        and all(wire.isClosed() for wire in face.Wires),
        "unexpected-aperture-topology",
        "expected one face with an outer wire and separate circular holes",
    )
    _require(
        isinstance(face.Surface, Part.Plane)
        and math.dist(tuple(face.normalAt(0, 0)), (0, 0, 1)) <= epsilon,
        "aperture-face-orientation", "expected a plane with positive Z normal",
    )
    measurements = _measure_face(Part.Face(face.OuterWire), geometry.outline)
    tolerance = face.getTolerance(1)
    _require(
        tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            tolerance, KERNEL_TOLERANCE_MM, rel_tol=1e-12, abs_tol=0,
        ),
        "aperture-tolerance-growth", "kernel tolerance grew at an aperture",
    )
    unmatched = [wire for wire in face.Wires
                 if not wire.isSame(face.OuterWire)]
    aperture_measurements = []
    for aperture in geometry.apertures:
        centre = tuple(map(float, aperture.centre_mm))
        radius = float(aperture.radius_mm)
        candidates = [wire for wire in unmatched if (
            len(wire.Edges) == 1
            and isinstance(wire.Edges[0].Curve, Part.Circle)
            and math.dist(tuple(wire.Edges[0].Curve.Center), centre)
            <= epsilon
        )]
        _require(
            len(candidates) == 1, "aperture-centre-mismatch",
            aperture.aperture_id,
        )
        wire = candidates[0]
        unmatched.remove(wire)
        edge = wire.Edges[0]
        _require(
            wire.Orientation == "Reversed"
            and abs(edge.Curve.Radius - radius) <= epsilon
            and abs(edge.Length - 2 * math.pi * radius) <= epsilon
            and math.dist(tuple(edge.Curve.Axis), (0, 0, 1)) <= epsilon
            and not face.isInside(_vector(aperture.centre_mm), epsilon, True),
            "aperture-circle-mismatch", aperture.aperture_id,
        )
        aperture_measurements.append({
            "aperture_id": aperture.aperture_id,
            "centre_mm": tuple(edge.Curve.Center),
            "radius_mm": edge.Curve.Radius, "perimeter_mm": edge.Length,
        })
    expected_area = (float(geometry.area_constant_mm2)
                     + math.pi * float(geometry.area_pi_coefficient_mm2))
    expected_perimeter = (
        float(geometry.perimeter_constant_mm)
        + math.pi * float(geometry.perimeter_pi_coefficient_mm)
    )
    area_budget = max(face.Length * epsilon, abs(expected_area) * 1e-12)
    _require(
        math.isfinite(expected_area) and math.isfinite(face.Area)
        and face.Area > 0 and math.isfinite(area_budget)
        and abs(face.Area - expected_area) <= area_budget,
        "aperture-area-mismatch", "native net area differs from the plan",
    )
    _require(
        math.isfinite(expected_perimeter) and math.isfinite(face.Length)
        and abs(face.Length - expected_perimeter)
        <= len(face.Edges) * epsilon,
        "aperture-perimeter-mismatch",
        "native perimeter differs from the plan with apertures",
    )
    measurements.update({
        "vertex_count": 8 + count, "edge_count": 8 + count,
        "wire_count": 1 + count, "aperture_count": count,
        "apertures": aperture_measurements, "area_mm2": face.Area,
        "perimeter_mm": face.Length, "numerical_area_budget_mm2": area_budget,
        "maximum_kernel_tolerance_mm": tolerance,
    })
    return measurements


def _construct_apertures_and_measure(parameters, apertures):
    geometry = compute_chair_base_aperture_geometry(parameters, apertures)
    try:
        face = _make_aperture_face(geometry)
        return face, _measure_aperture_face(face, geometry)
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairBaseNominalExactGeometryError(
            "aperture-kernel-construction-failed", str(error),
        ) from error


def construct_chair_base_aperture_face(parameters, apertures):
    """Return one checked plan face with explicit circular apertures.

    Input positions use the existing geometric frame. The caller owns
    provenance and the represented plane; this supplies no hole walls,
    placement in a chair, physical fit or production admission.
    """
    face, _measurements = _construct_apertures_and_measure(parameters, apertures)
    return face


def validate_chair_base_aperture_exact_geometry(parameters, apertures):
    """Construct a fresh aperture face and return neutral measurements."""
    _face, measurements = _construct_apertures_and_measure(parameters, apertures)
    return measurements
