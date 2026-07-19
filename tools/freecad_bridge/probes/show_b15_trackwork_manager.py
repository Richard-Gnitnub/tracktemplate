"""Show B15's trackwork manager non-modally in the dedicated session."""

import json
import sys

import FreeCAD as App

module = sys.modules.get("tracktemplate_b15_session")
if module is None:
    raise RuntimeError("Load B15 with load_b15.py before showing the manager")

manager = getattr(module, "_automation_trackwork_manager", None)
if manager is None:
    document = App.ActiveDocument or App.newDocument("TrackTemplateB15Acceptance")
    manager = module.TurnoutManagerDialog(document)
    module._automation_trackwork_manager = manager
    state = "created"
else:
    state = "reused"

manager.show()
manager.raise_()
manager.activateWindow()
print(json.dumps({
    "state": state,
    "document": manager.doc.Name,
    "window_title": manager.windowTitle(),
    "turnout_count": len(manager.turnouts),
    "crossover_count": len(manager.crossover_panel.crossovers),
}, sort_keys=True))
