"""Run only the approved X2 ZY source construction through hosted controls.

The existing coordinator owns workflow transport. This fixed workload adds
one compiler service followed by the unchanged FreeCAD guard. They share a
lease and absolute deadline; it never admits the resulting model to a chair
catalogue. Import performs no process, network or geometry operation.
"""

from contextlib import ExitStack
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402
from tools import hosted_l1_private_validation as coordinator  # noqa: E402
from tools import hosted_native_geometry_pilot as pilot  # noqa: E402
from tools import l1_private_payload as payload  # noqa: E402

WORKLOAD = "to-zy-generation"
SCOPE = "TO-001-X2-ZY-generation-v1"
MANIFEST_SHA256 = (
    "3ff851541917e251809a5512348ae234b7499adca203bf4bde4263359d74667d"
)
ENTRY_SHA256 = (
    "e4fc8566f07651bc931b36d553a21e78eae40dd4b4f20d7b39b478034ec7c190"
)
ARCHIVE_SHA256 = (
    "3ead0083bcb6424669d9a58cf922c02376edd3fd455cf2965f2564f48891e3a0"
)
INPUT_COUNT = 71
INPUT_BYTES = 4009495
ARCHIVE_BYTES = 4085760
OWNER_DECISION_SHA256 = (
    "00e91e606417d0f78c65e2c06aae1132213dc3c61d449087907cd0e63e298acc"
)
MANIFEST_MEMBER = "known-input-manifest.json"
PACKAGE_VERSION = "3.2.2+dfsg-32"
CONTROL_FILES = (
    ".github/workflows/l1-private-validation.yml",
    "tools/hosted_l1_private_validation.py",
    "tools/hosted_to_zy_generation.py",
    "tools/l1_private_payload.py",
    "tools/freecad_validation_guard.py",
    "tools/hosted_native_geometry_pilot.py",
    "tests/hosted_to_zy_generation_suite.py",
    "tests/validate_hosted_to_zy_generation.py",
)
SENTINELS = (
    ("readiness", "Fixed ZY generation hosted readiness passed"),
    ("native", "Fixed X2 ZY hosted construction passed"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    return payload.file_identity(Path(path))


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read(path):
    payload._regular(path)
    return json.loads(
        Path(path).read_bytes(),
        object_pairs_hook=unique_object,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("Nonfinite JSON token")
        ),
    )


def unique_object(pairs):
    require(
        len(pairs) == len({key for key, _ in pairs}), "Duplicate JSON field"
    )
    return dict(pairs)


def valid_hash(value):
    return (
        type(value) is str
        and re.fullmatch(r"[0-9a-f]{64}", value)
        and value != "0" * 64
    )


def safe_member(name):
    return (
        type(name) is str
        and name != ""
        and "\\" not in name
        and not name.startswith("/")
        and all(part not in ("", ".", "..") for part in name.split("/"))
        and PurePosixPath(name).as_posix() == name
    )


def extract_inputs(archive_path, target):
    """Validate the exact approved membership before exclusive extraction."""
    require(
        identity(archive_path)["bytes"] == ARCHIVE_BYTES,
        "Approved archive length differs",
    )
    require(
        target.is_absolute()
        and target.resolve() == target
        and not target.exists()
        and not any(p.is_symlink() for p in (target, *target.parents)),
        "Input target is linked, occupied or unresolved",
    )
    with tarfile.open(archive_path, "r:") as archive:
        members = archive.getmembers()
        names = [row.name for row in members]
        require(
            len(names) == len(set(names)) == INPUT_COUNT + 1
            and all(
                safe_member(row.name) and row.isfile() and not row.pax_headers
                for row in members
            ),
            "Input archive membership or file type differs",
        )
        require(MANIFEST_MEMBER in names, "Known input manifest absent")
        content = archive.extractfile(MANIFEST_MEMBER).read()
        require(
            hashlib.sha256(content).hexdigest() == MANIFEST_SHA256,
            "Known input manifest changed",
        )
        manifest = json.loads(content, object_pairs_hook=unique_object)
        rows = manifest["files"]
        require(
            type(rows) is list
            and len(rows) == INPUT_COUNT
            and manifest["file_count"] == INPUT_COUNT
            and type(manifest["file_count"]) is int
            and manifest["total_bytes"] == INPUT_BYTES
            and sum(row["bytes"] for row in rows) == INPUT_BYTES
            and len({row["member"] for row in rows}) == INPUT_COUNT
            and set(names) == {MANIFEST_MEMBER, *(r["member"] for r in rows)},
            "Known input count or names differ",
        )
        contents = {MANIFEST_MEMBER: content}
        for row in rows:
            require(
                safe_member(row["member"])
                and type(row["bytes"]) is int
                and row["bytes"] > 0
                and valid_hash(row["sha256"]),
                "Invalid fixed input row",
            )
            item = archive.getmember(row["member"])
            require(item.size == row["bytes"], "Input length changed")
            raw = archive.extractfile(item).read()
            require(
                hashlib.sha256(raw).hexdigest() == row["sha256"],
                "Input hash changed",
            )
            contents[row["member"]] = raw
    target.mkdir(mode=0o700)
    for name, raw in contents.items():
        path = target / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o400)
    verify_inputs(target)
    return manifest


def verify_inputs(target):
    require(
        identity(target / MANIFEST_MEMBER)["sha256"] == MANIFEST_SHA256,
        "Approved manifest changed",
    )
    manifest = read(target / MANIFEST_MEMBER)
    expected = {row["member"] for row in manifest["files"]}
    expected.add(MANIFEST_MEMBER)
    paths = list(target.rglob("*"))
    require(
        not any(path.is_symlink() for path in paths)
        and {
            path.relative_to(target).as_posix()
            for path in paths
            if path.is_file()
        }
        == expected,
        "Approved staging membership changed",
    )
    for row in manifest["files"]:
        require(
            identity(target / row["member"])
            == {
                "sha256": row["sha256"],
                "bytes": row["bytes"],
            },
            "Approved input changed",
        )
    return manifest


def compiler_path(path):
    path = Path(path)
    require(
        path.is_absolute()
        and path.resolve() == path
        and not any(item.is_symlink() for item in (path, *path.parents)),
        "Compiler must be absolute, resolved and nonsymlink",
    )
    payload._regular(path)
    return path


def validate_compiler(record):
    """Rehash the reviewed actual driver, backend, configuration and RTL."""
    require(
        record.get("status") == "PASS_COMPILER_READINESS"
        and record.get("version") == "3.2.2"
        and record.get("package_version") == PACKAGE_VERSION
        and record.get("architecture") == "x86_64"
        and record.get("package_provenance"),
        "Compiler readiness contract differs",
    )
    compiler = compiler_path(record["compiler_path"])
    require(
        identity(compiler) == record["binary_identity"],
        "Compiler driver changed",
    )
    files = record["toolchain_files"]
    require(
        type(files) is list
        and {row["role"] for row in files}
        >= {"driver", "backend", "config", "rtl"}
        and len({row["path"] for row in files}) == len(files),
        "Compiler closure is incomplete or duplicated",
    )
    for row in files:
        path = compiler_path(row["path"])
        require(
            identity(path) == {key: row[key] for key in ("sha256", "bytes")},
            "Compiler toolchain changed",
        )
    require(
        any(
            row["path"] == str(compiler) and row["role"] == "driver"
            for row in files
        ),
        "Driver missing from compiler closure",
    )
    aliases = record["toolchain_aliases"]
    require(
        type(aliases) is list
        and aliases
        and len({row["path"] for row in aliases}) == len(aliases),
        "Compiler lookup aliases absent or duplicated",
    )
    targets = {row["path"] for row in files}
    for row in aliases:
        lexical = Path(row["path"])
        require(
            lexical.is_absolute()
            and row["resolved"] in targets
            and str(lexical.resolve(strict=True)) == row["resolved"],
            "Compiler lookup target changed",
        )
    return compiler


def bounded_command(arguments, deadline, *, check=True):
    seconds = deadline - time.monotonic()
    require(seconds > 0, "Workload deadline expired")
    return subprocess.run(
        arguments,
        check=check,
        capture_output=True,
        text=True,
        timeout=min(15, seconds),
    )


def capture_compiler(deadline):
    """Observe installed package provenance; never compile in readiness."""
    packages = ("fp-compiler-3.2.2", "fp-units-rtl-3.2.2")
    provenance, paths, aliases = {}, {}, {}
    driver_alias = Path(shutil.which("fpc") or "")
    driver = compiler_path(driver_alias.resolve())
    aliases[str(driver_alias)] = str(driver)
    for package in packages:
        description = bounded_command(
            [
                "dpkg-query",
                "-W",
                "-f=${Package}\t${Version}\t${Architecture}\t${Status}\n",
                package,
            ],
            deadline,
        ).stdout.strip()
        require(
            description
            == package
            + "\t"
            + PACKAGE_VERSION
            + "\tamd64\tinstall ok installed",
            "Compiler package differs",
        )
        provenance[package] = {
            "installed": description,
            "apt_policy": bounded_command(
                ["apt-cache", "policy", package], deadline
            ).stdout,
            "verification": bounded_command(
                ["dpkg", "--verify", package], deadline
            ).stdout,
        }
        require(
            not provenance[package]["verification"],
            "Compiler package content differs from installed metadata",
        )
        listing = bounded_command(
            ["dpkg-query", "-L", package], deadline
        ).stdout
        provenance[package]["file_listing"] = listing
        for name in listing.splitlines():
            path = Path(name)
            if path.is_file():
                resolved = compiler_path(path.resolve())
                aliases[str(path)] = str(resolved)
                role = (
                    "driver"
                    if resolved == driver
                    else "backend"
                    if resolved.name == "ppcx64"
                    else "config"
                    if resolved.suffix == ".cfg"
                    else "rtl"
                    if package == "fp-units-rtl-3.2.2"
                    else "support"
                )
                paths[str(resolved)] = {
                    "path": str(resolved),
                    "role": role,
                    **identity(resolved),
                }
    for name in ("/etc/fpc.cfg",):
        path = compiler_path(Path(name).resolve())
        aliases[name] = str(path)
        paths[str(path)] = {
            "path": str(path),
            "role": "config",
            **identity(path),
        }
    for executable in ("as", "ld", "ppcx64"):
        alias = Path(shutil.which(executable) or "")
        path = compiler_path(alias.resolve())
        aliases[str(alias)] = str(path)
        paths[str(path)] = {
            "path": str(path),
            "role": "backend" if executable == "ppcx64" else "support",
            **identity(path),
        }
        provenance[executable] = bounded_command(
            ["dpkg-query", "-S", str(path)], deadline
        ).stdout
    version = bounded_command([str(driver), "-iV"], deadline).stdout.strip()
    architecture = bounded_command(
        [str(driver), "-iTP"], deadline
    ).stdout.strip()
    record = {
        "status": "PASS_COMPILER_READINESS",
        "version": version,
        "package_version": PACKAGE_VERSION,
        "architecture": architecture,
        "compiler_path": str(driver),
        "binary_identity": identity(driver),
        "package_provenance": provenance,
        "toolchain_files": [paths[name] for name in sorted(paths)],
        "toolchain_aliases": [
            {"path": name, "resolved": aliases[name]}
            for name in sorted(aliases)
        ],
    }
    validate_compiler(record)
    return record


def remaining_seconds(deadline, now=None):
    now = time.monotonic() if now is None else now
    seconds = math.floor(deadline - now)
    require(seconds >= 1, "Shared workload deadline exhausted")
    return seconds


def preparation_properties(seconds):
    require(
        type(seconds) is int and 1 <= seconds <= 7200,
        "Invalid remaining preparation budget",
    )
    return {
        "MemoryMax": str(4096 * 1024**2),
        "MemoryHigh": str(4096 * 1024**2),
        "MemorySwapMax": "0",
        "CPUQuota": "100%",
        "CPUQuotaPeriodSec": "100ms",
        "TasksMax": "128",
        "RuntimeMaxSec": str(seconds),
        "TimeoutStopSec": "5",
        "KillMode": "control-group",
        "SendSIGKILL": "yes",
        "Restart": "no",
        "Type": "exec",
        "RemainAfterExit": "yes",
        "LimitCORE": "0",
    }


def pressure(text):
    require(type(text) is str, "Pressure telemetry absent")
    rows = {}
    for line in text.splitlines():
        match = re.fullmatch(
            r"(some|full) avg10=([0-9.]+) avg60=([0-9.]+) "
            r"avg300=([0-9.]+) total=([0-9]+)",
            line,
        )
        require(match and match[1] not in rows, "Pressure telemetry malformed")
        rows[match[1]] = [float(match[index]) for index in (2, 3, 4)]
    require(
        set(rows) == {"some", "full"}
        and all(
            math.isfinite(value) and 0 <= value <= 100
            for values in rows.values()
            for value in values
        ),
        "Pressure telemetry incomplete",
    )
    return rows


def validate_sample(sample, host):
    """Apply existing ceilings/events/reserve and retain measured PSI."""
    require(
        all(type(sample.get(name)) is str for name in pilot.SAMPLE_FIELDS),
        "Live resource telemetry incomplete",
    )
    numbers = {
        name: int(sample[name])
        for name in (
            "memory.current",
            "memory.peak",
            "memory.swap.current",
            "pids.current",
        )
    }
    require(
        all(value >= 0 for value in numbers.values())
        and numbers["memory.peak"] <= 4096 * 1024**2
        and numbers["memory.swap.current"] == 0
        and numbers["pids.current"] <= 128,
        "Resource ceiling or swap",
    )
    events = dict(
        line.split() for line in sample["memory.events"].splitlines()
    )
    require(
        {"high", "max", "oom", "oom_kill"} <= events.keys()
        and not any(
            int(events.get(name, 0))
            for name in ("high", "max", "oom", "oom_kill", "oom_group_kill")
        ),
        "Memory event observed",
    )
    cpu = dict(line.split() for line in sample["cpu.stat"].splitlines())
    require(int(cpu["usage_usec"]) >= 0, "CPU telemetry invalid")
    pressure(sample["memory.pressure"])
    pressure(host["memory_pressure"])
    require(host["MemAvailable"] >= 8192 * 1024**2, "Host 8 GiB reserve lost")
    require(host["SwapTotal"] - host["SwapFree"] == 0, "Host swap in use")


def host_sample():
    host = pilot._memory(Path("/proc/meminfo").read_text())
    host["memory_pressure"] = Path("/proc/pressure/memory").read_text()
    host["monotonic_seconds"] = time.monotonic()
    return host


def validate_readiness(review, control, current_run):
    require(
        all(
            review.get(key) == value
            for key, value in {
                "status": "PASS",
                "stage": "readiness",
                "independent_review": "PASS",
                "source_commit": control["source_commit"],
                "manifest_sha256": MANIFEST_SHA256,
                "compiler": control["compiler"],
                "cleanup": True,
                "native_tests": 1,
                "skips": 0,
                "input_integrity": True,
                "runtime_profile_id": pilot.EXPECTED_PROFILE,
            }.items()
        )
        and review.get("cleanup") is True
        and type(review.get("native_tests")) is int
        and type(review.get("skips")) is int
        and review.get("input_integrity") is True
        and type(review.get("run_id")) is int
        and review["run_id"] > 0
        and review["run_id"] != int(current_run)
        and valid_hash(review.get("evidence_sha256")),
        "Independent exact compiler/runtime readiness is required",
    )


def preserve_copy(source, destination):
    payload._regular(source)
    with source.open("rb") as incoming, destination.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
        outgoing.flush()
        os.fsync(outgoing.fileno())
    require(identity(source) == identity(destination), "Evidence copy differs")
    return identity(destination)


def preserve_generation_failure(generated, rows, evidence):
    """Retain only the first incomplete/failed selected request's raw bytes."""
    for row in rows:
        name = row["name"]
        folder = (
            "source_generator"
            if name in ("bolt", "p-bolt")
            else "generated-raw"
        )
        stdout = generated / folder / (name + ".faces.json")
        stderr = generated / "generated-raw" / (name + ".stderr")
        process = Path(str(stdout) + ".process.json")
        if not stdout.exists() and not stderr.exists():
            continue
        result = read(process) if process.exists() else None
        if result is not None and result.get("returncode") == 0:
            try:
                historical = row.get("historical_raw_identity")
                if read(stdout).get("status") == "PASS" and (
                    historical is None or identity(stdout) == historical
                ):
                    continue
            except (OSError, ValueError, UnicodeError):
                # A zero process exit does not make malformed source output pass.
                pass
        record = {
            "request": name,
            "request_identity": row["request_identity"],
            "process": result,
            "process_metadata_present": process.exists(),
            "streams": {},
        }
        for kind, path in (("stdout", stdout), ("stderr", stderr)):
            record["streams"][kind] = (
                preserve_copy(path, evidence / ("failed-request." + kind))
                if path.exists()
                else None
            )
        write(evidence / "failed-request.json", record)
        if process.exists():
            preserve_copy(process, evidence / "failed-request.process.json")
        return record
    return None


def preserve_native_failure(generated, evidence):
    results = {}
    for source, destination in (
        (
            "native-x2/components/component-results.json",
            "component-results.json",
        ),
        ("native-x2/ZY.failure.txt", "ZY.failure.txt"),
    ):
        path = generated / source
        if path.exists():
            results[destination] = preserve_copy(path, evidence / destination)
    return results


def generation_sequence(work, control, lease, deadline):
    """Never enter native execution with a failed or populated host tree."""
    prepared = run_preparation(work, control, lease, deadline)
    require(
        prepared.get("status") == "PASS" and prepared.get("cleanup") is True,
        "Preparation or complete descendant cleanup failed",
    )
    native = run_native(
        work,
        control,
        lease=lease,
        seconds=remaining_seconds(deadline),
        stage="native",
    )
    return {"preparation": prepared, "native": native}


def source_unit():
    run = os.environ.get("GITHUB_RUN_ID", "")
    require(re.fullmatch(r"[1-9][0-9]*", run), "Missing hosted run identity")
    return "tracktemplate-zy-source-" + run + ".service"


def show_unit(unit, deadline):
    fields = (
        "Id",
        "InvocationID",
        "ControlGroup",
        "MainPID",
        "ControlPID",
        "ActiveState",
        "SubState",
        "ExecMainCode",
        "ExecMainStatus",
        "ExecMainExitTimestampMonotonic",
        "Result",
        "ExecStart",
        "KillMode",
        "Restart",
        "SendSIGKILL",
        "RuntimeMaxUSec",
        "TimeoutStopUSec",
    )
    args = ["systemctl", "--user", "show", unit]
    args.extend("--property=" + name for name in fields)
    result = bounded_command(args, deadline, check=False)
    require(result.returncode in (0, 4), "Source unit query failed")
    return unique_object(
        line.split("=", 1) for line in result.stdout.splitlines()
    )


def duration_seconds(text):
    if str(text).isdigit():
        return int(text) / 1000000
    units = {"h": 3600, "min": 60, "s": 1, "ms": 0.001, "us": 0.000001}
    pieces = re.findall(r"([0-9.]+)(h|min|ms|us|s)", str(text))
    require(pieces, "Missing kernel runtime duration")
    return sum(float(value) * units[unit] for value, unit in pieces)


def source_owner(state, intent, previous=None):
    unit = intent["unit"]
    group = (
        f"/user.slice/user-{os.getuid()}.slice/"
        f"user@{os.getuid()}.service/app.slice/{unit}"
    )
    stopped = (
        previous is not None
        and state.get("ControlGroup") == ""
        and state.get("MainPID") == "0"
        and state.get("ControlPID") == "0"
    )
    match = re.search(r"argv\[\]=(.*?)\s*;", state.get("ExecStart", ""))
    require(
        state.get("Id") == unit
        and (state.get("ControlGroup") == group or stopped)
        and re.fullmatch(r"[0-9a-f]{32}", state.get("InvocationID", ""))
        and state.get("KillMode") == "control-group"
        and state.get("Restart") == "no"
        and state.get("SendSIGKILL") == "yes"
        and duration_seconds(state.get("RuntimeMaxUSec")) == intent["seconds"]
        and duration_seconds(state.get("TimeoutStopUSec")) == 5
        and match
        and shlex.split(match[1]) == intent["command"],
        "Source unit ownership, deadline or command differs",
    )
    owner = {
        "unit": unit,
        "invocation": state["InvocationID"],
        "cgroup": group,
        "intent": intent,
    }
    require(previous is None or owner == previous, "Source invocation changed")
    return owner


def source_cleanup(work):
    """Stop only the recorded source service; no unproved handoff is allowed."""
    result = {"cleanup": False, "errors": []}
    owner_path = work / "evidence/source-ownership.json"
    intent_path = work / "evidence/source-intent.json"
    deadline = time.monotonic() + 15
    try:
        if not intent_path.exists():
            return {"cleanup": True, "never_started": True, "errors": []}
        intent = read(intent_path)
        require(intent["unit"] == source_unit(), "Source unit name differs")
        state = show_unit(intent["unit"], deadline)
        owner = read(owner_path) if owner_path.exists() else None
        # A failed launch can leave an intent but no service or side effect.
        if (
            owner is None
            and state.get("InvocationID") == ""
            and state.get("MainPID") == "0"
            and state.get("ControlGroup") == ""
        ):
            return {"cleanup": True, "never_started": True, "errors": []}
        owner = source_owner(state, intent, owner)
        group = Path("/sys/fs/cgroup") / owner["cgroup"].lstrip("/")
        result["owner"] = owner
        if state.get("ActiveState") not in ("inactive", "failed"):
            bounded_command(
                ["systemctl", "--user", "stop", owner["unit"]], deadline
            )
        while True:
            state = show_unit(owner["unit"], deadline)
            result["final_state"] = state
            if state.get("InvocationID"):
                source_owner(state, intent, owner)
            if (
                guard._empty(group)
                and state.get("MainPID") == "0"
                and state.get("ControlPID") == "0"
            ):
                result.update(cleanup=True, group_removed=not group.exists())
                break
            require(time.monotonic() < deadline, "Source descendants remain")
            time.sleep(0.1)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ):
        result["errors"].append(traceback.format_exc())
    return result


def run_preparation(work, control, lease, deadline):
    stage = control["stage"]
    seconds = remaining_seconds(deadline)
    approved = work / "approved"
    generated = work / "generated"
    verify_inputs(approved)
    if stage == "native":
        compiler = validate_compiler(
            read(work / "evidence/compiler-readiness.json")
        )
        command = [
            "/usr/bin/python3",
            "-B",
            str(approved / "x2/build_x2_zy.py"),
            "prepare",
            "--source",
            str(approved / "source"),
            "--work",
            str(generated),
            "--compiler",
            str(compiler),
            "--compiler-readiness",
            str(work / "evidence/compiler-readiness.json"),
        ]
    else:
        command = [
            "/usr/bin/python3",
            "-B",
            str(Path(__file__)),
            "compiler-readiness",
            str(work),
        ]
    # The shell stops before any compiler or input helper can execute.
    gated = [
        "/bin/sh",
        "-c",
        'kill -STOP "$$"; exec "$@"',
        "zy-source",
        *command,
    ]
    intent = {
        "unit": source_unit(),
        "command": gated,
        "seconds": seconds,
        "absolute_deadline": deadline,
        "lease_id": lease.lease_id,
    }
    prior = show_unit(intent["unit"], deadline)
    require(
        not prior.get("InvocationID") and prior.get("MainPID", "0") == "0",
        "Source unit already exists",
    )
    write(work / "evidence/source-intent.json", intent)
    home = work / "compiler-home"
    home.mkdir(mode=0o700)
    properties = preparation_properties(seconds)
    properties.update(
        Slice="app.slice",
        WorkingDirectory=str(ROOT),
        StandardOutput="append:"
        + str(work / "evidence/source-service.stdout"),
        StandardError="append:" + str(work / "evidence/source-service.stderr"),
        Environment="HOME="
        + str(home)
        + " PATH=/usr/bin:/bin LANG=C LC_ALL=C "
        "PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1",
    )
    arguments = [
        "systemd-run",
        "--user",
        "--quiet",
        "--unit=" + intent["unit"],
    ]
    arguments.extend(
        "--property=" + key + "=" + value for key, value in properties.items()
    )
    arguments.extend(gated)
    result = {
        "status": "FAIL",
        "cleanup": False,
        "errors": [],
        "command": arguments,
        "python_child_timeout_seconds": 7200,
        "effective_tree_budget_seconds": seconds,
    }
    live_samples = 0
    try:
        bounded_command(arguments, deadline)
        state = show_unit(intent["unit"], deadline)
        owner = source_owner(state, intent)
        write(work / "evidence/source-ownership.json", owner)
        group = Path("/sys/fs/cgroup") / owner["cgroup"].lstrip("/")
        expected = {
            "memory.max": str(4096 * 1024**2),
            "memory.high": str(4096 * 1024**2),
            "memory.swap.max": "0",
            "cpu.max": "100000 100000",
            "pids.max": "128",
        }
        kernel = {
            name: (group / name).read_text().strip() for name in expected
        }
        require(kernel == expected, "Source kernel limits differ")
        pid = int(state["MainPID"])
        require(
            pid > 0
            and re.search(
                r"^State:\s+T", Path(f"/proc/{pid}/status").read_text(), re.M
            )
            and (group / "cgroup.procs").read_text().split() == [str(pid)],
            "Source service is not stopped alone at its release gate",
        )
        result["kernel_limits"] = kernel
        record = lease.read()
        record.update(
            scope=owner["unit"],
            invocation=owner["invocation"],
            cgroup=owner["cgroup"],
        )
        lease.write(record)
        remaining_seconds(deadline)
        require(
            not (work / "evidence/absolute-deadline-fired.json").exists(),
            "Absolute workload deadline fired",
        )
        bounded_command(
            [
                "systemctl",
                "--user",
                "kill",
                "--kill-whom=all",
                "--signal=SIGCONT",
                owner["unit"],
            ],
            deadline,
        )
        with (work / "evidence/source-measurements.jsonl").open("x") as stream:
            while True:
                state = show_unit(owner["unit"], deadline)
                source_owner(state, intent, owner)
                terminated = (
                    int(state.get("ExecMainExitTimestampMonotonic", "0")) > 0
                )
                sample, host = guard._sample(group), host_sample()
                stream.write(
                    json.dumps({"cgroup": sample, "host": host}) + "\n"
                )
                stream.flush()
                if group.exists():
                    validate_sample(sample, host)
                    live_samples += 1
                else:
                    require(terminated, "Live source cgroup disappeared")
                if terminated:
                    result["terminal_state"] = state
                    require(
                        state.get("ExecMainCode") == "1"
                        and state.get("ExecMainStatus") == "0"
                        and state.get("Result") == "success",
                        "Source preparation failed or exhausted its budget",
                    )
                    require(
                        stage == "readiness"
                        or (work / "evidence/source-service.stdout")
                        .read_text()
                        .splitlines()
                        .count("X2_ZY_SOURCE_PREPARATION_COMPLETE")
                        == 1,
                        "Source preparation sentinel missing",
                    )
                    remaining_seconds(deadline)
                    require(live_samples > 0, "Source resource samples absent")
                    result["status"] = "PASS"
                    break
                remaining_seconds(deadline)
                time.sleep(0.1)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        InterruptedError,
        subprocess.SubprocessError,
    ):
        result["errors"].append(traceback.format_exc())
    finally:
        cleanup = source_cleanup(work)
        result.update(cleanup=cleanup["cleanup"], finalization=cleanup)
        result["live_samples"] = live_samples
        if cleanup["cleanup"]:
            record = lease.read()
            for key in ("scope", "invocation", "cgroup"):
                record.pop(key, None)
            lease.write(record)
        else:
            result["status"] = "FAIL"
        if stage == "native" and result["status"] != "PASS":
            rows = read(approved / "x2/x2-generation-settings.json")[
                "requests"
            ]
            result["failed_request"] = preserve_generation_failure(
                generated, rows, work / "evidence"
            )
        for name in ("compile.stdout", "compile.stderr"):
            if (generated / name).is_file():
                preserve_copy(generated / name, work / "evidence" / name)
        write(work / "evidence/source-result.json", result)
    return result


def deadline_intent(work, lease, deadline):
    record = {
        "schema": 1,
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "pid": os.getpid(),
        "process_start": guard._process_start(os.getpid()),
        "lease_path": str(lease.path),
        "lease_id": lease.lease_id,
        "deadline": deadline,
        "source_commit": os.environ["GITHUB_SHA"],
    }
    write(work / "evidence/absolute-deadline.json", record)
    unit = "tracktemplate-zy-deadline-" + str(record["run_id"])
    seconds = remaining_seconds(deadline)
    arguments = [
        "systemd-run",
        "--user",
        "--quiet",
        "--unit=" + unit,
        "--on-active=" + str(seconds) + "s",
        "--timer-property=AccuracySec=10ms",
        "--timer-property=RandomizedDelaySec=0",
        "-p",
        "MemoryMax=64M",
        "-p",
        "MemorySwapMax=0",
        "-p",
        "CPUQuota=25%",
        "-p",
        "TasksMax=16",
        "-p",
        "RuntimeMaxSec=10s",
        "-p",
        "TimeoutStopSec=1s",
        "-p",
        "StandardOutput=append:"
        + str(work / "evidence/absolute-deadline.stdout"),
        "-p",
        "StandardError=append:"
        + str(work / "evidence/absolute-deadline.stderr"),
        "/usr/bin/python3",
        "-B",
        str(Path(__file__)),
        "deadline",
        str(work),
    ]
    bounded_command(arguments, deadline)
    state = bounded_command(
        [
            "systemctl",
            "--user",
            "show",
            unit + ".timer",
            "-p",
            "ActiveState",
            "-p",
            "TimersMonotonic",
            "-p",
            "NextElapseUSecMonotonic",
        ],
        deadline,
    ).stdout
    interval = re.search(r"OnActiveUSec=([^;]+);", state)
    next_elapse = re.search(r"^NextElapseUSecMonotonic=(.+)$", state, re.M)
    require(
        "ActiveState=active" in state
        and interval
        and duration_seconds(interval[1]) == seconds
        and next_elapse
        and duration_seconds(next_elapse[1]) <= deadline,
        "Absolute deadline timer unproved",
    )
    write(
        work / "evidence/absolute-deadline-armed.json",
        {
            "unit": unit,
            "seconds": seconds,
            "state": state,
            "command": arguments,
        },
    )
    return unit


def absolute_stop(work):
    """Independent timer kills only the lease-bound current invocation."""
    intent = read(work / "evidence/absolute-deadline.json")
    require(
        type(intent["run_id"]) is int and intent["run_id"] > 0,
        "Invalid absolute deadline owner",
    )
    expected = Path("/run/user") / str(os.getuid()) / guard.LOCK_NAME
    require(intent["lease_path"] == str(expected), "Deadline lease differs")
    result = {"fired": True, "observations": [], "errors": []}
    # Immutable per-scope ownership avoids racing a handoff lease rewrite.
    for relative in ("source-ownership.json", "guard/ownership.json"):
        path = work / "evidence" / relative
        if not path.exists():
            continue
        try:
            owner = read(path)
            if relative == "source-ownership.json":
                require(
                    owner["intent"]["lease_id"] == intent["lease_id"],
                    "Source deadline lease differs",
                )
                scope = owner["unit"]
                require(
                    scope
                    == "tracktemplate-zy-source-"
                    + str(intent["run_id"])
                    + ".service",
                    "Source deadline unit differs",
                )
            else:
                require(
                    owner["lease_id"] == intent["lease_id"]
                    and owner["supervisor_pid"] == intent["pid"]
                    and owner["supervisor_start"] == intent["process_start"],
                    "Native deadline owner differs",
                )
                scope = owner["scope"]
                require(
                    re.fullmatch(
                        r"app-flatpak-org\.freecad\.FreeCAD-[A-Za-z0-9_-]+\.scope",
                        scope,
                    ),
                    "Unsupported native deadline scope",
                )
            invocation = owner["invocation"]
            group_name = (
                f"/user.slice/user-{os.getuid()}.slice/"
                f"user@{os.getuid()}.service/app.slice/{scope}"
            )
            require(
                owner["cgroup"] == group_name
                and re.fullmatch(r"[0-9a-f]{32}", invocation),
                "Deadline cgroup or invocation differs",
            )
            context, commands = guard.GuardContext(), []
            group = context.cgroup_root / group_name.lstrip("/")
            empty = guard._empty(group)
            if not empty:
                require(
                    guard._identity(context, commands, scope) == invocation,
                    "Deadline invocation changed",
                )
                require(
                    guard._kill(context, commands, scope, invocation),
                    "Absolute deadline kill failed",
                )
            result["observations"].append(
                {
                    "scope": scope,
                    "invocation": invocation,
                    "empty_before": empty,
                    "commands": commands,
                }
            )
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            subprocess.SubprocessError,
        ):
            result["errors"].append(traceback.format_exc())
    try:
        if guard._process_start(intent["pid"]) == intent["process_start"]:
            os.kill(intent["pid"], signal.SIGTERM)
    except ProcessLookupError:
        result["coordinator_already_exited"] = True
    write(work / "evidence/absolute-deadline-fired.json", result)
    return 1


def run_native(work, control, *, lease, seconds, stage):
    """Use the unchanged qualified Flatpak gate with only remaining time."""
    config = work / "run-config.json"
    argv = [
        "flatpak",
        "run",
        "--command=FreeCADCmd",
        "--env=OMP_NUM_THREADS=1",
        "--env=OPENBLAS_NUM_THREADS=1",
        "--env=TRACKTEMPLATE_ZY_RUN_CONFIG=" + str(config),
        "--env=TRACKTEMPLATE_ZY_RUN_CONFIG_SHA256="
        + identity(config)["sha256"],
        guard.APP_ID,
        "-P",
        str(ROOT / "tests"),
        "-t",
        "hosted_to_zy_generation_suite.ZyGeneration.test_" + stage,
    ]
    clean = {
        name: os.environ[name]
        for name in (
            "HOME",
            "USER",
            "LOGNAME",
            "XDG_RUNTIME_DIR",
            "DBUS_SESSION_BUS_ADDRESS",
        )
        if name in os.environ
    }
    clean.update(
        PATH="/usr/bin:/bin", LANG="C", LC_ALL="C", PYTHONDONTWRITEBYTECODE="1"
    )
    absolute = read(work / "evidence/absolute-deadline.json")["deadline"]

    def guarded_command(arguments, **kwargs):
        if "--signal=SIGCONT" in arguments:
            remaining_seconds(absolute)
            require(
                not (work / "evidence/absolute-deadline-fired.json").exists(),
                "Native release after absolute deadline refused",
            )
        return subprocess.run(arguments, **kwargs)

    observation_failures = []

    def observe(seconds_to_sleep):
        # Never raise from a sleep callback used by the guard's finally path.
        try:
            host = host_sample()
            with (work / "evidence/host.jsonl").open("a") as stream:
                stream.write(json.dumps(host) + "\n")
            pressure(host["memory_pressure"])
            require(time.monotonic() < absolute, "Absolute deadline exhausted")
            require(
                host["MemAvailable"] >= 8192 * 1024**2
                and host["SwapTotal"] == host["SwapFree"],
                "Host reserve or swap stop",
            )
        except (OSError, ValueError, KeyError):
            observation_failures.append(traceback.format_exc())
            try:
                owner = lease.read()
                if owner.get("scope") and owner.get("invocation"):
                    guard._kill(
                        guard.GuardContext(),
                        [],
                        owner["scope"],
                        owner["invocation"],
                    )
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                observation_failures.append(traceback.format_exc())
        time.sleep(seconds_to_sleep)

    limits = guard.ValidationLimits(4096, seconds)
    result = guard.run_guarded_flatpak(
        argv,
        limits=limits,
        evidence_dir=work / "evidence/guard",
        lease=lease,
        context=guard.GuardContext(run=guarded_command, sleep=observe),
        cwd=ROOT,
        env=clean,
        isolate_profile=True,
    )
    with patch.object(pilot, "OUTPUT", work / "evidence"):
        clearance = pilot._deadline_clearance(result) and pilot._clearance()
    output = work / "evidence/guard"
    samples = [
        json.loads(line)
        for line in (output / "measurements.jsonl").read_text().splitlines()
    ]
    stdout, stderr = (
        (output / "stdout").read_text(),
        (output / "stderr").read_text(),
    )
    with ExitStack() as stack:
        stack.enter_context(patch.object(pilot, "LIMITS", limits))
        stack.enter_context(
            patch.object(pilot, "GEOMETRY_SENTINEL", dict(SENTINELS)[stage])
        )
        stack.enter_context(
            patch.object(
                pilot,
                "_qualified_runtime",
                lambda text: require(
                    text.count("TRACKTEMPLATE_ZY_RUNTIME=") == 1
                    and read(work / "evidence/native-result.json")[
                        "runtime_profile_id"
                    ]
                    == pilot.EXPECTED_PROFILE,
                    "Qualified generation runtime absent",
                ),
            )
        )
        assessment = pilot.assess_result(
            result,
            stdout,
            stderr,
            samples,
            clearance,
            deadline_clearance=clearance,
        )
    assessment["classification"] = (
        (
            "GENERATION_READINESS_ONLY"
            if stage == "readiness"
            else "NEW_X2_CONSTRUCTION_ONLY"
        )
        if assessment["status"] == "PASS"
        else assessment["classification"]
    )
    if observation_failures:
        assessment.update(
            status="FAIL",
            classification="HOST_TELEMETRY_STOP",
            observation_failures=observation_failures,
        )
    write(work / "evidence/native-assessment.json", assessment)
    return assessment


def resource_contract(stage):
    require(stage in ("readiness", "native"), "Unsupported generation stage")
    return {
        "memory_mib": 4096,
        "cpu_percent": 100,
        "tasks": 128,
        "swap_bytes": 0,
        "reserve_mib": 8192,
        "timeout_seconds": 90 if stage == "readiness" else 7200,
    }


def validate_control(control, stage, environ, root=ROOT):
    """Bind existing owner approval and the exact independently reviewed run."""
    fields = {
        "schema",
        "workload",
        "stage",
        "scope_id",
        "source_commit",
        "workflow_commit",
        "manifest_sha256",
        "entry_sha256",
        "execution_enabled",
        "independent_review",
        "independent_review_sha256",
        "dispatch_nonce",
        "limits",
        "handling_decision",
        "access_review",
        "recovery",
        "source_publication",
        "input_archive",
        "control_files_sha256",
        "compiler",
        "compiler_record_asset",
        "readiness_review",
    }
    require(
        type(control) is dict
        and set(control) == fields
        and control.get("schema") == 1
        and type(control["schema"]) is int
        and control.get("workload") == WORKLOAD
        and control.get("stage") == stage
        and control.get("scope_id") == SCOPE
        and control.get("source_commit") == environ["GITHUB_SHA"]
        and control.get("workflow_commit") == environ["GITHUB_SHA"]
        and control.get("manifest_sha256") == MANIFEST_SHA256
        and control.get("entry_sha256") == ENTRY_SHA256
        and control.get("execution_enabled") is True
        and control.get("independent_review") == "PASS"
        and valid_hash(control.get("independent_review_sha256"))
        and re.fullmatch(r"[0-9a-f]{32}", control.get("dispatch_nonce", ""))
        and control.get("limits") == resource_contract(stage)
        and all(type(value) is int for value in control["limits"].values()),
        "Generation scope or execution review differs",
    )
    owner = control["handling_decision"]
    require(
        owner.get("status") == "APPROVED"
        and owner.get("sha256") == OWNER_DECISION_SHA256
        and owner.get("manifest_sha256") == MANIFEST_SHA256
        and valid_hash(owner.get("independent_review_sha256")),
        "Exact owner handling approval missing",
    )
    access = control["access_review"]
    require(
        access.get("status") == "PASS"
        and access.get("audited_at_utc")
        and access.get("owner") == "Richard-Gnitnub"
        and access.get("environment") == "l1-private-validation"
        and access.get("branches") == ["main"]
        and access.get("tags") == []
        and access.get("input_repository") == coordinator.INPUT_REPOSITORY
        and access.get("repository_public") is True
        and all(
            type(access.get(key)) is int and access[key] == 0
            for key in ("active_runs", "queued_runs", "waiting_runs")
        ),
        "Fresh owner/repository/environment/serial review absent",
    )
    for record, status in (
        (control["recovery"], "PASS"),
        (control["source_publication"], "PASS"),
    ):
        require(
            record.get("status") == status
            and record.get("manifest_sha256") == MANIFEST_SHA256
            and valid_hash(record.get("independent_review_sha256")),
            "Approved source publication or recovery unproved",
        )
    require(
        control["recovery"].get("source_commit") == environ["GITHUB_SHA"],
        "Recovery source differs",
    )
    archive = control["input_archive"]
    require(
        type(archive.get("asset_id")) is int
        and archive["asset_id"] > 0
        and archive.get("sha256") == ARCHIVE_SHA256
        and archive.get("bytes") == ARCHIVE_BYTES,
        "Exact approved archive unavailable",
    )
    pins = control["control_files_sha256"]
    require(
        set(pins) == set(CONTROL_FILES), "Generation source pins incomplete"
    )
    for name, expected in pins.items():
        require(
            valid_hash(expected)
            and identity(root / name)["sha256"] == expected,
            "Generation source changed",
        )
    require(
        identity(root / "tools/freecad_validation_guard.py")["sha256"]
        == pilot.GUARD_SHA256,
        "Existing native guard changed",
    )
    if stage == "native":
        validate_readiness(
            control["readiness_review"], control, environ["GITHUB_RUN_ID"]
        )
        compiler = control["compiler"]
        require(
            set(compiler) == {"sha256", "bytes"}
            and valid_hash(compiler["sha256"])
            and type(compiler["bytes"]) is int
            and 0 < compiler["bytes"] <= payload.MAX_CONTROL_BYTES,
            "Reviewed actual compiler identity absent",
        )
        asset = control["compiler_record_asset"]
        require(
            all(asset.get(key) == compiler[key] for key in compiler)
            and type(asset.get("asset_id")) is int
            and asset["asset_id"] > 0,
            "Compiler record publication differs",
        )
    else:
        require(
            control.get("compiler") is None
            and control.get("readiness_review") is None
            and control.get("compiler_record_asset") is None,
            "Readiness cannot predeclare compiler qualification",
        )


def prepare(stage, work):
    require(os.getuid() != 0 and not sys.flags.optimize, "Unsafe interpreter")
    host = coordinator.validate_host(
        os.environ, Path("/proc/meminfo").read_text()
    )
    control = json.loads(
        os.environ["L1_PRIVATE_CONTROL"], object_pairs_hook=unique_object
    )
    # Preserve the exact proposed control even when admission refuses it.
    write(work / "control.json", control)
    validate_control(control, stage, os.environ)
    require(
        coordinator.command("git", "rev-parse", "HEAD")
        == control["source_commit"]
        and not coordinator.command(
            "git", "status", "--porcelain", "--untracked-files=no"
        ),
        "Hosted source checkout differs",
    )
    write(
        work / "evidence/admission.json",
        {
            "status": "PASS",
            "source_commit": control["source_commit"],
            "manifest_sha256": MANIFEST_SHA256,
            "control": identity(work / "control.json"),
            "host": host,
            "scope": SCOPE,
        },
    )
    preserve_copy(
        work / "control.json", work / "evidence/generation-control.json"
    )


def acquire(stage, work):
    control = read(work / "control.json")
    validate_control(control, stage, os.environ)
    coordinator.validate_host(os.environ, Path("/proc/meminfo").read_text())
    coordinator.validate_input_repository()
    coordinator.download_asset(control["input_archive"], work / "inputs.tar")
    extract_inputs(work / "inputs.tar", work / "approved")
    require(
        identity(work / "approved/x2/build_x2_zy.py")["sha256"]
        == ENTRY_SHA256,
        "Approved generator entry changed",
    )
    if stage == "native":
        target = work / "evidence/compiler-readiness.json"
        coordinator.download_asset(
            control["compiler_record_asset"],
            target,
            maximum_bytes=payload.MAX_CONTROL_BYTES,
        )
        validate_compiler(read(target))
    write(
        work / "run-config.json",
        {
            "schema": 1,
            "stage": stage,
            "source_commit": control["source_commit"],
            "manifest_sha256": MANIFEST_SHA256,
            "entry_sha256": ENTRY_SHA256,
            "approved_directory": str(work / "approved"),
            "generated_directory": str(work / "generated"),
            "evidence_directory": str(work / "evidence"),
            "repository_root": str(ROOT),
            "run_id": int(os.environ["GITHUB_RUN_ID"]),
        },
    )
    write(
        work / "evidence/input-verification.json",
        {
            "status": "PASS",
            "archive": identity(work / "inputs.tar"),
            "manifest_sha256": MANIFEST_SHA256,
            "files": INPUT_COUNT,
            "bytes": INPUT_BYTES,
        },
    )


def interrupt(_signum, _frame):
    raise InterruptedError("Absolute generation deadline or cancellation")


def run(stage, work):
    control = read(work / "control.json")
    validate_control(control, stage, os.environ)
    coordinator.validate_host(os.environ, Path("/proc/meminfo").read_text())
    coordinator.require_finalization_time(stage, os.environ, time.time())
    for arguments, expected in (
        (("--show-commit", guard.APP_ID), pilot.APP_COMMIT),
        (("--show-runtime", guard.APP_ID), pilot.RUNTIME),
        (("--show-commit", pilot.RUNTIME), pilot.RUNTIME_COMMIT),
    ):
        require(
            coordinator.command("flatpak", "info", "--system", *arguments)
            == expected,
            "Qualified runtime package differs",
        )
    verify_inputs(work / "approved")
    result = {
        "status": "FAIL",
        "stage": stage,
        "workload": WORKLOAD,
        "source_commit": control["source_commit"],
        "errors": [],
        "manifest_sha256": MANIFEST_SHA256,
        "model_admitted": False,
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
    }
    started = time.monotonic()
    deadline = started + resource_contract(stage)["timeout_seconds"]
    old = {
        sig: signal.signal(sig, interrupt)
        for sig in (signal.SIGTERM, signal.SIGINT)
    }
    timer = None
    try:
        with guard.acquire_validation_lease(
            guard.GuardContext().runtime_dir
        ) as lease:
            guard._residual(lease, guard.GuardContext())
            require(
                not coordinator.command(
                    "flatpak", "ps", "--columns=application,pid"
                ),
                "Foreign Flatpak instance present",
            )
            timer = deadline_intent(work, lease, deadline)
            if stage == "native":
                validate_compiler(
                    read(work / "evidence/compiler-readiness.json")
                )
                result["scopes"] = generation_sequence(
                    work, control, lease, deadline
                )
            else:
                source = run_preparation(work, control, lease, deadline)
                require(
                    source.get("status") == "PASS"
                    and source.get("cleanup") is True,
                    "Compiler readiness or source-tree cleanup failed",
                )
                result["scopes"] = {
                    "preparation": source,
                    "native": run_native(
                        work,
                        control,
                        lease=lease,
                        seconds=remaining_seconds(deadline),
                        stage=stage,
                    ),
                }
            require(
                result["scopes"]["native"]["status"] == "PASS",
                "Qualified native result incomplete",
            )
            remaining_seconds(deadline)
            require(
                not (work / "evidence/absolute-deadline-fired.json").exists(),
                "Absolute deadline fired",
            )
            compiler = read(work / "evidence/compiler-readiness.json")
            validate_compiler(compiler)
            result["compiler"] = identity(
                work / "evidence/compiler-readiness.json"
            )
            verify_inputs(work / "approved")
            validate_control(control, stage, os.environ)
            result["status"] = "PASS"
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        InterruptedError,
        subprocess.SubprocessError,
    ):
        result["errors"].append(traceback.format_exc())
    finally:
        for sig in old:
            signal.signal(sig, signal.SIG_IGN)
        result["elapsed_seconds"] = time.monotonic() - started
        cleanup = source_cleanup(work)
        native_result = work / "evidence/guard/result.json"
        native_owner = work / "evidence/guard/ownership.json"
        native_clean = (
            read(native_result).get("cleanup_proved") is True
            if native_result.exists()
            else not native_owner.exists()
        )
        if timer and cleanup["cleanup"] and native_clean:
            stop = subprocess.run(
                [
                    "systemctl",
                    "--user",
                    "stop",
                    timer + ".timer",
                    timer + ".service",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            result["absolute_timer_stop"] = {
                "returncode": stop.returncode,
                "stdout": stop.stdout,
                "stderr": stop.stderr,
            }
            if stop.returncode:
                result["status"] = "FAIL"
        elif timer:
            result.update(status="FAIL", absolute_deadline_retained=True)
        generated = work / "generated"
        if result["status"] != "PASS" and generated.exists():
            result["native_failure_records"] = preserve_native_failure(
                generated, work / "evidence"
            )
        for name in ("x2-prepared.json", "x2-native-summary.json"):
            if (generated / name).exists():
                preserve_copy(generated / name, work / "evidence" / name)
        model = generated / "native-x2/ZY/ZY.FCStd"
        if result["status"] == "PASS" and stage == "native":
            result["generated_model"] = preserve_copy(
                model, work / "evidence/ZY-X2-Y.FCStd"
            )
        write(work / "evidence/assessment.json", result)
        for sig, handler in old.items():
            signal.signal(sig, handler)
    return 0 if result["status"] == "PASS" else 1


def finalize(work):
    if coordinator._installation_was_skipped(work):
        write(
            work / "evidence/process-finalization.json",
            {
                "cleanup": True,
                "never_started": True,
                "source": None,
                "native": None,
            },
        )
        return 0
    source = source_cleanup(work)
    native = {"cleanup": False, "errors": []}
    try:
        guard_result = work / "evidence/guard/result.json"
        owner = work / "evidence/guard/ownership.json"
        with patch.object(pilot, "OUTPUT", work / "evidence"):
            if guard_result.exists():
                record = read(guard_result)
                native["cleanup"] = (
                    record.get("cleanup_proved") is True
                    and pilot._deadline_clearance(record)
                    and pilot._clearance()
                )
            elif owner.exists():
                native["cleanup"] = coordinator.emergency_cleanup(
                    work, read(owner)
                )["proved"]
            else:
                native["cleanup"] = pilot._clearance()
                native["never_started"] = True
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ):
        native["errors"].append(traceback.format_exc())
    result = {
        "cleanup": source["cleanup"] and native["cleanup"],
        "source": source,
        "native": native,
    }
    write(work / "evidence/process-finalization.json", result)
    return 0 if result["cleanup"] else 1


def evidence_name(name):
    roots = {
        "prepare.log",
        "install.log",
        "acquisition.log",
        "execution.log",
        "finalizer.log",
        "seal.log",
        "publication.log",
        "admission.json",
        "generation-control.json",
        "input-verification.json",
        "assessment.json",
        "compiler-readiness.json",
        "source-intent.json",
        "source-ownership.json",
        "source-service.stdout",
        "source-service.stderr",
        "source-measurements.jsonl",
        "source-result.json",
        "absolute-deadline.json",
        "absolute-deadline-armed.json",
        "absolute-deadline-fired.json",
        "absolute-deadline.stdout",
        "absolute-deadline.stderr",
        "native-result.json",
        "native-failure.txt",
        "native-assessment.json",
        "host.jsonl",
        "clearance.json",
        "deadline-clearance.json",
        "emergency-cleanup.json",
        "process-finalization.json",
        "publication.json",
        "compile.stdout",
        "compile.stderr",
        "failed-request.stdout",
        "failed-request.stderr",
        "failed-request.json",
        "failed-request.process.json",
        "component-results.json",
        "ZY.failure.txt",
        "x2-prepared.json",
        "x2-native-summary.json",
        "ZY-X2-Y.FCStd",
    }
    guard_names = {
        "result.json",
        "control.json",
        "ownership.json",
        "stdout",
        "stderr",
        "wrapper.stdout",
        "measurements.jsonl",
        "watchdog.json",
        "commands.json",
    }
    require(
        name in roots or name.startswith("guard/") and name[6:] in guard_names,
        "Unapproved generation evidence member: " + name,
    )


def evidence_archive(work, destination):
    """Only reviewed output names enter the existing diagnostic transport."""
    require(not destination.exists(), "Evidence archive already exists")
    files, excluded = {}, []
    partial = destination.with_suffix(destination.suffix + ".partial")
    with partial.open("xb") as output:
        with tarfile.open(
            fileobj=output, mode="w", format=tarfile.USTAR_FORMAT
        ) as archive:
            for path in sorted((work / "evidence").rglob("*")):
                require(not path.is_symlink(), "Linked diagnostic refused")
                if path.is_relative_to(work / "evidence/guard/profile"):
                    if path.is_file():
                        excluded.append(
                            {
                                "member": path.relative_to(
                                    work / "evidence"
                                ).as_posix(),
                                "reason": "private-runtime-state",
                                **identity(path),
                            }
                        )
                    continue
                if path.is_file():
                    name = path.relative_to(work / "evidence").as_posix()
                    evidence_name(name)
                    files[name] = identity(path)
                    payload._add_bytes(
                        archive, "evidence/" + name, path.read_bytes()
                    )
            payload._add_bytes(
                archive,
                "evidence-manifest.json",
                encoded({"files": files, "excluded_inputs": excluded}),
            )
        output.flush()
        os.fsync(output.fileno())
    require(
        partial.stat().st_size <= 512 * 1024**2,
        "Existing evidence transport bound exceeded",
    )
    os.link(partial, destination)
    partial.unlink()
    return identity(destination)


def encoded(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def cleanup_owned(work):
    """Retire only exclusive run staging after original evidence readback."""
    require(
        read(work / "evidence/process-finalization.json")["cleanup"] is True,
        "Process cleanup must precede staging cleanup",
    )
    if (work / "approved").exists():
        verify_inputs(work / "approved")
    targets = (work / "approved", work / "generated", work / "compiler-home")
    inventory = []
    for directory in targets:
        require(
            directory.parent == work and not directory.is_symlink(),
            "Staging root differs",
        )
        if not directory.exists():
            continue
        for path in (directory, *directory.rglob("*")):
            require(
                not path.is_symlink()
                and path.stat().st_uid == os.getuid()
                and (path.is_dir() or path.is_file()),
                "Foreign staging member",
            )
            if path.is_file():
                inventory.append(
                    {
                        "member": path.relative_to(work).as_posix(),
                        **identity(path),
                    }
                )
    for directory in targets:
        if directory.exists():
            shutil.rmtree(directory)
        require(not directory.exists(), "Staging directory remains")
    archive = work / "inputs.tar"
    if archive.exists():
        require(
            identity(archive)
            == {"sha256": ARCHIVE_SHA256, "bytes": ARCHIVE_BYTES},
            "Input archive changed before cleanup",
        )
        archive.unlink()
    return {
        "cleanup": True,
        "removed_files": inventory,
        "source_immutable": True,
        "deletion_is_not_secure_erasure": True,
    }


def publish(work):
    result = {"primary": None, "errors": [], "retention_days": 30}
    try:
        result["primary"] = coordinator.verify_artifact(
            work / "evidence.tar",
            work / "readback-primary/evidence.tar",
            os.environ.get("L1_PRIMARY_UPLOAD", ""),
            os.environ.get("L1_PRIMARY_DOWNLOAD", ""),
            os.environ.get("L1_PRIMARY_ID", ""),
        )
        result["staging"] = cleanup_owned(work)
    except (OSError, ValueError, KeyError, TypeError):
        result["errors"].append(traceback.format_exc())
    write(work / "evidence/publication.json", result)
    evidence_archive(work, work / "publication.tar")
    return 0 if not result["errors"] else 1


def complete(stage, work, public):
    result = {
        "schema": 1,
        "workload": WORKLOAD,
        "stage": stage,
        "status": "FAIL",
        "manifest_sha256": MANIFEST_SHA256,
        "source_commit": os.environ["GITHUB_SHA"],
        "model_admitted": False,
        "errors": [],
    }
    try:
        result["artifact"] = coordinator.verify_artifact(
            work / "publication.tar",
            work / "readback-final/publication.tar",
            os.environ.get("L1_FINAL_UPLOAD", ""),
            os.environ.get("L1_FINAL_DOWNLOAD", ""),
            os.environ.get("L1_FINAL_ID", ""),
        )
        publication = read(work / "evidence/publication.json")
        assessment = read(work / "evidence/assessment.json")
        require(
            os.environ.get("L1_PUBLICATION") == "success"
            and publication["primary"] is not None
            and not publication["errors"]
            and publication["staging"]["cleanup"] is True
            and assessment["status"] == "PASS",
            "Generation/preservation incomplete",
        )
        result["status"] = "PASS"
    except (OSError, ValueError, KeyError, TypeError):
        # The small summary intentionally contains no raw diagnostic text.
        result["errors"].append("generation-or-preservation-incomplete")
    public.mkdir(mode=0o700, exist_ok=True)
    write(public / "summary.json", result)
    return 0 if result["status"] == "PASS" else 1


def dispatch(operation, stage, work, public):
    if operation == "prepare":
        prepare(stage, work)
    elif operation == "acquire":
        acquire(stage, work)
    elif operation == "run":
        return run(stage, work)
    elif operation == "finalize":
        return finalize(work)
    elif operation == "seal":
        evidence_archive(work, work / "evidence.tar")
    elif operation == "publish":
        return publish(work)
    elif operation == "complete":
        return complete(stage, work, public)
    elif operation == "finish":
        summary = read(public / "summary.json")
        return (
            0
            if (
                summary["status"] == "PASS"
                and summary["workload"] == WORKLOAD
                and summary["source_commit"] == os.environ["GITHUB_SHA"]
                and summary["manifest_sha256"] == MANIFEST_SHA256
                and summary["model_admitted"] is False
                and os.environ.get("L1_SUMMARY_UPLOAD") == "success"
            )
            else 1
        )
    else:
        raise ValueError("Unsupported generation operation")
    return 0


if __name__ == "__main__":
    require(
        len(sys.argv) == 3, "Expected fixed internal operation and workspace"
    )
    internal, workspace = sys.argv[1], Path(sys.argv[2])
    payload._regular(workspace / "control.json")
    if internal == "compiler-readiness":
        control = read(workspace / "control.json")
        require(
            control["stage"] == "readiness", "Compiler capture stage differs"
        )
        deadline = read(workspace / "evidence/absolute-deadline.json")[
            "deadline"
        ]
        write(
            workspace / "evidence/compiler-readiness.json",
            capture_compiler(deadline),
        )
        print("ZY_COMPILER_READINESS_CAPTURED", flush=True)
    elif internal == "deadline":
        raise SystemExit(absolute_stop(workspace))
    else:
        raise ValueError("Unsupported internal operation")
