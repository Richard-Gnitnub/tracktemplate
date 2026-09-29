"""Prove a bounded XO-001 selected SVG export on a copied curved host.

The output is private-development evidence, not a production-ready assembly
or a Phase 8 exit decision. The fixed B14 fixture is never opened directly.
"""

import csv
import hashlib
import json
import os
import pathlib
import runpy
import shutil
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_export_recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 crossover selected export FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
IDENTIFIER = "XO-001"
SET_ID = "SET-001"
EXPORT_FAULT = "injected selected SVG exporter failure"
COMMIT_FAULT = "injected selected SVG commit failure"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_product():
    assert pathlib.Path(api.__file__).resolve() == ROOT / "tracktemplate/api.py"
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        ROOT, api, contract,
    )
    assert str(session.module.MACRO_VERSION_NUMBER) == "10.2A8A7B15"
    return session.module


def _records(module, document):
    settings = module.settings_for_template_set(document, SET_ID)
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None and index["schema_version"] == 2
    return index["records"]


def _document_state(module, document):
    stored_names = {
        "TemplateSetID", "GeneratedBy", "GeneratedRole", "RouteID",
        "CrossoverID", "ExportSubtype", "ExportCategory",
        "ProductionRecordID", "ProductionRecordIDsJSON",
    }
    objects = []
    for obj in document.Objects:
        properties = tuple(sorted(
            (name, str(getattr(obj, name)))
            for name in obj.PropertiesList
            if name in stored_names or name.endswith("JSON")
        ))
        shape = getattr(obj, "Shape", None)
        geometry = (
            recipe.shape_summary(shape)
            if shape is not None and not shape.isNull() else None
        )
        view = getattr(obj, "ViewObject", None)
        objects.append((
            str(obj.Name), str(obj.TypeId), properties, geometry,
            bool(view.Visibility) if view is not None else None,
        ))
    return {
        "objects": tuple(sorted(objects)),
        "config": recipe.stable(
            module.crossover_config_by_id(document, IDENTIFIER)
        ),
        "records": _records(module, document),
        "history": (
            int(document.UndoCount), int(document.RedoCount),
            tuple(str(name) for name in document.UndoNames),
            tuple(str(name) for name in document.RedoNames),
        ),
        "file_name": str(document.FileName),
    }


def _prepared_copy(module, source, target, chainage_mm):
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    config, _selection = recipe.create_controlled_crossover(
        module, document, chainage_mm,
    )
    assert config["crossover_id"] == IDENTIFIER
    b4 = module.apply_crossover_b4_timbering(document, IDENTIFIER)
    assert b4["applied"] is True
    assert b4["timber_resolution_complete"] is True
    integration = module.create_crossover_host_integration(
        document, IDENTIFIER,
    )
    assert integration["integration_active"] is True
    assert integration["production_ready"] is False
    assert len(_records(module, document)) == 7
    document.save()
    App.closeDocument(document.Name)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    assert module.crossover_host_integration_by_id(
        document, IDENTIFIER,
    ) is not None
    assert module.crossover_config_by_id(
        document, IDENTIFIER,
    )["production_ready"] is False
    assert len(_records(module, document)) == 7
    return document


def _selected_plan(module, document, output_directory):
    index = module.production_record_index_for_set(document, SET_ID)
    catalogue = module.hydrate_production_index_records(document, index)
    integrated = [
        record for record in catalogue
        if record["route_id"] == IDENTIFIER
        and record["subtype"] in {
            module.CROSSOVER_INTEGRATED_SUBTYPE,
            module.CROSSOVER_INTEGRATED_TIMBER_SUBTYPE,
        }
    ]
    assert len(integrated) == 3, [
        (record["record_id"], record["route_id"], record["subtype"])
        for record in catalogue
    ]
    outline = next(
        record for record in integrated
        if record["category"] == module.EXPORT_CATEGORY_CUTTING
    )
    outline_obj = document.getObject(outline["source_name"])
    assert outline_obj is not None
    assert module.object_string_property(
        outline_obj, "GeneratedRole", ""
    ) == module.CROSSOVER_INTEGRATED_OUTLINE_ROLE
    scope = {
        "scope_type": module.SELECTED_EXPORT_SCOPE_OBJECTS,
        "route_id": IDENTIFIER,
        "route_label": "Integrated managed crossover",
        "selected_objects": [{
            "name": str(outline_obj.Name),
            "record_ids": module.selected_export_object_record_ids(
                outline_obj
            ),
            "generated_role": module.CROSSOVER_INTEGRATED_OUTLINE_ROLE,
            "export_subtype": module.object_string_property(
                outline_obj, "ExportSubtype", "",
            ),
            "route_id": IDENTIFIER,
            "track_number": 0,
            "platform_number": 0,
            "section_number": 0,
            "feature_number": 0,
        }],
    }
    matching = module.filter_production_records_by_selected_scope(
        catalogue, scope,
    )
    assert {record["category"] for record in matching} == {
        module.EXPORT_CATEGORY_SOLID,
        module.EXPORT_CATEGORY_CUTTING,
    }
    assert {record["route_id"] for record in matching} == {IDENTIFIER}

    settings = module.settings_for_template_set(document, SET_ID)
    config = module.read_production_export_config(settings)
    config.update({
        "enabled": True,
        "output_directory": str(output_directory),
        "create_combined_files": False,
        "create_manifest": True,
        "overwrite_existing": False,
        "open_output_directory": False,
        "formats": {
            "dxf": False, "svg": True, "stl": False, "step": False,
        },
    })
    export_records, skipped = module.selected_export_records_for_formats(
        matching, config,
    )
    assert [record["record_id"] for record in export_records] == [
        outline["record_id"]
    ]
    assert len(skipped) == 1
    plan = module.plan_selected_production_export(
        export_records, config, SET_ID, scope,
    )
    assert len(plan["tasks"]) == 1
    assert plan["tasks"][0]["format"] == "svg"
    assert plan["tasks"][0]["records"][0]["record_id"] == (
        outline["record_id"]
    )
    assert plan["manifest_path"]
    validation_records = module.selected_export_validation_records(
        catalogue, matching, scope,
    )
    assert {record["route_id"] for record in validation_records} == {
        IDENTIFIER
    }
    issues = module.run_production_preflight(
        document,
        validation_records,
        export_records,
        module.selected_export_preflight_config(config, plan),
        SET_ID,
        module.read_section_config(settings),
        module.read_registration_config(settings),
        module.read_template_assembly_config(settings),
        settings_obj=settings,
        plan=plan,
        include_export_checks=True,
        probe_export_bounds=True,
        filename_issues_override=module.selected_export_filename_issues(
            plan, config, SET_ID,
        ),
    )
    return config, plan, skipped, issues, outline


def _export(module, document, config, plan, skipped, override=None):
    settings = module.settings_for_template_set(document, SET_ID)
    platforms = module.read_platform_configs(settings)
    return module.run_selected_production_export(
        document,
        plan,
        config,
        SET_ID,
        platforms[0] if platforms else module.default_platform_config(),
        module.read_formation_config(settings),
        module.read_registration_config(settings),
        module.read_template_assembly_config(settings),
        extra_skipped=skipped,
        exporter_override=override,
    )


def _output_witness(module, directory, plan, outline):
    svg_name = pathlib.Path(plan["tasks"][0]["path"]).name
    manifest_name = pathlib.Path(plan["manifest_path"]).name
    assert svg_name.endswith(".svg")
    assert manifest_name.endswith(".csv")
    assert {path.name for path in directory.iterdir()} == {
        svg_name, manifest_name,
    }
    svg = directory / svg_name
    assert svg.stat().st_size > 0
    assert b"<svg" in svg.read_bytes().lower()
    with (directory / manifest_name).open(
        "r", encoding="utf-8-sig", newline="",
    ) as source:
        reader = csv.DictReader(source)
        assert tuple(reader.fieldnames or ()) == tuple(
            module.EXPORT_MANIFEST_FIELDS
        )
        rows = list(reader)
    assert len(rows) == 2
    success = [row for row in rows if row["Export status"] == "Success"]
    skipped = [row for row in rows if row["Export status"] == "Skipped"]
    assert len(success) == len(skipped) == 1
    assert success[0]["Generated object name"] == outline["source_name"]
    assert success[0]["Generated object role"] == (
        module.CROSSOVER_INTEGRATED_OUTLINE_ROLE
    )
    assert success[0]["Export filename"] == svg_name
    assert success[0]["Export format"] == "SVG"
    assert success[0]["Template-set identifier"] == SET_ID
    assert skipped[0]["Export status"] == "Skipped"
    snapshot = ordinary_track_export_recipe.export_directory_snapshot(
        directory
    )
    assert not snapshot["directories"]
    return snapshot["content_by_path"]


def _failure_witness(summary, marker, directory):
    assert summary["successful_files"] == 0, summary
    assert summary["failed_files"] == 1, summary
    assert summary["manifest_path"] == "", summary
    assert marker in " ".join(summary["failures"]), summary
    assert not list(directory.iterdir()), list(directory.iterdir())


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    fixture = contract["fixture"]
    source = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_SELECTED_EXPORT_FIXTURE",
        ROOT / fixture["path"],
    )).resolve()
    assert source.is_file(), source
    source_hash = _sha256(source)
    assert source_hash == fixture["sha256"]
    for label in ("b14", "b15"):
        frozen = contract["source_state"][label]
        assert _sha256(ROOT / frozen["path"]) == frozen["sha256"]
    module = _load_product()
    chainage_mm = float(contract["scenario"]["host_a_chainage_mm"])

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-selected-export-"
    ) as temporary:
        temporary = pathlib.Path(temporary)
        document = _prepared_copy(
            module, source, temporary / "integrated-xo001.FCStd",
            chainage_mm,
        )
        try:
            baseline = _document_state(module, document)
            outputs = []
            for number in (1, 2):
                directory = temporary / "output-{}".format(number)
                directory.mkdir()
                config, plan, skipped, issues, outline = _selected_plan(
                    module, document, directory,
                )
                warning = [
                    issue for issue in issues
                    if issue["issue_code"] == (
                        "CROSSOVER_CHAIR_VALIDATION_OUTSTANDING"
                    )
                ]
                assert len(warning) == 1, issues
                assert warning[0]["severity"] == "Warning", issues
                assert warning[0]["blocks_export"] is False, issues
                assert not module.preflight_blocking_report(issues), issues
                assert _document_state(module, document) == baseline
                summary = _export(
                    module, document, config, plan, skipped,
                )
                assert summary["successful_files"] == 2, summary
                assert summary["failed_files"] == 0, summary
                assert summary["formats"] == ["SVG"], summary
                assert summary["manifest_path"] == plan["manifest_path"]
                assert _document_state(module, document) == baseline
                outputs.append(_output_witness(
                    module, directory, plan, outline,
                ))
            assert outputs[0] == outputs[1], outputs

            failure_directory = temporary / "exporter-failure"
            failure_directory.mkdir()
            config, plan, skipped, issues, _outline = _selected_plan(
                module, document, failure_directory,
            )
            assert not module.preflight_blocking_report(issues), issues

            def fail_after_export(doc, task, path):
                module.dispatch_freecad_export(doc, task, path)
                raise RuntimeError(EXPORT_FAULT)

            summary = _export(
                module, document, config, plan, skipped,
                override=fail_after_export,
            )
            _failure_witness(summary, EXPORT_FAULT, failure_directory)
            assert _document_state(module, document) == baseline

            commit_directory = temporary / "commit-failure"
            commit_directory.mkdir()
            config, plan, skipped, issues, _outline = _selected_plan(
                module, document, commit_directory,
            )
            assert not module.preflight_blocking_report(issues), issues
            original_commit = module.commit_staged_export_entries
            replace_calls = []

            def fail_second_replace(entries, overwrite_existing):
                original_replace = module.os.replace

                def injected_replace(source_path, target_path):
                    replace_calls.append(str(target_path))
                    if len(replace_calls) == 2:
                        raise RuntimeError(COMMIT_FAULT)
                    return original_replace(source_path, target_path)

                module.os.replace = injected_replace
                try:
                    return original_commit(entries, overwrite_existing)
                finally:
                    module.os.replace = original_replace

            module.commit_staged_export_entries = fail_second_replace
            try:
                summary = _export(module, document, config, plan, skipped)
            finally:
                module.commit_staged_export_entries = original_commit
            assert len(replace_calls) == 2, replace_calls
            _failure_witness(summary, COMMIT_FAULT, commit_directory)
            assert _document_state(module, document) == baseline
            print("SELECTED_EXPORT_WITNESS=" + json.dumps({
                "scope": "selected integrated cutting-profile object",
                "matching_record_count": 2,
                "exported_record_count": 1,
                "format": "SVG",
                "files": sorted(outputs[0]),
                "normalised_sha256": outputs[0],
                "chair_warning_nonblocking": True,
                "production_ready": False,
                "exporter_failure_rollback": True,
                "commit_failure_rollback": True,
                "source_fixture_sha256": source_hash,
            }, sort_keys=True), flush=True)
        finally:
            if document.Name in App.listDocuments():
                App.closeDocument(document.Name)

    assert _sha256(source) == source_hash
    assert not App.listDocuments()
    print(SENTINEL, flush=True)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {
    "__main__", "freecad_validate_phase8_crossover_selected_export",
}:
    _run_as_script()
