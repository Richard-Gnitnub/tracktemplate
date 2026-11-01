"""Preserve the frozen diagnostic contract with inert host doubles.

These tests execute the hash-pinned historical source. Current product
activation behavior is checked by validate_chair_preview_activation.py.
"""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from types import FunctionType
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import l1_gui_lifecycle_observer as observer  # noqa: E402
from tools.hosted_l1_gui_validation import DIAGNOSTIC_BASE  # noqa: E402


def extract_functions(path, names, namespace):
    """Execute only unchanged Python functions against inert host doubles."""
    tree = ast.parse(path.read_text(), filename=str(path))
    selected = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in selected} != set(names):
        raise AssertionError("Test source selection is incomplete")
    compiled = compile(path.read_bytes(), str(path), "exec")
    codes = {code.co_qualname: code for code in observer._nested_codes(compiled)}
    for node in selected:
        defaults = tuple(ast.literal_eval(value) for value in node.args.defaults)
        function = FunctionType(codes[node.name], namespace, node.name, defaults)
        function.__kwdefaults__ = {
            arg.arg: ast.literal_eval(value)
            for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults)
            if value is not None
        }
        namespace[node.name] = function


class Document:
    def __init__(self, app, name):
        self.app = app
        self.Name = name
        self.FileName = ""
        self.Temporary = False
        self.Objects = []

    def addObject(self, _kind, name):
        self.app.mutations.append("addObject")
        obj = SimpleNamespace(Name=name, Document=self,
                              ViewObject=SimpleNamespace())
        self.Objects.append(obj)
        return obj

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)

    def openTransaction(self, _label):
        self.app.mutations.append("openTransaction")

    def abortTransaction(self):
        self.app.mutations.append("abortTransaction")
        self.Objects.clear()

    def commitTransaction(self):
        self.app.mutations.append("commitTransaction")

    def recompute(self):
        self.app.mutations.append("recompute")
        return True


class Application:
    GuiUp = True

    def __init__(self):
        self.documents = {}
        self.ActiveDocument = None
        self.mutations = []

    def listDocuments(self):
        return dict(self.documents)

    def activeDocument(self):
        return self.ActiveDocument

    def newDocument(self, name, *_args):
        self.mutations.append("newDocument")
        document = Document(self, name)
        self.documents[name] = document
        self.ActiveDocument = document
        return document

    def closeDocument(self, name):
        self.mutations.append("closeDocument")
        removed = self.documents.pop(name)
        if self.ActiveDocument is removed:
            self.ActiveDocument = None
        selection = getattr(self, "selection", None)
        if selection is not None and selection.marker.Document is removed:
            selection.selected = False
            selection.preselected = False

    def setActiveDocument(self, name):
        self.mutations.append("setActiveDocument")
        self.ActiveDocument = self.documents.get(name)


class Selection:
    def __init__(self, app, marker):
        self.app = app
        self.marker = marker
        self.selected = True
        self.preselected = False

    def _item(self, present):
        return SimpleNamespace(
            DocumentName=self.marker.Document.Name if present else "",
            ObjectName=self.marker.Name if present else "",
            Object=self.marker if present else None,
            SubElementNames=("Edge1",) if present else (),
            PickedPoints=(SimpleNamespace(x=1.0, y=2.0, z=3.0),)
            if present else (),
        )

    def getSelectionEx(self, _documents, _resolve):
        return [self._item(True)] if self.selected else []

    def getPreselection(self):
        return self._item(self.preselected)

    def isSelected(self, _obj, _subname, _resolve):
        return self.selected

    def clearSelection(self):
        self.app.mutations.append("clearSelection")
        self.selected = False

    def addSelection(self, *_args):
        self.app.mutations.append("addSelection")
        self.selected = True

    def clearPreselection(self):
        self.app.mutations.append("clearPreselection")
        self.preselected = False

    def setPreselection(self, *_args):
        self.app.mutations.append("setPreselection")
        self.preselected = True


class View:
    def __init__(self, runtime):
        self.runtime = runtime

    def viewAxonometric(self):
        self.runtime.app.mutations.append("viewAxonometric")

    def getCamera(self):
        return "OrthographicCamera { position 1 2 3 height 10 }"

    def fitAll(self):
        runtime = self.runtime
        runtime.app.mutations.append("fitAll")
        if runtime.case != "changed-900":
            return
        if runtime.fail_operand == "active":
            runtime.app.ActiveDocument = runtime.foreign
        elif runtime.fail_operand == "registry":
            runtime.app.documents["Unexpected"] = Document(
                runtime.app, "Unexpected",
            )
        elif runtime.fail_operand == "selection":
            runtime.selection.selected = False
        elif runtime.fail_operand == "preselection":
            runtime.selection.preselected = True


class GuiDocument:
    def __init__(self, document, runtime):
        self.Document = document
        self.view = View(runtime)

    def activeView(self):
        return self.view


class Gui(ModuleType):
    def __init__(self, runtime):
        super().__init__("FreeCADGui")
        self.runtime = runtime
        self.Selection = runtime.selection
        self.documents = {}

    def getDocument(self, name):
        if name not in self.documents:
            self.documents[name] = GuiDocument(
                self.runtime.app.documents[name], self.runtime,
            )
        return self.documents[name]

    def activeDocument(self):
        document = self.runtime.app.ActiveDocument
        return None if document is None else self.getDocument(document.Name)

    @property
    def ActiveDocument(self):
        return self.activeDocument()


class Runtime:
    """Run the unchanged lifecycle function, with no FreeCAD import."""

    def __init__(self, fail_operand=None, *, source_root=ROOT):
        self.fail_operand = fail_operand
        self.case = None
        self.caught = None
        self.app = Application()
        self.source = self.app.newDocument("Source")
        self.foreign = self.app.newDocument("Unrelated")
        marker = self.foreign.addObject("Feature", "Keep")
        self.selection = Selection(self.app, marker)
        self.app.selection = self.selection
        self.gui = Gui(self)
        namespace = {"App": self.app, "uuid": uuid}
        core = source_root / (
            "tracktemplate/adapters/freecad/core_export_document.py"
        )
        names = ("_active_document", "_same_registry", "_selection_snapshot",
                 "_preselection_snapshot", "_restore_selection",
                 "_restore_preselection", "_cleanup")
        extract_functions(core, names, namespace)
        target = source_root / (
            "tracktemplate/adapters/freecad/chair_reference_preview.py"
        )
        extract_functions(target, ("_require", "_materialise_preview"),
                          namespace)
        self.preview = namespace["_materialise_preview"]
        self.codes = {
            "test": self.test_authorised_gui_stage.__code__,
            "journey": self._journey.__code__,
            "target": self.preview.__code__,
            "require": namespace["_require"].__code__,
            **{key: namespace[name].__code__ for key, name in (
                ("active", "_active_document"),
                ("registry", "_same_registry"),
                ("selection", "_selection_snapshot"),
                ("preselection", "_preselection_snapshot"),
            )},
        }

    def test_authorised_gui_stage(self):
        app = self.app
        gui = self.gui
        receipt = {"status": "RUNNING"}
        try:
            self._journey()
            receipt["status"] = "PASS"
        except BaseException as error:
            self.caught = error
            receipt["status"] = "FAIL"
            raise
        finally:
            for name in tuple(app.documents):
                app.closeDocument(name)
            assert gui.activeDocument() is None

    def _journey(self):
        for label, radius in (("reference-600", 600.0),
                              ("changed-900", 900.0),
                              ("returned-600", 600.0)):
            self.case = label
            self.app.setActiveDocument(self.foreign.Name)
            layers = (SimpleNamespace(Solids=[True]),)
            self.preview(
                "L1", {}, (("Layer", "Reference", (0.5, 0.5, 0.5)),),
                lambda: (layers, {}, lambda _shapes: None), lambda: None,
            )


class LifecycleObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory(prefix="l1-original-source-")
        cls.addClassCleanup(directory.cleanup)
        cls.historical_root = Path(directory.name)
        for name, digest in observer.SOURCE_HASHES.items():
            source = subprocess.run(
                ["git", "show", f"{DIAGNOSTIC_BASE}:{name}"], cwd=ROOT,
                capture_output=True, check=True,
            ).stdout
            if hashlib.sha256(source).hexdigest() != digest:
                raise AssertionError("Historical diagnostic source differs")
            target = cls.historical_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source)

    def run_observed(self, directory, failure=None, break_snapshot=False):
        runtime = Runtime(failure, source_root=self.historical_root)
        capture = observer._Observer(Path(directory), runtime.codes)
        original_snapshot = capture._snapshot

        def snapshot(frame, phase):
            if break_snapshot and phase == "pre_guard":
                raise OSError("synthetic capture fault")
            return original_snapshot(frame, phase)

        capture._snapshot = snapshot
        with patch.dict(sys.modules, {"FreeCADGui": runtime.gui}):
            capture.start()
            if failure:
                with self.assertRaisesRegex(RuntimeError, "preview changed"):
                    runtime.test_authorised_gui_stage()
            else:
                runtime.test_authorised_gui_stage()
        self.assertIsNone(sys.gettrace())
        self.assertFalse(runtime.app.documents)
        report = json.loads((Path(directory) / observer.REPORT).read_text())
        events = [json.loads(line) for line in
                  (Path(directory) / observer.EVENTS).read_text().splitlines()]
        return runtime, report, events

    def test_import_is_inert_and_source_binding_uses_no_host_import(self):
        script = (
            "import runpy, sys\n"
            f"m = runpy.run_path({str(ROOT / 'tools/l1_gui_lifecycle_observer.py')!r})\n"
            f"m['_source_codes'](m['Path']({str(self.historical_root)!r}))\n"
            "assert sys.gettrace() is None\n"
            "assert not any(n.startswith(('FreeCAD', 'Part', 'PySide')) "
            "for n in sys.modules)\n"
        )
        result = subprocess.run([sys.executable, "-c", script],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fixed_sources_and_code_binding_match_original_bytes(self):
        codes = observer._source_codes(self.historical_root)
        self.assertEqual(set(codes), {"test", "journey", "target", "require",
                                     "active", "registry", "selection",
                                     "preselection"})
        self.assertEqual(codes["target"].co_firstlineno, 336)
        for name, expected in observer.SOURCE_HASHES.items():
            source = (self.historical_root / name).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), expected)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises((OSError, ValueError)):
                observer._source_codes(Path(directory))

    def test_install_rejects_mismatch_existing_trace_and_unsafe_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch.object(observer, "ROOT", target):
                with self.assertRaises((OSError, ValueError)):
                    observer.install(target)
            self.assertEqual(list(target.iterdir()), [])
            with self.assertRaisesRegex(ValueError, "source identity differs"):
                observer.install(target)
            self.assertEqual(list(target.iterdir()), [])
            with patch.object(sys, "gettrace", return_value=lambda *_: None):
                with self.assertRaisesRegex(ValueError, "trace"):
                    observer.install(target)
            (target / observer.EVENTS).write_text("preserved")
            with patch.object(observer, "ROOT", self.historical_root):
                with self.assertRaises(FileExistsError):
                    observer.install(target)
            self.assertEqual((target / observer.EVENTS).read_text(), "preserved")
            link = target / "linked"
            link.symlink_to(target, target_is_directory=True)
            with patch.object(observer, "ROOT", self.historical_root):
                with self.assertRaises(ValueError):
                    observer.install(link)
        self.assertIsNone(sys.gettrace())

    def test_actual_short_circuit_and_cleanup_preserve_original_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, report, events = self.run_observed(directory, "active")
            self.assertEqual(report["status"], "COMPLETE")
            self.assertTrue(report["observed_failure"])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["original_test_exception"]["type"],
                             type(runtime.caught).__name__)
            guards = [row for row in events if row["event"] == "guard_evaluated"]
            self.assertEqual(guards[-1]["case"], "changed-900")
            self.assertEqual(guards[-1]["radius_mm"], 900.0)
            self.assertEqual(guards[-1]["predicates"], {
                "active": False, "registry": "NOT_EVALUATED",
                "selection": "NOT_EVALUATED", "preselection": "NOT_EVALUATED",
            })
            active_return = [row for row in events
                             if row["event"] == "helper_return"
                             and row["predicate"] == "active"][-1]
            self.assertEqual(active_return["observed"]["name"], "Unrelated")
            self.assertTrue(active_return["expected"]["name"].startswith(
                "TrackTemplateL1Reference_",
            ))
            phases = [row["event"] for row in events]
            self.assertLess(phases.index("product_exception"),
                            phases.index("after_cleanup"))
            cleanup = next(row for row in events if row["event"] == "after_cleanup")
            self.assertTrue(all(cleanup["state"]["sampled_predicates"].values()))
            self.assertEqual(cleanup["cleanup_errors"], [])
            finished = events[-1]
            self.assertEqual(finished["event"], "test_finished")
            self.assertEqual(finished["state"]["registry"], [])
            self.assertEqual(finished["state"]["selection"], [])
            self.assertIsNone(finished["state"]["app_active_method"])
            self.assertIsNone(finished["state"]["app_active_attribute"])
            self.assertIsNone(finished["state"]["preselection"])
            self.assertIn("OrthographicCamera", events[1]["state"]["gui"]
                          ["method_camera"])
            times = [row["elapsed_seconds"] for row in events]
            self.assertEqual(times, sorted(times))
            assessed = observer.assess(directory)
            self.assertEqual(assessed["status"], "COMPLETE")
            self.assertEqual(assessed["event_count"], len(events))
            self.assertTrue(assessed["trace_restored"])

    def test_each_guard_operand_has_distinct_actual_and_sampled_evidence(self):
        for operand in ("registry", "selection", "preselection"):
            with self.subTest(operand=operand), tempfile.TemporaryDirectory() as directory:
                _runtime, report, events = self.run_observed(directory, operand)
                self.assertEqual(report["status"], "COMPLETE")
                guard = [row for row in events
                         if row["event"] == "guard_evaluated"][-1]
                self.assertFalse(guard["predicates"][operand])
                returned = [row for row in events
                            if row["event"] == "helper_return"
                            and row["predicate"] == operand][-1]
                self.assertNotEqual(returned["observed"], returned["expected"])
                if operand == "registry":
                    self.assertIn("Unexpected", [row["name"]
                                                 for row in returned["observed"]])
                elif operand == "selection":
                    self.assertEqual(returned["observed"], [])
                    self.assertEqual(returned["expected"][0]["object"]["name"],
                                     "Keep")
                else:
                    self.assertEqual(returned["observed"]["point"], [1, 2, 3])
                    self.assertIsNone(returned["expected"])
                pre = [row for row in events if row["event"] == "pre_guard"][-1]
                self.assertFalse(pre["state"]["sampled_predicates"][operand])
                if operand == "selection":
                    self.assertEqual(guard["predicates"]["preselection"],
                                     "NOT_EVALUATED")

    def test_success_keeps_all_three_cases_without_qualification(self):
        with tempfile.TemporaryDirectory() as directory:
            _runtime, report, events = self.run_observed(directory)
            self.assertEqual(report["status"], "COMPLETE")
            self.assertFalse(report["observed_failure"])
            self.assertIsNone(report["original_test_exception"])
            self.assertEqual([row["case"] for row in events
                              if row["event"] == "entry"],
                             ["reference-600", "changed-900", "returned-600"])
            self.assertNotIn("PASS", report.values())

    def test_capture_error_does_not_replace_failure_or_interrupt_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime, report, _events = self.run_observed(
                directory, "active", break_snapshot=True,
            )
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertTrue(report["errors"])
            self.assertIn("preview changed", str(runtime.caught))
            self.assertEqual(report["original_test_exception"]["type"],
                             "RuntimeError")
            self.assertTrue(report["trace_restored"])
            self.assertIn("abortTransaction", runtime.app.mutations)
            self.assertEqual(observer.assess(directory)["status"], "INCOMPLETE")

    def test_observation_adds_no_host_mutators(self):
        for failure in (None, "active", "selection"):
            baseline = Runtime(failure, source_root=self.historical_root)
            with patch.dict(sys.modules, {"FreeCADGui": baseline.gui}):
                try:
                    baseline.test_authorised_gui_stage()
                except RuntimeError:
                    if failure is None:
                        raise
            with tempfile.TemporaryDirectory() as directory:
                observed, _report, _events = self.run_observed(directory, failure)
            self.assertEqual(observed.app.mutations, baseline.app.mutations)

    def test_event_limit_and_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(observer, "MAX_EVENTS", 3):
                _runtime, report, events = self.run_observed(directory)
            self.assertLessEqual(len(events), 3)
            self.assertEqual(report["status"], "INCOMPLETE")
        with tempfile.TemporaryDirectory() as directory:
            self.run_observed(directory)
            events = Path(directory) / observer.EVENTS
            events.write_text(events.read_text() + "{}\n")
            self.assertEqual(observer.assess(directory)["status"], "INCOMPLETE")
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(observer.assess(directory)["status"], "INCOMPLETE")

    def test_naturally_executed_code_must_equal_the_compiled_fixed_source(self):
        runtime = Runtime(source_root=self.historical_root)
        fixed = observer._source_codes(self.historical_root)
        for name in ("target", "require", "active", "registry", "selection",
                     "preselection"):
            self.assertEqual(runtime.codes[name], fixed[name])
        runtime.codes["target"] = runtime.codes["target"].replace(
            co_name="_materialise_preview", co_consts=(
                "different executable code", *runtime.codes["target"].co_consts[1:],
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            capture = observer._Observer(Path(directory), runtime.codes)
            with patch.dict(sys.modules, {"FreeCADGui": runtime.gui}):
                capture.start()
                runtime.test_authorised_gui_stage()
            report = json.loads((Path(directory) / observer.REPORT).read_text())
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertTrue(any("code differs" in row["message"]
                                for row in report["errors"]))
            self.assertIsNone(sys.gettrace())


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.wasSuccessful() and result.testsRun == 10 and not result.skipped:
        print("L1 lifecycle observer standalone validation passed", flush=True)
    else:
        raise SystemExit(1)
