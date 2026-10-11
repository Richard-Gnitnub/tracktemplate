#!/usr/bin/env python3
"""Prove complete Core output publication on a copied native document.

The actual exporters and qualified filesystem are exercised. This finite proof
makes no durability, crash recovery, arbitrary interruption or rights claim.
"""

import csv
import dataclasses
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from unittest import mock

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_SPEC = importlib.util.spec_from_file_location(
    "core_export_native_helpers", ROOT / "tests/freecad_validate_core_export_staging.py"
)
helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)

from tracktemplate.adapters.export.core_layout_set import (  # noqa: E402
    CoreLayoutExportSetFiles,
)
from tracktemplate.application.core_export_set import (  # noqa: E402
    prepare_core_export_plan,
)

SENTINEL = "Core export atomic set FreeCAD validation passed"


def files_state(directory):
    return {
        str(path.relative_to(directory)): (
            path.stat().st_ino, path.stat().st_mtime_ns, helpers.sha256(path),
        )
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def prepared_plan(module, document, parent, manifest):
    config, _ = helpers.prepared_plan(module, document, parent)
    config.update(create_manifest=manifest, overwrite_existing=False)
    index = module.production_record_index_for_set(document, "SET-001")
    records = module.hydrate_production_index_records(document, index)
    before = helpers.input_state((records, config))
    plan = prepare_core_export_plan(
        records, config, "SET-001", plan_export=module.plan_production_export,
    )
    assert helpers.input_state((records, config)) == before
    tasks = []
    formats = set()
    for task in plan["tasks"]:
        if task["format"] not in formats:
            tasks.append(task)
            formats.add(task["format"])
    assert formats == helpers.FORMATS
    plan = dict(plan, tasks=tasks)
    child = Path(plan["output_directory"])
    assert child.parent == parent and not child.exists()
    assert all(Path(task["path"]).parent == child for task in tasks)
    assert bool(plan.get("manifest_path")) is manifest
    return config, plan


def run_case(module, document, parent, *, manifest=True, failure=None):
    parent.mkdir()
    old = parent / "previous-complete-set"
    old.mkdir()
    (old / "operator-output.svg").write_text("preserve previous complete set\n")
    (parent / "operator-output.svg").write_text("preserve root output\n")
    old_state = files_state(parent)
    config, plan = prepared_plan(module, document, parent, manifest)
    child = Path(plan["output_directory"])
    baseline = helpers.document_state(module, document)
    inputs = helpers.input_state((config, plan))
    objects = {obj.Name: obj for obj in document.Objects}
    shapes = {obj.Name: obj.Shape for obj in document.Objects
              if "Shape" in obj.PropertiesList and not obj.Shape.isNull()}
    registry = dict(App.listDocuments())
    active = App.ActiveDocument
    internal_active = App.activeDocument()
    calls = []
    manifest_calls = []
    original = module.run_production_export

    class FaultFiles(CoreLayoutExportSetFiles):
        def publish(self):
            assert not child.exists()
            if failure == "collision":
                child.mkdir()
                (child / "foreign.txt").write_text("preserve collision owner\n")
            if failure == "publication":
                raise OSError("controlled native publication failure")
            super().publish()
            if failure == "postpublication":
                raise OSError("controlled native postpublication diagnostic")

    def dispatch(scratch, task, path):
        assert scratch is not document and scratch.Temporary
        assert task is plan["tasks"][len(calls)]
        assert Path(path).parent != child and not child.exists()
        assert all(files_state(parent).get(name) == value
                   for name, value in old_state.items())
        calls.append(task["format"])
        if failure == "preparation" and len(calls) == len(plan["tasks"]):
            raise RuntimeError("controlled native final-format failure")
        return module.dispatch_freecad_export(scratch, task, path)

    def write_manifest(path, rows):
        assert not child.exists()
        assert Path(path).parent != child
        manifest_calls.append(path)
        return original.write_export_manifest(path, rows)

    export = dataclasses.replace(
        original, export_files_factory=FaultFiles,
        dispatch_export_task=dispatch, write_export_manifest=write_manifest,
    )
    build_rows = original.build_manifest_rows
    if not manifest:
        build_rows = mock.Mock(side_effect=AssertionError("CSV was not selected"))
        export = dataclasses.replace(export, build_manifest_rows=build_rows)
    summary = export(document, plan, config, "SET-001", {}, {}, {}, {})
    published = failure in {None, "postpublication"}
    assert summary["publication_state"] == (
        "published" if published else "not-published"
    )
    assert summary["successful_files"] == (4 + int(manifest) if published else 0)
    assert summary["output_directory"] == str(child if published else parent)
    assert summary["manifest_path"] == (
        plan["manifest_path"] if published and manifest else ""
    )
    assert len(calls) == 4
    assert len(manifest_calls) == int(manifest and failure != "preparation")
    assert summary["manifest_requested"] is manifest
    for item, task in zip(summary["results"], plan["tasks"]):
        assert item["task"] is task and item["success"] is published
    if failure:
        assert summary["failed_files"] > 0 and summary["failures"]
    else:
        assert summary["failed_files"] == 0 and not summary["failures"]
    if not manifest:
        build_rows.assert_not_called()
    csv_rows = None
    if published:
        names = {Path(task["path"]).name for task in plan["tasks"]}
        if manifest:
            names.add(Path(plan["manifest_path"]).name)
        assert {path.name for path in child.iterdir()} == names
        if manifest:
            with Path(plan["manifest_path"]).open(newline="", encoding="utf-8-sig") as stream:
                rows = list(csv.DictReader(stream))
            csv_rows = rows
            expected_paths = {task["path"] for task in plan["tasks"]}
            actual_paths = {row["Full export path"] for row in rows}
            assert actual_paths == expected_paths
        output = helpers.output_state(module, child)
    else:
        output = None
        if failure == "collision":
            assert {path.name for path in child.iterdir()} == {"foreign.txt"}
            assert (child / "foreign.txt").read_text() == "preserve collision owner\n"
        else:
            assert not child.exists()
    assert not list(parent.glob(".tracktemplate_core_export_set_*"))
    assert all(files_state(parent).get(name) == value
               for name, value in old_state.items())
    assert helpers.document_state(module, document) == baseline
    assert helpers.input_state((config, plan)) == inputs
    assert dict(App.listDocuments()) == registry
    assert App.ActiveDocument is active and App.activeDocument() is internal_active
    for name, obj in objects.items():
        assert document.getObject(name) is obj
    for name, shape in shapes.items():
        assert document.getObject(name).Shape.isSame(shape)
    return {
        "case": failure or "success", "manifest_requested": manifest,
        "summary": {key: value for key, value in summary.items() if key != "results"},
        "task_record_ids": [[record["record_id"] for record in task["records"]]
                            for task in plan["tasks"]],
        "output": output, "csv_rows": csv_rows, "old_outputs_unchanged": True,
        "editable_state_identity_history_unchanged": True,
        "registry_active_restored": True,
    }


def validate():
    assert not App.listDocuments(), "Use an empty isolated qualified host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = Path(os.environ.get(
        "TRACKTEMPLATE_CORE_EXPORT_ATOMIC_RUN_DIR",
        str(ROOT / "tmp/core-export-atomic/native-runs" / stamp),
    ))
    directory.mkdir(parents=True, exist_ok=False)
    contract = json.loads(helpers.FIXTURE_CONTRACT.read_text())
    fixture = ROOT / contract["fixture"]["path"]
    assert helpers.sha256(fixture) == contract["fixture"]["sha256"]
    target = directory / "copied-core.FCStd"
    shutil.copy2(fixture, target)
    module, routing = helpers.load_product(atomic=True)
    assert module.run_production_export.export_files_factory is CoreLayoutExportSetFiles
    document = App.openDocument(str(target))
    document.UndoMode = 1
    original_datetime = module.datetime.datetime
    module.datetime.datetime = helpers.FixedDateTime
    sources = helpers.source_hashes()
    sources["tests/freecad_validate_core_export_atomic.py"] = helpers.sha256(__file__)
    report = {"profile": helpers.PROFILE, "routing": routing,
              "fixture_sha256": helpers.sha256(fixture), "source_sha256": sources}
    try:
        baseline = helpers.document_state(module, document)
        legacy = helpers.run_success(module, document, directory / "legacy", legacy=True)
        successes = [run_case(module, document, directory / ("success-" + str(csv_on)),
                              manifest=csv_on) for csv_on in (True, False)]
        with next((directory / "legacy").glob("*.csv")).open(
            newline="", encoding="utf-8-sig",
        ) as stream:
            legacy_rows = list(csv.DictReader(stream))
        for success in successes:
            if success["manifest_requested"]:
                child = success["summary"]["output_directory"]
                expected_rows = [dict(row, **{
                    "Full export path": str(Path(child) / Path(row["Full export path"]).name),
                }) for row in legacy_rows]
                assert success["csv_rows"] == expected_rows
            else:
                assert success["csv_rows"] is None
            assert success["task_record_ids"] == legacy["task_record_ids"]
            assert success["output"]["metrics"] == legacy["metrics"]
            expected = legacy["files"]["content_by_path"]
            actual = success["output"]["files"]["content_by_path"]
            # CSV is separately checked for exact final paths and identities.
            assert {name: value for name, value in actual.items() if not name.endswith(".csv")} == {
                name: value for name, value in expected.items() if not name.endswith(".csv")
            }
        report["success"] = successes
        report["failures"] = [run_case(module, document, directory / failure, failure=failure)
                              for failure in ("preparation", "collision", "publication", "postpublication")]
        assert helpers.document_state(module, document) == baseline
        document.save()
        saved = helpers.document_state(module, document)
        App.closeDocument(document.Name)
        document = App.openDocument(str(target))
        document.UndoMode = 1
        reopened = helpers.document_state(module, document)
        assert reopened["canonical_json"] == saved["canonical_json"]
        assert reopened["semantic"] == saved["semantic"]
        report["save_reopen_exact_canonical_state"] = True
        after = helpers.source_hashes()
        after["tests/freecad_validate_core_export_atomic.py"] = helpers.sha256(__file__)
        assert after == sources
        assert helpers.sha256(fixture) == contract["fixture"]["sha256"]
        report["result"] = "PASS"
        (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(SENTINEL)
    except BaseException:
        (directory / "failure.txt").write_text(traceback.format_exc())
        raise
    finally:
        module.datetime.datetime = original_datetime
        App.closeDocument(document.Name)


if __name__ in {"__main__", "freecad_validate_core_export_atomic"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
