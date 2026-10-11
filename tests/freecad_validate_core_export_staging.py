#!/usr/bin/env python3
"""Prove Core staged export on a copied native plain-line document.

This checks the generation barrier, actual format output and document state.
It does not establish a whole-set publication or recovery guarantee.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import traceback

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.adapters.export.core_layout_files import (
    CoreLayoutExportFiles,
)  # noqa: E402
from tools.freecad_bridge import ordinary_track_recipe as recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_export_recipe as artifacts  # noqa: E402
from tools.freecad_bridge.freecad_export_metrics import format_export_metrics  # noqa: E402


SENTINEL = "Core export staging FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
FIXTURE_CONTRACT = (
    ROOT / "reference/contracts/phase1-chair-analysis-persistence.json"
)
FORMATS = {"dxf", "svg", "stl", "step"}


class FixedDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 11, 12, 0, 0, tzinfo=tz)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_product():
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["matched_profile_id"] == PROFILE
    product, bootstrap = launcher["_load_foundation"](ROOT)
    session, routing = launcher["_load_modular_transition_workflow"](
        ROOT,
        product,
        bootstrap,
    )
    assert routing["route"] == "modular"
    export_routing = session.core_layout_export_routing_record()
    assert export_routing["contract_id"] == (
        "tracktemplate:phase9b:core-layout-export-staging:1"
    )
    assert export_routing["command_name"] == "run_staged_core_layout_export"
    assert export_routing["mixed_route"] is False
    assert (
        session.module.run_production_export.export_files_factory
        is CoreLayoutExportFiles
    )
    return session.module, export_routing


def document_state(module, document):
    """Keep exact canonical JSON as well as the established geometry witness."""
    return {
        "semantic": recipe.ordinary_track_document_snapshot(module, document),
        "canonical_json": {
            obj.Name: {
                name: getattr(obj, name)
                for name in obj.PropertiesList
                if name.endswith("JSON")
            }
            for obj in document.Objects
        },
        "objects": [
            (obj.Name, obj.TypeId, tuple(obj.State))
            for obj in document.Objects
        ],
        "history": {
            "undo": document.UndoCount,
            "redo": document.RedoCount,
            "undo_names": list(document.UndoNames),
            "redo_names": list(document.RedoNames),
        },
    }


def prepared_plan(module, document, directory):
    index = module.production_record_index_for_set(document, "SET-001")
    records = module.hydrate_production_index_records(document, index)
    assert records and all(record["record_id"] for record in records)
    config = module.default_production_export_config()
    config.update(
        {
            "enabled": True,
            "output_directory": str(directory),
            "overwrite_existing": True,
            "create_combined_files": False,
        }
    )
    complete = module.plan_production_export(records, config, "SET-001")
    tasks = []
    selected = set()
    for task in complete["tasks"]:
        if task["format"] not in selected:
            tasks.append(task)
            selected.add(task["format"])
    assert selected == FORMATS and len(tasks) == 4
    plan = dict(complete, tasks=tasks)
    return config, plan


def _export(module, document, config, plan, *, legacy=False, dispatch=None):
    args = (document, plan, config, "SET-001", {}, {}, {}, {})
    if legacy:
        return api.run_core_layout_export(
            *args,
            exporter_override=dispatch,
            execute_export_tasks=module.execute_export_tasks,
            build_manifest_rows=module.build_manifest_rows,
            write_export_manifest=module.write_export_manifest,
            failed_export_report=module._failed_export_report,
            skipped_export_report=module._skipped_export_report,
        )
    return module.run_production_export(*args, exporter_override=dispatch)


def output_state(module, directory):
    snapshot = artifacts.export_directory_snapshot(directory)
    metrics = format_export_metrics(
        module, directory, snapshot, recipe.shape_summary
    )
    assert {value["format"] for value in metrics.values()} == FORMATS
    assert all(item["bytes"] > 0 for item in snapshot["files"].values())
    return {"files": snapshot, "metrics": metrics}


def input_state(value):
    """Observe native shape inputs without copying or rounding them."""
    if hasattr(value, "exportBrepToString"):
        return {
            "shape_brep_sha256": hashlib.sha256(
                value.exportBrepToString().encode("utf-8")
            ).hexdigest()
        }
    if isinstance(value, dict):
        return {key: input_state(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(input_state(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(input_state(item) for item in value))
    return value


def run_success(module, document, directory, *, legacy=False):
    directory.mkdir()
    config, plan = prepared_plan(module, document, directory)
    before = document_state(module, document)
    objects = {obj.Name: obj for obj in document.Objects}
    shapes = {
        obj.Name: obj.Shape
        for obj in document.Objects
        if "Shape" in obj.PropertiesList and not obj.Shape.isNull()
    }
    inputs = input_state((config, plan))
    summary = _export(module, document, config, plan, legacy=legacy)
    assert summary["successful_files"] == 5 and summary["failed_files"] == 0
    assert summary["manifest_path"] == plan["manifest_path"]
    assert document_state(module, document) == before
    assert input_state((config, plan)) == inputs
    for item, task in zip(summary["results"], plan["tasks"]):
        assert item["task"] is task and item["success"] is True
    for name, obj in objects.items():
        assert document.getObject(name) is obj
    for name, shape in shapes.items():
        assert document.getObject(name).Shape.isSame(shape), name
    result = output_state(module, directory)
    result["summary"] = {
        key: summary[key]
        for key in (
            "successful_files",
            "failed_files",
            "skipped_objects",
            "formats",
            "manifest_requested",
        )
    }
    result["task_record_ids"] = [
        [record["record_id"] for record in task["records"]]
        for task in plan["tasks"]
    ]
    return result


def run_failure(module, document, directory, *, existing):
    directory.mkdir()
    config, plan = prepared_plan(module, document, directory)
    finals = [Path(task["path"]) for task in plan["tasks"]] + [
        Path(plan["manifest_path"])
    ]
    if existing:
        for path in finals:
            path.write_bytes(("preserve-" + path.name).encode())
    before_files = {
        path.name: (
            path.stat().st_ino,
            path.stat().st_mtime_ns,
            path.read_bytes(),
        )
        for path in finals
        if path.exists()
    }
    before = document_state(module, document)
    calls = []

    def fail_last(doc, task, path):
        assert task is plan["tasks"][len(calls)]
        calls.append(task["format"])
        if len(calls) == len(plan["tasks"]):
            raise RuntimeError("controlled native final-format failure")
        module.dispatch_freecad_export(doc, task, path)

    summary = _export(module, document, config, plan, dispatch=fail_last)
    assert len(calls) == 4
    assert summary["successful_files"] == 0 and summary["failed_files"] > 0
    assert summary["manifest_path"] == "" and summary["formats"] == []
    assert "controlled native final-format failure" in "\n".join(
        summary["failure_details"]
    )
    assert all(not item["success"] for item in summary["results"])
    after_files = {
        path.name: (
            path.stat().st_ino,
            path.stat().st_mtime_ns,
            path.read_bytes(),
        )
        for path in finals
        if path.exists()
    }
    assert after_files == before_files
    assert len(list(directory.iterdir())) == len(before_files)
    assert document_state(module, document) == before
    return {
        "existing": existing,
        "successful_files": 0,
        "final_files_unchanged": True,
        "document_unchanged": True,
    }


def validate():
    assert not App.listDocuments(), "Use an empty isolated qualified host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    directory = Path(
        os.environ.get(
            "TRACKTEMPLATE_CORE_EXPORT_STAGING_RUN_DIR",
            str(ROOT / "tmp/core-export-staging/native-runs" / stamp),
        )
    )
    directory.mkdir(parents=True, exist_ok=False)
    contract = json.loads(FIXTURE_CONTRACT.read_text())
    fixture = ROOT / contract["fixture"]["path"]
    assert sha256(fixture) == contract["fixture"]["sha256"]
    target = directory / "copied-core.FCStd"
    shutil.copy2(fixture, target)
    module, routing = load_product()
    document = App.openDocument(str(target))
    document.UndoMode = 1
    original_datetime = module.datetime.datetime
    module.datetime.datetime = FixedDateTime
    report = {
        "profile": PROFILE,
        "routing": routing,
        "fixture_sha256": sha256(fixture),
    }
    try:
        baseline = document_state(module, document)
        legacy = run_success(
            module, document, directory / "legacy", legacy=True
        )
        staged = run_success(module, document, directory / "staged")
        assert legacy["summary"] == staged["summary"]
        assert legacy["task_record_ids"] == staged["task_record_ids"]
        assert legacy["metrics"] == staged["metrics"]
        assert (
            legacy["files"]["content_by_path"]
            == staged["files"]["content_by_path"]
        )
        report["success"] = {"legacy": legacy, "staged": staged}
        report["failures"] = [
            run_failure(
                module,
                document,
                directory / ("failure-" + str(existing)),
                existing=existing,
            )
            for existing in (False, True)
        ]
        assert document_state(module, document) == baseline
        document.save()
        saved = document_state(module, document)
        App.closeDocument(document.Name)
        document = App.openDocument(str(target))
        document.UndoMode = 1
        reopened = document_state(module, document)
        assert reopened["canonical_json"] == saved["canonical_json"]
        assert reopened["semantic"] == saved["semantic"]
        report["save_reopen_exact_canonical_state"] = True
        report["result"] = "PASS"
        assert sha256(fixture) == contract["fixture"]["sha256"]
        (directory / "result.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(SENTINEL)
    except BaseException:
        (directory / "failure.txt").write_text(traceback.format_exc())
        raise
    finally:
        module.datetime.datetime = original_datetime
        App.closeDocument(document.Name)


if __name__ in {"__main__", "freecad_validate_core_export_staging"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
