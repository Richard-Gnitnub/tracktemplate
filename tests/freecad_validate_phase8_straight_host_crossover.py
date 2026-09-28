"""Compare one copied straight-host crossover across B14, B15, and B16.

This qualified FreeCAD check uses one B14 Generate/Replace document with
1500/450 mm connected straight routes. The source document is never opened
for mutation. It does not claim real-GUI, export, or Phase 8 acceptance.
"""

import ast
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

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
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
TOE_B_MM = 1316.0914869924563
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


def _neutral_version(value):
    """Remove only the three inherited macro-version fields."""
    result = json.loads(json.dumps(value, sort_keys=True))
    assert isinstance(result, dict)
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


def _snapshot(document):
    """Capture stored properties, memberships, exact shapes, and history."""
    objects = []
    for obj in document.Objects:
        properties = tuple(sorted(
            (name, str(getattr(obj, name)))
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
    return {
        "objects": objects,
        "history": _history(document),
        "file_name": str(document.FileName),
    }


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


def _crossover_observation(module, document, config, solved):
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
    assert math.isclose(
        float(config["minimum_resulting_radius"]),
        MINIMUM_RESULTING_RADIUS_MM,
        rel_tol=0.0,
        abs_tol=COMPARISON_TOLERANCE_MM,
    )
    assert math.isclose(
        float(config["toe_chainage_b"]),
        TOE_B_MM,
        rel_tol=0.0,
        abs_tol=COMPARISON_TOLERANCE_MM,
    )
    assert solved["toe_chainage_b"] == config["toe_chainage_b"]
    return {
        "config": _neutral_version(config),
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

    observations = {}
    rejection = None
    lifecycle = None
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
                if label == "B16":
                    document, lifecycle = _b16_lifecycle(
                        module, document, config["crossover_id"],
                        before, created,
                    )
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == copy:
                        App.closeDocument(opened.Name)
            assert _sha256(SOURCE) == source_raw_sha256

    assert observations["B14"] == observations["B15"]
    assert observations["B15"] == observations["B16"]
    assert rejection is not None and lifecycle is not None
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
        "source_raw_sha256": source_raw_sha256,
        "source_document_semantic_sha256": (
            SOURCE_DOCUMENT_SEMANTIC_SHA256
        ),
    }
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
