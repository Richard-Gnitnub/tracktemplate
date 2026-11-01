"""Check five source-qualified TO-001 heel corrections without FreeCAD.

Explicit fixtures exercise unchanged source records and selection safety.
Independent retained-source evidence supplies the railway comparison.
No native, GUI, physical-fit or production qualification follows.
"""

import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from validate_phase9b_turnout_single_rail import (  # noqa: E402
    HEEL_SELECTION, binding, corrected_source_case, heel_identity,
    identity, preview,
)
from tracktemplate.compatibility.chair_reference_preview import (  # noqa: E402
    _open_source_context,
)
from tracktemplate.compatibility import chair_reference_preview as references  # noqa: E402
from tracktemplate.compatibility.transition_workflow import (  # noqa: E402
    ModularCoreLayoutWorkflowSession,
)


def source_arguments(source):
    with patch.dict(sys.modules, {"FreeCAD": source.app}):
        return _open_source_context(
            source.module, source.document, "TO-001", "S1",
        )


def filtered(source):
    arguments = source_arguments(source)
    # T2 is still an analytical refusal at this boundary. The correction
    # must replace its reason before the old S1 frame-recovery operation.
    placements = tuple(SimpleNamespace(position_id=heel_identity(n, r))
                       for n, r in HEEL_SELECTION if n != "T2")
    other = SimpleNamespace(position_id="unrelated")
    excluded = [{"position_id": heel_identity("T2", 3), "chair_code": 1,
                 "reason": "gauge normal is not perpendicular to the local rail tangent"}]
    return binding().exclude_turnout_heel_l1(
        source.module, source.document, arguments, (*placements, other), excluded,
    )


class TurnoutHeelCorrectionTests(unittest.TestCase):
    def test_five_l1_replacements_preserve_all_raw_records(self):
        source = corrected_source_case()
        before = copy.deepcopy((source.context, source.plan))
        _, placements, _, receipt, _verify = preview(source)
        self.assertEqual(len(placements), 12)
        self.assertEqual(receipt["selected_family_counts"], {"L1": 11, "S1": 1})
        by_id = {p.position_id: p for p in placements}
        for name, rail in HEEL_SELECTION:
            self.assertEqual(by_id[heel_identity(name, rail)].family, "L1")
        self.assertEqual(by_id[identity("T2", 4)].family, "S1")
        corrections = receipt["corrected_heel_positions"]
        self.assertEqual(len(corrections), 5)
        self.assertTrue(all(p["original_position"]["chair_code_label"] == "S1"
                            for p in corrections))
        self.assertEqual(receipt["original_physical_instances"], before[1]["instances"])
        self.assertEqual(receipt["original_analytical_exclusions"], before[1]["analytical_only"])
        self.assertEqual((source.context, source.plan), before)

    def test_all_five_removed_before_s1_recovery(self):
        source = corrected_source_case()
        before = copy.deepcopy((source.context, source.plan))
        placements, excluded = filtered(source)
        self.assertEqual([p.position_id for p in placements], ["unrelated"])
        self.assertEqual({p["position_id"] for p in excluded},
                         {heel_identity(*p) for p in HEEL_SELECTION})
        self.assertTrue(all(p["replacement_family"] == "L1" for p in excluded))
        self.assertTrue(all(p["reason"] != "gauge normal is not perpendicular to the local rail tangent"
                            for p in excluded))
        t2 = next(p for p in excluded if p["position_id"] == heel_identity("T2", 3))
        self.assertEqual(t2["original_plan_record"]["reason"],
                         "gauge normal is not perpendicular to the local rail tangent")
        self.assertEqual((source.context, source.plan), before)

    def test_other_source_signatures_keep_existing_selection(self):
        source = corrected_source_case()
        arguments = list(source_arguments(source))
        context = json.loads(arguments[0])
        context["analysis"]["geometry_signature"] = "other-source"
        arguments[0] = json.dumps(context)
        original = (SimpleNamespace(position_id="kept"),)
        excluded = [{"position_id": "existing", "reason": "kept"}]
        result = binding().exclude_turnout_heel_l1(
            source.module, source.document, arguments, original, excluded,
        )
        self.assertEqual(result, (original, excluded))

    def test_missing_or_changed_heel_record_refused_before_preview(self):
        for field, value in (("chair_code", 5), ("chair_code_label", "L1"),
                             ("key_direction_sign", 1),
                             ("special_assignment_deferred", True),
                             ("rail_role", "wrong"),
                             ("source_configuration", {})):
            with self.subTest(field=field):
                source = corrected_source_case()
                record = next(p for p in source.context[2]["positions"]
                              if p["stable_chair_position_identity"] == heel_identity("S13", 1))
                record[field] = value
                factory = Mock()
                with self.assertRaises(ValueError):
                    preview(source, factory)
                factory.assert_not_called()

    def test_t2_original_refusal_must_remain_exact(self):
        source = corrected_source_case()
        record = next(p for p in source.plan["analytical_only"]
                      if p["chair_position_identity"] == heel_identity("T2", 3))
        record["reason"] = "different failure"
        with self.assertRaises(ValueError):
            preview(source)
        with self.assertRaises(ValueError):
            filtered(source)

    def test_changed_source_clearance_refuses_l1(self):
        source = corrected_source_case()
        original = source.module._rea_c10_turnout_outer_gauge_point_at_x

        def changed(dimensions, station):
            x, y, angle = original(dimensions, station)
            return x, y + 0.5, angle

        source.module._rea_c10_turnout_outer_gauge_point_at_x = changed
        with self.assertRaises(ValueError):
            filtered(source)

    def test_s1_and_combined_commands_apply_correction_before_recovery(self):
        for combined in (False, True):
            with self.subTest(combined=combined):
                source = corrected_source_case()
                before = copy.deepcopy((source.context, source.plan))
                selected = tuple(SimpleNamespace(position_id=heel_identity(n, r))
                                 for n, r in HEEL_SELECTION if n != "T2")
                original = [{"position_id": heel_identity("T2", 3), "chair_code": 1,
                             "reason": "gauge normal is not perpendicular to the local rail tangent"}]
                result = {}

                def capture(*args):
                    result["placements"] = args[5] if combined else args[3]
                    result["receipt"] = args[-2]
                    args[-1]()
                    return result

                # The existing family-selector regressions own generic
                # instance decoding. These fixtures isolate this command's
                # new ordering relative to the real recovery operation.
                selector = "_select_s1_s1j_positions" if combined else "_select_positions"
                selection = (selected, (), original) if combined else (selected, original)
                workflow = SimpleNamespace(
                    module=source.module, routing_record=Mock(),
                    _s1_reference_preview_factory=capture,
                    _s1_s1j_reference_preview_factory=capture,
                )
                with (patch.dict(sys.modules, {"FreeCAD": source.app}),
                      patch.object(references, selector, return_value=selection)):
                    if combined:
                        ModularCoreLayoutWorkflowSession.preview_s1_s1j_reference_chairs(
                            workflow, source.document, "TO-001",
                            None, None, None, None, None,
                        )
                    else:
                        ModularCoreLayoutWorkflowSession.preview_s1_reference_chairs(
                            workflow, source.document, "TO-001",
                            None, None, None,
                        )
                workflow.routing_record.assert_called_once()
                self.assertEqual(result["placements"], ())
                self.assertEqual(result["receipt"]["selected_s1_count"], 0)
                self.assertEqual(result["receipt"]["recovered_positions"], [])
                self.assertEqual(len(result["receipt"]["excluded_positions"]), 5)
                self.assertEqual((source.context, source.plan), before)

    def test_invalid_injected_filter_rejected_before_source_access(self):
        with patch.object(references, "_open_source_context") as opened:
            for operation, arguments in (
                (references.preview_s1_reference_chairs, (None,) * 6),
                (references.preview_s1_s1j_reference_chairs, (None,) * 8),
            ):
                with self.assertRaises(TypeError):
                    operation(*arguments, Mock(), source_selection_filter=7)
            opened.assert_not_called()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TurnoutHeelCorrectionTests),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: five TO-001 heel L1 replacements preserve source records")
