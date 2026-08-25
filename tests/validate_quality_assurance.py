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
TERMINOLOGY = ROOT / "reference" / "TERMINOLOGY.md"
VALIDATION = ROOT / "reference" / "VALIDATION.md"
WORKFLOWS = ROOT / "reference" / "AGENT_WORKFLOWS.md"
ASD_STE100_REFERENCE = (
    ROOT / "reference" / "external" / "asd-ste100" / "README.md"
)
GITIGNORE = ROOT / ".gitignore"
RISKS = ROOT / "reference" / "current" / "risks.json"
FROZEN = ROOT / "reference" / "history" / "frozen-records.json"
RECOVERY = ROOT / "reference" / "RECOVERY_AND_BACKUP.md"
CHANGE_VALIDATION_SKILL = (
    ROOT
    / ".agents"
    / "skills"
    / "tracktemplate-change-validation"
    / "SKILL.md"
)
CONTINUE_SKILL = (
    ROOT
    / ".agents"
    / "skills"
    / "tracktemplate-continue"
    / "SKILL.md"
)

EXPECTED_IMMUTABLE_SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro":
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro":
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
LFE_001_TO_017_SHA256 = (
    "6fe3654db8ee88566ede3c50ecddb12054399e20e78a8205eb5bb9f414f7e912"
)
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
    require(
        document["updated_on"] == "2026-08-16",
        "frozen-record manifest update date drifted",
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


def validate_validation_document_boundary() -> None:
    validation = read(VALIDATION)
    heading = "## Document boundary"
    require(
        validation.count(heading) == 1,
        "VALIDATION.md must contain one document-boundary section",
    )
    boundary = validation.split(heading, 1)[1].split("\n## ", 1)[0]
    boundary_flat = " ".join(boundary.split())
    for fragment in (
        "durable validation layers",
        "stable runner profiles and entry points",
        "minimum change matrix",
        "does not by itself justify changing this document",
        "Level 2 or Level 3 documentation lifecycle",
        "current/PHASE_EVIDENCE.md",
        "Do not use this document as a tranche log",
    ):
        require(
            fragment in boundary_flat,
            "VALIDATION.md document boundary lacks: " + fragment,
        )

    boundary_link = "../../../reference/VALIDATION.md#document-boundary"
    change_validation = read(CHANGE_VALIDATION_SKILL)
    for fragment in (
        boundary_link,
        "merely because a test was added or run",
        "durable validation contract",
    ):
        require(
            fragment in change_validation,
            "change-validation skill lacks boundary control: " + fragment,
        )

    continue_skill = read(CONTINUE_SKILL)
    for fragment in (
        boundary_link,
        "`reference/VALIDATION.md`",
        "routine tranche",
        "durable validation contract",
    ):
        require(
            fragment in continue_skill,
            "continue skill lacks boundary control: " + fragment,
        )


def validate_documentation_profile(
    engineering: str,
    plan: str,
    learning: str,
    terminology: str,
) -> None:
    """Validate the canonical TT-DOC-001 human-interface contract."""
    heading = "## TT-DOC-001 — TrackTemplate Technical Documentation Profile"
    require(
        engineering.count(heading) == 1,
        "Engineering Policy must own exactly one TT-DOC-001 profile",
    )
    profile = engineering.split(heading, 1)[1].split("\n## ", 1)[0]
    profile_flat = " ".join(profile.split())
    for fragment in (
        "Human comprehensibility is a governance control",
        "Owner view → canonical information → proof/provenance",
        "must never give project authority independently",
        "Only a Level 3 project-owner decision can change the scope",
        "ASD-STE100 Simplified Technical English, Issue 9",
        "2025-01-15",
        "normative controlled-writing standard",
        "official standard is the normative external reference",
        "Public summaries, model knowledge, and automatic validators do not "
        "show conformance",
        "A reviewer must use the official standard for a linguistic "
        "conformance review",
        "Do not copy the standard or its controlled general dictionary",
        "substantial workflow and skill prose",
        "API and schema identifiers",
        "machine-generated logs and evidence",
        "TrackTemplate uses UK English spelling as its project spelling "
        "directive",
        "directive uses the option in Issue 9 Rule 1.14",
        "directive changes spelling only",
        "does not change the applicable Issue 9 vocabulary or grammar rules",
        "does not change approved meanings, parts of speech, or technical-term "
        "controls",
        "does not claim S1000D conformance",
        "TT-DOC-001 conforming",
        "ASD-STE100 Issue 9 conforming",
        "ASD-STE100 Issue 9 conformance not verified",
        "Externally certified or endorsed",
        "does not claim this state",
        "cannot replace the linguistic review or show Issue 9 conformance",
        "facts, evidence, inferences, recommendations, and owner decisions "
        "distinct",
        "Short text must never change evidence or a recommendation into "
        "acceptance",
        "is the one project owner for TrackTemplate technical nouns",
        "All new canonical technical prose in English must obey the applicable "
        "ASD-STE100 Issue 9 requirements",
        "review the full logical unit that contains the change",
        "Review live canonical prose in bounded migration cycles",
        "Do not change frozen history only to correct its Issue 9 style",
        "Add the behaviour to the primary owner when possible",
        "Documentation simplification does not give a skill phase, "
        "production, security, merge, release, acceptance, or project-owner "
        "authority",
        "do not freeze full paragraphs",
        "do not use sentence-length checks as proof of linguistic conformance",
    ):
        require(
            fragment in profile_flat,
            "TT-DOC-001 profile lacks: " + fragment,
        )

    controlled_meanings = {
        "Pending": "Pending gives no authority",
        "Evidenced": "does not give wider acceptance or clearance",
        "Accepted": "decision applies only to its stated authority",
        "Blocked": "prevent the named action or decision",
        "Finding": "does not change project state",
        "Limitation": "reader must be able to see it",
        "Unknown": "does not mean accepted or rejected",
        "Decision required": "owner decision is absent",
    }
    for term, meaning in controlled_meanings.items():
        match = re.search(
            rf"^\| \*\*{re.escape(term)}\*\* \| (.+) \|$",
            profile,
            re.MULTILINE,
        )
        require(match is not None, "TT-DOC-001 lacks controlled term: " + term)
        require(
            meaning in match.group(1),
            "TT-DOC-001 meaning drifted for: " + term,
        )

    for field in (
        "Current state",
        "What changed",
        "What now works",
        "Limitations/findings",
        "Owner decision",
        "Next action",
    ):
        require(
            f"**{field}**" in profile,
            "TT-DOC-001 owner view lacks: " + field,
        )

    require(
        plan.count("## Current owner view") == 1,
        "PROJECT_PLAN must contain one derived current owner view",
    )
    owner_view = plan.split("## Current owner view", 1)[1].split("\n## ", 1)[0]
    require(
        "canonical status, evidence, and registers are the source of the owner "
        "view"
        in " ".join(plan.split()),
        "PROJECT_PLAN owner view lost its derivation boundary",
    )
    require(
        "Phase 6 has 2/5 accepted exits" in owner_view
        and "Exits 1, 4, and 5 stay Pending" in owner_view
        and "D-GOV-011" in owner_view
        and "selects one subsequent hypothesis for the measured canonical area "
        "of Edit" in owner_view
        and "bounds the product change at Level 2 to one FreeCAD "
        "adapter file"
        in owner_view
        and "D-GOV-009, D-GOV-010, and their evidence do not change"
        in owner_view
        and "two repeated reads of the selected record" in owner_view
        and "without work in a different Edit stage" in owner_view
        and "attribution noise floor is `2.895891 ms`" in owner_view
        and "only `0.0731425 ms` higher than that floor" in owner_view
        and "No result is improvement evidence or Exit 4 evidence"
        in owner_view
        and "tracktemplate/adapters/freecad/transition_state.py" in owner_view
        and "Keep one live read of the selected record before the write"
        in owner_view
        and "necessary read after the write" in owner_view
        and "make the D-GOV-011 change at Level 2" in owner_view
        and "record a new same-host baseline on the D-GOV-010 host" in owner_view
        and "attribution materiality rule in D-GOV-009" in owner_view
        and "Do not change the comparison rule" in owner_view
        and "Do not accept Exit 4 without a subsequent owner decision at Level 3"
        in owner_view
        and "Project status stays `unknown`" in owner_view,
        "PROJECT_PLAN owner view contradicts current authority",
    )

    require(
        terminology.count("## ASD-STE100 project terminology") == 1,
        "TERMINOLOGY must own one ASD-STE100 project-term register",
    )
    term_section = terminology.split(
        "## ASD-STE100 project terminology",
        1,
    )[1].split("\n## ", 1)[0]
    term_flat = " ".join(term_section.split())
    for fragment in (
        "one project register for TrackTemplate technical nouns and technical "
        "verbs",
        "does not copy the official controlled general dictionary",
        "Owner view",
        "canonical document",
        "ASD-STE100 Issue 9",
        "Validate",
        "Reconcile",
        "Authorize",
        "Admit",
        "Freeze",
        "stage",
        "Adopt",
        "Claim",
        "Own",
        "Review",
        "Preserve",
        "Map",
        "Migrate",
        "Report",
        "Centreline",
        "substantial cycle",
        "Product behavior",
        "Host compatibility",
        "exact host profile",
        "`exact_match` data in its contract record",
        "qualified host profile",
        "bundled stack",
        "host matrix",
        "Requalification",
        "runtime guard",
        "evaluator",
        "runtime probe",
        "launcher",
        "fixture",
        "Legacy ingress",
        "Functional compatibility",
        "Qualify",
        "Requalify",
        "comparison baseline",
        "performance hypothesis",
        "comparison rule",
        "performance optimisation",
        "Zero-origin integration",
        "preview sampler",
        "preview regeneration",
        "preview batch function",
        "Simpson integration",
        "interior station",
        "endpoint calculation",
        "unmeasured boundary",
        "paired block",
        "paired difference",
        "first quartile",
        "median absolute deviation (MAD)",
        "Measurement noise",
        "no-displacement rule",
        "warm block value",
        "resource metric",
        "High-water RSS",
        "journey remainder",
        "discrete invariant",
        "Visible recovery state",
        "stash inventory",
        "stash selector",
        "stash commit SHA",
        "stash component",
        "unique content",
        "Unresolved recovery state",
        "dirty path",
        "recovery purpose",
        "retained stash",
        "stash ownership",
        "stash reconciliation",
        "stash disposition",
        "recovery inventory",
        "recovery audit",
        "preservation diff",
        "Workspace alignment",
        "Accepted product state",
        "Setup",
        "Teardown",
        "attribution series",
        "attribution noise floor",
        "attribution materiality rule",
        "Worktree retirement",
        "Accepted-history containment",
        "local-state inventory",
        "retirement plan",
        "retirement audit",
        "ambiguous or uniquely owned state",
        "Put one local-state inventory item in one of the five types",
        "Do not use different technical terms for the same project concept",
        "Do not use a technical noun as a verb unless this register also "
        "approves the verb",
    ):
        require(
            fragment in term_flat,
            "TrackTemplate STE terminology lacks: " + fragment,
        )

    lfe_rows = [
        line
        for line in learning.splitlines()
        if re.match(r"^\| LFE-\d{3} ", line)
    ]
    lfe_ids = [
        re.match(r"^\| LFE-(\d{3}) ", row).group(1)
        for row in lfe_rows
    ]
    require(
        lfe_ids == [f"{value:03d}" for value in range(1, 22)],
        "LFE ledger is not unique and append-only through LFE-021",
    )
    protected_prefix = "\n".join(lfe_rows[:17]) + "\n"
    require(
        hashlib.sha256(protected_prefix.encode("utf-8")).hexdigest()
        == LFE_001_TO_017_SHA256,
        "an LFE row before LFE-018 was modified",
    )
    lfe_018 = lfe_rows[17]
    for fragment in (
        "current state",
        "limitations",
        "decision",
        "could not easily find the current state",
        "TT-DOC-001 Level 3 decision",
        "tt-doc-001-documentation-architecture-panel",
        "Technical Documentation Profile",
        "tt-doc-001-tracktemplate-technical-documentation-profile",
        "short owner view",
        "ASD-STE100 Issue 9",
        "Migration occurs in bounded cycles",
        "Frozen history does not change",
        "must never give authority",
    ):
        require(fragment in lfe_018, "LFE-018 lacks: " + fragment)


def validate_asd_ste100_reference(
    engineering: str,
    validation: str,
    workflows: str,
    reference: str,
    gitignore: str,
) -> None:
    """Validate the one local Issue 9 source-resolution contract."""
    local_pdf = (
        "reference/external/asd-ste100/ASD-STE100_ISSUE9.pdf"
    )
    source_owner = "external/asd-ste100/README.md"
    reference_flat = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        " ".join(reference.split()),
    )
    remote_targets = {
        target
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", reference)
        if target.startswith(("http://", "https://"))
    }
    engineering_flat = " ".join(engineering.split())
    validation_flat = " ".join(validation.split())
    workflows_flat = " ".join(workflows.split())

    require(
        reference.count(local_pdf) == 1,
        "ASD-STE100 reference instructions must define one local PDF path",
    )
    require(
        local_pdf not in engineering
        and local_pdf not in validation
        and local_pdf not in workflows,
        "ASD-STE100 local PDF path gained a competing canonical definition",
    )
    for fragment in (
        "ASD-STE100 Simplified Technical English, Issue 9",
        "ASD has the copyright for this external reference",
        "Do not commit the PDF to the TrackTemplate repository",
        "Get the official document from the ASD Simplified Technical English "
        "Maintenance Group",
        "Reviewers use the local file for documentation review and linguistic "
        "conformance assessment",
        "PDF is not necessary for TrackTemplate product execution or normal "
        "repository CI",
        "PDF is not a canonical TrackTemplate document",
        "TT-DOC-001 profile",
        "TT-DOC-002 decision",
        "Use the local official PDF when it is available",
        "If the local PDF is absent, use the official ASD/STEMG Issue 9 "
        "source when network access is available",
        "Do not use a third-party summary, search-result text, blog, or "
        "derived guidance as normative conformance evidence",
        "review record must report which official source the reviewer used",
        "neither official source is available, do not claim that the prose is "
        "ASD-STE100 Issue 9 conforming",
    ):
        require(
            fragment in reference_flat,
            "ASD-STE100 reference instructions lack: " + fragment,
        )

    official_targets = {
        "https://www.asd-ste100.org/",
        "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf",
    }
    require(
        remote_targets == official_targets,
        "ASD-STE100 official ASD/STEMG source targets drifted",
    )

    ignore_rule = "/reference/external/asd-ste100/*.pdf"
    require(
        gitignore.splitlines().count(ignore_rule) == 1,
        "ASD-STE100 local PDF must have one narrow Git exclusion",
    )
    for broad_rule in (
        "/reference/external/",
        "/reference/external/asd-ste100/",
        "/reference/external/asd-ste100/*",
    ):
        require(
            broad_rule not in gitignore.splitlines(),
            "ASD-STE100 Git exclusion is too broad: " + broad_rule,
        )

    require(
        source_owner in engineering,
        "TT-DOC-001 profile lost the ASD-STE100 source owner link",
    )
    require(
        "own only the local path and source priority" in engineering_flat
        and "do not own TrackTemplate documentation policy" in engineering_flat,
        "TT-DOC-001 profile confused source routing with policy authority",
    )
    require(
        source_owner in validation,
        "VALIDATION lost the ASD-STE100 source owner link",
    )
    require(
        "Normal CI does not use the ignored PDF" in validation_flat
        and "conformance record must report its official source"
        in validation_flat
        and "Automatic validation does not prove linguistic conformance"
        in validation_flat,
        "ASD-STE100 validation or CI boundary drifted",
    )
    require(
        source_owner in workflows,
        "AGENT_WORKFLOWS lost the ASD-STE100 source owner link",
    )
    require(
        "documentation review workflow uses the official source only for a "
        "linguistic conformance assessment" in workflows_flat
        and "Other workflows route that assessment to documentation review"
        in workflows_flat
        and "They do not read the PDF during usual work" in workflows_flat,
        "ASD-STE100 workflow routing drifted",
    )


def validate_no_product_ste100_dependency() -> None:
    """Keep the external linguistic reference out of product execution."""
    product_files = sorted((ROOT / "tracktemplate").rglob("*.py"))
    product_files.append(ROOT / "TrackTemplate.FCMacro")
    for path in product_files:
        text = path.read_text(encoding="utf-8")
        require(
            "external/asd-ste100" not in text
            and "ASD-STE100_ISSUE9.pdf" not in text,
            "TrackTemplate product depends on the external Issue 9 PDF: "
            + path.relative_to(ROOT).as_posix(),
        )


def main() -> None:
    quality = read(QUALITY)
    learning = read(LEARNING)
    plan = read(PLAN)
    agents = read(AGENTS)
    engineering = read(ENGINEERING)
    terminology = read(TERMINOLOGY)
    validation = read(VALIDATION)
    workflows = read(WORKFLOWS)
    asd_ste100_reference = read(ASD_STE100_REFERENCE)
    gitignore = read(GITIGNORE)

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
    validate_documentation_profile(engineering, plan, learning, terminology)
    validate_asd_ste100_reference(
        engineering,
        validation,
        workflows,
        asd_ste100_reference,
        gitignore,
    )
    validate_no_product_ste100_dependency()
    validate_validation_document_boundary()
    for relative, expected in EXPECTED_IMMUTABLE_SOURCE_HASHES.items():
        require(
            sha256(ROOT / relative) == expected,
            "unexpected immutable-source drift in " + relative,
        )
    validate_links()
    print("Repository QA, frozen-history and documentation controls passed")


if __name__ == "__main__":
    main()
