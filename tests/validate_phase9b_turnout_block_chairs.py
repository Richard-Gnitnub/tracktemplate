"""Check five fixed LH main-side block assemblies without native imports.

Independent source summaries supply the five outer and 56 raw frames.
Synthetic support geometry tests admission, not actual railway fit. Local
shape doubles observe full frames and nonidentity saved placements through
existing adapter code. Native geometry and lifecycle remain unqualified.
Source-informed comparison metadata: GPL-3.0-or-later; see NOTICE.md.
"""

import ast
import copy
from dataclasses import FrozenInstanceError
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

from tracktemplate.compatibility import (  # noqa: E402
    chair_pair_placement as binding,
)
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    S1JPlacement,
    S1Placement,
)
from tracktemplate.domain.turnout import rea_c10_dimensions  # noqa: E402
from validate_phase9b_turnout_central_cc import (  # noqa: E402
    selected_record,
    selected_timber,
    source_case as central_source_case,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    AdapterBoundary,
    ShapeDouble,
)

FRAME_SHA = "808f672e5df7f63b67cd0e6e2e8e0b0930e646eeb23a2791f8867b38c7ac087a"
METHOD = "preview_private_catalogue_turnout_block_chairs"
FACTORY = "create_private_catalogue_turnout_block_preview"
PORT = "private_catalogue_turnout_block_preview_factory"
FAMILIES = ("1P", "2P", "3P", "4P", "5P")
SENTINEL = "Phase 9B TO-001 LH main-side block validation passed"


def expected():
    path = ROOT / "tests/fixtures/phase9b-to-lh-main-block-source-frames.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FRAME_SHA
    return json.loads(raw)


def position(source, row):
    return next(
        p
        for p in source.context[2]["positions"]
        if p["stable_chair_position_identity"] == row["position_id"]
    )


def source_case():
    """Keep 168 records; insert five owners and ten unselected witnesses.

    Five interpolation values and timber bases are exact source inputs.
    Complete host arrays and 18-vertex rectangular supports are invented.
    No initial full-array source fingerprint is asserted; late array and
    object identity must be preserved. Actual support has a separate proof.
    """
    source = central_source_case()
    analysis, rails, timbers = (
        source.context[2],
        source.context[4],
        source.context[5],
    )
    template = copy.deepcopy(selected_record(source))
    timber_template = copy.deepcopy(selected_timber(source))
    source.module.CHAIR_ASSIGNMENT_CONFIRMED = (
        "confirmed ordinary or turnout assignment"
    )
    source.module.CHAIR_FAMILY_SWITCH_SUPPORT = "switch-support chair"
    source.module.CHAIR_FAMILY_SWITCH_HEEL = "switch-heel chair"
    source.module.CHAIR_CLASS_SOURCE = "source-derived prototype requirement"
    source.module.rea_c10_dimensions = rea_c10_dimensions
    source.host_frames = {}
    # Eighteen distinct synthetic perimeter vertices; no source polygon.
    outline = (
        [[700 + i * 30, 200] for i in range(5)]
        + [[850, 200 + i * 25] for i in range(4)]
        + [[850 - i * 30, 300] for i in range(5)]
        + [[700, 300 - i * 25] for i in range(4)]
    )
    rail_names = (
        "main-side stock rail",
        "curved switch and closure rail",
        "turnout-side stock rail",
    )
    rail_map = {}
    for rail_name in rail_names:
        identity = "TO-001:rail:" + rail_name.replace(" ", "-")
        rail = next(
            (r for r in rails if r["stable_identity"] == identity), None
        )
        if rail is None:
            rail = {"stable_identity": identity}
            rails.append(rail)
        rail.update(
            name=rail_name,
            rail_role=(
                "stock rail"
                if "stock" in rail_name
                else "curved switch and closure rail"
            ),
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
        for field in ("gauge_face_points", "points", "outer_face_points"):
            rail[field] = [[690.0, 240.0], [860.0, 240.0]]
        rail_map[identity] = rail
    slot = 0
    for row in expected()["positions"]:
        name = row["timber_id"].split(":")[-1]
        basis = copy.deepcopy(row["host_basis"])
        source.host_frames[basis["host_station_mm"]] = (
            SimpleNamespace(
                x=basis["host_point_mm"][0], y=basis["host_point_mm"][1]
            ),
            basis["heading_radians"],
        )
        nominal = row["nominal_timber_basis"]["source_configuration"]
        source.layout.append(
            dict(
                identifier=name,
                x=nominal["local_x"],
                near_y=nominal["local_near_y"],
                far_y=nominal["local_far_y"],
                length_prototype_inches=nominal["length_prototype_inches"],
            )
        )
        timber = copy.deepcopy(timber_template)
        timber.update(copy.deepcopy(row["nominal_timber_basis"]))
        timber.update(
            stable_identity=row["timber_id"],
            identifier=name,
            prototype_reference=name,
            section="switch",
            outline_polygon=copy.deepcopy(outline),
        )
        timbers.append(timber)
        for role in ("owner", "empty-companion", "turnout-side"):
            record = copy.deepcopy(template)
            record.update(copy.deepcopy(row["canonical_input"]))
            rail_id = (
                row["rail_id"]
                if role == "owner"
                else "TO-001:rail:curved-switch-and-closure-rail"
                if role == "empty-companion"
                else "TO-001:rail:turnout-side-stock-rail"
            )
            rail = rail_map[rail_id]
            identity = row["position_id"].replace(
                "main-side-stock-rail",
                rail_id.split(":rail:")[1],
            )
            label = "" if role == "empty-companion" else row["raw_label"]
            record.update(
                stable_chair_position_identity=identity,
                rail_identity=rail_id,
                rail_name=rail["name"],
                rail_role=rail["rail_role"],
                timber_identity=row["timber_id"],
                prototype_timber_identifier=name,
                timber_identifier=name,
                parent_turnout_identity="TO-001",
                parent_crossover_identity="",
                chair_code=0 if role == "empty-companion" else row["raw_code"],
                chair_code_label=label,
                source_or_assumed_classification=row[
                    "raw_source_classification"
                ],
                source_configuration={
                    "rail": copy.deepcopy(rail["source_configuration"]),
                    "timber": copy.deepcopy(nominal),
                },
            )
            if role == "empty-companion":
                record.update(
                    chair_family="deliberately omitted chair position",
                    deliberate_omission=True,
                )
            old_id = f"invented-unselected-{slot:03d}"
            index = next(
                i
                for i, p in enumerate(analysis["positions"])
                if p["stable_chair_position_identity"] == old_id
            )
            analysis["positions"][index] = record
            exclusion = next(
                p
                for p in source.plan["analytical_only"]
                if p["chair_position_identity"] == old_id
            )
            exclusion.update(
                chair_position_identity=identity,
                rail_identity=rail_id,
                timber_identity=row["timber_id"],
                chair_label=label,
                chair_family=record["chair_family"],
                reason=(
                    "shared support position deliberately has no separate "
                    "chair body"
                    if role == "empty-companion"
                    else "chair family "
                    + record["chair_family"]
                    + " requires a dedicated physical definition"
                ),
                deliberate_omission=role == "empty-companion",
                unresolved_special=role != "empty-companion",
            )
            slot += 1
    original = source.module.interpolate_alignment_station
    source.module.interpolate_alignment_station = lambda data, station: (
        source.host_frames[station]
        if station in source.host_frames
        else original(data, station)
    )
    for instance in source.plan["instances"]:
        instance["base_z"] = 0.8
    return source


def catalogue_selections():
    """Double only admitted catalogue summaries, never generate a model."""
    selections = {}
    for row in expected()["positions"]:
        family = row["family"]
        model = expected()["provenance"]["models"][family]
        context = dict(
            context_id=None,
            context_sha256=model["context_sha256"],
            frame="chair-local model mm, X along main rail, rail-top Z=0; "
            "crossing origin at main crossing rail gauge face",
            sample_id=None,
            sample_kind="fixture_timber",
            station_mm=row["source_station_mm"],
            timber_id=row["timber_id"].split(":")[-1],
        )
        fixing = dict(
            source_twist_reapplied=False,
            recipe_sha256=model["fixing_recipe_sha256"],
        )
        native = dict(
            family=family,
            source_recipe={
                "context_sha256": model["context_sha256"],
                "station_mm": row["source_station_mm"],
                "timber_id": context["timber_id"],
                "chair_code": row["raw_code"],
                "family": family,
            },
            fixing_proof={
                "model_sha256": model["sha256"],
                "source_fixings": {
                    "placement": fixing,
                    "head_rotation_degrees": 0.0,
                    "random_export_parity": False,
                    "p_bolt_status": "NOT_APPLICABLE_SOURCE_DISPATCH",
                },
            },
        )
        selections[family] = SimpleNamespace(
            label=family,
            run="context-native-02",
            context=context,
            model_sha256=model["sha256"],
            components=tuple(
                SimpleNamespace(name=name, label=name)
                for name in model["component_names"]
            ),
            catalogue_sha256="invented-catalogue",
            model_path="invented",
            bindings=(),
            metadata={"native_record": native},
            limitations=(),
        )
    return selections


def preview(source, factory=None, *, selections=None):
    selections = catalogue_selections() if selections is None else selections
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        patch.object(
            binding,
            "prepare_catalogue_chair",
            create=True,
            side_effect=lambda _path, family, **_kw: selections[family],
        ),
        patch.object(binding, "verify_catalogue_sources", create=True),
    ):
        return getattr(binding, METHOD)(
            source.module,
            source.document,
            "TO-001",
            "catalogue.json",
            factory or (lambda *args: args),
        )


def frame_token(frame):
    return (tuple(frame.origin_mm), tuple(frame.x_axis), tuple(frame.y_axis))


def adapter_boundary():
    """Observe actual adapter composition, including all saved placements.

    Tokens are deliberately nonidentity. The observer does not implement
    geometry: it records full-frame multiplication and shares identity.
    No permanent source-body hash or AST equality assertion is used.
    """
    boundary = AdapterBoundary()
    path = (
        ROOT
        / "tracktemplate/adapters/freecad"
        / "chair_catalogue_placement_preview.py"
    )
    tree = ast.parse(path.read_text())
    nodes = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == FACTORY
    ]
    assert len(nodes) == 1
    reference = (
        ROOT / "tracktemplate/adapters/freecad/chair_reference_preview.py"
    )
    helper = next(
        n
        for n in ast.parse(reference.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "_placements"
    )
    boundary.namespace.update(
        PairedChairPlacement=PairedChairPlacement,
        S1Placement=S1Placement,
        S1JPlacement=S1JPlacement,
    )
    exec(
        compile(
            ast.Module(body=[helper, *nodes], type_ignores=[]),
            str(path),
            "exec",
        ),
        boundary.namespace,
    )
    boundary.selections = catalogue_selections()
    boundary.prototypes = {}
    boundary.saved_tokens = {}

    def reader(_path, family, *, run):
        assert run == "context-native-02"
        return boundary.selections[family]

    def import_components(prepared):
        shapes = []
        for index, _component in enumerate(prepared.components):
            shape = ShapeDouble()
            token = (
                "saved-nonidentity",
                prepared.label,
                index,
                (index + 1.25, -2.5, 0.75),
                (0.0, 0.0, 0.6, 0.8),
            )
            shape.Placement = token
            shapes.append(shape)
        values = tuple(shapes)
        boundary.prototypes[prepared.label] = values
        boundary.saved_tokens[prepared.label] = tuple(
            s.Placement for s in values
        )
        return values, tuple(boundary.measure(s) for s in values)

    def verify_component(actual, wanted, **_kwargs):
        if not (
            actual.isPartner(wanted)
            and actual.Orientation == wanted.Orientation
            and actual.Placement == wanted.Placement
        ):
            raise ValueError("component identity or full placement changed")

    def prototype_state(shape, **_kwargs):
        return dict(
            boundary.measure(shape),
            saved_placement=copy.deepcopy(shape.Placement),
        )

    boundary.namespace.update(
        prepare_catalogue_chair=Mock(side_effect=reader),
        _import_components=import_components,
        _host_placement=lambda value: SimpleNamespace(
            multiply=lambda saved: (frame_token(value), saved),
        ),
        _prototype_state=prototype_state,
        _verify_component=verify_component,
        _same_presented_shape=lambda a, b: (
            a.isPartner(b)
            and a.Placement == b.Placement
            and a.Orientation == b.Orientation
        ),
    )
    return boundary


def adapter(boundary, args):
    return boundary.namespace[FACTORY](
        args[0],
        args[1],
        (ShapeDouble(context=True), ShapeDouble(context=True)),
        args[3],
        args[4],
    )


class TurnoutBlockChairTests(unittest.TestCase):
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

    def test_all_61_independent_frames_and_mounting_source_z_distinction(self):
        source = source_case()
        groups = preview(source)[1]
        frames = scalars = 0
        for row in expected()["positions"]:
            (value,) = groups[row["family"]]
            self.assertIs(type(value), PairedChairPlacement)
            for field in ("origin_mm", "x_axis", "y_axis"):
                self.near(getattr(value, field), row["body"][field])
                scalars += len(row["body"][field])
            frames += 1
            self.assertEqual(value.origin_mm[2], 0.8)
            with self.assertRaises(FrozenInstanceError):
                value.position_id = "changed"
            self.assertEqual(
                [
                    c["source_component_index"]
                    for c in row["constituent_frames"]
                ],
                list(range(len(row["constituent_frames"]))),
            )
            self.assertEqual(
                [f["source_index"] for f in row["fixing_frames"]], [1, 2, 3, 4]
            )
            sources = [
                (
                    c["source_insertion"]["x_mm"],
                    c["source_insertion"]["y_mm"],
                    c["source_insertion"]["z_mm"],
                    c["source_insertion"]["rotation_rad"],
                    c["world_source_frame"],
                )
                for c in row["constituent_frames"]
            ]
            sources += [
                (
                    f["source_centre_mm"][0],
                    f["source_centre_mm"][1],
                    0.0,
                    0.0,
                    f["world_source_frame"],
                )
                for f in row["fixing_frames"]
            ]
            for x, y, z, angle, wanted in sources:
                origin = value.transform_point((-x, -y - 0.45, z + 149 / 60))
                # Raw source axes are carried through retained negative XY.
                cosine, sine = math.cos(angle), math.sin(angle)
                x_axis = tuple(
                    -cosine * value.x_axis[i] - sine * value.y_axis[i]
                    for i in (0, 1)
                )
                y_axis = tuple(
                    sine * value.x_axis[i] - cosine * value.y_axis[i]
                    for i in (0, 1)
                )
                for actual, field in (
                    (origin, "origin_mm"),
                    (x_axis, "x_axis"),
                    (y_axis, "y_axis"),
                ):
                    self.near(actual, wanted[field])
                    scalars += len(wanted[field])
                self.assertNotEqual(origin[2], value.origin_mm[2])
                frames += 1
        self.assertEqual((frames, scalars), (61, 427))

    def test_exact_ordered_five_keep_all_168_records_and_key_policy(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        args = preview(source)
        self.assertEqual(len(args), 5)
        groups, receipt = args[1], args[3]
        self.assertEqual(tuple(groups), FAMILIES)
        self.assertTrue(all(len(group) == 1 for group in groups.values()))
        owners = {r["position_id"] for r in expected()["positions"]}
        self.assertEqual(
            {p.position_id for group in groups.values() for p in group}, owners
        )
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["selected_block_count"], 5)
        self.assertEqual(receipt["represented_source_position_count"], 5)
        self.assertEqual(
            receipt["selected_family_counts"], dict.fromkeys(FAMILIES, 1)
        )
        self.assertEqual(len(receipt["remaining_positions"]), 163)
        self.assertEqual(receipt.get("shared_supports", []), [])
        remaining = {
            p["stable_chair_position_identity"]
            for p in receipt["remaining_positions"]
        }
        for owner in owners:
            self.assertIn(
                owner.replace(
                    "main-side-stock-rail", "curved-switch-and-closure-rail"
                ),
                remaining,
            )
            self.assertIn(
                owner.replace("main-side", "turnout-side"), remaining
            )
        self.assertEqual(
            receipt["original_analytical_exclusions"],
            source.plan["analytical_only"],
        )
        self.assertEqual(receipt["retained_research_key_direction_sign"], 1)
        self.assertEqual(receipt["retained_research_key_offset_mm"], 0)
        self.assertEqual(len(receipt["selected_positions"]), 5)
        for row, record in zip(
            expected()["positions"], receipt["selected_positions"]
        ):
            original = record["original_position"]
            self.assertEqual(original, position(source, row))
            self.assertIs(type(original["key_direction_sign"]), int)
            self.assertEqual(original["key_direction_sign"], 0)
            self.assertEqual(record["source_branch"], row["source_branch"])
            self.assertEqual(
                record["source_station_mm"], row["source_station_mm"]
            )
            self.assertEqual(
                record["source_model_sha256"],
                expected()["provenance"]["models"][row["family"]]["sha256"],
            )
        self.assertEqual((source.context, source.plan), before)
        receipt["selected_positions"][0]["original_position"]["chair_code"] = (
            99
        )
        self.assertEqual((source.context, source.plan), before)

    def test_fixed_configuration_profile_and_mounting_datum(self):
        for field, value in (
            ("handing", "Right-hand"),
            ("orientation", "Trailing"),
            ("toe_chainage", 746.299),
            ("template_width", 33),
            ("track_gauge", 18.83),
            ("flangeway", 1.1),
            ("rail_geometry_revision", 1),
            ("timber_geometry_revision", True),
            ("chair_analysis_signature", "other"),
        ):
            source = source_case()
            source.context[1][field] = value
            with self.subTest(field=field):
                self.refuse(source)
        for change in ("profile", "embed", "scale", "datum", "datum-bool"):
            source = source_case()
            if change == "profile":
                source.plan["rail_profile"]["rail_depth_mm"] += 1e-9
            elif change == "embed":
                source.context[3]["future_chair_embed_depth"] += 1e-9
            elif change == "scale":
                source.module.TURNOUT_DEFAULT_SCALE = 87.0
            else:
                for instance in source.plan["instances"]:
                    instance["base_z"] = (
                        True if change == "datum-bool" else 0.9
                    )
            with self.subTest(change=change):
                self.refuse(source)

    def test_strict_identity_raw_classification_and_integer_key(self):
        for field, value in (
            ("parent_turnout_identity", "Other"),
            ("rail_identity", "Other"),
            ("chair_code", True),
            ("chair_code_label", "3P"),
            ("source_or_assumed_classification", "source-derived"),
            ("key_direction_sign", True),
            ("key_direction_sign", 1),
            ("key_orientation", "fixed"),
            ("special_assignment_deferred", 1),
            ("stale_signature_state", True),
            ("handedness", "Right-hand"),
        ):
            source = source_case()
            position(source, expected()["positions"][2])[field] = value
            with self.subTest(field=field, value=value):
                self.refuse(source)
        for change in ("missing", "duplicate", "extra"):
            source = source_case()
            rows = source.context[2]["positions"]
            item = position(source, expected()["positions"][0])
            if change == "missing":
                rows.remove(item)
            elif change == "duplicate":
                rows.append(copy.deepcopy(item))
            else:
                extra = copy.deepcopy(item)
                extra["stable_chair_position_identity"] += "-extra"
                rows[30] = extra
            with self.subTest(change=change):
                self.refuse(source)

    def test_exact_initial_host_and_nominal_timber_not_just_late_currentness(
        self,
    ):
        for row in expected()["positions"]:
            for change in (
                "point",
                "heading",
                "station",
                "nominal",
                "centre",
                "axis",
                "nonfinite",
                "boolean",
            ):
                source = source_case()
                station = row["host_basis"]["host_station_mm"]
                point, angle = source.host_frames[station]
                timber = selected_timber(
                    source, row["timber_id"].split(":")[-1]
                )
                if change == "point":
                    point.x += 0.1
                elif change == "heading":
                    source.host_frames[station] = point, angle + 0.001
                elif change == "station":
                    timber["host_chainage"] += 0.1
                elif change == "nominal":
                    timber["source_configuration"]["local_near_y"] += 0.1
                elif change == "centre":
                    timber["centre"][0] += 0.1
                elif change == "axis":
                    timber["source_configuration"][
                        "longitudinal_reference_axis"
                    ] = [1, 0]
                elif change == "nonfinite":
                    point.x = math.nan
                else:
                    point.x = True
                with self.subTest(family=row["family"], change=change):
                    self.refuse(source)

    def test_s12_strict_heel_station_and_branch_neighbours_refuse(self):
        row = expected()["positions"][-1]
        self.assertEqual(row["source_branch"], "closure")
        for station in (
            math.nextafter(row["source_station_mm"], -math.inf),
            math.nextafter(row["source_station_mm"], math.inf),
        ):
            source = source_case()
            timber = selected_timber(source, "S12")
            timber["source_configuration"]["local_x"] = station
            position(source, row)["source_configuration"]["timber"][
                "local_x"
            ] = station
            next(p for p in source.layout if p["identifier"] == "S12")["x"] = (
                station
            )
            with self.subTest(station=station):
                self.refuse(source)

    def test_each_family_model_context_recipe_and_component_order(self):
        for family in FAMILIES:
            for change in ("model", "context", "recipe", "fixing", "order"):
                selections = catalogue_selections()
                item = selections[family]
                if change == "model":
                    item.model_sha256 = "0" * 64
                elif change == "context":
                    item.context["context_sha256"] = "0" * 64
                elif change == "recipe":
                    item.metadata["native_record"]["source_recipe"][
                        "context_sha256"
                    ] = "0" * 64
                elif change == "fixing":
                    record = item.metadata["native_record"]["fixing_proof"]
                    record["source_fixings"]["placement"]["recipe_sha256"] = (
                        "0" * 64
                    )
                else:
                    item.components = tuple(reversed(item.components))
                with self.subTest(family=family, change=change):
                    self.refuse(source_case(), selections=selections)

    def test_two_rails_three_finite_paths_and_strict_centre_support(self):
        row = expected()["positions"][0]
        for rail_id in (
            row["rail_id"],
            "TO-001:rail:curved-switch-and-closure-rail",
        ):
            for field in ("gauge_face_points", "points", "outer_face_points"):
                for points in (
                    [],
                    [[680, 240], [690, 240]],
                    [[700, 200], [850, 200]],
                ):
                    source = source_case()
                    rail = next(
                        r
                        for r in source.context[4]
                        if r["stable_identity"] == rail_id
                    )
                    rail[field] = points
                    with self.subTest(
                        rail=rail_id, field=field, points=points
                    ):
                        self.refuse(source)
        for centre in ([700, 240], [699, 240]):
            source = source_case()
            position(source, row)["centre_point"] = centre
            self.refuse(source)

    def test_late_complete_host_source_and_all_five_catalogue_checks(self):
        for change in (
            "source",
            "point",
            "heading",
            "station",
            "total",
            "host-object",
            *FAMILIES,
        ):
            source = source_case()
            calls = []

            def create(*args):
                if change == "source":
                    source.context[2]["positions"][0]["validation_status"] = (
                        "changed"
                    )
                elif change == "point":
                    source.host_data["points"][0].x += 1
                elif change in ("heading", "station"):
                    source.host_data[change + "s"][0] += 1
                elif change == "total":
                    source.host_data["total"] += 1
                elif change == "host-object":
                    old = source.objects["Host"]
                    source.objects["Host"] = SimpleNamespace(
                        Name=old.Name, Shape=old.Shape
                    )

                def verify(prepared):
                    calls.append(prepared.label)
                    if prepared.label == change:
                        raise ValueError("late " + change)

                with patch.object(binding, "verify_catalogue_sources", verify):
                    args[4]()

            with self.subTest(change=change), self.assertRaises(ValueError):
                preview(source, create)
            if change in FAMILIES:
                self.assertIn(change, calls)

    def test_adapter_all_161_parts_use_full_outer_and_saved_frame_once(self):
        args = preview(source_case())
        boundary = adapter_boundary()
        result = adapter(boundary, args)
        boundary.materialise.assert_called_once()
        layers, report, verify = result.prepare()
        self.assertEqual((len(layers), len(result.specs)), (163, 163))
        self.assertEqual(
            (
                report["family_count"],
                report["placement_count"],
                report["component_count"],
            ),
            (5, 5, 161),
        )
        self.assertFalse(report["geometry_rebuilt"])
        self.assertFalse(report["production_geometry_authorized"])
        offset = 2
        for row in expected()["positions"]:
            family = row["family"]
            (value,) = args[1][family]
            prototypes = boundary.prototypes[family]
            names = expected()["provenance"]["models"][family][
                "component_names"
            ]
            family_report = report["families"][family]
            self.assertEqual(
                family_report["placement"],
                "source-paired-common-timber-frame.v1",
            )
            self.assertEqual(family_report["source_hand"], "LH")
            self.assertEqual(family_report["source_rail_code"], 1)
            self.assertEqual(family_report["excluded_source_components"], [])
            self.assertNotIn("RH", json.dumps(family_report))
            (placed,) = family_report["placements"]
            self.assertEqual(
                [c["source_name"] for c in placed["components"]], names
            )
            for index, (prototype, name) in enumerate(zip(prototypes, names)):
                (child,) = layers[offset + index].childShapes()
                self.assertTrue(child.isPartner(prototype))
                outer, saved = child.Placement
                for field, actual in zip(
                    ("origin_mm", "x_axis", "y_axis"), outer
                ):
                    self.near(actual, row["body"][field])
                self.assertEqual(saved, boundary.saved_tokens[family][index])
                self.assertEqual(prototype.Placement, saved)
                self.assertEqual(
                    placed["components"][index]["placement_identity"],
                    (
                        value.position_id,
                        boundary.selections[family].model_sha256,
                        name,
                    ),
                )
            offset += len(prototypes)
        self.assertEqual(offset, 163)
        verify(layers)

    def test_forged_groups_and_reflections_fail_before_materialise(
        self,
    ):
        original = preview(source_case())
        for change in (
            "missing",
            "extra",
            "swapped",
            "duplicate",
            "type",
            "reflected",
            "receipt",
            "key",
        ):
            groups, receipt = copy.deepcopy((original[1], original[3]))
            if change == "missing":
                del groups["5P"]
            elif change == "extra":
                groups["6P"] = groups["1P"]
            elif change == "swapped":
                groups["1P"], groups["2P"] = groups["2P"], groups["1P"]
            elif change == "duplicate":
                groups["1P"] += groups["1P"]
            elif change == "type":
                (value,) = groups["1P"]
                groups["1P"] = (S1Placement(**vars(value)),)
            elif change == "reflected":
                (value,) = groups["1P"]
                object.__setattr__(
                    value, "y_axis", tuple(-v for v in value.y_axis)
                )
            elif change == "receipt":
                receipt["selected_positions"][0]["family"] = "2P"
            else:
                receipt["retained_research_key_direction_sign"] = 0
            boundary = adapter_boundary()
            with (
                self.subTest(change=change),
                self.assertRaises((ValueError, TypeError)),
            ):
                adapter(
                    boundary,
                    (original[0], groups, original[2], receipt, original[4]),
                )
            boundary.materialise.assert_not_called()

    def test_each_slice_rejects_wrong_reflected_double_stored_transform(
        self,
    ):
        args = preview(source_case())
        for family in FAMILIES:
            for change in ("wrong", "reflection", "double"):
                boundary = adapter_boundary()
                result = adapter(boundary, args)
                layers, _report, verify = result.prepare()
                index = 2 + sum(
                    expected()["provenance"]["models"][f]["component_count"]
                    for f in FAMILIES[: FAMILIES.index(family)]
                )
                (original,) = layers[index].childShapes()
                child = ShapeDouble(original)
                outer, saved = child.Placement
                if change == "wrong":
                    altered = (
                        (outer[0][0] + 1, *outer[0][1:]),
                        outer[1],
                        outer[2],
                    )
                    child.Placement = altered, saved
                elif change == "reflection":
                    child.Placement = (
                        (outer[0], outer[1], tuple(-v for v in outer[2])),
                        saved,
                    )
                else:
                    child.Placement = outer, (outer, saved)
                layer = ShapeDouble(layers[index])
                layer.children = (child,)
                changed = (*layers[:index], layer, *layers[index + 1 :])
                with (
                    self.subTest(family=family, change=change),
                    self.assertRaises(ValueError),
                ):
                    verify(changed)

    def test_five_late_verifiers_and_failure_before_fifth_preparation(self):
        args = preview(source_case())
        boundary = adapter_boundary()
        result = adapter(boundary, (*args[:4], boundary.source_check))
        result.verify()
        boundary.source_check.assert_called_once()
        self.assertEqual(
            {c.args[0].label for c in boundary.catalogue_check.call_args_list},
            set(FAMILIES),
        )
        for family in FAMILIES:

            def fail(prepared):
                if prepared.label == family:
                    raise ValueError("late " + family)

            boundary.catalogue_check.side_effect = fail
            with (
                self.subTest(family=family),
                self.assertRaisesRegex(ValueError, "late"),
            ):
                result.verify()
        boundary.catalogue_check.side_effect = None
        boundary.source_check.side_effect = ValueError("late source")
        with self.assertRaisesRegex(ValueError, "late source"):
            result.verify()
        boundary = adapter_boundary()
        reader = boundary.namespace["prepare_catalogue_chair"]
        original_reader = reader.side_effect
        seen = []

        def fail_fifth(path, family, **kwargs):
            seen.append(family)
            if family == "5P":
                raise ValueError("fifth selection unavailable")
            return original_reader(path, family, **kwargs)

        reader.side_effect = fail_fifth
        with self.assertRaisesRegex(ValueError, "fifth selection unavailable"):
            adapter(boundary, args)
        self.assertEqual(tuple(seen), FAMILIES)
        boundary.materialise.assert_not_called()

    def test_session_optional_factory_uses_explicit_five_argument_operation(
        self,
    ):
        from tracktemplate import api
        from validate_phase9b_l1_reference_preview import _session

        original = _session()
        self.assertIsNone(getattr(original, "_" + PORT))
        session_type = transition_workflow.ModularCoreLayoutWorkflowSession
        factory = object()
        session = session_type(
            original._calculation_session,
            api.run_core_layout_export,
            **{PORT: factory},
        )
        self.assertIs(getattr(session, "_" + PORT), factory)
        calls = []
        session.routing_record = lambda: calls.append("routing")

        def operation(*args):
            self.assertEqual(calls, ["routing"])
            self.assertEqual(
                args,
                (
                    session.module,
                    "document",
                    "TO-001",
                    "catalogue.json",
                    factory,
                ),
            )
            return "receipt"

        with patch.object(binding, METHOD, operation):
            self.assertEqual(
                getattr(session, METHOD)(
                    "document", "TO-001", "catalogue.json"
                ),
                "receipt",
            )
        parameter = inspect.signature(
            transition_workflow.load_modular_transition_workflow_session
        ).parameters[PORT]
        self.assertIsNone(parameter.default)
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutBlockChairTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
