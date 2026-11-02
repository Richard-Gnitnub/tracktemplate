#!/usr/bin/env python3
"""Exercise batched research line presentation without importing Coin or Qt."""

import pathlib
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.presentation.rea_trackwork import (
    REA_TRACKWORK_VIEW_ELEMENT,
    ReaTrackworkLine,
    ReaTrackworkScene,
    ReaTrackworkViewProvider,
)


class Field:
    def setValue(self, *value):
        self.value = value[0] if len(value) == 1 else value

    def setValues(self, start, count, values):
        self.value = tuple(values)

    def getValue(self):
        return self.value


class Node:
    def __init__(self):
        self.children = []
        self.name = ""
        self.whichChild = Field()
        self.whichChild.setValue(0)
        self.point = Field()
        self.numVertices = Field()
        self.rgb = Field()
        self.lineWidth = Field()

    def addChild(self, child):
        self.children.append(child)

    def removeAllChildren(self):
        self.children.clear()

    def replaceChild(self, old, new):
        self.children[self.children.index(old)] = new

    def getNumChildren(self):
        return len(self.children)

    def getChild(self, index):
        return self.children[index]

    def findChild(self, child):
        return self.children.index(child) if child in self.children else -1

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name


def fake_coin():
    return types.SimpleNamespace(
        SoSeparator=Node, SoBaseColor=Node, SoDrawStyle=Node,
        SoCoordinate3=Node, SoLineSet=Node,
        SoType=types.SimpleNamespace(fromName=lambda name:
            types.SimpleNamespace(createInstance=Node)),
    )


class ViewObject:
    def __init__(self):
        self.Proxy = None
        self.Visibility = True
        self.RootNode = Node()
        self.SwitchNode = Node()
        self.RootNode.addChild(self.SwitchNode)
        self.modes = []

    def addDisplayMode(self, node, name):
        self.modes.append(name)
        self.SwitchNode.addChild(node)


def scene():
    return ReaTrackworkScene("source:TO:1", (
        ReaTrackworkLine("rail:first", "rails",
                         ((1., 2., 0.), (2., 3., 0.), (3., 4., 0.))),
        ReaTrackworkLine("timber:T1", "timbers",
                         ((5., 6., 0.), (7., 8., 0.))),
    ))


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.obj = types.SimpleNamespace(ViewObject=ViewObject())
        self.signature = "sha256:" + "1" * 64
        self.view = ReaTrackworkViewProvider(
            self.obj, scene(), self.signature, coin_module=fake_coin(),
        )

    def test_batched_points_preserve_exact_world_order(self):
        binding = self.view.snapshot().binding
        self.assertEqual(binding.coordinates.point.value, (
            (1., 2., 0.), (2., 3., 0.), (3., 4., 0.),
            (5., 6., 0.), (7., 8., 0.),
        ))
        self.assertEqual(binding.line_set.numVertices.value, (3, 2))
        self.assertEqual(self.view.selection_for_element(
            REA_TRACKWORK_VIEW_ELEMENT), "source:TO:1")
        self.assertEqual(self.view.scene.lines[1].visual_id, "timber:T1")
        self.assertEqual(len(self.obj.ViewObject.modes), 1)

    def test_rollback_restores_binding_and_visibility(self):
        previous = self.view.snapshot()
        self.obj.ViewObject.Visibility = False
        replacement = ReaTrackworkScene("source:TO:1", tuple(reversed(
            scene().lines,
        )))
        self.view.replace(replacement, "sha256:" + "2" * 64)
        self.view.restore(previous)
        self.assertEqual(self.view.scene, scene())
        self.assertEqual(self.view.signature, self.signature)
        self.assertTrue(self.obj.ViewObject.Visibility)
        self.assertIs(self.view.snapshot().binding, previous.binding)

    def test_undo_or_external_canonical_change_clears_visible_scene(self):
        self.view.updateData(self.obj, "TrackTemplateReaIntentJSON")
        self.assertIsNone(self.view.scene)
        self.assertEqual(self.view.selection_root.getNumChildren(), 0)
        self.assertTrue(self.view.diagnostic)

    def test_restore_is_empty_and_does_not_need_geometry_or_cached_points(self):
        self.assertIsNone(self.view.dumps())
        restored = object.__new__(ReaTrackworkViewProvider)
        restored.loads(None)
        with patch.dict(sys.modules, {
            "pivy": types.SimpleNamespace(coin=fake_coin()),
        }):
            restored.attach(ViewObject())
        self.assertIsNone(restored.scene)
        self.assertTrue(restored.diagnostic)
        self.assertIsNone(restored.dumps())

    def test_existing_view_reader_preserves_live_binding(self):
        from tracktemplate.presentation.rea_trackwork import (
            read_rea_trackwork_view,
        )
        before = self.view.snapshot()
        self.assertIs(read_rea_trackwork_view(self.obj), self.view)
        self.assertEqual(self.view.snapshot(), before)
        foreign = types.SimpleNamespace(ViewObject=ViewObject())
        foreign.ViewObject.Proxy = self.view
        with self.assertRaisesRegex(ValueError, "different"):
            read_rea_trackwork_view(foreign)
        self.assertEqual(self.view.snapshot(), before)

    def test_existing_view_reader_restores_empty_and_rejects_foreign(self):
        from tracktemplate.presentation.rea_trackwork import (
            read_rea_trackwork_view,
        )
        restored = object.__new__(ReaTrackworkViewProvider)
        restored.loads(None)
        self.obj.ViewObject.Proxy = restored
        with patch.dict(sys.modules, {
            "pivy": types.SimpleNamespace(coin=fake_coin()),
        }):
            self.assertIs(read_rea_trackwork_view(self.obj), restored)
        self.assertIsNone(restored.scene)
        self.assertEqual(restored.selection_root.getNumChildren(), 0)
        self.obj.ViewObject.Proxy = object()
        with self.assertRaisesRegex(ValueError, "foreign"):
            read_rea_trackwork_view(self.obj)
        self.obj.ViewObject.Proxy = None
        self.assertIsNone(read_rea_trackwork_view(self.obj))
        self.assertIsNone(read_rea_trackwork_view(
            types.SimpleNamespace(ViewObject=None),
        ))

    def test_pick_rejects_foreign_path_and_preserves_entity(self):
        pick = types.SimpleNamespace(getPath=lambda: types.SimpleNamespace(
            findNode=lambda node: 0 if node is self.view.selection_root else -1,
        ))
        self.assertEqual(self.view.getElementPicked(pick),
                         REA_TRACKWORK_VIEW_ELEMENT)
        foreign = types.SimpleNamespace(getPath=lambda: types.SimpleNamespace(
            findNode=lambda node: -1,
        ))
        self.assertIsNone(self.view.getElementPicked(foreign))

    def test_no_geometry_or_gui_module_imported_by_scene(self):
        self.assertNotIn("Part", sys.modules)
        self.assertNotIn("FreeCADGui", sys.modules)
        self.assertNotIn("PySide", sys.modules)

    def test_dependency_notification_clears_without_rebuilding(self):
        document = types.SimpleNamespace()
        self.obj.Document = document
        host = types.SimpleNamespace(Document=document, Radius=3000.)
        settings = types.SimpleNamespace(Document=document, Width=32.)
        observers = []
        app = types.SimpleNamespace(
            addDocumentObserver=observers.append,
            removeDocumentObserver=observers.remove,
        )
        observe = getattr(self.view, "observe_dependencies", None)
        if observe is not None:
            observe(self.obj, (host, settings), app_module=app)
        host.Radius = 3100.
        for observer in tuple(observers):
            observer.slotChangedObject(host, "Radius")
        self.assertIsNone(self.view.scene)
        self.assertEqual(self.view.selection_root.getNumChildren(), 0)
        self.assertEqual(len(observers), 1)
        self.view.replace(scene(), self.signature)
        for observer in tuple(observers):
            observer.slotChangedObject(settings, "Width")
        self.assertIsNone(self.view.scene)

    def test_dependency_rollback_restores_watch_and_cleanup_is_exact(self):
        document = types.SimpleNamespace()
        self.obj.Document = document
        first = types.SimpleNamespace(Document=document)
        second = types.SimpleNamespace(Document=document)
        observers = []
        app = types.SimpleNamespace(
            addDocumentObserver=observers.append,
            removeDocumentObserver=observers.remove,
        )
        self.view.observe_dependencies(self.obj, (first,), app_module=app)
        original = self.view.snapshot()
        self.view.observe_dependencies(self.obj, (second,), app_module=app)
        self.view.restore(original)
        self.assertEqual(len(observers), 1)
        observers[0].slotChangedObject(second, "Shape")
        self.assertEqual(self.view.scene, scene())
        observers[0].slotChangedObject(first, "Shape")
        self.assertIsNone(self.view.scene)
        self.assertTrue(self.view.onDelete(self.obj.ViewObject, ()))
        self.assertEqual(observers, [])
        self.assertTrue(self.view.onDelete(self.obj.ViewObject, ()))

    def test_observer_close_and_failed_removal_keep_diagnostic(self):
        document = types.SimpleNamespace()
        self.obj.Document = document
        host = types.SimpleNamespace(Document=document)
        observers = []

        def fail_remove(observer):
            raise RuntimeError("injected observer cleanup failure")

        app = types.SimpleNamespace(
            addDocumentObserver=observers.append,
            removeDocumentObserver=fail_remove,
        )
        self.view.observe_dependencies(self.obj, (host,), app_module=app)
        self.assertTrue(self.view.onDelete(self.obj.ViewObject, ()))
        self.assertIn("observer cleanup failure", self.view.diagnostic)
        self.assertIsNone(self.view.scene)
        app.removeDocumentObserver = observers.remove
        self.assertTrue(self.view.onDelete(self.obj.ViewObject, ()))
        self.assertEqual(observers, [])
        self.view.observe_dependencies(self.obj, (host,), app_module=app)
        self.view.slotDeletedDocument(document)
        self.assertEqual(observers, [])

    def test_partial_observer_registration_cleans_and_clears(self):
        document = types.SimpleNamespace()
        self.obj.Document = document
        host = types.SimpleNamespace(Document=document)
        observers = []

        def fail_add(observer):
            observers.append(observer)
            raise RuntimeError("injected observer registration failure")

        app = types.SimpleNamespace(
            addDocumentObserver=fail_add,
            removeDocumentObserver=observers.remove,
        )
        with self.assertRaises(RuntimeError):
            self.view.observe_dependencies(self.obj, (host,), app_module=app)
        self.assertEqual(observers, [])
        self.assertIsNone(self.view.scene)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PresentationTests)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("REA trackwork presentation standalone validation passed")
