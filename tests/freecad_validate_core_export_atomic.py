#!/usr/bin/env python3
"""Prove complete Core output publication on a copied native document.

The actual exporters and qualified filesystem are exercised. This finite proof
makes no durability, crash recovery, arbitrary interruption or rights claim.
"""

import csv
import dataclasses
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from unittest import mock

import FreeCAD as App
import Part


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
from tools.validate_dependency_manifest import validate_document  # noqa: E402

SENTINEL = "Core export atomic set FreeCAD validation passed"
DEPENDENCY_FILENAME = "Core_Dependency_Manifest.json"


def dependency_manifest_witness(path, expected_paths, generation_origin):
    """Check emitted schema, actual file/source hashes and uncleared rights."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert not validate_document(payload)
    assert validate_document(payload, require_project_cleared=True)
    assert payload["schema_version"] == 1
    assert payload["intended_uses"] == ["private-development"]
    assert payload["project_status"]["status"] == "unknown"
    artifacts = payload["subject"]["artifacts"]
    assert [item["path"] for item in artifacts] == [
        Path(item).name for item in expected_paths
    ]
    assert DEPENDENCY_FILENAME not in {item["path"] for item in artifacts}
    for item in artifacts:
        artifact = path.parent / item["path"]
        assert item["format"] == artifact.suffix[1:]
        assert item["sha256"] == helpers.sha256(artifact)
    dependencies = {item["identifier"]: item
                    for item in payload["dependencies"]}
    expected_ids = {
        "tracktemplate:core-canonical-input",
        "tracktemplate:core-generator-source",
        "tracktemplate:core-host-exporters",
        "legacy.user-input-and-persisted-parametric-state",
        "legacy.retained-freecad-shapes-and-document-objects",
        "legacy.dxf-svg-stl-step-export-artifacts",
        "legacy.csv-manifests-reports-and-production-records",
        "legacy.output-names-labels-and-boilerplate",
        "legacy.user-assets-fonts-and-external-exporters",
        "legacy.b14-b15-version-and-release-boundary",
    }
    assert set(dependencies) == expected_ids
    assert len(payload["dependencies"]) == len(expected_ids)
    lineage = json.loads((ROOT / (
        "reference/lineage/phase1-other-snc-legacy-lineage.json"
    )).read_text())
    entries = {item["entry_id"]: item for scope in lineage["scopes"]
               for item in scope["entries"]}
    for identifier in expected_ids:
        item = dependencies[identifier]
        assert item["output_affecting"] is True
        assert item["project_status"]["status"] in {
            "unknown", "reference-only",
        }
        if identifier.startswith("legacy."):
            assert item["classifications"] == entries[identifier][
                "classifications"
            ]
            assert item["project_status"]["status"] == entries[identifier][
                "current_project_status"
            ]
    canonical = dependencies["tracktemplate:core-canonical-input"]
    signature = payload["subject"]["canonical_model_sha256"]
    assert canonical["source"]["evidence_sha256"] == signature
    assert signature != "0" * 64
    assert any("Persisted generation origin: " + generation_origin in text
               for text in canonical["conditions"])
    generator = dependencies["tracktemplate:core-generator-source"]
    prefix = "Installed generator source inventory: "
    assert generator["source"]["locator"].startswith(prefix)
    sources = json.loads(generator["source"]["locator"][len(prefix):])
    assert sources and len({item["path"] for item in sources}) == len(sources)
    for item in sources:
        assert helpers.sha256(ROOT / item["path"]) == item["sha256"]
    digest = hashlib.sha256(json.dumps(
        sources, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()
    assert payload["subject"]["generator"]["version"] == "10.2A8A7B16"
    assert payload["subject"]["generator"]["source_sha256"] == digest
    assert generator["source"]["evidence_sha256"] == digest
    return {
        "path": str(path), "sha256": helpers.sha256(path),
        "artifact_count": len(artifacts), "dependency_count": len(dependencies),
        "canonical_model_sha256": signature, "generator_source_sha256": digest,
        "schema_and_actual_hashes_verified": True,
        "project_clearance_refused": True,
        "persisted_generation_origin": generation_origin,
    }



def inject_duplicate_track_key(settings):
    """Install real invalid input before measurement; return fixture cleanup."""
    previous = settings.TrackConfigurationJSON
    previous_state = tuple(settings.State)
    tracks = json.loads(previous)
    assert isinstance(tracks, list) and tracks and isinstance(tracks[0], dict)
    key = next(iter(tracks[0]))
    duplicate = json.dumps(key) + ":" + json.dumps(tracks[0][key]) + ","
    malformed = previous.replace("{", "{" + duplicate, 1)
    assert malformed != previous and json.loads(malformed) == tracks
    settings.TrackConfigurationJSON = malformed

    def restore():
        settings.TrackConfigurationJSON = previous
        if "Touched" not in previous_state:
            settings.purgeTouched()
        assert tuple(settings.State) == previous_state
        assert settings.TrackConfigurationJSON == previous

    return restore


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
        dependency_manifest=True,
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
    assert plan["dependency_manifest_path"] == str(child / DEPENDENCY_FILENAME)
    for task in tasks:
        for record in task["records"]:
            source = document.getObject(record["source_name"])
            assert record["shape"].exportBrepToString() == (
                source.Shape.copy().exportBrepToString()
            )
    return config, plan


def run_case(module, document, parent, *, manifest=True, failure=None):
    parent.mkdir()
    old = parent / "previous-complete-set"
    old.mkdir()
    (old / "operator-output.svg").write_text("preserve previous complete set\n")
    (parent / "operator-output.svg").write_text("preserve root output\n")
    old_state = files_state(parent)
    config, plan = prepared_plan(module, document, parent, manifest)
    if failure == "missing-plan":
        plan.pop("dependency_manifest_path")
    shape_failure = failure in {
        "foreign-shape", "translated-shape", "rotated-shape", "reversed-shape",
    }
    if shape_failure:
        tasks = [dict(task, records=list(task["records"]))
                 for task in plan["tasks"]]
        shape = tasks[0]["records"][0]["shape"].copy()
        if failure == "foreign-shape":
            shape = Part.makeBox(1, 2, 3)
        elif failure == "translated-shape":
            shape.translate(App.Vector(1, 0, 0))
        elif failure == "rotated-shape":
            shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1)
        else:
            shape.reverse()
        tasks[0]["records"][0] = dict(tasks[0]["records"][0], shape=shape)
        plan = dict(plan, tasks=tasks)
    child = Path(plan["output_directory"])
    settings = next(obj for obj in document.Objects
                    if getattr(obj, "GeneratedRole", None) == "Settings"
                    and getattr(obj, "TemplateSetID", None) == "SET-001")
    restore_input = (inject_duplicate_track_key(settings)
                     if failure == "malformed-inventory" else None)
    baseline = helpers.document_state(module, document)
    inputs = helpers.input_state((config, plan))
    record_shapes = [(record, record["shape"]) for task in plan["tasks"]
                     for record in task["records"]]
    objects = {obj.Name: obj for obj in document.Objects}
    shapes = {obj.Name: obj.Shape for obj in document.Objects
              if "Shape" in obj.PropertiesList and not obj.Shape.isNull()}
    registry = dict(App.listDocuments())
    active = App.ActiveDocument
    internal_active = App.activeDocument()
    calls = []
    manifest_calls = []
    files_open_calls = []
    original = module.run_production_export
    generation_origin = settings.GeneratorVersion
    assert callable(original.prepare_dependency_manifest)

    class FaultFiles(CoreLayoutExportSetFiles):
        def open(self, *args):
            files_open_calls.append(True)
            return super().open(*args)

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
        prepare_dependency_manifest=(
            None if failure == "missing-inventory"
            else original.prepare_dependency_manifest
        ),
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
    assert summary["successful_files"] == (5 + int(manifest) if published else 0)
    assert summary["output_directory"] == str(child if published else parent)
    assert summary["manifest_path"] == (
        plan["manifest_path"] if published and manifest else ""
    )
    inventory_failure = failure in {
        "malformed-inventory", "missing-inventory", "missing-plan",
        "foreign-shape", "translated-shape", "rotated-shape", "reversed-shape",
    }
    expected_diagnostic = {
        "malformed-inventory": "duplicate JSON key",
        "missing-inventory": "dependency inventory is unavailable",
        "missing-plan": "dependency manifest is missing from the plan",
        "foreign-shape": "planned shape differs from current bound source copy",
        "translated-shape": "planned shape placement differs from current bound source",
        "rotated-shape": "planned shape placement differs from current bound source",
        "reversed-shape": "planned shape differs from current bound source copy",
    }.get(failure)
    if expected_diagnostic:
        assert any(expected_diagnostic in value for value in summary["failures"])
    assert len(files_open_calls) == (0 if inventory_failure else 1)
    assert len(calls) == (0 if inventory_failure else 4)
    assert len(manifest_calls) == int(
        manifest and failure != "preparation" and not inventory_failure
    )
    assert summary.get("dependency_manifest_path", "") == (
        plan["dependency_manifest_path"] if published else ""
    )
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
    dependency = None
    if published:
        names = {Path(task["path"]).name for task in plan["tasks"]}
        names.add(DEPENDENCY_FILENAME)
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
        expected_paths = [task["path"] for task in plan["tasks"]]
        if manifest:
            expected_paths.append(plan["manifest_path"])
        dependency = dependency_manifest_witness(
            plan["dependency_manifest_path"], expected_paths, generation_origin,
        )
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
    for record, shape in record_shapes:
        assert record["shape"] is shape
    assert dict(App.listDocuments()) == registry
    assert App.ActiveDocument is active and App.activeDocument() is internal_active
    for name, obj in objects.items():
        assert document.getObject(name) is obj
    for name, shape in shapes.items():
        assert document.getObject(name).Shape.isSame(shape)
    if restore_input is not None:
        restore_input()
    return {
        "case": failure or "success", "manifest_requested": manifest,
        "summary": {key: value for key, value in summary.items() if key != "results"},
        "task_record_ids": [[record["record_id"] for record in task["records"]]
                            for task in plan["tasks"]],
        "output": output, "csv_rows": csv_rows, "old_outputs_unchanged": True,
        "dependency_manifest": dependency,
        "source_copied_snapshot_binding_verified": not shape_failure,
        "changed_shape_refused": shape_failure,
        "source_and_record_shapes_unchanged": True,
        "inventory_refusal_before_files_open": inventory_failure,
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
    for relative in (
        "tests/freecad_validate_core_export_atomic.py",
        "tools/validate_dependency_manifest.py",
        "reference/lineage/phase1-other-snc-legacy-lineage.json",
    ):
        sources[relative] = helpers.sha256(ROOT / relative)
    report = {"profile": helpers.PROFILE, "routing": routing,
              "fixture_sha256": helpers.sha256(fixture), "source_sha256": sources,
              "proof_boundary": "Copied B14 fixture at the B16 export boundary; "
              "this does not prove B16 regeneration of the input."}
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
            # CSV paths and the new JSON are separately verified above.
            assert {name: value for name, value in actual.items()
                    if not name.endswith(".csv")
                    and name != DEPENDENCY_FILENAME} == {
                name: value for name, value in expected.items() if not name.endswith(".csv")
            }
        report["success"] = successes
        repeat = run_case(module, document, directory / "repeat")
        assert repeat["dependency_manifest"]["canonical_model_sha256"] == (
            successes[0]["dependency_manifest"]["canonical_model_sha256"]
        )
        assert repeat["dependency_manifest"]["generator_source_sha256"] == (
            successes[0]["dependency_manifest"]["generator_source_sha256"]
        )
        report["repeat"] = repeat
        report["failures"] = [run_case(module, document, directory / failure, failure=failure)
                              for failure in (
                                  "preparation", "collision", "publication",
                                  "postpublication", "malformed-inventory",
                                  "missing-inventory", "missing-plan",
                                  "foreign-shape", "translated-shape",
                                  "rotated-shape", "reversed-shape",
                              )]
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
        for relative in sources:
            after[relative] = helpers.sha256(ROOT / relative)
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
