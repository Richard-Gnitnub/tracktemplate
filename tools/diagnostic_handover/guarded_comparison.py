"""Run one readiness sequence with unchanged qualified resource controls."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
APP_ID = "org.freecad.FreeCAD"
HANDOVER_TIMEOUT_SECONDS = 10.0
HANDOVER_POLL_SECONDS = 0.25


def read_flatpak_instances(timeout):
    """Read strict instance identities within the remaining handover time."""
    command = ["flatpak", "ps", "--columns=application,pid,instance"]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"Flatpak observation timed out: stdout={error.stdout!r}; "
            f"stderr={error.stderr!r}"
        ) from error
    if result.returncode:
        raise RuntimeError(
            f"Flatpak observation failed ({result.returncode}): "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )
    rows = []
    seen = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if (len(fields) != 3 or not fields[1].isascii()
                or not fields[1].isdigit() or int(fields[1]) <= 0
                or fields[2] in seen):
            raise RuntimeError(
                f"Malformed Flatpak observation: stdout={result.stdout!r}; "
                f"stderr={result.stderr!r}"
            )
        seen.add(fields[2])
        rows.append({"application": fields[0], "pid": int(fields[1]),
                     "instance": fields[2]})
    return rows


def observe_predecessor(pid, cgroup, *, proc_root=Path("/proc"),
                        cgroup_root=Path("/sys/fs/cgroup")):
    """Observe only; never kill a process or remove instance metadata."""
    try:
        (proc_root / str(pid)).stat()
        pid_exists = True
    except FileNotFoundError:
        pid_exists = False
    group = cgroup_root / cgroup.lstrip("/")
    try:
        group.stat()
        processes = (group / "cgroup.procs").read_text().strip()
        lines = (group / "cgroup.events").read_text().splitlines()
        events = dict(line.split() for line in lines)
        if len(events) != len(lines) or "populated" not in events:
            raise RuntimeError("Predecessor cgroup state is ambiguous")
        empty = not processes and events["populated"] == "0"
    except FileNotFoundError:
        # A disappearing file proves cleanup only if the group also went.
        try:
            group.stat()
        except FileNotFoundError:
            empty = True
        else:
            raise RuntimeError("Predecessor cgroup observation incomplete")
    return {"pid_exists": pid_exists, "cgroup_empty": empty}


def predecessor_identity(runtime, helpers):
    """Bind the handover to the completed stage's original guard receipt."""
    guard = runtime["guard_result"]
    if (runtime["status"] != "PASS" or runtime["process_exit"] != 0
            or guard["status"] != "completed"
            or guard["process_exit"] != 0
            or guard["process_exit_after_cleanup"] != 0
            or guard["cleanup_proved"] is not True
            or guard["failure_reason"] is not None):
        raise RuntimeError("Predecessor completion and cleanup are unproved")
    scope = guard["scope"]
    match = re.fullmatch(r"app-flatpak-org\.freecad\.FreeCAD-([1-9]\d*)\.scope",
                         scope)
    if not match:
        raise RuntimeError("Predecessor scope identity is invalid")
    uid = os.getuid()
    cgroup = (
        f"/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{scope}"
    )
    if guard["cgroup"] != cgroup:
        raise RuntimeError("Predecessor cgroup identity is invalid")
    ownership = helpers.read_json(
        Path(runtime["guard_path"]) / "ownership.json",
    )
    for key in ("scope", "cgroup", "invocation", "lease_id"):
        if not guard[key] or ownership[key] != guard[key]:
            raise RuntimeError("Predecessor ownership identity mismatch")
    return int(match[1]), cgroup


def wait_for_handover(runtime, helpers):
    """Wait for completed metadata to disappear, without another admission."""
    started = time.monotonic()
    deadline = started + HANDOVER_TIMEOUT_SECONDS
    record = {"status": "FAIL", "deadline_seconds": deadline,
              "timeout_seconds": HANDOVER_TIMEOUT_SECONDS, "samples": []}
    try:
        pid, cgroup = predecessor_identity(runtime, helpers)
        record.update(predecessor_pid=pid, predecessor_cgroup=cgroup)
        initial = runtime["final_host"]
        instance = None
        while True:
            if time.monotonic() >= deadline:
                raise RuntimeError("Flatpak handover deadline exceeded")
            sample = {"monotonic_seconds": time.monotonic()}
            record["samples"].append(sample)
            prior = observe_predecessor(pid, cgroup)
            sample["predecessor"] = prior
            if prior["pid_exists"] or prior["cgroup_empty"] is not True:
                raise RuntimeError("Predecessor identity or cleanup uncertain")
            host = helpers.host_sample()
            sample["host"] = host
            helpers.check_host(host, initial, 12288 * 2**20)
            if (host["available_bytes"] < (12288 + 8192) * 2**20
                    or host["some_avg10"] != 0 or host["full_avg10"] != 0):
                raise RuntimeError("Host headroom or pressure blocks handover")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Flatpak handover deadline exceeded")
            rows = read_flatpak_instances(remaining)
            sample["instances"] = rows
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Flatpak handover deadline exceeded")
            freecad = [row for row in rows if row["application"] == APP_ID]
            if not freecad:
                record["status"] = "PASS"
                return record
            if len(freecad) != 1 or freecad[0]["pid"] != pid:
                raise RuntimeError("Foreign FreeCAD instance blocks handover")
            current = freecad[0]["instance"]
            if instance is not None and current != instance:
                raise RuntimeError("Predecessor Flatpak identity changed")
            instance = current
            time.sleep(min(HANDOVER_POLL_SECONDS, remaining))
    except BaseException:
        record["exception"] = traceback.format_exc()
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        helpers.write_exclusive(OUTPUT / "handover-result.json", record)


def capture_guard_result(guard_parent, prior_results, record, helpers):
    """Find refusal receipts even when no payload ownership was created."""
    paths = set(guard_parent.glob("*/result.json")) - prior_results
    if len(paths) != 1:
        raise RuntimeError("Expected exactly one new guard result receipt")
    path = next(iter(paths))
    guard = helpers.read_json(path)
    if not isinstance(guard, dict) or guard.get("status") not in (
            "completed", "failed", "refused"):
        raise RuntimeError("Invalid guard result receipt")
    record.update(guard_path=str(path.parent), guard_result=guard,
                  failure_reason=guard.get("failure_reason"))
    return path.parent, guard


def load_helpers():
    path = ROOT / "tmp/issue213-xo-native-attempt-03/guarded_native.py"
    spec = importlib.util.spec_from_file_location("_comparison_host_helpers", path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    return helpers


def verify_files(manifest):
    for item in manifest["files"]:
        path = Path(item["path"])
        assert path.resolve() == path and path.is_relative_to(ROOT)
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def run_stage(name, command, cap_mib, guard_parent, helpers):
    """Observe host pressure; stop only the identified owned supervisor."""
    output = OUTPUT / name
    output.mkdir(mode=0o700)
    prior = set(guard_parent.glob("*/ownership.json"))
    prior_results = set(guard_parent.glob("*/result.json"))
    process = None
    ownership = None
    guard_path = None
    record = {"status": "FAIL", "command": command, "cap_mib": cap_mib}
    started = time.monotonic()
    try:
        with (output / "host.jsonl").open("x") as host_log, \
                (output / "stdout").open("xb") as stdout, \
                (output / "stderr").open("xb") as stderr:
            initial = helpers.host_sample()
            record["initial_host"] = initial
            assert initial["available_bytes"] >= (cap_mib + 8192) * 2**20
            assert initial["some_avg10"] == initial["full_avg10"] == 0
            # #219 limits payload swap to zero. Preserve the existing host
            # baseline separately; any increase or full stall stops this run.
            helpers.check_host(initial, initial, cap_mib * 2**20)
            host_log.write(json.dumps(initial) + "\n")
            host_log.flush()
            parent = os.getpid()
            process = subprocess.Popen(
                command, cwd=ROOT, stdout=stdout, stderr=stderr,
                preexec_fn=lambda: helpers.bind_parent(parent),
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )
            record["pid"] = process.pid
            record["process_start"] = helpers.process_start(process.pid)
            while process.poll() is None:
                paths = set(guard_parent.glob("*/ownership.json")) - prior
                assert len(paths) <= 1, "More than one new guard ownership"
                if paths:
                    guard_path = next(iter(paths)).parent
                    ownership = helpers.read_json(guard_path / "ownership.json")
                    supervisor = ownership["supervisor_pid"]
                    assert helpers.process_start(supervisor) == (
                        ownership["supervisor_start"])
                    if supervisor != process.pid:
                        status = Path(f"/proc/{supervisor}/status").read_text()
                        assert f"PPid:\t{process.pid}\n" in status
                sample = helpers.host_sample(
                    ownership["cgroup"] if ownership else None,
                )
                host_log.write(json.dumps(sample) + "\n")
                host_log.flush()
                os.fsync(host_log.fileno())
                helpers.check_host(sample, initial, cap_mib * 2**20)
                if time.monotonic() - started > 120:
                    raise RuntimeError("Readiness sequence stage exceeded 120s")
                time.sleep(0.25)
            record["process_exit"] = process.returncode
            final = helpers.host_sample()
            record["final_host"] = final
            host_log.write(json.dumps(final) + "\n")
            host_log.flush()
            os.fsync(host_log.fileno())
            helpers.check_host(final, initial, cap_mib * 2**20)
        guard_path, guard = capture_guard_result(
            guard_parent, prior_results, record, helpers,
        )
        paths = set(guard_parent.glob("*/ownership.json")) - prior
        if guard["status"] == "refused":
            if (paths or "process_exit" not in guard
                    or guard["process_exit"] is not None
                    or guard.get("process_exit_after_cleanup") is not None
                    or any(guard.get(key) is not None
                           for key in ("scope", "cgroup", "invocation"))
                    or guard.get("cleanup_proved") is not False
                    or not isinstance(guard.get("failure_reason"), str)
                    or not guard["failure_reason"]):
                raise RuntimeError("Refusal has conflicting launch evidence")
            record.update(status="REFUSED", pre_launch=True,
                          payload_started=False)
            raise RuntimeError("Guard refused: " + guard["failure_reason"])
        assert paths == {guard_path / "ownership.json"}
        assert process.returncode == 0
        assert guard["status"] == "completed" and guard["process_exit"] == 0
        assert guard["cleanup_proved"] and not guard["failure_reason"]
        assert guard["kernel_limits"]["memory.swap.max"] == "0"
        samples = [json.loads(line) for line in
                   (guard_path / "measurements.jsonl").read_text().splitlines()]
        active = []
        for sample in samples:
            helpers.check_memory_limits(sample)
            if all(isinstance(sample.get(key), str)
                   for key in helpers.TELEMETRY_FILES):
                active.append(helpers.validate_telemetry(sample))
        assert active, "No complete cgroup measurements"
        record["recorded_peak_bytes"] = max(x["memory.peak"] for x in active)
        record["peak_limit"] = "Sampled kernel peak; not a lifetime peak claim"
        record["status"] = "PASS"
    except BaseException:
        record["exception"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            try:
                if ownership:
                    helpers.stop_owned(ownership["supervisor_pid"],
                                       ownership["supervisor_start"])
                else:
                    helpers.stop_owned(process.pid, record["process_start"])
                process.wait(timeout=20)
            except BaseException:
                record["stop_exception"] = traceback.format_exc()
        if "guard_result" not in record:
            try:
                capture_guard_result(
                    guard_parent, prior_results, record, helpers,
                )
            except (OSError, ValueError, RuntimeError):
                record["receipt_discovery_exception"] = traceback.format_exc()
    record["elapsed_seconds"] = time.monotonic() - started
    helpers.write_exclusive(output / "stage-result.json", record)
    if record["status"] != "PASS":
        raise RuntimeError(name + " failed; stop without retry")
    return record


def main():
    helpers = load_helpers()
    manifest_path = OUTPUT / "manifest.json"
    manifest = helpers.read_json(manifest_path)
    helpers.write_exclusive(OUTPUT / "attempted.json", {
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "candidate": manifest["candidate"], "pid": os.getpid(),
    })
    result = {"status": "FAIL", "comparison_attempts": 0, "stages": []}
    try:
        verify_files(manifest)
        review = helpers.read_json(OUTPUT / "pre-execution-review.json")
        assert review["decision"] == "PASS"
        assert review["manifest_sha256"] == hashlib.sha256(
            manifest_path.read_bytes()).hexdigest()
        assert helpers.read_json(OUTPUT / "independent-recovery-review.json")[
            "result"] == "PASS"
        runtime = run_stage(
            "runtime-qualification",
            [sys.executable, "-B", "tools/development_toolchain_preflight.py",
             "--stage", "freecad"], 4096,
            ROOT / "benchmark-output/freecad-validation", helpers,
        )
        result["stages"].append(runtime)
        text = (OUTPUT / "runtime-qualification/stdout").read_text()
        prefix = "TRACKTEMPLATE_TOOLCHAIN_PREFLIGHT="
        lines = [line for line in text.splitlines() if line.startswith(prefix)]
        assert len(lines) == 1
        assert json.loads(lines[0][len(prefix):])["status"] == "passed"
        verify_files(manifest)
        result["handover"] = wait_for_handover(runtime, helpers)
        result["comparison_attempts"] = 1
        compared = run_stage(
            "comparison",
            [sys.executable, "-B", "tools/freecad_validation_guard.py",
             "--memory-max-mib", "12288", "--timeout-seconds", "90",
             "--evidence-dir", str(OUTPUT / "comparison-guard"),
             "--isolate-profile", "--", "flatpak", "run",
             "--command=FreeCADCmd", "org.freecad.FreeCAD",
             str(OUTPUT / "comparison_entry.py")],
            12288, OUTPUT, helpers,
        )
        result["stages"].append(compared)
        native = helpers.read_json(OUTPUT / "native-result.json")
        assert native["status"] == "PASS" and native["comparisons"] == 702
        assert native["tests"] == 5 and native["negative_cases"] == 106
        stdout = (OUTPUT / "comparison-guard/stdout").read_text()
        assert stdout.splitlines().count(manifest["sentinel"]) == 1
        result["measurements"] = helpers.verify_measurements(
            OUTPUT / "comparison-guard/measurements.jsonl",
            compared["guard_result"], native["completed_monotonic_seconds"],
            compared["final_host"],
        )
        verify_files(manifest)
        result.update(status="PASS", source_bindings_unchanged=True,
                      native_result=str(OUTPUT / "native-result.json"))
    except BaseException:
        result["exception"] = traceback.format_exc()
        traceback.print_exc()
    helpers.write_exclusive(OUTPUT / "result.json", result)
    print(json.dumps({"status": result["status"],
                      "comparison_attempts": result["comparison_attempts"]}),
          flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
