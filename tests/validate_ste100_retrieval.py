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
        "retrieval optimisation only",
        "does not define or limit the applicable rule set",
        "applicable rule set is mandatory",
        "controlled vocabulary is also mandatory",
        "must not claim conformance because of rules in a lookup result",
        "must not claim conformance because the pre-check has no finding",
        "pass result from automatic validation also does not show conformance",
        "ste lookup controls the source text that an agent reads for this task",
        "does not control the applicable writing rules",
    ):
        require(fragment in section, "application profile lacks: " + fragment)
    require(
        "tracktemplate uses uk english spelling as its project spelling directive"
        in section,
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
        "read the technical documentation profile",
        "read the technical-term register",
        "use the tracktemplate-documentation-review skill",
        "record each logical unit with a material edit",
        "for each logical unit, record the content category",
        "use the writing checklist for each logical unit",
        "record findings and their dispositions",
        "resolve all findings and unresolved terminology",
        "after the last wording change, review each complete logical unit again",
        "validate the temporary author-review worklist",
        "before the author freezes an exact candidate, get a read-only challenge",
        "when project authority makes it necessary, get an independent review",
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
        "they are not the applicable rule set",
        "use complete-source inspection only for these bounded conditions",
        "task is about the complete standard",
        "validates the retrieval architecture",
        "targeted retrieval cannot resolve an ambiguity that the reviewer records",
        "owner decision makes complete-source inspection necessary",
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
        require(
            "../../../reference/external/asd-ste100/README.md" in text,
            name + " bypasses the canonical source/retrieval owner",
        )
        require(
            "local-retrieval-interface" in text
            or "pre-check-and-review-receipt" in text,
            name + " does not route through the retrieval interface",
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
        and "does not select the issue 9 requirement set"
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
    require(
        "reviewer examines the complete applicable requirement set"
        in semantic_text(skills["tracktemplate-quality-review"]),
        "quality review does not check full applicability",
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
        "byte size or sha-256 identity is different from the source manifest",
        "source-derived index when its identity is not the identity in the source "
        "manifest",
        "must be a regular file",
        "must not be in the repository or active python environment",
        "group and other users must not have write access",
        "derived cache must contain metadata only",
        "source mode must use verified source bytes",
        "must not make a linguistic conformance, certification, or endorsement claim",
        "review receipt must record that the reviewer examines the complete "
        "applicable requirement set",
        "review receipt, pre-check, derived cache, and selected lookup results do "
        "not show",
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
    expected = ["LFE-{:03d}".format(number) for number in range(1, 22)]
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
        "The applicable rule set is mandatory. The controlled\n"
        "vocabulary is also mandatory.",
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
        "They are not the\napplicable rule set.",
        "They are the applicable rule set.",
    )
    require(narrowed_workflow != workflows, "workflow narrowing fixture is stale")
    try:
        validate_workflow_text(narrowed_workflow)
    except AssertionError:
        pass
    else:
        raise AssertionError("lookup-as-complete workflow mutation was accepted")
    contradictory_workflow = (
        workflows + "\nLookup results are the complete applicable rule set.\n"
    )
    try:
        validate_workflow_text(contradictory_workflow)
    except AssertionError:
        pass
    else:
        raise AssertionError("contradictory workflow addition was accepted")

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
    bypassed = dict(skills)
    bypassed["tracktemplate-quality-review"] = bypassed[
        "tracktemplate-quality-review"
    ].replace("local-retrieval-interface", "removed-retrieval-route")
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



def validate_author_review_traceability() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        document = root / "review.md"
        document.write_text("# Review\n\nThe author reviews the text.\n", encoding="utf-8")
        for command in (
            ["git", "init", "--quiet"],
            ["git", "add", document.name],
            [
                "git",
                "-c",
                "user.name=TrackTemplate Validation",
                "-c",
                "user.email=validation@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "baseline",
            ],
        ):
            subprocess.run(command, cwd=root, check=True)
        baseline = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        document.write_text(
            "# Review\n\nThe author reviews all changed prose.\n",
            encoding="utf-8",
        )
        output_dir = root / "tmp"
        output_dir.mkdir()
        output = output_dir / "validation.log"
        output.write_text(
            "RESULT=PASS\n",
            encoding="utf-8",
        )
        source_manifest = {
            "issue": "9",
            "page_count": 434,
            "publication_date": "2025-01-15",
            "sha256": EXPECTED_SOURCE_SHA256,
            "size_bytes": EXPECTED_SOURCE_SIZE,
            "standard_id": "ASD-STE100",
        }
        document_hash = hashlib.sha256(document.read_bytes()).hexdigest()
        unit_payload = "".join(
            document.read_text(encoding="utf-8").splitlines(keepends=True)
        ).encode("utf-8")
        source = {"path": document.name, "sha256": document_hash}
        evidence = {
            "actual_result": "RESULT=PASS",
            "claim": "The fixture command gave a PASS result.",
            "command": {
                "argv": [sys.executable, "-c", "print('RESULT=PASS')"],
                "exit_status": 0,
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_source": "tmp/validation.log",
                "profile": "fixture",
                "sentinel": "RESULT=",
                "working_directory": str(root),
            },
            "id": "evidence-001",
            "source": source,
            "type": "command-result",
        }
        candidate = STE._assurance_candidate(baseline, root=root)
        worklist = {
            "author_review": {
                "completed_on": "2026-08-26",
                "method": "complete-human-ASD-STE100-Issue-9-review",
                "reviewer": "fixture author",
                "status": "complete",
            },
            "baseline_revision": baseline,
            "candidate": candidate,
            "documents": [source],
            "prefreeze_challenge": {
                "candidate_content_sha256": "",
                "completed_on": "",
                "review_worklist_sha256": "",
                "result_sha256": "",
                "result_source": "",
                "reviewer": "",
                "status": "pending",
                "unresolved_findings": [],
            },
            "source_identity": source_manifest,
            "units": [
                {
                    "applicable_review_categories": list(
                        STE.ASSURANCE_REVIEW_CATEGORIES
                    ),
                    "content_category": "descriptive",
                    "document_class": "guidance",
                    "end_line": 3,
                    "evidence_claims": [evidence],
                    "findings": [
                        {
                            "category": "controlled-vocabulary",
                            "description": "The first wording used an unapproved word.",
                            "disposition": "The author used approved vocabulary.",
                            "end_line": 3,
                            "id": "finding-001",
                            "start_line": 3,
                            "status": "resolved",
                        }
                    ],
                    "id": "unit-001",
                    "path": document.name,
                    "review_status": "complete",
                    "sha256": hashlib.sha256(unit_payload).hexdigest(),
                    "start_line": 1,
                    "unresolved_findings": [],
                }
            ],
            "unresolved_findings": [],
            "worklist_schema_version": 1,
        }
        receipt = STE.validate_author_assurance_worklist(
            worklist,
            root=root,
            source_manifest=source_manifest,
        )
        require(
            receipt["assurance_status"]
            == "candidate-bound-human-review-traceability-not-linguistic-conformance",
            "author assurance claimed automatic linguistic conformance",
        )
        changed_document = copy.deepcopy(worklist)
        document.write_text(
            "# Review\n\nThe author changed the reviewed text.\n",
            encoding="utf-8",
        )
        expect_ste_error(
            "author-assurance-candidate-changed",
            lambda: STE.validate_author_assurance_worklist(
                changed_document,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        document.write_text(
            "# Review\n\nThe author reviews all changed prose.\n",
            encoding="utf-8",
        )
        omitted_scope = copy.deepcopy(worklist)
        omitted_scope["documents"] = []
        expect_ste_error(
            "author-assurance-scope-invalid",
            lambda: STE.validate_author_assurance_worklist(
                omitted_scope,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        unresolved = copy.deepcopy(worklist)
        unresolved["units"][0]["unresolved_findings"] = ["open finding"]
        expect_ste_error(
            "author-assurance-unresolved",
            lambda: STE.validate_author_assurance_worklist(
                unresolved,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        wrong_source = copy.deepcopy(worklist)
        wrong_source["source_identity"]["sha256"] = "0" * 64
        expect_ste_error(
            "author-assurance-source-invalid",
            lambda: STE.validate_author_assurance_worklist(
                wrong_source,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        incomplete_review = copy.deepcopy(worklist)
        incomplete_review["author_review"]["status"] = "incomplete"
        expect_ste_error(
            "author-assurance-review-invalid",
            lambda: STE.validate_author_assurance_worklist(
                incomplete_review,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        false_result = copy.deepcopy(worklist)
        false_result["units"][0]["evidence_claims"][0]["actual_result"] = (
            "RESULT=FAIL"
        )
        expect_ste_error(
            "author-assurance-evidence-invalid",
            lambda: STE.validate_author_assurance_worklist(
                false_result,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        relative_command = copy.deepcopy(worklist)
        relative_command["units"][0]["evidence_claims"][0]["command"]["argv"][0] = (
            "python"
        )
        expect_ste_error(
            "author-assurance-evidence-invalid",
            lambda: STE.validate_author_assurance_worklist(
                relative_command,
                root=root,
                source_manifest=source_manifest,
            ),
        )
        expect_ste_error(
            "author-assurance-challenge-required",
            lambda: STE.validate_author_assurance_worklist(
                worklist,
                root=root,
                source_manifest=source_manifest,
                require_challenge=True,
            ),
        )
        challenge_output = output_dir / "challenge.json"
        challenge_output.write_text(
            '{"status":"pass"}\n',
            encoding="utf-8",
        )
        challenged = copy.deepcopy(worklist)
        review_payload = json.dumps(
            {
                key: value
                for key, value in challenged.items()
                if key != "prefreeze_challenge"
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        challenged["prefreeze_challenge"] = {
            "candidate_content_sha256": candidate["content_sha256"],
            "completed_on": "2026-08-26",
            "review_worklist_sha256": hashlib.sha256(
                review_payload
            ).hexdigest(),
            "result_sha256": hashlib.sha256(
                challenge_output.read_bytes()
            ).hexdigest(),
            "result_source": "tmp/challenge.json",
            "reviewer": "read-only documentation reviewer",
            "status": "pass",
            "unresolved_findings": [],
        }
        STE.validate_author_assurance_worklist(
            challenged,
            root=root,
            source_manifest=source_manifest,
            require_challenge=True,
        )
        stale_challenge = copy.deepcopy(challenged)
        stale_challenge["prefreeze_challenge"]["candidate_content_sha256"] = "0" * 64
        expect_ste_error(
            "author-assurance-candidate-changed",
            lambda: STE.validate_author_assurance_worklist(
                stale_challenge,
                root=root,
                source_manifest=source_manifest,
                require_challenge=True,
            ),
        )
        stale_review = copy.deepcopy(challenged)
        stale_review["author_review"]["reviewer"] = "replacement author"
        expect_ste_error(
            "author-assurance-candidate-changed",
            lambda: STE.validate_author_assurance_worklist(
                stale_review,
                root=root,
                source_manifest=source_manifest,
                require_challenge=True,
            ),
        )
        same_reviewer = copy.deepcopy(challenged)
        same_reviewer["prefreeze_challenge"]["reviewer"] = "fixture author"
        expect_ste_error(
            "author-assurance-challenge-invalid",
            lambda: STE.validate_author_assurance_worklist(
                same_reviewer,
                root=root,
                source_manifest=source_manifest,
                require_challenge=True,
            ),
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
    validate_author_review_traceability()
    validate_live_source_resolvability()
    validate_semantic_mutations(index)
    print(SENTINEL)


if __name__ == "__main__":
    main()
