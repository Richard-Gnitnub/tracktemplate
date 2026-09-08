#!/usr/bin/env python3
"""Prove complete core conversion and actual main/parallel host callers."""

import ast
import copy
import hashlib
import math
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402


def document_state():
    return {
        name: tuple(obj.Name for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def caller_snapshot():
    """Reuse the exact retained main/matched/manual snapshot helpers."""
    path = ROOT / "tests/freecad_validate_phase3_transition_slice.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {"_normalise", "_caller_snapshot"}
    definitions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert {node.name for node in definitions} == names
    helper_source = "\n".join(
        ast.get_source_segment(source, node) for node in definitions
    )
    digest = hashlib.sha256(helper_source.encode("utf-8")).hexdigest()
    assert digest == (
        "0cf72bf17d63b5e261eaa638ac4d5e8c1b056aa5982acf476ed6dd89fd17e90a"
    )
    namespace = {"copy": copy, "math": math}
    module = ast.Module(body=definitions, type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    print("Inherited main/matched/manual snapshot helpers SHA-256:", digest)
    return namespace["_caller_snapshot"]


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
snapshot = caller_snapshot()
host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
original = core_proof._snapshot(host)
legacy_results = [
    host.module.build_concentric_core(*case)
    for case in core_proof.CALCULATION_CASES
]
legacy_failures = [
    core_proof.failure(host.module.build_concentric_core, case)
    for case in core_proof.INVALID_CASES
]
legacy_snapshot = snapshot(host.module)
functions = core_proof._functions()
for dependency in (
    "clothoid_entry_displacement", "clothoid_exit_displacement",
):
    incomplete = dict(functions)
    incomplete["build_concentric_core"] = core_proof.detached(
        api.build_concentric_core, dependency,
        getattr(host.module, dependency),
    )
    core_proof.centre_proof._expect_error(
        lambda: transition_workflow.ModularTransitionWorkflowSession(
            host, incomplete,
        ),
        "does not use its selected " + repr(dependency),
    )
    assert core_proof._snapshot(host) == original
    assert document_state() == before

for caller_name in ("run_macro", "prepare_track_alignment"):
    caller = getattr(host.module, caller_name)
    setattr(host.module, caller_name, core_proof.detached(
        caller, "build_concentric_core", api.build_concentric_core,
    ))
    core_proof.centre_proof._expect_error(
        lambda: transition_workflow.ModularTransitionWorkflowSession(
            host, functions,
        ),
        "caller " + repr(caller_name) + " is unavailable",
    )
    assert core_proof._snapshot(host) == original
    assert document_state() == before
    setattr(host.module, caller_name, caller)

session = transition_workflow.ModularTransitionWorkflowSession(host, functions)
record = session.routing_record()
assert record["contract_id"] == "tracktemplate:phase7:common-straight-extensions:1"
assert record["schema_version"] == 5 and record["mixed_route"] is False
assert record["function_names"] == list(core_proof.PRODUCT_FUNCTION_NAMES)
assert len(record["caller_names"]) == len(set(record["caller_names"]))
adapter = session.module.build_concentric_core
assert type(adapter) is transition_workflow._ConcentricCoreAdapter
assert adapter.calculation is api.build_concentric_core
assert adapter.vector_factory is App.Vector
for caller_name in ("run_macro", "prepare_track_alignment"):
    caller = getattr(session.module, caller_name)
    assert caller.__globals__ is session.module.__dict__
    assert "build_concentric_core" in caller.__code__.co_names
    assert caller.__globals__["build_concentric_core"] is adapter
for case, legacy in zip(core_proof.CALCULATION_CASES, legacy_results):
    result = adapter(*case)
    assert tuple(result) == tuple(legacy) == core_proof.RESULT_KEYS
    assert result == legacy
    assert all(type(point) is App.Vector for point in result["points"])
    assert all(point.z == 0.0 for point in result["points"])
    assert core_proof.neutral_result(result) == (
        core_proof.neutral_result(legacy)
    ) == api.build_concentric_core(*case)
assert [
    core_proof.failure(adapter, case)
    for case in core_proof.INVALID_CASES
] == legacy_failures
assert snapshot(session.module) == legacy_snapshot
assert document_state() == before

# Instrument the existing endpoint below the adapter without changing any
# arithmetic. The three exact inherited main/matched/manual calls use it.
calls = []


def observed_exit(length, radius, integration_steps=240):
    calls.append((length, radius, integration_steps))
    return api.clothoid_exit_displacement(length, radius, integration_steps)


observed_functions = dict(functions, clothoid_exit_displacement=observed_exit)
observed_functions["build_concentric_core"] = core_proof.detached(
    api.build_concentric_core, "clothoid_exit_displacement", observed_exit,
)
observed_session = transition_workflow.ModularTransitionWorkflowSession(
    host, observed_functions,
)
assert snapshot(observed_session.module) == legacy_snapshot
assert len(calls) == 3
assert all(length > 0.0 and radius > 0.0 for length, radius, _steps in calls)
assert document_state() == before

print("Phase 7 concentric core FreeCAD validation passed")
