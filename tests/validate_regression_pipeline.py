#!/usr/bin/env python3
"""Validate the durable local regression-pipeline contract."""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


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
            memory_max_mib=4096,
            timeout_seconds=120,
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
        memory_max_mib=4096,
        timeout_seconds=120,
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
    assert all(step.freecad_limits == (4096, 120)
               for step in gui_steps[4:7])
    assert dict(gui_steps[-1].environment) == {
        "TRACKTEMPLATE_VALIDATION_MEMORY_MAX_MIB": "4096",
        "TRACKTEMPLATE_VALIDATION_TIMEOUT_SECONDS": "120",
    }
    for profile in ("transition", "transition-gui"):
        try:
            pipeline.build_steps(profile)
        except ValueError as error:
            assert "explicit" in str(error)
        else:
            raise AssertionError("Full proof accepted implicit limits")


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


def _validate_resource_failure_cannot_pass():
    with tempfile.TemporaryDirectory(prefix="tt-pipeline-resource-") as name:
        root = pathlib.Path(name)
        stdout = root / "payload.stdout"
        stderr = root / "payload.stderr"
        stdout.write_text("PROOF_PASS\n", encoding="utf-8")
        stderr.write_text("original diagnostic\n", encoding="utf-8")
        receipt = root / "receipt.json"
        receipt.write_text("{}", encoding="utf-8")
        step = pipeline.PipelineStep(
            "native", ("flatpak", "run", "org.freecad.FreeCAD"),
            "PROOF_PASS", freecad_limits=(4096, 120),
        )
        for index, (status, cleanup) in enumerate((
            ("failed", True), ("completed", False),
        )):
            calls = []

            def guarded_run(argv, **kwargs):
                calls.append((argv, kwargs))
                return {
                    "status": status, "process_exit": 0,
                    "cleanup_proved": cleanup,
                    "stdout_path": str(stdout), "stderr_path": str(stderr),
                    "receipt_path": str(receipt),
                }

            fake = SimpleNamespace(
                ValidationLimits=lambda **values: values,
                run_guarded_flatpak=guarded_run,
            )
            with (
                patch.object(pipeline, "_guard_module", return_value=fake),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                summary = pipeline.run_pipeline(
                    profile="transition", steps=(step,), root=root,
                    run_directory=root / str(index),
                    local_owner_exception="fixture-only-mocked-resource-test",
                )
            assert summary["failed"] == ["native"]
            assert summary["results"][0]["sentinel_found"] is True
            assert summary["results"][0]["return_code"] != 0
            assert len(calls) == 1
            assert calls[0][0] == step.command
            assert calls[0][1]["isolate_profile"] is True


def validate():
    _validate_profiles()
    _validate_execution_and_logs()
    _validate_canonical_routing()
    _validate_resource_failure_cannot_pass()
    print("Programmatic regression pipeline contract passed")


if __name__ == "__main__":
    validate()
