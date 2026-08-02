"""Failure-safe private-development DXF export for one transition."""

import ctypes
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
_TRANSACTION_SCHEMA_ID = "tracktemplate.transition-dxf.transaction.v2"
_TRANSACTION_JOURNAL_PREFIX = _STAGING_PREFIX + "transaction-"
_TRANSACTION_STAGE_PREFIX = _STAGING_PREFIX + "stage-"
# Linux linkat flag used by the qualified Linux x86_64 profile.
_AT_EMPTY_PATH = 0x1000

try:
    _LINKAT = ctypes.CDLL(None, use_errno=True).linkat
except AttributeError:  # pragma: no cover - rejected by the host contract
    _LINKAT = None
else:
    _LINKAT.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    )
    _LINKAT.restype = ctypes.c_int

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
        getattr(os, "O_TMPFILE", 0),
    )
    required_dir_fd = (
        os.link,
        os.open,
        os.stat,
        os.unlink,
    )
    if (
        fcntl is None
        or _LINKAT is None
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


def _descriptor_snapshot(
    descriptor,
    *,
    error_code,
    description,
    expected_identity=None,
    expected_link_count=None,
):
    try:
        opened = os.fstat(descriptor)
        identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (
                expected_identity is not None
                and identity != expected_identity
            )
            or (
                expected_link_count is not None
                and opened.st_nlink != expected_link_count
            )
        ):
            raise _export_error(
                error_code,
                "{} ownership is ambiguous".format(description),
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        digest = _sha256_descriptor(descriptor)
        final = os.fstat(descriptor)
        if (
            _metadata_snapshot(final) != _metadata_snapshot(opened)
            or (
                expected_link_count is not None
                and final.st_nlink != expected_link_count
            )
        ):
            raise _export_error(
                error_code,
                "{} changed while it was read".format(description),
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
    except OSError as error:
        raise _export_error(
            error_code,
            "{} cannot be inspected safely".format(description),
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    return _metadata_snapshot(opened) + (digest,)


def _read_staged_descriptor(descriptor, expected_snapshot, description):
    snapshot = _descriptor_snapshot(
        descriptor,
        error_code="invalid-transition-dxf-staged-file",
        description=description,
        expected_identity=expected_snapshot[:2],
        expected_link_count=0,
    )
    if snapshot != expected_snapshot:
        raise _export_error(
            "invalid-transition-dxf-staged-file",
            "{} changed before validation".format(description),
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    os.lseek(descriptor, 0, os.SEEK_SET)
    return b"".join(
        iter(lambda: os.read(descriptor, 1024 * 1024), b"")
    )


def _write_staged_file(directory_descriptor, name, value):
    # O_EXCL would prevent a later linkat publication of an O_TMPFILE inode.
    flags = (
        os.O_RDWR
        | os.O_TMPFILE
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = None
    try:
        descriptor = os.open(
            ".",
            flags,
            0o666,
            dir_fd=directory_descriptor,
        )
        created = os.fstat(descriptor)
        identity = (created.st_dev, created.st_ino)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 0:
            raise _export_error(
                "transition-dxf-export-staging-failed",
                "an anonymous staging file was not created with exclusive "
                "ownership",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        _write_all(descriptor, value)
        os.fsync(descriptor)
        snapshot = _descriptor_snapshot(
            descriptor,
            error_code="transition-dxf-export-staging-failed",
            description="the anonymous staged {}".format(name),
            expected_identity=identity,
            expected_link_count=0,
        )
        if snapshot[-1] != _sha256_bytes(value):
            raise _export_error(
                "transition-dxf-export-staging-failed",
                "an anonymous staging file changed while it was written",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        return descriptor, snapshot
    except Exception as error:
        if descriptor is not None:
            os.close(descriptor)
        if isinstance(error, TransitionDxfExportError):
            raise
        raise _export_error(
            "transition-dxf-export-staging-failed",
            "an anonymous staging file could not be created durably",
            source_code=type(error).__name__,
            recoverable=False,
        ) from error


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
    staged_snapshots,
):
    key, _journal, _temporary, _legacy_stage = _transaction_names(
        dxf_name,
        manifest_name,
    )
    return {
        "schema": _TRANSACTION_SCHEMA_ID,
        "contract_id": TRANSITION_DXF_EXPORT_CONTRACT_ID,
        "output_set_key": key,
        "staging": "anonymous-regular-files",
        "entries": [
            {
                "final_name": dxf_name,
                "sha256": dxf_sha256,
                "staged_snapshot": list(staged_snapshots[dxf_name]),
            },
            {
                "final_name": manifest_name,
                "sha256": manifest_sha256,
                "staged_snapshot": list(
                    staged_snapshots[manifest_name]
                ),
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


def _path_metadata(directory_descriptor, name, description):
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
            "transition-dxf-export-recovery-failed",
            "{} cannot be inspected".format(description),
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        ) from error
    return metadata


def _ensure_no_legacy_stage(
    directory_descriptor,
    legacy_stage_name,
    *,
    error_code,
):
    if (
        _path_metadata(
            directory_descriptor,
            legacy_stage_name,
            "the legacy staging pathname",
        )
        is not None
    ):
        raise _export_error(
            error_code,
            "a legacy staging pathname exists without creation-bound "
            "ownership",
            source_code="FileExistsError",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )


def _reject_preexisting_transaction_controls(
    directory_descriptor,
    journal_name,
    temporary_name,
    legacy_stage_name,
):
    controls = (
        (journal_name, "the durable transaction journal"),
        (temporary_name, "the transaction journal staging link"),
        (legacy_stage_name, "the legacy staging pathname"),
    )
    for name, description in controls:
        if _path_metadata(
            directory_descriptor,
            name,
            description,
        ) is not None:
            raise _export_error(
                "transition-dxf-export-recovery-failed",
                "{} exists without creation-bound ownership".format(
                    description
                ),
                source_code="FileExistsError",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )


def _close_staged_files(staged_files):
    close_error = None
    for descriptor, _snapshot in staged_files.values():
        try:
            os.close(descriptor)
        except OSError as error:
            close_error = close_error or error
    staged_files.clear()
    if close_error is not None:
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "an anonymous staging descriptor could not be closed",
            source_code=type(close_error).__name__,
            cleanup_complete=False,
            recoverable=False,
        ) from close_error


def _create_staged_files(
    directory_descriptor,
    legacy_stage_name,
    values,
):
    staged_files = {}
    try:
        _ensure_no_legacy_stage(
            directory_descriptor,
            legacy_stage_name,
            error_code="transition-dxf-export-staging-failed",
        )
        for name, value in values:
            _ensure_no_legacy_stage(
                directory_descriptor,
                legacy_stage_name,
                error_code="transition-dxf-export-staging-failed",
            )
            staged_files[name] = _write_staged_file(
                directory_descriptor,
                name,
                value,
            )
        _ensure_no_legacy_stage(
            directory_descriptor,
            legacy_stage_name,
            error_code="transition-dxf-export-staging-failed",
        )
        return staged_files
    except Exception as error:
        try:
            _close_staged_files(staged_files)
        except TransitionDxfExportError as cleanup_error:
            raise _export_error(
                "transition-dxf-export-cleanup-failed",
                "anonymous staging failed and descriptor cleanup was "
                "incomplete",
                source_code=str(
                    getattr(error, "code", "")
                    or type(error).__name__
                ),
                destination_changed=bool(
                    getattr(error, "destination_changed", False)
                ),
                cleanup_complete=False,
                recoverable=False,
            ) from cleanup_error
        raise


def _staged_file_snapshots(staged_files, *, expected_link_count):
    snapshots = {}
    for name, (descriptor, expected_snapshot) in staged_files.items():
        snapshot = _descriptor_snapshot(
            descriptor,
            error_code="invalid-transition-dxf-staged-file",
            description="the anonymous staged {}".format(name),
            expected_identity=expected_snapshot[:2],
            expected_link_count=expected_link_count,
        )
        if snapshot != expected_snapshot:
            raise _export_error(
                "invalid-transition-dxf-staged-file",
                "an anonymous staged output changed before commit",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        snapshots[name] = snapshot
    return snapshots


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
        os.O_RDWR
        | os.O_TMPFILE
        | getattr(os, "O_CLOEXEC", 0)
    )
    journal_descriptor = None
    journal_linked = False
    try:
        for name, description in (
            (journal_name, "the durable transaction journal"),
            (temporary_name, "the transaction journal staging link"),
        ):
            if _path_metadata(
                directory_descriptor,
                name,
                description,
            ) is not None:
                raise _export_error(
                    "transition-dxf-export-journal-failed",
                    "{} exists without creation-bound ownership".format(
                        description
                    ),
                    source_code="FileExistsError",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )
        journal_descriptor = os.open(
            ".",
            flags,
            0o600,
            dir_fd=directory_descriptor,
        )
        created = os.fstat(journal_descriptor)
        identity = (created.st_dev, created.st_ino)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 0:
            raise _export_error(
                "transition-dxf-export-journal-failed",
                "the interruption journal was not created with exclusive "
                "ownership",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        _write_all(journal_descriptor, value)
        os.fsync(journal_descriptor)
        anonymous_snapshot = _descriptor_snapshot(
            journal_descriptor,
            error_code="transition-dxf-export-journal-failed",
            description="the anonymous interruption journal",
            expected_identity=identity,
            expected_link_count=0,
        )
        if anonymous_snapshot[-1] != _sha256_bytes(value):
            raise _export_error(
                "transition-dxf-export-journal-failed",
                "the interruption journal changed while it was written",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        _link_file(
            journal_descriptor,
            None,
            directory_descriptor,
            journal_name,
        )
        journal_linked = True
        os.fsync(directory_descriptor)
        linked_snapshot = _descriptor_snapshot(
            journal_descriptor,
            error_code="transition-dxf-export-journal-failed",
            description="the linked interruption journal",
            expected_identity=identity,
            expected_link_count=1,
        )
        journal_metadata = _path_metadata(
            directory_descriptor,
            journal_name,
            "the durable transaction journal",
        )
        if (
            journal_metadata is None
            or _metadata_snapshot(journal_metadata)
            != linked_snapshot[:-1]
        ):
            raise _export_error(
                "transition-dxf-export-journal-failed",
                "the transaction journal did not retain its identity",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        if _path_metadata(
            directory_descriptor,
            temporary_name,
            "the transaction journal staging link",
        ) is not None:
            raise _export_error(
                "transition-dxf-export-journal-failed",
                "the transaction journal staging link appeared without "
                "creation-bound ownership",
                source_code="FileExistsError",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        return linked_snapshot
    except Exception as error:
        if isinstance(error, TransitionDxfExportError):
            raise
        raise _export_error(
            "transition-dxf-export-journal-failed",
            "the transaction journal could not be committed durably",
            source_code=type(error).__name__,
            destination_changed=isinstance(error, FileExistsError),
            cleanup_complete=not journal_linked,
            recoverable=False,
        ) from error
    finally:
        if journal_descriptor is not None:
            os.close(journal_descriptor)


def _link_file(
    source_directory_descriptor,
    source_name,
    destination_directory_descriptor,
    destination_name,
):
    if source_name is None:
        ctypes.set_errno(0)
        result = _LINKAT(
            source_directory_descriptor,
            b"",
            destination_directory_descriptor,
            os.fsencode(destination_name),
            _AT_EMPTY_PATH,
        )
        if result != 0:
            error_number = ctypes.get_errno()
            raise OSError(
                error_number,
                os.strerror(error_number),
                destination_name,
            )
        return
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


def _rollback_partial_commit(
    directory_descriptor,
    staged_snapshots,
    entries,
):
    linked = []
    for name, expected_sha256 in entries:
        snapshot = _file_snapshot(directory_descriptor, name)
        if snapshot is None:
            continue
        if (
            snapshot[-1] != expected_sha256
            or snapshot != staged_snapshots[name]
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
    staged_files,
    entries,
    output_directory,
    directory_identity,
):
    try:
        staged = _staged_file_snapshots(
            staged_files,
            expected_link_count=0,
        )
        for name, _expected_sha256 in entries:
            _link_file(
                staged_files[name][0],
                None,
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
                staged,
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

    try:
        return _create_transaction_journal(
            directory_descriptor,
            journal_name,
            journal_temporary_name,
            transaction_document,
        )
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


def _cleanup_transaction(
    directory_descriptor,
    journal_name,
    journal_snapshot,
    legacy_stage_name,
):
    _ensure_no_legacy_stage(
        directory_descriptor,
        legacy_stage_name,
        error_code="transition-dxf-export-cleanup-failed",
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
    deterministic files are committed through a durable interruption journal;
    identical existing files may be reused when no unowned transaction control
    exists, but nothing is overwritten or recovered from first-observed state.
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
        legacy_stage_name,
    ) = _transaction_names(plan.dxf_filename, plan.manifest_filename)
    directory_descriptor = _open_output_directory(
        output_directory,
        directory_identity,
    )
    try:
        _reject_preexisting_transaction_controls(
            directory_descriptor,
            journal_name,
            journal_temporary_name,
            legacy_stage_name,
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

        staged_files = {}
        try:
            transaction_document = None
            journal_snapshot = None
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
                staged_files = _create_staged_files(
                    directory_descriptor,
                    legacy_stage_name,
                    (
                        (plan.dxf_filename, dxf_value),
                        (plan.manifest_filename, manifest_value),
                    ),
                )
                observed_dxf = _read_staged_descriptor(
                    staged_files[plan.dxf_filename][0],
                    staged_files[plan.dxf_filename][1],
                    "the staged DXF",
                )
                observed_manifest = _read_staged_descriptor(
                    staged_files[plan.manifest_filename][0],
                    staged_files[plan.manifest_filename][1],
                    "the staged dependency manifest",
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
                staged_snapshots = {
                    name: snapshot
                    for name, (_descriptor, snapshot)
                    in staged_files.items()
                }
                transaction_document = _transaction_document(
                    plan.dxf_filename,
                    dxf_sha256,
                    plan.manifest_filename,
                    manifest_sha256,
                    staged_snapshots,
                )
                _ensure_no_legacy_stage(
                    directory_descriptor,
                    legacy_stage_name,
                    error_code="transition-dxf-export-staging-failed",
                )
                journal_snapshot = _create_transaction_journal(
                    directory_descriptor,
                    journal_name,
                    journal_temporary_name,
                    transaction_document,
                )
                _ensure_no_legacy_stage(
                    directory_descriptor,
                    legacy_stage_name,
                    error_code="transition-dxf-export-staging-failed",
                )
                committed_snapshots = _commit_staged_files(
                    directory_descriptor,
                    staged_files,
                    entries,
                    output_directory,
                    directory_identity,
                )
            except Exception as error:
                operation_error = error

            cleanup_error = None
            if (
                journal_snapshot is not None
                and (
                    operation_error is None
                    or getattr(operation_error, "cleanup_complete", True)
                    or getattr(operation_error, "code", "")
                    == "transition-dxf-export-staging-failed"
                )
            ):
                try:
                    _cleanup_transaction(
                        directory_descriptor,
                        journal_name,
                        journal_snapshot,
                        legacy_stage_name,
                    )
                except TransitionDxfExportError as error:
                    cleanup_error = error

            if cleanup_error is not None:
                rollback_error = None
                if committed_snapshots is not None:
                    try:
                        _rollback_committed_files(
                            directory_descriptor,
                            entries,
                            committed_snapshots,
                        )
                    except TransitionDxfExportError as error:
                        rollback_error = error
                journal_cleanup_error = None
                if rollback_error is None:
                    try:
                        _remove_owned_file(
                            directory_descriptor,
                            journal_name,
                            journal_snapshot,
                            error_code=(
                                "transition-dxf-export-cleanup-failed"
                            ),
                            description=(
                                "the durable transaction journal"
                            ),
                        )
                    except TransitionDxfExportError as error:
                        journal_cleanup_error = error
                terminal_error = rollback_error or journal_cleanup_error
                changed = bool(
                    cleanup_error.destination_changed
                    or committed_snapshots is not None
                    or getattr(
                        operation_error,
                        "destination_changed",
                        False,
                    )
                )
                raise _export_error(
                    "transition-dxf-export-cleanup-failed",
                    (
                        cleanup_error.detail
                        if terminal_error is None
                        else "{}; owned output rollback or journal cleanup "
                        "was incomplete".format(cleanup_error.detail)
                    ),
                    source_code=str(
                        getattr(operation_error, "code", "")
                        or getattr(terminal_error, "source_code", "")
                        or cleanup_error.source_code
                    ),
                    destination_changed=changed,
                    cleanup_complete=False,
                    recoverable=(
                        cleanup_error.recoverable
                        if terminal_error is None
                        else False
                    ),
                ) from (
                    operation_error or terminal_error or cleanup_error
                )
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
                        rollback_journal_snapshot = (
                            _create_rollback_controls(
                                directory_descriptor,
                                journal_name,
                                journal_temporary_name,
                                transaction_document,
                                entries,
                                committed_snapshots,
                            )
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
                            legacy_stage_name,
                        )
                    except TransitionDxfExportError as rollback_error:
                        raise _export_error(
                            "transition-dxf-export-rollback-failed",
                            "the output destination changed after commit "
                            "and rollback was incomplete",
                            source_code=identity_error.code,
                            destination_changed=True,
                            cleanup_complete=False,
                            recoverable=False,
                        ) from rollback_error
                    raise identity_error
            return result
        finally:
            _close_staged_files(staged_files)
    finally:
        os.close(directory_descriptor)
