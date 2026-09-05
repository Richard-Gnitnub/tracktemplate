#!/usr/bin/env python3
"""Provide source-bound local ASD-STE100 retrieval and review aids."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import concurrent.futures
import difflib
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "reference" / "external" / "asd-ste100"
SOURCE_MANIFEST = REFERENCE_DIR / "source-manifest.json"
RETRIEVAL_INDEX = REFERENCE_DIR / "retrieval-index.json"
SOURCE_FILE = REFERENCE_DIR / "ASD-STE100_ISSUE9.pdf"
CACHE_FILE = REFERENCE_DIR / ".cache" / "issue9-cache-v2.json"
TERMINOLOGY = ROOT / "reference" / "TERMINOLOGY.md"
APPLICATION_PROFILE = ROOT / "reference" / "ENGINEERING_POLICY.md"
RECEIPT_DIR = ROOT / "tmp" / "ste100-review-receipts"
STE_REVIEW_STATE = ROOT / "reference" / "ste-review-state.json"
STE_REVIEW_SCOPE_DIR = ROOT / "tmp" / "ste100-review-scopes"
STE_REVIEW_RESULT_DIR = ROOT / "tmp" / "ste100-review-results"
STE_REVIEW_PROPOSAL_DIR = ROOT / "tmp" / "ste100-review-state-proposals"
SENTINEL = "TRACKTEMPLATE_STE100="
ERROR_SENTINEL = "TRACKTEMPLATE_STE100_ERROR="
FINAL_SENTINEL = "TRACKTEMPLATE_STE100_FINAL="
MAX_SOURCE_EXCERPT_CHARS = 600
MAX_REVIEW_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_TRACKED_JSON_BYTES = 128 * 1024
MAX_CACHE_JSON_BYTES = 2 * 1024 * 1024
MAX_HASHED_INPUT_BYTES = 32 * 1024 * 1024
MAX_EXTRACTED_TEXT_BYTES = 8 * 1024 * 1024
MAX_EXTRACTED_PAGE_BYTES = 256 * 1024
MAX_EXTRACTOR_ERROR_BYTES = 64 * 1024
MAX_RECEIPT_BYTES = 512 * 1024
MAX_RECEIPT_ITEMS = 50
MAX_LIFECYCLE_DOCUMENTS = 64
MAX_LIFECYCLE_UNITS = 512
MAX_LIFECYCLE_BLOCKERS = 4096
MAX_LIFECYCLE_BYTES = 4 * 1024 * 1024
MAX_LIFECYCLE_GIT_OUTPUT_BYTES = 4 * 1024 * 1024
STE_REVIEW_RESULTS = {
    "ACCEPT",
    "APPROVED_WITH_EXACT_CORRECTIONS",
    "BLOCKED",
}
CANONICAL_JSON_PROSE = {
    "reference/current/gate-decisions.json": "decisions",
    "reference/current/risks.json": "risks",
}
WORD_RE = re.compile(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b")
DICTIONARY_ENTRY_RE = re.compile(
    r"^ {0,2}([A-Za-z][A-Za-z0-9' -]*?)\s+"
    r"\((art|adj|adv|conj|n|prep|pron|v)\)"
)
DICTIONARY_FORM_RE = re.compile(r"^ {0,2}([A-Z][A-Z0-9' -]*?)(?:,)?(?:\s{2,}|$)")
DICTIONARY_CONTINUED_POS_RE = re.compile(
    r"^\s*(?:\([^)]*\)\s*)?\((art|adj|adv|conj|n|prep|pron|v)\)\s*$"
)
DICTIONARY_TERM_COLUMN_WIDTH = 19
PAGE_LABEL_RE = re.compile(r"\bPage\s+([A-Z0-9]+(?:-[A-Z0-9]+)+)\b")
CONTRACTION_RE = re.compile(
    r"\b(?:can't|cannot've|couldn't|didn't|doesn't|don't|hadn't|hasn't|"
    r"haven't|isn't|mustn't|shouldn't|wasn't|weren't|won't|wouldn't)\b",
    re.IGNORECASE,
)


class Ste100Error(RuntimeError):
    """Report one fail-closed lookup or cache error."""

    def __init__(self, code: str, message: str, remedy: str) -> None:
        super().__init__(message)
        self.code = code
        self.remedy = remedy


class _SubprocessOutputLimitError(RuntimeError):
    """Signal that one bounded development-tool stream exceeded its limit."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(
    path: pathlib.Path,
    max_bytes: int = MAX_HASHED_INPUT_BYTES,
) -> str:
    """Return the SHA-256 identity of one file."""
    try:
        file_status = path.stat()
    except OSError as error:
        raise Ste100Error(
            "input-unreadable",
            "An identity input cannot be read: {}.".format(path),
            "Restore the expected bounded local input.",
        ) from error
    if not stat.S_ISREG(file_status.st_mode) or file_status.st_size > max_bytes:
        raise Ste100Error(
            "input-size-invalid",
            "An identity input is not a regular bounded file: {}.".format(path),
            "Restore the expected bounded local input.",
        )
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise Ste100Error(
            "input-unreadable",
            "An identity input cannot be read: {}.".format(path),
            "Restore the expected bounded local input.",
        ) from error
    return digest.hexdigest()


def _read_json_object(
    path: pathlib.Path,
    subject: str,
    *,
    max_bytes: int = MAX_TRACKED_JSON_BYTES,
) -> dict[str, object]:
    try:
        with path.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise Ste100Error(
                    subject + "-invalid",
                    "The {} is not a regular file.".format(subject),
                    "Restore the expected bounded JSON object.",
                )
            payload = stream.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise Ste100Error(
                subject + "-too-large",
                "The {} exceeds its local size limit.".format(subject),
                "Restore or rebuild the bounded JSON object.",
            )
        value = json.loads(payload.decode("utf-8"))
    except FileNotFoundError as error:
        raise Ste100Error(
            subject + "-missing",
            "The {} is absent: {}.".format(subject, path),
            "Restore the tracked file before using the lookup.",
        ) from error
    except OSError as error:
        raise Ste100Error(
            subject + "-unreadable",
            "The {} cannot be read: {}.".format(subject, path),
            "Restore the expected bounded JSON object.",
        ) from error
    except json.JSONDecodeError as error:
        raise Ste100Error(
            subject + "-invalid",
            "The {} is not valid JSON: {}.".format(subject, path),
            "Correct and validate the tracked contract before use.",
        ) from error
    except UnicodeDecodeError as error:
        raise Ste100Error(
            subject + "-invalid",
            "The {} is not valid UTF-8 JSON: {}.".format(subject, path),
            "Correct and validate the bounded JSON object before use.",
        ) from error
    if not isinstance(value, dict):
        raise Ste100Error(
            subject + "-invalid",
            "The {} must contain one JSON object.".format(subject),
            "Correct and validate the tracked contract before use.",
        )
    return value


def expected_rule_ids() -> set[str]:
    """Return the complete set of formal Part 1 rule identifiers."""
    counts = (14, 2, 7, 5, 5, 6, 3, 7, 4)
    return {
        "{}.{}".format(section, rule)
        for section, count in enumerate(counts, start=1)
        for rule in range(1, count + 1)
    }


def expected_recommendation_ids() -> set[str]:
    """Return the Issue 9 general-recommendation identifiers."""
    return {"GR-{}".format(number) for number in range(1, 9)}


def validate_source_manifest(manifest: dict[str, object]) -> None:
    """Validate the tracked exact-source contract."""
    expected_keys = {
        "cache_schema_version",
        "copyright_status",
        "extraction_index_sha256",
        "filename",
        "issue",
        "official_url",
        "page_count",
        "publication_date",
        "schema_version",
        "sha256",
        "size_bytes",
        "standard_id",
    }
    if set(manifest) != expected_keys:
        raise Ste100Error(
            "source-manifest-invalid",
            "The source manifest fields do not match schema version 1.",
            "Correct the tracked source manifest and run its validator.",
        )
    checks = (
        (manifest["schema_version"] == 1, "manifest schema version"),
        (manifest["cache_schema_version"] == 2, "cache schema version"),
        (manifest["standard_id"] == "ASD-STE100", "standard identifier"),
        (manifest["issue"] == 9, "issue number"),
        (manifest["publication_date"] == "2025-01-15", "publication date"),
        (
            manifest["copyright_status"] == "external-copyrighted-reference-local-only",
            "copyright status",
        ),
        (
            isinstance(manifest["page_count"], int) and manifest["page_count"] > 0,
            "page count",
        ),
        (
            isinstance(manifest["sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"]) is not None,
            "source hash",
        ),
        (
            isinstance(manifest["extraction_index_sha256"], str)
            and re.fullmatch(
                r"[0-9a-f]{64}",
                manifest["extraction_index_sha256"],
            )
            is not None,
            "extraction index hash",
        ),
        (
            isinstance(manifest["size_bytes"], int)
            and 0 < manifest["size_bytes"] <= MAX_HASHED_INPUT_BYTES,
            "source size",
        ),
        (
            isinstance(manifest["filename"], str)
            and pathlib.PurePath(manifest["filename"]).name == manifest["filename"],
            "source filename",
        ),
        (
            isinstance(manifest["official_url"], str)
            and manifest["official_url"].startswith("https://www.asd-ste100.org/"),
            "official source URL",
        ),
    )
    for condition, subject in checks:
        if not condition:
            raise Ste100Error(
                "source-manifest-invalid",
                "The {} is invalid.".format(subject),
                "Correct the tracked source manifest and run its validator.",
            )


def validate_retrieval_index(index: dict[str, object]) -> None:
    """Validate compact retrieval hints without treating them as authority."""
    if set(index) != {
        "applicability_statement",
        "families",
        "review_categories",
        "schema_version",
        "status",
    }:
        raise Ste100Error(
            "retrieval-index-invalid",
            "The retrieval index fields do not match schema version 1.",
            "Correct the tracked index and run its validator.",
        )
    if index["schema_version"] != 1 or index["status"] != "retrieval-hints-only":
        raise Ste100Error(
            "retrieval-index-invalid",
            "The retrieval index version or retrieval-only status is invalid.",
            "Correct the tracked index and run its validator.",
        )
    statement = str(index["applicability_statement"]).casefold()
    for phrase in (
        "retrieval hints only",
        "issue 9",
        "application profile",
        "complete applicable requirement set",
    ):
        if phrase not in statement:
            raise Ste100Error(
                "retrieval-index-invalid",
                "The retrieval-only applicability safeguard is incomplete.",
                "Restore the source, profile, and applicability distinction.",
            )

    families = index["families"]
    if not isinstance(families, list) or not families:
        raise Ste100Error(
            "retrieval-index-invalid",
            "The retrieval index must contain rule families.",
            "Add complete family metadata with source locations.",
        )
    family_ids: set[str] = set()
    rule_ids: set[str] = set()
    recommendation_ids: set[str] = set()
    for family in families:
        required = {
            "content_categories",
            "id",
            "rule_ids",
            "source_location",
            "title",
            "topic_tags",
        }
        if not isinstance(family, dict) or set(family) not in (
            required,
            required | {"recommendation_ids"},
        ):
            raise Ste100Error(
                "retrieval-index-invalid",
                "A rule family lacks required retrieval metadata.",
                "Add its identifier, topics, rules, categories, and source.",
            )
        family_id = family["id"]
        if not isinstance(family_id, str) or family_id in family_ids:
            raise Ste100Error(
                "retrieval-index-invalid",
                "A rule family identifier is invalid or duplicated.",
                "Give each retrieval family one stable identifier.",
            )
        family_ids.add(family_id)
        rules = family["rule_ids"]
        recommendations = family.get("recommendation_ids", [])
        categories_for_family = family["content_categories"]
        tags = family["topic_tags"]
        if (
            not isinstance(family["title"], str)
            or not family["title"]
            or not isinstance(rules, list)
            or not rules
            or not all(isinstance(item, str) for item in rules)
            or not isinstance(recommendations, list)
            or not all(isinstance(item, str) for item in recommendations)
            or not isinstance(categories_for_family, list)
            or not categories_for_family
            or not set(categories_for_family).issubset(
                {"descriptive", "procedural", "safety"}
            )
            or not isinstance(tags, list)
            or not tags
            or not all(isinstance(item, str) and item for item in tags)
        ):
            raise Ste100Error(
                "retrieval-index-invalid",
                "A rule family has invalid compact retrieval values.",
                "Use non-empty identifiers, topics, rules, and categories.",
            )
        location = family["source_location"]
        if (
            not isinstance(location, dict)
            or set(location) != {"part", "section", "pages"}
            or not all(location.get(key) for key in ("part", "section", "pages"))
            or location["part"] != "Part 1"
        ):
            raise Ste100Error(
                "retrieval-index-invalid",
                "Rule family {} has no complete source location.".format(family_id),
                "Add its authoritative part, section, and page range.",
            )
        for rule_id in rules:
            section = rule_id.split(".", 1)[0]
            if location["section"] != "Section {}".format(section) or not str(
                location["pages"]
            ).startswith("1-{}-".format(section)):
                raise Ste100Error(
                    "retrieval-index-invalid",
                    "Rule {} is not bound to its Part 1 section.".format(rule_id),
                    "Correct its authoritative section and page range.",
                )
            if rule_id in rule_ids:
                raise Ste100Error(
                    "retrieval-index-invalid",
                    "Rule {} occurs in more than one family.".format(rule_id),
                    "Keep each formal rule in one retrieval family.",
                )
            rule_ids.add(rule_id)
        for recommendation_id in recommendations:
            if location["section"] != "Section 9" or not str(
                location["pages"]
            ).startswith("1-9-"):
                raise Ste100Error(
                    "retrieval-index-invalid",
                    "A general recommendation is not bound to Part 1 Section 9.",
                    "Correct its authoritative section and page range.",
                )
            if recommendation_id in recommendation_ids:
                raise Ste100Error(
                    "retrieval-index-invalid",
                    "Recommendation {} is duplicated.".format(recommendation_id),
                    "Keep each recommendation in one retrieval family.",
                )
            recommendation_ids.add(recommendation_id)
    if rule_ids != expected_rule_ids():
        raise Ste100Error(
            "retrieval-index-invalid",
            "The index does not cover the complete set of 53 formal rules.",
            "Restore every formal rule identifier and its source family.",
        )
    if recommendation_ids != expected_recommendation_ids():
        raise Ste100Error(
            "retrieval-index-invalid",
            "The index does not cover all eight general recommendations.",
            "Restore the recommendation identifiers and their source family.",
        )

    categories = index["review_categories"]
    if not isinstance(categories, list) or not categories:
        raise Ste100Error(
            "retrieval-index-invalid",
            "The retrieval index has no review-category mappings.",
            "Add bounded retrieval-priority mappings.",
        )
    category_ids: set[str] = set()
    for category in categories:
        if not isinstance(category, dict) or set(category) != {
            "id",
            "retrieval_priority_families",
        }:
            raise Ste100Error(
                "retrieval-index-invalid",
                "A review category has invalid fields.",
                "Use an identifier and retrieval-priority families only.",
            )
        category_id = category["id"]
        priorities = category["retrieval_priority_families"]
        if (
            not isinstance(category_id, str)
            or category_id in category_ids
            or not isinstance(priorities, list)
            or not priorities
            or not set(priorities).issubset(family_ids)
        ):
            raise Ste100Error(
                "retrieval-index-invalid",
                "A review category has invalid or unknown priorities.",
                "Keep unique categories that reference known families.",
            )
        category_ids.add(category_id)


def load_contracts(
    manifest_path: pathlib.Path = SOURCE_MANIFEST,
    index_path: pathlib.Path = RETRIEVAL_INDEX,
) -> tuple[dict[str, object], dict[str, object]]:
    """Load and validate the tracked source and retrieval contracts."""
    manifest = _read_json_object(manifest_path, "source-manifest")
    index = _read_json_object(index_path, "retrieval-index")
    validate_source_manifest(manifest)
    validate_retrieval_index(index)
    return manifest, index


def _read_verified_source(
    source_path: pathlib.Path,
    manifest: dict[str, object],
) -> tuple[dict[str, object], bytes]:
    """Read and verify the authorised source through one open file handle."""
    if source_path.name != manifest["filename"]:
        raise Ste100Error(
            "source-path-mismatch",
            "The local source path does not match the authorised filename.",
            "Use the canonical local source path.",
        )
    try:
        stream = source_path.open("rb")
    except FileNotFoundError as error:
        raise Ste100Error(
            "source-missing",
            "The authorised Issue 9 source is absent.",
            "Put the official PDF at the canonical path, then rebuild the cache.",
        ) from error
    except OSError as error:
        raise Ste100Error(
            "source-not-file",
            "The authorised Issue 9 source cannot be opened as a regular file.",
            "Restore the official PDF at the canonical path.",
        ) from error
    try:
        with stream:
            opened_status = os.fstat(stream.fileno())
            path_status = source_path.lstat()
            if (
                not stat.S_ISREG(opened_status.st_mode)
                or not stat.S_ISREG(path_status.st_mode)
                or (opened_status.st_dev, opened_status.st_ino)
                != (path_status.st_dev, path_status.st_ino)
            ):
                raise Ste100Error(
                    "source-not-file",
                    "The authorised Issue 9 source path is not one stable "
                    "regular file.",
                    "Restore the official PDF at the canonical path.",
                )
            if opened_status.st_size != manifest["size_bytes"]:
                raise Ste100Error(
                    "source-size-mismatch",
                    "The local Issue 9 source does not have the authorised size.",
                    "Do not use it. Restore the authorised source.",
                )
            source_bytes = stream.read(int(manifest["size_bytes"]) + 1)
    except OSError as error:
        raise Ste100Error(
            "source-unreadable",
            "The authorised Issue 9 source cannot be read.",
            "Restore the official PDF at the canonical path.",
        ) from error
    if len(source_bytes) != manifest["size_bytes"]:
        raise Ste100Error(
            "source-size-mismatch",
            "The local Issue 9 source does not have the authorised size.",
            "Do not use it. Restore the authorised source.",
        )
    actual_hash = _sha256_bytes(source_bytes)
    if actual_hash != manifest["sha256"]:
        raise Ste100Error(
            "source-hash-mismatch",
            "The local Issue 9 source does not have the authorised SHA-256.",
            "Do not use the cache. Restore the authorised source or review a "
            "new source identity.",
        )
    identity = {
        "filename": manifest["filename"],
        "issue": manifest["issue"],
        "page_count": manifest["page_count"],
        "publication_date": manifest["publication_date"],
        "sha256": actual_hash,
        "size_bytes": len(source_bytes),
        "standard_id": manifest["standard_id"],
    }
    return identity, source_bytes


def verify_source(
    source_path: pathlib.Path,
    manifest: dict[str, object],
) -> dict[str, object]:
    """Verify the exact authorised local source before cache use."""
    identity, _ = _read_verified_source(source_path, manifest)
    return identity


def _input_identities(
    manifest_path: pathlib.Path,
    index_path: pathlib.Path,
    terminology_path: pathlib.Path,
    profile_path: pathlib.Path,
    tool_path: pathlib.Path = pathlib.Path(__file__).resolve(),
) -> dict[str, str]:
    return {
        "application_profile_sha256": sha256_file(profile_path),
        "lookup_tool_sha256": sha256_file(tool_path),
        "retrieval_index_sha256": sha256_file(index_path),
        "source_manifest_sha256": sha256_file(manifest_path),
        "technical_terms_sha256": sha256_file(terminology_path),
    }


def _derived_content_sha256(cache: dict[str, object]) -> str:
    payload = {
        key: cache[key] for key in ("dictionary", "rule_pages", "technical_terms")
    }
    payload["source_text_utf8_bytes"] = cache["source"]["text_utf8_bytes"]
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _source_index_sha256(
    dictionary: dict[str, list[dict[str, object]]],
    rule_pages: dict[str, list[dict[str, object]]],
) -> str:
    encoded = json.dumps(
        {"dictionary": dictionary, "rule_pages": rule_pages},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _require_output_within(
    path: pathlib.Path,
    allowed_root: pathlib.Path,
    subject: str,
) -> None:
    resolved_root = allowed_root.resolve()
    resolved_path = path.resolve(strict=False)
    if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
        raise Ste100Error(
            subject + "-path-invalid",
            "The {} path is outside its documented local directory.".format(subject),
            "Use the fixed repository-local output location.",
        )


def _two_column_table(
    section: str,
    header: str,
) -> list[tuple[str, str]]:
    lines = section.splitlines()
    matches = [number for number, line in enumerate(lines) if line.strip() == header]
    if len(matches) != 1:
        raise Ste100Error(
            "technical-term-owner-invalid",
            "A canonical technical-term table is missing or duplicated.",
            "Restore one technical-noun table and one technical-verb table.",
        )
    header_number = matches[0]
    if (
        header_number + 1 >= len(lines)
        or re.fullmatch(
            r"\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|",
            lines[header_number + 1].strip(),
        )
        is None
    ):
        raise Ste100Error(
            "technical-term-owner-invalid",
            "A canonical technical-term table has no valid separator row.",
            "Restore the canonical two-column Markdown table.",
        )
    rows: list[tuple[str, str]] = []
    for line in lines[header_number + 2 :]:
        stripped = line.strip()
        if not stripped:
            break
        if not stripped.startswith("|") or not stripped.endswith("|"):
            break
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) != 2 or not all(cells):
            raise Ste100Error(
                "technical-term-owner-invalid",
                "A canonical technical-term row is not a two-column row.",
                "Correct the row in reference/TERMINOLOGY.md.",
            )
        rows.append((cells[0], cells[1]))
    if not rows:
        raise Ste100Error(
            "technical-term-owner-invalid",
            "A canonical technical-term table has no registrations.",
            "Restore the approved technical-term registrations.",
        )
    return rows


def _plain_markdown(value: str) -> str:
    value = re.sub(r"!?\[([^]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = value.replace("**", "")
    return re.sub(r"\s+", " ", value).strip()


def _noun_meaning(cell: str, term: str) -> str:
    marker = re.compile(r"\*\*{}\*\*".format(re.escape(term)), re.IGNORECASE)
    sentences = re.split(r"(?<=[.!?])\s+", cell)
    for sentence in sentences:
        if marker.search(sentence):
            return _plain_markdown(sentence)
    return _plain_markdown(cell)


def extract_project_terms(markdown: str) -> list[dict[str, str]]:
    """Read category-bound registrations from the canonical term tables."""
    heading = "## ASD-STE100 project terminology"
    if markdown.count(heading) != 1:
        raise Ste100Error(
            "technical-term-owner-invalid",
            "The canonical ASD-STE100 technical-term section is missing or duplicated.",
            "Restore one section in reference/TERMINOLOGY.md.",
        )
    section = markdown.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", section, re.MULTILINE)
    if next_heading is not None:
        section = section[: next_heading.start()]
    registrations: dict[tuple[str, str], dict[str, str]] = {}
    noun_rows = _two_column_table(
        section,
        "| Term group | Approved technical nouns and meaning |",
    )
    for term_group, cell in noun_rows:
        terms = dict.fromkeys(
            re.sub(r"\s+", " ", match).strip()
            for match in re.findall(r"\*\*([^*]+)\*\*", cell)
        )
        for term in terms:
            key = (term.casefold(), "noun")
            registration = {
                "canonical_term": term,
                "category": "noun",
                "meaning": _noun_meaning(cell, term),
                "term_group": _plain_markdown(term_group),
            }
            if key in registrations and registrations[key] != registration:
                raise Ste100Error(
                    "technical-term-owner-invalid",
                    "A technical noun has competing registered meanings.",
                    "Keep one canonical registration for each technical noun.",
                )
            registrations[key] = registration

    verb_rows = _two_column_table(
        section,
        "| Technical verb | Project meaning |",
    )
    for cell, meaning in verb_rows:
        terms = dict.fromkeys(
            re.sub(r"\s+", " ", match).strip()
            for match in re.findall(r"\*\*([^*]+)\*\*", cell)
        )
        for term in terms:
            key = (term.casefold(), "verb")
            registration = {
                "canonical_term": term,
                "category": "verb",
                "meaning": _plain_markdown(meaning),
                "term_group": "Technical verb",
            }
            if key in registrations and registrations[key] != registration:
                raise Ste100Error(
                    "technical-term-owner-invalid",
                    "A technical verb has competing registered meanings.",
                    "Keep one canonical registration for each technical verb.",
                )
            registrations[key] = registration

    if not registrations:
        raise Ste100Error(
            "technical-term-owner-invalid",
            "The canonical technical-term register has no registrations.",
            "Restore the approved technical nouns and technical verbs.",
        )
    return sorted(
        registrations.values(),
        key=lambda item: (item["canonical_term"].casefold(), item["category"]),
    )


def _minimal_extractor_environment() -> dict[str, str]:
    return {"LANG": "C", "LC_ALL": "C"}


def _read_bounded_stream(
    stream: object,
    limit: int,
    process: subprocess.Popen[bytes],
) -> bytes:
    chunks: list[bytes] = []
    size = 0
    try:
        while True:
            chunk = stream.read(64 * 1024)  # type: ignore[attr-defined]
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                process.kill()
                raise _SubprocessOutputLimitError
            chunks.append(chunk)
    finally:
        stream.close()  # type: ignore[attr-defined]
    return b"".join(chunks)


def _write_subprocess_input(stream: object, payload: bytes) -> None:
    try:
        stream.write(payload)  # type: ignore[attr-defined]
        stream.flush()  # type: ignore[attr-defined]
    except BrokenPipeError:
        # The return code and bounded stderr own the useful failure evidence.
        pass
    finally:
        stream.close()  # type: ignore[attr-defined]


def _run_bounded_process(
    command: list[str],
    *,
    input_bytes: bytes,
    stdout_limit: int,
    stderr_limit: int,
    timeout: int,
) -> tuple[int, bytes, bytes]:
    """Run one fixed local tool with bounded input, output, time, and env."""
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_minimal_extractor_environment(),
        )
    except OSError as error:
        raise Ste100Error(
            "extractor-start-failed",
            "The local PDF extractor could not start.",
            "Check the PDF extractor, then run an explicit rebuild.",
        ) from error
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    timed_out = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        stdout_future = executor.submit(
            _read_bounded_stream,
            process.stdout,
            stdout_limit,
            process,
        )
        stderr_future = executor.submit(
            _read_bounded_stream,
            process.stderr,
            stderr_limit,
            process,
        )
        input_future = executor.submit(
            _write_subprocess_input,
            process.stdin,
            input_bytes,
        )
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            return_code = process.wait()
        try:
            stdout = stdout_future.result()
            stderr = stderr_future.result()
            input_future.result()
        except _SubprocessOutputLimitError as error:
            if process.poll() is None:
                process.kill()
                process.wait()
            raise Ste100Error(
                "extractor-output-too-large",
                "The local PDF extractor exceeded a bounded output limit.",
                "Discard the result. Check the source and PDF extractor.",
            ) from error
    if timed_out:
        raise Ste100Error(
            "extractor-timeout",
            "The local PDF extraction did not finish within its time limit.",
            "Check the source and PDF extractor, then run an explicit rebuild.",
        )
    return return_code, stdout, stderr


def _validate_extractor_file(path: pathlib.Path, file_status: object) -> None:
    mode = getattr(file_status, "st_mode", None)
    owner_uid = getattr(file_status, "st_uid", None)
    effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
    if not isinstance(mode, int) or not stat.S_ISREG(mode):
        raise Ste100Error(
            "extractor-invalid",
            "The pdftotext path is not a regular file.",
            "Use a protected regular extractor outside the repository.",
        )
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise Ste100Error(
            "extractor-invalid",
            "The pdftotext path is writable by its group or by other users.",
            "Use an extractor that only its permitted owner can write.",
        )
    if effective_uid is None or not isinstance(owner_uid, int):
        raise Ste100Error(
            "extractor-owner-unverified",
            "The local PDF extractor owner cannot be established.",
            "Do not use the extractor on this platform.",
        )
    if owner_uid not in {0, effective_uid}:
        raise Ste100Error(
            "extractor-owner-untrusted",
            "The local PDF extractor is owned by a different local user.",
            "Use an extractor owned by root or by the current user.",
        )
    if path == ROOT or ROOT in path.parents:
        raise Ste100Error(
            "extractor-invalid",
            "The pdftotext path is inside the repository.",
            "Use a trusted development tool outside the repository.",
        )
    environment_root = pathlib.Path(sys.prefix).resolve()
    if sys.prefix != sys.base_prefix and (
        path == environment_root or environment_root in path.parents
    ):
        raise Ste100Error(
            "extractor-invalid",
            "The pdftotext path is inside the active Python environment.",
            "Use a trusted development tool outside the project environment.",
        )


def _extractor_identity() -> dict[str, object]:
    executable = shutil.which("pdftotext")
    if executable is None:
        raise Ste100Error(
            "extractor-missing",
            "The local pdftotext development tool is absent.",
            "Install a trusted local Poppler pdftotext tool, then rebuild the cache.",
        )
    try:
        path = pathlib.Path(executable).resolve(strict=True)
        file_status = path.stat()
    except OSError as error:
        raise Ste100Error(
            "extractor-invalid",
            "The local pdftotext development tool cannot be resolved.",
            "Install a trusted system pdftotext tool, then rebuild the cache.",
        ) from error
    _validate_extractor_file(path, file_status)
    return_code, stdout, stderr = _run_bounded_process(
        [str(path), "-v"],
        input_bytes=b"",
        stdout_limit=MAX_EXTRACTOR_ERROR_BYTES,
        stderr_limit=MAX_EXTRACTOR_ERROR_BYTES,
        timeout=10,
    )
    if return_code:
        raise Ste100Error(
            "extractor-invalid",
            "The local pdftotext development tool did not report its version.",
            "Install a trusted system pdftotext tool, then rebuild the cache.",
        )
    version_text = (stderr or stdout).decode("utf-8", errors="replace").strip()
    return {
        "mode": "{:04o}".format(stat.S_IMODE(file_status.st_mode)),
        "owner_uid": file_status.st_uid,
        "path": str(path),
        "sha256": sha256_file(path),
        "version": version_text.splitlines()[0] if version_text else "unknown",
    }


def _run_pdftotext(
    source_bytes: bytes,
    *,
    first_page: int | None = None,
    expected_identity: dict[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    identity = _extractor_identity()
    if expected_identity is not None and identity != expected_identity:
        raise Ste100Error(
            "extractor-identity-mismatch",
            "The current PDF extractor identity does not match the derived cache.",
            "Do not use source mode. Review the PDF extractor and rebuild explicitly.",
        )
    command = [str(identity["path"])]
    if first_page is not None:
        command.extend(["-f", str(first_page), "-l", str(first_page)])
    command.extend(["-layout", "-enc", "UTF-8", "-", "-"])
    return_code, stdout, stderr = _run_bounded_process(
        command,
        input_bytes=source_bytes,
        stdout_limit=(
            MAX_EXTRACTED_PAGE_BYTES
            if first_page is not None
            else MAX_EXTRACTED_TEXT_BYTES
        ),
        stderr_limit=MAX_EXTRACTOR_ERROR_BYTES,
        timeout=30 if first_page is not None else 120,
    )
    if return_code:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise Ste100Error(
            "extractor-failed",
            "The local PDF extractor failed: {}".format(detail or "no detail"),
            "Check the source and PDF extractor, then run an explicit rebuild.",
        )
    if _extractor_identity() != identity:
        raise Ste100Error(
            "extractor-identity-changed",
            "The pdftotext executable changed during extraction.",
            "Discard the result. Review the PDF extractor and rebuild explicitly.",
        )
    try:
        text = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "extractor-output-invalid",
            "The local PDF extractor did not return UTF-8 text.",
            "Discard the result. Check the source and PDF extractor.",
        ) from error
    return text, identity


def _extract_pdf_pages(
    source_bytes: bytes,
) -> tuple[list[str], dict[str, object]]:
    text, identity = _run_pdftotext(source_bytes)
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages, identity


def _extract_pdf_page(
    source_bytes: bytes,
    page_number: int,
    expected_identity: dict[str, object],
) -> str:
    text, _ = _run_pdftotext(
        source_bytes,
        first_page=page_number,
        expected_identity=expected_identity,
    )
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != 1:
        raise Ste100Error(
            "extraction-incomplete",
            "The bounded source extraction did not return exactly one page.",
            "Do not use the excerpt. Check the source and PDF extractor.",
        )
    return pages[0]


def _page_label(text: str, page_number: int) -> str:
    labels = PAGE_LABEL_RE.findall(text)
    return labels[-1] if labels else "PDF-{}".format(page_number)


def _dictionary_index(
    pages: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    entries: dict[str, list[dict[str, object]]] = {}
    for page in pages:
        source_label = str(page["source_label"])
        if not source_label.startswith("2-1-"):
            continue
        active_entry: dict[str, object] | None = None
        accept_forms = False
        pending_displayed: str | None = None
        for line in str(page["text"]).splitlines():
            left_column = line[:DICTIONARY_TERM_COLUMN_WIDTH]
            if pending_displayed is not None:
                continued_pos = DICTIONARY_CONTINUED_POS_RE.match(left_column)
                if continued_pos is not None:
                    active_entry = {
                        "displayed_word": pending_displayed,
                        "headword": pending_displayed,
                        "page_number": page["page_number"],
                        "part_of_speech": continued_pos.group(1),
                        "source_label": source_label,
                        "status": "inspect",
                    }
                    key = pending_displayed.casefold()
                    if active_entry not in entries.setdefault(key, []):
                        entries[key].append(active_entry)
                    pending_displayed = None
                    accept_forms = False
                    continue
                pending_displayed = None

            match = DICTIONARY_ENTRY_RE.match(left_column)
            if match is not None:
                displayed = re.sub(r"\s+", " ", match.group(1)).strip()
                status = "recognised" if displayed == displayed.upper() else "inspect"
                active_entry = {
                    "displayed_word": displayed,
                    "headword": displayed,
                    "page_number": page["page_number"],
                    "part_of_speech": match.group(2),
                    "source_label": source_label,
                    "status": status,
                }
                key = displayed.casefold()
                if active_entry not in entries.setdefault(key, []):
                    entries[key].append(active_entry)
                accept_forms = status == "recognised"
                continue
            form_match = DICTIONARY_FORM_RE.match(left_column) if accept_forms else None
            if form_match is not None and active_entry is not None:
                displayed = re.sub(r"\s+", " ", form_match.group(1)).strip()
                record = {
                    **active_entry,
                    "displayed_word": displayed,
                }
                key = displayed.casefold()
                if record not in entries.setdefault(key, []):
                    entries[key].append(record)
                continue
            pending_candidate = re.sub(r"\s+", " ", left_column).strip()
            if re.fullmatch(r"[a-z][A-Za-z0-9' -]*", pending_candidate):
                pending_displayed = pending_candidate
            accept_forms = False
    return dict(sorted(entries.items()))


def _rule_page_index(
    pages: list[dict[str, object]],
    identifiers: set[str],
) -> dict[str, list[dict[str, object]]]:
    results: dict[str, list[dict[str, object]]] = {}
    for identifier in sorted(identifiers):
        prefix = "" if identifier.startswith("GR-") else "Rule "
        section = "9" if identifier.startswith("GR-") else identifier.split(".", 1)[0]
        source_label_prefix = "1-{}-".format(section)
        pattern = re.compile(
            r"^\s*{}{}(?:\s|$)".format(prefix, re.escape(identifier)),
            re.MULTILINE,
        )
        hits = [
            {
                "page_number": page["page_number"],
                "source_label": page["source_label"],
            }
            for page in pages
            if str(page["source_label"]).startswith(source_label_prefix)
            and pattern.search(str(page["text"]))
        ]
        if not hits:
            raise Ste100Error(
                "extraction-incomplete",
                (
                    "The extracted source has no authoritative Part 1 location for {}."
                ).format(identifier),
                "Do not use this derived cache. Check the source and PDF extractor.",
            )
        results[identifier] = hits
    return results


def _validate_extractor_identity(identity: object) -> None:
    if (
        not isinstance(identity, dict)
        or set(identity) != {"mode", "owner_uid", "path", "sha256", "version"}
        or not isinstance(identity["mode"], str)
        or re.fullmatch(r"0[0-7]{3}", identity["mode"]) is None
        or not isinstance(identity["owner_uid"], int)
        or identity["owner_uid"] < 0
        or not isinstance(identity["path"], str)
        or not pathlib.PurePath(identity["path"]).is_absolute()
        or not isinstance(identity["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None
        or not isinstance(identity["version"], str)
        or not identity["version"]
    ):
        raise Ste100Error(
            "extractor-identity-invalid",
            "The derived cache has no valid extractor identity.",
            "Use the supported explicit rebuild route.",
        )


def build_cache_data(
    *,
    source_path: pathlib.Path,
    manifest_path: pathlib.Path,
    index_path: pathlib.Path,
    terminology_path: pathlib.Path,
    profile_path: pathlib.Path,
    extracted_pages: list[str] | None = None,
    extractor_identity: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build deterministic derived data after exact source verification."""
    manifest, _ = load_contracts(manifest_path, index_path)
    source_identity, source_bytes = _read_verified_source(source_path, manifest)
    if extracted_pages is None:
        extracted_pages, extractor_identity = _extract_pdf_pages(source_bytes)
    if extractor_identity is None:
        raise Ste100Error(
            "extractor-identity-missing",
            "The derived cache has no extractor identity.",
            "Use the supported explicit rebuild route.",
        )
    _validate_extractor_identity(extractor_identity)
    if len(extracted_pages) != manifest["page_count"]:
        raise Ste100Error(
            "source-page-count-mismatch",
            "Extraction returned {} pages; the source contract requires {}.".format(
                len(extracted_pages), manifest["page_count"]
            ),
            "Do not use this derived cache. Check the source identity and "
            "PDF extractor.",
        )
    pages = [
        {
            "page_number": number,
            "source_label": _page_label(text, number),
            "text": text,
        }
        for number, text in enumerate(extracted_pages, start=1)
    ]
    identifiers = expected_rule_ids() | expected_recommendation_ids()
    rule_pages = _rule_page_index(pages, identifiers)
    dictionary = _dictionary_index(pages)
    if not dictionary:
        raise Ste100Error(
            "extraction-incomplete",
            "The extracted source has no searchable dictionary entries.",
            "Do not use this derived cache. Check the source and PDF extractor.",
        )
    extraction_index_sha256 = _source_index_sha256(dictionary, rule_pages)
    if extraction_index_sha256 != manifest["extraction_index_sha256"]:
        raise Ste100Error(
            "extraction-index-mismatch",
            "The source-derived index does not match the authorised source contract.",
            "Do not use it. Check the exact source and protected PDF extractor.",
        )
    terms_text = terminology_path.read_text(encoding="utf-8")
    technical_terms = extract_project_terms(terms_text)
    source_identity["text_utf8_bytes"] = sum(
        len(text.encode("utf-8")) for text in extracted_pages
    )
    source_identity["extraction_index_sha256"] = extraction_index_sha256
    cache = {
        "dictionary": dictionary,
        "extractor_identity": extractor_identity,
        "inputs": _input_identities(
            manifest_path,
            index_path,
            terminology_path,
            profile_path,
        ),
        "rule_pages": rule_pages,
        "schema_version": manifest["cache_schema_version"],
        "source": source_identity,
        "technical_terms": technical_terms,
    }
    cache["derived_content_sha256"] = _derived_content_sha256(cache)
    return cache


def write_cache(cache_path: pathlib.Path, cache: dict[str, object]) -> None:
    """Write the derived cache atomically without following a cache symlink."""
    if cache_path.is_symlink():
        raise Ste100Error(
            "cache-path-invalid",
            "The cache path is a symbolic link.",
            "Remove the link and rebuild into the documented local cache path.",
        )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=cache_path.parent,
            prefix=".issue9-cache-",
            suffix=".json",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            json.dump(cache, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, cache_path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


def validate_cache_data(
    cache: dict[str, object],
    *,
    source_identity: dict[str, object],
    manifest: dict[str, object],
    input_identities: dict[str, str],
    expected_technical_terms: list[dict[str, str]],
) -> None:
    """Reject incompatible, stale, or internally inconsistent derived data."""
    required = {
        "derived_content_sha256",
        "dictionary",
        "extractor_identity",
        "inputs",
        "rule_pages",
        "schema_version",
        "source",
        "technical_terms",
    }
    if set(cache) != required:
        raise Ste100Error(
            "cache-invalid",
            "The cache fields do not match the supported schema.",
            "Delete no evidence. Run the explicit cache rebuild command.",
        )
    if cache["schema_version"] != manifest["cache_schema_version"]:
        raise Ste100Error(
            "cache-version-incompatible",
            "The derived cache version is incompatible.",
            "Run the explicit cache rebuild command.",
        )
    if cache["inputs"] != input_identities:
        raise Ste100Error(
            "cache-input-mismatch",
            "The cache does not match the tracked profile, terms, manifest, or index.",
            "Run the explicit cache rebuild command.",
        )
    if cache["technical_terms"] != expected_technical_terms:
        raise Ste100Error(
            "cache-technical-terms-mismatch",
            "The cache does not match the canonical technical-term register.",
            "Do not approve a cached term. Run the explicit cache rebuild command.",
        )
    _validate_extractor_identity(cache["extractor_identity"])
    cached_source = cache["source"]
    if not isinstance(cached_source, dict) or any(
        cached_source.get(key) != source_identity.get(key)
        for key in (
            "filename",
            "issue",
            "page_count",
            "publication_date",
            "sha256",
            "size_bytes",
            "standard_id",
        )
    ):
        raise Ste100Error(
            "cache-source-mismatch",
            "The cache metadata does not match the verified source.",
            "Do not reuse it. Run the explicit cache rebuild command.",
        )
    if (
        cached_source.get("extraction_index_sha256")
        != manifest["extraction_index_sha256"]
        or not isinstance(cached_source.get("text_utf8_bytes"), int)
        or cached_source["text_utf8_bytes"] <= 0
    ):
        raise Ste100Error(
            "cache-invalid",
            "The cache source-derived metadata is incomplete or incompatible.",
            "Run the explicit cache rebuild command.",
        )
    rule_pages = cache["rule_pages"]
    required_ids = expected_rule_ids() | expected_recommendation_ids()
    if not isinstance(rule_pages, dict) or set(rule_pages) != required_ids:
        raise Ste100Error(
            "cache-invalid",
            "The cached rule-location set is incomplete.",
            "Run the explicit cache rebuild command.",
        )
    for identifier, hits in rule_pages.items():
        section = "9" if identifier.startswith("GR-") else identifier.split(".", 1)[0]
        if (
            not isinstance(hits, list)
            or not hits
            or any(
                not isinstance(hit, dict)
                or set(hit) != {"page_number", "source_label"}
                or not isinstance(hit["page_number"], int)
                or not 1 <= hit["page_number"] <= manifest["page_count"]
                or not str(hit["source_label"]).startswith("1-{}-".format(section))
                for hit in hits
            )
        ):
            raise Ste100Error(
                "cache-invalid",
                "A cached rule source location is invalid.",
                "Run the explicit cache rebuild command.",
            )
    dictionary = cache["dictionary"]
    if not isinstance(dictionary, dict) or not dictionary:
        raise Ste100Error(
            "cache-invalid",
            "The cached dictionary index is absent or empty.",
            "Run the explicit cache rebuild command.",
        )
    dictionary_fields = {
        "displayed_word",
        "headword",
        "page_number",
        "part_of_speech",
        "source_label",
        "status",
    }
    for query, entries in dictionary.items():
        if (
            not isinstance(query, str)
            or not query
            or not isinstance(entries, list)
            or not entries
            or any(
                not isinstance(entry, dict)
                or set(entry) != dictionary_fields
                or not isinstance(entry["page_number"], int)
                or not 1 <= entry["page_number"] <= manifest["page_count"]
                or not str(entry["source_label"]).startswith("2-1-")
                or entry["status"] not in {"recognised", "inspect"}
                for entry in entries
            )
        ):
            raise Ste100Error(
                "cache-invalid",
                "A cached dictionary lookup record is invalid.",
                "Run the explicit cache rebuild command.",
            )
    if (
        _source_index_sha256(dictionary, rule_pages)
        != manifest["extraction_index_sha256"]
    ):
        raise Ste100Error(
            "cache-source-index-mismatch",
            "The derived cache does not match the authorised source-derived index.",
            "Do not use it. Run the explicit cache rebuild command.",
        )
    if cache["derived_content_sha256"] != _derived_content_sha256(cache):
        raise Ste100Error(
            "cache-content-mismatch",
            "The derived cache content does not match its integrity metadata.",
            "Do not use it. Run the explicit cache rebuild command.",
        )


def load_verified_cache(
    *,
    source_path: pathlib.Path = SOURCE_FILE,
    cache_path: pathlib.Path = CACHE_FILE,
    manifest_path: pathlib.Path = SOURCE_MANIFEST,
    index_path: pathlib.Path = RETRIEVAL_INDEX,
    terminology_path: pathlib.Path = TERMINOLOGY,
    profile_path: pathlib.Path = APPLICATION_PROFILE,
) -> tuple[dict[str, object], dict[str, object], bytes]:
    """Load a cache only after current source and tracked-input verification."""
    manifest, index = load_contracts(manifest_path, index_path)
    source_identity, source_bytes = _read_verified_source(source_path, manifest)
    if not cache_path.is_file() or cache_path.is_symlink():
        raise Ste100Error(
            "cache-missing",
            "No verified local Issue 9 cache is available.",
            "Run: .venv/bin/python tools/ste100_lookup.py rebuild",
        )
    cache = _read_json_object(
        cache_path,
        "cache",
        max_bytes=MAX_CACHE_JSON_BYTES,
    )
    identities = _input_identities(
        manifest_path,
        index_path,
        terminology_path,
        profile_path,
    )
    validate_cache_data(
        cache,
        source_identity=source_identity,
        manifest=manifest,
        input_identities=identities,
        expected_technical_terms=extract_project_terms(
            terminology_path.read_text(encoding="utf-8")
        ),
    )
    return cache, index, source_bytes


def rebuild_cache() -> dict[str, object]:
    """Rebuild the fixed derived cache after source verification."""
    _require_output_within(CACHE_FILE, REFERENCE_DIR, "cache")
    cache = build_cache_data(
        source_path=SOURCE_FILE,
        manifest_path=SOURCE_MANIFEST,
        index_path=RETRIEVAL_INDEX,
        terminology_path=TERMINOLOGY,
        profile_path=APPLICATION_PROFILE,
    )
    write_cache(CACHE_FILE, cache)
    return cache


def _controls() -> dict[str, str]:
    return {
        "applicability": (
            "all-applicable-issue-9-rules-and-controlled-vocabulary-remain-mandatory"
        ),
        "assurance": "lookup-and-automatic-checks-do-not-prove-conformance",
        "retrieval_scope": "returned-items-only",
    }


def _dictionary_headword_count(cache: dict[str, object]) -> int:
    return len(
        {
            str(entry["headword"]).casefold()
            for entries in cache["dictionary"].values()
            for entry in entries
        }
    )


def _families(index: dict[str, object]) -> list[dict[str, object]]:
    return list(index["families"])


def _family_summary(family: dict[str, object]) -> dict[str, object]:
    return {
        "id": family["id"],
        "source_location": family["source_location"],
        "title": family["title"],
        "topic_tags": family["topic_tags"],
    }


def _family_for_identifier(
    index: dict[str, object], identifier: str
) -> tuple[dict[str, object], str]:
    normalised = (
        identifier.upper() if identifier.upper().startswith("GR-") else identifier
    )
    for family in _families(index):
        if normalised in family["rule_ids"]:
            return family, "formal-rule"
        if normalised in family.get("recommendation_ids", []):
            return family, "general-recommendation"
    raise Ste100Error(
        "rule-not-found",
        "The index has no rule or recommendation {}.".format(identifier),
        "Check the identifier or use a topic lookup.",
    )


def _load_source_page(
    page_loader: Callable[[int], str] | None,
    page_number: int,
    source_label: str,
) -> str:
    if page_loader is None:
        raise Ste100Error(
            "source-loader-missing",
            "Source mode has no verified bounded-page loader.",
            "Use the supported command-line source mode.",
        )
    text = page_loader(page_number)
    if _page_label(text, page_number) != source_label:
        raise Ste100Error(
            "source-page-location-mismatch",
            "The bounded source page does not match its source-derived index location.",
            "Do not use the excerpt. Check the source and PDF extractor.",
        )
    return text


def _bounded_excerpt(text: str, needle: re.Pattern[str]) -> str:
    lines = text.splitlines()
    match = needle.search(text)
    if match is None:
        raise Ste100Error(
            "source-target-not-found",
            "The indexed source page does not contain the source item.",
            "Do not use an excerpt from another item. Check the source, "
            "retrieval index, and PDF extractor.",
        )
    match_line = text.count("\n", 0, match.start())
    start = max(0, match_line - 1)
    excerpt = "\n".join(lines[start : match_line + 5]).strip()
    if len(excerpt) > MAX_SOURCE_EXCERPT_CHARS:
        excerpt = excerpt[:MAX_SOURCE_EXCERPT_CHARS].rstrip() + "…"
    return excerpt


def _dictionary_source_pattern(
    headword: str,
    part_of_speech: str,
) -> re.Pattern[str]:
    """Match one indexed dictionary item in either supported source layout."""
    words = r"\s+".join(re.escape(item) for item in headword.split())
    part = re.escape(part_of_speech)
    return re.compile(
        r"^\s{{0,2}}{}(?:\s+\({}\)|[^\n]*\n\s*"
        r"(?:\([^)]*\)\s*)?\({}\))".format(
            words,
            part,
            part,
        ),
        re.IGNORECASE | re.MULTILINE,
    )


def lookup_rule(
    identifier: str,
    cache: dict[str, object],
    index: dict[str, object],
    *,
    include_source: bool = False,
    page_loader: Callable[[int], str] | None = None,
) -> dict[str, object]:
    """Return compact metadata for one rule or recommendation."""
    family, kind = _family_for_identifier(index, identifier)
    normalised = identifier.upper() if kind == "general-recommendation" else identifier
    result: dict[str, object] = {
        "controls": _controls(),
        "family": _family_summary(family),
        "identifier": normalised,
        "kind": kind,
    }
    if kind == "general-recommendation":
        result["classification"] = "recommendation-not-formal-rule"
    if include_source:
        # Section-opening material can name all rules before their normative
        # occurrences. The final section-local hit is the rule occurrence.
        hit = cache["rule_pages"][normalised][-1]
        page_number = int(hit["page_number"])
        source_label = str(hit["source_label"])
        page_text = _load_source_page(
            page_loader,
            page_number,
            source_label,
        )
        prefix = "" if normalised.startswith("GR-") else "Rule "
        result["source_excerpt"] = {
            "page_number": page_number,
            "source_label": source_label,
            "text": _bounded_excerpt(
                page_text,
                re.compile(
                    r"^\s*{}{}(?:\s|$)".format(
                        prefix,
                        re.escape(normalised),
                    ),
                    re.MULTILINE,
                ),
            ),
        }
    return result


def lookup_topic(
    topic: str,
    index: dict[str, object],
    *,
    verbose: bool = False,
) -> dict[str, object]:
    """Return retrieval families whose metadata matches one topic."""
    query = topic.casefold().strip().replace(" ", "-")
    if not query or len(query) > 100:
        raise Ste100Error(
            "topic-query-invalid",
            "The topic query is empty or too long.",
            "Use one short topic name.",
        )
    matches = []
    for family in _families(index):
        values = [
            str(family["id"]),
            str(family["title"]).replace(" ", "-"),
            *[str(tag) for tag in family["topic_tags"]],
        ]
        if any(query in value.casefold() for value in values):
            matches.append(_family_summary(family))
    if not matches:
        raise Ste100Error(
            "topic-not-found",
            "No retrieval metadata matches topic {!r}.".format(topic),
            "Use a broader topic or inspect the tracked retrieval index.",
        )
    limit = len(matches) if verbose else 5
    return {
        "controls": _controls(),
        "matches": matches[:limit],
        "query": topic,
        "returned_count": min(len(matches), limit),
        "total_matches": len(matches),
    }


def lookup_review_category(
    category_id: str,
    index: dict[str, object],
) -> dict[str, object]:
    """Return retrieval priorities, never a reduced applicability decision."""
    categories = {
        str(category["id"]): category for category in index["review_categories"]
    }
    if category_id not in categories:
        raise Ste100Error(
            "review-category-not-found",
            "The retrieval index has no review category {!r}.".format(category_id),
            "Use a category in the tracked retrieval index.",
        )
    by_id = {str(family["id"]): family for family in _families(index)}
    priorities = categories[category_id]["retrieval_priority_families"]
    return {
        "category": category_id,
        "controls": _controls(),
        "retrieval_priorities": [
            _family_summary(by_id[family_id]) for family_id in priorities
        ],
    }


def _normalise_term(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _third_person_verb(word: str) -> str:
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh", "o")):
        return word + "es"
    return word + "s"


def _project_term_forms(
    terms: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    forms: dict[str, list[dict[str, str]]] = {}
    for registration in terms:
        term = registration["canonical_term"]
        normalised = _normalise_term(term)
        exact_registration = dict(registration)
        exact_registration["match_basis"] = "exact-registered-form"
        forms.setdefault(normalised, []).append(exact_registration)
        words = normalised.split()
        if not words:
            continue
        if registration["category"] == "verb":
            verb_registration = dict(registration)
            verb_registration["match_basis"] = "inferred-verb-third-person"
            forms.setdefault(
                " ".join([_third_person_verb(words[0])] + words[1:]),
                [],
            ).append(verb_registration)
            continue
        last = words[-1]
        if last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
            plural = last[:-1] + "ies"
        elif last.endswith(("s", "x", "z", "ch", "sh")):
            plural = last + "es"
        else:
            plural = last + "s"
        plural_registration = dict(registration)
        plural_registration["match_basis"] = "inferred-noun-plural"
        forms.setdefault(
            " ".join(words[:-1] + [plural]),
            [],
        ).append(plural_registration)
    return forms


def _term_form_pattern(form: str) -> re.Pattern[str]:
    words = form.split()
    return re.compile(r"(?<!\w){}(?!\w)".format(r"\s+".join(map(re.escape, words))))


def _possible_inflection_bases(query: str) -> list[str]:
    """Return bounded base-form candidates without assigning approval."""
    if not query.isalpha() or len(query) < 5:
        return []
    candidates: set[str] = set()
    if query.endswith("ies") and len(query) > 4:
        candidates.add(query[:-3] + "y")
    if query.endswith("es") and len(query) > 4:
        candidates.update((query[:-1], query[:-2]))
    elif query.endswith("s") and len(query) > 4:
        candidates.add(query[:-1])
    if query.endswith("ed") and len(query) > 4:
        stem = query[:-2]
        candidates.update((stem, query[:-1]))
        if len(stem) > 2 and stem[-1] == stem[-2]:
            candidates.add(stem[:-1])
    if query.endswith("ing") and len(query) > 5:
        stem = query[:-3]
        candidates.update((stem, stem + "e"))
        if len(stem) > 2 and stem[-1] == stem[-2]:
            candidates.add(stem[:-1])
    candidates.discard(query)
    return sorted(candidate for candidate in candidates if len(candidate) >= 3)


def _dictionary_matches(
    query: str,
    cache: dict[str, object],
) -> tuple[list[dict[str, object]], str]:
    exact = cache["dictionary"].get(query, [])
    if exact:
        return exact, "exact-dictionary-form"
    candidates: list[dict[str, object]] = []
    for base in _possible_inflection_bases(query):
        for entry in cache["dictionary"].get(base, []):
            candidate = dict(entry)
            candidate["status"] = "inspect"
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates, "possible-inflection-base"


def lookup_word(
    word: str,
    cache: dict[str, object],
    *,
    part_of_speech: str | None = None,
    include_source: bool = False,
    page_loader: Callable[[int], str] | None = None,
) -> dict[str, object]:
    """Classify one term without adding it to a terminology owner."""
    query = _normalise_term(word)
    if not query or len(query) > 100:
        raise Ste100Error(
            "word-query-invalid",
            "The word query is empty or too long.",
            "Use one word or one short project technical term.",
        )
    if part_of_speech not in {None, "noun", "verb"}:
        raise Ste100Error(
            "word-part-of-speech-invalid",
            "The requested technical-term category is invalid.",
            "Use noun or verb when the contextual category is known.",
        )
    project_terms = _project_term_forms(cache["technical_terms"])
    result: dict[str, object] = {
        "controls": _controls(),
        "query": word,
    }
    if query in project_terms:
        registrations = project_terms[query]
        category_matches = [
            item
            for item in registrations
            if part_of_speech is None or item["category"] == part_of_speech
        ]
        exact_matches = [
            item
            for item in category_matches
            if item["match_basis"] == "exact-registered-form"
        ]
        if not category_matches:
            selected = registrations
            status = "technical-term-category-mismatch-review-required"
        elif exact_matches:
            selected = exact_matches
            status = "approved-tracktemplate-technical-term"
        else:
            selected = category_matches
            status = "technical-term-inflection-review-required"
        canonical_terms = sorted(
            {item["canonical_term"] for item in selected},
            key=str.casefold,
        )
        result.update(
            {
                "approval_changed": False,
                "canonical_term": (
                    canonical_terms[0] if len(canonical_terms) == 1 else canonical_terms
                ),
                "contextual_usage_review_required": True,
                "registered_usages": selected,
                "requested_part_of_speech": part_of_speech,
                "source": "reference/TERMINOLOGY.md",
                "status": status,
            }
        )
        return result

    entries, match_basis = _dictionary_matches(query, cache)
    if entries:
        recognised = [entry for entry in entries if entry["status"] == "recognised"]
        result["dictionary_entries"] = [
            {
                "displayed_word": entry["displayed_word"],
                "headword": entry["headword"],
                "match_basis": match_basis,
                "part_of_speech": entry["part_of_speech"],
                "source_label": entry["source_label"],
                "status": entry["status"],
            }
            for entry in entries
        ]
        result["inspection_required"] = True
        result["status"] = (
            "recognised-ste-vocabulary"
            if recognised
            else "dictionary-inspection-required"
        )
        if include_source:
            entry = recognised[0] if recognised else entries[0]
            page_number = int(entry["page_number"])
            source_label = str(entry["source_label"])
            page_text = _load_source_page(
                page_loader,
                page_number,
                source_label,
            )
            result["source_excerpt"] = {
                "page_number": page_number,
                "source_label": source_label,
                "text": _bounded_excerpt(
                    page_text,
                    _dictionary_source_pattern(
                        str(entry["headword"]),
                        str(entry["part_of_speech"]),
                    ),
                ),
            }
        return result

    result.update(
        {
            "approval_changed": False,
            "status": "unresolved-terminology-review-required",
        }
    )
    return result


def _markdown_prose(text: str) -> tuple[str, dict[str, int]]:
    lines: list[str] = []
    fenced_lines = 0
    inline_code_items = 0
    table_rows = 0
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            fenced_lines += 1
            continue
        if in_fence:
            fenced_lines += 1
            continue
        if re.fullmatch(r"\s*\|?(?:\s*:?-+:?\s*\|)+\s*", line):
            continue
        inline_code_items += len(re.findall(r"`[^`]+`", line))
        line = re.sub(r"`[^`]+`", " ", line)
        line = re.sub(r"!?\[([^]]*)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"^\s{0,3}(?:#{1,6}|[-*+] |\d+[.)] )", "", line)
        if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            table_rows += 1
            cells = [cell.strip() for cell in line.strip()[1:-1].split("|")]
            lines.append("\n\n".join(cells) + "\n")
            continue
        lines.append(line)
    return "\n".join(lines), {
        "fenced_lines": fenced_lines,
        "inline_code_items": inline_code_items,
        "table_rows": table_rows,
    }


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n\s*\n", text)
        if sentence.strip()
    ]


def precheck_text(
    text: str,
    category: str,
    cache: dict[str, object],
    *,
    verbose: bool = False,
) -> dict[str, object]:
    """Identify deterministic review candidates without a conformance claim."""
    if category not in {"descriptive", "procedural", "safety"}:
        raise Ste100Error(
            "review-category-invalid",
            "The pre-check category is invalid.",
            "Use descriptive, procedural, or safety.",
        )
    prose, exclusions = _markdown_prose(text)
    sentences = _sentences(prose)
    word_limit = 25 if category == "descriptive" else 20
    long_sentences = []
    for number, sentence in enumerate(sentences, start=1):
        count = len(WORD_RE.findall(sentence))
        if count > word_limit:
            long_sentences.append(
                {
                    "detected_words": count,
                    "sentence_number": number,
                    "text": sentence[:160],
                }
            )

    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", prose) if item.strip()]
    long_paragraphs = []
    if category == "descriptive":
        for number, paragraph in enumerate(paragraphs, start=1):
            count = len(_sentences(paragraph))
            if count > 6:
                long_paragraphs.append(
                    {"detected_sentences": count, "paragraph_number": number}
                )

    project_terms = _project_term_forms(cache["technical_terms"])
    prose_folded = prose.casefold()
    matched_project_terms = {
        normalised: registrations
        for normalised, registrations in project_terms.items()
        if _term_form_pattern(normalised).search(prose_folded)
    }
    used_project_terms_by_key: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for matched_form, registrations in matched_project_terms.items():
        for registration in registrations:
            key = (
                registration["canonical_term"].casefold(),
                registration["category"],
                matched_form,
                registration["match_basis"],
            )
            used_project_terms_by_key[key] = {
                "canonical_term": registration["canonical_term"],
                "category": registration["category"],
                "match_basis": registration["match_basis"],
                "matched_form": matched_form,
                "meaning": registration["meaning"],
                "status": (
                    "approved-tracktemplate-technical-term"
                    if registration["match_basis"] == "exact-registered-form"
                    else "technical-term-inflection-review-required"
                ),
            }
    used_project_terms = [
        used_project_terms_by_key[key] for key in sorted(used_project_terms_by_key)
    ]
    dictionary_candidates: set[str] = set()
    unresolved_candidates: set[str] = set()
    technical_term_words = {
        token.casefold()
        for matched_form in matched_project_terms
        for token in WORD_RE.findall(matched_form)
    }
    prose_tokens = WORD_RE.findall(prose)
    token_counts = Counter(token.casefold() for token in prose_tokens)
    display_by_key: dict[str, str] = {}
    for token in prose_tokens:
        display_by_key.setdefault(token.casefold(), token)
    for key in sorted(display_by_key):
        token = display_by_key[key]
        if key in technical_term_words or len(key) < 4:
            continue
        entries, match_basis = _dictionary_matches(key, cache)
        if entries and (
            match_basis == "possible-inflection-base"
            or not any(entry["status"] == "recognised" for entry in entries)
        ):
            dictionary_candidates.add(token)
        elif not entries and (
            token_counts[key] >= 3 or token.isupper() or "-" in token
        ):
            unresolved_candidates.add(token)

    construction_candidates = []
    if ";" in prose:
        construction_candidates.append("semicolon")
    if CONTRACTION_RE.search(prose):
        construction_candidates.append("contraction")
    terminology_candidates = []
    if re.search(r"\bordinary track\b", prose, re.IGNORECASE):
        terminology_candidates.append(
            {
                "candidate": "ordinary track",
                "review_against": "plain line",
            }
        )
    dictionary_items = sorted(dictionary_candidates)
    unresolved_items = sorted(unresolved_candidates)
    result_limits = {
        "project_technical_terms_found": 30,
        "sentence_length_review": 30,
        "ste_dictionary_inspection_candidates": 20,
        "unresolved_vocabulary_candidates": 20,
    }

    def bounded(items: list[object], subject: str) -> list[object]:
        if verbose:
            return items
        return items[: result_limits[subject]]

    complete_results: dict[str, list[object]] = {
        "project_technical_terms_found": used_project_terms,
        "sentence_length_review": long_sentences,
        "ste_dictionary_inspection_candidates": dictionary_items,
        "unresolved_vocabulary_candidates": unresolved_items,
    }
    result_counts = {
        subject: {
            "returned_count": len(bounded(items, subject)),
            "total_count": len(items),
            "truncated": not verbose and len(items) > result_limits[subject],
        }
        for subject, items in complete_results.items()
    }
    return {
        "category": category,
        "candidate_totals": {
            "dictionary_inspection": len(dictionary_candidates),
            "unresolved_vocabulary": len(unresolved_candidates),
        },
        "controls": _controls(),
        "exact_content_exclusions": exclusions,
        "likely_construction_review": construction_candidates,
        "likely_inconsistent_terminology": terminology_candidates,
        "paragraph_length_review": long_paragraphs,
        "project_technical_terms_found": bounded(
            used_project_terms,
            "project_technical_terms_found",
        ),
        "result_counts": result_counts,
        "sentence_length_review": bounded(
            long_sentences,
            "sentence_length_review",
        ),
        "sentence_word_limit_reference": word_limit,
        "ste_dictionary_inspection_candidates": bounded(
            dictionary_items,
            "ste_dictionary_inspection_candidates",
        ),
        "unresolved_vocabulary_candidates": bounded(
            unresolved_items,
            "unresolved_vocabulary_candidates",
        ),
        "limitations": [
            "Candidate detection is deterministic but does not interpret every "
            "Issue 9 rule.",
            "Sentence counts are pre-check hints; review the official "
            "word-count rules.",
            "An unresolved lowercase token is reported only after three "
            "occurrences; review single occurrences during the full prose review.",
            "A technical-term match does not determine its contextual noun or "
            "verb category. Review each use against its registered meaning.",
            "An inferred project-term form requires review and does not receive "
            "technical-term approval.",
            "No finding and no empty result proves linguistic conformance.",
        ],
    }


def _read_review_document(path: pathlib.Path) -> str:
    try:
        stream = path.open("rb")
    except (FileNotFoundError, IsADirectoryError, OSError) as error:
        raise Ste100Error(
            "review-document-missing",
            "The review document is absent or is not a regular file.",
            "Give one existing UTF-8 text or Markdown file.",
        ) from error
    try:
        with stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise Ste100Error(
                    "review-document-missing",
                    "The review document is absent or is not a regular file.",
                    "Give one existing UTF-8 text or Markdown file.",
                )
            payload = stream.read(MAX_REVIEW_DOCUMENT_BYTES + 1)
    except OSError as error:
        raise Ste100Error(
            "review-document-unreadable",
            "The review document cannot be read.",
            "Give one readable UTF-8 text or Markdown file.",
        ) from error
    return _decode_review_text(payload)


def _decode_review_text(payload: bytes) -> str:
    if len(payload) > MAX_REVIEW_DOCUMENT_BYTES:
        raise Ste100Error(
            "review-document-too-large",
            "The review document exceeds the bounded pre-check size.",
            "Review smaller logical units separately.",
        )
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "review-document-not-utf8",
            "The review document is not valid UTF-8 text.",
            "Use a UTF-8 text representation for the review.",
        ) from error


def _document_identity(path: pathlib.Path, text: str) -> dict[str, object]:
    resolved = path.resolve()
    encoded = text.encode("utf-8")
    return {
        "path": (
            resolved.relative_to(ROOT).as_posix()
            if resolved == ROOT or ROOT in resolved.parents
            else path.name
        ),
        "sha256": _sha256_bytes(encoded),
        "size_bytes": len(encoded),
    }


def precheck_document(
    path: pathlib.Path,
    category: str,
    cache: dict[str, object],
    *,
    verbose: bool = False,
) -> dict[str, object]:
    text = _read_review_document(path)
    result = precheck_text(text, category, cache, verbose=verbose)
    result["document"] = _document_identity(path, text)
    return result


def _changed_review_scope(
    baseline_text: str,
    candidate_text: str,
) -> tuple[str, dict[str, int]]:
    baseline_lines = baseline_text.splitlines()
    candidate_lines = candidate_text.splitlines()
    chunks: list[str] = []
    reviewed_line_count = 0
    for (
        operation,
        _first,
        _last,
        candidate_first,
        candidate_last,
    ) in difflib.SequenceMatcher(
        a=baseline_lines,
        b=candidate_lines,
        autojunk=False,
    ).get_opcodes():
        if operation not in {"insert", "replace"} or candidate_first == candidate_last:
            continue
        chunk = "\n".join(candidate_lines[candidate_first:candidate_last])
        if chunk:
            chunks.append(chunk)
            reviewed_line_count += candidate_last - candidate_first
    reviewed_text = "\n\n".join(chunks)
    if not reviewed_text:
        raise Ste100Error(
            "review-scope-empty",
            "The baseline comparison contains no candidate prose to review.",
            "Use the exact earlier revision and a candidate with changed prose.",
        )
    return reviewed_text, {
        "hunk_count": len(chunks),
        "line_count": reviewed_line_count,
    }


def make_review_receipt(
    *,
    document_path: pathlib.Path,
    category: str,
    cache: dict[str, object],
    index: dict[str, object],
    full_applicability_considered: bool,
    rule_ids: list[str],
    words: list[str],
    topics: list[str],
    exact_content_exclusions: list[str],
    unresolved_uncertainties: list[str],
    baseline_text: str | None = None,
    baseline_revision: str | None = None,
) -> dict[str, object]:
    """Create a generated review record after explicit human confirmation."""
    if not full_applicability_considered:
        raise Ste100Error(
            "full-applicability-not-confirmed",
            "The receipt needs explicit confirmation of full applicability review.",
            "Review all applicable requirements, then use the confirmation flag.",
        )
    receipt_inputs = {
        "exact-content exclusions": exact_content_exclusions,
        "rule identifiers": rule_ids,
        "topics": topics,
        "unresolved uncertainties": unresolved_uncertainties,
        "words": words,
    }
    for subject, values in receipt_inputs.items():
        if len(values) > MAX_RECEIPT_ITEMS or any(
            not isinstance(value, str) or not value or len(value.encode("utf-8")) > 500
            for value in values
        ):
            raise Ste100Error(
                "receipt-input-invalid",
                "The {} exceed the bounded receipt input.".format(subject),
                "Use concise bounded receipt evidence.",
            )
    candidate_text = _read_review_document(document_path)
    document = _document_identity(document_path, candidate_text)
    if (baseline_text is None) != (baseline_revision is None):
        raise Ste100Error(
            "review-baseline-invalid",
            "The changed-unit review needs both baseline text and its revision.",
            "Supply one exact 40-character Git revision and its document text.",
        )
    if baseline_text is None:
        reviewed_text = candidate_text
        reviewed_scope: dict[str, object] = {
            "kind": "complete-document",
            "reviewed_text": {
                "hunk_count": 1,
                "line_count": len(candidate_text.splitlines()),
                "sha256": document["sha256"],
                "size_bytes": document["size_bytes"],
            },
        }
    else:
        if re.fullmatch(r"[0-9a-f]{40}", str(baseline_revision)) is None:
            raise Ste100Error(
                "review-baseline-invalid",
                "The review baseline is not one exact Git revision.",
                "Supply the complete lowercase commit identifier.",
            )
        baseline_payload = baseline_text.encode("utf-8")
        if len(baseline_payload) > MAX_REVIEW_DOCUMENT_BYTES:
            raise Ste100Error(
                "review-document-too-large",
                "The review baseline exceeds the bounded pre-check size.",
                "Review smaller logical units separately.",
            )
        baseline_prose, _baseline_exclusions = _markdown_prose(baseline_text)
        candidate_prose, _candidate_exclusions = _markdown_prose(candidate_text)
        reviewed_text, scope_counts = _changed_review_scope(
            baseline_prose,
            candidate_prose,
        )
        reviewed_payload = reviewed_text.encode("utf-8")
        reviewed_scope = {
            "baseline_document": {
                "path": document["path"],
                "sha256": _sha256_bytes(baseline_payload),
                "size_bytes": len(baseline_payload),
            },
            "baseline_revision": baseline_revision,
            "candidate_document": document,
            "kind": "changed-canonical-prose-bundle",
            "reviewed_text": {
                **scope_counts,
                "sha256": _sha256_bytes(reviewed_payload),
                "size_bytes": len(reviewed_payload),
            },
        }
    precheck = precheck_text(reviewed_text, category, cache)
    targeted = {
        "rules": [lookup_rule(item, cache, index) for item in rule_ids],
        "topics": [lookup_topic(item, index) for item in topics],
        "words": [lookup_word(item, cache) for item in words],
    }
    return {
        "assurance_status": (
            "review-record-not-external-certification-or-automatic-proof"
        ),
        "controls": _controls(),
        "document": document,
        "exact_content_exclusions": exact_content_exclusions,
        "full_applicability_considered": True,
        "precheck": precheck,
        "profile_revision": "sha256:" + cache["inputs"]["application_profile_sha256"],
        "receipt_schema_version": 2,
        "review_scope": reviewed_scope,
        "source_identity": cache["source"],
        "targeted_lookups": targeted,
        "technical_term_status": {
            "project_term_matches": precheck["project_technical_terms_found"],
            "dictionary_inspection_candidates": precheck[
                "ste_dictionary_inspection_candidates"
            ],
            "unresolved_candidates": precheck["unresolved_vocabulary_candidates"],
        },
        "unresolved_uncertainties": unresolved_uncertainties,
    }


def write_review_receipt(
    document_path: pathlib.Path,
    receipt: dict[str, object],
    receipt_dir: pathlib.Path = RECEIPT_DIR,
    allowed_root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Write or reuse one content-addressed generated receipt."""
    if allowed_root is not None:
        _require_output_within(receipt_dir, allowed_root, "receipt")
    if receipt_dir.is_symlink():
        raise Ste100Error(
            "receipt-path-invalid",
            "The generated receipt directory is a symbolic link.",
            "Use the fixed repository-local receipt directory.",
        )
    receipt_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(receipt_dir, 0o700)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", document_path.stem).strip("-")
    content = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(content.encode("utf-8")) > MAX_RECEIPT_BYTES:
        raise Ste100Error(
            "receipt-too-large",
            "The generated receipt exceeds its local size limit.",
            "Use concise bounded receipt evidence.",
        )
    document_digest = str(receipt["document"]["sha256"])[:12]
    receipt_digest = _sha256_bytes(content.encode("utf-8"))[:12]
    path = receipt_dir / "{}-{}-{}.json".format(
        safe_stem or "document",
        document_digest,
        receipt_digest,
    )
    if path.exists():
        if (
            path.is_symlink()
            or path.stat().st_size != len(content.encode("utf-8"))
            or path.read_text(encoding="utf-8") != content
        ):
            raise Ste100Error(
                "receipt-path-conflict",
                "The generated receipt path contains different content.",
                "Inspect the existing local receipt; do not overwrite it silently.",
            )
        os.chmod(path, 0o600)
        return path
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
    except FileExistsError as error:
        raise Ste100Error(
            "receipt-path-conflict",
            "Another process created the receipt path.",
            "Inspect the local receipt and rerun if necessary.",
        ) from error
    return path


def _lifecycle_text(value: object, subject: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.encode("utf-8")) > 1000
    ):
        raise Ste100Error(
            "ste-lifecycle-invalid",
            "The STE lifecycle record has invalid {}.".format(subject),
            "Use concise UTF-8 text.",
        )
    return value


def _lifecycle_sha256(value: object, subject: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise Ste100Error(
            "ste-lifecycle-invalid",
            "The STE lifecycle record has an invalid {}.".format(subject),
            "Use one lowercase SHA-256 value.",
        )
    return value


def _lifecycle_path(value: object, subject: str) -> str:
    path_text = _lifecycle_text(value, subject)
    pure_path = pathlib.PurePosixPath(path_text)
    if (
        pure_path.is_absolute()
        or ".." in pure_path.parts
        or str(pure_path) != path_text
        or path_text == "."
    ):
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "The STE lifecycle record has an invalid repository path.",
            "Use one normalized repository-relative path.",
        )
    return path_text


def _lifecycle_git(
    arguments: list[str],
    *,
    root: pathlib.Path,
    accepted_codes: tuple[int, ...] = (0,),
) -> tuple[int, bytes]:
    executable = shutil.which("git", path=os.defpath)
    if executable is None:
        raise Ste100Error(
            "ste-lifecycle-git-untrusted",
            "A trusted system Git executable is not available.",
            "Install Git outside the repository and active Python environment.",
        )
    try:
        git_path = pathlib.Path(executable).resolve(strict=True)
        git_status = git_path.stat()
        repository_root = root.resolve(strict=True)
    except OSError as error:
        raise Ste100Error(
            "ste-lifecycle-git-untrusted",
            "The system Git executable or repository root cannot be resolved.",
            "Restore the trusted Git installation and repository state.",
        ) from error
    effective_uid = getattr(os, "geteuid", lambda: None)()
    environment_root = pathlib.Path(sys.prefix).resolve()
    if (
        not stat.S_ISREG(git_status.st_mode)
        or git_status.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        or effective_uid is None
        or git_status.st_uid not in {0, effective_uid}
        or git_path == repository_root
        or repository_root in git_path.parents
        or (
            sys.prefix != sys.base_prefix
            and (
                git_path == environment_root
                or environment_root in git_path.parents
            )
        )
    ):
        raise Ste100Error(
            "ste-lifecycle-git-untrusted",
            "The system Git executable does not have a trusted local identity.",
            "Use a regular Git executable owned by root or the current user outside "
            "the repository and active Python environment.",
        )
    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
    }
    try:
        process = subprocess.Popen(
            [
                str(git_path),
                "--no-pager",
                "--no-replace-objects",
                "--work-tree=" + str(repository_root),
                "-c",
                "core.useReplaceRefs=false",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.hooksPath=" + os.devnull,
                *arguments,
            ],
            cwd=repository_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
    except OSError as error:
        raise Ste100Error(
            "ste-lifecycle-git-failed",
            "Git could not examine the STE lifecycle state.",
            "Restore the repository Git state and return to the project owner.",
        ) from error
    assert process.stdout is not None
    assert process.stderr is not None
    timed_out = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        stdout_future = executor.submit(
            _read_bounded_stream,
            process.stdout,
            MAX_LIFECYCLE_GIT_OUTPUT_BYTES,
            process,
        )
        stderr_future = executor.submit(
            _read_bounded_stream,
            process.stderr,
            MAX_LIFECYCLE_GIT_OUTPUT_BYTES,
            process,
        )
        try:
            return_code = process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            return_code = process.wait()
        try:
            stdout = stdout_future.result()
            stderr_future.result()
        except _SubprocessOutputLimitError as error:
            if process.poll() is None:
                process.kill()
                process.wait()
            raise Ste100Error(
                "ste-lifecycle-git-output-too-large",
                "Git returned more lifecycle data than the limit.",
                "Use one bounded documentation change.",
            ) from error
    if timed_out or return_code not in accepted_codes:
        raise Ste100Error(
            "ste-lifecycle-git-failed",
            "Git did not give the necessary STE lifecycle state.",
            "Restore the repository Git state and return to the project owner.",
        )
    return return_code, stdout


def _lifecycle_revision(revision: object, *, root: pathlib.Path) -> str:
    value = _lifecycle_text(revision, "Git revision")
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise Ste100Error(
            "ste-lifecycle-revision-invalid",
            "The STE lifecycle revision is not one complete commit identifier.",
            "Use one lowercase 40-character commit identifier.",
        )
    _lifecycle_git(["cat-file", "-e", value + "^{commit}"], root=root)
    return value


def _lifecycle_head(*, root: pathlib.Path, require_clean: bool) -> str:
    _return_code, output = _lifecycle_git(["rev-parse", "HEAD"], root=root)
    try:
        head = output.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "ste-lifecycle-revision-invalid",
            "Git returned an invalid HEAD identifier.",
            "Restore the repository Git state.",
        ) from error
    _lifecycle_revision(head, root=root)
    if require_clean:
        _return_code, status = _lifecycle_git(
            ["status", "--porcelain=v1", "--untracked-files=no"],
            root=root,
        )
        if status:
            raise Ste100Error(
                "ste-lifecycle-candidate-not-clean",
                "The tracked candidate is not clean.",
                "Commit the complete candidate before the review is frozen.",
            )
    return head


def _lifecycle_tree(revision: str, *, root: pathlib.Path) -> str:
    _return_code, output = _lifecycle_git(
        ["rev-parse", revision + "^{tree}"], root=root
    )
    tree = output.decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", tree) is None:
        raise Ste100Error(
            "ste-lifecycle-revision-invalid",
            "Git returned an invalid tree identifier.",
            "Restore the repository Git state.",
        )
    return tree


def _lifecycle_changed_paths(
    baseline_revision: str,
    candidate_revision: str,
    *,
    root: pathlib.Path,
) -> list[str]:
    _return_code, output = _lifecycle_git(
        [
            "diff",
            "--name-only",
            "-z",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
            "--no-renames",
            "--diff-filter=ACMDR",
            baseline_revision,
            candidate_revision,
            "--",
        ],
        root=root,
    )
    try:
        paths = output.decode("utf-8").split("\0")
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "A changed repository path is not valid UTF-8.",
            "Use valid UTF-8 paths for canonical prose.",
        ) from error
    return sorted(_lifecycle_path(path, "changed path") for path in paths if path)


def _lifecycle_candidate_identity(
    baseline_revision: str,
    candidate_revision: str,
    *,
    root: pathlib.Path,
) -> dict[str, object]:
    changed_paths = _lifecycle_changed_paths(
        baseline_revision, candidate_revision, root=root
    )
    _return_code, binary_diff = _lifecycle_git(
        [
            "diff",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
            "--no-renames",
            baseline_revision,
            candidate_revision,
            "--",
        ],
        root=root,
    )
    return {
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "candidate_tree": _lifecycle_tree(candidate_revision, root=root),
        "changed_paths": changed_paths,
        "diff_sha256": _sha256_bytes(binary_diff),
    }


def _lifecycle_git_file(
    revision: str,
    path_text: str,
    *,
    root: pathlib.Path,
) -> tuple[bytes, str] | None:
    path_text = _lifecycle_path(path_text, "document path")
    object_name = revision + ":" + path_text
    return_code, _output = _lifecycle_git(
        ["cat-file", "-e", object_name],
        root=root,
        accepted_codes=(0, 128),
    )
    if return_code == 128:
        return None
    _return_code, payload = _lifecycle_git(
        ["cat-file", "blob", object_name], root=root
    )
    _return_code, oid_payload = _lifecycle_git(
        ["rev-parse", object_name], root=root
    )
    oid = oid_payload.decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", oid) is None:
        raise Ste100Error(
            "ste-lifecycle-blob-invalid",
            "Git returned an invalid document blob identifier.",
            "Restore the repository Git state.",
        )
    if len(payload) > MAX_REVIEW_DOCUMENT_BYTES:
        raise Ste100Error(
            "review-document-too-large",
            "A canonical document exceeds the bounded review size.",
            "Return to the project owner with the oversized document path.",
        )
    return payload, oid


def _lifecycle_blob(oid: str, *, root: pathlib.Path) -> bytes:
    if re.fullmatch(r"[0-9a-f]{40}", oid) is None:
        raise Ste100Error(
            "ste-lifecycle-blob-invalid",
            "The accepted document blob identifier is invalid.",
            "Restore the accepted review-state register.",
        )
    _return_code, payload = _lifecycle_git(["cat-file", "blob", oid], root=root)
    if len(payload) > MAX_REVIEW_DOCUMENT_BYTES:
        raise Ste100Error(
            "review-document-too-large",
            "An accepted document exceeds the bounded review size.",
            "Return to the project owner with the oversized document identity.",
        )
    return payload


def _lifecycle_blob_oid(payload: bytes) -> str:
    header = "blob {}\0".format(len(payload)).encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _empty_review_state() -> dict[str, object]:
    return {"schema_version": 1, "documents": []}


def _is_canonical_prose_path(path_text: str) -> bool:
    return path_text.endswith(".md") or path_text in CANONICAL_JSON_PROSE


def _validate_review_state(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"documents", "schema_version"}:
        raise Ste100Error(
            "ste-review-state-invalid",
            "The STE review-state register has an invalid structure.",
            "Restore the schema-1 document baseline register.",
        )
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] not in (1, 2)
        or not isinstance(value["documents"], list)
    ):
        raise Ste100Error(
            "ste-review-state-invalid",
            "The STE review-state register has an unsupported schema.",
            "Use schema version 1 or 2 and one ordered document list.",
        )
    if len(value["documents"]) > MAX_LIFECYCLE_DOCUMENTS:
        raise Ste100Error(
            "ste-review-state-invalid",
            "The STE review-state register exceeds its document limit.",
            "Return to the project owner with the register size.",
        )
    documents: list[dict[str, str]] = []
    for item in value["documents"]:
        identity_fields = {
            "accepted_blob",
            "accepted_sha256",
            "issue9_source",
            "path",
            "review_receipt",
        }
        closure_fields = {"lifecycle_status", "review_result"}
        if not isinstance(item, dict) or set(item) not in (
            identity_fields,
            identity_fields | closure_fields,
        ):
            raise Ste100Error(
                "ste-review-state-invalid",
                "One STE document baseline has an invalid structure.",
                "Use document identity fields and schema-2 closure fields.",
            )
        closure = {}
        if closure_fields <= set(item):
            if (
                value["schema_version"] != 2
                or item["lifecycle_status"] != "locked"
                or not isinstance(item["review_result"], str)
                or item["review_result"] not in STE_REVIEW_RESULTS
            ):
                raise Ste100Error(
                    "ste-review-state-invalid",
                    "One document has invalid lifecycle closure fields.",
                    "Keep the original verdict separate from locked status.",
                )
            closure = {key: item[key] for key in closure_fields}
        path_text = _lifecycle_path(item["path"], "baseline document path")
        if not _is_canonical_prose_path(path_text):
            raise Ste100Error(
                "ste-review-state-invalid",
                "The STE review-state register names a non-canonical prose path.",
                "Record only canonical Markdown or supported canonical registers.",
            )
        accepted_blob = _lifecycle_text(item["accepted_blob"], "accepted blob")
        if re.fullmatch(r"sha1:[0-9a-f]{40}", accepted_blob) is None:
            raise Ste100Error(
                "ste-review-state-invalid",
                "One accepted document blob identifier is invalid.",
                "Use the repository's sha1 Git blob identity.",
            )
        identities = {
            "accepted_sha256": _lifecycle_text(
                item["accepted_sha256"], "accepted SHA-256"
            ),
            "issue9_source": _lifecycle_text(
                item["issue9_source"], "Issue 9 source"
            ),
            "review_receipt": _lifecycle_text(
                item["review_receipt"], "review receipt"
            ),
        }
        if any(
            re.fullmatch(r"sha256:[0-9a-f]{64}", identity) is None
            for identity in identities.values()
        ):
            raise Ste100Error(
                "ste-review-state-invalid",
                "One algorithm-qualified SHA-256 identity is invalid.",
                "Restore the accepted review-state register.",
            )
        documents.append(
            {
                "accepted_blob": accepted_blob,
                **closure,
                **identities,
                "path": path_text,
            }
        )
    paths = [item["path"] for item in documents]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise Ste100Error(
            "ste-review-state-invalid",
            "The STE document baselines are not unique and ordered.",
            "Sort the entries by path and remove duplicates.",
        )
    return {"schema_version": value["schema_version"], "documents": documents}


def _review_state_at_revision(
    revision: str,
    *,
    root: pathlib.Path,
) -> tuple[dict[str, object], bytes | None]:
    item = _lifecycle_git_file(
        revision,
        STE_REVIEW_STATE.relative_to(ROOT).as_posix(),
        root=root,
    )
    if item is None:
        return _empty_review_state(), None
    payload, _oid = item
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Ste100Error(
            "ste-review-state-invalid",
            "The STE review-state register is not valid UTF-8 JSON.",
            "Restore the schema-1 document baseline register.",
        ) from error
    return _validate_review_state(value), payload


def _decode_lifecycle_document(payload: bytes, path_text: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "ste-review-document-invalid",
            "The canonical document is not valid UTF-8: {}.".format(path_text),
            "Restore valid UTF-8 canonical prose.",
        ) from error


def _line_units(text: str) -> list[dict[str, object]]:
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))
    headings = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^ {0,3}#{1,6}(?:[ \t]+|$)", line)
    ]
    boundaries = sorted({0, *headings, len(lines)})
    units: list[dict[str, object]] = []
    for first, last in zip(boundaries, boundaries[1:]):
        if first == last:
            continue
        units.append(
            {
                "end_byte": starts[last],
                "end_line": last,
                "kind": "markdown-logical-unit",
                "start_byte": starts[first],
                "start_line": first + 1,
                "text": "".join(lines[first:last]),
            }
        )
    return units


def _changed_line_intervals(
    baseline_text: str,
    candidate_text: str,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    old_lines = baseline_text.splitlines(keepends=True)
    new_lines = candidate_text.splitlines(keepends=True)
    old_intervals: list[tuple[int, int]] = []
    new_intervals: list[tuple[int, int]] = []
    for tag, old_start, old_end, new_start, new_end in difflib.SequenceMatcher(
        None, old_lines, new_lines, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            continue
        if old_start != old_end:
            old_intervals.append((old_start + 1, old_end))
        if new_start != new_end:
            new_intervals.append((new_start + 1, new_end))
    return old_intervals, new_intervals


def _unit_intersects(
    unit: dict[str, object], intervals: list[tuple[int, int]]
) -> bool:
    start = int(unit["start_line"])
    end = int(unit["end_line"])
    return any(start <= last and first <= end for first, last in intervals)


def _with_unit_identity(unit: dict[str, object], side: str) -> dict[str, object]:
    content = str(unit["text"])
    return {
        **unit,
        "sha256": _sha256_bytes(content.encode("utf-8")),
        "side": side,
    }


def _changed_markdown_units(
    baseline_text: str,
    candidate_text: str,
) -> list[dict[str, object]]:
    old_intervals, new_intervals = _changed_line_intervals(
        baseline_text, candidate_text
    )
    units = [
        _with_unit_identity(unit, "baseline")
        for unit in _line_units(baseline_text)
        if _unit_intersects(unit, old_intervals)
    ]
    units.extend(
        _with_unit_identity(unit, "candidate")
        for unit in _line_units(candidate_text)
        if _unit_intersects(unit, new_intervals)
    )
    return units


def _json_array_object_units(
    text: str,
    array_name: str,
) -> list[dict[str, object]]:
    try:
        root_value = json.loads(text)
    except json.JSONDecodeError as error:
        raise Ste100Error(
            "ste-review-document-invalid",
            "A canonical prose register is not valid JSON.",
            "Restore the canonical register before review.",
        ) from error
    if (
        not isinstance(root_value, dict)
        or not isinstance(root_value.get(array_name), list)
        or any(not isinstance(item, dict) for item in root_value[array_name])
    ):
        raise Ste100Error(
            "ste-review-document-invalid",
            "A canonical prose register has an invalid logical-unit array.",
            "Restore the canonical register schema before review.",
        )
    decoder = json.JSONDecoder()
    depth = 0
    index = 0
    array_start = None
    while index < len(text):
        if text[index] == '"':
            value, end = decoder.raw_decode(text, index)
            cursor = end
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if depth == 1 and value == array_name and cursor < len(text) and text[cursor] == ":":
                cursor += 1
                while cursor < len(text) and text[cursor].isspace():
                    cursor += 1
                if cursor < len(text) and text[cursor] == "[":
                    array_start = cursor
                    break
            index = end
            continue
        if text[index] in "{[":
            depth += 1
        elif text[index] in "}]":
            depth -= 1
        index += 1
    if array_start is None:
        raise Ste100Error(
            "ste-review-document-invalid",
            "The canonical prose register has no supported logical-unit array.",
            "Restore the canonical register schema before review.",
        )
    spans: list[tuple[int, int]] = []
    depth = 0
    in_string = False
    escaped = False
    object_start = None
    index = array_start + 1
    while index < len(text):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            if depth == 0:
                object_start = index
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0 and object_start is not None:
                spans.append((object_start, index + 1))
                object_start = None
        elif character == "]" and depth == 0:
            break
        index += 1
    values = root_value[array_name]
    if len(spans) != len(values):
        raise Ste100Error(
            "ste-review-document-invalid",
            "The canonical register logical units cannot be mapped to source bytes.",
            "Restore deterministic JSON formatting before review.",
        )
    units: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for position, ((first, last), value) in enumerate(zip(spans, values), start=1):
        identifier = value.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
            raise Ste100Error(
                "ste-review-document-invalid",
                "A canonical register logical unit has no unique identifier.",
                "Restore unique non-empty logical-unit identifiers.",
            )
        seen_ids.add(identifier)
        units.append(
            {
                "end_byte": len(text[:last].encode("utf-8")),
                "end_line": text.count("\n", 0, last) + 1,
                "identifier": identifier,
                "kind": "json-object",
                "position": position,
                "start_byte": len(text[:first].encode("utf-8")),
                "start_line": text.count("\n", 0, first) + 1,
                "text": text[first:last],
                "value": value,
            }
        )
    return units


def _changed_json_units(
    baseline_text: str,
    candidate_text: str,
    array_name: str,
) -> list[dict[str, object]]:
    old_units = _json_array_object_units(baseline_text, array_name)
    new_units = _json_array_object_units(candidate_text, array_name)
    old_by_id = {str(unit["identifier"]): unit for unit in old_units}
    new_by_id = {str(unit["identifier"]): unit for unit in new_units}
    changed_ids = {
        identifier
        for identifier in old_by_id.keys() | new_by_id.keys()
        if old_by_id.get(identifier, {}).get("value")
        != new_by_id.get(identifier, {}).get("value")
    }
    units = [
        _with_unit_identity(
            {key: value for key, value in unit.items() if key != "value"},
            "baseline",
        )
        for identifier, unit in old_by_id.items()
        if identifier in changed_ids
    ]
    units.extend(
        _with_unit_identity(
            {key: value for key, value in unit.items() if key != "value"},
            "candidate",
        )
        for identifier, unit in new_by_id.items()
        if identifier in changed_ids
    )
    return units


def _document_identity_record(
    item: tuple[bytes, str] | None,
) -> dict[str, object] | None:
    if item is None:
        return None
    payload, oid = item
    return {
        "blob": "sha1:" + oid,
        "sha256": "sha256:" + _sha256_bytes(payload),
        "size_bytes": len(payload),
    }


def _complete_document_units(
    text: str,
    path_text: str,
    side: str,
) -> list[dict[str, object]]:
    if path_text in CANONICAL_JSON_PROSE:
        return [
            _with_unit_identity(
                {key: value for key, value in unit.items() if key != "value"},
                side,
            )
            for unit in _json_array_object_units(
                text, CANONICAL_JSON_PROSE[path_text]
            )
        ]
    if not text:
        return []
    payload = text.encode("utf-8")
    return [
        {
            "end_byte": len(payload),
            "end_line": len(text.splitlines()),
            "kind": "complete-markdown-document",
            "sha256": _sha256_bytes(payload),
            "side": side,
            "start_byte": 0,
            "start_line": 1,
            "text": text,
        }
    ]


def _scope_document(
    path_text: str,
    *,
    baseline_revision: str,
    candidate_revision: str,
    state_entry: dict[str, str] | None,
    root: pathlib.Path,
    changed_legacy_units: bool = False,
) -> dict[str, object] | None:
    candidate_item = _lifecycle_git_file(candidate_revision, path_text, root=root)
    candidate_text = (
        _decode_lifecycle_document(candidate_item[0], path_text)
        if candidate_item is not None
        else ""
    )
    if state_entry is None and not changed_legacy_units:
        baseline_item = _lifecycle_git_file(baseline_revision, path_text, root=root)
        selected_item = candidate_item if candidate_item is not None else baseline_item
        if selected_item is None:
            return None
        selected_text = _decode_lifecycle_document(selected_item[0], path_text)
        selected_side = "candidate" if candidate_item is not None else "baseline"
        units = _complete_document_units(selected_text, path_text, selected_side)
        if not units:
            return None
        mode = (
            "complete-document"
            if candidate_item is not None
            else "complete-document-deletion"
        )
        baseline_identity = _document_identity_record(baseline_item)
    else:
        if state_entry is None:
            baseline_item = _lifecycle_git_file(
                baseline_revision, path_text, root=root
            )
            if baseline_item is None:
                return _scope_document(
                    path_text,
                    baseline_revision=baseline_revision,
                    candidate_revision=candidate_revision,
                    state_entry=None,
                    root=root,
                )
            baseline_payload = baseline_item[0]
        else:
            accepted_oid = state_entry["accepted_blob"].removeprefix("sha1:")
            baseline_payload = _lifecycle_blob(accepted_oid, root=root)
            if (
                "sha256:" + _sha256_bytes(baseline_payload)
                != state_entry["accepted_sha256"]
            ):
                raise Ste100Error(
                    "ste-review-state-invalid",
                    "A baseline blob does not match its SHA-256 identity.",
                    "Restore the review-state register and Git object.",
                )
            baseline_item = (baseline_payload, accepted_oid)
        baseline_text = _decode_lifecycle_document(baseline_payload, path_text)
        if path_text in CANONICAL_JSON_PROSE:
            units = _changed_json_units(
                baseline_text,
                candidate_text,
                CANONICAL_JSON_PROSE[path_text],
            )
        else:
            units = _changed_markdown_units(baseline_text, candidate_text)
        if not units:
            return None
        mode = "changed-logical-units"
        baseline_identity = _document_identity_record(baseline_item)
    if len(units) > MAX_LIFECYCLE_UNITS:
        raise Ste100Error(
            "ste-review-scope-too-large",
            "The derived Documentation Review scope exceeds its unit limit.",
            "Use one smaller documentation change.",
        )
    document = {
        "baseline_document": baseline_identity,
        "candidate_document": _document_identity_record(candidate_item),
        "mode": mode,
        "path": path_text,
        "units": units,
    }
    document["scope_sha256"] = _sha256_bytes(_canonical_json_bytes(document))
    return document


def _issue9_identity(manifest: dict[str, object]) -> dict[str, object]:
    return {
        key: manifest[key]
        for key in (
            "issue",
            "page_count",
            "publication_date",
            "sha256",
            "size_bytes",
            "standard_id",
        )
    }


def _build_review_scope(
    *,
    baseline_revision: str,
    candidate_revision: str,
    author_id: str,
    source_manifest: dict[str, object],
    root: pathlib.Path,
    schema_version: int = 2,
) -> dict[str, object]:
    baseline_revision = _lifecycle_revision(baseline_revision, root=root)
    candidate_revision = _lifecycle_revision(candidate_revision, root=root)
    _lifecycle_git(
        ["merge-base", "--is-ancestor", baseline_revision, candidate_revision],
        root=root,
    )
    candidate_state, candidate_state_payload = _review_state_at_revision(
        candidate_revision, root=root
    )
    if candidate_state_payload is None:
        raise Ste100Error(
            "ste-review-state-missing",
            "The candidate has no phase-independent STE review-state register.",
            "Add the empty schema-1 register before the candidate is frozen.",
        )
    baseline_state, baseline_state_payload = _review_state_at_revision(
        baseline_revision, root=root
    )
    if baseline_state_payload is None:
        if candidate_state != _empty_review_state():
            raise Ste100Error(
                "ste-review-state-changed",
                "The first candidate pre-populates unproved STE baselines.",
                "Use the empty register; do not review prose only to bootstrap it.",
            )
    elif (
        candidate_state_payload != baseline_state_payload
        or candidate_state != baseline_state
    ):
        raise Ste100Error(
            "ste-review-state-changed",
            "The author changed accepted STE baseline state before review.",
            "Restore the baseline register and freeze the prose candidate again.",
        )
    candidate = _lifecycle_candidate_identity(
        baseline_revision, candidate_revision, root=root
    )
    changed_paths = candidate["changed_paths"]
    assert isinstance(changed_paths, list)
    prose_paths = [
        str(path) for path in changed_paths if _is_canonical_prose_path(str(path))
    ]
    state_documents = candidate_state["documents"]
    assert isinstance(state_documents, list)
    state_by_path = {str(item["path"]): item for item in state_documents}
    documents: list[dict[str, object]] = []
    for path_text in prose_paths:
        state_entry = state_by_path.get(path_text)
        document = _scope_document(
            path_text,
            baseline_revision=baseline_revision,
            candidate_revision=candidate_revision,
            state_entry=(
                state_entry
                if schema_version == 1 and isinstance(state_entry, dict)
                else None
            ),
            root=root,
            changed_legacy_units=schema_version == 2,
        )
        if document is not None:
            documents.append(document)
    if not documents:
        raise Ste100Error(
            "ste-review-scope-empty",
            "The candidate has no materially changed canonical prose.",
            "Do not start a Documentation Review for exact machine-data changes.",
        )
    if len(documents) > MAX_LIFECYCLE_DOCUMENTS:
        raise Ste100Error(
            "ste-review-scope-too-large",
            "The Documentation Review scope exceeds its document limit.",
            "Use one smaller documentation change.",
        )
    scope: dict[str, object] = {
        "author_id": _lifecycle_text(author_id, "author identifier"),
        "candidate": candidate,
        "documents": documents,
        "issue9_source": _issue9_identity(source_manifest),
        "pre_review_state": candidate_state,
        "pre_review_state_sha256": _sha256_bytes(candidate_state_payload),
        "schema_version": schema_version,
    }
    scope["scope_sha256"] = _sha256_bytes(_canonical_json_bytes(scope))
    if len(_canonical_json_bytes(scope)) > MAX_LIFECYCLE_BYTES:
        raise Ste100Error(
            "ste-review-scope-too-large",
            "The frozen Documentation Review scope exceeds its byte limit.",
            "Use one smaller documentation change.",
        )
    return scope


def _lifecycle_tmp_path(
    path: pathlib.Path,
    subject: str,
    *,
    root: pathlib.Path,
) -> pathlib.Path:
    try:
        resolved = path.resolve(strict=True)
        tmp_root = (root / "tmp").resolve(strict=True)
    except OSError as error:
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "The {} is absent or unreadable.".format(subject),
            "Use one regular JSON file in the repository tmp directory.",
        ) from error
    if path.is_symlink() or tmp_root not in resolved.parents or not resolved.is_file():
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "The {} is outside the repository tmp directory.".format(subject),
            "Use one regular JSON file in the repository tmp directory.",
        )
    return resolved


def _read_lifecycle_json(
    path: pathlib.Path,
    subject: str,
    *,
    root: pathlib.Path,
) -> dict[str, object]:
    def reject_duplicate_members(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise Ste100Error(
                    "ste-lifecycle-record-invalid",
                    "The {} contains a duplicate JSON member.".format(subject),
                    "Restore one unambiguous lifecycle record.",
                )
            value[key] = item
        return value

    resolved = _lifecycle_tmp_path(path, subject, root=root)
    try:
        payload = resolved.read_bytes()
        if len(payload) > MAX_LIFECYCLE_BYTES:
            raise Ste100Error(
                "ste-lifecycle-record-too-large",
                "The {} exceeds its byte limit.".format(subject),
                "Use one bounded lifecycle record.",
            )
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicate_members,
        )
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as error:
        raise Ste100Error(
            "ste-lifecycle-record-invalid",
            "The {} is not readable UTF-8 JSON.".format(subject),
            "Restore the exact generated lifecycle record.",
        ) from error
    if not isinstance(value, dict):
        raise Ste100Error(
            "ste-lifecycle-record-invalid",
            "The {} is not one JSON object.".format(subject),
            "Restore the exact generated lifecycle record.",
        )
    return value


def _write_lifecycle_json(
    directory: pathlib.Path,
    stem: str,
    value: dict[str, object],
    *,
    root: pathlib.Path,
) -> tuple[pathlib.Path, str]:
    _require_output_within(directory, root / "tmp", "STE lifecycle output")
    if directory.is_symlink():
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "The STE lifecycle output directory is a symbolic link.",
            "Use the fixed repository-local tmp directory.",
        )
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    content = _canonical_json_bytes(value)
    if len(content) > MAX_LIFECYCLE_BYTES:
        raise Ste100Error(
            "ste-lifecycle-record-too-large",
            "The STE lifecycle output exceeds its byte limit.",
            "Use one bounded documentation change.",
        )
    digest = _sha256_bytes(content)
    path = directory / "{}-{}.json".format(stem, digest)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != content:
            raise Ste100Error(
                "ste-lifecycle-path-conflict",
                "A content-addressed lifecycle path contains different bytes.",
                "Inspect the local evidence and return to the project owner.",
            )
        os.chmod(path, 0o600)
        return path, digest
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
    except FileExistsError as error:
        raise Ste100Error(
            "ste-lifecycle-path-conflict",
            "Another process created the lifecycle output path.",
            "Inspect the local evidence and return to the project owner.",
        ) from error
    return path, digest


def freeze_documentation_review(
    *,
    baseline_revision: str,
    author_id: str,
    source_manifest: dict[str, object],
    root: pathlib.Path = ROOT,
) -> tuple[pathlib.Path, dict[str, object]]:
    candidate_revision = _lifecycle_head(root=root, require_clean=True)
    scope = _build_review_scope(
        baseline_revision=baseline_revision,
        candidate_revision=candidate_revision,
        author_id=author_id,
        source_manifest=source_manifest,
        root=root,
    )
    _check_review_restart(scope, root=root)
    path, _digest = _write_lifecycle_json(
        root / "tmp" / STE_REVIEW_SCOPE_DIR.name,
        "scope",
        scope,
        root=root,
    )
    return path, scope


def _validated_scope(
    path: pathlib.Path,
    *,
    source_manifest: dict[str, object],
    root: pathlib.Path,
    require_current_candidate: bool,
) -> dict[str, object]:
    scope = _read_lifecycle_json(path, "frozen review scope", root=root)
    if (
        type(scope.get("schema_version")) is not int
        or scope.get("schema_version") not in (1, 2)
        or not isinstance(scope.get("scope_sha256"), str)
    ):
        raise Ste100Error(
            "ste-review-scope-invalid",
            "The frozen Documentation Review scope has an invalid schema.",
            "Use the exact generated schema-1 or schema-2 scope.",
        )
    supplied_digest = _lifecycle_sha256(scope["scope_sha256"], "scope SHA-256")
    unhashed = {key: value for key, value in scope.items() if key != "scope_sha256"}
    if _sha256_bytes(_canonical_json_bytes(unhashed)) != supplied_digest:
        raise Ste100Error(
            "ste-review-scope-invalid",
            "The frozen Documentation Review scope identity is invalid.",
            "Use the exact generated scope without mutation.",
        )
    candidate = scope.get("candidate")
    if not isinstance(candidate, dict):
        raise Ste100Error(
            "ste-review-scope-invalid",
            "The frozen Documentation Review scope has no candidate identity.",
            "Use the exact generated scope.",
        )
    baseline_revision = _lifecycle_revision(
        candidate.get("baseline_revision"), root=root
    )
    candidate_revision = _lifecycle_revision(
        candidate.get("candidate_revision"), root=root
    )
    if (
        require_current_candidate
        and _lifecycle_head(root=root, require_clean=True) != candidate_revision
    ):
        raise Ste100Error(
            "ste-review-candidate-changed",
            "The repository is not at the frozen review candidate.",
            "Do not mutate the candidate after the Documentation Review starts.",
        )
    author_id = scope.get("author_id")
    if not isinstance(author_id, str):
        raise Ste100Error(
            "ste-review-scope-invalid",
            "The frozen review scope has no author identifier.",
            "Use the exact generated scope.",
        )
    rebuilt = _build_review_scope(
        baseline_revision=baseline_revision,
        candidate_revision=candidate_revision,
        author_id=author_id,
        source_manifest=source_manifest,
        root=root,
        schema_version=int(scope["schema_version"]),
    )
    if rebuilt != scope:
        raise Ste100Error(
            "ste-review-scope-changed",
            "The required Documentation Review scope no longer matches the frozen scope.",
            "Return to the project owner; do not start another review loop.",
        )
    return scope


def _candidate_unit_contains(
    document: dict[str, object],
    start_byte: int,
    end_byte: int,
) -> bool:
    units = document.get("units")
    return isinstance(units, list) and any(
        isinstance(unit, dict)
        and unit.get("side") == "candidate"
        and isinstance(unit.get("start_byte"), int)
        and isinstance(unit.get("end_byte"), int)
        and int(unit["start_byte"]) <= start_byte
        and end_byte <= int(unit["end_byte"])
        for unit in units
    )


def _validate_review_blockers(
    value: object,
    *,
    result: str,
    scope: dict[str, object],
) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) > MAX_LIFECYCLE_BLOCKERS:
        raise Ste100Error(
            "ste-review-blockers-invalid",
            "The Documentation Review blocker list is invalid or too large.",
            "Return one bounded complete blocker list in the same review.",
        )
    if result == "BLOCKED" and not value:
        raise Ste100Error(
            "ste-review-blockers-invalid",
            "The BLOCKED Documentation Review result has no recorded blocker.",
            "Record the complete blocker set in the same review.",
        )
    if result != "BLOCKED" and value:
        raise Ste100Error(
            "ste-review-blockers-invalid",
            "A non-BLOCKED Documentation Review result contains blockers.",
            "Use an empty blocker list for ACCEPT or APPROVED_WITH_EXACT_CORRECTIONS.",
        )
    documents = scope["documents"]
    assert isinstance(documents, list)
    frozen_units: dict[
        tuple[str, str, int, int, str], tuple[int, int]
    ] = {}
    for document_position, document in enumerate(documents):
        assert isinstance(document, dict)
        path_text = str(document["path"])
        units = document["units"]
        assert isinstance(units, list)
        for unit_position, unit in enumerate(units):
            assert isinstance(unit, dict)
            frozen_units[(
                path_text,
                str(unit["side"]),
                int(unit["start_byte"]),
                int(unit["end_byte"]),
                str(unit["sha256"]),
            )] = (
                document_position,
                unit_position,
            )
    rule_order = {
        identifier: position
        for position, identifier in enumerate(
            sorted(
                expected_rule_ids(),
                key=lambda identifier: tuple(
                    int(part) for part in identifier.split(".")
                ),
            )
        )
    }
    validated: list[dict[str, object]] = []
    previous_key: tuple[int, int, tuple[int, ...], str] | None = None
    for blocker in value:
        if not isinstance(blocker, dict) or set(blocker) != {
            "finding",
            "path",
            "rule_ids",
            "unit",
        }:
            raise Ste100Error(
                "ste-review-blockers-invalid",
                "One Documentation Review blocker has an invalid structure.",
                "Record the finding, path, formal rule identifiers, and frozen unit.",
            )
        path_text = _lifecycle_path(blocker["path"], "blocker path")
        finding = _lifecycle_text(blocker["finding"], "blocker finding")
        unit = blocker["unit"]
        if not isinstance(unit, dict) or set(unit) != {
            "end_byte",
            "sha256",
            "side",
            "start_byte",
        }:
            raise Ste100Error(
                "ste-review-blockers-invalid",
                "One Documentation Review blocker has an invalid unit identity.",
                "Use the exact frozen logical-unit identity from the review scope.",
            )
        side = unit["side"]
        start = unit["start_byte"]
        end = unit["end_byte"]
        if (
            not isinstance(side, str)
            or side not in {"baseline", "candidate"}
            or isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
        ):
            raise Ste100Error(
                "ste-review-blockers-invalid",
                "One Documentation Review blocker has an invalid unit identity.",
                "Use the exact frozen logical-unit identity from the review scope.",
            )
        digest = _lifecycle_sha256(unit["sha256"], "blocker unit SHA-256")
        frozen_position = frozen_units.get(
            (path_text, side, start, end, digest)
        )
        if frozen_position is None:
            raise Ste100Error(
                "ste-review-blocker-outside-scope",
                "One Documentation Review blocker does not identify a frozen logical unit.",
                "Return to the project owner; do not change the frozen review scope.",
            )
        rule_ids = blocker["rule_ids"]
        if (
            not isinstance(rule_ids, list)
            or not rule_ids
            or any(
                not isinstance(identifier, str) or identifier not in rule_order
                for identifier in rule_ids
            )
            or len(set(rule_ids)) != len(rule_ids)
            or rule_ids
            != sorted(rule_ids, key=lambda identifier: rule_order[identifier])
        ):
            raise Ste100Error(
                "ste-review-blockers-invalid",
                "One Documentation Review blocker has invalid formal rule identifiers.",
                "Use unique formal Issue 9 rule identifiers in numeric order.",
            )
        order_key = (
            frozen_position[0],
            frozen_position[1],
            tuple(rule_order[identifier] for identifier in rule_ids),
            finding,
        )
        if previous_key is not None and order_key <= previous_key:
            raise Ste100Error(
                "ste-review-blockers-invalid",
                "The Documentation Review blockers are duplicated or out of order.",
                "Sort unique blockers by frozen unit, formal rule identifiers, and finding.",
            )
        previous_key = order_key
        validated.append(
            {
                "finding": finding,
                "path": path_text,
                "rule_ids": list(rule_ids),
                "unit": {
                    "end_byte": end,
                    "sha256": digest,
                    "side": side,
                    "start_byte": start,
                },
            }
        )
    return validated


def _validate_review_result(
    value: object,
    *,
    scope: dict[str, object],
    root: pathlib.Path,
) -> dict[str, object]:
    required = {
        "blocker_set_complete",
        "blockers",
        "corrections",
        "full_applicability_considered",
        "independent",
        "issue9_source_sha256",
        "result",
        "reviewer_id",
        "schema_version",
        "scope_sha256",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise Ste100Error(
            "ste-review-result-invalid",
            "The Documentation Review result has an invalid structure.",
            "Return one result with the fields for its frozen scope version.",
        )
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] not in (2, 3)
    ):
        raise Ste100Error(
            "ste-review-result-invalid",
            "The Documentation Review result has an unsupported schema.",
            "Use schema version 2 for retained results or 3 for new reviews.",
        )
    if value["schema_version"] != int(scope["schema_version"]) + 1:
        raise Ste100Error(
            "ste-review-result-schema-mismatch",
            "The review result version does not match its frozen scope.",
            "Use result schema 3 with scope schema 2; retain old pairs unchanged.",
        )
    if value["scope_sha256"] != scope["scope_sha256"]:
        raise Ste100Error(
            "ste-review-result-scope-mismatch",
            "The Documentation Review result does not cover the frozen scope.",
            "Return to the project owner; do not start another review.",
        )
    source = scope.get("issue9_source")
    if (
        not isinstance(source, dict)
        or value["issue9_source_sha256"] != source.get("sha256")
    ):
        raise Ste100Error(
            "ste-review-result-source-mismatch",
            "The Documentation Review result used a different Issue 9 source identity.",
            "Return to the project owner; do not start another review.",
        )
    if value["independent"] is not True:
        raise Ste100Error(
            "ste-review-result-not-independent",
            "The Documentation Review result does not attest independence.",
            "Use one independent Documentation Reviewer.",
        )
    if value["full_applicability_considered"] is not True:
        raise Ste100Error(
            "ste-review-result-incomplete",
            "The Documentation Review did not consider full Issue 9 applicability.",
            "Return to the project owner; do not start another review.",
        )
    reviewer_id = _lifecycle_text(value["reviewer_id"], "reviewer identifier")
    if reviewer_id == scope.get("author_id"):
        raise Ste100Error(
            "ste-review-result-not-independent",
            "The author and Documentation Reviewer identifiers are equal.",
            "Use one independent Documentation Reviewer.",
        )
    result = value["result"]
    if not isinstance(result, str) or result not in STE_REVIEW_RESULTS:
        raise Ste100Error(
            "ste-review-result-invalid",
            "The Documentation Review result value is invalid.",
            "Use ACCEPT, APPROVED_WITH_EXACT_CORRECTIONS, or BLOCKED.",
        )
    if value["blocker_set_complete"] is not True:
        raise Ste100Error(
            "ste-review-blocker-set-incomplete",
            "The Documentation Review does not attest a complete blocker set.",
            "Record all blockers from the completed review in the same result.",
        )
    blockers = _validate_review_blockers(
        value["blockers"], result=str(result), scope=scope
    )
    corrections = value["corrections"]
    if not isinstance(corrections, list) or len(corrections) > MAX_LIFECYCLE_UNITS:
        raise Ste100Error(
            "ste-review-corrections-invalid",
            "The exact-correction list is invalid or too large.",
            "Return one bounded complete correction list in the same review.",
        )
    if result == "APPROVED_WITH_EXACT_CORRECTIONS" and not corrections:
        raise Ste100Error(
            "ste-review-corrections-invalid",
            "The approved result has no exact correction.",
            "Supply all exact replacements in the same Documentation Review.",
        )
    permits_corrections = result == "APPROVED_WITH_EXACT_CORRECTIONS" or (
        value["schema_version"] == 3 and result == "BLOCKED"
    )
    if not permits_corrections and corrections:
        raise Ste100Error(
            "ste-review-corrections-invalid",
            "A non-correction review result contains corrections.",
            "Use an empty list for ACCEPT and schema-2 BLOCKED results.",
        )
    documents = scope.get("documents")
    candidate = scope.get("candidate")
    if not isinstance(documents, list) or not isinstance(candidate, dict):
        raise Ste100Error(
            "ste-review-scope-invalid",
            "The frozen review scope lacks its documents or candidate.",
            "Use the exact generated scope.",
        )
    document_by_path = {
        str(document.get("path")): document
        for document in documents
        if isinstance(document, dict)
    }
    candidate_revision = _lifecycle_revision(
        candidate.get("candidate_revision"), root=root
    )
    validated: list[dict[str, object]] = []
    previous_key: tuple[str, int, int] | None = None
    previous_path = ""
    previous_end = -1
    for correction in corrections:
        if not isinstance(correction, dict) or set(correction) != {
            "end_byte",
            "path",
            "preimage",
            "preimage_sha256",
            "replacement",
            "start_byte",
        }:
            raise Ste100Error(
                "ste-review-corrections-invalid",
                "One exact correction has an invalid structure.",
                "Use path, byte range, preimage, preimage SHA-256, and replacement.",
            )
        path_text = _lifecycle_path(correction["path"], "correction path")
        document = document_by_path.get(path_text)
        start = correction["start_byte"]
        end = correction["end_byte"]
        if (
            document is None
            or isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or not _candidate_unit_contains(document, start, end)
        ):
            raise Ste100Error(
                "ste-review-corrections-outside-scope",
                "One exact correction is outside a reviewed candidate logical unit.",
                "Return to the project owner; do not widen correction prose.",
            )
        preimage = correction["preimage"]
        replacement = correction["replacement"]
        if (
            not isinstance(preimage, str)
            or not preimage
            or not isinstance(replacement, str)
            or len(preimage.encode("utf-8")) > MAX_REVIEW_DOCUMENT_BYTES
            or len(replacement.encode("utf-8")) > MAX_REVIEW_DOCUMENT_BYTES
            or preimage == replacement
        ):
            raise Ste100Error(
                "ste-review-corrections-invalid",
                "One exact correction has invalid replacement text.",
                "Supply a non-empty exact preimage and different exact replacement.",
            )
        preimage_hash = _lifecycle_sha256(
            correction["preimage_sha256"], "correction preimage SHA-256"
        )
        preimage_bytes = preimage.encode("utf-8")
        if _sha256_bytes(preimage_bytes) != preimage_hash:
            raise Ste100Error(
                "ste-review-correction-preimage-mismatch",
                "One correction preimage does not match its SHA-256.",
                "Return to the project owner with the invalid review result.",
            )
        candidate_item = _lifecycle_git_file(
            candidate_revision, path_text, root=root
        )
        if candidate_item is None or candidate_item[0][start:end] != preimage_bytes:
            raise Ste100Error(
                "ste-review-correction-preimage-mismatch",
                "One correction preimage does not match the frozen candidate bytes.",
                "Return to the project owner; do not invent replacement prose.",
            )
        key = (path_text, start, end)
        if previous_key is not None and key <= previous_key:
            raise Ste100Error(
                "ste-review-corrections-invalid",
                "The exact corrections are not in deterministic order.",
                "Sort the corrections by path and byte range.",
            )
        if path_text == previous_path and start < previous_end:
            raise Ste100Error(
                "ste-review-corrections-overlap",
                "Two exact corrections overlap.",
                "Return one non-overlapping complete correction list.",
            )
        previous_key = key
        previous_path = path_text
        previous_end = end
        validated.append(
            {
                "end_byte": end,
                "path": path_text,
                "preimage": preimage,
                "preimage_sha256": preimage_hash,
                "replacement": replacement,
                "start_byte": start,
            }
        )
    if value["schema_version"] == 3 and result == "BLOCKED" and validated:
        for blocker in blockers:
            unit = blocker["unit"]
            assert isinstance(unit, dict)
            if not any(
                correction["path"] == blocker["path"]
                and (
                    unit["side"] == "baseline"
                    or (
                        int(correction["start_byte"]) < int(unit["end_byte"])
                        and int(unit["start_byte"]) < int(correction["end_byte"])
                    )
                )
                for correction in validated
            ):
                raise Ste100Error(
                    "ste-review-corrections-incomplete",
                    "The exact adjustments omit a recorded blocker unit.",
                    "Supply the complete corrections in the one review.",
                )
    return {
        "blocker_set_complete": True,
        "blockers": blockers,
        "corrections": validated,
        "full_applicability_considered": True,
        "independent": True,
        "issue9_source_sha256": str(value["issue9_source_sha256"]),
        "result": str(result),
        "reviewer_id": reviewer_id,
        "schema_version": value["schema_version"],
        "scope_sha256": str(value["scope_sha256"]),
    }


def _review_receipt(
    result: dict[str, object],
    *,
    scope: dict[str, object],
) -> dict[str, object]:
    candidate = scope["candidate"]
    assert isinstance(candidate, dict)
    return {
        **result,
        "author_id": scope["author_id"],
        "candidate_revision": candidate["candidate_revision"],
        "candidate_tree": candidate["candidate_tree"],
    }


def _review_binding(
    scope: dict[str, object], receipt_digest: str
) -> dict[str, object]:
    candidate = scope["candidate"]
    documents = scope["documents"]
    assert isinstance(candidate, dict)
    assert isinstance(documents, list)
    return {
        "baseline_revision": candidate["baseline_revision"],
        "candidate_revision": candidate["candidate_revision"],
        "paths": sorted(str(item["path"]) for item in documents),
        "receipt_sha256": receipt_digest,
        "schema_version": 1,
        "scope_sha256": scope["scope_sha256"],
    }


def _check_review_restart(
    scope: dict[str, object], *, root: pathlib.Path
) -> None:
    """Keep a revised candidate within its existing local review cycle."""
    directory = root / "tmp" / STE_REVIEW_RESULT_DIR.name
    _require_output_within(directory, root / "tmp", "review bindings")
    if not directory.exists():
        return
    if directory.is_symlink():
        raise Ste100Error(
            "ste-lifecycle-path-invalid",
            "The review binding directory is a symbolic link.",
            "Use the repository-local review result directory.",
        )
    candidate = scope["candidate"]
    documents = scope["documents"]
    assert isinstance(candidate, dict)
    assert isinstance(documents, list)
    candidate_revision = str(candidate["candidate_revision"])
    baseline_revision = str(candidate["baseline_revision"])
    paths = {str(item["path"]) for item in documents}
    for position, path in enumerate(directory.glob("binding-*.json")):
        if position >= MAX_LIFECYCLE_BLOCKERS:
            raise Ste100Error(
                "ste-review-bindings-too-large",
                "The retained local review bindings exceed their limit.",
                "Preserve the evidence before bounded repository maintenance.",
            )
        binding = _read_lifecycle_json(path, "review binding", root=root)
        if (
            set(binding) != {
                "baseline_revision", "candidate_revision", "paths",
                "receipt_sha256", "schema_version", "scope_sha256",
            }
            or binding["schema_version"] != 1
            or not isinstance(binding["paths"], list)
            or not binding["paths"]
            or len(binding["paths"]) > MAX_LIFECYCLE_DOCUMENTS
        ):
            raise Ste100Error(
                "ste-review-binding-invalid",
                "A retained review binding has an invalid structure.",
                "Restore the original local binding without changing it.",
            )
        old_revision = _lifecycle_revision(
            binding["candidate_revision"], root=root
        )
        _lifecycle_revision(binding["baseline_revision"], root=root)
        _lifecycle_sha256(binding["receipt_sha256"], "bound receipt")
        _lifecycle_sha256(binding["scope_sha256"], "bound scope")
        bound_paths = [
            _lifecycle_path(item, "bound document path")
            for item in binding["paths"]
        ]
        if (
            path.name != "binding-{}.json".format(old_revision)
            or bound_paths != sorted(set(bound_paths))
        ):
            raise Ste100Error(
                "ste-review-binding-invalid",
                "A retained review binding has an invalid identity.",
                "Restore the original local binding without changing it.",
            )
        if old_revision == candidate_revision:
            if binding["scope_sha256"] == scope["scope_sha256"]:
                continue
            raise Ste100Error(
                "ste-review-already-recorded",
                "This candidate already has its one Documentation Review.",
                "Use the original frozen scope and review receipt.",
            )
        overlap = paths.intersection(bound_paths)
        ancestor, _output = _lifecycle_git(
            ["merge-base", "--is-ancestor", old_revision, candidate_revision],
            root=root,
            accepted_codes=(0, 1),
        )
        if not overlap or (
            ancestor != 0 and binding["baseline_revision"] != baseline_revision
        ):
            continue
        completion_path = directory / "completion-{}.json".format(old_revision)
        if completion_path.exists():
            completion = _validated_review_completion(
                completion_path, candidate_revision=old_revision,
                receipt_digest=str(binding["receipt_sha256"]), root=root,
            )
            completed_ancestor, _output = _lifecycle_git(
                ["merge-base", "--is-ancestor",
                 str(completion["final_revision"]), baseline_revision],
                root=root, accepted_codes=(0, 1),
            )
            if completed_ancestor == 0:
                continue
        raise Ste100Error(
            "ste-review-cycle-restart",
            "The revised candidate overlaps an unfinished review cycle.",
            "Complete its locked deterministic proof; do not review again.",
        )


def _bind_documentation_review(
    scope: dict[str, object], receipt_digest: str, *, root: pathlib.Path
) -> None:
    """Atomically bind one result; an identical retry is idempotent."""
    _check_review_restart(scope, root=root)
    binding = _review_binding(scope, receipt_digest)
    directory = root / "tmp" / STE_REVIEW_RESULT_DIR.name
    _require_output_within(directory, root / "tmp", "review binding output")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / "binding-{}.json".format(binding["candidate_revision"])
    payload = _canonical_json_bytes(binding)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if path.is_symlink() or path.read_bytes() != payload:
            raise Ste100Error(
                "ste-review-already-recorded",
                "This candidate already has a different Documentation Review.",
                "Keep its original result and apply at most one adjustment.",
            ) from None
        return
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)


def _validated_review_completion(
    path: pathlib.Path, *, candidate_revision: str,
    receipt_digest: str, root: pathlib.Path,
) -> dict[str, object]:
    completion = _read_lifecycle_json(path, "review completion", root=root)
    if (
        set(completion) != {
            "candidate_revision", "final_revision", "receipt_sha256",
            "schema_version",
        }
        or completion["schema_version"] != 1
        or completion["candidate_revision"] != candidate_revision
        or completion["receipt_sha256"] != receipt_digest
    ):
        raise Ste100Error(
            "ste-review-completion-invalid",
            "The local completion does not identify its original review.",
            "Restore the exact completion from final deterministic validation.",
        )
    _lifecycle_revision(completion["final_revision"], root=root)
    return completion


def _record_review_completion(
    *, candidate_revision: str, final_revision: str,
    receipt_digest: str, root: pathlib.Path,
) -> None:
    """Retain the first completed proof without rewriting later retries."""
    path = (
        root / "tmp" / STE_REVIEW_RESULT_DIR.name
        / "completion-{}.json".format(candidate_revision)
    )
    payload = _canonical_json_bytes({
        "candidate_revision": candidate_revision,
        "final_revision": final_revision,
        "receipt_sha256": receipt_digest,
        "schema_version": 1,
    })
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        _validated_review_completion(
            path, candidate_revision=candidate_revision,
            receipt_digest=receipt_digest, root=root,
        )
        return
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)


def _corrections_by_path(
    receipt: dict[str, object],
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    corrections = receipt.get("corrections", [])
    assert isinstance(corrections, list)
    for correction in corrections:
        assert isinstance(correction, dict)
        grouped.setdefault(str(correction["path"]), []).append(correction)
    return grouped


def _apply_exact_corrections(
    payload: bytes,
    corrections: list[dict[str, object]],
) -> bytes:
    result = payload
    for correction in reversed(corrections):
        start = int(correction["start_byte"])
        end = int(correction["end_byte"])
        preimage = str(correction["preimage"]).encode("utf-8")
        if result[start:end] != preimage:
            raise Ste100Error(
                "ste-review-correction-preimage-mismatch",
                "A recorded correction preimage is no longer present.",
                "Apply only the recorded correction against the frozen bytes.",
            )
        replacement = str(correction["replacement"]).encode("utf-8")
        result = result[:start] + replacement + result[end:]
    try:
        result.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Ste100Error(
            "ste-review-corrections-invalid",
            "The recorded corrections do not produce valid UTF-8.",
            "Return to the project owner with the review result.",
        ) from error
    return result


def _expected_review_state(
    *,
    scope: dict[str, object],
    receipt: dict[str, object],
    receipt_digest: str,
    root: pathlib.Path,
) -> tuple[dict[str, object], dict[str, bytes | None]]:
    pre_state = _validate_review_state(scope.get("pre_review_state"))
    pre_documents = pre_state["documents"]
    assert isinstance(pre_documents, list)
    entries = {str(item["path"]): dict(item) for item in pre_documents}
    candidate = scope["candidate"]
    source = scope["issue9_source"]
    documents = scope["documents"]
    assert isinstance(candidate, dict)
    assert isinstance(source, dict)
    assert isinstance(documents, list)
    candidate_revision = str(candidate["candidate_revision"])
    corrections = _corrections_by_path(receipt)
    expected_documents: dict[str, bytes | None] = {}
    for document in documents:
        assert isinstance(document, dict)
        path_text = str(document["path"])
        candidate_item = _lifecycle_git_file(
            candidate_revision, path_text, root=root
        )
        if candidate_item is None:
            expected_documents[path_text] = None
            entries.pop(path_text, None)
            continue
        payload = _apply_exact_corrections(
            candidate_item[0], corrections.get(path_text, [])
        )
        expected_documents[path_text] = payload
        entries[path_text] = {
            "accepted_blob": "sha1:" + _lifecycle_blob_oid(payload),
            "accepted_sha256": "sha256:" + _sha256_bytes(payload),
            "issue9_source": "sha256:" + str(source["sha256"]),
            "path": path_text,
            "review_receipt": "sha256:" + receipt_digest,
        }
        if receipt["schema_version"] == 3:
            entries[path_text].update(
                lifecycle_status="locked",
                review_result=str(receipt["result"]),
            )
    state = {
        "schema_version": (
            2 if receipt["schema_version"] == 3 else pre_state["schema_version"]
        ),
        "documents": [entries[path] for path in sorted(entries)],
    }
    return _validate_review_state(state), expected_documents


def record_documentation_review(
    *,
    scope_path: pathlib.Path,
    result_path: pathlib.Path,
    source_manifest: dict[str, object],
    root: pathlib.Path = ROOT,
) -> tuple[pathlib.Path, pathlib.Path | None, dict[str, object]]:
    scope = _validated_scope(
        scope_path,
        source_manifest=source_manifest,
        root=root,
        require_current_candidate=True,
    )
    _check_review_restart(scope, root=root)
    raw_result = _read_lifecycle_json(
        result_path, "Documentation Review result", root=root
    )
    result = _validate_review_result(raw_result, scope=scope, root=root)
    receipt = _review_receipt(result, scope=scope)
    if result["schema_version"] == 3:
        _bind_documentation_review(
            scope, _sha256_bytes(_canonical_json_bytes(receipt)), root=root
        )
    receipt_path, receipt_digest = _write_lifecycle_json(
        root / "tmp" / STE_REVIEW_RESULT_DIR.name,
        "review",
        receipt,
        root=root,
    )
    if result["result"] == "BLOCKED" and (
        result["schema_version"] == 2 or not result["corrections"]
    ):
        return receipt_path, None, receipt
    state, _expected_documents = _expected_review_state(
        scope=scope,
        receipt=receipt,
        receipt_digest=receipt_digest,
        root=root,
    )
    proposal_path, _proposal_digest = _write_lifecycle_json(
        root / "tmp" / STE_REVIEW_PROPOSAL_DIR.name,
        "state",
        state,
        root=root,
    )
    return receipt_path, proposal_path, receipt


def _validated_review_receipt(
    path: pathlib.Path,
    *,
    scope: dict[str, object],
    root: pathlib.Path,
) -> tuple[dict[str, object], str]:
    receipt = _read_lifecycle_json(
        path, "Documentation Review receipt", root=root
    )
    result_keys = {
        "blocker_set_complete",
        "blockers",
        "corrections",
        "full_applicability_considered",
        "independent",
        "issue9_source_sha256",
        "result",
        "reviewer_id",
        "schema_version",
        "scope_sha256",
    }
    if set(receipt) != result_keys | {
        "author_id",
        "candidate_revision",
        "candidate_tree",
    }:
        raise Ste100Error(
            "ste-review-receipt-invalid",
            "The Documentation Review receipt has an invalid structure.",
            "Use the exact content-addressed receipt from record-review.",
        )
    validated_result = _validate_review_result(
        {key: receipt[key] for key in result_keys}, scope=scope, root=root
    )
    expected = _review_receipt(validated_result, scope=scope)
    if receipt != expected:
        raise Ste100Error(
            "ste-review-receipt-invalid",
            "The Documentation Review receipt does not match the validated result.",
            "Use the exact content-addressed receipt from record-review.",
        )
    receipt_digest = _sha256_bytes(_canonical_json_bytes(receipt))
    if path.name != "review-{}.json".format(receipt_digest):
        raise Ste100Error(
            "ste-review-receipt-invalid",
            "The Documentation Review receipt path does not match its content.",
            "Use the exact content-addressed receipt from record-review.",
        )
    return receipt, receipt_digest


def validate_final_review_state(
    *,
    scope_path: pathlib.Path,
    receipt_path: pathlib.Path,
    source_manifest: dict[str, object],
    root: pathlib.Path = ROOT,
) -> dict[str, object]:
    final_revision = _lifecycle_head(root=root, require_clean=True)
    scope = _validated_scope(
        scope_path,
        source_manifest=source_manifest,
        root=root,
        require_current_candidate=False,
    )
    receipt, receipt_digest = _validated_review_receipt(
        receipt_path, scope=scope, root=root
    )
    _check_review_restart(scope, root=root)
    if receipt["schema_version"] == 3:
        candidate = scope["candidate"]
        assert isinstance(candidate, dict)
        binding_path = (
            root / "tmp" / STE_REVIEW_RESULT_DIR.name
            / "binding-{}.json".format(candidate["candidate_revision"])
        )
        binding = _read_lifecycle_json(
            binding_path, "review binding", root=root
        )
        if binding != _review_binding(scope, receipt_digest):
            raise Ste100Error(
                "ste-review-binding-invalid",
                "The final receipt differs from the one recorded review.",
                "Restore the original review binding and receipt.",
            )
    if receipt["result"] == "BLOCKED" and (
        receipt["schema_version"] == 2 or not receipt["corrections"]
    ):
        raise Ste100Error(
            "ste-review-blocked",
            "The Documentation Review result is BLOCKED.",
            "Resolve the recorded technical fact with its subject owner.",
        )
    expected_state, expected_documents = _expected_review_state(
        scope=scope,
        receipt=receipt,
        receipt_digest=receipt_digest,
        root=root,
    )
    candidate = scope["candidate"]
    assert isinstance(candidate, dict)
    candidate_revision = str(candidate["candidate_revision"])
    changed_after_review = _lifecycle_changed_paths(
        candidate_revision, final_revision, root=root
    )
    correction_paths = set(_corrections_by_path(receipt))
    state_path = STE_REVIEW_STATE.relative_to(ROOT).as_posix()
    unexpected = sorted(set(changed_after_review) - correction_paths - {state_path})
    if unexpected:
        raise Ste100Error(
            "ste-final-unreviewed-mutation",
            "The final candidate contains an unreviewed post-review mutation: {}.".format(
                ", ".join(unexpected)
            ),
            "Restore the locked bytes and rerun this deterministic check.",
        )
    for path_text, expected_payload in expected_documents.items():
        actual_item = _lifecycle_git_file(final_revision, path_text, root=root)
        actual_payload = actual_item[0] if actual_item is not None else None
        if actual_payload != expected_payload:
            raise Ste100Error(
                "ste-final-reviewed-bytes-mismatch",
                "The final bytes do not match the reviewed or exactly corrected bytes: {}.".format(
                    path_text
                ),
                "Restore the locked bytes and rerun this deterministic check.",
            )
    state_item = _lifecycle_git_file(final_revision, state_path, root=root)
    if state_item is None or state_item[0] != _canonical_json_bytes(expected_state):
        raise Ste100Error(
            "ste-final-state-mismatch",
            "The durable STE review state does not match the final documents.",
            "Restore the exact state proposal and rerun this check.",
        )
    if receipt["schema_version"] == 3:
        _record_review_completion(
            candidate_revision=candidate_revision,
            final_revision=final_revision,
            receipt_digest=receipt_digest,
            root=root,
        )
    return {
        "candidate_revision": candidate_revision,
        "document_count": len(expected_documents),
        "final_revision": final_revision,
        "issue9_source_sha256": receipt["issue9_source_sha256"],
        "receipt_sha256": receipt_digest,
        "result": receipt["result"],
        "scope_sha256": scope["scope_sha256"],
        "status": (
            "locked-and-deterministically-validated"
            if receipt["schema_version"] == 3
            else "reviewed-state-present-and-no-unreviewed-prose-mutation"
        ),
    }


def _emit(value: dict[str, object]) -> None:
    print(SENTINEL + json.dumps(value, ensure_ascii=False, sort_keys=True))


def _repository_document(path: pathlib.Path) -> pathlib.Path:
    resolved = path.resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise Ste100Error(
            "review-document-path-invalid",
            "The review document is outside this repository.",
            "Use one repository document or copy a review input into tmp/.",
        )
    return resolved


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "status", help="Show verified source and derived cache identity."
    )
    commands.add_parser("validate", help="Validate source, cache, and tracked inputs.")
    commands.add_parser("rebuild", help="Explicitly rebuild the ignored derived cache.")

    rule = commands.add_parser("rule", help="Look up one rule identifier.")
    rule.add_argument("identifier")
    rule.add_argument(
        "--source",
        action="store_true",
        help="Return one bounded source excerpt.",
    )

    word = commands.add_parser("word", help="Classify one word or project term.")
    word.add_argument("word")
    word.add_argument(
        "--part-of-speech",
        choices=("noun", "verb"),
        help="Check a project term against one contextual category.",
    )
    word.add_argument(
        "--source",
        action="store_true",
        help="Return one bounded dictionary excerpt.",
    )

    topic = commands.add_parser("topic", help="Look up retrieval families by topic.")
    topic.add_argument("topic")
    topic.add_argument(
        "--verbose",
        action="store_true",
        help="Return all matching families.",
    )

    review = commands.add_parser(
        "review",
        help="Show retrieval priorities for a review category.",
    )
    review.add_argument("category")

    precheck = commands.add_parser(
        "precheck",
        help="Find deterministic review candidates.",
    )
    precheck.add_argument("document", type=pathlib.Path)
    precheck.add_argument(
        "--category",
        choices=("descriptive", "procedural", "safety"),
        required=True,
    )
    precheck.add_argument(
        "--verbose",
        action="store_true",
        help="Return every deterministic finding instead of bounded lists.",
    )

    receipt = commands.add_parser("receipt", help="Generate a local review receipt.")
    receipt.add_argument("document", type=pathlib.Path)
    receipt.add_argument(
        "--category",
        choices=("descriptive", "procedural", "safety"),
        required=True,
    )
    receipt.add_argument("--rule", action="append", default=[])
    receipt.add_argument("--topic", action="append", default=[])
    receipt.add_argument("--word", action="append", default=[])
    receipt.add_argument("--exclude", action="append", default=[])
    receipt.add_argument("--unresolved", action="append", default=[])
    receipt.add_argument(
        "--baseline-revision",
        help="Bind a changed-unit review to one exact baseline commit.",
    )
    receipt.add_argument(
        "--baseline-stdin",
        action="store_true",
        help="Read the baseline form of the document from standard input.",
    )
    receipt.add_argument(
        "--full-applicability-considered",
        action="store_true",
        help="Confirm that lookup results were not treated as the complete rule set.",
    )
    freeze_review = commands.add_parser(
        "freeze-review",
        help="Freeze one candidate-bound Documentation Review scope.",
    )
    freeze_review.add_argument(
        "--baseline-revision",
        required=True,
        help="Use one exact accepted baseline commit.",
    )
    freeze_review.add_argument(
        "--author-id",
        required=True,
        help="Record the candidate author identifier for independence checks.",
    )

    record_review = commands.add_parser(
        "record-review",
        help="Validate exactly one independent Documentation Review result.",
    )
    record_review.add_argument("scope", type=pathlib.Path)
    record_review.add_argument("result", type=pathlib.Path)

    final_validate = commands.add_parser(
        "final-validate",
        help="Prove the reviewed or exactly corrected bytes and durable state.",
    )
    final_validate.add_argument("scope", type=pathlib.Path)
    final_validate.add_argument("receipt", type=pathlib.Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    try:
        if arguments.command == "rebuild":
            cache = rebuild_cache()
            _emit(
                {
                    "cache": str(CACHE_FILE.relative_to(ROOT)),
                    "controls": _controls(),
                    "dictionary_headwords": _dictionary_headword_count(cache),
                    "dictionary_lookup_forms": len(cache["dictionary"]),
                    "source": cache["source"],
                    "status": "rebuilt-and-source-bound",
                }
            )
            return 0

        cache, index, source_bytes = load_verified_cache()
        manifest = _read_json_object(SOURCE_MANIFEST, "source-manifest")
        validate_source_manifest(manifest)

        if arguments.command == "freeze-review":
            path, scope = freeze_documentation_review(
                baseline_revision=arguments.baseline_revision,
                author_id=arguments.author_id,
                source_manifest=manifest,
            )
            _emit(
                {
                    "candidate_revision": scope["candidate"]["candidate_revision"],
                    "document_count": len(scope["documents"]),
                    "scope": str(path.relative_to(ROOT)),
                    "scope_sha256": scope["scope_sha256"],
                    "status": "documentation-review-scope-frozen",
                }
            )
            return 0
        if arguments.command == "record-review":
            receipt_path, proposal_path, receipt = record_documentation_review(
                scope_path=arguments.scope,
                result_path=arguments.result,
                source_manifest=manifest,
            )
            _emit(
                {
                    "receipt": str(receipt_path.relative_to(ROOT)),
                    "result": receipt["result"],
                    "state_proposal": (
                        str(proposal_path.relative_to(ROOT))
                        if proposal_path is not None
                        else None
                    ),
                    "status": (
                        "documentation-review-blocked"
                        if receipt["result"] == "BLOCKED" and proposal_path is None
                        else "documentation-review-recorded"
                    ),
                }
            )
            return 0
        if arguments.command == "final-validate":
            result = validate_final_review_state(
                scope_path=arguments.scope,
                receipt_path=arguments.receipt,
                source_manifest=manifest,
            )
            print(
                FINAL_SENTINEL
                + json.dumps(result, ensure_ascii=False, sort_keys=True)
            )
            return 0

        def page_loader(number: int) -> str:
            return _extract_pdf_page(
                source_bytes,
                number,
                cache["extractor_identity"],
            )

        if arguments.command in {"status", "validate"}:
            _emit(
                {
                    "cache_schema_version": cache["schema_version"],
                    "controls": _controls(),
                    "dictionary_headwords": _dictionary_headword_count(cache),
                    "dictionary_lookup_forms": len(cache["dictionary"]),
                    "extractor_identity": cache["extractor_identity"],
                    "inputs": cache["inputs"],
                    "source": cache["source"],
                    "status": "verified-source-bound-cache",
                }
            )
        elif arguments.command == "rule":
            _emit(
                lookup_rule(
                    arguments.identifier,
                    cache,
                    index,
                    include_source=arguments.source,
                    page_loader=page_loader,
                )
            )
        elif arguments.command == "word":
            _emit(
                lookup_word(
                    arguments.word,
                    cache,
                    part_of_speech=arguments.part_of_speech,
                    include_source=arguments.source,
                    page_loader=page_loader,
                )
            )
        elif arguments.command == "topic":
            _emit(lookup_topic(arguments.topic, index, verbose=arguments.verbose))
        elif arguments.command == "review":
            _emit(lookup_review_category(arguments.category, index))
        elif arguments.command == "precheck":
            document = _repository_document(arguments.document)
            _emit(
                precheck_document(
                    document,
                    arguments.category,
                    cache,
                    verbose=arguments.verbose,
                )
            )
        elif arguments.command == "receipt":
            document = _repository_document(arguments.document)
            baseline_text = None
            if arguments.baseline_stdin:
                baseline_text = _decode_review_text(
                    sys.stdin.buffer.read(MAX_REVIEW_DOCUMENT_BYTES + 1)
                )
            receipt = make_review_receipt(
                document_path=document,
                category=arguments.category,
                cache=cache,
                index=index,
                full_applicability_considered=(arguments.full_applicability_considered),
                rule_ids=arguments.rule,
                words=arguments.word,
                topics=arguments.topic,
                exact_content_exclusions=arguments.exclude,
                unresolved_uncertainties=arguments.unresolved,
                baseline_text=baseline_text,
                baseline_revision=arguments.baseline_revision,
            )
            path = write_review_receipt(
                document,
                receipt,
                allowed_root=ROOT / "tmp",
            )
            _emit(
                {
                    "controls": _controls(),
                    "document_sha256": receipt["document"]["sha256"],
                    "full_applicability_considered": True,
                    "receipt": str(path.relative_to(ROOT)),
                    "status": "review-receipt-recorded",
                }
            )
        return 0
    except Ste100Error as error:
        print(
            ERROR_SENTINEL
            + json.dumps(
                {
                    "code": error.code,
                    "message": str(error),
                    "remedy": error.remedy,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
