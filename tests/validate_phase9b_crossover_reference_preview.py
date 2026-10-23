#!/usr/bin/env python3
"""Prove crossover preview accounting with invented host records.

Exercise the additive command, current B4 context, full source binding and
refusals. These doubles establish no native geometry or railway fit.
"""

import copy
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_reference_preview as binding,
)
from validate_phase9b_l1_reference_preview import _session  # noqa: E402
from validate_phase9b_s1_reference_preview import (  # noqa: E402
    assert_rejected,
    source_record,
    unresolved_record,
)
from validate_phase9b_s1_s1j_reference_preview import (  # noqa: E402
    ShapeDouble,
)


SENTINEL = "Phase 9B crossover preview standalone validation passed"


def source_double():
    """Represent two C10 constituents and their current resolved timbers."""
    analysis = {"positions": [], "geometry_signature": "invented-xo"}
    plan = {"instances": [], "analytical_only": []}
    for name, code, selected in (
        ("s1-a", 1, True), ("s1-b", 1, True), ("s1j-a", 7, True),
        ("unresolved-s1", 1, False), ("slide", 2, False),
        ("deferred-l1", 5, False), ("omitted", 0, False),
    ):
        instance = source_record(name, chair_code=code)
        position = {
            "stable_chair_position_identity": name,
            "rail_identity": instance["rail_identity"],
            "timber_identity": instance["timber_identity"],
            "chair_code": code, "assignment_status": "confirmed",
            "deliberate_omission": code == 0,
            "special_assignment_deferred": code == 5,
        }
        if code == 5:
            position["assignment_status"] = "deferred"
        analysis["positions"].append(position)
        if selected:
            plan["instances"].append(instance)
        else:
            item = unresolved_record(instance)
            item["reason"] = "Original unresolved decision: " + name
            plan["analytical_only"].append(item)
    timber_id = analysis["positions"][0]["timber_identity"]
    timbers = [{"stable_identity": timber_id, "length_mm": 20.0}]
    rails = [{"stable_identity": analysis["positions"][0]["rail_identity"]}]
    config = {
        "crossover_id": "XO-001", "size": "C10",
        "turnout_a_config": {"turnout_id": "XO-A", "size": "C10"},
        "turnout_b_config": {"turnout_id": "XO-B", "size": "C10"},
        "b4_result": {"applied": True, "resolved_timbers": timbers},
    }
    settings = {"future_chair_embed_depth": 0.1}
    objects = {
        role: SimpleNamespace(Name=role, GeneratedRole=role,
                              Shape=ShapeDouble(role))
        for role in ("rails", "resolved")
    }
    document = SimpleNamespace(Name="Source", getObject=objects.get)
    documents = {document.Name: document}
    state = SimpleNamespace(kind="crossover", current=True,
                            context_calls=[], objects=list(objects.values()))

    def context(_document, kind, identifier):
        state.context_calls.append((kind, identifier))
        return state.kind, config, analysis, settings, rails, timbers

    module = SimpleNamespace(
        CHAIR_ASSIGNMENT_CONFIRMED="confirmed", TURNOUT_SIZE_C10="C10",
        TURNOUT_DEFAULT_SCALE=76.2, CROSSOVER_RAIL_ROLE="rails",
        CROSSOVER_B4_ROLE="resolved", _chair_generation_context=context,
        _A8A7B15_BUILD_SOLID_PLAN=lambda *_args: plan,
        _crossover_objects=lambda *_args: state.objects,
        object_string_property=lambda obj, name, default: getattr(
            obj, name, default,
        ),
        crossover_inherited_timber_records=lambda *_args: ["inherited"],
        _crossover_b4_result_is_current=lambda *_args: state.current,
    )
    app = SimpleNamespace(getDocument=documents.get)
    return SimpleNamespace(module=module, document=document, app=app,
                           config=config, analysis=analysis, plan=plan,
                           timbers=timbers, objects=objects, state=state)


def call(source, factory):
    with patch.dict(sys.modules, {"FreeCAD": source.app}):
        return binding.preview_s1_s1j_crossover_reference_chairs(
            source.module, source.document, "XO-001", "s1-package",
            "s1-manifest", "s1j-package", "s1j-manifest", "request", factory,
        )


def validate_accounting():
    source = source_double()
    before = copy.deepcopy((source.config, source.analysis, source.plan))

    def factory(*args):
        assert args[:5] == (
            "s1-package", "s1-manifest", "s1j-package", "s1j-manifest",
            "request",
        )
        s1, s1j, shapes, receipt, verify = args[5:]
        assert [p.position_id for p in s1] == ["s1-a", "s1-b"]
        assert [p.position_id for p in s1j] == ["s1j-a"]
        assert receipt["crossover_id"] == "XO-001"
        assert "turnout_id" not in receipt
        assert receipt["analysis_position_count"] == 7
        assert (receipt["confirmed_s1_count"],
                receipt["confirmed_s1j_count"]) == (3, 1)
        assert receipt["selected_count"] == 3
        assert receipt["unresolved_confirmed_count"] == 1
        excluded = receipt["excluded_positions"]
        assert {p["position_id"] for p in excluded} == {
            "unresolved-s1", "slide", "deferred-l1", "omitted",
        }
        for item in excluded:
            assert item["reason"] == (
                "Original unresolved decision: " + item["position_id"]
            )
        for shape, obj in zip(shapes, source.objects.values()):
            assert shape is not obj.Shape and shape.isSame(obj.Shape)
        verify()
        return receipt

    receipt = call(source, factory)
    assert receipt["coverage_summary"] == (
        "3/4 S1/S1J; 1 unresolved; 2/3 S1; 1/1 S1J"
    )
    assert source.state.context_calls == [("crossover", "XO-001")] * 2
    assert (source.config, source.analysis, source.plan) == before
    return 7


def validate_context_refusals():
    cases = (
        "kind", "identity", "size", "a-size", "b-size", "missing-a",
        "missing-b", "scale", "missing-b4", "unapplied-b4", "stale-b4",
        "fallback-timbers", "missing-rails", "missing-timbers",
        "duplicate-role", "null-shape", "invalid-shape", "closed-source",
    )
    for case in cases:
        source = source_double()
        if case == "kind":
            source.state.kind = "turnout"
        elif case == "identity":
            source.config["crossover_id"] = "different"
        elif case == "size":
            source.config["size"] = "unsupported"
        elif case in ("a-size", "b-size"):
            source.config[f"turnout_{case[0]}_config"]["size"] = "unsupported"
        elif case in ("missing-a", "missing-b"):
            source.config.pop(f"turnout_{case[-1]}_config")
        elif case == "scale":
            source.module.TURNOUT_DEFAULT_SCALE = 48.0
        elif case == "missing-b4":
            source.config.pop("b4_result")
        elif case == "unapplied-b4":
            source.config["b4_result"]["applied"] = False
        elif case == "stale-b4":
            source.state.current = False
        elif case == "fallback-timbers":
            source.config["b4_result"]["resolved_timbers"] = []
        elif case in ("missing-rails", "missing-timbers"):
            role = "rails" if case == "missing-rails" else "resolved"
            source.state.objects.remove(source.objects[role])
        elif case == "duplicate-role":
            source.state.objects.append(copy.copy(source.objects["rails"]))
        elif case == "null-shape":
            source.objects["rails"].Shape.isNull = lambda: True
        elif case == "invalid-shape":
            source.objects["resolved"].Shape.isValid = lambda: False
        else:
            source.app.getDocument = lambda _name: None

        def forbidden(*_args):
            raise AssertionError("Invalid context reached native construction")

        assert_rejected(lambda: call(source, forbidden), case)
    return len(cases)


def validate_late_source_refusals():
    cases = (
        "datum", "timber", "object", "shape", "closed", "b4", "duplicate-role",
    )
    for case in cases:
        source = source_double()

        def factory(*args):
            if case == "datum":
                source.plan["instances"][0]["base_z"] += 1e-10
            elif case == "timber":
                source.timbers[0]["length_mm"] += 1e-10
            elif case == "object":
                source.objects["rails"] = copy.copy(source.objects["rails"])
            elif case == "shape":
                source.objects["rails"].Shape = ShapeDouble("changed")
            elif case == "closed":
                source.app.getDocument = lambda _name: None
            elif case == "b4":
                source.state.current = False
            else:
                source.state.objects.append(copy.copy(source.objects["rails"]))
            args[-1]()

        assert_rejected(lambda: call(source, factory), case)
    return len(cases)


def validate_workflow():
    session = _session()
    token = object()
    session._s1_s1j_reference_preview_factory = token
    arguments = ("document", "XO-001", "s1", "m1", "s1j", "m1j", "request")
    with patch.object(binding, "preview_s1_s1j_crossover_reference_chairs",
                      return_value={"owned": "preview"}) as operation:
        assert session.preview_s1_s1j_crossover_reference_chairs(
            *arguments,
        ) == {"owned": "preview"}
        operation.assert_called_once_with(session.module, *arguments, token)
    return 1


def main():
    print({
        "accounted_positions": validate_accounting(),
        "context_refusals": validate_context_refusals(),
        "late_source_refusals": validate_late_source_refusals(),
        "workflow": validate_workflow(),
    })
    print(SENTINEL)


if __name__ == "__main__":
    main()
