"""Validate a reference-only key with disposable native Part geometry.

No GUI, document object, retained solid or export is produced. The
accepted seat's numerical comparison limits apply unchanged.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_seat_exact import (
    KERNEL_TOLERANCE_MM,
    NUMERICAL_LENGTH_TOLERANCE_MM,
)
from tracktemplate.application.chair_research import prepare_chair_key_research


class ChairKeyExactGeometryError(RuntimeError):
    """Recoverable failure without document or filesystem mutation."""

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
        raise ChairKeyExactGeometryError(code, message)


def _make_shape(geometry):
    """Construct declared planar faces without Boolean work or healing."""
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
            wire.isClosed() and wire.isValid(), "invalid-key-wire", name
        )
        face = Part.Face(wire)
        _require(face.isValid(), "invalid-key-face", name)
        faces.append(face)
    shell = Part.makeShell(faces)
    _require(
        shell.isClosed() and shell.isValid(),
        "invalid-key-shell", "key shell must be valid and closed",
    )
    return Part.makeSolid(shell)


def validate_chair_key_exact_geometry(package, manifest_text):
    """Revalidate canonical research data and return neutral measurements.

    Each call constructs a fresh shape in full-size millimetres, then
    disposes it. Numerical limits do not establish physical rail fit,
    prototype accuracy, manufacturing tolerance or package acceptance.
    """
    research = prepare_chair_key_research(package, manifest_text)
    geometry = research.geometry
    try:
        shape = _make_shape(geometry)
        _require(
            not shape.isNull() and shape.ShapeType == "Solid"
            and shape.isValid() and shape.isClosed()
            and len(shape.Solids) == 1 and len(shape.Shells) == 1,
            "invalid-key-solid", "expected one valid closed solid",
        )
        _require(
            (len(shape.Vertexes), len(shape.Edges), len(shape.Faces))
            == (20, 36, 18),
            "unexpected-key-topology",
            "expected 20 vertices/36 edges/18 faces",
        )
        tolerance = shape.getTolerance(1)
        _require(
            tolerance <= KERNEL_TOLERANCE_MM
            or math.isclose(
                tolerance, KERNEL_TOLERANCE_MM,
                rel_tol=1.0e-12, abs_tol=0.0,
            ),
            "key-tolerance-growth", "kernel tolerance grew during construction",
        )
        unmatched = [tuple(vertex.Point) for vertex in shape.Vertexes]
        residuals = {}
        for name, *point in geometry.vertices:
            expected = tuple(float(value) for value in point)
            closest = min(unmatched, key=lambda p: math.dist(p, expected))
            residual = math.dist(closest, expected)
            _require(
                residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
                "key-landmark-mismatch", name,
            )
            residuals[name] = residual
            unmatched.remove(closest)
        box = shape.BoundBox
        bounds = (
            box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax
        )
        bound_residual = max(
            abs(actual - float(expected))
            for actual, expected in zip(bounds, geometry.bounds_mm)
        )
        _require(
            bound_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "key-bounds-mismatch", "solid bounds differ from analytical key",
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
            "key-volume-mismatch", "solid volume differs from analytical key",
        )
        return {
            "contract_id": "tracktemplate.chair-key-exact-research.v1",
            "component_id": research.component_id,
            "package_signature": package.content_signature,
            "manifest_signature": research.manifest_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "frame_id": package.to_record()["definition"]["frame"]["frame_id"],
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
            "bounds_mm": bounds,
            "volume_mm3": shape.Volume,
            "maximum_vertex_residual_mm": max(residuals.values()),
            "vertex_residuals_mm": residuals,
            "maximum_bounds_residual_mm": bound_residual,
            "volume_residual_mm3": volume_residual,
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
            "maximum_kernel_tolerance_mm": tolerance,
            "document_mutation": False,
            "filesystem_mutation": False,
        }
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairKeyExactGeometryError(
            "key-kernel-construction-failed", str(error)
        ) from error
