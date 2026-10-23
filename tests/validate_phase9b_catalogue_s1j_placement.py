#!/usr/bin/env python3
"""Check catalogue S1J routing with invented source records and host doubles.

Native geometry and actual joint coverage require separate host evidence.
These tests preserve the existing analytical selection and frame recovery.
"""

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
    transition_workflow,
)
from tracktemplate.domain.chair_placement import S1JPlacement  # noqa: E402
from validate_phase9b_catalogue_p_placement import (  # noqa: E402
    source_case as p_source_case,
)
from validate_phase9b_s1_s1j_reference_preview import (  # noqa: E402
    ShapeDouble,
)


SENTINEL = "Phase 9B catalogue S1J placement standalone validation passed"
FRAME_REASON = "gauge normal is not perpendicular to the local rail tangent"


def source_case():
    """Invent one resolved and one recoverable joint on opposite rail sides."""
    source = p_source_case()
    module, _document, _app, context, plan, _objects = source
    module.CHAIR_FAMILY_JOINT = "rail-joint support"
    module._chair_supported_physical_position = lambda _position: (True, "")
    for index in (0, 7):
        position = context[2]["positions"][index]
        position.update({
            "chair_code": 7, "chair_code_label": "S1J",
            "chair_family": module.CHAIR_FAMILY_JOINT,
            "chair_subtype": "REA S1J switch-front joint chair",
            "key_orientation": (
                "towards the adjacent rail joint; exact direction sign "
                "requires stored joint chainage"
            ),
            "key_orientation_classification": module.CHAIR_CLASS_SOURCE,
        })
        item = next(item for item in plan["analytical_only"]
                    if item["chair_position_identity"]
                    == position["stable_chair_position_identity"])
        item.update(chair_label="S1J", chair_family=module.CHAIR_FAMILY_JOINT)
        if index == 0:
            plan["analytical_only"].remove(item)
            plan["instances"].append({
                "chair_position_identity": item["chair_position_identity"],
                "rail_identity": item["rail_identity"],
                "timber_identity": item["timber_identity"],
                "chair_code": 7, "chair_label": "S1J",
                "centre_point": position["centre_point"][:],
                "base_z": 1.7500000001,
                "outward_axis": [0, 1], "local_y_axis": [-1, 0],
            })
        else:
            item["reason"] = FRAME_REASON
    return source


def preview(source, factory):
    module, document, app, *_rest = source
    with patch.dict(sys.modules, {"FreeCAD": app}):
        return binding.preview_private_catalogue_s1j_chairs(
            module, document, "TO-001", "private-catalogue.json", factory,
        )


class CatalogueS1JPlacementTests(unittest.TestCase):
    def test_partition_frames_and_original_evidence(self):
        source = source_case()
        _module, _document, _app, context, plan, objects = source
        before = copy.deepcopy((context, plan))

        def factory(path, placements, shapes, receipt, verify):
            self.assertEqual(path, "private-catalogue.json")
            self.assertEqual(len(placements), 2)
            self.assertEqual([p.position_id for p in placements],
                             sorted(p.position_id for p in placements))
            for placement in placements:
                self.assertIs(type(placement), S1JPlacement)
                expected = ((5, 24, 6.7500000001)
                            if "main-side" in placement.position_id
                            else (-1, 36, 6.7500000001))
                self.assertEqual(placement.transform_point((3, 4, 5)),
                                 expected)
                with self.assertRaises(FrozenInstanceError):
                    placement.position_id = "changed"
            for shape, obj in zip(shapes, objects.values()):
                self.assertIsNot(shape, obj.Shape)
                self.assertTrue(shape.isSame(obj.Shape))
            verify()
            return receipt

        receipt = preview(source, factory)
        self.assertEqual(receipt["analysis_position_count"], 17)
        self.assertEqual(receipt["selected_s1j_count"], 2)
        self.assertEqual(len(receipt["remaining_positions"]), 15)
        selected = receipt["selected_positions"]
        selected_ids = {item["position_id"] for item in selected}
        remaining_ids = {item["position_id"]
                         for item in receipt["remaining_positions"]}
        self.assertTrue(selected_ids.isdisjoint(remaining_ids))
        self.assertEqual(selected_ids | remaining_ids, {
            item["stable_chair_position_identity"]
            for item in context[2]["positions"]
        })
        self.assertEqual(receipt["original_analytical_exclusions"],
                         plan["analytical_only"])
        self.assertEqual(len(receipt["recovered_positions"]), 1)
        self.assertEqual(receipt["recovered_positions"][0]["original_reason"],
                         FRAME_REASON)
        for item in selected:
            self.assertEqual(item["key_direction_sign"], 0)
            self.assertIn("requires stored joint chainage",
                          item["key_orientation"])
            if item["original_instance"] is not None:
                self.assertIn(item["original_instance"], plan["instances"])
                self.assertIsNone(item["original_exclusion"])
            else:
                self.assertIn(item["original_exclusion"],
                              plan["analytical_only"])
        self.assertFalse(receipt["source_document_mutation"])
        receipt["original_analytical_exclusions"][0]["reason"] = "changed"
        selected[0]["original_instance"]["base_z"] = 99
        self.assertEqual((context, plan), before)

    def test_context_and_complete_profile_refusals(self):
        for field, value in (
            ("track_gauge", 18.83), ("flangeway", 1.2),
            ("flangeway", True), ("flangeway", math.nan),
            ("size", "other"), ("turnout_id", "other"),
        ):
            with self.subTest(field=field, value=value):
                source = source_case()
                source[3][1][field] = value
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(field))
        for field, value in binding._CODE75_PROFILE:
            with self.subTest(profile_field=field):
                source = source_case()
                source[4]["rail_profile"][field] = (
                    value + 1e-9 if type(value) is float else "changed"
                )
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(field))
        for case in ("scale", "plan-id", "plan-kind", "profile-id", "embed"):
            with self.subTest(case=case):
                source = source_case()
                if case == "scale":
                    source[0].TURNOUT_DEFAULT_SCALE = 87
                elif case.startswith("plan-"):
                    source[4]["entity_" + case[5:]] = "other"
                elif case == "profile-id":
                    source[3][3]["rail_profile_id"] = "other"
                else:
                    source[4]["settings"]["embed_depth"] += 1e-9
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(case))

    def test_assignment_and_identity_refusals(self):
        mutations = {
            "chair_code": 7.0, "chair_code_label": "S1",
            "chair_family": "other", "assignment_status": "open",
            "assignment_complete_in_current_stage": False,
            "deliberate_omission": True, "special_assignment_deferred": True,
            "stale_signature_state": True, "validation_status": "pending",
            "parent_turnout_identity": "TO-002",
            "parent_crossover_identity": "XO-001", "rail_name": "other",
            "rail_role": "other", "timber_identifier": "other",
            "prototype_timber_identifier": "other",
            "source_or_assumed_classification": "assumed",
            "chair_footprint_parameters": {}, "key_direction_sign": 1,
            "key_orientation": "chosen",
            "key_orientation_classification": "accepted",
            "rail_identity": "missing", "timber_identity": "missing",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                source = source_case()
                source[3][2]["positions"][0][field] = value
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(field))
        for case in (
            "duplicate-position", "duplicate-rail", "duplicate-timber",
            "duplicate-plan", "missing-plan", "changed-plan-source",
            "changed-plan-label", "changed-plan-centre", "changed-owner",
            "datum-missing", "datum-nan", "datum-inconsistent",
        ):
            with self.subTest(case=case):
                source = source_case()
                _module, _doc, _app, context, plan, _objects = source
                if case in ("duplicate-position", "duplicate-rail",
                            "duplicate-timber", "duplicate-plan"):
                    records = {
                        "duplicate-position": context[2]["positions"],
                        "duplicate-rail": context[4],
                        "duplicate-timber": context[5],
                        "duplicate-plan": plan["instances"],
                    }[case]
                    records.append(copy.deepcopy(records[0]))
                elif case == "missing-plan":
                    plan["analytical_only"].pop()
                elif case == "changed-plan-source":
                    plan["instances"][-1]["rail_identity"] = "other"
                elif case == "changed-plan-label":
                    plan["instances"][-1]["chair_label"] = "S1"
                elif case == "changed-plan-centre":
                    plan["instances"][-1]["centre_point"][0] += 1e-9
                elif case == "changed-owner":
                    context[4][0]["parent_turnout_identity"] = "TO-002"
                elif case == "datum-missing":
                    del plan["instances"][-1]["base_z"]
                elif case == "datum-nan":
                    plan["instances"][-1]["base_z"] = math.nan
                else:
                    plan["instances"][-1]["base_z"] += 1e-9
                with self.assertRaises(ValueError):
                    preview(source, lambda *_args: self.fail(case))

    def test_unresolved_frame_stays_excluded(self):
        source = source_case()
        source[3][4][1]["gauge_face_points"] = []
        receipt = preview(source, lambda _p, _s, _c, receipt, _v: receipt)
        self.assertEqual(receipt["selected_s1j_count"], 1)
        refused = next(item for item in receipt["remaining_positions"]
                       if item["chair_code"] == 7)
        self.assertEqual(refused["reason"], FRAME_REASON)
        self.assertIn("placement_recovery_reason", refused)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         source[4]["analytical_only"])

    def test_late_source_refusals(self):
        for case in ("position", "profile", "shape", "object"):
            with self.subTest(case=case):
                source = source_case()
                _module, _doc, _app, context, _plan, objects = source

                def factory(_path, _placements, _shapes, _receipt, verify):
                    if case == "position":
                        context[2]["positions"][0]["centre_point"][0] += 1e-9
                    elif case == "profile":
                        context[3]["rail_profile_id"] = "other"
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

    def test_session_routes_exact_inputs(self):
        calls = []
        session = SimpleNamespace(
            module=object(), _private_catalogue_s1j_preview_factory=object(),
            routing_record=lambda: calls.append("route"),
        )
        document = object()

        def operation(*args):
            self.assertEqual(calls, ["route"])
            self.assertEqual(args, (
                session.module, document, "TO-001", "catalogue.json",
                session._private_catalogue_s1j_preview_factory,
            ))
            return "receipt"

        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        with patch.object(
            binding, "preview_private_catalogue_s1j_chairs", operation,
        ):
            result = session_type.preview_private_catalogue_s1j_chairs(
                session, document, "TO-001", "catalogue.json",
            )
        self.assertEqual(result, "receipt")
        with self.assertRaises(ValueError):
            preview(source_case(), None)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CatalogueS1JPlacementTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)


if __name__ == "__main__":
    main()
