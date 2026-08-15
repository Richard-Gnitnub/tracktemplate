#!/usr/bin/env python3
"""Validate the compact dashboard, frozen closeouts, and current records."""

from __future__ import annotations

import json
import pathlib
import re

from governance_markdown import direct_section_content


ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
PRODUCT_VISION_PATH = ROOT / "reference" / "PRODUCT_VISION.md"
CAPABILITY_MATRIX_PATH = ROOT / "reference" / "CAPABILITY_MATRIX.md"
ARCHITECTURE_PATH = ROOT / "reference" / "ARCHITECTURE.md"
VALIDATION_PATH = ROOT / "reference" / "VALIDATION.md"
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
EXPECTED_PHASE6_DECISION_IDS = {
    "D-P6-001",
    "D-GOV-005",
    "D-P6-002",
    "D-P6-003",
    "D-P6-004",
    "D-P6-005",
    "TT-DOC-001",
}
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
EXPECTED_EXIT2_DECISION = (
    "Accept Phase 6 Exit 2 and retain Exit 3 Pending."
)
EXPECTED_EXIT2_AUTHORITY = (
    "At accepted `main` source state "
    "`a5b6a79bf3e73e1673d440077bd65000986bb4c7`, accept Phase 6 Exit 2, "
    "“No transient production objects leak into the editable document”, as "
    "`Evidenced` and owner-accepted only for the accepted B16 Entry/Exit "
    "transition exact-validation and export routes assessed by this panel. "
    "Phase 6 advances from 0/5 to 1/5. Exit 3 remains Pending until its six "
    "recorded required-before-exit conditions are satisfied and a fresh Level "
    "3 evidence-admission review recommends acceptance."
)
EXPECTED_EXIT2_EXCLUSIONS = (
    "No Phase 6 exit 1, 3, 4 or 5; production or physical-output clearance; "
    "`project-cleared` status; output equivalence; product-wide export roster; "
    "GUI or operator workflow; persisted or retained exact geometry; "
    "whole-B14 or whole-layout parity; legacy retirement; performance "
    "acceptance; packaging or release authority; or risk downgrade is granted. "
    "The export remains private-development with deliberately `unknown` "
    "project status, and PR #33 performance evidence does not satisfy Exit 4."
)
EXPECTED_EXIT3_RECOVERY_DECISION = (
    "Select strict add-only, journal-free monotonic completion for Exit 3 "
    "recovery."
)
EXPECTED_EXIT3_RECOVERY_AUTHORITY = (
    "At accepted `main` source state "
    "`cee78cff84618c6a5be3be99714682f5822c814f`, select strict add-only, "
    "journal-free monotonic completion as the required cross-process "
    "recovery-authority contract for the bounded B16 Entry/Exit "
    "DXF-and-manifest pair. A later bounded Level 2 tranche is authorised to "
    "recompute the exact expected pair, create unpublished payloads only in "
    "anonymous creation-bound descriptors, abandon unpublished work only by "
    "closing those descriptors, inspect existing finals without acquiring "
    "mutation authority, and publish only by adding an absent final pathname "
    "without overwrite. The first successful final link permanently ends "
    "rollback. No published final may be unlinked, renamed, rewritten, "
    "truncated or replaced; authenticating or verifying a pathname does not "
    "grant deletion authority, and POSIX pathname deletion has no "
    "expected-inode atomic condition. After any post-publication failure, all "
    "published finals are preserved, including any exact partial or complete "
    "output pair. A later invocation may add only an absent exact counterpart, "
    "and success may be reported only after the complete final pair is "
    "independently revalidated as exact. Mismatch, non-regular finals, symbolic "
    "links, collision, replay, substitution, inconsistency, ambiguity or "
    "unsupported primitives fail closed without further mutation. Foreign or "
    "uncertain destination state is never removed, and `cleanup_complete`, "
    "`recoverable`, `destination_changed` and related diagnostics must describe "
    "the state actually retained. `recoverable=True` is permitted only after "
    "independently revalidating an exact zero-member, partial or complete "
    "destination with safe retry or remaining add-only authority; ambiguity, "
    "mismatch, uncertain durability or an unsupported primitive remains "
    "non-recoverable. Any successful addition requires "
    "`destination_changed=True`, and any surviving published final on a failed "
    "invocation requires `cleanup_complete=False`. Identical complete-pair "
    "reuse, deterministic filenames and bytes, manifest schema and contract "
    "IDs, the two-file layout, no-overwrite behaviour and "
    "`reuse-identical-or-fail` collision refusal remain unchanged; one exact "
    "regular partial member may now be completed rather than treated as a "
    "collision. "
    "Phase 6 remains 1/5 and Exit 3 remains Pending until implementation, "
    "focused interruption/recovery evidence and a fresh Level 3 "
    "evidence-admission review."
)
EXPECTED_EXIT3_RECOVERY_EXCLUSIONS = (
    "No product code is changed by this decision. It does not mark Exit 3 or "
    "another exit `Evidenced` or owner-accepted; grant production, "
    "physical-output, `project-cleared`, equivalence, GUI, operator, "
    "wider-family, performance, legacy-retirement, packaging or release "
    "authority; or change a risk state. It does not authorise "
    "post-publication unlink, rename, rewrite, truncation, replacement or "
    "pathname-based rollback; reading or deleting pre-existing controls; "
    "mutation of any foreign or uncertain destination state; deriving deletion "
    "authority from equality, metadata or pathname verification; changing "
    "output names/bytes/schema/layout, contract/result IDs or the "
    "collision-policy value; or adding a trust service, generic storage "
    "framework or runtime dependency."
)
EXPECTED_EXIT3_ACCEPTANCE_DECISION = (
    "Accept Phase 6 Exit 3 for the bounded B16 Entry/Exit exporter."
)
EXPECTED_EXIT3_ACCEPTANCE_SCOPE = (
    "At protected `main` `7198b05b6a4b7e4654b7d02d0bad4e5cf627a799`, I "
    "accept Phase 6 Exit 3, “Export is deterministic and failure-safe”, as "
    "Evidenced and owner-accepted only for the bounded B16 Entry/Exit "
    "private-development DXF-and-dependency-manifest route under D-P6-003 "
    "and D-P6-004. Phase 6 advances from 1/5 to 2/5."
)
EXPECTED_EXIT3_ACCEPTANCE_COVERAGE = (
    "This acceptance covers deterministic names, bytes, hashes, schema and "
    "identifiers; descriptor-relative add-only/no-overwrite publication; "
    "exact-complete reuse; exact-partial monotonic completion; supported "
    "exception, cancellation, retained interruption, staging, publication, "
    "cleanup, durability and process-termination evidence; qualified "
    "FreeCAD import and host execution; truthful conservative diagnostics; "
    "and restart-based containment with independent destination revalidation."
)
EXPECTED_EXIT3_ACCEPTANCE_LIMITATIONS = (
    "It does not extend assurance to arbitrary instruction-level "
    "asynchronous interruption or repeated interruption of cleanup, physical "
    "power loss, unqualified hosts or filesystems, continuously active "
    "external mutation after final observation, or destructive or manual "
    "recovery. Existing and published finals must never be deleted, renamed, "
    "rewritten, truncated, replaced or manually altered to recover."
)
EXPECTED_EXIT3_ACCEPTANCE_EXCLUSIONS = (
    "Output remains private-development with project status `unknown`. No "
    "Exit 1, 4 or 5; production or physical-output clearance; "
    "`project-cleared` status; output equivalence; GUI/operator or "
    "wider-family authority; persisted schema; retained exact geometry; "
    "performance acceptance; legacy retirement; packaging; release; risk "
    "downgrade; or later-phase authority is granted."
)
EXPECTED_EXIT3_ACCEPTANCE_AUTHORITY = (
    EXPECTED_EXIT3_ACCEPTANCE_SCOPE
    + " "
    + EXPECTED_EXIT3_ACCEPTANCE_COVERAGE
)
EXPECTED_EXIT3_ACCEPTANCE_STRUCTURED_EXCLUSIONS = (
    EXPECTED_EXIT3_ACCEPTANCE_LIMITATIONS
    + " "
    + EXPECTED_EXIT3_ACCEPTANCE_EXCLUSIONS
)
EXPECTED_TT_DOC_DECISION = (
    "Adopt the TrackTemplate Technical Documentation Profile."
)
EXPECTED_PHASE6_DISPOSITIONS = [
    (
        "Pending — exact-validation and private-development DXF evidence "
        "exists, but agreed output equivalence and production clearance "
        "remain absent"
    ),
    (
        "Evidenced and owner-accepted under D-P6-002 — bounded to the accepted "
        "B16 Entry/Exit exact-validation and export routes with the recorded "
        "limitations"
    ),
    (
        "Evidenced and owner-accepted under D-P6-005 — bounded to the "
        "private-development B16 Entry/Exit DXF-and-manifest route under "
        "D-P6-003 and D-P6-004 with the recorded platform, recovery and "
        "assurance limitations; project status remains `unknown`"
    ),
    (
        "Pending — PR #33 accounts for complete cold/warm Edit, Validate and "
        "Export cost, but the edit range overlaps Phase 5 and demonstrates no "
        "improvement beyond normal measurement noise; it does not satisfy "
        "Exit 4"
    ),
    (
        "Pending — B14 remains available, but whole-scope parity and retirement "
        "authority remain absent"
    ),
]
EXPECTED_PHASE6_PERFORMANCE_DISPOSITION = (
    "Under D-P6-002, Phase 6 remains 1/5 with Exit 2 alone Evidenced and "
    "owner-accepted; this evidence does not satisfy Exit 4, which remains "
    "Pending."
)
EXPECTED_EXIT3_CONDITION_ROWS = {
    "Export transaction owner": [
        "Export transaction owner",
        "Before another Exit 3 panel",
        (
            "Provide atomic durable commit or an explicit recoverable "
            "transaction protocol for the DXF-and-manifest set."
        ),
    ],
    "Export path-safety owner": [
        "Export path-safety owner",
        "Before another Exit 3 panel",
        (
            "Provide descriptor-relative path control sufficient to address "
            "rename and symbolic-link races."
        ),
    ],
    "Export validation owner": [
        "Export validation owner",
        "Before another Exit 3 panel",
        (
            "Provide focused interruption, partial-commit and recovery "
            "evidence."
        ),
    ],
    "Qualified FreeCAD validation owner": [
        "Qualified FreeCAD validation owner",
        "Before another Exit 3 panel",
        (
            "Import and validate the zero-length DXF POINT in the qualified "
            "FreeCAD profile."
        ),
    ],
    "Validation-document owner": [
        "Validation-document owner",
        "Before another Exit 3 panel",
        (
            "Register the qualified command and required success sentinel "
            "durably in reference/VALIDATION.md."
        ),
    ],
    "Phase owner and independent reviewers": [
        "Phase owner and independent reviewers",
        "After the preceding conditions pass",
        (
            "Conduct a fresh Level 3 evidence-admission review before any "
            "Exit 3 acceptance."
        ),
    ],
}
EXPECTED_EXIT3_RECOVERY_ROWS = {
    "Recoverable DXF-and-manifest transaction": [
        "Recoverable DXF-and-manifest transaction",
        (
            "Open technical gap — durable live-invocation controls and "
            "in-process rollback are present, but no independently trusted "
            "creation authority supports cross-process automatic recovery"
        ),
    ],
    "Descriptor-relative rename and symbolic-link control": [
        "Descriptor-relative rename and symbolic-link control",
        (
            "Present — all transaction operations use the bound directory "
            "descriptor and focused replacement proofs fail closed; not yet "
            "admitted by a Level 3 panel"
        ),
    ],
    "Interruption, partial-commit and recovery proof": [
        "Interruption, partial-commit and recovery proof",
        (
            "Open technical gap — abrupt one-link and two-link termination now "
            "prove exact residue preservation and fail-closed rejection, not "
            "automatic recovery"
        ),
    ],
    "Qualified zero-length POINT import": [
        "Qualified zero-length POINT import",
        (
            "Present — qualified FreeCAD imports one exact vertex and restores "
            "host state; not yet admitted by a Level 3 panel"
        ),
    ],
    "Durable qualified command and sentinel": [
        "Durable qualified command and sentinel",
        (
            "Present in reference/VALIDATION.md; not yet admitted by a Level "
            "3 panel"
        ),
    ],
    "Fresh Level 3 evidence-admission review": [
        "Fresh Level 3 evidence-admission review",
        "Open — required before Exit 3 can be recommended or accepted",
    ],
}
EXPECTED_VISION_DECISION = (
    "Adopt the TrackTemplate product vision and vision-led execution model."
)
EXPECTED_VISION_AUTHORITY = (
    "`reference/PRODUCT_VISION.md` owns product purpose, the current "
    "TrackTemplate Core migration, the subsequent Layout Editor horizon and "
    "migration-completion meaning. Architecture adopts D-GOV-005-A through "
    "D-GOV-005-G for canonical state, immutable presentation snapshots, "
    "batched Coin presentation, the lightweight normal editing view, "
    "on-demand exact geometry, ViewProvider-owned display modes, presentation "
    "performance and product horizons. Work selection follows product vision, "
    "architecture, authorised programme, active phase, current evidence, "
    "bounded work item, delegated assignment, then independent evidence and "
    "acceptance. The Chief of Staff and literal `$tracktemplate-continue` "
    "workflow apply that vision-led selection, loop-prevention and "
    "result-accountability model."
)
EXPECTED_VISION_EXCLUSIONS = (
    "Product vision supplies direction, not scope. D-GOV-004 continues to own "
    "literal continuation invocation and its one-cycle Level 1/2 execution "
    "limit. No Phase 6 criterion or exit status changes. No shared renderer, "
    "ViewProvider replacement, exact-geometry expansion, output, persistence, "
    "railway calculation, map/background, connected placement, constituent "
    "editing or layout solving is implemented or authorised. No pull request, "
    "migration completion, output clearance, package, release or phase exit "
    "is accepted; draft PR #31 remains separate and unaccepted."
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


def _semantic_markdown(value: str) -> str:
    """Normalise presentation whitespace while retaining Markdown targets."""
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "-", value)
    value = value.replace("**", "").replace("`", "")
    return " ".join(value.split())


def _semantic_text(value: str) -> str:
    """Normalise presentation Markdown after its structure is isolated."""
    return MARKDOWN_LINK_RE.sub(r"\1", _semantic_markdown(value))


def _document_preamble(text: str, title: str) -> str:
    """Return direct document preamble content before any child heading."""
    title_marker = "# " + title
    _require(
        text.startswith(title_marker + "\n"),
        "document title drifted: " + title,
    )
    return direct_section_content(text, title, level=1)


def _raw_paragraphs(text: str) -> list[str]:
    """Return non-empty Markdown paragraphs without semantic normalisation."""
    return [
        block
        for block in re.split(r"\n[ \t]*\n", text)
        if block.strip()
    ]


def _paragraphs(text: str) -> list[str]:
    """Return semantic paragraphs while ignoring line wrapping and Markdown."""
    return [_semantic_text(block) for block in _raw_paragraphs(text)]


def _require_paragraph(text: str, expected: str, message: str) -> str:
    """Require one exact semantic paragraph and return its raw Markdown."""
    expected_semantic = _semantic_text(expected)
    for paragraph in _raw_paragraphs(text):
        if _semantic_text(paragraph) == expected_semantic:
            return paragraph
    raise AssertionError(message)


def _require_links(
    paragraph: str,
    expected: tuple[tuple[str, str], ...],
    message: str,
) -> None:
    """Require the exact label-target associations in one paragraph."""
    actual = tuple(
        (_semantic_text(label), target.strip())
        for label, target in MARKDOWN_LINK_RE.findall(paragraph)
    )
    _require(actual == expected, message)


def _table_blocks(section: str) -> list[list[str]]:
    """Return each contiguous Markdown table as a separate line block."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section.splitlines():
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _structured_table_rows(
    section: str,
    expected_header: tuple[str, ...],
    table_name: str,
) -> dict[str, list[str]]:
    """Return rows from exactly one table with the expected header."""
    semantic_header = [_semantic_markdown(cell) for cell in expected_header]
    candidates = []
    for block in _table_blocks(section):
        header = [_semantic_markdown(cell) for cell in _cells(block[0])]
        if header == semantic_header:
            candidates.append(block)
    _require(
        len(candidates) == 1,
        table_name + " must contain exactly one governing table",
    )
    block = candidates[0]
    _require(
        len(block) >= 2
        and len(_cells(block[1])) == len(expected_header)
        and all(
            re.fullmatch(r":?-{3,}:?", cell) is not None
            for cell in _cells(block[1])
        ),
        table_name + " has an invalid Markdown separator row",
    )

    rows: dict[str, list[str]] = {}
    for line in block[2:]:
        cells = _cells(line)
        _require(
            len(cells) == len(expected_header),
            table_name + " contains a row with the wrong cell count",
        )
        semantic_cells = [_semantic_markdown(cell) for cell in cells]
        _require(
            semantic_cells[0] not in rows,
            "duplicate structured governance row: " + semantic_cells[0],
        )
        rows[semantic_cells[0]] = semantic_cells
    return rows


def _numbered_items(section: str) -> list[tuple[int, str]]:
    """Return one Markdown ordered list without depending on line wrapping."""
    items: list[tuple[int, str]] = []
    for match in re.finditer(
        r"^(\d+)\. (.*?)(?=^\d+\. |\n\n|\Z)",
        section,
        re.DOTALL | re.MULTILINE,
    ):
        items.append((int(match.group(1)), _semantic_text(match.group(2))))
    return items


def _section(text: str, heading: str) -> str:
    marker = "## " + heading
    _require(marker in text, "missing project-plan section: " + marker)
    tail = text.split(marker, 1)[1]
    next_heading = re.search(r"^## ", tail, re.MULTILINE)
    return tail if next_heading is None else tail[:next_heading.start()]


def _validate_transition_export_validation(validation: str) -> None:
    """Bind the current commands to bounded D-P6-003 implementation proof."""
    validation_flat = " ".join(validation.split())
    _require(
        (
            ".venv/bin/python "
            "tests/validate_phase6_transition_dxf_export.py"
        )
        in validation
        and (
            "flatpak run --command=FreeCADCmd org.freecad.FreeCAD \\\n"
            "  tests/freecad_validate_phase6_transition_dxf_export.py"
        )
        in validation
        and (
            "Phase 6 transition DXF qualified FreeCAD validation passed"
        )
        in validation
        and "exact zero-member, DXF-only, manifest-only and complete-pair states"
        in validation_flat
        and "inert historical controls" in validation_flat
        and "interruption after each addition" in validation_flat
        and "next-invocation monotonic completion" in validation_flat
        and "required directory synchronisation before complete-pair reuse"
        in validation_flat
        and "fail-closed preservation when that synchronisation fails"
        in validation_flat
        and "resolve-to-bind removal and substitution" in validation_flat
        and "post-lock substitution" in validation_flat
        and "initial-member and post-addition substitution" in validation_flat
        and "unsupported primitives" in validation_flat
        and "non-regular-final and byte-collision refusal" in validation_flat
        and "active-lock fail-closed diagnostics" in validation_flat
        and "observed descriptor-close abandonment" in validation_flat
        and "surviving-host `BaseException` propagation with chained "
        "truthful retained-state diagnostics" in validation_flat
        and "preservation of the original interruption when an anonymous "
        "close itself fails" in validation_flat
        and "best-effort remaining anonymous closes and non-replacing "
        "bound-directory close diagnostics" in validation_flat
        and "non-recoverable post-link/pre-sync durability uncertainty"
        in validation_flat
        and "truthful retained-state diagnostics" in validation_flat
        and (
            "It proves the bounded D-P6-003 strict add-only, journal-free "
            "implementation"
        )
        in validation_flat
        and "no published final is removed, rewritten or replaced by "
        "TrackTemplate"
        in validation_flat
        and "exact partial preservation and next-invocation completion"
        in validation_flat
        and "surviving-host interruption cleanup" in validation_flat
        and (
            "they supply no GUI, production-output, Phase 6 exit or release "
            "acceptance"
        )
        in validation_flat,
        "the transition DXF command, sentinel or recovery-evidence boundary "
        "is missing",
    )


def _validate_plan_programme(plan: str) -> None:
    """Bind programme and horizon claims to the dashboard preamble."""
    preamble = direct_section_content(plan, "Project Plan", level=1)
    diagnostic = (
        "project plan lost its local current-programme and future-horizon "
        "clause"
    )
    programme_paragraph = next(
        (
            paragraph
            for paragraph in _raw_paragraphs(preamble)
            if "The active program is" in _semantic_text(paragraph)
        ),
        "",
    )
    programme = _semantic_text(programme_paragraph)
    for fragment in (
        "active program is the TrackTemplate Core macro-to-Addon migration",
        "migration has defined completion conditions",
        "Addon must be the usual route",
        "modular package must be the sole runtime",
        "without a legacy-macro dependency",
        "owner must accept the Core parity and output that the project claims",
        "Each distribution build must give the same result",
        "Release qualification must pass",
    ):
        _require(
            fragment in programme,
            diagnostic + ": " + fragment,
        )
    layout_paragraph = next(
        (
            _semantic_text(paragraph)
            for paragraph in _raw_paragraphs(preamble)
            if "The Layout Editor is" in _semantic_text(paragraph)
        ),
        "",
    )
    for fragment in (
        "Layout Editor is the later program",
        "does not change Phase 6 exits",
        "record future architecture without current implementation",
    ):
        _require(
            fragment in layout_paragraph,
            diagnostic + ": " + fragment,
        )
    _require_links(
        programme_paragraph,
        (("PRODUCT_VISION.md", "PRODUCT_VISION.md"),),
        "project plan Product Vision authority link or destination drifted",
    )


def _validate_owner_view(plan: str) -> None:
    """Require one derived, status-consistent TT-DOC-001 owner view."""
    section = _section(plan, "Current owner view")
    rows: list[list[str]] = []
    for line in section.splitlines():
        cells = _cells(line) if line.startswith("|") else []
        if len(cells) == 2 and cells[0] not in {"Field", "---"}:
            rows.append(cells)
    expected_fields = [
        "**Current state**",
        "**What changed**",
        "**What now works**",
        "**Limitations/findings**",
        "**Owner decision**",
        "**Next action**",
    ]
    _require(
        [row[0] for row in rows] == expected_fields,
        "project-plan owner view fields drifted",
    )
    owner_view = " ".join(section.split())
    for fragment in (
        "Phase 6 is 2/5 evidenced",
        "The owner accepted Exits 2 and 3",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays `unknown`",
        "ASD-STE100 Issue 9 the normative standard for canonical technical "
        "prose in English",
        "No phase, exit, risk, or product state changes",
        "The workflows apply the profile through canonical links",
        "ASD-STE100 Issue 9 conformance not verified` applies to the live corpus",
        "Frozen history does not change",
        "TT-DOC-001 is Accepted",
        "All other owner decisions and exclusions stay unchanged",
        "authorizes no later project work",
    ):
        _require(
            fragment in owner_view,
            "project-plan owner view lost or contradicted: " + fragment,
        )
    plan_preamble = direct_section_content(plan, "Project Plan", level=1)
    _require(
        "canonical status, evidence, and registers are the source of the owner "
        "view. The owner view does not establish authority"
        in _semantic_text(plan_preamble),
        "project-plan owner view became an authority source",
    )


def _validate_plan_shape(plan: str) -> dict[int, dict[str, object]]:
    headings = re.findall(r"^#{1,2} .+$", plan, re.MULTILINE)
    _require(
        headings
        == [
            "# Project Plan",
            "## Current owner view",
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
    _validate_plan_programme(plan)
    _validate_owner_view(plan)
    _require(
        "CAPABILITY_MATRIX.md" in plan,
        "project plan does not route to the capability evidence map",
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
        rows[6]["evidenced"] == 2
        and str(rows[6]["state"])
        == "Current — opened 2026-08-01",
        "Phase 6 must remain current at the accepted 2/5 state",
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
        "Phase 6 current — 2/5 evidenced" in " ".join(plan.split())
        and "owner accepted Exit 2 under D-P6-002 on 2026-08-02"
        in " ".join(plan.split())
        and "Exit 3 under D-P6-005 on 2026-08-15"
        in " ".join(plan.split()),
        "the accepted Phase 6 2/5 status is missing",
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

    expected_plan = [
        "Pending",
        "Evidenced — owner-accepted 2026-08-02",
        "Evidenced — owner-accepted 2026-08-15",
        "Pending",
        "Pending",
    ]
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
    _require(
        "D-P6-002 accepts only the bounded transient-object Exit 2"
        in plan_flat
        and "advances Phase 6 to 1/5" in plan_flat
        and "D-P6-003 selects strict add-only, journal-free monotonic "
        "completion" in plan_flat
        and "authorises its later bounded Level 2 implementation" in plan_flat
        and "D-P6-004 defines the finite supported exporter fault model" in plan_flat
        and "D-P6-005 accepts only the bounded private-development B16 "
        "Entry/Exit deterministic, failure-safe DXF-and-manifest route"
        in plan_flat
        and "advances Phase 6 to 2/5" in plan_flat
        and "project status remains `unknown`" in plan_flat,
        "Phase 6 Exit 2/3 acceptance or Exit 3 contract boundary is missing",
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
        "Current — 2/5 evidenced. Exit 2 was owner-accepted under D-P6-002 on "
        "2026-08-02 and Exit 3 under D-P6-005 on 2026-08-15; exits 1, 4 and 5 "
        "remain Pending" in current_flat,
        "current record does not preserve the accepted Phase 6 2/5 state",
    )
    performance_section = _section(
        current_evidence,
        "B16 Entry/Exit edit-through-export performance",
    )
    performance_flat = " ".join(performance_section.split())
    _require(
        "This bounded Level 2 performance-evidence tranche" in performance_flat
        and "The complete cold journey was" in performance_flat
        and "does not establish an improvement beyond normal noise"
        in performance_flat
        and EXPECTED_PHASE6_PERFORMANCE_DISPOSITION in performance_flat
        and (
            "../benchmarks/"
            "2026-08-02-phase6-transition-pipeline-performance.md"
        )
        in performance_section,
        "Phase 6 performance evidence boundary drifted",
    )
    _require(
        "Phase 5 closeout" in current_evidence
        and "history/phase-closeouts/PHASE5_CLOSEOUT.md" in current_evidence,
        "current Phase 6 record does not link its frozen predecessor",
    )
    recovery_section = _section(
        current_evidence,
        "B16 Entry/Exit durable DXF recovery",
    )
    recovery_flat = " ".join(recovery_section.split())
    _require(
        "7acdab4f925592d49394960c76f7552e1b47be9d" in recovery_section
        and "versioned internal journal" in recovery_flat
        and "immediately after the first and second final links"
        in recovery_flat
        and "automatic recovery claim is withdrawn" in recovery_flat
        and (
            "Phase 6 transition DXF qualified FreeCAD validation passed"
        )
        in recovery_section
        and "Phase 6 therefore remains 1/5 with Exit 3 Pending"
        in recovery_flat,
        "Phase 6 durable DXF recovery evidence boundary drifted",
    )
    recovery_rows = _structured_table_rows(
        recovery_section,
        (
            "Exit 3 required-before-exit condition",
            "Present evidence after this tranche",
        ),
        "Exit 3 recovery evidence status",
    )
    _require(
        recovery_rows == EXPECTED_EXIT3_RECOVERY_ROWS,
        "Exit 3 recovery evidence status drifted or implied acceptance",
    )
    staging_repair_section = _section(
        current_evidence,
        "B16 Entry/Exit staging-ownership repair",
    )
    staging_repair_flat = " ".join(staging_repair_section.split())
    _require(
        "284695784004320d541cd3fc5def4369e43c7f5c"
        in staging_repair_section
        and "25360f23fc8393517d8c3ab7145cf7812193dc94"
        in staging_repair_section
        and "recommended **Do not proceed** for Exit 3"
        in staging_repair_flat
        and "remaining `mkdir`-to-first-open ownership interval"
        in staging_repair_flat
        and "Content equivalence" in staging_repair_flat
        and "O_TMPFILE" in staging_repair_section
        and "linkat(AT_EMPTY_PATH)" in staging_repair_section
        and "internal v2 interruption journal" in staging_repair_flat
        and "journal is also created anonymously and linked from its "
        "still-open descriptor" in staging_repair_flat
        and "`.new` remains only a reserved ambiguity detector"
        in staging_repair_flat
        and "no staging pathname or directory removal"
        in staging_repair_flat
        and "identities, metadata and bytes" in staging_repair_flat
        and "destination_changed=True" in staging_repair_section
        and "cleanup_complete=False" in staging_repair_section
        and "recoverable=False" in staging_repair_section
        and "No final output survives" in staging_repair_flat
        and "file appears in the process working directory"
        in staging_repair_flat
        and "both anonymous files have zero links before commit"
        in staging_repair_flat
        and "valid v2 journal" in staging_repair_flat
        and "changed its access time" in staging_repair_flat
        and "descriptor-relative non-reading metadata inspection"
        in staging_repair_flat
        and "preserved unchanged and rejected as unclaimable"
        in staging_repair_flat
        and "matching partial DXF" in staging_repair_flat
        and "lone v1 journal and `.new` control" in staging_repair_flat
        and "including access time" in staging_repair_flat
        and "do not claim automatic recovery" in staging_repair_flat
        and "All pre-existing transaction-control residue remains preserved"
        in staging_repair_flat
        and "remain open Exit 3 technical gaps" in staging_repair_flat
        and (
            "Phase 6 remains 1/5 with Exit 2 alone Evidenced and "
            "owner-accepted; Exit 3 remains Pending"
        )
        in staging_repair_flat,
        "Phase 6 staging-ownership repair evidence drifted",
    )
    recovery_contract_heading = (
        "Phase 6 Exit 3 recovery-authority contract panel and owner decision"
    )
    _require(
        '<a id="phase-6-exit-3-recovery-authority-contract-panel"></a>\n\n'
        "## "
        + recovery_contract_heading
        in current_evidence,
        "D-P6-003 panel anchor or heading association is missing",
    )
    recovery_contract_section = direct_section_content(
        current_evidence,
        recovery_contract_heading,
    )
    recovery_contract_flat = " ".join(recovery_contract_section.split())
    for required_contract_clause in (
        "strict add-only, journal-free monotonic completion",
        "unpublished payloads in anonymous, creation-bound descriptors",
        "Before publication, abandonment consists only of closing owned "
        "anonymous descriptors",
        "Publication may only add an absent deterministic final pathname",
        "No published final file may be unlinked, renamed, rewritten, "
        "truncated, replaced",
        "Pathname-based rollback ends permanently at the first successful "
        "final link",
        "After any post-publication failure, every published final is "
        "preserved",
        "A later invocation may add only an absent exact counterpart",
        "inspection grants no deletion or replacement authority",
        "Success is reported only after the complete final pair and required "
        "durability state are independently revalidated as exact",
        "Substitution, ambiguity, collision, replay, inconsistency",
        "A race discovered after an addition leaves every published file "
        "untouched",
        "`cleanup_complete`, `recoverable`, `destination_changed`",
        "`recoverable=True` requires an independently revalidated exact "
        "zero-member, partial or complete destination",
        "A surviving published final on a failed invocation requires "
        "`cleanup_complete=False`",
        "Identical complete-pair reuse, deterministic bytes and filenames",
        "host or filesystem without every required anonymous-file",
        "authenticating or verifying a pathname does not create authority to "
        "delete it",
        "POSIX pathname deletion has no expected-inode atomic condition",
        "cross-process recovery means safe monotonic completion, not "
        "destructive cleanup",
        "foreign or uncertain destination state is never removed by "
        "TrackTemplate",
        "inert foreign residue",
        "presence neither permits nor blocks final-set completion",
        "Content equivalence establishes compatibility for reuse or addition "
        "only",
        "an exact regular partial pair may be completed instead of rejected",
        "collision policy is therefore defined per final member",
        "no accepted consumer treats exact-partial collision failure as a "
        "required outcome",
        "No material owner choice remains",
        "automatic recovery is not present",
        "prove pre-publication descriptor abandonment, interruption after "
        "each addition, post-addition races and next-invocation monotonic "
        "completion",
        "Phase 6 remains 1/5",
        "Exit 3 remains Pending",
        "no risk state, treatment or effectiveness changes",
        "tracktemplate/adapters/export/transition_dxf.py",
        "tracktemplate/application/transition_export.py",
        "must stop without publication",
        "freeze both export contract/result IDs",
        "identical output fingerprints and `created` result signatures",
        "generic storage framework or runtime dependency",
    ):
        _require(
            required_contract_clause in recovery_contract_flat,
            "D-P6-003 recovery-authority contract or status boundary drifted",
        )
    _require_paragraph(
        recovery_contract_section,
        (
            "Panel recommendation: Proceed with bounded conditions. The "
            "fresh filesystem-security and architecture/API reviewers accept "
            "the strict add-only contract and later Level 2 boundary; the "
            "governance and staff-level quality review finds no status, "
            "evidence or authority contradiction. No material owner choice or "
            "dissent remains."
        ),
        "D-P6-003 panel recommendation drifted",
    )
    recovery_contract_quoted = _blockquote_paragraphs(
        recovery_contract_section
    )
    _require(
        recovery_contract_quoted
        == [
            _semantic_text(
                "D-P6-003 — Select strict add-only, journal-free monotonic "
                "completion for Exit 3 recovery"
            ),
            _semantic_text(EXPECTED_EXIT3_RECOVERY_AUTHORITY),
            _semantic_text(EXPECTED_EXIT3_RECOVERY_EXCLUSIONS),
        ],
        "D-P6-003 exact owner decision drifted or was relocated",
    )
    implementation_heading = (
        "B16 Entry/Exit add-only DXF monotonic recovery"
    )
    implementation_section = direct_section_content(
        current_evidence,
        implementation_heading,
    )
    implementation_flat = _semantic_text(implementation_section)
    for required_implementation_clause in (
        "ccacb5ca638b1e3a79fb59107a97d90e9434f0d5",
        "exact regular partial pair raised "
        "transition-dxf-export-collision",
        "stages only absent payloads in anonymous creation-bound descriptors",
        "Historical journals, .new files and stage directories are inert",
        "no post-publication rollback, journal cleanup or final-path unlink "
        "route",
        "Phase 6 transition DXF export validation passed",
        "same created result signature as fresh creation",
        "next-invocation completion only after required directory "
        "synchronisation",
        "fail-closed complete-pair preservation when that synchronisation "
        "fails",
        "resolve-to-bind removal and substitution",
        "post-lock, initial-member and post-addition substitution",
        "active-lock ambiguity",
        "non-regular and byte-collision refusal",
        "observed descriptor closure on pre-publication abandonment",
        "sentinel proving no unlink, rename, replace or rmdir call",
        "6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd861",
        "16de67625d952e9bb0c7c3f7891b30987f78d7c5878a9838999ab0909f131552",
        "7b2757bc3559013a2399df7efe6c25721288f8dad56b6cc05d93c2938c86c2b1",
        "8cff21c710de1da266d0a0c590cd90dc4edf46c37403275c146e2ffe5a9b3e9f",
        "Phase 6 transition DXF qualified FreeCAD validation passed",
        "Conditions 1 and 3 now have bounded evidence",
        "Condition 6 remains open",
        "not an Exit 3 evidence-admission or owner-acceptance decision",
        "Phase 6 remains 1/5 with only Exit 2 Evidenced and owner-accepted",
        "Exit 3 remains Pending",
        "PR-09, PR-13, PR-16, PR-22 and QA-R03 retain their existing states",
    ):
        _require(
            required_implementation_clause in implementation_flat,
            "Phase 6 add-only recovery implementation evidence drifted: "
            + required_implementation_clause,
        )
    interruption_section = direct_section_content(
        current_evidence,
        "B16 Entry/Exit surviving-host interruption cleanup",
    )
    interruption_flat = _semantic_text(interruption_section)
    for required_interruption_clause in (
        "49d9a85ee3f942a801c65f1cd051a2586ffa10d8",
        "anonymous staging descriptor remained open",
        "implementation-defect under D-P6-003 invariant 2",
        "first independent security review then blocked retention",
        "TransitionDxfExportError instead of the original "
        "CleanupInterruption",
        "second independent security review confirmed those paths but "
        "blocked retention",
        "retained regression reproduced [True, True] against that second "
        "reviewed state",
        "preserves the original KeyboardInterrupt, SystemExit or custom "
        "direct BaseException type and value",
        "Each descriptor enters the outer ownership map immediately after "
        "open",
        "Cleanup attempts every observed invocation-owned anonymous "
        "descriptor",
        "completion and bound-directory cleanup routers also preserve an "
        "active direct interruption",
        "failed or uncertain close is reported cleanup-incomplete and "
        "non-recoverable through the existing chained "
        "TransitionDxfExportError",
        "marked durability-uncertain before linkat until the directory "
        "fsync returns",
        "unchanged/clean/recoverable",
        "changed/not-clean/recoverable",
        "No exception class, public ID, receipt, filename, output byte, "
        "schema or collision policy changes",
        "Phase 6 transition DXF export validation passed",
        "Phase 6 transition DXF qualified FreeCAD validation passed",
        "Process-kill, os._exit and a second asynchronous interruption",
        "Exit 3 remains Pending for a fresh Level 3 panel",
        "Phase 6 remains 1/5",
        "no risk or output authority changes",
    ):
        _require(
            required_interruption_clause in interruption_flat,
            "Phase 6 interruption cleanup evidence drifted: "
            + required_interruption_clause,
        )
    _validate_transition_export_validation(_read(VALIDATION_PATH))
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
        and [row[1] for row in current_rows] == EXPECTED_PHASE6_DISPOSITIONS,
        "Phase 6 exits do not match the accepted 2/5 dispositions",
    )
    exit3_acceptance_heading = (
        "Phase 6 Exit 3 supported-model evidence-admission panel and owner "
        "decision"
    )
    _require(
        '<a id="phase-6-exit-3-supported-model-evidence-admission-panel">'
        "</a>\n\n## "
        + exit3_acceptance_heading
        in current_evidence,
        "D-P6-005 panel anchor or heading association is missing",
    )
    exit3_acceptance_section = direct_section_content(
        current_evidence,
        exit3_acceptance_heading,
    )
    exit3_acceptance_flat = _semantic_text(exit3_acceptance_section)
    for required_acceptance_clause in (
        "7198b05b6a4b7e4654b7d02d0bad4e5cf627a799",
        "PROCEED TO OWNER ACCEPTANCE WITH BOUNDED CONDITIONS",
        "There was no dissent",
        "No supported-model defect, unsafe recovery path, material evidence "
        "gap or contradiction with D-P6-003/D-P6-004 was found",
        "No risk state, treatment, effectiveness or disposition changes",
        "no product source, test oracle, schema, manifest, output byte, "
        "identifier or railway behaviour changes",
        "fresh independent acceptance review",
        "exact-head protected CI",
        "preservation-audited protected-main integration",
    ):
        _require(
            required_acceptance_clause in exit3_acceptance_flat,
            "D-P6-005 evidence-admission panel drifted: "
            + required_acceptance_clause,
        )
    exit3_acceptance_quoted = _blockquote_paragraphs(
        exit3_acceptance_section
    )
    _require(
        exit3_acceptance_quoted
        == [
            _semantic_text(
                "D-P6-005 — Accept Phase 6 Exit 3 for the bounded B16 "
                "Entry/Exit exporter"
            ),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_SCOPE),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_COVERAGE),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_LIMITATIONS),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_EXCLUSIONS),
        ],
        "D-P6-005 panel exact owner decision drifted or was relocated",
    )
    tt_doc_heading = (
        "TT-DOC-001 documentation-architecture panel and owner decision"
    )
    _require(
        '<a id="tt-doc-001-documentation-architecture-panel"></a>\n\n## '
        + tt_doc_heading
        in current_evidence,
        "TT-DOC-001 panel anchor or heading association is missing",
    )
    tt_doc_section = direct_section_content(current_evidence, tt_doc_heading)
    tt_doc_flat = _semantic_text(
        re.sub(r"^> ?", "", tt_doc_section, flags=re.MULTILINE)
    )
    for required_clause in (
        "f03818d71bce06c5cfb85da84d8f3f230e08b47c",
        "Phase 6 stays at 2/5",
        "No risk disposition or product authority changes",
        "reference/ENGINEERING_POLICY.md owns the documentation lifecycle and "
        "completion reports",
        "The panel examined all 28 skills",
        "No new skill or competing primary responsibility is necessary",
        "ASD-STE100 Simplified Technical English, Issue 9",
        "2025-01-15",
        "reference/TERMINOLOGY.md is the one project terminology owner",
        "official Issue 9 standard",
        "Some descriptive sentences have more than 25 words",
        "Full Issue 9 conformance of the live corpus is not verified",
        "Issue 9 conformance assessment for this candidate",
        "The review examined each full logical unit in this table",
        "The internal result for these logical units is ASD-STE100 Issue 9 "
        "conforming",
        "This result is a TrackTemplate conformance assessment",
        "It is not external ASD certification, endorsement, or an official "
        "conformance assessment",
        "It excludes exact machine data and externally controlled information",
        "It excludes unchanged live prose outside the named logical units",
        "It also excludes frozen history",
        "Two reviewers independently reviewed the exact candidate",
        "The architecture and Issue 9 review result was PASS WITH FINDINGS",
        "The quality review result was PASS WITH FINDINGS",
        "No reviewer found a blocker",
        "Issue 9 conformance is Unknown for unchanged live prose",
        "The reviewers did not change the candidate",
        "The same reviewers also examined previous candidate states",
        "Proceed with bounded conditions",
        "TT-DOC-001 — TrackTemplate Technical Documentation Profile",
        "owner view → canonical information → proof/provenance",
        "The owner view gives no project authority",
        "normative standard for canonical technical prose in English in the "
        "defined scope",
        "All new prose in this scope must obey the applicable ASD-STE100 "
        "Issue 9 requirements",
        "A reviewer must use the official standard for the linguistic review",
        "claims no S1000D conformance",
        "claims no external ASD certification, endorsement, or official "
        "conformance assessment",
        "changes no phase or exit status",
        "changes no risk disposition, product source, or product behavior",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays unknown",
    ):
        _require(
            required_clause in tt_doc_flat,
            "TT-DOC-001 evidence panel drifted: " + required_clause,
        )
    expected_conformance_scope = {
        "AGENTS.md": ("completion-report requirement",),
        "reference/ENGINEERING_POLICY.md": (
            "TT-DOC-001 profile",
            "first paragraph",
            "completion-report section",
        ),
        "reference/PROJECT_PLAN.md": (
            "preamble",
            "current owner view",
            "TT-DOC-001 decision row",
            "authority links",
        ),
        "reference/CAPABILITY_MATRIX.md": (
            "first evidence boundary",
            "DXF row",
        ),
        "reference/TERMINOLOGY.md": (
            "ASD-STE100 project terminology section",
        ),
        "reference/current/PHASE_EVIDENCE.md": (
            "TT-DOC-001 panel",
            "current-register paragraph",
        ),
        "reference/current/gate-decisions.json": (
            "human-readable TT-DOC-001 record",
            "Exact JSON data stays outside",
        ),
        "reference/LEARNING_FROM_EXPERIENCE.md": ("LFE-018 only",),
        "reference/AGENT_WORKFLOWS.md": (
            "TT-DOC-001 workflow-integration section",
        ),
        ".agents/skills/tracktemplate-change-validation/SKILL.md": (
            "profile preparation",
            "Issue 9 validation rules",
            "full output section",
        ),
        ".agents/skills/tracktemplate-context-recovery/SKILL.md": (
            "owner-view guidance",
            "recovery-report introduction",
        ),
        ".agents/skills/tracktemplate-continue/SKILL.md": (
            "full Owner acceptance pack section",
        ),
        ".agents/skills/tracktemplate-documentation-alignment/SKILL.md": (
            "profile preparation",
            "full report section",
        ),
        ".agents/skills/tracktemplate-documentation-review/SKILL.md": (
            "full preparation",
            "editing-rules",
            "output sections",
        ),
        (
            ".agents/skills/tracktemplate-documentation-review/references/"
            "document-ownership.md"
        ): ("two changed ownership rows",),
        (
            ".agents/skills/tracktemplate-documentation-review/references/"
            "writing-checklist.md"
        ): (
            "introduction",
            "full Ownership, Accuracy, and Concision sections",
        ),
        ".agents/skills/tracktemplate-quality-review/SKILL.md": (
            "full preparation and output sections",
        ),
        ".agents/skills/tracktemplate-technical-lead/SKILL.md": (
            "profile guidance in preparation and final handoff",
        ),
    }
    conformance_rows = _structured_table_rows(
        tt_doc_section,
        ("Path", "Full logical unit"),
        "TT-DOC-001 Issue 9 conformance scope",
    )
    _require(
        set(conformance_rows) == set(expected_conformance_scope),
        "TT-DOC-001 conformance-scope path set drifted",
    )
    for reviewed_path, scope_fragments in expected_conformance_scope.items():
        scope = conformance_rows[reviewed_path][1]
        _require(
            all(fragment in scope for fragment in scope_fragments),
            "TT-DOC-001 conformance scope changed: " + reviewed_path,
        )
    _require(
        "[official Issue 9 standard](https://www.asd-ste100.org/assets/files/"
        "ASD-STE100_ISSUE9.pdf)" in tt_doc_section,
        "TT-DOC-001 conformance review lost its official Issue 9 source",
    )
    _require(
        'id="phase-6-opening-panel"' in current_evidence
        and "Proceed with bounded conditions" in current_evidence
        and "I accept D-P6-001 exactly as presented" in current_evidence
        and EXPECTED_PHASE6_AUTHORITY in decision_quote_flat
        and EXPECTED_PHASE6_EXCLUSIONS in decision_quote_flat,
        "Phase 6 opening panel or exact owner acceptance is missing",
    )
    exit2_panel_heading = (
        "Phase 6 Exits 2 and 3 evidence-admission panel and owner decision"
    )
    _require(
        '<a id="phase-6-exits-2-and-3-evidence-admission-panel"></a>\n\n'
        "## "
        + exit2_panel_heading
        in current_evidence,
        "D-P6-002 panel anchor or heading association is missing",
    )
    exit2_panel_section = direct_section_content(
        current_evidence,
        exit2_panel_heading,
    )
    _require_paragraph(
        exit2_panel_section,
        (
            "Panel recommendation: Exit 2 was Proceed with bounded conditions "
            "and sufficient to recommend Evidenced. Exit 3 was Do not proceed "
            "and must remain Pending. There was no dissent between the "
            "independent reviewers."
        ),
        "D-P6-002 panel recommendation drifted",
    )
    exit2_quoted = _blockquote_paragraphs(exit2_panel_section)
    _require(
        exit2_quoted
        == [
            _semantic_text(
                "D-P6-002 — Accept Phase 6 Exit 2 and retain Exit 3 Pending"
            ),
            _semantic_text(EXPECTED_EXIT2_AUTHORITY),
            _semantic_text(EXPECTED_EXIT2_EXCLUSIONS),
        ],
        "D-P6-002 panel exact owner decision drifted or was relocated",
    )
    condition_rows = _structured_table_rows(
        exit2_panel_section,
        ("Accountable owner", "Deadline", "Condition"),
        "Exit 3 required-before-exit conditions",
    )
    _require(
        condition_rows == EXPECTED_EXIT3_CONDITION_ROWS,
        "Exit 3 required-before-exit conditions drifted",
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
    phase5_records = phase5_document["risks"]
    _require(isinstance(phase5_records, list), "Phase 5 risks must be a list")

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
    phase5_by_id = {
        str(record["id"]): record
        for record in phase5_records
        if isinstance(record, dict) and "id" in record
    }
    _require(
        set(phase5_by_id) == set(by_id),
        "current risks do not preserve the frozen Phase 5 risk set",
    )
    governance_risks = {"PR-12", "PR-20", "PR-22"}
    immutable_risk_fields = expected_fields - {
        "summary",
        "owner",
        "required_work",
        "closure_evidence",
    }
    for risk_id, record in by_id.items():
        frozen = phase5_by_id[risk_id]
        if risk_id not in governance_risks:
            _require(
                record == frozen,
                "non-governance risk changed from Phase 5: " + risk_id,
            )
            continue
        for field in immutable_risk_fields:
            _require(
                record[field] == frozen[field],
                "governance-only risk changed protected field: "
                + risk_id
                + "/"
                + field,
            )
    _require(
        "Product Vision owner" in str(by_id["PR-12"]["required_work"])
        and "unchanged execution loops"
        in str(by_id["PR-12"]["required_work"]),
        "PR-12 lacks product-direction or loop-prevention control",
    )
    _require(
        "canonical-versus-derived authority"
        in str(by_id["PR-20"]["required_work"])
        and "Layout Editor" in str(by_id["PR-20"]["required_work"]),
        "PR-20 lacks horizon and canonical-authority scope controls",
    )
    _require(
        "Level 3" in str(by_id["PR-22"]["required_work"])
        and "independently accepted" in str(by_id["PR-22"]["required_work"])
        and "sole acceptance authority"
        in str(by_id["PR-22"]["required_work"]),
        "PR-22 does not enforce independent Level 3 acceptance",
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
        and current_document["updated_on"] == "2026-08-15",
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
        and len(phase6_records) == len(EXPECTED_PHASE6_DECISION_IDS)
        and all(isinstance(record, dict) for record in phase6_records),
        "current decision register has an unexpected record count or shape",
    )
    phase6_by_id: dict[str, dict[str, object]] = {}
    for record in phase6_records:
        _require(set(record) == expected_fields, "current decision fields changed")
        decision_id = record["id"]
        _require(
            isinstance(decision_id, str) and decision_id not in phase6_by_id,
            "duplicate current decision ID",
        )
        _require(
            record["decided_on"]
            == (
                "2026-08-15"
                if decision_id in {"D-P6-004", "D-P6-005", "TT-DOC-001"}
                else (
                    "2026-08-02"
                    if decision_id in {"D-P6-002", "D-P6-003"}
                    else "2026-08-01"
                )
            )
            and record["status"] == "Accepted"
            and record["panel_required_under_current_policy"] is True,
            "current Level 3 decision status or panel requirement drifted",
        )
        panel_record = str(record["panel_record"])
        panel_path_text, separator, panel_anchor = panel_record.partition("#")
        panel_path = ROOT / panel_path_text
        _require(panel_path.is_file(), "current panel record path is missing")
        _require(
            separator and 'id="{}"'.format(panel_anchor) in _read(panel_path),
            "current panel record anchor is missing",
        )
        _require(
            record["evidence"] == panel_record,
            "current decision evidence does not match its panel",
        )
        phase6_by_id[decision_id] = record
    _require(
        set(phase6_by_id) == EXPECTED_PHASE6_DECISION_IDS,
        "current decision IDs drifted",
    )

    phase6_record = phase6_by_id["D-P6-001"]
    _require(
        phase6_record["decision"] == "Open Phase 6."
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

    vision_record = phase6_by_id["D-GOV-005"]
    vision_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#product-vision-and-execution-governance-panel"
    )
    _require(
        vision_record["decision"] == EXPECTED_VISION_DECISION
        and vision_record["authority"] == EXPECTED_VISION_AUTHORITY
        and vision_record["exclusions"] == EXPECTED_VISION_EXCLUSIONS
        and vision_record["evidence"] == vision_panel
        and vision_record["panel_record"] == vision_panel,
        "D-GOV-005 authority, exclusions or panel routing drifted",
    )
    exit2_record = phase6_by_id["D-P6-002"]
    exit2_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#phase-6-exits-2-and-3-evidence-admission-panel"
    )
    _require(
        exit2_record["decision"] == EXPECTED_EXIT2_DECISION
        and exit2_record["authority"] == EXPECTED_EXIT2_AUTHORITY
        and exit2_record["exclusions"] == EXPECTED_EXIT2_EXCLUSIONS
        and exit2_record["evidence"] == exit2_panel
        and exit2_record["panel_record"] == exit2_panel,
        "D-P6-002 authority, exclusions or panel routing drifted",
    )
    recovery_contract_record = phase6_by_id["D-P6-003"]
    recovery_contract_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#phase-6-exit-3-recovery-authority-contract-panel"
    )
    _require(
        recovery_contract_record["decision"]
        == EXPECTED_EXIT3_RECOVERY_DECISION
        and recovery_contract_record["authority"]
        == EXPECTED_EXIT3_RECOVERY_AUTHORITY
        and recovery_contract_record["exclusions"]
        == EXPECTED_EXIT3_RECOVERY_EXCLUSIONS
        and recovery_contract_record["evidence"] == recovery_contract_panel
        and recovery_contract_record["panel_record"]
        == recovery_contract_panel,
        "D-P6-003 authority, exclusions or panel routing drifted",
    )
    exit3_acceptance_record = phase6_by_id["D-P6-005"]
    exit3_acceptance_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#phase-6-exit-3-supported-model-evidence-admission-panel"
    )
    _require(
        exit3_acceptance_record["decision"]
        == EXPECTED_EXIT3_ACCEPTANCE_DECISION
        and exit3_acceptance_record["authority"]
        == EXPECTED_EXIT3_ACCEPTANCE_AUTHORITY
        and exit3_acceptance_record["exclusions"]
        == EXPECTED_EXIT3_ACCEPTANCE_STRUCTURED_EXCLUSIONS
        and exit3_acceptance_record["evidence"]
        == exit3_acceptance_panel
        and exit3_acceptance_record["panel_record"]
        == exit3_acceptance_panel,
        "D-P6-005 authority, exclusions or panel routing drifted",
    )
    tt_doc_record = phase6_by_id["TT-DOC-001"]
    tt_doc_panel = (
        "reference/current/PHASE_EVIDENCE.md"
        "#tt-doc-001-documentation-architecture-panel"
    )
    _require(
        tt_doc_record["decision"] == EXPECTED_TT_DOC_DECISION
        and tt_doc_record["evidence"] == tt_doc_panel
        and tt_doc_record["panel_record"] == tt_doc_panel,
        "TT-DOC-001 decision or panel routing drifted",
    )
    tt_doc_semantic = _semantic_text(
        str(tt_doc_record["authority"])
        + " "
        + str(tt_doc_record["exclusions"])
    )
    for fragment in (
        "f03818d71bce06c5cfb85da84d8f3f230e08b47c",
        "human comprehensibility as a governance control",
        "reference/ENGINEERING_POLICY.md is the sole canonical owner",
        "owner view → canonical information → proof/provenance",
        "owner view gives no project authority",
        "ASD-STE100 Simplified Technical English, Issue 9",
        "2025-01-15",
        "official standard is the normative external reference",
        "All new prose in this scope must obey the applicable Issue 9 "
        "requirements",
        "full logical unit that contains the change must obey these "
        "requirements",
        "reviewer must use the official standard for the linguistic review",
        "reference/TERMINOLOGY.md is the one owner",
        "This decision adds no skill",
        "Issue 9 style does not authorize a change to frozen history",
        "ASD-STE100 Issue 9 conformance not verified applies to the live "
        "corpus",
        "claims no external ASD certification, endorsement, or official "
        "conformance assessment",
        "claims no S1000D conformance",
        "changes no phase or exit status, accepted-exit count, risk "
        "disposition",
        "authorizes no S1000D XML, Common Source Database, BREX",
        "Phase 6 stays at 2/5",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays unknown",
    ):
        _require(
            fragment in tt_doc_semantic,
            "TT-DOC-001 authority or exclusion drifted: " + fragment,
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
        and "owns Phase 6 and current cross-phase governance decisions"
        in decision_flat,
        "the current decision-register ownership is missing",
    )
    plan_ids = set(
        re.findall(
            r"^\| (D-[A-Z0-9-]+|TT-DOC-\d{3}) \|",
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


def _validate_product_vision(vision: str) -> None:
    """Validate Product Vision meaning in the sections that own each clause."""
    required_vision_headings = {
        "Product definition",
        "Vision and execution authority",
        "Canonical and derived authority",
        "Normal design experience",
        "On-demand exact geometry and production",
        "Product horizons",
        "Migration completion",
        "Present-programme non-goals",
        "Product acceptance journey",
    }
    vision_headings = set(re.findall(r"^## (.+)$", vision, re.MULTILINE))
    _require(
        required_vision_headings <= vision_headings,
        "Product Vision lacks required governing sections",
    )

    preamble = _document_preamble(vision, "TrackTemplate Product Vision")
    authority_paragraph = _require_paragraph(
        preamble,
        (
            "This document says what TrackTemplate is and what the current "
            "programme is trying to establish. ARCHITECTURE.md owns the "
            "technical invariants, PROJECT_PLAN.md owns live phase and exit "
            "status, and CAPABILITY_MATRIX.md records bounded repository "
            "evidence. Product vision directs work; it does not independently "
            "authorise a feature, phase exit, migration family, output clearance "
            "or release."
        ),
        "Product Vision lost its local direction-without-authority clause",
    )
    _require_links(
        authority_paragraph,
        (
            ("ARCHITECTURE.md", "ARCHITECTURE.md"),
            ("PROJECT_PLAN.md", "PROJECT_PLAN.md"),
            ("CAPABILITY_MATRIX.md", "CAPABILITY_MATRIX.md"),
        ),
        "Product Vision authority links or destinations drifted",
    )

    definition = direct_section_content(vision, "Product definition")
    _require_paragraph(
        definition,
        (
            "Templot is the closest product analogy because both products centre "
            "on parametric model-railway templates rather than generic drawing "
            "primitives. The analogy communicates the intended railway breadth "
            "and template-led way of working. It does not claim file-format "
            "compatibility, identical interaction, shared implementation, "
            "transferred rights or feature parity at the current repository state."
        ),
        "Product Vision lost its bounded Templot analogy",
    )
    _require_paragraph(
        definition,
        (
            "TrackTemplate's distinction is that FreeCAD is the host product "
            "boundary. The normal result is an installable TrackTemplate Workbench "
            "backed by the modular tracktemplate package, FreeCAD documents and "
            "transactions, FreeCAD-native selection and task-panel workflows, and "
            "explicit use of FreeCAD/OpenCASCADE where exact geometry is required. "
            "The accepted legacy macro remains comparison and migration evidence; "
            "it must not be a runtime dependency of the completed Addon."
        ),
        "Product Vision lost its FreeCAD-native migration boundary",
    )

    authority = direct_section_content(
        vision,
        "Vision and execution authority",
    )
    _require(
        _numbered_items(authority)
        == [
            (1, "this canonical product vision;"),
            (2, "accepted architectural invariants;"),
            (3, "the current authorised programme;"),
            (4, "the active phase and its exact exit criteria;"),
            (5, "current risks, findings and repository evidence;"),
            (6, "one selected bounded work item;"),
            (7, "one explicit delegated assignment; and"),
            (8, "independent evidence and acceptance."),
        ],
        "Product Vision authority hierarchy or ordering drifted",
    )
    _require_paragraph(
        authority,
        (
            "Every agent assignment must support a bounded work item that closes "
            "an evidenced finding or advances an active exit criterion, advances "
            "the current authorised programme and thereby helps establish this "
            "vision. A later horizon may inform an extension point, but it cannot "
            "authorise present implementation."
        ),
        "Product Vision lost its assignment trace or future-authority polarity",
    )

    current_programme = direct_section_content(
        vision,
        "Current programme: TrackTemplate Core migration",
        level=3,
    )
    _require_paragraph(
        current_programme,
        (
            "The current programme faithfully converts the accepted legacy macro "
            "into a modular, tested, maintainable, installable and operational "
            "FreeCAD Addon. It preserves accepted behaviour, geometry, workflows, "
            "persistence and production outputs while moving authority into the "
            "modular package."
        ),
        "Product Vision lost its current Core-migration clause",
    )
    future_programme = direct_section_content(
        vision,
        "Subsequent programme: TrackTemplate Layout Editor",
        level=3,
    )
    _require_paragraph(
        future_programme,
        (
            "These capabilities are future until separately authorised. Recording "
            "their direction does not add an implementation task or alter a "
            "current exit."
        ),
        "Product Vision lost its future Layout Editor non-authority clause",
    )
    _require(
        vision.index("### Current programme: TrackTemplate Core migration")
        < vision.index("### Subsequent programme: TrackTemplate Layout Editor")
        < vision.index("## Migration completion"),
        "Product Vision current/future programme ordering drifted",
    )
    migration = direct_section_content(vision, "Migration completion")
    _require_paragraph(
        migration,
        (
            "Completion of one phase or one capability family is not "
            "macro-migration completion. Layout Editor features are not "
            "prerequisites for Core migration."
        ),
        "Product Vision lost its migration-completion boundary",
    )


def _validate_architecture_direction(architecture: str) -> None:
    """Validate each D-GOV-005 clause as one structured architecture record."""
    section = direct_section_content(
        architecture,
        "Accepted Level 3 product-direction decisions",
    )
    _require_paragraph(
        section,
        (
            "D-GOV-005 records the following architectural clauses. They govern "
            "direction; their acceptance does not claim that a shared renderer, "
            "wider exact geometry, another migrated family or a future Layout "
            "Editor capability is implemented."
        ),
        "architecture lost its direction-not-delivery clause",
    )
    expected_rows = {
        "D-GOV-005-A — canonical authority": (
            "Versioned railway intent, identities, topology, analysis decisions, "
            "production intent and accepted definitions are canonical. Coin nodes, "
            "ViewProvider state, transient/generated Part geometry, caches, previews, "
            "exports, reports and manifests are derived and replaceable.",
            "Existing schemas and accepted family boundaries are unchanged.",
        ),
        "D-GOV-005-B — presentation pipeline": (
            "Canonical state feeds railway geometry and analysis, then an immutable "
            "presentation snapshot, then a batched Coin representation.",
            "The accepted B16 Entry/Exit scene remains the only demonstrated slice; "
            "no shared renderer is claimed.",
        ),
        "D-GOV-005-C — normal editing view": (
            "Routine editing is fast Coin-based 2D or pseudo-2D with rails and "
            "sleepers/timbers, construction information and optional chair, analysis "
            "and warning layers, without a Part dependency.",
            "The current centreline fixture does not yet implement the complete "
            "normal view.",
        ),
        "D-GOV-005-D — exact geometry": (
            "Exact geometry is explicit, on demand, derived, safe to delete and "
            "regenerate, and not automatically rebuilt for ordinary selection or "
            "editing.",
            "Accepted transient geometry remains limited to the Phase 6 Entry/Exit "
            "evidence.",
        ),
        "D-GOV-005-E — display modes": (
            "Register only genuinely distinct FreeCAD display modes owned by that "
            "ViewProvider. Detail, construction and analysis choices normally remain "
            "internal layer switches or presets. Invalid restored modes fail closed "
            "or recover through the accepted lifecycle without becoming canonical "
            "state.",
            "No current ViewProvider is replaced and no display-mode migration is "
            "implemented by this decision.",
        ),
        "D-GOV-005-F — presentation performance": (
            "Batch rails, sleeper/timber faces and chair markers; avoid one FreeCAD "
            "object per sleeper/chair and one transform per chair; separate static "
            "geometry from dynamic overlays/labels; do not rebuild the complete scene "
            "graph for selection-only changes.",
            "Numerical budgets and a product-wide renderer remain unaccepted.",
        ),
        "D-GOV-005-G — product horizons": (
            "TrackTemplate Core migration is the current programme; TrackTemplate "
            "Layout Editor is a subsequent programme.",
            "Future extension direction does not alter an active phase or authorise "
            "Layout Editor implementation.",
        ),
    }
    rows = _structured_table_rows(
        section,
        (
            "Clause",
            "Accepted direction",
            "Implementation boundary retained",
        ),
        "architecture D-GOV-005 record",
    )
    _require(
        list(rows) == list(expected_rows),
        "architecture D-GOV-005 clause set or ordering drifted",
    )
    for clause, expected in expected_rows.items():
        expected_cells = [
            _semantic_markdown(cell)
            for cell in (clause, *expected)
        ]
        _require(
            rows.get(clause) == expected_cells,
            "architecture {} semantic record drifted".format(
                clause.split(" — ", 1)[0]
            ),
        )
    recovery_section = direct_section_content(
        architecture,
        "D-P6-003 cross-process recovery authority",
        level=4,
    )
    recovery_semantic = _semantic_text(recovery_section)
    for required_clause in (
        "strict add-only, journal-free monotonic-completion protocol",
        "Recovery authority is constructive, not destructive",
        "unpublished payloads in anonymous, creation-bound descriptors",
        "Before publication, failure is abandoned only by closing those owned "
        "anonymous descriptors",
        "not opened, parsed, modified, deleted or used to permit or block "
        "final-set completion",
        "when exactly one exact regular member exists, preserve it unchanged "
        "and add only its missing exact counterpart",
        "on a mismatch, symbolic link, non-regular member, collision, replay, "
        "substitution, inconsistency or ambiguous observation, fail closed "
        "without further mutation",
        "The first successful final link permanently ends rollback",
        "no published final may thereafter be unlinked, renamed, rewritten, "
        "truncated, replaced",
        "Authenticating or verifying a pathname does not create authority to "
        "delete it",
        "POSIX pathname deletion has no expected-inode atomic condition",
        "A later invocation may add only an absent exact counterpart",
        "success may be reported only after the complete final pair is "
        "independently revalidated as exact",
        "Unsupported host or filesystem primitives fail closed",
        "diagnostics describe the state actually retained",
        "recoverable=True requires an independently revalidated exact "
        "zero-member, partial or complete destination",
        "any surviving published final on a failed invocation sets "
        "cleanup_complete=False",
        "Content equivalence establishes compatibility for reuse or "
        "completion only; it never establishes ownership, deletion or "
        "replacement authority",
        "one collision outcome: a lone exact regular final member may be "
        "completed instead of rejected",
        "That policy applies per final member",
        "Exit 3 remains Pending",
    ):
        _require(
            required_clause in recovery_semantic,
            "architecture D-P6-003 recovery contract drifted",
        )
    export_section = direct_section_content(
        architecture,
        "6. Export adapter",
        level=3,
    )
    _require(
        "Commit the complete output set atomically or, for an explicitly "
        "accepted bounded protocol, complete it monotonically under that "
        "protocol's named invariants" in _semantic_text(export_section)
        and "without claiming authority over foreign or published state"
        in _semantic_text(export_section),
        "architecture export commit contract drifted",
    )


def _validate_capability_matrix(matrix: str) -> None:
    """Validate accepted-source, Addon and future status in local matrix units."""
    preamble = _document_preamble(matrix, "TrackTemplate Capability Matrix")
    preamble_flat = _semantic_text(preamble)
    for fragment, diagnostic in (
        (
            "compares the accepted legacy baseline with the modular B16 checkpoint",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "TT-DOC-001 panel reconciled it on 2026-08-15",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "f03818d71bce06c5cfb85da84d8f3f230e08b47c",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "frozen Phase 1 inventory",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "Phase 5 closeout",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "current Phase 6 evidence",
            "capability matrix lost its local accepted-source and PR-status clause",
        ),
        (
            "D-P6-002 accepts the bounded transient-object exit",
            "capability matrix lost its bounded decision boundary",
        ),
        (
            "D-P6-005 accepts only the bounded private-development exporter "
            "failure-safety claim",
            "capability matrix lost its bounded decision boundary",
        ),
        (
            "Neither decision grants output clearance",
            "capability matrix lost its bounded decision boundary",
        ),
        (
            "Addon column describes the modular tracktemplate implementation",
            "capability matrix lost its local Addon-status authority clause",
        ),
        (
            "not an installable or production-ready Addon claim",
            "capability matrix lost its local Addon-status authority clause",
        ),
        (
            "PROJECT_PLAN.md owns formal phase status",
            "capability matrix lost its local Addon-status authority clause",
        ),
    ):
        _require(
            fragment in preamble_flat,
            diagnostic + ": " + fragment,
        )

    rows = _structured_table_rows(
        direct_section_content(matrix, "Matrix"),
        (
            "Capability",
            "Legacy macro baseline",
            "Current Addon",
            "Canonical state",
            "Coin presentation",
            "Exact geometry",
            "Export",
            "Persistence",
            "Accepted fixture or evidence",
            "Classification",
        ),
        "capability matrix",
    )
    expected_rows = (
        (
            "Straight track",
            "C — bounded straight/station workflow",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[Phase 1 workflow inventory](phase-evidence/"
            "PHASE1_INVENTORY.md#release-critical-workflow-coverage-inventory); "
            "[straight/station series](benchmarks/"
            "2026-07-20-b14-straight-station-workflow-series.md)",
            "Partial",
        ),
        (
            "Curves",
            "C — bounded curve/easement create, edit and output oracles",
            "P — Entry/Exit transition slice only",
            "P — transition-state v1 only",
            "P — transition centreline only",
            "P — transition centreline only",
            "P — private-development DXF only",
            "P — transition records only",
            "[Phase 1 workflow contract](contracts/"
            "phase1-workflow-coverage.json); [Phase 5 closeout](history/"
            "phase-closeouts/PHASE5_CLOSEOUT.md); [Phase 6 evidence](current/"
            "PHASE_EVIDENCE.md)",
            "Partial",
        ),
        (
            "Euler transitions",
            "C — accepted B14/B15 calculation and workflow evidence",
            "C — bounded B16 Entry/Exit slice",
            "C — signed transition-state v1 boundary",
            "C — accepted bounded centreline view",
            "C — transient exact centreline",
            "P — private-development DXF only",
            "C — bounded transition records",
            "[Transition pilot](contracts/phase1-transition-pilot.json); "
            "[Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md); "
            "[Phase 6 evidence](current/PHASE_EVIDENCE.md)",
            "Partial",
        ),
        (
            "Multiple parallel tracks",
            "C — fixed two-track fixture",
            "P — fixture-only Entry/Exit records for one secondary track",
            "P",
            "P — representative pair only",
            "P — transition records only",
            "A",
            "P",
            "[Workflow coverage contract](contracts/"
            "phase1-workflow-coverage.json); [Phase 5 closeout](history/"
            "phase-closeouts/PHASE5_CLOSEOUT.md#"
            "representative-multi-object-selection-and-edit-tranche)",
            "Partial",
        ),
        (
            "General track widening",
            "P — B14 source contains a general track/platform-widening route; "
            "no dedicated accepted general-widening fixture was found",
            "A — spacing-transition evidence does not establish general widening",
            "A for general widening",
            "A for general widening",
            "A for general widening",
            "A",
            "A for general widening",
            "[B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 workflow "
            "inventory](phase-evidence/PHASE1_INVENTORY.md#"
            "release-critical-workflow-coverage-inventory)",
            "Partial",
        ),
        (
            "Spacing-matched Entry/Exit transitions",
            "C — accepted spacing-matched secondary plain-line Entry/Exit fixture",
            "P — fixture-only accepted Entry/Exit slice",
            "P — transition-state v1 records derived from start/curve/finish "
            "spacing",
            "P — bounded transition centreline pair only",
            "P — transient transition centrelines only",
            "P — private-development DXF only",
            "P — bounded transition records only",
            "[Phase 4 closeout](history/phase-closeouts/PHASE4_CLOSEOUT.md#"
            "exact-family-support-enablement); [Phase 5 closeout](history/"
            "phase-closeouts/PHASE5_CLOSEOUT.md#"
            "representative-multi-object-selection-and-edit-tranche); "
            "[Phase 6 evidence](current/PHASE_EVIDENCE.md#"
            "phase-6-exits-2-and-3-evidence-admission-panel)",
            "Partial",
        ),
        (
            "Turnouts",
            "C — bounded REA C10 lifecycle oracle",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[Workflow coverage contract](contracts/"
            "phase1-workflow-coverage.json); [turnout series](benchmarks/"
            "2026-07-20-b14-standalone-turnout-workflow-series.md)",
            "Partial",
        ),
        (
            "Crossovers",
            "C — bounded XO-001 geometry and lifecycle evidence",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[Crossover feasibility contract](contracts/"
            "phase1-crossover-feasibility.json); [workflow coverage contract]"
            "(contracts/phase1-workflow-coverage.json)",
            "Partial",
        ),
        (
            "Sleepers and turnout timbers",
            "C — bounded automatic crossover-timbering evidence",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[Timbering contract](contracts/phase1-crossover-timbering.json); "
            "[Phase 1 workflow inventory](phase-evidence/PHASE1_INVENTORY.md#"
            "release-critical-workflow-coverage-inventory)",
            "Partial",
        ),
        (
            "Chair analysis",
            "C — bounded logical analysis, invalidation and persistence evidence",
            "A — chair analysis is not migrated",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[Chair persistence contract](contracts/"
            "phase1-chair-analysis-persistence.json); [chair invalidation "
            "contract](contracts/phase1-chair-analysis-invalidation.json)",
            "Partial",
        ),
        (
            "Procedural chairs and support components",
            "P — five-box bodies are legacy gap evidence, not the production "
            "oracle",
            "P — neutral package validation boundary only",
            "P — chair-definition package v1",
            "A",
            "A",
            "A",
            "P — serialisable package, not supported FreeCAD product persistence",
            "[Chair package fixture](../tests/fixtures/"
            "chair-definition-v1-contract.json); [architecture boundary]"
            "(ARCHITECTURE.md#chair-definition-and-procedural-geometry-contract)",
            "Partial",
        ),
        (
            "Platforms",
            "P — substantial B14 source exists; the accepted inventory retains "
            "physical platform and wider-workflow gaps",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 workflow "
            "inventory](phase-evidence/PHASE1_INVENTORY.md#"
            "release-critical-workflow-coverage-inventory)",
            "Partial",
        ),
        (
            "Formation boards",
            "P — substantial B14 source exists; no dedicated accepted "
            "formation-board migration fixture was found",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "[B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 inventory]"
            "(phase-evidence/PHASE1_INVENTORY.md)",
            "Partial",
        ),
        (
            "SVG",
            "C — fixed plain-line selected and Generate-path output oracles",
            "A",
            "P — bounded transition intent exists, not an SVG output contract",
            "—",
            "P — centreline-only exact seam",
            "A",
            "—",
            "[Workflow coverage contract](contracts/"
            "phase1-workflow-coverage.json); [selected-export series](benchmarks/"
            "2026-07-19-b14-ordinary-track-selected-export-series.md)",
            "Partial",
        ),
        ("DXF",),
        (
            "STL",
            "C — fixed plain-line legacy output oracle",
            "A",
            "A for solids/meshes",
            "—",
            "A for required production solids/meshes",
            "A",
            "—",
            "[Workflow coverage contract](contracts/"
            "phase1-workflow-coverage.json); [create-time export series]"
            "(benchmarks/"
            "2026-07-19-b14-ordinary-track-create-time-export-series.md)",
            "Partial",
        ),
        (
            "STEP",
            "C — fixed plain-line legacy output oracle",
            "A",
            "A for B-rep production scope",
            "—",
            "A for required production B-reps",
            "A",
            "—",
            "[Workflow coverage contract](contracts/"
            "phase1-workflow-coverage.json); [create-time export series]"
            "(benchmarks/"
            "2026-07-19-b14-ordinary-track-create-time-export-series.md)",
            "Partial",
        ),
        (
            "Calibrated map or image reference layers",
            "U",
            "F",
            "F",
            "F",
            "—",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); no accepted "
            "implementation fixture found",
            "Future",
        ),
        (
            "FreeCAD sketch reference layers",
            "U",
            "F",
            "F",
            "F",
            "—",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); no accepted "
            "implementation fixture found",
            "Future",
        ),
        (
            "Complete-template placement and rotation",
            "U for the Layout Editor meaning",
            "F",
            "F",
            "F",
            "—",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); existing "
            "turnout host placement is a different bounded legacy workflow",
            "Future",
        ),
        (
            "Connected placement, extension, attach and detach",
            "U for the Layout Editor meaning",
            "F",
            "F",
            "F",
            "—",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); no accepted "
            "connected-layout fixture found",
            "Future",
        ),
        (
            "Constituent template geometry editing",
            "U",
            "F",
            "F",
            "F",
            "F where later validation requires it",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); no accepted "
            "implementation fixture found",
            "Future",
        ),
        (
            "Fixed-end fitting and connected-layout solving",
            "U",
            "F",
            "F",
            "F",
            "F where later validation requires it",
            "U",
            "F",
            "[Product vision](PRODUCT_VISION.md#"
            "subsequent-programme-tracktemplate-layout-editor); no accepted "
            "solver fixture found",
            "Future",
        ),
    )
    _require(
        list(rows) == [row[0] for row in expected_rows],
        "capability matrix capability set or ordering drifted",
    )
    for expected_row in expected_rows:
        capability = expected_row[0]
        if capability == "DXF":
            dxf = rows[capability]
            dxf_flat = [_semantic_text(cell) for cell in dxf]
            for index, fragment in (
                (1, "fixed plain-line selected and Generate-path output oracles"),
                (2, "private-development Entry/Exit writer only"),
                (3, "bounded transition intent exists"),
                (5, "transient transition centreline"),
                (6, "deterministic output"),
                (6, "supported-model failure safety"),
                (6, "owner-accepted under D-P6-005"),
                (6, "bounded private-development Entry/Exit route only"),
            ):
                _require(
                    fragment in dxf_flat[index],
                    "capability matrix DXF boundary drifted: " + fragment,
                )
            _require(
                dxf_flat[1].startswith("C —")
                and dxf_flat[2].startswith("P —")
                and dxf_flat[3].startswith("P —")
                and dxf_flat[4] == "—"
                and dxf_flat[5].startswith("P —")
                and dxf_flat[6].startswith("P —")
                and dxf_flat[7] == "—"
                and dxf_flat[9] == "Partial",
                "capability matrix DXF classification drifted",
            )
            _require_links(
                dxf[8],
                (
                    (
                        "Workflow coverage contract",
                        "contracts/phase1-workflow-coverage.json",
                    ),
                    (
                        "current Phase 6 evidence",
                        "current/PHASE_EVIDENCE.md#"
                        "phase-6-exit-3-supported-model-evidence-admission-panel",
                    ),
                ),
                "capability matrix DXF evidence routing drifted",
            )
            continue
        expected_cells = [
            _semantic_markdown(cell)
            for cell in expected_row
        ]
        _require(
            rows.get(capability) == expected_cells,
            "capability matrix structured row drifted: " + capability,
        )

    evidence_limits = direct_section_content(
        matrix,
        "Evidence limits and maintenance",
    )
    _require_paragraph(
        evidence_limits,
        (
            "C never widens the evidence named in its cell. In particular, the "
            "accepted Coin and transient exact-geometry results cover the B16 "
            "Entry/Exit transition slice, not a shared renderer, complete curve "
            "family or whole layout. A legacy C does not mean that the capability "
            "has migrated."
        ),
        "capability matrix lost its legacy-to-Addon evidence limit",
    )
    _require_paragraph(
        evidence_limits,
        (
            "The spacing-matched Entry/Exit row is confined to the accepted "
            "bounded centreline, transition-record and private-development DXF "
            "slice. It does not establish general track widening, a shared "
            "renderer, complete rail, sleeper/timber or chair presentation, "
            "manufacturing geometry, output equivalence, production clearance or "
            "any Phase 6 exit beyond D-P6-002's bounded transient-object "
            "acceptance."
        ),
        "capability matrix lost its spacing-transition evidence limits",
    )


def _blockquote_paragraphs(section: str) -> list[str]:
    """Return semantic paragraphs from Markdown blockquotes in one section."""
    paragraphs: list[str] = []
    lines: list[str] = []
    for line in section.splitlines():
        if line.startswith(">"):
            content = line[1:].lstrip()
            if content:
                lines.append(content)
            elif lines:
                paragraphs.append(_semantic_text("\n".join(lines)))
                lines = []
        elif lines:
            paragraphs.append(_semantic_text("\n".join(lines)))
            lines = []
    if lines:
        paragraphs.append(_semantic_text("\n".join(lines)))
    return paragraphs


def _validate_current_governance_evidence(current_evidence: str) -> None:
    """Validate D-GOV-005 state and D-GOV-004 non-regression in its panel."""
    _require(
        '<a id="product-vision-and-execution-governance-panel"></a>'
        in current_evidence,
        "current evidence lost the D-GOV-005 panel anchor",
    )
    section = direct_section_content(
        current_evidence,
        "Product vision and execution governance panel",
    )
    _require_paragraph(
        section,
        (
            "Decision and repository state: This Level 3 governance decision "
            "applies to accepted main at "
            "61237508b0c1fefedcf740afd230e5e563acab3e, the merge commit for PR "
            "#30. PR #30 is therefore merged, not pending. Draft PR #31 and its "
            "bounded transition-DXF branch remain separate, unaccepted Phase 6 "
            "implementation; this governance branch was created from accepted "
            "main and does not alter, rebase, ready or merge that work. Phase 6 "
            "remains current at 0/5, and this panel admits no new phase-exit evidence."
        ),
        "current evidence lost its local repository, PR or Phase 6 state clause",
    )
    quoted = _blockquote_paragraphs(section)
    expected_quoted = [
        _semantic_text(
            "D-GOV-005 — Adopt the TrackTemplate product vision and vision-led "
            "execution model"
        ),
        _semantic_text(
            "PRODUCT_VISION.md owns product purpose, the current TrackTemplate "
            "Core migration, the later Layout Editor horizon and "
            "migration-completion meaning. Architecture adopts D-GOV-005-A "
            "through D-GOV-005-G for canonical state, immutable snapshots, "
            "batched Coin presentation, lightweight normal editing, on-demand "
            "exact geometry, ViewProvider-owned display modes, presentation "
            "performance and product horizons. Work selection follows vision → "
            "architecture → programme → phase → evidence → bounded item → "
            "assignment → independent evidence and acceptance. The Chief of "
            "Staff and literal $tracktemplate-continue workflow apply that "
            "selection and accountability model."
        ),
        _semantic_text(
            "Vision supplies direction, not scope. D-GOV-004 continues to own "
            "literal continuation invocation and its one-cycle Level 1/2 "
            "execution limit. This decision changes no Phase 6 criterion or exit "
            "status; implements no shared renderer, ViewProvider, exact-geometry "
            "expansion, output, persistence or railway calculation; authorises no "
            "Layout Editor feature; accepts no pull request, migration completion, "
            "output clearance, package, release or phase exit; and leaves draft "
            "PR #31 separate and unaccepted."
        ),
    ]
    _require(
        quoted == expected_quoted,
        "current evidence D-GOV-005 authority block drifted or gained a "
        "competing record",
    )


def _validate_product_direction(current_evidence: str) -> None:
    """Require localised vision, architecture and evidence-map boundaries."""
    _validate_product_vision(_read(PRODUCT_VISION_PATH))
    _validate_architecture_direction(_read(ARCHITECTURE_PATH))
    _validate_capability_matrix(_read(CAPABILITY_MATRIX_PATH))
    _validate_current_governance_evidence(current_evidence)


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
    _validate_product_direction(current_evidence)
    _validate_fixed_paths()
    _validate_ci_workflow()
    print("Project dashboard and current-record validation passed")


if __name__ == "__main__":
    main()
