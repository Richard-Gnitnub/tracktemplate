"""Prove B16 B4 first-tag failure recovery on the fixed XO-001 copy."""

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
SOURCE_ROOT = pathlib.Path(
    os.environ.get("TRACKTEMPLATE_B4_SOURCE_ROOT", ROOT)
).resolve()
sys.path.insert(0, str(SOURCE_ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402
from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility.crossover_b4_recovery import (  # noqa: E402
    CrossoverB4RecoveryAdapter,
)
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 crossover B4 recovery FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = SOURCE_ROOT / "reference/contracts/phase1-crossover-timbering.json"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_product():
    assert pathlib.Path(api.__file__).resolve() == SOURCE_ROOT / "tracktemplate/api.py"
    launcher = runpy.run_path(str(SOURCE_ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](SOURCE_ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        SOURCE_ROOT, api, contract,
    )
    module = session.module
    apply = module.apply_crossover_b4_timbering
    assert isinstance(apply.__self__, CrossoverB4RecoveryAdapter)
    assert apply.__func__ is CrossoverB4RecoveryAdapter.apply
    assert apply.__self__.module is module
    panel = module.CrossoverManagerPanel.__dict__["apply_b4_timbering"]
    if getattr(panel, "_whole_workflow_benchmark_wrapper", False):
        panel = panel._whole_workflow_original
    assert panel.__globals__ is module.__dict__
    assert "apply_crossover_b4_timbering" in panel.__code__.co_names
    return module


def _history(document):
    return {
        "mode": int(document.UndoMode),
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": tuple(str(value) for value in document.UndoNames),
        "redo_names": tuple(str(value) for value in document.RedoNames),
    }


def _shape_state(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        return None
    brep = shape.exportBrepToString()
    return {
        "brep_sha256": hashlib.sha256(brep.encode("utf-8")).hexdigest(),
        "summary": recipe.shape_summary(shape),
    }


def _snapshot(module, document, crossover_id):
    records = []
    for obj in document.Objects:
        properties = tuple(sorted(
            (name, str(getattr(obj, name)))
            for name in obj.PropertiesList
            if name not in {"Shape", "Group", "_Part_ShapeCache"}
        ))
        members = tuple(sorted(
            member.Name for member in getattr(obj, "Group", ()) or ()
        )) if "Group" in obj.PropertiesList else None
        view = getattr(obj, "ViewObject", None)
        visibility = (
            bool(view.Visibility)
            if view is not None and hasattr(view, "Visibility") else None
        )
        records.append({
            "name": str(obj.Name),
            "type_id": str(obj.TypeId),
            "properties": properties,
            "group_members": members,
            "visibility": visibility,
            "shape": _shape_state(obj),
        })
    return {
        "objects": records,
        "config": recipe.stable(
            module.crossover_config_by_id(document, crossover_id)
        ),
        "history": _history(document),
        "file_name": str(document.FileName),
    }


def _document_state(snapshot):
    return {key: value for key, value in snapshot.items() if key != "history"}


def _persistent_state(snapshot):
    state = _document_state(snapshot)
    state["objects"] = [
        {
            **item,
            "shape": item["shape"]["summary"] if item["shape"] else None,
        }
        for item in snapshot["objects"]
    ]
    return state


def _assert_core_result(module, result, contract):
    expected = contract["legacy_semantics"]
    actual = recipe.result_snapshot(module, result)
    for key in (
        "status", "counts", "record_turnout_sides",
        "record_envelope_kinds", "record_identity_sha256",
        "stable_record_sha256",
    ):
        assert actual[key] == expected[key], (key, actual[key], expected[key])
    assert actual["resolution_signature"] == (
        expected["default_resolution_signature"]
    )
    return actual


def _assert_resolved_analysis(module, result, document, crossover_id,
                              expected=None):
    """Prove the effective analysis in the return and stored B4 payloads."""
    returned = result.get("resolved_analysis")
    assert isinstance(returned, dict) and returned, returned
    # The document stores JSON, which restores nested tuples as lists.
    analysis = json.loads(json.dumps(returned, sort_keys=True))
    assert analysis.get("geometry_signature"), analysis
    assert analysis.get("analysis_basis") == (
        "Effective automatically resolved timber arrangement"
    ), analysis.get("analysis_basis")
    if expected is not None:
        assert analysis == expected, "Returned B4 resolved analysis changed"

    config = module.crossover_config_by_id(document, crossover_id)
    assert config is not None
    stored_result = config.get("b4_result")
    assert isinstance(stored_result, dict)
    stored_analysis = stored_result.get("resolved_analysis")
    if stored_analysis != analysis:
        differences = sorted(
            key for key in set(analysis) | set(stored_analysis or {})
            if analysis.get(key) != (stored_analysis or {}).get(key)
        )
        raise AssertionError(
            "Crossover config changed effective B4 analysis fields: {!r}"
            .format(differences)
        )
    settings = [
        obj for obj in module._crossover_objects(document, crossover_id)
        if module.object_string_property(obj, "GeneratedRole", "")
        == module.CROSSOVER_SETTINGS_ROLE
    ]
    assert len(settings) == 1, settings
    persisted = json.loads(str(getattr(
        settings[0], module.CROSSOVER_B4_RESULT_PROPERTY,
    )))
    assert persisted.get("resolved_analysis") == analysis, (
        "CrossoverB4ResultJSON lost the effective B4 analysis"
    )
    return analysis


def _snapshot_difference(before, after):
    before_objects = {item["name"]: item for item in before["objects"]}
    after_objects = {item["name"]: item for item in after["objects"]}
    before_names = set(before_objects)
    after_names = set(after_objects)
    changed = {
        name: {
            key: (
                sorted(
                    property_name
                    for property_name in (
                        set(dict(before_objects[name]["properties"]))
                        | set(dict(after_objects[name]["properties"]))
                    )
                    if dict(before_objects[name]["properties"]).get(property_name)
                    != dict(after_objects[name]["properties"]).get(property_name)
                ) if key == "properties" else "changed"
            )
            for key in before_objects[name]
            if before_objects[name][key] != after_objects[name][key]
        }
        for name in before_names & after_names
        if before_objects[name] != after_objects[name]
    }
    return {
        "added": sorted(after_names - before_names),
        "removed": sorted(before_names - after_names),
        "changed": changed,
        "config_equal": before["config"] == after["config"],
        "file_name_equal": before["file_name"] == after["file_name"],
        "history_before": before["history"],
        "history_after": after["history"],
    }


def _expect_first_tag_recovery(module, document, crossover_id, contract):
    before = _snapshot(module, document, crossover_id)
    fault = contract["legacy_defects"]["incomplete_abort_cleanup"]
    original = module.tag_generated_object
    calls = []

    def fail_first_b4_tag(obj, role, set_id):
        if str(role) == str(module.CROSSOVER_B4_ROLE):
            calls.append(str(obj.Name))
            raise RuntimeError(fault["fault_text"])
        return original(obj, role, set_id)

    module.tag_generated_object = fail_first_b4_tag
    try:
        try:
            module.apply_crossover_b4_timbering(document, crossover_id)
        except RuntimeError as error:
            assert str(error) == fault["fault_text"], str(error)
        else:
            raise AssertionError("The injected first B4 tag failure was accepted")
    finally:
        module.tag_generated_object = original
    assert len(calls) == 1, calls
    after = _snapshot(module, document, crossover_id)
    if after != before:
        raise AssertionError(
            "B4 first-tag failure changed the copied document: {!r}".format(
                _snapshot_difference(before, after),
            )
        )
    return before


def _prove_success_lifecycle(module, document, crossover_id, contract):
    expected = contract["legacy_semantics"]
    counts = expected["lifecycle_object_counts"]
    document.UndoMode = 1
    before = _snapshot(module, document, crossover_id)
    assert len(document.Objects) == counts["after_crossover_geometry"]
    first = module.apply_crossover_b4_timbering(document, crossover_id)
    assert first.get("cache_reused") is False
    core = _assert_core_result(module, first, contract)
    resolved_analysis = _assert_resolved_analysis(
        module, first, document, crossover_id,
    )
    b4_object = module._crossover_b4_object(document, crossover_id)
    assert b4_object is not None
    assert recipe.shape_summary(b4_object.Shape) == expected["display_shape"]
    assert len(document.Objects) == counts["after_first_apply"]
    after = _snapshot(module, document, crossover_id)
    assert after["history"]["undo"] == before["history"]["undo"] + 1
    assert after["history"]["redo"] == 0
    stored = module.crossover_config_by_id(document, crossover_id)["b4_result"]
    _assert_core_result(module, stored, contract)

    reused = module.apply_crossover_b4_timbering(document, crossover_id)
    assert reused.get("cache_reused") is True
    _assert_core_result(module, reused, contract)
    _assert_resolved_analysis(
        module, reused, document, crossover_id, resolved_analysis,
    )
    assert len(document.Objects) == counts["after_unchanged_reuse"]
    assert _snapshot(module, document, crossover_id) == after

    document.undo()
    document.recompute()
    assert len(document.Objects) == counts["after_undo"]
    assert module._crossover_b4_object(document, crossover_id) is None
    assert _document_state(_snapshot(module, document, crossover_id)) == (
        _document_state(before)
    )
    assert module.crossover_config_by_id(
        document, crossover_id,
    ).get("b4_result") == before["config"].get("b4_result")
    document.redo()
    document.recompute()
    assert len(document.Objects) == counts["after_redo"]
    assert _document_state(_snapshot(module, document, crossover_id)) == (
        _document_state(after)
    )
    _assert_resolved_analysis(
        module, module.crossover_config_by_id(document, crossover_id)[
            "b4_result"
        ], document, crossover_id, resolved_analysis,
    )

    document.save()
    saved = _snapshot(module, document, crossover_id)
    copy_path = pathlib.Path(document.FileName)
    App.closeDocument(document.Name)
    reopened_document = App.openDocument(str(copy_path))
    assert len(reopened_document.Objects) == counts["after_reopen"]
    reopened_state = _snapshot(module, reopened_document, crossover_id)
    if _persistent_state(reopened_state) != _persistent_state(saved):
        raise AssertionError(
            "B4 save/reopen state changed: {!r}".format(
                _snapshot_difference(saved, reopened_state),
            )
        )
    _assert_resolved_analysis(
        module, module.crossover_config_by_id(reopened_document, crossover_id)[
            "b4_result"
        ], reopened_document, crossover_id, resolved_analysis,
    )
    reopened = module.apply_crossover_b4_timbering(
        reopened_document, crossover_id,
    )
    assert reopened.get("cache_reused") is True
    _assert_core_result(module, reopened, contract)
    _assert_resolved_analysis(
        module, reopened, reopened_document, crossover_id, resolved_analysis,
    )
    assert _persistent_state(_snapshot(
        module, reopened_document, crossover_id,
    )) == _persistent_state(saved)
    core["resolved_analysis_signature"] = resolved_analysis[
        "geometry_signature"
    ]
    core["resolved_analysis_sha256"] = recipe.digest(resolved_analysis)
    return reopened_document, core


def validate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        assert _sha256(SOURCE_ROOT / source["path"]) == source["sha256"]
    fixture = contract["fixture"]
    fixture_path = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_B4_FIXTURE", SOURCE_ROOT / fixture["path"]
    )).resolve()
    assert fixture_path.is_file(), fixture_path
    fixture_hash = _sha256(fixture_path)
    assert fixture_hash == fixture["sha256"]
    module = _load_product()

    witness = None
    with tempfile.TemporaryDirectory(prefix="tracktemplate-phase8-b4-") as temp:
        copy = pathlib.Path(temp) / "phase8-b4-xo001.FCStd"
        shutil.copy2(fixture_path, copy)
        document = App.openDocument(str(copy))
        try:
            document.UndoMode = 1
            base = b14_recipe.freecad_base_snapshot(
                module, document, expected_macro_version="10.2A8A7B15"
            )
            legacy_semantic = dict(base["semantic"])
            legacy_semantic["macro_version"] = "10.2A8A7B14"
            assert recipe.digest(legacy_semantic) == fixture["semantic_sha256"]
            scenario = contract["scenario"]
            config, selected = recipe.create_controlled_crossover(
                module, document, scenario["host_a_chainage_mm"]
            )
            identifier = str(config["crossover_id"])
            assert identifier == scenario["crossover_id"]
            for side in ("a", "b"):
                expected = scenario["host_{}_identity".format(side)]
                actual = selected["host_{}_identity".format(side)]
                assert all(actual[key] == value for key, value in expected.items())
            assert len(document.Objects) == 18
            assert _history(document)["mode"] == 1
            _expect_first_tag_recovery(module, document, identifier, contract)
            document.UndoMode = 0
            assert _history(document)["mode"] == 0
            _expect_first_tag_recovery(module, document, identifier, contract)
            document, witness = _prove_success_lifecycle(
                module, document, identifier, contract,
            )
        finally:
            for opened in list(App.listDocuments().values()):
                if pathlib.Path(opened.FileName) == copy:
                    App.closeDocument(opened.Name)
    assert _sha256(fixture_path) == fixture_hash
    print("PHASE8_B4_RECOVERY_WITNESS=" + json.dumps(
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


if __name__ in {"__main__", "freecad_validate_phase8_crossover_b4_recovery"}:
    _run_as_script()
