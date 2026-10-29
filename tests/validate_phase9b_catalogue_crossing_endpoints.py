#!/usr/bin/env python3
"""Check source endpoint exclusions without constructing geometry.

Invented polylines exercise endpoint and lineage checks. Source identities,
the fixed XA context and its station are independent retained-source facts.
The established public fixture substitutes only prior admission layers and
the native boundary. No physical support or native proof is claimed.
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
    chair_catalogue_placement as binding,
    transition_workflow,
)
from validate_phase9b_catalogue_crossing_splits_adapter import (  # noqa: E402
    public_fixture as split_public_fixture,
    run_public as run_split_public,
)
from validate_phase9b_catalogue_crossing_zy import identity  # noqa: E402

CONTEXT_HASH = (
    "56b7518f6446e9d2c91fcee3b94dc9c351b328eed19ac970dfa6fe096e91e802"
)
SOURCE_STATION = 277.23290043721454
KIND = "finite-segment-endpoint-not-selected-source-chair"
NAMES = ("main-side wing knuckle", "turnout-side wing knuckle")
FIELDS = ("points", "gauge_face_points", "outer_face_points")


def fixture():
    """Invent eight continuous rail paths under two 12 mm square timbers."""
    positions, rails, timbers, witnesses, companions = {}, {}, {}, {}, {}
    for side in ("A", "B"):
        owner, timber_id = f"XO-001-{side}001", f"XO-001:{side}:X3-X"
        timber_source = {"local_x": SOURCE_STATION, "crossing_suffix": "X",
                         "turnout_geometry_revision": 2}
        timbers[timber_id] = {
            "stable_identity": timber_id, "identifier": "X3-X",
            "prototype_reference": "X3-X", "section": "crossing wing front",
            "crossover_identity": "XO-001", "parent_turnout_identity": owner,
            "turnout_side": side, "source_configuration": timber_source,
            "outline_polygon": [[-6, -6], [6, -6], [6, 6], [-6, 6]],
        }
        for index, name in enumerate(NAMES):
            y = -2.0 if index == 0 else 2.0
            for continuing in (False, True):
                rail_name = (name.replace("knuckle", "rail")
                             if continuing else name)
                rail_id = owner + ":rail:" + rail_name.replace(" ", "-")
                key = identity(side, "X3-X", rail_name)
                start, end = ((0.0, 4.0) if continuing else (-3.0, 0.0))
                configuration = {
                    "rail_geometry_revision": 2,
                    "gauge_face": rail_name + " gauge face",
                    "outer_face": rail_name + " outer face",
                    "gauge_orientation_source": (
                        "mapped named turnout rail faces"
                    ),
                }
                role = "wing rail" if continuing else "wing rail knuckle"
                rail = {
                    "stable_identity": rail_id, "name": rail_name,
                    "parent_turnout_identity": owner,
                    "parent_crossover_identity": "XO-001",
                    "turnout_side": side,
                    "rail_role": role, "source_configuration": configuration,
                }
                for field, offset in zip(FIELDS, (0.0, -0.45, 0.45)):
                    rail[field] = [[start, y + offset], [end, y + offset]]
                rails[rail_id] = rail
                positions[key] = {
                    "stable_chair_position_identity": key,
                    "parent_turnout_identity": owner,
                    "parent_crossover_identity": "XO-001",
                    "rail_identity": rail_id, "rail_name": rail_name,
                    "rail_role": role, "timber_identity": timber_id,
                    "timber_identifier": "X3-X",
                    "prototype_timber_identifier": "X3-X",
                    "chair_code": 23 if continuing else 22,
                    "chair_code_label": "XA" if continuing else "XN",
                    "special_assignment_deferred": True,
                    "assignment_complete_in_current_stage": False,
                    "assignment_status": (
                        "deferred to special-chair assignment"
                    ),
                    "mandatory": True, "deliberate_omission": False,
                    "centre_point": [1.0 if continuing else end, y],
                    "rail_station": 1.0 if continuing else end - start,
                    "source_configuration": {
                        "rail": copy.deepcopy(configuration),
                        "timber": copy.deepcopy(timber_source),
                    },
                }
        selected = identity(side, "X3-X", "turnout-side wing rail")
        mate = identity(side, "X3-X", "main-side wing rail")
        companions[mate] = selected
        witnesses[selected] = {
            "family": "XA", "source_chair_code": 23,
            "context_id": "RH-X3-X", "source_station_mm": SOURCE_STATION,
            "source_context_sha256": CONTEXT_HASH, "source_rail_code": 3,
            "mate_position_ids": [mate], "physical_fit": "NOT_PROVED",
            "placement_convention": "source-paired-common-timber-frame.v1",
        }
    return positions, rails, timbers, witnesses, companions


def qualify(source):
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_endpoint_exclusions",
    )
    return operation.qualify_knuckle_exclusions(*source)


def public_fixture():
    """Add independent endpoint paths to the established 355-record fixture."""
    data, pairs, splits = split_public_fixture()
    endpoints = fixture()
    for key, record in endpoints[0].items():
        data[0][3][key].update(copy.deepcopy(record))
    for timber in data[0][4]:
        if timber["stable_identity"] in endpoints[2]:
            timber.update(copy.deepcopy(
                endpoints[2][timber["stable_identity"]],
            ))
    splits[0].context.update(station_mm=SOURCE_STATION,
                             context_sha256=CONTEXT_HASH)
    return data, pairs, splits, list(endpoints[1].values())


def run_public(source, **options):
    """Keep actual classification, receipt composition and late validation."""
    data, pairs, splits, rails = source
    original = binding.preview_private_catalogue_crossover_chairs

    def invoke(*args, **kwargs):
        kwargs.update(options)
        context = list(binding._open_source_context(*args[:3]))
        context[4] = rails
        with patch.object(binding, "_open_source_context",
                          return_value=tuple(context)):
            return original(*args, **kwargs)

    with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                      side_effect=invoke):
        return run_split_public(data, pairs, splits, enabled=True)


class CrossingEndpointContractTests(unittest.TestCase):
    def test_missing_source_qualification_refuses_before_source_access(self):
        with patch.object(binding, "_open_source_context") as opened:
            create = Mock()
            with self.assertRaises(ValueError):
                binding.preview_private_catalogue_crossover_chairs(
                    object(), object(), "XO-001", "unused", create,
                    classify_knuckle_exclusions=True,
                )
            opened.assert_not_called()
            create.assert_not_called()

    def test_strict_boolean_and_missing_stack_fail_before_source_access(self):
        invalid = [({"classify_knuckle_exclusions": value})
                   for value in (None, 0, 1, "true", [], {})]
        invalid += [dict(classify_knuckle_exclusions=True, **options)
                    for options in (
                        {"crossing_split_contexts_path": "splits"},
                        {"include_single_rail": True},
                        {"crossing_split_contexts_path": "splits",
                         "include_single_rail": True},
                    )]
        for options in invalid:
            with self.subTest(options=options), patch.object(
                binding, "_open_source_context",
            ) as opened:
                create = Mock()
                with self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        **options,
                    )
                opened.assert_not_called()
                create.assert_not_called()

    def test_default_false_and_session_forwarding_preserve_old_calls(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        operations = (method, binding.preview_private_catalogue_crossover_chairs)
        for operation in operations:
            self.assertIs(inspect.signature(operation).parameters[
                "classify_knuckle_exclusions"].default, False)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for options in ({}, {"classify_knuckle_exclusions": False},
                        {"classify_knuckle_exclusions": True}):
            with patch.object(
                binding, "preview_private_catalogue_crossover_chairs",
                return_value="receipt",
            ) as operation:
                self.assertEqual(method(session, "doc", "XO-001", "catalogue",
                                        **options), "receipt")
            expected = (options if options.get("classify_knuckle_exclusions")
                        else {})
            self.assertEqual(operation.call_args.kwargs, expected)


class CrossingEndpointSourceTests(unittest.TestCase):
    def test_four_exclusions_preserve_source_and_separate_fit_status(self):
        source = fixture()
        before = copy.deepcopy(source)
        result = qualify(source)
        expected = {identity(side, "X3-X", name)
                    for side in ("A", "B") for name in NAMES}
        self.assertEqual(set(result), expected)
        self.assertEqual(source, before)
        self.assertEqual(result, qualify(source))
        for key, row in result.items():
            self.assertEqual(row["exclusion_kind"], KIND)
            self.assertEqual(row["physical_status"],
                             "source-endpoint-exclusion")
            self.assertNotIn("supporting_position_id", row)
            self.assertNotIn("supporting_assembly_placed", row)
            evidence = row["source_endpoint_exclusion"]
            self.assertEqual(evidence["context_id"], "RH-X3-X")
            self.assertEqual(evidence["selected_source_family"], "XA")
            self.assertEqual(evidence["selected_source_chair_code"], 23)
            self.assertEqual(evidence["source_station_mm"], SOURCE_STATION)
            self.assertEqual(evidence["source_context_sha256"], CONTEXT_HASH)
            self.assertIs(evidence["canonical_position_is_rail_endpoint"],
                          True)
            self.assertEqual(evidence["endpoint_continuity_fields"],
                             list(FIELDS))
            self.assertEqual(evidence["physical_fit"], "NOT_ASSESSED")
            continuing = source[0][key]["rail_identity"].replace(
                "knuckle", "rail",
            )
            self.assertEqual(evidence["continuing_rail_identity"], continuing)

    def test_rigid_changes_and_winding_preserve_both_sides(self):
        for angle in (0.0, 0.37, math.pi):
            for reverse in (False, True):
                source = fixture()
                c, s = math.cos(angle), math.sin(angle)

                def transform(point):
                    x, y = point
                    return [17 + c*x - s*y, -23 + s*x + c*y]

                for rail in source[1].values():
                    for field in FIELDS:
                        rail[field] = [transform(p) for p in rail[field]]
                for position in source[0].values():
                    position["centre_point"] = transform(
                        position["centre_point"],
                    )
                for timber in source[2].values():
                    points = [transform(p) for p in timber["outline_polygon"]]
                    timber["outline_polygon"] = (
                        points[::-1] if reverse else points
                    )
                self.assertEqual(len(qualify(source)), 4)

    def test_missing_endpoint_and_identity_or_assignment_defects_fail(self):
        keys = [identity(side, "X3-X", name)
                for side in ("A", "B") for name in NAMES]
        for key in keys:
            source = fixture()
            del source[0][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                qualify(source)
        mutations = {
            "stable_chair_position_identity": "wrong",
            "parent_turnout_identity": "XO-001-B001",
            "parent_crossover_identity": "wrong",
            "rail_identity": "wrong", "rail_name": "wrong",
            "rail_role": "wing rail", "timber_identity": "wrong",
            "prototype_timber_identifier": "X2-Y", "timber_identifier": "X2-Y",
            "chair_code": 23, "chair_code_label": "XA",
            "special_assignment_deferred": False, "deliberate_omission": True,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                source = fixture()
                source[0][keys[0]][field] = value
                with self.assertRaises(ValueError):
                    qualify(source)

    def test_endpoint_and_all_three_continuity_arrays_are_required(self):
        for defect in ("interior", "station", "rail-config", "timber-config",
                       "short", "nonfinite", "boolean", *FIELDS):
            with self.subTest(defect=defect):
                source = fixture()
                position = source[0][identity("A", "X3-X", NAMES[0])]
                rail = source[1][position["rail_identity"]]
                continuing = source[1][rail["stable_identity"].replace(
                    "knuckle", "rail",
                )]
                if defect == "interior":
                    position["centre_point"] = [-1.0, -2.0]
                elif defect == "station":
                    timber = source[2][position["timber_identity"]]
                    timber["source_configuration"]["local_x"] += 1
                elif defect.endswith("config"):
                    position["source_configuration"][defect.split("-")[0]] = {}
                elif defect == "short":
                    rail["points"] = rail["points"][-1:]
                elif defect in ("nonfinite", "boolean"):
                    rail["points"][0][0] = (math.nan
                                            if defect == "nonfinite" else True)
                else:
                    continuing[defect][0][0] += 0.001
                with self.assertRaises(ValueError):
                    qualify(source)

    def test_qualified_xa_context_owner_and_companion_are_required(self):
        for defect in ("missing", "context", "hash", "family", "code",
                       "station", "rail", "mate", "companion"):
            with self.subTest(defect=defect):
                source = fixture()
                key = identity("A", "X3-X", "turnout-side wing rail")
                witness = source[3][key]
                if defect == "missing":
                    del source[3][key]
                elif defect == "companion":
                    source[4].clear()
                else:
                    field, value = {
                        "context": ("context_id", "RH-X2-Y"),
                        "hash": ("source_context_sha256", "unqualified"),
                        "family": ("family", "XN"),
                        "code": ("source_chair_code", 22),
                        "station": ("source_station_mm", SOURCE_STATION + 1),
                        "rail": ("source_rail_code", 2),
                        "mate": ("mate_position_ids", []),
                    }[defect]
                    witness[field] = value
                with self.assertRaises(ValueError):
                    qualify(source)


class CrossingEndpointReceiptTests(unittest.TestCase):
    def test_four_exclusions_keep_261_assemblies_and_349_positions(self):
        source = public_fixture()
        before = copy.deepcopy(source[0][0][3:5])
        old_groups, old, _, old_options = run_public(source)
        groups, receipt, _, options = run_public(
            source, classify_knuckle_exclusions=True,
        )
        self.assertEqual(source[0][0][3:5], before)
        self.assertEqual(groups, old_groups)
        self.assertEqual(options, old_options)
        self.assertEqual(receipt["selected_positions"],
                         old["selected_positions"])
        self.assertEqual(receipt["original_analytical_exclusions"],
                         old["original_analytical_exclusions"])
        for field, expected in (
            ("analysis_position_count", 355), ("placement_count", 261),
            ("existing_shared_support_count", 48),
            ("represented_source_position_count", 349),
            ("unrepresented_source_position_count", 6),
            ("finite_source_exclusion_count", 2),
            ("source_endpoint_exclusion_count", 4),
            ("unresolved_source_position_count", 0),
        ):
            self.assertEqual(receipt[field], expected, field)
        old_rows = {r["position_id"]: r for r in old["excluded_positions"]}
        rows = {r["position_id"]: r for r in receipt["excluded_positions"]}
        changed = {key for key in rows if rows[key] != old_rows[key]}
        self.assertEqual(changed, {identity(side, "X3-X", name)
                                  for side in ("A", "B") for name in NAMES})
        for key in changed:
            self.assertEqual(rows[key]["exclusion_kind"], KIND)
            self.assertEqual(rows[key]["original_exclusion"],
                             old_rows[key]["original_exclusion"])
            self.assertEqual(rows[key]["chair_code"], 22)
            self.assertEqual(rows[key]["chair_label"], "XN")
            self.assertNotIn("supporting_position_id", rows[key])
            self.assertNotIn("supporting_assembly_placed", rows[key])
        explicit_false = run_public(source, classify_knuckle_exclusions=False)
        self.assertEqual(explicit_false[1], old)

    def test_late_endpoint_rail_timber_and_context_mutations_fail(self):
        for defect in ("endpoint", "interior-rail", "timber", "context"):
            with self.subTest(defect=defect):
                source = public_fixture()
                _, _, verify, _ = run_public(
                    source, classify_knuckle_exclusions=True,
                )
                with patch.object(binding, "_e001_exclusions",
                                  return_value=source[0][5]):
                    verify()
                    position = source[0][0][3][
                        identity("A", "X3-X", NAMES[0])
                    ]
                    if defect == "endpoint":
                        position["centre_point"][0] += 1
                    elif defect == "interior-rail":
                        source[3][0]["points"][0][0] -= 1
                    elif defect == "timber":
                        timber = source[0][0][4][-1]
                        timber["source_configuration"]["local_x"] += 1
                    else:
                        position["source_configuration"]["rail"]["heave"] = True
                    with self.assertRaises(ValueError):
                        verify()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: source-qualified endpoint exclusions; geometry unchanged")
