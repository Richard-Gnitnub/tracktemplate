"""Validate one reference-only research seat with transient Part geometry.

No document object, retained solid, mesh or export is produced. This is
an explicit research validation boundary, not production admission.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.application.chair_definition import (
    chair_definition_manifest_signature,
)
from tracktemplate.application.chair_research import (
    prepare_chair_seat_research,
)


# Numerical comparison only, not prototype or model-rail fit tolerances.
# Planar construction uses the kernel's unchanged 1e-7 mm tolerance.
NUMERICAL_LENGTH_TOLERANCE_MM = 1.0e-7
KERNEL_TOLERANCE_MM = 1.0e-7


class ChairSeatExactGeometryError(RuntimeError):
    """Recoverable failure without a document or filesystem mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return a host-neutral failure record."""
        return {
            "code": self.code,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
            "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairSeatExactGeometryError(code, message)


def _make_shape(geometry):
    """Construct the finite analytical boundary; do no healing or Boolean."""
    points = {}
    for name, *coordinates in geometry.vertices:
        values = tuple(float(value) for value in coordinates)
        _require(
            all(math.isfinite(value) for value in values),
            "non-finite-host-coordinate",
            "analytical coordinate cannot be represented by the host",
        )
        points[name] = App.Vector(*values)
    faces = []
    for name, vertex_ids in geometry.faces:
        vertices = [points[vertex_id] for vertex_id in vertex_ids]
        wire = Part.makePolygon(vertices + [vertices[0]])
        _require(
            wire.isClosed() and wire.isValid(),
            "invalid-seat-wire", name,
        )
        face = Part.Face(wire)
        _require(face.isValid(), "invalid-seat-face", name)
        faces.append(face)
    shell = Part.makeShell(faces)
    _require(
        shell.isClosed() and shell.isValid(),
        "invalid-seat-shell", "seat shell must be valid and closed",
    )
    return Part.makeSolid(shell)


def validate_chair_seat_exact_geometry(package, manifest_text):
    """Revalidate research inputs and return neutral solid measurements.

    The caller owns runtime qualification. Canonical inputs use full-size
    millimetres; no scale or manufacturing profile is applied here.
    Every call constructs and disposes its own in-memory shape. No GUI,
    document, persistence or production-output acceptance is implied.
    """
    research = prepare_chair_seat_research(package, manifest_text)
    geometry = research.geometry
    try:
        shape = _make_shape(geometry)
        _require(
            not shape.isNull() and shape.ShapeType == "Solid"
            and shape.isValid() and shape.isClosed()
            and len(shape.Solids) == 1 and len(shape.Shells) == 1,
            "invalid-seat-solid", "expected one valid closed solid",
        )
        _require(
            (len(shape.Vertexes), len(shape.Edges), len(shape.Faces))
            == (12, 21, 11),
            "unexpected-seat-topology", "expected 12 vertices/21 edges/11 faces",
        )
        kernel_tolerance = shape.getTolerance(1)
        _require(
            kernel_tolerance <= KERNEL_TOLERANCE_MM
            or math.isclose(
                kernel_tolerance, KERNEL_TOLERANCE_MM,
                rel_tol=1.0e-12, abs_tol=0.0,
            ),
            "seat-tolerance-growth", "kernel tolerance grew during construction",
        )
        unmatched = [tuple(vertex.Point) for vertex in shape.Vertexes]
        vertex_residuals = {}
        for name, *point in geometry.vertices:
            expected = tuple(float(value) for value in point)
            closest = min(unmatched, key=lambda p: math.dist(p, expected))
            residual = math.dist(closest, expected)
            _require(
                residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
                "seat-landmark-mismatch", name,
            )
            vertex_residuals[name] = residual
            unmatched.remove(closest)
        bounds = shape.BoundBox
        actual_bounds = (
            bounds.XMin, bounds.YMin, bounds.ZMin,
            bounds.XMax, bounds.YMax, bounds.ZMax,
        )
        bound_residual = max(
            abs(actual - float(expected))
            for actual, expected in zip(actual_bounds, geometry.bounds_mm)
        )
        _require(
            bound_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "seat-bounds-mismatch", "solid bounds differ from analytical seat",
        )
        expected_volume = float(geometry.volume_mm3)
        volume_residual = abs(shape.Volume - expected_volume)
        volume_budget = max(
            shape.Area * NUMERICAL_LENGTH_TOLERANCE_MM,
            expected_volume * 1.0e-12,
        )
        _require(
            shape.Volume > 0 and math.isfinite(shape.Volume)
            and math.isfinite(volume_budget)
            and volume_residual <= volume_budget,
            "seat-volume-mismatch", "solid volume differs from analytical seat",
        )
        record = package.to_record()
        return {
            "contract_id": "tracktemplate.chair-seat-exact-research.v1",
            "component_id": record["definition"]["components"][0]["component_id"],
            "package_signature": package.content_signature,
            "manifest_signature": chair_definition_manifest_signature(
                manifest_text
            ),
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "frame_id": record["definition"]["frame"]["frame_id"],
            "length_unit": "mm",
            "length_basis": "full-size",
            "freecad_version": ".".join(App.Version()[:3]),
            "opencascade_version": Part.OCC_VERSION,
            "solid_count": 1,
            "shell_count": 1,
            "vertex_count": len(shape.Vertexes),
            "edge_count": len(shape.Edges),
            "face_count": len(shape.Faces),
            "face_ids": [name for name, _ids in geometry.faces],
            "valid": True,
            "closed": True,
            "bounds_mm": actual_bounds,
            "volume_mm3": shape.Volume,
            "maximum_vertex_residual_mm": max(vertex_residuals.values()),
            "vertex_residuals_mm": vertex_residuals,
            "maximum_bounds_residual_mm": bound_residual,
            "volume_residual_mm3": volume_residual,
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
            "maximum_kernel_tolerance_mm": kernel_tolerance,
            "document_mutation": False,
            "filesystem_mutation": False,
        }
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairSeatExactGeometryError(
            "seat-kernel-construction-failed", str(error)
        ) from error
