#!/usr/bin/env python3
"""Verify the operator bridge preserves and restores the inherited launch."""

import ast
from dataclasses import dataclass
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tracktemplate.presentation.rea_trackwork import (  # noqa: E402
    ReaTrackworkLine, ReaTrackworkScene,
)


def launcher_functions():
    path = ROOT / "TrackTemplate.FCMacro"
    tree = ast.parse(path.read_text())
    body = [node for node in tree.body if isinstance(
        node, (ast.Import, ast.ImportFrom, ast.FunctionDef),
    )]
    namespace = {"__file__": str(path)}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"),
         namespace)
    return namespace


@dataclass(frozen=True)
class HostChoice:
    object_ref: object
    object_name: str
    template_set_id: str
    label: str


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.launch = launcher_functions().get(
            "_launch_workflow_with_rea_editor",
        )
        self.doc = object()
        self.calls = []
        self.controllers = []
        self.attachments = []
        self.stores = []
        self.workflows = []
        self.report = object()
        self.records = ((object(), object()),)
        self.host = types.SimpleNamespace(Name="HostB", TemplateSetID="SET-B")
        self.workflow = object()
        self.scene_factory = None
        self.qt = object()

        class Curve:
            def __init__(inner):
                inner.turnout_manager_button = types.SimpleNamespace(
                    setText=lambda value: setattr(inner, "text", value),
                    setToolTip=lambda value: setattr(inner, "tooltip", value),
                )

        class Manager:
            def __init__(inner):
                inner.doc = self.doc

        self.module = types.SimpleNamespace(
            CurveInputDialog=Curve, TurnoutManagerDialog=Manager,
            dialog_exec=lambda dialog: self.calls.append(dialog) or 23,
            App=types.SimpleNamespace(ActiveDocument=self.doc),
            QtWidgets=self.qt, CROSSOVER_DEFAULT_MINIMUM_RADIUS=600.0,
            turnout_host_objects=lambda doc: [self.host],
            object_string_property=lambda obj, name, default: getattr(
                obj, name, default,
            ),
            turnout_host_label=lambda obj: "Visible host",
        )
        self.original = self.module.dialog_exec
        self.session = types.SimpleNamespace(
            module=self.module, rea_trackwork_workflow=self.make_workflow,
            launch_workflow=lambda: self.module.dialog_exec(self.module.CurveInputDialog()),
        )
        self.modules = {
            "tracktemplate.adapters.freecad.rea_turnout_state": types.SimpleNamespace(
                FreeCADReaTrackworkStore=self.store,
                read_rea_trackwork_objects=lambda doc: self.records,
            ),
            "tracktemplate.presentation.rea_trackwork": types.SimpleNamespace(
                ReaTrackworkLine=ReaTrackworkLine,
                ReaTrackworkScene=ReaTrackworkScene,
                attach_rea_trackwork_view=object(),
                read_rea_trackwork_view=object(),
            ),
            "tracktemplate.ui.rea_trackwork_editor": types.SimpleNamespace(
                ReaHostChoice=HostChoice,
                ReaTrackworkEditorController=self.controller,
                attach_rea_trackwork_panel=self.attach,
            ),
        }

    def store(self, report, **ports):
        value = types.SimpleNamespace(report=report, **ports)
        self.stores.append(value)
        return value

    def make_workflow(self, store, scene_factory):
        self.workflows.append(store)
        self.scene_factory = scene_factory
        return self.workflow

    def controller(self, document, workflow, **ports):
        value = types.SimpleNamespace(document=document, workflow=workflow,
                                      **ports)
        self.controllers.append(value)
        return value

    def attach(self, dialog, controller, qt_widgets, *, minimum_radius_mm):
        self.attachments.append((dialog, controller, qt_widgets,
                                 minimum_radius_mm))
        dialog._tracktemplate_rea_panel = types.SimpleNamespace(
            controller=controller,
        )

    def invoke(self):
        self.assertTrue(callable(self.launch), "Missing source editor launch")
        with patch("importlib.import_module", side_effect=self.modules.__getitem__):
            return self.launch(self.session, self.report)

    def test_operator_launch_forwards_result_and_preserves_classes(self):
        curve_class = self.module.CurveInputDialog
        manager_class = self.module.TurnoutManagerDialog
        curve = curve_class()
        manager = manager_class()
        other = object()

        def launch():
            for dialog in (curve, manager, manager, other):
                self.assertEqual(self.module.dialog_exec(dialog), 23)
            return "accepted"

        self.session.launch_workflow = launch
        self.assertEqual(self.invoke(), "accepted")
        self.assertEqual(self.calls, [curve, manager, manager, other])
        self.assertIn("B/C", curve.text)
        self.assertEqual(len(self.attachments), 1)
        self.assertIs(self.module.dialog_exec, self.original)
        self.assertIs(self.module.CurveInputDialog, curve_class)
        self.assertIs(self.module.TurnoutManagerDialog, manager_class)
        self.assertEqual(len(self.stores), 1)
        store = self.stores[0]
        self.assertIs(store.report, self.report)
        presenter = self.modules["tracktemplate.presentation.rea_trackwork"]
        self.assertIs(store.view_factory, presenter.attach_rea_trackwork_view)
        self.assertIs(store.view_reader, presenter.read_rea_trackwork_view)
        controller = self.controllers[0]
        self.assertIs(controller.document, self.doc)
        self.assertIs(controller.workflow, self.workflow)
        self.assertEqual(controller.read_records(self.doc), self.records)
        choice, = controller.read_hosts(self.doc)
        self.assertIs(choice.object_ref, self.host)
        self.assertEqual((choice.object_name, choice.template_set_id,
                          choice.label), ("HostB", "SET-B", "Visible host"))
        self.assertIs(controller.active_document(), self.doc)
        replacement_doc = object()
        self.module.App.ActiveDocument = replacement_doc
        self.assertIs(controller.active_document(), replacement_doc)
        ids = {controller.new_entity_id() for _ in range(8)}
        self.assertEqual(len(ids), 8)
        self.assertTrue(all(isinstance(value, str) and value for value in ids))
        self.assertEqual(self.attachments[0][2:], (self.qt, 600.0))
        scene = self.scene_factory("REA-1", (
            ("R1", "rails", ((0.0, 1.0, 0.0), (2.0, 3.0, 0.0))),
            ("T1", "timbers", ((4.0, 5.0, 0.0), (6.0, 7.0, 0.0))),
        ))
        self.assertEqual(scene.entity_id, "REA-1")
        self.assertEqual(tuple(line.visual_id for line in scene.lines),
                         ("R1", "T1"))

    def test_dialog_exception_restores_hook(self):
        error = RuntimeError("nested Qt loop failed")

        def fail(dialog):
            raise error

        self.module.dialog_exec = fail
        with self.assertRaises(RuntimeError) as caught:
            self.invoke()
        self.assertIs(caught.exception, error)
        self.assertIs(self.module.dialog_exec, fail)

    def test_panel_construction_failure_restores_and_does_not_execute(self):
        error = ValueError("invalid document")

        def fail(*args, **kwargs):
            raise error

        self.modules["tracktemplate.ui.rea_trackwork_editor"].attach_rea_trackwork_panel = fail
        self.session.launch_workflow = lambda: self.module.dialog_exec(
            self.module.TurnoutManagerDialog(),
        )
        with self.assertRaises(ValueError) as caught:
            self.invoke()
        self.assertIs(caught.exception, error)
        self.assertEqual(self.calls, [])
        self.assertIs(self.module.dialog_exec, self.original)

    def test_recursive_launch_refused_and_original_restored(self):
        self.session.launch_workflow = lambda: self.launch(
            self.session, self.report,
        )
        with self.assertRaisesRegex(RuntimeError, "already active"):
            self.invoke()
        self.assertEqual(len(self.stores), 1)
        self.assertIs(self.module.dialog_exec, self.original)

    def test_binding_conflict_is_visible_and_original_restored(self):
        self.session.launch_workflow = lambda: setattr(
            self.module, "dialog_exec", lambda dialog: 99,
        )
        with self.assertRaisesRegex(RuntimeError, "binding changed"):
            self.invoke()
        self.assertIs(self.module.dialog_exec, self.original)

    def test_other_dialog_subclasses_are_unchanged(self):
        class OtherManager(self.module.TurnoutManagerDialog):
            pass

        dialog = OtherManager()
        self.session.launch_workflow = lambda: self.module.dialog_exec(dialog)
        self.assertEqual(self.invoke(), 23)
        self.assertEqual(self.controllers, [])
        self.assertEqual(self.calls, [dialog])
        self.assertIs(self.module.dialog_exec, self.original)

    def test_real_entry_uses_operator_bridge_only_for_launch(self):
        functions = launcher_functions()
        functions["_launcher_root"] = lambda: ROOT
        functions["_load_foundation"] = lambda root: (
            types.SimpleNamespace(DEVELOPMENT_CHECKPOINT="B16", __all__=()),
            types.SimpleNamespace(require_qualified_runtime=lambda path: {
                "compatibility_evaluation": {"matched_profile_id": "test"},
            }),
        )
        functions["LAUNCH_SENTINEL"] = "test="
        functions["_load_modular_transition_workflow"] = lambda *args: (
            self.session, None,
        )
        calls = []
        functions["_launch_workflow_with_rea_editor"] = lambda *args: calls.append(args)
        functions["run_macro"]()
        self.assertEqual(calls, [])
        functions["run_macro"](True)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], self.session)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CompositionTests),
    )
    if result.wasSuccessful():
        print("REA operator composition checks passed")
    raise SystemExit(not result.wasSuccessful())
