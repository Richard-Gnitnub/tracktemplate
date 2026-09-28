#!/usr/bin/env python3
"""Check the B16 complete-radius decision against the frozen witnesses."""

import json
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain import crossover  # noqa: E402


SENTINEL = "Phase 8 crossover complete-radius preflight validation passed"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
COMPONENT_FIELDS = (
    "turnout_a_mapped_minimum_radius_mm",
    "turnout_b_mapped_minimum_radius_mm",
    "connector_minimum_radius_mm",
)
RESULT_FIELDS = (
    "turnout_a_minimum_radius_mm",
    "turnout_b_minimum_radius_mm",
    "connector_minimum_radius_mm",
)


def _expect_value_error(arguments, text):
    try:
        crossover.complete_radius_decision(*arguments)
    except ValueError as error:
        assert text in str(error), str(error)
        return
    raise AssertionError("Invalid crossover radius was accepted: {!r}".format(
        arguments,
    ))


def validate_frozen_witnesses():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-feasibility:1"
    )
    requested = contract["request"]["minimum_radius_mm"]
    tolerance = contract["request"]["comparison_tolerance_mm"]
    assert requested == 600.0
    assert tolerance == 1.0e-6
    witnesses = {item["id"]: item for item in contract["witnesses"]}
    assert set(witnesses) == {
        "lower-preview-pass-complete-fail",
        "documented-valid-placement",
    }
    for witness in witnesses.values():
        radii = tuple(witness[key] for key in COMPONENT_FIELDS)
        result = crossover.complete_radius_decision(*radii, requested)
        for key, expected in zip(RESULT_FIELDS, radii):
            assert math.isclose(
                result[key], expected, rel_tol=0.0, abs_tol=tolerance,
            ), (witness["id"], key, result[key], expected)
        assert math.isclose(
            result["complete_minimum_radius_mm"],
            witness["complete_minimum_radius_mm"],
            rel_tol=0.0,
            abs_tol=tolerance,
        )
        assert result["minimum_requested_radius_mm"] == requested
        assert result["accepted"] is (
            witness["complete_rule_result"] == "accept"
        )
        assert str(result["limiting_component"]) in result["diagnostic"]
        assert "600.000000 mm" in result["diagnostic"]
    rejected = crossover.complete_radius_decision(*(
        witnesses["lower-preview-pass-complete-fail"][key]
        for key in COMPONENT_FIELDS
    ), requested)
    assert rejected["limiting_component"] == "Host Track B turnout road"
    assert "540.848375 mm" in rejected["diagnostic"]
    accepted = crossover.complete_radius_decision(*(
        witnesses["documented-valid-placement"][key]
        for key in COMPONENT_FIELDS
    ), requested)
    assert accepted["limiting_component"] == "Connecting road"


def validate_boundaries():
    decide = crossover.complete_radius_decision
    assert decide(700.0, 600.0, 800.0, 600.0)["accepted"] is True
    assert decide(700.0, 600.0 - 1.0e-7, 800.0, 600.0)[
        "accepted"
    ] is False
    assert decide(700.0, 600.0 - 2.0e-7, 800.0, 600.0)[
        "accepted"
    ] is False
    tie = decide(600.0, 600.0, 700.0, 600.0)
    assert tie["limiting_component"] == "Host Track A turnout road"
    straight = decide(None, None, None, 600.0)
    assert straight["accepted"] is True
    assert straight["complete_minimum_radius_mm"] is None
    assert straight["limiting_component"] is None
    assert "straight" in straight["diagnostic"]
    assert decide(None, 650.0, None, 600.0)[
        "limiting_component"
    ] == "Host Track B turnout road"

    for requested in (0.0, -1.0, math.nan, math.inf, -math.inf):
        _expect_value_error((700.0, 800.0, 900.0, requested),
                            "Minimum resulting radius")
    for index, label in enumerate((
        "Host Track A turnout road",
        "Host Track B turnout road",
        "Connecting road",
    )):
        for invalid in (0.0, -1.0, math.nan, math.inf, -math.inf):
            values = [700.0, 800.0, 900.0, 600.0]
            values[index] = invalid
            _expect_value_error(tuple(values), label)


def validate():
    validate_frozen_witnesses()
    validate_boundaries()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
