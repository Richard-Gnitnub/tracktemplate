"""Bounded L1 archive primitives; no transfer or execution authority.

The public coordinator pins approved archive bytes before acquisition.
Archive validation and extraction are unchanged. Historical encryption
helpers remain available for preserved evidence; the public workflow does
not call them. The fixed summary admits no paths or diagnostic text.
"""

from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import tempfile
import time
import traceback


INPUT_IDS = (
    "catalogue", "inventory", "context_recipes", "supplemental_recipes",
    "l1_model", "validation_receipt", "execution_receipt", "build_receipt",
    "reference_document", "expected_frames",
)
REQUIRED_CONTROLS = ("run-config", "recovery")
OPTIONAL_CONTROLS = ("readiness-review",)
MANIFEST_MEMBER = "control/payload-manifest.json"
# The approved ten files total 15,523,169 bytes. This transport bound leaves
# space for their JSON controls and tar framing, without admitting bulk data.
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_CONTROL_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_COUNTS = (
    "expected_tests", "observed_tests", "skips", "expected_frames",
    "observed_frames", "expected_components", "observed_components",
    "successful_components", "rolled_back_components",
)
_FLAGS = ("sentinel", "input_integrity", "cleanup")
_TIMES = ("total", "readiness", "native", "finalization")
_RESOURCES = ("memory_peak_bytes", "cpu_usage_usec", "swap_peak_bytes",
              "initial_mem_available_bytes", "tasks_peak")


class PayloadError(ValueError):
    """Fixed, non-private error class; full diagnostics belong in logs."""


def _require(condition, reason):
    if not condition:
        raise PayloadError(reason)


def _regular(path):
    path = Path(path)
    _require(path.is_absolute(), "absolute path required")
    _require(not any(part.is_symlink() for part in (path, *path.parents)),
             "linked path refused")
    _require(stat.S_ISREG(path.stat().st_mode), "regular file required")
    return path


def _private_output(path):
    path = Path(path)
    _require(path.is_absolute(), "absolute output required")
    parent = path.parent
    _require(parent.is_dir(), "output parent missing")
    _require(not any(part.is_symlink() for part in (path, *path.parents)),
             "linked output refused")
    _require(parent.stat().st_uid == os.getuid(), "output owner differs")
    _require(parent.stat().st_mode & 0o077 == 0, "output parent not private")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, 0o600)
    except OSError as error:
        raise PayloadError("output creation refused") from error
    return os.fdopen(descriptor, "wb")


def file_identity(path):
    """Return digest and byte count of a regular, non-linked file."""
    path = _regular(path)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return {"sha256": digest.hexdigest(), "bytes": size}


def member_name(group, identity):
    """Map a reviewed identity to its one archive member name."""
    if group == "inputs" and identity in INPUT_IDS:
        return "inputs/" + identity
    if group == "controls" and identity in (
            *REQUIRED_CONTROLS, *OPTIONAL_CONTROLS):
        return "control/" + identity + ".json"
    raise PayloadError("unknown payload identity")


def validate_manifest(manifest):
    """Validate the exact ten-file and bounded control-record allowlist."""
    _require(isinstance(manifest, dict)
             and set(manifest) == {"schema", "inputs", "controls"},
             "manifest fields differ")
    _require(type(manifest["schema"]) is int and manifest["schema"] == 1,
             "manifest schema differs")
    records = []
    for group in ("inputs", "controls"):
        values = manifest[group]
        _require(isinstance(values, list), "manifest list required")
        identities = []
        for record in values:
            _require(isinstance(record, dict) and set(record) == {
                "id", "member", "path", "sha256", "bytes",
            }, "manifest record fields differ")
            identity = record["id"]
            _require(record["member"] == member_name(group, identity),
                     "member identity differs")
            _require(isinstance(record["path"], str)
                     and Path(record["path"]).is_absolute(),
                     "manifest path differs")
            _require(isinstance(record["sha256"], str)
                     and bool(_SHA256.fullmatch(record["sha256"])),
                     "manifest digest differs")
            _require(type(record["bytes"]) is int and record["bytes"] > 0,
                     "manifest size differs")
            if group == "controls":
                _require(record["bytes"] <= MAX_CONTROL_BYTES,
                         "control too large")
            identities.append(identity)
            records.append(record)
        _require(len(set(identities)) == len(identities),
                 "duplicate payload identity")
        if group == "inputs":
            _require(set(identities) == set(INPUT_IDS),
                     "input identities differ")
        else:
            _require(set(REQUIRED_CONTROLS) <= set(identities)
                     <= set((*REQUIRED_CONTROLS, *OPTIONAL_CONTROLS)),
                     "control identities differ")
    _require(sum(record["bytes"] for record in records)
             < MAX_ARCHIVE_BYTES - MAX_MANIFEST_BYTES,
             "payload exceeds transport bound")
    return records


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _add_bytes(archive, name, content):
    member = tarfile.TarInfo(name)
    member.size = len(content)
    member.mode = 0o600
    member.mtime = 0
    archive.addfile(member, io.BytesIO(content))


def create_archive(manifest, output):
    """Package only hash-bound regular inputs and controls, without overwrite."""
    records = validate_manifest(manifest)
    contents = []
    for record in records:
        path = _regular(record["path"])
        _require(path.stat().st_size == record["bytes"],
                 "input size differs")
        content = path.read_bytes()
        _require(len(content) == record["bytes"]
                 and hashlib.sha256(content).hexdigest() == record["sha256"],
                 "input identity differs")
        contents.append((record["member"], content))
    manifest_content = _json_bytes(manifest)
    _require(len(manifest_content) <= MAX_MANIFEST_BYTES,
             "manifest too large")
    with _private_output(output) as stream:
        with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT
                          ) as archive:
            _add_bytes(archive, MANIFEST_MEMBER, manifest_content)
            for name, content in contents:
                _add_bytes(archive, name, content)
    receipt = file_identity(output)
    _require(receipt["bytes"] <= MAX_ARCHIVE_BYTES, "archive too large")
    return receipt


def _archive_records(archive_path):
    path = _regular(archive_path)
    _require(path.stat().st_size <= MAX_ARCHIVE_BYTES, "archive too large")
    archive = tarfile.open(path, mode="r:")
    try:
        members = archive.getmembers()
        names = [member.name for member in members]
        _require(len(names) == len(set(names)), "duplicate archive member")
        _require(len(names) <= 15, "too many archive members")
        _require(all(member.isreg() and not member.pax_headers
                     for member in members), "non-regular member refused")
        return archive, members
    except BaseException:
        archive.close()
        raise


def read_manifest(archive_path):
    """Read the bounded manifest from a byte-verified input archive."""
    archive, members = _archive_records(archive_path)
    with archive:
        matches = [item for item in members if item.name == MANIFEST_MEMBER]
        _require(len(matches) == 1, "embedded manifest missing")
        member = matches[0]
        _require(0 < member.size <= MAX_MANIFEST_BYTES, "manifest too large")
        with archive.extractfile(member) as stream:
            manifest = json.loads(stream.read())
        validate_manifest(manifest)
        return manifest


def extract_archive(archive_path, manifest, destination_root):
    """Verify every member before copying into a fresh mode-0700 root."""
    records = validate_manifest(manifest)
    expected = {record["member"]: record for record in records}
    archive, members = _archive_records(archive_path)
    contents = {}
    with archive:
        _require(set(item.name for item in members)
                 == {*expected, MANIFEST_MEMBER}, "archive members differ")
        for member in members:
            if member.name == MANIFEST_MEMBER:
                _require(member.size <= MAX_MANIFEST_BYTES,
                         "manifest too large")
            else:
                _require(member.size == expected[member.name]["bytes"],
                         "member size differs")
            with archive.extractfile(member) as stream:
                content = stream.read()
            if member.name == MANIFEST_MEMBER:
                _require(json.loads(content) == manifest,
                         "embedded manifest differs")
            else:
                _require(hashlib.sha256(content).hexdigest()
                         == expected[member.name]["sha256"],
                         "member digest differs")
                contents[member.name] = content
    root = Path(destination_root)
    _require(root.is_absolute()
             and not any(item.is_symlink() for item in (root, *root.parents)),
             "unsafe extraction root")
    try:
        root.mkdir(mode=0o700)
    except OSError as error:
        raise PayloadError("extraction root must be fresh") from error
    result = {}
    for record in records:
        target = root / record["member"]
        if not target.parent.exists():
            target.parent.mkdir(mode=0o700)
        with _private_output(target) as stream:
            stream.write(contents[record["member"]])
        result[record["id"]] = target
    return result


def capture_private_process(command, log_path, environment, timeout):
    """Capture child and launch failures without returning diagnostic text."""
    _require(not any("TOKEN" in name or "PASSPHRASE" in name
                     or "SECRET" in name for name in environment),
             "credential in child environment")
    with _private_output(log_path) as log:
        try:
            result = subprocess.run(command, env=environment, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout,
                                    check=False)
        except subprocess.TimeoutExpired:
            log.write(traceback.format_exc().encode())
            return {"outcome": "TIMEOUT", "returncode": None}
        except OSError:
            log.write(traceback.format_exc().encode())
            return {"outcome": "LAUNCH_FAILED", "returncode": None}
    return {"outcome": "PASS" if result.returncode == 0 else "FAILED",
            "returncode": result.returncode}


def _gpg(home):
    return ["gpg", "--no-options", "--homedir", str(home), "--batch",
            "--no-tty", "--no-autostart"]


@contextmanager
def _symmetric_home(log):
    # GPG 2.4 requires its agent for symmetric operations even with loopback
    # input and no caching. Scope that agent to an empty disposable keyring.
    with tempfile.TemporaryDirectory(prefix="l1-input-gpg-") as home:
        result = subprocess.run(
            ["gpgconf", "--homedir", home, "--launch", "gpg-agent"],
            stdout=log, stderr=log, timeout=10, check=False,
        )
        try:
            _require(result.returncode == 0, "isolated agent launch failed")
            result = subprocess.run(
                ["gpg-connect-agent", "--homedir", home, "--no-autostart",
                 "GETINFO pid", "/bye"], stdout=subprocess.PIPE,
                stderr=log, timeout=10, check=False,
            )
            log.write(result.stdout)
            match = re.search(rb"^D ([0-9]+)$", result.stdout, re.MULTILINE)
            _require(result.returncode == 0 and match is not None,
                     "isolated agent identity missing")
            pid = int(match.group(1))
            process = Path("/proc") / str(pid)
            command = (process / "cmdline").read_bytes().split(b"\0")
            _require(home.encode() in command, "isolated agent owner differs")
            yield home
        finally:
            stopped = subprocess.run(
                ["gpgconf", "--homedir", home, "--kill", "gpg-agent"],
                stdout=log, stderr=log, timeout=10, check=False,
            )
            _require(stopped.returncode == 0, "isolated agent stop failed")
            clearance = subprocess.run(
                ["gpg-connect-agent", "--homedir", home, "--no-autostart",
                 "GETINFO pid", "/bye"], stdout=subprocess.PIPE, stderr=log,
                timeout=10, check=False,
            )
            log.write(clearance.stdout)
            # gpg-connect-agent returns zero even when --no-autostart says
            # no agent exists. A live endpoint answers with its PID.
            _require(clearance.stdout == b"",
                     "isolated agent endpoint remains active")
            if "process" in locals():
                deadline = time.monotonic() + 5
                while process.exists():
                    # A reaped-by-init zombie is no longer executing or
                    # retaining secrets; it cannot serve an agent socket.
                    try:
                        status = (process / "stat").read_text().split()[2]
                    except FileNotFoundError:
                        break
                    if status == "Z":
                        break
                    _require(time.monotonic() < deadline,
                             "isolated agent cleanup uncertain")
                    time.sleep(0.05)


def _gpg_stream(command, source, output, log, passphrase_fd=None):
    descriptor = () if passphrase_fd is None else (passphrase_fd,)
    with _regular(source).open("rb") as stream, _private_output(output) as dest:
        try:
            result = subprocess.run(command, stdin=stream, stdout=dest,
                                    stderr=log, pass_fds=descriptor, timeout=120,
                                    check=False, env={"PATH": os.environ["PATH"],
                                                      "LC_ALL": "C"})
        except (OSError, subprocess.TimeoutExpired) as error:
            log.write(traceback.format_exc().encode())
            raise PayloadError("encryption process failed") from error
        _require(result.returncode == 0, "encryption process failed")
    return file_identity(output)


def encrypt_inputs(source, output, passphrase_fd, log_path):
    """Encrypt with AES-256 and integrity protection; secret arrives by FD."""
    with _private_output(log_path) as log:
        with _symmetric_home(log) as home:
            command = _gpg(home) + ["--pinentry-mode", "loopback",
                "--passphrase-fd", str(passphrase_fd), "--no-symkey-cache",
                "--cipher-algo", "AES256", "--force-mdc",
                "--compress-algo", "none", "--symmetric", "--output", "-"]
            return _gpg_stream(command, source, output, log, passphrase_fd)


def decrypt_inputs(source, output, passphrase_fd, expected_sha256,
                   expected_bytes, log_path):
    """Check the frozen ciphertext identity, then require GPG integrity PASS."""
    _require(file_identity(source) == {
        "sha256": expected_sha256, "bytes": expected_bytes,
    }, "ciphertext identity differs")
    with _private_output(log_path) as log:
        with _symmetric_home(log) as home:
            command = _gpg(home) + ["--pinentry-mode", "loopback",
                "--passphrase-fd", str(passphrase_fd), "--no-symkey-cache",
                "--decrypt", "--output", "-"]
            return _gpg_stream(command, source, output, log, passphrase_fd)


def empty_public_summary(source_commit, workflow_commit, run_id, run_attempt,
                         stage):
    """Build the fixed public schema, with no private text fields."""
    value = {
        "schema": 1, "source_commit": source_commit,
        "workflow_commit": workflow_commit, "run_id": run_id,
        "run_attempt": run_attempt, "stage": stage, "outcome": "NOT_RUN",
        "counts": dict.fromkeys(_COUNTS, 0),
        "flags": dict.fromkeys(_FLAGS, False),
        "timings_seconds": dict.fromkeys(_TIMES, 0),
        "resources": dict.fromkeys(_RESOURCES, 0),
        "evidence": {"sha256": "0" * 64, "bytes": 0, "asset_id": 0},
    }
    return validate_public_summary(value)


def validate_public_summary(value):
    """Refuse any unapproved field, string, non-finite number or false PASS."""
    _require(isinstance(value, dict) and set(value) == {
        "schema", "source_commit", "workflow_commit", "run_id", "run_attempt",
        "stage", "outcome", "counts", "flags", "timings_seconds", "resources",
        "evidence",
    }, "public summary fields differ")
    _require(type(value["schema"]) is int and value["schema"] == 1,
             "public summary schema differs")
    for name in ("source_commit", "workflow_commit"):
        _require(isinstance(value[name], str)
                 and bool(_COMMIT.fullmatch(value[name])), "public commit differs")
    for name in ("run_id", "run_attempt"):
        _require(type(value[name]) is int and value[name] > 0,
                 "public run identity differs")
    _require(value["stage"] in ("readiness", "native"), "public stage differs")
    _require(value["outcome"] in (
        "NOT_RUN", "PASS", "FAILED", "REFUSED", "TIMEOUT", "INCOMPLETE",
    ), "public outcome differs")
    for group, names in (("counts", _COUNTS), ("resources", _RESOURCES)):
        _require(isinstance(value[group], dict) and set(value[group]) == set(names),
                 "public numeric fields differ")
        _require(all(type(item) is int and item >= 0
                     for item in value[group].values()), "public integer differs")
    _require(isinstance(value["flags"], dict)
             and set(value["flags"]) == set(_FLAGS)
             and all(type(item) is bool for item in value["flags"].values()),
             "public flag differs")
    _require(isinstance(value["timings_seconds"], dict)
             and set(value["timings_seconds"]) == set(_TIMES)
             and all(type(item) in (int, float) and math.isfinite(item)
                     and item >= 0 for item in value["timings_seconds"].values()),
             "public timing differs")
    evidence = value["evidence"]
    _require(isinstance(evidence, dict)
             and set(evidence) == {"sha256", "bytes", "asset_id"}
             and isinstance(evidence["sha256"], str)
             and bool(_SHA256.fullmatch(evidence["sha256"]))
             and all(type(evidence[name]) is int and evidence[name] >= 0
                     for name in ("bytes", "asset_id")),
             "public evidence receipt differs")
    if value["outcome"] == "PASS":
        counts = value["counts"]
        frames, components = ((0, 0) if value["stage"] == "readiness"
                              else (150, 138))
        successful, rolled_back = ((0, 0) if value["stage"] == "readiness"
                                   else (690, 230))
        _require(all(value["flags"].values()) and counts["skips"] == 0
                 and counts["expected_tests"] == counts["observed_tests"] == 1
                 and counts["expected_frames"] == counts["observed_frames"] == frames
                 and counts["expected_components"]
                 == counts["observed_components"] == components
                 and counts["successful_components"] == successful
                 and counts["rolled_back_components"] == rolled_back
                 and evidence["bytes"] > 0 and evidence["asset_id"] > 0
                 and evidence["sha256"] != "0" * 64,
                 "public PASS lacks evidence")
    return value
