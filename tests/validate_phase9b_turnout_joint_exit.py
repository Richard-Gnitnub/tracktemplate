"""Check the fixed three-position TO joint group without native execution.

Independent 556b frames are copied from the reviewed source packet.
Synthetic outlines and host/catalogue doubles test admission, not fit.
Source-informed metadata is GPL-3.0-or-later; see NOTICE.md.
"""

import copy
from dataclasses import replace
import hashlib
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import single_rail_source_oracle as oracle  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain.single_rail_placement import (  # noqa: E402
    place_left_hand_single_rail,
)
from validate_phase9b_turnout_crossing_tail import (  # noqa: E402
    observable, source_case as tail_source_case,
)
from validate_phase9b_turnout_r2_exit import (  # noqa: E402
    adapter, fixture, r2_inputs,
)
from validate_phase9b_turnout_single_rail import (  # noqa: E402
    binding, selection,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary, FACTORY, METHOD,
)

SENTINEL = "Phase 9B TO-001 joint-exit standalone validation passed"
FRAME_SHA = (
    "04736591db0df308f2a3b7ce15146c8557fb529ffb7921e478c44bf4adf55cd9"
)
S1J_SHA = "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b"
BLOCKED = "TO-001:chair:to-001-timber-x9-f:turnout-side-stock-rail"
# Captured before product edits against aa1db705, on this exact source case.
BASELINE_SHA = (
    "50bb5ba4810838a6f4fcc8a98ecd959f852970773fa582b21a4a1d01b1ab9407",
    "29399fc000b833466bb3ef3759c5b8047e81b2b0767f0a3f29f2b5291112677d",
    "2d2168129717d67e2637a01c67a78eaa15fe6f52d3af622e11a3120825393eca",
    "47152c56cb3e508cfbd818fd626b59ff4e741fe45b5391544c0551bba95f83ba",
)


def expected():
    return fixture("phase9b-to-joint-exit-source-frames.json", FRAME_SHA)


def source_case():
    """Extend existing admission doubles; no expected geometry is derived."""
    source = tail_source_case()
    analysis, rails, timbers = (
        source.context[2], source.context[4], source.context[5]
    )
    template = r2_inputs()["positions"][0]
    rows = copy.deepcopy(expected()["positions"])
    blocked = copy.deepcopy(rows[0])
    blocked.update(
        position_id=BLOCKED,
        rail_id="TO-001:rail:turnout-side-stock-rail",
        source_rail_code=4,
    )
    rows.append(blocked)
    old_interpolate = source.module.interpolate_alignment_station
    stations = {}
    for index, row in enumerate(rows, 22):
        name = row["timber_id"].split(":")[-1]
        rail = next(r for r in rails if r["stable_identity"] == row["rail_id"])
        point = row["host_basis"]["host_point_mm"]
        heading = row["host_basis"]["heading_radians"]
        station = row["host_basis"]["host_station_mm"]
        stations[station] = (SimpleNamespace(x=point[0], y=point[1]), heading)
        timber = next((t for t in timbers if t["identifier"] == name), None)
        if timber is None:
            timber_source = dict(
                local_x=row["source_station_mm"], local_near_y=-16.0,
                local_far_y=20.0, length_prototype_inches=108.0,
                turnout_geometry_revision=2, crossing_suffix="",
            )
            timber = dict(
                stable_identity=row["timber_id"], identifier=name,
                parent_turnout_identity="TO-001", crossover_identity="",
                source_configuration=timber_source, host_chainage=station,
                local_rail_heading_radians=heading,
                centre=[point[0] - 2 * math.sin(heading),
                        point[1] + 2 * math.cos(heading)],
                outline_polygon=[[800, 400], [920, 400],
                                 [920, 520], [800, 520]],
            )
            timbers.append(timber)
            source.layout.append(dict(
                identifier=name, x=row["source_station_mm"],
                near_y=-16.0, far_y=20.0, length_prototype_inches=108.0,
            ))
        # Existing tail fixture supplies finite invented lines on these rails.
        record = copy.deepcopy(template)
        record.update(
            stable_chair_position_identity=row["position_id"],
            rail_identity=row["rail_id"], rail_name=rail["name"],
            rail_role="stock rail" if name == "X9-F" else rail["name"],
            timber_identity=row["timber_id"], timber_identifier=name,
            prototype_timber_identifier=name, chair_code=row["raw_code"],
            chair_code_label=row["raw_label"],
            chair_family=("common-crossing chair" if name == "X9-F" else
                          "splice-rail support" if row["source_rail_code"] == 2
                          else "vee support"),
            source_configuration={"rail": rail["source_configuration"],
                                  "timber": timber["source_configuration"]},
            centre_point=[1000, 1000] if row["position_id"] == BLOCKED
            else [870, 487],
        )
        old_id = f"invented-unselected-{index:03d}"
        slot = next(i for i, p in enumerate(analysis["positions"])
                    if p["stable_chair_position_identity"] == old_id)
        analysis["positions"][slot] = record
        original = next(p for p in source.plan["analytical_only"]
                        if p["chair_position_identity"] == old_id)
        original.update(
            chair_position_identity=row["position_id"],
            rail_identity=row["rail_id"], timber_identity=row["timber_id"],
            chair_label=row["raw_label"], chair_family=record["chair_family"],
            deliberate_omission=False, unresolved_special=True,
            reason="special chair assignment remains analytical",
        )
    source.module.interpolate_alignment_station = lambda data, station: (
        stations[station] if station in stations
        else old_interpolate(data, station)
    )
    return source


def catalogue(path, family, *, run):
    if family != "S1J":
        return selection(path, family, run=run)
    return SimpleNamespace(
        label="S1J", run=run, context="fixed-basic-source-context",
        model_sha256=S1J_SHA, components=tuple(range(18)),
    )


def preview(source, factory=None, *, select=catalogue, **options):
    command = binding()
    with (patch.dict(sys.modules, {"FreeCAD": source.app}),
          patch.object(command, "prepare_catalogue_chair", side_effect=select),
          patch.object(command, "verify_catalogue_sources")):
        return getattr(command, METHOD)(
            source.module, source.document, "TO-001", "catalogue.json",
            factory or (lambda *args, **kwargs: (args, kwargs)), **options,
        )


def joint_records(source):
    ids = {r["position_id"] for r in expected()["positions"]}
    return [p for p in source.context[2]["positions"]
            if p["stable_chair_position_identity"] in ids]


def arguments(row):
    pose = oracle.source_rail_pose(
        oracle.SOURCE_PARAMETERS, row["source_station_mm"],
        row["source_rail_code"],
    )
    return dict(
        position_id=row["position_id"], rail_id=row["rail_id"],
        timber_id=row["timber_id"], family=row["family"],
        source_rail_code=row["source_rail_code"],
        source_angle_rad=pose["k_rad"], source_gauge_y_mm=pose["y_mm"],
        host_point_mm=row["host_basis"]["host_point_mm"],
        travel_heading_rad=row["host_basis"]["heading_radians"],
        base_z_mm=row["body"]["origin_mm"][2],
    )


def boundary():
    result = AdapterBoundary()
    item = result.selection("S1J")
    item.run = "basic-04"
    item.context = "fixed-basic-source-context"
    result.selections["S1J"] = item

    def select(_path, family, *, run):
        assert run == ("basic-04" if family == "S1J" else "existing-02")
        return result.selections[family]

    result.namespace["prepare_catalogue_chair"] = select
    return result


class JointExitTests(unittest.TestCase):
    def near(self, actual, frozen):
        self.assertEqual(len(actual), len(frozen))
        for a, b in zip(actual, frozen):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def refuse(self, source, **kwargs):
        create = Mock()
        with self.assertRaises(ValueError):
            preview(source, create, include_joint_exit=True, **kwargs)
        create.assert_not_called()

    def test_all_four_previous_modes_preserve_complete_output_bytes(self):
        for index, (r2, tail) in enumerate(
            (r, t) for r in (False, True) for t in (False, True)
        ):
            options = {k: True for k, v in (
                ("include_r2_exit", r2), ("include_crossing_tail", tail)
            ) if v}
            source = source_case()
            select = Mock(side_effect=catalogue)
            old, forwarded = preview(source, select=select, **options)
            new, explicit = preview(
                source, include_joint_exit=False, select=select, **options
            )
            self.assertEqual(forwarded, options)
            self.assertEqual(explicit, options)
            self.assertEqual(observable(old), observable(new))
            self.assertEqual(hashlib.sha256(observable(new)).hexdigest(),
                             BASELINE_SHA[index])
            self.assertNotIn("S1J", [c.args[1] for c in select.call_args_list])

    def test_direct_thirteen_independent_lh_frames(self):
        count = 0
        for row in expected()["positions"]:
            value = place_left_hand_single_rail(**arguments(row))
            self.assertEqual(value.family, row["family"])
            for actual, frozen in zip((value,) + value.fixing_frames,
                                      [row["body"]] + row["fixing_frames"]):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(actual, field), frozen[field])
                count += 1
        self.assertEqual(count, 13)

    def test_frames_follow_rigid_host_transforms_and_both_travel_directions(
        self,
    ):
        for row in expected()["positions"]:
            base = arguments(row)
            for delta in (math.pi, -0.71, 1.25):
                c, s = math.cos(delta), math.sin(delta)

                def rotate(point):
                    return (c * point[0] - s * point[1],
                            s * point[0] + c * point[1])

                host = rotate(base["host_point_mm"])
                values = dict(base, host_point_mm=(host[0] + 7, host[1] - 11),
                              travel_heading_rad=base["travel_heading_rad"]
                              + delta, base_z_mm=2.0)
                placed = place_left_hand_single_rail(**values)
                for actual, frozen in zip((placed,) + placed.fixing_frames,
                                          [row["body"]] + row["fixing_frames"]):
                    origin = rotate(frozen["origin_mm"])
                    self.near(actual.origin_mm,
                              (origin[0] + 7, origin[1] - 11, 2.0))
                    self.near(actual.x_axis, rotate(frozen["x_axis"]))
                    self.near(actual.y_axis, rotate(frozen["y_axis"]))
        for key, bad in (("source_angle_rad", math.nan),
                         ("source_gauge_y_mm", True), ("base_z_mm", math.inf),
                         ("source_rail_code", True), ("family", "unknown")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                place_left_hand_single_rail(**dict(arguments(
                    expected()["positions"][0]), **{key: bad}))
        # This outcome admits S1J only on source rails 1/3. A mathematically
        # finite curved pose does not establish another qualified consumer.
        for rail in (2, 4):
            pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, 337, rail)
            with self.subTest(unsupported_s1j_rail=rail):
                with self.assertRaises(ValueError):
                    place_left_hand_single_rail(**dict(
                        arguments(expected()["positions"][0]),
                        source_rail_code=rail,
                        source_angle_rad=pose["k_rad"],
                        source_gauge_y_mm=pose["y_mm"],
                    ))

    def test_four_added_modes_exact_counts_and_original_records(self):
        ids = {r["position_id"] for r in expected()["positions"]}
        for r2, tail, counts in (
            (False, False, (15, 72, 327)), (True, False, (17, 80, 361)),
            (False, True, (23, 106, 475)), (True, True, (25, 114, 509)),
        ):
            source = source_case()
            before = copy.deepcopy((source.context, source.plan))
            options = dict(include_r2_exit=r2, include_crossing_tail=tail)
            old = preview(source, **options)[0]
            args, forwarded = preview(
                source, include_joint_exit=True, **options
            )
            values, receipt = args[1], args[3]
            self.assertEqual(forwarded, {k: True for k, v in
                             dict(options, include_joint_exit=True).items()
                             if v})
            self.assertEqual((len(values),
                              sum(1 + len(p.fixing_frames) for p in values),
                              sum(23 if p.family == "L1" else 17
                                  for p in values)), counts)
            self.assertEqual(tuple(p for p in values if p.position_id not in ids),
                             old[1])
            self.assertEqual({p.position_id for p in values},
                             {p.position_id for p in old[1]} | ids)
            by_id = {p.position_id: p for p in values}
            for row in expected()["positions"]:
                value = by_id[row["position_id"]]
                self.assertEqual(value.family, row["family"])
                self.assertEqual(len(value.fixing_frames),
                                 len(row["fixing_frames"]))
                for actual, frozen in zip((value,) + value.fixing_frames,
                                          [row["body"]] + row["fixing_frames"]):
                    for field in ("origin_mm", "x_axis", "y_axis"):
                        self.near(getattr(actual, field), frozen[field])
            self.assertEqual(receipt["corrected_heel_positions"],
                             old[3]["corrected_heel_positions"])
            self.assertEqual(len(receipt["corrected_heel_positions"]), 5)
            self.assertEqual(receipt["selected_family_counts"], {
                "L1": 14 if tail else 12, "S1": 1 + 2 * r2 + 6 * tail,
                "S1J": 2,
            })
            self.assertEqual(len(receipt["remaining_positions"]),
                             168 - counts[0])
            self.assertIn(BLOCKED, {p["stable_chair_position_identity"]
                                   for p in receipt["remaining_positions"]})
            self.assertEqual((source.context, source.plan), before)

    def test_adapter_materialises_all_indexed_components_without_rebuild(self):
        for r2, tail, total in ((False, False, 327), (True, False, 361),
                                (False, True, 475), (True, True, 509)):
            options = dict(include_r2_exit=r2, include_crossing_tail=tail,
                           include_joint_exit=True)
            values = preview(source_case(), **options)[0][1]
            host = boundary()
            made = adapter(host, values, **options)
            layers, receipt, verify = made.prepare()
            self.assertEqual(len(layers), 59)
            self.assertEqual(receipt["component_count"], 57)
            self.assertEqual(receipt["family_count"], 3)
            self.assertEqual(sum(len(s.children) for s in layers[2:]), total)
            by_id = {p.position_id: p for p in values}
            compared = added = 0
            for family in receipt["families"].values():
                for row in family["placements"]:
                    value = by_id[row["position_id"]]
                    for component in row["components"]:
                        name = component["source_name"]
                        fixing = host.namespace["_CC_FIXING_NAMES"]
                        frame = (value.fixing_frames[fixing.index(name) // 4]
                                 if name in fixing else value)
                        for field in ("origin_mm", "x_axis", "y_axis"):
                            self.assertEqual(component[field],
                                             getattr(frame, field))
                        compared += 1
                        added += value.position_id in {
                            r["position_id"] for r in expected()["positions"]
                        }
            self.assertEqual(compared, total)
            self.assertEqual(added, 57)
            self.assertEqual(receipt["families"]["S1J"]["run"], "basic-04")
            self.assertEqual(receipt["families"]["S1J"]["source_model_sha256"],
                             S1J_SHA)
            self.assertEqual(len(receipt["families"]["S1J"]
                                 ["excluded_source_components"]), 1)
            verify(layers)
            with self.assertRaises(ValueError):
                verify(layers[:-1])

    def test_adapter_refuses_missing_extra_wrong_and_blocked_identities(self):
        values = preview(source_case(), include_joint_exit=True)[0][1]
        chosen = next(p for p in values if p.family == "S1J")
        blocked = replace(chosen, position_id=BLOCKED,
                          fixing_frames=tuple(replace(f, position_id=BLOCKED)
                                              for f in chosen.fixing_frames))
        for bad in (values[:-1], values + (chosen,), values + (blocked,),
                    tuple(replace(p, family="S1") if p is chosen else p
                          for p in values)):
            host = boundary()
            with self.assertRaises(ValueError):
                adapter(host, bad, include_joint_exit=True)
            host.materialise.assert_not_called()
        host = boundary()
        with self.assertRaises(ValueError):
            adapter(host, values)
        host.materialise.assert_not_called()

    def test_strict_boolean_before_all_three_boundaries(self):
        method = getattr(transition_workflow.ModularCoreLayoutWorkflowSession,
                         METHOD)
        for bad in (None, 0, 1, "true", (), [], object()):
            create = Mock()
            with self.subTest(value=repr(bad)):
                with self.assertRaises(ValueError):
                    preview(source_case(), create, include_joint_exit=bad)
                create.assert_not_called()
                host = boundary()
                with self.assertRaises(ValueError):
                    adapter(host, (), include_joint_exit=bad)
                host.materialise.assert_not_called()
                session = SimpleNamespace(routing_record=Mock())
                with self.assertRaises(ValueError):
                    method(session, None, "TO-001", "catalogue.json",
                           include_joint_exit=bad)
                session.routing_record.assert_not_called()

    def test_session_forwards_only_true_in_all_eight_modes(self):
        from validate_phase9b_l1_reference_preview import _session

        session = _session()
        setattr(session, "_" + FACTORY, object())
        for r2 in (False, True):
            for tail in (False, True):
                for joint in (False, True):
                    options = dict(include_r2_exit=r2,
                                   include_crossing_tail=tail,
                                   include_joint_exit=joint)
                    with patch.object(binding(), METHOD,
                                      return_value="receipt") as call:
                        self.assertEqual(getattr(session, METHOD)(
                            "document", "TO-001", "catalogue.json", **options
                        ), "receipt")
                        self.assertEqual(call.call_args.kwargs,
                                         {k: True for k, v in options.items()
                                          if v})

    def test_source_identity_raw_labels_ownership_and_currentness(self):
        changes = dict(
            chair_code_label="S1J", chair_code=True,
            chair_family="joint chair", parent_turnout_identity="TO-002",
            parent_crossover_identity="XO-001", handedness="Right-hand",
            assignment_complete_in_current_stage=True,
            special_assignment_deferred=False, stale_signature_state=True,
            source_configuration={}, rail_identity="wrong",
            timber_identity="wrong", key_direction_sign=1,
        )
        for index in range(3):
            for field, value in changes.items():
                with self.subTest(index=index, field=field):
                    source = source_case()
                    joint_records(source)[index][field] = value
                    self.refuse(source)

    def test_missing_duplicate_exclusion_and_host_source_changes(self):
        for kind in ("missing", "duplicate", "exclusion", "rail-owner",
                     "timber-owner", "station", "host", "nonfinite"):
            with self.subTest(kind=kind):
                source = source_case()
                row = joint_records(source)[-1]
                positions = source.context[2]["positions"]
                timber = next(t for t in source.context[5]
                              if t["stable_identity"] == row["timber_identity"])
                if kind == "missing":
                    positions.remove(row)
                elif kind == "duplicate":
                    positions.append(copy.deepcopy(row))
                elif kind == "exclusion":
                    next(p for p in source.plan["analytical_only"]
                         if p["chair_position_identity"]
                         == row["stable_chair_position_identity"])["chair_label"] = "S1J"
                elif kind == "rail-owner":
                    next(r for r in source.context[4] if r["stable_identity"]
                         == row["rail_identity"])["parent_turnout_identity"] = "TO-002"
                elif kind == "timber-owner":
                    timber["crossover_identity"] = "XO-001"
                elif kind == "station":
                    timber["source_configuration"]["local_x"] += 1
                elif kind == "host":
                    timber["centre"][0] += 1
                else:
                    timber["local_rail_heading_radians"] = math.inf
                self.refuse(source)

    def test_strict_finite_support_at_all_three_selected_positions(self):
        for index in range(3):
            for kind in ("outside", "boundary", "finite-end",
                         "missing-outer", "nonfinite", "boolean"):
                with self.subTest(index=index, kind=kind):
                    source = source_case()
                    row = joint_records(source)[index]
                    timber = next(t for t in source.context[5]
                                  if t["stable_identity"] == row["timber_identity"])
                    rail = next(r for r in source.context[4]
                                if r["stable_identity"] == row["rail_identity"])
                    if kind in ("outside", "boundary"):
                        row["centre_point"] = ([1000, 1000] if kind == "outside"
                                               else timber["outline_polygon"][0])
                    elif kind == "finite-end":
                        rail["points"] = [[700, 487], [790, 487]]
                    elif kind == "missing-outer":
                        rail["outer_face_points"] = []
                    else:
                        rail["points"][0][0] = math.nan if kind == "nonfinite" else True
                    self.refuse(source)

    def test_joint_check_wing_and_gap_predicates_remain_explicit(self):
        for field, value in (("a_timber_x", 300),
                             ("check_main_end_x", 500),
                             ("wing_end_main_x", 500),
                             ("wing_flare_turnout_x", 500),
                             ("flare_angle", math.nan)):
            with self.subTest(field=field):
                source = source_case()
                source.module.rea_c10_dimensions()[field] = value
                self.refuse(source)
        source = source_case()
        source.module._rea_c10_inner_gauge_face = lambda _d, x: (x, 18, 0.1)
        self.refuse(source)

    def test_s1j_catalogue_context_model_names_and_fixing_order_are_bound(self):
        for field, bad in (("run", "existing-02"), ("context", "wrong"),
                           ("model_sha256", "wrong"), ("label", "S1"),
                           ("components", ())):
            def changed(path, family, *, run):
                item = catalogue(path, family, run=run)
                if family == "S1J":
                    setattr(item, field, bad)
                return item

            with self.subTest(field=field):
                self.refuse(source_case(), select=changed)
        values = preview(source_case(), include_joint_exit=True)[0][1]
        for kind in ("run", "context", "hash", "order"):
            host = boundary()
            item = host.selections["S1J"]
            if kind == "order":
                item.components = item.components[::-1]
            else:
                setattr(item, "model_sha256" if kind == "hash" else kind,
                        "wrong")
            with self.assertRaises(ValueError):
                adapter(host, values, include_joint_exit=True)
            host.materialise.assert_not_called()

    def test_late_source_host_and_catalogue_changes_preserve_failure(self):
        for kind in ("source", "host"):
            source = source_case()

            def create(_path, _values, _shapes, _receipt, verify, **_kwargs):
                if kind == "source":
                    joint_records(source)[0]["stale_signature_state"] = True
                else:
                    source.host_data["points"][-1].x += 1
                verify()

            with self.subTest(kind=kind), self.assertRaises(ValueError):
                preview(source, create, include_joint_exit=True)
        values = preview(source_case(), include_joint_exit=True)[0][1]
        host = boundary()
        made = adapter(host, values, include_joint_exit=True)
        host.catalogue_check.side_effect = ValueError("changed S1J catalogue")
        with self.assertRaisesRegex(ValueError, "changed S1J"):
            made.verify()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(JointExitTests)
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
