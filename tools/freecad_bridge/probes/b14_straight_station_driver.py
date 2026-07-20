"""Drive B14's connected straight-pair creation, edit and persistence path."""

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

from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_TRACK_CONFIGURATION,
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
)
from tools.freecad_bridge.straight_station_recipe import (
    CREATED_LENGTHS_MM,
    EDITED_LENGTHS_MM,
    EXPECTED_CREATED_SEMANTIC_SHA256,
    EXPECTED_EDITED_SEMANTIC_SHA256,
    MANAGER_IDS,
    curve_geometry_contract,
    expected_pair_configs,
    expected_remembered_straight_contract,
    remembered_straight_contract,
    straight_route_analysis_snapshot,
    straight_station_document_snapshot,
    validate_straight_station_snapshot,
)


MODULE_NAME = "tracktemplate_b14_session"
SUCCESS_TEXT = "Curve and straight-track outputs created successfully"

module = sys.modules.get(MODULE_NAME)
if module is None:
    raise RuntimeError("Load B14 before running its straight/station recipe")
document = App.ActiveDocument
if document is None:
    raise RuntimeError("Open a copied B14 plain-line fixture before the recipe")
if not str(document.FileName or ""):
    raise RuntimeError("The straight/station recipe requires a saved copied document")


def _current_rss_mb():
    reader = getattr(module, "_workflow_current_rss_mb", None)
    return float(reader()) if callable(reader) else 0.0


def _history_state(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(name) for name in active_document.UndoNames],
        "redo_names": [str(name) for name in active_document.RedoNames],
        "memory_bytes": int(active_document.UndoRedoMemSize),
    }


def _require_history(state, undo_count, redo_count, label):
    actual = (state["undo_count"], state["redo_count"])
    expected = (int(undo_count), int(redo_count))
    if actual != expected:
        raise RuntimeError(
            "{} produced undo/redo counts {} instead of {}".format(
                label, actual, expected
            )
        )
    if state["undo_mode"] != 1:
        raise RuntimeError("{} found FreeCAD undo mode disabled".format(label))


def _dialog_straight_configs(dialog):
    return [
        dialog._straight_row_config(row)
        for row in range(dialog.straight_table.rowCount())
    ]


def _dialog_contract(dialog):
    return {
        "transition_mm": float(dialog.transition_box.value()),
        "radius_mm": float(dialog.radius_box.value()),
        "angle_degrees": float(dialog.angle_box.value()),
        "main_width_mm": float(dialog.main_width_box.value()),
        "straight_configs": _dialog_straight_configs(dialog),
        "selected_straight_index": int(dialog.straight_table.currentRow()),
        "output_mode": str(dialog.output_mode_box.currentText()),
    }


def _configure_dialog(dialog, target_lengths, initial_configs, use_pair_control):
    initial = _dialog_contract(dialog)
    expected_initial_configs = (
        expected_pair_configs(initial_configs) if initial_configs else []
    )
    if initial["straight_configs"] != expected_initial_configs:
        raise ValueError(
            "The straight/station dialog loaded unexpected initial routes: {}".format(
                initial["straight_configs"]
            )
        )

    dialog.transition_box.setValue(600.0)
    dialog.radius_box.setValue(600.0)
    dialog.angle_box.setValue(90.0)
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

    if use_pair_control:
        dialog.add_connected_pair_button.click()
    if dialog.straight_table.rowCount() != 2:
        raise ValueError("The controlled connection action did not create two rows")
    for index, (manager_id, length) in enumerate(zip(MANAGER_IDS, target_lengths)):
        dialog._straight_configs[index]["manager_id"] = manager_id
        length_box = dialog.straight_table.cellWidget(
            index, dialog.STRAIGHT_COLUMNS["length"]
        )
        if length_box is None:
            raise ValueError("A controlled straight length field is unavailable")
        length_box.setValue(float(length))
    dialog.straight_table.selectRow(0)
    dialog._straight_current_index = 0

    values = dialog.values()
    expected_configs = expected_pair_configs(target_lengths)
    checks = {
        "controlled_pair": values[5] == expected_configs,
        "selected_first_route": values[6] == 0,
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
            "Unexpected straight/station input(s): {}".format(", ".join(failed))
        )
    return {
        "initial": initial,
        "accepted": _dialog_contract(dialog),
        "checks": checks,
        "used_controlled_pair_button": bool(use_pair_control),
    }


def _yes_button(box):
    try:
        choice = QtWidgets.QMessageBox.StandardButton.Yes
    except AttributeError:
        choice = QtWidgets.QMessageBox.Yes
    return box.button(choice)


def _run_generation(name, target_lengths, initial_lengths, use_pair_control):
    active_document = App.ActiveDocument
    if active_document is None:
        raise RuntimeError("{} lost its active document".format(name))
    state = {
        "name": name,
        "target_lengths_mm": list(target_lengths),
        "active": True,
        "seen": set(),
        "curve_dialog_count": 0,
        "replacement_questions": [],
        "success_dialogs": [],
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
                    state["dialog"] = _configure_dialog(
                        widget,
                        target_lengths,
                        initial_lengths,
                        use_pair_control,
                    )
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
                elif SUCCESS_TEXT in record["text"]:
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
    original_builder = module.build_straight_routes
    observations = []

    def observed_builder(straight_configs, curve_alignments):
        routes = original_builder(straight_configs, curve_alignments)
        observations.append(
            straight_route_analysis_snapshot(module, routes, curve_alignments)
        )
        return routes

    module.read_last_dialog_inputs = lambda _document: None
    module.build_straight_routes = observed_builder
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
        module.build_straight_routes = original_builder

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

    if state["monitor_errors"]:
        raise RuntimeError("; ".join(state["monitor_errors"]))
    if state["curve_dialog_count"] != 1:
        raise RuntimeError("{} did not drive exactly one curve dialog".format(name))
    if len(state["replacement_questions"]) != 1:
        raise RuntimeError("{} did not approve exactly one replacement".format(name))
    if len(state["success_dialogs"]) != 1 or state["unexpected_dialogs"]:
        raise RuntimeError("{} did not report one clean success".format(name))
    if len(observations) != 1:
        raise RuntimeError("{} observed {} route builds".format(name, len(observations)))

    analysis = observations[0]
    snapshot = straight_station_document_snapshot(
        module, App.ActiveDocument, analysis
    )
    expected_hash = (
        EXPECTED_CREATED_SEMANTIC_SHA256
        if tuple(target_lengths) == tuple(CREATED_LENGTHS_MM)
        else EXPECTED_EDITED_SEMANTIC_SHA256
    )
    validate_straight_station_snapshot(
        snapshot,
        target_lengths,
        expected_hash=expected_hash or None,
    )
    remembered = remembered_straight_contract(
        module.read_last_dialog_inputs(App.ActiveDocument)
    )
    expected_remembered = expected_remembered_straight_contract(target_lengths)
    if remembered != expected_remembered:
        raise RuntimeError("{} retained unexpected straight inputs".format(name))
    state["analysis"] = analysis
    state["snapshot"] = snapshot
    state["remembered_inputs"] = remembered
    return {
        key: value for key, value in state.items() if key not in ("active", "seen")
    }


def _history_cycle(
    label,
    undo_snapshot,
    redo_snapshot,
    redo_analysis,
    undo_count_after,
    redo_count_after_undo,
):
    active_document = App.ActiveDocument
    before = _history_state(active_document)
    wall_started = time.perf_counter()
    for _index in range(3):
        active_document.undo()
        active_document.recompute()
    after_undo = _history_state(active_document)
    _require_history(
        after_undo,
        undo_count_after,
        redo_count_after_undo,
        "{} undo".format(label),
    )
    if "analysis" in undo_snapshot.get("semantic", {}):
        restored_undo = straight_station_document_snapshot(
            module,
            active_document,
            undo_snapshot["analysis_wrapper"],
        )
        expected_undo_hash = undo_snapshot["semantic_sha256"]
        actual_undo_hash = restored_undo["semantic_sha256"]
    else:
        restored_undo = ordinary_track_document_snapshot(module, active_document)
        expected_undo_hash = undo_snapshot["semantic_sha256"]
        actual_undo_hash = restored_undo["semantic_sha256"]
    if (
        actual_undo_hash != expected_undo_hash
        or restored_undo["semantic"] != undo_snapshot["semantic"]
    ):
        raise RuntimeError("{} undo restored the wrong document".format(label))

    for _index in range(3):
        active_document.redo()
        active_document.recompute()
    after_redo = _history_state(active_document)
    _require_history(
        after_redo,
        undo_count_after + 3,
        redo_count_after_undo - 3,
        "{} redo".format(label),
    )
    restored_redo = straight_station_document_snapshot(
        module, active_document, redo_analysis
    )
    if (
        restored_redo["semantic_sha256"] != redo_snapshot["semantic_sha256"]
        or restored_redo["semantic"] != redo_snapshot["semantic"]
    ):
        raise RuntimeError("{} redo restored the wrong document".format(label))
    return {
        "before": before,
        "after_undo": after_undo,
        "after_redo": after_redo,
        "undo_semantic_sha256": actual_undo_hash,
        "redo_semantic_sha256": restored_redo["semantic_sha256"],
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
    }


def _workflow_snapshot_wrapper(snapshot, analysis):
    result = dict(snapshot)
    result["analysis_wrapper"] = analysis
    return result


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
    "schema_version": 1,
    "source_document": str(document.FileName),
    "initial_base": ordinary_track_snapshot(module, document),
    "initial_document": ordinary_track_document_snapshot(module, document),
    "scenarios": [],
    "history_cycles": [],
}

try:
    result["initial_history"] = _history_state(document)
    _require_history(result["initial_history"], 0, 0, "initial document")

    created = _run_generation(
        "create_controlled_connected_pair",
        CREATED_LENGTHS_MM,
        None,
        True,
    )
    result["scenarios"].append(created)
    created_snapshot = created["snapshot"]
    created_analysis = created["analysis"]

    generation_name = "Generate Version {} curve and straight production templates".format(
        module.MACRO_VERSION_NUMBER
    )
    schedule_name = "Update Version {} production schedule".format(
        module.MACRO_VERSION_NUMBER
    )
    report_name = "Update Version {} material report".format(
        module.MACRO_VERSION_NUMBER
    )
    transaction_stack = [report_name, schedule_name, generation_name]
    created_history = _history_state(App.ActiveDocument)
    _require_history(created_history, 3, 0, "connected-pair creation")
    if created_history["undo_names"] != transaction_stack:
        raise RuntimeError("Connected-pair creation recorded unexpected transactions")
    result["created_history"] = created_history

    result["history_cycles"].append(
        _history_cycle(
            "connected-pair creation",
            result["initial_document"],
            created_snapshot,
            created_analysis,
            0,
            3,
        )
    )

    edited = _run_generation(
        "edit_connected_pair_lengths",
        EDITED_LENGTHS_MM,
        CREATED_LENGTHS_MM,
        False,
    )
    result["scenarios"].append(edited)
    edited_snapshot = edited["snapshot"]
    edited_analysis = edited["analysis"]
    if created_snapshot["semantic_sha256"] == edited_snapshot["semantic_sha256"]:
        raise RuntimeError("Changing both connected lengths did not change semantics")
    if curve_geometry_contract(created_snapshot) != curve_geometry_contract(edited_snapshot):
        raise RuntimeError("A connected-straight length edit changed curve geometry")
    result["curve_geometry_preserved"] = True

    edited_history = _history_state(App.ActiveDocument)
    _require_history(edited_history, 6, 0, "connected-pair length edit")
    if edited_history["undo_names"] != transaction_stack + transaction_stack:
        raise RuntimeError("Connected-pair editing recorded unexpected transactions")
    result["edited_history"] = edited_history

    result["history_cycles"].append(
        _history_cycle(
            "connected-pair length edit",
            _workflow_snapshot_wrapper(created_snapshot, created_analysis),
            edited_snapshot,
            edited_analysis,
            3,
            3,
        )
    )

    document = App.ActiveDocument
    persistence_started = time.perf_counter()
    document.recompute()
    document.save()
    saved_path = str(document.FileName)
    saved_name = str(document.Name)
    App.closeDocument(saved_name)
    document = App.openDocument(saved_path)
    reopened = straight_station_document_snapshot(
        module, document, edited_analysis
    )
    validate_straight_station_snapshot(
        reopened,
        EDITED_LENGTHS_MM,
        expected_hash=EXPECTED_EDITED_SEMANTIC_SHA256 or None,
    )
    if (
        reopened["semantic_sha256"] != edited_snapshot["semantic_sha256"]
        or reopened["semantic"] != edited_snapshot["semantic"]
    ):
        raise RuntimeError("Save/reopen changed the connected straight/station state")
    reopened_history = _history_state(document)
    _require_history(reopened_history, 0, 0, "reopened connected-pair document")
    result["save_reopen"] = {
        "document": str(document.Name),
        "path": saved_path,
        "semantic_sha256": reopened["semantic_sha256"],
        "history": reopened_history,
        "wall_ms": (time.perf_counter() - persistence_started) * 1000.0,
        "objects": len(document.Objects),
    }
finally:
    for key, value in preferences_before.items():
        parameter_group.SetString(key, value)
    result["preference_store_restored"] = all(
        str(parameter_group.GetString(key, "") or "") == value
        for key, value in preferences_before.items()
    )

if not result["preference_store_restored"]:
    raise RuntimeError("The straight/station recipe did not restore bridge preferences")
print(json.dumps(result, sort_keys=True))
