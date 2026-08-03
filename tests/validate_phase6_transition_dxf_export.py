#!/usr/bin/env python3
"""Validate the bounded Phase 6 transition DXF export contract."""

from dataclasses import replace
import errno
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


def _assert_descriptors_closed(descriptors):
    for descriptor in descriptors:
        try:
            os.fstat(descriptor)
        except OSError:
            continue
        raise AssertionError("anonymous staging descriptor remained open")


def _historical_transaction_names(plan):
    value = (
        contract.TRANSITION_DXF_EXPORT_CONTRACT_ID
        + "\x00"
        + plan.dxf_filename
        + "\x00"
        + plan.manifest_filename
    ).encode("utf-8")
    key = _sha256(value)
    journal = ".tracktemplate-transition-dxf-transaction-" + key + ".json"
    return journal, journal + ".new", (
        ".tracktemplate-transition-dxf-stage-" + key
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
    for (
        transition_length_mm,
        expected_shape,
        expected_dxf_sha256,
        expected_manifest_sha256,
    ) in (
        (
            300.0,
            "Wire",
            "6861d0565a737615ec5b242aaa8d2b3ef"
            "d51b0e22aad9d93fb929489a25fd861",
            "16de67625d952e9bb0c7c3f7891b3098"
            "7f78d7c5878a9838999ab0909f131552",
        ),
        (
            0.0,
            "Vertex",
            "7b2757bc3559013a2399df7efe6c2572"
            "1288f8dad56b6cc05d93c2938c86c2b1",
            "8cff21c710de1da266d0a0c590cd90dc"
            "4edf46c37403275c146e2ffe5a9b3e9f",
        ),
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
            assert receipt.dxf_sha256 == expected_dxf_sha256
            assert receipt.manifest_sha256 == expected_manifest_sha256
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
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _directory_snapshot(output) == partial
        (output / plan.dxf_filename).unlink()

        (output / plan.dxf_filename).write_bytes(b"operator DXF\n")
        (output / plan.manifest_filename).write_bytes(b"operator manifest\n")
        complete = _directory_snapshot(output)
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
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _directory_snapshot(output) == complete
        (output / plan.dxf_filename).unlink()
        (output / plan.manifest_filename).unlink()
        assert _directory_snapshot(output) == baseline

        target = root / "operator-target"
        target.write_text("operator symlink target", encoding="utf-8")
        os.symlink(target, output / plan.dxf_filename)
        linked = _directory_snapshot(output)
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
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _directory_snapshot(output) == linked
        assert target.read_text(encoding="utf-8") == "operator symlink target"
        (output / plan.dxf_filename).unlink()

        non_regular = output / plan.dxf_filename
        non_regular.mkdir(mode=0o700)
        foreign_member = non_regular / "operator-owned.txt"
        foreign_member.write_text("unchanged", encoding="utf-8")
        non_regular_snapshot = _staging_snapshot(non_regular)
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
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _staging_snapshot(non_regular) == non_regular_snapshot
        foreign_member.unlink()
        non_regular.rmdir()

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


def _validate_prebind_destination_ambiguity_fails_closed():
    for interval in (
        "removed-before-open",
        "substituted-before-open",
        "substituted-after-lock",
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            output = root / "output"
            moved = root / "moved-output"
            foreign = root / "foreign-output"
            output.mkdir()
            foreign.mkdir()
            state, specification, artifact, request = _fixture(output)
            plan = api.prepare_transition_dxf_export(
                state,
                artifact,
                specification,
                request,
            )
            (output / plan.dxf_filename).write_bytes(
                adapter._dxf_bytes(plan)
            )
            (output / "operator-owned.txt").write_text(
                "original unchanged",
                encoding="utf-8",
            )
            (foreign / "foreign-owned.txt").write_text(
                "foreign unchanged",
                encoding="utf-8",
            )
            original_snapshot = _regular_file_snapshots(output)
            foreign_snapshot = _regular_file_snapshots(foreign)
            original_resolve = adapter._resolve_output_directory
            original_flock = adapter.fcntl.flock
            substituted = False

            def replace_destination(*, install_foreign):
                nonlocal substituted
                output.rename(moved)
                if install_foreign:
                    foreign.rename(output)
                substituted = True

            def resolve_then_replace(value):
                resolved = original_resolve(value)
                if interval == "removed-before-open":
                    replace_destination(install_foreign=False)
                elif interval == "substituted-before-open":
                    replace_destination(install_foreign=True)
                return resolved

            def lock_then_replace(descriptor, operation):
                result = original_flock(descriptor, operation)
                if interval == "substituted-after-lock":
                    replace_destination(install_foreign=True)
                return result

            adapter._resolve_output_directory = resolve_then_replace
            adapter.fcntl.flock = lock_then_replace
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
            finally:
                adapter.fcntl.flock = original_flock
                adapter._resolve_output_directory = original_resolve

            assert substituted
            assert error.destination_changed is True
            assert error.cleanup_complete is False
            assert error.recoverable is False
            assert _regular_file_snapshots(moved) == original_snapshot
            _assert_no_staging(moved)
            if interval == "removed-before-open":
                assert not output.exists()
                assert _regular_file_snapshots(foreign) == foreign_snapshot
                _assert_no_staging(foreign)
            else:
                assert not foreign.exists()
                assert _regular_file_snapshots(output) == foreign_snapshot
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
        (output / plan.dxf_filename).write_bytes(adapter._dxf_bytes(plan))
        before = _regular_file_snapshots(output)
        descriptor = os.open(
            output,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
        )
        adapter.fcntl.flock(
            descriptor,
            adapter.fcntl.LOCK_EX | adapter.fcntl.LOCK_NB,
        )
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-transaction-active",
            )
        finally:
            adapter.fcntl.flock(descriptor, adapter.fcntl.LOCK_UN)
            os.close(descriptor)
        assert error.destination_changed is False
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert _regular_file_snapshots(output) == before
        _assert_no_staging(output)


def _validate_initial_member_substitution_is_reported():
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
        final_path = output / plan.dxf_filename
        foreign_path = output / "foreign-exact.dxf"
        displaced_path = output / "displaced-exact.dxf"
        final_path.write_bytes(dxf_value)
        foreign_path.write_bytes(dxf_value)
        original_open = adapter.os.open
        original_open_output = adapter._open_output_directory
        substituted = False
        displaced_snapshot = None
        replacement_snapshot = None

        def substitute_during_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal displaced_snapshot, replacement_snapshot, substituted
            if (
                not substituted
                and dir_fd is not None
                and path == plan.dxf_filename
            ):
                final_path.rename(displaced_path)
                foreign_path.rename(final_path)
                substituted = True
                displaced_snapshot = _path_snapshot(displaced_path)
                replacement_snapshot = _path_snapshot(final_path)
            return original_open(path, flags, mode, dir_fd=dir_fd)

        def bind_then_install_substitution(path, expected_identity):
            descriptor = original_open_output(path, expected_identity)
            adapter.os.open = substitute_during_open
            return descriptor

        adapter._open_output_directory = bind_then_install_substitution
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-collision",
            )
        finally:
            adapter.os.open = original_open
            adapter._open_output_directory = original_open_output

        assert substituted
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert displaced_snapshot is not None
        assert replacement_snapshot is not None
        assert _path_snapshot(displaced_path) == displaced_snapshot
        assert _path_snapshot(final_path) == replacement_snapshot
        assert not foreign_path.exists()
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)

        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        assert _path_snapshot(displaced_path) == displaced_snapshot
        assert _path_snapshot(final_path) == replacement_snapshot
        assert (output / plan.manifest_filename).is_file()
        _assert_no_staging(output)


def _validate_initial_member_open_failure_is_reported():
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
        dxf_value = adapter._dxf_bytes(plan)
        final_path = output / plan.dxf_filename
        displaced_path = output / "displaced-exact.dxf"
        target_path = root / "foreign-symlink-target.dxf"
        final_path.write_bytes(dxf_value)
        target_path.write_bytes(dxf_value)
        target_snapshot = _path_snapshot(target_path)
        original_open = adapter.os.open
        original_open_output = adapter._open_output_directory
        substituted = False
        displaced_snapshot = None
        symlink_snapshot = None

        def observe_symlink(path):
            target = os.readlink(path)
            metadata = os.lstat(path)
            return (
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_uid,
                metadata.st_gid,
                metadata.st_size,
                metadata.st_mtime_ns,
                metadata.st_ctime_ns,
                target,
            )

        def substitute_during_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal displaced_snapshot, substituted, symlink_snapshot
            if (
                not substituted
                and dir_fd is not None
                and path == plan.dxf_filename
            ):
                final_path.rename(displaced_path)
                os.symlink(target_path, final_path)
                substituted = True
                displaced_snapshot = _path_snapshot(displaced_path)
                symlink_snapshot = observe_symlink(final_path)
            return original_open(path, flags, mode, dir_fd=dir_fd)

        def bind_then_install_substitution(path, expected_identity):
            descriptor = original_open_output(path, expected_identity)
            adapter.os.open = substitute_during_open
            return descriptor

        adapter._open_output_directory = bind_then_install_substitution
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-collision",
            )
        finally:
            adapter.os.open = original_open
            adapter._open_output_directory = original_open_output

        assert substituted
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert displaced_snapshot is not None
        assert symlink_snapshot is not None
        assert _path_snapshot(displaced_path) == displaced_snapshot
        assert observe_symlink(final_path) == symlink_snapshot
        assert _path_snapshot(target_path) == target_snapshot
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)


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
        assert external.destination_changed is True
        assert external.cleanup_complete is False
        assert external.recoverable is False
        assert (output / plan.dxf_filename).read_bytes() == b"external actor\n"
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)


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
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal observed_links
            original_link(
                source_directory_descriptor,
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
        staged_descriptors = []

        def corrupt_manifest_write(directory_descriptor, name, value):
            staged_file = original_write(
                directory_descriptor,
                name,
                b"{}\n" if name.endswith(".json") else value,
            )
            staged_descriptors.append(staged_file[0])
            return staged_file

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
        assert len(staged_descriptors) == 2
        _assert_descriptors_closed(staged_descriptors)
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


def _validate_exact_partial_monotonic_completion():
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        reference_output = root / "reference"
        reference_output.mkdir()
        state, specification, artifact, reference_request = _fixture(
            reference_output
        )
        plan = api.prepare_transition_dxf_export(
            state,
            artifact,
            specification,
            reference_request,
        )
        dxf_value = adapter._dxf_bytes(plan)
        manifest_value = adapter._manifest_bytes(
            plan,
            adapter._sha256_bytes(dxf_value),
        )
        reference_receipt = _export_with_stub(
            state,
            artifact,
            specification,
            reference_request,
        )

        for existing_name, existing_value, missing_name in (
            (
                plan.dxf_filename,
                dxf_value,
                plan.manifest_filename,
            ),
            (
                plan.manifest_filename,
                manifest_value,
                plan.dxf_filename,
            ),
        ):
            output = root / ("partial-" + existing_name.rsplit(".", 1)[-1])
            output.mkdir()
            request = replace(
                reference_request,
                output_directory=str(output),
            )
            existing_path = output / existing_name
            existing_path.write_bytes(existing_value)
            existing_snapshot = _path_snapshot(existing_path)

            receipt = _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )

            assert receipt.disposition == "created"
            assert receipt.result_signature == reference_receipt.result_signature
            assert _path_snapshot(existing_path) == existing_snapshot
            assert (output / plan.dxf_filename).read_bytes() == dxf_value
            assert (
                output / plan.manifest_filename
            ).read_bytes() == manifest_value
            assert (output / missing_name).is_file()
            _assert_no_staging(output)

            complete_snapshot = _regular_file_snapshots(output)
            reused = _export_with_stub(
                state,
                artifact,
                specification,
                request,
            )
            assert reused.disposition == "reused"
            assert _regular_file_snapshots(output) == complete_snapshot


def _validate_inert_historical_controls_are_preserved():
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
        journal_name, temporary_name, stage_name = (
            _historical_transaction_names(plan)
        )
        journal_path = output / journal_name
        temporary_path = output / temporary_name
        stage_path = output / stage_name
        journal_path.write_bytes(b"foreign journal\n")
        temporary_path.write_bytes(b"foreign temporary control\n")
        stage_path.mkdir(mode=0o700)
        (stage_path / plan.dxf_filename).write_bytes(dxf_value)
        (stage_path / plan.manifest_filename).write_bytes(manifest_value)
        controls = {
            journal_path: _path_snapshot(journal_path),
            temporary_path: _path_snapshot(temporary_path),
        }
        stage_snapshot = _staging_snapshot(stage_path)

        created = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )

        assert created.disposition == "created"
        assert {
            path: _path_snapshot(path) for path in controls
        } == controls
        assert _staging_snapshot(stage_path) == stage_snapshot
        assert (output / plan.dxf_filename).read_bytes() == dxf_value
        assert (
            output / plan.manifest_filename
        ).read_bytes() == manifest_value

        complete_snapshot = _regular_file_snapshots(output)
        reused = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert reused.disposition == "reused"
        assert _regular_file_snapshots(output) == complete_snapshot
        assert {
            path: _path_snapshot(path) for path in controls
        } == controls
        assert _staging_snapshot(stage_path) == stage_snapshot


def _validate_monotonic_interruption_recovery():
    for link_count in (1, 2):
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

            _interrupt_after_link(
                state,
                artifact,
                specification,
                request,
                link_count,
            )

            _assert_no_staging(output)
            assert (output / plan.dxf_filename).read_bytes() == dxf_value
            if link_count == 1:
                assert not (output / plan.manifest_filename).exists()
                retained_path = output / plan.dxf_filename
                retained_snapshot = _path_snapshot(retained_path)
                receipt = _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                )
                assert receipt.disposition == "created"
                assert _path_snapshot(retained_path) == retained_snapshot
                assert (
                    output / plan.manifest_filename
                ).read_bytes() == manifest_value
            else:
                assert (
                    output / plan.manifest_filename
                ).read_bytes() == manifest_value
                complete_snapshot = _regular_file_snapshots(output)
                original_fsync = adapter.os.fsync
                failed_sync = False

                def fail_recovery_sync(_descriptor):
                    nonlocal failed_sync
                    failed_sync = True
                    raise OSError(
                        "injected complete-pair durability failure"
                    )

                adapter.os.fsync = fail_recovery_sync
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
                finally:
                    adapter.os.fsync = original_fsync

                assert failed_sync
                assert error.destination_changed is False
                assert error.cleanup_complete is False
                assert error.recoverable is False
                assert _regular_file_snapshots(output) == complete_snapshot

                successful_syncs = 0

                def observe_recovery_sync(descriptor):
                    nonlocal successful_syncs
                    successful_syncs += 1
                    return original_fsync(descriptor)

                adapter.os.fsync = observe_recovery_sync
                try:
                    receipt = _export_with_stub(
                        state,
                        artifact,
                        specification,
                        request,
                    )
                finally:
                    adapter.os.fsync = original_fsync

                assert successful_syncs == 1
                assert receipt.disposition == "reused"
                assert _regular_file_snapshots(output) == complete_snapshot


def _validate_failed_addition_is_recoverable_without_rollback():
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
        dxf_path = output / plan.dxf_filename
        manifest_path = output / plan.manifest_filename
        final_names = {plan.dxf_filename, plan.manifest_filename}
        original_link = adapter._link_file
        link_calls = 0

        def fail_second_link(
            source_directory_descriptor,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal link_calls
            if destination_name in final_names:
                link_calls += 1
                if link_calls == 2:
                    raise OSError("injected second addition failure")
            return original_link(
                source_directory_descriptor,
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
        finally:
            adapter._link_file = original_link

        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is True
        assert dxf_path.is_file()
        assert not manifest_path.exists()
        retained_snapshot = _path_snapshot(dxf_path)
        _assert_no_staging(output)

        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        assert _path_snapshot(dxf_path) == retained_snapshot
        assert manifest_path.is_file()
        _assert_no_staging(output)


def _validate_cancellation_after_addition_is_recoverable():
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
        calls = 0

        def cancellation_requested():
            nonlocal calls
            calls += 1
            return calls == 5

        error = _expect_export_error(
            lambda: _export_with_stub(
                state,
                artifact,
                specification,
                request,
                cancellation_requested=cancellation_requested,
            ),
            "transition-dxf-export-cancelled",
        )
        assert calls == 5
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is True
        dxf_path = output / plan.dxf_filename
        assert dxf_path.is_file()
        assert not (output / plan.manifest_filename).exists()
        retained_snapshot = _path_snapshot(dxf_path)

        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        assert _path_snapshot(dxf_path) == retained_snapshot


def _validate_uncertain_durability_preserves_added_output():
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
        original_link = adapter._link_file
        original_fsync = adapter.os.fsync
        linked = False
        failed = False

        def observe_link(*args):
            nonlocal linked
            result = original_link(*args)
            if args[-1] == plan.dxf_filename:
                linked = True
            return result

        def fail_first_post_link_sync(descriptor):
            nonlocal failed
            if linked and not failed:
                failed = True
                raise OSError("injected directory durability failure")
            return original_fsync(descriptor)

        adapter._link_file = observe_link
        adapter.os.fsync = fail_first_post_link_sync
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
        finally:
            adapter.os.fsync = original_fsync
            adapter._link_file = original_link

        assert linked and failed
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert (output / plan.dxf_filename).is_file()
        assert not (output / plan.manifest_filename).exists()
        _assert_no_staging(output)


def _validate_unsupported_publication_fails_closed():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        original_link = adapter._link_file

        def reject_anonymous_link(*_args):
            raise OSError(
                errno.EOPNOTSUPP,
                "injected unsupported anonymous link",
            )

        adapter._link_file = reject_anonymous_link
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "unsupported-transition-dxf-export-filesystem",
            )
        finally:
            adapter._link_file = original_link

        assert error.destination_changed is False
        assert error.cleanup_complete is True
        assert error.recoverable is False
        assert list(output.iterdir()) == []


def _validate_post_addition_substitution_is_preserved():
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
        original_link = adapter._link_file
        replacement_snapshot = None

        def substitute_first_final(
            source_directory_descriptor,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal replacement_snapshot
            original_link(
                source_directory_descriptor,
                destination_directory_descriptor,
                destination_name,
            )
            if destination_name != plan.dxf_filename:
                return
            value = (output / destination_name).read_bytes()
            os.unlink(
                destination_name,
                dir_fd=destination_directory_descriptor,
            )
            descriptor = os.open(
                destination_name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW,
                0o666,
                dir_fd=destination_directory_descriptor,
            )
            try:
                adapter._write_all(descriptor, value)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            replacement_snapshot = _path_snapshot(
                output / destination_name
            )

        adapter._link_file = substitute_first_final
        try:
            error = _expect_export_error(
                lambda: _export_with_stub(
                    state,
                    artifact,
                    specification,
                    request,
                ),
                "transition-dxf-export-commit-identity-failed",
            )
        finally:
            adapter._link_file = original_link

        replacement_path = output / plan.dxf_filename
        assert replacement_snapshot is not None
        assert _path_snapshot(replacement_path) == replacement_snapshot
        assert not (output / plan.manifest_filename).exists()
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        _assert_no_staging(output)

        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        assert _path_snapshot(replacement_path) == replacement_snapshot
        assert (output / plan.manifest_filename).is_file()


def _validate_rename_after_addition_preserves_output():
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
        original_link = adapter._link_file
        renamed = False

        def rename_after_first_final(
            source_directory_descriptor,
            destination_directory_descriptor,
            destination_name,
        ):
            nonlocal renamed
            result = original_link(
                source_directory_descriptor,
                destination_directory_descriptor,
                destination_name,
            )
            if not renamed and destination_name == plan.dxf_filename:
                output.rename(moved)
                os.symlink(redirect, output, target_is_directory=True)
                renamed = True
            return result

        adapter._link_file = rename_after_first_final
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
        finally:
            adapter._link_file = original_link

        assert renamed
        assert error.destination_changed is True
        assert error.cleanup_complete is False
        assert error.recoverable is False
        assert output.is_symlink()
        assert marker.name in {item.name for item in moved.iterdir()}
        dxf_path = moved / plan.dxf_filename
        assert dxf_path.is_file()
        assert not (moved / plan.manifest_filename).exists()
        retained_snapshot = _path_snapshot(dxf_path)
        assert list(redirect.iterdir()) == []

        output.unlink()
        moved.rename(output)
        recovered = _export_with_stub(
            state,
            artifact,
            specification,
            request,
        )
        assert recovered.disposition == "created"
        assert _path_snapshot(output / plan.dxf_filename) == (
            retained_snapshot
        )
        assert (output / plan.manifest_filename).is_file()
        assert marker.read_text(encoding="utf-8") == "unchanged"


def _validate_anonymous_staging_has_no_pathname_deletion():
    with tempfile.TemporaryDirectory() as temporary:
        output = pathlib.Path(temporary) / "output"
        output.mkdir()
        state, specification, artifact, request = _fixture(output)
        original_link = adapter._link_file
        original_unlink = adapter.os.unlink
        original_rename = adapter.os.rename
        original_replace = adapter.os.replace
        original_rmdir = adapter.os.rmdir
        staged_descriptors = []

        def inspect_anonymous_link(
            source_directory_descriptor,
            destination_directory_descriptor,
            destination_name,
        ):
            metadata = os.fstat(source_directory_descriptor)
            assert metadata.st_nlink == 0
            staged_descriptors.append(source_directory_descriptor)
            return original_link(
                source_directory_descriptor,
                destination_directory_descriptor,
                destination_name,
            )

        def reject_pathname_removal(*_args, **_kwargs):
            raise AssertionError(
                "add-only export must not remove or replace a pathname"
            )

        def install_removal_sentinels(candidate, _cancel):
            adapter.os.unlink = reject_pathname_removal
            adapter.os.rename = reject_pathname_removal
            adapter.os.replace = reject_pathname_removal
            adapter.os.rmdir = reject_pathname_removal
            return _geometry_receipt(candidate)

        adapter._link_file = inspect_anonymous_link
        try:
            receipt = _export_with_stub(
                state,
                artifact,
                specification,
                request,
                builder=install_removal_sentinels,
            )
        finally:
            adapter.os.rmdir = original_rmdir
            adapter.os.replace = original_replace
            adapter.os.rename = original_rename
            adapter.os.unlink = original_unlink
            adapter._link_file = original_link

        assert receipt.disposition == "created"
        assert len(staged_descriptors) == 2
        _assert_descriptors_closed(staged_descriptors)
        _assert_no_staging(output)


def validate():
    _validate_public_contract_and_isolation()
    _validate_plan_signatures_and_stale_inputs()
    _validate_success_manifest_reuse_and_zero_length()
    _validate_destination_and_collision_controls()
    _validate_prebind_destination_ambiguity_fails_closed()
    _validate_initial_member_substitution_is_reported()
    _validate_initial_member_open_failure_is_reported()
    _validate_cancellation_stale_geometry_and_destination_change()
    _validate_exact_partial_monotonic_completion()
    _validate_inert_historical_controls_are_preserved()
    _validate_monotonic_interruption_recovery()
    _validate_failed_addition_is_recoverable_without_rollback()
    _validate_cancellation_after_addition_is_recoverable()
    _validate_uncertain_durability_preserves_added_output()
    _validate_unsupported_publication_fails_closed()
    _validate_post_addition_substitution_is_preserved()
    _validate_rename_after_addition_preserves_output()
    _validate_anonymous_staging_has_no_pathname_deletion()
    _validate_changed_anonymous_staging_is_discarded()
    print("Phase 6 transition DXF export validation passed")


if __name__ == "__main__":
    validate()
