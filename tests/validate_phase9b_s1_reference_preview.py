#!/usr/bin/env python3
"""Prove rigid S1 placement with invented coordinates and exact examples.

These checks establish no chair fit, production or source-data acceptance.
Qualified native geometry and real-GUI evidence remain separate.
"""

import copy
from dataclasses import FrozenInstanceError
from fractions import Fraction
import math
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain.chair_placement import (  # noqa: E402
    S1Placement,
    prepare_s1_placements,
)
from tracktemplate.compatibility.chair_reference_preview import (  # noqa: E402
    _select_positions,
    _source_context,
)


SENTINEL = "Phase 9B S1 reference preview standalone validation passed"


def source_record(position_id="TO-001:S1:01", **changes):
    """Supply an invented identity rotation at a nonzero model-mm datum."""
    record = {
        "chair_position_identity": position_id,
        "rail_identity": "TO-001:rail:stock",
        "timber_identity": "TO-001:timber:01",
        "chair_code": 1,
        "centre_point": [10.0, 20.0],
        "base_z": 1.8,
        "outward_axis": [0.0, 1.0],
        "local_y_axis": [-1.0, 0.0],
    }
    record.update(changes)
    return record


def assert_rejected(operation, label):
    """Require the public rejection contract, not an incidental exception."""
    try:
        operation()
    except ValueError as error:
        assert str(error), label
    else:
        raise AssertionError("Accepted invalid placement: " + label)


def validate_known_transforms():
    """Hand-checkable rotations expose wrong yaw, signs and datum offsets."""
    cases = (
        (source_record(), (12.0, 23.0, 5.8)),
        (
            source_record(
                outward_axis=[-1.0, 0.0], local_y_axis=[0.0, -1.0],
            ),
            (7.0, 22.0, 5.8),
        ),
        (
            source_record(
                outward_axis=[0.0, -1.0], local_y_axis=[1.0, 0.0],
            ),
            (8.0, 17.0, 5.8),
        ),
    )
    for record, expected in cases:
        placement, = prepare_s1_placements([record])
        assert placement.transform_point((2, 3, 4)) == expected
        assert placement.transform_point((0, 0, 0)) == (10.0, 20.0, 1.8)
        assert placement.transform_point((0, 0, Fraction(1, 2))) == (
            10.0, 20.0, 2.3,
        )
    # A 3:4:5 frame supplies an independently calculable non-right angle.
    placement, = prepare_s1_placements([
        source_record(
            centre_point=[0, 0], base_z=0,
            outward_axis=[-0.8, 0.6], local_y_axis=[-0.6, -0.8],
        ),
    ])
    actual = placement.transform_point((5, 0, 7))
    assert actual == (3.0, 4.0, 7.0), actual
    return len(cases) + 1


def validate_rigid_distances():
    """Preserve lengths under many rotations without introducing scale."""
    start = (-2.0, 3.0, 4.0)
    finish = (4.0, -5.0, 4.0)
    for degrees in range(-180, 181, 15):
        radians = math.radians(degrees)
        cosine, sine = math.cos(radians), math.sin(radians)
        placement, = prepare_s1_placements([
            source_record(
                outward_axis=[-sine, cosine],
                local_y_axis=[-cosine, -sine],
            ),
        ])
        actual = math.dist(
            placement.transform_point(start),
            placement.transform_point(finish),
        )
        # The integer-coordinate displacement is a 6:8:10 triangle.
        assert math.isclose(actual, 10.0, rel_tol=0, abs_tol=2e-14), actual
    return 25


def validate_order_and_immutability():
    """Copy mutable inputs, retain exact translation and sort only by ID."""
    records = [source_record("b"), source_record("a", base_z=1.8000000001)]
    original = copy.deepcopy(records)
    placements = prepare_s1_placements(records)
    assert records == original
    assert isinstance(placements, tuple)
    assert tuple(item.position_id for item in placements) == ("a", "b")
    assert prepare_s1_placements(reversed(records)) == placements
    assert placements[0].origin_mm[2] == 1.8000000001
    assert placements[0].rail_id == records[1]["rail_identity"]
    assert placements[0].timber_id == records[1]["timber_identity"]
    records[1]["centre_point"][0] = 999
    records[1]["outward_axis"][0] = 999
    assert placements[0].origin_mm == (10.0, 20.0, 1.8000000001)
    assert placements[0].y_axis == (0.0, 1.0)
    try:
        placements[0].position_id = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Placement was mutable")
    # Direct construction has the same immutable coordinate boundary.
    origin = [1, 2, 3]
    direct = S1Placement("a", "r", "t", origin, [1, 0], [0, 1])
    origin[0] = 4
    assert direct.origin_mm == (1.0, 2.0, 3.0)
    assert isinstance(direct.x_axis, tuple)
    return 1


def invalid_records():
    yield "empty", []
    yield "none", None
    yield "non-record", ["chair"]
    yield "duplicate", [source_record(), source_record()]
    for field in source_record():
        record = source_record()
        del record[field]
        yield "missing-" + field, [record]
    for field in (
        "chair_position_identity", "rail_identity", "timber_identity",
    ):
        for value in ("", "   ", None, 1, True):
            yield field + "-" + repr(value), [source_record(**{field: value})]
    for value in (False, True, 0, 2, -1, 1.0, "1", None):
        yield "code-" + repr(value), [source_record(chair_code=value)]
    for value in (math.nan, math.inf, -math.inf, True, "2", 10 ** 1000):
        yield "z-" + repr(value), [source_record(base_z=value)]
        for field in ("centre_point", "local_y_axis", "outward_axis"):
            record = source_record()
            record[field][0] = value
            yield field + "-" + repr(value), [record]
    for field in ("centre_point", "local_y_axis", "outward_axis"):
        for value in (None, [], [0], [0, 1, 2], "01"):
            yield field + "-shape-" + repr(value), [
                source_record(**{field: value}),
            ]
    for label, changes in (
        ("zero-axis", {"local_y_axis": [0, 0]}),
        ("scaled-axis", {"local_y_axis": [-2, 0]}),
        ("small-scale-drift", {"local_y_axis": [-1 - 1e-12, 0]}),
        ("skew", {"outward_axis": [0.6, 0.8]}),
        ("parallel", {"outward_axis": [1, 0]}),
        ("reflection", {"local_y_axis": [1, 0]}),
    ):
        yield label, [source_record(**changes)]


def validate_rejections():
    count = 0
    for label, records in invalid_records():
        assert_rejected(lambda: prepare_s1_placements(records), label)
        count += 1
    placement, = prepare_s1_placements([source_record()])
    for point in (None, [], [0, 1], [0, 1, 2, 3], "123"):
        assert_rejected(lambda: placement.transform_point(point), repr(point))
        count += 1
    for value in (True, "1", math.nan, math.inf, -math.inf, 10 ** 1000):
        for index in range(3):
            point = [0, 0, 0]
            point[index] = value
            assert_rejected(
                lambda: placement.transform_point(point), repr(point),
            )
            count += 1
    huge = S1Placement("a", "r", "t", (0, 0, 1e308), (1, 0), (0, 1))
    assert_rejected(lambda: huge.transform_point((0, 0, 1e308)), "overflow")
    assert_rejected(
        lambda: S1Placement("a", "r", "t", (0, 0, 0), (1, 0), (0, -1)),
        "direct-reflection",
    )
    return count + 2


def selection_records():
    """Supply two S1s, one S1J and one unresolved analytical position."""
    module = SimpleNamespace(CHAIR_ASSIGNMENT_CONFIRMED="confirmed")
    positions = [
        {
            "stable_chair_position_identity": identity,
            "rail_identity": "TO-001:rail:stock",
            "timber_identity": "TO-001:timber:01",
            "chair_code": code,
            "assignment_status": "confirmed" if code in (1, 7) else "open",
            "deliberate_omission": False,
            "special_assignment_deferred": code == 99,
        }
        for identity, code in (("b", 1), ("a", 1), ("joint", 7), ("open", 99))
    ]
    analysis = {"positions": positions, "geometry_signature": "analysis-one"}
    plan = {
        "instances": [
            source_record("b"), source_record("a"),
            source_record("joint", chair_code=7),
        ],
        "analytical_only": [{
            "chair_position_identity": "open", "reason": "Unresolved",
            "rail_identity": "TO-001:rail:stock",
            "timber_identity": "TO-001:timber:01",
        }],
        "solid_signature": "rounded-solid-signature",
    }
    return module, analysis, plan


def unresolved_record(instance):
    """Retain the qualified host's frame rejection without repairing it."""
    return {
        "chair_position_identity": instance["chair_position_identity"],
        "rail_identity": instance["rail_identity"],
        "timber_identity": instance["timber_identity"],
        "reason": (
            "gauge normal is not perpendicular to the local rail tangent"
        ),
    }


def selection_rejections():
    """Exercise identity accounting and unsupported S1 assignment states."""
    module, base_analysis, base_plan = selection_records()
    for label in (
        "duplicate-analysis", "missing-analysis-id", "empty-analysis-id",
        "unknown-plan-id", "missing-plan-id", "duplicate-plan-id",
        "duplicate-across-plan-kinds", "unaccounted-position",
        "all-s1-unresolved", "empty-s1", "unconfirmed-s1",
        "omitted-s1", "deferred-s1", "analysis-code-bool",
        "plan-code-bool", "plan-analysis-code-mismatch",
        "plan-analysis-rail-mismatch", "plan-analysis-timber-mismatch",
        "missing-exclusion-reason", "empty-exclusion-reason",
        "blank-exclusion-reason", "nontext-exclusion-reason",
    ):
        analysis, plan = copy.deepcopy((base_analysis, base_plan))
        position = analysis["positions"][0]
        instance = plan["instances"][0]
        if label == "duplicate-analysis":
            analysis["positions"].append(copy.deepcopy(position))
        elif label == "missing-analysis-id":
            del position["stable_chair_position_identity"]
        elif label == "empty-analysis-id":
            position["stable_chair_position_identity"] = ""
        elif label == "unknown-plan-id":
            instance["chair_position_identity"] = "unknown"
        elif label == "missing-plan-id":
            del instance["chair_position_identity"]
        elif label == "duplicate-plan-id":
            plan["instances"].append(copy.deepcopy(instance))
        elif label == "duplicate-across-plan-kinds":
            plan["analytical_only"].append({
                "chair_position_identity": "b", "reason": "Duplicated",
            })
        elif label == "unaccounted-position":
            plan["instances"].pop(0)
        elif label == "all-s1-unresolved":
            for item in plan["instances"][:2]:
                plan["analytical_only"].append(unresolved_record(item))
            del plan["instances"][:2]
        elif label == "empty-s1":
            analysis["positions"] = analysis["positions"][2:]
            plan["instances"] = plan["instances"][2:]
        elif label == "unconfirmed-s1":
            position["assignment_status"] = "open"
        elif label == "omitted-s1":
            position["deliberate_omission"] = True
        elif label == "deferred-s1":
            position["special_assignment_deferred"] = True
        elif label == "analysis-code-bool":
            position["chair_code"] = True
        elif label == "plan-code-bool":
            instance["chair_code"] = True
        elif label == "plan-analysis-code-mismatch":
            instance["chair_code"] = 7
        elif label == "plan-analysis-rail-mismatch":
            instance["rail_identity"] = "other-rail"
        elif label == "plan-analysis-timber-mismatch":
            instance["timber_identity"] = "other-timber"
        elif label == "missing-exclusion-reason":
            del plan["analytical_only"][0]["reason"]
        elif label == "empty-exclusion-reason":
            plan["analytical_only"][0]["reason"] = ""
        elif label == "blank-exclusion-reason":
            plan["analytical_only"][0]["reason"] = "  "
        elif label == "nontext-exclusion-reason":
            plan["analytical_only"][0]["reason"] = None
        yield label, module, analysis, plan


def validate_resolved_only_selection():
    """Keep valid S1s and explicitly account for an unavailable S1 frame."""
    module, analysis, plan = selection_records()
    unresolved = unresolved_record(plan["instances"].pop(0))
    plan["analytical_only"].append(unresolved)
    original = copy.deepcopy((analysis, plan))
    placements, excluded = _select_positions(module, analysis, plan)
    assert tuple(item.position_id for item in placements) == ("a",)
    assert placements[0] == prepare_s1_placements([source_record("a")])[0]
    assert [item["position_id"] for item in excluded] == ["b", "joint", "open"]
    assert excluded[0] == {
        "position_id": "b", "chair_code": 1,
        "rail_id": unresolved["rail_identity"],
        "timber_id": unresolved["timber_identity"],
        "reason": unresolved["reason"],
    }
    assert len(placements) + len(excluded) == len(analysis["positions"])
    assert (analysis, plan) == original
    return 1


def validate_selection_accounting():
    """Test pure extraction only; no fake document is native evidence."""
    module, analysis, plan = selection_records()
    original = copy.deepcopy((analysis, plan))
    placements, excluded = _select_positions(module, analysis, plan)
    assert tuple(item.position_id for item in placements) == ("a", "b")
    assert [item["position_id"] for item in excluded] == ["joint", "open"]
    assert excluded[0]["chair_code"] == 7
    assert excluded[1]["reason"] == "Unresolved"
    assert len(placements) + len(excluded) == len(analysis["positions"])
    assert (analysis, plan) == original
    failures = []
    count = 0
    for label, module, analysis, plan in selection_rejections():
        try:
            _select_positions(module, analysis, plan)
        except ValueError:
            pass
        except Exception as error:
            failures.append((label, type(error).__name__, str(error)))
        else:
            failures.append((label, "accepted"))
        count += 1
    assert not failures, failures
    return count + 1


def validate_source_context():
    """Bind unrounded context and propagate the host's stale-analysis error."""
    module, analysis, plan = selection_records()
    module.TURNOUT_SIZE_C10 = "REA C10 natural"
    module.TURNOUT_DEFAULT_SCALE = 76.2
    config = {"turnout_id": "TO-001", "size": "REA C10 natural"}
    settings = {"future_chair_embed_depth": 0.2}
    rails = [{"stable_identity": "rail-one", "points": [[1, 2], [3, 4]]}]
    timbers = [{"stable_identity": "timber-one", "centre": [2, 3]}]
    current = ["turnout", config, analysis, settings, rails, timbers]
    module._chair_generation_context = lambda *args: tuple(current)
    module._A8A7B15_BUILD_SOLID_PLAN = lambda *args: plan

    def reject_cached_plan(*args):
        raise AssertionError("Rounded cached plan must not bind this preview")

    module._chair_build_solid_plan = reject_cached_plan
    original = copy.deepcopy(current)
    signature, *_rest = _source_context(module, object(), "TO-001")
    assert current == original
    assert _source_context(module, object(), "TO-001")[0] == signature
    previous_z = plan["instances"][0]["base_z"]
    plan["instances"][0]["base_z"] += 1e-10
    assert round(plan["instances"][0]["base_z"], 6) == round(previous_z, 6)
    assert plan["solid_signature"] == "rounded-solid-signature"
    assert _source_context(module, object(), "TO-001")[0] != signature
    plan["instances"][0]["base_z"] = previous_z
    assert _source_context(module, object(), "TO-001")[0] == signature
    for index in range(len(current)):
        if index == 0:
            continue
        before = copy.deepcopy(current[index])
        if isinstance(current[index], list):
            current[index][0]["changed-context"] = True
        else:
            current[index]["changed-context"] = True
        assert _source_context(module, object(), "TO-001")[0] != signature
        current[index] = before
    for field, value in (("size", "unsupported"), ("turnout_id", "TO-002")):
        before = current[1][field]
        current[1][field] = value
        assert_rejected(
            lambda: _source_context(module, object(), "TO-001"), field,
        )
        current[1][field] = before
    for scale in (True, 0, 152.4, "76.2", math.nan):
        module.TURNOUT_DEFAULT_SCALE = scale
        assert_rejected(
            lambda: _source_context(module, object(), "TO-001"),
            "scale-" + repr(scale),
        )
    module.TURNOUT_DEFAULT_SCALE = 76.2
    current[0] = "crossover"
    assert_rejected(
        lambda: _source_context(module, object(), "TO-001"), "wrong-kind",
    )
    stale_error = ValueError("Existing analysis is stale")

    def stale_context(*args):
        raise stale_error

    module._chair_generation_context = stale_context
    try:
        _source_context(module, object(), "TO-001")
    except ValueError as error:
        assert error is stale_error
    else:
        raise AssertionError("Stale analysis was accepted")
    return 18


def main():
    results = {
        "known_transforms": validate_known_transforms(),
        "rigid_distances": validate_rigid_distances(),
        "ordering_and_immutability": validate_order_and_immutability(),
        "rejections": validate_rejections(),
        "source_context": validate_source_context(),
        "resolved_only_selection": validate_resolved_only_selection(),
        "selection_accounting": validate_selection_accounting(),
    }
    print(results)
    print(SENTINEL)


if __name__ == "__main__":
    main()
