#!/usr/bin/env python3
"""Fast contracts for the Phase 5 Coin performance baseline."""

import copy
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase5_transition_performance as profile  # noqa: E402


def _assert_raises_text(error_type, text, action):
    try:
        action()
    except error_type as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected {}".format(error_type.__name__))


def _warm_measurement(seed):
    return {
        "cache_reuse_count": profile.FIXTURE_OBJECT_COUNT,
        "document_object_count_after": profile.FIXTURE_OBJECT_COUNT,
        "document_object_count_before": profile.FIXTURE_OBJECT_COUNT,
        "document_object_delta": 0,
        "part_shape_count": 0,
        "process_cpu_ms": 2.0 + seed,
        "recompute_count": 0,
        "rss_after_mb": 110.0 + seed,
        "rss_before_mb": 109.0 + seed,
        "rss_delta_mb": 1.0,
        "scene_replacement_count": 0,
        "stable_mapping_count": profile.FIXTURE_OBJECT_COUNT,
        "wall_ms": 3.0 + seed,
    }


def _sample(seed=0.0):
    return {
        "schema_version": 1,
        "profile_id": profile.SAMPLE_PROFILE_ID,
        "status": "completed",
        "freecad_version": "1.1.1",
        "qualified_profile_id": profile.QUALIFIED_PROFILE_ID,
        "fixture": {
            "logical_object_count": profile.FIXTURE_OBJECT_COUNT,
            "preview_segment_count": profile.PREVIEW_SEGMENT_COUNT,
        },
        "boundary": {
            "cold": profile.COLD_BOUNDARY,
            "warm": profile.WARM_BOUNDARY,
        },
        "cold": {
            "cache_current_count": profile.FIXTURE_OBJECT_COUNT,
            "cache_missing_count_before": profile.FIXTURE_OBJECT_COUNT,
            "display_modes_added": profile.FIXTURE_OBJECT_COUNT,
            "document_object_count_after": profile.FIXTURE_OBJECT_COUNT,
            "document_object_count_before": 0,
            "document_object_delta": profile.FIXTURE_OBJECT_COUNT,
            "part_shape_count": 0,
            "process_cpu_ms": 20.0 + seed,
            "recompute_count": 1,
            "recompute_wall_ms": 4.0 + seed,
            "root_children_added": 0,
            "rss_after_mb": 120.0 + seed,
            "rss_before_mb": 100.0,
            "rss_delta_mb": 20.0 + seed,
            "stable_mapping_count": profile.FIXTURE_OBJECT_COUNT,
            "wall_ms": 25.0 + seed,
        },
        "warm": {
            "measurement_count": profile.WARM_MEASUREMENT_COUNT,
            "measurements": [
                _warm_measurement(seed + index)
                for index in range(profile.WARM_MEASUREMENT_COUNT)
            ],
            "warm_up": {
                "cache_reuse_count": profile.FIXTURE_OBJECT_COUNT,
                "recompute_count": 0,
                "scene_replacement_count": 0,
            },
        },
        "cleanup": {
            "cache_count_after": 0,
            "document_object_count_after": 0,
            "open_document_count_after": 0,
            "viewprovider_count_after": 0,
        },
    }


def validate_sample_contract():
    validated = profile._validate_sample(_sample())
    assert validated["cold"]["document_object_delta"] == (
        profile.FIXTURE_OBJECT_COUNT
    )
    assert validated["warm"]["measurement_count"] == 3

    wrong_version = _sample()
    wrong_version["freecad_version"] = "1.2.0"
    _assert_raises_text(
        RuntimeError,
        "qualified FreeCAD version",
        lambda: profile._validate_sample(wrong_version),
    )

    wrong_profile = _sample()
    wrong_profile["qualified_profile_id"] = "another-profile"
    _assert_raises_text(
        RuntimeError,
        "qualified runtime profile",
        lambda: profile._validate_sample(wrong_profile),
    )

    stale = _sample()
    stale["warm"]["measurements"][1]["cache_reuse_count"] -= 1
    _assert_raises_text(
        RuntimeError,
        "cache reuse",
        lambda: profile._validate_sample(stale),
    )

    leaked = _sample()
    leaked["cleanup"]["open_document_count_after"] = 1
    _assert_raises_text(
        RuntimeError,
        "cleanup",
        lambda: profile._validate_sample(leaked),
    )

    dense = _sample()
    dense["cold"]["part_shape_count"] = 1
    _assert_raises_text(
        RuntimeError,
        "Part shape",
        lambda: profile._validate_sample(dense),
    )


def validate_summaries():
    samples = [_sample(float(index)) for index in range(3)]
    summary = profile._summarise_samples(samples)
    assert summary["fresh_process_count"] == 3
    assert summary["warm_measurement_count"] == 9
    assert summary["cold"]["wall_ms"] == {
        "maximum": 27.0,
        "median": 26.0,
        "minimum": 25.0,
        "values": [25.0, 26.0, 27.0],
    }
    assert summary["warm"]["wall_ms"]["median"] == 5.0
    assert summary["structure"]["cold_document_object_count_after"][
        "values"
    ] == [profile.FIXTURE_OBJECT_COUNT] * 3
    assert summary["structure"]["warm_recompute_count"]["values"] == [0] * 9

    _assert_raises_text(
        ValueError,
        "at least three",
        lambda: profile._summarise_samples(samples[:2]),
    )

    inconsistent = copy.deepcopy(samples)
    inconsistent[2]["fixture"]["logical_object_count"] += 1
    _assert_raises_text(
        RuntimeError,
        "fixture",
        lambda: profile._summarise_samples(inconsistent),
    )


def validate_source_and_routing_contract():
    profiler_text = (
        ROOT / "tools/phase5_transition_performance.py"
    ).read_text(encoding="utf-8")
    sample_runner_text = (
        ROOT
        / "tools/freecad_bridge/run_phase5_transition_performance_sample.py"
    ).read_text(encoding="utf-8")
    wrapper_text = (
        ROOT
        / "tools/freecad_bridge/run-phase5-transition-performance-sample"
    ).read_text(encoding="utf-8")
    gui_probe_text = (
        ROOT
        / "tests/freecad_gui_profile_phase5_transition_coin_performance.py"
    ).read_text(encoding="utf-8")

    assert "run-phase5-transition-performance-sample" in profiler_text
    assert "one fresh isolated FreeCAD GUI process" in profiler_text
    assert "uncontrolled operating-system file cache" in profiler_text
    assert "not an accepted budget" in profiler_text
    assert "import FreeCAD" not in profiler_text
    assert "import FreeCADGui" not in profiler_text
    assert "run-isolated" in wrapper_text
    assert "profile.SAMPLE_SENTINEL" in sample_runner_text
    assert profile.SAMPLE_SENTINEL in gui_probe_text
    assert "time.perf_counter_ns()" in gui_probe_text
    assert "time.process_time_ns()" in gui_probe_text
    assert "VmRSS:" in gui_probe_text
    assert "document.recompute()" in gui_probe_text
    assert "hasattr(obj, \"Shape\")" in gui_probe_text
    assert "refresh_for_state(state)" in gui_probe_text


def validate_evidence_links():
    validation = (ROOT / "reference/VALIDATION.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT / "reference/current/PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert "tools/phase5_transition_performance.py" in validation
    assert "tests/validate_phase5_transition_performance.py" in validation
    assert "## Bounded Coin performance baseline" in evidence
    assert "three fresh isolated freecad gui processes" in evidence.lower()
    assert "No numerical budget" in evidence


def validate():
    assert profile.DEFAULT_REPETITIONS == 3
    assert profile.FIXTURE_OBJECT_COUNT == 8
    assert profile.PREVIEW_SEGMENT_COUNT == 32
    assert profile.WARM_MEASUREMENT_COUNT == 3
    validate_sample_contract()
    validate_summaries()
    validate_source_and_routing_contract()
    validate_evidence_links()
    print("Phase 5 transition performance baseline validation passed")


if __name__ == "__main__":
    validate()
