"""Transient FreeCAD Part geometry for one verified transition centreline."""

from dataclasses import dataclass
import math
import uuid

import FreeCAD as App
import Part

from tracktemplate.application.transition_derived import (
    transition_derived_contract_signature,
)
from tracktemplate.application.transition_exact import (
    TRANSITION_EXACT_FRAME_ID,
    TRANSITION_EXACT_LENGTH_UNIT,
    transition_exact_result_from_artifact,
)
from tracktemplate.application.transition_state import TransitionStateError


TRANSITION_EXACT_GEOMETRY_CONTRACT_ID = (
    "tracktemplate.freecad.transition-exact-geometry.v1"
)
TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME = (
    "TrackTemplateTransitionExactGeometry"
)
TRANSITION_EXACT_GEOMETRY_OBJECT_NAME = "TransitionExactCentreline"
TRANSITION_EXACT_GEOMETRY_NUMERICAL_TOLERANCE_MM = 1.0e-8
_SIGNATURE_PREFIX = "sha256:"
_LOWER_HEXADECIMAL = "0123456789abcdef"
_TEMPORARY_DOCUMENT_NAME_ATTEMPTS = 16

__all__ = (
    "TRANSITION_EXACT_GEOMETRY_CONTRACT_ID",
    "TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME",
    "TRANSITION_EXACT_GEOMETRY_NUMERICAL_TOLERANCE_MM",
    "TRANSITION_EXACT_GEOMETRY_OBJECT_NAME",
    "TransitionExactGeometryError",
    "TransitionExactGeometryReceipt",
    "build_transition_exact_geometry",
)


class TransitionExactGeometryError(RuntimeError):
    """Structured failure from transient FreeCAD exact construction."""

    def __init__(
        self,
        code,
        message,
        source_code="",
        cleanup_complete=True,
        recoverable=True,
    ):
        self.code = str(code)
        self.detail = str(message)
        self.source_code = str(source_code)
        self.cleanup_complete = bool(cleanup_complete)
        self.recoverable = bool(recoverable)
        super().__init__("{}: {}".format(self.code, self.detail))

    def diagnostic(self):
        """Return an adapter-neutral, JSON-compatible diagnostic."""
        return {
            "cleanup_complete": self.cleanup_complete,
            "code": self.code,
            "message": self.detail,
            "recoverable": self.recoverable,
            "source_code": self.source_code,
        }


def _require_signature(path, value):
    if (
        not isinstance(value, str)
        or not value.startswith(_SIGNATURE_PREFIX)
        or len(value) != len(_SIGNATURE_PREFIX) + 64
        or any(
            character not in _LOWER_HEXADECIMAL
            for character in value[len(_SIGNATURE_PREFIX):]
        )
    ):
        raise ValueError(
            "{} must be sha256 followed by 64 lower-case hexadecimal "
            "characters".format(path)
        )
    return value


def _finite_float(path, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a finite number".format(path))
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("{} must be a finite number".format(path))
    return value


@dataclass(frozen=True)
class TransitionExactGeometryReceipt:
    """Neutral measurements from one disposed FreeCAD exact shape."""

    contract_id: str
    domain_id: str
    frame_id: str
    length_unit: str
    source_signature: str
    exact_artifact_signature: str
    exact_result_signature: str
    freecad_version: str
    opencascade_version: str
    shape_type: str
    vertex_count: int
    edge_count: int
    closed: bool
    polyline_length_mm: float
    minimum_x_mm: float
    minimum_y_mm: float
    maximum_x_mm: float
    maximum_y_mm: float
    maximum_abs_z_mm: float
    geometry_signature: str = ""

    def __post_init__(self):
        if self.contract_id != TRANSITION_EXACT_GEOMETRY_CONTRACT_ID:
            raise ValueError("unsupported exact-geometry contract identifier")
        for name in (
            "domain_id",
            "freecad_version",
            "opencascade_version",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("{} must be non-empty text".format(name))
        if self.frame_id != TRANSITION_EXACT_FRAME_ID:
            raise ValueError("unsupported exact-geometry coordinate frame")
        if self.length_unit != TRANSITION_EXACT_LENGTH_UNIT:
            raise ValueError("unsupported exact-geometry length unit")
        for name in (
            "source_signature",
            "exact_artifact_signature",
            "exact_result_signature",
        ):
            _require_signature(name, getattr(self, name))
        if self.shape_type not in ("Vertex", "Wire"):
            raise ValueError("shape_type must be Vertex or Wire")
        if not isinstance(self.closed, bool) or self.closed:
            raise ValueError("transition exact geometry must be open")
        for name in ("vertex_count", "edge_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("{} must be an integer".format(name))
        if self.shape_type == "Vertex":
            if self.vertex_count != 1 or self.edge_count != 0:
                raise ValueError("a point result must contain one vertex")
        elif self.vertex_count < 2 or self.edge_count != self.vertex_count - 1:
            raise ValueError(
                "an open wire must contain n vertices and n-1 edges"
            )
        for name in (
            "polyline_length_mm",
            "minimum_x_mm",
            "minimum_y_mm",
            "maximum_x_mm",
            "maximum_y_mm",
            "maximum_abs_z_mm",
        ):
            object.__setattr__(
                self,
                name,
                _finite_float(name, getattr(self, name)),
            )
        if self.polyline_length_mm < 0.0 or self.maximum_abs_z_mm < 0.0:
            raise ValueError(
                "length and planarity residual must not be negative"
            )
        if (
            self.minimum_x_mm > self.maximum_x_mm
            or self.minimum_y_mm > self.maximum_y_mm
        ):
            raise ValueError("exact-geometry bounds are inverted")
        signature_inputs = {
            "contract_id": self.contract_id,
            "domain_id": self.domain_id,
            "exact_artifact_signature": self.exact_artifact_signature,
            "exact_result_signature": self.exact_result_signature,
            "frame_id": self.frame_id,
            "freecad_version": self.freecad_version,
            "length_unit": self.length_unit,
            "measurements": {
                "closed": self.closed,
                "edge_count": self.edge_count,
                "maximum_abs_z_mm": self.maximum_abs_z_mm,
                "maximum_x_mm": self.maximum_x_mm,
                "maximum_y_mm": self.maximum_y_mm,
                "minimum_x_mm": self.minimum_x_mm,
                "minimum_y_mm": self.minimum_y_mm,
                "polyline_length_mm": self.polyline_length_mm,
                "shape_type": self.shape_type,
                "vertex_count": self.vertex_count,
            },
            "numerical_tolerance_mm": (
                TRANSITION_EXACT_GEOMETRY_NUMERICAL_TOLERANCE_MM
            ),
            "opencascade_version": self.opencascade_version,
            "source_signature": self.source_signature,
        }
        expected_signature = transition_derived_contract_signature(
            TRANSITION_EXACT_GEOMETRY_CONTRACT_ID,
            signature_inputs,
        )
        if self.geometry_signature:
            _require_signature("geometry_signature", self.geometry_signature)
            if self.geometry_signature != expected_signature:
                raise ValueError(
                    "geometry_signature does not match the exact receipt"
                )
        else:
            object.__setattr__(
                self,
                "geometry_signature",
                expected_signature,
            )


def _geometry_error(code, message, source_code=""):
    return TransitionExactGeometryError(
        code,
        message,
        source_code=source_code,
    )


def _check_cancellation(cancellation_requested):
    if cancellation_requested is None:
        return
    try:
        cancelled = bool(cancellation_requested())
    except Exception as error:
        raise _geometry_error(
            "exact-geometry-cancellation-check-failed",
            str(error),
        ) from error
    if cancelled:
        raise _geometry_error(
            "exact-geometry-cancelled",
            "transient exact construction was cancelled",
        )


def _make_transition_shape(centreline):
    vectors = [
        App.Vector(point.x_mm, point.y_mm, 0.0)
        for point in centreline.points
    ]
    if len(vectors) == 1:
        return Part.Vertex(vectors[0])
    return Part.makePolygon(vectors)


def _close_enough(observed, expected):
    return math.isclose(
        float(observed),
        float(expected),
        rel_tol=0.0,
        abs_tol=TRANSITION_EXACT_GEOMETRY_NUMERICAL_TOLERANCE_MM,
    )


def _ordered_vertices(shape):
    if str(shape.ShapeType) == "Vertex":
        return tuple(shape.Vertexes)
    try:
        return tuple(shape.OrderedVertexes)
    except AttributeError:
        return tuple(Part.Wire(shape.Edges).OrderedVertexes)


def _shape_measurements(shape, centreline):
    if shape.isNull():
        raise _geometry_error(
            "invalid-exact-geometry",
            "FreeCAD returned a null exact shape",
        )
    if not shape.isValid():
        raise _geometry_error(
            "invalid-exact-geometry",
            "FreeCAD returned an invalid exact shape",
        )

    point_count = len(centreline.points)
    expected_shape_type = "Vertex" if point_count == 1 else "Wire"
    shape_type = str(shape.ShapeType)
    if shape_type != expected_shape_type:
        raise _geometry_error(
            "invalid-exact-topology",
            "expected {}, observed {}".format(
                expected_shape_type,
                shape_type,
            ),
        )
    closed = bool(shape.isClosed()) if shape_type == "Wire" else False
    if closed:
        raise _geometry_error(
            "invalid-exact-topology",
            "the transition centreline wire must remain open",
        )

    vertices = _ordered_vertices(shape)
    edges = tuple(shape.Edges)
    expected_edge_count = max(0, point_count - 1)
    if len(vertices) != point_count or len(edges) != expected_edge_count:
        raise _geometry_error(
            "invalid-exact-topology",
            "the exact shape does not preserve centreline point topology",
        )
    for observed, expected in zip(vertices, centreline.points):
        point = observed.Point
        if not all(
            (
                _close_enough(point.x, expected.x_mm),
                _close_enough(point.y, expected.y_mm),
                _close_enough(point.z, 0.0),
            )
        ):
            raise _geometry_error(
                "invalid-exact-geometry",
                "FreeCAD changed an ordered centreline coordinate",
            )

    expected_length_mm = sum(
        math.hypot(
            current.x_mm - previous.x_mm,
            current.y_mm - previous.y_mm,
        )
        for previous, current in zip(
            centreline.points,
            centreline.points[1:],
        )
    )
    polyline_length_mm = float(shape.Length)
    if not _close_enough(polyline_length_mm, expected_length_mm):
        raise _geometry_error(
            "invalid-exact-geometry",
            "FreeCAD changed the exact-centreline polyline length",
        )

    expected_minimum_x_mm = min(point.x_mm for point in centreline.points)
    expected_minimum_y_mm = min(point.y_mm for point in centreline.points)
    expected_maximum_x_mm = max(point.x_mm for point in centreline.points)
    expected_maximum_y_mm = max(point.y_mm for point in centreline.points)
    bounds = shape.BoundBox
    observed_bounds = (
        float(bounds.XMin),
        float(bounds.YMin),
        float(bounds.XMax),
        float(bounds.YMax),
    )
    expected_bounds = (
        expected_minimum_x_mm,
        expected_minimum_y_mm,
        expected_maximum_x_mm,
        expected_maximum_y_mm,
    )
    if not all(
        _close_enough(observed, expected)
        for observed, expected in zip(observed_bounds, expected_bounds)
    ):
        raise _geometry_error(
            "invalid-exact-geometry",
            "FreeCAD changed the exact-centreline bounds",
        )
    maximum_abs_z_mm = max(abs(float(bounds.ZMin)), abs(float(bounds.ZMax)))
    if maximum_abs_z_mm > TRANSITION_EXACT_GEOMETRY_NUMERICAL_TOLERANCE_MM:
        raise _geometry_error(
            "invalid-exact-geometry",
            "the exact-centreline shape is not planar in canonical XY",
        )
    return {
        "closed": closed,
        "edge_count": len(edges),
        "maximum_abs_z_mm": maximum_abs_z_mm,
        "maximum_x_mm": observed_bounds[2],
        "maximum_y_mm": observed_bounds[3],
        "minimum_x_mm": observed_bounds[0],
        "minimum_y_mm": observed_bounds[1],
        "polyline_length_mm": polyline_length_mm,
        "shape_type": shape_type,
        "vertex_count": len(vertices),
    }


def _runtime_version():
    freecad_version = ".".join(str(item) for item in App.Version()[:3])
    opencascade_version = str(
        getattr(
            Part,
            "OCC_VERSION_STRING",
            getattr(Part, "OCC_VERSION", "unknown"),
        )
    )
    if not freecad_version or opencascade_version == "unknown":
        raise _geometry_error(
            "unsupported-exact-runtime",
            "FreeCAD and OpenCASCADE versions must be identifiable",
        )
    return freecad_version, opencascade_version


def _receipt(result, measurements):
    freecad_version, opencascade_version = _runtime_version()
    return TransitionExactGeometryReceipt(
        contract_id=TRANSITION_EXACT_GEOMETRY_CONTRACT_ID,
        domain_id=result.centreline.domain_id,
        frame_id=result.centreline.frame_id,
        length_unit=result.centreline.length_unit,
        source_signature=result.source_signature,
        exact_artifact_signature=result.artifact_signature,
        exact_result_signature=result.result_signature,
        freecad_version=freecad_version,
        opencascade_version=opencascade_version,
        **measurements,
    )


def _same_document_registry(observed, expected):
    return (
        set(observed) == set(expected)
        and all(
            observed.get(name) is document
            for name, document in expected.items()
        )
    )


def _allocate_temporary_document_name(previous_documents):
    if not _same_document_registry(
        dict(App.listDocuments()),
        previous_documents,
    ):
        raise _geometry_error(
            "exact-geometry-document-ownership-ambiguous",
            "the FreeCAD document registry changed before temporary "
            "document creation",
        )
    for _attempt in range(_TEMPORARY_DOCUMENT_NAME_ATTEMPTS):
        document_name = "{}_{}".format(
            TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME,
            uuid.uuid4().hex,
        )
        if document_name not in previous_documents:
            return document_name
    raise _geometry_error(
        "exact-geometry-document-ownership-ambiguous",
        "a unique temporary FreeCAD document name could not be allocated",
    )


def _request_temporary_document(document_name):
    return App.newDocument(
        document_name,
        "Track Template transient exact geometry",
        True,
        True,
    )


def _create_owned_temporary_document(previous_documents):
    document_name = _allocate_temporary_document_name(previous_documents)
    document = _request_temporary_document(document_name)
    observed_documents = dict(App.listDocuments())
    expected_names = set(previous_documents) | {document_name}
    ownership_established = (
        document is not None
        and str(document.Name) == document_name
        and set(observed_documents) == expected_names
        and observed_documents.get(document_name) is document
        and all(
            observed_documents.get(name) is previous_document
            for name, previous_document in previous_documents.items()
        )
    )
    if not ownership_established:
        raise _geometry_error(
            "exact-geometry-document-ownership-ambiguous",
            "FreeCAD did not return exactly one newly created temporary "
            "document owned by this invocation",
        )
    return document_name, document


def _cleanup_temporary_document(
    document,
    document_name,
    previous_documents,
    previous_active,
    previous_name,
):
    errors = []
    if document is not None:
        try:
            registered = App.listDocuments().get(document_name)
            if registered is document:
                App.closeDocument(document_name)
            else:
                errors.append(
                    "temporary document ownership could not be confirmed "
                    "during cleanup"
                )
            if App.listDocuments().get(document_name) is document:
                errors.append("temporary document remained open")
        except Exception as error:
            errors.append("temporary document close failed: {}".format(error))

    observed_documents = dict(App.listDocuments())
    if not _same_document_registry(
        observed_documents,
        previous_documents,
    ):
        errors.append(
            "the pre-operation document registry was not restored"
        )
    try:
        if previous_active is None:
            if App.ActiveDocument is not None:
                App.setActiveDocument("")
            if App.ActiveDocument is not None:
                errors.append(
                    "the prior empty active-document state was not restored"
                )
        else:
            registered = observed_documents.get(previous_name)
            if registered is not previous_active:
                errors.append(
                    "the prior active document is no longer registered"
                )
            else:
                App.setActiveDocument(previous_name)
                if App.ActiveDocument is not previous_active:
                    errors.append("the prior active document was not restored")
    except Exception as error:
        errors.append("active-document restoration failed: {}".format(error))
    if errors:
        raise TransitionExactGeometryError(
            "exact-geometry-cleanup-failed",
            "; ".join(errors),
            cleanup_complete=False,
            recoverable=False,
        )


def build_transition_exact_geometry(
    artifact,
    cancellation_requested=None,
):
    """Build, verify and dispose one temporary FreeCAD exact shape.

    The supplied artifact must already be current for its caller-owned state
    and request. This operation verifies artifact integrity, creates no file,
    returns no ``Part.Shape`` and always attempts to restore application state.
    """
    if cancellation_requested is not None and not callable(
        cancellation_requested
    ):
        raise TypeError("cancellation_requested must be callable or None")
    try:
        result = transition_exact_result_from_artifact(artifact)
    except TransitionStateError as error:
        raise _geometry_error(
            "invalid-exact-artifact",
            str(error),
            source_code=error.code,
        ) from error

    previous_active = App.ActiveDocument
    previous_documents = dict(App.listDocuments())
    previous_name = (
        str(previous_active.Name) if previous_active is not None else ""
    )
    document = None
    document_name = ""
    receipt = None
    operation_error = None
    cleanup_error = None
    try:
        _check_cancellation(cancellation_requested)
        document_name, document = _create_owned_temporary_document(
            previous_documents,
        )
        if not bool(document.Temporary) or str(document.FileName):
            raise _geometry_error(
                "invalid-exact-geometry-document",
                "the owned exact-geometry document must be temporary and "
                "unsaved",
            )
        obj = document.addObject(
            "Part::Feature",
            TRANSITION_EXACT_GEOMETRY_OBJECT_NAME,
        )
        _check_cancellation(cancellation_requested)
        obj.Shape = _make_transition_shape(result.centreline)
        document.recompute()
        measurements = _shape_measurements(obj.Shape, result.centreline)
        _check_cancellation(cancellation_requested)
        receipt = _receipt(result, measurements)
    except Exception as error:
        operation_error = error
    finally:
        try:
            _cleanup_temporary_document(
                document,
                document_name,
                previous_documents,
                previous_active,
                previous_name,
            )
        except TransitionExactGeometryError as error:
            cleanup_error = error

    if cleanup_error is not None:
        if operation_error is not None:
            raise cleanup_error from operation_error
        raise cleanup_error
    if operation_error is not None:
        if isinstance(operation_error, TransitionExactGeometryError):
            raise operation_error
        raise _geometry_error(
            "exact-geometry-build-failed",
            str(operation_error),
        ) from operation_error
    return receipt
