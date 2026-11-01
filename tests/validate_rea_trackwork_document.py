#!/usr/bin/env python3
"""Check the REA logical-object transaction boundary with lightweight fakes."""

from copy import copy
from dataclasses import replace
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.adapters.freecad import rea_turnout_state as adapter
from tools.modular_structure import structure_report
from tracktemplate.application import rea_turnout_state as state
from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification
from tracktemplate.presentation.rea_trackwork import (
    ReaTrackworkLine,
    ReaTrackworkScene,
)


class FakeObject:
    def __init__(self, document, name, type_id="App::FeaturePython"):
        self.Document = document
        self.Name = name
        self.TypeId = type_id
        self.Label = name
        self.Proxy = None
        self.PropertiesList = []
        self.types = {}
        self.ViewObject = types.SimpleNamespace(Visibility=True, Proxy=None)

    def addProperty(self, type_id, name, group, description):
        self.PropertiesList.append(name)
        self.types[name] = type_id
        setattr(self, name, None)

    def getTypeIdOfProperty(self, name):
        return self.types[name]

    def setEditorMode(self, name, mode):
        pass


class FakeDocument:
    def __init__(self):
        self.Name = "ReaDocument"
        self.Objects = []
        self.UndoMode = 1
        self.commits = 0
        self.opens = 0
        self.fail_commit = False
        self.collision = False

    def addObject(self, type_id, name):
        obj = FakeObject(self, name, type_id)
        if self.collision:
            obj.addProperty("App::PropertyString",
                            adapter.REA_INTENT_JSON_PROPERTY, "", "")
        self.Objects.append(obj)
        return obj

    def openTransaction(self, name):
        self.opens += 1
        self.before = [(obj, copy(obj.__dict__)) for obj in self.Objects]

    def commitTransaction(self):
        if self.fail_commit:
            raise RuntimeError("injected commit failure")
        self.commits += 1

    def abortTransaction(self):
        self.Objects[:] = [obj for obj, _fields in self.before]
        for obj, fields in self.before:
            obj.__dict__.clear()
            obj.__dict__.update(fields)


class FakeView:
    def __init__(self, obj, scene, signature):
        self.obj = obj
        self.scene = scene
        self.signature = signature
        self.diagnostic = ""
        self.fail_replace = False
        self.disposed = False
        self.dependencies = ()

    def snapshot(self):
        return self.scene, self.signature, self.diagnostic, self.dependencies

    def replace(self, scene, signature):
        self.scene = scene
        self.signature = signature
        if self.fail_replace:
            raise RuntimeError("injected view failure")
        self.diagnostic = ""

    def restore(self, snapshot):
        (self.scene, self.signature, self.diagnostic,
         self.dependencies) = snapshot

    def observe_dependencies(self, obj, dependencies):
        self.dependencies = tuple(dependencies)

    def invalidate(self, diagnostic):
        self.scene = None
        self.diagnostic = diagnostic

    def dispose(self):
        self.disposed = True
        self.scene = None


def intent(**changes):
    values = dict(
        entity_id="research:TO:1", entity_kind="turnout",
        template_set_id="set:1", host_names=("HostA",),
        source_specification=ReaTurnoutSpecification("B", 8.0),
        reference_chainage_mm=100.0, handing="Left-hand",
        orientation="Facing in host travel direction",
    )
    values.update(changes)
    return state.ReaTrackworkIntent(**values)


def scene(entity_id="research:TO:1", offset=0.0):
    return ReaTrackworkScene(entity_id, (
        ReaTrackworkLine("rail:stock", "rails", (
            (offset, 0.0, 0.0), (offset + 1.0, 0.0, 0.0),
        )),
        ReaTrackworkLine("timber:T1", "timbers", (
            (offset, 1.0, 0.0), (offset + 1.0, 1.0, 0.0),
        )),
    ))


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.doc = FakeDocument()
        self.host = self.doc.addObject("PartDesign::Feature", "HostA")
        self.host.TemplateSetID = "set:1"
        self.previous_app = sys.modules.get("FreeCAD")
        sys.modules["FreeCAD"] = types.SimpleNamespace(
            getDocument=lambda name: self.doc if name == self.doc.Name else None,
            Version=lambda: (1, 1, 4), GuiUp=False,
        )
        self.store = adapter.FreeCADReaTrackworkStore({
            "compatibility_evaluation": {
                "status": "qualified", "matched_profile_id": "test-fake",
            },
            "runtime": {"freecad": {
                "available": True, "version_info": [1, 1, 4],
            }},
        }, view_factory=FakeView)
        self.signature = "sha256:" + "1" * 64

    def tearDown(self):
        if self.previous_app is None:
            sys.modules.pop("FreeCAD", None)
        else:
            sys.modules["FreeCAD"] = self.previous_app

    def create(self):
        return self.store.create(
            self.doc, intent(), scene(), self.signature,
            hosts=(self.host,), current_signature=lambda: self.signature,
        )

    def test_create_read_noop_and_exact_edit(self):
        obj = self.create()
        self.assertEqual(len(self.doc.Objects), 2)
        self.assertEqual(obj.TypeId, "App::FeaturePython")
        self.assertIsNone(obj.Proxy)
        self.assertEqual(adapter.read_rea_trackwork_object(obj), intent())
        original_name = obj.Name
        self.store.update(
            self.doc, obj, intent(), scene(), self.signature,
            hosts=(self.host,), current_signature=lambda: self.signature,
        )
        self.assertEqual(self.doc.commits, 1)
        replacement = replace(intent(), reference_chainage_mm=101.0)
        self.store.update(
            self.doc, obj, replacement, scene(offset=1), self.signature,
            hosts=(self.host,), current_signature=lambda: self.signature,
        )
        self.assertEqual(adapter.read_rea_trackwork_object(obj), replacement)
        self.assertEqual(obj.Name, original_name)
        self.assertEqual(self.doc.commits, 2)

    def test_currentness_is_checked_again_before_commit(self):
        answers = iter((self.signature, "sha256:" + "2" * 64))
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.store.create(
                self.doc, intent(), scene(), self.signature,
                hosts=(self.host,), current_signature=lambda: next(answers),
            )
        self.assertEqual(self.doc.Objects, [self.host])
        self.assertEqual(self.doc.commits, 0)

    def test_failed_edit_restores_exact_bytes_and_view(self):
        obj = self.create()
        before = getattr(obj, adapter.REA_INTENT_JSON_PROPERTY)
        view = self.store.view_for(obj)
        snapshot = view.snapshot()
        view.fail_replace = True
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.store.update(
                self.doc, obj, replace(intent(), reference_chainage_mm=101.0),
                scene(offset=1), self.signature, hosts=(self.host,),
                current_signature=lambda: self.signature,
            )
        self.assertEqual(getattr(obj, adapter.REA_INTENT_JSON_PROPERTY), before)
        self.assertEqual(view.snapshot(), snapshot)
        self.assertEqual(self.doc.commits, 1)

    def test_commit_failure_and_collision_leave_no_object(self):
        for failure in ("fail_commit", "collision"):
            setattr(self.doc, failure, True)
            with self.assertRaises(adapter.ReaTrackworkDocumentError):
                self.create()
            self.assertEqual(self.doc.Objects, [self.host])
            setattr(self.doc, failure, False)

    def test_create_failure_disposes_view_before_object_is_removed(self):
        disposed = []

        class LiveView(FakeView):
            def dispose(self):
                if self.obj not in self.obj.Document.Objects:
                    raise RuntimeError("ViewObject has already been removed")
                disposed.append(self.obj.Name)
                super().dispose()

        self.store._view_factory = LiveView
        self.doc.fail_commit = True
        with self.assertRaises(adapter.ReaTrackworkDocumentError) as caught:
            self.create()
        self.assertEqual(caught.exception.code, "transaction-failed")
        self.assertEqual(len(disposed), 1)
        self.assertEqual(self.doc.Objects, [self.host])

    def test_generated_label_updates_and_custom_label_is_preserved(self):
        obj = self.create()
        changed = replace(intent(), source_specification=
                          ReaTurnoutSpecification("C", 10.0))
        self.store.update(
            self.doc, obj, changed, scene(), self.signature,
            hosts=(self.host,), current_signature=lambda: self.signature,
        )
        self.assertEqual(obj.Label, "REA C 1:10 turnout (research)")
        obj.Label = "Operator label"
        self.store.update(
            self.doc, obj, intent(), scene(), self.signature,
            hosts=(self.host,), current_signature=lambda: self.signature,
        )
        self.assertEqual(obj.Label, "Operator label")

    def test_commit_failure_restores_previous_display_dependencies(self):
        obj = self.create()
        settings = self.doc.addObject("App::FeaturePython", "Settings")
        self.doc.fail_commit = True
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.store.update(
                self.doc, obj, replace(intent(), reference_chainage_mm=101.),
                scene(offset=1), self.signature, hosts=(self.host,),
                dependencies=(self.host, settings),
                current_signature=lambda: self.signature,
            )
        self.assertEqual(self.store.view_for(obj).dependencies, (self.host,))
        self.assertEqual(adapter.read_rea_trackwork_object(obj), intent())

    def test_corrupt_restore_remains_inspectable_and_clears_view(self):
        obj = self.create()
        setattr(obj, adapter.REA_INTENT_JSON_PROPERTY, '{"schema_version":99}')
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.store.rebuild(
                obj, scene(), self.signature,
                current_signature=lambda: self.signature,
            )
        self.assertEqual(getattr(obj, adapter.REA_INTENT_JSON_PROPERTY),
                         '{"schema_version":99}')
        self.assertIsNone(self.store.view_for(obj).scene)

    def test_host_links_duplicate_ids_and_identity_changes_refused(self):
        obj = self.create()
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.create()
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            self.store.update(
                self.doc, obj, intent(entity_id="other"), scene("other"),
                self.signature, hosts=(self.host,),
                current_signature=lambda: self.signature,
            )
        setattr(obj, adapter.REA_HOSTS_PROPERTY, [])
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            adapter.read_rea_trackwork_object(obj)

    def test_unknown_or_partial_source_markers_cannot_disappear(self):
        obj = self.create()
        setattr(obj, adapter.REA_RECORD_TYPE_PROPERTY, "unknown-future-record")
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            adapter.read_rea_trackwork_objects(self.doc)
        self.assertEqual(getattr(obj, adapter.REA_RECORD_TYPE_PROPERTY),
                         "unknown-future-record")
        obj.PropertiesList[:] = [adapter.REA_HOSTS_PROPERTY]
        with self.assertRaises(adapter.ReaTrackworkDocumentError):
            adapter.read_rea_trackwork_objects(self.doc)

    def test_stale_view_clear_and_rebuild_without_history(self):
        obj = self.create()
        self.store.check_view(obj, lambda: "sha256:" + "2" * 64)
        self.assertIsNone(self.store.view_for(obj).scene)
        self.store.rebuild(
            obj, scene(), self.signature,
            current_signature=lambda: self.signature,
        )
        self.assertEqual(self.store.view_for(obj).scene, scene())
        self.assertEqual(self.doc.commits, 1)
        self.store.detach_view(obj)
        self.assertIsNone(self.store.view_for(obj))
        self.assertEqual(adapter.read_rea_trackwork_object(obj), intent())

    def test_scene_rejects_nonfinite_and_duplicate_ids(self):
        with self.assertRaises(ValueError):
            ReaTrackworkLine("r", "rails", ((0., 0., 0.), (float("nan"), 0., 0.)))
        with self.assertRaises(ValueError):
            ReaTrackworkScene("x", (scene().lines[0], scene().lines[0]))

    def test_adapter_keeps_existing_dependency_direction(self):
        report = structure_report(ROOT)
        self.assertFalse([
            edge for edge in report["prohibited_layer_edges"]
            if edge["from"] == "tracktemplate.adapters.freecad.rea_turnout_state"
        ])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(DocumentTests)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("REA trackwork document standalone validation passed")
