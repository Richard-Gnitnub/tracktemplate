#!/usr/bin/env python3
"""Exercise ZY routing and complete accounting at the native boundary.

Use the actual adapter operation extracted by the established AST fixture.
Native materialisation stays a stand-in; this is no FreeCAD or GUI proof.
"""

from contextlib import ExitStack
import copy
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    chair_check_end_placement,
    chair_check_placement,
    chair_pair_placement,
    chair_single_rail_placement,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    S1Placement,
)
from validate_phase9b_catalogue_crossing_zy import (  # noqa: E402
    CONTEXTS, RAILS, identity, zy_source,
)
from validate_phase9b_catalogue_e001_exclusions import (  # noqa: E402
    fixture as e001_fixture,
)
from validate_phase9b_catalogue_heel_adapter import (  # noqa: E402
    RoutingBoundary,
    frame,
)
from validate_phase9b_catalogue_r1_exit import (  # noqa: E402
    r1_adapter_fixture,
)


class ZYBoundary(RoutingBoundary):
    def __init__(self):
        self.zy_checks = Mock()
        super().__init__()
        self.namespace.update(
            ZY_CONTEXT_IDS=CONTEXTS,
            prepare_zy_catalogue=self.zy_catalogue,
            verify_zy_catalogue=self.zy_checks,
            _context_layers=lambda _: (),
            _measure_layer=lambda _: {},
        )

    @staticmethod
    def zy_catalogue(_path):
        return tuple(SimpleNamespace(
            run=context, label="ZY", model_sha256=f"invented-{context}",
            context={"context_id": context},
            components=tuple(SimpleNamespace(name=f"part{i}")
                             for i in range(33)),
        ) for context in CONTEXTS)

    def select(self, path, placements, context, receipt, **specification):
        prepared, _, _ = super().select(path, placements, context, receipt,
                                       **specification)
        return prepared, (), lambda: (
            (), {"source_receipt": receipt, "label": specification["family"],
                 "component_count": 0, "solid_count": 0}, Mock(),
        )


def adapter_groups(*, enabled=True):
    groups = r1_adapter_fixture(corrected=True, include_r2=True)
    if enabled:
        for context in CONTEXTS:
            groups[context] = tuple(frame(identity(s, context[3:], RAILS[0]),
                                          PairedChairPlacement)
                                    for s in ("A", "B"))
    return groups


def adapter_options(*, enabled=True):
    options = {"correct_heel_l1": True, "include_r2_exit": True,
               "include_r1_exit": True}
    if enabled:
        options["crossing_zy_contexts_path"] = "private-zy"
    return options


class ZYAdapterTests(unittest.TestCase):
    def test_four_new_assemblies_use_unchanged_paired_native_boundary(self):
        boundary = ZYBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        selected = [(placements, spec) for placements, spec in boundary.selections
                    if spec["run"] in CONTEXTS]
        self.assertEqual(len(selected), 2)
        self.assertEqual(sum(len(items) for items, _ in boundary.selections), 249)
        for items, spec in selected:
            self.assertEqual(len(items), 2)
            self.assertIs(spec["placement_type"], PairedChairPlacement)
            self.assertEqual(spec["family"], "ZY")
            self.assertEqual(len(spec["source_names"]), 33)
            self.assertEqual(spec["model_sha256"], "invented-" + spec["run"])
            self.assertEqual(spec["prepared_selection"].run, spec["run"])
        _, receipt, _ = result.prepare()
        self.assertEqual(receipt["contract_id"],
                         "tracktemplate.private-catalogue-crossover.v6")
        self.assertEqual(receipt["placement_count"], 249)
        self.assertFalse(receipt["geometry_rebuilt"])
        self.assertFalse(receipt["production_geometry_authorized"])
        result.verify()
        boundary.zy_checks.assert_called_once()
        boundary.paired_checks.assert_called_once()
        self.assertEqual(boundary.catalogue_checks.call_count, 9)

    def test_none_preserves_default_v5_and_245_assemblies(self):
        results = []
        for explicit in (False, True):
            boundary = ZYBoundary()
            options = adapter_options(enabled=False)
            if explicit:
                options["crossing_zy_contexts_path"] = None
            result = boundary.run(adapter_groups(enabled=False), **options)
            _, receipt, _ = result.prepare()
            results.append(receipt)
            self.assertEqual(receipt["placement_count"], 245)
            self.assertEqual(receipt["contract_id"],
                             "tracktemplate.private-catalogue-crossover.v5")
            result.verify()
            boundary.zy_checks.assert_not_called()
        self.assertEqual(results[0], results[1])

    def test_incomplete_extra_duplicate_and_overlapping_groups_refused(self):
        for defect in ("missing", "few", "many", "duplicate", "overlap",
                       "extra", "without-option", "without-stack"):
            with self.subTest(defect=defect):
                boundary = ZYBoundary()
                groups, options = adapter_groups(), adapter_options()
                if defect == "missing":
                    del groups[CONTEXTS[0]]
                elif defect == "few":
                    groups[CONTEXTS[0]] = groups[CONTEXTS[0]][:1]
                elif defect == "many":
                    groups[CONTEXTS[0]] += (frame("extra", PairedChairPlacement),)
                elif defect == "duplicate":
                    groups[CONTEXTS[0]] = groups[CONTEXTS[0]][:1] * 2
                elif defect == "overlap":
                    groups[CONTEXTS[0]] = (frame("base:0", PairedChairPlacement),
                                           groups[CONTEXTS[0]][1])
                elif defect == "extra":
                    groups["RH-X3-X"] = groups[CONTEXTS[0]]
                elif defect == "without-option":
                    options.pop("crossing_zy_contexts_path")
                else:
                    options["include_single_rail"] = False
                with self.assertRaises(ValueError):
                    boundary.run(groups, **options)
                boundary.materialise.assert_not_called()

    def test_late_supplement_failure_is_retained_at_transaction_boundary(self):
        boundary = ZYBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        boundary.zy_checks.side_effect = ValueError("ZY source changed")
        with self.assertRaisesRegex(ValueError, "ZY source changed"):
            result.verify()
        boundary.source_check.assert_called_once_with()


def public_fixture():
    source = zy_source()
    positions = source[3]
    template = next(iter(e001_fixture()[0].values()))
    for key, position in list(positions.items()):
        positions[key] = dict(copy.deepcopy(template), **position)
    owners = []
    for number in range(245):
        key = f"accepted:{number}"
        positions[key] = dict(copy.deepcopy(template),
                             stable_chair_position_identity=key,
                             chair_code=1, chair_code_label="S1",
                             special_assignment_deferred=False)
        owners.append(S1Placement(key, "rail:" + key, "timber:" + key,
                                  (0, 0, 0.8), (1, 0), (0, 1)))
    shared, central, ends = {}, {}, {}
    for prefix, count, target in (("shared", 48, shared),
                                   ("central", 12, central), ("end", 8, ends)):
        for number in range(count):
            key = f"{prefix}:{number}"
            owner = f"accepted:{number}"
            positions[key] = dict(copy.deepcopy(template),
                                 stable_chair_position_identity=key,
                                 chair_code=0 if prefix == "shared" else 25,
                                 deliberate_omission=prefix == "shared")
            target[key] = positions[owner] if prefix == "shared" else owner
    for number in range(32):
        key = f"unsupported:{number}"
        positions[key] = dict(copy.deepcopy(template),
                             stable_chair_position_identity=key)
    e001 = e001_fixture()[0]
    positions.update(e001)
    exclusions = {key: {"exclusion_kind": "source-anchor-outside-finite-rail-domain"}
                  for key in e001}
    plan = {"instances": [], "analytical_only": [
        {"chair_position_identity": key, "reason": "preserved source reason"}
        for key in positions if not key.startswith("accepted:")
    ]}
    return source, owners, shared, central, ends, exclusions, plan


def run_public(data, *, enabled):
    source, owners, shared, central, ends, exclusions, plan = data
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_zy_placement",
    )
    context = (source[2], {"geometry_signature": "invented",
                          "positions": list(source[3].values())},
               {"future_chair_embed_depth": 0.2}, plan, [], source[4])
    captured = Mock(side_effect=lambda _path, groups, _shapes, receipt,
                    verify, **options: (groups, receipt, verify, options))
    with ExitStack() as stack:
        for name, value in (("_open_source_context", context),
                            ("_require_p_crossover_context", {}),
                            ("_whole_crossover_records", source[3]),
                            ("_e001_exclusions", exclusions),
                            ("_select_s1_s1j_positions", (tuple(owners), (), [])),
                            ("_select_p_positions", ((), [], [], 0.8)),
                            ("_context_shapes_and_verifier", ((), Mock()))):
            stack.enter_context(patch.object(binding, name, return_value=value))
        stack.enter_context(patch.object(
            binding, "_shared_stock_support", side_effect=lambda p, _:
            shared[p["stable_chair_position_identity"]],
        ))
        stack.enter_context(patch.object(
            binding, "_recover_positions", side_effect=lambda _m, _a, _p, _r,
            _t, values, remaining, _c: (values, remaining, []),
        ))
        for module, name, result in (
            (chair_pair_placement, "prepare_crossover_pairs", ({}, {}, Mock())),
            (chair_check_placement, "prepare_central_checks", ((), {}, central, Mock())),
            (chair_check_end_placement, "prepare_check_ends", ({}, {}, ends, Mock())),
            (chair_single_rail_placement, "prepare_single_rails", ({}, {}, Mock())),
        ):
            stack.enter_context(patch.object(module, name, return_value=result))
        stack.enter_context(patch.object(operation, "prepare_zy_catalogue",
                                         return_value=tuple(source[5])))
        return binding.preview_private_catalogue_crossover_chairs(
            source[0], SimpleNamespace(Name="Invented", getObject=source[1].getObject),
            "XO-001", "private-catalogue", captured,
            paired_contexts_path="pairs", include_central_cc=True,
            include_check_ends=True, include_single_rail=True,
            classify_e001_exclusions=True,
            **({"crossing_zy_contexts_path": "private-zy"} if enabled else {}),
        )


class ZYReceiptTests(unittest.TestCase):
    def test_355_positions_preserve_245_assemblies_and_48_shared_supports(self):
        data = public_fixture()
        before = copy.deepcopy(data[0][3:5])
        _, old, _, old_options = run_public(data, enabled=False)
        groups, receipt, verify, options = run_public(data, enabled=True)
        self.assertEqual(data[0][3:5], before)
        self.assertEqual(old["placement_count"], 245)
        self.assertEqual(old["unresolved_source_position_count"], 40)
        self.assertEqual(receipt["analysis_position_count"], 355)
        self.assertEqual(receipt["placement_count"], 249)
        self.assertEqual(receipt["existing_shared_support_count"], 48)
        self.assertEqual(receipt["source_paired_crossing_support_count"], 4)
        self.assertEqual(receipt["represented_source_position_count"], 321)
        self.assertEqual(receipt["unrepresented_source_position_count"], 34)
        self.assertEqual(receipt["finite_source_exclusion_count"], 2)
        self.assertEqual(receipt["unresolved_source_position_count"], 32)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         old["original_analytical_exclusions"])
        self.assertNotIn("crossing_zy_contexts_path", old_options)
        self.assertEqual(options["crossing_zy_contexts_path"], "private-zy")
        self.assertEqual(sum(len(groups[c]) for c in CONTEXTS), 4)
        old_rows = {r["position_id"]: r for r in old["excluded_positions"]}
        rows = {r["position_id"]: r for r in receipt["excluded_positions"]}
        for side in ("A", "B"):
            for timber in ("X1-Z", "X2-Y"):
                key = identity(side, timber, RAILS[1])
                self.assertEqual(rows[key]["exclusion_kind"],
                                 "source-paired-crossing-support")
                self.assertEqual(rows[key]["supporting_position_id"],
                                 identity(side, timber, RAILS[0]))
                self.assertTrue(rows[key]["supporting_assembly_placed"])
                self.assertEqual(rows[key]["original_exclusion"],
                                 old_rows[key]["original_exclusion"])
        for key in rows:
            if key.startswith("unsupported:"):
                self.assertEqual(rows[key], old_rows[key])
        # Keep the same E001 stand-in through the saved callback.
        # ZY source verification remains real at both calls.
        with patch.object(binding, "_e001_exclusions", return_value=data[5]):
            verify()
            data[0][3][identity("A", "X1-Z", RAILS[1])]["chair_code"] = 25
            with self.assertRaises(ValueError):
                verify()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: ZY adapter routing and complete 355-position accounting")
