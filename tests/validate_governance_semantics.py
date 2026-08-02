#!/usr/bin/env python3
"""Adversarial checks for localised product-governance validators."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Callable

import validate_agent_guidance as agent_guidance
import validate_ontology as ontology
import validate_project_progress as progress


ROOT = Path(__file__).resolve().parents[1]
RESULT_PREFIX = "TRACKTEMPLATE_GOVERNANCE_MUTATION="
RESULTS: list[dict[str, str]] = []
PROTECTIONS: set[str] = set()


def read(relative_path: str) -> str:
    """Read one retained governance input."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str) -> str:
    """Replace exactly one mutation target."""
    if text.count(old) != 1:
        raise AssertionError(
            "mutation target must occur once, found {}: {!r}".format(
                text.count(old),
                old,
            )
        )
    return text.replace(old, new, 1)


def paragraph_containing(text: str, marker: str) -> str:
    """Return the raw Markdown paragraph containing one marker."""
    for match in re.finditer(
        r"(?:\A|\n\n)(.*?)(?=\n\n|\Z)",
        text,
        re.DOTALL,
    ):
        paragraph = match.group(1)
        if marker in paragraph:
            return paragraph
    raise AssertionError("paragraph mutation marker not found: " + marker)


def list_item_containing(text: str, marker: str) -> str:
    """Return one raw top-level Markdown list item and its wrapped lines."""
    for match in re.finditer(
        r"^- .*?(?=^- |\n\n|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    ):
        item = match.group(0).rstrip("\n")
        if marker in item:
            return item
    raise AssertionError("list-item mutation marker not found: " + marker)


def table_row_containing(text: str, marker: str) -> str:
    """Return one raw Markdown table row."""
    for line in text.splitlines():
        if line.startswith("|") and marker in line:
            return line
    raise AssertionError("table-row mutation marker not found: " + marker)


def blockquote_paragraph_containing(text: str, marker: str) -> str:
    """Return one contiguous non-empty Markdown blockquote paragraph."""
    lines = text.splitlines(keepends=True)
    for start, line in enumerate(lines):
        if line.startswith(">") and marker in line:
            end = start + 1
            while (
                end < len(lines)
                and lines[end].startswith(">")
                and lines[end].strip() != ">"
            ):
                end += 1
            return "".join(lines[start:end]).rstrip("\n")
    raise AssertionError("blockquote mutation marker not found: " + marker)


def expect_rejected(
    name: str,
    validator: Callable[[], None],
    expected_diagnostic: str,
    protection: str | None = None,
) -> None:
    """Require one in-memory semantic mutation to fail for its owning check."""
    try:
        validator()
    except AssertionError as error:
        diagnostic = str(error)
        if expected_diagnostic not in diagnostic:
            raise AssertionError(
                "{} failed for the wrong reason: {!r}".format(name, diagnostic)
            ) from error
        result = {
            "diagnostic": expected_diagnostic,
            "mutation": name,
            "protection": protection or name,
            "result": "rejected",
        }
        PROTECTIONS.add(result["protection"])
        RESULTS.append(result)
        print(RESULT_PREFIX + json.dumps(result, sort_keys=True))
        return
    raise AssertionError(name + " escaped its semantic validator")


def validate_product_vision_mutations() -> None:
    """Reject deletion, inversion, substitution and unrelated relocation."""
    vision = read("reference/PRODUCT_VISION.md")
    paragraph = paragraph_containing(vision, "Product vision directs work")
    diagnostic = "Product Vision lost its local direction-without-authority clause"
    cases = {
        "product-vision/deleted-authority-clause": replace_once(
            vision,
            paragraph,
            "This document records the long-term product direction.",
        ),
        "product-vision/semantic-inversion": replace_once(
            vision,
            "does not independently authorise",
            "independently authorises",
        ),
        "product-vision/authority-substitution": replace_once(
            vision,
            "Product vision directs work",
            "Repository source directs work",
        ),
        "product-vision/unrelated-relocation": (
            replace_once(vision, paragraph, "Product purpose is recorded here.")
            + "\n\n## Unrelated vocabulary\n\n"
            + paragraph
            + "\n"
        ),
    }
    for name, mutated in cases.items():
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_product_vision(value),
            diagnostic,
        )

    reordered = replace_once(
        replace_once(
            replace_once(
                vision,
                "1. this canonical product vision;",
                "__VISION_AUTHORITY_ITEM__",
            ),
            "2. accepted architectural invariants;",
            "1. accepted architectural invariants;",
        ),
        "__VISION_AUTHORITY_ITEM__",
        "2. this canonical product vision;",
    )
    expect_rejected(
        "product-vision/reordered-authority-hierarchy",
        lambda: progress._validate_product_vision(reordered),
        "Product Vision authority hierarchy or ordering drifted",
    )

    link_diagnostic = "Product Vision authority links or destinations drifted"
    for name, mutated in (
        (
            "product-vision/architecture-label-wrong-existing-target",
            replace_once(
                vision,
                "[ARCHITECTURE.md](ARCHITECTURE.md)",
                "[ARCHITECTURE.md](TERMINOLOGY.md)",
            ),
        ),
        (
            "product-vision/architecture-label-wrong-authority-target",
            replace_once(
                vision,
                "[ARCHITECTURE.md](ARCHITECTURE.md)",
                "[ARCHITECTURE.md](PROJECT_PLAN.md)",
            ),
        ),
        (
            "product-vision/architecture-link-destination-omitted",
            replace_once(
                vision,
                "[ARCHITECTURE.md](ARCHITECTURE.md)",
                "ARCHITECTURE.md",
            ),
        ),
    ):
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_product_vision(value),
            link_diagnostic,
            protection="product-vision/authority-link-association",
        )

    analogy = paragraph_containing(vision, "Templot is the closest")
    nested_analogy = replace_once(
        replace_once(
            vision,
            analogy,
            "The product analogy remains bounded.",
        ),
        "## Vision and execution authority",
        "### Unrelated analogy vocabulary\n\n"
        + analogy
        + "\n\n## Vision and execution authority",
    )
    expect_rejected(
        "product-vision/templot-clause-in-unrelated-nested-section",
        lambda: progress._validate_product_vision(nested_analogy),
        "Product Vision lost its bounded Templot analogy",
    )


def validate_architecture_mutations() -> None:
    """Keep one complete D-GOV-005 record inside its owning table."""
    architecture = read("reference/ARCHITECTURE.md")
    row = table_row_containing(architecture, "D-GOV-005-B")
    record_diagnostic = "architecture D-GOV-005-B semantic record drifted"
    set_diagnostic = "architecture D-GOV-005 clause set or ordering drifted"
    cases = (
        (
            "architecture/deleted-record",
            replace_once(architecture, row + "\n", ""),
            set_diagnostic,
        ),
        (
            "architecture/semantic-inversion",
            replace_once(
                architecture,
                "no shared renderer is claimed",
                "a shared renderer is delivered",
            ),
            record_diagnostic,
        ),
        (
            "architecture/authority-substitution",
            replace_once(
                architecture,
                "Canonical state feeds railway geometry",
                "Coin scene state feeds railway geometry",
            ),
            record_diagnostic,
        ),
        (
            "architecture/unrelated-relocation",
            (
                replace_once(architecture, row + "\n", "")
                + "\n## Unrelated implementation notes\n\n"
                + row
                + "\n"
            ),
            set_diagnostic,
        ),
    )
    for name, mutated, diagnostic in cases:
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_architecture_direction(value),
            diagnostic,
        )
    next_row = table_row_containing(architecture, "D-GOV-005-C")
    reordered = replace_once(
        replace_once(
            replace_once(architecture, row, "__ARCHITECTURE_ROW__"),
            next_row,
            row,
        ),
        "__ARCHITECTURE_ROW__",
        next_row,
    )
    expect_rejected(
        "architecture/reordered-decision-records",
        lambda: progress._validate_architecture_direction(reordered),
        set_diagnostic,
    )

    nested_relocation = replace_once(architecture, row + "\n", "")
    nested_relocation = replace_once(
        nested_relocation,
        "## Target layers",
        "### Unrelated implementation table\n\n"
        "| Clause | Accepted direction | Implementation boundary retained |\n"
        "| --- | --- | --- |\n"
        + row
        + "\n\n## Target layers",
    )
    expect_rejected(
        "architecture/decision-row-in-unrelated-nested-table",
        lambda: progress._validate_architecture_direction(nested_relocation),
        set_diagnostic,
    )

    row_g = table_row_containing(architecture, "D-GOV-005-G")
    extra_h = row_g.replace(
        "D-GOV-005-G — product horizons",
        "D-GOV-005-H — delivered Layout Editor",
    ).replace(
        "TrackTemplate Core migration is the current programme; TrackTemplate "
        "Layout Editor is a subsequent programme.",
        "Maps, connected placement and layout solving are delivered and "
        "authorised for accepted Phase 6.",
    ).replace(
        "Future extension direction does not alter an active phase or authorise "
        "Layout Editor implementation.",
        "Phase 6 is accepted and future implementation is authorised.",
    )
    expect_rejected(
        "architecture/unexpected-d-gov-005-h-delivery-clause",
        lambda: progress._validate_architecture_direction(
            replace_once(architecture, row_g, row_g + "\n" + extra_h)
        ),
        set_diagnostic,
    )


def validate_capability_matrix_mutations() -> None:
    """Keep legacy, Addon and future meanings in their owning units."""
    matrix = read("reference/CAPABILITY_MATRIX.md")
    evidence_paragraph = paragraph_containing(
        matrix,
        "A legacy\n`C` does not mean",
    )
    addon_paragraph = paragraph_containing(matrix, "The Addon column describes")
    cases = (
        (
            "capability-matrix/deleted-legacy-limit",
            replace_once(
                matrix,
                evidence_paragraph,
                evidence_paragraph.split(" A legacy", 1)[0] + ".",
            ),
            "capability matrix lost its legacy-to-Addon evidence limit",
        ),
        (
            "capability-matrix/semantic-inversion",
            replace_once(matrix, "does not mean", "proves"),
            "capability matrix lost its legacy-to-Addon evidence limit",
        ),
        (
            "capability-matrix/authority-substitution",
            replace_once(
                matrix,
                "The Addon column describes",
                "The legacy column describes",
            ),
            "capability matrix lost its local Addon-status authority clause",
        ),
        (
            "capability-matrix/unrelated-relocation",
            (
                replace_once(matrix, addon_paragraph, "Addon status is tabulated.")
                + "\n\n## Unrelated glossary\n\n"
                + addon_paragraph
                + "\n"
            ),
            "capability matrix lost its local Addon-status authority clause",
        ),
    )
    for name, mutated, diagnostic in cases:
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_capability_matrix(value),
            diagnostic,
        )

    nested_authority = replace_once(
        matrix,
        addon_paragraph,
        "Addon status is tabulated in the governing matrix.",
    )
    nested_authority = replace_once(
        nested_authority,
        "## Status vocabulary",
        "### Unrelated glossary\n\n"
        + addon_paragraph
        + "\n\n## Status vocabulary",
    )
    expect_rejected(
        "capability-matrix/addon-authority-in-unrelated-nested-glossary",
        lambda: progress._validate_capability_matrix(nested_authority),
        "capability matrix lost its local Addon-status authority clause",
    )

    spacing_limit = paragraph_containing(
        matrix,
        "The spacing-matched Entry/Exit row",
    )
    nested_spacing_limit = replace_once(
        matrix,
        spacing_limit,
        "### Unrelated spacing vocabulary\n\n" + spacing_limit,
    )
    expect_rejected(
        "capability-matrix/spacing-limit-in-unrelated-nested-section",
        lambda: progress._validate_capability_matrix(nested_spacing_limit),
        "capability matrix lost its spacing-transition evidence limits",
    )

    row_diagnostic = "capability matrix structured row drifted: "
    set_diagnostic = "capability matrix capability set or ordering drifted"
    general_row = table_row_containing(matrix, "General track widening")
    spacing_row = table_row_containing(
        matrix,
        "Spacing-matched Entry/Exit transitions",
    )
    euler_row = table_row_containing(matrix, "Euler transitions")

    combined_row = (
        "| Track or spacing widening | C — accepted legacy evidence | "
        "P — spacing-transition slice | P | P | P | A | P | "
        "Spacing-transition evidence | Partial |"
    )
    recombined = replace_once(
        matrix,
        general_row + "\n" + spacing_row,
        combined_row,
    )
    expect_rejected(
        "capability-matrix/recombined-widening-and-spacing-rows",
        lambda: progress._validate_capability_matrix(recombined),
        set_diagnostic,
    )

    spacing_absent = replace_once(
        spacing_row,
        "P — fixture-only accepted Entry/Exit slice",
        "A",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-addon-marked-absent",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_absent)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    spacing_unqualified = replace_once(
        spacing_row,
        "P — fixture-only accepted Entry/Exit slice",
        "C",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-addon-unqualified-current",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_unqualified)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    spacing_complete = spacing_row
    for old in (
        "P — fixture-only accepted Entry/Exit slice",
        "P — transition-state v1 records derived from start/curve/finish spacing",
        "P — bounded transition centreline pair only",
        "P — transient transition centrelines only",
        "P — bounded transition records only",
    ):
        spacing_complete = replace_once(spacing_complete, old, "C")
    spacing_complete = replace_once(
        spacing_complete,
        "| Partial |",
        "| Current |",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-promoted-to-complete-modular",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_complete)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    general_promoted = general_row
    for old, new in (
        (
            "A — spacing-transition evidence does not establish general widening",
            "P — fixture-only accepted Entry/Exit slice",
        ),
        (
            "A for general widening",
            "P — spacing-transition evidence",
        ),
    ):
        general_promoted = general_promoted.replace(old, new)
    expect_rejected(
        "capability-matrix/spacing-evidence-applied-to-general-widening",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, general_row, general_promoted)
        ),
        row_diagnostic + "General track widening",
    )

    spacing_export = replace_once(
        spacing_row,
        "A — no accepted modular export",
        "C — accepted modular export",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-modular-export-claimed",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_export)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    spacing_renderer = replace_once(
        spacing_row,
        "P — bounded transition centreline pair only",
        "C — complete shared rail, sleeper and chair renderer",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-full-renderer-claimed",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_renderer)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    spacing_phase_exit = replace_once(
        spacing_row,
        "| Partial |",
        "| Complete — Phase 6 accepted |",
    )
    expect_rejected(
        "capability-matrix/spacing-transition-phase-6-acceptance-claimed",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, spacing_row, spacing_phase_exit)
        ),
        row_diagnostic + "Spacing-matched Entry/Exit transitions",
    )

    euler_renderer = replace_once(
        euler_row,
        "C — accepted bounded centreline view",
        "C — complete shared rail, sleeper and chair renderer",
    )
    expect_rejected(
        "capability-matrix/euler-coin-cell-claims-complete-renderer",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, euler_row, euler_renderer)
        ),
        row_diagnostic + "Euler transitions",
    )


def validate_current_evidence_mutations() -> None:
    """Keep current PR/phase state and decision authority inside the panel."""
    evidence = read("reference/current/PHASE_EVIDENCE.md")
    authority = blockquote_paragraph_containing(
        evidence,
        "Vision supplies direction, not scope",
    )
    authority_diagnostic = (
        "current evidence D-GOV-005 authority block drifted or gained a "
        "competing record"
    )
    cases = (
        (
            "phase-evidence/deleted-authority-clause",
            replace_once(evidence, authority, ""),
            authority_diagnostic,
        ),
        (
            "phase-evidence/semantic-inversion",
            replace_once(
                evidence,
                "Vision supplies direction, not scope",
                "Vision supplies scope, not direction",
            ),
            authority_diagnostic,
        ),
        (
            "phase-evidence/authority-substitution",
            replace_once(
                evidence,
                "D-GOV-004 continues to own literal",
                "D-GOV-005 now owns literal",
            ),
            authority_diagnostic,
        ),
        (
            "phase-evidence/unrelated-relocation",
            (
                replace_once(evidence, authority, "")
                + "\n\n## Unrelated historical note\n\n"
                + authority
                + "\n"
            ),
            authority_diagnostic,
        ),
        (
            "phase-evidence/phase-status-inversion",
            replace_once(
                evidence,
                "Phase 6 remains current at\n0/5",
                "Phase 6 is complete at\n5/5",
            ),
            "current evidence lost its local repository, PR or Phase 6 state clause",
        ),
        (
            "phase-evidence/pr31-status-inversion",
            replace_once(
                evidence,
                "remain separate, unaccepted Phase 6",
                "are accepted Phase 6",
            ),
            "current evidence lost its local repository, PR or Phase 6 state clause",
        ),
    )
    for name, mutated, diagnostic in cases:
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_current_governance_evidence(
                value
            ),
            diagnostic,
        )

    competing_quote = (
        "> **Competing governance authority**\n>\n"
        "> D-GOV-005 supersedes D-GOV-004, Phase 6 is accepted, and Layout\n"
        "> Editor implementation is authorised.\n\n"
    )
    competing_authority = replace_once(
        evidence,
        authority,
        authority + "\n\n" + competing_quote.rstrip(),
    )
    expect_rejected(
        "phase-evidence/competing-contradictory-authority-blockquote",
        lambda: progress._validate_current_governance_evidence(
            competing_authority
        ),
        authority_diagnostic,
    )


def validate_project_plan_mutations() -> None:
    """Keep current/future programme polarity in the dashboard preamble."""
    plan = read("reference/PROJECT_PLAN.md")
    paragraph = paragraph_containing(plan, "The active programme is")
    diagnostic = (
        "project plan lost its local current-programme and future-horizon clause"
    )
    cases = {
        "project-plan/deleted-future-clause": replace_once(
            plan,
            "Future architecture may be recorded\nnow without being implemented now.",
            "",
        ),
        "project-plan/semantic-inversion": replace_once(
            plan,
            "it does not alter Phase 6 exits",
            "it alters Phase 6 exits",
        ),
        "project-plan/authority-substitution": replace_once(
            plan,
            "[PRODUCT_VISION.md](PRODUCT_VISION.md)",
            "[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md)",
        ),
        "project-plan/unrelated-relocation": (
            replace_once(plan, paragraph, "Programme status is recorded below.")
            + "\n\n## Unrelated planning note\n\n"
            + paragraph
            + "\n"
        ),
    }
    for name, mutated in cases.items():
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_plan_programme(value),
            diagnostic,
        )

    wrong_vision_target = replace_once(
        plan,
        "[PRODUCT_VISION.md](PRODUCT_VISION.md)",
        "[PRODUCT_VISION.md](ARCHITECTURE.md)",
    )
    expect_rejected(
        "project-plan/product-vision-label-wrong-existing-target",
        lambda: progress._validate_plan_programme(wrong_vision_target),
        "project plan Product Vision authority link or destination drifted",
    )

    nested_programme = replace_once(
        plan,
        paragraph,
        "### Unrelated programme vocabulary\n\n" + paragraph,
    )
    expect_rejected(
        "project-plan/programme-clause-in-unrelated-nested-section",
        lambda: progress._validate_plan_programme(nested_programme),
        diagnostic,
    )


def validate_agents_mutations() -> None:
    """Reject every removed or abstracted explicit AGENTS safeguard."""
    agents = read("AGENTS.md")
    change_item = list_item_containing(agents, "Do not silently change")
    terminology_item = list_item_containing(agents, "ordinary track")
    safeguard_diagnostic = (
        "AGENTS lost or weakened an explicit no-silent-change safeguard"
    )
    terminology_diagnostic = (
        "AGENTS lost or weakened its explicit terminology-surface boundary"
    )

    for safeguard in (
        "stable identities",
        "stored properties",
        "visibility",
        "transactions",
        "rollback",
        "cache invalidation",
    ):
        expect_rejected(
            "agents/deleted-" + safeguard.replace(" ", "-"),
            lambda value=replace_once(agents, safeguard, ""): (
                agent_guidance.validate_explicit_agent_safeguards(value)
            ),
            safeguard_diagnostic,
        )

    weakenings = {
        "stable identities": "identities",
        "stored properties": "lifecycle state",
        "visibility": "presentation lifecycle",
        "transactions": "lifecycle operations",
        "rollback": "recovery lifecycle",
        "cache invalidation": "cache lifecycle",
    }
    for safeguard, abstraction in weakenings.items():
        expect_rejected(
            "agents/weakened-" + safeguard.replace(" ", "-"),
            lambda old=safeguard, new=abstraction: (
                agent_guidance.validate_explicit_agent_safeguards(
                    replace_once(agents, old, new)
                )
            ),
            safeguard_diagnostic,
            protection=(
                "agents/stored-properties-explicit"
                if safeguard == "stored properties"
                else None
            ),
        )

    for surface in ("prose", "UI", "schemas", "APIs"):
        mutated_item = replace_once(terminology_item, surface, "")
        expect_rejected(
            "agents/deleted-terminology-surface-" + surface.lower(),
            lambda value=replace_once(agents, terminology_item, mutated_item): (
                agent_guidance.validate_explicit_agent_safeguards(value)
            ),
            terminology_diagnostic,
        )

    cases = (
        (
            "agents/semantic-inversion",
            replace_once(
                agents,
                "Do not silently change",
                "Agents may silently change",
            ),
            safeguard_diagnostic,
        ),
        (
            "agents/authority-substitution",
            replace_once(agents, "stored properties", "lifecycle"),
            safeguard_diagnostic,
        ),
        (
            "agents/unrelated-relocation",
            (
                replace_once(agents, change_item, "- Protect lifecycle behaviour.")
                + "\n\n## Unrelated notes\n\n"
                + change_item
                + "\n"
            ),
            safeguard_diagnostic,
        ),
        (
            "agents/terminology-unrelated-relocation",
            (
                replace_once(
                    agents,
                    terminology_item,
                    "- Follow the accepted terminology owner.",
                )
                + "\n\n## Unrelated terminology examples\n\n"
                + terminology_item
                + "\n"
            ),
            terminology_diagnostic,
        ),
    )
    for name, mutated, diagnostic in cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                agent_guidance.validate_explicit_agent_safeguards(value)
            ),
            diagnostic,
            protection=(
                "agents/stored-properties-explicit"
                if name == "agents/authority-substitution"
                else None
            ),
        )

    nested_safeguards = replace_once(
        agents,
        change_item,
        "### Unrelated safeguard vocabulary\n\n" + change_item,
    )
    expect_rejected(
        "agents/safeguards-in-unrelated-nested-section",
        lambda: agent_guidance.validate_explicit_agent_safeguards(
            nested_safeguards
        ),
        safeguard_diagnostic,
    )


def validate_chief_mutations() -> None:
    """Reject highest-value wording without a comparative rationale."""
    chief = read(".agents/skills/tracktemplate-chief-of-staff/SKILL.md")
    workflows = read("reference/AGENT_WORKFLOWS.md")
    explanation = paragraph_containing(chief, "The brief must compare")
    field = list_item_containing(
        chief,
        "Why this outranks maintenance alternatives",
    )
    rationale_diagnostic = "Chief of Staff lost its comparative-rationale rule"
    field_diagnostic = (
        "Chief of Staff brief lost its comparative-priority assignment field"
    )
    cases = (
        (
            "chief/deleted-comparative-field",
            replace_once(chief, field + "\n", ""),
            workflows,
            field_diagnostic,
        ),
        (
            "chief/semantic-inversion",
            replace_once(
                chief,
                "without that comparative rationale is insufficient",
                "without that comparative rationale is sufficient",
            ),
            workflows,
            rationale_diagnostic,
        ),
        (
            "chief/unrelated-priority-substitution",
            replace_once(
                chief,
                "Why this outranks maintenance alternatives",
                "Why this item has general priority",
            ),
            workflows,
            field_diagnostic,
        ),
        (
            "chief/highest-value-without-comparison",
            replace_once(
                replace_once(chief, explanation, ""),
                field + "\n",
                "",
            ),
            workflows,
            rationale_diagnostic,
        ),
        (
            "chief/unrelated-relocation",
            (
                replace_once(
                    replace_once(chief, explanation, ""),
                    field + "\n",
                    "",
                )
                + "\n\n## Unrelated priority vocabulary\n\n"
                + explanation
                + "\n\n"
                + field
                + "\n"
            ),
            workflows,
            rationale_diagnostic,
        ),
    )
    for name, mutated_chief, mutated_workflows, diagnostic in cases:
        expect_rejected(
            name,
            lambda skill=mutated_chief, flow=mutated_workflows: (
                agent_guidance.validate_chief_comparative_priority(skill, flow)
            ),
            diagnostic,
        )

    nested_comparison = replace_once(chief, field + "\n", "")
    nested_comparison = replace_once(
        nested_comparison,
        explanation,
        "### Unrelated priority vocabulary\n\n"
        + explanation
        + "\n\n"
        + field,
    )
    expect_rejected(
        "chief/comparative-contract-in-unrelated-nested-section",
        lambda: agent_guidance.validate_chief_comparative_priority(
            nested_comparison,
            workflows,
        ),
        rationale_diagnostic,
    )

    workflow_mutation = replace_once(
        workflows,
        "compares the selected work with credible maintenance, evidence,\n"
        "risk-reduction and other authorised alternatives;",
        "selects an item labelled highest-value;",
    )
    expect_rejected(
        "chief/workflow-comparison-deleted",
        lambda: agent_guidance.validate_chief_comparative_priority(
            chief,
            workflow_mutation,
        ),
        "AGENT_WORKFLOWS lost the comparative-priority contract",
    )

    workflow_paragraph = paragraph_containing(
        workflows,
        "It is a vision-informed programme orchestrator",
    )
    polarity_diagnostic = (
        "Chief of Staff comparative priority became optional or unnecessary"
    )
    contradictory_sentences = (
        (
            "chief/workflow-comparison-explicitly-optional",
            "Nevertheless, comparison is optional.",
        ),
        (
            "chief/workflow-comparison-may-be-omitted",
            "Comparison may be omitted.",
        ),
        (
            "chief/workflow-highest-value-declared-sufficient",
            "Highest value is sufficient.",
        ),
        (
            "chief/workflow-alternatives-need-not-be-considered",
            "Alternatives need not be considered.",
        ),
    )
    for name, sentence in contradictory_sentences:
        contradictory_workflow = replace_once(
            workflows,
            workflow_paragraph,
            workflow_paragraph + " " + sentence,
        )
        expect_rejected(
            name,
            lambda value=contradictory_workflow: (
                agent_guidance.validate_chief_comparative_priority(chief, value)
            ),
            polarity_diagnostic,
            protection="chief/contradictory-comparison-polarity",
        )


def validate_ontology_mutation() -> None:
    """Reject omission of Product Vision from JSON-LD authority."""
    document = ontology.load_json(ontology.ONTOLOGY_PATH)
    graph = document["@graph"]
    header = next(node for node in graph if node.get("@id") == ontology.ONTOLOGY_ID)
    mutated = copy.deepcopy(header)
    mutated["rdfs:isDefinedBy"] = [
        value
        for value in mutated["rdfs:isDefinedBy"]
        if value.get("@id") != ontology.EXPECTED_AUTHORITY_IDS[0]
    ]
    expect_rejected(
        "ontology/product-vision-authority-omitted",
        lambda: ontology.validate_ontology_authorities(mutated),
        "ontology authority relationship drifted or omitted Product Vision",
    )


def main() -> None:
    """Run every durable in-memory adversarial mutation."""
    validate_product_vision_mutations()
    validate_architecture_mutations()
    validate_capability_matrix_mutations()
    validate_current_evidence_mutations()
    validate_project_plan_mutations()
    validate_agents_mutations()
    validate_chief_mutations()
    validate_ontology_mutation()
    summary = {
        "escaped": 0,
        "independent_protections": len(PROTECTIONS),
        "rejected": len(RESULTS),
        "total_executions": len(RESULTS),
    }
    print(
        "TRACKTEMPLATE_GOVERNANCE_MUTATION_SUMMARY="
        + json.dumps(summary, sort_keys=True, separators=(",", ":"))
    )


if __name__ == "__main__":
    main()
