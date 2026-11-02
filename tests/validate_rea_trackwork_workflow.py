#!/usr/bin/env python3
"""Exercise source TO/XO commands with real analytical host calculations."""

from dataclasses import replace
import ast
import importlib
import json
import math
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from validate_phase9b_rea_bc_consumers import host, railway_module
from validate_rea_trackwork_document import FakeDocument, FakeView
from tracktemplate.adapters.freecad.rea_turnout_state import (
    FreeCADReaTrackworkStore,
)
from tracktemplate.application.rea_turnout_state import ReaTrackworkIntent
from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification
from tracktemplate.presentation.rea_trackwork import (
    ReaTrackworkLine,
    ReaTrackworkScene,
)


SENTINEL = "REA shared source workflow checks passed"


def scene_factory(entity_id, lines):
    return ReaTrackworkScene(entity_id, tuple(
        ReaTrackworkLine(*line) for line in lines
    ))


def complete_railway_module():
    """Add unchanged connector helpers to the existing bounded fixture."""
    module = railway_module()
    contract = json.loads((ROOT / (
        "reference/contracts/phase1-transition-pilot.json"
    )).read_text())
    path = ROOT / contract["source_state"]["b15"]["path"]
    tree = ast.parse(path.read_text())
    functions = {node.name: node for node in tree.body
                 if isinstance(node, ast.FunctionDef)}
    selected = set()
    pending = ["_crossover_offset_polyline"]
    while pending:
        name = pending.pop()
        if name in selected or name in module.__dict__ or name not in functions:
            continue
        selected.add(name)
        pending.extend(node.id for node in ast.walk(functions[name])
                       if isinstance(node, ast.Name))
    exec(compile(ast.Module(body=[node for node in tree.body
                                  if isinstance(node, ast.FunctionDef)
                                  and node.name in selected], type_ignores=[]),
                 str(path), "exec"), module.__dict__)
    return module


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = importlib.import_module(
            "tracktemplate.compatibility.rea_trackwork"
        )

    def setUp(self):
        self.module = complete_railway_module()
        self.doc = FakeDocument()
        self.doc.turnouts = []
        self.doc.crossovers = []
        self.doc.getObject = lambda name: next(
            (obj for obj in self.doc.Objects if obj.Name == name), None,
        )
        self.hosts = []
        for name, offset in (("HostA", 0.0), ("HostB", 50.0)):
            obj = host(self.module, offset=offset, name=name)
            obj.Document = self.doc
            obj.GeneratedBy = self.module.GENERATOR_ID
            obj.GeneratedRole = "Centreline"
            obj.ExportSubtype = "TrackCentreline"
            obj.TrackNumber = len(self.hosts) + 1
            obj.RouteID = ""
            obj.TrackName = name
            obj.RouteName = ""
            obj.PropertiesList = list(vars(obj))
            self.doc.Objects.append(obj)
            self.hosts.append(obj)
        self.settings = self.doc.addObject("App::FeaturePython", "Settings")
        self.settings.TemplateSetID = "SET-001"
        self.settings.GeneratedRole = "Settings"
        self.settings.TransitionLength = 0.0
        self.settings.CurveRadius = 3000.0
        self.settings.TotalTurnAngle = 90.0
        self.settings.MainTemplateWidth = 32.0
        self.settings.TemplateThickness = 2.0
        self.settings.TrackConfigurationJSON = '[{"width":32.0}]'
        setattr(self.settings, self.module.STRAIGHT_CONFIGS_PROPERTY, "[]")
        self.module.settings_for_template_set = lambda doc, sid: self.settings
        self.module.is_generated_settings = lambda obj: obj is self.settings
        self.module.quantity_value = lambda obj, name, default: getattr(
            obj, name, default,
        )
        self.module._integer_object_property = lambda obj, name, default: (
            getattr(obj, name, default)
        )
        self.previous_app = sys.modules.get("FreeCAD")
        sys.modules["FreeCAD"] = types.SimpleNamespace(
            getDocument=lambda name: self.doc if name == self.doc.Name else None,
            Version=lambda: (1, 1, 4), GuiUp=False,
        )
        self.store = FreeCADReaTrackworkStore({
            "compatibility_evaluation": {
                "status": "qualified", "matched_profile_id": "test-fake",
            },
            "runtime": {"freecad": {
                "available": True, "version_info": [1, 1, 4],
            }},
        }, view_factory=FakeView)
        self.workflow = self.subject.ReaTrackworkWorkflow(
            self.module, self.store, scene_factory,
        )

    def tearDown(self):
        if self.previous_app is None:
            sys.modules.pop("FreeCAD", None)
        else:
            sys.modules["FreeCAD"] = self.previous_app

    def intent(self, **changes):
        values = dict(
            entity_id="Research-TO-1", entity_kind="turnout",
            template_set_id="SET-001", host_names=("HostA",),
            source_specification=ReaTurnoutSpecification("B", 8.0),
            reference_chainage_mm=1500.0, handing="Left-hand",
            orientation=self.module.TURNOUT_ORIENTATION_FACING,
        )
        values.update(changes)
        return ReaTrackworkIntent(**values)

    def legacy_turnout(self, *, identifier="TO-001", host_name="HostA",
                       toe=500.0, orientation=None, handing="Left-hand"):
        module = self.module
        if orientation is None:
            orientation = module.TURNOUT_ORIENTATION_FACING
        dimensions = module.rea_c10_dimensions(16.5, 1.0)
        host_obj = self.doc.getObject(host_name)
        return {
            "schema_version": module.TURNOUT_SCHEMA_VERSION,
            "turnout_id": identifier, "size": module.TURNOUT_SIZE_C10,
            "source": module.TURNOUT_SOURCE_NOTE,
            "host_object": host_name, "template_set_id": "SET-001",
            "route_id": "", "track_number": host_obj.TrackNumber,
            "toe_chainage": toe, "orientation": orientation,
            "handing": handing, "track_gauge": 16.5, "flangeway": 1.0,
            "host_station_interval": list(module.turnout_host_station_interval(
                toe, dimensions, orientation,
            )),
        }

    def install_legacy(self, config, kind="turnout"):
        obj = self.doc.addObject("App::FeaturePython", "Old" + kind)
        obj.GeneratedBy = self.module.GENERATOR_ID
        obj.GeneratedRole = getattr(self.module, kind.upper() + "_SETTINGS_ROLE")
        obj.TemplateSetID = config["template_set_id"]
        setattr(obj, getattr(self.module, kind.upper() + "_CONFIGURATION_PROPERTY"),
                json.dumps(config))
        getattr(self.doc, kind + "s").append(config)
        return obj

    def legacy_crossover(self, minimum_radius=600.0):
        module = self.module
        dimensions = module.rea_c10_dimensions(16.5, 1.0)
        data_a, data_b = (obj.alignment for obj in self.hosts)
        orientation_a = module.TURNOUT_ORIENTATION_FACING
        orientation_b, _, _ = module._crossover_orientation_b(
            data_a, data_b, 500.0, orientation_a,
        )
        handing = module._crossover_automatic_hand(
            data_a, data_b, 500.0, orientation_a,
        )
        solved = module._crossover_solve_toe_b(
            data_a, data_b, 500.0, orientation_a, orientation_b, handing,
            dimensions, minimum_radius,
        )
        config = {
            "schema_version": module.CROSSOVER_SCHEMA_VERSION,
            "crossover_id": "XO-001", "size": module.TURNOUT_SIZE_C10,
            "source": module.CROSSOVER_SOURCE_NOTE,
            "template_set_id": "SET-001", "host_a_object": "HostA",
            "host_b_object": "HostB", "reference_chainage": 500.0,
            "arrangement": module.CROSSOVER_ARRANGEMENT_FACING,
            "handing": handing, "minimum_requested_radius": minimum_radius,
            "track_gauge": 16.5, "flangeway": 1.0,
        }
        for side, host_name, toe, orientation in (
            ("a", "HostA", 500.0, orientation_a),
            ("b", "HostB", solved["toe_b"], orientation_b),
        ):
            child = self.legacy_turnout(
                identifier="XO-001-" + side.upper(), host_name=host_name,
                toe=toe, orientation=orientation, handing=handing,
            )
            config.update({
                "turnout_" + side + "_id": child["turnout_id"],
                "turnout_" + side + "_config": child,
                "toe_chainage_" + side: toe,
                "orientation_" + side: orientation,
                "host_" + side + "_station_interval": (
                    child["host_station_interval"]
                ),
            })
        return config

    def assert_legacy_refused_before_calculation(self, config, kind="turnout"):
        self.install_legacy(config, kind)
        self.workflow._calculate = lambda *_args: self.fail(
            "Invalid legacy record reached the source geometry calculation",
        )
        with self.assertRaises(ValueError):
            self.workflow.create(self.doc, self.intent())
        self.assertEqual(self.doc.commits, 0)

    def test_unknown_legacy_context_is_rejected_before_calculation(self):
        for changes in (
            {"orientation": "Unrecognised"}, {"schema_version": 999},
            {"size": "B8"}, {"source": "unqualified"},
            {"source_specification": {"switch_size": "B"}},
            {"handing": "unknown"}, {"template_set_id": "Another"},
            {"track_number": 2}, {"route_id": "another"},
            {"host_station_interval": [0.0, 1.0]},
        ):
            with self.subTest(changes=changes):
                config = self.legacy_turnout()
                config.update(changes)
                try:
                    self.assert_legacy_refused_before_calculation(config)
                finally:
                    self.doc.Objects.pop()
                    self.doc.turnouts.clear()

    def test_valid_legacy_background_is_preserved(self):
        config = self.legacy_turnout()
        self.install_legacy(config)
        self.workflow.create(self.doc, self.intent())
        self.assertEqual(self.doc.turnouts, [config])
        self.assertEqual(self.doc.commits, 1)

    def test_legacy_crossover_context_and_cached_intervals_are_checked(self):
        original = self.legacy_crossover()
        for location, changes in (
            (None, {"schema_version": 999}),
            (None, {"host_b_station_interval": [0.0, 1.0]}),
            (None, {"turnout_b_id": "Other"}),
            (None, {"toe_chainage_b": original["toe_chainage_b"] + 1.0}),
            (None, {"handing": "Right-hand"}),
            (None, {"minimum_requested_radius": -1.0}),
            (None, {"minimum_requested_radius": 0.0}),
            (None, {"minimum_requested_radius": 1.0}),
            (None, {"minimum_requested_radius": 49.0}),
            ("turnout_a_config", {"track_gauge": 18.0}),
            ("turnout_b_config", {"source": "Other"}),
            ("turnout_b_config", {"template_set_id": "Other"}),
        ):
            with self.subTest(location=location, changes=changes):
                config = json.loads(json.dumps(original))
                target = config if location is None else config[location]
                target.update(changes)
                try:
                    self.assert_legacy_refused_before_calculation(
                        config, "crossover",
                    )
                finally:
                    self.doc.Objects.pop()
                    self.doc.crossovers.clear()

    def test_valid_legacy_crossover_keeps_original_lower_solution(self):
        config = self.legacy_crossover()
        self.install_legacy(config, "crossover")
        original = json.dumps(config, sort_keys=True)
        obj = self.workflow.create(self.doc, self.intent(
            reference_chainage_mm=3000.0,
        ))
        self.assertIsNotNone(obj)
        self.assertEqual(json.dumps(self.doc.crossovers[0], sort_keys=True),
                         original)
        self.assertEqual(self.doc.commits, 1)

    def test_legacy_crossover_preflight_precedes_lower_solver(self):
        original = self.legacy_crossover()
        lower = self.module._crossover_solve_toe_b
        direction = self.module._crossover_orientation_b
        nearest = self.module._crossover_nearest_point_on_alignment
        for case in ("reference", "separation", "direction"):
            with self.subTest(case=case):
                config = json.loads(json.dumps(original))
                if case == "reference":
                    config["reference_chainage"] = -100.0
                elif case == "separation":
                    self.module._crossover_nearest_point_on_alignment = (
                        lambda *args: (*nearest(*args)[:3], 501.0)
                    )
                else:
                    self.module._crossover_orientation_b = lambda *args: (
                        *direction(*args)[:2], math.cos(math.radians(35.0)),
                    )
                self.module._crossover_solve_toe_b = lambda *args: self.fail(
                    "Invalid legacy input reached the lower solver",
                )
                try:
                    with self.assertRaises(ValueError):
                        self.workflow._legacy_intervals(
                            self.doc, "crossover", config,
                        )
                finally:
                    self.module._crossover_solve_toe_b = lower
                    self.module._crossover_orientation_b = direction
                    self.module._crossover_nearest_point_on_alignment = nearest
        self.assertEqual(self.doc.commits, 0)

    def test_legacy_complete_radius_includes_both_turnout_roads(self):
        config = self.legacy_crossover(minimum_radius=4000.0)
        self.assert_legacy_refused_before_calculation(config, "crossover")

    def test_create_edit_change_back_reuses_real_source_geometry(self):
        initial = self.intent()
        obj = self.workflow.create(self.doc, initial)
        view = self.store.view_for(obj)
        first = view.scene
        first_signature = view.signature
        self.assertEqual(len(first.lines), 30 + 32)
        self.assertEqual(first.entity_id, initial.entity_id)
        changed = replace(initial, source_specification=(
            ReaTurnoutSpecification("C", 9.25)
        ))
        self.workflow.update(self.doc, obj, changed)
        self.assertNotEqual(first, view.scene)
        self.assertNotEqual(first_signature, view.signature)
        self.workflow.update(self.doc, obj, initial)
        self.assertEqual(first, view.scene)
        self.assertEqual(first_signature, view.signature)
        self.assertEqual(self.doc.commits, 3)
        self.workflow.update(self.doc, obj, initial)
        self.assertEqual(self.doc.commits, 3)
        self.assertFalse(hasattr(obj, "TurnoutID"))
        self.assertFalse(hasattr(obj, "CrossoverID"))

    def test_source_crossover_has_two_roads_and_four_connector_faces(self):
        initial = self.intent(
            entity_id="Research-XO-1", entity_kind="crossover",
            host_names=("HostA", "HostB"), orientation=None,
            arrangement=self.module.CROSSOVER_ARRANGEMENT_FACING,
            handing=self.module.CROSSOVER_HAND_AUTO, minimum_radius_mm=600.0,
        )
        obj = self.workflow.create(self.doc, initial)
        scene = self.store.view_for(obj).scene
        identifiers = [line.visual_id for line in scene.lines]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(sum("connector:" in value for value in identifiers), 4)
        self.assertTrue(any(":a:" in value for value in identifiers))
        self.assertTrue(any(":b:" in value for value in identifiers))
        self.assertEqual(len(self.doc.Objects), 4)

    def test_every_host_state_change_invalidates_before_commit(self):
        initial = self.intent()
        for field, replacement in (
            ("CurveRadius", 3100.0), ("MainTemplateWidth", 33.0),
            ("TrackConfigurationJSON", '[{"width":34}]'),
        ):
            original = getattr(self.settings, field)
            prepared = self.workflow.prepare(self.doc, initial)
            setattr(self.settings, field, replacement)
            with self.assertRaises(ValueError):
                self.workflow.commit(self.doc, prepared)
            setattr(self.settings, field, original)
        prepared = self.workflow.prepare(self.doc, initial)
        self.hosts[0].alignment["points"][3].y += 0.1
        with self.assertRaises(ValueError):
            self.workflow.commit(self.doc, prepared)
        self.assertEqual(self.doc.commits, 0)

    def test_occupied_source_interval_refuses_without_mutation(self):
        self.workflow.create(self.doc, self.intent())
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.workflow.create(self.doc, self.intent(entity_id="Research-TO-2"))
        self.assertEqual(self.doc.commits, 1)
        obj = self.workflow.create(self.doc, self.intent(
            entity_id="Research-TO-2", reference_chainage_mm=3000.0,
        ))
        self.assertIsNotNone(obj)

    def test_legacy_occupancy_and_malformed_settings_never_disappear(self):
        config = self.legacy_turnout(toe=1500.0)
        settings = self.install_legacy(config)
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.workflow.create(self.doc, self.intent())
        setattr(settings, self.module.TURNOUT_CONFIGURATION_PROPERTY, "{")
        self.doc.turnouts.clear()
        with self.assertRaises(ValueError):
            self.workflow.create(self.doc, self.intent())
        self.assertEqual(self.doc.commits, 0)

    def test_bad_hosts_and_unsupported_source_leave_document_intact(self):
        for initial in (
            self.intent(host_names=("Absent",)),
            self.intent(template_set_id="Other"),
            self.intent(source_specification=ReaTurnoutSpecification("B", 3.5)),
        ):
            with self.assertRaises(ValueError):
                self.workflow.create(self.doc, initial)
        self.assertEqual(self.doc.commits, 0)

    def test_preparation_is_private_and_tampering_is_rejected(self):
        prepared = self.workflow.prepare(self.doc, self.intent())
        with self.assertRaises((AttributeError, TypeError)):
            prepared.signature = "sha256:" + "0" * 64
        self.assertEqual(self.doc.commits, 0)
        other_workflow = self.subject.ReaTrackworkWorkflow(
            self.module, self.store, scene_factory,
        )
        with self.assertRaises(ValueError):
            other_workflow.commit(self.doc, prepared)
        with self.assertRaises(ValueError):
            self.workflow.commit(self.doc, replace(prepared, signature=(
                "sha256:" + "0" * 64
            )))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(WorkflowTests),
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(not result.wasSuccessful())
