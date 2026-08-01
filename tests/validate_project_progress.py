#!/usr/bin/env python3
"""Validate the compact dashboard, frozen closeouts, and current records."""

from __future__ import annotations

import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
CURRENT_EVIDENCE_PATH = ROOT / "reference" / "current" / "PHASE_EVIDENCE.md"
RISKS_PATH = ROOT / "reference" / "current" / "risks.json"
CURRENT_DECISIONS_PATH = (
    ROOT / "reference" / "current" / "gate-decisions.json"
)
PHASE4_CLOSEOUT_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE4_CLOSEOUT.md"
)
PHASE4_RISKS_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE4_RISKS.json"
)
PHASE4_DECISIONS_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE4_GATE_DECISIONS.json"
)
PHASE5_CLOSEOUT_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE5_CLOSEOUT.md"
)
PHASE5_RISKS_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE5_RISKS.json"
)
PHASE5_DECISIONS_PATH = (
    ROOT
    / "reference"
    / "history"
    / "phase-closeouts"
    / "PHASE5_GATE_DECISIONS.json"
)
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
    *{
        "PR-{:02d}".format(value)
        for value in range(1, 23)
        if value != 14
    },
    "QA-R03",
    "QA-R04",
    "QA-R05",
}
EXPECTED_PHASE4_DECISION_IDS = {
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
    "D-P4-008",
    "D-P4-009",
}
EXPECTED_PHASE5_DECISION_IDS = {
    "D-P5-001",
    "D-GOV-004",
    "D-P5-002",
    "D-P5-003",
}
EXPECTED_PHASE6_DECISION_IDS = {"D-P6-001"}
EXPECTED_PHASE6_AUTHORITY = (
    "At source state `35d4124c28d6be7e536a5f3773681ff0bf243283`, "
    "open Phase 6 at 0/5 for bounded exact-validation and export-seam work "
    "on the accepted B16 Entry/Exit transition slice. Separate Level 2 "
    "tranches may establish the exact artifact/oracle and contracts, "
    "complete stage signatures and invalidation, transient exact geometry "
    "in disposable FreeCAD scope, private-development target-format export "
    "with atomic staging and rollback, and complete edit/Validate/Export "
    "performance evidence."
)
EXPECTED_PHASE6_EXCLUSIONS = (
    "No Phase 6 exit, production-output clearance, `project-cleared` status, "
    "operator or migration route, whole-layout or complete B14 export port, "
    "persisted-schema change, retained production shape, legacy-oracle "
    "retirement, numerical performance budget, new runtime dependency, "
    "packaging, release, or later-phase authority is accepted. Any required "
    "manifest-schema change receives separate API, licensing, validation, "
    "and owner review."
)
EXPECTED_CONTINUATION_DECISION = (
    "Authorise explicit repository-driven continuation cycles."
)
EXPECTED_CONTINUATION_AUTHORITY = (
    "Only an explicit project-owner invocation containing the literal "
    "`$tracktemplate-continue` command starts one cycle. That cycle may "
    "integrate one previous exact-green authorised Level 1 or Level 2 pull "
    "request, synchronise protected main in every path, reconstruct canonical "
    "repository authority, classify candidates, select and deliver one "
    "highest-value worthwhile authorised Level 1 or Level 2 outcome or stop "
    "cleanly, use the bounded chief-of-staff and technical-lead workflows where "
    "applicable, validate and obtain separate read-only staff review, repair "
    "BLOCKER findings only through at most two shared repair-and-review passes "
    "with affected final validation and a new separate read-only review after "
    "every repair, delegate only review-frozen publication of the exact "
    "final-reviewed source, and publish one exact-green draft pull request "
    "before stopping with a plain-English owner acceptance pack."
)
EXPECTED_CONTINUATION_EXCLUSIONS = (
    "Natural-language equivalents do not invoke it. A next-tranche sentence, "
    "review finding, branch name, test expectation or source shape is not "
    "authority; maintenance, governance/tooling and non-blocking review "
    "findings cannot nominate themselves as the next tranche. Delegated "
    "publication has no independent source-edit or CI-repair authority. No "
    "Level 3 decision, renderer or phase acceptance, migration support, "
    "production output or chair clearance, release or tagging, protection "
    "bypass, force push, history rewrite, destructive reset or restore, git "
    "clean, branch deletion, destructive operation, unresolved product choice "
    "or same-invocation readying or merge of the newly published draft is "
    "authorised."
)
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
            "## Phase 6 exit conditions",
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
        "history/phase-closeouts/PHASE4_CLOSEOUT.md" in plan,
        "project plan does not route to the frozen Phase 4 closeout",
    )
    _require(
        "history/phase-closeouts/PHASE5_CLOSEOUT.md" in plan,
        "project plan does not route to the frozen Phase 5 closeout",
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
    _require(rows[4]["evidenced"] == 6, "Phase 4 must show six evidenced exits")
    _require(
        rows[4]["state"] == "Complete — accepted 2026-07-28",
        "Phase 4 must be closed with the accepted date",
    )
    _require(
        rows[5]["evidenced"] == 4
        and rows[5]["state"] == "Complete — accepted 2026-08-01",
        "Phase 5 must be closed with all four accepted exits",
    )
    _require(
        rows[6]["evidenced"] == 0
        and str(rows[6]["state"])
        == "Current — opened 2026-08-01",
        "Phase 6 must remain current at its accepted opening state",
    )
    _require(
        [
            phase
            for phase, row in rows.items()
            if str(row["state"]).startswith("Current")
        ]
        == [6],
        "the dashboard must identify only Phase 6 as current",
    )
    _require(
        "Phase 6 current" in plan
        and "opened at 0/5 under D-P6-001 on 2026-08-01"
        in " ".join(plan.split()),
        "the accepted Phase 6 opening status is missing",
    )
    return rows


def _validate_exit_conditions(
    plan: str,
    phase4_closeout: str,
    phase5_closeout: str,
    current_evidence: str,
) -> None:
    plan_states: list[str] = []
    for line in _section(plan, "Phase 6 exit conditions").splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) == 3 and cells[0] not in {"Exit condition", "---"}:
            plan_states.append(cells[1])

    phase4_section = phase4_closeout.split(
        "## Current Phase 4 exit-condition disposition",
        1,
    )[1]
    next_heading = phase4_section.find("\n## ")
    if next_heading >= 0:
        phase4_section = phase4_section[:next_heading]
    phase4_states: list[str] = []
    for line in phase4_section.splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) != 2 or cells[0] in {"Exit condition", "---"}:
            continue
        phase4_states.append(cells[1].split(":", 1)[0])

    expected_plan = ["Pending", "Pending", "Pending", "Pending", "Pending"]
    expected_phase4 = [
        "Evidenced",
        "Evidenced",
        "Evidenced",
        "Evidenced",
        "Evidenced",
        "Evidenced",
    ]
    _require(
        plan_states == expected_plan,
        "project-plan Phase 6 exit states drifted",
    )
    _require(
        phase4_states == expected_phase4,
        "frozen Phase 4 exit states drifted",
    )
    phase4_flat = " ".join(phase4_closeout.split())
    _require(
        "all six revised exit conditions" in phase4_flat.lower(),
        "frozen Phase 4 summary count drifted",
    )

    phase5_section = _section(
        phase5_closeout,
        "Final Phase 5 exit-condition disposition",
    )
    phase5_states: list[str] = []
    for line in phase5_section.splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) == 2 and cells[0] not in {"Exit condition", "---"}:
            phase5_states.append(cells[1])
    _require(
        phase5_states
        == [
            (
                "Accepted — Coin is selected for the demonstrated B16 "
                "Entry/Exit boundary using the retained correctness, editing, "
                "qualified FreeCAD, maintainability and descriptive "
                "2–32-object resource evidence"
            ),
            (
                "Accepted — one logical object and layer per transition, "
                "stable Entry/Exit identities and deterministic pointer "
                "mapping remain exact across the 2–32-object observations; "
                "no whole-layout claim is made"
            ),
            (
                "Accepted — edit, no-op, Undo/Redo, failure recovery and "
                "reopen retain compact objects and zero `Shape` properties "
                "without constructing exact `Part` geometry"
            ),
            (
                "Accepted — the owner explicitly accepts the demonstrated "
                "lifecycle and the confined one-empty-switch-child-per-object "
                "limitation at exact source commit "
                "`0f437f9de8c81f773a50e4b03c1ad6efd8a34169`"
            ),
        ],
        "frozen Phase 5 exit evidence drifted",
    )
    phase5_flat = " ".join(phase5_closeout.split())
    _require(
        "Closed — all 4/4 Phase 5 exits were accepted under D-P5-002 on "
        "2026-07-31, and Phase 5 was closed under D-P5-003 on 2026-08-01"
        in phase5_flat,
        "frozen Phase 5 closeout status drifted",
    )
    for anchor in (
        "phase-5-opening-panel",
        "phase-5-coin-renderer-and-editing-acceptance-panel",
        "phase-5-closeout-panel",
    ):
        _require(
            'id="{}"'.format(anchor) in phase5_closeout,
            "frozen Phase 5 panel is missing: " + anchor,
        )
    _require(
        "2026-08-01-phase5-closeout-01" in phase5_closeout
        and "QA-R01 remains closed" in phase5_closeout,
        "Phase 5 closeout backup condition is missing",
    )

    plan_flat = " ".join(plan.split())
    _require(
        "D-P5-002 accepted Coin and the demonstrated B16 Entry/Exit editing "
        "boundary, evidencing all four exact exits" in plan_flat,
        "accepted Phase 5 boundary is missing",
    )
    _require(
        "D-P5-003 closed Phase 5 without opening Phase 6" in plan_flat,
        "Phase 5 closeout boundary is missing",
    )
    _require(
        "D-P6-001 later opened Phase 6 at 0/5" in plan_flat
        and "bounded exact-validation and private-development export-seam "
        "work" in plan_flat,
        "Phase 6 opening boundary is missing",
    )

    current_flat = " ".join(current_evidence.split())
    decision_quote_flat = " ".join(
        " ".join(
            line[2:] if line.startswith("> ") else ""
            for line in current_evidence.splitlines()
            if line.startswith(">")
        ).split()
    )
    _require(
        "Current — opened at 0/5 under D-P6-001 on 2026-08-01. No Phase 6 "
        "exit is evidenced or accepted" in current_flat,
        "current record does not preserve the accepted Phase 6 opening state",
    )
    _require(
        "Phase 5 closeout" in current_evidence
        and "history/phase-closeouts/PHASE5_CLOSEOUT.md" in current_evidence,
        "current Phase 6 record does not link its frozen predecessor",
    )
    current_section = _section(
        current_evidence,
        "Current Phase 6 exit-condition disposition",
    )
    current_rows: list[list[str]] = []
    for line in current_section.splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) == 2 and cells[0] not in {"Exit condition", "---"}:
            current_rows.append(cells)
    _require(
        len(current_rows) == 5
        and [row[0] for row in current_rows]
        == [
            (
                "The selected slice has equivalent exact validation and "
                "production output for the agreed scope"
            ),
            "No transient production objects leak into the editable document",
            "Export is deterministic and failure-safe",
            (
                "Editing resource use improves beyond normal noise, with "
                "complete end-to-end cost accounted for"
            ),
            (
                "The legacy path remains available until parity and "
                "project-owner acceptance permit removal"
            ),
        ]
        and all(
            row[1] == "Pending — no Phase 6 evidence admitted"
            for row in current_rows
        ),
        "Phase 6 exits must remain five pending rows at opening",
    )
    _require(
        'id="phase-6-opening-panel"' in current_evidence
        and "Proceed with bounded conditions" in current_evidence
        and "I accept D-P6-001 exactly as presented" in current_evidence
        and EXPECTED_PHASE6_AUTHORITY in decision_quote_flat
        and EXPECTED_PHASE6_EXCLUSIONS in decision_quote_flat,
        "Phase 6 opening panel or exact owner acceptance is missing",
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
    phase5_document = _load_json(PHASE5_RISKS_PATH)
    phase4_document = _load_json(PHASE4_RISKS_PATH)
    _require(
        set(document) == {"schema_version", "current_phase", "updated_on", "risks"},
        "current risk-register fields changed",
    )
    _require(
        set(phase5_document)
        == {"schema_version", "current_phase", "updated_on", "risks"},
        "frozen Phase 5 risk-register fields changed",
    )
    _require(
        set(phase4_document)
        == {"schema_version", "current_phase", "updated_on", "risks"},
        "frozen Phase 4 risk-register fields changed",
    )
    _require(document["schema_version"] == 1, "unsupported risk-register schema")
    _require(
        phase5_document["schema_version"] == 1,
        "unsupported frozen Phase 5 risk-register schema",
    )
    _require(
        phase4_document["schema_version"] == 1,
        "unsupported frozen risk-register schema",
    )
    _require(
        document["current_phase"] == 6
        and document["updated_on"] == "2026-08-01",
        "risk register is not prepared for current Phase 6",
    )
    _require(
        phase5_document["current_phase"] == 5
        and phase5_document["updated_on"] == "2026-08-01",
        "frozen risk snapshot is not the Phase 5 closeout state",
    )
    _require(
        phase4_document["current_phase"] == 4,
        "frozen risk snapshot is not for Phase 4",
    )
    records = document["risks"]
    _require(isinstance(records, list), "risks must be a list")
    _require(
        phase5_document["risks"] == records,
        "Phase 5 risks did not carry unchanged into Phase 6",
    )

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
    for risk_id in ("PR-16", "PR-17", "QA-R03", "QA-R04"):
        _require(
            by_id[risk_id]["control_effectiveness"] == "Partial",
            "{} changed without Phase 5 evidence".format(risk_id),
        )
    for risk_id in ("PR-20", "PR-22"):
        _require(
            by_id[risk_id]["control_effectiveness"]
            == "Effective (current scope)",
            "{} lost the bounded opening control".format(risk_id),
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
    current_document = _load_json(CURRENT_DECISIONS_PATH)
    document = _load_json(PHASE5_DECISIONS_PATH)
    phase4_document = _load_json(PHASE4_DECISIONS_PATH)
    expected_document_fields = {
        "schema_version",
        "current_phase",
        "updated_on",
        "decisions",
    }
    _require(
        set(current_document) == expected_document_fields,
        "current decision-register fields changed",
    )
    _require(
        current_document["schema_version"] == 1,
        "unsupported current decision schema",
    )
    _require(
        current_document["current_phase"] == 6
        and current_document["updated_on"] == "2026-08-01",
        "current decision register is not for Phase 6",
    )
    _require(
        set(document) == expected_document_fields,
        "frozen Phase 5 decision-register fields changed",
    )
    _require(
        document["schema_version"] == 1
        and document["current_phase"] == 5
        and document["updated_on"] == "2026-08-01",
        "frozen decision register is not the Phase 5 closeout state",
    )
    _require(
        set(phase4_document) == expected_document_fields,
        "frozen Phase 4 decision-register fields changed",
    )
    _require(
        phase4_document["schema_version"] == 1
        and phase4_document["current_phase"] == 4,
        "frozen decision register is not for Phase 4",
    )
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
    phase6_records = current_document["decisions"]
    _require(
        isinstance(phase6_records, list)
        and len(phase6_records) == 1
        and isinstance(phase6_records[0], dict),
        "current decision register must contain exactly D-P6-001",
    )
    phase6_record = phase6_records[0]
    _require(
        set(phase6_record) == expected_fields,
        "D-P6-001 decision fields changed",
    )
    _require(
        phase6_record["id"] in EXPECTED_PHASE6_DECISION_IDS
        and phase6_record["decided_on"] == "2026-08-01"
        and phase6_record["status"] == "Accepted"
        and phase6_record["decision"] == "Open Phase 6."
        and phase6_record["authority"] == EXPECTED_PHASE6_AUTHORITY
        and phase6_record["exclusions"] == EXPECTED_PHASE6_EXCLUSIONS,
        "D-P6-001 authority or exclusions drifted",
    )
    phase6_panel = (
        "reference/current/PHASE_EVIDENCE.md#phase-6-opening-panel"
    )
    _require(
        phase6_record["evidence"] == phase6_panel
        and phase6_record["panel_required_under_current_policy"] is True
        and phase6_record["panel_record"] == phase6_panel,
        "D-P6-001 panel routing drifted",
    )
    panel_path_text, separator, panel_anchor = phase6_panel.partition("#")
    panel_path = ROOT / panel_path_text
    _require(panel_path.is_file(), "D-P6-001 panel record path is missing")
    _require(
        separator and 'id="{}"'.format(panel_anchor) in _read(panel_path),
        "D-P6-001 panel record anchor is missing",
    )
    current_records = document["decisions"]
    _require(
        isinstance(current_records, list),
        "Phase 5 decisions must be a list",
    )
    _require(
        len(current_records) == len(EXPECTED_PHASE5_DECISION_IDS)
        and all(isinstance(record, dict) for record in current_records),
        "Phase 5 decision register has an unexpected record count or shape",
    )
    current_by_id: dict[str, dict[str, object]] = {}
    for current_record in current_records:
        _require(
            set(current_record) == expected_fields,
            "current decision fields changed",
        )
        decision_id = current_record["id"]
        _require(
            isinstance(decision_id, str)
            and decision_id not in current_by_id,
            "duplicate current decision ID",
        )
        _require(
            current_record["status"] == "Accepted",
            "unaccepted current decision",
        )
        _require(
            re.fullmatch(
                r"\d{4}-\d{2}-\d{2}",
                str(current_record["decided_on"]),
            )
            is not None,
            "current decision date is not ISO formatted",
        )
        _require(
            current_record["panel_required_under_current_policy"] is True,
            "Phase 5 Level 3 decision lost its panel requirement",
        )
        for field in ("decision", "authority", "exclusions", "evidence"):
            _require(
                isinstance(current_record[field], str)
                and bool(current_record[field].strip()),
                "{} lacks {}".format(decision_id, field),
            )
        current_evidence_path = (
            ROOT / str(current_record["evidence"]).split("#", 1)[0]
        )
        _require(
            current_evidence_path.is_file(),
            "Phase 5 decision evidence path is missing",
        )
        _require(
            str(current_record["evidence"]).startswith(
                "reference/history/phase-closeouts/PHASE5_CLOSEOUT.md#"
            ),
            "Phase 5 decision does not route to its frozen closeout",
        )
        panel_path_text, separator, panel_anchor = str(
            current_record["panel_record"]
        ).partition("#")
        panel_path = ROOT / panel_path_text
        _require(panel_path.is_file(), "current panel record path is missing")
        _require(
            separator
            and 'id="{}"'.format(panel_anchor) in _read(panel_path),
            "current panel record anchor is missing",
        )
        current_by_id[decision_id] = current_record

    _require(
        set(current_by_id) == EXPECTED_PHASE5_DECISION_IDS,
        "Phase 5 decision IDs drifted",
    )
    opening_record = current_by_id["D-P5-001"]
    _require(
        "Phase 5 is open at 0/4" in str(opening_record["authority"])
        and "No renderer or exit is accepted"
        in str(opening_record["exclusions"]),
        "Phase 5 opening authority or exclusions drifted",
    )
    continuation_record = current_by_id["D-GOV-004"]
    _require(
        continuation_record["decision"] == EXPECTED_CONTINUATION_DECISION
        and continuation_record["authority"]
        == EXPECTED_CONTINUATION_AUTHORITY
        and continuation_record["exclusions"]
        == EXPECTED_CONTINUATION_EXCLUSIONS,
        "D-GOV-004 continuation authority or exclusions drifted",
    )
    renderer_record = current_by_id["D-P5-002"]
    _require(
        renderer_record["decision"]
        == (
            "Accept Coin and the demonstrated B16 Entry/Exit "
            "transition-editing behaviour."
        )
        and "0f437f9de8c81f773a50e4b03c1ad6efd8a34169"
        in str(renderer_record["authority"])
        and "All four exact Phase 5 exits are evidenced"
        in str(renderer_record["authority"])
        and "pending a separate closeout decision"
        in str(renderer_record["authority"])
        and "No automatic Addon startup"
        in str(renderer_record["exclusions"])
        and "Phase 5 closeout or Phase 6 opening"
        in str(renderer_record["exclusions"])
        and "Reopen this decision and PR-14"
        in str(renderer_record["exclusions"]),
        "D-P5-002 renderer authority or exclusions drifted",
    )
    closeout_record = current_by_id["D-P5-003"]
    _require(
        closeout_record["decision"] == "Close Phase 5."
        and "Phase 5 is closed at 4/4"
        in str(closeout_record["authority"])
        and "fixed-path Phase 6 administrative holding records are "
        "established at 0/5, "
        "Not started, unopened and unauthorised"
        in str(closeout_record["authority"])
        and "non-overwriting independent backup"
        in str(closeout_record["authority"])
        and "Phase 6 is not opened"
        in str(closeout_record["exclusions"])
        and "D-P5-002 and retired PR-14 reopen trigger"
        in str(closeout_record["exclusions"])
        and "does not authorise publication or merge"
        in str(closeout_record["exclusions"]),
        "D-P5-003 closeout authority or exclusions drifted",
    )

    records = phase4_document["decisions"]
    _require(isinstance(records, list), "decisions must be a list")
    by_id: dict[str, dict[str, object]] = {}
    for record in records:
        _require(isinstance(record, dict), "each decision must be an object")
        _require(set(record) == expected_fields, "decision fields changed")
        decision_id = record["id"]
        _require(
            isinstance(decision_id, str) and decision_id not in by_id,
            "duplicate decision ID",
        )
        _require(
            record["status"] == "Accepted",
            "unaccepted decision in frozen Phase 4 register",
        )
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

    _require(
        set(by_id) == EXPECTED_PHASE4_DECISION_IDS,
        "Phase 4 decision IDs drifted",
    )
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
        by_id["D-P4-008"]["panel_required_under_current_policy"] is True,
        "Phase 4 exit-ownership transfer lost its panel requirement",
    )
    _require(
        "6/6 evidenced" in str(by_id["D-P4-008"]["authority"])
        and "not closed" in str(by_id["D-P4-008"]["exclusions"]),
        "Phase 4 exit transfer lost its closeout boundary",
    )
    _require(
        by_id["D-P4-009"]["panel_required_under_current_policy"] is True,
        "Phase 4 closeout lost its panel requirement",
    )
    _require(
        "Phase 4 is complete" in str(by_id["D-P4-009"]["authority"])
        and "Phase 5 remains 0/4 and Not started"
        in str(by_id["D-P4-009"]["exclusions"]),
        "Phase 4 closeout lost its later-phase boundary",
    )
    _require(
        by_id["D-P4-003"]["panel_required_under_current_policy"] is False,
        "development-only route retirement became a Level 3 gate",
    )
    decision_section = _section(plan, "Owner decisions")
    decision_flat = " ".join(decision_section.split())
    _require(
        "history/phase-closeouts/PHASE4_GATE_DECISIONS.json"
        in decision_section,
        "Phase 4 decision summary does not route to the frozen register",
    )
    _require(
        "history/phase-closeouts/PHASE5_GATE_DECISIONS.json"
        in decision_section
        and "owns the displayed Phase 5 decisions" in decision_flat,
        "the frozen Phase 5 decision-register ownership is missing",
    )
    _require(
        "current decision register" in decision_flat
        and "owns Phase 6 decisions" in decision_flat,
        "the current Phase 6 decision-register ownership is missing",
    )
    plan_ids = set(
        re.findall(
            r"^\| (D-[A-Z0-9-]+) \|",
            decision_section,
            re.MULTILINE,
        )
    )
    _require(
        plan_ids
        == set(by_id)
        | EXPECTED_PHASE5_DECISION_IDS
        | EXPECTED_PHASE6_DECISION_IDS,
        "project-plan decisions differ from the frozen registers",
    )


def _validate_fixed_paths() -> None:
    redirect = _read(REDIRECT_PATH)
    _require(
        "owns no live status or evidence" in redirect,
        "old Phase 4 path is not retired",
    )
    _require(
        "../history/phase-closeouts/PHASE4_CLOSEOUT.md" in redirect,
        "old Phase 4 path does not redirect to the frozen closeout",
    )
    _require(
        "../current/PHASE_EVIDENCE.md" in redirect,
        "old Phase 4 path does not identify the fixed current record",
    )
    _require(
        "Phase 6 evidence record" in redirect,
        "old Phase 4 path does not identify the current Phase 6 record",
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
    current_evidence = _read(CURRENT_EVIDENCE_PATH)
    phase4_closeout = _read(PHASE4_CLOSEOUT_PATH)
    phase5_closeout = _read(PHASE5_CLOSEOUT_PATH)
    _validate_plan_shape(plan)
    _validate_exit_conditions(
        plan,
        phase4_closeout,
        phase5_closeout,
        current_evidence,
    )
    _validate_risks(plan)
    _validate_decisions(plan)
    _validate_fixed_paths()
    _validate_ci_workflow()
    print("Project dashboard and current-record validation passed")


if __name__ == "__main__":
    main()
