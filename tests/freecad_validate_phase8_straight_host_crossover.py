"""Compare one copied straight-host crossover across B14, B15, and B16.

This qualified FreeCAD check uses one B14 Generate/Replace document with
1500/450 mm connected straight routes. The source document is never opened
for mutation. This is development comparison, not output acceptance.
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
import Materials


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_export_recipe  # noqa: E402
from tools.freecad_bridge.ordinary_track_recipe import (  # noqa: E402
    ordinary_track_document_snapshot,
)
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 straight-host crossover FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_STRAIGHT_CROSSOVER_FIXTURE",
    ROOT / "tmp/phase8-straight-crossover/straight-source.FCStd",
)).resolve()
SOURCE_DOCUMENT_SEMANTIC_SHA256 = (
    "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
)
LEGACY_CONTRACT = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
ROUTE_ID = "straight-phase1-curve-entrance"
HOST_NAMES = (
    "RailwayStraightTrackCentreline_R01_T01",
    "RailwayStraightTrackCentreline_R01_T02",
)
TOE_A_MM = 580.134  # The Manager's chainage field has three decimals.
EDIT_TOE_A_MM = 580.135
TOE_B_MM = 1316.0914869924563
EDIT_TOE_B_MM = 1316.0924869924656
MINIMUM_RESULTING_RADIUS_MM = 2761.6371011858214
COMPARISON_TOLERANCE_MM = 1.0e-6
REJECTED_MINIMUM_RADIUS_MM = 3000.0


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_legacy(label, source):
    """Load a frozen macro without invoking its GUI entry point."""
    tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
    final = tree.body[-1]
    assert isinstance(final, ast.Expr)
    assert isinstance(final.value, ast.Call)
    assert isinstance(final.value.func, ast.Name)
    assert final.value.func.id == "run_macro"
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType("straight_crossover_" + label.lower())
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
    return session.module


def _hosts(module, document):
    """Select the same stored straight-route pair in every source."""
    selected = [
        obj for obj in module.turnout_host_objects(document)
        if module.object_string_property(obj, "RouteID", "") == ROUTE_ID
        and module.object_string_property(obj, "GeneratedRole", "")
        == "StraightTrackCentreline"
    ]
    selected.sort(key=lambda obj: obj.Name)
    assert tuple(obj.Name for obj in selected) == HOST_NAMES
    for number, host in enumerate(selected, start=1):
        assert module.object_string_property(
            host, "TemplateSetID", "",
        ) == "SET-001"
        assert module._integer_object_property(
            host, "TrackNumber", 0,
        ) == number
        assert math.isclose(
            float(module.turnout_host_alignment(host)["total"]),
            1500.0,
            rel_tol=0.0,
            abs_tol=COMPARISON_TOLERANCE_MM,
        )
    return tuple(selected)


def _args(module, document, hosts, radius_mm=600.0):
    return (
        document, hosts[0], hosts[1], TOE_A_MM,
        module.CROSSOVER_ARRANGEMENT_FACING,
        module.CROSSOVER_HAND_AUTO,
        16.5, 1.0, radius_mm,
    )


def _neutral_version(value, edited=False):
    """Remove only frozen-version differences from compared configs."""
    result = json.loads(json.dumps(value, sort_keys=True))
    assert isinstance(result, dict)
    if edited:
        assert result["edited_from_macro_version"] == result["macro_version"]
        del result["edited_from_macro_version"]
    for config in (
        result, result["turnout_a_config"], result["turnout_b_config"],
    ):
        assert isinstance(config.get("macro_version"), str)
        del config["macro_version"]
    return result


def _shape_state(shape):
    if shape is None or shape.isNull():
        return None
    assert shape.isValid(), "A generated crossover shape is invalid"
    brep = shape.exportBrepToString()
    return {
        "brep_sha256": hashlib.sha256(brep.encode("utf-8")).hexdigest(),
        "shape_type": str(shape.ShapeType),
        "vertices": len(shape.Vertexes),
        "edges": len(shape.Edges),
        "faces": len(shape.Faces),
        "solids": len(shape.Solids),
        "summary": recipe.shape_summary(shape),
    }


def _history(document):
    return {
        "mode": int(document.UndoMode),
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": tuple(str(name) for name in document.UndoNames),
        "redo_names": tuple(str(name) for name in document.RedoNames),
    }


def _property_value(obj, name):
    value = getattr(obj, name)
    if obj.getTypeIdOfProperty(name) != "Materials::PropertyMaterial":
        return str(value)
    # FreeCAD returns a copied Material whose repr contains its address.
    # Keep its persisted UUID and material data instead of that address.
    return json.dumps({
        "type": value.TypeId,
        "uuid": value.UUID,
        "parent": value.Parent,
        "properties": value.Properties,
        "legacy_properties": value.LegacyProperties,
        "physical_models": value.PhysicalModels,
        "appearance_models": value.AppearanceModels,
    }, sort_keys=True)


def _snapshot(document):
    """Capture stored properties, memberships, exact shapes, and history."""
    objects = []
    for obj in document.Objects:
        properties = tuple(sorted(
            (name, _property_value(obj, name))
            for name in obj.PropertiesList
            if name not in {"Shape", "Group", "_Part_ShapeCache"}
        ))
        members = (
            tuple(sorted(member.Name for member in obj.Group))
            if "Group" in obj.PropertiesList else None
        )
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "properties": properties,
            "group_members": members,
            "shape": _shape_state(getattr(obj, "Shape", None)),
        })
    # FreeCAD can enumerate the same objects in another order after Undo.
    objects.sort(key=lambda item: item["name"])
    return {
        "objects": objects,
        "history": _history(document),
        "file_name": str(document.FileName),
    }


def _verify_material_snapshot():
    """Keep identity and material-value changes visible to the snapshot."""
    document = App.newDocument("MaterialSnapshotCheck")
    try:
        obj = document.addObject("Part::Feature", "MaterialWitness")
        original = obj.ShapeMaterial
        before = _snapshot(document)
        assert _snapshot(document) == before
        replacement = Materials.Material()
        assert replacement.UUID != original.UUID
        obj.ShapeMaterial = replacement
        assert _snapshot(document) != before
        obj.ShapeMaterial = original
        assert _snapshot(document) == before
        changed = obj.ShapeMaterial
        changed.Description += " snapshot negative case"
        assert changed.UUID == original.UUID
        obj.ShapeMaterial = changed
        assert _snapshot(document) != before
        obj.ShapeMaterial = original
        assert _snapshot(document) == before
    finally:
        App.closeDocument(document.Name)


def _state_without_history(snapshot):
    return {
        key: value for key, value in snapshot.items()
        if key != "history"
    }


def _persistent_state(snapshot):
    state = _state_without_history(snapshot)
    state["objects"] = [
        {
            **item,
            "shape": (
                {key: value for key, value in item["shape"].items()
                 if key != "brep_sha256"}
                if item["shape"] else None
            ),
        }
        for item in snapshot["objects"]
    ]
    return state


def _crossover_observation(
    module, document, config, solved, *,
    expected_toe_a_mm=TOE_A_MM,
    expected_toe_b_mm=TOE_B_MM,
    edited=False,
):
    """Retain complete railway config, exact B-reps, and production IDs."""
    identifier = str(config["crossover_id"])
    objects = []
    for obj in module._crossover_objects(document, identifier):
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "role": module.object_string_property(obj, "GeneratedRole", ""),
            "template_set_id": module.object_string_property(
                obj, "TemplateSetID", "",
            ),
            "crossover_id": module.object_string_property(
                obj, module.CROSSOVER_ID_PROPERTY, "",
            ),
            "export_subtype": module.object_string_property(
                obj, "ExportSubtype", "",
            ),
            "members": (
                tuple(sorted(member.Name for member in obj.Group))
                if "Group" in obj.PropertiesList else None
            ),
            "shape": _shape_state(getattr(obj, "Shape", None)),
        })
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None
    production = [
        record for record in index["records"]
        if record.get("route_id") == identifier
    ]
    assert len(objects) == 9
    assert sum(item["shape"] is not None for item in objects) == 6
    assert len(production) == 4
    record_ids = [record["record_id"] for record in production]
    assert all(record_ids) and len(set(record_ids)) == len(record_ids)
    assert config == module.crossover_config_by_id(document, identifier)
    assert identifier == "XO-001"
    assert config["host_a_object"] == HOST_NAMES[0]
    assert config["host_b_object"] == HOST_NAMES[1]
    assert config["turnout_a_id"] == "XO-001-A001"
    assert config["turnout_b_id"] == "XO-001-B001"
    assert config["production_ready"] is False
    assert config["host_integration_allowed"] is False
    assert float(config["toe_chainage_a"]) == expected_toe_a_mm
    assert math.isclose(
        float(config["minimum_resulting_radius"]),
        MINIMUM_RESULTING_RADIUS_MM,
        rel_tol=0.0,
        abs_tol=COMPARISON_TOLERANCE_MM,
    )
    assert math.isclose(
        float(config["toe_chainage_b"]),
        expected_toe_b_mm,
        rel_tol=0.0,
        abs_tol=COMPARISON_TOLERANCE_MM,
    )
    assert solved["toe_chainage_b"] == config["toe_chainage_b"]
    if edited:
        assert config["edit_revision"] == 1
    return {
        "config": _neutral_version(config, edited=edited),
        "objects": objects,
        "production_records": production,
    }


def _expect_b16_rejection(module, document, arguments):
    """An unbuildable minimum radius must leave all document state alone."""
    rejected = (*arguments[:-1], REJECTED_MINIMUM_RADIUS_MM)
    before = _snapshot(document)
    diagnostics = []
    for action in (
        lambda: module.solve_rea_c10_crossover_geometry(*rejected),
        lambda: module.create_rea_c10_crossover(*rejected),
    ):
        try:
            action()
        except ValueError as error:
            diagnostic = str(error)
            assert "Host Track B turnout road minimum radius" in diagnostic
            assert "3000.000000 mm" in diagnostic
            diagnostics.append(diagnostic)
        else:
            raise AssertionError("An infeasible straight crossover was accepted")
        assert _snapshot(document) == before
    assert diagnostics[0] == diagnostics[1]
    return diagnostics[0]


def _edit_arguments(document, config, hosts):
    """Use the stored crossover parameters for one toe-chainage edit."""
    return (
        document,
        str(config["crossover_id"]),
        hosts[0],
        hosts[1],
        EDIT_TOE_A_MM,
        str(config["arrangement"]),
        str(config["handing"]),
        float(config["track_gauge"]),
        float(config["flangeway"]),
        float(config["minimum_requested_radius"]),
    )


def _solve_edit(module, arguments):
    return module.solve_rea_c10_crossover_geometry(
        arguments[0], *arguments[2:],
        ignored_crossover_id=arguments[1],
    )


def _expect_b16_edit_rejection(module, document, arguments):
    """Rejected preview and edit must preserve the created crossover."""
    rejected = (*arguments[:-1], REJECTED_MINIMUM_RADIUS_MM)
    before = _snapshot(document)
    diagnostics = []
    for action in (
        lambda: _solve_edit(module, rejected),
        lambda: module.edit_rea_c10_crossover(*rejected),
    ):
        try:
            action()
        except ValueError as error:
            diagnostic = str(error)
            assert "Host Track B turnout road minimum radius" in diagnostic
            assert "3000.000000 mm" in diagnostic
            diagnostics.append(diagnostic)
        else:
            raise AssertionError("An infeasible crossover edit was accepted")
        assert _snapshot(document) == before
    assert diagnostics[0] == diagnostics[1]
    return diagnostics[0]


def _b16_lifecycle(module, document, identifier, before, created):
    """Prove one B16 create Undo/Redo and copied-file save/reopen."""
    assert len(document.Objects) == 32
    assert created["history"]["undo"] == 1
    assert created["history"]["redo"] == 0
    copy_path = pathlib.Path(document.FileName)
    document.undo()
    document.recompute()
    undone = _snapshot(document)
    assert len(document.Objects) == 23
    assert module.crossover_config_by_id(document, identifier) is None
    assert _state_without_history(undone) == _state_without_history(before)
    assert undone["history"]["redo"] == 1
    document.redo()
    document.recompute()
    redone = _snapshot(document)
    assert _state_without_history(redone) == _state_without_history(created)
    assert redone["history"]["redo"] == 0
    document.save()
    saved = _snapshot(document)
    App.closeDocument(document.Name)
    reopened = App.openDocument(str(copy_path))
    assert len(reopened.Objects) == 32
    assert module.crossover_config_by_id(reopened, identifier) is not None
    reopened_state = _snapshot(reopened)
    assert _persistent_state(reopened_state) == _persistent_state(saved)
    return reopened, {
        "after_create": len(created["objects"]),
        "after_undo": len(undone["objects"]),
        "after_redo": len(redone["objects"]),
        "after_reopen": len(reopened_state["objects"]),
    }


def _b16_edit_lifecycle(module, document, identifier, before, edited):
    """Prove one edit Undo/Redo and copied-file save/reopen."""
    assert len(document.Objects) == 32
    assert edited["history"]["undo"] == before["history"]["undo"] + 1
    assert edited["history"]["redo"] == 0
    copy_path = pathlib.Path(document.FileName)
    document.undo()
    document.recompute()
    undone = _snapshot(document)
    assert len(document.Objects) == 32
    assert _state_without_history(undone) == _state_without_history(before)
    assert undone["history"]["redo"] == 1
    document.redo()
    document.recompute()
    redone = _snapshot(document)
    assert _state_without_history(redone) == _state_without_history(edited)
    assert redone["history"]["redo"] == 0
    document.save()
    saved = _snapshot(document)
    App.closeDocument(document.Name)
    reopened = App.openDocument(str(copy_path))
    assert len(reopened.Objects) == 32
    assert module.crossover_config_by_id(reopened, identifier) is not None
    reopened_state = _snapshot(reopened)
    assert _persistent_state(reopened_state) == _persistent_state(saved)
    return reopened, {
        "after_edit": len(edited["objects"]),
        "after_undo": len(undone["objects"]),
        "after_redo": len(redone["objects"]),
        "after_reopen": len(reopened_state["objects"]),
    }


def _selected_pair(module, document):
    """Find the existing unintegrated XO-001 physical representations."""
    assert module.crossover_host_integration_by_id(document, "XO-001") is None
    index = module.production_record_index_for_set(document, "SET-001")
    catalogue = module.hydrate_production_index_records(document, index)
    assert len(catalogue) == 16
    crossover = [
        record for record in catalogue if record["route_id"] == "XO-001"
    ]
    assert len(crossover) == 4
    assert {record["role"] for record in crossover} == {
        module.CROSSOVER_TEMPLATE_ROLE, module.CROSSOVER_OUTLINE_ROLE,
        module.CROSSOVER_RAIL_ROLE, module.CROSSOVER_DATUM_ROLE,
    }
    pair = [
        record for record in crossover
        if record["subtype"] == module.CROSSOVER_SUBTYPE_TEMPLATE
    ]
    assert len(pair) == 2
    outline = next(record for record in pair
                   if record["category"] == module.EXPORT_CATEGORY_CUTTING)
    solid = next(record for record in pair
                 if record["category"] == module.EXPORT_CATEGORY_SOLID)
    assert outline["role"] == module.CROSSOVER_OUTLINE_ROLE
    assert solid["role"] == module.CROSSOVER_TEMPLATE_ROLE
    for record in pair:
        obj = document.getObject(record["source_name"])
        assert module.object_string_property(
            obj, module.CROSSOVER_ID_PROPERTY, "",
        ) == "XO-001"
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
        "route_id": "XO-001",
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
    assert SOURCE.is_file(), (
        "Generate the ignored 1500/450 mm B14 straight fixture first: {}"
        .format(SOURCE)
    )
    source_raw_sha256 = _sha256(SOURCE)
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
    _verify_material_snapshot()

    observations = {}
    edited_observations = {}
    rejection = None
    edit_rejection = None
    lifecycle = None
    edit_lifecycle = None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    export_root = (
        ROOT / "benchmark-output/phase8-straight-crossover-export" / stamp
    )
    export_root.mkdir(parents=True, exist_ok=False)
    print("PHASE8_STRAIGHT_XO_EXPORT_EVIDENCE=" + str(export_root), flush=True)
    exports = {}
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-straight-crossover-"
    ) as temporary:
        for label, module in modules.items():
            copy = pathlib.Path(temporary) / (
                "straight-crossover-{}.FCStd".format(label.lower())
            )
            shutil.copy2(SOURCE, copy)
            document = App.openDocument(str(copy))
            try:
                document.UndoMode = 1
                assert len(document.Objects) == 23
                source_semantic = ordinary_track_document_snapshot(
                    module, document,
                )["semantic_sha256"]
                assert source_semantic == SOURCE_DOCUMENT_SEMANTIC_SHA256
                hosts = _hosts(module, document)
                arguments = _args(module, document, hosts)
                before = _snapshot(document)
                if label == "B16":
                    rejection = _expect_b16_rejection(
                        module, document, arguments,
                    )
                solved = module.solve_rea_c10_crossover_geometry(*arguments)
                assert _snapshot(document) == before
                config = module.create_rea_c10_crossover(
                    *arguments, pre_solved=solved,
                )
                created = _snapshot(document)
                assert len(document.Objects) == 32
                assert created["history"]["undo"] == (
                    before["history"]["undo"] + 1
                )
                observations[label] = _crossover_observation(
                    module, document, config, solved,
                )
                exports[label] = []
                for number in (1, 2):
                    directory = export_root / "{}-{}".format(label, number)
                    directory.mkdir()
                    exports[label].append(_selected_export(
                        module, document, directory,
                    ))
                    assert _snapshot(document) == created
                assert (exports[label][0]["comparison"]
                        == exports[label][1]["comparison"])
                if label == "B16":
                    document, lifecycle = _b16_lifecycle(
                        module, document, config["crossover_id"],
                        before, created,
                    )
                else:
                    document.save()
                    saved = _snapshot(document)
                    App.closeDocument(document.Name)
                    document = App.openDocument(str(copy))
                    assert _persistent_state(_snapshot(document)) == (
                        _persistent_state(saved)
                    )

                document.UndoMode = 1
                hosts = _hosts(module, document)
                current = module.crossover_config_by_id(
                    document, config["crossover_id"],
                )
                edit_arguments = _edit_arguments(document, current, hosts)
                before_edit = _snapshot(document)
                if label == "B16":
                    edit_rejection = _expect_b16_edit_rejection(
                        module, document, edit_arguments,
                    )
                solved_edit = _solve_edit(module, edit_arguments)
                if label == "B16":
                    assert solved_edit["complete_radius_preflight"][
                        "accepted"
                    ] is True
                assert _snapshot(document) == before_edit
                updated = module.edit_rea_c10_crossover(
                    *edit_arguments, pre_solved=solved_edit,
                )
                edited = _snapshot(document)
                assert len(document.Objects) == 32
                assert edited["history"]["undo"] == (
                    before_edit["history"]["undo"] + 1
                )
                edited_observations[label] = _crossover_observation(
                    module, document, updated, solved_edit,
                    expected_toe_a_mm=EDIT_TOE_A_MM,
                    expected_toe_b_mm=EDIT_TOE_B_MM,
                    edited=True,
                )
                assert [
                    item["record_id"]
                    for item in edited_observations[label][
                        "production_records"
                    ]
                ] == [
                    item["record_id"]
                    for item in observations[label]["production_records"]
                ]
                if label == "B16":
                    document, edit_lifecycle = _b16_edit_lifecycle(
                        module, document, config["crossover_id"],
                        before_edit, edited,
                    )
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == copy:
                        App.closeDocument(opened.Name)
            assert _sha256(SOURCE) == source_raw_sha256

    assert observations["B14"] == observations["B15"]
    assert observations["B15"] == observations["B16"]
    assert (exports["B14"][0]["comparison"]
            == exports["B15"][0]["comparison"]
            == exports["B16"][0]["comparison"])
    assert edited_observations["B14"] == edited_observations["B15"]
    assert edited_observations["B15"] == edited_observations["B16"]
    assert rejection is not None and lifecycle is not None
    assert edit_rejection is not None and edit_lifecycle is not None
    edited_result = edited_observations["B16"]
    witness = {
        "host_route_id": ROUTE_ID,
        "toe_a_mm": TOE_A_MM,
        "toe_b_mm": TOE_B_MM,
        "minimum_resulting_radius_mm": MINIMUM_RESULTING_RADIUS_MM,
        "crossover_id": "XO-001",
        "production_record_count": len(
            observations["B16"]["production_records"]
        ),
        "crossover_object_count": len(observations["B16"]["objects"]),
        "exact_brep_sha256": {
            item["role"]: item["shape"]["brep_sha256"]
            for item in observations["B16"]["objects"]
            if item["shape"] is not None
        },
        "rejection": rejection,
        "lifecycle": lifecycle,
        "edit": {
            "toe_a_mm": EDIT_TOE_A_MM,
            "toe_b_mm": edited_result["config"]["toe_chainage_b"],
            "minimum_resulting_radius_mm": edited_result[
                "config"
            ]["minimum_resulting_radius"],
            "edit_revision": edited_result["config"]["edit_revision"],
            "crossover_object_count": len(edited_result["objects"]),
            "production_record_ids": [
                item["record_id"]
                for item in edited_result["production_records"]
            ],
            "exact_brep_sha256": {
                item["role"]: item["shape"]["brep_sha256"]
                for item in edited_result["objects"]
                if item["shape"] is not None
            },
            "rejection": edit_rejection,
            "lifecycle": edit_lifecycle,
        },
        "source_raw_sha256": source_raw_sha256,
        "source_document_semantic_sha256": (
            SOURCE_DOCUMENT_SEMANTIC_SHA256
        ),
        "source_files_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                pathlib.Path(__file__),
                ROOT / contract["source_state"]["b14"]["path"],
                ROOT / contract["source_state"]["b15"]["path"],
                ROOT / "TrackTemplate.FCMacro",
            )
        },
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
    print("PHASE8_STRAIGHT_CROSSOVER_WITNESS=" + json.dumps(
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


if __name__ in {"__main__", "freecad_validate_phase8_straight_host_crossover"}:
    _run_as_script()
