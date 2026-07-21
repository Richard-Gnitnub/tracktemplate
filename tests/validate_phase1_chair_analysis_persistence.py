#!/usr/bin/env python3
"""Fail-closed checks for the Phase 1 chair-analysis persistence contract."""

import ast
import copy
import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" /
    "phase1-chair-analysis-persistence.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "6cb871ba642c2336ad57e4befc4d5ce69fb9705631975d85f4cf0d6827105b3f"
)
TOP_LEVEL_FIELDS = {
    "schema_version",
    "contract_id",
    "recorded_on",
    "phase",
    "status",
    "scope",
    "source_state",
    "fixture",
    "scenario",
    "legacy_semantics",
    "persistence_boundary",
    "legacy_defects",
    "successor_acceptance",
    "evidence",
}
DISPLAY_ONLY_SETTINGS = {
    "markers_visible",
    "protected_markers_visible",
    "footprints_visible",
    "physical_solids_visible",
    "unresolved_markers_visible",
    "cache_enabled",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _definitions(tree, name):
    return [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]


def _classes(tree, name):
    return [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    ]


def _method(class_node, name):
    return next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _calls(node):
    return [item for item in ast.walk(node) if isinstance(item, ast.Call)]


def _subscript_key(node):
    if not isinstance(node, ast.Subscript):
        return None
    value = node.slice
    return value.value if isinstance(value, ast.Constant) else None


def _assignment_lines(function, owner_name):
    result = {}
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == owner_name
            ):
                key = _subscript_key(target)
                if isinstance(key, str):
                    result.setdefault(key, []).append(node.lineno)
    return result


class _NormaliseRecompute(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "_document_recompute"
            and len(node.args) == 1
        ):
            return ast.copy_location(
                ast.Call(
                    func=ast.Attribute(
                        value=copy.deepcopy(node.args[0]),
                        attr="recompute",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                ),
                node,
            )
        return node


def _normalised_dump(node):
    clone = _NormaliseRecompute().visit(copy.deepcopy(node))
    ast.fix_missing_locations(clone)
    return ast.dump(clone, include_attributes=False)


def validate_contract(contract):
    errors = []
    if not isinstance(contract, dict) or set(contract) != TOP_LEVEL_FIELDS:
        return ["contract top-level fields are invalid"]
    expected = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:chair-analysis-persistence:1",
        "recorded_on": "2026-07-21",
        "phase": 1,
        "status": "fixed-xo001-characterised-successor-fixes-not-started",
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            errors.append("{} is invalid".format(key))

    scope = contract.get("scope", {})
    if set(scope) != {
        "closed_by_this_contract", "still_open", "product_effect",
        "provenance_boundary",
    }:
        errors.append("scope fields are invalid")
    elif (
        "not project-cleared" not in scope["provenance_boundary"]
        or "remain open" not in scope["still_open"]
    ):
        errors.append("scope does not fail closed")

    source_state = contract.get("source_state", {})
    if set(source_state) != {"b14", "b15"}:
        errors.append("source_state must contain exactly B14 and B15")
    else:
        for label, version in (("b14", "10.2A8A7B14"), ("b15", "10.2A8A7B15")):
            source = source_state[label]
            if set(source) != {"path", "version", "sha256", "role"}:
                errors.append("{} source fields are invalid".format(label))
            elif source["version"] != version or len(source["sha256"]) != 64:
                errors.append("{} source identity is invalid".format(label))

    fixture = contract.get("fixture", {})
    if set(fixture) != {
        "path", "tracked", "reproduction_command", "sha256",
        "semantic_sha256", "object_count", "safety_rule",
    }:
        errors.append("fixture fields are invalid")
    elif fixture["tracked"] is not False or fixture["object_count"] != 9:
        errors.append("fixture must remain an ignored nine-object input")

    scenario = contract.get("scenario", {})
    if set(scenario) != {
        "crossover_id", "host_a_chainage_mm",
        "prerequisite_b4_resolution_signature",
        "starting_object_count_after_b4", "settings_source",
        "execution_boundary",
    }:
        errors.append("scenario fields are invalid")
    elif (
        scenario["crossover_id"] != "XO-001"
        or scenario["host_a_chainage_mm"] != 746.298
        or scenario["starting_object_count_after_b4"] != 20
    ):
        errors.append("controlled scenario changed")

    semantics = contract.get("legacy_semantics", {})
    required_semantics = {
        "status", "geometry_signature", "semantic_sha256",
        "position_identity_sha256", "finding_sha256", "summary_counts",
        "severity_counts", "family_counts", "display",
        "lifecycle_object_counts",
    }
    if set(semantics) != required_semantics:
        errors.append("legacy semantic fields are invalid")
    else:
        counts = semantics["summary_counts"]
        if (
            counts.get("rail_count") != 30
            or counts.get("timber_count") != 86
            or counts.get("chair_position_count") != 355
            or counts.get("mandatory_position_count") != 170
            or counts.get("deliberately_omitted_count") != 48
        ):
            errors.append("fixed semantic counts changed")
        for field in (
            "geometry_signature", "semantic_sha256",
            "position_identity_sha256", "finding_sha256",
        ):
            if len(semantics.get(field, "")) != 64:
                errors.append("{} is not a SHA-256".format(field))
        display = semantics.get("display", {})
        if display.get("marker_type_id") != "Part::Feature":
            errors.append("legacy display boundary changed")
        shape = display.get("marker_shape", {})
        if shape.get("edges") != 710 or shape.get("faces") or shape.get("solids"):
            errors.append("legacy marker topology changed")

    persistence = contract.get("persistence_boundary", {})
    if set(persistence) != {
        "cold_returned_timing_keys", "cold_persisted_timing_keys",
        "reuse_returned_timing_keys", "reuse_persisted_timing_keys",
        "reopen_result", "reuse_history_witness",
    }:
        errors.append("persistence fields are invalid")
    else:
        for prefix in ("cold", "reuse"):
            returned = set(persistence[prefix + "_returned_timing_keys"])
            stored = set(persistence[prefix + "_persisted_timing_keys"])
            if not stored < returned:
                errors.append("{} timing defect is not bounded".format(prefix))
            for required in (
                "metadata_updates", "document_recompute",
                "transaction_commit", "total",
            ):
                if required not in returned or required in stored:
                    errors.append("{} timing witness omits {}".format(
                        prefix, required
                    ))

    defects = contract.get("legacy_defects", {})
    if set(defects) != {
        "premature_timing_persistence", "unchanged_reuse_still_mutates",
        "repeated_effective_status_scan", "redundant_panel_refresh",
    }:
        errors.append("bounded legacy-defect set changed")
    elif "120.415 seconds" not in defects["redundant_panel_refresh"]:
        errors.append("accepted GUI witness is missing")

    successor = contract.get("successor_acceptance", {})
    if set(successor) != {"rules", "remaining_matrix", "migration_gate"}:
        errors.append("successor acceptance fields are invalid")
    else:
        if len(successor["rules"]) != 8 or len(successor["remaining_matrix"]) != 6:
            errors.append("successor coverage is incomplete")
        joined = " ".join(successor["rules"])
        for required in (
            "canonical signature-bound", "final complete timing",
            "before rail/timber record extraction", "dependency snapshot",
            "Refresh", "presentation controls", "model output", "provenance",
        ):
            if required not in joined:
                errors.append("successor rules omit {!r}".format(required))

    evidence = contract.get("evidence", {})
    if set(evidence) != {
        "report", "fast_validator", "freecad_validator",
        "existing_gui_acceptance", "performance_boundary_contract",
    }:
        errors.append("evidence fields are invalid")
    else:
        for label, relative in evidence.items():
            if not (ROOT / relative).is_file():
                errors.append("{} evidence is missing: {}".format(label, relative))
    return errors


def validate_source(contract):
    errors = []
    trees = {}
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        path = ROOT / source["path"]
        if _sha256(path) != source["sha256"]:
            errors.append("{} source fingerprint drifted".format(label))
            continue
        trees[label] = ast.parse(
            path.read_text(encoding="utf-8"), filename=str(path)
        )
    if errors:
        return errors

    shared_names = (
        "_chair_geometry_signature",
        "_chair_write_metadata",
        "chair_analysis_effective_status",
        "analyse_entity_chair_positions",
    )
    for name in shared_names:
        b14 = _definitions(trees["b14"], name)[0]
        b15 = _definitions(trees["b15"], name)[0]
        if _normalised_dump(b14) != _normalised_dump(b15):
            errors.append("B14/B15 inherited boundary drifted: {}".format(name))

    signature = _definitions(trees["b14"], "_chair_geometry_signature")[0]
    strings = {
        node.value for node in ast.walk(signature)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if not DISPLAY_ONLY_SETTINGS.issubset(strings):
        errors.append("calculation signature no longer excludes all display controls")

    core = _definitions(trees["b14"], "analyse_entity_chair_positions")[0]
    result_assignments = _assignment_lines(core, "result").get(
        "performance_timings_ms", []
    )
    timing_assignments = _assignment_lines(core, "timings")
    write_lines = [
        call.lineno for call in _calls(core)
        if _call_name(call) == "_chair_write_metadata"
    ]
    required_timing_lines = {
        key: timing_assignments.get(key, [])
        for key in (
            "metadata_updates", "diagnostic_display_construction",
            "document_recompute", "transaction_commit", "total",
        )
    }
    if (
        len(result_assignments) != 2
        or len(write_lines) != 1
        or any(not lines for lines in required_timing_lines.values())
    ):
        errors.append("timing-persistence source witness changed")
    elif not (
        min(result_assignments)
        < write_lines[0]
        < min(required_timing_lines["metadata_updates"])
        < min(required_timing_lines["transaction_commit"])
        < min(required_timing_lines["total"])
        < max(result_assignments)
    ):
        errors.append("premature timing-persistence ordering changed")

    call_lines = {}
    for call in _calls(core):
        call_lines.setdefault(_call_name(call), []).append(call.lineno)
    for required in (
        "chair_rail_records_for_entity", "chair_timber_records_for_entity",
        "_chair_read_cached_result", "openTransaction",
    ):
        if required not in call_lines:
            errors.append("reuse boundary omits {}".format(required))
    if not errors and not (
        min(call_lines["chair_rail_records_for_entity"])
        < min(call_lines["_chair_read_cached_result"])
        < min(call_lines["openTransaction"])
    ):
        errors.append("unchanged-reuse source ordering changed")

    status = _definitions(trees["b14"], "chair_analysis_effective_status")[0]
    status_calls = {_call_name(call) for call in _calls(status)}
    if not {
        "chair_rail_records_for_entity", "chair_timber_records_for_entity",
        "_chair_geometry_signature",
    }.issubset(status_calls):
        errors.append("effective-status rescan witness changed")

    panel = _classes(trees["b14"], "ChairAnalysisPanel")[-1]
    refresh_parent = _method(panel, "_refresh_parent")
    run_analysis = _method(panel, "run_analysis")
    refresh_parent_calls = [_call_name(call) for call in _calls(refresh_parent)]
    run_calls = [_call_name(call) for call in _calls(run_analysis)]
    if "refresh" not in refresh_parent_calls:
        errors.append("parent refresh source witness changed")
    if run_calls.count("_refresh_parent") != 1 or run_calls.count("refresh") != 1:
        errors.append("redundant panel refresh source witness changed")

    b14_aliases = {
        target.id: node.value.id
        for node in trees["b14"].body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Name)
        for target in node.targets
    }
    b15_aliases = {
        target.id: node.value.id
        for node in trees["b15"].body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Name)
        for target in node.targets
    }
    if b14_aliases.get("_A8A7B11_ANALYSE_ENTITY_CHAIR_POSITIONS") != (
        "analyse_entity_chair_positions"
    ):
        errors.append("B14 analysis-core capture alias changed")
    if b15_aliases.get("_A8A7B15_ANALYSE_CHAIRS") != (
        "analyse_entity_chair_positions"
    ):
        errors.append("B15 analysis wrapper capture alias changed")
    b15_wrapper = _definitions(
        trees["b15"], "analyse_entity_chair_positions"
    )[-1]
    if not {
        "_A8A7B15_ANALYSE_CHAIRS", "_workflow_note_cache"
    }.issubset({_call_name(call) for call in _calls(b15_wrapper)}):
        errors.append("B15 instrumentation wrapper changed")
    return errors


def main():
    errors = []
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        errors.append("contract fingerprint drifted")
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        errors.append("contract cannot be read: {}".format(error))
        contract = None
    if contract is not None:
        errors.extend(validate_contract(contract))
        errors.extend(validate_source(contract))
    if errors:
        for error in errors:
            print("ERROR: {}".format(error))
        raise SystemExit(1)
    print("Phase 1 chair analysis persistence contract passed")


if __name__ == "__main__":
    main()
