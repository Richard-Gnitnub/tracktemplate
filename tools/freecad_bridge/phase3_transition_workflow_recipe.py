"""Stable comparison contract for the Phase 3 routed workflow oracle."""

import copy

from tools.semantic_compare import compare_structures


LEGACY_ROUTE = "legacy"
MODULAR_ROUTE = "modular"
ROUTES = (LEGACY_ROUTE, MODULAR_ROUTE)

PLAIN_LINE_EDIT = "plain-line-edit"
CONNECTED_STRAIGHT = "connected-straight"
WORKFLOWS = (PLAIN_LINE_EDIT, CONNECTED_STRAIGHT)

DRIVER_PATHS = {
    PLAIN_LINE_EDIT: "tools/freecad_bridge/probes/b14_ordinary_edit_driver.py",
    CONNECTED_STRAIGHT: "tools/freecad_bridge/probes/b14_straight_station_driver.py",
}

EXPECTED_SCHEMA_VERSIONS = {
    PLAIN_LINE_EDIT: 2,
    CONNECTED_STRAIGHT: 1,
}

EXPECTED_SCENARIOS = {
    PLAIN_LINE_EDIT: (
        "replace_left_with_right",
        "change_right_back_to_left",
        "reject_zero_angle_before_transaction",
        "abort_replacement_transaction",
    ),
    CONNECTED_STRAIGHT: (
        "create_controlled_connected_pair",
        "edit_connected_pair_lengths",
    ),
}

EXPECTED_PLAIN_LINE_HISTORY_ACTIONS = (
    "undo_replacement_material_report",
    "undo_replacement_production_schedule",
    "undo_replacement_geometry",
    "redo_replacement_geometry",
    "redo_replacement_production_schedule",
    "redo_replacement_material_report",
    "undo_change_back_material_report",
    "undo_change_back_production_schedule",
    "undo_change_back_geometry",
)

# These fields are development-harness observations rather than workflow
# semantics. Every other value, including semantic hashes, dialog records,
# history counts/names, object counts, persistence records and failure results,
# remains in the exact legacy/modular comparison.
VOLATILE_RECIPE_FIELDS = frozenset({
    "measurement",
    "memory_bytes",
    "path",
    "source_document",
    "wall_ms",
})


def _pop_field(mapping, key, context):
    if not isinstance(mapping, dict) or key not in mapping:
        raise ValueError(
            "The Phase 3 workflow is missing volatile field {}.{}.".format(
                context,
                key,
            )
        )
    mapping.pop(key)


def _remove_history_memory(mapping, context):
    _pop_field(mapping, "memory_bytes", context)


def _plain_line_equivalence_contract(recipe_result):
    result = copy.deepcopy(recipe_result)
    _pop_field(result, "source_document", "recipe")
    for index, scenario in enumerate(result["scenarios"]):
        _pop_field(scenario, "measurement", "scenarios[{}]".format(index))
    history_actions = result.get("history_actions")
    if not isinstance(history_actions, list):
        raise ValueError("The plain-line recipe has no history action list.")
    names = tuple(
        item.get("name") if isinstance(item, dict) else None
        for item in history_actions
    )
    if names != EXPECTED_PLAIN_LINE_HISTORY_ACTIONS:
        raise ValueError("The plain-line history action sequence drifted.")
    for index, action in enumerate(history_actions):
        context = "history_actions[{}]".format(index)
        _pop_field(action, "measurement", context)
        _remove_history_memory(action.get("before_history"), context + ".before_history")
        _remove_history_memory(action.get("after_history"), context + ".after_history")
    for key in (
        "initial_history",
        "post_replace_history",
        "post_change_back_history",
    ):
        _remove_history_memory(result.get(key), key)
    persistence = result.get("right_hand_save_reopen")
    _pop_field(persistence, "measurement", "right_hand_save_reopen")
    _pop_field(persistence, "path", "right_hand_save_reopen")
    _remove_history_memory(
        persistence.get("history"),
        "right_hand_save_reopen.history",
    )
    return result


def _connected_straight_equivalence_contract(recipe_result):
    result = copy.deepcopy(recipe_result)
    _pop_field(result, "source_document", "recipe")
    for index, scenario in enumerate(result["scenarios"]):
        _pop_field(scenario, "measurement", "scenarios[{}]".format(index))
    for key in ("initial_history", "created_history", "edited_history"):
        _remove_history_memory(result.get(key), key)
    history_cycles = result.get("history_cycles")
    if not isinstance(history_cycles, list) or len(history_cycles) != 2:
        raise ValueError("The connected-straight history-cycle sequence drifted.")
    for index, cycle in enumerate(history_cycles):
        context = "history_cycles[{}]".format(index)
        _pop_field(cycle, "wall_ms", context)
        for key in ("before", "after_undo", "after_redo"):
            _remove_history_memory(cycle.get(key), context + "." + key)
    persistence = result.get("save_reopen")
    _pop_field(persistence, "path", "save_reopen")
    _pop_field(persistence, "wall_ms", "save_reopen")
    _remove_history_memory(persistence.get("history"), "save_reopen.history")
    return result


def workflow_equivalence_contract(workflow, recipe_result):
    """Return the exact route-independent workflow contract.

    The legacy Phase 1 drivers remain the behavioural oracle. This function
    removes only the five declared host/process-volatility fields and fails
    closed if the expected workflow identity or successful cleanup drifts.
    """
    if workflow not in WORKFLOWS:
        raise ValueError("Unknown Phase 3 workflow {!r}.".format(workflow))
    if not isinstance(recipe_result, dict):
        raise ValueError("The Phase 3 workflow result must be a mapping.")
    if recipe_result.get("schema_version") != EXPECTED_SCHEMA_VERSIONS[workflow]:
        raise ValueError("The {} recipe schema drifted.".format(workflow))
    scenarios = recipe_result.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("The {} recipe has no scenario list.".format(workflow))
    scenario_names = tuple(
        item.get("name") if isinstance(item, dict) else None
        for item in scenarios
    )
    if scenario_names != EXPECTED_SCENARIOS[workflow]:
        raise ValueError(
            "The {} scenario sequence drifted: {!r}.".format(
                workflow,
                scenario_names,
            )
        )
    if recipe_result.get("preference_store_restored") is not True:
        raise ValueError(
            "The {} recipe did not restore its isolated preferences.".format(
                workflow
            )
        )
    if workflow == PLAIN_LINE_EDIT:
        return _plain_line_equivalence_contract(recipe_result)
    return _connected_straight_equivalence_contract(recipe_result)


def compare_workflow_routes(workflow, legacy_result, modular_result):
    """Compare complete normalised legacy and modular workflow results."""
    legacy_contract = workflow_equivalence_contract(workflow, legacy_result)
    modular_contract = workflow_equivalence_contract(workflow, modular_result)
    return compare_structures(legacy_contract, modular_contract)
