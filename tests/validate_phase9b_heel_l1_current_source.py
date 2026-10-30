#!/usr/bin/env python3
"""Test narrow current-source L1 admission with invented host records.

The independent straight-rail arithmetic below reuses the accepted source
oracle, not product placement helpers. These are analytical and routing
checks; retained native geometry and real-GUI lifecycle remain unproved.
"""

from contextlib import ExitStack
import ast
import copy
import importlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as previous,
    transition_workflow,
)
from validate_phase9b_catalogue_heel_l1 import (  # noqa: E402
    CORRECTED_IDS, L1_SHA256, RAIL_NAMES, heel_source,
)
import single_rail_source_oracle as oracle  # noqa: E402

MODULE = "tracktemplate.compatibility.chair_heel_l1_placement"
SENTINEL = "Phase 9B current-source heel L1 standalone validation passed"


def source_case(radius=600.0):
    """Supply nominal identities on deliberately invented circular hosts."""
    module, document, signature, positions, timbers, data = heel_source()
    module.TURNOUT_SIZE_C10 = "C10"
    module.TURNOUT_DEFAULT_SCALE = 76.2
    module.CHAIR_ASSIGNMENT_CONFIRMED = "confirmed"
    module.CHAIR_CLASS_SOURCE = "source-derived"
    module.CHAIR_FAMILY_ORDINARY = "running rail"
    config = json.loads(signature)["configuration"]
    config.update(
        size="C10", track_gauge=16.5, flangeway=1.0,
        template_thickness=1.0, minimum_requested_radius=600.0,
        minimum_resulting_radius=650.0,
        chair_analysis_signature="radius:" + str(radius),
    )
    layout = [{"identifier": name, "x": station,
               "near_y": -10.0, "far_y": 15.0,
               "length_prototype_inches": 75.0}
              for name, station in oracle.NOMINAL_STATIONS]
    module.rea_c10_timber_layout = lambda *_args: copy.deepcopy(layout)
    selected_timbers = []
    for timber in timbers:
        name = timber["stable_identity"].split(":")[-1]
        if name not in ("S13", "T1", "T2"):
            continue
        side = timber["stable_identity"].split(":")[1]
        timber.update(
            identifier=name, prototype_reference=name, turnout_side=side,
            crossover_identity="XO-001",
            parent_turnout_identity=f"XO-001-{side}001",
            section="switch" if name == "S13" else "closure",
        )
        timber["source_configuration"].update(
            local_near_y=-10.0, local_far_y=15.0,
            length_prototype_inches=75.0, turnout_geometry_revision=2,
        )
        selected_timbers.append(timber)
    timbers = selected_timbers
    rails = []
    for side in ("A", "B"):
        constituent = config["turnout_" + side.lower() + "_config"]
        constituent.update(
            size="C10", turnout_id=f"XO-001-{side}001",
            track_gauge=16.5, flangeway=1.0, template_thickness=1.0,
            rail_geometry_revision=2, timber_geometry_revision=2,
        )
        for name in RAIL_NAMES.values():
            rails.append({
                "stable_identity": f"XO-001-{side}001:rail:"
                + name.replace(" ", "-"),
                "name": name, "parent_turnout_identity": f"XO-001-{side}001",
                "rail_role": "stock rail" if name == RAIL_NAMES[1] else RAIL_NAMES[3],
                "parent_crossover_identity": "XO-001", "turnout_side": side,
                "source_configuration": {
                    "rail_geometry_revision": 2,
                    "gauge_face": name + " gauge face",
                    "outer_face": name + " outer face",
                    "gauge_orientation_source": "mapped named turnout rail faces",
                },
            })
    selected = []
    for item in positions.values():
        if (item["prototype_timber_identifier"] not in ("S13", "T1", "T2")
                or item["rail_name"] not in RAIL_NAMES.values()):
            continue
        side = item["parent_turnout_identity"][-4]
        rail = next(r for r in rails if r["name"] == item["rail_name"]
                    and r["turnout_side"] == side)
        timber = next(t for t in timbers
                      if t["stable_identity"] == item["timber_identity"])
        item.update(
            rail_identity=rail["stable_identity"], parent_crossover_identity="XO-001",
            assignment_status="confirmed", assignment_complete_in_current_stage=True,
            deliberate_omission=False, stale_signature_state=False,
            validation_status="validated", key_direction_sign=0,
            timber_identifier=timber["identifier"], rail_role=rail["rail_role"],
            chair_family=module.CHAIR_FAMILY_ORDINARY,
            chair_subtype=("REA S1 ordinary chair beyond the C-switch block-chair zone"
                if timber["identifier"] == "S13" else
                "REA S1 ordinary closure-region chair; L1 clearance selection awaits detailed bridge-chair assignment"),
            source_or_assumed_classification=module.CHAIR_CLASS_SOURCE,
            chair_footprint_parameters={"dimension_classification": module.CHAIR_CLASS_SOURCE},
            key_orientation=previous._KEY_ORIENTATION,
            key_orientation_classification=previous._KEY_CLASSIFICATION,
            source_configuration={"rail": copy.deepcopy(rail["source_configuration"]),
                                  "timber": copy.deepcopy(timber["source_configuration"])},
        )
        selected.append(item)
    instances = [{"chair_position_identity": p["stable_chair_position_identity"],
                  "rail_identity": p["rail_identity"],
                  "timber_identity": p["timber_identity"],
                  "chair_code": 1, "chair_label": "S1", "base_z": 0.8}
                 for p in selected]
    settings = {"future_chair_embed_depth": 0.2,
                "rail_profile_id": dict(previous._CODE75_PROFILE)["profile_id"]}
    plan = {"instances": instances, "analytical_only": [],
            "entity_kind": "crossover", "entity_id": "XO-001",
            "settings": {"embed_depth": 0.2},
            "rail_profile": dict(previous._CODE75_PROFILE)}
    analysis = {"positions": selected, "geometry_signature": "radius:" + str(radius)}
    document.Name = "InventedCurrentHeel"

    def interpolate(_host, station):
        if radius is None:
            return SimpleNamespace(x=station, y=0.0), 0.0
        angle = station / radius
        return SimpleNamespace(x=radius * math.sin(angle),
                               y=radius * (1 - math.cos(angle))), angle

    module.interpolate_alignment_station = interpolate
    context = [json.dumps({"kind": "crossover", "configuration": config}),
               analysis, settings, plan, rails, timbers]
    source = SimpleNamespace(module=module, document=document, context=context,
                             data=data, config=config, radius=radius)
    update_timbers(source)
    return source


def update_timbers(source):
    """Map invented nominal timber centres through the test host only."""
    for timber in source.context[5]:
        side = timber["turnout_side"]
        config = source.config["turnout_" + side.lower() + "_config"]
        direction = 1 if config["orientation"] == "facing" else -1
        station = config["toe_chainage"] + direction * timber["source_configuration"]["local_x"]
        point, heading = source.module.interpolate_alignment_station(None, station)
        travel = heading + (math.pi if direction < 0 else 0)
        timber.update(host_chainage=station, local_rail_heading_radians=travel,
                      centre=[point.x + 2.5 * math.sin(travel),
                              point.y - 2.5 * math.cos(travel)])


def refresh(source):
    source.context[0] = json.dumps({"kind": "crossover", "configuration": source.config})


class CurrentHeelTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
                             "Current-source ten-chair L1 operation is missing")
        self.binding = importlib.import_module(MODULE)

    def call(self, source, factory=None):
        refresh(source)
        factory = factory or Mock(side_effect=lambda *args: args)
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                self.binding, "_open_source_context", return_value=source.context,
            ))
            stack.enter_context(patch.object(
                self.binding, "_context_shapes_and_verifier",
                return_value=(("rails", "timbers"), Mock()),
            ))
            stack.enter_context(patch.object(
                self.binding, "prepare_catalogue_chair",
                return_value=SimpleNamespace(label="L1", run="existing-02",
                    context="retained-S1-L1-reference-package", model_sha256=L1_SHA256),
            ))
            return self.binding.preview_private_catalogue_heel_l1_chairs(
                source.module, source.document, "XO-001", "private-catalogue", factory,
            )

    def reject(self, source):
        factory = Mock()
        with self.assertRaises(ValueError):
            self.call(source, factory)
        factory.assert_not_called()

    def test_ten_frames_change_and_return_without_changing_source(self):
        snapshots = []
        for radius in (600.0, 900.0, 600.0):
            source = source_case(radius)
            before = copy.deepcopy(source.context)
            _path, placements, _shapes, receipt, _verify = self.call(source)
            self.assertEqual(source.context, before)
            self.assertEqual({p.position_id for p in placements}, CORRECTED_IDS)
            self.assertEqual([p.position_id for p in placements], sorted(CORRECTED_IDS))
            self.assertEqual(receipt["selected_l1_count"], 10)
            self.assertEqual(receipt["analysis_position_count"], 12)
            self.assertFalse(receipt["source_document_mutation"])
            self.assertEqual(len(receipt["remaining_positions"]), 2)
            for selected in receipt["selected_positions"]:
                self.assertEqual(selected["family"], "L1")
                self.assertEqual(selected["original_family"], "S1")
            for placement in placements:
                owner = "A" if "xo-001-a-" in placement.position_id else "B"
                timber = next(p["prototype_timber_identifier"] for p in source.context[1]["positions"]
                              if p["stable_chair_position_identity"] == placement.position_id)
                station = dict(oracle.NOMINAL_STATIONS)[timber]
                reverse = owner == "B"
                chainage = 500 - station if reverse else 500 + station
                heading = chainage / radius + (math.pi if reverse else 0)
                point = (radius * math.sin(chainage / radius),
                         radius * (1 - math.cos(chainage / radius)))
                rail = 1 if placement.position_id.endswith("main-side-stock-rail") else 3
                local_frames = oracle.local_frames("L1", rail, 0.0, 0.0 if rail == 1 else 16.5)
                matrices = (local_frames["body"], *local_frames["fixings"])
                for actual, expected in zip((placement, *placement.fixing_frames), matrices):
                    x, y = expected[0][3], expected[1][3]
                    normal = (-math.sin(heading), math.cos(heading))
                    tangent = (math.cos(heading), math.sin(heading))
                    target = (point[0] + x * tangent[0] + (y + 8.25) * normal[0],
                              point[1] + x * tangent[1] + (y + 8.25) * normal[1], 0.8)
                    for a, b in zip(actual.origin_mm, target):
                        self.assertLessEqual(abs(a-b), 128*sys.float_info.epsilon*max(1000,abs(a),abs(b)))
                    for column, name in enumerate(("x_axis", "y_axis")):
                        axis = (expected[0][column], expected[1][column])
                        target_axis = (axis[0]*tangent[0] + axis[1]*normal[0],
                                       axis[0]*tangent[1] + axis[1]*normal[1])
                        for a, b in zip(getattr(actual, name), target_axis):
                            self.assertLessEqual(abs(a-b), 128*sys.float_info.epsilon*1000)
            snapshots.append(placements)
        self.assertNotEqual(snapshots[0], snapshots[1])
        self.assertEqual(snapshots[0], snapshots[2])

    def test_original_assignment_and_currentness_rejections(self):
        for field, value in (("chair_code", 5), ("chair_code_label", "L1"),
                ("assignment_status", "unknown"), ("assignment_complete_in_current_stage", False),
                ("special_assignment_deferred", True), ("deliberate_omission", True),
                ("stale_signature_state", True), ("validation_status", "invalid"),
                ("parent_crossover_identity", "XO-002"), ("parent_turnout_identity", "Other"),
                ("key_direction_sign", 1)):
            with self.subTest(field=field):
                source = source_case()
                source.context[1]["positions"][0][field] = value
                self.reject(source)

    def test_missing_duplicate_and_renamed_positions(self):
        for kind in ("missing", "duplicate", "renamed"):
            source = source_case()
            positions = source.context[1]["positions"]
            if kind == "missing":
                positions.pop(0)
            elif kind == "duplicate":
                positions.append(copy.deepcopy(positions[0]))
            else:
                positions[0]["stable_chair_position_identity"] = "Other"
            with self.subTest(kind=kind):
                self.reject(source)

    def test_nominal_timber_context_and_source_ownership_rejections(self):
        for field, value in (("local_x", 999), ("local_near_y", -9),
                ("local_far_y", 16), ("turnout_geometry_revision", 9),
                ("extended_source_timber_identity", "XO-001:A:S13")):
            source = source_case()
            timber = source.context[5][0]
            timber["source_configuration"][field] = value
            for p in source.context[1]["positions"]:
                if p["timber_identity"] == timber["stable_identity"]:
                    p["source_configuration"]["timber"][field] = value
            with self.subTest(field=field):
                self.reject(source)

    def test_source_signature_profile_and_minimum_radius_rejections(self):
        for change in ("signature", "profile", "below", "nan", "infinite", "zero"):
            source = source_case()
            if change == "signature":
                source.config["chair_analysis_signature"] = "stale"
            elif change == "profile":
                source.context[3]["rail_profile"]["rail_head_width_mm"] += 0.1
            else:
                source.config["minimum_resulting_radius"] = {
                    "below": 599.0, "nan": math.nan, "infinite": math.inf, "zero": 0,
                }[change]
            with self.subTest(change=change):
                self.reject(source)

    def test_minimum_radius_boundary_uses_existing_arithmetic_rule(self):
        source = source_case()
        source.config["minimum_resulting_radius"] = 600.0
        self.assertEqual(len(self.call(source)[1]), 10)
        source.config["minimum_resulting_radius"] = 600.0 - 2e-7
        self.reject(source)

    def test_rail_and_plan_disagreements_are_refused(self):
        for change in ("rail_owner", "rail_name", "rail_revision", "plan_code", "base_z"):
            source = source_case()
            if change == "rail_owner":
                source.context[4][0]["parent_turnout_identity"] = "Other"
            elif change == "rail_name":
                source.context[4][0]["name"] = "Other"
            elif change == "rail_revision":
                source.context[4][0]["source_configuration"]["rail_geometry_revision"] = 9
            elif change == "plan_code":
                source.context[3]["instances"][0]["chair_code"] = 5
            else:
                source.context[3]["instances"][0]["base_z"] = 1.2
            with self.subTest(change=change):
                self.reject(source)

    def test_late_host_change_is_rejected(self):
        source = source_case()
        _path, _placements, _shapes, _receipt, verify = self.call(source)
        with patch.object(self.binding, "verify_catalogue_sources"):
            verify()
            source.data["HostB"]["points"][0].x += 1
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_invalid_host_numbers_fail_before_creation(self):
        for field in ("toe", "total"):
            for value in (True, math.nan, math.inf, -math.inf):
                source = source_case()
                if field == "toe":
                    source.config["turnout_a_config"]["toe_chainage"] = value
                else:
                    source.data["HostA"]["total"] = value
                with self.subTest(field=field, value=value):
                    self.reject(source)

    def test_invalid_requested_radius_and_existing_boundary(self):
        for value in (True, 0, -1, math.nan, math.inf):
            source = source_case()
            source.config["minimum_requested_radius"] = value
            with self.subTest(value=value):
                self.reject(source)
        for delta in (0.0, -0.5e-7, -1e-7):
            source = source_case()
            source.config["minimum_resulting_radius"] = 600.0 + delta
            self.assertEqual(len(self.call(source)[1]), 10)

    def test_roles_and_classifications_are_not_inferred_from_identity(self):
        for field in ("rail_role", "timber_identifier", "chair_family",
                      "chair_subtype", "source_or_assumed_classification"):
            source = source_case()
            source.context[1]["positions"][0][field] = "Different"
            with self.subTest(field=field):
                self.reject(source)
        source = source_case()
        source.context[1]["positions"][0]["chair_footprint_parameters"]["dimension_classification"] = "assumed"
        self.reject(source)
        source = source_case()
        source.context[4][0]["rail_role"] = "check rail"
        self.reject(source)

    def test_nominal_timber_is_not_a_shoved_world_record(self):
        for field in ("host_chainage", "local_rail_heading_radians", "centre"):
            source = source_case()
            timber = source.context[5][0]
            if field == "centre":
                timber[field][0] += 1
            else:
                timber[field] += 1
            with self.subTest(field=field):
                self.reject(source)

    def test_both_directions_and_signed_curvature_keep_ten_identities(self):
        for radius in (None, -600.0, -900.0, -1800.0, 1800.0):
            for orientations in (("facing", "trailing"), ("trailing", "facing")):
                source = source_case(radius)
                for side, orientation in zip(("a", "b"), orientations):
                    source.config["turnout_" + side + "_config"]["orientation"] = orientation
                update_timbers(source)
                with self.subTest(radius=radius, orientations=orientations):
                    self.assertEqual({p.position_id for p in self.call(source)[1]}, CORRECTED_IDS)

    def test_host_station_endpoints_are_inclusive_and_outside_is_refused(self):
        first = dict(oracle.NOMINAL_STATIONS)["S13"]
        last = dict(oracle.NOMINAL_STATIONS)["T2"]
        source = source_case()
        source.config["turnout_b_config"]["toe_chainage"] = last
        source.data["HostA"]["total"] = 500 + last
        update_timbers(source)
        self.assertEqual(len(self.call(source)[1]), 10)
        source.config["turnout_b_config"]["toe_chainage"] = last - 0.01
        update_timbers(source)
        self.reject(source)
        source = source_case()
        source.data["HostA"]["total"] = 500 + first - 0.01
        self.reject(source)

    def test_original_exclusion_is_retained_and_unknown_refusals_stay_blocked(self):
        source = source_case()
        original = source.context[3]["instances"].pop(0)
        original.pop("chair_code")
        original.update(reason="gauge normal is not perpendicular to the local rail tangent",
                        deliberate_omission=False)
        source.context[3]["analytical_only"].append(original)
        receipt = self.call(source)[3]
        self.assertIn(original, [p["original_record"] for p in receipt["selected_positions"]])
        original["reason"] = "Unsupported source"
        self.reject(source)

    def test_late_original_verifier_and_catalogue_checks_are_called(self):
        source = source_case()
        original = Mock()
        prepared = SimpleNamespace(label="L1", run="existing-02",
            context="retained-S1-L1-reference-package", model_sha256=L1_SHA256)
        refresh(source)
        with (
            patch.object(self.binding, "_open_source_context", return_value=source.context),
            patch.object(self.binding, "_context_shapes_and_verifier", return_value=((), original)),
            patch.object(self.binding, "prepare_catalogue_chair", return_value=prepared),
            patch.object(self.binding, "verify_catalogue_sources") as catalogue,
        ):
            result = self.binding.preview_private_catalogue_heel_l1_chairs(
                source.module, source.document, "XO-001", "private", lambda *args: args)
            result[-1]()
            original.assert_called_once_with()
            catalogue.assert_called_once_with(prepared)
            original.side_effect = ValueError("source changed")
            with self.assertRaisesRegex(ValueError, "source changed"):
                result[-1]()
            original.side_effect = None
            catalogue.side_effect = ValueError("catalogue changed")
            with self.assertRaisesRegex(ValueError, "catalogue changed"):
                result[-1]()

    def test_l1_adapter_uses_retained_components_and_existing_lifecycle(self):
        from validate_phase9b_catalogue_heel_adapter import RoutingBoundary

        boundary = RoutingBoundary()
        namespace = boundary.namespace
        path = ROOT / "tracktemplate/adapters/freecad/chair_catalogue_placement_preview.py"
        tree = ast.parse(path.read_text(), filename=str(path))
        names = {"create_private_catalogue_l1_preview", "_create_private_catalogue_preview",
                 "_prepare_catalogue_family"}
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        self.assertEqual(len(nodes), 3)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
        namespace["_component_colour"] = lambda _label: (0.5, 0.5, 0.5)
        prepared = SimpleNamespace(label="L1", run="existing-02", model_sha256=L1_SHA256,
            context="retained-S1-L1-reference-package",
            components=tuple(SimpleNamespace(name=name, label=name)
                             for name in namespace["_L1_SOURCE_NAMES"]))
        namespace["prepare_catalogue_chair"] = Mock(return_value=prepared)
        source = source_case()
        placements = self.call(source)[1]
        source_check = Mock()
        result = namespace["create_private_catalogue_l1_preview"](
            "private", placements, ("rail-wires", "timber-wires"), {}, source_check)
        self.assertEqual(result.family, "L1")
        self.assertEqual(len(result.specs), 25)
        self.assertEqual(len(prepared.components), 23)
        self.assertTrue(all(len(p.fixing_frames) == 4 for p in placements))
        namespace["prepare_catalogue_chair"].assert_called_once_with(
            "private", "L1", run="existing-02")
        result.verify()
        source_check.assert_called_once_with()
        boundary.catalogue_checks.assert_called_once_with(prepared)
        for field, value in (("model_sha256", "wrong"), ("run", "basic-04"),
                             ("context", "wrong"), ("components", ())):
            original = getattr(prepared, field)
            setattr(prepared, field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                namespace["create_private_catalogue_l1_preview"](
                    "private", placements, (), {}, source_check)
            setattr(prepared, field, original)

    def test_plan_duplicates_and_unknown_sources_fail_before_creation(self):
        for kind in ("duplicate_instance", "overlap", "missing", "wrong_owner"):
            source = source_case()
            instances = source.context[3]["instances"]
            if kind == "duplicate_instance":
                instances.append(copy.deepcopy(instances[0]))
            elif kind == "overlap":
                source.context[3]["analytical_only"].append(copy.deepcopy(instances[0]))
            elif kind == "missing":
                instances.pop(0)
            else:
                source.context[4][0]["parent_turnout_identity"] = "Different"
                for position in source.context[1]["positions"]:
                    if position["rail_identity"] == source.context[4][0]["stable_identity"]:
                        position["parent_turnout_identity"] = "Different"
            with self.subTest(kind=kind):
                self.reject(source)

    def test_workflow_has_an_additive_private_command(self):
        method = getattr(transition_workflow.ModularCoreLayoutWorkflowSession,
                         "preview_private_catalogue_heel_l1_chairs", None)
        self.assertTrue(callable(method))
        session = SimpleNamespace(module=object(), routing_record=Mock(),
                                  _private_catalogue_l1_preview_factory=object())
        with patch.object(self.binding, "preview_private_catalogue_heel_l1_chairs",
                          return_value="receipt") as operation:
            self.assertEqual(method(session, "doc", "XO-001", "catalogue"), "receipt")
        operation.assert_called_once_with(session.module, "doc", "XO-001", "catalogue",
                                          session._private_catalogue_l1_preview_factory)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
