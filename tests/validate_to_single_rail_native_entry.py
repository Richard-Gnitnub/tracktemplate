#!/usr/bin/env python3
"""Check the fixed TO native entry without loading FreeCAD or Qt."""

import ast
from contextlib import contextmanager, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import freecad_validate_to_single_rail as entry  # noqa: E402


SENTINEL = "Fixed TO single-rail native entry offline checks passed"


@contextmanager
def composed_session():
    """Reuse the existing host fixture with both real session layers."""
    from tracktemplate import api
    from tracktemplate.compatibility import (
        b15_workflow_host, transition_workflow,
    )
    from validate_phase7_concentric_core import _fixture

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        host = b15_workflow_host.load_b15_workflow_host(root, _fixture(root))
        module = host.module
        for _, name in transition_workflow.CORE_LAYOUT_EXPORT_HOST_OPERATIONS:
            exec(f"def {name}(*args, **kwargs):\n"
                 "    raise AssertionError('Unexpected export')\n",
                 module.__dict__)
        tree = ast.parse((root / "legacy.FCMacro").read_text())
        caller = next(node for node in tree.body
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "run_macro")
        caller.body.insert(0, ast.parse("run_production_export()").body[0])
        exec(compile(ast.Module(body=[caller], type_ignores=[]),
                     str(root / "legacy.FCMacro"), "exec"), module.__dict__)
        inner = transition_workflow.ModularTransitionWorkflowSession(
            host, {name: getattr(api, name) for name in
                   transition_workflow.PRODUCT_FUNCTION_NAMES},
        )
        yield transition_workflow.ModularCoreLayoutWorkflowSession(
            inner, api.run_core_layout_export,
        )


class NativeEntryTests(unittest.TestCase):
    def fixture(self):
        return entry.read_fixture()

    def test_import_and_exact_named_discovery_are_host_free(self):
        for name in ("FreeCAD", "FreeCADGui", "Part", "PySide6"):
            self.assertNotIn(name, sys.modules)
        loader = unittest.defaultTestLoader
        self.assertEqual(loader.getTestCaseNames(entry.ToSingleRail),
                         ["test_fixed_twelve", "test_readiness"])
        for method in ("test_readiness", "test_fixed_twelve"):
            suite = loader.loadTestsFromName("ToSingleRail." + method, entry)
            self.assertEqual(suite.countTestCases(), 1)
            self.assertEqual(next(iter(suite))._testMethodName, method)

    def test_fixture_provenance_and_exact_counts(self):
        values = self.fixture()
        self.assertEqual(entry.validate_fixture(values), 59)
        self.assertEqual(len(values["positions"]), 12)
        self.assertEqual(sum(row["family"] == "L1"
                             for row in values["positions"]), 11)
        for field in ("source_context_sha256", "source_analysis_sha256",
                      "source_archive_sha256", "source_receipt_sha256",
                      "source_member_sha256", "model_sha256"):
            changed = copy.deepcopy(values)
            changed[field] = "wrong"
            with self.subTest(field=field), self.assertRaises(AssertionError):
                entry.validate_fixture(changed)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            work, evidence = base / "work", base / "evidence"
            work.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            rows = []
            for name in entry.INPUT_HASHES:
                path = base / name
                path.write_bytes(name.encode())
                rows.append(dict(id=name, path=str(path), bytes=len(name),
                                 sha256=hashlib.sha256(name.encode()).hexdigest()))
            hashes = {row["id"]: row["sha256"] for row in rows}
            recovery = base / "recovery.json"
            recovery.write_text(json.dumps(dict(
                status="PASS", independent_review="PASS",
                checkpoint_commit="1" * 40, input_hashes=hashes,
            )))
            config = dict(
                schema_version=1, scope_id=entry.SCOPE, stage="readiness",
                source_commit="1" * 40,
                entry_sha256=entry.shared().sha256(Path(entry.__file__)),
                inputs=rows, recovery=dict(path=str(recovery),
                                          bytes=recovery.stat().st_size,
                                          sha256=entry.shared().sha256(recovery)),
                working_directory=str(work), evidence_directory=str(evidence),
                handling_decision="disposable offline test only",
            )
            path = base / "config.json"
            environment = dict(
                GITHUB_ACTIONS="true", RUNNER_ENVIRONMENT="github-hosted",
                GITHUB_RUN_ATTEMPT="1", GITHUB_RUN_ID="123",
                GITHUB_SHA="1" * 40, TRACKTEMPLATE_TO_RUN_CONFIG=str(path),
            )
            for change in (None, "stage", "duplicate", "digest", "unknown"):
                value = copy.deepcopy(config)
                if change == "stage":
                    value["stage"] = "native"
                elif change == "duplicate":
                    value["inputs"][-1] = value["inputs"][0]
                elif change == "digest":
                    value["entry_sha256"] = "0" * 64
                elif change == "unknown":
                    value["unknown"] = 1
                path.write_text(json.dumps(value))
                environment["TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"] = (
                    entry.shared().sha256(path)
                )
                with (patch.dict(entry.INPUT_HASHES, hashes, clear=True),
                      patch.dict("os.environ", environment, clear=True)):
                    if change is None:
                        self.assertEqual(entry.configuration("readiness").work,
                                         work)
                    else:
                        with self.subTest(change=change), self.assertRaises(
                                AssertionError):
                            entry.configuration("readiness")
            for commit in (None, "wrong", "A" * 40, "1" * 39, "1" * 41):
                value = copy.deepcopy(config)
                value["source_commit"] = commit
                path.write_text(json.dumps(value))
                env = dict(environment)
                env["TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"] = (
                    entry.shared().sha256(path)
                )
                if commit is None:
                    env.pop("GITHUB_SHA")
                else:
                    env["GITHUB_SHA"] = commit
                with (patch.dict(entry.INPUT_HASHES, hashes, clear=True),
                      patch.dict("os.environ", env, clear=True),
                      patch.object(entry, "verify_inputs") as verify):
                    with self.subTest(commit=commit), self.assertRaises(
                            AssertionError):
                        entry.configuration("readiness")
                    self.assertEqual(verify.call_count, 0)

    def test_fixture_rejects_identity_family_and_frame_count_changes(self):
        for kind in ("missing", "duplicate", "order", "family", "rail",
                     "timber", "source", "fixings", "unknown"):
            values = self.fixture()
            row = values["positions"][0]
            if kind == "missing":
                values["positions"].pop()
            elif kind == "duplicate":
                values["positions"][-1] = copy.deepcopy(row)
            elif kind == "order":
                values["positions"].reverse()
            elif kind == "fixings":
                row["fixing_frames"].pop()
            elif kind == "unknown":
                row["unknown"] = 1
            else:
                key = {"family": "family", "rail": "rail_id",
                       "timber": "timber_id",
                       "source": "source_receipt_sha256"}[kind]
                row[key] = "wrong"
            with self.subTest(kind=kind), self.assertRaises(AssertionError):
                entry.validate_fixture(values)

    def test_json_and_frame_numbers_fail_closed(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                entry.strict_json(text)
        for value in (True, None, "1", float("inf"), float("nan"), 10**400):
            values = self.fixture()
            values["positions"][0]["body"]["origin_mm"][0] = value
            with self.subTest(value=type(value)), self.assertRaises(
                    (AssertionError, ValueError)):
                entry.validate_fixture(values)

    def test_component_mapping_preserves_body_and_indexed_fixings(self):
        fixture = self.fixture()
        count = 0
        for row in fixture["positions"]:
            names = entry.component_names(row["family"])
            bodies = 7 if row["family"] == "L1" else 5
            for index, name in enumerate(names):
                expected = (row["body"] if index < bodies else
                            row["fixing_frames"][(index - bodies) // 4])
                self.assertIs(entry.component_frame(row, name), expected)
                count += 1
            with self.assertRaises(ValueError):
                entry.component_frame(row, "unknown")
        self.assertEqual(count, 270)
        opened, closed = [], []
        documents = {}

        def open_copy(_app, record, _work, name, owned):
            family = record["family"]
            document = SimpleNamespace(Name=family, Objects=[
                SimpleNamespace(Name=key, TypeId="Part::Feature", Shape=key)
                for key in entry.component_names(family)
            ])
            documents[family] = document
            owned[family] = document
            opened.append(name)
            return document

        def close(name):
            closed.append(name)
            documents.pop(name)

        app = SimpleNamespace(closeDocument=close,
                              listDocuments=lambda: dict(documents))
        part = SimpleNamespace(Shape=lambda shape: ("native-copy", shape))
        inputs = {key.lower() + "_model": {"family": key}
                  for key in ("L1", "S1")}
        with patch.object(entry, "open_copy", open_copy):
            references = entry.reference_shapes(app, part, inputs, ROOT, {})
        self.assertEqual(opened, ["L1-copy.FCStd", "S1-copy.FCStd"])
        self.assertEqual(closed, ["L1", "S1"])
        self.assertFalse(documents)
        self.assertEqual(references["S1"]["Part_00"],
                         ("native-copy", "Part_00"))

    def test_mixed_layer_structure_rejects_missing_reordered_or_wrong_counts(self):
        names = entry.layer_names()
        counts = {name: 11 if name.startswith("L1_") else 1
                  for name in names[2:]}
        self.assertEqual(entry.check_layers(names, counts), 270)
        variants = [(names[:-1], counts), (names[::-1], counts)]
        for name in ("L1_Part_00", "S1_Part_00"):
            changed = dict(counts, **{name: counts[name] + 1})
            variants.append((names, changed))
        variants.append((names, dict(counts, unknown=1)))
        for observed, sizes in variants:
            with self.assertRaises(AssertionError):
                entry.check_layers(observed, sizes)

    def test_retained_comparator_and_wrong_frame_rejection(self):
        helpers = entry.shared().load_comparator(ROOT)
        self.assertEqual(entry.shared().comparator_controls(helpers), 8)
        first = self.fixture()["positions"][0]["body"]
        entry.shared().compare_frame(SimpleNamespace(**first), first)
        wrong = copy.deepcopy(first)
        wrong["origin_mm"][0] += 1
        with self.assertRaises(AssertionError):
            entry.shared().compare_frame(SimpleNamespace(**wrong), first)

    def run_readiness(self, session, *, cleanup_error=False, input_error=False):
        """Run the complete named test; mock only host/input boundaries."""
        fixture = self.fixture()
        app = SimpleNamespace(
            listDocuments=lambda: {}, ActiveDocument=None, GuiUp=False,
            newDocument=lambda *args: self.fail("created document"),
            openDocument=lambda *args: self.fail("opened document"),
        )
        part = SimpleNamespace(Shape=lambda: None, makeCompound=lambda x: x)
        captured = []
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(
                inputs={}, fixture=fixture, work=Path(directory),
                evidence=Path(directory), source_commit="1" * 40,
            )
            with (patch.object(entry, "configuration", return_value=config),
                  patch.object(entry, "runtime", return_value=(app, session)),
                  patch.object(entry, "native_imports", return_value=part),
                  patch.object(entry, "catalogues", return_value={
                      "L1": object(), "S1": object()}),
                  patch.object(entry, "verify_inputs", side_effect=(
                      RuntimeError("input changed") if input_error else None)),
                  patch.object(entry, "write_result", side_effect=(
                      lambda _config, result: captured.append(result))),
                  patch.object(entry, "cleanup", side_effect=(
                      RuntimeError("cleanup failed") if cleanup_error else
                      lambda *_args: None)) as clean,
                  redirect_stdout(io.StringIO())):
                try:
                    entry.ToSingleRail("test_readiness").test_readiness()
                finally:
                    self.assertEqual(clean.call_count, 1)
                    if cleanup_error or input_error:
                        self.assertEqual(captured[0]["status"], "FAIL")
                        self.assertNotIn("sentinel", captured[0])
        return captured

    def test_actual_readiness_uses_real_composed_binding(self):
        with composed_session() as session:
            result = self.run_readiness(session)[0]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checks"], entry.expected_checks("readiness"))
        self.assertEqual(result["remaining_documents"], 0)

    def test_readiness_rejects_real_calculation_and_export_mutation(self):
        from tracktemplate.compatibility.transition_workflow import (
            TransitionWorkflowError,
        )
        for name in ("build_concentric_core", "run_production_export"):
            with self.subTest(name=name), composed_session() as session:
                setattr(session.module, name, lambda *args: None)
                with self.assertRaises(TransitionWorkflowError):
                    self.run_readiness(session)

    def test_cleanup_failure_never_emits_success(self):
        with composed_session() as session:
            with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
                self.run_readiness(session, cleanup_error=True)
            with self.assertRaisesRegex(RuntimeError, "input changed"):
                self.run_readiness(session, input_error=True)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeEntryTests),
    )
    if result.wasSuccessful() and result.testsRun == 10 and not result.skipped:
        print(SENTINEL)
    else:
        raise SystemExit(1)
