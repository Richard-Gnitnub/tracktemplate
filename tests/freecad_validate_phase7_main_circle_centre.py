#!/usr/bin/env python3
"""Prove the bounded centre route on a qualified, unchanged FreeCAD host."""

import pathlib
import runpy
import sys
import types

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_main_circle_centre as centre_proof  # noqa: E402


def document_state():
    return {
        name: tuple(obj.Name for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


before = document_state()
launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
foundation = launcher["FOUNDATION_RESULT"]
assert foundation["status"] == "modular-foundation-ready"
assert foundation["matched_profile_id"] in {
    "linux-x86_64-flatpak-freecad-1.1.1",
    "linux-x86_64-flatpak-freecad-1.1.3",
    "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1",
}
assert foundation["workflow_host_loaded"] is False
api, bootstrap = launcher["_load_foundation"](ROOT)
contract = bootstrap.load_contract(
    ROOT / "reference/contracts/phase1-transition-pilot.json"
)
centre_proof.validate_calculations()

host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
original = {
    name: host.module.__dict__[name]
    for name in centre_proof.PRODUCT_FUNCTION_NAMES
}
legacy_results = [
    host.module.main_circle_centre(*case)
    for case in centre_proof.CALCULATION_CASES
]
functions = {
    name: getattr(api, name) for name in centre_proof.PRODUCT_FUNCTION_NAMES
}
wrong_globals = dict(api.main_circle_centre.__globals__)
wrong_globals["clothoid_entry_displacement"] = lambda *values: None
incomplete_closure = dict(functions)
incomplete_closure["main_circle_centre"] = types.FunctionType(
    api.main_circle_centre.__code__, wrong_globals,
)
centre_proof._expect_error(
    lambda: transition_workflow.ModularTransitionWorkflowSession(
        host, incomplete_closure,
    ),
    "route",
)
assert {
    name: host.module.__dict__[name]
    for name in centre_proof.PRODUCT_FUNCTION_NAMES
} == original
assert document_state() == before

session = transition_workflow.ModularTransitionWorkflowSession(host, functions)
record = session.routing_record()
assert record["contract_id"] == "tracktemplate:phase7:concentric-core:1"
assert record["schema_version"] == 4 and record["mixed_route"] is False
assert session.module.run_macro.__globals__ is session.module.__dict__
assert session.module.run_macro.__globals__["main_circle_centre"] is (
    api.main_circle_centre
)
assert "main_circle_centre" in session.module.run_macro.__code__.co_names
assert [
    session.module.main_circle_centre(*case)
    for case in centre_proof.CALCULATION_CASES
] == legacy_results
assert document_state() == before

print("Phase 7 main-circle-centre FreeCAD validation passed")
