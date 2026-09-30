"""Compare one copied straight-host TO-001 across B14, B15, and B16.

Use the accepted 1500/450 mm B14 straight-route source. The source stays
closed and unchanged. This is development comparison, not output acceptance.
"""

import ast
import copy
import datetime
import hashlib
import json
import math
import os
import pathlib
import runpy
import shutil
import sys
import tempfile
import types

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import turnout_recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_export_recipe  # noqa: E402
from tools.freecad_bridge.ordinary_track_recipe import (  # noqa: E402
    ordinary_track_document_snapshot,
)
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 straight-host turnout FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_STRAIGHT_TURNOUT_FIXTURE",
    ROOT / "tmp/phase8-straight-turnout/straight-source.FCStd",
)).resolve()
SOURCE_SEMANTIC_SHA256 = (
    "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
)
LEGACY_CONTRACT = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
ROUTE_ID = "straight-phase1-curve-entrance"
HOST_NAME = "RailwayStraightTrackCentreline_R01_T01"
TOE_MM = 580.134
HOST_LENGTH_MM = 1500.0
LENGTH_TOLERANCE_MM = 1.0e-6


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_sha256(value):
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_legacy(label, source):
    tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
    final = tree.body[-1]
    assert isinstance(final, ast.Expr)
    assert isinstance(final.value, ast.Call)
    assert isinstance(final.value.func, ast.Name)
    assert final.value.func.id == "run_macro"
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType("straight_turnout_" + label.lower())
    module.__file__ = str(source)
    sys.modules[module.__name__] = module
    exec(compile(tree, str(source), "exec"), module.__dict__)
    return module


def _load_b16():
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


def _host(module, document):
    selected = [
        obj for obj in module.turnout_host_objects(document)
        if module.object_string_property(obj, "TemplateSetID", "") == "SET-001"
        and module.object_string_property(obj, "RouteID", "") == ROUTE_ID
        and module.object_string_property(obj, "GeneratedRole", "")
        == "StraightTrackCentreline"
        and module._integer_object_property(obj, "TrackNumber", 0) == 1
    ]
    assert [obj.Name for obj in selected] == [HOST_NAME]
    host = selected[0]
    length_mm = float(module.turnout_host_alignment(host)["total"])
    assert math.isclose(
        length_mm, HOST_LENGTH_MM, rel_tol=0.0,
        abs_tol=LENGTH_TOLERANCE_MM,
    )
    dimensions = module.rea_c10_dimensions(16.5, 1.0)
    minimum, maximum = module.turnout_valid_toe_range(
        length_mm, dimensions, module.TURNOUT_ORIENTATION_FACING,
    )
    assert minimum < TOE_MM < maximum
    return host


def _history(document):
    return {
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": tuple(str(name) for name in document.UndoNames),
        "redo_names": tuple(str(name) for name in document.RedoNames),
    }


def _shape(shape):
    if shape is None or shape.isNull():
        return None
    assert shape.isValid()
    return {
        "brep_sha256": hashlib.sha256(
            shape.exportBrepToString().encode("utf-8")
        ).hexdigest(),
        "summary": turnout_recipe.shape_summary(shape),
    }


def _state(document):
    """Capture document data, exact geometry, and transaction history."""
    objects = []
    for obj in document.Objects:
        properties = tuple(sorted(
            (name, str(getattr(obj, name)))
            for name in obj.PropertiesList
            if name not in {
                "Shape", "Group", "_Part_ShapeCache", "ShapeMaterial",
            }
        ))
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "properties": properties,
            "members": (
                tuple(sorted(member.Name for member in obj.Group))
                if "Group" in obj.PropertiesList else None
            ),
            "shape": _shape(getattr(obj, "Shape", None)),
        })
    return {"objects": objects, "history": _history(document)}


def _persistent_state(state):
    result = copy.deepcopy(state["objects"])
    for obj in result:
        if obj["shape"] is not None:
            del obj["shape"]["brep_sha256"]
    return result


def _neutral_config(config):
    result = copy.deepcopy(config)
    assert isinstance(result.get("macro_version"), str)
    del result["macro_version"]
    return result


def _turnout_observation(module, document, source_records):
    config = module.turnout_config_by_id(document, turnout_recipe.TURNOUT_ID)
    assert config is not None
    assert config["host_object"] == HOST_NAME
    assert config["route_id"] == ROUTE_ID
    assert config["turnout_id"] == "TO-001"
    assert config["toe_chainage"] == TOE_MM
    assert config["handing"] == module.TURNOUT_HAND_LEFT
    assert config["orientation"] == module.TURNOUT_ORIENTATION_FACING
    assert config["timber_count"] > 0
    objects = turnout_recipe._turnout_objects(module, document)
    assert len(objects) == 8
    assert [item["role"] for item in objects] == sorted(
        turnout_recipe.EXPECTED_TURNOUT_ROLES
    )
    for item in objects:
        assert item["properties"]["TurnoutHostObject"] == HOST_NAME
        item["properties"]["TurnoutConfigurationJSON"] = _neutral_config(
            item["properties"]["TurnoutConfigurationJSON"]
        )
        obj = document.getObject(item["name"])
        assert str(obj.GeneratorVersion) == str(module.MACRO_VERSION)
        item["all_property_types"] = tuple(sorted(
            (name, str(obj.getTypeIdOfProperty(name)))
            for name in obj.PropertiesList
        ))
        all_properties = {}
        for name in obj.PropertiesList:
            if name in {
                "Shape", "Group", "_Part_ShapeCache", "ShapeMaterial",
                "GeneratorVersion",
            }:
                continue
            if name == "TurnoutConfigurationJSON":
                all_properties[name] = _neutral_config(
                    json.loads(str(getattr(obj, name)))
                )
            else:
                all_properties[name] = str(getattr(obj, name))
        item["all_properties"] = all_properties
        item["exact_shape"] = _shape(getattr(obj, "Shape", None))
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None and index["schema_version"] == 2
    records = index["records"]
    assert records[:len(source_records)] == source_records
    added = records[len(source_records):]
    assert len(added) == 6
    assert [record["role"] for record in added] == [
        "TurnoutTemplate", "TurnoutPlanOutline", "TurnoutRailGeometry",
        "TurnoutTimberGeometry", "TurnoutTimberLabels",
        "TurnoutConstructionMarks",
    ]
    assert all(record["route_id"] == ROUTE_ID for record in added)
    assert all(record["source_binding_type"] == "direct" for record in added)
    assert all(record["source_name"] in {
        item["name"] for item in objects
    } for record in added)
    for record in added:
        obj = document.getObject(record["source_name"])
        record_id = record["record_id"]
        assert str(obj.ProductionRecordID) == record_id
        assert json.loads(str(obj.ProductionRecordIDsJSON)) == [record_id]
    ids = [record["record_id"] for record in records]
    assert len(set(ids)) == len(ids)
    catalogue = json.loads(str(settings.TurnoutConfigurationsJSON))
    assert len(catalogue) == 1
    assert _neutral_config(catalogue[0]) == _neutral_config(config)
    return {
        "config": _neutral_config(config),
        "objects": objects,
        "production_records": copy.deepcopy(records),
    }


def _b16_lifecycle(module, document, before, created):
    assert created["history"]["undo"] == before["history"]["undo"] + 1
    assert created["history"]["redo"] == 0
    copy_path = pathlib.Path(document.FileName)
    document.undo()
    document.recompute()
    undone = _state(document)
    assert undone["objects"] == before["objects"]
    assert module.turnout_config_by_id(document, "TO-001") is None
    assert undone["history"]["redo"] == 1
    document.redo()
    document.recompute()
    redone = _state(document)
    assert redone["objects"] == created["objects"]
    assert redone["history"]["redo"] == 0
    document.save()
    saved = _state(document)
    App.closeDocument(document.Name)
    reopened = App.openDocument(str(copy_path))
    after_reopen = _state(reopened)
    assert _persistent_state(after_reopen) == _persistent_state(saved)
    assert module.turnout_config_by_id(reopened, "TO-001") is not None
    return reopened, {
        "before": len(before["objects"]),
        "created": len(created["objects"]),
        "undone": len(undone["objects"]),
        "redone": len(redone["objects"]),
        "reopened": len(after_reopen["objects"]),
    }


def _selected_pair(module, document):
    """Find the existing unintegrated TO-001 physical representations."""
    assert module.turnout_integration_by_id(document, "TO-001") is None
    index = module.production_record_index_for_set(document, "SET-001")
    catalogue = module.hydrate_production_index_records(document, index)
    assert len(catalogue) == 18
    pair = [
        record for record in catalogue
        if record["role"] in {
            module.TURNOUT_TEMPLATE_ROLE, module.TURNOUT_OUTLINE_ROLE,
        }
        and record["route_id"] == ROUTE_ID
        and module.object_string_property(
            document.getObject(record["source_name"]), "TurnoutID", "",
        ) == "TO-001"
    ]
    assert len(pair) == 2
    outline = next(record for record in pair
                   if record["category"] == module.EXPORT_CATEGORY_CUTTING)
    solid = next(record for record in pair
                 if record["category"] == module.EXPORT_CATEGORY_SOLID)
    for record in pair:
        obj = document.getObject(record["source_name"])
        assert module.selected_export_object_record_ids(obj) == {
            record["record_id"]
        }
    return catalogue, outline, solid


def _selected_export_output(module, directory, plan, outline, solid):
    """Retain full artifact evidence and compare only verified version data."""
    snapshot = ordinary_track_export_recipe.export_directory_snapshot(directory)
    svg_name = pathlib.Path(plan["tasks"][0]["path"]).name
    manifest_name = pathlib.Path(plan["manifest_path"]).name
    assert set(snapshot["files"]) == {svg_name, manifest_name}
    assert not snapshot["directories"]
    assert svg_name.endswith(".svg") and manifest_name.endswith(".csv")
    bounds = module.validate_svg_export_bounds(str(directory / svg_name))
    manifest = snapshot["files"][manifest_name]["manifest"]
    assert manifest["fields"] == list(module.EXPORT_MANIFEST_FIELDS)
    rows = manifest["rows"]
    assert len(rows) == 2
    successful = [row for row in rows if row["Export status"] == "Success"]
    skipped = [row for row in rows if row["Export status"] == "Skipped"]
    assert len(successful) == len(skipped) == 1
    assert successful[0]["Export filename"] == svg_name
    assert successful[0]["Export format"] == "SVG"
    assert skipped[0]["Export filename"] == skipped[0]["Export format"] == ""
    for row, record in ((successful[0], outline), (skipped[0], solid)):
        assert row["Generated object name"] == record["source_name"]
        assert row["Generated object role"] == record["role"]
        assert row["Template-set identifier"] == "SET-001"
        assert row["Macro version"] == str(module.MACRO_VERSION)
        for column, key in (
            ("Track number", "track_number"),
            ("Platform number", "platform_number"),
            ("Section number", "section_number"),
            ("Travel-order number", "travel_order_number"),
        ):
            assert row[column] == str(record.get(key) or "")
    comparison_manifest = copy.deepcopy(manifest)
    for row in comparison_manifest["rows"]:
        del row["Macro version"]
    return {
        "artifacts": snapshot,
        "macro_version": str(module.MACRO_VERSION),
        "svg_bounds": bounds,
        "comparison": {
            "filenames": sorted(snapshot["files"]),
            "svg_sha256": snapshot["files"][svg_name]["normalised_sha256"],
            "manifest": comparison_manifest,
        },
    }


def _selected_export(module, document, directory):
    """Export the outline and retain every preflight finding unchanged."""
    catalogue, outline, solid = _selected_pair(module, document)
    scope = {
        "scope_type": module.SELECTED_EXPORT_SCOPE_OBJECTS,
        "route_id": ROUTE_ID,
        "route_label": outline["route_name"],
        "selected_objects": [{
            "name": outline["source_name"],
            "record_ids": {outline["record_id"]},
            "generated_role": outline["role"],
            "export_subtype": outline["subtype"],
            **{key: outline[key] for key in (
                "route_id", "track_number", "platform_number",
                "section_number", "feature_number",
            )},
        }],
    }
    matching = module.filter_production_records_by_selected_scope(
        catalogue, scope,
    )
    assert {item["record_id"] for item in matching} == {
        outline["record_id"], solid["record_id"],
    }
    settings = module.settings_for_template_set(document, "SET-001")
    config = module.read_production_export_config(settings)
    config.update({
        "enabled": True, "output_directory": str(directory),
        "create_combined_files": False, "create_manifest": True,
        "overwrite_existing": False, "open_output_directory": False,
        "formats": {"svg": True, "dxf": False, "step": False, "stl": False},
    })
    records, skipped = module.selected_export_records_for_formats(
        matching, config,
    )
    assert [record["record_id"] for record in records] == [outline["record_id"]]
    assert len(skipped) == 1
    assert skipped[0]["record"]["record_id"] == solid["record_id"]
    plan = module.plan_selected_production_export(
        records, config, "SET-001", scope,
    )
    assert len(plan["tasks"]) == 1
    assert plan["tasks"][0]["format"] == "svg"
    issues = module.run_production_preflight(
        document,
        module.selected_export_validation_records(catalogue, matching, scope),
        records, module.selected_export_preflight_config(config, plan),
        "SET-001", module.read_section_config(settings),
        module.read_registration_config(settings),
        module.read_template_assembly_config(settings), settings_obj=settings,
        plan=plan, include_export_checks=True, probe_export_bounds=True,
        filename_issues_override=module.selected_export_filename_issues(
            plan, config, "SET-001",
        ),
    )
    evidence = {
        "issues": issues,
        "record_ids": [record["record_id"] for record in matching],
        "macro_version": str(module.MACRO_VERSION),
    }
    receipt = directory.parent / (directory.name + ".json")
    receipt.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    assert not module.preflight_blocking_report(issues), issues
    platforms = module.read_platform_configs(settings)
    summary = module.run_selected_production_export(
        document, plan, config, "SET-001",
        platforms[0] if platforms else module.default_platform_config(),
        module.read_formation_config(settings),
        module.read_registration_config(settings),
        module.read_template_assembly_config(settings), extra_skipped=skipped,
    )
    evidence["summary"] = summary
    receipt.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    assert summary["successful_files"] == 2, summary
    assert summary["failed_files"] == 0, summary
    evidence.update(_selected_export_output(
        module, directory, plan, outline, solid,
    ))
    receipt.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return evidence


def validate():
    contract = json.loads(LEGACY_CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-feasibility:1"
    )
    assert SOURCE.is_file(), "Generate the copied straight source first"
    source_sha256 = _sha256(SOURCE)
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    modules = {}
    for label in ("B14", "B15"):
        source_state = contract["source_state"][label.lower()]
        macro = ROOT / source_state["path"]
        assert _sha256(macro) == source_state["sha256"]
        modules[label] = _load_legacy(label, macro)
        assert str(modules[label].MACRO_VERSION_NUMBER) == (
            source_state["version"]
        )
    modules["B16"] = _load_b16()

    observations = {}
    lifecycle = None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    export_root = (
        ROOT / "benchmark-output/phase8-straight-turnout-export" / stamp
    )
    export_root.mkdir(parents=True, exist_ok=False)
    print("PHASE8_STRAIGHT_EXPORT_EVIDENCE=" + str(export_root), flush=True)
    exports = {}
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-straight-turnout-"
    ) as temporary:
        for label, module in modules.items():
            copy_path = pathlib.Path(temporary) / (
                "straight-turnout-{}.FCStd".format(label.lower())
            )
            shutil.copy2(SOURCE, copy_path)
            document = App.openDocument(str(copy_path))
            try:
                document.UndoMode = 1
                assert len(document.Objects) == 23
                assert ordinary_track_document_snapshot(
                    module, document,
                )["semantic_sha256"] == SOURCE_SEMANTIC_SHA256
                host = _host(module, document)
                settings = module.settings_for_template_set(document, "SET-001")
                source_records = copy.deepcopy(
                    module.read_production_record_index(settings)["records"]
                )
                assert len(source_records) == 12
                before = _state(document)
                if label == "B16":
                    try:
                        module.create_curve_inheriting_c10_turnout(
                            document, host, 0.0,
                            module.TURNOUT_HAND_LEFT,
                            module.TURNOUT_ORIENTATION_FACING, 16.5, 1.0,
                        )
                    except ValueError as error:
                        assert "Switch-toe chainage must be between" in str(error)
                    else:
                        raise AssertionError("An invalid straight toe was accepted")
                    assert _state(document) == before
                config = module.create_curve_inheriting_c10_turnout(
                    document, host, TOE_MM,
                    module.TURNOUT_HAND_LEFT,
                    module.TURNOUT_ORIENTATION_FACING, 16.5, 1.0,
                )
                assert config["turnout_id"] == "TO-001"
                created = _state(document)
                assert len(created["objects"]) == 31
                observations[label] = _turnout_observation(
                    module, document, source_records,
                )
                exports[label] = []
                for number in (1, 2):
                    directory = export_root / "{}-{}".format(label, number)
                    directory.mkdir()
                    exports[label].append(_selected_export(
                        module, document, directory,
                    ))
                    assert _state(document) == created
                assert (exports[label][0]["comparison"]
                        == exports[label][1]["comparison"])
                if label == "B16":
                    document, lifecycle = _b16_lifecycle(
                        module, document, before, created,
                    )
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == copy_path:
                        App.closeDocument(opened.Name)
            assert _sha256(SOURCE) == source_sha256

    assert observations["B14"] == observations["B15"]
    assert observations["B15"] == observations["B16"]
    assert (exports["B14"][0]["comparison"]
            == exports["B15"][0]["comparison"]
            == exports["B16"][0]["comparison"])
    assert lifecycle is not None
    witness = {
        "host_name": HOST_NAME,
        "host_route_id": ROUTE_ID,
        "toe_mm": TOE_MM,
        "turnout_id": "TO-001",
        "turnout_object_count": len(observations["B16"]["objects"]),
        "production_record_count": len(
            observations["B16"]["production_records"]
        ),
        "comparison_sha256": {
            key: _semantic_sha256(observations["B16"][key])
            for key in ("config", "objects", "production_records")
        },
        "exact_brep_sha256": {
            item["role"]: item["exact_shape"]["brep_sha256"]
            for item in observations["B16"]["objects"]
            if item["exact_shape"] is not None
        },
        "source_sha256": source_sha256,
        "source_semantic_sha256": SOURCE_SEMANTIC_SHA256,
        "lifecycle": lifecycle,
        "selected_export": {
            "directory": str(export_root),
            "comparison": exports["B16"][0]["comparison"],
            "version_by_label": {
                label: values[0]["macro_version"]
                for label, values in exports.items()
            },
            "document_and_undo_unchanged": True,
        },
    }
    (export_root / "witness.json").write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("PHASE8_STRAIGHT_TURNOUT_WITNESS=" + json.dumps(
        witness, sort_keys=True, separators=(",", ":"),
    ))
    print(SENTINEL)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase8_straight_host_turnout"}:
    _run_as_script()
