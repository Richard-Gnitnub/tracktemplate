"""Inspect one private P slide-seat as a transient full-size native solid.

The analytical constituent supplies its finite faceted boundary. This
adapter imports no source mesh and changes no document or file. Successful
construction supplies no physical-fit, production or rights acceptance.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_seat_exact import (
    ChairSeatExactGeometryError,
    construct_chair_seat_shape,
)
from tracktemplate.application.chair_research import (
    prepare_chair_p_seat_research,
)
from tracktemplate.domain.chair_p_seat import (
    ChairPSeatGeometry,
    construct_chair_p_seat,
)


# Existing numerical/kernel budgets, not railway or physical-fit limits.
NUMERICAL_LENGTH_TOLERANCE_MM = 1.0e-7
KERNEL_TOLERANCE_MM = 1.0e-7


class ChairPSeatExactGeometryError(RuntimeError):
    """Recoverable native refusal without document or filesystem mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return the neutral failure boundary."""
        return {
            "code": self.code, "message": self.detail,
            "recoverable": True, "document_mutation": False,
            "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairPSeatExactGeometryError(code, message)


def _make_shape(geometry):
    """Reuse the qualified polygon/face/shell/solid chain without healing."""
    return construct_chair_seat_shape(geometry)


def construct_chair_p_seat_shape(geometry):
    """Build derived Part geometry for an already authorised research caller.

    Reconstruct the finite domain boundary before host work. A caller must
    still validate its complete package and manifest; this composition
    helper does not admit caller-made geometry or grant production use.
    """
    if not isinstance(geometry, ChairPSeatGeometry):
        raise TypeError("geometry must be ChairPSeatGeometry")
    _require(
        construct_chair_p_seat(geometry.parameters) == geometry,
        "p-seat-boundary-mismatch", "geometry differs from its parameters",
    )
    try:
        return _make_shape(geometry)
    except (ChairSeatExactGeometryError, Part.OCCError,
            OverflowError, ValueError) as error:
        raise ChairPSeatExactGeometryError(
            "p-seat-kernel-construction-failed", str(error),
        ) from error


def _point_match(actual, expected):
    """Require complete one-to-one vertex coverage within the fixed budget."""
    unmatched = list(actual)
    residuals = {}
    for name, point in expected.items():
        _require(bool(unmatched), "p-seat-vertex-count", name)
        nearest = min(unmatched, key=lambda value: math.dist(value, point))
        residual = math.dist(nearest, point)
        _require(
            residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "p-seat-vertex-mismatch", name,
        )
        residuals[name] = residual
        unmatched.remove(nearest)
    _require(not unmatched, "p-seat-vertex-count", "unexpected native vertex")
    return residuals


def _measure_faces(shape, geometry, points):
    """Map every native plane to one complete semantic polygon boundary."""
    unmatched = list(shape.Faces)
    result = []
    for name, names in geometry.faces:
        expected = {identity: points[identity] for identity in names}
        matches = [face for face in unmatched if (
            len(face.Vertexes) == len(names)
            and all(any(math.dist(tuple(vertex.Point), point)
                        <= NUMERICAL_LENGTH_TOLERANCE_MM
                        for point in expected.values())
                    for vertex in face.Vertexes)
        )]
        _require(len(matches) == 1, "p-seat-face-mismatch", name)
        face = matches[0]
        unmatched.remove(face)
        _point_match([tuple(v.Point) for v in face.Vertexes], expected)
        _require(
            face.isValid() and isinstance(face.Surface, Part.Plane)
            and len(face.Wires) == 1 and len(face.Edges) == len(names),
            "p-seat-face-type", name,
        )
        vectors = [App.Vector(*points[identity]) for identity in names]
        normal = App.Vector(0, 0, 0)
        for first, second in zip(vectors, vectors[1:] + vectors[:1]):
            normal += first.cross(second)
        expected_area = normal.Length / 2
        _require(
            expected_area > 0 and math.isfinite(expected_area),
            "p-seat-face-area", name,
        )
        normal.normalize()
        native_normal = face.normalAt(0, 0)
        normal_residual = (native_normal - normal).Length
        _require(
            normal_residual <= 1.0e-12,
            "p-seat-face-orientation", name,
        )
        plane_residual = max(
            abs((vector - vectors[0]).dot(native_normal))
            for vector in vectors
        )
        _require(
            plane_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "p-seat-face-plane", name,
        )
        area_budget = max(
            face.Length * NUMERICAL_LENGTH_TOLERANCE_MM,
            expected_area * 1.0e-12,
        )
        area_residual = abs(face.Area - expected_area)
        _require(
            math.isfinite(face.Area) and face.Area > 0
            and math.isfinite(area_budget) and area_residual <= area_budget,
            "p-seat-face-area", name,
        )
        result.append({
            "face_id": name, "vertex_count": len(names),
            "area_mm2": face.Area, "area_residual_mm2": area_residual,
            "numerical_area_budget_mm2": area_budget,
            "plane_residual_mm": plane_residual,
            "normal_residual": normal_residual,
        })
    _require(not unmatched, "p-seat-face-count", "unexpected native face")
    return result


def validate_chair_p_seat_exact_geometry(package, manifest_text):
    """Revalidate the complete private request and inspect a transient solid.

    Full-size millimetres and the unchanged chair frame apply. Every call
    constructs and releases its own shape. No document, persistent object,
    file, export, source reader or GUI state is created by this operation.
    """
    research = prepare_chair_p_seat_research(package, manifest_text)
    geometry = research.geometry
    try:
        shape = construct_chair_p_seat_shape(geometry)
        _require(
            not shape.isNull() and shape.ShapeType == "Solid"
            and shape.isValid() and shape.isClosed()
            and len(shape.Solids) == len(shape.Shells) == 1,
            "invalid-p-seat-solid", "expected one valid closed solid",
        )
        _require(
            (len(shape.Vertexes), len(shape.Edges), len(shape.Faces))
            == (62, 93, 33),
            "unexpected-p-seat-topology",
            "expected 62 vertices/93 edges/33 faces",
        )
        tolerance = shape.getTolerance(1)
        _require(
            tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
                tolerance, KERNEL_TOLERANCE_MM,
                rel_tol=1.0e-12, abs_tol=0.0,
            ),
            "p-seat-tolerance-growth", "native tolerance grew",
        )
        points = {name: tuple(float(value) for value in coordinates)
                  for name, *coordinates in geometry.vertices}
        residuals = _point_match(
            [tuple(vertex.Point) for vertex in shape.Vertexes], points,
        )
        face_measurements = _measure_faces(shape, geometry, points)
        box = shape.BoundBox
        bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
        bounds_residual = max(abs(actual - float(expected))
                              for actual, expected in zip(
                                  bounds, geometry.bounds_mm,
                              ))
        _require(
            bounds_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "p-seat-bounds-mismatch", "native bounds differ",
        )
        expected_volume = float(geometry.volume_mm3)
        volume_budget = max(
            shape.Area * NUMERICAL_LENGTH_TOLERANCE_MM,
            expected_volume * 1.0e-12,
        )
        volume_residual = abs(shape.Volume - expected_volume)
        _require(
            shape.Volume > 0 and math.isfinite(shape.Volume)
            and math.isfinite(volume_budget)
            and volume_residual <= volume_budget,
            "p-seat-volume-mismatch", "native volume differs",
        )
        record = package.to_record()
        return {
            "contract_id": "tracktemplate.chair-p-seat-exact-research.v1",
            "component_id": research.component_id,
            "procedure_id": research.procedure_id,
            "package_signature": package.content_signature,
            "manifest_signature": research.manifest_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "frame_id": record["definition"]["frame"]["frame_id"],
            "length_unit": "mm", "length_basis": "full-size",
            "freecad_version": ".".join(App.Version()[:3]),
            "opencascade_version": Part.OCC_VERSION,
            "solid_count": 1, "shell_count": 1,
            "vertex_count": 62, "edge_count": 93, "face_count": 33,
            "face_ids": [name for name, _names in geometry.faces],
            "valid": True, "closed": True, "bounds_mm": bounds,
            "volume_mm3": shape.Volume, "area_mm2": shape.Area,
            "landmarks_mm": {name: tuple(float(v) for v in point)
                             for name, point in geometry.landmarks},
            "maximum_vertex_residual_mm": max(residuals.values()),
            "vertex_residuals_mm": residuals,
            "face_measurements": face_measurements,
            "maximum_bounds_residual_mm": bounds_residual,
            "volume_residual_mm3": volume_residual,
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
            "maximum_kernel_tolerance_mm": tolerance,
            "document_mutation": False, "filesystem_mutation": False,
        }
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairPSeatExactGeometryError(
            "p-seat-kernel-construction-failed", str(error),
        ) from error
