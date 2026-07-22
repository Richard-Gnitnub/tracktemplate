#!/usr/bin/env python3
"""Validate the Phase 4 neutral chair-definition package contract."""

import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tools import validate_dependency_manifest as manifest_validator  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.application import chair_definition as contract  # noqa: E402


SCHEMA_PATH = ROOT / "reference" / "schemas" / "chair-definition-v1.schema.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "chair-definition-v1-contract.json"
MANIFEST_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "chair-definition-v1-contract.dependency-manifest.json"
)
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


def _canonical_json(value):
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _resign(record):
    unsigned = copy.deepcopy(record)
    unsigned.pop("content_signature", None)
    record["content_signature"] = "sha256:" + hashlib.sha256(
        _canonical_json(unsigned).encode("utf-8")
    ).hexdigest()
    return record


def _expect_error(record, code, resign=True, manifest_text=None):
    changed = copy.deepcopy(record)
    if resign:
        _resign(changed)
    try:
        api.chair_definition_package_from_json(
            _canonical_json(changed),
            dependency_manifest_text=manifest_text,
        )
    except api.ChairDefinitionError as error:
        assert error.code == code, error
        assert error.diagnostic() == {
            "code": error.code,
            "path": error.path,
            "message": error.detail,
            "recoverable": True,
            "document_mutation": False,
            "filesystem_mutation": False,
        }
        return error
    raise AssertionError("Expected ChairDefinitionError {!r}".format(code))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_schema_and_fixture():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema"]["const"] == (
        contract.CHAIR_DEFINITION_SCHEMA_ID
    )
    assert schema["properties"]["schema_version"]["const"] == 1
    assert tuple(schema["$defs"]["projectStatus"]["enum"]) == (
        contract.CHAIR_PROJECT_STATUSES
    )
    assert tuple(
        schema["$defs"]["lineage"]["properties"]["classifications"]["items"][
            "enum"
        ]
    ) == contract.CHAIR_CLASSIFICATIONS
    assert tuple(schema["$defs"]["permissions"]["required"]) == (
        contract.CHAIR_PERMISSION_FIELDS
    )
    assert tuple(
        schema["$defs"]["procedure"]["properties"]["kind"]["enum"]
    ) == contract.CHAIR_PROCEDURE_KINDS

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest_validator.validate_document(
        manifest, require_project_cleared=True
    ) == []
    assert "S1" not in manifest["subject"]["description"]
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert fixture["definition"]["prototype_designation"] == (
        "TEST-ONLY-NON-PROTOTYPE-CONTRACT-FIXTURE"
    )
    assert "do not define an S1 chair" in fixture["definition"]["description"]
    return fixture, MANIFEST_PATH.read_text(encoding="utf-8")


def _validate_round_trip(record, manifest_text):
    source_text = FIXTURE_PATH.read_text(encoding="utf-8")
    package = api.chair_definition_package_from_json(source_text, manifest_text)
    assert isinstance(package, api.ChairDefinitionPackage)
    assert package.package_id == "tracktemplate:test:chair-contract"
    assert package.package_version == "1.0.0-test"
    assert package.definition_id == "tracktemplate:test:chair-contract:definition"
    assert package.definition_version == "1.0.0-test"
    assert package.project_status == "project-cleared"
    assert package.validation_status == "passed"
    assert package.acceptance_status == "accepted"
    assert package.content_signature == record["content_signature"]

    canonical_text = api.chair_definition_package_to_json(package)
    assert canonical_text == _canonical_json(record)
    reopened = api.chair_definition_package_from_json(canonical_text, manifest_text)
    assert reopened == package
    assert api.chair_definition_package_to_json(reopened) == canonical_text
    assert api.chair_definition_manifest_signature(manifest_text) == (
        record["dependency_manifest"]["content_signature"]
    )
    assert api.verify_chair_definition_manifest(package, manifest_text) is None

    detached = package.to_record()
    detached["package"]["package_id"] = "changed"
    assert package.to_record()["package"]["package_id"] == package.package_id
    try:
        package.package_id = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ChairDefinitionPackage is not immutable")

    status = api.chair_definition_package_status(package, manifest_text)
    assert status == {
        "status": "blocked",
        "findings": ("phase9-production-admission-not-enabled",),
        "production_geometry_authorized": False,
        "document_mutation_authorized": False,
        "filesystem_mutation_authorized": False,
    }
    assert api.CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED is False

    try:
        api.ChairDefinitionPackage(
            package_id=package.package_id,
            package_version=package.package_version,
            definition_id=package.definition_id,
            definition_version=package.definition_version,
            prototype_designation=package.prototype_designation,
            content_signature=package.content_signature,
            project_status=package.project_status,
            validation_status=package.validation_status,
            acceptance_status=package.acceptance_status,
            _canonical_json="{}",
        )
    except api.ChairDefinitionError as error:
        assert error.code == "invalid-fields"
    else:
        raise AssertionError("direct construction bypassed package validation")

    definition = record["definition"]
    assert definition["canonical_length_unit"] == "mm"
    assert definition["frame"] == {
        "frame_id": "chair-local-right-handed-v1",
        "handedness": "right",
        "x_axis": "nominal-rail-direction",
        "y_axis": "gauge-to-field",
        "z_axis": "up-from-base-mounting-plane",
        "origin": (
            "longitudinal-chair-centre-plane/rail-section-centre-plane/"
            "base-mounting-plane"
        ),
    }
    assert all(
        isinstance(item[field], str)
        for item in definition["quantities"]
        for field in ("source_value", "canonical_value")
    )
    assert not set(definition) & {
        "model_scale",
        "printer_compensation",
        "material_compensation",
        "export_settings",
    }
    assert record["manufacturing_profiles"][0]["model_scale"] == "1"
    forbidden = {"shape", "mesh", "brep", "part_shape", "source_file_body"}

    def visit(value):
        if isinstance(value, dict):
            assert not (set(value) & forbidden)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(record)
    return package


def _validate_fail_closed_contract(record, manifest_text, package):
    changed = copy.deepcopy(record)
    changed["schema_version"] = 2
    _expect_error(changed, "unsupported-schema-version")

    changed = copy.deepcopy(record)
    changed["schema_version"] = True
    _expect_error(changed, "invalid-schema-version")

    changed = copy.deepcopy(record)
    changed["schema"] = "tracktemplate.unknown-chair-package"
    _expect_error(changed, "unsupported-schema")

    changed = copy.deepcopy(record)
    changed["unexpected"] = True
    _expect_error(changed, "invalid-fields")

    changed = copy.deepcopy(record)
    del changed["definition"]["components"]
    _expect_error(changed, "invalid-fields")

    changed = copy.deepcopy(record)
    changed["definition"]["quantities"][0]["source_value"] = 0.1
    _expect_error(changed, "invalid-decimal")

    changed = copy.deepcopy(record)
    quantity = changed["definition"]["quantities"][1]
    quantity["source_value"] = "1"
    quantity["source_unit"] = "in"
    quantity["canonical_value"] = "1"
    _expect_error(changed, "unit-conversion-mismatch")

    converted = copy.deepcopy(record)
    quantity = converted["definition"]["quantities"][1]
    quantity["source_value"] = "1"
    quantity["source_unit"] = "in"
    quantity["canonical_value"] = "25.4"
    _resign(converted)
    converted_package = api.chair_definition_package_from_json(
        _canonical_json(converted)
    )
    converted_record = converted_package.to_record()
    assert converted_record["definition"]["quantities"][1]["source_value"] == "1"
    assert converted_record["definition"]["quantities"][1]["source_unit"] == "in"
    assert converted_record["definition"]["quantities"][1][
        "canonical_value"
    ] == "25.4"

    changed = copy.deepcopy(record)
    changed["definition"]["quantities"][0]["uncertainty"] = {
        "value": "-0.1",
        "unit": "mm",
    }
    _expect_error(changed, "invalid-uncertainty")

    changed = copy.deepcopy(record)
    changed["definition"]["datums"] = changed["definition"]["datums"][:-1]
    _expect_error(changed, "missing-required-datum")

    changed = copy.deepcopy(record)
    changed["definition"]["quantities"][1]["quantity_id"] = (
        changed["definition"]["quantities"][0]["quantity_id"]
    )
    _expect_error(changed, "duplicate-identity")

    changed = copy.deepcopy(record)
    changed["definition"]["datums"].reverse()
    _expect_error(changed, "invalid-order")

    changed = copy.deepcopy(record)
    changed["definition"]["procedures"][0]["input_ids"] = ["missing:input"]
    _expect_error(changed, "missing-reference")

    changed = copy.deepcopy(record)
    changed["definition"]["components"][0]["procedure_ids"] = []
    _expect_error(changed, "inconsistent-component-presence")

    changed = copy.deepcopy(record)
    changed["definition"]["components"][1]["absence_reason"] = None
    _expect_error(changed, "inconsistent-component-presence")

    changed = copy.deepcopy(record)
    changed["lineage"][0]["derivation"] = None
    _expect_error(changed, "missing-derivation")

    changed = copy.deepcopy(record)
    changed["lineage"][0]["lineage_id"] = "lineage:test:unused"
    _expect_error(changed, "lineage-coverage-mismatch")

    changed = copy.deepcopy(record)
    changed["content_signature"] = "sha256:" + ("0" * 64)
    _expect_error(changed, "content-signature-mismatch", resign=False)

    unresolved = copy.deepcopy(record)
    unresolved["package"]["license_expression"] = "NOASSERTION"
    unresolved["package"]["project_status"] = "unknown"
    unresolved["validation"]["status"] = "blocked"
    unresolved["acceptance"] = {
        "status": "not-accepted",
        "accepted_by": None,
        "accepted_on": None,
        "decision_reference": None,
    }
    unresolved["lineage"][0]["evidence_state"] = "unresolved"
    unresolved["lineage"][0]["derivation"] = None
    unresolved["lineage"][0]["project_status"] = "unknown"
    unresolved["lineage"][0]["validation_state"] = "blocked"
    _resign(unresolved)
    unresolved_package = api.chair_definition_package_from_json(
        _canonical_json(unresolved)
    )
    status = api.chair_definition_package_status(unresolved_package)
    assert status["status"] == "blocked"
    assert set(status["findings"]) == {
        "phase9-production-admission-not-enabled",
        "dependency-manifest-not-verified",
        "package-not-project-cleared",
        "package-licence-unresolved",
        "package-validation-not-passed",
        "package-not-accepted",
        "output-lineage-not-resolved",
        "output-lineage-not-project-cleared",
        "output-lineage-not-accepted",
    }

    changed_manifest = json.loads(manifest_text)
    changed_manifest["subject"]["version"] = "changed"
    try:
        api.verify_chair_definition_manifest(
            package, _canonical_json(changed_manifest)
        )
    except api.ChairDefinitionError as error:
        assert error.code == "dependency-manifest-mismatch"
    else:
        raise AssertionError("changed dependency manifest was accepted")

    future_manifest = json.loads(manifest_text)
    future_manifest["schema_version"] = 2
    try:
        api.verify_chair_definition_manifest(
            package, _canonical_json(future_manifest)
        )
    except api.ChairDefinitionError as error:
        assert error.code == "unsupported-dependency-manifest-version"
    else:
        raise AssertionError("future dependency-manifest version was accepted")

    circular_manifest = json.loads(manifest_text)
    circular_manifest["subject"]["content_sha256"] = "0" * 64
    try:
        api.verify_chair_definition_manifest(
            package, _canonical_json(circular_manifest)
        )
    except api.ChairDefinitionError as error:
        assert error.code == "invalid-fields"
    else:
        raise AssertionError("ambiguous circular content hash was accepted")

    duplicate = api.chair_definition_package_to_json(package)
    duplicate = duplicate[:-1] + ',"schema_version":1}'
    try:
        api.chair_definition_package_from_json(duplicate)
    except api.ChairDefinitionError as error:
        assert error.code == "duplicate-field"
    else:
        raise AssertionError("duplicate JSON field was accepted")
    try:
        api.chair_definition_package_from_json("{not-json}")
    except api.ChairDefinitionError as error:
        assert error.code == "invalid-json"
    else:
        raise AssertionError("invalid JSON was accepted")


def _validate_public_and_structural_boundaries():
    assert api.ChairDefinitionPackage is contract.ChairDefinitionPackage
    assert api.ChairDefinitionError is contract.ChairDefinitionError
    assert api.CHAIR_DEFINITION_SCHEMA_VERSION == 1
    assert contract.CHAIR_DEFINITION_READ_VERSIONS == (1,)
    assert api.CHAIR_DEFINITION_FRAME_ID == "chair-local-right-handed-v1"
    assert api.CHAIR_DEFINITION_LENGTH_UNIT == "mm"

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    application = modules["tracktemplate.application.chair_definition"]
    assert application["layer"] == "application"
    assert application["warning_signals"] == []
    assert application["imports"] == [
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
    ]

    script = """
import importlib.abc
import json
import pathlib
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
from tracktemplate import api
package_text = pathlib.Path({fixture!r}).read_text(encoding="utf-8")
package = api.chair_definition_package_from_json(package_text)
print(json.dumps({{
    "attempted": attempted,
    "round_trip": api.chair_definition_package_from_json(
        api.chair_definition_package_to_json(package)
    ) == package,
    "production": api.chair_definition_package_status(package)[
        "production_geometry_authorized"
    ],
}}))
""".format(root=str(ROOT), fixture=str(FIXTURE_PATH))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "attempted": [],
        "round_trip": True,
        "production": False,
    }


def _validate_source_and_phase_controls():
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(encoding="utf-8")
    assert "chair-definition-v1.schema.json" in evidence
    assert "validate_phase4_chair_definition.py" in validation
    assert "3/6 exit conditions evidenced" in plan
    assert "Phase 9 production admission remains disabled" in " ".join(
        evidence.split()
    )


def validate():
    record, manifest_text = _validate_schema_and_fixture()
    package = _validate_round_trip(record, manifest_text)
    _validate_fail_closed_contract(record, manifest_text, package)
    _validate_public_and_structural_boundaries()
    _validate_source_and_phase_controls()
    print("Phase 4 chair-definition package validation passed")


if __name__ == "__main__":
    validate()
