"""Check opt-in TO R2 source frames and finite support without FreeCAD.

Expected frames predate implementation. Metadata follows the retained TO
source; invented finite-geometry/host/catalogue/shape doubles qualify routing,
not native geometry, GUI, physical fit or production. Source-informed
fixtures are GPL-3.0-or-later; see NOTICE.md and reference/PROVENANCE.md.
"""

import copy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import transition_workflow  # noqa: E402
from validate_phase9b_left_hand_single_rail import FROZEN  # noqa: E402
from validate_phase9b_turnout_single_rail import (  # noqa: E402
    binding, corrected_source_case, selection,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary, FACTORY, FUNCTION, METHOD, ShapeDouble,
)

SENTINEL = "Phase 9B TO-001 R2 exit standalone validation passed"
FRAME_SHA = "009c1a8aaf46a7f33d1422d948c85ddcb6eda8a03abcafcb767c93f2f55ff095"


def fixture(name, digest):
    data = (ROOT / "tests/fixtures" / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest
    return json.loads(data)


def expected():
    return fixture("phase9b-to-r2-source-frames.json", FRAME_SHA)


def r2_inputs():
    """Keep source labels/configuration; use an explicitly invented rectangle."""
    oracle = expected()
    rs = dict(local_x=oracle["host"]["local_station_mm"],
              local_near_y=-16.10005179210283, local_far_y=39.89994820789717,
              length_prototype_inches=168.0, turnout_geometry_revision=2,
              crossing_suffix="", source_note="30-inch exit sleeper spacing",
              longitudinal_reference_axis=[0.7358589851037945, 0.6771348123099369])
    polygon = [[860, 480], [885, 480], [885, 495], [860, 495]]
    timber = dict(stable_identity="TO-001:timber:R2", identifier="R2",
                  parent_turnout_identity="TO-001", crossover_identity="",
                  source_configuration=rs, outline_polygon=polygon)
    positions, rails, exclusions = [], [], []
    for suffix, code, label, family, centre in (
        ("point", 26, "BB/BC", "vee support", [874, 487]),
        ("splice", 25, "AB", "splice-rail support", [868, 488]),
    ):
        name = f"vee {suffix} rail"
        rail_id = "TO-001:rail:" + name.replace(" ", "-")
        identity = "TO-001:chair:to-001-timber-r2:" + name.replace(" ", "-")
        rail_source = dict(gauge_face=name + " gauge face",
                           outer_face=name + " outer face",
                           gauge_orientation_source="mapped named turnout rail faces",
                           rail_geometry_revision=2)
        rails.append(dict(stable_identity=rail_id, name=name, rail_role=name,
                          parent_turnout_identity="TO-001", parent_crossover_identity="",
                          source_configuration=rail_source,
                          gauge_face_points=[[850, centre[1]], [895, centre[1]]],
                          points=[[850, centre[1]], [895, centre[1]]],
                          outer_face_points=[[850, centre[1] + 1], [895, centre[1] + 1]]))
        positions.append(dict(
            stable_chair_position_identity=identity, rail_identity=rail_id,
            rail_name=name, rail_role=name, timber_identity="TO-001:timber:R2",
            prototype_timber_identifier="R2", timber_identifier="R2",
            parent_turnout_identity="TO-001", parent_crossover_identity="",
            handedness="Left-hand", chair_code=code, chair_code_label=label,
            chair_family=family, assignment_status="deferred to special-chair assignment",
            assignment_complete_in_current_stage=False, special_assignment_deferred=True,
            deliberate_omission=False, stale_signature_state=False,
            validation_status="Advisory", key_direction_sign=0,
            key_orientation="requires confirmation from the final special-chair "
            "subtype and keying arrangement",
            key_orientation_classification="dimension requiring later confirmation",
            source_or_assumed_classification="temporary visual approximation",
            source_configuration={"rail": rail_source, "timber": rs}, centre_point=centre,
        ))
        exclusions.append(dict(chair_position_identity=identity, rail_identity=rail_id,
                               timber_identity="TO-001:timber:R2", chair_label=label,
                               chair_family=family, deliberate_omission=False,
                               reason="special chair assignment remains analytical",
                               unresolved_special=True))
    return dict(positions=positions, rails=rails, timber=timber, exclusions=exclusions)


def source_case():
    """Use existing doubles with retained frames and invented finite geometry."""
    source = corrected_source_case()
    inputs = r2_inputs()
    oracle = expected()
    analysis, rails, timbers = source.context[2], source.context[4], source.context[5]
    for index, row in enumerate(inputs["positions"], 12):
        old = "invented-unselected-" + f"{index:03d}"
        slot = next(i for i, p in enumerate(analysis["positions"])
                    if p["stable_chair_position_identity"] == old)
        analysis["positions"][slot] = row
        source.plan["analytical_only"][:] = [
            p for p in source.plan["analytical_only"]
            if p["chair_position_identity"] != old
        ]
    source.plan["analytical_only"].extend(inputs["exclusions"])
    rails.extend(inputs["rails"])
    timbers.append(inputs["timber"])
    rs = inputs["timber"]["source_configuration"]
    source.layout.append(dict(identifier="R2", x=rs["local_x"],
                              near_y=rs["local_near_y"], far_y=rs["local_far_y"],
                              length_prototype_inches=rs["length_prototype_inches"]))
    dimensions = source.module.rea_c10_dimensions()
    dimensions["a_timber_x"] = 287.23290043721454
    host_frames = {row[0]: (row[3], row[4]) for row in FROZEN}
    host_frames["R2"] = (oracle["host"]["host_point_mm"],
                         oracle["host"]["host_heading_rad"])
    original = source.module.interpolate_alignment_station
    stations = {}
    for timber in timbers:
        if timber["identifier"] not in host_frames:
            continue
        point, heading = host_frames[timber["identifier"]]
        config = timber["source_configuration"]
        station = 746.298 + config["local_x"]
        stations[station] = (SimpleNamespace(x=point[0], y=point[1]), heading)
        mean = (config["local_near_y"] + config["local_far_y"]) / 2
        timber.update(host_chainage=station, local_rail_heading_radians=heading,
                      centre=[point[0] - mean * math.sin(heading),
                              point[1] + mean * math.cos(heading)])
    source.module.interpolate_alignment_station = (
        lambda data, station: stations[station] if station in stations
        else original(data, station)
    )
    for record in source.plan["instances"]:
        record["base_z"] = 0.8
    return source


def preview(source, factory=None, **options):
    command = binding()
    with (patch.dict(sys.modules, {"FreeCAD": source.app}),
          patch.object(command, "prepare_catalogue_chair", side_effect=selection),
          patch.object(command, "verify_catalogue_sources")):
        return command.preview_private_catalogue_turnout_single_rail_chairs(
            source.module, source.document, "TO-001", "catalogue.json",
            factory or (lambda *args, **kwargs: (args, kwargs)), **options,
        )


def adapter(boundary, placements, **options):
    return boundary.namespace[FUNCTION](
        "catalogue.json", placements,
        (ShapeDouble(context=True), ShapeDouble(context=True)),
        {"represented_source_position_count": len(placements)},
        boundary.source_check, **options,
    )


class TurnoutR2Tests(unittest.TestCase):
    def near(self, actual, wanted):
        self.assertEqual(len(actual), len(wanted))
        for a, b in zip(actual, wanted):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def test_default_twelve_and_false_are_identical(self):
        source = source_case()
        default, kwargs = preview(source)
        explicit, forwarded = preview(source, include_r2_exit=False)
        self.assertEqual(kwargs, {})
        self.assertEqual(forwarded, {})
        self.assertEqual(default[:2], explicit[:2])
        self.assertEqual(default[3], explicit[3])
        self.assertEqual([vars(shape) for shape in default[2]],
                         [vars(shape) for shape in explicit[2]])
        self.assertEqual(len(default[1]), 12)
        self.assertEqual(default[3]["selected_family_counts"], {"L1": 11, "S1": 1})

    def test_fourteen_source_identities_and_all_sixty_seven_frames(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        (args, kwargs) = preview(source, include_r2_exit=True)
        self.assertEqual(kwargs, {"include_r2_exit": True})
        placements, receipt = args[1], args[3]
        self.assertEqual(len(placements), 14)
        self.assertEqual(len({p.position_id for p in placements}), 14)
        self.assertEqual(receipt["selected_family_counts"], {"L1": 11, "S1": 3})
        self.assertEqual(receipt["represented_source_position_count"], 14)
        self.assertEqual(len(receipt["remaining_positions"]), 154)
        self.assertEqual(len(receipt["corrected_heel_positions"]), 5)
        self.assertEqual((source.context, source.plan), before)
        baseline = fixture("phase9b-to-single-rail-frames.json",
                           "407040d01dd0f9c8ac275d7e4d40c928ea32a5da0a05c853bf3a1de4221a8d4b")
        wanted = {r["position_id"]: r for r in
                  baseline["positions"] + expected()["positions"]}
        frames = 0
        for p in placements:
            row = wanted[p.position_id]
            for actual, frozen in zip((p,) + p.fixing_frames,
                                      [row["body"]] + row["fixing_frames"]):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(actual, field), frozen[field])
                frames += 1
        self.assertEqual(frames, 67)
        with patch.object(binding(), "verify_catalogue_sources"):
            args[4]()

    def test_adapter_materialises_304_component_transforms_in_42_layers(self):
        values = preview(source_case(), include_r2_exit=True)[0][1]
        boundary = AdapterBoundary()
        result = adapter(boundary, values, include_r2_exit=True)
        layers, receipt, verify = result.prepare()
        self.assertEqual(len(layers), 42)
        self.assertEqual(receipt["placement_count"], 14)
        self.assertEqual(receipt["component_count"], 40)  # Family prototypes.
        self.assertEqual(sum(len(s.children) for s in layers[2:]), 304)
        by_id = {p.position_id: p for p in values}
        count = 0
        for family in receipt["families"].values():
            for p in family["placements"]:
                original = by_id[p["position_id"]]
                for component in p["components"]:
                    name = component["source_name"]
                    fixing = boundary.namespace["_CC_FIXING_NAMES"]
                    frame = (original.fixing_frames[fixing.index(name) // 4]
                             if name in fixing else original)
                    for field in ("origin_mm", "x_axis", "y_axis"):
                        self.assertEqual(component[field], getattr(frame, field))
                    count += 1
        self.assertEqual(count, 304)
        verify(layers)

    def test_adapter_independently_refuses_partial_duplicate_or_wrong_owners(self):
        values = preview(source_case(), include_r2_exit=True)[0][1]
        r2 = next(p for p in values if p.timber_id.endswith(":R2"))
        wrong = replace(r2, family="S1J")
        for bad, opt in ((values, {}), (values[:-1], {"include_r2_exit": True}),
                         (values + (r2,), {"include_r2_exit": True}),
                         (tuple(wrong if p is r2 else p for p in values),
                          {"include_r2_exit": True})):
            with self.subTest(size=len(bad), opt=opt):
                boundary = AdapterBoundary()
                with self.assertRaises(ValueError):
                    adapter(boundary, bad, **opt)
                boundary.materialise.assert_not_called()

    def test_actual_boolean_required_at_all_three_boundaries(self):
        for bad in (None, 0, 1, "true", (), []):
            with self.subTest(value=bad):
                create = Mock()
                with self.assertRaises(ValueError):
                    preview(source_case(), create, include_r2_exit=bad)
                create.assert_not_called()
                boundary = AdapterBoundary()
                with self.assertRaises(ValueError):
                    adapter(boundary, (), include_r2_exit=bad)
                boundary.materialise.assert_not_called()
                session = SimpleNamespace(routing_record=Mock())
                method = getattr(transition_workflow.ModularCoreLayoutWorkflowSession,
                                 METHOD)
                with self.assertRaises(ValueError):
                    method(session, object(), "TO-001", "catalogue.json",
                           include_r2_exit=bad)
                session.routing_record.assert_not_called()

    def test_session_forwards_only_explicit_true_after_routing(self):
        from validate_phase9b_l1_reference_preview import _session

        session = _session()
        setattr(session, "_" + FACTORY, object())
        for opt, wanted in (({}, {}), ({"include_r2_exit": False}, {}),
                            ({"include_r2_exit": True}, {"include_r2_exit": True})):
            with patch.object(binding(), METHOD, return_value="receipt") as operation:
                self.assertEqual(getattr(session, METHOD)(
                    "document", "TO-001", "catalogue.json", **opt), "receipt")
                self.assertEqual(operation.call_args.kwargs, wanted)

    def test_source_identity_raw_labels_ownership_and_currentness(self):
        changes = {
            "chair_code_label": "S1", "chair_code": True,
            "parent_turnout_identity": "TO-002", "parent_crossover_identity": "XO-001",
            "rail_identity": "TO-001:rail:main-side-stock-rail",
            "timber_identity": "TO-001:timber:R1", "handedness": "Right-hand",
            "assignment_complete_in_current_stage": True,
            "special_assignment_deferred": False, "stale_signature_state": True,
            "source_configuration": {}, "chair_family": "ordinary running-rail chair",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                source = source_case()
                record = next(p for p in source.context[2]["positions"]
                              if "timber-r2:vee-" in p["stable_chair_position_identity"])
                record[field] = value
                create = Mock()
                with self.assertRaises(ValueError):
                    preview(source, create, include_r2_exit=True)
                create.assert_not_called()

    def test_missing_duplicate_and_modified_original_exclusion(self):
        for kind in ("missing", "duplicate", "exclusion", "rail-owner", "timber-owner"):
            with self.subTest(kind=kind):
                source = source_case()
                positions = source.context[2]["positions"]
                row = next(p for p in positions
                           if "timber-r2:vee-" in p["stable_chair_position_identity"])
                if kind == "missing":
                    positions.remove(row)
                elif kind == "duplicate":
                    positions.append(copy.deepcopy(row))
                elif kind == "exclusion":
                    next(p for p in source.plan["analytical_only"]
                         if p["chair_position_identity"] == row[
                             "stable_chair_position_identity"])["chair_label"] = "S1"
                elif kind == "rail-owner":
                    next(p for p in source.context[4] if p["stable_identity"] ==
                         row["rail_identity"])["parent_turnout_identity"] = "TO-002"
                else:
                    source.context[5][-1]["crossover_identity"] = "XO-001"
                create = Mock()
                with self.assertRaises(ValueError):
                    preview(source, create, include_r2_exit=True)
                create.assert_not_called()

    def test_finite_actual_support_refuses_outside_boundary_and_bad_geometry(self):
        for kind in ("centre-outside", "centre-boundary", "finite-end", "missing-outer",
                     "nonfinite", "boolean", "degenerate", "self-crossing"):
            with self.subTest(kind=kind):
                source = source_case()
                timber = source.context[5][-1]
                row = next(p for p in source.context[2]["positions"]
                           if "timber-r2:vee-" in p["stable_chair_position_identity"])
                rail = next(p for p in source.context[4]
                            if p["stable_identity"] == row["rail_identity"])
                if kind.startswith("centre"):
                    row["centre_point"] = ([0, 0] if kind == "centre-outside"
                                           else timber["outline_polygon"][0])
                elif kind == "finite-end":
                    rail["gauge_face_points"] = [[850, 487], [855, 487]]
                elif kind == "missing-outer":
                    rail["outer_face_points"] = []
                elif kind in ("nonfinite", "boolean"):
                    rail["points"][0][0] = float("nan") if kind == "nonfinite" else True
                elif kind == "degenerate":
                    timber["outline_polygon"] = [[0, 0]] * 16
                else:
                    polygon = timber["outline_polygon"]
                    polygon[1], polygon[2] = polygon[2], polygon[1]
                create = Mock()
                with self.assertRaises(ValueError):
                    preview(source, create, include_r2_exit=True)
                create.assert_not_called()

    def test_nominal_source_host_and_late_verifier_remain_strict(self):
        for kind in ("source", "host", "outside-host", "late-host"):
            with self.subTest(kind=kind):
                source = source_case()
                host = source.module.turnout_host_alignment(None)
                if kind == "source":
                    source.context[5][-1]["source_configuration"]["local_x"] += 1
                elif kind == "host":
                    source.context[5][-1]["centre"][0] += 1
                elif kind == "outside-host":
                    host["total"] = 1000.0
                if kind == "late-host":
                    args, _kw = preview(source, include_r2_exit=True)
                    host["points"][0].x += 1
                    with self.assertRaises(ValueError):
                        args[4]()
                else:
                    create = Mock()
                    with self.assertRaises(ValueError):
                        preview(source, create, include_r2_exit=True)
                    create.assert_not_called()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TurnoutR2Tests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
