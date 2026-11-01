"""Check current preview activation and rollback with inert host doubles.

The view double models the preserved active-document change during view
setup. It does not establish which callback caused the hosted L1 failure.
"""

from pathlib import Path
import sys
from types import ModuleType
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_l1_gui_lifecycle_observer import (  # noqa: E402
    Application,
    Document,
    Selection,
    extract_functions,
)


class PreviewRuntime:
    """Bind current product functions while replacing only the host boundary."""

    def __init__(self, *, gui=True, effect=None, activation=None):
        self.app = Application()
        self.app.GuiUp = gui
        self.source = self.app.newDocument("Source")
        self.witness = self.app.newDocument("Witness")
        self.marker = self.witness.addObject("Part::Feature", "Keep")
        self.selection = Selection(self.app, self.marker)
        self.app.selection = self.selection
        self.app.setActiveDocument(self.source.Name)
        self.baseline = dict(self.app.documents)
        self.initial_objects = tuple(self.witness.Objects)
        self.fitted = False
        self.created = None
        self.source_checks = 0
        self.layer_checks = 0
        self.original_error = RuntimeError("final activation failed")
        original_activation = self.app.setActiveDocument

        def activate(name):
            if self.fitted and name.startswith("TrackTemplate"):
                if activation == "raise":
                    raise self.original_error
                if activation == "ignore":
                    return
                if activation == "clear_selection":
                    self.selection.selected = False
            original_activation(name)

        self.app.setActiveDocument = activate

        def fit_all():
            self.fitted = True
            if effect:
                self.app.ActiveDocument = self.witness
            if effect == "selection":
                self.selection.selected = False
            elif effect == "preselection":
                self.selection.preselected = not self.selection.preselected
            elif effect == "registry":
                self.app.documents["Unexpected"] = Document(
                    self.app, "Unexpected",
                )

        self.view = SimpleNamespace(viewAxonometric=lambda: None,
                                    fitAll=fit_all)
        self.gui = ModuleType("FreeCADGui")
        self.gui.Selection = self.selection
        self.gui.getDocument = lambda _name: SimpleNamespace(
            activeView=lambda: self.view,
        )
        namespace = {"App": self.app, "uuid": uuid}
        extract_functions(
            ROOT / "tracktemplate/adapters/freecad/core_export_document.py",
            ("_active_document", "_same_registry", "_selection_snapshot",
             "_preselection_snapshot", "_restore_selection",
             "_restore_preselection", "_cleanup"), namespace,
        )
        extract_functions(
            ROOT / "tracktemplate/adapters/freecad/chair_reference_preview.py",
            ("_require", "_materialise_preview"), namespace,
        )
        self.preview = namespace["_materialise_preview"]
        self.namespace = namespace

    def snapshots(self):
        gui = self.gui if self.app.GuiUp else None
        return tuple(self.namespace[name](self.app, gui) for name in (
            "_selection_snapshot", "_preselection_snapshot",
        ))

    def run(self, source_error=None):
        shape = SimpleNamespace(Solids=[True])

        def verify_layers(shapes):
            if shapes != (shape,):
                raise AssertionError("Prepared shape identity changed")
            self.layer_checks += 1
            self.created = self.app.ActiveDocument

        def verify_source():
            self.source_checks += 1
            if self.app.ActiveDocument is not self.created:
                raise AssertionError("Source check ran with wrong preview")
            if source_error is not None:
                raise source_error

        with patch.dict(sys.modules, {
                "FreeCADGui": self.gui if self.app.GuiUp else None}):
            return self.preview(
                "L1", {}, (("Layer", "Reference", (0.5, 0.5, 0.5)),),
                lambda: ((shape,), {}, verify_layers), verify_source,
            )


class ChairPreviewActivationTests(unittest.TestCase):
    def assert_preserved(self, runtime, before):
        self.assertIs(runtime.app.documents["Source"], runtime.source)
        self.assertIs(runtime.app.documents["Witness"], runtime.witness)
        self.assertEqual(tuple(runtime.witness.Objects), runtime.initial_objects)
        self.assertEqual(runtime.snapshots(), before)

    def assert_rolled_back(self, runtime, before, *, extra_document=False):
        self.assert_preserved(runtime, before)
        self.assertIs(runtime.app.ActiveDocument, runtime.source)
        expected = {"Source", "Witness"}
        if extra_document:
            expected.add("Unexpected")
        self.assertEqual(set(runtime.app.documents), expected)
        self.assertNotIn(runtime.created, runtime.app.documents.values())
        self.assertIn("abortTransaction", runtime.app.mutations)
        self.assertNotIn("commitTransaction", runtime.app.mutations)

    def test_preview_is_active_after_view_changes_it(self):
        for preselected in (False, True):
            with self.subTest(preselected=preselected):
                runtime = PreviewRuntime(effect="active")
                runtime.selection.preselected = preselected
                before = runtime.snapshots()
                result = runtime.run()
                preview = runtime.app.documents[result["document_name"]]
                self.assertIs(runtime.app.ActiveDocument, preview)
                self.assert_preserved(runtime, before)
                self.assertEqual(runtime.source_checks, 1)
                self.assertEqual(runtime.layer_checks, 1)
                self.assertIn("commitTransaction", runtime.app.mutations)
                self.assertNotIn("abortTransaction", runtime.app.mutations)

    def test_ordinary_gui_preview_preserves_nonempty_state(self):
        runtime = PreviewRuntime()
        runtime.selection.preselected = True
        before = runtime.snapshots()
        result = runtime.run()
        self.assertIs(runtime.app.ActiveDocument,
                      runtime.app.documents[result["document_name"]])
        self.assert_preserved(runtime, before)
        self.assertEqual(runtime.source_checks, 1)

    def test_activation_does_not_mask_other_guard_failures(self):
        for effect in ("selection", "preselection", "registry"):
            with self.subTest(effect=effect):
                runtime = PreviewRuntime(effect=effect)
                runtime.selection.preselected = True
                before = runtime.snapshots()
                with self.assertRaisesRegex(RuntimeError, "preview changed"):
                    runtime.run()
                self.assert_rolled_back(runtime, before,
                                        extra_document=effect == "registry")
                self.assertEqual(runtime.source_checks, 0)

    def test_final_activation_exception_survives_rollback(self):
        runtime = PreviewRuntime(effect="active", activation="raise")
        before = runtime.snapshots()
        with self.assertRaises(RuntimeError) as caught:
            runtime.run()
        self.assertIs(caught.exception, runtime.original_error)
        self.assert_rolled_back(runtime, before)
        self.assertEqual(runtime.source_checks, 0)

    def test_ineffective_final_activation_remains_a_failure(self):
        runtime = PreviewRuntime(effect="active", activation="ignore")
        before = runtime.snapshots()
        with self.assertRaisesRegex(RuntimeError, "preview changed"):
            runtime.run()
        self.assert_rolled_back(runtime, before)

    def test_selection_change_during_final_activation_is_rejected(self):
        runtime = PreviewRuntime(activation="clear_selection")
        before = runtime.snapshots()
        with self.assertRaisesRegex(RuntimeError, "preview changed"):
            runtime.run()
        self.assert_rolled_back(runtime, before)
        self.assertEqual(runtime.source_checks, 0)

    def test_late_source_verification_failure_still_rolls_back(self):
        runtime = PreviewRuntime()
        runtime.selection.preselected = True
        before = runtime.snapshots()
        original = RuntimeError("source changed before commit")
        with self.assertRaises(RuntimeError) as caught:
            runtime.run(source_error=original)
        self.assertIs(caught.exception, original)
        self.assert_rolled_back(runtime, before)
        self.assertEqual(runtime.source_checks, 1)

    def test_headless_preview_uses_no_gui_and_retains_commit_contract(self):
        runtime = PreviewRuntime(gui=False, effect="active", activation="raise")
        before = runtime.snapshots()
        result = runtime.run()
        self.assertFalse(runtime.fitted)
        self.assertIs(runtime.app.ActiveDocument,
                      runtime.app.documents[result["document_name"]])
        self.assert_preserved(runtime, before)
        self.assertEqual(runtime.source_checks, 1)
        self.assertIn("commitTransaction", runtime.app.mutations)
        self.assertNotIn("abortTransaction", runtime.app.mutations)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.wasSuccessful() and result.testsRun == 8 and not result.skipped:
        print("Chair preview activation standalone validation passed", flush=True)
    else:
        raise SystemExit(1)
