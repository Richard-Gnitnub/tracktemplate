#!/usr/bin/env python3
"""Check fixed XA/BB source admission without constructing geometry."""

import copy
import importlib
import inspect
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    transition_workflow,
)
from tracktemplate.application.chair_catalogue import (  # noqa: E402
    CatalogueChairError,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
)
import validate_phase9b_catalogue_crossing_pairs as pair_tests  # noqa: E402
from validate_phase9b_catalogue_crossing_zy import (  # noqa: E402
    identity,
    zy_source,
)

CONTEXTS = ("RH-X3-X", "RH-X5-B")
FAMILIES = ("XA", "BB")
COUNTS = (33, 43)
SOURCE_CODES = (23, 26)
RAILS = (
    (("turnout-side wing rail", 23, "XA"),
     ("main-side wing rail", 23, "XA")),
    (("vee point rail", 26, "BB/BC"),
     ("vee splice rail", 25, "AB"),
     ("turnout-side wing flare", 25, "AB"),
     ("main-side wing flare", 25, "AB")),
)
KNUCKLES = ("main-side wing knuckle", "turnout-side wing knuckle")


def split_source(*, toe=500.0, heading=0.0):
    """Invent host values; preserve independently observed rail ownership."""
    module, document, signature, _, _, selected, data = zy_source(
        toe=toe, heading=heading,
    )
    positions, timbers, selections = {}, [], []
    for index, context in enumerate(CONTEXTS):
        timber, station = context[3:], 70.0 + 10 * index
        recipe = copy.deepcopy(selected[0].context)
        recipe.update(context_id=context, timber_id=timber, station_mm=station,
                      family=FAMILIES[index], chair_code=SOURCE_CODES[index])
        selections.append(SimpleNamespace(
            run=context, label=FAMILIES[index], context=recipe,
            metadata=copy.deepcopy(selected[0].metadata),
            model_sha256=f"invented-model-{index}",
        ))
        for side in ("A", "B"):
            owner, timber_id = f"XO-001-{side}001", f"XO-001:{side}:{timber}"
            source = {"local_x": station}
            timbers.append({"stable_identity": timber_id,
                            "source_configuration": source,
                            "parent_turnout_identity": owner,
                            "prototype_identifier": timber,
                            "identifier": timber})
            records = RAILS[index] + (
                tuple((rail, 22, "XN") for rail in KNUCKLES)
                if index == 0 else ()
            )
            for rail, code, label in records:
                key = identity(side, timber, rail)
                positions[key] = {
                    "stable_chair_position_identity": key,
                    "parent_crossover_identity": "XO-001",
                    "parent_turnout_identity": owner,
                    "prototype_timber_identifier": timber,
                    "timber_identifier": timber, "timber_identity": timber_id,
                    "rail_identity": owner + ":rail:" + rail.replace(" ", "-"),
                    "rail_name": rail, "chair_code": code,
                    "chair_code_label": label,
                    "special_assignment_deferred": True,
                    "deliberate_omission": False,
                    "source_configuration": {"timber": copy.deepcopy(source)},
                }
    return module, document, signature, positions, timbers, selections, data


def prepare(source):
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_pair_placement",
    )
    with patch.object(operation, "prepare_crossing_split_catalogue",
                      return_value=tuple(source[5])):
        return operation.prepare_crossing_splits(*source[:5], 0.8, "invented")


class CrossingSplitContractTests(unittest.TestCase):
    def test_optional_path_forwards_only_when_supplied(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (method, binding.preview_private_catalogue_crossover_chairs):
            self.assertIsNone(inspect.signature(operation).parameters[
                "crossing_split_contexts_path"].default)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for value in (None, "private-splits"):
            with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                              return_value="receipt") as operation:
                self.assertEqual(method(
                    session, "doc", "XO-001", "catalogue",
                    crossing_split_contexts_path=value,
                ), "receipt")
            self.assertEqual(operation.call_args.kwargs,
                             {"crossing_split_contexts_path": value}
                             if value is not None else {})

    def test_prerequisite_stack_refuses_before_source_access(self):
        for options in ({}, {"include_single_rail": False},
                        {"include_single_rail": True}):
            with self.subTest(options=options), patch.object(
                binding, "_open_source_context",
            ) as opened:
                create = Mock()
                with self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        crossing_split_contexts_path="private-splits", **options,
                    )
                opened.assert_not_called()
                create.assert_not_called()


class CrossingSplitPlacementTests(unittest.TestCase):
    def test_four_assemblies_twelve_records_leave_four_knuckles_unsupported(self):
        source = split_source()
        before = copy.deepcopy(source[3:6])
        groups, witnesses, companions, verify = prepare(source)
        self.assertEqual(tuple(groups), CONTEXTS)
        self.assertEqual([len(group) for group in groups.values()], [2, 2])
        self.assertEqual(len(witnesses), 4)
        self.assertEqual(len(companions), 8)
        self.assertEqual(source[3:6], before)
        for index, context in enumerate(CONTEXTS):
            for side in ("A", "B"):
                keys = [identity(side, context[3:], rail)
                        for rail, _, _ in RAILS[index]]
                owner, mates = keys[0], keys[1:]
                self.assertEqual({key: companions[key] for key in mates},
                                 dict.fromkeys(mates, owner))
                self.assertEqual(set(witnesses[owner]["mate_position_ids"]),
                                 set(mates))
                self.assertEqual(witnesses[owner]["family"], FAMILIES[index])
                self.assertEqual(witnesses[owner]["source_chair_code"],
                                 SOURCE_CODES[index])
                self.assertEqual(witnesses[owner]["source_rail_code"], 3)
                self.assertEqual(witnesses[owner]["physical_fit"], "NOT_PROVED")
        for side in ("A", "B"):
            for rail in KNUCKLES:
                key = identity(side, "X3-X", rail)
                self.assertNotIn(key, witnesses)
                self.assertNotIn(key, companions)
        self.assertEqual(prepare(source)[:3], (groups, witnesses, companions))
        verify()

    def test_independent_world_coordinates_and_finite_station_boundaries(self):
        for heading in (0.0, 0.37, math.pi / 2, -math.pi):
            groups = prepare(split_source(heading=heading))[0]
            for index, context in enumerate(CONTEXTS):
                for frame in groups[context]:
                    self.assertIsInstance(frame, PairedChairPlacement)
                    direction = 1 if "-a-" in frame.position_id else -1
                    station = 500 + direction * (70 + 10 * index)
                    angle = heading + (0 if direction == 1 else math.pi)
                    c, s = math.cos(angle), math.sin(angle)
                    for nx, ny, nz in ((0, 0, 0), (-2, -3.45, 1.25),
                                       (4, 18, -0.5)):
                        x, y = -nx, 7.8 - ny
                        expected = (17 + station * math.cos(heading) + c*x - s*y,
                                    -23 + station * math.sin(heading) + s*x + c*y,
                                    0.8 + nz)
                        for actual, wanted in zip(
                            frame.transform_point((nx, ny, nz)), expected,
                        ):
                            self.assertAlmostEqual(actual, wanted, places=11)
        for toe in (80.0, 920.0):
            self.assertEqual(sum(map(len, prepare(split_source(toe=toe))[0]
                                    .values())), 4)
        for toe in (79.0, 921.0):
            with self.subTest(toe=toe), self.assertRaises(ValueError):
                prepare(split_source(toe=toe))

    def test_every_missing_supported_record_and_wrong_ownership_fails(self):
        source = split_source()
        supported = [key for key, row in source[3].items()
                     if row["rail_name"] not in KNUCKLES]
        for key in supported:
            with self.subTest(missing=key):
                changed = split_source()
                del changed[3][key]
                with self.assertRaises(ValueError):
                    prepare(changed)
        for defect in ("duplicate", "id", "rail", "owner", "code", "label",
                       "deferred", "omission", "timber-id", "timber-station",
                       "companion-timber"):
            with self.subTest(defect=defect):
                changed = split_source()
                key = identity("B", "X5-B", RAILS[1][-1][0])
                row = changed[3][key]
                if defect == "duplicate":
                    changed[3]["extra-owner"] = copy.deepcopy(row)
                elif defect == "timber-station":
                    changed[4][-1]["source_configuration"]["local_x"] += 1
                elif defect == "companion-timber":
                    row["source_configuration"]["timber"]["local_x"] += 1
                else:
                    field, value = {
                        "id": ("stable_chair_position_identity", "wrong"),
                        "rail": ("rail_identity", "wrong"),
                        "owner": ("parent_turnout_identity", "wrong"),
                        "code": ("chair_code", 26),
                        "label": ("chair_code_label", "BB/BC"),
                        "deferred": ("special_assignment_deferred", False),
                        "omission": ("deliberate_omission", True),
                        "timber-id": ("timber_identity", "XO-001:A:X5-B"),
                    }[defect]
                    row[field] = value
                with self.assertRaises(ValueError):
                    prepare(changed)

    def test_wrong_context_and_nonfinite_input_fail_closed(self):
        for defect in ("source", "host", "context", "family", "station",
                       "timber", "source-code", "curving", "direction",
                       "nonfinite-point", "nonfinite-heading"):
            with self.subTest(defect=defect):
                source = split_source()
                recipe = source[5][0].context
                if defect in ("source", "host"):
                    source[5][0].metadata[defect + "_context_sha256"] = "wrong"
                elif defect == "curving":
                    recipe["native_frame"]["common_timber_curving_applied"] = True
                elif defect == "direction":
                    source[0]._turnout_orientation_sign = lambda _: 0
                elif defect.startswith("nonfinite"):
                    source[0].interpolate_alignment_station = lambda *_: (
                        SimpleNamespace(x=math.nan if defect.endswith("point")
                                        else 0, y=0),
                        math.inf if defect.endswith("heading") else 0,
                    )
                else:
                    field, value = {
                        "context": ("context_id", "RH-X5-B"),
                        "family": ("family", "BB"),
                        "station": ("station_mm", 71),
                        "timber": ("timber_id", "X5-B"),
                        "source-code": ("chair_code", 25),
                    }[defect]
                    recipe[field] = value
                with self.assertRaises(ValueError):
                    prepare(source)

    def test_late_host_source_timber_and_object_replacement_fail(self):
        for defect in ("host", "position", "timber", "host-object"):
            with self.subTest(defect=defect):
                source = split_source()
                verify = prepare(source)[3]
                verify()
                if defect == "host":
                    source[6]["HostA"]["points"][0].x += 1
                elif defect == "position":
                    source[3][identity("A", "X3-X", KNUCKLES[0])][
                        "chair_code"] = 23
                elif defect == "timber":
                    source[4][-1]["source_configuration"]["local_x"] += 1
                else:
                    original = source[1].getObject
                    source[1].getObject = lambda name: copy.copy(original(name))
                with self.assertRaises(ValueError):
                    verify()


def reader_fixture(root, defect=None):
    """Reuse synthetic bookkeeping; do not represent native geometry."""
    with patch.object(pair_tests, "pair_source", split_source), patch.object(
        pair_tests, "COUNTS", COUNTS,
    ), patch.object(pair_tests, "SOURCE_CODES", SOURCE_CODES):
        return pair_tests.reader_fixture(root, defect)


class CrossingSplitReaderTests(unittest.TestCase):
    def test_pin_and_exact_complete_selection_are_required(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_pair_catalogue",
        )
        self.assertEqual(catalogue.CROSSING_SPLIT_CONTEXT_IDS, CONTEXTS)
        for value in ((), [], (object(),) * 2):
            with self.subTest(value=value), self.assertRaises(CatalogueChairError):
                catalogue.verify_crossing_split_catalogue(value)
        with tempfile.TemporaryDirectory(prefix="crossing-split-pin-") as temp:
            path, digest = reader_fixture(Path(temp).resolve())
            with self.assertRaises(CatalogueChairError):
                catalogue.prepare_crossing_split_catalogue(path)
            with self.assertRaises(TypeError):
                catalogue.prepare_crossing_split_catalogue(path, sha256=digest)
            with patch.object(catalogue, "CROSSING_PAIR_CATALOGUE_SHA256", digest):
                selections = catalogue.prepare_crossing_split_catalogue(path)
                self.assertEqual(tuple(s.run for s in selections), CONTEXTS)
                self.assertEqual(tuple(s.label for s in selections), FAMILIES)
                self.assertEqual(tuple(len(s.components) for s in selections),
                                 COUNTS)
                catalogue.verify_crossing_split_catalogue(selections)
                for invalid in (selections[::-1], selections[:1],
                                selections + selections[:1]):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.verify_crossing_split_catalogue(invalid)
                (Path(temp) / "RH-X5-B-recipe.json").write_text("{}")
                with self.assertRaises(CatalogueChairError):
                    catalogue.verify_crossing_split_catalogue(selections)

    def test_semantic_and_binding_defects_fail_even_with_rehashed_fixture(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_pair_catalogue",
        )
        for defect in ("wrong-rail", "wrong-source-code", "wrong-family",
                       "component-count", "component-order", "model-binding",
                       "qualification", "rights"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(
                prefix="crossing-split-negative-",
            ) as temp:
                path, digest = reader_fixture(Path(temp).resolve(), defect)
                with patch.object(catalogue, "CROSSING_PAIR_CATALOGUE_SHA256",
                                  digest):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.prepare_crossing_split_catalogue(path)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: fixed XA/BB source admission and unchanged exclusions")
