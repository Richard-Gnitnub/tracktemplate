"""Check eight source-qualified TO chairs without FreeCAD or Qt.

The fixture copies independent 556b frames. Synthetic finite polylines and
rectangles exercise admission only; they do not establish physical fit.
Source-informed metadata is GPL-3.0-or-later; see NOTICE.md.
"""

import copy
from dataclasses import asdict, replace
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
from tracktemplate.domain.turnout import rea_c10_dimensions  # noqa: E402
from validate_phase9b_turnout_r2_exit import (  # noqa: E402
    adapter,
    expected as r2_expected,
    fixture,
    preview,
    r2_inputs,
    source_case as r2_source_case,
)
from validate_phase9b_turnout_single_rail import binding  # noqa: E402
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary,
    FACTORY,
    METHOD,
)

SENTINEL = "Phase 9B TO-001 crossing-tail standalone validation passed"
FRAME_SHA = "b375ed2446c815e3988da128dc54520184f8b746cda3b32fe744035f79d3ccd4"
BASELINE_SHA = (
    "407040d01dd0f9c8ac275d7e4d40c928ea32a5da0a05c853bf3a1de4221a8d4b"
)
PREDECESSOR_SHA = (
    "94187f756efc28563bd94f27eee5bfa494b0992084974b9445ac8441df534663",
    "2b25ae24f4cc2277045f44ac257f65eed13689ec52dd9ad52a78b8101c78c791",
)


def expected():
    return fixture("phase9b-to-crossing-tail-source-frames.json", FRAME_SHA)


def source_case():
    """Reuse fixed-source doubles with independent frames and invented spans."""
    source = r2_source_case()
    analysis, rails, timbers = (
        source.context[2],
        source.context[4],
        source.context[5],
    )
    dimensions = rea_c10_dimensions(16.5, 1.0, 76.2)
    dimensions.update(source.module.rea_c10_dimensions())
    source.module.rea_c10_dimensions = lambda *_args: dimensions
    template = r2_inputs()["positions"][0]
    old_interpolate = source.module.interpolate_alignment_station
    stations = {}
    for index, row in enumerate(expected()["positions"], 14):
        name = row["timber_id"].split(":")[-1]
        rail = next(r for r in rails if r["stable_identity"] == row["rail_id"])
        rail_name = rail["name"]
        # These spans and centres are deliberately invented admission inputs.
        for field in ("points", "gauge_face_points", "outer_face_points"):
            rail[field] = [[800, 487], [920, 487]]
        point = row["host_basis"]["host_point_mm"]
        heading = row["host_basis"]["heading_radians"]
        station = row["host_basis"]["host_station_mm"]
        stations[station] = (SimpleNamespace(x=point[0], y=point[1]), heading)
        timber = next((t for t in timbers if t["identifier"] == name), None)
        if timber is None:
            timber_source = dict(
                local_x=row["source_station_mm"],
                local_near_y=-16.0,
                local_far_y=20.0,
                length_prototype_inches=108.0,
                turnout_geometry_revision=2,
                crossing_suffix=name[-1],
            )
            timber = dict(
                stable_identity=row["timber_id"],
                identifier=name,
                parent_turnout_identity="TO-001",
                crossover_identity="",
                source_configuration=timber_source,
                host_chainage=station,
                local_rail_heading_radians=heading,
                centre=[
                    point[0] - 2 * math.sin(heading),
                    point[1] + 2 * math.cos(heading),
                ],
                outline_polygon=[
                    [800, 400],
                    [920, 400],
                    [920, 520],
                    [800, 520],
                ],
            )
            timbers.append(timber)
            source.layout.append(
                dict(
                    identifier=name,
                    x=timber_source["local_x"],
                    near_y=-16.0,
                    far_y=20.0,
                    length_prototype_inches=108.0,
                )
            )
        record = copy.deepcopy(template)
        record.update(
            stable_chair_position_identity=row["position_id"],
            rail_identity=row["rail_id"],
            rail_name=rail_name,
            rail_role="stock rail"
            if row["source_rail_code"] in (1, 4)
            else rail_name,
            timber_identity=row["timber_id"],
            prototype_timber_identifier=name,
            timber_identifier=name,
            chair_code=row["raw_code"],
            chair_code_label=row["raw_label"],
            chair_family=(
                "common-crossing chair"
                if name != "X9-F"
                else "splice-rail support"
                if row["source_rail_code"] == 2
                else "vee support"
            ),
            source_configuration={
                "rail": rail["source_configuration"],
                "timber": timber["source_configuration"],
            },
            centre_point=[870, 487],
        )
        old_id = f"invented-unselected-{index:03d}"
        slot = next(
            i
            for i, p in enumerate(analysis["positions"])
            if p["stable_chair_position_identity"] == old_id
        )
        analysis["positions"][slot] = record
        original = next(
            p
            for p in source.plan["analytical_only"]
            if p["chair_position_identity"] == old_id
        )
        original.update(
            chair_position_identity=row["position_id"],
            rail_identity=row["rail_id"],
            timber_identity=row["timber_id"],
            chair_label=row["raw_label"],
            chair_family=record["chair_family"],
            deliberate_omission=False,
            unresolved_special=True,
            reason="special chair assignment remains analytical",
        )
    source.module.interpolate_alignment_station = lambda data, station: (
        stations[station]
        if station in stations
        else old_interpolate(data, station)
    )
    return source


def observable(args):
    """Encode stable output bytes, excluding callback and shape identities."""
    return json.dumps(
        {"placements": [asdict(p) for p in args[1]], "receipt": args[3]},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def tail_records(source):
    ids = {row["position_id"] for row in expected()["positions"]}
    return [
        p
        for p in source.context[2]["positions"]
        if p["stable_chair_position_identity"] in ids
    ]


class CrossingTailTests(unittest.TestCase):
    def near(self, actual, frozen):
        self.assertEqual(len(actual), len(frozen))
        for a, b in zip(actual, frozen):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def test_default_and_r2_only_preserve_predecessor_bytes(self):
        source = source_case()
        for r2 in (False, True):
            options = {"include_r2_exit": True} if r2 else {}
            args, forwarded = preview(source, **options)
            explicit, kw = preview(
                source, include_crossing_tail=False, **options
            )
            self.assertEqual(forwarded, options)
            self.assertEqual(kw, options)
            self.assertEqual(observable(args), observable(explicit))
            self.assertEqual(
                hashlib.sha256(observable(args)).hexdigest(),
                PREDECESSOR_SHA[r2],
            )
            self.assertEqual(len(args[1]), 14 if r2 else 12)

    def test_exact_twenty_and_twenty_two_with_all_independent_frames(self):
        baseline = fixture("phase9b-to-single-rail-frames.json", BASELINE_SHA)
        for r2, count, frames, components in (
            (False, 20, 93, 418),
            (True, 22, 101, 452),
        ):
            with self.subTest(r2=r2):
                source = source_case()
                before = copy.deepcopy((source.context, source.plan))
                options = dict(include_crossing_tail=True)
                if r2:
                    options["include_r2_exit"] = True
                args, kw = preview(source, **options)
                self.assertEqual(kw, options)
                placements, receipt = args[1], args[3]
                wanted = {
                    r["position_id"]: r
                    for r in baseline["positions"]
                    + expected()["positions"]
                    + (r2_expected()["positions"] if r2 else [])
                }
                self.assertEqual(
                    {p.position_id for p in placements}, set(wanted)
                )
                self.assertEqual(len(placements), count)
                self.assertEqual(
                    receipt["selected_family_counts"],
                    {"L1": 13, "S1": 9 if r2 else 7},
                )
                self.assertEqual(
                    receipt["represented_source_position_count"], count
                )
                self.assertEqual(
                    len(receipt["remaining_positions"]), 168 - count
                )
                old_heel = preview(source)[0][3]["corrected_heel_positions"]
                self.assertEqual(receipt["corrected_heel_positions"], old_heel)
                self.assertEqual(len(old_heel), 5)
                compared = 0
                for p in placements:
                    row = wanted[p.position_id]
                    self.assertEqual(
                        len(p.fixing_frames), len(row["fixing_frames"])
                    )
                    for value, frozen in zip(
                        (p,) + p.fixing_frames,
                        [row["body"]] + row["fixing_frames"],
                    ):
                        for field in ("origin_mm", "x_axis", "y_axis"):
                            self.near(getattr(value, field), frozen[field])
                        compared += 1
                self.assertEqual(compared, frames)
                self.assertEqual(
                    sum(23 if p.family == "L1" else 17 for p in placements),
                    components,
                )
                self.assertEqual((source.context, source.plan), before)

    def test_adapter_materialises_exact_components_and_indexed_frames(self):
        for r2, count in ((False, 418), (True, 452)):
            options = dict(include_crossing_tail=True, include_r2_exit=r2)
            values = preview(source_case(), **options)[0][1]
            boundary = AdapterBoundary()
            result = adapter(boundary, values, **options)
            layers, receipt, verify = result.prepare()
            self.assertEqual(len(layers), 42)
            self.assertEqual(receipt["component_count"], 40)
            self.assertEqual(receipt["placement_count"], 22 if r2 else 20)
            self.assertEqual(sum(len(s.children) for s in layers[2:]), count)
            by_id = {p.position_id: p for p in values}
            transformed = 0
            for family in receipt["families"].values():
                for row in family["placements"]:
                    placement = by_id[row["position_id"]]
                    for component in row["components"]:
                        name = component["source_name"]
                        fixing = boundary.namespace["_CC_FIXING_NAMES"]
                        frame = (
                            placement.fixing_frames[fixing.index(name) // 4]
                            if name in fixing
                            else placement
                        )
                        for field in ("origin_mm", "x_axis", "y_axis"):
                            self.assertEqual(
                                component[field], getattr(frame, field)
                            )
                        transformed += 1
            self.assertEqual(transformed, count)
            verify(layers)
            with self.assertRaises(ValueError):
                verify(layers[:-1])

    def test_adapter_refuses_missing_duplicate_surplus_and_wrong_identity(
        self,
    ):
        values = preview(source_case(), include_crossing_tail=True)[0][1]
        chosen = next(p for p in values if ":X9-F" in p.timber_id)
        for bad in (
            values[:-1],
            values + (chosen,),
            values[2:],
            tuple(
                replace(p, family="S1", fixing_frames=p.fixing_frames[:3])
                if p is chosen
                else p
                for p in values
            ),
            tuple(
                replace(
                    p,
                    rail_id="TO-002:rail:vee-point-rail",
                    fixing_frames=tuple(
                        replace(f, rail_id="TO-002:rail:vee-point-rail")
                        for f in p.fixing_frames
                    ),
                )
                if p is chosen
                else p
                for p in values
            ),
        ):
            boundary = AdapterBoundary()
            with self.assertRaises(ValueError):
                adapter(boundary, bad, include_crossing_tail=True)
            boundary.materialise.assert_not_called()
        boundary = AdapterBoundary()
        with self.assertRaises(ValueError):
            adapter(boundary, values)
        boundary.materialise.assert_not_called()

    def test_flags_are_actual_booleans_before_all_three_boundaries(self):
        for bad in (None, 0, 1, "true", (), [], object()):
            create = Mock()
            with self.subTest(value=repr(bad)):
                with self.assertRaises(ValueError):
                    preview(source_case(), create, include_crossing_tail=bad)
                create.assert_not_called()
                boundary = AdapterBoundary()
                with self.assertRaises(ValueError):
                    adapter(boundary, (), include_crossing_tail=bad)
                boundary.materialise.assert_not_called()
                session = SimpleNamespace(routing_record=Mock())
                method = getattr(
                    transition_workflow.ModularCoreLayoutWorkflowSession,
                    METHOD,
                )
                with self.assertRaises(ValueError):
                    method(
                        session,
                        None,
                        "TO-001",
                        "catalogue.json",
                        include_crossing_tail=bad,
                    )
                session.routing_record.assert_not_called()

    def test_session_forwards_only_true_options_in_all_four_modes(self):
        from validate_phase9b_l1_reference_preview import _session

        session = _session()
        setattr(session, "_" + FACTORY, object())
        for r2 in (False, True):
            for tail in (False, True):
                options = dict(include_r2_exit=r2, include_crossing_tail=tail)
                wanted = {key: True for key, value in options.items() if value}
                with patch.object(
                    binding(), METHOD, return_value="receipt"
                ) as call:
                    self.assertEqual(
                        getattr(session, METHOD)(
                            "document", "TO-001", "catalogue.json", **options
                        ),
                        "receipt",
                    )
                    self.assertEqual(call.call_args.kwargs, wanted)

    def test_raw_labels_flags_identity_and_ownership_refuse_before_mutation(
        self,
    ):
        changes = dict(
            chair_code_label="S1",
            chair_code=True,
            chair_family="bridge chair",
            parent_turnout_identity="TO-002",
            parent_crossover_identity="XO-001",
            rail_identity="TO-001:rail:straight-switch-and-closure-rail",
            timber_identity="TO-001:timber:R2",
            handedness="Right-hand",
            assignment_complete_in_current_stage=True,
            special_assignment_deferred=False,
            stale_signature_state=True,
            source_configuration={},
            source_or_assumed_classification="unknown",
        )
        for row_index in range(8):
            for field, value in changes.items():
                with self.subTest(row=row_index, field=field):
                    source = source_case()
                    tail_records(source)[row_index][field] = value
                    create = Mock()
                    with self.assertRaises(ValueError):
                        preview(source, create, include_crossing_tail=True)
                    create.assert_not_called()

    def test_missing_duplicate_exclusion_and_source_host_changes_refuse(self):
        for kind in (
            "missing",
            "duplicate",
            "exclusion",
            "rail-owner",
            "timber-owner",
            "source",
            "host",
            "outside-host",
            "late-host",
        ):
            with self.subTest(kind=kind):
                source = source_case()
                row = tail_records(source)[0]
                positions = source.context[2]["positions"]
                timber = next(
                    t
                    for t in source.context[5]
                    if t["stable_identity"] == row["timber_identity"]
                )
                if kind == "missing":
                    positions.remove(row)
                elif kind == "duplicate":
                    positions.append(copy.deepcopy(row))
                elif kind == "exclusion":
                    next(
                        p
                        for p in source.plan["analytical_only"]
                        if p["chair_position_identity"]
                        == row["stable_chair_position_identity"]
                    )["chair_label"] = "S1"
                elif kind == "rail-owner":
                    next(
                        r
                        for r in source.context[4]
                        if r["stable_identity"] == row["rail_identity"]
                    )["parent_turnout_identity"] = "TO-002"
                elif kind == "timber-owner":
                    timber["crossover_identity"] = "XO-001"
                elif kind == "source":
                    timber["source_configuration"]["local_x"] += 1
                elif kind == "host":
                    timber["centre"][0] += 1
                elif kind == "outside-host":
                    source.module.turnout_host_alignment(None)["total"] = 1000
                if kind == "late-host":
                    args, _ = preview(source, include_crossing_tail=True)
                    source.module.turnout_host_alignment(None)["points"][
                        0
                    ].x += 1
                    with self.assertRaises(ValueError):
                        args[4]()
                else:
                    create = Mock()
                    with self.assertRaises(ValueError):
                        preview(source, create, include_crossing_tail=True)
                    create.assert_not_called()

    def test_finite_support_requires_real_interior_at_each_tail_position(self):
        for row_index in range(8):
            for kind in (
                "outside",
                "boundary",
                "finite-end",
                "missing-outer",
                "nonfinite",
                "boolean",
                "repeated",
                "self-crossing",
            ):
                with self.subTest(row=row_index, kind=kind):
                    source = source_case()
                    row = tail_records(source)[row_index]
                    timber = next(
                        t
                        for t in source.context[5]
                        if t["stable_identity"] == row["timber_identity"]
                    )
                    rail = next(
                        r
                        for r in source.context[4]
                        if r["stable_identity"] == row["rail_identity"]
                    )
                    if kind in ("outside", "boundary"):
                        row["centre_point"] = (
                            [0, 0]
                            if kind == "outside"
                            else timber["outline_polygon"][0]
                        )
                    elif kind == "finite-end":
                        rail["points"] = [[700, 487], [790, 487]]
                    elif kind == "missing-outer":
                        rail["outer_face_points"] = []
                    elif kind in ("nonfinite", "boolean"):
                        rail["points"][0][0] = (
                            float("nan") if kind == "nonfinite" else True
                        )
                    elif kind == "repeated":
                        timber["outline_polygon"] = [[0, 0]] * 4
                    else:
                        polygon = timber["outline_polygon"]
                        polygon[1], polygon[2] = polygon[2], polygon[1]
                    create = Mock()
                    with self.assertRaises(ValueError):
                        preview(source, create, include_crossing_tail=True)
                    create.assert_not_called()

    def test_check_end_joint_wing_and_gap_domains_remain_explicit(self):
        for field in (
            "check_main_end_x",
            "check_turnout_end_x",
            "wing_end_main_x",
            "wing_flare_turnout_x",
            "a_timber_x",
        ):
            with self.subTest(field=field):
                source = source_case()
                dimensions = source.module.rea_c10_dimensions()
                dimensions[field] = 300.0 if field == "a_timber_x" else 500.0
                create = Mock()
                with self.assertRaises(ValueError):
                    preview(source, create, include_crossing_tail=True)
                create.assert_not_called()
        source = source_case()
        source.module._rea_c10_inner_gauge_face = lambda _d, x: (
            x,
            18,
            0.09966865249116202,
        )
        create = Mock()
        with self.assertRaises(ValueError):
            preview(source, create, include_crossing_tail=True)
        create.assert_not_called()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CrossingTailTests)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
