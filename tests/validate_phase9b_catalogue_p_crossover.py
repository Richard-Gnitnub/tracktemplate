#!/usr/bin/env python3
"""Check retained P placement on two current crossover constituents.

Invented coordinates exercise ownership, frame and source-state boundaries.
Native component reuse and actual railway fit need separate host evidence.
"""

import copy
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
)
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain.chair_placement import PPlacement  # noqa: E402
from validate_phase9b_catalogue_p_placement import source_case  # noqa: E402
from validate_phase9b_s1_s1j_reference_preview import (  # noqa: E402
    ShapeDouble,
)


SENTINEL = "Phase 9B catalogue P crossover standalone validation passed"


def crossover_source():
    """Join two independent P fixtures, with B facing the opposite way."""
    source = source_case()
    module, document, app, context, plan, objects = source
    config = {
        "crossover_id": "XO-001", "size": module.TURNOUT_SIZE_C10,
        "track_gauge": 16.5, "flangeway": 1.0, "template_thickness": 1.0,
    }
    rails, timbers, positions, instances, exclusions = [], [], [], [], []
    for side in ("A", "B"):
        _module, _doc, _app, old, old_plan, _objects = source_case()
        parent_id = "XO-001-" + side + "001"
        constituent = dict(old[1], turnout_id=parent_id,
                           template_thickness=1.0)
        config["turnout_" + side.lower() + "_id"] = parent_id
        config["turnout_" + side.lower() + "_config"] = constituent

        def rename(value):
            return side + ":" + value

        for rail in old[4]:
            rail.update(
                stable_identity=rename(rail["stable_identity"]),
                parent_turnout_identity=parent_id,
                parent_crossover_identity="XO-001", turnout_side=side,
            )
            if side == "B":
                for field in ("gauge_face_points", "outer_face_points"):
                    rail[field] = [[100 - x, 100 - y]
                                   for x, y in rail[field]]
        for timber in old[5]:
            timber.update(
                stable_identity=rename(timber["stable_identity"]),
                parent_turnout_identity=parent_id,
                crossover_identity="XO-001", turnout_side=side,
            )
        for position in old[2]["positions"]:
            position["stable_chair_position_identity"] = rename(
                position["stable_chair_position_identity"],
            )
            position["rail_identity"] = rename(position["rail_identity"])
            position["timber_identity"] = rename(position["timber_identity"])
            if position["chair_code"] == 2:
                position.update(parent_turnout_identity=parent_id,
                                parent_crossover_identity="XO-001")
                if side == "B":
                    x, y = position["centre_point"]
                    position["centre_point"] = [100 - x, 100 - y]
                    position["local_rail_tangent"] = [-1, 0]
        for record in old_plan["instances"] + old_plan["analytical_only"]:
            for field in ("chair_position_identity", "rail_identity",
                          "timber_identity"):
                record[field] = rename(record[field])
            if "base_z" in record:
                record["base_z"] = 0.8
        rails.extend(old[4])
        timbers.extend(old[5])
        positions.extend(old[2]["positions"])
        instances.extend(old_plan["instances"])
        exclusions.extend(old_plan["analytical_only"])

    config["b4_result"] = {"applied": True, "resolved_timbers": timbers}
    analysis = {"positions": positions, "geometry_signature": "invented-xo"}
    context[:] = ["crossover", config, analysis,
                  context[3], rails, timbers]
    plan.update(entity_id="XO-001", entity_kind="crossover",
                instances=instances, analytical_only=exclusions)
    objects["resolved"] = objects.pop("timbers")
    for role, obj in objects.items():
        obj.Name = role
        obj.GeneratedRole = role
    state = SimpleNamespace(current=True)
    module.CROSSOVER_RAIL_ROLE = "rails"
    module.CROSSOVER_B4_ROLE = "resolved"
    module._crossover_objects = lambda *_args: list(objects.values())
    module.object_string_property = getattr
    module.crossover_inherited_timber_records = lambda *_args: ["inherited"]
    module._crossover_b4_result_is_current = lambda *_args: state.current
    return (*source, state)


def preview(source, factory):
    module, document, app, *_rest = source
    with patch.dict(sys.modules, {"FreeCAD": app}):
        return binding.preview_private_catalogue_p_crossover_chairs(
            module, document, "XO-001", "private-catalogue.json", factory,
        )


class CatalogueCrossoverTests(unittest.TestCase):
    def reject(self, source):
        def forbidden(*_args):
            self.fail("Unsupported crossover reached native creation")

        with self.assertRaises(ValueError):
            preview(source, forbidden)

    def test_complete_partition_rigid_frames_and_preservation(self):
        source = crossover_source()
        _module, _doc, _app, context, plan, objects, _state = source
        before = copy.deepcopy((context, plan))

        def factory(path, placements, shapes, receipt, verify):
            self.assertEqual(path, "private-catalogue.json")
            self.assertEqual(len(placements), 28)
            self.assertTrue(all(type(p) is PPlacement for p in placements))
            self.assertEqual([p.position_id for p in placements],
                             sorted(p.position_id for p in placements))
            for placement in placements:
                number = int(placement.position_id[-1])
                if "main-side" in placement.position_id:
                    expected = (number * 2 + 3, 24, 5.8)
                else:
                    expected = (number * 2 - 3, 36, 5.8)
                if placement.position_id.startswith("B:"):
                    expected = (100 - expected[0], 100 - expected[1], 5.8)
                self.assertEqual(placement.transform_point((3, 4, 5)),
                                 expected)
            for shape, obj in zip(shapes, objects.values()):
                self.assertIsNot(shape, obj.Shape)
                self.assertTrue(shape.isSame(obj.Shape))
            verify()
            return receipt

        receipt = preview(source, factory)
        self.assertEqual(receipt["crossover_id"], "XO-001")
        self.assertNotIn("turnout_id", receipt)
        self.assertEqual(receipt["source_kind"], "crossover")
        self.assertEqual(receipt["timber_context"],
                         "current B4 resolved timbers")
        self.assertEqual(receipt["analysis_position_count"], 34)
        self.assertEqual(receipt["selected_p_count"], 28)
        selected = receipt["selected_positions"]
        remaining = receipt["remaining_positions"]
        selected_ids = {item["position_id"] for item in selected}
        remaining_ids = {item["position_id"] for item in remaining}
        self.assertEqual(len(remaining), 6)
        self.assertTrue(selected_ids.isdisjoint(remaining_ids))
        self.assertEqual(selected_ids | remaining_ids, {
            item["stable_chair_position_identity"]
            for item in context[2]["positions"]
        })
        self.assertEqual(receipt["original_analytical_exclusions"],
                         plan["analytical_only"])
        for original in plan["analytical_only"]:
            identity = original["chair_position_identity"]
            if identity in remaining_ids:
                remaining_record = next(item for item in remaining
                                        if item["position_id"] == identity)
                self.assertEqual(remaining_record["reason"],
                                 original["reason"])
        for item in selected:
            self.assertEqual(item["key_direction_sign"], 0)
            self.assertIn(item["original_exclusion"], plan["analytical_only"])
        self.assertFalse(receipt["source_document_mutation"])
        self.assertEqual((context, plan), before)
        receipt["original_analytical_exclusions"][0]["reason"] = "changed"
        self.assertEqual((context, plan), before)

    def test_placement_count_follows_current_records(self):
        source = crossover_source()
        context, plan = source[3], source[4]
        removed = context[2]["positions"].pop(0)
        identity = removed["stable_chair_position_identity"]
        plan["analytical_only"][:] = [
            item for item in plan["analytical_only"]
            if item["chair_position_identity"] != identity
        ]

        def factory(_path, placements, _shapes, receipt, verify):
            self.assertEqual(len(placements), 27)
            self.assertNotIn(identity, {item.position_id for item in placements})
            verify()
            return receipt

        receipt = preview(source, factory)
        self.assertEqual(receipt["analysis_position_count"], 33)
        self.assertEqual(receipt["selected_p_count"], 27)
        self.assertEqual(len(receipt["remaining_positions"]), 6)

    def test_each_constituent_must_match_supported_inputs(self):
        for side in ("a", "b"):
            for field, value in (
                ("size", "other"), ("turnout_id", "unknown"),
                ("track_gauge", 18.83), ("flangeway", 1.000000001),
                ("template_thickness", 1.000000001),
                ("template_thickness", math.nan),
                ("template_thickness", True),
            ):
                with self.subTest(side=side, field=field, value=value):
                    source = crossover_source()
                    config = source[3][1]
                    config["turnout_" + side + "_config"][field] = value
                    self.reject(source)
        for case in ("missing-parent", "same-parent", "root-gauge",
                     "root-datum", "plan-kind", "plan-id", "full-profile"):
            with self.subTest(case=case):
                source = crossover_source()
                config, plan = source[3][1], source[4]
                if case == "missing-parent":
                    del config["turnout_b_id"]
                elif case == "same-parent":
                    config["turnout_b_id"] = config["turnout_a_id"]
                    config["turnout_b_config"]["turnout_id"] = (
                        config["turnout_a_id"]
                    )
                elif case == "root-gauge":
                    config["track_gauge"] = 18.83
                elif case == "root-datum":
                    config["template_thickness"] += 1e-9
                elif case.startswith("plan-"):
                    plan["entity_" + case[5:]] = "other"
                else:
                    plan["rail_profile"]["rail_foot_width_mm"] += 1e-9
                self.reject(source)

    def test_current_b4_required_even_with_confirmed_assignments(self):
        for case in ("missing", "unapplied", "stale", "different-timbers"):
            with self.subTest(case=case):
                source = crossover_source()
                config, state = source[3][1], source[-1]
                if case == "missing":
                    del config["b4_result"]
                elif case == "unapplied":
                    config["b4_result"]["applied"] = False
                elif case == "stale":
                    state.current = False
                else:
                    config["b4_result"]["resolved_timbers"] = copy.deepcopy(
                        source[3][5][:-1],
                    )
                self.reject(source)

    def test_crossed_parent_or_side_ownership_is_rejected(self):
        for record_kind, field, value in (
            ("position", "parent_turnout_identity", "XO-001-B001"),
            ("position", "parent_crossover_identity", "XO-002"),
            ("position", "assignment_status", "deferred"),
            ("position", "special_assignment_deferred", True),
            ("position", "stale_signature_state", True),
            ("rail", "parent_turnout_identity", "XO-001-B001"),
            ("rail", "parent_crossover_identity", "XO-002"),
            ("rail", "turnout_side", "B"),
            ("timber", "parent_turnout_identity", "XO-001-B001"),
            ("timber", "crossover_identity", "XO-002"),
            ("timber", "turnout_side", "B"),
            ("timber", "prototype_reference", "S8"),
        ):
            with self.subTest(record=record_kind, field=field):
                source = crossover_source()
                context = source[3]
                records = {"position": context[2]["positions"],
                           "rail": context[4], "timber": context[5]}
                records[record_kind][0][field] = value
                self.reject(source)

    def test_late_source_changes_reject_before_commit(self):
        for case in ("parent", "b4", "datum", "position", "profile",
                     "shape", "object"):
            with self.subTest(case=case):
                source = crossover_source()
                _module, _doc, _app, context, plan, objects, state = source

                def factory(_path, _placements, _shapes, _receipt, verify):
                    if case == "parent":
                        context[1]["turnout_b_config"]["flangeway"] += 1e-9
                    elif case == "b4":
                        state.current = False
                    elif case == "datum":
                        plan["instances"][0]["base_z"] += 1e-10
                    elif case == "position":
                        context[2]["positions"][0]["centre_point"][0] += 1e-9
                    elif case == "profile":
                        plan["rail_profile"]["rail_foot_width_mm"] += 1e-9
                    elif case == "shape":
                        objects["rails"].Shape = ShapeDouble("changed")
                    else:
                        objects["rails"] = copy.copy(objects["rails"])
                    verify()

                with self.assertRaises(ValueError):
                    preview(source, factory)

    def test_session_routes_exact_crossover_inputs(self):
        calls = []
        session = SimpleNamespace(
            module=object(), _private_catalogue_p_preview_factory=object(),
            routing_record=lambda: calls.append("route"),
        )
        document = object()

        def operation(*args):
            self.assertEqual(calls, ["route"])
            self.assertEqual(args, (
                session.module, document, "XO-001", "catalogue.json",
                session._private_catalogue_p_preview_factory,
            ))
            return "receipt"

        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        with patch.object(binding,
                          "preview_private_catalogue_p_crossover_chairs",
                          operation):
            result = session_type.preview_private_catalogue_p_crossover_chairs(
                session, document, "XO-001", "catalogue.json",
            )
        self.assertEqual(result, "receipt")
        with self.assertRaises(ValueError):
            preview(crossover_source(), None)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CatalogueCrossoverTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)


if __name__ == "__main__":
    main()
