#!/usr/bin/env python3
"""Fail-closed checks for the Phase 1 chair invalidation contract."""

import ast
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import chair_analysis_recipe as chair_recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" /
    "phase1-chair-analysis-invalidation.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "22bac0a48770285e77e8b32a5ed6a69734524618ae144da3c3aa40f809634174"
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
    "observed_inputs",
    "baseline",
    "mutation_matrix",
    "application_cache",
    "presentation_boundary",
    "legacy_defects",
    "successor_acceptance",
    "evidence",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _definitions(tree, name):
    return [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]


def _config_get_keys(function):
    result = set()
    for node in ast.walk(function):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"config", "cfg"}
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            continue
        result.add(node.args[0].value)
    return result


def _group_union(groups):
    values = []
    for group in groups.values():
        values.extend(group)
    return values, set(values)


def validate_contract(contract):
    errors = []
    if not isinstance(contract, dict) or set(contract) != TOP_LEVEL_FIELDS:
        return ["contract top-level fields are invalid"]
    expected = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:chair-analysis-invalidation:1",
        "recorded_on": "2026-07-21",
        "phase": 1,
        "status": (
            "fixed-xo001-input-matrix-characterised-"
            "successor-fixes-not-started"
        ),
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
        "remain open" not in scope["still_open"]
        or "project-cleared" not in scope["provenance_boundary"]
        or "byte-identical" not in scope["product_effect"]
    ):
        errors.append("scope does not fail closed")

    source_state = contract.get("source_state", {})
    if set(source_state) != {"b14", "b15"}:
        errors.append("source_state must contain exactly B14 and B15")
    else:
        for label, version in (("b14", "10.2A8A7B14"),
                               ("b15", "10.2A8A7B15")):
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
        "prerequisite_b4_resolution_signature", "rail_count",
        "timber_count", "execution_boundary",
    }:
        errors.append("scenario fields are invalid")
    elif (
        scenario["crossover_id"] != "XO-001"
        or scenario["host_a_chainage_mm"] != 746.298
        or scenario["rail_count"] != 30
        or scenario["timber_count"] != 86
    ):
        errors.append("controlled scenario changed")

    observed = contract.get("observed_inputs", {})
    if set(observed) != {
        "classification_rule", "direct_config", "settings",
        "rail_records", "timber_records",
    }:
        errors.append("observed input sections are invalid")
    else:
        direct = dict(observed["direct_config"])
        direct.pop("scope", None)
        if direct != {
            key: list(value)
            for key, value in chair_recipe.DIRECT_CONFIG_FIELD_GROUPS.items()
        }:
            errors.append("direct config groups drifted from the shared recipe")

        setting = dict(observed["settings"])
        setting_keys = set(setting.pop("normalised_keys", []))
        expected_setting_groups = {
            key: list(value)
            for key, value in chair_recipe.SETTING_GROUPS.items()
        }
        if setting != expected_setting_groups:
            errors.append("setting groups drifted from the shared recipe")
        values, union = _group_union(expected_setting_groups)
        if len(values) != len(union) or union != setting_keys:
            errors.append("setting groups do not partition the schema")

        for name, helper_groups in (
            ("rail_records", chair_recipe.RAIL_FIELD_GROUPS),
            ("timber_records", chair_recipe.TIMBER_FIELD_GROUPS),
        ):
            record = observed[name]
            schema = set(record.get("schema", []))
            actual_groups = {
                key: value for key, value in record.items() if key != "schema"
            }
            expected_groups = {
                key: list(value) for key, value in helper_groups.items()
            }
            if actual_groups != expected_groups:
                errors.append("{} groups drifted from the shared recipe".format(
                    name
                ))
            values, union = _group_union(expected_groups)
            if len(values) != len(union) or union != schema:
                errors.append("{} groups do not partition the schema".format(
                    name
                ))

    baseline = contract.get("baseline", {})
    if set(baseline) != {
        "status", "geometry_signature", "deterministic_result_sha256",
        "output_without_settings_sha256", "position_count", "finding_count",
    }:
        errors.append("baseline fields are invalid")
    else:
        if baseline["position_count"] != 355 or baseline["finding_count"] != 269:
            errors.append("baseline semantic counts changed")
        for key in (
            "geometry_signature", "deterministic_result_sha256",
            "output_without_settings_sha256",
        ):
            if len(baseline[key]) != 64:
                errors.append("{} is not a SHA-256".format(key))

    matrix = contract.get("mutation_matrix", {})
    if set(matrix) != {"settings", "records"}:
        errors.append("mutation matrix fields are invalid")
    else:
        if set(matrix["settings"]) != set(chair_recipe.SETTING_ALTERNATIVES):
            errors.append("setting mutation matrix is incomplete")
        for key, witness in matrix["settings"].items():
            if set(witness) != {
                "signature_changed", "output_without_settings_changed",
                "position_count", "finding_count",
            }:
                errors.append("{} setting witness fields are invalid".format(key))
        required_records = {
            "config_handing_current_core_unused",
            "config_template_set_omitted",
            "rail_gauge_face_current_core_unused",
            "rail_name_omitted",
            "rail_order_over_invalidates",
            "rail_parent_turnout_omitted",
            "rail_point_below_signature_precision",
            "rail_points_included",
            "rail_source_configuration_omitted",
            "rail_supported_feature_omitted",
            "timber_axes_omitted",
            "timber_centre_included",
            "timber_crossing_suffix_omitted",
            "timber_identifier_omitted",
            "timber_order_over_invalidates",
            "timber_protected_features_omitted",
            "timber_source_configuration_omitted",
            "timber_support_requirements_omitted",
        }
        if set(matrix["records"]) != required_records:
            errors.append("record mutation matrix is incomplete")
        for key, witness in matrix["records"].items():
            if set(witness) != {
                "signature_changed", "output_changed", "output_sha256",
                "position_count", "finding_count", "status",
            } or len(witness.get("output_sha256", "")) != 64:
                errors.append("{} record witness fields are invalid".format(key))

    cache = contract.get("application_cache", {})
    if set(cache) != {
        "witness", "cache_reused", "geometry_signature",
        "actual_stale_output_sha256", "expected_recalculated_output_sha256",
        "stale_result_returned",
    }:
        errors.append("application cache fields are invalid")
    elif not (
        cache["cache_reused"] is True
        and cache["stale_result_returned"] is True
        and cache["actual_stale_output_sha256"]
        != cache["expected_recalculated_output_sha256"]
    ):
        errors.append("stale-cache defect witness is missing")

    presentation = contract.get("presentation_boundary", {})
    if set(presentation) != {
        "common_geometry_signature", "common_output_without_settings_sha256",
        "headless_visibility_authority", "headless_visibility_note", "steps",
    }:
        errors.append("presentation fields are invalid")
    else:
        required_steps = {
            "baseline", "markers_hidden", "markers_restored",
            "protected_shown", "protected_hidden", "footprints_shown",
            "footprints_hidden", "physical_visibility_changed",
            "unresolved_visibility_changed", "cache_disabled",
        }
        if set(presentation["steps"]) != required_steps:
            errors.append("presentation step matrix is incomplete")
        if presentation["headless_visibility_authority"] is not False:
            errors.append("headless visibility must remain non-authoritative")
        for key, step in presentation["steps"].items():
            if set(step) != {
                "cache_reused", "display_cache_reused", "object_count",
                "layers",
            } or "ChairAnalysisDisplay" not in step["layers"]:
                errors.append("{} presentation step is invalid".format(key))

    defects = contract.get("legacy_defects", {})
    if set(defects) != {
        "under_invalidation", "precision_alias", "order_over_invalidation",
        "downstream_setting_over_invalidation", "part_presentation_rebuild",
    }:
        errors.append("legacy-defect set changed")

    successor = contract.get("successor_acceptance", {})
    if set(successor) != {"rules", "remaining_matrix", "migration_gate"}:
        errors.append("successor acceptance fields are invalid")
    else:
        if len(successor["rules"]) != 9 or len(successor["remaining_matrix"]) != 6:
            errors.append("successor acceptance coverage is incomplete")
        joined = " ".join(successor["rules"])
        for required in (
            "exact canonical inputs", "Separate logical-analysis",
            "quantised canonical values", "ordering semantic", "stale cached",
            "presentation-only", "model output", "real GUI", "provenance",
        ):
            if required not in joined:
                errors.append("successor rules omit {!r}".format(required))

    evidence = contract.get("evidence", {})
    if set(evidence) != {
        "report", "fast_validator", "freecad_validator", "shared_recipe",
        "persistence_contract",
    }:
        errors.append("evidence fields are invalid")
    else:
        for label, relative in evidence.items():
            if not (ROOT / relative).is_file():
                errors.append("{} evidence is missing: {}".format(
                    label, relative
                ))
    return errors


def validate_source(contract):
    errors = []
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        path = ROOT / source["path"]
        if _sha256(path) != source["sha256"]:
            errors.append("{} source fingerprint drifted".format(label))

    path = ROOT / contract["source_state"]["b14"]["path"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    signatures = _definitions(tree, "_chair_geometry_signature")
    if len(signatures) != 1:
        return errors + ["chair geometry signature definition count changed"]
    signature_literals = {
        node.value for node in ast.walk(signatures[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    excluded = set(chair_recipe.SETTING_GROUPS[
        "presentation_only_excluded"
    ]) | set(chair_recipe.SETTING_GROUPS["execution_policy_excluded"])
    if not excluded <= signature_literals:
        errors.append("signature exclusion literals changed")
    round_digits = {
        node.args[1].value for node in ast.walk(signatures[0])
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "round"
            and len(node.args) > 1
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, int)
        )
    }
    if round_digits != {5, 8}:
        errors.append("signature precision boundary changed")

    direct_reads = set()
    for name in ("generate_chair_positions", "analyse_chair_position_records"):
        definitions = _definitions(tree, name)
        if len(definitions) != 2:
            errors.append("{} shadow-definition count changed".format(name))
            continue
        for definition in definitions:
            direct_reads.update(_config_get_keys(definition))
    if direct_reads != {"turnout_id", "crossover_id", "template_set_id"}:
        errors.append("direct logical config reads changed")
    return errors


def main():
    errors = []
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        errors.append("chair invalidation contract fingerprint drifted")
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except Exception as error:
        print("Phase 1 chair invalidation validation failed:")
        print("- contract JSON is invalid: {}".format(error))
        raise SystemExit(1)
    errors.extend(validate_contract(contract))
    errors.extend(validate_source(contract))
    if errors:
        print("Phase 1 chair invalidation validation failed:")
        for error in errors:
            print("- {}".format(error))
        raise SystemExit(1)
    print("Phase 1 chair analysis invalidation contract checks passed")


if __name__ == "__main__":
    main()
