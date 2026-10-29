#!/usr/bin/env python3
"""Check bounded ZY admission and placement without native geometry.

Invented bookkeeping and frames exercise the contract independently of
retained geometry. Direct world-coordinate equations are the placement
oracle. Private source/native qualification remains separate evidence.
"""

import copy
import hashlib
import importlib
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

from tracktemplate.application.chair_catalogue import (  # noqa: E402
    CatalogueChairError,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    transition_workflow,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
)
from validate_phase9b_chair_catalogue import (  # noqa: E402
    synthetic_archive,
    synthetic_document,
)
from validate_phase9b_catalogue_paired_crossover import (  # noqa: E402
    invented_source,
)

CONTEXTS = ("RH-X1-Z", "RH-X2-Y")
RAILS = ("straight switch and closure rail", "curved switch and closure rail")
PIN = "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"


def identity(side, timber, rail):
    return (f"XO-001:chair:xo-001-{side.lower()}-{timber.lower()}:"
            + rail.replace(" ", "-"))


def zy_source(*, toe=500.0, heading=0.0):
    """Invent two finite straight hosts and eight canonical-shaped records."""
    module, document, signature, _, _, _, data = invented_source()
    configuration = json.loads(signature)["configuration"]
    for side in ("A", "B"):
        configuration["turnout_" + side.lower() + "_id"] = f"XO-001-{side}001"
        configuration["turnout_" + side.lower() + "_config"]["toe_chainage"] = toe
        data["Host" + side]["headings"] = [heading, heading]
    module.interpolate_alignment_station = lambda _host, s: (
        SimpleNamespace(x=17 + s * math.cos(heading),
                        y=-23 + s * math.sin(heading)), heading,
    )
    module.rea_c10_dimensions = lambda *_args: {"a_timber_x": 100.0}
    module.rea_c10_timber_layout = lambda *_args: [
        {"identifier": "X1-Z", "x": 70.0},
        {"identifier": "X2-Y", "x": 80.0},
    ]
    signature = json.dumps({"configuration": configuration}, sort_keys=True)
    records = {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        host = data["Host" + side]
        records[side] = dict(
            object_name="Host" + side,
            points=[[p.x, p.y] for p in host["points"]],
            headings=host["headings"], stations=host["stations"],
            total=host["total"], toe_chainage=toe,
            orientation=config["orientation"], handing=config["handing"],
        )
    metadata = {
        "source_context_sha256": hashlib.sha256(signature.encode()).hexdigest(),
        "host_context_sha256": hashlib.sha256(json.dumps(
            records, sort_keys=True, allow_nan=False,
        ).encode()).hexdigest(),
    }
    positions, timbers, selections = {}, [], []
    for index, context_id in enumerate(CONTEXTS):
        timber = context_id[3:]
        station = 70.0 + 10 * index
        recipe = {
            "family": "ZY", "context_id": context_id, "timber_id": timber,
            "station_mm": station, "chair_code": 21,
            "context_sha256": f"invented-context-{index}",
            "native_frame": {"common_timber_curving_applied": False},
            "context": {"hand_i": -1, "rail_code": 3, "keq_rad": 0,
                        "chair_y_mm": 16.5, "chair_k_rad": 0.0},
        }
        selections.append(SimpleNamespace(
            run=context_id, label="ZY", context=recipe,
            metadata=copy.deepcopy(metadata),
            model_sha256=f"invented-model-{index}",
        ))
        for side in ("A", "B"):
            timber_id = f"XO-001:{side}:{timber}"
            timber_config = {"local_x": station}
            timbers.append({"stable_identity": timber_id,
                            "source_configuration": timber_config})
            for rail in RAILS:
                key = identity(side, timber, rail)
                positions[key] = {
                    "stable_chair_position_identity": key,
                    "parent_crossover_identity": "XO-001",
                    "parent_turnout_identity": f"XO-001-{side}001",
                    "prototype_timber_identifier": timber,
                    "timber_identifier": timber, "timber_identity": timber_id,
                    "rail_identity": f"XO-001-{side}001:rail:"
                    + rail.replace(" ", "-"), "rail_name": rail,
                    "chair_code": 21 if index == 0 else 22,
                    "chair_code_label": "ZY" if index == 0 else "XN",
                    "special_assignment_deferred": True,
                    "deliberate_omission": False,
                    "source_configuration": {
                        "timber": copy.deepcopy(timber_config),
                    },
                }
    return module, document, signature, positions, timbers, selections, data


def prepare(source):
    operation = importlib.import_module(
        "tracktemplate.compatibility.chair_crossing_zy_placement",
    )
    with patch.object(operation, "prepare_zy_catalogue",
                      return_value=tuple(source[5])):
        return operation.prepare_crossing_zy(*source[:5], 0.8, "invented")


class ZYPlacementTests(unittest.TestCase):
    def test_eight_records_make_four_assemblies_without_rewriting_labels(self):
        source = zy_source()
        before = copy.deepcopy(source[3:6])
        groups, witnesses, companions, verify = prepare(source)
        owners = {identity(s, t, RAILS[0]) for s in ("A", "B")
                  for t in ("X1-Z", "X2-Y")}
        mates = {identity(s, t, RAILS[1]) for s in ("A", "B")
                 for t in ("X1-Z", "X2-Y")}
        self.assertEqual(tuple(groups), CONTEXTS)
        self.assertEqual([len(group) for group in groups.values()], [2, 2])
        self.assertEqual(set(witnesses), owners)
        self.assertEqual(set(companions), mates)
        self.assertEqual(set(companions.values()), owners)
        self.assertEqual(source[3:6], before)
        for key, witness in witnesses.items():
            self.assertEqual(witness["family"], "ZY")
            self.assertEqual(witness["placement_convention"],
                             "source-paired-common-timber-frame.v1")
            self.assertEqual(witness["physical_fit"], "NOT_PROVED")
            self.assertEqual(source[3][key]["chair_code"],
                             21 if "x1-z" in key else 22)
        verify()

    def test_direct_world_oracle_covers_both_directions_and_host_headings(self):
        native_points = ((0.0, 0.0, 0.0), (-2.0, -3.45, 1.25),
                         (4.0, 18.0, -0.5))
        for heading in (0.0, 0.37, math.pi / 2, -math.pi):
            source = zy_source(heading=heading)
            groups, witnesses, _, _ = prepare(source)
            for context_id, placements in groups.items():
                local_x = 70.0 if context_id == "RH-X1-Z" else 80.0
                for frame in placements:
                    self.assertIsInstance(frame, PairedChairPlacement)
                    direction = 1 if "-a-" in frame.position_id else -1
                    station = 500 + direction * local_x
                    origin = (17 + station * math.cos(heading),
                              -23 + station * math.sin(heading))
                    angle = heading + (0 if direction == 1 else math.pi)
                    c, s = math.cos(angle), math.sin(angle)
                    self.assertEqual(witnesses[frame.position_id][
                        "host_station_mm"], station)
                    for nx, ny, nz in native_points:
                        # Invert retained XY, then apply the host frame.
                        x, y = -nx, -ny - 0.45 + 8.25
                        expected = (origin[0] + c * x - s * y,
                                    origin[1] + s * x + c * y, 0.8 + nz)
                        actual = frame.transform_point((nx, ny, nz))
                        for observed, wanted in zip(actual, expected):
                            self.assertAlmostEqual(observed, wanted, places=11)

    def test_finite_host_boundaries_and_outside_stations(self):
        for toe in (80.0, 920.0):
            groups, _, _, _ = prepare(zy_source(toe=toe))
            self.assertEqual(sum(map(len, groups.values())), 4)
        for toe in (79.0, 921.0):
            with self.subTest(toe=toe), self.assertRaises(ValueError):
                prepare(zy_source(toe=toe))

    def test_incomplete_and_wrong_canonical_records_fail_closed(self):
        for defect in ("missing-owner", "missing-mate", "identity", "owner",
                       "rail", "code", "label", "deferred", "omitted",
                       "duplicate", "station", "source-station"):
            with self.subTest(defect=defect):
                source = zy_source()
                key = identity("A", "X2-Y", RAILS[0])
                position = source[3][key]
                if defect == "missing-owner":
                    del source[3][key]
                elif defect == "missing-mate":
                    del source[3][identity("A", "X2-Y", RAILS[1])]
                elif defect == "duplicate":
                    source[3]["duplicate"] = copy.deepcopy(position)
                elif defect == "station":
                    source[4][0]["source_configuration"]["local_x"] += 1
                elif defect == "source-station":
                    position["source_configuration"]["timber"]["local_x"] += 1
                else:
                    field, value = {
                        "identity": ("stable_chair_position_identity", "wrong"),
                        "owner": ("parent_turnout_identity", "wrong"),
                        "rail": ("rail_identity", "wrong"),
                        "code": ("chair_code", 21),
                        "label": ("chair_code_label", "ZY"),
                        "deferred": ("special_assignment_deferred", False),
                        "omitted": ("deliberate_omission", True),
                    }[defect]
                    position[field] = value
                with self.assertRaises(ValueError):
                    prepare(source)

    def test_context_hashes_and_recipe_mismatch_fail_before_placement(self):
        for defect in ("source", "host", "context-id", "family", "station",
                       "timber", "curving", "direction", "base-z"):
            with self.subTest(defect=defect):
                source = zy_source()
                recipe = source[5][0].context
                if defect in ("source", "host"):
                    source[5][0].metadata[defect + "_context_sha256"] = "wrong"
                elif defect == "curving":
                    recipe["native_frame"]["common_timber_curving_applied"] = True
                elif defect == "direction":
                    source[0]._turnout_orientation_sign = lambda _: 0
                elif defect == "base-z":
                    # A nonfinite canonical host interpolation must not pass.
                    source[0].interpolate_alignment_station = lambda *_: (
                        SimpleNamespace(x=math.nan, y=0.0), 0.0,
                    )
                else:
                    field, value = {"context-id": ("context_id", "RH-X3-X"),
                                    "family": ("family", "XA"),
                                    "station": ("station_mm", 71.0),
                                    "timber": ("timber_id", "X3-X")}[defect]
                    recipe[field] = value
                with self.assertRaises(ValueError):
                    prepare(source)

    def test_late_hosts_source_rows_and_source_timbers_are_reverified(self):
        for defect in ("host", "position", "timber", "host-object"):
            with self.subTest(defect=defect):
                source = zy_source()
                _, _, _, verify = prepare(source)
                verify()
                if defect == "host":
                    source[6]["HostA"]["points"][0].x += 1
                elif defect == "position":
                    source[3][next(iter(source[3]))]["chair_code"] = 25
                elif defect == "timber":
                    source[4][0]["source_configuration"]["local_x"] += 1
                else:
                    original = source[1].getObject
                    source[1].getObject = lambda name: copy.copy(original(name))
                with self.assertRaises(ValueError):
                    verify()


class ZYAdmissionTests(unittest.TestCase):
    def test_private_pin_and_complete_selection_contract(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_zy_catalogue",
        )
        self.assertEqual(catalogue.ZY_CONTEXT_IDS, CONTEXTS)
        self.assertEqual(catalogue.ZY_CATALOGUE_SHA256, PIN)
        with tempfile.TemporaryDirectory(prefix="zy-contract-") as temporary:
            path = Path(temporary) / "catalogue.json"
            path.write_text('{"synthetic":true}', encoding="utf-8")
            with self.assertRaises(CatalogueChairError):
                catalogue.prepare_zy_catalogue(path)
            with self.assertRaises(TypeError):
                catalogue.prepare_zy_catalogue(path, sha256=PIN)
        for value in ((), [], (object(),), (object(), object())):
            with self.subTest(value=value), self.assertRaises(CatalogueChairError):
                catalogue.verify_zy_catalogue(value)

    def test_optional_path_defaults_none_and_session_omits_none(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (method, binding.preview_private_catalogue_crossover_chairs):
            self.assertIsNone(inspect.signature(operation).parameters[
                "crossing_zy_contexts_path"].default)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for options in ({}, {"crossing_zy_contexts_path": None},
                        {"crossing_zy_contexts_path": "private-zy"}):
            with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                              return_value="receipt") as operation:
                self.assertEqual(method(session, "doc", "XO-001", "catalogue",
                                        **options), "receipt")
            self.assertEqual(operation.call_args.kwargs,
                             options if options.get("crossing_zy_contexts_path")
                             else {})

    def test_supplement_requires_existing_stack_before_source_access(self):
        for options in ({}, {"include_single_rail": False},
                        {"include_single_rail": True}):
            with self.subTest(options=options), patch.object(
                binding, "_open_source_context",
            ) as opened:
                create = Mock()
                with self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        crossing_zy_contexts_path="private-zy", **options,
                    )
                opened.assert_not_called()
                create.assert_not_called()


def reader_fixture(root, defect=None):
    """Write synthetic bookkeeping; no stored bytes represent geometry."""
    def store(name, value):
        path = root / name
        content = (value if isinstance(value, bytes) else
                   json.dumps(value, sort_keys=True).encode())
        path.write_bytes(content)
        return {"path": str(path),
                "sha256": hashlib.sha256(content).hexdigest()}

    document = synthetic_document()
    objects = document.find("Objects")
    details = document.find("ObjectData")
    obj, detail = copy.deepcopy(objects[0]), copy.deepcopy(details[0])
    objects.clear()
    details.clear()
    members = []
    names = tuple(f"TestPart{i:02d}" for i in range(33))
    for name in names:
        first, second = copy.deepcopy(obj), copy.deepcopy(detail)
        first.set("name", name)
        second.set("name", name)
        second.find(".//Part").set("file", name + ".Shape.brp")
        objects.append(first)
        details.append(second)
        members.append((name + ".Shape.brp", b"SYNTHETIC NO GEOMETRY"))
    model = synthetic_archive(members=[("Document.xml", ET.tostring(document)),
                                       *members])
    contexts = {}
    for index, selection in enumerate(zy_source()[5]):
        context = selection.run
        recipe = copy.deepcopy(selection.context)
        recipe["sample_kind"] = "fixture_timber_" + context[3:]
        recipe["native_frame"].update(
            hand_i=-1, native_from_source=[[-1, 0, 0, 0],
                                          [0, -1, 0, -0.45],
                                          [0, 0, 1, 149 / 60],
                                          [0, 0, 0, 1]],
        )
        if defect == "recipe" and index == 0:
            recipe["context"]["rail_code"] = 2
        if defect == "family" and index == 0:
            recipe["family"] = "XA"
        model_record = store(context + ".FCStd", model)
        result = store(context + "-result.json", {
            "ZY": {"status": "PASS", "native_reload": "PASS"},
        })
        recipe_binding = store(context + "-recipe.json", [recipe])
        execution = store(context + "-execution.json", {
            "status": "PASS", "context_id": context,
            "model_hashes": {"ZY": model_record["sha256"]},
            "result_sha256": result["sha256"],
            "source_recipe_binding": recipe_binding,
            "native_reload": "PASS", "fixing_proof": "PASS",
        })
        contexts[context] = {
            "status": "PASS", "native_reload": "PASS", "fixing_proof": "PASS",
            "family": "ZY", "context_id": context, "timber_id": context[3:],
            "chair_code": 21, "source_station_mm": recipe["station_mm"],
            "source_recipe": recipe, "model": model_record,
            "receipt": result, "result_receipt": result,
            "execution_receipt": execution,
            "components": [{"name": n} for n in names], "component_count": 33,
        }
        if defect == "component-order" and index == 0:
            contexts[context]["components"].reverse()
        if defect == "component-count" and index == 0:
            contexts[context]["component_count"] = 32
        if defect == "model-hash" and index == 0:
            contexts[context]["model"] = dict(model_record, sha256="0" * 64)
    all_ids = (*CONTEXTS, "RH-X3-X", "RH-X4-A", "RH-X5-B", "RH-X6-C",
               "RH-X7-D", "RH-X8-E")
    for context in all_ids[2:]:
        contexts[context] = {"status": "PASS"}
    qualification = {
        "status": "PASS", "contexts": contexts, "documents_closed": True,
        "production_accepted": False, "physical_fit": "NOT_PROVED",
        "qualified_runtime": "synthetic", "freecad_version": [1, 1, 4],
        "occt_version": "synthetic", "python_version": "synthetic",
    }
    if defect == "qualification":
        qualification["documents_closed"] = False
    hosts = {"hosts": {"A": {"synthetic": True}, "B": {"synthetic": True}}}
    manifest = {
        "schema_version": 1,
        "contract_id": "tracktemplate.private-crossing-catalogue.v1",
        "physical_fit": "NOT_PROVED",
        "project_status": "reference-only", "intended_uses": ["private-development"],
        "production_accepted": False, "rights_cleared": False,
        "inventory_root": str(root), "context_ids": all_ids,
        "context_count": 8, "source_position_count": 40,
        "qualification": store("qualification.json", qualification),
        "source_oracle": store("oracle.json", {"status": "PASS",
                                               "context_count": 8,
                                               "position_count": 40}),
        "canonical_hosts": store("hosts.json", hosts),
        "host_context_sha256": hashlib.sha256(json.dumps(
            hosts["hosts"], sort_keys=True, allow_nan=False,
        ).encode()).hexdigest(),
        "source_context_sha256": "f" * 64,
        "native_process": store("process.json", {
            "status": "PASS", "returncode": 0,
            "sentinel": "CROSSING_CONTEXT_NATIVE_PASS", "sentinel_present": True,
        }),
    }
    for key in ("normalisation_qualification", "original_normalisation_failure",
                "source_generation", "test_first_red"):
        manifest[key] = store(key + ".json", {"synthetic": key})
    if defect == "rights":
        manifest["rights_cleared"] = True
    if defect == "root":
        manifest["inventory_root"] = str(root / "outside")
    manifest_record = store("catalogue.json", manifest)
    return Path(manifest_record["path"]), manifest_record["sha256"]


class ZYReaderTests(unittest.TestCase):
    def test_synthetic_complete_reader_and_late_bound_change(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_zy_catalogue",
        )
        with tempfile.TemporaryDirectory(prefix="zy-reader-") as temporary:
            root = Path(temporary).resolve()
            path, digest = reader_fixture(root)
            with patch.object(catalogue, "ZY_CATALOGUE_SHA256", digest):
                selections = catalogue.prepare_zy_catalogue(path)
                self.assertEqual(tuple(s.run for s in selections), CONTEXTS)
                self.assertEqual(tuple(len(s.components) for s in selections),
                                 (33, 33))
                self.assertTrue(all(s.label == "ZY" for s in selections))
                catalogue.verify_zy_catalogue(selections)
                for invalid in (selections[::-1], selections[:1],
                                selections + selections[:1]):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.verify_zy_catalogue(invalid)
                (root / "RH-X2-Y-recipe.json").write_text("{}", encoding="utf-8")
                with self.assertRaises(CatalogueChairError):
                    catalogue.verify_zy_catalogue(selections)

    def test_rehashed_synthetic_semantic_and_binding_defects_are_rejected(self):
        catalogue = importlib.import_module(
            "tracktemplate.application.chair_crossing_zy_catalogue",
        )
        for defect in ("qualification", "recipe", "family", "component-order",
                       "component-count", "model-hash", "rights", "root"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory(
                prefix="zy-reader-negative-",
            ) as temporary:
                path, digest = reader_fixture(Path(temporary).resolve(), defect)
                with patch.object(catalogue, "ZY_CATALOGUE_SHA256", digest):
                    with self.assertRaises(CatalogueChairError):
                        catalogue.prepare_zy_catalogue(path)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: four ZY placements and eight canonical crossing records")
