#!/usr/bin/env python3
"""Validate the fail-closed Phase 1 release-critical workflow registry."""

import copy
import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-workflow-coverage.json"
)
INVENTORY_PATH = ROOT / "reference" / "PHASE1_INVENTORY.md"
TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "recorded_on",
    "status",
    "phase",
    "scope",
    "source_state",
    "policy",
    "workflows",
    "phase1_gate",
}
SOURCE_EXPECTATIONS = {
    "b14": {
        "path": "AdvancedTurnout.FCMacro",
        "version_token": "10.2A8A7B14",
        "sha256": (
            "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
        ),
        "role": "immutable legacy comparison oracle",
    },
    "b15": {
        "path": (
            "model_railway_curve_template_multitrack_v10_2a8a7b15_"
            "chair_performance_and_representation.FCMacro"
        ),
        "version_token": "10.2A8A7B15",
        "sha256": (
            "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
        ),
        "role": "accepted behavioural reference",
    },
}
EXPECTED_WORKFLOW_IDS = (
    "curve-easement-create-edit",
    "straight-stationing",
    "multiple-track-spacing",
    "standalone-turnout",
    "crossover-geometry",
    "automatic-timbering",
    "chair-analysis-presentation",
    "legacy-supported-chair-bodies",
    "procedural-chair-definitions",
    "assisted-chair-assimilation",
    "host-integration",
    "save-reopen",
    "production-export-manifests",
    "failure-recovery",
)
BLOCKED_WORKFLOW_IDS = {
    "procedural-chair-definitions",
    "assisted-chair-assimilation",
}
CLASSIFICATIONS = {
    "current-and-successor",
    "legacy-reference-only",
    "successor-only",
    "cross-cutting",
}
ORACLE_STATES = {"bounded-executed", "defined-blocked"}
SCOPE_FIELDS = {
    "purpose",
    "bounded_claim",
    "product_effect",
    "duplication_rule",
    "terminology",
}
POLICY_FIELDS = {
    "inventory_owner",
    "inventory_heading",
    "coverage_rule",
    "oracle_rule",
    "gap_rule",
    "evidence_rule",
    "phase_rule",
}
WORKFLOW_FIELDS = {
    "workflow_id",
    "inventory_title",
    "classification",
    "owner_role",
    "oracle",
    "gap_control",
}
ORACLE_FIELDS = {
    "state",
    "definition",
    "evidence_paths",
    "recipe_paths",
    "validation_paths",
}
GAP_FIELDS = {
    "summary",
    "owner_role",
    "closure_phases",
    "closure_gate",
}
GATE_FIELDS = {
    "exit_condition",
    "assessment",
    "workflow_count",
    "bounded_executed_count",
    "defined_blocked_count",
    "open_gap_count",
    "claim",
    "non_claim",
    "phase_effect",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _inventory_workflow_rows(text, heading, errors):
    start = text.find(heading)
    if start < 0:
        errors.append("workflow inventory heading is missing")
        return {}
    body = text[start + len(heading):]
    next_heading = re.search(r"^## ", body, re.MULTILINE)
    if next_heading is not None:
        body = body[:next_heading.start()]

    result = {}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) != 4:
            continue
        title = cells[0]
        if title in {"Workflow family", "---"}:
            continue
        if title in result:
            errors.append("workflow inventory contains duplicate {!r}".format(title))
        if not all(_non_empty_text(cell) for cell in cells):
            errors.append("workflow inventory row {!r} is incomplete".format(title))
        result[title] = cells[1:]
    return result


def _safe_repository_file(relative_path, label, errors, check_paths):
    if not _non_empty_text(relative_path):
        errors.append("{} contains an empty path".format(label))
        return
    path = pathlib.PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or str(path) != relative_path:
        errors.append("{} path {!r} is not repository-relative".format(
            label, relative_path
        ))
        return
    if check_paths and not (ROOT / relative_path).is_file():
        errors.append("{} path {!r} does not exist".format(label, relative_path))


def _validate_path_list(value, label, errors, check_paths):
    if not isinstance(value, list) or not value:
        errors.append("{} must be a non-empty list".format(label))
        return
    if len(value) != len(set(value)):
        errors.append("{} contains duplicate paths".format(label))
    for relative_path in value:
        _safe_repository_file(relative_path, label, errors, check_paths)


def validate_contract(document, inventory_text, check_paths=True):
    errors = []
    if not isinstance(document, dict):
        return ["workflow coverage contract must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("workflow coverage top-level fields are invalid")

    exact_root = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:workflow-coverage:1",
        "recorded_on": "2026-07-22",
        "status": "all-release-critical-workflows-owned-oracle-defined-gaps-scheduled",
        "phase": 1,
    }
    for field, expected in exact_root.items():
        if document.get(field) != expected:
            errors.append("workflow coverage {} is invalid".format(field))

    scope = document.get("scope")
    if not isinstance(scope, dict) or set(scope) != SCOPE_FIELDS:
        errors.append("workflow coverage scope fields are invalid")
    elif not all(_non_empty_text(value) for value in scope.values()):
        errors.append("workflow coverage scope contains empty text")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or source_state != SOURCE_EXPECTATIONS:
        errors.append("workflow coverage source_state is invalid")
    elif check_paths:
        for source_id, expected in SOURCE_EXPECTATIONS.items():
            source_path = ROOT / expected["path"]
            if _sha256(source_path) != expected["sha256"]:
                errors.append("{} source fingerprint changed".format(source_id))
            if expected["version_token"] not in source_path.read_text(
                encoding="utf-8"
            ):
                errors.append("{} version token is missing".format(source_id))

    policy = document.get("policy")
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS:
        errors.append("workflow coverage policy fields are invalid")
        policy = {}
    elif not all(_non_empty_text(value) for value in policy.values()):
        errors.append("workflow coverage policy contains empty text")
    if policy.get("inventory_owner") != "reference/PHASE1_INVENTORY.md":
        errors.append("workflow inventory owner is invalid")
    heading = policy.get("inventory_heading")
    if heading != "## Release-critical workflow coverage inventory":
        errors.append("workflow inventory heading contract is invalid")

    inventory_rows = _inventory_workflow_rows(
        inventory_text, heading if _non_empty_text(heading) else "", errors
    )
    workflows = document.get("workflows")
    if not isinstance(workflows, list):
        errors.append("workflows must be a list")
        workflows = []
    workflow_map = {}
    for index, workflow in enumerate(workflows):
        label = "workflow[{}]".format(index)
        if not isinstance(workflow, dict) or set(workflow) != WORKFLOW_FIELDS:
            errors.append("{} fields are invalid".format(label))
            continue
        workflow_id = workflow.get("workflow_id")
        if not _non_empty_text(workflow_id):
            errors.append("{} has no workflow_id".format(label))
            continue
        if workflow_id in workflow_map:
            errors.append("duplicate workflow_id {!r}".format(workflow_id))
        workflow_map[workflow_id] = workflow

        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", workflow_id):
            errors.append("{} workflow_id format is invalid".format(workflow_id))
        if not _non_empty_text(workflow.get("inventory_title")):
            errors.append("{} has no inventory title".format(workflow_id))
        classification = workflow.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append("{} classification is invalid".format(workflow_id))
        if not _non_empty_text(workflow.get("owner_role")):
            errors.append("{} has no owner role".format(workflow_id))

        oracle = workflow.get("oracle")
        oracle_record = oracle if isinstance(oracle, dict) else {}
        if not isinstance(oracle, dict) or set(oracle) != ORACLE_FIELDS:
            errors.append("{} oracle fields are invalid".format(workflow_id))
        else:
            state = oracle.get("state")
            if state not in ORACLE_STATES:
                errors.append("{} oracle state is invalid".format(workflow_id))
            if not _non_empty_text(oracle.get("definition")):
                errors.append("{} oracle definition is empty".format(workflow_id))
            for field in ("evidence_paths", "recipe_paths", "validation_paths"):
                _validate_path_list(
                    oracle.get(field),
                    "{} {}".format(workflow_id, field),
                    errors,
                    check_paths,
                )
            if oracle.get("state") == "bounded-executed":
                recipes = oracle.get("recipe_paths") or []
                if not any(path.startswith("tools/") for path in recipes):
                    errors.append(
                        "{} executed oracle has no tool/recipe path".format(workflow_id)
                    )
            if (classification == "successor-only") != (
                state == "defined-blocked"
            ):
                errors.append(
                    "{} successor/blocker classification is inconsistent".format(
                        workflow_id
                    )
                )

        gap = workflow.get("gap_control")
        gap_record = gap if isinstance(gap, dict) else {}
        if not isinstance(gap, dict) or set(gap) != GAP_FIELDS:
            errors.append("{} gap-control fields are invalid".format(workflow_id))
        else:
            for field in ("summary", "owner_role", "closure_gate"):
                if not _non_empty_text(gap.get(field)):
                    errors.append("{} gap {} is empty".format(workflow_id, field))
            phases = gap.get("closure_phases")
            if (
                not isinstance(phases, list)
                or not phases
                or any(
                    not isinstance(phase, int) or phase < 2 or phase > 11
                    for phase in phases
                )
                or phases != sorted(set(phases))
            ):
                errors.append("{} closure phases are invalid".format(workflow_id))

        living_text = " ".join(
            [
                str(workflow.get("inventory_title") or ""),
                str(workflow.get("owner_role") or ""),
                str(oracle_record.get("definition") or ""),
                str(gap_record.get("summary") or ""),
                str(gap_record.get("owner_role") or ""),
                str(gap_record.get("closure_gate") or ""),
            ]
        ).lower()
        if "ordinary track" in living_text or "ordinary-track" in living_text:
            errors.append("{} uses prohibited living terminology".format(workflow_id))

    if tuple(workflow_map) != EXPECTED_WORKFLOW_IDS:
        errors.append("workflow registry identity/order set is invalid")
    registered_titles = [
        workflow.get("inventory_title")
        for workflow in workflows
        if isinstance(workflow, dict)
    ]
    if len(registered_titles) != len(set(registered_titles)):
        errors.append("workflow registry contains duplicate inventory titles")
    if list(inventory_rows) != registered_titles:
        errors.append("Markdown workflow inventory and contract order/set differ")
    blocked_ids = {
        workflow_id
        for workflow_id, workflow in workflow_map.items()
        if isinstance(workflow.get("oracle"), dict)
        and workflow["oracle"].get("state") == "defined-blocked"
    }
    if blocked_ids != BLOCKED_WORKFLOW_IDS:
        errors.append("workflow blocked-oracle identity set is invalid")

    gate = document.get("phase1_gate")
    if not isinstance(gate, dict) or set(gate) != GATE_FIELDS:
        errors.append("workflow phase1_gate fields are invalid")
        gate = {}
    for field in ("exit_condition", "claim", "non_claim", "phase_effect"):
        if not _non_empty_text(gate.get(field)):
            errors.append("workflow phase1_gate {} is empty".format(field))
    bounded_count = sum(
        isinstance(workflow.get("oracle"), dict)
        and workflow["oracle"].get("state") == "bounded-executed"
        for workflow in workflow_map.values()
    )
    blocked_count = sum(
        isinstance(workflow.get("oracle"), dict)
        and workflow["oracle"].get("state") == "defined-blocked"
        for workflow in workflow_map.values()
    )
    expected_gate = {
        "assessment": "evidenced",
        "workflow_count": len(EXPECTED_WORKFLOW_IDS),
        "bounded_executed_count": (
            len(EXPECTED_WORKFLOW_IDS) - len(BLOCKED_WORKFLOW_IDS)
        ),
        "defined_blocked_count": len(BLOCKED_WORKFLOW_IDS),
        "open_gap_count": len(EXPECTED_WORKFLOW_IDS),
    }
    for field, expected in expected_gate.items():
        if gate.get(field) != expected:
            errors.append("workflow phase1_gate {} count/state drifted".format(field))
    if (
        len(workflow_map) != len(EXPECTED_WORKFLOW_IDS)
        or bounded_count != expected_gate["bounded_executed_count"]
        or blocked_count != expected_gate["defined_blocked_count"]
    ):
        errors.append("derived workflow state counts are invalid")
    if gate.get("exit_condition") != (
        "Every release-critical workflow has an owner document/recipe, known "
        "oracle, and stated coverage gap."
    ):
        errors.append("workflow Phase 1 exit-condition wording drifted")
    if gate.get("phase_effect") != (
        "This supplied evidence for the first Phase 1 exit condition. The "
        "project owner accepted the complete Phase 1 closeout on 2026-07-22; "
        "all 14 open workflow gaps remain mandatory at their named later gates."
    ):
        errors.append("workflow Phase 1 acceptance/later-gate boundary drifted")

    return errors


def _expect_invalid(document, inventory_text, label):
    if not validate_contract(document, inventory_text, check_paths=False):
        raise AssertionError("mutation unexpectedly passed: {}".format(label))


def main():
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    inventory_text = INVENTORY_PATH.read_text(encoding="utf-8")
    errors = validate_contract(document, inventory_text)
    if errors:
        raise AssertionError("\n".join(errors))

    missing_workflow = copy.deepcopy(document)
    missing_workflow["workflows"].pop()
    _expect_invalid(missing_workflow, inventory_text, "missing workflow")

    promoted_blocker = copy.deepcopy(document)
    next(
        workflow
        for workflow in promoted_blocker["workflows"]
        if workflow["workflow_id"] == "assisted-chair-assimilation"
    )["oracle"]["state"] = "bounded-executed"
    _expect_invalid(promoted_blocker, inventory_text, "unsupported blocker promotion")

    missing_gap = copy.deepcopy(document)
    missing_gap["workflows"][0]["gap_control"]["summary"] = ""
    _expect_invalid(missing_gap, inventory_text, "missing gap")

    missing_evidence = copy.deepcopy(document)
    missing_evidence["workflows"][0]["oracle"]["evidence_paths"] = []
    _expect_invalid(missing_evidence, inventory_text, "missing evidence")

    drifted_count = copy.deepcopy(document)
    drifted_count["phase1_gate"]["workflow_count"] += 1
    _expect_invalid(drifted_count, inventory_text, "drifted gate count")

    print("Phase 1 workflow coverage validation passed")


if __name__ == "__main__":
    main()
