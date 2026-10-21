#!/usr/bin/env python3
"""Prove combined C10 accounting with invented data and adapter doubles.

These checks cover the compatibility contract, not native geometry or GUI
behaviour. Both families keep their existing placement and exclusion rules.
"""

import copy
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility.chair_reference_preview import (  # noqa: E402
    _select_s1_s1j_positions,
    preview_s1_reference_chairs,
    preview_s1j_reference_chairs,
    preview_s1_s1j_reference_chairs,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    S1Placement,
    S1JPlacement,
)
import validate_phase9b_s1_reference_preview as s1_tests  # noqa: E402


def combined_records():
    """Invent a 168-position partition independent of private source data."""
    module = SimpleNamespace(CHAIR_ASSIGNMENT_CONFIRMED="confirmed")
    analysis = {"positions": [], "geometry_signature": "invented-analysis"}
    plan = {"instances": [], "analytical_only": []}
    for family, code, count, resolved in (
        ("s1", 1, 54, 37), ("s1j", 7, 5, 4), ("other", 2, 109, 1),
    ):
        for index in range(count):
            identity = f"{family}-{index:03d}"
            instance = s1_tests.source_record(identity, chair_code=code)
            analysis["positions"].append({
                "stable_chair_position_identity": identity,
                "rail_identity": instance["rail_identity"],
                "timber_identity": instance["timber_identity"],
                "chair_code": code, "assignment_status": "confirmed",
                "deliberate_omission": False,
                "special_assignment_deferred": False,
            })
            if index < resolved:
                plan["instances"].append(instance)
            else:
                unresolved = s1_tests.unresolved_record(instance)
                if family == "other":
                    unresolved["reason"] = "Separate definition required."
                plan["analytical_only"].append(unresolved)
    return module, analysis, plan


def validate_partition():
    module, analysis, plan = combined_records()
    original = copy.deepcopy((analysis, plan))
    s1, s1j, excluded = _select_s1_s1j_positions(module, analysis, plan)
    assert (len(s1), len(s1j), len(excluded)) == (37, 4, 127)
    assert all(type(item) is S1Placement for item in s1)
    assert all(type(item) is S1JPlacement for item in s1j)
    groups = [
        {item.position_id for item in s1},
        {item.position_id for item in s1j},
        {item["position_id"] for item in excluded},
    ]
    assert all(groups[i].isdisjoint(groups[j])
               for i in range(3) for j in range(i + 1, 3))
    assert set.union(*groups) == {
        item["stable_chair_position_identity"]
        for item in analysis["positions"]
    }
    assert [item["position_id"] for item in excluded] == sorted(groups[2])
    reasons = {item["position_id"]: item["reason"] for item in excluded}
    for item in plan["analytical_only"]:
        assert reasons[item["chair_position_identity"]] == item["reason"]
    assert "S1 and S1J" in reasons["other-000"]
    assert (analysis, plan) == original
    return 168


class ShapeDouble:
    """Expose only the source-identity contract used by compatibility."""

    def __init__(self, identity):
        self.identity = identity

    def isNull(self):
        return False

    def isValid(self):
        return True

    def copy(self):
        return ShapeDouble(self.identity)

    def isSame(self, other):
        return self.identity == other.identity


def source_double():
    module, analysis, plan = combined_records()
    config = {"turnout_id": "TO-001", "size": "C10"}
    settings = {"future_chair_embed_depth": 0.1}
    captures = []
    objects = {
        role: SimpleNamespace(Name=role, Shape=ShapeDouble(role))
        for role in ("rails", "timbers")
    }
    document = SimpleNamespace(Name="Source", getObject=objects.get)
    documents = {document.Name: document}

    def generation_context(*_args):
        captures.append("capture")
        return "turnout", config, analysis, settings, [], []

    module.TURNOUT_SIZE_C10 = "C10"
    module.TURNOUT_DEFAULT_SCALE = 76.2
    module.TURNOUT_RAIL_ROLE = "rails"
    module.TURNOUT_TIMBER_ROLE = "timbers"
    module._chair_generation_context = generation_context
    module._A8A7B15_BUILD_SOLID_PLAN = lambda *_args: plan
    module._turnout_objects_by_role = lambda *_args: objects
    app = SimpleNamespace(getDocument=documents.get)
    return module, document, app, captures, objects, plan


def combined_call(module, document, factory):
    return preview_s1_s1j_reference_chairs(
        module, document, "TO-001", "s1-package", "s1-manifest",
        "s1j-package", "s1j-manifest", "model-request", factory,
    )


def validate_common_context():
    module, document, app, captures, objects, _plan = source_double()

    def factory(*args):
        assert args[:5] == (
            "s1-package", "s1-manifest", "s1j-package", "s1j-manifest",
            "model-request",
        )
        s1, s1j, shapes, receipt, verify_source = args[5:]
        assert (len(s1), len(s1j)) == (37, 4)
        assert captures == ["capture"]
        for shape, obj in zip(shapes, objects.values()):
            assert shape is not obj.Shape and shape.isSame(obj.Shape)
        verify_source()
        assert captures == ["capture", "capture"]
        return receipt

    with patch.dict(sys.modules, {"FreeCAD": app}):
        receipt = combined_call(module, document, factory)
        singles = []
        for operation in (preview_s1_reference_chairs,
                          preview_s1j_reference_chairs):
            singles.append(operation(
                module, document, "TO-001", "package", "manifest", "request",
                lambda *args: args[-2],
            ))
    assert receipt["source_context_signature"] == (
        singles[0]["source_context_signature"]
    ) == singles[1]["source_context_signature"]
    assert receipt["analysis_position_count"] == 168
    for field, value in {
        "selected_s1_count": 37, "confirmed_s1_count": 54,
        "unresolved_confirmed_s1_count": 17,
        "selected_s1j_count": 4, "confirmed_s1j_count": 5,
        "unresolved_confirmed_s1j_count": 1,
        "selected_count": 41, "confirmed_count": 59,
        "unresolved_confirmed_count": 18,
    }.items():
        assert receipt[field] == value, (field, receipt[field])
    assert receipt["coverage_summary"] == (
        "41/59 S1/S1J; 18 unresolved; 37/54 S1; 4/5 S1J"
    )
    assert len(receipt["excluded_positions"]) == 127
    for single, family in zip(singles, ("s1", "s1j")):
        assert "selected_count" not in single
        assert single[f"selected_{family}_count"] == (
            receipt[f"selected_{family}_count"]
        )
    return 1


def validate_source_rejections():
    for defect in ("full-precision-datum", "shape", "closed", "object"):
        module, document, app, _captures, objects, plan = source_double()

        def factory(*args):
            if defect == "full-precision-datum":
                plan["instances"][0]["base_z"] += 1e-10
            elif defect == "shape":
                objects["rails"].Shape = ShapeDouble("changed")
            elif defect == "closed":
                app.getDocument = lambda _name: None
            else:
                objects["rails"] = SimpleNamespace(
                    Name="rails", Shape=ShapeDouble("rails"),
                )
            args[-1]()

        with patch.dict(sys.modules, {"FreeCAD": app}):
            s1_tests.assert_rejected(
                lambda: combined_call(module, document, factory), defect,
            )
    return 4


def validate_selection_rejections():
    count = 0
    for swap in (False, True):
        for label, module, analysis, plan in s1_tests.selection_rejections():
            if swap:
                for item in analysis["positions"] + plan["instances"]:
                    code = item.get("chair_code")
                    if type(code) is int and code in (1, 7):
                        item["chair_code"] = 8 - code
            s1_tests.assert_rejected(
                lambda: _select_s1_s1j_positions(module, analysis, plan), label,
            )
            count += 1
    return count


def main():
    print({
        "partition_positions": validate_partition(),
        "common_context": validate_common_context(),
        "source_rejections": validate_source_rejections(),
        "selection_rejections": validate_selection_rejections(),
    })
    print("Phase 9B combined S1/S1J preview standalone validation passed")


if __name__ == "__main__":
    main()
