"""Offline counterexamples for the fixed pre-execution diagnostic adapter."""

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import prepare_runtime_assessment as assessment  # noqa: E402
from tools import runtime_compatibility_diagnostics as diagnostic  # noqa: E402


HOST = "tests/freecad_validate_phase8_crossover_host_integration_recovery.py"
REPORT = "tests/freecad_validate_phase7_connected_straight_validation.py"
PHASE5 = "tools/freecad_bridge/run_phase5_transition_viewprovider.py"


def predecessor(relative):
    raw = (ROOT / relative).read_bytes()
    for name, _, old in assessment.PROFILE_ADAPTATIONS:
        if name == relative:
            raw = raw.replace(old.encode(),
                              assessment.CANDIDATE_PROFILE.encode(), 1)
    if relative.endswith("run_phase8_crossover_preflight_gui.py"):
        raw = raw.replace(b"b14-default-base.FCStd",
                          b"b14-default-base-regenerated.FCStd", 1)
    return raw


def helper_namespace(relative):
    namespace = {}
    exec(diagnostic._helper_source(diagnostic.SOURCES[relative]), namespace)
    return namespace


def compile_node(node, namespace):
    module = ast.Module(body=[copy.deepcopy(node)], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<bound-source>", "exec"),
         namespace)


def function(raw, name):
    return next(node for node in ast.parse(raw).body
                if isinstance(node, ast.FunctionDef) and node.name == name)


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tt-diagnostic-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.session = self.root / "session"
        self.session.mkdir(mode=0o700)
        self.environment = patch.dict(
            os.environ, {diagnostic.SESSION_ENV: str(self.session)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def report(self, relative=REPORT, payload=None):
        namespace = helper_namespace(relative)
        site = diagnostic.SOURCES[relative]["sites"][0][2]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            namespace["_tt_diagnostic_report"](
                site, json.dumps(payload or {"raw_points": [[1, 2, 3]]}),
                flush=True)
        return site, stdout.getvalue()

    def fixture(self):
        tree = self.root / "assessment"
        tree.mkdir(mode=0o700)
        rows = []
        for relative, binding in diagnostic.SOURCES.items():
            path = tree / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = predecessor(relative)
            path.write_bytes(raw)
            path.chmod(0o644)
            rows.append({
                "path": relative, "original": {
                    "bytes": len((ROOT / relative).read_bytes()),
                    "sha256": binding["original_sha256"],
                }, "assessment": diagnostic._identity(raw), "mode": 0o644,
                "adapted": raw != (ROOT / relative).read_bytes(),
            })
        raw = (ROOT / diagnostic.B15_PATH).read_bytes()
        (tree / diagnostic.B15_PATH).write_bytes(raw)
        (tree / diagnostic.B15_PATH).chmod(0o644)
        rows.append({"path": diagnostic.B15_PATH,
                     "original": diagnostic._identity(raw),
                     "assessment": diagnostic._identity(raw),
                     "mode": 0o644, "adapted": False})
        (tree / "base.FCStd").write_bytes(b"offline fixture, never executed")
        (tree / "base.FCStd").chmod(0o644)
        (tree / "_assessment").mkdir()
        (tree / "_assessment/adaptations.diff").write_bytes(b"")
        (tree / "_assessment/adaptations.diff").chmod(0o644)
        manifest = {
            "base_commit": assessment.BASE_COMMIT, "source_files": rows,
            "base_fixture": {"path": "base.FCStd", **diagnostic._identity(
                (tree / "base.FCStd").read_bytes())},
            "adaptation_diff": diagnostic._identity(b""),
        }
        (tree / "_assessment/manifest.json").write_bytes(
            assessment._json_bytes(manifest))
        (tree / "_assessment/manifest.json").chmod(0o644)
        return tree, manifest

    def test_every_fixed_source_preserves_complete_other_ast(self):
        self.assertEqual(len(diagnostic.SOURCES), 21)
        self.assertEqual(sum(len(row["sites"])
                             for row in diagnostic.SOURCES.values()), 24)
        for relative in diagnostic.SOURCES:
            with self.subTest(source=relative):
                before = predecessor(relative)
                after, receipt = diagnostic.transform_source(relative, before)
                self.assertTrue(diagnostic.verify_equivalence(
                    relative, before, after))
                self.assertEqual(receipt["successor"],
                                 diagnostic._identity(after))
                self.assertEqual(
                    sum(isinstance(n, ast.Assert)
                        for n in ast.walk(ast.parse(before))),
                    sum(isinstance(n, ast.Assert)
                        for n in ast.walk(ast.parse(after))))

    def test_original_native38_counterexample_rejected_without_geometry_text(self):
        before = predecessor(HOST)
        after, _ = diagnostic.transform_source(HOST, before)
        value = {"changed": {"CuttingProfile": {
            "shape": {"bounds_mm": [1, 2, 3, 4, 5, 6]}}}}
        calls = []
        namespace = helper_namespace(HOST)
        namespace["_difference"] = lambda old, new: (
            calls.append((old, new)) or value)
        compile_node(function(before, "_assert_equal"), namespace)
        with self.assertRaises(AssertionError) as former:
            namespace["_assert_equal"]({"state": 1}, {"state": 2}, "undo")
        self.assertIn("bounds_mm", str(former.exception))
        self.assertEqual(len(calls), 1)
        calls.clear()
        compile_node(function(after, "_assert_equal"), namespace)
        with self.assertRaises(AssertionError) as successor:
            namespace["_assert_equal"]({"state": 1}, {"state": 2}, "undo")
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(successor.exception),
                         "TT_DIAGNOSTIC site=n38-state value_sha256="
                         + hashlib.sha256(str(former.exception).encode())
                         .hexdigest())
        self.assertNotIn("bounds_mm", str(successor.exception))
        calls.clear()
        namespace["_assert_equal"]({"state": 1}, {"state": 1}, "undo")
        self.assertEqual(calls, [])

    def test_original_message_expression_exception_is_not_intercepted(self):
        after, _ = diagnostic.transform_source(HOST, predecessor(HOST))
        namespace = helper_namespace(HOST)
        original = RuntimeError("Original callback failure")

        def failing_difference(before, after):
            raise original

        namespace["_difference"] = failing_difference
        compile_node(function(after, "_assert_equal"), namespace)
        with self.assertRaises(RuntimeError) as caught:
            namespace["_assert_equal"](1, 2, "undo")
        self.assertIs(caught.exception, original)

    def test_each_named_message_keeps_expression_once_and_exception_class(self):
        for relative, binding in diagnostic.SOURCES.items():
            before = predecessor(relative)
            for kind, line, site, _, _ in binding["sites"]:
                if kind in ("report", "embedded-raise", "loader"):
                    continue
                with self.subTest(site=site):
                    namespace = helper_namespace(relative)
                    calls = []

                    def message():
                        calls.append(site)
                        return {"excluded": [1, 2, 3]}

                    namespace["message"] = message
                    original = next(n for n in ast.walk(ast.parse(before))
                                    if getattr(n, "lineno", 0) == line
                                    and isinstance(n, (ast.Assert, ast.Raise)))
                    exception_class = ("AssertionError" if kind == "message"
                                       else original.exc.func.id)
                    source = ("raise " + exception_class
                              + "(_tt_diagnostic_message(" + repr(site)
                              + ", message()))")
                    with self.assertRaises(Exception) as caught:
                        exec(source, namespace)
                    self.assertEqual(type(caught.exception).__name__,
                                     exception_class)
                    self.assertEqual(calls, [site])
                    self.assertNotIn("excluded", str(caught.exception))

    def test_private_report_is_exact_original_print_and_public_witness(self):
        before = predecessor(REPORT)
        after, _ = diagnostic.transform_source(REPORT, before)
        original_node = diagnostic._selected_node(ast.parse(before),
                                                  "report", 216)
        successor_node = next(n for n in ast.walk(ast.parse(after))
                              if isinstance(n, ast.Call)
                              and isinstance(n.func, ast.Name)
                              and n.func.id == "_tt_diagnostic_report")
        namespace = helper_namespace(REPORT)
        namespace.update(json=json, result={"raw_points": [[1, 2, 3]],
                                            "input_array": ["private"]})
        original = io.StringIO()
        with contextlib.redirect_stdout(original):
            compile_node(ast.Expr(value=original_node), namespace)
        public = io.StringIO()
        with contextlib.redirect_stdout(public):
            compile_node(ast.Expr(value=successor_node), namespace)
        path = self.session / "diagnostic-private/n24-report.txt"
        self.assertEqual(path.read_bytes(), original.getvalue().encode())
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        witness = json.loads(public.getvalue().removeprefix(
            diagnostic.REPORT_MARKER))
        self.assertEqual(witness, {"site": "n24-report",
                                   **diagnostic._identity(path.read_bytes())})
        self.assertNotIn("raw_points", public.getvalue())
        self.assertNotIn(str(self.session), public.getvalue())

    def test_phase5_sentinel_survives_with_bound_private_report(self):
        site, public = self.report(PHASE5)
        self.assertEqual(site, "g05-report")
        self.assertTrue(public.startswith(
            "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI="))
        self.assertTrue((self.session / "diagnostic-private/g05-report.txt")
                        .is_file())

    def test_report_original_argument_failure_runs_before_helper(self):
        namespace = helper_namespace(REPORT)
        with self.assertRaises(ValueError):
            namespace["_tt_diagnostic_report"](
                "n24-report", json.dumps(float("nan"), allow_nan=False))
        self.assertFalse((self.session / "diagnostic-private").exists())

    def test_private_report_never_overwrites_original(self):
        site, _ = self.report()
        path = self.session / "diagnostic-private" / (site + ".txt")
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.report(payload={"replacement": True})
        self.assertEqual(path.read_bytes(), original)

    def test_report_rejects_missing_relative_linked_or_public_session(self):
        namespace = helper_namespace(REPORT)
        linked = self.root / "linked"
        linked.symlink_to(self.session, target_is_directory=True)
        for value in ("", "relative", str(linked), str(self.session / "..")):
            with self.subTest(value=value), patch.dict(
                    os.environ, {diagnostic.SESSION_ENV: value}):
                with self.assertRaises(ValueError):
                    namespace["_tt_diagnostic_report"]("n24-report", "data")
        self.session.chmod(0o755)
        with self.assertRaises(ValueError):
            self.report()

    def test_report_rejects_linked_private_directory_and_file(self):
        target = self.root / "elsewhere"
        target.mkdir(mode=0o700)
        private = self.session / "diagnostic-private"
        private.symlink_to(target, target_is_directory=True)
        with self.assertRaises(OSError):
            self.report()
        private.unlink()
        private.mkdir(mode=0o700)
        target_file = target / "untouched"
        target_file.write_bytes(b"retained")
        (private / "n24-report.txt").symlink_to(target_file)
        with self.assertRaises(FileExistsError):
            self.report()
        self.assertEqual(target_file.read_bytes(), b"retained")

    def test_unlisted_site_and_output_stream_are_refused(self):
        namespace = helper_namespace(REPORT)
        for site, keywords in (("../../escape", {}),
                               ("n24-report", {"file": sys.stdout})):
            with self.assertRaises(ValueError):
                namespace["_tt_diagnostic_report"](site, "data", **keywords)
        self.assertFalse((self.session / "diagnostic-private").exists())

    def test_source_drift_unlisted_source_and_repeat_are_refused(self):
        before = predecessor(HOST)
        after, _ = diagnostic.transform_source(HOST, before)
        for path, raw in ((HOST, before + b"\n"), (HOST, after),
                          ("unlisted.py", before)):
            with self.assertRaises(ValueError):
                diagnostic.transform_source(path, raw)

    def test_equivalence_detects_predicate_cleanup_or_helper_changes(self):
        before = predecessor(HOST)
        after, _ = diagnostic.transform_source(HOST, before)
        variants = (after.replace(b"if before != after:",
                                  b"if before == after:", 1),
                    after.replace(b"App.closeDocument(document.Name)",
                                  b"App.closeDocument('wrong')", 1),
                    after.replace(b"str(value).encode", b"repr(value).encode", 1))
        for raw in variants:
            self.assertNotEqual(raw, after)
            with self.assertRaises(ValueError):
                diagnostic.verify_equivalence(HOST, before, raw)

    def test_complete_disposable_adaptation_and_preflight_no_partial_write(self):
        tree, manifest = self.fixture()
        changed, receipt = diagnostic.adapt_diagnostics(tree, manifest)
        self.assertEqual(receipt["source_count"], 21)
        self.assertEqual(receipt["site_count"], 24)
        self.assertEqual(assessment.verify_assessment(tree, changed)["status"],
                         "PASS")
        self.assertNotIn("diagnostic_successor", manifest)
        with self.assertRaises(ValueError):
            diagnostic.adapt_diagnostics(tree, changed)

    def test_missing_drift_and_hardlink_fail_before_other_writes(self):
        tree, manifest = self.fixture()
        first = tree / next(iter(diagnostic.SOURCES))
        retained = first.read_bytes()
        last = tree / list(diagnostic.SOURCES)[-1]
        os.link(last, self.root / "hardlink")
        with self.assertRaises(ValueError):
            diagnostic.adapt_diagnostics(tree, manifest)
        self.assertEqual(first.read_bytes(), retained)
        self.assertNotIn("diagnostic_successor", json.loads(
            (tree / "_assessment/manifest.json").read_text()))

    def test_native46_original_causal_prints_are_outside_adaptation(self):
        path = "tests/freecad_validate_phase8_turnout_host_integration_recovery.py"
        self.assertNotIn(path, diagnostic.SOURCES)
        source = (ROOT / path).read_text()
        self.assertIn('print("PHASE8_TURNOUT_HOST_DIFFERENCE="', source)
        self.assertIn('print("PHASE8_TURNOUT_HOST_REOPEN_DIFFERENCE="', source)

    def test_fixed_helper_source_parses_directly(self):
        ast.parse(diagnostic.INLINE_HELPERS)

    def test_compiled_macro_changes_only_console_argument_and_keeps_panel(self):
        raw = (ROOT / diagnostic.B15_PATH).read_bytes()
        receipt = diagnostic.compiled_b15_receipt(raw)
        self.assertTrue(receipt["original_file_unchanged"])
        namespace = helper_namespace(diagnostic.LOADER_PATH)
        original = ast.parse(raw)
        original.body.pop()
        derived = namespace["_tt_diagnostic_b15_tree"](original, raw.decode())
        original_method = next(n for n in ast.walk(original)
                               if isinstance(n, ast.FunctionDef)
                               and n.name == "preview_geometry"
                               and n.lineno == 38670)
        derived_method = next(n for n in ast.walk(derived)
                              if isinstance(n, ast.FunctionDef)
                              and n.name == "preview_geometry"
                              and n.lineno == 38670)
        original_warning = []
        public_warning = []
        original_panel = []
        derived_panel = []
        selected_panel = original_panel
        warnings = original_warning

        def reject(*args, **kwargs):
            raise ValueError("Expected 500 mm radius rejection")

        def panel():
            return SimpleNamespace(
                doc=object(), proposed_values=lambda: (),
                _preview_signature=lambda values: "signature",
                _last_preview_signature=None, _last_preview_result=None,
                diagnostics=SimpleNamespace(setPlainText=selected_panel.append))

        namespace.update(
            solve_rea_c10_crossover_geometry=reject,
            crossover_solver_trace_text=lambda: "chosen_xy=(123.4, 567.8)",
            App=SimpleNamespace(Console=SimpleNamespace(
                PrintWarning=lambda value: warnings.append(value))))
        compile_node(original_method, namespace)
        original_object = panel()
        for _ in range(4):
            self.assertIsNone(namespace["preview_geometry"](original_object))
        selected_panel = derived_panel
        warnings = public_warning
        compile_node(derived_method, namespace)
        derived_object = panel()
        for _ in range(4):
            self.assertIsNone(namespace["preview_geometry"](derived_object))
        self.assertEqual(derived_panel, original_panel)
        self.assertIn("chosen_xy", original_warning[0])
        self.assertNotIn("chosen_xy", public_warning[0])
        for index, value in enumerate(original_warning, 1):
            path = self.session / ("diagnostic-private/b15-console-%04d.txt"
                                   % index)
            self.assertEqual(path.read_bytes(), value.encode())
        checked = diagnostic.verify_private_reports(
            self.session, "phase8-crossover_preflight", public_warning,
            completed=True)
        self.assertEqual(checked["console_instances"], 4)

    def test_compiled_macro_source_or_prior_ast_drift_is_refused(self):
        raw = (ROOT / diagnostic.B15_PATH).read_bytes()
        namespace = helper_namespace(diagnostic.LOADER_PATH)
        original = ast.parse(raw)
        original.body.pop()
        with self.assertRaises(ValueError):
            namespace["_tt_diagnostic_b15_tree"](original, raw.decode() + "\n")
        original.body.pop()
        with self.assertRaises(ValueError):
            namespace["_tt_diagnostic_b15_tree"](original, raw.decode())

    def test_console_instances_are_unique_and_bounded(self):
        namespace = helper_namespace(diagnostic.LOADER_PATH)
        values = [namespace["_tt_diagnostic_console"]("b15-console", "original")
                  for _ in range(9)]
        self.assertEqual(len(set(values)), 9)
        with self.assertRaises(ValueError):
            namespace["_tt_diagnostic_console"]("b15-console", "tenth")
        self.assertEqual(len(list((self.session / "diagnostic-private")
                                  .iterdir())), 9)
        result = diagnostic.verify_private_reports(
            self.session, "phase8-straight_host_crossover", values,
            completed=False)
        self.assertEqual(result["console_instances"], 9)
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "phase8-straight_host_crossover", values,
                completed=True)

    def test_embedded_message_retains_actual_original_value_evaluation(self):
        relative = "tools/freecad_bridge/run_phase8_crossover_preflight_gui.py"
        before = predecessor(relative)
        after, _ = diagnostic.transform_source(relative, before)
        former, inner, sites = diagnostic._embedded_sites(
            ast.parse(before), diagnostic.SOURCES[relative]["sites"])[0]
        expression = diagnostic._selected_node(inner, "raise", sites[0][1])
        changed = next(n for n in ast.walk(ast.parse(after))
                       if isinstance(n, ast.Constant)
                       and isinstance(n.value, str)
                       and "_TT_DIAGNOSTIC_SITES" in n.value)
        wrapper = next(n for n in ast.walk(ast.parse(changed.value))
                       if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Name)
                       and n.func.id == "_tt_diagnostic_message")
        namespace = helper_namespace(relative)
        calls = []
        namespace["panel"] = SimpleNamespace(diagnostics=SimpleNamespace(
            toPlainText=lambda: calls.append(1) or "chosen_xy=(123,456)"))
        old = eval(compile(ast.Expression(expression), "<original>", "eval"),
                   namespace)
        self.assertEqual(calls, [1])
        calls.clear()
        new = eval(compile(ast.Expression(wrapper), "<successor>", "eval"),
                   namespace)
        self.assertEqual(calls, [1])
        self.assertTrue(new.endswith(hashlib.sha256(old.encode()).hexdigest()))
        self.assertNotIn("chosen_xy", new)
        self.assertEqual(former.value.count("panel.preview_geometry()"),
                         changed.value.count("panel.preview_geometry()"))

    def test_private_verification_rejects_missing_extra_changed_and_duplicate(self):
        site, text = self.report()
        path = self.session / "diagnostic-private" / (site + ".txt")
        original = path.read_bytes()
        self.assertEqual(diagnostic.verify_private_reports(
            self.session, "native-24", [text], completed=True)["status"], "PASS")
        for channel in ([], [text, text], [text.replace('"bytes": ',
                                                       '"extra": 1, "bytes": ')],
                        [text.replace('"bytes": ' + str(len(original)),
                                      '"bytes": true')]):
            with self.assertRaises(ValueError):
                diagnostic.verify_private_reports(
                    self.session, "native-24", channel, completed=True)
        path.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "native-24", [text], completed=True)
        path.write_bytes(original)
        extra = path.parent / "unlisted.txt"
        extra.write_bytes(b"extra")
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "native-24", [text], completed=True)

    def test_completed_source_requires_report_and_expected_console_count(self):
        for entry in ("native-24", "phase5-view-edit-lifecycle",
                      "phase8-crossover_preflight",
                      "phase8-straight_host_crossover"):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                diagnostic.verify_private_reports(
                    self.session, entry, [], completed=True)
        for entry in ("native-99", "unlisted"):
            with self.assertRaises(ValueError):
                diagnostic.verify_private_reports(
                    self.session, entry, [], completed=False)

    def test_console_sidecar_does_not_invent_stdout_visibility(self):
        namespace = helper_namespace(diagnostic.LOADER_PATH)
        for _ in range(4):
            namespace["_tt_diagnostic_console"]("b15-console", "full original")
        result = diagnostic.verify_private_reports(
            self.session, "phase8-crossover_preflight", [], completed=True)
        self.assertEqual(result["console_instances"], 4)
        (self.session / "diagnostic-witnesses.jsonl").unlink()
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "phase8-crossover_preflight", [], completed=True)

    def test_private_sidecar_rejects_extra_duplicate_partial_or_false_records(self):
        _, text = self.report()
        sidecar = self.session / "diagnostic-witnesses.jsonl"
        original = sidecar.read_bytes()
        variants = (original + original, original[:-1],
                    original.replace(b'"bytes": ', b'"extra": 1, "bytes": '),
                    original.replace(b'"site": "n24-report"',
                                     b'"site": "unlisted"'))
        for raw in variants:
            sidecar.write_bytes(raw)
            with self.assertRaises(ValueError):
                diagnostic.verify_private_reports(
                    self.session, "native-24", [text], completed=True)
        sidecar.write_bytes(original)
        sidecar.chmod(0o644)
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "native-24", [text], completed=True)

    def test_private_sidecar_symlink_never_changes_target(self):
        target = self.root / "target"
        target.write_bytes(b"untouched")
        (self.session / "diagnostic-witnesses.jsonl").symlink_to(target)
        with self.assertRaises(OSError):
            self.report()
        self.assertEqual(target.read_bytes(), b"untouched")
        with self.assertRaises(ValueError):
            diagnostic.verify_private_reports(
                self.session, "native-24", [], completed=False)


if __name__ == "__main__":
    unittest.main()
