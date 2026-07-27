#!/usr/bin/env python3
"""Run every standalone validator under an explicit evidence profile."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SENTINEL = "TRACKTEMPLATE_STANDALONE_VALIDATION="
PROFILES = ("ci", "local")
RECOVERY_VALIDATOR = "validate_recovery_controls.py"


def discover_validators(root=ROOT):
    """Return the complete deterministic standalone-validator list."""
    return sorted((root / "tests").glob("validate_*.py"))


def validator_command(path, profile, python_executable=sys.executable):
    """Build one validator command for the selected evidence profile."""
    command = [python_executable, str(path)]
    if profile == "local" and path.name == RECOVERY_VALIDATOR:
        command.append("--live-workstation")
    return command


def run_validators(
    *,
    root,
    validators,
    profile,
    python_executable=sys.executable,
):
    """Run every validator, preserving raw output and collecting all failures."""
    results = []
    for path in validators:
        relative_path = path.relative_to(root).as_posix()
        print(
            "TRACKTEMPLATE_VALIDATOR_START="
            + json.dumps({"path": relative_path}, sort_keys=True),
            flush=True,
        )
        completed = subprocess.run(
            validator_command(path, profile, python_executable),
            cwd=root,
            check=False,
        )
        result = {
            "exit_code": completed.returncode,
            "path": relative_path,
            "status": "passed" if completed.returncode == 0 else "failed",
        }
        results.append(result)
        print(
            "TRACKTEMPLATE_VALIDATOR_RESULT="
            + json.dumps(result, sort_keys=True),
            flush=True,
        )
    return results


def build_summary(profile, results):
    """Return the stable machine-readable result summary."""
    failed = [result["path"] for result in results if result["exit_code"]]
    return {
        "failed": failed,
        "failed_count": len(failed),
        "passed_count": len(results) - len(failed),
        "profile": profile,
        "total_count": len(results),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        required=True,
        help=(
            "'ci' runs clean-checkout contracts; 'local' additionally requires "
            "the workstation-only recovery evidence"
        ),
    )
    arguments = parser.parse_args(argv)

    validators = discover_validators()
    if not validators:
        parser.error("no tests/validate_*.py validators were found")

    results = run_validators(
        root=ROOT,
        validators=validators,
        profile=arguments.profile,
    )
    summary = build_summary(arguments.profile, results)
    print(
        SENTINEL + json.dumps(summary, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return int(bool(summary["failed_count"]))


if __name__ == "__main__":
    raise SystemExit(main())
