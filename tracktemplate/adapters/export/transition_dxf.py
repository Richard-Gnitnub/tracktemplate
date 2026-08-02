"""Failure-safe private-development DXF export for one transition."""

import hashlib
import json
import math
import os
import stat

try:
    import fcntl
except ImportError:  # pragma: no cover - rejected by the qualified contract
    fcntl = None

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
_TRANSACTION_SCHEMA_ID = "tracktemplate.transition-dxf.transaction.v1"
_TRANSACTION_JOURNAL_PREFIX = _STAGING_PREFIX + "transaction-"
_TRANSACTION_STAGE_PREFIX = _STAGING_PREFIX + "stage-"

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


def _sha256_descriptor(descriptor):
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    for chunk in iter(lambda: os.read(descriptor, 1024 * 1024), b""):
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


def _require_descriptor_controls():
    required_flags = (
        getattr(os, "O_DIRECTORY", 0),
        getattr(os, "O_NOFOLLOW", 0),
    )
    required_dir_fd = (
        os.link,
        os.mkdir,
        os.open,
        os.rmdir,
        os.stat,
        os.unlink,
    )
    if (
        fcntl is None
        or not all(required_flags)
        or any(item not in os.supports_dir_fd for item in required_dir_fd)
        or os.stat not in os.supports_follow_symlinks
        or os.link not in os.supports_follow_symlinks
    ):
        raise _export_error(
            "unsupported-transition-dxf-export-filesystem",
            "the qualified descriptor-relative filesystem controls are "
            "unavailable",
            recoverable=False,
        )


def _open_output_directory(path, expected_identity):
    _require_descriptor_controls()
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-destination-changed",
            "the output directory changed before it could be bound",
            source_code=type(error).__name__,
            destination_changed=True,
        ) from error
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != expected_identity
        ):
            raise _export_error(
                "transition-dxf-export-destination-changed",
                "the output directory changed before it could be bound",
                destination_changed=True,
            )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise _export_error(
                "transition-dxf-export-transaction-active",
                "another transition DXF transaction owns this directory",
                source_code=type(error).__name__,
            ) from error
        except OSError as error:
            raise _export_error(
                "unsupported-transition-dxf-export-filesystem",
                "the output directory cannot provide the required lock",
                source_code=type(error).__name__,
                recoverable=False,
            ) from error
        _verify_directory_identity(path, expected_identity)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _verify_directory_identity(path, expected_identity):
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-destination-changed",
            "the output directory changed during export",
            source_code=type(error).__name__,
            destination_changed=True,
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
            destination_changed=True,
        )


def _metadata_snapshot(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _file_snapshot(
    directory_descriptor,
    name,
    *,
    error_code="transition-dxf-export-collision",
    description="an output filename",
):
    try:
        metadata = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return None
    except OSError as error:
        raise _export_error(
            error_code,
            "{} cannot be inspected safely".format(description),
            source_code=type(error).__name__,
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise _export_error(
            error_code,
            "{} is not one regular file".format(description),
        )
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(
            name,
            flags,
            dir_fd=directory_descriptor,
        )
    except OSError as error:
        raise _export_error(
            error_code,
            "{} cannot be opened safely".format(description),
            source_code=type(error).__name__,
        ) from error
    try:
        opened_metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_metadata.st_mode)
            or _metadata_snapshot(opened_metadata)
            != _metadata_snapshot(metadata)
        ):
            raise _export_error(
                error_code,
                "{} changed while it was opened".format(description),
            )
        digest = _sha256_descriptor(descriptor)
        final_metadata = os.fstat(descriptor)
        path_metadata = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        if (
            _metadata_snapshot(final_metadata)
            != _metadata_snapshot(opened_metadata)
            or _metadata_snapshot(path_metadata)
            != _metadata_snapshot(opened_metadata)
        ):
            raise _export_error(
                error_code,
                "{} changed while it was read".format(description),
            )
    except OSError as error:
        raise _export_error(
            error_code,
            "{} changed while it was read".format(description),
            source_code=type(error).__name__,
        ) from error
    finally:
        os.close(descriptor)
    return _metadata_snapshot(opened_metadata) + (digest,)


def _target_snapshots(directory_descriptor, dxf_name, manifest_name):
    return (
        _file_snapshot(directory_descriptor, dxf_name),
        _file_snapshot(directory_descriptor, manifest_name),
    )


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


def _write_all(descriptor, value):
    view = memoryview(value)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("descriptor write made no progress")
        view = view[written:]


def _write_staged_file(directory_descriptor, name, value):
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(
        name,
        flags,
        0o666,
        dir_fd=directory_descriptor,
    )
    try:
        _write_all(descriptor, value)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_regular_file(
    directory_descriptor,
    name,
    *,
    error_code,
    description,
):
    snapshot = _file_snapshot(
        directory_descriptor,
        name,
        error_code=error_code,
        description=description,
    )
    if snapshot is None:
        raise _export_error(
            error_code,
            "{} is missing".format(description),
        )
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(
            name,
            flags,
            dir_fd=directory_descriptor,
        )
        try:
            metadata = os.fstat(descriptor)
            if _metadata_snapshot(metadata) != snapshot[:-1]:
                raise _export_error(
                    error_code,
                    "{} changed while it was opened".format(description),
                )
            chunks = []
            for chunk in iter(
                lambda: os.read(descriptor, 1024 * 1024),
                b"",
            ):
                chunks.append(chunk)
            value = b"".join(chunks)
            if _sha256_bytes(value) != snapshot[-1]:
                raise _export_error(
                    error_code,
                    "{} changed while it was read".format(description),
                )
        finally:
            os.close(descriptor)
    except OSError as error:
        raise _export_error(
            error_code,
            "{} cannot be read safely".format(description),
            source_code=type(error).__name__,
        ) from error
    if (
        _file_snapshot(
            directory_descriptor,
            name,
            error_code=error_code,
            description=description,
        )
        != snapshot
    ):
        raise _export_error(
            error_code,
            "{} changed while it was read".format(description),
        )
    return value, snapshot


def _safe_leaf_name(value):
    return (
        isinstance(value, str)
        and value not in ("", ".", "..")
        and os.path.basename(value) == value
        and "\x00" not in value
    )


def _valid_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _transaction_names(dxf_name, manifest_name):
    value = (
        TRANSITION_DXF_EXPORT_CONTRACT_ID
        + "\x00"
        + dxf_name
        + "\x00"
        + manifest_name
    ).encode("utf-8")
    key = _sha256_bytes(value)
    journal_name = _TRANSACTION_JOURNAL_PREFIX + key + ".json"
    return (
        key,
        journal_name,
        journal_name + ".new",
        _TRANSACTION_STAGE_PREFIX + key,
    )


def _transaction_document(
    dxf_name,
    dxf_sha256,
    manifest_name,
    manifest_sha256,
):
    key, _journal, _temporary, stage_name = _transaction_names(
        dxf_name,
        manifest_name,
    )
    return {
        "schema": _TRANSACTION_SCHEMA_ID,
        "contract_id": TRANSITION_DXF_EXPORT_CONTRACT_ID,
        "output_set_key": key,
        "stage_directory": stage_name,
        "entries": [
            {"final_name": dxf_name, "sha256": dxf_sha256},
            {
                "final_name": manifest_name,
                "sha256": manifest_sha256,
            },
        ],
    }


def _transaction_bytes(document):
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


def _validated_transaction(value, dxf_name, manifest_name):
    try:
        document = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the durable transaction journal is malformed",
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    key, _journal, _temporary, stage_name = _transaction_names(
        dxf_name,
        manifest_name,
    )
    expected_keys = {
        "contract_id",
        "entries",
        "output_set_key",
        "schema",
        "stage_directory",
    }
    entries = document.get("entries") if isinstance(document, dict) else None
    if (
        not isinstance(document, dict)
        or set(document) != expected_keys
        or document.get("schema") != _TRANSACTION_SCHEMA_ID
        or document.get("contract_id")
        != TRANSITION_DXF_EXPORT_CONTRACT_ID
        or document.get("output_set_key") != key
        or document.get("stage_directory") != stage_name
        or not isinstance(entries, list)
        or len(entries) != TRANSITION_DXF_EXPORT_FILE_COUNT
        or value != _transaction_bytes(document)
    ):
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the durable transaction journal is outside its contract",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    expected_names = (dxf_name, manifest_name)
    result = []
    for entry, expected_name in zip(entries, expected_names):
        if (
            not isinstance(entry, dict)
            or set(entry) != {"final_name", "sha256"}
            or entry.get("final_name") != expected_name
            or not _safe_leaf_name(entry.get("final_name"))
            or not _valid_sha256(entry.get("sha256"))
        ):
            raise _export_error(
                "transition-dxf-export-recovery-failed",
                "the durable transaction journal has an unsafe entry",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        result.append((entry["final_name"], entry["sha256"]))
    return document, tuple(result)


def _control_snapshot(directory_descriptor, name, description):
    snapshot = _file_snapshot(
        directory_descriptor,
        name,
        error_code="transition-dxf-export-recovery-failed",
        description=description,
    )
    if snapshot is None:
        return None
    try:
        metadata = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "{} changed during inspection".format(description),
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    if (
        metadata.st_uid != os.geteuid()
        or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        or metadata.st_nlink not in (1, 2)
    ):
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "{} ownership is ambiguous".format(description),
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    return snapshot


def _stage_metadata(directory_descriptor, stage_name):
    try:
        metadata = os.stat(
            stage_name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return None
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the transaction staging directory cannot be inspected",
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    ):
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the transaction staging directory ownership is ambiguous",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    return metadata


def _open_stage_directory(
    directory_descriptor,
    stage_name,
    expected_identity=None,
):
    metadata = _stage_metadata(directory_descriptor, stage_name)
    if metadata is None:
        return None
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(
            stage_name,
            flags,
            dir_fd=directory_descriptor,
        )
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the transaction staging directory cannot be opened safely",
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    opened = os.fstat(descriptor)
    identity = (opened.st_dev, opened.st_ino)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or identity != (metadata.st_dev, metadata.st_ino)
        or (expected_identity is not None and identity != expected_identity)
    ):
        os.close(descriptor)
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the transaction staging directory changed during inspection",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    return descriptor


def _create_staging_directory(directory_descriptor, stage_name):
    try:
        os.mkdir(stage_name, 0o700, dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
        stage_descriptor = _open_stage_directory(
            directory_descriptor,
            stage_name,
        )
        metadata = os.fstat(stage_descriptor)
        return stage_descriptor, (metadata.st_dev, metadata.st_ino)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-staging-failed",
            "the owned staging directory could not be created durably",
            source_code=type(error).__name__,
        ) from error


def _cleanup_staging(
    directory_descriptor,
    stage_name,
    entries,
    expected_identity=None,
):
    stage_descriptor = _open_stage_directory(
        directory_descriptor,
        stage_name,
        expected_identity,
    )
    if stage_descriptor is None:
        return
    expected_hashes = dict(entries)
    expected_names = set(expected_hashes)
    try:
        observed_names = set(os.listdir(stage_descriptor))
        if not observed_names.issubset(expected_names):
            raise _export_error(
                "transition-dxf-export-cleanup-failed",
                "the staging directory contains an unowned entry",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        snapshots = {}
        for name in sorted(observed_names):
            snapshot = _file_snapshot(
                stage_descriptor,
                name,
                error_code="transition-dxf-export-cleanup-failed",
                description="a staged transaction file",
            )
            if (
                snapshot is None
                or snapshot[-1] != expected_hashes[name]
            ):
                raise _export_error(
                    "transition-dxf-export-cleanup-failed",
                    "a staged transaction file is not the journal-owned "
                    "content",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
            snapshots[name] = snapshot
        for name in sorted(observed_names):
            _remove_owned_file(
                stage_descriptor,
                name,
                snapshots[name],
                error_code="transition-dxf-export-cleanup-failed",
                description="a staged transaction file",
            )
        os.fsync(stage_descriptor)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the staged transaction files could not be removed",
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error
    finally:
        os.close(stage_descriptor)
    try:
        os.rmdir(stage_name, dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the owned staging directory could not be removed",
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error


def _remove_owned_file(
    directory_descriptor,
    name,
    expected_snapshot,
    *,
    error_code,
    description,
):
    snapshot = _file_snapshot(
        directory_descriptor,
        name,
        error_code=error_code,
        description=description,
    )
    if snapshot != expected_snapshot:
        raise _export_error(
            error_code,
            "{} ownership changed".format(description),
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    try:
        os.unlink(name, dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
    except OSError as error:
        raise _export_error(
            error_code,
            "{} could not be removed durably".format(description),
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error


def _create_transaction_journal(
    directory_descriptor,
    journal_name,
    temporary_name,
    document,
):
    value = _transaction_bytes(document)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    temporary_descriptor = None
    temporary_snapshot = None
    journal_snapshot = None
    try:
        temporary_descriptor = os.open(
            temporary_name,
            flags,
            0o600,
            dir_fd=directory_descriptor,
        )
        _write_all(temporary_descriptor, value)
        os.fsync(temporary_descriptor)
        temporary_metadata = os.fstat(temporary_descriptor)
        temporary_snapshot = (
            _metadata_snapshot(temporary_metadata)
            + (_sha256_bytes(value),)
        )
        os.close(temporary_descriptor)
        temporary_descriptor = None
        os.link(
            temporary_name,
            journal_name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        os.fsync(directory_descriptor)
        journal_snapshot = _control_snapshot(
            directory_descriptor,
            journal_name,
            "the durable transaction journal",
        )
        if (
            journal_snapshot is None
            or journal_snapshot[:2] != temporary_snapshot[:2]
            or journal_snapshot[-1] != temporary_snapshot[-1]
        ):
            raise _export_error(
                "transition-dxf-export-journal-failed",
                "the transaction journal did not retain its identity",
                cleanup_complete=False,
                recoverable=False,
            )
        temporary_link_snapshot = _control_snapshot(
            directory_descriptor,
            temporary_name,
            "the transaction journal staging link",
        )
        _remove_owned_file(
            directory_descriptor,
            temporary_name,
            temporary_link_snapshot,
            error_code="transition-dxf-export-journal-failed",
            description="the transaction journal staging link",
        )
        journal_snapshot = _control_snapshot(
            directory_descriptor,
            journal_name,
            "the durable transaction journal",
        )
        return journal_snapshot
    except Exception as error:
        if temporary_descriptor is not None:
            os.close(temporary_descriptor)
        if isinstance(error, TransitionDxfExportError):
            raise
        raise _export_error(
            "transition-dxf-export-journal-failed",
            "the transaction journal could not be committed durably",
            source_code=type(error).__name__,
            cleanup_complete=False,
        ) from error


def _link_file(
    source_directory_descriptor,
    source_name,
    destination_directory_descriptor,
    destination_name,
):
    os.link(
        source_name,
        destination_name,
        src_dir_fd=source_directory_descriptor,
        dst_dir_fd=destination_directory_descriptor,
        follow_symlinks=False,
    )


def _unlink_owned_file(
    directory_descriptor,
    name,
    expected_snapshot,
):
    snapshot = _file_snapshot(directory_descriptor, name)
    if snapshot != expected_snapshot:
        raise _export_error(
            "transition-dxf-export-rollback-failed",
            "a newly linked output could not be identified for rollback",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    os.unlink(name, dir_fd=directory_descriptor)


def _staged_snapshots(stage_descriptor, entries):
    result = {}
    for name, expected_sha256 in entries:
        snapshot = _file_snapshot(
            stage_descriptor,
            name,
            error_code="invalid-transition-dxf-staged-file",
            description="a staged output",
        )
        if snapshot is None or snapshot[-1] != expected_sha256:
            raise _export_error(
                "invalid-transition-dxf-staged-file",
                "a staged output changed before commit",
            )
        result[name] = snapshot
    return result


def _rollback_partial_commit(
    directory_descriptor,
    stage_descriptor,
    entries,
):
    staged = _staged_snapshots(stage_descriptor, entries)
    linked = []
    for name, expected_sha256 in entries:
        snapshot = _file_snapshot(directory_descriptor, name)
        if snapshot is None:
            continue
        if (
            snapshot[-1] != expected_sha256
            or snapshot[:2] != staged[name][:2]
        ):
            raise _export_error(
                "transition-dxf-export-rollback-failed",
                "a partial output no longer has owned staged identity",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        linked.append((name, snapshot))
    for name, snapshot in reversed(linked):
        _unlink_owned_file(directory_descriptor, name, snapshot)
    os.fsync(directory_descriptor)


def _commit_staged_files(
    directory_descriptor,
    stage_descriptor,
    entries,
    output_directory,
    directory_identity,
):
    try:
        staged = _staged_snapshots(stage_descriptor, entries)
        for name, _expected_sha256 in entries:
            _link_file(
                stage_descriptor,
                name,
                directory_descriptor,
                name,
            )
            os.fsync(directory_descriptor)
            if _file_snapshot(directory_descriptor, name) != staged[name]:
                raise _export_error(
                    "transition-dxf-export-commit-identity-failed",
                    "a committed output is not the owned staged file",
                )
            _verify_directory_identity(
                output_directory,
                directory_identity,
            )
        if tuple(
            _file_snapshot(directory_descriptor, name)
            for name, _digest in entries
        ) != tuple(staged[name] for name, _digest in entries):
            raise _export_error(
                "transition-dxf-export-commit-identity-failed",
                "the committed output set changed before completion",
            )
        os.fsync(directory_descriptor)
        _verify_directory_identity(output_directory, directory_identity)
        return staged
    except Exception as error:
        try:
            _rollback_partial_commit(
                directory_descriptor,
                stage_descriptor,
                entries,
            )
        except Exception as rollback_error:
            raise _export_error(
                "transition-dxf-export-rollback-failed",
                "the staged-file commit failed and rollback was incomplete",
                source_code=str(
                    getattr(error, "code", "") or type(error).__name__
                ),
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            ) from rollback_error
        if isinstance(error, TransitionDxfExportError):
            raise error
        raise _export_error(
            "transition-dxf-export-commit-failed",
            "the staged-file commit failed and was rolled back completely",
            source_code=type(error).__name__,
        ) from error


def _rollback_committed_files(
    directory_descriptor,
    entries,
    expected_snapshots,
):
    observed = {}
    for name, expected_sha256 in entries:
        snapshot = _file_snapshot(
            directory_descriptor,
            name,
            error_code="transition-dxf-export-rollback-failed",
            description="a newly committed output",
        )
        if (
            snapshot is None
            or snapshot != expected_snapshots[name]
            or snapshot[-1] != expected_sha256
        ):
            raise _export_error(
                "transition-dxf-export-rollback-failed",
                "a newly committed output changed before final rollback",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        observed[name] = snapshot
    try:
        for name, _expected_sha256 in reversed(entries):
            _unlink_owned_file(
                directory_descriptor,
                name,
                observed[name],
            )
            os.fsync(directory_descriptor)
    except TransitionDxfExportError:
        raise
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-rollback-failed",
            "the committed output set could not be rolled back durably",
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error


def _create_rollback_controls(
    directory_descriptor,
    journal_name,
    journal_temporary_name,
    stage_name,
    transaction_document,
    entries,
    expected_snapshots,
):
    for name, expected_sha256 in entries:
        snapshot = _file_snapshot(
            directory_descriptor,
            name,
            error_code="transition-dxf-export-rollback-failed",
            description="a newly committed output",
        )
        if (
            snapshot is None
            or snapshot != expected_snapshots[name]
            or snapshot[-1] != expected_sha256
        ):
            raise _export_error(
                "transition-dxf-export-rollback-failed",
                "the committed output set changed before rollback controls "
                "could be established",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )

    stage_descriptor = None
    try:
        journal_snapshot = _create_transaction_journal(
            directory_descriptor,
            journal_name,
            journal_temporary_name,
            transaction_document,
        )
        stage_descriptor, stage_identity = _create_staging_directory(
            directory_descriptor,
            stage_name,
        )
        for name, _expected_sha256 in entries:
            _link_file(
                directory_descriptor,
                name,
                stage_descriptor,
                name,
            )
            os.fsync(stage_descriptor)
            if (
                _file_snapshot(
                    stage_descriptor,
                    name,
                    error_code="transition-dxf-export-rollback-failed",
                    description="a rollback staging link",
                )
                != expected_snapshots[name]
            ):
                raise _export_error(
                    "transition-dxf-export-rollback-failed",
                    "a rollback staging link did not retain owned identity",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
        os.fsync(stage_descriptor)
        return journal_snapshot, stage_identity
    except Exception as error:
        if isinstance(error, TransitionDxfExportError):
            source_code = error.code
            recoverable = error.recoverable
        else:
            source_code = type(error).__name__
            recoverable = False
        raise _export_error(
            "transition-dxf-export-rollback-failed",
            "durable rollback controls could not be established",
            source_code=source_code,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=recoverable,
        ) from error
    finally:
        if stage_descriptor is not None:
            os.close(stage_descriptor)


def _recover_transaction(
    directory_descriptor,
    stage_name,
    entries,
    output_directory,
    directory_identity,
):
    target_snapshots = tuple(
        _file_snapshot(directory_descriptor, name)
        for name, _digest in entries
    )
    present = tuple(snapshot is not None for snapshot in target_snapshots)
    if all(present):
        for snapshot, (_name, expected_sha256) in zip(
            target_snapshots,
            entries,
        ):
            if snapshot[-1] != expected_sha256:
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "a complete interrupted output changed before recovery",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
        os.fsync(directory_descriptor)
        _verify_directory_identity(output_directory, directory_identity)
        _cleanup_staging(directory_descriptor, stage_name, entries)
        return True
    if any(present):
        stage_descriptor = _open_stage_directory(
            directory_descriptor,
            stage_name,
        )
        if stage_descriptor is None:
            raise _export_error(
                "transition-dxf-export-recovery-failed",
                "a partial interrupted output has no ownership evidence",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        try:
            _rollback_partial_commit(
                directory_descriptor,
                stage_descriptor,
                entries,
            )
        finally:
            os.close(stage_descriptor)
        _verify_directory_identity(output_directory, directory_identity)
        _cleanup_staging(directory_descriptor, stage_name, entries)
        return False
    _cleanup_staging(directory_descriptor, stage_name, entries)
    _verify_directory_identity(output_directory, directory_identity)
    return False


def _recover_pending_transaction(
    directory_descriptor,
    dxf_name,
    manifest_name,
    output_directory,
    directory_identity,
):
    _key, journal_name, temporary_name, stage_name = _transaction_names(
        dxf_name,
        manifest_name,
    )
    journal_snapshot = _control_snapshot(
        directory_descriptor,
        journal_name,
        "the durable transaction journal",
    )
    temporary_snapshot = _control_snapshot(
        directory_descriptor,
        temporary_name,
        "the transaction journal staging link",
    )
    if temporary_snapshot is not None:
        if journal_snapshot is None:
            target_snapshots = _target_snapshots(
                directory_descriptor,
                dxf_name,
                manifest_name,
            )
            if _stage_metadata(directory_descriptor, stage_name) is not None:
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "an unpublished journal has ambiguous transaction state",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
            temporary_value, observed_temporary_snapshot = (
                _read_regular_file(
                    directory_descriptor,
                    temporary_name,
                    error_code="transition-dxf-export-recovery-failed",
                    description="the transaction journal staging link",
                )
            )
            if observed_temporary_snapshot != temporary_snapshot:
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "the unpublished journal changed during recovery",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
            _document, temporary_entries = _validated_transaction(
                temporary_value,
                dxf_name,
                manifest_name,
            )
            targets_present = tuple(
                snapshot is not None for snapshot in target_snapshots
            )
            if any(targets_present) and not all(targets_present):
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "an unpublished journal has an incomplete output set",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
            if all(targets_present) and any(
                snapshot[-1] != expected_sha256
                for snapshot, (_name, expected_sha256) in zip(
                    target_snapshots,
                    temporary_entries,
                )
            ):
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "an unpublished journal does not own the complete "
                    "output bytes",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
            try:
                _link_file(
                    directory_descriptor,
                    temporary_name,
                    directory_descriptor,
                    journal_name,
                )
                os.fsync(directory_descriptor)
            except OSError as error:
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "the unpublished journal could not be recovered durably",
                    source_code=type(error).__name__,
                    cleanup_complete=False,
                ) from error
            journal_snapshot = _control_snapshot(
                directory_descriptor,
                journal_name,
                "the durable transaction journal",
            )
            if (
                journal_snapshot is None
                or journal_snapshot[:2] != temporary_snapshot[:2]
                or journal_snapshot[-1] != temporary_snapshot[-1]
            ):
                raise _export_error(
                    "transition-dxf-export-recovery-failed",
                    "the recovered journal did not retain its identity",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
        elif temporary_snapshot[:2] != journal_snapshot[:2]:
            raise _export_error(
                "transition-dxf-export-recovery-failed",
                "the journal staging link has ambiguous ownership",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        _remove_owned_file(
            directory_descriptor,
            temporary_name,
            temporary_snapshot,
            error_code="transition-dxf-export-recovery-failed",
            description="the transaction journal staging link",
        )
    if journal_snapshot is None:
        if _stage_metadata(directory_descriptor, stage_name) is not None:
            raise _export_error(
                "transition-dxf-export-recovery-failed",
                "a staging directory has no durable ownership journal",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        return False
    value, observed_snapshot = _read_regular_file(
        directory_descriptor,
        journal_name,
        error_code="transition-dxf-export-recovery-failed",
        description="the durable transaction journal",
    )
    if observed_snapshot != journal_snapshot:
        raise _export_error(
            "transition-dxf-export-recovery-failed",
            "the durable transaction journal changed during recovery",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    _document, entries = _validated_transaction(
        value,
        dxf_name,
        manifest_name,
    )
    complete = _recover_transaction(
        directory_descriptor,
        stage_name,
        entries,
        output_directory,
        directory_identity,
    )
    _remove_owned_file(
        directory_descriptor,
        journal_name,
        journal_snapshot,
        error_code="transition-dxf-export-recovery-failed",
        description="the durable transaction journal",
    )
    return complete


def _cleanup_transaction(
    directory_descriptor,
    journal_name,
    journal_snapshot,
    stage_name,
    stage_identity,
    entries,
):
    _cleanup_staging(
        directory_descriptor,
        stage_name,
        entries,
        stage_identity,
    )
    _remove_owned_file(
        directory_descriptor,
        journal_name,
        journal_snapshot,
        error_code="transition-dxf-export-cleanup-failed",
        description="the durable transaction journal",
    )


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
    The destination is bound to one locked directory descriptor. Two
    deterministic files are committed through a durable recovery journal;
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
    dxf_value = _dxf_bytes(plan)
    dxf_sha256 = _sha256_bytes(dxf_value)
    manifest_value = _manifest_bytes(plan, dxf_sha256)
    manifest_sha256 = _sha256_bytes(manifest_value)
    entries = (
        (plan.dxf_filename, dxf_sha256),
        (plan.manifest_filename, manifest_sha256),
    )
    (
        _transaction_key,
        journal_name,
        journal_temporary_name,
        stage_name,
    ) = _transaction_names(plan.dxf_filename, plan.manifest_filename)
    directory_descriptor = _open_output_directory(
        output_directory,
        directory_identity,
    )
    try:
        _recover_pending_transaction(
            directory_descriptor,
            plan.dxf_filename,
            plan.manifest_filename,
            output_directory,
            directory_identity,
        )
        initial_snapshots = _target_snapshots(
            directory_descriptor,
            plan.dxf_filename,
            plan.manifest_filename,
        )
        if (initial_snapshots[0] is None) != (
            initial_snapshots[1] is None
        ):
            raise _export_error(
                "transition-dxf-export-collision",
                "only part of the deterministic output set already exists",
            )
        if initial_snapshots[0] is not None:
            expected_hashes = (dxf_sha256, manifest_sha256)
            observed_hashes = tuple(
                item[-1] for item in initial_snapshots
            )
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
                source_code=str(
                    getattr(error, "code", type(error).__name__)
                ),
                cleanup_complete=cleanup_complete,
                recoverable=recoverable,
            ) from error
        geometry_receipt = _validated_geometry_receipt(
            geometry_receipt,
            plan,
        )
        _check_cancellation(cancellation_requested)
        _verify_directory_identity(output_directory, directory_identity)
        if (
            _target_snapshots(
                directory_descriptor,
                plan.dxf_filename,
                plan.manifest_filename,
            )
            != initial_snapshots
        ):
            raise _export_error(
                "transition-dxf-export-destination-changed",
                "the deterministic output filenames changed during "
                "validation",
            )
        if initial_snapshots[0] is not None:
            return _receipt(
                plan,
                geometry_receipt,
                dxf_sha256,
                manifest_sha256,
                "reused",
            )

        transaction_document = _transaction_document(
            plan.dxf_filename,
            dxf_sha256,
            plan.manifest_filename,
            manifest_sha256,
        )
        journal_snapshot = None
        stage_identity = None
        committed_snapshots = None
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
            journal_snapshot = _create_transaction_journal(
                directory_descriptor,
                journal_name,
                journal_temporary_name,
                transaction_document,
            )
            stage_descriptor, stage_identity = (
                _create_staging_directory(
                    directory_descriptor,
                    stage_name,
                )
            )
            try:
                _write_staged_file(
                    stage_descriptor,
                    plan.dxf_filename,
                    dxf_value,
                )
                _write_staged_file(
                    stage_descriptor,
                    plan.manifest_filename,
                    manifest_value,
                )
                os.fsync(stage_descriptor)
                observed_dxf, _dxf_snapshot = _read_regular_file(
                    stage_descriptor,
                    plan.dxf_filename,
                    error_code="invalid-transition-dxf-staged-file",
                    description="the staged DXF",
                )
                observed_manifest, _manifest_snapshot = (
                    _read_regular_file(
                        stage_descriptor,
                        plan.manifest_filename,
                        error_code=(
                            "invalid-transition-dxf-export-manifest"
                        ),
                        description="the staged dependency manifest",
                    )
                )
                _validate_dxf(observed_dxf, plan)
                _validate_manifest(
                    observed_manifest,
                    plan,
                    dxf_sha256,
                )
                _check_cancellation(cancellation_requested)
                _verify_directory_identity(
                    output_directory,
                    directory_identity,
                )
                if (
                    _target_snapshots(
                        directory_descriptor,
                        plan.dxf_filename,
                        plan.manifest_filename,
                    )
                    != initial_snapshots
                ):
                    raise _export_error(
                        "transition-dxf-export-destination-changed",
                        "the deterministic output filenames changed "
                        "before commit",
                    )
                committed_snapshots = _commit_staged_files(
                    directory_descriptor,
                    stage_descriptor,
                    entries,
                    output_directory,
                    directory_identity,
                )
            finally:
                os.close(stage_descriptor)
        except Exception as error:
            operation_error = error

        cleanup_error = None
        if (
            journal_snapshot is not None
            and (
                operation_error is None
                or getattr(operation_error, "cleanup_complete", True)
            )
        ):
            try:
                _cleanup_transaction(
                    directory_descriptor,
                    journal_name,
                    journal_snapshot,
                    stage_name,
                    stage_identity,
                    entries,
                )
            except TransitionDxfExportError as error:
                cleanup_error = error

        if cleanup_error is not None:
            changed = bool(
                cleanup_error.destination_changed
                or operation_error is None
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
                recoverable=cleanup_error.recoverable,
            ) from (operation_error or cleanup_error)
        if operation_error is not None:
            if isinstance(operation_error, TransitionDxfExportError):
                raise operation_error
            raise _export_error(
                "transition-dxf-export-failed",
                "the staged export failed before a complete result was "
                "returned",
                source_code=type(operation_error).__name__,
            ) from operation_error
        if committed_snapshots is not None:
            try:
                _verify_directory_identity(
                    output_directory,
                    directory_identity,
                )
            except TransitionDxfExportError as identity_error:
                try:
                    (
                        rollback_journal_snapshot,
                        rollback_stage_identity,
                    ) = _create_rollback_controls(
                        directory_descriptor,
                        journal_name,
                        journal_temporary_name,
                        stage_name,
                        transaction_document,
                        entries,
                        committed_snapshots,
                    )
                    _rollback_committed_files(
                        directory_descriptor,
                        entries,
                        committed_snapshots,
                    )
                    _cleanup_transaction(
                        directory_descriptor,
                        journal_name,
                        rollback_journal_snapshot,
                        stage_name,
                        rollback_stage_identity,
                        entries,
                    )
                except TransitionDxfExportError as rollback_error:
                    raise _export_error(
                        "transition-dxf-export-rollback-failed",
                        "the output destination changed after commit and "
                        "rollback was incomplete",
                        source_code=identity_error.code,
                        destination_changed=True,
                        cleanup_complete=False,
                        recoverable=False,
                    ) from rollback_error
                raise identity_error
        return result
    finally:
        os.close(directory_descriptor)
