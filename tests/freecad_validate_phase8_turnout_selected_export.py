"""Prove a bounded TO-001 integrated selected SVG export on a copied host.

The output is private-development evidence, not a production-ready assembly
or a Phase 8 exit decision. The fixed B14 fixture is never opened directly.
"""

import copy
import csv
import hashlib
import importlib.util
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

from tools.freecad_bridge import ordinary_track_export_recipe  # noqa: E402
from tools.freecad_bridge import turnout_recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 turnout selected export FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
IDENTIFIER = turnout_recipe.TURNOUT_ID
SET_ID = "SET-001"
EXPORT_FAULT = "injected selected SVG exporter failure"
COMMIT_FAULT = "injected selected SVG commit failure"


def _host_proof():
    """Reuse the separately qualified narrow save/reopen comparator."""
    path = (
        ROOT
        / "tests/freecad_validate_phase8_turnout_host_integration_recovery.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_phase8_turnout_host_comparator", path,
    )
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.ROOT == ROOT
    return helper


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_product():
    assert pathlib.Path(api.__file__).resolve() == (
        ROOT / "tracktemplate/api.py"
    )
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
    return copy.deepcopy(index["records"])


def _prepared_copy(module, host_proof, source, target):
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    hosts = module.turnout_host_objects(document)
    selected = turnout_recipe.select_turnout_host(
        hosts, module.object_string_property,
        module._integer_object_property,
    )
    host = hosts[selected["index"]]
    config = module.create_curve_inheriting_c10_turnout(
        document, host, turnout_recipe.TURNOUT_CHAINAGE_MM,
        module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
        turnout_recipe.TRACK_GAUGE_MM, turnout_recipe.FLANGEWAY_MM,
    )
    assert config["turnout_id"] == IDENTIFIER
    assert module.analyse_entity_chair_positions(
        document, "turnout", IDENTIFIER,
    )
    integration = module.create_turnout_host_integration(
        document, IDENTIFIER,
    )
    assert integration == module.turnout_integration_by_id(
        document, IDENTIFIER,
    )
    assert len(integration["integration_object_names"]) == 5
    assert len(integration["integrated_record_ids"]) == 2
    assert len(_records(module, document)) == 8
    document.save()
    saved = host_proof._snapshot(module, document)
    App.closeDocument(document.Name)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    host_proof._assert_reopen_equal(
        saved, host_proof._snapshot(module, document),
    )
    assert _records(module, document) == saved["records"]
    assert module.turnout_integration_by_id(
        document, IDENTIFIER,
    ) == integration
    return document


def _selected_plan(module, document, output_directory):
    index = module.production_record_index_for_set(document, SET_ID)
    catalogue = module.hydrate_production_index_records(document, index)
    integration = module.turnout_integration_by_id(document, IDENTIFIER)
    assert integration is not None
    integration_names = set(integration["integration_object_names"])
    pair_ids = list(integration["integrated_record_ids"])
    assert len(pair_ids) == len(set(pair_ids)) == 2
    indexed = _records(module, document)
    assert [item["record_id"] for item in indexed] == [
        item["record_id"] for item in catalogue
    ]
    integrated = [
        record for record in catalogue
        if record["record_id"] in pair_ids
    ]
    assert [record["record_id"] for record in integrated] == pair_ids
    assert {record["category"] for record in integrated} == {
        module.EXPORT_CATEGORY_SOLID,
        module.EXPORT_CATEGORY_CUTTING,
    }
    assert {record["route_id"] for record in integrated} == {
        integration["route_id"]
    }
    assert {record["source_name"] for record in integrated} <= (
        integration_names
    )
    assert len({record["subtype"] for record in integrated}) == 1
    for record in integrated:
        source = document.getObject(record["source_name"])
        assert source is not None
        assert record["record_id"] in module.selected_export_object_record_ids(
            source
        )
        assert module.object_string_property(
            source, "ExportCategory", "",
        ) == record["category"]
    outline = next(
        record for record in integrated
        if record["category"] == module.EXPORT_CATEGORY_CUTTING
    )
    solid = next(
        record for record in integrated
        if record["category"] == module.EXPORT_CATEGORY_SOLID
    )
    for key in (
        "route_id", "route_name", "track_number", "platform_number",
        "section_number", "feature_number", "subtype",
    ):
        assert outline[key] == solid[key], key
    outline_obj = document.getObject(outline["source_name"])
    assert outline_obj is not None
    assert module.object_string_property(
        outline_obj, "GeneratedRole", ""
    ) == module.TURNOUT_INTEGRATED_OUTLINE_ROLE
    assert module.object_string_property(
        document.getObject(solid["source_name"]), "GeneratedRole", "",
    ) == module.TURNOUT_INTEGRATED_TEMPLATE_ROLE
    scope = {
        "scope_type": module.SELECTED_EXPORT_SCOPE_OBJECTS,
        "route_id": integration["route_id"],
        "route_label": integration["route_name"],
        "selected_objects": [{
            "name": str(outline_obj.Name),
            "record_ids": module.selected_export_object_record_ids(
                outline_obj
            ),
            "generated_role": module.TURNOUT_INTEGRATED_OUTLINE_ROLE,
            "export_subtype": module.object_string_property(
                outline_obj, "ExportSubtype", "",
            ),
            "route_id": integration["route_id"],
            "track_number": int(outline["track_number"] or 0),
            "platform_number": int(outline["platform_number"] or 0),
            "section_number": int(outline["section_number"] or 0),
            "feature_number": int(outline["feature_number"] or 0),
        }],
    }
    matching = module.filter_production_records_by_selected_scope(
        catalogue, scope,
    )
    assert [record["record_id"] for record in matching] == pair_ids
    assert {record["route_id"] for record in matching} == {
        integration["route_id"]
    }

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
    assert skipped[0]["record"]["record_id"] == solid["record_id"]
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
        integration["route_id"]
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
    return config, plan, skipped, issues, outline, solid, integration


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


def _output_witness(module, directory, plan, outline, solid):
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
    assert success[0]["Generated object role"] == outline["role"]
    assert success[0]["Export filename"] == svg_name
    assert success[0]["Export format"] == "SVG"
    assert success[0]["Template-set identifier"] == SET_ID
    assert skipped[0]["Generated object name"] == solid["source_name"]
    assert skipped[0]["Generated object role"] == solid["role"]
    assert skipped[0]["Export filename"] == ""
    assert skipped[0]["Export format"] == ""
    assert skipped[0]["Template-set identifier"] == SET_ID
    for row, record in ((success[0], outline), (skipped[0], solid)):
        for column, key in (
            ("Track number", "track_number"),
            ("Platform number", "platform_number"),
            ("Section number", "section_number"),
            ("Travel-order number", "travel_order_number"),
        ):
            assert row[column] == str(record.get(key) or ""), (
                column, row, record,
            )
    snapshot = ordinary_track_export_recipe.export_directory_snapshot(
        directory
    )
    assert not snapshot["directories"]
    return snapshot["content_by_path"], {
        "success": success[0]["Generated object name"],
        "skipped": skipped[0]["Generated object name"],
    }


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
        "TRACKTEMPLATE_TURNOUT_SELECTED_EXPORT_FIXTURE",
        ROOT / fixture["path"],
    )).resolve()
    assert source.is_file(), source
    source_hash = _sha256(source)
    assert source_hash == fixture["sha256"]
    source_hashes = {}
    for label in ("b14", "b15"):
        frozen = contract["source_state"][label]
        source_hashes[label] = _sha256(ROOT / frozen["path"])
        assert source_hashes[label] == frozen["sha256"]
    host_proof = _host_proof()
    host_proof._assert_reopen_comparator_contract()
    module = _load_product()
    assert turnout_recipe.TURNOUT_CHAINAGE_MM == float(
        contract["scenario"]["host_a_chainage_mm"]
    )
    print("PHASE8_TURNOUT_SELECTED_SOURCE=" + str(ROOT), flush=True)
    print("PHASE8_TURNOUT_SELECTED_FIXTURE=" + str(source), flush=True)
    print("PHASE8_TURNOUT_SELECTED_FIXTURE_SHA256=" + source_hash,
          flush=True)
    print("PHASE8_TURNOUT_SELECTED_REQUIRED_SENTINEL=" + SENTINEL,
          flush=True)

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-turnout-selected-export-"
    ) as temporary:
        temporary = pathlib.Path(temporary)
        document = _prepared_copy(
            module, host_proof, source,
            temporary / "integrated-to001.FCStd",
        )
        try:
            baseline = host_proof._snapshot(module, document)
            baseline_records = _records(module, document)
            assert baseline["records"] == baseline_records
            outputs = []
            manifest_bindings = []
            finding_codes = []
            integration_binding = None
            for number in (1, 2):
                directory = temporary / "output-{}".format(number)
                directory.mkdir()
                (
                    config, plan, skipped, issues, outline, solid,
                    integration,
                ) = _selected_plan(module, document, directory)
                assert not module.preflight_blocking_report(issues), issues
                assert host_proof._snapshot(module, document) == baseline
                current_codes = sorted({
                    item["issue_code"] for item in issues
                })
                if number == 1:
                    finding_codes = current_codes
                    integration_binding = {
                        "turnout_id": integration["turnout_id"],
                        "route_id": integration["route_id"],
                        "record_ids": list(
                            integration["integrated_record_ids"]
                        ),
                        "record_order": [
                            item["record_id"] for item in baseline_records
                        ],
                    }
                else:
                    assert current_codes == finding_codes
                summary = _export(
                    module, document, config, plan, skipped,
                )
                assert summary["successful_files"] == 2, summary
                assert summary["failed_files"] == 0, summary
                assert summary["formats"] == ["SVG"], summary
                assert summary["manifest_path"] == plan["manifest_path"]
                assert host_proof._snapshot(module, document) == baseline
                hashes, binding = _output_witness(
                    module, directory, plan, outline, solid,
                )
                outputs.append(hashes)
                manifest_bindings.append(binding)
            assert outputs[0] == outputs[1], outputs
            assert manifest_bindings[0] == manifest_bindings[1]

            failure_directory = temporary / "exporter-failure"
            failure_directory.mkdir()
            config, plan, skipped, issues, *_ = _selected_plan(
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
            assert host_proof._snapshot(module, document) == baseline

            commit_directory = temporary / "commit-failure"
            commit_directory.mkdir()
            config, plan, skipped, issues, *_ = _selected_plan(
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
            assert host_proof._snapshot(module, document) == baseline
            assert _records(module, document) == baseline_records
            print("TURNOUT_SELECTED_EXPORT_WITNESS=" + json.dumps({
                "scope": "selected integrated cutting-profile object",
                "integration_binding": integration_binding,
                "matching_record_count": 2,
                "exported_record_count": 1,
                "format": "SVG",
                "files": sorted(outputs[0]),
                "normalised_sha256": outputs[0],
                "manifest_bindings": manifest_bindings[0],
                "finding_codes": finding_codes,
                "preflight_nonblocking": True,
                "exporter_failure_rollback": True,
                "commit_failure_rollback": True,
                "document_and_undo_unchanged": True,
                "saved_reopened": True,
                "source_fixture_sha256": source_hash,
                "source_macro_sha256": source_hashes,
            }, sort_keys=True), flush=True)
        finally:
            if document.Name in App.listDocuments():
                App.closeDocument(document.Name)

    assert _sha256(source) == source_hash
    for label in ("b14", "b15"):
        frozen = contract["source_state"][label]
        assert _sha256(ROOT / frozen["path"]) == source_hashes[label]
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
    "__main__", "freecad_validate_phase8_turnout_selected_export",
}:
    _run_as_script()
