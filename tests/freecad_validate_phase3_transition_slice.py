#!/usr/bin/env python3
"""Exercise modular-only B16 composition and the retained Phase 3 oracle."""

import copy
import json
import math
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase3_transition_pilot  # noqa: E402

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
host_modules_before = tuple(
    name
    for name in sys.modules
    if name.startswith("_tracktemplate_b15_workflow_")
)
assert host_modules_before == ()
namespace = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
result = namespace.get("FOUNDATION_RESULT")

assert isinstance(result, dict), "current B16 transition result is missing"
assert result.get("schema_version") == 1
assert result.get("development_checkpoint") == "10.2A8A7B16"
assert result.get("status") == "modular-foundation-ready"
assert result.get("matched_profile_id") == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
assert result.get("calculation_routing") == "modular"
assert result.get("legacy_comparison_route_available") is False
assert result.get("workflow_host_loaded") is False
assert result.get("workflow_launched") is False
assert result.get("document_mutation") is False
assert "rollback_calculation_routing" not in result
assert "legacy_source_sha256" not in result
assert "routed_function_names" not in result
assert "routed_caller_names" not in result
assert set(FUNCTION_NAMES) <= set(result.get("public_api", []))
json.dumps(result, sort_keys=True)
assert not any(
    name.startswith("_tracktemplate_b15_workflow_")
    for name in sys.modules
), "the default B16 foundation eagerly loaded the B15 host"

api, bootstrap = namespace["_load_foundation"](ROOT)
try:
    namespace["run_macro"]("legacy")
except RuntimeError as error:
    assert "launch_workflow must be a boolean value" in str(error)
else:
    raise AssertionError("B16 accepted the retired legacy route argument")
assert not any(
    name.startswith("_tracktemplate_b15_workflow_")
    for name in sys.modules
), "a rejected legacy route eagerly loaded the B15 host"

transition_contract = bootstrap.load_contract(
    ROOT / "reference" / "contracts" / "phase1-transition-pilot.json"
)
oracle_session = phase3_transition_pilot.load_transition_pilot_session(
    ROOT,
    api,
    transition_contract,
)
legacy_route = oracle_session.apply_route("legacy")
assert tuple(legacy_route["function_names"]) == FUNCTION_NAMES
assert tuple(legacy_route["caller_names"]) == CALLER_NAMES
assert legacy_route["mixed_route"] is False
legacy_snapshot = _caller_snapshot(oracle_session.module)

modular_route = oracle_session.apply_route("modular")
assert modular_route["mixed_route"] is False
modular_snapshot = _caller_snapshot(oracle_session.module)
assert modular_snapshot == legacy_snapshot

rollback_route = oracle_session.apply_route("legacy")
assert rollback_route["mixed_route"] is False
assert _caller_snapshot(oracle_session.module) == legacy_snapshot

product_session, product_route = namespace[
    "_load_modular_transition_workflow"
](
    ROOT,
    api,
    bootstrap,
)
assert product_route == {
    "schema_version": 1,
    "route": "modular",
    "comparison_route_available": False,
    "function_names": list(FUNCTION_NAMES),
    "caller_names": list(CALLER_NAMES),
    "workflow_version": "10.2A8A7B15",
    "workflow_source_sha256": (
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
    ),
    "mixed_route": False,
}
assert _caller_snapshot(product_session.module) == legacy_snapshot
for name in FUNCTION_NAMES:
    assert product_session.module.__dict__[name] is getattr(api, name)
assert before == _document_state(), (
    "B16 retirement or calculation-only parity changed FreeCAD document state"
)

print("Phase 3 transition routing FreeCAD smoke test passed")
