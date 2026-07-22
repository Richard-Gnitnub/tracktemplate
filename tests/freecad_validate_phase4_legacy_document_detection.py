#!/usr/bin/env python3
"""Prove read-only legacy detection in disposable real FreeCAD documents."""

import json
import pathlib
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import legacy_document  # noqa: E402


DOCUMENT_PREFIX = "TrackTemplatePhase4LegacyDetection"
GENERATOR_ID = "ModelRailwayCurveTemplate.IndependentEasements"
B14 = "10.2A8A7B14"
B15 = "10.2A8A7B15"
CAPTURE_PROPERTIES = (
    "GeneratedBy",
    "GeneratedRole",
    "TemplateSetID",
    "GeneratorVersion",
    "TrackConfigurationJSON",
    "OperatorNotesJSON",
    "OperatorData",
)


def _contract():
    return json.loads(
        (ROOT / "reference" / "contracts" / "phase1-compatibility.json").read_text(
            encoding="utf-8"
        )
    )


def _new_document(suffix):
    document = App.newDocument(DOCUMENT_PREFIX + suffix)
    document.UndoMode = 1
    return document


def _add_string(obj, name, value):
    obj.addProperty("App::PropertyString", name, "Legacy detection fixture")
    setattr(obj, name, value)


def _owned(document, name, version, payload=None, role="Settings"):
    obj = document.addObject("App::FeaturePython", name)
    _add_string(obj, "GeneratedBy", GENERATOR_ID)
    _add_string(obj, "GeneratedRole", role)
    _add_string(obj, "TemplateSetID", "SET-001")
    if version is not None:
        _add_string(obj, "GeneratorVersion", version)
    if payload is not None:
        _add_string(obj, "TrackConfigurationJSON", payload)
    return obj


def _foreign(document, name="OperatorObject"):
    obj = document.addObject("App::FeaturePython", name)
    obj.Label = "Operator object remains independent"
    _add_string(obj, "GeneratedBy", "Some.Other.Tool")
    _add_string(obj, "GeneratorVersion", "99.0 FUTURE")
    _add_string(obj, "TrackConfigurationJSON", "{not-json")
    _add_string(obj, "OperatorData", "untouched")
    return obj


def _snapshot(document):
    objects = []
    for obj in sorted(document.Objects, key=lambda item: str(item.Name)):
        properties = tuple(obj.PropertiesList)
        values = tuple(
            (name, str(getattr(obj, name)))
            for name in CAPTURE_PROPERTIES
            if name in properties
        )
        objects.append(
            (
                str(obj.Name),
                str(obj.Label),
                str(obj.TypeId),
                properties,
                values,
            )
        )
    return (
        int(document.UndoCount),
        int(document.RedoCount),
        tuple(objects),
    )


def _codes(report):
    return {item.code for item in report.findings}


def _inspect_without_mutation(document, contract):
    before = _snapshot(document)
    report = legacy_document.inspect_legacy_document(document, contract)
    assert _snapshot(document) == before
    assert report.write_authorized is False
    return report


def _validate_accepted_and_reopen(contract, directory):
    document = _new_document("Mixed")
    b14 = _owned(
        document,
        "B14Settings",
        B14 + " WHOLE WORKFLOW",
        json.dumps({"schema_version": 1, "macro_version": B14}, sort_keys=True),
    )
    _add_string(b14, "OperatorNotesJSON", "{not-project-json")
    _owned(
        document,
        "B15ChairSettings",
        B15 + " CHAIR DISPLAY",
        json.dumps({"schema_version": 5, "macro_version": B15}, sort_keys=True),
        role="ChairAnalysisDisplay",
    )
    foreign = _foreign(document)
    assert "Shape" not in foreign.PropertiesList

    report = _inspect_without_mutation(document, contract)
    assert report.status == legacy_document.STATUS_INSPECTION_ONLY
    assert report.version_window_status == "accepted"
    assert report.observed_versions == (B14, B15)
    assert report.owned_object_names == ("B14Settings", "B15ChairSettings")
    assert report.owned_roles == ("ChairAnalysisDisplay", "Settings")
    assert report.foreign_object_count == 1
    assert "B14Settings.OperatorNotesJSON" not in report.json_payload_paths
    assert _codes(report) == {"migration-family-not-qualified"}

    path = pathlib.Path(directory) / "legacy-detection-mixed.FCStd"
    document.saveAs(str(path))
    persisted_snapshot = _snapshot(document)
    persisted_json = legacy_document.legacy_inspection_to_json(report)
    App.closeDocument(document.Name)

    reopened = App.openDocument(str(path))
    assert _snapshot(reopened) == persisted_snapshot
    reopened_report = _inspect_without_mutation(reopened, contract)
    assert legacy_document.legacy_inspection_to_json(reopened_report) == persisted_json
    assert str(reopened.getObject("OperatorObject").OperatorData) == "untouched"
    App.closeDocument(reopened.Name)


def _validate_single_versions(contract):
    for suffix, version in (("B14", B14), ("B15", B15)):
        document = _new_document(suffix)
        _owned(document, suffix + "Object", version + " descriptive suffix")
        report = _inspect_without_mutation(document, contract)
        assert report.version_window_status == "accepted"
        assert report.observed_versions == (version,)
        assert report.status == legacy_document.STATUS_INSPECTION_ONLY
        App.closeDocument(document.Name)


def _validate_unsupported_and_blocked(contract):
    versionless = _new_document("Versionless")
    _owned(versionless, "VersionlessObject", None)
    report = _inspect_without_mutation(versionless, contract)
    assert report.version_window_status == "incomplete"
    assert "versionless-owned-object" in _codes(report)
    App.closeDocument(versionless.Name)

    future = _new_document("Future")
    _owned(future, "FutureObject", "10.2A8A7B99 FUTURE")
    report = _inspect_without_mutation(future, contract)
    assert report.version_window_status == "unsupported"
    assert "unsupported-version-set" in _codes(report)
    App.closeDocument(future.Name)

    conflict = _new_document("Conflict")
    _owned(
        conflict,
        "ConflictObject",
        B14,
        json.dumps({"schema_version": 1, "macro_version": B15}),
    )
    report = _inspect_without_mutation(conflict, contract)
    assert report.status == legacy_document.STATUS_BLOCKED
    assert "conflicting-object-version-evidence" in _codes(report)
    App.closeDocument(conflict.Name)

    malformed = _new_document("Malformed")
    _owned(malformed, "MalformedObject", B14, "{not-json")
    report = _inspect_without_mutation(malformed, contract)
    assert report.status == legacy_document.STATUS_BLOCKED
    assert "malformed-json-payload" in _codes(report)
    App.closeDocument(malformed.Name)


def _close_test_documents():
    for name in list(App.listDocuments()):
        if str(name).startswith(DOCUMENT_PREFIX):
            App.closeDocument(name)


contract = _contract()
try:
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase4-legacy-detection-"
    ) as temporary_directory:
        _validate_accepted_and_reopen(contract, temporary_directory)
        _validate_single_versions(contract)
        _validate_unsupported_and_blocked(contract)
finally:
    _close_test_documents()

print("Phase 4 legacy document FreeCAD detection validation passed")
