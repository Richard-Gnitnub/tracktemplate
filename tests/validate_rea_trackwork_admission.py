#!/usr/bin/env python3
"""Disprove accidental legacy admission of stored source research objects."""

import copy
import importlib
from pathlib import Path
import sys
from types import ModuleType
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import rea_turnout_state as state  # noqa: E402
import validate_phase9b_rea_turnout_state as fixture  # noqa: E402


SENTINEL = "REA trackwork legacy admission checks passed"


class Document:
    def __init__(self):
        self.Objects = []
        self.UndoMode = 1
        self.transactions = 0
        self.calls = []

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)

    def openTransaction(self, label):
        self.transactions += 1

    def commitTransaction(self):
        pass

    def abortTransaction(self):
        pass


def source_document(*, switch="B", kind="turnout"):
    doc = Document()
    value = fixture.record(kind)
    value["intent"]["source_specification"]["switch_size"] = switch
    intent = state.rea_trackwork_intent_from_json(fixture.encoded(value))
    hosts = [SimpleNamespace(Name=name, TemplateSetID=intent.template_set_id,
                             Document=doc, PropertiesList=[])
             for name in intent.host_names]
    obj = SimpleNamespace(
        Name="ResearchSource", Document=doc, TypeId="App::FeaturePython",
        PropertiesList=[state.REA_RECORD_TYPE_PROPERTY,
                        state.REA_INTENT_JSON_PROPERTY,
                        state.REA_HOSTS_PROPERTY],
    )
    setattr(obj, state.REA_RECORD_TYPE_PROPERTY, state.REA_TRACKWORK_SCHEMA_ID)
    setattr(obj, state.REA_INTENT_JSON_PROPERTY,
            state.rea_trackwork_intent_to_json(intent))
    setattr(obj, state.REA_HOSTS_PROPERTY, hosts)
    doc.Objects = hosts + [obj]
    return doc, obj, intent, hosts


class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = importlib.import_module(
            "tracktemplate.compatibility.rea_trackwork_admission"
        )
        cls.error = cls.subject.ReaTrackworkAdmissionError

    def test_strict_records_and_relevant_selectors(self):
        for switch in ("B", "C"):
            doc, obj, intent, hosts = source_document(switch=switch)
            self.assertEqual(self.subject.source_records(doc), ((obj, intent),))
            for selectors in ({}, {"set_id": "SET-001"},
                              {"host_names": (hosts[0].Name,)},
                              {"entity_id": intent.entity_id}):
                with self.subTest(switch=switch, selectors=selectors):
                    with self.assertRaises(self.error):
                        self.subject.refuse_rea_operation(doc, **selectors)
            self.assertIsNone(self.subject.refuse_rea_operation(
                doc, set_id="OTHER", host_names=("OtherHost",),
                entity_id="Legacy-TO",
            ))
            self.assertEqual(doc.transactions, 0)
        self.assertEqual(self.subject.source_records(Document()), ())
        self.assertIsNone(self.subject.refuse_rea_operation(Document()))

    def test_every_marker_presence_is_safety_relevant(self):
        names = (state.REA_RECORD_TYPE_PROPERTY, state.REA_INTENT_JSON_PROPERTY,
                 state.REA_HOSTS_PROPERTY)
        for retained in names:
            doc = Document()
            obj = SimpleNamespace(Name="Broken", Document=doc,
                                  PropertiesList=[retained])
            setattr(obj, retained, "")
            doc.Objects = [obj]
            with self.subTest(retained=retained):
                with self.assertRaises(self.error):
                    self.subject.refuse_rea_operation(doc, set_id="OTHER")
                self.assertEqual(doc.Objects, [obj])
        for marker in ("", "future-record", None, True):
            doc, obj, _intent, _hosts = source_document()
            setattr(obj, state.REA_RECORD_TYPE_PROPERTY, marker)
            with self.assertRaises(self.error):
                self.subject.source_records(doc)

    def test_corrupt_payload_links_and_mixed_identity_fail_closed(self):
        for payload in ("", "{}", "{", '{"x":1,"x":2}'):
            doc, obj, _intent, _hosts = source_document()
            setattr(obj, state.REA_INTENT_JSON_PROPERTY, payload)
            with self.assertRaises(self.error):
                self.subject.refuse_rea_operation(doc, set_id="OTHER")
        for fault in ("missing", "reversed", "wrong-set", "foreign",
                      "replaced", "legacy-id", "duplicate"):
            doc, obj, _intent, hosts = source_document(kind="crossover")
            if fault == "missing":
                setattr(obj, state.REA_HOSTS_PROPERTY, [])
            elif fault == "reversed":
                setattr(obj, state.REA_HOSTS_PROPERTY, hosts[::-1])
            elif fault == "wrong-set":
                hosts[0].TemplateSetID = "OTHER"
            elif fault == "foreign":
                hosts[0].Document = Document()
            elif fault == "replaced":
                doc.Objects[0] = copy.copy(hosts[0])
            elif fault == "legacy-id":
                obj.PropertiesList.append("TurnoutID")
                obj.TurnoutID = "TO-001"
            else:
                duplicate = copy.copy(obj)
                duplicate.Name = "Duplicate"
                doc.Objects.append(duplicate)
            with self.subTest(fault=fault):
                with self.assertRaises(self.error):
                    self.subject.source_records(doc)

    def test_crossover_actual_preflight_blocks_before_original_or_cache(self):
        from tracktemplate.compatibility.crossover_preflight import (
            CrossoverPreflightAdapter,
        )
        doc, _obj, intent, hosts = source_document(kind="crossover")

        def solve(doc, host_a, host_b, reference_chainage,
                  arrangement="Facing crossover", handing="Automatic handing",
                  track_gauge=16.5, flangeway=1, minimum_radius=600,
                  ignored_crossover_id=None, ignored_turnout_id=None):
            doc.calls.append("solver")
            raise AssertionError("Legacy solver must not run")

        def build(doc, host_a, host_b, reference_chainage,
                  arrangement="Facing crossover", handing="Automatic handing",
                  track_gauge=16.5, flangeway=1, minimum_radius=600,
                  ignored_crossover_id=None, ignored_turnout_id=None,
                  pre_solved=None):
            doc.calls.append("builder")

        def edit(doc, crossover_id, host_a, host_b, reference_chainage,
                 arrangement="Facing crossover", handing="Automatic handing",
                 track_gauge=16.5, flangeway=1, minimum_radius=600,
                 pre_solved=None):
            doc.calls.append("editor")

        module = SimpleNamespace()
        adapter = CrossoverPreflightAdapter(
            module, solve, build, edit, None, None, None,
        )
        for action in (
            lambda: adapter.solve(doc, *hosts, 80),
            lambda: adapter.build(doc, *hosts, 80),
            lambda: adapter.build(doc, *hosts, 80, pre_solved={
                "complete_radius_preflight": {"accepted": True},
            }),
            lambda: adapter.edit(doc, intent.entity_id, *hosts, 80),
            lambda: adapter.input_signature(
                doc, *hosts, 80, "Facing crossover", "Automatic handing",
                16.5, 1, 600,
            ),
        ):
            with self.subTest(action=action):
                with self.assertRaises(self.error):
                    action()
                self.assertEqual(doc.calls, [])

    def test_host_integration_blocks_before_transaction_and_keeps_legacy(self):
        from tracktemplate.compatibility.turnout_host_integration_recovery import (
            TurnoutHostIntegrationRecoveryAdapter,
        )
        from tracktemplate.compatibility.crossover_host_integration_recovery import (
            CrossoverHostIntegrationRecoveryAdapter,
        )
        for kind, cls in (("turnout", TurnoutHostIntegrationRecoveryAdapter),
                          ("crossover", CrossoverHostIntegrationRecoveryAdapter)):
            module = ModuleType("legacy_integration_fixture")
            exec("def run(doc, entity_id):\n"
                 "    doc.calls.append('original')\n"
                 "    doc.openTransaction('label')\n"
                 "    doc.commitTransaction()\n"
                 "    return entity_id\n", module.__dict__)
            adapter = cls(module, module.run, module.run)
            doc, _obj, intent, _hosts = source_document(kind=kind)
            setattr(module, kind + "_config_by_id", lambda _doc, _id: {
                "template_set_id": "SET-001", "host_object": "HostA",
                "host_a_object": "HostA", "host_b_object": "HostB",
            })
            for entity_id in (intent.entity_id, "LegacyEntity"):
                with self.subTest(kind=kind, entity_id=entity_id):
                    with self.assertRaises(self.error):
                        adapter._run(doc, entity_id, module.run, "label")
                    self.assertEqual((doc.calls, doc.transactions), ([], 0))
            legacy = Document()
            self.assertEqual(adapter._run(legacy, "LegacyEntity", module.run,
                                          "label"), "LegacyEntity")
            self.assertEqual((legacy.calls, legacy.transactions),
                             (["original"], 1))

    def test_generate_and_direct_removal_refuse_before_original(self):
        from tracktemplate.compatibility.crossover_dependent_recalculation import (
            CrossoverDependentRecalculationAdapter, HOOK_NAMES,
        )
        doc, _obj, _intent, _hosts = source_document()
        adapter = object.__new__(CrossoverDependentRecalculationAdapter)
        adapter.module = SimpleNamespace(
            App=SimpleNamespace(ActiveDocument=doc), OUTPUT_REPLACE="replace",
        )
        adapter.originals = {
            HOOK_NAMES[1]: lambda: doc.calls.append("validate-original"),
            HOOK_NAMES[2]: lambda document: document.calls.append("remove"),
        }
        adapter._invocation = lambda: None
        adapter._caller_request = lambda *args, **kwargs: None
        with self.assertRaises(self.error):
            adapter._remove(doc)
        self.assertEqual(doc.calls, [])
        adapter._caller_request = lambda *args, **kwargs: {
            "request": {"output_mode": "replace"}, "document_id": id(doc),
        }
        with self.assertRaises(self.error):
            adapter._validate_export()
        self.assertEqual(doc.calls, [])
        legacy = Document()
        adapter._caller_request = lambda *args, **kwargs: None
        adapter._remove(legacy)
        self.assertEqual(legacy.calls, ["remove"])

    def test_reference_and_b4_refuse_before_context_or_reuse(self):
        from tracktemplate.compatibility.chair_reference_preview import (
            _source_context,
        )
        from tracktemplate.compatibility.crossover_b4_recovery import (
            CrossoverB4RecoveryAdapter,
        )
        doc, _obj, intent, _hosts = source_document(kind="crossover")

        def context(*args, **kwargs):
            doc.calls.append("context")
            raise AssertionError("Legacy chair context must not run")

        module = SimpleNamespace(_chair_generation_context=context)
        with self.assertRaises(self.error):
            _source_context(module, doc, intent.entity_id,
                            entity_kind="crossover")
        self.assertEqual(doc.calls, [])

        def apply(doc, crossover_id):
            doc.calls.append("apply")

        writer = lambda *args: None
        module._write_crossover_b4_and_timber_analysis_metadata = writer
        module.crossover_config_by_id = context
        adapter = CrossoverB4RecoveryAdapter(module, apply, writer)
        with self.assertRaises(self.error):
            adapter.apply(doc, intent.entity_id)
        self.assertEqual(doc.calls, [])

    def test_selected_export_refuses_before_dispatcher_or_files(self):
        from tracktemplate.compatibility.selected_export_workflow import (
            SelectedExportBinding,
        )
        doc, _obj, _intent, _hosts = source_document()
        adapter = object.__new__(SelectedExportBinding)
        with self.assertRaises(self.error):
            adapter(doc, {}, {}, "SET-001", {}, {}, {}, {})
        self.assertEqual((doc.calls, doc.transactions), ([], 0))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AdmissionTests)
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
