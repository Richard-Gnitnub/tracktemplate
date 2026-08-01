#!/usr/bin/env python3
"""Validate the bounded Phase 6 transition exact-centreline contract."""

from dataclasses import replace
from decimal import Decimal, localcontext
import hashlib
import importlib.abc
import json
import math
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.application import transition_exact as exact  # noqa: E402
from tracktemplate.domain import alignment  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _intent(transition_length_mm=300.0, **changes):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    values = {
        "transition_id": "transition:phase6:exact",
        "circle_centre_y_mm": circle_centre_y_mm,
        "radius_mm": radius_mm,
        "target_signed_offset_mm": api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        "total_angle_rad": math.pi / 2.0,
        "track_name": "Phase 6 exact transition",
        "end_name": "Entry",
    }
    values.update(changes)
    return api.TransitionIntent(**values)


def _state(transition_length_mm=300.0, **changes):
    return api.analyse_transition_state(
        api.TransitionState(
            _intent(
                transition_length_mm=transition_length_mm,
                **changes,
            )
        )
    )


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _decimal_clothoid_point(station_mm, transition_length_mm, radius_mm):
    """Evaluate the Euler curve independently with a Decimal power series."""
    if station_mm == 0.0 or transition_length_mm == 0.0:
        return 0.0, 0.0, 0.0
    with localcontext() as context:
        context.prec = 70
        station = Decimal(str(station_mm))
        transition_length = Decimal(str(transition_length_mm))
        radius = Decimal(str(radius_mm))
        scale = Decimal(2) * radius * transition_length
        x_value = Decimal(0)
        y_value = Decimal(0)
        for index in range(32):
            sign = Decimal(-1 if index % 2 else 1)
            x_value += (
                sign
                * station ** (4 * index + 1)
                / (
                    scale ** (2 * index)
                    * Decimal(math.factorial(2 * index))
                    * Decimal(4 * index + 1)
                )
            )
            y_value += (
                sign
                * station ** (4 * index + 3)
                / (
                    scale ** (2 * index + 1)
                    * Decimal(math.factorial(2 * index + 1))
                    * Decimal(4 * index + 3)
                )
            )
        tangent = station * station / scale
        return float(x_value), float(y_value), float(tangent)


def _distance_to_chord(point, start, end):
    chord_x = end[0] - start[0]
    chord_y = end[1] - start[1]
    squared_length = chord_x * chord_x + chord_y * chord_y
    assert squared_length > 0.0
    fraction = (
        (point[0] - start[0]) * chord_x
        + (point[1] - start[1]) * chord_y
    ) / squared_length
    fraction = min(1.0, max(0.0, fraction))
    nearest_x = start[0] + fraction * chord_x
    nearest_y = start[1] + fraction * chord_y
    return math.hypot(point[0] - nearest_x, point[1] - nearest_y)


def _validate_specification_and_public_contract():
    specification = api.TransitionExactSpecification(
        maximum_chord_error_mm=0.05,
        maximum_segment_count=64,
    )
    request = specification.derived_request()
    assert request.stage == "exact-validation"
    assert request.exact_validation_result_signature is None
    assert request == specification.derived_request()
    assert request != api.TransitionExactSpecification(
        maximum_chord_error_mm=0.025,
        maximum_segment_count=64,
    ).derived_request()
    assert request != api.TransitionExactSpecification(
        maximum_chord_error_mm=0.05,
        maximum_segment_count=128,
    ).derived_request()

    for invalid in (True, 0.0, -0.1, math.nan, math.inf, "0.05"):
        _expect_state_error(
            lambda invalid=invalid: api.TransitionExactSpecification(
                maximum_chord_error_mm=invalid,
                maximum_segment_count=64,
            ),
            "invalid-exact-specification"
            if invalid in (0.0, -0.1)
            else "invalid-exact-value",
        )
    for invalid in (True, 0, -1, 2.5, "64"):
        _expect_state_error(
            lambda invalid=invalid: api.TransitionExactSpecification(
                maximum_chord_error_mm=0.05,
                maximum_segment_count=invalid,
            ),
            "invalid-exact-specification",
        )

    assert api.TransitionExactCentreline is exact.TransitionExactCentreline
    assert api.TransitionExactPoint is exact.TransitionExactPoint
    assert (
        api.TransitionExactSpecification
        is exact.TransitionExactSpecification
    )
    assert (
        api.TransitionExactValidationResult
        is exact.TransitionExactValidationResult
    )
    assert api.regenerate_transition_exact is exact.regenerate_transition_exact
    assert (
        api.transition_exact_result_from_artifact
        is exact.transition_exact_result_from_artifact
    )
    for name in exact.__all__:
        assert name in api.__all__


def _validate_exact_geometry_and_independent_oracle():
    state = _state()
    specification = api.TransitionExactSpecification(0.05, 64)
    persisted_before = api.transition_state_to_json(state)
    artifact = api.regenerate_transition_exact(
        api.TransitionDerivedCache(),
        state,
        specification,
    )
    result = artifact.payload
    assert isinstance(result, api.TransitionExactValidationResult)
    assert artifact.stage == "exact-validation"
    assert artifact.source_signature == result.source_signature
    assert result.artifact_signature.startswith("sha256:")
    assert result.result_signature.startswith("sha256:")

    centreline = result.centreline
    assert centreline.domain_id == state.intent.transition_id
    assert centreline.frame_id == api.TRANSITION_EXACT_FRAME_ID
    assert api.TRANSITION_EXACT_INTEGRATION_STEPS == 240
    assert centreline.length_unit == "mm"
    assert centreline.angle_unit == "rad"
    assert centreline.maximum_chord_error_mm == 0.05
    expected_segments = math.ceil(
        state.analysis.transition_length_mm
        / math.sqrt(8.0 * state.intent.radius_mm * 0.05)
    )
    assert len(centreline.points) == expected_segments + 1
    assert centreline.points[0] == api.TransitionExactPoint(0.0, 0.0, 0.0, 0.0)
    assert centreline.points[-1].station_mm == (
        state.analysis.transition_length_mm
    )
    expected_bound = (
        (state.analysis.transition_length_mm / expected_segments) ** 2
        / (8.0 * state.intent.radius_mm)
    )
    assert math.isclose(
        centreline.chord_error_bound_mm,
        expected_bound,
        rel_tol=1.0e-15,
    )
    assert centreline.chord_error_bound_mm <= 0.05

    for point in centreline.points:
        oracle = _decimal_clothoid_point(
            point.station_mm,
            state.analysis.transition_length_mm,
            state.intent.radius_mm,
        )
        assert math.isclose(point.x_mm, oracle[0], abs_tol=2.0e-10)
        assert math.isclose(point.y_mm, oracle[1], abs_tol=2.0e-10)
        assert math.isclose(point.tangent_rad, oracle[2], abs_tol=1.0e-15)

    for start, end in zip(centreline.points, centreline.points[1:]):
        for numerator in range(1, 8):
            station_mm = start.station_mm + (
                (end.station_mm - start.station_mm)
                * float(numerator)
                / 8.0
            )
            oracle = _decimal_clothoid_point(
                station_mm,
                state.analysis.transition_length_mm,
                state.intent.radius_mm,
            )
            distance = _distance_to_chord(
                oracle[:2],
                (start.x_mm, start.y_mm),
                (end.x_mm, end.y_mm),
            )
            assert distance <= centreline.chord_error_bound_mm + 2.0e-10

    export_request = api.TransitionDerivedRequest(
        stage="export",
        contract_signature=api.transition_derived_contract_signature(
            "test-only.phase6-export.v1",
            {"format": "not-selected"},
        ),
        exact_validation_result_signature=result.result_signature,
    )
    assert export_request.exact_validation_result_signature == (
        result.result_signature
    )
    assert api.transition_state_to_json(state) == persisted_before
    assert "exact" not in json.loads(persisted_before)


def _validate_representative_mathematical_ranges():
    cases = (
        (50.0, 2000.0, 0.001, 64),
        (300.0, 655.0, 0.05, 64),
        (600.0, 600.0, 0.1, 64),
        (1000.0, 400.0, 0.05, 128),
    )
    for transition_length_mm, radius_mm, tolerance_mm, limit in cases:
        stations, error_bound = alignment.clothoid_entry_polyline_stations(
            transition_length_mm,
            radius_mm,
            tolerance_mm,
            limit,
        )
        assert stations[0] == 0.0
        assert stations[-1] == transition_length_mm
        assert all(
            current > previous
            for previous, current in zip(stations, stations[1:])
        )
        assert error_bound <= tolerance_mm
        previous_tangent = -1.0
        for station_mm in stations:
            observed = alignment.clothoid_entry_displacement_at_station(
                station_mm,
                transition_length_mm,
                radius_mm,
                api.TRANSITION_EXACT_INTEGRATION_STEPS,
            )
            oracle = _decimal_clothoid_point(
                station_mm,
                transition_length_mm,
                radius_mm,
            )
            assert math.isclose(observed[0], oracle[0], abs_tol=2.0e-8)
            assert math.isclose(observed[1], oracle[1], abs_tol=2.0e-8)
            assert math.isclose(observed[2], oracle[2], abs_tol=1.0e-14)
            assert observed[2] >= previous_tangent
            previous_tangent = observed[2]


def _validate_lifecycle_and_failure_atomicity():
    state = _state()
    specification = api.TransitionExactSpecification(0.05, 64)
    request = specification.derived_request()
    cache = api.TransitionDerivedCache()
    assert cache.status(state, request) == "missing"
    first = api.regenerate_transition_exact(cache, state, specification)
    assert api.transition_exact_result_from_artifact(first) is first.payload
    assert cache.status(state, request) == "current"
    assert (
        api.regenerate_transition_exact(cache, state, specification)
        is first
    )

    renamed = api.replace_transition_intent(
        state,
        replace(
            state.intent,
            track_name="Renamed exact diagnostic",
            end_name="Exit",
        ),
    )
    assert api.transition_analysis_status(renamed) == "current"
    assert (
        api.regenerate_transition_exact(cache, renamed, specification)
        is first
    )

    changed = _state(260.0)
    assert cache.status(changed, request) == "stale"
    changed_artifact = api.regenerate_transition_exact(
        cache,
        changed,
        specification,
    )
    assert changed_artifact.payload.result_signature != (
        first.payload.result_signature
    )

    restored = _state()
    assert cache.status(restored, request) == "stale"
    restored_artifact = api.regenerate_transition_exact(
        cache,
        restored,
        specification,
    )
    assert restored_artifact.source_signature == first.source_signature
    assert restored_artifact.payload == first.payload

    tighter = api.TransitionExactSpecification(0.01, 128)
    assert cache.status(restored, tighter.derived_request()) == "stale"
    tighter_artifact = api.regenerate_transition_exact(
        cache,
        restored,
        tighter,
    )
    assert len(tighter_artifact.payload.centreline.points) > len(
        first.payload.centreline.points
    )

    current = cache.artifact("exact-validation")
    impossible = api.TransitionExactSpecification(1.0e-8, 1)
    _expect_state_error(
        lambda: api.regenerate_transition_exact(cache, restored, impossible),
        "exact-resolution-exceeded",
    )
    assert cache.artifact("exact-validation") is current

    cold = api.TransitionState(state.intent)
    _expect_state_error(
        lambda: api.regenerate_transition_exact(
            api.TransitionDerivedCache(),
            cold,
            specification,
        ),
        "analysis-required",
    )

    incompatible_cache = api.TransitionDerivedCache()
    incompatible_cache.regenerate(
        state,
        request,
        lambda _state, _request: {"not": "an exact result"},
    )
    _expect_state_error(
        lambda: api.regenerate_transition_exact(
            incompatible_cache,
            state,
            specification,
        ),
        "invalid-exact-artifact",
    )

    valid_result = first.payload
    changed_points = list(valid_result.centreline.points)
    changed_points[1] = replace(
        changed_points[1],
        x_mm=changed_points[1].x_mm + 0.25,
    )
    corrupt_results = (
        replace(
            valid_result,
            centreline=replace(
                valid_result.centreline,
                points=tuple(changed_points),
            ),
        ),
        replace(
            valid_result,
            artifact_signature="sha256:" + "0" * 64,
        ),
        replace(
            valid_result,
            result_signature="sha256:" + "1" * 64,
        ),
    )
    for corrupt_result in corrupt_results:
        corrupt_cache = api.TransitionDerivedCache()
        corrupt_cache.regenerate(
            state,
            request,
            lambda _state, _request, payload=corrupt_result: payload,
        )
        _expect_state_error(
            lambda cache=corrupt_cache: api.regenerate_transition_exact(
                cache,
                state,
                specification,
            ),
            "invalid-exact-artifact",
        )

    wrong_stage = api.TransitionDerivedArtifact(
        stage="preview",
        source_signature=first.source_signature,
        payload=first.payload,
    )
    _expect_state_error(
        lambda: api.transition_exact_result_from_artifact(wrong_stage),
        "invalid-exact-artifact",
    )
    try:
        api.transition_exact_result_from_artifact(object())
    except TypeError:
        pass
    else:
        raise AssertionError("Expected exact-artifact TypeError")


def _validate_zero_length_and_domain_limits():
    zero_state = _state(0.0)
    specification = api.TransitionExactSpecification(0.05, 1)
    result = api.regenerate_transition_exact(
        api.TransitionDerivedCache(),
        zero_state,
        specification,
    ).payload
    assert result.centreline.points == (
        api.TransitionExactPoint(0.0, 0.0, 0.0, 0.0),
    )
    assert result.centreline.chord_error_bound_mm == 0.0

    stations, error_bound = alignment.clothoid_entry_polyline_stations(
        300.0,
        655.0,
        0.05,
        64,
    )
    assert stations[0] == 0.0
    assert stations[-1] == 300.0
    assert len(stations) == 20
    assert error_bound <= 0.05
    for arguments in (
        (-1.0, 655.0, 0.05, 64),
        (300.0, 0.0, 0.05, 64),
        (300.0, 655.0, 0.0, 64),
        (300.0, 655.0, math.nan, 64),
        (300.0, 655.0, 0.05, True),
        (300.0, 655.0, 0.05, 0),
        (300.0, 655.0, 1.0e-8, 1),
        (alignment.GEOMETRY_TOLERANCE / 2.0, 655.0, 0.05, 1),
    ):
        try:
            alignment.clothoid_entry_polyline_stations(*arguments)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Expected invalid exact stationing for {!r}".format(arguments)
            )

    for action in (
        lambda: api.regenerate_transition_exact(
            object(),
            zero_state,
            specification,
        ),
        lambda: api.regenerate_transition_exact(
            api.TransitionDerivedCache(),
            object(),
            specification,
        ),
        lambda: api.regenerate_transition_exact(
            api.TransitionDerivedCache(),
            zero_state,
            object(),
        ),
    ):
        try:
            action()
        except TypeError:
            pass
        else:
            raise AssertionError("Expected exact-contract TypeError")


def _validate_structure_and_isolation():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    exact_module = modules["tracktemplate.application.transition_exact"]
    assert exact_module["layer"] == "application"
    assert exact_module["warning_signals"] == []
    assert exact_module["imports"] == [
        "dataclasses",
        "math",
        "tracktemplate.application.transition_derived",
        "tracktemplate.application.transition_state",
        "tracktemplate.domain.alignment",
    ]

    script = f"""
import importlib.abc
import sys

forbidden = {{
    "FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"
}}
attempted = []

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden import attempted: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {str(ROOT)!r})
from tracktemplate import api
specification = api.TransitionExactSpecification(0.05, 64)
assert specification.derived_request().stage == "exact-validation"
assert attempted == []
print("Phase 6 transition exact isolated import passed")
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert (
        "Phase 6 transition exact isolated import passed"
        in completed.stdout
    )

    for relative_path, expected_hash in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def validate():
    _validate_specification_and_public_contract()
    _validate_exact_geometry_and_independent_oracle()
    _validate_representative_mathematical_ranges()
    _validate_lifecycle_and_failure_atomicity()
    _validate_zero_length_and_domain_limits()
    _validate_structure_and_isolation()
    print("Phase 6 transition exact contract validation passed")


if __name__ == "__main__":
    validate()
