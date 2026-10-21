#!/usr/bin/env python3
"""Prove family isolation and resolved-only S1J placement with invented data."""

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.domain.chair_placement import (  # noqa: E402
    S1JPlacement,
    prepare_s1_placements,
    prepare_s1j_placements,
)
from tracktemplate.compatibility.chair_reference_preview import (  # noqa: E402
    _select_positions,
    _select_s1j_positions,
)
import validate_phase9b_s1_reference_preview as s1_tests  # noqa: E402


def validate_family_and_frame():
    """Use a hand-calculable 3:4:5 frame; retain the exact source datum."""
    record = s1_tests.source_record(
        "joint", chair_code=7, centre_point=[10, 20], base_z=1.8000000001,
        outward_axis=[-0.8, 0.6], local_y_axis=[-0.6, -0.8],
    )
    original = copy.deepcopy(record)
    placement, = prepare_s1j_placements([record])
    assert type(placement) is S1JPlacement
    assert placement.transform_point((5, 0, 0)) == (13, 24, 1.8000000001)
    assert placement.transform_point((0, 5, 0)) == (6, 23, 1.8000000001)
    assert record == original
    record["centre_point"][0] = 999
    assert placement.origin_mm == (10, 20, 1.8000000001)
    try:
        placement.position_id = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("S1J placement was mutable")
    for operation, label in (
        (lambda: prepare_s1_placements([original]), "S1 accepts S1J"),
        (lambda: prepare_s1j_placements([s1_tests.source_record()]),
         "S1J accepts S1"),
        (lambda: prepare_s1j_placements([
            s1_tests.source_record(chair_code=7, local_y_axis=[1, 0]),
        ]), "reflected frame"),
        (lambda: prepare_s1j_placements([
            s1_tests.source_record(chair_code=7, outward_axis=[0.6, 0.8]),
        ]), "skewed frame"),
        (lambda: prepare_s1j_placements([
            s1_tests.source_record(chair_code=7.0),
        ]), "noninteger family"),
    ):
        s1_tests.assert_rejected(operation, label)
    return 5


def validate_resolved_only_selection():
    """Select one joint chair, keeping its unresolved peer and S1s explicit."""
    module, analysis, plan = s1_tests.selection_records()
    pending = copy.deepcopy(analysis["positions"][2])
    pending["stable_chair_position_identity"] = "joint-unresolved"
    analysis["positions"].append(pending)
    unresolved = s1_tests.unresolved_record(s1_tests.source_record(
        "joint-unresolved", chair_code=7,
    ))
    plan["analytical_only"].append(unresolved)
    original = copy.deepcopy((analysis, plan))
    selected, excluded = _select_s1j_positions(module, analysis, plan)
    assert tuple(item.position_id for item in selected) == ("joint",)
    assert type(selected[0]) is S1JPlacement
    assert [item["position_id"] for item in excluded] == [
        "a", "b", "joint-unresolved", "open",
    ]
    assert excluded[2]["reason"] == unresolved["reason"]
    assert excluded[2]["chair_code"] == 7
    assert len(selected) + len(excluded) == len(analysis["positions"])
    s1_selected, _s1_excluded = _select_positions(module, analysis, plan)
    assert {item.position_id for item in selected}.isdisjoint(
        item.position_id for item in s1_selected
    )
    assert (analysis, plan) == original
    return 1


def validate_shared_rejections():
    """Apply the established accounting witnesses with the two families swapped."""
    count = 0
    for label, module, analysis, plan in s1_tests.selection_rejections():
        for record in analysis["positions"] + plan["instances"]:
            code = record.get("chair_code")
            if type(code) is int and code in (1, 7):
                record["chair_code"] = 8 - code
        s1_tests.assert_rejected(
            lambda: _select_s1j_positions(module, analysis, plan), label,
        )
        count += 1
    return count


def main():
    print({
        "family_and_frame": validate_family_and_frame(),
        "resolved_only_selection": validate_resolved_only_selection(),
        "shared_rejections": validate_shared_rejections(),
    })
    print("Phase 9B S1J reference preview standalone validation passed")


if __name__ == "__main__":
    main()
