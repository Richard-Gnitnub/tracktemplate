#!/usr/bin/env python3
"""Check bounded AA/CD/DD/EF admission with invented analytical inputs.

The world-coordinate oracle does not call a product placement helper.
These tests construct no geometry and grant no native or fit acceptance.
"""

import copy
import importlib
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET
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
from validate_phase9b_catalogue_crossing_zy import (  # noqa: E402
    identity as zy_identity,
    reader_fixture as zy_reader_fixture,
    zy_source,
)
from validate_phase9b_chair_catalogue import (  # noqa: E402
    synthetic_archive,
    synthetic_document,
)

CONTEXTS = ("RH-X4-A", "RH-X6-C", "RH-X7-D", "RH-X8-E")
FAMILIES = ("AA", "CD", "DD", "EF")
COUNTS = (42, 27, 33, 33)
CODES = ((25, "AB"), (26, "BB/BC"), (27, "CD"), (28, "EF"))
SOURCE_CODES = (24, 27, 27, 28)
WING_RAILS = ("turnout-side wing rail", "main-side wing rail")
VEE_RAILS = ("vee point rail", "vee splice rail")
PIN = "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"


def identity(side, timber, rail):
    """Keep the independently observed long-timber chair identities."""
    inherited = {("A", "X8-E"): 1, ("B", "X6-C"): 5,
                 ("B", "X7-D"): 6, ("B", "X8-E"): 7}
    if (side, timber) in inherited:
        return (f"XO-001:chair:xo-001-inherited-long-{side.lower()}-"
                f"{inherited[side, timber]:03}:" + rail.replace(" ", "-"))
    return zy_identity(side, timber, rail)


def pair_source(*, toe=500.0, heading=0.0):
    """Reuse host fixtures; invent sixteen records and a long timber."""
    module, document, signature, _, _, selected, data = zy_source(
        toe=toe, heading=heading,
    )
    positions, timbers, selections = {}, [], []
    for index, context_id in enumerate(CONTEXTS):
        timber = context_id[3:]
        station = 70.0 + 10 * index
        recipe = copy.deepcopy(selected[0].context)
        recipe.update(context_id=context_id, timber_id=timber,
                      station_mm=station, family=FAMILIES[index],
                      chair_code=SOURCE_CODES[index])
        selections.append(SimpleNamespace(
            run=context_id, label=FAMILIES[index], context=recipe,
            metadata=copy.deepcopy(selected[0].metadata),
            model_sha256=f"invented-model-{index}",
        ))
        for side in ("A", "B"):
            timber_id = f"XO-001:{side}:{timber}"
            timber_config = {"local_x": station}
            actual_timber = timber
            if (side == "A" and index == 3) or (side == "B" and index > 0):
                timber_config = {
                    "path_station": station,
                    "extended_source_timber_identity": timber_id,
                }
                number = 1 if side == "A" else index + 4
                timber_id = f"XO-001:INHERITED-LONG:{side}:{number:03}"
                actual_timber = f"{side}L{number:03}"
            timbers.append({"stable_identity": timber_id,
                            "source_configuration": timber_config,
                            "parent_turnout_identity": (
                                "XO-001:ENVELOPE" if "INHERITED" in timber_id
                                else f"XO-001-{side}001"),
                            "prototype_identifier": timber,
                            "identifier": actual_timber})
            for rail in WING_RAILS if index == 0 else VEE_RAILS:
                key = identity(side, timber, rail)
                positions[key] = {
                    "stable_chair_position_identity": key,
                    "parent_crossover_identity": "XO-001",
                    "parent_turnout_identity": f"XO-001-{side}001",
                    "prototype_timber_identifier": timber,
                    "timber_identifier": actual_timber,
                    "timber_identity": timber_id,
                    "rail_identity": f"XO-001-{side}001:rail:"
                    + rail.replace(" ", "-"), "rail_name": rail,
                    "chair_code": CODES[index][0],
                    "chair_code_label": CODES[index][1],
                    "special_assignment_deferred": True,
                    "deliberate_omission": False,
                    "source_configuration": {
                        "timber": copy.deepcopy(timber_config),
                    },
                }
    return module, document, signature, positions, timbers, selections, data


def prepare(source):
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_pair_placement",
    )
    with patch.object(operation, "prepare_crossing_pair_catalogue",
                      return_value=tuple(source[5])):
        return operation.prepare_crossing_pairs(*source[:5], 0.8, "invented")


class CrossingPairPlacementTests(unittest.TestCase):
    def test_sixteen_positions_eight_assemblies_preserve_source_identities(self):
        source = pair_source()
        before = copy.deepcopy(source[3:6])
        groups, witnesses, companions, verify = prepare(source)
        self.assertEqual(tuple(groups), CONTEXTS)
        self.assertEqual([len(g) for g in groups.values()], [2] * 4)
        self.assertEqual(len(witnesses), 8)
        self.assertEqual(len(companions), 8)
        self.assertEqual(source[3:6], before)
        for index, context in enumerate(CONTEXTS):
            rails = WING_RAILS if index == 0 else VEE_RAILS
            for side in ("A", "B"):
                owner, mate = [identity(side, context[3:], r) for r in rails]
                self.assertEqual(companions[mate], owner)
                self.assertEqual(witnesses[owner]["family"], FAMILIES[index])
                self.assertEqual(witnesses[owner]["source_chair_code"],
                                 SOURCE_CODES[index])
                self.assertEqual(witnesses[owner]["source_rail_code"], 3)
                self.assertEqual(witnesses[owner]["physical_fit"], "NOT_PROVED")
                frame = next(p for p in groups[context]
                             if p.position_id == owner)
                self.assertEqual(frame.timber_id,
                                 source[3][owner]["timber_identity"])
        verify()

    def test_direct_world_oracle_both_directions_and_headings(self):
        for heading in (0.0, 0.37, math.pi / 2, -math.pi):
            source = pair_source(heading=heading)
            groups, _, _, _ = prepare(source)
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
                        expected = (
                            17 + station * math.cos(heading) + c * x - s * y,
                            -23 + station * math.sin(heading) + s * x + c * y,
                            0.8 + nz,
                        )
                        for actual, wanted in zip(
                            frame.transform_point((nx, ny, nz)), expected,
                        ):
                            self.assertAlmostEqual(actual, wanted, places=11)

    def test_finite_host_endpoints_and_outside_station_rejection(self):
        for toe in (100.0, 900.0):
            self.assertEqual(sum(map(len, prepare(pair_source(toe=toe))[0]
                                    .values())), 8)
        for toe in (99.0, 901.0):
            with self.subTest(toe=toe), self.assertRaises(ValueError):
                prepare(pair_source(toe=toe))

    def test_missing_wrong_and_duplicate_canonical_positions_are_rejected(self):
        for defect in ("missing-owner", "missing-mate", "duplicate", "id",
                       "rail", "owner", "code", "label", "deferred",
                       "omission", "timber-id", "timber-station",
                       "inherited-source", "inherited-station"):
            with self.subTest(defect=defect):
                source = pair_source()
                key = identity("B", "X6-C", VEE_RAILS[0])
                position = source[3][key]
                if defect == "missing-owner":
                    del source[3][key]
                elif defect == "missing-mate":
                    del source[3][identity("B", "X6-C", VEE_RAILS[1])]
                elif defect == "duplicate":
                    source[3]["duplicate"] = copy.deepcopy(position)
                elif defect == "timber-station":
                    source[4][0]["source_configuration"]["local_x"] += 1
                elif defect in ("inherited-source", "inherited-station"):
                    field = ("extended_source_timber_identity"
                             if defect == "inherited-source" else "path_station")
                    position["source_configuration"]["timber"][field] = "wrong"
                else:
                    field, value = {
                        "id": ("stable_chair_position_identity", "wrong"),
                        "rail": ("rail_identity", "wrong"),
                        "owner": ("parent_turnout_identity", "wrong"),
                        "code": ("chair_code", 27),
                        "label": ("chair_code_label", "CD"),
                        "deferred": ("special_assignment_deferred", False),
                        "omission": ("deliberate_omission", True),
                        "timber-id": ("timber_identity", "XO-001:B:X6-C"),
                    }[defect]
                    position[field] = value
                with self.assertRaises(ValueError):
                    prepare(source)

    def test_source_binding_recipe_and_numeric_inputs_fail_closed(self):
        for defect in ("source", "host", "context", "family", "station",
                       "timber", "source-code", "curving", "direction",
                       "nonfinite-point", "nonfinite-heading"):
            with self.subTest(defect=defect):
                source = pair_source()
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

    def test_late_host_identity_position_and_inherited_timber_changes_fail(self):
        for defect in ("host", "position", "timber", "host-object"):
            with self.subTest(defect=defect):
                source = pair_source()
                verify = prepare(source)[3]
                verify()
                if defect == "host":
                    source[6]["HostA"]["points"][0].x += 1
                elif defect == "position":
                    source[3][identity("A", "X4-A", WING_RAILS[0])][
                        "chair_code"] = 24
                elif defect == "timber":
                    source[4][-1]["source_configuration"]["path_station"] += 1
                else:
                    original = source[1].getObject
                    source[1].getObject = lambda name: copy.copy(original(name))
                with self.assertRaises(ValueError):
                    verify()

    def test_optional_path_defaults_none_and_session_omits_none(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (method, binding.preview_private_catalogue_crossover_chairs):
            self.assertIsNone(inspect.signature(operation).parameters[
                "crossing_pair_contexts_path"].default)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for value in (None, "private-pairs"):
            with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                              return_value="receipt") as operation:
                self.assertEqual(method(
                    session, "doc", "XO-001", "catalogue",
                    crossing_pair_contexts_path=value,
                ), "receipt")
            self.assertEqual(operation.call_args.kwargs,
                             {"crossing_pair_contexts_path": value}
                             if value is not None else {})

    def test_single_rail_stack_required_before_source_access(self):
        for options in ({}, {"include_single_rail": False},
                        {"include_single_rail": True}):
            with self.subTest(options=options), patch.object(
                binding, "_open_source_context",
            ) as opened:
                create = Mock()
                with self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        crossing_pair_contexts_path="private-pairs", **options,
                    )
                opened.assert_not_called()
                create.assert_not_called()


def reader_fixture(root, defect=None):
    """Extend synthetic catalogue bookkeeping, never native geometry."""
    path, _digest = zy_reader_fixture(root)
    manifest = json.loads(path.read_text())
    qualification = json.loads(Path(manifest["qualification"]["path"]).read_text())

    def store(name, value):
        content = (value if isinstance(value, bytes) else
                   json.dumps(value, sort_keys=True).encode())
        target = root / name
        target.write_bytes(content)
        return {"path": str(target),
                "sha256": hashlib.sha256(content).hexdigest()}

    for index, selection in enumerate(pair_source()[5]):
        context_id, family = selection.run, selection.label
        recipe = copy.deepcopy(selection.context)
        recipe["sample_kind"] = "fixture_timber_" + context_id[3:]
        recipe["native_frame"].update(
            hand_i=-1, native_from_source=[[-1, 0, 0, 0],
                                          [0, -1, 0, -0.45],
                                          [0, 0, 1, 149 / 60],
                                          [0, 0, 0, 1]],
        )
        if index == 0 and defect == "wrong-rail":
            recipe["context"]["rail_code"] = 2
        if index == 0 and defect == "wrong-source-code":
            recipe["chair_code"] = 25
        if index == 0 and defect == "wrong-family":
            recipe["family"] = "BB"
        document = synthetic_document()
        objects, details = document.find("Objects"), document.find("ObjectData")
        obj, detail = copy.deepcopy(objects[0]), copy.deepcopy(details[0])
        objects.clear()
        details.clear()
        names = tuple(f"{family}Part{i:02d}" for i in range(COUNTS[index]))
        members = []
        for name in names:
            first, second = copy.deepcopy(obj), copy.deepcopy(detail)
            first.set("name", name)
            second.set("name", name)
            second.find(".//Part").set("file", name + ".Shape.brp")
            objects.append(first)
            details.append(second)
            members.append((name + ".Shape.brp", b"SYNTHETIC NO GEOMETRY"))
        model = store(context_id + ".FCStd", synthetic_archive(members=[
            ("Document.xml", ET.tostring(document)), *members,
        ]))
        result = store(context_id + "-result.json", {
            family: {"status": "PASS", "native_reload": "PASS"},
        })
        recipe_binding = store(context_id + "-recipe.json", [recipe])
        execution = store(context_id + "-execution.json", {
            "status": "PASS", "context_id": context_id,
            "model_hashes": {family: model["sha256"]},
            "result_sha256": result["sha256"],
            "source_recipe_binding": recipe_binding,
            "native_reload": "PASS", "fixing_proof": "PASS",
        })
        record = {
            "status": "PASS", "native_reload": "PASS", "fixing_proof": "PASS",
            "family": family, "context_id": context_id,
            "timber_id": context_id[3:], "chair_code": SOURCE_CODES[index],
            "source_station_mm": recipe["station_mm"], "source_recipe": recipe,
            "model": model, "receipt": result, "result_receipt": result,
            "execution_receipt": execution,
            "components": [{"name": name} for name in names],
            "component_count": COUNTS[index],
        }
        if index == 0 and defect == "component-count":
            record["component_count"] -= 1
        if index == 0 and defect == "component-order":
            record["components"].reverse()
        if index == 0 and defect == "model-binding":
            record["model"] = dict(model, sha256="0" * 64)
        qualification["contexts"][context_id] = record
    if defect == "qualification":
        qualification["documents_closed"] = False
    if defect == "rights":
        manifest["rights_cleared"] = True
    manifest["qualification"] = store("qualification.json", qualification)
    bound = store("catalogue.json", manifest)
    return path, bound["sha256"]


class CrossingPairReaderTests(unittest.TestCase):
    def test_private_pin_rejects_ad_hoc_admission_and_partial_selections(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_pair_catalogue",
        )
        self.assertEqual(catalogue.CROSSING_PAIR_CONTEXT_IDS, CONTEXTS)
        self.assertEqual(catalogue.CROSSING_PAIR_CATALOGUE_SHA256, PIN)
        with tempfile.TemporaryDirectory(prefix="crossing-pair-pin-") as temp:
            path, _digest = reader_fixture(Path(temp).resolve())
            with self.assertRaises(CatalogueChairError):
                catalogue.prepare_crossing_pair_catalogue(path)
            with self.assertRaises(TypeError):
                catalogue.prepare_crossing_pair_catalogue(path, sha256=PIN)
        for value in ((), [], (object(),) * 4):
            with self.subTest(value=value), self.assertRaises(CatalogueChairError):
                catalogue.verify_crossing_pair_catalogue(value)

    def test_reader_binds_exact_families_counts_order_and_late_files(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_pair_catalogue",
        )
        with tempfile.TemporaryDirectory(prefix="crossing-pair-reader-") as temp:
            root = Path(temp).resolve()
            path, digest = reader_fixture(root)
            with patch.object(catalogue, "CROSSING_PAIR_CATALOGUE_SHA256", digest):
                selections = catalogue.prepare_crossing_pair_catalogue(path)
                self.assertEqual(tuple(s.run for s in selections), CONTEXTS)
                self.assertEqual(tuple(s.label for s in selections), FAMILIES)
                self.assertEqual(tuple(len(s.components) for s in selections),
                                 COUNTS)
                catalogue.verify_crossing_pair_catalogue(selections)
                for invalid in (selections[::-1], selections[:3],
                                selections + selections[:1]):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.verify_crossing_pair_catalogue(invalid)
                (root / "RH-X8-E-recipe.json").write_text("{}", encoding="utf-8")
                with self.assertRaises(CatalogueChairError):
                    catalogue.verify_crossing_pair_catalogue(selections)

    def test_rehashed_semantic_and_binding_defects_remain_rejected(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_pair_catalogue",
        )
        for defect in ("wrong-rail", "wrong-source-code", "wrong-family",
                       "component-count", "component-order", "model-binding",
                       "qualification", "rights"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(
                prefix="crossing-pair-negative-",
            ) as temp:
                path, digest = reader_fixture(Path(temp).resolve(), defect)
                with patch.object(catalogue, "CROSSING_PAIR_CATALOGUE_SHA256",
                                  digest):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.prepare_crossing_pair_catalogue(path)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: eight crossing assemblies and sixteen canonical records")
