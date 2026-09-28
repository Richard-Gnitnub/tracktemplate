#!/usr/bin/env python3
"""Prove bounded B16 turnout creation, edit and recovery in the inherited GUI."""

import argparse
import ast
import datetime
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".devtools" / "freecad-cli" / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


DEFAULT_PORT = 19875
B15_PATH = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
CONTRACT_PATH = ROOT / "reference/contracts/phase1-transition-pilot.json"
LOADER_PATH = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = ROOT / "benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs"
SOURCE_PATHS = (
    ROOT / "AdvancedTurnout.FCMacro",
    B15_PATH,
    ROOT / "TrackTemplate.FCMacro",
    ROOT / "reference/contracts/phase1-compatibility.json",
    CONTRACT_PATH,
    ROOT / "tools/phase3_transition_pilot.py",
    ROOT / "tools/freecad_bridge/run-isolated",
    ROOT / "tools/freecad_bridge/launch-freecad",
    ROOT / "tools/freecad_bridge/orchestration.py",
    ROOT / "tools/freecad_bridge/turnout_recipe.py",
    LOADER_PATH,
    *sorted((ROOT / "tracktemplate").rglob("*.py")),
    pathlib.Path(__file__).resolve(),
    ROOT / "tools/freecad_bridge/run-phase8-turnout-toe-gui",
)


GUI_PROBE = r'''
import json
import pathlib
import sys

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge.turnout_recipe import (
    CREATED_HANDING,
    EDITED_HANDING,
    EXPECTED_TURNOUT_ROLES,
    TURNOUT_CHAINAGE_MM,
    TURNOUT_ID,
    _expected_turnout_record_contract,
    _production_record_contract,
    plain_line_geometry_contract,
    select_turnout_host,
    turnout_document_snapshot,
)
from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_PRODUCTION_RECORDS,
    ordinary_track_document_state,
)
from tracktemplate.application.turnout_edit import (
    turnout_configuration_change_summary as selected_summary,
)
from tracktemplate.compatibility.transition_workflow import (
    _TurnoutConfigurationSummaryAdapter,
)
from tracktemplate.domain import turnout as domain_turnout

module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
selected = domain_turnout.turnout_valid_toe_range
selected_interval = domain_turnout.turnout_host_station_interval
selected_summary_adapter = module.turnout_configuration_change_summary
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if module.turnout_valid_toe_range is not selected:
    raise RuntimeError("The B16 turnout toe binding is not the selected domain function")
if module.turnout_host_station_interval is not selected_interval:
    raise RuntimeError("The B16 turnout interval binding is not the selected domain function")
if (not isinstance(selected_summary_adapter, _TurnoutConfigurationSummaryAdapter)
        or selected_summary_adapter.calculation is not selected_summary
        or selected_summary_adapter.host_globals is not module.__dict__):
    raise RuntimeError("The B16 turnout edit summary binding is not the selected application function")
if (routing.get("route") != "modular" or routing.get("schema_version") != 16
        or len(routing.get("function_names", ())) != 25
        or len(routing.get("caller_names", ())) != 40):
    raise RuntimeError("The inherited B16 public routing envelope changed")

callers = {
    "_build_curve_inheriting_c10_turnout": module._build_curve_inheriting_c10_turnout,
    "_crossover_solve_toe_b": module._crossover_solve_toe_b,
    "solve_rea_c10_crossover_geometry": module.solve_rea_c10_crossover_geometry,
    "CrossoverManagerPanel.update_chainage_range": module.CrossoverManagerPanel.update_chainage_range,
    "TurnoutManagerDialog.update_host_summary": module.TurnoutManagerDialog.update_host_summary,
}
for name, caller in callers.items():
    if (caller.__globals__ is not module.__dict__
            or caller.__globals__["turnout_valid_toe_range"] is not selected
            or "turnout_valid_toe_range" not in caller.__code__.co_names):
        raise RuntimeError("The inherited turnout caller is not routed: " + name)
interval_callers = {
    "_turnout_find_overlap": module._turnout_find_overlap,
    "_build_curve_inheriting_c10_turnout": module._build_curve_inheriting_c10_turnout,
    "build_turnout_host_integration": module.build_turnout_host_integration,
    "solve_rea_c10_crossover_geometry": module.solve_rea_c10_crossover_geometry,
}
for name, caller in interval_callers.items():
    if (caller.__globals__ is not module.__dict__
            or caller.__globals__["turnout_host_station_interval"] is not selected_interval
            or "turnout_host_station_interval" not in caller.__code__.co_names):
        raise RuntimeError("The inherited interval caller is not routed: " + name)
summary_callers = {
    "edit_curve_inheriting_c10_turnout": module.edit_curve_inheriting_c10_turnout,
    "TurnoutManagerDialog.update_host_summary": module.TurnoutManagerDialog.update_host_summary,
    "TurnoutManagerDialog.apply_turnout_edit": module.TurnoutManagerDialog.apply_turnout_edit,
}
for name, caller in summary_callers.items():
    if (caller.__globals__ is not module.__dict__
            or caller.__globals__["turnout_configuration_change_summary"]
            is not selected_summary_adapter
            or "turnout_configuration_change_summary" not in caller.__code__.co_names):
        raise RuntimeError("The inherited turnout edit caller is not routed: " + name)

document = App.ActiveDocument
if document is None or not document.FileName:
    raise RuntimeError("Open the copied saved fixture before the turnout GUI probe")
initial_host_geometry = plain_line_geometry_contract(
    ordinary_track_document_state(module, document)
)
manager = module.TurnoutManagerDialog(document)
manager.show()
QtWidgets.QApplication.processEvents()
selection = select_turnout_host(
    manager.hosts, module.object_string_property, module._integer_object_property
)
manager.host_combo.setCurrentIndex(selection["index"])
host = manager.hosts[selection["index"]]
panel = manager.crossover_panel
panel.refresh_hosts()
panel_matches = [
    index for index, candidate in enumerate(panel.hosts)
    if candidate.Name == host.Name
]
if len(panel_matches) != 1:
    raise RuntimeError("The crossover panel did not retain the selected host")
panel.host_a_combo.setCurrentIndex(panel_matches[0])

def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The inherited GUI choice is absent: " + value)
    combo.setCurrentIndex(index)

def observed_calls(action):
    calls = []
    active = []
    def profile(frame, event, value):
        if frame.f_code is selected.__code__:
            if event == "call":
                item = {
                    "host_length": frame.f_locals["host_length"],
                    "dimensions": {
                        key: frame.f_locals["dimensions"][key]
                        for key in ("module_start_x", "module_end_x")
                    },
                    "orientation": str(frame.f_locals["orientation"]),
                }
                calls.append(item)
                active.append(item)
            elif event == "return" and active:
                item = active.pop()
                item["returned"] = list(value) if value is not None else None
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        action()
    finally:
        sys.setprofile(previous)
    return calls

def require_call(calls, total, dimensions, orientation, expected):
    matching = [
        call for call in calls
        if call["host_length"] == total
        and call["dimensions"] == {
            key: dimensions[key] for key in ("module_start_x", "module_end_x")
        }
        and call["orientation"] == orientation
        and call.get("returned") == list(expected)
    ]
    if not matching:
        raise RuntimeError("The GUI method did not call and return from the selected domain function")

def require_range(box, expected):
    actual = [float(box.minimum()), float(box.maximum())]
    tolerance = 0.5 * 10.0 ** (-int(box.decimals())) + 1.0e-7
    if any(abs(a - b) > tolerance for a, b in zip(actual, expected)):
        raise RuntimeError("The inherited GUI range differs from the domain range: {} != {}".format(actual, expected))
    return actual

def observed_interval_calls(action):
    calls = []
    active = []
    def profile(frame, event, value):
        if frame.f_code is selected_interval.__code__:
            if event == "call":
                item = {
                    "caller": frame.f_back.f_code.co_name,
                    "toe_chainage": float(frame.f_locals["toe_chainage"]),
                    "dimensions": {
                        key: frame.f_locals["dimensions"][key]
                        for key in ("module_start_x", "module_end_x")
                    },
                    "orientation": str(frame.f_locals["orientation"]),
                }
                calls.append(item)
                active.append(item)
            elif event == "return" and active:
                active.pop()["returned"] = list(value)
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        result = action()
    finally:
        sys.setprofile(previous)
    return result, calls

def run_result_dialog(action, expected_text):
    state = {"active": True, "seen": set(), "matches": [], "unexpected": []}
    def monitor():
        if not state["active"]:
            return
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                continue
            identity = id(widget)
            if identity in state["seen"]:
                continue
            state["seen"].add(identity)
            message = "{}\n{}".format(widget.text(), widget.informativeText())
            if expected_text in message:
                state["matches"].append(message)
            else:
                state["unexpected"].append(message)
            widget.accept()
        QtCore.QTimer.singleShot(25, monitor)
    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        state["active"] = False
    if state["unexpected"] or len(state["matches"]) != 1:
        raise RuntimeError("The turnout action showed unexpected dialogs: {}".format(state))
    return state["matches"][0]

def run_edit_dialog(action, question_text, result_text):
    state = {
        "active": True, "seen": set(), "questions": [],
        "results": [], "unexpected": [], "monitor_errors": [],
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
                message = "{}\n{}".format(widget.text(), widget.informativeText())
                yes_button = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                if yes_button is not None:
                    state["questions"].append(message)
                    yes_button.click()
                elif result_text in message:
                    state["results"].append(message)
                    widget.accept()
                else:
                    state["unexpected"].append(message)
                    widget.accept()
        except Exception as error:
            state["monitor_errors"].append("{}: {}".format(type(error).__name__, error))
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)
    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        state["active"] = False
    if (state["monitor_errors"] or state["unexpected"]
            or len(state["questions"]) != 1
            or question_text not in state["questions"][0]
            or len(state["results"]) != 1):
        raise RuntimeError("The turnout edit showed unexpected dialogs: {}".format(state))
    return {key: value for key, value in state.items() if key not in ("active", "seen")}

def observed_summary_calls(action):
    calls = []
    active = []
    caller_codes = {caller.__code__: name for name, caller in summary_callers.items()}
    def profile(frame, event, value):
        if frame.f_code is not selected_summary.__code__:
            return
        if event == "call":
            inherited_caller = None
            parent = frame.f_back
            while parent is not None:
                inherited_caller = caller_codes.get(parent.f_code)
                if inherited_caller is not None:
                    break
                parent = parent.f_back
            old_config = frame.f_locals["old_config"]
            new_config = frame.f_locals["new_config"]
            item = {
                "inherited_caller": inherited_caller,
                "old_handing": old_config.get("handing"),
                "new_handing": new_config.get("handing"),
            }
            calls.append(item)
            active.append(item)
        elif event == "return" and active:
            active.pop()["returned"] = list(value)
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        result = action()
    finally:
        sys.setprofile(previous)
    return result, calls

def history_state(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(name) for name in active_document.UndoNames],
        "redo_names": [str(name) for name in active_document.RedoNames],
    }

def require_history(state, undo_count, redo_count, undo_names, label):
    if (state["undo_mode"] != 1
            or [state["undo_count"], state["redo_count"]]
            != [undo_count, redo_count]
            or state["undo_names"] != undo_names):
        raise RuntimeError("{} changed the expected FreeCAD history: {}".format(label, state))

def production_order(snapshot):
    values = snapshot["semantic"]["document"]["persistence"]["settings"]["values"]
    records = list(values["ProductionRecordIndexJSON"]["records"])
    if len(records) != 10:
        raise RuntimeError("The turnout document lost its ten production records")
    base_contract = [
        (
            str(record.get("record_id", "")),
            str(record.get("role", "")),
            str(record.get("subtype", "")),
            str(record.get("category", "")),
            str(record.get("selection_key", "")),
            str(record.get("source_binding_type", "")),
            tuple(record.get("supported_formats", [])),
            int(record.get("track_number", 0)),
        )
        for record in records[:4]
    ]
    if base_contract != EXPECTED_PRODUCTION_RECORDS:
        raise RuntimeError("The turnout changed the accepted base production order")
    if ([_production_record_contract(record) for record in records[4:]]
            != _expected_turnout_record_contract()):
        raise RuntimeError("The turnout changed the accepted trackwork production order")
    return [str(record["record_id"]) for record in records]

def require_turnout_snapshot(snapshot, handing):
    semantic = snapshot["semantic"]
    config = semantic["turnout_catalogue"]
    if (len(config) != 1 or config[0].get("turnout_id") != TURNOUT_ID
            or config[0].get("macro_version") != "10.2A8A7B15"
            or config[0].get("handing") != handing
            or semantic["host"]["identity"] != selection["identity"]):
        raise RuntimeError("The selected B16 turnout catalogue or host identity changed")
    objects = semantic["turnout_objects"]
    if [item["role"] for item in objects] != sorted(EXPECTED_TURNOUT_ROLES):
        raise RuntimeError("The B16 turnout lost a managed object role")
    for item in objects:
        properties = item["properties"]
        if (properties["TurnoutID"] != TURNOUT_ID
                or properties["TurnoutHanding"] != handing
                or properties["TurnoutConfigurationJSON"] != config[0]):
            raise RuntimeError("A managed turnout object lost its configuration")
        shape = item.get("shape")
        if item["role"] == "TurnoutSettings":
            if shape is None or not shape["is_null"]:
                raise RuntimeError("Turnout settings unexpectedly contain geometry")
        elif shape is not None and (shape["is_null"] or not shape["is_valid"]):
            raise RuntimeError("A managed turnout object has invalid geometry")
    if plain_line_geometry_contract(semantic["document"]) != initial_host_geometry:
        raise RuntimeError("The turnout changed its host plain-line geometry")
    return production_order(snapshot)

def configure_turnout_creation():
    manager.mode_tabs.setCurrentIndex(0)
    manager.refresh_hosts()
    current = select_turnout_host(
        manager.hosts, module.object_string_property, module._integer_object_property
    )
    if current["identity"] != selection["identity"]:
        raise RuntimeError("The turnout manager changed the selected host identity")
    manager.host_combo.setCurrentIndex(current["index"])
    choose(manager.orientation_combo, module.TURNOUT_ORIENTATION_FACING)
    choose(manager.handing_combo, module.TURNOUT_HAND_LEFT)
    manager.gauge_box.setValue(16.5)
    manager.flangeway_box.setValue(1.0)
    manager.chainage_box.setValue(TURNOUT_CHAINAGE_MM)
    manager.timber_outline_box.setChecked(True)
    manager.timber_centre_box.setChecked(False)
    manager.timber_number_box.setChecked(True)
    manager.timber_length_box.setChecked(False)
    manager.datum_box.setChecked(True)
    manager.update_host_summary()

def capture_top_view(filename):
    visual_dir = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR)
    top_path = visual_dir / filename
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(top_path), 1600, 1000, "Current")
    image = QtGui.QImage(str(top_path))
    if not top_path.is_file() or top_path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("Turnout GUI screenshot is absent or invalid: {}".format(top_path))
    return str(top_path)

def capture_visuals(stage):
    visual_dir = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR)
    manager.hide()
    top_path = capture_top_view(stage + "-top-view.png")
    manager_path = visual_dir / (stage + "-manager.png")
    manager.show()
    QtWidgets.QApplication.processEvents()
    if not manager.grab().save(str(manager_path), "PNG"):
        raise RuntimeError("Qt could not save the turnout manager screenshot")
    image = QtGui.QImage(str(manager_path))
    if not manager_path.is_file() or manager_path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("Turnout GUI screenshot is absent or invalid: {}".format(manager_path))
    return [top_path, str(manager_path)]

cases = []
interval_proof = None
edit_proof = None
try:
    for name, orientation, arrangement in (
        ("facing", module.TURNOUT_ORIENTATION_FACING, module.CROSSOVER_ARRANGEMENT_FACING),
        ("trailing", module.TURNOUT_ORIENTATION_TRAILING, module.CROSSOVER_ARRANGEMENT_TRAILING),
    ):
        choose(manager.orientation_combo, orientation)
        manager_data = module.turnout_host_alignment(host)
        manager_dimensions = module.rea_c10_dimensions(
            manager.gauge_box.value(), manager.flangeway_box.value()
        )
        manager_expected = selected(manager_data["total"], manager_dimensions, orientation)
        if manager_expected[1] < manager_expected[0]:
            raise RuntimeError("The controlled fixture has no valid turnout range")
        manager_calls = observed_calls(manager.update_host_summary)
        require_call(manager_calls, manager_data["total"], manager_dimensions, orientation, manager_expected)
        manager_range = require_range(manager.chainage_box, manager_expected)
        summary = str(manager.host_summary.text())
        if "{:.3f} to {:.3f} mm".format(*manager_expected) not in summary:
            raise RuntimeError("The real turnout manager summary lost the toe range")

        choose(panel.arrangement_combo, arrangement)
        panel_data = module.turnout_host_alignment(host)
        panel_dimensions = module.rea_c10_dimensions(
            panel.gauge_box.value(), panel.flangeway_box.value()
        )
        panel_expected = selected(panel_data["total"], panel_dimensions, orientation)
        if panel_expected[1] < panel_expected[0]:
            raise RuntimeError("The controlled fixture has no valid crossover range")
        diagnostics_before = str(panel.diagnostics.toPlainText())
        panel_calls = observed_calls(panel.update_chainage_range)
        require_call(panel_calls, panel_data["total"], panel_dimensions, orientation, panel_expected)
        panel_range = require_range(panel.chainage_box, panel_expected)
        if str(panel.diagnostics.toPlainText()) != diagnostics_before:
            raise RuntimeError("The real crossover panel reported a new range error")

        cases.append({
            "orientation": name,
            "turnout": {
                "host_length": manager_data["total"],
                "dimensions": {key: manager_dimensions[key] for key in ("module_start_x", "module_end_x")},
                "domain_range": list(manager_expected),
                "gui_range": manager_range,
                "widget_decimals": int(manager.chainage_box.decimals()),
                "selected_function_calls": manager_calls,
                "summary": summary,
            },
            "crossover": {
                "host_length": panel_data["total"],
                "dimensions": {key: panel_dimensions[key] for key in ("module_start_x", "module_end_x")},
                "domain_range": list(panel_expected),
                "gui_range": panel_range,
                "widget_decimals": int(panel.chainage_box.decimals()),
                "selected_function_calls": panel_calls,
            },
        })

    configure_turnout_creation()
    dimensions = module.rea_c10_dimensions(
        manager.gauge_box.value(), manager.flangeway_box.value()
    )
    expected_interval = list(selected_interval(
        TURNOUT_CHAINAGE_MM, dimensions, module.TURNOUT_ORIENTATION_FACING
    ))
    creation_message, creation_calls = observed_interval_calls(
        lambda: run_result_dialog(manager.create_turnout, "Created " + TURNOUT_ID)
    )
    if not any(
        call["caller"] == "_build_curve_inheriting_c10_turnout"
        and call["toe_chainage"] == TURNOUT_CHAINAGE_MM
        and call["returned"] == expected_interval
        for call in creation_calls
    ):
        raise RuntimeError("Turnout creation did not use the selected occupied interval")
    created = turnout_document_snapshot(module, document)
    created_production_order = require_turnout_snapshot(created, CREATED_HANDING)
    settings = module.settings_for_template_set(document, "SET-001")
    if settings is None:
        raise RuntimeError("Turnout creation lost the selected template-set settings")
    catalogue = json.loads(str(settings.TurnoutConfigurationsJSON))
    if len(catalogue) != 1 or catalogue[0].get("turnout_id") != TURNOUT_ID:
        raise RuntimeError("Turnout creation did not persist the selected identity")
    stored_interval = catalogue[0].get("host_station_interval")
    if stored_interval != expected_interval:
        raise RuntimeError("The stored turnout interval differs from the selected calculation")
    turnout_objects = [
        obj for obj in document.Objects
        if module.object_string_property(obj, "TurnoutID", "") == TURNOUT_ID
    ]
    if len(turnout_objects) != 8:
        raise RuntimeError("Turnout creation did not retain eight managed objects")
    for obj in turnout_objects:
        config = json.loads(str(obj.TurnoutConfigurationJSON))
        if config.get("host_station_interval") != expected_interval:
            raise RuntimeError("A turnout object retained a different occupied interval")
    created_history = [int(document.UndoCount), int(document.RedoCount)]
    create_transaction = "Create Version {} REA C10 turnout".format(
        module.MACRO_VERSION_NUMBER
    )
    created_history_state = history_state(document)
    require_history(created_history_state, 1, 0, [create_transaction], "turnout creation")
    created_object_count = len(document.Objects)
    visual_evidence = capture_visuals("created-turnout")

    configure_turnout_creation()
    rejection_message, rejection_calls = observed_interval_calls(
        lambda: run_result_dialog(manager.create_turnout, "overlaps " + TURNOUT_ID)
    )
    if sum(
        call["caller"] == "_turnout_find_overlap"
        and call["toe_chainage"] == TURNOUT_CHAINAGE_MM
        and call["returned"] == expected_interval
        for call in rejection_calls
    ) < 2:
        raise RuntimeError("Overlap rejection did not compare both selected intervals")
    rejected = turnout_document_snapshot(module, document)
    rejected_history = [int(document.UndoCount), int(document.RedoCount)]
    if (rejected != created or rejected_history != created_history
            or len(document.Objects) != created_object_count):
        raise RuntimeError("Rejected overlapping turnout changed the copied document")
    interval_proof = {
        "host_identity": selection["identity"],
        "toe_chainage": TURNOUT_CHAINAGE_MM,
        "orientation": module.TURNOUT_ORIENTATION_FACING,
        "dimensions": {key: dimensions[key] for key in ("module_start_x", "module_end_x")},
        "domain_interval": expected_interval,
        "stored_interval": stored_interval,
        "created_semantic_sha256": created["semantic_sha256"],
        "rejected_semantic_sha256": rejected["semantic_sha256"],
        "created_object_count": created_object_count,
        "rejected_object_count": len(document.Objects),
        "created_history": created_history,
        "rejected_history": rejected_history,
        "creation_message": creation_message,
        "rejection_message": rejection_message,
        "creation_calls": creation_calls,
        "rejection_calls": rejection_calls,
        "visual_evidence": visual_evidence,
    }

    manager.refresh_turnouts(selected_id=TURNOUT_ID)
    manager.begin_edit_turnout()
    if manager.editing_turnout_id != TURNOUT_ID:
        raise RuntimeError("The inherited manager did not enter turnout edit mode")
    choose(manager.handing_combo, EDITED_HANDING)
    _, summary_calls = observed_summary_calls(manager.update_host_summary)
    expected_change = "Handing: {} -> {}".format(CREATED_HANDING, EDITED_HANDING)
    if not any(
        call["inherited_caller"] == "TurnoutManagerDialog.update_host_summary"
        and call["old_handing"] == CREATED_HANDING
        and call["new_handing"] == EDITED_HANDING
        and call.get("returned") == [expected_change]
        for call in summary_calls
    ):
        raise RuntimeError("The real GUI summary did not use the selected B16 application function")
    edit_dialogs, apply_summary_calls = observed_summary_calls(
        lambda: run_edit_dialog(
            manager.apply_turnout_edit, expected_change, "Updated " + TURNOUT_ID
        )
    )
    for caller_name in (
        "TurnoutManagerDialog.apply_turnout_edit",
        "edit_curve_inheriting_c10_turnout",
    ):
        if not any(
            call["inherited_caller"] == caller_name
            and call["old_handing"] == CREATED_HANDING
            and call["new_handing"] == EDITED_HANDING
            and call.get("returned") == [expected_change]
            for call in apply_summary_calls
        ):
            raise RuntimeError("Turnout edit did not call selected B16 summary: " + caller_name)
    edited = turnout_document_snapshot(module, document)
    edited_production_order = require_turnout_snapshot(edited, EDITED_HANDING)
    if edited["semantic_sha256"] == created["semantic_sha256"]:
        raise RuntimeError("Changing handing did not change turnout document semantics")
    if edited_production_order != created_production_order:
        raise RuntimeError("Turnout edit changed stable production record identities or order")
    created_role_names = {
        item["role"]: item["name"] for item in created["semantic"]["turnout_objects"]
    }
    edited_role_names = {
        item["role"]: item["name"] for item in edited["semantic"]["turnout_objects"]
    }
    if edited_role_names != created_role_names:
        raise RuntimeError("Turnout edit changed stable managed object names")
    edit_transaction = "Edit Version {} turnout {}".format(
        module.MACRO_VERSION_NUMBER, TURNOUT_ID
    )
    edited_history = history_state(document)
    require_history(
        edited_history, 2, 0, [edit_transaction, create_transaction],
        "turnout edit"
    )
    edited_visuals = capture_visuals("edited-turnout")

    document.undo()
    document.recompute()
    undone = turnout_document_snapshot(module, document)
    if undone != created:
        raise RuntimeError("One turnout edit Undo did not restore created semantics")
    undo_history = history_state(document)
    require_history(undo_history, 1, 1, [create_transaction], "turnout edit Undo")
    if undo_history["redo_names"] != [edit_transaction]:
        raise RuntimeError("Turnout edit Undo lost the Redo transaction")
    document.redo()
    document.recompute()
    redone = turnout_document_snapshot(module, document)
    if redone != edited:
        raise RuntimeError("One turnout edit Redo did not restore edited semantics")
    if history_state(document) != edited_history:
        raise RuntimeError("Turnout edit Redo changed the original transaction history")

    manager.refresh_turnouts(selected_id=TURNOUT_ID)
    manager.begin_edit_turnout()
    if manager.editing_turnout_id != TURNOUT_ID:
        raise RuntimeError("The inherited manager did not reopen turnout edit mode")
    choose(manager.handing_combo, CREATED_HANDING)
    manager.update_host_summary()
    original_tagger = module.tag_generated_object
    fault_count = {"calls": 0}
    fault_text = "Phase 8 injected turnout edit failure"
    def failing_tagger(*args, **kwargs):
        fault_count["calls"] += 1
        raise RuntimeError(fault_text)
    module.tag_generated_object = failing_tagger
    try:
        fault_dialogs = run_edit_dialog(
            manager.apply_turnout_edit,
            "Handing: {} -> {}".format(EDITED_HANDING, CREATED_HANDING),
            fault_text,
        )
    finally:
        module.tag_generated_object = original_tagger
    if fault_count["calls"] != 1:
        raise RuntimeError("The turnout edit fault did not occur at its first object tag")
    aborted = turnout_document_snapshot(module, document)
    if aborted != edited or history_state(document) != edited_history:
        raise RuntimeError("The aborted turnout edit changed semantics or history")
    manager.cancel_turnout_edit()
    edit_proof = {
        "summary_binding": "tracktemplate.application.turnout_edit.turnout_configuration_change_summary",
        "summary_caller_names": list(summary_callers),
        "summary_calls": summary_calls,
        "apply_summary_calls": apply_summary_calls,
        "edit_dialogs": edit_dialogs,
        "created_semantic_sha256": created["semantic_sha256"],
        "edited_semantic_sha256": edited["semantic_sha256"],
        "undo_semantic_sha256": undone["semantic_sha256"],
        "redo_semantic_sha256": redone["semantic_sha256"],
        "aborted_semantic_sha256": aborted["semantic_sha256"],
        "created_role_names": created_role_names,
        "edited_role_names": edited_role_names,
        "production_record_ids": edited_production_order,
        "created_history": created_history_state,
        "edited_history": edited_history,
        "undo_history": undo_history,
        "fault_dialogs": fault_dialogs,
        "fault_tagger_calls": fault_count["calls"],
        "visual_evidence": edited_visuals,
    }
finally:
    manager.close()
    QtWidgets.QApplication.processEvents()

document.recompute()
document.save()
saved_path = str(document.FileName)
saved_name = str(document.Name)
App.closeDocument(saved_name)
document = App.openDocument(saved_path)
reopened = turnout_document_snapshot(module, document)
reopened_production_order = require_turnout_snapshot(reopened, EDITED_HANDING)
if (reopened != edited or reopened_production_order != edited_production_order):
    raise RuntimeError("Copied turnout FCStd save/reopen changed edited semantics")
reopened_history = history_state(document)
require_history(reopened_history, 0, 0, [], "reopened turnout document")
reopened_visual = capture_top_view("reopened-turnout-top-view.png")
edit_proof["save_reopen"] = {
    "path": saved_path,
    "semantic_sha256": reopened["semantic_sha256"],
    "object_count": len(document.Objects),
    "history": reopened_history,
    "production_record_ids": reopened_production_order,
    "visual_evidence": [reopened_visual],
}

print(json.dumps({
    "sentinel": "PHASE8_TURNOUT_TOE_GUI_PASS",
    "development_checkpoint": "10.2A8A7B16",
    "inherited_host_version": str(module.MACRO_VERSION_NUMBER),
    "matched_profile_id": _PHASE3_QUALIFICATION["compatibility_evaluation"]["matched_profile_id"],
    "routing": {
        "route": routing["route"],
        "schema_version": routing["schema_version"],
        "function_names": routing["function_names"],
        "caller_names": routing["caller_names"],
    },
    "selected_binding": "tracktemplate.domain.turnout.turnout_valid_toe_range",
    "selected_interval_binding": "tracktemplate.domain.turnout.turnout_host_station_interval",
    "selected_summary_binding": "tracktemplate.application.turnout_edit.turnout_configuration_change_summary",
    "caller_names": list(callers),
    "interval_caller_names": list(interval_callers),
    "summary_caller_names": list(summary_callers),
    "host_identity": selection["identity"],
    "cases": cases,
    "interval_proof": interval_proof,
    "edit_proof": edit_proof,
}, sort_keys=True))
'''


def _source_hashes():
    return {str(path.relative_to(ROOT)): sha256(path) for path in SOURCE_PATHS}


def _frozen_oracle(path, function_name):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TURNOUT_ORIENTATION_TRAILING"
            for target in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in (
            "_turnout_orientation_sign", function_name
        ):
            selected.append(node)
    if len(selected) != 3:
        raise RuntimeError("The frozen turnout oracle AST does not have three exact definitions")
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    namespace = {}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[function_name]


def _compare_oracles(report, contract):
    if report.get("sentinel") != "PHASE8_TURNOUT_TOE_GUI_PASS":
        raise RuntimeError("The real GUI probe did not return its PASS sentinel")
    if report.get("matched_profile_id") != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2":
        raise RuntimeError("The real GUI probe used a different qualified host profile")
    oracles = {}
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        path = ROOT / source["path"]
        if sha256(path) != source["sha256"]:
            raise RuntimeError("The frozen {} source identity drifted".format(label))
        oracles[label] = {
            "toe_range": _frozen_oracle(path, "turnout_valid_toe_range"),
            "interval": _frozen_oracle(path, "turnout_host_station_interval"),
        }
    cases = report.get("cases")
    if not isinstance(cases, list) or [item.get("orientation") for item in cases] != ["facing", "trailing"]:
        raise RuntimeError("The real GUI proof did not cover facing and trailing")
    frozen_results = []
    for case in cases:
        for control in ("turnout", "crossover"):
            item = case[control]
            arguments = (
                item["host_length"],
                item["dimensions"],
                "Facing in host travel direction" if case["orientation"] == "facing"
                else "Trailing against host travel direction",
            )
            observed = item["gui_range"]
            for label, oracle in oracles.items():
                expected = list(oracle["toe_range"](*arguments))
                tolerance = 0.5 * 10.0 ** (-int(item["widget_decimals"])) + 1.0e-7
                if (item["domain_range"] != expected
                        or any(abs(a - b) > tolerance for a, b in zip(observed, expected))):
                    raise RuntimeError("{} {} {} GUI/domain range differs from frozen {}".format(case["orientation"], control, observed, label))
                frozen_results.append({
                    "orientation": case["orientation"], "control": control,
                    "oracle": label, "range": expected,
                })
    interval_proof = report.get("interval_proof")
    if not isinstance(interval_proof, dict):
        raise RuntimeError("The real GUI proof has no created turnout interval")
    interval_arguments = (
        interval_proof["toe_chainage"],
        interval_proof["dimensions"],
        interval_proof["orientation"],
    )
    for label, oracle in oracles.items():
        expected = list(oracle["interval"](*interval_arguments))
        if (interval_proof["domain_interval"] != expected
                or interval_proof["stored_interval"] != expected):
            raise RuntimeError("The stored turnout interval differs from frozen " + label)
        frozen_results.append({
            "orientation": "facing", "control": "stored turnout interval",
            "oracle": label, "interval": expected,
        })
    if (interval_proof["created_semantic_sha256"]
            != interval_proof["rejected_semantic_sha256"]
            or interval_proof["created_history"] != interval_proof["rejected_history"]
            or interval_proof["created_object_count"]
            != interval_proof["rejected_object_count"]):
        raise RuntimeError("Overlap rejection changed the copied turnout document")
    edit_proof = report.get("edit_proof")
    if not isinstance(edit_proof, dict):
        raise RuntimeError("The real GUI proof has no turnout edit and recovery result")
    created = edit_proof["created_semantic_sha256"]
    edited = edit_proof["edited_semantic_sha256"]
    if (created != interval_proof["created_semantic_sha256"]
            or created == edited
            or edit_proof["undo_semantic_sha256"] != created
            or edit_proof["redo_semantic_sha256"] != edited
            or edit_proof["aborted_semantic_sha256"] != edited
            or edit_proof["save_reopen"]["semantic_sha256"] != edited
            or edit_proof["created_role_names"] != edit_proof["edited_role_names"]
            or len(edit_proof["production_record_ids"]) != 10
            or edit_proof["fault_tagger_calls"] != 1):
        raise RuntimeError("The real GUI edit/recovery/persistence contract changed")
    return frozen_results


def _close_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for name in list(App.listDocuments()):
    App.closeDocument(name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('Turnout toe GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=pathlib.Path, default=(
        ROOT / "benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd"
    ))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()
    if args.port != DEFAULT_PORT:
        raise SystemExit("Phase 8 turnout toe GUI proof requires bridge port 19875")
    base = args.base.resolve()
    if not base.is_file():
        raise SystemExit("B14 default-base fixture is absent: {}".format(base))
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not token.is_file():
        raise SystemExit("The isolated FreeCAD bridge token is absent")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    source_hashes = _source_hashes()
    base_hash = sha256(base)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "phase8-turnout-toe.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-turnout-edit-recovery-gui-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": base_hash,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": "development-only curved-host turnout creation, edit and recovery",
    }
    client = FreeCADClient(
        host="127.0.0.1", port=DEFAULT_PORT, timeout=30.0,
        token=token.read_text(encoding="utf-8").strip(),
    )
    try:
        if not client.ping():
            raise RuntimeError("The isolated FreeCAD bridge did not answer ping")
        state["session_before"] = parse_json_output(execute_file(
            client, ROOT / "tools/freecad_bridge/probes/session_snapshot.py"
        ))
        if state["session_before"].get("documents"):
            raise RuntimeError("The isolated FreeCAD session is not empty")
        state["opened"] = parse_json_output(execute(client, """
import json
import FreeCAD as App
if App.listDocuments():
    raise RuntimeError('Turnout toe GUI proof requires an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER_PATH.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 turnout toe real GUI",
            args.timeout,
        )
        state["probe"] = parse_json_output(job)
        state["frozen_oracle_comparison"] = _compare_oracles(state["probe"], contract)
        visual_paths = (
            state["probe"]["interval_proof"]["visual_evidence"]
            + state["probe"]["edit_proof"]["visual_evidence"]
            + state["probe"]["edit_proof"]["save_reopen"]["visual_evidence"]
        )
        state["visual_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in visual_paths
        }
        state["run_document_sha256"] = sha256(document_path)
        state["status"] = "PASS"
    except (Exception, SystemExit) as error:
        state["status"] = "FAIL"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        primary_failure = sys.exc_info()[0] is not None
        cleanup_failure = None
        try:
            state["cleanup"] = _close_documents(client)
        except Exception as error:
            cleanup_failure = error
            state["cleanup_error"] = "{}: {}".format(type(error).__name__, error)
        state["source_fixture_sha256_after"] = sha256(base)
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != base_hash
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError("The proof source or fixture changed during the run")
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault("error", "{}: {}".format(type(cleanup_failure).__name__, cleanup_failure))
        state["retained_logs"] = {}
        for name in ("FreeCAD.log", "isolated-launcher.log"):
            source = ROOT / "benchmark-output/freecad-bridge" / name
            if source.is_file():
                try:
                    retained = run_dir / name
                    shutil.copy2(source, retained)
                    state["retained_logs"][name] = {
                        "path": str(retained), "sha256": sha256(retained),
                    }
                except Exception as error:
                    cleanup_failure = error
                    state["status"] = "FAIL"
                    state["log_retention_error"] = "{}: {}".format(type(error).__name__, error)
                    state.setdefault("error", state["log_retention_error"])
        state["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("Phase 8 turnout toe GUI evidence: {}".format(run_dir), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print("PHASE8_TURNOUT_TOE_GUI_PASS", flush=True)


if __name__ == "__main__":
    main()
