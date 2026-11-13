"""Check fixed TO switch omissions without generating native geometry.

Source-informed metadata follows Templot 556b switch_select:1833-1835
and math_unit:29668-29727 (GPL-3.0-or-later; see NOTICE.md). Existing
P/block doubles supply invented geometry and admitted catalogue summaries.
These tests prove accounting and currentness, not physical shared support,
railway fit, native geometry or permission to transfer source/models.
"""

import copy
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
    chair_catalogue_placement as p_binding,
    chair_pair_placement as block_binding,
    chair_reference_preview,
    transition_workflow,
)
from validate_chair_preview_activation import PreviewRuntime  # noqa: E402
from validate_phase9b_turnout_block_chairs import (  # noqa: E402
    adapter,
    adapter_boundary,
    catalogue_selections,
    source_case as block_source_case,
)

SIGNATURE = (
    "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379"
)
FLAG = "classify_switch_exclusions"
REASON = "shared support position deliberately has no separate chair body"
SIDES = (
    ("main-side stock rail", "curved switch and closure rail"),
    ("turnout-side stock rail", "straight switch and closure rail"),
)
ROUTES = (
    (p_binding, "preview_private_catalogue_p_chairs",
     "private_catalogue_p_preview_factory", 14),
    (block_binding, "preview_private_catalogue_turnout_block_chairs",
     "private_catalogue_turnout_block_preview_factory", 5),
)
SENTINEL = "PASS: fixed TO switch source omissions; geometry unchanged"


def identity(number, rail_name):
    return (f"TO-001:chair:to-001-timber-s{number}:"
            + rail_name.replace(" ", "-"))


def position(source, value):
    return next(p for p in source.context[2]["positions"]
                if p["stable_chair_position_identity"] == value)


def rail(source, name):
    return next(r for r in source.context[4] if r["name"] == name)


def exclusion(source, value):
    return next(p for p in source.plan["analytical_only"]
                if p["chair_position_identity"] == value)


def put_record(source, record):
    """Replace one existing or invented row without enlarging the context."""
    records = source.context[2]["positions"]
    value = record["stable_chair_position_identity"]
    index = next((i for i, p in enumerate(records)
                  if p["stable_chair_position_identity"] == value), None)
    if index is None:
        index = next(i for i, p in enumerate(records)
                     if p["stable_chair_position_identity"].startswith(
                         "invented-unselected-"))
    prior = records[index]["stable_chair_position_identity"]
    plan_record = exclusion(source, prior)
    records[index] = record
    plan_record.update(
        chair_position_identity=value,
        rail_identity=record["rail_identity"],
        timber_identity=record["timber_identity"], chair_label="",
        chair_family=record["chair_family"], reason=REASON,
        deliberate_omission=True, unresolved_special=False,
    )


def fixture():
    """Keep 168 unique records and add all 24 source omission witnesses.

    Metadata and named owner relationships are source-informed. The
    complete rail arrays, P coordinates and S1-S7 timber bases are invented
    doubles, not replacements for the separately reviewed source proof.
    The five block host frames and source expectations remain unchanged.
    """
    source = block_source_case()
    source.module.CHAIR_FAMILY_SLIDE = "slide chair"
    source.module.CHAIR_ASSIGNMENT_OMITTED = "confirmed shared switch support"
    for side, (stock_name, closure_name) in enumerate(SIDES):
        stock = rail(source, stock_name)
        for field, y in (("points", 240.0),
                         ("gauge_face_points", 239.0 + 2 * side),
                         ("outer_face_points", 241.0 - 2 * side)):
            stock[field] = [[-100.0, y], [900.0, y]]
        closure = next((r for r in source.context[4]
                        if r["name"] == closure_name), None)
        if closure is None:
            closure = copy.deepcopy(stock)
            source.context[4].append(closure)
        closure.update(
            stable_identity="TO-001:rail:" + closure_name.replace(" ", "-"),
            name=closure_name, rail_role=closure_name,
            source_configuration={
                "gauge_face": closure_name + " gauge face",
                "outer_face": closure_name + " outer face",
                "gauge_orientation_source": "mapped named turnout rail faces",
                "rail_geometry_revision": 2,
            },
        )
        for number in range(1, 13):
            timber = next(t for t in source.context[5]
                          if t["identifier"] == f"S{number}")
            if number <= 7:
                timber["source_configuration"] = {
                    "local_x": float(number * 10),
                    "turnout_geometry_revision": 2,
                }
                side_name = "main-side" if side == 0 else "turnout-side"
                old = f"invented-P-{side_name}-{number}"
                owner = position(source, old)
                owner.update(
                    stable_chair_position_identity=identity(
                        number, stock_name,
                    ),
                    assignment_status=source.module.CHAIR_ASSIGNMENT_CONFIRMED,
                    source_or_assumed_classification=(
                        "source-derived prototype requirement"
                    ),
                    chair_footprint_parameters={
                        "dimension_classification": (
                            "source-derived prototype requirement"
                        ),
                    },
                    centre_point=[number * 2.0, 240.0],
                    source_configuration={
                        "rail": copy.deepcopy(stock["source_configuration"]),
                        "timber": copy.deepcopy(
                            timber["source_configuration"],
                        ),
                    },
                )
                exclusion(source, old)["chair_position_identity"] = (
                    owner["stable_chair_position_identity"]
                )
            else:
                owner = position(source, identity(number, stock_name))
            record = copy.deepcopy(owner)
            record.update(
                stable_chair_position_identity=identity(number, closure_name),
                rail_identity=closure["stable_identity"],
                rail_name=closure_name, rail_role=closure_name,
                chair_code=0, chair_code_label="",
                chair_family="deliberately omitted chair position",
                chair_subtype=(
                    "switch blade supported by the adjacent P slide-chair "
                    "table" if number <= 7 else
                    "switch blade supported by the adjacent 1P/2P "
                    "block-slide chair" if number <= 9 else
                    "switch rail supported by the adjacent PLR block-heel "
                    "chair"
                ),
                assignment_status="confirmed shared switch support",
                assignment_complete_in_current_stage=True,
                deliberate_omission=True, special_assignment_deferred=False,
                stale_signature_state=False, validation_status="validated",
                key_direction_sign=0, key_orientation="not applicable",
                key_orientation_classification=(
                    "source-derived prototype requirement"
                ),
                source_or_assumed_classification=(
                    "source-derived prototype requirement"
                ),
                source_configuration={
                    "rail": copy.deepcopy(closure["source_configuration"]),
                    "timber": copy.deepcopy(timber["source_configuration"]),
                },
            )
            put_record(source, record)
    return source


def preview(source, route, factory=None, **options):
    """Keep both real public routes and final source verifiers in use."""
    selections = catalogue_selections()
    binding, method, _port, _count = ROUTES[route]
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        patch.object(block_binding, "prepare_catalogue_chair", create=True,
                     side_effect=lambda _p, family, **_kw: selections[family]),
        patch.object(block_binding, "verify_catalogue_sources", create=True),
    ):
        return getattr(binding, method)(
            source.module, source.document, "TO-001", "catalogue.json",
            factory or (lambda *args: args), **options,
        )


def selected_ids(route):
    numbers = range(1, 8) if route == 0 else range(8, 13)
    sides = SIDES if route == 0 else SIDES[:1]
    return {identity(n, closure): identity(n, owner)
            for n in numbers for owner, closure in sides}


def remaining_ids(receipt):
    return {p.get("position_id", p.get("stable_chair_position_identity"))
            for p in receipt["remaining_positions"]}


class SwitchExclusionTests(unittest.TestCase):
    def refuse(self, source, route):
        factory = Mock()
        with self.assertRaises(ValueError):
            preview(source, route, factory, **{FLAG: True})
        factory.assert_not_called()

    def test_fixture_old_routes_preserve_complete_context(self):
        for route in (0, 1):
            source = fixture()
            before = copy.deepcopy((source.context, source.plan))
            records = source.context[2]["positions"]
            self.assertEqual(len(records), 168)
            self.assertEqual(len({p["stable_chair_position_identity"]
                                  for p in records}), 168)
            for items in (source.context[4], source.context[5]):
                self.assertEqual(len({r["stable_identity"] for r in items}),
                                 len(items))
            args = preview(source, route)
            self.assertEqual(len(args[3]["remaining_positions"]),
                             168 - ROUTES[route][3])
            self.assertNotIn("source_switch_exclusions", args[3])
            self.assertEqual((source.context, source.plan), before)

    def test_false_and_omitted_are_exact_old_outputs_and_shapes(self):
        for route in (0, 1):
            source = fixture()
            old = preview(source, route)
            explicit = preview(source, route, **{FLAG: False})
            self.assertEqual(old[:2], explicit[:2])
            self.assertEqual(json.dumps(old[3], sort_keys=True),
                             json.dumps(explicit[3], sort_keys=True))
            self.assertNotIn("source_switch_exclusions", explicit[3])
            for a, b in zip(old[2], explicit[2]):
                self.assertTrue(a.isSame(b))

    def test_nonboolean_refused_before_source_and_factory(self):
        for binding, method, _port, _count in ROUTES:
            for value in (None, 0, 1, "true", [], {}):
                with (
                    self.subTest(method=method, value=value),
                    patch.object(chair_reference_preview,
                                 "_open_source_context") as opened,
                    patch.object(p_binding, "_open_source_context") as p_open,
                ):
                    factory = Mock()
                    with self.assertRaises(ValueError):
                        getattr(binding, method)(
                            object(), object(), "TO-001", "unused", factory,
                            **{FLAG: value},
                        )
                    opened.assert_not_called()
                    p_open.assert_not_called()
                    factory.assert_not_called()

    def test_session_keyword_only_preserves_old_forwarding(self):
        cls = transition_workflow.ModularCoreLayoutWorkflowSession
        for binding, name, port, _count in ROUTES:
            method = getattr(cls, name)
            for operation in (method, getattr(binding, name)):
                parameter = inspect.signature(operation).parameters[FLAG]
                self.assertIs(parameter.default, False)
                self.assertEqual(parameter.kind, parameter.KEYWORD_ONLY)
            session = SimpleNamespace(module=object(), routing_record=Mock(),
                                      **{"_" + port: object()})
            for options in ({}, {FLAG: False}, {FLAG: True}):
                with patch.object(binding, name, return_value="receipt") as op:
                    self.assertEqual(method(session, "doc", "TO-001", "cat",
                                            **options), "receipt")
                    self.assertEqual(op.call_args.args, (
                        session.module, "doc", "TO-001", "cat",
                        getattr(session, "_" + port),
                    ))
                    self.assertEqual(op.call_args.kwargs,
                                     options if options.get(FLAG) else {})
            for value in (None, 0, 1, "true"):
                session.routing_record.reset_mock()
                with patch.object(binding, name) as op:
                    with self.assertRaises(ValueError):
                        method(session, "doc", "TO-001", "cat",
                               **{FLAG: value})
                    op.assert_not_called()
                    session.routing_record.assert_not_called()

    def test_exact_fourteen_and_five_are_disjoint_source_exclusions(self):
        observed = []
        for route in (0, 1):
            source = fixture()
            before = copy.deepcopy((source.context, source.plan))
            old = preview(source, route)
            args = preview(source, route, **{FLAG: True})
            receipt = args[3]
            witnesses = receipt["source_switch_exclusions"]
            wanted = selected_ids(route)
            self.assertEqual(set(witnesses), set(wanted))
            count = ROUTES[route][3]
            self.assertEqual(receipt["source_switch_exclusion_count"], count)
            self.assertEqual(receipt["represented_source_position_count"],
                             count)
            self.assertEqual(receipt["unresolved_source_position_count"],
                             168 - 2 * count)
            self.assertEqual(len(receipt["remaining_positions"]),
                             168 - 2 * count)
            self.assertEqual(remaining_ids(receipt),
                             remaining_ids(old[3]) - set(wanted))
            self.assertEqual(receipt["selected_positions"],
                             old[3]["selected_positions"])
            self.assertEqual(args[:2], old[:2])
            self.assertEqual(receipt.get("coverage_summary"),
                             old[3].get("coverage_summary"))
            self.assertEqual(receipt.get("shared_supports", {}), {})
            self.assertEqual(receipt["original_analytical_exclusions"],
                             source.plan["analytical_only"])
            for value, owner in wanted.items():
                witness = witnesses[value]
                self.assertEqual(witness["physical_status"],
                                 "source-switch-omission")
                self.assertEqual(witness["exclusion_kind"],
                                 "source-null-chair-with-admitted-stock-owner")
                self.assertNotIn("supporting_assembly_placed", witness)
                self.assertNotIn("supporting_position_id", witness)
                proof = witness["source_switch_omission"]
                self.assertEqual(proof["owner_position_id"], owner)
                self.assertIs(type(proof["source_chair_code"]), int)
                self.assertEqual(proof["source_chair_code"], 0)
                self.assertEqual(proof["selected_owner_chair_code"],
                                 position(source, owner)["chair_code"])
                self.assertEqual(proof["prototype_timber_identifier"],
                                 position(source, value)["timber_identifier"])
                self.assertEqual(proof["physical_fit"], "NOT_ASSESSED")
                self.assertEqual(proof["source_geometry_sha256"], SIGNATURE)
            observed.append(set(witnesses))
            self.assertEqual((source.context, source.plan), before)
            # The receipt must not be a mutable alias of source records.
            next(iter(witnesses.values()))["source_switch_omission"][
                "owner_position_id"] = "changed"
            self.assertEqual((source.context, source.plan), before)
        self.assertFalse(observed[0] & observed[1])
        self.assertEqual(len(observed[0] | observed[1]), 19)

    def test_unadmitted_turnout_block_companions_remain_unresolved(self):
        source = fixture()
        for route in (0, 1):
            receipt = preview(source, route, **{FLAG: True})[3]
            for number in range(8, 13):
                value = identity(number, SIDES[1][1])
                self.assertIn(value, remaining_ids(receipt))
                self.assertNotIn(value, receipt["source_switch_exclusions"])

    def test_each_omission_assignment_is_exact(self):
        changes = {
            "chair_code": (1, False, 0.0), "chair_code_label": ("P", " "),
            "chair_family": ("slide chair",),
            "assignment_status": ("confirmed",),
            "assignment_complete_in_current_stage": (False, 1),
            "deliberate_omission": (False, 1),
            "special_assignment_deferred": (True, 0),
            "stale_signature_state": (True, 0),
            "validation_status": ("unvalidated",),
            "source_or_assumed_classification": ("assumed",),
            "key_direction_sign": (1, False, 0.0),
        }
        for route in (0, 1):
            for value in selected_ids(route):
                for field, replacements in changes.items():
                    for replacement in replacements:
                        source = fixture()
                        position(source, value)[field] = replacement
                        with self.subTest(route=route, value=value,
                                          field=field,
                                          replacement=replacement):
                            self.refuse(source, route)

    def test_exact_owners_side_timber_and_raw_source_bindings(self):
        changes = {
            "rail_identity": "TO-001:rail:other",
            "rail_name": "main-side stock rail", "rail_role": "stock rail",
            "parent_turnout_identity": "TO-002",
            "parent_crossover_identity": "XO-001",
            "timber_identity": "TO-001:timber:S2",
            "timber_identifier": "S2", "prototype_timber_identifier": "S2",
        }
        for route in (0, 1):
            value, owner = next(iter(selected_ids(route).items()))
            for field, replacement in changes.items():
                source = fixture()
                if position(source, value)[field] == replacement:
                    replacement = "TO-002:other"
                position(source, value)[field] = replacement
                with self.subTest(route=route, field=field):
                    self.refuse(source, route)
            for field, replacement in (
                ("chair_code", 1), ("chair_code_label", "S1"),
                ("chair_family", "ordinary rail chair"),
                ("assignment_complete_in_current_stage", False),
                ("source_or_assumed_classification", "assumed"),
                ("deliberate_omission", True),
                ("rail_identity", position(fixture(), value)["rail_identity"]),
            ):
                source = fixture()
                position(source, owner)[field] = replacement
                with self.subTest(route=route, owner_field=field):
                    self.refuse(source, route)
            for part in ("rail", "timber"):
                source = fixture()
                position(source, value)["source_configuration"][part][
                    "unexpected"] = "changed"
                with self.subTest(route=route, binding=part):
                    self.refuse(source, route)

    def test_fixed_source_configuration_signature_and_count(self):
        changes = {
            "handing": "Right-hand", "orientation": "Trailing",
            "rail_geometry_revision": True, "timber_geometry_revision": 3,
            "toe_chainage": math.nan, "template_width": 32.01,
            "chair_analysis_signature": "changed", "turnout_id": "TO-002",
        }
        for route in (0, 1):
            for field, replacement in changes.items():
                source = fixture()
                source.context[1][field] = replacement
                with self.subTest(route=route, field=field):
                    self.refuse(source, route)
            source = fixture()
            source.context[2]["geometry_signature"] = "changed"
            self.refuse(source, route)
            source = fixture()
            source.context[2]["positions"].pop()
            self.refuse(source, route)

    def test_duplicate_missing_and_nonfinite_witnesses_refuse(self):
        for route in (0, 1):
            value, owner = next(iter(selected_ids(route).items()))
            for target in (value, owner):
                for mode in ("duplicate", "missing"):
                    source = fixture()
                    records = source.context[2]["positions"]
                    record = position(source, target)
                    if mode == "duplicate":
                        records.append(copy.deepcopy(record))
                    else:
                        records.remove(record)
                    with self.subTest(route=route, target=target, mode=mode):
                        self.refuse(source, route)
            for field in ("centre_point", "local_rail_tangent"):
                for value_bad in (math.nan, math.inf, True):
                    source = fixture()
                    position(source, value)[field][0] = value_bad
                    with self.subTest(route=route, field=field,
                                      value=value_bad):
                        self.refuse(source, route)
            for kind in ("rails", "timbers"):
                source = fixture()
                items = source.context[4 if kind == "rails" else 5]
                items.append(copy.deepcopy(items[0]))
                with self.subTest(route=route, duplicate=kind):
                    self.refuse(source, route)

    def test_original_plan_binding_and_partition_are_required(self):
        changes = {
            "reason": "invented support acceptance", "chair_label": "P",
            "deliberate_omission": False, "unresolved_special": True,
            "rail_identity": "wrong", "timber_identity": "wrong",
        }
        for route in (0, 1):
            value = next(iter(selected_ids(route)))
            for field, replacement in changes.items():
                source = fixture()
                exclusion(source, value)[field] = replacement
                with self.subTest(route=route, field=field):
                    self.refuse(source, route)
            source = fixture()
            duplicate = copy.deepcopy(exclusion(source, value))
            duplicate.update(chair_code=0, base_z=0.8)
            source.plan["instances"].append(duplicate)
            self.refuse(source, route)

    def test_source_and_plan_mutation_during_factory_are_rejected(self):
        for route in (0, 1):
            for defect in ("record", "owner", "rail", "timber", "plan"):
                source = fixture()
                value, owner = next(iter(selected_ids(route).items()))

                def create(*args):
                    if defect == "record":
                        position(source, value)["centre_point"][0] += 0.001
                    elif defect == "owner":
                        position(source, owner)["chair_code_label"] = "changed"
                    elif defect == "rail":
                        rail(source, SIDES[0][1])["points"][0][0] += 0.001
                    elif defect == "timber":
                        position(source, value)["source_configuration"][
                            "timber"]["local_x"] += 0.001
                    else:
                        exclusion(source, value)["reason"] = "changed"
                    args[4]()

                with self.subTest(route=route, defect=defect):
                    with self.assertRaises(ValueError):
                        preview(source, route, create, **{FLAG: True})

    def test_block_adapter_placement_layers_and_title_do_not_change(self):
        observations = []
        for options in ({}, {FLAG: True}):
            args = preview(fixture(), 1, **options)
            boundary = adapter_boundary()
            result = adapter(boundary, args)
            layers, report, verify = result.prepare()
            verify(layers)
            observations.append((result.specs,
                                 boundary.materialise.call_args.kwargs,
                                 [child.Placement for layer in layers[2:]
                                  for child in layer.childShapes()]))
            self.assertEqual(len(layers), 163)
            self.assertEqual(report["component_count"], 161)
        self.assertEqual(observations[0], observations[1])

    def test_late_omission_change_rolls_back_only_owned_preview(self):
        source = fixture()
        args = preview(source, 1, **{FLAG: True})
        runtime = PreviewRuntime()
        before = runtime.snapshots()
        boundary = adapter_boundary()
        boundary.materialise.side_effect = runtime.preview

        def changed_source():
            self.assertIn("openTransaction", runtime.app.mutations)
            value = next(iter(selected_ids(1)))
            position(source, value)["centre_point"][0] += 0.001
            args[4]()

        with patch.dict(sys.modules, {"FreeCAD": source.app,
                                     "FreeCADGui": runtime.gui}):
            with self.assertRaises(ValueError):
                adapter(boundary, (*args[:4], changed_source))
        self.assertEqual(set(runtime.app.documents), {"Source", "Witness"})
        self.assertIs(runtime.app.ActiveDocument, runtime.source)
        self.assertIn("abortTransaction", runtime.app.mutations)
        self.assertNotIn("commitTransaction", runtime.app.mutations)
        self.assertEqual(runtime.snapshots(), before)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SwitchExclusionTests),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
