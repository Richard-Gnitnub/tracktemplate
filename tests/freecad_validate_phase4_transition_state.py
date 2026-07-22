#!/usr/bin/env python3
"""Exercise the Phase 4 canonical-state foundation in qualified FreeCAD."""

import math
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


before = _document_state()
qualification = bootstrap.require_qualified_runtime(
    ROOT / "reference" / "contracts" / "phase1-compatibility.json"
)
circle_centre_y_mm = 624.7779655573173
radius_mm = 655.0
intent = api.TransitionIntent(
    transition_id="transition:phase4:freecad-smoke",
    circle_centre_y_mm=circle_centre_y_mm,
    radius_mm=radius_mm,
    target_signed_offset_mm=api.transition_start_signed_offset(
        circle_centre_y_mm,
        radius_mm,
        300.0,
    ),
    total_angle_rad=math.pi / 2.0,
    track_name="Phase 4 smoke",
    end_name="Entry",
)
analysed = api.analyse_transition_state(api.TransitionState(intent=intent))
encoded = api.transition_state_to_json(analysed)
reopened = api.transition_state_from_json(encoded)
after = _document_state()

assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
assert reopened == analysed
assert api.transition_state_to_json(reopened) == encoded
assert before == after, "canonical-state smoke changed FreeCAD document state"

print("Phase 4 transition canonical-state FreeCAD smoke test passed")
