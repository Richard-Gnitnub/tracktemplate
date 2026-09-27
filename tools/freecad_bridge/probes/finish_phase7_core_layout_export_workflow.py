"""Validate and report one routed core-layout export GUI lifecycle."""

import copy
import json
import pathlib
import re


_PHASE7_VOLATILE_KEYS = frozenset({
    "close_reopen_ms",
    "process_cpu_ms",
    "recompute_ms",
    "rss_after_mb",
    "rss_before_mb",
    "rss_delta_mb",
    "save_ms",
    "wall_ms",
})
_PHASE7_PATH_BOUND_DIGEST_KEYS = frozenset({
    "after_semantic_sha256",
    "before_semantic_sha256",
})
_PHASE7_EXPECTED_SCENARIOS = (
    "create_time_export_success",
    "create_time_export_final_task_failure",
)


def _normalise_core_layout_export_recipe(
    recipe,
    expected_source_document=None,
):
    """Remove only process and copied-run volatility from one recipe."""
    if not isinstance(recipe, dict):
        raise RuntimeError("The core-layout export driver returned no mapping.")
    if recipe.get("schema_version") != 1:
        raise RuntimeError("The core-layout export recipe schema drifted.")
    scenarios = recipe.get("scenarios")
    names = tuple(
        item.get("name") if isinstance(item, dict) else None
        for item in scenarios or ()
    )
    if names != _PHASE7_EXPECTED_SCENARIOS:
        raise RuntimeError(
            "The core-layout export scenario sequence drifted: {!r}.".format(
                names
            )
        )
    if recipe.get("preference_store_restored") is not True:
        raise RuntimeError(
            "The core-layout export recipe did not restore its preferences."
        )

    source_document = pathlib.Path(str(recipe.get("source_document") or ""))
    if not source_document.is_absolute():
        raise RuntimeError("The core-layout export recipe has no run document.")
    if (
        expected_source_document is not None
        and source_document.resolve()
        != pathlib.Path(str(expected_source_document)).resolve()
    ):
        raise RuntimeError(
            "The core-layout export recipe used an unexpected run document."
        )
    run_directory = str(source_document.parent)
    contract = copy.deepcopy(recipe)
    for scenario in contract["scenarios"]:
        for key in _PHASE7_PATH_BOUND_DIGEST_KEYS:
            scenario.pop(key, None)

    def normalise(value):
        if isinstance(value, dict):
            return {
                key: normalise(item)
                for key, item in value.items()
                if key not in _PHASE7_VOLATILE_KEYS
            }
        if isinstance(value, list):
            return [normalise(item) for item in value]
        if isinstance(value, str):
            result = value.replace(run_directory, "<run-directory>")
            result = re.sub(
                r"RailwayPreflight_[0-9a-fA-F]+",
                "RailwayPreflight_<generated-id>",
                result,
            )
            return re.sub(
                r"_tmp_[0-9a-fA-F]+",
                "_tmp_<generated-id>",
                result,
            )
        return copy.deepcopy(value)

    return normalise(contract)


def _validate_core_layout_export_recipe_normaliser():
    """Prove root volatility is ignored without masking output drift."""
    def fixture(run_directory, raw_digest):
        return {
            "schema_version": 1,
            "source_document": "{}/workflow.FCStd".format(run_directory),
            "scenarios": [
                {
                    "name": name,
                    "before_semantic_sha256": "{}-before".format(raw_digest),
                    "after_semantic_sha256": "{}-after".format(raw_digest),
                    "normalised_after_semantic_sha256": "stable-document",
                    "configured_dialog": {
                        "output_directory": "{}/{}".format(
                            run_directory,
                            name,
                        ),
                    },
                    "measurement": {"wall_ms": 1.0},
                }
                for name in _PHASE7_EXPECTED_SCENARIOS
            ],
            "success_output": {
                "after_semantic_sha256": "retained-non-scenario-digest",
                "logical_sha256": "stable-output",
            },
            "failure_output": {"content_sha256": "stable-partial-output"},
            "preference_store_restored": True,
        }

    legacy = fixture("/tmp/phase7-legacy", "legacy-path-bound")
    modular = fixture("/tmp/phase7-modular", "modular-path-bound")
    expected = _normalise_core_layout_export_recipe(legacy)
    if expected != _normalise_core_layout_export_recipe(modular):
        raise RuntimeError(
            "Core-layout export recipe root normalisation regressed."
        )

    semantic_change = copy.deepcopy(modular)
    semantic_change["scenarios"][0][
        "normalised_after_semantic_sha256"
    ] = "changed-document"
    if expected == _normalise_core_layout_export_recipe(semantic_change):
        raise RuntimeError(
            "Core-layout export recipe normalisation masked semantic drift."
        )

    output_change = copy.deepcopy(modular)
    output_change["success_output"]["logical_sha256"] = "changed-output"
    if expected == _normalise_core_layout_export_recipe(output_change):
        raise RuntimeError(
            "Core-layout export recipe normalisation masked output drift."
        )
    digest_name_change = copy.deepcopy(modular)
    digest_name_change["success_output"][
        "after_semantic_sha256"
    ] = "changed-non-scenario-digest"
    if expected == _normalise_core_layout_export_recipe(digest_name_change):
        raise RuntimeError(
            "Core-layout export recipe removed a non-scenario digest."
        )
    try:
        _normalise_core_layout_export_recipe(
            modular,
            "/tmp/phase7-other/workflow.FCStd",
        )
    except RuntimeError as error:
        if "unexpected run document" not in str(error):
            raise
    else:
        raise RuntimeError(
            "Core-layout export recipe accepted a forged run root."
        )


_validate_core_layout_export_recipe_normaliser()
if "_PHASE3_SESSION" not in globals() and __name__ == "__main__":
    print("Phase 7 core-layout export recipe normaliser validation passed")
    raise SystemExit(0)


_PHASE7_REQUIRED_CONTEXT_NAMES = (
    "TRACKTEMPLATE_WORKFLOW_RESULT",
    "TRACKTEMPLATE_EXPECTED_WORKFLOW_DOCUMENT",
    "_PHASE3_API",
    "_PHASE3_BINDING_RECORDS_BEFORE",
    "_PHASE3_BINDINGS_BEFORE",
    "_PHASE3_LAUNCHER_SHA256",
    "_PHASE3_PRODUCT_COMPOSITION",
    "_PHASE3_QUALIFICATION",
    "_PHASE3_ROUTE",
    "_PHASE3_ROUTING",
    "_PHASE3_SESSION",
    "_PHASE3_WORKFLOW_MODULE_NAME",
    "_PHASE7_EXPORT_BINDING_BEFORE",
    "module",
)
_phase7_context = globals()
_phase7_missing_context = sorted(
    name for name in _PHASE7_REQUIRED_CONTEXT_NAMES if name not in _phase7_context
)
if _phase7_missing_context:
    raise RuntimeError(
        "The embedded core-layout export context is incomplete: {}.".format(
            ", ".join(_phase7_missing_context)
        )
    )

workflow_result = _phase7_context["TRACKTEMPLATE_WORKFLOW_RESULT"]
expected_workflow_document = _phase7_context[
    "TRACKTEMPLATE_EXPECTED_WORKFLOW_DOCUMENT"
]
phase3_api = _phase7_context["_PHASE3_API"]
phase3_binding_records_before = _phase7_context[
    "_PHASE3_BINDING_RECORDS_BEFORE"
]
phase3_bindings_before = _phase7_context["_PHASE3_BINDINGS_BEFORE"]
phase3_launcher_sha256 = _phase7_context["_PHASE3_LAUNCHER_SHA256"]
phase3_product_composition = _phase7_context["_PHASE3_PRODUCT_COMPOSITION"]
phase3_qualification = _phase7_context["_PHASE3_QUALIFICATION"]
phase3_route = _phase7_context["_PHASE3_ROUTE"]
phase3_routing = _phase7_context["_PHASE3_ROUTING"]
phase3_session = _phase7_context["_PHASE3_SESSION"]
phase3_workflow_module_name = _phase7_context[
    "_PHASE3_WORKFLOW_MODULE_NAME"
]
phase7_export_binding_before = _phase7_context[
    "_PHASE7_EXPORT_BINDING_BEFORE"
]
workflow_module = _phase7_context["module"]

if not isinstance(workflow_result, dict):
    raise RuntimeError("The embedded core-layout export workflow returned no result.")
if workflow_module is not phase3_session.module:
    raise RuntimeError("The export driver did not use the routed B16 module.")

phase7_export_binding_after = phase3_session.module.__dict__.get(
    "run_production_export"
)
if phase7_export_binding_after is not phase7_export_binding_before:
    raise RuntimeError("The export driver did not restore its routed binding.")

phase3_bindings_after = {
    name: phase3_session.module.__dict__[name]
    for name in phase3_routing["function_names"]
}
phase3_changed_bindings = sorted(
    name
    for name in phase3_bindings_before
    if phase3_bindings_after[name] is not phase3_bindings_before[name]
)
if phase3_changed_bindings:
    raise RuntimeError(
        "The workflow changed routed calculation bindings: {}.".format(
            ", ".join(phase3_changed_bindings)
        )
    )

if phase3_product_composition:
    phase3_revalidated_routing = phase3_session.routing_record()
    phase3_active_route_after = "modular"
    phase7_export_routing = phase3_session.core_layout_export_routing_record()
    if (
        phase7_export_routing.get("contract_id")
        != "tracktemplate:phase7:core-layout-export:1"
        or phase7_export_routing.get("route") != "modular"
        or phase7_export_routing.get("command_name")
        != "run_core_layout_export"
        or phase7_export_routing.get("host_binding_name")
        != "run_production_export"
        or phase7_export_routing.get("mixed_route") is not False
    ):
        raise RuntimeError("The modular core-layout export route drifted.")
else:
    phase3_revalidated_routing = phase3_session.apply_route(phase3_route)
    phase3_active_route_after = phase3_session.active_route
    if (
        not callable(phase7_export_binding_after)
        or getattr(phase7_export_binding_after, "__globals__", None)
        is not phase3_session.module.__dict__
        or getattr(phase7_export_binding_after, "__name__", "")
        != "run_production_export"
    ):
        raise RuntimeError("The legacy core-layout export oracle drifted.")
    phase7_export_routing = {
        "schema_version": 1,
        "route": "legacy",
        "comparison_route_available": True,
        "command_name": "run_production_export",
        "host_binding_name": "run_production_export",
        "workflow_version": str(phase3_session.module.MACRO_VERSION_NUMBER),
        "workflow_source_sha256": str(phase3_session.source_sha256),
        "mixed_route": False,
    }

if phase3_revalidated_routing != phase3_routing:
    raise RuntimeError("The calculation route record drifted after the workflow.")

phase7_recipe_contract = _normalise_core_layout_export_recipe(
    workflow_result,
    expected_workflow_document,
)
phase7_workflow_report = {
    "schema_version": 1,
    "development_checkpoint": str(phase3_api.DEVELOPMENT_CHECKPOINT),
    "matched_profile_id": str(
        phase3_qualification["compatibility_evaluation"][
            "matched_profile_id"
        ]
    ),
    "routing": phase3_routing,
    "active_route_after_workflow": phase3_active_route_after,
    "core_layout_export_routing": phase7_export_routing,
    "core_layout_export_binding_identity_preserved": (
        phase7_export_binding_after is phase7_export_binding_before
    ),
    "workflow_module": phase3_workflow_module_name,
    "workflow_version": str(phase3_session.module.MACRO_VERSION_NUMBER),
    "launcher_sha256": phase3_launcher_sha256,
    "binding_records_before": phase3_binding_records_before,
    "binding_identity_preserved": not phase3_changed_bindings,
    "recipe": workflow_result,
    "recipe_contract": phase7_recipe_contract,
}
print(json.dumps(phase7_workflow_report, sort_keys=True))
