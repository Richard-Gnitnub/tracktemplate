"""Check two fixed TO endpoint exclusions without native geometry.

Invented continuous paths exercise source accounting, never physical fit.
The independent LH XA fixture supplies station, context and owner facts.
Existing inert doubles retain the real application and adapter boundaries.
Source-informed comparison: GPL-3.0-or-later; see NOTICE.md.
"""

import copy
import importlib
import inspect
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_crossing_pair_placement as binding,
    chair_reference_preview,
    transition_workflow,
)
from validate_chair_preview_activation import PreviewRuntime  # noqa: E402
from validate_phase9b_turnout_crossing_chairs import (  # noqa: E402
    FAMILIES,
    METHOD,
    adapter,
    adapter_boundary,
    admitted_catalogue,
    position,
    rows,
    source_case as cohort_source_case,
)

FIELDS = ("points", "gauge_face_points", "outer_face_points")
NAMES = ("main-side wing knuckle", "turnout-side wing knuckle")
CONTEXT = "36546313e1234ab7a926419c482c2136a20d2ab7e52a9cd74c88d9de59e7a4e6"
STATION = 277.23290043721454
KIND = "finite-segment-endpoint-not-selected-source-chair"
SENTINEL = "PASS: fixed TO source endpoint exclusions; geometry unchanged"


def identity(name):
    return "TO-001:chair:to-001-timber-x3-x:" + name.replace(" ", "-")


def rail(source, name):
    return next(item for item in source.context[4] if item["name"] == name)


def fixture():
    """Replace two invented unresolved rows; keep 168 unique records."""
    source = cohort_source_case()
    for name in NAMES:
        wing_name = name.replace("knuckle", "rail")
        wing = rail(source, wing_name)
        record = copy.deepcopy(position(source, identity(wing_name)))
        knuckle = copy.deepcopy(wing)
        knuckle.update(
            stable_identity="TO-001:rail:" + name.replace(" ", "-"),
            name=name, rail_role="wing rail knuckle",
        )
        knuckle["source_configuration"].update(
            gauge_face=name + " gauge face", outer_face=name + " outer face",
        )
        for field, offset in zip(FIELDS, (0.0, -0.45, 0.45)):
            # Both XA and AA retain support on this shared continuing rail.
            wing[field] = [[850 + offset, 412.0], [850 + offset, 460.0]]
            knuckle[field] = [[850 + offset, 409.0], [850 + offset, 412.0]]
        record.update(
            stable_chair_position_identity=identity(name),
            rail_identity=knuckle["stable_identity"], rail_name=name,
            rail_role="wing rail knuckle", chair_code=22,
            chair_code_label="XN", chair_family="knuckle-region support",
            chair_subtype=(
                "REA XN knuckle-chair assignment awaiting detailed "
                "special-chair assignment"
            ),
            centre_point=copy.deepcopy(knuckle["points"][-1]),
        )
        record["source_configuration"]["rail"] = copy.deepcopy(
            knuckle["source_configuration"],
        )
        source.context[4].append(knuckle)
        records = source.context[2]["positions"]
        index = next(i for i, item in enumerate(records)
                     if item["stable_chair_position_identity"].startswith(
                         "invented-unselected-"))
        old = records[index]["stable_chair_position_identity"]
        records[index] = record
        exclusion = next(item for item in source.plan["analytical_only"]
                         if item["chair_position_identity"] == old)
        exclusion.update(
            chair_position_identity=identity(name),
            rail_identity=record["rail_identity"],
            timber_identity=record["timber_identity"], chair_label="XN",
            chair_family="knuckle-region support", deliberate_omission=False,
            unresolved_special=True,
        )
    return source


def indexed(source):
    """Supply independent witnesses without deriving them from the product."""
    positions = {p["stable_chair_position_identity"]: p
                 for p in source.context[2]["positions"]}
    rails = {r["stable_identity"]: r for r in source.context[4]}
    timbers = {t["stable_identity"]: t for t in source.context[5]}
    selected, shared = [], {}
    for value in rows():
        owner, mate = value["source_positions"]
        shared[mate["position_id"]] = owner["position_id"]
        selected.append({
            "position_id": owner["position_id"], "family": value["family"],
            "source_hand": "LH", "source_rail_code": 3,
            "prototype_timber_identifier": value["timber_id"].split(":")[-1],
            "source_chair_code": value["source_chair_code"],
            "source_station_mm": value["source_station_mm"],
            "source_context_sha256": value["model"]["context_sha256"],
            "source_model_sha256": value["model"]["model_sha256"],
            "fixing_recipe_sha256": value["model"]["fixing_recipe_sha256"],
            "original_position": copy.deepcopy(positions[owner["position_id"]]),
            "original_companion": copy.deepcopy(positions[mate["position_id"]]),
            "physical_fit": "NOT_PROVED",
        })
    return positions, rails, timbers, selected, shared


def qualify(data):
    module = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_endpoint_exclusions",
    )
    return module.qualify_turnout_knuckle_exclusions(*data)


def preview(source, factory=None, **options):
    with patch.dict(sys.modules, {"FreeCAD": source.app}), admitted_catalogue():
        return getattr(binding, METHOD)(
            source.module, source.document, "TO-001", "invented-catalogue",
            factory or (lambda *args: args), **options,
        )


class TurnoutEndpointTests(unittest.TestCase):
    def test_fixture_and_default_keep_all_original_source_records(self):
        source = fixture()
        before = copy.deepcopy((source.context, source.plan))
        records = source.context[2]["positions"]
        self.assertEqual(len(records), 168)
        self.assertEqual(len({p["stable_chair_position_identity"]
                              for p in records}), 168)
        default = preview(source)
        self.assertEqual(len(default[3]["remaining_positions"]), 160)
        self.assertNotIn("source_endpoint_exclusions", default[3])
        self.assertEqual((source.context, source.plan), before)

    def test_strict_boolean_refuses_before_source_or_factory_access(self):
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(value=value), patch.object(
                chair_reference_preview, "_open_source_context",
            ) as opened:
                factory = Mock()
                with self.assertRaises(ValueError):
                    getattr(binding, METHOD)(
                        object(), object(), "TO-001", "unused", factory,
                        classify_knuckle_exclusions=value,
                    )
                opened.assert_not_called()
                factory.assert_not_called()

    def test_session_keyword_only_forwarding_preserves_old_call(self):
        method = getattr(
            transition_workflow.ModularCoreLayoutWorkflowSession, METHOD,
        )
        for operation in (method, getattr(binding, METHOD)):
            parameter = inspect.signature(operation).parameters[
                "classify_knuckle_exclusions"]
            self.assertIs(parameter.default, False)
            self.assertEqual(parameter.kind, parameter.KEYWORD_ONLY)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_turnout_crossing_preview_factory=object(),
        )
        for options in ({}, {"classify_knuckle_exclusions": False},
                        {"classify_knuckle_exclusions": True}):
            with patch.object(binding, METHOD, return_value="receipt") as op:
                self.assertEqual(method(session, "doc", "TO-001", "catalogue",
                                        **options), "receipt")
                self.assertEqual(op.call_args.args, (
                    session.module, "doc", "TO-001", "catalogue",
                    session._private_catalogue_turnout_crossing_preview_factory,
                ))
                self.assertEqual(op.call_args.kwargs,
                                 options if options.get(
                                     "classify_knuckle_exclusions") else {})
        for value in (None, 0, 1, "true"):
            session.routing_record.reset_mock()
            with self.subTest(value=value), patch.object(binding, METHOD) as op:
                with self.assertRaises(ValueError):
                    method(session, "doc", "TO-001", "catalogue",
                           classify_knuckle_exclusions=value)
                op.assert_not_called()
                session.routing_record.assert_not_called()

    def test_two_exact_witnesses_keep_source_and_separate_physical_fit(self):
        data = indexed(fixture())
        before = copy.deepcopy(data)
        result = qualify(data)
        self.assertEqual(set(result), {identity(name) for name in NAMES})
        self.assertEqual(result, qualify(data))
        self.assertEqual(data, before)
        for key, record in result.items():
            self.assertEqual(record["physical_status"],
                             "source-endpoint-exclusion")
            self.assertEqual(record["exclusion_kind"], KIND)
            self.assertNotIn("supporting_position_id", record)
            self.assertNotIn("supporting_assembly_placed", record)
            proof = record["source_endpoint_exclusion"]
            self.assertEqual(proof["selected_source_family"], "XA")
            self.assertEqual(proof["selected_source_chair_code"], 23)
            self.assertEqual(proof["source_station_mm"], STATION)
            self.assertEqual(proof["source_context_sha256"], CONTEXT)
            self.assertEqual(proof["selected_owner_position_id"],
                             identity("turnout-side wing rail"))
            self.assertEqual(proof["continuing_rail_identity"],
                             data[0][key]["rail_identity"].replace(
                                 "knuckle", "rail"))
            self.assertIs(proof["canonical_position_is_rail_endpoint"], True)
            self.assertEqual(proof["endpoint_continuity_fields"], list(FIELDS))
            self.assertEqual(proof["physical_fit"], "NOT_ASSESSED")

    def test_each_raw_identity_owner_assignment_and_parent_is_required(self):
        mutations = {
            "stable_chair_position_identity": "wrong",
            "parent_turnout_identity": "XO-001-A001",
            "parent_crossover_identity": "XO-001",
            "rail_identity": "wrong", "rail_name": "wrong",
            "rail_role": "wing rail", "timber_identity": "wrong",
            "prototype_timber_identifier": "X2-Y", "timber_identifier": "X2-Y",
            "chair_code": True, "chair_code_label": "XA",
            "special_assignment_deferred": 1, "deliberate_omission": True,
        }
        for name in NAMES:
            for field, value in mutations.items():
                data = indexed(fixture())
                data[0][identity(name)][field] = value
                with self.subTest(name=name, field=field), self.assertRaises(
                    ValueError,
                ):
                    qualify(data)
            data = indexed(fixture())
            del data[0][identity(name)]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                qualify(data)

    def test_named_rail_timber_and_configuration_bindings_are_required(self):
        for name in NAMES:
            for defect in ("parent", "name", "role", "rail-config",
                           "timber-config", "timber-id", "station", "heave"):
                data = indexed(fixture())
                p = data[0][identity(name)]
                r, t = data[1][p["rail_identity"]], data[2][p["timber_identity"]]
                if defect == "parent":
                    r["parent_turnout_identity"] = "Other"
                elif defect == "name":
                    r["name"] = "other"
                elif defect == "role":
                    r["rail_role"] = "wing rail"
                elif defect.endswith("config"):
                    p["source_configuration"][defect.split("-")[0]] = {}
                elif defect == "timber-id":
                    t["stable_identity"] = "Other"
                elif defect == "station":
                    t["source_configuration"]["local_x"] += 0.1
                else:
                    # Consistent source dictionaries still cannot add heave.
                    r["source_configuration"]["heave"] = True
                    p["source_configuration"]["rail"]["heave"] = True
                with self.subTest(name=name, defect=defect):
                    with self.assertRaises(ValueError):
                        qualify(data)

    def test_xa_source_witness_and_exact_companion_mapping_are_required(self):
        for field, value in (
            ("position_id", identity("main-side wing rail")),
            ("family", "XN"), ("source_hand", "RH"),
            ("prototype_timber_identifier", "X2-Y"),
            ("source_chair_code", 22), ("source_chair_code", True),
            ("source_rail_code", 2), ("source_context_sha256", "0" * 64),
            ("source_model_sha256", "0" * 64),
            ("source_station_mm", math.nextafter(STATION, math.inf)),
            ("source_station_mm", math.nan),
        ):
            data = indexed(fixture())
            data[3][0][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    qualify(data)
        for defect in ("missing", "duplicate", "mate", "reverse", "overlap"):
            data = indexed(fixture())
            if defect == "missing":
                data[3].pop(0)
            elif defect == "duplicate":
                data[3].append(copy.deepcopy(data[3][0]))
            elif defect == "mate":
                data[4].pop(identity("main-side wing rail"))
            elif defect == "reverse":
                data[4][identity("turnout-side wing rail")] = identity(
                    "main-side wing rail")
            else:
                data[4][identity(NAMES[0])] = identity("turnout-side wing rail")
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                qualify(data)

    def test_every_endpoint_field_and_complete_polyline_is_checked(self):
        for name in NAMES:
            for field in FIELDS:
                for defect in ("knuckle-end", "wing-start", "nan", "inf",
                               "boolean", "short"):
                    data = indexed(fixture())
                    p = data[0][identity(name)]
                    knuckle = data[1][p["rail_identity"]]
                    wing = data[1][p["rail_identity"].replace("knuckle", "rail")]
                    if defect == "knuckle-end":
                        knuckle[field][-1][0] = math.nextafter(
                            knuckle[field][-1][0], math.inf)
                    elif defect == "wing-start":
                        wing[field][0][0] = math.nextafter(
                            wing[field][0][0], math.inf)
                    elif defect == "short":
                        knuckle[field] = knuckle[field][-1:]
                    else:
                        knuckle[field][0][0] = {
                            "nan": math.nan, "inf": math.inf, "boolean": True,
                        }[defect]
                    with self.subTest(name=name, field=field, defect=defect):
                        with self.assertRaises(ValueError):
                            qualify(data)

    def test_centres_are_exact_endpoints_without_a_fit_or_support_claim(self):
        for name in NAMES:
            for centre in ([850, 410], [math.nan, 412], [True, 412], [850]):
                data = indexed(fixture())
                data[0][identity(name)]["centre_point"] = centre
                with self.subTest(name=name, centre=centre):
                    with self.assertRaises(ValueError):
                        qualify(data)

    def test_opt_in_changes_only_two_dispositions_not_assembly_coverage(self):
        source = fixture()
        before = copy.deepcopy((source.context, source.plan))
        old = preview(source)
        explicit = preview(source, classify_knuckle_exclusions=False)
        current = preview(source, classify_knuckle_exclusions=True)
        self.assertEqual(explicit[:2], old[:2])
        self.assertEqual(explicit[3], old[3])
        self.assertEqual(current[1], old[1])
        for candidate in (explicit, current):
            self.assertEqual(len(candidate[2]), len(old[2]))
            self.assertTrue(all(a.isSame(b) for a, b in zip(
                candidate[2], old[2])))
        new, previous = current[3], old[3]
        for field, expected in (("analysis_position_count", 168),
                                ("selected_crossing_count", 4),
                                ("represented_source_position_count", 8),
                                ("source_endpoint_exclusion_count", 2),
                                ("unresolved_source_position_count", 158)):
            self.assertEqual(new[field], expected, field)
        self.assertEqual(new["selected_positions"], previous["selected_positions"])
        self.assertEqual(new["shared_supports"], previous["shared_supports"])
        self.assertEqual(new["original_analytical_exclusions"],
                         previous["original_analytical_exclusions"])
        endpoint_ids = {identity(name) for name in NAMES}
        self.assertEqual(set(new["source_endpoint_exclusions"]), endpoint_ids)
        self.assertEqual(new["source_endpoint_exclusions"], qualify(indexed(source)))
        remaining = {p["stable_chair_position_identity"]: p
                     for p in new["remaining_positions"]}
        self.assertEqual(len(remaining), 158)
        self.assertEqual(remaining, {
            p["stable_chair_position_identity"]: p
            for p in previous["remaining_positions"]
            if p["stable_chair_position_identity"] not in endpoint_ids
        })
        self.assertNotIn("coverage_summary", new)
        self.assertEqual((source.context, source.plan), before)
        new["remaining_positions"][0]["chair_code"] = 999
        self.assertEqual((source.context, source.plan), before)

    def test_bad_endpoint_refuses_before_factory(self):
        source = fixture()
        position(source, identity(NAMES[0]))["centre_point"][0] += 1
        factory = Mock()
        with self.assertRaises(ValueError):
            preview(source, factory, classify_knuckle_exclusions=True)
        factory.assert_not_called()
        for name in NAMES:
            for field, value in (
                ("rail_identity", "other"), ("timber_identity", "other"),
                ("chair_label", "XA"), ("chair_family", "wing-rail chair"),
                ("deliberate_omission", True), ("unresolved_special", False),
                ("unresolved_special", 1),
            ):
                source = fixture()
                exclusion = next(
                    item for item in source.plan["analytical_only"]
                    if item["chair_position_identity"] == identity(name)
                )
                exclusion[field] = value
                factory = Mock()
                with self.subTest(name=name, field=field, value=value):
                    with self.assertRaises(ValueError):
                        preview(source, factory,
                                classify_knuckle_exclusions=True)
                    factory.assert_not_called()

    def test_late_endpoint_interior_timber_context_and_plan_changes_refuse(self):
        for defect in ("centre", "interior", "timber", "context", "plan"):
            source = fixture()

            def create(*args):
                args[4]()
                p = position(source, identity(NAMES[0]))
                if defect == "centre":
                    p["centre_point"][0] += 1
                elif defect == "interior":
                    rail(source, NAMES[0])["points"][0][0] += 1
                elif defect == "timber":
                    p["source_configuration"]["timber"]["local_x"] += 1
                elif defect == "context":
                    p["source_configuration"]["rail"]["heave"] = True
                else:
                    source.plan["analytical_only"][-1]["reason"] = "changed"
                args[4]()

            with self.subTest(defect=defect), self.assertRaises(ValueError):
                preview(source, create, classify_knuckle_exclusions=True)

    def test_same_adapter_layers_placements_and_title_with_opt_in(self):
        observed = []
        for options in ({}, {"classify_knuckle_exclusions": True}):
            args = preview(fixture(), **options)
            boundary = adapter_boundary()
            with admitted_catalogue():
                result = adapter(boundary, args)
                layers, report, verify = result.prepare()
                verify(layers)
                result.verify()
            observed.append((result.specs,
                             boundary.materialise.call_args.kwargs, [
                child.Placement for layer in layers[2:]
                for child in layer.childShapes()
            ]))
            self.assertEqual(len(layers), 137)
            self.assertEqual(report["component_count"], 135)
            self.assertEqual(report["family_count"], len(FAMILIES))
        self.assertEqual(observed[0], observed[1])

    def test_late_endpoint_change_aborts_only_owned_preview(self):
        source = fixture()
        args = preview(source, classify_knuckle_exclusions=True)
        runtime = PreviewRuntime()
        before = runtime.snapshots()
        boundary = adapter_boundary()
        boundary.materialise.side_effect = runtime.preview

        def changed_source():
            self.assertIn("openTransaction", runtime.app.mutations)
            position(source, identity(NAMES[0]))["centre_point"][0] += 1
            args[4]()

        with admitted_catalogue(), patch.dict(sys.modules, {
            "FreeCAD": source.app, "FreeCADGui": runtime.gui,
        }):
            with self.assertRaises(ValueError):
                adapter(boundary, (*args[:4], changed_source))
        self.assertEqual(set(runtime.app.documents), {"Source", "Witness"})
        self.assertIs(runtime.app.ActiveDocument, runtime.source)
        self.assertIn("abortTransaction", runtime.app.mutations)
        self.assertNotIn("commitTransaction", runtime.app.mutations)
        self.assertEqual(runtime.snapshots(), before)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
