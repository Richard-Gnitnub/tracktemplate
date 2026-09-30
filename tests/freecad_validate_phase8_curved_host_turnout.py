"""Compare one curved-host TO-001 workflow across B14, B15, and B16.

Use separate copies of the fixed B14 base document for handed editing and
the retained integrated selected-export route. Output is development evidence.
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
import tempfile
import traceback

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import turnout_recipe  # noqa: E402


SENTINEL = "Phase 8 curved-host turnout comparison FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
SOURCE = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_CURVED_FIXTURE",
    ROOT / "tmp/phase8-curved-comparison/source.FCStd",
)).resolve()
EXPECTED_FIXTURE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _helper(relative, name):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.ROOT == ROOT
    return helper


def _source_hashes(contract):
    paths = [
        ROOT / contract["source_state"][label]["path"]
        for label in ("b14", "b15")
    ]
    paths.extend((
        ROOT / "TrackTemplate.FCMacro",
        pathlib.Path(__file__),
        ROOT / "tests/freecad_validate_phase8_straight_host_turnout.py",
        ROOT / "tests/freecad_validate_phase8_turnout_selected_export.py",
        ROOT / "tests/freecad_validate_phase8_turnout_host_integration_recovery.py",
    ))
    paths.extend(sorted((ROOT / "tracktemplate").rglob("*.py")))
    return {
        str(path.relative_to(ROOT)): _sha256(path)
        for path in paths
    }


def _material_value(obj, name):
    value = getattr(obj, name)
    if obj.getTypeIdOfProperty(name) != "Materials::PropertyMaterial":
        return str(value)
    # A FreeCAD Material repr contains a transient Python address.
    return json.dumps({
        "type": value.TypeId,
        "uuid": value.UUID,
        "parent": value.Parent,
        "properties": value.Properties,
        "legacy_properties": value.LegacyProperties,
        "physical_models": value.PhysicalModels,
        "appearance_models": value.AppearanceModels,
    }, sort_keys=True)


def _neutral_config(config, module):
    result = copy.deepcopy(config)
    assert result["macro_version"] == str(module.MACRO_VERSION_NUMBER)
    del result["macro_version"]
    return result


def _observation(module, document, host, source_records, straight):
    """Capture full stable turnout properties, exact shapes and record order."""
    config = module.turnout_config_by_id(document, turnout_recipe.TURNOUT_ID)
    assert config is not None
    assert config["turnout_id"] == turnout_recipe.TURNOUT_ID
    assert config["host_object"] == host.Name
    assert config["route_id"] == ""
    assert config["toe_chainage"] == turnout_recipe.TURNOUT_CHAINAGE_MM
    assert config["orientation"] == module.TURNOUT_ORIENTATION_FACING
    assert config["handing"] in {
        module.TURNOUT_HAND_LEFT, module.TURNOUT_HAND_RIGHT,
    }
    assert config["timber_count"] > 0
    objects = turnout_recipe._turnout_objects(module, document)
    assert len(objects) == 8
    assert [item["role"] for item in objects] == sorted(
        turnout_recipe.EXPECTED_TURNOUT_ROLES
    )
    for item in objects:
        obj = document.getObject(item["name"])
        assert obj is not None
        assert str(obj.GeneratorVersion) == str(module.MACRO_VERSION)
        assert item["properties"]["TurnoutHostObject"] == host.Name
        item["properties"]["TurnoutConfigurationJSON"] = _neutral_config(
            item["properties"]["TurnoutConfigurationJSON"], module,
        )
        item["all_property_types"] = tuple(sorted(
            (name, str(obj.getTypeIdOfProperty(name)))
            for name in obj.PropertiesList
        ))
        properties = {}
        for name in obj.PropertiesList:
            if name in {
                "Shape", "Group", "_Part_ShapeCache", "GeneratorVersion",
            }:
                continue
            if name == "TurnoutConfigurationJSON":
                properties[name] = _neutral_config(
                    json.loads(str(getattr(obj, name))), module,
                )
            else:
                properties[name] = _material_value(obj, name)
        item["all_properties"] = properties
        item["exact_shape"] = straight._shape(getattr(obj, "Shape", None))
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None and index["schema_version"] == 2
    records = copy.deepcopy(index["records"])
    assert len(records) == 10
    assert records[:len(source_records)] == source_records
    assert [item["role"] for item in records[len(source_records):]] == [
        "TurnoutTemplate", "TurnoutPlanOutline", "TurnoutRailGeometry",
        "TurnoutTimberGeometry", "TurnoutTimberLabels",
        "TurnoutConstructionMarks",
    ]
    ids = [item["record_id"] for item in records]
    assert len(ids) == len(set(ids))
    catalogue = json.loads(str(settings.TurnoutConfigurationsJSON))
    assert len(catalogue) == 1
    assert _neutral_config(catalogue[0], module) == _neutral_config(
        config, module,
    )
    return {
        "config": _neutral_config(config, module),
        "objects": objects,
        "production_records": records,
    }


def _edit_copy(module, source, target, straight):
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    try:
        document.UndoMode = 1
        assert len(document.Objects) == 9
        hosts = module.turnout_host_objects(document)
        selection = turnout_recipe.select_turnout_host(
            hosts, module.object_string_property,
            module._integer_object_property,
        )
        host = hosts[selection["index"]]
        assert selection["identity"]["route_id"] == ""
        assert abs(float(module.turnout_host_alignment(host)["total"])
                   - 1542.475839) <= 1.0e-6
        settings = module.settings_for_template_set(document, "SET-001")
        source_records = copy.deepcopy(
            module.read_production_record_index(settings)["records"]
        )
        assert len(source_records) == 4
        created_config = module.create_curve_inheriting_c10_turnout(
            document, host, turnout_recipe.TURNOUT_CHAINAGE_MM,
            module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
            turnout_recipe.TRACK_GAUGE_MM,
            turnout_recipe.FLANGEWAY_MM,
        )
        assert created_config["turnout_id"] == turnout_recipe.TURNOUT_ID
        assert len(document.Objects) == 17
        created = _observation(
            module, document, host, source_records, straight,
        )
        assert created["config"]["handing"] == module.TURNOUT_HAND_LEFT
        edited_config = module.edit_curve_inheriting_c10_turnout(
            document, turnout_recipe.TURNOUT_ID, host,
            turnout_recipe.TURNOUT_CHAINAGE_MM,
            module.TURNOUT_HAND_RIGHT, module.TURNOUT_ORIENTATION_FACING,
            turnout_recipe.TRACK_GAUGE_MM,
            turnout_recipe.FLANGEWAY_MM,
        )
        assert edited_config["turnout_id"] == turnout_recipe.TURNOUT_ID
        assert len(document.Objects) == 17
        edited = _observation(
            module, document, host, source_records, straight,
        )
        assert edited["config"]["handing"] == module.TURNOUT_HAND_RIGHT
        assert [item["name"] for item in edited["objects"]] == [
            item["name"] for item in created["objects"]
        ]
        assert [item["record_id"] for item in edited["production_records"]] == [
            item["record_id"] for item in created["production_records"]
        ]
        assert edited["objects"] != created["objects"]
        return {"created": created, "edited": edited}
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


def _export_copy(module, source, target, label, output_root,
                 selected, host_proof, straight):
    document = selected._prepared_copy(module, host_proof, source, target)
    try:
        baseline = host_proof._snapshot(module, document)
        integration = module.turnout_integration_by_id(
            document, turnout_recipe.TURNOUT_ID,
        )
        assert integration is not None
        records = selected._records(module, document)
        result = {
            "integration": integration,
            "record_ids": [item["record_id"] for item in records],
            "outputs": [],
        }
        for number in (1, 2):
            directory = output_root / "{}-{}".format(label, number)
            directory.mkdir()
            (config, plan, skipped, issues, outline, solid,
             selected_integration) = selected._selected_plan(
                module, document, directory,
            )
            assert selected_integration == integration
            assert not module.preflight_blocking_report(issues), issues
            assert host_proof._snapshot(module, document) == baseline
            summary = selected._export(
                module, document, config, plan, skipped,
            )
            assert summary["successful_files"] == 2, summary
            assert summary["failed_files"] == 0, summary
            assert summary["formats"] == ["SVG"], summary
            assert host_proof._snapshot(module, document) == baseline
            output = straight._selected_export_output(
                module, directory, plan, outline, solid,
            )
            result["outputs"].append({
                "issues": issues,
                "summary": summary,
                **output,
            })
        assert (result["outputs"][0]["comparison"]
                == result["outputs"][1]["comparison"])
        return result
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


def _compare_versions(versions):
    for key in ("created", "edited"):
        for part in ("config", "objects", "production_records"):
            values = [versions[label]["edit"][key][part]
                      for label in ("B14", "B15", "B16")]
            assert values[0] == values[1] == values[2], (
                "Curved turnout {} {} differs across versions".format(
                    key, part,
                )
            )
    exports = [
        versions[label]["selected_export"]["outputs"][0]["comparison"]
        for label in ("B14", "B15", "B16")
    ]
    assert exports[0] == exports[1] == exports[2], (
        "Curved turnout selected SVG/CSV differs across versions"
    )
    bindings = [
        versions[label]["selected_export"]["record_ids"]
        for label in ("B14", "B15", "B16")
    ]
    assert bindings[0] == bindings[1] == bindings[2], (
        "Curved turnout integrated record order differs across versions"
    )


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    assert SOURCE.is_file(), SOURCE
    fixture_sha256 = _sha256(SOURCE)
    assert fixture_sha256 == EXPECTED_FIXTURE_SHA256
    assert fixture_sha256 == contract["fixture"]["sha256"]
    source_hashes = _source_hashes(contract)
    for label in ("b14", "b15"):
        entry = contract["source_state"][label]
        assert source_hashes[entry["path"]] == entry["sha256"]
    straight = _helper(
        "tests/freecad_validate_phase8_straight_host_turnout.py",
        "_phase8_curved_straight_turnout_helper",
    )
    selected = _helper(
        "tests/freecad_validate_phase8_turnout_selected_export.py",
        "_phase8_curved_turnout_selected_helper",
    )
    host_proof = _helper(
        "tests/freecad_validate_phase8_turnout_host_integration_recovery.py",
        "_phase8_curved_turnout_host_helper",
    )
    assert straight.PROFILE == selected.PROFILE == host_proof.PROFILE == PROFILE
    host_proof._assert_reopen_comparator_contract()
    modules = {}
    for label in ("B14", "B15"):
        entry = contract["source_state"][label.lower()]
        module = straight._load_legacy(label, ROOT / entry["path"])
        assert str(module.MACRO_VERSION_NUMBER) == entry["version"]
        modules[label] = module
    modules["B16"] = straight._load_b16()

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    output_root = ROOT / "benchmark-output/phase8-curved-turnout-comparison" / stamp
    output_root.mkdir(parents=True, exist_ok=False)
    report_path = output_root / "run.json"
    report = {
        "status": "FAIL",
        "host_profile_id": PROFILE,
        "fixture_sha256": fixture_sha256,
        "source_sha256": source_hashes,
        "versions": {},
    }
    print("PHASE8_CURVED_TURNOUT_REPORT=" + str(report_path), flush=True)
    try:
        with tempfile.TemporaryDirectory(
            prefix="tracktemplate-phase8-curved-turnout-"
        ) as temporary:
            temporary = pathlib.Path(temporary)
            for label, module in modules.items():
                version = report["versions"].setdefault(label, {})
                version["macro_version"] = str(module.MACRO_VERSION)
                version["edit"] = _edit_copy(
                    module, SOURCE,
                    temporary / "{}-edit.FCStd".format(label.lower()),
                    straight,
                )
                version["selected_export"] = _export_copy(
                    module, SOURCE,
                    temporary / "{}-integrated.FCStd".format(label.lower()),
                    label, output_root, selected, host_proof, straight,
                )
                report_path.write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                assert _sha256(SOURCE) == fixture_sha256
                assert _source_hashes(contract) == source_hashes
        _compare_versions(report["versions"])
        report["status"] = "PASS"
    except Exception:
        report["error"] = traceback.format_exc()
        raise
    finally:
        report["fixture_sha256_after"] = _sha256(SOURCE)
        report["source_sha256_after"] = _source_hashes(contract)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    assert report["fixture_sha256_after"] == fixture_sha256
    assert report["source_sha256_after"] == source_hashes
    assert not App.listDocuments()
    print(SENTINEL, flush=True)


def _run_as_script():
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase8_curved_host_turnout"}:
    _run_as_script()
