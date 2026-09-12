#!/usr/bin/env python3
"""Prove common-end vector identity and inherited core-layout integration."""

import copy
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
import validate_phase7_common_straight_extensions as proof  # noqa: E402


def document_state():
    return {
        name: tuple(obj.Name for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def host_groups(module):
    groups = proof.calculation_groups(module.__dict__)
    for _name, records, _angle in groups:
        for item in records:
            item["points"] = [
                App.Vector(float(point.x), float(point.y), float(point.z))
                for point in item["points"]
            ]
    angle = math.pi / 2.0
    centre = module.main_circle_centre(600.0, 600.0)
    platform = module.build_platform_core(
        centre, 655.0, 600.0, 600.0, 0.0, 0.0, angle, "Platform Track",
    )
    original = next(
        records for name, records, _angle in groups
        if name == "main-matched-manual"
    )
    groups.append((
        "main-matched-manual-platform",
        copy.deepcopy(original) + [platform], angle,
    ))
    return groups


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
host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
groups = host_groups(host.module)
legacy_groups = copy.deepcopy(groups)
legacy_results = []
for name, records, angle in legacy_groups:
    first = proof.check_host_call(
        host.module.add_common_straight_extensions, records, angle,
    )
    second = proof.check_host_call(
        host.module.add_common_straight_extensions, records, angle,
    )
    legacy_results.append((name, first, second))

functions = proof.core_proof._functions()
original = proof.core_proof._snapshot(host)
runner = host.module.run_macro
host.module.run_macro = proof.core_proof.detached(
    runner, "add_common_straight_extensions",
    api.add_common_straight_extensions,
)
proof.core_proof.centre_proof._expect_error(
    lambda: transition_workflow.ModularTransitionWorkflowSession(
        host, functions,
    ),
    "caller 'run_macro' is unavailable",
)
assert proof.core_proof._snapshot(host) == original
assert document_state() == before
host.module.run_macro = runner

session = transition_workflow.ModularTransitionWorkflowSession(host, functions)
record = session.routing_record()
assert record["contract_id"] == (
    "tracktemplate:phase7:station-mapping:1"
)
assert record["schema_version"] == 7 and record["mixed_route"] is False
assert record["function_names"] == list(proof.core_proof.PRODUCT_FUNCTION_NAMES)
adapter = session.module.add_common_straight_extensions
assert type(adapter) is transition_workflow._CommonStraightExtensionsAdapter
assert adapter.calculation is api.add_common_straight_extensions
assert adapter.vector_factory is App.Vector
assert session.module.run_macro.__globals__ is session.module.__dict__
assert "add_common_straight_extensions" in runner.__code__.co_names
assert runner.__globals__["add_common_straight_extensions"] is adapter

for (name, records, angle), expected in zip(groups, legacy_results):
    first = proof.check_host_call(adapter, records, angle)
    second = proof.check_host_call(adapter, records, angle)
    assert (name, first, second) == expected
    assert all(
        type(point) is App.Vector
        for item in records for point in item["points"]
    )
assert document_state() == before

# Select an observed neutral API while keeping every other route unchanged.
# Actual Generate/Replace reaches this same verified host global in GUI proof.
calls = []


def observed_extensions(alignments, total_angle):
    assert all(
        tuple(item) == ("start", "end", "core_length")
        for item in alignments
    )
    assert all(
        isinstance(item["start"], tuple) and isinstance(item["end"], tuple)
        for item in alignments
    )
    calls.append(len(alignments))
    return api.add_common_straight_extensions(alignments, total_angle)


observed = dict(functions, add_common_straight_extensions=observed_extensions)
observed_session = transition_workflow.ModularTransitionWorkflowSession(
    host, observed,
)
fresh_groups = host_groups(observed_session.module)
for (name, records, angle), expected in zip(fresh_groups, legacy_results):
    first = proof.check_host_call(
        observed_session.module.add_common_straight_extensions, records, angle,
    )
    second = proof.check_host_call(
        observed_session.module.add_common_straight_extensions, records, angle,
    )
    assert (name, first, second) == expected
assert len(calls) == 2 * (len(fresh_groups) - 2)
assert calls[-2:] == [4, 4]
assert document_state() == before

print(
    "Phase 7 common straight extensions FreeCAD validation passed:"
    f" {len(groups)} groups"
)
