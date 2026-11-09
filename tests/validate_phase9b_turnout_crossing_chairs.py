"""Check four fixed LH TO crossing assemblies without FreeCAD or Qt.

Fifty independent source frames provide 350 numeric expectations.
Invented finite supports exercise admission; actual railway support and
native geometry have separate evidence. Existing inert host doubles run
the shared lifecycle, including late refusal and owned rollback.
Source-informed comparison: GPL-3.0-or-later; see NOTICE.md.
"""

import ast
from contextlib import contextmanager
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

from tracktemplate.application import chair_catalogue  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_crossing_pair_catalogue as catalogue,
)
from tracktemplate.application.chair_catalogue import (  # noqa: E402
    CatalogueBinding,
    CatalogueChair,
    CatalogueComponent,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_crossing_pair_placement as binding,
    transition_workflow,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    S1Placement,
)
from validate_chair_preview_activation import PreviewRuntime  # noqa: E402
from validate_phase9b_turnout_block_chairs import (  # noqa: E402
    adapter_boundary as block_adapter_boundary,
    source_case as block_source_case,
)
from validate_phase9b_turnout_central_cc import (  # noqa: E402
    selected_record,
    selected_timber,
)
from validate_phase9b_turnout_single_rail_adapter import (  # noqa: E402
    ShapeDouble,
)

FRAME_SHA = "3fe86e5e6e0a565e1e151555fb9e1bca7723c176df804281486ec795c10da900"
METHOD = "preview_private_catalogue_turnout_crossing_chairs"
FACTORY = "create_private_catalogue_turnout_crossing_preview"
PORT = "private_catalogue_turnout_crossing_preview_factory"
FAMILIES = ("XA", "AA", "CD", "DD")
# Invented disjoint support bands; these are not railway dimensions.
SYNTHETIC_Y_BOUNDS = {
    "XA": (410, 417),
    "AA": (420, 427),
    "CD": (439, 445),
    "DD": (449, 455),
}
SENTINEL = "Phase 9B TO-001 LH crossing cohort validation passed"


def expected():
    path = (
        ROOT / "tests/fixtures/phase9b-to-crossing-cohort-source-frames.json"
    )
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FRAME_SHA
    return json.loads(raw)


def rows():
    return expected()["positions"]


def row(family):
    return next(value for value in rows() if value["family"] == family)


def position(source, identity):
    return next(
        p
        for p in source.context[2]["positions"]
        if p["stable_chair_position_identity"] == identity
    )


def source_case():
    """Use exact eight input records with invented supporting geometry.

    Four independently frozen host samples and nominal timber bases are
    inputs. Synthetic 18-vertex outlines and shared named polylines only
    exercise the guard. Actual finite railway support remains separate.
    """
    source = block_source_case()
    analysis, rails, timbers = (
        source.context[2],
        source.context[4],
        source.context[5],
    )
    template = copy.deepcopy(selected_record(source))
    timber_template = copy.deepcopy(selected_timber(source))
    records = []
    for value in rows():
        near_y, far_y = SYNTHETIC_Y_BOUNDS[value["family"]]
        step = (far_y - near_y) / 4
        outline = (
            [[800 + i * 20, near_y] for i in range(5)]
            + [[900, near_y + i * step] for i in range(4)]
            + [[900 - i * 20, far_y] for i in range(5)]
            + [[800, far_y - i * step] for i in range(4)]
        )
        name = value["timber_id"].split(":")[-1]
        timber = copy.deepcopy(timber_template)
        timber.update(copy.deepcopy(value["nominal_timber_basis"]))
        timber.update(
            stable_identity=value["timber_id"],
            identifier=name,
            prototype_reference=name,
            outline_polygon=copy.deepcopy(outline),
        )
        timber_index = next(
            (
                i
                for i, item in enumerate(timbers)
                if item["stable_identity"] == value["timber_id"]
            ),
            None,
        )
        if timber_index is None:
            timbers.append(timber)
        else:
            timbers[timber_index] = timber
        nominal = timber["source_configuration"]
        layout_row = dict(
            identifier=name,
            x=nominal["local_x"],
            near_y=nominal["local_near_y"],
            far_y=nominal["local_far_y"],
            length_prototype_inches=nominal["length_prototype_inches"],
        )
        layout_index = next(
            (
                i
                for i, item in enumerate(source.layout)
                if item["identifier"] == name
            ),
            None,
        )
        if layout_index is None:
            source.layout.append(layout_row)
        else:
            source.layout[layout_index] = layout_row
        basis = value["host_basis"]
        source.host_frames[basis["host_station_mm"]] = (
            SimpleNamespace(
                x=basis["host_point_mm"][0], y=basis["host_point_mm"][1]
            ),
            basis["heading_radians"],
        )
        for item in value["source_positions"]:
            rail = next(
                (r for r in rails if r["stable_identity"] == item["rail_id"]),
                None,
            )
            if rail is None:
                rail = {"stable_identity": item["rail_id"]}
                rails.append(rail)
            rail.update(
                name=item["rail_name"],
                rail_role=item["rail_role"],
                parent_turnout_identity="TO-001",
                parent_crossover_identity="",
                turnout_side="",
                source_configuration=copy.deepcopy(
                    item["rail_source_configuration"]
                ),
            )
            for field in ("points", "gauge_face_points", "outer_face_points"):
                rail[field] = [[850.0, 400.0], [850.0, 460.0]]
            record = copy.deepcopy(template)
            record.update(copy.deepcopy(item["canonical_input"]))
            record.update(
                stable_chair_position_identity=item["position_id"],
                rail_identity=item["rail_id"],
                rail_name=item["rail_name"],
                rail_role=item["rail_role"],
                timber_identity=value["timber_id"],
                prototype_timber_identifier=name,
                timber_identifier=name,
                parent_turnout_identity="TO-001",
                parent_crossover_identity="",
                chair_code=item["raw_code"],
                chair_code_label=item["raw_label"],
                source_configuration={
                    "rail": copy.deepcopy(rail["source_configuration"]),
                    "timber": copy.deepcopy(nominal),
                },
            )
            records.append(record)
    # Invented unchanged witnesses for the whole excluded BB assembly.
    for identity in expected()["provenance"]["excluded_position_ids"]:
        record = copy.deepcopy(template)
        rail_name = identity.split(":")[-1].replace("-", " ")
        record.update(
            stable_chair_position_identity=identity,
            rail_identity="TO-001:rail:" + identity.split(":")[-1],
            rail_name=rail_name,
            timber_identity="TO-001:timber:X5-B",
            prototype_timber_identifier="X5-B",
            timber_identifier="X5-B",
            chair_code=26 if rail_name == "vee point rail" else 25,
            chair_code_label="BB/BC"
            if rail_name == "vee point rail"
            else "AB",
        )
        records.append(record)
    for record in records:
        index = next(
            i
            for i, item in enumerate(analysis["positions"])
            if item["stable_chair_position_identity"].startswith(
                "invented-unselected-"
            )
        )
        old = analysis["positions"][index]["stable_chair_position_identity"]
        analysis["positions"][index] = record
        exclusion = next(
            item
            for item in source.plan["analytical_only"]
            if item["chair_position_identity"] == old
        )
        exclusion.update(
            chair_position_identity=record["stable_chair_position_identity"],
            rail_identity=record["rail_identity"],
            timber_identity=record["timber_identity"],
            chair_label=record["chair_code_label"],
            chair_family=record["chair_family"],
            reason="chair family requires a dedicated physical definition",
            deliberate_omission=False,
            unresolved_special=True,
        )
    timber_ids = [item["stable_identity"] for item in timbers]
    layout_ids = [item["identifier"] for item in source.layout]
    assert len(timber_ids) == len(set(timber_ids)), "unique fixture timbers"
    assert len(layout_ids) == len(set(layout_ids)), "unique fixture layout"
    return source


def selection(family):
    """Return immutable metadata and inert components, not a model."""
    value = row(family)
    model = value["model"]
    context = dict(
        context_sha256=model["context_sha256"],
        sample_kind=model["sample_kind"],
        station_mm=value["source_station_mm"],
    )
    centres = [f["source_origin_mm"][:2] for f in value["fixing_frames"]]
    native = dict(
        family=family,
        status="PASS",
        native_reload="PASS",
        scope="private-development",
        production_ready=False,
        source_recipe=dict(
            context,
            family=family,
            chair_code=value["source_chair_code"],
            base={"bolt_centres_twisted_mm": centres},
        ),
        fixing_proof=dict(
            model_sha256=model["model_sha256"],
            source_fixings=dict(
                placement=dict(
                    centres_source_mm=centres,
                    basis="recipe.base.bolt_centres_twisted_mm; used once",
                    recipe_sha256=model["fixing_recipe_sha256"],
                    source_twist_reapplied=False,
                ),
                head_rotation_degrees=0.0,
                random_export_parity=False,
                p_bolt_status="NOT_APPLICABLE_SOURCE_DISPATCH",
            ),
        ),
    )
    native["source_recipe"].update(value["source_branch"])
    return CatalogueChair(
        "invented-catalogue",
        family,
        "context-native-02",
        json.dumps(context),
        "invented-model",
        model["model_sha256"],
        model["catalogue_sha256"],
        tuple(
            CatalogueComponent(name, name, "", (0, 0, 0, 0, 0, 0, 1))
            for name in model["component_names"]
        ),
        (CatalogueBinding("invented-model", model["model_sha256"]),),
        ("Reference-only metadata double; no native model loaded.",),
        json.dumps({"native_record": native}),
    )


@contextmanager
def admitted_catalogue(prepared=None):
    """Replace file access only; actual application admission stays real."""
    values = {family: selection(family) for family in FAMILIES}
    if prepared is not None:
        values.update(prepared)
    reader = Mock(side_effect=lambda _path, family, **_kwargs: values[family])
    with (
        patch.object(chair_catalogue, "prepare_catalogue_chair", reader),
        patch.object(
            catalogue, "prepare_catalogue_chair", reader, create=True
        ),
    ):
        yield reader


def preview(source, factory=None, *, prepared=None):
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        admitted_catalogue(prepared),
    ):
        return getattr(binding, METHOD)(
            source.module,
            source.document,
            "TO-001",
            "invented-catalogue",
            factory or (lambda *args: args),
        )


def adapter_boundary():
    """Execute the actual adapter with existing inert full-frame observers."""
    boundary = block_adapter_boundary()
    path = ROOT / (
        "tracktemplate/adapters/freecad/chair_catalogue_placement_preview.py"
    )
    nodes = [
        node
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == FACTORY
    ]
    if len(nodes) != 1:
        raise AssertionError("Expected one combined TO crossing adapter")
    boundary.selections = {family: selection(family) for family in FAMILIES}
    boundary.namespace.update(
        prepare_turnout_crossing_catalogue=getattr(
            catalogue, "prepare_turnout_crossing_catalogue"
        ),
        verify_turnout_crossing_catalogue=getattr(
            catalogue, "verify_turnout_crossing_catalogue"
        ),
    )
    exec(
        compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"),
        boundary.namespace,
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


class TurnoutCrossingTests(unittest.TestCase):
    def near(self, actual, wanted):
        self.assertEqual(len(actual), len(wanted))
        for a, b in zip(actual, wanted):
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def refuse(self, source, *, prepared=None):
        factory = Mock()
        with self.assertRaises((ValueError, TypeError)):
            preview(source, factory, prepared=prepared)
        factory.assert_not_called()

    def test_fifty_frames_and_distinct_source_mounting_datum(self):
        groups = preview(source_case())[1]
        self.assertEqual(tuple(groups), FAMILIES)
        frames = scalars = 0
        for expected_row in rows():
            (value,) = groups[expected_row["family"]]
            self.assertIs(type(value), PairedChairPlacement)
            with self.assertRaises(FrozenInstanceError):
                value.position_id = "changed"
            self.assertEqual(
                value.position_id,
                expected_row["source_positions"][0]["position_id"],
            )
            for field in ("origin_mm", "x_axis", "y_axis"):
                self.near(getattr(value, field), expected_row["body"][field])
                scalars += len(expected_row["body"][field])
            frames += 1
            self.assertEqual(value.origin_mm[2], 0.8)
            constituents = expected_row["constituent_frames"]
            self.assertEqual(
                [c["source_index"] for c in constituents],
                list(range(len(constituents))),
            )
            self.assertEqual(
                [c["source_index"] for c in expected_row["fixing_frames"]],
                [1, 2, 3, 4],
            )
            sources = [
                (c["source_origin_mm"], c["source_angle_rad"], c["frame"])
                for c in constituents
            ]
            sources += [
                (c["source_origin_mm"], 0.0, c["frame"])
                for c in expected_row["fixing_frames"]
            ]
            for (x, y, z), angle, wanted in sources:
                origin = value.transform_point((-x, -y - 0.45, z + 149 / 60))
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
        self.assertEqual((frames, scalars), (50, 350))

    def test_all_records_exclusions_and_explicit_source_owners_survive(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        args = preview(source)
        self.assertEqual(len(args), 5)
        groups, receipt = args[1], args[3]
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["selected_crossing_count"], 4)
        self.assertEqual(receipt["represented_source_position_count"], 8)
        self.assertEqual(
            receipt["selected_family_counts"], dict.fromkeys(FAMILIES, 1)
        )
        pairs = {
            r["source_positions"][1]["position_id"]: r["source_positions"][0][
                "position_id"
            ]
            for r in rows()
        }
        self.assertEqual(receipt["shared_supports"], pairs)
        originals = {
            p["stable_chair_position_identity"]: p
            for p in before[0][2]["positions"]
        }
        chosen = set(pairs) | set(pairs.values())
        remaining = {
            p["stable_chair_position_identity"]: p
            for p in receipt["remaining_positions"]
        }
        self.assertEqual(len(remaining), 160)
        self.assertEqual(
            remaining, {k: v for k, v in originals.items() if k not in chosen}
        )
        self.assertTrue(
            set(expected()["provenance"]["excluded_position_ids"])
            <= set(remaining)
        )
        self.assertEqual(
            receipt["original_analytical_exclusions"],
            before[1]["analytical_only"],
        )
        self.assertEqual(receipt["retained_research_key_direction_sign"], 1)
        self.assertEqual(receipt["retained_research_key_offset_mm"], 0)
        for record, expected_row in zip(receipt["selected_positions"], rows()):
            owner, mate = expected_row["source_positions"]
            self.assertEqual(record["position_id"], owner["position_id"])
            self.assertEqual(record["source_rail_code"], 3)
            self.assertEqual(record["source_hand"], "LH")
            self.assertEqual(
                record["original_position"], originals[owner["position_id"]]
            )
            self.assertEqual(
                record["original_companion"], originals[mate["position_id"]]
            )
            self.assertEqual(
                record["source_chair_code"], expected_row["source_chair_code"]
            )
            for field in ("original_position", "original_companion"):
                self.assertIs(type(record[field]["key_direction_sign"]), int)
                self.assertEqual(record[field]["key_direction_sign"], 0)
            self.assertEqual(
                groups[expected_row["family"]][0].position_id,
                owner["position_id"],
            )
        self.assertEqual((source.context, source.plan), before)
        source.context[2]["positions"].reverse()
        reversed_args = preview(source)
        self.assertEqual(reversed_args[1], groups)
        self.assertEqual(reversed_args[3]["shared_supports"], pairs)
        receipt["selected_positions"][0]["original_companion"][
            "chair_code"
        ] = 99
        self.assertEqual(
            {
                p["stable_chair_position_identity"]: p
                for p in source.context[2]["positions"]
            },
            originals,
        )

    def test_fixed_configuration_profile_and_mounting_refusals(self):
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

    def test_each_identity_role_key_and_literal_branch_refuses(self):
        for expected_row in rows():
            for item in expected_row["source_positions"]:
                for field, value in (
                    ("parent_turnout_identity", "Other"),
                    ("rail_identity", "Other"),
                    ("rail_name", "other"),
                    ("rail_role", item["rail_name"]),
                    ("chair_code", True),
                    ("chair_code_label", "EF"),
                    ("deliberate_omission", True),
                    ("source_or_assumed_classification", "source-derived"),
                    ("key_direction_sign", True),
                    ("key_direction_sign", 1),
                    ("key_orientation", "fixed"),
                    ("special_assignment_deferred", 1),
                    ("stale_signature_state", True),
                    ("handedness", "Right-hand"),
                ):
                    if field == "rail_role" and value == item["rail_role"]:
                        continue
                    source = source_case()
                    position(source, item["position_id"])[field] = value
                    with self.subTest(
                        identity=item["position_id"], field=field
                    ):
                        self.refuse(source)
            for change in ("missing", "duplicate", "extra"):
                source = source_case()
                records = source.context[2]["positions"]
                item = position(
                    source, expected_row["source_positions"][1]["position_id"]
                )
                if change == "missing":
                    records.remove(item)
                elif change == "duplicate":
                    records.append(copy.deepcopy(item))
                else:
                    extra = copy.deepcopy(item)
                    extra["stable_chair_position_identity"] += "-extra"
                    records[-1] = extra
                with self.subTest(
                    family=expected_row["family"], change=change
                ):
                    self.refuse(source)
            for station in (
                math.nextafter(expected_row["source_station_mm"], -math.inf),
                math.nextafter(expected_row["source_station_mm"], math.inf),
            ):
                source = source_case()
                name = expected_row["timber_id"].split(":")[-1]
                selected_timber(source, name)["source_configuration"][
                    "local_x"
                ] = station
                for item in expected_row["source_positions"]:
                    position(source, item["position_id"])[
                        "source_configuration"
                    ]["timber"]["local_x"] = station
                next(t for t in source.layout if t["identifier"] == name)[
                    "x"
                ] = station
                with self.subTest(
                    family=expected_row["family"], station=station
                ):
                    self.refuse(source)

    def test_initial_host_and_nominal_timber_must_match_all_four_samples(self):
        for expected_row in rows():
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
                station = expected_row["host_basis"]["host_station_mm"]
                point, angle = source.host_frames[station]
                timber = selected_timber(
                    source, expected_row["timber_id"].split(":")[-1]
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
                else:
                    point.x = math.nan if change == "nonfinite" else True
                with self.subTest(
                    family=expected_row["family"], change=change
                ):
                    self.refuse(source)

    def test_eight_centres_and_twenty_four_record_path_checks(self):
        records = [(r, p) for r in rows() for p in r["source_positions"]]
        rail_ids = {p["rail_id"] for _, p in records}
        self.assertEqual(len(rail_ids), 4)
        checks = 0
        for value, item in records:
            near_y, far_y = SYNTHETIC_Y_BOUNDS[value["family"]]
            other_rows = [
                r
                for r in rows()
                if r["family"] != value["family"]
                and any(
                    p["rail_id"] == item["rail_id"]
                    for p in r["source_positions"]
                )
            ]
            self.assertEqual(len(other_rows), 1)
            other_near, other_far = SYNTHETIC_Y_BOUNDS[other_rows[0]["family"]]
            self.assertTrue(far_y < other_near or other_far < near_y)
            centre = item["canonical_input"]["centre_point"]
            self.assertTrue(800 < centre[0] < 900)
            self.assertTrue(near_y < centre[1] < far_y)
            for field in ("points", "gauge_face_points", "outer_face_points"):
                checks += 1
                source = source_case()
                rail = next(
                    r
                    for r in source.context[4]
                    if r["stable_identity"] == item["rail_id"]
                )
                # This shared path supports the other timber only.
                # The target centre and the other paths remain valid.
                rail[field] = [[850, other_near + 1], [850, other_far - 1]]
                with self.subTest(
                    identity=item["position_id"],
                    field=field,
                    supported_other=other_rows[0]["timber_id"],
                ):
                    self.refuse(source)
            middle_y = (near_y + far_y) / 2
            for centre in (
                [800, middle_y],
                [799, middle_y],
                [math.nan, middle_y],
            ):
                source = source_case()
                position(source, item["position_id"])["centre_point"] = centre
                with self.subTest(identity=item["position_id"], centre=centre):
                    self.refuse(source)
        self.assertEqual(checks, 24)
        for rail_id in sorted(rail_ids):
            # Preserve empty, outside and boundary-only path refusals.
            for field in ("points", "gauge_face_points", "outer_face_points"):
                for points in (
                    [],
                    [[780, 430], [790, 430]],
                    [[800, 400], [800, 460]],
                ):
                    source = source_case()
                    rail = next(
                        r
                        for r in source.context[4]
                        if r["stable_identity"] == rail_id
                    )
                    rail[field] = points
                    with self.subTest(rail=rail_id, field=field, path=points):
                        self.refuse(source)
            for change in ("name", "role", "missing", "duplicate"):
                source = source_case()
                rails = source.context[4]
                rail = next(
                    r for r in rails if r["stable_identity"] == rail_id
                )
                if change == "name":
                    rail["source_configuration"]["gauge_face"] = "other"
                elif change == "role":
                    rail["rail_role"] = "other"
                elif change == "missing":
                    rails.remove(rail)
                else:
                    rails.append(copy.deepcopy(rail))
                with self.subTest(rail=rail_id, change=change):
                    self.refuse(source)

    def test_all_four_application_model_and_semantic_guards(self):
        with admitted_catalogue() as reader:
            prepared = getattr(
                catalogue, "prepare_turnout_crossing_catalogue"
            )("invented-catalogue")
            self.assertEqual(prepared, tuple(selection(f) for f in FAMILIES))
            self.assertEqual(
                [call.args[1] for call in reader.call_args_list],
                list(FAMILIES),
            )
            getattr(catalogue, "verify_turnout_crossing_catalogue")(prepared)
        for family in FAMILIES:
            good = selection(family)
            for change in (
                "model",
                "catalogue",
                "run",
                "family",
                "context",
                "sample",
                "station",
                "code",
                "recipe",
                "fixing",
                "centres",
                "twist",
                "head-angle",
                "random",
                "p-bolt",
                "order",
                "duplicate",
                "count",
            ):
                item = good
                context, metadata = item.context, item.metadata
                native = metadata["native_record"]
                fixings = native["fixing_proof"]["source_fixings"]
                if change in ("model", "catalogue"):
                    item = replace(item, **{change + "_sha256": "0" * 64})
                elif change == "run":
                    item = replace(item, run="RH-X4-A")
                elif change == "family":
                    item = replace(item, label="BB")
                elif change == "context":
                    context["context_sha256"] = "0" * 64
                elif change == "sample":
                    context["sample_kind"] = "fixture_timber_X5-B"
                elif change == "station":
                    context["station_mm"] += 0.1
                elif change == "code":
                    native["source_recipe"]["chair_code"] = True
                elif change == "recipe":
                    native["source_recipe"]["context_sha256"] = "0" * 64
                elif change == "fixing":
                    fixings["placement"]["recipe_sha256"] = "0" * 64
                elif change == "centres":
                    fixings["placement"]["centres_source_mm"].reverse()
                elif change == "twist":
                    fixings["placement"]["source_twist_reapplied"] = True
                elif change == "head-angle":
                    fixings["head_rotation_degrees"] = 1
                elif change == "random":
                    fixings["random_export_parity"] = True
                elif change == "p-bolt":
                    fixings["p_bolt_status"] = "inserted"
                elif change == "order":
                    item = replace(
                        item, components=tuple(reversed(item.components))
                    )
                elif change == "duplicate":
                    item = replace(
                        item,
                        components=(item.components[1],) + item.components[1:],
                    )
                else:
                    item = replace(item, components=item.components[:-1])
                item = replace(
                    item,
                    context_json=json.dumps(context),
                    metadata_json=json.dumps(metadata),
                )
                with self.subTest(family=family, change=change):
                    self.refuse(source_case(), prepared={family: item})
            detached = good.context
            detached["context_sha256"] = "changed"
            self.assertNotEqual(good.context, detached)

    def test_late_source_complete_host_and_each_catalogue_refuse(self):
        for change in (
            "source",
            "plan",
            "point",
            "heading",
            "station",
            "total",
            "host-object",
            *FAMILIES,
        ):
            source = source_case()

            def create(*args):
                if change == "source":
                    source.context[2]["positions"][-1]["validation_status"] = (
                        "changed"
                    )
                elif change == "plan":
                    source.plan["analytical_only"][-1]["reason"] = "changed"
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
                if change in FAMILIES:
                    with admitted_catalogue(
                        {
                            change: replace(
                                selection(change), model_sha256="0" * 64
                            )
                        }
                    ):
                        args[4]()
                else:
                    args[4]()

            with self.subTest(change=change), self.assertRaises(ValueError):
                preview(source, create)

    def test_135_full_saved_frames_once_in_one_137_layer_preview(self):
        args = preview(source_case())
        boundary = adapter_boundary()
        with admitted_catalogue():
            result = adapter(boundary, args)
            boundary.materialise.assert_called_once()
            layers, report, verify = result.prepare()
            self.assertEqual((len(layers), len(result.specs)), (137, 137))
            self.assertEqual(
                report["contract_id"],
                "tracktemplate.private-catalogue-turnout-crossings.v1",
            )
            self.assertEqual(
                (
                    report["family_count"],
                    report["placement_count"],
                    report["component_count"],
                ),
                (4, 4, 135),
            )
            self.assertFalse(report["geometry_rebuilt"])
            self.assertFalse(report["production_geometry_authorized"])
            self.assertEqual(report["project_status"], "reference-only")
            start = 2
            for family in FAMILIES:
                value = row(family)
                report_row = report["families"][family]
                self.assertEqual(report_row["source_hand"], "LH")
                self.assertEqual(report_row["source_rail_code"], 3)
                self.assertEqual(report_row["excluded_source_components"], [])
                self.assertEqual(
                    report_row["placement"],
                    "source-paired-common-timber-frame.v1",
                )
                (placed,) = report_row["placements"]
                names = value["model"]["component_names"]
                self.assertEqual(
                    [c["source_name"] for c in placed["components"]], names
                )
                for index, (prototype, name) in enumerate(
                    zip(boundary.prototypes[family], names)
                ):
                    (child,) = layers[start + index].childShapes()
                    self.assertTrue(child.isPartner(prototype))
                    outer, saved = child.Placement
                    for field, actual in zip(
                        ("origin_mm", "x_axis", "y_axis"), outer
                    ):
                        self.near(actual, value["body"][field])
                    self.assertEqual(
                        saved, boundary.saved_tokens[family][index]
                    )
                    self.assertEqual(prototype.Placement, saved)
                    self.assertEqual(
                        placed["components"][index]["placement_identity"],
                        (
                            args[1][family][0].position_id,
                            selection(family).model_sha256,
                            name,
                        ),
                    )
                    self.assertTrue(
                        result.specs[start + index][0].startswith(family + "_")
                    )
                start += len(names)
            self.assertEqual(start, 137)
            verify(layers)
            result.verify()

    def test_wrong_reflected_doubled_or_saved_frame_failure_in_every_family(
        self,
    ):
        args = preview(source_case())
        start = 2
        for family in FAMILIES:
            count = row(family)["model"]["component_count"]
            for component in (0, count - 17, count - 16, count - 1):
                for change in ("wrong", "reflection", "double", "saved"):
                    boundary = adapter_boundary()
                    with admitted_catalogue():
                        result = adapter(boundary, args)
                        layers, _report, verify = result.prepare()
                        index = start + component
                        (original,) = layers[index].childShapes()
                        child = ShapeDouble(original)
                        outer, saved = child.Placement
                        if change == "wrong":
                            child.Placement = (
                                (
                                    (outer[0][0] + 1, *outer[0][1:]),
                                    outer[1],
                                    outer[2],
                                ),
                                saved,
                            )
                        elif change == "reflection":
                            child.Placement = (
                                (
                                    outer[0],
                                    outer[1],
                                    tuple(-v for v in outer[2]),
                                ),
                                saved,
                            )
                        elif change == "double":
                            child.Placement = outer, (outer, saved)
                        else:
                            child.Placement = outer, ("different-saved",)
                        layer = ShapeDouble(layers[index])
                        layer.children = (child,)
                        changed = (
                            *layers[:index],
                            layer,
                            *layers[index + 1 :],
                        )
                        with self.subTest(
                            family=family, component=component, change=change
                        ):
                            with self.assertRaises(ValueError):
                                verify(changed)
            start += count

    def test_adapter_rejects_forged_partial_and_wrong_owner_groups_early(self):
        original = preview(source_case())
        for family in FAMILIES:
            for change in (
                "empty",
                "extra",
                "duplicate",
                "wrong-type",
                "owner",
                "rail",
                "timber",
                "datum",
                "receipt",
                "companion",
                "key",
                "family",
                "source-rail",
                "model",
            ):
                args = copy.deepcopy(original[:4])
                groups, receipt = args[1], args[3]
                value = groups[family][0]
                record = next(
                    r
                    for r in receipt["selected_positions"]
                    if r["family"] == family
                )
                if change == "empty":
                    groups[family] = ()
                elif change == "extra":
                    groups["BB"] = (value,)
                elif change == "duplicate":
                    groups[family] = (value, value)
                elif change == "wrong-type":
                    groups[family] = (
                        S1Placement(
                            value.position_id,
                            value.rail_id,
                            value.timber_id,
                            value.origin_mm,
                            value.x_axis,
                            value.y_axis,
                        ),
                    )
                elif change in ("owner", "rail", "timber", "datum"):
                    field = {
                        "owner": "position_id",
                        "rail": "rail_id",
                        "timber": "timber_id",
                        "datum": "origin_mm",
                    }[change]
                    changed = (
                        (value.origin_mm[0], value.origin_mm[1], 0.9)
                        if change == "datum"
                        else "wrong"
                    )
                    groups[family] = (replace(value, **{field: changed}),)
                elif change == "receipt":
                    receipt["represented_source_position_count"] = True
                elif change == "companion":
                    (
                        record["original_position"],
                        record["original_companion"],
                    ) = (
                        record["original_companion"],
                        record["original_position"],
                    )
                elif change == "key":
                    record["original_position"]["key_direction_sign"] = 1
                elif change == "family":
                    record["family"] = "BB"
                elif change == "source-rail":
                    record["source_rail_code"] = 2
                else:
                    record["source_model_sha256"] = "0" * 64
                boundary = adapter_boundary()
                with self.subTest(family=family, change=change):
                    with (
                        admitted_catalogue(),
                        self.assertRaises((ValueError, TypeError)),
                    ):
                        adapter(boundary, (*args, original[4]))
                    boundary.materialise.assert_not_called()

    def test_one_lifecycle_all_four_late_verifiers_and_final_child_rollback(
        self,
    ):
        args = preview(source_case())
        for fault in (None, "source", *FAMILIES, "last-component"):
            runtime = PreviewRuntime()
            runtime.selection.preselected = True
            before = runtime.snapshots()
            baseline_mutations = len(runtime.app.mutations)
            boundary = adapter_boundary()
            boundary.materialise.side_effect = runtime.preview
            error = RuntimeError("late crossing " + str(fault))
            source_check = Mock(
                side_effect=error if fault == "source" else None
            )
            original_check = boundary.namespace["_verify_component"]
            stored_children, stored_compounds, stored_kinds = [], [], []

            def verify_component(actual, wanted, **kwargs):
                if (
                    "openTransaction"
                    in runtime.app.mutations[baseline_mutations:]
                ):
                    if actual.childShapes():
                        stored_compounds.append(actual)
                        stored_kinds.append("compound")
                    else:
                        stored_children.append(actual)
                        stored_kinds.append("component")
                        if (
                            fault == "last-component"
                            and len(stored_children) == 135
                        ):
                            self.assertTrue(
                                actual.isPartner(boundary.prototypes["DD"][-1])
                            )
                            raise error
                return original_check(actual, wanted, **kwargs)

            boundary.namespace["_verify_component"] = verify_component
            with (
                admitted_catalogue() as reader,
                patch.dict(sys.modules, {"FreeCADGui": runtime.gui}),
            ):
                if fault in FAMILIES:

                    def read(_path, family, **_kwargs):
                        if (
                            family == fault
                            and "openTransaction"
                            in runtime.app.mutations[baseline_mutations:]
                        ):
                            raise error
                        return selection(family)

                    reader.side_effect = read
                if fault is None:
                    result = adapter(boundary, (*args[:4], source_check))
                    preview_doc = runtime.app.documents[
                        result["document_name"]
                    ]
                    self.assertEqual(len(preview_doc.Objects), 137)
                    self.assertIs(runtime.app.ActiveDocument, preview_doc)
                    self.assertIn("commitTransaction", runtime.app.mutations)
                    self.assertNotIn("abortTransaction", runtime.app.mutations)
                    source_check.assert_called_once()
                else:
                    with self.assertRaises(RuntimeError) as caught:
                        adapter(boundary, (*args[:4], source_check))
                    self.assertIs(caught.exception, error)
                    self.assertEqual(
                        set(runtime.app.documents), {"Source", "Witness"}
                    )
                    self.assertIs(runtime.app.ActiveDocument, runtime.source)
                    self.assertIn("abortTransaction", runtime.app.mutations)
                    self.assertNotIn(
                        "commitTransaction", runtime.app.mutations
                    )
                self.assertIs(runtime.app.documents["Source"], runtime.source)
                self.assertIs(
                    runtime.app.documents["Witness"], runtime.witness
                )
                self.assertEqual(
                    tuple(runtime.witness.Objects), runtime.initial_objects
                )
                self.assertEqual(runtime.snapshots(), before)
                self.assertEqual(len(stored_children), 135)
                self.assertEqual(len(stored_compounds), 135)
                self.assertEqual(stored_kinds, ["compound", "component"] * 135)

    def test_fourth_family_preparation_failure_precedes_native_mutation(self):
        args = preview(source_case())
        runtime = PreviewRuntime()
        before = runtime.snapshots()
        registry = runtime.app.listDocuments()
        mutations = tuple(runtime.app.mutations)
        boundary = adapter_boundary()
        boundary.materialise.side_effect = runtime.preview
        original_import = boundary.namespace["_import_components"]
        error = RuntimeError("fourth crossing import failed")
        called = []

        def import_components(prepared):
            called.append(prepared.label)
            if prepared.label == "DD":
                raise error
            return original_import(prepared)

        boundary.namespace["_import_components"] = import_components
        with (
            admitted_catalogue(),
            patch.dict(sys.modules, {"FreeCADGui": runtime.gui}),
        ):
            with self.assertRaises(RuntimeError) as caught:
                adapter(boundary, args)
        self.assertIs(caught.exception, error)
        self.assertEqual(called, list(FAMILIES))
        self.assertEqual(runtime.app.listDocuments(), registry)
        self.assertEqual(tuple(runtime.app.mutations), mutations)
        self.assertEqual(runtime.snapshots(), before)

    def test_session_optional_factory_preserves_explicit_call(self):
        from tracktemplate import api
        from validate_phase9b_l1_reference_preview import _session

        original = _session()
        self.assertIsNone(getattr(original, "_" + PORT))
        factory = object()
        session = transition_workflow.ModularCoreLayoutWorkflowSession(
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
                    "invented-catalogue",
                    factory,
                ),
            )
            return "receipt"

        with patch.object(binding, METHOD, operation):
            self.assertEqual(
                getattr(session, METHOD)(
                    "document", "TO-001", "invented-catalogue"
                ),
                "receipt",
            )
        parameter = inspect.signature(
            transition_workflow.load_modular_transition_workflow_session,
        ).parameters[PORT]
        self.assertIsNone(parameter.default)
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutCrossingTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
