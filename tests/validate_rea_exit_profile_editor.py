#!/usr/bin/env python3
"""Check explicit exit-profile choices through the existing editor ports."""

import inspect
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application.rea_turnout_state import (
    REA_INTENT_JSON_PROPERTY,
)
from tracktemplate.domain import rea_turnout
from tracktemplate.ui import rea_trackwork_editor as editor
from validate_rea_trackwork_editor import EditorTests


def profile():
    return rea_turnout.ReaExitSleeperProfile(
        "templot-556b-00-D0GAF-32mm-full-exit",
    )


class ExitProfileEditorTests(unittest.TestCase):
    def setUp(self):
        self.editor_fixture = EditorTests()
        self.editor_fixture.setUp()
        self.addCleanup(self.editor_fixture.doCleanups)
        self.controller = self.editor_fixture.controller
        self.doc = self.editor_fixture.doc

    @staticmethod
    def payload(obj):
        return getattr(obj, REA_INTENT_JSON_PROPERTY)

    def selected_panel(self):
        panel = self.editor_fixture.panel()
        self.editor_fixture.fill(panel)
        panel.exit_profile_combo.setCurrentIndex(1)
        return panel

    def test_controller_keywords_are_optional_and_explicit(self):
        for method in (editor.ReaTrackworkEditorController.create,
                       editor.ReaTrackworkEditorController.apply_changes):
            parameter = inspect.signature(method).parameters.get(
                "exit_sleeper_profile",
            )
            self.assertIsNotNone(parameter)
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIsNone(parameter.default)

    def test_new_panel_does_not_infer_a_profile_from_host_width(self):
        panel = self.editor_fixture.panel()
        self.assertIsNone(panel.exit_profile_combo.currentData())
        self.assertEqual(panel.exit_profile_combo.currentText(),
                         "Not selected; exit sleepers pending")
        self.assertEqual(panel.exit_profile_combo.object_name,
                         "TrackTemplateReaExitProfile")
        self.assertEqual(self.doc.opens, 0)
        self.editor_fixture.fill(panel)
        panel.create_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        data = json.loads(self.payload(panel.last_result))
        self.assertEqual(data["schema_version"], 1)
        self.assertNotIn("exit_sleeper_profile", data["intent"])
        self.assertIsNone(self.controller.records[0][1].exit_sleeper_profile)

    def test_selected_turnout_creation_uses_the_fixed_profile(self):
        panel = self.selected_panel()
        self.assertIn("00-D0GAF", panel.exit_profile_combo.currentText())
        self.assertIn("32 mm", panel.exit_profile_combo.currentText())
        self.assertEqual(self.doc.opens, 0)
        panel.create_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        intent = self.controller.records[0][1]
        self.assertEqual(intent.exit_sleeper_profile, profile())
        data = json.loads(self.payload(panel.last_result))
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(data["intent"]["exit_sleeper_profile"],
                         profile().to_record())
        self.assertEqual(self.doc.commits, 1)

    def test_selected_crossover_keeps_existing_minimum_radius(self):
        panel = self.selected_panel()
        self.editor_fixture.fill(
            panel, entity_kind="crossover", host_names=("HostA", "HostB"),
        )
        self.assertEqual(panel.minimum_radius_edit.text(), "600.0")
        panel.create_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        intent = self.controller.records[0][1]
        self.assertEqual(intent.exit_sleeper_profile, profile())
        self.assertEqual(intent.host_names, ("HostA", "HostB"))
        self.assertEqual(intent.minimum_radius_mm, 600.0)
        self.assertEqual(self.doc.commits, 1)

    def test_loaded_profile_and_exact_numbers_survive_unchanged_apply(self):
        obj = self.controller.create(**self.editor_fixture.values(
            crossing_ratio=8.1234567890123,
            reference_chainage_mm=1500.1234567890123,
            exit_sleeper_profile=profile(),
        ))
        original = self.payload(obj)
        panel = self.editor_fixture.panel()
        panel.edit_button.clicked.emit(False)
        self.assertEqual(panel.exit_profile_combo.currentData(),
                         profile().profile_id)
        self.assertEqual(panel.ratio_edit.text(), "8.1234567890123")
        self.assertEqual(panel.chainage_edit.text(), repr(1500.1234567890123))
        self.assertEqual(float(panel.chainage_edit.text()),
                         1500.1234567890123)
        panel.apply_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        self.assertEqual(self.payload(obj), original)
        self.assertEqual(self.doc.commits, 1)
        self.assertEqual(panel.exit_profile_combo.currentData(),
                         profile().profile_id)

    def test_explicit_toggle_back_restores_exact_schema_one_and_label(self):
        obj = self.controller.create(**self.editor_fixture.values())
        original = self.payload(obj)
        obj.Label = "Operator's exit"
        panel = self.editor_fixture.panel()
        panel.edit_button.clicked.emit(False)
        self.assertIsNone(panel.exit_profile_combo.currentData())
        panel.exit_profile_combo.setCurrentIndex(1)
        panel.apply_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        self.assertEqual(json.loads(self.payload(obj))["schema_version"], 2)
        panel.exit_profile_combo.setCurrentIndex(0)
        panel.apply_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        self.assertIs(panel.last_result, obj)
        self.assertEqual(self.payload(obj), original)
        self.assertEqual(obj.Label, "Operator's exit")
        self.assertEqual(self.doc.commits, 3)

    def test_cancel_does_not_change_loaded_profile_and_resets_new_choice(self):
        panel = self.selected_panel()
        panel.create_button.clicked.emit(False)
        self.assertIsNone(panel.last_error)
        obj = panel.last_result
        original = self.payload(obj)
        panel.edit_button.clicked.emit(False)
        panel.exit_profile_combo.setCurrentIndex(0)
        panel.cancel_button.clicked.emit(False)
        self.assertIsNone(panel.exit_profile_combo.currentData())
        self.assertEqual(self.payload(obj), original)
        panel.edit_button.clicked.emit(False)
        self.assertEqual(panel.exit_profile_combo.currentData(),
                         profile().profile_id)
        self.assertEqual(self.doc.commits, 1)

    def test_failed_profile_edit_retains_form_and_restores_canonical_view(self):
        obj = self.controller.create(**self.editor_fixture.values())
        original = self.payload(obj)
        view = self.editor_fixture.fixture.store.view_for(obj)
        old_scene, old_signature = view.scene, view.signature
        panel = self.editor_fixture.panel()
        panel.edit_button.clicked.emit(False)
        panel.exit_profile_combo.setCurrentIndex(1)
        self.doc.fail_commit = True
        panel.apply_button.clicked.emit(False)
        self.assertIsNotNone(panel.last_error)
        self.assertTrue(panel.status_label.text())
        self.assertEqual(panel.exit_profile_combo.currentData(),
                         profile().profile_id)
        self.assertEqual(self.payload(obj), original)
        self.assertEqual((view.scene, view.signature),
                         (old_scene, old_signature))
        self.assertIsNone(self.controller.editing_intent.exit_sleeper_profile)
        self.assertEqual(self.doc.commits, 1)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            ExitProfileEditorTests,
        ),
    )
    if result.wasSuccessful() and result.testsRun == 8 and not result.skipped:
        print("REA exit profile editor standalone validation passed")
    raise SystemExit(not result.wasSuccessful())
