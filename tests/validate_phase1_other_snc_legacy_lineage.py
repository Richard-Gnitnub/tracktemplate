#!/usr/bin/env python3
"""Validate the bounded other-S&C and legacy B14/B15 lineage registers."""

import ast
import collections
import copy
import hashlib
import json
import pathlib
import sys
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_dependency_manifest as manifest_validator  # noqa: E402


REGISTER_PATH = (
    ROOT
    / "reference"
    / "lineage"
    / "phase1-other-snc-legacy-lineage.json"
)
S1_CORE_REGISTER_PATH = (
    ROOT / "reference" / "lineage" / "phase1-s1-core-lineage.json"
)
EXPECTED_REGISTER_ID = "tracktemplate:phase1:other-snc-and-legacy-lineage:1"
EXPECTED_SCOPE_IDS = (
    "other-switches-crossings-output",
    "legacy-b14-b15-output",
)
EXPECTED_ENTRY_COUNTS = {
    "other-switches-crossings-output": 14,
    "legacy-b14-b15-output": 10,
}
EXPECTED_ANCHOR_COUNT = 43
EXPECTED_EVIDENCE_COUNT = 5
EXPECTED_STATUS_COUNTS = {
    "other-switches-crossings-output": {
        "reference-only": 9,
        "unknown": 5,
    },
    "legacy-b14-b15-output": {
        "reference-only": 5,
        "unknown": 5,
    },
}
EXPECTED_OWNER_ROLES = {
    "project-provenance-review",
    "project-geometry-review",
    "project-export-review",
    "project-owner",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "register_id",
    "recorded_on",
    "status",
    "status_reason",
    "intended_uses",
    "owners",
    "source_state",
    "upstream_evidence",
    "source_anchors",
    "scopes",
}
SCOPE_KEYS = {
    "scope_id",
    "status",
    "owner_roles",
    "included",
    "excluded",
    "later_gate",
    "entries",
}
ENTRY_KEYS = {
    "entry_id",
    "subject",
    "output_effect",
    "observed_values",
    "classifications",
    "source_anchor_ids",
    "upstream_evidence_ids",
    "current_project_status",
    "release_disposition",
    "evidence_needed",
    "owner_role",
}
CURRENT_STATUSES = {"reference-only", "unknown"}
TEMPLOT_CLASSIFICATIONS = {
    "templot_source_expression",
    "templot_reference_data",
    "templot_media_output",
}
REFERENCE_ONLY_TEMPLOT_CLASSIFICATIONS = {
    "templot_reference_data",
    "templot_media_output",
}
DOCUMENTATION_PATHS = (
    ROOT / "AGENTS.md",
    ROOT / "reference" / "LICENSING_BOUNDARIES.md",
    ROOT / "reference" / "PHASE1_INVENTORY.md",
    ROOT / "reference" / "PROJECT_PLAN.md",
    ROOT / "reference" / "PROVENANCE.md",
    ROOT / "reference" / "VALIDATION.md",
)


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path):
    return _sha256_bytes(path.read_bytes())


def _normalise_literal(value):
    if isinstance(value, tuple):
        return [_normalise_literal(item) for item in value]
    if isinstance(value, list):
        return [_normalise_literal(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _normalise_literal(item)
            for key, item in value.items()
        }
    return value


def _literal_hash(value):
    payload = json.dumps(
        _normalise_literal(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _top_level_assignment(tree, symbol):
    matches = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == symbol
            for target in targets
        ):
            matches.append(node.value)
    return matches[-1] if matches else None


def _active_top_level_function_hash(tree, symbol):
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    ]
    if not matches:
        return None
    return _sha256_bytes(
        ast.dump(matches[-1], include_attributes=False).encode("utf-8")
    )


def _nonempty_unique_strings(value):
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(set(value)) == len(value)
    )


def validate_register(document):
    """Return fail-closed structural and classification errors."""
    errors = []
    if not isinstance(document, dict):
        return ["register must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("register top-level fields do not match the contract")
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if document.get("register_id") != EXPECTED_REGISTER_ID:
        errors.append("register_id does not identify this bounded register")
    if document.get("recorded_on") != "2026-07-20":
        errors.append("recorded_on must preserve the accepted audit date")
    if document.get("status") != "blocked":
        errors.append("the bounded Phase 1 register must remain blocked")
    if not str(document.get("status_reason", "")).strip():
        errors.append("blocked status requires a reason")

    intended_uses = document.get("intended_uses")
    if not _nonempty_unique_strings(intended_uses):
        errors.append("intended_uses must be a non-empty unique string list")
    elif not set(intended_uses).issubset(manifest_validator.INTENDED_USES):
        errors.append("intended_uses contain unsupported values")

    owners = document.get("owners")
    if not isinstance(owners, dict) or set(owners) != EXPECTED_OWNER_ROLES:
        errors.append("the register must assign the four expected owner roles")
        owners = owners if isinstance(owners, dict) else {}
    elif any(not isinstance(value, str) or not value.strip() for value in owners.values()):
        errors.append("every owner role requires a description")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or set(source_state) != {
        "b14",
        "b15",
        "templot5_archive",
    }:
        errors.append("source_state must identify B14, B15 and the local archive")

    anchors = document.get("source_anchors")
    if not isinstance(anchors, list) or len(anchors) != EXPECTED_ANCHOR_COUNT:
        errors.append(
            "source_anchors must contain the bounded {} anchors".format(
                EXPECTED_ANCHOR_COUNT
            )
        )
        anchors = []
    anchor_ids = [
        item.get("anchor_id")
        for item in anchors
        if isinstance(item, dict)
    ]
    if len(anchor_ids) != len(anchors) or len(set(anchor_ids)) != len(anchor_ids):
        errors.append("source anchor identifiers must be present and unique")
    anchor_id_set = set(anchor_ids)
    for anchor in anchors:
        if not isinstance(anchor, dict):
            errors.append("every source anchor must be an object")
            continue
        kind = anchor.get("kind")
        if kind not in {"literal_assignment", "function_ast"}:
            errors.append("unsupported source anchor kind")
            continue
        if not str(anchor.get("symbol", "")).strip():
            errors.append("every source anchor requires a symbol")
        if kind == "literal_assignment":
            allowed = {
                "anchor_id",
                "kind",
                "symbol",
                "expected_value",
                "value_sha256",
            }
            if set(anchor) - allowed:
                errors.append("literal_assignment has unsupported fields")
            value_fields = {
                field
                for field in ("expected_value", "value_sha256")
                if field in anchor
            }
            if len(value_fields) != 1:
                errors.append(
                    "literal_assignment requires exactly one expected value form"
                )
            digest = anchor.get("value_sha256")
            if digest is not None and (
                not isinstance(digest, str) or len(digest) != 64
            ):
                errors.append("literal value_sha256 must be a SHA-256 digest")
        else:
            allowed = {
                "anchor_id",
                "kind",
                "symbol",
                "ast_sha256",
                "b15_ast_sha256",
            }
            if set(anchor) - allowed:
                errors.append("function_ast has unsupported fields")
            digest = anchor.get("ast_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append("function_ast requires a SHA-256 digest")
            b15_digests = anchor.get("b15_ast_sha256")
            if b15_digests is not None and (
                not _nonempty_unique_strings(b15_digests)
                or any(len(value) != 64 for value in b15_digests)
            ):
                errors.append("b15_ast_sha256 must contain unique SHA-256 digests")

    evidence = document.get("upstream_evidence")
    if not isinstance(evidence, list) or len(evidence) != EXPECTED_EVIDENCE_COUNT:
        errors.append(
            "upstream_evidence must contain the bounded {} records".format(
                EXPECTED_EVIDENCE_COUNT
            )
        )
        evidence = []
    evidence_ids = [
        item.get("evidence_id")
        for item in evidence
        if isinstance(item, dict)
    ]
    members = [
        item.get("archive_member")
        for item in evidence
        if isinstance(item, dict)
    ]
    if len(evidence_ids) != len(evidence) or len(set(evidence_ids)) != len(evidence_ids):
        errors.append("upstream evidence identifiers must be present and unique")
    if len(members) != len(evidence) or len(set(members)) != len(members):
        errors.append("upstream archive members must be present and unique")
    evidence_id_set = set(evidence_ids)
    permitted_roles = {
        "local special-trackwork comparison oracle",
        "local switch/timber comparison oracle",
        "local timber-behaviour comparison oracle",
        "local chair-assignment comparison oracle",
        "local cited inactive-alternate evidence",
    }
    for item in evidence:
        if not isinstance(item, dict):
            errors.append("every upstream evidence record must be an object")
            continue
        required = {
            "evidence_id",
            "archive_member",
            "sha256",
            "symbols",
            "classifications",
            "permitted_role",
        }
        allowed = required | {"active_in_exact_556b_project"}
        if not required.issubset(item) or set(item) - allowed:
            errors.append("upstream evidence fields do not match the contract")
        if not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64:
            errors.append("upstream evidence requires a SHA-256 digest")
        if not _nonempty_unique_strings(item.get("symbols")):
            errors.append("upstream evidence requires named symbols")
        classifications = item.get("classifications")
        if (
            not _nonempty_unique_strings(classifications)
            or not set(classifications).issubset(TEMPLOT_CLASSIFICATIONS)
        ):
            errors.append("upstream evidence needs Templot classifications")
        if item.get("permitted_role") not in permitted_roles:
            errors.append("upstream evidence has an unrecognised permitted role")
    inactive = [
        item
        for item in evidence
        if item.get("evidence_id") == "templot5-556b-chairs-unit-x"
    ]
    if len(inactive) != 1 or inactive[0].get("active_in_exact_556b_project") is not False:
        errors.append("chairs_unit_x must remain explicit inactive-alternate evidence")

    scopes = document.get("scopes")
    if not isinstance(scopes, list):
        errors.append("scopes must be a list")
        scopes = []
    scope_ids = [
        scope.get("scope_id")
        for scope in scopes
        if isinstance(scope, dict)
    ]
    if tuple(scope_ids) != EXPECTED_SCOPE_IDS:
        errors.append("register must contain the two remaining bounded scopes in order")

    used_anchor_ids = set()
    used_evidence_ids = set()
    entry_ids = []
    for scope in scopes:
        if not isinstance(scope, dict):
            errors.append("each scope must be an object")
            continue
        if set(scope) != SCOPE_KEYS:
            errors.append("scope fields do not match the contract")
        scope_id = scope.get("scope_id")
        if scope.get("status") != "blocked":
            errors.append("scope {} must remain blocked".format(scope_id))
        if set(scope.get("owner_roles", [])) != EXPECTED_OWNER_ROLES:
            errors.append("scope {} does not assign every owner role".format(scope_id))
        for field in ("included", "excluded"):
            if not _nonempty_unique_strings(scope.get(field)):
                errors.append(
                    "scope {} requires unique {} items".format(scope_id, field)
                )
        later_gate = scope.get("later_gate")
        if not isinstance(later_gate, str) or not later_gate.strip():
            errors.append("scope {} requires a later gate".format(scope_id))
        elif "project-cleared" not in later_gate or "manifest" not in later_gate:
            errors.append(
                "scope {} later gate must preserve status and manifest controls".format(
                    scope_id
                )
            )

        entries = scope.get("entries")
        expected_count = EXPECTED_ENTRY_COUNTS.get(scope_id)
        if not isinstance(entries, list) or len(entries) != expected_count:
            errors.append(
                "scope {} must contain {} entries".format(scope_id, expected_count)
            )
            entries = entries if isinstance(entries, list) else []
        statuses = collections.Counter()
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append("each lineage entry must be an object")
                continue
            if set(entry) != ENTRY_KEYS:
                errors.append("lineage entry fields do not match the contract")
            entry_id = entry.get("entry_id")
            entry_ids.append(entry_id)
            for field in ("subject", "output_effect", "release_disposition"):
                if not isinstance(entry.get(field), str) or not entry[field].strip():
                    errors.append("{} requires {}".format(entry_id, field))
            if not isinstance(entry.get("observed_values"), dict) or not entry["observed_values"]:
                errors.append("{} requires observed values".format(entry_id))
            if not _nonempty_unique_strings(entry.get("evidence_needed")):
                errors.append("{} requires unique unresolved evidence".format(entry_id))

            classifications = entry.get("classifications")
            if (
                not _nonempty_unique_strings(classifications)
                or not set(classifications).issubset(
                    manifest_validator.CLASSIFICATIONS
                )
            ):
                errors.append("{} has invalid classifications".format(entry_id))
                classifications = []
            status = entry.get("current_project_status")
            statuses[status] += 1
            if status not in CURRENT_STATUSES:
                errors.append(
                    "{} must remain reference-only or unknown".format(entry_id)
                )
            templot_evidenced = bool(
                TEMPLOT_CLASSIFICATIONS.intersection(classifications)
            )
            reference_only_dependency = bool(
                REFERENCE_ONLY_TEMPLOT_CLASSIFICATIONS.intersection(
                    classifications
                )
            )
            if reference_only_dependency and status != "reference-only":
                errors.append(
                    "{} uses Templot reference data/media and must be reference-only".format(
                        entry_id
                    )
                )
            if status == "reference-only" and not reference_only_dependency:
                errors.append(
                    "{} needs an output-blocking Templot classification for reference-only status".format(
                        entry_id
                    )
                )
            if status == "unknown" and reference_only_dependency:
                errors.append(
                    "{} cannot hide Templot reference data/media under unknown".format(
                        entry_id
                    )
                )

            source_ids = entry.get("source_anchor_ids")
            if not isinstance(source_ids, list) or len(set(source_ids)) != len(source_ids):
                errors.append("{} has invalid source anchors".format(entry_id))
                source_ids = []
            if set(source_ids) - anchor_id_set:
                errors.append("{} references unknown source anchors".format(entry_id))
            used_anchor_ids.update(source_ids)

            upstream_ids = entry.get("upstream_evidence_ids")
            if (
                not isinstance(upstream_ids, list)
                or len(set(upstream_ids)) != len(upstream_ids)
            ):
                errors.append("{} has invalid upstream evidence links".format(entry_id))
                upstream_ids = []
            if set(upstream_ids) - evidence_id_set:
                errors.append("{} references unknown upstream evidence".format(entry_id))
            if templot_evidenced and not upstream_ids:
                errors.append("{} requires explicit upstream evidence".format(entry_id))
            if upstream_ids and not templot_evidenced:
                errors.append(
                    "{} cannot link Templot evidence without classifying it".format(entry_id)
                )
            used_evidence_ids.update(upstream_ids)

            if entry.get("owner_role") not in owners:
                errors.append("{} has an unknown owner role".format(entry_id))

        if statuses != collections.Counter(EXPECTED_STATUS_COUNTS.get(scope_id, {})):
            errors.append(
                "scope {} current status counts have drifted".format(scope_id)
            )

    if len(set(entry_ids)) != len(entry_ids) or any(not value for value in entry_ids):
        errors.append("lineage entry identifiers must be present and unique")
    if anchor_id_set != used_anchor_ids:
        errors.append("every source anchor must be used by a lineage entry")
    if evidence_id_set != used_evidence_ids:
        errors.append("every upstream evidence record must be used by an entry")
    return errors


def validate_source_contract(document):
    source_state = document["source_state"]
    trees = {}
    for label in ("b14", "b15"):
        record = source_state[label]
        path = ROOT / record["path"]
        assert _sha256_path(path) == record["sha256"], label
        trees[label] = ast.parse(
            path.read_text(encoding="utf-8"), filename=str(path)
        )

    for anchor in document["source_anchors"]:
        symbol = anchor["symbol"]
        if anchor["kind"] == "literal_assignment":
            for label, tree in trees.items():
                value_node = _top_level_assignment(tree, symbol)
                assert value_node is not None, (label, symbol)
                value = _normalise_literal(ast.literal_eval(value_node))
                if "expected_value" in anchor:
                    assert value == anchor["expected_value"], (label, symbol)
                else:
                    assert _literal_hash(value) == anchor["value_sha256"], (
                        label,
                        symbol,
                    )
        else:
            assert (
                _active_top_level_function_hash(trees["b14"], symbol)
                == anchor["ast_sha256"]
            ), ("b14", symbol)
            expected_b15 = anchor.get("b15_ast_sha256") or [
                anchor["ast_sha256"]
            ]
            assert _active_top_level_function_hash(trees["b15"], symbol) in set(
                expected_b15
            ), ("b15", symbol)

    archive_record = source_state["templot5_archive"]
    archive_path = ROOT / archive_record["path"]
    assert archive_record["required_in_clean_checkout"] is False
    if archive_path.exists():
        assert _sha256_path(archive_path) == archive_record["sha256"]
        with zipfile.ZipFile(archive_path) as archive:
            for item in document["upstream_evidence"]:
                payload = archive.read(item["archive_member"])
                assert _sha256_bytes(payload) == item["sha256"], item["evidence_id"]


def validate_four_scope_boundary(document):
    first_register = json.loads(
        S1_CORE_REGISTER_PATH.read_text(encoding="utf-8")
    )
    first_scope_ids = tuple(
        scope["scope_id"] for scope in first_register["scopes"]
    )
    current_scope_ids = tuple(scope["scope_id"] for scope in document["scopes"])
    assert first_scope_ids + current_scope_ids == manifest_validator.AUDIT_SCOPES
    for key in ("b14", "b15", "templot5_archive"):
        assert first_register["source_state"][key] == document["source_state"][key]

    detailed_reference = "reference/lineage/phase1-s1-core-lineage.json"
    legacy_chair = next(
        entry
        for scope in document["scopes"]
        for entry in scope["entries"]
        if entry["entry_id"] == "legacy.b15-chair-display-and-retained-body"
    )
    assert legacy_chair["observed_values"]["owning_detailed_register"] == detailed_reference


def validate_current_manifest_boundary():
    current_scope_manifests = []
    for path in sorted((ROOT / "reference" / "manifests").glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("audit_scope") in EXPECTED_SCOPE_IDS:
            current_scope_manifests.append(path.name)
    assert current_scope_manifests == [], current_scope_manifests


def validate_documentation_links():
    filename = REGISTER_PATH.name
    for path in DOCUMENTATION_PATHS:
        text = path.read_text(encoding="utf-8")
        assert filename in text, path


def validate_fail_closed_contract(document):
    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["current_project_status"] = "project-cleared"
    assert any(
        "must remain reference-only or unknown" in error
        for error in validate_register(changed)
    )

    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["current_project_status"] = "unknown"
    assert any(
        "must be reference-only" in error for error in validate_register(changed)
    )

    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][1]["upstream_evidence_ids"] = [
        "templot5-556b-math-unit"
    ]
    assert any(
        "without classifying it" in error for error in validate_register(changed)
    )

    changed = copy.deepcopy(document)
    changed["scopes"][1]["later_gate"] = ""
    assert any("requires a later gate" in error for error in validate_register(changed))

    changed = copy.deepcopy(document)
    changed["scopes"][1]["entries"][0]["source_anchor_ids"] = [
        "missing:anchor"
    ]
    assert any(
        "unknown source anchors" in error for error in validate_register(changed)
    )


def validate():
    document = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    errors = validate_register(document)
    assert errors == [], errors
    validate_source_contract(document)
    validate_four_scope_boundary(document)
    validate_current_manifest_boundary()
    validate_documentation_links()
    validate_fail_closed_contract(document)
    print("Phase 1 other-S&C/legacy lineage validation passed")


if __name__ == "__main__":
    validate()
