#!/usr/bin/env python3
"""Validate the compact dashboard, frozen closeouts, and current records."""

from __future__ import annotations

import hashlib
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
PERFORMANCE_SOP_PATH = ROOT / "reference" / "PERFORMANCE_SOP.md"
TERMINOLOGY_PATH = ROOT / "reference" / "TERMINOLOGY.md"
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
# Each tuple contains the date, decision, panel route, authority digest, and
# exclusions digest. The digests bind the complete UTF-8 register fields.
EXPECTED_PHASE6_DECISIONS = {
    "D-P6-001": (
        "2026-08-01",
        "Open Phase 6.",
        "reference/current/PHASE_EVIDENCE.md#phase-6-opening-panel",
        "30251ac623544df6a253373edf5c01fa174c5166a9deac0a1859d6187b411f94",
        "5d64c15adbcf5ed432adcbb48bc24620d12a254d24f97bd3b737edc454565199",
    ),
    "D-GOV-005": (
        "2026-08-01",
        (
            "Adopt the TrackTemplate Product Vision and an execution model "
            "based on it."
        ),
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#product-vision-and-execution-governance-panel"
        ),
        "5f374fbeb09e7f5409c5063afdac92e62ac3cf4b11c595985e74151cd5ee64f9",
        "bf5e99281efe057f11f4ccdbbd87261344ece78ec45a4c37355175c725b3a0a3",
    ),
    "D-P6-002": (
        "2026-08-02",
        "Accept Phase 6 Exit 2 and retain Exit 3 Pending.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exits-2-and-3-evidence-admission-panel"
        ),
        "25a3ece0a3a0057f66bea805c24bea0c661d7a9b0208639cd40d7271847dc5e8",
        "51f76d4a6339f3b28bdb11c09c8e2f56c6b079607bd831cb9a4ce4a8beb57d98",
    ),
    "D-P6-003": (
        "2026-08-02",
        "Select strict completion rules for Exit 3 recovery.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exit-3-recovery-authority-contract-panel"
        ),
        "e513389bcddb1dceaa29cf6e2c00bbcc7ecf9a3b1b9f0d734474023307e608fb",
        "bc8bfe13e0d53f3839734e12cac312b4443593476228c7180bbda7d22e8449fa",
    ),
    "D-P6-004": (
        "2026-08-15",
        "Define the supported exporter failure model and its evidence limit.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exporter-fault-model-clarification-panel"
        ),
        "6bc24b07a9d1e5bb8c8f99eb3605a188c374d7101db2b99b279a08152b70dab5",
        "13c36c9a504efa48b4f1ae308ce1e16c259de2a05e3988cfd06b94a15e87081a",
    ),
    "D-P6-005": (
        "2026-08-15",
        "Accept Phase 6 Exit 3 for the bounded B16 Entry/Exit exporter.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exit-3-supported-model-evidence-admission-panel"
        ),
        "52ede8d935c565028ab570dc31279b390db801b4f579f70b9a593a7ccc6952b5",
        "88d1b941e15afd12ad36106a8c7e32db01446b46b8269746801197b0971263a7",
    ),
    "TT-DOC-001": (
        "2026-08-15",
        "Adopt the TrackTemplate Technical Documentation Profile.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#tt-doc-001-documentation-architecture-panel"
        ),
        "60cfd12a3941b0ef596c70229bae3ca10026b28e622907e022f951eb17b5edea",
        "99a0e8ec8a6a4ff44cb3320741ed64d76884b2996f5024985ffe39ddce9fe0e1",
    ),
    "TT-DOC-002": (
        "2026-08-15",
        "Correct the TT-DOC-001 instruction for UK English.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#tt-doc-002-uk-english-spelling-correction-panel"
        ),
        "ba5f655e63fe208696e9fd03808b7e4a84b736439e24d81a2c009c95a2b62ba8",
        "7e0289ab67901a6b3078d620e7f1f14c8b72ea0826b903cc3e6cf4676dae7cd3",
    ),
    "D-GOV-006": (
        "2026-08-15",
        "Qualify the exact FreeCAD 1.1.3 host profile.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#freecad-1-1-3-compatibility-requalification-panel"
        ),
        "c5255a5f08624f980d410a6cd45453e27fcad3d689b2b1fcea3c7bcfbec90f29",
        "4ed48bdaf7b64ae2c3af23426c9ab0bcdcc38a8204a6acda38e363cbe562c41a",
    ),
    "D-GOV-007": (
        "2026-08-16",
        (
            "Authorise the exact FreeCAD 1.1.3 profile for Phase 6 "
            "performance evidence."
        ),
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-performance-evidence-host-boundary-panel"
        ),
        "7efed03343a5e0f5809ebe66d8a8fe8c09aea964c9fcc9d409db9a361af432e7",
        "de60cdef93da0d1752f33bf342dfee26e5ae9fde7e043f0dfce7c4451d2f888c",
    ),
    "D-GOV-008": (
        "2026-08-16",
        (
            "Accept the Phase 6 Exit 4 comparison baseline and performance "
            "direction."
        ),
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exit-4-performance-direction-panel"
        ),
        "020bb03a2ff19a9ef0e35746b45a8ae1791028aa5aeb3ea2948fdf3625131b46",
        "26e987683368b4641eff1a0214dfddc74625635f9e5d75fd94c44d343eac2e86",
    ),
    "D-GOV-009": (
        "2026-08-23",
        (
            "Record the D-GOV-008 direction as exhausted and select baseline "
            "attribution."
        ),
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exit-4-d-gov-009-panel"
        ),
        "a3772cf1a6b5fc251dae1e608440d69d0bb54601341686df0d5b493a30cb5d51",
        "63cf152328ead842c439bf704d64cdfe987d52504991afacf33d4fd59c07e653",
    ),
    "D-GOV-010": (
        "2026-08-23",
        "Qualify the new exact FreeCAD 1.1.3 host profile.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#freecad-1-1-3-py31313-qt6111-qualification-panel"
        ),
        "6560bc0b5c85f626bafa3c967f793a18f9671319813f1eebcabe00ecc7117405",
        "6ea566c0ed669a0220ec9ed12ff0739bde6a15649523855cee505161d5b248f7",
    ),
    "D-GOV-011": (
        "2026-08-23",
        "Select one canonical-record performance hypothesis.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#phase-6-exit-4-d-gov-011-direction-selection-panel"
        ),
        "60096e93c2464f2939a4f3f44894508c43dcd04134f98ce541f60d0ff16b4089",
        "09c6d15c429b174f6ca68a7eddbd39de652c2b9861108ec644ed961e4ae6b0e1",
    ),
    "D-GOV-012": (
        "2026-08-25",
        "Record the sequence nonconformance after worktree retirement.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#d-gov-012-worktree-sequence-nonconformance"
        ),
        "5cb62e99d39efbb0653bc7b6e126ddb6b49b17135d52c5c4665edd22faafe99b",
        "d9c5f694e0068cf39f76e755fec1a629c7b0b8bdcb69586d538c2cea6407071d",
    ),
    "D-GOV-015": (
        "2026-08-31",
        "Adopt the simplified single-review STE lifecycle.",
        (
            "reference/current/PHASE_EVIDENCE.md"
            "#d-gov-015-simplified-ste-lifecycle"
        ),
        "81641613e133fea5946be8895d027037578b67a3ce5f048552baf21c6acf6a33",
        "869717862c88675519f8b24b74419e33dcca25a3077272a43fa5c0e188131ad0",
    ),
}
EXPECTED_PHASE6_DECISION_IDS = set(EXPECTED_PHASE6_DECISIONS)
EXPECTED_PHASE6_AUTHORITY = (
    "At source state `35d4124c28d6be7e536a5f3773681ff0bf243283`, "
    "open Phase 6 at 0/5 for bounded exact-validation and export-seam work "
    "on the accepted B16 Entry/Exit transition slice. Separate Level 2 "
    "tranches may establish the exact centreline result, oracle, and "
    "contracts, "
    "complete stage signatures and invalidation, transient exact geometry "
    "in a disposable FreeCAD document, private-development target-format "
    "export with atomic staging and rollback, and complete "
    "edit/Validate/Export performance evidence."
)
EXPECTED_PHASE6_EXCLUSIONS = (
    "No Phase 6 exit, production-output clearance, or `project-cleared` "
    "status is accepted. No operator route, migration route, whole-layout "
    "work, or complete B14 export port is accepted. No persisted-schema "
    "change, retained production shape, or legacy-oracle retirement is "
    "accepted. No numerical performance budget, new runtime dependency, "
    "packaging, release, or later-phase authority is accepted. Any required "
    "manifest-schema change receives separate API, licensing, validation, "
    "and owner review."
)
EXPECTED_EXIT2_PANEL_AUTHORITY = (
    "At accepted `main` source state "
    "`a5b6a79bf3e73e1673d440077bd65000986bb4c7`, accept Phase 6 Exit 2, "
    "“No transient production objects leak into the editable document”, as "
    "`Evidenced` and owner-accepted only for the accepted B16 Entry/Exit "
    "transition exact-validation and export routes assessed by this panel. "
    "Phase 6 advances from 0/5 to 1/5. Exit 3 remains Pending until its six "
    "recorded required-before-exit conditions are satisfied and a fresh Level "
    "3 review to admit evidence recommends acceptance."
)
EXPECTED_EXIT2_PANEL_EXCLUSIONS_ONE = (
    "No authority is granted for Phase 6 Exit 1, 3, 4, or 5. Production "
    "clearance, physical-output clearance, `project-cleared` status, and "
    "output equivalence are not granted. No product-wide export roster, GUI "
    "workflow, or operator workflow is granted. No persisted or retained "
    "exact geometry is granted."
)
EXPECTED_EXIT2_PANEL_EXCLUSIONS_TWO = (
    "Whole-B14 parity, whole-layout parity, legacy retirement, and performance "
    "acceptance are not granted. No packaging, release authority, or risk "
    "downgrade is granted. The export remains private-development with "
    "deliberately `unknown` project status. PR #33 performance evidence does "
    "not satisfy Exit 4."
)
EXPECTED_EXIT3_ACCEPTANCE_SCOPE = (
    "At protected `main` `7198b05b6a4b7e4654b7d02d0bad4e5cf627a799`, I "
    "accept Phase 6 Exit 3, “Export is deterministic and failure-safe”, as "
    "Evidenced and owner-accepted only for the bounded B16 Entry/Exit "
    "private-development DXF-and-dependency-manifest route under D-P6-003 "
    "and D-P6-004. Phase 6 advances from 1/5 to 2/5."
)
EXPECTED_EXIT3_ACCEPTANCE_COVERAGE = (
    "This acceptance covers deterministic names, bytes, hashes, schema, and "
    "identifiers. It covers descriptor-relative add-only/no-overwrite "
    "publication. It covers exact-complete reuse and exact-partial monotonic "
    "completion. It covers supported exception, cancellation, and retained "
    "interruption evidence. It also covers staging, publication, cleanup, "
    "durability, and process-termination evidence. Qualified FreeCAD import "
    "and host execution are included."
)
EXPECTED_EXIT3_ACCEPTANCE_COVERAGE_CONTINUED = (
    "Truthful conservative diagnostics are included. Restart-based "
    "containment with independent destination revalidation is also included."
)
EXPECTED_EXIT3_ACCEPTANCE_LIMITATIONS = (
    "It does not extend assurance to interruption at every arbitrary "
    "instruction. It does not extend assurance to repeated interruption of "
    "cleanup, physical power loss, or unqualified hosts or file systems. "
    "Continuously active external mutation after final observation is not "
    "included. Destructive or manual recovery is not included."
)
EXPECTED_EXIT3_ACCEPTANCE_PRESERVATION = (
    "Existing and published finals must never be deleted, renamed, rewritten, "
    "truncated, replaced or manually altered to recover."
)
EXPECTED_EXIT3_ACCEPTANCE_EXCLUSIONS = (
    "Output remains private-development with project status `unknown`. No "
    "authority is granted for Exit 1, 4, or 5. No production or "
    "physical-output clearance is granted. No `project-cleared` status or "
    "output equivalence is granted. No GUI/operator or wider-family authority "
    "is granted. No persisted schema or retained exact geometry is granted. "
    "No performance acceptance, legacy retirement, packaging, or release "
    "authority is granted. No risk downgrade or later-phase authority is "
    "granted."
)
EXPECTED_STE_LIFECYCLE_PLAN_ROW = (
    "| D-GOV-015 | 2026-08-31 | Accepted | The "
    "[decision](current/PHASE_EVIDENCE.md#d-gov-015-simplified-ste-lifecycle) "
    "adopts author → freeze scope → one Documentation Review → optional exact "
    "reviewed correction once → one final deterministic validation → complete "
    "or owner stop. Phase 6 stays at 2/5. If validation is exact-green, the "
    "owner permits one draft pull request. The owner gives no merge authority. |"
)
EXPECTED_PHASE6_DISPOSITIONS = [
    (
        "Pending. Exact-validation and private-development DXF evidence "
        "exists. Agreed output equivalence and production clearance remain "
        "absent."
    ),
    (
        "Evidenced and owner-accepted under D-P6-002 — bounded to the accepted "
        "B16 Entry/Exit exact-validation and export routes with the recorded "
        "limitations"
    ),
    (
        "Evidenced and owner-accepted under D-P6-005. This is bounded to the "
        "private-development B16 Entry/Exit DXF-and-manifest route under "
        "D-P6-003 and D-P6-004. The recorded platform, recovery, and "
        "assurance limitations apply. Project status remains `unknown`."
    ),
    (
        "Pending — D-GOV-008 stays the authority for its baseline, hypothesis, "
        "and comparison rule. D-GOV-009 records the two results as retained negative "
        "evidence and stops work in that direction. Its attribution record "
        "gives a PASS result for the canonical area, which is only `0.0731425 ms` "
        "higher than the noise floor. D-GOV-010 qualifies the exact host for that "
        "evidence. D-GOV-011 selects one subsequent hypothesis for the canonical "
        "record and its comparison rule. It makes no product change, admits no performance "
        "result, and does not accept Exit 4."
    ),
    (
        "Pending. B14 remains available. Parity for the complete accepted "
        "work and retirement authority remain absent."
    ),
]
EXPECTED_PHASE6_PERFORMANCE_DISPOSITION = (
    "Under D-P6-002, Phase 6 remains 1/5 with Exit 2 alone Evidenced and "
    "owner-accepted. This evidence does not satisfy Exit 4, which remains "
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
            "Conduct a fresh Level 3 review to admit evidence before any "
            "Exit 3 acceptance."
        ),
    ],
}
EXPECTED_EXIT3_RECOVERY_ROWS = {
    "Recoverable DXF-and-manifest transaction": [
        "Recoverable DXF-and-manifest transaction",
        (
            "Open technical gap — durable live-invocation controls and "
            "in-process rollback are present. No independently trusted "
            "creation authority supports cross-process automatic recovery."
        ),
    ],
    "Descriptor-relative rename and symbolic-link control": [
        "Descriptor-relative rename and symbolic-link control",
        (
            "Present — all transaction operations use the bound directory "
            "descriptor. Focused replacement proofs fail closed. A Level 3 "
            "panel has not admitted this evidence."
        ),
    ],
    "Interruption, partial-commit and recovery proof": [
        "Interruption, partial-commit and recovery proof",
        (
            "Open technical gap — abrupt one-link and two-link termination "
            "prove exact residue preservation and fail-closed rejection. They "
            "do not prove automatic recovery."
        ),
    ],
    "Qualified zero-length POINT import": [
        "Qualified zero-length POINT import",
        (
            "Present — qualified FreeCAD imports one exact vertex and restores "
            "host state. A Level 3 panel has not admitted this evidence."
        ),
    ],
    "Durable qualified command and sentinel": [
        "Durable qualified command and sentinel",
        (
            "Present in reference/VALIDATION.md. A Level 3 panel has not "
            "admitted this evidence."
        ),
    ],
    "Fresh Level 3 review to admit evidence": [
        "Fresh Level 3 review to admit evidence",
        "Open — required before Exit 3 can be recommended or accepted.",
    ],
}
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
        and (
            "exact zero-member, DXF-only, manifest-only, and complete-pair "
            "states"
        )
        in validation_flat
        and "Historical controls remain inert" in validation_flat
        and "interruption after each addition" in validation_flat
        and "next-invocation monotonic completion" in validation_flat
        and "Complete-pair reuse requires directory synchronisation"
        in validation_flat
        and "A synchronisation failure must preserve data and fail closed"
        in validation_flat
        and "resolve-to-bind removal, and substitution" in validation_flat
        and "post-lock substitution" in validation_flat
        and "initial-member and post-addition substitution" in validation_flat
        and "Unsupported primitives must fail closed" in validation_flat
        and "It refuses non-regular finals and byte collisions"
        in validation_flat
        and "Active-lock diagnostics must fail closed" in validation_flat
        and "observed descriptor-close abandonment" in validation_flat
        and "The original interruption must propagate on a surviving host "
        "with truthful chained `BaseException` diagnostics" in validation_flat
        and "It must remain the primary interruption when an anonymous close "
        "fails" in validation_flat
        and "Cleanup must attempt all remaining anonymous closes"
        in validation_flat
        and "Bound-directory close diagnostics must not replace the original "
        "error" in validation_flat
        and "Post-link/pre-sync durability uncertainty must remain "
        "non-recoverable"
        in validation_flat
        and "All retained-state diagnostics must be truthful"
        in validation_flat
        and (
            "The proof covers the bounded D-P6-003 strict add-only, "
            "journal-free "
            "implementation"
        )
        in validation_flat
        and "TrackTemplate removes, rewrites, or replaces no published final"
        in validation_flat
        and "exact partial preservation, and next-invocation completion"
        in validation_flat
        and "surviving-host interruption cleanup" in validation_flat
        and (
            "They supply no GUI, production-output, Phase 6 exit, or release "
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
            if "The active programme is" in _semantic_text(paragraph)
        ),
        "",
    )
    programme = _semantic_text(programme_paragraph)
    for fragment in (
        "active programme is the TrackTemplate Core macro-to-Addon migration",
        "migration has defined completion conditions",
        "Addon must be the usual route",
        "modular tracktemplate package must contain the one authoritative "
        "product implementation",
        "Addon must not use the legacy macro when the product operates",
        "must not use the legacy macro",
        "owner must accept the claimed Core parity and output",
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
        "Layout Editor is the later programme",
        "does not change the Phase 6 exits",
        "project can record its future architecture without current implementation",
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
        "Phase 6 has 2/5 accepted exits",
        "The owner accepted Exits 2 and 3",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays `unknown`",
        "D-GOV-011",
        "selects one later performance hypothesis for the measured canonical "
        "Edit area",
        "limits the Level 2 product change to one FreeCAD adapter file",
        "D-GOV-009, D-GOV-010, and their evidence do not change",
        "D-GOV-009 attribution result and source assessment",
        "two repeated reads of the selected record",
        "does not need work in another Edit stage",
        "attribution noise floor is `2.895891 ms`",
        "first quartile was only `0.0731425 ms` higher than that floor",
        "evidence does not report the cost of each operation",
        "selected performance hypothesis can fail its later comparison",
        "No result is improvement evidence or Exit 4 evidence",
        "tracktemplate/adapters/freecad/transition_state.py",
        "Keep one live read before the write",
        "necessary read after the write",
        "Preserve all specified invariants",
        "Make the D-GOV-011 Level 2 change in a new cycle",
        "record a new same-host baseline on the D-GOV-010 host",
        "Apply the D-GOV-009 attribution materiality rule to the canonical area",
        "Do not change the comparison rule",
        "A later Level 3 owner decision is necessary to accept Exit 4",
    ):
        _require(
            fragment in owner_view,
            "project-plan owner view lost or contradicted: " + fragment,
        )
    plan_preamble = direct_section_content(plan, "Project Plan", level=1)
    _require(
        "canonical registers and evidence are the source of this owner view. "
        "This view does not establish authority"
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
        len(plan.splitlines()) <= 160,
        "PROJECT_PLAN.md exceeded its 160-line dashboard budget",
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
        match = re.fullmatch(
            r"(\d+)/(\d+) (evidenced|accepted exits)",
            cells[2],
        )
        _require(match is not None, "invalid phase exit status: " + cells[2])
        phase = int(cells[0])
        rows[phase] = {
            "count": int(match.group(1)),
            "total": int(match.group(2)),
            "status_term": match.group(3),
            "state": cells[3],
        }

    _require(set(rows) == set(PHASE_TOTALS), "project phase rows must be 0 through 11")
    for phase, total in PHASE_TOTALS.items():
        _require(rows[phase]["total"] == total, "phase total drifted: {}".format(phase))
        expected_term = "accepted exits" if phase == 6 else "evidenced"
        _require(
            rows[phase]["status_term"] == expected_term,
            "phase exit-status term drifted: {}".format(phase),
        )
    _require(rows[4]["count"] == 6, "Phase 4 must show six evidenced exits")
    _require(
        rows[4]["state"] == "Complete — accepted 2026-07-28",
        "Phase 4 must be closed with the accepted date",
    )
    _require(
        rows[5]["count"] == 4
        and rows[5]["state"] == "Complete — accepted 2026-08-01",
        "Phase 5 must be closed with all four accepted exits",
    )
    _require(
        rows[6]["count"] == 2
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
        "Phase 6 current — 2/5 accepted exits" in " ".join(plan.split())
        and "owner accepted Exit 2 under D-P6-002 on 2026-08-02"
        in " ".join(plan.split())
        and "Exit 3 under D-P6-005 on 2026-08-15"
        in " ".join(plan.split()),
        "the accepted Phase 6 2/5 status is missing",
    )
    return rows


def _validate_performance_host_sources(
    performance_sop: str,
    validation: str,
) -> None:
    """Keep the exact-host performance authority in its two owning units."""
    performance_sop_flat = _semantic_text(performance_sop)
    validation_flat = _semantic_text(validation)
    for source_name, source_text in (
        ("PERFORMANCE_SOP", performance_sop_flat),
        ("VALIDATION", validation_flat),
    ):
        for required_clause in (
            "linux-x86_64-flatpak-freecad-1.1.1",
            "linux-x86_64-flatpak-freecad-1.1.3",
            "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
            "D-GOV-010",
            "authorise only",
            "supply candidate",
            "A subsequent decision can admit only a performance result from "
            "one of these profiles",
            "schema-2",
            "1.1.1 report from 2026-08-02 is a schema-1 report",
            "does not have a host_profile_id field",
            "qualified-runtime contract hash",
            "identify the exact host profile for FreeCAD 1.1.1",
            "as 1.1.1 evidence",
            "one exact host profile",
            "admit no performance result",
            "baseline",
            "do not accept Exit 4",
        ):
            _require(
                required_clause in source_text,
                source_name + " performance host boundary drifted: "
                + required_clause,
            )
        _require(
            "do not identify the exact host profile for FreeCAD 1.1.1"
            not in source_text,
            source_name + " performance host boundary drifted: identify the "
            "exact host profile for FreeCAD 1.1.1 (contradicted)",
        )
    _require(
        "independently shows the effect of the host profile and the "
        "TrackTemplate effect" in performance_sop_flat,
        "PERFORMANCE_SOP performance host boundary drifted: independently "
        "shows the effect of the host profile and the TrackTemplate effect",
    )
    _require(
        "independently shows both effects. These are the host-profile effect "
        "and the TrackTemplate effect" in validation_flat,
        "VALIDATION performance host boundary drifted: independently shows "
        "the effect of the host profile and the TrackTemplate effect",
    )
    _require(
        "project qualifies a subsequent host profile, this does not "
        "authorise performance evidence from that profile"
        in performance_sop_flat,
        "PERFORMANCE_SOP performance host boundary drifted: project qualifies "
        "a subsequent host profile, this does not authorise performance "
        "evidence from that profile",
    )
    _require(
        "Qualification of a subsequent host profile does not authorise its "
        "performance evidence" in validation_flat,
        "VALIDATION performance host boundary drifted: project qualifies a "
        "subsequent host profile, this does not authorise performance evidence "
        "from that profile",
    )
    _require(
        "previous 1.1.1-only validator rejected the 1.1.3 test result"
        in validation_flat
        and "D-GOV-007 does not admit this test result as Exit 4 evidence"
        in validation_flat,
        "VALIDATION admitted the rejected 1.1.3 test result",
    )
    for required_clause in (
        "profile_id",
        "identifies the measurement method, not the record schema",
        "schema_version value is 2",
    ):
        _require(
            required_clause in performance_sop_flat,
            "PERFORMANCE_SOP performance schema boundary drifted: "
            + required_clause,
        )
    for required_clause in (
        "validator examines new schema-2 results",
        "rejects schema 1",
        "host_profile_id value that is not a string",
        "result set that contains two host profiles",
    ):
        _require(
            required_clause in validation_flat,
            "VALIDATION performance schema boundary drifted: "
            + required_clause,
        )
    _require(
        "ID and FreeCAD version of the exact host profile"
        in performance_sop_flat,
        "PERFORMANCE_SOP performance host boundary drifted: ID and FreeCAD "
        "version of the exact host profile",
    )
    _require(
        "ID and FreeCAD version of its exact host profile" in validation_flat,
        "VALIDATION performance host boundary drifted: ID and FreeCAD version "
        "of its exact host profile",
    )
    _require(
        "claim that TrackTemplate performance became better, compare results "
        "from one exact host profile" in performance_sop_flat,
        "PERFORMANCE_SOP performance comparison drifted: compare results "
        "from one exact host profile",
    )
    _require(
        "Use one exact host profile to compare TrackTemplate performance"
        in validation_flat,
        "VALIDATION performance comparison drifted: use one exact host "
        "profile",
    )


def _validate_performance_direction_sources(
    performance_sop: str,
    terminology: str,
    current_evidence: str,
) -> None:
    """Keep D-GOV-008 history and D-GOV-009 bounded."""
    heading = "Phase 6 Exit 4 comparison direction"
    _require(
        '<a id="phase-6-exit-4-comparison-direction"></a>\n\n## '
        + heading in performance_sop,
        "D-GOV-008 performance-direction anchor or heading is missing",
    )
    direction = _section(performance_sop, heading)
    direction_flat = _semantic_text(direction)
    for required_clause in (
        "accepts the PR #50 performance series as the comparison baseline",
        "83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a",
        "f370b029bb4c1ce34987dc025a741185e233df04",
        "linux-x86_64-flatpak-freecad-1.1.3",
        "phase6-transition-edit-validate-export-profile-v1",
        "For each of the 31 interior stations, the API does a 240-step Simpson "
        "integration from station zero",
        "3.263 ms of process CPU time for each preview regeneration",
        "profile recorded 0.144 seconds for integration and 0.163 seconds for "
        "the preview sampler",
        "zero-origin integration is a measured cost during Edit",
        "One preview batch function can calculate all preview displacement "
        "values without zero-origin integration at each interior station",
        "must do all new calculation work during measured Edit",
        "must add no work to Validate, Export, a warm cycle, cleanup, or an "
        "unmeasured boundary",
        "does not measure process launch, module import, fixture construction, "
        "dialog opening, or document disposal at the end",
        "must add no work to other setup or teardown that the profile does not "
        "measure",
        "Code inspection must show that the candidate does all new product "
        "work during measured Edit",
        "If inspection does not give sufficient proof, stop the cycle",
        "result is FAIL if measured Edit does not include all new candidate "
        "work",
        "tracktemplate/presentation/transition_preview.py",
        "tracktemplate/domain/alignment.py",
        "preserve the scalar alignment API",
        "Preview points must agree with their oracle within 1.0e-10 mm",
        "Exact validation, DXF bytes, manifest bytes, hashes, and diagnostics "
        "must not change",
        "Do not add a cache that the evidence does not make necessary",
        "Do not add a runtime dependency or a public API",
        "must use 12 paired blocks",
        "Use the baseline first in six blocks",
        "Use the candidate first in the other six blocks",
        "Preserve all raw attempts",
        "Record the failure class before a replacement pair starts",
        "A product defect, invariant difference, or correctness failure gives "
        "a FAIL result and stops the cycle",
        "replacement is possible only for the failure class "
        "fixture-or-harness-defect or environment-or-profile-defect",
        "attempt with this failure must give no measurement for the comparison",
        "Record the failure class before replacement",
        "same block and the same recorded sequence",
        "For each numeric warm metric, calculate the median of the three "
        "measured warm cycles in one sample",
        "warm block value for that sample",
        "All warm-cycle correctness results must be PASS",
        "candidate minus baseline",
        "paired difference for process CPU time in Edit is negative in a "
        "minimum of 10 of the 12 blocks",
        "median of the paired differences for Edit wall time is negative",
        "medians of the paired differences for cold-journey CPU and wall time "
        "are negative",
        "The Level 2 cycle must use the no-displacement rule for Validate, "
        "Export, cleanup, all warm block values, all resource metrics, and the "
        "journey remainder",
        "median of its paired differences is more than its baseline MAD",
        "result is also FAIL if 10 or more paired differences are positive",
        "The Level 2 cycle must use condition 4 for RSS, RSS change, high-water "
        "RSS, and high-water RSS change in each measured stage and the full "
        "journey",
        "All discrete invariants must have results equal to the baseline "
        "results",
        "Code inspection must show that the candidate does all new product "
        "work during measured Edit",
        "New work in an unmeasured boundary gives FAIL",
        "One sample cannot give a PASS result",
        "Do not select a new rule after the project knows the candidate "
        "results",
        "makes no product change",
        "does not admit the baseline or a subsequent result as Exit 4 "
        "evidence",
        "Exit 4 stays Pending",
        "subsequent decision at Level 3 must admit the evidence",
    ):
        _require(
            required_clause in direction_flat,
            "D-GOV-008 performance direction drifted: " + required_clause,
        )
    boundary_marker = "The authorised product boundary at Level 2 is:"
    boundary_end = "The product change must preserve the scalar alignment API."
    _require(
        direction.count(boundary_marker) == 1 and boundary_end in direction,
        "D-GOV-008 authorised product boundary structure drifted",
    )
    boundary = direction.split(boundary_marker, 1)[1].split(boundary_end, 1)[0]
    authorised_product_paths = set(
        re.findall(r"`(tracktemplate/[^`]+)`", boundary)
    )
    _require(
        authorised_product_paths
        == {
            "tracktemplate/domain/alignment.py",
            "tracktemplate/presentation/transition_preview.py",
        },
        "D-GOV-008 authorised product path set drifted",
    )
    _require_links(
        direction,
        ((
            "PR #50 performance series",
            "benchmarks/2026-08-16-phase6-freecad-1.1.3-transition-"
            "pipeline-performance.md",
        ),),
        "D-GOV-008 baseline report link drifted",
    )

    terminology_flat = _semantic_text(terminology)
    for required_term in (
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
        "Setup",
        "Teardown",
    ):
        _require(
            required_term in terminology_flat,
            "D-GOV-008 performance terminology drifted: " + required_term,
        )
    for meaning_clause in (
        "A preview batch function calculates all preview displacement values "
        "in one function",
        "A paired difference is the candidate value minus the baseline value "
        "in one paired block",
        "If an ordered sample has an odd number of values, its median is the "
        "middle value",
        "If an ordered sample has an even number of values, its median is the "
        "sum of the two middle values divided by two",
        "Python statistics.quantiles(..., method='inclusive') gives a first "
        "quartile",
        "High-water RSS is the maximum RSS that the profiler records",
        "A resource metric is an RSS, RSS change, high-water RSS, or high-water "
        "RSS change in a performance record",
        "A journey remainder is the full-journey CPU or wall time minus the "
        "measured stage times",
    ):
        _require(
            meaning_clause in terminology_flat,
            "D-GOV-008 performance terminology meaning drifted: "
            + meaning_clause,
        )

    panel_heading = "Phase 6 Exit 4 performance-direction panel"
    _require(
        '<a id="phase-6-exit-4-performance-direction-panel"></a>\n\n## '
        + panel_heading in current_evidence,
        "D-GOV-008 panel anchor or heading is missing",
    )
    panel = _section(current_evidence, panel_heading)
    panel_flat = _semantic_text(panel)
    for required_clause in (
        "9169b7e7beec5cf614b8a5284db0f97367728def",
        "Phase 6 has 2/5 accepted exits",
        "Exit 4 is Pending",
        "D-GOV-008 is the next decision ID",
        "accepts this series as the comparison baseline",
        "must collect new samples in paired blocks",
        "block must have a baseline sample and a candidate sample",
        "must not use the 1.1.1 report to claim that TrackTemplate performance "
        "became better",
        "fixture-or-harness-defect",
        "selects a performance hypothesis for zero-origin integration in the "
        "preview sampler",
        "approximately 88% of the sampler time in the profile",
        "must use 12 paired blocks",
        "Preserve all raw attempts",
        "product defect, invariant difference, or correctness failure gives a "
        "FAIL result and stops the cycle",
        "replacement is possible only for the failure class "
        "fixture-or-harness-defect or environment-or-profile-defect",
        "attempt with this failure must give no measurement for the comparison",
        "warm block value for that sample",
        "All warm-cycle correctness results must be PASS",
        "Use the no-displacement rule for Validate, Export, cleanup, all warm "
        "block values, all resource metrics, and the journey remainder",
        "Use the same rule for RSS, RSS change, high-water RSS, and high-water "
        "RSS change",
        "result is FAIL if measured Edit does not include all new candidate "
        "work",
        "One sample cannot give a PASS result",
        "defines a comparison rule and not a product budget",
        "makes no product change",
        "does not admit the PR #50 baseline or a subsequent result as Exit 4 "
        "evidence",
        "Exit 4 stays Pending",
        "subsequent decision at Level 3 must admit the evidence",
    ):
        _require(
            required_clause in panel_flat,
            "D-GOV-008 evidence panel drifted: " + required_clause,
        )

    for risk_clause in (
        "PR-15 — deferred cost",
        "QA-R04 — no product performance budget",
        "PR-22 — authority transfer",
        "PR-13 — repository or evidence loss",
        "all unmeasured boundaries",
        "High / Mitigate / Partial. The disposition does not change",
        "High / Remove / Effective for the current bounded scope. The "
        "disposition does not change",
        "Critical / Mitigate / Effective for the current bounded scope. The "
        "disposition does not change",
    ):
        _require(
            risk_clause in panel_flat,
            "D-GOV-008 risk panel drifted: " + risk_clause,
        )

    for conformance_clause in (
        "Documentation conformance",
        "local Issue 9 source",
        "This is the official source",
        "TrackTemplate UK English spelling directive",
        "reference/PERFORMANCE_SOP.md",
        "reference/TERMINOLOGY.md",
        "five new performance-term rows",
        "reference/PROJECT_PLAN.md",
        "reference/current/PHASE_EVIDENCE.md",
        "reference/current/gate-decisions.json",
        "Issue 9 conformance stays Unknown for other live prose",
    ):
        _require(
            conformance_clause in panel_flat,
            "D-GOV-008 conformance scope drifted: " + conformance_clause,
        )

    for review_clause in (
        "Two reviewers who did not make the change must examine one exact "
        "candidate",
        "performance reviewer must examine the baseline and performance "
        "hypothesis",
        "reviewer must examine the comparison rule, no-displacement rule, and "
        "unmeasured boundaries",
        "governance reviewer must examine authority, evidence, documentation, "
        "and preservation",
        "The two reviews must find no blocking condition before the project "
        "merges the candidate",
        "pull request and completion report must record the results",
        "panel must not change after those reviews",
    ):
        _require(
            review_clause in panel_flat,
            "D-GOV-008 review gate drifted: " + review_clause,
        )

    decision_marker = (
        "> **D-GOV-008 — Accept the Exit 4 comparison baseline and "
        "performance direction**"
    )
    _require(
        panel.count(decision_marker) == 1,
        "D-GOV-008 quoted owner decision is missing or duplicated",
    )
    decision_quote = panel.split(decision_marker, 1)[1]
    decision_quote_flat = _semantic_text(
        "\n".join(
            line[2:] if line.startswith("> ") else ""
            for line in decision_quote.splitlines()
            if line.startswith(">")
        )
    )
    for decision_clause in (
        "I accept the PR #50 FreeCAD 1.1.3 series as the comparison baseline",
        "I select one performance hypothesis",
        "I authorise a Level 2 change in the preview sampler",
        "rule uses 12 paired blocks on the exact 1.1.3 host profile",
        "candidate must add no work to an unmeasured boundary",
        "Inspection must show that the candidate does all new product work "
        "during measured Edit",
        "product defect, invariant difference, or correctness failure gives "
        "FAIL and stops the cycle",
        "replacement is possible only for the failure class "
        "fixture-or-harness-defect or environment-or-profile-defect",
        "attempt with this failure must give no measurement for the comparison",
        "Level 2 cycle must record the sequence before measurements start",
        "same block and the same recorded sequence",
        "This decision makes no product change",
        "does not admit the PR #50 baseline or a subsequent result as Exit 4 "
        "evidence",
        "Exit 4 stays Pending",
        "Phase 6 stays at 2/5 accepted exits",
        "subsequent decision at Level 3 must admit the evidence before owner "
        "acceptance of Exit 4",
    ):
        _require(
            decision_clause in decision_quote_flat,
            "D-GOV-008 quoted owner decision drifted: " + decision_clause,
        )

    _require_links(
        panel,
        (
            (
                "PR #50 performance series",
                "../benchmarks/2026-08-16-phase6-freecad-1.1.3-transition-"
                "pipeline-performance.md",
            ),
            (
                "comparison-direction section",
                "../PERFORMANCE_SOP.md#phase-6-exit-4-comparison-direction",
            ),
            (
                "local Issue 9 source",
                "../external/asd-ste100/README.md",
            ),
        ),
        "D-GOV-008 panel link drifted",
    )

    for required_term in (
        "retained negative evidence",
        "exhausted performance direction",
        "baseline-attribution investigation",
        "measurement area",
        "attribution series",
        "attribution noise floor",
        "attribution materiality rule",
        "unattributed remainder",
    ):
        _require(
            required_term in terminology_flat,
            "D-GOV-009 performance terminology drifted: " + required_term,
        )
    for meaning_clause in (
        "Retained negative evidence is preserved evidence from a candidate "
        "with a FAIL comparison result or a required invariant difference",
        "An exhausted performance direction is a performance hypothesis that "
        "has sufficient retained negative evidence to stop new product work "
        "in that direction",
        "A baseline-attribution investigation measures one accepted operator "
        "journey and reports each measurement area without a product change",
        "An attribution series is a set of process samples from that "
        "investigation",
        "Three values give the attribution noise floor",
        "They are the Edit CPU MAD for the baseline, the Edit CPU MAD for "
        "attribution, and the maximum of the calibrated instrumentation "
        "overhead",
        "The noise floor is the highest of these three values",
        "The attribution materiality rule gives PASS when the first quartile "
        "for an applicable measurement area is higher than that floor",
        "An unattributed remainder is measured journey time that is not part "
        "of a different measurement area",
    ):
        _require(
            meaning_clause in terminology_flat,
            "D-GOV-009 performance terminology meaning drifted: "
            + meaning_clause,
        )

    followup_heading = "Phase 6 Exit 4 baseline-attribution direction"
    _require(
        '<a id="phase-6-exit-4-baseline-attribution-direction"></a>\n\n## '
        + followup_heading in performance_sop,
        "D-GOV-009 direction anchor or heading is missing",
    )
    followup_direction = _section(performance_sop, followup_heading)
    followup_direction_flat = _semantic_text(followup_direction)
    for required_clause in (
        "D-GOV-009 records the D-GOV-008 performance direction as exhausted "
        "for new product work for Phase 6 Exit 4",
        "D-GOV-008 stays Accepted as the authority for its comparison "
        "baseline, performance hypothesis, comparison rule, and first boundary "
        "at Level 2",
        "Preserve the two subsequent results from Level 2 as retained negative "
        "evidence",
        "The two results are not improvement evidence",
        "They are not Exit 4 evidence",
        "Do not make a third preview-sampler change",
        "new polynomial, approximation, cache, or other variation of the "
        "D-GOV-008 hypothesis",
        "does not show sufficient measured cost in a different measurement "
        "area that is not part of the D-GOV-008 preview-sampler boundary",
        "D-GOV-009 investigation used the accepted Edit journey on FreeCAD 1.1.3",
        "reported these measurement areas",
        "accepted Edit journey on FreeCAD 1.1.3",
        "Canonical-state and state-construction work",
        "Preview and sampler construction",
        "Coin binding or scene-graph replacement",
        "GUI processing",
        "unattributed remainder",
        "retained record contains the exact host profile, source state, "
        "workload, method, measurement boundary, and instrumentation overhead",
        "reports a measurement area as Unknown when the evidence does not show "
        "a TrackTemplate product boundary or an architectural boundary",
        "investigation changed no product source",
        "made no performance optimisation",
        "result is direction-selection evidence only",
        "D-GOV-011 uses this result to select one different performance "
        "hypothesis",
        "does not change the D-GOV-008 comparison rule",
        "does not do either retained comparison again",
        "defines no product performance budget and does not accept Exit 4",
    ):
        _require(
            required_clause in followup_direction_flat,
            "D-GOV-009 direction drifted: " + required_clause,
        )

    canonical_heading = "Phase 6 Exit 4 canonical-record direction"
    _require(
        '<a id="phase-6-exit-4-canonical-record-direction"></a>\n\n## '
        + canonical_heading in performance_sop,
        "D-GOV-011 direction anchor or heading is missing",
    )
    canonical_direction = _section(performance_sop, canonical_heading)
    canonical_direction_flat = _semantic_text(canonical_direction)
    for required_clause in (
        "D-GOV-011 selects one performance hypothesis in the measured canonical "
        "area of Edit",
        "route reads the selected canonical record three times before the write",
        "necessary check reads it one more time after the write",
        "remove only two repeated reads before the write",
        "keep one live read before the write and the read after the write",
        "tracktemplate/adapters/freecad/transition_state.py",
        "one live state for the stale-edit-base and stable-identity checks",
        "During object mapping, it must use the same state for the selected "
        "object",
        "object-mapping check must still read other canonical records",
        "still reject a duplicate stable identity",
        "public read and update contracts must not change",
        "Do not add a cache",
        "Do not move a record read to selection, setup, teardown, preview, "
        "Coin, or GUI processing",
        "preserve canonical state and transaction semantics",
        "preserve one-unit Undo/Redo",
        "persistence, lifecycle, cleanup, exact validation, deterministic "
        "export, diagnostics, and failure recovery",
        "do the exact attribution method in D-GOV-009 again on clean protected "
        "main",
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "new baseline series of 10 processes and a new attribution series of "
        "10 processes",
        "attribution materiality rule in D-GOV-009",
        "Record the 12-block comparison sequence before a product change",
        "six baseline-first blocks and six candidate-first blocks",
        "new process for each sample",
        "full accepted journey for Edit, Validate, Export, warm reuse, "
        "correctness, lifecycle, output, and cleanup",
        "Process CPU time for Edit is lower in at least 10 of 12 paired blocks",
        "median paired difference is negative",
        "median paired differences for Edit wall time and cold-journey CPU "
        "and wall time are negative",
        "D-GOV-008 no-displacement rule to Validate, Export, cleanup, warm "
        "block values, resource metrics, and the journey remainder",
        "preview and sampler construction, Coin or scene-graph work, GUI "
        "processing, and the unattributed remainder",
        "measurement areas in D-GOV-009 in both samples of each paired block",
        "same test-owned instrumentation in both samples",
        "All discrete invariants and warm-cycle correctness results are equal "
        "to the baseline results",
        "product change removes the two repeated reads",
        "must add no work to an unmeasured boundary",
        "missing condition gives FAIL",
        "host-identity difference gives FAIL",
        "product defect or invariant difference gives FAIL and stops the cycle",
        "Preserve all attempts. Classify a failure before a replacement",
        "Do not select a new rule after the project knows the candidate results",
        "authorises one subsequent product change at Level 2 in this boundary",
        "makes no product change",
        "admits no performance result or Exit 4 evidence",
        "Exit 4 stays Pending",
        "subsequent owner decision at Level 3 is necessary before the owner can "
        "admit a "
        "subsequent result for Exit 4",
    ):
        _require(
            required_clause in canonical_direction_flat,
            "D-GOV-011 direction drifted: " + required_clause,
        )

    followup_panel_heading = "Phase 6 Exit 4 D-GOV-009 panel"
    _require(
        '<a id="phase-6-exit-4-d-gov-009-panel"></a>\n\n## '
        + followup_panel_heading in current_evidence,
        "D-GOV-009 panel anchor or heading is missing",
    )
    followup_panel = _section(current_evidence, followup_panel_heading)
    followup_panel_flat = _semantic_text(followup_panel)
    for required_clause in (
        "bbc90531813415ca966131351f668256cdca838f",
        "D-GOV-009 follows D-GOV-008",
        "does not change D-GOV-008",
        "does not change a retained comparison",
        "Phase 6 has 2/5 accepted exits",
        "Exit 4 is Pending",
        "Project status is unknown",
        "6e1a0c755d7872fe631332d4d1ce4330febdd81b",
        "044244345ea65b8a5ed99548be8f2f1f9f34537eddf813dbb7f92f9c4696f936",
        "temporary D-GOV-008 profile measured 50 preview regenerations",
        "recorded approximately 3.263 ms of process CPU time for one "
        "regeneration",
        "For the 50 regenerations, it recorded 0.144 seconds of integration "
        "process CPU time and 0.163 seconds of preview-sampling process CPU "
        "time",
        "Edit CPU was lower in only 9 of 12 paired blocks",
        "Twenty-two metrics had FAIL results",
        "no length limit and did not keep the 1.0e-10 mm preview-oracle "
        "tolerance in the full product domain",
        "64c167b424fefe604ada0b66deb435eaa32e924ff09c2265a3f9f9569382874b",
        "f402ef196ef78f287357f5484b47505a31a2799c3e6b2160053b6ae927d3a110",
        "73a236a44ce39d4ac8aace714dcac0e4c9f400bf030561718a9c77bf1301ec8b",
        "All 24 samples had PASS validation results",
        "Edit CPU was lower in only 5 of 12 paired blocks",
        "paired median difference was +2.923202 ms",
        "candidate median was approximately 10.71% higher",
        "Ten metrics had FAIL results",
        "The two retained results are not improvement evidence",
        "evidence does not show sufficient cost in a measurement area outside "
        "the D-GOV-008 preview-sampler boundary",
        "Exit 4 stays Pending",
        "local branch agent/phase6-exit4-preview-batch-performance contains "
        "the first candidate",
        "2026-08-23-phase6-exit4-simpson-polynomial-failed-comparison-01",
        "snapshot with checksum PASS results",
        "audit checks showed content identity",
        "Do not change this retained state as part of D-GOV-009",
        "Do not publish it",
        "Do not merge it",
        "Do not remove it",
        "two retained negative results are sufficient to stop new product "
        "work in the D-GOV-008 direction",
        "Do not make a third preview sampler, polynomial, approximation, "
        "cache, or other variation of the D-GOV-008 hypothesis",
        "No measured evidence shows sufficient cost in a measurement area "
        "outside the D-GOV-008 preview-sampler boundary",
        "next action is a bounded baseline-attribution investigation at Level "
        "1",
        "can report a result for each of these measurement areas if the "
        "architecture and the measurement method let it do this",
        "investigation is attribution only",
        "Do not start that investigation in this cycle",
        "subsequent Level 3 owner decision is necessary before a new Level 2 "
        "optimisation",
        "No risk state, treatment, severity, owner, deadline, or control "
        "effectiveness changes",
        "exact Edit cost in each measurement area stays Unknown",
        "internal result for the D-GOV-009 logical units is ASD-STE100 Issue 9 "
        "conforming",
        "This result is a TrackTemplate conformance assessment",
        "It is not external ASD certification, endorsement, or an official "
        "conformance assessment",
        "It does not include exact machine data",
        "It does not include unchanged live prose outside the named logical "
        "units",
        "It does not include frozen history",
        "Issue 9 conformance stays Unknown for other live prose",
        "Proceed with bounded conditions",
    ):
        _require(
            required_clause in followup_panel_flat,
            "D-GOV-009 evidence panel drifted: " + required_clause,
        )

    for risk_clause in (
        "PR-12 — stale or repeated direction",
        "PR-13 — repository or evidence loss",
        "PR-15 — deferred cost",
        "PR-16 — incomplete cache signature",
        "PR-22 — authority transfer",
        "QA-R04 — no product performance budget",
        "Critical / Mitigate / Effective for the current bounded scope",
        "High / Remove / Effective for the current bounded scope",
    ):
        _require(
            risk_clause in followup_panel_flat,
            "D-GOV-009 risk panel drifted: " + risk_clause,
        )

    for review_clause in (
        "new read-only QA, risk, evidence, validation, and documentation "
        "review of the exact candidate",
        "The reviewer who did not make the change must examine the evidence "
        "classes and the two retained negative results",
        "reviewer must also make sure that the change does not start the "
        "baseline-attribution investigation",
        "reviewer must make sure that the change does not admit Exit 4",
        "The project must not merge the candidate if the reviewer finds a "
        "blocking condition",
        "panel must not change after the exact-candidate review",
    ):
        _require(
            review_clause in followup_panel_flat,
            "D-GOV-009 review gate drifted: " + review_clause,
        )

    followup_marker = (
        "> **D-GOV-009 — Record the D-GOV-008 direction as exhausted and "
        "select baseline attribution**"
    )
    _require(
        followup_panel.count(followup_marker) == 1,
        "D-GOV-009 quoted owner decision is missing or duplicated",
    )
    followup_quote = followup_panel.split(followup_marker, 1)[1]
    followup_quote_flat = _semantic_text(
        "\n".join(
            line[2:] if line.startswith("> ") else ""
            for line in followup_quote.splitlines()
            if line.startswith(">")
        )
    )
    for decision_clause in (
        "D-GOV-008 stays Accepted as the authority",
        "D-GOV-009 after D-GOV-008",
        "Preserve the two subsequent Level 2 attempts as retained negative "
        "evidence",
        "The two results are not improvement evidence",
        "They are not Exit 4 evidence",
        "Do not make a third preview sampler, polynomial, approximation, "
        "cache, or other variation of that hypothesis",
        "Current measurements do not show sufficient cost in a measurement "
        "area outside the D-GOV-008 bounded preview-sampler work",
        "next action is a bounded Level 1 baseline-attribution "
        "investigation",
        "Report a result for each measurement area if the method lets the "
        "investigation do this",
        "investigation is attribution only",
        "Do not start the investigation in this cycle",
        "subsequent explicit Level 3 owner decision is necessary before a new "
        "Level 2 optimisation",
        "Phase 6 stays at 2/5 accepted exits",
        "Exit 4 stays Pending",
        "Project status stays unknown",
        "changes no product source, public API, railway mathematics, "
        "persistence, export behaviour, performance threshold, qualified host "
        "profile, or retained evidence",
        "gives no production authority, physical-output authority, "
        "project-cleared status, packaging, release, or tagging authority",
    ):
        _require(
            decision_clause in followup_quote_flat,
            "D-GOV-009 quoted owner decision drifted: " + decision_clause,
        )

    qualification_heading = (
        "Qualification panel and owner decision for the new exact FreeCAD "
        "1.1.3 host profile"
    )
    _require(
        '<a id="freecad-1-1-3-py31313-qt6111-qualification-panel"></a>\n\n'
        "## " + qualification_heading in current_evidence,
        "D-GOV-010 panel anchor or heading is missing",
    )
    qualification_panel = _section(current_evidence, qualification_heading)
    qualification_flat = _semantic_text(qualification_panel)
    for required_clause in (
        "dc750df93682b3b0fd5fdf79fa6fe94296a10697",
        "changes no TrackTemplate product source",
        "Phase 6 has 2/5 accepted exits",
        "Exit 4 is Pending",
        "Project status is unknown",
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "revision 44987 (Git)",
        "145529fe741292ff0b3977a01195bf0247425794",
        "fa3ef6bebc139083246bd4fb6b8baf6a032a3b5bbb0a57479cb14d52bad733ae",
        "d7a54c855bce9f4fb7b00b33d43f0ecb1908af510f9147bcc9bc32f614a6bbad",
        "org.kde.Platform/x86_64/6.11",
        "org.kde.Sdk/x86_64/6.11",
        "CPython 3.13.13",
        "PySide6 6.11.1 with Qt 6.11.1",
        "OpenCASCADE 7.8.1",
        "SIM Coin 4.0.8",
        "runtime guard accepts this profile only when all of its exact_match "
        "data are equal to the reported data",
        "do not change the runtime guard",
        "do not qualify a different Flatpak package",
        "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c",
        "probe reported only the profile that D-GOV-010 identifies and zero "
        "mismatches",
        "Legacy and modular results were equal for both workflows",
        "zero open documents after cleanup",
        "eff5df685a7b37b98cb23a2f853f186aa03a014bda0d2ac19754b8d8fa296e88",
        "fcc98740aaaea626541d095f35d18e98a4b9bff72ce0968d71a5370e83f36865",
        "0c06db37b9bdab8114fe600b34dd62a3beb7af1adc2edc8622fe1eff006fded3",
        "e8bb482506b81ff0e328ffb64f3c37de820fe7a171e8247c866c2d1c38edaf77",
        "16fa438aba7fa967a134241087239a86c14f65a03ad48ea20ef086910cb80713",
        "fixture-or-harness-defect",
        "a4e7168492056439f78dde745b541dc778c82879ef5b8ef3f4568683a60bd54a",
        "d132f439fd0a1f144f2891d2789bbb0cdebe376500c1fb62508d90113cc09cca",
        "adc996312467c3bb821f04f88024e62983418aae5b7977760a3612edb337c25b",
        "bab8889d4e0e920bf5c72fbda11a2d925c86385e450da689dd0730aa8a831306",
        "6df27b7a89079588dfa5ca513ba7df42a7967edfb7ddf3c2eabad1fa017a78c7",
        "No TrackTemplate product source changes",
        "D-GOV-006 and its exact CPython 3.13.14 and PySide6/Qt 6.10.3 "
        "profile do not change",
        "D-GOV-007 authority for its two named profiles does not change",
        "D-GOV-010 authorises this profile to supply candidate evidence for "
        "performance in a subsequent cycle",
        "Each comparison must use one profile with an exact identity",
        "not a TrackTemplate before/after comparison with a result from a "
        "different exact profile",
        "This cycle records no performance measurement, comparison, or "
        "budget",
        "makes no new measurement from either D-GOV-008 result",
        "Both results are retained negative evidence",
        "D-GOV-009 stays the current Exit 4 direction",
        "must record a baseline for this profile",
        "This qualification does not start that investigation",
        "does not select an optimisation candidate and does not accept Exit "
        "4",
        "No risk state, treatment, severity, owner, deadline, or control "
        "effectiveness changes",
        "Issue 9 result for these logical units is Unknown",
        "Continue with bounded conditions",
    ):
        _require(
            required_clause in qualification_flat,
            "D-GOV-010 evidence panel drifted: " + required_clause,
        )

    for risk_clause in (
        "PR-01 — release workflow coverage",
        "PR-13 — repository or evidence loss",
        "PR-17 — persistence or migration corruption",
        "PR-22 — authority transfer",
        "QA-R03 — release GUI evidence",
        "QA-R04 — no product performance budget",
        "Critical / Mitigate / Effective for the current bounded scope",
        "High / Remove / Effective for the current bounded scope",
    ):
        _require(
            risk_clause in qualification_flat,
            "D-GOV-010 risk panel drifted: " + risk_clause,
        )

    for reviewed_path in (
        "reference/PROJECT_PLAN.md",
        "reference/VALIDATION.md",
        "reference/PERFORMANCE_SOP.md",
        "reference/contracts/phase1-compatibility.json",
        "reference/current/PHASE_EVIDENCE.md",
        "reference/current/gate-decisions.json",
    ):
        _require(
            reviewed_path in qualification_panel,
            "D-GOV-010 documentation scope drifted: " + reviewed_path,
        )

    for review_clause in (
        "A new reviewer did not make the change",
        "This reviewer must examine the exact host identity",
        "must also make sure that the change does not start D-GOV-009 "
        "baseline attribution",
        "must not change files",
        "must not merge the candidate after a BLOCK review result",
        "panel must not change after the exact-state review",
    ):
        _require(
            review_clause in qualification_flat,
            "D-GOV-010 review gate drifted: " + review_clause,
        )

    qualification_marker = (
        "> **D-GOV-010 — Qualify the new exact FreeCAD 1.1.3 host profile**"
    )
    _require(
        qualification_panel.count(qualification_marker) == 1,
        "D-GOV-010 quoted owner decision is missing or duplicated",
    )
    qualification_quote = qualification_panel.split(
        qualification_marker,
        1,
    )[1]
    qualification_quote_flat = _semantic_text(
        "\n".join(
            line[2:] if line.startswith("> ") else ""
            for line in qualification_quote.splitlines()
            if line.startswith(">")
        )
    )
    for decision_clause in (
        "qualify only "
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "does not qualify all FreeCAD 1.1.3 hosts",
        "Keep the exact FreeCAD 1.1.1 profile qualified",
        "Keep the D-GOV-006 exact FreeCAD 1.1.3 profile qualified",
        "D-GOV-010 authorises this profile to supply candidate evidence for "
        "performance in a subsequent cycle",
        "Each comparison must use one profile with an exact identity",
        "For a TrackTemplate before/after comparison, do not use results from "
        "profiles with different exact identities",
        "Before the project claims that TrackTemplate performance changed on "
        "this profile, the D-GOV-009 investigation must record a baseline for "
        "this profile",
        "admits no performance result",
        "defines no performance budget",
        "does not start baseline attribution",
        "does not select an optimisation candidate",
        "does not accept Exit 4",
        "changes no product source, public API, railway mathematics, "
        "persistence, schema, export behaviour, qualified-host criterion, "
        "performance threshold, or evidence",
        "Phase 6 stays at 2/5 accepted exits",
        "Exit 4 stays Pending",
        "Project status stays unknown",
        "No risk disposition changes",
    ):
        _require(
            decision_clause in qualification_quote_flat,
            "D-GOV-010 quoted owner decision drifted: " + decision_clause,
        )

    selection_heading = "Phase 6 Exit 4 D-GOV-011 direction-selection panel"
    _require(
        '<a id="phase-6-exit-4-d-gov-011-direction-selection-panel"></a>\n\n'
        "## " + selection_heading in current_evidence,
        "D-GOV-011 panel anchor or heading is missing",
    )
    selection_panel = _section(current_evidence, selection_heading)
    selection_flat = _semantic_text(selection_panel)
    for required_clause in (
        "bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2",
        "D-GOV-011 follows D-GOV-009 and D-GOV-010",
        "changes performance direction only",
        "changes no product source",
        "Phase 6 has 2/5 accepted exits",
        "Exit 4 is Pending",
        "Project status is unknown",
        "D-GOV-009 records the preview-sampler direction as exhausted",
        "D-GOV-010 qualifies the exact host for this evidence",
        "D-GOV-009 attribution record is completed and preserved",
        "attribution noise floor is 2.895891 ms",
        "first quartile of the canonical area was only 0.0731425 ms higher than "
        "that floor",
        "evidence does not report the cost of each operation in that area",
        "not improvement evidence or Exit 4 evidence",
        "77-entry SHA256SUMS check had a PASS result",
        "8e47cb21e4aa8fe4ec1706b60d0ec1c665e3a338d626e7d99fd62e105a31ba22",
        "196060f8d22ac3dcebec720beb77e779534d4371f1212e3da0849ee3f9826568",
        "9695a0d279a4f1472fcfd676a310a66382a0350b05b58b70a215d31cf9f0eee9",
        "02525791c17fa5630be57608543b7c0dfa3c7254cc22c623ff79c007e0a94880",
        "9928501e6460b68742f441f497be602de10596e33d772a65245efa1ee2549c71",
        "f706b4405db524d87bc50bfb36579482450ffa137c84546a502d66354a959d5c",
        "8414286cf783789afc5c079541438e1ff129c9e012163396842bc1607ea33aee",
        "52f141c5c45a9c5752d93d70aece9943e7b535bfde0804c53fc7b5d2cbad6388",
        "2026-08-23-phase6-exit4-attribution-preservation-01",
        "snapshot contains 6,519 files and 1,244 directories",
        "byte check found no difference between the source and snapshot",
        "manifest had a PASS result in the snapshot",
        "does not replace the retained negative-evidence snapshots",
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "baseline series has 10 processes",
        "attribution series also has 10 processes",
        "Each process starts FreeCAD",
        "All correctness, deterministic-output, lifecycle, cleanup, and "
        "host-identity checks had PASS results",
        "Full Edit baseline",
        "29.571971 ms",
        "21.0001125 ms",
        "Canonical state and state construction",
        "3.126380 ms",
        "2.9690335 ms",
        "Preview and sampler construction",
        "1.9991765 ms",
        "1.95987775 ms",
        "Coin or scene-graph work",
        "0.3987415 ms",
        "0.38801125 ms",
        "GUI processing",
        "20.109802 ms",
        "19.804105 ms",
        "TrackTemplate product boundary is Unknown",
        "Unattributed remainder",
        "2.5621155 ms",
        "2.40463225 ms",
        "attribution noise floor is 2.895891 ms",
        "median of the calibrated instrumentation overhead is 0.01776712815 ms",
        "Its maximum is 0.0187707963 ms",
        "baseline and attribution series are not paired",
        "median differences are -1.0994865 ms for process CPU time and "
        "+22.4718825 ms for wall time",
        "application span for "
        "tracktemplate/application/transition_edit.py::edit_transition_length_mm",
        "tracktemplate/adapters/freecad/transition_state.py",
        "measurement subtracts the preview and ViewProvider refresh that occur "
        "in the application span",
        "does not include Coin work or the two calls for GUI processing that "
        "the method names",
        "selected record, apply_transition_edit calls read_transition_object",
        "object-mapping scan calls it for the selected record for a third time",
        "read after the write is necessary for the write check",
        "scan of the other canonical record is necessary for duplicate-identity "
        "rejection",
        "transaction and the property write are necessary for persistence and "
        "one-unit Undo/Redo",
        "product change must not replace the accepted calculation with the "
        "input length",
        "assessment identifies only one hypothesis from the measured cost, identified "
        "operation, and architecture",
        "Keep one live read of the selected record before the write",
        "state for the stale-base and stable-identity checks",
        "During object mapping, use the same state for the selected object",
        "removes two repeated reads of all selected-record data from the measured "
        "Edit route",
        "hypothesis has a different product boundary from D-GOV-008",
        "changes no preview sampler, railway calculation, polynomial, "
        "approximation, cache, Coin route, or GUI processing",
        "only permitted product file is "
        "tracktemplate/adapters/freecad/transition_state.py",
        "Do not change tracktemplate/application/transition_edit.py",
        "do the exact attribution method in D-GOV-009 again on clean protected "
        "main",
        "new baseline series of 10 processes and a new attribution series "
        "of 10 processes",
        "attribution materiality rule in D-GOV-009",
        "record the 12-block sequence before product work",
        "Six blocks use the baseline first",
        "Six blocks use the candidate first",
        "Process CPU time for Edit must be lower in at least 10 of 12 paired "
        "blocks",
        "D-GOV-008 no-displacement rule to Validate, Export, cleanup, warm "
        "block values, resource metrics, and the journey remainder",
        "same test-owned instrumentation in both samples",
        "must add no work to an unmeasured boundary",
        "No risk state, treatment, severity, owner, deadline, or control "
        "effectiveness changes",
        "size of a subsequent improvement is Unknown",
        "internal result for the D-GOV-011 logical units is ASD-STE100 Issue 9 "
        "conforming",
        "Issue 9 conformance stays Unknown for other live prose",
        "reviewer who did not make the change must examine the preserved "
        "evidence",
        "reviewer must not change files",
        "project must not merge the candidate after a BLOCK review result",
        "panel must not change after the exact-state review",
        "Proceed with bounded conditions",
    ):
        _require(
            required_clause in selection_flat,
            "D-GOV-011 evidence panel drifted: " + required_clause,
        )

    for reviewed_path in (
        "reference/PERFORMANCE_SOP.md",
        "reference/TERMINOLOGY.md",
        "reference/PROJECT_PLAN.md",
        "reference/current/PHASE_EVIDENCE.md",
        "reference/current/gate-decisions.json",
    ):
        _require(
            reviewed_path in selection_panel,
            "D-GOV-011 documentation scope drifted: " + reviewed_path,
        )

    for risk_clause in (
        "PR-12 — stale or repeated direction",
        "PR-13 — repository or evidence loss",
        "PR-15 — deferred cost",
        "PR-17 — persistence or migration corruption",
        "PR-22 — authority transfer",
        "QA-R04 — no product performance budget",
        "Critical / Mitigate / Effective (current bounded scope)",
        "High / Remove / Effective (current bounded scope)",
    ):
        _require(
            risk_clause in selection_flat,
            "D-GOV-011 risk panel drifted: " + risk_clause,
        )

    selection_marker = (
        "> **D-GOV-011 — Select one canonical-record performance hypothesis**"
    )
    _require(
        selection_panel.count(selection_marker) == 1,
        "D-GOV-011 quoted owner decision is missing or duplicated",
    )
    selection_quote = selection_panel.split(selection_marker, 1)[1]
    selection_quote_flat = _semantic_text(
        "\n".join(
            line[2:] if line.startswith("> ") else ""
            for line in selection_quote.splitlines()
            if line.startswith(">")
        )
    )
    for decision_clause in (
        "accept the retained attribution result in D-GOV-009 as "
        "direction-selection evidence only",
        "exact D-GOV-010 host is "
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "median for process CPU time in the canonical measurement area is "
        "3.126380 ms",
        "first quartile is 2.9690335 ms",
        "only 0.0731425 ms higher than the attribution noise floor, which is "
        "2.895891 ms",
        "not improvement evidence",
        "not Exit 4 evidence",
        "select one performance hypothesis",
        "Read the selected canonical record one time before the write",
        "state for the stale-base and stable-identity checks",
        "During object mapping, use the same state for the selected object",
        "Keep the scan of other canonical records",
        "Keep the read after the write",
        "only permitted product file is "
        "tracktemplate/adapters/freecad/transition_state.py",
        "new ten-process baseline and ten-process attribution series",
        "attribution materiality rule in D-GOV-009",
        "Record the 12-block sequence before product work",
        "Process CPU time for Edit must be lower in at least 10 of 12 paired "
        "blocks",
        "Apply the D-GOV-008 no-displacement rule to all non-target stages",
        "Apply it to the other Edit measurement areas in D-GOV-009",
        "must add no work to an unmeasured boundary",
        "Preserve canonical state and transaction semantics",
        "Preserve one-unit Undo/Redo",
        "I authorise one subsequent product change at Level 2 in this adapter "
        "file",
        "Do not start it in this cycle",
        "Preserve D-GOV-008, D-GOV-009, D-GOV-010, the two retained negative "
        "results, and the attribution corpus",
        "makes no product change",
        "admits no performance result",
        "defines no product performance budget",
        "does not accept Exit 4",
        "Phase 6 stays at 2/5 accepted exits",
        "Exit 4 stays Pending",
        "Project status stays unknown",
        "No risk disposition changes",
        "gives no production authority",
        "gives no physical-output authority",
        "gives no project-cleared status",
        "gives no packaging, release, or tagging authority",
    ):
        _require(
            decision_clause in selection_quote_flat,
            "D-GOV-011 quoted owner decision drifted: " + decision_clause,
        )


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
        "D-P5-002 accepted Coin and the demonstrated B16 Entry/Exit product "
        "boundary. Its evidence supports all four exact exits" in plan_flat,
        "accepted Phase 5 boundary is missing",
    )
    _require(
        "D-P5-003 closed Phase 5 without opening Phase 6" in plan_flat,
        "Phase 5 closeout boundary is missing",
    )
    _require(
        "D-P6-001 later opened Phase 6 at 0/5" in plan_flat
        and "The authorised work was bounded exact validation and a "
        "private-development export seam" in plan_flat,
        "Phase 6 opening boundary is missing",
    )
    _require(
        "D-P6-002 accepts only the bounded transient-object Exit 2"
        in plan_flat
        and "advances Phase 6 to 1/5" in plan_flat
        and "D-P6-003 selects a strict completion method" in plan_flat
        and "The method can add output members" in plan_flat
        and "It cannot change or remove an existing output member" in plan_flat
        and "It keeps no separate journal" in plan_flat
        and "Its completion count can only increase" in plan_flat
        and "D-P6-003 authorises a later bounded Level 2 implementation"
        in plan_flat
        and "D-P6-004 defines the finite supported exporter fault model" in plan_flat
        and "D-P6-005 accepts only the bounded B16 Entry/Exit "
        "DXF-and-manifest route"
        in plan_flat
        and "The route has private-development status" in plan_flat
        and "The same input gives the same bytes" in plan_flat
        and "the route is failure-safe under D-P6-003 and D-P6-004"
        in plan_flat
        and "advances Phase 6 to 2/5" in plan_flat
        and "Project status remains `unknown`" in plan_flat,
        "Phase 6 Exit 2/3 acceptance or Exit 3 contract boundary is missing",
    )
    _require(
        "D-GOV-007 authorises only the exact 1.1.1 and 1.1.3 host profiles"
        in plan_flat
        and "supply Phase 6 performance evidence" in plan_flat
        and "A later decision can Admit a result only from one of these "
        "profiles" in plan_flat
        and "admits no performance result and defines no budget" in plan_flat
        and "accepts no phase exit and makes no improvement claim" in plan_flat,
        "D-GOV-007 performance-host summary drifted",
    )
    _require(
        "D-GOV-008 accepts the PR #50 FreeCAD 1.1.3 series as the comparison "
        "baseline" in plan_flat
        and "selects one performance hypothesis for the preview sampler and "
        "defines the comparison rule" in plan_flat
        and "authorises one performance optimisation at Level 2 but "
        "makes no product change" in plan_flat
        and "Exit 4 stays Pending" in plan_flat,
        "D-GOV-008 performance-direction summary drifted",
    )
    _require(
        "D-GOV-009 keeps D-GOV-008 Accepted as the authority for that first "
        "direction" in plan_flat
        and "records two later Level 2 results as retained negative "
        "evidence"
        in plan_flat
        and "stops new product work in that direction" in plan_flat
        and "authorised the bounded Level 1 baseline-attribution "
        "investigation, which is complete" in plan_flat
        and "attribution result is direction-selection evidence only"
        in plan_flat
        and "Exit 4 stays Pending" in plan_flat,
        "D-GOV-009 direction summary drifted",
    )
    _require(
        "D-GOV-010 qualifies only the exact FreeCAD 1.1.3 host profile with "
        "CPython 3.13.13 and PySide6/Qt 6.11.1" in plan_flat
        and "keeps the previously qualified profiles and their evidence"
        in plan_flat
        and "authorises this profile to supply performance evidence in a "
        "later cycle" in plan_flat
        and "Each comparison must use one profile with an exact identity"
        in plan_flat
        and "admits no performance result and does not change D-GOV-009"
        in plan_flat
        and "Exit 4 stays Pending" in plan_flat,
        "D-GOV-010 host-qualification summary drifted",
    )
    _require(
        "D-GOV-011 selects one later performance hypothesis for the read route "
        "in the canonical FreeCAD adapter" in plan_flat
        and "can remove only two repeated reads of the selected record"
        in plan_flat
        and "exact D-GOV-010 host" in plan_flat
        and "record a new same-host baseline" in plan_flat
        and "must not change the comparison rule" in plan_flat
        and "makes no product change and admits no performance result"
        in plan_flat
        and "Exit 4 stays Pending" in plan_flat,
        "D-GOV-011 canonical-record direction summary drifted",
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
        "Current — 2/5 accepted exits. The owner accepted Exit 2 under "
        "D-P6-002 on 2026-08-02. The owner accepted Exit 3 under D-P6-005 on "
        "2026-08-15. Exits 1, 4, and 5 remain Pending" in current_flat,
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
    current_performance_heading = "Performance evidence on FreeCAD 1.1.3"
    _require(
        '<a id="phase-6-performance-evidence-on-freecad-1-1-3"></a>\n\n'
        "## " + current_performance_heading in current_evidence,
        "current FreeCAD 1.1.3 performance anchor or heading is missing",
    )
    current_performance = _section(
        current_evidence,
        current_performance_heading,
    )
    current_performance_flat = " ".join(current_performance.split())
    for required_clause in (
        "f370b029bb4c1ce34987dc025a741185e233df04",
        "linux-x86_64-flatpak-freecad-1.1.3",
        "All samples use evidence schema 2",
        "full cold journey had a median of 142.912 ms",
        "full warm cycle for Validate and Export had a median of 10.417 ms",
        "correctness checks found no failure in the three cold journeys or "
        "nine warm cycles",
        "2026-08-16-phase6-freecad-1.1.3-transition-pipeline-performance.md",
        "83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a",
        "cannot use the difference between these reports to claim that "
        "TrackTemplate performance became better",
        "risk dispositions do not change",
        "admits no evidence for Exit 4",
        "defines no performance budget",
        "Phase 6 stays at 2/5 accepted exits",
        "Exit 4 stays Pending",
    ):
        _require(
            required_clause in current_performance_flat,
            "current FreeCAD 1.1.3 performance evidence drifted: "
            + required_clause,
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
        and "automatic recovery claim is therefore withdrawn" in recovery_flat
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
        and "That journal is also created anonymously" in staging_repair_flat
        and "journal is linked from its still-open descriptor"
        in staging_repair_flat
        and "`.new` remains only a reserved ambiguity detector"
        in staging_repair_flat
        and "no staging pathname or directory removal"
        in staging_repair_flat
        and "every file, identity, metadata value, and byte"
        in staging_repair_flat
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
        and "preserves and rejects that item as unclaimable"
        in staging_repair_flat
        and "matching partial DXF" in staging_repair_flat
        and "lone v1 journal, and `.new` control" in staging_repair_flat
        and "They also preserve access time" in staging_repair_flat
        and "do not claim automatic recovery" in staging_repair_flat
        and "All pre-existing transaction-control residue remains preserved"
        in staging_repair_flat
        and "remain open Exit 3 technical gaps" in staging_repair_flat
        and (
            "Phase 6 remains 1/5 with Exit 2 alone Evidenced and "
            "owner-accepted. Exit 3 remains Pending"
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
        "Authenticating or verifying a pathname does not create authority to "
        "delete it",
        "POSIX pathname deletion has no expected-inode atomic condition",
        "Cross-process recovery means safe monotonic completion, not "
        "destructive cleanup",
        "TrackTemplate never removes foreign or uncertain destination state",
        "inert foreign residue",
        "Their presence neither permits nor prevents final-set completion",
        "Content equivalence establishes compatibility for reuse or addition "
        "only",
        "An exact regular partial pair may be completed instead of rejected",
        "collision policy is therefore defined per final member",
        "No accepted consumer requires exact-partial collision failure",
        "No material owner choice remains",
        "Automatic recovery is not present",
        "Prove pre-publication descriptor abandonment and interruption after "
        "each addition",
        "Prove post-addition races and next-invocation monotonic completion",
        "Phase 6 remains 1/5",
        "Exit 3 remains Pending",
        "No risk state, treatment, or effectiveness changes",
        "tracktemplate/adapters/export/transition_dxf.py",
        "tracktemplate/application/transition_export.py",
        "must stop without publication",
        "Freeze both export contract/result IDs",
        "identical output fingerprints and `created` result signatures",
        "generic storage framework, or runtime dependency",
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
            "the strict add-only contract and later bounded Level 2 work. The "
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
            _semantic_text(
                "At accepted main source state "
                "cee78cff84618c6a5be3be99714682f5822c814f, select strict "
                "add-only, journal-free monotonic completion as the required "
                "cross-process recovery-authority contract for the bounded B16 "
                "Entry/Exit DXF-and-manifest pair. A later bounded Level 2 "
                "tranche is authorised to recompute the exact expected pair. "
                "It may create unpublished payloads only in anonymous "
                "creation-bound descriptors. It may abandon unpublished work "
                "only by closing those descriptors."
            ),
            _semantic_text(
                "It may inspect existing finals without acquiring mutation "
                "authority. It may publish only by adding an absent final "
                "pathname without overwrite. The first successful final link "
                "permanently ends rollback. No published final may be unlinked, "
                "renamed, rewritten, truncated or replaced. Authenticating or "
                "verifying a pathname does not grant deletion authority. POSIX "
                "pathname deletion has no expected-inode atomic condition."
            ),
            _semantic_text(
                "After any post-publication failure, all published finals are "
                "preserved, including any exact partial or complete output "
                "pair. A later invocation may add only an absent exact "
                "counterpart. Success may be reported only after independent "
                "revalidation shows that the complete final pair is exact. "
                "Mismatch, non-regular finals, symbolic links, collision, "
                "replay, substitution, inconsistency, ambiguity or unsupported "
                "primitives fail closed without further mutation. Foreign or "
                "uncertain destination state is never removed."
            ),
            _semantic_text(
                "The cleanup_complete, recoverable, destination_changed, and "
                "related diagnostics must describe the state actually retained. "
                "recoverable=True is permitted only after independently "
                "revalidating an exact zero-member, partial or complete "
                "destination with safe retry or remaining add-only authority. "
                "Ambiguity, mismatch, uncertain durability, or an unsupported "
                "primitive remains non-recoverable. Any successful addition "
                "requires destination_changed=True. Any surviving published "
                "final on a failed invocation requires cleanup_complete=False."
            ),
            _semantic_text(
                "Identical complete-pair reuse, deterministic filenames and "
                "bytes, manifest schema and contract IDs, the two-file layout, "
                "no-overwrite behaviour and reuse-identical-or-fail collision "
                "refusal remain unchanged. One exact regular partial member may "
                "now be completed rather than treated as a collision. Phase 6 "
                "remains 1/5 and Exit 3 remains Pending until implementation, "
                "focused interruption/recovery evidence and a fresh Level 3 "
                "review to admit evidence."
            ),
            _semantic_text(
                "No product code is changed by this decision. It does not mark "
                "Exit 3 or another exit Evidenced or owner-accepted. It grants "
                "no production, physical-output, project-cleared, equivalence, "
                "GUI, operator, wider-family, performance, legacy-retirement, "
                "packaging, or release authority. It changes no risk state."
            ),
            _semantic_text(
                "It does not authorise post-publication unlink, rename, rewrite, "
                "truncation, replacement, or pathname-based rollback. It does "
                "not authorise reading or deleting pre-existing controls. It "
                "does not authorise mutation of foreign or uncertain destination "
                "state. It does not authorise deletion authority from equality, "
                "metadata, or pathname verification. It does not authorise "
                "output name, byte, schema, layout, contract/result ID, or "
                "collision-policy value changes. It adds no trust service, "
                "generic storage framework, or runtime dependency."
            ),
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
        "interruption after each addition and next-invocation completion",
        "Completion occurs only after the required directory "
        "synchronisation",
        "fail-closed complete-pair preservation when synchronisation fails",
        "resolve-to-bind removal, and substitution",
        "Post-lock, initial-member, and post-addition substitution",
        "active-lock ambiguity",
        "Non-regular and byte-collision refusal",
        "observed descriptor closure during pre-publication abandonment",
        "A sentinel proves that normal publication makes no unlink, rename, "
        "replace, or rmdir call",
        "6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd861",
        "16de67625d952e9bb0c7c3f7891b30987f78d7c5878a9838999ab0909f131552",
        "7b2757bc3559013a2399df7efe6c25721288f8dad56b6cc05d93c2938c86c2b1",
        "8cff21c710de1da266d0a0c590cd90dc4edf46c37403275c146e2ffe5a9b3e9f",
        "Phase 6 transition DXF qualified FreeCAD validation passed",
        "Conditions 1 and 3 now have bounded evidence",
        "Condition 6 remains open",
        "not a decision to admit Exit 3 evidence or give owner acceptance",
        "Phase 6 remains 1/5 with only Exit 2 Evidenced and owner-accepted",
        "Exit 3 remains Pending",
        "PR-09, PR-13, PR-16, PR-22, and QA-R03 retain their existing states",
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
        "A first independent security review then returned BLOCKED for "
        "retention",
        "TransitionDxfExportError instead of the original "
        "CleanupInterruption",
        "A second independent security review confirmed those paths but "
        "returned BLOCKED for retention",
        "retained regression reproduced [True, True] against that second "
        "reviewed state",
        "preserves the original KeyboardInterrupt, SystemExit, or custom "
        "direct BaseException type and value",
        "Each descriptor enters the outer ownership map immediately after "
        "open",
        "Cleanup attempts every observed invocation-owned anonymous "
        "descriptor",
        "completion and bound-directory cleanup routers also preserve an "
        "active direct interruption",
        "A failed or uncertain close is reported as cleanup-incomplete and "
        "non-recoverable",
        "The existing chained TransitionDxfExportError contains this report",
        "Publication is marked durability-uncertain before linkat",
        "It keeps that status until the directory fsync returns",
        "unchanged, clean, and recoverable diagnostic",
        "diagnostic is changed, not clean, and recoverable",
        "No exception class, public ID, receipt, filename, output byte, "
        "schema, or collision policy changes",
        "Phase 6 transition DXF export validation passed",
        "Phase 6 transition DXF qualified FreeCAD validation passed",
        "Process-kill, os._exit, and a second interruption",
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
                "production output for the agreed bounded work"
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
        "Phase 6 Exit 3 supported-model panel to admit evidence and owner "
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
        "gap, or contradiction with D-P6-003/D-P6-004 was found",
        "No risk state, treatment, effectiveness, or disposition changes",
        "No product source, test oracle, schema, manifest, output byte, "
        "identifier, or railway behaviour changes",
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
            _semantic_text(
                EXPECTED_EXIT3_ACCEPTANCE_COVERAGE_CONTINUED
            ),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_LIMITATIONS),
            _semantic_text(EXPECTED_EXIT3_ACCEPTANCE_PRESERVATION),
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
        "No reviewer found a blocking condition",
        "Issue 9 conformance is Unknown for unchanged live prose",
        "The reviewers did not change the candidate",
        "The same reviewers also examined previous candidate states",
        "Proceed with bounded conditions",
        "TT-DOC-001 — TrackTemplate Technical Documentation Profile",
        "owner view → canonical information → proof/provenance",
        "The owner view gives no project authority",
        "normative standard for canonical technical prose in English in the "
        "defined bounded scope",
        "All new prose in this bounded scope must obey the applicable ASD-STE100 "
        "Issue 9 requirements",
        "A reviewer must use the official standard for the linguistic review",
        "claims no S1000D conformance",
        "claims no external ASD certification, endorsement, or official "
        "conformance assessment",
        "changes no phase or exit status",
        "changes no risk disposition, product source, or product behaviour",
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
            "first evidence limit",
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
    spelling_heading = (
        "TT-DOC-002 UK English spelling-directive correction panel and owner "
        "decision"
    )
    _require(
        '<a id="tt-doc-002-uk-english-spelling-correction-panel"></a>\n\n## '
        + spelling_heading
        in current_evidence,
        "TT-DOC-002 panel anchor or heading association is missing",
    )
    spelling_section = direct_section_content(
        current_evidence,
        spelling_heading,
    )
    spelling_flat = _semantic_text(
        re.sub(r"^> ?", "", spelling_section, flags=re.MULTILINE)
    )
    for required_clause in (
        "54d5d8312429ededff83084a3bc39c8756729d19",
        "ASD-STE100 Simplified Technical English, Issue 9",
        "stays the normative standard",
        "Issue 9 Rule 1.14 permits a different spelling",
        "project owner gives the UK English spelling directive",
        "changes spelling only",
        "does not change vocabulary, grammar, approved meaning, part-of-speech, "
        "technical-term, or linguistic-review requirements",
        "reference/ENGINEERING_POLICY.md stays the one canonical owner of "
        "TT-DOC-001",
        "reference/TERMINOLOGY.md stays the one project owner",
        "does not add spelling entries to that register",
        "accepted TT-DOC-001 quotation and LFE-018 do not change",
        "changes only the previous spelling rule",
        "information order does not change: owner view → canonical information "
        "→ proof/provenance",
        "American English spelling is not necessary after this correction",
        "18-unit conformance table keeps the same path set",
        "original 18-unit conformance scope does not expand",
        "internal result for these six units is ASD-STE100 Issue 9 conforming",
        "TrackTemplate UK English spelling directive",
        "Issue 9 conformance stays Unknown for live prose outside",
        "ASD-STE100 review result was PASS WITH FINDINGS",
        "candidate obeys Issue 9 with the TrackTemplate UK English spelling "
        "directive",
        "governance review result was PASS WITH FINDINGS",
        "That review examined authority and preservation",
        "No reviewer found a blocking condition",
        "The reviewers did not change the candidate",
        "The same reviewers also examined previous candidate states",
        "The finding is that Issue 9 conformance stays Unknown for live prose "
        "outside the logical units in the two tables",
        "This decision changes no phase, exit, risk, or evidence acceptance",
        "Phase 6 stays at 2/5",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays unknown",
    ):
        _require(
            required_clause in spelling_flat,
            "TT-DOC-002 evidence panel drifted: " + required_clause,
        )
    expected_spelling_scope = {
        "reference/ENGINEERING_POLICY.md": (
            "full TT-DOC-001 profile",
        ),
        "reference/PROJECT_PLAN.md": (
            "current owner view",
            "TT-DOC-002 decision row",
        ),
        "reference/current/PHASE_EVIDENCE.md": (
            "TT-DOC-002 panel",
            "current-register paragraph",
        ),
        "reference/current/gate-decisions.json": (
            "human-readable TT-DOC-002 record",
            "Exact JSON data stays outside",
        ),
        ".agents/skills/tracktemplate-documentation-review/SKILL.md": (
            "full Editing rules section",
        ),
        (
            ".agents/skills/tracktemplate-documentation-review/references/"
            "writing-checklist.md"
        ): ("full Concision and tone section",),
    }
    spelling_rows = _structured_table_rows(
        spelling_section,
        ("Path", "Full logical unit that changed"),
        "TT-DOC-002 Issue 9 conformance scope",
    )
    _require(
        set(spelling_rows) == set(expected_spelling_scope),
        "TT-DOC-002 conformance-scope path set drifted",
    )
    for reviewed_path, scope_fragments in expected_spelling_scope.items():
        scope = spelling_rows[reviewed_path][1]
        _require(
            all(fragment in scope for fragment in scope_fragments),
            "TT-DOC-002 conformance scope changed: " + reviewed_path,
        )
    _require(
        "[official Issue 9 standard](https://www.asd-ste100.org/assets/files/"
        "ASD-STE100_ISSUE9.pdf)" in spelling_section,
        "TT-DOC-002 conformance review lost its official Issue 9 source",
    )
    compatibility_heading = (
        "FreeCAD 1.1.3 compatibility requalification panel and owner decision"
    )
    _require(
        '<a id="freecad-1-1-3-compatibility-requalification-panel"></a>\n\n'
        "## " + compatibility_heading in current_evidence,
        "D-GOV-006 panel anchor or heading association is missing",
    )
    compatibility_section = _section(
        current_evidence,
        compatibility_heading,
    )
    compatibility_flat = _semantic_text(
        re.sub(r"^> ?", "", compatibility_section, flags=re.MULTILINE)
    )
    for required_clause in (
        "724a3b79ab5b71025041e84eac3501a457b3fb76",
        "Phase 6 stays at 2/5",
        "exact 1.1.1 and 1.1.3 host profiles",
        "FreeCAD 1.1.2 and all other releases are not qualified",
        "linux-x86_64-flatpak-freecad-1.1.3",
        "145529fe741292ff0b3977a01195bf0247425794",
        "CPython 3.13.14",
        "PySide6/Qt 6.10.3",
        "OpenCASCADE 7.8.1",
        "SIM Coin 4.0.8",
        "Expected host-version difference with no TrackTemplate contract "
        "effect",
        "benchmark-output/validation-pipeline/20260815T195204447910Z/",
        "corrected standalone profile with 187 parsed files and 59 of 59 "
        "results",
        "benchmark-output/validation-pipeline/20260815T184826613031Z/",
        "1.1.3 transition host and GUI profile",
        "call_aQfBr45aDcefyiKCYr3AToMc",
        "the required argument for option '--pass' is missing",
        "result for the invocation without a --pass argument is "
        "fixture-or-harness-defect",
        "contract command --pass --require-qualified was not the command "
        "with exit code 1",
        "58bd07e3d79c706cdbb8c3cd41eb7cf2090c2d12437c197a05eb5a9945aeae69",
        "security issues in FCStd and file handling",
        "Each FreeCAD release before 1.1.3 has one or more of these issues",
        "1.1.1 functional compatibility decision",
        "not a security endorsement",
        "panel found no TrackTemplate compatibility defect",
        "cannot examine a packaged Workbench or Addon",
        "Timing differences are not defects or Phase 6 Exit 4 evidence",
        "changes no tracktemplate product module",
        "Phase 10 package.xml intent stays at exact 1.1.1",
        "PR-17 — persistence or migration corruption",
        "Continue with bounded conditions",
        "D-GOV-006 — Qualify the exact FreeCAD 1.1.3 host profile",
        "changes compatibility authority only",
        "Output stays private-development",
        "Project status stays unknown",
    ):
        _require(
            required_clause in compatibility_flat,
            "D-GOV-006 evidence panel drifted: " + required_clause,
        )
    compatibility_qualification = _semantic_text(
        direct_section_content(
            compatibility_section,
            "Qualification evidence",
            level=3,
        )
    )
    for required_clause in (
        "initial invocation used flatpak run --command=FreeCADCmd",
        "--pass option had no argument",
        "the required argument for option '--pass' is missing",
        "call_aQfBr45aDcefyiKCYr3AToMc",
        "result for the invocation without a --pass argument is "
        "fixture-or-harness-defect",
        "contract command --pass --require-qualified was not the command "
        "with exit code 1",
        "invocation with exit code 1 did not produce a runtime record",
        "Other runtime checks show that the installed host is the exact "
        "1.1.3 host profile",
        "After that, an invocation of the contract command qualified 1.1.3",
        "diagnostic command --pass=--require-qualified gave the same result "
        "as the contract command",
        "does not replace the contract command",
        "58bd07e3d79c706cdbb8c3cd41eb7cf2090c2d12437c197a05eb5a9945aeae69",
    ):
        _require(
            required_clause in compatibility_qualification,
            "D-GOV-006 qualification provenance drifted: "
            + required_clause,
        )
    compatibility_host_review = _semantic_text(
        direct_section_content(
            compatibility_section,
            "Official host review",
            level=3,
        )
    )
    for required_clause in (
        "FreeCAD 1.1.3 release",
        "security issues in FCStd and file handling",
        "Each FreeCAD release before 1.1.3 has one or more of these issues",
        "recommends that all users install 1.1.3",
        "1.1.1 functional compatibility decision",
        "not a security endorsement",
    ):
        _require(
            required_clause in compatibility_host_review,
            "D-GOV-006 official host security boundary drifted: "
            + required_clause,
        )
    compatibility_issue9 = direct_section_content(
        compatibility_section,
        "Issue 9 review",
        level=3,
    )
    for reviewed_path, scope_fragments in {
        "reference/TERMINOLOGY.md": (
            "three Host compatibility rows",
            "Qualify and Requalify technical-verb rows",
        ),
        "reference/PROJECT_PLAN.md": (
            "current owner view",
            "D-GOV-006 summary",
            "D-GOV-006 decision row",
            "compatibility authority link",
        ),
        "reference/VALIDATION.md": (
            "full FreeCAD document validation unit",
            "Phase 1 runtime and legacy ingress compatibility unit",
        ),
        "reference/contracts/phase1-compatibility.json": (
            "human-readable bounded-scope strings",
            "security limit",
            "1.1.3 evidence strings",
            "support rule",
            "evidence-gap string",
        ),
        "reference/current/PHASE_EVIDENCE.md": (
            "full D-GOV-006 panel",
            "D-GOV-006 carried-control sentences",
        ),
        "reference/current/gate-decisions.json": (
            "human-readable D-GOV-006 record",
            "Exact JSON data stays outside",
        ),
    }.items():
        _require(
            reviewed_path in compatibility_issue9
            and all(
                fragment in compatibility_issue9
                for fragment in scope_fragments
            ),
            "D-GOV-006 Issue 9 review scope drifted: " + reviewed_path,
        )
    compatibility_issue9_flat = _semantic_text(compatibility_issue9)
    for required_clause in (
        "official Issue 9 standard",
        "TrackTemplate UK English spelling directive",
        "Before the final reviews, ASD-STE100 Issue 9 conformance was not "
        "verified",
        "these six corrected units",
        "final documentation review must examine this exact state",
        "pull request and completion report must record the result",
        "Unknown for live prose outside the TT-DOC-001, TT-DOC-002, and "
        "D-GOV-006 tables",
        "Frozen history also stays outside this assessment",
    ):
        _require(
            required_clause in compatibility_issue9_flat,
            "D-GOV-006 Issue 9 result or limitation drifted: "
            + required_clause,
        )
    compatibility_review = _semantic_text(
        direct_section_content(
            compatibility_section,
            "Review state",
            level=3,
        )
    )
    for required_clause in (
        "initial compatibility review examined FreeCAD and the API",
        "Its result was BLOCKED",
        "reviewer found no host-compatibility defect",
        "command record was not correct",
        "security limitation and Issue 9 review were missing",
        "initial quality review examined authority and preservation",
        "Its result was PASS WITH FINDINGS",
        "found no blocking condition in the supported bounded scope",
        "initial quality reviewer did not have the session call",
        "reviewers did not change the candidate",
        "two reviewers must examine the final exact state",
        "two final reviews must find no blocking condition before merge",
        "pull request and completion report must record the two final results",
        "panel must not change after the reviews",
    ):
        _require(
            required_clause in compatibility_review,
            "D-GOV-006 independent review state drifted: "
            + required_clause,
        )
    compatibility_decision_paragraphs = _blockquote_paragraphs(
        compatibility_section
    )
    _require(
        any(
            "This decision changes compatibility authority only" in paragraph
            for paragraph in compatibility_decision_paragraphs
        )
        and any(
            "Phase 6 stays at 2/5" in paragraph
            and "Exits 1, 4, and 5 stay Pending" in paragraph
            for paragraph in compatibility_decision_paragraphs
        ),
        "D-GOV-006 owner decision changed phase or exit authority",
    )
    performance_host_heading = (
        "Panel and owner decision about hosts for Phase 6 performance evidence"
    )
    _require(
        '<a id="phase-6-performance-evidence-host-boundary-panel"></a>\n\n'
        "## " + performance_host_heading in current_evidence,
        "D-GOV-007 panel anchor or heading association is missing",
    )
    performance_host_section = _section(
        current_evidence,
        performance_host_heading,
    )
    performance_host_flat = _semantic_text(
        re.sub(r"^> ?", "", performance_host_section, flags=re.MULTILINE)
    )
    performance_rule_flat = _semantic_text(
        performance_host_section.split("### Documentation conformance", 1)[0]
    )
    for required_clause in (
        "authorises only these two exact host profiles to supply candidate "
        "evidence for Phase 6 performance",
        "later decision can admit a performance result only if it comes from "
        "one of these exact host profiles",
        "project qualifies a subsequent host profile, this does not authorise "
        "performance evidence from that profile",
    ):
        _require(
            required_clause in performance_rule_flat,
            "D-GOV-007 evidence panel drifted: " + required_clause,
        )
    for required_clause in (
        "3f20de704a060ab37478c34b3a7cb3586a9b2220",
        "D-GOV-006 qualifies the exact "
        "linux-x86_64-flatpak-freecad-1.1.3 host profile",
        "Phase 6 stays at 2/5 accepted exits",
        "Exit 4 stays Pending",
        "previous validator rejected a result unless it recorded FreeCAD 1.1.1",
        "previous validator then rejected that result",
        "20260815T214842401485Z-profile/sample-01.log",
        "D-GOV-007 does not admit this test result as Exit 4 evidence",
        "linux-x86_64-flatpak-freecad-1.1.1",
        "linux-x86_64-flatpak-freecad-1.1.3",
        "authorises only these two exact host profiles to supply candidate "
        "evidence for Phase 6 performance",
        "later decision can admit a performance result only if it comes from "
        "one of these exact host profiles",
        "Each new schema-2 result has exact host identity",
        "records the ID and FreeCAD version of its exact host profile",
        "rejects a result that names a different host profile or FreeCAD "
        "version",
        "rejects a result set that contains two host profiles",
        "project qualifies a subsequent host profile, this does not "
        "authorise performance evidence from that profile",
        "compare TrackTemplate performance, use one exact host profile",
        "independently shows the effect of the host profile and the "
        "TrackTemplate effect",
        "The different results do not show that TrackTemplate performance "
        "became better",
        "1.1.1 performance report does not have a host_profile_id field",
        "qualified-runtime contract hash",
        "data identify the exact host profile for FreeCAD 1.1.1",
        "D-GOV-007 keeps this report as 1.1.1 evidence",
        "1.1.1 report is a schema-1 report",
        "New samples and performance records use schema 2",
        "schema_version value identifies the structure of the evidence record",
        "profile_id value is phase6-transition-edit-validate-export-profile-v1",
        "identifies the measurement method and not the record schema",
        "standalone validator has the two exact ID/version mappings",
        "rejects schema 1 and FreeCAD 1.1.2",
        "rejects a result unless its ID/version pair is one of the two mappings",
        "rejects a host_profile_id value that is not a string",
        "rejects an exact-geometry receipt that records a different FreeCAD "
        "version",
        "does not measure performance",
        "does not admit the test result",
        "defines no value for a performance budget",
        "changes the schema for internal performance-evidence records from 1 "
        "to 2",
        "changes no TrackTemplate product behaviour, product output, product "
        "schema",
        "PR-15 — deferred cost",
        "host difference cannot be evidence of a TrackTemplate or "
        "deferred-cost change",
        "QA-R04 — no value for a performance budget",
        "decision defines no budget and admits no performance result",
        "Continue with bounded conditions",
        "D-GOV-007 — Authorise the exact 1.1.3 profile for Phase 6 "
        "performance evidence",
        "does not accept Exit 4",
        "separate Level 3 decision from the owner is necessary",
        "gives no production, physical-output, project-cleared, packaging, "
        "release, or tagging authority",
        "Exits 1 and 5 stay Pending",
        "Output stays private-development",
        "Project status stays unknown",
    ):
        _require(
            required_clause in performance_host_flat,
            "D-GOV-007 evidence panel drifted: " + required_clause,
        )
    performance_decision_flat = " ".join(
        _blockquote_paragraphs(performance_host_section)
    )
    for required_clause in (
        "authorises the exact linux-x86_64-flatpak-freecad-1.1.1 profile and "
        "the exact linux-x86_64-flatpak-freecad-1.1.3 profile to supply "
        "candidate evidence",
        "later decision can admit a performance result only if it comes from "
        "one of these exact host profiles",
        "Each new schema-2 result must have exact host identity",
        "1.1.1 report from 2026-08-02 is a schema-1 report",
        "project qualifies a subsequent host profile, this does not authorise "
        "performance evidence from that profile",
        "separate Level 3 decision from the owner is necessary",
        "changes the schema for internal performance-evidence records to "
        "version 2",
        "does not accept Exit 4",
        "product output, product schema",
        "gives no production, physical-output, project-cleared, packaging, "
        "release, or tagging authority",
    ):
        _require(
            required_clause in performance_decision_flat,
            "D-GOV-007 quoted owner decision drifted: " + required_clause,
        )
    performance_host_issue9 = direct_section_content(
        performance_host_section,
        "Documentation conformance",
        level=3,
    )
    expected_performance_scope = {
        "reference/PERFORMANCE_SOP.md": (
            "full section with the heading `Hosts for Phase 6 performance "
            "evidence`",
        ),
        "reference/VALIDATION.md": (
            "full compatibility unit for Phase 1 runtime and legacy ingress",
        ),
        "reference/PROJECT_PLAN.md": (
            "current owner view",
            "D-GOV-007 phase summary",
            "D-GOV-007 decision row",
        ),
        "reference/current/PHASE_EVIDENCE.md": (
            "full D-GOV-007 panel",
            "changed Exit 4 disposition",
            "D-GOV-007 carried-control sentences",
        ),
        "reference/current/gate-decisions.json": (
            "human-readable D-GOV-007 record",
            "Exact JSON data is not part of the linguistic assessment",
        ),
    }
    for reviewed_path, scope_fragments in expected_performance_scope.items():
        _require(
            reviewed_path in performance_host_issue9
            and all(
                fragment in performance_host_issue9
                for fragment in scope_fragments
            ),
            "D-GOV-007 Issue 9 review scope drifted: " + reviewed_path,
        )
    performance_host_issue9_flat = _semantic_text(performance_host_issue9)
    for required_clause in (
        "official Issue 9 standard",
        "TrackTemplate UK English spelling directive",
        "Before the conformance review, no reviewer verified ASD-STE100 Issue 9 "
        "conformance for these five changed units",
        "conformance review must examine this exact candidate",
        "pull request and completion report must record the result",
        "machine values are not part of the linguistic review",
        "Issue 9 conformance stays Unknown for other live prose",
    ):
        _require(
            required_clause in performance_host_issue9_flat,
            "D-GOV-007 Issue 9 result or limitation drifted: "
            + required_clause,
        )
    performance_review_flat = _semantic_text(
        direct_section_content(
            performance_host_section,
            "Review state",
            level=3,
        )
    )
    for required_clause in (
        "reviewer who did not make this change must examine the exact "
        "candidate",
        "reviewer must not change files",
        "host rule for performance, the decision to admit evidence, authority, "
        "preservation, and the Issue 9 assessment",
        "must find no blocking condition before the project merges the "
        "candidate",
        "pull request and completion report record the result",
        "panel must not change after the review",
    ):
        _require(
            required_clause in performance_review_flat,
            "D-GOV-007 independent review gate drifted: " + required_clause,
        )
    _validate_performance_host_sources(
        _read(PERFORMANCE_SOP_PATH),
        _read(VALIDATION_PATH),
    )
    current_register_flat = _semantic_text(
        direct_section_content(current_evidence, "Carried controls and exclusions")
    )
    for required_clause in (
        "TT-DOC-001",
        "TT-DOC-002",
        "TT-DOC-002 corrects only the spelling directive",
        "D-GOV-006 qualifies only the exact FreeCAD 1.1.3 profile",
        "D-GOV-007 changes only the host rule and the directly dependent "
        "schema for internal performance-evidence records",
        "admits no performance result and defines no budget",
        "does not claim that performance became better",
        "does not accept Exit 4",
        "D-GOV-010 qualifies only the profile with ID "
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
        "two profiles that the project qualified before D-GOV-010 stay "
        "qualified, and their evidence does not change",
        "authorises its profile to supply candidate evidence for performance "
        "in a subsequent cycle",
        "Each comparison must use one profile with an exact identity",
        "does not change D-GOV-009 or Exit 4",
        "D-GOV-011 accepts the D-GOV-009 attribution result as evidence for "
        "direction selection only",
        "selects one subsequent hypothesis at Level 2 in "
        "tracktemplate/adapters/freecad/transition_state.py",
        "keeps one live read of the selected record before the write",
        "removes only two repeated reads",
        "defines the new same-host baseline and comparison rule",
        "makes no product change. It admits no performance result, defines no "
        "budget, and does not accept Exit 4",
    ):
        _require(
            required_clause in current_register_flat,
            "current-register TT-DOC-002 wording drifted: " + required_clause,
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
        "Phase 6 Exits 2 and 3 panel to admit evidence and owner decision"
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
            _semantic_text(EXPECTED_EXIT2_PANEL_AUTHORITY),
            _semantic_text(EXPECTED_EXIT2_PANEL_EXCLUSIONS_ONE),
            _semantic_text(EXPECTED_EXIT2_PANEL_EXCLUSIONS_TWO),
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
        and current_document["updated_on"] == "2026-08-31",
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
            record["status"] == "Accepted"
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

    for decision_id, expected in EXPECTED_PHASE6_DECISIONS.items():
        (
            expected_date,
            expected_decision,
            expected_panel_record,
            expected_authority_sha256,
            expected_exclusions_sha256,
        ) = expected
        record = phase6_by_id[decision_id]
        _require(
            record["decided_on"] == expected_date,
            decision_id + " decision date drifted",
        )
        _require(
            record["decision"] == expected_decision,
            decision_id + " decision wording drifted",
        )
        _require(
            record["evidence"] == expected_panel_record
            and record["panel_record"] == expected_panel_record,
            decision_id + " evidence or panel routing drifted",
        )
        for field in ("authority", "exclusions"):
            value = record[field]
            _require(
                isinstance(value, str) and bool(value.strip()),
                decision_id + " lacks " + field,
            )
            expected_digest = (
                expected_authority_sha256
                if field == "authority"
                else expected_exclusions_sha256
            )
            actual_digest = hashlib.sha256(
                value.encode("utf-8")
            ).hexdigest()
            _require(
                actual_digest == expected_digest,
                decision_id + " " + field + " digest drifted",
            )

    _require(
        EXPECTED_STE_LIFECYCLE_PLAN_ROW in _section(plan, "Owner decisions"),
        "project-plan D-GOV-015 decision row drifted",
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
        and "owns the Phase 5 decisions below" in decision_flat,
        "the frozen Phase 5 decision-register ownership is missing",
    )
    _require(
        "decision register" in decision_flat
        and "owns Phase 6" in decision_flat
        and "owns current governance decisions for more than 1 phase"
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
            "implementation. This governance branch was created from accepted "
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
            "Vision supplies direction. It does not define a bounded scope or "
            "give task authority. D-GOV-004 continues to own literal "
            "continuation invocation and its one-cycle Level 1/2 execution "
            "limit. This decision changes no Phase 6 criterion or exit status. "
            "It implements no shared renderer, ViewProvider, exact-geometry "
            "expansion, output, persistence, or railway calculation. It "
            "authorises no Layout Editor feature. It accepts no pull request, "
            "migration completion, output clearance, package, release, or "
            "phase exit."
        ),
        _semantic_text("Draft PR #31 remains separate and unaccepted."),
    ]
    _require(
        quoted == expected_quoted,
        "current evidence D-GOV-005 authority block drifted or gained a "
        "competing record",
    )


def _validate_ste_lifecycle_panel(current_evidence: str) -> None:
    """Bind the D-GOV-015 panel to its exact bounded lifecycle."""
    anchor = '<a id="d-gov-015-simplified-ste-lifecycle"></a>'
    _require(
        current_evidence.count(anchor) == 1,
        "current evidence lost or duplicated the D-GOV-015 panel anchor",
    )
    section = _section(
        current_evidence,
        "D-GOV-015 simplified STE lifecycle",
    )
    owner_view = direct_section_content(
        section,
        "Owner view",
        level=3,
    )
    rows = _structured_table_rows(
        owner_view,
        ("Field", "Current result"),
        "D-GOV-015 owner view",
    )
    expected_rows = {
        "Current state": (
            "The interrupted three-path implementation at recovery checkpoint "
            "`ac5a7d7ae8c6bf72069b802ebe9e929faf27e789` is bounded "
            "implementation evidence. Its authorised protected-main baseline is "
            "`54176f5ae0fea1f72743f856fd9251a53d7e1dbf`. The checkpoint is not "
            "accepted project state."
        ),
        "What changed": (
            "D-GOV-015 adopts one lifecycle: author → freeze scope → one "
            "Documentation Review → optional exact reviewed correction once → "
            "one final deterministic validation → complete or owner stop. The "
            "existing Issue 9 retrieval and cache remain."
        ),
        "What now works": (
            "Git derives whole-document first review and later "
            "changed-complete-unit scope. One review returns one of three "
            "complete verdicts. Exact corrections bind to frozen preimages. "
            "Durable state records document identities. Final validation binds "
            "source, scope, receipt, state, and final bytes and detects "
            "unreviewed mutation."
        ),
        "Limitations/findings": (
            "The tool cannot authenticate a reviewer. Actual role separation "
            "remains necessary. One-shot ignored evidence requires independent "
            "preservation. Final validation does not judge linguistic "
            "conformance. The current backup condition must be proved before "
            "Documentation Review."
        ),
        "Owner decision": (
            "Accept D-GOV-015. Complete only the bounded lifecycle, canonical "
            "and skill alignment, Level 3 record, one review, and optional "
            "exact correction once. Then complete final deterministic "
            "validation, non-linguistic publication review, and one draft pull "
            "request if exact-green. Do not merge."
        ),
        "Next action": (
            "Complete fail-closed development validation. Freeze and preserve "
            "one exact candidate and its scope. Run the one Documentation "
            "Review. Preserve each resulting review file. Run the one final "
            "deterministic validation. Get the required non-linguistic "
            "independent review, and publish one draft pull request only if "
            "exact-green."
        ),
    }
    _require(
        set(rows) == set(expected_rows),
        "D-GOV-015 owner-view fields drifted",
    )
    for label, expected in expected_rows.items():
        _require(
            rows[label] == [label, _semantic_markdown(expected)],
            "D-GOV-015 owner-view row drifted: " + label,
        )

    participants = direct_section_content(
        section,
        "Participants and reviewed evidence",
        level=3,
    )
    participant_rows = _structured_table_rows(
        participants,
        ("Participant", "Role and independence"),
        "D-GOV-015 participants",
    )
    expected_participants = {
        "owner:tracktemplate-project-owner": (
            "Project owner, panel chair, and decision owner. The owner supplied "
            "the exact lifecycle, baseline, checkpoint, exclusions, completion "
            "route, draft-pull-request authority, and no-merge limit."
        ),
        "agent:openai-codex-primary": (
            "Change owner and presenter. This agent recovered, corrected, "
            "aligned, and validated the candidate. It cannot independently "
            "accept its own implementation or linguistic conformance."
        ),
        "agent:aquinas-lifecycle-risk-panel": (
            "QA/risk reviewer. This delegated reviewer examined the checkpoint, "
            "current implementation, tests, recovery controls, and alignment "
            "without mutation or linguistic Documentation Review. The reviewer "
            "is independent of implementation changes but shares the agent team "
            "and workspace. It is not an external organisational review."
        ),
    }
    _require(
        set(participant_rows) == set(expected_participants),
        "D-GOV-015 panel participants drifted",
    )
    for participant, expected in expected_participants.items():
        _require(
            participant_rows[participant]
            == [participant, _semantic_markdown(expected)],
            "D-GOV-015 participant role drifted: " + participant,
        )
    reviewed_evidence = _require_paragraph(
        participants,
        (
            "The panel reviewed the exact protected-main baseline and recovery "
            "checkpoint, the three-path lookup implementation, lifecycle fixture, "
            "and empty document-level state. It also reviewed the Engineering "
            "Policy, validation owner, recovery policy, current risks, source and "
            "retrieval procedure, and the development-validation results in this "
            "panel."
        ),
        "D-GOV-015 panel lost its linked evidence-reviewed record",
    )
    _require_links(
        reviewed_evidence,
        (
            ("lookup implementation", "../../tools/ste100_lookup.py"),
            ("lifecycle fixture", "../../tests/validate_ste100_retrieval.py"),
            ("empty document-level state", "../ste-review-state.json"),
            (
                "Engineering Policy",
                "../ENGINEERING_POLICY.md#true-gates-and-safetyrisk-panels",
            ),
            (
                "validation owner",
                "../VALIDATION.md#validation-of-the-retrieval-contract",
            ),
            ("recovery policy", "../RECOVERY_AND_BACKUP.md"),
            ("current risks", "risks.json"),
            (
                "source and retrieval procedure",
                "../external/asd-ste100/README.md",
            ),
        ),
        "D-GOV-015 panel evidence links drifted",
    )

    dissent = direct_section_content(
        section,
        "Dissent, unknowns, and exceptions",
        level=3,
    )
    _require_paragraph(
        dissent,
        (
            "The QA/risk reviewer recorded no dissent from the bounded "
            "recommendation. The accepted backup device is not currently "
            "mounted, so independent preservation for this gate remains unknown. "
            "The tool also cannot authenticate the declared reviewer identity. "
            "The same-team and shared-workspace review is an independence "
            "limitation, not an external organisational review. There is no "
            "exception to the single-review lifecycle, preservation condition, "
            "owner-stop rule, Phase 6 limit, or hard exclusions."
        ),
        "D-GOV-015 panel lost dissent, unknowns, or exceptions",
    )

    conditions = direct_section_content(
        section,
        "Bounded conditions and accountable owners",
        level=3,
    )
    condition_rows = _structured_table_rows(
        conditions,
        ("Condition", "Accountable owner", "Deadline and current result"),
        "D-GOV-015 bounded conditions",
    )
    expected_conditions = {
        "Harden Git identity and add the fail-closed source, scope, receipt, "
        "state, correction, and mutation proofs.": (
            "agent:openai-codex-primary",
            "Before candidate freeze — completed, focused and full development "
            "validation must remain green on the exact candidate.",
        ),
        "Commit and push the exact candidate.": (
            "agent:openai-codex-primary",
            "Before Documentation Review — pending candidate freeze.",
        ),
        "Make the accepted independent backup device available.": (
            "owner:tracktemplate-project-owner",
            "Before independent scope preservation and Documentation Review — "
            "pending.",
        ),
        "Preserve the frozen scope and then each review result, receipt, and "
        "accepted-state proposal on the accepted device.": (
            "agent:openai-codex-primary",
            "Preserve each review file before its next dependent operation — "
            "pending.",
        ),
        "Return the sole linguistic verdict with actual role separation and all "
        "exact wording, if applicable.": (
            "Independent Documentation Reviewer",
            "Once, after scope preservation and before any correction — pending.",
        ),
        "Apply only exact approved corrections once, run one final deterministic "
        "validation, and return any failure to the owner.": (
            "agent:openai-codex-primary",
            "After the sole Documentation Review and before publication review — "
            "pending.",
        ),
    }
    _require(
        set(condition_rows) == set(expected_conditions),
        "D-GOV-015 bounded conditions or accountable ownership drifted",
    )
    for condition, (owner, deadline) in expected_conditions.items():
        _require(
            condition_rows[condition]
            == [condition, _semantic_markdown(owner), _semantic_markdown(deadline)],
            "D-GOV-015 condition owner or deadline drifted: " + condition,
        )

    panel = _semantic_text(section)
    for fragment in (
        "exact 54176f5ae0fea1f72743f856fd9251a53d7e1dbf to "
        "ac5a7d7ae8c6bf72069b802ebe9e929faf27e789 delta changes only "
        "tools/ste100_lookup.py, tests/validate_ste100_retrieval.py, and "
        "reference/ste-review-state.json",
        "keeps 66 existing functions unchanged",
        "removes 17 functions for the retired author-worklist design",
        "adds 44 lifecycle-specific functions",
        "1,645 additions and 1,205 deletions, for net growth of 440 lines",
        "No generic workflow state, grants, uses, completions, telemetry, or "
        "ontology machinery remains",
        "tracked Python parsing passed for 189 files",
        "focused ASD-STE100 retrieval validator passed",
        "CI standalone profile passed all 60 validators",
        "This evidence preceded alignment and trust-control hardening",
        "The negative tests prove rejection of self-review, tampered source, "
        "scope, receipt, state, and final bytes. They also reject invalid "
        "corrections, a hostile Git environment, fsmonitor, text conversion, "
        "replacement objects, and unreviewed final mutation",
        "candidate still requires the preservation conditions before review",
        "After alignment and trust-control hardening, tracked Python parsing "
        "passed for 189 files",
        "governance mutation validator rejected all 328 mutations",
        "CI standalone profile passed all 60 validators",
        "No FreeCAD or GUI validation applies",
        "One independent Documentation Reviewer owns the sole linguistic verdict",
        "separate final review is non-linguistic",
        "Proceed with bounded conditions",
        "Any preservation, reviewer-separation, source, scope, receipt, state, "
        "semantic, Git-identity, or final-byte failure returns to the owner",
        "Do not run a second Documentation Review",
        "On 2026-08-31, owner:tracktemplate-project-owner accepts the exact "
        "authority and exclusions",
        "earlier author-side assurance section remains historical evidence of "
        "the retired route",
        "Phase 6 stays at 2/5",
        "Exits 1, 4, and 5 stay Pending",
        "Project status stays unknown",
        "No risk disposition changes",
        "no authority to resume D-GOV-014 or modify aa6c506",
        "no authority for a second documentation-assurance framework or a "
        "second Documentation Review",
    ):
        _require(
            _semantic_text(fragment) in panel,
            "D-GOV-015 evidence panel drifted: " + fragment,
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
    _validate_performance_direction_sources(
        _read(PERFORMANCE_SOP_PATH),
        _read(TERMINOLOGY_PATH),
        current_evidence,
    )
    _validate_risks(plan)
    _validate_decisions(plan)
    _validate_ste_lifecycle_panel(current_evidence)
    _validate_product_direction(current_evidence)
    _validate_fixed_paths()
    _validate_ci_workflow()
    print("Project dashboard and current-record validation passed")


if __name__ == "__main__":
    main()
