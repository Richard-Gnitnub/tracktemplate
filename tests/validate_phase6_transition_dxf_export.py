#!/usr/bin/env python3
"""Validate the bounded Phase 6 transition DXF export contract."""

from dataclasses import replace
import hashlib
import importlib.abc
import json
import math
import os
import pathlib
import subprocess
import sys
import tempfile
from types import SimpleNamespace


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tools import validate_dependency_manifest  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.adapters.export import transition_dxf as adapter  # noqa: E402
from tracktemplate.application import transition_export as contract  # noqa: E402


def _state(transition_length_mm=300.0, **changes):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    values = {
        "transition_id": "transition:phase6:dxf-export",
        "circle_centre_y_mm": circle_centre_y_mm,
        "radius_mm": radius_mm,
        "target_signed_offset_mm": api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        "total_angle_rad": math.pi / 2.0,
        "track_name": "Phase 6 DXF export transition",
        "end_name": "Entry",
    }
    values.update(changes)
    return api.analyse_transition_state(
        api.TransitionState(api.TransitionIntent(**values))
    )


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


def _geometry_receipt(artifact, **changes):
    result = api.transition_exact_result_from_artifact(artifact)
    values = {
        "source_signature": result.source_signature,
        "exact_artifact_signature": result.artifact_signature,
        "exact_result_signature": result.result_signature,
        "domain_id": result.centreline.domain_id,
        "frame_id": result.centreline.frame_id,
        "length_unit": result.centreline.length_unit,
        "shape_type": (
            "Vertex" if len(result.centreline.points) == 1 else "Wire"
        ),
        "geometry_signature": api.transition_derived_contract_signature(
            "test-only.transition-exact-geometry.v1",
            {
                "artifact_signature": result.artifact_signature,
                "point_count": len(result.centreline.points),
            },
        ),
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _export_with_stub(
    state,
    artifact,
    specification,
    request,
    *,
    cancellation_requested=None,
    builder=None,
):
    original = adapter._default_geometry_builder
    adapter._default_geometry_builder = builder or (
        lambda candidate, _cancel: _geometry_receipt(candidate)
    )
    try:
        return adapter.export_transition_dxf(
            state,
            artifact,
            specification,
            request,
            cancellation_requested=cancellation_requested,
        )
    finally:
        adapter._default_geometry_builder = original


def _expect_export_error(action, code):
    try:
        action()
    except adapter.TransitionDxfExportError as error:
        assert error.code == code, error.diagnostic()
        assert set(error.diagnostic()) == {
            "cleanup_complete",
            "code",
            "destination_changed",
            "message",
            "recoverable",
            "source_code",
        }
        return error
    raise AssertionError("Expected TransitionDxfExportError {!r}".format(code))


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _sha256(value):
    return hashlib.sha256(value).hexdigest()


def _directory_snapshot(path):
    return tuple(
        sorted(
            (
                item.name,
                item.is_symlink(),
                item.read_bytes() if item.is_file() else None,
            )
            for item in path.iterdir()
        )
    )


def _assert_no_staging(path):
    assert not any(
        item.name.startswith(".tracktemplate-transition-dxf-")
        for item in path.iterdir()
    )


def _transaction_artifacts(path):
    return tuple(
        sorted(
            item.name
            for item in path.iterdir()
            if item.name.startswith(".tracktemplate-transition-dxf-")
        )
    )


def _metadata_snapshot(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_atime_ns,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_descriptor(descriptor):
    return b"".join(
        iter(lambda: os.read(descriptor, 1024 * 1024), b"")
    )


def _path_snapshot(path):
    descriptor = os.open(
        path,
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOATIME", 0),
    )
    try:
        value = _read_descriptor(descriptor)
        return _metadata_snapshot(os.fstat(descriptor)) + (value,)
    finally:
        os.close(descriptor)


def _regular_file_snapshots(path):
    return {
        item.name: _path_snapshot(item)
        for item in sorted(path.iterdir())
        if item.is_file() and not item.is_symlink()
    }


def _staging_snapshot(path):
    directory_descriptor = os.open(
        path,
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOATIME", 0),
    )
    try:
        entries = []
        for name in sorted(os.listdir(directory_descriptor)):
            descriptor = os.open(
                name,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOATIME", 0),
                dir_fd=directory_descriptor,
            )
            try:
                entries.append(
                    (name,)
                    + _metadata_snapshot(os.fstat(descriptor))
                    + (_read_descriptor(descriptor),)
                )
            finally:
                os.close(descriptor)
        return (
            _metadata_snapshot(os.fstat(directory_descriptor)),
            tuple(entries),
        )
    finally:
        os.close(directory_descriptor)


def _dxf_pairs(value):
    lines = value.decode("ascii").splitlines()
    assert lines and len(lines) % 2 == 0
    return tuple(
        (int(lines[index]), lines[index + 1])
        for index in range(0, len(lines), 2)
    )


def _dxf_section(pairs, name):
    start = next(
        index + 2
        for index in range(len(pairs) - 1)
        if pairs[index:index + 2] == ((0, "SECTION"), (2, name))
    )
    end = pairs.index((0, "ENDSEC"), start)
    return pairs[start:end]


def _header_value(header, name):
    index = header.index((9, name))
    return header[index + 1]


def _assert_independent_dxf(value, exact_result):
    pairs = _dxf_pairs(value)
    assert pairs[-1] == (0, "EOF")
    header = _dxf_section(pairs, "HEADER")
    assert _header_value(header, "$ACADVER") == (1, "AC1015")
    assert _header_value(header, "$INSUNITS") == (70, "4")
    assert _header_value(header, "$MEASUREMENT") == (70, "1")
    tables = _dxf_section(pairs, "TABLES")
    assert (2, api.TRANSITION_DXF_EXPORT_LAYER_NAME) in tables
    entities = _dxf_section(pairs, "ENTITIES")
    expected = tuple(
        (point.x_mm, point.y_mm)
        for point in exact_result.centreline.points
    )
    if len(expected) == 1:
        assert entities[0] == (0, "POINT")
        assert [pair for pair in entities if pair[0] == 10] == [
            (10, "0")
        ]
        assert [pair for pair in entities if pair[0] == 20] == [
            (20, "0")
        ]
        assert [pair for pair in entities if pair[0] == 30] == [
            (30, "0")
        ]
        return
    assert entities[0] == (0, "LWPOLYLINE")
    assert next(value for code, value in entities if code == 90) == str(
        len(expected)
    )
    assert next(value for code, value in entities if code == 70) == "0"
    observed_x = [float(value) for code, value in entities if code == 10]
    observed_y = [float(value) for code, value in entities if code == 20]
    assert tuple(zip(observed_x, observed_y)) == expected


def _validate_public_contract_and_isolation():
    request = api.TransitionDxfExportRequest(
        output_directory="/tmp/phase6-transition-dxf-test",
        generator_version=api.DEVELOPMENT_CHECKPOINT,
    )
    assert request.output_directory.endswith("phase6-transition-dxf-test")
    assert request.generator_version == "10.2A8A7B16"
    for name in contract.__all__:
        assert name in api.__all__
        assert getattr(api, name) is getattr(contract, name)
    assert api.TRANSITION_DXF_EXPORT_PROJECT_STATUS == "unknown"
    assert api.TRANSITION_DXF_EXPORT_COLLISION_POLICY == (
        "reuse-identical-or-fail"
    )

    for output_directory, generator_version in (
        ("", api.DEVELOPMENT_CHECKPOINT),
        ("bad\x00path", api.DEVELOPMENT_CHECKPOINT),
        ("/tmp/output", ""),
        ("/tmp/output", " untrimmed"),
        ("/tmp/output", "bad\nversion"),
    ):
        _expect_state_error(
            lambda output_directory=output_directory,
            generator_version=generator_version: (
                api.TransitionDxfExportRequest(
                    output_directory=output_directory,
                    generator_version=generator_version,
                )
            ),
            "invalid-transition-dxf-export-request",
        )

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    application_module = modules[
        "tracktemplate.application.transition_export"
    ]
    adapter_module = modules["tracktemplate.adapters.export.transition_dxf"]
    assert application_module["layer"] == "application"
    assert adapter_module["layer"] == "adapter"
    assert application_module["warning_signals"] == []
    assert adapter_module["warning_signals"] == []

    script = f"""
import importlib.abc
import sys

forbidden = {{
    "FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"
}}
attempted = []

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden import attempted: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {str(ROOT)!r})
from tracktemplate import api
from tracktemplate.adapters.export import transition_dxf
request = api.TransitionDxfExportRequest(
    "/tmp/isolated-transition-export",
    api.DEVELOPMENT_CHECKPOINT,
)
assert request.generator_version == api.DEVELOPMENT_CHECKPOINT
assert attempted == []
print("Phase 6 transition DXF isolated import passed")
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Phase 6 transition DXF isolated import passed" in (
        completed.stdout
    )


def _validate_plan_signatures_and_stale_inputs():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary)
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        result = api.transition_exact_result_from_artifact(artifact)
        assert plan.exact_result == result
        assert plan.canonical_model_sha256 == hashlib.sha256(
            api.transition_state_to_json(state).encode("utf-8")
        ).hexdigest()
        assert plan.source_signature.startswith("sha256:")
        assert plan.contract_signature == request.derived_request(
            result.result_signature
        ).contract_signature
        assert result.artifact_signature[7:] in plan.dxf_filename
        assert plan.dxf_filename.endswith(".dxf")
        assert plan.manifest_filename.endswith(
            ".dependency-manifest.json"
        )
        changed_version = replace(request, generator_version="next-version")
        changed_plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            changed_version,
        )
        assert changed_plan.contract_signature != plan.contract_signature
        assert changed_plan.source_signature != plan.source_signature
        assert changed_plan.dxf_filename == plan.dxf_filename

        stale_state = _state(260.0)
        _expect_state_error(
            lambda: api.prepare_transition_dxf_export(
                stale_state,
                artifact,
                specification,
                request,
            ),
            "stale-exact-validation",
        )
        result = artifact.payload
        corrupt = api.TransitionDerivedArtifact(
            stage="exact-validation",
            source_signature=artifact.source_signature,
            payload=replace(
                result,
                result_signature="sha256:" + "0" * 64,
            ),
        )
        _expect_state_error(
            lambda: api.prepare_transition_dxf_export(
                state,
                corrupt,
                specification,
                request,
            ),
            "invalid-exact-artifact",
        )


def _validate_success_manifest_reuse_and_zero_length():
    for transition_length_mm, expected_shape in (
        (300.0, "Wire"),
        (0.0, "Vertex"),
    ):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary) / "output"
            output.mkdir()
            state, specification, artifact, request = _fixture(
                output,
                transition_length_mm,
            )
            receipt = _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )
            assert receipt.disposition == "created"
            assert receipt.project_status == "unknown"
            assert receipt.cleanup_complete is True
            assert receipt.result_signature.startswith("sha256:")
            assert set(item.name for item in output.iterdir()) == {
                receipt.dxf_filename,
                receipt.manifest_filename,
            }
            _assert_no_staging(output)

            dxf_path = output / receipt.dxf_filename
            manifest_path = output / receipt.manifest_filename
            dxf_value = dxf_path.read_bytes()
            manifest_value = manifest_path.read_bytes()
            assert receipt.dxf_sha256 == _sha256(dxf_value)
            assert receipt.manifest_sha256 == _sha256(manifest_value)
            exact_result = api.transition_exact_result_from_artifact(artifact)
            _assert_independent_dxf(dxf_value, exact_result)
            assert receipt.geometry_signature == _geometry_receipt(
                artifact
            ).geometry_signature
            assert expected_shape == _geometry_receipt(artifact).shape_type

            manifest = json.loads(manifest_value.decode("utf-8"))
            assert validate_dependency_manifest.validate_document(
                manifest
            ) == []
            assert manifest["manifest_kind"] == "output"
            assert manifest["audit_scope"] == "core-rail-timber-path"
            assert manifest["intended_uses"] == ["private-development"]
            assert manifest["project_status"]["status"] == "unknown"
            assert manifest["project_status"]["decision_reference"] == (
                "D-P6-001"
            )
            assert manifest["subject"]["generator"] == {
                "program": "TrackTemplate",
                "version": api.DEVELOPMENT_CHECKPOINT,
            }
            assert manifest["subject"]["canonical_model_sha256"] == (
                hashlib.sha256(
                    api.transition_state_to_json(state).encode("utf-8")
                ).hexdigest()
            )
            assert manifest["dependencies"][0]["source"]["locator"] == (
                "canonical-model-sha256:"
                + manifest["subject"]["canonical_model_sha256"]
            )
            assert manifest["subject"]["artifacts"] == [
                {
                    "format": "DXF",
                    "path": receipt.dxf_filename,
                    "sha256": receipt.dxf_sha256,
                }
            ]
            assert all(
                dependency["project_status"]["status"] == "unknown"
                for dependency in manifest["dependencies"]
            )

            normal = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "validate_dependency_manifest.py"),
                    str(manifest_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            assert normal.returncode == 0, normal.stderr
            assert "valid (unknown)" in normal.stdout
            clearance = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "validate_dependency_manifest.py"),
                    "--require-project-cleared",
                    str(manifest_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            assert clearance.returncode == 1
            assert "rather than project-cleared" in clearance.stderr

            before = tuple(
                (
                    path.name,
                    path.stat().st_ino,
                    path.stat().st_mtime_ns,
                    path.read_bytes(),
                )
                for path in sorted(output.iterdir())
            )
            reused = _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )
            after = tuple(
                (
                    path.name,
                    path.stat().st_ino,
                    path.stat().st_mtime_ns,
                    path.read_bytes(),
                )
                for path in sorted(output.iterdir())
            )
            assert reused.disposition == "reused"
            assert reused.dxf_sha256 == receipt.dxf_sha256
            assert reused.manifest_sha256 == receipt.manifest_sha256
            assert reused.result_signature != receipt.result_signature
            assert after == before

            try:
                replace(receipt, dxf_sha256="0" * 64)
            except ValueError as error:
                assert "result_signature" in str(error)
            else:
                raise AssertionError("Expected inconsistent receipt rejection")


def _validate_destination_and_collision_controls():
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        other = output / "operator-owned.txt"
        other.write_text("unchanged", encoding="utf-8")
        baseline = _directory_snapshot(output)

        (output / plan.dxf_filename).write_bytes(b"operator collision\n")
        partial = _directory_snapshot(output)
        error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-collision",
        )
        assert error.destination_changed is False
        assert _directory_snapshot(output) == partial
        (output / plan.dxf_filename).unlink()

        (output / plan.dxf_filename).write_bytes(b"operator DXF\n")
        (output / plan.manifest_filename).write_bytes(b"operator manifest\n")
        complete = _directory_snapshot(output)
        _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-collision",
        )
        assert _directory_snapshot(output) == complete
        (output / plan.dxf_filename).unlink()
        (output / plan.manifest_filename).unlink()
        assert _directory_snapshot(output) == baseline

        target = root / "operator-target"
        target.write_text("operator symlink target", encoding="utf-8")
        os.symlink(target, output / plan.dxf_filename)
        linked = _directory_snapshot(output)
        _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-collision",
        )
        assert _directory_snapshot(output) == linked
        assert target.read_text(encoding="utf-8") == "operator symlink target"
        (output / plan.dxf_filename).unlink()

        linked_output = root / "linked-output"
        os.symlink(output, linked_output)
        linked_request = replace(request, output_directory=str(linked_output))
        _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                linked_request,
            ),
            "unsafe-transition-dxf-export-destination",
        )
        assert _directory_snapshot(output) == baseline

        for invalid_path in (
            "relative-output",
            str(output) + os.sep,
            os.path.dirname(str(output)) + os.sep + "missing",
            os.path.abspath(os.sep),
        ):
            invalid_request = replace(request, output_directory=invalid_path)
            expected = (
                "invalid-transition-dxf-export-destination"
                if invalid_path.endswith("missing")
                else "unsafe-transition-dxf-export-destination"
            )
            _expect_export_error(
                lambda invalid_request=invalid_request: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    invalid_request,
                ),
                expected,
            )
        assert _directory_snapshot(output) == baseline


def _validate_cancellation_stale_geometry_and_destination_change():
    for cancel_on_call in (1, 2, 3):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary) / "output"
            output.mkdir()
            state, specification, artifact, request = _fixture(output)
            calls = 0

            def cancellation_requested():
                nonlocal calls
                calls += 1
                return calls == cancel_on_call

            _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                    cancellation_requested=cancellation_requested,
                ),
                "transition-dxf-export-cancelled",
            )
            assert calls == cancel_on_call
            assert list(output.iterdir()) == []
            _assert_no_staging(output)

    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)

        def fail_geometry(_artifact, _cancellation_requested):
            raise RuntimeError("injected exact geometry failure")

        error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=fail_geometry,
            ),
            "transition-dxf-exact-geometry-failed",
        )
        assert error.source_code == "RuntimeError"
        assert error.cleanup_complete is True
        assert error.recoverable is True
        assert list(output.iterdir()) == []

        class InjectedGeometryCleanupFailure(RuntimeError):
            code = "exact-geometry-cleanup-failed"
            cleanup_complete = False
            recoverable = False

        def fail_geometry_cleanup(_artifact, _cancellation_requested):
            raise InjectedGeometryCleanupFailure(
                "injected exact geometry cleanup failure"
            )

        cleanup_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=fail_geometry_cleanup,
            ),
            "transition-dxf-exact-geometry-cleanup-failed",
        )
        assert cleanup_error.source_code == "exact-geometry-cleanup-failed"
        assert cleanup_error.cleanup_complete is False
        assert cleanup_error.recoverable is False
        assert list(output.iterdir()) == []

        mismatched = _geometry_receipt(
            artifact,
            exact_result_signature="sha256:" + "1" * 64,
        )
        _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=lambda _artifact, _cancel: mismatched,
            ),
            "invalid-transition-dxf-exact-geometry-receipt",
        )
        assert list(output.iterdir()) == []

        stale = _state(260.0)
        error = _expect_export_error(
            lambda: _export_with_stub(
                stale,
                artifact,
                specification,
                request,
            ),
            "invalid-transition-dxf-export-input",
        )
        assert error.source_code == "stale-exact-validation"
        assert list(output.iterdir()) == []

        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )

        def create_external_collision(candidate, _cancel):
            (output / plan.dxf_filename).write_bytes(b"external actor\n")
            return _geometry_receipt(candidate)

        external = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=create_external_collision,
            ),
            "transition-dxf-export-destination-changed",
        )
        assert external.destination_changed is False
        assert (output / plan.dxf_filename).read_bytes() == b"external actor\n"
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)


def _validate_descriptor_relative_rename_controls():
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        moved = root / "moved-output"
        redirect = root / "redirect"
        output.mkdir()
        redirect.mkdir()
        marker = output / "operator-owned.txt"
        marker.write_text("unchanged", encoding="utf-8")
        baseline = _directory_snapshot(output)
        state, specification, artifact, request = _fixture(output)

        def rename_during_geometry(candidate, _cancel):
            output.rename(moved)
            os.symlink(redirect, output, target_is_directory=True)
            return _geometry_receipt(candidate)

        error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=rename_during_geometry,
            ),
            "transition-dxf-export-destination-changed",
        )
        assert error.destination_changed is True
        assert output.is_symlink()
        assert _directory_snapshot(moved) == baseline
        assert list(redirect.iterdir()) == []
        _assert_no_staging(moved)

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        moved = root / "moved-output"
        redirect = root / "redirect"
        output.mkdir()
        redirect.mkdir()
        marker = output / "operator-owned.txt"
        marker.write_text("unchanged", encoding="utf-8")
        baseline = _directory_snapshot(output)
        state, specification, artifact, request = _fixture(output)
        original_cleanup = adapter._cleanup_transaction
        renamed = False

        def rename_after_cleanup(*args):
            nonlocal renamed
            original_cleanup(*args)
            if not renamed:
                output.rename(moved)
                os.symlink(redirect, output, target_is_directory=True)
                renamed = True

        adapter._cleanup_transaction = rename_after_cleanup
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-destination-changed",
            )
            assert error.destination_changed is True
            assert error.cleanup_complete is True
        finally:
            adapter._cleanup_transaction = original_cleanup
        assert output.is_symlink()
        assert _directory_snapshot(moved) == baseline
        assert list(redirect.iterdir()) == []
        _assert_no_staging(moved)

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        moved = root / "moved-output"
        redirect = root / "redirect"
        output.mkdir()
        redirect.mkdir()
        marker = output / "operator-owned.txt"
        marker.write_text("unchanged", encoding="utf-8")
        baseline = _directory_snapshot(output)
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        final_names = {plan.dxf_filename, plan.manifest_filename}
        original_link = adapter._link_file
        link_calls = 0

        def rename_after_first_link(
            source_directory_descriptor,
            source_name,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal link_calls
            original_link(
                source_directory_descriptor,
                source_name,
                destination_directory_descriptor,
                destination_name,
            )
            if destination_name not in final_names:
                return
            link_calls += 1
            if link_calls == 1:
                output.rename(moved)
                os.symlink(redirect, output, target_is_directory=True)

        adapter._link_file = rename_after_first_link
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-destination-changed",
            )
            assert error.destination_changed is True
            assert error.cleanup_complete is True
        finally:
            adapter._link_file = original_link
        assert output.is_symlink()
        assert _directory_snapshot(moved) == baseline
        assert list(redirect.iterdir()) == []
        _assert_no_staging(moved)


def _validate_mkdir_to_first_open_substitution_is_preserved():
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        working = root / "working"
        output.mkdir()
        working.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        manifest_value = adapter._manifest_bytes(
            plan,
            adapter._sha256_bytes(dxf_value),
        )
        stage_name = adapter._transaction_names(
            plan.dxf_filename,
            plan.manifest_filename,
        )[3]
        stage_path = output / stage_name
        relocated = output / "relocated-invocation-stage"
        original_mkdir = adapter.os.mkdir
        original_atomic_create = getattr(
            adapter,
            "_create_staged_files",
            None,
        )
        injected = False
        foreign_snapshot = None

        def create_foreign_stage(directory_descriptor):
            nonlocal foreign_snapshot, injected
            original_mkdir(
                stage_name,
                0o700,
                dir_fd=directory_descriptor,
            )
            (stage_path / plan.dxf_filename).write_bytes(dxf_value)
            (stage_path / plan.manifest_filename).write_bytes(
                manifest_value
            )
            foreign_snapshot = _staging_snapshot(stage_path)
            injected = True

        def substitute_before_first_open(
            name,
            mode=0o777,
            *,
            dir_fd=None,
        ):
            result = original_mkdir(name, mode, dir_fd=dir_fd)
            if name == stage_name and not injected:
                os.rename(
                    name,
                    relocated.name,
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                create_foreign_stage(dir_fd)
            return result

        def substitute_before_atomic_create(
            directory_descriptor,
            name,
            values,
        ):
            if not injected:
                create_foreign_stage(directory_descriptor)
            return original_atomic_create(
                directory_descriptor,
                name,
                values,
            )

        def arm_substitution(candidate, _cancel):
            adapter.os.mkdir = substitute_before_first_open
            if original_atomic_create is not None:
                adapter._create_staged_files = (
                    substitute_before_atomic_create
                )
            return _geometry_receipt(candidate)

        previous_directory = os.getcwd()
        try:
            os.chdir(working)
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                    builder=arm_substitution,
                ),
                "transition-dxf-export-staging-failed",
            )
        finally:
            os.chdir(previous_directory)
            adapter.os.mkdir = original_mkdir
            if original_atomic_create is not None:
                adapter._create_staged_files = original_atomic_create

        assert injected is True
        assert foreign_snapshot is not None
        assert stage_path.is_dir()
        assert _staging_snapshot(stage_path) == foreign_snapshot
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()
        assert tuple(working.iterdir()) == ()

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert stage_path.is_dir()
        assert _staging_snapshot(stage_path) == foreign_snapshot
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()
        assert tuple(working.iterdir()) == ()


def _validate_preexisting_staging_is_preserved():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        manifest_value = adapter._manifest_bytes(
            plan,
            adapter._sha256_bytes(dxf_value),
        )
        stage_name = adapter._transaction_names(
            plan.dxf_filename,
            plan.manifest_filename,
        )[3]
        stage_path = output / stage_name
        foreign_snapshot = None

        def create_foreign_stage(candidate, _cancel):
            nonlocal foreign_snapshot
            stage_path.mkdir(mode=0o700)
            (stage_path / plan.dxf_filename).write_bytes(dxf_value)
            (stage_path / plan.manifest_filename).write_bytes(
                manifest_value
            )
            foreign_snapshot = _staging_snapshot(stage_path)
            return _geometry_receipt(candidate)

        error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=create_foreign_stage,
            ),
            "transition-dxf-export-staging-failed",
        )
        assert error.source_code == "FileExistsError"
        assert foreign_snapshot is not None
        assert stage_path.is_dir()
        assert _staging_snapshot(stage_path) == foreign_snapshot
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _transaction_artifacts(output) == (stage_name,)
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert stage_path.is_dir()
        assert _staging_snapshot(stage_path) == foreign_snapshot


def _validate_preexisting_transaction_controls_are_preserved():
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        working = root / "working"
        output.mkdir()
        working.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        dxf_sha256 = adapter._sha256_bytes(dxf_value)
        manifest_value = adapter._manifest_bytes(plan, dxf_sha256)
        manifest_sha256 = adapter._sha256_bytes(manifest_value)
        _key, journal_name, _temporary_name, _stage_name = (
            adapter._transaction_names(
                plan.dxf_filename,
                plan.manifest_filename,
            )
        )
        dxf_path = output / plan.dxf_filename
        dxf_path.write_bytes(dxf_value)
        dxf_metadata = dxf_path.stat()
        staged_snapshots = {
            plan.dxf_filename: (
                dxf_metadata.st_dev,
                dxf_metadata.st_ino,
                dxf_metadata.st_mode,
                dxf_metadata.st_size,
                dxf_metadata.st_mtime_ns,
                dxf_sha256,
            ),
            plan.manifest_filename: (
                dxf_metadata.st_dev,
                dxf_metadata.st_ino + 1,
                dxf_metadata.st_mode,
                len(manifest_value),
                dxf_metadata.st_mtime_ns,
                manifest_sha256,
            ),
        }
        journal_path = output / journal_name
        journal_path.write_bytes(
            adapter._transaction_bytes(
                adapter._transaction_document(
                    plan.dxf_filename,
                    dxf_sha256,
                    plan.manifest_filename,
                    manifest_sha256,
                    staged_snapshots,
                )
            )
        )
        foreign_snapshots = {
            dxf_path: _path_snapshot(dxf_path),
            journal_path: _path_snapshot(journal_path),
        }

        previous_directory = os.getcwd()
        try:
            os.chdir(working)
            for _attempt in range(2):
                error = _expect_export_error(
                    lambda: _export_with_stub(
                        state,
                        artifact,
                        specification,
                        request,
                    ),
                    "transition-dxf-export-recovery-failed",
                )
                assert error.source_code == "FileExistsError"
                assert error.destination_changed is True
                assert error.cleanup_complete is False
                assert error.recoverable is False
                assert {
                    path: _path_snapshot(path)
                    for path in foreign_snapshots
                } == foreign_snapshots
                assert not (output / plan.manifest_filename).exists()
                assert tuple(working.iterdir()) == ()
        finally:
            os.chdir(previous_directory)

    for control_kind in ("journal", "temporary"):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary) / "output"
            output.mkdir()
            state, specification, artifact, request = _fixture(output)
            plan = api.prepare_transition_dxf_export(
                state,
                artifact,
                specification,
                request,
            )
            key, journal_name, temporary_name, stage_name = (
                adapter._transaction_names(
                    plan.dxf_filename,
                    plan.manifest_filename,
                )
            )
            name = (
                journal_name
                if control_kind == "journal"
                else temporary_name
            )
            control_path = output / name
            control_path.write_bytes(
                adapter._transaction_bytes(
                    {
                        "schema": (
                            "tracktemplate.transition-dxf.transaction.v1"
                        ),
                        "contract_id": (
                            contract.TRANSITION_DXF_EXPORT_CONTRACT_ID
                        ),
                        "output_set_key": key,
                        "stage_directory": stage_name,
                        "entries": [],
                    }
                )
            )
            foreign_snapshot = _path_snapshot(control_path)
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-recovery-failed",
            )
            assert error.source_code == "FileExistsError"
            assert error.destination_changed is True
            assert error.cleanup_complete is False
            assert error.recoverable is False
            assert _path_snapshot(control_path) == foreign_snapshot
            assert not (output / plan.dxf_filename).exists()
            assert not (output / plan.manifest_filename).exists()


def _validate_staging_identity_races_fail_closed():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        _key, journal_name, temporary_name, _stage_name = (
            adapter._transaction_names(
                plan.dxf_filename,
                plan.manifest_filename,
            )
        )
        journal_path = output / journal_name
        temporary_path = output / temporary_name
        original_link = adapter._link_file
        foreign_snapshot = None

        def substitute_during_journal_binding(
            source_directory_descriptor,
            source_name,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal foreign_snapshot
            original_link(
                source_directory_descriptor,
                source_name,
                destination_directory_descriptor,
                destination_name,
            )
            if destination_name == journal_name:
                temporary_path.write_bytes(b"foreign-control\n")
                foreign_snapshot = _path_snapshot(temporary_path)

        adapter._link_file = substitute_during_journal_binding
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-journal-failed",
            )
        finally:
            adapter._link_file = original_link
        assert foreign_snapshot is not None
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        residue = {
            journal_path: _path_snapshot(journal_path),
            temporary_path: _path_snapshot(temporary_path),
        }
        assert residue[temporary_path] == foreign_snapshot
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert {
            path: _path_snapshot(path)
            for path in residue
        } == residue

    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        manifest_value = adapter._manifest_bytes(
            plan,
            adapter._sha256_bytes(dxf_value),
        )
        stage_name = adapter._transaction_names(
            plan.dxf_filename,
            plan.manifest_filename,
        )[3]
        stage_path = output / stage_name
        original_journal = adapter._create_transaction_journal
        foreign_snapshot = None

        def substitute_during_durable_binding(*args):
            nonlocal foreign_snapshot
            journal_snapshot = original_journal(*args)
            stage_path.mkdir(mode=0o700)
            (stage_path / plan.dxf_filename).write_bytes(dxf_value)
            (stage_path / plan.manifest_filename).write_bytes(
                manifest_value
            )
            foreign_snapshot = _staging_snapshot(stage_path)
            return journal_snapshot

        adapter._create_transaction_journal = (
            substitute_during_durable_binding
        )
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-cleanup-failed",
            )
        finally:
            adapter._create_transaction_journal = original_journal
        assert foreign_snapshot is not None
        assert stage_path.is_dir()
        assert _staging_snapshot(stage_path) == foreign_snapshot
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()
        assert _transaction_artifacts(output) == (stage_name,)

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert _staging_snapshot(stage_path) == foreign_snapshot

    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        original_commit = adapter._commit_staged_files
        original_rmdir = adapter.os.rmdir
        staged_identities = set()

        def inspect_anonymous_commit(
            directory_descriptor,
            staged_files,
            entries,
            output_directory,
            directory_identity,
        ):
            for descriptor, snapshot in staged_files.values():
                metadata = os.fstat(descriptor)
                assert metadata.st_nlink == 0
                assert (metadata.st_dev, metadata.st_ino) == snapshot[:2]
                staged_identities.add(snapshot[:2])
            return original_commit(
                directory_descriptor,
                staged_files,
                entries,
                output_directory,
                directory_identity,
            )

        def reject_directory_removal(*_args, **_kwargs):
            raise AssertionError("anonymous staging must not call rmdir")

        adapter._commit_staged_files = inspect_anonymous_commit
        adapter.os.rmdir = reject_directory_removal
        try:
            receipt = _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )
        finally:
            adapter._commit_staged_files = original_commit
            adapter.os.rmdir = original_rmdir
        assert receipt.disposition == "created"
        assert len(staged_identities) == 2
        _assert_no_staging(output)

    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        manifest_value = adapter._manifest_bytes(
            plan,
            adapter._sha256_bytes(dxf_value),
        )
        stage_name = adapter._transaction_names(
            plan.dxf_filename,
            plan.manifest_filename,
        )[3]
        stage_path = output / stage_name
        original_cleanup = adapter._cleanup_transaction
        foreign_snapshot = None

        def substitute_before_cleanup(*args):
            nonlocal foreign_snapshot
            stage_path.mkdir(mode=0o700)
            (stage_path / plan.dxf_filename).write_bytes(dxf_value)
            (stage_path / plan.manifest_filename).write_bytes(
                manifest_value
            )
            foreign_snapshot = _staging_snapshot(stage_path)
            return original_cleanup(*args)

        adapter._cleanup_transaction = substitute_before_cleanup
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-cleanup-failed",
            )
        finally:
            adapter._cleanup_transaction = original_cleanup
        assert foreign_snapshot is not None
        assert _staging_snapshot(stage_path) == foreign_snapshot
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()
        assert _transaction_artifacts(output) == (stage_name,)

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert _staging_snapshot(stage_path) == foreign_snapshot


def _validate_late_rename_rollback_residue_is_preserved():
    assert hasattr(os, "fork")
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        output = root / "output"
        moved = root / "moved-output"
        redirect = root / "redirect"
        output.mkdir()
        redirect.mkdir()
        marker = output / "operator-owned.txt"
        marker.write_text("unchanged", encoding="utf-8")
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        final_names = {plan.dxf_filename, plan.manifest_filename}
        expected_status = 79
        process_id = os.fork()
        if process_id == 0:
            original_cleanup = adapter._cleanup_transaction
            original_unlink = adapter._unlink_owned_file

            def rename_after_cleanup(*args):
                original_cleanup(*args)
                output.rename(moved)
                os.symlink(redirect, output, target_is_directory=True)

            def interrupt_final_rollback(
                directory_descriptor,
                name,
                expected_snapshot,
            ):
                original_unlink(
                    directory_descriptor,
                    name,
                    expected_snapshot,
                )
                if name in final_names:
                    os._exit(expected_status)

            adapter._cleanup_transaction = rename_after_cleanup
            adapter._unlink_owned_file = interrupt_final_rollback
            try:
                _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                )
            except BaseException:
                os._exit(90)
            os._exit(91)

        waited_process, status = os.waitpid(process_id, 0)
        assert waited_process == process_id
        assert os.WIFEXITED(status), status
        assert os.WEXITSTATUS(status) == expected_status, status
        assert output.is_symlink()
        assert (moved / marker.name).read_text(
            encoding="utf-8"
        ) == "unchanged"
        assert sum(
            int((moved / name).is_file()) for name in final_names
        ) == 1
        assert len(_transaction_artifacts(moved)) == 1

        output.unlink()
        moved.rename(output)
        residue = _regular_file_snapshots(output)
        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert _regular_file_snapshots(output) == residue
        assert marker.read_text(encoding="utf-8") == "unchanged"
        assert len(_transaction_artifacts(output)) == 1


def _interrupt_after_link(
    state,
    artifact,
    specification,
    request,
    link_count,
):
    assert hasattr(os, "fork")
    plan = api.prepare_transition_dxf_export(
        state,
        artifact,
        specification,
        request,
    )
    final_names = {plan.dxf_filename, plan.manifest_filename}
    expected_status = 70 + link_count
    process_id = os.fork()
    if process_id == 0:
        original_link = adapter._link_file
        observed_links = 0

        def interrupt_link(
            source_directory_descriptor,
            source_name,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal observed_links
            original_link(
                source_directory_descriptor,
                source_name,
                destination_directory_descriptor,
                destination_name,
            )
            if destination_name not in final_names:
                return
            observed_links += 1
            if observed_links == link_count:
                os._exit(expected_status)

        adapter._link_file = interrupt_link
        try:
            _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )
        except BaseException:
            os._exit(90)
        os._exit(91)
    waited_process, status = os.waitpid(process_id, 0)
    assert waited_process == process_id
    assert os.WIFEXITED(status), status
    assert os.WEXITSTATUS(status) == expected_status, status


def _validate_interruption_residue_is_preserved():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        _interrupt_after_link(
            state,
            artifact,
            specification,
            request,
            1,
        )
        assert (output / plan.dxf_filename).is_file()
        assert not (output / plan.manifest_filename).exists()
        assert len(_transaction_artifacts(output)) == 1

        residue = _regular_file_snapshots(output)
        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert _regular_file_snapshots(output) == residue

    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        _interrupt_after_link(
            state,
            artifact,
            specification,
            request,
            2,
        )
        residue = _regular_file_snapshots(output)
        assert len(_transaction_artifacts(output)) == 1

        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert recovery_error.recoverable is False
        assert _regular_file_snapshots(output) == residue


def _validate_changed_anonymous_staging_is_discarded():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        original_write = adapter._write_staged_file

        def corrupt_manifest_write(directory_descriptor, name, value):
            return original_write(
                directory_descriptor,
                name,
                b"{}\n" if name.endswith(".json") else value,
            )

        adapter._write_staged_file = corrupt_manifest_write
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "invalid-transition-dxf-export-manifest",
            )
        finally:
            adapter._write_staged_file = original_write
        assert error.destination_changed is False
        assert error.cleanup_complete is True
        assert error.recoverable is True
        assert not (output / plan.dxf_filename).exists()
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)

        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        _assert_no_staging(output)


def _validate_staging_commit_rollback_and_ownership():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        marker = output / "operator-owned.txt"
        marker.write_text("unchanged", encoding="utf-8")
        baseline = _directory_snapshot(output)
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            request,
        )
        final_names = {plan.dxf_filename, plan.manifest_filename}

        original_receipt = adapter._receipt

        def fail_receipt(*_args):
            raise RuntimeError("injected signed-receipt failure")

        adapter._receipt = fail_receipt
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-failed",
            )
            assert error.source_code == "RuntimeError"
            assert error.destination_changed is False
        finally:
            adapter._receipt = original_receipt
        assert _directory_snapshot(output) == baseline
        _assert_no_staging(output)

        original_write = adapter._write_staged_file
        write_calls = 0

        def fail_second_write(directory_descriptor, name, value):
            nonlocal write_calls
            write_calls += 1
            if write_calls == 2:
                raise OSError("injected second staging write failure")
            return original_write(directory_descriptor, name, value)

        adapter._write_staged_file = fail_second_write
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-failed",
            )
            assert error.source_code == "OSError"
        finally:
            adapter._write_staged_file = original_write
        assert _directory_snapshot(output) == baseline
        _assert_no_staging(output)

        original_link = adapter._link_file
        link_calls = 0

        def fail_second_link(
            source_directory_descriptor,
            source_name,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal link_calls
            if destination_name not in final_names:
                return original_link(
                    source_directory_descriptor,
                    source_name,
                    destination_directory_descriptor,
                    destination_name,
                )
            link_calls += 1
            if link_calls == 2:
                raise OSError("injected second commit failure")
            original_link(
                source_directory_descriptor,
                source_name,
                destination_directory_descriptor,
                destination_name,
            )

        adapter._link_file = fail_second_link
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-commit-failed",
            )
            assert error.destination_changed is False
        finally:
            adapter._link_file = original_link
        assert _directory_snapshot(output) == baseline
        _assert_no_staging(output)

        link_calls = 0
        replaced_path = None

        def replace_first_link_then_fail(
            source_directory_descriptor,
            source_name,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal link_calls, replaced_path
            if destination_name not in final_names:
                return original_link(
                    source_directory_descriptor,
                    source_name,
                    destination_directory_descriptor,
                    destination_name,
                )
            link_calls += 1
            if link_calls == 1:
                original_link(
                    source_directory_descriptor,
                    source_name,
                    destination_directory_descriptor,
                    destination_name,
                )
                value = (output / destination_name).read_bytes()
                os.unlink(
                    destination_name,
                    dir_fd=destination_directory_descriptor,
                )
                replacement_descriptor = os.open(
                    destination_name,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | os.O_NOFOLLOW,
                    0o666,
                    dir_fd=destination_directory_descriptor,
                )
                try:
                    adapter._write_all(replacement_descriptor, value)
                    os.fsync(replacement_descriptor)
                finally:
                    os.close(replacement_descriptor)
                replaced_path = output / destination_name
                return
            raise OSError("injected commit failure after replacement")

        adapter._link_file = replace_first_link_then_fail
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-rollback-failed",
            )
            assert error.destination_changed is True
            assert error.recoverable is False
        finally:
            adapter._link_file = original_link
        assert replaced_path is not None and replaced_path.exists()
        assert marker.read_text(encoding="utf-8") == "unchanged"
        assert len(list(output.glob("*.dependency-manifest.json"))) == 0
        residue = _transaction_artifacts(output)
        assert len(residue) == 1, residue
        recovery_error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
            ),
            "transition-dxf-export-recovery-failed",
        )
        assert recovery_error.destination_changed is True
        assert recovery_error.cleanup_complete is False
        assert _transaction_artifacts(output) == residue


def validate():
    _validate_public_contract_and_isolation()
    _validate_plan_signatures_and_stale_inputs()
    _validate_success_manifest_reuse_and_zero_length()
    _validate_destination_and_collision_controls()
    _validate_cancellation_stale_geometry_and_destination_change()
    _validate_descriptor_relative_rename_controls()
    _validate_mkdir_to_first_open_substitution_is_preserved()
    _validate_preexisting_staging_is_preserved()
    _validate_preexisting_transaction_controls_are_preserved()
    _validate_staging_identity_races_fail_closed()
    _validate_late_rename_rollback_residue_is_preserved()
    _validate_interruption_residue_is_preserved()
    _validate_changed_anonymous_staging_is_discarded()
    _validate_staging_commit_rollback_and_ownership()
    print("Phase 6 transition DXF export validation passed")


if __name__ == "__main__":
    validate()
