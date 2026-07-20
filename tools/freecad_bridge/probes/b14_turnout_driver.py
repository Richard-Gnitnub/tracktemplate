"""Drive B14's standalone turnout creation, edit and recovery lifecycle."""

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
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
)
from tools.freecad_bridge.turnout_recipe import (
    CREATED_HANDING,
    EDITED_HANDING,
    EXPECTED_CREATED_SEMANTIC_SHA256,
    EXPECTED_EDITED_SEMANTIC_SHA256,
    FLANGEWAY_MM,
    ORIENTATION,
    TRACK_GAUGE_MM,
    TURNOUT_CHAINAGE_MM,
    TURNOUT_ID,
    plain_line_geometry_contract,
    select_turnout_host,
    turnout_document_snapshot,
    validate_turnout_snapshot,
)


MODULE_NAME = "tracktemplate_b14_session"
FAULT_TEXT = "Phase 1 injected turnout edit failure"

module = sys.modules.get(MODULE_NAME)
if module is None:
    raise RuntimeError("Load B14 before running its standalone-turnout recipe")
document = App.ActiveDocument
if document is None:
    raise RuntimeError("Open a copied B14 plain-line fixture before the turnout recipe")
if not str(document.FileName or ""):
    raise RuntimeError("The turnout recipe requires a saved copied document")

manager = getattr(module, "_automation_trackwork_manager", None)
if manager is None or manager.doc is not document:
    raise RuntimeError("Show B14's real turnout manager before running the recipe")


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
                label,
                actual,
                expected,
            )
        )
    if state["undo_mode"] != 1:
        raise RuntimeError("{} found FreeCAD undo mode disabled".format(label))


def _set_combo_text(combo, text):
    index = combo.findText(str(text))
    if index < 0:
        raise RuntimeError("Turnout manager choice is unavailable: {}".format(text))
    combo.setCurrentIndex(index)


def _select_host_and_inputs(handing):
    manager.mode_tabs.setCurrentIndex(0)
    manager.refresh_hosts()
    selection = select_turnout_host(
        manager.hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    manager.host_combo.setCurrentIndex(selection["index"])
    manager.chainage_box.setValue(TURNOUT_CHAINAGE_MM)
    _set_combo_text(manager.orientation_combo, ORIENTATION)
    _set_combo_text(manager.handing_combo, handing)
    manager.gauge_box.setValue(TRACK_GAUGE_MM)
    manager.flangeway_box.setValue(FLANGEWAY_MM)
    manager.timber_outline_box.setChecked(True)
    manager.timber_centre_box.setChecked(False)
    manager.timber_number_box.setChecked(True)
    manager.timber_length_box.setChecked(False)
    manager.datum_box.setChecked(True)
    manager.update_host_summary()
    return selection


def _yes_button(box):
    try:
        choice = QtWidgets.QMessageBox.StandardButton.Yes
    except AttributeError:
        choice = QtWidgets.QMessageBox.Yes
    return box.button(choice)


def _run_with_dialogs(
    label,
    action,
    approve_question=False,
    required_question_text="",
    required_result_text="",
):
    state = {
        "label": label,
        "active": True,
        "seen": set(),
        "questions": [],
        "results": [],
        "unexpected": [],
        "monitor_errors": [],
    }

    def monitor():
        if not state["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                    continue
                identity = id(widget)
                if identity in state["seen"]:
                    continue
                state["seen"].add(identity)
                record = {
                    "title": str(widget.windowTitle() or ""),
                    "text": str(widget.text() or ""),
                    "informative_text": str(widget.informativeText() or ""),
                    "detailed_text": str(widget.detailedText() or ""),
                }
                yes_button = _yes_button(widget)
                if approve_question and yes_button is not None:
                    state["questions"].append(record)
                    yes_button.click()
                elif required_result_text and required_result_text in (
                    record["text"] + "\n" + record["informative_text"]
                ):
                    state["results"].append(record)
                    widget.accept()
                else:
                    state["unexpected"].append(record)
                    widget.accept()
        except Exception as error:
            state["monitor_errors"].append(
                "{}: {}".format(type(error).__name__, error)
            )
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _current_rss_mb()
    objects_before = len(App.ActiveDocument.Objects)
    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        state["active"] = False
    state["measurement"] = {
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
        "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
        "rss_before_mb": rss_before,
        "rss_after_mb": _current_rss_mb(),
        "objects_before": objects_before,
        "objects_after": len(App.ActiveDocument.Objects),
    }
    state["measurement"]["rss_delta_mb"] = (
        state["measurement"]["rss_after_mb"] - rss_before
    )
    state["measurement"]["object_delta"] = (
        state["measurement"]["objects_after"] - objects_before
    )
    if state["monitor_errors"]:
        raise RuntimeError("; ".join(state["monitor_errors"]))
    if state["unexpected"]:
        raise RuntimeError(
            "{} produced unexpected dialogs: {}".format(label, state["unexpected"])
        )
    if approve_question:
        if len(state["questions"]) != 1:
            raise RuntimeError("{} did not show exactly one confirmation".format(label))
        question = state["questions"][0]
        combined = question["text"] + "\n" + question["informative_text"]
        if required_question_text and required_question_text not in combined:
            raise RuntimeError("{} showed the wrong confirmation".format(label))
    elif state["questions"]:
        raise RuntimeError("{} showed an unapproved confirmation".format(label))
    if len(state["results"]) != 1:
        raise RuntimeError("{} did not show exactly one expected result".format(label))
    return {
        key: value
        for key, value in state.items()
        if key not in ("active", "seen")
    }


def _turnout_snapshot(handing, expected_hash):
    snapshot = turnout_document_snapshot(module, App.ActiveDocument)
    validate_turnout_snapshot(
        snapshot,
        handing,
        expected_hash=expected_hash or None,
    )
    return snapshot


def _history_cycle(label, undo_snapshot, redo_snapshot, redo_handing, undo_is_base):
    active_document = App.ActiveDocument
    before = _history_state(active_document)
    wall_started = time.perf_counter()
    active_document.undo()
    active_document.recompute()
    after_undo = _history_state(active_document)
    if undo_is_base:
        restored_undo = ordinary_track_document_snapshot(module, active_document)
    else:
        restored_undo = turnout_document_snapshot(module, active_document)
    if (
        restored_undo["semantic_sha256"] != undo_snapshot["semantic_sha256"]
        or restored_undo["semantic"] != undo_snapshot["semantic"]
    ):
        raise RuntimeError("{} undo restored the wrong document".format(label))

    active_document.redo()
    active_document.recompute()
    after_redo = _history_state(active_document)
    restored_redo = turnout_document_snapshot(module, active_document)
    validate_turnout_snapshot(restored_redo, redo_handing)
    if (
        restored_redo["semantic_sha256"] != redo_snapshot["semantic_sha256"]
        or restored_redo["semantic"] != redo_snapshot["semantic"]
    ):
        raise RuntimeError("{} redo restored the wrong document".format(label))
    return {
        "before": before,
        "after_undo": after_undo,
        "after_redo": after_redo,
        "undo_semantic_sha256": restored_undo["semantic_sha256"],
        "redo_semantic_sha256": restored_redo["semantic_sha256"],
        "wall_ms_including_deep_validation": (
            time.perf_counter() - wall_started
        ) * 1000.0,
    }


initial_base = ordinary_track_snapshot(module, document)
initial_document = ordinary_track_document_snapshot(module, document)
initial_geometry = plain_line_geometry_contract(initial_document["semantic"])
result = {
    "schema_version": 1,
    "source_document": str(document.FileName),
    "initial_base": initial_base,
    "initial_document": initial_document,
    "host_selection": None,
    "actions": [],
    "history_cycles": [],
}

result["initial_history"] = _history_state(document)
_require_history(result["initial_history"], 0, 0, "initial document")

result["host_selection"] = _select_host_and_inputs(CREATED_HANDING)
created_action = _run_with_dialogs(
    "create_left_facing_turnout",
    manager.create_turnout,
    required_result_text="Created {}".format(TURNOUT_ID),
)
created_snapshot = _turnout_snapshot(
    CREATED_HANDING,
    EXPECTED_CREATED_SEMANTIC_SHA256,
)
if plain_line_geometry_contract(
    created_snapshot["semantic"]["document"]
) != initial_geometry:
    raise RuntimeError("Standalone turnout creation changed the host plain-line geometry")
created_action["snapshot"] = created_snapshot
result["actions"].append(created_action)

create_transaction = "Create Version {} REA C10 turnout".format(
    module.MACRO_VERSION_NUMBER
)
created_history = _history_state(App.ActiveDocument)
_require_history(created_history, 1, 0, "turnout creation")
if created_history["undo_names"] != [create_transaction]:
    raise RuntimeError("Turnout creation recorded an unexpected transaction")
result["created_history"] = created_history
result["history_cycles"].append(
    _history_cycle(
        "turnout creation",
        initial_document,
        created_snapshot,
        CREATED_HANDING,
        True,
    )
)
manager.refresh_turnouts(selected_id=TURNOUT_ID)

manager.begin_edit_turnout()
if manager.editing_turnout_id != TURNOUT_ID:
    raise RuntimeError("The turnout manager did not enter edit mode for TO-001")
_set_combo_text(manager.handing_combo, EDITED_HANDING)
manager.update_host_summary()
edited_action = _run_with_dialogs(
    "edit_turnout_handing",
    manager.apply_turnout_edit,
    approve_question=True,
    required_question_text="Handing: {} -> {}".format(
        CREATED_HANDING,
        EDITED_HANDING,
    ),
    required_result_text="Updated {}".format(TURNOUT_ID),
)
edited_snapshot = _turnout_snapshot(
    EDITED_HANDING,
    EXPECTED_EDITED_SEMANTIC_SHA256,
)
if created_snapshot["semantic_sha256"] == edited_snapshot["semantic_sha256"]:
    raise RuntimeError("Changing turnout handing did not change document semantics")
if plain_line_geometry_contract(
    edited_snapshot["semantic"]["document"]
) != initial_geometry:
    raise RuntimeError("Standalone turnout editing changed the host plain-line geometry")
created_role_names = {
    record["role"]: record["name"]
    for record in created_snapshot["semantic"]["turnout_objects"]
}
edited_role_names = {
    record["role"]: record["name"]
    for record in edited_snapshot["semantic"]["turnout_objects"]
}
if created_role_names != edited_role_names:
    raise RuntimeError("Turnout handing edit changed stable object names")
edited_action["snapshot"] = edited_snapshot
result["actions"].append(edited_action)
result["stable_object_names_preserved"] = True

edit_transaction = "Edit Version {} turnout {}".format(
    module.MACRO_VERSION_NUMBER,
    TURNOUT_ID,
)
edited_history = _history_state(App.ActiveDocument)
_require_history(edited_history, 2, 0, "turnout edit")
if edited_history["undo_names"] != [edit_transaction, create_transaction]:
    raise RuntimeError("Turnout editing recorded an unexpected transaction")
result["edited_history"] = edited_history
result["history_cycles"].append(
    _history_cycle(
        "turnout handing edit",
        created_snapshot,
        edited_snapshot,
        EDITED_HANDING,
        False,
    )
)
manager.refresh_turnouts(selected_id=TURNOUT_ID)

_select_host_and_inputs(CREATED_HANDING)
overlap_action = _run_with_dialogs(
    "reject_overlapping_turnout",
    manager.create_turnout,
    required_result_text="overlaps {}".format(TURNOUT_ID),
)
overlap_snapshot = _turnout_snapshot(EDITED_HANDING, EXPECTED_EDITED_SEMANTIC_SHA256)
if overlap_snapshot != edited_snapshot:
    raise RuntimeError("Rejected overlapping turnout changed the document")
overlap_action["semantic_sha256"] = overlap_snapshot["semantic_sha256"]
result["actions"].append(overlap_action)
_require_history(_history_state(App.ActiveDocument), 2, 0, "overlap rejection")

manager.refresh_turnouts(selected_id=TURNOUT_ID)
manager.begin_edit_turnout()
_set_combo_text(manager.handing_combo, CREATED_HANDING)
manager.update_host_summary()
original_tagger = module.tag_generated_object
fault_count = {"calls": 0}


def failing_tagger(*args, **kwargs):
    fault_count["calls"] += 1
    raise RuntimeError(FAULT_TEXT)


module.tag_generated_object = failing_tagger
try:
    fault_action = _run_with_dialogs(
        "abort_injected_turnout_edit",
        manager.apply_turnout_edit,
        approve_question=True,
        required_question_text="Handing: {} -> {}".format(
            EDITED_HANDING,
            CREATED_HANDING,
        ),
        required_result_text=FAULT_TEXT,
    )
finally:
    module.tag_generated_object = original_tagger
if fault_count["calls"] != 1:
    raise RuntimeError("The turnout fault hook did not fail at its first mutation")
fault_snapshot = _turnout_snapshot(EDITED_HANDING, EXPECTED_EDITED_SEMANTIC_SHA256)
if fault_snapshot != edited_snapshot:
    raise RuntimeError("Aborted turnout edit changed the accepted document")
fault_action["fault_tagger_calls"] = fault_count["calls"]
fault_action["semantic_sha256"] = fault_snapshot["semantic_sha256"]
result["actions"].append(fault_action)
_require_history(_history_state(App.ActiveDocument), 2, 0, "injected edit abort")
manager.cancel_turnout_edit()

manager.hide()
manager.close()
module._automation_trackwork_manager = None
document = App.ActiveDocument
persistence_started = time.perf_counter()
document.recompute()
document.save()
saved_path = str(document.FileName)
saved_name = str(document.Name)
App.closeDocument(saved_name)
document = App.openDocument(saved_path)
reopened = turnout_document_snapshot(module, document)
validate_turnout_snapshot(
    reopened,
    EDITED_HANDING,
    expected_hash=EXPECTED_EDITED_SEMANTIC_SHA256 or None,
)
if (
    reopened["semantic_sha256"] != edited_snapshot["semantic_sha256"]
    or reopened["semantic"] != edited_snapshot["semantic"]
):
    raise RuntimeError("Save/reopen changed the standalone-turnout document")
reopened_history = _history_state(document)
_require_history(reopened_history, 0, 0, "reopened turnout document")
result["save_reopen"] = {
    "document": str(document.Name),
    "path": saved_path,
    "semantic_sha256": reopened["semantic_sha256"],
    "history": reopened_history,
    "objects": len(document.Objects),
    "wall_ms_including_deep_validation": (
        time.perf_counter() - persistence_started
    ) * 1000.0,
}

print(json.dumps(result, sort_keys=True))
