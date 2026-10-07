#!/usr/bin/env python3
"""Prove native platform heading/coverage mapping and selected B16 route."""

import hashlib
import json
import math
import os
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_platform_heading_coverage as proof  # noqa: E402


PROFILES = {
    "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2",
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10",
}
SENTINEL = "Phase 7 platform heading and coverage FreeCAD validation passed"


def document_state():
    return {
        "active": getattr(App.ActiveDocument, "Name", None),
        "documents": {
            name: (
                document.Label, document.FileName,
                tuple((obj.Name, obj.TypeId, tuple(obj.State))
                      for obj in document.Objects),
                document.UndoCount, document.RedoCount,
            )
            for name, document in sorted(App.listDocuments().items())
        },
    }


def caller_case(module):
    centre = module.main_circle_centre(600.0, 600.0)
    track = module.build_concentric_core(
        centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track",
    )
    track.update(name="Main Track", width=32.0,
                 create_template=True, show_centreline=True)
    config = {
        "enabled": True, "name": "Platform A", "track_a_index": 0,
        "track_b_index": 0, "arrangement": module.PLATFORM_OUTSIDE,
        "clearance_a": 20.0, "clearance_b": 20.0,
        "platform_length": 100.0, "platform_width": 40.0,
        "body_output": module.PLATFORM_FACE, "platform_height": 2.0,
        "vertical_end_ramps": False, "entry_end_style": "Square",
        "entry_taper_length": 10.0, "exit_end_style": "Square",
        "exit_taper_length": 10.0, "create_edges": True,
        "check_clearance": False, "required_clearance": 17.0,
        "coverage": module.PLATFORM_CORE,
        "centre_offset": 1.0e6,
    }
    return config, [track]


def caller_rejection(caller, config, tracks):
    before = proof.snapshot((config, tracks))
    result = proof.observe(caller, config, tracks, 1.0)
    assert result["exception"] == "ValueError"
    assert "centre offset" in result["message"].lower()
    assert proof.snapshot((config, tracks)) == before
    return result


def validate():
    before = document_state()
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] in PROFILES
    modular_api, bootstrap = launcher["_load_foundation"](ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    )

    def load_host():
        return b15_workflow_host.load_b15_workflow_host(ROOT, contract)

    host = load_host()
    namespace = host.module.__dict__
    native = {name: namespace[name] for name in proof.NAMES}
    native_caller = namespace["calculate_platform_boundaries"]
    b14, _ = proof.legacy_namespace(proof.legacy.B14_PATH, App.Vector)
    b15, _ = proof.legacy_namespace(proof.legacy.B15_PATH, App.Vector)
    expected = proof.cases(b14, vector_factory=App.Vector)
    assert proof.cases(b15, vector_factory=App.Vector) == expected
    assert proof.cases(namespace, vector_factory=App.Vector) == expected
    assert document_state() == before

    config, tracks = caller_case(host.module)
    native_rejection = caller_rejection(native_caller, config, tracks)
    assert document_state() == before

    functions = {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }
    session = transition_workflow.ModularTransitionWorkflowSession(
        host, functions,
    )
    route = session.routing_record()
    assert route["schema_version"] == 16
    assert route["contract_id"] == (
        "tracktemplate:phase7:platform-top-heights:1"
    )
    assert len(route["function_names"]) == 25
    assert len(route["caller_names"]) == 40
    assert proof.cases(namespace, vector_factory=App.Vector) == expected
    assert native_caller.__globals__ is namespace
    assert namespace["calculate_platform_boundaries"] is native_caller
    assert caller_rejection(native_caller, config, tracks) == native_rejection
    for name in proof.NAMES:
        selected = namespace[name]
        assert selected is not native[name]
        namespace[name] = native[name]
        try:
            try:
                session.routing_record()
            except transition_workflow.TransitionWorkflowError:
                pass
            else:
                raise AssertionError("A mixed platform station route passed")
        finally:
            namespace[name] = selected
    assert session.routing_record() == route
    assert document_state() == before

    result = {
        "status": "PASS", "profile": foundation["matched_profile_id"],
        "case_count": len(expected), "native_caller_rejection": native_rejection,
        "routing": route, "document_state_unchanged": True,
        "run_macro_executed": False,
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "tracktemplate/domain/alignment.py", "tracktemplate/api.py",
                "tracktemplate/compatibility/transition_workflow.py",
            )
        },
        "test_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes())
                               .hexdigest(),
    }
    output = os.environ.get("TRACKTEMPLATE_PLATFORM_HEADING_COVERAGE_OUTPUT")
    if output:
        with pathlib.Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase7_platform_heading_coverage"}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - retain exact qualified traceback
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
