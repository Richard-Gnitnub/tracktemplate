"""Capture the deterministic Phase 1 ordinary-track oracle inside FreeCAD."""

import json
import sys

import FreeCAD as App

from tools.freecad_bridge.ordinary_track_recipe import ordinary_track_snapshot


module = sys.modules.get("tracktemplate_b14_session")
if module is None:
    raise RuntimeError("Load B14 before capturing its ordinary-track snapshot")
if App.ActiveDocument is None:
    raise RuntimeError("No B14 ordinary-track document is open")

print(json.dumps(ordinary_track_snapshot(module, App.ActiveDocument), sort_keys=True))
