"""Check the three supported LH TO-001 check ends without native imports.

The independent numeric fixture supplies all eighteen expected frames.
Existing source, catalogue and shape doubles exercise admission and routing.
They do not prove native geometry, display, physical fit or model rights.
Source-informed comparison metadata is GPL-3.0-or-later; see NOTICE.md.
"""

import ast
import copy
from dataclasses import FrozenInstanceError, replace
import hashlib
import inspect
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
from tracktemplate.domain import check_end_placement as ends  # noqa: E402
from tracktemplate.domain.turnout import rea_c10_dimensions  # noqa: E402
from validate_phase9b_turnout_central_cc import (  # noqa: E402
    FIXING_NAMES,
    placement_binding,
    selected_record,
    selected_timber,
    source_case as main_source_case,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary,
    ShapeDouble,
)

FRAME_SHA = "25c88cae53fc70fb114d75b3025fe19d51001e6b83ae442a7e701b880d813541"
METHOD = "preview_private_catalogue_turnout_check_end_chairs"
FACTORY = "create_private_catalogue_turnout_check_end_preview"
PORT = "private_catalogue_turnout_check_end_preview_factory"
SEAT_KEY_NAMES = ("c06_CCSEATCK_CCSEATCK", "c07_CCKEY_CCKEY")
BLOCKED_OWNER = (
    "TO-001:chair:to-001-timber-x1-z:turnout-side-stock-rail"
)
SENTINEL = "Phase 9B TO-001 supported check-end validation passed"


def expected():
    path = ROOT / "tests/fixtures/phase9b-to-check-end-source-frames.json"
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FRAME_SHA
    return json.loads(data)


def arguments(row):
    return dict(
        position_id=row["position_id"], rail_id=row["rail_id"],
        timber_id=row["timber_id"],
        host_point_mm=row["host_basis"]["host_point_mm"],
        travel_heading_rad=row["host_basis"]["heading_radians"],
        base_z_mm=row["body"]["origin_mm"][2],
        side="MS" if row["source_rail_code"] == 1 else "TS",
        family=row["family"],
        # Preserve the existing binary64 source-pose token; fixture world
        # values stay the independent Decimal-derived expectations.
        source_angle_rad=(0.0 if row["source_rail_code"] == 1
                          else math.atan(0.1)),
        source_gauge_y_mm=row["source_gauge_y_mm"],
    )


def left_frame(row, **changes):
    return getattr(ends, "place_left_hand_check_end")(
        **dict(arguments(row), **changes),
    )


def source_case():
    """Reuse fixed TO doubles; add eight records and two synthetic timbers.

    The blocked pair is present in the canonical 168 records, with its
    check centre outside the synthetic support. It must remain unselected.
    These rectangles and finite lines are not source geometry evidence.
    """
    source = main_source_case()
    analysis, rails, timbers = (
        source.context[2], source.context[4], source.context[5]
    )
    templates = [copy.deepcopy(selected_record(source, companion=flag))
                 for flag in (False, True)]
    timber_template = copy.deepcopy(selected_timber(source))
    rows = expected()["positions"]
    dimensions = rea_c10_dimensions(16.5, 1.0, 76.2)
    source.module.rea_c10_dimensions = lambda *_args: dimensions
    turnout = rows[2]

    def pose(_dimensions, station):
        assert station == turnout["source_station_mm"]
        return (station, turnout["source_gauge_y_mm"] - 8.25,
                math.atan(0.1))

    source.module._rea_c10_turnout_outer_gauge_point_at_x = pose
    host_frames = {}
    for row in (rows[0], rows[1]):
        name = row["timber_id"].split(":")[-1]
        basis = row["host_basis"]
        point, heading = basis["host_point_mm"], basis["heading_radians"]
        host_frames[basis["host_station_mm"]] = (
            SimpleNamespace(x=point[0], y=point[1]), heading,
        )
        nominal = dict(source.layout[0], identifier=name,
                       x=row["source_station_mm"])
        source.layout.append(nominal)
        timber = copy.deepcopy(timber_template)
        timber["source_configuration"].update(
            local_x=nominal["x"], local_near_y=nominal["near_y"],
            local_far_y=nominal["far_y"], crossing_suffix=name[-1],
            length_prototype_inches=nominal["length_prototype_inches"],
            longitudinal_reference_axis=[math.cos(heading), math.sin(heading)],
        )
        mean_y = (nominal["near_y"] + nominal["far_y"]) / 2
        timber.update(
            stable_identity=row["timber_id"], identifier=name,
            prototype_reference=name, host_chainage=basis["host_station_mm"],
            local_rail_heading_radians=heading,
            centre=[point[0] - mean_y * math.sin(heading),
                    point[1] + mean_y * math.cos(heading)],
            outline_polygon=[[800, 380], [900, 380], [900, 460], [800, 460]],
        )
        timbers.append(timber)
    old_interpolate = source.module.interpolate_alignment_station
    source.module.interpolate_alignment_station = lambda data, station: (
        host_frames[station] if station in host_frames
        else old_interpolate(data, station)
    )
    named_rails = {}
    for side in ("main-side", "turnout-side"):
        for role in ("stock rail", "check rail"):
            name = side + " " + role
            identity = "TO-001:rail:" + name.replace(" ", "-")
            rail = next((r for r in rails
                         if r["stable_identity"] == identity), None)
            if rail is None:
                rail = {"stable_identity": identity}
                rails.append(rail)
            rail.update(
                name=name, rail_role=role, parent_turnout_identity="TO-001",
                parent_crossover_identity="", turnout_side="",
                source_configuration={
                    "gauge_face": name + " gauge face",
                    "outer_face": name + " outer face",
                    "gauge_orientation_source": (
                        "mapped named turnout rail faces"
                    ),
                    "rail_geometry_revision": 2,
                },
            )
            for field in ("gauge_face_points", "points", "outer_face_points"):
                rail[field] = [[790.0, 420.0], [910.0, 420.0]]
            named_rails[identity] = rail
    slot = 0
    for row, side in ((rows[0], "main-side"), (rows[0], "turnout-side"),
                      (rows[1], "main-side"), (rows[2], "turnout-side")):
        name = row["timber_id"].split(":")[-1]
        timber = selected_timber(source, name)
        for role, template in enumerate(templates):
            rail_name = side + (" stock rail" if role == 0
                                else " check rail")
            rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
            rail = named_rails[rail_id]
            identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                        + rail_name.replace(" ", "-"))
            position = copy.deepcopy(template)
            code, label = ((row["raw_code"], row["raw_label"])
                           if role == 0 else (15, "CC"))
            position.update(
                stable_chair_position_identity=identity,
                rail_identity=rail_id, rail_name=rail_name,
                rail_role=rail["rail_role"], timber_identity=row["timber_id"],
                prototype_timber_identifier=name, timber_identifier=name,
                chair_code=code, chair_code_label=label,
                source_configuration={
                    "rail": copy.deepcopy(rail["source_configuration"]),
                    "timber": copy.deepcopy(timber["source_configuration"]),
                },
                centre_point=([950.0, 500.0] if name == "X1-Z"
                              and side == "turnout-side" and role == 1
                              else [850.0, 420.0]),
            )
            old_id = f"invented-unselected-{slot:03d}"
            index = next(i for i, p in enumerate(analysis["positions"])
                         if p["stable_chair_position_identity"] == old_id)
            analysis["positions"][index] = position
            exclusion = next(p for p in source.plan["analytical_only"]
                             if p["chair_position_identity"] == old_id)
            exclusion.update(
                chair_position_identity=identity, rail_identity=rail_id,
                timber_identity=row["timber_id"], chair_label=label,
                chair_family=position["chair_family"],
                reason="special chair assignment remains analytical",
                deliberate_omission=False, unresolved_special=True,
            )
            slot += 1
    for record in source.plan["instances"]:
        record["base_z"] = 0.8
    return source


def catalogue_selections(boundary=None):
    """Reuse existing fixed component names without requiring the new API."""
    boundary = boundary or AdapterBoundary()
    models = expected()["provenance"]["models"]
    return {
        family: SimpleNamespace(
            label=family, run="context-native-02",
            context={"context_sha256": models[family]["context_sha256"]},
            model_sha256=models[family]["sha256"],
            components=tuple(SimpleNamespace(name=name, label=name)
                             for name in names),
            catalogue_sha256="invented-catalogue", model_path="invented",
            bindings=(), metadata={}, limitations=(),
        )
        for family, names in boundary.namespace["_CHECK_END_NAMES"]
    }


def adapter_boundary():
    """Run the actual wrapper and existing family helper with shape doubles."""
    boundary = AdapterBoundary()
    path = (ROOT / "tracktemplate/adapters/freecad"
            / "chair_catalogue_placement_preview.py")
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name == FACTORY]
    assert len(nodes) == 1
    boundary.namespace["prepare_check_end_placements"] = (
        ends.prepare_check_end_placements
    )
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"),
         boundary.namespace)
    boundary.selections = catalogue_selections(boundary)

    def reader(_path, family, *, run):
        assert run == "context-native-02"
        return boundary.selections[family]

    boundary.namespace["prepare_catalogue_chair"] = Mock(side_effect=reader)
    return boundary


def preview(source, factory=None, *, selections=None):
    command = placement_binding()
    if selections is None:
        selections = catalogue_selections()
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        patch.object(command, "prepare_catalogue_chair",
                     side_effect=lambda _path, family, **_kw:
                     selections[family]),
        patch.object(command, "verify_catalogue_sources"),
    ):
        return getattr(command, METHOD)(
            source.module, source.document, "TO-001", "catalogue.json",
            factory or (lambda *args: args),
        )


def adapter(boundary, args):
    return boundary.namespace[FACTORY](
        args[0], args[1],
        (ShapeDouble(context=True), ShapeDouble(context=True)),
        args[3], args[4],
    )


class TurnoutCheckEndTests(unittest.TestCase):
    def near(self, actual, wanted):
        self.assertEqual(len(actual), len(wanted))
        for a, b in zip(actual, wanted):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def refuse(self, source, *, selections=None):
        factory = Mock()
        with self.assertRaises((ValueError, TypeError)):
            preview(source, factory, selections=selections)
        factory.assert_not_called()

    def test_eighteen_independent_frames_and_six_source_identities(self):
        rows = expected()["positions"]
        self.assertEqual([r["family"] for r in rows], ["CCL", "CCR", "CCL"])
        ids = {identity for row in rows for identity in (
            row["position_id"], row["companion"]["position_id"],
        )}
        self.assertEqual(len(ids), 6)
        self.assertNotIn(BLOCKED_OWNER, ids)
        count = scalars = 0
        for row in rows:
            self.assertEqual([f["source_index"] for f in row["fixing_frames"]],
                             [1, 2, 3, 4])
            value = left_frame(row)
            self.assertIs(type(value), ends.CheckEndPlacement)
            for actual, wanted in zip(
                (value, value.check_frame, *value.fixing_frames),
                (row["body"], row["check_frame"], *row["fixing_frames"]),
            ):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(actual, field), wanted[field])
                    scalars += len(wanted[field])
                count += 1
            with self.assertRaises(FrozenInstanceError):
                value.position_id = "changed"
        self.assertEqual((count, scalars), (18, 126))

    def test_rigid_host_translation_rotation_and_reverse_heading(self):
        for row in expected()["positions"]:
            for delta in (math.pi, -0.71):
                cosine, sine = math.cos(delta), math.sin(delta)

                def rotate(xy):
                    return (cosine * xy[0] - sine * xy[1],
                            sine * xy[0] + cosine * xy[1])

                original = arguments(row)
                point = rotate(original["host_point_mm"])
                value = left_frame(
                    row, host_point_mm=(point[0] + 31, point[1] - 29),
                    travel_heading_rad=original["travel_heading_rad"] + delta,
                )
                for actual, wanted in zip(
                    (value, value.check_frame, *value.fixing_frames),
                    (row["body"], row["check_frame"], *row["fixing_frames"]),
                ):
                    origin = rotate(wanted["origin_mm"])
                    self.near(actual.origin_mm, (origin[0] + 31,
                              origin[1] - 29, wanted["origin_mm"][2]))
                    self.near(actual.x_axis, rotate(wanted["x_axis"]))
                    self.near(actual.y_axis, rotate(wanted["y_axis"]))

    def test_narrow_lh_pose_and_nested_frame_refusals(self):
        rows = expected()["positions"]
        for row, changes in (
            (rows[0], {"source_angle_rad": math.atan(0.1)}),
            (rows[0], {"source_gauge_y_mm": 1.0}),
            (rows[2], {"family": "CCR"}),
            (rows[2], {"source_angle_rad": math.atan(0.1) / 2}),
            (rows[2], {"source_angle_rad": True}),
            (rows[2], {"source_gauge_y_mm": math.nan}),
            (rows[2], {"base_z_mm": math.inf}),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                left_frame(row, **changes)
        value = left_frame(rows[2])
        forged = copy.deepcopy(value)
        object.__setattr__(forged.check_frame, "rail_id", "wrong-rail")
        with self.assertRaises(ValueError):
            ends.prepare_check_end_placements((forged,))

    def test_exact_three_pairs_preserve_canonical_records_and_blocked_pair(
        self,
    ):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        args = preview(source)
        self.assertEqual(len(args), 5)
        values, receipt = args[1], args[3]
        owners = {r["position_id"] for r in expected()["positions"]}
        self.assertEqual({p.position_id for p in values}, owners)
        by_id = {value.position_id: value for value in values}
        frames = scalars = 0
        for row in expected()["positions"]:
            value = by_id[row["position_id"]]
            self.assertEqual(len(value.fixing_frames), 4)
            for actual, wanted in zip(
                (value, value.check_frame, *value.fixing_frames),
                (row["body"], row["check_frame"], *row["fixing_frames"]),
            ):
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.near(getattr(actual, field), wanted[field])
                    scalars += len(wanted[field])
                frames += 1
        self.assertEqual((frames, scalars), (18, 126))
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["selected_check_end_count"], 3)
        self.assertEqual(receipt["represented_source_position_count"], 6)
        self.assertEqual(receipt["selected_family_counts"],
                         {"CCL": 2, "CCR": 1})
        self.assertEqual(len(receipt["remaining_positions"]), 162)
        remaining = {p["stable_chair_position_identity"]
                     for p in receipt["remaining_positions"]}
        self.assertTrue({BLOCKED_OWNER,
                         BLOCKED_OWNER.replace("stock-rail", "check-rail")}
                        <= remaining)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         source.plan["analytical_only"])
        self.assertEqual({(p["position_id"], p["assembly_position_id"])
                          for p in receipt["shared_supports"]},
                         {(r["companion"]["position_id"], r["position_id"])
                          for r in expected()["positions"]})
        self.assertEqual(before, (source.context, source.plan))

    def test_changed_binding_and_catalogue_fail_before_factory(self):
        for change in ("missing", "owner", "raw-label", "source",
                       "model", "context"):
            with self.subTest(change=change):
                source = source_case()
                selections = catalogue_selections()
                row = expected()["positions"][1]
                positions = source.context[2]["positions"]
                item = next(p for p in positions if p[
                    "stable_chair_position_identity"] == row["position_id"])
                if change == "missing":
                    positions[:] = [p for p in positions if p[
                        "stable_chair_position_identity"]
                        != row["companion"]["position_id"]]
                elif change == "owner":
                    item["parent_turnout_identity"] = "Other"
                elif change == "raw-label":
                    item["chair_code_label"] = "CCL"
                elif change == "source":
                    item["source_configuration"]["timber"]["local_x"] += 1
                elif change == "model":
                    selections["CCR"].model_sha256 = "0" * 64
                else:
                    selections["CCR"].context["context_sha256"] = "0" * 64
                self.refuse(source, selections=selections)

    def test_finite_named_paths_and_canonical_centres_remain_hard_guards(self):
        row = expected()["positions"][2]
        for change in ("centre", "gauge_face_points", "points",
                       "outer_face_points"):
            with self.subTest(change=change):
                source = source_case()
                position = next(p for p in source.context[2]["positions"]
                                if p["stable_chair_position_identity"]
                                == row["companion"]["position_id"])
                rail = next(r for r in source.context[4]
                            if r["stable_identity"]
                            == position["rail_identity"])
                if change == "centre":
                    position["centre_point"] = [950.0, 500.0]
                else:
                    rail[change] = [[700.0, 470.0], [710.0, 470.0]]
                self.refuse(source)

    def test_late_source_host_and_both_catalogue_verifiers(self):
        for change in ("source", "host", "CCL", "CCR"):
            source = source_case()
            calls = []

            def create(*args):
                def check(prepared):
                    calls.append(prepared.label)
                    if prepared.label == change:
                        raise ValueError("changed " + change)

                if change == "source":
                    item = source.context[2]["positions"][0]
                    item["validation_status"] = "changed"
                elif change == "host":
                    source.host_data["points"][0].x += 1.0
                with patch.object(placement_binding(),
                                  "verify_catalogue_sources", check):
                    args[4]()

            with self.subTest(change=change), self.assertRaises(ValueError):
                preview(source, create)
            if change in ("CCL", "CCR"):
                self.assertIn(change, calls)

    def test_adapter_maps_99_parts_to_body_check_and_indexed_fixings(self):
        boundary = adapter_boundary()
        args = preview(source_case())
        result = adapter(boundary, args)
        boundary.materialise.assert_called_once()
        layers, report, verify = result.prepare()
        self.assertEqual((len(layers), report["layer_count"]), (68, 68))
        self.assertEqual((report["family_count"], report["placement_count"],
                          report["component_count"]), (2, 3, 66))
        self.assertEqual(sum(len(layer.children) for layer in layers[2:]), 99)
        self.assertFalse(report["geometry_rebuilt"])
        self.assertFalse(report["production_geometry_authorized"])
        by_id = {p.position_id: p for p in args[1]}
        count = 0
        for family, family_report in report["families"].items():
            self.assertEqual(family_report["fixing_angle_frame"],
                             "uncurved-LH-source-before-common-host-rotation")
            self.assertEqual(family_report["fixing_head_rotation_rad"], 0.0)
            self.assertFalse(family_report["random_export_parity"])
            self.assertFalse(
                family_report["templot_global_fixing_angle_parity"],
            )
            for record in family_report["placements"]:
                value = by_id[record["position_id"]]
                self.assertEqual(value.family, family)
                for component in record["components"]:
                    name = component["source_name"]
                    frame = (value.fixing_frames[FIXING_NAMES.index(name) // 4]
                             if name in FIXING_NAMES else value.check_frame
                             if name in SEAT_KEY_NAMES else value)
                    for field in ("origin_mm", "x_axis", "y_axis"):
                        self.assertEqual(component[field],
                                         getattr(frame, field))
                    self.assertEqual(component["placement_identity"], (
                        value.position_id,
                        expected()["provenance"]["models"][family]["sha256"],
                        name,
                    ))
                    count += 1
        self.assertEqual(count, 99)
        verify(layers)

    def test_adapter_refuses_partial_extra_blocked_or_forged_cohort(self):
        args = preview(source_case())
        for change in ("missing", "duplicate", "blocked", "family",
                       "check-frame", "receipt"):
            with self.subTest(change=change):
                boundary = adapter_boundary()
                values, receipt = args[1], copy.deepcopy(args[3])
                if change == "missing":
                    values = values[:-1]
                elif change == "duplicate":
                    values += (values[0],)
                elif change == "blocked":
                    value = copy.deepcopy(values[0])
                    for frame in (value, value.check_frame,
                                  *value.fixing_frames):
                        object.__setattr__(frame, "position_id", BLOCKED_OWNER)
                        object.__setattr__(
                            frame, "rail_id",
                            "TO-001:rail:turnout-side-stock-rail",
                        )
                    values += (value,)
                elif change == "family":
                    values = (replace(values[0], family="CCR"),) + values[1:]
                elif change == "check-frame":
                    values = copy.deepcopy(values)
                    object.__setattr__(values[0].check_frame,
                                       "x_axis", (2.0, 0.0))
                else:
                    support = receipt["shared_supports"][0]
                    support["assembly_position_id"] = "Other"
                changed = (args[0], values, args[2], receipt, args[4])
                with self.assertRaises((ValueError, TypeError)):
                    adapter(boundary, changed)
                boundary.materialise.assert_not_called()

    def test_both_family_slices_and_late_inputs_are_verified(self):
        boundary = adapter_boundary()
        args = preview(source_case())
        args = (*args[:4], boundary.source_check)
        result = adapter(boundary, args)
        layers, _report, verify = result.prepare()
        verify(layers)
        for index in (2, 35):
            changed = list(layers)
            changed[index] = ShapeDouble()
            with self.subTest(layer=index), self.assertRaises(ValueError):
                verify(tuple(changed))
        result.verify()
        boundary.source_check.assert_called_once()
        self.assertEqual({call.args[0].label
                          for call in boundary.catalogue_check.call_args_list},
                         {"CCL", "CCR"})
        for family in ("CCL", "CCR"):
            def check(prepared):
                if prepared.label == family:
                    raise ValueError("late " + family)
            boundary.catalogue_check.side_effect = check
            with (self.subTest(family=family),
                  self.assertRaisesRegex(ValueError, "late")):
                result.verify()
        boundary.catalogue_check.side_effect = None
        boundary.source_check.side_effect = ValueError("late source")
        with self.assertRaisesRegex(ValueError, "late source"):
            result.verify()

    def test_second_family_preparation_failure_creates_no_document(self):
        boundary = adapter_boundary()
        args = preview(source_case())
        reader = boundary.namespace["prepare_catalogue_chair"]
        original = reader.side_effect
        calls = []

        def fail_second(path, family, **options):
            calls.append(family)
            if len(calls) == 2:
                raise ValueError("second family unavailable")
            return original(path, family, **options)

        reader.side_effect = fail_second
        with self.assertRaisesRegex(ValueError, "second family unavailable"):
            adapter(boundary, args)
        self.assertEqual(len(calls), 2)
        self.assertEqual(set(calls), {"CCL", "CCR"})
        boundary.materialise.assert_not_called()

    def test_session_factory_and_composition_keep_five_argument_route(self):
        from tracktemplate import api
        from validate_phase9b_l1_reference_preview import _session

        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        original = _session()
        self.assertIsNone(getattr(original, "_" + PORT))
        factory = object()
        session = session_type(original._calculation_session,
                               api.run_core_layout_export, **{PORT: factory})
        self.assertIs(getattr(session, "_" + PORT), factory)
        calls = []
        session.routing_record = lambda: calls.append("routing")

        def operation(*args):
            self.assertEqual(calls, ["routing"])
            self.assertEqual(args, (session.module, "document", "TO-001",
                                    "catalogue.json", factory))
            return "receipt"

        with patch.object(placement_binding(), METHOD, operation):
            self.assertEqual(getattr(session, METHOD)(
                "document", "TO-001", "catalogue.json"), "receipt")
        parameter = inspect.signature(
            transition_workflow.load_modular_transition_workflow_session
        ).parameters[PORT]
        self.assertIsNone(parameter.default)
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        macro = ast.parse((ROOT / "TrackTemplate.FCMacro").read_text())
        values = [keyword.value for node in ast.walk(macro)
                  if isinstance(node, ast.Call) for keyword in node.keywords
                  if keyword.arg == PORT]
        self.assertEqual(len(values), 1)
        self.assertIsInstance(values[0], ast.Attribute)
        self.assertEqual(values[0].attr, FACTORY)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutCheckEndTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
