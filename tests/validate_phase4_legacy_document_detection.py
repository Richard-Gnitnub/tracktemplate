#!/usr/bin/env python3
"""Validate the bounded Phase 4 B14/B15 read-only document detector."""

import ast
import copy
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate.compatibility import legacy_document  # noqa: E402


CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
MODULE_PATH = ROOT / "tracktemplate" / "compatibility" / "legacy_document.py"
FREECAD_TEST_PATH = ROOT / "tests" / "freecad_validate_phase4_legacy_document_detection.py"
GENERATOR_ID = "ModelRailwayCurveTemplate.IndependentEasements"
B14 = "10.2A8A7B14"
B15 = "10.2A8A7B15"
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


class FakeObject:
    def __init__(self, name, properties):
        self.Name = name
        self.PropertiesList = list(properties)
        for property_name, value in properties.items():
            setattr(self, property_name, value)


class FakeDocument:
    def __init__(self, objects):
        self.Objects = list(objects)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _owned(name, version, role="Settings", set_id="SET-001", **payloads):
    properties = {
        "GeneratedBy": GENERATOR_ID,
        "GeneratedRole": role,
        "TemplateSetID": set_id,
    }
    if version is not None:
        properties["GeneratorVersion"] = version
    properties.update(payloads)
    return FakeObject(name, properties)


def _foreign(name="OperatorObject"):
    return FakeObject(
        name,
        {
            "GeneratedBy": "Some.Other.Tool",
            "GeneratorVersion": "99.0 FUTURE",
            "BrokenJSON": "{not-json",
            "OperatorData": "untouched",
        },
    )


def _snapshot(document):
    return tuple(
        (
            obj.Name,
            tuple(obj.PropertiesList),
            tuple((name, copy.deepcopy(getattr(obj, name))) for name in obj.PropertiesList),
        )
        for obj in document.Objects
    )


def _codes(report):
    return {item.code for item in report.findings}


def _expect_error(action, code):
    try:
        action()
    except legacy_document.LegacyInspectionError as error:
        assert error.code == code, error
        assert error.diagnostic() == {
            "code": code,
            "message": error.detail,
            "recoverable": True,
            "document_mutation": False,
        }
        return
    raise AssertionError("Expected LegacyInspectionError {!r}".format(code))


def _validate_accepted_windows():
    contract = _contract()
    b14_payload = json.dumps(
        {
            "schema_version": 1,
            "macro_version": B14 + " descriptive suffix",
        },
        sort_keys=True,
    )
    b14 = _owned(
        "B14Settings",
        B14 + " WHOLE WORKFLOW",
        TrackConfigurationJSON=b14_payload,
        OperatorNotesJSON="{not-project-json",
    )
    document = FakeDocument([b14, _foreign()])
    before = _snapshot(document)
    report = legacy_document.inspect_legacy_document(document, contract)
    assert _snapshot(document) == before
    assert report.status == legacy_document.STATUS_INSPECTION_ONLY
    assert report.version_window_status == "accepted"
    assert report.observed_versions == (B14,)
    assert report.owned_object_names == ("B14Settings",)
    assert report.owned_roles == ("Settings",)
    assert report.foreign_object_count == 1
    assert "B14Settings.OperatorNotesJSON" not in report.json_payload_paths
    assert report.write_authorized is False
    assert _codes(report) == {"migration-family-not-qualified"}
    record = report.to_record()
    assert set(record) == {
        "schema_id",
        "schema_version",
        "contract_id",
        "status",
        "version_window_status",
        "generator_id",
        "supported_versions",
        "observed_versions",
        "owned_object_names",
        "owned_roles",
        "json_payload_paths",
        "foreign_object_count",
        "version_evidence",
        "findings",
        "write_authorized",
    }
    encoded = legacy_document.legacy_inspection_to_json(report)
    assert json.loads(encoded) == record
    assert encoded == (
        legacy_document.legacy_inspection_to_json(
            legacy_document.inspect_legacy_document(document, contract)
        )
    )

    b15 = _owned(
        "B15Settings",
        B15 + " DISPLAY REVISION",
        ChairAnalysisResultJSON=json.dumps(
            {"schema_version": 5, "macro_version": B15},
            sort_keys=True,
        ),
    )
    b15_report = legacy_document.inspect_legacy_document(
        FakeDocument([b15]),
        contract,
    )
    assert b15_report.version_window_status == "accepted"
    assert b15_report.observed_versions == (B15,)

    mixed = legacy_document.inspect_legacy_document(
        FakeDocument([b15, _foreign("ForeignFirst"), b14]),
        contract,
    )
    assert mixed.version_window_status == "accepted"
    assert mixed.observed_versions == (B14, B15)
    assert mixed.owned_object_names == ("B14Settings", "B15Settings")
    assert mixed.foreign_object_count == 1
    reordered = legacy_document.inspect_legacy_document(
        FakeDocument([b14, b15, _foreign("ForeignFirst")]),
        contract,
    )
    assert mixed == reordered


def _validate_inspection_only_cases():
    contract = _contract()
    empty = legacy_document.inspect_legacy_document(FakeDocument([]), contract)
    assert empty.status == legacy_document.STATUS_INSPECTION_ONLY
    assert empty.version_window_status == "not-detected"
    assert _codes(empty) == {"no-owned-legacy-objects"}

    foreign = legacy_document.inspect_legacy_document(
        FakeDocument([_foreign()]),
        contract,
    )
    assert foreign.version_window_status == "not-detected"
    assert foreign.foreign_object_count == 1

    versionless = legacy_document.inspect_legacy_document(
        FakeDocument([_owned("Versionless", None)]),
        contract,
    )
    assert versionless.version_window_status == "incomplete"
    assert _codes(versionless) == {
        "versionless-owned-object",
        "migration-family-not-qualified",
    }

    future = legacy_document.inspect_legacy_document(
        FakeDocument([_owned("Future", "10.2A8A7B99 FUTURE")]),
        contract,
    )
    assert future.version_window_status == "unsupported"
    assert future.observed_versions == ("10.2A8A7B99",)
    assert _codes(future) == {
        "unsupported-version-set",
        "migration-family-not-qualified",
    }

    incomplete = _owned("Incomplete", B14)
    del incomplete.GeneratedRole
    incomplete.PropertiesList.remove("GeneratedRole")
    del incomplete.TemplateSetID
    incomplete.PropertiesList.remove("TemplateSetID")
    incomplete_report = legacy_document.inspect_legacy_document(
        FakeDocument([incomplete]),
        contract,
    )
    assert incomplete_report.version_window_status == "accepted"
    assert _codes(incomplete_report) == {
        "missing-family-role",
        "missing-template-set-identity",
        "migration-family-not-qualified",
    }


def _validate_blocked_cases():
    contract = _contract()
    cases = (
        (
            _owned(
                "Conflict",
                B14,
                TurnoutConfigurationJSON=json.dumps(
                    {"schema_version": 1, "macro_version": B15}
                ),
            ),
            "conflicting-object-version-evidence",
        ),
        (
            _owned("MalformedJSON", B14, TurnoutConfigurationJSON="{not-json"),
            "malformed-json-payload",
        ),
        (
            _owned(
                "DuplicateJSON",
                B14,
                TurnoutConfigurationJSON='{"macro_version":"%s","macro_version":"%s"}'
                % (B14, B14),
            ),
            "malformed-json-payload",
        ),
        (
            _owned(
                "BadSchema",
                B14,
                TurnoutConfigurationJSON=json.dumps({"schema_version": True}),
            ),
            "malformed-schema-version",
        ),
        (
            _owned(
                "BadJSONRoot",
                B14,
                TurnoutConfigurationJSON=json.dumps("not a payload"),
            ),
            "malformed-json-root",
        ),
        (
            _owned(
                "BadJSONVersion",
                B14,
                TurnoutConfigurationJSON=json.dumps(
                    {"schema_version": 1, "source_macro_version": 14}
                ),
            ),
            "malformed-json-version",
        ),
        (
            _owned("BadGeneratorVersion", 14),
            "malformed-generator-version",
        ),
    )
    for obj, expected_code in cases:
        document = FakeDocument([obj, _foreign(obj.Name + "Foreign")])
        before = _snapshot(document)
        report = legacy_document.inspect_legacy_document(document, contract)
        assert _snapshot(document) == before
        assert report.status == legacy_document.STATUS_BLOCKED
        assert report.version_window_status == "conflicting-or-corrupt"
        assert expected_code in _codes(report)
        assert report.write_authorized is False


def _validate_fail_closed_invocation():
    contract = _contract()
    _expect_error(
        lambda: legacy_document.inspect_legacy_document(FakeDocument([]), None),
        "invalid-compatibility-contract",
    )
    changed_id = copy.deepcopy(contract)
    changed_id["contract_id"] = "unknown"
    _expect_error(
        lambda: legacy_document.inspect_legacy_document(FakeDocument([]), changed_id),
        "unsupported-compatibility-contract",
    )
    broadened = copy.deepcopy(contract)
    broadened["legacy_document_window"]["supported_ingress_versions"].append(
        "10.2A8A7B16"
    )
    _expect_error(
        lambda: legacy_document.inspect_legacy_document(FakeDocument([]), broadened),
        "invalid-compatibility-contract",
    )
    duplicate_names = FakeDocument(
        [_owned("Duplicate", B14), _owned("Duplicate", B15)]
    )
    _expect_error(
        lambda: legacy_document.inspect_legacy_document(duplicate_names, contract),
        "ambiguous-document-objects",
    )


def _validate_structure_and_controls():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
    assert imported_roots == {"dataclasses", "json"}
    for forbidden in (
        "import FreeCAD",
        "import Part",
        "openTransaction(",
        "commitTransaction(",
        "abortTransaction(",
        "addObject(",
        "addProperty(",
        "setattr(",
        "recompute(",
        "saveAs(",
    ):
        assert forbidden not in source
    assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()
    expected_json_properties = None
    for relative in SOURCE_HASHES:
        macro_tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        observed = tuple(
            sorted(
                {
                    node.value
                    for node in ast.walk(macro_tree)
                    if isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and node.value.endswith("JSON")
                    and node.value.isidentifier()
                }
            )
        )
        expected_json_properties = observed if expected_json_properties is None else expected_json_properties
        assert observed == expected_json_properties
    assert legacy_document.RECOGNISED_LEGACY_JSON_PROPERTIES == expected_json_properties

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    detector = modules["tracktemplate.compatibility.legacy_document"]
    assert detector["layer"] == "compatibility"
    assert detector["imports"] == ["dataclasses", "json"]
    assert detector["warning_signals"] == []
    assert not any(
        item.startswith("tracktemplate.compatibility.legacy_document")
        for item in modules["tracktemplate.api"]["imports"]
    )

    script = """
import importlib.abc
import sys

forbidden = {{"FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"}}
attempted = []

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden host import: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {root!r})
from tracktemplate.compatibility import legacy_document
assert attempted == []
assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    for relative, expected_hash in SOURCE_HASHES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash
    freecad_source = FREECAD_TEST_PATH.read_text(encoding="utf-8")
    for marker in (
        "TemporaryDirectory",
        "saveAs(",
        "App.openDocument(",
        "STATUS_BLOCKED",
        "version_window_status == \"accepted\"",
        "Phase 4 legacy document FreeCAD detection validation passed",
    ):
        assert marker in freecad_source
    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(encoding="utf-8")
    assert "Legacy-document detection tranche" in evidence
    assert "freecad_validate_phase4_legacy_document_detection.py" in validation


def validate():
    _validate_accepted_windows()
    _validate_inspection_only_cases()
    _validate_blocked_cases()
    _validate_fail_closed_invocation()
    _validate_structure_and_controls()
    print("Phase 4 legacy document detection validation passed")


if __name__ == "__main__":
    validate()
