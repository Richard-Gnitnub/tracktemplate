#!/usr/bin/env python3
"""Validate the fail-closed Phase 1 candidate boundary register."""

import ast
import copy
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase1_inventory  # noqa: E402


REGISTER_PATH = (
    ROOT / "reference" / "contracts" / "phase1-candidate-boundaries.json"
)
SCORECARD_PATH = ROOT / "reference" / "PHASE1_SLICE_SCORECARD.md"
SOURCE_PATHS = {
    "b14": ROOT / "AdvancedTurnout.FCMacro",
    "b15": ROOT
    / (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ),
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "register_id",
    "recorded_on",
    "status",
    "status_reason",
    "source_state",
    "conventions",
    "source_anchors",
    "candidates",
    "selection_gate",
}
CANDIDATE_KEYS = {
    "candidate_id",
    "candidate_kind",
    "contract_status",
    "role",
    "roots",
    "inputs",
    "outputs",
    "units",
    "coordinate_frames",
    "tolerances",
    "identities",
    "ordering",
    "schemas",
    "signature_and_invalidation",
    "side_effects",
    "errors",
    "existing_oracles",
    "structural_inventory",
    "extraction_disposition",
    "open_gaps",
}
EXPECTED_CANDIDATES = {
    name: list(roots)
    for name, roots in phase1_inventory.DEFAULT_CANDIDATES
}
EXPECTED_CANDIDATE_ORDER = list(EXPECTED_CANDIDATES)
EXPECTED_CONTRACT_STATUS = {
    "curve_easement_station": "composed-current-legacy-boundary",
    "transition_length_solver": "recorded-current-legacy-boundary",
    "alignment_station_index": "recorded-current-legacy-boundary",
    "alignment_station_interpolation": "recorded-current-legacy-boundary",
    "chair_analysis_core": (
        "recorded-current-legacy-boundary-with-open-signature-and-provenance-gates"
    ),
}
EXPECTED_DISPOSITIONS = {
    "curve_easement_station": "not-selected-too-broad",
    "transition_length_solver": (
        "recommended-first-architecture-pilot-owner-decision-pending"
    ),
    "alignment_station_index": "not-selected-high-fanout",
    "alignment_station_interpolation": "not-selected-adapter-seam-required",
    "chair_analysis_core": (
        "not-selected-coupling-signature-and-provenance-gates-open"
    ),
}
CHAIR_SCHEMA_KEYS = {
    "analysis_schema_version",
    "default_setting_fields",
    "normalised_setting_fields",
    "numeric_setting_defaults",
    "boolean_setting_defaults",
    "numeric_setting_bounds",
    "turnout_rail_fields",
    "turnout_rail_source_fields",
    "connector_rail_fields",
    "connector_rail_source_fields",
    "timber_fields",
    "timber_source_fields",
    "position_fields",
    "generation_only_position_fields",
    "position_source_fields",
    "footprint_fields",
    "future_solid_parameter_fields",
    "protected_support_zone_fields",
    "model_support_adjustment_fields",
    "finding_fields",
    "model_support_plan_fields",
    "summary_fields",
    "analysis_result_fields",
    "persistent_property_names",
}
PERSISTENT_PROPERTY_SYMBOLS = {
    "settings": "CHAIR_ANALYSIS_SETTINGS_PROPERTY",
    "result": "CHAIR_ANALYSIS_RESULT_PROPERTY",
    "status": "CHAIR_ANALYSIS_STATUS_PROPERTY",
    "signature": "CHAIR_ANALYSIS_SIGNATURE_PROPERTY",
}


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


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


def _function_occurrences(tree, symbol):
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    ]


def _function(tree, symbol, occurrence=-1):
    nodes = _function_occurrences(tree, symbol)
    if not nodes:
        raise AssertionError("missing function {}".format(symbol))
    if occurrence == -1:
        return nodes[-1]
    if occurrence < 1 or occurrence > len(nodes):
        raise AssertionError(
            "function {} has no occurrence {}".format(symbol, occurrence)
        )
    return nodes[occurrence - 1]


def _assignment_occurrences(tree, symbol):
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
            matches.append(node)
    return matches


def _assignment_value(tree, symbol, occurrence=-1):
    nodes = _assignment_occurrences(tree, symbol)
    if not nodes:
        raise AssertionError("missing assignment {}".format(symbol))
    node = nodes[-1] if occurrence == -1 else nodes[occurrence - 1]
    return _normalise_literal(ast.literal_eval(node.value))


def _dict_key_sets(node):
    result = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Dict) or not child.keys:
            continue
        if not all(
            isinstance(key, ast.Constant) and isinstance(key.value, str)
            for key in child.keys
            if key is not None
        ):
            continue
        result.append(
            tuple(key.value for key in child.keys if key is not None)
        )
    return result


def _require_dict_keys(errors, tree, function_name, expected, occurrence=-1):
    node = _function(tree, function_name, occurrence)
    observed = [set(values) for values in _dict_key_sets(node)]
    if set(expected) not in observed:
        errors.append(
            "{} occurrence {} no longer contains schema {}".format(
                function_name, occurrence, sorted(expected)
            )
        )


def _local_assignment_literal(function, name):
    matches = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            matches.append(node.value)
    if not matches:
        raise AssertionError(
            "{} has no local assignment {}".format(function.name, name)
        )
    return _normalise_literal(ast.literal_eval(matches[-1]))


def _literal_default_values(function, expected_fields):
    candidates = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Dict):
            continue
        keys = [
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        ]
        if set(keys) == set(expected_fields):
            candidates.append(node)
    if len(candidates) != 1:
        raise AssertionError("chair default-settings dictionary is ambiguous")
    values = {}
    for key, value in zip(candidates[0].keys, candidates[0].values):
        if not isinstance(key, ast.Constant) or key.value == "schema_version":
            continue
        values[key.value] = ast.literal_eval(value)
    return values


def _has_pop_call(function, key):
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "pop" or not node.args:
            continue
        if isinstance(node.args[0], ast.Constant) and node.args[0].value == key:
            return True
    return False


def _has_subscript_assignment(function, key):
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if not isinstance(target, ast.Subscript):
                continue
            slice_node = target.slice
            if isinstance(slice_node, ast.Constant) and slice_node.value == key:
                return True
    return False


def _candidate(document, candidate_id):
    return next(
        item
        for item in document["candidates"]
        if item["candidate_id"] == candidate_id
    )


def _non_empty_string_list(value):
    return (
        isinstance(value, list)
        and bool(value)
        and len(set(value)) == len(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate_register(document):
    """Return structural/decision errors without consulting the macros."""
    errors = []
    if not isinstance(document, dict):
        return ["register must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("register top-level fields do not match the contract")
    if document.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if document.get("register_id") != "tracktemplate:phase1:candidate-boundaries:2":
        errors.append("register_id must identify candidate-boundary schema 2")
    if document.get("status") != "inventory-and-recommendation-complete-selection-open":
        errors.append("candidate inventory/recommendation must keep selection open")
    if not str(document.get("status_reason", "")).strip():
        errors.append("register status requires a reason")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or set(source_state) != set(SOURCE_PATHS):
        errors.append("source_state must contain exact b14 and b15 records")
    else:
        for label, path in SOURCE_PATHS.items():
            record = source_state.get(label)
            if not isinstance(record, dict) or set(record) != {"path", "sha256", "role"}:
                errors.append("{} source record fields are invalid".format(label))
                continue
            if record.get("path") != path.relative_to(ROOT).as_posix():
                errors.append("{} source path is invalid".format(label))
            digest = record.get("sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append("{} source digest is invalid".format(label))
            if not str(record.get("role", "")).strip():
                errors.append("{} source role is missing".format(label))

    conventions = document.get("conventions")
    if not isinstance(conventions, dict) or not conventions:
        errors.append("conventions must be a non-empty mapping")
    elif any(not isinstance(value, str) or not value.strip() for value in conventions.values()):
        errors.append("every convention must be non-empty text")

    anchors = document.get("source_anchors")
    if not isinstance(anchors, list) or not anchors:
        errors.append("source_anchors must be a non-empty list")
        anchors = []
    anchor_ids = [item.get("anchor_id") for item in anchors if isinstance(item, dict)]
    if len(anchor_ids) != len(anchors) or len(set(anchor_ids)) != len(anchor_ids):
        errors.append("source anchor identifiers must be present and unique")
    for anchor in anchors:
        if not isinstance(anchor, dict):
            errors.append("every source anchor must be an object")
            continue
        common = {
            "anchor_id", "kind", "symbol", "occurrence", "b14_line", "b15_line"
        }
        kind = anchor.get("kind")
        expected = common | (
            {"ast_sha256"} if kind == "function_ast" else {"expected_value"}
        )
        if "b15_ast_sha256" in anchor:
            expected.add("b15_ast_sha256")
        if kind not in {"function_ast", "literal_assignment"} or set(anchor) != expected:
            errors.append("source anchor fields or kind are invalid")
        if not isinstance(anchor.get("occurrence"), int) or anchor.get("occurrence", 0) < 1:
            errors.append("source anchor occurrence must be positive")
        for field in ("b14_line", "b15_line"):
            if not isinstance(anchor.get(field), int) or anchor.get(field, 0) < 1:
                errors.append("source anchor line must be positive")
        if kind == "function_ast":
            digest = anchor.get("ast_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append("function source anchor requires a SHA-256 digest")
            b15_digest = anchor.get("b15_ast_sha256")
            if b15_digest is not None and (
                not isinstance(b15_digest, str) or len(b15_digest) != 64
            ):
                errors.append("B15 function source anchor requires a SHA-256 digest")
        elif "b15_ast_sha256" in anchor:
            errors.append("literal source anchors cannot have a B15 AST digest")

    candidates = document.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        candidates = []
    candidate_ids = [
        item.get("candidate_id") for item in candidates if isinstance(item, dict)
    ]
    if candidate_ids != EXPECTED_CANDIDATE_ORDER:
        errors.append("candidate IDs/order do not match the Phase 1 inventory")
    if len(set(candidate_ids)) != len(candidate_ids):
        errors.append("candidate identifiers must be unique")
    repeated_text_fields = (
        "inputs",
        "outputs",
        "units",
        "coordinate_frames",
        "tolerances",
        "identities",
        "ordering",
        "side_effects",
        "errors",
        "existing_oracles",
        "open_gaps",
    )
    for item in candidates:
        if not isinstance(item, dict):
            errors.append("each candidate must be an object")
            continue
        candidate_id = item.get("candidate_id")
        if set(item) != CANDIDATE_KEYS:
            errors.append("{} fields do not match the candidate contract".format(candidate_id))
        if item.get("roots") != EXPECTED_CANDIDATES.get(candidate_id):
            errors.append("{} roots do not match the static inventory".format(candidate_id))
        if item.get("contract_status") != EXPECTED_CONTRACT_STATUS.get(candidate_id):
            errors.append("{} contract status is invalid".format(candidate_id))
        if item.get("extraction_disposition") != EXPECTED_DISPOSITIONS.get(candidate_id):
            errors.append("{} extraction disposition is invalid".format(candidate_id))
        for field in ("candidate_kind", "role"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append("{} requires {}".format(candidate_id, field))
        for field in repeated_text_fields:
            if not _non_empty_string_list(item.get(field)):
                errors.append("{} requires unique non-empty {}".format(candidate_id, field))
        if not isinstance(item.get("schemas"), dict) or not item["schemas"]:
            errors.append("{} schemas must be a non-empty mapping".format(candidate_id))
        signature = item.get("signature_and_invalidation")
        if not isinstance(signature, dict) or not signature:
            errors.append("{} signature/invalidation must be recorded".format(candidate_id))
        structural = item.get("structural_inventory")
        if not isinstance(structural, dict) or set(structural) != set(SOURCE_PATHS):
            errors.append("{} must have b14/b15 structural facts".format(candidate_id))

    if candidate_ids == EXPECTED_CANDIDATE_ORDER:
        aggregate = _candidate(document, "curve_easement_station")
        expected_components = EXPECTED_CANDIDATE_ORDER[1:4]
        if aggregate["schemas"].get("composes_candidate_ids") != expected_components:
            errors.append("aggregate candidate component IDs are invalid")
        chair = _candidate(document, "chair_analysis_core")
        if set(chair["schemas"]) != CHAIR_SCHEMA_KEYS:
            errors.append("chair schema sections do not match the boundary contract")
        if chair["schemas"].get("analysis_schema_version") != 5:
            errors.append("chair analysis schema version must remain 5")
        for key, value in chair["schemas"].items():
            if key == "analysis_schema_version":
                continue
            if isinstance(value, list) and (
                not value or len(value) != len(set(value))
            ):
                errors.append("chair schema {} must be non-empty and unique".format(key))
            elif isinstance(value, dict) and not value:
                errors.append("chair schema {} must be non-empty".format(key))
        signature = chair["signature_and_invalidation"]
        if set(signature.get("known_signature_gaps", [])) == set():
            errors.append("chair signature omissions must remain explicit")
        if signature.get("rail_point_rounding_decimal_places") != 5:
            errors.append("chair rail signature rounding is invalid")
        if signature.get("timber_linear_rounding_decimal_places") != 5:
            errors.append("chair timber linear signature rounding is invalid")
        if signature.get("timber_angle_rounding_decimal_places") != 8:
            errors.append("chair timber angle signature rounding is invalid")

    gate = document.get("selection_gate")
    expected_gate_keys = {
        "status",
        "selected_candidate_id",
        "recommended_candidate_id",
        "recommendation_class",
        "scorecard_path",
        "current_structural_leader",
        "leader_reason",
        "not_a_selection",
        "required_before_selection",
    }
    if not isinstance(gate, dict) or set(gate) != expected_gate_keys:
        errors.append("selection_gate fields do not match the contract")
    else:
        if (
            gate.get("status") != "recommendation-ready-owner-decision-pending"
            or gate.get("selected_candidate_id") is not None
        ):
            errors.append("no extraction candidate may be selected by this register")
        if gate.get("recommended_candidate_id") != "transition_length_solver":
            errors.append("the scorecard recommendation must remain explicit")
        if gate.get("recommendation_class") != (
            "first-architecture-pilot-not-performance-optimisation"
        ):
            errors.append("the recommendation class is invalid")
        if gate.get("scorecard_path") != "reference/PHASE1_SLICE_SCORECARD.md":
            errors.append("the scorecard path is invalid")
        if gate.get("current_structural_leader") != "transition_length_solver":
            errors.append("the current structural leader must remain explicit")
        if not _non_empty_string_list(gate.get("required_before_selection")):
            errors.append("selection prerequisites must be unique non-empty text")
        for field in ("leader_reason", "not_a_selection"):
            if not isinstance(gate.get(field), str) or not gate[field].strip():
                errors.append("selection gate requires {}".format(field))
    return errors


def _structural_record(report, candidate_id):
    source = next(
        item for item in report["candidates"] if item["name"] == candidate_id
    )
    return {
        "root_lines": [item["line"] for item in source["roots"]],
        "closure_definition_count": source["closure_definition_count"],
        "closure_source_lines": source["closure_source_lines"],
        "direct_caller_count": len(source["direct_callers"]),
        "caller_closure_definition_count": source[
            "caller_closure_definition_count"
        ],
        "closure_external_caller_count": source[
            "closure_external_caller_count"
        ],
        "closure_outgoing_dependency_count": source[
            "closure_outgoing_dependency_count"
        ],
        "platform_signals": source["platform_signals"],
        "duplicate_definition_names": source["duplicate_definition_names"],
        "captured_alias_calls": source["captured_alias_calls"],
    }


def validate_source_contract(document):
    """Return drift/semantic errors against the immutable B14 and accepted B15."""
    errors = []
    trees = {}
    for label, path in SOURCE_PATHS.items():
        payload = path.read_bytes()
        digest = _sha256_bytes(payload)
        declared = document.get("source_state", {}).get(label, {}).get("sha256")
        if digest != declared:
            errors.append("{} source fingerprint does not match".format(label))
        try:
            trees[label] = ast.parse(payload.decode("utf-8"), filename=str(path))
        except Exception as error:
            errors.append("{} cannot be parsed: {}".format(label, error))
    if len(trees) != len(SOURCE_PATHS):
        return errors

    for anchor in document.get("source_anchors", []):
        if not isinstance(anchor, dict):
            continue
        symbol = anchor.get("symbol")
        occurrence = anchor.get("occurrence")
        for label, tree in trees.items():
            try:
                if anchor.get("kind") == "function_ast":
                    node = _function(tree, symbol, occurrence)
                    digest = _sha256_bytes(
                        ast.dump(node, include_attributes=False).encode("utf-8")
                    )
                    expected_digest = anchor.get(
                        label + "_ast_sha256", anchor.get("ast_sha256")
                    )
                    if digest != expected_digest:
                        errors.append(
                            "{} function anchor {} digest drifted".format(
                                label, anchor.get("anchor_id")
                            )
                        )
                else:
                    nodes = _assignment_occurrences(tree, symbol)
                    node = nodes[occurrence - 1]
                    value = _normalise_literal(ast.literal_eval(node.value))
                    if value != anchor.get("expected_value"):
                        errors.append(
                            "{} literal anchor {} value drifted".format(
                                label, anchor.get("anchor_id")
                            )
                        )
                if node.lineno != anchor.get(label + "_line"):
                    errors.append(
                        "{} source anchor {} line drifted".format(
                            label, anchor.get("anchor_id")
                        )
                    )
            except Exception as error:
                errors.append(
                    "{} source anchor {} failed: {}".format(
                        label, anchor.get("anchor_id"), error
                    )
                )

    reports = {
        label: phase1_inventory.analyse_source(path, label.upper())
        for label, path in SOURCE_PATHS.items()
    }
    for label, report in reports.items():
        if report.get("schema_version") != 2:
            errors.append("{} inventory report must use schema 2".format(label))
    for candidate in document.get("candidates", []):
        candidate_id = candidate.get("candidate_id")
        for label, report in reports.items():
            try:
                observed = _structural_record(report, candidate_id)
                expected = candidate["structural_inventory"][label]
                if observed != expected:
                    errors.append(
                        "{} {} structural inventory drifted".format(
                            label, candidate_id
                        )
                    )
            except Exception as error:
                errors.append(
                    "{} {} structural validation failed: {}".format(
                        label, candidate_id, error
                    )
                )

    transition = _candidate(document, "transition_length_solver")
    station_index = _candidate(document, "alignment_station_index")
    station_interpolation = _candidate(
        document, "alignment_station_interpolation"
    )
    chair = _candidate(document, "chair_analysis_core")
    schemas = chair["schemas"]
    signature = chair["signature_and_invalidation"]
    for label, tree in trees.items():
        solver = _function(tree, "solve_transition_length")
        parameter_order = [argument.arg for argument in solver.args.args]
        if parameter_order != transition["schemas"].get("input_parameter_order"):
            errors.append("{} transition parameter order drifted".format(label))

        _require_dict_keys(
            errors,
            tree,
            "alignment_station_data",
            station_index["schemas"].get("station_data_fields", []),
        )
        expected_interpolation_fields = set(
            station_interpolation["schemas"].get(
                "required_station_data_fields", []
            )
        )
        interpolation = _function(tree, "interpolate_alignment_station")
        subscript_keys = {
            child.slice.value
            for child in ast.walk(interpolation)
            if isinstance(child, ast.Subscript)
            and isinstance(child.slice, ast.Constant)
            and isinstance(child.slice.value, str)
        }
        if not expected_interpolation_fields.issubset(subscript_keys):
            errors.append("{} station interpolation schema drifted".format(label))

        defaults_function = _function(
            tree, "default_chair_analysis_settings", occurrence=3
        )
        default_fields = schemas["default_setting_fields"]
        _require_dict_keys(
            errors,
            tree,
            "default_chair_analysis_settings",
            default_fields,
            occurrence=3,
        )
        try:
            default_values = _literal_default_values(
                defaults_function, default_fields
            )
            declared_defaults = dict(schemas["numeric_setting_defaults"])
            declared_defaults.update(schemas["boolean_setting_defaults"])
            if default_values != declared_defaults:
                errors.append("{} chair setting defaults drifted".format(label))
        except Exception as error:
            errors.append("{} chair setting defaults failed: {}".format(label, error))

        normalise = _function(
            tree, "normalise_chair_analysis_settings", occurrence=3
        )
        try:
            bounds = _local_assignment_literal(normalise, "limits")
            if bounds != schemas["numeric_setting_bounds"]:
                errors.append("{} chair numeric setting bounds drifted".format(label))
        except Exception as error:
            errors.append("{} chair setting bounds failed: {}".format(label, error))
        if set(schemas["normalised_setting_fields"]) != (
            set(default_fields) | {"rail_profile_id"}
        ) or not _has_subscript_assignment(normalise, "rail_profile_id"):
            errors.append("{} normalised chair setting schema drifted".format(label))

        schema_functions = (
            ("_chair_turnout_rail_records", 2, "turnout_rail_fields"),
            ("_chair_turnout_rail_records", 2, "turnout_rail_source_fields"),
            ("_chair_connector_rail_records", 2, "connector_rail_fields"),
            ("_chair_connector_rail_records", 2, "connector_rail_source_fields"),
            ("_timber_record_from_layout", 1, "timber_fields"),
            ("_timber_record_from_layout", 1, "timber_source_fields"),
            ("generate_chair_positions", 2, "footprint_fields"),
            ("generate_chair_positions", 2, "future_solid_parameter_fields"),
            ("generate_chair_positions", 2, "position_source_fields"),
            ("_chair_support_zone", 1, "protected_support_zone_fields"),
            ("_chair_model_support_adjustment", 1, "model_support_adjustment_fields"),
            ("_chair_finding", 1, "finding_fields"),
            ("_chair_model_support_plan", 1, "model_support_plan_fields"),
            ("analyse_chair_position_records", 2, "summary_fields"),
            ("analyse_chair_position_records", 2, "analysis_result_fields"),
        )
        for function_name, occurrence, schema_name in schema_functions:
            _require_dict_keys(
                errors,
                tree,
                function_name,
                schemas[schema_name],
                occurrence=occurrence,
            )

        expected_generated_position = set(schemas["position_fields"]) | set(
            schemas["generation_only_position_fields"]
        )
        _require_dict_keys(
            errors,
            tree,
            "generate_chair_positions",
            expected_generated_position,
            occurrence=2,
        )
        refine = _function(tree, "_chair_refine_bridge_candidates")
        if schemas["generation_only_position_fields"] != ["_generation_timber"]:
            errors.append("{} generation-only chair field contract drifted".format(label))
        elif not _has_pop_call(refine, "_generation_timber"):
            errors.append("{} temporary chair field is no longer removed".format(label))

        _require_dict_keys(
            errors,
            tree,
            "_chair_geometry_signature",
            {
                "schema_version",
                "entity_kind",
                "entity_id",
                "settings",
                "rails",
                "timbers",
            },
        )
        _require_dict_keys(
            errors,
            tree,
            "_chair_geometry_signature",
            signature["rail_signature_fields"],
        )
        _require_dict_keys(
            errors,
            tree,
            "_chair_geometry_signature",
            signature["timber_signature_fields"],
        )
        geometry_signature = _function(tree, "_chair_geometry_signature")
        excluded_candidates = [
            [item.value for item in child.elts]
            for child in ast.walk(geometry_signature)
            if isinstance(child, ast.Tuple)
            and child.elts
            and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in child.elts
            )
        ]
        if signature["display_only_settings_excluded"] not in excluded_candidates:
            errors.append("{} display-only signature exclusions drifted".format(label))

        for field, symbol in PERSISTENT_PROPERTY_SYMBOLS.items():
            if schemas["persistent_property_names"].get(field) != _assignment_value(
                tree, symbol
            ):
                errors.append("{} chair property {} drifted".format(label, field))

    scorecard_path = ROOT / document["selection_gate"]["scorecard_path"]
    if scorecard_path != SCORECARD_PATH or not scorecard_path.is_file():
        errors.append("the declared first-slice scorecard is unavailable")
    else:
        scorecard = scorecard_path.read_text(encoding="utf-8")
        required_scorecard_text = (
            "recommendation complete; project-owner decision pending",
            "Recommend `transition_length_solver`",
            "Selected candidate: **none**",
            "Recommendation class: first architecture pilot",
            "optimisation",
        )
        for required in required_scorecard_text:
            if required not in scorecard:
                errors.append(
                    "the first-slice scorecard is missing {!r}".format(required)
                )
    return errors


def validate_fail_closed(document):
    selected = copy.deepcopy(document)
    selected["selection_gate"]["selected_candidate_id"] = "transition_length_solver"
    assert validate_register(selected), "selection mutation must fail closed"

    redirected = copy.deepcopy(document)
    redirected["selection_gate"]["recommended_candidate_id"] = (
        "chair_analysis_core"
    )
    assert validate_register(redirected), "recommendation mutation must fail closed"

    promoted = copy.deepcopy(document)
    promoted["candidates"][-1]["contract_status"] = "ready"
    assert validate_register(promoted), "chair readiness mutation must fail closed"

    missing_schema = copy.deepcopy(document)
    missing_schema["candidates"][-1]["schemas"].pop("analysis_result_fields")
    assert validate_register(missing_schema), "missing chair schema must fail closed"

    bad_source = copy.deepcopy(document)
    bad_source["source_state"]["b15"]["sha256"] = "0" * 64
    assert validate_source_contract(bad_source), "source drift must fail closed"


def validate():
    document = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register_errors = validate_register(document)
    assert not register_errors, "\n".join(register_errors)
    source_errors = validate_source_contract(document)
    assert not source_errors, "\n".join(source_errors)
    validate_fail_closed(document)
    print("Phase 1 candidate boundary validation passed")


if __name__ == "__main__":
    validate()
