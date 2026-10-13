#!/usr/bin/env python3
"""Prove selected whole-set publication on a copied qualified document.

Reuse the retained turnout, exporter normalisations and document witnesses.
This proof gives no durability, restart recovery or production clearance.
"""

import datetime
import importlib.util
import json
from pathlib import Path
import traceback
from unittest import mock

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "Selected export set FreeCAD validation passed"
FAULT = "controlled selected set failure"


def helper(filename):
    path = ROOT / "tests" / filename
    spec = importlib.util.spec_from_file_location("_selected_set", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DOCUMENT = helper("freecad_validate_selected_export_document.py")
PREVIOUS = DOCUMENT.PREVIOUS
CORE = DOCUMENT.CORE
SELECTED = DOCUMENT.SELECTED


def prepared_plan(module, document, parent, manifest=True):
    from tracktemplate.application.selected_export_set import (
        prepare_selected_export_plan,
    )

    config, old, _, issues, outline, solid, _ = SELECTED._selected_plan(
        module, document, parent,
    )
    assert not module.preflight_blocking_report(issues), issues
    config.update(create_manifest=manifest, overwrite_existing=False)
    config["formats"] = {name: True for name in CORE.FORMATS}
    records, skipped = module.selected_export_records_for_formats(
        [outline, solid], config,
    )
    before = CORE.input_state((records, config))
    plan = prepare_selected_export_plan(
        records, config, SELECTED.SET_ID, old["selected_scope"],
        plan_export=module.plan_selected_production_export,
    )
    assert CORE.input_state((records, config)) == before
    assert len(plan["tasks"]) == 4 and not skipped
    assert {task["format"] for task in plan["tasks"]} == CORE.FORMATS
    child = Path(plan["output_directory"])
    assert child.parent == parent and not child.exists()
    assert all(Path(task["path"]).parent == child for task in plan["tasks"])
    assert bool(plan.get("manifest_path")) is manifest
    return config, plan, skipped


def files_state(parent):
    return {
        str(path.relative_to(parent)): (
            path.stat().st_ino, path.stat().st_mtime_ns, CORE.sha256(path),
        )
        for path in parent.rglob("*") if path.is_file()
    }


def run_case(module, document, parent, *, manifest=True, failure=None):
    from tracktemplate.adapters.export.core_layout_set import (
        CoreLayoutExportSetFiles,
    )

    parent.mkdir()
    old = parent / "previous-complete-set"
    old.mkdir()
    (old / "operator.svg").write_text("preserve previous output\n")
    (parent / "operator.csv").write_text("preserve parent output\n")
    previous = files_state(parent)
    config, plan, skipped = prepared_plan(
        module, document, parent, manifest,
    )
    child = Path(plan["output_directory"])
    before = PREVIOUS.document_witness(module, document)
    inputs = CORE.input_state((config, plan))
    registry = dict(App.listDocuments())
    active = App.ActiveDocument
    internal = App.activeDocument()
    binding = module.run_selected_production_export
    calls = []
    csv_calls = []

    class FaultFiles(CoreLayoutExportSetFiles):
        def publish(self):
            if failure == "collision":
                child.mkdir()
                (child / "foreign.txt").write_text("collision owner\n")
            if failure == "publication":
                raise OSError(FAULT + " publication")
            super().publish()
            if failure == "postpublication":
                raise OSError(FAULT + " postpublication")

    def dispatch(scratch, task, path):
        assert scratch is not document and scratch.Temporary
        assert not child.exists()
        assert task is plan["tasks"][len(calls)]
        assert all(files_state(parent).get(k) == v
                   for k, v in previous.items())
        calls.append(task["format"])
        if failure == "writer" and len(calls) == len(plan["tasks"]):
            scratch.addObject("Part::Feature", "PartialExport")
            raise RuntimeError(FAULT + " final writer")
        return module.dispatch_freecad_export(scratch, task, path)

    original_csv = binding.write_export_manifest

    def write_csv(path, rows):
        csv_calls.append(path)
        assert not child.exists()
        if failure == "csv":
            raise OSError(FAULT + " CSV")
        return original_csv(path, rows)

    with (
        mock.patch.object(binding, "export_files_factory", FaultFiles),
        mock.patch.object(binding, "write_export_manifest", write_csv),
    ):
        summary = SELECTED._export(
            module, document, config, plan, skipped, override=dispatch,
        )
    published = failure in (None, "postpublication")
    assert summary["publication_state"] == (
        "published" if published else "not-published"
    ), summary
    assert summary["successful_files"] == (
        4 + int(manifest) if published else 0
    ), summary
    assert bool(summary["manifest_path"]) is (manifest and published)
    assert len(csv_calls) == int(manifest and failure != "writer")
    assert bool(summary["failed_files"]) is (failure is not None)
    if published:
        assert summary["output_directory"] == str(child)
        assert {path.name for path in child.iterdir()} == {
            Path(task["path"]).name for task in plan["tasks"]
        } | ({Path(plan["manifest_path"]).name} if manifest else set())
    elif failure == "collision":
        assert {p.name for p in child.iterdir()} == {"foreign.txt"}
        assert (child / "foreign.txt").read_text() == "collision owner\n"
    else:
        assert not child.exists()
    assert all(files_state(parent).get(k) == v
               for k, v in previous.items())
    assert not [p for p in parent.iterdir() if p.name.startswith(".")]
    PREVIOUS.assert_document(module, document, before)
    assert CORE.input_state((config, plan)) == inputs
    assert dict(App.listDocuments()) == registry
    assert App.ActiveDocument is active and App.activeDocument() is internal
    result = {
        "summary": {key: summary[key] for key in (
            "output_directory", "successful_files", "failed_files",
            "skipped_objects", "formats", "manifest_path",
            "manifest_requested", "failures", "failure_details",
            "skipped_outputs", "skipped_details", "publication_state",
        )},
        "task_results": [{
            "path": item["task"]["path"],
            "format": item["task"]["format"],
            "success": item["success"], "error": item["error"],
        } for item in summary["results"]],
        "previous_outputs_unchanged": True,
        "editable_document_unchanged": True,
    }
    if published:
        snapshot = CORE.output_state(module, child)
        result["content_by_path"] = snapshot["files"]["content_by_path"]
        result["metrics"] = snapshot["metrics"]
    return result


def validate():
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    directory = ROOT / "tmp/selected-export-set/native-runs" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    _, identities = PREVIOUS.source_evidence()
    sources = CORE.source_hashes()
    for path in (Path(__file__), Path(DOCUMENT.__file__),
                 Path(PREVIOUS.__file__), Path(SELECTED.__file__)):
        sources[str(path.relative_to(ROOT))] = CORE.sha256(path)
    receipt = {"status": "RUNNING", "source_sha256": sources}
    document = module = original_datetime = None
    try:
        module, routing = CORE.load_product(atomic=True)
        receipt.update(profile=CORE.PROFILE, core_routing=routing)
        assert module.run_selected_production_export.atomic
        document = PREVIOUS.prepare_document(module, directory)
        original_datetime = module.datetime.datetime
        module.datetime.datetime = CORE.FixedDateTime
        legacy = DOCUMENT.success(
            module, document, directory / "legacy", legacy=True,
        )
        cases = {}
        for name, manifest, failure in (
            ("success", True, None), ("repeat", True, None),
            ("csv-off", False, None), ("final-writer", True, "writer"),
            ("csv-failure", True, "csv"),
            ("collision", True, "collision"),
            ("publication", True, "publication"),
            ("postpublication", True, "postpublication"),
        ):
            cases[name] = run_case(
                module, document, directory / name,
                manifest=manifest, failure=failure,
            )
        for key in ("content_by_path", "metrics"):
            assert legacy[key] == cases["success"][key]
            assert cases["success"][key] == cases["repeat"][key]
        receipt["cases"] = cases
        receipt["legacy_and_repeat_equivalence"] = True
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
        receipt["fixture_and_oracles_preserved"] = all(
            CORE.sha256(path) == value for path, value in identities.items()
        )
        receipt["source_unchanged"] = all(
            CORE.sha256(ROOT / path) == value for path, value in sources.items()
        )
        receipt["remaining_documents"] = sorted(App.listDocuments())
        if (not receipt["fixture_and_oracles_preserved"]
                or not receipt["source_unchanged"]
                or receipt["remaining_documents"]):
            receipt["status"] = "FAIL"
        (directory / "result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        )
        print("SELECTED_EXPORT_SET_EVIDENCE=" + str(directory), flush=True)
    assert receipt["status"] == "PASS"
    print(SENTINEL, flush=True)


if __name__ in {"__main__", "freecad_validate_selected_export_set"}:
    validate()
