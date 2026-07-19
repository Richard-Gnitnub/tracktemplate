"""Validate and fingerprint the active B14 benchmark starting document."""

import json
import sys

import FreeCAD as App

from tools.freecad_bridge.b14_recipe import freecad_base_snapshot

module = sys.modules.get("tracktemplate_b14_session")
if module is None:
    raise RuntimeError("Load B14 before validating its benchmark base")
if App.ActiveDocument is None:
    raise RuntimeError("No active B14 benchmark document is open")

print(json.dumps(freecad_base_snapshot(module, App.ActiveDocument), sort_keys=True))
