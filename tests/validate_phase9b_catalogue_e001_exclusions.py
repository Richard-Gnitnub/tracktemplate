#!/usr/bin/env python3
"""Check two E001 finite-source exclusions without native construction.

All geometry here is invented. Rectangle clipping supplies an independent
intersection oracle. Public-binding checks retain the real classification
and receipt logic; earlier placement and native boundaries are stand-ins.
This proves neither physical fit nor FreeCAD geometry or GUI behaviour.
"""

from contextlib import ExitStack
import copy
import inspect
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    chair_check_placement,
    chair_pair_placement,
    transition_workflow,
)
from tracktemplate.domain.chair_placement import S1Placement  # noqa: E402

TIMBER_ID = "XO-001:ENVELOPE:001"
OWNER = "XO-001-A001"
NAMES = ("vee point rail", "vee splice rail")
IDS = tuple("XO-001:chair:xo-001-envelope-001:" + name.replace(" ", "-")
            for name in NAMES)
KIND = "source-anchor-outside-finite-rail-domain"
METHOD = "finite-polyline-outside-timber-edge-half-plane"


def fixture():
    """Invent canonical-shaped records with 1 mm and 2 mm clear gaps."""
    configuration = {
        "path_station": 8.0,
        "route_kinds": ["CONNECTOR", "HOST-A", "HOST-B"],
        "route_identities": [f"XO-001:VIRTUAL:{name}:001"
                             for name in ("CONNECTOR", "HOST-A", "HOST-B")],
        "source_note": "Invented shared envelope test fixture",
    }
    timber = {
        "stable_identity": TIMBER_ID, "identifier": "E001",
        "crossover_identity": "XO-001",
        "parent_turnout_identity": "XO-001:ENVELOPE",
        "envelope_timber": True, "turnout_side": "ENVELOPE",
        "envelope_path_station": 8.0,
        "outline_polygon": [[0.0, 0.0], [8.0, 0.0],
                            [8.0, 2.0], [0.0, 2.0]],
        "source_configuration": configuration,
    }
    positions, rails = {}, {}
    for index, name in enumerate(NAMES):
        points = ([[2.0, -4.0], [3.0, -3.0], [4.0, -1.0]] if index == 0
                  else [[5.0, -6.0], [6.0, -4.0], [7.0, -2.0]])
        rail_id = OWNER + ":rail:" + name.replace(" ", "-")
        rail_configuration = {"rail_geometry_revision": 2,
                              "gauge_face": name + " gauge face",
                              "outer_face": name + " outer face"}
        rails[rail_id] = {
            "stable_identity": rail_id, "name": name,
            "parent_turnout_identity": OWNER,
            "parent_crossover_identity": "XO-001", "points": points,
            "source_configuration": rail_configuration,
        }
        positions[IDS[index]] = {
            "stable_chair_position_identity": IDS[index],
            "parent_turnout_identity": OWNER,
            "parent_crossover_identity": "XO-001",
            "rail_identity": rail_id, "rail_name": name,
            "timber_identity": TIMBER_ID,
            "prototype_timber_identifier": "E001",
            "timber_identifier": "E001",
            "chair_code": 26 if index == 0 else 25,
            "chair_code_label": "BB/BC" if index == 0 else "AB",
            "special_assignment_deferred": True,
            "deliberate_omission": False,
            "centre_point": copy.deepcopy(points[-1]),
            "rail_station": sum(math.dist(a, b)
                                for a, b in zip(points, points[1:])),
            "source_configuration": {
                "rail": copy.deepcopy(rail_configuration),
                "timber": copy.deepcopy(configuration),
            },
            "chair_subtype": "deferred invented fixture",
            "assignment_status": "deferred to special-chair assignment",
            "source_or_assumed_classification": "temporary approximation",
            "key_direction_sign": 0, "key_orientation": "unresolved",
            "key_orientation_classification": "unresolved",
        }
    return positions, rails, {TIMBER_ID: timber}


def segment_intersects_box(start, end):
    """Clip a segment to the closed fixture box by axis intervals."""
    enter, leave = 0.0, 1.0
    for axis, lower, upper in ((0, 0.0, 8.0), (1, 0.0, 2.0)):
        delta = end[axis] - start[axis]
        if delta == 0:
            if not lower <= start[axis] <= upper:
                return False
            continue
        first, last = sorted(((lower - start[axis]) / delta,
                              (upper - start[axis]) / delta))
        enter, leave = max(enter, first), min(leave, last)
        if enter > leave:
            return False
    return True


def classify(source):
    return binding._e001_exclusions(*source)


class E001GeometryTests(unittest.TestCase):
    def test_invented_oracle_distinguishes_finite_rails_and_extensions(self):
        for rail in fixture()[1].values():
            points = rail["points"]
            self.assertFalse(any(segment_intersects_box(a, b)
                                 for a, b in zip(points, points[1:])))
            a, b = points[-2:]
            extension = [b[i] + 2 * (b[i] - a[i]) for i in (0, 1)]
            self.assertTrue(segment_intersects_box(b, extension))

    def test_two_exclusions_preserve_inputs_and_report_separate_fit_state(self):
        source = fixture()
        before = copy.deepcopy(source)
        result = classify(source)
        self.assertEqual(set(result), set(IDS))
        self.assertEqual(source, before)
        for index, identity in enumerate(IDS, 1):
            record = result[identity]
            self.assertEqual(record["exclusion_kind"], KIND)
            evidence = record["source_evidence"]
            self.assertEqual(evidence["method"], METHOD)
            self.assertEqual(evidence["finite_rail_segment_count"], 2)
            self.assertEqual(evidence["minimum_separation_mm"], index)
            self.assertEqual(evidence["endpoint_separation_mm"], index)
            self.assertIs(evidence["canonical_position_is_rail_endpoint"], True)
            self.assertEqual(evidence["physical_fit"], "NOT_ASSESSED")

    def test_rigid_frames_and_both_polygon_windings_preserve_separation(self):
        for angle in (0.0, 0.37, math.pi / 2):
            for reflection in (-1, 1):
                for reverse in (False, True):
                    with self.subTest(angle=angle, reflection=reflection,
                                      reverse=reverse):
                        source = fixture()
                        c, s = math.cos(angle), math.sin(angle)

                        def transform(point):
                            x, y = point[0], reflection * point[1]
                            return [17 + c * x - s * y,
                                    -23 + s * x + c * y]

                        polygon = source[2][TIMBER_ID]["outline_polygon"]
                        polygon[:] = [transform(point) for point in polygon]
                        if reverse:
                            polygon.reverse()
                        for position in source[0].values():
                            rail = source[1][position["rail_identity"]]
                            rail["points"] = [transform(point)
                                              for point in rail["points"]]
                            position["centre_point"] = rail["points"][-1][:]
                        result = classify(source)
                        # Floating arithmetic allowance, not physical fit.
                        allowance = 128 * sys.float_info.epsilon * 32
                        for index, identity in enumerate(IDS, 1):
                            evidence = result[identity]["source_evidence"]
                            for field in ("minimum_separation_mm",
                                          "endpoint_separation_mm"):
                                self.assertLessEqual(
                                    abs(evidence[field] - index), allowance,
                                )

    def test_intersection_touching_and_unseparated_paths_fail_closed(self):
        cases = {
            "crossing": [[4.0, -2.0], [4.0, 4.0]],
            "middle-enters": [[2.0, -4.0], [4.0, 1.0], [6.0, -1.0]],
            "touch-edge": [[2.0, -4.0], [4.0, 0.0]],
            "touch-corner": [[-2.0, -2.0], [0.0, 0.0]],
            # Disjoint, but no single timber edge separates all segments.
            "around-corner": [[-2.0, 1.0], [-2.0, -2.0], [4.0, -2.0]],
        }
        for label, points in cases.items():
            with self.subTest(label=label):
                source = fixture()
                position = source[0][IDS[0]]
                rail = source[1][position["rail_identity"]]
                rail["points"] = points
                position["centre_point"] = points[-1][:]
                observed = any(segment_intersects_box(a, b)
                               for a, b in zip(points, points[1:]))
                self.assertEqual(observed, label != "around-corner")
                with self.assertRaises(ValueError):
                    classify(source)

    def test_invalid_geometry_never_becomes_an_exclusion(self):
        for defect in ("short-rail", "nan-rail", "infinite-rail", "bool-rail",
                       "nan-polygon", "three-corners", "zero-edge",
                       "bow-tie", "concave", "centre-not-endpoint"):
            with self.subTest(defect=defect):
                source = fixture()
                position = source[0][IDS[0]]
                rail = source[1][position["rail_identity"]]
                timber = source[2][TIMBER_ID]
                if defect == "short-rail":
                    rail["points"] = [rail["points"][-1]]
                elif defect.endswith("rail"):
                    rail["points"][0][0] = {
                        "nan-rail": math.nan, "infinite-rail": math.inf,
                        "bool-rail": True,
                    }[defect]
                elif defect == "nan-polygon":
                    timber["outline_polygon"][0][0] = math.nan
                elif defect == "three-corners":
                    timber["outline_polygon"].pop()
                elif defect == "zero-edge":
                    timber["outline_polygon"][1] = [0.0, 0.0]
                elif defect == "bow-tie":
                    timber["outline_polygon"] = [
                        [0.0, 0.0], [8.0, 2.0], [8.0, 0.0], [0.0, 2.0],
                    ]
                elif defect == "concave":
                    timber["outline_polygon"][2] = [2.0, 0.5]
                else:
                    position["centre_point"][0] += 1
                with self.assertRaises(ValueError):
                    classify(source)

    def test_wrong_source_identity_owner_or_configuration_is_rejected(self):
        for defect in ("missing", "identity", "owner", "rail-id", "rail-owner",
                       "rail-name", "code", "deferred", "omitted", "prototype",
                       "timber-id", "generated", "route-kinds", "station",
                       "rail-configuration", "local-x", "extended-source"):
            with self.subTest(defect=defect):
                source = fixture()
                position = source[0][IDS[0]]
                rail = source[1][position["rail_identity"]]
                timber = source[2][TIMBER_ID]
                if defect == "missing":
                    del source[0][IDS[1]]
                elif defect == "identity":
                    position["stable_chair_position_identity"] = "wrong"
                elif defect == "owner":
                    position["parent_turnout_identity"] = "XO-001-B001"
                elif defect == "rail-id":
                    position["rail_identity"] = "XO-001-B001:rail:vee-point-rail"
                elif defect == "rail-owner":
                    rail["parent_turnout_identity"] = "XO-001-B001"
                elif defect == "rail-name":
                    position["rail_name"] = "vee splice rail"
                elif defect == "code":
                    position["chair_code"] = 25
                elif defect == "deferred":
                    position["special_assignment_deferred"] = False
                elif defect == "omitted":
                    position["deliberate_omission"] = True
                elif defect == "prototype":
                    position["prototype_timber_identifier"] = "R1"
                elif defect == "timber-id":
                    timber["stable_identity"] = "XO-001:ENVELOPE:002"
                elif defect == "generated":
                    timber["envelope_timber"] = False
                elif defect == "route-kinds":
                    timber["source_configuration"]["route_kinds"] = ["HOST-A"]
                elif defect == "station":
                    position["source_configuration"]["timber"]["path_station"] += 1
                elif defect == "rail-configuration":
                    position["source_configuration"]["rail"] = {}
                else:
                    key = ("local_x" if defect == "local-x"
                           else "extended_source_timber_identity")
                    timber["source_configuration"][key] = 8.0
                    for row in source[0].values():
                        row["source_configuration"]["timber"] = copy.deepcopy(
                            timber["source_configuration"],
                        )
                with self.assertRaises(ValueError):
                    classify(source)


def public_fixture(*, shared_owner_placed=True):
    """Include unchanged selected, unresolved and shared-support positions."""
    source = fixture()
    positions, rails, timbers = source
    for identity, code in (("accepted", 1), ("crossing", 25), ("shared", 0)):
        positions[identity] = dict(
            copy.deepcopy(positions[IDS[0]]),
            stable_chair_position_identity=identity, chair_code=code,
            chair_code_label="S1" if code == 1 else "deferred",
            deliberate_omission=code == 0,
        )
    selected = S1Placement("accepted", positions["accepted"]["rail_identity"],
                           TIMBER_ID, (0, 0, 0.8), (1, 0), (0, 1))
    plan = {
        "instances": [{"chair_position_identity": "accepted",
                       "centre_point": positions["accepted"]["centre_point"]}],
        "analytical_only": [{"chair_position_identity": identity,
                             "reason": "original preserved exclusion"}
                            for identity in positions if identity != "accepted"],
    }
    context = ("{}", {"geometry_signature": "invented",
                      "positions": list(positions.values())},
               {"future_chair_embed_depth": 0.2}, plan,
               list(rails.values()), list(timbers.values()))
    create = Mock(side_effect=lambda _path, groups, _shapes, receipt,
                  verify, **options: (groups, receipt, verify, options))
    verifier = Mock()
    owner = positions["accepted" if shared_owner_placed else "crossing"]
    return source, plan, context, selected, owner, create, verifier


def run_public(data, **options):
    source, _plan, context, selected, owner, create, verifier = data
    with ExitStack() as stack:
        for name, result in (
            ("_open_source_context", context),
            ("_require_p_crossover_context", {}),
            ("_whole_crossover_records", source[0]),
            ("_select_s1_s1j_positions", ((selected,), (), [])),
            ("_select_p_positions", ((), [], [], 0.8)),
            ("_shared_stock_support", owner),
            ("_context_shapes_and_verifier", ((), verifier)),
        ):
            stack.enter_context(patch.object(binding, name, return_value=result))
        stack.enter_context(patch.object(
            binding, "_recover_positions",
            side_effect=lambda _m, _a, _p, _r, _t, values, remaining, _c:
            (values, remaining, []),
        ))
        stack.enter_context(patch.object(
            chair_pair_placement, "prepare_crossover_pairs",
            return_value=({}, {}, Mock()),
        ))
        stack.enter_context(patch.object(
            chair_check_placement, "prepare_central_checks",
            return_value=((), {}, {}, Mock()),
        ))
        return binding.preview_private_catalogue_crossover_chairs(
            object(), SimpleNamespace(Name="Invented"), "XO-001", "unused",
            create, **options,
        )


class E001ReceiptTests(unittest.TestCase):
    def test_option_defaults_false_and_session_omits_false_keyword(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (method, binding.preview_private_catalogue_crossover_chairs):
            self.assertIs(inspect.signature(operation).parameters[
                "classify_e001_exclusions"].default, False)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for options in ({}, {"classify_e001_exclusions": False},
                        {"classify_e001_exclusions": True}):
            with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                              return_value="receipt") as operation:
                self.assertEqual(method(session, "doc", "XO-001", "catalogue",
                                        **options), "receipt")
            self.assertEqual(operation.call_args.kwargs,
                             options if options.get("classify_e001_exclusions")
                             else {})

    def test_non_booleans_fail_before_reading_or_native_boundary(self):
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(value=value), patch.object(
                binding, "_open_source_context",
            ) as opened:
                create = Mock()
                with self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        classify_e001_exclusions=value,
                    )
                opened.assert_not_called()
                create.assert_not_called()

    def test_only_two_receipt_rows_change_and_adapter_contract_is_unchanged(self):
        for central in (False, True):
            with self.subTest(central=central):
                data = public_fixture()
                before = copy.deepcopy(data[:2])
                options = ({"paired_contexts_path": "pairs",
                            "include_central_cc": True} if central else {})
                old_groups, old, _, old_options = run_public(data, **options)
                groups, new, _, adapter_options = run_public(
                    data, classify_e001_exclusions=True, **options,
                )
                self.assertEqual(data[:2], before)
                self.assertEqual(groups, old_groups)
                self.assertEqual(adapter_options, old_options)
                self.assertNotIn("classify_e001_exclusions", adapter_options)
                self.assertEqual(new["finite_source_exclusion_count"], 2)
                self.assertEqual(new["unresolved_source_position_count"], 1)
                self.assertNotIn("finite_source_exclusion_count", old)
                for key, value in old.items():
                    if key != "excluded_positions":
                        self.assertEqual(new[key], value, key)
                old_rows = {r["position_id"]: r for r in old["excluded_positions"]}
                new_rows = {r["position_id"]: r for r in new["excluded_positions"]}
                self.assertEqual(old_rows.keys(), new_rows.keys())
                for identity, previous in old_rows.items():
                    current = new_rows[identity]
                    if identity not in IDS:
                        self.assertEqual(current, previous)
                        continue
                    self.assertEqual(current["exclusion_kind"], KIND)
                    for key, value in previous.items():
                        if key not in ("exclusion_kind", "reason"):
                            self.assertEqual(current[key], value)
                    self.assertEqual(current["source_evidence"]["physical_fit"],
                                     "NOT_ASSESSED")

    def test_unplaced_shared_support_is_not_counted_as_represented(self):
        _, receipt, _, _ = run_public(
            public_fixture(shared_owner_placed=False),
            classify_e001_exclusions=True,
        )
        self.assertEqual(receipt["placement_count"], 1)
        self.assertEqual(receipt["finite_source_exclusion_count"], 2)
        self.assertEqual(receipt["unresolved_source_position_count"], 2)

    def test_invalid_or_changed_evidence_fails_before_or_inside_verifier(self):
        data = public_fixture()
        data[0][0][IDS[0]]["centre_point"][0] += 1
        with self.assertRaises(ValueError):
            run_public(data, classify_e001_exclusions=True)
        data[-2].assert_not_called()
        data = public_fixture()
        _, _, verify, _ = run_public(data, classify_e001_exclusions=True)
        verify()
        data[-1].assert_called_once_with()
        rail = data[0][1][data[0][0][IDS[0]]["rail_identity"]]
        rail["points"][1] = [4.0, 1.0]
        with self.assertRaises(ValueError):
            verify()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: two E001 finite-source exclusions preserve chair placement")
