#!/usr/bin/env python3
"""Validate QA ownership, frozen history and repository documentation links."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / "reference" / "QUALITY_ASSURANCE.md"
LEARNING = ROOT / "reference" / "LEARNING_FROM_EXPERIENCE.md"
PLAN = ROOT / "reference" / "PROJECT_PLAN.md"
AGENTS = ROOT / "AGENTS.md"
ENGINEERING = ROOT / "reference" / "ENGINEERING_POLICY.md"
RISKS = ROOT / "reference" / "current" / "risks.json"
FROZEN = ROOT / "reference" / "history" / "frozen-records.json"
RECOVERY = ROOT / "reference" / "RECOVERY_AND_BACKUP.md"

EXPECTED_IMMUTABLE_SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro":
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro":
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
QA_RISK_RE = re.compile(r"^\|\s*(QA-R\d{2})\s*\|", re.MULTILINE)
NON_AUTHORITY_GATE_REGRESSIONS = {
    "reference/PERFORMANCE_SOP.md": ("## Acceptance gates",),
    "reference/ARCHITECTURE.md": (
        "retirement gate",
        "correctness and performance gates",
    ),
    "reference/MODULARISATION_PLAN.md": (
        "Maintainability and reuse gate",
        "Exit gate:",
        "Validation gates",
        "retirement gate",
    ),
    "reference/TESTING_POLICY.md": (
        "failed-test adjudication gate",
        "retirement gate",
    ),
    "reference/VALIDATION.md": (
        "temporary duplicate/retirement gate",
        "live phase gates",
        "missing artifact and independent-evidence gates",
    ),
    ".agents/skills/tracktemplate-task-automation/SKILL.md": (
        "## Admission gate",
    ),
    ".agents/skills/tracktemplate-performance-engineering/SKILL.md": (
        "current phase gate",
    ),
    ".agents/skills/tracktemplate-api-design/SKILL.md": (
        "retirement gate",
    ),
    ".agents/skills/tracktemplate-architecture-review/SKILL.md": (
        "current gate",
        "retirement gate",
        "live gate status",
        "open-phase record",
    ),
    ".agents/skills/tracktemplate-change-validation/references/"
    "validation-checklist.md": ("open gates",),
    ".agents/skills/tracktemplate-quality-review/references/"
    "review-checklist.md": ("retirement gate",),
    ".agents/skills/tracktemplate-release-readiness/SKILL.md": (
        "non-functional gates",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.is_file(), "missing required QA control: {}".format(path))
    return path.read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(read(path))
    except json.JSONDecodeError as error:
        raise AssertionError("invalid JSON in {}".format(path)) from error
    require(isinstance(value, dict), "{} must contain an object".format(path))
    return value


def markdown_documents() -> list[Path]:
    documents = list(ROOT.glob("*.md"))
    for base in (
        ROOT / "reference",
        ROOT / "tools",
        ROOT / "tests",
        ROOT / "tracktemplate",
    ):
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
    require(
        not target.startswith("/"),
        "non-portable absolute Markdown target in {}: {}".format(
            document.relative_to(ROOT),
            target,
        ),
    )
    resolved = (document.parent / target).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as error:
        raise AssertionError(
            "repository-external Markdown target in {}: {}".format(
                document.relative_to(ROOT),
                target,
            )
        ) from error
    return resolved


def prose_outside_fenced_blocks(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def validate_links() -> None:
    broken: list[str] = []
    for document in markdown_documents():
        prose = prose_outside_fenced_blocks(read(document))
        for raw_target in LINK_RE.findall(prose):
            target = local_link_target(document, raw_target)
            if target is not None and not target.exists():
                broken.append(
                    "{} -> {}".format(
                        document.relative_to(ROOT),
                        target.relative_to(ROOT),
                    )
                )
    require(
        not broken,
        "broken repository-internal Markdown targets:\n" + "\n".join(broken),
    )


def validate_frozen_records() -> None:
    document = load_json(FROZEN)
    require(
        set(document) == {"schema_version", "status", "updated_on", "records"},
        "frozen-record manifest fields changed",
    )
    require(document["schema_version"] == 1, "unsupported frozen-record schema")
    require(
        document["status"] == "accepted-frozen-records",
        "frozen-record status changed",
    )
    records = document["records"]
    require(isinstance(records, list), "frozen records must be a list")

    by_path: dict[str, dict[str, str]] = {}
    for record in records:
        require(isinstance(record, dict), "frozen record must be an object")
        require(
            set(record) == {"category", "path", "sha256"},
            "frozen-record fields changed",
        )
        relative = record["path"]
        require(
            isinstance(relative, str) and relative not in by_path,
            "duplicate or invalid frozen path",
        )
        require(
            record["category"]
            in {
                "phase-closeout",
                "phase-inventory",
                "phase-foundation",
                "audit",
                "benchmark",
            },
            "unsupported frozen-record category",
        )
        require(
            re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"])) is not None,
            "invalid frozen-record hash",
        )
        path = ROOT / relative
        require(path.is_file(), "missing frozen record: " + relative)
        require(
            sha256(path) == record["sha256"],
            "frozen record changed without accepted manifest update: " + relative,
        )
        by_path[relative] = record

    expected_phase_records = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "reference" / "phase-evidence").glob("*.md")
        if path.name != "PHASE4_CANONICAL_STATE.md"
    }
    expected_benchmarks = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "reference" / "benchmarks").glob("*.md")
    }
    expected_new_closeouts = {
        path.relative_to(ROOT).as_posix()
        for path in (
            ROOT / "reference" / "history" / "phase-closeouts"
        ).iterdir()
        if path.is_file()
    }
    expected = (
        expected_phase_records
        | expected_benchmarks
        | expected_new_closeouts
        | {
            "reference/QUALITY_ASSURANCE.md"
        }
    )
    require(set(by_path) == expected, "frozen-record manifest coverage drifted")


def validate_current_qa_risks(quality: str) -> None:
    audit_ids = set(QA_RISK_RE.findall(quality))
    require(
        audit_ids == {"QA-R01", "QA-R02", "QA-R03", "QA-R04", "QA-R05"},
        "frozen QA risk IDs drifted",
    )
    live = load_json(RISKS)
    live_qa = {
        record["id"]
        for record in live["risks"]
        if isinstance(record, dict) and str(record.get("id", "")).startswith("QA-R")
    }
    require(
        live_qa == audit_ids - {"QA-R01", "QA-R02"},
        "current QA risks differ from the frozen audit and closed QA-R01/QA-R02",
    )
    require(
        "QA-R01 remains closed" in read(RECOVERY),
        "QA-R01 closure authority is missing from the recovery owner",
    )


def validate_governance_controls(
    plan: str,
    agents: str,
    engineering: str,
) -> None:
    engineering_flat = " ".join(engineering.split())
    require(100 <= len(agents.splitlines()) <= 140, "AGENTS.md line budget drifted")
    require(len(agents.encode("utf-8")) < 12 * 1024, "AGENTS.md byte budget drifted")
    require(
        "reference/AGENT_WORKFLOWS.md" in agents,
        "AGENTS.md does not route specialist skills",
    )
    require(
        "reference/ENGINEERING_POLICY.md" in agents,
        "AGENTS.md does not route engineering governance",
    )
    require(
        "reference/current/PHASE_EVIDENCE.md" in agents,
        "AGENTS.md does not route the fixed current evidence",
    )
    require(
        "$tracktemplate-" not in agents,
        "the specialist skill catalogue returned to AGENTS.md",
    )

    require(
        "Governance changes must not exceed the implementation change"
        in engineering_flat,
        "engineering policy lacks the governance budget",
    )
    for level in (
        "Level 1 — Routine",
        "Level 2 — Behavioural",
        "Level 3 — Authority or release",
    ):
        require(level in engineering, "engineering policy lacks " + level)
        require(level in agents, "AGENTS.md lacks " + level)
    require("Level 0" not in engineering, "obsolete Level 0 remains in policy")
    require("Level 0" not in agents, "obsolete Level 0 remains in AGENTS.md")
    for requirement in (
        "Required: the relevant test, complete diff review and a concise "
        "commit message.",
        "relevant specialist skill, automated and applicable FreeCAD/GUI "
        "validation, exactly one concise entry",
        "Required: full evidence review, a safety/risk panel, an explicit "
        "project-owner decision and a project-plan update.",
        "Do not run a panel for Level 1 or Level 2 work.",
    ):
        require(
            requirement in engineering_flat,
            "three-level requirement is missing: " + requirement,
        )
    require(
        "A gate is a decision that transfers, expands, retires or irreversibly "
        "changes project authority"
        in engineering_flat,
        "engineering policy lacks a true-gate definition",
    )
    for trigger in (
        "phase or release closure, including beta or release-candidate "
        "packaging",
        "a legacy migration family or window becoming supported",
        "retirement of an accepted oracle or rollback authority",
        "production-output or chair-package clearance",
        "governance, licensing or provenance authority changes",
        "irreversible or destructive repository, data or external operations",
    ):
        require(
            trigger in engineering_flat,
            "risk-panel trigger is missing: " + trigger,
        )
    require(
        "Every Level 3 task is a true gate and requires a safety/risk panel."
        in engineering_flat,
        "engineering policy does not reserve gates for Level 3",
    )
    for outcome in (
        "**Proceed**",
        "**Proceed with bounded conditions**",
        "**Do not proceed**",
    ):
        require(outcome in engineering, "panel outcome is missing: " + outcome)
    for heading in (
        "Changed:",
        "Validated:",
        "GUI work outstanding:",
        "Risks or authority changes:",
    ):
        require(
            heading in engineering,
            "compact completion field is missing: " + heading,
        )

    for duplicated_policy in (
        "Mandatory safety/risk panel",
        "Principal risk treatment register",
        "Principal control assurance matrix",
        "QA audit risk log",
        "### Deliverables",
    ):
        require(
            duplicated_policy not in plan,
            "PROJECT_PLAN.md contains duplicated policy/detail: " + duplicated_policy,
        )

    for relative, forbidden_phrases in NON_AUTHORITY_GATE_REGRESSIONS.items():
        text = read(ROOT / relative)
        for phrase in forbidden_phrases:
            require(
                phrase not in text,
                "{} again labels an ordinary control as a gate: {}".format(
                    relative,
                    phrase,
                ),
            )


def main() -> None:
    quality = read(QUALITY)
    learning = read(LEARNING)
    plan = read(PLAN)
    agents = read(AGENTS)
    engineering = read(ENGINEERING)

    for heading in (
        "# Quality Assurance",
        "## Audit boundary and verdict",
        "## What We Are Doing Well",
        "## What We Are Not Doing Well",
        "## Action Matrix",
        "## Residual risk disposition",
    ):
        require(heading in quality, "QUALITY_ASSURANCE.md missing " + heading)
    for heading in (
        "# Learning from Experience",
        "## Ledger rules",
        "## Experience ledger",
    ):
        require(heading in learning, "learning ledger missing " + heading)
    require(
        re.search(r"owns no live\s+phase status", learning) is not None,
        "learning ledger must reject live phase ownership",
    )
    require(
        '<a id="qa-audit-risk-log"></a>' in plan,
        "the frozen QA audit's compatibility anchor is missing",
    )

    validate_frozen_records()
    validate_current_qa_risks(quality)
    validate_governance_controls(plan, agents, engineering)
    for relative, expected in EXPECTED_IMMUTABLE_SOURCE_HASHES.items():
        require(
            sha256(ROOT / relative) == expected,
            "unexpected immutable-source drift in " + relative,
        )
    validate_links()
    print("Repository QA, frozen-history and documentation controls passed")


if __name__ == "__main__":
    main()
