#!/usr/bin/env python3
"""Prove private frame recovery without changing source or legacy plans."""

import copy
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_reference_preview as binding,
)
import validate_phase9b_s1_s1j_reference_preview as combined  # noqa: E402
from validate_phase9b_s1_reference_preview import (  # noqa: E402
    assert_rejected,
)


def source_case():
    """Use invented sloping faces with an exact vertical normal section."""
    module, document, app, _captures, _objects, plan = combined.source_double()
    context = list(module._chair_generation_context())
    analysis = context[2]
    for position in analysis["positions"]:
        position.update(centre_point=[10.0, 20.0],
                        local_rail_tangent=[1.0, 0.0])
    rails = [{
        "stable_identity": "TO-001:rail:stock",
        "gauge_face_points": [[8.0, 18.0], [12.0, 19.0]],
        "outer_face_points": [[8.0, 21.0], [12.0, 22.0]],
    }]
    timbers = [{"stable_identity": "TO-001:timber:01"}]
    context[4:] = rails, timbers
    module._chair_generation_context = lambda *_args: tuple(context)
    module._chair_supported_physical_position = lambda _position: (True, "")
    return module, document, app, context, plan


def call(source, factory):
    module, document, app, _context, _plan = source
    with patch.dict(sys.modules, {"FreeCAD": app}):
        return combined.combined_call(module, document, factory)


def validate_complete_preview():
    source = source_case()
    module, _document, _app, context, plan = source
    before = copy.deepcopy((context, plan))
    legacy = binding._select_s1_s1j_positions(module, context[2], plan)

    def factory(*args):
        s1, s1j, _shapes, receipt, verify = args[5:]
        assert (len(s1), len(s1j)) == (54, 5), "Missing supported placements"
        for current, previous in zip((s1, s1j), legacy[:2]):
            by_id = {item.position_id: item for item in current}
            assert all(by_id[item.position_id] == item for item in previous)
        previous_ids = {item.position_id for item in (*legacy[0], *legacy[1])}
        recovered = [item for item in (*s1, *s1j)
                     if item.position_id not in previous_ids]
        assert len(recovered) == 18
        for item in recovered:
            assert item.origin_mm == (10.0, 20.0, 1.8)
            assert item.x_axis == (1.0, 0.0)
            assert item.y_axis == (0.0, 1.0)
        verify()
        return receipt

    receipt = call(source, factory)
    assert receipt["coverage_summary"] == (
        "59/59 S1/S1J; 0 unresolved; 54/54 S1; 5/5 S1J"
    )
    assert len(receipt["excluded_positions"]) == 109
    recovered = receipt["recovered_positions"]
    assert len(recovered) == 18
    assert [item["position_id"] for item in recovered] == sorted(
        item["position_id"] for item in recovered
    )
    old_reasons = {item["position_id"]: item["reason"] for item in legacy[2]}
    for item in (*recovered, *receipt["excluded_positions"]):
        reason = item.get("original_reason", item.get("reason"))
        assert reason == old_reasons[item["position_id"]]
    assert (context, plan) == before
    return 59


def validate_refusals():
    """Missing evidence must retain the old exclusion and all old frames."""
    cases = (
        "missing-face", "same-side", "multiple-crossings", "missing-rail",
        "missing-timber", "unconfirmed", "omitted", "deferred",
        "unsupported", "other-reason",
    )
    for case in cases:
        source = source_case()
        module, _document, _app, context, plan = source
        if case == "missing-face":
            context[4][0]["gauge_face_points"] = []
        elif case == "same-side":
            context[4][0]["gauge_face_points"] = [[8, 23], [12, 24]]
        elif case == "multiple-crossings":
            context[4][0]["gauge_face_points"] = [
                [8, 18], [12, 18], [12, 17], [8, 17],
            ]
        elif case == "missing-rail":
            context[4].clear()
        elif case == "missing-timber":
            context[5].clear()
        elif case == "unsupported":
            module._chair_supported_physical_position = (
                lambda _position: (False, "No source-dimensional footprint")
            )
        else:
            excluded_ids = {item["chair_position_identity"]
                            for item in plan["analytical_only"]}
            for position in context[2]["positions"]:
                if position["stable_chair_position_identity"] in excluded_ids:
                    if case == "unconfirmed":
                        position["assignment_status"] = "unconfirmed"
                    elif case == "omitted":
                        position["deliberate_omission"] = True
                    elif case == "deferred":
                        position["special_assignment_deferred"] = True
            if case == "other-reason":
                for item in plan["analytical_only"]:
                    item["reason"] = "The source does not define this frame."
        before = copy.deepcopy((context, plan))

        def factory(*args):
            assert (len(args[5]), len(args[6])) == (37, 4), case
            args[-1]()
            return args[-2]

        receipt = call(source, factory)
        assert receipt["recovered_positions"] == [], case
        assert len(receipt["excluded_positions"]) == 127, case
        assert (context, plan) == before, case
    return len(cases)


def validate_ambiguous_context():
    for case in ("duplicate-rail", "duplicate-timber", "inconsistent-datum"):
        source = source_case()
        _module, _document, _app, context, plan = source
        if case == "inconsistent-datum":
            plan["instances"][0]["base_z"] += 0.01
        else:
            records = context[4 if case == "duplicate-rail" else 5]
            records.append(copy.deepcopy(records[0]))

        def factory(*_args):
            raise AssertionError("Ambiguous input reached native preparation")

        assert_rejected(lambda: call(source, factory), case)
    return 3


def validate_final_source_check():
    for field in ("gauge_face_points", "outer_face_points"):
        source = source_case()
        context = source[3]

        def factory(*args):
            assert len(args[5]) + len(args[6]) == 59
            context[4][0][field][0][1] += 1e-9
            args[-1]()

        assert_rejected(lambda: call(source, factory), field)
    return 2


def main():
    print({
        "placements": validate_complete_preview(),
        "refusals": validate_refusals(),
        "ambiguous_context": validate_ambiguous_context(),
        "source_mutations": validate_final_source_check(),
    })
    print("Phase 9B chair frame preview standalone validation passed")


if __name__ == "__main__":
    main()
