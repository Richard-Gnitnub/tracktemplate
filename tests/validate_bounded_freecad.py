#!/usr/bin/env python3
"""Exercise validation containment without launching FreeCAD or systemd."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from tools import freecad_validation_guard as guard
except ImportError:
    guard = None


class FakeProcess:
    """A sandbox launcher whose exit does not imply descendant cleanup."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.pid = kernel.pid
        self.returncode = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired("fake sandbox", timeout)
        return self.returncode

    def terminate(self):
        self.kernel.events.append("launcher-terminate")
        self.returncode = -15

    def kill(self):
        self.kernel.events.append("launcher-kill")
        self.returncode = -9


class FakeKernel:
    """Model external observations, including Flatpak's scope migration."""

    pid = 41001
    invocation = "1234567890abcdef1234567890abcdef"

    def __init__(self, root, *, fault=None, exit_code=0):
        self.root = root
        self.proc_root = root / "proc"
        self.cgroup_root = root / "cgroup"
        self.runtime_dir = root / "runtime"
        self.runtime_dir.mkdir(mode=0o700)
        self.fault = fault
        self.exit_code = exit_code
        self.clock = 0.0
        self.released = False
        self.release_time = None
        self.timer_seconds = None
        self.timer_armed = False
        self.timer_cancelled = False
        self.events = []
        self.calls = []
        self.process = None
        self.stdout = None
        self.scope = "app-flatpak-org.freecad.FreeCAD-41001.scope"
        self.relative_group = (
            "/user.slice/user-{}.slice/user@{}.service/app.slice/{}"
        ).format(os.getuid(), os.getuid(), self.scope)
        self.group = self.cgroup_root / self.relative_group.lstrip("/")
        self.group.mkdir(parents=True)
        self._group_files()

    def _write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(value), encoding="utf-8")

    def _group_files(self):
        values = {
            "cgroup.procs": "41001\n41002\n",
            "cgroup.events": "populated 1\nfrozen 0\n",
            "memory.max": "max", "memory.high": "max",
            "memory.swap.max": "max", "memory.current": "8388608",
            "memory.peak": "8388608", "memory.swap.current": "0",
            "memory.events": "high 0\nmax 0\noom 0\noom_kill 0\n",
            "memory.pressure": "some avg10=0.00 total=0\n",
            "cpu.max": "max 100000", "cpu.stat": "usage_usec 1000\n",
            "cpu.pressure": "some avg10=0.00 total=0\n",
            "pids.max": "max", "pids.current": "2",
        }
        for name, value in values.items():
            self._write(self.group / name, value)
        self._write(
            self.proc_root / "meminfo",
            "MemTotal: 33554432 kB\nMemAvailable: 25165824 kB\n"
            "SwapTotal: 2097152 kB\nSwapFree: 2097152 kB\n",
        )
        self._write(
            self.proc_root / "pressure/memory",
            "some avg10=0.00 total=0\nfull avg10=0.00 total=0\n",
        )

    def _output(self, value):
        try:
            self.stdout.write(value)
        except TypeError:
            self.stdout.write(value.encode())
        self.stdout.flush()

    def popen(self, argv, **kwargs):
        self.calls.append([str(value) for value in argv])
        self.events.append("spawn")
        self.process = FakeProcess(self)
        self.stdout = kwargs["stdout"]
        for pid in (41001, 41002):
            membership = self.relative_group
            if self.fault == "wrong-scope":
                membership = "/operator-owned.scope"
            self._write(
                self.proc_root / str(pid) / "cgroup",
                "0::" + membership + "\n",
            )
            state = "T (stopped)" if pid == 41002 else "S (sleeping)"
            if self.fault == "gate-not-stopped":
                state = "S (sleeping)"
            self._write(
                self.proc_root / str(pid) / "status",
                "Name:\tsh\nState:\t{}\nUid:\t{}\t{}\t{}\t{}\n"
                .format(state, *([os.getuid()] * 4)),
            )
            fields = [str(pid), "(sh)", "S"] + ["0"] * 19
            fields[21] = "123456"
            self._write(self.proc_root / str(pid) / "stat", " ".join(fields))
        if self.fault != "gate-marker-missing":
            self._output("TT_SCOPE_GATE_READY\n")
        if self.fault == "premature-release":
            self._output("TT_SCOPE_GATE_RELEASED\n")
        return self.process

    def _properties(self, argv):
        properties = []
        for index, value in enumerate(argv[:-1]):
            if value in ("-p", "--property"):
                properties.extend(argv[index + 1].split(","))
        invocation = self.invocation
        if self.fault == "changed-invocation" and self.released:
            invocation = "fedcba0987654321fedcba0987654321"
        values = {
            "InvocationID": invocation,
            "ControlGroup": self.relative_group,
            "ActiveState": "active" if self.timer_armed else "inactive",
            "NextElapseUSecMonotonic": "1min",
            "TimersMonotonic": "{{ OnActiveUSec={}s ; next_elapse=1min }}"
            .format(self.timer_seconds),
            "Result": "success",
        }
        if "--value" in argv:
            return "\n".join(values.get(name, "") for name in properties) + "\n"
        return "\n".join(
            "{}={}".format(name, values.get(name, "")) for name in properties
        ) + "\n"

    def run(self, argv, **kwargs):
        del kwargs
        argv = [str(value) for value in argv]
        self.calls.append(argv)
        code, output = 0, ""
        command = Path(argv[0]).name
        if command == "flatpak" and "ps" in argv:
            if self.fault == "foreign-instance":
                output = "org.freecad.FreeCAD\t9999\n"
        elif command == "systemctl" and "set-property" in argv:
            self.events.append("set-limits")
            if self.fault == "limit-command-failed":
                code = 1
            else:
                names = {
                    "MemoryMax": "memory.max",
                    "MemoryHigh": "memory.high",
                    "MemorySwapMax": "memory.swap.max",
                    "TasksMax": "pids.max",
                }
                for value in argv:
                    name, sep, content = value.partition("=")
                    if sep and name in names:
                        self._write(self.group / names[name], content)
                    elif sep and name == "CPUQuota":
                        quota = int(content.rstrip("%")) * 1000
                        self._write(self.group / "cpu.max", f"{quota} 100000")
                if self.fault == "effective-limit-mismatch":
                    self._write(self.group / "memory.max", "max")
        elif command == "systemd-run":
            self.events.append("arm-deadline")
            for value in argv:
                if value.startswith("--on-active="):
                    self.timer_seconds = int(value.split("=", 1)[1].rstrip("s"))
            self.timer_armed = self.fault != "inactive-deadline"
            if self.fault == "deadline-command-failed":
                code = 1
                self.timer_armed = False
        elif command == "systemctl" and "show" in argv:
            output = self._properties(argv)
        elif command == "systemctl" and "kill" in argv:
            if any("SIGCONT" in value for value in argv):
                self.events.append("payload-release")
                self.released = True
                self.release_time = self.clock
                self._output("TT_SCOPE_GATE_RELEASED\n")
                if self.fault == "memory-limit":
                    self._write(
                        self.group / "memory.events",
                        "high 1\nmax 1\noom 1\noom_kill 1\n",
                    )
            else:
                self.events.append("scope-kill")
                if self.fault == "cleanup-fails":
                    code = 1
                else:
                    self.finish(-9)
        elif command == "systemctl" and "stop" in argv:
            self.events.append("cancel-deadline")
            self.timer_cancelled = True
            self.timer_armed = False
        else:
            raise AssertionError("Unexpected host command: {!r}".format(argv))
        return subprocess.CompletedProcess(argv, code, output, "")

    def finish(self, exit_code):
        if self.process.returncode is None:
            self.process.returncode = exit_code
        self._write(self.group / "cgroup.events", "populated 0\nfrozen 0\n")
        self._write(self.group / "cgroup.procs", "")
        self.events.append("scope-empty")

    def monotonic(self):
        return self.clock

    def sleep(self, seconds):
        self.clock += seconds
        if not self.released or self.process.returncode is not None:
            return
        if self.fault == "interrupted-oom":
            self._write(
                self.group / "memory.events",
                "high 1\nmax 1\noom 1\noom_kill 1\n",
            )
            raise KeyboardInterrupt("interruption overlaps memory kill")
        if self.fault == "interrupted-deadline":
            self.clock = self.release_time + self.timer_seconds
            raise KeyboardInterrupt("interruption overlaps deadline")
        if self.fault == "interrupted":
            raise KeyboardInterrupt("injected supervisor interruption")
        if self.fault in ("exited-before-keyboard", "exited-before-signal"):
            self.process.returncode = 7
            self.events.append("payload-exited-before-interruption")
            if self.fault == "exited-before-keyboard":
                raise KeyboardInterrupt("payload exited; descendant survives")
            raise InterruptedError("payload exited; descendant survives")
        if self.fault in ("descendant-survives", "cleanup-fails",
                          "changed-invocation"):
            self.process.returncode = 0
        elif self.fault == "deadline":
            if self.clock - self.release_time >= self.timer_seconds:
                self.events.append("watchdog-fired")
                self.finish(-9)
        elif self.fault == "memory-limit":
            self.finish(-9)
        else:
            self._output("PAYLOAD_SENTINEL\n")
            self.finish(self.exit_code)

    def context(self):
        return guard.GuardContext(
            run=self.run, popen=self.popen,
            proc_root=self.proc_root, cgroup_root=self.cgroup_root,
            runtime_dir=self.runtime_dir,
            monotonic=self.monotonic, sleep=self.sleep,
        )


class BoundedValidationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            guard, "Shared resource-bounded FreeCAD launcher is absent",
        )
        temporary = tempfile.TemporaryDirectory(prefix="tt-guard-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def invoke(self, kernel, *, evidence_name="evidence", argv=None,
               lease=None):
        if argv is None:
            argv = ["flatpak", "run", "--command=FreeCADCmd",
                    "org.freecad.FreeCAD", "proof.py"]
        result = guard.run_guarded_flatpak(
            argv,
            limits=guard.ValidationLimits(memory_max_mib=256, timeout_seconds=3),
            evidence_dir=self.root / evidence_name,
            context=kernel.context(),
            lease=lease,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["schema_version"], 1)
        self.assertTrue(Path(result["receipt_path"]).is_file())
        receipt = json.loads(Path(result["receipt_path"]).read_text())
        for key in ("status", "process_exit", "cleanup_proved",
                    "failure_reason"):
            self.assertEqual(receipt[key], result[key])
        return result

    def test_explicit_valid_limits(self):
        limits = guard.ValidationLimits(memory_max_mib=256, timeout_seconds=3)
        self.assertEqual(limits.memory_max_mib, 256)
        self.assertEqual(limits.timeout_seconds, 3)
        self.assertEqual(limits.cpu_percent, 100)
        self.assertEqual(limits.tasks_max, 128)

    def test_malformed_limits_rejected_before_execution(self):
        for name in ("memory_max_mib", "timeout_seconds", "cpu_percent",
                     "tasks_max"):
            for value in (True, False, 0, -1, 1.5, "4", None):
                with self.subTest(name=name, value=value):
                    values = {"memory_max_mib": 256, "timeout_seconds": 3}
                    values[name] = value
                    with self.assertRaises((TypeError, ValueError)):
                        guard.ValidationLimits(**values)

    def test_shared_lease_excludes_second_worktree(self):
        runtime = self.root / "shared-runtime"
        runtime.mkdir(mode=0o700)
        first_worktree = self.root / "one"
        second_worktree = self.root / "two"
        first_worktree.mkdir()
        second_worktree.mkdir()
        previous = Path.cwd()
        try:
            os.chdir(first_worktree)
            with guard.acquire_validation_lease(runtime):
                os.chdir(second_worktree)
                with self.assertRaises((ValueError, RuntimeError, OSError)):
                    with guard.acquire_validation_lease(runtime):
                        self.fail("Second worktree acquired the active lease")
            with guard.acquire_validation_lease(runtime):
                pass
        finally:
            os.chdir(previous)

    def test_foreign_freecad_is_preserved(self):
        kernel = FakeKernel(self.root, fault="foreign-instance")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["failure_reason"], "foreign-freecad-instance")
        self.assertNotIn("spawn", kernel.events)
        self.assertNotIn("scope-kill", kernel.events)

    def test_host_headroom_must_be_known_and_exceed_requested_cap(self):
        cases = (
            "MemTotal: 32724360 kB\nMemAvailable: 262144 kB\n",
            "MemTotal: 32724360 kB\nMemAvailable: 131072 kB\n",
            "MemTotal: 131072 kB\nMemAvailable: 524288 kB\n",
            "MemTotal: 32724360 kB\n",
            "MemTotal: 32724360 kB\nMemAvailable: unknown kB\n",
            "MemTotal: 32724360 kB\nMemAvailable: -1 kB\n",
            "MemTotal: 32724360 kB\nMemAvailable: 0 kB\n",
        )
        for index, meminfo in enumerate(cases):
            with self.subTest(meminfo=meminfo):
                case_root = self.root / str(index)
                case_root.mkdir()
                kernel = FakeKernel(case_root)
                kernel._write(kernel.proc_root / "meminfo", meminfo)
                result = self.invoke(kernel, evidence_name=f"headroom-{index}")
                self.assertNotEqual(result["status"], "completed")
                self.assertEqual(result["failure_reason"], "containment-unproved")
                self.assertNotIn("spawn", kernel.events)

    def test_existing_same_runtime_lease_can_be_adopted(self):
        kernel = FakeKernel(self.root)
        with guard.acquire_validation_lease(kernel.runtime_dir) as lease:
            result = self.invoke(kernel, lease=lease)
        self.assertEqual(result["status"], "completed")
        self.assertIs(result["cleanup_proved"], True)

    def test_unverified_lease_cannot_bypass_admission(self):
        kernel = FakeKernel(self.root)
        with self.assertRaises(ValueError):
            self.invoke(kernel, lease=object())
        self.assertNotIn("spawn", kernel.events)

    def test_other_runtime_lease_cannot_bypass_global_lock(self):
        kernel = FakeKernel(self.root)
        unrelated_runtime = self.root / "unrelated-runtime"
        unrelated_runtime.mkdir(mode=0o700)
        with guard.acquire_validation_lease(unrelated_runtime) as lease:
            with self.assertRaises(ValueError):
                self.invoke(kernel, lease=lease)
        self.assertNotIn("spawn", kernel.events)

    def test_guard_refusals_never_release_payload(self):
        cases = {
            "wrong-scope": "scope-gate-unproved",
            "gate-not-stopped": "scope-gate-unproved",
            "gate-marker-missing": "scope-gate-unproved",
            "premature-release": "scope-gate-unproved",
            "limit-command-failed": "containment-unproved",
            "effective-limit-mismatch": "containment-unproved",
            "deadline-command-failed": "deadline-unarmed",
            "inactive-deadline": "deadline-unarmed",
        }
        for index, (fault, expected) in enumerate(cases.items()):
            with self.subTest(fault=fault):
                case_root = self.root / str(index)
                case_root.mkdir()
                kernel = FakeKernel(case_root, fault=fault)
                result = self.invoke(kernel, evidence_name="proof-" + fault)
                self.assertNotEqual(result["status"], "completed")
                self.assertEqual(result["failure_reason"], expected)
                self.assertNotIn("payload-release", kernel.events)

    def test_normal_completion_preserves_payload_and_proves_cleanup(self):
        kernel = FakeKernel(self.root)
        argv = ["flatpak", "run", "--command=FreeCADCmd",
                "org.freecad.FreeCAD", "proof with spaces.py", "--pass",
                "--require-qualified"]
        result = self.invoke(kernel, argv=argv)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["process_exit"], 0)
        self.assertIsNone(result["failure_reason"])
        self.assertIs(result["cleanup_proved"], True)
        spawned = next(call for call in kernel.calls if "TT_SCOPE_GATE" in
                       " ".join(call))
        self.assertEqual(spawned[-3:], argv[-3:])
        self.assertLess(kernel.events.index("set-limits"),
                        kernel.events.index("payload-release"))
        self.assertLess(kernel.events.index("arm-deadline"),
                        kernel.events.index("payload-release"))
        self.assertLess(kernel.events.index("scope-empty"),
                        kernel.events.index("cancel-deadline"))

    def test_payload_failure_is_not_successful_validation(self):
        result = self.invoke(FakeKernel(self.root, exit_code=7))
        self.assertEqual(result["process_exit"], 7)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "payload-nonzero")
        self.assertIs(result["cleanup_proved"], True)

    def test_deadline_is_not_a_payload_pass(self):
        kernel = FakeKernel(self.root, fault="deadline")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "deadline-exceeded")
        self.assertNotEqual(result["process_exit"], 0)
        self.assertIs(result["cleanup_proved"], True)

    def test_memory_limit_is_not_a_payload_pass(self):
        kernel = FakeKernel(self.root, fault="memory-limit")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "memory-limit")
        self.assertIs(result["cleanup_proved"], True)

    def test_launcher_exit_does_not_hide_live_descendant(self):
        kernel = FakeKernel(self.root, fault="descendant-survives")
        result = self.invoke(kernel)
        self.assertIn("scope-kill", kernel.events)
        self.assertIs(result["cleanup_proved"], True)
        self.assertLess(kernel.events.index("scope-empty"),
                        kernel.events.index("cancel-deadline"))

    def test_unknown_cleanup_keeps_deadline_and_blocks_next_launch(self):
        kernel = FakeKernel(self.root, fault="cleanup-fails")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "cleanup-unproved")
        self.assertIs(result["cleanup_proved"], False)
        self.assertFalse(kernel.timer_cancelled)
        spawn_count = kernel.events.count("spawn")
        second = self.invoke(kernel, evidence_name="second")
        self.assertEqual(second["status"], "refused")
        self.assertEqual(second["failure_reason"], "residual-scope")
        self.assertEqual(kernel.events.count("spawn"), spawn_count)

    def test_changed_scope_identity_is_not_killed(self):
        kernel = FakeKernel(self.root, fault="changed-invocation")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertIs(result["cleanup_proved"], False)
        self.assertNotIn("scope-kill", kernel.events)
        self.assertFalse(kernel.timer_cancelled)

    def test_interruption_cleans_scope_and_restores_signal_handlers(self):
        kernel = FakeKernel(self.root, fault="interrupted")
        handlers = {sig: signal.getsignal(sig)
                    for sig in (signal.SIGINT, signal.SIGTERM)}
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "interrupted")
        self.assertIs(result["cleanup_proved"], True)
        self.assertIn("scope-kill", kernel.events)
        self.assertEqual(
            {sig: signal.getsignal(sig) for sig in handlers}, handlers,
        )

    def test_interruption_cannot_hide_memory_limit(self):
        kernel = FakeKernel(self.root, fault="interrupted-oom")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "memory-limit")
        self.assertIs(result["cleanup_proved"], True)

    def test_interruption_cannot_hide_expired_deadline(self):
        kernel = FakeKernel(self.root, fault="interrupted-deadline")
        result = self.invoke(kernel)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "deadline-exceeded")
        self.assertIs(result["cleanup_proved"], True)

    def complete_requested_stop(self, result):
        receipt = Path(result["receipt_path"])
        request = {
            "schema_version": 1, "client_exit": 0,
            "signal": "SIGTERM", "signal_sent": True,
            **{key: result[key] for key in ("scope", "invocation", "lease_id")},
        }
        receipt.with_name("shutdown-request.json").write_text(
            json.dumps(request), encoding="utf-8",
        )
        outcome = guard.main(["check-gui-cleanup", str(receipt), "0"])
        completion = json.loads(receipt.with_name("gui-completion.json")
                                .read_text())
        return outcome, completion

    def test_requested_stop_cannot_hide_prior_payload_failure(self):
        for index, fault in enumerate((
            "exited-before-keyboard", "exited-before-signal",
        )):
            with self.subTest(fault=fault):
                case_root = self.root / str(index)
                case_root.mkdir()
                kernel = FakeKernel(case_root, fault=fault)
                result = self.invoke(kernel, evidence_name=f"race-{index}")
                outcome, completion = self.complete_requested_stop(result)
                self.assertEqual(result["process_exit"], 7)
                self.assertIn("scope-kill", kernel.events)
                self.assertIs(result["cleanup_proved"], True)
                self.assertNotEqual(outcome, 0, completion)
                self.assertEqual(result["failure_reason"], "payload-nonzero")
                self.assertEqual(completion["status"], "failed")
                self.assertEqual(completion["guard_process_exit"], 7)
                self.assertEqual(completion["failure_reason"], "payload-nonzero")

    def test_requested_stop_accepts_guard_kill_of_running_payload(self):
        kernel = FakeKernel(self.root, fault="interrupted")
        result = self.invoke(kernel)
        outcome, completion = self.complete_requested_stop(result)
        self.assertNotIn("payload-exited-before-interruption", kernel.events)
        self.assertIn("scope-kill", kernel.events)
        self.assertEqual(result["process_exit"], -9)
        self.assertEqual(result["failure_reason"], "interrupted")
        self.assertIs(result["cleanup_proved"], True)
        self.assertEqual(outcome, 0, completion)
        self.assertEqual(completion["status"], "completed")
        self.assertEqual(completion["guard_process_exit"], -9)
        self.assertEqual(completion["client_exit"], 0)

    def test_untrusted_launch_command_rejected_without_spawn(self):
        for index, argv in enumerate((
            ["sudo", "flatpak", "run", "org.freecad.FreeCAD"],
            ["flatpak", "run", "org.other.Application"],
            ["flatpak", "run", "--command=sh", "org.freecad.FreeCAD"],
            ["flatpak", "run", "--command=python", "org.freecad.FreeCAD"],
        )):
            with self.subTest(argv=argv):
                case_root = self.root / str(index)
                case_root.mkdir()
                kernel = FakeKernel(case_root)
                with self.assertRaises((TypeError, ValueError)):
                    self.invoke(kernel, argv=argv, evidence_name=f"invalid-{index}")
                self.assertNotIn("spawn", kernel.events)


class GuiLeaseTests(unittest.TestCase):
    """Verify inherited GUI admission without running a GUI or a host tool."""

    def setUp(self):
        self.assertIsNotNone(guard)
        temporary = tempfile.TemporaryDirectory(prefix="tt-gui-lease-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.context = guard.GuardContext(runtime_dir=self.runtime)

    def verify(self, lease, *, replacements=None, owner_pid=None):
        inherited = fcntl.fcntl(lease.fd, fcntl.F_DUPFD, 10)
        try:
            environment = {
                "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB": "256",
                "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS": "3",
                "TRACKTEMPLATE_VALIDATION_LEASE_FD": str(inherited),
                "TRACKTEMPLATE_VALIDATION_LEASE_ID": lease.lease_id,
            }
            environment.update(replacements or {})
            with mock.patch.dict(os.environ, environment), mock.patch.object(
                guard, "GuardContext", return_value=self.context,
            ), mock.patch.object(
                guard.os, "getppid", return_value=owner_pid or os.getpid(),
            ):
                return guard.main(["verify-gui-lease"])
        finally:
            os.close(inherited)

    def test_live_inherited_lease_is_accepted(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            self.assertEqual(self.verify(lease), 0)

    def test_forged_descriptor_or_lease_identity_is_rejected(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            for replacements in (
                {"TRACKTEMPLATE_VALIDATION_LEASE_FD": "3"},
                {"TRACKTEMPLATE_VALIDATION_LEASE_FD": "2147483647"},
                {"TRACKTEMPLATE_VALIDATION_LEASE_ID": "wrong-lease"},
            ):
                with self.subTest(replacements=replacements):
                    with self.assertRaises(ValueError):
                        self.verify(lease, replacements=replacements)

    def test_descriptor_for_another_inode_is_rejected(self):
        other = self.root / "other-owned-file"
        other_fd = os.open(other, os.O_RDWR | os.O_CREAT, 0o600)
        wrong_fd = fcntl.fcntl(other_fd, fcntl.F_DUPFD, 10)
        try:
            with guard.acquire_validation_lease(self.runtime) as lease:
                with self.assertRaises(ValueError):
                    self.verify(lease, replacements={
                        "TRACKTEMPLATE_VALIDATION_LEASE_FD": str(wrong_fd),
                    })
        finally:
            os.close(wrong_fd)
            os.close(other_fd)

    def test_reused_pid_start_time_is_rejected(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            record = lease.read()
            record["owner_start"] = "0"
            lease.write(record)
            with self.assertRaises(ValueError):
                self.verify(lease)

    def test_unrelated_owner_is_rejected(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            record = lease.read()
            record["owner_pid"] = 2147483647
            lease.write(record)
            with self.assertRaises(ValueError):
                self.verify(lease)

    def test_missing_limits_are_rejected_before_gui_admission(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            with self.assertRaises(ValueError):
                self.verify(lease, replacements={
                    "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB": "",
                })

    def test_both_gui_entries_refuse_before_shared_file_mutation(self):
        project = self.root / "copied-project"
        bridge = project / "tools/freecad_bridge"
        bridge.mkdir(parents=True)
        binary = project / "private-bin"
        binary.mkdir()
        blocked = binary / "flatpak"
        blocked.write_text("#!/bin/sh\nexit 99\n")
        blocked.chmod(0o700)
        python = project / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        (project / "tools/freecad_validation_guard.py").write_text(
            "import sys\nsys.exit(23)\n",
        )
        admission = "tools/validation_execution_policy.py"
        (project / admission).write_bytes((ROOT / admission).read_bytes())
        (bridge / "freecad-cli").write_text("#!/bin/sh\nexit 1\n")
        (bridge / "freecad-cli").chmod(0o700)
        (project / ".devtools/freecad-cli/addon/FreecadCli").mkdir(parents=True)
        state = project / "benchmark-output/freecad-bridge"
        (state / "profile").mkdir(parents=True)
        for name in ("profile/user.cfg", "profile/system.cfg", "rpc-token",
                     "isolated-launcher.log", "isolated-instance-id",
                     "instance-id"):
            (state / name).write_text("operator-owned fixture: " + name)

        def snapshot():
            return {
                str(path.relative_to(state)): (
                    path.is_dir(), path.stat().st_mode & 0o777,
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    if path.is_file() else None,
                )
                for path in state.rglob("*")
            }

        before = snapshot()
        for name in ("run-isolated", "launch-freecad"):
            source = (ROOT / "tools/freecad_bridge" / name).read_text()
            self.assertIn("PATH=/bin:/usr/bin\n", source)
            # Replace only external-tool resolution in this disposable copy;
            # a regression must never launch an installed Flatpak from CI.
            copied = source.replace(
                "PATH=/bin:/usr/bin\n", f"PATH={binary}:/bin:/usr/bin\n", 1,
            )
            script = bridge / name
            script.write_text(copied)
            script.chmod(0o700)
            for reserved in ("", str(script)):
                with self.subTest(entry=name, reserved=bool(reserved)):
                    environment = dict(os.environ)
                    environment.update(
                        TRACKTEMPLATE_VALIDATION_RESERVED_ENTRY=reserved,
                        TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB="256",
                        TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS="3",
                        TRACKTEMPLATE_LOCAL_VALIDATION_EXCEPTION=(
                            "fixture-only-mocked-guard-refusal"
                        ),
                    )
                    completed = subprocess.run(
                        [str(script), "/bin/true"], env=environment,
                        capture_output=True, text=True, timeout=5,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 23, completed.stderr)
                    self.assertEqual(snapshot(), before)


class GuiShutdownTests(unittest.TestCase):
    """Require a matching, sent shutdown request for interrupted GUI cleanup."""

    def setUp(self):
        self.assertIsNotNone(guard)
        temporary = tempfile.TemporaryDirectory(prefix="tt-gui-stop-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.scope = "app-flatpak-org.freecad.FreeCAD-41001.scope"
        self.invocation = "1234567890abcdef1234567890abcdef"
        self.lease_id = "aabbccddeeff00112233445566778899"
        self.receipt = self.root / "result.json"
        self.result = {
            "schema_version": 1, "status": "failed", "process_exit": -9,
            "cleanup_proved": True, "failure_reason": "interrupted",
            "scope": self.scope, "invocation": self.invocation,
            "lease_id": self.lease_id,
        }
        self.request = {
            "schema_version": 1, "supervisor_pid": os.getpid(),
            "supervisor_start": Path(f"/proc/{os.getpid()}/stat")
            .read_text().rsplit(")", 1)[1].split()[19],
            "scope": self.scope, "invocation": self.invocation,
            "lease_id": self.lease_id, "client_exit": 0,
            "signal": "SIGTERM", "signal_sent": True,
        }

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def completion(self, *, request=True, client_exit=0):
        self.write("result.json", self.result)
        if request:
            self.write("shutdown-request.json", self.request)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/freecad_validation_guard.py"),
             "check-gui-cleanup", str(self.receipt), str(client_exit)],
            capture_output=True, text=True, timeout=5, check=False,
        )
        output = self.root / "gui-completion.json"
        self.assertTrue(output.is_file(), completed.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report["client_exit"], client_exit)
        self.assertEqual(report["guard_process_exit"], self.result["process_exit"])
        self.assertEqual(report["cleanup_proved"], self.result["cleanup_proved"])
        return completed, report

    def test_boolean_claim_cannot_authorise_interruption(self):
        self.write("result.json", self.result)
        try:
            outcome = guard.main([
                "check-gui-cleanup", str(self.receipt), "0", "1",
            ])
        except (ValueError, guard.GuardFailure):
            outcome = 2
        self.assertNotEqual(outcome, 0)

    def test_interrupted_cleanup_needs_matching_sent_request(self):
        completed, report = self.completion(request=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["status"], "failed")
        self.assertIs(report["supervisor_shutdown_requested"], False)

    def test_valid_owned_shutdown_preserves_both_exit_channels(self):
        completed, report = self.completion()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(report["status"], "completed")
        self.assertIs(report["supervisor_shutdown_requested"], True)
        self.assertEqual(report["guard_process_exit"], -9)

    def test_wrong_request_identity_or_unsent_signal_is_rejected(self):
        cases = (
            ("scope", "unowned.scope"),
            ("invocation", "different"),
            ("lease_id", "different"),
            ("signal", "SIGKILL"),
            ("signal_sent", False),
            ("client_exit", 7),
        )
        original = dict(self.request)
        for name, value in cases:
            with self.subTest(name=name):
                self.request = dict(original, **{name: value})
                completed, report = self.completion()
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["status"], "failed")

    def test_resource_failure_cannot_be_relabelled_as_requested_stop(self):
        for reason in ("memory-limit", "deadline-exceeded", "payload-nonzero",
                       "cleanup-unproved"):
            with self.subTest(reason=reason):
                self.result["failure_reason"] = reason
                completed, report = self.completion()
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["failure_reason"], reason)

    def test_successful_cleanup_does_not_hide_client_failure(self):
        self.request["client_exit"] = 7
        completed, report = self.completion(client_exit=7)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["client_exit"], 7)

    def test_normal_exit_needs_no_shutdown_request(self):
        self.result.update(status="completed", process_exit=0,
                           failure_reason=None)
        completed, report = self.completion(request=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(report["status"], "completed")
        self.assertIs(report["supervisor_shutdown_requested"], False)

    def stop_request(self, lease, *, ownership=None, signal_error=False):
        record = lease.read()
        record.update(scope=self.scope, invocation=self.invocation,
                      cgroup="/user.slice/owned.scope")
        lease.write(record)
        owner = dict(self.request)
        owner.pop("client_exit")
        owner.pop("signal")
        owner.pop("signal_sent")
        owner.update(lease_id=lease.lease_id,
                     cgroup="/user.slice/owned.scope")
        owner.update(ownership or {})
        self.write("ownership.json", owner)
        inherited = fcntl.fcntl(lease.fd, fcntl.F_DUPFD, 10)
        descriptors = []

        def pidfd_open(pid, flags=0):
            self.assertEqual(pid, os.getpid())
            self.assertEqual(flags, 0)
            descriptor = os.open(os.devnull, os.O_RDONLY)
            descriptors.append(descriptor)
            return descriptor

        def run(argv, **kwargs):
            del kwargs
            self.assertEqual(Path(argv[0]).name, "systemctl")
            self.assertIn("show", argv)
            self.assertIn(self.scope, argv)
            return subprocess.CompletedProcess(
                argv, 0, self.invocation + "\n", "",
            )

        context = guard.GuardContext(runtime_dir=self.runtime, run=run)
        environment = {
            "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB": "256",
            "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS": "3",
            "TRACKTEMPLATE_VALIDATION_LEASE_FD": str(inherited),
            "TRACKTEMPLATE_VALIDATION_LEASE_ID": lease.lease_id,
        }
        try:
            with mock.patch.dict(os.environ, environment), mock.patch.object(
                guard, "GuardContext", return_value=context,
            ), mock.patch.object(
                guard.os, "pidfd_open", side_effect=pidfd_open,
            ), mock.patch.object(
                guard.signal, "pidfd_send_signal",
                side_effect=PermissionError("injected send failure")
                if signal_error else None,
            ) as send:
                try:
                    outcome = guard.main([
                        "request-gui-stop", str(self.root), str(os.getpid()),
                        "0",
                    ])
                except (ValueError, OSError, guard.GuardFailure):
                    outcome = 2
                calls = list(send.call_args_list)
        finally:
            os.close(inherited)
            for descriptor in descriptors:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        return outcome, calls

    def test_stop_request_uses_verified_pidfd_and_preserves_sent_state(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            outcome, calls = self.stop_request(lease)
        self.assertEqual(outcome, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[1], signal.SIGTERM)
        request = json.loads((self.root / "shutdown-request.json").read_text())
        self.assertIs(request["signal_sent"], True)
        self.assertEqual(request["scope"], self.scope)
        self.assertEqual(request["invocation"], self.invocation)

    def test_wrong_supervisor_start_never_sends_signal(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            outcome, calls = self.stop_request(
                lease, ownership={"supervisor_start": "0"},
            )
        self.assertNotEqual(outcome, 0)
        self.assertEqual(calls, [])

    def test_unsent_shutdown_is_not_written_as_sent(self):
        with guard.acquire_validation_lease(self.runtime) as lease:
            outcome, _calls = self.stop_request(lease, signal_error=True)
        self.assertNotEqual(outcome, 0)
        request = json.loads((self.root / "shutdown-request.json").read_text())
        self.assertIs(request["signal_sent"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
