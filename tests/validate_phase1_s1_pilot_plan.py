#!/usr/bin/env python3
"""Validate the owner-accepted, deliberately blocked Phase 1 S1 pilot plan."""

import copy
import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_dependency_manifest as manifest_validator  # noqa: E402


PLAN_PATH = ROOT / "reference" / "S1_PILOT_PLAN.md"
MANIFEST_PATH = (
    ROOT / "reference" / "manifests" / "s1-chair-pilot.dependency-manifest.json"
)
LINEAGE_PATH = ROOT / "reference" / "lineage" / "phase1-s1-core-lineage.json"
ORACLE_PATH = ROOT / "reference" / "oracles" / "templot5-556b-s1-oracle.json"
SOURCE_EXPECTATIONS = {
    "AdvancedTurnout.FCMacro": (
        "10.2A8A7B14",
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): (
        "10.2A8A7B15",
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
    ),
}
DECISION_STATES = {
    "S1-01": "accepted-direction",
    "S1-02": "accepted-direction",
    "S1-03": "accepted-direction",
    "S1-04": "accepted-direction",
    "S1-05": "accepted-direction",
    "S1-06": "accepted-direction",
    "S1-07": "owner-decision-required",
    "S1-08": "owner-decision-required",
    "S1-09": "owner-decision-required",
    "S1-10": "owner-decision-required",
    "S1-11": "owner-decision-required",
    "S1-12": "blocked-evidence",
    "S1-13": "owner-decision-required",
    "S1-14": "blocked-evidence",
    "S1-15": "owner-decision-required",
}
INTENDED_USES = (
    "public-redistribution",
    "commercial-production",
    "publication",
    "physical-production",
)
REQUIRED_MARKERS = (
    "Status: **Accepted Phase 1 control; production definition and pilot remain",
    "authoritative interchange is a neutral, versioned TrackTemplateMacro",
    "Serialised output-affecting numbers use exact decimal strings",
    "`+X` longitudinally along the nominal rail direction",
    "`+Y` from the gauge side towards the field side",
    "`+Z` upwards from the base mounting plane",
    "validate the complete package before creating geometry",
    "reject unsupported future schema versions",
    "leave the document and filesystem unchanged",
    "a precise prototype/company/standard designation",
    "A scan or CAD body may assist fitting, but cannot alone",
    "Phase 1 fixes the metric families, not unsupported numerical limits",
    "Mesh hash, face order, visual similarity or a low aggregate surface residual",
    "do not publish “LMS”, “REA” or another attribution by assumption",
    "Target CC0-1.0 only if the project controls the complete package rights",
    "The project owner explicitly accepted this plan on 2026-07-22",
    "> I accept S1_PILOT_PLAN.md as the blocked Phase 1 control, including S1-04",
    "> S1-15 remain blocked pending their stated evidence and decisions.",
    "no S1 production definition, project-cleared package or permission from a",
    "manifest cannot substitute for the recorded owner acceptance",
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _decision_rows(text, errors):
    start_marker = "## Decision register"
    finish_marker = "## Phase 1 acceptance boundary"
    start = text.find(start_marker)
    finish = text.find(finish_marker, start + len(start_marker))
    if start < 0 or finish < 0:
        errors.append("S1 decision-register boundary is missing")
        return []
    rows = []
    for line in text[start:finish].splitlines():
        if not line.startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) != 5 or cells[0] in {"ID", "---"}:
            continue
        rows.append(cells)
    return rows


def _all_reviews_have_status(review, status):
    return (
        isinstance(review, dict)
        and set(review) == set(manifest_validator.NON_COPYRIGHT_AREAS)
        and all(item.get("status") == status for item in review.values())
    )


def validate_plan(
    text,
    manifest,
    lineage,
    oracle,
    check_repository=True,
):
    errors = []
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append("S1 pilot plan marker is missing: {}".format(marker))

    rows = _decision_rows(text, errors)
    row_ids = [row[0] for row in rows]
    if row_ids != list(DECISION_STATES):
        errors.append("S1 decision identities/order are invalid")
    if len(row_ids) != len(set(row_ids)):
        errors.append("S1 decision identities are duplicated")
    for row in rows:
        if not all(cell for cell in row):
            errors.append("S1 decision {} contains an empty cell".format(row[0]))
        expected_state = DECISION_STATES.get(row[0])
        if row[2] != expected_state:
            errors.append("S1 decision {} state is invalid".format(row[0]))

    if "Status: **Project-cleared" in text:
        errors.append("S1 pilot plan falsely claims project clearance")
    lowered_text = text.lower()
    if "full-size millimetres" not in lowered_text:
        errors.append("S1 plan does not state its recommended canonical length unit")
    if "original decimal value and unit" not in lowered_text:
        errors.append("S1 plan does not preserve source quantities")

    manifest_errors = manifest_validator.validate_document(manifest)
    if manifest_errors:
        errors.extend("S1 manifest: {}".format(item) for item in manifest_errors)
    strict_errors = manifest_validator.validate_document(
        manifest, require_project_cleared=True
    )
    if not any("rather than project-cleared" in item for item in strict_errors):
        errors.append("S1 manifest no longer fails the strict project-cleared gate")

    subject = manifest.get("subject") if isinstance(manifest, dict) else {}
    if not isinstance(subject, dict):
        subject = {}
    if subject.get("identifier") != "tracktemplate:s1-chair-pilot":
        errors.append("S1 manifest subject identity drifted")
    if subject.get("version") != "0-unresolved":
        errors.append("S1 manifest prematurely received a package version")
    if subject.get("package_license") != "NOASSERTION":
        errors.append("S1 manifest prematurely received a package licence")
    if tuple(manifest.get("intended_uses") or []) != INTENDED_USES:
        errors.append("S1 intended-use declaration drifted")
    project_status = manifest.get("project_status") or {}
    if project_status.get("status") != "unknown":
        errors.append(
            "S1 manifest must remain unknown before final package/evidence review"
        )
    if (
        project_status.get("reviewed_on") != "2026-07-22"
        or project_status.get("reviewed_by")
        != "Project owner and Phase 1 inventory"
        or project_status.get("decision_reference")
        != "reference/lineage/phase1-s1-core-lineage.json"
        or "Phase 1 control plan is accepted"
        not in project_status.get("reason", "")
        or "final package acceptance" not in project_status.get("reason", "")
    ):
        errors.append("S1 manifest does not preserve the accepted-plan boundary")
    if not _all_reviews_have_status(
        manifest.get("non_copyright_review"), "not-performed"
    ):
        errors.append("S1 package rights reviews were promoted without evidence")

    dependencies = manifest.get("dependencies")
    if not isinstance(dependencies, list):
        dependencies = []
    dependency_map = {
        item.get("identifier"): item
        for item in dependencies
        if isinstance(item, dict)
    }
    if set(dependency_map) != {
        "s1-primary-evidence-unselected",
        "templot5-556b-local-comparison",
    }:
        errors.append("S1 manifest dependency identity set drifted")
    primary = dependency_map.get("s1-primary-evidence-unselected", {})
    if (
        primary.get("role") != "production-input"
        or primary.get("output_affecting") is not True
        or primary.get("license_expression") != "NOASSERTION"
        or (primary.get("project_status") or {}).get("status") != "unknown"
        or set((primary.get("permissions") or {}).values()) != {"unknown"}
        or not _all_reviews_have_status(
            primary.get("non_copyright_review"), "not-performed"
        )
    ):
        errors.append("unselected primary S1 evidence is not fail-closed")
    comparison = dependency_map.get("templot5-556b-local-comparison", {})
    if (
        comparison.get("role") != "comparison-only"
        or comparison.get("output_affecting") is not False
        or (comparison.get("project_status") or {}).get("status")
        != "reference-only"
    ):
        errors.append("Templot S1 evidence escaped its comparison-only boundary")

    if lineage.get("status") != "blocked":
        errors.append("first-S1/core lineage register is not blocked")
    if tuple(lineage.get("intended_uses") or []) != INTENDED_USES:
        errors.append("S1 plan and lineage intended uses differ")
    scopes = lineage.get("scopes")
    if not isinstance(scopes, list) or not scopes:
        errors.append("first-S1/core lineage scopes are missing")
        scopes = []
    if any(scope.get("status") != "blocked" for scope in scopes):
        errors.append("an S1/core lineage scope was promoted without evidence")
    for scope in scopes:
        for entry in scope.get("entries") or []:
            if entry.get("current_project_status") == "project-cleared":
                errors.append("an S1/core lineage entry was prematurely cleared")

    if oracle.get("status") != "blocked":
        errors.append("Templot 556b S1 oracle is not blocked")
    if oracle.get("permitted_role") != "local comparison oracle only":
        errors.append("Templot 556b S1 oracle role drifted")
    blockers = oracle.get("blockers")
    if not isinstance(blockers, list) or len(blockers) != 4:
        errors.append("Templot 556b S1 blocker set drifted")
    elif any(item.get("status") != "open" for item in blockers):
        errors.append("Templot 556b S1 blocker closed without capture evidence")
    acceptance_gate = oracle.get("acceptance_gate") or {}
    if (
        acceptance_gate.get("status") != "blocked"
        or acceptance_gate.get("canonical_production_input") is not False
        or acceptance_gate.get("raw_hash_equality_is_geometry_oracle") is not False
    ):
        errors.append("Templot 556b S1 acceptance gate weakened")

    if check_repository:
        for relative_path, (version, expected_digest) in SOURCE_EXPECTATIONS.items():
            path = ROOT / relative_path
            if _sha256(path) != expected_digest:
                errors.append("{} source fingerprint changed".format(relative_path))
            if version not in path.read_text(encoding="utf-8"):
                errors.append("{} version token is missing".format(relative_path))
        if (ROOT / "reference" / "schemas" / "chair-definition-v1.schema.json").exists():
            errors.append("production chair-definition schema appeared during Phase 1")

    return errors


def _expect_invalid(text, manifest, lineage, oracle, label):
    errors = validate_plan(
        text,
        manifest,
        lineage,
        oracle,
        check_repository=False,
    )
    if not errors:
        raise AssertionError("mutation unexpectedly passed: {}".format(label))


def main():
    text = PLAN_PATH.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    errors = validate_plan(text, manifest, lineage, oracle)
    if errors:
        raise AssertionError("\n".join(errors))

    promoted_decision = text.replace(
        "| S1-07 | Precise prototype designation | owner-decision-required |",
        "| S1-07 | Precise prototype designation | accepted-direction |",
        1,
    )
    _expect_invalid(
        promoted_decision, manifest, lineage, oracle, "unsupported designation"
    )

    licensed_manifest = copy.deepcopy(manifest)
    licensed_manifest["subject"]["package_license"] = "CC0-1.0"
    _expect_invalid(text, licensed_manifest, lineage, oracle, "premature licence")

    cleared_lineage = copy.deepcopy(lineage)
    cleared_lineage["scopes"][0]["entries"][0][
        "current_project_status"
    ] = "project-cleared"
    _expect_invalid(text, manifest, cleared_lineage, oracle, "premature lineage")

    output_comparison = copy.deepcopy(manifest)
    output_comparison["dependencies"][1]["output_affecting"] = True
    _expect_invalid(
        text, output_comparison, lineage, oracle, "output-affecting comparison"
    )

    weakened_oracle = copy.deepcopy(oracle)
    weakened_oracle["acceptance_gate"]["canonical_production_input"] = True
    _expect_invalid(text, manifest, lineage, weakened_oracle, "canonical Templot")

    print("Phase 1 S1 pilot plan validation passed")


if __name__ == "__main__":
    main()
