#!/usr/bin/env python3
"""Exercise REA editor signals and actual commands with lightweight hosts."""

from dataclasses import replace
import importlib
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.adapters.freecad.rea_turnout_state import (
    read_rea_trackwork_objects,
)
from tracktemplate.application.rea_turnout_state import (
    REA_INTENT_JSON_PROPERTY,
    rea_trackwork_intent_to_json,
)
from tracktemplate.ui import rea_trackwork_editor as editor
from validate_rea_trackwork_workflow import WorkflowTests


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


class Widget:
    def __init__(self, *args):
        self.enabled = True
        self.visible = True
        self.object_name = ""

    def setObjectName(self, name):
        self.object_name = name

    def setEnabled(self, enabled):
        self.enabled = enabled

    def setVisible(self, visible):
        self.visible = visible

    def setWordWrap(self, value):
        pass


class Text(Widget):
    def __init__(self, text="", *args):
        super().__init__()
        self.value = text
        self.clicked = Signal()

    def text(self):
        return self.value

    def setText(self, text):
        self.value = text


class Combo(Widget):
    def __init__(self, *args):
        super().__init__()
        self.items = []
        self.index = -1
        self.currentIndexChanged = Signal()
        self.blocked = False

    def addItem(self, label, data=None):
        self.items.append((label, data))
        if self.index < 0:
            self.index = 0

    def addItems(self, labels):
        for label in labels:
            self.addItem(label)

    def clear(self):
        self.items.clear()
        self.index = -1

    def currentData(self):
        return self.items[self.index][1] if self.index >= 0 else None

    def currentText(self):
        return self.items[self.index][0] if self.index >= 0 else ""

    def findData(self, data):
        return next((i for i, item in enumerate(self.items)
                     if item[1] == data), -1)

    def findText(self, text):
        return next((i for i, item in enumerate(self.items)
                     if item[0] == text), -1)

    def setCurrentIndex(self, index):
        self.index = index
        if not self.blocked:
            self.currentIndexChanged.emit(index)

    def blockSignals(self, blocked):
        previous = self.blocked
        self.blocked = blocked
        return previous


class Layout:
    def __init__(self, *args):
        self.items = []

    def addWidget(self, widget):
        self.items.append(widget)

    def addLayout(self, layout):
        self.items.append(layout)


class Scroll(Widget):
    def setWidgetResizable(self, value):
        pass

    def setWidget(self, widget):
        self.widget = widget


def qt_widgets():
    return types.SimpleNamespace(
        QWidget=Widget, QScrollArea=Scroll, QVBoxLayout=Layout,
        QHBoxLayout=Layout, QLabel=Text, QLineEdit=Text,
        QPushButton=Text, QComboBox=Combo,
    )


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkflowTests()
        self.fixture.setUpClass()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.doc = self.fixture.doc
        self.active = self.doc
        self.next_id = 0
        self.controller = editor.ReaTrackworkEditorController(
            self.doc, self.fixture.workflow,
            read_records=read_rea_trackwork_objects,
            read_hosts=self.host_choices,
            active_document=lambda: self.active,
            new_entity_id=self.allocate_id,
        )
        self.controller.refresh()

    def allocate_id(self):
        self.next_id += 1
        return "Research-UI-{}".format(self.next_id)

    def host_choices(self, document):
        return tuple(editor.ReaHostChoice(
            obj, obj.Name, obj.TemplateSetID, obj.Name,
        ) for obj in self.fixture.hosts if obj in document.Objects)

    def values(self, **changes):
        values = dict(
            entity_kind="turnout", host_names=("HostA",),
            switch_size="B", crossing_ratio=8.0,
            reference_chainage_mm=1500.0, handing="Left-hand",
            orientation="Facing in host travel direction",
            arrangement=None, minimum_radius_mm=None,
        )
        values.update(changes)
        return values

    def changes(self, **changes):
        values = self.values(**changes)
        values.pop("entity_kind")
        return values

    def panel(self):
        return editor.ReaTrackworkEditorPanel(
            self.controller, qt_widgets(), minimum_radius_mm=600.0,
        )

    def fill(self, panel, **changes):
        values = self.values(**changes)
        panel.kind_combo.setCurrentIndex(panel.kind_combo.findData(
            values["entity_kind"],
        ))
        panel.size_combo.setCurrentIndex(panel.size_combo.findData(
            values["switch_size"],
        ))
        panel.host_a_combo.setCurrentIndex(panel.host_a_combo.findData(
            values["host_names"][0],
        ))
        if len(values["host_names"]) == 2:
            panel.host_b_combo.setCurrentIndex(panel.host_b_combo.findData(
                values["host_names"][1],
            ))
        panel.ratio_edit.setText(str(values["crossing_ratio"]))
        panel.chainage_edit.setText(str(values["reference_chainage_mm"]))

    def test_create_edit_change_back_keeps_identity_and_operator_label(self):
        obj = self.controller.create(**self.values())
        original = getattr(obj, REA_INTENT_JSON_PROPERTY)
        obj.Label = "Operator's siding"
        self.controller.begin_edit("Research-UI-1")
        self.controller.apply_changes(**self.changes(
            switch_size="C", crossing_ratio=9.25,
        ))
        changed = read_rea_trackwork_objects(self.doc)[0][1]
        self.assertEqual(changed.source_specification.crossing_ratio, 9.25)
        self.assertEqual(changed.source_specification.switch_size, "C")
        self.controller.apply_changes(**self.changes())
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), original)
        self.assertEqual(obj.Label, "Operator's siding")
        self.assertEqual(self.doc.commits, 3)
        self.assertEqual(len(read_rea_trackwork_objects(self.doc)), 1)

    def test_crossover_uses_ordered_hosts_and_explicit_radius(self):
        obj = self.controller.create(**self.values(
            entity_kind="crossover", host_names=("HostA", "HostB"),
            orientation=None, arrangement="Facing crossover",
            handing="Automatic handing", minimum_radius_mm=600.0,
        ))
        intent = read_rea_trackwork_objects(self.doc)[0][1]
        self.assertEqual(intent.entity_kind, "crossover")
        self.assertEqual(intent.host_names, ("HostA", "HostB"))
        self.assertEqual(intent.minimum_radius_mm, 600.0)
        self.assertEqual(self.fixture.store.view_for(obj).scene.entity_id,
                         intent.entity_id)

    def test_invalid_and_unsupported_inputs_do_not_open_transaction(self):
        for value in (float("nan"), float("inf"), True, 0.49, 3.0, 20.125):
            with self.subTest(value=value):
                with self.assertRaises((ValueError, TypeError)):
                    self.controller.create(**self.values(crossing_ratio=value))
                self.assertEqual(self.doc.opens, 0)
        with self.assertRaises(ValueError):
            self.controller.create(**self.values(host_names=("Missing",)))
        self.assertEqual(self.doc.commits, 0)

    def test_changed_active_document_and_replaced_host_refuse(self):
        self.active = object()
        with self.assertRaisesRegex(ValueError, "document"):
            self.controller.create(**self.values())
        self.active = self.doc
        old = self.fixture.hosts[0]
        replacement = types.SimpleNamespace(**vars(old))
        self.doc.Objects[self.doc.Objects.index(old)] = replacement
        self.fixture.hosts[0] = replacement
        with self.assertRaisesRegex(ValueError, "[Hh]ost.*changed"):
            self.controller.create(**self.values())
        self.assertEqual(self.doc.opens, 0)

    def test_stale_loaded_record_and_same_id_replacement_refuse(self):
        obj = self.controller.create(**self.values())
        intent = self.controller.begin_edit("Research-UI-1")
        setattr(obj, REA_INTENT_JSON_PROPERTY, rea_trackwork_intent_to_json(
            replace(intent, reference_chainage_mm=1600.0),
        ))
        with self.assertRaisesRegex(ValueError, "changed"):
            self.controller.apply_changes(**self.changes())
        self.assertEqual(self.doc.opens, 1)
        self.controller.refresh()
        self.controller.begin_edit(intent.entity_id)
        replacement = types.SimpleNamespace(**vars(obj))
        self.doc.Objects[self.doc.Objects.index(obj)] = replacement
        replacement.getTypeIdOfProperty = obj.getTypeIdOfProperty
        with self.assertRaisesRegex(ValueError, "changed"):
            self.controller.apply_changes(**self.changes())
        self.assertEqual(self.doc.opens, 1)

    def test_corrupt_record_refresh_never_silently_omits_it(self):
        obj = self.controller.create(**self.values())
        setattr(obj, REA_INTENT_JSON_PROPERTY, '{"schema_version":999}')
        panel = self.panel()
        self.assertIsNotNone(panel.last_error)
        self.assertFalse(panel.create_button.enabled)
        self.assertFalse(panel.apply_button.enabled)
        self.assertFalse(panel.rebuild_button.enabled)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY),
                         '{"schema_version":999}')

    def test_cancel_cannot_reenable_actions_after_a_failed_refresh(self):
        obj = self.controller.create(**self.values())
        original = getattr(obj, REA_INTENT_JSON_PROPERTY)
        panel = self.panel()
        panel.records_combo.setCurrentIndex(0)
        panel.edit_button.clicked.emit(False)
        setattr(obj, REA_INTENT_JSON_PROPERTY, '{"schema_version":999}')
        panel.refresh_button.clicked.emit(False)
        self.assertFalse(panel.create_button.enabled)
        panel.cancel_button.clicked.emit(False)
        self.assertFalse(panel.create_button.enabled)
        self.assertFalse(panel.apply_button.enabled)
        self.assertIsNotNone(panel.last_error)
        setattr(obj, REA_INTENT_JSON_PROPERTY, original)
        panel.refresh_button.clicked.emit(False)
        self.assertTrue(panel.create_button.enabled)

    def test_actual_signals_create_and_apply_nonmenu_ratio(self):
        panel = self.panel()
        self.fill(panel)
        self.assertEqual(self.doc.opens, 0)
        panel.create_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        self.assertEqual(self.doc.commits, 1)
        panel.edit_button.clicked.emit(False)
        panel.size_combo.setCurrentIndex(panel.size_combo.findData("C"))
        panel.ratio_edit.setText("9.25")
        panel.apply_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        intent = read_rea_trackwork_objects(self.doc)[0][1]
        self.assertEqual(intent.source_specification.crossing_ratio, 9.25)
        self.assertEqual(self.doc.commits, 2)

    def test_exact_numeric_text_roundtrip_and_cancel_are_noops(self):
        original = self.values(crossing_ratio=8.1234567890123,
                               reference_chainage_mm=1500.1234567890123)
        obj = self.controller.create(**original)
        canonical = getattr(obj, REA_INTENT_JSON_PROPERTY)
        panel = self.panel()
        panel.records_combo.setCurrentIndex(0)
        panel.edit_button.clicked.emit(False)
        self.assertEqual(float(panel.ratio_edit.text()),
                         original["crossing_ratio"])
        self.assertEqual(float(panel.chainage_edit.text()),
                         original["reference_chainage_mm"])
        panel.apply_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.assertEqual(self.doc.commits, 1)
        panel.ratio_edit.setText("9.25")
        panel.cancel_button.clicked.emit(False)
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), canonical)
        self.assertEqual(self.doc.commits, 1)

    def test_signal_invalid_text_reports_error_and_preserves_document(self):
        panel = self.panel()
        self.fill(panel)
        for value in ("", "invalid", "NaN", "1e999", "3"):
            panel.ratio_edit.setText(value)
            panel.create_button.clicked.emit(False)
            self.assertIsNotNone(panel.last_error)
            self.assertTrue(panel.status_label.text())
            self.assertEqual(self.doc.opens, 0)

    def test_explicit_rebuild_and_unchanged_apply_keep_history(self):
        obj = self.controller.create(**self.values())
        original = getattr(obj, REA_INTENT_JSON_PROPERTY)
        view = self.fixture.store.view_for(obj)
        view.invalidate("restored empty")
        self.controller.rebuild("Research-UI-1")
        self.assertIsNotNone(view.scene)
        self.controller.begin_edit("Research-UI-1")
        self.controller.apply_changes(**self.changes())
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), original)
        self.assertEqual(self.doc.commits, 1)

    def test_failed_commit_leaves_form_visible_and_previous_object_intact(self):
        obj = self.controller.create(**self.values())
        original = getattr(obj, REA_INTENT_JSON_PROPERTY)
        panel = self.panel()
        panel.records_combo.setCurrentIndex(0)
        panel.edit_button.clicked.emit(False)
        panel.ratio_edit.setText("9.25")
        self.doc.fail_commit = True
        panel.apply_button.clicked.emit(False)
        self.assertIsNotNone(panel.last_error)
        self.assertEqual(panel.ratio_edit.text(), "9.25")
        self.assertEqual(getattr(obj, REA_INTENT_JSON_PROPERTY), original)
        self.assertEqual(self.doc.commits, 1)

    def test_attach_adds_one_plain_widget_tab_without_touching_callbacks(self):
        tabs = []
        original = object()
        dialog = types.SimpleNamespace(
            doc=self.doc, create_turnout=original,
            mode_tabs=types.SimpleNamespace(
                addTab=lambda page, name: tabs.append((page, name)),
            ),
        )
        first = editor.attach_rea_trackwork_panel(
            dialog, self.controller, qt_widgets(), minimum_radius_mm=600.0,
        )
        second = editor.attach_rea_trackwork_panel(
            dialog, self.controller, qt_widgets(), minimum_radius_mm=600.0,
        )
        self.assertIs(first, second)
        self.assertEqual(tabs, [(first.scroll_area, "REA B/C")])
        self.assertIs(dialog.create_turnout, original)
        self.assertEqual(first.minimum_radius_edit.text(), "600.0")

    def test_module_import_and_layer_remain_host_independent(self):
        from tools.modular_structure import structure_report, validate_report
        report = structure_report(ROOT)
        self.assertEqual(validate_report(report), [])
        source = (ROOT / "tracktemplate/ui/rea_trackwork_editor.py").read_text()
        for forbidden in ("import FreeCAD", "import Part", "from pivy",
                          "import PySide", "tracktemplate.adapters",
                          "tracktemplate.compatibility"):
            self.assertNotIn(forbidden, source)
        self.assertIs(importlib.import_module(
            "tracktemplate.ui.rea_trackwork_editor",
        ), editor)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(EditorTests),
    )
    if result.wasSuccessful():
        print("REA trackwork editor standalone validation passed")
    raise SystemExit(not result.wasSuccessful())
