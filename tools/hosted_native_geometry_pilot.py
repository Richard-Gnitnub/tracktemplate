#!/usr/bin/env python3
"""Compose one manual hosted pilot; never replace workstation controls."""

import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402


EXPECTED_PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-"
    "py3.13.15-qt6.11.2-coin4.0.10"
)
APP_COMMIT = "e63d66825c4daf9adb09283488c2bc2ace92ed8b24bcf81666933226ed082fd4"
RUNTIME = "org.kde.Platform/x86_64/6.11"
RUNTIME_COMMIT = (
    "fe192771c0992ad873e6a9ccc6e4f087c76314ce5ced165650cc7ea045a6bbaa"
)
TEST_PATH = "tests/freecad_validate_phase6_transition_exact_geometry.py"
TEST_SHA256 = (
    "e9df630ef1a33a20b52b0bd961dd4255e9e23ad8344f8832718a095baee7cf51"
)
GUARD_SHA256 = (
    "b193209f0f21f28c3c17f9c52e509e31dccb32690152c02414769c0f6e49c559"
)
GEOMETRY_SENTINEL = (
    "Phase 6 transition transient exact geometry validation passed"
)
RUNTIME_SENTINEL = "TRACKTEMPLATE_HOSTED_RUNTIME="
REA_TEST_PATH = "tests/freecad_validate_rea_trackwork.py"
REA_TEST_SHA256 = (
    "ac316a5e49794361186f0f78e54db45839ca77f6d0b3905745b350c86c558e3d"
)
REA_SENTINEL = "TRACKTEMPLATE_REA_TRACKWORK="
REA_INPUT_PATHS = (
    "tests/fixtures/phase9b-rea-bc-source.json",
    "tests/validate_phase1_turnout.py",
    "reference/contracts/phase1-compatibility.json",
    "reference/contracts/phase1-transition-pilot.json",
    "TrackTemplate.FCMacro",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro",
)
OUTPUT = ROOT / "benchmark-output/hosted-native-geometry"
LIMITS = guard.ValidationLimits(memory_max_mib=4096, timeout_seconds=900)
SAMPLE_FIELDS = (
    "memory.current", "memory.peak", "memory.events", "memory.swap.current",
    "memory.pressure", "cpu.stat", "pids.current", "cgroup.events",
    "cgroup.procs",
)


def _workload(name):
    if name == "transition":
        return {
            "test_path": TEST_PATH, "test_sha256": TEST_SHA256,
            "selector": "hosted_transition_geometry_suite."
                        "TestTransitionGeometry.test_transition",
            "mode": None, "expected_native_tests": 1,
        }
    if name in ("rea-bc-readiness", "rea-bc-native"):
        mode = name.removeprefix("rea-bc-")
        return {
            "test_path": REA_TEST_PATH, "test_sha256": REA_TEST_SHA256,
            "selector": "freecad_validate_rea_trackwork", "mode": mode,
            "expected_native_tests": 1 if mode == "readiness" else 2,
        }
    raise ValueError("Unknown hosted workload")


def _native_command(workload="transition"):
    selected = _workload(workload)
    command = ["flatpak", "run", "--command=FreeCADCmd",
               "--env=OMP_NUM_THREADS=1", "--env=OPENBLAS_NUM_THREADS=1"]
    if selected["mode"]:
        command.append("--env=TRACKTEMPLATE_REA_MODE=" + selected["mode"])
    return command + [guard.APP_ID, "-P", str(ROOT / "tests"), "-t",
                      selected["selector"]]


def _unique_object(pairs):
    record = dict(pairs)
    if len(record) != len(pairs):
        raise ValueError("Duplicate report field")
    return record


def _rea_report(stdout, mode):
    lines = [line[len(REA_SENTINEL):] for line in stdout.splitlines()
             if line.startswith(REA_SENTINEL)]
    if len(lines) != 1:
        raise ValueError("Expected one REA trackwork report")
    report = json.loads(lines[0], object_pairs_hook=_unique_object)
    expected_keys = {
        "mode", "status", "tests", "failures", "errors", "skips",
        "documents_created", "documents_remaining", "input_sha256",
        "checks", "elapsed_seconds",
    }
    if not isinstance(report, dict) or report.keys() != expected_keys:
        raise ValueError("Unexpected REA report fields")
    native = mode == "native"
    expected = {
        "tests": 2 if native else 1, "failures": 0, "errors": 0, "skips": 0,
        "documents_created": 2 if native else 0, "documents_remaining": 0,
    }
    if (report["mode"] != mode or report["status"] != "PASS"
            or any(type(report[key]) is not int or report[key] != value
                   for key, value in expected.items())):
        raise ValueError("REA mode, counts or completion mismatch")
    elapsed = report["elapsed_seconds"]
    if (type(elapsed) not in (int, float)
            or not 0 <= elapsed <= LIMITS.timeout_seconds
            or not math.isfinite(elapsed)):
        raise ValueError("Invalid REA elapsed time")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in REA_INPUT_PATHS}
    if report["input_sha256"] != hashes:
        raise ValueError("REA source input identity mismatch")
    checks = report["checks"]
    expected_checks = {
        "source_scalars": 425, "timber_records": 165, "rail_anchors": 70,
        "scene_lines": 319, "canonical_reads": 13, "negative_controls": 7,
        "undo_redo": 2, "save_reopen": 2, "no_op": 1,
    }
    if (not isinstance(checks, dict)
            or checks.keys() != expected_checks.keys() | {"mapped_points"}):
        raise ValueError("Unexpected REA check counters")
    if (any(type(value) is not int or (value <= 0 if native else value != 0)
            for value in checks.values())
            or any(checks[key] != (count if native else 0)
                   for key, count in expected_checks.items())):
        raise ValueError("REA checks do not prove selected workload")
    return report


def _memory(text):
    values = {}
    for name in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
        matches = re.findall(rf"^{name}:\s+([0-9]+) kB$", text, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous host memory: " + name)
        values[name] = int(matches[0]) * 1024
    if not 0 < values["MemAvailable"] <= values["MemTotal"]:
        raise ValueError("Invalid available host memory")
    if values["SwapFree"] > values["SwapTotal"]:
        raise ValueError("Invalid host swap measurement")
    return values


def validate_admission(environ, meminfo_text):
    """Refuse other environments, reruns and insufficient fresh headroom."""
    expected = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "Richard-Gnitnub/tracktemplate",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_RUN_ATTEMPT": "1",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
    }
    for key, value in expected.items():
        if environ.get(key) != value:
            raise ValueError("Hosted pilot admission refused: " + key)
    values = _memory(meminfo_text)
    if values["MemAvailable"] < (4096 + 8192) * 1024**2:
        raise ValueError("Insufficient memory for ceiling and 8 GiB reserve")
    return values


def _failure(classification, detail):
    return {"status": "FAIL", "classification": classification,
            "detail": detail, "expected_native_tests": 1}


def _qualified_runtime(stdout):
    lines = [line[len(RUNTIME_SENTINEL):] for line in stdout.splitlines()
             if line.startswith(RUNTIME_SENTINEL)]
    if len(lines) != 1:
        raise ValueError("Expected one runtime report")
    runtime = json.loads(lines[0])["compatibility_evaluation"]
    if (runtime.get("status") != "qualified"
            or runtime.get("matched_profile_id") != EXPECTED_PROFILE
            or runtime.get("mismatches")):
        raise ValueError("Qualified runtime mismatch")


def assess_result(result, stdout, stderr, samples, clearance, *,
                  deadline_clearance=False, workload="transition"):
    """Require native assertions, contained execution and complete evidence."""
    selected = _workload(workload)
    expected_tests = selected["expected_native_tests"]

    def failed(classification, detail):
        failure = _failure(classification, detail)
        if selected["mode"]:
            failure.update(workload=workload,
                           expected_native_tests=expected_tests)
        return failure

    reason = result.get("failure_reason") or result.get(
        "execution_failure_reason"
    )
    if result.get("status") == "refused":
        return failed("SETUP_FAILURE", reason)
    if not result.get("cleanup_proved") or not clearance:
        return failed("CLEANUP_FAILURE", "Owned cleanup or clearance unproved")
    if reason and reason not in (
        "deadline-exceeded", "interrupted", "memory-limit", "payload-nonzero",
    ):
        return failed("SETUP_FAILURE", reason)
    if reason in ("deadline-exceeded", "interrupted"):
        return failed("TIMEOUT", reason)
    if reason == "memory-limit":
        return failed("MEMORY_LIMIT", reason)
    if result.get("process_exit") != 0 or reason == "payload-nonzero":
        try:
            _qualified_runtime(stdout)
        except (KeyError, TypeError, ValueError) as error:
            return failed("SETUP_FAILURE", str(error))
        return failed("GEOMETRY_FAILURE", reason or "Nonzero native exit")
    if result.get("status") != "completed" or reason:
        return failed("SETUP_FAILURE", reason or "Guard did not complete")
    cancellation = result.get("deadline_cancellation_exit")
    if cancellation != 0 and not (
        cancellation == 5 and deadline_clearance is True
    ):
        return failed("CLEANUP_FAILURE", "Deadline cancellation unproved")
    expected_kernel = {
        "memory.max": str(4096 * 1024**2),
        "memory.high": str(4096 * 1024**2), "memory.swap.max": "0",
        "cpu.max": "100000 100000", "pids.max": "128",
    }
    if (result.get("kernel_limits") != expected_kernel
            or result.get("limits") != vars(LIMITS)):
        return failed("SETUP_FAILURE", "Unexpected kernel limits")
    try:
        live = []
        removed = False
        final_accounting = False
        final_samples = [result[key] for key in ("before_cleanup", "after_cleanup")
                         if isinstance(result.get(key), dict)]
        for sample in [*samples, *final_samples]:
            # An empty scope can disappear after payload exit. Partial
            # telemetry is not evidence of removal and must fail closed.
            if all(sample.get(key) is None for key in SAMPLE_FIELDS):
                removed = True
                continue
            if removed or any(sample.get(key) is None for key in SAMPLE_FIELDS):
                raise ValueError("Incomplete live cgroup telemetry")
            numbers = {key: int(sample[key]) for key in (
                "memory.current", "memory.peak", "memory.swap.current",
                "pids.current",
            )}
            if any(value < 0 for value in numbers.values()):
                raise ValueError("Negative resource measurement")
            events = dict(line.split() for line in
                          sample["memory.events"].splitlines())
            if not {"high", "max", "oom", "oom_kill"} <= events.keys():
                raise ValueError("Incomplete memory events")
            if (any(int(events.get(key, 0)) for key in (
                    "high", "max", "oom", "oom_kill", "oom_group_kill"))
                    or numbers["memory.swap.current"]
                    or numbers["memory.peak"] > 4096 * 1024**2):
                return failed("MEMORY_LIMIT", "Memory event, swap or ceiling")
            if numbers["pids.current"] > 128:
                raise ValueError("Task ceiling exceeded")
            cpu = dict(line.split() for line in sample["cpu.stat"].splitlines())
            numbers["cpu_usage_usec"] = int(cpu["usage_usec"])
            live.append(numbers)
            if (any(sample is item for item in final_samples)
                    and numbers["pids.current"] == 0
                    and not sample["cgroup.procs"].strip()
                    and dict(line.split() for line in
                             sample["cgroup.events"].splitlines()).get(
                                 "populated"
                             ) == "0"):
                final_accounting = True
        if not live:
            raise ValueError("No complete owned cgroup sample")
        _qualified_runtime(stdout)
        combined = stdout + "\n" + stderr
        counts = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$",
                            combined, re.MULTILINE)
        if (len(counts) != 1 or counts[0][0] != str(expected_tests)
                or len(re.findall(r"^OK$", combined, re.MULTILINE)) != 1
                or re.search(r"skipped|FAILED|ERROR:", combined)):
            raise ValueError("Native test count, no-skips or sentinel unproved")
        rea = None
        if selected["mode"]:
            rea = _rea_report(stdout, selected["mode"])
        elif stdout.splitlines().count(GEOMETRY_SENTINEL) != 1:
            raise ValueError("Native geometry sentinel unproved")
        assessment = {
            "status": "PASS", "classification": "NATIVE_GEOMETRY_PASS",
            "expected_native_tests": expected_tests,
            "completed_native_tests": expected_tests,
            "skips": 0, "native_test_seconds": float(counts[0][1]),
            "peak_cgroup_memory_bytes": max(x["memory.peak"] for x in live),
            "peak_tasks_observed": max(x["pids.current"] for x in live),
            "cpu_usage_usec": max(x["cpu_usage_usec"] for x in live),
            "complete_resource_samples": len(live),
            "resource_accounting": (
                "final" if final_accounting else "sampled-lower-bound"
            ),
            "scope": "One unchanged transition validator; no chair or GUI proof",
        }
        if rea is not None:
            assessment.update(
                workload=workload,
                classification="REA_BC_" + selected["mode"].upper() + "_PASS",
                rea_trackwork=rea,
                scope=("REA B/C readiness only; no documents or geometry"
                       if selected["mode"] == "readiness" else
                       "REA B/C two native lifecycle tests; no GUI proof"),
            )
        return assessment
    except (KeyError, OSError, TypeError, ValueError) as error:
        return failed("EVIDENCE_INCOMPLETE", str(error))


def _write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _command(*args):
    return subprocess.run(args, cwd=ROOT, check=True, text=True,
                          capture_output=True, timeout=15).stdout.strip()


def _identity(workload="transition"):
    selected = _workload(workload)
    if os.getuid() == 0 or sys.flags.optimize:
        raise ValueError("Non-root execution with assertions is required")
    sha = _command("git", "rev-parse", "HEAD")
    if sha != os.environ.get("GITHUB_SHA"):
        raise ValueError("Checkout differs from dispatched commit")
    if _command("git", "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked checkout has changed")
    if not isinstance(selected["test_sha256"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", selected["test_sha256"],
    ):
        raise ValueError("Native entry identity is not frozen")
    hashes = {}
    paths = (selected["test_path"], "tools/freecad_validation_guard.py",
             "tests/hosted_transition_geometry_suite.py",
             "tools/hosted_native_geometry_pilot.py",
             ".github/workflows/native-geometry-pilot.yml",
             "reference/contracts/phase1-compatibility.json")
    if selected["mode"]:
        paths += REA_INPUT_PATHS
    for name in paths:
        hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if (hashes[selected["test_path"]] != selected["test_sha256"]
            or hashes["tools/freecad_validation_guard.py"] != GUARD_SHA256):
        raise ValueError("Frozen validator or guard identity changed")
    app = _command(
        "flatpak", "info", "--system", "--show-commit", guard.APP_ID,
    )
    runtime = _command(
        "flatpak", "info", "--system", "--show-runtime", guard.APP_ID,
    )
    runtime_commit = _command(
        "flatpak", "info", "--system", "--show-commit", RUNTIME,
    )
    if (app, runtime, runtime_commit) != (APP_COMMIT, RUNTIME, RUNTIME_COMMIT):
        raise ValueError("Deployed Flatpak build differs from qualified pins")
    _command("systemctl", "--user", "show-environment")
    return {
        "source_commit": sha, "files_sha256": hashes,
        "workload": workload, "native_entry": selected,
        "app_commit": app, "runtime": runtime,
        "runtime_commit": runtime_commit, "limits": vars(LIMITS),
        "runner": {key: os.environ.get(key) for key in (
            "ImageOS", "ImageVersion", "RUNNER_OS", "RUNNER_ARCH",
            "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
        )},
        "kernel": _command("uname", "-a"),
        "flatpak_version": _command("flatpak", "--version"),
        "systemd_version": _command("systemctl", "--version"),
        "guard_sha256": GUARD_SHA256,
    }


def _clearance():
    observations = []
    deadline = time.monotonic() + 10
    while True:
        listing = _command("flatpak", "ps", "--columns=application,pid")
        active = any(line.split()[0] == guard.APP_ID
                     for line in listing.splitlines() if line.split())
        observations.append({"monotonic_seconds": time.monotonic(),
                             "listing": listing})
        if not active or time.monotonic() >= deadline:
            _write(OUTPUT / "clearance.json", observations)
            return not active
        time.sleep(0.1)


def _deadline_clearance(result):
    """Read back the owned deadline units without changing guard evidence."""
    watchdog = result.get("watchdog")
    receipt = {"watchdog": watchdog, "proved": False, "observations": []}
    if (result.get("cleanup_proved") is not True
            or not isinstance(watchdog, str)
            or not re.fullmatch(r"tracktemplate-validation-[0-9a-f]{32}",
                                watchdog)):
        _write(OUTPUT / "deadline-clearance.json", receipt)
        return False
    proved = True
    for suffix in (".timer", ".service"):
        expected = {
            "Id": watchdog + suffix, "LoadState": "not-found",
            "ActiveState": "inactive", "SubState": "dead", "Job": "",
        }
        if suffix == ".service":
            expected.update(MainPID="0", ControlPID="0", ControlGroup="")
        command = ["systemctl", "--user", "show", "--all"]
        for field in expected:
            command.extend(["-p", field])
        command.append(watchdog + suffix)
        observation = {"command": command}
        receipt["observations"].append(observation)
        try:
            completed = subprocess.run(
                command, cwd=ROOT, check=False, text=True,
                capture_output=True, timeout=15,
            )
            observation.update(returncode=completed.returncode,
                               stdout=completed.stdout,
                               stderr=completed.stderr)
            pairs = [line.split("=", 1)
                     for line in completed.stdout.splitlines()]
            values = dict(pairs)
            if (completed.returncode != 0 or len(pairs) != len(expected)
                    or values.get("LoadState") not in ("loaded", "not-found")):
                proved = False
                continue
            expected["LoadState"] = values["LoadState"]
            if values != expected:
                proved = False
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            observation["error"] = repr(error)
            proved = False
    receipt["proved"] = proved
    _write(OUTPUT / "deadline-clearance.json", receipt)
    return proved


def main():
    """Run only on the explicit hosted workflow; retain every outcome."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if (OUTPUT / "summary.json").exists() or (OUTPUT / "guard").exists():
        raise ValueError("Evidence already exists; no automatic retry")
    summary = _failure("SETUP_FAILURE", "Preparation did not complete")
    workload = os.environ.get("TRACKTEMPLATE_HOSTED_WORKLOAD", "transition")
    started = time.monotonic()
    host_observations = []

    def observe_host():
        observation = {"monotonic_seconds": time.monotonic()}
        try:
            observation.update(_memory(Path("/proc/meminfo").read_text()))
            observation["memory_pressure"] = Path(
                "/proc/pressure/memory"
            ).read_text()
        except (OSError, ValueError) as error:
            observation["error"] = str(error)
        host_observations.append(observation)
        try:
            with (OUTPUT / "host.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(observation) + "\n")
        except OSError as error:
            observation["error"] = str(error)

    def observed_sleep(seconds):
        # Passive host observations only. The unchanged guard owns stops
        # and cleanup; this callback must not interrupt its finally block.
        observe_host()
        time.sleep(seconds)

    try:
        selected = _workload(workload)
        summary["expected_native_tests"] = selected["expected_native_tests"]
        identity = _identity(workload)
        identity["host_admission"] = validate_admission(
            os.environ, Path("/proc/meminfo").read_text(),
        )
        _write(OUTPUT / "identity.json", identity)
        observe_host()
        if "error" in host_observations[-1]:
            raise ValueError(host_observations[-1]["error"])
        guard_started = time.monotonic()
        children_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        result = guard.run_guarded_flatpak(
            _native_command(workload),
            limits=LIMITS, evidence_dir=OUTPUT / "guard",
            context=guard.GuardContext(sleep=observed_sleep),
            cwd=ROOT, isolate_profile=True,
        )
        children_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        guard_seconds = time.monotonic() - guard_started
        observe_host()
        samples_path = OUTPUT / "guard/measurements.jsonl"
        samples = (
            [json.loads(line) for line in samples_path.read_text().splitlines()]
            if samples_path.exists() else []
        )
        deadline_clearance = _deadline_clearance(result)
        clearance = _clearance()
        summary = assess_result(
            result, (OUTPUT / "guard/stdout").read_text(),
            (OUTPUT / "guard/stderr").read_text(), samples,
            clearance and deadline_clearance,
            deadline_clearance=deadline_clearance, workload=workload,
        )
        summary["deadline_cleanup_proved"] = deadline_clearance
        if any("error" in row for row in host_observations):
            summary = _failure(
                "EVIDENCE_INCOMPLETE", "Host telemetry unavailable",
            )
            summary["expected_native_tests"] = selected["expected_native_tests"]
            summary["host_telemetry_errors"] = [
                row["error"] for row in host_observations if "error" in row
            ]
        else:
            summary["minimum_host_available_bytes"] = min(
                row["MemAvailable"] for row in host_observations
            )
        summary["source_commit"] = identity["source_commit"]
        summary["guard_elapsed_seconds"] = guard_seconds
        summary["waited_children"] = {
            "user_cpu_seconds_delta": (
                children_after.ru_utime - children_before.ru_utime
            ),
            "system_cpu_seconds_delta": (
                children_after.ru_stime - children_before.ru_stime
            ),
            "cumulative_maximum_single_child_rss_bytes": (
                children_after.ru_maxrss * 1024
            ),
            "boundary": (
                "CPU deltas cover this coordinator's waited children, "
                "including guard control commands. Maximum RSS includes "
                "earlier metadata children; it is not aggregate RSS or "
                "proof of complete FreeCAD descendant consumption."
            ),
        }
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        summary["detail"] = repr(error)
    finally:
        summary["workload"] = workload
        summary["pilot_elapsed_seconds"] = time.monotonic() - started
        summary["local_pressure_guard_qualification"] = False
        _write(OUTPUT / "summary.json", summary)
        print("TRACKTEMPLATE_HOSTED_GEOMETRY=" + json.dumps(summary))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
