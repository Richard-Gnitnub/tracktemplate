#!/usr/bin/env python3
"""Check hosted-pilot admission and evidence without launching FreeCAD."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_native_geometry_pilot as pilot  # noqa: E402


PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-"
    "py3.13.15-qt6.11.2-coin4.0.10"
)
GEOMETRY_SENTINEL = (
    "Phase 6 transition transient exact geometry validation passed"
)
RUNTIME_SENTINEL = "TRACKTEMPLATE_HOSTED_RUNTIME="


def hosted_environment():
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "Richard-Gnitnub/tracktemplate",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_RUN_ATTEMPT": "1",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
    }


def meminfo(available_kib=12 * 1024**2):
    return (
        "MemTotal:       16777216 kB\n"
        f"MemAvailable:   {available_kib} kB\n"
        "SwapTotal:             0 kB\n"
        "SwapFree:              0 kB\n"
    )


def live_sample():
    return {
        "monotonic_seconds": 1.0,
        "memory.current": "1048576",
        "memory.peak": "2097152",
        "memory.events": "low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n",
        "memory.swap.current": "0",
        "memory.pressure": (
            "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
            "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        ),
        "cpu.stat": (
            "usage_usec 300000\nuser_usec 250000\nsystem_usec 50000\n"
            "nr_periods 4\nnr_throttled 0\nthrottled_usec 0\n"
        ),
        "pids.current": "3",
        "cgroup.events": "populated 1\nfrozen 0\n",
        "cgroup.procs": "101\n102\n103\n",
    }


def good_guard():
    return {
        "schema_version": 1,
        "status": "completed",
        "process_exit": 0,
        "process_exit_after_cleanup": 0,
        "cleanup_proved": True,
        "failure_reason": None,
        "execution_failure_reason": None,
        "deadline_cancellation_exit": 0,
        "scope": "tracktemplate-validation-example.scope",
        "invocation": "0123456789abcdef0123456789abcdef",
        "cgroup": "/user.slice/example.scope",
        "limits": {
            "memory_max_mib": 4096,
            "timeout_seconds": 900,
            "cpu_percent": 100,
            "tasks_max": 128,
        },
        "kernel_limits": {
            "memory.max": "4294967296",
            "memory.high": "4294967296",
            "memory.swap.max": "0",
            "cpu.max": "100000 100000",
            "pids.max": "128",
        },
    }


def qualified_output():
    runtime = {
        "compatibility_evaluation": {
            "status": "qualified",
            "matched_profile_id": PROFILE,
            "mismatches": [],
        },
    }
    return RUNTIME_SENTINEL + json.dumps(runtime) + "\n" + (
        GEOMETRY_SENTINEL + "\n"
    )


def native_report():
    return "\nRan 1 test in 0.500s\n\nOK\n"


def rea_report(mode):
    paths = (
        "tests/fixtures/phase9b-rea-bc-source.json",
        "tests/validate_phase1_turnout.py",
        "reference/contracts/phase1-compatibility.json",
        "reference/contracts/phase1-transition-pilot.json",
        "TrackTemplate.FCMacro",
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
    )
    native = mode == "native"
    checks = {
        "source_scalars": 425, "timber_records": 165, "rail_anchors": 70,
        "mapped_points": 1, "scene_lines": 319, "canonical_reads": 13,
        "negative_controls": 7, "undo_redo": 2, "save_reopen": 2, "no_op": 1,
    }
    if not native:
        checks = dict.fromkeys(checks, 0)
    return {
        "mode": mode, "status": "PASS", "tests": 2 if native else 1,
        "failures": 0, "errors": 0, "skips": 0,
        "documents_created": 2 if native else 0, "documents_remaining": 0,
        "input_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in paths
        },
        "checks": checks, "elapsed_seconds": 0.5,
    }


class ReaWorkloadTests(unittest.TestCase):
    def assess(self, mode, *, report=None, stdout=None, stderr=None):
        record = rea_report(mode) if report is None else report
        output = qualified_output().replace(GEOMETRY_SENTINEL + "\n", "")
        output += "TRACKTEMPLATE_REA_TRACKWORK=" + json.dumps(record) + "\n"
        return pilot.assess_result(
            good_guard(), output if stdout is None else stdout,
            (f"\nRan {record['tests']} tests in 0.500s\n\nOK\n"
             if stderr is None else stderr), [live_sample()], True,
            workload="rea-bc-" + mode,
        )

    def test_workload_commands_are_fixed_and_default_is_unchanged(self):
        transition = [
            "flatpak", "run", "--command=FreeCADCmd",
            "--env=OMP_NUM_THREADS=1", "--env=OPENBLAS_NUM_THREADS=1",
            pilot.guard.APP_ID, "-P", str(ROOT / "tests"), "-t",
            "hosted_transition_geometry_suite.TestTransitionGeometry."
            "test_transition",
        ]
        self.assertEqual(pilot._native_command(), transition)
        for mode in ("readiness", "native"):
            with self.subTest(mode=mode):
                expected = transition[:5] + [
                    "--env=TRACKTEMPLATE_REA_MODE=" + mode,
                    *transition[5:-1], "freecad_validate_rea_trackwork",
                ]
                self.assertEqual(pilot._native_command("rea-bc-" + mode),
                                 expected)
        for name in ("", "REA-BC-native", "native", "x; echo unsafe"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                pilot._native_command(name)

    def test_readiness_and_lifecycle_have_distinct_pass_classifications(self):
        for mode, count, classification in (
            ("readiness", 1, "REA_BC_READINESS_PASS"),
            ("native", 2, "REA_BC_NATIVE_PASS"),
        ):
            with self.subTest(mode=mode):
                result = self.assess(mode)
                self.assertEqual(result["status"], "PASS", result)
                self.assertEqual(result["classification"], classification)
                self.assertEqual(result["workload"], "rea-bc-" + mode)
                self.assertEqual(result["completed_native_tests"], count)
                self.assertEqual(result["rea_trackwork"], rea_report(mode))

    def test_incomplete_or_geometry_bearing_reports_fail_closed(self):
        for mode in ("readiness", "native"):
            variants = [
                {"mode": "native" if mode == "readiness" else "readiness"},
                {"status": "FAIL"}, {"tests": True}, {"failures": 1},
                {"errors": False}, {"skips": 1}, {"documents_remaining": 1},
                {"documents_created": 1}, {"elapsed_seconds": float("nan")},
                {"elapsed_seconds": -1.0}, {"elapsed_seconds": True},
                {"elapsed_seconds": 901.0}, {"elapsed_seconds": 10**400},
                {"unexpected_geometry": [1, 2, 3]}, {"input_sha256": {}},
                {"checks": {}},
            ]
            for updates in variants:
                with self.subTest(mode=mode, updates=updates):
                    record = rea_report(mode)
                    record.update(updates)
                    result = self.assess(mode, report=record)
                    self.assertEqual(result["classification"],
                                     "EVIDENCE_INCOMPLETE", result)
                    self.assertEqual(result["expected_native_tests"],
                                     1 if mode == "readiness" else 2)

    def test_hashes_and_check_counters_must_match_the_selected_mode(self):
        for mode in ("readiness", "native"):
            record = rea_report(mode)
            for group, key, value in (
                ("input_sha256", next(iter(record["input_sha256"])), "0" * 64),
                ("input_sha256", "extra-file", "0" * 64),
                ("checks", "source_scalars", -1),
                ("checks", "source_scalars", True),
                ("checks", "source_scalars", 0 if mode == "native" else 1),
                ("checks", "save_reopen", 1),
                ("checks", "geometry", [1, 2, 3]),
            ):
                with self.subTest(mode=mode, group=group, key=key, value=value):
                    changed = copy.deepcopy(record)
                    changed[group][key] = value
                    self.assertEqual(self.assess(mode, report=changed)[
                        "classification"], "EVIDENCE_INCOMPLETE")

    def test_count_runtime_report_and_no_skips_remain_mandatory(self):
        runtime = qualified_output().replace(GEOMETRY_SENTINEL + "\n", "")
        sentinel = "TRACKTEMPLATE_REA_TRACKWORK="
        report = sentinel + json.dumps(rea_report("native")) + "\n"
        for stdout, stderr in (
            (runtime, None), (runtime + report * 2, None),
            (report, None), (runtime * 2 + report, None),
            (qualified_output(), None),
            (runtime + report, native_report()),
            (runtime + report, "Ran 2 tests in 0.1s\nOK (skipped=1)\n"),
            (runtime + report.replace('"status": "PASS"',
                                      '"status": "FAIL", "status": "PASS"'),
             None),
        ):
            with self.subTest(stdout=stdout, stderr=stderr):
                self.assertEqual(self.assess(
                    "native", stdout=stdout, stderr=stderr,
                )["classification"], "EVIDENCE_INCOMPLETE")

    def test_native_requires_every_deterministic_check_total(self):
        record = rea_report("native")
        for key, count in record["checks"].items():
            if key == "mapped_points":
                continue
            for value in (count - 1, count + 1):
                with self.subTest(key=key, value=value):
                    changed = copy.deepcopy(record)
                    changed["checks"][key] = value
                    self.assertEqual(self.assess("native", report=changed)[
                        "classification"], "EVIDENCE_INCOMPLETE")
        for value in (0, -1, True):
            with self.subTest(mapped_points=value):
                changed = copy.deepcopy(record)
                changed["checks"]["mapped_points"] = value
                self.assertEqual(self.assess("native", report=changed)[
                    "classification"], "EVIDENCE_INCOMPLETE")


class HostedAdmissionTests(unittest.TestCase):
    def test_exact_host_and_minimum_headroom_are_admitted(self):
        result = pilot.validate_admission(hosted_environment(), meminfo())
        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    def test_missing_hosted_authority_is_rejected(self):
        for key in hosted_environment():
            with self.subTest(key=key):
                environment = hosted_environment()
                del environment[key]
                with self.assertRaises(ValueError):
                    pilot.validate_admission(environment, meminfo())

    def test_wrong_repository_trigger_retry_or_runner_is_rejected(self):
        alternatives = {
            "GITHUB_ACTIONS": "false",
            "GITHUB_REPOSITORY": "someone/tracktemplate",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_RUN_ATTEMPT": "2",
            "RUNNER_ENVIRONMENT": "self-hosted",
            "RUNNER_OS": "Windows",
            "RUNNER_ARCH": "ARM64",
        }
        for key, value in alternatives.items():
            with self.subTest(key=key):
                environment = hosted_environment()
                environment[key] = value
                with self.assertRaises(ValueError):
                    pilot.validate_admission(environment, meminfo())

    def test_insufficient_headroom_is_rejected(self):
        with self.assertRaises(ValueError):
            pilot.validate_admission(
                hosted_environment(), meminfo(12 * 1024**2 - 1),
            )

    def test_missing_or_invalid_memory_telemetry_is_rejected(self):
        for text in ("", "MemAvailable: invalid kB\n", "MemTotal: 0 kB\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                pilot.validate_admission(hosted_environment(), text)


class HostedResultTests(unittest.TestCase):
    def assess(self, *, guard=None, stdout=None, stderr=None, samples=None,
               clearance=True):
        return pilot.assess_result(
            good_guard() if guard is None else guard,
            qualified_output() if stdout is None else stdout,
            native_report() if stderr is None else stderr,
            [live_sample()] if samples is None else samples,
            clearance,
        )

    def assert_failed(self, result, classification=None):
        self.assertEqual(result["status"], "FAIL", result)
        self.assertIn(result["classification"], {
            "SETUP_FAILURE", "TIMEOUT", "MEMORY_LIMIT", "CLEANUP_FAILURE",
            "GEOMETRY_FAILURE", "EVIDENCE_INCOMPLETE",
        })
        if classification is not None:
            self.assertEqual(result["classification"], classification)

    def test_complete_single_native_test_passes(self):
        result = self.assess()
        self.assertEqual(result["status"], "PASS")
        # The L1 controller also reuses the default resource assessor.
        self.assertNotIn("workload", result)

    def test_prelaunch_refusal_is_setup_failure(self):
        guard = good_guard()
        guard.update(status="refused", process_exit=None,
                     failure_reason="foreign-freecad-instance")
        self.assert_failed(self.assess(guard=guard), "SETUP_FAILURE")

    def test_failed_prerequisites_are_not_geometry_failures(self):
        for reason in (
            "scope-gate-unproved", "containment-unproved", "deadline-unarmed",
        ):
            with self.subTest(reason=reason):
                guard = good_guard()
                guard.update(
                    status="failed", process_exit=-15,
                    failure_reason=reason, execution_failure_reason=reason,
                )
                self.assert_failed(self.assess(guard=guard), "SETUP_FAILURE")

    def test_deadline_and_memory_stops_remain_distinct(self):
        for reason, classification in (
            ("deadline-exceeded", "TIMEOUT"),
            ("memory-limit", "MEMORY_LIMIT"),
        ):
            with self.subTest(reason=reason):
                guard = good_guard()
                guard.update(status="failed", process_exit=1,
                             failure_reason=reason)
                self.assert_failed(self.assess(guard=guard), classification)

    def test_nonzero_geometry_exit_cannot_pass(self):
        guard = good_guard()
        guard.update(status="failed", process_exit=1,
                     failure_reason="payload-nonzero")
        self.assert_failed(self.assess(guard=guard), "GEOMETRY_FAILURE")

    def test_nonzero_exit_without_runtime_qualification_is_setup_failure(self):
        guard = good_guard()
        guard.update(status="failed", process_exit=1,
                     failure_reason="payload-nonzero")
        self.assert_failed(
            self.assess(guard=guard, stdout=""), "SETUP_FAILURE",
        )

    def test_final_memory_stop_overrides_earlier_payload_failure(self):
        guard = good_guard()
        guard.update(
            status="failed", process_exit=1,
            failure_reason="memory-limit",
            execution_failure_reason="payload-nonzero",
        )
        self.assert_failed(self.assess(guard=guard), "MEMORY_LIMIT")

    def test_cleanup_and_deadline_cancellation_are_required(self):
        for key, value in (
            ("cleanup_proved", False),
            ("deadline_cancellation_exit", 5),
        ):
            with self.subTest(key=key):
                guard = good_guard()
                guard[key] = value
                self.assert_failed(self.assess(guard=guard))
        self.assert_failed(self.assess(clearance=False), "CLEANUP_FAILURE")

    def test_geometry_sentinel_must_appear_exactly_once(self):
        for stdout in (
            qualified_output().replace(GEOMETRY_SENTINEL, ""),
            qualified_output() + GEOMETRY_SENTINEL + "\n",
        ):
            with self.subTest(stdout=stdout):
                self.assert_failed(self.assess(stdout=stdout))

    def test_runtime_report_must_be_exact_and_qualified(self):
        for stdout in (
            GEOMETRY_SENTINEL + "\n",
            qualified_output().replace(PROFILE, "unqualified-profile"),
            qualified_output().replace('"qualified"', '"unqualified"'),
            RUNTIME_SENTINEL + "not JSON\n" + GEOMETRY_SENTINEL + "\n",
        ):
            with self.subTest(stdout=stdout):
                self.assert_failed(self.assess(stdout=stdout))

    def test_native_count_success_and_no_skips_are_required(self):
        for stderr in (
            "", "Ran 0 tests in 0.1s\n\nOK\n",
            "Ran 2 tests in 0.1s\n\nOK\n",
            "Ran 1 test in 0.1s\n\nOK (skipped=1)\n",
            "Ran 1 test in 0.1s\n\nFAILED (failures=1)\n",
        ):
            with self.subTest(stderr=stderr):
                self.assert_failed(self.assess(stderr=stderr))

    def test_missing_live_sample_or_live_field_fails(self):
        self.assert_failed(self.assess(samples=[]), "EVIDENCE_INCOMPLETE")
        for key in live_sample():
            if key == "monotonic_seconds":
                continue
            with self.subTest(key=key):
                sample = live_sample()
                del sample[key]
                self.assert_failed(self.assess(samples=[sample]))

    def test_memory_limit_events_or_swap_cannot_pass(self):
        for name in ("high", "max", "oom", "oom_kill"):
            with self.subTest(name=name):
                sample = live_sample()
                sample["memory.events"] = sample["memory.events"].replace(
                    name + " 0\n", name + " 1\n",
                )
                self.assert_failed(
                    self.assess(samples=[sample]), "MEMORY_LIMIT",
                )
        sample = live_sample()
        sample["memory.swap.current"] = "4096"
        self.assert_failed(self.assess(samples=[sample]), "MEMORY_LIMIT")

    def test_removed_terminal_sample_requires_live_evidence_and_cleanup(self):
        terminal = {key: None for key in live_sample()}
        terminal["monotonic_seconds"] = 2.0
        self.assertEqual(
            self.assess(samples=[live_sample(), terminal])["status"], "PASS",
        )
        self.assert_failed(self.assess(samples=[terminal]))
        self.assert_failed(self.assess(
            samples=[live_sample(), terminal], clearance=False,
        ))

    def test_partially_missing_terminal_sample_fails(self):
        terminal = copy.deepcopy(live_sample())
        terminal["monotonic_seconds"] = 2.0
        terminal["memory.current"] = None
        self.assert_failed(self.assess(samples=[live_sample(), terminal]))

    def test_final_samples_contribute_peak_memory_and_cpu(self):
        before = live_sample()
        before["memory.peak"] = "33554432"
        before["cpu.stat"] = before["cpu.stat"].replace(
            "usage_usec 300000", "usage_usec 900000",
        )
        after = live_sample()
        after["memory.peak"] = "67108864"
        after["cpu.stat"] = after["cpu.stat"].replace(
            "usage_usec 300000", "usage_usec 1200000",
        )
        after["pids.current"] = "0"
        after["cgroup.events"] = "populated 0\nfrozen 0\n"
        after["cgroup.procs"] = ""
        for final_samples, expected_peak, expected_cpu in (
            ({"before_cleanup": before}, 33554432, 900000),
            ({"after_cleanup": after}, 67108864, 1200000),
            ({"before_cleanup": before, "after_cleanup": after},
             67108864, 1200000),
        ):
            with self.subTest(final_samples=list(final_samples)):
                guard = good_guard()
                guard.update(final_samples)
                result = self.assess(guard=guard)
                self.assertEqual(result["status"], "PASS", result)
                self.assertEqual(
                    result["peak_cgroup_memory_bytes"], expected_peak,
                )
                self.assertEqual(result["cpu_usage_usec"], expected_cpu)

    def test_absent_final_accounting_is_labelled_as_sampled_lower_bound(self):
        removed = {key: None for key in live_sample()}
        for final_samples in (
            {}, {"before_cleanup": removed, "after_cleanup": removed},
        ):
            with self.subTest(final_samples=list(final_samples)):
                guard = good_guard()
                guard.update(final_samples)
                result = self.assess(guard=guard)
                self.assertEqual(result["status"], "PASS", result)
                self.assertEqual(
                    result.get("resource_accounting"), "sampled-lower-bound",
                )

    def test_memory_limit_events_in_final_samples_cannot_pass(self):
        for name in ("before_cleanup", "after_cleanup"):
            with self.subTest(name=name):
                final = live_sample()
                final["memory.events"] = final["memory.events"].replace(
                    "oom_kill 0", "oom_kill 1",
                )
                guard = good_guard()
                guard[name] = final
                self.assert_failed(self.assess(guard=guard), "MEMORY_LIMIT")


class DeadlineResultTests(unittest.TestCase):
    def test_failed_cancellation_needs_independent_true_clearance(self):
        result = good_guard()
        result["deadline_cancellation_exit"] = 5
        for clearance in (False, None, "true", 1, True):
            with self.subTest(clearance=clearance):
                assessment = pilot.assess_result(
                    result, qualified_output(), native_report(),
                    [live_sample()], True, deadline_clearance=clearance,
                )
                self.assertEqual(assessment["status"],
                                 "PASS" if clearance is True else "FAIL")
                if clearance is not True:
                    self.assertEqual(assessment["classification"],
                                     "CLEANUP_FAILURE")

    def test_unexpected_cancellation_exit_cannot_be_overridden(self):
        result = good_guard()
        result["deadline_cancellation_exit"] = 1
        assessment = pilot.assess_result(
            result, qualified_output(), native_report(), [live_sample()],
            True, deadline_clearance=True,
        )
        self.assertEqual(assessment["status"], "FAIL")
        self.assertEqual(assessment["classification"], "CLEANUP_FAILURE")

    def test_deadline_proof_does_not_override_other_failures(self):
        for changes, classification in (
            ({"cleanup_proved": False}, "CLEANUP_FAILURE"),
            ({"status": "failed", "failure_reason": "deadline-exceeded"},
             "TIMEOUT"),
            ({"status": "failed", "failure_reason": "memory-limit"},
             "MEMORY_LIMIT"),
            ({"status": "failed", "process_exit": 1,
              "failure_reason": "payload-nonzero"}, "GEOMETRY_FAILURE"),
        ):
            with self.subTest(classification=classification):
                result = good_guard()
                result["deadline_cancellation_exit"] = 5
                result.update(changes)
                assessment = pilot.assess_result(
                    result, qualified_output(), native_report(),
                    [live_sample()], True, deadline_clearance=True,
                )
                self.assertEqual(assessment["status"], "FAIL")
                self.assertEqual(assessment["classification"], classification)


class DeadlineClearanceTests(unittest.TestCase):
    watchdog = "tracktemplate-validation-0123456789abcdef0123456789abcdef"

    def properties(self, suffix, load_state="not-found"):
        values = {
            "Id": self.watchdog + suffix,
            "LoadState": load_state,
            "ActiveState": "inactive",
            "SubState": "dead",
            "Job": "",
        }
        if suffix == ".service":
            values.update(MainPID="0", ControlPID="0", ControlGroup="")
        return values

    def readback(self, suffix, load_state="not-found"):
        return "".join(name + "=" + value + "\n" for name, value in
                       self.properties(suffix, load_state).items())

    def probe(self, *, outputs=None, fail_suffix=None, failure=None,
              result=None):
        result = good_guard() if result is None else result
        result.setdefault("watchdog", self.watchdog)
        observed = []
        outputs = outputs or {}

        def command(argv, **kwargs):
            observed.append(list(argv))
            self.assertEqual(argv[:4],
                             ["systemctl", "--user", "show", "--all"])
            unit = argv[-1]
            self.assertIn(unit, [self.watchdog + ".timer",
                                 self.watchdog + ".service"])
            suffix = ".timer" if unit.endswith(".timer") else ".service"
            fields = list(self.properties(suffix))
            self.assertEqual(argv[4:-1:2], ["-p"] * len(fields))
            self.assertEqual(set(argv[5:-1:2]), set(fields))
            self.assertFalse(kwargs["check"])
            self.assertTrue(kwargs["capture_output"])
            self.assertTrue(kwargs["text"])
            self.assertEqual(kwargs["timeout"], 15)
            if suffix == fail_suffix and isinstance(failure, Exception):
                raise failure
            return subprocess.CompletedProcess(
                argv, failure if suffix == fail_suffix else 0,
                outputs.get(suffix, self.readback(suffix)), "query diagnostic",
            )

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(pilot, "OUTPUT", directory), patch.object(
                pilot.subprocess, "run", side_effect=command,
            ):
                proved = pilot._deadline_clearance(result)
            receipt = json.loads(
                (directory / "deadline-clearance.json").read_text(),
            )
        self.assertIs(receipt["proved"], proved)
        self.assertEqual(receipt["watchdog"], result.get("watchdog"))
        self.assertEqual([row["command"] for row in receipt["observations"]],
                         observed)
        for row in receipt["observations"]:
            if "error" not in row:
                self.assertEqual(row["stderr"], "query diagnostic")
                suffix = (".timer" if row["command"][-1].endswith(".timer")
                          else ".service")
                self.assertEqual(row["stdout"], outputs.get(
                    suffix, self.readback(suffix),
                ))
                self.assertIn("returncode", row)
        return proved, observed

    def test_loaded_or_unloaded_inactive_deadline_units_are_proved(self):
        for timer in ("loaded", "not-found"):
            for service in ("loaded", "not-found"):
                with self.subTest(timer=timer, service=service):
                    proved, observed = self.probe(outputs={
                        ".timer": self.readback(".timer", timer),
                        ".service": self.readback(".service", service),
                    })
                    self.assertIs(proved, True)
                    self.assertEqual(len(observed), 2)

    def test_active_missing_duplicate_or_wrong_unit_readback_is_rejected(self):
        for suffix in (".timer", ".service"):
            original = self.readback(suffix)
            variants = (
                original.replace("ActiveState=inactive", "ActiveState=active"),
                original.replace("SubState=dead", "SubState=running"),
                original.replace("LoadState=not-found", "LoadState=error"),
                original.replace("Job=\n", "Job=123 /job/123\n"),
                original.replace("Id=" + self.watchdog,
                                 "Id=tracktemplate-validation-foreign"),
                original + "Id=" + self.watchdog + suffix + "\n",
                "", "malformed output\n",
                *(original.replace(name + "=" + value + "\n", "")
                  for name, value in self.properties(suffix).items()),
            )
            for output in variants:
                with self.subTest(suffix=suffix, output=output):
                    self.assertIs(self.probe(outputs={suffix: output})[0],
                                  False)

    def test_service_processes_or_control_group_cannot_pass(self):
        original = self.readback(".service")
        for field, value in (("MainPID", "900"), ("ControlPID", "901"),
                             ("ControlGroup", "/user.slice/owned.service")):
            with self.subTest(field=field):
                output = original.replace(
                    field + "=" + self.properties(".service")[field],
                    field + "=" + value,
                )
                self.assertIs(self.probe(outputs={".service": output})[0],
                              False)

    def test_errors_and_timeouts_cannot_prove_clearance(self):
        for suffix in (".timer", ".service"):
            for failure in (
                1, OSError("query unavailable"),
                subprocess.TimeoutExpired("systemctl", 15),
            ):
                with self.subTest(suffix=suffix, failure=str(failure)):
                    self.assertIs(self.probe(fail_suffix=suffix,
                                             failure=failure)[0], False)

    def test_invalid_owned_name_or_unproved_cleanup_never_queries(self):
        variants = [
            {"watchdog": value} for value in (
                None, "", "--all", self.watchdog + ".service",
                "tracktemplate-validation-" + "g" * 32,
                "tracktemplate-validation-" + "0" * 31,
                self.watchdog + "\n",
            )
        ] + [{"cleanup_proved": False}]
        for changes in variants:
            with self.subTest(changes=changes):
                result = good_guard()
                result.update(changes)
                proved, observed = self.probe(result=result)
                self.assertIs(proved, False)
                self.assertEqual(observed, [])


class NativeWrapperTests(unittest.TestCase):
    def load_wrapper(self):
        path = ROOT / "tests/hosted_transition_geometry_suite.py"
        specification = importlib.util.spec_from_file_location(
            "_hosted_geometry_offline_wrapper", path,
        )
        module = importlib.util.module_from_spec(specification)
        with patch.dict(sys.modules, {"FreeCAD": None, "Part": None}):
            specification.loader.exec_module(module)
        return module

    def test_import_is_safe_without_freecad(self):
        module = self.load_wrapper()
        self.assertTrue(issubclass(module.TestTransitionGeometry,
                                   unittest.TestCase))

    def test_one_method_uses_unchanged_validator_and_reports_runtime(self):
        module = self.load_wrapper()
        report = {"compatibility_evaluation": {
            "status": "qualified", "matched_profile_id": PROFILE,
        }}
        output = io.StringIO()
        with patch("tracktemplate.bootstrap.require_qualified_runtime",
                   return_value=report), patch.object(
                       module.runpy, "run_path", return_value={},
                   ) as run_path, contextlib.redirect_stdout(output):
            result = unittest.TestResult()
            module.TestTransitionGeometry("test_transition").run(result)
        self.assertTrue(result.wasSuccessful(), result.errors)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.skipped, [])
        self.assertEqual(run_path.call_count, 1)
        self.assertEqual(
            Path(run_path.call_args.args[0]),
            ROOT / "tests/freecad_validate_phase6_transition_exact_geometry.py",
        )
        self.assertIn(RUNTIME_SENTINEL, output.getvalue())
        self.assertIn(PROFILE, output.getvalue())

    def test_verbose_runner_keeps_runtime_report_on_its_own_line(self):
        module = self.load_wrapper()
        report = {"compatibility_evaluation": {
            "status": "qualified", "matched_profile_id": PROFILE,
            "mismatches": [],
        }}
        output = io.StringIO()
        with (
            patch("tracktemplate.bootstrap.require_qualified_runtime",
                  return_value=report),
            patch.object(module.runpy, "run_path", side_effect=lambda _path:
                         print(GEOMETRY_SENTINEL)) as run_path,
            contextlib.redirect_stdout(output),
        ):
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(
                unittest.TestSuite([
                    module.TestTransitionGeometry("test_transition"),
                ]),
            )
        self.assertTrue(result.wasSuccessful(), result.errors)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.skipped, [])
        run_path.assert_called_once_with(str(
            ROOT / "tests/freecad_validate_phase6_transition_exact_geometry.py"
        ))
        assessment = pilot.assess_result(
            good_guard(), output.getvalue(), "", [live_sample()], True,
        )
        self.assertEqual(assessment["status"], "PASS", output.getvalue())
        self.assertEqual(sum(line.startswith(RUNTIME_SENTINEL)
                             for line in output.getvalue().splitlines()), 1)

    def test_original_validator_failure_propagates(self):
        module = self.load_wrapper()
        report = {"compatibility_evaluation": {
            "status": "qualified", "matched_profile_id": PROFILE,
        }}
        original_error = AssertionError("original geometry comparison failed")
        with patch("tracktemplate.bootstrap.require_qualified_runtime",
                   return_value=report), patch.object(
                       module.runpy, "run_path", side_effect=original_error,
                   ) as run_path, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(AssertionError) as caught:
                case = module.TestTransitionGeometry("test_transition")
                case.test_transition()
        self.assertIs(caught.exception, original_error)
        run_path.assert_called_once()

    def test_other_qualified_profile_is_refused_before_geometry(self):
        module = self.load_wrapper()
        report = {"compatibility_evaluation": {
            "status": "qualified", "matched_profile_id": "other-profile",
        }}
        with patch("tracktemplate.bootstrap.require_qualified_runtime",
                   return_value=report), patch.object(
                       module.runpy, "run_path",
                   ) as run_path, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(AssertionError):
                case = module.TestTransitionGeometry("test_transition")
                case.test_transition()
        run_path.assert_not_called()


class PilotIdentityTests(unittest.TestCase):
    def test_rea_entry_is_frozen_before_runtime_commands(self):
        read_bytes = Path.read_bytes
        entry = b"reviewed REA entry fixture"
        digest = hashlib.sha256(entry).hexdigest()
        commit = "1" * 40

        def changed_read(path):
            return entry if path == ROOT / pilot.REA_TEST_PATH else read_bytes(
                path,
            )

        def command(*args):
            if args == ("git", "rev-parse", "HEAD"):
                return commit
            if args == (
                "git", "status", "--porcelain", "--untracked-files=no",
            ):
                return ""
            self.fail("Unfrozen entry reached runtime metadata: " + repr(args))

        for mode in ("readiness", "native"):
            for frozen in (None, "", "0" * 64, digest + "\n"):
                with (
                    self.subTest(mode=mode, frozen=frozen),
                    patch.object(pilot, "REA_TEST_SHA256", frozen),
                    patch.object(Path, "read_bytes", changed_read),
                    patch.object(pilot, "_command", side_effect=command),
                    patch.object(pilot.os, "getuid", return_value=1000),
                    patch.dict(pilot.os.environ, {"GITHUB_SHA": commit}),
                    self.assertRaises(ValueError),
                ):
                    pilot._identity("rea-bc-" + mode)

    def test_validator_and_guard_match_retained_hashes(self):
        expected = {
            "tests/freecad_validate_rea_trackwork.py": (
                "32a3dffdbb6cbe3d378a14de80c20a1a961d5d77935c627c606ae2ad7b909a7e"
            ),
            "tests/freecad_validate_phase6_transition_exact_geometry.py": (
                "e9df630ef1a33a20b52b0bd961dd4255e9e23ad8344f8832718a095baee7cf51"
            ),
            "tools/freecad_validation_guard.py": (
                "b193209f0f21f28c3c17f9c52e509e31dccb32690152c02414769c0f6e49c559"
            ),
        }
        self.assertEqual(pilot.TEST_SHA256, expected[pilot.TEST_PATH])
        self.assertEqual(pilot.REA_TEST_SHA256, expected[pilot.REA_TEST_PATH])
        self.assertEqual(
            pilot.GUARD_SHA256, expected["tools/freecad_validation_guard.py"],
        )
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                    digest,
                )

    def test_changed_frozen_input_is_rejected_before_runtime_commands(self):
        read_bytes = Path.read_bytes
        commit = "1" * 40

        def command(*args):
            if args == ("git", "rev-parse", "HEAD"):
                return commit
            if args == (
                "git", "status", "--porcelain", "--untracked-files=no",
            ):
                return ""
            self.fail("Changed input reached a runtime command: " + repr(args))

        for name in (pilot.TEST_PATH, "tools/freecad_validation_guard.py"):
            with self.subTest(name=name):
                def changed_read(path):
                    original = read_bytes(path)
                    if path == ROOT / name:
                        return original + b"\n"
                    return original

                with (
                    patch.object(Path, "read_bytes", changed_read),
                    patch.object(pilot, "_command", side_effect=command),
                    patch.object(pilot.os, "getuid", return_value=1000),
                    patch.dict(pilot.os.environ, {"GITHUB_SHA": commit}),
                    self.assertRaisesRegex(ValueError, "identity changed"),
                ):
                    pilot._identity()

    def test_workflow_is_manual_read_only_pinned_and_non_cancelling(self):
        path = ROOT / ".github/workflows/native-geometry-pilot.yml"
        workflow = path.read_text()

        def top_block(name):
            match = re.search(
                rf"^{name}:\n((?:[ \t].*\n|\n)*)", workflow, re.MULTILINE,
            )
            self.assertIsNotNone(match, name)
            return [
                line.strip() for line in match[1].splitlines() if line.strip()
            ]

        self.assertEqual(top_block("on"), [
            "workflow_dispatch:", "inputs:", "workload:",
            "description: Bounded native workload", "required: true",
            "type: choice", "default: transition", "options:",
            "- transition", "- rea-bc-readiness", "- rea-bc-native",
        ])
        self.assertIn("TRACKTEMPLATE_HOSTED_WORKLOAD: ${{ inputs.workload }}",
                      workflow)
        self.assertIn("'workload': os.environ['PILOT_WORKLOAD']", workflow)
        self.assertIn("PILOT_WORKLOAD: ${{ inputs.workload }}", workflow)
        uploaded_paths = re.findall(
            r"^            (benchmark-output/[^\n]+)$", workflow, re.MULTILINE,
        )
        self.assertEqual(len(uploaded_paths), 14)
        self.assertFalse(any("*" in path or "FCStd" in path
                             for path in uploaded_paths))
        self.assertEqual(top_block("permissions"), ["contents: read"])
        self.assertEqual(len(re.findall(r"^\s*permissions:", workflow,
                                       re.MULTILINE)), 1)
        self.assertEqual(
            re.findall(r"^\s*cancel-in-progress:\s*(\S+)", workflow,
                       re.MULTILINE), ["false"],
        )
        actions = re.findall(r"^\s*uses:\s*(\S+)", workflow, re.MULTILINE)
        self.assertTrue(actions)
        for action in actions:
            self.assertRegex(action, r"^[A-Za-z0-9_./-]+@[0-9a-f]{40}$")


_SETUP_STUB = r"""import json
import os
from pathlib import Path
import sys

command = [Path(sys.argv[0]).name, *sys.argv[1:]]
with open(os.environ["SETUP_CALLS"], "a") as stream:
    stream.write(json.dumps(command) + "\n")
fixture = json.loads(Path(os.environ["SETUP_FIXTURE"]).read_text())
manager = "user@1001.service"
group = "/user.slice/user-1001.slice/" + manager
output = "benchmark-output/hosted-native-geometry"
if command == ["mkdir", "-p", output]:
    Path(output).mkdir(parents=True)
elif command == ["tee", output + "/setup.log"]:
    data = sys.stdin.read()
    Path(output, "setup.log").write_text(data)
    sys.stdout.write(data)
elif command == ["id", "-u"]:
    print("1001")
elif command == ["id", "-un"]:
    print("runner")
elif command[:2] == ["sudo", "apt-get"]:
    assert command[2:] in (
        ["update"],
        ["install", "--no-install-recommends", "-y", "flatpak",
         "dbus-user-session"],
    ), command
elif command[:2] == ["sudo", "flatpak"]:
    assert command[2] in ("remote-add", "install", "update"), command
elif command == ["sudo", "loginctl", "enable-linger", "runner"]:
    pass
elif command == ["sudo", "systemctl", "start", manager]:
    pass
elif command[:3] == ["sudo", "systemctl", "set-property"]:
    print("Cannot set property Delegate, or unknown property.",
          file=sys.stderr)
    sys.exit(1)
elif command[:3] == ["systemctl", "show", manager]:
    arguments = command[3:]
    properties = []
    while arguments:
        option = arguments.pop(0)
        if option == "-p":
            properties.append(arguments.pop(0))
        else:
            assert option == "--value", command
    if fixture.get("failed_property") in properties:
        print("Injected systemctl query failure", file=sys.stderr)
        sys.exit(1)
    for name in properties:
        value = fixture["properties"][name]
        print(value if "--value" in command else name + "=" + value)
elif command == ["cat", "/sys/fs/cgroup" + group + "/cgroup.controllers"]:
    if fixture["kernel_controllers"] is None:
        print("Injected cgroup read failure", file=sys.stderr)
        sys.exit(1)
    print(fixture["kernel_controllers"])
else:
    raise AssertionError("Unexpected command: " + repr(command))
"""


class HostedSetupTests(unittest.TestCase):
    """Run the workflow's setup shell with no access to host commands."""

    def setup_shell(self):
        path = ROOT / ".github/workflows/native-geometry-pilot.yml"
        workflow = path.read_text()
        setup = workflow.split("        id: setup\n", 1)[1]
        body = setup.split("        run: |\n", 1)[1]
        body = body.split("\n      - name:", 1)[0]
        lines = body.splitlines()
        self.assertTrue(all(not line or line.startswith("          ")
                            for line in lines))
        return "\n".join(line[10:] for line in lines) + "\n"

    def execute_setup(self, *, properties=None, kernel_controllers=None,
                      failed_property=None, unreadable_kernel=False):
        fixture = {
            "properties": {
                "ActiveState": "active",
                "ControlGroup": (
                    "/user.slice/user-1001.slice/user@1001.service"
                ),
                "Delegate": "yes",
                "DelegateControllers": "pids memory cpu",
            },
            "kernel_controllers": "cpuset cpu io memory pids",
            "failed_property": failed_property,
        }
        fixture["properties"].update(properties or {})
        if kernel_controllers is not None:
            fixture["kernel_controllers"] = kernel_controllers
        if unreadable_kernel:
            fixture["kernel_controllers"] = None
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            binary = directory / "bin"
            binary.mkdir()
            stub = binary / "stub"
            stub.write_text(f"#!{sys.executable}\n" + _SETUP_STUB)
            stub.chmod(0o700)
            for command in ("sudo", "id", "systemctl", "cat", "mkdir", "tee"):
                (binary / command).symlink_to(stub)
            inputs = directory / "fixture.json"
            inputs.write_text(json.dumps(fixture))
            calls = directory / "calls.jsonl"
            environment_file = directory / "github-env"
            result = subprocess.run(
                ["/bin/bash", "--noprofile", "--norc", "-c",
                 self.setup_shell()],
                cwd=directory,
                env={
                    "PATH": str(binary),
                    "GITHUB_RUN_ATTEMPT": "1",
                    "GITHUB_ENV": str(environment_file),
                    "SETUP_FIXTURE": str(inputs),
                    "SETUP_CALLS": str(calls),
                },
                text=True, capture_output=True, timeout=10, check=False,
            )
            observed = [
                json.loads(line) for line in calls.read_text().splitlines()
            ]
            exported = (environment_file.read_text()
                        if environment_file.exists() else "")
        return result, observed, exported

    def assert_refused_after_query(self, result, calls, exported):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(any(command[:2] == ["systemctl", "show"]
                            for command in calls), calls)
        self.assertEqual(exported, "")

    def test_existing_delegation_admits_without_runtime_mutation(self):
        result, calls, exported = self.execute_setup()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(["sudo", "loginctl", "enable-linger", "runner"], calls)
        self.assertIn(
            ["sudo", "systemctl", "start", "user@1001.service"], calls,
        )
        self.assertIn(
            ["cat", "/sys/fs/cgroup/user.slice/user-1001.slice/"
             "user@1001.service/cgroup.controllers"], calls,
        )
        self.assertEqual(exported.splitlines(), [
            "XDG_RUNTIME_DIR=/run/user/1001",
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus",
        ])
        self.assertFalse(any("set-property" in command or "restart" in command
                             for command in calls), calls)

    def test_inactive_wrong_or_undelegated_manager_is_refused(self):
        for name, value in (
            ("ActiveState", "inactive"), ("ActiveState", ""),
            ("ActiveState", "active\ninactive"),
            ("ControlGroup", "/user.slice/user-1002.slice/user@1002.service"),
            ("ControlGroup", ""), ("Delegate", "no"),
            ("Delegate", ""), ("Delegate", "yes\nno"),
        ):
            with self.subTest(name=name, value=value):
                self.assert_refused_after_query(*self.execute_setup(
                    properties={name: value},
                ))

    def test_missing_or_malformed_unit_controllers_are_refused(self):
        for controllers in (
            "", "memory pids", "cpu pids", "cpu memory", "cpux memory pids",
        ):
            with self.subTest(controllers=controllers):
                self.assert_refused_after_query(*self.execute_setup(
                    properties={"DelegateControllers": controllers},
                ))

    def test_missing_or_malformed_kernel_controllers_are_refused(self):
        for controllers in (
            "", "memory pids", "cpu pids", "cpu memory", "cpu memory pidsx",
        ):
            with self.subTest(controllers=controllers):
                self.assert_refused_after_query(*self.execute_setup(
                    kernel_controllers=controllers,
                ))

    def test_failed_metadata_or_kernel_queries_are_refused(self):
        for name in ("ActiveState", "ControlGroup", "Delegate",
                     "DelegateControllers"):
            with self.subTest(name=name):
                self.assert_refused_after_query(*self.execute_setup(
                    failed_property=name,
                ))
        self.assert_refused_after_query(*self.execute_setup(
            unreadable_kernel=True,
        ))


class HostObservationTests(unittest.TestCase):
    def test_rea_main_passes_only_the_selected_workload_to_guard(self):
        read_text = Path.read_text

        def host_read(path, *args, **kwargs):
            if path == Path("/proc/meminfo"):
                return meminfo()
            if path == Path("/proc/pressure/memory"):
                return live_sample()["memory.pressure"]
            return read_text(path, *args, **kwargs)

        for mode in ("readiness", "native"):
            with self.subTest(mode=mode):
                record = rea_report(mode)

                def guarded_run(argv, *, evidence_dir, limits, **_kwargs):
                    self.assertEqual(argv, pilot._native_command(
                        "rea-bc-" + mode,
                    ))
                    self.assertEqual(vars(limits), good_guard()["limits"])
                    evidence_dir.mkdir()
                    (evidence_dir / "stdout").write_text(
                        qualified_output().replace(GEOMETRY_SENTINEL, "")
                        + "TRACKTEMPLATE_REA_TRACKWORK=" + json.dumps(record)
                        + "\n",
                    )
                    (evidence_dir / "stderr").write_text(
                        f"Ran {record['tests']} tests in 0.5s\nOK\n",
                    )
                    (evidence_dir / "measurements.jsonl").write_text(
                        json.dumps(live_sample()) + "\n",
                    )
                    return good_guard()

                with tempfile.TemporaryDirectory() as temporary:
                    output = Path(temporary) / "evidence"
                    with (
                        patch.object(pilot, "OUTPUT", output),
                        patch.object(pilot, "_identity", return_value={
                            "source_commit": "1" * 40,
                        }) as identity,
                        patch.dict(pilot.os.environ, {
                            **hosted_environment(),
                            "TRACKTEMPLATE_HOSTED_WORKLOAD": "rea-bc-" + mode,
                        }),
                        patch.object(Path, "read_text", host_read),
                        patch.object(pilot.guard, "run_guarded_flatpak",
                                     side_effect=guarded_run) as guarded,
                        patch.object(pilot, "_clearance", return_value=True),
                        patch.object(pilot, "_deadline_clearance",
                                     return_value=True),
                        contextlib.redirect_stdout(io.StringIO()),
                    ):
                        self.assertEqual(pilot.main(), 0)
                    identity.assert_called_once_with("rea-bc-" + mode)
                    guarded.assert_called_once()
                    summary = json.loads((output / "summary.json").read_text())
                    self.assertEqual(summary["workload"], "rea-bc-" + mode)
                    self.assertEqual(summary["expected_native_tests"],
                                     record["tests"])

    def test_main_requires_fresh_deadline_clearance_for_every_exit(self):
        read_text = Path.read_text

        def host_read(path, *args, **kwargs):
            if path == Path("/proc/meminfo"):
                return meminfo()
            if path == Path("/proc/pressure/memory"):
                return live_sample()["memory.pressure"]
            return read_text(path, *args, **kwargs)

        for cancellation_exit in (0, 5):
            for cleared in (False, True):
                with self.subTest(exit=cancellation_exit, cleared=cleared):
                    result = good_guard()
                    result["deadline_cancellation_exit"] = cancellation_exit
                    result["watchdog"] = DeadlineClearanceTests.watchdog

                    def guarded_run(_argv, *, evidence_dir, **_kwargs):
                        evidence_dir.mkdir()
                        (evidence_dir / "stdout").write_text(
                            qualified_output(),
                        )
                        (evidence_dir / "stderr").write_text(native_report())
                        (evidence_dir / "measurements.jsonl").write_text(
                            json.dumps(live_sample()) + "\n",
                        )
                        return result

                    with tempfile.TemporaryDirectory() as temporary:
                        output = Path(temporary) / "evidence"
                        with (
                            patch.object(pilot, "OUTPUT", output),
                            patch.object(pilot, "_identity", return_value={
                                "source_commit": "1" * 40,
                            }),
                            patch.dict(pilot.os.environ, hosted_environment()),
                            patch.object(Path, "read_text", host_read),
                            patch.object(pilot.guard, "run_guarded_flatpak",
                                         side_effect=guarded_run),
                            patch.object(pilot, "_clearance",
                                         return_value=True),
                            patch.object(pilot, "_deadline_clearance",
                                         return_value=cleared) as clearance,
                            contextlib.redirect_stdout(io.StringIO()),
                        ):
                            exit_code = pilot.main()
                        clearance.assert_called_once_with(result)
                        self.assertEqual(exit_code, 0 if cleared else 1)
                        summary = json.loads(
                            (output / "summary.json").read_text(),
                        )
                        self.assertEqual(summary["status"],
                                         "PASS" if cleared else "FAIL")
                        if not cleared:
                            self.assertEqual(summary["classification"],
                                             "CLEANUP_FAILURE")

    def test_observation_write_failure_cannot_interrupt_guard_cleanup(self):
        read_text = Path.read_text
        path_open = Path.open
        cleanup = {"entered": False, "completed": False}

        def host_read(path, *args, **kwargs):
            if path == Path("/proc/meminfo"):
                return meminfo()
            if path == Path("/proc/pressure/memory"):
                return live_sample()["memory.pressure"]
            return read_text(path, *args, **kwargs)

        def evidence_open(path, *args, **kwargs):
            if path.name == "host.jsonl" and cleanup["entered"]:
                raise OSError("injected host telemetry write failure")
            return path_open(path, *args, **kwargs)

        def simulated_guard(_argv, *, evidence_dir, context, **_kwargs):
            evidence_dir.mkdir()
            (evidence_dir / "stdout").write_text(qualified_output())
            (evidence_dir / "stderr").write_text(native_report())
            (evidence_dir / "measurements.jsonl").write_text(
                json.dumps(live_sample()) + "\n",
            )
            cleanup["entered"] = True
            context.sleep(0)
            cleanup["completed"] = True
            return good_guard()

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            with (
                patch.object(pilot, "OUTPUT", output),
                patch.object(
                    pilot, "_identity", return_value={
                        "source_commit": "1" * 40,
                    },
                ),
                patch.dict(pilot.os.environ, hosted_environment()),
                patch.object(Path, "read_text", host_read),
                patch.object(Path, "open", evidence_open),
                patch.object(
                    pilot.guard, "run_guarded_flatpak",
                    side_effect=simulated_guard,
                ) as guarded,
                patch.object(pilot, "_clearance", return_value=True),
                patch.object(pilot, "_deadline_clearance", return_value=True,
                             create=True),
                patch.object(pilot.time, "sleep"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                status = pilot.main()
            self.assertEqual(status, 1)
            guarded.assert_called_once()
            self.assertTrue(cleanup["completed"])
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["classification"], "EVIDENCE_INCOMPLETE")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Hosted native geometry offline validation passed")
