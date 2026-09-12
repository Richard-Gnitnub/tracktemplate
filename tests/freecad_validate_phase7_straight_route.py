#!/usr/bin/env python3
"""Prove native straight-route records and the actual inherited B16 caller."""

import copy
import pathlib
import runpy
import sys

import FreeCAD as App

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_straight_route as proof  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402


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
host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
module = host.module
namespace = module.__dict__
original_builder = module.build_straight_route
original_cloner = module.clone_straight_config
original_identity = module.new_straight_manager_id
clones = []
identities = []


def tracked_clone(config, index=0):
    result = original_cloner(config, index)
    clones.append(result)
    return result


def tracked_identity():
    result = "qualified-{:03d}".format(len(identities) + 1)
    identities.append(result)
    return result


module.clone_straight_config = tracked_clone
module.new_straight_manager_id = tracked_identity
cases = proof.cases(namespace)
for _name, _config, curves in cases:
    for item in curves:
        if "points" in item:
            item["points"] = [
                App.Vector(point.x, point.y, point.z)
                for point in item["points"]
            ]
# Include actual main, parallel and platform Core builder endpoints without
# migrating their preparation or station consumers.
import math  # noqa: E402

centre = module.main_circle_centre(600.0, 600.0)
main = module.build_concentric_core(
    centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track"
)
main.update({"width": 32.0, "name": "Main Track"})
parallel_config = {
    "name": "Outside Track",
    "side": "Outside",
    "alignment_mode": module.MODE_MATCH_SPACINGS,
    "start_spacing": 50.0,
    "curve_spacing": 55.0,
    "finish_spacing": 50.0,
    "entry_transition_length": 600.0,
    "exit_transition_length": 600.0,
    "width": 35.0,
    "create_template": True,
    "show_centreline": True,
}
parallel = module.prepare_track_alignment(
    parallel_config, centre, 600.0, math.pi / 2.0, main
)
platform = module.build_platform_core(
    centre, 655.0, 600.0, 600.0, 0.0, 0.0, math.pi / 2.0, "Platform Track"
)
platform.update({"width": 40.0, "name": "Platform Track"})
for mode in ("Curve entrance", "Curve exit"):
    for label, tracks in (
        ("main-parallel", [main, parallel]),
        ("platform", [platform]),
    ):
        curves = copy.deepcopy(tracks)
        module.add_common_straight_extensions(curves, math.pi / 2.0)
        cases.append(
            (
                f"actual-builders-{mode}-{label}",
                {
                    "manager_id": "actual-builders",
                    "connection_mode": mode,
                    "length": 75.0,
                },
                curves,
            )
        )


def observe(builder, config, curves):
    clones.clear()
    identities.clear()
    old = proof.snapshot((config, curves))
    references = [
        (
            curve,
            curve.get("points"),
            curve.get("headings"),
            tuple(curve.get("points", [])),
        )
        for curve in curves
    ]
    try:
        route = builder(config, curves)
    except (ValueError, TypeError, KeyError) as error:
        result = ("error", type(error).__name__, str(error))
    else:
        result = ("result", proof.snapshot(route))
        if route is not None:
            assert len(clones) == 1 and route["config"] is clones[0]
            assert route["config"] is not config
            assert all(
                type(point) is App.Vector
                for item in route["alignments"]
                for point in item["points"]
            )
            assert all(
                point is not old_point
                for item in route["alignments"]
                for point in item["points"]
                for curve in curves
                for old_point in curve.get("points", [])
            )
            proof.assert_route_geometry(namespace, route, curves)
    assert proof.snapshot((config, curves)) == old
    for curve, points, headings, point_refs in references:
        assert (
            curve["points"] is points if "points" in curve else points is None
        )
        assert (
            curve["headings"] is headings
            if "headings" in curve
            else headings is None
        )
        assert all(
            current is saved
            for current, saved in zip(curve.get("points", []), point_refs)
        )
    return result, list(identities), [proof.snapshot(item) for item in clones]


legacy = [
    observe(original_builder, config, curves)
    for _name, config, curves in cases
]
functions = core_proof._functions()
original = core_proof._snapshot(host)
caller = module.build_straight_routes
module.build_straight_routes = core_proof.detached(
    caller, "build_straight_route", api.build_straight_route
)
core_proof.centre_proof._expect_error(
    lambda: transition_workflow.ModularTransitionWorkflowSession(
        host, functions
    ),
    "caller 'build_straight_routes' is unavailable",
)
assert core_proof._snapshot(host) == original and document_state() == before
module.build_straight_routes = caller
session = transition_workflow.ModularTransitionWorkflowSession(host, functions)
record = session.routing_record()
assert record["schema_version"] == 7
assert record["contract_id"] == "tracktemplate:phase7:station-mapping:1"
assert record["function_names"] == list(functions)
assert record["caller_names"] == list(proof.STATION_CALLER_NAMES)
adapter = module.build_straight_route
assert type(adapter) is transition_workflow._StraightRouteAdapter
assert adapter.calculation is api.build_straight_route
assert adapter.vector_factory is App.Vector
assert adapter.config_cloner is module.clone_straight_config
assert adapter.connected_template_thickness is module.TEMPLATE_THICKNESS
assert caller.__globals__ is namespace
assert caller.__globals__["build_straight_route"] is adapter
assert "build_straight_route" in caller.__code__.co_names
for (name, config, curves), expected in zip(cases, legacy):
    assert observe(adapter, config, curves) == expected, name
assert document_state() == before

calls = []


def observed_calculation(config, curve_alignments, thickness):
    assert config is clones[-1]
    assert thickness is module.TEMPLATE_THICKNESS
    for item in curve_alignments:
        assert tuple(item)[:6] == proof.CURVE_KEYS
        assert set(item) <= {
            *proof.CURVE_KEYS,
            "name",
            "width",
            "create_template",
            "show_centreline",
        }
        assert all(
            item[key] is None or type(item[key]) is tuple
            for key in ("start", "end")
        )
    calls.append((config["manager_id"], len(curve_alignments)))
    return api.build_straight_route(config, curve_alignments, thickness)


observed = dict(functions, build_straight_route=observed_calculation)
observed_session = transition_workflow.ModularTransitionWorkflowSession(
    host, observed
)
clones.clear()
identities.clear()
routes = observed_session.module.build_straight_routes(
    [
        {"manager_id": "same", "name": "Independent", "track_count": 2},
        {
            "manager_id": "same",
            "name": "Entrance",
            "connection_mode": "Curve entrance",
        },
        {
            "manager_id": "exit",
            "name": "Exit",
            "connection_mode": "Curve exit",
        },
        {"manager_id": "disabled", "enabled": False},
    ],
    copy.deepcopy([main]),
)
assert len(routes) == 3 and len(calls) == 4 and len(clones) == 8
assert len({route["route_id"] for route in routes}) == 3
assert [count for _identity, count in calls] == [0, 1, 1, 0]
assert all(
    route["config"] is clones[index] for route, index in zip(routes, (1, 3, 5))
)
assert document_state() == before
# The instrumented host is disposable; restore its original identity helper.
module.new_straight_manager_id = original_identity
print(
    f"Phase 7 straight route FreeCAD validation passed: {len(cases)} cases and actual batch caller"
)
