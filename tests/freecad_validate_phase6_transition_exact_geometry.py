#!/usr/bin/env python3
"""Validate disposable transition exact geometry in qualified FreeCAD."""

from dataclasses import replace
import math
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import (  # noqa: E402
    transition_exact as adapter,
)


EDITABLE_DOCUMENT_NAME = "Phase6TransitionExactGeometryEditable"


def _state(transition_length_mm=300.0):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase6:exact-geometry",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 6 transient exact geometry",
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _artifact(transition_length_mm=300.0):
    return api.regenerate_transition_exact(
        api.TransitionDerivedCache(),
        _state(transition_length_mm),
        api.TransitionExactSpecification(0.05, 64),
    )


def _property_snapshot(container):
    names = tuple(getattr(container, "PropertiesList", ()))
    return tuple(
        (name, repr(getattr(container, name)))
        for name in names
    )


def _application_snapshot():
    return (
        App.ActiveDocument,
        tuple(
            (
                name,
                document,
                str(document.Label),
                str(document.FileName),
                bool(document.Temporary),
                int(document.UndoCount),
                int(document.RedoCount),
                tuple(
                    (
                        obj,
                        str(obj.Name),
                        str(obj.TypeId),
                        tuple(obj.PropertiesList),
                        _property_snapshot(obj),
                    )
                    for obj in document.Objects
                ),
            )
            for name, document in sorted(App.listDocuments().items())
        ),
    )


def _new_editable_document():
    document = App.newDocument(EDITABLE_DOCUMENT_NAME)
    document.UndoMode = 1
    document.openTransaction("Create operator-owned baseline")
    obj = document.addObject("App::FeaturePython", "OperatorOwnedObject")
    obj.addProperty("App::PropertyString", "OperatorData")
    obj.OperatorData = "must remain unchanged"
    obj.Label = "Operator-owned baseline"
    document.commitTransaction()
    document.recompute()
    assert App.ActiveDocument is document
    return document, obj


def _new_colliding_temporary_document():
    document = App.newDocument(
        adapter.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME,
        "Pre-existing operator-owned temporary document",
        True,
        True,
    )
    obj = document.addObject("App::FeaturePython", "CollidingOwner")
    obj.addProperty("App::PropertyString", "OperatorData")
    obj.OperatorData = "pre-existing collision must remain unchanged"
    obj.Label = "Pre-existing colliding object"
    document.recompute()
    assert str(document.Name) == (
        adapter.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME
    )
    assert bool(document.Temporary) is True
    return document, obj


def _expect_geometry_error(action, code):
    try:
        action()
    except adapter.TransitionExactGeometryError as error:
        assert error.code == code, error
        assert error.cleanup_complete is True, error.diagnostic()
        assert set(error.diagnostic()) == {
            "cleanup_complete",
            "code",
            "message",
            "recoverable",
            "source_code",
        }
        return error
    raise AssertionError(
        "Expected TransitionExactGeometryError {!r}".format(code)
    )


def _new_documents(previous_documents):
    return tuple(
        document
        for name, document in App.listDocuments().items()
        if name not in previous_documents
    )


def _validate_ambiguous_ownership(document, collision, artifact):
    App.setActiveDocument(str(document.Name))
    before = _application_snapshot()
    missing = object()
    original_request = getattr(
        adapter,
        "_request_temporary_document",
        missing,
    )

    def return_preexisting_document(*_args, **_kwargs):
        return collision

    adapter._request_temporary_document = return_preexisting_document
    try:
        error = _expect_geometry_error(
            lambda: adapter.build_transition_exact_geometry(artifact),
            "exact-geometry-document-ownership-ambiguous",
        )
        assert "newly created" in error.detail
    finally:
        if original_request is missing:
            del adapter._request_temporary_document
        else:
            adapter._request_temporary_document = original_request
    assert _application_snapshot() == before


def _validate_success_and_determinism(document, artifact):
    App.setActiveDocument(str(document.Name))
    before = _application_snapshot()
    previous_documents = dict(App.listDocuments())
    observations = []

    def observe_without_cancelling():
        temporary = _new_documents(previous_documents)
        observations.append(
            tuple(
                (
                    str(candidate.Name),
                    str(candidate.Label),
                    str(candidate.FileName),
                    bool(candidate.Temporary),
                    tuple(
                        (
                            str(item.Name),
                            str(item.TypeId),
                            str(item.Shape.ShapeType)
                            if "Shape" in item.PropertiesList
                            and not item.Shape.isNull()
                            else "Null",
                        )
                        for item in candidate.Objects
                    ),
                )
                for candidate in temporary
            )
        )
        return False

    receipt = adapter.build_transition_exact_geometry(
        artifact,
        cancellation_requested=observe_without_cancelling,
    )
    assert len(observations) == 3
    assert observations[0] == ()
    assert len(observations[1]) == 1
    temporary_name = observations[1][0][0]
    assert temporary_name.startswith(
        adapter.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME + "_"
    )
    assert temporary_name not in previous_documents
    assert observations[1][0][1] == (
        "Track Template transient exact geometry"
    )
    assert observations[1][0][2] == ""
    assert observations[1][0][3] is True
    assert observations[1][0][4] == (
        (
            adapter.TRANSITION_EXACT_GEOMETRY_OBJECT_NAME,
            "Part::Feature",
            "Null",
        ),
    )
    assert observations[2][0][4][0][2] == "Wire"
    assert _application_snapshot() == before

    result = api.transition_exact_result_from_artifact(artifact)
    centreline = result.centreline
    assert receipt.contract_id == (
        adapter.TRANSITION_EXACT_GEOMETRY_CONTRACT_ID
    )
    assert receipt.domain_id == centreline.domain_id
    assert receipt.frame_id == centreline.frame_id
    assert receipt.length_unit == "mm"
    assert receipt.source_signature == result.source_signature
    assert receipt.exact_artifact_signature == result.artifact_signature
    assert receipt.exact_result_signature == result.result_signature
    assert receipt.shape_type == "Wire"
    assert receipt.vertex_count == len(centreline.points)
    assert receipt.edge_count == len(centreline.points) - 1
    assert receipt.closed is False
    assert receipt.maximum_abs_z_mm == 0.0
    assert receipt.geometry_signature.startswith("sha256:")
    assert receipt.freecad_version in {"1.1.1", "1.1.3"}
    assert receipt.opencascade_version.startswith("7.8.1")
    assert receipt.polyline_length_mm < (
        centreline.points[-1].station_mm
    )
    assert math.isclose(
        receipt.minimum_x_mm,
        min(point.x_mm for point in centreline.points),
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        receipt.maximum_y_mm,
        max(point.y_mm for point in centreline.points),
        abs_tol=1.0e-12,
    )
    assert not hasattr(receipt, "shape")
    try:
        replace(
            receipt,
            maximum_x_mm=receipt.maximum_x_mm + 1.0,
        )
    except ValueError as error:
        assert "geometry_signature" in str(error)
    else:
        raise AssertionError("Expected inconsistent receipt rejection")

    repeated = adapter.build_transition_exact_geometry(artifact)
    assert repeated == receipt
    changed = adapter.build_transition_exact_geometry(_artifact(260.0))
    assert changed.exact_result_signature != receipt.exact_result_signature
    assert changed.geometry_signature != receipt.geometry_signature
    assert _application_snapshot() == before


def _validate_active_collision(collision, artifact):
    App.setActiveDocument(str(collision.Name))
    assert App.ActiveDocument is collision
    before = _application_snapshot()
    receipt = adapter.build_transition_exact_geometry(artifact)
    assert receipt.shape_type == "Wire"
    assert _application_snapshot() == before


def _validate_nested_construction(document, artifact):
    App.setActiveDocument(str(document.Name))
    before = _application_snapshot()
    previous_documents = dict(App.listDocuments())
    cancellation_calls = 0
    nested_receipts = []

    def construct_nested_without_cancelling():
        nonlocal cancellation_calls
        cancellation_calls += 1
        if cancellation_calls == 2:
            outer_documents = _new_documents(previous_documents)
            assert len(outer_documents) == 1
            outer_document = outer_documents[0]
            assert App.ActiveDocument is document
            nested_receipts.append(
                adapter.build_transition_exact_geometry(artifact)
            )
            assert App.ActiveDocument is document
            assert _new_documents(previous_documents) == (outer_document,)
        return False

    outer_receipt = adapter.build_transition_exact_geometry(
        artifact,
        cancellation_requested=construct_nested_without_cancelling,
    )
    assert cancellation_calls == 3
    assert nested_receipts == [outer_receipt]
    assert _application_snapshot() == before


def _validate_cancellation_and_failure(document, artifact):
    App.setActiveDocument(str(document.Name))
    before = _application_snapshot()
    previous_documents = dict(App.listDocuments())
    cancellation_calls = 0

    def cancel_after_shape_construction():
        nonlocal cancellation_calls
        cancellation_calls += 1
        if cancellation_calls == 3:
            temporary = _new_documents(previous_documents)
            assert len(temporary) == 1
            assert len(temporary[0].Objects) == 1
            assert str(temporary[0].Objects[0].Shape.ShapeType) == "Wire"
            return True
        return False

    _expect_geometry_error(
        lambda: adapter.build_transition_exact_geometry(
            artifact,
            cancellation_requested=cancel_after_shape_construction,
        ),
        "exact-geometry-cancelled",
    )
    assert cancellation_calls == 3
    assert _application_snapshot() == before

    check_calls = 0

    def fail_cancellation_check_after_object_creation():
        nonlocal check_calls
        check_calls += 1
        if check_calls == 2:
            raise RuntimeError("injected cancellation-check failure")
        return False

    error = _expect_geometry_error(
        lambda: adapter.build_transition_exact_geometry(
            artifact,
            cancellation_requested=(
                fail_cancellation_check_after_object_creation
            ),
        ),
        "exact-geometry-cancellation-check-failed",
    )
    assert "injected cancellation-check failure" in error.detail
    assert _application_snapshot() == before

    original_shape_builder = adapter._make_transition_shape

    def fail_shape_build(_centreline):
        temporary = _new_documents(previous_documents)
        assert len(temporary) == 1
        assert len(temporary[0].Objects) == 1
        raise RuntimeError("injected Part build failure")

    adapter._make_transition_shape = fail_shape_build
    try:
        error = _expect_geometry_error(
            lambda: adapter.build_transition_exact_geometry(artifact),
            "exact-geometry-build-failed",
        )
        assert "injected Part build failure" in error.detail
    finally:
        adapter._make_transition_shape = original_shape_builder
    assert _application_snapshot() == before


def _validate_invalid_and_zero_length(document, artifact):
    App.setActiveDocument(str(document.Name))
    before = _application_snapshot()
    result = artifact.payload
    corrupt = api.TransitionDerivedArtifact(
        stage="exact-validation",
        source_signature=artifact.source_signature,
        payload=replace(
            result,
            result_signature="sha256:" + "0" * 64,
        ),
    )
    error = _expect_geometry_error(
        lambda: adapter.build_transition_exact_geometry(corrupt),
        "invalid-exact-artifact",
    )
    assert error.source_code == "invalid-exact-artifact"
    assert _application_snapshot() == before

    zero_receipt = adapter.build_transition_exact_geometry(_artifact(0.0))
    assert zero_receipt.shape_type == "Vertex"
    assert zero_receipt.vertex_count == 1
    assert zero_receipt.edge_count == 0
    assert zero_receipt.polyline_length_mm == 0.0
    assert zero_receipt.minimum_x_mm == zero_receipt.maximum_x_mm == 0.0
    assert zero_receipt.minimum_y_mm == zero_receipt.maximum_y_mm == 0.0
    assert _application_snapshot() == before

    for invalid in (object(), True):
        try:
            if invalid is True:
                adapter.build_transition_exact_geometry(
                    artifact,
                    cancellation_requested=invalid,
                )
            else:
                adapter.build_transition_exact_geometry(invalid)
        except TypeError:
            pass
        else:
            raise AssertionError("Expected exact-geometry TypeError")
    assert _application_snapshot() == before


def validate():
    assert App.listDocuments() == {}, (
        "the exact-geometry validator requires an isolated FreeCAD process; "
        "observed {!r}".format(tuple(App.listDocuments()))
    )
    assert App.ActiveDocument is None
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    assert qualification["compatibility_evaluation"]["matched_profile_id"] in {
        "linux-x86_64-flatpak-freecad-1.1.1",
        "linux-x86_64-flatpak-freecad-1.1.3",
    }

    document, _obj = _new_editable_document()
    collision, _collision_obj = _new_colliding_temporary_document()
    assert App.ActiveDocument is document
    artifact = _artifact()
    try:
        _validate_success_and_determinism(document, artifact)
        _validate_ambiguous_ownership(document, collision, artifact)
        _validate_active_collision(collision, artifact)
        _validate_nested_construction(document, artifact)
        _validate_cancellation_and_failure(document, artifact)
        _validate_invalid_and_zero_length(document, artifact)
    finally:
        for test_document in (collision, document):
            name = str(test_document.Name)
            if App.listDocuments().get(name) is test_document:
                App.closeDocument(name)

    assert App.listDocuments() == {}
    assert App.ActiveDocument is None
    receipt = adapter.build_transition_exact_geometry(artifact)
    assert receipt.shape_type == "Wire"
    assert App.listDocuments() == {}
    assert App.ActiveDocument is None
    print("Phase 6 transition transient exact geometry validation passed")


validate()
