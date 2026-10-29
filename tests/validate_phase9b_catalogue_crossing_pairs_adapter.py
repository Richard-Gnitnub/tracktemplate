#!/usr/bin/env python3
"""Check crossing composition at the established native routing seam.

Materialisation is a stand-in. These checks prove no FreeCAD execution,
exact solids, document lifecycle or GUI behaviour.
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
from validate_phase9b_catalogue_crossing_pairs import (  # noqa: E402
    CONTEXTS, COUNTS, FAMILIES, VEE_RAILS, WING_RAILS, identity, pair_source,
)
from validate_phase9b_catalogue_crossing_zy_adapter import (  # noqa: E402
    ZYBoundary,
    adapter_groups as zy_groups,
    adapter_options as zy_options,
    public_fixture as zy_public_fixture,
    run_public as run_zy_public,
)
from validate_phase9b_catalogue_heel_adapter import frame  # noqa: E402


class CrossingPairBoundary(ZYBoundary):
    def __init__(self):
        self.crossing_checks = Mock()
        super().__init__()
        self.namespace.update(
            CROSSING_PAIR_CONTEXT_IDS=CONTEXTS,
            prepare_crossing_pair_catalogue=self.crossing_catalogue,
            verify_crossing_pair_catalogue=self.crossing_checks,
        )

    @staticmethod
    def crossing_catalogue(_path):
        return tuple(SimpleNamespace(
            run=context, label=family, model_sha256=f"invented-{context}",
            context={"context_id": context},
            components=tuple(SimpleNamespace(name=f"{family}Part{i:02d}")
                             for i in range(count)),
        ) for context, family, count in zip(CONTEXTS, FAMILIES, COUNTS))


def adapter_groups(*, pairs=True, zy=True):
    groups = zy_groups(enabled=zy)
    if pairs:
        for index, context in enumerate(CONTEXTS):
            rail = WING_RAILS[0] if index == 0 else VEE_RAILS[0]
            groups[context] = tuple(frame(identity(side, context[3:], rail),
                                          PairedChairPlacement)
                                    for side in ("A", "B"))
    return groups


def adapter_options(*, pairs=True, zy=True):
    options = zy_options(enabled=zy)
    if pairs:
        options["crossing_pair_contexts_path"] = "private-crossing-pairs"
    return options


class CrossingPairAdapterTests(unittest.TestCase):
    def test_eight_assemblies_bind_exact_families_components_and_models(self):
        boundary = CrossingPairBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        selected = [(placements, spec) for placements, spec in boundary.selections
                    if spec["run"] in CONTEXTS]
        self.assertEqual(len(selected), 4)
        self.assertEqual(sum(len(items) for items, _ in boundary.selections), 257)
        self.assertEqual(sum(len(items) * len(spec["source_names"])
                             for items, spec in selected), 270)
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
                         "tracktemplate.private-catalogue-crossover.v7")
        self.assertEqual(receipt["placement_count"], 257)
        self.assertFalse(receipt["geometry_rebuilt"])
        self.assertFalse(receipt["production_geometry_authorized"])
        result.verify()
        boundary.crossing_checks.assert_called_once()
        boundary.zy_checks.assert_called_once()
        boundary.paired_checks.assert_called_once()

    def test_pairs_do_not_require_zy_and_absence_keeps_v5_v6(self):
        for pairs, zy, count, version in ((True, False, 253, 7),
                                         (False, False, 245, 5),
                                         (False, True, 249, 6)):
            receipts = []
            for explicit_none in (False, True):
                boundary = CrossingPairBoundary()
                options = adapter_options(pairs=pairs, zy=zy)
                if not pairs and explicit_none:
                    options["crossing_pair_contexts_path"] = None
                result = boundary.run(adapter_groups(pairs=pairs, zy=zy),
                                      **options)
                _, receipt, _ = result.prepare()
                receipts.append(receipt)
                self.assertEqual(receipt["placement_count"], count)
                self.assertEqual(receipt["contract_id"],
                                 "tracktemplate.private-catalogue-crossover.v"
                                 + str(version))
                result.verify()
                self.assertEqual(boundary.crossing_checks.call_count,
                                 int(pairs))
            self.assertEqual(receipts[0], receipts[1])

    def test_incomplete_extra_duplicate_overlap_and_wrong_frame_fail(self):
        for defect in ("missing", "few", "many", "duplicate", "overlap",
                       "extra", "without-option", "without-stack", "frame"):
            with self.subTest(defect=defect):
                boundary = CrossingPairBoundary()
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
                    groups["RH-X5-B"] = groups[CONTEXTS[0]]
                elif defect == "without-option":
                    options.pop("crossing_pair_contexts_path")
                elif defect == "without-stack":
                    options["include_single_rail"] = False
                else:
                    groups[CONTEXTS[0]] = (frame("wrong-type"),
                                           groups[CONTEXTS[0]][1])
                error = TypeError if defect == "frame" else ValueError
                with self.assertRaises(error):
                    boundary.run(groups, **options)
                boundary.materialise.assert_not_called()

    def test_late_new_source_failure_reaches_transaction_verifier(self):
        boundary = CrossingPairBoundary()
        result = boundary.run(adapter_groups(), **adapter_options())
        boundary.crossing_checks.side_effect = ValueError("Crossing source changed")
        with self.assertRaisesRegex(ValueError, "Crossing source changed"):
            result.verify()
        boundary.source_check.assert_called_once_with()


def public_fixture():
    """Compose existing 355-record fixture with sixteen named positions."""
    data = zy_public_fixture()
    pairs = pair_source()
    positions = data[0][3]
    template = copy.deepcopy(positions["unsupported:0"])
    for number in range(16):
        del positions[f"unsupported:{number}"]
    for key, position in pairs[3].items():
        positions[key] = dict(copy.deepcopy(template), **position)
    data[0][4].extend(pairs[4])
    data[-1]["analytical_only"] = [
        {"chair_position_identity": key, "reason": "preserved source reason"}
        for key in positions if not key.startswith("accepted:")
    ]
    return data, pairs[5]


def run_public(data, selections, *, enabled):
    """Reuse established fixture wiring around the actual public operation."""
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_pair_placement",
    )
    original = binding.preview_private_catalogue_crossover_chairs

    def invoke(*args, **kwargs):
        if enabled:
            kwargs["crossing_pair_contexts_path"] = "private-crossing-pairs"
        return original(*args, **kwargs)

    with patch.object(operation, "prepare_crossing_pair_catalogue",
                      return_value=tuple(selections)), patch.object(
        binding, "preview_private_catalogue_crossover_chairs", side_effect=invoke,
    ):
        return run_zy_public(data, enabled=True)


class CrossingPairReceiptTests(unittest.TestCase):
    def test_355_records_keep_249_accepted_assemblies_and_48_shared_supports(self):
        data, selections = public_fixture()
        before = copy.deepcopy(data[0][3:5])
        _, old, _, old_options = run_public(data, selections, enabled=False)
        groups, receipt, verify, options = run_public(data, selections,
                                                     enabled=True)
        self.assertEqual(data[0][3:5], before)
        self.assertEqual(old["placement_count"], 249)
        self.assertEqual(old["unresolved_source_position_count"], 32)
        self.assertEqual(receipt["analysis_position_count"], 355)
        self.assertEqual(receipt["placement_count"], 257)
        self.assertEqual(receipt["existing_shared_support_count"], 48)
        self.assertEqual(receipt["source_paired_crossing_support_count"], 12)
        self.assertEqual(receipt["represented_source_position_count"], 337)
        self.assertEqual(receipt["unrepresented_source_position_count"], 18)
        self.assertEqual(receipt["finite_source_exclusion_count"], 2)
        self.assertEqual(receipt["unresolved_source_position_count"], 16)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         old["original_analytical_exclusions"])
        self.assertNotIn("crossing_pair_contexts_path", old_options)
        self.assertEqual(options["crossing_pair_contexts_path"],
                         "private-crossing-pairs")
        self.assertEqual(sum(len(groups[c]) for c in CONTEXTS), 8)
        old_rows = {r["position_id"]: r for r in old["excluded_positions"]}
        rows = {r["position_id"]: r for r in receipt["excluded_positions"]}
        for index, context in enumerate(CONTEXTS):
            owner, mate = WING_RAILS if index == 0 else VEE_RAILS
            for side in ("A", "B"):
                key = identity(side, context[3:], mate)
                self.assertEqual(rows[key]["supporting_position_id"],
                                 identity(side, context[3:], owner))
                self.assertTrue(rows[key]["supporting_assembly_placed"])
                self.assertEqual(rows[key]["original_exclusion"],
                                 old_rows[key]["original_exclusion"])
        for key, row in rows.items():
            if key.startswith("unsupported:") or key in data[5]:
                self.assertEqual(row, old_rows[key])
        with patch.object(binding, "_e001_exclusions", return_value=data[5]):
            verify()
            data[0][3][identity("B", "X8-E", VEE_RAILS[1])]["chair_code"] = 27
            with self.assertRaises(ValueError):
                verify()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: crossing pair routing and complete 355-position accounting")
