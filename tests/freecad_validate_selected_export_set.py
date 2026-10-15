#!/usr/bin/env python3
"""Prove selected whole-set publication on a copied qualified document.

Reuse the retained turnout/crossover, normalisations and document witnesses.
This proof gives no durability, restart recovery or production clearance.
"""

import csv
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
CROSSOVER = helper("freecad_validate_phase8_crossover_selected_export.py")
CROSSOVER_HOST = helper(
    "freecad_validate_phase8_crossover_host_integration_recovery.py",
)


def prepare_crossover(module, directory):
    """Build the existing XO-001 case on a copy of the fixed fixture."""
    source, _ = PREVIOUS.source_evidence()
    contract = json.loads(CROSSOVER.CONTRACT.read_text())
    assert CORE.sha256(source) == contract["fixture"]["sha256"]
    return CROSSOVER._prepared_copy(
        module, source, directory / "selected-crossover.FCStd",
        contract["scenario"]["host_a_chainage_mm"],
    )


def crossover_pair(module, document, directory):
    """Resolve the existing integrated cutting and solid record identities."""
    config, old, _, issues, outline = CROSSOVER._selected_plan(
        module, document, directory,
    )
    assert not module.preflight_blocking_report(issues), issues
    index = module.production_record_index_for_set(document, SELECTED.SET_ID)
    catalogue = module.hydrate_production_index_records(document, index)
    records = module.filter_production_records_by_selected_scope(
        catalogue, old["selected_scope"],
    )
    assert len(records) == 2
    assert {record["category"] for record in records} == {
        module.EXPORT_CATEGORY_CUTTING, module.EXPORT_CATEGORY_SOLID,
    }
    assert {record["route_id"] for record in records} == {"XO-001"}
    assert len({record["record_id"] for record in records}) == 2
    assert outline["record_id"] in {r["record_id"] for r in records}
    return config, old, records, outline


def crossover_witness(module, document):
    return {
        "snapshot": CROSSOVER_HOST._snapshot(module, document),
        "objects": {obj.Name: obj for obj in document.Objects},
        "shapes": {
            obj.Name: obj.Shape for obj in document.Objects
            if "Shape" in obj.PropertiesList and not obj.Shape.isNull()
        },
    }


def assert_crossover_document(module, document, before):
    CROSSOVER_HOST._assert_equal(
        before["snapshot"], CROSSOVER_HOST._snapshot(module, document),
        "Crossover four-format export",
    )
    for name, obj in before["objects"].items():
        assert document.getObject(name) is obj, name
    for name, shape in before["shapes"].items():
        assert document.getObject(name).Shape.isSame(shape), name


def reopen_crossover(module, document):
    document.save()
    saved = CROSSOVER_HOST._snapshot(module, document)
    path = document.FileName
    App.closeDocument(document.Name)
    document = App.openDocument(path)
    document.UndoMode = 1
    CROSSOVER_HOST._assert_persistent_reopen_equal(
        saved, CROSSOVER_HOST._snapshot(module, document),
    )
    return document


def prepared_plan(module, document, parent, manifest=True, *,
                  crossover=False, legacy=False):
    from tracktemplate.application.selected_export_set import (
        prepare_selected_export_plan,
    )

    if crossover:
        config, old, pair, _ = crossover_pair(module, document, parent)
    else:
        assert not legacy
        config, old, _, issues, outline, solid, _ = SELECTED._selected_plan(
            module, document, parent,
        )
        assert not module.preflight_blocking_report(issues), issues
        pair = [outline, solid]
    config.update(create_manifest=manifest, overwrite_existing=False)
    config["formats"] = {name: True for name in CORE.FORMATS}
    records, skipped = module.selected_export_records_for_formats(
        pair, config,
    )
    before = CORE.input_state((records, config))
    if legacy:
        plan = module.plan_selected_production_export(
            records, config, SELECTED.SET_ID, old["selected_scope"],
        )
    else:
        plan = prepare_selected_export_plan(
            records, config, SELECTED.SET_ID, old["selected_scope"],
            plan_export=module.plan_selected_production_export,
        )
    assert CORE.input_state((records, config)) == before
    assert len(plan["tasks"]) == 4 and not skipped
    assert {task["format"] for task in plan["tasks"]} == CORE.FORMATS
    child = parent if legacy else Path(plan["output_directory"])
    if not legacy:
        assert child.parent == parent and not child.exists()
    assert all(Path(task["path"]).parent == child for task in plan["tasks"])
    assert bool(plan.get("manifest_path")) is manifest
    if crossover:
        settings = module.settings_for_template_set(document, SELECTED.SET_ID)
        index = module.production_record_index_for_set(
            document, SELECTED.SET_ID,
        )
        catalogue = module.hydrate_production_index_records(document, index)
        validation_records = module.selected_export_validation_records(
            catalogue, pair, old["selected_scope"],
        )
        issues = module.run_production_preflight(
            document, validation_records, records,
            module.selected_export_preflight_config(config, plan),
            SELECTED.SET_ID, module.read_section_config(settings),
            module.read_registration_config(settings),
            module.read_template_assembly_config(settings),
            settings_obj=settings, plan=plan, include_export_checks=True,
            probe_export_bounds=True,
            filename_issues_override=module.selected_export_filename_issues(
                plan, config, SELECTED.SET_ID,
            ),
        )
        assert not module.preflight_blocking_report(issues), issues
    return config, plan, skipped


def crossover_output(module, plan, child):
    """Check format-to-record and CSV associations without new normalisation."""
    snapshot = CORE.output_state(module, child)
    assert len(plan["tasks"]) == 4
    assert {task["format"] for task in plan["tasks"]} == CORE.FORMATS
    associations = []
    with Path(plan["manifest_path"]).open(
        newline="", encoding="utf-8-sig",
    ) as stream:
        reader = csv.DictReader(stream)
        assert tuple(reader.fieldnames) == tuple(module.EXPORT_MANIFEST_FIELDS)
        rows = list(reader)
    assert len(rows) == 4
    for task in plan["tasks"]:
        assert len(task["records"]) == 1
        record = task["records"][0]
        assert record["route_id"] == "XO-001"
        expected_category = (
            module.EXPORT_CATEGORY_CUTTING
            if task["format"] in {"dxf", "svg"}
            else module.EXPORT_CATEGORY_SOLID
        )
        assert record["category"] == expected_category
        matches = [row for row in rows
                   if row["Export format"] == task["format"].upper()]
        assert len(matches) == 1
        row = matches[0]
        assert row["Generated object name"] == record["source_name"]
        assert row["Generated object role"] == record["role"]
        assert row["Template-set identifier"] == SELECTED.SET_ID
        assert row["Full export path"] == task["path"]
        assert row["Export filename"] == Path(task["path"]).name
        assert row["Export status"] == "Success" and not row["Error message"]
        associations.append({
            "format": task["format"], "record_id": record["record_id"],
            "source_name": record["source_name"],
        })
    assert len({row["record_id"] for row in associations}) == 2
    return {
        "content_by_path": snapshot["files"]["content_by_path"],
        "metrics": snapshot["metrics"], "record_associations": associations,
    }


def crossover_previous_output(module, document, directory):
    """Compare the retained selected command with the same crossover pair."""
    directory.mkdir()
    config, plan, skipped = prepared_plan(
        module, document, directory, crossover=True, legacy=True,
    )
    before = crossover_witness(module, document)
    inputs = CORE.input_state((config, plan))
    registry = dict(App.listDocuments())
    active, internal = App.ActiveDocument, App.activeDocument()
    binding = module.run_selected_production_export
    module.run_selected_production_export = binding.original_command
    try:
        summary = CROSSOVER._export(module, document, config, plan, skipped)
    finally:
        module.run_selected_production_export = binding
    assert summary["successful_files"] == 5 and not summary["failed_files"]
    assert_crossover_document(module, document, before)
    assert CORE.input_state((config, plan)) == inputs
    assert dict(App.listDocuments()) == registry
    assert App.ActiveDocument is active and App.activeDocument() is internal
    return crossover_output(module, plan, directory)


def files_state(parent):
    return {
        str(path.relative_to(parent)): (
            path.stat().st_ino, path.stat().st_mtime_ns, CORE.sha256(path),
        )
        for path in parent.rglob("*") if path.is_file()
    }


def run_case(module, document, parent, *, manifest=True, failure=None,
             crossover=False):
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
        module, document, parent, manifest, crossover=crossover,
    )
    child = Path(plan["output_directory"])
    before = (crossover_witness(module, document) if crossover
              else PREVIOUS.document_witness(module, document))
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
    if crossover:
        assert_crossover_document(module, document, before)
    else:
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
        if crossover:
            result.update(crossover_output(module, plan, child))
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
                 Path(PREVIOUS.__file__), Path(SELECTED.__file__),
                 Path(CROSSOVER.__file__), Path(CROSSOVER_HOST.__file__)):
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
        App.closeDocument(document.Name)
        document = None
        document = prepare_crossover(module, directory)
        crossover = {
            "legacy": crossover_previous_output(
                module, document, directory / "crossover-legacy",
            ),
        }
        for name in ("success", "repeat"):
            crossover[name] = run_case(
                module, document, directory / ("crossover-" + name),
                crossover=True,
            )
        for key in ("content_by_path", "metrics", "record_associations"):
            assert crossover["legacy"][key] == crossover["success"][key]
            assert crossover["success"][key] == crossover["repeat"][key]
        crossover["legacy_and_same_state_repeat_equivalence"] = True
        document = reopen_crossover(module, document)
        crossover["save_reopen_unchanged"] = True
        crossover["scope"] = (
            "XO-001 integrated template cutting/solid pair; no chair solids "
            "or output-byte comparison across save/reopen"
        )
        receipt["crossover"] = crossover
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
