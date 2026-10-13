#!/usr/bin/env python3
"""Prove selected serializers preserve copied editable FreeCAD documents.

Reuse the qualified turnout fixture, unchanged artifact normalisation and
existing object/history/persistence witnesses. This is not whole-set atomic
publication, restart recovery, physical fit or production clearance.
"""

import datetime
import importlib.util
import json
from pathlib import Path
import traceback
from unittest import mock

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "Selected export document FreeCAD validation passed"
FAULT = "controlled selected document failure"


def helper(filename):
    path = ROOT / "tests" / filename
    spec = importlib.util.spec_from_file_location("_selected_document", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREVIOUS = helper("freecad_validate_selected_export_rollback.py")
CORE = PREVIOUS.CORE
SELECTED = PREVIOUS.SELECTED


def prepared_plan(module, document, directory):
    config, previous, _, issues, outline, solid, _ = (
        SELECTED._selected_plan(module, document, directory)
    )
    assert not module.preflight_blocking_report(issues), issues
    config["formats"] = {name: True for name in CORE.FORMATS}
    records, skipped = module.selected_export_records_for_formats(
        [outline, solid], config,
    )
    plan = module.plan_selected_production_export(
        records, config, SELECTED.SET_ID, previous["selected_scope"],
    )
    assert {task["format"] for task in plan["tasks"]} == CORE.FORMATS
    assert len(plan["tasks"]) == 4 and not skipped
    return config, plan, skipped


def success(module, document, directory, *, legacy=False):
    directory.mkdir()
    config, plan, skipped = prepared_plan(module, document, directory)
    before = PREVIOUS.document_witness(module, document)
    inputs = CORE.input_state((config, plan))
    registry = dict(App.listDocuments())
    active = App.activeDocument()
    binding = module.run_selected_production_export
    if legacy:
        module.run_selected_production_export = binding.original_command
    try:
        summary = SELECTED._export(module, document, config, plan, skipped)
    finally:
        module.run_selected_production_export = binding
    assert summary["successful_files"] == 5, summary
    assert summary["failed_files"] == 0, summary
    PREVIOUS.assert_document(module, document, before)
    assert CORE.input_state((config, plan)) == inputs
    assert dict(App.listDocuments()) == registry
    assert App.ActiveDocument is active and App.activeDocument() is active
    snapshot = CORE.output_state(module, directory)
    return {
        "content_by_path": snapshot["files"]["content_by_path"],
        "metrics": snapshot["metrics"],
        "summary": {key: summary[key] for key in (
            "successful_files", "failed_files", "formats",
            "manifest_requested", "skipped_objects",
        )},
    }


def lifecycle(module, document, directory):
    from tracktemplate.adapters.freecad.core_export_document import (
        CoreExportDocument,
    )

    witness = App.newDocument("SelectedIndependentWitness")
    obj = witness.addObject("App::FeaturePython", "Witness")
    obj.addProperty("App::PropertyString", "WitnessValue")
    obj.WitnessValue = "preserve independent document"
    witness.recompute()
    outcomes = []
    binding = module.run_selected_production_export
    factory = binding.export_dispatcher_factory
    try:
        for mode in (
            "success-other-active", "success-no-active", "inconsistent-active",
            "construction", "recompute-removal", "swallowed-removal",
            "close", "interruption",
        ):
            target = directory / mode
            target.mkdir()
            config, plan, skipped, *_ = SELECTED._selected_plan(
                module, document, target,
            )
            config["overwrite_existing"] = True
            previous = PREVIOUS.seed_previous(plan)
            previous_files = {
                path.name: (data, path.stat().st_ino)
                for path, data in previous.items()
            }
            App.setActiveDocument(witness.Name)
            if mode == "inconsistent-active":
                App.setActiveDocument("")
                assert App.ActiveDocument is witness
                assert App.activeDocument() is None
            elif mode == "success-no-active":
                setup = App.newDocument("SelectedActiveSetup")
                App.closeDocument(setup.Name)
                assert App.ActiveDocument is None
                assert App.activeDocument() is None
            registry = dict(App.listDocuments())
            active, internal_active = App.ActiveDocument, App.activeDocument()
            before = PREVIOUS.document_witness(module, document)
            inputs = CORE.input_state((config, plan))
            calls, retained, removal_calls = [], [], []
            interruption = KeyboardInterrupt(FAULT + " interruption")

            class CloseFault:
                def __getattr__(self, name):
                    return getattr(App, name)

                def closeDocument(self, name):
                    assert name not in registry
                    retained.append(App.getDocument(name))
                    raise RuntimeError(FAULT + " close")

            class RemovalFault:
                def __init__(self, scratch):
                    self.scratch = scratch

                def __getattr__(self, name):
                    return getattr(self.scratch, name)

                def removeObject(self, name):
                    removal_calls.append(name)
                    raise RuntimeError(FAULT + " removal")

            def dispatch(scratch, task, path):
                assert scratch is not document and scratch is not witness
                assert scratch.Name not in registry and scratch.Temporary
                calls.append(scratch.Name)
                if mode in {"construction", "interruption"}:
                    scratch.addObject("Part::Feature", "PartialConstruction")
                    if mode == "interruption":
                        raise interruption
                    raise RuntimeError(FAULT + " construction")
                if mode == "recompute-removal":
                    scratch = RemovalFault(scratch)
                return module.dispatch_freecad_export(scratch, task, path)

            def leave_objects(scratch, objects):
                assert scratch is not document
                removal_calls.extend(item.Name for item in objects)

            if mode == "close":
                binding.export_dispatcher_factory = lambda serializer: (
                    CoreExportDocument(serializer, app=CloseFault())
                )
            try:
                with mock.patch.object(
                    module, "_document_recompute",
                    side_effect=RuntimeError(FAULT + " recompute")
                    if mode == "recompute-removal"
                    else module._document_recompute,
                ), mock.patch.object(
                    module, "_remove_temporary_export_objects",
                    side_effect=leave_objects if mode == "swallowed-removal"
                    else module._remove_temporary_export_objects,
                ):
                    try:
                        summary = SELECTED._export(
                            module, document, config, plan, skipped, dispatch,
                        )
                    except KeyboardInterrupt as error:
                        assert mode == "interruption" and error is interruption
                        summary = None
            finally:
                binding.export_dispatcher_factory = factory
            successful = mode.startswith("success") or mode == "swallowed-removal"
            if successful:
                assert summary["successful_files"] == 2, summary
                assert summary["failed_files"] == 0, summary
                assert len(calls) == 1
            else:
                if summary is not None:
                    assert summary["successful_files"] == 0, summary
                    assert summary["failed_files"] == 1, summary
                    details = "\n".join(summary["failure_details"])
                    if mode == "inconsistent-active":
                        assert "active" in details.lower() and not calls
                    else:
                        assert FAULT in details, summary
                assert {
                    path.name: (path.read_bytes(), path.stat().st_ino)
                    for path in previous
                } == previous_files
            if mode in {"swallowed-removal", "recompute-removal"}:
                assert removal_calls
            if mode == "close":
                assert len(retained) == 1
                assert retained[0].Name in details
                assert App.getDocument(retained[0].Name) is retained[0]
                assert set(App.listDocuments()) == set(registry) | {
                    retained[0].Name,
                }
                assert App.ActiveDocument is active
                # This test owns the isolated host and this retained document.
                App.closeDocument(retained[0].Name)
                App.setActiveDocument(active.Name)
            assert dict(App.listDocuments()) == registry
            assert App.ActiveDocument is active
            assert App.activeDocument() is internal_active
            PREVIOUS.assert_document(module, document, before)
            assert CORE.input_state((config, plan)) == inputs
            assert witness.getObject("Witness") is obj
            assert obj.WitnessValue == "preserve independent document"
            assert not list(target.glob(".railway_selected_export_*"))
            outcomes.append({
                "case": mode, "isolated_calls": len(calls),
                "editable_model_history_identity_unchanged": True,
                "registry_restored": mode != "close",
                "owned_close_failure_retained": len(retained),
                "active_document_restored": True,
                "success": successful,
            })
    finally:
        binding.export_dispatcher_factory = factory
        App.closeDocument(witness.Name)
        App.setActiveDocument(document.Name)
    return outcomes


def validate():
    assert not App.listDocuments(), "Use an empty isolated qualified host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    directory = ROOT / "tmp/selected-export-document/native-runs" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    _, identities = PREVIOUS.source_evidence()
    sources = CORE.source_hashes()
    for path in (Path(__file__), Path(PREVIOUS.__file__),
                 Path(SELECTED.__file__), Path(PREVIOUS.HOST.__file__)):
        sources[str(path.relative_to(ROOT))] = CORE.sha256(path)
    receipt = {"status": "RUNNING", "source_sha256": sources}
    document = None
    module = None
    original_datetime = None
    try:
        module, routing = CORE.load_product(atomic=True, selected_atomic=False)
        receipt.update(profile=CORE.PROFILE, core_routing=routing)
        document = PREVIOUS.prepare_document(module, directory)
        original_datetime = module.datetime.datetime
        module.datetime.datetime = CORE.FixedDateTime
        expected = success(module, document, directory / "legacy", legacy=True)
        actual = success(module, document, directory / "modular")
        repeated = success(module, document, directory / "repeated")
        assert expected == actual == repeated
        receipt["all_format_equivalence"] = actual
        receipt["lifecycle"] = lifecycle(module, document, directory)
        document = PREVIOUS.reopen_document(module, document)
        receipt["save_reopen_unchanged"] = True
        receipt["status"] = "PASS"
    except BaseException:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        if original_datetime is not None:
            module.datetime.datetime = original_datetime
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        receipt["source_fixture_and_oracles_preserved"] = all(
            CORE.sha256(path) == value for path, value in identities.items()
        )
        receipt["remaining_documents"] = sorted(App.listDocuments())
        receipt["source_unchanged"] = all(
            CORE.sha256(ROOT / path) == value for path, value in sources.items()
        )
        if (not receipt["source_fixture_and_oracles_preserved"]
                or receipt["remaining_documents"]
                or not receipt["source_unchanged"]):
            receipt["status"] = "FAIL"
        (directory / "result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("SELECTED_EXPORT_DOCUMENT_EVIDENCE=" + str(directory), flush=True)
    assert receipt["status"] == "PASS"
    print(SENTINEL, flush=True)


if __name__ in {"__main__", "freecad_validate_selected_export_document"}:
    try:
        validate()
    except BaseException:
        traceback.print_exc()
        raise SystemExit(1)
