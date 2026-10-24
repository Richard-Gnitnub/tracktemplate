#!/usr/bin/env python3
"""Check whole-crossover accounting with invented source records.

No private catalogue or native geometry is admitted by this standalone proof.
Qualified native and real-GUI proofs own actual retained component evidence.
"""

import copy
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    transition_workflow,
)
from validate_phase9b_catalogue_p_crossover import (  # noqa: E402
    crossover_source,
)

SENTINEL = "Phase 9B catalogue whole crossover standalone validation passed"


def whole_source():
    """Extend the two-constituent source with each coverage disposition."""
    source = crossover_source()
    module, _document, _app, context, plan, _objects, _state = source
    positions, rails, timbers = context[2]["positions"], context[4], context[5]
    positions[:] = [p for p in positions if p["chair_code"] == 2]
    plan["instances"][:] = []
    plan["analytical_only"][:] = [
        p for p in plan["analytical_only"] if p["chair_label"] == "P"
    ]
    module.CHAIR_FAMILY_BRIDGE = "bridge chair"
    module.CHAIR_ASSIGNMENT_OMITTED = "confirmed shared switch support"
    module.CHAIR_ASSIGNMENT_DEFERRED_SPECIAL = "deferred special"
    module.CHAIR_CODE_CATALOG = {
        1: {"label": "S1", "family": "running chair"},
        2: {"label": "P"}, 5: {"label": "L1"},
        7: {"label": "S1J", "family": "joint chair"},
        11: {"label": "1P/2P"},
    }
    module._chair_supported_physical_position = lambda _p: (True, "supported")
    template = copy.deepcopy(positions[0])

    def add(identity, code, identifier, *, omitted=False, deferred=False):
        position = copy.deepcopy(template)
        position.update(
            stable_chair_position_identity=identity, chair_code=code,
            chair_code_label="" if code == 0 else
            module.CHAIR_CODE_CATALOG[code]["label"],
            timber_identity="A:timber:" + identifier,
            timber_identifier=identifier, prototype_timber_identifier=identifier,
            deliberate_omission=omitted, special_assignment_deferred=deferred,
            assignment_status=(module.CHAIR_ASSIGNMENT_OMITTED if omitted else
                               module.CHAIR_ASSIGNMENT_DEFERRED_SPECIAL
                               if deferred else module.CHAIR_ASSIGNMENT_CONFIRMED),
            chair_subtype="invented support evidence",
        )
        if not any(t["stable_identity"] == position["timber_identity"]
                   for t in timbers):
            timber = copy.deepcopy(timbers[0])
            timber.update(stable_identity=position["timber_identity"],
                          identifier=identifier, prototype_reference=identifier)
            timbers.append(timber)
        if code in (1, 7):
            position["chair_family"] = module.CHAIR_CODE_CATALOG[code]["family"]
        if code == 5:
            position["chair_family"] = module.CHAIR_FAMILY_BRIDGE
        if code == 7:
            position["key_orientation"] = (
                "towards the adjacent rail joint; exact direction sign "
                "requires stored joint chainage"
            )
            position["key_orientation_classification"] = module.CHAIR_CLASS_SOURCE
        if omitted:
            position.update(rail_name="curved switch and closure rail",
                            rail_role="curved switch and closure rail",
                            rail_identity="A:rail:curved-switch")
            if not any(r["stable_identity"] == position["rail_identity"]
                       for r in rails):
                rail = copy.deepcopy(rails[0])
                rail.update(stable_identity=position["rail_identity"],
                            name=position["rail_name"], rail_role=position["rail_role"])
                rails.append(rail)
            position["key_orientation"] = "not applicable"
        positions.append(position)
        record = {
            "chair_position_identity": identity,
            "chair_label": position["chair_code_label"],
            "rail_identity": position["rail_identity"],
            "timber_identity": position["timber_identity"],
        }
        if code in (1, 7):
            record.update(chair_code=code, centre_point=position["centre_point"],
                          base_z=0.8, outward_axis=[0, 1], local_y_axis=[-1, 0])
            plan["instances"].append(record)
        else:
            record.update(reason="original source exclusion")
            plan["analytical_only"].append(record)
        return position

    add("single", 1, "T1")
    add("joint", 7, "J1")
    add("deferred", 5, "T2", deferred=True)
    block = add("block", 11, "S8")
    mate = add("block-mate", 0, "S8", omitted=True)
    mate["local_rail_tangent"] = [math.cos(0.15), math.sin(0.15)]
    shared = add("p-mate", 0, "S1", omitted=True)
    # Use the pre-existing P timber identity, not the new synthetic S1.
    shared["timber_identity"] = template["timber_identity"]
    plan["analytical_only"][-1]["timber_identity"] = template["timber_identity"]
    assert block["rail_name"] == "main-side stock rail"
    return source


def preparation():
    return SimpleNamespace(
        label="1P", model_sha256="invented-model",
        context={"context_sha256": "invented-context"},
        metadata={"native_record": {"source_recipe": {
            "sample_kind": "fixture_timber", "timber_id": "S8",
            "chair_code": 11, "context": {"aq_k_rad": 0.03},
        }}},
    )


def preview(source, factory, *, prepared=None, verify=None):
    module, document, app, *_rest = source
    with patch.dict(sys.modules, {"FreeCAD": app}), patch.object(
        binding, "prepare_catalogue_chair", return_value=prepared or preparation(),
    ), patch.object(binding, "verify_catalogue_sources", verify or Mock()):
        return binding.preview_private_catalogue_crossover_chairs(
            module, document, "XO-001", "private-catalogue.json", factory,
        )


class WholeCrossoverTests(unittest.TestCase):
    def reject(self, source, **kwargs):
        factory = Mock(side_effect=AssertionError("native creation reached"))
        with self.assertRaises(ValueError):
            preview(source, factory, **kwargs)
        factory.assert_not_called()

    def test_complete_disjoint_accounting_preserves_originals(self):
        source = whole_source()
        before = copy.deepcopy((source[3], source[4]))
        verified = Mock()

        def factory(_path, families, _shapes, receipt, verify):
            self.assertEqual({k: len(v) for k, v in families.items()},
                             {"S1": 1, "S1J": 1, "P": 28})
            verify()
            return receipt

        receipt = preview(source, factory, verify=verified)
        self.assertEqual(receipt["analysis_position_count"], 34)
        self.assertEqual(receipt["placement_count"], 30)
        self.assertEqual(receipt["excluded_position_count"], 4)
        selected = {p["position_id"] for p in receipt["selected_positions"]}
        excluded = {p["position_id"]: p for p in receipt["excluded_positions"]}
        self.assertFalse(selected & excluded.keys())
        self.assertEqual(selected | excluded.keys(), {
            p["stable_chair_position_identity"] for p in source[3][2]["positions"]
        })
        self.assertTrue(excluded["p-mate"]["supporting_assembly_placed"])
        self.assertFalse(excluded["block-mate"]["supporting_assembly_placed"])
        self.assertEqual(excluded["block-mate"]["supporting_position_id"], "block")
        comparison = excluded["block"]["source_context_comparison"]
        self.assertEqual(comparison["retained_uncurved_gauge_face_angle_rad"],
                         0.03)
        self.assertEqual(comparison["physical_fit"], "NOT_PROVED")
        self.assertEqual(excluded["block"]["exclusion_kind"],
                         "paired-source-context-not-qualified")
        self.assertNotIn("angle_magnitude_difference_rad", comparison)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         source[4]["analytical_only"])
        verified.assert_called_once()
        receipt["original_analytical_exclusions"][0]["reason"] = "changed"
        receipt["selected_positions"][0]["key_direction_sign"] = 1
        self.assertEqual((source[3], source[4]), before)

    def test_reuses_named_face_recovery(self):
        source = whole_source()
        extra = copy.deepcopy(source[3][2]["positions"][-6])
        extra["stable_chair_position_identity"] = "single-kept"
        source[3][2]["positions"].append(extra)
        instance = copy.deepcopy(source[4]["instances"][0])
        instance["chair_position_identity"] = "single-kept"
        source[4]["instances"].append(instance)
        record = source[4]["instances"].pop(0)
        record["reason"] = "gauge normal is not perpendicular to the local rail tangent"
        source[4]["analytical_only"].append(record)
        result = preview(source, lambda _p, _f, _s, r, _v: r)
        self.assertEqual(result["recovered_positions"][0]["position_id"], "single")
        self.assertEqual(result["placement_count"], 31)

    def test_refuses_corrupt_source_instead_of_inventing_exclusions(self):
        for field, value in (
            ("chair_code", 999), ("chair_code", True),
            ("chair_code_label", "unknown"), ("key_direction_sign", 1),
            ("stale_signature_state", True),
            ("parent_crossover_identity", "OTHER"),
            ("assignment_status", "unresolved"),
            ("local_rail_tangent", [float("nan"), 0]),
        ):
            with self.subTest(field=field):
                source = whole_source()
                source[3][2]["positions"][-3][field] = value
                self.reject(source)

    def test_refuses_unsupported_deferred_state_and_shared_links(self):
        for identity, field, value in (
            ("deferred", "special_assignment_deferred", False),
            ("deferred", "assignment_status", "confirmed"),
            ("deferred", "chair_family", "unknown"),
            ("p-mate", "rail_name", "unknown shared rail"),
            ("block", "prototype_timber_identifier", "S99"),
            ("single", "chair_family", "unknown"),
            ("joint", "key_orientation", "forwards"),
        ):
            with self.subTest(identity=identity, field=field):
                source = whole_source()
                item = next(p for p in source[3][2]["positions"]
                            if p["stable_chair_position_identity"] == identity)
                item[field] = value
                self.reject(source)

    def test_equal_sampled_angle_does_not_qualify_source_context(self):
        source = whole_source()
        mate = next(p for p in source[3][2]["positions"]
                    if p["stable_chair_position_identity"] == "block-mate")
        mate["local_rail_tangent"] = [math.cos(0.03), math.sin(0.03)]
        receipt = preview(source, lambda _p, _f, _s, result, _v: result)
        block = next(item for item in receipt["excluded_positions"]
                     if item["position_id"] == "block")
        self.assertEqual(block["exclusion_kind"],
                         "paired-source-context-not-qualified")
        self.assertNotIn("angle_magnitude_difference_rad",
                         block["source_context_comparison"])

    def test_late_source_and_catalogue_changes_refused(self):
        for change in ("source", "catalogue"):
            source = whole_source()
            verify_catalogue = Mock()

            def factory(_path, _families, _shapes, _receipt, verify):
                if change == "source":
                    source[3][2]["positions"][0]["key_direction_sign"] = 9
                else:
                    verify_catalogue.side_effect = ValueError("catalogue changed")
                with self.assertRaises(ValueError):
                    verify()
                return "rejected"

            self.assertEqual(preview(source, factory, verify=verify_catalogue),
                             "rejected")

    def test_session_command_forwards_existing_contract(self):
        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        session = SimpleNamespace(
            module=object(), _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        operation = Mock(return_value="receipt")
        with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                          operation):
            self.assertEqual(session_type.preview_private_catalogue_crossover_chairs(
                session, "document", "XO-001", "catalogue",
            ), "receipt")
        operation.assert_called_once_with(
            session.module, "document", "XO-001", "catalogue",
            session._private_catalogue_crossover_preview_factory,
        )
        session.routing_record.assert_called_once()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(WholeCrossoverTests),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
