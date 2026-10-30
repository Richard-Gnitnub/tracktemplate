#!/usr/bin/env python3
"""Check local validation admission without starting FreeCAD."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_regression_pipeline as pipeline  # noqa: E402


REFERENCE = "owner-decision:fixture-only-not-execution-authority"
EXCEPTION_ENV = "TRACKTEMPLATE_LOCAL_VALIDATION_EXCEPTION"


class ExecutionLocationTests(unittest.TestCase):
    def test_heavy_profiles_refuse_before_executor_or_log_creation(self):
        for profile in ("transition", "transition-gui"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory(
                prefix="tt-location-refusal-"
            ) as temporary:
                root = Path(temporary)
                output = root / "must-not-exist"
                step = pipeline.PipelineStep(
                    "mock-native", ("must-not-execute",), "MOCK_PASS"
                )
                with (
                    patch.object(pipeline, "_run_step", return_value=0) as run,
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    try:
                        pipeline.run_pipeline(
                            profile=profile, steps=(step,), root=root,
                            run_directory=output,
                        )
                    except ValueError as error:
                        self.assertIn("GitHub-hosted", str(error))
                run.assert_not_called()
                self.assertFalse(output.exists())

    def test_native_step_cannot_hide_in_standalone_profile(self):
        with tempfile.TemporaryDirectory(prefix="tt-location-step-") as name:
            root = Path(name)
            step = pipeline.PipelineStep(
                "native", ("must-not-execute",), "MOCK_PASS",
                freecad_limits=(4096, 120),
            )
            with (
                patch.object(pipeline, "_run_step", return_value=0) as run,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                try:
                    pipeline.run_pipeline(
                        profile="standalone", steps=(step,), root=root,
                        run_directory=root / "must-not-exist",
                    )
                except ValueError as error:
                    self.assertIn("GitHub-hosted", str(error))
            run.assert_not_called()
            self.assertFalse((root / "must-not-exist").exists())

    def test_hosted_environment_is_not_scope_approval(self):
        with patch.dict(os.environ, {
            "CI": "true", "GITHUB_ACTIONS": "true",
            "RUNNER_ENVIRONMENT": "github-hosted",
            EXCEPTION_ENV: REFERENCE,
        }):
            self.test_heavy_profiles_refuse_before_executor_or_log_creation()

    def test_invalid_exception_references_are_rejected(self):
        policy = importlib.import_module("tools.validation_execution_policy")
        for reference in (
            None, "", " ", " decision", "decision ", "x\ny", "x\ty",
            "x\x00y", "x" * 513, True, 1,
        ):
            with self.subTest(reference=repr(reference)):
                with self.assertRaises(ValueError):
                    policy.require_local_exception("transition", reference)

    def test_exception_receipt_does_not_claim_authenticated_authority(self):
        policy = importlib.import_module("tools.validation_execution_policy")
        receipt = policy.require_local_exception("transition", REFERENCE)
        self.assertEqual(receipt["owner_exception_reference"], REFERENCE)
        self.assertEqual(receipt["workload"], "transition")
        self.assertIs(receipt["owner_authority_authenticated"], False)

    def test_standalone_does_not_need_exception(self):
        with tempfile.TemporaryDirectory(prefix="tt-location-light-") as name:
            root = Path(name)
            with (
                patch.object(pipeline, "_run_step", return_value=0) as run,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                summary = pipeline.run_pipeline(
                    profile="standalone", steps=(), root=root,
                    run_directory=root / "logs",
                )
            self.assertEqual(summary["failed"], [])
            run.assert_not_called()

    def test_exception_reaches_original_guard_with_original_limits(self):
        with tempfile.TemporaryDirectory(prefix="tt-location-admission-") as name:
            root = Path(name)
            step = pipeline.PipelineStep(
                "native", ("never-executed",), "MOCK_PASS",
                freecad_limits=(4096, 120),
            )

            def run(accepted, accepted_root, log, evidence, **kwargs):
                self.assertIs(accepted, step)
                self.assertEqual(accepted.freecad_limits, (4096, 120))
                self.assertEqual(kwargs["local_owner_exception"], REFERENCE)
                log.write("MOCK_PASS\n")
                return 0

            with (
                patch.object(pipeline, "_run_step", side_effect=run) as executed,
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                summary = pipeline.run_pipeline(
                    profile="transition", steps=(step,), root=root,
                    run_directory=root / "logs",
                    local_owner_exception=REFERENCE,
                )
            executed.assert_called_once()
            self.assertEqual(summary["failed"], [])
            self.assertEqual(summary["local_owner_exception"][
                "owner_exception_reference"
            ], REFERENCE)
            self.assertIn(REFERENCE, output.getvalue())

    def test_pipeline_cli_refuses_before_running(self):
        with (
            patch.object(pipeline, "run_pipeline") as run,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as stopped,
        ):
            pipeline.main([
                "--profile", "transition", "--memory-max-mib", "4096",
                "--timeout-seconds", "120",
            ])
        self.assertEqual(stopped.exception.code, 2)
        run.assert_not_called()

    def test_pipeline_transports_exception_and_limits_to_bridge(self):
        step = pipeline.PipelineStep(
            "gui", ("must-not-execute",), "MOCK_PASS",
            environment=(
                ("TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB", "4096"),
                ("TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS", "120"),
            ),
        )
        with patch.object(pipeline.subprocess, "run") as run:
            run.return_value.returncode = 7
            result = pipeline._run_step(
                step, ROOT, io.StringIO(), ROOT / "never-created",
                local_owner_exception=REFERENCE,
            )
        self.assertEqual(result, 7)
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment[EXCEPTION_ENV], REFERENCE)
        self.assertEqual(environment[
            "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB"
        ], "4096")
        self.assertEqual(environment[
            "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS"
        ], "120")

    def _bridge_fixture(self, root, entry):
        bridge = root / "tools" / "freecad_bridge"
        bridge.mkdir(parents=True)
        shutil.copy2(ROOT / "tools" / "freecad_bridge" / entry, bridge / entry)
        policy = ROOT / "tools" / "validation_execution_policy.py"
        if policy.exists():
            shutil.copy2(policy, root / "tools" / policy.name)
        python = root / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        marker = root / "guard-command.json"
        python.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, subprocess, sys\n"
            "if pathlib.Path(sys.argv[1]).name == "
            "'validation_execution_policy.py':\n"
            "    raise SystemExit(subprocess.run([sys.executable, "
            "*sys.argv[1:]], check=False).returncode)\n"
            f"pathlib.Path({str(marker)!r}).write_text(json.dumps({{\n"
            "    'argv': sys.argv[1:],\n"
            "    'exception': os.environ.get("
            "'TRACKTEMPLATE_LOCAL_VALIDATION_EXCEPTION'),\n"
            "    'memory': os.environ.get("
            "'TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB'),\n"
            "    'time': os.environ.get("
            "'TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS'),\n"
            "}))\n"
            "raise SystemExit(91)\n",
            encoding="utf-8",
        )
        python.chmod(0o700)
        return bridge / entry, marker

    def test_bridge_refuses_before_guard_and_output_mutation(self):
        for entry in ("run-isolated", "launch-freecad"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory(
                prefix="tt-location-bridge-deny-"
            ) as name:
                root = Path(name)
                command, marker = self._bridge_fixture(root, entry)
                result = subprocess.run(
                    [str(command), "must-not-execute"],
                    env={"PATH": os.defpath, "GITHUB_ACTIONS": "true",
                         "RUNNER_ENVIRONMENT": "github-hosted"},
                    capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("GitHub-hosted", result.stderr)
                self.assertFalse(marker.exists())
                self.assertFalse((root / "benchmark-output").exists())

    def test_bridge_exception_retains_original_guard_and_limits(self):
        for entry in ("run-isolated", "launch-freecad"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory(
                prefix="tt-location-bridge-allow-"
            ) as name:
                root = Path(name)
                command, marker = self._bridge_fixture(root, entry)
                result = subprocess.run(
                    [str(command), "must-not-execute"],
                    env={"PATH": os.defpath, EXCEPTION_ENV: REFERENCE,
                         "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB": "4096",
                         "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS": "120"},
                    capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(result.returncode, 91, result.stderr)
                record = json.loads(marker.read_text(encoding="utf-8"))
                self.assertEqual(Path(record["argv"][0]).name,
                                 "freecad_validation_guard.py")
                self.assertEqual(record["argv"][1:], [
                    "reserve-gui", str(command), "must-not-execute"
                ])
                self.assertEqual(record["exception"], REFERENCE)
                self.assertEqual((record["memory"], record["time"]),
                                 ("4096", "120"))
                self.assertIn(REFERENCE, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
