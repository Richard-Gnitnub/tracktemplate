#!/usr/bin/env python3
"""Check the finite TO-001 adapter and session without FreeCAD or Qt.

The exact adapter functions run with catalogue and shape doubles. These
checks prove retained selection, metadata, validation and callback wiring.
They do not qualify native geometry, transactions, display or physical fit.
"""

import ast
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain.chair_placement import S1Placement  # noqa: E402
from tracktemplate.domain.central_check_placement import (  # noqa: E402
    CentralCheckPlacement,
)
from tracktemplate.domain.check_end_placement import (  # noqa: E402
    CheckEndPlacement,
)
from tracktemplate.domain.single_rail_placement import (  # noqa: E402
    SingleRailPlacement,
    place_left_hand_single_rail,
    prepare_single_rail_placements,
)

FUNCTION = "create_private_catalogue_turnout_single_rail_preview"
METHOD = "preview_private_catalogue_turnout_single_rail_chairs"
FACTORY = "private_catalogue_turnout_single_rail_preview_factory"
BINDING = "tracktemplate.compatibility.chair_turnout_single_rail_placement"
SENTINEL = "Phase 9B TO-001 single-rail adapter validation passed"
SELECTED = (
    ("S13", "curved-switch-and-closure-rail", "L1"),
    ("S13", "turnout-side-stock-rail", "L1"),
    ("T1", "curved-switch-and-closure-rail", "L1"),
    ("T1", "turnout-side-stock-rail", "L1"),
    ("T2", "curved-switch-and-closure-rail", "L1"),
    ("T2", "turnout-side-stock-rail", "S1"),
    ("T14", "curved-switch-and-closure-rail", "L1"),
)


def fixture(include_corrected=True):
    """Keep seven invented frames; add five source-qualified heel frames."""
    values = []
    for timber, rail, family in SELECTED:
        body = S1Placement(
            f"TO-001:chair:to-001-timber-{timber.lower()}:{rail}",
            f"TO-001:rail:{rail}", f"TO-001:timber:{timber}",
            (1.0, 2.0, 0.8), (1.0, 0.0), (0.0, 1.0),
        )
        values.append(SingleRailPlacement(
            **vars(body), family=family,
            fixing_frames=(body,) * (4 if family == "L1" else 3),
        ))
    if include_corrected:
        from validate_phase9b_turnout_heel_l1_frames import FROZEN, arguments

        values.extend(place_left_hand_single_rail(**arguments(row))
                      for row in FROZEN)
    return tuple(values)


class ShapeDouble:
    """Represent component identity and placement without native geometry."""

    def __init__(self, source=None, *, children=(), context=False):
        self.identity = source.identity if source else object()
        self.Placement = source.Placement if source else ()
        self.Orientation = "Forward"
        self.children = tuple(children)
        self.Faces = () if context else ("face",)
        self.Solids = () if context else ("solid",)
        self.Edges = ("edge",)

    def isPartner(self, other):
        return self.identity is other.identity

    def childShapes(self):
        return self.children


class AdapterBoundary:
    """Run the adapter with real frame checks and explicit host doubles."""

    def __init__(self):
        path = (ROOT / "tracktemplate/adapters/freecad"
                / "chair_catalogue_placement_preview.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        names = {FUNCTION, "_prepare_catalogue_family", "_require",
                 "_source_identity"}
        nodes = [node for node in tree.body if (
            isinstance(node, ast.FunctionDef) and node.name in names
        ) or (
            isinstance(node, ast.Assign)
            and all(isinstance(target, ast.Name) and target.id.isupper()
                    for target in node.targets)
        )]
        self.source_check = Mock()
        self.catalogue_check = Mock()
        self.materialise = Mock(side_effect=self.capture)
        self.namespace = dict(
            json=json, SingleRailPlacement=SingleRailPlacement,
            CentralCheckPlacement=CentralCheckPlacement,
            CheckEndPlacement=CheckEndPlacement,
            prepare_single_rail_placements=prepare_single_rail_placements,
            prepare_catalogue_chair=self.catalogue,
            verify_catalogue_sources=self.catalogue_check,
            _materialise_preview=self.materialise,
            _component_colour=lambda _label: (0.5, 0.5, 0.5),
            _context_layers=lambda shapes: shapes,
            _measure_layer=lambda shape: {"solid_count": len(shape.Solids)},
            _measure_shape=self.measure,
            _prototype_state=lambda shape, **_kw: self.measure(shape),
            _verify_component=lambda _actual, _expected, **_kw: None,
            _same_presented_shape=lambda actual, expected: actual is expected,
            _host_placement=lambda placement: SimpleNamespace(
                multiply=lambda source: (placement.origin_mm, source),
            ),
            Part=SimpleNamespace(
                Shape=ShapeDouble,
                makeCompound=lambda shapes: ShapeDouble(children=shapes),
            ),
        )
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path),
                     "exec"), self.namespace)
        self.namespace["_import_components"] = self.import_components
        self.selections = {family: self.selection(family)
                           for family in ("L1", "S1")}

    @staticmethod
    def capture(family, receipt, specs, prepare, verify, **_kwargs):
        return SimpleNamespace(family=family, receipt=receipt, specs=specs,
                               prepare=prepare, verify=verify)

    def measure(self, _shape):
        return dict.fromkeys(self.namespace["_DISCRETE_FIELDS"], 1)

    def selection(self, family):
        return SimpleNamespace(
            label=family, run="existing-02",
            context="retained-S1-L1-reference-package",
            model_sha256=self.namespace[f"_{family}_MODEL_SHA256"],
            components=tuple(SimpleNamespace(name=name, label=name)
                             for name in self.namespace[
                                 f"_{family}_SOURCE_NAMES"]),
            catalogue_sha256="invented-catalogue", model_path="invented",
            bindings=(), metadata={}, limitations=(),
        )

    def catalogue(self, _path, family, *, run):
        assert run == "existing-02"
        return self.selections[family]

    def import_components(self, prepared):
        shapes = tuple(ShapeDouble() for _item in prepared.components)
        return shapes, tuple(self.measure(shape) for shape in shapes)

    def run(self, values=None, receipt=None, verify=None):
        return self.namespace[FUNCTION](
            "invented-catalogue", fixture() if values is None else values,
            (ShapeDouble(context=True), ShapeDouble(context=True)),
            {"source": ["kept"]} if receipt is None else receipt,
            self.source_check if verify is None else verify,
        )


class TurnoutSingleRailAdapterTests(unittest.TestCase):
    def test_retained_components_counts_and_lh_metadata(self):
        boundary = AdapterBoundary()
        result = boundary.run()
        self.assertEqual(len(result.specs), 42)
        self.assertEqual(len({spec[0] for spec in result.specs}), 42)
        layers, receipt, verify = result.prepare()
        self.assertEqual(len(layers), 42)
        self.assertEqual(receipt["contract_id"],
                         "tracktemplate.private-catalogue-turnout-single-rail.v1")
        self.assertEqual(receipt["placement_count"], 12)
        self.assertEqual(receipt["component_count"], 40)
        self.assertEqual(receipt["family_count"], 2)
        self.assertEqual(receipt["source_receipt"], {"source": ["kept"]})
        self.assertEqual(receipt["project_status"], "reference-only")
        self.assertFalse(receipt["production_geometry_authorized"])
        self.assertFalse(receipt["geometry_rebuilt"])
        for family, count, components in (("L1", 11, 23), ("S1", 1, 17)):
            item = receipt["families"][family]
            self.assertEqual(item["placement_count"], count)
            self.assertEqual(item["component_count"], components)
            self.assertEqual(item["run"], "existing-02")
            self.assertEqual(item["source_model_sha256"],
                             boundary.selections[family].model_sha256)
            self.assertEqual(item["fixing_angle_frame"],
                             "uncurved-LH-source-before-common-host-rotation")
            self.assertEqual(item["excluded_source_components"], [])
            self.assertNotIn("source_receipt", item)
            self.assertEqual(len(item["placements"]), count)
            self.assertTrue(all(len(p["components"]) == components
                                for p in item["placements"]))
        verify(layers)
        with self.assertRaises(ValueError):
            verify(layers[:-1])
        changed = (ShapeDouble(context=True),) + layers[1:]
        with self.assertRaises(ValueError):
            verify(changed)

    def test_five_corrected_heel_component_frames(self):
        boundary = AdapterBoundary()
        receipt = boundary.run().prepare()[1]
        records = {p["position_id"]: p for p in
                   receipt["families"]["L1"]["placements"]}
        components = 0
        for value in fixture()[7:]:
            record = records[value.position_id]
            self.assertEqual(len(record["components"]), 23)
            for component in record["components"]:
                name = component["source_name"]
                frame = value
                if name in boundary.namespace["_CC_FIXING_NAMES"]:
                    index = boundary.namespace["_CC_FIXING_NAMES"].index(name)
                    frame = value.fixing_frames[index // 4]
                for field in ("origin_mm", "x_axis", "y_axis"):
                    self.assertEqual(component[field], getattr(frame, field))
                self.assertEqual(component["placement_identity"], (
                    value.position_id,
                    boundary.namespace["_L1_MODEL_SHA256"], name,
                ))
                components += 1
        self.assertEqual(components, 115)

    def test_seven_previous_frames_and_component_identities_preserved(self):
        boundary = AdapterBoundary()
        receipt = boundary.run().prepare()[1]
        for value in fixture(include_corrected=False):
            family = receipt["families"][value.family]
            record = next(p for p in family["placements"]
                          if p["position_id"] == value.position_id)
            self.assertEqual(record["rail_id"], value.rail_id)
            self.assertEqual(record["timber_id"], value.timber_id)
            for field in ("origin_mm", "x_axis", "y_axis"):
                self.assertEqual(record[field], getattr(value, field))
                for component in record["components"]:
                    self.assertEqual(component[field], getattr(value, field))
            names = boundary.namespace[f"_{value.family}_SOURCE_NAMES"]
            self.assertEqual(tuple(p["source_name"]
                                   for p in record["components"]), names)

    def test_each_corrected_heel_and_its_l1_family_are_required(self):
        values = fixture()
        for index in range(7, 12):
            wrong = replace(values[index], family="S1",
                            fixing_frames=values[index].fixing_frames[:3])
            for candidate in (values[:index] + values[index + 1:],
                              values[:index] + (wrong,) + values[index + 1:]):
                boundary = AdapterBoundary()
                with self.subTest(index=index), self.assertRaises(ValueError):
                    boundary.run(candidate)
                boundary.materialise.assert_not_called()
        with self.assertRaises(ValueError):
            AdapterBoundary().run(fixture(include_corrected=False))

    def test_source_and_both_catalogues_are_checked_at_shared_boundary(self):
        boundary = AdapterBoundary()
        result = boundary.run()
        boundary.materialise.assert_called_once()
        result.verify()
        boundary.source_check.assert_called_once_with()
        self.assertEqual(boundary.catalogue_check.call_count, 2)
        self.assertEqual({call.args[0].label
                          for call in boundary.catalogue_check.call_args_list},
                         {"L1", "S1"})
        for failed in (boundary.source_check, boundary.catalogue_check):
            failed.side_effect = ValueError("changed input")
            with self.assertRaisesRegex(ValueError, "changed input"):
                result.verify()
            failed.side_effect = None

    def test_input_order_keeps_canonical_placement_order(self):
        receipts = []
        for values in (fixture(), tuple(reversed(fixture()))):
            boundary = AdapterBoundary()
            result = boundary.run(values).prepare()[1]
            receipts.append({
                family: item["placements"]
                for family, item in result["families"].items()
            })
        self.assertEqual(receipts[0], receipts[1])

    def test_finite_identity_family_and_nested_frame_rejections(self):
        values = fixture()
        wrong_family = replace(values[0], family="S1",
                               fixing_frames=values[0].fixing_frames[:3])
        wrong_owner = replace(values[0], position_id="invented",
                              fixing_frames=tuple(
                                  replace(f, position_id="invented")
                                  for f in values[0].fixing_frames))
        corrupt = replace(values[0])
        object.__setattr__(corrupt.fixing_frames[0], "origin_mm",
                           (float("nan"), 2.0, 0.8))
        for bad in ((), values[:-1], values + values[:1], list(values),
                    values[:-1] + values[:1],
                    (wrong_family,) + values[1:],
                    (wrong_owner,) + values[1:], (corrupt,) + values[1:]):
            boundary = AdapterBoundary()
            with self.subTest(bad=bad), self.assertRaises((TypeError, ValueError)):
                boundary.run(bad)
            boundary.materialise.assert_not_called()

    def test_catalogue_substitution_fails_before_materialisation(self):
        for family in ("L1", "S1"):
            for field, value in (("label", "P"), ("run", "basic-04"),
                                 ("context", "wrong"),
                                 ("model_sha256", "wrong"),
                                 ("components", ())):
                boundary = AdapterBoundary()
                setattr(boundary.selections[family], field, value)
                with self.subTest(family=family, field=field):
                    with self.assertRaises(ValueError):
                        boundary.run()
                    boundary.materialise.assert_not_called()

    def test_receipt_copy_rejection_and_callable_guard(self):
        boundary = AdapterBoundary()
        original = {"source": ["kept"]}
        result = boundary.run(receipt=original)
        original["source"].append("later")
        self.assertEqual(result.receipt, {"source": ["kept"]})
        for bad in ([], "text", {"bad": float("nan")}):
            with self.subTest(receipt=bad), self.assertRaises(ValueError):
                boundary.run(receipt=bad)
        with self.assertRaises(TypeError):
            boundary.run(verify=object())

    def test_existing_single_rail_receipt_defaults_to_rh(self):
        boundary = AdapterBoundary()
        family = "S1"
        options = dict(
            family=family, placement_type=SingleRailPlacement,
            model_sha256=boundary.namespace["_S1_MODEL_SHA256"],
            source_names=boundary.namespace["_S1_SOURCE_NAMES"],
            run="existing-02",
            source_context="retained-S1-L1-reference-package",
        )
        operation = boundary.namespace["_prepare_catalogue_family"]
        arguments = ("invented", (fixture()[5],), None, {})
        _prepared, _specs, prepare = operation(*arguments, **options)
        self.assertEqual(prepare()[1]["fixing_angle_frame"],
                         "uncurved-RH-source-before-common-host-rotation")
        for bad in (None, "Left-hand", "", True):
            with self.subTest(hand=bad), self.assertRaises(ValueError):
                operation(*arguments, **options, source_handing=bad)

    def test_session_routes_exact_inputs_after_routing_check(self):
        calls = []
        factory = object()
        session = SimpleNamespace(
            module=object(), routing_record=lambda: calls.append("route"),
            **{"_" + FACTORY: factory},
        )
        document = object()

        def operation(*args):
            self.assertEqual(calls, ["route"])
            self.assertEqual(args, (session.module, document, "TO-001",
                                    "catalogue.json", factory))
            return "receipt"

        with patch.dict(sys.modules, {BINDING: SimpleNamespace(
            **{METHOD: operation},
        )}):
            method = getattr(
                transition_workflow.ModularCoreLayoutWorkflowSession, METHOD,
            )
            self.assertEqual(method(session, document, "TO-001",
                                    "catalogue.json"), "receipt")

    def test_session_constructor_preserves_optional_factory_default(self):
        from tracktemplate import api
        from validate_phase9b_l1_reference_preview import _session

        original = _session()
        self.assertIsNone(getattr(original, "_" + FACTORY))
        factory = object()
        session = transition_workflow.ModularCoreLayoutWorkflowSession(
            original._calculation_session, api.run_core_layout_export,
            **{FACTORY: factory},
        )
        self.assertIs(getattr(session, "_" + FACTORY), factory)

    def test_source_binding_reaches_adapter_with_exact_selected_set(self):
        from validate_phase9b_turnout_single_rail import (
            corrected_source_case,
            preview,
        )

        boundary = AdapterBoundary()

        def create(*args):
            result = boundary.namespace[FUNCTION](*args)
            result.verify()
            return result

        result = preview(corrected_source_case(), create)
        self.assertEqual(result.receipt["selected_family_counts"],
                         {"L1": 11, "S1": 1})
        self.assertEqual(len(result.specs), 42)
        self.assertEqual(boundary.catalogue_check.call_count, 2)

    def test_macro_composition_uses_exact_new_factory(self):
        macro = ast.parse((ROOT / "TrackTemplate.FCMacro").read_text())
        keywords = [keyword for node in ast.walk(macro)
                    if isinstance(node, ast.Call) for keyword in node.keywords
                    if keyword.arg == FACTORY]
        self.assertEqual(len(keywords), 1)
        self.assertIsInstance(keywords[0].value, ast.Attribute)
        self.assertEqual(keywords[0].value.attr, FUNCTION)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutSingleRailAdapterTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
