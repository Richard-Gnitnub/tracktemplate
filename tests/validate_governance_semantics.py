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
import validate_recovery_controls as recovery_controls


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
        "Vision supplies direction.",
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
                "Vision supplies direction. It does not define a bounded "
                "scope or give task\n> authority.",
                "Vision defines the bounded scope and gives task authority.",
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
        "Phase 6 exits do not match the accepted 3/5 dispositions",
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
        "Phase 6 exits do not match the accepted 3/5 dispositions",
    )

    for name, marker, before, after in (
        (
            "exit1-acceptance-downgraded",
            "Evidenced and owner-accepted under D-P6-006",
            "Evidenced and owner-accepted under D-P6-006",
            "Pending",
        ),
        (
            "exit5-prematurely-evidenced",
            "Pending. B14 remains available",
            "Pending. B14 remains available",
            "Evidenced. B14 remains available",
        ),
    ):
        row = table_row_containing(evidence, marker)
        changed_row = replace_once(row, before, after)
        expect_rejected(
            "phase-evidence/" + name,
            lambda value=replace_once(evidence, row, changed_row): (
                progress._validate_exit_conditions(
                    plan, phase4_closeout, phase5_closeout, value,
                )
            ),
            "Phase 6 exits do not match the accepted 3/5 dispositions",
        )

    for name, marker, before, after in (
        (
            "exit1-agreed-scope-widened",
            "At protected main `e1ab8a9fdbde29d5e0fe953ff678b33d9a55e3d7`",
            "the PR #63 centreline comparison profile",
            "all legacy production outputs",
        ),
        (
            "exit1-production-clearance-granted",
            "> Output stays private-development and project status",
            "No production-use clearance, wider output equivalence",
            "Production-use clearance and wider output equivalence",
        ),
    ):
        quote = blockquote_paragraph_containing(evidence, marker)
        changed_quote = replace_once(quote, before, after)
        expect_rejected(
            "phase-evidence/" + name,
            lambda value=replace_once(evidence, quote, changed_quote): (
                progress._validate_exit_conditions(
                    plan, phase4_closeout, phase5_closeout, value,
                )
            ),
            "D-P6-006 panel exact owner decision drifted or was relocated",
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
        "No independently trusted creation authority supports cross-process "
        "automatic recovery",
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
        "The exporter preserves and rejects that item as unclaimable.",
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
        "The cases do not claim automatic recovery",
        "The cases prove automatic recovery",
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
        "They also preserve access\ntime.",
        "They do not preserve access\ntime.",
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
        "It also preserves every file, identity, metadata value, and byte.",
        "It may delete files or change their identities, metadata, and bytes.",
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
        "creates each output in an anonymous regular staging file with "
        "`O_TMPFILE`. It\nimmediately captures the device/inode identity from "
        "the descriptor returned by\nthat operation",
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
        "journal is also created anonymously. Before\n"
        "`linkat(AT_EMPTY_PATH)` commits either output file, the journal is "
        "linked from\nits still-open descriptor",
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
        "Normal stage cleanup is descriptor close. There is no staging "
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
        "Their presence neither\npermits nor prevents final-set completion",
        "Their presence authorises deletion and prevents final-set completion",
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
        "establishes compatibility for reuse or addition only. It never "
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
        "grant deletion\n> authority. POSIX pathname deletion has no "
        "expected-inode atomic condition",
        "grant deletion\n> authority. POSIX pathname deletion has an "
        "expected-inode atomic condition",
    )
    expect_rejected(
        "phase-evidence/exit3-expected-inode-delete-invented",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            expected_inode_delete_invented,
        ),
        "D-P6-003 exact owner decision drifted or was relocated",
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
        "An exact regular partial pair may\nbe completed instead of rejected",
        "An exact regular partial pair must remain unrecoverable",
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
        "Condition 6\nremains open",
        "Condition 6\nis closed",
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
        "The completed D-GOV-011 baseline-attribution investigation gave FAIL",
    )
    exit4_promoted = replace_once(
        exit4_row,
        "Pending — D-GOV-008 and D-GOV-009",
        "Evidenced — D-GOV-008 and D-GOV-009",
    )
    expect_rejected(
        "phase-evidence/exit4-prematurely-evidenced",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            replace_once(evidence, exit4_row, exit4_promoted),
        ),
        "Phase 6 exits do not match the accepted 3/5 dispositions",
    )

    prerequisite_promoted = replace_once(
        evidence,
        "The D-GOV-009 attribution materiality rule gave FAIL.",
        "The D-GOV-009 attribution materiality rule gave PASS.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-negative-prerequisite-promoted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            prerequisite_promoted,
        ),
        "D-GOV-011 prerequisite completion drifted: D-GOV-009 "
        "attribution materiality rule gave FAIL",
    )

    performance_promoted = replace_once(
        evidence,
        "This evidence does not satisfy Exit 4, which remains Pending",
        "This evidence satisfies Exit 4",
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

    exit2_section = progress._section(
        evidence,
        "Phase 6 Exits 2 and 3 panel to admit evidence and owner decision",
    )
    exit2_authority = blockquote_paragraph_containing(
        exit2_section,
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
        "The previous 1.1.1-only validator rejected the 1.1.3 test result.\n"
        "D-GOV-007 does not admit this test result as Exit 4 evidence",
        "The previous 1.1.1-only validator rejected the 1.1.3 test result.\n"
        "D-GOV-007 admits this test result as Exit 4 evidence",
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
        "The two reviews must find no blocking condition before the project "
        "merges the\ncandidate.",
        "The project can merge the candidate when a review finds a blocking "
        "condition.",
    )
    expect_rejected(
        "phase-evidence/d-gov-008-review-gate-inverted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            direction_review_gate_inverted,
        ),
        "D-GOV-008 review gate drifted: The two reviews must find no blocking "
        "condition before the project merges the candidate",
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

    followup_reopened = replace_once(
        performance_sop,
        "Do not make a third preview-sampler change.",
        "Make a third preview-sampler change.",
    )
    expect_rejected(
        "performance-direction/d-gov-009-exhausted-direction-reopened",
        lambda: progress._validate_performance_direction_sources(
            followup_reopened,
            terminology,
            evidence,
        ),
        "D-GOV-009 direction drifted: Do not make a third preview-sampler "
        "change",
    )

    followup_result_promoted = replace_once(
        evidence,
        "The two retained results are not improvement evidence.",
        "The two retained results are improvement evidence.",
    )
    expect_rejected(
        "phase-evidence/d-gov-009-negative-results-promoted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            followup_result_promoted,
        ),
        "D-GOV-009 evidence panel drifted: The two retained results are not "
        "improvement evidence",
    )

    followup_alternative_claimed = replace_once(
        evidence,
        "No measured evidence shows sufficient\ncost in a measurement area "
        "outside the D-GOV-008 preview-sampler boundary.",
        "Measured evidence shows sufficient cost in a measurement area "
        "outside the D-GOV-008 preview-sampler boundary.",
    )
    expect_rejected(
        "phase-evidence/d-gov-009-unevidenced-alternative-claimed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            followup_alternative_claimed,
        ),
        "D-GOV-009 evidence panel drifted: No measured evidence shows "
        "sufficient cost in a measurement area outside the D-GOV-008 "
        "preview-sampler boundary",
    )

    followup_investigation_started = replace_once(
        evidence,
        "Do not start that investigation in this cycle.",
        "Start that investigation in this cycle.",
    )
    expect_rejected(
        "phase-evidence/d-gov-009-investigation-started",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            followup_investigation_started,
        ),
        "D-GOV-009 evidence panel drifted: Do not start that investigation in "
        "this cycle",
    )

    followup_owner_gate_removed = replace_once(
        evidence,
        "A subsequent Level 3 owner decision is necessary before a new Level "
        "2\noptimisation.",
        "No owner decision is necessary before a new Level 2 optimisation.",
    )
    expect_rejected(
        "phase-evidence/d-gov-009-owner-gate-removed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            followup_owner_gate_removed,
        ),
        "D-GOV-009 evidence panel drifted: subsequent Level 3 owner decision "
        "is necessary before a new Level 2 optimisation",
    )

    host_scope_widened = replace_once(
        evidence,
        "They do not qualify a different Flatpak package.",
        "They qualify all FreeCAD 1.1.3 Flatpak packages.",
    )
    expect_rejected(
        "phase-evidence/d-gov-010-host-scope-widened",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            host_scope_widened,
        ),
        "D-GOV-010 evidence panel drifted: do not qualify a different "
        "Flatpak package",
    )

    host_performance_admitted = replace_once(
        evidence,
        "This cycle records no performance\nmeasurement, comparison, or "
        "budget.",
        "This cycle records an accepted performance result.",
    )
    expect_rejected(
        "phase-evidence/d-gov-010-performance-admitted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            host_performance_admitted,
        ),
        "D-GOV-010 evidence panel drifted: This cycle records no performance "
        "measurement, comparison, or budget",
    )

    host_attribution_started = replace_once(
        evidence,
        "This qualification does not start that\ninvestigation.",
        "This qualification starts that investigation.",
    )
    expect_rejected(
        "phase-evidence/d-gov-010-attribution-started",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            host_attribution_started,
        ),
        "D-GOV-010 evidence panel drifted: This qualification does not start "
        "that investigation",
    )

    selection_snapshot_removed = replace_once(
        evidence,
        "The snapshot contains\n6,519 files and 1,244 directories.",
        "The snapshot content was not checked.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-snapshot-proof-removed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_snapshot_removed,
        ),
        "D-GOV-011 evidence panel drifted: snapshot contains 6,519 files "
        "and 1,244 directories",
    )

    selection_host_gate_removed = replace_once(
        evidence,
        "Before product work, do the exact attribution method in D-GOV-009 "
        "again on clean\nprotected main. Use only the exact D-GOV-010 host.",
        "Before product work, use results from any available host.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-host-gate-removed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_host_gate_removed,
        ),
        "D-GOV-011 evidence panel drifted: do the exact attribution method in "
        "D-GOV-009 again on clean protected main",
    )

    selection_boundary_widened = replace_once(
        evidence,
        "Do not\nchange `tracktemplate/application/transition_edit.py` or a "
        "preview, Coin, GUI,\nexact-validation, export, or "
        "railway-mathematics file.",
        "Change any application, preview, Coin, GUI, export, or railway file.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-product-boundary-widened",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_boundary_widened,
        ),
        "D-GOV-011 evidence panel drifted: Do not change "
        "tracktemplate/application/transition_edit.py",
    )

    selection_displacement_allowed = replace_once(
        evidence,
        "> Edit measurement areas in D-GOV-009. The candidate must add no work "
        "to an\n> unmeasured boundary.",
        "> Edit measurement areas in D-GOV-009. The candidate can move work to "
        "an\n> unmeasured boundary.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-displacement-allowed",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_displacement_allowed,
        ),
        "D-GOV-011 quoted owner decision drifted: must add no work to an "
        "unmeasured boundary",
    )

    selection_product_started = replace_once(
        evidence,
        "> I authorise one subsequent product change at Level 2 in this "
        "adapter file. Do\n> not start it in this cycle.",
        "> I authorise one subsequent product change at Level 2 in this "
        "adapter file.\n> Start it in this cycle.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-product-started",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_product_started,
        ),
        "D-GOV-011 quoted owner decision drifted: Do not start it in this "
        "cycle",
    )

    selection_exit_accepted = replace_once(
        evidence,
        "> defines no product performance budget. It does not accept Exit 4.",
        "> defines a product performance budget and accepts Exit 4.",
    )
    expect_rejected(
        "phase-evidence/d-gov-011-exit4-accepted",
        lambda: progress._validate_performance_direction_sources(
            performance_sop,
            terminology,
            selection_exit_accepted,
        ),
        "D-GOV-011 quoted owner decision drifted: defines no product "
        "performance budget",
    )

    lifecycle_changed_row = table_row_containing(
        evidence,
        "| What changed | D-GOV-015 adopts one Documentation Review lifecycle",
    )
    lifecycle_two_reviews = replace_once(
        lifecycle_changed_row,
        "→ one Documentation Review →",
        "→ two Documentation Reviews →",
    )
    expect_rejected(
        "phase-evidence/d-gov-015-second-review-authorised",
        lambda: progress._validate_ste_lifecycle_panel(
            replace_once(
                evidence,
                lifecycle_changed_row,
                lifecycle_two_reviews,
            )
        ),
        "D-GOV-015 owner-view row drifted: What changed",
    )
    lifecycle_result_row = table_row_containing(
        evidence,
        "The review-state register keeps document identities",
    )
    lifecycle_unit_state = replace_once(
        lifecycle_result_row,
        "The review-state register keeps document identities.",
        "The review-state register keeps every logical unit.",
    )
    expect_rejected(
        "phase-evidence/d-gov-015-persistent-unit-state-added",
        lambda: progress._validate_ste_lifecycle_panel(
            replace_once(
                evidence,
                lifecycle_result_row,
                lifecycle_unit_state,
            )
        ),
        "D-GOV-015 owner-view row drifted: What now works",
    )
    lifecycle_limitations_row = table_row_containing(
        evidence,
        "Final validation does not judge linguistic conformance",
    )
    lifecycle_linguistic_validation = replace_once(
        lifecycle_limitations_row,
        "does not judge linguistic conformance",
        "independently judges linguistic conformance",
    )
    expect_rejected(
        "phase-evidence/d-gov-015-final-validation-made-linguistic",
        lambda: progress._validate_ste_lifecycle_panel(
            replace_once(
                evidence,
                lifecycle_limitations_row,
                lifecycle_linguistic_validation,
            )
        ),
        "D-GOV-015 owner-view row drifted: Limitations/findings",
    )

    tdmp_section = progress._section(
        evidence,
        "D-GOV-017 whole technical-document lifecycle",
    )
    expect_rejected(
        "phase-evidence/d-gov-017-historical-blocked-status-erased",
        lambda: progress._validate_tdmp_lifecycle_panel(
            replace_once(
                evidence,
                "Its `BLOCKED` result uses schema 2",
                "Its result uses schema 2",
            )
        ),
        "D-GOV-017 evidence panel drifted: Its BLOCKED result uses schema 2",
    )
    tdmp_current_row = table_row_containing(
        tdmp_section,
        "Repository integration did not yet make it the current "
        "controlled baseline",
    )
    tdmp_candidate_made_current = replace_once(
        tdmp_current_row,
        "Repository integration did not yet make it the current "
        "controlled baseline",
        "Repository integration made it the current "
        "controlled baseline",
    )
    expect_rejected(
        "phase-evidence/d-gov-017-draft-made-current",
        lambda: progress._validate_tdmp_lifecycle_panel(
            replace_once(
                evidence,
                tdmp_section,
                replace_once(
                    tdmp_section,
                    tdmp_current_row,
                    tdmp_candidate_made_current,
                ),
            )
        ),
        "D-GOV-017 owner view drifted: Repository integration did not yet "
        "make it the current controlled baseline",
    )
    tdmp_authority_row = table_row_containing(
        tdmp_section,
        "Keep the D-GOV-015 authoring controls and sole Documentation Review "
        "authoritative",
    )
    tdmp_dgov015_replaced = replace_once(
        tdmp_authority_row,
        "Keep the D-GOV-015 authoring controls and sole Documentation Review "
        "authoritative",
        "Replace the D-GOV-015 authoring controls and Documentation Review",
    )
    expect_rejected(
        "phase-evidence/d-gov-017-replaces-d-gov-015",
        lambda: progress._validate_tdmp_lifecycle_panel(
            replace_once(
                evidence,
                tdmp_section,
                replace_once(
                    tdmp_section,
                    tdmp_authority_row,
                    tdmp_dgov015_replaced,
                ),
            )
        ),
        "D-GOV-017 owner view drifted: Keep the D-GOV-015 authoring controls "
        "and sole Documentation Review authoritative",
    )


def validate_finite_documentation_mutations() -> None:
    """Keep D-GOV-018 completion distinct from acceptance and re-review."""
    plan = read("reference/PROJECT_PLAN.md")
    evidence = read("reference/current/PHASE_EVIDENCE.md")
    for name, original, replacement in (
        (
            "d-gov-018/locked-completion-made-linguistic-acceptance",
            (
                'keeps the initial linguistic verdict and completed lifecycle '
                'as different results'
            ),
            "converts the original linguistic verdict to ACCEPT at lock",
        ),
        (
            "d-gov-018/replacement-review-and-cycle-restart-authorised",
            (
                'rejection of replacement reviews and new cycles for the same '
                'document\npaths before the initial cycle is complete'
            ),
            "acceptance of replacement reviews and overlapping cycle restarts",
        ),
        (
            "d-gov-018/uncommitted-final-validation-claimed",
            (
                'Before you claim completion of the\nGit final-validation '
                'command, use it against committed content'
            ),
            "Claim completion of the Git final-validation command without "
            "committed content",
        ),
    ):
        mutated = replace_once(evidence, original, replacement)
        expect_rejected(
            name,
            lambda value=mutated: (
                progress._validate_finite_documentation_completion(plan, value)
            ),
            "D-GOV-018 evidence boundary drifted: "
            + progress._semantic_text(original),
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
            "The project can record its future architecture without current "
            "implementation.",
            "",
        ),
        "project-plan/semantic-inversion": replace_once(
            plan,
            "It does not change the Phase 6 exits",
            "It changes the Phase 6 exits",
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
        "3/5 accepted exits",
        "1/5 accepted exits",
    )
    expect_rejected(
        "project-plan/phase6-count-returned-to-one",
        lambda: progress._validate_plan_shape(
            replace_once(plan, phase6_row, phase6_previous)
        ),
        "Phase 6 must remain current at the accepted 3/5 state",
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
    exit1_decision_row = table_row_containing(plan, "| D-P6-006 |")
    expect_rejected(
        "project-plan/d-p6-006-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(plan, exit1_decision_row + "\n", "")
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
    direction_followup_decision_row = table_row_containing(
        plan,
        "| D-GOV-009 |",
    )
    expect_rejected(
        "project-plan/d-gov-009-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                direction_followup_decision_row + "\n",
                "",
            )
        ),
        "project-plan decisions differ from the frozen registers",
    )
    host_followup_decision_row = table_row_containing(
        plan,
        "| D-GOV-010 |",
    )
    expect_rejected(
        "project-plan/d-gov-010-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                host_followup_decision_row + "\n",
                "",
            )
        ),
        "project-plan decisions differ from the frozen registers",
    )
    selection_decision_row = table_row_containing(
        plan,
        "| D-GOV-011 |",
    )
    expect_rejected(
        "project-plan/d-gov-011-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                selection_decision_row + "\n",
                "",
            )
        ),
        "project-plan decisions differ from the frozen registers",
    )
    retirement_decision_row = table_row_containing(
        plan,
        "| D-GOV-012 |",
    )
    expect_rejected(
        "project-plan/d-gov-012-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                retirement_decision_row + "\n",
                "",
            )
        ),
        "project-plan decisions differ from the frozen registers",
    )
    lifecycle_decision_row = table_row_containing(
        plan,
        "| D-GOV-015 |",
    )
    expect_rejected(
        "project-plan/d-gov-015-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                lifecycle_decision_row + "\n",
                "",
            )
        ),
        "project-plan D-GOV-015 decision row drifted",
    )
    tdmp_decision_row = table_row_containing(
        plan,
        "| D-GOV-017 |",
    )
    expect_rejected(
        "project-plan/d-gov-017-decision-omitted",
        lambda: progress._validate_decisions(
            replace_once(
                plan,
                tdmp_decision_row + "\n",
                "",
            )
        ),
        "project-plan D-GOV-017 decision row drifted",
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
            "must not give project authority independently",
            "can give project authority independently",
            "TT-DOC-001 profile lacks: must not give project authority "
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
            "The reader must see it.",
            "The reader does not have to see it.",
            "TT-DOC-001 meaning drifted for: Limitation",
        ),
        (
            "tt-doc/evidence-manufactures-acceptance",
            "A short result must\nnot change evidence or a recommendation into "
            "acceptance",
            "A short result can\nchange evidence or a recommendation into "
            "acceptance",
            "TT-DOC-001 profile lacks: A short result must not change evidence "
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
            "### Normative controlled-writing standard",
            "### Optional writing inspiration",
            "TT-DOC-001 profile lacks: Normative controlled-writing standard",
        ),
        (
            "tt-doc/official-reference-removed",
            "The official standard is the normative\nexternal reference.",
            "Public summaries are the normative\nexternal reference.",
            "TT-DOC-001 profile lacks: official standard is the normative "
            "external reference",
        ),
        (
            "tt-doc/american-only-spelling-restored",
            "TrackTemplate uses UK English.",
            "TrackTemplate requires American English spelling in this scope",
            "TT-DOC-001 profile lacks: TrackTemplate uses UK English",
        ),
        (
            "tt-doc/rule-1-14-option-removed",
            "Rule 1.14 permits this instruction",
            "Rule 1.14 prohibits this instruction",
            "TT-DOC-001 profile lacks: Rule 1.14 permits this instruction",
        ),
        (
            "tt-doc/spelling-directive-widens-ste-change",
            "It does not\nchange the applicable Issue 9 vocabulary or grammar "
            "rules.",
            "It changes\nthe applicable Issue 9 vocabulary and grammar rules.",
            "TT-DOC-001 profile lacks: does not change the applicable Issue 9 "
            "vocabulary or grammar rules",
        ),
        (
            "tt-doc/checker-made-conformance-authority",
            "The tool cannot replace\nthe linguistic conformance review. It "
            "cannot show Issue 9 conformance.",
            "The tool replaces\nthe linguistic conformance review. It shows "
            "Issue 9 conformance.",
            "TT-DOC-001 profile lacks: cannot replace the linguistic "
            "conformance review. It cannot show Issue 9 conformance",
        ),
        (
            "tt-doc/material-unit-review-waived",
            "review the complete logical unit that contains the\n"
            "  change.\n- Use the applicable requirement set for that review",
            "review only the changed words.\n- Use the applicable requirement "
            "set for that review",
            "TT-DOC-001 profile lacks: review the complete logical unit that "
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
            "Documentation simplification gives no security/recovery-review "
            "authority. It\ngives no phase, production, merge, release, "
            "acceptance, or project-owner authority",
            "Documentation simplification gives security/recovery-review "
            "authority. It\ngives phase, production, merge, release, acceptance, and "
            "project-owner authority",
            "TT-DOC-001 profile lacks: Documentation simplification gives no "
            "security/recovery-review authority. It gives no phase, production, "
            "merge, release, acceptance, or project-owner authority.",
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

    tdmp_cases = (
        (
            "tdmp/d-gov-018-sequence-authority-removed",
            "D-GOV-018 controls that bounded cycle.",
            "A replacement review controls that sequence.",
        ),
        (
            "tdmp/technical-author-gains-subject-authority",
            "does not become the technical authority for that\nsubject",
            "becomes the technical authority for that\nsubject",
        ),
        (
            "tdmp/second-database-authorised",
            "Do not create a\nnew document-management database",
            "Create a\nnew document-management database",
        ),
        (
            "tdmp/post-validation-review-added",
            "Do not send the document to another\n"
            "documentation, quality, publication, wording, or semantic review.",
            "After final validation, send the document to another\n"
            "documentation, quality, publication, wording, or semantic review.",
        ),
        (
            "tdmp/historical-evidence-rewritten",
            "Do not rewrite a historical record only to apply a newer "
            "documentation\nstandard",
            "Rewrite a historical record to apply a newer documentation\n"
            "standard",
        ),
    )
    for name, original, replacement in tdmp_cases:
        mutated = replace_once(engineering, original, replacement)
        expect_rejected(
            name,
            lambda value=mutated: quality_assurance.validate_tdmp_lifecycle(
                value,
                terminology,
            ),
            "TDMP lifecycle lost:",
        )

    owner_view_status = replace_once(
        plan,
        "Phase 6 has 3/5 accepted exits",
        "Phase 6 has 4/5 accepted exits",
    )
    expect_rejected(
        "tt-doc/owner-view-status-contradiction",
        lambda: progress._validate_owner_view(owner_view_status),
        "project-plan owner view lost or contradicted: Phase 6 has 3/5 "
        "accepted exits",
    )
    owner_view_authority = replace_once(
        plan,
        "This view does not establish authority",
        "This view establishes authority",
    )
    expect_rejected(
        "tt-doc/owner-view-authority-inversion",
        lambda: progress._validate_owner_view(owner_view_authority),
        "project-plan owner view became an authority source",
    )
    owner_view_change = table_row_containing(plan, "**What changed**")
    widened_change = replace_once(
        owner_view_change,
        "accepts Exit 1 for the agreed PR #63 Entry/Exit centreline "
        "comparison scope",
        "accepts Exit 1 for every legacy output and the whole-layout product",
    )
    owner_view_boundary_widened = replace_once(
        plan, owner_view_change, widened_change,
    )
    expect_rejected(
        "tt-doc/owner-view-product-boundary-widened",
        lambda: progress._validate_owner_view(owner_view_boundary_widened),
        "project-plan owner view lost or contradicted: accepts Exit 1 for "
        "the agreed PR #63 Entry/Exit centreline comparison scope",
    )

    owner_view_restarted = replace_once(
        plan,
        "Do not do the measurement again. Do not make the stopped "
        "product change.",
        "Repeat the measurement and make the D-GOV-011 product change.",
    )
    expect_rejected(
        "tt-doc/owner-view-stopped-direction-restarted",
        lambda: progress._validate_owner_view(owner_view_restarted),
        "project-plan owner view lost or contradicted: Do not do the "
        "measurement again. Do not make the stopped product change",
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
        "The [Technical Documentation Profile](ENGINEERING_POLICY.md#"
        "tt-doc-001-tracktemplate-technical-documentation-profile) owns the "
        "policy.",
        "The [Technical Documentation Profile](missing-documentation-profile) "
        "owns the policy.",
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
        "Do not use an external summary, text from a search engine, a blog, "
        "or\n   derived guidance as normative conformance evidence.",
        "Use an external summary as normative conformance evidence.",
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
        "ASD-STE100 reference instructions lack: Do not use an external "
        "summary, text from a search engine, a blog, or derived guidance as "
        "normative conformance evidence.",
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
        "neither official source is available, do not claim that the "
        "canonical prose is\nASD-STE100 Issue 9 conforming",
        "neither official source is available, claim that the canonical prose "
        "is\n"
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
        "Normal CI does not\nuse the ignored PDF.",
        "Normal CI uses\nthe ignored PDF.",
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
        "use an existing owner when possible",
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

    technical_author = read(
        ".agents/skills/tracktemplate-technical-author-lead/SKILL.md"
    )
    technical_author_metadata = read(
        ".agents/skills/tracktemplate-technical-author-lead/agents/openai.yaml"
    )
    implicit_author_disabled = replace_once(
        technical_author_metadata,
        "allow_implicit_invocation: true",
        "# allow_implicit_invocation: true\n  allow_implicit_invocation: false",
    )
    expect_rejected(
        "tdmp/automatic-author-routing-disabled",
        lambda: agent_guidance.validate_technical_author_lifecycle(
            technical_author,
            implicit_author_disabled,
            workflows,
        ),
        "Technical Author Lead is not available for automatic routing",
    )
    author_acceptance_added = replace_once(
        technical_author,
        "The lead does not\nown terminology, the linguistic verdict, "
        "the validation result, or acceptance\nof the controlled baseline.",
        "The lead owns terminology, the linguistic verdict, the validation "
        "result, and acceptance of the controlled baseline.",
    )
    expect_rejected(
        "tdmp/technical-author-self-acceptance-added",
        lambda: agent_guidance.validate_technical_author_lifecycle(
            author_acceptance_added,
            technical_author_metadata,
            workflows,
        ),
        "Technical Author Lead lifecycle lost:",
    )

    documentation_review = read(
        ".agents/skills/tracktemplate-documentation-review/SKILL.md"
    )
    writing_checklist = read(
        ".agents/skills/tracktemplate-documentation-review/references/"
        "writing-checklist.md"
    )
    documentation_review_cases = (
        (
            "tt-doc/documentation-review-controlled-vocabulary-removed",
            "controlled vocabulary",
            "uncontrolled text",
            "controlled vocabulary / technical term / controlled meaning / "
            "part of speech",
        ),
        (
            "tt-doc/documentation-review-term-register-removed",
            "technical-term register",
            "local glossary",
            "technical-term register / technical-term category / controlled "
            "vocabulary does not identify the tracktemplate item",
        ),
        (
            "tt-doc/documentation-review-ordinary-vocabulary-removed",
            "controlled vocabulary does not identify the TrackTemplate item",
            "general wording identifies the TrackTemplate item",
            "technical-term register / technical-term category / controlled "
            "vocabulary does not identify the tracktemplate item",
        ),
        (
            "tt-doc/documentation-review-actor-check-removed",
            "person, tool, or system",
            "text",
            "person, tool, or system / each operation",
        ),
        (
            "tt-doc/documentation-review-antecedent-check-removed",
            "noun to which it refers",
            "nearby word",
            "each pronoun / noun to which it refers / state and result",
        ),
        (
            "tt-doc/documentation-review-noun-group-check-removed",
            "noun group",
            "word sequence",
            "rule 2 / noun group",
        ),
        (
            "tt-doc/documentation-review-instruction-check-weakened",
            "different instruction",
            "same instruction",
            "different instruction / condition before its instruction",
        ),
        (
            "tt-doc/documentation-review-condition-order-inverted",
            "condition before its instruction",
            "condition after its instruction",
            "different instruction / condition before its instruction",
        ),
        (
            "tt-doc/documentation-review-sentence-check-removed",
            "sentence construction",
            "sentence text",
            "sentence construction / paragraph structure",
        ),
        (
            "tt-doc/documentation-review-paragraph-check-removed",
            "paragraph structure",
            "paragraph text",
            "sentence construction / paragraph structure",
        ),
        (
            "tt-doc/documentation-review-full-applicability-weakened",
            "all other applicable Issue 9 requirements",
            "selected Issue 9 requirements",
            "all other applicable issue 9 requirements",
        ),
        (
            "tt-doc/documentation-review-evidence-source-removed",
            "evidence claim",
            "unsupported statement",
            "evidence claim / source",
        ),
        (
            "tt-doc/documentation-review-unresolved-terminology-kept",
            "Resolve all unresolved terminology",
            "Keep unresolved terminology",
            "resolve all unresolved terminology",
        ),
        (
            "tt-doc/documentation-review-unresolved-terminology-removed",
            "Resolve all unresolved terminology",
            "",
            "resolve all unresolved terminology",
        ),
        (
            "tt-doc/documentation-review-unresolved-terminology-weakened",
            "Resolve all unresolved terminology",
            "Resolve some unresolved terminology",
            "resolve all unresolved terminology",
        ),
        (
            "tt-doc/documentation-review-blocker-binding-removed",
            "For each BLOCKED finding, record its exact path and frozen "
            "logical-unit\n    identity. Also record the finding and applicable "
            "formal Issue 9 rule\n    identifiers.",
            "For each BLOCKED finding, record a short note.",
            "for each blocked finding / exact path / frozen logical-unit "
            "identity / finding / applicable formal issue 9 rule identifiers",
        ),
        (
            "tt-doc/documentation-review-empty-blocker-set-authorised",
            "For a `BLOCKED`\n    verdict, make sure that this set is not empty.",
            "For a `BLOCKED`\n    verdict, an empty set is sufficient.",
            "set contains all blocked findings / blocked verdict / set is not "
            "empty",
        ),
    )
    for name, old, new, expected_concepts in documentation_review_cases:
        if old not in writing_checklist:
            raise AssertionError(name + " fixture is stale")
        mutated_checklist = writing_checklist.replace(old, new)
        expect_rejected(
            name,
            lambda value=mutated_checklist: (
                agent_guidance.validate_issue9_documentation_lifecycle(
                    documentation_review,
                    value,
                    workflows,
                    engineering,
                )
            ),
            "documentation checklist lost linguistic-review coverage: "
            + expected_concepts,
        )

    lifecycle_cases = (
        (
            "tt-doc/lifecycle-order-weakened",
            "policy",
            (
                'Use this lifecycle for each material change to canonical '
                'technical prose:\n\n> write once → review once → if necessary, '
                'apply corrections once → record `locked` → validate → finish'
            ),
            "> author → Documentation Review → complete",
            "documentation policy lost simplified lifecycle control: write once",
        ),
        (
            "tt-doc/lifecycle-verdict-removed",
            "policy",
            "The reviewer returns one complete verdict. The verdict is "
            "`ACCEPT`,\n`APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED`.",
            "The reviewer returns `ACCEPT` or `BLOCKED`.",
            "documentation policy lost simplified lifecycle control: only "
            "linguistic conformance review / reviewer returns one complete "
            "verdict. the verdict is accept, approved_with_exact_corrections, "
            "or blocked",
        ),
        (
            "tt-doc/lifecycle-second-review-authorised",
            "policy",
            'Do not add other wording or get another linguistic verdict.',
            "Run a second Documentation Review after a correction.",
            "documentation policy lost simplified lifecycle control: give all "
            "necessary exact replacements in that same review",
        ),
        (
            "tt-doc/lifecycle-empty-blocked-result-authorised",
            "policy",
            "A `BLOCKED` result with\nan empty `blockers` array is invalid.",
            "A `BLOCKED` result with an empty `blockers` array is valid.",
            (
                'documentation policy lost simplified lifecycle control: each '
                'new result with schema version 3 records the full blockers '
                'array / accept and approved_with_exact_corrections use an '
                'empty blockers array / blocked uses a nonempty blockers array '
                '/ exact path / frozen logical-unit identity / finding / formal'
                ' issue 9 rule identifiers / review receipt preserves the '
                'complete blockers array / exact candidate and frozen review '
                'scope bindings / blocked result with an empty blockers array '
                'is invalid'
            ),
        ),
        (
            "tt-doc/lifecycle-final-validation-made-linguistic",
            "policy",
            (
                'It does not judge linguistic conformance or\nchange the review '
                'verdict.'
            ),
            "It independently judges linguistic conformance.",
            (
                'documentation policy lost simplified lifecycle control: it '
                'proves these identities: - source. - exact candidate. - frozen'
                ' review scope. - receipt. - document state and initial review '
                'result - final content.'
            ),
        ),
        (
            "tt-doc/lifecycle-durable-unit-state-added",
            "policy",
            "Keep durable review state at document level.",
            "Keep durable review state for every logical unit.",
            "documentation policy lost simplified lifecycle control: durable "
            "review state at document level",
        ),
        (
            "tt-doc/lifecycle-untouched-legacy-review-added",
            "policy",
            "Do not review an untouched legacy document.",
            "Review every untouched legacy document.",
            "documentation policy lost simplified lifecycle control: do not "
            "review an untouched legacy document",
        ),
        (
            "tt-doc/lifecycle-exact-wording-deferred",
            "skill",
            "Give all necessary exact\nreplacements in this review",
            "let a later reviewer supply replacement wording",
            "documentation review lost simplified lifecycle control: all "
            "necessary exact replacements in this review",
        ),
        (
            "tt-doc/lifecycle-preimage-removed",
            "skill",
            "path, byte range, and\nfrozen preimage",
            "path only",
            "documentation review lost simplified lifecycle control: all "
            "necessary exact replacements in this review",
        ),
        (
            "tt-doc/lifecycle-blocker-set-made-partial",
            "skill",
            "For `BLOCKED`, give the complete set of BLOCKED findings in this "
            "review.",
            "For `BLOCKED`, give a sample of the BLOCKED findings.",
            "documentation review lost simplified lifecycle control: complete "
            "set of blocked findings in this review / at least one finding / "
            "for each finding, give the finding wording and exact path / "
            "applicable formal issue 9 rule identifiers / side, bounds, and "
            "sha-256 of the frozen logical unit / set blocker_set_complete to "
            "true / blockers array is empty",
        ),
        (
            "tt-doc/lifecycle-invented-prose-authorised",
            "workflow",
            (
                'Apply the set of exact corrections once against verified '
                'preimages.'
            ),
            "Apply other useful canonical prose without verified preimages.",
            "AGENT_WORKFLOWS lost the simplified documentation lifecycle",
        ),
        (
            "tt-doc/lifecycle-validation-restarts-review",
            "workflow",
            'Do not repeat\n    linguistic review.',
            "Repeat linguistic review after validation.",
            "AGENT_WORKFLOWS lost the simplified documentation lifecycle",
        ),
        (
            "tt-doc/lifecycle-blocked-completion-made-acceptance",
            "policy",
            (
                'Record the completed lifecycle and\nlinguistic acceptance as '
                'different results.'
            ),
            "Record lifecycle completion as linguistic acceptance.",
            (
                'documentation policy lost simplified lifecycle control: '
                'blocked verdict lets the implementing agent make this one '
                'correction set'
            ),
        ),
        (
            "tt-doc/lifecycle-replacement-candidate-restarts-cycle",
            "policy",
            (
                'different filename, reviewer, or candidate to start the same '
                'cycle again.'
            ),
            "candidate can reset the same cycle.",
            "documentation policy lost simplified lifecycle control: reject "
            "a replacement review result or a change outside that set",
        ),
        (
            "tt-doc/lifecycle-empty-blocker-workflow-authorised",
            "workflow",
            "For `BLOCKED`, record the complete finding set. The finding set\n"
            "    must not be empty.",
            "A `BLOCKED` verdict can record an empty finding set.",
            "AGENT_WORKFLOWS lost the simplified documentation lifecycle",
        ),
    )
    for name, owner, old, new, diagnostic in lifecycle_cases:
        source = {
            "policy": engineering,
            "skill": documentation_review,
            "workflow": workflows,
        }[owner]
        mutated = replace_once(source, old, new)
        expect_rejected(
            name,
            lambda value=mutated, target=owner: (
                agent_guidance.validate_issue9_documentation_lifecycle(
                    value if target == "skill" else documentation_review,
                    writing_checklist,
                    value if target == "workflow" else workflows,
                    value if target == "policy" else engineering,
                )
            ),
            diagnostic,
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
        "examined\nauthority and preservation. No reviewer found a blocking "
        "condition.",
        "The governance review result was PASS WITH FINDINGS. That review "
        "examined\nauthority and preservation. One reviewer found a blocking "
        "condition.",
    )
    expect_rejected(
        "tt-doc-002/review-blocker-inverted",
        lambda: progress._validate_exit_conditions(
            plan,
            phase4_closeout,
            phase5_closeout,
            spelling_review_blocker_inverted,
        ),
        "TT-DOC-002 evidence panel drifted: No reviewer found a blocking "
        "condition",
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
                "resolve-to-bind removal,\nand substitution",
                "resolve-to-bind removal only",
            ),
        ),
        (
            "validation/exit3-active-lock-made-recoverable",
            replace_once(
                validation,
                "Active-lock diagnostics must fail\nclosed",
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
                "observed\ndescriptor-close abandonment",
                "descriptor-close abandonment was not observed",
            ),
        ),
        (
            "validation/exit3-surviving-host-interruption-proof-withdrawn",
            replace_once(
                validation,
                "propagate on a surviving host with truthful chained "
                "`BaseException`\ndiagnostics",
                "surviving-host interruption cleanup remains unproved",
            ),
        ),
        (
            "validation/exit3-add-only-proof-withdrawn",
            replace_once(
                validation,
                "The proof covers the\nbounded D-P6-003 strict add-only, "
                "journal-free implementation",
                "The proof does not cover the bounded D-P6-003 strict "
                "add-only, journal-free implementation",
            ),
        ),
        (
            "validation/exit3-published-final-mutation-authorised",
            replace_once(
                validation,
                "TrackTemplate removes, rewrites, or replaces no published\n"
                "final",
                "TrackTemplate can remove, rewrite, or replace a published "
                "final",
            ),
        ),
        (
            "validation/exit3-command-claims-phase-acceptance",
            replace_once(
                validation,
                "They supply no GUI,\nproduction-output, Phase 6 exit, or release "
                "acceptance",
                "They supply Phase 6 exit and release acceptance",
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


def validate_visible_recovery_mutations() -> None:
    """Reject hidden, destructive, durable, or competing recovery state."""
    policy = read("reference/RECOVERY_AND_BACKUP.md")
    workflows = read("reference/AGENT_WORKFLOWS.md")
    phase_evidence = read("reference/current/PHASE_EVIDENCE.md")
    skills = {
        name: path.read_text(encoding="utf-8")
        for name, path in recovery_controls.RECOVERY_SKILL_PATHS.items()
    }

    def mutate_section_sentence(
        document: str,
        heading: str,
        markers: tuple[str, ...],
        mutation: Callable[[str], str],
    ) -> str:
        """Mutate one sentence selected by meaning in one named section."""
        section = recovery_controls._section(document, heading)
        matches = [
            match.group(1)
            for match in re.finditer(
                r"(?:\A|(?<=[.!?])\s+)(.*?[.!?])(?=\s|\Z)",
                section,
                re.DOTALL,
            )
            if all(
                marker in recovery_controls._semantic_text(match.group(1))
                for marker in markers
            )
        ]
        if len(matches) != 1:
            raise AssertionError(
                "section sentence target must occur once, found {} in {}: {}"
                .format(len(matches), heading, " / ".join(markers))
            )
        sentence = matches[0]
        mutated_sentence = mutation(sentence)
        if mutated_sentence == sentence:
            raise AssertionError(
                "section sentence mutation made no change in " + heading
            )
        mutated_section = replace_once(
            section,
            sentence,
            mutated_sentence,
        )
        return replace_once(document, section, mutated_section)

    def replace_all_in_section(
        document: str,
        heading: str,
        old: str,
        new: str,
    ) -> str:
        """Replace all occurrences of one exact identity in one section."""
        section = recovery_controls._section(document, heading)
        if old not in section:
            raise AssertionError(
                "section identity target is missing in " + heading + ": " + old
            )
        mutated_section = section.replace(old, new)
        return replace_once(document, section, mutated_section)

    policy_cases = (
        (
            "recovery/planned-stash-use-permitted",
            replace_once(
                policy,
                "must not use `git stash` for planned preservation,",
                "may use `git stash` for planned preservation,",
            ),
            "visible recovery policy lacks: must not use git stash for planned "
            "preservation recovery or handoff",
        ),
        (
            "recovery/gate-closes-without-stash-inventory",
            replace_once(
                policy,
                "- Examine the output of `git stash list`.",
                "- Examine the active branch.",
            ),
            "visible recovery policy lacks: examine the output of git stash list",
        ),
        (
            "recovery/retained-stash-treated-as-resolved",
            replace_once(
                policy,
                "A retained stash is unresolved recovery state.",
                "A retained stash is resolved recovery state.",
            ),
            "visible recovery policy contradicts visible recovery state: "
            "a retained stash is resolved recovery state",
        ),
        (
            "recovery/automatic-stash-deletion",
            replace_once(
                policy,
                "A tool must not remove a stash only to get empty `git stash "
                "list`\noutput.",
                "A tool can remove a stash only to get empty `git stash "
                "list`\noutput.",
            ),
            "visible recovery policy lacks: tool must not remove a stash only "
            "to get empty git stash list output",
        ),
        (
            "recovery/unique-stash-content-discarded",
            replace_once(
                policy,
                "Preserve unique content that Git can contain in named Git "
                "state. Preserve\n"
                "  sensitive evidence and local evidence only with approved "
                "independent\n"
                "  preservation.",
                "Discard unique content before inspection.",
            ),
            "visible recovery policy lacks: preserve unique content that git "
            "can contain in named git state",
        ),
        (
            "recovery/emergency-stash-made-durable",
            replace_once(
                policy,
                "Do not use it for\nplanned preservation or handoff.",
                "Use it as durable\nplanned preservation and handoff.",
            ),
            "visible recovery policy lacks: do not use it for planned "
            "preservation or handoff",
        ),
        (
            "recovery/local-evidence-admitted-to-git",
            replace_once(
                policy,
                "Do not stage sensitive evidence or\n"
                "local evidence. Do not commit sensitive evidence or local "
                "evidence. Do not push\n"
                "sensitive evidence or local evidence.",
                "Stage sensitive evidence or local evidence. Commit sensitive "
                "evidence or local evidence. Push\n"
                "sensitive evidence or local evidence.",
            ),
            "visible recovery policy lacks: do not stage sensitive evidence or "
            "local evidence",
        ),
        (
            "recovery/local-evidence-admitted-to-stash",
            replace_once(
                policy,
                "Do not put sensitive evidence or local evidence in a stash.",
                "Put sensitive evidence and local evidence in a stash.",
            ),
            "visible recovery policy lacks: do not put sensitive evidence or "
            "local evidence in a stash",
        ),
        (
            "recovery/local-evidence-admitted-to-recovery-commit",
            replace_once(
                policy,
                "If unique content is sensitive evidence or local evidence, "
                "do not put it in a\n  recovery commit.",
                "If unique content is sensitive evidence or local evidence, "
                "put it in a\n  recovery commit.",
            ),
            "visible recovery policy lacks: unique content is sensitive "
            "evidence or local evidence do not put it in a recovery commit",
        ),
        (
            "recovery/stash-disposition-claims-object-erasure",
            replace_once(
                policy,
                "It does not remove\nits Git objects.",
                "It removes\nits Git objects.",
            ),
            "visible recovery policy lacks: it does not remove its git objects",
        ),
        (
            "recovery/object-residue-gate-closed",
            replace_once(
                policy,
                "If a stash contains sensitive evidence or local evidence, the "
                "recovery gate\ndoes not have a complete result.",
                "If a stash contains sensitive evidence or local evidence, the "
                "recovery gate\nhas a complete result.",
            ),
            "visible recovery policy lacks: stash contains sensitive evidence "
            "or local evidence the recovery gate does not have a complete result",
        ),
        (
            "recovery/automatic-object-deletion-permitted",
            replace_once(
                policy,
                "Do not use an automatic\noperation to remove Git objects.",
                "Use an automatic operation to remove Git objects.",
            ),
            "visible recovery policy lacks: do not use an automatic operation "
            "to remove git objects",
        ),
        (
            "recovery/stash-branch-removal-uncontrolled",
            replace_once(
                policy,
                "`git stash branch`,\nor other operation that removes a "
                "stash",
                "other operation that removes a stash",
            ),
            "visible recovery policy lacks: do not use drop clear overwrite "
            "pop rewrite git stash branch or other operation that removes "
            "a stash without a report and applicable authority",
        ),
        (
            "recovery/stash-base-omitted",
            replace_once(
                policy,
                "- Record the SHA of the base commit. Record the base tree.",
                "- Do not record the base commit or tree.",
            ),
            "visible recovery policy lacks: sha of the base commit record the "
            "base tree",
        ),
        (
            "recovery/stash-u-tree-split",
            replace_once(
                policy,
                "Git keeps those files\nonly in U.",
                "Git makes a second tree for ignored files.",
            ),
            "visible recovery policy lacks: git keeps those files only in u",
        ),
        (
            "recovery/stash-deletion-delta-omitted",
            replace_once(
                policy,
                "Review each path,\n  file-mode difference, and deletion.",
                "Review only new blobs.",
            ),
            "visible recovery policy lacks: review each path file mode "
            "difference and deletion",
        ),
        (
            "recovery/stash-selector-not-revalidated",
            replace_once(
                policy,
                "Validate that the\n"
                "  stash selector identifies the same stash commit SHA and stash "
                "inventory.",
                "Trust the current selector without another identity check.",
            ),
            "visible recovery policy lacks: stash selector identifies the same "
            "stash commit sha and stash inventory",
        ),
        (
            "recovery/missing-purpose-treated-as-resolved",
            replace_once(
                policy,
                "recovery purpose, stash inventory, unique content, or "
                "stash disposition is\nmissing or changed, fail closed.",
                "stash inventory, unique content, or stash disposition is\n"
                "missing or changed, fail closed.",
            ),
            "visible recovery policy lacks: stash ownership recovery purpose "
            "stash inventory unique content or stash disposition is "
            "missing or changed fail closed",
        ),
        (
            "recovery/post-disposition-inventory-removed",
            replace_once(
                policy,
                "Then, examine the repository, stashes,\n"
                "  and preservation state again. Record the "
                "preservation diff.",
                "Do not inspect the repository after disposition.",
            ),
            "visible recovery policy lacks: record the preservation diff",
        ),
        (
            "recovery/appended-retained-stash-contradiction",
            policy
            + "\n\nA retained stash is resolved recovery state. Close the "
            + "recovery gate while it stays in the inventory.\n",
            "visible recovery policy contradicts visible recovery state: "
            "a retained stash is resolved recovery state",
        ),
    )
    for name, mutated, diagnostic in policy_cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                recovery_controls.validate_visible_recovery_policy(value)
            ),
            diagnostic,
        )

    retirement_policy_heading = "Worktree retirement"
    merged_state_markers = (
        "pull request state merged",
        "gives no removal authority",
    )
    cleanliness_markers = (
        "tracked cleanliness",
        "gives no removal authority",
    )
    retirement_policy_cases = (
        (
            "retirement/merged-state-no-authority-deleted",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                merged_state_markers,
                lambda _sentence: "",
            ),
            "worktree retirement policy lacks: pull request state merged "
            "gives no removal authority",
        ),
        (
            "retirement/merged-state-no-authority-inverted",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                merged_state_markers,
                lambda _sentence: (
                    "The pull-request state `MERGED` gives removal authority."
                ),
            ),
            "worktree retirement policy lacks: pull request state merged "
            "gives no removal authority",
        ),
        (
            "retirement/merged-state-no-authority-weakened",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                merged_state_markers,
                lambda _sentence: (
                    "The pull-request state `MERGED` does not necessarily give "
                    "removal authority."
                ),
            ),
            "worktree retirement policy lacks: pull request state merged "
            "gives no removal authority",
        ),
        (
            "retirement/tracked-cleanliness-no-authority-deleted",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                cleanliness_markers,
                lambda _sentence: "",
            ),
            "worktree retirement policy lacks: tracked cleanliness gives no "
            "removal authority",
        ),
        (
            "retirement/tracked-cleanliness-no-authority-inverted",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                cleanliness_markers,
                lambda _sentence: (
                    "Tracked cleanliness gives removal authority."
                ),
            ),
            "worktree retirement policy lacks: tracked cleanliness gives no "
            "removal authority",
        ),
        (
            "retirement/tracked-cleanliness-no-authority-weakened",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                cleanliness_markers,
                lambda _sentence: (
                    "Tracked cleanliness does not necessarily give removal "
                    "authority."
                ),
            ),
            "worktree retirement policy lacks: tracked cleanliness gives no "
            "removal authority",
        ),
        (
            "retirement/ignored-inventory-omitted",
            replace_once(
                policy,
                "Make a local-state inventory of all files that are not in the "
                "Git index.",
                "Make a local-state inventory of tracked files only.",
            ),
            (
                "worktree retirement policy lacks: make a local state inventory "
                "of all files that are not in the git index"
            ),
        ),
        (
            "retirement/preservation-proof-omitted",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                (
                    "for authoritative local source preserve each item",
                    "in a different location",
                ),
                lambda _sentence: "Assume that another copy exists.",
            ),
            "worktree retirement policy lacks: for authoritative local source "
            "preserve each item in a different location",
        ),
        (
            "retirement/ambiguous-state-does-not-stop",
            replace_once(
                policy,
                "If the retirement plan has ambiguous or uniquely owned state, "
                "keep the worktree.",
                "If the retirement plan has ambiguous or uniquely owned state, "
                "remove the worktree.",
            ),
            (
                "worktree retirement policy lacks: if the retirement plan has "
                "ambiguous or uniquely owned state keep the worktree"
            ),
        ),
        (
            "retirement/force-removal-permitted",
            replace_once(
                policy,
                "Do not use `--force`.",
                "Use `--force` when ignored files remain.",
            ),
            "worktree retirement policy lacks: do not use force",
        ),
        (
            "retirement/branch-deleted-before-worktree",
            mutate_section_sentence(
                policy,
                retirement_policy_heading,
                (
                    "if git worktree list does not contain the worktree",
                    "record the local branch and branch tip",
                ),
                lambda _sentence: (
                    "Before `git worktree list` does not contain the worktree, "
                    "record the local branch and branch tip in phase evidence."
                ),
            ),
            "worktree retirement policy lacks: if git worktree list does not "
            "contain the worktree record the local branch and branch tip",
        ),
    )
    for name, mutated, diagnostic in retirement_policy_cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                recovery_controls.validate_worktree_retirement_policy(value)
            ),
            diagnostic,
        )

    audit = read("tools/repository_safety_audit.py")
    dangerous_audit = audit + (
        "\n\ndef dispose_stash(root):\n"
        "    return _git(root, 'stash', 'drop', 'stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-adds-stash-drop",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            dangerous_audit
        ),
        "safety audit contains a non-read-only Git command",
    )
    force_retirement_audit = audit + (
        "\n\ndef force_retire(root):\n"
        "    return _git(root, 'worktree', 'remove', '--force', '/tmp/example')\n"
    )
    expect_rejected(
        "retirement/safety-audit-adds-force-removal",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            force_retirement_audit
        ),
        "safety audit contains a non-read-only Git command",
    )
    exposed_audit = audit + (
        "\n\ndef expose_stash(root):\n"
        "    return _git(root, 'stash', 'show', '-p', 'stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-exposes-stash-patch",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            exposed_audit
        ),
        "safety audit contains a non-private stash command",
    )
    os_bypass_audit = audit + (
        "\n\ndef dispose_stash_with_os():\n"
        "    return os.system('git stash drop stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-adds-os-system-bypass",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            os_bypass_audit
        ),
        "safety audit bypasses the Git wrapper",
    )
    aliased_os_audit = audit + (
        "\n\nimport os as runner_os\n"
        "def dispose_stash_with_aliased_os():\n"
        "    return runner_os.system('git stash drop stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-adds-aliased-os-bypass",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            aliased_os_audit
        ),
        "safety audit aliases process-capable modules",
    )
    subprocess_shell_audit = audit + (
        "\n\ndef dispose_stash_with_getoutput():\n"
        "    return subprocess.getoutput('git stash drop stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-adds-subprocess-shell-bypass",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            subprocess_shell_audit
        ),
        "safety audit bypasses the Git wrapper",
    )
    module_alias_audit = audit + (
        "\n\nrunner_os = os\n"
        "def dispose_stash_with_module_alias():\n"
        "    return runner_os.system('git stash drop stash@{0}')\n"
    )
    expect_rejected(
        "recovery/safety-audit-adds-module-alias-bypass",
        lambda: recovery_controls.validate_safety_audit_git_commands(
            module_alias_audit
        ),
        "safety audit aliases process-capable modules",
    )

    weakened_workflows = replace_once(
        workflows,
        "get applicable authority for the exact disposition",
        "skip authority for the exact disposition",
    )
    expect_rejected(
        "recovery/workflow-removes-disposition-authority",
        lambda: recovery_controls.validate_visible_recovery_routing(
            weakened_workflows,
            skills,
        ),
        "agent workflow recovery routing lacks: get applicable authority for "
        "the exact disposition",
    )
    contradictory_workflows = workflows + (
        "\n\nA retained stash is resolved recovery state.\n"
    )
    expect_rejected(
        "recovery/workflow-appends-resolved-stash-contradiction",
        lambda: recovery_controls.validate_visible_recovery_routing(
            contradictory_workflows,
            skills,
        ),
        "agent workflow recovery routing contradicts visible recovery state: "
        "a retained stash is resolved recovery state",
    )
    workflow_retirement_cases = (
        (
            "retirement/workflow-adds-merged-state-shortcut",
            mutate_section_sentence(
                workflows,
                "Session continuity",
                merged_state_markers,
                lambda _sentence: (
                    "The pull-request state `MERGED` gives removal authority."
                ),
            ),
            "agent workflow retirement routing lacks: pull request state "
            "merged gives no removal authority",
        ),
        (
            "retirement/workflow-adds-cleanliness-shortcut",
            mutate_section_sentence(
                workflows,
                "Session continuity",
                cleanliness_markers,
                lambda _sentence: (
                    "Tracked cleanliness gives removal authority."
                ),
            ),
            "agent workflow retirement routing lacks: tracked cleanliness "
            "gives no removal authority",
        ),
    )
    for name, mutated, diagnostic in workflow_retirement_cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                recovery_controls.validate_worktree_retirement_routing(
                    value,
                    skills,
                )
            ),
            diagnostic,
        )

    missing_snapshot = replace_once(
        phase_evidence,
        "[2026-08-01 repository snapshot]"
        "(../backup-records/2026-08-01-phase5-closeout-snapshot.md)",
        "2026-08-01 repository snapshot",
    )
    expect_rejected(
        "recovery/phase-evidence-loses-independent-preservation-link",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            missing_snapshot
        ),
        "recovery phase evidence lacks independent-preservation linkage",
    )
    unique_state_reintroduced = replace_once(
        phase_evidence,
        "The stash had no repository information that named state or\n"
        "approved preservation did not contain.",
        "The stash had repository information that no preservation contained.",
    )
    expect_rejected(
        "recovery/phase-evidence-overlooks-unique-state",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            unique_state_reintroduced
        ),
        "recovery phase evidence lacks: stash had no repository information "
        "that named state or approved preservation did not contain",
    )
    contamination_overstated = replace_once(
        phase_evidence,
        "Thus, current evidence\nidentifies no incident with sensitive evidence "
        "or local evidence in this\nrepository.",
        "Thus, current evidence identifies an unresolved incident with\n"
        "sensitive evidence in this repository.",
    )
    expect_rejected(
        "recovery/phase-evidence-invents-contamination-incident",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            contamination_overstated
        ),
        "recovery phase evidence lacks: current evidence identifies no incident "
        "with sensitive evidence or local evidence in this repository",
    )
    cleanup_scope_added = replace_once(
        phase_evidence,
        "This migration does not define a procedure to remove Git objects. It "
        "does not\ndefine a procedure to replace a repository. It does not "
        "change independent\npreservation.",
        "This migration defines Git object removal and backup replacement.",
    )
    expect_rejected(
        "recovery/phase-evidence-adds-object-cleanup-scope",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            cleanup_scope_added
        ),
        "recovery phase evidence lacks: does not define a procedure to remove "
        "git objects",
    )
    ambiguous_merge = replace_once(
        phase_evidence,
        "`dd768006c83b9bc26e3d2e6d6e13b2cebed40173` on `main` contained "
        "that state.",
        "A merge commit on `main` contained that state.",
    )
    expect_rejected(
        "recovery/phase-evidence-loses-exact-merge-identity",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            ambiguous_merge
        ),
        "recovery phase evidence lacks: merge commit "
        "dd768006c83b9bc26e3d2e6d6e13b2cebed40173 on main contained that state",
    )
    accidental_stash_evidence_removed = replace_once(
        phase_evidence,
        "During independent review, a command made an emergency stash\n"
        "`e52bd0409feee7dc7dce9fc853a3bed99081c948` by accident.",
        "During independent review, no recovery state changed.",
    )
    expect_rejected(
        "recovery/phase-evidence-loses-accidental-stash-identity",
        lambda: recovery_controls.validate_recovery_phase_evidence(
            accidental_stash_evidence_removed
        ),
        "recovery phase evidence lacks: during independent review a command "
        "made an emergency stash "
        "e52bd0409feee7dc7dce9fc853a3bed99081c948 by accident",
    )

    ambiguous_retirement_overlooked = replace_once(
        phase_evidence,
        "| Ambiguous or uniquely owned state | 0 | 0 |",
        "| Ambiguous or uniquely owned state | 1 | 1 |",
    )
    expect_rejected(
        "retirement/phase-evidence-overlooks-ambiguous-state",
        lambda: recovery_controls.validate_worktree_retirement_phase_evidence(
            ambiguous_retirement_overlooked
        ),
        "worktree retirement phase evidence lacks: ambiguous or uniquely "
        "owned state 0 0",
    )
    force_retirement_claimed = replace_once(
        mutate_section_sentence(
            phase_evidence,
            "Workflow migration for worktree retirement",
            ("implementing agent used git worktree remove without force",),
            lambda _sentence: (
                "The implementing agent used `git worktree remove` with "
                "`--force`."
            ),
        ),
        "with `--force`.",
        "with `--force`.",
    )
    expect_rejected(
        "retirement/phase-evidence-claims-force-removal",
        lambda: recovery_controls.validate_worktree_retirement_phase_evidence(
            force_retirement_claimed
        ),
        "worktree retirement phase evidence lacks: implementing agent used "
        "git worktree remove without force",
    )
    cycle_3_started_early = mutate_section_sentence(
        phase_evidence,
        "Workflow migration for worktree retirement",
        ("project owner gives no project authority to start cycle 3",),
        lambda _sentence: (
            "The project owner gives project authority to start Cycle 3."
        ),
    )
    expect_rejected(
        "retirement/phase-evidence-starts-cycle-3-early",
        lambda: recovery_controls.validate_worktree_retirement_phase_evidence(
            cycle_3_started_early
        ),
        "worktree retirement phase evidence lacks: project owner gives no "
        "project authority to start cycle 3",
    )
    historical_cleanliness_overstated = mutate_section_sentence(
        phase_evidence,
        "Workflow migration for worktree retirement",
        ("it found no tracked change",),
        lambda _sentence: "It had tracked cleanliness.",
    )
    expect_rejected(
        "retirement/phase-evidence-overstates-historical-cleanliness",
        lambda: recovery_controls.validate_worktree_retirement_phase_evidence(
            historical_cleanliness_overstated
        ),
        "worktree retirement phase evidence overstates: it had tracked "
        "cleanliness",
    )
    retrospective_authority_phrase = "It gives no retrospective authority."
    if retrospective_authority_phrase not in phase_evidence:
        raise AssertionError("retrospective-authority fixture is stale")
    retrospective_authority_added = phase_evidence.replace(
        retrospective_authority_phrase,
        "This decision gives retrospective authority.",
        1,
    )
    expect_rejected(
        "retirement/phase-evidence-manufactures-retrospective-authority",
        lambda: recovery_controls.validate_worktree_retirement_phase_evidence(
            retrospective_authority_added
        ),
        "worktree retirement phase evidence overstates: this decision gives "
        "retrospective authority",
    )

    retirement_assurance_cases = (
        (
            "retirement/phase-evidence-loses-official-source-path",
            mutate_section_sentence(
                phase_evidence,
                "Workflow migration for worktree retirement",
                (
                    "asd ste100 issue 9 pdf stayed at the primary source path",
                ),
                lambda _sentence: "",
            ),
            "worktree retirement phase evidence lacks: asd ste100 issue 9 pdf "
            "stayed at the primary source path",
        ),
        (
            "retirement/phase-evidence-inverts-source-identity",
            mutate_section_sentence(
                phase_evidence,
                "Workflow migration for worktree retirement",
                ("pdf kept its source identity",),
                lambda _sentence: "The PDF lost its source identity.",
            ),
            "worktree retirement phase evidence lacks: pdf kept its source "
            "identity",
        ),
        (
            "retirement/phase-evidence-removes-author-review-duty",
            mutate_section_sentence(
                phase_evidence,
                "Workflow migration for worktree retirement",
                ("author completes the conformance review",),
                lambda _sentence: (
                    "The author does not complete the conformance review."
                ),
            ),
            "worktree retirement phase evidence lacks: author completes the "
            "conformance review",
        ),
        (
            "retirement/phase-evidence-weakens-full-applicability",
            mutate_section_sentence(
                phase_evidence,
                "Workflow migration for worktree retirement",
                (
                    "author reviews each logical unit with a material edit",
                    "all applicable rules 1 through 9",
                ),
                lambda _sentence: (
                    "The author reviews each logical unit with a material edit "
                    "against selected Issue 9 rules."
                ),
            ),
            "worktree retirement phase evidence lacks: author reviews each "
            "logical unit with a material edit against all applicable rules 1 "
            "through 9",
        ),
        (
            "retirement/phase-evidence-removes-official-pdf-duty",
            mutate_section_sentence(
                phase_evidence,
                "Workflow migration for worktree retirement",
                ("author uses the official pdf with sha 256",),
                lambda _sentence: "The author uses a local summary.",
            ),
            "worktree retirement phase evidence lacks: author uses the official "
            "pdf with sha 256",
        ),
        (
            "retirement/phase-evidence-loses-verified-source-sha",
            replace_all_in_section(
                phase_evidence,
                "Workflow migration for worktree retirement",
                "d1f4ea9e7cd6e46b47aa9057209f99e78c0e9cfc4e27a5b07895b05c1a166431",
                "0000000000000000000000000000000000000000000000000000000000000000",
            ),
            "worktree retirement evidence lacks identity: "
            "d1f4ea9e7cd6e46b47aa9057209f99e78c0e9cfc4e27a5b07895b05c1a166431",
        ),
    )
    for name, mutated, diagnostic in retirement_assurance_cases:
        expect_rejected(
            name,
            lambda value=mutated: (
                recovery_controls.validate_worktree_retirement_phase_evidence(
                    value
                )
            ),
            diagnostic,
        )

    accepted_recovery_state = replace_once(
        skills["ide"],
        "It is not\naccepted product state.",
        "It is accepted product state.",
    )
    accepted_skills = dict(skills)
    accepted_skills["ide"] = accepted_recovery_state
    expect_rejected(
        "recovery/recovery-worktree-made-accepted-product-state",
        lambda: recovery_controls.validate_visible_recovery_routing(
            workflows,
            accepted_skills,
        ),
        "ide recovery routing lacks: not accepted product state",
    )

    markdown = recovery_controls._load_tracked_markdown()
    competing = dict(markdown)
    context_path = ".agents/skills/tracktemplate-context-recovery/SKILL.md"
    competing[context_path] = (
        competing[context_path]
        + "\n## Git stash policy owner\n\n"
        + "This skill owns policy for planned Git recovery.\n"
    )
    expect_rejected(
        "recovery/skill-becomes-competing-policy-owner",
        lambda: recovery_controls.validate_recovery_policy_owner(competing),
        "competing recovery policy owner: " + context_path,
    )
    body_competing = dict(markdown)
    body_competing[context_path] = (
        body_competing[context_path]
        + "\n## Notes\n\n"
        + "This skill owns the policy for Git stash recovery.\n"
    )
    expect_rejected(
        "recovery/skill-body-becomes-competing-policy-owner",
        lambda: recovery_controls.validate_recovery_policy_owner(body_competing),
        "competing recovery policy owner: " + context_path,
    )

    learning = read("reference/LEARNING_FROM_EXPERIENCE.md")
    weakened_lfe = replace_once(
        learning,
        "Before a stash disposition, validate that unique content stays "
        "available. Then, get applicable authority.",
        "Dispose of each stash when the work is complete.",
    )
    expect_rejected(
        "recovery/lfe-reusable-rule-loses-loss-proof",
        lambda: recovery_controls.validate_recovery_lfe(weakened_lfe),
        "LFE-020 reusable rule lacks: before a stash disposition validate that "
        "unique content stays available",
    )
    purposeless_lfe = replace_once(
        learning,
        "If its recovery purpose or stash disposition is missing, do not give "
        "the recovery gate a complete result.",
        "If its stash disposition is missing, do not give the recovery gate a "
        "complete result.",
    )
    expect_rejected(
        "recovery/lfe-reusable-rule-loses-purpose",
        lambda: recovery_controls.validate_recovery_lfe(purposeless_lfe),
        "LFE-020 reusable rule lacks: if its recovery purpose or stash "
        "disposition is missing do not give the recovery gate a complete result",
    )
    unlinked_lfe = replace_once(
        learning,
        "[recovery evidence]"
        "(current/PHASE_EVIDENCE.md#visible-recovery-state-workflow-migration)",
        "recovery evidence",
    )
    expect_rejected(
        "recovery/lfe-loses-phase-evidence-link",
        lambda: recovery_controls.validate_recovery_lfe(unlinked_lfe),
        "LFE-020 lacks canonical link: current/PHASE_EVIDENCE.md"
        "#visible-recovery-state-workflow-migration",
    )
    lfe_020_row = table_row_containing(learning, "| LFE-020 /")
    contradictory_lfe = replace_once(
        learning,
        lfe_020_row,
        lfe_020_row.removesuffix(" |")
        + " A retained stash is resolved recovery state. |",
    )
    expect_rejected(
        "recovery/lfe-appends-resolved-stash-contradiction",
        lambda: recovery_controls.validate_recovery_lfe(contradictory_lfe),
        "LFE-020 contradicts visible recovery state: a retained stash is "
        "resolved recovery state",
    )
    lfe_021_row = table_row_containing(learning, "| LFE-021 /")
    weakened_retirement_lfe_row = replace_once(
        lfe_021_row,
        "Before worktree removal, make a local-state inventory.",
        "A clean merged worktree needs no local-state inventory.",
    )
    weakened_retirement_lfe = replace_once(
        learning,
        lfe_021_row,
        weakened_retirement_lfe_row,
    )
    expect_rejected(
        "retirement/lfe-loses-local-state-inventory",
        lambda: recovery_controls.validate_recovery_lfe(
            weakened_retirement_lfe
        ),
        "LFE-021 reusable rule lacks: before worktree removal make a local "
        "state inventory",
    )
    weakened_lfe_rule = mutate_section_sentence(
        learning,
        "Ledger rules",
        (
            "if a semantic control can prevent the same problem",
            "add the semantic control",
        ),
        lambda _sentence: (
            "If row length can prevent the same problem, examine row length."
        ),
    )
    expect_rejected(
        "lfe/application-loses-regression-question",
        lambda: recovery_controls.validate_recovery_lfe(
            weakened_lfe_rule
        ),
        "LFE rule lacks: if a semantic control can prevent the same problem "
        "add the semantic control",
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
        "It compares selected work with credible authorised\nalternatives. "
        "These can include maintenance, evidence, and risk-reduction\nwork.",
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
        "vision-informed programme orchestrator",
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
    validate_finite_documentation_mutations()
    validate_documentation_profile_mutations()
    validate_transition_export_validation_mutations()
    validate_visible_recovery_mutations()
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
