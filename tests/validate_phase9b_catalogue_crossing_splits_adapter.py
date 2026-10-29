#!/usr/bin/env python3
"""Check XA/BB composition and accounting at the existing native seam.

Native materialisation is a stand-in. No document, exact geometry,
transaction, GUI or physical-fit proof is claimed by these checks.
"""

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
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
)
from validate_phase9b_catalogue_crossing_pairs_adapter import (  # noqa: E402
    CrossingPairBoundary,
    adapter_groups as pair_groups,
    adapter_options as pair_options,
    public_fixture as pair_public_fixture,
    run_public as run_pair_public,
)
from validate_phase9b_catalogue_crossing_splits import (  # noqa: E402
    CONTEXTS, COUNTS, FAMILIES, KNUCKLES, RAILS, identity, split_source,
)
from validate_phase9b_catalogue_heel_adapter import frame  # noqa: E402


class CrossingSplitBoundary(CrossingPairBoundary):
    def __init__(self):
        self.split_checks = Mock()
        super().__init__()
        self.namespace.update(
            CROSSING_SPLIT_CONTEXT_IDS=CONTEXTS,
            prepare_crossing_split_catalogue=self.split_catalogue,
            verify_crossing_split_catalogue=self.split_checks,
        )

    @staticmethod
    def split_catalogue(_path):
        return tuple(SimpleNamespace(
            run=context, label=family, model_sha256=f"invented-{context}",
            context={"context_id": context},
            components=tuple(SimpleNamespace(name=f"{family}Part{i:02d}")
                             for i in range(count)),
        ) for context, family, count in zip(CONTEXTS, FAMILIES, COUNTS))


def adapter_groups(*, splits=True, pairs=True, zy=True):
    groups = pair_groups(pairs=pairs, zy=zy)
    if splits:
        for index, context in enumerate(CONTEXTS):
            groups[context] = tuple(
                frame(identity(side, context[3:], RAILS[index][0][0]),
                      PairedChairPlacement) for side in ("A", "B")
            )
    return groups


def adapter_options(*, splits=True, pairs=True, zy=True):
    options = pair_options(pairs=pairs, zy=zy)
    if splits:
        options["crossing_split_contexts_path"] = "private-splits"
    return options


class CrossingSplitAdapterTests(unittest.TestCase):
    def test_exact_retained_models_components_and_old_groups_are_preserved(self):
        old = CrossingSplitBoundary()
        old.run(adapter_groups(splits=False),
                **adapter_options(splits=False))
        boundary = CrossingSplitBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        selected = [(items, spec) for items, spec in boundary.selections
                    if spec["run"] in CONTEXTS]
        self.assertEqual(len(selected), 2)
        self.assertEqual(sum(len(items) for items, _ in boundary.selections),
                         261)
        self.assertEqual(sum(len(items) * len(spec["source_names"])
                             for items, spec in selected), 152)
        self.assertEqual([(items, spec) for items, spec in boundary.selections
                          if spec["run"] not in CONTEXTS], old.selections)
        for items, spec in selected:
            index = CONTEXTS.index(spec["run"])
            self.assertEqual(len(items), 2)
            self.assertIs(spec["placement_type"], PairedChairPlacement)
            self.assertEqual(spec["family"], FAMILIES[index])
            self.assertEqual(spec["source_names"], tuple(
                f"{FAMILIES[index]}Part{i:02d}" for i in range(COUNTS[index])
            ))
            self.assertEqual(spec["model_sha256"], "invented-" + spec["run"])
            self.assertEqual(spec["prepared_selection"].run, spec["run"])
        _, receipt, _ = result.prepare()
        self.assertEqual(receipt["contract_id"],
                         "tracktemplate.private-catalogue-crossover.v8")
        self.assertEqual(receipt["placement_count"], 261)
        self.assertFalse(receipt["geometry_rebuilt"])
        self.assertFalse(receipt["production_geometry_authorized"])
        result.verify()
        boundary.split_checks.assert_called_once()
        boundary.crossing_checks.assert_called_once()
        boundary.zy_checks.assert_called_once()
        boundary.paired_checks.assert_called_once()

    def test_independent_options_and_none_preserve_every_legacy_version(self):
        for pairs in (False, True):
            for zy in (False, True):
                old_receipts = []
                for explicit_none in (False, True):
                    boundary = CrossingSplitBoundary()
                    options = adapter_options(splits=False, pairs=pairs, zy=zy)
                    if explicit_none:
                        options["crossing_split_contexts_path"] = None
                    result = boundary.run(adapter_groups(
                        splits=False, pairs=pairs, zy=zy,
                    ), **options)
                    _, receipt, _ = result.prepare()
                    old_receipts.append(receipt)
                    count = 245 + 8 * pairs + 4 * zy
                    self.assertEqual(receipt["placement_count"], count)
                    self.assertEqual(receipt["contract_id"],
                                     "tracktemplate.private-catalogue-crossover.v"
                                     + str(7 if pairs else 6 if zy else 5))
                    result.verify()
                    boundary.split_checks.assert_not_called()
                self.assertEqual(*old_receipts)
                boundary = CrossingSplitBoundary()
                result = boundary.run(adapter_groups(pairs=pairs, zy=zy),
                                      **adapter_options(pairs=pairs, zy=zy))
                _, receipt, _ = result.prepare()
                self.assertEqual(receipt["placement_count"], count + 4)
                self.assertEqual(receipt["contract_id"],
                                 "tracktemplate.private-catalogue-crossover.v8")
                result.verify()
                boundary.split_checks.assert_called_once()

    def test_incomplete_extra_overlapping_wrong_frames_fail_before_creation(self):
        for defect in ("missing", "few", "many", "duplicate", "overlap",
                       "extra", "without-option", "without-stack", "frame"):
            with self.subTest(defect=defect):
                boundary = CrossingSplitBoundary()
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
                    groups["RH-X3-X-KNUCKLE"] = groups[CONTEXTS[0]]
                elif defect == "without-option":
                    options.pop("crossing_split_contexts_path")
                elif defect == "without-stack":
                    options["include_single_rail"] = False
                else:
                    groups[CONTEXTS[0]] = (frame("wrong-type"),
                                           groups[CONTEXTS[0]][1])
                with self.assertRaises(TypeError if defect == "frame"
                                       else ValueError):
                    boundary.run(groups, **options)
                boundary.materialise.assert_not_called()

    def test_late_split_failure_reaches_existing_transaction_verifier(self):
        boundary = CrossingSplitBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        boundary.split_checks.side_effect = ValueError("Split source changed")
        with self.assertRaisesRegex(ValueError, "Split source changed"):
            result.verify()
        boundary.source_check.assert_called_once_with()


def public_fixture():
    """Keep 355 records, including all four unsupported XN knuckles."""
    data, pairs = pair_public_fixture()
    splits = split_source()
    positions = data[0][3]
    template = copy.deepcopy(positions["unsupported:16"])
    for number in range(16, 32):
        del positions[f"unsupported:{number}"]
    for key, position in splits[3].items():
        positions[key] = dict(copy.deepcopy(template), **position)
    data[0][4].extend(splits[4])
    data[-1]["analytical_only"] = [
        {"chair_position_identity": key, "reason": "preserved source reason"}
        for key in positions if not key.startswith("accepted:")
    ]
    return data, pairs, splits[5]


def run_public(data, pairs, splits, *, enabled):
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_pair_placement",
    )
    original = binding.preview_private_catalogue_crossover_chairs

    def invoke(*args, **kwargs):
        if enabled:
            kwargs["crossing_split_contexts_path"] = "private-splits"
        return original(*args, **kwargs)

    with patch.object(operation, "prepare_crossing_split_catalogue",
                      return_value=tuple(splits)), patch.object(
        binding, "preview_private_catalogue_crossover_chairs", side_effect=invoke,
    ):
        return run_pair_public(data, pairs, enabled=True)


class CrossingSplitReceiptTests(unittest.TestCase):
    def test_355_records_preserve_257_assemblies_and_all_unqualified_exclusions(self):
        data, pairs, splits = public_fixture()
        before = copy.deepcopy(data[0][3:5])
        old_groups, old, _, old_options = run_public(
            data, pairs, splits, enabled=False,
        )
        groups, receipt, verify, options = run_public(
            data, pairs, splits, enabled=True,
        )
        self.assertEqual(data[0][3:5], before)
        self.assertEqual(old["placement_count"], 257)
        self.assertEqual(old["unresolved_source_position_count"], 16)
        self.assertEqual({key: value for key, value in groups.items()
                          if key not in CONTEXTS}, old_groups)
        for field, expected in (
            ("analysis_position_count", 355), ("placement_count", 261),
            ("existing_shared_support_count", 48),
            ("source_paired_crossing_support_count", 20),
            ("represented_source_position_count", 349),
            ("unrepresented_source_position_count", 6),
            ("finite_source_exclusion_count", 2),
            ("unresolved_source_position_count", 4),
        ):
            self.assertEqual(receipt[field], expected, field)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         old["original_analytical_exclusions"])
        self.assertNotIn("crossing_split_contexts_path", old_options)
        self.assertEqual(options["crossing_split_contexts_path"],
                         "private-splits")
        selected = {row["position_id"]: row
                    for row in receipt["selected_positions"]}
        for row in old["selected_positions"]:
            self.assertEqual(selected[row["position_id"]], row)
        old_rows = {r["position_id"]: r for r in old["excluded_positions"]}
        rows = {r["position_id"]: r for r in receipt["excluded_positions"]}
        changed = set()
        for index, context in enumerate(CONTEXTS):
            for side in ("A", "B"):
                owner = identity(side, context[3:], RAILS[index][0][0])
                changed.add(owner)
                for rail, _, _ in RAILS[index][1:]:
                    key = identity(side, context[3:], rail)
                    changed.add(key)
                    self.assertEqual(rows[key]["supporting_position_id"], owner)
                    self.assertTrue(rows[key]["supporting_assembly_placed"])
                    self.assertEqual(rows[key]["original_exclusion"],
                                     old_rows[key]["original_exclusion"])
        for key, row in old_rows.items():
            if key not in changed:
                self.assertEqual(rows[key], row)
        for side in ("A", "B"):
            for rail in KNUCKLES:
                self.assertNotIn("supporting_position_id",
                                 rows[identity(side, "X3-X", rail)])
        with patch.object(binding, "_e001_exclusions", return_value=data[5]):
            verify()
            data[0][3][identity("B", "X5-B", RAILS[1][-1][0])]["chair_code"] = 26
            with self.assertRaises(ValueError):
                verify()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: four XA/BB assemblies and twelve supported source records")
