"""Save the active FreeCAD Qt dialog into the ignored bridge output area."""

import json
import os
import pathlib

try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets

dialog = QtWidgets.QApplication.activeModalWidget()
if dialog is None:
    active = QtWidgets.QApplication.activeWindow()
    dialog = active if isinstance(active, QtWidgets.QDialog) else None
if dialog is None:
    visible_dialogs = [
        widget for widget in QtWidgets.QApplication.topLevelWidgets()
        if widget.isVisible() and isinstance(widget, QtWidgets.QDialog)
    ]
    dialog = visible_dialogs[-1] if visible_dialogs else None
if dialog is None:
    raise RuntimeError("No visible FreeCAD dialog is available to capture")

output_dir = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"]) / "benchmark-output" / "freecad-bridge" / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "active-dialog.png"
if not dialog.grab().save(str(output_path), "PNG"):
    raise RuntimeError("Qt could not save the active dialog screenshot")

print(json.dumps({
    "class": type(dialog).__name__,
    "title": dialog.windowTitle(),
    "path": str(output_path),
    "width": dialog.width(),
    "height": dialog.height(),
}, sort_keys=True))
