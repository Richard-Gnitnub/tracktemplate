#!/usr/bin/env python3
"""Exercise the current B16 transition-slice orchestration in FreeCAD."""

import json
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FUNCTION_NAMES = {
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
}


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


before = _document_state()
namespace = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
after = _document_state()
result = namespace.get("FOUNDATION_RESULT")

assert before == after, "current B16 transition loading changed document state"
assert isinstance(result, dict), "current B16 transition result is missing"
assert result.get("schema_version") == 1
assert result.get("development_checkpoint") == "10.2A8A7B16"
assert result.get("status") == "foundation-loaded-not-routed"
assert result.get("matched_profile_id") == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
assert result.get("calculation_routing") == "not-started"
assert result.get("document_mutation") is False
assert FUNCTION_NAMES <= set(result.get("public_api", []))
json.dumps(result, sort_keys=True)

print("Phase 3 transition domain smoke test passed")
