"""Prove one B16 TO-001 host-integration transaction and record lifecycle.

Use a copy of the fixed B14 base document. This is bounded Phase 8 Exit 2
and PR-17 evidence, not production-output acceptance.
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
import traceback

import FreeCAD as App


ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_TURNOUT_HOST_SOURCE_ROOT",
    pathlib.Path(__file__).resolve().parents[1],
)).resolve()
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import turnout_recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 turnout host integration recovery FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
FIXTURE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)
FAULT_BUILD = "injected turnout host-integration build failure"
FAULT_TAG = "injected turnout host-integration tag failure"
FAULT_WRITE = "injected turnout host-integration record-write failure"
IDENTIFIER = turnout_recipe.TURNOUT_ID


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
    return {
        "summary": turnout_recipe.shape_summary(shape),
        "shape_type": str(shape.ShapeType),
        "vertices": len(shape.Vertexes),
        "length_mm": round(float(shape.Length), 9),
        "area_mm2": round(float(shape.Area), 9),
        "volume_mm3": round(float(shape.Volume), 9),
        "valid": bool(shape.isValid()),
    }


def _snapshot(module, document):
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None and index["schema_version"] == 2
    objects = []
    for obj in document.Objects:
        view = getattr(obj, "ViewObject", None)
        objects.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
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
    objects.sort(key=lambda item: item["name"])
    return {
        "objects": objects,
        "config": copy.deepcopy(
            module.turnout_config_by_id(document, IDENTIFIER)
        ),
        "records": copy.deepcopy(index["records"]),
        "chairs": tuple(sorted(
            str(obj.Name)
            for obj in module._chair_analysis_display_objects(
                document, "turnout", IDENTIFIER,
            )
        )),
        "history": _history(document),
        "file_name": str(document.FileName),
    }


def _difference(before, after):
    old = {item["name"]: item for item in before["objects"]}
    new = {item["name"]: item for item in after["objects"]}
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": sorted(
            name for name in set(old) & set(new) if old[name] != new[name]
        ),
        "config_equal": before["config"] == after["config"],
        "records_equal": before["records"] == after["records"],
        "chairs_before": before["chairs"],
        "chairs_after": after["chairs"],
        "history_before": before.get("history"),
        "history_after": after.get("history"),
    }


def _assert_equal(before, after, label):
    if before != after:
        print("PHASE8_TURNOUT_HOST_DIFFERENCE=" + json.dumps({
            "label": label, "difference": _difference(before, after),
        }, sort_keys=True), flush=True)
        raise AssertionError(label + " changed the copied document")


def _without_history(snapshot):
    return {
        key: value for key, value in snapshot.items()
        if key != "history"
    }


def _normalised_reopen(saved, reopened):
    expected = _without_history(saved)
    actual = copy.deepcopy(_without_history(reopened))
    for before, after in zip(expected["objects"], actual["objects"]):
        if before["name"] != after["name"]:
            break
        if before["name"] == "ModelRailwayCurve":
            old_shape = before["shape"]
            new_shape = after["shape"]
            if old_shape is None or new_shape is None:
                continue
            # Existing qualified-host allowance for this derived shape.
            if abs(old_shape["area_mm2"] - new_shape["area_mm2"]) <= 2e-9:
                new_shape["area_mm2"] = old_shape["area_mm2"]
                new_shape["summary"]["area_mm2"] = (
                    old_shape["summary"]["area_mm2"]
                )
        elif before["name"] == "RailwayTurnoutIntegration_TO_001":
            old_shape = before["shape"]
            new_shape = after["shape"]
            if old_shape is None or new_shape is None:
                continue
            # This allowance covers only derived integration-group area.
            if abs(old_shape["area_mm2"] - new_shape["area_mm2"]) <= 2e-9:
                new_shape["area_mm2"] = old_shape["area_mm2"]
    return expected, actual


def _assert_reopen_comparator_contract():
    shape = {
        "area_mm2": 10.0,
        "length_mm": 20.0,
        "summary": {"area_mm2": 10.0},
    }
    saved = {
        "objects": [
            {"name": "ModelRailwayCurve", "shape": copy.deepcopy(shape)},
            {
                "name": "RailwayTurnoutIntegration_TO_001",
                "shape": copy.deepcopy(shape), "properties": ("stable",),
            },
            {"name": "OtherObject", "shape": copy.deepcopy(shape)},
        ],
        "records": ["first", "second"],
    }
    allowed = copy.deepcopy(saved)
    allowed["objects"][0]["shape"]["area_mm2"] += 1e-9
    allowed["objects"][0]["shape"]["summary"]["area_mm2"] += 1e-9
    allowed["objects"][1]["shape"]["area_mm2"] += 1e-9
    assert _normalised_reopen(saved, allowed)[0] == (
        _normalised_reopen(saved, allowed)[1]
    )

    for object_index, field, value in (
        (1, "area_mm2", 3e-9),
        (1, "length_mm", 1e-9),
        (2, "area_mm2", 1e-9),
    ):
        changed = copy.deepcopy(saved)
        changed["objects"][object_index]["shape"][field] += value
        expected, actual = _normalised_reopen(saved, changed)
        assert actual != expected, (object_index, field)
    changed = copy.deepcopy(saved)
    changed["objects"][1]["shape"]["summary"]["area_mm2"] += 1e-9
    assert _normalised_reopen(saved, changed)[0] != (
        _normalised_reopen(saved, changed)[1]
    )
    changed = copy.deepcopy(saved)
    changed["objects"][1]["properties"] = ("changed",)
    changed["records"].reverse()
    assert _normalised_reopen(saved, changed)[0] != (
        _normalised_reopen(saved, changed)[1]
    )


def _assert_reopen_equal(saved, reopened):
    expected, actual = _normalised_reopen(saved, reopened)
    if actual != expected:
        print("PHASE8_TURNOUT_HOST_REOPEN_DIFFERENCE=" + json.dumps(
            _difference(saved, reopened), sort_keys=True,
        ), flush=True)
        raise AssertionError("Turnout host integration changed after reopen")


def _expect_error(action, expected):
    try:
        action()
    except (RuntimeError, ValueError) as error:
        assert expected.lower() in str(error).lower(), str(error)
        return str(error)
    raise AssertionError("Expected command rejection: " + expected)


def _prepared_copy(module, source, target):
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
    before = _snapshot(module, document)
    assert len(before["chairs"]) >= 2, before["chairs"]
    assert len(before["records"]) == 10, len(before["records"])
    return document


def _rejected_create(module, document):
    before = _snapshot(module, document)
    original = module.build_turnout_host_integration
    calls = []

    def fail_build(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError(FAULT_BUILD)

    module.build_turnout_host_integration = fail_build
    try:
        _expect_error(
            lambda: module.create_turnout_host_integration(
                document, IDENTIFIER,
            ), FAULT_BUILD,
        )
    finally:
        module.build_turnout_host_integration = original
    assert len(calls) == 1, len(calls)
    _assert_equal(
        before, _snapshot(module, document),
        "Rejected turnout host-integration Create",
    )
    return before


def _rejected_remove(module, document):
    before = _snapshot(module, document)
    _expect_error(
        lambda: module.remove_turnout_host_integration(
            document, IDENTIFIER,
        ), "no host-template integration to remove",
    )
    _assert_equal(
        before, _snapshot(module, document),
        "Rejected turnout host-integration Remove",
    )


def _undo_disabled(module, document, action):
    document.UndoMode = 0
    before = _snapshot(module, document)
    original_clear = module.clear_chair_analysis_display
    clear_calls = []

    def unexpected_clear(*args, **kwargs):
        clear_calls.append((args, kwargs))
        raise RuntimeError("Undo-disabled operation began chair clearing")

    module.clear_chair_analysis_display = unexpected_clear
    try:
        operation = (
            module.create_turnout_host_integration
            if action == "create" else
            module.remove_turnout_host_integration
        )
        _expect_error(
            lambda: operation(document, IDENTIFIER), "Undo",
        )
    finally:
        module.clear_chair_analysis_display = original_clear
    try:
        assert not clear_calls, clear_calls
        _assert_equal(
            before, _snapshot(module, document),
            "Undo-disabled " + action,
        )
    finally:
        document.UndoMode = 1


def _create_failure(module, document, target_name, failure,
                    after_call=False):
    before = _snapshot(module, document)
    original = getattr(module, target_name)
    calls = []

    def injected(*args, **kwargs):
        if target_name == "tag_generated_object":
            if str(args[1]) != module.TURNOUT_INTEGRATION_GROUP_ROLE:
                return original(*args, **kwargs)
            calls.append(True)
            raise RuntimeError(failure)
        calls.append(True)
        if after_call:
            original(*args, **kwargs)
        raise RuntimeError(failure)

    setattr(module, target_name, injected)
    try:
        _expect_error(
            lambda: module.create_turnout_host_integration(
                document, IDENTIFIER,
            ), failure,
        )
    finally:
        setattr(module, target_name, original)
    assert len(calls) == 1, (target_name, calls)
    _assert_equal(before, _snapshot(module, document),
                  "Failed turnout Create at " + target_name)


def _remove_write_failure(module, document):
    before = _snapshot(module, document)
    original = module._turnout_write_production_records
    calls = []

    def fail_after_write(*args, **kwargs):
        calls.append(True)
        original(*args, **kwargs)
        raise RuntimeError(FAULT_WRITE)

    module._turnout_write_production_records = fail_after_write
    try:
        _expect_error(
            lambda: module.remove_turnout_host_integration(
                document, IDENTIFIER,
            ), FAULT_WRITE,
        )
    finally:
        module._turnout_write_production_records = original
    assert len(calls) == 1, calls
    _assert_equal(before, _snapshot(module, document),
                  "Failed turnout Remove after record write")


def _record_bindings(document, records):
    bindings = {}
    for record in records:
        source_name = str(record["source_name"])
        source = document.getObject(source_name)
        assert source is not None, (record["record_id"], source_name)
        ids = json.loads(str(getattr(source, "ProductionRecordIDsJSON", "[]")))
        assert record["record_id"] in ids, (record["record_id"], ids)
        bindings[record["record_id"]] = source_name
    return bindings


def _visibility(snapshot, names):
    by_name = {item["name"]: item for item in snapshot["objects"]}
    return {name: by_name[name]["visibility"] for name in names}


def _lifecycle(module, document, copied):
    document_name = str(document.Name)
    before = _rejected_create(module, document)
    _rejected_remove(module, document)
    _create_failure(
        module, document, "tag_generated_object", FAULT_TAG,
    )
    _create_failure(
        module, document, "_turnout_write_production_records",
        FAULT_WRITE, after_call=True,
    )
    original_ids = [item["record_id"] for item in before["records"]]
    original_bindings = _record_bindings(document, before["records"])

    result = module.create_turnout_host_integration(document, IDENTIFIER)
    integration = module.turnout_integration_by_id(document, IDENTIFIER)
    assert integration is not None and result == integration
    assert len(integration["integration_object_names"]) == 5
    assert all(
        document.getObject(name) is not None
        for name in integration["integration_object_names"]
    )
    created = _snapshot(module, document)
    assert not created["chairs"]
    assert created["history"]["undo"] == before["history"]["undo"] + 1
    assert created["history"]["redo"] == 0
    assert len(created["records"]) == 8
    created_ids = [item["record_id"] for item in created["records"]]
    removed_ids = set(original_ids) - set(created_ids)
    added_ids = set(created_ids) - set(original_ids)
    replaced_ids = set(integration["removed_record_ids"])
    integrated_ids = set(integration["integrated_record_ids"])
    assert len(replaced_ids) == 4, replaced_ids
    assert len(integrated_ids) == 2, integrated_ids
    assert replaced_ids <= set(original_ids)
    assert integrated_ids <= set(created_ids)
    assert removed_ids == replaced_ids - integrated_ids
    assert added_ids == integrated_ids - replaced_ids
    originals = {item["record_id"]: item for item in before["records"]}
    integrated = {item["record_id"]: item for item in created["records"]}
    assert {
        item["record_id"]: item
        for item in integration["original_record_metadata"]
    } == {identifier: originals[identifier] for identifier in replaced_ids}
    for identifier in integrated_ids & set(original_ids):
        assert integrated[identifier]["source_name"] != (
            originals[identifier]["source_name"]
        )
    created_bindings = _record_bindings(document, created["records"])
    assert {
        created_bindings[identifier] for identifier in integrated_ids
    } <= set(integration["integration_object_names"])
    source_names = set(integration["source_visibility"])
    source_names.update(integration["turnout_visibility"])
    if any(value is not None for value in _visibility(before, source_names).values()):
        assert all(
            value is False
            for value in _visibility(created, source_names).values()
        )

    document.undo()
    document.recompute()
    _assert_equal(_without_history(before),
                  _without_history(_snapshot(module, document)),
                  "Turnout Create Undo")
    document.redo()
    document.recompute()
    _assert_equal(_without_history(created),
                  _without_history(_snapshot(module, document)),
                  "Turnout Create Redo")

    document.save()
    saved = _snapshot(module, document)
    App.closeDocument(document_name)
    document = App.openDocument(str(copied))
    document_name = str(document.Name)
    try:
        reopened = _snapshot(module, document)
        _assert_reopen_equal(saved, reopened)
        assert module.turnout_integration_by_id(
            document, IDENTIFIER,
        ) is not None
        _record_bindings(document, reopened["records"])

        _undo_disabled(module, document, "remove")
        _remove_write_failure(module, document)
        before_remove = _snapshot(module, document)
        removed = module.remove_turnout_host_integration(
            document, IDENTIFIER,
        )
        assert removed == IDENTIFIER
        assert module.turnout_integration_by_id(
            document, IDENTIFIER,
        ) is None
        after_remove = _snapshot(module, document)
        assert len(after_remove["records"]) == 10
        assert {
            item["record_id"] for item in after_remove["records"]
        } == set(original_ids)
        assert _record_bindings(document, after_remove["records"]) == (
            original_bindings
        )
        assert all(
            document.getObject(name) is None
            for name in integration["integration_object_names"]
        )
        if any(
            value is not None
            for value in _visibility(before, source_names).values()
        ):
            assert _visibility(after_remove, source_names) == (
                _visibility(before, source_names)
            )
        assert after_remove["history"]["undo"] == (
            before_remove["history"]["undo"] + 1
        )
        assert after_remove["history"]["redo"] == 0

        document.undo()
        document.recompute()
        _assert_equal(_without_history(before_remove),
                      _without_history(_snapshot(module, document)),
                      "Turnout Remove Undo")
        document.redo()
        document.recompute()
        _assert_equal(_without_history(after_remove),
                      _without_history(_snapshot(module, document)),
                      "Turnout Remove Redo")
        document.save()
        saved_removed = _snapshot(module, document)
        App.closeDocument(document_name)
        document = App.openDocument(str(copied))
        document_name = str(document.Name)
        reopened_removed = _snapshot(module, document)
        _assert_reopen_equal(saved_removed, reopened_removed)
        assert module.turnout_integration_by_id(
            document, IDENTIFIER,
        ) is None
        assert _record_bindings(
            document, reopened_removed["records"],
        ) == original_bindings
        assert module.analyse_entity_chair_positions(
            document, "turnout", IDENTIFIER,
        )
        assert _snapshot(module, document)["chairs"]
        _undo_disabled(module, document, "create")
        return {
            "source_records": len(original_ids),
            "integrated_records": len(created_ids),
            "replaced_record_ids": sorted(replaced_ids),
            "integrated_record_ids": sorted(integrated_ids),
            "integration_objects": len(integration["integration_object_names"]),
            "create_undo_delta": 1,
            "remove_undo_delta": 1,
            "create_and_remove_saved_reopened": True,
        }
    finally:
        if document_name in App.listDocuments():
            App.closeDocument(document_name)


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    source = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_TURNOUT_HOST_FIXTURE",
        ROOT / "benchmark-output/freecad-bridge/fixtures/"
        "b14-default-base-regenerated.FCStd",
    )).resolve()
    assert source.is_file(), source
    assert _sha256(source) == FIXTURE_SHA256
    print("PHASE8_TURNOUT_HOST_SOURCE=" + str(ROOT), flush=True)
    print("PHASE8_TURNOUT_HOST_FIXTURE=" + str(source), flush=True)
    print("PHASE8_TURNOUT_HOST_FIXTURE_SHA256=" + FIXTURE_SHA256,
          flush=True)
    print("PHASE8_TURNOUT_HOST_REQUIRED_SENTINEL=" + SENTINEL,
          flush=True)
    _assert_reopen_comparator_contract()
    module = _load_product()
    try:
        with tempfile.TemporaryDirectory(
            prefix="tracktemplate-phase8-turnout-host-integration-"
        ) as temporary:
            copied = pathlib.Path(temporary) / "turnout-host.FCStd"
            document = _prepared_copy(module, source, copied)
            document_name = str(document.Name)
            try:
                result = _lifecycle(module, document, copied)
            finally:
                if document_name in App.listDocuments():
                    App.closeDocument(document_name)
        print("PHASE8_TURNOUT_HOST_SUMMARY=" + json.dumps(
            result, sort_keys=True,
        ), flush=True)
        print(SENTINEL, flush=True)
    finally:
        assert _sha256(source) == FIXTURE_SHA256
        assert not App.listDocuments()


if __name__ in {
    "__main__", "freecad_validate_phase8_turnout_host_integration_recovery",
}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
