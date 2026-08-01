"""Failure-safe private-development DXF export for one transition."""

import hashlib
import json
import math
import os
import shutil
import stat
import tempfile

from tracktemplate.application.transition_export import (
    TRANSITION_DXF_EXPORT_AUDIT_SCOPE,
    TRANSITION_DXF_EXPORT_COLLISION_POLICY,
    TRANSITION_DXF_EXPORT_CONTRACT_ID,
    TRANSITION_DXF_EXPORT_FORMAT_ID,
    TRANSITION_DXF_EXPORT_LAYER_NAME,
    TRANSITION_DXF_EXPORT_MANIFEST_SCHEMA_ID,
    TRANSITION_DXF_EXPORT_PROJECT_STATUS,
    TransitionDxfExportReceipt,
    prepare_transition_dxf_export,
)
from tracktemplate.application.transition_state import TransitionStateError


TRANSITION_DXF_EXPORT_FILE_COUNT = 2
_DXF_ACAD_VERSION = "AC1015"
_MANIFEST_REVIEW_DATE = "2026-08-01"
_MANIFEST_REVIEWER = "TrackTemplate Phase 6 export control"
_SIGNATURE_PREFIX = "sha256:"
_STAGING_PREFIX = ".tracktemplate-transition-dxf-"

__all__ = (
    "TRANSITION_DXF_EXPORT_FILE_COUNT",
    "TransitionDxfExportError",
    "export_transition_dxf",
)


class TransitionDxfExportError(RuntimeError):
    """Structured failure from the concrete DXF transaction."""

    def __init__(
        self,
        code,
        message,
        *,
        source_code="",
        destination_changed=False,
        cleanup_complete=True,
        recoverable=True,
    ):
        self.code = str(code)
        self.detail = str(message)
        self.source_code = str(source_code)
        self.destination_changed = bool(destination_changed)
        self.cleanup_complete = bool(cleanup_complete)
        self.recoverable = bool(recoverable)
        super().__init__("{}: {}".format(self.code, self.detail))

    def diagnostic(self):
        """Return a path-free, adapter-neutral diagnostic record."""
        return {
            "cleanup_complete": self.cleanup_complete,
            "code": self.code,
            "destination_changed": self.destination_changed,
            "message": self.detail,
            "recoverable": self.recoverable,
            "source_code": self.source_code,
        }


def _export_error(code, message, **details):
    return TransitionDxfExportError(code, message, **details)


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _signature_digest(value):
    if (
        not isinstance(value, str)
        or not value.startswith(_SIGNATURE_PREFIX)
        or len(value) != len(_SIGNATURE_PREFIX) + 64
    ):
        raise _export_error(
            "invalid-transition-dxf-export-signature",
            "an export dependency signature is malformed",
        )
    digest = value[len(_SIGNATURE_PREFIX):]
    if any(character not in "0123456789abcdef" for character in digest):
        raise _export_error(
            "invalid-transition-dxf-export-signature",
            "an export dependency signature is malformed",
        )
    return digest


def _check_cancellation(cancellation_requested):
    if cancellation_requested is None:
        return
    try:
        cancelled = bool(cancellation_requested())
    except Exception as error:
        raise _export_error(
            "transition-dxf-export-cancellation-check-failed",
            "the export cancellation check failed",
            source_code=type(error).__name__,
        ) from error
    if cancelled:
        raise _export_error(
            "transition-dxf-export-cancelled",
            "the transition DXF export was cancelled",
        )


def _resolve_output_directory(value):
    if not os.path.isabs(value):
        raise _export_error(
            "unsafe-transition-dxf-export-destination",
            "the private-development output directory must be absolute",
        )
    normalised = os.path.normpath(value)
    if value != normalised:
        raise _export_error(
            "unsafe-transition-dxf-export-destination",
            "the output directory must use its normalised absolute path",
        )
    resolved = os.path.realpath(normalised)
    if resolved != normalised:
        raise _export_error(
            "unsafe-transition-dxf-export-destination",
            "symbolic-link destination components are not accepted",
        )
    if os.path.dirname(resolved) == resolved:
        raise _export_error(
            "unsafe-transition-dxf-export-destination",
            "a filesystem root cannot be an export destination",
        )
    try:
        metadata = os.lstat(resolved)
    except OSError as error:
        raise _export_error(
            "invalid-transition-dxf-export-destination",
            "the output directory does not exist or cannot be inspected",
            source_code=type(error).__name__,
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise _export_error(
            "invalid-transition-dxf-export-destination",
            "the output destination must be one real directory",
        )
    return resolved, (metadata.st_dev, metadata.st_ino)


def _verify_directory_identity(path, expected_identity):
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-destination-changed",
            "the output directory changed during export",
            source_code=type(error).__name__,
        ) from error
    observed = (metadata.st_dev, metadata.st_ino)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or observed != expected_identity
        or os.path.realpath(path) != path
    ):
        raise _export_error(
            "transition-dxf-export-destination-changed",
            "the output directory changed during export",
        )


def _file_snapshot(path):
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-collision",
            "an output filename cannot be inspected safely",
            source_code=type(error).__name__,
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise _export_error(
            "transition-dxf-export-collision",
            "an output filename is not one regular file",
        )
    try:
        digest = _sha256_path(path)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-collision",
            "an output file cannot be read safely",
            source_code=type(error).__name__,
        ) from error
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        digest,
    )


def _target_snapshots(dxf_path, manifest_path):
    return (_file_snapshot(dxf_path), _file_snapshot(manifest_path))


def _dxf_number(value):
    value = float(value)
    if not math.isfinite(value):
        raise _export_error(
            "invalid-transition-dxf-export-coordinate",
            "DXF coordinates must be finite",
        )
    text = format(value, ".17g")
    return "0" if text in ("-0", "-0.0") else text


def _append_pair(lines, code, value):
    lines.append(str(code))
    lines.append(str(value))


def _dxf_bytes(plan):
    points = plan.exact_result.centreline.points
    lines = []
    _append_pair(lines, 0, "SECTION")
    _append_pair(lines, 2, "HEADER")
    _append_pair(lines, 9, "$ACADVER")
    _append_pair(lines, 1, _DXF_ACAD_VERSION)
    _append_pair(lines, 9, "$INSUNITS")
    _append_pair(lines, 70, 4)
    _append_pair(lines, 9, "$MEASUREMENT")
    _append_pair(lines, 70, 1)
    _append_pair(lines, 0, "ENDSEC")
    _append_pair(lines, 0, "SECTION")
    _append_pair(lines, 2, "TABLES")
    _append_pair(lines, 0, "TABLE")
    _append_pair(lines, 2, "LAYER")
    _append_pair(lines, 70, 1)
    _append_pair(lines, 0, "LAYER")
    _append_pair(lines, 100, "AcDbSymbolTableRecord")
    _append_pair(lines, 100, "AcDbLayerTableRecord")
    _append_pair(lines, 2, TRANSITION_DXF_EXPORT_LAYER_NAME)
    _append_pair(lines, 70, 0)
    _append_pair(lines, 62, 7)
    _append_pair(lines, 6, "CONTINUOUS")
    _append_pair(lines, 0, "ENDTAB")
    _append_pair(lines, 0, "ENDSEC")
    _append_pair(lines, 0, "SECTION")
    _append_pair(lines, 2, "ENTITIES")
    if len(points) == 1:
        point = points[0]
        _append_pair(lines, 0, "POINT")
        _append_pair(lines, 100, "AcDbEntity")
        _append_pair(lines, 8, TRANSITION_DXF_EXPORT_LAYER_NAME)
        _append_pair(lines, 100, "AcDbPoint")
        _append_pair(lines, 10, _dxf_number(point.x_mm))
        _append_pair(lines, 20, _dxf_number(point.y_mm))
        _append_pair(lines, 30, 0)
    else:
        _append_pair(lines, 0, "LWPOLYLINE")
        _append_pair(lines, 100, "AcDbEntity")
        _append_pair(lines, 8, TRANSITION_DXF_EXPORT_LAYER_NAME)
        _append_pair(lines, 100, "AcDbPolyline")
        _append_pair(lines, 90, len(points))
        _append_pair(lines, 70, 0)
        _append_pair(lines, 38, 0)
        for point in points:
            _append_pair(lines, 10, _dxf_number(point.x_mm))
            _append_pair(lines, 20, _dxf_number(point.y_mm))
    _append_pair(lines, 0, "ENDSEC")
    _append_pair(lines, 0, "EOF")
    return ("\n".join(lines) + "\n").encode("ascii")


def _non_copyright_review(subject):
    result = {}
    for area in (
        "registered_designs",
        "unregistered_designs",
        "patents",
        "trade_marks",
    ):
        result[area] = {
            "status": "not-performed",
            "territories": ["GB"],
            "reviewed_on": _MANIFEST_REVIEW_DATE,
            "reviewed_by": _MANIFEST_REVIEWER,
            "evidence": [],
            "notes": (
                "No {} review is claimed for this private-development "
                "{}; project status remains unknown."
            ).format(area.replace("_", " "), subject),
        }
    return result


def _project_status(reason):
    return {
        "status": TRANSITION_DXF_EXPORT_PROJECT_STATUS,
        "reason": reason,
        "reviewed_by": _MANIFEST_REVIEWER,
        "reviewed_on": _MANIFEST_REVIEW_DATE,
        "decision_reference": "D-P6-001",
    }


def _manifest_document(plan, dxf_sha256):
    canonical_digest = plan.canonical_model_sha256
    artifact_digest = _signature_digest(
        plan.exact_result.artifact_signature
    )
    unknown_permissions = {
        "access": "permitted",
        "adaptation": "unknown",
        "production_output": "unknown",
        "redistribution": "unknown",
        "commercial_use": "unknown",
        "publication": "unknown",
    }
    dependencies = [
        {
            "identifier": "tracktemplate:transition-user-design",
            "name": "B16 transition canonical user design",
            "role": "user-input",
            "output_affecting": True,
            "classifications": ["user_design"],
            "source": {
                "creator_or_supplier": "TrackTemplate operator",
                "locator": "canonical-model-sha256:" + canonical_digest,
            },
            "license_expression": "NOASSERTION",
            "permissions": dict(unknown_permissions),
            "conditions": [
                "This output is restricted to private development under "
                "D-P6-001.",
                "No redistribution, commercial, publication or physical-"
                "production permission is inferred from user input.",
            ],
            "contribution_attestation": {
                "status": "missing",
                "reference": (
                    "No per-output data declaration is attached to this "
                    "private-development invocation."
                ),
            },
            "non_copyright_review": _non_copyright_review(
                "user design"
            ),
            "project_status": _project_status(
                "The user-design rights and declared-use permissions have "
                "not been reviewed for output clearance."
            ),
        },
        {
            "identifier": "tracktemplate:transition-dxf-generator-v1",
            "name": "TrackTemplate B16 transition DXF generator",
            "role": "software-source",
            "output_affecting": True,
            "classifications": ["engineering_method"],
            "source": {
                "creator_or_supplier": "TrackTemplate contributors",
                "locator": (
                    "tracktemplate/application/transition_export.py and "
                    "tracktemplate/adapters/export/transition_dxf.py"
                ),
            },
            "license_expression": "GPL-3.0-or-later",
            "permissions": dict(unknown_permissions),
            "conditions": [
                "Program licensing and generated-output status remain "
                "separate under reference/LICENSING_BOUNDARIES.md.",
            ],
            "contribution_attestation": {
                "status": "not-required",
                "reference": (
                    "Existing project source under LICENSE and repository "
                    "contribution controls."
                ),
            },
            "non_copyright_review": _non_copyright_review(
                "generator dependency"
            ),
            "project_status": _project_status(
                "D-P6-001 permits only a private-development writer and "
                "does not clear generated output."
            ),
        },
    ]
    return {
        "schema_version": 1,
        "manifest_id": (
            "tracktemplate:transition-dxf-output:" + artifact_digest
        ),
        "manifest_kind": "output",
        "audit_scope": TRANSITION_DXF_EXPORT_AUDIT_SCOPE,
        "subject": {
            "identifier": (
                "tracktemplate:transition-centreline-dxf:" + artifact_digest
            ),
            "version": "1",
            "description": (
                "Private-development B16 Entry/Exit transition "
                "centreline DXF."
            ),
            "generator": {
                "program": "TrackTemplate",
                "version": plan.request.generator_version,
            },
            "canonical_model_sha256": canonical_digest,
            "artifacts": [
                {
                    "path": plan.dxf_filename,
                    "format": "DXF",
                    "sha256": dxf_sha256,
                }
            ],
        },
        "intended_uses": ["private-development"],
        "dependencies": dependencies,
        "non_copyright_review": _non_copyright_review(
            "generated output"
        ),
        "project_status": _project_status(
            "D-P6-001 authorises private-development export only; no "
            "production-output clearance or project-cleared status exists."
        ),
    }


def _manifest_bytes(plan, dxf_sha256):
    document = _manifest_document(plan, dxf_sha256)
    return (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _dxf_pairs(value):
    try:
        text = value.decode("ascii")
    except UnicodeDecodeError as error:
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF is not ASCII text",
        ) from error
    lines = text.splitlines()
    if not lines or len(lines) % 2:
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF does not contain complete code/value pairs",
        )
    result = []
    for index in range(0, len(lines), 2):
        try:
            code = int(lines[index])
        except ValueError as error:
            raise _export_error(
                "invalid-transition-dxf-output",
                "the staged DXF contains a non-numeric group code",
            ) from error
        result.append((code, lines[index + 1]))
    return tuple(result)


def _section(pairs, name):
    for index, pair in enumerate(pairs[:-1]):
        if pair == (0, "SECTION") and pairs[index + 1] == (2, name):
            for end in range(index + 2, len(pairs)):
                if pairs[end] == (0, "ENDSEC"):
                    return pairs[index + 2:end]
    raise _export_error(
        "invalid-transition-dxf-output",
        "the staged DXF is missing its {} section".format(name),
    )


def _header_value(header, name):
    for index, pair in enumerate(header[:-1]):
        if pair == (9, name):
            return header[index + 1]
    raise _export_error(
        "invalid-transition-dxf-output",
        "the staged DXF is missing header variable {}".format(name),
    )


def _validate_dxf(value, plan):
    if value != _dxf_bytes(plan):
        raise _export_error(
            "non-deterministic-transition-dxf-output",
            "the staged DXF differs from its deterministic contract",
        )
    pairs = _dxf_pairs(value)
    if pairs[-1] != (0, "EOF"):
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF has no EOF marker",
        )
    header = _section(pairs, "HEADER")
    if _header_value(header, "$ACADVER") != (1, _DXF_ACAD_VERSION):
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF has the wrong format version",
        )
    if _header_value(header, "$INSUNITS") != (70, "4"):
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF does not declare millimetres",
        )
    if _header_value(header, "$MEASUREMENT") != (70, "1"):
        raise _export_error(
            "invalid-transition-dxf-output",
            "the staged DXF does not declare metric measurement",
        )

    entities = _section(pairs, "ENTITIES")
    expected_points = tuple(
        (point.x_mm, point.y_mm)
        for point in plan.exact_result.centreline.points
    )
    if len(expected_points) == 1:
        if not entities or entities[0] != (0, "POINT"):
            raise _export_error(
                "invalid-transition-dxf-output",
                "a zero-length transition must export one DXF point",
            )
        coordinates = {}
        for code, raw_value in entities:
            if code in (10, 20, 30):
                coordinates[code] = float(raw_value)
        observed = (
            coordinates.get(10),
            coordinates.get(20),
            coordinates.get(30),
        )
        if observed != (expected_points[0][0], expected_points[0][1], 0.0):
            raise _export_error(
                "invalid-transition-dxf-output",
                "the DXF point changed the exact centreline coordinate",
            )
        return

    if not entities or entities[0] != (0, "LWPOLYLINE"):
        raise _export_error(
            "invalid-transition-dxf-output",
            "a non-zero transition must export one lightweight polyline",
        )
    vertex_count = next(
        (int(value) for code, value in entities if code == 90),
        None,
    )
    flags = next(
        (int(value) for code, value in entities if code == 70),
        None,
    )
    x_values = [float(value) for code, value in entities if code == 10]
    y_values = [float(value) for code, value in entities if code == 20]
    observed_points = tuple(zip(x_values, y_values))
    if vertex_count != len(expected_points) or flags != 0:
        raise _export_error(
            "invalid-transition-dxf-output",
            "the DXF polyline changed centreline topology",
        )
    if observed_points != expected_points:
        raise _export_error(
            "invalid-transition-dxf-output",
            "the DXF polyline changed an ordered centreline coordinate",
        )


def _validate_manifest(value, plan, dxf_sha256):
    expected = _manifest_document(plan, dxf_sha256)
    try:
        observed = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _export_error(
            "invalid-transition-dxf-export-manifest",
            "the staged dependency manifest is not valid UTF-8 JSON",
        ) from error
    if observed != expected or value != _manifest_bytes(plan, dxf_sha256):
        raise _export_error(
            "invalid-transition-dxf-export-manifest",
            "the staged dependency manifest differs from its contract",
        )
    if (
        observed.get("intended_uses") != ["private-development"]
        or observed.get("project_status", {}).get("status")
        != TRANSITION_DXF_EXPORT_PROJECT_STATUS
    ):
        raise _export_error(
            "invalid-transition-dxf-export-manifest",
            "the dependency manifest attempted to expand output authority",
        )


def _write_staged_file(path, value):
    with open(path, "xb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def _link_file(source, destination):
    os.link(source, destination, follow_symlinks=False)


def _unlink_owned_file(path, expected_snapshot):
    snapshot = _file_snapshot(path)
    if snapshot != expected_snapshot:
        raise _export_error(
            "transition-dxf-export-rollback-failed",
            "a newly linked output could not be identified for rollback",
            destination_changed=True,
            recoverable=False,
        )
    os.unlink(path)


def _commit_staged_files(entries):
    linked = []
    try:
        for staged_path, final_path, expected_sha256 in entries:
            staged_snapshot = _file_snapshot(staged_path)
            if (
                staged_snapshot is None
                or staged_snapshot[-1] != expected_sha256
            ):
                raise _export_error(
                    "invalid-transition-dxf-staged-file",
                    "a staged output changed before commit",
                )
            _link_file(staged_path, final_path)
            linked.append((final_path, staged_snapshot))
            if _file_snapshot(final_path) != staged_snapshot:
                raise _export_error(
                    "transition-dxf-export-commit-identity-failed",
                    "a committed output is not the owned staged file",
                )
    except Exception as error:
        rollback_errors = []
        for final_path, expected_snapshot in reversed(linked):
            try:
                _unlink_owned_file(final_path, expected_snapshot)
            except Exception as rollback_error:
                rollback_errors.append(rollback_error)
        if rollback_errors:
            raise _export_error(
                "transition-dxf-export-rollback-failed",
                "the staged-file commit failed and rollback was incomplete",
                source_code=type(error).__name__,
                destination_changed=True,
                recoverable=False,
            ) from error
        raise _export_error(
            "transition-dxf-export-commit-failed",
            "the staged-file commit failed and was rolled back completely",
            source_code=type(error).__name__,
        ) from error


def _cleanup_staging(
    staging_directory,
    output_directory,
    expected_identity,
):
    if not staging_directory:
        return
    resolved = os.path.realpath(staging_directory)
    if (
        os.path.dirname(resolved) != output_directory
        or not os.path.basename(resolved).startswith(_STAGING_PREFIX)
    ):
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the staging directory identity became ambiguous",
            cleanup_complete=False,
            recoverable=False,
        )
    try:
        metadata = os.lstat(staging_directory)
    except FileNotFoundError:
        return
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the staging directory could not be inspected",
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or (metadata.st_dev, metadata.st_ino) != expected_identity
    ):
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the staging directory is no longer the owned directory",
            cleanup_complete=False,
            recoverable=False,
        )
    try:
        shutil.rmtree(resolved)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the owned staging directory could not be removed",
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error


def _default_geometry_builder(artifact, cancellation_requested):
    from tracktemplate.adapters.freecad.transition_exact import (
        build_transition_exact_geometry,
    )

    return build_transition_exact_geometry(
        artifact,
        cancellation_requested=cancellation_requested,
    )


def _validated_geometry_receipt(receipt, plan):
    expected = plan.exact_result
    fields = (
        ("source_signature", expected.source_signature),
        ("exact_artifact_signature", expected.artifact_signature),
        ("exact_result_signature", expected.result_signature),
        ("domain_id", expected.centreline.domain_id),
        ("frame_id", expected.centreline.frame_id),
        ("length_unit", expected.centreline.length_unit),
    )
    if any(getattr(receipt, name, None) != value for name, value in fields):
        raise _export_error(
            "invalid-transition-dxf-exact-geometry-receipt",
            "the exact-geometry receipt does not match the export plan",
        )
    expected_shape_type = (
        "Vertex" if len(expected.centreline.points) == 1 else "Wire"
    )
    if getattr(receipt, "shape_type", None) != expected_shape_type:
        raise _export_error(
            "invalid-transition-dxf-exact-geometry-receipt",
            "the exact-geometry receipt has the wrong topology",
        )
    _signature_digest(getattr(receipt, "geometry_signature", None))
    return receipt


def _receipt(plan, geometry_receipt, dxf_sha256, manifest_sha256, disposition):
    return TransitionDxfExportReceipt(
        contract_id=TRANSITION_DXF_EXPORT_CONTRACT_ID,
        source_signature=plan.source_signature,
        exact_result_signature=plan.exact_result.result_signature,
        geometry_signature=geometry_receipt.geometry_signature,
        dxf_filename=plan.dxf_filename,
        dxf_sha256=dxf_sha256,
        manifest_filename=plan.manifest_filename,
        manifest_sha256=manifest_sha256,
        project_status=TRANSITION_DXF_EXPORT_PROJECT_STATUS,
        disposition=disposition,
        cleanup_complete=True,
    )


def export_transition_dxf(
    state,
    artifact,
    exact_specification,
    request,
    cancellation_requested=None,
):
    """Validate, stage and commit one private-development DXF output set.

    The complete exact-stage dependency is checked before filesystem work.
    The destination must be an existing normalised absolute directory with no
    symbolic-link component. Two deterministic files are created together;
    identical existing files may be reused, but nothing is overwritten.
    """
    if cancellation_requested is not None and not callable(
        cancellation_requested
    ):
        raise TypeError("cancellation_requested must be callable or None")
    try:
        plan = prepare_transition_dxf_export(
            state,
            artifact,
            exact_specification,
            request,
        )
    except TransitionStateError as error:
        raise _export_error(
            "invalid-transition-dxf-export-input",
            "the transition export input is invalid or stale",
            source_code=error.code,
        ) from error

    output_directory, directory_identity = _resolve_output_directory(
        plan.request.output_directory
    )
    dxf_path = os.path.join(output_directory, plan.dxf_filename)
    manifest_path = os.path.join(
        output_directory,
        plan.manifest_filename,
    )
    dxf_value = _dxf_bytes(plan)
    dxf_sha256 = _sha256_bytes(dxf_value)
    manifest_value = _manifest_bytes(plan, dxf_sha256)
    manifest_sha256 = _sha256_bytes(manifest_value)
    initial_snapshots = _target_snapshots(dxf_path, manifest_path)
    if (initial_snapshots[0] is None) != (initial_snapshots[1] is None):
        raise _export_error(
            "transition-dxf-export-collision",
            "only part of the deterministic output set already exists",
        )
    if initial_snapshots[0] is not None:
        expected_hashes = (dxf_sha256, manifest_sha256)
        observed_hashes = tuple(item[-1] for item in initial_snapshots)
        if observed_hashes != expected_hashes:
            raise _export_error(
                "transition-dxf-export-collision",
                "existing output is not byte-identical and cannot be "
                "overwritten",
            )

    _check_cancellation(cancellation_requested)
    try:
        geometry_receipt = _default_geometry_builder(
            artifact,
            cancellation_requested,
        )
    except TransitionDxfExportError:
        raise
    except Exception as error:
        cleanup_complete = getattr(error, "cleanup_complete", True)
        recoverable = getattr(error, "recoverable", True)
        if not isinstance(cleanup_complete, bool):
            cleanup_complete = False
        if not isinstance(recoverable, bool):
            recoverable = False
        raise _export_error(
            (
                "transition-dxf-exact-geometry-failed"
                if cleanup_complete
                else "transition-dxf-exact-geometry-cleanup-failed"
            ),
            (
                "transient exact geometry rejected the export"
                if cleanup_complete
                else "transient exact geometry cleanup was incomplete"
            ),
            source_code=str(getattr(error, "code", type(error).__name__)),
            cleanup_complete=cleanup_complete,
            recoverable=recoverable,
        ) from error
    geometry_receipt = _validated_geometry_receipt(
        geometry_receipt,
        plan,
    )
    _check_cancellation(cancellation_requested)
    _verify_directory_identity(output_directory, directory_identity)
    if _target_snapshots(dxf_path, manifest_path) != initial_snapshots:
        raise _export_error(
            "transition-dxf-export-destination-changed",
            "the deterministic output filenames changed during validation",
        )
    if initial_snapshots[0] is not None:
        return _receipt(
            plan,
            geometry_receipt,
            dxf_sha256,
            manifest_sha256,
            "reused",
        )

    staging_directory = ""
    staging_identity = None
    operation_error = None
    result = None
    try:
        result = _receipt(
            plan,
            geometry_receipt,
            dxf_sha256,
            manifest_sha256,
            "created",
        )
        staging_directory = tempfile.mkdtemp(
            prefix=_STAGING_PREFIX,
            dir=output_directory,
        )
        staging_metadata = os.lstat(staging_directory)
        staging_identity = (
            staging_metadata.st_dev,
            staging_metadata.st_ino,
        )
        staged_dxf = os.path.join(
            staging_directory,
            plan.dxf_filename,
        )
        staged_manifest = os.path.join(
            staging_directory,
            plan.manifest_filename,
        )
        _write_staged_file(staged_dxf, dxf_value)
        _write_staged_file(staged_manifest, manifest_value)
        with open(staged_dxf, "rb") as stream:
            observed_dxf = stream.read()
        with open(staged_manifest, "rb") as stream:
            observed_manifest = stream.read()
        _validate_dxf(observed_dxf, plan)
        _validate_manifest(observed_manifest, plan, dxf_sha256)
        _check_cancellation(cancellation_requested)
        _verify_directory_identity(output_directory, directory_identity)
        if _target_snapshots(dxf_path, manifest_path) != initial_snapshots:
            raise _export_error(
                "transition-dxf-export-destination-changed",
                "the deterministic output filenames changed before commit",
            )
        _commit_staged_files(
            (
                (staged_dxf, dxf_path, dxf_sha256),
                (
                    staged_manifest,
                    manifest_path,
                    manifest_sha256,
                ),
            )
        )
    except Exception as error:
        operation_error = error

    cleanup_error = None
    try:
        _cleanup_staging(
            staging_directory,
            output_directory,
            staging_identity,
        )
    except TransitionDxfExportError as error:
        cleanup_error = error

    if cleanup_error is not None:
        changed = bool(
            operation_error is None
            or getattr(operation_error, "destination_changed", False)
        )
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            cleanup_error.detail,
            source_code=str(
                getattr(operation_error, "code", "")
                or cleanup_error.source_code
            ),
            destination_changed=changed,
            cleanup_complete=False,
            recoverable=not changed,
        ) from (operation_error or cleanup_error)
    if operation_error is not None:
        if isinstance(operation_error, TransitionDxfExportError):
            raise operation_error
        raise _export_error(
            "transition-dxf-export-failed",
            "the staged export failed before a complete result was returned",
            source_code=type(operation_error).__name__,
        ) from operation_error
    return result
