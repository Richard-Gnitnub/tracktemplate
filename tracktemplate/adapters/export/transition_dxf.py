"""Failure-safe private-development DXF export for one transition."""

import ctypes
import errno
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
        os.open,
        os.stat,
    )
    if (
        fcntl is None
        or _LINKAT is None
        or not all(required_flags)
        or any(item not in os.supports_dir_fd for item in required_dir_fd)
        or os.stat not in os.supports_follow_symlinks
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
            cleanup_complete=False,
            recoverable=False,
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
                cleanup_complete=False,
                recoverable=False,
            )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise _export_error(
                "transition-dxf-export-transaction-active",
                "another transition DXF transaction owns this directory",
                source_code=type(error).__name__,
                cleanup_complete=False,
                recoverable=False,
            ) from error
        except OSError as error:
            raise _export_error(
                "unsupported-transition-dxf-export-filesystem",
                "the output directory cannot provide the required lock",
                source_code=type(error).__name__,
                cleanup_complete=False,
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
            cleanup_complete=False,
            recoverable=False,
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
            cleanup_complete=False,
            recoverable=False,
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
        | getattr(os, "O_NOATIME", 0)
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
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
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
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
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
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
    except OSError as error:
        raise _export_error(
            error_code,
            "{} changed while it was read".format(description),
            source_code=type(error).__name__,
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
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
    values,
):
    staged_files = {}
    try:
        for name, value in values:
            staged_files[name] = _write_staged_file(
                directory_descriptor,
                name,
                value,
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


def _link_file(
    source_directory_descriptor,
    destination_directory_descriptor,
    destination_name,
):
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


def _copy_export_error(
    error,
    *,
    destination_changed,
    cleanup_complete,
    recoverable,
):
    if isinstance(error, TransitionDxfExportError):
        code = error.code
        message = error.detail
        source_code = error.source_code
    else:
        code = "transition-dxf-export-failed"
        message = "the transition DXF export failed"
        source_code = type(error).__name__
    return _export_error(
        code,
        message,
        source_code=source_code,
        destination_changed=destination_changed,
        cleanup_complete=cleanup_complete,
        recoverable=recoverable,
    )


def _owned_publication_snapshots(
    directory_descriptor,
    staged_files,
):
    owned = {}
    ambiguous = False
    for name, (descriptor, expected_snapshot) in staged_files.items():
        try:
            metadata = os.fstat(descriptor)
            snapshot = _descriptor_snapshot(
                descriptor,
                error_code="transition-dxf-export-commit-identity-failed",
                description="the anonymous staged {}".format(name),
                expected_identity=expected_snapshot[:2],
            )
        except (OSError, TransitionDxfExportError):
            ambiguous = True
            continue
        if snapshot != expected_snapshot:
            ambiguous = True
            continue
        if metadata.st_nlink == 0:
            continue
        if metadata.st_nlink != 1:
            ambiguous = True
            continue
        try:
            path_snapshot = _file_snapshot(
                directory_descriptor,
                name,
                error_code=(
                    "transition-dxf-export-commit-identity-failed"
                ),
                description="a newly published output",
            )
        except TransitionDxfExportError:
            ambiguous = True
            continue
        if path_snapshot != expected_snapshot:
            ambiguous = True
            continue
        owned[name] = expected_snapshot
    return owned, ambiguous


def _observe_failed_destination(
    directory_descriptor,
    output_directory,
    directory_identity,
    entries,
    initial_snapshots,
    staged_files,
):
    names = tuple(name for name, _digest in entries)
    expected_hashes = {
        name: digest for name, digest in entries
    }
    ambiguous = False
    directory_changed = False
    try:
        _verify_directory_identity(
            output_directory,
            directory_identity,
        )
    except TransitionDxfExportError:
        ambiguous = True
        directory_changed = True

    try:
        observed = _target_snapshots(
            directory_descriptor,
            names[0],
            names[1],
        )
    except TransitionDxfExportError:
        observed = None
        ambiguous = True

    owned, owned_ambiguous = _owned_publication_snapshots(
        directory_descriptor,
        staged_files,
    )
    ambiguous = ambiguous or owned_ambiguous
    destination_changed = directory_changed
    exact_state = observed is not None
    final_count = 0
    if observed is not None:
        destination_changed = (
            destination_changed or observed != initial_snapshots
        )
        for name, before, after in zip(
            names,
            initial_snapshots,
            observed,
        ):
            if after is not None:
                final_count += 1
                if after[-1] != expected_hashes[name]:
                    exact_state = False
            if before is not None:
                if after != before:
                    ambiguous = True
            elif after is not None and owned.get(name) != after:
                ambiguous = True
            if name in owned and after != owned[name]:
                ambiguous = True
        destination_changed = destination_changed or bool(owned)

    return {
        "ambiguous": ambiguous,
        "cleanup_complete": observed is not None and final_count == 0,
        "destination_changed": destination_changed,
        "recoverable": (
            observed is not None
            and exact_state
            and not ambiguous
            and final_count in (0, 1, 2)
        ),
    }


def _raise_bound_failure(
    error,
    directory_descriptor,
    output_directory,
    directory_identity,
    entries,
    initial_snapshots,
    staged_files,
):
    state = _observe_failed_destination(
        directory_descriptor,
        output_directory,
        directory_identity,
        entries,
        initial_snapshots,
        staged_files,
    )
    close_error = None
    try:
        _close_staged_files(staged_files)
    except TransitionDxfExportError as cleanup_error:
        close_error = cleanup_error

    source_error = (
        error
        if isinstance(error, TransitionDxfExportError)
        else _export_error(
            "transition-dxf-export-failed",
            "the transition DXF export failed",
            source_code=type(error).__name__,
        )
    )
    cleanup_complete = (
        state["cleanup_complete"]
        and close_error is None
        and source_error.cleanup_complete
    )
    recoverable = (
        state["recoverable"]
        and close_error is None
        and source_error.recoverable
    )
    if state["ambiguous"]:
        recoverable = False
    if close_error is not None:
        source_code = str(
            source_error.source_code
            or source_error.code
            or close_error.source_code
            or close_error.code
        )
        raise _export_error(
            "transition-dxf-export-cleanup-failed",
            "the export failed and anonymous descriptor cleanup was "
            "incomplete",
            source_code=source_code,
            destination_changed=(
                state["destination_changed"]
                or source_error.destination_changed
            ),
            cleanup_complete=False,
            recoverable=False,
        ) from close_error
    raise _copy_export_error(
        source_error,
        destination_changed=(
            state["destination_changed"]
            or source_error.destination_changed
        ),
        cleanup_complete=cleanup_complete,
        recoverable=recoverable,
    ) from error


def _publish_staged_files(
    directory_descriptor,
    staged_files,
    entries,
    output_directory,
    directory_identity,
    cancellation_requested,
):
    staged = _staged_file_snapshots(
        staged_files,
        expected_link_count=0,
    )
    for name, _expected_sha256 in entries:
        _check_cancellation(cancellation_requested)
        _verify_directory_identity(
            output_directory,
            directory_identity,
        )
        try:
            _link_file(
                staged_files[name][0],
                directory_descriptor,
                name,
            )
        except FileExistsError as error:
            raise _export_error(
                "transition-dxf-export-collision",
                "an absent deterministic output appeared during "
                "publication",
                source_code=type(error).__name__,
                recoverable=False,
            ) from error
        except OSError as error:
            if error.errno in (
                errno.EINVAL,
                errno.ENOSYS,
                errno.EOPNOTSUPP,
                errno.EPERM,
            ):
                raise _export_error(
                    "unsupported-transition-dxf-export-filesystem",
                    "the filesystem cannot publish an anonymous file by "
                    "descriptor",
                    source_code=type(error).__name__,
                    recoverable=False,
                ) from error
            raise _export_error(
                "transition-dxf-export-commit-failed",
                "an exact output could not be added without overwrite",
                source_code=type(error).__name__,
            ) from error
        try:
            os.fsync(directory_descriptor)
        except OSError as error:
            raise _export_error(
                "transition-dxf-export-commit-failed",
                "an added output could not be made durably visible",
                source_code=type(error).__name__,
                recoverable=False,
            ) from error
        linked_snapshot = _descriptor_snapshot(
            staged_files[name][0],
            error_code="transition-dxf-export-commit-identity-failed",
            description="the newly linked {}".format(name),
            expected_identity=staged[name][:2],
            expected_link_count=1,
        )
        if (
            linked_snapshot != staged[name]
            or _file_snapshot(
                directory_descriptor,
                name,
                error_code=(
                    "transition-dxf-export-commit-identity-failed"
                ),
                description="the newly linked output",
            )
            != staged[name]
        ):
            raise _export_error(
                "transition-dxf-export-commit-identity-failed",
                "a newly linked output changed after publication",
                destination_changed=True,
                cleanup_complete=False,
                recoverable=False,
            )
        _verify_directory_identity(
            output_directory,
            directory_identity,
        )
    return staged


def _revalidate_complete_pair(
    directory_descriptor,
    output_directory,
    directory_identity,
    names,
    expected_snapshots,
):
    _verify_directory_identity(output_directory, directory_identity)
    observed = _target_snapshots(
        directory_descriptor,
        names[0],
        names[1],
    )
    if observed != expected_snapshots:
        raise _export_error(
            "transition-dxf-export-commit-identity-failed",
            "the complete output pair changed before final validation",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
        )
    try:
        os.fsync(directory_descriptor)
    except OSError as error:
        raise _export_error(
            "transition-dxf-export-commit-failed",
            "the complete output pair durability could not be established",
            source_code=type(error).__name__,
            recoverable=False,
        ) from error
    _verify_directory_identity(output_directory, directory_identity)
    if (
        _target_snapshots(
            directory_descriptor,
            names[0],
            names[1],
        )
        != expected_snapshots
    ):
        raise _export_error(
            "transition-dxf-export-commit-identity-failed",
            "the complete output pair changed during final validation",
            destination_changed=True,
            cleanup_complete=False,
            recoverable=False,
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
    """Validate and monotonically publish one private-development pair.

    The destination is bound to one locked directory descriptor. Existing
    exact regular members are preserved, absent members are published from
    anonymous creation-bound descriptors without overwrite, and no published
    pathname is removed or replaced.
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
    values = {
        plan.dxf_filename: dxf_value,
        plan.manifest_filename: manifest_value,
    }
    names = tuple(name for name, _digest in entries)
    expected_hashes = {
        name: digest for name, digest in entries
    }
    directory_descriptor = _open_output_directory(
        output_directory,
        directory_identity,
    )
    staged_files = {}
    try:
        try:
            initial_snapshots = _target_snapshots(
                directory_descriptor,
                names[0],
                names[1],
            )
        except TransitionDxfExportError as error:
            raise _copy_export_error(
                error,
                destination_changed=error.destination_changed,
                cleanup_complete=False,
                recoverable=False,
            ) from error

        try:
            for name, snapshot in zip(names, initial_snapshots):
                if (
                    snapshot is not None
                    and snapshot[-1] != expected_hashes[name]
                ):
                    raise _export_error(
                        "transition-dxf-export-collision",
                        "an existing output is not byte-identical and "
                        "cannot be overwritten",
                        cleanup_complete=False,
                        recoverable=False,
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
                cleanup_complete = getattr(
                    error,
                    "cleanup_complete",
                    True,
                )
                recoverable = getattr(error, "recoverable", True)
                if not isinstance(cleanup_complete, bool):
                    cleanup_complete = False
                if not isinstance(recoverable, bool):
                    recoverable = False
                raise _export_error(
                    (
                        "transition-dxf-exact-geometry-failed"
                        if cleanup_complete
                        else (
                            "transition-dxf-exact-geometry-cleanup-failed"
                        )
                    ),
                    (
                        "transient exact geometry rejected the export"
                        if cleanup_complete
                        else (
                            "transient exact geometry cleanup was "
                            "incomplete"
                        )
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
            _verify_directory_identity(
                output_directory,
                directory_identity,
            )
            if (
                _target_snapshots(
                    directory_descriptor,
                    names[0],
                    names[1],
                )
                != initial_snapshots
            ):
                raise _export_error(
                    "transition-dxf-export-destination-changed",
                    "the deterministic output filenames changed during "
                    "validation",
                    destination_changed=True,
                    cleanup_complete=False,
                    recoverable=False,
                )

            missing_entries = tuple(
                entry
                for entry, snapshot in zip(entries, initial_snapshots)
                if snapshot is None
            )
            if not missing_entries:
                _revalidate_complete_pair(
                    directory_descriptor,
                    output_directory,
                    directory_identity,
                    names,
                    initial_snapshots,
                )
                result = _receipt(
                    plan,
                    geometry_receipt,
                    dxf_sha256,
                    manifest_sha256,
                    "reused",
                )
            else:
                result = _receipt(
                    plan,
                    geometry_receipt,
                    dxf_sha256,
                    manifest_sha256,
                    "created",
                )
                staged_files = _create_staged_files(
                    directory_descriptor,
                    tuple(
                        (name, values[name])
                        for name, _digest in missing_entries
                    ),
                )
                observed_values = dict(values)
                for name, _digest in missing_entries:
                    observed_values[name] = _read_staged_descriptor(
                        staged_files[name][0],
                        staged_files[name][1],
                        "the staged {}".format(name),
                    )
                _validate_dxf(
                    observed_values[plan.dxf_filename],
                    plan,
                )
                _validate_manifest(
                    observed_values[plan.manifest_filename],
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
                        names[0],
                        names[1],
                    )
                    != initial_snapshots
                ):
                    raise _export_error(
                        "transition-dxf-export-destination-changed",
                        "the deterministic output filenames changed "
                        "before publication",
                        destination_changed=True,
                        cleanup_complete=False,
                        recoverable=False,
                    )
                staged_snapshots = _publish_staged_files(
                    directory_descriptor,
                    staged_files,
                    missing_entries,
                    output_directory,
                    directory_identity,
                    cancellation_requested,
                )
                expected_snapshots = tuple(
                    before
                    if before is not None
                    else staged_snapshots[name]
                    for name, before in zip(names, initial_snapshots)
                )
                _revalidate_complete_pair(
                    directory_descriptor,
                    output_directory,
                    directory_identity,
                    names,
                    expected_snapshots,
                )
        except Exception as error:
            _raise_bound_failure(
                error,
                directory_descriptor,
                output_directory,
                directory_identity,
                entries,
                initial_snapshots,
                staged_files,
            )

        try:
            _close_staged_files(staged_files)
        except TransitionDxfExportError as error:
            raise _export_error(
                "transition-dxf-export-cleanup-failed",
                "the complete output pair was retained but anonymous "
                "descriptor cleanup was incomplete",
                source_code=str(error.source_code or error.code),
                destination_changed=bool(missing_entries),
                cleanup_complete=False,
                recoverable=False,
            ) from error
        return result
    finally:
        os.close(directory_descriptor)
