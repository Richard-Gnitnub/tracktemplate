#!/usr/bin/env python3
"""Validate the bounded exporter fault-model governance contract."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]

PATHS = {
    "architecture": ROOT / "reference" / "ARCHITECTURE.md",
    "validation": ROOT / "reference" / "VALIDATION.md",
    "recovery": ROOT / "reference" / "RECOVERY_AND_BACKUP.md",
    "evidence": ROOT / "reference" / "current" / "PHASE_EVIDENCE.md",
    "decisions": (
        ROOT / "reference" / "current" / "gate-decisions.json"
    ),
    "risks": ROOT / "reference" / "current" / "risks.json",
    "plan": ROOT / "reference" / "PROJECT_PLAN.md",
    "learning": ROOT / "reference" / "LEARNING_FROM_EXPERIENCE.md",
}

SKILL_ROOT = ROOT / ".agents" / "skills"
SKILL_NAMES = (
    "tracktemplate-architecture-review",
    "tracktemplate-api-design",
    "tracktemplate-change-validation",
    "tracktemplate-security-review",
    "tracktemplate-debugging",
    "tracktemplate-quality-review",
    "tracktemplate-technical-lead",
    "tracktemplate-continue",
)

DESCRIPTION_RULES = {
    "tracktemplate-architecture-review": (
        19,
        ("architecture", "dependency-direction", "canonical-state"),
    ),
    "tracktemplate-api-design": (
        29,
        ("versioned", "Python APIs", "FreeCAD integration", "exporters"),
    ),
    "tracktemplate-change-validation": (
        15,
        ("proportionate", "classify failed tests", "FreeCAD"),
    ),
    "tracktemplate-security-review": (
        20,
        ("trust boundaries", "security-sensitive", "export destinations"),
    ),
    "tracktemplate-debugging": (
        22,
        ("Reproduce, isolate and diagnose", "regressions", "FreeCAD"),
    ),
    "tracktemplate-quality-review": (
        27,
        (
            "staff-level review",
            "source and tests",
            "read-only",
            "Governance documents use their sole Documentation Review instead",
        ),
    ),
    "tracktemplate-technical-lead": (
        44,
        ("Level 1 or Level 2", "cross-specialist", "Level 3 decision"),
    ),
    "tracktemplate-continue": (
        49,
        ("`$tracktemplate-continue`", "draft pull request", "Level 3"),
    ),
}

ARCHITECTURE_LINK = (
    "../../../reference/ARCHITECTURE.md"
    "#supported-exporter-failure-model"
)
VALIDATION_LINK = (
    "../../../reference/VALIDATION.md"
    "#supported-exporter-interruption-evidence"
)
RECOVERY_LINK = (
    "../../../reference/RECOVERY_AND_BACKUP.md"
    "#recovery-after-an-abnormally-interrupted-export"
)

REQUIRED_SKILL_LINKS = {
    "tracktemplate-architecture-review": {ARCHITECTURE_LINK},
    "tracktemplate-api-design": {ARCHITECTURE_LINK},
    "tracktemplate-change-validation": {
        ARCHITECTURE_LINK,
        VALIDATION_LINK,
        RECOVERY_LINK,
    },
    "tracktemplate-security-review": {ARCHITECTURE_LINK, RECOVERY_LINK},
    "tracktemplate-debugging": {ARCHITECTURE_LINK, RECOVERY_LINK},
    "tracktemplate-quality-review": {ARCHITECTURE_LINK},
}

LFE_001_TO_016_SHA256 = (
    "a6b39465c32acef87c48f2ef11d86e365f30539d327a460f2a0af8597adf13f8"
)


def require(condition: bool, message: str) -> None:
    """Raise a focused assertion when a governance invariant drifts."""
    if not condition:
        raise AssertionError(message)


def semantic(text: str) -> str:
    """Normalise only presentation whitespace."""
    return " ".join(text.split())


def require_fragments(label: str, text: str, fragments: tuple[str, ...]) -> None:
    """Require bounded semantic clauses without freezing whole paragraphs."""
    flattened = semantic(text)
    for fragment in fragments:
        require(fragment in flattened, f"{label} lacks: {fragment}")


def section(text: str, heading: str) -> str:
    """Return one Markdown section beneath an exact heading."""
    require(text.count(heading) == 1, f"expected one heading: {heading}")
    start = text.index(heading) + len(heading)
    level = len(heading) - len(heading.lstrip("#"))
    tail = text[start:]
    next_heading = re.search(rf"^#{{1,{level}}} ", tail, re.MULTILINE)
    return tail if next_heading is None else tail[: next_heading.start()]


def load_documents() -> dict[str, str]:
    """Load every canonical and skill surface owned by this validator."""
    documents = {
        name: path.read_text(encoding="utf-8")
        for name, path in PATHS.items()
    }
    for name in SKILL_NAMES:
        path = SKILL_ROOT / name / "SKILL.md"
        documents[name] = path.read_text(encoding="utf-8")
    return documents


def validate_canonical_sections(documents: dict[str, str]) -> None:
    """Validate the three canonical owners and their authority boundaries."""
    architecture = section(
        documents["architecture"],
        "#### Supported exporter failure model",
    )
    require_fragments(
        "supported exporter failure model",
        architecture,
        (
            "D-P6-004 is a successor clarification to D-P6-003",
            "defined, finite and testable supported failure model",
            "Widening or narrowing that model requires a further Level 3",
            "ordinary Python exceptions",
            "explicit application cancellation points",
            "retained and expressly tested `BaseException`",
            "staging, publication, cleanup and durability failures",
            "exact-partial and exact-complete next-invocation recovery",
            "operating system closes process-owned descriptors",
            "qualified FreeCAD import and host execution",
            "deliberately excludes arbitrary asynchronous",
            "between every possible pair of Python bytecode instructions",
            "research evidence, not automatically",
            "retained mandatory invariant violation",
            "descriptor-relative destination access",
            "add-only and no-overwrite publication",
            "exact-complete-pair reuse only",
            "exact-partial monotonic completion only",
            "preserves every existing or published final file",
            "never unlinks, renames, rewrites, truncates or replaces",
            "`destination_changed`, `cleanup_complete`, `recoverable`",
            "private-development with project status `unknown`",
            "closing FreeCAD completely is the supported containment",
            "Restart restores the process boundary; it does not prove",
            "Restart containment never permits deletion",
            "isolated, short-lived export helper process",
            "not authorised here",
        ),
    )

    validation = section(
        documents["validation"],
        "#### Supported exporter interruption evidence",
    )
    require_fragments(
        "supported exporter interruption evidence",
        validation,
        (
            "supported exporter failure model",
            "Recovery after an abnormally interrupted export",
            "does not create a second command catalogue",
            "ordinary exceptions and explicit application cancellation",
            "expressly retained `BaseException` product boundaries",
            "staging, publication, durability, cleanup, and recovery matrix",
            "preserve each pre-existing and published final",
            "conservative diagnostics when durability or retained state is "
            "uncertain",
            "D-P6-003 exact-partial and exact-complete handling on the next "
            "invocation",
            "qualified FreeCAD import and host-execution evidence",
            "exploratory disposable probes have different authority",
            "does not automatically show an implementation defect",
            "does not automatically prevent Exit 3",
            "another mandatory-invariant violation also prevents Exit 3",
        ),
    )

    recovery = section(
        documents["recovery"],
        "## Recovery after an abnormally interrupted export",
    )
    require_fragments(
        "abnormally interrupted export recovery",
        recovery,
        (
            "Do not alter or delete any existing DXF or manifest member",
            "Close FreeCAD completely",
            "Restart FreeCAD and reopen the project",
            "Inspect the destination through the normal TrackTemplate "
            "workflow",
            "Retry the export through the normal exporter",
            "Never manually delete, rename, replace or edit a partial pair",
            "does not prove that a destination member is regular, exact, "
            "complete or durable",
            "independently inspect and validate destination state",
            "D-P6-003 add-only protocol",
            "Restart-based containment never grants authority to delete, "
            "overwrite, replace, rewrite, truncate, rename",
        ),
    )


def validate_skill_routing(documents: dict[str, str]) -> None:
    """Protect concise skill routing without making skills policy owners."""
    for name in SKILL_NAMES:
        text = documents[name]
        description = re.search(r"^description: (.+)$", text, re.MULTILINE)
        require(description is not None, f"{name} lacks description")
        description_text = description.group(1)
        minimum_words, markers = DESCRIPTION_RULES[name]
        require(
            len(description_text.split()) >= minimum_words,
            f"{name} description was materially shortened",
        )
        require_fragments(f"{name} description", description_text, markers)

    for name, links in REQUIRED_SKILL_LINKS.items():
        for link in links:
            require(
                f"]({link})" in documents[name],
                f"{name} lacks canonical fault-model routing: {link}",
            )

    require_fragments(
        "architecture-review skill",
        documents["tracktemplate-architecture-review"],
        (
            "widening or narrowing that model as an architecture and Level 3",
            "process-local cleanup, restart containment and an isolated "
            "helper-process boundary",
        ),
    )
    require_fragments(
        "api-design skill",
        documents["tracktemplate-api-design"],
        (
            "interruption, failure, cleanup, retry and recovery guarantees as "
            "explicit contract terms",
            "must not widen that supported contract implicitly",
        ),
    )
    require_fragments(
        "change-validation skill",
        documents["tracktemplate-change-validation"],
        (
            "outside the supported exporter failure model as research "
            "evidence",
            "not automatically a blocker",
            "retained invariant violation",
        ),
    )
    require_fragments(
        "security-review skill",
        documents["tracktemplate-security-review"],
        (
            "Do not promote an explicitly unsupported arbitrary-bytecode "
            "micro-window into a blocker",
            "lock or descriptor failure inside the supported model",
            "violations of the restart boundary remain blockers",
        ),
    )
    require_fragments(
        "debugging skill",
        documents["tracktemplate-debugging"],
        (
            "classify the report as: (1) a failure inside that model",
            "operator-recovery case covered by the",
            "deliberately unsupported arbitrary asynchronous interruption "
            "micro-window",
            "not automatically a current implementation defect or phase-exit "
            "blocker",
        ),
    )
    require_fragments(
        "quality-review skill",
        documents["tracktemplate-quality-review"],
        (
            "Do not silently widen it during staff review",
            "contradiction between an implementation or evidence claim and "
            "the supported exporter failure model",
        ),
    )

    policy_markers = (
        "ordinary Python exceptions",
        "explicit application cancellation points",
        "process termination where the operating system",
        "between every possible pair of Python bytecode instructions",
        "repeatedly during cleanup itself",
    )
    for name in REQUIRED_SKILL_LINKS:
        copied_markers = sum(
            marker in documents[name] for marker in policy_markers
        )
        require(
            copied_markers <= 1,
            f"{name} duplicates the complete canonical fault model",
        )

    all_skills = "\n".join(documents[name] for name in SKILL_NAMES)
    forbidden_claims = (
        "every arbitrary bytecode interruption is supported",
        "every possible pair of Python bytecode instructions is supported",
        "unsupported micro-window is automatically a blocker",
    )
    for claim in forbidden_claims:
        require(claim not in semantic(all_skills), f"skill widens policy: {claim}")


def validate_current_authority(documents: dict[str, str]) -> None:
    """Protect D-P6-004/D-P6-005, current status and risk dispositions."""
    plan = semantic(documents["plan"])
    require(
        "Phase 6 current — 2/5 accepted exits" in plan,
        "PROJECT_PLAN lost Phase 6 2/5 status",
    )
    require(
        "The same export input gives the same output, and export is "
        "failure-safe | Evidenced — owner-accepted 2026-08-15" in plan,
        "PROJECT_PLAN lost D-P6-005 Exit 3 acceptance",
    )
    require_fragments(
        "PROJECT_PLAN exporter dashboard",
        documents["plan"],
        (
            "D-P6-004 defines the finite supported exporter fault model",
            "D-P6-005 accepts only the bounded B16 Entry/Exit "
            "DXF-and-manifest route",
            "The route has private-development status",
            "The same input gives the same bytes, and the route is "
            "failure-safe under D-P6-003 and D-P6-004",
            "advances Phase 6 to 2/5",
            "Project status remains `unknown`",
        ),
    )

    evidence = documents["evidence"]
    panel = section(
        evidence,
        "## Phase 6 exporter fault-model clarification panel and owner "
        "decision",
    )
    require_fragments(
        "D-P6-004 panel",
        panel,
        (
            "d8e2b640da412ec0aff0300cd7344e78cec0048b",
            "exactly two fresh read-only reviewers",
            "one frozen candidate",
            "No ordinary exception or explicit cancellation point is "
            "excluded only to obtain Exit 3",
            "No retained tested interruption condition or accepted recovery "
            "path is excluded for that purpose",
            "Proceed with bounded conditions",
            "No risk state, treatment, effectiveness, or disposition changes",
            "changes no product source",
            "Phase 6 remains 1/5 and Exit 3 remains Pending",
            "next decision is a fresh Level 3 Exit 3 panel to admit evidence "
            "against the supported model",
        ),
    )
    acceptance_panel = section(
        evidence,
        "## Phase 6 Exit 3 supported-model panel to admit evidence and "
        "owner decision",
    )
    require_fragments(
        "D-P6-005 panel",
        acceptance_panel,
        (
            "7198b05b6a4b7e4654b7d02d0bad4e5cf627a799",
            "PROCEED TO OWNER ACCEPTANCE WITH BOUNDED CONDITIONS",
            "There was no dissent",
            "No supported-model defect, unsafe recovery path, material "
            "evidence gap, or contradiction with D-P6-003/D-P6-004 was found",
            "No risk state, treatment, effectiveness, or disposition changes",
            "Phase 6 advances from 1/5 to 2/5",
            "published finals must never be deleted, renamed, rewritten, "
            "truncated",
            "replaced or manually altered to recover",
            "Output remains private-development with project status `unknown`. No",
            "authority is granted for Exit 1, 4, or 5. No production or "
            "physical-output",
            "clearance is granted",
        ),
    )
    current = section(
        evidence,
        "## Current Phase 6 exit-condition disposition",
    )
    require(
        "| Export is deterministic and failure-safe | Evidenced and "
        "owner-accepted under D-P6-005" in current,
        "current evidence lost D-P6-005 Exit 3 acceptance",
    )
    require(
        "The accepted current state is 2/5 under D-P6-002 and D-P6-005"
        in semantic(current),
        "current evidence lost the accepted Phase 6 2/5 state",
    )

    decision_document = json.loads(documents["decisions"])
    decisions = decision_document["decisions"]
    ids = [record["id"] for record in decisions]
    require(len(ids) == len(set(ids)), "duplicate current decision ID")
    fault_model_index = ids.index("D-P6-004")
    require(
        ids[fault_model_index:fault_model_index + 4]
        == ["D-P6-004", "D-P6-005", "TT-DOC-001", "TT-DOC-002"],
        "D-P6-004/D-P6-005 or later TT-DOC decision order drifted",
    )
    decisions_by_id = {record["id"]: record for record in decisions}
    fault_model_record = decisions_by_id["D-P6-004"]
    require(
        fault_model_record["status"] == "Accepted"
        and fault_model_record["decided_on"] == "2026-08-15",
        "D-P6-004 status or date drifted",
    )
    require_fragments(
        "D-P6-004 structured authority",
        fault_model_record["authority"]
        + " "
        + fault_model_record["exclusions"],
        (
            "d8e2b640da412ec0aff0300cd7344e78cec0048b",
            "ordinary Python exceptions",
            "named and tested `BaseException` cases",
            "excludes injection of arbitrary asynchronous `BaseException` "
            "values",
            "An excluded probe is not automatically a problem or a finding "
            "that prevents Exit 3",
            "Preserve each D-P6-003 file-addition, no-overwrite",
            "close FreeCAD completely",
            "does not prove destination correctness",
            "changes no product source or exporter implementation",
            "authorises no helper process",
            "does not accept Exit 3",
            "Phase 6 remains 1/5 and Exit 3 remains Pending",
        ),
    )
    expected_fault_model_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#phase-6-exporter-fault-model-clarification-panel"
    )
    require(
        fault_model_record["evidence"] == expected_fault_model_panel
        and fault_model_record["panel_record"]
        == expected_fault_model_panel,
        "D-P6-004 panel routing drifted",
    )
    acceptance_record = decisions_by_id["D-P6-005"]
    require(
        acceptance_record["status"] == "Accepted"
        and acceptance_record["decided_on"] == "2026-08-15"
        and acceptance_record["decision"]
        == "Accept Phase 6 Exit 3 for the bounded B16 Entry/Exit exporter.",
        "D-P6-005 status, date or decision drifted",
    )
    require_fragments(
        "D-P6-005 structured authority",
        acceptance_record["authority"]
        + " "
        + acceptance_record["exclusions"],
        (
            "7198b05b6a4b7e4654b7d02d0bad4e5cf627a799",
            "The result is Evidenced and owner-accepted only for the bounded "
            "B16 Entry/Exit route",
            "This private-development output route produces DXF and a "
            "dependency manifest under D-P6-003 and D-P6-004",
            "Phase 6 advances from 1/5 to 2/5",
            "Publication uses paths relative to an open directory descriptor",
            "It can only add an absent member and never overwrites",
            "After a process stop, start the application again and "
            "independently validate the destination",
            "This acceptance does not cover arbitrary interruption between "
            "bytecode instructions",
            "Never delete, rename, rewrite, truncate, replace, or manually "
            "change an existing published final file",
            "The output keeps its private-development status and project "
            "status stays `unknown`",
            "This decision gives no authority for Exits 1, 4, or 5",
            "risk downgrade",
        ),
    )
    expected_acceptance_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#phase-6-exit-3-supported-model-evidence-admission-panel"
    )
    require(
        acceptance_record["evidence"] == expected_acceptance_panel
        and acceptance_record["panel_record"]
        == expected_acceptance_panel,
        "D-P6-005 panel routing drifted",
    )

    risks = json.loads(documents["risks"])["risks"]
    by_id = {record["id"]: record for record in risks}
    expected_risks = {
        "PR-09": ("Critical", "Remove", "Partial"),
        "PR-13": (
            "Critical",
            "Mitigate",
            "Effective (current scope)",
        ),
        "PR-16": ("High", "Mitigate", "Partial"),
        "PR-22": ("High", "Remove", "Effective (current scope)"),
        "QA-R03": ("High", "Remove", "Partial"),
    }
    for risk_id, expected in expected_risks.items():
        record = by_id[risk_id]
        actual = (
            record["severity"],
            record["treatment"],
            record["control_effectiveness"],
        )
        require(actual == expected, f"{risk_id} disposition changed")


def validate_lfe(documents: dict[str, str]) -> None:
    """Protect the append-only ledger and D-P6-004 lesson routing."""
    rows = re.findall(
        r"^\| LFE-(\d{3}) .*\|$",
        documents["learning"],
        re.MULTILINE,
    )
    require(
        rows == [f"{value:03d}" for value in range(1, 23)],
        "LFE identifiers are not unique, ordered and append-only through 022",
    )
    row_lines = [
        line
        for line in documents["learning"].splitlines()
        if re.match(r"^\| LFE-\d{3} ", line)
    ]
    protected_prefix = "\n".join(row_lines[:16]) + "\n"
    actual_hash = hashlib.sha256(protected_prefix.encode("utf-8")).hexdigest()
    require(
        actual_hash == LFE_001_TO_016_SHA256,
        "an earlier LFE row was modified, renumbered or removed",
    )
    lfe = row_lines[16]
    require_fragments(
        "LFE-017",
        lfe,
        (
            "material descriptor, advisory-lock, recoverability and "
            "diagnostic defects",
            "arbitrary-`BaseException` ownership-transfer micro-windows",
            "did not demonstrate deletion, overwrite, corruption or unsafe "
            "mutation",
            "ARCHITECTURE.md#supported-exporter-failure-model",
            "VALIDATION.md#supported-exporter-interruption-evidence",
            "RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-"
            "export",
            "current/PHASE_EVIDENCE.md#phase-6-exporter-fault-model-"
            "clarification-panel",
            "Define the supported fault model before claiming failure safety",
            "do not turn every arbitrary instruction-level interruption probe "
            "into a release blocker",
            "operating-system process boundary",
        ),
    )


def validate_documents(documents: dict[str, str]) -> None:
    """Validate all exporter fault-model governance controls."""
    validate_canonical_sections(documents)
    validate_skill_routing(documents)
    validate_current_authority(documents)
    validate_lfe(documents)


def require_mutation_rejected(
    documents: dict[str, str],
    key: str,
    original: str,
    replacement: str,
    label: str,
) -> None:
    """Require one representative semantic mutation to fail closed."""
    require(original in documents[key], f"mutation target drifted: {label}")
    mutated = dict(documents)
    mutated[key] = mutated[key].replace(original, replacement, 1)
    try:
        validate_documents(mutated)
    except (AssertionError, KeyError, json.JSONDecodeError):
        return
    raise AssertionError(f"governance mutation escaped: {label}")


def validate_mutations(documents: dict[str, str]) -> None:
    """Exercise deletion, inversion and authority-widening mutations."""
    mutations = (
        (
            "architecture",
            "#### Supported exporter failure model",
            "#### Removed exporter failure model",
            "canonical heading deletion",
        ),
        (
            "architecture",
            "requires a further\nLevel 3 project-owner decision",
            "requires no further\nLevel 3 project-owner decision",
            "Level 3 authority inversion",
        ),
        (
            "architecture",
            "research evidence, not automatically",
            "research evidence, automatically",
            "unsupported-probe blocker inversion",
        ),
        (
            "recovery",
            "never grants authority to delete, overwrite",
            "grants authority to delete or overwrite",
            "destructive restart widening",
        ),
        (
            "plan",
            "Phase 6 current — 2/5 accepted exits",
            "Phase 6 current — 3/5 accepted exits",
            "Phase 6 status widening",
        ),
        (
            "evidence",
            "| Export is deterministic and failure-safe | Evidenced and "
            "owner-accepted under D-P6-005",
            "| Export is deterministic and failure-safe | Pending",
            "Exit 3 acceptance deletion",
        ),
        (
            "tracktemplate-change-validation",
            "](" + VALIDATION_LINK + ")",
            "](missing-validation-owner)",
            "skill canonical-link deletion",
        ),
        (
            "tracktemplate-security-review",
            "Do not promote an explicitly unsupported",
            "Promote an explicitly unsupported",
            "security blocker inversion",
        ),
        (
            "tracktemplate-quality-review",
            "description: Perform a staff-level review",
            "description: Review",
            "skill description shortening",
        ),
        (
            "learning",
            "| LFE-017 /",
            "| LFE-016 /",
            "LFE identifier duplication",
        ),
        (
            "learning",
            "ARCHITECTURE.md#supported-exporter-failure-model",
            "ARCHITECTURE.md#missing-fault-model",
            "LFE architecture-link deletion",
        ),
        (
            "decisions",
            "This decision does not accept Exit 3.",
            "This decision accepts Exit 3.",
            "D-P6-004 historical authority widening",
        ),
        (
            "decisions",
            "Never delete, rename, rewrite, truncate, replace",
            "May delete, rename, rewrite, truncate, replace",
            "D-P6-005 destructive recovery widening",
        ),
    )
    for key, original, replacement, label in mutations:
        require_mutation_rejected(
            documents,
            key,
            original,
            replacement,
            label,
        )


def main() -> None:
    documents = load_documents()
    validate_documents(documents)
    validate_mutations(documents)
    print("Exporter fault-model governance validation passed")


if __name__ == "__main__":
    main()
