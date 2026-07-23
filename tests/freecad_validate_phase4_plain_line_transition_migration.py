#!/usr/bin/env python3
"""Exercise the authorised copied-target transition migration fixture."""

from dataclasses import replace
import hashlib
import json
import pathlib
import pprint
import shutil
import sys
import tempfile
import traceback

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.application.transition_state import TransitionState  # noqa: E402
from tracktemplate.compatibility import legacy_document  # noqa: E402
from tracktemplate.compatibility import plain_line_transition_migration  # noqa: E402


CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
B14_FIXTURE_PATH = (
    ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "fixtures"
    / "b14-default-base-regenerated.FCStd"
)
B14_FIXTURE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)
GENERATOR_ID = "ModelRailwayCurveTemplate.IndependentEasements"
B14 = "10.2A8A7B14"
B15 = "10.2A8A7B15"
CAPTURE_PROPERTIES = (
    "GeneratedBy",
    "GeneratedRole",
    "TemplateSetID",
    "GeneratorVersion",
    "TransitionLength",
    "CurveRadius",
    "TotalTurnAngle",
    "ParallelTrackCount",
    "TrackConfigurationJSON",
    "OperatorData",
    adapter.FREECAD_RECORD_TYPE_PROPERTY,
    adapter.FREECAD_STATE_JSON_PROPERTY,
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _track_payload():
    return json.dumps(
        [
            {
                "alignment_mode": "Euler - match spacings",
                "create_template": True,
                "curve_spacing": 55.0,
                "entry_transition_length": 559.4102547270278,
                "exit_transition_length": 559.4102547270278,
                "finish_spacing": 50.0,
                "name": "Track 2",
                "show_centreline": True,
                "side": "Outside",
                "start_spacing": 50.0,
                "width": 32.0,
            }
        ],
        sort_keys=True,
    )


def _add_property(obj, property_type, name, value):
    obj.addProperty(property_type, name, "Copied-target fixture")
    setattr(obj, name, value)


def _add_identity(obj, version, role, set_id="SET-001"):
    _add_property(obj, "App::PropertyString", "GeneratedBy", GENERATOR_ID)
    _add_property(obj, "App::PropertyString", "GeneratedRole", role)
    _add_property(obj, "App::PropertyString", "TemplateSetID", set_id)
    _add_property(obj, "App::PropertyString", "GeneratorVersion", version)


def _write_synthetic_source(path, settings_version, mixed=False):
    document = App.newDocument("Phase4MigrationBuild" + settings_version[-3:])
    document.UndoMode = 1
    settings = document.addObject("App::FeaturePython", "RailwayCurveSettings")
    _add_identity(settings, settings_version + " fixture", "Settings")
    _add_property(settings, "App::PropertyLength", "TransitionLength", 600.0)
    _add_property(settings, "App::PropertyLength", "CurveRadius", 600.0)
    _add_property(settings, "App::PropertyAngle", "TotalTurnAngle", 90.0)
    _add_property(settings, "App::PropertyInteger", "ParallelTrackCount", 1)
    _add_property(
        settings,
        "App::PropertyString",
        "TrackConfigurationJSON",
        _track_payload(),
    )
    if mixed:
        chair = document.addObject("App::FeaturePython", "B15ChairDisplay")
        _add_identity(chair, B15 + " fixture", "ChairAnalysisDisplay")
    foreign = document.addObject("App::FeaturePython", "OperatorObject")
    _add_property(foreign, "App::PropertyString", "OperatorData", "untouched")
    document.saveAs(str(path))
    App.closeDocument(document.Name)


def _property_value(obj, property_name):
    value = getattr(obj, property_name)
    if hasattr(value, "Value"):
        return float(value.Value)
    return str(value) if isinstance(value, str) else value


def _shape_signature(obj, persistent=False):
    if "Shape" not in obj.PropertiesList:
        return None
    shape = obj.Shape
    if shape.isNull():
        return ("null",)
    stable = (
        str(shape.ShapeType),
        len(shape.Vertexes),
        len(shape.Edges),
        len(shape.Faces),
        round(float(shape.BoundBox.XMin), 12),
        round(float(shape.BoundBox.YMin), 12),
        round(float(shape.BoundBox.XMax), 12),
        round(float(shape.BoundBox.YMax), 12),
    )
    if persistent:
        return stable
    return stable[:1] + (int(shape.hashCode()),) + stable[1:]


def _is_canonical(obj):
    return (
        adapter.FREECAD_RECORD_TYPE_PROPERTY in obj.PropertiesList
        and str(getattr(obj, adapter.FREECAD_RECORD_TYPE_PROPERTY))
        == adapter.FREECAD_TRANSITION_RECORD_TYPE
    )


def _object_snapshot(document, include_canonical=True, persistent=False):
    records = []
    for obj in sorted(document.Objects, key=lambda item: str(item.Name)):
        if not include_canonical and _is_canonical(obj):
            continue
        properties = tuple(obj.PropertiesList)
        values = tuple(
            (
                name,
                str(obj.getTypeIdOfProperty(name)),
                _property_value(obj, name),
            )
            for name in CAPTURE_PROPERTIES
            if name in properties
        )
        records.append(
            (
                str(obj.Name),
                str(obj.Label),
                str(obj.TypeId),
                properties,
                values,
                tuple(sorted(str(item.Name) for item in obj.InList)),
                tuple(
                    str(item.Name)
                    for item in getattr(obj, "Group", ())
                ),
                _shape_signature(obj, persistent=persistent),
            )
        )
    return tuple(records)


def _history(document):
    return int(document.UndoCount), int(document.RedoCount)


def _assert_snapshot_equal(actual, expected, label):
    if actual == expected:
        return
    actual_by_name = {item[0]: item for item in actual}
    expected_by_name = {item[0]: item for item in expected}
    names = sorted(set(actual_by_name) | set(expected_by_name))
    differences = [
        (
            name,
            expected_by_name.get(name),
            actual_by_name.get(name),
        )
        for name in names
        if actual_by_name.get(name) != expected_by_name.get(name)
    ]
    pprint.pprint((label, differences))
    raise AssertionError(label)


def _canonical_states(document):
    records = []
    for obj in sorted(document.Objects, key=lambda item: str(item.Name)):
        if _is_canonical(obj):
            records.append((str(obj.Name), adapter.read_transition_object(obj)))
    return tuple(records)


def _expect_store_error(action, code):
    try:
        action()
    except adapter.TransitionDocumentError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionDocumentError {!r}".format(code))


def _open_pair(source_path, target_path):
    source = App.openDocument(str(source_path))
    target = App.openDocument(str(target_path))
    assert source is not target
    target.UndoMode = 1
    return source, target


def _exercise_success(
    store,
    contract,
    source_path,
    target_path,
    expected_versions,
):
    source_file_before = _sha256(source_path)
    target_file_before = _sha256(target_path)
    assert source_file_before == target_file_before
    source, target = _open_pair(source_path, target_path)
    try:
        source_before = (_history(source), _object_snapshot(source))
        target_history_before = _history(target)
        target_legacy_before = _object_snapshot(target, include_canonical=False)
        target_legacy_persisted_before = _object_snapshot(
            target,
            include_canonical=False,
            persistent=True,
        )
        plan = (
            plain_line_transition_migration.prepare_copied_plain_line_transition_migration(
                source,
                target,
                contract,
            )
        )
        assert (_history(source), _object_snapshot(source)) == source_before
        assert _history(target) == target_history_before
        assert _object_snapshot(target, include_canonical=False) == target_legacy_before
        assert plan.source_versions == expected_versions
        assert plan.transition_ids == (
            "SET-001/curve-track/2/transition/entry",
            "SET-001/curve-track/2/transition/exit",
        )
        assert plan.migration_support_advertised is False
        assert plan.production_output_authorized is False
        assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()

        created = store.create_many(target, plan.states)
        created_names = tuple(str(obj.Name) for obj in created)
        assert len(created_names) == 2 and len(set(created_names)) == 2
        assert _history(target) == (target_history_before[0] + 1, 0)
        assert _object_snapshot(target, include_canonical=False) == target_legacy_before
        assert (_history(source), _object_snapshot(source)) == source_before
        assert tuple(
            state.intent.transition_id for _name, state in _canonical_states(target)
        ) == plan.transition_ids
        assert all("Shape" not in obj.PropertiesList for obj in created)

        target.undo()
        assert _history(target) == (target_history_before[0], 1)
        assert _canonical_states(target) == ()
        assert _object_snapshot(target, include_canonical=False) == target_legacy_before
        target.redo()
        assert _history(target) == (target_history_before[0] + 1, 0)
        assert tuple(name for name, _state in _canonical_states(target)) == created_names
        assert tuple(
            state.intent.transition_id for _name, state in _canonical_states(target)
        ) == plan.transition_ids

        before_duplicate = (_history(target), _object_snapshot(target))
        _expect_store_error(
            lambda: store.create_many(target, plan.states),
            "duplicate-stable-identity",
        )
        assert (_history(target), _object_snapshot(target)) == before_duplicate

        canonical_before_reopen = _canonical_states(target)
        target.save()
        App.closeDocument(target.Name)
        target = None
        reopened = App.openDocument(str(target_path))
        try:
            _assert_snapshot_equal(
                _object_snapshot(
                    reopened,
                    include_canonical=False,
                    persistent=True,
                ),
                target_legacy_persisted_before,
                "legacy snapshot drift after target save/reopen",
            )
            assert _canonical_states(reopened) == canonical_before_reopen
        finally:
            App.closeDocument(reopened.Name)
        assert _sha256(target_path) != target_file_before
        assert _sha256(source_path) == source_file_before
        assert (_history(source), _object_snapshot(source)) == source_before
    finally:
        if target is not None and App.getDocument(str(target.Name)) is target:
            App.closeDocument(target.Name)
        if App.getDocument(str(source.Name)) is source:
            App.closeDocument(source.Name)
    assert _sha256(source_path) == source_file_before


def _exercise_atomic_failure(store, contract, source_path, target_path):
    source_hash = _sha256(source_path)
    target_hash = _sha256(target_path)
    source, target = _open_pair(source_path, target_path)
    try:
        source_before = (_history(source), _object_snapshot(source))
        target_before = (_history(target), _object_snapshot(target))
        plan = (
            plain_line_transition_migration.prepare_copied_plain_line_transition_migration(
                source,
                target,
                contract,
            )
        )
        _expect_store_error(
            lambda: store.create_many(target, ()),
            "empty-create-batch",
        )
        _expect_store_error(
            lambda: store.create_many(target, (plan.states[0], plan.states[0])),
            "duplicate-batch-stable-identity",
        )
        stale_state = TransitionState(
            replace(
                plan.states[1].intent,
                radius_mm=plan.states[1].intent.radius_mm + 1.0,
            ),
            plan.states[1].analysis,
        )
        _expect_store_error(
            lambda: store.create_many(target, (plan.states[0], stale_state)),
            "invalid-write-state",
        )
        try:
            store.create_many(target, (plan.states[0], object()))
        except TypeError as error:
            assert str(error) == "every batch item must be a TransitionState"
        else:
            raise AssertionError("Expected a batch item TypeError")
        assert (_history(target), _object_snapshot(target)) == target_before

        original_writer = adapter._write_transition_payload
        writes = {"count": 0}

        def fail_on_second_payload(obj, payload):
            original_writer(obj, payload)
            writes["count"] += 1
            if writes["count"] == 2:
                raise RuntimeError("injected failure after second batch payload")

        adapter._write_transition_payload = fail_on_second_payload
        try:
            error = _expect_store_error(
                lambda: store.create_many(target, plan.states),
                "transaction-failed",
            )
            assert error.document_mutation is False
        finally:
            adapter._write_transition_payload = original_writer
        assert writes["count"] == 2
        assert (_history(target), _object_snapshot(target)) == target_before
        assert _canonical_states(target) == ()
        assert (_history(source), _object_snapshot(source)) == source_before
        assert _sha256(source_path) == source_hash
        assert _sha256(target_path) == target_hash
    finally:
        App.closeDocument(target.Name)
        App.closeDocument(source.Name)
    assert _sha256(source_path) == source_hash
    assert _sha256(target_path) == target_hash


def _close_all_documents():
    for name in list(App.listDocuments()):
        App.closeDocument(name)


def _validate():
    if not B14_FIXTURE_PATH.is_file():
        raise AssertionError(
            "Reproduce the ignored B14 fixture with tools/freecad_bridge/build-b14-base"
        )
    assert _sha256(B14_FIXTURE_PATH) == B14_FIXTURE_SHA256
    contract = _contract()
    qualification = bootstrap.require_qualified_runtime(CONTRACT_PATH)
    store = adapter.FreeCADTransitionStore(qualification)

    try:
        with tempfile.TemporaryDirectory(
            prefix="tracktemplate-phase4-copied-target-"
        ) as temporary_directory:
            directory = pathlib.Path(temporary_directory)
            source_paths = {}

            b14_source = directory / "b14-source.FCStd"
            shutil.copy2(B14_FIXTURE_PATH, b14_source)
            source_paths["b14"] = (b14_source, (B14,))

            b15_source = directory / "b15-source.FCStd"
            _write_synthetic_source(b15_source, B15)
            source_paths["b15"] = (b15_source, (B15,))

            mixed_source = directory / "mixed-source.FCStd"
            _write_synthetic_source(mixed_source, B14, mixed=True)
            source_paths["mixed"] = (mixed_source, (B14, B15))

            for name in ("b14", "b15", "mixed"):
                source_path, versions = source_paths[name]
                target_path = directory / (name + "-target.FCStd")
                shutil.copy2(source_path, target_path)
                _exercise_success(
                    store,
                    contract,
                    source_path,
                    target_path,
                    versions,
                )

            failure_target = directory / "b14-failure-target.FCStd"
            shutil.copy2(b14_source, failure_target)
            _exercise_atomic_failure(store, contract, b14_source, failure_target)
    finally:
        _close_all_documents()

    assert _sha256(B14_FIXTURE_PATH) == B14_FIXTURE_SHA256
    assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()
    assert plain_line_transition_migration.MIGRATION_SUPPORT_ADVERTISED is False
    assert plain_line_transition_migration.PRODUCTION_OUTPUT_AUTHORIZED is False


try:
    _validate()
except Exception:
    traceback.print_exc()
    raise

print("Phase 4 copied-target transition migration fixture passed")
