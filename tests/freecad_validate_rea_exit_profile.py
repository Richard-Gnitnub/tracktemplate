"""Hosted native checks for the explicitly selected REA exit-sleeper profile.

Import and discovery load no host or product modules. The frozen baseline
entry supplies runtime qualification and disposable document lifecycle only.
This separate report provides no GUI or production qualification.
"""

from dataclasses import replace
from decimal import Decimal, localcontext
import hashlib
import json
import os
import time
import unittest

import freecad_validate_rea_trackwork as baseline


PROFILE_ID = "templot-556b-00-D0GAF-32mm-full-exit"
BASE_ENTRY = "tests/freecad_validate_rea_trackwork.py"
BASE_ENTRY_SHA256 = (
    "ac316a5e49794361186f0f78e54db45839ca77f6d0b3905745b350c86c558e3d"
)


def _expected_checks(mode):
    if mode == "readiness":
        return {
            "profile_constructors": 1, "profile_constructor_refusals": 1,
            "schema2_round_trips": 1, "schema2_refusals": 2,
        }
    return {
        "source_roads": 3, "baseline_rail_records": 90,
        "baseline_timber_records": 96, "unchanged_connector_paths": 4,
        "exit_body_records": 6, "exit_local_corners": 24,
        "exit_mapped_points": 102, "exit_scene_lines": 6,
        "initial_selected_scene_lines": 196, "canonical_reads": 12,
        "schema1_reads": 4, "schema2_reads": 8,
        "successful_profile_toggles": 4, "default_scene_equalities": 3,
        "reselect_scene_equalities": 2, "rollback_scene_equalities": 1,
        "redo_scene_equalities": 1, "reopen_scene_equalities": 2,
        "no_op": 1, "post_write_rollback": 1, "stale_profile_refusal": 1,
        "undo_redo": 2, "save_reopen": 2,
    }


def _base_entry_digest():
    digest = hashlib.sha256((baseline.ROOT / BASE_ENTRY).read_bytes()).hexdigest()
    if digest != BASE_ENTRY_SHA256:
        raise RuntimeError("The inherited native entry changed.")
    return digest


class Readiness(baseline.Readiness):
    @classmethod
    def setUpClass(cls):
        digest = _base_entry_digest()
        super().setUpClass()
        cls.state["input_sha256"][BASE_ENTRY] = digest

    def test_profile_contract_and_entry(self):
        from tracktemplate.application import rea_turnout_state as state
        from tracktemplate.domain.rea_turnout import (
            ReaExitSleeperProfile,
            ReaTurnoutError,
        )

        super().test_imports_runtime_and_entry()
        profile = ReaExitSleeperProfile(PROFILE_ID)
        self.assertEqual(profile.profile_id, PROFILE_ID)
        self.assertEqual(profile.schema_version, 1)
        self.count("profile_constructors")
        with self.assertRaises(ReaTurnoutError):
            ReaExitSleeperProfile("unknown-profile")
        self.count("profile_constructor_refusals")
        # This frozen helper constructs an immutable value, without geometry.
        intent = replace(baseline.Native._intent(self),
                         exit_sleeper_profile=profile)
        text = state.rea_trackwork_intent_to_json(intent)
        record = json.loads(text)
        self.assertEqual(record["schema_version"], 2)
        self.assertEqual(record["intent"]["exit_sleeper_profile"],
                         profile.to_record())
        self.assertEqual(state.rea_trackwork_intent_from_json(text), intent)
        self.count("schema2_round_trips")
        for invalid in (None, dict(profile.to_record(),
                                   profile_id="unknown-profile")):
            record["intent"]["exit_sleeper_profile"] = invalid
            with self.assertRaises(state.ReaTrackworkStateError):
                state.rea_trackwork_intent_from_json(json.dumps(record))
            self.count("schema2_refusals")
        self.assertEqual(_case_names("native"), (
            "test_turnout_selected_toggle_and_reopen",
            "test_crossover_selected_toggle_and_reopen",
        ))
        self.assertEqual(self.state["app"].listDocuments(), {})
        self.assertEqual(self.state["documents_created"], 0)


class Native(baseline.Native):
    @classmethod
    def setUpClass(cls):
        digest = _base_entry_digest()
        super().setUpClass()
        cls.state["input_sha256"][BASE_ENTRY] = digest

    def _selected(self, crossover=False):
        from tracktemplate.domain.rea_turnout import ReaExitSleeperProfile

        return replace(self._intent(crossover), exit_sleeper_profile=(
            ReaExitSleeperProfile(PROFILE_ID)
        ))

    def _read(self, obj, expected):
        from tracktemplate.application.rea_turnout_state import (
            REA_INTENT_JSON_PROPERTY,
        )

        super()._read(obj, expected)
        record = json.loads(getattr(obj, REA_INTENT_JSON_PROPERTY))
        profile = expected.exit_sleeper_profile
        version = 1 if profile is None else 2
        self.assertEqual(record["schema_version"], version)
        if profile is None:
            self.assertNotIn("exit_sleeper_profile", record["intent"])
        else:
            self.assertEqual(record["intent"]["exit_sleeper_profile"],
                             profile.to_record())
        self.count("schema" + str(version) + "_reads")

    def _geometry(self, intent):
        if intent.entity_kind == "turnout":
            return self.session.prepare_rea_turnout_geometry(
                self.doc, self.hosts[0], intent.reference_chainage_mm,
                intent.handing, intent.orientation, intent.source_specification,
                exit_sleeper_profile=intent.exit_sleeper_profile,
            )
        return self.session.prepare_rea_crossover_geometry(
            self.doc, *self.hosts, intent.reference_chainage_mm,
            intent.source_specification, arrangement=intent.arrangement,
            handing=intent.handing, minimum_radius=intent.minimum_radius_mm,
            exit_sleeper_profile=intent.exit_sleeper_profile,
        )

    def _exit_bodies(self, old, selected, offset, side, intent, lines):
        from validate_phase1_turnout import _close

        for key in ("source_specification", "host_identity", "toe_chainage",
                    "handing", "orientation", "dimensions", "mapping",
                    "host_station_interval"):
            self.assertEqual(selected[key], old[key], key)
        self.assertNotIn("exit_sleeper_profile", old)
        self.assertEqual(selected["exit_sleeper_profile"],
                         intent.exit_sleeper_profile.to_record())
        self.assertEqual(len(old["rails"]), 30)
        self.assertEqual(len(selected["rails"]), 30)
        for actual, wanted in zip(selected["rails"], old["rails"]):
            self.assertEqual(actual, wanted)
            self.count("baseline_rail_records")
        self.assertEqual(len(old["timbers"]), 32)
        self.assertEqual(len(selected["timbers"]), 34)
        for actual, wanted in zip(selected["timbers"][:-2], old["timbers"]):
            self.assertEqual(actual, wanted)
            self.count("baseline_timber_records")
        expected = next(row for row in self.fixture["cases"]
                        if row["switch"] == "B"
                        and float(row["crossing_ratio"]) == 8.0)
        with localcontext() as context:
            context.prec = 50
            # B8 has six vee timbers. Derive J from the independent nose.
            joint = Decimal(expected["dimensions"]["blunt_nose_x"]) + (
                Decimal(4) + Decimal("12.5") + 5 * 30
            ) / 3
            centers = tuple(float(joint + distance / 3)
                            for distance in (Decimal(12), Decimal("38.5")))
        direction = (1 if old["orientation"]
                     == self.module.TURNOUT_ORIENTATION_FACING else -1)
        hand = 1 if old["handing"] == self.module.TURNOUT_HAND_LEFT else -1
        for index, (body, center) in enumerate(zip(
            selected["timbers"][-2:], centers,
        )):
            identifier = "E" + str(index + 1)
            for key, value in (
                ("identifier", identifier), ("section", "exit"),
                ("crossing_suffix", ""), ("angle_radians", 0.0),
                ("joint_sleeper", index - 1), ("key_towards", -1),
                ("sequence", 33 + index), ("length", 32.0),
                ("near_y", -16.0), ("far_y", 16.0),
            ):
                self.assertEqual(body[key], value, key)
            _close(body["x"], center)
            _close(body["width"], 10 / 3)
            self.count("exit_body_records")
            lower, upper = center - 5 / 3, center + 5 / 3
            # Frozen B15 outline: seven intervals, rounded to nine decimals.
            xs = [round(lower + (upper - lower) * step / 7, 9)
                  for step in range(8)]
            points = ([(x, -16.0) for x in xs]
                      + [(x, 16.0) for x in reversed(xs)] + [(lower, -16.0)])
            self.assertEqual(len(body["local_points"]), 17)
            self.assertEqual(len(body["points"]), 17)
            for position, wanted in zip((0, 7, 8, 15), (
                (lower, -16.0), (upper, -16.0),
                (upper, 16.0), (lower, 16.0),
            )):
                for actual, coordinate in zip(body["local_points"][position],
                                              wanted):
                    _close(actual, coordinate)
                self.count("exit_local_corners")
            for local, actual, wanted in zip(body["local_points"],
                                              body["points"], points):
                _close(local[0], wanted[0])
                _close(local[1], wanted[1])
                _close(actual.x, old["toe_chainage"] + direction * wanted[0])
                _close(actual.y, offset + direction * hand * wanted[1])
                _close(actual.z, 0.0)
                self.count("exit_mapped_points")
            visual_id = ":".join((intent.entity_id, side, "timber", identifier))
            self.assertEqual(lines[visual_id].points, tuple(
                (point.x, point.y, point.z) for point in body["points"]
            ))
            self.count("exit_scene_lines")
        self.count("source_roads")

    def _initial(self, intent):
        unselected = replace(intent, exit_sleeper_profile=None)
        # A separate coordinator preserves the selected commit token.
        default_scene = self._workflow().prepare(self.doc, unselected).scene
        old, selected = self._geometry(unselected), self._geometry(intent)
        prepared = self.workflow.prepare(self.doc, intent)
        lines = {line.visual_id: line for line in prepared.scene.lines}
        self.assertEqual(len(lines), len(prepared.scene.lines))
        if intent.entity_kind == "turnout":
            roads = ((old, selected, 0.0, "to"),)
            expected_count = 64
        else:
            self.assertEqual(selected["connector"], old["connector"])
            self.assertEqual(selected["radius_assessment"],
                             old["radius_assessment"])
            self.assertTrue(selected["radius_assessment"]["accepted"])
            roads = ((old["turnout_a"], selected["turnout_a"], 0.0, "a"),
                     (old["turnout_b"], selected["turnout_b"], 50.0, "b"))
            connectors = [line for line in default_scene.lines
                          if ":connector:" in line.visual_id]
            self.assertEqual(len(connectors), 4)
            for line in connectors:
                self.assertEqual(lines[line.visual_id], line)
                self.count("unchanged_connector_paths")
            expected_count = 132
        for old_road, road, offset, side in roads:
            self._exit_bodies(old_road, road, offset, side, intent, lines)
        self.assertEqual(tuple(line.visual_id for line in prepared.scene.lines
                               if line.visual_id.endswith((":E1", ":E2"))),
                         tuple(":".join((intent.entity_id, side, "timber", name))
                               for _old, _road, _offset, side in roads
                               for name in ("E1", "E2")))
        self.assertEqual(tuple(line for line in prepared.scene.lines
                               if not line.visual_id.endswith((":E1", ":E2"))),
                         default_scene.lines)
        self.assertEqual(len(lines), expected_count)
        self.count("initial_selected_scene_lines", expected_count)
        return prepared, unselected, default_scene

    def _scene_equals(self, obj, intent, scene, counter):
        actual = self._workflow().prepare(self.doc, intent, existing=obj).scene
        self.assertEqual(actual, scene)
        self.count(counter)

    def _save_reopen(self, obj, intent, scene):
        super()._save_reopen(obj, intent, scene)
        self.count("reopen_scene_equalities")

    def test_turnout_selected_toggle_and_reopen(self):
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            ReaTrackworkDocumentError,
        )
        from tracktemplate.application.rea_turnout_state import (
            REA_INTENT_JSON_PROPERTY,
        )

        selected = self._selected()
        first, unselected, default_scene = self._initial(selected)
        obj = self.workflow.commit(self.doc, first)
        obj.Label = "Operator turnout with exit sleepers"
        self._read(obj, selected)
        history = baseline._history(self.doc)
        canonical = getattr(obj, REA_INTENT_JSON_PROPERTY)
        self.assertIs(self.workflow.update(self.doc, obj, selected), obj)
        self.assertEqual(baseline._history(self.doc), history)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.count("no_op")
        names = tuple(item.Name for item in self.doc.Objects)
        label = obj.Label
        self.assertEqual(len(names), 4)
        self.assertEqual(int(self.doc.RedoCount), 0)

        def reject_after_write(candidate, scene, signature):
            self._read(candidate, unselected)
            raise RuntimeError("Deliberate exit-profile post-write failure")

        failing = self._workflow(view_factory=reject_after_write)
        with self.assertRaises(ReaTrackworkDocumentError) as caught:
            failing.update(self.doc, obj, unselected)
        self.assertEqual(caught.exception.code, "transaction-failed")
        self.assertTrue(caught.exception.recoverable)
        self._read(obj, selected)
        self.assertEqual(baseline._history(self.doc), history)
        self.assertEqual(tuple(item.Name for item in self.doc.Objects), names)
        self.assertEqual(obj.Label, label)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self._scene_equals(obj, selected, first.scene,
                           "rollback_scene_equalities")
        self.count("post_write_rollback")
        self.workflow.update(self.doc, obj, unselected)
        self._read(obj, unselected)
        self._scene_equals(obj, unselected, default_scene,
                           "default_scene_equalities")
        prepared = self.workflow.prepare(self.doc, selected, existing=obj)
        self._workflow().update(self.doc, obj, selected)
        self._read(obj, selected)
        self._scene_equals(obj, selected, first.scene,
                           "reselect_scene_equalities")
        history = baseline._history(self.doc)
        with self.assertRaisesRegex(
            ValueError, "the edited intent changed after preparation",
        ):
            self.workflow.commit(self.doc, prepared)
        self.assertEqual(baseline._history(self.doc), history)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.count("stale_profile_refusal")
        self.count("successful_profile_toggles", 2)
        self.doc.undo()
        self._read(obj, unselected)
        self._scene_equals(obj, unselected, default_scene,
                           "default_scene_equalities")
        self.doc.redo()
        self._read(obj, selected)
        self._scene_equals(obj, selected, first.scene, "redo_scene_equalities")
        self.count("undo_redo", 2)
        self.assertEqual(obj.Label, label)
        self._save_reopen(obj, selected, first.scene)
        self.success = True

    def test_crossover_selected_toggle_and_reopen(self):
        selected = self._selected(crossover=True)
        first, unselected, default_scene = self._initial(selected)
        obj = self.workflow.commit(self.doc, first)
        obj.Label = "Operator crossover with exit sleepers"
        self._read(obj, selected)
        self.assertEqual(len(self.doc.Objects), 4)
        self.workflow.update(self.doc, obj, unselected)
        self._read(obj, unselected)
        self._scene_equals(obj, unselected, default_scene,
                           "default_scene_equalities")
        self.workflow.update(self.doc, obj, selected)
        self._read(obj, selected)
        self._scene_equals(obj, selected, first.scene,
                           "reselect_scene_equalities")
        self.count("successful_profile_toggles", 2)
        self._save_reopen(obj, selected, first.scene)
        self.success = True


class _ReportedSuite(unittest.TestSuite):
    def run(self, result, debug=False):
        started = time.monotonic()
        before = result.testsRun
        previous_failfast = result.failfast
        result.failfast = True
        try:
            super().run(result, debug)
        finally:
            result.failfast = previous_failfast
        state = self.state
        count = result.testsRun - before
        app = state.get("app")
        documents = 0 if self.mode == "readiness" else 2
        if (result.wasSuccessful() and not result.skipped
                and count == self.expected and app is not None
                and not app.listDocuments()
                and state["documents_created"] == documents
                and state["checks"] == _expected_checks(self.mode)):
            payload = {
                "mode": self.mode, "status": "PASS", "tests": count,
                "failures": 0, "errors": 0, "skips": 0,
                "documents_created": documents, "documents_remaining": 0,
                "input_sha256": state["input_sha256"],
                "checks": state["checks"],
                "elapsed_seconds": time.monotonic() - started,
            }
            print("TRACKTEMPLATE_REA_EXIT_PROFILE=" + json.dumps(
                payload, sort_keys=True, allow_nan=False,
            ), flush=True)
        return result


def _case_names(mode):
    return (("test_profile_contract_and_entry",) if mode == "readiness" else (
        "test_turnout_selected_toggle_and_reopen",
        "test_crossover_selected_toggle_and_reopen",
    ))


def load_tests(loader, tests, pattern):
    """Select only the named exit-profile cases, never inherited tests."""
    mode = os.environ.get("TRACKTEMPLATE_REA_MODE")
    if mode not in ("readiness", "native"):
        raise ValueError("TRACKTEMPLATE_REA_MODE must be readiness or native.")
    selected = Readiness if mode == "readiness" else Native
    state = {"documents_created": 0,
             "checks": dict.fromkeys(_expected_checks(mode), 0)}
    selected.state = state
    cases = tuple(selected(name) for name in _case_names(mode))
    expected_ids = tuple(__name__ + "." + selected.__name__ + "." + name
                         for name in _case_names(mode))
    if tuple(case.id() for case in cases) != expected_ids:
        raise RuntimeError("The selected exit-profile cases changed.")
    suite = _ReportedSuite(cases)
    suite.state, suite.mode = state, mode
    suite.expected = 1 if mode == "readiness" else 2
    if suite.countTestCases() != suite.expected:
        raise RuntimeError("The approved exit-profile test count changed.")
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
