#!/usr/bin/env python3
"""Fast contracts for Phase 1 provenance and project-status controls."""

import copy
import json
import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools import validate_dependency_manifest as validator  # noqa: E402


SCHEMA_PATH = (
    PROJECT_ROOT / "reference" / "schemas" / "dependency-manifest-v1.schema.json"
)
S1_MANIFEST_PATH = (
    PROJECT_ROOT
    / "reference"
    / "manifests"
    / "s1-chair-pilot.dependency-manifest.json"
)


def _clear_non_copyright_review():
    result = {}
    for area in validator.NON_COPYRIGHT_AREAS:
        result[area] = {
            "status": "no-known-conflict",
            "territories": ["GB"],
            "reviewed_on": "2026-07-20",
            "reviewed_by": "Test reviewer",
            "evidence": ["test-evidence:{}".format(area)],
            "notes": "Synthetic passing record used only by the validator test.",
        }
    return result


def _decision(status="project-cleared"):
    return {
        "status": status,
        "reason": "Synthetic test decision.",
        "reviewed_by": "Test reviewer",
        "reviewed_on": "2026-07-20",
        "decision_reference": "tests/validate_licensing_controls.py",
    }


def _clear_dependency():
    return {
        "identifier": "project-s1-measurements",
        "name": "Synthetic project S1 measurement set",
        "role": "production-input",
        "output_affecting": True,
        "classifications": ["project_measurement", "project_derivation"],
        "source": {
            "creator_or_supplier": "Test contributor",
            "locator": "synthetic:test-fixture",
            "acquired_on": "2026-07-20",
            "evidence_sha256": "1" * 64,
        },
        "license_expression": "CC0-1.0",
        "permissions": {
            "access": "permitted",
            "adaptation": "permitted",
            "production_output": "permitted",
            "redistribution": "permitted",
            "commercial_use": "permitted",
            "publication": "permitted",
        },
        "conditions": [],
        "contribution_attestation": {
            "status": "recorded",
            "reference": "Signed-off-by: Test Contributor <test@example.invalid>",
        },
        "non_copyright_review": _clear_non_copyright_review(),
        "project_status": _decision(),
    }


def _clear_package_manifest():
    return {
        "schema_version": 1,
        "manifest_id": "tracktemplate:test-s1:manifest:1",
        "manifest_kind": "package",
        "audit_scope": "s1-chair-release-path",
        "subject": {
            "identifier": "tracktemplate:test-s1",
            "version": "1.0.0",
            "description": "Synthetic project-cleared package validator fixture.",
            "content_sha256": "2" * 64,
            "package_license": "CC0-1.0",
        },
        "intended_uses": [
            "public-redistribution",
            "commercial-production",
            "publication",
            "physical-production",
        ],
        "dependencies": [_clear_dependency()],
        "non_copyright_review": _clear_non_copyright_review(),
        "project_status": _decision(),
    }


def _clear_output_manifest():
    result = _clear_package_manifest()
    result["manifest_id"] = "tracktemplate:test-output:manifest:1"
    result["manifest_kind"] = "output"
    result["subject"] = {
        "identifier": "tracktemplate:test-output",
        "version": "1",
        "description": "Synthetic project-cleared output validator fixture.",
        "generator": {
            "program": "TrackTemplateMacro",
            "version": "test",
            "source_sha256": "3" * 64,
        },
        "canonical_model_sha256": "4" * 64,
        "artifacts": [
            {
                "path": "test-output.step",
                "format": "STEP",
                "sha256": "5" * 64,
            }
        ],
    }
    return result


def _expect_error(document, expected_text, require_project_cleared=False):
    errors = validator.validate_document(
        document,
        require_project_cleared=require_project_cleared,
    )
    assert any(expected_text in error for error in errors), errors


def validate():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == validator.SCHEMA_VERSION
    assert tuple(schema["properties"]["manifest_kind"]["enum"]) == validator.MANIFEST_KINDS
    assert tuple(schema["properties"]["audit_scope"]["enum"]) == validator.AUDIT_SCOPES
    assert tuple(schema["$defs"]["projectStatus"]["enum"]) == validator.PROJECT_STATUSES
    assert tuple(
        schema["$defs"]["dependency"]["properties"]["classifications"]["items"]["enum"]
    ) == validator.CLASSIFICATIONS
    assert tuple(schema["$defs"]["permissions"]["required"]) == validator.PERMISSION_FIELDS
    assert tuple(
        schema["$defs"]["nonCopyrightReview"]["required"]
    ) == validator.NON_COPYRIGHT_AREAS

    current = json.loads(S1_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert validator.validate_document(current) == []
    assert current["project_status"]["status"] == "unknown"
    assert current["subject"]["package_license"] == "NOASSERTION"
    assert any(
        item["project_status"]["status"] == "reference-only"
        and not item["output_affecting"]
        for item in current["dependencies"]
    )
    _expect_error(current, "rather than project-cleared", require_project_cleared=True)

    package = _clear_package_manifest()
    output = _clear_output_manifest()
    assert validator.validate_document(package, require_project_cleared=True) == []
    assert validator.validate_document(output, require_project_cleared=True) == []

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["project_status"]["status"] = "unknown"
    _expect_error(changed, "output-affecting but not project-cleared")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["license_expression"] = "NOASSERTION"
    _expect_error(changed, "cannot be project-cleared with NOASSERTION")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["permissions"]["adaptation"] = "restricted"
    _expect_error(changed, "requires permitted or not-applicable adaptation")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["permissions"]["production_output"] = "unknown"
    _expect_error(changed, "requires permitted production output")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["permissions"]["redistribution"] = "restricted"
    _expect_error(changed, "requires permitted redistribution")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["permissions"]["commercial_use"] = "restricted"
    _expect_error(changed, "requires permitted commercial use")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["permissions"]["publication"] = "unknown"
    _expect_error(changed, "requires permitted publication")

    changed = copy.deepcopy(package)
    changed["non_copyright_review"]["patents"]["status"] = "not-performed"
    _expect_error(changed, "patents blocks project-cleared status")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["contribution_attestation"]["status"] = "missing"
    _expect_error(changed, "without authority evidence")

    changed = copy.deepcopy(package)
    changed["dependencies"].append(copy.deepcopy(changed["dependencies"][0]))
    _expect_error(changed, "duplicate identifiers")

    changed = copy.deepcopy(package)
    changed["dependencies"][0]["role"] = "comparison-only"
    _expect_error(changed, "cannot be output-affecting")

    changed = copy.deepcopy(package)
    changed["subject"]["package_license"] = "NOASSERTION"
    _expect_error(changed, "package_license cannot be NOASSERTION")

    changed = copy.deepcopy(output)
    changed["subject"]["artifacts"][0]["sha256"] = "not-a-hash"
    _expect_error(changed, "lowercase SHA-256")

    changed = copy.deepcopy(output)
    del changed["subject"]["generator"]
    _expect_error(changed, "subject is missing: generator")

    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "https://developercertificate.org/" in contributing
    assert "Signed-off-by: Your Name <your.email@example.com>" in contributing
    assert "Data and evidence declaration" in contributing
    assert "upstream table" in contributing
    assert "proprietary CAD" in contributing

    policy = (
        PROJECT_ROOT / "reference" / "LICENSING_BOUNDARIES.md"
    ).read_text(encoding="utf-8")
    assert "base policy accepted by the project owner on 2026-07-20" in policy.lower()
    assert "No package or output may receive `project-cleared` status" in policy
    assert "validate_dependency_manifest.py" in policy
    assert "registered_designs" in policy
    assert "unregistered_designs" in policy
    assert "patents" in policy
    assert "trade_marks" in policy

    living_documents = [
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "NOTICE.md",
        PROJECT_ROOT / "reference" / "ARCHITECTURE.md",
        PROJECT_ROOT / "reference" / "LICENSING_BOUNDARIES.md",
        PROJECT_ROOT / "reference" / "PHASE1_INVENTORY.md",
        PROJECT_ROOT / "reference" / "PROJECT_PLAN.md",
        PROJECT_ROOT / "reference" / "PROVENANCE.md",
        PROJECT_ROOT / "reference" / "VALIDATION.md",
    ]
    deprecated_status = "rights" + "-cleared"
    for path in living_documents:
        assert deprecated_status not in path.read_text(encoding="utf-8"), path

    assert (PROJECT_ROOT / "tools" / "validate_dependency_manifest.py").stat().st_mode & 0o111
    print("Phase 1 licensing-control validation passed")


if __name__ == "__main__":
    validate()
