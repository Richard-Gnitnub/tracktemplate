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


def _editable_snapshot(document, obj):
    return (
        tuple(sorted(App.listDocuments())),
        App.ActiveDocument,
        tuple(document.Objects),
        tuple(obj.PropertiesList),
        str(obj.OperatorData),
        str(obj.Label),
        int(document.UndoCount),
        int(document.RedoCount),
        str(document.FileName),
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


def _temporary_documents(editable_document):
    return tuple(
        document
        for document in App.listDocuments().values()
        if document is not editable_document
    )


def _validate_success_and_determinism(document, obj, artifact):
    before = _editable_snapshot(document, obj)
    observations = []

    def observe_without_cancelling():
        temporary = _temporary_documents(document)
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
    assert _editable_snapshot(document, obj) == before

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
    assert receipt.freecad_version == "1.1.1"
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
    assert _editable_snapshot(document, obj) == before


def _validate_cancellation_and_failure(document, obj, artifact):
    before = _editable_snapshot(document, obj)
    cancellation_calls = 0

    def cancel_after_shape_construction():
        nonlocal cancellation_calls
        cancellation_calls += 1
        if cancellation_calls == 3:
            temporary = _temporary_documents(document)
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
    assert _editable_snapshot(document, obj) == before

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
    assert _editable_snapshot(document, obj) == before

    original_shape_builder = adapter._make_transition_shape

    def fail_shape_build(_centreline):
        temporary = _temporary_documents(document)
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
    assert _editable_snapshot(document, obj) == before


def _validate_invalid_and_zero_length(document, obj, artifact):
    before = _editable_snapshot(document, obj)
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
    assert _editable_snapshot(document, obj) == before

    zero_receipt = adapter.build_transition_exact_geometry(_artifact(0.0))
    assert zero_receipt.shape_type == "Vertex"
    assert zero_receipt.vertex_count == 1
    assert zero_receipt.edge_count == 0
    assert zero_receipt.polyline_length_mm == 0.0
    assert zero_receipt.minimum_x_mm == zero_receipt.maximum_x_mm == 0.0
    assert zero_receipt.minimum_y_mm == zero_receipt.maximum_y_mm == 0.0
    assert _editable_snapshot(document, obj) == before

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
    assert _editable_snapshot(document, obj) == before


def validate():
    assert App.listDocuments() == {}, (
        "the exact-geometry validator requires an isolated FreeCAD process"
    )
    assert App.ActiveDocument is None
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
        "linux-x86_64-flatpak-freecad-1.1.1"
    )

    document, obj = _new_editable_document()
    artifact = _artifact()
    try:
        _validate_success_and_determinism(document, obj, artifact)
        _validate_cancellation_and_failure(document, obj, artifact)
        _validate_invalid_and_zero_length(document, obj, artifact)
    finally:
        for name in tuple(App.listDocuments()):
            if (
                name == EDITABLE_DOCUMENT_NAME
                or name.startswith(
                    adapter.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME
                )
            ):
                App.closeDocument(name)

    assert App.listDocuments() == {}
    assert App.ActiveDocument is None
    receipt = adapter.build_transition_exact_geometry(artifact)
    assert receipt.shape_type == "Wire"
    assert App.listDocuments() == {}
    assert App.ActiveDocument is None
    print("Phase 6 transition transient exact geometry validation passed")


validate()
