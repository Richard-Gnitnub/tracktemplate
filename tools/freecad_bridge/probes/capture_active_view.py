"""Save a fitted top-view screenshot from the active FreeCAD document."""

import json
import os
import pathlib
import sys

import FreeCAD as App
import FreeCADGui as Gui

try:
    from PySide6 import QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtGui, QtWidgets
    except ImportError:
        from PySide import QtGui
        QtWidgets = QtGui

if App.ActiveDocument is None or Gui.ActiveDocument is None:
    raise RuntimeError("No active FreeCAD document view is available")

output_dir = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"]) / "benchmark-output" / "freecad-bridge" / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "active-document-top.png"
module = next(
    (
        sys.modules.get(name)
        for name in ("tracktemplate_b15_session", "tracktemplate_b14_session")
        if sys.modules.get(name) is not None
    ),
    None,
)
manager = getattr(module, "_automation_trackwork_manager", None) if module else None
manager_was_visible = bool(manager is not None and manager.isVisible())
if manager_was_visible:
    manager.hide()
try:
    main_window = Gui.getMainWindow()
    main_window.showNormal()
    main_window.show()
    main_window.raise_()
    main_window.activateWindow()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    for _iteration in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
    view.saveImage(str(output_path), 1600, 1000, "Current")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("FreeCAD did not create the active-view screenshot")
    image = QtGui.QImage(str(output_path))
    sampled_colours = {
        int(image.pixel(x_pos, y_pos))
        for y_pos in range(0, image.height(), 5)
        for x_pos in range(0, image.width(), 5)
    }
    if len(sampled_colours) < 2:
        raise RuntimeError("The active-view screenshot is a sampled single-colour frame")
finally:
    if manager_was_visible:
        manager.show()
        manager.raise_()
        manager.activateWindow()

print(json.dumps({
    "document": App.ActiveDocument.Name,
    "path": str(output_path),
    "bytes": output_path.stat().st_size,
    "sampled_colour_count": len(sampled_colours),
}, sort_keys=True))
