#!/usr/bin/env python3
"""Check strict fixed XO-001 B4 cross-mode receipt comparison."""

import copy
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge import (  # noqa: E402
    compare_phase8_crossover_b4_modes as comparator,
)


SENTINEL = "Phase 8 crossover B4 cross-mode comparison validation passed"


def _receipts():
    analysis = {
        "geometry_signature": "fixed-xo001-geometry",
        "analysis_basis": "Effective automatically resolved timber arrangement",
        "findings": [{"code": "retained-finding", "measure": 1}],
        "nested": {"performance_timings_ms": {"important": 2}},
        "performance_timings_ms": {"total": 10.0},
    }
    core = {
        "status": "complete",
        "counts": {"effective_timber_count": 86},
        "record_turnout_sides": {"a": 43, "b": 43},
        "record_envelope_kinds": {"shared": 16},
        "record_identity_sha256": "a" * 64,
        "stable_record_sha256": "b" * 64,
        "resolution_signature": "fixed-xo001-resolution",
    }
    sources = {
        path: "c" * 64 for path in recipe.COMPARISON_SOURCE_PATHS
    }
    sources["tracktemplate/api.py"] = "d" * 64
    headless = {
        "status": "PASS",
        "sentinel": comparator.HEADLESS_SENTINEL,
        "host_profile_id": comparator.PROFILE,
        "source_fixture_sha256": "e" * 64,
        "source_fixture_sha256_after": "e" * 64,
        "comparison_source_sha256": sources,
        "comparison_source_sha256_after": copy.deepcopy(sources),
        "result": {
            **core,
            "resolved_analysis": copy.deepcopy(analysis),
            "resolved_analysis_signature": "fixed-xo001-geometry",
            "resolved_analysis_sha256": recipe.digest(analysis),
        },
    }
    gui_analysis = copy.deepcopy(analysis)
    gui_analysis["performance_timings_ms"] = {"total": 12.0}
    gui = {
        "status": "PASS",
        "source_fixture_sha256": "e" * 64,
        "source_fixture_sha256_after": "e" * 64,
        "comparison_source_sha256": copy.deepcopy(sources),
        "comparison_source_sha256_after": copy.deepcopy(sources),
        "probe": {
            "sentinel": comparator.GUI_SENTINEL,
            "matched_profile_id": comparator.PROFILE,
            "applied": {
                "result": copy.deepcopy(core),
                "resolved_analysis": {
                    "geometry_signature": "fixed-xo001-geometry",
                    "sha256": recipe.digest(gui_analysis),
                    "full": gui_analysis,
                },
            },
        },
    }
    return headless, gui


def _must_fail(headless, gui, reason):
    try:
        comparator.compare_receipts(headless, gui)
    except ValueError as error:
        assert reason in str(error), (reason, error)
    else:
        raise AssertionError("Invalid cross-mode receipt passed: " + reason)


def validate():
    headless, gui = _receipts()
    report = comparator.compare_receipts(headless, gui)
    assert report["status"] == "PASS"
    assert report["resolved_analysis_headless_sha256"] != (
        report["resolved_analysis_gui_sha256"]
    )
    assert report["resolved_analysis_semantic_sha256"] == recipe.digest({
        key: value
        for key, value in headless["result"]["resolved_analysis"].items()
        if key != "performance_timings_ms"
    })
    assert report["measured_performance_timings_ms"] == {
        "headless": {"total": 10.0},
        "real_gui": {"total": 12.0},
    }

    changed = copy.deepcopy(gui)
    analysis = changed["probe"]["applied"]["resolved_analysis"]
    analysis["full"]["findings"][0]["measure"] = 2
    analysis["sha256"] = recipe.digest(analysis["full"])
    _must_fail(headless, changed, "Non-timing resolved_analysis")

    changed = copy.deepcopy(gui)
    analysis = changed["probe"]["applied"]["resolved_analysis"]
    analysis["full"]["nested"]["performance_timings_ms"]["important"] = 3
    analysis["sha256"] = recipe.digest(analysis["full"])
    _must_fail(headless, changed, "Non-timing resolved_analysis")

    changed = copy.deepcopy(gui)
    analysis = changed["probe"]["applied"]["resolved_analysis"]
    del analysis["full"]["performance_timings_ms"]
    analysis["sha256"] = recipe.digest(analysis["full"])
    _must_fail(headless, changed, "performance_timings_ms")

    changed = copy.deepcopy(gui)
    changed["comparison_source_sha256"]["tracktemplate/api.py"] = "f" * 64
    _must_fail(headless, changed, "source identity")

    changed = copy.deepcopy(gui)
    changed["source_fixture_sha256"] = "f" * 64
    _must_fail(headless, changed, "fixture identity")

    changed = copy.deepcopy(gui)
    changed["probe"]["matched_profile_id"] = "different-profile"
    _must_fail(headless, changed, "host profiles")

    changed = copy.deepcopy(gui)
    changed["probe"]["applied"]["result"]["stable_record_sha256"] = "f" * 64
    _must_fail(headless, changed, "stable_record_sha256")

    changed = copy.deepcopy(gui)
    changed["probe"]["applied"]["resolved_analysis"]["geometry_signature"] = (
        "different-geometry"
    )
    _must_fail(headless, changed, "geometry signature")

    changed = copy.deepcopy(gui)
    changed["probe"]["applied"]["resolved_analysis"]["sha256"] = "f" * 64
    _must_fail(headless, changed, "receipt digest")
    print(SENTINEL)


if __name__ == "__main__":
    validate()
