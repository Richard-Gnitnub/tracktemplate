#!/usr/bin/env python3
"""Validate the durable local regression-pipeline contract."""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_regression_pipeline as pipeline  # noqa: E402


def _write_program(path, *lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _step_names(profile):
    return tuple(
        step.name
        for step in pipeline.build_steps(
            profile,
            root=ROOT,
            python_executable="python-under-test",
        )
    )


def _validate_profiles():
    standalone = (
        "validation-preflight-and-ruff",
        "python-syntax",
        "standalone-contracts",
    )
    transition = standalone + (
        "freecad-preflight",
        "transition-persistence",
        "transition-coin-scene",
        "transition-edit-lifecycle",
    )
    assert pipeline.PROFILES == (
        "standalone",
        "transition",
        "transition-gui",
    )
    assert _step_names("standalone") == standalone
    assert _step_names("transition") == transition
    assert _step_names("transition-gui") == transition + (
        "freecad-gui-preflight",
        "transition-viewprovider-gui",
    )

    gui_steps = pipeline.build_steps(
        "transition-gui",
        root=ROOT,
        python_executable="python-under-test",
    )
    assert gui_steps[0].command == (
        "python-under-test",
        str(ROOT / "tools" / "development_toolchain_preflight.py"),
        "--stage",
        "validation",
        "--run-ruff",
    )
    assert gui_steps[1].command == (
        "python-under-test",
        str(ROOT / "tools" / "validate_python_syntax.py"),
    )
    assert gui_steps[2].command[-2:] == ("--profile", "ci")
    assert gui_steps[3].command[-2:] == ("--stage", "freecad")
    assert gui_steps[-2].command[-2:] == ("--stage", "freecad-gui")
    assert gui_steps[-1].command == (
        str(
            ROOT
            / "tools"
            / "freecad_bridge"
            / "run-phase5-transition-viewprovider"
        ),
    )


def _validate_execution_and_logs():
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-regression-pipeline-"
    ) as temporary:
        root = pathlib.Path(temporary)
        programs = root / "programs"
        programs.mkdir()
        success = programs / "success.py"
        failure = programs / "failure.py"
        never = programs / "never.py"
        missing_sentinel = programs / "missing_sentinel.py"
        never_marker = root / "never.marker"

        _write_program(success, "print('STEP_SUCCESS')")
        _write_program(
            failure,
            "print('raw failure detail')",
            "raise SystemExit(7)",
        )
        _write_program(
            never,
            "import pathlib",
            f"pathlib.Path({str(never_marker)!r}).write_text('ran')",
            "print('NEVER_SUCCESS')",
        )
        _write_program(missing_sentinel, "print('wrong success text')")

        steps = (
            pipeline.PipelineStep(
                "first",
                (sys.executable, str(success)),
                "STEP_SUCCESS",
            ),
            pipeline.PipelineStep(
                "failure",
                (sys.executable, str(failure)),
                "FAILURE_SUCCESS",
            ),
            pipeline.PipelineStep(
                "never",
                (sys.executable, str(never)),
                "NEVER_SUCCESS",
            ),
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            summary = pipeline.run_pipeline(
                profile="standalone",
                steps=steps,
                root=root,
                run_directory=root / "logs",
            )

        assert summary["passed"] == ["first"]
        assert summary["failed"] == ["failure"]
        assert summary["skipped"] == ["never"]
        assert summary["completed_count"] == 2
        assert summary["requested_count"] == 3
        assert never_marker.exists() is False
        assert "raw failure detail" not in captured.getvalue()
        assert pipeline.SENTINEL in captured.getvalue()
        failure_result = summary["results"][1]
        assert failure_result["return_code"] == 7
        assert failure_result["sentinel_found"] is False
        failure_log = root / failure_result["log"]
        assert "raw failure detail" in failure_log.read_text(
            encoding="utf-8"
        )

        missing_output = io.StringIO()
        with contextlib.redirect_stdout(missing_output):
            missing_summary = pipeline.run_pipeline(
                profile="standalone",
                steps=(
                    pipeline.PipelineStep(
                        "missing-sentinel",
                        (sys.executable, str(missing_sentinel)),
                        "EXPECTED_SUCCESS",
                    ),
                ),
                root=root,
                run_directory=root / "missing-logs",
            )
        assert missing_summary["failed"] == ["missing-sentinel"]
        assert missing_summary["results"][0]["return_code"] == 0
        assert (
            missing_summary["results"][0]["failure_reason"]
            == "missing-success-sentinel"
        )
        assert pipeline.SENTINEL in missing_output.getvalue()


def _validate_canonical_routing():
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(
        encoding="utf-8"
    )
    testing_policy = (
        ROOT / "reference" / "TESTING_POLICY.md"
    ).read_text(encoding="utf-8")
    workflow = (
        ROOT / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")

    assert (
        "tools/run_regression_pipeline.py --profile transition-gui"
        in validation
    )
    assert "## Programmatic regression lifecycle" in testing_policy
    assert "run-phase5-transition-viewprovider" not in workflow
    assert "--profile transition-gui" not in workflow


def validate():
    _validate_profiles()
    _validate_execution_and_logs()
    _validate_canonical_routing()
    print("Programmatic regression pipeline contract passed")


if __name__ == "__main__":
    validate()
