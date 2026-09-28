"""Prove one B16 XO-001 host-integration transaction and record lifecycle.

The fixed B14 source is opened only through temporary copies. This is a
bounded Phase 8 Exit 2 and PR-17 check, not production-output acceptance.
"""

import copy
import hashlib
import json
import os
import pathlib
import runpy
import shutil
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_HOST_INTEGRATION_SOURCE_ROOT",
    pathlib.Path(__file__).resolve().parents[1],
)).resolve()
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 crossover host integration recovery FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"
IDENTIFIER = "XO-001"
FAULT_BUILD = "injected host-integration build failure"
FAULT_TAG = "injected first host-integration tag failure"
FAULT_WRITE = "injected host-integration record-write failure"


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
    # A qualified control showed that a read-only integration build changes
    # exportBrepToString() bytes for four existing shapes. Compare stable
    # geometric quantities while the snapshot checks stored object state.
    return {
        "summary": recipe.shape_summary(shape),
        "shape_type": str(shape.ShapeType),
        "vertices": len(shape.Vertexes),
        "length_mm": round(float(shape.Length), 9),
        "area_mm2": round(float(shape.Area), 9),
        "volume_mm3": round(float(shape.Volume), 9),
        "valid": bool(shape.isValid()),
    }


def _records(module, document):
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None and index["schema_version"] == 2
    return index["records"]


def _chair_names(module, document):
    return sorted(
        str(obj.Name)
        for obj in module._chair_analysis_display_objects(
            document, "crossover", IDENTIFIER,
        )
    )


def _snapshot(module, document):
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
                # FreeCAD prints ShapeMaterial as a transient pointer.
                if name not in {
                    "Shape", "Group", "_Part_ShapeCache", "ShapeMaterial",
                }
            )),
            "members": (
                tuple(sorted(member.Name for member in obj.Group))
                if "Group" in obj.PropertiesList else None
            ),
            "shape": _shape(obj),
            "visibility": (
                bool(view.Visibility)
                if view is not None and hasattr(view, "Visibility")
                else None
            ),
        })
    # FreeCAD can enumerate objects in a different order after Undo.
    objects.sort(key=lambda item: item["name"])
    return {
        "objects": objects,
        "config": recipe.stable(
            module.crossover_config_by_id(document, IDENTIFIER)
        ),
        "records": _records(module, document),
        "chairs": _chair_names(module, document),
        "history": _history(document),
        "file_name": str(document.FileName),
    }


def _without_history(snapshot):
    return {
        key: value for key, value in snapshot.items()
        if key != "history"
    }


def _persistent(snapshot):
    return _without_history(snapshot)


def _assert_persistent_reopen_equal(saved, reopened):
    expected = _persistent(saved)
    actual = copy.deepcopy(_persistent(reopened))
    for before, after in zip(expected["objects"], actual["objects"]):
        if before["name"] != after["name"]:
            break
        if before["name"] != "ModelRailwayCurve":
            continue
        old_shape = before["shape"]
        new_shape = after["shape"]
        if old_shape is None or new_shape is None:
            break
        # A qualified save/reopen diagnostic found a 1e-9 mm² derived-area
        # drift here; every other persisted and geometric field stays exact.
        if abs(old_shape["area_mm2"] - new_shape["area_mm2"]) <= 2e-9:
            new_shape["area_mm2"] = old_shape["area_mm2"]
        break
    assert actual == expected, _difference(saved, reopened)


def _difference(before, after):
    old = {item["name"]: item for item in before["objects"]}
    new = {item["name"]: item for item in after["objects"]}
    changed = {}
    for name in sorted(set(old) & set(new)):
        if old[name] == new[name]:
            continue
        fields = {}
        for field in old[name]:
            if old[name][field] == new[name][field]:
                continue
            if field == "properties":
                previous = dict(old[name][field])
                current = dict(new[name][field])
                fields[field] = sorted(
                    property_name
                    for property_name in set(previous) | set(current)
                    if previous.get(property_name) != current.get(property_name)
                )
            else:
                fields[field] = {
                    "before": old[name][field],
                    "after": new[name][field],
                }
        changed[name] = fields
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": changed,
        "config_equal": before["config"] == after["config"],
        "records_equal": before["records"] == after["records"],
        "chairs_before": before["chairs"],
        "chairs_after": after["chairs"],
        "history_before": before["history"],
        "history_after": after["history"],
    }


def _assert_equal(before, after, label):
    if before != after:
        raise AssertionError(
            "{} changed the copied document: {!r}".format(
                label, _difference(before, after),
            )
        )


def _expect_error(action, expected_text):
    try:
        action()
    except (RuntimeError, ValueError) as error:
        assert expected_text.lower() in str(error).lower(), str(error)
        return str(error)
    raise AssertionError("Expected command rejection: " + expected_text)


def _prepared_copy(module, source, target, chainage_mm):
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    config, _selection = recipe.create_controlled_crossover(
        module, document, chainage_mm,
    )
    assert config["crossover_id"] == IDENTIFIER
    result = module.apply_crossover_b4_timbering(document, IDENTIFIER)
    assert result["applied"] is True
    assert result["timber_resolution_complete"] is True
    assert len(document.Objects) == 20
    assert len(_records(module, document)) == 8
    assert module.analyse_entity_chair_positions(
        document, "crossover", IDENTIFIER,
    )
    assert _chair_names(module, document)
    assert len(document.Objects) == 22
    return document


def _rejection_probe(module, source, target, chainage_mm, undo_mode):
    document = _prepared_copy(module, source, target, chainage_mm)
    try:
        document.UndoMode = undo_mode
        before = _snapshot(module, document)
        original_builder = module.build_crossover_host_integration
        calls = []
        expected_create = FAULT_BUILD if undo_mode == 1 else "Undo"
        expected_remove = (
            "no host integration to remove" if undo_mode == 1 else "Undo"
        )

        def failing_builder(*args, **kwargs):
            calls.append((args, kwargs))
            raise RuntimeError(FAULT_BUILD)

        module.build_crossover_host_integration = failing_builder
        try:
            build_error = _expect_error(
                lambda: module.create_crossover_host_integration(
                    document, IDENTIFIER,
                ), expected_create,
            )
        finally:
            module.build_crossover_host_integration = original_builder
        assert len(calls) == (1 if undo_mode == 1 else 0), len(calls)
        _assert_equal(
            before, _snapshot(module, document),
            "Rejected host-integration create in UndoMode {}".format(undo_mode),
        )

        remove_error = _expect_error(
            lambda: module.remove_crossover_host_integration(
                document, IDENTIFIER,
            ), expected_remove,
        )
        _assert_equal(
            before, _snapshot(module, document),
            "Rejected host-integration remove in UndoMode {}".format(undo_mode),
        )
        if undo_mode == 0:
            # A ready operation without FreeCAD Undo must reject before build.
            guarded = _expect_error(
                lambda: module.create_crossover_host_integration(
                    document, IDENTIFIER,
                ), "Undo",
            )
            _assert_equal(before, _snapshot(module, document),
                          "Undo-disabled create")
        else:
            guarded = None
        return {
            "undo_mode": undo_mode,
            "build_failure": build_error,
            "missing_integration": remove_error,
            "undo_disabled_create": guarded,
            "chair_count": len(before["chairs"]),
        }
    finally:
        App.closeDocument(document.Name)


def _injected_create_failure(module, document, original_name, failure,
                             after_call=False):
    before = _snapshot(module, document)
    original = getattr(module, original_name)
    calls = []

    def injected(*args, **kwargs):
        if original_name == "tag_generated_object":
            if str(args[1]) != module.CROSSOVER_INTEGRATION_GROUP_ROLE:
                return original(*args, **kwargs)
            calls.append(True)
            raise RuntimeError(failure)
        calls.append(True)
        if after_call:
            original(*args, **kwargs)
        raise RuntimeError(failure)

    setattr(module, original_name, injected)
    try:
        _expect_error(
            lambda: module.create_crossover_host_integration(
                document, IDENTIFIER,
            ), failure,
        )
    finally:
        setattr(module, original_name, original)
    assert len(calls) == 1, (original_name, calls)
    _assert_equal(before, _snapshot(module, document),
                  "Failed host-integration create at " + original_name)


def _injected_remove_record_failure(module, document):
    before = _snapshot(module, document)
    original = module._turnout_write_production_records
    calls = []

    def failing_writer(*args, **kwargs):
        calls.append(True)
        original(*args, **kwargs)
        raise RuntimeError(FAULT_WRITE)

    module._turnout_write_production_records = failing_writer
    try:
        _expect_error(
            lambda: module.remove_crossover_host_integration(
                document, IDENTIFIER,
            ), FAULT_WRITE,
        )
    finally:
        module._turnout_write_production_records = original
    assert len(calls) == 1, calls
    _assert_equal(before, _snapshot(module, document),
                  "Failed host-integration remove after record write")


def _record_bindings(document, records):
    bound = {}
    for record in records:
        source_name = str(record["source_name"])
        source = document.getObject(source_name)
        assert source is not None, (record["record_id"], source_name)
        value = str(getattr(source, "ProductionRecordIDsJSON", "[]"))
        ids = json.loads(value)
        assert record["record_id"] in ids, (record["record_id"], ids)
        bound[record["record_id"]] = source_name
    return bound


def _lifecycle_probe(module, source, target, chainage_mm):
    document = _prepared_copy(module, source, target, chainage_mm)
    try:
        before = _snapshot(module, document)
        original_ids = [item["record_id"] for item in before["records"]]
        original_bindings = _record_bindings(document, before["records"])
        _injected_create_failure(
            module, document, "tag_generated_object", FAULT_TAG,
        )
        _injected_create_failure(
            module, document, "_turnout_write_production_records",
            FAULT_WRITE, after_call=True,
        )

        result = module.create_crossover_host_integration(
            document, IDENTIFIER,
        )
        assert result["integration_active"] is True
        assert result["production_ready"] is False
        integration = module.crossover_host_integration_by_id(
            document, IDENTIFIER,
        )
        assert integration is not None
        assert len(integration["integration_object_names"]) == 6
        assert all(
            document.getObject(name) is not None
            for name in integration["integration_object_names"]
        )
        created = _snapshot(module, document)
        assert len(created["objects"]) == 26
        assert not created["chairs"]
        assert created["history"]["undo"] == before["history"]["undo"] + 1
        assert created["history"]["redo"] == 0
        assert len(created["records"]) == 7
        created_ids = [item["record_id"] for item in created["records"]]
        removed_ids = set(original_ids) - set(created_ids)
        added_ids = set(created_ids) - set(original_ids)
        assert len(removed_ids) == 4
        assert len(added_ids) == 3
        assert set(integration["source_record_ids"]) == removed_ids
        _record_bindings(document, created["records"])

        document.undo()
        document.recompute()
        assert _without_history(_snapshot(module, document)) == (
            _without_history(before)
        )
        document.redo()
        document.recompute()
        assert _without_history(_snapshot(module, document)) == (
            _without_history(created)
        )

        document.save()
        saved = _snapshot(module, document)
        App.closeDocument(document.Name)
        document = App.openDocument(str(target))
        reopened = _snapshot(module, document)
        _assert_persistent_reopen_equal(saved, reopened)
        assert module.crossover_host_integration_by_id(
            document, IDENTIFIER,
        ) is not None
        _record_bindings(document, reopened["records"])

        document.UndoMode = 0
        undo_disabled = _snapshot(module, document)
        _expect_error(
            lambda: module.remove_crossover_host_integration(
                document, IDENTIFIER,
            ), "Undo",
        )
        _assert_equal(undo_disabled, _snapshot(module, document),
                      "Undo-disabled remove")
        document.UndoMode = 1
        _injected_remove_record_failure(module, document)
        before_remove = _snapshot(module, document)

        removed = module.remove_crossover_host_integration(
            document, IDENTIFIER,
        )
        assert removed["integration_active"] is False
        assert removed["production_ready"] is False
        assert module.crossover_host_integration_by_id(
            document, IDENTIFIER,
        ) is None
        after_remove = _snapshot(module, document)
        assert len(after_remove["objects"]) == 20
        assert len(after_remove["records"]) == 8
        assert {
            item["record_id"] for item in after_remove["records"]
        } == set(original_ids)
        assert _record_bindings(document, after_remove["records"]) == (
            original_bindings
        )
        assert after_remove["history"]["undo"] == (
            before_remove["history"]["undo"] + 1
        )
        assert after_remove["history"]["redo"] == 0

        document.undo()
        document.recompute()
        assert _without_history(_snapshot(module, document)) == (
            _without_history(before_remove)
        )
        document.redo()
        document.recompute()
        assert _without_history(_snapshot(module, document)) == (
            _without_history(after_remove)
        )
        document.save()
        saved_removed = _snapshot(module, document)
        App.closeDocument(document.Name)
        document = App.openDocument(str(target))
        reopened_removed = _snapshot(module, document)
        _assert_persistent_reopen_equal(saved_removed, reopened_removed)
        assert _record_bindings(document, reopened_removed["records"]) == (
            original_bindings
        )
        return {
            "source_records": len(original_ids),
            "integrated_records": len(created_ids),
            "replaced_record_ids": sorted(removed_ids),
            "integrated_record_ids": sorted(added_ids),
            "integration_object_count": len(integration["integration_object_names"]),
            "create_undo_delta": created["history"]["undo"] - (
                before["history"]["undo"]
            ),
            "remove_undo_delta": after_remove["history"]["undo"] - (
                before_remove["history"]["undo"]
            ),
            "removed_record_order": [
                item["record_id"] for item in after_remove["records"]
            ],
            "saved_reopened": True,
        }
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    fixture = contract["fixture"]
    source = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_HOST_INTEGRATION_FIXTURE",
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
        prefix="tracktemplate-phase8-host-integration-"
    ) as temporary:
        temporary = pathlib.Path(temporary)
        rejections = [
            _rejection_probe(
                module, source,
                temporary / "rejected-mode-{}.FCStd".format(mode),
                chainage_mm, mode,
            )
            for mode in (1, 0)
        ]
        print("HOST_INTEGRATION_REJECTION_WITNESS=" + json.dumps(
            rejections, sort_keys=True,
        ), flush=True)
        lifecycle = _lifecycle_probe(
            module, source, temporary / "lifecycle.FCStd", chainage_mm,
        )
        print("HOST_INTEGRATION_LIFECYCLE_WITNESS=" + json.dumps(
            lifecycle, sort_keys=True,
        ), flush=True)

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
    "__main__", "freecad_validate_phase8_crossover_host_integration_recovery",
}:
    _run_as_script()
