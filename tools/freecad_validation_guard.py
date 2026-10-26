#!/usr/bin/env python3
"""Serialize and contain local FreeCAD validation without accepting its proof."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
APP_ID = "org.freecad.FreeCAD"
LOCK_NAME = "tracktemplate-freecad-validation.lock"
READY = "TT_SCOPE_GATE_READY\n"
RELEASED = "TT_SCOPE_GATE_RELEASED\n"
GATE = (
    'echo TT_SCOPE_GATE_READY; kill -STOP "$$"; '
    'echo TT_SCOPE_GATE_RELEASED; exec "$@"'
)
LEASE_ENV = "TRACKTEMPLATE_VALIDATION_LEASE_FD"
LEASE_ID_ENV = "TRACKTEMPLATE_VALIDATION_LEASE_ID"
ENTRY_ENV = "TRACKTEMPLATE_VALIDATION_RESERVED_ENTRY"


@dataclass(frozen=True)
class ValidationLimits:
    """Explicit run safety ceilings, distinct from product budgets."""

    memory_max_mib: int
    timeout_seconds: int
    cpu_percent: int = 100
    tasks_max: int = 128

    def __post_init__(self):
        for name, value in vars(self).items():
            if type(value) is not int or not 0 < value <= 2**31 - 1:
                raise ValueError(f"{name} must be a positive bounded integer")


@dataclass
class GuardContext:
    """Inject command operations and kernel paths for offline failure tests."""

    run: object = subprocess.run
    popen: object = subprocess.Popen
    proc_root: Path = Path("/proc")
    cgroup_root: Path = Path("/sys/fs/cgroup")
    runtime_dir: Path = field(
        default_factory=lambda: Path("/run/user") / str(os.getuid())
    )
    monotonic: object = time.monotonic
    sleep: object = time.sleep


class GuardFailure(RuntimeError):
    """Describe a failed admission or containment requirement."""

    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = reason


def _json_write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _process_start(pid, proc_root=Path("/proc")):
    text = (proc_root / str(pid) / "stat").read_text()
    return text.rsplit(")", 1)[1].split()[19]


def _runtime_path(runtime_dir):
    runtime = Path(runtime_dir)
    info = runtime.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o022
        or runtime.resolve() != runtime.absolute()
    ):
        raise ValueError("Validation runtime directory is not private")
    return runtime / LOCK_NAME


@dataclass
class ValidationLease:
    """An owned flock descriptor and its recoverable scope identity."""

    fd: int
    path: Path
    lease_id: str

    def read(self):
        os.lseek(self.fd, 0, os.SEEK_SET)
        raw = os.read(self.fd, 16385)
        if len(raw) > 16384:
            raise ValueError("Validation lease is oversized")
        return json.loads(raw) if raw else {}

    def write(self, value):
        encoded = (json.dumps(value, sort_keys=True) + "\n").encode()
        if len(encoded) > 16384:
            raise ValueError("Validation lease is oversized")
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.write(self.fd, encoded)
        os.ftruncate(self.fd, len(encoded))
        os.fsync(self.fd)

    def verify(self, runtime_dir):
        expected = _runtime_path(runtime_dir)
        if self.path != expected:
            raise ValueError("Validation lease belongs to another runtime")
        descriptor = os.fstat(self.fd)
        current = expected.lstat()
        if (
            self.path != expected
            or not stat.S_ISREG(descriptor.st_mode)
            or stat.S_ISLNK(current.st_mode)
            or descriptor.st_uid != os.getuid()
            or descriptor.st_mode & 0o077
            or (descriptor.st_dev, descriptor.st_ino)
            != (current.st_dev, current.st_ino)
            or self.read().get("lease_id") != self.lease_id
        ):
            raise ValueError("Validation lease identity is invalid")
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def acquire_validation_lease(runtime_dir):
    """Take one per-user lock shared by every TrackTemplate worktree."""
    path = _runtime_path(runtime_dir)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("Validation lock is not an owned regular file")
        if info.st_mode & 0o077:
            raise ValueError("Validation lock permissions are not private")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lease = ValidationLease(fd, path, "")
        previous = lease.read()
        lease.lease_id = uuid.uuid4().hex
        previous.update(
            lease_id=lease.lease_id,
            owner_pid=os.getpid(),
            owner_start=_process_start(os.getpid()),
        )
        lease.write(previous)
        yield lease
    finally:
        # Do not LOCK_UN: an authorised GUI child can share this same open
        # file description and must retain exclusion after its parent exits.
        os.close(fd)


def _command(context, records, argv, timeout=5):
    argv = [str(value) for value in argv]
    try:
        result = context.run(
            argv, capture_output=True, text=True, check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        records.append({"command": argv, "error": repr(error)})
        raise
    records.append({
        "command": argv, "exit": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
    })
    return result


def _identity(context, records, scope, timeout=5):
    result = _command(
        context, records,
        ["systemctl", "--user", "show", scope,
         "-p", "InvocationID", "--value"], timeout=timeout,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _empty(group):
    if group is None:
        return False
    try:
        lines = (group / "cgroup.events").read_text().splitlines()
        return "populated 0" in lines
    except FileNotFoundError:
        return not group.exists()
    except OSError:
        return False


def _residual(lease, context):
    prior = lease.read()
    relative = prior.get("cgroup")
    if relative:
        parts = Path(relative).parts
        if not relative.startswith("/user.slice/") or ".." in parts:
            raise GuardFailure("residual-scope")
        group = Path(context.cgroup_root) / relative.lstrip("/")
        if not _empty(group):
            raise GuardFailure("residual-scope")
        prior.pop("scope", None)
        prior.pop("invocation", None)
        prior.pop("cgroup", None)
        lease.write(prior)


def _payload_command(argv):
    argv = [str(item) for item in argv]
    if (
        len(argv) < 3
        or argv[0] not in ("flatpak", "/usr/bin/flatpak", "/bin/flatpak")
        or argv[1] != "run"
        or argv.count(APP_ID) != 1
    ):
        raise ValueError("Only the qualified FreeCAD Flatpak is supported")
    index = argv.index(APP_ID)
    options = argv[2:index]
    command = "FreeCAD"
    remaining = []
    for option in options:
        if option.startswith("--command="):
            command = option.split("=", 1)[1]
            if command not in ("FreeCAD", "FreeCADCmd"):
                raise ValueError("Unsupported FreeCAD entry command")
        elif option.startswith(("--env=", "--instance-id-fd=")):
            remaining.append(option)
        elif option == "--die-with-parent":
            remaining.append(option)
        else:
            raise ValueError("Unsupported Flatpak startup option")
    return [
        argv[0], "run", *remaining, "--command=sh", APP_ID,
        "-c", GATE, "tracktemplate-validation-gate", command,
        *argv[index + 1:],
    ]


def _gate(context, process, raw_path):
    expected = f"app-flatpak-{APP_ID}-{process.pid}.scope"
    until = context.monotonic() + 5
    while context.monotonic() < until and process.poll() is None:
        try:
            membership = (
                Path(context.proc_root) / str(process.pid) / "cgroup"
            ).read_text().strip()
            relative = membership.split("::", 1)[1]
            expected_group = (
                f"/user.slice/user-{os.getuid()}.slice/"
                f"user@{os.getuid()}.service/app.slice/{expected}"
            )
            if relative != expected_group:
                context.sleep(0.05)
                continue
            group = Path(context.cgroup_root) / relative.lstrip("/")
            pids = (group / "cgroup.procs").read_text().split()
            stopped = False
            for pid in pids:
                directory = Path(context.proc_root) / pid
                text = (directory / "status").read_text()
                uid_line = next(
                    line for line in text.splitlines()
                    if line.startswith("Uid:")
                )
                if set(uid_line.split()[1:]) != {str(os.getuid())}:
                    raise GuardFailure("scope-gate-unproved")
                if (directory / "cgroup").read_text().strip() != membership:
                    raise GuardFailure("scope-gate-unproved")
                _process_start(pid, Path(context.proc_root))
                stopped |= "State:\tT (stopped)" in text
            raw = raw_path.read_text()
            if stopped and raw == READY:
                return expected, relative, group
        except (OSError, IndexError, StopIteration):
            pass
        context.sleep(0.05)
    raise GuardFailure("scope-gate-unproved")


def _set_limits(context, records, scope, group, limits):
    memory = limits.memory_max_mib * 1024**2
    result = _command(context, records, [
        "systemctl", "--user", "set-property", "--runtime", scope,
        f"MemoryMax={memory}", f"MemoryHigh={memory}",
        "MemorySwapMax=0", f"CPUQuota={limits.cpu_percent}%",
        f"TasksMax={limits.tasks_max}",
    ])
    expected = {
        "memory.max": str(memory), "memory.high": str(memory),
        "memory.swap.max": "0",
        "cpu.max": f"{limits.cpu_percent * 1000} 100000",
        "pids.max": str(limits.tasks_max),
    }
    actual = {name: (group / name).read_text().strip() for name in expected}
    if result.returncode or actual != expected:
        raise GuardFailure("containment-unproved")
    return actual


def _arm(context, records, scope, invocation, limits, output):
    name = "tracktemplate-validation-" + uuid.uuid4().hex
    result = _command(context, records, [
        "systemd-run", "--user", f"--unit={name}",
        f"--on-active={limits.timeout_seconds}s",
        "--timer-property=AccuracySec=10ms",
        "--timer-property=RandomizedDelaySec=0",
        "-p", "MemoryMax=64M", "-p", "MemorySwapMax=0",
        "-p", "CPUQuota=25%", "-p", "TasksMax=16",
        "-p", "RuntimeMaxSec=10s", "-p", "TimeoutStopSec=1s",
        "-p", f"StandardOutput=append:{output / 'watchdog.json'}",
        "/usr/bin/python3", str(Path(__file__).resolve()),
        "watchdog", scope, invocation,
    ])
    if result.returncode:
        raise GuardFailure("deadline-unarmed")
    state = _command(context, records, [
        "systemctl", "--user", "show", name + ".timer",
        "-p", "ActiveState", "-p", "TimersMonotonic",
        "-p", "NextElapseUSecMonotonic",
    ])
    interval = re.search(r"OnActiveUSec=([^;]+);", state.stdout)
    duration = 0.0
    if interval:
        pieces = re.findall(r"([0-9.]+)(h|min|ms|us|s)", interval[1])
        units = {"h": 3600, "min": 60, "s": 1, "ms": .001, "us": .000001}
        duration = sum(float(value) * units[unit] for value, unit in pieces)
    if (
        state.returncode or "ActiveState=active" not in state.stdout
        or duration != limits.timeout_seconds
        or "NextElapseUSecMonotonic=" not in state.stdout
    ):
        raise GuardFailure("deadline-unarmed")
    return name


def _kill(context, records, scope, invocation):
    try:
        if _identity(context, records, scope, timeout=2) == invocation and invocation:
            return _command(context, records, [
                "systemctl", "--user", "kill", "--kill-whom=all",
                "--signal=SIGKILL", scope,
            ], timeout=2).returncode == 0
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def _sample(group):
    sample = {}
    for name in (
        "memory.current", "memory.peak", "memory.events",
        "memory.swap.current", "memory.pressure", "cpu.stat",
        "pids.current", "cgroup.events", "cgroup.procs",
    ):
        try:
            sample[name] = (group / name).read_text().strip()
        except OSError:
            sample[name] = None
    return sample


def _memory_kill(sample):
    for line in (sample.get("memory.events") or "").splitlines():
        name, count = line.split()
        if name in ("oom_kill", "oom_group_kill") and int(count):
            return True
    return False


def _private_profile(argv, output):
    """Use the bridge's qualified profile convention for native proofs."""
    profile = output / "profile"
    profile.mkdir(mode=0o700)
    directories = {
        "FREECAD_USER_HOME": "user-home", "FREECAD_USER_DATA": "user-data",
        "FREECAD_USER_TEMP": "temp", "XDG_CACHE_HOME": "xdg-cache",
        "XDG_CONFIG_HOME": "xdg-config", "XDG_DATA_HOME": "xdg-data",
        "PYTHONPYCACHEPREFIX": "python-cache",
    }
    environment = {}
    for name, directory in directories.items():
        target = profile / directory
        target.mkdir(mode=0o700)
        environment[name] = str(target)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    index = argv.index(APP_ID)
    effective = [
        *argv[:index],
        *(f"--env={name}={value}" for name, value in environment.items()),
        APP_ID, "--user-cfg", str(profile / "user.cfg"),
        "--system-cfg", str(profile / "system.cfg"), *argv[index + 1:],
    ]
    return effective, {"path": str(profile), "environment": environment}


def _config_evidence(profile):
    evidence = {}
    for name in ("user.cfg", "system.cfg"):
        path = Path(profile["path"]) / name
        entry = {"path": str(path), "exists": path.exists()}
        if path.is_file():
            data = path.read_bytes()
            entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        evidence[name] = entry
    return evidence


def _host_memory_admission(context, limits, result):
    """Refuse a ceiling that can exhaust the presently available host RAM."""
    try:
        raw = (Path(context.proc_root) / "meminfo").read_text()
        result["host_meminfo_before"] = raw
        values = {}
        for name in ("MemTotal", "MemAvailable"):
            matches = re.findall(rf"^{name}:\s+([0-9]+) kB$", raw, re.MULTILINE)
            if len(matches) != 1 or int(matches[0]) <= 0:
                raise ValueError(f"{name} is unknown")
            values[name] = int(matches[0]) * 1024
        result["host_memory_bytes_before"] = values
        ceiling = limits.memory_max_mib * 1024**2
        if ceiling >= values["MemAvailable"] or ceiling > values["MemTotal"]:
            raise ValueError("Requested ceiling exceeds available host RAM")
    except (OSError, ValueError) as error:
        raise GuardFailure("containment-unproved", str(error)) from error


def run_guarded_flatpak(
    argv, *, limits, evidence_dir, lease=None, context=None,
    cwd=None, env=None, pass_fds=(), isolate_profile=False,
):
    """Run one explicit FreeCAD workload; preserve payload and cleanup facts."""
    if not isinstance(limits, ValidationLimits):
        raise ValueError("Explicit validation limits are required")
    argv = [str(item) for item in argv]
    command = _payload_command(argv)
    if type(isolate_profile) is not bool:
        raise ValueError("isolate_profile must be boolean")
    context = context or GuardContext()
    if lease is not None:
        if not isinstance(lease, ValidationLease):
            raise ValueError("Invalid validation lease")
        lease.verify(context.runtime_dir)
    output = Path(evidence_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "schema_version": 1, "status": "failed", "process_exit": None,
        "cleanup_proved": False, "failure_reason": None,
        "receipt_path": str(output / "result.json"),
        "stdout_path": str(output / "stdout"),
        "stderr_path": str(output / "stderr"),
        "original_argv": [str(item) for item in argv],
        "effective_argv": argv,
        "guarded_argv": command, "limits": vars(limits),
        "diagnostic_safety_limits_only": True,
    }
    records = []
    manager = None
    process = None
    scope = invocation = timer = None
    group = None
    released = False
    deadline = None
    memory_killed = False
    old_handlers = {}
    raw = output / "wrapper.stdout"
    stderr = output / "stderr"
    raw.touch()
    stderr.touch()
    try:
        if lease is None:
            manager = acquire_validation_lease(context.runtime_dir)
            try:
                lease = manager.__enter__()
            except (OSError, ValueError) as error:
                raise GuardFailure("validation-busy", str(error)) from error
        _residual(lease, context)
        result["lease_id"] = lease.lease_id
        instances = _command(context, records, [
            "flatpak", "ps", "--columns=application,pid",
        ])
        if instances.returncode or any(
            line.split()[0] == APP_ID
            for line in instances.stdout.splitlines() if line.split()
        ):
            raise GuardFailure("foreign-freecad-instance")
        _host_memory_admission(context, limits, result)
        if isolate_profile:
            effective, profile = _private_profile(argv, output)
            command = _payload_command(effective)
            profile["config_before"] = _config_evidence(profile)
            result.update(
                effective_argv=effective, guarded_argv=command,
                private_profile=profile,
            )
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, _interrupt)
        with raw.open("w") as stdout_file, stderr.open("w") as stderr_file:
            process = context.popen(
                command, cwd=cwd, env=env, stdout=stdout_file,
                stderr=stderr_file, pass_fds=tuple(pass_fds),
            )
            scope, relative, group = _gate(context, process, raw)
            invocation = _identity(context, records, scope)
            if len(invocation) != 32:
                raise GuardFailure("scope-gate-unproved")
            record = lease.read()
            record.update(scope=scope, invocation=invocation, cgroup=relative)
            lease.write(record)
            result.update(scope=scope, invocation=invocation, cgroup=relative)
            _json_write(output / "ownership.json", {
                "schema_version": 1, "supervisor_pid": os.getpid(),
                "supervisor_start": _process_start(os.getpid()),
                "scope": scope, "invocation": invocation,
                "cgroup": relative, "lease_id": lease.lease_id,
            })
            try:
                result["kernel_limits"] = _set_limits(
                    context, records, scope, group, limits,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise GuardFailure("containment-unproved") from error
            deadline = context.monotonic() + limits.timeout_seconds
            try:
                timer = _arm(
                    context, records, scope, invocation, limits, output,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise GuardFailure("deadline-unarmed") from error
            result["watchdog"] = timer
            if _identity(context, records, scope) != invocation:
                raise GuardFailure("scope-gate-unproved")
            continued = _command(context, records, [
                "systemctl", "--user", "kill", "--kill-whom=all",
                "--signal=SIGCONT", scope,
            ])
            if continued.returncode:
                raise GuardFailure("scope-gate-unproved")
            released = True
            with (output / "measurements.jsonl").open("w") as measurements:
                while process.poll() is None:
                    sample = _sample(group)
                    sample["monotonic_seconds"] = context.monotonic()
                    memory_killed |= _memory_kill(sample)
                    measurements.write(json.dumps(sample) + "\n")
                    measurements.flush()
                    if context.monotonic() >= deadline + 5:
                        raise GuardFailure("deadline-exceeded")
                    context.sleep(0.1)
            result["process_exit"] = process.poll()
            memory_killed |= _memory_kill(_sample(group))
            if memory_killed:
                raise GuardFailure("memory-limit")
            if context.monotonic() >= deadline:
                raise GuardFailure("deadline-exceeded")
            if process.poll() != 0:
                unit_result = _command(context, records, [
                    "systemctl", "--user", "show", scope,
                    "-p", "Result", "--value",
                ])
                reason = (
                    "memory-limit" if "oom-kill" in unit_result.stdout
                    else "payload-nonzero"
                )
                raise GuardFailure(reason)
    except GuardFailure as error:
        result["failure_reason"] = error.reason
        result["error"] = str(error)
        if process is None:
            result["status"] = "refused"
    except (KeyboardInterrupt, InterruptedError):
        result["failure_reason"] = "interrupted"
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result["failure_reason"] = "scope-gate-unproved"
        result["error"] = repr(error)
    finally:
        for signum in old_handlers:
            signal.signal(signum, signal.SIG_IGN)
        observed_exit = process.poll() if process is not None else None
        if result["process_exit"] is None:
            result["process_exit"] = observed_exit
        if (
            observed_exit is not None and observed_exit != 0
            and result["failure_reason"] == "interrupted"
        ):
            # A requested stop cannot excuse a failure that preceded our kill.
            result["failure_reason"] = "payload-nonzero"
        if released:
            final_sample = _sample(group)
            result["before_cleanup"] = final_sample
            memory_killed |= _memory_kill(final_sample)
            if memory_killed:
                result["failure_reason"] = "memory-limit"
            elif deadline is not None and context.monotonic() >= deadline:
                result["failure_reason"] = "deadline-exceeded"
        result["execution_failure_reason"] = result["failure_reason"]
        clean = _empty(group)
        if not clean and scope and invocation:
            result["owned_cleanup_kill"] = _kill(
                context, records, scope, invocation,
            )
            until = context.monotonic() + 2
            while context.monotonic() < until:
                clean = _empty(group)
                if clean:
                    break
                context.sleep(0.1)
        elif process is not None and not scope and process.poll() is None:
            # The only possible payload is the unreleased shell gate.
            process.terminate()
        if process is not None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            result["process_exit_after_cleanup"] = process.poll()
            if result["process_exit"] is None:
                result["process_exit"] = process.poll()
        if released:
            after = _sample(group)
            result["after_cleanup"] = after
            memory_killed |= _memory_kill(after)
            try:
                unit = _command(context, records, [
                    "systemctl", "--user", "show", scope,
                    "-p", "Result", "--value",
                ], timeout=2)
                result["scope_result_after_cleanup"] = unit.stdout.strip()
                memory_killed |= unit.returncode == 0 and "oom-kill" in unit.stdout
            except (OSError, subprocess.SubprocessError) as error:
                result["scope_result_after_cleanup_error"] = repr(error)
            if memory_killed:
                result["failure_reason"] = "memory-limit"
            watchdog_output = output / "watchdog.json"
            if watchdog_output.exists():
                result["watchdog_evidence"] = str(watchdog_output)
                if result["failure_reason"] != "memory-limit":
                    result["failure_reason"] = "deadline-exceeded"
        if group is not None:
            result["cleanup_proved"] = clean
            if not clean:
                result["failure_reason"] = "cleanup-unproved"
                result["status"] = "failed"
            elif lease is not None:
                prior = lease.read()
                for name in ("scope", "invocation", "cgroup"):
                    prior.pop(name, None)
                lease.write(prior)
        if timer and clean:
            try:
                stopped = _command(context, records, [
                    "systemctl", "--user", "stop",
                    timer + ".timer", timer + ".service",
                ])
                result["deadline_cancellation_exit"] = stopped.returncode
            except (OSError, subprocess.SubprocessError) as error:
                result["deadline_cancellation_error"] = repr(error)
        elif timer:
            result["deadline_retained"] = True
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        if manager is not None:
            manager.__exit__(None, None, None)
        payload = raw.read_bytes()
        if payload.startswith((READY + RELEASED).encode()):
            payload = payload[len(READY + RELEASED):]
        elif payload.startswith(READY.encode()):
            payload = payload[len(READY):]
        Path(result["stdout_path"]).write_bytes(payload)
        if "private_profile" in result:
            result["private_profile"]["config_after"] = _config_evidence(
                result["private_profile"],
            )
        if (
            released and result["process_exit"] == 0
            and result["cleanup_proved"] and not result["failure_reason"]
        ):
            result["status"] = "completed"
        _json_write(output / "control.json", records)
        _json_write(output / "result.json", result)
    return result


def _interrupt(_signum, _frame):
    raise InterruptedError("Validation supervisor interrupted")


def _watchdog(scope, invocation):
    context = GuardContext()
    records = []
    result = {"scope": scope, "invocation": invocation}
    try:
        if not scope.startswith(f"app-flatpak-{APP_ID}-"):
            raise ValueError("Unsupported watchdog scope")
        result["kill_returned_success"] = _kill(context, records, scope, invocation)
        result["action"] = (
            "owned-kill-attempted" if result["kill_returned_success"]
            else "identity-refused-or-kill-failed"
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result["action"] = "identity-unknown"
        result["error"] = repr(error)
    result["commands"] = records
    print(json.dumps(result), flush=True)


def _env_limits():
    try:
        return ValidationLimits(
            memory_max_mib=int(os.environ[
                "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB"
            ]),
            timeout_seconds=int(os.environ[
                "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS"
            ]),
        )
    except (KeyError, ValueError) as error:
        raise ValueError("Explicit FreeCAD memory/deadline inputs required") from error


def _adopt_gui_lease(owner_pid=None):
    context = GuardContext()
    try:
        fd = int(os.environ[LEASE_ENV])
        lease_id = os.environ[LEASE_ID_ENV]
        if fd < 10:
            raise ValueError("Reserved descriptor overlaps bridge instance FD")
        lease = ValidationLease(fd, _runtime_path(context.runtime_dir), lease_id)
        lease.verify(context.runtime_dir)
        record = lease.read()
        pid = owner_pid or os.getpid()
        while pid > 1 and pid != record["owner_pid"]:
            info = (Path("/proc") / str(pid) / "stat").read_text()
            pid = int(info.rsplit(")", 1)[1].split()[1])
        if (
            pid != record["owner_pid"]
            or _process_start(pid) != record["owner_start"]
        ):
            raise ValueError("Validation reservation is not a live ancestor")
        return lease
    except (KeyError, OSError, TypeError) as error:
        raise ValueError("GUI validation reservation is invalid") from error


def _reserve_gui(arguments):
    if not arguments:
        raise ValueError("GUI launcher entry is required")
    entry = Path(arguments[0]).resolve()
    allowed = {
        ROOT / "tools/freecad_bridge/run-isolated",
        ROOT / "tools/freecad_bridge/launch-freecad",
    }
    if entry not in allowed:
        raise ValueError("Unsupported GUI launcher entry")
    _env_limits()
    if LEASE_ENV in os.environ:
        lease = _adopt_gui_lease()
        _residual(lease, GuardContext())
        os.environ[ENTRY_ENV] = str(entry)
        os.execv(str(entry), [str(entry), *arguments[1:]])
    with acquire_validation_lease(GuardContext().runtime_dir) as lease:
        _residual(lease, GuardContext())
        instances = _command(GuardContext(), [], [
            "flatpak", "ps", "--columns=application,pid",
        ])
        if instances.returncode or any(
            line.split()[0] == APP_ID
            for line in instances.stdout.splitlines() if line.split()
        ):
            raise GuardFailure("foreign-freecad-instance")
        inherited = fcntl.fcntl(lease.fd, fcntl.F_DUPFD, 10)
        os.set_inheritable(inherited, True)
        os.environ[LEASE_ENV] = str(inherited)
        os.environ[LEASE_ID_ENV] = lease.lease_id
        os.environ[ENTRY_ENV] = str(entry)
        os.execv(str(entry), [str(entry), *arguments[1:]])


def _request_gui_stop(arguments):
    if len(arguments) != 3:
        raise ValueError("GUI stop requires evidence, supervisor and client exit")
    output = Path(arguments[0])
    pid, client_exit = int(arguments[1]), int(arguments[2])
    context = GuardContext()
    lease = _adopt_gui_lease()
    ownership = json.loads((output / "ownership.json").read_text())
    record = lease.read()
    if (
        ownership.get("schema_version") != 1
        or ownership.get("supervisor_pid") != pid
        or ownership.get("lease_id") != lease.lease_id
        or not 0 <= client_exit <= 255
        or any(ownership.get(name) != record.get(name)
               for name in ("scope", "invocation", "cgroup"))
        or not ownership.get("scope")
        or _identity(context, [], ownership["scope"]) != ownership["invocation"]
    ):
        raise ValueError("GUI shutdown ownership is not proved")
    descriptor = os.pidfd_open(pid, 0)
    try:
        if _process_start(pid, context.proc_root) != ownership["supervisor_start"]:
            raise ValueError("GUI supervisor identity changed")
        request = {
            name: ownership[name] for name in (
                "schema_version", "supervisor_pid", "supervisor_start",
                "scope", "invocation", "lease_id",
            )
        }
        request.update(client_exit=client_exit, signal="SIGTERM", signal_sent=False)
        path = output / "shutdown-request.json"
        if path.exists():
            raise ValueError("GUI shutdown request already exists")
        _json_write(path, request)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        request["signal_sent"] = True
        _json_write(path, request)
    finally:
        os.close(descriptor)
    return 0


def _gui_completion(arguments):
    if len(arguments) != 2:
        raise ValueError("GUI completion requires receipt and client exit")
    path = Path(arguments[0])
    result = json.loads(path.read_text())
    command_status = int(arguments[1])
    request_path = path.with_name("shutdown-request.json")
    request = json.loads(request_path.read_text()) if request_path.exists() else {}
    requested = (
        request.get("schema_version") == 1
        and request.get("signal") == "SIGTERM"
        and request.get("signal_sent") is True
        and type(request.get("client_exit")) is int
        and request["client_exit"] == command_status
        and all(request.get(name) == result.get(name) and result.get(name)
                for name in ("scope", "invocation", "lease_id"))
    )
    accepted = result.get("cleanup_proved") is True and (
        result.get("status") == "completed" or (
            requested and result.get("failure_reason") == "interrupted"
        )
    )
    passed = accepted and command_status == 0
    reason = None if passed else result.get("failure_reason") or "client-failed"
    _json_write(path.with_name("gui-completion.json"), {
        "status": "completed" if passed else "failed",
        "client_exit": command_status,
        "supervisor_shutdown_requested": bool(requested),
        "guard_process_exit": result.get("process_exit"),
        "failure_reason": reason,
        "cleanup_proved": result.get("cleanup_proved"),
    })
    return 0 if passed else 1


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["watchdog"]:
        _watchdog(*arguments[1:])
        return 0
    if arguments[:1] == ["reserve-gui"]:
        _reserve_gui(arguments[1:])
        return 0
    if arguments[:1] == ["verify-gui-lease"]:
        _env_limits()
        _adopt_gui_lease(os.getppid())
        return 0
    if arguments[:1] == ["request-gui-stop"]:
        return _request_gui_stop(arguments[1:])
    if arguments[:1] == ["check-gui-cleanup"]:
        return _gui_completion(arguments[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-max-mib", type=int, required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--isolate-profile", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(arguments)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    lease = _adopt_gui_lease() if LEASE_ENV in os.environ else None
    pass_fds = (3,) if "--instance-id-fd=3" in command else ()
    result = run_guarded_flatpak(
        command, limits=ValidationLimits(args.memory_max_mib, args.timeout_seconds),
        evidence_dir=args.evidence_dir, lease=lease, pass_fds=pass_fds,
        isolate_profile=args.isolate_profile,
    )
    sys.stdout.buffer.write(Path(result["stdout_path"]).read_bytes())
    sys.stderr.buffer.write(Path(result["stderr_path"]).read_bytes())
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, GuardFailure) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error
