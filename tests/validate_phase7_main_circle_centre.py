#!/usr/bin/env python3
"""Prove the bounded main-circle calculation and atomic product route."""

import ast
import copy
import hashlib
import json
import math
import pathlib
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host as host_loader,
    transition_workflow as workflow,
)
from tracktemplate.domain import alignment  # noqa: E402
import validate_phase3_transition_routing as phase3_fixture  # noqa: E402


FUNCTION_NAMES = (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
    "main_circle_centre",
)
PRODUCT_FUNCTION_NAMES = FUNCTION_NAMES + (
    "clothoid_exit_displacement", "build_concentric_core",
    "add_common_straight_extensions", "build_straight_route",
)
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
CALCULATION_CASES = tuple(
    (length, radius)
    for radius in (150.0, 600.0, 1200.0, 6000.0)
    for length in (
        -1.0, 0.0, 1.0e-9, 1.0e-8,
        math.nextafter(1.0e-8, math.inf), 1.0e-7,
        25.0, 420.0, 600.0, 900.0,
    )
)


def legacy_calculation(path):
    """Load only the frozen numeric definitions, without importing a host."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {
        "left_normal", "clothoid_entry_displacement", "main_circle_centre",
    }
    definitions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    }
    assert set(definitions) == names
    tolerance = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "GEOMETRY_TOLERANCE"
            for target in node.targets
        )
    )
    namespace = {"math": math, "GEOMETRY_TOLERANCE": tolerance}
    module = ast.Module(body=list(definitions.values()), type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace, definitions


def _mechanical_body(node):
    node = copy.deepcopy(node)
    if (
        node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        node.body.pop(0)
    if node.name == "_left_normal":
        node.name = "left_normal"
    for item in ast.walk(node):
        if isinstance(item, ast.Name) and item.id == "_left_normal":
            item.id = "left_normal"
    return ast.dump(node, include_attributes=False)


def validate_calculations():
    contract = json.loads((
        ROOT / "reference/contracts/phase7-main-circle-centre.json"
    ).read_text(encoding="utf-8"))
    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "tracktemplate:phase7:main-circle-centre:1"
    assert contract["authority"] == "D-P7-001"
    assert contract["change_level"] == 2
    calculation = contract["calculation"]
    for field, expected_value in {
        "module": "tracktemplate.domain.alignment",
        "api": "tracktemplate.api.main_circle_centre",
        "parameters": ["main_transition", "main_radius"],
        "defaults": {},
        "length_unit": "mm",
        "frame": "canonical-local-XY-left-turn",
        "heading_unit": "rad",
        "private_helper": "_left_normal",
        "endpoint_function": "clothoid_entry_displacement",
        "integration_steps": 240,
        "geometry_tolerance": 1.0e-8,
        "left_normal": ["-sin(heading)", "cos(heading)"],
        "centre": [
            "x_end + (main_radius * normal_x)",
            "y_end + (main_radius * normal_y)",
        ],
    }.items():
        assert calculation[field] == expected_value, field
    for field, expected_value in {
        "record_schema_version": 2,
        "route": "modular",
        "comparison_route_available": False,
        "function_names": list(FUNCTION_NAMES),
        "caller_names": [
            "main_circle_centre", "build_concentric_core",
            "prepare_track_alignment", "run_macro", "build_straight_routes",
        ],
        "workflow_version": "10.2A8A7B15",
        "mixed_route": False,
    }.items():
        assert contract["product_routing"][field] == expected_value, field
    assert api.main_circle_centre is alignment.main_circle_centre
    assert "main_circle_centre" in api.__all__
    assert "_left_normal" not in api.__all__
    modular_tree = ast.parse(
        (ROOT / "tracktemplate/domain/alignment.py").read_text()
    )
    modular = {
        node.name: node for node in modular_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    oracles = []
    for reference, (relative, digest) in zip(
        ("b14", "b15"), SOURCE_HASHES.items(),
    ):
        assert contract["comparison"][reference + "_path"] == relative
        assert contract["comparison"][reference + "_sha256"] == digest
        path = ROOT / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        namespace, definitions = legacy_calculation(path)
        oracles.append(namespace)
        for legacy_name, modular_name in (
            ("left_normal", "_left_normal"),
            ("main_circle_centre", "main_circle_centre"),
        ):
            assert _mechanical_body(definitions[legacy_name]) == (
                _mechanical_body(modular[modular_name])
            )

    for length, radius in CALCULATION_CASES:
        actual = api.main_circle_centre(length, radius)
        assert isinstance(actual, tuple) and len(actual) == 2
        assert all(type(value) is float for value in actual)
        assert all(
            actual == oracle["main_circle_centre"](length, radius)
            for oracle in oracles
        )
        endpoint_x, endpoint_y, heading = api.clothoid_entry_displacement(
            length, radius,
        )
        normal_x = actual[0] - endpoint_x
        normal_y = actual[1] - endpoint_y
        assert abs(math.hypot(normal_x, normal_y) - radius) <= 1.0e-9
        assert abs(
            normal_x * math.cos(heading) + normal_y * math.sin(heading)
        ) <= 1.0e-9
        assert normal_y * math.cos(heading) - normal_x * math.sin(heading) > 0
        assert api.main_circle_centre(length, radius) == actual

    expected = (297.51728975552163, 624.7779655573173)
    assert contract["comparison"]["retained_fixture"] == {
        "main_transition": 600.0,
        "main_radius": 600.0,
        "centre": list(expected),
        "absolute_tolerance": 1.0e-9,
    }
    assert all(
        abs(actual - target) <= 1.0e-9
        for actual, target in zip(
            api.main_circle_centre(600.0, 600.0), expected,
        )
    )
    for radius in (0.0, -600.0):
        messages = []
        for function in (
            api.main_circle_centre,
            *(oracle["main_circle_centre"] for oracle in oracles),
        ):
            try:
                function(600.0, radius)
            except ValueError as error:
                messages.append(str(error))
            else:
                raise AssertionError("Invalid radius was accepted")
        assert messages == [
            "A clothoid radius must be greater than zero."
        ] * 3
        assert messages[0] == calculation["invalid_radius_diagnostic"]


def _functions():
    return {name: getattr(api, name) for name in PRODUCT_FUNCTION_NAMES}


def _fixture(temporary_root):
    from validate_phase7_concentric_core import _fixture as core_fixture
    return core_fixture(temporary_root)



def _expect_error(action, text):
    try:
        action()
    except workflow.TransitionWorkflowError as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected TransitionWorkflowError: " + text)


def _snapshot(host):
    return {name: host.module.__dict__[name] for name in PRODUCT_FUNCTION_NAMES}


def validate_binding():
    prefix = "tracktemplate-phase7-centre-"
    with tempfile.TemporaryDirectory(prefix=prefix) as path:
        temporary_root = pathlib.Path(path)
        contract = _fixture(temporary_root)

        def load_host():
            return host_loader.load_b15_workflow_host(temporary_root, contract)

        session = workflow.load_modular_transition_workflow_session(
            temporary_root, api, contract,
        )
        from validate_phase7_concentric_core import _expected
        expected_centre = _expected()
        assert session.launch_workflow() == expected_centre
        assert session.module.LAUNCH_COUNT == 1
        assert session.module.run_macro.__globals__["main_circle_centre"] is (
            api.main_circle_centre
        )
        assert session.routing_record()["schema_version"] == 6
        assert session.routing_record()["contract_id"] == (
            "tracktemplate:phase7:straight-route:1"
        )
        assert session.routing_record()["function_names"] == list(
            PRODUCT_FUNCTION_NAMES
        )
        assert session.routing_record()["caller_names"] == [
            "main_circle_centre", "build_concentric_core",
            "prepare_track_alignment", "run_macro", "build_straight_routes",
        ]
        assert session.routing_record()["comparison_route_available"] is False

        for invalid in (
            {name: value for name, value in _functions().items()
             if name != "main_circle_centre"},
            dict(_functions(), main_circle_centre=None),
            dict(_functions(), unselected=lambda: None),
        ):
            host = load_host()
            before = _snapshot(host)
            _expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, invalid,
                ),
                "complete eight-function",
            )
            assert _snapshot(host) == before and host.module.LAUNCH_COUNT == 0

        for name, dependency in (
            ("main_circle_centre", "clothoid_entry_displacement"),
            ("solve_transition_length", "transition_start_signed_offset"),
        ):
            host = load_host()
            before = _snapshot(host)
            functions = _functions()
            function = functions[name]
            wrong_globals = dict(function.__globals__)
            wrong_globals[dependency] = lambda *arguments: None
            functions[name] = types.FunctionType(
                function.__code__, wrong_globals,
            )
            _expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, functions,
                ),
                "route",
            )
            assert _snapshot(host) == before and host.module.LAUNCH_COUNT == 0

        host = load_host()
        before = _snapshot(host)
        runner = host.module.run_macro
        host.module.run_macro = types.FunctionType(
            runner.__code__, dict(runner.__globals__),
        )
        _expect_error(
            lambda: workflow.ModularTransitionWorkflowSession(
                host, _functions(),
            ),
            "caller 'run_macro' is unavailable",
        )
        assert _snapshot(host) == before and host.module.LAUNCH_COUNT == 0

        session.module.main_circle_centre = lambda *arguments: None
        _expect_error(session.routing_record, "mixed 'main_circle_centre'")
        assert session.module.LAUNCH_COUNT == 1
        assert session.launch_workflow() == expected_centre
        assert session.module.LAUNCH_COUNT == 2

        missing_api = types.SimpleNamespace(**{
            name: value for name, value in _functions().items()
            if name != "main_circle_centre"
        })
        _expect_error(
            lambda: workflow.load_modular_transition_workflow_session(
                temporary_root / "absent", missing_api, contract,
            ),
            "complete modular transition calculation route",
        )


def main():
    validate_calculations()
    validate_binding()
    print(
        "Phase 7 main-circle-centre calculation and routing validation passed"
    )


if __name__ == "__main__":
    main()
