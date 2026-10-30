"""Offline contracts for the import-safe L1 hosted test entry.

These checks use harmless records and shape doubles. They do not qualify
FreeCAD, geometry, hosted readiness, resource containment or cleanup.
"""

import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "tests/hosted_l1_current_source_suite.py"


def load_entry():
    spec = importlib.util.spec_from_file_location("l1_entry_contract", ENTRY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_data(entry):
    frame = {"origin_mm": [0.0, 0.0, 0.8], "x_axis": [1.0, 0.0],
             "y_axis": [0.0, 1.0]}
    values = {}
    for identity, rail_id, timber_id in entry.identities():
        values[identity] = {
            "family": "L1", "rail_id": rail_id, "timber_id": timber_id,
            "body": copy.deepcopy(frame),
            "fixing_frames": [copy.deepcopy(frame) for _ in range(4)],
        }
    return {label: copy.deepcopy(values) for label, _radius, _count
            in entry.CASES}


class HostedL1Contracts(unittest.TestCase):
    def setUp(self):
        self.entry = load_entry()

    def test_import_has_no_host_file_or_process_side_effects(self):
        with (patch("builtins.open", side_effect=AssertionError("open")),
              patch.object(Path, "open", side_effect=AssertionError("open")),
              patch("subprocess.Popen", side_effect=AssertionError("process"))):
            module = load_entry()
        self.assertEqual(len(unittest.defaultTestLoader.getTestCaseNames(
            module.L1CurrentSource)), 2)
        tree = ast.parse(ENTRY.read_text())
        imports = [node for node in tree.body
                   if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("FreeCAD" in ast.unparse(node)
                             for node in imports))

    def test_expected_input_contract_and_exact_counts(self):
        data = expected_data(self.entry)
        self.assertEqual(self.entry.validate_expectations(data), 150)
        self.assertEqual(len(self.entry.COMPONENT_NAMES), 23)
        self.assertEqual(len(self.entry.REPRESENTATIVES), 2)
        self.assertEqual(len(self.entry.INPUT_IDS), 10)

    def test_expected_contract_rejects_missing_extra_and_nonfinite(self):
        data = expected_data(self.entry)
        label = self.entry.CASES[0][0]
        identity = self.entry.identities()[0][0]
        mutations = []
        missing = copy.deepcopy(data)
        del missing[label][identity]
        mutations.append(missing)
        extra = copy.deepcopy(data)
        extra[label]["unsupported"] = extra[label][identity]
        mutations.append(extra)
        for field in ("origin_mm", "x_axis", "y_axis"):
            bad = copy.deepcopy(data)
            bad[label][identity]["body"][field][0] = float("nan")
            mutations.append(bad)
        bad = copy.deepcopy(data)
        bad[label][identity]["fixing_frames"].pop()
        mutations.append(bad)
        bad = copy.deepcopy(data)
        bad[label][identity]["rail_id"] = "substitution"
        mutations.append(bad)
        bad = copy.deepcopy(data)
        del bad[label][identity]["body"]["origin_mm"]
        mutations.append(bad)
        for value in mutations:
            with self.subTest(value=repr(value)[:60]):
                with self.assertRaises((AssertionError, ValueError, KeyError)):
                    self.entry.validate_expectations(value)

    def test_frame_comparison_uses_existing_arithmetic_budget(self):
        frame = {"origin_mm": [1.0, 2.0, 0.8], "x_axis": [1.0, 0.0],
                 "y_axis": [0.0, 1.0]}
        self.entry.compare_frame(SimpleNamespace(**frame), frame)
        for field in frame:
            bad = copy.deepcopy(frame)
            bad[field][0] += 1.0
            with self.assertRaises(AssertionError):
                self.entry.compare_frame(SimpleNamespace(**bad), frame)

    def test_original_complete_comparator_reused_with_negative_controls(self):
        helpers = self.entry.load_comparator(ROOT)
        self.assertEqual(self.entry.comparator_controls(helpers), 8)
        self.assertEqual(helpers["EPSILON_MM"], 1.0e-7)

    def test_helper_hash_change_fails_closed(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "tests").mkdir()
            for key, (relative, _digest) in self.entry.HELPERS.items():
                path = root / relative
                path.write_text("def altered(*args): return True\n")
                with self.subTest(key=key):
                    with self.assertRaisesRegex(AssertionError, "hash"):
                        self.entry.extract_helper(root, key, ("altered",))

    def test_native_helper_is_extracted_before_native_journey(self):
        helper = self.entry.load_generate(ROOT, SimpleNamespace())
        self.assertTrue(callable(helper))
        tree = ast.parse(ENTRY.read_text())
        execute = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef)
                       and node.name == "_execute")
        calls = [(node.lineno, ast.unparse(node.func))
                 for node in ast.walk(execute) if isinstance(node, ast.Call)]
        setup_line = next(line for line, name in calls if name == "native_setup")
        journey_line = next(line for line, name in calls if name == "self._journey")
        self.assertLess(setup_line, journey_line)

    def test_regular_path_and_content_binding(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = root / "input.json"
            path.write_text("{}")
            digest = self.entry.sha256(path)
            self.assertEqual(self.entry.bound_file({
                "path": str(path), "sha256": digest, "bytes": 2,
            }), path)
            for changes in ({"sha256": "0" * 64}, {"bytes": 3}):
                with self.assertRaises(AssertionError):
                    self.entry.bound_file({"path": str(path),
                                           "sha256": digest, "bytes": 2,
                                           **changes})
            link = root / "link"
            link.symlink_to(path)
            with self.assertRaises(AssertionError):
                self.entry.bound_file({"path": str(link),
                                       "sha256": digest, "bytes": 2})
            folder = root / "alias"
            folder.symlink_to(root, target_is_directory=True)
            with self.assertRaises(AssertionError):
                self.entry.bound_file({"path": str(folder / path.name),
                                       "sha256": digest, "bytes": 2})

    def test_config_requires_exact_input_set_and_private_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            directory.chmod(0o700)
            self.entry.private_directory(directory)
            directory.chmod(0o755)
            with self.assertRaisesRegex(AssertionError, "private"):
                self.entry.private_directory(directory)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises((AssertionError, KeyError)):
                self.entry.load_configuration()

    def test_success_is_written_once_and_after_cleanup(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            directory.chmod(0o700)
            result = {"status": "PASS", "owned_documents_closed": True}
            self.entry.write_private_result(directory, result)
            target = directory / "result.json"
            self.assertEqual(json.loads(target.read_text()), result)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                self.entry.write_private_result(directory, result)

    def test_live_entry_uses_existing_generate_and_never_recreates_xo(self):
        source = ENTRY.read_text()
        self.assertIn('"_native_generate"', source)
        self.assertIn("preview_private_catalogue_heel_l1_chairs", source)
        self.assertNotIn("create_rea_c10_crossover(", source)
        self.assertNotIn("solve_rea_c10_crossover_geometry(", source)
        self.assertNotIn("refresh_crossover_chair_analysis(", source)
        self.assertIn("preview.undo()", source)
        self.assertIn("preview.redo()", source)
        self.assertIn("late_model_read", source)


if __name__ == "__main__":
    unittest.main()
