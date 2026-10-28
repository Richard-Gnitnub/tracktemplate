"""Standalone coordinator regressions; host/native boundaries are mocked."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ENTRY = Path(__file__).with_name("guarded_comparison.py")
SPEC = importlib.util.spec_from_file_location("handover_candidate", ENTRY)
coordinator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coordinator)
APP = "org.freecad.FreeCAD"
PID = 410952
INSTANCE = "23817291"
UID = os.getuid()
SCOPE = f"app-flatpak-{APP}-{PID}.scope"
CGROUP = (
    f"/user.slice/user-{UID}.slice/user@{UID}.service/app.slice/{SCOPE}"
)


class Clock:
    """Advance deterministic monotonic time without sleeping."""

    def __init__(self):
        self.value = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        if seconds <= 0:
            raise AssertionError("Polling must advance time")
        self.sleeps.append(seconds)
        self.value += seconds


def host_sample():
    """A qualified idle fixture, not a measurement of the workstation."""
    return {
        "available_bytes": 30 * 2**30,
        "total_bytes": 32 * 2**30,
        "swap_used_bytes": 12288,
        "some_avg10": 0.0,
        "full_avg10": 0.0,
        "some_total_us": 100,
        "full_total_us": 50,
        "foreign_freecad": [],
        "freecad_processes": [],
    }


class Helpers:
    """Fixture-only filesystem and host boundary for the coordinator."""

    TELEMETRY_FILES = ("memory.peak",)

    def __init__(self):
        self.stops = []
        self.checks = []

    @staticmethod
    def read_json(path):
        return json.loads(Path(path).read_text())

    @staticmethod
    def write_exclusive(path, value):
        with Path(path).open("x") as stream:
            json.dump(value, stream)

    @staticmethod
    def host_sample(*unused):
        return host_sample()

    def check_host(self, sample, initial, cap_bytes, admission=False):
        self.checks.append(copy.deepcopy(sample))
        reserve = 8 * 2**30 + (cap_bytes if admission else 0)
        if sample["available_bytes"] < reserve:
            raise RuntimeError("Host headroom violated")
        if sample["swap_used_bytes"] > initial["swap_used_bytes"]:
            raise RuntimeError("Host swap increased")
        if sample["full_total_us"] > initial["full_total_us"]:
            raise RuntimeError("Host pressure increased")
        if sample["foreign_freecad"]:
            raise RuntimeError("Foreign native process")

    @staticmethod
    def process_start(pid):
        return "13962132"

    def stop_owned(self, pid, start):
        self.stops.append((pid, start))
        raise AssertionError("These tests must never require process kills")

    @staticmethod
    def bind_parent(parent):
        raise AssertionError("No real subprocess may be created")

    @staticmethod
    def verify_measurements(*unused):
        return {"fixture": True}

    @staticmethod
    def check_memory_limits(sample):
        if int(sample["memory.peak"]) > 12 * 2**30:
            raise RuntimeError("Synthetic memory limit exceeded")

    @staticmethod
    def validate_telemetry(sample):
        return {"memory.peak": int(sample["memory.peak"])}


class CoordinatorTests(unittest.TestCase):
    """Assert launch/refusal outcomes across the real coordinator path."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tt-handover-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.output.mkdir()
        self.guard_path = self.root / "prior-guard"
        self.guard_path.mkdir()
        self.helpers = Helpers()
        self.clock = Clock()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("ROOT", self.root), ("OUTPUT", self.output)):
            self.stack.enter_context(mock.patch.object(coordinator, name, value))
        self.stack.enter_context(mock.patch.object(
            coordinator.time, "monotonic", self.clock.monotonic,
        ))
        self.stack.enter_context(mock.patch.object(
            coordinator.time, "sleep", self.clock.sleep,
        ))
        self.stack.enter_context(mock.patch.object(
            coordinator.subprocess, "run",
            side_effect=AssertionError("Unexpected host command"),
        ))
        self.stack.enter_context(mock.patch.object(
            coordinator.subprocess, "Popen",
            side_effect=AssertionError("Unexpected process launch"),
        ))
        self.ownership = {
            "schema_version": 1,
            "supervisor_pid": 410947,
            "supervisor_start": "13962138",
            "scope": SCOPE,
            "invocation": "6d8ccbf02c274e19b7f4730725181bb6",
            "cgroup": CGROUP,
            "lease_id": "2a419af1fed44aff81b7adb72d98a6e4",
        }
        self.write(self.guard_path / "ownership.json", self.ownership)
        self.runtime = {
            "status": "PASS",
            "process_exit": 0,
            "guard_path": str(self.guard_path),
            "final_host": host_sample(),
            "guard_result": {
                "status": "completed",
                "process_exit": 0,
                "process_exit_after_cleanup": 0,
                "cleanup_proved": True,
                "failure_reason": None,
                "scope": SCOPE,
                "cgroup": CGROUP,
                "invocation": self.ownership["invocation"],
                "lease_id": self.ownership["lease_id"],
            },
        }
        self.listing = [{
            "application": APP, "pid": PID, "instance": INSTANCE,
        }]
        self.observed = {"pid_exists": False, "cgroup_empty": True}

    @staticmethod
    def write(path, value):
        Path(path).write_text(json.dumps(value))

    def install_observations(self, observations, predecessor=None):
        """Mock only OS observations; leave handover policy executable."""
        state = {"calls": 0, "timeouts": [], "empty_seen": False}

        def read(timeout):
            state["timeouts"].append(timeout)
            index = min(state["calls"], len(observations) - 1)
            state["calls"] += 1
            value = observations[index]
            if isinstance(value, BaseException):
                raise value
            if callable(value):
                value = value()
            state["empty_seen"] |= not value
            return copy.deepcopy(value)

        self.stack.enter_context(mock.patch.object(
            coordinator, "read_flatpak_instances", read, create=True,
        ))
        self.stack.enter_context(mock.patch.object(
            coordinator, "observe_predecessor",
            side_effect=predecessor if isinstance(predecessor, BaseException)
            else None,
            return_value=predecessor or self.observed, create=True,
        ))
        return state

    def prepare_main(self, observations):
        state = self.install_observations(observations)
        manifest = {"candidate": "bf41a7dd", "sentinel": "TEST_OK",
                    "files": []}
        manifest_path = self.output / "manifest.json"
        self.write(manifest_path, manifest)
        self.write(self.output / "pre-execution-review.json", {
            "decision": "PASS", "manifest_sha256": hashlib.sha256(
                manifest_path.read_bytes()).hexdigest(),
        })
        self.write(self.output / "independent-recovery-review.json", {
            "result": "PASS",
        })
        launches = []

        def stage(name, command, cap_mib, guard_parent, helpers):
            if name == "runtime-qualification":
                directory = self.output / name
                directory.mkdir()
                (directory / "stdout").write_text(
                    'TRACKTEMPLATE_TOOLCHAIN_PREFLIGHT={"status":"passed"}\n'
                )
                return copy.deepcopy(self.runtime)
            launches.append({"name": name, "empty_seen": state["empty_seen"],
                             "at": self.clock.monotonic()})
            directory = self.output / "comparison-guard"
            directory.mkdir()
            (directory / "stdout").write_text("TEST_OK\n")
            self.write(self.output / "native-result.json", {
                "status": "PASS", "comparisons": 702, "tests": 5,
                "negative_cases": 106, "completed_monotonic_seconds": 101,
            })
            return {"status": "PASS", "guard_result": {},
                    "final_host": host_sample()}

        self.stack.enter_context(mock.patch.object(
            coordinator, "load_helpers", return_value=self.helpers,
        ))
        self.stack.enter_context(mock.patch.object(
            coordinator, "run_stage", side_effect=stage,
        ))
        return state, launches

    def run_main(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return coordinator.main()

    def assert_wait_failure(self):
        with self.assertRaises(Exception):
            coordinator.wait_for_handover(self.runtime, self.helpers)
        receipt = self.helpers.read_json(self.output / "handover-result.json")
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(self.helpers.stops, [])
        return receipt

    def test_main_delayed_cleanup_admits_once_only_after_empty(self):
        state, launches = self.prepare_main([self.listing, self.listing, []])
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(len(launches), 1)
        self.assertTrue(launches[0]["empty_seen"])
        self.assertGreaterEqual(state["calls"], 3)
        self.assertGreater(launches[0]["at"], 100.0)

    def test_main_persistent_listing_never_admits(self):
        unused, launches = self.prepare_main([self.listing])
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(launches, [])
        self.assertLessEqual(self.clock.value, 110.0)

    def test_main_foreign_listing_never_admits(self):
        foreign = [{"application": APP, "pid": PID + 1,
                    "instance": "23817292"}]
        unused, launches = self.prepare_main([foreign])
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(launches, [])
        self.assertEqual(self.clock.sleeps, [])

    def test_main_query_failure_never_admits(self):
        unused, launches = self.prepare_main([OSError("query failed")])
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(launches, [])

    def test_wait_empty_is_immediately_ready(self):
        state = self.install_observations([[]])
        coordinator.wait_for_handover(self.runtime, self.helpers)
        receipt = self.helpers.read_json(self.output / "handover-result.json")
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(state["calls"], 1)
        self.assertEqual(self.clock.sleeps, [])

    def test_deadline_does_not_accept_late_empty_observation(self):
        def late_empty():
            self.clock.value = 110.0
            return []

        state = self.install_observations([late_empty])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 1)

    def test_persistent_listing_has_one_fixed_deadline(self):
        state = self.install_observations([self.listing])
        self.assert_wait_failure()
        self.assertLessEqual(self.clock.value, 110.0)
        self.assertLessEqual(state["calls"], 41)
        for index, timeout in enumerate(state["timeouts"]):
            self.assertGreater(timeout, 0)
            self.assertLessEqual(timeout, 10.0 - index * 0.25)

    def test_foreign_instance_fails_without_waiting(self):
        self.install_observations([[{
            "application": APP, "pid": PID + 1, "instance": "99999",
        }]])
        self.assert_wait_failure()
        self.assertEqual(self.clock.sleeps, [])

    def test_multiple_freecad_instances_fail_without_waiting(self):
        self.install_observations([self.listing + [{
            "application": APP, "pid": PID + 1, "instance": "99999",
        }]])
        self.assert_wait_failure()
        self.assertEqual(self.clock.sleeps, [])

    def test_changed_instance_identity_fails(self):
        changed = copy.deepcopy(self.listing)
        changed[0]["instance"] = "99999"
        state = self.install_observations([self.listing, changed, []])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 2)

    def test_live_or_reused_predecessor_pid_fails(self):
        self.install_observations([self.listing], {
            "pid_exists": True, "cgroup_empty": True,
        })
        self.assert_wait_failure()

    def test_live_predecessor_cgroup_fails(self):
        self.install_observations([self.listing], {
            "pid_exists": False, "cgroup_empty": False,
        })
        self.assert_wait_failure()

    def test_predecessor_observation_error_fails(self):
        self.install_observations([[]], PermissionError("proc unreadable"))
        self.assert_wait_failure()

    def test_failed_cleanup_receipt_fails_before_observation(self):
        self.runtime["guard_result"]["cleanup_proved"] = False
        state = self.install_observations([[]])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 0)

    def test_unreaped_child_fails_before_observation(self):
        self.runtime["guard_result"]["process_exit_after_cleanup"] = None
        state = self.install_observations([[]])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 0)

    def test_mismatched_ownership_fails_before_observation(self):
        self.ownership["invocation"] = "0" * 32
        self.write(self.guard_path / "ownership.json", self.ownership)
        state = self.install_observations([[]])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 0)

    def test_untrusted_scope_path_fails_before_observation(self):
        self.runtime["guard_result"]["cgroup"] = "/../../proc"
        state = self.install_observations([[]])
        self.assert_wait_failure()
        self.assertEqual(state["calls"], 0)

    def test_query_exception_keeps_failure_evidence(self):
        self.install_observations([OSError("flatpak unavailable")])
        receipt = self.assert_wait_failure()
        self.assertIn("flatpak unavailable", json.dumps(receipt))

    def test_host_pressure_during_wait_fails(self):
        self.install_observations([self.listing, []])
        pressured = host_sample()
        pressured["full_total_us"] += 1
        with mock.patch.object(self.helpers, "host_sample",
                               side_effect=[host_sample(), pressured]):
            self.assert_wait_failure()

    def refusal_stage(self, *, receipt=None, malformed=False, second=False,
                      ownership=False):
        guard = self.output / "comparison-guard"
        guard_result = receipt or {
            "schema_version": 1, "status": "refused", "process_exit": None,
            "cleanup_proved": False,
            "failure_reason": "foreign-freecad-instance",
            "execution_failure_reason": "foreign-freecad-instance",
        }

        def launch(*args, **kwargs):
            guard.mkdir()
            if malformed:
                (guard / "result.json").write_text("broken json")
            else:
                self.write(guard / "result.json", guard_result)
            if ownership:
                self.write(guard / "ownership.json", self.ownership)
            if second:
                other = self.output / "other-guard"
                other.mkdir()
                self.write(other / "result.json", guard_result)
            process = mock.Mock(pid=77123, returncode=1)
            process.poll.return_value = 1
            return process

        with mock.patch.object(coordinator.subprocess, "Popen",
                               side_effect=launch):
            with self.assertRaises(RuntimeError):
                coordinator.run_stage(
                    "comparison", ["fixture-guard"], 12288,
                    self.output, self.helpers,
                )
        self.assertEqual(self.helpers.stops, [])
        return self.helpers.read_json(
            self.output / "comparison/stage-result.json",
        ), guard_result

    def test_prelaunch_refusal_preserves_original_cause_without_ownership(self):
        record, raw = self.refusal_stage()
        self.assertEqual(record["status"], "REFUSED")
        self.assertEqual(record["failure_reason"], "foreign-freecad-instance")
        self.assertTrue(record["pre_launch"])
        self.assertFalse(record["payload_started"])
        self.assertEqual(record["guard_result"], raw)
        self.assertFalse(record["guard_result"]["cleanup_proved"])
        self.assertNotIn("AssertionError", record.get("exception", ""))
        self.assertEqual(self.helpers.read_json(
            self.output / "comparison-guard/result.json"), raw)

    def test_multiple_receipts_cannot_be_a_prelaunch_refusal(self):
        record, unused = self.refusal_stage(second=True)
        self.assertEqual(record["status"], "FAIL")
        self.assertFalse(record.get("pre_launch", False))

    def test_malformed_receipt_is_failure(self):
        record, unused = self.refusal_stage(malformed=True)
        self.assertEqual(record["status"], "FAIL")

    def test_refusal_with_ownership_is_not_reported_as_never_launched(self):
        record, unused = self.refusal_stage(ownership=True)
        self.assertEqual(record["status"], "FAIL")
        self.assertFalse(record.get("pre_launch", False))

    def test_refusal_with_payload_exit_is_not_never_launched(self):
        record, unused = self.refusal_stage(receipt={
            "status": "refused", "process_exit": 0,
            "cleanup_proved": False, "failure_reason": "foreign-instance",
        })
        self.assertEqual(record["status"], "FAIL")
        self.assertFalse(record.get("pre_launch", False))

    def test_refusal_missing_process_exit_does_not_prove_no_launch(self):
        record, unused = self.refusal_stage(receipt={
            "status": "refused", "cleanup_proved": False,
            "failure_reason": "foreign-freecad-instance",
        })
        self.assertEqual(record["status"], "FAIL")
        self.assertFalse(record.get("pre_launch", False))

    def test_refusal_with_reaped_payload_is_not_never_launched(self):
        record, unused = self.refusal_stage(receipt={
            "status": "refused", "process_exit": None,
            "process_exit_after_cleanup": 0, "cleanup_proved": False,
            "failure_reason": "foreign-freecad-instance",
        })
        self.assertEqual(record["status"], "FAIL")
        self.assertFalse(record.get("pre_launch", False))

    def completed_stage(self, ownership="valid", telemetry=True):
        guard = self.output / "comparison-guard"

        def launch(*args, **kwargs):
            guard.mkdir()
            receipt = {
                "status": "completed", "process_exit": 0,
                "cleanup_proved": True, "failure_reason": None,
                "kernel_limits": {"memory.swap.max": "0"},
            }
            self.write(guard / "result.json", receipt)
            if ownership == "valid":
                identity = dict(self.ownership, supervisor_pid=77123,
                                supervisor_start="13962132")
                self.write(guard / "ownership.json", identity)
            elif ownership == "malformed":
                (guard / "ownership.json").write_text("malformed")
            measurements = [{"memory.peak": "52740096"}] if telemetry else []
            (guard / "measurements.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in measurements)
            )
            process = mock.Mock(pid=77123, returncode=0)
            process.poll.side_effect = [None, 0, 0]
            return process

        with mock.patch.object(coordinator.subprocess, "Popen",
                               side_effect=launch):
            if ownership == "valid" and telemetry:
                coordinator.run_stage(
                    "comparison", ["fixture-guard"], 12288,
                    self.output, self.helpers,
                )
            else:
                with self.assertRaises(RuntimeError):
                    coordinator.run_stage(
                        "comparison", ["fixture-guard"], 12288,
                        self.output, self.helpers,
                    )
        self.assertEqual(self.helpers.stops, [])
        return self.helpers.read_json(
            self.output / "comparison/stage-result.json",
        )

    def test_completed_stage_retains_ownership_and_measurement_checks(self):
        record = self.completed_stage()
        self.assertEqual(record["status"], "PASS")
        self.assertEqual(record["recorded_peak_bytes"], 52740096)

    def test_completed_stage_without_ownership_fails(self):
        self.assertEqual(self.completed_stage(ownership="missing")["status"],
                         "FAIL")

    def test_completed_stage_with_malformed_ownership_fails(self):
        self.assertEqual(self.completed_stage(ownership="malformed")["status"],
                         "FAIL")

    def test_completed_stage_without_telemetry_fails(self):
        self.assertEqual(self.completed_stage(telemetry=False)["status"],
                         "FAIL")


class PredecessorAdapterTests(unittest.TestCase):
    """Read only synthetic process and cgroup trees."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tt-observer-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proc = self.root / "proc"
        self.groups = self.root / "cgroups"
        self.proc.mkdir()
        self.groups.mkdir()
        self.group = self.groups / CGROUP.lstrip("/")

    def observe(self):
        return coordinator.observe_predecessor(
            PID, CGROUP, proc_root=self.proc, cgroup_root=self.groups,
        )

    def create_group(self, processes="", events="populated 0\nfrozen 0\n"):
        self.group.mkdir(parents=True)
        (self.group / "cgroup.procs").write_text(processes)
        if events is not None:
            (self.group / "cgroup.events").write_text(events)

    def test_absent_pid_and_cgroup_are_clear(self):
        self.assertEqual(self.observe(), {
            "pid_exists": False, "cgroup_empty": True,
        })

    def test_existing_pid_is_detected_even_with_no_cgroup(self):
        (self.proc / str(PID)).mkdir()
        self.assertTrue(self.observe()["pid_exists"])

    def test_existing_empty_cgroup_is_clear(self):
        self.create_group()
        self.assertTrue(self.observe()["cgroup_empty"])

    def test_descendant_population_is_not_clear(self):
        self.create_group(events="populated 1\nfrozen 0\n")
        self.assertFalse(self.observe()["cgroup_empty"])

    def test_process_list_is_not_clear_despite_zero_population(self):
        self.create_group(processes="778899\n")
        self.assertFalse(self.observe()["cgroup_empty"])

    def test_missing_events_with_existing_group_is_not_cleanup_proof(self):
        self.create_group(events=None)
        with self.assertRaises(Exception):
            self.observe()

    def test_duplicate_event_keys_are_rejected(self):
        self.create_group(events="populated 1\npopulated 0\n")
        with self.assertRaises(Exception):
            self.observe()

    def test_malformed_events_are_rejected(self):
        self.create_group(events="populated\n")
        with self.assertRaises(Exception):
            self.observe()

    def test_unreadable_process_identity_is_not_absence(self):
        original = Path.stat
        pid_path = self.proc / str(PID)

        def stat(path, *args, **kwargs):
            if path == pid_path:
                raise PermissionError("Process identity unreadable")
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "stat", stat):
            with self.assertRaises(PermissionError):
                self.observe()


class FlatpakAdapterTests(unittest.TestCase):
    """Parse synthetic process listings without invoking Flatpak."""

    def invoke(self, text, returncode=0, stderr="", timeout=3.5):
        response = subprocess.CompletedProcess([], returncode, text, stderr)
        with mock.patch.object(coordinator.subprocess, "run",
                               return_value=response) as run:
            result = coordinator.read_flatpak_instances(timeout)
        run.assert_called_once_with(
            ["flatpak", "ps", "--columns=application,pid,instance"],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        return result

    def test_valid_listing_preserves_identity(self):
        result = self.invoke(
            f"{APP}\t{PID}\t{INSTANCE}\ncom.google.Chrome\t6521\t23817292\n"
        )
        self.assertIn({"application": APP, "pid": PID,
                       "instance": INSTANCE}, result)

    def test_empty_listing_is_valid(self):
        self.assertEqual(self.invoke(""), [])

    def test_malformed_rows_are_rejected(self):
        cases = [
            f"{APP}\t{PID}\n", f"{APP}\tnan\t{INSTANCE}\n",
            f"{APP}\t0\t{INSTANCE}\n", f"{APP}\t-1\t{INSTANCE}\n",
            f"{APP}\t{PID}\t\n", f"{APP}\t{PID}\t{INSTANCE}\textra\n",
            f"{APP}\t{PID}\t{INSTANCE}\n{APP}\t{PID}\t{INSTANCE}\n",
        ]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(Exception):
                self.invoke(text)

    def test_failed_command_is_not_an_empty_listing(self):
        with self.assertRaises(Exception):
            self.invoke("", returncode=1, stderr="query failed")

    def test_query_timeout_propagates(self):
        with mock.patch.object(coordinator.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired(
                                   "flatpak", 0.2)):
            with self.assertRaises(Exception):
                coordinator.read_flatpak_instances(0.2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
