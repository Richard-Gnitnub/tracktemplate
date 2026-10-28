"""Inspect the fixed private P outer jaw as two transient native solids.

The spacer and body stay separate. Their finite analytical boundaries
supply every face. No source file, mesh, document or export is consumed or
created. Construction grants no physical-fit, production or rights status.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_p_seat_exact import (
    ChairPSeatExactGeometryError,
    _measure_faces,
    _point_match,
)
from tracktemplate.adapters.freecad.chair_seat_exact import (
    ChairSeatExactGeometryError,
    construct_chair_seat_shape,
)
from tracktemplate.application.chair_research import (
    prepare_chair_p_outer_jaw_research,
)
from tracktemplate.domain.chair_p_outer_jaw import (
    ChairPOuterJawGeometry,
    construct_chair_p_outer_jaw,
)


# Existing numerical/kernel budgets, not railway or physical-fit limits.
NUMERICAL_LENGTH_TOLERANCE_MM = 1.0e-7
KERNEL_TOLERANCE_MM = 1.0e-7


class ChairPOuterJawExactGeometryError(RuntimeError):
    """Recoverable native refusal without document or file mutation."""

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
        raise ChairPOuterJawExactGeometryError(code, message)


def construct_chair_p_outer_jaw_shapes(geometry):
    """Return ordered spacer/body solids after exact boundary reconstruction.

    This composition helper requires an authorised research caller. It
    does not admit a package or grant production use. No Boolean, healing,
    placement, document mutation or tolerance change is performed.
    """
    if not isinstance(geometry, ChairPOuterJawGeometry):
        raise TypeError("geometry must be ChairPOuterJawGeometry")
    try:
        reconstructed = construct_chair_p_outer_jaw(geometry.parameters)
    except (TypeError, ValueError) as error:
        raise ChairPOuterJawExactGeometryError(
            "p-outer-jaw-boundary-invalid", str(error),
        ) from error
    _require(
        reconstructed == geometry,
        "p-outer-jaw-boundary-mismatch",
        "geometry differs from its parameters",
    )
    try:
        return tuple((name, construct_chair_seat_shape(boundary))
                     for name, boundary in geometry.parts)
    except (ChairSeatExactGeometryError, Part.OCCError,
            OverflowError, ValueError) as error:
        raise ChairPOuterJawExactGeometryError(
            "p-outer-jaw-kernel-construction-failed", str(error),
        ) from error


def _measure_part(name, shape, geometry):
    """Measure each complete closed boundary against its analytical part."""
    _require(
        not shape.isNull() and shape.ShapeType == "Solid"
        and shape.isValid() and shape.isClosed()
        and len(shape.Solids) == len(shape.Shells) == 1,
        "invalid-p-outer-jaw-solid", name,
    )
    edges = {
        frozenset((start, end))
        for _, boundary in geometry.faces
        for start, end in zip(boundary, boundary[1:] + boundary[:1])
    }
    topology = (len(geometry.vertices), len(edges), len(geometry.faces))
    _require(
        (len(shape.Vertexes), len(shape.Edges), len(shape.Faces)) == topology,
        "unexpected-p-outer-jaw-topology", name,
    )
    tolerance = shape.getTolerance(1)
    _require(
        math.isfinite(tolerance) and (
            tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
                tolerance, KERNEL_TOLERANCE_MM,
                rel_tol=1.0e-12, abs_tol=0.0,
            )
        ),
        "p-outer-jaw-tolerance-growth", name,
    )
    points = {identity: tuple(float(value) for value in coordinates)
              for identity, *coordinates in geometry.vertices}
    try:
        residuals = _point_match(
            [tuple(vertex.Point) for vertex in shape.Vertexes], points,
        )
        face_measurements = _measure_faces(shape, geometry, points)
    except ChairPSeatExactGeometryError as error:
        raise ChairPOuterJawExactGeometryError(
            error.code.replace("p-seat-", "p-outer-jaw-"),
            "{}: {}".format(name, error.detail),
        ) from error
    box = shape.BoundBox
    bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
    bounds_residual = max(abs(actual - float(expected))
                          for actual, expected in zip(
                              bounds, geometry.bounds_mm,
                          ))
    _require(
        all(math.isfinite(value) for value in bounds)
        and bounds_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
        "p-outer-jaw-bounds-mismatch", name,
    )
    expected_volume = float(geometry.volume_mm3)
    volume_budget = max(
        shape.Area * NUMERICAL_LENGTH_TOLERANCE_MM,
        expected_volume * 1.0e-12,
    )
    volume_residual = abs(shape.Volume - expected_volume)
    _require(
        shape.Volume > 0 and math.isfinite(shape.Volume)
        and math.isfinite(volume_budget) and volume_residual <= volume_budget,
        "p-outer-jaw-volume-mismatch", name,
    )
    return {
        "part_id": name, "solid_count": 1, "shell_count": 1,
        "vertex_count": topology[0], "edge_count": topology[1],
        "face_count": topology[2],
        "face_ids": [identity for identity, _ in geometry.faces],
        "source_face_ids": [identity for identity, _ in geometry.source_faces],
        "valid": True, "closed": True, "bounds_mm": bounds,
        "volume_mm3": shape.Volume, "area_mm2": shape.Area,
        "landmarks_mm": {identity: tuple(float(v) for v in point)
                         for identity, point in geometry.landmarks},
        "maximum_vertex_residual_mm": max(residuals.values()),
        "vertex_residuals_mm": residuals,
        "face_measurements": face_measurements,
        "maximum_bounds_residual_mm": bounds_residual,
        "volume_residual_mm3": volume_residual,
        "numerical_volume_budget_mm3": volume_budget,
        "maximum_kernel_tolerance_mm": tolerance,
    }


def validate_chair_p_outer_jaw_exact_geometry(package, manifest_text):
    """Revalidate a complete private request and inspect both native solids.

    Full-size millimetres and the unchanged chair frame apply. Each call
    constructs and releases its own shapes. No document, persistent
    object, file, source reader or GUI state is created by this operation.
    """
    research = prepare_chair_p_outer_jaw_research(package, manifest_text)
    geometry = research.geometry
    try:
        shapes = construct_chair_p_outer_jaw_shapes(geometry)
        parts = [
            _measure_part(name, shape, boundary)
            for (name, shape), (_, boundary) in zip(shapes, geometry.parts)
        ]
        _require(
            len(parts) == 2 and [part["part_id"] for part in parts]
            == ["spacer", "body"],
            "unexpected-p-outer-jaw-parts", "expected spacer and body",
        )
        bounds = tuple(
            (min if axis < 3 else max)(
                part["bounds_mm"][axis] for part in parts
            )
            for axis in range(6)
        )
        record = package.to_record()
        return {
            "contract_id": "tracktemplate.chair-p-outer-jaw-exact-research.v1",
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
            "solid_count": 2, "shell_count": 2, "parts": parts,
            "source_face_count": sum(len(part["source_face_ids"])
                                     for part in parts),
            "face_count": sum(part["face_count"] for part in parts),
            "valid": True, "closed": True, "bounds_mm": bounds,
            "volume_mm3": sum(part["volume_mm3"] for part in parts),
            "landmarks_mm": {identity: tuple(float(v) for v in point)
                             for identity, point in geometry.landmarks},
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "maximum_kernel_tolerance_mm": max(
                part["maximum_kernel_tolerance_mm"] for part in parts
            ),
            "document_mutation": False, "filesystem_mutation": False,
        }
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairPOuterJawExactGeometryError(
            "p-outer-jaw-kernel-construction-failed", str(error),
        ) from error
