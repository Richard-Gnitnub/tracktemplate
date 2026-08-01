#!/usr/bin/env python3
"""Exercise the adapter-neutral exact contract in qualified FreeCAD."""

import math
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402


def _document_state():
    return tuple(
        (
            str(name),
            tuple(
                (str(obj.Name), tuple(sorted(obj.PropertiesList)))
                for obj in document.Objects
            ),
            int(document.UndoCount),
            int(document.RedoCount),
        )
        for name, document in sorted(App.listDocuments().items())
    )


def _state():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase6:freecad-exact",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            300.0,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 6 FreeCAD exact transition",
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


qualification = bootstrap.require_qualified_runtime(
    ROOT / "reference" / "contracts" / "phase1-compatibility.json"
)
assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)

before = _document_state()
active_before = App.ActiveDocument
state = _state()
cache = api.TransitionDerivedCache()
specification = api.TransitionExactSpecification(0.05, 64)
artifact = api.regenerate_transition_exact(cache, state, specification)
assert api.regenerate_transition_exact(cache, state, specification) is artifact
assert len(artifact.payload.centreline.points) == 20
assert artifact.payload.result_signature.startswith("sha256:")
assert _document_state() == before
assert App.ActiveDocument is active_before

print("Phase 6 transition exact qualified FreeCAD validation passed")
