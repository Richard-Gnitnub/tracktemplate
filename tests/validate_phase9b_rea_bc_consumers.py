#!/usr/bin/env python3
"""Exercise explicit B/C inputs through the retained railway consumers."""

import ast
import dataclasses
import hashlib
import json
import math
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SENTINEL = "Phase 9B source B/C geometry consumers passed"


def railway_module():
    """Load unchanged analytical helpers; replace only external host access."""
    contract = json.loads((ROOT / (
        "reference/contracts/phase1-transition-pilot.json"
    )).read_text())
    identity = contract["source_state"]["b15"]
    path = ROOT / identity["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == identity["sha256"]
    tree = ast.parse(path.read_text())
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    namespace = {"math": math}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    namespace[target.id] = value
    calculated = {
        "CROSSOVER_TANGENT_TOLERANCE", "CROSSOVER_CONNECTOR_MAX_SWEEP",
        "CROSSOVER_CONNECTOR_MAX_TOTAL_SWEEP", "CROSSOVER_TOPOLOGY_TANGENT_DOT",
    }
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id in calculated
                        for t in node.targets)) or (
                isinstance(node, ast.ClassDef)
                and node.name == "_CrossoverCandidateFailure"):
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         str(path), "exec"), namespace)
    required = {target.id for node in tree.body if isinstance(node, ast.Assign)
                for target in node.targets if isinstance(target, ast.Name)
                and target.id.startswith("CROSSOVER_")}
    assert required <= namespace.keys(), required - namespace.keys()
    selected = set()
    pending = [
        "rea_c10_complete_rail_polylines", "turnout_mapping_metrics",
        "_turnout_timber_end_data", "_turnout_timber_outline_local_points",
        "_crossover_solve_toe_b", "_crossover_orientation_b",
        "_crossover_automatic_hand", "turnout_valid_toe_range",
        "turnout_host_station_interval", "_turnout_find_overlap",
        "_crossover_find_existing_conflict",
    ]
    external = {
        "vector_xy", "interpolate_alignment_station",
        "existing_turnout_configs", "existing_crossover_configs",
    }
    while pending:
        name = pending.pop()
        if name in selected or name in external or name not in functions:
            continue
        selected.add(name)
        pending.extend(
            node.id for node in ast.walk(functions[name])
            if isinstance(node, ast.Name)
        )
    exec(compile(ast.Module(
        body=[node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name in selected], type_ignores=[],
    ), str(path), "exec"), namespace)

    def point(x, y, z=0.0):
        return types.SimpleNamespace(x=float(x), y=float(y), z=float(z))

    def at_station(data, station):
        # Independent circular host parameterisation, not product transforms.
        curvature = data["curvature"]
        heading = curvature * station
        if curvature:
            x = math.sin(heading) / curvature
            y = (1.0 - math.cos(heading)) / curvature
        else:
            x, y = station, 0.0
        return point(x, y + data["offset"]), heading

    namespace.update({
        "vector_xy": point,
        "interpolate_alignment_station": at_station,
        "is_turnout_host_centreline": lambda host: hasattr(host, "alignment"),
        "turnout_host_alignment": lambda host: host.alignment,
        "object_string_property": lambda obj, name, default="": getattr(
            obj, name, default,
        ),
        "turnout_host_template_dimensions": lambda doc, host: (32.0, 2.0),
        "existing_turnout_configs": lambda doc: doc.turnouts,
        "existing_crossover_configs": lambda doc: doc.crossovers,
    })
    module = types.ModuleType("rea_bc_consumer_fixture")
    module.__dict__.update(namespace)
    return module


def host(module, curvature=0.0, offset=0.0, name="HostA"):
    data = {"total": 5000.0, "curvature": curvature, "offset": offset}
    data["stations"] = [float(x) for x in range(0, 5001, 5)]
    samples = [module.interpolate_alignment_station(data, x)
               for x in data["stations"]]
    data["points"] = [sample[0] for sample in samples]
    data["headings"] = [sample[1] for sample in samples]
    return types.SimpleNamespace(
        Name=name, TemplateSetID="SET-001", alignment=data,
    )


class SourceConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tracktemplate.compatibility.rea_turnout import (
            ReaTurnoutGeometryAdapter,
        )
        from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification

        cls.adapter_type = ReaTurnoutGeometryAdapter
        cls.spec_type = ReaTurnoutSpecification
        cls.module = railway_module()

    def setUp(self):
        self.adapter = self.adapter_type(self.module)
        self.document = types.SimpleNamespace(turnouts=[], crossovers=[])

    def test_explicit_inputs_reach_real_rails_and_both_transforms(self):
        module = self.module
        seen = {}
        for size, ratio in (("B", 5.5), ("C", 9.25), ("C", 10.0)):
            spec = self.spec_type(size, ratio)
            for curvature in (0.0, 1 / 3000.0, -1 / 3000.0):
                source_host = host(module, curvature)
                for hand, sign in ((module.TURNOUT_HAND_LEFT, 1),
                                   (module.TURNOUT_HAND_RIGHT, -1)):
                    for orientation, direction in (
                        (module.TURNOUT_ORIENTATION_FACING, 1),
                        (module.TURNOUT_ORIENTATION_TRAILING, -1),
                    ):
                        result = self.adapter.turnout(
                            self.document, source_host, 2000.0, hand,
                            orientation, spec,
                        )
                        self.assertEqual(result["source_specification"],
                                         dataclasses.asdict(spec))
                        self.assertEqual(result["status"], "transient-only")
                        self.assertNotIn("config", result)
                        self.assertGreater(len(result["rails"]), 10)
                        fixture = json.loads((ROOT / (
                            "tests/fixtures/phase9b-rea-bc-source.json"
                        )).read_text())
                        expected = next(row for row in fixture["cases"]
                                        if row["switch"] == size and
                                        float(row["crossing_ratio"]) == ratio)
                        self.assertEqual(len(result["timbers"]),
                                         len(expected["timbers"]))
                        for actual, wanted in zip(result["timbers"],
                                                  expected["timbers"]):
                            self.assertEqual(actual["identifier"], wanted["identifier"])
                            self.assertEqual(actual["crossing_suffix"],
                                             wanted["crossing_suffix"])
                            self.assertAlmostEqual(actual["x"], float(wanted["x"]), 9)
                            self.assertAlmostEqual(actual["width"],
                                                   float(wanted["width"]), 12)
                            self.assertEqual(len(actual["local_points"]),
                                             len(actual["points"]))
                            for local, point in zip(actual["local_points"],
                                                    actual["points"]):
                                anchor, angle = module.interpolate_alignment_station(
                                    source_host.alignment, 2000.0 + direction * local[0],
                                )
                                angle += math.pi if direction == -1 else 0.0
                                self.assertAlmostEqual(point.x,
                                    anchor.x - sign * local[1] * math.sin(angle), 9)
                                self.assertAlmostEqual(point.y,
                                    anchor.y + sign * local[1] * math.cos(angle), 9)
                        self.assertTrue(any("R1/R2" in gap
                            for gap in result["qualification_gaps"]))
                        for rail in result["rails"]:
                            self.assertEqual(len(rail["local_points"]),
                                             len(rail["points"]))
                            for local, actual in zip(rail["local_points"],
                                                     rail["points"]):
                                station = 2000.0 + direction * local[0]
                                anchor, angle = module.interpolate_alignment_station(
                                    source_host.alignment, station,
                                )
                                angle += math.pi if direction == -1 else 0.0
                                self.assertAlmostEqual(actual.x, anchor.x
                                    - sign * local[1] * math.sin(angle), 9)
                                self.assertAlmostEqual(actual.y, anchor.y
                                    + sign * local[1] * math.cos(angle), 9)
                        seen[size, ratio] = result["dimensions"]
        self.assertNotEqual(seen["B", 5.5]["heel_lead"],
                            seen["C", 9.25]["heel_lead"])
        self.assertNotEqual(seen["C", 9.25]["fine_point_x"],
                            seen["C", 10.0]["fine_point_x"])
        self.assertEqual(vars(self.document), {"turnouts": [], "crossovers": []})

    def test_source_result_never_masquerades_as_committable_c10(self):
        with self.assertRaises((TypeError, ValueError)):
            self.adapter.turnout(self.document, host(self.module), 2000.0,
                self.module.TURNOUT_HAND_LEFT,
                self.module.TURNOUT_ORIENTATION_FACING, None)

    def test_crossover_uses_same_specification_and_complete_radius_rule(self):
        from tracktemplate.compatibility.crossover_preflight import (
            CrossoverPreflightAdapter,
        )

        source_a = host(self.module)
        source_b = host(self.module, offset=50.0, name="HostB")
        for size, ratio in (("B", 8.0), ("C", 9.25)):
            spec = self.spec_type(size, ratio)
            result = self.adapter.crossover(
                self.document, source_a, source_b, 2000.0, spec,
                minimum_radius=600.0,
            )
            self.assertEqual(result["status"], "transient-only")
            self.assertEqual(result["turnout_a"]["source_specification"],
                             result["turnout_b"]["source_specification"])
            self.assertEqual(result["turnout_a"]["dimensions"],
                             result["turnout_b"]["dimensions"])
            self.assertTrue(result["radius_assessment"]["accepted"])
            # The actual retained commit preflight rejects this payload
            # before using any cached geometry or changing a document.
            with self.assertRaisesRegex(ValueError, "preflight is invalid"):
                CrossoverPreflightAdapter._checked_result(None, {}, result)
        with self.assertRaisesRegex(ValueError, "different centrelines"):
            self.adapter.crossover(self.document, source_a, source_a, 2000.0,
                                   self.spec_type("C", 10))

    def test_existing_session_gate_cannot_be_bypassed(self):
        from tracktemplate.compatibility.transition_workflow import (
            ModularTransitionWorkflowSession,
        )

        session = object.__new__(ModularTransitionWorkflowSession)
        session._host = types.SimpleNamespace(module=self.module)
        calls = []
        session._validate_binding = lambda: calls.append("checked")
        result = session.prepare_rea_turnout_geometry(
            self.document, host(self.module), 2000.0,
            self.module.TURNOUT_HAND_LEFT,
            self.module.TURNOUT_ORIENTATION_FACING, self.spec_type("B", 8),
        )
        self.assertEqual(calls, ["checked"])
        self.assertEqual(result["source_specification"]["switch_size"], "B")

        def refuse():
            raise ValueError("mixed binding")

        session._validate_binding = refuse
        with self.assertRaisesRegex(ValueError, "mixed binding"):
            session.prepare_rea_turnout_geometry(
                self.document, host(self.module), 2000.0,
                self.module.TURNOUT_HAND_LEFT,
                self.module.TURNOUT_ORIENTATION_FACING,
                self.spec_type("B", 8),
            )

    def test_invalid_placement_and_existing_occupancy_refuse(self):
        module = self.module
        source_host = host(module)
        spec = self.spec_type("B", 8)
        for toe in (math.nan, math.inf, -1.0, 5001.0):
            with self.subTest(toe=toe), self.assertRaises(ValueError):
                self.adapter.turnout(self.document, source_host, toe,
                    module.TURNOUT_HAND_LEFT,
                    module.TURNOUT_ORIENTATION_FACING, spec)
        for hand, orientation in (("wrong", module.TURNOUT_ORIENTATION_FACING),
                                  (module.TURNOUT_HAND_LEFT, "wrong")):
            with self.assertRaises(ValueError):
                self.adapter.turnout(self.document, source_host, 2000,
                                     hand, orientation, spec)
        self.document.turnouts.append({
            "turnout_id": "TO-001", "host_object": source_host.Name,
            "toe_chainage": 2000.0,
            "orientation": module.TURNOUT_ORIENTATION_FACING,
            "track_gauge": 16.5, "flangeway": 1.0,
        })
        before = json.dumps(vars(self.document), sort_keys=True)
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.adapter.turnout(self.document, source_host, 2000,
                module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
                spec)
        self.assertEqual(json.dumps(vars(self.document), sort_keys=True), before)

    def test_invalid_crossover_input_stops_before_connector_search(self):
        module = self.module
        source_a = host(module)
        source_b = host(module, offset=50, name="HostB")
        cases = (
            {"reference_chainage": math.nan},
            {"reference_chainage": -1.0},
            {"arrangement": "wrong"},
            {"minimum_radius": math.nan},
            {"minimum_radius": module.CROSSOVER_MINIMUM_ALLOWED_RADIUS - 1},
            {"handing": module.TURNOUT_HAND_RIGHT},
        )
        for changes in cases:
            request = {"doc": self.document, "host_a": source_a,
                       "host_b": source_b, "reference_chainage": 2000,
                       "specification": self.spec_type("B", 8)}
            request.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.adapter.crossover(**request)


def validate():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SourceConsumerTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and not result.skipped
    print(SENTINEL)


if __name__ == "__main__":
    validate()
