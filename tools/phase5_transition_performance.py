#!/usr/bin/env python3
"""Profile the bounded Phase 5 Coin candidate in isolated FreeCAD GUIs."""

import argparse
import datetime
import json
import os
import pathlib
import platform
import statistics
import subprocess
import sys
import time


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase5-transition-performance-runs"
)
SAMPLE_PROFILE_ID = "phase5-transition-coin-performance-sample-v1"
PROFILE_ID = "phase5-transition-coin-performance-baseline-v1"
QUALIFIED_PROFILE_ID = "linux-x86_64-flatpak-freecad-1.1.1"
SAMPLE_SENTINEL = "TRACKTEMPLATE_PHASE5_COIN_PERFORMANCE_SAMPLE="
PROFILE_SENTINEL = "TRACKTEMPLATE_PHASE5_COIN_PERFORMANCE="
DEFAULT_REPETITIONS = 3
FIXTURE_OBJECT_COUNT = 8
PREVIEW_SEGMENT_COUNT = 32
WARM_MEASUREMENT_COUNT = 3
COLD_BOUNDARY = (
    "prepared analysed canonical states and an empty FreeCAD document through "
    "atomic object creation, empty-cache preview construction, Coin "
    "ViewProvider attachment, one explicit document recompute and first redraw"
)
WARM_BOUNDARY = (
    "unchanged canonical states and current preview caches through "
    "ViewProvider refresh and GUI event processing, after one unmeasured "
    "same-process warm-up"
)

sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge.orchestration import sha256  # noqa: E402


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _require_number(record, field, boundary):
    value = record.get(field)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise RuntimeError(
            "{} measurement lacks numeric {}.".format(boundary, field)
        )
    return value


def _metric_summary(values):
    values = list(values)
    if not values:
        raise ValueError("A metric summary requires at least one value.")
    return {
        "maximum": max(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "values": values,
    }


def _validate_sample(sample):
    _require(isinstance(sample, dict), "Performance sample must be an object.")
    _require(
        sample.get("schema_version") == 1
        and sample.get("profile_id") == SAMPLE_PROFILE_ID
        and sample.get("status") == "completed",
        "Performance sample did not complete the v1 contract.",
    )
    _require(
        sample.get("freecad_version") == "1.1.1",
        "Performance sample did not use the qualified FreeCAD version.",
    )
    _require(
        sample.get("qualified_profile_id") == QUALIFIED_PROFILE_ID,
        "Performance sample did not use the qualified runtime profile.",
    )
    fixture = sample.get("fixture", {})
    _require(
        fixture
        == {
            "logical_object_count": FIXTURE_OBJECT_COUNT,
            "preview_segment_count": PREVIEW_SEGMENT_COUNT,
        },
        "Performance sample fixture drifted.",
    )
    _require(
        sample.get("boundary")
        == {"cold": COLD_BOUNDARY, "warm": WARM_BOUNDARY},
        "Performance sample boundary drifted.",
    )

    cold = sample.get("cold", {})
    for field in (
        "process_cpu_ms",
        "recompute_wall_ms",
        "rss_after_mb",
        "rss_before_mb",
        "rss_delta_mb",
        "wall_ms",
    ):
        _require_number(cold, field, "Cold")
    _require(
        cold.get("document_object_count_before") == 0
        and cold.get("document_object_count_after")
        == FIXTURE_OBJECT_COUNT
        and cold.get("document_object_delta") == FIXTURE_OBJECT_COUNT,
        "Cold document-object accounting drifted.",
    )
    _require(
        cold.get("cache_missing_count_before") == FIXTURE_OBJECT_COUNT
        and cold.get("cache_current_count") == FIXTURE_OBJECT_COUNT,
        "Cold cache accounting drifted.",
    )
    _require(
        cold.get("recompute_count") == 1,
        "Cold boundary must contain one explicit recompute.",
    )
    _require(
        cold.get("part_shape_count") == 0,
        "Cold boundary created a forbidden Part shape.",
    )
    _require(
        cold.get("display_modes_added") == FIXTURE_OBJECT_COUNT
        and cold.get("root_children_added") == 0
        and cold.get("stable_mapping_count") == FIXTURE_OBJECT_COUNT,
        "Cold Coin structure or stable mapping drifted.",
    )

    warm = sample.get("warm", {})
    measurements = warm.get("measurements")
    _require(
        warm.get("measurement_count") == WARM_MEASUREMENT_COUNT
        and isinstance(measurements, list)
        and len(measurements) == WARM_MEASUREMENT_COUNT,
        "Warm measurement count drifted.",
    )
    warm_up = warm.get("warm_up", {})
    _require(
        warm_up.get("cache_reuse_count") == FIXTURE_OBJECT_COUNT
        and warm_up.get("recompute_count") == 0
        and warm_up.get("scene_replacement_count") == 0,
        "Warm-up did not prove unchanged-result reuse.",
    )
    for measurement in measurements:
        for field in (
            "process_cpu_ms",
            "rss_after_mb",
            "rss_before_mb",
            "rss_delta_mb",
            "wall_ms",
        ):
            _require_number(measurement, field, "Warm")
        _require(
            measurement.get("document_object_count_before")
            == FIXTURE_OBJECT_COUNT
            and measurement.get("document_object_count_after")
            == FIXTURE_OBJECT_COUNT
            and measurement.get("document_object_delta") == 0,
            "Warm document-object accounting drifted.",
        )
        _require(
            measurement.get("cache_reuse_count")
            == FIXTURE_OBJECT_COUNT,
            "Warm cache reuse accounting drifted.",
        )
        _require(
            measurement.get("scene_replacement_count") == 0
            and measurement.get("recompute_count") == 0
            and measurement.get("stable_mapping_count")
            == FIXTURE_OBJECT_COUNT,
            "Warm reuse changed the scene, mapping or recompute boundary.",
        )
        _require(
            measurement.get("part_shape_count") == 0,
            "Warm boundary created a forbidden Part shape.",
        )

    cleanup = sample.get("cleanup", {})
    _require(
        cleanup
        == {
            "cache_count_after": 0,
            "document_object_count_after": 0,
            "open_document_count_after": 0,
            "viewprovider_count_after": 0,
        },
        "Performance sample cleanup was incomplete.",
    )
    return sample


def _summarise_samples(samples):
    samples = tuple(_validate_sample(sample) for sample in samples)
    if len(samples) < 3:
        raise ValueError(
            "Phase 5 performance profiling requires at least three "
            "fresh-process samples."
        )
    fixtures = {json.dumps(sample["fixture"], sort_keys=True) for sample in samples}
    boundaries = {
        json.dumps(sample["boundary"], sort_keys=True) for sample in samples
    }
    if len(fixtures) != 1:
        raise RuntimeError("Performance sample fixture varied between runs.")
    if len(boundaries) != 1:
        raise RuntimeError("Performance sample boundary varied between runs.")

    warm_measurements = [
        measurement
        for sample in samples
        for measurement in sample["warm"]["measurements"]
    ]
    return {
        "fresh_process_count": len(samples),
        "warm_measurement_count": len(warm_measurements),
        "cold": {
            field: _metric_summary(
                sample["cold"][field] for sample in samples
            )
            for field in (
                "wall_ms",
                "process_cpu_ms",
                "rss_delta_mb",
                "recompute_wall_ms",
            )
        },
        "warm": {
            field: _metric_summary(
                measurement[field] for measurement in warm_measurements
            )
            for field in (
                "wall_ms",
                "process_cpu_ms",
                "rss_delta_mb",
            )
        },
        "structure": {
            "cold_document_object_count_after": _metric_summary(
                sample["cold"]["document_object_count_after"]
                for sample in samples
            ),
            "cold_document_object_delta": _metric_summary(
                sample["cold"]["document_object_delta"]
                for sample in samples
            ),
            "cold_recompute_count": _metric_summary(
                sample["cold"]["recompute_count"] for sample in samples
            ),
            "warm_document_object_delta": _metric_summary(
                measurement["document_object_delta"]
                for measurement in warm_measurements
            ),
            "warm_recompute_count": _metric_summary(
                measurement["recompute_count"]
                for measurement in warm_measurements
            ),
        },
    }


def _load_completed_sample(path):
    sample = json.loads(path.read_text(encoding="utf-8"))
    return _validate_sample(sample)


def profile_samples(run_dir, repetitions, timeout):
    if repetitions < 3:
        raise ValueError(
            "Phase 5 performance profiling requires at least three "
            "fresh-process samples."
        )
    wrapper = (
        PROJECT_ROOT
        / "tools"
        / "freecad_bridge"
        / "run-phase5-transition-performance-sample"
    )
    samples = []
    records = []
    for index in range(repetitions):
        sample_dir = run_dir / "samples" / "sample-{:02d}".format(index + 1)
        command = [
            str(wrapper),
            "--run-dir",
            str(sample_dir),
            "--timeout",
            str(timeout),
        ]
        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout + 120.0,
        )
        harness_elapsed_seconds = time.monotonic() - started
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "wrapper.stdout.log").write_text(
            completed.stdout,
            encoding="utf-8",
        )
        (sample_dir / "wrapper.stderr.log").write_text(
            completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode:
            raise RuntimeError(
                "Fresh-process sample {} exited with status {}.".format(
                    index + 1,
                    completed.returncode,
                )
            )
        sample_path = sample_dir / "sample.json"
        sample = _load_completed_sample(sample_path)
        samples.append(sample)
        records.append({
            "harness_elapsed_seconds": harness_elapsed_seconds,
            "sample_json": str(sample_path),
            "sample_json_sha256": sha256(sample_path),
        })

    versions = sorted({sample["freecad_version"] for sample in samples})
    if versions != ["1.1.1"]:
        raise RuntimeError("The qualified FreeCAD version set drifted.")
    return {
        "profile_class": "bounded_multi_object_coin_gui_baseline",
        "process_policy": (
            "one fresh isolated FreeCAD GUI process per cold sample; each "
            "process performs one unmeasured warm-up and exactly three "
            "same-process unchanged-state measurements"
        ),
        "cache_qualification": (
            "empty per-object preview caches for cold attachment; current "
            "per-object preview caches for warm reuse; persistent isolated "
            "preferences and uncontrolled operating-system file cache"
        ),
        "fixture": {
            "logical_object_count": FIXTURE_OBJECT_COUNT,
            "preview_segment_count": PREVIEW_SEGMENT_COUNT,
        },
        "boundaries": {
            "cold": COLD_BOUNDARY,
            "warm": WARM_BOUNDARY,
            "excluded": (
                "process launch, GUI readiness polling, screenshots, pointer "
                "selection, save/reopen, exact validation and export"
            ),
        },
        "samples": records,
        "summary": _summarise_samples(samples),
    }


def _git_record():
    def run(arguments):
        completed = subprocess.run(
            ["/usr/bin/git"] + list(arguments),
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            return None
        return completed.stdout.strip()

    status = run(("status", "--porcelain", "--untracked-files=all"))
    return {
        "head": run(("rev-parse", "HEAD")),
        "status_porcelain": [] if not status else status.splitlines(),
    }


def _environment_record():
    cpu_model = None
    cpuinfo = pathlib.Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    memory_total_kib = None
    meminfo = pathlib.Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                memory_total_kib = int(line.split()[1])
                break
    return {
        "cpu_count": os.cpu_count(),
        "cpu_model": cpu_model,
        "machine": platform.machine(),
        "memory_total_kib": memory_total_kib,
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
    }


def _source_record():
    paths = (
        PROJECT_ROOT / "reference/contracts/phase1-compatibility.json",
        PROJECT_ROOT / "tracktemplate/adapters/freecad/transition_state.py",
        PROJECT_ROOT / "tracktemplate/application/transition_derived.py",
        PROJECT_ROOT / "tracktemplate/presentation/transition_preview.py",
        PROJECT_ROOT / "tracktemplate/presentation/transition_coin.py",
        PROJECT_ROOT
        / "tracktemplate/presentation/transition_coin_viewprovider.py",
        PROJECT_ROOT
        / "tests/freecad_gui_profile_phase5_transition_coin_performance.py",
        PROJECT_ROOT / "tools/freecad_bridge/launch-freecad",
        PROJECT_ROOT / "tools/freecad_bridge/orchestration.py",
        PROJECT_ROOT / "tools/freecad_bridge/run-isolated",
        PROJECT_ROOT
        / "tools/freecad_bridge/run-phase5-transition-performance-sample",
        PROJECT_ROOT
        / "tools/freecad_bridge/run_phase5_transition_performance_sample.py",
        pathlib.Path(__file__).resolve(),
    )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): sha256(path)
        for path in paths
    }


def _run_directory(requested):
    root = RUN_ROOT.resolve()
    if requested is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        run_dir = root / (stamp + "-profile")
    else:
        run_dir = requested.resolve()
        try:
            run_dir.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "Phase 5 performance output must remain under {}.".format(
                    root
                )
            ) from error
    if run_dir.exists():
        raise SystemExit(
            "Phase 5 performance directory already exists: {}".format(
                run_dir
            )
        )
    run_dir.mkdir(parents=True)
    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
    )
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--run-dir", type=pathlib.Path)
    args = parser.parse_args()

    run_dir = _run_directory(args.run_dir)
    result_path = run_dir / "performance.json"
    state = {
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "started_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "purpose": (
            "Measure the bounded Phase 5 Coin candidate. This is "
            "not an accepted budget, renderer decision or whole-product "
            "profile."
        ),
        "git": _git_record(),
        "environment": _environment_record(),
        "source_sha256": _source_record(),
    }
    try:
        state["sample_profile"] = profile_samples(
            run_dir,
            args.repetitions,
            args.timeout,
        )
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        state["finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            PROFILE_SENTINEL
            + json.dumps(
                {
                    "path": str(result_path),
                    "status": state["status"],
                },
                sort_keys=True,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
