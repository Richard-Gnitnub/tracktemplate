#!/usr/bin/env python3
"""Validate complete-run and evidence-profile behaviour of the CI runner."""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_standalone_validators as runner  # noqa: E402


def _write_validator(path, marker_name, exit_code):
    path.write_text(
        "\n".join(
            (
                "import pathlib",
                f"pathlib.Path({marker_name!r}).write_text(",
                "    'ran\\n', encoding='utf-8'",
                ")",
                f"raise SystemExit({exit_code})",
                "",
            )
        ),
        encoding="utf-8",
    )


def validate():
    recovery = pathlib.Path("tests") / runner.RECOVERY_VALIDATOR
    local_command = runner.validator_command(
        recovery,
        "local",
        python_executable="python-under-test",
    )
    ci_command = runner.validator_command(
        recovery,
        "ci",
        python_executable="python-under-test",
    )
    if local_command[-1] != "--live-workstation":
        raise AssertionError("local profile lost workstation recovery evidence")
    if "--live-workstation" in ci_command:
        raise AssertionError("CI profile incorrectly requires local-only evidence")

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-standalone-runner-"
    ) as temporary:
        fixture_root = pathlib.Path(temporary)
        tests_root = fixture_root / "tests"
        tests_root.mkdir()
        _write_validator(
            tests_root / "validate_a_failure.py",
            "failure.marker",
            3,
        )
        _write_validator(
            tests_root / "validate_b_success.py",
            "success.marker",
            0,
        )
        (tests_root / "not_a_validator.py").write_text(
            "raise AssertionError('must not run')\n",
            encoding="utf-8",
        )

        validators = runner.discover_validators(fixture_root)
        if [path.name for path in validators] != [
            "validate_a_failure.py",
            "validate_b_success.py",
        ]:
            raise AssertionError("validator discovery is incomplete or unordered")

        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            results = runner.run_validators(
                root=fixture_root,
                validators=validators,
                profile="ci",
                python_executable=sys.executable,
            )
        if not (fixture_root / "failure.marker").is_file():
            raise AssertionError("failing validator did not run")
        if not (fixture_root / "success.marker").is_file():
            raise AssertionError("runner stopped after the first failure")
        if captured_output.getvalue().count(
            "TRACKTEMPLATE_VALIDATOR_RESULT="
        ) != 2:
            raise AssertionError("runner did not emit one result per validator")

        summary = runner.build_summary("ci", results)
        expected = {
            "failed": ["tests/validate_a_failure.py"],
            "failed_count": 1,
            "passed_count": 1,
            "profile": "ci",
            "total_count": 2,
        }
        if summary != expected:
            raise AssertionError(
                "standalone summary drifted: {!r}".format(summary)
            )

    print("Standalone validation runner contract passed")


if __name__ == "__main__":
    validate()
