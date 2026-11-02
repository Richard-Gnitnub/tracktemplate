#!/usr/bin/env python3
"""Verify remaining legacy ingresses refuse source records before effects."""

from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from validate_rea_trackwork_admission import Document, source_document
from tracktemplate.compatibility import transition_workflow as workflow


class BindingTests(unittest.TestCase):
    def test_turnout_build_and_edit_refuse_before_original_call(self):
        for switch in ("B", "C"):
            doc, _obj, intent, hosts = source_document(switch=switch)
            module = types.SimpleNamespace(
                turnout_config_by_id=lambda doc, identifier: {
                    "host_object": "HostA", "template_set_id": "SET-001",
                },
            )
            calls = []

            def build(doc, host_obj, turnout_id=None):
                calls.append("build")
                return 12

            def edit(doc, turnout_id, host_obj):
                calls.append("edit")
                return 13

            adapter = workflow._ReaTurnoutAdmissionAdapter(module, build, edit)
            with self.assertRaises(ValueError):
                adapter.build(doc, hosts[0])
            with self.assertRaises(ValueError):
                adapter.edit(doc, "TO-001", hosts[0])
            with self.assertRaises(ValueError):
                adapter.edit(doc, intent.entity_id, hosts[0])
            self.assertEqual(calls, [])
            self.assertEqual(adapter.build(Document(), hosts[0]), 12)
            self.assertEqual(adapter.edit(Document(), "TO-001", hosts[0]), 13)
            self.assertEqual(calls, ["build", "edit"])

    def test_chair_reuse_refuses_before_cache_or_original(self):
        doc, _obj, intent, _hosts = source_document()
        calls = []
        adapter = workflow._ChairAnalysisReuseAdapter(
            lambda *args: calls.append("original"), {},
        )
        with self.assertRaises(ValueError):
            adapter(doc, "turnout", intent.entity_id)
        self.assertEqual(calls, [])

    def test_core_export_refuses_before_calculation_or_dispatch(self):
        doc, _obj, _intent, _hosts = source_document()
        calls = []

        def operation(*args, **kwargs):
            calls.append("operation")
            return 17

        adapters = (
            workflow._CoreLayoutExportAdapter(*([operation] * 6)),
            workflow._StagedCoreLayoutExportAdapter(*([operation] * 8)),
        )
        for adapter in adapters:
            with self.assertRaises(ValueError):
                adapter(doc, {}, {}, "SET-001", {}, {}, {}, {})
            self.assertEqual(calls, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BindingTests),
    )
    if result.wasSuccessful():
        print("REA trackwork composition guards passed")
    raise SystemExit(not result.wasSuccessful())
