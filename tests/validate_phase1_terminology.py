#!/usr/bin/env python3
"""Validate the fail-closed Phase 1 railway terminology assurance contract."""

import copy
import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-terminology-assurance.json"
)
TERMINOLOGY_PATH = ROOT / "reference" / "TERMINOLOGY.md"
SOURCE_EXPECTATIONS = {
    "b14": (
        "AdvancedTurnout.FCMacro",
        "10.2A8A7B14",
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    ),
    "b15": (
        (
            "model_railway_curve_template_multitrack_v10_2a8a7b15_"
            "chair_performance_and_representation.FCMacro"
        ),
        "10.2A8A7B15",
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
    ),
}
STATE_ORDER = (
    "accepted",
    "provisional",
    "review-required",
    "frozen-legacy",
)
TERM_STATES = {
    "plain-line": "accepted",
    "switches-and-crossings": "accepted",
    "straight-and-curve": "accepted",
    "easement-and-transition": "accepted",
    "chainage-and-station": "accepted",
    "multiple-track": "accepted",
    "ordinary-track": "frozen-legacy",
    "ordinary-single-road-timbers": "review-required",
    "ordinary-chair": "review-required",
    "sleeper-and-timber": "review-required",
    "switch-points-and-turnout": "review-required",
    "crossing-vee-and-frog": "review-required",
    "s1-chair-designation": "provisional",
}
FROZEN_PATHS = (
    "reference/benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md",
    "reference/benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md",
    "reference/benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md",
    "tests/validate_phase1_ordinary_edit.py",
    "tests/validate_phase1_ordinary_export.py",
    "tests/validate_phase1_ordinary_track.py",
    "tools/freecad_bridge/ordinary_track_edit_recipe.py",
    "tools/freecad_bridge/ordinary_track_export_recipe.py",
    "tools/freecad_bridge/ordinary_track_recipe.py",
    "tools/freecad_bridge/probes/b14_ordinary_create_export_driver.py",
    "tools/freecad_bridge/probes/b14_ordinary_edit_driver.py",
    "tools/freecad_bridge/probes/b14_ordinary_export_driver.py",
    "tools/freecad_bridge/probes/snapshot_b14_ordinary_track.py",
    "tools/freecad_bridge/run-b14-ordinary-create-export",
    "tools/freecad_bridge/run-b14-ordinary-edit",
    "tools/freecad_bridge/run-b14-ordinary-export",
    "tools/freecad_bridge/run-b14-ordinary-snapshot",
    "tools/freecad_bridge/run_b14_ordinary_create_export.py",
    "tools/freecad_bridge/run_b14_ordinary_edit.py",
    "tools/freecad_bridge/run_b14_ordinary_export.py",
    "tools/freecad_bridge/run_b14_ordinary_snapshot.py",
)
FINDING_EXPECTATIONS = {
    "TERM-F01": ("ordinary-track", "ordinary parallel tracks", "frozen-legacy", 1),
    "TERM-F02": (
        "ordinary-single-road-timbers",
        "ordinary single-road timbers",
        "review-required",
        1,
    ),
    "TERM-F03": ("ordinary-chair", "ordinary chair", "review-required", 5),
}
OPEN_REVIEW_TERMS = {
    "TERM-R01": "ordinary-single-road-timbers",
    "TERM-R02": "ordinary-chair",
    "TERM-R03": "sleeper-and-timber",
    "TERM-R04": "switch-points-and-turnout",
    "TERM-R05": "crossing-vee-and-frog",
    "TERM-R06": "s1-chair-designation",
}
POLICY_MARKERS = (
    "A lexical check cannot determine whether a railway term is correct",
    "`accepted`",
    "`provisional`",
    "`review-required`",
    "`frozen-legacy`",
    "TERM-REVIEW[<term_id>]",
    "Do not resolve uncertainty by choosing the most plausible synonym",
    "tests/validate_phase1_terminology.py",
)
TEXT_SUFFIXES = {".py", ".json", ".md", ".xml", ".txt", ".FCMacro"}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _non_empty(value):
    return isinstance(value, str) and bool(value.strip())


def _term_map(document):
    terms = document.get("terms")
    if not isinstance(terms, list):
        return {}
    return {
        item.get("term_id"): item
        for item in terms
        if isinstance(item, dict) and _non_empty(item.get("term_id"))
    }


def _repository_frozen_paths():
    found = []
    for top_level in ("reference", "tests", "tools"):
        root = ROOT / top_level
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            text = relative.as_posix().lower()
            if "ordinary" in text:
                found.append(relative.as_posix())
    return tuple(sorted(found))


def _successor_files(policy):
    files = {}
    for relative_root in policy.get("successor_scan_roots") or []:
        path = ROOT / relative_root
        candidates = [path] if path.is_file() else path.rglob("*") if path.is_dir() else []
        for candidate in candidates:
            if (
                candidate.is_file()
                and candidate.suffix in TEXT_SUFFIXES
                and "__pycache__" not in candidate.parts
            ):
                files[candidate.relative_to(ROOT).as_posix()] = (
                    candidate.read_text(encoding="utf-8")
                )
    return files


def _token_lines(text, token):
    escaped = re.escape(token)
    pattern = (
        re.compile(r"\b{}\b".format(escaped), re.IGNORECASE)
        if token.isalpha()
        else re.compile(escaped, re.IGNORECASE)
    )
    result = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            result.append(line_number)
    return result


def validate_contract(
    document,
    terminology_text,
    source_texts,
    frozen_paths,
    successor_files,
    check_repository=True,
):
    errors = []
    if document.get("schema_version") != 1:
        errors.append("terminology contract schema version drifted")
    if document.get("contract_id") != "tracktemplate:phase1:terminology-assurance:1":
        errors.append("terminology contract identity drifted")
    if document.get("status") != (
        "accepted-at-phase1-closeout-open-reviews-scheduled"
    ):
        errors.append("terminology contract status drifted")
    if document.get("phase") != 1:
        errors.append("terminology contract phase drifted")

    definitions = document.get("state_definitions")
    if not isinstance(definitions, list):
        definitions = []
    states = [item.get("state") for item in definitions if isinstance(item, dict)]
    if tuple(states) != STATE_ORDER:
        errors.append("terminology assurance state order/set is invalid")
    for item in definitions:
        if not all(_non_empty(item.get(field)) for field in ("meaning", "new_use")):
            errors.append("terminology state definition is incomplete")

    terms = document.get("terms")
    if not isinstance(terms, list):
        terms = []
    term_map = _term_map(document)
    if tuple(term_map) != tuple(TERM_STATES):
        errors.append("terminology term identity/order set is invalid")
    if len(terms) != len(term_map):
        errors.append("terminology term identities are missing or duplicated")
    for term_id, expected_state in TERM_STATES.items():
        item = term_map.get(term_id, {})
        if item.get("state") != expected_state:
            errors.append("{} state drifted".format(term_id))
        for field in (
            "display",
            "bounded_meaning",
            "context_rule",
            "owner_role",
            "later_gate",
        ):
            if not _non_empty(item.get(field)):
                errors.append("{} {} is empty".format(term_id, field))
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(
            _non_empty(entry) for entry in evidence
        ):
            errors.append("{} evidence is incomplete".format(term_id))
        preferred = item.get("preferred_forms")
        if not isinstance(preferred, list):
            errors.append("{} preferred forms are invalid".format(term_id))
        elif expected_state == "accepted" and not preferred:
            errors.append("{} accepted term has no preferred form".format(term_id))

    policy = document.get("policy")
    if not isinstance(policy, dict):
        policy = {}
    if policy.get("canonical_owner") != "reference/TERMINOLOGY.md":
        errors.append("terminology canonical owner drifted")
    if policy.get("validation_owner") != "tests/validate_phase1_terminology.py":
        errors.append("terminology validation owner drifted")
    if policy.get("uncertain_use_marker") != "TERM-REVIEW[<term_id>]":
        errors.append("terminology review marker drifted")
    roots = policy.get("successor_scan_roots")
    if not isinstance(roots, list) or not roots:
        errors.append("successor terminology scan roots are missing")
    if set(policy.get("successor_text_suffixes") or []) != TEXT_SUFFIXES:
        errors.append("successor terminology suffix set drifted")
    prohibited = policy.get("prohibited_unreviewed_tokens")
    if prohibited != [
        "ordinary_track",
        "ordinary track",
        "ordinary-track",
        "CHAIR_FAMILY_ORDINARY",
        "frog",
    ]:
        errors.append("prohibited successor terminology token set drifted")

    declared_frozen = document.get("frozen_legacy_paths")
    if tuple(declared_frozen or []) != FROZEN_PATHS:
        errors.append("frozen legacy path register drifted")
    if tuple(frozen_paths) != tuple(sorted(FROZEN_PATHS)):
        errors.append("repository ordinary-named path set is not fully registered")
    if check_repository:
        for relative_path in FROZEN_PATHS:
            if not (ROOT / relative_path).is_file():
                errors.append("frozen legacy path is missing: {}".format(relative_path))

    findings = document.get("macro_findings")
    if not isinstance(findings, list):
        findings = []
    finding_map = {
        item.get("finding_id"): item
        for item in findings
        if isinstance(item, dict)
    }
    if tuple(finding_map) != tuple(FINDING_EXPECTATIONS):
        errors.append("terminology macro finding identity/order set drifted")
    for finding_id, expectation in FINDING_EXPECTATIONS.items():
        term_id, literal, state, expected_count = expectation
        finding = finding_map.get(finding_id, {})
        if (
            finding.get("term_id") != term_id
            or finding.get("literal") != literal
            or finding.get("state") != state
            or finding.get("expected_occurrences_per_source") != expected_count
            or not _non_empty(finding.get("disposition"))
        ):
            errors.append("{} definition drifted".format(finding_id))
        if term_map.get(term_id, {}).get("state") != state:
            errors.append("{} disagrees with its term state".format(finding_id))
        for source_key, source_text in source_texts.items():
            count = source_text.lower().count(literal.lower())
            if count != expected_count:
                errors.append(
                    "{} occurrence count drifted in {}".format(finding_id, source_key)
                )

    reviews = document.get("open_reviews")
    if not isinstance(reviews, list):
        reviews = []
    review_map = {
        item.get("review_id"): item
        for item in reviews
        if isinstance(item, dict)
    }
    if tuple(review_map) != tuple(OPEN_REVIEW_TERMS):
        errors.append("terminology open-review identity/order set drifted")
    for review_id, term_id in OPEN_REVIEW_TERMS.items():
        review = review_map.get(review_id, {})
        if review.get("term_id") != term_id or review.get("state") != "open":
            errors.append("{} state or term link drifted".format(review_id))
        if term_map.get(term_id, {}).get("state") not in {
            "provisional",
            "review-required",
        }:
            errors.append("{} no longer points to an unresolved term".format(review_id))
        for field in ("question", "owner_role", "closure_gate"):
            if not _non_empty(review.get(field)):
                errors.append("{} {} is empty".format(review_id, field))
        locations = review.get("locations")
        if not isinstance(locations, list) or not locations or not all(
            _non_empty(location) for location in locations
        ):
            errors.append("{} locations are incomplete".format(review_id))
    unresolved_terms = {
        term_id
        for term_id, state in TERM_STATES.items()
        if state in {"provisional", "review-required"}
    }
    if set(OPEN_REVIEW_TERMS.values()) != unresolved_terms:
        errors.append("not every unresolved terminology family has one open review")

    exceptions = policy.get("product_exceptions")
    if not isinstance(exceptions, list):
        exceptions = []
        errors.append("terminology product exception register is invalid")
    exception_keys = set()
    exception_reviews = {}
    for exception in exceptions:
        if not isinstance(exception, dict):
            errors.append("terminology product exception is invalid")
            continue
        required = ("path", "token", "line", "review_id", "reason", "retirement_gate")
        if not all(exception.get(field) for field in required):
            errors.append("terminology product exception is incomplete")
            continue
        if exception.get("review_id") not in review_map:
            errors.append("terminology product exception has no open review")
        key = (exception.get("path"), exception.get("token"), exception.get("line"))
        exception_keys.add(key)
        exception_reviews[key] = exception.get("review_id")

    observed_exception_keys = set()
    marker_pattern = re.compile(r"TERM-REVIEW\[([a-z0-9-]+)\]")
    for relative_path, text in successor_files.items():
        for token in prohibited or []:
            for line_number in _token_lines(text, token):
                key = (relative_path, token, line_number)
                observed_exception_keys.add(key)
                if key not in exception_keys:
                    errors.append(
                        "unreviewed successor term {!r} at {}:{}".format(
                            token, relative_path, line_number
                        )
                    )
        for line_number, line in enumerate(text.splitlines(), 1):
            for marker_term in marker_pattern.findall(line):
                if marker_term not in unresolved_terms:
                    errors.append(
                        "unregistered or resolved TERM-REVIEW marker at {}:{}".format(
                            relative_path, line_number
                        )
                    )
                    continue
                marker_token = "TERM-REVIEW[{}]".format(marker_term)
                key = (relative_path, marker_token, line_number)
                observed_exception_keys.add(key)
                review_id = exception_reviews.get(key)
                if review_id not in review_map:
                    errors.append(
                        "unregistered TERM-REVIEW location at {}:{}".format(
                            relative_path, line_number
                        )
                    )
                elif review_map[review_id].get("term_id") != marker_term:
                    errors.append(
                        "TERM-REVIEW marker and review disagree at {}:{}".format(
                            relative_path, line_number
                        )
                    )
    if exception_keys != observed_exception_keys:
        errors.append("terminology product exception register is stale")

    gate = document.get("phase1_gate")
    if not isinstance(gate, dict) or gate.get("status") != (
        "accepted-at-phase1-closeout"
    ):
        errors.append("terminology Phase 1 gate status drifted")
    else:
        for field in ("evidenced", "not_claimed"):
            values = gate.get(field)
            if not isinstance(values, list) or not values or not all(
                _non_empty(value) for value in values
            ):
                errors.append("terminology Phase 1 {} is incomplete".format(field))

    for marker in POLICY_MARKERS:
        if marker not in terminology_text:
            errors.append("TERMINOLOGY policy marker is missing: {}".format(marker))

    if check_repository:
        source_state = document.get("source_state") or {}
        for source_key, (relative_path, version, digest) in SOURCE_EXPECTATIONS.items():
            record = source_state.get(source_key) or {}
            path = ROOT / relative_path
            if (
                record.get("path") != relative_path
                or record.get("version_token") != version
                or record.get("sha256") != digest
            ):
                errors.append("{} source-state record drifted".format(source_key))
            if _sha256(path) != digest:
                errors.append("{} source fingerprint changed".format(source_key))
            if version not in source_texts.get(source_key, ""):
                errors.append("{} version token is missing".format(source_key))

    return errors


def _expect_invalid(document, terminology_text, source_texts, frozen_paths, files, label):
    errors = validate_contract(
        document,
        terminology_text,
        source_texts,
        frozen_paths,
        files,
        check_repository=False,
    )
    if not errors:
        raise AssertionError("mutation unexpectedly passed: {}".format(label))


def main():
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    terminology_text = TERMINOLOGY_PATH.read_text(encoding="utf-8")
    source_texts = {
        source_key: (ROOT / details[0]).read_text(encoding="utf-8")
        for source_key, details in SOURCE_EXPECTATIONS.items()
    }
    frozen_paths = _repository_frozen_paths()
    successor_files = _successor_files(document.get("policy") or {})
    errors = validate_contract(
        document,
        terminology_text,
        source_texts,
        frozen_paths,
        successor_files,
    )
    if errors:
        raise AssertionError("\n".join(errors))

    promoted = copy.deepcopy(document)
    promoted["terms"][8]["state"] = "accepted"
    _expect_invalid(
        promoted,
        terminology_text,
        source_texts,
        frozen_paths,
        successor_files,
        "unsupported ordinary-chair promotion",
    )

    missing_review = copy.deepcopy(document)
    missing_review["open_reviews"].pop()
    _expect_invalid(
        missing_review,
        terminology_text,
        source_texts,
        frozen_paths,
        successor_files,
        "missing S1 designation review",
    )

    _expect_invalid(
        document,
        terminology_text,
        source_texts,
        frozen_paths + ("tests/new_ordinary_track_test.py",),
        successor_files,
        "unregistered frozen path",
    )

    prohibited_successor = dict(successor_files)
    prohibited_successor["tracktemplate/ui.py"] = "label = 'Ordinary track'\n"
    _expect_invalid(
        document,
        terminology_text,
        source_texts,
        frozen_paths,
        prohibited_successor,
        "unreviewed successor terminology",
    )

    unknown_marker = dict(successor_files)
    unknown_marker["tracktemplate/ui.py"] = "# TERM-REVIEW[unknown-term]\n"
    _expect_invalid(
        document,
        terminology_text,
        source_texts,
        frozen_paths,
        unknown_marker,
        "unknown review marker",
    )

    unregistered_marker = dict(successor_files)
    unregistered_marker["tracktemplate/ui.py"] = (
        "# TERM-REVIEW[ordinary-chair]\n"
    )
    _expect_invalid(
        document,
        terminology_text,
        source_texts,
        frozen_paths,
        unregistered_marker,
        "unregistered review location",
    )

    print("Phase 1 terminology assurance validation passed")


if __name__ == "__main__":
    main()
