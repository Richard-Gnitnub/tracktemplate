#!/usr/bin/env python3
"""Exercise source line routing through unchanged inherited consumers."""

import ast
from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host, rea_turnout_rails, transition_workflow,
)
from tracktemplate.compatibility.rea_turnout import (  # noqa: E402
    ReaTurnoutGeometryAdapter,
)
from tracktemplate.domain import rea_turnout, turnout  # noqa: E402
from validate_phase1_turnout import _close  # noqa: E402
from validate_phase7_concentric_core import _fixture  # noqa: E402
import validate_phase9b_rea_bc_consumers as consumers  # noqa: E402
from validate_rea_straight_closure import HEEL_N, expected_inner  # noqa: E402


CALLERS = ("_rea_c10_local_point", "_rea_c10_offset_from_inner",
           "_rea_c10_turnout_outer_gauge_point_at_x")
INNER = "_rea_c10_inner_gauge_face"


def actual_functions(module, names):
    contract = json.loads((ROOT / (
        "reference/contracts/phase1-transition-pilot.json"
    )).read_text())
    path = ROOT / contract["source_state"]["b15"]["path"]
    tree = ast.parse(path.read_text())
    selected = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"),
         module.__dict__)


def railway_module(bind=True):
    module = consumers.railway_module()
    names = {name for name, value in vars(module).items()
             if isinstance(value, types.FunctionType)
             and value.__code__.co_filename.endswith(".FCMacro")}
    actual_functions(module, names)
    if bind:
        module._rea_c10_inner_gauge_face = (
            rea_turnout_rails._ReaInnerGaugeAdapter(
                module._rea_c10_inner_gauge_face,
            )
        )
    return module


class StraightConsumerTests(unittest.TestCase):
    def setUp(self):
        self.spec = rea_turnout.ReaTurnoutSpecification("B", HEEL_N)
        self.dims = rea_turnout.rea_turnout_dimensions(self.spec)

    def test_facade_only_replacement_cannot_reach_nested_consumers(self):
        module = railway_module(False)
        original = module._rea_c10_inner_gauge_face
        facade = types.SimpleNamespace(**vars(module))
        setattr(facade, INNER, lambda d, x: expected_inner(x))
        expected = expected_inner(150)[1] - 8.25
        self.assertGreater(abs(facade._rea_c10_local_point(
            self.dims, 150, "turnout_inner",
        )[1] - expected), 1.0)
        self.assertIs(module._rea_c10_local_point.__globals__[INNER], original)
        bound = railway_module()
        host = consumers.host(module)
        # The broken facade also leaves actual timber, mapped centreline
        # and XO topology consumers resolving the unchanged circle helper.
        self.assertNotEqual(
            facade._turnout_timber_end_data(self.dims, 150, 32),
            bound._turnout_timber_end_data(self.dims, 150, 32),
        )
        arguments = (host.alignment, 2000, module.TURNOUT_ORIENTATION_FACING,
                     module.TURNOUT_HAND_LEFT, self.dims)
        self.assertNotEqual(facade.turnout_mapping_metrics(*arguments),
                            bound.turnout_mapping_metrics(*arguments))
        self.assertNotEqual(facade._crossover_switch_region_points(*arguments),
                            bound._crossover_switch_region_points(*arguments))
        self.assertNotEqual(
            facade.rea_c10_complete_rail_polylines(self.dims),
            bound.rea_c10_complete_rail_polylines(self.dims),
        )
        with self.assertRaisesRegex(ValueError, "binding"):
            ReaTurnoutGeometryAdapter(facade).turnout(
                types.SimpleNamespace(turnouts=[], crossovers=[]),
                consumers.host(module), 2000, module.TURNOUT_HAND_LEFT,
                module.TURNOUT_ORIENTATION_FACING, self.spec,
            )
        with self.assertRaisesRegex(ValueError, "binding"):
            ReaTurnoutGeometryAdapter(facade).crossover(
                types.SimpleNamespace(turnouts=[], crossovers=[]),
                consumers.host(module),
                consumers.host(module, offset=50, name="HostB"),
                2000, self.spec,
            )

    def test_actual_running_faces_and_timber_inversion(self):
        module = railway_module()
        rails = dict(rea_turnout_rails.rea_turnout_rail_polylines(
            module, self.dims,
        ))
        faces = {
            "turnout-side stock rail gauge face": 16.5,
            "turnout-side stock rail outer face": 16.5 + 11 / 12,
            "curved switch and closure rail gauge face": 0.0,
            "curved switch and closure rail outer face": -11 / 12,
        }
        k = math.atan(1 / HEEL_N)
        for name, offset in faces.items():
            sampled = 0
            for x, y in rails[name]:
                u = x + offset * math.sin(k)
                if u > self.dims["heel_lead"] + 1e-8:
                    _close(y, expected_inner(x)[1]
                           + offset / math.cos(k) - 8.25)
                    sampled += 1
            self.assertGreater(sampled, 100, name)
        for x in (100, 150, 250, self.dims["fine_point_x"]):
            actual = module._rea_c10_turnout_outer_gauge_point_at_x(
                self.dims, x,
            )
            _close(actual[0], x)
            _close(actual[1], expected_inner(x)[1] + 16.5 / math.cos(k) - 8.25)
            ends = module._turnout_timber_end_data(self.dims, x, 32.0)
            self.assertGreater(ends["far_y"], actual[1])

    def test_preheel_delegation_and_each_segment_boundary(self):
        module = railway_module()
        adapter = module._rea_c10_inner_gauge_face
        for ratio in (HEEL_N - 1e-10, HEEL_N, HEEL_N + 1e-10):
            dims = rea_turnout.rea_turnout_dimensions(
                rea_turnout.ReaTurnoutSpecification("B", ratio),
            )
            for boundary in (0.0, dims["planing_x"], dims["heel_lead"],
                             dims["switch_curve_end_x"], dims["fine_point_x"]):
                for x in (math.nextafter(boundary, -math.inf), boundary,
                          math.nextafter(boundary, math.inf)):
                    point = adapter(dims, x)
                    if x <= dims["heel_lead"]:
                        self.assertEqual(point, adapter.original(dims, x))
                    else:
                        for actual, expected in zip(point,
                                                    expected_inner(x, ratio)):
                            _close(actual, expected)
                    # Each rail retains normal parameterisation, including
                    # its distinct actual-x endpoint at the heel/entry join.
                    for offset in (0.0, -11 / 12, 16.5, 16.5 + 11 / 12):
                        actual = module._rea_c10_offset_from_inner(
                            dims, x, offset,
                        )
                        _close(actual[0], point[0] - offset * math.sin(point[2]))
                        _close(actual[1], point[1] + offset * math.cos(point[2])
                               - 8.25)

    def test_complete_to_mapping_hands_directions_and_exit_bodies(self):
        module = railway_module()
        adapter = ReaTurnoutGeometryAdapter(module)
        doc = types.SimpleNamespace(turnouts=[], crossovers=[])
        profile = rea_turnout.ReaExitSleeperProfile(
            "templot-556b-00-D0GAF-32mm-full-exit",
        )
        for curvature in (0.0, 1 / 3000, -1 / 3000):
            host = consumers.host(module, curvature)
            for hand, sign in ((module.TURNOUT_HAND_LEFT, 1),
                               (module.TURNOUT_HAND_RIGHT, -1)):
                for orientation, direction in (
                    (module.TURNOUT_ORIENTATION_FACING, 1),
                    (module.TURNOUT_ORIENTATION_TRAILING, -1),
                ):
                    result = adapter.turnout(
                        doc, host, 2000, hand, orientation, self.spec,
                        exit_sleeper_profile=profile,
                    )
                    self.assertEqual(len(result["rails"]), 30)
                    mapping = result["mapping"]
                    for field in ("host_minimum_radius",
                                  "turnout_minimum_radius"):
                        if curvature == 0.0:
                            self.assertIsNone(mapping[field])
                        else:
                            self.assertTrue(math.isfinite(mapping[field]))
                            self.assertGreater(mapping[field], 0.0)
                    self.assertEqual([r["identifier"] for r in
                                      result["timbers"][-2:]], ["E1", "E2"])
                    for item in (*result["rails"], *result["timbers"]):
                        for local, actual in zip(item["local_points"],
                                                 item["points"]):
                            anchor, angle = module.interpolate_alignment_station(
                                host.alignment, 2000 + direction * local[0],
                            )
                            angle += math.pi if direction < 0 else 0
                            _close(actual.x, anchor.x
                                   - sign * local[1] * math.sin(angle))
                            _close(actual.y, anchor.y
                                   + sign * local[1] * math.cos(angle))
                    points = module._crossover_switch_region_points(
                        host.alignment, 2000, orientation, hand, self.dims,
                    )
                    start = self.dims["module_start_x"]
                    finish = self.dims["switch_curve_end_x"]
                    count = max(8, math.ceil((finish - start) / 5))
                    self.assertEqual(len(points), 2 * (count + 1))
                    for index in range(count + 1):
                        x = start + (finish - start) * index / count
                        inner = (expected_inner(x) if x > self.dims["heel_lead"]
                                 else module._rea_c10_inner_gauge_face.original(
                                     self.dims, x,
                                 ))
                        branch = (x - 8.25 * math.sin(inner[2]),
                                  inner[1] + 8.25 * math.cos(inner[2]) - 8.25)
                        for route, (local_x, local_y) in enumerate(
                            ((x, 0.0), branch),
                        ):
                            anchor, heading = module.interpolate_alignment_station(
                                host.alignment, 2000 + direction * local_x,
                            )
                            heading += math.pi if direction < 0 else 0
                            actual = points[2 * index + route]
                            _close(actual.x, anchor.x
                                   - sign * local_y * math.sin(heading))
                            _close(actual.y, anchor.y
                                   + sign * local_y * math.cos(heading))
        self.assertEqual(vars(doc), {"turnouts": [], "crossovers": []})

    def test_both_xo_legs_and_configured_minimum(self):
        module = railway_module()
        adapter = ReaTurnoutGeometryAdapter(module)
        doc = types.SimpleNamespace(turnouts=[], crossovers=[])
        for curvature in (0.0, 1 / 6000, -1 / 6000):
            a = consumers.host(module, curvature)
            b = consumers.host(module, curvature, offset=50, name="HostB")
            result = adapter.crossover(doc, a, b, 2000, self.spec)
            self.assertTrue(result["radius_assessment"]["accepted"])
            from tracktemplate.domain.crossover import complete_radius_decision
            assessment = result["radius_assessment"]
            radii = tuple(assessment[key] for key in (
                "turnout_a_minimum_radius_mm", "turnout_b_minimum_radius_mm",
                "connector_minimum_radius_mm",
            ))
            minimum = assessment["complete_minimum_radius_mm"]
            if minimum is None:
                self.assertTrue(complete_radius_decision(
                    *radii, 100000.0,
                )["accepted"])
            else:
                self.assertTrue(complete_radius_decision(
                    *radii, minimum,
                )["accepted"])
                self.assertFalse(complete_radius_decision(
                    *radii, math.nextafter(minimum, math.inf),
                )["accepted"])
            for leg in ("turnout_a", "turnout_b"):
                self.assertEqual(result[leg]["dimensions"]["source_closure_kind"],
                                 "line")
                self.assertEqual(len(result[leg]["rails"]), 30)
        with self.assertRaises(ValueError):
            adapter.crossover(doc, a, b, 2000, self.spec,
                              minimum_radius=100000.0)

    def test_canonical_changeback_and_fresh_store_reconstruction(self):
        import validate_rea_trackwork_workflow as lifecycle
        from tracktemplate.application import rea_turnout_state as state
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            read_rea_trackwork_object,
        )

        lifecycle.WorkflowTests.setUpClass()
        fixture = lifecycle.WorkflowTests()
        with patch.object(lifecycle, "complete_railway_module", railway_module):
            fixture.setUp()
        try:
            initial = fixture.intent()
            obj = fixture.workflow.create(fixture.doc, initial)
            view = fixture.store.view_for(obj)
            initial_scene = view.scene
            initial_bytes = getattr(obj, state.REA_INTENT_JSON_PROPERTY)
            selected = rea_turnout.ReaExitSleeperProfile(
                "templot-556b-00-D0GAF-32mm-full-exit",
            )
            for profile in (None, selected):
                straight = replace(initial, source_specification=self.spec,
                                   exit_sleeper_profile=profile)
                fixture.workflow.update(fixture.doc, obj, straight)
                canonical = getattr(obj, state.REA_INTENT_JSON_PROPERTY)
                self.assertEqual(json.loads(canonical)["schema_version"],
                                 1 if profile is None else 2)
                self.assertEqual(read_rea_trackwork_object(obj), straight)
                scene = view.scene
                self.assertNotEqual(scene, initial_scene)
                commits = fixture.doc.commits
                fixture.workflow.update(fixture.doc, obj, straight)
                self.assertEqual(fixture.doc.commits, commits)
                # Reconstruct only canonical object fields in a new fake
                # document/store. This is not an FCStd persistence claim.
                restored = lifecycle.WorkflowTests()
                with patch.object(lifecycle, "complete_railway_module",
                                  railway_module):
                    restored.setUp()
                try:
                    copied = restored.doc.addObject(obj.TypeId, obj.Name)
                    copied.Label = "Operator's straight turnout"
                    for name in obj.PropertiesList:
                        copied.addProperty(obj.getTypeIdOfProperty(name),
                                           name, "", "")
                        value = getattr(obj, name)
                        if name == state.REA_HOSTS_PROPERTY:
                            value = [restored.doc.getObject(host.Name)
                                     for host in value]
                        setattr(copied, name, value)
                    self.assertIsNone(restored.store.view_for(copied))
                    self.assertEqual(read_rea_trackwork_object(copied), straight)
                    restored.workflow.rebuild(restored.doc, copied)
                    self.assertEqual(restored.store.view_for(copied).scene,
                                     scene)
                    self.assertEqual(copied.Label, "Operator's straight turnout")
                    self.assertEqual(getattr(copied,
                                             state.REA_INTENT_JSON_PROPERTY),
                                     canonical)
                finally:
                    restored.tearDown()
                fixture.workflow.update(fixture.doc, obj, initial)
                self.assertEqual(view.scene, initial_scene)
                self.assertEqual(getattr(obj, state.REA_INTENT_JSON_PROPERTY),
                                 initial_bytes)
        finally:
            fixture.tearDown()


class StraightBindingTests(unittest.TestCase):
    def test_session_ownership_idempotence_legacy_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = _fixture(root)
            hosts = [b15_workflow_host.load_b15_workflow_host(root, contract)
                     for _ in range(3)]
            for host in hosts:
                actual_functions(host.module, (*CALLERS, INNER))
            self.assertIsNot(hosts[0].module.__dict__, hosts[1].module.__dict__)
            originals = [getattr(host.module, INNER) for host in hosts]
            functions = {name: getattr(api, name) for name in
                         transition_workflow.PRODUCT_FUNCTION_NAMES}
            session = transition_workflow.ModularTransitionWorkflowSession(
                hosts[0], functions,
            )
            adapter = getattr(session.module, INNER)
            self.assertIs(type(adapter), rea_turnout_rails._ReaInnerGaugeAdapter)
            self.assertIs(adapter.original, originals[0])
            session._bind_modular()
            self.assertIs(getattr(session.module, INNER), adapter)
            for dims in (turnout.rea_c10_dimensions(),
                         rea_turnout.rea_turnout_dimensions(
                             rea_turnout.ReaTurnoutSpecification("C", 9.25))):
                for x in (-10, 0, 20, 100, 150, 300):
                    self.assertEqual(adapter(dims, x), originals[0](dims, x))
            self.assertIs(getattr(hosts[1].module, INNER), originals[1])
            self.assertIs(getattr(hosts[2].module, INNER), originals[2])
            other = transition_workflow.ModularTransitionWorkflowSession(
                hosts[1], functions,
            )
            other_adapter = getattr(other.module, INNER)
            self.assertIsNot(other_adapter, adapter)
            self.assertIs(other_adapter.original, originals[1])
            straight = rea_turnout.rea_turnout_dimensions(
                rea_turnout.ReaTurnoutSpecification("B", HEEL_N),
            )
            for active in (session, other, session):
                bound = getattr(active.module, INNER)
                for value, expected in zip(bound(straight, 150),
                                           expected_inner(150)):
                    _close(value, expected)
                self.assertEqual(bound(turnout.rea_c10_dimensions(), 150),
                                 bound.original(turnout.rea_c10_dimensions(), 150))
                active._validate_binding()
            self.assertIs(getattr(hosts[2].module, INNER), originals[2])
            for name in CALLERS:
                with patch.object(session.module, name, None):
                    with self.assertRaises(
                        transition_workflow.TransitionWorkflowError,
                    ):
                        session._validate_binding()
            with patch.object(session.module, INNER, originals[1]):
                with self.assertRaises(
                    transition_workflow.TransitionWorkflowError,
                ):
                    session._bind_modular()
            with self.assertRaises(KeyError):
                adapter({}, 10)
            self.assertIs(getattr(hosts[1].module, INNER), other_adapter)
            with self.assertRaises(transition_workflow.TransitionWorkflowError):
                transition_workflow.ModularTransitionWorkflowSession(
                    hosts[0], functions,
                )
            with patch.object(session.module, CALLERS[0],
                              getattr(hosts[1].module, CALLERS[0])):
                before = dict(vars(session.module))
                with self.assertRaises(transition_workflow.TransitionWorkflowError):
                    session._bind_modular()
                self.assertEqual(vars(session.module), before)
            session._validate_binding()


if __name__ == "__main__":
    result = unittest.main(exit=False)
    if result.result.wasSuccessful() and not result.result.skipped:
        print("REA B straight closure consumers and session binding passed")
    raise SystemExit(not result.result.wasSuccessful()
                     or bool(result.result.skipped))
