#!/usr/bin/env python3
"""Validate the bounded Phase 1 S1 and core rail/timber lineage register."""

import ast
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
    ROOT / "reference" / "lineage" / "phase1-s1-core-lineage.json"
)
S1_MANIFEST_PATH = (
    ROOT
    / "reference"
    / "manifests"
    / "s1-chair-pilot.dependency-manifest.json"
)
EXPECTED_SCOPE_IDS = (
    "s1-chair-release-path",
    "core-rail-timber-path",
)
EXPECTED_ENTRY_COUNTS = {
    "s1-chair-release-path": 7,
    "core-rail-timber-path": 9,
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
TEMPLOT_CLASSIFICATIONS = {
    "templot_source_expression",
    "templot_reference_data",
    "templot_media_output",
}


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


def _top_level_function_hashes(tree, symbol):
    return {
        _sha256_bytes(
            ast.dump(node, include_attributes=False).encode("utf-8")
        )
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    }


def validate_register(document):
    """Return fail-closed structural and classification errors."""
    errors = []
    if not isinstance(document, dict):
        return ["register must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("register top-level fields do not match the contract")
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if document.get("status") != "blocked":
        errors.append("the bounded Phase 1 register must remain blocked")
    if not str(document.get("status_reason", "")).strip():
        errors.append("blocked status requires a reason")

    intended_uses = document.get("intended_uses")
    if not isinstance(intended_uses, list) or not intended_uses:
        errors.append("intended_uses must be a non-empty list")
    elif (
        len(set(intended_uses)) != len(intended_uses)
        or not set(intended_uses).issubset(manifest_validator.INTENDED_USES)
    ):
        errors.append("intended_uses contain duplicates or unsupported values")

    owners = document.get("owners")
    if not isinstance(owners, dict) or not owners:
        errors.append("owners must be a non-empty mapping")
        owners = {}
    elif any(not str(value).strip() for value in owners.values()):
        errors.append("every owner role requires a description")

    anchors = document.get("source_anchors")
    if not isinstance(anchors, list) or not anchors:
        errors.append("source_anchors must be a non-empty list")
        anchors = []
    anchor_ids = [item.get("anchor_id") for item in anchors if isinstance(item, dict)]
    if len(anchor_ids) != len(anchors) or len(set(anchor_ids)) != len(anchor_ids):
        errors.append("source anchor identifiers must be present and unique")
    anchor_id_set = set(anchor_ids)
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        kind = anchor.get("kind")
        if kind not in ("literal_assignment", "function_ast"):
            errors.append("unsupported source anchor kind")
        if not str(anchor.get("symbol", "")).strip():
            errors.append("every source anchor requires a symbol")
        if kind == "literal_assignment" and "expected_value" not in anchor:
            errors.append("literal_assignment anchor requires expected_value")
        if kind == "function_ast":
            digest = anchor.get("ast_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append("function_ast anchor requires a SHA-256 digest")
            b15_digests = anchor.get("b15_ast_sha256")
            if b15_digests is not None and (
                not isinstance(b15_digests, list)
                or not b15_digests
                or len(set(b15_digests)) != len(b15_digests)
                or any(
                    not isinstance(value, str) or len(value) != 64
                    for value in b15_digests
                )
            ):
                errors.append("b15_ast_sha256 must contain unique SHA-256 digests")

    evidence = document.get("upstream_evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("upstream_evidence must be a non-empty list")
        evidence = []
    evidence_ids = [item.get("evidence_id") for item in evidence if isinstance(item, dict)]
    members = [item.get("archive_member") for item in evidence if isinstance(item, dict)]
    if len(evidence_ids) != len(evidence) or len(set(evidence_ids)) != len(evidence_ids):
        errors.append("upstream evidence identifiers must be present and unique")
    if len(members) != len(evidence) or len(set(members)) != len(members):
        errors.append("upstream archive members must be present and unique")
    for item in evidence:
        if not isinstance(item, dict):
            continue
        classifications = item.get("classifications")
        if (
            not isinstance(classifications, list)
            or not classifications
            or len(set(classifications)) != len(classifications)
            or not set(classifications).issubset(TEMPLOT_CLASSIFICATIONS)
        ):
            errors.append("upstream comparison evidence needs Templot classifications")
        if item.get("permitted_role") not in {
            "local comparison oracle",
            "local procedural comparison oracle",
            "local rail/component comparison oracle",
            "local assignment/timber comparison oracle",
            "local switch/timber comparison oracle",
            "local timber-behaviour comparison oracle",
        }:
            errors.append("upstream evidence has an unrecognised permitted role")

    scopes = document.get("scopes")
    if not isinstance(scopes, list):
        errors.append("scopes must be a list")
        scopes = []
    scope_ids = [scope.get("scope_id") for scope in scopes if isinstance(scope, dict)]
    if tuple(scope_ids) != EXPECTED_SCOPE_IDS:
        errors.append("register must contain the two bounded scopes in order")

    used_anchor_ids = set()
    used_evidence_ids = set()
    evidence_id_set = set(evidence_ids)
    entry_ids = []
    for scope in scopes:
        if not isinstance(scope, dict):
            errors.append("each scope must be an object")
            continue
        scope_id = scope.get("scope_id")
        if scope.get("status") != "blocked":
            errors.append("scope {} must remain blocked".format(scope_id))
        if set(scope.get("owner_roles", [])) != set(owners):
            errors.append("scope {} does not assign every owner role".format(scope_id))
        for field in ("included", "excluded"):
            if not isinstance(scope.get(field), list) or not scope[field]:
                errors.append("scope {} requires {} items".format(scope_id, field))
        if not str(scope.get("later_gate", "")).strip():
            errors.append("scope {} requires a later gate".format(scope_id))
        entries = scope.get("entries")
        expected_count = EXPECTED_ENTRY_COUNTS.get(scope_id)
        if not isinstance(entries, list) or len(entries) != expected_count:
            errors.append(
                "scope {} must contain {} entries".format(scope_id, expected_count)
            )
            entries = entries if isinstance(entries, list) else []
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append("each lineage entry must be an object")
                continue
            if set(entry) != ENTRY_KEYS:
                errors.append("lineage entry fields do not match the contract")
            entry_id = entry.get("entry_id")
            entry_ids.append(entry_id)
            classifications = entry.get("classifications")
            if (
                not isinstance(classifications, list)
                or not classifications
                or len(set(classifications)) != len(classifications)
                or not set(classifications).issubset(
                    manifest_validator.CLASSIFICATIONS
                )
            ):
                errors.append("{} has invalid classifications".format(entry_id))
                classifications = []
            status = entry.get("current_project_status")
            if status not in manifest_validator.PROJECT_STATUSES:
                errors.append("{} has an invalid project status".format(entry_id))
            if status == "project-cleared":
                errors.append("{} cannot be project-cleared in this register".format(entry_id))
            if TEMPLOT_CLASSIFICATIONS.intersection(classifications) and status != "reference-only":
                errors.append(
                    "{} uses Templot evidence and must be reference-only".format(entry_id)
                )
            source_ids = entry.get("source_anchor_ids")
            if not isinstance(source_ids, list) or len(set(source_ids)) != len(source_ids):
                errors.append("{} has invalid source anchors".format(entry_id))
                source_ids = []
            unknown_ids = set(source_ids) - anchor_id_set
            if unknown_ids:
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
            if TEMPLOT_CLASSIFICATIONS.intersection(classifications) and not upstream_ids:
                errors.append("{} requires explicit upstream evidence".format(entry_id))
            used_evidence_ids.update(upstream_ids)
            if not isinstance(entry.get("observed_values"), dict) or not entry["observed_values"]:
                errors.append("{} requires observed values".format(entry_id))
            if not str(entry.get("release_disposition", "")).strip():
                errors.append("{} requires a release disposition".format(entry_id))
            if not isinstance(entry.get("evidence_needed"), list) or not entry["evidence_needed"]:
                errors.append("{} requires unresolved evidence".format(entry_id))
            if entry.get("owner_role") not in owners:
                errors.append("{} has an unknown owner role".format(entry_id))

    if len(set(entry_ids)) != len(entry_ids) or any(not value for value in entry_ids):
        errors.append("lineage entry identifiers must be present and unique")
    if anchor_id_set != used_anchor_ids:
        errors.append("every source anchor must be used by a lineage entry")
    if evidence_id_set != used_evidence_ids:
        errors.append("every upstream evidence record must be used by a lineage entry")
    return errors


def validate_source_contract(document):
    source_state = document["source_state"]
    trees = {}
    for label in ("b14", "b15"):
        record = source_state[label]
        path = ROOT / record["path"]
        assert _sha256_path(path) == record["sha256"], label
        trees[label] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for anchor in document["source_anchors"]:
        symbol = anchor["symbol"]
        if anchor["kind"] == "literal_assignment":
            for label, tree in trees.items():
                value_node = _top_level_assignment(tree, symbol)
                assert value_node is not None, (label, symbol)
                actual = _normalise_literal(ast.literal_eval(value_node))
                assert actual == anchor["expected_value"], (label, symbol)
        else:
            expected = anchor["ast_sha256"]
            assert expected in _top_level_function_hashes(trees["b14"], symbol), symbol
            b15_expected = set(anchor.get("b15_ast_sha256") or [expected])
            assert b15_expected.issubset(
                _top_level_function_hashes(trees["b15"], symbol)
            ), symbol

    archive_record = source_state["templot5_archive"]
    archive_path = ROOT / archive_record["path"]
    assert archive_record["required_in_clean_checkout"] is False
    if archive_path.exists():
        assert _sha256_path(archive_path) == archive_record["sha256"]
        with zipfile.ZipFile(archive_path) as archive:
            for item in document["upstream_evidence"]:
                payload = archive.read(item["archive_member"])
                assert _sha256_bytes(payload) == item["sha256"], item["evidence_id"]


def validate_manifest_link(document):
    manifest = json.loads(S1_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest_validator.validate_document(manifest) == []
    assert manifest["audit_scope"] == document["scopes"][0]["scope_id"]
    assert manifest["project_status"]["status"] == "unknown"
    assert manifest["subject"]["package_license"] == "NOASSERTION"
    assert manifest["project_status"]["decision_reference"] == str(
        REGISTER_PATH.relative_to(ROOT)
    )
    assert any(
        str(REGISTER_PATH.relative_to(ROOT)) in condition
        for dependency in manifest["dependencies"]
        for condition in dependency["conditions"]
    )
    comparison = next(
        item
        for item in manifest["dependencies"]
        if item["role"] == "comparison-only"
    )
    assert comparison["output_affecting"] is False
    assert comparison["project_status"]["status"] == "reference-only"
    assert (
        comparison["source"]["evidence_sha256"]
        == document["source_state"]["templot5_archive"]["sha256"]
    )


def validate_fail_closed_contract(document):
    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["current_project_status"] = "project-cleared"
    assert any("cannot be project-cleared" in error for error in validate_register(changed))

    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["source_anchor_ids"] = ["missing:anchor"]
    assert any("unknown source anchors" in error for error in validate_register(changed))

    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["current_project_status"] = "unknown"
    assert any("must be reference-only" in error for error in validate_register(changed))

    changed = copy.deepcopy(document)
    changed["scopes"][0]["entries"][0]["evidence_needed"] = []
    assert any("unresolved evidence" in error for error in validate_register(changed))


def validate():
    document = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    errors = validate_register(document)
    assert errors == [], errors
    validate_source_contract(document)
    validate_manifest_link(document)
    validate_fail_closed_contract(document)
    print("Phase 1 S1/core lineage validation passed")


if __name__ == "__main__":
    validate()
