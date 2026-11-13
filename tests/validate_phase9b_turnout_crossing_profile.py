#!/usr/bin/env python3
"""Check the fixed TO crossing profile with synthetic metadata and ZIPs.

Only the already published numeric comparison fixture supplies source facts.
ZIP contents are artificial text, never geometry or native model evidence.
Synthetic digest/model substitutions exercise real parsing and qualification;
they do not admit synthetic inputs through the unpatched product boundary.
Source-informed comparisons remain reference-only; see NOTICE.md and
reference/PROVENANCE.md for GPL-3.0-or-later source obligations.
"""

from contextlib import contextmanager
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import chair_catalogue as catalogue  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_crossing_pair_catalogue as crossing,
)
from validate_phase9b_chair_catalogue import (  # noqa: E402
    synthetic_archive,
    synthetic_document,
)


SENTINEL = "Phase 9B turnout crossing profile validation passed"
PROFILE_SHA256 = (
    "801a2b43f623aa292b87762970fe3f249e4fb5b3a78d3f36bcf64eb435a3e70e"
)
FAMILIES = ("XA", "AA", "CD", "DD")
FIXTURE = ROOT / "tests/fixtures/phase9b-to-crossing-cohort-source-frames.json"
FRAME = (
    "chair-local model mm, X along main rail, rail-top Z=0; "
    "crossing origin at main crossing rail gauge face"
)
LOCAL_PLACE = (2.25, -4.5, 6.0, 0.0, 0.0, 0.6, 0.8)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")


def source_rows():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["positions"]


def model_bytes(family, names):
    """Preserve semantic names with invented labels, text and placements."""
    document = synthetic_document()
    prototype = copy.deepcopy(document.find("./ObjectData/Object"))
    objects = document.find("Objects")
    data = document.find("ObjectData")
    objects.clear()
    data.clear()
    members = []
    for index, name in enumerate(names):
        ET.SubElement(objects, "Object", type="Part::Feature", name=name)
        item = copy.deepcopy(prototype)
        item.set("name", name)
        item.find(".//Part").set("file", name + ".Shape.brp")
        item.find(".//String").set("value", family + ":" + name)
        item.find(".//PropertyPlacement").set("Px", str(2.25 + index))
        data.append(item)
        members.append((name + ".Shape.brp",
                        f"ARTIFICIAL {family} COMPONENT {index}".encode()))
    return synthetic_archive(members=[("Document.xml", ET.tostring(document)),
                                      *members])


def manifest_and_models():
    """Build invented transport evidence around frozen comparison facts."""
    families = []
    models = {}
    for row in source_rows():
        family = row["family"]
        model = row["model"]
        centres = [item["source_origin_mm"][:2]
                   for item in row["fixing_frames"]]
        models[family] = model_bytes(family, model["component_names"])
        digest = sha(models[family])
        recipe = {
            "family": family, "chair_code": model["source_code"],
            "context_sha256": model["context_sha256"],
            "sample_kind": model["sample_kind"],
            "station_mm": model["station_mm"],
            "base": {"bolt_centres_twisted_mm": copy.deepcopy(centres)},
        }
        native = {
            "family": family, "status": "PASS", "native_reload": "PASS",
            "scope": "private-development", "production_ready": False,
            "physical_fit": "NOT_PROVED", "fused_casting": "NOT_PROVED",
            "source_recipe": recipe,
            "fixing_proof": {
                "model_sha256": digest,
                "source_fixings": {
                    "head_rotation_degrees": 0,
                    "p_bolt_status": "NOT_APPLICABLE_SOURCE_DISPATCH",
                    "random_export_parity": False,
                    "placement": {
                        "basis": "recipe.base.bolt_centres_twisted_mm; "
                                 "used once",
                        "recipe_sha256": model["fixing_recipe_sha256"],
                        "centres_source_mm": copy.deepcopy(centres),
                        "source_twist_reapplied": False,
                    },
                },
            },
        }
        families.append({
            "label": family, "run": "context-native-02",
            "model": {"member": f"models/{family}.FCStd",
                      "bytes": len(models[family]), "sha256": digest},
            "context": {
                "context_id": None, "sample_id": None, "timber_id": None,
                "context_sha256": model["context_sha256"], "frame": FRAME,
                "sample_kind": model["sample_kind"],
                "station_mm": model["station_mm"],
            },
            "component_names": model["component_names"],
            "limitations": ["Synthetic reference-only parser evidence"],
            "metadata": {
                "acceptance": "NO_NEW_ACCEPTANCE",
                "intended_uses": ["private-development"],
                "native_record": native,
                "phase_acceptance": "UNCHANGED_PHASE_9B_3_OF_6",
                "production_geometry_authorized": False,
                "project_status": "reference-only",
                "reference_admission": "Private development; not accepted",
                "source_codes": [model["source_code"]],
                "source_explicit_nyi": ["Synthetic excluded source scope"],
                "source_inventory": "Synthetic inventory description",
            },
        })
    lineage = {
        "catalogue": {"bytes": 189151, "sha256": catalogue.CATALOGUE_SHA256},
        "execution_plan_sha256": "1" * 64,
        "execution_receipt": {"bytes": 3213, "sha256": "2" * 64},
        "recipe_file": {"bytes": 776816, "sha256": "3" * 64},
        "result_and_receipt": {"bytes": 2666045, "sha256": "4" * 64},
        "source_archive_sha256": "5" * 64,
        "source_inventory": {"bytes": 6820,
                             "sha256": catalogue.INVENTORY_SHA256},
        "source_members": {
            name: "6" * 64 for name in ("chairs_unit.pas", "dxf_unit.pas",
                                        "licence.txt", "math_unit.pas",
                                        "pad_unit.pas")
        },
    }
    manifest = {
        "schema_version": 1,
        "profile": "TO-001-XA-AA-CD-DD-fixed-reference-candidate-v1",
        "status": "LOCAL_CANDIDATE_NOT_ADMITTED",
        "authority": {
            "acceptance": "NO_NEW_ACCEPTANCE", "rights_cleared": False,
            "native_execution_authorized": False,
            "production_accepted": False, "public_transfer_authorized": False,
        },
        "scope": {"component_count": 135, "family_count": 4,
                  "family_order": list(FAMILIES), "source_position_count": 8},
        "families": families, "original_lineage": lineage,
        "historical_execution": {
            "status": "PASS", "execution_plan_sha256": "1" * 64,
            "result_sha256": "4" * 64,
            "model_hashes": {key: sha(value) for key, value in models.items()},
            "freecad_version": ["synthetic"] * 8,
            "occt_version": "synthetic", "python_version": "synthetic",
            "qualified_runtime": "opaque historical text; never evaluated",
        },
        "limitations": ["Synthetic parser evidence; no native qualification"],
    }
    return manifest, models


def put(record, path, value):
    for key in path[:-1]:
        record = record[key]
    record[path[-1]] = value


def dictionaries(value, path=()):
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from dictionaries(item, (*path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from dictionaries(item, (*path, index))


class ProfileTests(unittest.TestCase):
    """Exercise the real cohort facade without native code or model inputs."""

    def setUp(self):
        self.manifest, self.models = manifest_and_models()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        self.path = self.root / "four-family-manifest.json"
        (self.root / "models").mkdir()
        self.write()

    def write(self, raw=None):
        for family, data in self.models.items():
            (self.root / f"models/{family}.FCStd").write_bytes(data)
        self.path.write_bytes(encoded(self.manifest) if raw is None else raw)

    @contextmanager
    def synthetic_admission(self):
        """Substitute only code-owned profile/model digests in these tests."""
        bindings = tuple(
            (family, (*spec[:3], sha(self.models[family]), *spec[4:]))
            for family, spec in crossing._TO_CROSSING_BINDINGS
        )
        with patch.object(crossing, "TO_CROSSING_PROFILE_SHA256",
                          sha(self.path.read_bytes())), patch.object(
                              crossing, "_TO_CROSSING_BINDINGS", bindings):
            yield

    def prepare(self):
        return crossing.prepare_turnout_crossing_catalogue(str(self.path))

    def reject(self):
        with self.synthetic_admission():
            with self.assertRaises(catalogue.CatalogueChairError):
                self.prepare()

    def replace_model(self, family, data):
        self.models[family] = data
        entry = self.manifest["families"][FAMILIES.index(family)]
        entry["model"].update(bytes=len(data), sha256=sha(data))
        entry["metadata"]["native_record"]["fixing_proof"][
            "model_sha256"] = sha(data)
        self.manifest["historical_execution"]["model_hashes"][family] = sha(data)
        self.write()

    def test_fixed_identity_and_no_caller_trust_override(self):
        self.assertEqual(crossing.TO_CROSSING_PROFILE_SHA256, PROFILE_SHA256)
        self.assertNotEqual(PROFILE_SHA256, catalogue.CATALOGUE_SHA256)
        with (
            patch.object(catalogue.zipfile, "ZipFile",
                         side_effect=AssertionError("untrusted archive")),
            patch.object(catalogue.json, "loads",
                         side_effect=AssertionError("untrusted JSON")),
        ):
            with self.assertRaises(catalogue.CatalogueChairError):
                self.prepare()
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue.prepare_catalogue_chair(str(self.path), "XA")
        with self.assertRaises(TypeError):
            crossing.prepare_turnout_crossing_catalogue(
                str(self.path), expected_sha256=sha(self.path.read_bytes()),
            )
        with self.synthetic_admission():
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue.prepare_catalogue_chair(str(self.path), "XA")

    def test_complete_ordered_selections_and_detached_metadata(self):
        with self.synthetic_admission():
            prepared = self.prepare()
            crossing.verify_turnout_crossing_catalogue(prepared)
        self.assertIsInstance(prepared, tuple)
        self.assertEqual(tuple(item.label for item in prepared), FAMILIES)
        self.assertEqual(tuple(len(item.components) for item in prepared),
                         (33, 42, 27, 33))
        for selection, entry in zip(prepared, self.manifest["families"]):
            with self.subTest(family=selection.label):
                self.assertEqual(selection.catalogue_path, str(self.path))
                self.assertEqual(selection.catalogue_sha256,
                                 sha(self.path.read_bytes()))
                self.assertNotEqual(selection.catalogue_sha256,
                                    catalogue.CATALOGUE_SHA256)
                self.assertEqual(selection.run, entry["run"])
                self.assertEqual(selection.context, entry["context"])
                self.assertEqual(selection.metadata, entry["metadata"])
                self.assertEqual(selection.limitations,
                                 tuple(entry["limitations"]))
                self.assertEqual(selection.model_path,
                                 str(self.root / entry["model"]["member"]))
                self.assertEqual(selection.model_sha256,
                                 entry["model"]["sha256"])
                self.assertEqual(tuple(c.name for c in selection.components),
                                 tuple(entry["component_names"]))
                for index, component in enumerate(selection.components):
                    self.assertEqual(component.label,
                                     selection.label + ":" + component.name)
                    self.assertEqual(component.brep_text,
                                     f"ARTIFICIAL {selection.label} "
                                     f"COMPONENT {index}")
                    self.assertEqual(component.xml_placement,
                                     (2.25 + index, *LOCAL_PLACE[1:]))
                bindings = {item.path: item.sha256
                            for item in selection.bindings}
                self.assertIn(str(self.path), bindings)
                self.assertIn(selection.model_path, bindings)
                self.assertEqual(len(bindings), len(selection.bindings))
                for path, digest in bindings.items():
                    self.assertIn(Path(path), {self.path, *(
                        self.root / f"models/{family}.FCStd"
                        for family in FAMILIES)})
                    self.assertEqual(sha(Path(path).read_bytes()), digest)
                detached = selection.metadata
                detached["native_record"]["status"] = "CHANGED"
                self.assertEqual(selection.metadata, entry["metadata"])

    def test_missing_extra_and_wrong_object_shapes(self):
        baseline = copy.deepcopy(self.manifest)
        for path, value in dictionaries(baseline):
            for mutation in ("missing", "extra", "wrong_type"):
                with self.subTest(path=path, mutation=mutation):
                    changed = copy.deepcopy(value)
                    if mutation == "missing":
                        del changed[next(iter(changed))]
                    elif mutation == "extra":
                        changed["unexpected"] = "not admitted"
                    else:
                        changed = []
                    self.manifest = copy.deepcopy(baseline)
                    if path:
                        put(self.manifest, path, changed)
                    else:
                        self.manifest = changed
                    self.write()
                    self.reject()

    def test_family_run_order_and_scope_are_exact(self):
        baseline = copy.deepcopy(self.manifest)
        cases = (
            (("schema_version",), True), (("schema_version",), 2),
            (("profile",), "other"), (("status",), "ACCEPTED"),
            (("scope", "family_count"), 4.0),
            (("scope", "component_count"), 136),
            (("scope", "source_position_count"), 9),
            (("scope", "family_order"), list(reversed(FAMILIES))),
            (("families",), baseline["families"][:-1]),
            (("families",), list(reversed(baseline["families"]))),
            (("families",), [baseline["families"][0]] * 4),
            (("families",), baseline["families"] + [baseline["families"][0]]),
        )
        for path, value in cases:
            with self.subTest(path=path, value=value):
                self.manifest = copy.deepcopy(baseline)
                put(self.manifest, path, value)
                self.write()
                self.reject()
        for index in range(4):
            for field, value in (("label", "BB"), ("run", "basic-04")):
                with self.subTest(index=index, field=field):
                    self.manifest = copy.deepcopy(baseline)
                    self.manifest["families"][index][field] = value
                    self.write()
                    self.reject()

    def test_every_native_qualification_predicate_is_live(self):
        baseline = copy.deepcopy(self.manifest)
        recipe = ("source_recipe",)
        fixing = ("fixing_proof",)
        source = (*fixing, "source_fixings")
        placement = (*source, "placement")
        cases = (
            (("family",), "BB"), (("status",), "FAIL"),
            (("native_reload",), "FAIL"), (("scope",), "production"),
            (("production_ready",), 0),
            ((*recipe, "family"), "BB"),
            ((*recipe, "context_sha256"), "0" * 64),
            ((*recipe, "sample_kind"), "other"),
            ((*recipe, "station_mm"), True),
            ((*recipe, "station_mm"), 123.0),
            ((*recipe, "chair_code"), True),
            ((*recipe, "chair_code"), 23.0),
            ((*recipe, "chair_code"), 999),
            ((*recipe, "base", "bolt_centres_twisted_mm"), [[0, 0]] * 4),
            ((*fixing, "model_sha256"), "0" * 64),
            ((*placement, "recipe_sha256"), "0" * 64),
            ((*placement, "centres_source_mm"), [[0, 0]] * 4),
            ((*placement, "basis"), "twisted twice"),
            ((*placement, "source_twist_reapplied"), 0),
            ((*source, "head_rotation_degrees"), False),
            ((*source, "head_rotation_degrees"), 1),
            ((*source, "random_export_parity"), 0),
            ((*source, "p_bolt_status"), "PASS"),
        )
        for index in range(4):
            for path, value in cases:
                with self.subTest(family=FAMILIES[index], path=path, value=value):
                    self.manifest = copy.deepcopy(baseline)
                    native = self.manifest["families"][index]["metadata"][
                        "native_record"]
                    put(native, path, value)
                    self.write()
                    self.reject()

    def test_context_metadata_component_names_and_centres(self):
        baseline = copy.deepcopy(self.manifest)
        cases = (
            (("context", "context_sha256"), "0" * 64),
            (("context", "sample_kind"), "other"),
            (("context", "station_mm"), True),
            (("context", "station_mm"), 123.0),
            (("context", "frame"), "world"),
            (("context", "context_id"), "invented"),
            (("context", "sample_id"), "invented"),
            (("context", "timber_id"), "invented"),
            (("metadata", "acceptance"), "ACCEPTED"),
            (("metadata", "project_status"), "project-cleared"),
            (("metadata", "intended_uses"), ["production"]),
            (("metadata", "production_geometry_authorized"), 0),
            (("metadata", "phase_acceptance"), "ACCEPTED"),
            (("metadata", "source_codes"), [True]),
            (("metadata", "native_record", "physical_fit"), "PASS"),
            (("metadata", "native_record", "fused_casting"), "PASS"),
        )
        for index in range(4):
            for path, value in cases:
                with self.subTest(family=FAMILIES[index], path=path):
                    self.manifest = copy.deepcopy(baseline)
                    put(self.manifest["families"][index], path, value)
                    self.write()
                    self.reject()
            for field in ("component_names", "centres"):
                with self.subTest(family=FAMILIES[index], field=field):
                    self.manifest = copy.deepcopy(baseline)
                    entry = self.manifest["families"][index]
                    if field == "component_names":
                        entry[field].reverse()
                    else:
                        entry["metadata"]["native_record"]["source_recipe"][
                            "base"]["bolt_centres_twisted_mm"].reverse()
                    self.write()
                    self.reject()

    def test_authority_flags_and_historical_runtime(self):
        baseline = copy.deepcopy(self.manifest)
        for field in baseline["authority"]:
            for value in (True, 0, None):
                with self.subTest(field=field, value=value):
                    self.manifest = copy.deepcopy(baseline)
                    self.manifest["authority"][field] = value
                    self.write()
                    self.reject()
        for field in ("qualified_runtime", "freecad_version", "occt_version",
                      "python_version", "status"):
            for value in ("", None, False, {}):
                with self.subTest(field=field, value=value):
                    self.manifest = copy.deepcopy(baseline)
                    self.manifest["historical_execution"][field] = value
                    self.write()
                    self.reject()
        self.manifest = copy.deepcopy(baseline)
        self.manifest["historical_execution"]["qualified_runtime"] = (
            "__import__('builtins').eval('must never execute')"
        )
        self.write()
        with self.synthetic_admission(), patch(
            "builtins.eval", side_effect=AssertionError("runtime evaluated"),
        ):
            self.assertEqual(len(self.prepare()), 4)

    def test_original_lineage_and_execution_cross_bindings(self):
        baseline = copy.deepcopy(self.manifest)
        cases = (
            (("original_lineage", "catalogue", "sha256"), PROFILE_SHA256),
            (("original_lineage", "source_inventory", "sha256"), "0" * 64),
            (("original_lineage", "execution_receipt", "bytes"), True),
            (("original_lineage", "recipe_file", "sha256"), "not-a-hash"),
            (("historical_execution", "execution_plan_sha256"), "0" * 64),
            (("historical_execution", "result_sha256"), "0" * 64),
            (("historical_execution", "status"), "FAIL"),
            (("historical_execution", "model_hashes", "XA"), "0" * 64),
        )
        for path, value in cases:
            with self.subTest(path=path):
                self.manifest = copy.deepcopy(baseline)
                put(self.manifest, path, value)
                self.write()
                self.reject()

    def test_duplicate_json_and_all_nonfinite_spellings(self):
        raw = encoded(self.manifest)
        duplicates = (
            raw.replace(b'"schema_version": 1',
                        b'"schema_version": 1, "schema_version": 1', 1),
            raw.replace(b'"native_reload": "PASS"',
                        b'"native_reload": "PASS", "native_reload": "PASS"',
                        1),
        )
        for data in duplicates:
            with self.subTest(kind="duplicate"):
                self.write(data)
                self.reject()
        station = repr(self.manifest["families"][0]["context"]["station_mm"])
        for token in (b"NaN", b"Infinity", b"-Infinity", b"1e999", b"-1e999"):
            with self.subTest(token=token):
                self.write(raw.replace(station.encode(), token, 1))
                self.reject()

    def test_member_spelling_is_checked_before_normalisation(self):
        baseline = copy.deepcopy(self.manifest)
        for member in ("/models/XA.FCStd", "../models/XA.FCStd",
                       "models/../models/XA.FCStd", "models//XA.FCStd",
                       "./models/XA.FCStd", "models\\XA.FCStd",
                       "models/AA.FCStd", "models/xa.FCStd", "models/Other",
                       "models/XA.FCStd/", "models/XA.FCStd\x00"):
            with self.subTest(member=member):
                self.manifest = copy.deepcopy(baseline)
                self.manifest["families"][0]["model"]["member"] = member
                self.write()
                self.reject()

    def test_missing_symlink_nonregular_and_oversize_files(self):
        target = self.root / "models/XA.FCStd"
        held = self.root / "held-model"
        target.rename(held)
        self.reject()
        target.symlink_to(held)
        self.reject()
        target.unlink()
        target.mkdir()
        self.reject()
        target.rmdir()
        held.rename(target)
        original_model = self.models["XA"]
        self.replace_model("XA", b"x" * (catalogue._FILE_LIMIT + 1))
        self.reject()
        self.replace_model("XA", original_model)
        directory = self.root / "models"
        moved_directory = self.root / "held-models"
        directory.rename(moved_directory)
        directory.symlink_to(moved_directory, target_is_directory=True)
        self.reject()
        directory.unlink()
        moved_directory.rename(directory)
        alias = self.root / "manifest-alias.json"
        alias.symlink_to(self.path)
        with self.synthetic_admission():
            with self.assertRaises(catalogue.CatalogueChairError):
                crossing.prepare_turnout_crossing_catalogue(str(alias))
            with self.assertRaises(catalogue.CatalogueChairError):
                crossing.prepare_turnout_crossing_catalogue(
                    str(self.root / "models/../four-family-manifest.json"),
                )
        self.path.write_bytes(b" " * (catalogue._FILE_LIMIT + 1))
        self.reject()

    def test_model_byte_count_and_digest_precede_archive_parsing(self):
        baseline = copy.deepcopy(self.manifest)
        for field, value in (("bytes", True), ("bytes", 0),
                             ("bytes", len(self.models["XA"]) + 1),
                             ("sha256", "0" * 64)):
            with self.subTest(field=field, value=value):
                self.manifest = copy.deepcopy(baseline)
                self.manifest["families"][0]["model"][field] = value
                self.write()
                with patch.object(catalogue.zipfile, "ZipFile",
                                  side_effect=AssertionError("unsafe parse")):
                    self.reject()
        self.manifest = copy.deepcopy(baseline)
        self.write()
        data = self.models["XA"]
        (self.root / "models/XA.FCStd").write_bytes(
            bytes([data[0] ^ 1]) + data[1:],
        )
        with patch.object(catalogue.zipfile, "ZipFile",
                          side_effect=AssertionError("unsafe parse")):
            self.reject()

    def test_real_archive_parser_and_component_order_remain_active(self):
        names = self.manifest["families"][0]["component_names"]
        document = synthetic_document()
        bad = (
            synthetic_archive(xml=b"<!DOCTYPE Document []><Document/>"),
            synthetic_archive(members=[("../escape", b"x")]),
            synthetic_archive(members=[("Document.xml", b"x")] * 2),
            synthetic_archive(members=[(f"extra{i}", b"x")
                                       for i in range(129)]),
            synthetic_archive(members=[
                ("Document.xml", ET.tostring(document)),
                ("Sample.Shape.brp", b"x" * (catalogue._ARCHIVE_LIMIT + 1)),
            ]),
            model_bytes("XA", list(reversed(names))),
            model_bytes("XA", names[:-1]),
        )
        for index, data in enumerate(bad):
            with self.subTest(index=index):
                self.replace_model("XA", data)
                self.reject()

    def test_late_manifest_and_each_model_change_are_refused(self):
        with self.synthetic_admission():
            prepared = self.prepare()
            original = self.path.read_bytes()
            self.path.write_bytes(original + b" ")
            with self.assertRaises(catalogue.CatalogueChairError):
                crossing.verify_turnout_crossing_catalogue(prepared)
            self.path.write_bytes(original)
            for family in FAMILIES:
                with self.subTest(family=family):
                    path = self.root / f"models/{family}.FCStd"
                    path.write_bytes(self.models[family] + b"changed")
                    with self.assertRaises(catalogue.CatalogueChairError):
                        crossing.verify_turnout_crossing_catalogue(prepared)
                    path.write_bytes(self.models[family])
            crossing.verify_turnout_crossing_catalogue(prepared)

    def test_late_whole_selection_and_each_component_field(self):
        with self.synthetic_admission():
            prepared = self.prepare()
            for index, selection in enumerate(prepared):
                changes = (
                    {"catalogue_sha256": catalogue.CATALOGUE_SHA256},
                    {"context_json": selection.context_json + " "},
                    {"metadata_json": selection.metadata_json + " "},
                    {"limitations": (*selection.limitations, "changed")},
                    {"bindings": selection.bindings[:-1]},
                    {"model_path": selection.model_path + ".other"},
                    {"run": "other"},
                )
                for change in changes:
                    with self.subTest(family=selection.label, change=change):
                        altered = list(prepared)
                        altered[index] = replace(selection, **change)
                        with self.assertRaises(catalogue.CatalogueChairError):
                            crossing.verify_turnout_crossing_catalogue(
                                tuple(altered),
                            )
                for field, value in (("name", "changed"),
                                     ("label", "changed"),
                                     ("brep_text", "changed"),
                                     ("xml_placement", (0,) * 7)):
                    with self.subTest(family=selection.label, field=field):
                        components = list(selection.components)
                        components[-1] = replace(components[-1],
                                                 **{field: value})
                        altered = list(prepared)
                        altered[index] = replace(selection,
                                                 components=tuple(components))
                        with self.assertRaises(catalogue.CatalogueChairError):
                            crossing.verify_turnout_crossing_catalogue(
                                tuple(altered),
                            )
            for altered in (list(prepared), prepared[:-1],
                            tuple(reversed(prepared)), (prepared[0],) * 4):
                with self.subTest(kind=type(altered), count=len(altered)):
                    with self.assertRaises(catalogue.CatalogueChairError):
                        crossing.verify_turnout_crossing_catalogue(altered)

    def test_original_reader_and_rh_routes_keep_their_contracts(self):
        from validate_phase9b_turnout_crossing_chairs import selection

        old_bytes = b"Synthetic old-profile dispatch witness"
        self.path.write_bytes(old_bytes)
        old_digest = sha(old_bytes)
        original = tuple(replace(selection(family),
                                 catalogue_path=str(self.path),
                                 catalogue_sha256=old_digest)
                         for family in FAMILIES)
        # This isolated old-reader delegation test permits strict dispatch.
        # Actual old catalogue byte parity remains a separate local proof.
        with (
            patch.object(crossing, "CATALOGUE_SHA256", old_digest),
            patch.object(crossing, "prepare_catalogue_chair",
                         side_effect=lambda path, family, run:
                         original[FAMILIES.index(family)]) as reader,
        ):
            result = crossing.prepare_turnout_crossing_catalogue(str(self.path))
            self.assertEqual(result, original)
            self.assertEqual([call.args[1] for call in reader.call_args_list],
                             list(FAMILIES))
            self.assertTrue(all(call.kwargs == {"run": "context-native-02"}
                                for call in reader.call_args_list))
            crossing.verify_turnout_crossing_catalogue(result)
        for prepare, verify, specifications, ids in (
            (crossing.prepare_crossing_pair_catalogue,
             crossing.verify_crossing_pair_catalogue,
             crossing._SPECIFICATIONS, crossing.CROSSING_PAIR_CONTEXT_IDS),
            (crossing.prepare_crossing_split_catalogue,
             crossing.verify_crossing_split_catalogue,
             crossing._SPLIT_SPECIFICATIONS, crossing.CROSSING_SPLIT_CONTEXT_IDS),
        ):
            expected = tuple(replace(original[0], run=value) for value in ids)
            with patch.object(crossing, "_prepare_contexts",
                              return_value=expected) as reader:
                self.assertEqual(prepare("original-rh"), expected)
                self.assertEqual(reader.call_args.args[:3],
                                 ("original-rh",
                                  crossing.CROSSING_PAIR_CATALOGUE_SHA256,
                                  specifications))
                verify(expected)


def main():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if result.wasSuccessful():
        print(SENTINEL)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
