#!/usr/bin/env python3
"""Validate complete-run and evidence-profile behaviour of the CI runner."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_standalone_validators as runner  # noqa: E402


def _write_validator(path, marker_name, exit_code, output_statement):
    path.write_text(
        "\n".join(
            (
                "import pathlib",
                "import sys",
                output_statement,
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
            (
                "sys.stdout.write('failure-start\\n' + "
                "('x' * 12000) + '\\nfailure-end\\n'); "
                "sys.stderr.write('failure-stderr\\n')"
            ),
        )
        _write_validator(
            tests_root / "validate_b_success.py",
            "success.marker",
            0,
            "sys.stdout.write('success-noise-' + ('y' * 12000) + '\\n')",
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
        captured_errors = io.StringIO()
        log_directory = fixture_root / "retained-output"
        with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(
            captured_errors
        ):
            results = runner.run_validators(
                root=fixture_root,
                validators=validators,
                profile="ci",
                log_directory=log_directory,
                python_executable=sys.executable,
            )
        if not (fixture_root / "failure.marker").is_file():
            raise AssertionError("failing validator did not run")
        if not (fixture_root / "success.marker").is_file():
            raise AssertionError("runner stopped after the first failure")
        if captured_output.getvalue():
            raise AssertionError("successful validator output reached stdout")
        failure_output = captured_errors.getvalue()
        if failure_output.count("TRACKTEMPLATE_VALIDATOR_FAILURE=") != 1:
            raise AssertionError("runner did not emit one bounded failure record")
        if "failure-start" not in failure_output or "failure-end" not in failure_output:
            raise AssertionError("bounded failure detail lost the head or tail")
        if "success-noise" in failure_output:
            raise AssertionError("successful validator output reached stderr")
        if len(failure_output.encode("utf-8")) > (
            runner.FAILURE_EXCERPT_BYTES + 2048
        ):
            raise AssertionError("failure detail exceeded its bounded allowance")

        by_path = {result["path"]: result for result in results}
        failure = by_path["tests/validate_a_failure.py"]
        success = by_path["tests/validate_b_success.py"]
        for result in (failure, success):
            if result["command"][0] != sys.executable:
                raise AssertionError("retained validator command is incorrect")
            log_path = fixture_root / result["log"]
            raw_output = log_path.read_bytes()
            if result["output_bytes"] != len(raw_output):
                raise AssertionError("retained output byte count is incorrect")
            if result["output_sha256"] != hashlib.sha256(raw_output).hexdigest():
                raise AssertionError("retained output identity is incorrect")
        failure_log = (fixture_root / failure["log"]).read_text(
            encoding="utf-8"
        )
        if not all(
            value in failure_log
            for value in ("failure-start", "failure-end", "failure-stderr")
        ):
            raise AssertionError("failing validator output was not retained")
        success_log = (fixture_root / success["log"]).read_text(
            encoding="utf-8"
        )
        if "success-noise" not in success_log:
            raise AssertionError("successful validator output was not retained")

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

        manifest_path = runner.write_manifest(
            root=fixture_root,
            log_directory=log_directory,
            profile="ci",
            results=results,
            summary=summary,
        )
        manifest = json.loads((fixture_root / manifest_path).read_text())
        if manifest["summary"] != expected or manifest["results"] != results:
            raise AssertionError("retained manifest does not index the full run")

        try:
            runner.run_validators(
                root=fixture_root,
                validators=(),
                profile="ci",
                log_directory=fixture_root,
                python_executable=sys.executable,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("runner accepted the repository root as a log")

    print("Standalone validation runner contract passed")


if __name__ == "__main__":
    validate()
