#!/usr/bin/env python3
"""Exercise harness prerequisites without FreeCAD or chair construction.

Dispatch checks execute the retained entry statements with a recording main.
Frame checks execute the accepted comparator AST and its accepted length
budget. Subprocess checks use the real pipeline, with a file marker in place
of expensive construction. These are standalone controls, not host evidence.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import math
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import repository_safety_audit as safety  # noqa: E402
from tools import run_regression_pipeline as pipeline  # noqa: E402


RUNTIME_PROBE = ROOT / "tools/runtime_compatibility_probe.py"
NATIVE_FIXTURE = ROOT / "tests/freecad_validate_harness_readiness.py"
CENTRAL_PROOF = (
    ROOT / "tests/freecad_validate_phase9b_catalogue_central_check.py"
)
P_PROOF = ROOT / "tests/freecad_validate_phase9b_catalogue_p_placement.py"
READY_SENTINEL = "HARNESS_PREREQUISITES_PASSED"


def _parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _accepted_comparator():
    """Load only accepted arithmetic, excluding native imports and runners."""
    function, = (
        node for node in _parse(CENTRAL_PROOF).body
        if isinstance(node, ast.FunctionDef) and node.name == "_near_frame"
    )
    budget, = (
        ast.literal_eval(node.value) for node in _parse(P_PROOF).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EPSILON_MM"
                for target in node.targets)
    )
    namespace = {"math": math, "p": SimpleNamespace(EPSILON_MM=budget)}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 str(CENTRAL_PROOF), "exec"), namespace)
    return namespace["_near_frame"], budget


def _frame_pair():
    actual = {
        "origin_mm": (12.25, -7.5, 3.125),
        "x_axis": (0.6, 0.8),
        "y_axis": (-0.8, 0.6),
    }
    return actual, SimpleNamespace(**copy.deepcopy(actual))


def _dispatch(path, name, status=0, failure=None):
    """Run real entry control flow; substitute only the expensive main."""
    entry, = (
        node for node in _parse(path).body
        if isinstance(node, ast.If)
        and any(isinstance(child, ast.Name) and child.id == "__name__"
                for child in ast.walk(node.test))
    )
    calls = []

    def recording_main():
        calls.append(name)
        if failure is not None:
            raise failure
        return status

    namespace = {
        "__name__": name, "__file__": str(path), "main": recording_main,
        "Path": Path,
    }
    exception = None
    try:
        exec(compile(ast.Module(body=[entry], type_ignores=[]),
                     str(path), "exec"), namespace)
    except (SystemExit, RuntimeError, AssertionError) as error:
        exception = error
    return calls, exception


def _asset_specification():
    return {
        "path": Path("source.zip"), "kind": "source-archive",
        "required": True,
        "expected_sha256": hashlib.sha256(b"fixture source\n").hexdigest(),
    }


class EntryContextTests(unittest.TestCase):
    def _check_entry(self, path):
        for name in ("__main__", path.stem):
            with self.subTest(path=path.name, name=name):
                calls, error = _dispatch(path, name)
                self.assertEqual(calls, [name])
                if isinstance(error, SystemExit):
                    self.assertEqual(error.code, 0)
                else:
                    self.assertIsNone(error)
                failure = AssertionError("readiness rejected")
                calls, error = _dispatch(path, name, failure=failure)
                self.assertEqual(calls, [name])
                self.assertIs(error, failure)
        self.assertEqual(_dispatch(path, "_readiness_helper"), ([], None))

    def test_runtime_probe_dispatch(self):
        self._check_entry(RUNTIME_PROBE)
        for name in ("__main__", RUNTIME_PROBE.stem):
            calls, error = _dispatch(RUNTIME_PROBE, name, status=1)
            self.assertEqual(calls, [name])
            self.assertIsInstance(error, (SystemExit, RuntimeError))
            if isinstance(error, SystemExit):
                self.assertNotEqual(error.code, 0)

    def test_native_fixture_dispatch(self):
        self._check_entry(NATIVE_FIXTURE)

    def test_native_fixture_alias_import_is_inert(self):
        # Full module import, with host imports rejected, catches hidden
        # import-time execution that a dispatch-only check cannot observe.
        output = io.StringIO()
        with patch.dict(sys.modules, {"FreeCAD": None, "Part": None}):
            with contextlib.redirect_stdout(output):
                module = runpy.run_path(
                    str(NATIVE_FIXTURE), run_name="_readiness_safe_helper",
                )
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(callable(module["main"]))
        self.assertTrue(callable(module["load_comparator"]))


class ComparatorInputTests(unittest.TestCase):
    def test_complete_asymmetric_frame(self):
        comparator, _budget = _accepted_comparator()
        actual, expected = _frame_pair()
        comparator(actual, expected)

    def test_required_fields_fail_before_construction(self):
        comparator, _budget = _accepted_comparator()
        for field in ("origin_mm", "x_axis", "y_axis"):
            with self.subTest(field=field):
                actual, expected = _frame_pair()
                del actual[field]
                constructed = []
                with self.assertRaisesRegex(KeyError, field):
                    comparator(actual, expected)
                    constructed.append(True)
                self.assertEqual(constructed, [])

    def test_wrong_origin_and_axes_are_rejected(self):
        comparator, budget = _accepted_comparator()
        for field, displacement in (
            ("origin_mm", 2 * budget), ("x_axis", 1e-9), ("y_axis", 1e-9),
        ):
            with self.subTest(field=field):
                actual, expected = _frame_pair()
                actual[field] = tuple(
                    value + displacement if index == 0 else value
                    for index, value in enumerate(actual[field])
                )
                with self.assertRaises(AssertionError):
                    comparator(actual, expected)

    def test_expected_fields_are_required(self):
        comparator, _budget = _accepted_comparator()
        for field in ("origin_mm", "x_axis", "y_axis"):
            with self.subTest(field=field):
                actual, expected = _frame_pair()
                delattr(expected, field)
                with self.assertRaisesRegex(AttributeError, field):
                    comparator(actual, expected)


class NativeFixtureHelperTests(unittest.TestCase):
    def test_frame_helper_uses_the_accepted_comparator(self):
        module = runpy.run_path(
            str(NATIVE_FIXTURE), run_name="_readiness_helper",
        )
        comparator, _budget = _accepted_comparator()
        result = module["check_frames"](comparator)
        self.assertEqual(result["valid_frames"], 1)
        self.assertCountEqual(result["rejected_inputs"], [
            "missing-origin_mm", "different-origin_mm",
            "missing-x_axis", "different-x_axis",
            "missing-y_axis", "different-y_axis",
            "missing-expected-origin_mm",
        ])

    def test_asset_helper_uses_the_existing_isolation_contract(self):
        module = runpy.run_path(
            str(NATIVE_FIXTURE), run_name="_readiness_helper",
        )
        with tempfile.TemporaryDirectory() as directory:
            result = module["check_assets"](Path(directory))
        self.assertEqual(result["valid_assets"], 1)
        self.assertCountEqual(result["rejected_inputs"],
                              ["wrong-hash", "missing", "escaped-path"])


class IsolatedAssetTests(unittest.TestCase):
    def test_escaped_source_rejected_even_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "worktree"
            root.mkdir()
            external = base / "source.zip"
            external.write_bytes(b"fixture source\n")
            (root / "source.zip").symlink_to(external)
            with self.assertRaisesRegex(safety.SafetyAuditError, "escaped"):
                safety._asset_record(root, _asset_specification())

    def test_local_missing_wrong_and_correct_hash_readiness(self):
        repository = {
            "working_tree_clean": True, "upstream": "origin/fixture",
            "ahead": 0, "behind": 0, "checkpoint_ready": True,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for content, ready, finding in (
                (None, False, "required-local-asset-missing:source.zip"),
                (b"different\n", False,
                 "required-local-asset-hash-mismatch:source.zip"),
                (b"fixture source\n", True, None),
            ):
                with self.subTest(content=content):
                    if content is not None:
                        (root / "source.zip").write_bytes(content)
                    with patch.object(safety, "LOCAL_ASSETS", (
                        _asset_specification(),
                    )), patch.object(
                        safety, "_repository_state", return_value=repository,
                    ):
                        report = safety.audit_repository(root)
                    self.assertEqual(
                        report["readiness"]["critical_assets_ready"], ready,
                    )
                    if finding:
                        self.assertIn(finding, report["findings"])


def _readiness_case(case, root):
    if case == "wrong-entry":
        calls, error = _dispatch(RUNTIME_PROBE, "_readiness_helper")
        assert not calls and error is None
        return
    if case == "escaped-asset":
        safety._asset_record(root, _asset_specification())
    comparator, _budget = _accepted_comparator()
    actual, expected = _frame_pair()
    if case == "missing-origin":
        del actual["origin_mm"]
    comparator(actual, expected)
    print(READY_SENTINEL, flush=True)


class FailFastPipelineTests(unittest.TestCase):
    def test_prerequisites_gate_the_construction_marker(self):
        for case, expected_reason in (
            ("missing-origin", "nonzero-exit"),
            ("wrong-entry", "missing-success-sentinel"),
            ("escaped-asset", "nonzero-exit"),
            ("valid", None),
        ):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as directory:
                    base = Path(directory)
                    root = base / "worktree"
                    root.mkdir()
                    outside = base / "source.zip"
                    outside.write_bytes(b"fixture source\n")
                    (root / "source.zip").symlink_to(outside)
                    marker = root / "construction.marker"
                    program = root / "construction.py"
                    program.write_text(
                        "from pathlib import Path\n"
                        f"Path({str(marker)!r}).write_text('constructed')\n"
                        "print('CONSTRUCTION_MARKER_PASSED')\n",
                        encoding="utf-8",
                    )
                    steps = (
                        pipeline.PipelineStep(
                            "readiness", (sys.executable, __file__,
                                          "--readiness-case", case, str(root)),
                            READY_SENTINEL,
                        ),
                        pipeline.PipelineStep(
                            "construction-marker",
                            (sys.executable, str(program)),
                            "CONSTRUCTION_MARKER_PASSED",
                        ),
                    )
                    with contextlib.redirect_stdout(io.StringIO()):
                        result = pipeline.run_pipeline(
                            profile="standalone", steps=steps, root=root,
                            run_directory=root / "logs",
                        )
                    self.assertEqual(
                        result["results"][0]["failure_reason"],
                        expected_reason,
                    )
                    self.assertEqual(marker.exists(), expected_reason is None)
                    if expected_reason:
                        self.assertEqual(result["failed"], ["readiness"])
                        self.assertEqual(result["skipped"],
                                         ["construction-marker"])
                        self.assertEqual(result["completed_count"], 1)
                        log = (root / "logs/01-readiness.log").read_text()
                        if case == "missing-origin":
                            self.assertIn("KeyError: 'origin_mm'", log)
                        elif case == "escaped-asset":
                            self.assertIn("local asset escaped", log)
                    else:
                        self.assertEqual(result["failed"], [])
                        self.assertEqual(result["completed_count"], 2)
                        self.assertEqual(marker.read_text(), "constructed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--readiness-case":
        _readiness_case(sys.argv[2], Path(sys.argv[3]))
    else:
        unittest.main()
