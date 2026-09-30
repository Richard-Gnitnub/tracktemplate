#!/usr/bin/env python3
"""Prove B16 straight-host crossover creation and edit in the real GUI."""

import argparse
import datetime
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".devtools/freecad-cli/src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


PORT = 19875
SOURCE_RECIPE = "phase8-b14-straight-host-source-v1"
SOURCE_SEMANTIC_SHA256 = (
    "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
)
CONTRACT = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
LOADER = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
RUN_ROOT = (
    ROOT / "benchmark-output/freecad-bridge/"
    "phase8-straight-host-crossover-gui-runs"
)
SENTINEL = "PHASE8_STRAIGHT_HOST_CROSSOVER_GUI_PASS"


GUI_PROBE = r'''
import json
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

from tools.freecad_bridge.b14_recipe import host_identity
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
    shape_summary,
)
from tracktemplate.compatibility.crossover_preflight import (
    CrossoverPreflightAdapter,
)


module = _PHASE3_SESSION.module
routing = _PHASE3_ROUTING
document = App.ActiveDocument
if document is None or not document.FileName or Gui.activeDocument() is None:
    raise RuntimeError("Open the copied straight-host fixture in a real GUI")
if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("The inherited B15 host version changed")
if routing.get("route") != "modular" or routing.get("schema_version") != 16:
    raise RuntimeError("The B16 product route is not active")
edit_binding = getattr(module.edit_rea_c10_crossover, "__self__", None)
if (not isinstance(edit_binding, CrossoverPreflightAdapter)
        or edit_binding.module is not module
        or getattr(module.edit_rea_c10_crossover, "__func__", None)
        is not CrossoverPreflightAdapter.edit):
    raise RuntimeError("The GUI edit action is not routed through B16")


def history(active_document):
    return {
        "undo_mode": int(active_document.UndoMode),
        "undo_count": int(active_document.UndoCount),
        "redo_count": int(active_document.RedoCount),
        "undo_names": [str(item) for item in active_document.UndoNames],
        "redo_names": [str(item) for item in active_document.RedoNames],
    }


def state(active_document):
    snapshot = ordinary_track_document_snapshot(module, active_document)
    return {
        "semantic_sha256": snapshot["semantic_sha256"],
        "semantic": snapshot["semantic"],
        "object_names": [str(obj.Name) for obj in active_document.Objects],
        "configs": module.existing_crossover_configs(active_document),
        "history": history(active_document),
    }


def same_document(actual, expected, label, object_order=True):
    for key in ("semantic_sha256", "semantic", "object_names", "configs"):
        if key == "object_names" and not object_order:
            changed = set(actual[key]) != set(expected[key])
        else:
            changed = actual[key] != expected[key]
        if changed:
            raise RuntimeError("{} changed copied document {}".format(label, key))


def crossover_integrity(active_document, snapshot, expected_roles,
                        geometry_roles, expected_record_ids=None):
    """Check XO-001 roles, shapes, records and live source bindings."""
    objects = [
        obj for obj in active_document.Objects
        if module.object_string_property(
            obj, module.CROSSOVER_ID_PROPERTY, ""
        ) == "XO-001"
    ]
    by_role = {
        module.object_string_property(obj, "GeneratedRole", ""): obj
        for obj in objects
    }
    if len(objects) != 9 or set(by_role) != expected_roles:
        raise RuntimeError("The live XO-001 object roles changed")
    group = by_role[module.CROSSOVER_GROUP_ROLE]
    members = list(group.Group)
    if (len(members) != 8
            or {
                module.object_string_property(obj, "GeneratedRole", "")
                for obj in members
            } != expected_roles - {module.CROSSOVER_GROUP_ROLE}):
        raise RuntimeError("The live XO-001 group membership changed")
    shapes = {
        role: shape_summary(by_role[role].Shape)
        for role in geometry_roles
    }
    if any(
        item["is_null"] or not item["is_valid"] or item["edges"] <= 0
        for item in shapes.values()
    ):
        raise RuntimeError("The live XO-001 geometry shapes changed")

    records = snapshot["semantic"]["persistence"]["settings"][
        "values"
    ]["ProductionRecordIndexJSON"]["records"]
    crossover_records = [
        item for item in records if "|XO-001|" in item["record_id"]
    ]
    record_ids = [item["record_id"] for item in crossover_records]
    if (len(crossover_records) != 4
            or len(set(record_ids)) != 4
            or (expected_record_ids is not None
                and record_ids != expected_record_ids)
            or {item["role"] for item in crossover_records}
            != {
                module.CROSSOVER_TEMPLATE_ROLE,
                module.CROSSOVER_OUTLINE_ROLE,
                module.CROSSOVER_RAIL_ROLE,
                module.CROSSOVER_DATUM_ROLE,
            }):
        raise RuntimeError("The live XO-001 production record IDs changed")
    for record in crossover_records:
        source = active_document.getObject(record["source_name"])
        if (source is None
                or str(source.Name) != str(by_role[record["role"]].Name)
                or module.object_string_property(
                    source, module.CROSSOVER_ID_PROPERTY, ""
                ) != "XO-001"):
            raise RuntimeError(
                "XO-001 production record lost its live source binding"
            )
    return {
        "object_names": sorted(str(obj.Name) for obj in objects),
        "roles": sorted(by_role),
        "shapes": shapes,
        "record_ids": record_ids,
        "source_bindings": {
            item["record_id"]: item["source_name"]
            for item in crossover_records
        },
    }


def choose(combo, value):
    index = combo.findText(value)
    if index < 0:
        raise RuntimeError("The GUI choice is absent: " + value)
    combo.setCurrentIndex(index)


def image_checked(path):
    image = QtGui.QImage(str(path))
    if not path.is_file() or path.stat().st_size == 0 or image.isNull():
        raise RuntimeError("The GUI image is absent or invalid: {}".format(path))
    return str(path)


def capture_panel(filename):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    manager.show()
    manager.mode_tabs.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()
    if not panel.grab().save(str(path), "PNG"):
        raise RuntimeError("Qt could not capture crossover panel")
    return image_checked(path)


def capture_top(filename, panel_open=True):
    path = pathlib.Path(TRACKTEMPLATE_PHASE8_VISUAL_DIR) / filename
    if panel_open:
        manager.hide()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view.saveImage(str(path), 1600, 1000, "Current")
    if panel_open:
        manager.show()
    return image_checked(path)


def confirm_create(action):
    seen = {"active": True, "questions": [], "unexpected": []}

    def monitor():
        if not seen["active"]:
            return
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if not isinstance(widget, QtWidgets.QMessageBox) or not widget.isVisible():
                continue
            message = "{}\n{}".format(widget.text(), widget.informativeText())
            yes = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
            if yes is not None and not seen["questions"]:
                seen["questions"].append(message)
                yes.click()
            else:
                seen["unexpected"].append(message)
                widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    QtCore.QTimer.singleShot(0, monitor)
    try:
        action()
    finally:
        seen["active"] = False
    if len(seen["questions"]) != 1 or seen["unexpected"]:
        raise RuntimeError("Crossover confirmation changed: {}".format(seen))
    return seen["questions"][0]


manager = module.TurnoutManagerDialog(document)
manager.show()
manager.mode_tabs.setCurrentIndex(1)
QtWidgets.QApplication.processEvents()
panel = manager.crossover_panel

try:
    before = state(document)
    if (len(before["object_names"]) != 23 or before["configs"]
            or before["history"]["undo_count"]):
        raise RuntimeError("The copied straight-host fixture changed")

    panel.refresh_hosts()
    identities = [
        host_identity(
            host, module.object_string_property,
            module._integer_object_property,
        )
        for host in panel.hosts
    ]

    def select_host(route_id, track_number):
        matches = [
            index for index, item in enumerate(identities)
            if item["template_set_id"] == "SET-001"
            and item["route_id"] == route_id
            and item["track_number"] == track_number
            and item["generated_role"] == "StraightTrackCentreline"
        ]
        if len(matches) != 1:
            raise RuntimeError(
                "Expected one straight host {}/{}: {}".format(
                    route_id, track_number, identities
                )
            )
        return matches[0]

    entrance_route = "straight-phase1-curve-entrance"
    a_index = select_host(entrance_route, 1)
    b_index = select_host(entrance_route, 2)
    panel.host_a_combo.setCurrentIndex(a_index)
    panel.host_b_combo.setCurrentIndex(b_index)
    selected_a = identities[a_index]
    selected_b = identities[b_index]
    if (selected_a["object_name"] != "RailwayStraightTrackCentreline_R01_T01"
            or selected_b["object_name"] != "RailwayStraightTrackCentreline_R01_T02"):
        raise RuntimeError("The GUI selected another pair of straight hosts")
    choose(panel.arrangement_combo, module.CROSSOVER_ARRANGEMENT_FACING)
    choose(panel.handing_combo, module.CROSSOVER_HAND_AUTO)
    panel.gauge_box.setValue(16.5)
    panel.flangeway_box.setValue(1.0)
    panel.minimum_radius_box.setValue(600.0)
    panel.chainage_box.setValue(580.134)
    if abs(float(panel.chainage_box.value()) - 580.134) > 1.0e-9:
        raise RuntimeError("The GUI did not retain its representable toe")

    panel.minimum_radius_box.setValue(100000.0)
    rejected = panel.preview_geometry()
    rejection = str(panel.diagnostics.toPlainText())
    if rejected is not None or "REJECTED" not in rejection:
        raise RuntimeError("The impossible-radius GUI preview was accepted")
    rejected_preview = state(document)
    same_document(rejected_preview, before, "Rejected preview")
    if rejected_preview["history"] != before["history"]:
        raise RuntimeError("Rejected preview changed Undo/Redo history")
    rejected_visual = capture_panel("straight-host-rejected-preview.png")
    panel.create_crossover()
    rejected_create = state(document)
    same_document(rejected_create, before, "Rejected create")
    if rejected_create["history"] != before["history"]:
        raise RuntimeError("Rejected create changed Undo/Redo history")

    panel.minimum_radius_box.setValue(600.0)
    preview = panel.preview_geometry()
    if preview is None:
        raise RuntimeError(
            "The straight-host GUI preview was rejected: {}".format(
                panel.diagnostics.toPlainText()
            )
        )
    preflight = dict(preview.get("complete_radius_preflight") or {})
    if (preflight.get("accepted") is not True
            or len(str(preflight.get("input_signature") or "")) != 64
            or float(preflight.get("complete_minimum_radius_mm") or 0) < 600):
        raise RuntimeError("Straight-host preview lost the signed radius decision")
    positive = str(panel.diagnostics.toPlainText())
    if "Complete crossover minimum radius" not in positive:
        raise RuntimeError("The GUI did not show the complete radius decision")
    preview_visual = capture_panel("straight-host-accepted-preview.png")
    confirmation = confirm_create(panel.create_crossover)
    created = state(document)
    configs = created["configs"]
    if len(configs) != 1 or configs[0].get("crossover_id") != "XO-001":
        raise RuntimeError("The GUI did not create exactly one XO-001")
    config = configs[0]
    if (config.get("host_a_object") != selected_a["object_name"]
            or config.get("host_b_object") != selected_b["object_name"]
            or abs(float(config.get("toe_chainage_a") or 0) - 580.134) > 1.0e-9
            or config.get("arrangement") != module.CROSSOVER_ARRANGEMENT_FACING
            or float(config.get("track_gauge") or 0) != 16.5
            or float(config.get("flangeway") or 0) != 1.0
            or float(config.get("minimum_requested_radius") or 0) != 600.0):
        raise RuntimeError("The stored crossover inputs differ from GUI choices")
    if (float(config.get("minimum_resulting_radius") or 0) < 600.0
            or abs(
                float(config.get("minimum_resulting_radius") or 0)
                - float(preflight["complete_minimum_radius_mm"])
            ) > 1.0e-3):
        raise RuntimeError("Built crossover differs from radius preflight")
    if (config.get("connector_topology_status")
            != "Accepted: diverging branch end to diverging branch end; "
               "sampled route clear of both switch regions"
            or int(config.get("connector_point_count") or 0) != 3
            or abs(float(config.get("positional_continuity_error") or 0))
            > 1.0e-6
            or abs(float(config.get("tangent_continuity_error_degrees") or 0))
            > 1.0e-6):
        raise RuntimeError("The straight-host connector topology changed")
    expected_roles = {
        module.CROSSOVER_GROUP_ROLE,
        module.CROSSOVER_SETTINGS_ROLE,
        module.CROSSOVER_TURNOUT_A_SETTINGS_ROLE,
        module.CROSSOVER_TURNOUT_B_SETTINGS_ROLE,
        module.CROSSOVER_TEMPLATE_ROLE,
        module.CROSSOVER_OUTLINE_ROLE,
        module.CROSSOVER_RAIL_ROLE,
        module.CROSSOVER_TIMBER_REFERENCE_ROLE,
        module.CROSSOVER_DATUM_ROLE,
    }
    crossover_objects = [
        obj for obj in document.Objects
        if module.object_string_property(
            obj, module.CROSSOVER_ID_PROPERTY, ""
        ) == "XO-001"
    ]
    crossover_roles = {
        module.object_string_property(obj, "GeneratedRole", "")
        for obj in crossover_objects
    }
    if len(crossover_objects) != 9 or crossover_roles != expected_roles:
        raise RuntimeError("The straight-host XO-001 object roles changed")
    geometry_roles = {
        module.CROSSOVER_TEMPLATE_ROLE,
        module.CROSSOVER_OUTLINE_ROLE,
        module.CROSSOVER_RAIL_ROLE,
    }
    geometry_shapes = {
        module.object_string_property(obj, "GeneratedRole", ""):
            shape_summary(obj.Shape)
        for obj in crossover_objects
        if module.object_string_property(obj, "GeneratedRole", "")
        in geometry_roles
    }
    if (set(geometry_shapes) != geometry_roles
            or any(
                item["is_null"] or not item["is_valid"]
                or item["edges"] <= 0
                for item in geometry_shapes.values()
            )):
        raise RuntimeError("The straight-host geometry shapes changed")
    before_records = before["semantic"]["persistence"]["settings"][
        "values"
    ]["ProductionRecordIndexJSON"]["records"]
    created_records = created["semantic"]["persistence"]["settings"][
        "values"
    ]["ProductionRecordIndexJSON"]["records"]
    before_ids = {item["record_id"] for item in before_records}
    created_ids = [item["record_id"] for item in created_records]
    crossover_records = [
        item for item in created_records
        if "|XO-001|" in item["record_id"]
    ]
    record_roles = {
        item["role"] for item in crossover_records
    }
    if (len(before_records) != 12 or len(created_records) != 16
            or len(set(created_ids)) != 16
            or not before_ids.issubset(created_ids)
            or len(crossover_records) != 4
            or record_roles != {
                module.CROSSOVER_TEMPLATE_ROLE,
                module.CROSSOVER_OUTLINE_ROLE,
                module.CROSSOVER_RAIL_ROLE,
                module.CROSSOVER_DATUM_ROLE,
            }
            or any(
                item["source_name"] not in created["object_names"]
                for item in crossover_records
            )):
        raise RuntimeError("The straight-host production records changed")
    created_object_names = sorted(str(obj.Name) for obj in crossover_objects)
    created_record_ids = [item["record_id"] for item in crossover_records]
    if (len(created["object_names"]) != 32
            or created["history"]["undo_count"] != 1
            or created["history"]["redo_count"] != 0):
        raise RuntimeError("GUI creation did not make one Undo unit")
    created_visuals = [
        capture_panel("straight-host-created-panel.png"),
        capture_top("straight-host-created-top-view.png"),
    ]

    document.undo()
    document.recompute()
    undone = state(document)
    same_document(undone, before, "Crossover Undo")
    if (undone["history"]["undo_count"] != 0
            or undone["history"]["redo_count"] != 1):
        raise RuntimeError("Crossover Undo changed history")
    document.redo()
    document.recompute()
    redone = state(document)
    same_document(redone, created, "Crossover Redo")
    if (redone["history"]["undo_count"] != 1
            or redone["history"]["redo_count"] != 0):
        raise RuntimeError("Crossover Redo changed history")

    manager.close()
    QtWidgets.QApplication.processEvents()
    document.save()
    saved_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(saved_path)
    reopened = state(document)
    same_document(reopened, created, "Copied FCStd save/reopen")
    if (reopened["history"]["undo_count"] != 0
            or reopened["history"]["redo_count"] != 0):
        raise RuntimeError("The reopened document retained session history")
    reopened_visual = capture_top(
        "straight-host-reopened-top-view.png", panel_open=False
    )
    reopened_integrity = crossover_integrity(
        document, reopened, expected_roles, geometry_roles,
        expected_record_ids=created_record_ids,
    )

    manager = module.TurnoutManagerDialog(document)
    manager.show()
    manager.mode_tabs.setCurrentIndex(1)
    QtWidgets.QApplication.processEvents()
    panel = manager.crossover_panel
    panel.refresh_crossovers("XO-001")
    selected_config = panel.current_config()
    if (selected_config is None
            or selected_config.get("crossover_id") != "XO-001"
            or selected_config != reopened["configs"][0]):
        raise RuntimeError("The reopened GUI did not select stored XO-001")
    panel.begin_crossover_edit()
    if panel.editing_crossover_id != "XO-001":
        raise RuntimeError("The GUI did not enter XO-001 edit mode")
    if "Editing XO-001" not in str(panel.selection_status.text()):
        raise RuntimeError("The GUI did not show the XO-001 edit cue")
    panel.chainage_box.setValue(580.135)
    if abs(float(panel.chainage_box.value()) - 580.135) > 1.0e-9:
        raise RuntimeError("The GUI did not retain the edited toe")

    panel.minimum_radius_box.setValue(100000.0)
    rejected_edit_preview = panel.preview_geometry()
    edit_rejection = str(panel.diagnostics.toPlainText())
    if rejected_edit_preview is not None or "REJECTED" not in edit_rejection:
        raise RuntimeError("The impossible-radius edit preview was accepted")
    edit_rejected = state(document)
    same_document(edit_rejected, reopened, "Rejected crossover edit preview")
    if edit_rejected["history"] != reopened["history"]:
        raise RuntimeError("Rejected edit preview changed Undo/Redo history")
    edit_rejected_visual = capture_panel(
        "straight-host-edit-rejected-preview.png"
    )
    panel.create_crossover()
    rejected_edit_create = state(document)
    same_document(
        rejected_edit_create, reopened, "Rejected crossover edit apply"
    )
    if rejected_edit_create["history"] != reopened["history"]:
        raise RuntimeError("Rejected edit apply changed Undo/Redo history")
    rejected_edit_status = str(panel.selection_status.text())
    if (panel.editing_crossover_id != "XO-001"
            or "Editing XO-001" not in rejected_edit_status):
        raise RuntimeError("Rejected XO-001 Edit lost its edit cue")

    panel.minimum_radius_box.setValue(600.0)
    edit_preview = panel.preview_geometry()
    if edit_preview is None:
        raise RuntimeError(
            "The straight-host GUI edit preview was rejected: {}".format(
                panel.diagnostics.toPlainText()
            )
        )
    edit_preflight = dict(
        edit_preview.get("complete_radius_preflight") or {}
    )
    if (abs(float(edit_preview.get("toe_chainage_a") or 0)
            - 580.135) > 1.0e-9
            or edit_preflight.get("accepted") is not True
            or len(str(edit_preflight.get("input_signature") or "")) != 64
            or float(edit_preflight.get(
                "complete_minimum_radius_mm") or 0
            ) < 600):
        raise RuntimeError("Straight-host edit preview lost its radius decision")
    edit_previewed = state(document)
    same_document(edit_previewed, reopened, "Crossover edit preview")
    if edit_previewed["history"] != reopened["history"]:
        raise RuntimeError("Crossover edit preview changed Undo/Redo history")
    edit_preview_visual = capture_panel(
        "straight-host-edit-accepted-preview.png"
    )

    edit_confirmation = confirm_create(panel.create_crossover)
    edit_success_visual = capture_panel("straight-host-edited-panel.png")
    edit_success_status = str(panel.selection_status.text())
    edit_success_diagnostic = str(panel.diagnostics.toPlainText())
    if (panel.editing_crossover_id is not None
            or "Updated XO-001" not in edit_success_status
            or "Editing XO-001" in edit_success_status
            or "Updated XO-001 transactionally." not in
            edit_success_diagnostic):
        raise RuntimeError(
            "Accepted XO-001 Edit left a stale Picked placement cue: "
            "status={!r}; diagnostic={!r}; visual={!r}".format(
                edit_success_status, edit_success_diagnostic,
                edit_success_visual,
            )
        )
    panel.refresh_crossovers("XO-001")
    edited_config = panel.current_config()
    edited = state(document)
    if (edited_config is None
            or edited_config.get("crossover_id") != "XO-001"
            or edited_config != edited["configs"][0]
            or int(edited_config.get("edit_revision") or 0) != 1
            or abs(float(edited_config.get("toe_chainage_a") or 0)
                   - 580.135) > 1.0e-9):
        raise RuntimeError("The GUI did not retain the XO-001 edit identity")
    preserved_config_keys = (
        "crossover_id", "template_set_id", "host_a_object",
        "host_b_object", "arrangement", "handing", "track_gauge",
        "flangeway", "minimum_requested_radius", "turnout_a_id",
        "turnout_b_id", "production_ready", "host_integration_allowed",
    )
    if any(
        edited_config.get(key) != config.get(key)
        for key in preserved_config_keys
    ):
        raise RuntimeError("The edit changed a preserved XO-001 config field")
    if (len(edited["object_names"]) != 32
            or not set(before["object_names"]).issubset(
                edited["object_names"]
            )
            or len(edited["configs"]) != 1
            or edited["semantic_sha256"] == reopened["semantic_sha256"]
            or edited["history"]["undo_count"] != 1
            or edited["history"]["redo_count"] != 0):
        raise RuntimeError("GUI edit changed hosts, state or Undo unit")
    edited_integrity = crossover_integrity(
        document, edited, expected_roles, geometry_roles,
        expected_record_ids=created_record_ids,
    )
    edited_records = edited["semantic"]["persistence"]["settings"][
        "values"
    ]["ProductionRecordIndexJSON"]["records"]
    if (len(edited_records) != 16
            or [
                item for item in edited_records
                if "|XO-001|" not in item["record_id"]
            ] != [
                item for item in created_records
                if "|XO-001|" not in item["record_id"]
            ]):
        raise RuntimeError("The edit changed unrelated production records")
    edited_visuals = [
        edit_success_visual,
        capture_top("straight-host-edited-top-view.png"),
    ]

    document.undo()
    document.recompute()
    edit_undone = state(document)
    same_document(
        edit_undone, reopened, "Crossover edit Undo", object_order=False
    )
    if (edit_undone["history"]["undo_count"] != 0
            or edit_undone["history"]["redo_count"] != 1):
        raise RuntimeError("Crossover edit Undo changed history")
    undo_integrity = crossover_integrity(
        document, edit_undone, expected_roles, geometry_roles,
        expected_record_ids=created_record_ids,
    )
    panel.refresh_crossovers("XO-001")
    undo_config = panel.current_config()
    if (undo_config is None
            or undo_config.get("crossover_id") != "XO-001"
            or undo_config != reopened["configs"][0]):
        raise RuntimeError("Crossover edit Undo lost XO-001 selection")
    edit_undo_visual = capture_top(
        "straight-host-edit-undone-top-view.png"
    )

    document.redo()
    document.recompute()
    edit_redone = state(document)
    same_document(
        edit_redone, edited, "Crossover edit Redo", object_order=False
    )
    if (edit_redone["history"]["undo_count"] != 1
            or edit_redone["history"]["redo_count"] != 0):
        raise RuntimeError("Crossover edit Redo changed history")
    redo_integrity = crossover_integrity(
        document, edit_redone, expected_roles, geometry_roles,
        expected_record_ids=created_record_ids,
    )
    panel.refresh_crossovers("XO-001")
    redo_config = panel.current_config()
    if (redo_config is None
            or redo_config.get("crossover_id") != "XO-001"
            or redo_config != edited_config):
        raise RuntimeError("Crossover edit Redo lost XO-001 selection")
    edit_redo_visual = capture_top(
        "straight-host-edit-redone-top-view.png"
    )

    manager.close()
    QtWidgets.QApplication.processEvents()
    before_edit_save = state(document)
    same_document(
        before_edit_save, edited, "Closing edited crossover panel",
        object_order=False,
    )
    document.save()
    edited_saved_path = str(document.FileName)
    App.closeDocument(str(document.Name))
    document = App.openDocument(edited_saved_path)
    edit_reopened = state(document)
    same_document(
        edit_reopened, edited, "Edited copied FCStd save/reopen",
        object_order=False,
    )
    if (edit_reopened["history"]["undo_count"] != 0
            or edit_reopened["history"]["redo_count"] != 0):
        raise RuntimeError("The edited reopened document retained history")
    edit_reopened_integrity = crossover_integrity(
        document, edit_reopened, expected_roles, geometry_roles,
        expected_record_ids=created_record_ids,
    )
    edit_reopened_visual = capture_top(
        "straight-host-edited-reopened-top-view.png", panel_open=False
    )

    print(json.dumps({
        "sentinel": "PHASE8_STRAIGHT_HOST_CROSSOVER_GUI_PROBE_PASS",
        "matched_profile_id": _PHASE3_QUALIFICATION[
            "compatibility_evaluation"
        ]["matched_profile_id"],
        "routing": {
            "route": routing["route"],
            "schema_version": routing["schema_version"],
        },
        "host_a_identity": selected_a,
        "host_b_identity": selected_b,
        "source_object_count": len(before["object_names"]),
        "rejection": {
            "diagnostic": rejection,
            "state_unchanged": True,
            "history": rejected_create["history"],
            "visual": rejected_visual,
        },
        "creation": {
            "toe_chainage_a_mm": float(config["toe_chainage_a"]),
            "toe_chainage_b_mm": float(config["toe_chainage_b"]),
            "preflight": preflight,
            "built_minimum_radius_mm": float(
                config["minimum_resulting_radius"]
            ),
            "object_count": len(created["object_names"]),
            "crossover_object_names": created_object_names,
            "crossover_roles": sorted(crossover_roles),
            "geometry_shapes": geometry_shapes,
            "production_record_count": len(created_records),
            "crossover_production_record_ids": [
                item["record_id"] for item in crossover_records
            ],
            "semantic_sha256": created["semantic_sha256"],
            "config": config,
            "history": created["history"],
            "confirmation": confirmation,
            "diagnostic": positive,
            "visuals": [preview_visual, *created_visuals],
        },
        "undo": {
            "object_count": len(undone["object_names"]),
            "semantic_sha256": undone["semantic_sha256"],
            "history": undone["history"],
        },
        "redo": {
            "object_count": len(redone["object_names"]),
            "semantic_sha256": redone["semantic_sha256"],
            "history": redone["history"],
        },
        "save_reopen": {
            "path": saved_path,
            "object_count": len(reopened["object_names"]),
            "semantic_sha256": reopened["semantic_sha256"],
            "source_bindings": reopened_integrity["source_bindings"],
            "history": reopened["history"],
            "visual": reopened_visual,
        },
        "edit_rejection": {
            "diagnostic": edit_rejection,
            "picked_placement": rejected_edit_status,
            "state_unchanged": True,
            "history": rejected_edit_create["history"],
            "visual": edit_rejected_visual,
        },
        "edit_preview": {
            "toe_chainage_a_mm": float(edit_preview["toe_chainage_a"]),
            "preflight": edit_preflight,
            "state_unchanged": True,
            "history": edit_previewed["history"],
            "visual": edit_preview_visual,
        },
        "edit": {
            "selected_crossover_id": edited_config["crossover_id"],
            "toe_chainage_a_mm": float(edited_config["toe_chainage_a"]),
            "edit_revision": int(edited_config["edit_revision"]),
            "object_count": len(edited["object_names"]),
            "crossover_object_names": edited_integrity["object_names"],
            "crossover_roles": edited_integrity["roles"],
            "geometry_shapes": edited_integrity["shapes"],
            "production_record_count": len(edited_records),
            "crossover_production_record_ids": edited_integrity[
                "record_ids"
            ],
            "source_bindings": edited_integrity["source_bindings"],
            "semantic_sha256": edited["semantic_sha256"],
            "config": edited_config,
            "history": edited["history"],
            "confirmation": edit_confirmation,
            "success_cue": {
                "picked_placement": edit_success_status,
                "diagnostic": edit_success_diagnostic,
                "visual": edit_success_visual,
            },
            "visuals": edited_visuals,
        },
        "edit_undo": {
            "selected_crossover_id": undo_config["crossover_id"],
            "object_count": len(edit_undone["object_names"]),
            "semantic_sha256": edit_undone["semantic_sha256"],
            "source_bindings": undo_integrity["source_bindings"],
            "history": edit_undone["history"],
            "visual": edit_undo_visual,
        },
        "edit_redo": {
            "selected_crossover_id": redo_config["crossover_id"],
            "object_count": len(edit_redone["object_names"]),
            "semantic_sha256": edit_redone["semantic_sha256"],
            "source_bindings": redo_integrity["source_bindings"],
            "history": edit_redone["history"],
            "visual": edit_redo_visual,
        },
        "edit_save_reopen": {
            "path": edited_saved_path,
            "object_count": len(edit_reopened["object_names"]),
            "semantic_sha256": edit_reopened["semantic_sha256"],
            "source_bindings": edit_reopened_integrity["source_bindings"],
            "history": edit_reopened["history"],
            "visual": edit_reopened_visual,
        },
    }, sort_keys=True))
finally:
    manager.close()
    QtWidgets.QApplication.processEvents()
'''


def _source_hashes():
    paths = [
        ROOT / "AdvancedTurnout.FCMacro",
        ROOT / "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
        ROOT / "TrackTemplate.FCMacro",
        LOADER,
        ROOT / "tools/freecad_bridge/run_b14_straight_station.py",
        ROOT / "tools/freecad_bridge/probes/b14_straight_station_driver.py",
        pathlib.Path(__file__).resolve(),
        ROOT / "tools/freecad_bridge/run-phase8-straight-host-crossover-gui",
        *sorted((ROOT / "tracktemplate").rglob("*.py")),
    ]
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def _close_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for name in list(App.listDocuments()):
    App.closeDocument(name)
remaining = sorted(App.listDocuments())
if remaining:
    raise RuntimeError('The GUI proof left documents open: {}'.format(remaining))
print(json.dumps({'closed': closed, 'remaining': remaining}, sort_keys=True))
"""))


def _check_probe(probe):
    if probe.get("sentinel") != "PHASE8_STRAIGHT_HOST_CROSSOVER_GUI_PROBE_PASS":
        raise RuntimeError("The GUI probe did not return its PASS sentinel")
    if (probe.get("matched_profile_id")
            != "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"):
        raise RuntimeError("The real GUI proof used another FreeCAD profile")
    if (probe["host_a_identity"]["object_name"]
            != "RailwayStraightTrackCentreline_R01_T01"
            or probe["host_b_identity"]["object_name"]
            != "RailwayStraightTrackCentreline_R01_T02"):
        raise RuntimeError("The real GUI used another host pair")
    if (probe["rejection"]["state_unchanged"] is not True
            or probe["source_object_count"] != 23
            or probe["creation"]["object_count"] != 32
            or probe["creation"]["production_record_count"] != 16
            or len(probe["creation"]["crossover_production_record_ids"]) != 4
            or probe["save_reopen"]["object_count"] != 32
            or probe["creation"]["history"]["undo_count"] != 1
            or probe["undo"]["semantic_sha256"]
            == probe["creation"]["semantic_sha256"]
            or probe["redo"]["semantic_sha256"]
            != probe["creation"]["semantic_sha256"]
            or probe["save_reopen"]["semantic_sha256"]
            != probe["creation"]["semantic_sha256"]):
        raise RuntimeError("The GUI transaction or persistence proof changed")
    if (probe["edit_rejection"]["state_unchanged"] is not True
            or "Editing XO-001" not in
            probe["edit_rejection"]["picked_placement"]
            or probe["edit_preview"]["state_unchanged"] is not True
            or abs(probe["edit_preview"]["toe_chainage_a_mm"]
                   - 580.135) > 1.0e-9
            or probe["edit_preview"]["preflight"]["accepted"] is not True
            or probe["edit"]["selected_crossover_id"] != "XO-001"
            or probe["edit"]["edit_revision"] != 1
            or abs(probe["edit"]["toe_chainage_a_mm"]
                   - 580.135) > 1.0e-9
            or probe["edit"]["object_count"] != 32
            or probe["edit"]["production_record_count"] != 16
            or probe["edit"]["crossover_production_record_ids"]
            != probe["creation"]["crossover_production_record_ids"]
            or probe["edit"]["history"]["undo_count"] != 1
            or probe["edit"]["history"]["redo_count"] != 0
            or "Updated XO-001" not in
            probe["edit"]["success_cue"]["picked_placement"]
            or "Editing XO-001" in
            probe["edit"]["success_cue"]["picked_placement"]
            or "Updated XO-001 transactionally." not in
            probe["edit"]["success_cue"]["diagnostic"]
            or probe["edit"]["semantic_sha256"]
            == probe["save_reopen"]["semantic_sha256"]
            or probe["edit_undo"]["selected_crossover_id"] != "XO-001"
            or probe["edit_undo"]["semantic_sha256"]
            != probe["save_reopen"]["semantic_sha256"]
            or probe["edit_undo"]["history"]["undo_count"] != 0
            or probe["edit_undo"]["history"]["redo_count"] != 1
            or probe["edit_redo"]["selected_crossover_id"] != "XO-001"
            or probe["edit_redo"]["semantic_sha256"]
            != probe["edit"]["semantic_sha256"]
            or probe["edit_redo"]["history"]["undo_count"] != 1
            or probe["edit_redo"]["history"]["redo_count"] != 0
            or probe["edit_save_reopen"]["object_count"] != 32
            or probe["edit_save_reopen"]["semantic_sha256"]
            != probe["edit"]["semantic_sha256"]
            or probe["edit_save_reopen"]["history"]["undo_count"] != 0
            or probe["edit_save_reopen"]["history"]["redo_count"] != 0):
        raise RuntimeError("The GUI edit transaction or persistence proof changed")
    return [
        probe["rejection"]["visual"],
        *probe["creation"]["visuals"],
        probe["save_reopen"]["visual"],
        probe["edit_rejection"]["visual"],
        probe["edit_preview"]["visual"],
        *probe["edit"]["visuals"],
        probe["edit_undo"]["visual"],
        probe["edit_redo"]["visual"],
        probe["edit_save_reopen"]["visual"],
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-receipt", type=pathlib.Path, required=True,
        help="PASS receipt from run-b14-straight-station --scenario phase8-straight-host",
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()
    if args.port != PORT:
        raise SystemExit("The isolated GUI proof requires port 19875")
    receipt_path = args.source_receipt.resolve()
    if not receipt_path.is_file():
        raise SystemExit("The B14 source-generation receipt is absent")
    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (source_receipt.get("recipe_id") != SOURCE_RECIPE
            or source_receipt.get("scenario") != "phase8-straight-host"
            or source_receipt.get("status") != "completed"
            or source_receipt.get("comparison_witness_sha256")
            != SOURCE_SEMANTIC_SHA256
            or source_receipt.get("source_fixture_sha256_after")
            != source_receipt.get("source_fixture_sha256")
            or source_receipt["recipe"]["scenarios"][-1]["snapshot"][
                "semantic_sha256"
            ] != SOURCE_SEMANTIC_SHA256
            or source_receipt["recipe"]["save_reopen"][
                "semantic_sha256"
            ] != SOURCE_SEMANTIC_SHA256):
        raise SystemExit("The B14 straight-host source receipt is not accepted")
    base = pathlib.Path(source_receipt["run_document"]).resolve()
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    if not base.is_file() or not token.is_file():
        raise SystemExit("The source fixture or isolated bridge token is absent")
    if sha256(base) != source_receipt.get("run_document_sha256"):
        raise SystemExit("The generated B14 straight-host FCStd identity drifted")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise SystemExit("Frozen {} source identity drifted".format(label))
    source_hashes = _source_hashes()
    fixture_hash = sha256(base)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_dir = RUN_ROOT / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "straight-host-crossover.FCStd"
    shutil.copy2(base, document_path)
    state = {
        "recipe_id": "phase8-b16-straight-host-crossover-real-gui-v2",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base),
        "source_fixture_sha256": fixture_hash,
        "source_receipt": str(receipt_path),
        "source_receipt_sha256": sha256(receipt_path),
        "source_semantic_sha256": SOURCE_SEMANTIC_SHA256,
        "source_sha256": source_hashes,
        "run_document": str(document_path),
        "scope": (
            "one straight-host facing crossover; GUI rejection, creation, "
            "edit, Undo/Redo and copied-FCStd save/reopen at each state"
        ),
    }
    client = FreeCADClient(
        host="127.0.0.1", port=PORT, timeout=30.0,
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
    raise RuntimeError('The straight-host GUI proof needs an empty session')
document = App.openDocument({path!r})
print(json.dumps({{'document': document.Name, 'objects': len(document.Objects)}}, sort_keys=True))
""".format(path=str(document_path))))
        job = submit_and_wait(
            client,
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + "TRACKTEMPLATE_PHASE8_VISUAL_DIR = {!r}\n".format(str(run_dir))
            + LOADER.read_text(encoding="utf-8") + "\n" + GUI_PROBE,
            "Phase 8 straight-host crossover real GUI", args.timeout,
        )
        state["probe"] = parse_json_output(job)
        visuals = _check_probe(state["probe"])
        state["visual_evidence"] = {
            pathlib.Path(path).name: {
                "path": path,
                "bytes": pathlib.Path(path).stat().st_size,
                "sha256": sha256(pathlib.Path(path)),
            }
            for path in visuals
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
            state["cleanup_error"] = "{}: {}".format(
                type(error).__name__, error
            )
        state["source_fixture_sha256_after"] = sha256(base)
        state["source_receipt_sha256_after"] = sha256(receipt_path)
        state["source_sha256_after"] = _source_hashes()
        if (state["source_fixture_sha256_after"] != fixture_hash
                or state["source_receipt_sha256_after"]
                != state["source_receipt_sha256"]
                or state["source_sha256_after"] != source_hashes):
            cleanup_failure = RuntimeError(
                "The GUI proof changed a source or the source fixture"
            )
        if cleanup_failure is not None:
            state["status"] = "FAIL"
            state.setdefault("error", "{}: {}".format(
                type(cleanup_failure).__name__, cleanup_failure
            ))
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
                    state["log_retention_error"] = "{}: {}".format(
                        type(error).__name__, error
                    )
                    state.setdefault("error", state["log_retention_error"])
        state["finished_utc"] = (
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        (run_dir / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Phase 8 straight-host GUI evidence: {}".format(run_dir), flush=True)
        if cleanup_failure is not None and not primary_failure:
            raise cleanup_failure
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
