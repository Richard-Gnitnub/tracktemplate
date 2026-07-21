#!/usr/bin/env python3
"""Fast fail-closed checks for the Phase 1 crossover feasibility contract."""

import ast
import copy
import hashlib
import json
import math
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-crossover-feasibility.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "bfa5c2ca19888cadcdf4dcec87f8f15759b078205bb916d6b6d2b8fde8c8a5a3"
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
    "request",
    "witnesses",
    "legacy_path_characterisation",
    "successor_acceptance",
    "evidence",
}
WITNESS_FIELDS = {
    "id",
    "host_a_chainage_mm",
    "host_b_chainage_mm",
    "current_b14_preview",
    "turnout_a_mapped_minimum_radius_mm",
    "turnout_b_mapped_minimum_radius_mm",
    "connector_minimum_radius_mm",
    "complete_minimum_radius_mm",
    "complete_rule_result",
    "successor_preflight_result",
}
FUNCTION_NAMES = {
    "_build_curve_inheriting_c10_turnout",
    "_build_rea_c10_crossover_geometry",
    "_crossover_minimum_radius_value",
    "_crossover_validate_pre_solved_result",
    "solve_rea_c10_crossover_geometry",
    "turnout_mapping_metrics",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _calls(function):
    result = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            continue
        result.setdefault(name, []).append(node)
    return result


def _definitions(tree):
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    }
    panels = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "CrossoverManagerPanel"
    ]
    assert len(panels) == 1
    methods = {
        node.name: node
        for node in panels[0].body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"preview_geometry", "create_crossover"}
    }
    assert set(functions) == FUNCTION_NAMES
    assert set(methods) == {"preview_geometry", "create_crossover"}
    return functions, methods


def _literal_assignments(tree, names):
    result = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                result[target.id] = ast.literal_eval(node.value)
    return result


def _return_string_keys(function):
    keys = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
            continue
        for key in node.value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return keys


def validate_contract(contract):
    errors = []
    if not isinstance(contract, dict) or set(contract) != TOP_LEVEL_FIELDS:
        return ["contract top-level fields are invalid"]
    expected_scalars = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:crossover-feasibility:1",
        "recorded_on": "2026-07-21",
        "phase": 1,
        "status": "b14-mismatch-characterised-successor-alignment-not-started",
    }
    for field, expected in expected_scalars.items():
        if contract.get(field) != expected:
            errors.append("{} is invalid".format(field))

    scope = contract.get("scope", {})
    if set(scope) != {
        "closed_by_this_contract",
        "still_open",
        "product_effect",
        "legacy_defect_rule",
    }:
        errors.append("scope fields are invalid")
    elif "not implemented" not in scope["still_open"]:
        errors.append("scope must keep successor implementation open")

    source_state = contract.get("source_state", {})
    if set(source_state) != {"b14", "b15"}:
        errors.append("source_state must declare exactly B14 and B15")
    else:
        for label, expected_version in (("b14", "10.2A8A7B14"), ("b15", "10.2A8A7B15")):
            record = source_state[label]
            if set(record) != {"path", "version", "sha256", "role"}:
                errors.append("{} source fields are invalid".format(label))
                continue
            if record["version"] != expected_version:
                errors.append("{} version is invalid".format(label))
            try:
                int(record["sha256"], 16)
            except (TypeError, ValueError):
                errors.append("{} source hash is invalid".format(label))

    fixture = contract.get("fixture", {})
    required_fixture_fields = {
        "path",
        "tracked",
        "reproduction_command",
        "sha256",
        "semantic_sha256",
        "object_count",
        "host_a_identity",
        "host_b_identity",
        "safety_rule",
    }
    if set(fixture) != required_fixture_fields:
        errors.append("fixture fields are invalid")
    else:
        if fixture["tracked"] is not False or fixture["object_count"] != 9:
            errors.append("fixture must remain an ignored nine-object source")
        if fixture["reproduction_command"] != "tools/freecad_bridge/build-b14-base":
            errors.append("fixture reproduction command is invalid")
        if fixture["host_a_identity"].get("track_number") != 1:
            errors.append("Host A identity is invalid")
        if fixture["host_b_identity"].get("track_number") != 2:
            errors.append("Host B identity is invalid")

    request = contract.get("request", {})
    expected_request = {
        "arrangement": "Facing crossover",
        "handing": "Automatic handing",
        "track_gauge_mm": 16.5,
        "flangeway_mm": 1.0,
        "minimum_radius_mm": 600.0,
        "comparison_tolerance_mm": 0.000001,
        "complete_rule": "minimum(turnout_a_mapped_road, turnout_b_mapped_road, connector) >= requested minimum radius",
    }
    if request != expected_request:
        errors.append("request contract is invalid")

    witnesses = contract.get("witnesses")
    if not isinstance(witnesses, list) or len(witnesses) != 2:
        errors.append("exactly two witnesses are required")
    else:
        by_id = {}
        for witness in witnesses:
            if not isinstance(witness, dict) or set(witness) != WITNESS_FIELDS:
                errors.append("witness fields are invalid")
                continue
            by_id[witness["id"]] = witness
            components = [
                witness["turnout_a_mapped_minimum_radius_mm"],
                witness["turnout_b_mapped_minimum_radius_mm"],
                witness["connector_minimum_radius_mm"],
            ]
            if not all(math.isfinite(float(value)) and float(value) > 0.0 for value in components):
                errors.append("witness component radii must be finite and positive")
                continue
            if not math.isclose(
                min(components),
                witness["complete_minimum_radius_mm"],
                rel_tol=0.0,
                abs_tol=request.get("comparison_tolerance_mm", 0.0),
            ):
                errors.append("witness complete minimum does not equal its limiting component")
            expected_result = (
                "accept"
                if min(components) >= request.get("minimum_radius_mm", math.inf) - 1.0e-7
                else "reject"
            )
            if witness["complete_rule_result"] != expected_result:
                errors.append("witness complete-rule result is invalid")
        if set(by_id) != {
            "lower-preview-pass-complete-fail",
            "documented-valid-placement",
        }:
            errors.append("witness identities are invalid")
        else:
            invalid = by_id["lower-preview-pass-complete-fail"]
            valid = by_id["documented-valid-placement"]
            if invalid["host_a_chainage_mm"] >= valid["host_a_chainage_mm"]:
                errors.append("the defect witness must be below the documented placement")
            if invalid["current_b14_preview"] != "accepted" or invalid["complete_rule_result"] != "reject":
                errors.append("the legacy preview/complete mismatch was weakened")
            if valid["current_b14_preview"] != "accepted" or valid["complete_rule_result"] != "accept":
                errors.append("the documented valid witness was weakened")
            if "before-part-construction-or-document-mutation" not in invalid["successor_preflight_result"]:
                errors.append("the successor fail-closed boundary was weakened")

    legacy = contract.get("legacy_path_characterisation", {})
    if set(legacy) != {"preview", "commit", "consequence", "available_pure_boundary"}:
        errors.append("legacy characterisation fields are invalid")
    successor = contract.get("successor_acceptance", {})
    if set(successor) != {"shared_result", "rules", "migration_gate"}:
        errors.append("successor acceptance fields are invalid")
    else:
        if len(successor["shared_result"]) != 8 or len(successor["rules"]) != 6:
            errors.append("successor acceptance coverage is incomplete")
        joined = " ".join(successor["rules"])
        for required in (
            "one shared analytical preflight",
            "500.000 mm",
            "746.298 mm",
            "limiting component",
            "create, edit and turnout-extension",
        ):
            if required not in joined:
                errors.append("successor rules omit {!r}".format(required))

    evidence = contract.get("evidence", {})
    if set(evidence) != {
        "report",
        "fast_validator",
        "freecad_validator",
        "existing_valid_commit_series",
    }:
        errors.append("evidence fields are invalid")
    else:
        for field, path in evidence.items():
            if not (ROOT / path).is_file():
                errors.append("{} evidence is missing: {}".format(field, path))
    return errors


def validate_source(contract):
    errors = []
    parsed = {}
    definitions = {}
    for label in ("b14", "b15"):
        record = contract["source_state"][label]
        path = ROOT / record["path"]
        if _sha256(path) != record["sha256"]:
            errors.append("{} source fingerprint drifted".format(label))
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[label] = tree
        definitions[label] = _definitions(tree)
    if errors:
        return errors

    b14_functions, b14_methods = definitions["b14"]
    b15_functions, b15_methods = definitions["b15"]
    for name in FUNCTION_NAMES:
        if ast.dump(b14_functions[name], include_attributes=False) != ast.dump(
            b15_functions[name], include_attributes=False
        ):
            errors.append("B14/B15 crossover function parity drifted: {}".format(name))
    for name in ("preview_geometry", "create_crossover"):
        if ast.dump(b14_methods[name], include_attributes=False) != ast.dump(
            b15_methods[name], include_attributes=False
        ):
            errors.append("B14/B15 crossover panel parity drifted: {}".format(name))

    constants = _literal_assignments(parsed["b14"], {
        "CROSSOVER_ARRANGEMENT_FACING",
        "CROSSOVER_HAND_AUTO",
        "CROSSOVER_DEFAULT_MINIMUM_RADIUS",
        "TURNOUT_DEFAULT_GAUGE",
        "TURNOUT_DEFAULT_FLANGEWAY",
    })
    request = contract["request"]
    expected_constants = {
        "CROSSOVER_ARRANGEMENT_FACING": request["arrangement"],
        "CROSSOVER_HAND_AUTO": request["handing"],
        "CROSSOVER_DEFAULT_MINIMUM_RADIUS": request["minimum_radius_mm"],
        "TURNOUT_DEFAULT_GAUGE": request["track_gauge_mm"],
        "TURNOUT_DEFAULT_FLANGEWAY": request["flangeway_mm"],
    }
    if constants != expected_constants:
        errors.append("B14 crossover request constants drifted")

    solve_calls = _calls(b14_functions["solve_rea_c10_crossover_geometry"])
    if "_crossover_solve_toe_b" not in solve_calls:
        errors.append("legacy preview solver no longer resolves the connector")
    for absent in ("turnout_mapping_metrics", "_crossover_minimum_radius_value"):
        if absent in solve_calls:
            errors.append("legacy preview mismatch no longer matches contract: {}".format(absent))

    mapping_keys = _return_string_keys(b14_functions["turnout_mapping_metrics"])
    if not {"host_minimum_radius", "turnout_minimum_radius"}.issubset(mapping_keys):
        errors.append("mapped-turnout analytical result fields drifted")
    turnout_build_calls = _calls(b14_functions["_build_curve_inheriting_c10_turnout"])
    if "turnout_mapping_metrics" not in turnout_build_calls:
        errors.append("turnout build no longer consumes the analytical mapping boundary")

    build_calls = _calls(b14_functions["_build_rea_c10_crossover_geometry"])
    build_turnouts = build_calls.get("_build_curve_inheriting_c10_turnout", [])
    complete_calls = build_calls.get("_crossover_minimum_radius_value", [])
    if len(build_turnouts) != 2 or len(complete_calls) != 1:
        errors.append("legacy complete crossover gate structure drifted")
    else:
        late_work = build_turnouts + build_calls.get("_crossover_make_connector_shapes", []) + build_calls.get("fuse", []) + build_calls.get("makeCompound", [])
        if not late_work or complete_calls[0].lineno <= max(node.lineno for node in late_work):
            errors.append("legacy complete gate is no longer after exact-shape work")

    preview_calls = _calls(b14_methods["preview_geometry"])
    if len(preview_calls.get("solve_rea_c10_crossover_geometry", [])) != 1:
        errors.append("preview does not have the characterised solver boundary")
    create_calls = _calls(b14_methods["create_crossover"])
    if len(create_calls.get("preview_geometry", [])) != 1:
        errors.append("create no longer reuses preview first")
    for name in (
        "create_rea_c10_crossover",
        "edit_rea_c10_crossover",
        "extend_turnout_to_rea_c10_crossover",
    ):
        calls = create_calls.get(name, [])
        if len(calls) != 1:
            errors.append("{} entry route drifted".format(name))
            continue
        keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords}
        pre_solved = keywords.get("pre_solved")
        if not isinstance(pre_solved, ast.Name) or pre_solved.id != "result":
            errors.append("{} no longer reuses the preview result".format(name))
    return errors


def validate_fail_closed_mutations(contract):
    mutations = []
    changed = copy.deepcopy(contract)
    changed["witnesses"][0].pop("connector_minimum_radius_mm")
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["witnesses"][0]["complete_rule_result"] = "accept"
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["scope"]["still_open"] = "complete"
    mutations.append(changed)
    changed = copy.deepcopy(contract)
    changed["successor_acceptance"]["rules"].pop()
    mutations.append(changed)
    return all(validate_contract(mutation) for mutation in mutations)


def validate():
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        raise SystemExit("Phase 1 crossover feasibility contract fingerprint drifted")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors = validate_contract(contract)
    errors.extend(validate_source(contract))
    if not validate_fail_closed_mutations(contract):
        errors.append("crossover feasibility mutation checks did not fail closed")
    if errors:
        raise SystemExit("\n".join("- {}".format(error) for error in errors))
    print("Phase 1 crossover feasibility contract checks passed")


if __name__ == "__main__":
    validate()
