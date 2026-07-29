#!/usr/bin/env python3
"""Run durable regression layers with concise output and retained raw logs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SENTINEL = "TRACKTEMPLATE_REGRESSION_PIPELINE="
PROFILES = (
    "standalone",
    "transition",
    "transition-gui",
)


@dataclass(frozen=True)
class PipelineStep:
    """Describe one ordered command and its required success sentinel."""

    name: str
    command: tuple[str, ...]
    sentinel: str


def build_steps(
    profile,
    *,
    root=ROOT,
    python_executable=sys.executable,
):
    """Return the ordered durable regression steps for ``profile``."""
    if profile not in PROFILES:
        raise ValueError("unknown regression profile: {!r}".format(profile))

    root = pathlib.Path(root).resolve()
    steps = [
        PipelineStep(
            "python-syntax",
            (
                str(python_executable),
                str(root / "tools" / "validate_python_syntax.py"),
            ),
            "Tracked Python and FCMacro parsing passed",
        ),
        PipelineStep(
            "standalone-contracts",
            (
                str(python_executable),
                str(root / "tools" / "run_standalone_validators.py"),
                "--profile",
                "ci",
            ),
            "TRACKTEMPLATE_STANDALONE_VALIDATION=",
        ),
    ]

    if profile in ("transition", "transition-gui"):
        freecad_prefix = (
            "flatpak",
            "run",
            "--command=FreeCADCmd",
            "org.freecad.FreeCAD",
        )
        steps.extend(
            (
                PipelineStep(
                    "transition-persistence",
                    freecad_prefix
                    + (
                        str(
                            root
                            / "tests"
                            / (
                                "freecad_validate_phase4_"
                                "transition_persistence.py"
                            )
                        ),
                    ),
                    (
                        "Phase 4 transition FreeCAD persistence "
                        "validation passed"
                    ),
                ),
                PipelineStep(
                    "transition-coin-scene",
                    freecad_prefix
                    + (
                        str(
                            root
                            / "tests"
                            / "freecad_validate_phase5_transition_coin_scene.py"
                        ),
                    ),
                    "Phase 5 transition Coin host validation passed",
                ),
                PipelineStep(
                    "transition-edit-lifecycle",
                    freecad_prefix
                    + (
                        str(
                            root
                            / "tests"
                            / "freecad_validate_phase5_transition_edit.py"
                        ),
                    ),
                    "Phase 5 transition edit FreeCAD validation passed",
                ),
            )
        )

    if profile == "transition-gui":
        steps.append(
            PipelineStep(
                "transition-viewprovider-gui",
                (
                    str(
                        root
                        / "tools"
                        / "freecad_bridge"
                        / "run-phase5-transition-viewprovider"
                    ),
                ),
                "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=",
            )
        )

    return tuple(steps)


def default_run_directory(root=ROOT):
    """Return a new ignored log-directory path for one pipeline run."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (
        pathlib.Path(root)
        / "benchmark-output"
        / "validation-pipeline"
        / stamp
    )


def _display_path(path, root):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _log_contains(path, sentinel):
    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as stream:
        return any(sentinel in line for line in stream)


def _validate_steps(steps):
    names = []
    for step in steps:
        if not isinstance(step, PipelineStep):
            raise TypeError("every pipeline step must be a PipelineStep")
        if (
            not step.name
            or not step.command
            or not step.sentinel
        ):
            raise ValueError("pipeline steps require a name, command and sentinel")
        if any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
            for character in step.name
        ):
            raise ValueError(
                "pipeline step names must be lowercase ASCII slugs"
            )
        names.append(step.name)
    if len(names) != len(set(names)):
        raise ValueError("pipeline step names must be unique")


def run_pipeline(
    *,
    profile,
    steps,
    root,
    run_directory,
):
    """Run ordered steps, stopping after a failed prerequisite."""
    if profile not in PROFILES:
        raise ValueError("unknown regression profile: {!r}".format(profile))

    steps = tuple(steps)
    _validate_steps(steps)
    root = pathlib.Path(root).resolve()
    run_directory = pathlib.Path(run_directory)
    if not run_directory.is_absolute():
        run_directory = root / run_directory
    run_directory = run_directory.resolve()
    if run_directory == root:
        raise ValueError("the repository root cannot be a pipeline log directory")
    run_directory.mkdir(parents=True, exist_ok=False)

    results = []
    failed = []
    skipped = []

    for index, step in enumerate(steps, start=1):
        print(
            "[{}/{}] Running {}...".format(
                index,
                len(steps),
                step.name,
            ),
            flush=True,
        )
        log_path = run_directory / "{:02d}-{}.log".format(
            index,
            step.name,
        )
        return_code = 127
        command_started = False
        with log_path.open("w", encoding="utf-8") as log:
            log.write(
                "TRACKTEMPLATE_PIPELINE_COMMAND="
                + json.dumps(step.command)
                + "\n"
            )
            log.flush()
            try:
                completed = subprocess.run(
                    step.command,
                    cwd=root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                command_started = True
                return_code = completed.returncode
            except OSError as error:
                log.write(
                    "TRACKTEMPLATE_PIPELINE_START_ERROR="
                    + repr(error)
                    + "\n"
                )

        sentinel_found = _log_contains(log_path, step.sentinel)
        if not command_started:
            failure_reason = "command-not-started"
        elif return_code:
            failure_reason = "nonzero-exit"
        elif not sentinel_found:
            failure_reason = "missing-success-sentinel"
        else:
            failure_reason = None

        result = {
            "failure_reason": failure_reason,
            "log": _display_path(log_path, root),
            "name": step.name,
            "return_code": return_code,
            "sentinel_found": sentinel_found,
            "status": "passed" if failure_reason is None else "failed",
        }
        results.append(result)
        if failure_reason is None:
            print(
                "PASS {} (log: {})".format(
                    step.name,
                    result["log"],
                ),
                flush=True,
            )
            continue

        failed.append(step.name)
        skipped.extend(
            remaining.name
            for remaining in steps[index:]
        )
        print(
            "FAIL {} [{}] (log: {})".format(
                step.name,
                failure_reason,
                result["log"],
            ),
            flush=True,
        )
        break

    passed = [
        result["name"]
        for result in results
        if result["status"] == "passed"
    ]
    summary = {
        "completed_count": len(results),
        "failed": failed,
        "log_directory": _display_path(run_directory, root),
        "passed": passed,
        "profile": profile,
        "requested_count": len(steps),
        "results": results,
        "skipped": skipped,
    }
    print(
        SENTINEL
        + json.dumps(
            summary,
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="standalone",
        help=(
            "standalone is the default; transition adds qualified headless "
            "FreeCAD; transition-gui also runs the isolated real-GUI proof"
        ),
    )
    arguments = parser.parse_args(argv)
    summary = run_pipeline(
        profile=arguments.profile,
        steps=build_steps(arguments.profile),
        root=ROOT,
        run_directory=default_run_directory(),
    )
    return int(bool(summary["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
