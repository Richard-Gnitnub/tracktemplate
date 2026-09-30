"""Compare one copied curved-host crossover across B14, B15 and B16.

The fixed B14-generated source stays byte-identical. Each version creates
XO-001, exports its selected outline, applies B4 and edits the toe position
on a separate copy. Raw observations remain available after a failure.
"""

import copy
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sys
import traceback

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_export_recipe  # noqa: E402


SENTINEL = "Phase 8 curved-host crossover FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_CURVED_FIXTURE",
    ROOT / "tmp/phase8-curved-comparison/source.FCStd",
)).resolve()
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
TOE_A_MM = 746.298
EDIT_TOE_A_MM = 746.299


def _load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_helper(
    "phase8_curved_xo_straight_helpers",
    "tests/freecad_validate_phase8_straight_host_crossover.py",
)
b4_base = _load_helper(
    "phase8_curved_xo_b4_helpers",
    "tests/freecad_validate_phase8_straight_crossover_b4.py",
)
selected_base = _load_helper(
    "phase8_curved_xo_selected_export_helpers",
    "tests/freecad_validate_phase8_crossover_selected_export.py",
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hashes():
    hashes = recipe.comparison_source_hashes(ROOT)
    relative = "tests/freecad_validate_phase8_curved_host_crossover.py"
    hashes[relative] = _sha256(ROOT / relative)
    for relative in (
        "tests/freecad_validate_phase8_straight_host_crossover.py",
        "tests/freecad_validate_phase8_straight_crossover_b4.py",
        "tests/freecad_validate_phase8_crossover_selected_export.py",
    ):
        hashes[relative] = _sha256(ROOT / relative)
    return hashes


def _write_report(path, report):
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _production(module, document):
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index["schema_version"] == 2
    assert index["template_set_id"] == "SET-001"
    records = index["records"]
    assert len(records) == 8
    crossover = [
        record for record in records if record["route_id"] == "XO-001"
    ]
    assert len(crossover) == 4
    for record in crossover:
        assert record["source_binding_type"] == "direct"
        obj = document.getObject(record["source_name"])
        assert obj is not None
        assert record["record_id"] in json.loads(
            module.object_string_property(
                obj, "ProductionRecordIDsJSON", ""
            )
        )
    return index, crossover


def _crossover_observation(module, document, config, *, edited=False):
    identifier = str(config["crossover_id"])
    assert identifier == "XO-001"
    assert config == module.crossover_config_by_id(document, identifier)
    assert float(config["toe_chainage_a"]) == (
        EDIT_TOE_A_MM if edited else TOE_A_MM
    )
    assert config["production_ready"] is False
    assert config["host_integration_allowed"] is False
    if edited:
        assert config["edit_revision"] == 1
    objects = []
    for obj in module._crossover_objects(document, identifier):
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "role": module.object_string_property(
                obj, "GeneratedRole", ""
            ),
            "template_set_id": module.object_string_property(
                obj, "TemplateSetID", ""
            ),
            "crossover_id": module.object_string_property(
                obj, module.CROSSOVER_ID_PROPERTY, ""
            ),
            "export_subtype": module.object_string_property(
                obj, "ExportSubtype", ""
            ),
            "members": (
                tuple(sorted(member.Name for member in obj.Group))
                if "Group" in obj.PropertiesList else None
            ),
            "shape": base._shape_state(getattr(obj, "Shape", None)),
        })
    index, production = _production(module, document)
    assert len(objects) == 9
    assert sum(item["shape"] is not None for item in objects) == 6
    record_ids = [item["record_id"] for item in production]
    assert all(record_ids) and len(set(record_ids)) == 4
    return {
        "config": base._neutral_version(config, edited=edited),
        "objects": objects,
        "production_records": production,
        "production_index": b4_base._neutral_index(index),
    }


def _selected_export(module, document, directory):
    """Use the already-qualified integrated curved XO selected route."""
    config, plan, skipped, issues, outline = (
        selected_base._selected_plan(module, document, directory)
    )
    evidence = {
        "issues": issues,
        "macro_version": str(module.MACRO_VERSION),
    }
    receipt = directory.parent / (directory.name + ".json")
    _write_report(receipt, evidence)
    assert not module.preflight_blocking_report(issues), issues
    summary = selected_base._export(
        module, document, config, plan, skipped,
    )
    evidence["summary"] = summary
    _write_report(receipt, evidence)
    assert summary["successful_files"] == 2, summary
    assert summary["failed_files"] == 0, summary
    evidence["content_by_path"] = selected_base._output_witness(
        module, directory, plan, outline,
    )
    snapshot = ordinary_track_export_recipe.export_directory_snapshot(
        directory
    )
    svg_name = pathlib.Path(plan["tasks"][0]["path"]).name
    manifest_name = pathlib.Path(plan["manifest_path"]).name
    assert set(snapshot["files"]) == {svg_name, manifest_name}
    assert not snapshot["directories"]
    manifest = snapshot["files"][manifest_name]["manifest"]
    assert manifest["fields"] == list(module.EXPORT_MANIFEST_FIELDS)
    assert len(manifest["rows"]) == 2
    for row in manifest["rows"]:
        assert row["Macro version"] == str(module.MACRO_VERSION)
    comparison_manifest = copy.deepcopy(manifest)
    for row in comparison_manifest["rows"]:
        del row["Macro version"]
    evidence["artifacts"] = snapshot
    evidence["comparison"] = {
        "filenames": sorted(snapshot["files"]),
        "svg_sha256": snapshot["files"][svg_name]["normalised_sha256"],
        "manifest": comparison_manifest,
    }
    _write_report(receipt, evidence)
    return evidence


def _b4_observation(module, document, result, before_index, contract):
    assert result.get("cache_reused") is False
    core = recipe.result_snapshot(module, result)
    expected = contract["legacy_semantics"]
    assert core["counts"] == expected["counts"]
    for key in (
        "status", "record_turnout_sides", "record_envelope_kinds",
        "record_identity_sha256", "stable_record_sha256",
    ):
        assert core[key] == expected[key]
    records = recipe.stable(result["resolved_timbers"])
    identities = [item["stable_identity"] for item in records]
    assert len(identities) == len(set(identities)) == 86
    assert core["record_identity_sha256"] == recipe.digest(identities)
    stable_records = [
        module._b4_stable_record(item) for item in result["resolved_timbers"]
    ]
    index, bound = _production(module, document)
    assert index == before_index, "B4 changed production index"
    b4 = b4_base._stored_b4(module, document, result)
    assert b4["shape"] is not None
    assert len(document.Objects) == contract["legacy_semantics"][
        "lifecycle_object_counts"
    ]["after_first_apply"]
    return {
        "core": core,
        "full_ordered_records": records,
        "stable_ordered_records": stable_records,
        "inherited_findings": recipe.stable(
            result["inherited_analysis"]["findings"]
        ),
        "resolved_findings": recipe.stable(
            result["resolved_analysis"]["findings"]
        ),
        "unresolved": recipe.stable(result["unresolved"]),
        "object_map": recipe.object_map(module, document),
        "b4_object": b4,
        "production_index": b4_base._neutral_index(index),
        "production_bindings": bound,
        "raw_resolved_analysis": result["resolved_analysis"],
    }


def _edit_arguments(document, config):
    return (
        document, str(config["crossover_id"]),
        document.getObject(str(config["host_a_object"])),
        document.getObject(str(config["host_b_object"])),
        EDIT_TOE_A_MM, str(config["arrangement"]),
        str(config["handing"]), float(config["track_gauge"]),
        float(config["flangeway"]),
        float(config["minimum_requested_radius"]),
    )


def _comparison_b4(observation):
    """Use accepted B4 stable boundary; retain raw analysis separately."""
    return {
        key: value for key, value in observation.items()
        if key != "raw_resolved_analysis"
    }


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    assert SOURCE.is_file(), SOURCE
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    fixture_sha256 = _sha256(SOURCE)
    assert fixture_sha256 == contract["fixture"]["sha256"]
    source_hashes = _source_hashes()
    modules = {}
    for label in ("B14", "B15"):
        state = contract["source_state"][label.lower()]
        path = ROOT / state["path"]
        assert _sha256(path) == state["sha256"]
        modules[label] = base._load_legacy(label, path)
        assert str(modules[label].MACRO_VERSION_NUMBER) == state["version"]
    modules["B16"] = base._load_b16()

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_root = ROOT / "benchmark-output/phase8-curved-crossover-comparison"
    run_root /= stamp
    run_root.mkdir(parents=True, exist_ok=False)
    receipt = run_root / "receipt.json"
    print("PHASE8_CURVED_XO_EVIDENCE=" + str(run_root), flush=True)
    report = {
        "status": "RUNNING",
        "host_profile_id": PROFILE,
        "source_fixture": str(SOURCE),
        "source_fixture_sha256": fixture_sha256,
        "source_sha256": source_hashes,
        "versions": {},
    }
    _write_report(receipt, report)
    try:
        for label, module in modules.items():
            report["stage"] = label + " copy"
            copied = run_root / (label.lower() + ".FCStd")
            shutil.copy2(SOURCE, copied)
            document = App.openDocument(str(copied))
            version = report["versions"].setdefault(label, {})
            try:
                document.UndoMode = 1
                assert len(document.Objects) == 9
                config, selected = recipe.create_controlled_crossover(
                    module, document, TOE_A_MM,
                )
                assert config["crossover_id"] == "XO-001"
                assert len(document.Objects) == 18
                version["selected_hosts"] = selected
                version["create"] = _crossover_observation(
                    module, document, config,
                )
                version["created_state"] = base._snapshot(document)
                _write_report(receipt, report)

                report["stage"] = label + " B4"
                before_index, _ = _production(module, document)
                b4_result = module.apply_crossover_b4_timbering(
                    document, "XO-001"
                )
                version["b4"] = _b4_observation(
                    module, document, b4_result, before_index, contract,
                )
                _write_report(receipt, report)

                report["stage"] = label + " edit"
                before_edit = base._snapshot(document)
                args = _edit_arguments(document, config)
                solved = base._solve_edit(module, args)
                assert base._snapshot(document) == before_edit
                edited = module.edit_rea_c10_crossover(
                    *args, pre_solved=solved,
                )
                assert len(document.Objects) == 18
                assert module._crossover_b4_object(
                    document, "XO-001"
                ) is None
                version["edit"] = _crossover_observation(
                    module, document, edited, edited=True,
                )
                version["edit_state"] = base._snapshot(document)
                _write_report(receipt, report)
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == copied:
                        App.closeDocument(opened.Name)
            assert _sha256(SOURCE) == fixture_sha256

            report["stage"] = label + " integrated export copy"
            export_copy = run_root / (label.lower() + "-export.FCStd")
            export_document = selected_base._prepared_copy(
                module, SOURCE, export_copy, TOE_A_MM,
            )
            try:
                version["integrated_export_state"] = base._snapshot(
                    export_document
                )
                _write_report(receipt, report)
                for number in (1, 2):
                    report["stage"] = "{} integrated export {}".format(
                        label, number,
                    )
                    directory = run_root / "{}-export-{}".format(label, number)
                    directory.mkdir()
                    evidence = _selected_export(
                        module, export_document, directory,
                    )
                    version.setdefault("exports", []).append(evidence)
                    assert base._snapshot(export_document) == (
                        version["integrated_export_state"]
                    )
                    _write_report(receipt, report)
                assert (version["exports"][0]["comparison"]
                        == version["exports"][1]["comparison"])
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == export_copy:
                        App.closeDocument(opened.Name)
            assert _sha256(SOURCE) == fixture_sha256

        report["stage"] = "cross-version comparison"
        versions = report["versions"]
        for stage in ("create", "edit"):
            assert versions["B14"][stage] == versions["B15"][stage]
            assert versions["B15"][stage] == versions["B16"][stage]
        for label in ("B14", "B15", "B16"):
            assert (versions[label]["exports"][0]["comparison"]
                    == versions[label]["exports"][1]["comparison"])
        assert (versions["B14"]["exports"][0]["comparison"]
                == versions["B15"]["exports"][0]["comparison"]
                == versions["B16"]["exports"][0]["comparison"])
        assert _comparison_b4(versions["B14"]["b4"]) == (
            _comparison_b4(versions["B15"]["b4"])
        )
        assert _comparison_b4(versions["B15"]["b4"]) == (
            _comparison_b4(versions["B16"]["b4"])
        )
        assert _sha256(SOURCE) == fixture_sha256
        assert _source_hashes() == source_hashes
        report["status"] = "PASS"
        report["sentinel"] = SENTINEL
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        raise
    finally:
        report["source_fixture_sha256_after"] = _sha256(SOURCE)
        report["source_sha256_after"] = _source_hashes()
        _write_report(receipt, report)
    print("PHASE8_CURVED_XO_RECEIPT=" + str(receipt))
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase8_curved_host_crossover"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
