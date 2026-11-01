"""Hosted, import-safe native checks for explicit REA research documents.

Select readiness or native with TRACKTEMPLATE_REA_MODE. Importing this module
does not load FreeCAD or the product. Readiness creates no document. Native
checks use two disposable documents; they provide no GUI or production proof.
"""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-"
    "py3.13.15-qt6.11.2-coin4.0.10"
)
FIXTURE = "tests/fixtures/phase9b-rea-bc-source.json"
FIXTURE_SHA256 = (
    "d8c356a8cd84be1de0f6535abc09090a12dd82ecbb6083bd3ca65e19f43694f4"
)
INPUTS = (
    FIXTURE,
    "tests/validate_phase1_turnout.py",
    "reference/contracts/phase1-compatibility.json",
    "reference/contracts/phase1-transition-pilot.json",
    "TrackTemplate.FCMacro",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro",
)
CHECKS = (
    "source_scalars", "timber_records", "rail_anchors", "mapped_points",
    "scene_lines", "canonical_reads", "negative_controls", "undo_redo",
    "save_reopen", "no_op",
)


def _scene_factory(entity_id, lines):
    from tracktemplate.presentation.rea_trackwork import (
        ReaTrackworkLine,
        ReaTrackworkScene,
    )
    return ReaTrackworkScene(entity_id, tuple(
        ReaTrackworkLine(*line) for line in lines
    ))


def _history(document):
    return (int(document.UndoMode), int(document.UndoCount),
            int(document.RedoCount), tuple(document.UndoNames),
            tuple(document.RedoNames))


def _property(obj, kind, name, value):
    obj.addProperty("App::Property" + kind, name, "Native fixture")
    setattr(obj, name, value)


class _QualifiedCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "tests"))
        import FreeCAD as App
        from tracktemplate import api, bootstrap

        if sys.flags.optimize != 0 or App.GuiUp:
            raise RuntimeError("Native checks require assertions and no GUI.")
        if App.listDocuments():
            raise RuntimeError("Refusing a process with pre-existing documents.")
        cls.state["app"] = App
        cls.report = bootstrap.require_qualified_runtime(
            ROOT / "reference/contracts/phase1-compatibility.json",
        )
        if cls.report["compatibility_evaluation"]["matched_profile_id"] != PROFILE:
            raise RuntimeError("The approved native runtime is required.")
        cls.state["input_sha256"] = {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in INPUTS
        }
        if cls.state["input_sha256"][FIXTURE] != FIXTURE_SHA256:
            raise RuntimeError("Independent source fixture identity changed.")
        cls.fixture = json.loads((ROOT / FIXTURE).read_text(encoding="utf-8"))
        if cls.fixture["case_count"] != 88:
            raise RuntimeError("Unexpected independent source fixture count.")
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        if (launcher["FOUNDATION_RESULT"]["status"]
                != "modular-foundation-ready"):
            raise RuntimeError("The modular foundation did not qualify.")
        modular_api, loader = launcher["_load_foundation"](ROOT)
        if modular_api is not api:
            raise RuntimeError("The modular API resolved outside this checkout.")
        cls.session, _routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, loader,
        )
        cls.module = cls.session.module
        # Compose the actual ports, but create no document or scene here.
        cls._workflow()
        if App.listDocuments():
            raise RuntimeError("Product composition created a document.")
        print("TRACKTEMPLATE_HOSTED_RUNTIME=" + json.dumps(
            cls.report, sort_keys=True, allow_nan=False,
        ), flush=True)

    @classmethod
    def _workflow(cls, view_factory=None):
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            FreeCADReaTrackworkStore,
        )
        from tracktemplate.presentation.rea_trackwork import (
            attach_rea_trackwork_view,
        )
        store = FreeCADReaTrackworkStore(
            cls.report,
            view_factory=(attach_rea_trackwork_view if view_factory is None
                          else view_factory),
        )
        return cls.session.rea_trackwork_workflow(store, _scene_factory)

    def count(self, key, amount=1):
        self.state["checks"][key] += amount


class Readiness(_QualifiedCase):
    def test_imports_runtime_and_entry(self):
        self.assertEqual(self.state["app"].listDocuments(), {})
        self.assertEqual(self.state["documents_created"], 0)
        self.assertTrue(callable(self.session.prepare_rea_turnout_geometry))
        self.assertTrue(callable(self.session.prepare_rea_crossover_geometry))
        self.assertTrue(callable(self.session.rea_trackwork_workflow))


class Native(_QualifiedCase):
    def setUp(self):
        import Part

        self.app = self.state["app"]
        self.assertEqual(self.app.listDocuments(), {})
        self.success = False
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(
            prefix="rea-native-", dir=ROOT / "tmp",
        ))
        self.saved = self.folder / "research.FCStd"
        self.owned_names = set()
        self.addCleanup(self._cleanup)
        self.doc = self.app.newDocument("ReaNative")
        self.owned_names.add(self.doc.Name)
        self.state["documents_created"] += 1
        self.doc.UndoMode = 1
        self.settings = self.doc.addObject("App::FeaturePython", "Settings")
        for name, value in (
            ("GeneratedBy", self.module.GENERATOR_ID),
            ("GeneratedRole", "Settings"), ("TemplateSetID", "SET-001"),
            ("TrackConfigurationJSON", "[]"),
        ):
            _property(self.settings, "String", name, value)
        for name, value in (
            ("TransitionLength", 0.0), ("CurveRadius", 3000.0),
            ("TotalTurnAngle", 90.0), ("MainTemplateWidth", 32.0),
            ("TemplateThickness", 2.0),
        ):
            _property(self.settings, "Float", name, value)
        self.hosts = []
        routes = []
        for name, offset in (("HostA", 0.0), ("HostB", 50.0)):
            config = self.module.default_straight_config(len(routes))
            config.update(manager_id="ROUTE-" + name, name=name,
                          length=5000.0, start_y=offset,
                          template_width=32.0, template_thickness=2.0)
            routes.append(config)
            host = self.doc.addObject("Part::Feature", name)
            host.Shape = Part.makePolygon([
                self.app.Vector(0, offset, 0),
                self.app.Vector(5000, offset, 0),
            ])
            for field, value in (
                ("GeneratedBy", self.module.GENERATOR_ID),
                ("GeneratedRole", "StraightTrackCentreline"),
                ("ExportSubtype", "TrackCentreline"),
                ("TemplateSetID", "SET-001"),
                ("RouteID", config["manager_id"]),
                ("RouteName", name), ("TrackName", name),
            ):
                _property(host, "String", field, value)
            _property(host, "Integer", "TrackNumber", 1)
            self.hosts.append(host)
        _property(self.settings, "String", self.module.STRAIGHT_CONFIGS_PROPERTY,
                  json.dumps(routes, sort_keys=True, allow_nan=False))
        self.doc.recompute()
        self.workflow = self._workflow()

    def _cleanup(self):
        for name in self.owned_names:
            if name in self.app.listDocuments():
                self.app.closeDocument(name)
        self.assertEqual(self.app.listDocuments(), {})
        if self.success:
            # Only this exact test-owned file; unknown/failure data is retained.
            if self.saved.exists():
                self.saved.unlink()
            self.folder.rmdir()

    def _intent(self, crossover=False):
        from tracktemplate.application.rea_turnout_state import ReaTrackworkIntent
        from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification

        return ReaTrackworkIntent(
            entity_id="REA-XO-1" if crossover else "REA-TO-1",
            entity_kind="crossover" if crossover else "turnout",
            template_set_id="SET-001",
            host_names=("HostA", "HostB") if crossover else ("HostA",),
            source_specification=ReaTurnoutSpecification("B", 8.0),
            reference_chainage_mm=1500.0,
            handing=(self.module.CROSSOVER_HAND_AUTO if crossover
                     else self.module.TURNOUT_HAND_LEFT),
            orientation=(None if crossover
                         else self.module.TURNOUT_ORIENTATION_FACING),
            arrangement=(self.module.CROSSOVER_ARRANGEMENT_FACING
                         if crossover else None),
            minimum_radius_mm=600.0 if crossover else None,
        )

    def _read(self, obj, expected):
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            read_rea_trackwork_object,
        )
        from tracktemplate.application.rea_turnout_state import (
            REA_HOSTS_PROPERTY,
            REA_INTENT_JSON_PROPERTY,
            rea_trackwork_intent_to_json,
        )
        self.assertEqual(read_rea_trackwork_object(obj), expected)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY),
                         rea_trackwork_intent_to_json(expected))
        self.assertEqual(tuple(host.Name for host in getattr(
            obj, REA_HOSTS_PROPERTY,
        )), expected.host_names)
        self.assertNotIn("TurnoutID", obj.PropertiesList)
        self.assertNotIn("CrossoverID", obj.PropertiesList)
        self.assertNotIn("Shape", obj.PropertiesList)
        self.assertIsNone(obj.ViewObject)
        self.count("canonical_reads")

    def _source_road(self, road, expected, offset):
        from validate_phase1_turnout import _close

        dimensions = {key: float(value)
                      for key, value in expected["dimensions"].items()}
        for key, value in dimensions.items():
            _close(road["dimensions"][key], value)
            self.count("source_scalars")
        self.assertEqual(len(road["timbers"]), len(expected["timbers"]))
        for actual, wanted in zip(road["timbers"], expected["timbers"]):
            for key in ("identifier", "section", "crossing_suffix"):
                self.assertEqual(actual[key], wanted[key])
            _close(actual["x"], wanted["x"])
            _close(actual["width"], wanted["width"])
            self.assertEqual(actual["angle_radians"], 0.0)
            self.count("timber_records")
        rails = {rail["name"]: rail for rail in road["rails"]}
        self.assertEqual(len(rails), 30)
        anchors = (
            ("turnout-side wing flare gauge face", "wing_flare_turnout_x",
             "wing_end_turnout_x"),
            ("turnout-side wing flare outer face", "wing_flare_turnout_outer_x",
             "wing_end_turnout_outer_x"),
            ("main-side wing flare gauge face", "wing_flare_main_x",
             "wing_end_main_x"),
            ("main-side wing flare outer face", "wing_flare_main_outer_x",
             "wing_end_main_outer_x"),
            ("main-side check rail gauge face", "check_main_start_x",
             "check_main_end_x"),
            ("main-side check rail outer face", "check_main_outer_start_x",
             "check_main_outer_end_x"),
            ("turnout-side check rail gauge face", "check_turnout_start_x",
             "check_turnout_end_x"),
        )
        for name, start, finish in anchors:
            for index, key in ((0, start), (-1, finish)):
                _close(rails[name]["local_points"][index][0], dimensions[key])
                self.count("rail_anchors")
        direction = (1 if road["orientation"]
                     == self.module.TURNOUT_ORIENTATION_FACING else -1)
        hand = 1 if road["handing"] == self.module.TURNOUT_HAND_LEFT else -1
        for record in road["rails"] + road["timbers"]:
            self.assertEqual(len(record["local_points"]), len(record["points"]))
            for local, world in zip(record["local_points"], record["points"]):
                # These fixtures have analytically straight +X hosts.
                _close(world.x, road["toe_chainage"] + direction * local[0])
                _close(world.y, offset + direction * hand * local[1])
                _close(world.z, 0.0)
                self.count("mapped_points")

    def _prepared(self, intent, existing=None):
        spec = intent.source_specification
        expected = next(row for row in self.fixture["cases"]
                        if row["switch"] == spec.switch_size
                        and float(row["crossing_ratio"]) == spec.crossing_ratio)
        if intent.entity_kind == "turnout":
            geometry = self.session.prepare_rea_turnout_geometry(
                self.doc, self.hosts[0], intent.reference_chainage_mm,
                intent.handing, intent.orientation, spec,
            )
            roads = (("to", geometry, 0.0),)
        else:
            geometry = self.session.prepare_rea_crossover_geometry(
                self.doc, *self.hosts, intent.reference_chainage_mm, spec,
                arrangement=intent.arrangement, handing=intent.handing,
                minimum_radius=intent.minimum_radius_mm,
            )
            roads = (("a", geometry["turnout_a"], 0.0),
                     ("b", geometry["turnout_b"], 50.0))
            self.assertTrue(geometry["radius_assessment"]["accepted"])
        prepared = self.workflow.prepare(self.doc, intent, existing=existing)
        lines = {line.visual_id: line for line in prepared.scene.lines}
        self.assertEqual(len(lines), len(prepared.scene.lines))
        for side, road, offset in roads:
            self._source_road(road, expected, offset)
            for category, records, key in (("rail", road["rails"], "name"),
                                           ("timber", road["timbers"],
                                            "identifier")):
                for record in records:
                    identity = ":".join((intent.entity_id, side, category,
                                         record[key]))
                    self.assertEqual(lines[identity].points, tuple(
                        (point.x, point.y, point.z) for point in record["points"]
                    ))
        connectors = [name for name in lines if ":connector:" in name]
        self.assertEqual(len(connectors), 4 if intent.entity_kind == "crossover"
                         else 0)
        self.assertEqual(len(lines), len(roads) * (30 + len(expected["timbers"]))
                         + len(connectors))
        self.count("scene_lines", len(lines))
        return prepared

    def _save_reopen(self, obj, intent, scene):
        name, label = obj.Name, obj.Label
        self.doc.saveAs(str(self.saved))
        self.assertTrue(self.saved.is_file())
        self.assertGreater(self.saved.stat().st_size, 0)
        self.app.closeDocument(self.doc.Name)
        self.assertEqual(self.app.listDocuments(), {})
        self.doc = self.app.openDocument(str(self.saved))
        self.owned_names.add(self.doc.Name)
        self.doc.UndoMode = 1
        self.settings = self.doc.getObject("Settings")
        self.hosts = [self.doc.getObject("HostA"), self.doc.getObject("HostB")]
        self.workflow = self._workflow()
        restored = self.doc.getObject(name)
        self.assertEqual(restored.Label, label)
        self._read(restored, intent)
        history = _history(self.doc)
        self.workflow.rebuild(self.doc, restored)
        prepared = self.workflow.prepare(self.doc, intent, existing=restored)
        self.assertEqual(prepared.scene, scene)
        self.assertEqual(_history(self.doc), history)
        self.count("save_reopen")

    def _negative_controls(self, obj, initial, changed):
        import Part
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            ReaTrackworkDocumentError,
        )
        from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification

        baseline_names = tuple(sorted(item.Name for item in self.doc.Objects))
        history = _history(self.doc)
        for invalid in (
            replace(initial, entity_id="Other"),
            replace(initial, entity_id="Other", source_specification=(
                ReaTurnoutSpecification("B", 3.5)
            )),
        ):
            with self.assertRaises(ValueError):
                self.workflow.create(self.doc, invalid)
            self.assertEqual(tuple(sorted(item.Name for item in self.doc.Objects)),
                             baseline_names)
            self.assertEqual(_history(self.doc), history)
            self.count("negative_controls")
        prepared = self.workflow.prepare(self.doc, changed, existing=obj)
        original = self.settings.MainTemplateWidth
        self.settings.MainTemplateWidth = original + 1.0
        try:
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                self.workflow.commit(self.doc, prepared)
        finally:
            self.settings.MainTemplateWidth = original
        self._read(obj, initial)
        self.assertEqual(_history(self.doc), history)
        self.count("negative_controls")
        prepared = self.workflow.prepare(self.doc, changed, existing=obj)
        original_shape = self.hosts[0].Shape.copy()
        self.hosts[0].Shape = Part.makePolygon([
            self.app.Vector(0, 0, 0), self.app.Vector(5001, 0, 0),
        ])
        try:
            with self.assertRaisesRegex(ValueError, "inputs changed"):
                self.workflow.commit(self.doc, prepared)
        finally:
            self.hosts[0].Shape = original_shape
        self._read(obj, initial)
        self.assertEqual(_history(self.doc), history)
        self.count("negative_controls")
        prepared = self.workflow.prepare(self.doc, changed, existing=obj)
        other = replace(initial, entity_id="Other", reference_chainage_mm=3000.0)
        self._workflow().create(self.doc, other)
        occupied_history = _history(self.doc)
        with self.assertRaisesRegex(ValueError, "inputs changed"):
            self.workflow.commit(self.doc, prepared)
        self.assertEqual(_history(self.doc), occupied_history)
        self._read(obj, initial)
        self.doc.undo()
        self.assertEqual(tuple(sorted(item.Name for item in self.doc.Objects)),
                         baseline_names)
        self.count("negative_controls")
        history = _history(self.doc)
        with self.assertRaises(ValueError):
            self.module._build_curve_inheriting_c10_turnout(
                self.doc, self.hosts[0], 1500.0,
                self.module.TURNOUT_HAND_LEFT,
                self.module.TURNOUT_ORIENTATION_FACING, 16.5, 1.0,
            )
        self.assertEqual(_history(self.doc), history)
        self.assertEqual(tuple(sorted(item.Name for item in self.doc.Objects)),
                         baseline_names)
        self.count("negative_controls")

        def reject_after_write(candidate, scene, signature):
            self._read(candidate, changed)
            raise RuntimeError("REA native deliberate post-write failure")

        failing = self._workflow(view_factory=reject_after_write)
        with self.assertRaises(ReaTrackworkDocumentError) as caught:
            failing.update(self.doc, obj, changed)
        self.assertEqual(caught.exception.code, "transaction-failed")
        self.assertTrue(caught.exception.recoverable)
        self._read(obj, initial)
        self.assertEqual(_history(self.doc), history)
        self.assertEqual(tuple(sorted(item.Name for item in self.doc.Objects)),
                         baseline_names)
        self.count("negative_controls")

    def test_turnout_create_edit_return_and_reopen(self):
        from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification

        initial = self._intent()
        changed = replace(initial, source_specification=(
            ReaTurnoutSpecification("C", 9.25)
        ))
        first = self._prepared(initial)
        obj = self.workflow.commit(self.doc, first)
        self._read(obj, initial)
        name, label = obj.Name, obj.Label
        candidate = self._prepared(changed, existing=obj)
        self.assertNotEqual(candidate.scene, first.scene)
        self.workflow.commit(self.doc, candidate)
        self._read(obj, changed)
        self.doc.undo()
        self._read(obj, initial)
        self.doc.redo()
        self._read(obj, changed)
        self.count("undo_redo", 2)
        restored = self._prepared(initial, existing=obj)
        self.assertEqual(restored.scene, first.scene)
        self.assertEqual(restored.signature, first.signature)
        self.workflow.commit(self.doc, restored)
        self.assertEqual(obj.Name, name)
        self.assertEqual(obj.Label, label)
        self._read(obj, initial)
        history = _history(self.doc)
        self.assertIs(self.workflow.update(self.doc, obj, initial), obj)
        self.assertEqual(_history(self.doc), history)
        self.count("no_op")
        self._negative_controls(obj, initial, changed)
        self._save_reopen(obj, initial, first.scene)
        self.success = True

    def test_crossover_create_and_reopen(self):
        initial = self._intent(crossover=True)
        prepared = self._prepared(initial)
        obj = self.workflow.commit(self.doc, prepared)
        self._read(obj, initial)
        self.assertEqual(len(self.doc.Objects), 4)
        self._save_reopen(obj, initial, prepared.scene)
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
        if (result.wasSuccessful() and not result.skipped
                and count == self.expected and app is not None
                and not app.listDocuments()):
            payload = {
                "mode": self.mode, "status": "PASS", "tests": count,
                "failures": 0, "errors": 0, "skips": 0,
                "documents_created": state["documents_created"],
                "documents_remaining": 0,
                "input_sha256": state["input_sha256"],
                "checks": state["checks"],
                "elapsed_seconds": time.monotonic() - started,
            }
            print("TRACKTEMPLATE_REA_TRACKWORK=" + json.dumps(
                payload, sort_keys=True, allow_nan=False,
            ), flush=True)
        return result


def load_tests(loader, tests, pattern):
    """FreeCAD's native unittest discovery selects one approved stage."""
    mode = os.environ.get("TRACKTEMPLATE_REA_MODE")
    if mode not in ("readiness", "native"):
        raise ValueError("TRACKTEMPLATE_REA_MODE must be readiness or native.")
    selected = Readiness if mode == "readiness" else Native
    state = {"documents_created": 0, "checks": dict.fromkeys(CHECKS, 0)}
    selected.state = state
    cases = (loader.loadTestsFromTestCase(selected) if mode == "readiness" else
             (Native("test_turnout_create_edit_return_and_reopen"),
              Native("test_crossover_create_and_reopen")))
    suite = _ReportedSuite(cases)
    suite.state, suite.mode = state, mode
    suite.expected = 1 if mode == "readiness" else 2
    if suite.countTestCases() != suite.expected:
        raise RuntimeError("The approved native test count changed.")
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
