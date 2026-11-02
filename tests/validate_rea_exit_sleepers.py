#!/usr/bin/env python3
"""Independent source/body and canonical tests for optional exit sleepers."""

import copy
from dataclasses import asdict, replace
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from tracktemplate.domain import rea_turnout as domain  # noqa: E402
from tracktemplate.application import rea_turnout_state as state  # noqa: E402
from tracktemplate.compatibility.rea_turnout import (  # noqa: E402
    ReaTurnoutGeometryAdapter,
)
from validate_phase1_turnout import _close  # noqa: E402
from validate_phase9b_rea_turnout_state import record, encoded  # noqa: E402
from validate_phase9b_rea_bc_consumers import host  # noqa: E402
from validate_rea_trackwork_workflow import (  # noqa: E402
    WorkflowTests, complete_railway_module,
)


PROFILE_ID = "templot-556b-00-D0GAF-32mm-full-exit"
ARCHIVE = "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
FIXTURE = ROOT / "tests/fixtures/phase9b-rea-bc-source.json"
FIXTURE_SHA256 = "d8c356a8cd84be1de0f6535abc09090a12dd82ecbb6083bd3ca65e19f43694f4"


def expected_profile():
    # Independent source contract: see the preserved 556b review.
    return {
        "schema_version": 1, "profile_id": PROFILE_ID,
        "source_archive_sha256": ARCHIVE, "calculation_revision": 1,
        "source_gauge_identity": "t_00DGF_i",
        "source_gauge_name": "00-D0GAF", "nominal_sleeper_length_mm": 32.0,
        "source_flags": {
            "exittb_i": 2, "fdm_timber_correction_enabled": False,
            "frackeq": 0, "full_length": True, "gaunt": False,
            "half_diamond": False, "include_xing_timbers": True,
            "jt_slwide_inches": 10, "mv_joint_offset_inches": 0,
            "mvj_sp_inches": 12.5, "plain_track": False, "pt_i": 3,
            "randangle": 0, "randend": 0, "retpar_i": 0,
            "shoves_omissions_or_inserts": "none", "slwide_inches": 10,
            "tb_end_offset_inches": 0, "tb_roll_percent": 0,
            "tv_joint_offset_inches": 0, "veetimb_spacing_inches": 30,
            "wingtimb_spacing_inches": 30,
        },
    }


class ExitSleeperTests(unittest.TestCase):
    def profile(self):
        factory = getattr(domain, "ReaExitSleeperProfile", None)
        self.assertTrue(callable(factory), "Explicit profile is missing")
        return factory(PROFILE_ID)

    def test_all_88_source_cases_keep_literal_exit_identities_and_bodies(self):
        profile = self.profile()
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                         FIXTURE_SHA256)
        cases = json.loads(FIXTURE.read_text())["cases"]
        self.assertEqual(len(cases), 88)
        count = 0
        with localcontext() as context:
            context.prec = 50
            inch = Decimal(1) / 3
            for case in cases:
                n = Decimal(case["crossing_ratio"])
                # Source branches, not the product joint or count selector.
                vee_count = (5 if n < Decimal("6.875") else
                             6 if n < Decimal("10.125") else
                             7 if n < Decimal("15.125") else 8)
                joint = Decimal(case["dimensions"]["blunt_nose_x"]) + (
                    Decimal(4) + Decimal("12.5") + (vee_count - 1) * 30
                ) * inch
                spec = domain.ReaTurnoutSpecification(case["switch"], float(n))
                exits = domain.rea_turnout_exit_sleepers(spec, profile)
                self.assertEqual(len(exits), 2)
                for index, offset in enumerate((Decimal(12), Decimal("38.5"))):
                    actual = exits[index]
                    self.assertEqual(actual["identifier"], "E" + str(index + 1))
                    self.assertEqual(actual["section"], "exit")
                    self.assertEqual(actual["crossing_suffix"], "")
                    self.assertEqual(actual["angle_radians"], 0.0)
                    self.assertEqual(actual["joint_sleeper"], index - 1)
                    self.assertEqual(actual["key_towards"], -1)
                    _close(actual["x"], float(joint + offset * inch))
                    _close(actual["width"], float(10 * inch))
                    self.assertEqual((actual["length"], actual["near_y"],
                                      actual["far_y"]), (32.0, -16.0, 16.0))
                    count += 1
        self.assertEqual(count, 176)

    def test_profile_has_fixed_fresh_provenance_and_strict_identity(self):
        profile = self.profile()
        self.assertEqual(profile.to_record(), expected_profile())
        changed = profile.to_record()
        changed["source_flags"]["full_length"] = False
        self.assertEqual(profile.to_record(), expected_profile())
        for identifier, version in ((None, 1), (True, 1), ("unknown", 1),
                                    (PROFILE_ID, True), (PROFILE_ID, 2)):
            with self.assertRaises(domain.ReaTurnoutError):
                domain.ReaExitSleeperProfile(identifier, version)
        spec = domain.ReaTurnoutSpecification("B", 8.0)
        for invalid in (None, PROFILE_ID, {}, True):
            with self.assertRaises(domain.ReaTurnoutError):
                domain.rea_turnout_exit_sleepers(spec, invalid)
        with self.assertRaises(domain.ReaTurnoutError):
            domain.rea_turnout_exit_sleepers(
                domain.ReaTurnoutSpecification("B", 3.5), profile,
            )

    def test_old_bytes_and_signatures_round_trip_after_explicit_deselection(self):
        profile = self.profile()
        for kind in ("turnout", "crossover"):
            old_text = encoded(record(kind))
            old = state.rea_trackwork_intent_from_json(old_text)
            self.assertIsNone(old.exit_sleeper_profile)
            self.assertEqual(state.rea_trackwork_intent_to_json(old), old_text)
            selected = replace(old, exit_sleeper_profile=profile)
            expected = record(kind)
            expected["schema_version"] = 2
            expected["intent"]["exit_sleeper_profile"] = expected_profile()
            text = state.rea_trackwork_intent_to_json(selected)
            self.assertEqual(text, encoded(expected))
            self.assertEqual(state.rea_trackwork_intent_from_json(text), selected)
            self.assertNotEqual(state.rea_trackwork_intent_signature(selected),
                                state.rea_trackwork_intent_signature(old))
            reverted = replace(selected, exit_sleeper_profile=None)
            self.assertEqual(state.rea_trackwork_intent_to_json(reverted), old_text)
            self.assertEqual(state.rea_trackwork_intent_signature(reverted),
                             state.rea_trackwork_intent_signature(old))
            self.assertEqual(asdict(selected.source_specification),
                             asdict(old.source_specification))

    def test_invalid_profile_records_do_not_fall_back_to_old_schema(self):
        profile = self.profile()
        old = state.rea_trackwork_intent_from_json(encoded(record()))
        good = json.loads(state.rea_trackwork_intent_to_json(
            replace(old, exit_sleeper_profile=profile),
        ))
        bad_records = []
        for version in (1, True, 3, "2"):
            value = copy.deepcopy(good)
            value["schema_version"] = version
            bad_records.append(value)
        for field in expected_profile():
            value = copy.deepcopy(good)
            del value["intent"]["exit_sleeper_profile"][field]
            bad_records.append(value)
        for replacement in (None, {}, PROFILE_ID):
            value = copy.deepcopy(good)
            value["intent"]["exit_sleeper_profile"] = replacement
            bad_records.append(value)
        for path, value in (
            (("nominal_sleeper_length_mm",), 32),
            (("nominal_sleeper_length_mm",), 34.0),
            (("source_gauge_identity",), "00-BF"),
            (("calculation_revision",), True),
            (("source_flags", "full_length"), 1),
            (("source_flags", "tb_roll_percent"), 1),
            (("source_flags", "frackeq"), False),
            (("source_flags", "new_flag"), 0),
        ):
            bad = copy.deepcopy(good)
            target = bad["intent"]["exit_sleeper_profile"]
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            bad_records.append(bad)
        missing = copy.deepcopy(good)
        del missing["intent"]["exit_sleeper_profile"]
        bad_records.append(missing)
        for bad in bad_records:
            with self.subTest(bad=bad):
                with self.assertRaises(state.ReaTrackworkStateError):
                    state.rea_trackwork_intent_from_json(encoded(bad))
        duplicate = encoded(good).replace('"full_length":true',
                                         '"full_length":true,"full_length":true')
        with self.assertRaises(state.ReaTrackworkStateError):
            state.rea_trackwork_intent_from_json(duplicate)

    def test_selected_geometry_keeps_existing_rows_and_uses_source_body_frame(self):
        profile = self.profile()
        module = complete_railway_module()
        document = types.SimpleNamespace(turnouts=[], crossovers=[])
        adapter = ReaTurnoutGeometryAdapter(module)
        for width in (28.0, 44.0):
            module.turnout_host_template_dimensions = lambda doc, obj: (width, 2.0)
            for curvature in (0.0, 1 / 3000, -1 / 3000):
                source_host = host(module, curvature)
                for sign, hand in ((1, module.TURNOUT_HAND_LEFT),
                                   (-1, module.TURNOUT_HAND_RIGHT)):
                    for direction, orientation in (
                        (1, module.TURNOUT_ORIENTATION_FACING),
                        (-1, module.TURNOUT_ORIENTATION_TRAILING),
                    ):
                        args = (document, source_host, 2000.0, hand,
                                orientation, domain.ReaTurnoutSpecification("C", 9.25))
                        old = adapter.turnout(*args)
                        new = adapter.turnout(*args, exit_sleeper_profile=profile)
                        self.assertEqual(new["source_specification"], old["source_specification"])
                        self.assertEqual(new["dimensions"], old["dimensions"])
                        self.assertEqual(new["rails"], old["rails"])
                        self.assertEqual(new["timbers"][:-2], old["timbers"])
                        self.assertEqual(new["host_station_interval"], old["host_station_interval"])
                        self.assertNotIn("exit_sleeper_profile", old)
                        self.assertEqual(new["exit_sleeper_profile"], expected_profile())
                        for index, timber in enumerate(new["timbers"][-2:]):
                            self.assertEqual(timber["sequence"], len(old["timbers"]) + index + 1)
                            local = timber["local_points"]
                            _close(min(x for x, y in local), timber["x"] - 5 / 3)
                            _close(max(x for x, y in local), timber["x"] + 5 / 3)
                            self.assertEqual({y for x, y in local}, {-16.0, 16.0})
                            for (x, y), actual in zip(local, timber["points"]):
                                station = 2000.0 + direction * x
                                theta = curvature * station
                                cx = math.sin(theta) / curvature if curvature else station
                                cy = (1 - math.cos(theta)) / curvature if curvature else 0.0
                                _close(actual.x, cx - direction * sign * y * math.sin(theta))
                                _close(actual.y, cy + direction * sign * y * math.cos(theta))

    def test_stored_selection_rebuild_noop_rollback_and_change_back(self):
        profile = self.profile()
        fixture = WorkflowTests()
        fixture.setUpClass()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        initial = fixture.intent()
        obj = fixture.workflow.create(fixture.doc, initial)
        old_json = getattr(obj, state.REA_INTENT_JSON_PROPERTY)
        old_scene = fixture.store.view_for(obj).scene
        selected = replace(initial, exit_sleeper_profile=profile)
        fixture.workflow.update(fixture.doc, obj, selected)
        new_scene = fixture.store.view_for(obj).scene
        self.assertEqual(len(new_scene.lines), len(old_scene.lines) + 2)
        self.assertEqual(new_scene.lines[:-2], old_scene.lines)
        commits = fixture.doc.commits
        fixture.workflow.update(fixture.doc, obj, selected)
        self.assertEqual(fixture.doc.commits, commits)
        fixture.workflow.rebuild(fixture.doc, obj)
        self.assertEqual(fixture.store.view_for(obj).scene, new_scene)
        prepared = fixture.workflow.prepare(fixture.doc, initial, existing=obj)
        other = fixture.subject.ReaTrackworkWorkflow(
            fixture.module, fixture.store, fixture.workflow.scene_factory,
        )
        other.update(fixture.doc, obj, initial)
        with self.assertRaisesRegex(
            ValueError, "the edited intent changed after preparation",
        ):
            fixture.workflow.commit(fixture.doc, prepared)
        self.assertEqual(getattr(obj, state.REA_INTENT_JSON_PROPERTY), old_json)
        self.assertEqual(fixture.store.view_for(obj).scene, old_scene)
        fixture.doc.fail_commit = True
        with self.assertRaises(RuntimeError):
            fixture.workflow.update(fixture.doc, obj, selected)
        fixture.doc.fail_commit = False
        self.assertEqual(getattr(obj, state.REA_INTENT_JSON_PROPERTY), old_json)
        self.assertEqual(fixture.store.view_for(obj).scene, old_scene)

    def test_crossover_adds_two_exits_per_road_without_changing_connector(self):
        profile = self.profile()
        fixture = WorkflowTests()
        fixture.setUpClass()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        intent = fixture.intent(entity_kind="crossover", host_names=("HostA", "HostB"),
                                orientation=None, arrangement="Facing crossover",
                                handing="Automatic handing", minimum_radius_mm=600.0)
        old = fixture.workflow._calculate(fixture.doc, intent)
        selected = replace(intent, exit_sleeper_profile=profile)
        new = fixture.workflow._calculate(fixture.doc, selected)
        self.assertEqual(new["connector"], old["connector"])
        self.assertEqual(new["radius_assessment"], old["radius_assessment"])
        for key in ("turnout_a", "turnout_b"):
            self.assertEqual(new[key]["timbers"][:-2], old[key]["timbers"])
            self.assertEqual([row["identifier"] for row in new[key]["timbers"][-2:]], ["E1", "E2"])
            self.assertEqual(new[key]["exit_sleeper_profile"], expected_profile())
        obj = fixture.workflow.create(fixture.doc, selected)
        scene = fixture.store.view_for(obj).scene
        self.assertEqual(len([line for line in scene.lines if line.visual_id.endswith(":E1")]), 2)
        self.assertEqual(len([line for line in scene.lines if line.visual_id.endswith(":E2")]), 2)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ExitSleeperTests),
    )
    if result.wasSuccessful():
        print("REA source exit sleeper checks passed")
    raise SystemExit(not result.wasSuccessful())
