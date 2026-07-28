#!/usr/bin/env python3
"""Validate the compact project dashboard and fixed current-phase records."""

from __future__ import annotations

import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
EVIDENCE_PATH = ROOT / "reference" / "current" / "PHASE_EVIDENCE.md"
RISKS_PATH = ROOT / "reference" / "current" / "risks.json"
DECISIONS_PATH = ROOT / "reference" / "current" / "gate-decisions.json"
REDIRECT_PATH = (
    ROOT / "reference" / "phase-evidence" / "PHASE4_CANONICAL_STATE.md"
)
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

PHASE_TOTALS = {
    0: 6,
    1: 9,
    2: 5,
    3: 5,
    4: 6,
    5: 4,
    6: 5,
    7: 4,
    8: 4,
    9: 9,
    10: 5,
    11: 7,
}
EXPECTED_RISK_IDS = {
    *{"PR-{:02d}".format(value) for value in range(1, 23)},
    "QA-R03",
    "QA-R04",
    "QA-R05",
}
EXPECTED_DECISION_IDS = {
    "D-P4-001",
    "D-P4-002",
    "D-P4-003",
    "D-P4-004",
    "D-P4-005",
    "D-P4-006",
    "D-GOV-001",
    "D-GOV-002",
    "D-GOV-003",
    "D-P4-007",
}
ALLOWED_TREATMENTS = {"Tolerate", "Remove", "Mitigate"}
ALLOWED_SEVERITIES = {"Low", "Medium", "High", "Critical"}
ALLOWED_EFFECTIVENESS = {
    "Effective (current scope)",
    "Partial",
    "Not yet effective",
    "Ineffective",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _read(path: pathlib.Path) -> str:
    _require(path.is_file(), "missing required control: {}".format(path))
    return path.read_text(encoding="utf-8")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _section(text: str, heading: str) -> str:
    marker = "## " + heading
    _require(marker in text, "missing project-plan section: " + marker)
    tail = text.split(marker, 1)[1]
    next_heading = re.search(r"^## ", tail, re.MULTILINE)
    return tail if next_heading is None else tail[:next_heading.start()]


def _validate_plan_shape(plan: str) -> dict[int, dict[str, object]]:
    headings = re.findall(r"^#{1,2} .+$", plan, re.MULTILINE)
    _require(
        headings
        == [
            "# Project Plan",
            "## Phase status",
            "## Current Phase 4 exit conditions",
            "## Live risks",
            "## Owner decisions",
            "## Authority and evidence links",
        ],
        "PROJECT_PLAN.md contains an unsupported dashboard section",
    )
    _require(
        len(plan.splitlines()) <= 140,
        "PROJECT_PLAN.md exceeded its 140-line dashboard budget",
    )
    for forbidden in (
        "### Deliverables",
        "### Goal",
        "Slice definition of done",
        "Mandatory safety/risk panel",
        "Principal control assurance matrix",
        "QA audit risk log",
    ):
        _require(
            forbidden not in plan,
            "implementation/policy detail returned: " + forbidden,
        )
    _require(
        "current/PHASE_EVIDENCE.md" in plan,
        "project plan does not route to the fixed current evidence path",
    )
    _require(
        "phase-evidence/PHASE4_CANONICAL_STATE.md" not in plan,
        "project plan routes to the retired descriptive Phase 4 path",
    )

    rows: dict[int, dict[str, object]] = {}
    for line in _section(plan, "Phase status").splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        match = re.fullmatch(r"(\d+)/(\d+) evidenced", cells[2])
        _require(match is not None, "invalid phase exit status: " + cells[2])
        phase = int(cells[0])
        rows[phase] = {
            "evidenced": int(match.group(1)),
            "total": int(match.group(2)),
            "state": cells[3],
        }

    _require(set(rows) == set(PHASE_TOTALS), "project phase rows must be 0 through 11")
    for phase, total in PHASE_TOTALS.items():
        _require(rows[phase]["total"] == total, "phase total drifted: {}".format(phase))
    _require(rows[4]["evidenced"] == 4, "Phase 4 must show four evidenced exits")
    _require(
        str(rows[4]["state"]).startswith("Current"),
        "Phase 4 must be the sole current phase",
    )
    _require(
        all(
            phase == 4 or not str(row["state"]).startswith("Current")
            for phase, row in rows.items()
        ),
        "more than one phase is current",
    )
    _require(
        "bounded product implementation resumed" in plan.lower(),
        "the bounded owner resumption decision is missing",
    )
    return rows


def _validate_exit_conditions(plan: str, evidence: str) -> None:
    plan_states: list[str] = []
    for line in _section(plan, "Current Phase 4 exit conditions").splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) == 3 and cells[0] not in {"Exit condition", "---"}:
            plan_states.append(cells[1])

    evidence_section = evidence.split(
        "## Current Phase 4 exit-condition disposition",
        1,
    )[1]
    next_heading = evidence_section.find("\n## ")
    if next_heading >= 0:
        evidence_section = evidence_section[:next_heading]
    evidence_states: list[str] = []
    for line in evidence_section.splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) != 2 or cells[0] in {"Exit condition", "---"}:
            continue
        evidence_states.append(cells[1].split(":", 1)[0])

    expected = [
        "Evidenced",
        "Active",
        "Evidenced",
        "Pending",
        "Evidenced",
        "Evidenced",
    ]
    _require(plan_states == expected, "project-plan Phase 4 exit states drifted")
    _require(
        evidence_states == expected,
        "current-evidence Phase 4 exit states drifted",
    )
    _require(
        "Four of six Phase 4 exit conditions" in evidence,
        "current evidence summary count drifted",
    )


def _load_json(path: pathlib.Path) -> dict[str, object]:
    try:
        value = json.loads(_read(path))
    except json.JSONDecodeError as error:
        raise AssertionError("invalid JSON in {}".format(path)) from error
    _require(isinstance(value, dict), "{} must contain an object".format(path))
    return value


def _validate_risks(plan: str) -> None:
    document = _load_json(RISKS_PATH)
    _require(
        set(document) == {"schema_version", "current_phase", "updated_on", "risks"},
        "current risk-register fields changed",
    )
    _require(document["schema_version"] == 1, "unsupported risk-register schema")
    _require(document["current_phase"] == 4, "risk register is not for Phase 4")
    records = document["risks"]
    _require(isinstance(records, list), "risks must be a list")

    expected_fields = {
        "id",
        "severity",
        "state",
        "treatment",
        "control_effectiveness",
        "summary",
        "owner",
        "deadline",
        "required_work",
        "closure_evidence",
    }
    by_id: dict[str, dict[str, object]] = {}
    for record in records:
        _require(isinstance(record, dict), "each risk must be an object")
        _require(set(record) == expected_fields, "risk fields changed")
        risk_id = record["id"]
        _require(isinstance(risk_id, str) and risk_id not in by_id, "duplicate risk ID")
        _require(record["state"] == "Open", "closed risk retained in live register")
        _require(record["severity"] in ALLOWED_SEVERITIES, "invalid risk severity")
        _require(record["treatment"] in ALLOWED_TREATMENTS, "invalid risk treatment")
        _require(
            record["control_effectiveness"] in ALLOWED_EFFECTIVENESS,
            "invalid control effectiveness",
        )
        for field in (
            "summary",
            "owner",
            "deadline",
            "required_work",
            "closure_evidence",
        ):
            _require(
                isinstance(record[field], str) and bool(record[field].strip()),
                "{} lacks {}".format(risk_id, field),
            )
        _require(
            "Phase " in record["deadline"],
            "{} lacks a phase deadline".format(risk_id),
        )
        by_id[risk_id] = record

    _require(set(by_id) == EXPECTED_RISK_IDS, "live risk IDs drifted")
    _require(
        "Level 3" in str(by_id["PR-22"]["required_work"]),
        "PR-22 does not enforce Level 3 panel scope",
    )
    plan_ids = set(
        re.findall(
            r"^\| (PR-\d{2}|QA-R\d{2}) \|",
            _section(plan, "Live risks"),
            re.MULTILINE,
        )
    )
    _require(
        plan_ids == set(by_id),
        "project-plan risk summary differs from risks.json",
    )


def _validate_decisions(plan: str) -> None:
    document = _load_json(DECISIONS_PATH)
    _require(
        set(document)
        == {"schema_version", "current_phase", "updated_on", "decisions"},
        "current decision-register fields changed",
    )
    _require(document["schema_version"] == 1, "unsupported decision schema")
    _require(document["current_phase"] == 4, "decision register is not for Phase 4")
    records = document["decisions"]
    _require(isinstance(records, list), "decisions must be a list")
    expected_fields = {
        "id",
        "decided_on",
        "status",
        "decision",
        "authority",
        "exclusions",
        "evidence",
        "panel_required_under_current_policy",
        "panel_record",
    }
    by_id: dict[str, dict[str, object]] = {}
    for record in records:
        _require(isinstance(record, dict), "each decision must be an object")
        _require(set(record) == expected_fields, "decision fields changed")
        decision_id = record["id"]
        _require(
            isinstance(decision_id, str) and decision_id not in by_id,
            "duplicate decision ID",
        )
        _require(record["status"] == "Accepted", "unaccepted decision in live summary")
        _require(
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(record["decided_on"])) is not None,
            "decision date is not ISO formatted",
        )
        for field in ("decision", "authority", "exclusions", "evidence"):
            _require(
                isinstance(record[field], str) and bool(record[field].strip()),
                "{} lacks {}".format(decision_id, field),
            )
        evidence_path = ROOT / str(record["evidence"]).split("#", 1)[0]
        _require(evidence_path.is_file(), "decision evidence path is missing")
        panel_required = record["panel_required_under_current_policy"]
        _require(isinstance(panel_required, bool), "panel requirement must be boolean")
        if panel_required:
            _require(
                isinstance(record["panel_record"], str)
                and bool(record["panel_record"].strip()),
                "required panel record is missing",
            )
        panel_record = record["panel_record"]
        if isinstance(panel_record, str):
            panel_path_text, separator, anchor = panel_record.partition("#")
            panel_path = ROOT / panel_path_text
            _require(panel_path.is_file(), "panel record path is missing")
            if separator:
                _require(
                    'id="{}"'.format(anchor) in _read(panel_path),
                    "panel record anchor is missing",
                )
        by_id[decision_id] = record

    _require(set(by_id) == EXPECTED_DECISION_IDS, "current decision IDs drifted")
    _require(
        by_id["D-P4-005"]["panel_required_under_current_policy"] is True,
        "supported-migration decision lost its panel requirement",
    )
    _require(
        by_id["D-GOV-002"]["panel_required_under_current_policy"] is True,
        "three-level governance decision lost its panel requirement",
    )
    _require(
        by_id["D-GOV-003"]["panel_required_under_current_policy"] is True,
        "CI enforcement decision lost its panel requirement",
    )
    _require(
        by_id["D-P4-007"]["panel_required_under_current_policy"] is True,
        "bounded Phase 4 resumption lost its panel requirement",
    )
    _require(
        by_id["D-P4-003"]["panel_required_under_current_policy"] is False,
        "development-only route retirement became a Level 3 gate",
    )
    plan_ids = set(
        re.findall(
            r"^\| (D-[A-Z0-9-]+) \|",
            _section(plan, "Owner decisions"),
            re.MULTILINE,
        )
    )
    _require(
        plan_ids == set(by_id),
        "project-plan decisions differ from decisions.json",
    )


def _validate_fixed_paths() -> None:
    redirect = _read(REDIRECT_PATH)
    _require(
        "owns no live status or evidence" in redirect,
        "old Phase 4 path is not retired",
    )
    _require(
        "../current/PHASE_EVIDENCE.md" in redirect,
        "old Phase 4 path does not redirect to the fixed current record",
    )


def _validate_ci_workflow() -> None:
    workflow = _read(CI_PATH)
    _require("pull_request_target:" not in workflow, "unsafe CI trigger is enabled")
    _require("permissions:\n  contents: read" in workflow, "CI lacks least permissions")
    _require("persist-credentials: false" in workflow, "checkout credentials persist")
    _require("tools/validate_python_syntax.py" in workflow, "CI omits syntax parsing")
    _require(
        "tools/run_standalone_validators.py --profile ci" in workflow,
        "CI omits the explicit clean-checkout standalone matrix",
    )
    pins = re.findall(r"uses: actions/[a-z-]+@([0-9a-f]{40})", workflow)
    _require(len(pins) == 2, "official CI actions must be pinned to two full SHAs")
    _require("timeout-minutes:" in workflow, "CI job lacks a timeout")


def main() -> None:
    plan = _read(PLAN_PATH)
    evidence = _read(EVIDENCE_PATH)
    _validate_plan_shape(plan)
    _validate_exit_conditions(plan, evidence)
    _validate_risks(plan)
    _validate_decisions(plan)
    _validate_fixed_paths()
    _validate_ci_workflow()
    print("Project dashboard and current-record validation passed")


if __name__ == "__main__":
    main()
