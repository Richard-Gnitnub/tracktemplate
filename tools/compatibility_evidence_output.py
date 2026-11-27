"""Project only the approved compatibility evidence into public files.

This module does not run tests or authorise uploads. Its callers must supply
actual source-bound observations, preserve rejected original diagnostics in
owned scratch, and bind operational evidence through its separate transport.
A successful projection is not proof that every future failure is safe.
"""

import ast
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
from types import CodeType, MappingProxyType
import zlib


SCOPE_BYTES = 157516
SCOPE_SHA256 = (
    "0dc9d0d13eeb9722e6d3e9e9d4c7ecdf14131fe1e8724be65bfd2ab726a2930b"
)
BASE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)
BASE_BYTES = 636344
SOURCE_COMMIT = "dcb326e531bde7d861ce4a316776dd00dab297e8"
CAPSULE_SHA256 = (
    "db94a823d811dd96ccdc4a2f3917ec365409d4682a781f78feb62e3478098c60"
)
RUNTIME = {
    "freecad": [1, 1, 4],
    "python": [3, 13, 16],
    "pyside": "6.11.3",
    "qt": "6.11.3",
    "occt": "7.8.1",
    "coin": "SIM Coin 4.0.10",
    "app_commit": "b7e0947f142c4e263d2cf950a7decb5a96f7243b0bf5adc9fda60d8e8d1eb811",
    "runtime_commit": "2c059c881e5059ea801dc963cc970b83d775de03b98e9f570b31790e1f92ab5d",
}
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_RESULT_BYTES = 128 * 1024
MAX_FAILURE_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FRAME = re.compile(
    r'  File "([a-zA-Z0-9_./-]+)", line ([1-9][0-9]*), '
    r"in ([a-zA-Z_][a-zA-Z0-9_]*|<module>)\Z"
)
PHASE5_GROUP = "phase5-view-edit-lifecycle"
PHASE5_FAILURE_SOURCES = MappingProxyType({
    "g05-selection":
        "assessment/tests/freecad_gui_validate_phase5_transition_coin_viewprovider.py",
    "g05-multi-selection":
        "assessment/tests/freecad_gui_validate_phase5_transition_multi_object_edit.py",
})
_PHASE5_SERVER_FRAME = re.compile(
    r'  File "/home/runner/work/_temp/l1-gui-([1-9][0-9]*)/bridge/'
    r'addon/FreecadCli/rpc_server\.py", line 89, in _execute_and_capture'
)
_PHASE5_REASON = re.compile(
    r"AssertionError: TT_DIAGNOSTIC site=(g05-(?:multi-)?selection) "
    r"value_sha256=[0-9a-f]{64}"
)
_ROOT_FIELDS = {
    "schema_version",
    "group_id",
    "status",
    "source_commit",
    "entry_sha256",
    "assessment_entry_sha256",
    "runtime",
    "inputs",
    "checks",
    "images",
    "export_comparisons",
    "document_preservation",
    "cleanup",
    "failure",
}
_COMMON_OBSERVATIONS = {
    "status",
    "assessment_entry_sha256",
    "runtime",
    "sentinel",
    "returncode",
    "sessions",
    "inputs",
    "document_preservation",
    "cleanup",
    "failure",
}
_READINESS_FIELDS = {
    "renderer",
    "pre_geometry_readiness",
    "source_copy_only",
    "geometry_builds",
}
_PRESERVATION_FIELDS = {
    "source_sha256_before",
    "source_sha256_after",
    "original_unchanged",
    "copy_only",
    "object_count_before",
    "object_count_after",
    "undo",
    "redo",
    "save_reopen",
}
_STRAIGHT_FIELDS = {
    "macro_sha256",
    "generated_document",
    "comparison_witness_sha256",
    "source_document_semantic_sha256",
    "timings",
    "straight_checks",
}


class EvidenceError(ValueError):
    """Reject evidence without including its potentially private contents."""


def _require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


def _exact(value, keys, reason):
    _require(type(value) is dict and set(value) == set(keys), reason)


def _integer(value, minimum=0, maximum=2**53):
    _require(
        type(value) is int and minimum <= value <= maximum,
        "integer observation differs",
    )
    return value


def _boolean(value):
    _require(type(value) is bool, "boolean observation differs")
    return value


def _digest(value):
    _require(
        type(value) is str and _SHA256.fullmatch(value),
        "digest observation differs",
    )
    return value


def _relative(value):
    _require(
        type(value) is str and bool(value) and "\\" not in value,
        "relative member required",
    )
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and str(path) == value
        and all(part not in ("", ".", "..") for part in path.parts)
        and re.fullmatch(r"[a-zA-Z0-9_./-]+", value),
        "unsafe evidence member",
    )
    return value


def _open_directory(path):
    path = Path(path)
    _require(
        path.is_absolute() and ".." not in path.parts,
        "absolute directory required",
    )
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError as error:
        os.close(descriptor)
        raise EvidenceError("directory refused") from error


def _read(path, maximum):
    path = Path(path)
    parent = _open_directory(path.parent)
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent,
        )
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            _require(
                stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                "regular unlinked evidence file required",
            )
            _require(0 < info.st_size <= maximum, "evidence size differs")
            content = stream.read(maximum + 1)
            _require(len(content) == info.st_size, "evidence changed on read")
            return content
    except OSError as error:
        raise EvidenceError("evidence read refused") from error
    finally:
        os.close(parent)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def _json(content):
    try:
        return json.loads(
            content,
            object_pairs_hook=_pairs,
            parse_constant=lambda _: _reject_constant(),
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError("invalid JSON evidence") from error


def _reject_constant():
    raise EvidenceError("nonfinite JSON number")


def _identity(content):
    return {
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


@dataclass(frozen=True)
class Group:
    """An exact source and output group from the approved scope."""

    group_id: str
    entry: str
    entry_sha256: str
    sentinel: str
    sessions: int
    images: tuple
    result: str
    failure: str


@dataclass(frozen=True)
class Scope:
    """Verified immutable group map and original source text."""

    groups: object
    sources: object
    assessments: object = field(default_factory=lambda: MappingProxyType({}))


def load_scope(manifest_path, repository_root):
    """Verify approved bytes, counts, member paths and bound source bytes."""
    content = _read(manifest_path, SCOPE_BYTES)
    _require(
        _identity(content)
        == {
            "bytes": SCOPE_BYTES,
            "sha256": SCOPE_SHA256,
        },
        "approved scope identity differs",
    )
    manifest = _json(content)
    _require(
        manifest["source_commit"] == SOURCE_COMMIT
        and manifest["publication"]["repository"]
        == "Richard-Gnitnub/tracktemplate"
        and manifest["publication"]["retention_days"] == 30,
        "publication scope differs",
    )
    groups = {}
    sources = {}
    root = Path(repository_root)

    def source(relative, digest, size=None):
        _relative(relative)
        raw = _read(root / relative, 2 * 1024 * 1024)
        _require(
            hashlib.sha256(raw).hexdigest() == digest
            and (size is None or len(raw) == size),
            "bound source identity differs",
        )
        sources[relative] = raw.decode("utf-8")

    rows = manifest["image_rows"]
    _require(
        len(rows) == 22 and len(manifest["metadata_rows"]) == 22,
        "matrix group count differs",
    )
    for row, metadata in zip(rows, manifest["metadata_rows"]):
        identity = row["group_id"]
        source(row["entry"], row["entry_sha256"])
        images = tuple(_relative(item["path"]) for item in row["images"])
        _require(
            len(images) == row["png_count"]
            and all(
                item["media_type"] == "image/png"
                and item["sha256"] is None
                and item["bytes"] is None
                for item in row["images"]
            )
            and metadata["path"] == f"gui/{identity}/result.json"
            and set(metadata["allowed_root_fields"]) == _ROOT_FIELDS,
            "group output shape differs",
        )
        groups[identity] = Group(
            identity,
            row["entry"],
            row["entry_sha256"],
            row["sentinel"],
            row["prospective_sessions"],
            images,
            metadata["path"],
            f"gui/{identity}/failure.txt",
        )
    auxiliary = manifest["auxiliary_metadata_rows"]
    _require(
        len(auxiliary) == 2 and len(manifest["auxiliary_image_rows"]) == 1,
        "auxiliary scope differs",
    )
    readiness = manifest["auxiliary_image_rows"][0]
    for binding in (
        readiness["source_bindings"] + auxiliary[1]["source_bindings"]
    ):
        relative = binding["path"].split("/TrackTemplateMacro/", 1)[1]
        source(relative, binding["sha256"], binding["bytes"])
    entry = "tests/hosted_l1_gui_suite.py"
    groups["readiness"] = Group(
        "readiness",
        entry,
        hashlib.sha256(sources[entry].encode("utf-8")).hexdigest(),
        "TRACKTEMPLATE_COMPATIBILITY_GUI_READINESS_PASS",
        1,
        (_relative(readiness["path"]),),
        auxiliary[0]["path"],
        "gui/readiness/failure.txt",
    )
    entry = "tools/freecad_bridge/run_b14_straight_station.py"
    groups["straight-generation"] = Group(
        "straight-generation",
        entry,
        hashlib.sha256(sources[entry].encode("utf-8")).hexdigest(),
        "TRACKTEMPLATE_COMPATIBILITY_STRAIGHT_GENERATION_PASS",
        1,
        (),
        auxiliary[1]["path"],
        "fixture-generation/straight/failure.txt",
    )
    members = [
        name
        for group in groups.values()
        for name in (*group.images, group.result, group.failure)
    ]
    _require(
        len(groups) == 24
        and sum(len(group.images) for group in groups.values()) == 160
        and len(members) == len(set(members)) == 208
        and {group.failure for group in groups.values()}
        == {item["path"] for item in manifest["conditional_failure_outputs"]},
        "complete output counts differ",
    )
    for member in members:
        _relative(member)
    return Scope(MappingProxyType(groups), MappingProxyType(sources))


def export_scope_capsule(scope):
    """Derive neutral public controls; never include the private proposal."""
    value = {
        "schema_version": 1,
        "approved_scope_sha256": SCOPE_SHA256,
        "approved_scope_bytes": SCOPE_BYTES,
        "repository": "Richard-Gnitnub/tracktemplate",
        "retention_days": 30,
        "source_commit": SOURCE_COMMIT,
        "groups": [asdict(group) for group in scope.groups.values()],
        "sources": [
            {"path": path, **_identity(text.encode("utf-8"))}
            for path, text in sorted(scope.sources.items())
        ],
    }
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        + b"\n"
    )


def load_scope_capsule(capsule_path, repository_root):
    """Load only the exact reviewed public derivative and verify sources."""
    raw = _read(capsule_path, 64 * 1024)
    _require(
        hashlib.sha256(raw).hexdigest() == CAPSULE_SHA256,
        "public scope capsule identity differs",
    )
    value = _json(raw)
    groups = {}
    for item in value["groups"]:
        item["images"] = tuple(item["images"])
        group = Group(**item)
        groups[group.group_id] = group
    sources = {}
    for item in value["sources"]:
        content = _read(
            Path(repository_root) / _relative(item["path"]), 2 * 1024 * 1024
        )
        _require(
            _identity(content)
            == {key: item[key] for key in ("bytes", "sha256")},
            "capsule source identity differs",
        )
        sources[item["path"]] = content.decode("utf-8")
    return Scope(MappingProxyType(groups), MappingProxyType(sources))


def bind_assessment_source(
    scope, group_id, relative, source_path, expected_sha256
):
    """Bind a caller-pinned reviewed adaptation without extending outputs.

    The controller must pin the independently reviewed source identity.
    An arbitrary digest supplied by an untrusted caller is not a review.
    """
    _require(group_id in scope.groups, "assessment group differs")
    _relative(relative)
    raw = _read(source_path, 2 * 1024 * 1024)
    _require(
        hashlib.sha256(raw).hexdigest() == _digest(expected_sha256),
        "assessment source identity differs",
    )
    sources = dict(scope.sources)
    _require(
        relative not in sources or sources[relative].encode() == raw,
        "assessment replaces bound source",
    )
    sources[relative] = raw.decode("utf-8")
    assessments = dict(scope.assessments)
    _require(group_id not in assessments, "assessment already bound")
    assessments[group_id] = (relative, expected_sha256)
    return Scope(
        scope.groups, MappingProxyType(sources), MappingProxyType(assessments)
    )


def _png(content):
    _require(content.startswith(b"\x89PNG\r\n\x1a\n"), "PNG signature differs")
    offset = 8
    chunks = []
    compressed = bytearray()
    dimensions = None
    while offset < len(content):
        _require(offset + 12 <= len(content), "truncated PNG chunk")
        length, kind = struct.unpack(">I4s", content[offset : offset + 8])
        end = offset + 12 + length
        _require(end <= len(content), "truncated PNG data")
        data = content[offset + 8 : end - 4]
        checksum = struct.unpack(">I", content[end - 4 : end])[0]
        _require(
            zlib.crc32(kind + data) & 0xFFFFFFFF == checksum,
            "PNG checksum differs",
        )
        _require(
            kind
            in (b"IHDR", b"IDAT", b"IEND", b"pHYs", b"sRGB", b"gAMA", b"cHRM"),
            "unapproved PNG chunk",
        )
        if kind == b"IHDR":
            _require(not chunks and length == 13, "PNG header differs")
            width, height, depth, colour, method, filtering, interlace = (
                struct.unpack(">IIBBBBB", data)
            )
            _require(
                0 < width <= 4096
                and 0 < height <= 4096
                and depth == 8
                and colour in (2, 6)
                and (method, filtering, interlace) == (0, 0, 0),
                "PNG dimensions or format differ",
            )
            dimensions = (width, height, 3 if colour == 2 else 4)
        elif kind == b"IDAT":
            _require(
                b"IDAT" not in chunks or chunks[-1] == b"IDAT",
                "PNG data chunks are not contiguous",
            )
            compressed.extend(data)
        elif kind == b"IEND":
            _require(
                length == 0 and end == len(content), "PNG trailer differs"
            )
        else:
            _require(
                length
                == {b"pHYs": 9, b"sRGB": 1, b"gAMA": 4, b"cHRM": 32}[kind]
                and kind not in chunks
                and b"IDAT" not in chunks,
                "PNG ancillary chunk differs",
            )
        chunks.append(kind)
        offset = end
    _require(
        dimensions is not None
        and chunks[-1:] == [b"IEND"]
        and b"IDAT" in chunks,
        "incomplete PNG",
    )
    width, height, channels = dimensions
    expected = height * (1 + width * channels)
    decoder = zlib.decompressobj()
    try:
        pixels = decoder.decompress(bytes(compressed), expected + 1)
    except zlib.error as error:
        raise EvidenceError("PNG pixel stream differs") from error
    _require(
        len(pixels) == expected
        and decoder.eof
        and not decoder.unused_data
        and not decoder.unconsumed_tail
        and all(
            pixels[row * (1 + width * channels)] <= 4 for row in range(height)
        ),
        "PNG pixel data differs",
    )
    return width, height


def _images(group, root):
    images = []
    for member in group.images:
        path = root / member
        if not path.exists() and not path.is_symlink():
            continue
        content = _read(path, MAX_IMAGE_BYTES)
        width, height = _png(content)
        images.append(
            dict(path=member, **_identity(content), width=width, height=height)
        )
    return images


def _runtime(value):
    _exact(value, RUNTIME, "runtime fields differ")
    _require(value == RUNTIME, "runtime tuple differs")
    for key in ("freecad", "python"):
        _require(type(value[key]) is list, "runtime version differs")
        for part in value[key]:
            _integer(part)
    return json.loads(json.dumps(value))


def _inputs(value):
    _require(
        type(value) is list and 1 <= len(value) <= 2,
        "input observations differ",
    )
    expected = {
        "id": "approved-base",
        "sha256": BASE_SHA256,
        "bytes": BASE_BYTES,
    }
    _require(value[0] == expected, "approved input identity differs")
    result = [expected]
    for item in value[1:]:
        _exact(item, ("id", "sha256", "bytes"), "input fields differ")
        _require(
            item["id"] == "b14-long-straight-generated.FCStd",
            "input identity not approved",
        )
        result.append(
            {
                "id": item["id"],
                "sha256": _digest(item["sha256"]),
                "bytes": _integer(item["bytes"], 1),
            }
        )
    return result


def _preservation(value):
    _exact(value, _PRESERVATION_FIELDS, "preservation fields differ")
    result = {
        key: _digest(value[key])
        for key in ("source_sha256_before", "source_sha256_after")
    }
    _require(
        result["source_sha256_before"] == BASE_SHA256,
        "source observation differs",
    )
    result.update(
        {
            key: _boolean(value[key])
            for key in ("original_unchanged", "copy_only")
        }
    )
    result.update(
        {
            key: _integer(value[key])
            for key in ("object_count_before", "object_count_after")
        }
    )
    for key in ("undo", "redo", "save_reopen"):
        _require(
            value[key] in ("PASS", "FAIL", "NOT_APPLICABLE"),
            "lifecycle observation differs",
        )
        result[key] = value[key]
    _require(
        result["original_unchanged"]
        == (result["source_sha256_before"] == result["source_sha256_after"]),
        "source preservation contradicts hashes",
    )
    return result


def _cleanup(value):
    _exact(
        value,
        ("owned_pids", "remaining_pids", "complete"),
        "cleanup fields differ",
    )
    result = {"complete": _boolean(value["complete"])}
    for key in ("owned_pids", "remaining_pids"):
        _require(
            type(value[key]) is list and len(value[key]) <= 128,
            "process observations differ",
        )
        result[key] = [_integer(pid, 1, 2**31 - 1) for pid in value[key]]
        _require(
            len(set(result[key])) == len(result[key]),
            "duplicate process observation",
        )
    _require(
        set(result["remaining_pids"]) <= set(result["owned_pids"])
        and (not result["complete"] or not result["remaining_pids"]),
        "cleanup observations conflict",
    )
    return result


def _source_frame(source, line, function):
    """Match executable locations without importing or executing source."""
    pending = [compile(source, "<bound-source>", "exec", dont_inherit=True)]
    while pending:
        code = pending.pop()
        if code.co_name == function and any(
            number == line for _start, _end, number in code.co_lines()
        ):
            return True
        pending.extend(
            value for value in code.co_consts if isinstance(value, CodeType)
        )
    return False


def _phase5_failure_location(scope, raw):
    """Bind the unmodified remote traceback to one reviewed derived assert."""
    try:
        lines = raw.decode("utf-8").split("\n")
    except UnicodeError as error:
        raise EvidenceError("failure encoding differs") from error
    # The pinned bridge executes the supplied source directly as <string>.
    # Hosted PYTHONNODEBUGRANGES leaves exactly these original frames.
    _require(
        len(lines) == 7 and lines[-1] == ""
        and lines[0] == "Traceback (most recent call last):"
        and lines[2] == '    exec(code, {"__builtins__": __builtins__})',
        "Phase 5 bridge failure frames differ",
    )
    bridge_frame = _PHASE5_SERVER_FRAME.fullmatch(lines[1])
    run_id = os.environ.get("GITHUB_RUN_ID")
    _require(
        bridge_frame is not None and (run_id is None or bridge_frame[1] == run_id),
        "Phase 5 bridge failure does not match this hosted run",
    )
    reason = _PHASE5_REASON.fullmatch(lines[5])
    _require(reason is not None, "Phase 5 failure reason differs")
    site = reason[1]
    name = PHASE5_FAILURE_SOURCES[site]
    _require(name in scope.sources, "Phase 5 failure source not bound")
    source = ast.parse(scope.sources[name])
    _require(bool(source.body), "Phase 5 failure source is empty")
    module_call = source.body[-1]
    _require(
        isinstance(module_call, ast.Expr)
        and ast.unparse(module_call.value) == "validate()"
        and lines[3] == (
            f'  File "<string>", line {module_call.lineno}, in <module>'
        ),
        "Phase 5 module failure frame differs",
    )
    functions = [node for node in source.body
                 if isinstance(node, ast.FunctionDef) and node.name == "validate"]
    _require(len(functions) == 1, "Phase 5 validation source differs")
    assertions = [
        node for node in ast.walk(functions[0])
        if isinstance(node, ast.Assert)
        and isinstance(node.msg, ast.Call)
        and isinstance(node.msg.func, ast.Name)
        and node.msg.func.id == "_tt_diagnostic_message"
        and len(node.msg.args) == 2
        and not node.msg.keywords
        and isinstance(node.msg.args[0], ast.Constant)
        and node.msg.args[0].value == site
    ]
    _require(len(assertions) == 1 and lines[4] == (
        f'  File "<string>", line {assertions[0].lineno}, in validate'
    ), "Phase 5 assertion failure frame differs")
    return name, assertions[0].lineno


def _safe_failure(scope, group, value, root, original=None):
    if value is None:
        return None
    keys = ("exception_type", "source_relative_file", "line", "reason_code")
    _exact(value, keys, "failure fields differ")
    path = value["source_relative_file"]
    _require(path in scope.sources, "failure source not bound")
    lines = scope.sources[path].splitlines()
    line = _integer(value["line"], 1, len(lines))
    _require(
        value["exception_type"]
        in (
            "AssertionError",
            "RuntimeError",
            "ValueError",
            "TypeError",
        )
        and value["reason_code"] in ("ASSERTION_FAILED", "SOURCE_EXCEPTION"),
        "failure classification differs",
    )
    if original is None:
        original = _read(root / group.failure, MAX_FAILURE_BYTES)
    if (group.group_id == PHASE5_GROUP
            and path in PHASE5_FAILURE_SOURCES.values()):
        _require(
            _phase5_failure_location(scope, original) == (path, line)
            and value["exception_type"] == "AssertionError"
            and value["reason_code"] == "ASSERTION_FAILED",
            "Phase 5 failure binding differs",
        )
        return dict(
            stage=group.group_id,
            **value,
            original_safe_diagnostic_member=group.failure,
        )
    try:
        text = original.decode("utf-8")
    except UnicodeError as error:
        raise EvidenceError("failure encoding differs") from error
    diagnostic = text.splitlines()
    _require(
        diagnostic[:1] == ["Traceback (most recent call last):"]
        and len(diagnostic) >= 3,
        "original traceback required",
    )
    index = 1
    last_frame = None
    while index < len(diagnostic) - 1:
        frame = _FRAME.fullmatch(diagnostic[index])
        _require(frame is not None, "unsafe original traceback frame")
        filename, number, function = frame.groups()
        _require(filename in scope.sources, "traceback source not bound")
        source_lines = scope.sources[filename].splitlines()
        number = _integer(int(number), 1, len(source_lines))
        _require(
            _source_frame(scope.sources[filename], number, function),
            "traceback function differs from source",
        )
        last_frame = (filename, number)
        index += 1
        if index < len(diagnostic) - 1 and diagnostic[index].startswith(
            "    "
        ):
            _require(
                diagnostic[index] == "    " + source_lines[number - 1].strip(),
                "traceback source text differs",
            )
            index += 1
    _require(last_frame == (path, line), "failure frame differs")
    reasons = set()
    for node in ast.walk(ast.parse(scope.sources[path])):
        if not (
            getattr(node, "lineno", 0)
            <= line
            <= getattr(node, "end_lineno", 0)
        ):
            continue
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            call = node.exc
            if isinstance(call.func, ast.Name) and len(call.args) == 1:
                message = call.args[0]
                if isinstance(message, ast.Constant) and isinstance(
                    message.value, str
                ):
                    reasons.add(call.func.id + ": " + message.value)
        elif isinstance(node, ast.Assert):
            if node.msg is None:
                reasons.add("AssertionError")
            elif isinstance(node.msg, ast.Constant) and isinstance(
                node.msg.value, str
            ):
                reasons.add("AssertionError: " + node.msg.value)
    _require(
        diagnostic[-1] in reasons
        and diagnostic[-1].split(":", 1)[0] == value["exception_type"],
        "unsafe original failure reason",
    )
    return dict(
        stage=group.group_id,
        **value,
        original_safe_diagnostic_member=group.failure,
    )


def _renderer(value):
    _exact(
        value,
        (
            "gui_up",
            "widget_valid",
            "platform",
            "vendor",
            "renderer",
            "version",
        ),
        "renderer fields differ",
    )
    _boolean(value["gui_up"])
    _boolean(value["widget_valid"])
    _require(
        value["platform"] == "xcb"
        and value["vendor"] in ("Mesa", "Mesa/X.org", "Mesa Project"),
        "renderer identity differs",
    )
    _require(
        type(value["renderer"]) is str
        and re.fullmatch(
            r"llvmpipe \(LLVM [0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}, 256 bits\)",
            value["renderer"],
        ),
        "renderer description differs",
    )
    _require(
        type(value["version"]) is str
        and re.fullmatch(
            r"[0-9]\.[0-9] \((?:Core|Compatibility) Profile\) Mesa "
            r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}"
            r"(?: \(git-[0-9a-f]{10}\))?",
            value["version"],
        ),
        "renderer version differs",
    )
    return dict(value)


def build_result(scope, group_id, observation, source_root):
    """Project typed actual observations; reject raw receipts and unsafe text.

    The caller retains the original source result separately in owned scratch.
    It must not pass this projected result to an original fixture validator.
    Unsupported original failures stop publication and remain untouched.
    """
    _require(group_id in scope.groups, "unknown source group")
    group = scope.groups[group_id]
    _require(group_id in scope.assessments, "assessment source not bound")
    extra = (
        _READINESS_FIELDS
        if group_id == "readiness"
        else _STRAIGHT_FIELDS
        if group_id == "straight-generation"
        else set()
    )
    _exact(
        observation, _COMMON_OBSERVATIONS | extra, "observation fields differ"
    )
    _require(
        observation["assessment_entry_sha256"]
        == scope.assessments[group_id][1],
        "assessment digest differs",
    )
    _require(observation["status"] in ("PASS", "FAIL"), "status differs")
    passed = observation["status"] == "PASS"
    _require(
        type(observation["sentinel"]) is str
        and observation["sentinel"] in ("", group.sentinel),
        "source sentinel differs",
    )
    returncode = observation["returncode"]
    if passed or returncode is not None:
        returncode = _integer(returncode, -255, 255)
    sessions = _integer(observation["sessions"], 0, group.sessions)
    root = Path(source_root)
    images = _images(group, root)
    preservation = observation["document_preservation"]
    if passed or preservation is not None:
        preservation = _preservation(preservation)
    cleanup = observation["cleanup"]
    if passed or cleanup is not None:
        cleanup = _cleanup(cleanup)
    failure = _safe_failure(scope, group, observation["failure"], root)
    checks = [
        {
            "id": "source-sentinel",
            "result": bool(observation["sentinel"]),
            "observed": bool(observation["sentinel"]),
            "expected": True,
        },
        {
            "id": "source-exit",
            "result": returncode == 0,
            "observed": returncode,
            "expected": 0,
        },
        {
            "id": "source-sessions",
            "result": sessions == group.sessions,
            "observed": sessions,
            "expected": group.sessions,
        },
        {
            "id": "source-images",
            "result": len(images) == len(group.images),
            "observed": len(images),
            "expected": len(group.images),
        },
    ]
    _require(
        not passed
        or (
            all(item["result"] for item in checks)
            and failure is None
            and preservation["original_unchanged"]
            and preservation["copy_only"]
            and "FAIL" not in preservation.values()
            and cleanup["complete"]
        ),
        "PASS lacks mandatory source evidence",
    )
    _require(
        not passed or not (root / group.failure).exists(),
        "PASS has failure evidence",
    )
    _require(
        passed or failure is not None or not (root / group.failure).exists(),
        "unreferenced original failure",
    )
    result = {
        "schema_version": 1,
        "group_id": group_id,
        "status": observation["status"],
        "source_commit": SOURCE_COMMIT,
        "entry_sha256": group.entry_sha256,
        "assessment_entry_sha256": _digest(
            observation["assessment_entry_sha256"]
        ),
        "runtime": (
            _runtime(observation["runtime"])
            if passed or observation["runtime"] is not None
            else None
        ),
        "inputs": (
            _inputs(observation["inputs"])
            if passed or observation["inputs"] != []
            else []
        ),
        "checks": checks,
        "images": images,
        "export_comparisons": [],
        "document_preservation": preservation,
        "cleanup": cleanup,
        "failure": failure,
    }
    _require(
        (not passed and not result["inputs"])
        or len(result["inputs"]) == 1
        or "straight" in group_id,
        "generated input outside source group",
    )
    if group_id == "readiness":
        renderer = observation["renderer"]
        result.update(
            stage="readiness",
            renderer=(
                _renderer(renderer) if passed or renderer is not None else None
            ),
        )
        for key in ("pre_geometry_readiness", "source_copy_only"):
            result[key] = (
                _boolean(observation[key])
                if passed or observation[key] is not None
                else None
            )
        geometry = observation["geometry_builds"]
        result["geometry_builds"] = (
            _integer(geometry) if passed or geometry is not None else None
        )
        _require(
            not passed
            or (
                result["pre_geometry_readiness"]
                and result["source_copy_only"]
                and result["geometry_builds"] == 0
                and result["renderer"]["gui_up"]
                and result["renderer"]["widget_valid"]
            ),
            "readiness PASS lacks source-only evidence",
        )
    if group_id == "straight-generation":
        result = _straight_result(result, observation)
    return result


def _straight_result(common, observation):
    passed = common["status"] == "PASS"
    for key, expected in (
        (
            "comparison_witness_sha256",
            "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d",
        ),
        (
            "source_document_semantic_sha256",
            "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5",
        ),
    ):
        _require(
            observation[key] == expected
            or (not passed and observation[key] is None),
            "straight source witnesses differ",
        )
    generated = observation["generated_document"]
    if passed or generated is not None:
        _exact(
            generated, ("id", "sha256", "bytes"), "generated identity differs"
        )
        _require(
            generated["id"] == "b14-long-straight-generated.FCStd",
            "generated identifier differs",
        )
        generated = {
            "id": generated["id"],
            "sha256": _digest(generated["sha256"]),
            "bytes": _integer(generated["bytes"], 1),
        }
    straight = observation["straight_checks"]
    names = (
        "length_1500_mm",
        "length_450_mm",
        "curve_preserved",
        "history_preserved",
        "semantic_save_reopen",
    )
    checks = list(common["checks"])
    if passed or straight is not None:
        _exact(straight, names, "straight check fields differ")
        for name in names:
            outcome = _boolean(straight[name])
            checks.append(
                {
                    "id": name,
                    "result": outcome,
                    "observed": outcome,
                    "expected": True,
                }
            )
    _require(
        not passed or all(item["result"] for item in checks),
        "straight PASS lacks witnesses",
    )
    timings = observation["timings"]
    if passed or timings is not None:
        _exact(timings, ("generation", "save_reopen"), "timing fields differ")
        for value in timings.values():
            _require(
                type(value) in (int, float)
                and math.isfinite(value)
                and value >= 0,
                "timing value differs",
            )
        timings = dict(timings)
    result = {
        key: common[key]
        for key in (
            "schema_version",
            "status",
            "source_commit",
            "entry_sha256",
            "assessment_entry_sha256",
            "runtime",
            "cleanup",
            "failure",
        )
    }
    result.update(
        stage="straight-generation",
        recipe_id="phase8-b14-straight-host-source-v1",
        scenario="phase8-straight-host",
        macro_sha256=(
            _digest(observation["macro_sha256"])
            if passed or observation["macro_sha256"] is not None
            else None
        ),
        source_fixture_sha256=BASE_SHA256,
        source_fixture_bytes=BASE_BYTES,
        source_fixture_sha256_after=(
            common["document_preservation"]["source_sha256_after"]
            if common["document_preservation"] is not None
            else None
        ),
        comparison_witness_sha256=observation["comparison_witness_sha256"],
        source_document_semantic_sha256=observation[
            "source_document_semantic_sha256"
        ],
        generated_document=generated,
        checks=checks,
        timings=timings,
    )
    return result


def _inventory(root):
    descriptor = _open_directory(root)
    os.close(descriptor)
    members = []
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(current) / name
            _require(not path.is_symlink(), "linked evidence member refused")
            info = path.lstat()
            _require(
                stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                "special evidence member refused",
            )
        members.extend(
            (Path(current) / name).relative_to(root).as_posix()
            for name in files
        )
    return set(members)


def seal_outputs(
    scope, source_root, destination, started_groups, observations
):
    """Validate every started group before copying any approved output.

    Results must equal a fresh typed projection of the supplied observations.
    No unlisted file, missing result, missing PASS image or modified original
    failure is admitted. Source files remain intact on every rejection.
    The destination must be new; transport and visual review remain separate.
    """
    _require(
        type(started_groups) in (list, tuple)
        and started_groups
        and len(set(started_groups)) == len(started_groups)
        and set(started_groups) <= set(scope.groups),
        "started groups differ",
    )
    _exact(observations, started_groups, "group observations differ")
    source_root, destination = Path(source_root), Path(destination)
    _require(
        not destination.is_relative_to(source_root),
        "destination overlaps source evidence",
    )
    members = _inventory(source_root)
    expected = set()
    contents = {}

    def retain(name, data):
        _require(
            sum(len(value) for value in contents.values()) + len(data)
            <= MAX_TOTAL_BYTES,
            "evidence exceeds publication bound",
        )
        contents[name] = data

    for group_id in started_groups:
        group = scope.groups[group_id]
        result = build_result(
            scope, group_id, observations[group_id], source_root
        )
        expected.add(group.result)
        raw = _read(source_root / group.result, MAX_RESULT_BYTES)
        _require(
            json.dumps(_json(raw), sort_keys=True, allow_nan=False)
            == json.dumps(result, sort_keys=True, allow_nan=False),
            "stored result differs from projection",
        )
        retain(group.result, raw)
        for item in result.get("images", []):
            expected.add(item["path"])
            data = _read(source_root / item["path"], MAX_IMAGE_BYTES)
            _require(
                _identity(data)
                == {key: item[key] for key in ("bytes", "sha256")},
                "image changed during seal",
            )
            retain(item["path"], data)
        if result["failure"] is not None:
            expected.add(group.failure)
            original = _read(source_root / group.failure, MAX_FAILURE_BYTES)
            _safe_failure(
                scope,
                group,
                observations[group_id]["failure"],
                source_root,
                original=original,
            )
            retain(group.failure, original)
    _require(members == expected, "missing or unlisted evidence member")
    parent = _open_directory(destination.parent)
    try:
        os.mkdir(destination.name, mode=0o700, dir_fd=parent)
    except OSError as error:
        raise EvidenceError("new evidence destination required") from error
    finally:
        os.close(parent)
    for name in sorted(contents):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = _open_directory(target.parent)
        try:
            output = os.open(
                target.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=descriptor,
            )
            with os.fdopen(output, "wb") as stream:
                stream.write(contents[name])
        finally:
            os.close(descriptor)
    return {name: _identity(contents[name]) for name in sorted(contents)}
