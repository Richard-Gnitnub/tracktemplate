#!/usr/bin/env python3
"""Fast contracts for the Phase 3 transition performance profiler."""

import copy
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPORT_PATH = (
    ROOT
    / "reference"
    / "benchmarks"
    / "2026-07-22-b16-transition-performance-profile.md"
)

from tools import phase3_transition_performance as profile  # noqa: E402
from tools.semantic_compare import semantic_digest  # noqa: E402


def _assert_raises_text(error_type, text, action):
    try:
        action()
    except error_type as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected {}".format(error_type.__name__))


def _measurement(seed, object_delta):
    return {
        "wall_ms": 100.0 + seed,
        "process_cpu_ms": 90.0 + seed,
        "rss_delta_mb": 10.0 + seed,
        "object_delta": object_delta,
    }


def _recipe_result(workflow, seed=0.0):
    scenarios = []
    for index, declaration in enumerate(profile.PROFILED_ACTIONS[workflow]):
        scenarios.append({
            "name": declaration["scenario"],
            "measurement": _measurement(seed + index, index),
        })
    if workflow == profile.PLAIN_LINE_EDIT:
        scenarios.extend((
            {
                "name": "reject_zero_angle_before_transaction",
                "measurement": _measurement(seed + 2.0, 0),
            },
            {
                "name": "abort_replacement_transaction",
                "measurement": _measurement(seed + 3.0, 0),
            },
        ))
    return {"scenarios": scenarios}


def validate_calculation_profile():
    contract, implementations = profile._load_contract_and_implementations()
    cases = profile.build_calculation_cases(
        contract, implementations[profile.LEGACY_ROUTE]
    )
    assert len(cases) == 202
    assert sum(case["expected_error"] is None for case in cases) == 198
    assert sum(case["expected_error"] is not None for case in cases) == 4

    legacy = profile.execute_calculation_grid(
        implementations[profile.LEGACY_ROUTE], cases
    )
    modular = profile.execute_calculation_grid(
        implementations[profile.MODULAR_ROUTE], cases
    )
    assert type(legacy) is tuple and type(modular) is tuple
    assert legacy == modular
    assert semantic_digest(legacy) == semantic_digest(modular)

    measured = profile.profile_calculations(contract, implementations, 3)
    assert measured["repetitions_per_route"] == 3
    assert measured["route_orders"] == [
        [profile.LEGACY_ROUTE, profile.MODULAR_ROUTE],
        [profile.MODULAR_ROUTE, profile.LEGACY_ROUTE],
        [profile.LEGACY_ROUTE, profile.MODULAR_ROUTE],
    ]
    assert measured["case_counts"] == {"valid": 198, "error": 4, "total": 202}
    assert all(
        len(measured["runs"][route]) == 3 for route in profile.ROUTES
    )
    assert all(
        item["result_digest"] == measured["result_digest"]
        for route in profile.ROUTES
        for item in measured["runs"][route]
    )

    _assert_raises_text(
        ValueError,
        "at least three",
        lambda: profile.profile_calculations(contract, implementations, 2),
    )


def validate_action_boundaries_and_summaries():
    assert tuple(profile.PROFILED_ACTIONS) == profile.WORKFLOWS
    assert [
        declaration["scenario"]
        for declaration in profile.PROFILED_ACTIONS[profile.PLAIN_LINE_EDIT]
    ] == ["replace_left_with_right", "change_right_back_to_left"]
    assert [
        declaration["scenario"]
        for declaration in profile.PROFILED_ACTIONS[profile.CONNECTED_STRAIGHT]
    ] == [
        "create_controlled_connected_pair",
        "edit_connected_pair_lengths",
    ]
    for workflow in profile.WORKFLOWS:
        actions = profile._profiled_action_measurements(
            workflow, _recipe_result(workflow)
        )
        assert tuple(actions) == tuple(
            declaration["scenario"]
            for declaration in profile.PROFILED_ACTIONS[workflow]
        )
        assert [record["span_class"] for record in actions.values()] == [
            "operator_action",
            "same_process_correctness",
        ]

    broken = _recipe_result(profile.PLAIN_LINE_EDIT)
    broken["scenarios"][0]["measurement"].pop("wall_ms")
    _assert_raises_text(
        RuntimeError,
        "lacks wall_ms",
        lambda: profile._profiled_action_measurements(
            profile.PLAIN_LINE_EDIT, broken
        ),
    )

    samples = {
        workflow: {
            declaration["scenario"]: {
                profile.LEGACY_ROUTE: [
                    _measurement(float(index), index) for index in range(3)
                ],
                profile.MODULAR_ROUTE: [
                    _measurement(float(index) + 0.5, index) for index in range(3)
                ],
            }
            for declaration in profile.PROFILED_ACTIONS[workflow]
        }
        for workflow in profile.WORKFLOWS
    }
    summaries, comparisons = profile._workflow_summaries(samples)
    action = "replace_left_with_right"
    assert summaries[profile.PLAIN_LINE_EDIT][action][profile.LEGACY_ROUTE][
        "wall_ms"
    ]["median"] == 101.0
    assert comparisons[profile.PLAIN_LINE_EDIT][action]["wall_ms"][
        "observed_ranges_overlap"
    ] is True
    assert comparisons[profile.PLAIN_LINE_EDIT][action]["object_delta"][
        "exact_sample_equality"
    ] is True

    disjoint = profile._comparison(
        profile._metric_summary([{"value": value} for value in (1, 2, 3)], "value"),
        profile._metric_summary([{"value": value} for value in (4, 5, 6)], "value"),
    )
    assert disjoint["disposition"] == (
        "modular_range_above_legacy_range_review_required"
    )
    _assert_raises_text(
        ValueError,
        "at least three",
        lambda: profile.profile_workflows(
            ROOT / "missing.FCStd", ROOT / "unused", 2, 1.0
        ),
    )


def validate_source_contract():
    source = (ROOT / "tools/phase3_transition_performance.py").read_text(
        encoding="utf-8"
    )
    assert "run-phase3-transition-workflow" in source
    assert "one fresh isolated FreeCAD GUI process" in source
    assert "not an optimisation" in source
    assert profile.DEFAULT_CALCULATION_REPETITIONS == 9
    assert profile.DEFAULT_WORKFLOW_REPETITIONS == 3
    assert profile.RUN_ROOT.name == "phase3-transition-workflow-runs"
    assert profile.MEASUREMENT_FIELDS == (
        "wall_ms",
        "process_cpu_ms",
        "rss_delta_mb",
        "object_delta",
    )
    assert not any(
        name in source for name in ("import FreeCAD", "import Part", "import PySide")
    )

    altered = _recipe_result(profile.CONNECTED_STRAIGHT)
    missing = copy.deepcopy(altered)
    missing["scenarios"].pop()
    _assert_raises_text(
        RuntimeError,
        "scenario is missing",
        lambda: profile._profiled_action_measurements(
            profile.CONNECTED_STRAIGHT, missing
        ),
    )


def validate_evidence_links():
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "completed regression profile" in report
    assert "202 cases" in report
    assert "nine measurements per route" in report
    assert "12 GUI runs completed" in report
    assert (
        "80a1de3e60e34dbd96f0e1669b9b801ef9eb898cfd11be331a47560869beb486"
        in report
    )
    assert (
        "a6dd3dda62519972e7a2f36f0b822817e95984121f7db66097d44495ee6b0deb"
        in report
    )
    assert "no optimisation" in report.lower()
    assert "explicit project-owner acceptance" in report

    phase3 = (ROOT / "reference/PHASE3_TRANSITION_SLICE.md").read_text(
        encoding="utf-8"
    )
    assert "all five technical exit conditions and project-owner" in phase3
    assert "2026-07-22-b16-transition-performance-profile.md" in phase3
    assert "Closeout acceptance and carried controls" in phase3

    plan = (ROOT / "reference/PROJECT_PLAN.md").read_text(encoding="utf-8")
    assert "`█████` — 5/5 exit conditions evidenced and accepted" in plan
    assert "| `█████` — 5/5 evidenced | Complete — accepted 2026-07-22 |" in plan
    assert "Phase 3: first parity-proven vertical slice" in plan
    assert "Complete — all five technical exit conditions" in plan

    validation = (ROOT / "reference/VALIDATION.md").read_text(encoding="utf-8")
    assert "tests/validate_phase3_transition_performance.py" in validation
    assert "tools/phase3_transition_performance.py" in validation


def validate():
    validate_calculation_profile()
    validate_action_boundaries_and_summaries()
    validate_source_contract()
    validate_evidence_links()
    print("Phase 3 transition performance profiler validation passed")


if __name__ == "__main__":
    validate()
