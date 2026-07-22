#!/usr/bin/env python3
"""Exercise the current B16 transition-slice orchestration in FreeCAD."""

import copy
import json
import math
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FUNCTION_NAMES = (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)
CALLER_NAMES = (
    "main_circle_centre",
    "build_concentric_core",
    "prepare_track_alignment",
)


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def _normalise(value):
    if isinstance(value, dict):
        return (
            "dict",
            tuple((key, _normalise(value[key])) for key in sorted(value)),
        )
    if isinstance(value, list):
        return ("list", tuple(_normalise(item) for item in value))
    if isinstance(value, tuple):
        return ("tuple", tuple(_normalise(item) for item in value))
    if all(hasattr(value, field) for field in ("x", "y", "z")):
        return ("vector", float(value.x), float(value.y), float(value.z))
    return (type(value).__name__, value)


def _caller_snapshot(module):
    main_transition = 600.0
    main_radius = 600.0
    total_angle = math.pi / 2.0
    circle_centre = module.main_circle_centre(main_transition, main_radius)
    main_alignment = module.build_concentric_core(
        circle_centre,
        main_radius,
        main_transition,
        main_transition,
        total_angle,
        "Main Track",
    )
    match_config = {
        "name": "Outside Track",
        "side": "Outside",
        "alignment_mode": module.MODE_MATCH_SPACINGS,
        "start_spacing": 50.0,
        "curve_spacing": 55.0,
        "finish_spacing": 50.0,
        "entry_transition_length": main_transition,
        "exit_transition_length": main_transition,
        "width": 75.0,
        "create_template": True,
        "show_centreline": True,
    }
    match_alignment = module.prepare_track_alignment(
        match_config,
        circle_centre,
        main_radius,
        total_angle,
        main_alignment,
    )
    manual_config = copy.deepcopy(match_config)
    manual_config["alignment_mode"] = module.MODE_USE_LENGTHS
    manual_alignment = module.prepare_track_alignment(
        manual_config,
        circle_centre,
        main_radius,
        total_angle,
        main_alignment,
    )
    return _normalise(
        {
            "circle_centre": circle_centre,
            "main_alignment": main_alignment,
            "match_config": match_config,
            "match_alignment": match_alignment,
            "manual_config": manual_config,
            "manual_alignment": manual_alignment,
        }
    )


before = _document_state()
namespace = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
result = namespace.get("FOUNDATION_RESULT")

assert isinstance(result, dict), "current B16 transition result is missing"
assert result.get("schema_version") == 1
assert result.get("development_checkpoint") == "10.2A8A7B16"
assert result.get("status") == "transition-routing-ready"
assert result.get("matched_profile_id") == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
assert result.get("calculation_routing") == "modular"
assert result.get("rollback_calculation_routing") == "legacy"
assert tuple(result.get("routed_function_names", ())) == FUNCTION_NAMES
assert tuple(result.get("routed_caller_names", ())) == CALLER_NAMES
assert result.get("mixed_calculation_routing") is False
assert result.get("workflow_launched") is False
assert result.get("document_mutation") is False
assert set(FUNCTION_NAMES) <= set(result.get("public_api", []))
json.dumps(result, sort_keys=True)

api, bootstrap = namespace["_load_foundation"](ROOT)
try:
    namespace["_load_transition_pilot"](
        ROOT,
        api,
        bootstrap,
        "mixed",
    )
except RuntimeError as error:
    assert "Unknown transition calculation route" in str(error)
else:
    raise AssertionError("B16 accepted a mixed transition calculation route")

session, legacy_route = namespace["_load_transition_pilot"](
    ROOT,
    api,
    bootstrap,
    "legacy",
)
assert tuple(legacy_route["function_names"]) == FUNCTION_NAMES
assert tuple(legacy_route["caller_names"]) == CALLER_NAMES
assert legacy_route["mixed_route"] is False
legacy_snapshot = _caller_snapshot(session.module)

modular_route = session.apply_route("modular")
assert modular_route["mixed_route"] is False
modular_snapshot = _caller_snapshot(session.module)
assert modular_snapshot == legacy_snapshot

rollback_route = session.apply_route("legacy")
assert rollback_route["mixed_route"] is False
assert _caller_snapshot(session.module) == legacy_snapshot
assert before == _document_state(), (
    "B16 routing or calculation-only caller parity changed FreeCAD document state"
)

print("Phase 3 transition routing FreeCAD smoke test passed")
