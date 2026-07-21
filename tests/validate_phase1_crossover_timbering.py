#!/usr/bin/env python3
"""Fast fail-closed checks for the Phase 1 crossover-timbering contract."""

import ast
import copy
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-crossover-timbering.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "08591e9cd98214ed72d07aa1d8b9cbeec34bd50735ce0a624c25df5a51404fed"
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
    "legacy_defects",
    "successor_acceptance",
    "evidence",
}
FUNCTION_NAMES = {
    "default_crossover_b4_settings",
    "normalise_crossover_b4_settings",
    "_b4_stable_record",
    "_b4_resolution_signature",
    "resolve_crossover_b4_timbering",
    "_crossover_b4_result_is_current",
    "apply_crossover_b4_timbering",
    "clear_crossover_b4_timbering",
    "crossover_b4_effective_status",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _functions(tree):
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    }


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


def _normalised_dump(function):
    clone = _NormaliseRecompute().visit(copy.deepcopy(function))
    ast.fix_missing_locations(clone)
    return ast.dump(clone, include_attributes=False)


def _call_names(function):
    names = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.append((node.func.id, node.lineno))
        elif isinstance(node.func, ast.Attribute):
            names.append((node.func.attr, node.lineno))
    return names


def validate_contract(contract):
    errors = []
    if not isinstance(contract, dict) or set(contract) != TOP_LEVEL_FIELDS:
        return ["contract top-level fields are invalid"]
    expected_scalars = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:crossover-timbering:1",
        "recorded_on": "2026-07-21",
        "phase": 1,
        "status": "b14-characterised-successor-fixes-not-started",
    }
    for field, expected in expected_scalars.items():
        if contract.get(field) != expected:
            errors.append("{} is invalid".format(field))

    scope = contract.get("scope", {})
    if set(scope) != {
        "closed_by_this_contract",
        "still_open",
        "product_effect",
        "provenance_boundary",
    }:
        errors.append("scope fields are invalid")
    elif "not fixed" not in scope["still_open"]:
        errors.append("scope must keep the diagnosed defects open")

    source_state = contract.get("source_state", {})
    if set(source_state) != {"b14", "b15"}:
        errors.append("source_state must contain exactly B14 and B15")
    else:
        for label, version in (("b14", "10.2A8A7B14"), ("b15", "10.2A8A7B15")):
            record = source_state[label]
            if set(record) != {"path", "version", "sha256", "role"}:
                errors.append("{} source fields are invalid".format(label))
            elif record["version"] != version or len(record["sha256"]) != 64:
                errors.append("{} source identity is invalid".format(label))

    fixture = contract.get("fixture", {})
    if set(fixture) != {
        "path",
        "tracked",
        "reproduction_command",
        "sha256",
        "semantic_sha256",
        "object_count",
        "safety_rule",
    }:
        errors.append("fixture fields are invalid")
    elif fixture["tracked"] is not False or fixture["object_count"] != 9:
        errors.append("fixture must remain an ignored nine-object input")

    scenario = contract.get("scenario", {})
    if set(scenario) != {
        "crossover_id",
        "host_a_identity",
        "host_b_identity",
        "host_a_chainage_mm",
        "b3_calculation_change",
    }:
        errors.append("scenario fields are invalid")
    elif (
        scenario["crossover_id"] != "XO-001"
        or scenario["host_a_chainage_mm"] != 746.298
        or scenario["b3_calculation_change"] != {
            "maximum_timber_movement": 2.0
        }
    ):
        errors.append("controlled scenario changed")

    semantics = contract.get("legacy_semantics", {})
    required_semantics = {
        "status",
        "counts",
        "record_turnout_sides",
        "record_envelope_kinds",
        "record_identity_sha256",
        "stable_record_sha256",
        "default_resolution_signature",
        "display_hidden_resolution_signature",
        "calculation_change_resolution_signature",
        "display_shape",
        "lifecycle_object_counts",
    }
    if set(semantics) != required_semantics:
        errors.append("legacy semantic fields are invalid")
    else:
        counts = semantics["counts"]
        if (
            counts.get("effective_timber_count") != 86
            or counts.get("shared_timber_count") != 16
            or counts.get("unresolved_count") != 0
            or counts.get("remaining_production_conflicts") != 0
            or counts.get("remaining_production_critical_conflicts") != 0
            or counts.get("timber_resolution_complete") is not True
        ):
            errors.append("fixed semantic counts changed")
        if semantics["record_turnout_sides"] != {
            "A": 36, "B": 34, "ENVELOPE": 16
        }:
            errors.append("fixed timber-side distribution changed")
        signatures = {
            semantics["default_resolution_signature"],
            semantics["display_hidden_resolution_signature"],
            semantics["calculation_change_resolution_signature"],
        }
        if len(signatures) != 3 or any(len(value) != 64 for value in signatures):
            errors.append("legacy signature witnesses are invalid")
        shape = semantics["display_shape"]
        if set(shape) != {"edges", "faces", "solids", "bounds_mm"}:
            errors.append("display-shape fields are invalid")
        elif shape["edges"] != 1316 or shape["faces"] or shape["solids"]:
            errors.append("legacy display-shape topology changed")

    defects = contract.get("legacy_defects", {})
    expected_defects = {
        "resolved_analysis_persistence_drift",
        "display_only_over_invalidation",
        "incomplete_abort_cleanup",
    }
    if set(defects) != expected_defects:
        errors.append("the bounded legacy-defect set changed")
    else:
        retained = defects["incomplete_abort_cleanup"].get(
            "retained_object", {}
        )
        if retained != {
            "name": "CrossoverB4Timbering_XO_001",
            "type_id": "Part::Feature",
            "generated_role": "",
            "crossover_id": "",
        }:
            errors.append("abort-cleanup witness changed")

    successor = contract.get("successor_acceptance", {})
    if set(successor) != {"rules", "remaining_matrix", "migration_gate"}:
        errors.append("successor acceptance fields are invalid")
    else:
        if len(successor["rules"]) != 7 or len(successor["remaining_matrix"]) != 6:
            errors.append("successor coverage is incomplete")
        joined = " ".join(successor["rules"])
        for required in (
            "canonical signature-bound result",
            "Display-only controls",
            "calculation input",
            "exact pre-command document",
            "one complete Undo/Redo unit",
            "authoritative model output",
            "provenance",
        ):
            if required not in joined:
                errors.append("successor rules omit {!r}".format(required))

    evidence = contract.get("evidence", {})
    if set(evidence) != {
        "report",
        "fast_validator",
        "freecad_validator",
        "existing_gui_series",
    }:
        errors.append("evidence fields are invalid")
    else:
        for label, relative in evidence.items():
            if not (ROOT / relative).is_file():
                errors.append("{} evidence is missing: {}".format(label, relative))
    return errors


def validate_source(contract):
    errors = []
    parsed = {}
    definitions = {}
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        path = ROOT / source["path"]
        if _sha256(path) != source["sha256"]:
            errors.append("{} source fingerprint drifted".format(label))
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[label] = tree
        definitions[label] = _functions(tree)
        if set(definitions[label]) != FUNCTION_NAMES:
            errors.append("{} B4 function set is incomplete".format(label))
    if errors:
        return errors

    for name in FUNCTION_NAMES:
        if _normalised_dump(
            definitions["b14"][name]
        ) != _normalised_dump(definitions["b15"][name]):
            errors.append("B14/B15 B4 parity drifted: {}".format(name))

    default_return = next(
        node.value
        for node in definitions["b14"]["default_crossover_b4_settings"].body
        if isinstance(node, ast.Return)
    )
    default_items = {
        key.value: value
        for key, value in zip(default_return.keys, default_return.values)
        if isinstance(key, ast.Constant)
    }
    if (
        set(default_items) != {"schema_version", "show_b4_geometry"}
        or not isinstance(default_items["schema_version"], ast.Name)
        or default_items["schema_version"].id != "CROSSOVER_B4_SCHEMA_VERSION"
        or not isinstance(default_items["show_b4_geometry"], ast.Constant)
        or default_items["show_b4_geometry"].value is not True
    ):
        errors.append("B14 B4 default settings changed")

    signature_calls = {
        name for name, _ in _call_names(
            definitions["b14"]["_b4_resolution_signature"]
        )
    }
    if "normalise_crossover_b4_settings" not in signature_calls:
        errors.append("display-over-invalidation source witness changed")

    apply_function = definitions["b14"]["apply_crossover_b4_timbering"]
    calls = _call_names(apply_function)
    positions = {}
    for name, line in calls:
        positions.setdefault(name, []).append(line)
    for required in (
        "openTransaction",
        "addObject",
        "tag_generated_object",
        "_write_crossover_b4_and_timber_analysis_metadata",
        "commitTransaction",
        "abortTransaction",
    ):
        if required not in positions:
            errors.append("B4 mutation boundary omits {}".format(required))
    if not errors and not (
        min(positions["openTransaction"])
        < min(positions["addObject"])
        < min(positions["tag_generated_object"])
        < min(positions["commitTransaction"])
    ):
        errors.append("B4 mutation ordering changed")

    result_analysis_lines = [
        node.lineno
        for node in ast.walk(apply_function)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == "result"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "resolved_analysis"
            for target in node.targets
        )
    ]
    write_lines = positions.get(
        "_write_crossover_b4_and_timber_analysis_metadata", []
    )
    if (
        len(result_analysis_lines) != 1
        or len(write_lines) != 1
        or result_analysis_lines[0] <= write_lines[0]
    ):
        errors.append("resolved-analysis persistence-drift witness changed")
    return errors


def validate_helpers():
    sample = {
        "performance_timings_ms": {"total": 1.0},
        "nested": {"cache_reused": True, "kept": [2, 1]},
    }
    stable = recipe.stable(sample)
    return (
        stable == {"nested": {"kept": [2, 1]}}
        and recipe.digest(stable)
        == "8743d8205ad0981bd2298bba30da659ba9c4304bef19efdcb569d6cdc0382758"
    )


def validate_fail_closed_mutations(contract):
    mutations = []
    changed = copy.deepcopy(contract)
    changed["legacy_semantics"]["counts"]["effective_timber_count"] = 85
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["legacy_defects"].pop("incomplete_abort_cleanup")
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["successor_acceptance"]["rules"].pop()
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["scope"]["still_open"] = "complete"
    mutations.append(changed)
    return all(validate_contract(mutation) for mutation in mutations)


def validate():
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        raise SystemExit("Phase 1 crossover timbering contract fingerprint drifted")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors = validate_contract(contract)
    errors.extend(validate_source(contract))
    if not validate_helpers():
        errors.append("crossover-timber recipe helper contract failed")
    if not validate_fail_closed_mutations(contract):
        errors.append("crossover-timber mutation checks did not fail closed")
    if errors:
        raise SystemExit("\n".join("- {}".format(error) for error in errors))
    print("Phase 1 crossover timbering contract checks passed")


if __name__ == "__main__":
    validate()
