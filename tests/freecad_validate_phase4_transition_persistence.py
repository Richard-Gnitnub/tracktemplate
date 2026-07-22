#!/usr/bin/env python3
"""Validate transition persistence in disposable qualified FreeCAD documents."""

import copy
from dataclasses import replace
import json
import math
import pathlib
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402


DOCUMENT_PREFIX = "TrackTemplatePhase4Persistence"


def _intent(transition_id="transition:phase4:persistence"):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    return api.TransitionIntent(
        transition_id=transition_id,
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            300.0,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 4 persisted transition",
        end_name="Entry",
    )


def _analysed(transition_id="transition:phase4:persistence"):
    return api.analyse_transition_state(api.TransitionState(_intent(transition_id)))


def _new_document(suffix):
    document = App.newDocument(DOCUMENT_PREFIX + suffix)
    document.UndoMode = 1
    assert int(document.UndoCount) == 0
    assert int(document.RedoCount) == 0
    return document


def _expect_adapter_error(action, code, source_code=None):
    try:
        action()
    except adapter.TransitionDocumentError as error:
        assert error.code == code, error
        if source_code is not None:
            assert error.source_code == source_code, error.diagnostic()
        diagnostic = error.diagnostic()
        assert set(diagnostic) == {
            "code",
            "message",
            "object_name",
            "source_code",
            "recoverable",
            "document_mutation",
        }
        return error
    raise AssertionError("Expected TransitionDocumentError {!r}".format(code))


def _custom_payload(obj):
    return str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY))


def _add_indexed_object(document, name, record_type, payload=None):
    obj = document.addObject("App::FeaturePython", name)
    obj.addProperty(
        "App::PropertyString",
        adapter.FREECAD_RECORD_TYPE_PROPERTY,
        adapter.FREECAD_PROPERTY_GROUP,
    )
    setattr(obj, adapter.FREECAD_RECORD_TYPE_PROPERTY, record_type)
    if payload is not None:
        obj.addProperty(
            "App::PropertyString",
            adapter.FREECAD_STATE_JSON_PROPERTY,
            adapter.FREECAD_PROPERTY_GROUP,
        )
        setattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY, payload)
    return obj


def _validate_lifecycle(store, directory):
    document = _new_document("Lifecycle")
    foreign = document.addObject("App::FeaturePython", "OperatorOwnedObject")
    foreign.addProperty("App::PropertyString", "OperatorData")
    foreign.OperatorData = "untouched"
    other_record = _add_indexed_object(
        document,
        "OtherTrackTemplateRecord",
        "tracktemplate.other-state",
        "not transition JSON",
    )
    foreign_name = str(foreign.Name)
    other_record_name = str(other_record.Name)
    assert int(document.UndoCount) == 0

    initial = _analysed()
    created = store.create(document, initial)
    created_name = str(created.Name)
    assert len(document.Objects) == 3
    assert str(created.TypeId) == adapter.FREECAD_TRANSITION_OBJECT_TYPE
    assert "Shape" not in created.PropertiesList
    assert set(adapter.FREECAD_CUSTOM_PROPERTIES) <= set(created.PropertiesList)
    assert all(
        "ReadOnly" in created.getEditorMode(property_name)
        for property_name in adapter.FREECAD_CUSTOM_PROPERTIES
    )
    assert str(created.TrackTemplateRecordType) == (
        adapter.FREECAD_TRANSITION_RECORD_TYPE
    )
    assert adapter.read_transition_object(created) == initial
    assert adapter.find_transition_object(document, initial.intent.transition_id) is created
    assert int(document.UndoCount) == 1 and int(document.RedoCount) == 0

    created.Label = "Operator label independent of canonical identity"
    before_noop = (int(document.UndoCount), int(document.RedoCount), _custom_payload(created))
    assert store.update(document, created, initial) is created
    assert (int(document.UndoCount), int(document.RedoCount), _custom_payload(created)) == before_noop

    changed_intent = replace(
        initial.intent,
        target_signed_offset_mm=initial.intent.target_signed_offset_mm + 0.1,
    )
    updated = api.analyse_transition_state(
        api.replace_transition_intent(initial, changed_intent)
    )
    store.update(document, created, updated)
    assert adapter.read_transition_object(created) == updated
    assert int(document.UndoCount) == 2 and int(document.RedoCount) == 0

    document.undo()
    assert adapter.read_transition_object(created) == initial
    assert int(document.UndoCount) == 1 and int(document.RedoCount) == 1
    assert str(created.Label) == "Operator label independent of canonical identity"
    document.redo()
    assert adapter.read_transition_object(created) == updated
    assert int(document.UndoCount) == 2 and int(document.RedoCount) == 0

    failure_intent = replace(
        updated.intent,
        target_signed_offset_mm=updated.intent.target_signed_offset_mm + 0.1,
    )
    failure_state = api.analyse_transition_state(
        api.replace_transition_intent(updated, failure_intent)
    )
    before_failure = (
        _custom_payload(created),
        int(document.UndoCount),
        int(document.RedoCount),
        len(document.Objects),
    )
    original_writer = adapter._write_transition_payload

    def fail_after_write(obj, payload):
        original_writer(obj, payload)
        raise RuntimeError("injected failure after canonical property write")

    adapter._write_transition_payload = fail_after_write
    try:
        error = _expect_adapter_error(
            lambda: store.update(document, created, failure_state),
            "transaction-failed",
        )
        assert error.document_mutation is False and error.recoverable is True
    finally:
        adapter._write_transition_payload = original_writer
    assert (
        _custom_payload(created),
        int(document.UndoCount),
        int(document.RedoCount),
        len(document.Objects),
    ) == before_failure
    assert adapter.read_transition_object(created) == updated

    mismatched = api.TransitionState(
        replace(updated.intent, transition_id="transition:phase4:different"),
        updated.analysis,
    )
    before_mismatch = (int(document.UndoCount), _custom_payload(created))
    _expect_adapter_error(
        lambda: store.update(document, created, mismatched),
        "stable-identity-mismatch",
    )
    assert (int(document.UndoCount), _custom_payload(created)) == before_mismatch

    path = pathlib.Path(directory) / "transition-persistence.FCStd"
    persisted_payload = _custom_payload(created)
    document.saveAs(str(path))
    App.closeDocument(document.Name)
    reopened = App.openDocument(str(path))
    reopened_object = reopened.getObject(created_name)
    assert reopened_object is not None
    assert len(reopened.Objects) == 3
    assert str(reopened_object.TypeId) == adapter.FREECAD_TRANSITION_OBJECT_TYPE
    assert "Shape" not in reopened_object.PropertiesList
    assert all(
        "ReadOnly" in reopened_object.getEditorMode(property_name)
        for property_name in adapter.FREECAD_CUSTOM_PROPERTIES
    )
    assert _custom_payload(reopened_object) == persisted_payload
    assert adapter.read_transition_object(reopened_object) == updated
    assert adapter.find_transition_object(reopened, updated.intent.transition_id) is (
        reopened_object
    )
    assert str(reopened_object.Label) == (
        "Operator label independent of canonical identity"
    )
    assert str(reopened.getObject(foreign_name).OperatorData) == "untouched"
    assert str(reopened.getObject(other_record_name).TrackTemplateRecordType) == (
        "tracktemplate.other-state"
    )
    App.closeDocument(reopened.Name)


def _validate_create_history_and_failures(store):
    state = _analysed("transition:phase4:create-history")
    document = _new_document("CreateHistory")
    obj = store.create(document, state)
    object_name = str(obj.Name)
    assert len(document.Objects) == 1 and int(document.UndoCount) == 1
    document.undo()
    assert document.getObject(object_name) is None
    assert len(document.Objects) == 0
    assert int(document.UndoCount) == 0 and int(document.RedoCount) == 1
    _expect_adapter_error(
        lambda: adapter.read_transition_object(obj),
        "invalid-object-reference",
    )
    document.redo()
    restored = document.getObject(object_name)
    assert restored is not None and adapter.read_transition_object(restored) == state
    assert int(document.UndoCount) == 1 and int(document.RedoCount) == 0

    before_duplicate = (len(document.Objects), int(document.UndoCount))
    _expect_adapter_error(
        lambda: store.create(document, state),
        "duplicate-stable-identity",
    )
    assert (len(document.Objects), int(document.UndoCount)) == before_duplicate
    App.closeDocument(document.Name)

    failed_document = _new_document("FailedCreate")
    original_writer = adapter._write_transition_payload

    def fail_after_write(obj, payload):
        original_writer(obj, payload)
        raise RuntimeError("injected create failure after canonical property write")

    adapter._write_transition_payload = fail_after_write
    try:
        error = _expect_adapter_error(
            lambda: store.create(failed_document, state),
            "transaction-failed",
        )
        assert error.document_mutation is False
    finally:
        adapter._write_transition_payload = original_writer
    assert len(failed_document.Objects) == 0
    assert int(failed_document.UndoCount) == 0
    assert int(failed_document.RedoCount) == 0
    App.closeDocument(failed_document.Name)


def _validate_stale_and_corrupt_records(store):
    state = _analysed("transition:phase4:stale")
    document = _new_document("Stale")
    obj = store.create(document, state)
    record = json.loads(_custom_payload(obj))
    record["intent"]["radius_mm"] += 1.0
    stale_payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    document.openTransaction("Inject stale derived-result fixture")
    obj.TrackTemplateStateJSON = stale_payload
    document.commitTransaction()
    undo_before_read = int(document.UndoCount)
    stale = adapter.read_transition_object(obj)
    assert stale.analysis is None
    assert stale.findings == ("stale-analysis-discarded",)
    assert _custom_payload(obj) == stale_payload
    assert int(document.UndoCount) == undo_before_read
    recovered = api.analyse_transition_state(stale)
    store.update(document, obj, recovered)
    assert api.transition_analysis_status(adapter.read_transition_object(obj)) == (
        "current"
    )

    document.openTransaction("Inject corrupt derived-result fixture")
    corrupt_record = json.loads(_custom_payload(obj))
    corrupt_record["analysis"]["transition_length_mm"] += 1.0
    corrupt_payload = json.dumps(
        corrupt_record,
        sort_keys=True,
        separators=(",", ":"),
    )
    obj.TrackTemplateStateJSON = corrupt_payload
    document.commitTransaction()
    corrupt = adapter.read_transition_object(obj)
    assert corrupt.analysis is None
    assert corrupt.findings == ("corrupt-analysis-discarded",)
    assert _custom_payload(obj) == corrupt_payload
    App.closeDocument(document.Name)

    invalid_document = _new_document("Invalid")
    valid_record = json.loads(api.transition_state_to_json(state))
    valid_record["schema_version"] = 999
    future_payload = json.dumps(valid_record, sort_keys=True, separators=(",", ":"))
    future = _add_indexed_object(
        invalid_document,
        "FutureTransition",
        adapter.FREECAD_TRANSITION_RECORD_TYPE,
        future_payload,
    )
    before = (len(invalid_document.Objects), int(invalid_document.UndoCount), _custom_payload(future))
    _expect_adapter_error(
        lambda: adapter.read_transition_object(future),
        "invalid-canonical-state",
        source_code="unsupported-schema-version",
    )
    assert (len(invalid_document.Objects), int(invalid_document.UndoCount), _custom_payload(future)) == before

    missing = _add_indexed_object(
        invalid_document,
        "MissingStateTransition",
        adapter.FREECAD_TRANSITION_RECORD_TYPE,
    )
    _expect_adapter_error(
        lambda: adapter.read_transition_object(missing),
        "invalid-record-envelope",
    )
    App.closeDocument(invalid_document.Name)

    duplicate_document = _new_document("Duplicate")
    duplicate_payload = api.transition_state_to_json(state)
    duplicate_a = _add_indexed_object(
        duplicate_document,
        "DuplicateTransitionA",
        adapter.FREECAD_TRANSITION_RECORD_TYPE,
        duplicate_payload,
    )
    duplicate_b = _add_indexed_object(
        duplicate_document,
        "DuplicateTransitionB",
        adapter.FREECAD_TRANSITION_RECORD_TYPE,
        duplicate_payload,
    )
    duplicate_before = (
        len(duplicate_document.Objects),
        int(duplicate_document.UndoCount),
        _custom_payload(duplicate_a),
        _custom_payload(duplicate_b),
    )
    _expect_adapter_error(
        lambda: adapter.find_transition_object(
            duplicate_document,
            state.intent.transition_id,
        ),
        "duplicate-stable-identity",
    )
    assert (
        len(duplicate_document.Objects),
        int(duplicate_document.UndoCount),
        _custom_payload(duplicate_a),
        _custom_payload(duplicate_b),
    ) == duplicate_before
    App.closeDocument(duplicate_document.Name)


def _validate_runtime_gate(qualification):
    unqualified = copy.deepcopy(qualification)
    unqualified["compatibility_evaluation"]["status"] = "unqualified"
    _expect_adapter_error(
        lambda: adapter.FreeCADTransitionStore(unqualified),
        "runtime-not-qualified",
    )
    mismatch = copy.deepcopy(qualification)
    mismatch["runtime"]["freecad"]["version_info"] = [1, 1, 0]
    _expect_adapter_error(
        lambda: adapter.FreeCADTransitionStore(mismatch),
        "runtime-evidence-mismatch",
    )

    document = App.newDocument(DOCUMENT_PREFIX + "UndoDisabled")
    document.UndoMode = 0
    store = adapter.FreeCADTransitionStore(qualification)
    _expect_adapter_error(
        lambda: store.create(document, _analysed("transition:phase4:undo-disabled")),
        "undo-disabled",
    )
    assert len(document.Objects) == 0
    App.closeDocument(document.Name)


def _close_test_documents():
    for name in list(App.listDocuments()):
        if str(name).startswith(DOCUMENT_PREFIX):
            App.closeDocument(name)


qualification = bootstrap.require_qualified_runtime(
    ROOT / "reference" / "contracts" / "phase1-compatibility.json"
)
assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
store = adapter.FreeCADTransitionStore(qualification)
try:
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase4-persistence-"
    ) as temporary_directory:
        _validate_lifecycle(store, temporary_directory)
        _validate_create_history_and_failures(store)
        _validate_stale_and_corrupt_records(store)
        _validate_runtime_gate(qualification)
finally:
    _close_test_documents()

print("Phase 4 transition FreeCAD persistence validation passed")
