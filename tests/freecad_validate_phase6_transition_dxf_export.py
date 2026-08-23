#!/usr/bin/env python3
"""Validate transition DXF export in the qualified FreeCAD runtime."""

import json
import math
import os
import pathlib
import sys
import tempfile
import uuid

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_dependency_manifest  # noqa: E402
from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.export import transition_dxf as exporter  # noqa: E402
from tracktemplate.adapters.freecad import transition_exact  # noqa: E402


EDITABLE_DOCUMENT_NAME = "Phase6TransitionDxfExportEditable"


def _state(transition_length_mm=300.0):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase6:dxf-export-freecad",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 6 qualified DXF export",
        end_name="Exit",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _fixture(output_directory, transition_length_mm=300.0):
    state = _state(transition_length_mm)
    specification = api.TransitionExactSpecification(0.05, 64)
    artifact = api.regenerate_transition_exact(
        api.TransitionDerivedCache(),
        state,
        specification,
    )
    request = api.TransitionDxfExportRequest(
        output_directory=str(output_directory),
        generator_version=api.DEVELOPMENT_CHECKPOINT,
    )
    return state, specification, artifact, request


def _property_snapshot(container):
    names = tuple(getattr(container, "PropertiesList", ()))
    return tuple((name, repr(getattr(container, name))) for name in names)


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
    document.openTransaction("Create operator-owned export baseline")
    obj = document.addObject("App::FeaturePython", "OperatorOwnedObject")
    obj.addProperty("App::PropertyString", "OperatorData")
    obj.OperatorData = "must remain unchanged"
    obj.Label = "Operator-owned export baseline"
    document.commitTransaction()
    document.recompute()
    return document


def _new_colliding_temporary_document():
    document = App.newDocument(
        transition_exact.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME,
        "Pre-existing hidden export collision",
        True,
        True,
    )
    obj = document.addObject("App::FeaturePython", "CollidingOwner")
    obj.addProperty("App::PropertyString", "OperatorData")
    obj.OperatorData = "pre-existing collision must remain unchanged"
    obj.Label = "Pre-existing hidden export collision"
    document.recompute()
    return document


def _expect_export_error(action, code, *, cleanup_complete=True):
    try:
        action()
    except exporter.TransitionDxfExportError as error:
        assert error.code == code, error.diagnostic()
        assert error.cleanup_complete is cleanup_complete, error.diagnostic()
        return error
    raise AssertionError("Expected TransitionDxfExportError {!r}".format(code))


def _directory_snapshot(path):
    return tuple(
        sorted(
            (item.name, item.read_bytes())
            for item in path.iterdir()
            if item.is_file()
        )
    )


def _assert_no_staging(path):
    assert not any(
        item.name.startswith(".tracktemplate-transition-dxf-")
        for item in path.iterdir()
    )


def _assert_descriptors_closed(descriptors):
    for descriptor in descriptors:
        try:
            exporter.os.fstat(descriptor)
        except OSError:
            continue
        raise AssertionError("anonymous staging descriptor remained open")


def _descriptor_is_open(descriptor):
    try:
        os.fstat(descriptor)
    except OSError:
        return False
    return True


def _assert_directory_lock_released(path):
    descriptor = os.open(
        path,
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0),
    )
    locked = False
    try:
        exporter.fcntl.flock(
            descriptor,
            exporter.fcntl.LOCK_EX | exporter.fcntl.LOCK_NB,
        )
        locked = True
    finally:
        if locked:
            exporter.fcntl.flock(descriptor, exporter.fcntl.LOCK_UN)
        os.close(descriptor)


def _validate_freecad_dxf_import(dxf_path, exact_result):
    """Import the target file in one owned document and restore the host."""
    import importDXF

    before = _application_snapshot()
    previous_documents = dict(App.listDocuments())
    previous_active = App.ActiveDocument
    document = None
    document_name = ""
    for _attempt in range(16):
        candidate = "Phase6TransitionDxfImport_" + uuid.uuid4().hex
        if candidate not in App.listDocuments():
            document_name = candidate
            break
    assert document_name and document_name not in previous_documents
    try:
        document = App.newDocument(
            document_name,
            "Owned Phase 6 DXF import validation",
            True,
            True,
        )
        assert App.listDocuments().get(document_name) is document
        assert document_name not in previous_documents
        importDXF.insert(str(dxf_path), document_name)
        document.recompute()
        shapes = tuple(
            obj.Shape
            for obj in document.Objects
            if "Shape" in obj.PropertiesList and not obj.Shape.isNull()
        )
        assert shapes, "FreeCAD imported no exact shape from the DXF"
        if len(exact_result.centreline.points) == 1:
            assert any(
                str(shape.ShapeType) == "Vertex" for shape in shapes
            ), "FreeCAD did not import the zero-length DXF POINT as a vertex"
        minimum_x = min(shape.BoundBox.XMin for shape in shapes)
        minimum_y = min(shape.BoundBox.YMin for shape in shapes)
        maximum_x = max(shape.BoundBox.XMax for shape in shapes)
        maximum_y = max(shape.BoundBox.YMax for shape in shapes)
        expected_points = exact_result.centreline.points
        assert math.isclose(
            minimum_x,
            min(point.x_mm for point in expected_points),
            abs_tol=1.0e-7,
        )
        assert math.isclose(
            minimum_y,
            min(point.y_mm for point in expected_points),
            abs_tol=1.0e-7,
        )
        assert math.isclose(
            maximum_x,
            max(point.x_mm for point in expected_points),
            abs_tol=1.0e-7,
        )
        assert math.isclose(
            maximum_y,
            max(point.y_mm for point in expected_points),
            abs_tol=1.0e-7,
        )
    finally:
        if (
            document is not None
            and App.listDocuments().get(document_name) is document
            and document_name not in previous_documents
        ):
            App.closeDocument(document_name)
        if previous_active is None:
            if App.ActiveDocument is not None:
                App.setActiveDocument("")
        elif (
            App.listDocuments().get(str(previous_active.Name))
            is previous_active
        ):
            App.setActiveDocument(str(previous_active.Name))
    assert _application_snapshot() == before


def _validate_success_and_active_document_restoration(
    root,
    editable,
    collision,
):
    output = root / "success"
    output.mkdir()
    state, specification, artifact, request = _fixture(output)

    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    receipt = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert receipt.disposition == "created"
    assert receipt.project_status == "unknown"
    assert _application_snapshot() == before
    _assert_no_staging(output)

    dxf_path = output / receipt.dxf_filename
    manifest_path = output / receipt.manifest_filename
    assert dxf_path.read_text(encoding="ascii").endswith("0\nEOF\n")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert validate_dependency_manifest.validate_document(manifest) == []
    assert validate_dependency_manifest.validate_document(
        manifest,
        require_project_cleared=True,
    ) == [
        "$.project_status.status is unknown rather than project-cleared"
    ]
    _validate_freecad_dxf_import(
        dxf_path,
        api.transition_exact_result_from_artifact(artifact),
    )

    output_before = _directory_snapshot(output)
    App.setActiveDocument(str(collision.Name))
    active_collision_before = _application_snapshot()
    reused = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert reused.disposition == "reused"
    assert _application_snapshot() == active_collision_before
    assert _directory_snapshot(output) == output_before
    _assert_no_staging(output)
    return state, specification, artifact


def _validate_cancellation(root, editable, state, specification, artifact):
    output = root / "cancelled"
    output.mkdir()
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    baseline_names = set(App.listDocuments())
    observed_temporary_shape = False

    def cancel_after_exact_shape():
        nonlocal observed_temporary_shape
        for name, document in App.listDocuments().items():
            if name in baseline_names:
                continue
            for obj in document.Objects:
                if (
                    "Shape" in obj.PropertiesList
                    and not obj.Shape.isNull()
                    and str(obj.Shape.ShapeType) == "Wire"
                ):
                    observed_temporary_shape = True
                    return True
        return False

    error = _expect_export_error(
        lambda: exporter.export_transition_dxf(
            state,
            artifact,
            specification,
            request,
            cancellation_requested=cancel_after_exact_shape,
        ),
        "transition-dxf-exact-geometry-failed",
    )
    assert error.source_code == "exact-geometry-cancelled"
    assert observed_temporary_shape is True
    assert _application_snapshot() == before
    assert list(output.iterdir()) == []


def _validate_surviving_host_interruption(
    root,
    editable,
    state,
    specification,
    artifact,
):
    output = root / "surviving-host-interruption"
    output.mkdir()
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    original_write = exporter._write_staged_file
    staged_descriptors = []
    interruption = KeyboardInterrupt("qualified host interruption")

    def observe_write(
        directory_descriptor,
        name,
        value,
        staged_files,
        operation_state,
    ):
        staged_file = original_write(
            directory_descriptor,
            name,
            value,
            staged_files,
            operation_state,
        )
        staged_descriptors.append(staged_file[0])
        return staged_file

    def interrupt_after_staging():
        if len(staged_descriptors) == 2:
            raise interruption
        return False

    exporter._write_staged_file = observe_write
    try:
        try:
            exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
                cancellation_requested=interrupt_after_staging,
            )
        except KeyboardInterrupt as error:
            assert error is interruption
        else:
            raise AssertionError("Expected qualified host interruption")
    finally:
        exporter._write_staged_file = original_write

    assert len(staged_descriptors) == 2
    _assert_descriptors_closed(staged_descriptors)
    assert list(output.iterdir()) == []
    assert _application_snapshot() == before
    diagnostic = interruption.__cause__
    assert isinstance(diagnostic, exporter.TransitionDxfExportError)
    assert diagnostic.code == "transition-dxf-export-failed"
    assert diagnostic.source_code == "KeyboardInterrupt"
    assert diagnostic.destination_changed is False
    assert diagnostic.cleanup_complete is True
    assert diagnostic.recoverable is True

    receipt = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert receipt.disposition == "created"
    assert _application_snapshot() == before
    _assert_no_staging(output)


def _validate_resource_acquisition_interruptions(
    root,
    editable,
    state,
    specification,
    artifact,
):
    output = root / "resource-acquisition-interruption"
    output.mkdir()
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    original_fstat = exporter.os.fstat
    directory_descriptors = []
    interruption = KeyboardInterrupt(
        "qualified directory-acquisition interruption"
    )

    def interrupt_directory_fstat(descriptor):
        directory_descriptors.append(descriptor)
        raise interruption

    exporter.os.fstat = interrupt_directory_fstat
    try:
        try:
            exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
            )
        except KeyboardInterrupt as error:
            assert error is interruption
        else:
            raise AssertionError(
                "Expected qualified directory-acquisition interruption"
            )
    finally:
        exporter.os.fstat = original_fstat

    assert len(directory_descriptors) == 1
    _assert_descriptors_closed(directory_descriptors)
    _assert_directory_lock_released(output)
    assert list(output.iterdir()) == []
    assert _application_snapshot() == before
    diagnostic = interruption.__cause__
    assert isinstance(diagnostic, exporter.TransitionDxfExportError)
    assert diagnostic.code == "transition-dxf-export-failed"
    assert diagnostic.source_code == "KeyboardInterrupt"
    assert diagnostic.destination_changed is True
    assert diagnostic.cleanup_complete is True
    assert diagnostic.recoverable is False

    receipt = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert receipt.disposition == "created"
    exact_outputs = _directory_snapshot(output)
    assert _application_snapshot() == before

    original_digest = exporter._sha256_descriptor
    original_close = exporter.os.close
    final_descriptors = []
    close_interrupted = False
    close_interruption = SystemExit(43)

    def observe_final_digest(descriptor):
        final_descriptors.append(descriptor)
        return original_digest(descriptor)

    def interrupt_final_close(descriptor):
        nonlocal close_interrupted
        if (
            final_descriptors
            and descriptor == final_descriptors[0]
            and not close_interrupted
        ):
            close_interrupted = True
            raise close_interruption
        return original_close(descriptor)

    exporter._sha256_descriptor = observe_final_digest
    exporter.os.close = interrupt_final_close
    try:
        try:
            exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
            )
        except SystemExit as error:
            assert error is close_interruption
            assert error.code == 43
        else:
            raise AssertionError(
                "Expected qualified existing-final close interruption"
            )
    finally:
        exporter.os.close = original_close
        exporter._sha256_descriptor = original_digest

    assert close_interrupted is True
    assert len(final_descriptors) == 1
    final_descriptor_open = _descriptor_is_open(final_descriptors[0])
    _assert_directory_lock_released(output)
    assert _directory_snapshot(output) == exact_outputs
    assert _application_snapshot() == before
    diagnostic = close_interruption.__cause__
    assert isinstance(diagnostic, exporter.TransitionDxfExportError)
    assert diagnostic.code == "transition-dxf-export-cleanup-failed"
    assert diagnostic.source_code == "SystemExit"
    assert diagnostic.destination_changed is False
    assert diagnostic.cleanup_complete is False
    assert diagnostic.recoverable is False

    reused = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert reused.disposition == "reused"
    assert _directory_snapshot(output) == exact_outputs
    assert _application_snapshot() == before
    if final_descriptor_open:
        original_close(final_descriptors[0])
    _assert_no_staging(output)


def _validate_zero_length_point_import(root, editable):
    output = root / "zero-length"
    output.mkdir()
    state, specification, artifact, request = _fixture(output, 0.0)
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    receipt = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert receipt.disposition == "created"
    assert receipt.project_status == "unknown"
    assert _application_snapshot() == before
    dxf_path = output / receipt.dxf_filename
    assert "\nPOINT\n" in dxf_path.read_text(encoding="ascii")
    exact_result = api.transition_exact_result_from_artifact(artifact)
    assert len(exact_result.centreline.points) == 1
    _validate_freecad_dxf_import(dxf_path, exact_result)
    assert _application_snapshot() == before
    _assert_no_staging(output)


def _validate_geometry_failure(
    root,
    editable,
    state,
    specification,
    artifact,
):
    output = root / "geometry-failure"
    output.mkdir()
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    original_shape_builder = transition_exact._make_transition_shape

    def fail_shape_build(_centreline):
        raise RuntimeError("injected export geometry-build failure")

    transition_exact._make_transition_shape = fail_shape_build
    try:
        error = _expect_export_error(
            lambda: exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-exact-geometry-failed",
        )
        assert error.source_code == "exact-geometry-build-failed"
    finally:
        transition_exact._make_transition_shape = original_shape_builder
    assert _application_snapshot() == before
    assert list(output.iterdir()) == []


def _validate_geometry_cleanup_failure(
    root,
    editable,
    state,
    specification,
    artifact,
):
    output = root / "geometry-cleanup-failure"
    output.mkdir()
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    previous_documents = dict(App.listDocuments())
    previous_active = App.ActiveDocument
    original_cleanup = transition_exact._cleanup_temporary_document

    def leave_owned_document_open(
        document,
        document_name,
        captured_documents,
        _captured_active,
        _captured_name,
    ):
        assert captured_documents == previous_documents
        assert document_name not in captured_documents
        assert App.listDocuments().get(document_name) is document
        assert len(document.Objects) == 1
        assert str(document.Objects[0].Shape.ShapeType) == "Wire"
        raise transition_exact.TransitionExactGeometryError(
            "exact-geometry-cleanup-failed",
            "injected owned-document cleanup failure",
            cleanup_complete=False,
            recoverable=False,
        )

    transition_exact._cleanup_temporary_document = leave_owned_document_open
    residual_documents = ()
    try:
        error = _expect_export_error(
            lambda: exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-exact-geometry-cleanup-failed",
            cleanup_complete=False,
        )
        assert error.source_code == "exact-geometry-cleanup-failed"
        assert error.recoverable is False
        residual_documents = tuple(
            (name, document)
            for name, document in App.listDocuments().items()
            if name not in previous_documents
        )
        assert len(residual_documents) == 1
        assert residual_documents[0][1].Temporary is True
        assert _application_snapshot() != before
        assert list(output.iterdir()) == []
    finally:
        transition_exact._cleanup_temporary_document = original_cleanup
        owned_residuals = tuple(
            (name, document)
            for name, document in App.listDocuments().items()
            if name not in previous_documents
        )
        for name, document in owned_residuals:
            if App.listDocuments().get(name) is document:
                App.closeDocument(name)
        if previous_active is None:
            if App.ActiveDocument is not None:
                App.setActiveDocument("")
        elif (
            App.listDocuments().get(str(previous_active.Name))
            is previous_active
        ):
            App.setActiveDocument(str(previous_active.Name))
    assert _application_snapshot() == before


def _validate_commit_monotonic_recovery(
    root,
    editable,
    state,
    specification,
    artifact,
):
    output = root / "commit-failure"
    output.mkdir()
    marker = output / "operator-owned.txt"
    marker.write_text("must remain unchanged", encoding="utf-8")
    request = api.TransitionDxfExportRequest(
        str(output),
        api.DEVELOPMENT_CHECKPOINT,
    )
    App.setActiveDocument(str(editable.Name))
    before = _application_snapshot()
    plan = api.prepare_transition_dxf_export(
        state,
        artifact,
        specification,
        request,
    )
    original_link = exporter._link_file
    link_calls = 0

    def fail_second_link(
        source_directory_descriptor,
        destination_directory_descriptor,
        destination_name,
    ):
        nonlocal link_calls
        link_calls += 1
        if link_calls == 2:
            raise OSError("injected qualified commit failure")
        original_link(
            source_directory_descriptor,
            destination_directory_descriptor,
            destination_name,
        )

    exporter._link_file = fail_second_link
    try:
        error = _expect_export_error(
            lambda: exporter.export_transition_dxf(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-commit-failed",
            cleanup_complete=False,
        )
        assert error.destination_changed is True
        assert error.recoverable is True
    finally:
        exporter._link_file = original_link
    assert _application_snapshot() == before
    assert marker.read_text(encoding="utf-8") == "must remain unchanged"
    dxf_path = output / plan.dxf_filename
    manifest_path = output / plan.manifest_filename
    assert dxf_path.is_file()
    assert not manifest_path.exists()
    dxf_metadata = dxf_path.stat()
    dxf_snapshot = (
        dxf_metadata.st_dev,
        dxf_metadata.st_ino,
        dxf_metadata.st_mode,
        dxf_metadata.st_size,
        dxf_metadata.st_mtime_ns,
        dxf_path.read_bytes(),
    )
    _assert_no_staging(output)

    recovered = exporter.export_transition_dxf(
        state,
        artifact,
        specification,
        request,
    )
    assert recovered.disposition == "created"
    observed_metadata = dxf_path.stat()
    assert (
        observed_metadata.st_dev,
        observed_metadata.st_ino,
        observed_metadata.st_mode,
        observed_metadata.st_size,
        observed_metadata.st_mtime_ns,
        dxf_path.read_bytes(),
    ) == dxf_snapshot
    assert manifest_path.is_file()
    assert marker.read_text(encoding="utf-8") == "must remain unchanged"
    assert _application_snapshot() == before
    _assert_no_staging(output)


def validate():
    assert App.listDocuments() == {}, (
        "the DXF validator requires an isolated FreeCAD process; observed "
        "{!r}".format(tuple(App.listDocuments()))
    )
    assert App.ActiveDocument is None
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    assert qualification["compatibility_evaluation"]["matched_profile_id"] in {
        "linux-x86_64-flatpak-freecad-1.1.1",
        "linux-x86_64-flatpak-freecad-1.1.3",
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
    }

    editable = _new_editable_document()
    collision = _new_colliding_temporary_document()
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            state, specification, artifact = (
                _validate_success_and_active_document_restoration(
                    root,
                    editable,
                    collision,
                )
            )
            _validate_cancellation(
                root,
                editable,
                state,
                specification,
                artifact,
            )
            _validate_surviving_host_interruption(
                root,
                editable,
                state,
                specification,
                artifact,
            )
            _validate_resource_acquisition_interruptions(
                root,
                editable,
                state,
                specification,
                artifact,
            )
            _validate_zero_length_point_import(root, editable)
            _validate_geometry_failure(
                root,
                editable,
                state,
                specification,
                artifact,
            )
            _validate_geometry_cleanup_failure(
                root,
                editable,
                state,
                specification,
                artifact,
            )
            _validate_commit_monotonic_recovery(
                root,
                editable,
                state,
                specification,
                artifact,
            )
    finally:
        for document in (collision, editable):
            name = str(document.Name)
            if App.listDocuments().get(name) is document:
                App.closeDocument(name)

    assert App.listDocuments() == {}
    assert App.ActiveDocument is None
    print("Phase 6 transition DXF qualified FreeCAD validation passed")


validate()
