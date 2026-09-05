#!/usr/bin/env python3
"""Validate the ASD-STE100 retrieval, assurance, and routing contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "ste100_lookup.py"
ENGINEERING = ROOT / "reference" / "ENGINEERING_POLICY.md"
TERMINOLOGY = ROOT / "reference" / "TERMINOLOGY.md"
VALIDATION = ROOT / "reference" / "VALIDATION.md"
WORKFLOWS = ROOT / "reference" / "AGENT_WORKFLOWS.md"
LEARNING = ROOT / "reference" / "LEARNING_FROM_EXPERIENCE.md"
PROVENANCE = ROOT / "reference" / "PROVENANCE.md"
SOURCE_DIR = ROOT / "reference" / "external" / "asd-ste100"
SOURCE_MANIFEST = SOURCE_DIR / "source-manifest.json"
RETRIEVAL_INDEX = SOURCE_DIR / "retrieval-index.json"
SOURCE_README = SOURCE_DIR / "README.md"
AGENTS = ROOT / "AGENTS.md"
GITIGNORE = ROOT / ".gitignore"
SKILLS = ROOT / ".agents" / "skills"
SKILL_NAMES = (
    "tracktemplate-documentation-review",
    "tracktemplate-documentation-alignment",
    "tracktemplate-change-validation",
    "tracktemplate-quality-review",
    "tracktemplate-technical-author-lead",
)
SOURCE_ROUTING_SKILL_NAMES = tuple(
    name for name in SKILL_NAMES if name != "tracktemplate-quality-review"
)
EXPECTED_SOURCE_SHA256 = (
    "d1f4ea9e7cd6e46b47aa9057209f99e78c0e9cfc4e27a5b07895b05c1a166431"
)
EXPECTED_EXTRACTION_INDEX_SHA256 = (
    "0f1d34bff793a2241b1e5942982908b629145c06f5d6c01474ba5afe2ce1e76f"
)
EXPECTED_SOURCE_SIZE = 3_316_157
LFE_001_TO_018_ROWS_SHA256 = (
    "09a6449f8a202ffddf2adda3d35e14cecaaa69fa83260c119bbe460e6185512e"
)
SENTINEL = "ASD-STE100 retrieval validation passed"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: pathlib.Path) -> str:
    require(path.is_file(), "missing required file: {}".format(path))
    return path.read_text(encoding="utf-8")


def load_json(path: pathlib.Path) -> dict[str, object]:
    value = json.loads(read(path))
    require(isinstance(value, dict), "{} must contain an object".format(path))
    return value


def semantic_text(value: str) -> str:
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    value = re.sub(r"[`*_>#|]", " ", value)
    return " ".join(value.casefold().split())


def load_tool():
    spec = importlib.util.spec_from_file_location("ste100_lookup", TOOL_PATH)
    require(spec is not None and spec.loader is not None, "cannot load STE tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STE = load_tool()


def expect_ste_error(code: str, action) -> None:
    try:
        action()
    except STE.Ste100Error as error:
        require(
            error.code == code,
            "expected error {!r}, got {!r}".format(code, error.code),
        )
    else:
        raise AssertionError("expected STE error: " + code)


def validate_policy_text(text: str) -> None:
    validate_no_positive_assurance_claim(text)
    section = semantic_text(text)
    for fragment in (
        "ste lookup only makes retrieval faster",
        "does not define or limit the applicable rule set",
        "all applicable writing rules and the controlled vocabulary are mandatory",
        "must not claim conformance because of a lookup result",
        "must not claim conformance because the deterministic pre-check has no "
        "finding",
        "pass result from automatic validation also does not show conformance",
        "ste lookup selects the source text that an agent reads for a task",
        "does not select the applicable writing rules",
    ):
        require(fragment in section, "application profile lacks: " + fragment)
    require(
        "tracktemplate uses uk english" in section,
        "the UK English directive was lost",
    )
    require(
        "does not change the applicable issue 9 vocabulary or grammar rules" in section,
        "the spelling-only boundary was weakened",
    )


def validate_workflow_text(text: str) -> None:
    validate_no_positive_assurance_claim(text)
    value = semantic_text(text)
    ordered = (
        "for new or materially changed canonical technical prose, use "
        "tracktemplate-technical-author-lead automatically",
        "identify the document need",
        "identify the document class",
        "make a plan for the purpose",
        "get technical meaning from the applicable canonical subject owner",
        "read the technical-term register. read the applicable documentation "
        "policy",
        "before you write the affected logical units, use targeted retrieval",
        "write all candidate documents once",
        "connect the checks to the candidate bytes",
        "freeze one exact candidate",
        "use the document identity and supplied git baseline to identify "
        "the complete logical units that changed",
        "exclude unchanged legacy prose",
        "give the complete scope of the frozen review to one independent "
        "documentation reviewer",
        "record one complete accept",
        "approved with exact corrections",
        "or blocked verdict",
        "apply the set of exact corrections once against verified preimages",
        "record the locked state for the final content",
        "preserve the initial verdict and receipt",
        "do final deterministic validation",
        "finish the bounded d-gov-018 authoring and review lifecycle",
        "do not start another documentation, quality, publication, wording, or "
        "semantic review",
        "make the accepted content the controlled baseline",
    )
    position = -1
    for fragment in ordered:
        new_position = value.find(fragment)
        require(
            new_position > position,
            "workflow route lacks or reorders: " + fragment,
        )
        position = new_position
    for fragment in (
        "rule families in a lookup result are retrieval priorities",
        "they are not the applicable requirement set",
        "complete-source inspection is permitted only when one of these "
        "conditions applies",
        "task is about the complete standard",
        "validates the retrieval architecture",
        "targeted retrieval cannot resolve an ambiguity that the reviewer records",
        "owner decision makes complete-source inspection necessary",
        "documentation review is the only linguistic conformance review",
        "do not do a second documentation review",
        "keep an unresolved technical fact or rights question with its "
        "canonical subject owner",
        "if a deterministic check identifies a specified defect, repair that "
        "defect. do its proof again",
        "identifies changes outside the one correction set",
        "does not give or change the linguistic verdict",
        "write once and use one review. if necessary, apply one set of exact "
        "corrections. record the locked state. do final deterministic "
        "validation. finish the cycle",
        "a blocked verdict lets the implementing agent make the one correction set",
        "the completed lifecycle does not change the initial linguistic verdict",
        "do not use a replacement candidate to start the same cycle again",
        "cannot ask for or start another documentation review, wording pass, "
        "semantic reinterpretation, or improvement cycle",
    ):
        require(fragment in value, "workflow boundary lacks: " + fragment)


def validate_source_documentation(text: str) -> None:
    validate_no_positive_assurance_claim(text)
    value = semantic_text(text)
    for fragment in (
        "records data for an exact check of source identity",
        "does not accept a different source as an automatic update",
        "contains no complete source text for a writing rule or complete ste "
        "dictionary",
        "retrieval index has no authority to change full applicability",
        "keep them local",
        "do not add them to version control",
        "does not keep source page text, the complete ste dictionary, or complete "
        "extracted source text",
        "rights state stays unknown",
        "does not give a licence to reproduce or supply",
        "reads the authorised source pdf one time",
        "validates the source-derived index identity",
        "does not rebuild the stale cache without the rebuild command",
        "query does not show the complete source text",
        "approved technical-term result gives its technical-term category and "
        "term meaning",
        "if its category differs from the register",
        "do not approve a term that is missing from the technical-term register",
        "tool cannot add or approve a technical noun or technical verb",
        "bounded result reports its total count, shown count, and truncation status",
        "no finding and no empty result shows conformance",
        "a pass command result also does not show conformance",
        "do not keep all review receipts for usual work",
        "does not narrow the applicable issue 9 requirement set",
        "first use the task's commit authority to freeze a clean git commit",
        "derives the frozen review scope from document identities and git",
        "scope schema 2 includes the complete logical units that changed in "
        "an existing document. this includes legacy documents",
        "review a new document in full",
        "unchanged legacy prose stays outside the repair scope",
        "preserved schema 1 scopes keep their initial meaning",
        "one independent documentation reviewer",
        "approved with exact corrections",
        "give all necessary exact replacements in that same review. "
        "this also applies after blocked",
        "use schema 3 for each new review-result file",
        "an empty correction set for blocked gives no completion proposal",
        "do not migrate them to schema 3",
        "apply the complete exact correction set once",
        "examine each preimage",
        "do not invent other wording",
        "do not invent other wording or get another linguistic verdict",
        "new state schema 2 entries record lifecycle status as locked and "
        "preserve the initial review result",
        "they do not claim linguistic accept or project acceptance",
        "existing schema 1 entries keep their initial meaning and values",
        "the ste lookup rejects a replacement review. before final validation "
        "completes the initial cycle, it rejects a new candidate for any of "
        "the same document paths",
        "with commit authority, commit the content in the locked state and "
        "reference/ste-review-state.json",
        "tracktemplate ste100 final= success sentinel",
        "proves source identity, exact candidate identity, frozen review scope, "
        "receipt, document-state, and final-content identity",
        "rejects changes outside the candidate and its one exact correction set",
        "preserves the initial verdict and reports the completed lifecycle "
        "as a different result",
        "does not judge linguistic conformance",
    ):
        require(fragment in value, "source/retrieval instructions lack: " + fragment)


def validate_skill_routing(skills: dict[str, str]) -> None:
    for name in SKILL_NAMES:
        text = skills[name]
        validate_no_positive_assurance_claim(text)
        require(
            "../../../reference/ENGINEERING_POLICY.md#"
            "tt-doc-001-tracktemplate-technical-documentation-profile" in text,
            name + " bypasses the canonical application profile",
        )
        if name in SOURCE_ROUTING_SKILL_NAMES:
            require(
                "../../../reference/external/asd-ste100/README.md" in text,
                name + " bypasses the canonical source/retrieval owner",
            )
            require(
                "local-retrieval-interface" in text
                or "pre-check-and-review-receipt" in text,
                name + " does not route through the retrieval interface",
            )
        else:
            require(
                "../../../reference/external/asd-ste100/README.md" not in text,
                name + " retained an obsolete governance-review source route",
            )
        require(
            "ASD-STE100_ISSUE9.pdf" not in text,
            name + " duplicates the canonical local source path",
        )
        rule_ids = set(re.findall(r"\b[1-9]\.[0-9]+\b", text))
        require(
            len(rule_ids) < 3,
            name + " contains a duplicated normative rule corpus",
        )
    require(
        "lookup result selects source material to read"
        in semantic_text(skills["tracktemplate-documentation-review"])
        and "does not select the applicable issue 9 requirement set"
        in semantic_text(skills["tracktemplate-documentation-review"]),
        "documentation review lets retrieval narrow applicability",
    )
    require(
        "lookup result is not the complete applicable rule set"
        in semantic_text(skills["tracktemplate-documentation-alignment"]),
        "documentation alignment treats lookup as complete",
    )
    require(
        "selected lookup results and an empty pre-check do not show conformance"
        in semantic_text(skills["tracktemplate-change-validation"]),
        "change validation overstates automatic evidence",
    )
    quality_review = semantic_text(skills["tracktemplate-quality-review"])
    require(
        "this skill does not review governance-document prose at any stage"
        in quality_review
        and "one documentation review, one permitted adjustment and one final "
        "deterministic validation, then done" in quality_review
        and "cannot invoke this skill to reconsider their wording or meaning"
        in quality_review
        and "does not examine the governance prose, repeat that review, change "
        "its verdict or propose wording" in quality_review,
        "quality review can reopen the governance-document cycle",
    )
    change_validation = semantic_text(skills["tracktemplate-change-validation"])
    require(
        "for governance documents, final deterministic validation with a "
        "pass result "
        "completes the finite technical author lead procedure" in change_validation
        and "does not send the prose to another reviewer" in change_validation,
        "change validation can start a later governance-document review",
    )
    technical_author = semantic_text(
        skills["tracktemplate-technical-author-lead"]
    )
    require(
        "before you author affected logical units, use the local ste retrieval "
        "interface" in technical_author
        and "writing includes the necessary checks and corrections before "
        "handoff" in technical_author
        and "when an assertion changes with the prose, preserve technical "
        "safeguards" in technical_author
        and "if a changed assertion could accept an incorrect result, "
        "use a negative test" in technical_author
        and "these checks are not another documentation review or approval "
        "stage" in technical_author
        and "apply the complete set of exact corrections once, also after "
        "blocked" in technical_author
        and "a result in the locked state does not become linguistic accept" in technical_author
        and "final validation with a pass result ends this documentation cycle"
        in technical_author
        and "do not send the document to another documentation, quality, "
        "publication, wording, or semantic review" in technical_author
        and "continuous integration can examine the final bytes"
        in technical_author
        and "cannot start another documentation review, correction pass, or "
        "linguistic improvement cycle" in technical_author
        and "do not do a second documentation review" in technical_author,
        "Technical Author Lead lost its bounded authoring and retrieval route",
    )


def validate_no_positive_assurance_claim(text: str) -> None:
    value = semantic_text(text)
    prohibited = (
        "ste100 compliant",
        "ste100 certified",
        "asd-ste100 certified",
        "guaranteed compliance",
        "selected lookup results prove conformance",
        "selected lookup results prove compliance",
        "lookup results are the complete applicable rule set",
        "lookup results are the complete applicable requirement set",
        "lookup result is the complete applicable rule set",
        "returned rules are the complete applicable rule set",
        "absence of findings proves conformance",
        "absence of findings proves compliance",
        "automatic validation proves conformance",
        "automated validation proves conformance",
        "successful automated validation proves conformance",
        "bypass the canonical application profile",
        "bypass the canonical profile",
        "skip the canonical application profile",
        "lookup controls what rules apply",
    )
    for phrase in prohibited:
        require(phrase not in value, "unsupported assurance claim: " + phrase)


def validate_contract_files() -> tuple[dict[str, object], dict[str, object]]:
    manifest = load_json(SOURCE_MANIFEST)
    index = load_json(RETRIEVAL_INDEX)
    STE.validate_source_manifest(manifest)
    STE.validate_retrieval_index(index)
    require(manifest["sha256"] == EXPECTED_SOURCE_SHA256, "source hash drifted")
    require(
        manifest["size_bytes"] == EXPECTED_SOURCE_SIZE,
        "source byte size drifted",
    )
    require(
        manifest["extraction_index_sha256"] == EXPECTED_EXTRACTION_INDEX_SHA256,
        "compact source-derived index identity drifted",
    )
    require(manifest["page_count"] == 434, "source page count drifted")
    require(
        manifest["copyright_status"] == "external-copyrighted-reference-local-only",
        "source rights boundary drifted",
    )
    local_source = SOURCE_DIR / str(manifest["filename"])
    if local_source.exists():
        identity = STE.verify_source(local_source, manifest)
        require(
            identity["sha256"] == EXPECTED_SOURCE_SHA256,
            "the available local source identity drifted",
        )
    require(
        RETRIEVAL_INDEX.stat().st_size < 12 * 1024,
        "retrieval metadata became a large source reproduction",
    )
    serialised = json.dumps(index, sort_keys=True).casefold()
    for key in ("dictionary_entries", "normative_text", "quotation", "rule_text"):
        require(
            key not in serialised,
            "retrieval index contains normative payload: " + key,
        )
    for family in index["families"]:
        location = family["source_location"]
        require(
            all(location.get(key) for key in ("part", "section", "pages")),
            "a rule family has no authoritative source location",
        )
    return manifest, index


def validate_copyright_and_ignore_boundary() -> None:
    ignore_lines = read(GITIGNORE).splitlines()
    require(
        ignore_lines.count("/reference/external/asd-ste100/*.pdf") == 1,
        "the PDF needs one narrow ignore rule",
    )
    require(
        ignore_lines.count("/reference/external/asd-ste100/.cache/") == 1,
        "the local derived cache needs one narrow ignore rule",
    )
    tracked = subprocess.run(
        ["git", "ls-files", "reference/external/asd-ste100"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    allowed_tracked = {
        "reference/external/asd-ste100/README.md",
        "reference/external/asd-ste100/retrieval-index.json",
        "reference/external/asd-ste100/source-manifest.json",
    }
    require(
        set(tracked).issubset(allowed_tracked),
        "the external-source directory has an unapproved tracked payload",
    )
    for path in tracked:
        require(not path.endswith(".pdf"), "the copyrighted PDF is tracked")
        require("/.cache/" not in path, "derived extracted content is tracked")
        require(not path.endswith(".txt"), "a complete text extract is tracked")
    allowed_entries = {
        ".cache",
        "ASD-STE100_ISSUE9.pdf",
        "README.md",
        "retrieval-index.json",
        "source-manifest.json",
    }
    unexpected = sorted(
        path.name for path in SOURCE_DIR.iterdir() if path.name not in allowed_entries
    )
    require(
        not unexpected,
        "unexpected external-source payload: " + ", ".join(unexpected),
    )
    local_cache = SOURCE_DIR / ".cache" / "issue9-cache-v2.json"
    if local_cache.exists():
        require(
            local_cache.stat().st_size < 1_250_000,
            "the local metadata cache exceeded its compact boundary",
        )
        cache = json.loads(local_cache.read_text(encoding="utf-8"))
        require("pages" not in cache, "the local cache retained extracted pages")
        require(
            stat.S_IMODE(local_cache.stat().st_mode) == 0o600,
            "the local metadata cache is not private",
        )


def validate_local_tool_boundary() -> None:
    source = read(TOOL_PATH)
    for fragment in (
        "import requests",
        "import urllib",
        "shell=True",
        "sqlite3",
        "socket",
        "subprocess.run(",
    ):
        require(fragment not in source, "local tool boundary widened: " + fragment)
    require(
        'SOURCE_FILE = REFERENCE_DIR / "ASD-STE100_ISSUE9.pdf"' in source,
        "the CLI source path is no longer fixed and local",
    )
    require(
        'CACHE_FILE = REFERENCE_DIR / ".cache"' in source,
        "the CLI cache path is no longer fixed and local",
    )
    build_body = source.split("def build_cache_data", 1)[1].split("def write_cache", 1)[
        0
    ]
    require(
        '"pages": pages' not in build_body,
        "the local cache stores extracted page text",
    )
    for fragment in (
        'source_bytes = stream.read(int(manifest["size_bytes"]) + 1)',
        "input_bytes=source_bytes",
        "extractor-identity-mismatch",
        "MAX_EXTRACTED_TEXT_BYTES",
        "MAX_EXTRACTED_PAGE_BYTES",
        "extraction_index_sha256",
    ):
        require(fragment in source, "source/extractor boundary lacks: " + fragment)

    untrusted_owner = types.SimpleNamespace(
        st_mode=stat.S_IFREG | 0o755,
        st_uid=os.geteuid() + 1,
    )
    expect_ste_error(
        "extractor-owner-untrusted",
        lambda: STE._validate_extractor_file(
            pathlib.Path("/usr/bin/pdftotext"),
            untrusted_owner,
        ),
    )


def require_one_technical_term_owner(documents: dict[str, str]) -> None:
    heading = "## ASD-STE100 project terminology"
    owners = sorted(path for path, text in documents.items() if heading in text)
    require(
        owners == ["reference/TERMINOLOGY.md"],
        "competing technical-term owners: " + ", ".join(owners),
    )


def load_tracked_markdown() -> dict[str, str]:
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    return {path: read(ROOT / path) for path in tracked if path}


def require_no_substantial_normative_duplication(
    documents: dict[str, str],
) -> None:
    for path, text in documents.items():
        rule_markers = re.findall(r"\bRule [1-9]\.[0-9]+\b", text)
        require(
            len(rule_markers) <= 8,
            "substantial normative STE rule corpus in " + path,
        )
        dictionary_markers = re.findall(
            r"(?m)^\s*[A-Z][A-Z0-9' -]{1,50}\s+"
            r"\((?:art|adj|adv|conj|n|prep|pron|v)\)(?:,)?",
            text,
        )
        require(
            len(dictionary_markers) < 20,
            "substantial normative STE dictionary corpus in " + path,
        )
        page_labels = re.findall(r"\bPage [12]-[A-Z0-9-]+\b", text)
        require(
            len(page_labels) < 20,
            "substantial source-page corpus in " + path,
        )
        lowered = text.casefold()
        for payload_key in (
            '"complete_dictionary"',
            '"dictionary_corpus"',
            '"normative_text"',
            '"page_text"',
            '"rule_text"',
            '"source_text"',
        ):
            require(
                payload_key not in lowered,
                "normative source payload key in " + path,
            )


def validate_technical_term_owner() -> None:
    guidance = load_tracked_markdown()
    require_one_technical_term_owner(guidance)
    for text in guidance.values():
        validate_no_positive_assurance_claim(text)
    guidance["reference/external/asd-ste100/retrieval-index.json"] = read(
        RETRIEVAL_INDEX
    )
    guidance["reference/external/asd-ste100/source-manifest.json"] = read(
        SOURCE_MANIFEST
    )
    require_no_substantial_normative_duplication(guidance)
    terminology = semantic_text(read(TERMINOLOGY))
    for term in (
        "ste lookup",
        "word lookup",
        "rule lookup",
        "topic lookup",
        "targeted retrieval",
        "lookup query",
        "lookup result",
        "concise lookup output",
        "retrieval contract",
        "retrieval index",
        "retrieval architecture",
        "rule identifier",
        "source location",
        "source-derived index",
        "derived cache",
        "source manifest",
        "source identity",
        "authorised source",
        "pdf extractor",
        "verified source bytes",
        "source mode",
        "bounded source excerpt",
        "source page",
        "source text",
        "ste dictionary",
        "deterministic pre-check",
        "review candidate",
        "content category",
        "review receipt",
        "exact-content exclusion",
        "rule family",
        "writing rule",
        "full applicability",
        "applicable rule set",
        "controlled vocabulary",
        "complete-source inspection",
        "technical-term register",
        "technical-term status",
        "technical-term category",
        "unresolved terminology",
        "source efficiency",
        "retrieval optimisation",
        "requirement set",
        "independent review",
        "documentation alignment",
        "documentation skill routing",
        "partial retrieval",
        "partial conformance",
        "drift control",
        "rights state",
        "positive rights claim",
        "cache identity",
        "current user",
        "active python environment",
        "shown count",
        "truncation status",
        "retrieve",
        "approve",
        "bind",
        "rebuild",
        "optimise",
        "resolve",
        "return",
        "extract",
        "reproduce",
        "narrow",
        "fail closed",
        "record",
    ):
        require(term in terminology, "technical-term register lacks: " + term)
    registrations = STE.extract_project_terms(read(TERMINOLOGY))
    by_term_and_category = {
        (item["canonical_term"].casefold(), item["category"]): item
        for item in registrations
    }
    for convenience_noun in (
        "condition",
        "operation",
        "sentence",
    ):
        require(
            (convenience_noun, "noun") not in by_term_and_category,
            "ordinary language became a project technical noun: "
            + convenience_noun,
        )
    for generic_verb in ("separate", "improve", "reduce"):
        require(
            (generic_verb, "verb") not in by_term_and_category,
            "an ordinary verb became a generic project technical verb: " + generic_verb,
        )


def validate_provenance_documentation(text: str) -> None:
    validate_no_positive_assurance_claim(text)
    value = semantic_text(text)
    for fragment in (
        "asd-ste100 issue 9 reference",
        "local extraction and reproduction rights unknown",
        "does not give permission to reproduce or supply",
        "no positive rights claim, certification claim, or asd endorsement claim",
        "does not keep source text for a source page, a complete ste dictionary, "
        "or a complete source copy",
        "pdf is not a product runtime dependency",
        "derived cache is also not a product runtime dependency",
    ):
        require(fragment in value, "provenance boundary lacks: " + fragment)


def validate_validation_text(validation_text: str) -> None:
    validate_no_positive_assurance_claim(validation_text)
    validation = semantic_text(validation_text)
    for fragment in (
        "validate the retrieval contract without the pdf",
        "must fail closed when the source is missing",
        "byte size or sha-256 identity differs from the source manifest",
        "must reject a source-derived index whose identity differs from the "
        "source manifest",
        "must be a regular file",
        "must not be in the repository or active python environment",
        "group and other users must not have write access",
        "derived cache must contain metadata only",
        "source mode must use verified source bytes",
        "must not claim linguistic conformance, certification, or endorsement",
        "receipt must record examination of the complete applicable requirement "
        "set",
        "receipt, pre-check, derived cache, and selected lookup results do "
        "not show",
        "author examines all candidate documents together and freezes their "
        "exact content",
        "identifies the complete logical units that changed from document "
        "identities and the baseline",
        "review a new document in full",
        "one independent documentation reviewer returns one complete verdict for "
        "the frozen review scope",
        "it is accept",
        "approved with exact corrections",
        "or blocked",
        "all necessary exact replacements are in that review",
        "apply the set once against verified preimages",
        "then record the locked state for the final content",
        "preserves the initial review verdict and gives no linguistic "
        "acceptance",
        "documentation review is the only linguistic conformance review",
        "do not run a second documentation review",
        "final validation does not judge prose",
        "must validate the official source identity and frozen candidate",
        "must also validate the git-derived frozen review scope, review result, "
        "and receipt",
        "must validate expected document-level state and final content",
        "reject unrelated post-review mutation",
        "do not include unchanged legacy prose in the repair scope",
        "new scope schema 2 includes only materially changed complete logical "
        "units",
        "durable review state at document level",
        "state entries with schema 2 keep the initial verdict and identify "
        "the content in the locked state",
        "preserve existing schema 1 state entries and historical results "
        "without migration",
        "do not persist sentence, paragraph, or logical-unit workflow state",
        "a result with schema 3 and a blocked verdict must complete the "
        "lifecycle when it has a full set of exact corrections. its state "
        "must be locked . it must not get another review or falsely claim accept",
        "a blocked result with no correction stays recorded without a "
        "completion proposal",
        "an unresolved technical fact or rights question stays with its "
        "canonical subject owner",
        "reject replacement reviews and attempts to start the same cycle "
        "again with a candidate for any of the same document paths",
        "reject an old schema pair that bypasses a recorded review in this cycle",
        "after the recorded final commit, let later work start. this includes "
        "work after document deletion",
        "if a deterministic check identifies a specified defect, repair it "
        "at the boundary that caused it. do its proof again",
        "do not start another linguistic review",
    ):
        require(fragment in validation, "validation owner lacks: " + fragment)
    require(
        re.search(
            r"(?:pdf )?extractor (?:file )?owner can be root or the current user",
            validation,
        )
        is not None,
        "validation owner lacks the extractor-owner restriction",
    )


def validate_agent_and_validation_routing() -> None:
    agents = read(AGENTS)
    validate_no_positive_assurance_claim(agents)
    require(100 <= len(agents.splitlines()) <= 140, "AGENTS line budget drifted")
    agents_value = semantic_text(agents)
    for fragment in (
        "canonical prose follows the technical documentation profile",
        "use the documentation workflow and use its ste lookup first",
        "ste lookup changes the source text that an agent reads for this task",
        "does not narrow the applicable issue 9 requirement set",
    ):
        require(fragment in agents_value, "root routing lacks: " + fragment)
    validate_validation_text(read(VALIDATION))


def lfe_rows(text: str) -> list[str]:
    return [
        line for line in text.splitlines(keepends=True) if line.startswith("| LFE-")
    ]


def validate_lfe_text(text: str) -> None:
    validate_no_positive_assurance_claim(text)
    rows = lfe_rows(text)
    identifiers = [re.match(r"\| (LFE-\d{3})", row).group(1) for row in rows]
    expected = ["LFE-{:03d}".format(number) for number in range(1, 23)]
    require(identifiers == expected, "LFE identifiers are not unique and sequential")
    earlier = "".join(rows[:18]).encode("utf-8")
    require(
        hashlib.sha256(earlier).hexdigest() == LFE_001_TO_018_ROWS_SHA256,
        "an earlier LFE row was modified, renumbered, or replaced",
    )
    require(text.count("| LFE-019 /") == 1, "LFE-019 must occur exactly once")
    lfe_019 = rows[18]
    row = semantic_text(lfe_019)
    for fragment in (
        "large authorised source again and again",
        "too much read time and agent context",
        "targeted retrieval",
        "complete applicable requirement set",
        "source identity",
        "full applicability for issue 9",
        "independent review",
        "increase source efficiency",
        "concise lookup output",
        "documentation skill routing",
        "technical-term register",
        "optimise the access path, not the requirement set",
        "cannot use partial retrieval as evidence of partial conformance",
    ):
        require(fragment in row, "LFE-019 lacks: " + fragment)
    cells = [cell.strip() for cell in lfe_019.strip().strip("|").split("|")]
    require(len(cells) == 4, "LFE-019 row structure drifted")
    reusable = semantic_text(cells[3])
    for fragment in (
        "optimise the access path, not the requirement set",
        "official source identity",
        "give only the source material that is necessary for the task",
        "workflow, validation, and independent review controls",
        "cannot use partial retrieval as evidence of partial conformance",
    ):
        require(fragment in reusable, "LFE-019 reusable rule lacks: " + fragment)
    require(
        re.search(
            r"keep full applicability and targeted retrieval in different "
            r"(?:authority )?boundaries",
            reusable,
        )
        is not None,
        "LFE-019 reusable rule loses the applicability/retrieval boundary",
    )
    for link in (
        "ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile",
        "VALIDATION.md#asd-ste100-retrieval-assurance",
        "AGENT_WORKFLOWS.md#tt-doc-001-workflow-integration",
        "external/asd-ste100/README.md#local-retrieval-interface",
    ):
        require(link in lfe_019, "LFE-019 lacks canonical link: " + link)
    require(
        "this lfe owns" not in row and "lfe-019 owns" not in row,
        "LFE-019 became a competing STE policy owner",
    )
    require("certif" not in row, "LFE-019 implies certification")
    require("token" not in row, "LFE-019 makes an unmeasured token claim")


def _write_fixture_contracts(directory: pathlib.Path, index: dict[str, object]):
    source = directory / "issue9-fixture.pdf"
    source.write_bytes(b"synthetic Issue 9 test source")
    rule_ids = sorted(STE.expected_rule_ids())
    recommendation_ids = sorted(STE.expected_recommendation_ids())
    pages = [
        "\n".join(
            [" Rule {} history".format(item) for item in rule_ids]
            + [" {} history".format(item) for item in recommendation_ids]
            + ["Page HI-1"]
        )
    ]
    for section in range(1, 10):
        lines = [
            " Rule {} section index".format(item)
            for item in rule_ids
            if item.startswith("{}.".format(section))
        ]
        if section == 9:
            lines.extend(
                " {} section index".format(item) for item in recommendation_ids
            )
        lines.append("Page 1-{}-1".format(section))
        pages.append("\n".join(lines))
    pages.extend(
        [
            " Introductory material\n Rule 6.3 authoritative occurrence\nPage 1-6-4",
            (
                "INSTALL (v), To put in position\n"
                "INSTALLS,\n"
                "INSTALLED,\n"
                "INSTALLING\n"
                "CHANGE (v), To become different\n"
                "CHANGES,\n"
                "CHANGED,\n"
                "CHANGING\n"
                "CONTAIN (v), To hold\n"
                "CONTAINS,\n"
                "CONTAINED,\n"
                "CONTAINING\n"
                "differ (v) USE: BE DIFFERENT\n"
                "obsolete (adj) USE: OLD\n"
                "account for (v)    MAKE SURE (v)\n"
                "according to       REFER (v)\n"
                "(prep)             REFER TO (v)\n"
                "Page 2-1-A1"
            ),
        ]
    )
    page_records = [
        {
            "page_number": number,
            "source_label": STE._page_label(text, number),
            "text": text,
        }
        for number, text in enumerate(pages, start=1)
    ]
    dictionary = STE._dictionary_index(page_records)
    require(
        dictionary["account for"][0]["part_of_speech"] == "v",
        "a same-line multiword inspect entry was not indexed",
    )
    require(
        dictionary["according to"][0]["part_of_speech"] == "prep",
        "a continuation-line inspect entry was not indexed",
    )
    require(
        "according to refer" not in dictionary,
        "an inspect entry was fused with its approved alternative",
    )
    rule_pages = STE._rule_page_index(
        page_records,
        STE.expected_rule_ids() | STE.expected_recommendation_ids(),
    )
    manifest = {
        "cache_schema_version": 2,
        "copyright_status": "external-copyrighted-reference-local-only",
        "extraction_index_sha256": STE._source_index_sha256(
            dictionary,
            rule_pages,
        ),
        "filename": source.name,
        "issue": 9,
        "official_url": (
            "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf"
        ),
        "page_count": len(pages),
        "publication_date": "2025-01-15",
        "schema_version": 1,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "size_bytes": source.stat().st_size,
        "standard_id": "ASD-STE100",
    }
    manifest_path = directory / "source-manifest.json"
    index_path = directory / "retrieval-index.json"
    terms_path = directory / "TERMINOLOGY.md"
    profile_path = directory / "ENGINEERING_POLICY.md"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    index_path.write_text(json.dumps(index), encoding="utf-8")
    terms_path.write_text(
        "# Terms\n\n## ASD-STE100 project terminology\n\n"
        "Use these technical nouns only with their stated project meanings:\n\n"
        "| Term group | Approved technical nouns and meaning |\n"
        "| --- | --- |\n"
        "| Test | **TrackTemplate** is the product. A **plain line** is track "
        "without switches and crossings. |\n\n"
        "Use these technical verbs only with their stated project meanings:\n\n"
        "| Technical verb | Project meaning |\n"
        "| --- | --- |\n"
        "| **Validate** | Do a named check and examine its result. |\n\n"
        "## Next section\n",
        encoding="utf-8",
    )
    profile_path.write_text("synthetic profile revision\n", encoding="utf-8")
    return (
        source,
        manifest,
        manifest_path,
        index_path,
        terms_path,
        profile_path,
        pages,
    )


def validate_cache_and_lookup_behaviour(index: dict[str, object]) -> None:
    with tempfile.TemporaryDirectory(prefix="tracktemplate-ste100-test-") as name:
        directory = pathlib.Path(name)
        (
            source,
            manifest,
            manifest_path,
            index_path,
            terms_path,
            profile_path,
            pages,
        ) = _write_fixture_contracts(directory, index)
        cache = STE.build_cache_data(
            source_path=source,
            manifest_path=manifest_path,
            index_path=index_path,
            terminology_path=terms_path,
            profile_path=profile_path,
            extracted_pages=pages,
            extractor_identity={
                "mode": "0755",
                "owner_uid": os.geteuid(),
                "path": "/synthetic/pdftotext",
                "sha256": "a" * 64,
                "version": "synthetic-extractor:1",
            },
        )
        require("pages" not in cache, "the compact cache retained page text")
        serialised_cache = json.dumps(cache, sort_keys=True)
        require(
            "authoritative occurrence" not in serialised_cache,
            "the compact cache retained normative source prose",
        )
        require(
            len(serialised_cache.encode("utf-8")) < 256 * 1024,
            "the synthetic compact cache is unexpectedly large",
        )
        cache_path = directory / "cache" / "issue9.json"
        STE.write_cache(cache_path, cache)
        require(
            stat.S_IMODE(cache_path.stat().st_mode) == 0o600,
            "the ignored cache is not private",
        )
        verified, verified_index, source_bytes = STE.load_verified_cache(
            source_path=source,
            cache_path=cache_path,
            manifest_path=manifest_path,
            index_path=index_path,
            terminology_path=terms_path,
            profile_path=profile_path,
        )
        require(verified == cache, "written cache did not validate exactly")
        require(
            source_bytes == source.read_bytes(),
            "cache loading did not retain the verified source bytes",
        )

        def page_loader(number: int) -> str:
            return pages[number - 1]

        rule = STE.lookup_rule(
            "6.3",
            cache,
            verified_index,
            include_source=True,
            page_loader=page_loader,
        )
        require(rule["identifier"] == "6.3", "rule lookup returned wrong rule")
        require("source_excerpt" in rule, "source mode returned no bounded excerpt")
        require(
            rule["source_excerpt"]["source_label"] == "1-6-4",
            "source mode returned section-opening material instead of the rule",
        )
        require(
            len(rule["source_excerpt"]["text"]) <= STE.MAX_SOURCE_EXCERPT_CHARS + 1,
            "source excerpt exceeded its context boundary",
        )
        expect_ste_error(
            "source-page-location-mismatch",
            lambda: STE.lookup_rule(
                "6.3",
                cache,
                verified_index,
                include_source=True,
                page_loader=lambda _: "Rule 6.3\nPage 1-6-X",
            ),
        )
        expect_ste_error(
            "source-target-not-found",
            lambda: STE.lookup_rule(
                "6.3",
                cache,
                verified_index,
                include_source=True,
                page_loader=lambda _: "Rule 6.2 plausible substitute\nPage 1-6-4",
            ),
        )
        recommendation = STE.lookup_rule("GR-1", cache, verified_index)
        require(
            recommendation["classification"] == "recommendation-not-formal-rule",
            "a general recommendation became a formal rule",
        )
        topic = STE.lookup_topic("terminology", verified_index)
        require(topic["total_matches"] >= 1, "topic lookup returned no family")
        expect_ste_error(
            "topic-query-invalid",
            lambda: STE.lookup_topic("", verified_index),
        )
        review = STE.lookup_review_category("descriptive-prose", verified_index)
        require(
            review["controls"]["retrieval_scope"] == "returned-items-only",
            "review priorities claim complete applicability",
        )

        require(
            all(
                isinstance(item, dict)
                and item.get("category") in {"noun", "verb"}
                and item.get("canonical_term")
                and item.get("meaning")
                for item in cache["technical_terms"]
            ),
            "the cache flattened technical-term category or meaning metadata",
        )
        project_term = STE.lookup_word(
            "plain line",
            cache,
            part_of_speech="noun",
        )
        require(
            project_term["status"] == "approved-tracktemplate-technical-term",
            "project terminology was not the first authority",
        )
        require(
            project_term["registered_usages"][0]["category"] == "noun"
            and project_term["registered_usages"][0]["meaning"],
            "technical-noun category or registered meaning was not returned",
        )
        require(
            project_term["contextual_usage_review_required"] is True,
            "a registered term was treated as context-free approval",
        )
        plural_term = STE.lookup_word(
            "plain lines",
            cache,
            part_of_speech="noun",
        )
        require(
            plural_term["status"] == "technical-term-inflection-review-required"
            and plural_term["canonical_term"] == "plain line"
            and plural_term["registered_usages"][0]["match_basis"]
            == "inferred-noun-plural",
            "an inferred project-term plural received approval",
        )
        software_cache = {
            **cache,
            "technical_terms": [
                *cache["technical_terms"],
                {
                    "canonical_term": "Software",
                    "category": "noun",
                    "meaning": "Software is a test tool.",
                    "term_group": "Test",
                },
            ],
        }
        invalid_plural = STE.lookup_word(
            "softwares",
            software_cache,
            part_of_speech="noun",
        )
        require(
            invalid_plural["status"] == "technical-term-inflection-review-required"
            and invalid_plural["approval_changed"] is False,
            "an invented uncountable plural received technical-term approval",
        )
        wrong_noun_usage = STE.lookup_word(
            "plain line",
            cache,
            part_of_speech="verb",
        )
        require(
            wrong_noun_usage["status"]
            == "technical-term-category-mismatch-review-required"
            and wrong_noun_usage["approval_changed"] is False,
            "a technical noun silently became an approved verb",
        )
        technical_verb = STE.lookup_word(
            "validate",
            cache,
            part_of_speech="verb",
        )
        require(
            technical_verb["status"] == "approved-tracktemplate-technical-term"
            and technical_verb["registered_usages"][0]["category"] == "verb",
            "technical-verb category was not retained",
        )
        inflected_technical_verb = STE.lookup_word(
            "validates",
            cache,
            part_of_speech="verb",
        )
        require(
            inflected_technical_verb["status"]
            == "technical-term-inflection-review-required"
            and inflected_technical_verb["registered_usages"][0]["match_basis"]
            == "inferred-verb-third-person",
            "an inferred technical-verb form received approval",
        )
        wrong_verb_usage = STE.lookup_word(
            "validate",
            cache,
            part_of_speech="noun",
        )
        require(
            wrong_verb_usage["status"]
            == "technical-term-category-mismatch-review-required",
            "a technical verb silently became an approved noun",
        )
        recognised = STE.lookup_word(
            "install",
            cache,
            include_source=True,
            page_loader=page_loader,
        )
        require(
            recognised["status"] == "recognised-ste-vocabulary"
            and recognised["inspection_required"],
            "approved dictionary vocabulary classification drifted",
        )
        expect_ste_error(
            "source-target-not-found",
            lambda: STE.lookup_word(
                "install",
                cache,
                include_source=True,
                page_loader=lambda _: (
                    "CHANGE (v), A plausible substitute entry\nPage 2-1-A1"
                ),
            ),
        )
        recognised_form = STE.lookup_word(
            "changes",
            cache,
            include_source=True,
            page_loader=page_loader,
        )
        require(
            recognised_form["status"] == "recognised-ste-vocabulary"
            and recognised_form["dictionary_entries"][0]["headword"] == "CHANGE",
            "an explicitly listed STE inflection was not recognised",
        )
        require(
            "CHANGE (v)" in recognised_form["source_excerpt"]["text"],
            "an inflected lookup did not retrieve its dictionary headword",
        )
        inferred_form = STE.lookup_word("differs", cache)
        require(
            inferred_form["status"] == "dictionary-inspection-required"
            and inferred_form["dictionary_entries"][0]["match_basis"]
            == "possible-inflection-base",
            "a possible unapproved inflection bypassed dictionary review",
        )
        inspect = STE.lookup_word("obsolete", cache)
        require(
            inspect["status"] == "dictionary-inspection-required",
            "listed unapproved vocabulary was not sent to dictionary review",
        )
        same_line_inspect = STE.lookup_word(
            "account for",
            cache,
            include_source=True,
            page_loader=page_loader,
        )
        require(
            same_line_inspect["status"] == "dictionary-inspection-required"
            and "source_excerpt" in same_line_inspect,
            "a same-line multiword inspect entry was not retrievable",
        )
        continuation_inspect = STE.lookup_word(
            "according to",
            cache,
            include_source=True,
            page_loader=page_loader,
        )
        require(
            continuation_inspect["status"] == "dictionary-inspection-required"
            and continuation_inspect["dictionary_entries"][0]["part_of_speech"]
            == "prep"
            and "source_excerpt" in continuation_inspect,
            "a continuation-line inspect entry was not retrievable",
        )
        unknown = STE.lookup_word("unmappedterm", cache)
        require(
            unknown["status"] == "unresolved-terminology-review-required"
            and unknown["approval_changed"] is False,
            "an unknown term gained approval",
        )

        long_sentence = " ".join(["Alpha"] * 26) + "; ordinary track."
        precheck = STE.precheck_text(long_sentence, "descriptive", cache)
        require(precheck["sentence_length_review"], "long sentence was not found")
        require(
            "semicolon" in precheck["likely_construction_review"],
            "semicolon review candidate was not found",
        )
        require(
            precheck["likely_inconsistent_terminology"],
            "known terminology inconsistency was not found",
        )
        many_long_sentences = "\n\n".join(
            " ".join(["Alpha"] * 21) + "." for _ in range(31)
        )
        bounded_precheck = STE.precheck_text(
            many_long_sentences,
            "procedural",
            cache,
        )
        sentence_counts = bounded_precheck["result_counts"]["sentence_length_review"]
        require(
            sentence_counts
            == {"returned_count": 30, "total_count": 31, "truncated": True},
            "a bounded pre-check hid later sentence findings",
        )
        complete_precheck = STE.precheck_text(
            many_long_sentences,
            "procedural",
            cache,
            verbose=True,
        )
        require(
            len(complete_precheck["sentence_length_review"]) == 31
            and complete_precheck["result_counts"]["sentence_length_review"]
            == {
                "returned_count": 31,
                "total_count": 31,
                "truncated": False,
            },
            "verbose pre-check did not return the complete finding set",
        )
        precision = STE.precheck_text(
            "TrackTemplate changes a plain line. It contains installed items. "
            "The value differs.",
            "procedural",
            cache,
        )
        require(
            not precision["unresolved_vocabulary_candidates"],
            "ordinary listed or bounded inflections became unresolved noise",
        )
        require(
            precision["ste_dictionary_inspection_candidates"] == ["differs"],
            "the bounded inflection inspection status drifted",
        )
        wrapped_term = STE.precheck_text(
            "TrackTemplate uses a plain\nline.",
            "procedural",
            cache,
        )
        require(
            any(
                item["canonical_term"] == "plain line"
                and item["category"] == "noun"
                and item["status"] == "approved-tracktemplate-technical-term"
                and item["match_basis"] == "exact-registered-form"
                for item in wrapped_term["project_technical_terms_found"]
            ),
            "a line wrap hid a registered multiword technical term",
        )
        inferred_project_term = STE.precheck_text(
            "Softwares softwares softwares.",
            "procedural",
            software_cache,
        )
        require(
            any(
                item["matched_form"] == "softwares"
                and item["status"] == "technical-term-inflection-review-required"
                and item["match_basis"] == "inferred-noun-plural"
                for item in inferred_project_term["project_technical_terms_found"]
            ),
            "pre-check silently approved or hid an inferred project-term form",
        )
        repeated_unknown = STE.precheck_text(
            "Unmappedterm unmappedterm unmappedterm.",
            "procedural",
            cache,
        )
        require(
            repeated_unknown["unresolved_vocabulary_candidates"] == ["Unmappedterm"],
            "a repeated unresolved term was not sent to review",
        )

        baseline_text = " ".join(["Legacy"] * 26) + ".\n"
        document = directory / "review.md"
        document.write_text(
            baseline_text + "TrackTemplate uses plain line.\n",
            encoding="utf-8",
        )
        receipt_arguments = {
            "document_path": document,
            "category": "descriptive",
            "cache": cache,
            "index": verified_index,
            "baseline_text": baseline_text,
            "baseline_revision": "a" * 40,
            "rule_ids": ["6.3"],
            "words": ["install"],
            "topics": ["terminology"],
            "exact_content_exclusions": ["code identifiers"],
            "unresolved_uncertainties": [],
        }
        expect_ste_error(
            "full-applicability-not-confirmed",
            lambda: STE.make_review_receipt(
                full_applicability_considered=False,
                **receipt_arguments,
            ),
        )
        oversized_receipt_arguments = dict(receipt_arguments)
        oversized_receipt_arguments["unresolved_uncertainties"] = ["bounded item"] * (
            STE.MAX_RECEIPT_ITEMS + 1
        )
        expect_ste_error(
            "receipt-input-invalid",
            lambda: STE.make_review_receipt(
                full_applicability_considered=True,
                **oversized_receipt_arguments,
            ),
        )
        receipt = STE.make_review_receipt(
            full_applicability_considered=True,
            **receipt_arguments,
        )
        require(
            receipt["full_applicability_considered"] is True,
            "receipt lost confirmation",
        )
        require(
            receipt["precheck"]["result_counts"]["sentence_length_review"]
            == {"returned_count": 0, "total_count": 0, "truncated": False},
            "receipt pre-checked legacy text outside its changed-unit scope",
        )
        require(
            receipt["review_scope"]["kind"] == "changed-canonical-prose-bundle"
            and receipt["review_scope"]["baseline_revision"] == "a" * 40
            and receipt["review_scope"]["baseline_document"]["sha256"]
            == hashlib.sha256(baseline_text.encode("utf-8")).hexdigest()
            and receipt["review_scope"]["candidate_document"]["sha256"]
            == receipt["document"]["sha256"]
            and receipt["review_scope"]["reviewed_text"]["hunk_count"] == 1
            and receipt["review_scope"]["reviewed_text"]["line_count"] == 1,
            "receipt did not bind the reviewed change to baseline and candidate",
        )
        require(
            "project_term_matches" in receipt["technical_term_status"]
            and "approved_project_terms" not in receipt["technical_term_status"],
            "receipt gave every project-term match an approval label",
        )
        receipt_path = STE.write_review_receipt(
            document,
            receipt,
            directory / "receipts",
        )
        require(receipt_path.is_file(), "review receipt was not written")
        require(
            stat.S_IMODE(receipt_path.parent.stat().st_mode) == 0o700,
            "the receipt directory is not private",
        )
        require(
            stat.S_IMODE(receipt_path.stat().st_mode) == 0o600,
            "the receipt is not private",
        )
        require(
            STE.write_review_receipt(document, receipt, directory / "receipts")
            == receipt_path,
            "identical content-addressed receipt was not reused",
        )
        expect_ste_error(
            "receipt-path-invalid",
            lambda: STE.write_review_receipt(
                document,
                receipt,
                directory / "outside",
                allowed_root=directory / "allowed",
            ),
        )
        linked_receipts = directory / "linked-receipts"
        linked_receipts.symlink_to(receipt_path.parent, target_is_directory=True)
        expect_ste_error(
            "receipt-path-invalid",
            lambda: STE.write_review_receipt(
                document,
                receipt,
                linked_receipts,
            ),
        )
        validate_no_positive_assurance_claim(json.dumps(receipt))

        no_change_arguments = dict(receipt_arguments)
        no_change_arguments["baseline_text"] = document.read_text(encoding="utf-8")
        expect_ste_error(
            "review-scope-empty",
            lambda: STE.make_review_receipt(
                full_applicability_considered=True,
                **no_change_arguments,
            ),
        )
        invalid_revision_arguments = dict(receipt_arguments)
        invalid_revision_arguments["baseline_revision"] = "main"
        expect_ste_error(
            "review-baseline-invalid",
            lambda: STE.make_review_receipt(
                full_applicability_considered=True,
                **invalid_revision_arguments,
            ),
        )

        oversized_review = directory / "oversized-review.md"
        oversized_review.write_bytes(b"x" * (STE.MAX_REVIEW_DOCUMENT_BYTES + 1))
        expect_ste_error(
            "review-document-too-large",
            lambda: STE._read_review_document(oversized_review),
        )

        expect_ste_error(
            "source-missing",
            lambda: STE.verify_source(
                directory / "absent" / source.name,
                manifest,
            ),
        )
        expect_ste_error(
            "source-path-mismatch",
            lambda: STE.verify_source(directory / "wrong-name.pdf", manifest),
        )
        wrong_manifest = copy.deepcopy(manifest)
        wrong_manifest["sha256"] = "0" * 64
        expect_ste_error(
            "source-hash-mismatch",
            lambda: STE.verify_source(source, wrong_manifest),
        )
        changed_directory = directory / "changed"
        changed_directory.mkdir()
        changed_source = changed_directory / source.name
        changed_source.write_bytes(b"changed source")
        expect_ste_error(
            "source-size-mismatch",
            lambda: STE.verify_source(changed_source, manifest),
        )
        linked_directory = directory / "linked"
        linked_directory.mkdir()
        linked_source = linked_directory / source.name
        linked_source.symlink_to(source)
        expect_ste_error(
            "source-not-file",
            lambda: STE.verify_source(linked_source, manifest),
        )
        wrong_size_manifest = copy.deepcopy(manifest)
        wrong_size_manifest["size_bytes"] = manifest["size_bytes"] + 1
        expect_ste_error(
            "source-size-mismatch",
            lambda: STE.verify_source(source, wrong_size_manifest),
        )
        wrong_index_manifest = copy.deepcopy(manifest)
        wrong_index_manifest["extraction_index_sha256"] = "0" * 64
        wrong_index_path = directory / "wrong-index-manifest.json"
        wrong_index_path.write_text(
            json.dumps(wrong_index_manifest),
            encoding="utf-8",
        )
        expect_ste_error(
            "extraction-index-mismatch",
            lambda: STE.build_cache_data(
                source_path=source,
                manifest_path=wrong_index_path,
                index_path=index_path,
                terminology_path=terms_path,
                profile_path=profile_path,
                extracted_pages=pages,
                extractor_identity=cache["extractor_identity"],
            ),
        )

        expect_ste_error(
            "extractor-output-too-large",
            lambda: STE._run_bounded_process(
                [
                    sys.executable,
                    "-c",
                    'import sys; sys.stdout.buffer.write(b"x" * 1024)',
                ],
                input_bytes=b"",
                stdout_limit=64,
                stderr_limit=64,
                timeout=10,
            ),
        )
        original_extractor_identity = STE._extractor_identity
        STE._extractor_identity = lambda: {
            "mode": "0755",
            "owner_uid": os.geteuid(),
            "path": "/synthetic/current-pdftotext",
            "sha256": "b" * 64,
            "version": "synthetic-current:1",
        }
        try:
            expect_ste_error(
                "extractor-identity-mismatch",
                lambda: STE._run_pdftotext(
                    b"verified source bytes",
                    first_page=1,
                    expected_identity=cache["extractor_identity"],
                ),
            )
        finally:
            STE._extractor_identity = original_extractor_identity

        source_identity = STE.verify_source(source, manifest)
        identities = STE._input_identities(
            manifest_path,
            index_path,
            terms_path,
            profile_path,
        )
        stale = copy.deepcopy(cache)
        stale["inputs"]["technical_terms_sha256"] = "0" * 64
        expect_ste_error(
            "cache-input-mismatch",
            lambda: STE.validate_cache_data(
                stale,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        incompatible = copy.deepcopy(cache)
        incompatible["schema_version"] = 999
        expect_ste_error(
            "cache-version-incompatible",
            lambda: STE.validate_cache_data(
                incompatible,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        wrong_cache_source = copy.deepcopy(cache)
        wrong_cache_source["source"]["sha256"] = "0" * 64
        expect_ste_error(
            "cache-source-mismatch",
            lambda: STE.validate_cache_data(
                wrong_cache_source,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        corrupt_content = copy.deepcopy(cache)
        corrupt_content["dictionary"]["install"][0]["displayed_word"] = "ALTERED"
        expect_ste_error(
            "cache-source-index-mismatch",
            lambda: STE.validate_cache_data(
                corrupt_content,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        self_attested = copy.deepcopy(corrupt_content)
        self_attested["derived_content_sha256"] = STE._derived_content_sha256(
            self_attested
        )
        expect_ste_error(
            "cache-source-index-mismatch",
            lambda: STE.validate_cache_data(
                self_attested,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        corrupt_project_terms = copy.deepcopy(cache)
        corrupt_project_terms["technical_terms"].append("Unapproved term")
        expect_ste_error(
            "cache-technical-terms-mismatch",
            lambda: STE.validate_cache_data(
                corrupt_project_terms,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        corrupt_integrity = copy.deepcopy(cache)
        corrupt_integrity["derived_content_sha256"] = "0" * 64
        expect_ste_error(
            "cache-content-mismatch",
            lambda: STE.validate_cache_data(
                corrupt_integrity,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        drifted_text_size = copy.deepcopy(cache)
        drifted_text_size["source"]["text_utf8_bytes"] += 1
        expect_ste_error(
            "cache-content-mismatch",
            lambda: STE.validate_cache_data(
                drifted_text_size,
                source_identity=source_identity,
                manifest=manifest,
                input_identities=identities,
                expected_technical_terms=cache["technical_terms"],
            ),
        )
        oversized_json = directory / "oversized-cache.json"
        oversized_json.write_bytes(b"{" + b" " * STE.MAX_CACHE_JSON_BYTES + b"}")
        expect_ste_error(
            "cache-too-large",
            lambda: STE._read_json_object(
                oversized_json,
                "cache",
                max_bytes=STE.MAX_CACHE_JSON_BYTES,
            ),
        )


def validate_semantic_mutations(index: dict[str, object]) -> None:
    profile = read(ENGINEERING)
    validate_policy_text(profile)
    weakened_profile = profile.replace(
        "All applicable writing rules and the controlled vocabulary\n"
        "are mandatory.",
        "Only returned rules are mandatory.",
    )
    try:
        validate_policy_text(weakened_profile)
    except AssertionError:
        pass
    else:
        raise AssertionError("full-applicability policy mutation was accepted")

    incomplete_location = copy.deepcopy(index)
    incomplete_location["families"][0]["source_location"].pop("pages")
    expect_ste_error(
        "retrieval-index-invalid",
        lambda: STE.validate_retrieval_index(incomplete_location),
    )
    missing_rule = copy.deepcopy(index)
    missing_rule["families"][0]["rule_ids"].remove("1.1")
    expect_ste_error(
        "retrieval-index-invalid",
        lambda: STE.validate_retrieval_index(missing_rule),
    )
    normative_payload = copy.deepcopy(index)
    normative_payload["families"][0]["rule_text"] = "prohibited payload"
    expect_ste_error(
        "retrieval-index-invalid",
        lambda: STE.validate_retrieval_index(normative_payload),
    )
    wrong_section = copy.deepcopy(index)
    wrong_section["families"][0]["source_location"]["section"] = "Section 9"
    expect_ste_error(
        "retrieval-index-invalid",
        lambda: STE.validate_retrieval_index(wrong_section),
    )
    incomplete_manifest = load_json(SOURCE_MANIFEST)
    incomplete_manifest.pop("size_bytes")
    expect_ste_error(
        "source-manifest-invalid",
        lambda: STE.validate_source_manifest(incomplete_manifest),
    )

    workflows = read(WORKFLOWS)
    validate_workflow_text(workflows)
    narrowed_workflow = workflows.replace(
        "They are not the\napplicable requirement set.",
        "They are the applicable requirement set.",
    )
    require(narrowed_workflow != workflows, "workflow narrowing fixture is stale")
    try:
        validate_workflow_text(narrowed_workflow)
    except AssertionError:
        pass
    else:
        raise AssertionError("lookup-as-complete workflow mutation was accepted")
    contradictory_workflow = (
        workflows
        + "\nLookup results are the complete applicable requirement set.\n"
    )
    try:
        validate_workflow_text(contradictory_workflow)
    except AssertionError:
        pass
    else:
        raise AssertionError("contradictory workflow addition was accepted")
    restarted_workflow = workflows.replace(
        "A `BLOCKED` verdict lets the implementing agent make the one correction set.",
        "A `BLOCKED`\nverdict requires another Documentation Review.",
    )
    require(restarted_workflow != workflows, "finite-cycle fixture is stale")
    try:
        validate_workflow_text(restarted_workflow)
    except AssertionError:
        pass
    else:
        raise AssertionError("a BLOCKED review restart was accepted")

    documents = load_tracked_markdown()
    competing_terms = dict(documents)
    competing_terms["reference/ENGINEERING_POLICY.md"] += (
        "\n## ASD-STE100 project terminology\n"
    )
    try:
        require_one_technical_term_owner(competing_terms)
    except AssertionError:
        pass
    else:
        raise AssertionError("competing technical-term owner mutation was accepted")
    guidance = dict(documents)
    guidance["AGENTS.md"] = read(AGENTS)
    guidance.update(
        {
            path.relative_to(ROOT).as_posix(): read(path)
            for path in sorted(SKILLS.glob("*/SKILL.md"))
        }
    )
    competing_root_owner = dict(guidance)
    competing_root_owner["AGENTS.md"] += "\n## ASD-STE100 project terminology\n"
    try:
        require_one_technical_term_owner(competing_root_owner)
    except AssertionError:
        pass
    else:
        raise AssertionError("root technical-term owner mutation was accepted")
    competing_skill_owner = dict(guidance)
    skill_path = ".agents/skills/tracktemplate-documentation-review/SKILL.md"
    competing_skill_owner[skill_path] += "\n## ASD-STE100 project terminology\n"
    try:
        require_one_technical_term_owner(competing_skill_owner)
    except AssertionError:
        pass
    else:
        raise AssertionError("skill technical-term owner mutation was accepted")
    skill_reference_path = (
        ".agents/skills/tracktemplate-documentation-review/"
        "references/document-ownership.md"
    )
    competing_skill_reference_owner = dict(guidance)
    competing_skill_reference_owner[skill_reference_path] += (
        "\n## ASD-STE100 project terminology\n"
    )
    try:
        require_one_technical_term_owner(competing_skill_reference_owner)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            "skill-reference technical-term owner mutation was accepted"
        )
    contradictory_skill_reference = dict(guidance)
    contradictory_skill_reference[skill_reference_path] += (
        "\nBypass the canonical application profile for short changes.\n"
    )
    try:
        for text in contradictory_skill_reference.values():
            validate_no_positive_assurance_claim(text)
    except AssertionError:
        pass
    else:
        raise AssertionError("skill-reference profile bypass mutation was accepted")
    duplicated_rules = dict(documents)
    duplicated_rules["reference/VALIDATION.md"] += "\n".join(
        "Rule 1.{} copied wording".format(number) for number in range(1, 10)
    )
    try:
        require_no_substantial_normative_duplication(duplicated_rules)
    except AssertionError:
        pass
    else:
        raise AssertionError("substantial normative duplication was accepted")
    duplicated_dictionary = dict(documents)
    duplicated_dictionary["reference/VALIDATION.md"] += "\n".join(
        "COPIEDWORD{} (v) copied meaning".format(number) for number in range(20)
    )
    try:
        require_no_substantial_normative_duplication(duplicated_dictionary)
    except AssertionError:
        pass
    else:
        raise AssertionError("substantial dictionary duplication was accepted")
    duplicated_skill_reference = dict(guidance)
    duplicated_skill_reference[skill_reference_path] += "\n".join(
        "Rule 1.{} copied wording".format(number) for number in range(1, 10)
    )
    try:
        require_no_substantial_normative_duplication(duplicated_skill_reference)
    except AssertionError:
        pass
    else:
        raise AssertionError("substantial skill-reference duplication was accepted")

    skills = {name: read(SKILLS / name / "SKILL.md") for name in SKILL_NAMES}
    validate_skill_routing(skills)
    unchecked_author = dict(skills)
    unchecked_author["tracktemplate-technical-author-lead"] = skills[
        "tracktemplate-technical-author-lead"
    ].replace(
        "When an assertion changes with the prose, preserve technical safeguards.",
        "Update assertion wording without checking its technical safeguards.",
    )
    require(unchecked_author != skills, "author safeguard fixture is stale")
    try:
        validate_skill_routing(unchecked_author)
    except AssertionError:
        pass
    else:
        raise AssertionError("an unchecked author assertion change was accepted")
    bypassed = dict(skills)
    bypassed["tracktemplate-quality-review"] = bypassed[
        "tracktemplate-quality-review"
    ].replace(
        "This skill does not review governance-document prose at any stage.",
        "This skill reviews governance-document prose at any stage.",
    )
    try:
        validate_skill_routing(bypassed)
    except AssertionError:
        pass
    else:
        raise AssertionError("skill retrieval bypass mutation was accepted")
    profile_bypassed = dict(skills)
    profile_bypassed["tracktemplate-documentation-alignment"] = profile_bypassed[
        "tracktemplate-documentation-alignment"
    ].replace(
        "../../../reference/ENGINEERING_POLICY.md#"
        "tt-doc-001-tracktemplate-technical-documentation-profile",
        "../../../reference/ENGINEERING_POLICY.md#removed-profile",
    )
    try:
        validate_skill_routing(profile_bypassed)
    except AssertionError:
        pass
    else:
        raise AssertionError("skill application-profile bypass mutation was accepted")
    contradictory_skill = dict(skills)
    contradictory_skill["tracktemplate-documentation-review"] += (
        "\nBypass the canonical application profile for short changes.\n"
    )
    try:
        validate_skill_routing(contradictory_skill)
    except AssertionError:
        pass
    else:
        raise AssertionError("contradictory skill bypass was accepted")

    validate_no_positive_assurance_claim(read(TOOL_PATH))
    try:
        validate_no_positive_assurance_claim(
            read(TOOL_PATH) + "\nSelected lookup results prove conformance.\n"
        )
    except AssertionError:
        pass
    else:
        raise AssertionError("automatic assurance overclaim mutation was accepted")
    try:
        validate_validation_text(
            read(VALIDATION) + "\nSelected lookup results prove conformance.\n"
        )
    except AssertionError:
        pass
    else:
        raise AssertionError("contradictory validation addition was accepted")

    learning = read(LEARNING)
    validate_lfe_text(learning)
    weakened_lfe = learning.replace(
        "optimise the access path, not the requirement set",
        "optimise the requirement set",
    )
    try:
        validate_lfe_text(weakened_lfe)
    except AssertionError:
        pass
    else:
        raise AssertionError("weakened LFE reusable rule was accepted")
    narrowed_reusable_lfe = learning.replace(
        "Bind the derived cache and retrieval index to the official source "
        "identity. Keep full applicability and targeted retrieval in different "
        "authority boundaries. Give only the source material that is necessary "
        "for the task.",
        "Use one retrieval method.",
    )
    try:
        validate_lfe_text(narrowed_reusable_lfe)
    except AssertionError:
        pass
    else:
        raise AssertionError("narrowed LFE reusable rule was accepted")
    competing_lfe = learning.replace(
        "use partial retrieval as evidence of partial conformance.",
        "use partial retrieval as evidence of partial conformance. This LFE owns the "
        "STE policy.",
    )
    try:
        validate_lfe_text(competing_lfe)
    except AssertionError:
        pass
    else:
        raise AssertionError("competing LFE policy-owner mutation was accepted")



def validate_documentation_lifecycle() -> None:
    source_manifest = {
        "issue": "9",
        "page_count": 434,
        "publication_date": "2025-01-15",
        "sha256": EXPECTED_SOURCE_SHA256,
        "size_bytes": EXPECTED_SOURCE_SIZE,
        "standard_id": "ASD-STE100",
    }

    def git(root: pathlib.Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(root: pathlib.Path, message: str) -> str:
        git(root, "add", "--all")
        git(
            root,
            "-c",
            "user.name=TrackTemplate Validation",
            "-c",
            "user.email=validation@example.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
        )
        return git(root, "rev-parse", "HEAD")

    def freeze_retained_review(
        *, baseline_revision: str, author_id: str,
        source_manifest: dict[str, object], root: pathlib.Path,
    ) -> tuple[pathlib.Path, dict[str, object]]:
        scope = STE._build_review_scope(
            baseline_revision=baseline_revision,
            candidate_revision=STE._lifecycle_head(root=root, require_clean=True),
            author_id=author_id, source_manifest=source_manifest,
            root=root, schema_version=1,
        )
        path, _digest = STE._write_lifecycle_json(
            root / "tmp" / STE.STE_REVIEW_SCOPE_DIR.name,
            "scope", scope, root=root,
        )
        return path, scope

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        (root / "reference" / "current").mkdir(parents=True)
        (root / "tmp").mkdir()
        (root / ".gitignore").write_text("tmp/\n", encoding="utf-8")
        guide = root / "reference" / "guide.md"
        untouched = root / "reference" / "untouched.md"
        decisions = root / "reference" / "current" / "gate-decisions.json"
        guide.write_text(
            "# First\n\nLegacy text.\n\n# Second\n\nUnchanged legacy text.\n",
            encoding="utf-8",
        )
        untouched.write_text("# Untouched\n\nLegacy text.\n", encoding="utf-8")
        decisions.write_text(
            json.dumps(
                {
                    "current_phase": 6,
                    "decisions": [
                        {"decision": "Keep the baseline.", "id": "D-001"}
                    ],
                    "schema_version": 1,
                    "updated_on": "2026-08-30",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        git(root, "init", "--quiet")
        baseline = commit(root, "legacy baseline")

        guide.write_text(
            "# First\n\nNew reviewed text.\n\n# Second\n\nUnchanged legacy text.\n",
            encoding="utf-8",
        )
        state_path = root / "reference" / "ste-review-state.json"
        state_path.write_bytes(STE._canonical_json_bytes(STE._empty_review_state()))

        def write_result(name: str, value: dict[str, object]) -> pathlib.Path:
            path = root / "tmp" / name
            path.write_bytes(STE._canonical_json_bytes(value))
            return path

        def write_raw_result(name: str, value: bytes) -> pathlib.Path:
            path = root / "tmp" / name
            path.write_bytes(value)
            return path

        def blocker_for(
            document: dict[str, object],
            unit: dict[str, object],
            *,
            finding: str,
            rule_ids: list[str],
        ) -> dict[str, object]:
            return {
                "finding": finding,
                "path": document["path"],
                "rule_ids": rule_ids,
                "unit": {
                    "end_byte": unit["end_byte"],
                    "sha256": unit["sha256"],
                    "side": unit["side"],
                    "start_byte": unit["start_byte"],
                },
            }

        candidate_one = commit(root, "first material edit")
        scope_path, scope_one = freeze_retained_review(
            baseline_revision=baseline,
            author_id="fixture-author",
            source_manifest=source_manifest,
            root=root,
        )
        require(
            scope_one["candidate"]["candidate_revision"] == candidate_one,
            "the frozen scope did not bind the exact candidate",
        )
        document_one = scope_one["documents"][0]
        require(
            document_one["mode"] == "complete-document",
            "a retained legacy scope lost its complete-document meaning",
        )
        require(
            all(item["path"] != "reference/untouched.md" for item in scope_one["documents"]),
            "an untouched legacy document entered the review scope",
        )
        result_one = {
            "blocker_set_complete": True,
            "blockers": [],
            "corrections": [],
            "full_applicability_considered": True,
            "independent": True,
            "issue9_source_sha256": EXPECTED_SOURCE_SHA256,
            "result": "ACCEPT",
            "reviewer_id": "fixture-documentation-reviewer",
            "schema_version": 2,
            "scope_sha256": scope_one["scope_sha256"],
        }
        result_one_bytes = STE._canonical_json_bytes(result_one)
        blockers_member = b'  "blockers": [],\n'
        require(
            result_one_bytes.count(blockers_member) == 1,
            "the duplicate-result fixture cannot locate blockers",
        )
        duplicate_result_member = result_one_bytes.replace(
            blockers_member,
            b'  "blockers": [{}],\n  "blockers": [],\n',
            1,
        )
        expect_ste_error(
            "ste-lifecycle-record-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_raw_result(
                    "duplicate-result-member.json",
                    duplicate_result_member,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        schema_one_result = copy.deepcopy(result_one)
        schema_one_result.pop("blocker_set_complete")
        schema_one_result.pop("blockers")
        schema_one_result["schema_version"] = 1
        expect_ste_error(
            "ste-review-result-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "schema-one-result.json",
                    schema_one_result,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        false_blocker_attestation = copy.deepcopy(result_one)
        false_blocker_attestation["blocker_set_complete"] = False
        expect_ste_error(
            "ste-review-blocker-set-incomplete",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "false-blocker-attestation.json",
                    false_blocker_attestation,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        missing_blocker_attestation = copy.deepcopy(result_one)
        missing_blocker_attestation.pop("blocker_set_complete")
        expect_ste_error(
            "ste-review-result-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "missing-blocker-attestation.json",
                    missing_blocker_attestation,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        accept_with_blocker = copy.deepcopy(result_one)
        accept_with_blocker["blockers"] = [
            blocker_for(
                document_one,
                document_one["units"][0],
                finding="The accepted result contains a blocker.",
                rule_ids=["1.1"],
            )
        ]
        expect_ste_error(
            "ste-review-blockers-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "accept-with-blocker.json",
                    accept_with_blocker,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        tampered_scope = copy.deepcopy(scope_one)
        tampered_scope["author_id"] = "tampered-author"
        expect_ste_error(
            "ste-review-scope-invalid",
            lambda: STE.record_documentation_review(
                scope_path=write_result("tampered-scope.json", tampered_scope),
                result_path=write_result("scope-result.json", result_one),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        tampered_source = copy.deepcopy(source_manifest)
        tampered_source["sha256"] = "0" * 64
        expect_ste_error(
            "ste-review-scope-changed",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("source-result.json", result_one),
                source_manifest=tampered_source,
                root=root,
            ),
        )
        wrong_scope = copy.deepcopy(result_one)
        wrong_scope["scope_sha256"] = "0" * 64
        expect_ste_error(
            "ste-review-result-scope-mismatch",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("wrong-scope.json", wrong_scope),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        wrong_source = copy.deepcopy(result_one)
        wrong_source["issue9_source_sha256"] = "0" * 64
        expect_ste_error(
            "ste-review-result-source-mismatch",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("wrong-source.json", wrong_source),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        same_reviewer = copy.deepcopy(result_one)
        same_reviewer["reviewer_id"] = "fixture-author"
        expect_ste_error(
            "ste-review-result-not-independent",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("same-reviewer.json", same_reviewer),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        incomplete_review = copy.deepcopy(result_one)
        incomplete_review["full_applicability_considered"] = False
        expect_ste_error(
            "ste-review-result-incomplete",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "incomplete-review.json",
                    incomplete_review,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        invalid_verdict = copy.deepcopy(result_one)
        invalid_verdict["result"] = "REVIEW_AGAIN"
        expect_ste_error(
            "ste-review-result-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "invalid-verdict.json",
                    invalid_verdict,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        accept_with_correction = copy.deepcopy(result_one)
        accept_with_correction["corrections"] = [{}]
        expect_ste_error(
            "ste-review-corrections-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "accept-with-correction.json",
                    accept_with_correction,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        approved_without_correction = copy.deepcopy(result_one)
        approved_without_correction["result"] = (
            "APPROVED_WITH_EXACT_CORRECTIONS"
        )
        expect_ste_error(
            "ste-review-corrections-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result(
                    "approved-without-correction.json",
                    approved_without_correction,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )

        result_one_path = write_result("result-one.json", result_one)
        receipt_one, proposal_one, _recorded_one = STE.record_documentation_review(
            scope_path=scope_path,
            result_path=result_one_path,
            source_manifest=source_manifest,
            root=root,
        )
        require(proposal_one is not None, "ACCEPT did not create a state proposal")
        tampered_receipt = load_json(receipt_one)
        tampered_receipt["candidate_tree"] = "0" * 40
        expect_ste_error(
            "ste-review-receipt-invalid",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path,
                receipt_path=write_result(
                    "tampered-receipt.json",
                    tampered_receipt,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        expect_ste_error(
            "ste-final-state-mismatch",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path,
                receipt_path=receipt_one,
                source_manifest=source_manifest,
                root=root,
            ),
        )
        state_path.write_bytes(proposal_one.read_bytes())
        untouched_bytes = untouched.read_bytes()
        untouched.write_text(
            "# Untouched\n\nUnreviewed post-review text.\n",
            encoding="utf-8",
        )
        commit(root, "unreviewed post-review mutation")
        expect_ste_error(
            "ste-final-unreviewed-mutation",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path,
                receipt_path=receipt_one,
                source_manifest=source_manifest,
                root=root,
            ),
        )
        untouched.write_bytes(untouched_bytes)
        accepted_one = commit(root, "accepted baseline")
        final_one = STE.validate_final_review_state(
            scope_path=scope_path,
            receipt_path=receipt_one,
            source_manifest=source_manifest,
            root=root,
        )
        require(
            final_one["candidate_revision"] == candidate_one
            and final_one["final_revision"] == accepted_one
            and final_one["issue9_source_sha256"] == EXPECTED_SOURCE_SHA256
            and final_one["result"] == "ACCEPT"
            and final_one["scope_sha256"] == scope_one["scope_sha256"]
            and final_one["status"]
            == "reviewed-state-present-and-no-unreviewed-prose-mutation",
            "final validation did not bind the exact accepted revision",
        )
        state_one = load_json(state_path)
        require(
            len(state_one["documents"]) == 1,
            "the state register did not record the reviewed document",
        )
        require(
            "units" not in state_one["documents"][0],
            "the state register persisted logical-unit state",
        )
        require(
            set(state_one["documents"][0])
            == {
                "accepted_blob",
                "accepted_sha256",
                "issue9_source",
                "path",
                "review_receipt",
            }
            and state_one["documents"][0]["path"] == "reference/guide.md",
            "the state register is not a document-level identity record",
        )

        guide.write_text(
            "# First\n\nNew text with bounded fault.\n\n"
            "# Second\n\nUnchanged legacy text.\n",
            encoding="utf-8",
        )
        candidate_two = commit(root, "second material edit")
        scope_two_path, scope_two = freeze_retained_review(
            baseline_revision=accepted_one,
            author_id="fixture-author",
            source_manifest=source_manifest,
            root=root,
        )
        require(
            scope_two["candidate"]["candidate_revision"] == candidate_two,
            "the changed-unit scope did not bind the second candidate",
        )
        document_two = scope_two["documents"][0]
        require(
            document_two["mode"] == "changed-logical-units",
            "an accepted document did not use a changed-unit scope",
        )
        unit_text = "\n".join(str(unit["text"]) for unit in document_two["units"])
        require(
            "# First" in unit_text and "# Second" not in unit_text,
            "the changed-unit scope re-reviewed unchanged accepted prose",
        )
        candidate_bytes = guide.read_bytes()
        start = candidate_bytes.index(b"bounded fault")
        preimage = "bounded fault"
        result_two = {
            "blocker_set_complete": True,
            "blockers": [],
            "corrections": [
                {
                    "end_byte": start + len(preimage.encode("utf-8")),
                    "path": "reference/guide.md",
                    "preimage": preimage,
                    "preimage_sha256": hashlib.sha256(
                        preimage.encode("utf-8")
                    ).hexdigest(),
                    "replacement": "approved wording",
                    "start_byte": start,
                }
            ],
            "full_applicability_considered": True,
            "independent": True,
            "issue9_source_sha256": EXPECTED_SOURCE_SHA256,
            "result": "APPROVED_WITH_EXACT_CORRECTIONS",
            "reviewer_id": "fixture-documentation-reviewer",
            "schema_version": 2,
            "scope_sha256": scope_two["scope_sha256"],
        }
        approved_with_blocker = copy.deepcopy(result_two)
        approved_with_blocker["blockers"] = [
            blocker_for(
                document_two,
                document_two["units"][0],
                finding="The correction result contains a blocker.",
                rule_ids=["1.1"],
            )
        ]
        expect_ste_error(
            "ste-review-blockers-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_two_path,
                result_path=write_result(
                    "approved-with-blocker.json",
                    approved_with_blocker,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        correction_outside_scope = copy.deepcopy(result_two)
        correction_outside_scope["corrections"][0]["path"] = (
            "reference/untouched.md"
        )
        expect_ste_error(
            "ste-review-corrections-outside-scope",
            lambda: STE.record_documentation_review(
                scope_path=scope_two_path,
                result_path=write_result(
                    "correction-outside-scope.json",
                    correction_outside_scope,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        wrong_preimage = copy.deepcopy(result_two)
        wrong_preimage["corrections"][0]["preimage_sha256"] = "0" * 64
        expect_ste_error(
            "ste-review-correction-preimage-mismatch",
            lambda: STE.record_documentation_review(
                scope_path=scope_two_path,
                result_path=write_result(
                    "wrong-correction-preimage.json",
                    wrong_preimage,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        overlapping_corrections = copy.deepcopy(result_two)
        overlap_preimage = preimage[1:]
        overlap = copy.deepcopy(overlapping_corrections["corrections"][0])
        overlap["start_byte"] = start + 1
        overlap["preimage"] = overlap_preimage
        overlap["preimage_sha256"] = hashlib.sha256(
            overlap_preimage.encode("utf-8")
        ).hexdigest()
        overlap["replacement"] = "other reviewed wording"
        overlapping_corrections["corrections"].append(overlap)
        expect_ste_error(
            "ste-review-corrections-overlap",
            lambda: STE.record_documentation_review(
                scope_path=scope_two_path,
                result_path=write_result(
                    "overlapping-corrections.json",
                    overlapping_corrections,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )

        result_two_path = write_result("result-two.json", result_two)
        receipt_two, proposal_two, _recorded_two = STE.record_documentation_review(
            scope_path=scope_two_path,
            result_path=result_two_path,
            source_manifest=source_manifest,
            root=root,
        )
        require(
            proposal_two is not None,
            "an approved exact correction did not create a state proposal",
        )
        guide.write_bytes(
            candidate_bytes[:start]
            + b"approved wording"
            + candidate_bytes[start + len(preimage.encode("utf-8")) :]
        )
        corrected_bytes = guide.read_bytes()
        state_path.write_bytes(proposal_two.read_bytes())
        guide.write_bytes(corrected_bytes + b"\nUnreviewed wording.\n")
        commit(root, "unreviewed wording after exact correction")
        expect_ste_error(
            "ste-final-reviewed-bytes-mismatch",
            lambda: STE.validate_final_review_state(
                scope_path=scope_two_path,
                receipt_path=receipt_two,
                source_manifest=source_manifest,
                root=root,
            ),
        )
        guide.write_bytes(corrected_bytes)
        accepted_two = commit(root, "exact correction and state")
        final_two = STE.validate_final_review_state(
            scope_path=scope_two_path,
            receipt_path=receipt_two,
            source_manifest=source_manifest,
            root=root,
        )
        require(
            final_two["result"] == "APPROVED_WITH_EXACT_CORRECTIONS"
            and final_two["final_revision"] == accepted_two,
            "final validation did not prove the exactly corrected state",
        )

        guide.write_text(
            "# First\n\nNew text with approved wording.\n",
            encoding="utf-8",
        )
        decision_value = json.loads(decisions.read_text(encoding="utf-8"))
        decision_value["updated_on"] = "2026-08-31"
        decision_value["decisions"][0]["decision"] = "Use the changed decision."
        decisions.write_text(
            json.dumps(decision_value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        commit(root, "deletion and register change")
        scope_three_path, scope_three = freeze_retained_review(
            baseline_revision=accepted_two,
            author_id="fixture-author",
            source_manifest=source_manifest,
            root=root,
        )
        guide_scope = next(
            item for item in scope_three["documents"] if item["path"] == "reference/guide.md"
        )
        require(
            any(unit["side"] == "baseline" for unit in guide_scope["units"]),
            "deletion-only prose did not preserve the baseline logical unit",
        )
        decision_scope = next(
            item
            for item in scope_three["documents"]
            if item["path"] == "reference/current/gate-decisions.json"
        )
        require(
            {unit["identifier"] for unit in decision_scope["units"]} == {"D-001"},
            "canonical JSON scope did not select the complete changed object",
        )

        scope_units = [
            (document, unit)
            for document in scope_three["documents"]
            for unit in document["units"]
        ]
        blocker_units: list[tuple[dict[str, object], dict[str, object]]] = []
        blocker_sides: set[object] = set()
        for document, unit in scope_units:
            if unit["side"] not in blocker_sides:
                blocker_units.append((document, unit))
                blocker_sides.add(unit["side"])
        require(
            blocker_sides == {"baseline", "candidate"},
            "the BLOCKED fixture does not contain both frozen unit sides",
        )
        ordered_blockers = [
            blocker_for(
                blocker_units[0][0],
                blocker_units[0][1],
                finding="The first frozen logical unit does not conform.",
                rule_ids=["1.1"],
            ),
            blocker_for(
                blocker_units[1][0],
                blocker_units[1][1],
                finding="The second frozen logical unit does not conform.",
                rule_ids=["1.2"],
            ),
        ]
        blocked = copy.deepcopy(result_two)
        blocked["blockers"] = ordered_blockers
        blocked["result"] = "BLOCKED"
        blocked["corrections"] = []
        blocked["scope_sha256"] = scope_three["scope_sha256"]

        blocked_bytes = STE._canonical_json_bytes(blocked)
        unit_member = b'      "unit": {\n        "end_byte": '
        require(
            blocked_bytes.count(unit_member) == len(blocked["blockers"]),
            "the duplicate-unit fixture cannot locate frozen units",
        )
        duplicate_unit_member = blocked_bytes.replace(
            unit_member,
            b'      "unit": {\n        "end_byte": 0,\n'
            b'        "end_byte": ',
            1,
        )
        expect_ste_error(
            "ste-lifecycle-record-invalid",
            lambda: STE.record_documentation_review(
                scope_path=scope_three_path,
                result_path=write_raw_result(
                    "duplicate-unit-member.json",
                    duplicate_unit_member,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )

        def expect_invalid_blocked(
            name: str,
            code: str,
            value: dict[str, object],
        ) -> None:
            expect_ste_error(
                code,
                lambda: STE.record_documentation_review(
                    scope_path=scope_three_path,
                    result_path=write_result(name, value),
                    source_manifest=source_manifest,
                    root=root,
                ),
            )

        empty_blocked = copy.deepcopy(blocked)
        empty_blocked["blockers"] = []
        expect_invalid_blocked(
            "empty-blocked.json",
            "ste-review-blockers-invalid",
            empty_blocked,
        )
        unattested_blocked = copy.deepcopy(blocked)
        unattested_blocked["blocker_set_complete"] = False
        expect_invalid_blocked(
            "unattested-blocked.json",
            "ste-review-blocker-set-incomplete",
            unattested_blocked,
        )
        malformed_blocker = copy.deepcopy(blocked)
        malformed_blocker["blockers"] = [{}]
        expect_invalid_blocked(
            "malformed-blocker.json",
            "ste-review-blockers-invalid",
            malformed_blocker,
        )
        blocker_outside_scope = copy.deepcopy(blocked)
        blocker_outside_scope["blockers"][0]["path"] = (
            "reference/untouched.md"
        )
        expect_invalid_blocked(
            "blocker-outside-scope.json",
            "ste-review-blocker-outside-scope",
            blocker_outside_scope,
        )
        tampered_blocker_unit = copy.deepcopy(blocked)
        tampered_blocker_unit["blockers"][0]["unit"]["sha256"] = "0" * 64
        expect_invalid_blocked(
            "tampered-blocker-unit.json",
            "ste-review-blocker-outside-scope",
            tampered_blocker_unit,
        )
        invalid_blocker_rule = copy.deepcopy(blocked)
        invalid_blocker_rule["blockers"][0]["rule_ids"] = ["10.1"]
        expect_invalid_blocked(
            "invalid-blocker-rule.json",
            "ste-review-blockers-invalid",
            invalid_blocker_rule,
        )
        unsorted_blocker_rules = copy.deepcopy(blocked)
        unsorted_blocker_rules["blockers"][0]["rule_ids"] = ["1.2", "1.1"]
        expect_invalid_blocked(
            "unsorted-blocker-rules.json",
            "ste-review-blockers-invalid",
            unsorted_blocker_rules,
        )
        duplicate_blocker_rules = copy.deepcopy(blocked)
        duplicate_blocker_rules["blockers"][0]["rule_ids"] = ["1.1", "1.1"]
        expect_invalid_blocked(
            "duplicate-blocker-rules.json",
            "ste-review-blockers-invalid",
            duplicate_blocker_rules,
        )
        unordered_blockers = copy.deepcopy(blocked)
        unordered_blockers["blockers"].reverse()
        expect_invalid_blocked(
            "unordered-blockers.json",
            "ste-review-blockers-invalid",
            unordered_blockers,
        )
        duplicate_blockers = copy.deepcopy(blocked)
        duplicate_blockers["blockers"] = [
            copy.deepcopy(ordered_blockers[0]),
            copy.deepcopy(ordered_blockers[0]),
        ]
        expect_invalid_blocked(
            "duplicate-blockers.json",
            "ste-review-blockers-invalid",
            duplicate_blockers,
        )

        blocked_path = write_result("blocked.json", blocked)
        blocked_result_bytes = blocked_path.read_bytes()
        _blocked_receipt, blocked_proposal, _blocked_result = (
            STE.record_documentation_review(
                scope_path=scope_three_path,
                result_path=blocked_path,
                source_manifest=source_manifest,
                root=root,
            )
        )
        blocked_receipt_value = load_json(_blocked_receipt)
        receipt_result = {
            key: blocked_receipt_value[key]
            for key in blocked
        }
        returned_result = {
            key: _blocked_result[key]
            for key in blocked
        }
        require(
            _blocked_receipt.read_bytes()
            == STE._canonical_json_bytes(_blocked_result)
            and STE._canonical_json_bytes(returned_result)
            == blocked_result_bytes
            and STE._canonical_json_bytes(receipt_result) == blocked_result_bytes,
            "the BLOCKED receipt did not preserve the complete result value",
        )
        require(blocked_proposal is None, "BLOCKED created an accepted state proposal")
        schema_one_receipt = copy.deepcopy(blocked_receipt_value)
        schema_one_receipt.pop("blocker_set_complete")
        schema_one_receipt.pop("blockers")
        schema_one_receipt["schema_version"] = 1
        expect_ste_error(
            "ste-review-receipt-invalid",
            lambda: STE.validate_final_review_state(
                scope_path=scope_three_path,
                receipt_path=write_result(
                    "schema-one-blocked-receipt.json",
                    schema_one_receipt,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        changed_blocked_receipt = copy.deepcopy(blocked_receipt_value)
        changed_blocked_receipt["blockers"][0]["finding"] = (
            "A changed finding that is otherwise valid."
        )
        changed_receipt_dir = root / "tmp" / "changed-receipt"
        changed_receipt_dir.mkdir()
        changed_receipt_path = changed_receipt_dir / _blocked_receipt.name
        changed_receipt_path.write_bytes(
            STE._canonical_json_bytes(changed_blocked_receipt)
        )
        expect_ste_error(
            "ste-review-receipt-invalid",
            lambda: STE.validate_final_review_state(
                scope_path=scope_three_path,
                receipt_path=changed_receipt_path,
                source_manifest=source_manifest,
                root=root,
            ),
        )
        tampered_blocked_receipt = copy.deepcopy(blocked_receipt_value)
        tampered_blocked_receipt["blockers"] = []
        expect_ste_error(
            "ste-review-blockers-invalid",
            lambda: STE.validate_final_review_state(
                scope_path=scope_three_path,
                receipt_path=write_result(
                    "tampered-blocked-receipt.json",
                    tampered_blocked_receipt,
                ),
                source_manifest=source_manifest,
                root=root,
            ),
        )
        expect_ste_error(
            "ste-review-blocked",
            lambda: STE.validate_final_review_state(
                scope_path=scope_three_path,
                receipt_path=_blocked_receipt,
                source_manifest=source_manifest,
                root=root,
            ),
        )


def validate_finite_documentation_lifecycle() -> None:
    """Prove one blocked review can close without a replacement verdict."""
    source_manifest = {
        "issue": "9",
        "page_count": 434,
        "publication_date": "2025-01-15",
        "sha256": EXPECTED_SOURCE_SHA256,
        "size_bytes": EXPECTED_SOURCE_SIZE,
        "standard_id": "ASD-STE100",
    }

    def git(root: pathlib.Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def commit(root: pathlib.Path, message: str) -> str:
        git(root, "add", "--all")
        git(
            root, "-c", "user.name=TrackTemplate Validation",
            "-c", "user.email=validation@example.invalid",
            "commit", "--quiet", "-m", message,
        )
        return git(root, "rev-parse", "HEAD")

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        (root / "reference").mkdir()
        (root / "tmp").mkdir()
        (root / ".gitignore").write_text("tmp/\n", encoding="utf-8")
        guide = root / "reference" / "guide.md"
        state_path = root / "reference" / "ste-review-state.json"
        guide.write_text(
            "# Changed\n\nKeep the old instruction.\n\n"
            "# Also changed\n\nKeep the former description.\n\n"
            "# Unchanged\n\nKeep the untouched legacy instruction.\n",
            encoding="utf-8",
        )
        state_path.write_bytes(STE._canonical_json_bytes(STE._empty_review_state()))
        git(root, "init", "--quiet")
        baseline = commit(root, "baseline")
        candidate_bytes = guide.read_bytes().replace(
            b"old instruction", b"unclear instruction"
        ).replace(b"former description", b"current description")
        guide.write_bytes(candidate_bytes)
        candidate = commit(root, "one author candidate")
        scope_path, scope = STE.freeze_documentation_review(
            baseline_revision=baseline, author_id="author",
            source_manifest=source_manifest, root=root,
        )
        document = scope["documents"][0]
        start = candidate_bytes.index(b"unclear instruction")
        preimage = "unclear instruction"
        candidate_unit = next(
            unit for unit in document["units"]
            if unit["side"] == "candidate"
            and unit["start_byte"] <= start < unit["end_byte"]
        )
        result = {
            "blocker_set_complete": True,
            "blockers": [{
                "finding": "Replace the unclear instruction with the exact correction.",
                "path": "reference/guide.md",
                "rule_ids": ["1.1"],
                "unit": {
                    key: candidate_unit[key]
                    for key in ("end_byte", "sha256", "side", "start_byte")
                },
            }],
            "corrections": [{
                "end_byte": start + len(preimage),
                "path": "reference/guide.md",
                "preimage": preimage,
                "preimage_sha256": hashlib.sha256(preimage.encode()).hexdigest(),
                "replacement": "clear instruction",
                "start_byte": start,
            }],
            "full_applicability_considered": True,
            "independent": True,
            "issue9_source_sha256": EXPECTED_SOURCE_SHA256,
            "result": "BLOCKED",
            "reviewer_id": "independent-reviewer",
            "schema_version": 3,
            "scope_sha256": scope["scope_sha256"],
        }

        def write_result(name: str, value: dict[str, object]) -> pathlib.Path:
            path = root / "tmp" / name
            path.write_bytes(STE._canonical_json_bytes(value))
            return path

        result_path = write_result("one-review.json", result)
        downgraded = copy.deepcopy(result)
        downgraded["schema_version"] = 2
        downgraded["corrections"] = []
        expect_ste_error(
            "ste-review-result-schema-mismatch",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("downgraded-review.json", downgraded),
                source_manifest=source_manifest, root=root,
            ),
        )
        incomplete = copy.deepcopy(result)
        other_unit = next(
            unit for unit in document["units"]
            if unit["side"] == "candidate"
            and "current description" in unit["text"]
        )
        other_blocker = copy.deepcopy(result["blockers"][0])
        other_blocker["unit"] = {
            key: other_unit[key]
            for key in ("end_byte", "sha256", "side", "start_byte")
        }
        incomplete["blockers"].append(other_blocker)
        expect_ste_error(
            "ste-review-corrections-incomplete",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("incomplete-adjustment.json", incomplete),
                source_manifest=source_manifest, root=root,
            ),
        )
        receipt_path, proposal_path, receipt = STE.record_documentation_review(
            scope_path=scope_path, result_path=result_path,
            source_manifest=source_manifest, root=root,
        )
        require(proposal_path is not None, "a correctable BLOCKED review cannot close")
        require(
            receipt["result"] == "BLOCKED" and receipt["blockers"] == result["blockers"],
            "recording the adjustment changed the original review verdict or findings",
        )
        require(
            scope["schema_version"] == 2
            and document["mode"] == "changed-logical-units"
            and all("untouched legacy" not in unit["text"] for unit in document["units"]),
            "the finite review expanded into unchanged legacy prose",
        )
        old_scope = STE._build_review_scope(
            baseline_revision=baseline, candidate_revision=candidate,
            author_id="author", source_manifest=source_manifest,
            root=root, schema_version=1,
        )
        require(
            old_scope["documents"][0]["mode"] == "complete-document",
            "retained schema-1 scope reconstruction changed",
        )
        legacy_scope_path, _digest = STE._write_lifecycle_json(
            root / "tmp" / STE.STE_REVIEW_SCOPE_DIR.name,
            "scope", old_scope, root=root,
        )
        legacy_result = copy.deepcopy(result)
        legacy_result.update(
            schema_version=2, result="ACCEPT", blockers=[], corrections=[],
            scope_sha256=old_scope["scope_sha256"],
        )
        expect_ste_error(
            "ste-review-already-recorded",
            lambda: STE.record_documentation_review(
                scope_path=legacy_scope_path,
                result_path=write_result("legacy-reset.json", legacy_result),
                source_manifest=source_manifest, root=root,
            ),
        )
        legacy_receipt_path, _digest = STE._write_lifecycle_json(
            root / "tmp" / STE.STE_REVIEW_RESULT_DIR.name,
            "review", STE._review_receipt(legacy_result, scope=old_scope),
            root=root,
        )
        expect_ste_error(
            "ste-review-already-recorded",
            lambda: STE.validate_final_review_state(
                scope_path=legacy_scope_path, receipt_path=legacy_receipt_path,
                source_manifest=source_manifest, root=root,
            ),
        )
        require(
            STE.record_documentation_review(
                scope_path=scope_path, result_path=result_path,
                source_manifest=source_manifest, root=root,
            ) == (receipt_path, proposal_path, receipt),
            "an identical record-review retry was not idempotent",
        )
        second_review = copy.deepcopy(result)
        second_review["reviewer_id"] = "another-reviewer"
        expect_ste_error(
            "ste-review-already-recorded",
            lambda: STE.record_documentation_review(
                scope_path=scope_path,
                result_path=write_result("second-review.json", second_review),
                source_manifest=source_manifest, root=root,
            ),
        )
        expect_ste_error(
            "ste-review-already-recorded",
            lambda: STE.freeze_documentation_review(
                baseline_revision=baseline, author_id="renamed-author",
                source_manifest=source_manifest, root=root,
            ),
        )
        expect_ste_error(
            "ste-final-reviewed-bytes-mismatch",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path, receipt_path=receipt_path,
                source_manifest=source_manifest, root=root,
            ),
        )
        proposal_bytes = proposal_path.read_bytes()
        proposal = load_json(proposal_path)
        require(
            proposal["schema_version"] == 2
            and proposal["documents"][0]["lifecycle_status"] == "locked"
            and proposal["documents"][0]["review_result"] == "BLOCKED",
            "the controlled baseline conflates closure with linguistic acceptance",
        )
        invalid_state = copy.deepcopy(proposal)
        invalid_state["documents"][0]["review_result"] = []
        expect_ste_error(
            "ste-review-state-invalid",
            lambda: STE._validate_review_state(invalid_state),
        )
        invalid_state = copy.deepcopy(proposal)
        invalid_state["schema_version"] = 1
        expect_ste_error(
            "ste-review-state-invalid",
            lambda: STE._validate_review_state(invalid_state),
        )
        final_bytes = candidate_bytes.replace(
            b"unclear instruction", b"clear instruction"
        )
        guide.write_bytes(final_bytes)
        adjusted = commit(root, "one adjustment")
        expect_ste_error(
            "ste-review-cycle-restart",
            lambda: STE.freeze_documentation_review(
                baseline_revision=baseline, author_id="author",
                source_manifest=source_manifest, root=root,
            ),
        )
        expect_ste_error(
            "ste-review-cycle-restart",
            lambda: STE.freeze_documentation_review(
                baseline_revision=candidate, author_id="author",
                source_manifest=source_manifest, root=root,
            ),
        )
        require(adjusted != candidate, "the adjustment did not change the candidate")
        state_path.write_bytes(proposal_bytes)
        locked = commit(root, "record locked baseline")
        final = STE.validate_final_review_state(
            scope_path=scope_path, receipt_path=receipt_path,
            source_manifest=source_manifest, root=root,
        )
        require(
            final["result"] == "BLOCKED"
            and final["status"] == "locked-and-deterministically-validated"
            and final["final_revision"] == locked,
            "one adjusted BLOCKED review did not complete honestly",
        )
        completion_path = (
            root / "tmp" / STE.STE_REVIEW_RESULT_DIR.name
            / "completion-{}.json".format(candidate)
        )
        preserved_completion = completion_path.read_bytes()
        preserved_receipt = receipt_path.read_bytes()
        guide.write_bytes(final_bytes.replace(b"clear", b"different"))
        commit(root, "unauthorised second wording adjustment")
        expect_ste_error(
            "ste-final-reviewed-bytes-mismatch",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path, receipt_path=receipt_path,
                source_manifest=source_manifest, root=root,
            ),
        )
        guide.write_bytes(final_bytes)
        false_acceptance = copy.deepcopy(proposal)
        false_acceptance["documents"][0]["review_result"] = "ACCEPT"
        state_path.write_bytes(STE._canonical_json_bytes(false_acceptance))
        commit(root, "false acceptance claim")
        expect_ste_error(
            "ste-final-state-mismatch",
            lambda: STE.validate_final_review_state(
                scope_path=scope_path, receipt_path=receipt_path,
                source_manifest=source_manifest, root=root,
            ),
        )
        state_path.write_bytes(proposal_bytes)
        corrected_proof = commit(root, "restore exact locked state")
        STE.validate_final_review_state(
            scope_path=scope_path, receipt_path=receipt_path,
            source_manifest=source_manifest, root=root,
        )
        require(
            receipt_path.read_bytes() == preserved_receipt,
            "deterministic validation changed the original review receipt",
        )
        require(
            completion_path.read_bytes() == preserved_completion,
            "a later deterministic retry rewrote the first completed proof",
        )
        guide.write_bytes(final_bytes.replace(b"clear", b"new factual"))
        commit(root, "later distinct work after controlled baseline")
        later_scope_path, later_scope = STE.freeze_documentation_review(
            baseline_revision=corrected_proof, author_id="author",
            source_manifest=source_manifest, root=root,
        )
        unresolved = copy.deepcopy(result)
        unresolved["scope_sha256"] = later_scope["scope_sha256"]
        unresolved["corrections"] = []
        later_unit = next(
            unit for unit in later_scope["documents"][0]["units"]
            if unit["side"] == "candidate"
        )
        unresolved["blockers"][0]["unit"] = {
            key: later_unit[key]
            for key in ("end_byte", "sha256", "side", "start_byte")
        }
        unresolved["blockers"][0]["finding"] = "The subject owner must resolve the technical fact."
        unresolved_receipt, unresolved_proposal, _result = STE.record_documentation_review(
            scope_path=later_scope_path,
            result_path=write_result("unresolved-fact.json", unresolved),
            source_manifest=source_manifest, root=root,
        )
        require(unresolved_proposal is None, "an unresolved fact created a completion proposal")
        expect_ste_error(
            "ste-review-blocked",
            lambda: STE.validate_final_review_state(
                scope_path=later_scope_path, receipt_path=unresolved_receipt,
                source_manifest=source_manifest, root=root,
            ),
        )

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        (root / "reference").mkdir()
        (root / "tmp").mkdir()
        (root / ".gitignore").write_text("tmp/\n", encoding="utf-8")
        guide = root / "reference" / "guide.md"
        state_path = root / "reference" / "ste-review-state.json"
        old_bytes = b"# Closed\n\nOriginal instruction.\n\n# Current\n\nOld text.\n"
        guide.write_bytes(old_bytes)
        state_path.write_bytes(STE._canonical_json_bytes(STE._empty_review_state()))
        git(root, "init", "--quiet")
        commit(root, "old accepted text")
        state_path.write_bytes(STE._canonical_json_bytes({
            "schema_version": 1,
            "documents": [{
                "accepted_blob": "sha1:" + STE._lifecycle_blob_oid(old_bytes),
                "accepted_sha256": "sha256:" + hashlib.sha256(old_bytes).hexdigest(),
                "issue9_source": "sha256:" + EXPECTED_SOURCE_SHA256,
                "path": "reference/guide.md",
                "review_receipt": "sha256:" + "a" * 64,
            }],
        }))
        closed_bytes = old_bytes.replace(b"Original", b"Owner-closed")
        guide.write_bytes(closed_bytes)
        closed_baseline = commit(root, "owner-closed work with retained old state")
        guide.write_bytes(closed_bytes.replace(b"Old text", b"New text"))
        commit(root, "new bounded documentation task")
        scope_path, scope = STE.freeze_documentation_review(
            baseline_revision=closed_baseline, author_id="author",
            source_manifest=source_manifest, root=root,
        )
        units = scope["documents"][0]["units"]
        require(
            all("Owner-closed" not in unit["text"] for unit in units)
            and any("New text" in unit["text"] for unit in units),
            "an older state identity reopened already closed baseline prose",
        )
        blocked = copy.deepcopy(result)
        blocked["scope_sha256"] = scope["scope_sha256"]
        unit = next(unit for unit in units if unit["side"] == "candidate")
        blocked["blockers"][0]["unit"] = {
            key: unit[key]
            for key in ("end_byte", "sha256", "side", "start_byte")
        }
        start = guide.read_bytes().index(b"New text")
        blocked["corrections"] = [{
            "path": "reference/guide.md", "start_byte": start,
            "end_byte": start + len(b"New text"), "preimage": "New text",
            "preimage_sha256": hashlib.sha256(b"New text").hexdigest(),
            "replacement": "Clear text",
        }]
        result_path = root / "tmp" / "blocked.json"
        result_path.write_bytes(STE._canonical_json_bytes(blocked))
        STE.record_documentation_review(
            scope_path=scope_path, result_path=result_path,
            source_manifest=source_manifest, root=root,
        )
        guide.write_bytes(old_bytes)
        reverted = commit(root, "revert to old matching state without completion")
        guide.write_bytes(old_bytes.replace(b"Old text", b"Alternative text"))
        commit(root, "revised candidate after uncompleted revert")
        expect_ste_error(
            "ste-review-cycle-restart",
            lambda: STE.freeze_documentation_review(
                baseline_revision=reverted, author_id="author",
                source_manifest=source_manifest, root=root,
            ),
        )

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        (root / "reference").mkdir()
        (root / "tmp").mkdir()
        (root / ".gitignore").write_text("tmp/\n", encoding="utf-8")
        guide = root / "reference" / "guide.md"
        state_path = root / "reference" / "ste-review-state.json"
        guide.write_text("# Guide\n\nOld instruction.\n", encoding="utf-8")
        state_path.write_bytes(STE._canonical_json_bytes(STE._empty_review_state()))
        git(root, "init", "--quiet")
        baseline = commit(root, "deletion baseline")
        guide.unlink()
        commit(root, "document deletion")
        scope_path, scope = STE.freeze_documentation_review(
            baseline_revision=baseline, author_id="author",
            source_manifest=source_manifest, root=root,
        )
        accepted = copy.deepcopy(result)
        accepted.update(
            result="ACCEPT", blockers=[], corrections=[],
            scope_sha256=scope["scope_sha256"],
        )
        result_path = root / "tmp" / "accepted-deletion.json"
        result_path.write_bytes(STE._canonical_json_bytes(accepted))
        receipt_path, proposal_path, _receipt = STE.record_documentation_review(
            scope_path=scope_path, result_path=result_path,
            source_manifest=source_manifest, root=root,
        )
        require(proposal_path is not None, "an accepted deletion has no state proposal")
        state_path.write_bytes(proposal_path.read_bytes())
        deleted_baseline = commit(root, "lock accepted deletion")
        final = STE.validate_final_review_state(
            scope_path=scope_path, receipt_path=receipt_path,
            source_manifest=source_manifest, root=root,
        )
        require(
            final["result"] == "ACCEPT"
            and final["status"] == "locked-and-deterministically-validated",
            "an accepted deletion did not complete",
        )
        guide.write_text("# Guide\n\nLater distinct instruction.\n", encoding="utf-8")
        commit(root, "recreate document after completed deletion")
        _path, scope = STE.freeze_documentation_review(
            baseline_revision=deleted_baseline, author_id="author",
            source_manifest=source_manifest, root=root,
        )
        require(
            scope["documents"][0]["mode"] == "complete-document",
            "a completed deletion prevented later distinct document work",
        )


def validate_lifecycle_git_boundary() -> None:
    """Reject inherited Git execution and object-interpretation controls."""

    def git(root: pathlib.Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(root: pathlib.Path, message: str) -> str:
        git(root, "add", "--all")
        git(
            root,
            "-c",
            "user.name=TrackTemplate Validation",
            "-c",
            "user.email=validation@example.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
        )
        return git(root, "rev-parse", "HEAD")

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        (root / "reference").mkdir()
        guide = root / "reference" / "guide.md"
        attributes = root / ".gitattributes"
        attributes.write_text("*.md diff=evil\n", encoding="utf-8")
        guide.write_text("# Guide\n\nBaseline text.\n", encoding="utf-8")
        git(root, "init", "--quiet")
        baseline = commit(root, "baseline")
        guide.write_text("# Guide\n\nCandidate text.\n", encoding="utf-8")
        candidate = commit(root, "candidate")
        expected_identity = STE._lifecycle_candidate_identity(
            baseline,
            candidate,
            root=root,
        )

        hostile = root / "hostile"
        hostile.mkdir()
        marker = hostile / "executed"
        helper = hostile / "helper"
        helper.write_text(
            "#!/bin/sh\nprintf 'executed\\n' >> \"{}\"\nexit 1\n".format(
                marker
            ),
            encoding="utf-8",
        )
        helper.chmod(0o700)
        hostile_git = hostile / "git"
        hostile_git.write_text(
            "#!/bin/sh\nprintf 'git\\n' >> \"{}\"\nexit 99\n".format(marker),
            encoding="utf-8",
        )
        hostile_git.chmod(0o700)
        global_config = hostile / "global-config"
        global_config.write_text(
            "[core]\n\tfsmonitor = {}\n"
            "[diff \"evil\"]\n\ttextconv = {}\n".format(helper, helper),
            encoding="utf-8",
        )
        git(root, "config", "core.fsmonitor", str(helper))
        git(root, "config", "diff.evil.textconv", str(helper))
        git(root, "replace", candidate, baseline)

        decoy = root / "decoy"
        decoy.mkdir()
        git(decoy, "init", "--quiet")
        saved_environment = os.environ.copy()
        try:
            os.environ.update(
                {
                    "GIT_ATTR_SOURCE": baseline,
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_GLOBAL": str(global_config),
                    "GIT_CONFIG_KEY_0": "core.fsmonitor",
                    "GIT_CONFIG_VALUE_0": str(helper),
                    "GIT_DIR": str(decoy / ".git"),
                    "GIT_EXTERNAL_DIFF": str(helper),
                    "GIT_INDEX_FILE": str(decoy / "hostile-index"),
                    "GIT_REPLACE_REF_BASE": "refs/replace/hostile/",
                    "GIT_WORK_TREE": str(decoy),
                    "PATH": str(hostile),
                }
            )
            require(
                STE._lifecycle_head(root=root, require_clean=True) == candidate,
                "hostile Git state redirected the lifecycle HEAD",
            )
            require(
                STE._lifecycle_candidate_identity(
                    baseline,
                    candidate,
                    root=root,
                )
                == expected_identity,
                "Git configuration or replacement objects changed candidate identity",
            )
            guide.write_text(
                "# Guide\n\nUncommitted candidate text.\n",
                encoding="utf-8",
            )
            expect_ste_error(
                "ste-lifecycle-candidate-not-clean",
                lambda: STE._lifecycle_head(root=root, require_clean=True),
            )
        finally:
            os.environ.clear()
            os.environ.update(saved_environment)
        saved_default_path = os.defpath
        try:
            os.defpath = str(hostile)
            expect_ste_error(
                "ste-lifecycle-git-untrusted",
                lambda: STE._lifecycle_head(root=root, require_clean=True),
            )
        finally:
            os.defpath = saved_default_path
        require(
            not marker.exists(),
            "the lifecycle executed an inherited, repository-local, fsmonitor, "
            "or textconv helper",
        )


def validate_live_source_resolvability() -> None:
    source_path = SOURCE_DIR / "ASD-STE100_ISSUE9.pdf"
    cache_path = SOURCE_DIR / ".cache" / "issue9-cache-v2.json"
    if not source_path.is_file() or not cache_path.is_file():
        return
    cache, _, source_bytes = STE.load_verified_cache()
    pages, extractor_identity = STE._extract_pdf_pages(source_bytes)
    require(
        extractor_identity == cache["extractor_identity"],
        "the exhaustive dictionary proof used a different PDF extractor",
    )
    checked: set[tuple[str, str, int]] = set()
    for entries in cache["dictionary"].values():
        for entry in entries:
            key = (
                str(entry["headword"]),
                str(entry["part_of_speech"]),
                int(entry["page_number"]),
            )
            if key in checked:
                continue
            checked.add(key)
            page_text = pages[key[2] - 1]
            require(
                STE._page_label(page_text, key[2]) == entry["source_label"],
                "a dictionary entry has the wrong source-page label",
            )
            STE._bounded_excerpt(
                page_text,
                STE._dictionary_source_pattern(key[0], key[1]),
            )
    require(
        len(checked) >= 1_800,
        "the exhaustive dictionary source proof checked too few headwords",
    )
    for identifier, hits in cache["rule_pages"].items():
        hit = hits[-1]
        page_number = int(hit["page_number"])
        page_text = pages[page_number - 1]
        prefix = "" if identifier.startswith("GR-") else "Rule "
        STE._bounded_excerpt(
            page_text,
            re.compile(
                r"^\s*{}{}(?:\s|$)".format(prefix, re.escape(identifier)),
                re.MULTILINE,
            ),
        )
    require(
        len(cache["rule_pages"]) == 61,
        "the exhaustive rule source proof did not check all indexed items",
    )


def main() -> None:
    _, index = validate_contract_files()
    validate_source_documentation(read(SOURCE_README))
    validate_provenance_documentation(read(PROVENANCE))
    validate_copyright_and_ignore_boundary()
    validate_local_tool_boundary()
    validate_technical_term_owner()
    validate_agent_and_validation_routing()
    validate_cache_and_lookup_behaviour(index)
    validate_documentation_lifecycle()
    validate_finite_documentation_lifecycle()
    validate_lifecycle_git_boundary()
    validate_live_source_resolvability()
    validate_semantic_mutations(index)
    print(SENTINEL)


if __name__ == "__main__":
    main()
