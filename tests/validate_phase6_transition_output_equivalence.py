#!/usr/bin/env python3
"""Prove the finite B14/B15-to-B16 centreline comparison contract."""

from dataclasses import replace
import json
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from phase6_transition_output_equivalence import (  # noqa: E402
    NUMERICAL_TOLERANCE_MM,
    analytical_coordinates,
    compare_output_coordinates,
    equivalence_cases,
    exact_fixture,
    legacy_polyline,
    load_legacy_oracles,
    maximum_correspondence_error,
    simpson_remainder_bound_mm,
)
from validate_phase6_transition_exact_contract import (  # noqa: E402
    _decimal_clothoid_point,
)


def _must_reject(action, message=None):
    try:
        action()
    except AssertionError as error:
        if message is not None:
            assert message in str(error), error
        return
    raise AssertionError("The equivalence proof accepted corrupt geometry")


def _validate_independent_mathematics(state, result, oracles):
    length = state.analysis.transition_length_mm
    radius = state.intent.radius_mm
    stations = tuple(point.station_mm for point in result.centreline.points)
    oracle_results = []
    legacy_results = []
    maximum_absolute_error = 0.0
    maximum_remainder_bound = 0.0
    for oracle in oracles.values():
        coordinates = analytical_coordinates(oracle, state, stations)
        for station, coordinate in zip(stations, coordinates):
            x_mm, y_mm, _heading = _decimal_clothoid_point(
                station, length, radius,
            )
            absolute_error = math.dist(coordinate, (x_mm, y_mm, 0.0))
            remainder_bound = simpson_remainder_bound_mm(
                station, length, radius,
            )
            # The 1e-8 mm legacy parity tolerance is not an absolute
            # quadrature-accuracy promise. Keep the derived truncation
            # estimate distinct from the floating-point comparison term.
            assert absolute_error <= remainder_bound + NUMERICAL_TOLERANCE_MM
            maximum_absolute_error = max(
                maximum_absolute_error, absolute_error,
            )
            maximum_remainder_bound = max(
                maximum_remainder_bound, remainder_bound,
            )
        # The independent exit endpoint must normalise to the same Euler
        # entry, not merely acquire an Entry/Exit diagnostic label.
        exit_x, exit_y, angle = oracle["clothoid_exit_displacement"](
            length, radius,
        )
        rotated_x, rotated_y = oracle["rotate_xy"](
            exit_x, exit_y, -angle,
        )
        assert math.dist(
            (rotated_x, -rotated_y, 0.0), coordinates[-1],
        ) <= NUMERICAL_TOLERANCE_MM
        oracle_results.append(coordinates)
        legacy_results.append(legacy_polyline(oracle, state))
    assert oracle_results[0] == oracle_results[1]
    assert legacy_results[0] == legacy_results[1]
    return {
        "maximum_absolute_fresnel_error_mm": maximum_absolute_error,
        "maximum_simpson_remainder_bound_mm": maximum_remainder_bound,
        "floating_point_comparison_term_mm": NUMERICAL_TOLERANCE_MM,
    }


def _validate_negative_geometry(case, state, result, oracles):
    coordinates = tuple(
        (point.x_mm, point.y_mm, 0.0)
        for point in result.centreline.points
    )
    middle = len(coordinates) // 2
    altered = list(coordinates)
    point = altered[middle]
    altered[middle] = (point[0], point[1] + 0.01, point[2])
    # The modified interior point keeps every old min/max XY assertion.
    for axis in (0, 1):
        assert min(p[axis] for p in altered) == min(
            p[axis] for p in coordinates
        )
        assert max(p[axis] for p in altered) == max(
            p[axis] for p in coordinates
        )
    corruptions = (
        tuple((x, -y, z) for x, y, z in coordinates),
        tuple((x * 25.4, y * 25.4, z) for x, y, z in coordinates),
        tuple(reversed(coordinates)),
        tuple(altered),
        coordinates[:middle] + coordinates[middle + 1:],
        tuple((x, y, 0.01) for x, y, _z in coordinates),
    )
    for corrupted in corruptions:
        _must_reject(lambda corrupted=corrupted: compare_output_coordinates(
            case, state, result, corrupted, oracles=oracles,
        ))
    # A matching corruption of the B16 result and its transported points
    # defeats self-comparison. The legacy analytical oracle must reject it.
    bad_points = tuple(
        replace(point, y_mm=altered[index][1])
        for index, point in enumerate(result.centreline.points)
    )
    bad_result = replace(
        result, centreline=replace(result.centreline, points=bad_points),
    )
    _must_reject(lambda: compare_output_coordinates(
        case, state, bad_result, tuple(altered), oracles=oracles,
    ), "legacy analytical")
    legacy = legacy_polyline(next(iter(oracles.values())), state)
    reversed_stations = tuple(reversed(legacy))
    _must_reject(lambda: maximum_correspondence_error(
        legacy, reversed_stations,
    ))


def _validate_union_breakpoints():
    straight = ((0.0, 0.0, 0.0, 0.0), (2.0, 2.0, 0.0, 0.0))
    bend = (
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0, 0.0),
        (2.0, 2.0, 0.0, 0.0),
    )
    assert maximum_correspondence_error(straight, bend) == 1.0
    assert maximum_correspondence_error(bend, straight) == 1.0
    assert maximum_correspondence_error(straight, straight) == 0.0


def validate():
    oracles = load_legacy_oracles()
    reports = []
    cases = equivalence_cases()
    for case in cases:
        state, specification, artifact = exact_fixture(case, oracles)
        before = api.transition_state_to_json(state)
        result = api.transition_exact_result_from_artifact(artifact)
        coordinates = tuple(
            (point.x_mm, point.y_mm, 0.0)
            for point in result.centreline.points
        )
        reports.append(compare_output_coordinates(
            case, state, result, coordinates, oracles=oracles,
        ))
        reports[-1]["analytical_method_evidence"] = (
            _validate_independent_mathematics(state, result, oracles)
        )
        assert api.transition_state_to_json(state) == before
        assert specification.maximum_chord_error_mm == 0.05
        if case.case_id == "recorded-outside-entry":
            assert state.analysis.transition_length_mm == 559.4102547270278
        if case.case_id == "recorded-inside-exit":
            assert state.analysis.transition_length_mm == 627.7998161783615

    # The caller may request a different resolution without changing the
    # product default or legacy sampling. The independent route still holds.
    case = replace(cases[0], maximum_chord_error_mm=0.025)
    state, _specification, artifact = exact_fixture(case, oracles)
    result = artifact.payload
    reports.append(compare_output_coordinates(
        case, state, result,
        tuple((p.x_mm, p.y_mm, 0.0) for p in result.centreline.points),
        oracles=oracles,
    ))
    _validate_negative_geometry(case, state, result, oracles)
    _validate_union_breakpoints()
    print("PHASE6_TRANSITION_OUTPUT_EQUIVALENCE=" + json.dumps(
        reports, sort_keys=True,
    ))
    print("Phase 6 transition output equivalence standalone validation passed")


if __name__ == "__main__":
    validate()
