"""Validate fixed assessment adaptation and fail-closed file handling."""

import ast
import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import prepare_runtime_assessment as preparation  # noqa: E402
from tracktemplate.bootstrap import evaluate_runtime  # noqa: E402


class AssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.modes = preparation._frozen_source(ROOT)

    def test_public_capsule_is_exact_and_omits_private_paths(self):
        capsule = preparation._public_capsule(
            ROOT / "tests/fixtures/runtime-assessment-inputs.json",
        )
        self.assertEqual(len(capsule), preparation.PUBLIC_CAPSULE_BYTES)
        for private in (b"/home/", b"/root/", b"/Users/", b"credentials"):
            self.assertNotIn(private, capsule)
        contents = json.loads(capsule)
        for kind, count in (("native_entries", 57), ("gui_entries", 22)):
            self.assertEqual(len(contents["matrix"][kind]), count)
            for row in contents["matrix"][kind]:
                self.assertEqual(set(row), {"path", "bytes", "sha256"})
                self.assertEqual(
                    preparation._identity(self.original[row["path"]]),
                    {key: row[key] for key in ("bytes", "sha256")},
                )

    def test_default_rejects_candidate_and_exact_assessment_checks_components(self):
        capsule = json.loads(preparation._public_capsule(
            ROOT / "tests/fixtures/runtime-assessment-inputs.json",
        ))
        candidate = json.loads(capsule["assessment_contract_utf8"])
        canonical = json.loads(self.original[preparation.CANONICAL_PATH])
        profile, = candidate["runtime_baseline"]["qualified_profiles"]
        record = {"freecad": {"available": True}}
        for dotted, value in profile["exact_match"].items():
            section, name = dotted.split(".")
            record.setdefault(section, {})[name] = value
        self.assertEqual(evaluate_runtime(record, canonical)["status"],
                         "unqualified")
        self.assertEqual(evaluate_runtime(record, candidate)["matched_profile_id"],
                         preparation.CANDIDATE_PROFILE)
        for dotted in profile["exact_match"]:
            altered = copy.deepcopy(record)
            section, name = dotted.split(".")
            altered[section][name] = "wrong-component"
            self.assertEqual(evaluate_runtime(altered, candidate)["status"],
                             "unqualified", dotted)
        candidate.pop("assessment_boundary")
        candidate["runtime_baseline"]["qualified_profiles"] = canonical[
            "runtime_baseline"
        ]["qualified_profiles"]
        self.assertEqual(candidate, canonical)

    def test_unapproved_base_stops_before_destination_creation(self):
        capsule = preparation._public_capsule(
            ROOT / "tests/fixtures/runtime-assessment-inputs.json",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            fixture = root / "wrong.FCStd"
            fixture.write_bytes(b"unapproved input")
            target = root / "new-tree"
            with mock.patch.object(preparation, "_public_capsule",
                                   return_value=capsule):
                with self.assertRaisesRegex(ValueError, "approved exact input"):
                    preparation.prepare_assessment(ROOT, root, fixture, target)
            self.assertFalse(target.exists())

    def test_only_declared_bindings_change(self):
        candidate = b'{"assessment": "test-only"}\n'
        adapted = preparation._adapt_source(
            self.original, {"assessment_contract_utf8": candidate.decode()},
        )
        expected = {row[0] for row in preparation.PROFILE_ADAPTATIONS}
        expected.update((
            preparation.CANONICAL_PATH,
            "reference/contracts/phase1-crossover-feasibility.json",
            "tools/freecad_bridge/run_phase8_crossover_preflight_gui.py",
        ))
        changed = {name for name in self.original
                   if self.original[name] != adapted[name]}
        self.assertEqual(changed, expected)
        self.assertEqual(len(changed), 56)
        for name, _, old in preparation.PROFILE_ADAPTATIONS:
            restored = adapted[name].replace(
                preparation.CANDIDATE_PROFILE.encode(), old.encode(),
            )
            self.assertEqual(restored, self.original[name], name)
            self.assertEqual(
                ast.dump(ast.parse(restored)),
                ast.dump(ast.parse(self.original[name])), name,
            )
        self.assertEqual(adapted[preparation.CANONICAL_PATH], candidate)
        for name in self.original:
            if (name.startswith("tracktemplate/")
                    or name.endswith(".FCMacro")):
                self.assertEqual(adapted[name], self.original[name], name)

    def test_crossover_semantics_and_negative_witnesses_unchanged(self):
        name = "reference/contracts/phase1-crossover-feasibility.json"
        adapted = preparation._adapt_source(
            self.original, {"assessment_contract_utf8": "test-only"},
        )
        before = json.loads(self.original[name])
        after = json.loads(adapted[name])
        self.assertEqual(after["fixture"]["object_count"], 9)
        self.assertEqual(after["fixture"]["semantic_sha256"], (
            "a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e"
        ))
        self.assertEqual(after["fixture"]["path"], preparation.BASE_PATH)
        self.assertEqual(after["fixture"]["sha256"], preparation.BASE_SHA256)
        after["fixture"]["path"] = before["fixture"]["path"]
        after["fixture"]["sha256"] = before["fixture"]["sha256"]
        self.assertEqual(after, before)

    def test_profile_source_drift_refused(self):
        original = dict(self.original)
        name = preparation.PROFILE_ADAPTATIONS[0][0]
        original[name] += b"\n# drift\n"
        with self.assertRaisesRegex(ValueError, "source drift"):
            preparation._adapt_source(
                original, {"assessment_contract_utf8": "test-only"},
            )

    def test_semantic_contract_drift_refused(self):
        original = dict(self.original)
        name = "reference/contracts/phase1-crossover-feasibility.json"
        original[name] = original[name].replace(
            b'"object_count": 9', b'"object_count": 8',
        )
        with self.assertRaisesRegex(ValueError, "source drift"):
            preparation._adapt_source(
                original, {"assessment_contract_utf8": "test-only"},
            )

    def test_source_fixture_is_never_modified(self):
        self.assertNotIn(preparation.BASE_PATH, self.original)
        self.assertEqual(preparation._sha256(
            preparation._read_regular(ROOT / preparation.CANONICAL_PATH)
        ), preparation.CANONICAL_SHA256)

    def test_invalid_public_capsule_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "capsule.json"
            path.write_text('{"schema_version": 1}\n')
            with self.assertRaisesRegex(ValueError, "capsule changed"):
                preparation._public_capsule(path)

    def test_linked_input_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "source"
            source.write_bytes(b"approved-looking input")
            link = root / "link"
            link.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "Symbolic links"):
                preparation._read_regular(link)
            directory = root / "directory-link"
            directory.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Symbolic links"):
                preparation._read_regular(directory / "source")

    def test_existing_and_linked_destination_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            with self.assertRaisesRegex(ValueError, "new directory"):
                preparation._new_destination(root, ROOT)
            link = root / "link"
            link.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                preparation._new_destination(link / "new", ROOT)

    def test_unsafe_member_paths_refused(self):
        for name in ("/absolute", "../escape", "x/../escape", "x\\escape"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                preparation._relative_name(name)

    def test_frozen_tree_rejects_missing_extra_changed_or_linked_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = b"public frozen source\n"
            base = b"synthetic test fixture\n"
            diff = b"finite test diff\n"
            manifest = {
                "source_files": [{
                    "path": "source.py",
                    "assessment": preparation._identity(source),
                    "mode": 0o644,
                }],
                "base_fixture": {
                    "path": "fixture.FCStd", **preparation._identity(base),
                },
                "adaptation_diff": preparation._identity(diff),
            }
            for name, data in (
                ("source.py", source), ("fixture.FCStd", base),
                ("_assessment/adaptations.diff", diff),
                ("_assessment/manifest.json", preparation._json_bytes(manifest)),
            ):
                preparation._write_new(root / name, data)
            self.assertEqual(
                preparation.verify_assessment(root, manifest)["status"], "PASS",
            )
            source_path = root / "source.py"
            source_path.write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError, "member changed"):
                preparation.verify_assessment(root, manifest)
            source_path.write_bytes(source)
            source_path.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "member changed"):
                preparation.verify_assessment(root, manifest)
            source_path.chmod(0o644)
            source_path.rename(root / "unexpected.py")
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                preparation.verify_assessment(root, manifest)
            (root / "unexpected.py").rename(source_path)
            missing = copy.deepcopy(manifest)
            missing["source_files"].append({
                "path": "absent.py", "assessment": preparation._identity(b""),
                "mode": 0o644,
            })
            (root / "_assessment/manifest.json").write_bytes(
                preparation._json_bytes(missing),
            )
            with self.assertRaisesRegex(ValueError, "member missing"):
                preparation.verify_assessment(root, missing)
            (root / "_assessment/manifest.json").write_bytes(
                preparation._json_bytes(manifest),
            )
            (root / "link").symlink_to(source_path)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                preparation.verify_assessment(root, manifest)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AssessmentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    print("Runtime assessment preparation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
