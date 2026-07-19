"""Create and validate the deterministic B14 benchmark base inside FreeCAD."""

import json
import os
import pathlib
import sys

import FreeCAD as App

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore, QtGui

        QtWidgets = QtGui

from tools.freecad_bridge.b14_recipe import freecad_base_snapshot


MODULE_NAME = "tracktemplate_b14_session"
SUCCESS_TEXT = "Curve and straight-track outputs created successfully"
output_path = pathlib.Path(os.environ["TRACKTEMPLATE_B14_BASE_OUTPUT"]).resolve()

if App.listDocuments():
    raise RuntimeError("B14 base construction requires an empty FreeCAD session")
if output_path.exists():
    raise RuntimeError("Refusing to overwrite B14 base output: {}".format(output_path))
if MODULE_NAME not in sys.modules:
    raise RuntimeError("B14 definitions have not been loaded")

module = sys.modules[MODULE_NAME]
state = {
    "curve_dialogs": 0,
    "success_dialogs": 0,
    "unexpected_dialogs": [],
    "monitor_errors": [],
}


def validate_dialog_values(values):
    (
        transition,
        radius,
        angle,
        main_width,
        tracks,
        straight_configs,
        _selected_straight_index,
        platform_configs,
        _selected_platform_id,
        _selected_platform_index,
        formation_config,
        section_config,
        _registration_config,
        template_assembly_config,
        assembly_label_config,
        production_export_config,
        material_report_config,
        output_mode,
    ) = values
    expected_track = module.clone_track_config(
        module.DEFAULT_PARALLEL_TRACKS[0],
        module.DEFAULT_TRANSITION_LENGTH,
    )
    track_keys = (
        "name",
        "side",
        "alignment_mode",
        "start_spacing",
        "curve_spacing",
        "finish_spacing",
        "entry_transition_length",
        "exit_transition_length",
        "width",
        "create_template",
        "show_centreline",
    )
    actual_tracks = [{key: track[key] for key in track_keys} for track in tracks]
    expected_tracks = [{key: expected_track[key] for key in track_keys}]
    checks = {
        "transition_mm": transition == module.DEFAULT_TRANSITION_LENGTH,
        "radius_mm": radius == module.DEFAULT_RADIUS,
        "angle_degrees": angle == module.DEFAULT_TURN_ANGLE,
        "main_width_mm": main_width == module.DEFAULT_MAIN_TEMPLATE_WIDTH,
        "tracks": actual_tracks == expected_tracks,
        "straight_routes_disabled": straight_configs == [],
        "platforms_disabled": bool(platform_configs) and not any(
            config.get("enabled", False) for config in platform_configs
        ),
        "formation_disabled": not formation_config.get("enabled", False),
        "sectioning_disabled": not section_config.get("enabled", False),
        "template_assembly_disabled": not template_assembly_config.get("enabled", False),
        "assembly_labels_disabled": not assembly_label_config.get("enabled", False),
        "production_export_disabled": not production_export_config.get("enabled", False),
        "material_report_defaults": (
            material_report_config == module.default_material_report_config()
        ),
        "replace_output": output_mode == module.OUTPUT_REPLACE,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError("Unexpected B14 base input(s): {}".format(", ".join(failed)))
    return {
        "checks": checks,
        "track_configs": actual_tracks,
        "placement_basis": "generated centreline identities; no XYZ placement",
    }


def configure_dialog(dialog):
    dialog.transition_box.setValue(module.DEFAULT_TRANSITION_LENGTH)
    dialog.radius_box.setValue(module.DEFAULT_RADIUS)
    dialog.angle_box.setValue(module.DEFAULT_TURN_ANGLE)
    dialog.main_width_box.setValue(module.DEFAULT_MAIN_TEMPLATE_WIDTH)
    dialog.parallel_count_box.setValue(1)
    dialog._set_parallel_count(1)
    dialog._populate_row(
        0,
        module.clone_track_config(
            module.DEFAULT_PARALLEL_TRACKS[0],
            module.DEFAULT_TRANSITION_LENGTH,
        ),
    )
    mode_index = dialog.output_mode_box.findText(module.OUTPUT_REPLACE)
    if mode_index < 0:
        raise ValueError("The B14 replace-output choice is unavailable")
    dialog.output_mode_box.setCurrentIndex(mode_index)
    return validate_dialog_values(dialog.values())


def monitor_modal_widgets():
    try:
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if not widget.isVisible():
                continue
            if isinstance(widget, module.CurveInputDialog):
                if state["curve_dialogs"] == 0:
                    state["input_contract"] = configure_dialog(widget)
                    state["curve_dialogs"] += 1
                    widget.accept()
                continue
            if isinstance(widget, QtWidgets.QMessageBox):
                text = str(widget.text() or "")
                title = str(widget.windowTitle() or "")
                if SUCCESS_TEXT in text:
                    state["success_dialogs"] += 1
                else:
                    state["unexpected_dialogs"].append({"title": title, "text": text})
                widget.accept()
    except Exception as error:
        state["monitor_errors"].append(
            "{}: {}".format(type(error).__name__, error)
        )
        for widget in list(QtWidgets.QApplication.topLevelWidgets()):
            if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                widget.reject()


original_read_last_dialog_inputs = module.read_last_dialog_inputs
original_read_material_report_config = module.read_material_report_config
timer = QtCore.QTimer()
timer.setInterval(50)
timer.timeout.connect(monitor_modal_widgets)
module.read_last_dialog_inputs = lambda _document: None
module.read_material_report_config = (
    lambda _settings: module.default_material_report_config()
)
timer.start()
try:
    module.run_macro()
finally:
    timer.stop()
    module.read_last_dialog_inputs = original_read_last_dialog_inputs
    module.read_material_report_config = original_read_material_report_config

if state["monitor_errors"]:
    raise RuntimeError("; ".join(state["monitor_errors"]))
if state["curve_dialogs"] != 1:
    raise RuntimeError("Expected one B14 curve dialog, saw {}".format(state["curve_dialogs"]))
if state["success_dialogs"] != 1:
    raise RuntimeError("Expected one B14 success dialog, saw {}".format(state["success_dialogs"]))
if state["unexpected_dialogs"]:
    raise RuntimeError("Unexpected B14 dialog(s): {}".format(state["unexpected_dialogs"]))

document = App.ActiveDocument
if document is None:
    raise RuntimeError("B14 did not create an active document")
document.recompute()
snapshot = freecad_base_snapshot(module, document)
output_path.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(output_path))
if not output_path.is_file() or output_path.stat().st_size == 0:
    raise RuntimeError("FreeCAD did not save the B14 base fixture")

result = {
    "output": str(output_path),
    "bytes": output_path.stat().st_size,
    "dialog": state,
    "snapshot": snapshot,
}
App.closeDocument(document.Name)
print(json.dumps(result, sort_keys=True))
