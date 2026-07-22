#!/usr/bin/env python3
"""Fail-closed repository QA-document and risk-linkage controls."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / "reference" / "QUALITY_ASSURANCE.md"
LEARNING = ROOT / "reference" / "LEARNING_FROM_EXPERIENCE.md"
PLAN = ROOT / "reference" / "PROJECT_PLAN.md"
AGENTS = ROOT / "AGENTS.md"

EXPECTED_IMMUTABLE_SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro":
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro":
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
RISK_ROW_RE = re.compile(r"^\|\s*(QA-R\d{2})\s*\|", re.MULTILINE)
FINDING_ROW_RE = re.compile(r"^\|\s*(QA-F\d{2})\s*\|([^\n]+)$", re.MULTILINE)
ACTION_ROW_RE = re.compile(r"^\|\s*(QA-A\d{2})\s*\|([^\n]+)$", re.MULTILINE)
ALLOWED_RISK_STATES = {"Open", "Closed"}
ALLOWED_RISK_TREATMENTS = {"Tolerate", "Remove", "Mitigate"}
ALLOWED_RISK_SEVERITIES = {"Low", "Medium", "High", "Critical"}
ALLOWED_CONTROL_EFFECTIVENESS = {
    "Effective (current scope)",
    "Partial",
    "Not yet effective",
    "Ineffective",
}
QA_RISK_TABLE_HEADERS = [
    "ID",
    "Severity",
    "State",
    "Treatment",
    "Residual finding and present boundary",
    "Accountable owner",
    "Target end-state and deadline",
    "Required resolution and objective closure evidence",
]
PRINCIPAL_RISK_TABLE_HEADERS = [
    "ID",
    "Severity",
    "State",
    "Treatment",
    "Principal risk",
    "Accountable owner",
    "Mandatory target",
]
PRINCIPAL_CONTROL_TABLE_HEADERS = [
    "ID",
    "Control measures",
    "Effectiveness",
    "Evidence, gap and required assurance",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required QA control: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def subsection(text: str, heading: str) -> str:
    marker = f"### {heading}"
    require(marker in text, f"missing section: {marker}")
    tail = text.split(marker, 1)[1]
    return re.split(r"\n#{2,3} ", tail, maxsplit=1)[0]


def markdown_documents() -> list[Path]:
    documents = list(ROOT.glob("*.md"))
    for base in (ROOT / "reference", ROOT / "tools", ROOT / "tests", ROOT / "tracktemplate"):
        if base.exists():
            documents.extend(base.rglob("*.md"))
    return sorted(set(documents))


def local_link_target(document: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("//"):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    require(not target.startswith("/"),
            f"non-portable absolute Markdown target in {document.relative_to(ROOT)}: {target}")
    resolved = (document.parent / target).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as error:
        raise AssertionError(
            f"repository-external Markdown target in {document.relative_to(ROOT)}: {target}"
        ) from error
    return resolved


def validate_links() -> None:
    broken: list[str] = []
    for document in markdown_documents():
        for raw_target in LINK_RE.findall(document.read_text(encoding="utf-8")):
            target = local_link_target(document, raw_target)
            if target is not None and not target.exists():
                broken.append(
                    f"{document.relative_to(ROOT)} -> {target.relative_to(ROOT)}"
                )
    require(not broken, "broken repository-internal Markdown targets:\n" + "\n".join(broken))


def controlled_table_rows(
    text: str,
    row_pattern: str,
    expected_headers: list[str],
    label: str,
) -> dict[str, list[str]]:
    header_lines = [
        line for line in text.splitlines()
        if line.startswith("| ID |")
    ]
    require(len(header_lines) == 1, f"{label} must have one controlled table header")
    headers = [cell.strip() for cell in header_lines[0].strip().strip("|").split("|")]
    require(headers == expected_headers, f"{label} fields changed: {headers}")

    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not re.match(row_pattern, line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(len(cells) == len(expected_headers),
                f"{label} row has the wrong controlled field count: {line}")
        row_id = cells[0]
        require(row_id not in rows, f"duplicate {label} ID: {row_id}")
        rows[row_id] = cells
    require(rows, f"{label} must contain controlled rows")
    return rows


def validate_treatment_fields(
    risk_id: str,
    severity: str,
    state: str,
    treatment: str,
    finding: str,
    owner: str,
    target: str,
) -> None:
    require(severity in ALLOWED_RISK_SEVERITIES,
            f"{risk_id} has unsupported severity: {severity}")
    require(state in ALLOWED_RISK_STATES,
            f"{risk_id} has unsupported state: {state}")
    require(treatment in ALLOWED_RISK_TREATMENTS,
            f"{risk_id} treatment must be exactly Tolerate, Remove, or Mitigate")
    require(bool(finding), f"{risk_id} lacks a risk statement")
    for field_label, value in (("accountable owner", owner), ("deadline", target)):
        require(value and not re.search(r"\b(?:TBD|unassigned)\b", value, re.I),
                f"{risk_id} lacks a controlled {field_label}")
    require("Phase " in target, f"{risk_id} lacks a named phase deadline")
    if treatment == "Tolerate":
        require("tolerat" in target.lower(),
                f"{risk_id} target does not state its toleration boundary")
        require(re.search(r"\b(?:remove|mitigat\w*)\b", target, re.I) is not None,
                f"{risk_id} toleration is not bounded by removal or mitigation")
    elif treatment == "Remove":
        require("remov" in target.lower(), f"{risk_id} target does not require removal")
    elif treatment == "Mitigate":
        require("mitigat" in target.lower(), f"{risk_id} target does not require mitigation")


def qa_risk_rows(risk_log: str) -> dict[str, list[str]]:
    rows = controlled_table_rows(
        risk_log,
        r"^\|\s*QA-R\d{2}\s*\|",
        QA_RISK_TABLE_HEADERS,
        "QA risk register",
    )
    for risk_id, cells in rows.items():
        _, severity, state, treatment, finding, owner, target, resolution = cells
        validate_treatment_fields(risk_id, severity, state, treatment, finding, owner, target)
        require(resolution and not re.search(r"\b(?:TBD|unassigned)\b", resolution, re.I),
                f"{risk_id} lacks a controlled resolution")
        require("**Closure evidence:**" in resolution,
                f"{risk_id} lacks objective closure evidence")
        if state == "Closed":
            require(re.search(r"\bClosed\s+\d{4}-\d{2}-\d{2}\b", resolution) is not None,
                    f"{risk_id} closure lacks a dated record")
    return rows


def principal_risk_rows(register: str) -> dict[str, list[str]]:
    rows = controlled_table_rows(
        register,
        r"^\|\s*PR-\d{2}\s*\|",
        PRINCIPAL_RISK_TABLE_HEADERS,
        "principal risk treatment register",
    )
    for risk_id, cells in rows.items():
        _, severity, state, treatment, finding, owner, target = cells
        validate_treatment_fields(risk_id, severity, state, treatment, finding, owner, target)
    return rows


def principal_control_rows(
    matrix: str,
    principal_risks: dict[str, list[str]],
) -> dict[str, list[str]]:
    rows = controlled_table_rows(
        matrix,
        r"^\|\s*PR-\d{2}\s*\|",
        PRINCIPAL_CONTROL_TABLE_HEADERS,
        "principal control assurance matrix",
    )
    require(set(rows) == set(principal_risks),
            "principal treatment and control-assurance IDs differ")
    for risk_id, cells in rows.items():
        _, controls, effectiveness, assurance = cells
        for marker in ("**P:**", "**D:**", "**R:**"):
            require(marker in controls, f"{risk_id} lacks control type {marker}")
        require(effectiveness in ALLOWED_CONTROL_EFFECTIVENESS,
                f"{risk_id} has unsupported control effectiveness: {effectiveness}")
        require("](" in assurance, f"{risk_id} lacks linked control evidence")
        state = principal_risks[risk_id][2]
        if state == "Open":
            require("**Next proof:**" in assurance,
                    f"{risk_id} lacks mandatory next assurance evidence")
        else:
            require("**Closure evidence:**" in assurance and
                    re.search(r"\bClosed\s+\d{4}-\d{2}-\d{2}\b", assurance) is not None,
                    f"{risk_id} closure lacks dated assurance evidence")
    return rows


def main() -> None:
    quality = read(QUALITY)
    learning = read(LEARNING)
    plan = read(PLAN)
    agents = read(AGENTS)

    for heading in (
        "# Quality Assurance",
        "## Audit boundary and verdict",
        "## What We Are Doing Well",
        "## What We Are Not Doing Well",
        "## Action Matrix",
        "## Residual risk disposition",
    ):
        require(heading in quality, f"QUALITY_ASSURANCE.md missing {heading!r}")
    for heading in ("# Learning from Experience", "## Ledger rules", "## Experience ledger"):
        require(heading in learning, f"LEARNING_FROM_EXPERIENCE.md missing {heading!r}")

    require(re.search(r"owns no live\s+phase status", learning) is not None,
            "learning ledger must explicitly reject live phase ownership")
    require("reference/PROJECT_PLAN.md` is the sole project-wide live status record" in agents,
            "AGENTS.md must preserve the sole live-status owner")
    require("Update it with the human-readable table" not in agents,
            "stale instruction still permits mutation of frozen Phase 1 evidence")
    require("reference/QUALITY_ASSURANCE.md" in agents and
            "reference/LEARNING_FROM_EXPERIENCE.md" in agents,
            "AGENTS.md must route maintainers to both QA controls")

    assurance_rules = subsection(plan, "Risk treatment and control-assurance rules")
    principal_register = subsection(plan, "Principal risk treatment register")
    principal_matrix = subsection(plan, "Principal control assurance matrix")
    principal_risks = principal_risk_rows(principal_register)
    principal_control_rows(principal_matrix, principal_risks)
    principal_numbers = sorted(int(risk_id.split("-")[1]) for risk_id in principal_risks)
    require(len(principal_numbers) >= 21,
            "principal risk register lost an audited risk")
    require(principal_numbers == list(range(1, principal_numbers[-1] + 1)),
            "principal risk IDs must remain contiguous and append-only")

    for treatment in ALLOWED_RISK_TREATMENTS:
        require(f"**{treatment}**" in assurance_rules,
                f"risk assurance rules do not define the {treatment} treatment")
    for effectiveness in ALLOWED_CONTROL_EFFECTIVENESS:
        require(f"**{effectiveness}**" in assurance_rules,
                f"risk assurance rules do not define {effectiveness}")
    for owner_role in ("**project owner**", "**phase/slice owner**", "**QA owner**"):
        require(owner_role in assurance_rules,
                f"risk assurance rules do not define {owner_role}")

    risk_log = subsection(plan, "QA audit risk log")
    quality_risks = RISK_ROW_RE.findall(quality)
    controlled_risks = qa_risk_rows(risk_log)
    plan_risks = list(controlled_risks)
    require(len(quality_risks) == len(set(quality_risks)),
            "duplicate risk ID in QUALITY_ASSURANCE.md")
    require(len(plan_risks) == len(set(plan_risks)),
            "duplicate risk ID in PROJECT_PLAN.md QA risk log")
    require(len(plan_risks) >= 1, "QA risk log must contain at least one residual risk")
    require(set(quality_risks) == set(plan_risks),
            "QUALITY_ASSURANCE.md residual risks and live PROJECT_PLAN.md log differ")
    findings = FINDING_ROW_RE.findall(quality)
    require(findings, "QA audit must contain classified findings")
    for finding_id, row in findings:
        require(re.search(r"QA-(?:A|R)\d{2}", row) is not None,
                f"{finding_id} is neither corrected nor mapped to a residual risk")

    actions = ACTION_ROW_RE.findall(quality)
    require(actions, "QA audit must contain immediate correction actions")
    action_ids = [action_id for action_id, _ in actions]
    require(len(action_ids) == len(set(action_ids)),
            "duplicate action ID in QUALITY_ASSURANCE.md")
    for action_id, row in actions:
        require("| Completed |" in f"|{row}", f"{action_id} is not completed")

    valid_dispositions = set(plan_risks) | set(action_ids)
    for finding_id, row in findings:
        references = set(re.findall(r"QA-(?:A|R)\d{2}", row))
        require(references <= valid_dispositions,
                f"{finding_id} references an unknown disposition: "
                f"{sorted(references - valid_dispositions)}")

    for relative_path, expected in EXPECTED_IMMUTABLE_SOURCE_HASHES.items():
        actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        require(actual == expected, f"unexpected source drift in {relative_path}: {actual}")

    validate_links()
    print("Repository quality-assurance controls validation passed")


if __name__ == "__main__":
    main()
