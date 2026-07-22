#!/usr/bin/env python3
"""Validate the selected Phase 1 transition-pilot acceptance contract."""

import ast
import copy
import hashlib
import itertools
import json
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase1_inventory  # noqa: E402


CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-transition-pilot.json"
EXPECTED_CONTRACT_SHA256 = (
    "724f0d8812c355b2aacc2993353d5d56aea18ba57b241a5d3b30c7cd1e678ada"
)
CANDIDATE_REGISTER_PATH = (
    ROOT / "reference" / "contracts" / "phase1-candidate-boundaries.json"
)
SOURCE_PATHS = {
    "b14": ROOT / "AdvancedTurnout.FCMacro",
    "b15": ROOT
    / (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ),
}
FUNCTION_NAMES = (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)
TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "recorded_on",
    "status",
    "phase",
    "source_state",
    "selection",
    "successor",
    "module_boundary",
    "parity_contract",
    "performance_contract",
    "rollback_contract",
    "implementation_gates",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _function(tree, name):
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(matches) != 1:
        raise ValueError("Expected one top-level {!r} definition".format(name))
    return matches[0]


def _assignment_value(tree, name):
    matches = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            matches.append(node.value)
    if len(matches) != 1:
        raise ValueError("Expected one top-level {!r} assignment".format(name))
    return ast.literal_eval(matches[0])


def _signature_record(function):
    positional = list(function.args.posonlyargs) + list(function.args.args)
    parameters = [argument.arg for argument in positional]
    defaults = {}
    if function.args.defaults:
        start = len(positional) - len(function.args.defaults)
        for argument, default in zip(positional[start:], function.args.defaults):
            defaults[argument.arg] = ast.literal_eval(default)
    if function.args.vararg or function.args.kwarg or function.args.kwonlyargs:
        raise ValueError("Pilot functions must retain simple positional signatures")
    return parameters, defaults


def _load_namespace(path, declared_tolerance):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    observed_tolerance = _assignment_value(tree, "GEOMETRY_TOLERANCE")
    if observed_tolerance != declared_tolerance:
        raise ValueError("GEOMETRY_TOLERANCE drifted")
    definitions = [_function(tree, name) for name in FUNCTION_NAMES]
    definitions.sort(key=lambda node: node.lineno)
    module = ast.Module(body=definitions, type_ignores=[])
    namespace = {
        "math": math,
        "GEOMETRY_TOLERANCE": observed_tolerance,
    }
    exec(compile(module, str(path), "exec"), namespace)
    return tree, namespace


def _non_empty_unique_strings(value):
    return (
        isinstance(value, list)
        and bool(value)
        and len(value) == len(set(value))
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate_contract(document):
    errors = []
    if not isinstance(document, dict):
        return ["pilot contract must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("pilot contract top-level fields are invalid")
    if document.get("schema_version") != 1:
        errors.append("pilot contract schema_version must be 1")
    if document.get("contract_id") != "tracktemplate:phase1:transition-pilot:1":
        errors.append("pilot contract_id is invalid")
    if document.get("status") != (
        "selected-contract-frozen-phase2-foundation-authorised-"
        "source-movement-not-started"
    ):
        errors.append("pilot Phase 2 foundation authority/status drifted")
    if document.get("phase") != 1:
        errors.append("pilot selection belongs to Phase 1")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or set(source_state) != set(SOURCE_PATHS):
        errors.append("pilot source_state must identify exact B14 and B15 records")
    else:
        for label, path in SOURCE_PATHS.items():
            record = source_state.get(label)
            if not isinstance(record, dict) or set(record) != {
                "path",
                "sha256",
                "role",
            }:
                errors.append("{} source record fields are invalid".format(label))
                continue
            if record.get("path") != path.relative_to(ROOT).as_posix():
                errors.append("{} pilot source path is invalid".format(label))
            if not isinstance(record.get("sha256"), str) or len(record["sha256"]) != 64:
                errors.append("{} pilot source hash is invalid".format(label))
            if not str(record.get("role", "")).strip():
                errors.append("{} pilot source role is missing".format(label))

    selection = document.get("selection")
    expected_selection_keys = {
        "candidate_id",
        "selection_class",
        "owner_accepted_on",
        "owner_acceptance_basis",
        "scorecard_path",
        "candidate_register_path",
        "scope",
    }
    if not isinstance(selection, dict) or set(selection) != expected_selection_keys:
        errors.append("pilot selection fields are invalid")
    else:
        if selection.get("candidate_id") != "transition_length_solver":
            errors.append("the selected pilot must be transition_length_solver")
        if selection.get("selection_class") != (
            "first-architecture-pilot-not-performance-optimisation"
        ):
            errors.append("pilot selection class is invalid")
        if selection.get("owner_accepted_on") != "2026-07-20":
            errors.append("pilot owner-acceptance date is invalid")
        if selection.get("scorecard_path") != (
            "reference/PHASE1_SLICE_SCORECARD.md"
        ):
            errors.append("pilot scorecard path is invalid")
        if selection.get("candidate_register_path") != (
            "reference/contracts/phase1-candidate-boundaries.json"
        ):
            errors.append("pilot candidate-register path is invalid")
        for field in ("owner_acceptance_basis", "scope"):
            if not isinstance(selection.get(field), str) or not selection[field].strip():
                errors.append("pilot selection requires {}".format(field))

    successor = document.get("successor")
    expected_successor_keys = {
        "development_checkpoint_id",
        "checkpoint_scope",
        "compatibility_launcher_path",
        "compatibility_launcher_status",
        "compatibility_launcher_rule",
        "authoritative_package",
        "public_workbench_version_status",
        "behavioural_reference",
        "legacy_oracle",
    }
    if not isinstance(successor, dict) or set(successor) != expected_successor_keys:
        errors.append("pilot successor fields are invalid")
    else:
        exact_successor = {
            "development_checkpoint_id": "10.2A8A7B16",
            "compatibility_launcher_path": "TrackTemplate.FCMacro",
            "compatibility_launcher_status": "reserved-not-created",
            "authoritative_package": "tracktemplate",
            "public_workbench_version_status": "deferred-to-release-qualification",
            "behavioural_reference": "b15",
            "legacy_oracle": "b14",
        }
        for field, expected in exact_successor.items():
            if successor.get(field) != expected:
                errors.append("pilot successor {} is invalid".format(field))
        for field in ("checkpoint_scope", "compatibility_launcher_rule"):
            if not isinstance(successor.get(field), str) or not successor[field].strip():
                errors.append("pilot successor requires {}".format(field))

    boundary = document.get("module_boundary")
    expected_boundary_keys = {
        "domain_module_path",
        "temporary_facade_path",
        "facade_stability",
        "standard_library_imports",
        "forbidden_import_roots",
        "constants",
        "functions",
        "external_caller_routes",
        "outgoing_project_definition_dependencies",
        "migration_route",
        "current_input_policy",
        "behaviour_change_policy",
    }
    if not isinstance(boundary, dict) or set(boundary) != expected_boundary_keys:
        errors.append("pilot module-boundary fields are invalid")
    else:
        if boundary.get("domain_module_path") != "tracktemplate/domain/alignment.py":
            errors.append("pilot domain-module path is invalid")
        if boundary.get("temporary_facade_path") != "tracktemplate/api.py":
            errors.append("pilot temporary-façade path is invalid")
        if boundary.get("standard_library_imports") != ["math"]:
            errors.append("pilot standard-library imports are invalid")
        if boundary.get("constants") != {"GEOMETRY_TOLERANCE": 1.0e-8}:
            errors.append("pilot constant boundary is invalid")
        forbidden = boundary.get("forbidden_import_roots")
        if not _non_empty_unique_strings(forbidden):
            errors.append("pilot forbidden imports must be unique non-empty names")
        elif set(forbidden) != {
            "FreeCAD",
            "FreeCADGui",
            "Part",
            "PySide",
            "PySide2",
            "PySide6",
            "pivy",
        }:
            errors.append("pilot forbidden-import boundary is incomplete")
        functions = boundary.get("functions")
        if not isinstance(functions, list) or [
            item.get("name") for item in functions if isinstance(item, dict)
        ] != list(FUNCTION_NAMES):
            errors.append("pilot functions/order are invalid")
        routes = boundary.get("external_caller_routes")
        if not isinstance(routes, list) or [
            item.get("caller") for item in routes if isinstance(item, dict)
        ] != [
            "main_circle_centre",
            "build_concentric_core",
            "prepare_track_alignment",
        ]:
            errors.append("pilot external caller routes are invalid")
        if boundary.get("outgoing_project_definition_dependencies") != []:
            errors.append("pilot must retain no outgoing project-definition dependency")
        for field in (
            "facade_stability",
            "migration_route",
            "current_input_policy",
            "behaviour_change_policy",
        ):
            if not isinstance(boundary.get(field), str) or not boundary[field].strip():
                errors.append("pilot module boundary requires {}".format(field))

    parity = document.get("parity_contract")
    expected_parity_keys = {
        "comparison",
        "fixed_oracle_path",
        "pilot_validator_path",
        "displacement_grid",
        "offset_grid",
        "solver_scenarios",
        "solver_target_fractions",
        "error_cases",
        "workflow_oracles",
        "real_freecad_scope",
    }
    if not isinstance(parity, dict) or set(parity) != expected_parity_keys:
        errors.append("pilot parity fields are invalid")
    else:
        if parity.get("fixed_oracle_path") != "tests/validate_phase1_alignment.py":
            errors.append("pilot fixed oracle path is invalid")
        if parity.get("pilot_validator_path") != (
            "tests/validate_phase1_transition_pilot.py"
        ):
            errors.append("pilot validator path is invalid")
        fractions = parity.get("solver_target_fractions")
        if not isinstance(fractions, list) or fractions != sorted(set(fractions or [])):
            errors.append("pilot solver fractions must be ordered and unique")
        elif not fractions or fractions[0] != 0.0 or fractions[-1] != 1.0:
            errors.append("pilot solver fractions must include both endpoints")
        if not _non_empty_unique_strings(parity.get("workflow_oracles")):
            errors.append("pilot workflow oracles must be unique non-empty paths")
        if not isinstance(parity.get("error_cases"), list) or not parity["error_cases"]:
            errors.append("pilot error cases are missing")
        for field in ("comparison", "real_freecad_scope"):
            if not isinstance(parity.get(field), str) or not parity[field].strip():
                errors.append("pilot parity contract requires {}".format(field))

    performance = document.get("performance_contract")
    if not isinstance(performance, dict) or set(performance) != {
        "purpose",
        "calculation_profile",
        "workflow_profiles",
        "comparison_rule",
        "acceptance_rule",
    }:
        errors.append("pilot performance fields are invalid")
    elif not _non_empty_unique_strings(performance.get("workflow_profiles")):
        errors.append("pilot workflow profiles must be unique non-empty text")

    rollback = document.get("rollback_contract")
    if not isinstance(rollback, dict) or set(rollback) != {
        "legacy_reference_retention",
        "pre_routing_rollback",
        "routed_rollback",
        "retirement_gate",
    }:
        errors.append("pilot rollback fields are invalid")
    elif any(not isinstance(value, str) or not value.strip() for value in rollback.values()):
        errors.append("every pilot rollback rule must be non-empty text")

    if not _non_empty_unique_strings(document.get("implementation_gates")):
        errors.append("pilot implementation gates must be unique non-empty text")
    return errors


def _validate_function_contract(errors, tree, declared_functions, label):
    observed = {}
    for name in FUNCTION_NAMES:
        try:
            observed[name] = _signature_record(_function(tree, name))
        except Exception as error:
            errors.append("{} {} signature failed: {}".format(label, name, error))
    for declaration in declared_functions:
        name = declaration.get("name")
        expected = (declaration.get("parameters"), declaration.get("defaults"))
        if observed.get(name) != expected:
            errors.append("{} {} signature/defaults drifted".format(label, name))


def _capture_error(action):
    try:
        action()
    except Exception as error:  # Contract records the exact legacy exception.
        return type(error).__name__, str(error)
    return None


def validate_source_and_parity(document):
    errors = []
    boundary = document["module_boundary"]
    tolerance = boundary["constants"]["GEOMETRY_TOLERANCE"]
    namespaces = {}
    for label, path in SOURCE_PATHS.items():
        declared_hash = document["source_state"][label]["sha256"]
        if _sha256(path) != declared_hash:
            errors.append("{} pilot source fingerprint drifted".format(label))
            continue
        try:
            tree, namespace = _load_namespace(path, tolerance)
            namespaces[label] = namespace
            _validate_function_contract(errors, tree, boundary["functions"], label)
        except Exception as error:
            errors.append("{} pilot source loading failed: {}".format(label, error))
    if len(namespaces) != len(SOURCE_PATHS):
        return errors

    expected_routes = boundary["external_caller_routes"]
    for label, path in SOURCE_PATHS.items():
        report = phase1_inventory.analyse_source(path, label.upper())
        candidate = next(
            item
            for item in report["candidates"]
            if item["name"] == "transition_length_solver"
        )
        observed_routes = [
            {
                "caller": item["name"],
                "targets": [target["name"] for target in item["targets"]],
            }
            for item in candidate["closure_external_callers"]
        ]
        if observed_routes != expected_routes:
            errors.append("{} pilot external caller routes drifted".format(label))
        if candidate["closure_outgoing_dependencies"] != (
            boundary["outgoing_project_definition_dependencies"]
        ):
            errors.append("{} pilot outgoing dependency cut drifted".format(label))
        if [item["name"] for item in candidate["closure"]] != list(FUNCTION_NAMES):
            errors.append("{} pilot dependency closure/order drifted".format(label))

    parity = document["parity_contract"]
    first = namespaces["b14"]
    second = namespaces["b15"]
    displacement_grid = parity["displacement_grid"]
    for arguments in itertools.product(
        displacement_grid["lengths_mm"],
        displacement_grid["radii_mm"],
        displacement_grid["integration_steps"],
    ):
        b14_value = first["clothoid_entry_displacement"](*arguments)
        b15_value = second["clothoid_entry_displacement"](*arguments)
        if type(b14_value) is not type(b15_value) or b14_value != b15_value:
            errors.append("displacement grid parity failed for {!r}".format(arguments))

    offset_grid = parity["offset_grid"]
    for arguments in itertools.product(
        offset_grid["circle_centre_y_mm"],
        offset_grid["radii_mm"],
        offset_grid["transition_lengths_mm"],
    ):
        b14_value = first["transition_start_signed_offset"](*arguments)
        b15_value = second["transition_start_signed_offset"](*arguments)
        if type(b14_value) is not type(b15_value) or b14_value != b15_value:
            errors.append("offset grid parity failed for {!r}".format(arguments))

    for scenario in parity["solver_scenarios"]:
        base_arguments = (
            scenario["circle_centre_y_mm"],
            scenario["radius_mm"],
        )
        angle = scenario["total_angle_rad"]
        maximum_length = (2.0 * scenario["radius_mm"] * angle) - 1.0e-6
        endpoints = []
        for namespace in (first, second):
            signed_offset = namespace["transition_start_signed_offset"]
            endpoints.append(
                (
                    signed_offset(*base_arguments, 0.0),
                    signed_offset(*base_arguments, maximum_length),
                )
            )
        if endpoints[0] != endpoints[1]:
            errors.append("solver endpoint generation drifted for {!r}".format(scenario))
            continue
        start, finish = endpoints[0]
        for fraction in parity["solver_target_fractions"]:
            target = start + (fraction * (finish - start))
            arguments = (
                scenario["circle_centre_y_mm"],
                scenario["radius_mm"],
                target,
                angle,
                scenario["track_name"],
                scenario["end_name"],
            )
            b14_value = first["solve_transition_length"](*arguments)
            b15_value = second["solve_transition_length"](*arguments)
            if type(b14_value) is not type(b15_value) or b14_value != b15_value:
                errors.append("solver grid parity failed for {!r}".format(arguments))

    for case in parity["error_cases"]:
        function_name = case["function"]
        arguments = case["arguments"]
        observed = [
            _capture_error(lambda ns=namespace: ns[function_name](*arguments))
            for namespace in (first, second)
        ]
        if observed[0] != observed[1]:
            errors.append("error parity drifted for {}".format(function_name))
        if (
            observed[0] is None
            or observed[0][0] != case["exception_type"]
            or case["required_text"] not in observed[0][1]
        ):
            errors.append("error contract drifted for {}".format(function_name))

    declared_paths = [
        parity["fixed_oracle_path"],
        parity["pilot_validator_path"],
    ] + parity["workflow_oracles"]
    for relative in declared_paths:
        if not (ROOT / relative).is_file():
            errors.append("declared pilot evidence is missing: {}".format(relative))

    successor = document["successor"]
    if successor["compatibility_launcher_status"] == "reserved-not-created":
        if (ROOT / successor["compatibility_launcher_path"]).exists():
            errors.append("reserved-not-created B16 launcher already exists")
        if (ROOT / successor["authoritative_package"]).exists():
            errors.append("reserved-not-created pilot package already exists")
    return errors


def validate_register_link(document):
    register = json.loads(CANDIDATE_REGISTER_PATH.read_text(encoding="utf-8"))
    gate = register.get("selection_gate", {})
    expected_gate = {
        "status": "selected-owner-accepted-contract-frozen",
        "selected_candidate_id": document["selection"]["candidate_id"],
        "selected_on": document["selection"]["owner_accepted_on"],
        "selection_contract_path": CONTRACT_PATH.relative_to(ROOT).as_posix(),
        "recommendation_evidence_path": document["selection"]["scorecard_path"],
    }
    errors = []
    if register.get("schema_version") != 3:
        errors.append("candidate register must use schema 3 after selection")
    if register.get("status") != (
        "inventory-and-selection-complete-source-movement-not-started"
    ):
        errors.append("candidate register selection status is invalid")
    if gate != expected_gate:
        errors.append("candidate register does not point exactly to the pilot contract")
    return errors


def validate_fail_closed(document):
    wrong_candidate = copy.deepcopy(document)
    wrong_candidate["selection"]["candidate_id"] = "chair_analysis_core"
    assert validate_contract(wrong_candidate), "wrong candidate must fail closed"

    wrong_version = copy.deepcopy(document)
    wrong_version["successor"]["development_checkpoint_id"] = "10.2A8A7B15"
    assert validate_contract(wrong_version), "reused B15 version must fail closed"

    weakened_imports = copy.deepcopy(document)
    weakened_imports["module_boundary"]["forbidden_import_roots"].remove("FreeCAD")
    assert validate_contract(weakened_imports), "weakened import gate must fail closed"

    missing_endpoint = copy.deepcopy(document)
    missing_endpoint["parity_contract"]["solver_target_fractions"].pop()
    assert validate_contract(missing_endpoint), "missing endpoint must fail closed"


def validate():
    assert _sha256(CONTRACT_PATH) == EXPECTED_CONTRACT_SHA256, (
        "The frozen transition-pilot contract changed without an accepted "
        "contract-version/test update"
    )
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors = validate_contract(document)
    errors.extend(validate_register_link(document))
    errors.extend(validate_source_and_parity(document))
    assert not errors, "\n".join(errors)
    validate_fail_closed(document)
    print("Phase 1 transition pilot contract validation passed")


if __name__ == "__main__":
    validate()
