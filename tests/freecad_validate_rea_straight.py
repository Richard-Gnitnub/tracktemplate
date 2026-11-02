"""Hosted native qualification of the explicit REA B straight closure.

Import/discovery loads no product or FreeCAD modules. The frozen baseline
owns runtime, disposable hosts, transactions and save/reopen cleanup.
Source equations: Templot 556b, Martin Wynne and OpenTemplot contributors,
GPL-3.0-or-later; tracked independent arithmetic supplies the expectations.
This entry supplies no GUI, physical-fit or production evidence.
"""

from dataclasses import replace
import hashlib
import json
import math
import os
import time
import unittest

import freecad_validate_rea_trackwork as baseline


BASE_ENTRY = "tests/freecad_validate_rea_trackwork.py"
BASE_SHA256 = (
    "ac316a5e49794361186f0f78e54db45839ca77f6d0b3905745b350c86c558e3d"
)
ORACLE = "tests/validate_rea_straight_closure.py"
ORACLE_SHA256 = (
    "3639a9141403bc95147305ac523932c3ef6d8134e87cb153ba588f43aa61fdb9"
)
HEEL_N = 18.417941404842995
BOUNDARIES = (
    "0x1.26afe3537fbd6p+4", "0x1.26afe3537fbd7p+4",
    "0x1.26afe353ae7fdp+4", "0x1.26afe353ae7fep+4",
)
PROFILE_ID = "templot-556b-00-D0GAF-32mm-full-exit"


def _expected_checks(mode):
    if mode == "readiness":
        return {"binding_checks": 1, "canonical_round_trips": 5,
                "invalid_source_refusals": 5}
    return {
        "source_roads": 3, "source_scalars": 27, "rail_records": 90,
        "rail_anchors": 36,
        "timber_records": 135, "exit_body_records": 6,
        "scene_lines": 235, "boundary_cases": 4, "boundary_line_points": 2,
        "cap_controls": 1, "unsupported_controls": 3,
        "canonical_reads": 9, "no_op": 1, "source_changeback": 2,
        "undo_redo": 2, "save_reopen": 2, "reopen_scene_equalities": 2,
        "changeback_scene_equalities": 1, "redo_scene_equalities": 1,
        "boundary_refusal": 1,
    }


def _inputs():
    result = {}
    for path, expected in ((BASE_ENTRY, BASE_SHA256), (ORACLE, ORACLE_SHA256)):
        result[path] = hashlib.sha256(
            (baseline.ROOT / path).read_bytes(),
        ).hexdigest()
        if result[path] != expected:
            raise RuntimeError("Frozen native helper/oracle changed: " + path)
    return result


def _stations(ratio):
    from validate_rea_straight_closure import independent_line

    fine = independent_line(ratio)["fine_point_x"]
    blunt = fine + 0.125 / math.sin(math.atan(1 / ratio) / 2)
    first = blunt + 4 / 3 - 50
    records = [("J2", -17.5, 4.0), ("J1", -24.5 / 3, 4.0)]
    station = 0.0
    for index, spacing in enumerate((3.5, 28, 28, 28, 28, 28, 28,
                                     28.5, 28.5, 28.5, 26, 24), 1):
        station += spacing / 3
        records.append(("T1" if index == 12 else "S" + str(index),
                        station, 4.0))
    for index in range(1, 19):
        records.append(("T" + str(index + 1), station + index * (
            first - 25 / 3 - station) / 18, 4.0))
    for index, suffix in enumerate(("", "", "Z", "Y", "X", "A", "B", "C",
                                    "D", "", "", "", ""), 1):
        records.append(("X" + str(index) + ("-" + suffix if suffix else ""),
                        first + (index - 1) * 10, 4.0))
    for index, offset in enumerate((12, 38.5), 1):
        records.append(("E" + str(index), blunt + 75.5 + offset / 3, 10 / 3))
    return records


class Readiness(baseline.Readiness):
    @classmethod
    def setUpClass(cls):
        inputs = _inputs()
        super().setUpClass()
        cls.state["input_sha256"].update(inputs)

    def test_line_contract_and_entry(self):
        from tracktemplate.application import rea_turnout_state as state
        from tracktemplate.compatibility.rea_turnout_rails import (
            validate_rea_inner_gauge_binding,
        )
        from tracktemplate.domain.rea_turnout import (
            ReaExitSleeperProfile, ReaTurnoutError, ReaTurnoutSpecification,
        )

        super().test_imports_runtime_and_entry()
        validate_rea_inner_gauge_binding(self.module)
        self.session._validate_binding()
        self.count("binding_checks")
        for ratio in (HEEL_N, *(float.fromhex(x) for x in BOUNDARIES)):
            intent = replace(baseline.Native._intent(self),
                             source_specification=ReaTurnoutSpecification(
                                 "B", ratio),
                             exit_sleeper_profile=ReaExitSleeperProfile(
                                 PROFILE_ID))
            text = state.rea_trackwork_intent_to_json(intent)
            self.assertEqual(
                state.rea_trackwork_intent_from_json(text), intent,
            )
            self.assertEqual(json.loads(text)["schema_version"], 2)
            self.count("canonical_round_trips")
        for invalid in (True, math.nan, math.inf, "18", 10 ** 400):
            with self.assertRaises(ReaTurnoutError):
                ReaTurnoutSpecification("B", invalid)
            self.count("invalid_source_refusals")
        self.assertEqual(self.state["app"].listDocuments(), {})
        self.assertEqual(self.state["documents_created"], 0)


class Native(baseline.Native):
    @classmethod
    def setUpClass(cls):
        inputs = _inputs()
        super().setUpClass()
        cls.state["input_sha256"].update(inputs)

    def _selected(self, crossover=False):
        from tracktemplate.domain.rea_turnout import (
            ReaExitSleeperProfile, ReaTurnoutSpecification,
        )
        return replace(self._intent(crossover), source_specification=(
            ReaTurnoutSpecification("B", HEEL_N)), exit_sleeper_profile=(
                ReaExitSleeperProfile(PROFILE_ID)))

    def _boundaries(self):
        from tracktemplate.domain import rea_turnout as source
        from validate_rea_straight_closure import expected_inner
        from validate_phase1_turnout import _close

        for index, text in enumerate(BOUNDARIES):
            ratio = float.fromhex(text)
            inch = 25.4 / 76.2
            k1 = math.atan(1 / 32)
            k2 = math.asin((257 * inch - 88 * inch * math.cos(k1))
                           / (7356 * inch) + math.sin(k1))
            k3 = math.atan(1 / ratio)
            print("TRACKTEMPLATE_REA_STRAIGHT_BOUNDARY=" + json.dumps({
                "ratio_hex": text, "k2_hex": k2.hex(), "k3_hex": k3.hex(),
                "absolute_angle_delta": abs(k2 - k3),
                "binary64_source_predicate": abs(k2 - k3) < 1e-12,
            }, sort_keys=True, allow_nan=False), flush=True)
            spec = source.ReaTurnoutSpecification("B", ratio)
            if index == 3:
                with self.assertRaises(source.ReaTurnoutError) as caught:
                    source.rea_turnout_dimensions(spec)
                self.assertEqual(caught.exception.code,
                                 "unsupported-negative-closure")
            else:
                dims = source.rea_turnout_dimensions(spec)
                diagnostic = (text, dims["k2"].hex(), dims["k3"].hex())
                if index == 0:
                    self.assertNotIn("source_closure_kind", dims, diagnostic)
                    self.assertTrue(dims["auto_fit_cap"], diagnostic)
                    self.assertEqual(dims["turnout_radius"], 2452.0)
                    self.assertGreater(dims["turnout_curve_length"], 0.0)
                else:
                    self.assertEqual(dims["source_closure_kind"], "line",
                                     diagnostic)
                    self.assertFalse(dims["auto_fit_cap"])
                    self.assertEqual(dims["check_turnout_working_mode"],
                                     "straight crossing leg")
                    for actual, wanted in zip(
                        self.module._rea_c10_inner_gauge_face(dims, 150),
                        expected_inner(150, ratio),
                    ):
                        _close(actual, wanted)
                    stations = source.rea_turnout_timber_stations(spec)
                    self.assertEqual(len(stations), 45)
                    for actual, (name, x, width) in zip(
                        stations, _stations(ratio)[:45],
                    ):
                        self.assertEqual(actual["identifier"], name)
                        _close(actual["x"], x)
                        _close(actual["width"], width)
                    self.count("boundary_line_points")
            self.count("boundary_cases")
        capped = source.rea_turnout_dimensions(source.ReaTurnoutSpecification(
            "B", 18.417941403843))
        self.assertTrue(capped["auto_fit_cap"])
        self.assertEqual(capped["turnout_radius"], 2452.0)
        self.assertGreater(capped["turnout_curve_length"], 0.0)
        self.count("cap_controls")
        for size, ratio in (("B", 3.999), ("B", 20.125),
                            ("C", 22.70237204880366)):
            with self.assertRaises(source.ReaTurnoutError):
                source.rea_turnout_dimensions(
                    source.ReaTurnoutSpecification(size, ratio))
            self.count("unsupported_controls")

    def _road(self, road, offset):
        from validate_phase1_turnout import _close
        from validate_rea_straight_closure import (
            independent_line, expected_inner,
        )

        dims = road["dimensions"]
        for key, wanted in independent_line().items():
            _close(dims[key], wanted)
            self.count("source_scalars")
        self.assertEqual(dims["source_closure_kind"], "line")
        self.assertEqual(dims["turnout_origin_x"], 0.0)
        self.assertEqual(dims["turnout_origin_y"], 0.0)
        self.assertFalse(dims["auto_fit_cap"])
        self.assertEqual(len(road["rails"]), 30)
        self.assertEqual(len(road["timbers"]), 47)
        for index, (body, (name, x, width)) in enumerate(zip(
            road["timbers"], _stations(HEEL_N),
        ), 1):
            self.assertEqual(body["identifier"], name)
            self.assertEqual(body["sequence"], index)
            self.assertEqual(body["angle_radians"], 0.0)
            _close(body["x"], x)
            _close(body["width"], width)
            if index > 45:
                self.assertEqual((body["near_y"], body["far_y"]), (-16, 16))
                self.count("exit_body_records")
            else:
                self.count("timber_records")
        k = math.atan(1 / HEEL_N)
        faces = {"turnout-side stock rail gauge face": 16.5,
                 "turnout-side stock rail outer face": 16.5 + 11 / 12,
                 "curved switch and closure rail gauge face": 0.0,
                 "curved switch and closure rail outer face": -11 / 12}
        fine = independent_line()["fine_point_x"]
        a_timber = fine + 0.125 / math.sin(k / 2) + 4 / 3
        flare = math.asin((1.75 / 3) / 12)
        width, bend = 11 / 12, (11 / 12) / math.cos(flare / 2)
        wing_start = fine - math.sin(k) + (a_timber - fine + 14) * math.cos(k)
        wing_end = wing_start + 12 / math.cos(flare) * math.cos(k + flare)
        check_fp = fine - 15.5 * math.sin(k)
        after = (a_timber - check_fp) / math.cos(k) + 14
        before = 48 - after
        check_in = check_fp - before * math.cos(k)
        check_out = check_fp + after * math.cos(k)
        check = (check_in - 12 / math.cos(flare) * math.cos(k + flare),
                 check_in, check_out,
                 check_out + 12 / math.cos(flare) * math.cos(k - flare))
        anchors = {
            False: ((wing_start, wing_end), check),
            True: ((wing_start - bend * math.sin(k + flare / 2),
                    wing_end - width * math.sin(k + flare)), tuple(
                        value + shift for value, shift in zip(check, (
                            width * math.sin(k + flare),
                            bend * math.sin(k + flare / 2),
                            bend * math.sin(k - flare / 2),
                            width * math.sin(k - flare))))),
        }
        witnessed = set()
        for rail in road["rails"]:
            self.count("rail_records")
            if rail["name"] in faces:
                q = faces[rail["name"]]
                for x, y in rail["local_points"]:
                    if x + q * math.sin(k) > dims["heel_lead"] + 1e-8:
                        _close(y, expected_inner(x)[1]
                               + q / math.cos(k) - 8.25)
                        self.count("line_rail_samples")
                        witnessed.add(rail["name"])
            elif rail["name"].startswith(("turnout-side wing rail ",
                                            "turnout-side wing flare ",
                                            "turnout-side check rail ")):
                outer = rail["name"].endswith("outer face")
                wing, check = anchors[outer]
                is_check = rail["name"].startswith("turnout-side check")
                if is_check:
                    expected_x = check
                    for x in expected_x:
                        self.assertTrue(any(abs(point[0] - x) <= 1e-9
                                            for point in rail["local_points"]))
                        self.count("rail_anchors")
                elif "wing flare" in rail["name"]:
                    for point, x in zip((rail["local_points"][0],
                                         rail["local_points"][-1]), wing):
                        _close(point[0], x)
                        self.count("rail_anchors")
                for x, y in rail["local_points"]:
                    running = expected_inner(x)[1]
                    if is_check:
                        running += 16.5 / math.cos(k)
                        a, b, c, end = check
                        fraction = ((b - x) / (b - a) if x <= b else
                                    (x - c) / (end - c) if x >= c else 0.0)
                    else:
                        a, b = wing
                        fraction = (x - a) / (b - a) if x >= a else 0.0
                    offset_y = (1 + (width if outer else 0)
                                + fraction * 12 * math.sin(flare)
                                ) / math.cos(k)
                    _close(y, running + (-offset_y if is_check else offset_y)
                           - 8.25)
                    self.count("line_rail_samples")
                    witnessed.add(rail["name"])
        self.assertEqual(witnessed, set(faces) | {
            "turnout-side " + name + " " + face
            for name in ("wing rail", "wing flare", "check rail")
            for face in ("gauge face", "outer face")
        })
        direction = (1 if road["orientation"]
                     == self.module.TURNOUT_ORIENTATION_FACING else -1)
        hand = 1 if road["handing"] == self.module.TURNOUT_HAND_LEFT else -1
        for record in road["rails"] + road["timbers"]:
            self.assertEqual(len(record["local_points"]),
                             len(record["points"]))
            for local, world in zip(record["local_points"], record["points"]):
                _close(world.x, road["toe_chainage"] + direction * local[0])
                _close(world.y, offset + direction * hand * local[1])
                _close(world.z, 0.0)
                self.count("mapped_points")
        self.count("source_roads")

    def _prepared_line(self, intent):
        if intent.entity_kind == "turnout":
            geometry = self.session.prepare_rea_turnout_geometry(
                self.doc, self.hosts[0], intent.reference_chainage_mm,
                intent.handing, intent.orientation,
                intent.source_specification,
                exit_sleeper_profile=intent.exit_sleeper_profile)
            roads = (("to", geometry, 0.0),)
        else:
            geometry = self.session.prepare_rea_crossover_geometry(
                self.doc, *self.hosts, intent.reference_chainage_mm,
                intent.source_specification, arrangement=intent.arrangement,
                handing=intent.handing,
                minimum_radius=intent.minimum_radius_mm,
                exit_sleeper_profile=intent.exit_sleeper_profile)
            self.assertEqual(intent.minimum_radius_mm, 600.0)
            self.assertTrue(geometry["radius_assessment"]["accepted"])
            roads = (("a", geometry["turnout_a"], 0.0),
                     ("b", geometry["turnout_b"], 50.0))
        prepared = self.workflow.prepare(self.doc, intent)
        ordered_ids = []
        lines = {line.visual_id: line for line in prepared.scene.lines}
        self.assertEqual(len(lines), len(prepared.scene.lines))
        for side, road, offset in roads:
            self._road(road, offset)
            for kind, records, key in (
                ("rail", road["rails"], "name"),
                ("timber", road["timbers"], "identifier"),
            ):
                for record in records:
                    identity = ":".join((intent.entity_id, side, kind,
                                         record[key]))
                    ordered_ids.append(identity)
                    self.assertEqual(lines[identity].points, tuple(
                        (point.x, point.y, point.z)
                        for point in record["points"]))
        actual_ids = tuple(line.visual_id for line in prepared.scene.lines)
        self.assertEqual(actual_ids[:len(ordered_ids)], tuple(ordered_ids))
        connectors = actual_ids[len(ordered_ids):]
        self.assertEqual(len(connectors), 4 if len(roads) == 2 else 0)
        self.assertTrue(all(":connector:" in name for name in connectors))
        self.assertEqual(len(lines), 77 if len(roads) == 1 else 158)
        self.count("scene_lines", len(lines))
        return prepared

    def _scene_equals(self, obj, intent, scene, counter):
        prepared = self._workflow().prepare(self.doc, intent, existing=obj)
        self.assertEqual(prepared.scene, scene)
        self.count(counter)

    def _save_reopen(self, obj, intent, scene):
        super()._save_reopen(obj, intent, scene)
        self.count("reopen_scene_equalities")

    def test_turnout_line_changeback_and_reopen(self):
        from tracktemplate.application.rea_turnout_state import (
            REA_INTENT_JSON_PROPERTY,
        )
        from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification

        self._boundaries()
        intent = self._selected()
        first = self._prepared_line(intent)
        obj = self.workflow.commit(self.doc, first)
        obj.Label = "Operator straight-closure turnout"
        self._read(obj, intent)
        history = baseline._history(self.doc)
        canonical = getattr(obj, REA_INTENT_JSON_PROPERTY)
        self.assertIs(self.workflow.update(self.doc, obj, intent), obj)
        self.assertEqual(baseline._history(self.doc), history)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.count("no_op")
        rejected = replace(intent, source_specification=(
            ReaTurnoutSpecification("B", float.fromhex(BOUNDARIES[3]))))
        names = tuple(item.Name for item in self.doc.Objects)
        with self.assertRaises(ValueError):
            self.workflow.update(self.doc, obj, rejected)
        self._read(obj, intent)
        self.assertEqual(baseline._history(self.doc), history)
        self.assertEqual(tuple(item.Name for item in self.doc.Objects), names)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.count("boundary_refusal")
        changed = replace(intent, source_specification=ReaTurnoutSpecification(
            "B", 8.0))
        self.workflow.update(self.doc, obj, changed)
        self._read(obj, changed)
        self.workflow.update(self.doc, obj, intent)
        self._read(obj, intent)
        self._scene_equals(obj, intent, first.scene,
                           "changeback_scene_equalities")
        self.count("source_changeback", 2)
        self.doc.undo()
        self._read(obj, changed)
        self.doc.redo()
        self._read(obj, intent)
        self._scene_equals(obj, intent, first.scene, "redo_scene_equalities")
        self.count("undo_redo", 2)
        self.assertEqual(obj.Label, "Operator straight-closure turnout")
        self._save_reopen(obj, intent, first.scene)
        self.success = True

    def test_crossover_line_and_reopen(self):
        intent = self._selected(crossover=True)
        first = self._prepared_line(intent)
        obj = self.workflow.commit(self.doc, first)
        obj.Label = "Operator straight-closure crossover"
        self._read(obj, intent)
        self.assertEqual(len(self.doc.Objects), 4)
        self._save_reopen(obj, intent, first.scene)
        self.success = True


class _ReportedSuite(unittest.TestSuite):
    def run(self, result, debug=False):
        started = time.monotonic()
        before, previous = result.testsRun, result.failfast
        result.failfast = True
        try:
            super().run(result, debug)
        finally:
            result.failfast = previous
        state, count = self.state, result.testsRun - before
        app = state.get("app")
        documents = 0 if self.mode == "readiness" else 2
        expected = _expected_checks(self.mode)
        checks = state["checks"]
        if self.mode == "native":
            expected.update({key: checks[key] for key in
                             ("mapped_points", "line_rail_samples")
                             if type(checks[key]) is int and checks[key] > 0})
        if (result.wasSuccessful() and not result.skipped
                and count == self.expected and app is not None
                and not app.listDocuments()
                and state["documents_created"] == documents
                and checks == expected):
            print("TRACKTEMPLATE_REA_STRAIGHT=" + json.dumps({
                "mode": self.mode, "status": "PASS", "tests": count,
                "failures": 0, "errors": 0, "skips": 0,
                "documents_created": documents, "documents_remaining": 0,
                "input_sha256": state["input_sha256"], "checks": checks,
                "elapsed_seconds": time.monotonic() - started,
            }, sort_keys=True, allow_nan=False), flush=True)
        return result


def load_tests(loader, tests, pattern):
    """Select exactly the straight readiness or two native cases."""
    mode = os.environ.get("TRACKTEMPLATE_REA_MODE")
    if mode not in ("readiness", "native"):
        raise ValueError("TRACKTEMPLATE_REA_MODE must be readiness or native.")
    selected = Readiness if mode == "readiness" else Native
    checks = dict.fromkeys(_expected_checks(mode), 0)
    if mode == "native":
        checks.update(mapped_points=0, line_rail_samples=0)
    state = {"documents_created": 0, "checks": checks}
    selected.state = state
    names = (("test_line_contract_and_entry",) if mode == "readiness" else (
        "test_turnout_line_changeback_and_reopen",
        "test_crossover_line_and_reopen"))
    suite = _ReportedSuite(tuple(selected(name) for name in names))
    suite.state, suite.mode = state, mode
    suite.expected = 1 if mode == "readiness" else 2
    if suite.countTestCases() != suite.expected:
        raise RuntimeError("The approved straight test count changed.")
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
