#!/usr/bin/env python3
"""Check heel-correction adapter routing without a FreeCAD runtime.

Execute the exact adapter operation from its AST, stopping at its native
materialisation boundary. Pure placement validators remain real; catalogue
loading and materialisation are stand-ins. This proves routing and source
verification wiring, not geometry, documents, transactions or GUI behaviour.
"""

import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.application.chair_pair_catalogue import (  # noqa: E402
    CONTEXT_IDS,
)
from tracktemplate.domain.central_check_placement import (  # noqa: E402
    CentralCheckPlacement,
    prepare_central_check_placements,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    PPlacement,
    S1JPlacement,
    S1Placement,
)
from tracktemplate.domain.check_end_placement import (  # noqa: E402
    CheckEndPlacement,
    prepare_check_end_placements,
)
from tracktemplate.domain.single_rail_placement import (  # noqa: E402
    SingleRailPlacement,
    prepare_single_rail_placements,
)

ADAPTER = ROOT / "tracktemplate/adapters/freecad"
FUNCTION = "create_private_catalogue_crossover_preview"
L1_SHA256 = (
    "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042"
)


def frame(identity, placement_type=S1Placement):
    return placement_type(
        identity, "rail:" + identity, "timber:" + identity,
        (0.0, 0.0, 0.8), (1.0, 0.0), (0.0, 1.0),
    )


def single(identity, family):
    body = frame(identity)
    return SingleRailPlacement(
        **vars(body), family=family,
        fixing_frames=(body,) * (4 if family == "L1" else 3),
    )


def fixture(*, corrected=False):
    """Represent the published 237-assembly count with invented identities."""
    groups = {
        "S1": tuple(frame(f"base:{index}")
                    for index in range(113 if corrected else 123)),
        "S1J": tuple(frame(f"joint:{index}", S1JPlacement)
                     for index in range(12)),
        "P": tuple(frame(f"slide:{index}", PPlacement)
                   for index in range(28)),
    }
    for context in CONTEXT_IDS:
        groups[context] = tuple(frame(f"{context}:{index}", PairedChairPlacement)
                                for index in range(2))
    groups["CC"] = tuple(
        CentralCheckPlacement(**vars(body), fixing_frames=(body,) * 4)
        for body in (frame(f"central:{index}") for index in range(12))
    )
    for family in ("CCL", "CCR"):
        groups[family] = tuple(
            CheckEndPlacement(**vars(body), family=family,
                              check_frame=body, fixing_frames=(body,) * 4)
            for body in (frame(f"{family}:{index}") for index in range(4))
        )
    groups["SupplementS1"] = tuple(single(f"extra:{index}", "S1")
                                   for index in range(14))
    groups["SupplementS1J"] = tuple(single(f"extra-joint:{index}", "S1J")
                                    for index in range(4))
    groups["L1"] = tuple(single(f"limited:{index}", "L1")
                          for index in range(16))
    if corrected:
        groups["L1"] += tuple(single(f"base:{index}", "L1")
                               for index in range(113, 123))
    return groups


def extracted_operation(namespace):
    """Compile unchanged routing and record validation, without imports."""
    path = ADAPTER / "chair_catalogue_placement_preview.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = [node for node in tree.body if (
        isinstance(node, ast.FunctionDef)
        and node.name in (FUNCTION, "_require")
    ) or (
        isinstance(node, ast.Assign)
        and all(isinstance(target, ast.Name) and target.id.isupper()
                for target in node.targets)
    )]
    reference = ADAPTER / "chair_reference_preview.py"
    parsed = ast.parse(reference.read_text(encoding="utf-8"))
    nodes += [node for node in parsed.body
              if isinstance(node, ast.FunctionDef) and node.name == "_placements"]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"),
         namespace)
    return namespace[FUNCTION]


class RoutingBoundary:
    """Supply no native host; retain callbacks for explicit wiring checks."""

    def __init__(self):
        self.catalogue_checks = Mock()
        self.paired_checks = Mock()
        self.materialise = Mock(side_effect=self.capture)
        self.selections = []
        self.namespace = dict(
            json=json, CONTEXT_IDS=CONTEXT_IDS,
            S1Placement=S1Placement, S1JPlacement=S1JPlacement,
            PPlacement=PPlacement, PairedChairPlacement=PairedChairPlacement,
            CentralCheckPlacement=CentralCheckPlacement,
            CheckEndPlacement=CheckEndPlacement,
            SingleRailPlacement=SingleRailPlacement,
            prepare_central_check_placements=prepare_central_check_placements,
            prepare_check_end_placements=prepare_check_end_placements,
            prepare_single_rail_placements=prepare_single_rail_placements,
            prepare_paired_catalogue=self.paired_catalogue,
            prepare_catalogue_chair=self.catalogue,
            _prepare_catalogue_family=self.select,
            verify_catalogue_sources=self.catalogue_checks,
            verify_paired_catalogue=self.paired_checks,
            _materialise_preview=self.materialise,
        )
        self.operation = extracted_operation(self.namespace)

    def paired_catalogue(self, _path):
        return tuple(SimpleNamespace(
            run=context, label=context.rsplit("-", 1)[1],
            model_sha256="invented-pair", context="invented-pair",
            components=(SimpleNamespace(name="invented-part"),),
        ) for context in CONTEXT_IDS)

    def catalogue(self, _path, family, *, run):
        names = (("invented",) * 17 + self.namespace["_CC_FIXING_NAMES"]
                 if family == "CC" else ())
        return SimpleNamespace(
            run=run, components=tuple(SimpleNamespace(name=name)
                                      for name in names),
            context={"context_sha256":
                     self.namespace["_CHECK_END_CONTEXT_SHA256"]},
        )

    def select(self, _path, placements, _context, _receipt, **specification):
        self.selections.append((placements, specification))
        prepared = SimpleNamespace(run=specification["run"])
        return prepared, (), Mock(side_effect=AssertionError(
            "Native layers must not be constructed by this standalone test"
        ))

    @staticmethod
    def capture(family, receipt, specs, prepare, verify, **_kwargs):
        return SimpleNamespace(family=family, receipt=receipt, specs=specs,
                               prepare=prepare, verify=verify)

    def run(self, groups, **overrides):
        options = dict(paired_contexts_path="invented-pairs",
                       include_central_cc=True, include_check_ends=True,
                       include_single_rail=True)
        options.update(overrides)
        self.source_check = Mock()
        return self.operation("invented-catalogue", groups, (),
                              {"origin": "invented"}, self.source_check,
                              **options)


class HeelAdapterRoutingTests(unittest.TestCase):
    def test_default_and_successor_keep_237_identities_and_retained_l1(self):
        original_ids = None
        for corrected, expected in ((False, 16), (True, 26)):
            with self.subTest(corrected=corrected):
                boundary = RoutingBoundary()
                options = {"correct_heel_l1": True} if corrected else {}
                result = boundary.run(fixture(corrected=corrected), **options)
                boundary.materialise.assert_called_once()
                identities = {item.position_id for placements, _spec
                              in boundary.selections for item in placements}
                self.assertEqual(len(identities), 237)
                if original_ids is None:
                    original_ids = identities
                self.assertEqual(identities, original_ids)
                l1 = [(items, spec) for items, spec in boundary.selections
                      if spec["family"] == "L1"]
                self.assertEqual(len(l1), 1)
                placements, specification = l1[0]
                self.assertEqual(len(placements), expected)
                self.assertEqual(specification["model_sha256"], L1_SHA256)
                self.assertEqual(specification["run"], "existing-02")
                self.assertEqual(specification["source_context"],
                                 "retained-S1-L1-reference-package")
                self.assertIs(specification["placement_type"],
                              SingleRailPlacement)
                self.assertEqual(len(specification["source_names"]), 23)
                result.verify()
                boundary.source_check.assert_called_once_with()
                self.assertEqual(boundary.catalogue_checks.call_count, 9)
                boundary.paired_checks.assert_called_once()

    def test_option_requires_boolean_and_qualified_supplements(self):
        for options in (
            *({"correct_heel_l1": value} for value in (None, 0, 1, "true")),
            {"correct_heel_l1": True, "include_single_rail": False},
            {"correct_heel_l1": True, "include_check_ends": False},
            {"correct_heel_l1": True, "include_central_cc": False},
            {"correct_heel_l1": True, "paired_contexts_path": None},
        ):
            with self.subTest(options=options):
                boundary = RoutingBoundary()
                with self.assertRaises(ValueError):
                    boundary.run(fixture(corrected=True), **options)
                self.assertEqual(boundary.selections, [])
                boundary.materialise.assert_not_called()

    def test_incomplete_duplicate_and_overlapping_selections_are_refused(self):
        for defect in ("missing-group", "too-few", "too-many", "duplicate",
                       "overlap", "old-count", "new-count-without-option"):
            with self.subTest(defect=defect):
                boundary = RoutingBoundary()
                groups = fixture(corrected=True)
                option = True
                if defect == "missing-group":
                    del groups["L1"]
                elif defect == "too-few":
                    groups["L1"] = groups["L1"][:-1]
                elif defect == "too-many":
                    groups["L1"] += (single("extra-limited", "L1"),)
                elif defect == "duplicate":
                    groups["L1"] = groups["L1"][:-1] + groups["L1"][:1]
                elif defect == "overlap":
                    groups["L1"] = groups["L1"][:-1] + (single("base:0", "L1"),)
                elif defect == "old-count":
                    groups = fixture()
                else:
                    option = False
                with self.assertRaises(ValueError):
                    boundary.run(groups, correct_heel_l1=option)
                boundary.materialise.assert_not_called()

    def test_late_source_failure_reaches_materialisation_callback(self):
        boundary = RoutingBoundary()
        result = boundary.run(fixture(corrected=True), correct_heel_l1=True)
        boundary.source_check.side_effect = ValueError("source changed")
        with self.assertRaisesRegex(ValueError, "source changed"):
            result.verify()
        boundary.catalogue_checks.assert_not_called()
        boundary.paired_checks.assert_not_called()


if __name__ == "__main__":
    unittest.main()
