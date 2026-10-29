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
        self.assertEqual(self.assess()["status"], "PASS")

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
    def test_validator_and_guard_match_retained_hashes(self):
        expected = {
            "tests/freecad_validate_phase6_transition_exact_geometry.py": (
                "e9df630ef1a33a20b52b0bd961dd4255e9e23ad8344f8832718a095baee7cf51"
            ),
            "tools/freecad_validation_guard.py": (
                "b193209f0f21f28c3c17f9c52e509e31dccb32690152c02414769c0f6e49c559"
            ),
        }
        self.assertEqual(pilot.TEST_SHA256, expected[pilot.TEST_PATH])
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

        self.assertEqual(top_block("on"), ["workflow_dispatch:"])
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


class HostObservationTests(unittest.TestCase):
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
