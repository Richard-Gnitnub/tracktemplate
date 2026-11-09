"""Check fixed LH turnout-side CC admission without native execution.

The reviewed numeric fixture supplies all fifteen expected frames. Existing
host/catalogue/shape doubles exercise admission and component routing only.
They do not establish native geometry, display, fit, rights or phase exit.
Source-informed comparison metadata is GPL-3.0-or-later; see NOTICE.md.

Baseline values were captured on untouched integrated product before the
first implementation edit. Structural extraction checks are separate ignored
evidence; retained tests assert observable behavior.
"""

import ast
import copy
from dataclasses import asdict, FrozenInstanceError, replace
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
from tracktemplate.domain import central_check_placement as central  # noqa: E402
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    S1JPlacement,
    S1Placement,
)
from tracktemplate.domain.turnout import rea_c10_dimensions  # noqa: E402
from validate_phase9b_turnout_central_cc import (  # noqa: E402
    CC_CONTEXT_SHA256,
    CC_MODEL_SHA256,
    FIXING_NAMES,
    STATIONS,
    TIMBERS,
    catalogue_selection,
    placement_binding,
    position_id,
    selected_timber,
    source_case as main_source_case,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary,
    ShapeDouble,
)

SENTINEL = "Phase 9B TO-001 turnout-side central CC validation passed"
FRAME_SHA = "033292c8c1f56dd6f52fc8c3cdee0f2c751aec973ba0b67ea2dd9cca0307e5f9"
METHOD = "preview_private_catalogue_turnout_cc_chairs"
FACTORY = "create_private_catalogue_cc_preview"
# Complete observable outputs captured on untouched integrated 162c3e34.
BASELINE_SHA = (
    "c9b4f222fef5e02a937dc30a81c4d63daeed4ab527e5496b9fc5935c3256b699"
)
RH_BASELINE_SHA = (
    "28abdc0a221214229bb71e3e7458c0374e167a0376731eb75a64adaf64ca66aa"
)


def expected():
    path = (
        ROOT
        / "tests/fixtures/phase9b-to-central-cc-turnout-side-source-frames.json"
    )
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FRAME_SHA
    return json.loads(data)


def source_case():
    """Extend existing doubles; invented finite spans supply no expected frame."""
    source = main_source_case()
    analysis, rails = source.context[2], source.context[4]
    dimensions = rea_c10_dimensions(16.5, 1.0, 76.2)
    dimensions["a_timber_x"] = STATIONS[2]
    source.module.rea_c10_dimensions = lambda *_args: dimensions
    poses = {r["source_station_mm"]: r for r in expected()["positions"]}
    source.module._rea_c10_turnout_outer_gauge_point_at_x = (
        lambda _dimensions, x: (
            x,
            poses[x]["source_gauge_y_mm"] - 8.25,
            math.atan(0.1),
        )
    )
    host_frames = {}
    old_interpolate = source.module.interpolate_alignment_station
    ts_rails = {}
    for rail_name, role in (
        ("turnout-side stock rail", "stock rail"),
        ("turnout-side check rail", "check rail"),
    ):
        identity = "TO-001:rail:" + rail_name.replace(" ", "-")
        rail = next(
            (r for r in rails if r["stable_identity"] == identity), None
        )
        if rail is None:
            rail = {"stable_identity": identity}
            rails.append(rail)
        rail.update(
            name=rail_name,
            rail_role=role,
            parent_turnout_identity="TO-001",
            parent_crossover_identity="",
            turnout_side="",
            source_configuration={
                "gauge_face": rail_name + " gauge face",
                "outer_face": rail_name + " outer face",
                "gauge_orientation_source": "mapped named turnout rail faces",
                "rail_geometry_revision": 2,
            },
        )
        # Deliberately synthetic finite lines; real18-vertex support is a
        # separate ignored retained-context proof, never this fixture.
        for field in ("gauge_face_points", "points", "outer_face_points"):
            rail[field] = [[790.0, 420.0], [910.0, 420.0]]
        ts_rails[rail["stable_identity"]] = rail
    for index, row in enumerate(expected()["positions"]):
        name = row["timber_id"].split(":")[-1]
        timber = selected_timber(source, name)
        basis = row["host_basis"]
        point = basis["host_point_mm"]
        heading = basis["heading_radians"]
        host_frames[basis["host_station_mm"]] = (
            SimpleNamespace(x=point[0], y=point[1]),
            heading,
        )
        nominal = timber["source_configuration"]
        mean_y = (nominal["local_near_y"] + nominal["local_far_y"]) / 2
        timber.update(
            host_chainage=basis["host_station_mm"],
            local_rail_heading_radians=heading,
            centre=[
                point[0] - mean_y * math.sin(heading),
                point[1] + mean_y * math.cos(heading),
            ],
            outline_polygon=[[800, 380], [900, 380], [900, 460], [800, 460]],
        )
        for companion, record_input in enumerate((row, row["companion"])):
            template_id = position_id(name, companion=bool(companion))
            template = next(
                p
                for p in analysis["positions"]
                if p["stable_chair_position_identity"] == template_id
            )
            rail = ts_rails[record_input["rail_id"]]
            position = copy.deepcopy(template)
            position.update(
                stable_chair_position_identity=record_input["position_id"],
                rail_identity=rail["stable_identity"],
                rail_name=rail["name"],
                rail_role=rail["rail_role"],
                chair_code=record_input["raw_code"],
                chair_code_label=record_input["raw_label"],
                source_configuration={
                    "rail": copy.deepcopy(rail["source_configuration"]),
                    "timber": copy.deepcopy(nominal),
                },
                centre_point=[850.0, 420.0],
            )
            old_id = f"invented-unselected-{2 * index + companion:03d}"
            slot = next(
                i
                for i, p in enumerate(analysis["positions"])
                if p["stable_chair_position_identity"] == old_id
            )
            analysis["positions"][slot] = position
            exclusion = next(
                p
                for p in source.plan["analytical_only"]
                if p["chair_position_identity"] == old_id
            )
            exclusion.update(
                chair_position_identity=record_input["position_id"],
                rail_identity=rail["stable_identity"],
                timber_identity=row["timber_id"],
                chair_label=record_input["raw_label"],
                chair_family=position["chair_family"],
                reason="special chair assignment remains analytical",
                deliberate_omission=False,
                unresolved_special=True,
            )
    source.module.interpolate_alignment_station = lambda data, station: (
        host_frames[station]
        if station in host_frames
        else old_interpolate(data, station)
    )
    for record in source.plan["instances"]:
        record["base_z"] = 0.8
    return source


def preview(source, factory=None, *, selection=None, **options):
    command = placement_binding()
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        patch.object(
            command,
            "prepare_catalogue_chair",
            return_value=selection or catalogue_selection(),
        ),
        patch.object(command, "verify_catalogue_sources"),
    ):
        return getattr(command, METHOD)(
            source.module,
            source.document,
            "TO-001",
            "catalogue.json",
            factory or (lambda *args, **kwargs: (args, kwargs)),
            **options,
        )


def observable(args):
    """Include complete placement/receipt/context values, excluding callback identity."""
    return json.dumps(
        {
            "path": args[0],
            "placements": [asdict(p) for p in args[1]],
            "context": [vars(shape) for shape in args[2]],
            "receipt": args[3],
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def arguments(row):
    return dict(
        position_id=row["position_id"],
        rail_id=row["rail_id"],
        timber_id=row["timber_id"],
        host_point_mm=row["host_basis"]["host_point_mm"],
        travel_heading_rad=row["host_basis"]["heading_radians"],
        base_z_mm=row["body"]["origin_mm"][2],
        # Source oracle atan2(1,10) differs in the final binary64 bit.
        # The existing product/source-pose API admits this exact atan token;
        # expected world frames remain the unmodified independent fixture.
        source_angle_rad=math.atan(0.1),
        source_gauge_y_mm=row["source_gauge_y_mm"],
    )


def left_frame(**kwargs):
    return getattr(central, "place_left_hand_central_check")(**kwargs)


def selected_records(source):
    ids = {
        p[key]["position_id"] if key else p["position_id"]
        for p in expected()["positions"]
        for key in (None, "companion")
    }
    return [
        p
        for p in source.context[2]["positions"]
        if p["stable_chair_position_identity"] in ids
    ]


def adapter_boundary():
    """Reuse the existing native-boundary doubles and real selected functions."""
    boundary = AdapterBoundary()
    boundary.namespace.update(
        PairedChairPlacement=PairedChairPlacement,
        S1Placement=S1Placement,
        S1JPlacement=S1JPlacement,
        prepare_central_check_placements=central.prepare_central_check_placements,
    )
    for relative, names in (
        (
            "tracktemplate/adapters/freecad/chair_reference_preview.py",
            {"_placements"},
        ),
        (
            "tracktemplate/adapters/freecad/chair_catalogue_placement_preview.py",
            {FACTORY, "_create_private_catalogue_preview"},
        ),
    ):
        path = ROOT / relative
        nodes = [
            n
            for n in ast.parse(path.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name in names
        ]
        assert {n.name for n in nodes} == names
        exec(
            compile(
                ast.Module(body=nodes, type_ignores=[]), str(path), "exec"
            ),
            boundary.namespace,
        )
    selection = catalogue_selection()
    for component in selection.components:
        component.label = component.name
    selection.catalogue_sha256 = "invented-catalogue"
    selection.model_path = "invented-model"
    selection.bindings, selection.metadata, selection.limitations = (), {}, ()
    boundary.selections["CC"] = selection

    def reader(_path, family, *, run):
        assert family == "CC" and run == "context-native-02"
        return selection

    boundary.namespace["prepare_catalogue_chair"] = Mock(side_effect=reader)
    return boundary


def adapter(boundary, values, receipt, **options):
    return boundary.namespace[FACTORY](
        "catalogue.json",
        values,
        (ShapeDouble(context=True), ShapeDouble(context=True)),
        receipt,
        boundary.source_check,
        **options,
    )


def rh_records():
    """Observe the existing RH contract at two source sides and three headings."""
    return tuple(
        central.place_central_check(
            f"rh-{side}-{index}",
            f"rail-{side}",
            f"timber-{index}",
            (100.0, 200.0),
            heading,
            0.8,
            side=side,
            source_angle_rad=0.0 if side == "MS" else math.atan(0.1),
            source_gauge_y_mm=0.0 if side == "MS" else 32.46656308246101,
        )
        for index, heading in enumerate((0.0, 0.37, math.pi))
        for side in ("MS", "TS")
    )


class TurnoutSideCentralCheckTests(unittest.TestCase):
    def near(self, actual, wanted):
        self.assertEqual(len(actual), len(wanted))
        for a, b in zip(actual, wanted):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def refuse(self, source, *, selection=None):
        create = Mock()
        with self.assertRaises(ValueError):
            preview(
                source, create, selection=selection, include_turnout_side=True
            )
        create.assert_not_called()

    def test_frozen_fixture_has_fifteen_frames_and_six_source_identities(self):
        rows = expected()["positions"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            [r["timber_id"] for r in rows],
            ["TO-001:timber:" + name for name in TIMBERS],
        )
        self.assertEqual(sum(1 + len(r["fixing_frames"]) for r in rows), 15)
        self.assertEqual(
            len(
                {
                    identity
                    for r in rows
                    for identity in (
                        r["position_id"],
                        r["companion"]["position_id"],
                    )
                }
            ),
            6,
        )
        self.assertEqual(
            expected()["provenance"]["model"]["sha256"], CC_MODEL_SHA256
        )
        self.assertEqual(
            expected()["provenance"]["model"]["context_sha256"],
            CC_CONTEXT_SHA256,
        )
        for row in rows:
            self.assertEqual(
                [f["source_index"] for f in row["fixing_frames"]], [1, 2, 3, 4]
            )
            self.assertEqual(row["companion"]["raw_label"], "CC")

    def test_default_and_false_preserve_complete_ms_output_and_five_arguments(
        self,
    ):
        source = source_case()
        old, implicit = preview(source)
        new, explicit = preview(source, include_turnout_side=False)
        self.assertEqual(implicit, {})
        self.assertEqual(explicit, {})
        self.assertEqual(observable(old), observable(new))
        self.assertEqual(
            hashlib.sha256(observable(new)).hexdigest(), BASELINE_SHA
        )
        self.assertEqual(len(new), 5)
        self.assertTrue(all(type(p) is PairedChairPlacement for p in new[1]))
        self.assertEqual(new[3]["selected_cc_count"], 3)
        self.assertEqual(new[3]["represented_source_position_count"], 6)
        self.assertEqual(len(new[3]["remaining_positions"]), 162)

    def test_all_fifteen_independent_lh_source_frames(self):
        count = 0
        for row in expected()["positions"]:
            value = left_frame(**arguments(row))
            self.assertIs(type(value), central.CentralCheckPlacement)
            for actual, wanted in zip(
                (value,) + value.fixing_frames,
                [row["body"]] + row["fixing_frames"],
            ):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(actual, field), wanted[field])
                count += 1
            with self.assertRaises(FrozenInstanceError):
                value.position_id = "changed"
        self.assertEqual(count, 15)

    def test_rigid_host_transforms_and_both_direction_headings(self):
        for row in expected()["positions"]:
            inputs = arguments(row)
            for delta in (math.pi, -0.71, 1.25):
                cosine, sine = math.cos(delta), math.sin(delta)

                def rotate(xy):
                    return (
                        cosine * xy[0] - sine * xy[1],
                        sine * xy[0] + cosine * xy[1],
                    )

                point = rotate(inputs["host_point_mm"])
                values = dict(
                    inputs,
                    host_point_mm=(point[0] + 31, point[1] - 29),
                    travel_heading_rad=inputs["travel_heading_rad"] + delta,
                )
                actual = left_frame(**values)
                for frame, original in zip(
                    (actual,) + actual.fixing_frames,
                    [row["body"]] + row["fixing_frames"],
                ):
                    origin = rotate(original["origin_mm"])
                    self.near(
                        frame.origin_mm,
                        (
                            origin[0] + 31,
                            origin[1] - 29,
                            original["origin_mm"][2],
                        ),
                    )
                    self.near(frame.x_axis, rotate(original["x_axis"]))
                    self.near(frame.y_axis, rotate(original["y_axis"]))

    def test_pose_numeric_and_nested_frame_refusals(self):
        inputs = arguments(expected()["positions"][0])
        for field, value in (
            ("source_angle_rad", 0),
            ("source_angle_rad", True),
            ("source_angle_rad", math.nan),
            ("source_angle_rad", math.inf),
            ("source_gauge_y_mm", 0),
            ("source_gauge_y_mm", -1),
            ("source_gauge_y_mm", False),
            ("source_gauge_y_mm", math.nan),
            ("base_z_mm", math.inf),
            ("base_z_mm", True),
            ("travel_heading_rad", math.nan),
            ("host_point_mm", (0, math.inf)),
            ("host_point_mm", (False, 0)),
            ("source_angle_rad", 10**400),
        ):
            with (
                self.subTest(field=field, value=value),
                self.assertRaises(ValueError),
            ):
                left_frame(**dict(inputs, **{field: value}))
        frame = left_frame(**inputs)
        for field, value in (
            ("origin_mm", (math.nan, 0, 0)),
            ("x_axis", (2, 0)),
            ("y_axis", (0, -1)),
            ("position_id", "another"),
        ):
            damaged = copy.deepcopy(frame)
            object.__setattr__(damaged.fixing_frames[0], field, value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                central.prepare_central_check_placements((damaged,))
        for values in ((), [frame], (frame, frame)):
            with self.assertRaises(ValueError):
                central.prepare_central_check_placements(values)

    def test_options_are_actual_booleans_at_all_three_boundaries(self):
        command = placement_binding()
        for value in (None, 0, 1, "true", (), [], {}):
            with self.subTest(value=value):
                reader = Mock(side_effect=AssertionError("source was read"))
                with patch.object(command, "_open_source_context", reader):
                    with self.assertRaises(ValueError):
                        getattr(command, METHOD)(
                            object(),
                            object(),
                            "TO-001",
                            "unused",
                            Mock(),
                            include_turnout_side=value,
                        )
                reader.assert_not_called()
                session = SimpleNamespace(routing_record=Mock())
                with self.assertRaises(ValueError):
                    getattr(
                        transition_workflow.ModularCoreLayoutWorkflowSession,
                        METHOD,
                    )(
                        session,
                        object(),
                        "TO-001",
                        "unused",
                        include_turnout_side=value,
                    )
                session.routing_record.assert_not_called()
                boundary = adapter_boundary()
                with self.assertRaises(ValueError):
                    adapter(boundary, object(), {}, include_turnout_side=value)
                boundary.namespace[
                    "prepare_catalogue_chair"
                ].assert_not_called()
                boundary.materialise.assert_not_called()

    def test_combined_six_assemblies_and_source_partition_are_preserved(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        baseline = preview(source)[0]
        args, forwarded = preview(source, include_turnout_side=True)
        placements, receipt = args[1], args[3]
        self.assertEqual(forwarded, {"include_turnout_side": True})
        self.assertEqual(len(placements), 6)
        self.assertEqual(
            [p.position_id for p in placements],
            sorted(p.position_id for p in placements),
        )
        self.assertTrue(
            all(type(p) is central.CentralCheckPlacement for p in placements)
        )
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["selected_cc_count"], 6)
        self.assertEqual(receipt["represented_source_position_count"], 12)
        self.assertEqual(len(receipt["shared_supports"]), 6)
        self.assertEqual(len(receipt["remaining_positions"]), 156)
        self.assertEqual(
            receipt["original_analytical_exclusions"],
            before[1]["analytical_only"],
        )
        self.assertEqual((source.context, source.plan), before)
        by_id = {p.position_id: p for p in placements}
        for original in baseline[1]:
            value = by_id[original.position_id]
            for frame in (value,) + value.fixing_frames:
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.assertEqual(
                        getattr(frame, field), getattr(original, field)
                    )
        for row in expected()["positions"]:
            value = by_id[row["position_id"]]
            for frame, frozen in zip(
                (value,) + value.fixing_frames,
                [row["body"]] + row["fixing_frames"],
            ):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(frame, field), frozen[field])
        self.assertEqual(
            {
                r["position_id"]: r["assembly_position_id"]
                for r in receipt["shared_supports"]
            },
            {
                **{
                    position_id(name, companion=True): position_id(name)
                    for name in TIMBERS
                },
                **{
                    r["companion"]["position_id"]: r["position_id"]
                    for r in expected()["positions"]
                },
            },
        )

    def test_each_new_source_identity_and_raw_assignment_is_binding(self):
        for index in range(6):
            for field, value in (
                ("parent_turnout_identity", "TO-002"),
                ("parent_crossover_identity", "XO-001"),
                ("rail_identity", "unknown"),
                ("timber_identity", "other"),
                ("chair_code", True),
                ("chair_code_label", "S1"),
                ("assignment_complete_in_current_stage", True),
                ("special_assignment_deferred", False),
                ("stale_signature_state", True),
                ("handedness", "Right-hand"),
            ):
                source = source_case()
                selected_records(source)[index][field] = value
                with self.subTest(index=index, field=field):
                    self.refuse(source)
        for kind in ("rail-owner", "rail-source", "timber-owner", "exclusion"):
            source = source_case()
            position = selected_records(source)[0]
            rail = next(
                r
                for r in source.context[4]
                if r["stable_identity"] == position["rail_identity"]
            )
            if kind == "rail-owner":
                rail["parent_turnout_identity"] = "Other"
            elif kind == "rail-source":
                rail["source_configuration"]["rail_geometry_revision"] = 3
            elif kind == "timber-owner":
                selected_timber(source)["parent_turnout_identity"] = "Other"
            else:
                next(
                    r
                    for r in source.plan["analytical_only"]
                    if r["chair_position_identity"]
                    == position["stable_chair_position_identity"]
                )["reason"] = "unknown"
            with self.subTest(kind=kind):
                self.refuse(source)

    def test_missing_duplicate_extra_and_partial_pair_are_refused(self):
        for index in range(6):
            for change in ("missing", "duplicate", "extra", "exclusion"):
                source = source_case()
                record = selected_records(source)[index]
                if change == "missing":
                    source.context[2]["positions"].remove(record)
                elif change == "duplicate":
                    source.context[2]["positions"].append(
                        copy.deepcopy(record)
                    )
                elif change == "extra":
                    record["stable_chair_position_identity"] += "-extra"
                else:
                    source.plan["analytical_only"][:] = [
                        p
                        for p in source.plan["analytical_only"]
                        if p["chair_position_identity"]
                        != record["stable_chair_position_identity"]
                    ]
                with self.subTest(index=index, change=change):
                    self.refuse(source)

    def test_catalogue_model_context_and_component_index_are_binding(self):
        for field, value in (
            ("label", "CCL"),
            ("run", "other"),
            ("model_sha256", "0" * 64),
            ("context", {"context_sha256": "0" * 64}),
            ("components", ()),
        ):
            selection = catalogue_selection()
            setattr(selection, field, value)
            with self.subTest(field=field):
                self.refuse(source_case(), selection=selection)
        args = preview(source_case(), include_turnout_side=True)[0]
        for change in ("missing", "fixing-order"):
            boundary = adapter_boundary()
            item = boundary.selections["CC"]
            if change == "missing":
                item.components = item.components[:-1]
            else:
                parts = list(item.components)
                parts[-1], parts[-2] = parts[-2], parts[-1]
                item.components = tuple(parts)
            with self.subTest(change=change), self.assertRaises(ValueError):
                adapter(boundary, args[1], args[3], include_turnout_side=True)
            boundary.materialise.assert_not_called()

    def test_station_source_pose_configuration_and_host_are_binding(self):
        for kind in (
            "station",
            "layout",
            "chainage",
            "heading",
            "centre",
            "host-total",
            "host-point",
            "gauge",
            "angle",
            "lower",
            "upper",
            "configuration",
            "analysis",
        ):
            source = source_case()
            timber = selected_timber(source)
            dimensions = source.module.rea_c10_dimensions()
            if kind == "station":
                timber["source_configuration"]["local_x"] += 1e-6
            elif kind == "layout":
                source.layout[0]["x"] += 1e-6
            elif kind == "chainage":
                timber["host_chainage"] += 1e-6
            elif kind == "heading":
                timber["local_rail_heading_radians"] += 1e-6
            elif kind == "centre":
                timber["centre"][0] += 1e-6
            elif kind == "host-total":
                source.host_data["total"] = math.inf
            elif kind == "host-point":
                source.module.interpolate_alignment_station = lambda *_: (
                    SimpleNamespace(x=math.nan, y=0),
                    0,
                )
            elif kind in ("gauge", "angle"):
                source.module._rea_c10_turnout_outer_gauge_point_at_x = (
                    lambda _d, x: (
                        x,
                        math.nan if kind == "gauge" else 10,
                        0 if kind == "angle" else math.atan(0.1),
                    )
                )
            elif kind == "lower":
                dimensions["check_turnout_flare_in_x"] = STATIONS[0]
            elif kind == "upper":
                dimensions["check_turnout_flare_out_x"] = STATIONS[2] - 1e-6
            elif kind == "configuration":
                source.context[1]["orientation"] = "Trailing"
            else:
                source.context[2]["geometry_signature"] = "changed"
            with self.subTest(kind=kind):
                self.refuse(source)

    def test_finite_support_applies_to_all_six_new_source_positions(self):
        for index in range(6):
            for kind in (
                "outside",
                "boundary",
                "nonfinite",
                "bool",
                "degenerate",
                "self-intersection",
                "gauge_face_points",
                "points",
                "outer_face_points",
            ):
                source = source_case()
                record = selected_records(source)[index]
                timber = next(
                    t
                    for t in source.context[5]
                    if t["stable_identity"] == record["timber_identity"]
                )
                rail = next(
                    r
                    for r in source.context[4]
                    if r["stable_identity"] == record["rail_identity"]
                )
                if kind in ("outside", "boundary", "nonfinite", "bool"):
                    record["centre_point"] = {
                        "outside": [1000, 1000],
                        "boundary": [800, 420],
                        "nonfinite": [math.nan, 420],
                        "bool": [True, 420],
                    }[kind]
                elif kind == "degenerate":
                    timber["outline_polygon"] = [
                        [800, 380],
                        [850, 420],
                        [900, 460],
                    ]
                elif kind == "self-intersection":
                    timber["outline_polygon"] = [
                        [800, 380],
                        [900, 460],
                        [800, 460],
                        [900, 380],
                    ]
                else:
                    rail[kind] = [[790, 380], [910, 380]]  # Boundary only.
                with self.subTest(index=index, kind=kind):
                    self.refuse(source)

    def test_late_source_host_and_catalogue_failures_reach_existing_verifier(
        self,
    ):
        for change in (
            "analysis",
            "host",
            "host-object",
            "shape",
            "catalogue",
        ):
            source = source_case()

            def create(_path, _values, _shapes, _receipt, verify, **_options):
                if change == "analysis":
                    selected_records(source)[0]["centre_point"][0] += 1e-6
                elif change == "host":
                    source.host_data["points"][0].x += 1e-6
                elif change == "host-object":
                    old = source.objects["Host"]
                    source.objects["Host"] = SimpleNamespace(
                        Name=old.Name, Shape=old.Shape
                    )
                elif change == "shape":
                    from validate_phase9b_s1_s1j_reference_preview import (
                        ShapeDouble as ContextShape,
                    )

                    source.objects["rails"].Shape = ContextShape("changed")
                else:
                    with patch.object(
                        placement_binding(),
                        "verify_catalogue_sources",
                        side_effect=ValueError("changed catalogue"),
                    ):
                        verify()
                    return
                verify()

            with self.subTest(change=change), self.assertRaises(ValueError):
                preview(source, create, include_turnout_side=True)

    def test_session_forwards_only_true_after_routing_check(self):
        for options, wanted in (
            ({}, {}),
            ({"include_turnout_side": False}, {}),
            ({"include_turnout_side": True}, {"include_turnout_side": True}),
        ):
            calls = []
            session = SimpleNamespace(
                module=object(),
                _private_catalogue_cc_preview_factory=object(),
                routing_record=lambda: calls.append("route"),
            )
            document = object()

            def operation(*args, **kwargs):
                self.assertEqual(calls, ["route"])
                self.assertEqual(
                    args,
                    (
                        session.module,
                        document,
                        "TO-001",
                        "catalogue.json",
                        session._private_catalogue_cc_preview_factory,
                    ),
                )
                self.assertEqual(kwargs, wanted)
                return "receipt"

            with patch.object(placement_binding(), METHOD, operation):
                result = getattr(
                    transition_workflow.ModularCoreLayoutWorkflowSession,
                    METHOD,
                )(
                    session,
                    document,
                    "TO-001",
                    "catalogue.json",
                    **options,
                )
            self.assertEqual(result, "receipt")

    def test_adapter_198_transforms_35_layers_and_indexed_lh_metadata(self):
        args = preview(source_case(), include_turnout_side=True)[0]
        boundary = adapter_boundary()
        result = adapter(boundary, args[1], args[3], include_turnout_side=True)
        layers, report, verify = result.prepare()
        self.assertEqual(len(layers), 35)
        self.assertEqual(report["component_count"], 33)
        self.assertEqual(report["placement_count"], 6)
        self.assertEqual(report["layer_count"], 35)
        self.assertEqual(sum(len(layer.children) for layer in layers[2:]), 198)
        self.assertEqual(
            report["fixing_angle_frame"],
            "uncurved-LH-source-before-common-host-rotation",
        )
        self.assertEqual(report["fixing_head_rotation_rad"], 0.0)
        self.assertFalse(report["random_export_parity"])
        self.assertFalse(report["templot_global_fixing_angle_parity"])
        self.assertFalse(report["geometry_rebuilt"])
        by_id = {p.position_id: p for p in args[1]}
        count = 0
        for placement in report["placements"]:
            value = by_id[placement["position_id"]]
            for component in placement["components"]:
                name = component["source_name"]
                frame = (
                    value.fixing_frames[FIXING_NAMES.index(name) // 4]
                    if name in FIXING_NAMES
                    else value
                )
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.assertEqual(component[field], getattr(frame, field))
                self.assertEqual(
                    component["placement_identity"],
                    (value.position_id, CC_MODEL_SHA256, name),
                )
                count += 1
        self.assertEqual(count, 198)
        verify(layers)
        with self.assertRaises(ValueError):
            verify(layers[:-1])
        result.verify()
        boundary.source_check.assert_called_once()
        boundary.catalogue_check.assert_called_once()
        for check in (boundary.source_check, boundary.catalogue_check):
            check.side_effect = ValueError("late failure")
            with self.assertRaisesRegex(ValueError, "late failure"):
                result.verify()
            check.side_effect = None

    def test_adapter_independently_refuses_changed_cohort_and_nested_frames(
        self,
    ):
        args = preview(source_case(), include_turnout_side=True)[0]
        values, receipt = args[1], args[3]
        for change in (
            "missing",
            "duplicate",
            "owner",
            "rail",
            "timber",
            "frame",
            "receipt-owner",
            "receipt-pair",
            "receipt-count",
        ):
            boundary = adapter_boundary()
            candidate, record = copy.deepcopy(values), copy.deepcopy(receipt)
            if change == "missing":
                candidate = candidate[:-1]
            elif change == "duplicate":
                candidate = candidate[:-1] + (candidate[0],)
            elif change in ("owner", "rail", "timber"):
                field = {
                    "owner": "position_id",
                    "rail": "rail_id",
                    "timber": "timber_id",
                }[change]
                first = candidate[0]
                first = replace(
                    first,
                    **{field: "unknown"},
                    fixing_frames=tuple(
                        replace(f, **{field: "unknown"})
                        for f in first.fixing_frames
                    ),
                )
                candidate = (first,) + candidate[1:]
            elif change == "frame":
                object.__setattr__(
                    candidate[0].fixing_frames[0], "x_axis", (2, 0)
                )
            elif change == "receipt-owner":
                record["selected_positions"][0]["position_id"] = "unknown"
            elif change == "receipt-pair":
                record["shared_supports"][0]["assembly_position_id"] = (
                    "unknown"
                )
            else:
                record["represented_source_position_count"] = 6
            with self.subTest(change=change), self.assertRaises(ValueError):
                adapter(boundary, candidate, record, include_turnout_side=True)
            boundary.materialise.assert_not_called()

    def test_existing_finite_support_outcomes_and_diagnostics_are_preserved(
        self,
    ):
        from tracktemplate.compatibility import (
            chair_turnout_single_rail_placement as single,
        )

        def support_case():
            return (
                {"centre_point": [2.0, 2.0]},
                {
                    field: [[-1.0, 2.0], [5.0, 2.0]]
                    for field in (
                        "gauge_face_points",
                        "points",
                        "outer_face_points",
                    )
                },
                {"outline_polygon": [[0, 0], [4, 0], [4, 4], [0, 4]]},
            )

        for label in ("R2", "crossing-tail", "joint-exit"):
            valid = support_case()
            before = copy.deepcopy(valid)
            self.assertIsNone(single._r2_finite_support(*valid, label=label))
            self.assertEqual(valid, before)
            for case, suffix in (
                ("outside", "canonical centre is outside its finite timber"),
                ("boundary", "canonical centre is outside its finite timber"),
                ("nonfinite", "support geometry is not finite XY"),
                ("boolean", "support geometry is not finite XY"),
                ("repeat", "outline repeats a vertex"),
                ("degenerate", "outline is degenerate"),
                ("crossing", "outline intersects itself"),
            ):
                position, rail, timber = support_case()
                if case in ("outside", "boundary", "nonfinite", "boolean"):
                    position["centre_point"] = {
                        "outside": [5, 5],
                        "boundary": [0, 2],
                        "nonfinite": [math.nan, 2],
                        "boolean": [True, 2],
                    }[case]
                elif case == "repeat":
                    timber["outline_polygon"].append([0, 0])
                elif case == "degenerate":
                    timber["outline_polygon"] = [[0, 0], [2, 2], [4, 4]]
                else:
                    # Unequal lobes retain nonzero signed area, so this
                    # independently exercises the self-intersection guard.
                    timber["outline_polygon"] = [
                        [0, 0],
                        [4, 4],
                        [0, 4],
                        [3, 0],
                    ]
                with self.subTest(label=label, case=case):
                    with self.assertRaises(ValueError) as raised:
                        single._r2_finite_support(
                            position, rail, timber, label=label
                        )
                    self.assertEqual(
                        str(raised.exception),
                        "Private TO-001 single-rail: " + label + " " + suffix,
                    )
            for field in ("gauge_face_points", "points", "outer_face_points"):
                for vertices in (
                    [[-1, 0], [5, 0]],
                    [[-1, -1], [0, 0]],
                    [[-2, 2], [-1, 2]],
                ):
                    position, rail, timber = support_case()
                    rail[field] = vertices
                    with self.subTest(
                        label=label, field=field, vertices=vertices
                    ):
                        with self.assertRaises(ValueError) as raised:
                            single._r2_finite_support(
                                position, rail, timber, label=label
                            )
                        self.assertEqual(
                            str(raised.exception),
                            "Private TO-001 single-rail: "
                            + label
                            + " finite "
                            + field
                            + " has no interior timber span",
                        )

    def test_rh_output_and_opaque_default_factory_contract_remain(self):
        records = rh_records()
        self.assertEqual(
            hashlib.sha256(
                json.dumps(
                    [asdict(p) for p in records],
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest(),
            RH_BASELINE_SHA,
        )
        boundary = adapter_boundary()
        item = boundary.selections["CC"]
        _prepared, _specs, prepare = boundary.namespace[
            "_prepare_catalogue_family"
        ](
            "catalogue.json",
            records,
            None,
            {"source": "existing RH test"},
            family="CC",
            placement_type=central.CentralCheckPlacement,
            model_sha256=CC_MODEL_SHA256,
            source_names=tuple(p.name for p in item.components),
            run="context-native-02",
            source_context=item.context,
        )
        _layers, report, _verify = prepare()
        self.assertEqual(
            report["fixing_angle_frame"],
            "uncurved-RH-source-before-common-host-rotation",
        )
        helper = Mock(return_value="original-boundary")
        boundary.namespace["_create_private_catalogue_preview"] = helper
        args = (
            "catalogue.json",
            object(),
            object(),
            {"opaque": "receipt"},
            Mock(),
        )
        self.assertEqual(
            boundary.namespace[FACTORY](*args), "original-boundary"
        )
        self.assertEqual(helper.call_args.args, args)
        self.assertIs(
            helper.call_args.kwargs["placement_type"], PairedChairPlacement
        )
        self.assertNotIn("source_handing", helper.call_args.kwargs)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutSideCentralCheckTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
