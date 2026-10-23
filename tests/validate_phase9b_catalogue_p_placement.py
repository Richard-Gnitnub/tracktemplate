#!/usr/bin/env python3
"""Check private P assignment, accounting and source preservation.

Invented coordinates and host doubles exercise the compatibility boundary.
These checks do not qualify retained native geometry or railway fit.
"""

import ast
import copy
from dataclasses import FrozenInstanceError
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
from validate_phase9b_s1_s1j_reference_preview import (  # noqa: E402
    ShapeDouble,
)


SENTINEL = "Phase 9B catalogue P placement standalone validation passed"


def source_case():
    """Invent two rail sides, seven switch timbers and three other records."""
    module = SimpleNamespace(
        TURNOUT_SIZE_C10="REA C10 natural", TURNOUT_DEFAULT_SCALE=76.2,
        CHAIR_ASSIGNMENT_CONFIRMED="confirmed",
        CHAIR_FAMILY_SLIDE="slide chair", CHAIR_CLASS_SOURCE="source-derived",
        TURNOUT_RAIL_ROLE="rails", TURNOUT_TIMBER_ROLE="timbers",
    )
    config = {"turnout_id": "TO-001", "size": module.TURNOUT_SIZE_C10,
              "track_gauge": 16.5, "flangeway": 1.0}
    settings = {"future_chair_embed_depth": 0.2,
                "rail_profile_id": dict(binding._CODE75_PROFILE)["profile_id"]}
    rails, timbers, positions, exclusions = [], [], [], []
    for side, centre_y, gauge_y, outer_y in (
        ("main-side", 20, 19, 21), ("turnout-side", 40, 41, 39),
    ):
        rail_id = f"TO-001:rail:{side}-stock-rail"
        rails.append({
            "stable_identity": rail_id, "rail_role": "stock rail",
            "name": side + " stock rail", "parent_turnout_identity": "TO-001",
            "parent_crossover_identity": "",
            "gauge_face_points": [[-100, gauge_y], [100, gauge_y]],
            "outer_face_points": [[-100, outer_y], [100, outer_y]],
        })
        for number in range(1, 8):
            timber_id = f"TO-001:timber:S{number}"
            if side == "main-side":
                timbers.append({
                    "stable_identity": timber_id, "identifier": f"S{number}",
                    "prototype_reference": f"S{number}", "section": "switch",
                    "parent_turnout_identity": "TO-001",
                    "crossover_identity": "",
                })
            identity = f"invented-P-{side}-{number}"
            positions.append({
                "stable_chair_position_identity": identity,
                "rail_identity": rail_id, "timber_identity": timber_id,
                "chair_code": 2, "chair_code_label": "P",
                "chair_family": "slide chair",
                "chair_subtype": "REA P slide chair",
                "assignment_status": "confirmed",
                "assignment_complete_in_current_stage": True,
                "deliberate_omission": False,
                "special_assignment_deferred": False,
                "stale_signature_state": False,
                "validation_status": "validated",
                "prototype_timber_identifier": f"S{number}",
                "timber_identifier": f"S{number}", "rail_role": "stock rail",
                "rail_name": side + " stock rail",
                "parent_turnout_identity": "TO-001",
                "parent_crossover_identity": "",
                "source_or_assumed_classification": "source-derived",
                "chair_footprint_parameters": {
                    "dimension_classification": "source-derived",
                },
                "centre_point": [number * 2, centre_y],
                "local_rail_tangent": [1, 0], "key_direction_sign": 0,
                "key_orientation": (
                    "requires a configurable key-direction policy"
                ),
                "key_orientation_classification": (
                    "dimension requiring later confirmation"
                ),
            })
            exclusions.append({
                "chair_position_identity": identity,
                "rail_identity": rail_id, "timber_identity": timber_id,
                "chair_label": "P", "chair_family": "slide chair",
                "reason": (
                    "chair family slide chair requires a dedicated "
                    "physical definition"
                ),
                "deliberate_omission": False, "unresolved_special": True,
            })
    instances = []
    for label, code, reason in (
        ("S1", 1, None), ("shared/omitted", 0, "shared support stays omitted"),
        ("AA", 24, "crossing assignment remains deferred"),
    ):
        identity = "invented-other-" + label
        positions.append({
            "stable_chair_position_identity": identity,
            "rail_identity": rails[0]["stable_identity"],
            "timber_identity": timbers[0]["stable_identity"],
            "chair_code": code, "chair_code_label": label,
        })
        record = dict(positions[-1])
        record["chair_position_identity"] = record.pop(
            "stable_chair_position_identity",
        )
        record["chair_label"] = record.pop("chair_code_label")
        if reason:
            record["reason"] = reason
            exclusions.append(record)
        else:
            record["base_z"] = 1.7500000001
            instances.append(record)
    analysis = {"positions": positions, "geometry_signature": "invented"}
    plan = {"entity_id": "TO-001", "entity_kind": "turnout",
            "rail_profile": dict(binding._CODE75_PROFILE),
            "settings": {"embed_depth": 0.2}, "instances": instances,
            "analytical_only": exclusions}
    context = ["turnout", config, analysis, settings, rails, timbers]
    objects = {
        role: SimpleNamespace(Name=role, Shape=ShapeDouble(role))
        for role in ("rails", "timbers")
    }
    document = SimpleNamespace(Name="Source", getObject=objects.get)
    documents = {document.Name: document}
    module._chair_generation_context = lambda *_args: tuple(context)
    module._A8A7B15_BUILD_SOLID_PLAN = lambda *_args: plan
    module._turnout_objects_by_role = lambda *_args: objects
    app = SimpleNamespace(getDocument=documents.get)
    return module, document, app, context, plan, objects


def preview(source, factory):
    module, document, app, *_rest = source
    with patch.dict(sys.modules, {"FreeCAD": app}):
        return binding.preview_private_catalogue_p_chairs(
            module, document, "TO-001", "private-catalogue.json", factory,
        )


class CataloguePlacementTests(unittest.TestCase):
    def test_complete_partition_frames_and_preservation(self):
        source = source_case()
        _module, _doc, _app, context, plan, objects = source
        before = copy.deepcopy((context, plan))

        def factory(path, placements, shapes, receipt, verify):
            self.assertEqual(path, "private-catalogue.json")
            self.assertEqual(len(placements), 14)
            self.assertTrue(all(type(p) is PPlacement for p in placements))
            self.assertEqual([p.position_id for p in placements],
                             sorted(p.position_id for p in placements))
            for p in placements:
                number = int(p.position_id[-1])
                if "main-side" in p.position_id:
                    expected = (number * 2 + 3, 24, 6.7500000001)
                else:
                    expected = (number * 2 - 3, 36, 6.7500000001)
                self.assertEqual(p.transform_point((3, 4, 5)), expected)
                with self.assertRaises(FrozenInstanceError):
                    p.position_id = "mutated"
            for shape, obj in zip(shapes, objects.values()):
                self.assertIsNot(shape, obj.Shape)
                self.assertTrue(shape.isSame(obj.Shape))
            verify()
            return receipt

        receipt = preview(source, factory)
        selected = receipt["selected_positions"]
        remaining = receipt["remaining_positions"]
        self.assertEqual(receipt["analysis_position_count"], 17)
        self.assertEqual(receipt["selected_p_count"], 14)
        selected_ids = {p["position_id"] for p in selected}
        remaining_ids = {p["position_id"] for p in remaining}
        self.assertTrue(selected_ids.isdisjoint(remaining_ids))
        self.assertEqual(selected_ids | remaining_ids, {
            p["stable_chair_position_identity"]
            for p in context[2]["positions"]
        })
        self.assertEqual(len(remaining), 3)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         plan["analytical_only"])
        for p in selected:
            self.assertEqual(p["key_direction_sign"], 0)
            self.assertIn("configurable", p["key_orientation"])
            self.assertIn(p["original_exclusion"], plan["analytical_only"])
        self.assertFalse(receipt["source_document_mutation"])
        self.assertEqual((context, plan), before)
        receipt["original_analytical_exclusions"][0]["reason"] = "changed"
        self.assertEqual((context, plan), before)

    def test_profile_matches_retained_legacy_inputs(self):
        """The guard's fixed source dimensions match the accepted source."""
        path = ROOT / (
            "model_railway_curve_template_multitrack_v10_2a8a7b15_"
            "chair_performance_and_representation.FCMacro"
        )
        parsed = ast.parse(path.read_text())
        profile = next(ast.literal_eval(node.value) for node in parsed.body
                       if isinstance(node, ast.Assign) and any(
                           isinstance(target, ast.Name)
                           and target.id == "CHAIR_CODE75_RAIL_PROFILE"
                           for target in node.targets))
        self.assertEqual(profile, {key: dict(binding._CODE75_PROFILE)[key]
                                   for key in profile})

    def test_context_refusals_before_native_creation(self):
        def forbidden(*_args):
            self.fail("Unsupported source reached native creation")

        for field, value in (
            ("track_gauge", 18.83), ("flangeway", 1.2),
            ("flangeway", True), ("flangeway", math.nan),
            ("flangeway", 10 ** 1000), ("size", "other"),
            ("turnout_id", "other"),
        ):
            with self.subTest(field=field, value=value):
                source = source_case()
                source[3][1][field] = value
                with self.assertRaises(ValueError):
                    preview(source, forbidden)
        for field, value in binding._CODE75_PROFILE:
            with self.subTest(profile_field=field):
                source = source_case()
                source[4]["rail_profile"][field] = (
                    value + 1e-9 if type(value) is float else "changed"
                )
                with self.assertRaises(ValueError):
                    preview(source, forbidden)
        for case in ("scale", "profile-id", "embed", "plan-kind", "plan-id",
                     "missing-datum", "nan-datum", "inconsistent-datum"):
            with self.subTest(case=case):
                source = source_case()
                module, _doc, _app, context, plan, _objs = source
                if case == "scale":
                    module.TURNOUT_DEFAULT_SCALE = 87
                elif case == "profile-id":
                    context[3]["rail_profile_id"] = "other"
                elif case == "embed":
                    plan["settings"]["embed_depth"] += 1e-9
                elif case.startswith("plan-"):
                    plan["entity_" + case[5:]] = "other"
                elif case == "missing-datum":
                    del plan["instances"][0]["base_z"]
                elif case == "nan-datum":
                    plan["instances"][0]["base_z"] = math.nan
                else:
                    other = copy.deepcopy(plan["instances"][0])
                    other["chair_position_identity"] = "extra"
                    other["base_z"] += 1e-9
                    plan["instances"].append(other)
                    analysis = copy.deepcopy(context[2]["positions"][-3])
                    analysis["stable_chair_position_identity"] = "extra"
                    context[2]["positions"].append(analysis)
                with self.assertRaises(ValueError):
                    preview(source, forbidden)

    def test_assignment_refusals(self):
        mutations = {
            "chair_code": 2.0, "chair_code_label": "S1",
            "chair_family": "other", "chair_subtype": "other",
            "assignment_status": "open",
            "assignment_complete_in_current_stage": False,
            "deliberate_omission": True, "special_assignment_deferred": True,
            "stale_signature_state": True, "validation_status": "pending",
            "prototype_timber_identifier": "S8", "timber_identifier": "S8",
            "rail_role": "switch and closure rail", "rail_name": "other",
            "parent_turnout_identity": "TO-002",
            "parent_crossover_identity": "XO-001",
            "source_or_assumed_classification": "assumed",
            "chair_footprint_parameters": {}, "key_direction_sign": 1,
            "key_orientation": "chosen",
            "key_orientation_classification": "accepted",
            "rail_identity": "missing", "timber_identity": "missing",
            "centre_point": [math.inf, 20], "local_rail_tangent": [2, 0],
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                source = source_case()
                source[3][2]["positions"][0][field] = value
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(field))

    def test_identity_plan_and_frame_refusals(self):
        for case in (
            "duplicate-position", "duplicate-rail", "duplicate-timber",
            "missing-plan-item", "duplicate-plan-item", "changed-plan-rail",
            "changed-plan-reason", "missing-face", "same-side-faces",
            "ambiguous-face", "changed-rail-owner", "changed-timber-label",
        ):
            with self.subTest(case=case):
                source = source_case()
                _module, _doc, _app, context, plan, _objs = source
                if (case.startswith("duplicate-")
                        and case != "duplicate-plan-item"):
                    records = {"duplicate-position": context[2]["positions"],
                               "duplicate-rail": context[4],
                               "duplicate-timber": context[5]}[case]
                    records.append(copy.deepcopy(records[0]))
                elif case == "missing-plan-item":
                    plan["analytical_only"].pop()
                elif case == "duplicate-plan-item":
                    plan["analytical_only"].append(
                        copy.deepcopy(plan["analytical_only"][0]))
                elif case == "changed-plan-rail":
                    plan["analytical_only"][0]["rail_identity"] = "other"
                elif case == "changed-plan-reason":
                    plan["analytical_only"][0]["reason"] = "unknown source"
                elif case == "missing-face":
                    context[4][0]["gauge_face_points"] = []
                elif case == "same-side-faces":
                    context[4][0]["gauge_face_points"] = [
                        [-100, 22], [100, 22],
                    ]
                elif case == "ambiguous-face":
                    context[4][0]["gauge_face_points"] = [
                        [-100, 19], [100, 19], [100, 18], [-100, 18],
                    ]
                elif case == "changed-rail-owner":
                    context[4][0]["parent_turnout_identity"] = "other"
                else:
                    context[5][0]["prototype_reference"] = "S8"
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(case))

    def test_late_source_and_object_mutation_refusals(self):
        for case in (
            "subprecision-centre", "source-profile", "shape", "object",
        ):
            with self.subTest(case=case):
                source = source_case()
                _module, _doc, _app, context, _plan, objects = source

                def factory(_path, _placements, _shapes, _receipt, verify):
                    if case == "subprecision-centre":
                        context[2]["positions"][0]["centre_point"][0] += 1e-9
                    elif case == "source-profile":
                        context[3]["rail_profile_id"] = "changed"
                    elif case == "shape":
                        objects["rails"].Shape = ShapeDouble("other")
                    else:
                        old = objects["rails"]
                        objects["rails"] = SimpleNamespace(
                            Name=old.Name, Shape=old.Shape,
                        )
                    verify()

                with self.assertRaises(ValueError):
                    preview(source, factory)

    def test_session_routes_exact_inputs_after_routing_check(self):
        calls = []
        session = SimpleNamespace(
            module=object(), _private_catalogue_p_preview_factory=object(),
            routing_record=lambda: calls.append("route"),
        )
        document = object()

        def operation(*args):
            self.assertEqual(calls, ["route"])
            self.assertEqual(args, (
                session.module, document, "TO-001", "catalogue.json",
                session._private_catalogue_p_preview_factory,
            ))
            return "receipt"

        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        with patch.object(
            binding, "preview_private_catalogue_p_chairs", operation,
        ):
            result = session_type.preview_private_catalogue_p_chairs(
                session, document, "TO-001", "catalogue.json",
            )
        self.assertEqual(result, "receipt")
        source = source_case()
        with self.assertRaises(ValueError):
            preview(source, None)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CataloguePlacementTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)


if __name__ == "__main__":
    main()
