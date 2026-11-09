"""Check one fixed LH TO ZY assembly without FreeCAD or Qt.

Thirteen independent source frames provide 91 numeric expectations.
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
    chair_crossing_zy_catalogue as catalogue,
)
from tracktemplate.application.chair_catalogue import (  # noqa: E402
    CatalogueBinding,
    CatalogueChair,
    CatalogueComponent,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_crossing_zy_placement as binding,
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

FRAME_SHA = "ba36ffd49820a0a032d391e63fe0327a7df37c5a19f192cd183c13740462b7c4"
METHOD = "preview_private_catalogue_turnout_zy_chairs"
FACTORY = "create_private_catalogue_turnout_zy_preview"
PORT = "private_catalogue_turnout_zy_preview_factory"
SENTINEL = "Phase 9B TO-001 LH ZY standalone validation passed"


def expected():
    path = ROOT / "tests/fixtures/phase9b-to-zy-source-frames.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FRAME_SHA
    return json.loads(raw)


def row():
    return expected()["positions"][0]


def position(source, identity):
    return next(
        p
        for p in source.context[2]["positions"]
        if p["stable_chair_position_identity"] == identity
    )


def source_case():
    """Keep 168 accounted records and use only invented support paths.

    The exact two selected records, host anchor and nominal timber basis
    come from independent numeric inputs. Other records and finite paths
    are test doubles. Their preservation does not prove actual rail fit.
    """
    source = block_source_case()
    value = row()
    analysis, rails, timbers = (
        source.context[2],
        source.context[4],
        source.context[5],
    )
    template = copy.deepcopy(selected_record(source))
    timber = copy.deepcopy(selected_timber(source))
    timber.update(copy.deepcopy(value["nominal_timber_basis"]))
    timber.update(
        stable_identity=value["timber_id"],
        identifier="X1-Z",
        prototype_reference="X1-Z",
        section="crossing wing front",
        outline_polygon=(
            [[820 + i * 10, 380] for i in range(5)]
            + [[870, 380 + i * 7.5] for i in range(4)]
            + [[870 - i * 10, 410] for i in range(5)]
            + [[820, 410 - i * 7.5] for i in range(4)]
        ),
    )
    timbers.append(timber)
    nominal = timber["source_configuration"]
    source.layout.append(
        dict(
            identifier="X1-Z",
            x=nominal["local_x"],
            near_y=nominal["local_near_y"],
            far_y=nominal["local_far_y"],
            length_prototype_inches=nominal["length_prototype_inches"],
        )
    )
    basis = value["host_basis"]
    source.host_frames[basis["host_station_mm"]] = (
        SimpleNamespace(
            x=basis["host_point_mm"][0], y=basis["host_point_mm"][1]
        ),
        basis["heading_radians"],
    )
    records = []
    for item in value["source_positions"]:
        rail_name = item["rail_id"].split(":rail:")[1].replace("-", " ")
        rail = next(
            (r for r in rails if r["stable_identity"] == item["rail_id"]), None
        )
        if rail is None:
            rail = {"stable_identity": item["rail_id"]}
            rails.append(rail)
        rail.update(
            name=rail_name,
            rail_role=rail_name,
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
            rail[field] = [[810.0, 395.0], [880.0, 395.0]]
        record = copy.deepcopy(template)
        record.update(copy.deepcopy(item["canonical_input"]))
        record.update(
            stable_chair_position_identity=item["position_id"],
            rail_identity=item["rail_id"],
            rail_name=rail_name,
            rail_role=rail_name,
            timber_identity=value["timber_id"],
            prototype_timber_identifier="X1-Z",
            timber_identifier="X1-Z",
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
    # These unselected identities are invented preservation witnesses only.
    for timber_name, rail_name in (
        ("X1-Z", "main-side-stock-rail"),
        ("X1-Z", "main-side-check-rail"),
        ("X1-Z", "turnout-side-stock-rail"),
        ("X1-Z", "turnout-side-check-rail"),
        ("X9-F", "turnout-side-stock-rail"),
    ):
        record = copy.deepcopy(template)
        record.update(
            stable_chair_position_identity=(
                "TO-001:chair:to-001-timber-"
                + timber_name.lower()
                + ":"
                + rail_name
            ),
            rail_identity="TO-001:rail:" + rail_name,
            rail_name=rail_name.replace("-", " "),
            timber_identity="TO-001:timber:" + timber_name,
            prototype_timber_identifier=timber_name,
            timber_identifier=timber_name,
        )
        records.append(record)
    for record in records:
        index = next(
            i
            for i, p in enumerate(analysis["positions"])
            if p["stable_chair_position_identity"].startswith(
                "invented-unselected-"
            )
        )
        old_id = analysis["positions"][index]["stable_chair_position_identity"]
        analysis["positions"][index] = record
        exclusion = next(
            p
            for p in source.plan["analytical_only"]
            if p["chair_position_identity"] == old_id
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
    return source


def selection():
    """Return immutable metadata and inert components, not a model."""
    value = row()
    model = expected()["provenance"]["model"]
    context = dict(
        context_sha256=model["context_sha256"],
        sample_kind=model["sample_kind"],
        station_mm=value["source_station_mm"],
    )
    centres = [f["source_origin_mm"][:2] for f in value["fixing_frames"]]
    native = dict(
        family="ZY",
        status="PASS",
        native_reload="PASS",
        scope="private-development",
        production_ready=False,
        source_recipe=dict(
            context,
            family="ZY",
            chair_code=21,
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
    return CatalogueChair(
        "invented-catalogue",
        "ZY",
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
    """Replace file reads, leaving the proposed application guard real."""
    prepared = selection() if prepared is None else prepared
    reader = Mock(return_value=prepared)
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
    """Reuse the full-frame, nonidentity prototype observer unchanged."""
    boundary = block_adapter_boundary()
    path = ROOT / (
        "tracktemplate/adapters/freecad/chair_catalogue_placement_preview.py"
    )
    nodes = [
        n
        for n in ast.parse(path.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == FACTORY
    ]
    if len(nodes) != 1:
        raise AssertionError("Expected one TO ZY adapter entry")
    boundary.selections = {"ZY": selection()}
    boundary.namespace.update(
        prepare_turnout_zy_catalogue=getattr(
            catalogue, "prepare_turnout_zy_catalogue"
        ),
        verify_turnout_zy_catalogue=getattr(
            catalogue, "verify_turnout_zy_catalogue"
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


class TurnoutZYTests(unittest.TestCase):
    def near(self, actual, wanted):
        self.assertEqual(len(actual), len(wanted))
        for a, b in zip(actual, wanted):
            # Existing source-comparison arithmetic budget, not fit tolerance.
            budget = 128 * sys.float_info.epsilon * max(1000, abs(a), abs(b))
            self.assertLessEqual(abs(a - b), budget)

    def refuse(self, source, *, prepared=None):
        factory = Mock()
        with self.assertRaises((ValueError, TypeError)):
            preview(source, factory, prepared=prepared)
        factory.assert_not_called()

    def test_thirteen_source_frames_and_distinct_mounting_datum(self):
        (value,) = preview(source_case())[1]
        self.assertIs(type(value), PairedChairPlacement)
        with self.assertRaises(FrozenInstanceError):
            value.position_id = "changed"
        expected_row = row()
        frames, scalars = 0, 0
        for field in ("origin_mm", "x_axis", "y_axis"):
            self.near(getattr(value, field), expected_row["body"][field])
            scalars += len(expected_row["body"][field])
        frames += 1
        self.assertEqual(value.origin_mm[2], 0.8)
        self.assertEqual(
            [c["source_index"] for c in expected_row["constituent_frames"]],
            list(range(8)),
        )
        self.assertEqual(
            [c["source_index"] for c in expected_row["fixing_frames"]],
            [1, 2, 3, 4],
        )
        sources = [
            (c["source_origin"], c["source_angle_rad"], c["frame"])
            for c in expected_row["constituent_frames"]
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
        self.assertEqual((frames, scalars), (13, 91))

    def test_one_assembly_two_records_and_all_original_exclusions_survive(
        self,
    ):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        args = preview(source)
        self.assertEqual(len(args), 5)
        (value,), receipt = args[1], args[3]
        owner, mate = row()["source_positions"]
        self.assertEqual(value.position_id, owner["position_id"])
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["selected_zy_count"], 1)
        self.assertEqual(receipt["represented_source_position_count"], 2)
        self.assertEqual(receipt["selected_family_counts"], {"ZY": 1})
        self.assertEqual(
            receipt["shared_supports"],
            {
                mate["position_id"]: owner["position_id"],
            },
        )
        self.assertEqual(len(receipt["remaining_positions"]), 166)
        remaining = {
            p["stable_chair_position_identity"]: p
            for p in receipt["remaining_positions"]
        }
        originals = {
            p["stable_chair_position_identity"]: p
            for p in before[0][2]["positions"]
        }
        self.assertEqual(
            set(remaining),
            set(originals)
            - {
                owner["position_id"],
                mate["position_id"],
            },
        )
        self.assertTrue(all(v == originals[k] for k, v in remaining.items()))
        self.assertEqual(
            receipt["original_analytical_exclusions"],
            before[1]["analytical_only"],
        )
        self.assertEqual(receipt["retained_research_key_direction_sign"], 1)
        self.assertEqual(receipt["retained_research_key_offset_mm"], 0)
        (record,) = receipt["selected_positions"]
        self.assertEqual(
            record["original_position"], originals[owner["position_id"]]
        )
        self.assertEqual(
            record["original_companion"], originals[mate["position_id"]]
        )
        self.assertEqual(record["source_hand"], "LH")
        for field in ("original_position", "original_companion"):
            self.assertIs(type(record[field]["key_direction_sign"]), int)
            self.assertEqual(record[field]["key_direction_sign"], 0)
        self.assertEqual((source.context, source.plan), before)
        record["original_companion"]["chair_code"] = 99
        self.assertEqual((source.context, source.plan), before)

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

    def test_each_identity_classification_key_and_source_branch_refuses(self):
        for item in row()["source_positions"]:
            for field, value in (
                ("parent_turnout_identity", "Other"),
                ("rail_identity", "Other"),
                ("chair_code", True),
                ("chair_code_label", "XN"),
                ("deliberate_omission", True),
                ("source_or_assumed_classification", "source-derived"),
                ("key_direction_sign", True),
                ("key_direction_sign", 1),
                ("key_orientation", "fixed"),
                ("special_assignment_deferred", 1),
                ("stale_signature_state", True),
                ("handedness", "Right-hand"),
            ):
                source = source_case()
                position(source, item["position_id"])[field] = value
                with self.subTest(identity=item["position_id"], field=field):
                    self.refuse(source)
        for change in ("missing", "duplicate", "extra"):
            source = source_case()
            rows = source.context[2]["positions"]
            item = position(
                source, row()["source_positions"][1]["position_id"]
            )
            if change == "missing":
                rows.remove(item)
            elif change == "duplicate":
                rows.append(copy.deepcopy(item))
            else:
                extra = copy.deepcopy(item)
                extra["stable_chair_position_identity"] += "-extra"
                rows[-1] = extra
            with self.subTest(change=change):
                self.refuse(source)
        for station in (
            math.nextafter(row()["source_station_mm"], -math.inf),
            math.nextafter(row()["source_station_mm"], math.inf),
        ):
            source = source_case()
            timber = selected_timber(source, "X1-Z")
            timber["source_configuration"]["local_x"] = station
            for item in row()["source_positions"]:
                position(source, item["position_id"])["source_configuration"][
                    "timber"
                ]["local_x"] = station
            next(t for t in source.layout if t["identifier"] == "X1-Z")[
                "x"
            ] = station
            with self.subTest(station=station):
                self.refuse(source)

    def test_fixed_initial_host_and_nominal_timber_refuse_even_if_stable(self):
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
            station = row()["host_basis"]["host_station_mm"]
            point, angle = source.host_frames[station]
            timber = selected_timber(source, "X1-Z")
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
            with self.subTest(change=change):
                self.refuse(source)

    def test_both_centres_and_all_six_finite_named_paths_are_required(self):
        for item in row()["source_positions"]:
            for field in ("gauge_face_points", "points", "outer_face_points"):
                for points in (
                    [],
                    [[800, 395], [810, 395]],
                    [[820, 380], [870, 380]],
                ):
                    source = source_case()
                    rail = next(
                        r
                        for r in source.context[4]
                        if r["stable_identity"] == item["rail_id"]
                    )
                    rail[field] = points
                    with self.subTest(
                        rail=item["rail_id"], field=field, points=points
                    ):
                        self.refuse(source)
            for centre in ([820, 395], [819, 395], [math.nan, 395]):
                source = source_case()
                position(source, item["position_id"])["centre_point"] = centre
                with self.subTest(identity=item["position_id"], centre=centre):
                    self.refuse(source)
            for change in ("name", "missing", "duplicate"):
                source = source_case()
                rails = source.context[4]
                rail = next(
                    r for r in rails if r["stable_identity"] == item["rail_id"]
                )
                if change == "name":
                    rail["source_configuration"]["gauge_face"] = "other"
                elif change == "missing":
                    rails.remove(rail)
                else:
                    rails.append(copy.deepcopy(rail))
                with self.subTest(rail=item["rail_id"], change=change):
                    self.refuse(source)

    def test_application_model_context_fixing_and_component_guards(self):
        good = selection()
        with admitted_catalogue(good) as reader:
            prepared = getattr(catalogue, "prepare_turnout_zy_catalogue")(
                "invented-catalogue"
            )
            self.assertEqual(prepared, good)
            reader.assert_called_with(
                "invented-catalogue", "ZY", run="context-native-02"
            )
            getattr(catalogue, "verify_turnout_zy_catalogue")(prepared)
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
                item = replace(item, run="RH-X1-Z")
            elif change == "family":
                item = replace(item, label="XN")
            elif change == "context":
                context["context_sha256"] = "0" * 64
            elif change == "sample":
                context["sample_kind"] = "fixture_timber_X2-Y"
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
            with self.subTest(change=change):
                self.refuse(source_case(), prepared=item)
        detached = good.context
        detached["context_sha256"] = "changed"
        self.assertNotEqual(good.context, detached)

    def test_late_complete_host_source_and_catalogue_changes_refuse(self):
        for change in (
            "source",
            "point",
            "heading",
            "station",
            "total",
            "host-object",
            "catalogue",
        ):
            source = source_case()

            def create(*args):
                if change == "source":
                    source.context[2]["positions"][-1]["validation_status"] = (
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
                if change == "catalogue":
                    with admitted_catalogue(
                        replace(
                            selection(),
                            model_sha256="0" * 64,
                        )
                    ):
                        args[4]()
                else:
                    args[4]()

            with self.subTest(change=change), self.assertRaises(ValueError):
                preview(source, create)

    def test_adapter_33_full_saved_placements_once_and_35_layers(self):
        args = preview(source_case())
        boundary = adapter_boundary()
        with admitted_catalogue():
            result = adapter(boundary, args)
            boundary.materialise.assert_called_once()
            layers, report, verify = result.prepare()
            self.assertEqual((len(layers), len(result.specs)), (35, 35))
            self.assertEqual(
                report["contract_id"],
                "tracktemplate.private-catalogue-turnout-zy.v1",
            )
            self.assertEqual(
                (
                    report["family_count"],
                    report["placement_count"],
                    report["component_count"],
                ),
                (1, 1, 33),
            )
            self.assertFalse(report["geometry_rebuilt"])
            self.assertFalse(report["production_geometry_authorized"])
            self.assertEqual(report["project_status"], "reference-only")
            family = report["families"]["ZY"]
            self.assertEqual(family["source_hand"], "LH")
            self.assertEqual(family["source_rail_code"], 3)
            self.assertEqual(family["excluded_source_components"], [])
            self.assertEqual(
                family["placement"], "source-paired-common-timber-frame.v1"
            )
            (placed,) = family["placements"]
            names = expected()["provenance"]["model"]["component_names"]
            self.assertEqual(
                [c["source_name"] for c in placed["components"]], names
            )
            (value,) = args[1]
            for index, (prototype, name) in enumerate(
                zip(
                    boundary.prototypes["ZY"],
                    names,
                )
            ):
                (child,) = layers[index + 2].childShapes()
                self.assertTrue(child.isPartner(prototype))
                outer, saved = child.Placement
                for field, actual in zip(
                    ("origin_mm", "x_axis", "y_axis"), outer
                ):
                    self.near(actual, row()["body"][field])
                self.assertEqual(saved, boundary.saved_tokens["ZY"][index])
                self.assertEqual(prototype.Placement, saved)
                self.assertEqual(
                    placed["components"][index]["placement_identity"],
                    (value.position_id, selection().model_sha256, name),
                )
            verify(layers)
            result.verify()

    def test_wrong_reflected_double_saved_frames_and_last_part_are_rejected(
        self,
    ):
        args = preview(source_case())
        for component in (0, 16, 17, 32):
            for change in ("wrong", "reflection", "double", "saved"):
                boundary = adapter_boundary()
                with admitted_catalogue():
                    result = adapter(boundary, args)
                    layers, _report, verify = result.prepare()
                    index = component + 2
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
                            (outer[0], outer[1], tuple(-v for v in outer[2])),
                            saved,
                        )
                    elif change == "double":
                        child.Placement = outer, (outer, saved)
                    else:
                        child.Placement = outer, ("different-saved",)
                    layer = ShapeDouble(layers[index])
                    layer.children = (child,)
                    changed = (*layers[:index], layer, *layers[index + 1 :])
                    with self.subTest(component=component, change=change):
                        with self.assertRaises(ValueError):
                            verify(changed)

    def test_forged_adapter_records_refuse_before_materialisation(self):
        original = preview(source_case())
        for change in (
            "empty",
            "duplicate",
            "type",
            "reflected",
            "identity",
            "mate",
            "family",
            "count",
            "key",
            "no-verifier",
        ):
            values, receipt = copy.deepcopy((original[1], original[3]))
            verify = original[4]
            if change == "empty":
                values = ()
            elif change == "duplicate":
                values += values
            elif change == "type":
                values = (S1Placement(**vars(values[0])),)
            elif change == "reflected":
                object.__setattr__(
                    values[0], "y_axis", tuple(-v for v in values[0].y_axis)
                )
            elif change == "identity":
                values = (replace(values[0], position_id="Other"),)
            elif change == "mate":
                receipt["shared_supports"] = {}
            elif change == "family":
                receipt["selected_positions"][0]["family"] = "XN"
            elif change == "count":
                receipt["selected_zy_count"] = True
            elif change == "key":
                receipt["retained_research_key_direction_sign"] = 0
            else:
                verify = None
            boundary = adapter_boundary()
            with admitted_catalogue(), self.subTest(change=change):
                with self.assertRaises((ValueError, TypeError)):
                    adapter(
                        boundary,
                        (original[0], values, original[2], receipt, verify),
                    )
                boundary.materialise.assert_not_called()

    def test_shared_lifecycle_success_and_late_failure_roll_back_owned_only(
        self,
    ):
        args = preview(source_case())
        for fault in (None, "source", "catalogue", "last-component"):
            runtime = PreviewRuntime()
            runtime.selection.preselected = True
            before = runtime.snapshots()
            baseline_mutations = len(runtime.app.mutations)
            boundary = adapter_boundary()
            boundary.materialise.side_effect = runtime.preview
            error = RuntimeError("late ZY " + str(fault))
            source_check = Mock()
            if fault == "source":
                source_check.side_effect = error
            original_component_check = boundary.namespace["_verify_component"]
            stored_checks = []
            stored_compound_checks = []
            stored_kinds = []

            def verify_component(actual, wanted, **kwargs):
                if (
                    "openTransaction"
                    in runtime.app.mutations[baseline_mutations:]
                ):
                    if actual.childShapes():
                        stored_compound_checks.append(actual)
                        stored_kinds.append("compound")
                    else:
                        stored_checks.append(actual)
                        stored_kinds.append("component")
                        if (
                            fault == "last-component"
                            and len(stored_checks) == 33
                        ):
                            self.assertTrue(actual.isPartner(
                                boundary.prototypes["ZY"][-1]
                            ))
                            raise error
                return original_component_check(actual, wanted, **kwargs)

            boundary.namespace["_verify_component"] = verify_component
            with (
                admitted_catalogue() as reader,
                patch.dict(sys.modules, {"FreeCADGui": runtime.gui}),
            ):
                if fault == "catalogue":

                    def read(*_args, **_kwargs):
                        if (
                            "openTransaction"
                            in runtime.app.mutations[baseline_mutations:]
                        ):
                            raise error
                        return selection()

                    reader.side_effect = read
                new_args = (*args[:4], source_check)
                if fault is None:
                    result = adapter(boundary, new_args)
                    preview_doc = runtime.app.documents[
                        result["document_name"]
                    ]
                    self.assertEqual(len(preview_doc.Objects), 35)
                    self.assertIs(runtime.app.ActiveDocument, preview_doc)
                    self.assertIn("commitTransaction", runtime.app.mutations)
                    self.assertNotIn("abortTransaction", runtime.app.mutations)
                    source_check.assert_called_once()
                else:
                    with self.assertRaises(RuntimeError) as caught:
                        adapter(boundary, new_args)
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
                self.assertEqual(len(stored_checks), 33)
                self.assertEqual(len(stored_compound_checks), 33)
                self.assertEqual(stored_kinds, ["compound", "component"] * 33)

    def test_preparation_failure_precedes_document_and_transaction(self):
        args = preview(source_case())
        runtime = PreviewRuntime()
        before = runtime.snapshots()
        original_registry = runtime.app.listDocuments()
        original_mutations = tuple(runtime.app.mutations)
        boundary = adapter_boundary()
        boundary.materialise.side_effect = runtime.preview
        error = RuntimeError("ZY retained component import failed")
        boundary.namespace["_import_components"] = Mock(side_effect=error)
        with (
            admitted_catalogue(),
            patch.dict(
                sys.modules,
                {"FreeCADGui": runtime.gui},
            ),
        ):
            with self.assertRaises(RuntimeError) as caught:
                adapter(boundary, args)
        self.assertIs(caught.exception, error)
        self.assertEqual(runtime.app.listDocuments(), original_registry)
        self.assertEqual(tuple(runtime.app.mutations), original_mutations)
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
    result = unittest.main(exit=False, verbosity=2).result
    if result.wasSuccessful() and result.testsRun == 14 and not result.skipped:
        print(SENTINEL, flush=True)
    else:
        raise SystemExit(1)
