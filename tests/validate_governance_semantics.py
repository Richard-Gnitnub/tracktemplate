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
import validate_quality_assurance as quality_assurance


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
    """Keep accepted direction and recovery authority in their owning units."""
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

    recovery_cases = (
        (
            "architecture/exit3-recovery-made-destructive",
            replace_once(
                architecture,
                "Recovery authority is\nconstructive, not destructive",
                "Recovery authority is\ndestructive, not constructive",
            ),
        ),
        (
            "architecture/exit3-inert-controls-given-authority",
            replace_once(
                architecture,
                "not opened, parsed, modified, deleted or used to permit or\n"
                "block final-set completion",
                "opened and deleted to permit or\n"
                "block final-set completion",
            ),
        ),
        (
            "architecture/exit3-content-becomes-removal-authority",
            replace_once(
                architecture,
                "it never establishes ownership, deletion or replacement "
                "authority",
                "it establishes ownership, deletion and replacement "
                "authority",
            ),
        ),
        (
            "architecture/exit3-post-link-rollback-reintroduced",
            replace_once(
                architecture,
                "The first successful final link permanently ends rollback",
                "The first successful final link permits pathname rollback",
            ),
        ),
        (
            "architecture/exit3-expected-inode-delete-invented",
            replace_once(
                architecture,
                "POSIX pathname deletion\nhas no expected-inode atomic "
                "condition",
                "POSIX pathname deletion\nhas an expected-inode atomic "
                "condition",
            ),
        ),
        (
            "architecture/exit3-published-final-mutation-authorised",
            replace_once(
                architecture,
                "no published final may thereafter be unlinked, renamed, "
                "rewritten, truncated,\nreplaced",
                "a published final may thereafter be unlinked, renamed, "
                "rewritten, truncated,\nreplaced",
            ),
        ),
        (
            "architecture/exit3-prematurely-accepted",
            replace_once(
                architecture,
                "Exit 3 remains Pending",
                "Exit 3 is accepted",
            ),
        ),
    )
    for name, mutated in recovery_cases:
        expect_rejected(
            name,
            lambda value=mutated: progress._validate_architecture_direction(
                value
            ),
            "architecture D-P6-003 recovery contract drifted",
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

    d_p6_005_deleted = replace_once(
        matrix,
        "D-P6-005 accepts only the bounded\nprivate-development exporter "
        "failure-safety claim.",
        "The exporter evidence is present.",
    )
    expect_rejected(
        "capability-matrix/d-p6-005-boundary-deleted",
        lambda: progress._validate_capability_matrix(d_p6_005_deleted),
        "capability matrix lost its bounded decision boundary",
    )

    clearance_widened = replace_once(
        matrix,
        "Neither decision grants\noutput clearance.",
        "D-P6-005 grants\noutput clearance.",
    )
    expect_rejected(
        "capability-matrix/d-p6-005-grants-output-clearance",
        lambda: progress._validate_capability_matrix(clearance_widened),
        "capability matrix lost its bounded decision boundary",
    )

    dxf_row = table_row_containing(matrix, "| DXF |")
    dxf_safety_deleted = replace_once(
        dxf_row,
        "deterministic output and supported-model failure safety "
        "owner-accepted under D-P6-005",
        "deterministic output",
    )
    expect_rejected(
        "capability-matrix/dxf-supported-safety-deleted",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, dxf_row, dxf_safety_deleted)
        ),
        "capability matrix DXF boundary drifted",
    )

    dxf_clearance_widened = replace_once(
        dxf_row,
        "bounded private-development Entry/Exit route only",
        "production-cleared exporter family",
    )
    expect_rejected(
        "capability-matrix/dxf-scope-widened",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, dxf_row, dxf_clearance_widened)
        ),
        "capability matrix DXF boundary drifted",
    )

    dxf_link_changed = replace_once(
        dxf_row,
        "#phase-6-exit-3-supported-model-evidence-admission-panel",
        "#current-phase-6-exit-condition-disposition",
    )
    expect_rejected(
        "capability-matrix/dxf-evidence-link-changed",
        lambda: progress._validate_capability_matrix(
            replace_once(matrix, dxf_row, dxf_link_changed)
        ),
        "capability matrix DXF evidence routing drifted",
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
        "P — private-development DXF only",
        "C — production-cleared modular export",
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

    plan = read("reference/PROJECT_PLAN.md")
    phase4_closeout = read(
        "reference/history/phase-closeouts/PHASE4_CLOSEOUT.md"
    )
    phase5_closeout = read(
        "reference/history/phase-closeouts/PHASE5_CLOSEOUT.md"
    )
    exit2_row = table_row_containing(
        evidence,
        "Evidenced and owner-accepted under D-P6-002",
    )
    exit2_downgraded = replace_once(
        exit2_row,
        "Evidenced and owner-accepted under D-P6-002",
        "Pending",
    )
    expect_rejected(
        "phase-evidence/exit2-acceptance-downgraded",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(evidence, exit2_row, exit2_downgraded),
        ),
        "Phase 6 exits do not match the accepted 2/5 dispositions",
    )

    exit3_row = table_row_containing(
        evidence,
        "Evidenced and owner-accepted under D-P6-005",
    )
    exit3_downgraded = replace_once(
        exit3_row,
        "Evidenced and owner-accepted under D-P6-005",
        "Pending",
    )
    expect_rejected(
        "phase-evidence/exit3-acceptance-downgraded",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(evidence, exit3_row, exit3_downgraded),
        ),
        "Phase 6 exits do not match the accepted 2/5 dispositions",
    )

    exit3_authority = blockquote_paragraph_containing(
        evidence,
        "At protected `main` `7198b05b6a4b7e4654b7d02d0bad4e5cf627a799`",
    )
    weakened_exit3_authority = replace_once(
        exit3_authority,
        "private-development DXF-and-dependency-manifest route",
        "all production exporter routes",
    )
    expect_rejected(
        "phase-evidence/exit3-authority-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                exit3_authority,
                weakened_exit3_authority,
            ),
        ),
        "D-P6-005 panel exact owner decision drifted or was relocated",
    )

    exit3_limitations = blockquote_paragraph_containing(
        evidence,
        "published finals must never be deleted",
    )
    destructive_exit3_limitations = replace_once(
        exit3_limitations,
        "must never be deleted",
        "may be deleted",
    )
    expect_rejected(
        "phase-evidence/exit3-destructive-recovery-authorised",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                exit3_limitations,
                destructive_exit3_limitations,
            ),
        ),
        "D-P6-005 panel exact owner decision drifted or was relocated",
    )

    recovery_review_row = table_row_containing(
        evidence,
        "required before Exit 3 can be recommended or accepted",
    )
    recovery_review_closed = replace_once(
        recovery_review_row,
        "**Open** — required before Exit 3 can be recommended or accepted",
        "Evidenced — no further review required",
    )
    expect_rejected(
        "phase-evidence/exit3-recovery-review-prematurely-closed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                recovery_review_row,
                recovery_review_closed,
            ),
        ),
        "Exit 3 recovery evidence status drifted or implied acceptance",
    )

    recovery_transaction_row = table_row_containing(
        evidence,
        "no independently trusted creation authority",
    )
    recovery_transaction_accepted = replace_once(
        recovery_transaction_row,
        "**Open technical gap**",
        "Present and accepted as satisfying Exit 3",
    )
    expect_rejected(
        "phase-evidence/exit3-recovery-evidence-self-accepted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                recovery_transaction_row,
                recovery_transaction_accepted,
            ),
        ),
        "Exit 3 recovery evidence status drifted or implied acceptance",
    )

    preexisting_controls_weakened = replace_once(
        evidence,
        "preserved unchanged and rejected as\nunclaimable",
        "parsed and removed when their content matches",
    )
    expect_rejected(
        "phase-evidence/exit3-preexisting-controls-preservation-weakened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            preexisting_controls_weakened,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    interruption_recovery_overclaimed = replace_once(
        evidence,
        "They do not claim automatic recovery",
        "They prove automatic recovery",
    )
    expect_rejected(
        "phase-evidence/exit3-interruption-recovery-overclaimed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            interruption_recovery_overclaimed,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    control_metadata_weakened = replace_once(
        evidence,
        "including access time",
        "excluding access time",
    )
    expect_rejected(
        "phase-evidence/exit3-foreign-control-atime-omitted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            control_metadata_weakened,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    staging_preservation_weakened = replace_once(
        evidence,
        "preserves the foreign directory, every\n"
        "file, their identities, metadata and bytes",
        "may delete the foreign directory or matching files",
    )
    expect_rejected(
        "phase-evidence/exit3-staging-ownership-preservation-weakened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            staging_preservation_weakened,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    staging_creation_ownership_weakened = replace_once(
        evidence,
        "`O_TMPFILE`, captures the device/inode identity immediately from the "
        "descriptor\nreturned by that creation operation",
        "a pathname-created file whose identity is first observed later",
    )
    expect_rejected(
        "phase-evidence/exit3-staging-atomic-ownership-weakened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            staging_creation_ownership_weakened,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    journal_creation_ownership_weakened = replace_once(
        evidence,
        "journal is also created anonymously and linked\nfrom its still-open "
        "descriptor",
        "journal is created at a pathname and reopened later",
    )
    expect_rejected(
        "phase-evidence/exit3-journal-atomic-ownership-weakened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            journal_creation_ownership_weakened,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    staging_path_cleanup_reintroduced = replace_once(
        evidence,
        "Normal stage cleanup is descriptor close; there is no staging "
        "pathname or\ndirectory removal",
        "Normal stage cleanup removes a pathname-created directory",
    )
    expect_rejected(
        "phase-evidence/exit3-staging-path-cleanup-reintroduced",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            staging_path_cleanup_reintroduced,
        ),
        "Phase 6 staging-ownership repair evidence drifted",
    )

    inert_controls_trusted = replace_once(
        evidence,
        "presence\nneither permits nor blocks final-set completion",
        "presence\nauthorises deletion and blocks final-set completion",
    )
    expect_rejected(
        "phase-evidence/exit3-inert-controls-given-authority",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            inert_controls_trusted,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    equality_becomes_deletion_authority = replace_once(
        evidence,
        "Content equivalence\n"
        "establishes compatibility for reuse or addition only; it never "
        "grants\nownership, deletion or replacement authority",
        "Content equivalence establishes ownership\n"
        "and grants deletion and replacement authority",
    )
    expect_rejected(
        "phase-evidence/exit3-equality-becomes-deletion-authority",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            equality_becomes_deletion_authority,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    post_link_rollback_reintroduced = replace_once(
        evidence,
        "Pathname-based rollback ends permanently at the first successful "
        "final\n   link",
        "Pathname-based rollback remains available after the first successful "
        "final\n   link",
    )
    expect_rejected(
        "phase-evidence/exit3-post-link-rollback-reintroduced",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            post_link_rollback_reintroduced,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    expected_inode_delete_invented = replace_once(
        evidence,
        "POSIX pathname deletion has no expected-inode atomic condition",
        "POSIX pathname deletion has an expected-inode atomic condition",
    )
    expect_rejected(
        "phase-evidence/exit3-expected-inode-delete-invented",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            expected_inode_delete_invented,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    published_mutation_authorised = replace_once(
        evidence,
        "No published final file may be unlinked, renamed, rewritten, "
        "truncated,\n   replaced",
        "A published final file may be unlinked, renamed, rewritten, "
        "truncated,\n   replaced",
    )
    expect_rejected(
        "phase-evidence/exit3-published-final-mutation-authorised",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            published_mutation_authorised,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    race_cleanup_authorised = replace_once(
        evidence,
        "A race discovered after an addition leaves every published file "
        "untouched",
        "A race discovered after an addition permits published-file cleanup",
    )
    expect_rejected(
        "phase-evidence/exit3-race-cleanup-authorised",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            race_cleanup_authorised,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    zero_member_recovery_excluded = replace_once(
        evidence,
        "an independently revalidated exact zero-member, partial or complete "
        "destination",
        "an independently revalidated exact partial or complete destination",
    )
    expect_rejected(
        "phase-evidence/exit3-zero-member-recovery-excluded",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            zero_member_recovery_excluded,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    partial_completion_withdrawn = replace_once(
        evidence,
        "an exact regular partial pair may be completed instead of rejected",
        "an exact regular partial pair must remain unrecoverable",
    )
    expect_rejected(
        "phase-evidence/exit3-monotonic-completion-withdrawn",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            partial_completion_withdrawn,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    owner_choice_reopened = replace_once(
        evidence,
        "No material owner choice\nremains",
        "A material owner choice\nremains",
    )
    expect_rejected(
        "phase-evidence/exit3-owner-choice-reopened-after-decision",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            owner_choice_reopened,
        ),
        "D-P6-003 recovery-authority contract or status boundary drifted",
    )

    implementation_uses_post_link_rollback = replace_once(
        evidence,
        "no\npost-publication rollback, journal cleanup or final-path unlink "
        "route",
        "a\npost-publication rollback and final-path unlink route",
    )
    expect_rejected(
        "phase-evidence/exit3-implementation-reintroduces-final-unlink",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            implementation_uses_post_link_rollback,
        ),
        "Phase 6 add-only recovery implementation evidence drifted",
    )

    implementation_trusts_historical_controls = replace_once(
        evidence,
        "Historical journals, `.new` files\nand stage directories are inert",
        "Historical journals, `.new` files\nand stage directories are trusted",
    )
    expect_rejected(
        "phase-evidence/exit3-implementation-trusts-historical-controls",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            implementation_trusts_historical_controls,
        ),
        "Phase 6 add-only recovery implementation evidence drifted",
    )

    implementation_hash_tampered = replace_once(
        evidence,
        "6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd861",
        "6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd860",
    )
    expect_rejected(
        "phase-evidence/exit3-implementation-output-hash-tampered",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            implementation_hash_tampered,
        ),
        "Phase 6 add-only recovery implementation evidence drifted",
    )

    implementation_review_closed = replace_once(
        evidence,
        "Condition 6 remains open",
        "Condition 6 is closed",
    )
    expect_rejected(
        "phase-evidence/exit3-implementation-review-prematurely-closed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            implementation_review_closed,
        ),
        "Phase 6 add-only recovery implementation evidence drifted",
    )

    exit4_row = table_row_containing(
        evidence,
        "D-GOV-008 accepts the PR #50 FreeCAD 1.1.3 series as the comparison "
        "baseline",
    )
    exit4_promoted = replace_once(
        exit4_row,
        "Pending — D-GOV-008 accepts the PR #50 FreeCAD 1.1.3 series",
        "Evidenced — D-GOV-008 accepts the PR #50 FreeCAD 1.1.3 series",
    )
    expect_rejected(
        "phase-evidence/exit4-prematurely-evidenced",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(evidence, exit4_row, exit4_promoted),
        ),
        "Phase 6 exits do not match the accepted 2/5 dispositions",
    )

    performance_promoted = replace_once(
        evidence,
        "this evidence does not satisfy Exit 4, which remains Pending",
        "this evidence satisfies Exit 4",
    )
    expect_rejected(
        "phase-evidence/performance-evidence-promoted-to-exit4",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            performance_promoted,
        ),
        "Phase 6 performance evidence boundary drifted",
    )

    current_performance = progress._section(
        evidence,
        "Performance evidence on FreeCAD 1.1.3",
    )
    cross_host_improvement_claimed = replace_once(
        current_performance,
        "cannot use the difference",
        "can use the difference",
    )
    expect_rejected(
        "phase-evidence/current-performance-cross-host-improvement-claimed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                current_performance,
                cross_host_improvement_claimed,
            ),
        ),
        "current FreeCAD 1.1.3 performance evidence drifted: cannot use the "
        "difference between these reports to claim that TrackTemplate "
        "performance became better",
    )

    current_performance_admitted = replace_once(
        current_performance,
        "admits no evidence for",
        "admits evidence for",
    )
    expect_rejected(
        "phase-evidence/current-performance-prematurely-admitted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                current_performance,
                current_performance_admitted,
            ),
        ),
        "current FreeCAD 1.1.3 performance evidence drifted: admits no "
        "evidence for Exit 4",
    )

    transaction_condition = table_row_containing(
        evidence,
        "Provide atomic durable commit",
    )
    weakened_transaction_condition = replace_once(
        transaction_condition,
        "atomic durable commit or an explicit recoverable transaction protocol",
        "best-effort sequential commit",
    )
    expect_rejected(
        "phase-evidence/exit3-transaction-condition-weakened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                transaction_condition,
                weakened_transaction_condition,
            ),
        ),
        "Exit 3 required-before-exit conditions drifted",
    )

    recommendation_inverted = replace_once(
        evidence,
        "**Panel recommendation:** Exit 2 was **Proceed with bounded conditions**",
        "**Panel recommendation:** Exit 2 was **Do not proceed**",
    )
    expect_rejected(
        "phase-evidence/exit2-panel-recommendation-inverted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            recommendation_inverted,
        ),
        "D-P6-002 panel recommendation drifted",
    )

    exit2_authority = blockquote_paragraph_containing(
        evidence,
        "At accepted `main` source state",
    )
    authority_removed = replace_once(evidence, exit2_authority, "")
    authority_relocated = replace_once(
        authority_removed,
        '<a id="phase-6-exits-2-and-3-evidence-admission-panel"></a>',
        exit2_authority
        + "\n\n"
        + '<a id="phase-6-exits-2-and-3-evidence-admission-panel"></a>',
    )
    expect_rejected(
        "phase-evidence/exit2-owner-authority-relocated-outside-panel",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            authority_relocated,
        ),
        "D-P6-002 panel exact owner decision drifted or was relocated",
    )

    compatibility_section = progress._section(
        evidence,
        "FreeCAD 1.1.3 compatibility requalification panel and owner decision",
    )

    freecad_scope_widened = replace_once(
        evidence,
        "FreeCAD 1.1.2 and all other releases are not qualified.",
        "All FreeCAD 1.1.x releases are qualified.",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-host-scope-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            freecad_scope_widened,
        ),
        "D-GOV-006 evidence panel drifted: FreeCAD 1.1.2 and all other "
        "releases are not qualified",
    )

    freecad_state = blockquote_paragraph_containing(
        compatibility_section,
        "Phase 6 stays at 2/5",
    )
    freecad_phase_advanced = replace_once(
        freecad_state,
        "Phase 6 stays at 2/5",
        "Phase 6 advances to 3/5",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-phase-authority-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                freecad_state,
                freecad_phase_advanced,
            ),
        ),
        "D-GOV-006 owner decision changed phase or exit authority",
    )

    security_endorsement_added = replace_once(
        evidence,
        "That decision is not a security endorsement.",
        "That decision is a security endorsement.",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-security-endorsement-added",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            security_endorsement_added,
        ),
        "D-GOV-006 official host security boundary drifted: not a security "
        "endorsement",
    )

    incomplete_command_hidden = replace_once(
        evidence,
        "The `--pass`\noption had no argument.",
        "The documented separated command failed.",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-incomplete-command-hidden",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            incomplete_command_hidden,
        ),
        "D-GOV-006 qualification provenance drifted: --pass option had no "
        "argument",
    )

    compatibility_conformance_widened = replace_once(
        evidence,
        "Issue 9 conformance stays Unknown\nfor live prose outside the "
        "TT-DOC-001, TT-DOC-002, and D-GOV-006 tables.",
        "Issue 9 conformance is verified\nfor all live prose.",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-conformance-scope-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            compatibility_conformance_widened,
        ),
        "D-GOV-006 Issue 9 result or limitation drifted: Unknown for live "
        "prose outside the TT-DOC-001, TT-DOC-002, and D-GOV-006 tables",
    )

    compatibility_review_inverted = replace_once(
        evidence,
        "reviewer found no host-compatibility defect.",
        "reviewer found a host-compatibility defect.",
    )
    expect_rejected(
        "phase-evidence/d-gov-006-review-defect-inverted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            compatibility_review_inverted,
        ),
        "D-GOV-006 independent review state drifted: reviewer found no "
        "host-compatibility defect",
    )

    performance_host_section = progress._section(
        evidence,
        "Panel and owner decision about hosts for Phase 6 performance "
        "evidence",
    )
    mixed_hosts_allowed = replace_once(
        performance_host_section,
        "It\nalso rejects a result set that contains two host profiles.",
        "It\nalso accepts a result set that contains two host profiles.",
    )
    expect_rejected(
        "phase-evidence/d-gov-007-mixed-host-results-allowed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                performance_host_section,
                mixed_hosts_allowed,
            ),
        ),
        "D-GOV-007 evidence panel drifted: rejects a result set that "
        "contains two host profiles",
    )

    future_host_auto_admitted = replace_once(
        performance_host_section,
        "If the project qualifies a subsequent host profile, this does not "
        "authorise\nperformance evidence from that profile.",
        "If the project qualifies a subsequent host profile, this "
        "automatically authorises\nperformance evidence from that profile.",
    )
    expect_rejected(
        "phase-evidence/d-gov-007-future-host-auto-admitted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                performance_host_section,
                future_host_auto_admitted,
            ),
        ),
        "D-GOV-007 evidence panel drifted: project qualifies a subsequent "
        "host profile, this does not authorise performance evidence from "
        "that profile",
    )

    performance_exit_accepted = replace_once(
        performance_host_section,
        "It does not accept Exit 4, define a value for a performance budget",
        "It accepts Exit 4 and defines a value for a performance budget",
    )
    expect_rejected(
        "phase-evidence/d-gov-007-exit4-accepted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                performance_host_section,
                performance_exit_accepted,
            ),
        ),
        "D-GOV-007 evidence panel drifted: does not accept Exit 4",
    )

    owner_future_boundary = blockquote_paragraph_containing(
        performance_host_section,
        "If the project qualifies a subsequent host profile",
    )
    owner_future_auto_authorised = replace_once(
        owner_future_boundary,
        "this does not authorise",
        "this authorises",
    )
    expect_rejected(
        "phase-evidence/d-gov-007-owner-future-host-auto-authorised",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                owner_future_boundary,
                owner_future_auto_authorised,
            ),
        ),
        "D-GOV-007 quoted owner decision drifted: project qualifies a "
        "subsequent host profile, this does not authorise performance "
        "evidence from that profile",
    )

    owner_clearance_boundary = blockquote_paragraph_containing(
        performance_host_section,
        "This decision gives no production",
    )
    owner_clearance_added = replace_once(
        owner_clearance_boundary,
        "gives no production",
        "gives production",
    )
    expect_rejected(
        "phase-evidence/d-gov-007-owner-clearance-added",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(
                evidence,
                performance_host_section,
                replace_once(
                    performance_host_section,
                    owner_clearance_boundary,
                    owner_clearance_added,
                ),
            ),
        ),
        "D-GOV-007 evidence panel drifted: gives no production, "
        "physical-output, project-cleared, packaging, release, or tagging "
        "authority",
    )

    performance_sop = read("reference/PERFORMANCE_SOP.md")
    validation = read("reference/VALIDATION.md")
    automatic_host_sop = replace_once(
        performance_sop,
        "If the project qualifies a subsequent host profile, this does not "
        "authorise\nperformance evidence from that profile.",
        "If the project qualifies a subsequent host profile, this authorises"
        "\nperformance evidence from that profile.",
    )
    expect_rejected(
        "performance-sop/future-host-auto-admitted",
        lambda: progress._validate_performance_host_sources(
            automatic_host_sop,
            validation,
        ),
        "PERFORMANCE_SOP performance host boundary drifted: project qualifies "
        "a subsequent host profile, this does not authorise performance "
        "evidence from that profile",
    )

    cross_host_sop = replace_once(
        performance_sop,
        "compare results from one\nexact host profile",
        "compare results from two\ndifferent host profiles",
    )
    expect_rejected(
        "performance-sop/cross-host-product-comparison-authorised",
        lambda: progress._validate_performance_host_sources(
            cross_host_sop,
            validation,
        ),
        "PERFORMANCE_SOP performance host boundary drifted: one exact host "
        "profile",
    )

    host_effect_hidden = replace_once(
        performance_sop,
        "only if\nit independently shows the effect of the host profile and "
        "the TrackTemplate\neffect.",
        "without\nshowing the effect of the host profile or the TrackTemplate"
        "\neffect.",
    )
    expect_rejected(
        "performance-sop/cross-host-effect-not-separated",
        lambda: progress._validate_performance_host_sources(
            host_effect_hidden,
            validation,
        ),
        "PERFORMANCE_SOP performance host boundary drifted: independently "
        "shows the effect of the host profile and the TrackTemplate effect",
    )

    historical_host_identity_lost = replace_once(
        performance_sop,
        "These data identify the exact host profile\nfor FreeCAD 1.1.1.",
        "These data do not identify the exact host profile\nfor FreeCAD 1.1.1.",
    )
    expect_rejected(
        "performance-sop/historical-host-identity-lost",
        lambda: progress._validate_performance_host_sources(
            historical_host_identity_lost,
            validation,
        ),
        "PERFORMANCE_SOP performance host boundary drifted: identify the exact "
        "host profile for FreeCAD 1.1.1",
    )

    evidence_schema_downgraded = replace_once(
        performance_sop,
        "The `schema_version` value is `2`",
        "The `schema_version` value is `1`",
    )
    expect_rejected(
        "performance-sop/new-evidence-schema-downgraded",
        lambda: progress._validate_performance_host_sources(
            evidence_schema_downgraded,
            validation,
        ),
        "PERFORMANCE_SOP performance schema boundary drifted: schema_version "
        "value is 2",
    )

    diagnostic_admitted = replace_once(
        validation,
        "The previous 1.1.1-only validator rejected the 1.1.3 test result. "
        "D-GOV-007\ndoes not admit this test result as Exit 4 evidence",
        "The previous 1.1.1-only validator rejected the 1.1.3 test result. "
        "D-GOV-007\nadmits this test result as Exit 4 evidence",
    )
    expect_rejected(
        "validation/d-gov-007-diagnostic-run-admitted",
        lambda: progress._validate_performance_host_sources(
            performance_sop,
            diagnostic_admitted,
        ),
        "VALIDATION admitted the rejected 1.1.3 test result",
    )

    terminology = read("reference/TERMINOLOGY.md")
    paired_difference_orientation_inverted = replace_once(
        terminology,
        "A **paired difference** is the candidate value minus the baseline "
        "value in one paired block.",
        "A **paired difference** is the baseline value minus the candidate "
        "value in one paired block.",
    )
    expect_rejected(
        "performance-direction/paired-difference-orientation-inverted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            paired_difference_orientation_inverted,
            evidence,
        ),
        "D-GOV-008 performance terminology meaning drifted: A paired "
        "difference is the candidate value minus the baseline value in one "
        "paired block",
    )

    even_median_definition_inverted = replace_once(
        terminology,
        "If an ordered sample has an even number of values, its median is the "
        "sum of the two middle values divided by two.",
        "If an ordered sample has an even number of values, its median is the "
        "lower middle value.",
    )
    expect_rejected(
        "performance-direction/even-median-lower-middle-selected",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            even_median_definition_inverted,
            evidence,
        ),
        "D-GOV-008 performance terminology meaning drifted: If an ordered "
        "sample has an even number of values, its median is the sum of the two "
        "middle values divided by two",
    )

    high_water_definition_inverted = replace_once(
        terminology,
        "**High-water RSS** is the maximum RSS that the profiler records.",
        "**High-water RSS** is the minimum RSS that the profiler records.",
    )
    expect_rejected(
        "performance-direction/high-water-definition-inverted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            high_water_definition_inverted,
            evidence,
        ),
        "D-GOV-008 performance terminology meaning drifted: High-water RSS "
        "is the maximum RSS that the profiler records",
    )

    direction_sample_count_weakened = replace_once(
        performance_sop,
        "The Level 2 cycle must use 12 paired blocks.",
        "The Level 2 cycle may use one sample.",
    )
    expect_rejected(
        "performance-direction/paired-sample-rule-weakened",
        lambda: progress._validate_performance_direction_sources(
            direction_sample_count_weakened,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: must use 12 paired blocks",
    )

    direction_product_boundary_widened = replace_once(
        performance_sop,
        "  `tracktemplate/domain/alignment.py`\n",
        "  `tracktemplate/domain/alignment.py`\n"
        "- `tracktemplate/product/preview_cache.py`\n",
    )
    expect_rejected(
        "performance-direction/product-boundary-widened",
        lambda: progress._validate_performance_direction_sources(
            direction_product_boundary_widened,
            terminology,
            evidence,
        ),
        "D-GOV-008 authorised product path set drifted",
    )

    direction_displaced_cost_allowed = replace_once(
        performance_sop,
        "The candidate must add no work to Validate, Export, a warm cycle, "
        "cleanup, or\nan unmeasured boundary.",
        "The candidate may add work to Validate, Export, a warm cycle, "
        "cleanup, or\nan unmeasured boundary.",
    )
    expect_rejected(
        "performance-direction/displaced-cost-authorised",
        lambda: progress._validate_performance_direction_sources(
            direction_displaced_cost_allowed,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: must add no work to "
        "Validate, Export, a warm cycle, cleanup, or an unmeasured boundary",
    )

    direction_fixed_profile_weakened = replace_once(
        performance_sop,
        "If inspection does not give sufficient proof, stop the cycle.",
        "If inspection does not give sufficient proof, change the measurement "
        "profile.",
    )
    expect_rejected(
        "performance-direction/fixed-profile-weakened",
        lambda: progress._validate_performance_direction_sources(
            direction_fixed_profile_weakened,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: If inspection does not give "
        "sufficient proof, stop the cycle",
    )

    direction_warm_aggregation_removed = replace_once(
        performance_sop,
        "For each numeric warm metric, calculate the median of the three "
        "measured warm\ncycles in one sample.",
        "Select one warm cycle after the candidate results are known.",
    )
    expect_rejected(
        "performance-direction/warm-aggregation-removed",
        lambda: progress._validate_performance_direction_sources(
            direction_warm_aggregation_removed,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: For each numeric warm "
        "metric, calculate the median of the three measured warm cycles in "
        "one sample",
    )

    direction_product_failure_replaced = replace_once(
        performance_sop,
        "A product defect, invariant difference, or correctness failure gives "
        "a FAIL\nresult and stops the cycle.",
        "A product defect, invariant difference, or correctness failure can "
        "be replaced.",
    )
    expect_rejected(
        "performance-direction/product-failure-replaced",
        lambda: progress._validate_performance_direction_sources(
            direction_product_failure_replaced,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: A product defect, invariant "
        "difference, or correctness failure gives a FAIL result and stops the "
        "cycle",
    )

    direction_replacement_class_weakened = replace_once(
        performance_sop,
        "A replacement is possible only for the failure\nclass "
        "`fixture-or-harness-defect` or `environment-or-profile-defect`.",
        "A replacement is possible for any failure.",
    )
    expect_rejected(
        "performance-direction/replacement-class-weakened",
        lambda: progress._validate_performance_direction_sources(
            direction_replacement_class_weakened,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: replacement is possible "
        "only for the failure class fixture-or-harness-defect or "
        "environment-or-profile-defect",
    )

    direction_resource_rule_removed = replace_once(
        performance_sop,
        "The Level 2 cycle must use condition 4 for RSS, RSS change, high-water "
        "RSS,\n   and high-water RSS change in each measured stage and the full "
        "journey.",
        "Do not compare RSS or high-water RSS.",
    )
    expect_rejected(
        "performance-direction/resource-rule-removed",
        lambda: progress._validate_performance_direction_sources(
            direction_resource_rule_removed,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: The Level 2 cycle must use "
        "condition 4 for RSS, RSS change, high-water RSS, and high-water RSS "
        "change",
    )

    direction_rule_selected_after_results = replace_once(
        performance_sop,
        "Do not select a new rule after the project knows the candidate\n"
        "results.",
        "Select a new rule after the project knows the candidate\nresults.",
    )
    expect_rejected(
        "performance-direction/post-result-rule-authorised",
        lambda: progress._validate_performance_direction_sources(
            direction_rule_selected_after_results,
            terminology,
            evidence,
        ),
        "D-GOV-008 performance direction drifted: Do not select a new rule "
        "after the project knows the candidate results",
    )

    direction_exit_accepted = replace_once(
        evidence,
        "D-GOV-008 makes no product change. It does not admit the PR #50 "
        "baseline\nor a subsequent result as Exit 4 evidence.",
        "D-GOV-008 makes a product change. It admits the PR #50 baseline\n"
        "and a subsequent result as Exit 4 evidence.",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-exit4-evidence-admitted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_exit_accepted,
        ),
        "D-GOV-008 evidence panel drifted: does not admit the PR #50 baseline "
        "or a subsequent result as Exit 4 evidence",
    )

    direction_risk_panel_deleted = replace_once(
        evidence,
        table_row_containing(evidence, "all unmeasured boundaries") + "\n",
        "",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-risk-panel-deleted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_risk_panel_deleted,
        ),
        "D-GOV-008 risk panel drifted: PR-15 — deferred cost",
    )

    direction_conformance_scope_narrowed = replace_once(
        evidence,
        table_row_containing(evidence, "human-readable D-GOV-008 record")
        + "\n",
        "",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-conformance-scope-narrowed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_conformance_scope_narrowed,
        ),
        "D-GOV-008 conformance scope drifted: "
        "reference/current/gate-decisions.json",
    )

    direction_review_gate_inverted = replace_once(
        evidence,
        "The two reviews must find no blocker before the project merges the "
        "candidate.",
        "The project can merge the candidate when a review finds a blocker.",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-review-gate-inverted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_review_gate_inverted,
        ),
        "D-GOV-008 review gate drifted: two reviews must find no blocker "
        "before the project merges the candidate",
    )

    direction_owner_authority_removed = replace_once(
        evidence,
        "> I authorise a Level 2 change in the preview sampler.",
        "> A reviewer authorises a Level 2 change in the preview sampler.",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-owner-authority-removed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_owner_authority_removed,
        ),
        "D-GOV-008 quoted owner decision drifted: I authorise a Level 2 change "
        "in the preview sampler",
    )


def validate_project_plan_mutations() -> None:
    """Keep current/future programme polarity in the dashboard preamble."""
    plan = read("reference/PROJECT_PLAN.md")
    paragraph = paragraph_containing(plan, "The active program is")
    diagnostic = (
        "project plan lost its local current-programme and future-horizon clause"
    )
    cases = {
        "project-plan/deleted-future-clause": replace_once(
            plan,
            "The project can record future architecture without current "
            "implementation.",
            "",
        ),
        "project-plan/semantic-inversion": replace_once(
            plan,
            "It does not change Phase 6 exits",
            "It changes Phase 6 exits",
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

    authority_substitution = replace_once(
        plan,
        "[PRODUCT_VISION.md](PRODUCT_VISION.md)",
        "[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md)",
    )
    expect_rejected(
        "project-plan/authority-substitution",
        lambda: progress._validate_plan_programme(authority_substitution),
        "project plan Product Vision authority link or destination drifted",
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

    phase6_row = table_row_containing(
        plan,
        "| 6 | Explicit exact-validation and export seam",
    )
    phase6_previous = replace_once(
        phase6_row,
        "2/5 accepted exits",
        "1/5 accepted exits",
    )
    expect_rejected(
        "project-plan/phase6-count-returned-to-one",
        lambda: progress._validate_plan_shape(
            replace_once(plan, phase6_row, phase6_previous)
        ),
        "Phase 6 must remain current at the accepted 2/5 state",
    )

    exit2_row = table_row_containing(
        plan,
        "Evidenced — owner-accepted 2026-08-02",
    )
    exit2_pending = replace_once(
        exit2_row,
        "Evidenced — owner-accepted 2026-08-02",
        "Pending",
    )
    expect_rejected(
        "project-plan/exit2-returned-to-pending",
        lambda: progress._validate_exit_conditions(
            replace_once(plan, exit2_row, exit2_pending),
            read("reference/history/phase-closeouts/PHASE4_CLOSEOUT.md"),
            read("reference/history/phase-closeouts/PHASE5_CLOSEOUT.md"),
            read("reference/current/PHASE_EVIDENCE.md"),
        ),
        "project-plan Phase 6 exit states drifted",
    )

    exit3_row = table_row_containing(
        plan,
        "Evidenced — owner-accepted 2026-08-15",
    )
    exit3_pending = replace_once(
        exit3_row,
        "Evidenced — owner-accepted 2026-08-15",
        "Pending",
    )
    expect_rejected(
        "project-plan/exit3-returned-to-pending",
        lambda: progress._validate_exit_conditions(
            replace_once(plan, exit3_row, exit3_pending),
            read("reference/history/phase-closeouts/PHASE4_CLOSEOUT.md"),
            read("reference/history/phase-closeouts/PHASE5_CLOSEOUT.md"),
            read("reference/current/PHASE_EVIDENCE.md"),
        ),
        "project-plan Phase 6 exit states drifted",
    )

    recovery_decision_row = table_row_containing(plan, "| D-P6-003 |")
    expect_rejected(
        "project-plan/d-p6-003-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, recovery_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    acceptance_decision_row = table_row_containing(plan, "| D-P6-005 |")
    expect_rejected(
        "project-plan/d-p6-005-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, acceptance_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    tt_doc_decision_row = table_row_containing(plan, "| TT-DOC-001 |")
    expect_rejected(
        "project-plan/tt-doc-001-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, tt_doc_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    spelling_decision_row = table_row_containing(plan, "| TT-DOC-002 |")
    expect_rejected(
        "project-plan/tt-doc-002-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, spelling_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    compatibility_decision_row = table_row_containing(plan, "| D-GOV-006 |")
    expect_rejected(
        "project-plan/d-gov-006-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, compatibility_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    performance_host_decision_row = table_row_containing(
        plan,
        "| D-GOV-007 |",
    )
    expect_rejected(
        "project-plan/d-gov-007-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, performance_host_decision_row + "\n", "")
        ),
        "project-plan decisions differ from the frozen registers",
    )
    performance_direction_decision_row = table_row_containing(
        plan,
        "| D-GOV-008 |",
    )
    expect_rejected(
        "project-plan/d-gov-008-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                performance_direction_decision_row + "\n",
                "",
            )
        ),
        "project-plan decisions differ from the frozen registers",
    )


def validate_documentation_profile_mutations() -> None:
    """Reject TT-DOC deletion, contradiction and authority widening."""
    engineering = read("reference/ENGINEERING_POLICY.md")
    plan = read("reference/PROJECT_PLAN.md")
    learning = read("reference/LEARNING_FROM_EXPERIENCE.md")
    terminology = read("reference/TERMINOLOGY.md")

    profile_cases = (
        (
            "tt-doc/profile-heading-deleted",
            "## TT-DOC-001 — TrackTemplate Technical Documentation Profile",
            "## Removed documentation profile",
            "Engineering Policy must own exactly one TT-DOC-001 profile",
        ),
        (
            "tt-doc/owner-view-made-authoritative",
            "must never give project authority\nindependently",
            "can give project authority\nindependently",
            "TT-DOC-001 profile lacks: must never give project authority "
            "independently",
        ),
        (
            "tt-doc/pending-grants-authority",
            "Pending gives no authority.",
            "Pending gives acceptance authority.",
            "TT-DOC-001 meaning drifted for: Pending",
        ),
        (
            "tt-doc/limitation-hidden",
            "A reader must be able to see it.",
            "A reader does not have to see it.",
            "TT-DOC-001 meaning drifted for: Limitation",
        ),
        (
            "tt-doc/evidence-manufactures-acceptance",
            "Short text must never change evidence or a\nrecommendation into "
            "acceptance",
            "Short text can change evidence or a\nrecommendation into "
            "acceptance",
            "TT-DOC-001 profile lacks: Short text must never change evidence "
            "or a recommendation into acceptance",
        ),
        (
            "tt-doc/frozen-history-rewrite-authorized",
            "Do not change frozen history only to correct its Issue 9 style.",
            "Change frozen history to correct its Issue 9 style.",
            "TT-DOC-001 profile lacks: Do not change frozen history only to "
            "correct its Issue 9 style",
        ),
        (
            "tt-doc/issue9-made-optional",
            "as the normative controlled-writing standard",
            "as optional writing inspiration",
            "TT-DOC-001 profile lacks: normative controlled-writing standard",
        ),
        (
            "tt-doc/official-reference-removed",
            "The official standard is the normative external\nreference.",
            "Public summaries are the normative external\nreference.",
            "TT-DOC-001 profile lacks: official standard is the normative "
            "external reference",
        ),
        (
            "tt-doc/american-only-spelling-restored",
            "TrackTemplate uses UK English spelling as its project spelling "
            "directive",
            "TrackTemplate requires American English spelling in this scope",
            "TT-DOC-001 profile lacks: TrackTemplate uses UK English spelling "
            "as its project spelling directive",
        ),
        (
            "tt-doc/rule-1-14-option-removed",
            "directive uses the option in Issue 9 Rule 1.14",
            "directive conflicts with Issue 9 Rule 1.14",
            "TT-DOC-001 profile lacks: directive uses the option in Issue 9 "
            "Rule 1.14",
        ),
        (
            "tt-doc/spelling-directive-widens-ste-change",
            "The directive changes spelling\nonly.",
            "The directive changes spelling and vocabulary.",
            "TT-DOC-001 profile lacks: directive changes spelling only",
        ),
        (
            "tt-doc/checker-made-conformance-authority",
            "The tool cannot replace\nthe linguistic review or show Issue 9 "
            "conformance.",
            "The tool replaces\nthe linguistic review and proves Issue 9 "
            "conformance.",
            "TT-DOC-001 profile lacks: cannot replace the linguistic review "
            "or show Issue 9 conformance",
        ),
        (
            "tt-doc/material-unit-review-waived",
            "review the full logical unit that contains the change.\n"
            "  Use the applicable Issue 9 requirements",
            "review only the changed words.\n"
            "  Use the applicable Issue 9 requirements",
            "TT-DOC-001 profile lacks: review the full logical unit that "
            "contains the change",
        ),
        (
            "tt-doc/s1000d-conformance-claimed",
            "does not claim S1000D conformance",
            "claims S1000D conformance",
            "TT-DOC-001 profile lacks: does not claim S1000D conformance",
        ),
        (
            "tt-doc/external-certification-claimed",
            "TrackTemplate does not claim this state.",
            "TrackTemplate claims this state.",
            "TT-DOC-001 profile lacks: does not claim this state",
        ),
        (
            "tt-doc/skill-owner-authority-widened",
            "Documentation simplification does not give a skill phase, "
            "production,\nsecurity, merge, release, acceptance, or project-owner "
            "authority",
            "Documentation simplification gives every skill phase, production,\n"
            "security, merge, release, acceptance, and project-owner "
            "authority",
            "TT-DOC-001 profile lacks: Documentation simplification does not "
            "give a skill phase, production, security, merge, release, "
            "acceptance, or project-owner authority",
        ),
    )
    for name, original, replacement, diagnostic in profile_cases:
        mutated = replace_once(engineering, original, replacement)
        expect_rejected(
            name,
            lambda value=mutated: quality_assurance.validate_documentation_profile(
                value,
                plan,
                learning,
                terminology,
            ),
            diagnostic,
        )

    owner_view_status = replace_once(
        plan,
        "Phase 6 has 2/5 accepted exits",
        "Phase 6 has 3/5 accepted exits",
    )
    expect_rejected(
        "tt-doc/owner-view-status-contradiction",
        lambda: progress._validate_owner_view(owner_view_status),
        "project-plan owner view lost or contradicted: Phase 6 has 2/5 "
        "accepted exits",
    )
    owner_view_authority = replace_once(
        plan,
        "The owner view does not establish authority",
        "The owner view establishes authority",
    )
    expect_rejected(
        "tt-doc/owner-view-authority-inversion",
        lambda: progress._validate_owner_view(owner_view_authority),
        "project-plan owner view became an authority source",
    )

    compatibility_terms_removed = terminology
    for marker in (
        "| Host compatibility |",
        "| Host compatibility tools |",
        "| Host compatibility authority |",
    ):
        compatibility_terms_removed = replace_once(
            compatibility_terms_removed,
            table_row_containing(compatibility_terms_removed, marker) + "\n",
            "",
        )
    expect_rejected(
        "tt-doc/d-gov-006-compatibility-terms-removed",
        lambda: quality_assurance.validate_documentation_profile(
            engineering,
            plan,
            learning,
            compatibility_terms_removed,
        ),
        "TrackTemplate STE terminology lacks: Host compatibility",
    )

    lfe_link_deleted = replace_once(
        learning,
        "tt-doc-001-tracktemplate-technical-documentation-profile",
        "missing-documentation-profile",
    )
    expect_rejected(
        "tt-doc/lfe-canonical-link-deleted",
        lambda: quality_assurance.validate_documentation_profile(
            engineering,
            plan,
            lfe_link_deleted,
            terminology,
        ),
        "LFE-018 lacks: tt-doc-001-tracktemplate-technical-documentation-profile",
    )

    workflows = read("reference/AGENT_WORKFLOWS.md")
    validation = read("reference/VALIDATION.md")
    source_reference = read(
        "reference/external/asd-ste100/README.md"
    )
    gitignore = read(".gitignore")

    local_priority_removed = replace_once(
        source_reference,
        "Use the local official PDF when it is available",
        "Use an official remote source before the local PDF",
    )
    expect_rejected(
        "tt-doc/ste100-local-source-priority-removed",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            local_priority_removed,
            gitignore,
        ),
        "ASD-STE100 reference instructions lack: Use the local official PDF "
        "when it is available",
    )
    third_party_made_normative = replace_once(
        source_reference,
        "Do not use a third-party summary, search-result text, blog, or "
        "derived\n   guidance as normative conformance evidence.",
        "Use a third-party summary as normative conformance evidence.",
    )
    expect_rejected(
        "tt-doc/ste100-third-party-source-made-normative",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            third_party_made_normative,
            gitignore,
        ),
        "ASD-STE100 reference instructions lack: Do not use a third-party "
        "summary",
    )
    third_party_url_substituted = replace_once(
        source_reference,
        "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf",
        "https://example.com/ASD-STE100_ISSUE9.pdf",
    )
    expect_rejected(
        "tt-doc/ste100-official-url-substituted",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            third_party_url_substituted,
            gitignore,
        ),
        "ASD-STE100 official ASD/STEMG source targets drifted",
    )
    no_source_claim_authorized = replace_once(
        source_reference,
        "neither official source is available, do not claim that the prose is\n"
        "ASD-STE100 Issue 9 conforming",
        "neither official source is available, claim that the prose is\n"
        "ASD-STE100 Issue 9 conforming",
    )
    expect_rejected(
        "tt-doc/ste100-no-source-conformance-authorized",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            no_source_claim_authorized,
            gitignore,
        ),
        "ASD-STE100 reference instructions lack: neither official source is "
        "available, do not claim",
    )
    pdf_made_policy_owner = replace_once(
        source_reference,
        "The PDF is not a canonical TrackTemplate document.",
        "The PDF is a canonical TrackTemplate document.",
    )
    expect_rejected(
        "tt-doc/ste100-pdf-made-policy-owner",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            pdf_made_policy_owner,
            gitignore,
        ),
        "ASD-STE100 reference instructions lack: PDF is not a canonical "
        "TrackTemplate document",
    )
    pdf_ignore_broadened = replace_once(
        gitignore,
        "/reference/external/asd-ste100/*.pdf",
        "/reference/external/asd-ste100/",
    )
    expect_rejected(
        "tt-doc/ste100-git-exclusion-broadened",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            validation,
            workflows,
            source_reference,
            pdf_ignore_broadened,
        ),
        "ASD-STE100 local PDF must have one narrow Git exclusion",
    )
    pdf_made_ci_dependency = replace_once(
        validation,
        "Normal CI does not use the ignored PDF.",
        "Normal CI uses the ignored PDF.",
    )
    expect_rejected(
        "tt-doc/ste100-pdf-made-ci-dependency",
        lambda: quality_assurance.validate_asd_ste100_reference(
            engineering,
            pdf_made_ci_dependency,
            workflows,
            source_reference,
            gitignore,
        ),
        "ASD-STE100 validation or CI boundary drifted",
    )

    names = sorted(
        path.name
        for path in agent_guidance.SKILLS_ROOT.iterdir()
        if path.is_dir()
    )
    overlap_default_inverted = replace_once(
        workflows,
        "use the primary owner that is already in the\nskill catalog",
        "creation of a parallel skill is the default resolution",
    )
    expect_rejected(
        "tt-doc/overlap-integration-inverted",
        lambda: agent_guidance.validate_documentation_profile_routing(
            names,
            overlap_default_inverted,
        ),
        "AGENT_WORKFLOWS lost TT-DOC-001 overlap control",
    )
    expect_rejected(
        "tt-doc/parallel-profile-skill-introduced",
        lambda: agent_guidance.validate_documentation_profile_routing(
            names + ["tracktemplate-documentation-profile"],
            workflows,
        ),
        "TT-DOC-001 gained an overlapping profile or STE skill",
    )
    expect_rejected(
        "tt-doc/parallel-ste100-skill-introduced",
        lambda: agent_guidance.validate_documentation_profile_routing(
            names + ["tracktemplate-ste100"],
            workflows,
        ),
        "TT-DOC-001 gained an overlapping profile or STE skill",
    )

    phase4_closeout = read(
        "reference/history/phase-closeouts/PHASE4_CLOSEOUT.md"
    )
    phase5_closeout = read(
        "reference/history/phase-closeouts/PHASE5_CLOSEOUT.md"
    )
    current_evidence = read("reference/current/PHASE_EVIDENCE.md")
    conformance_result_removed = replace_once(
        current_evidence,
        "The internal result for these logical units is `ASD-STE100 Issue 9\n"
        "conforming`.",
        "The result for these logical units is not recorded.",
    )
    expect_rejected(
        "tt-doc/conformance-result-removed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            conformance_result_removed,
        ),
        "TT-DOC-001 evidence panel drifted: The internal result for these "
        "logical units is ASD-STE100 Issue 9 conforming",
    )
    conformance_limit_removed = replace_once(
        current_evidence,
        "It excludes unchanged\nlive prose outside the named logical units.",
        "It includes all live prose.",
    )
    expect_rejected(
        "tt-doc/conformance-scope-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            conformance_limit_removed,
        ),
        "TT-DOC-001 evidence panel drifted: It excludes unchanged live prose "
        "outside the named logical units",
    )
    conformance_unit_narrowed = replace_once(
        current_evidence,
        "| `reference/ENGINEERING_POLICY.md` | The TT-DOC-001 profile and the "
        "first paragraph of the completion-report section. |",
        "| `reference/ENGINEERING_POLICY.md` | One sentence. |",
    )
    expect_rejected(
        "tt-doc/conformance-logical-unit-narrowed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            conformance_unit_narrowed,
        ),
        "TT-DOC-001 conformance scope changed: "
        "reference/ENGINEERING_POLICY.md",
    )

    spelling_scope_widened = replace_once(
        current_evidence,
        "The 18-unit conformance table keeps the same path set.",
        "The conformance result now applies to all live prose.",
    )
    expect_rejected(
        "tt-doc-002/conformance-scope-widened",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            spelling_scope_widened,
        ),
        "TT-DOC-002 evidence panel drifted: 18-unit conformance "
        "table keeps the same path set",
    )
    spelling_unit_narrowed = replace_once(
        current_evidence,
        "| `reference/ENGINEERING_POLICY.md` | The full TT-DOC-001 "
        "profile. |",
        "| `reference/ENGINEERING_POLICY.md` | One sentence. |",
    )
    expect_rejected(
        "tt-doc-002/conformance-logical-unit-narrowed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            spelling_unit_narrowed,
        ),
        "TT-DOC-002 conformance scope changed: "
        "reference/ENGINEERING_POLICY.md",
    )
    spelling_only_boundary_removed = replace_once(
        current_evidence,
        "It does not change vocabulary, grammar, approved meaning, "
        "part-of-speech, technical-term, or linguistic-review requirements.",
        "It relaxes vocabulary, grammar, and technical-term requirements.",
    )
    expect_rejected(
        "tt-doc-002/non-spelling-requirements-relaxed",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            spelling_only_boundary_removed,
        ),
        "TT-DOC-002 evidence panel drifted: does not change vocabulary, "
        "grammar, approved meaning, part-of-speech, technical-term, or "
        "linguistic-review requirements",
    )

    spelling_review_blocker_inverted = replace_once(
        current_evidence,
        "The governance review result was PASS WITH FINDINGS. That review "
        "examined\nauthority and preservation. No reviewer found a blocker.",
        "The governance review result was PASS WITH FINDINGS. That review "
        "examined\nauthority and preservation. One reviewer found a blocker.",
    )
    expect_rejected(
        "tt-doc-002/review-blocker-inverted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            spelling_review_blocker_inverted,
        ),
        "TT-DOC-002 evidence panel drifted: No reviewer found a blocker",
    )

    terminology_owner_removed = replace_once(
        terminology,
        "one project register for TrackTemplate technical nouns and\n"
        "technical verbs",
        "a second optional register for project words",
    )
    expect_rejected(
        "tt-doc/terminology-owner-removed",
        lambda: quality_assurance.validate_documentation_profile(
            engineering,
            plan,
            learning,
            terminology_owner_removed,
        ),
        "TrackTemplate STE terminology lacks: one project register",
    )


def validate_transition_export_validation_mutations() -> None:
    """Reject weakening or promotion of the bounded D-P6-003 proof."""
    validation = read("reference/VALIDATION.md")
    diagnostic = (
        "the transition DXF command, sentinel or recovery-evidence boundary "
        "is missing"
    )
    cases = (
        (
            "validation/exit3-prebind-substitution-proof-withdrawn",
            replace_once(
                validation,
                "resolve-to-bind removal and\nsubstitution",
                "resolve-to-bind removal only",
            ),
        ),
        (
            "validation/exit3-active-lock-made-recoverable",
            replace_once(
                validation,
                "active-lock\nfail-closed diagnostics",
                "active-lock success diagnostics",
            ),
        ),
        (
            "validation/exit3-initial-member-substitution-proof-withdrawn",
            replace_once(
                validation,
                "initial-member and post-addition substitution",
                "post-addition substitution only",
            ),
        ),
        (
            "validation/exit3-descriptor-close-proof-withdrawn",
            replace_once(
                validation,
                "observed descriptor-close\nabandonment",
                "descriptor-close abandonment was not observed",
            ),
        ),
        (
            "validation/exit3-surviving-host-interruption-proof-withdrawn",
            replace_once(
                validation,
                "surviving-host `BaseException` propagation with chained "
                "truthful\nretained-state diagnostics",
                "surviving-host interruption cleanup remains unproved",
            ),
        ),
        (
            "validation/exit3-add-only-proof-withdrawn",
            replace_once(
                validation,
                "It proves the bounded D-P6-003 strict add-only, journal-free\n"
                "implementation",
                "It does not prove the bounded D-P6-003 strict add-only, "
                "journal-free\nimplementation",
            ),
        ),
        (
            "validation/exit3-published-final-mutation-authorised",
            replace_once(
                validation,
                "no published final is\nremoved, rewritten or replaced by "
                "TrackTemplate",
                "a published final may be\nremoved, rewritten or replaced by "
                "TrackTemplate",
            ),
        ),
        (
            "validation/exit3-command-claims-phase-acceptance",
            replace_once(
                validation,
                "they supply no GUI, production-output, Phase 6 exit or "
                "release\nacceptance",
                "they supply Phase 6 exit and release\nacceptance",
            ),
        ),
    )
    for name, mutated in cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                progress._validate_transition_export_validation(value)
            ),
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
    validate_documentation_profile_mutations()
    validate_transition_export_validation_mutations()
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
