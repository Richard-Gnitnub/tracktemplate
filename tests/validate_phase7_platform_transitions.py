#!/usr/bin/env python3
"""Prove the complete platform analytical closure and inherited consumers."""

import argparse
import ast
import collections
import copy
import hashlib
import inspect
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import types
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
B14 = ROOT / "AdvancedTurnout.FCMacro"
B15 = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
ANALYTICAL = (
    "platform_transition_displacement", "platform_peak_curvature_factor",
    "platform_transition_angle", "platform_line_offset",
    "_platform_parameter_grid", "solve_platform_shape_parameter",
)
PUBLIC = (ANALYTICAL[0], ANALYTICAL[1], ANALYTICAL[5])
PRIVATE = (ANALYTICAL[2], ANALYTICAL[3], ANALYTICAL[4])
SUPPORT = (
    "vector_xy", "rotate_xy", "left_normal", "dot_xy",
    "integrate_path_segment", "clothoid_entry_displacement",
    "clothoid_exit_displacement", "main_circle_centre",
    "build_concentric_core", "transition_start_signed_offset",
    "solve_transition_length", "signed_side_factor",
    "effective_constant_radius", "build_platform_core",
    "prepare_track_alignment",
)
CONSTANTS = (
    "GEOMETRY_TOLERANCE", "SAMPLE_SPACING", "MODE_PLATFORM",
    "MODE_MATCH_SPACINGS", "MODE_USE_LENGTHS",
)
Vector = collections.namedtuple("Vector", "x y z")
SENTINEL = "Phase 7 platform transition validation passed"
CONTRACT = ROOT / "reference/contracts/phase7-platform-transitions.json"


def snapshot(value):
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in value.items()]
    if hasattr(value, "x") and hasattr(value, "y"):
        return [snapshot(value.x), snapshot(value.y), snapshot(value.z)]
    if isinstance(value, (tuple, list)):
        return [snapshot(item) for item in value]
    if isinstance(value, float):
        return {"float": value.hex()}
    return value


def legacy_namespace(path, vector_factory=Vector):
    tree = ast.parse(path.read_text(), filename=str(path))
    names = set(ANALYTICAL + SUPPORT)
    nodes = {node.name: node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names}
    assert set(nodes) == names
    constants = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id in CONSTANTS
    }
    assert constants["GEOMETRY_TOLERANCE"] == 1.0e-8
    assert constants["SAMPLE_SPACING"] == 3.0
    namespace = {"math": math, "App": types.SimpleNamespace(Vector=vector_factory),
                 **constants}
    exec(compile(ast.Module(body=list(nodes.values()), type_ignores=[]),
                 str(path), "exec"), namespace)
    return namespace, nodes


def observe(function, *args, **kwargs):
    try:
        value = function(*args, **kwargs)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
        return {"exception": type(error).__name__, "message": str(error)}
    return {"value": snapshot(value)}


def analytical_cases(namespace):
    displacement = namespace[ANALYTICAL[0]]
    peak = namespace[ANALYTICAL[1]]
    angle = namespace[ANALYTICAL[2]]
    offset = namespace[ANALYTICAL[3]]
    grid = namespace[ANALYTICAL[4]]
    shapes = (-0.25, -0.187499, -1.0e-16, 0.0, 1.0e-16, 0.5, 2.0)
    rows = []
    for shape in shapes:
        entry = displacement(600.0, 655.0, shape, "entry")
        exiting = displacement(600.0, 655.0, shape, "exit")
        assert entry[2] == exiting[2] == angle(600.0, 655.0, shape)
        assert abs(exiting[0] - (math.cos(entry[2]) * entry[0]
                                + math.sin(entry[2]) * entry[1])) <= 1.0e-8
        assert abs(exiting[1] - (math.sin(entry[2]) * entry[0]
                                - math.cos(entry[2]) * entry[1])) <= 1.0e-8
        scaled = displacement(1200.0, 1310.0, shape, "entry")
        assert scaled == (2.0 * entry[0], 2.0 * entry[1], entry[2])
        assert peak(shape) >= 1.0
        rows.append({"shape": shape, "entry": snapshot(entry),
                     "exit": snapshot(exiting), "peak": snapshot(peak(shape)),
                     "offsets": [snapshot(offset(
                         (31.0, 624.0), 655.0, 600.0, shape,
                         math.pi / 2.0, kind,
                     )) for kind in ("entry", "exit")]})
    assert peak(0.0) == 1.0
    assert displacement(0.0, 1.0, -100.0, "invalid", None) == (0.0, 0.0, 0.0)
    assert angle(0.0, 0.0, None) == 0.0
    boundary = []
    for length in (-1.0, 0.0, 1.0e-8, math.nextafter(1.0e-8, math.inf)):
        boundary.append(observe(displacement, length, 655.0, 0.0, "entry"))
    for steps in (0, 79, 80, 81, 82, 80.9, "81", None, math.inf):
        boundary.append(observe(displacement, 20.0, 655.0, 0.0, "exit", steps))
    assert displacement(20.0, 655.0, 0.0, "exit", 81) == displacement(
        20.0, 655.0, 0.0, "exit", 82,
    )
    for arguments in (
        (0.0, 0.0, -100.0, "invalid"),
        (1.0, 655.0, -0.25 - 1.0e-10, "entry"),
        (1.0, 655.0, math.nextafter(-0.25 - 1.0e-10, -math.inf), "entry"),
        (1.0, 655.0, -100.0, "invalid"),
        (1.0, 655.0, 0.0, "invalid"),
    ):
        boundary.append(observe(displacement, *arguments))
    boundary.extend([observe(angle, 1.0, 0.0, 0.0),
                     observe(offset, (1.0,), 655.0, 0.0, 0.0, 1.0, "entry"),
                     observe(peak, math.nan), observe(peak, math.inf)])
    grids = []
    for lower, upper in ((1.0, 0.0), (-0.25, -0.1), (-0.25, 0.0),
                         (-0.187499, 2.0), (0.0, 2.0), (1.0, 2.0),
                         (0.0, 0.0), (1.0, 1.0)):
        values = grid(lower, upper)
        if upper < lower:
            assert values == []
        else:
            assert values[0] == lower and values[-1] == upper
            assert all(a <= b for a, b in zip(values, values[1:]))
        grids.append({"limits": [lower, upper], "values": snapshot(values)})
    return {"normal": rows, "boundaries": boundary, "grids": grids}


def solver_cases(namespace):
    solve = namespace[ANALYTICAL[5]]
    offset = namespace[ANALYTICAL[3]]
    centre = namespace["main_circle_centre"](600.0, 600.0)
    records = []
    for kind in ("entry", "exit"):
        for shape in (-0.187499, 0.0, 0.5):
            target = offset(centre, 655.0, 600.0, shape, math.pi / 2.0, kind)
            result = solve(centre, 655.0, 600.0, target, math.pi / 2.0,
                           "Platform", kind.title(), kind)
            assert tuple(result) == (
                "shape_parameter", "angle", "peak_factor", "minimum_radius",
            )
            assert result["minimum_radius"] == 655.0 / result["peak_factor"]
            records.append({"kind": kind, "seed_shape": shape,
                            "target": snapshot(target), "result": snapshot(result)})
    diagnostics = []
    for radius, length, target, total, kind in (
        (0.0, -1.0, 0.0, 1.0, "invalid"),
        (655.0, -1.0, 0.0, 1.0, "invalid"),
        (655.0, 6000.0, 0.0, 0.1, "entry"),
        (655.0, 600.0, 1.0e6, math.pi / 2.0, "entry"),
        (655.0, 600.0, 0.0, math.pi / 2.0, "invalid"),
    ):
        diagnostics.append(observe(solve, centre, radius, length, target,
                                   total, "Platform", "Entry", kind))
    zero = offset(centre, 655.0, 0.0, 0.0, math.pi / 2.0, "entry")
    for length, difference in ((0.0, 0.0), (1.0e-8, 0.0), (0.0, 0.5e-6),
                               (0.0, 2.0e-6)):
        diagnostics.append(observe(solve, centre, 655.0, length,
                                   zero + difference, math.pi / 2.0,
                                   "Platform", "Entry", "entry"))
    return {"normal": records, "diagnostics": diagnostics}


def controlled_solver_cases(namespace):
    """Exercise tangent, bracket and ordered candidate decisions explicitly."""
    original = namespace[ANALYTICAL[5]]
    results = []
    for name, grid, residual, peak in (
        ("tangent", [-0.1, 0.0, 0.2], lambda p: (p - 0.037) ** 2,
         lambda _p: 1.0),
        ("bracket", [-0.1, 0.0, 0.2], lambda p: p - 0.037,
         lambda _p: 1.0),
        ("gentlest", [-0.1, 0.0, 0.2], lambda p: p * (p - 0.2),
         lambda p: 2.0 if p < 0.1 else 1.0),
        ("angle-tie", [-0.1, 0.0, 0.2], lambda p: p * (p - 0.2),
         lambda _p: 1.0),
    ):
        calls = []

        def line_offset(_centre, _radius, _length, parameter, _total,
                        _kind, integration_steps=240):
            calls.append([parameter, integration_steps])
            return residual(parameter)

        globals_ = dict(original.__globals__)
        globals_.update(_platform_parameter_grid=lambda _lo, _hi: grid,
                        platform_line_offset=line_offset,
                        platform_peak_curvature_factor=peak)
        solve = types.FunctionType(original.__code__, globals_, original.__name__)
        value = solve((0.0, 0.0), 655.0, 600.0, 0.0, math.pi / 2.0,
                      "Controlled", "Entry", "entry")
        assert 240 in [call[1] for call in calls]
        assert 360 in [call[1] for call in calls]
        if name == "tangent":
            assert abs(value["shape_parameter"] - 0.037) <= 1.0e-8
        if name == "bracket":
            assert 320 in [call[1] for call in calls]
        if name == "gentlest":
            assert value["shape_parameter"] == 0.2
        if name == "angle-tie":
            assert abs(value["shape_parameter"]) <= 1.0e-8
        results.append({"name": name, "calls": snapshot(calls),
                        "result": snapshot(value)})
    return results


def platform_config(**changes):
    config = {
        "name": "Platform Track", "side": "Outside",
        "alignment_mode": "Platform widening", "start_spacing": 40.0,
        "curve_spacing": 55.0, "finish_spacing": 40.0,
        "entry_transition_length": 600.0, "exit_transition_length": 600.0,
        "width": 32.0, "create_template": True, "show_centreline": True,
        "metadata": {"stable_id": "platform-characterisation"},
    }
    config.update(changes)
    return config


def caller_cases(namespace):
    centre = namespace["main_circle_centre"](600.0, 600.0)
    main = namespace["build_concentric_core"](
        centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track",
    )
    before_main = snapshot(main)
    records = []
    configurations = [platform_config(), platform_config(start_spacing=41.0),
                      platform_config(side="Inside", curve_spacing=45.0),
                      platform_config(entry_transition_length=0.0),
                      platform_config(exit_transition_length=0.0),
                      platform_config(start_spacing=0.0),
                      platform_config(start_spacing=1.0e6),
                      platform_config(start_spacing=50.0, finish_spacing=50.0),
                      platform_config(start_spacing=51.0, finish_spacing=50.0)]
    for source in configurations:
        config = copy.deepcopy(source)
        metadata = config["metadata"]
        value = observe(namespace["prepare_track_alignment"], config, centre,
                        600.0, math.pi / 2.0, main)
        assert config["metadata"] is metadata
        assert snapshot(main) == before_main
        records.append({"input": snapshot(source), "after": snapshot(config),
                        "result": value})
    assert "value" in records[0]["result"]
    assert "value" in records[1]["result"]
    for record in records[-2:]:
        assert record["result"]["exception"] == "ValueError"
        assert "cannot be produced" in record["result"]["message"]
    builders = []
    for radius, entry, exiting, entry_shape, exit_shape, total in (
        (655.0, 600.0, 500.0, 0.0, 0.5, math.pi / 2.0),
        (655.0, 0.0, 0.0, 0.0, 0.0, math.pi / 2.0),
        (655.0, 1.0e-8, 1.0e-8, 0.0, 0.0, math.pi / 2.0),
        (0.0, -1.0, -1.0, -1.0, -1.0, -1.0),
        (655.0, -1.0, 0.0, 0.0, 0.0, math.pi / 2.0),
        (655.0, 600.0, 600.0, 2.0, 2.0, 0.1),
    ):
        builders.append(observe(namespace["build_platform_core"], centre,
                                radius, entry, exiting, entry_shape, exit_shape,
                                total, "Platform Builder"))
    return {"prepare": records, "builder": builders}


def characterise(namespace):
    return {"analytical": analytical_cases(namespace),
            "solver": solver_cases(namespace),
            "controlled_solver": controlled_solver_cases(namespace),
            "callers": caller_cases(namespace)}


def _signature_record(function):
    signature = inspect.signature(function)
    return {
        "parameters": list(signature.parameters),
        "defaults": {
            name: parameter.default
            for name, parameter in signature.parameters.items()
            if parameter.default is not inspect.Signature.empty
        },
    }


def _host_independent_import():
    script = """
import importlib.abc
import pathlib
import sys

blocked = {{
    "FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6",
    "PyQt5", "PyQt6", "pivy", "qtpy",
}}
attempted = []

class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in blocked:
            attempted.append(fullname)
            raise ModuleNotFoundError(fullname)
        return None

sys.meta_path.insert(0, Blocker())
sys.path.insert(0, {root!r})
from tracktemplate import api
from tracktemplate.domain import alignment

public = {public!r}
private = {private!r}
assert all(getattr(api, name) is getattr(alignment, name) for name in public)
assert all(name in api.__all__ for name in public)
assert all(not hasattr(api, name) and name not in api.__all__ for name in private)
assert not attempted, attempted
""".format(root=str(ROOT), public=PUBLIC, private=PRIVATE)
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def candidate_characterisation():
    """Exercise the extracted closure and the unchanged actual B16 callers."""
    from tracktemplate import api
    from tracktemplate.compatibility import transition_workflow
    from tracktemplate.domain import alignment as domain

    expected_signatures = {
        "platform_transition_displacement": (
            "length", "radius", "shape_parameter", "transition_kind",
            "integration_steps",
        ),
        "platform_peak_curvature_factor": ("shape_parameter",),
        "platform_transition_angle": (
            "length", "radius", "shape_parameter",
        ),
        "platform_line_offset": (
            "circle_centre", "radius", "length", "shape_parameter",
            "total_angle", "transition_kind", "integration_steps",
        ),
        "_platform_parameter_grid": ("lower", "upper"),
        "solve_platform_shape_parameter": (
            "circle_centre", "radius", "transition_length",
            "target_line_offset", "total_angle", "track_name", "end_name",
            "transition_kind",
        ),
    }
    expected_defaults = {
        "platform_transition_displacement": {"integration_steps": 320},
        "platform_peak_curvature_factor": {},
        "platform_transition_angle": {},
        "platform_line_offset": {"integration_steps": 240},
        "_platform_parameter_grid": {},
        "solve_platform_shape_parameter": {},
    }
    for name in PUBLIC:
        assert getattr(api, name) is getattr(domain, name)
        assert name in api.__all__ and name in domain.__all__
    for name in PRIVATE:
        assert not hasattr(api, name)
        assert name not in api.__all__ and name not in domain.__all__
    for name in ANALYTICAL:
        record = _signature_record(getattr(domain, name))
        assert tuple(record["parameters"]) == expected_signatures[name]
        assert record["defaults"] == expected_defaults[name]

    _host_independent_import()
    caller_namespace, _nodes = legacy_namespace(B15)
    caller_namespace.update({name: getattr(api, name) for name in PUBLIC})
    caller_namespace["build_platform_core"] = (
        transition_workflow._PlatformCoreAdapter(
            api.build_platform_core,
            Vector,
        )
    )
    return {
        "analytical": analytical_cases(domain.__dict__),
        "solver": solver_cases(domain.__dict__),
        "controlled_solver": controlled_solver_cases(domain.__dict__),
        "callers": caller_cases(caller_namespace),
    }


def _source_call_lines(path, caller_name, target_names):
    tree = ast.parse(path.read_text(), filename=str(path))
    caller = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == caller_name
    )
    return {
        target: sorted(
            node.lineno for node in ast.walk(caller)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == target
        )
        for target in target_names
    }


def validate_contract(workflow, routing_record):
    """Tie the machine contract to source, signatures and live composition."""
    contract = json.loads(CONTRACT.read_text())
    assert contract["schema_version"] == 1
    assert contract["contract_id"] == (
        "tracktemplate:phase7:platform-transition:1"
    )
    assert contract["authority"] == ["D-GOV-004", "D-P7-001"]
    assert contract["change_level"] == 2
    assert contract["contract_document"] == (
        "reference/contracts/phase7-platform-transitions.md"
    )

    from tracktemplate.domain import alignment as domain

    calculation = contract["calculation"]
    assert calculation["module"] == "tracktemplate.domain.alignment"
    assert calculation["api"] == [
        "tracktemplate.api." + name for name in PUBLIC
    ]
    assert calculation["public_functions"] == list(PUBLIC)
    assert calculation["internal_functions"] == list(PRIVATE)
    assert calculation["length_unit"] == "mm"
    assert calculation["angle_unit"] == "rad"
    assert calculation["frame"] == "canonical-local-XY-left-turn"
    assert calculation["input_mutation"] is False
    assert calculation["cached"] is False
    assert calculation["canonical_or_persisted_state"] is False
    for name in ANALYTICAL:
        observed = _signature_record(getattr(domain, name))
        recorded = calculation["functions"][name]
        assert recorded["parameters"] == observed["parameters"]
        assert recorded["defaults"] == observed["defaults"]
    numerical_rules = {
        "platform_transition_displacement": {
            "result": ["dx", "dy", "angle"],
            "transition_kinds": ["entry", "exit"],
            "geometry_tolerance": 1.0e-8,
            "minimum_integration_steps": 80,
            "integration_step_multiple": 2,
            "invalid_shape_lower_bound_expression": "-0.25 - 1.0e-10",
            "zero_length_precedes_shape_and_kind_validation": True,
        },
        "platform_peak_curvature_factor": {
            "minimum_result": 1.0,
            "root_zero_tolerance": 1.0e-14,
            "candidate_order": ["u=0.0", "u=1.0", "interior roots"],
        },
        "platform_transition_angle": {
            "geometry_tolerance": 1.0e-8,
            "expression": (
                "(length / radius) * (0.5 + ((8.0 / 15.0) * "
                "shape_parameter))"
            ),
        },
        "platform_line_offset": {
            "normal": "_left_normal(total_angle)",
            "dot_product": "(centre_x * normal_x) + (centre_y * normal_y)",
        },
        "_platform_parameter_grid": {
            "negative_crossing_steps": 36,
            "negative_only_steps": 80,
            "positive_quadratic_steps": 240,
            "endpoint_tolerance": 1.0e-12,
        },
        "solve_platform_shape_parameter": {
            "result_keys": [
                "shape_parameter", "angle", "peak_factor", "minimum_radius",
            ],
            "minimum_shape": -0.187499,
            "maximum_angle_floor": 1.0e-8,
            "maximum_angle_margin": 1.0e-8,
            "grid_integration_steps": 240,
            "golden_integration_steps": 360,
            "bisection_integration_steps": 320,
            "exact_sample_tolerance": 1.0e-7,
            "golden_residual_tolerance": 1.0e-5,
            "golden_iteration_limit": 72,
            "bisection_iteration_limit": 72,
            "bisection_residual_tolerance": 1.0e-10,
            "bisection_parameter_tolerance": 1.0e-9,
            "selection_order": [
                "-minimum_radius", "angle", "abs(shape_parameter)",
            ],
        },
    }
    for name, rules in numerical_rules.items():
        assert {
            key: calculation["functions"][name][key] for key in rules
        } == rules
    assert calculation["dependency_routes"] == [
        {
            "caller": "platform_line_offset",
            "targets": ["platform_transition_displacement"],
        },
        {
            "caller": "solve_platform_shape_parameter",
            "targets": [
                "_platform_parameter_grid", "platform_line_offset",
                "platform_transition_angle",
                "platform_peak_curvature_factor",
            ],
        },
        {
            "nested_caller": (
                "solve_platform_shape_parameter.squared_residual"
            ),
            "targets": ["platform_line_offset"],
            "globals": "same-domain-globals-as-solver",
        },
    ]

    composition = contract["host_composition"]
    assert composition["module"] == (
        "tracktemplate.compatibility.transition_workflow"
    )
    assert composition["new_adapter"] is False
    assert composition["direct_bindings"] == list(PUBLIC)
    assert composition["internal_bindings"] == []
    assert composition["internal_identity_capture"] == list(PRIVATE)
    assert "all fourteen" in composition["atomic_rollback"].lower()
    assert "originally absent" in composition["atomic_rollback"]

    product = contract["product_routing"]
    assert product["record_schema_version"] == 9
    assert routing_record["schema_version"] == 12
    assert product["route"] == routing_record["route"]
    assert product["comparison_route_available"] is False
    historical_names = [
        name for name in workflow.PRODUCT_FUNCTION_NAMES
        if name not in {
            "build_platform_core", "signed_side_factor",
            "effective_constant_radius", "prepare_track_alignment",
            "validate_connected_straight_routes",
        }
    ]
    assert product["function_names"] == historical_names
    assert product["caller_names"] == [
        caller for caller, _targets in workflow.PRODUCT_CALLER_ROUTES
    ]
    historical_routes = []
    for caller, targets in workflow.PRODUCT_CALLER_ROUTES:
        if caller == "prepare_track_alignment":
            targets = tuple(
                target for target in targets
                if target not in {
                    "signed_side_factor", "effective_constant_radius",
                    "build_platform_core",
                }
            )
        elif caller == "run_macro":
            targets = tuple(
                target for target in targets
                if target not in {
                    "prepare_track_alignment", "signed_side_factor",
                    "validate_connected_straight_routes",
                }
            )
        historical_routes.append(
            {"caller": caller, "targets": list(targets)}
        )
    assert product["caller_routes"] == historical_routes
    assert product["complete_current_caller_count"] == 39
    assert product["workflow_version"] == routing_record["workflow_version"]
    assert product["mixed_route"] is False

    source_evidence = contract["source_evidence"]
    assert source_evidence["b14_path"] == B14.name
    assert source_evidence["b15_path"] == B15.name
    assert source_evidence["b14_sha256"] == hashlib.sha256(
        B14.read_bytes(),
    ).hexdigest()
    assert source_evidence["b15_sha256"] == hashlib.sha256(
        B15.read_bytes(),
    ).hexdigest()
    fragment_hashes = []
    definition_ranges = []
    for path in (B14, B15):
        source = path.read_text()
        _namespace, nodes = legacy_namespace(path)
        fragments = "\n\n".join(
            ast.get_source_segment(source, nodes[name]) for name in ANALYTICAL
        )
        fragment_hashes.append(hashlib.sha256(fragments.encode()).hexdigest())
        definition_ranges.append([
            nodes[ANALYTICAL[0]].lineno,
            nodes[ANALYTICAL[-1]].end_lineno,
        ])
    assert len(set(fragment_hashes)) == 1
    assert fragment_hashes[0] == source_evidence[
        "combined_function_fragment_sha256"
    ]
    assert definition_ranges[0] == definition_ranges[1]
    assert definition_ranges[0] == source_evidence["identical_definition_lines"]
    prepare = _source_call_lines(
        B15, "prepare_track_alignment", ("solve_platform_shape_parameter",),
    )
    builder = _source_call_lines(
        B15, "build_platform_core",
        ("platform_transition_displacement", "platform_peak_curvature_factor"),
    )
    assert source_evidence["external_callers"] == [
        {
            "caller": "prepare_track_alignment",
            "calls": [
                {"target": "solve_platform_shape_parameter", "line": line}
                for line in prepare["solve_platform_shape_parameter"]
            ],
        },
        {
            "caller": "build_platform_core",
            "calls": [
                {"target": target, "line": line}
                for target in (
                    "platform_transition_displacement",
                    "platform_peak_curvature_factor",
                )
                for line in builder[target]
            ],
        },
    ]

    scope = contract["scope"]
    assert "Existing comparison and legacy-retirement conditions" in (
        scope["preserved"]
    )
    assert "Performance, phase-exit, output or release acceptance" in (
        scope["excluded"]
    )
    assert scope["deferred_obligation"] == "D-P6-008 unchanged in full"
    validation = contract["validation"]
    assert validation["standalone"] == (
        "tests/validate_phase7_platform_transitions.py"
    )
    assert validation["qualified_host"] == (
        "tests/freecad_validate_phase7_platform_transitions.py"
    )
    assert "both shape solvers" in validation["measurement_boundary"]
    assert "D-GOV-019-qualified B0 PASS" in validation["preimplementation"]


def _binding_state(namespace, names):
    return {
        name: (name in namespace, namespace.get(name)) for name in names
    }


def _assert_binding_state(namespace, expected):
    for name, (present, value) in expected.items():
        assert (name in namespace) is present
        if present:
            assert namespace[name] is value


def validate_binding_and_rollback():
    """Prove the 19-function host route and every platform closure edge."""
    from tracktemplate import api
    from tracktemplate.compatibility import b15_workflow_host as loader
    from tracktemplate.compatibility import transition_workflow as workflow
    from tracktemplate.domain import alignment as domain
    import validate_phase7_concentric_core as core

    def functions():
        return {
            name: getattr(api, name) for name in workflow.PRODUCT_FUNCTION_NAMES
        }

    def require_failure(action, message=None):
        try:
            action()
        except workflow.TransitionWorkflowError as error:
            if message is not None:
                assert message in str(error)
            return
        raise AssertionError("An invalid platform-transition route was accepted")

    with tempfile.TemporaryDirectory(prefix="tracktemplate-platform-") as path:
        temporary_root = pathlib.Path(path)
        host_contract = core._fixture(temporary_root)

        def load_host():
            return loader.load_b15_workflow_host(
                temporary_root, host_contract,
            )

        host = load_host()
        session = workflow.ModularTransitionWorkflowSession(host, functions())
        namespace = session.module.__dict__
        record = session.routing_record()
        assert record == {
            "schema_version": 12,
            "contract_id": "tracktemplate:phase7:connected-straight-validation:1",
            "route": "modular",
            "comparison_route_available": False,
            "function_names": list(workflow.PRODUCT_FUNCTION_NAMES),
            "caller_names": [
                name for name, _targets in workflow.PRODUCT_CALLER_ROUTES
            ],
            "workflow_version": "10.2A8A7B15",
            "workflow_source_sha256": host.source_sha256,
            "mixed_route": False,
        }
        assert len(record["function_names"]) == 19
        assert len(record["caller_names"]) == 39
        for name in PUBLIC:
            assert namespace[name] is getattr(api, name)
        preparation = namespace["prepare_track_alignment"]
        assert type(preparation) is workflow._PrepareTrackAlignmentAdapter
        assert preparation.calculation is api.prepare_track_alignment
        assert preparation.vector_factory is namespace["App"].Vector
        builder = namespace["build_platform_core"]
        assert type(builder) is workflow._PlatformCoreAdapter
        assert builder.calculation is api.build_platform_core
        preparation_globals = api.prepare_track_alignment.__globals__
        assert preparation_globals[PUBLIC[2]] is getattr(api, PUBLIC[2])
        assert preparation_globals["build_platform_core"] is (
            api.build_platform_core
        )

        platform_globals = api.solve_platform_shape_parameter.__globals__
        assert platform_globals is domain.__dict__
        assert all(
            getattr(api, name).__globals__ is platform_globals
            for name in (*PUBLIC, "build_platform_core")
        )
        line_offset = domain.platform_line_offset
        assert line_offset.__globals__ is platform_globals
        assert "platform_transition_displacement" in line_offset.__code__.co_names
        assert platform_globals["platform_transition_displacement"] is (
            api.platform_transition_displacement
        )
        solver = api.solve_platform_shape_parameter
        solver_targets = {
            "_platform_parameter_grid", "platform_line_offset",
            "platform_transition_angle", "platform_peak_curvature_factor",
        }
        assert solver_targets <= set(solver.__code__.co_names)
        for name in solver_targets:
            assert platform_globals[name] is getattr(domain, name)
        nested = [
            item for item in solver.__code__.co_consts
            if isinstance(item, type(solver.__code__))
            and item.co_name == "squared_residual"
        ]
        assert len(nested) == 1
        assert "platform_line_offset" in nested[0].co_names

        for name in workflow.PRODUCT_FUNCTION_NAMES:
            previous = namespace[name]
            namespace[name] = object()
            try:
                require_failure(session.routing_record, "mixed")
            finally:
                namespace[name] = previous
            assert session.routing_record() == record

        for name in (
            "platform_transition_displacement", "_platform_parameter_grid",
            "platform_line_offset", "platform_transition_angle",
            "platform_peak_curvature_factor",
        ):
            previous = platform_globals[name]
            platform_globals[name] = object()
            try:
                require_failure(session.routing_record, "platform")
            finally:
                platform_globals[name] = previous
            assert session.routing_record() == record

        invalid_host = load_host()
        invalid_namespace = invalid_host.module.__dict__
        invalid_before = _binding_state(
            invalid_namespace, workflow.PRODUCT_FUNCTION_NAMES,
        )
        invalid_maps = [dict(functions(), unselected=lambda: None)]
        for name in workflow.PRODUCT_FUNCTION_NAMES:
            missing = functions()
            missing.pop(name)
            invalid_maps.extend((missing, dict(functions(), **{name: None})))
        for candidate in invalid_maps:
            require_failure(
                lambda candidate=candidate: workflow.ModularTransitionWorkflowSession(
                    invalid_host, candidate,
                ),
                "complete nineteen-function",
            )
            _assert_binding_state(invalid_namespace, invalid_before)

        for absent in (None, *workflow.PRODUCT_FUNCTION_NAMES):
            rollback_host = load_host()
            rollback_namespace = rollback_host.module.__dict__
            if absent is not None:
                rollback_namespace.pop(absent, None)
            rollback_before = _binding_state(
                rollback_namespace, workflow.PRODUCT_FUNCTION_NAMES,
            )
            with mock.patch.object(
                workflow.ModularTransitionWorkflowSession,
                "_validate_binding",
                side_effect=RuntimeError("controlled platform setup failure"),
            ):
                try:
                    workflow.ModularTransitionWorkflowSession(
                        rollback_host, functions(),
                    )
                except RuntimeError as error:
                    assert str(error) == "controlled platform setup failure"
                else:
                    raise AssertionError("A controlled binding failure was lost")
            _assert_binding_state(rollback_namespace, rollback_before)

    validate_contract(workflow, record)
    return record


def validate():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    records = {}
    definitions = []
    for label, path in (("b14", B14), ("b15", B15)):
        namespace, nodes = legacy_namespace(path)
        definitions.append({name: ast.dump(node, include_attributes=False)
                            for name, node in nodes.items()})
        records[label] = characterise(namespace)
    assert definitions[0] == definitions[1]
    assert records["b14"] == records["b15"]
    stage = "pre-movement baseline"
    routing = None
    if not args.baseline_only:
        records["candidate"] = candidate_characterisation()
        assert records["candidate"] == records["b15"]
        routing = validate_binding_and_rollback()
        stage = "candidate-equivalence"
    if args.output:
        result = {
            "status": "PASS", "stage": stage,
            "source_sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (B14, B15)
            },
            "records": records,
        }
        if routing is not None:
            result.update({
                "contract_sha256": hashlib.sha256(
                    CONTRACT.read_bytes(),
                ).hexdigest(),
                "routing": routing,
            })
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


if __name__ == "__main__":
    validate()
