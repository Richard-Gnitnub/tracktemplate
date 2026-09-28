"""Prove B16 crossover edit recovery with retained chair display."""

import hashlib
import json
import os
import pathlib
import runpy
import shutil
import sys
import tempfile

import FreeCAD as App


SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.compatibility.crossover_preflight import (  # noqa: E402
    CrossoverPreflightAdapter,
)


SENTINEL = "Phase 8 crossover edit recovery FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = SOURCE_ROOT / "reference/contracts/phase1-crossover-timbering.json"
FAULT = "Phase 8 injected crossover edit build failure"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_product():
    assert pathlib.Path(api.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/api.py"
    )
    launcher = runpy.run_path(str(SOURCE_ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](SOURCE_ROOT)
    assert modular_api is api
    transition = bootstrap.load_contract(
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        SOURCE_ROOT, api, transition,
    )
    module = session.module
    edit = module.edit_rea_c10_crossover
    assert isinstance(edit.__self__, CrossoverPreflightAdapter)
    assert edit.__func__ is CrossoverPreflightAdapter.edit
    return module


def _history(document):
    return {
        "mode": int(document.UndoMode),
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": tuple(str(name) for name in document.UndoNames),
        "redo_names": tuple(str(name) for name in document.RedoNames),
    }


def _shape(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        return None
    brep = shape.exportBrepToString()
    return hashlib.sha256(brep.encode("utf-8")).hexdigest()


def _snapshot(module, document, identifier):
    objects = []
    for obj in document.Objects:
        view = getattr(obj, "ViewObject", None)
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "role": module.object_string_property(
                obj, "GeneratedRole", "",
            ),
            "properties": tuple(sorted(
                (name, str(getattr(obj, name)))
                for name in obj.PropertiesList
                # FreeCAD prints ShapeMaterial as a transient pointer address.
                if name not in {
                    "Shape", "Group", "_Part_ShapeCache", "ShapeMaterial",
                }
            )),
            "members": (
                tuple(member.Name for member in obj.Group)
                if "Group" in obj.PropertiesList else None
            ),
            "shape": _shape(obj),
            "visibility": (
                bool(view.Visibility)
                if view is not None and hasattr(view, "Visibility")
                else None
            ),
        })
    # Undo can change FreeCAD's object enumeration without changing identity.
    objects.sort(key=lambda item: item["name"])
    return {
        "objects": objects,
        "config": recipe.stable(
            module.crossover_config_by_id(document, identifier)
        ),
        "history": _history(document),
        "file_name": str(document.FileName),
    }


def _without_history(snapshot):
    return {
        key: value for key, value in snapshot.items()
        if key != "history"
    }


def _chair_names(module, document, identifier):
    return sorted(
        str(obj.Name)
        for obj in module._chair_analysis_display_objects(
            document, "crossover", identifier,
        )
    )


def _edit_arguments(module, document, config, chainage_mm):
    return (
        document,
        str(config["crossover_id"]),
        document.getObject(str(config["host_a_object"])),
        document.getObject(str(config["host_b_object"])),
        float(chainage_mm),
        str(config["arrangement"]),
        str(config["handing"]),
        float(config["track_gauge"]),
        float(config["flangeway"]),
        float(config["minimum_requested_radius"]),
    )


def _checked_edit_preflight(module, arguments):
    solved = module.solve_rea_c10_crossover_geometry(
        arguments[0], *arguments[2:],
        ignored_crossover_id=arguments[1],
    )
    assert solved["complete_radius_preflight"]["accepted"] is True
    return solved


def _prepared_copy(module, source, target, chainage_mm, undo_mode):
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    document.UndoMode = undo_mode
    config, _selected = recipe.create_controlled_crossover(
        module, document, chainage_mm,
    )
    identifier = str(config["crossover_id"])
    assert identifier == "XO-001"
    b4_result = module.apply_crossover_b4_timbering(
        document, identifier,
    )
    assert b4_result["applied"] is True
    chair_result = module.analyse_entity_chair_positions(
        document, "crossover", identifier,
    )
    assert chair_result
    chair_names = _chair_names(module, document, identifier)
    assert chair_names, "The copied crossover has no chair display"
    return document, chair_names


def _failure_probe(module, source, target, chainage_mm, undo_mode):
    document, chair_names = _prepared_copy(
        module, source, target, chainage_mm, undo_mode,
    )
    try:
        config = module.crossover_config_by_id(document, "XO-001")
        arguments = _edit_arguments(
            module, document, config, chainage_mm,
        )
        solved = _checked_edit_preflight(module, arguments)
        before = _snapshot(module, document, "XO-001")
        original_builder = module._build_rea_c10_crossover_geometry
        calls = []

        def failing_builder(*_args, **_kwargs):
            calls.append(True)
            raise RuntimeError(FAULT)

        module._build_rea_c10_crossover_geometry = failing_builder
        try:
            try:
                module.edit_rea_c10_crossover(
                    *arguments, pre_solved=solved,
                )
            except RuntimeError as error:
                assert str(error) == FAULT, str(error)
            else:
                raise AssertionError("Injected crossover edit failure missed")
        finally:
            module._build_rea_c10_crossover_geometry = original_builder
        assert len(calls) == 1, calls
        after = _snapshot(module, document, "XO-001")
        missing_chair = sorted(
            set(chair_names) - set(_chair_names(
                module, document, "XO-001",
            ))
        )
        before_names = {obj["name"] for obj in before["objects"]}
        after_names = {obj["name"] for obj in after["objects"]}
        return {
            "mode": undo_mode,
            "same_state": after == before,
            "missing_chair": missing_chair,
            "removed_objects": sorted(before_names - after_names),
            "history_equal": after["history"] == before["history"],
            "config_equal": after["config"] == before["config"],
            "snapshot_before": before,
            "snapshot_after": after,
        }
    finally:
        App.closeDocument(document.Name)


def _success_probe(module, source, target, chainage_mm):
    document, chair_names = _prepared_copy(
        module, source, target, chainage_mm, 1,
    )
    try:
        config = module.crossover_config_by_id(document, "XO-001")
        edited_chainage_mm = chainage_mm + 0.001
        arguments = _edit_arguments(
            module, document, config, edited_chainage_mm,
        )
        solved = _checked_edit_preflight(module, arguments)
        before = _snapshot(module, document, "XO-001")
        updated = module.edit_rea_c10_crossover(
            *arguments, pre_solved=solved,
        )
        assert updated["crossover_id"] == "XO-001"
        assert updated["edit_revision"] == (
            int(config.get("edit_revision") or 0) + 1
        )
        assert float(updated["toe_chainage_a"]) == edited_chainage_mm
        assert not set(chair_names) & set(
            _chair_names(module, document, "XO-001")
        )
        assert module._crossover_b4_object(document, "XO-001") is None
        after = _snapshot(module, document, "XO-001")
        assert after["history"]["undo"] == before["history"]["undo"] + 1
        assert after["history"]["redo"] == 0
        document.undo()
        document.recompute()
        undone = _snapshot(module, document, "XO-001")
        assert _without_history(undone) == _without_history(before)
        assert set(chair_names) == set(
            _chair_names(module, document, "XO-001")
        )
        document.redo()
        document.recompute()
        redone = _snapshot(module, document, "XO-001")
        assert _without_history(redone) == _without_history(after)
        document.save()
        saved = _snapshot(module, document, "XO-001")
        copy_path = pathlib.Path(document.FileName)
        App.closeDocument(document.Name)
        document = App.openDocument(str(copy_path))
        reopened = _snapshot(module, document, "XO-001")
        assert reopened["config"] == saved["config"]
        assert _chair_names(module, document, "XO-001") == []
        assert module._crossover_b4_object(document, "XO-001") is None
        return {
            "edited_chainage_mm": edited_chainage_mm,
            "chair_removed": len(chair_names),
            "saved_config_equal": reopened["config"] == saved["config"],
        }
    finally:
        App.closeDocument(document.Name)


def validate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    source = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_CROSSOVER_EDIT_FIXTURE",
        SOURCE_ROOT / contract["fixture"]["path"],
    )).resolve()
    assert source.is_file(), source
    fixture_hash = _sha256(source)
    assert fixture_hash == contract["fixture"]["sha256"]
    for label in ("b14", "b15"):
        item = contract["source_state"][label]
        assert _sha256(SOURCE_ROOT / item["path"]) == item["sha256"]
    module = _load_product()
    chainage_mm = float(contract["scenario"]["host_a_chainage_mm"])
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-crossover-edit-"
    ) as temporary:
        temporary = pathlib.Path(temporary)
        failures = [
            _failure_probe(
                module, source,
                temporary / "failed-edit-mode-{}.FCStd".format(mode),
                chainage_mm, mode,
            )
            for mode in (1, 0)
        ]
        summary = [
            {key: item[key] for key in (
                "mode", "same_state", "missing_chair", "removed_objects",
                "history_equal", "config_equal",
            )}
            for item in failures
        ]
        print("CROSSOVER_EDIT_RECOVERY_WITNESS={}".format(
            json.dumps(summary, sort_keys=True)
        ), flush=True)
        assert all(item["same_state"] for item in failures), summary
        success = _success_probe(
            module, source, temporary / "successful-edit.FCStd",
            chainage_mm,
        )
        print("CROSSOVER_EDIT_SUCCESS_WITNESS={}".format(
            json.dumps(success, sort_keys=True)
        ), flush=True)
    assert _sha256(source) == fixture_hash
    print(SENTINEL, flush=True)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase8_crossover_edit_recovery"}:
    _run_as_script()
