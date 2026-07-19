"""Drive B14 plain-line editing, history, validation failure and rollback."""

import copy
import json
import sys
import time

import FreeCAD as App

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets

from tools.freecad_bridge.ordinary_track_edit_recipe import (
    EDIT_RECIPE_SCHEMA_VERSION,
    EXPECTED_TRACK_CONFIGURATION,
    INJECTED_TRANSACTION_ERROR,
    INVALID_ANGLE_DEGREES,
    RIGHT_HAND_ANGLE_DEGREES,
    TRANSACTION_FAILURE_ANGLE_DEGREES,
    expected_remembered_input,
    remembered_input_contract,
    validate_handing_mirror,
    validate_right_hand_snapshot,
)
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
    semantic_sha256,
)


MODULE_NAME = "tracktemplate_b14_session"
SUCCESS_TEXT = "Curve and straight-track outputs created successfully"
ZERO_ANGLE_ERROR = "The total turn angle cannot be zero."

module = sys.modules.get(MODULE_NAME)
if module is None:
    raise RuntimeError("Load B14 before running its plain-line edit recipe")
document = App.ActiveDocument
if document is None:
    raise RuntimeError("Open a copied B14 plain-line fixture before editing")
if not str(document.FileName or ""):
    raise RuntimeError("The plain-line edit recipe requires a saved copied document")


def _current_rss_mb():
    reader = getattr(module, "_workflow_current_rss_mb", None)
    return float(reader()) if callable(reader) else 0.0


def _history_state(active_document):
    """Capture the observable FreeCAD transaction history without mutating it."""
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(name) for name in active_document.UndoNames],
        "redo_names": [str(name) for name in active_document.RedoNames],
        "memory_bytes": int(active_document.UndoRedoMemSize),
    }


def _validate_history_counts(state, expected_undo, expected_redo, label):
    actual = (state["undo_count"], state["redo_count"])
    expected = (int(expected_undo), int(expected_redo))
    if actual != expected:
        raise RuntimeError(
            "{} produced undo/redo counts {} instead of {}: {}".format(
                label, actual, expected, state
            )
        )
    if state["undo_mode"] != 1:
        raise RuntimeError("{} found FreeCAD undo mode disabled".format(label))


def _semantic_without_objects(snapshot, missing_objects):
    semantic = copy.deepcopy(snapshot.get("semantic"))
    if not isinstance(semantic, dict):
        raise ValueError("History comparison requires a semantic snapshot")
    missing = set(missing_objects)
    semantic["objects"] = [
        record
        for record in semantic.get("objects", [])
        if record.get("name") not in missing
    ]
    semantic["groups"] = {
        group_name: [name for name in members if name not in missing]
        for group_name, members in semantic.get("groups", {}).items()
    }
    return semantic


def _run_history_action(
    name,
    action,
    expected_snapshot,
    expected_undo_count,
    expected_redo_count,
    expected_remembered_angle,
    missing_objects=(),
):
    active_document = App.ActiveDocument
    if active_document is None:
        raise RuntimeError("{} lost its active document".format(name))
    before = _history_state(active_document)
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _current_rss_mb()
    action_wall_started = time.perf_counter()
    action_cpu_started = time.process_time()
    if action == "undo":
        active_document.undo()
    elif action == "redo":
        active_document.redo()
    else:
        raise ValueError("Unsupported history action: {}".format(action))
    action_ms = (time.perf_counter() - action_wall_started) * 1000.0
    action_cpu_ms = (time.process_time() - action_cpu_started) * 1000.0
    rss_after_action = _current_rss_mb()
    recompute_started = time.perf_counter()
    active_document.recompute()
    recompute_ms = (time.perf_counter() - recompute_started) * 1000.0
    action_with_recompute_ms = (time.perf_counter() - wall_started) * 1000.0
    action_with_recompute_cpu_ms = (time.process_time() - cpu_started) * 1000.0
    rss_after_recompute = _current_rss_mb()
    after = ordinary_track_document_snapshot(module, active_document)
    expected_semantic = _semantic_without_objects(
        expected_snapshot, missing_objects
    )
    expected_hash = semantic_sha256(expected_semantic)
    if (
        after["semantic_sha256"] != expected_hash
        or after["semantic"] != expected_semantic
    ):
        raise RuntimeError(
            "{} restored semantic SHA-256 {} instead of {}".format(
                name, after["semantic_sha256"], expected_hash
            )
        )
    history = _history_state(active_document)
    _validate_history_counts(
        history, expected_undo_count, expected_redo_count, name
    )
    remembered = remembered_input_contract(
        module.read_last_dialog_inputs(active_document)
    )
    expected_remembered = expected_remembered_input(expected_remembered_angle)
    if remembered != expected_remembered:
        raise RuntimeError(
            "{} changed last-used inputs outside the document transaction".format(name)
        )
    measurement = {
        "action_ms": action_ms,
        "action_process_cpu_ms": action_cpu_ms,
        "action_with_recompute_ms": action_with_recompute_ms,
        "action_with_recompute_process_cpu_ms": action_with_recompute_cpu_ms,
        "validated_wall_ms": (time.perf_counter() - wall_started) * 1000.0,
        "validated_process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
        "rss_before_mb": rss_before,
        "rss_after_action_mb": rss_after_action,
        "rss_after_recompute_mb": rss_after_recompute,
        "rss_after_validation_mb": _current_rss_mb(),
        "recompute_ms": recompute_ms,
        "objects_after": len(active_document.Objects),
    }
    measurement["action_rss_delta_mb"] = rss_after_action - rss_before
    measurement["validated_rss_delta_mb"] = (
        measurement["rss_after_validation_mb"] - rss_before
    )
    return {
        "name": name,
        "action": action,
        "before_history": before,
        "after_history": history,
        "semantic_sha256": after["semantic_sha256"],
        "missing_objects": sorted(missing_objects),
        "remembered_inputs": remembered,
        "measurement": measurement,
    }, after


def _dialog_contract(dialog):
    tracks = [
        dialog._row_config(row) for row in range(dialog.track_table.rowCount())
    ]
    if any(config is None for config in tracks):
        raise ValueError("The B14 curve dialog contains an incomplete track row")
    return {
        "transition_mm": float(dialog.transition_box.value()),
        "radius_mm": float(dialog.radius_box.value()),
        "angle_degrees": float(dialog.angle_box.value()),
        "main_width_mm": float(dialog.main_width_box.value()),
        "track_configs": tracks,
        "output_mode": str(dialog.output_mode_box.currentText()),
    }


def _configure_dialog(dialog, target_angle):
    dialog.transition_box.setValue(600.0)
    dialog.radius_box.setValue(600.0)
    dialog.angle_box.setValue(float(target_angle))
    dialog.main_width_box.setValue(32.0)
    dialog.parallel_count_box.setValue(1)
    dialog._set_parallel_count(1)
    dialog._populate_row(
        0,
        module.clone_track_config(EXPECTED_TRACK_CONFIGURATION[0], 600.0),
    )
    mode_index = dialog.output_mode_box.findText(module.OUTPUT_REPLACE)
    if mode_index < 0:
        raise ValueError("The B14 replace-output choice is unavailable")
    dialog.output_mode_box.setCurrentIndex(mode_index)

    values = dialog.values()
    checks = {
        "straight_routes_disabled": values[5] == [],
        "platforms_disabled": bool(values[7]) and not any(
            config.get("enabled", False) for config in values[7]
        ),
        "formation_disabled": not values[10].get("enabled", False),
        "sectioning_disabled": not values[11].get("enabled", False),
        "template_assembly_disabled": not values[13].get("enabled", False),
        "assembly_labels_disabled": not values[14].get("enabled", False),
        "production_export_disabled": not values[15].get("enabled", False),
        "replace_output": values[17] == module.OUTPUT_REPLACE,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError(
            "Unexpected plain-line edit input(s): {}".format(", ".join(failed))
        )
    return {"accepted": _dialog_contract(dialog), "checks": checks}


def _yes_button(box):
    try:
        choice = QtWidgets.QMessageBox.StandardButton.Yes
    except AttributeError:
        choice = QtWidgets.QMessageBox.Yes
    return box.button(choice)


def _run_scenario(name, target_angle, expected_initial_angle, expected_error=None, inject=False):
    active_document = App.ActiveDocument
    if active_document is None:
        raise RuntimeError("The plain-line edit scenario lost its active document")
    before = ordinary_track_document_snapshot(module, active_document)
    state = {
        "name": name,
        "target_angle_degrees": float(target_angle),
        "expected_initial_angle_degrees": float(expected_initial_angle),
        "active": True,
        "seen": set(),
        "curve_dialog_count": 0,
        "replacement_questions": [],
        "success_dialogs": [],
        "expected_errors": [],
        "unexpected_dialogs": [],
        "monitor_errors": [],
    }

    def monitor():
        if not state["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if not widget.isVisible():
                    continue
                identity = id(widget)
                if identity in state["seen"]:
                    continue
                if isinstance(widget, module.CurveInputDialog):
                    state["seen"].add(identity)
                    initial = _dialog_contract(widget)
                    if initial["angle_degrees"] != float(expected_initial_angle):
                        raise ValueError(
                            "{} loaded angle {} instead of {} from the document".format(
                                name,
                                initial["angle_degrees"],
                                expected_initial_angle,
                            )
                        )
                    configured = _configure_dialog(widget, target_angle)
                    state["initial_dialog"] = initial
                    state["configured_dialog"] = configured
                    state["curve_dialog_count"] += 1
                    widget.accept()
                    continue
                if not isinstance(widget, QtWidgets.QMessageBox):
                    continue
                state["seen"].add(identity)
                record = {
                    "title": str(widget.windowTitle() or ""),
                    "text": str(widget.text() or ""),
                    "informative_text": str(widget.informativeText() or ""),
                    "detailed_text": str(widget.detailedText() or ""),
                }
                yes_button = _yes_button(widget)
                if (
                    "Replace generated templates" in record["title"]
                    and "No object is removed until all requested geometry has passed validation."
                    in record["text"]
                    and yes_button is not None
                ):
                    state["replacement_questions"].append(record)
                    yes_button.click()
                elif expected_error and expected_error in record["text"]:
                    state["expected_errors"].append(record)
                    widget.accept()
                elif expected_error is None and SUCCESS_TEXT in record["text"]:
                    state["success_dialogs"].append(record)
                    widget.accept()
                else:
                    state["unexpected_dialogs"].append(record)
                    widget.accept()
        except Exception as error:
            state["monitor_errors"].append(
                "{}: {}".format(type(error).__name__, error)
            )
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    original_reader = module.read_last_dialog_inputs
    original_tag = module.tag_generated_object
    injection_calls = {"count": 0}

    def injected_tag(*_args, **_kwargs):
        injection_calls["count"] += 1
        raise RuntimeError(INJECTED_TRANSACTION_ERROR)

    module.read_last_dialog_inputs = lambda _document: None
    if inject:
        module.tag_generated_object = injected_tag
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _current_rss_mb()
    objects_before = len(active_document.Objects)
    QtCore.QTimer.singleShot(0, monitor)
    try:
        module.run_macro()
    finally:
        state["active"] = False
        module.read_last_dialog_inputs = original_reader
        module.tag_generated_object = original_tag
    state["measurement"] = {
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
        "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
        "rss_before_mb": rss_before,
        "rss_after_mb": _current_rss_mb(),
        "objects_before": objects_before,
        "objects_after": len(active_document.Objects),
    }
    state["measurement"]["rss_delta_mb"] = (
        state["measurement"]["rss_after_mb"] - rss_before
    )
    state["measurement"]["object_delta"] = (
        state["measurement"]["objects_after"] - objects_before
    )
    state["injected_tag_calls"] = injection_calls["count"]
    state["before_semantic_sha256"] = before["semantic_sha256"]
    after = ordinary_track_document_snapshot(module, active_document)
    state["after_semantic_sha256"] = after["semantic_sha256"]

    if state["monitor_errors"]:
        raise RuntimeError("; ".join(state["monitor_errors"]))
    if state["curve_dialog_count"] != 1:
        raise RuntimeError(
            "{} expected one curve dialog, saw {}".format(
                name, state["curve_dialog_count"]
            )
        )
    if len(state["replacement_questions"]) != 1:
        raise RuntimeError(
            "{} expected one replacement confirmation, saw {}".format(
                name, len(state["replacement_questions"])
            )
        )
    if state["unexpected_dialogs"]:
        raise RuntimeError(
            "{} produced unexpected dialogs: {}".format(
                name, state["unexpected_dialogs"]
            )
        )
    if expected_error is None:
        if len(state["success_dialogs"]) != 1 or state["expected_errors"]:
            raise RuntimeError("{} did not report one clean success".format(name))
        if before["semantic_sha256"] == after["semantic_sha256"]:
            raise RuntimeError("{} did not change plain-line semantics".format(name))
    else:
        if len(state["expected_errors"]) != 1 or state["success_dialogs"]:
            raise RuntimeError("{} did not report the expected failure".format(name))
        if before["semantic_sha256"] != after["semantic_sha256"]:
            raise RuntimeError("{} changed the document despite failure".format(name))
    state["remembered_inputs"] = remembered_input_contract(
        module.read_last_dialog_inputs(active_document)
    )
    if state["remembered_inputs"] != expected_remembered_input(target_angle):
        raise RuntimeError(
            "{} retained unexpected last-used inputs: {}".format(
                name, state["remembered_inputs"]
            )
        )
    if inject and state["injected_tag_calls"] != 1:
        raise RuntimeError("The injected transaction failure did not run exactly once")
    if not inject and state["injected_tag_calls"] != 0:
        raise RuntimeError("A non-injected edit unexpectedly called the failure hook")
    reported_state = {
        key: value for key, value in state.items() if key not in ("active", "seen")
    }
    return reported_state, after


parameter_group = App.ParamGet(module.LAST_INPUTS_PARAMETER_PATH)
preference_keys = (
    module.LAST_INPUTS_PARAMETER_KEY,
    module.LAST_INPUTS_DOCUMENT_MAP_KEY,
    module.MATERIAL_REPORT_PARAMETER_KEY,
)
preferences_before = {
    key: str(parameter_group.GetString(key, "") or "") for key in preference_keys
}
result = {
    "schema_version": EDIT_RECIPE_SCHEMA_VERSION,
    "source_document": str(document.FileName),
    "initial_base": ordinary_track_snapshot(module, document),
    "initial_document": ordinary_track_document_snapshot(module, document),
    "history_actions": [],
    "scenarios": [],
}

try:
    result["initial_history"] = _history_state(document)
    _validate_history_counts(result["initial_history"], 0, 0, "initial document")

    success, right_hand = _run_scenario(
        "replace_left_with_right",
        RIGHT_HAND_ANGLE_DEGREES,
        90.0,
    )
    validate_right_hand_snapshot(right_hand)
    result["scenarios"].append(success)
    result["right_hand_snapshot"] = right_hand
    result["handing_mirror"] = validate_handing_mirror(
        result["initial_base"], right_hand
    )

    generation_transaction_name = (
        "Generate Version {} curve and straight production templates".format(
            module.MACRO_VERSION_NUMBER
        )
    )
    schedule_transaction_name = "Update Version {} production schedule".format(
        module.MACRO_VERSION_NUMBER
    )
    report_transaction_name = "Update Version {} material report".format(
        module.MACRO_VERSION_NUMBER
    )
    transaction_stack = [
        report_transaction_name,
        schedule_transaction_name,
        generation_transaction_name,
    ]
    result["logical_edit_transaction_names"] = transaction_stack
    post_replace_history = _history_state(App.ActiveDocument)
    _validate_history_counts(post_replace_history, 3, 0, "left-to-right replacement")
    if post_replace_history["undo_names"] != transaction_stack:
        raise RuntimeError(
            "Left-to-right replacement recorded unexpected undo transaction names: {}".format(
                post_replace_history["undo_names"]
            )
        )
    result["post_replace_history"] = post_replace_history

    report_object = "RailwayMaterialLengthReport_SET_001"
    schedule_object = "RailwayProductionSchedule_SET_001"
    missing_both_reports = (report_object, schedule_object)
    replacement_history_sequence = (
        (
            "undo_replacement_material_report",
            "undo",
            right_hand,
            2,
            1,
            (report_object,),
        ),
        (
            "undo_replacement_production_schedule",
            "undo",
            right_hand,
            1,
            2,
            missing_both_reports,
        ),
        (
            "undo_replacement_geometry",
            "undo",
            result["initial_document"],
            0,
            3,
            (),
        ),
        (
            "redo_replacement_geometry",
            "redo",
            right_hand,
            1,
            2,
            missing_both_reports,
        ),
        (
            "redo_replacement_production_schedule",
            "redo",
            right_hand,
            2,
            1,
            (report_object,),
        ),
        (
            "redo_replacement_material_report",
            "redo",
            right_hand,
            3,
            0,
            (),
        ),
    )
    restored_right = None
    for (
        history_name,
        history_action,
        expected_snapshot,
        expected_undo_count,
        expected_redo_count,
        missing_objects,
    ) in replacement_history_sequence:
        history_record, restored_right = _run_history_action(
            history_name,
            history_action,
            expected_snapshot,
            expected_undo_count,
            expected_redo_count,
            RIGHT_HAND_ANGLE_DEGREES,
            missing_objects=missing_objects,
        )
        result["history_actions"].append(history_record)
    validate_right_hand_snapshot(restored_right)

    change_back, changed_back_left = _run_scenario(
        "change_right_back_to_left",
        90.0,
        RIGHT_HAND_ANGLE_DEGREES,
    )
    if (
        changed_back_left["semantic_sha256"]
        != result["initial_document"]["semantic_sha256"]
        or changed_back_left["semantic"] != result["initial_document"]["semantic"]
    ):
        raise RuntimeError("Explicit change-back did not restore the initial left-hand state")
    result["scenarios"].append(change_back)
    result["change_back_semantic_sha256"] = changed_back_left["semantic_sha256"]
    post_change_back_history = _history_state(App.ActiveDocument)
    _validate_history_counts(post_change_back_history, 6, 0, "explicit change-back")
    if post_change_back_history["undo_names"] != transaction_stack + transaction_stack:
        raise RuntimeError(
            "Explicit change-back recorded unexpected undo transaction names: {}".format(
                post_change_back_history["undo_names"]
            )
        )
    result["post_change_back_history"] = post_change_back_history

    change_back_history_sequence = (
        (
            "undo_change_back_material_report",
            changed_back_left,
            5,
            1,
            (report_object,),
        ),
        (
            "undo_change_back_production_schedule",
            changed_back_left,
            4,
            2,
            missing_both_reports,
        ),
        (
            "undo_change_back_geometry",
            right_hand,
            3,
            3,
            (),
        ),
    )
    restored_right_after_change_back = None
    for (
        history_name,
        expected_snapshot,
        expected_undo_count,
        expected_redo_count,
        missing_objects,
    ) in change_back_history_sequence:
        history_record, restored_right_after_change_back = _run_history_action(
            history_name,
            "undo",
            expected_snapshot,
            expected_undo_count,
            expected_redo_count,
            90.0,
            missing_objects=missing_objects,
        )
        result["history_actions"].append(history_record)
    validate_right_hand_snapshot(restored_right_after_change_back)

    document = App.ActiveDocument
    persistence_wall_started = time.perf_counter()
    persistence_cpu_started = time.process_time()
    persistence_rss_before = _current_rss_mb()
    recompute_started = time.perf_counter()
    document.recompute()
    recompute_ms = (time.perf_counter() - recompute_started) * 1000.0
    save_started = time.perf_counter()
    document.save()
    save_ms = (time.perf_counter() - save_started) * 1000.0
    saved_path = str(document.FileName)
    saved_name = str(document.Name)
    close_reopen_started = time.perf_counter()
    App.closeDocument(saved_name)
    document = App.openDocument(saved_path)
    close_reopen_ms = (time.perf_counter() - close_reopen_started) * 1000.0
    persistence_measurement = {
        "wall_ms": (time.perf_counter() - persistence_wall_started) * 1000.0,
        "process_cpu_ms": (time.process_time() - persistence_cpu_started) * 1000.0,
        "rss_before_mb": persistence_rss_before,
        "rss_after_mb": _current_rss_mb(),
        "recompute_ms": recompute_ms,
        "save_ms": save_ms,
        "close_reopen_ms": close_reopen_ms,
        "objects_after_reopen": len(document.Objects),
    }
    persistence_measurement["rss_delta_mb"] = (
        persistence_measurement["rss_after_mb"] - persistence_rss_before
    )
    reopened = ordinary_track_document_snapshot(module, document)
    validate_right_hand_snapshot(reopened)
    if reopened["semantic_sha256"] != right_hand["semantic_sha256"]:
        raise RuntimeError("Save/reopen changed the right-hand plain-line state")
    result["right_hand_save_reopen"] = {
        "document": str(document.Name),
        "path": saved_path,
        "semantic_sha256": reopened["semantic_sha256"],
        "measurement": persistence_measurement,
        "history": _history_state(document),
    }
    _validate_history_counts(
        result["right_hand_save_reopen"]["history"],
        0,
        0,
        "reopened right-hand document",
    )

    invalid, invalid_after = _run_scenario(
        "reject_zero_angle_before_transaction",
        INVALID_ANGLE_DEGREES,
        RIGHT_HAND_ANGLE_DEGREES,
        expected_error=ZERO_ANGLE_ERROR,
    )
    validate_right_hand_snapshot(invalid_after)
    result["scenarios"].append(invalid)

    rollback, rollback_after = _run_scenario(
        "abort_replacement_transaction",
        TRANSACTION_FAILURE_ANGLE_DEGREES,
        RIGHT_HAND_ANGLE_DEGREES,
        expected_error=INJECTED_TRANSACTION_ERROR,
        inject=True,
    )
    validate_right_hand_snapshot(rollback_after)
    result["scenarios"].append(rollback)

    document = App.ActiveDocument
    final_name = str(document.Name)
    final_path = str(document.FileName)
    App.closeDocument(final_name)
    document = App.openDocument(final_path)
    final_reopen = ordinary_track_document_snapshot(module, document)
    validate_right_hand_snapshot(final_reopen)
    if final_reopen["semantic_sha256"] != right_hand["semantic_sha256"]:
        raise RuntimeError("Failure handling changed the saved right-hand document")
    result["final_reopen_semantic_sha256"] = final_reopen["semantic_sha256"]
finally:
    for key, value in preferences_before.items():
        parameter_group.SetString(key, value)
    result["preference_store_restored"] = all(
        str(parameter_group.GetString(key, "") or "") == value
        for key, value in preferences_before.items()
    )

if not result["preference_store_restored"]:
    raise RuntimeError("The plain-line edit recipe did not restore bridge preferences")
print(json.dumps(result, sort_keys=True))
