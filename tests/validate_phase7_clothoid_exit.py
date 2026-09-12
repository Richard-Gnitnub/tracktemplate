#!/usr/bin/env python3
"""Prove inherited Euler exit endpoints and atomic B16 calculation routing."""

import ast
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
import validate_phase7_main_circle_centre as centre_proof  # noqa: E402


FUNCTION_NAMES = centre_proof.FUNCTION_NAMES + (
    "clothoid_exit_displacement",
)
PRODUCT_FUNCTION_NAMES = FUNCTION_NAMES + (
    "build_concentric_core", "add_common_straight_extensions",
    "build_straight_route",
)
CALCULATION_CASES = tuple(
    (length, radius, steps)
    for length, radius in centre_proof.CALCULATION_CASES
    for steps in (-1, 0, 1, 39, 40, 41, 239, 240, 241, 400, 41.9)
)
RADIUS_DIAGNOSTIC = "A clothoid radius must be greater than zero."


def legacy_calculations(path):
    """Load pure B14/B15 arithmetic without starting FreeCAD or its GUI."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"clothoid_entry_displacement", "clothoid_exit_displacement"}
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
    assert tolerance == 1.0e-8
    namespace = {"math": math, "GEOMETRY_TOLERANCE": tolerance}
    module = ast.Module(body=list(definitions.values()), type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace, definitions


def _check_result(function, entry_function, case):
    length, radius, steps = case
    result = function(*case)
    assert isinstance(result, tuple) and len(result) == 3
    assert all(type(value) is float for value in result)
    if length <= 1.0e-8:
        assert result == (0.0, 0.0, 0.0)
    else:
        dx, dy, angle = result
        assert angle == length / (2.0 * radius)
        # Reverse the entry parameter, reflect Y, then rotate by alpha.
        # theta_exit(1-v) = alpha - theta_entry(v).
        entry_x, entry_y, entry_angle = entry_function(*case)
        assert angle == entry_angle
        expected_x = entry_x * math.cos(angle) + entry_y * math.sin(angle)
        expected_y = entry_x * math.sin(angle) - entry_y * math.cos(angle)
        assert abs(dx - expected_x) <= 1.0e-9
        assert abs(dy - expected_y) <= 1.0e-9
        assert math.hypot(dx, dy) <= length + 1.0e-9
    normalized_steps = max(40, int(steps))
    normalized_steps += normalized_steps % 2
    assert result == function(length, radius, normalized_steps)
    return result


def _check_invalid_radius(function):
    for length in (-1.0, 0.0, 1.0e-9, 1.0e-8, 600.0):
        for radius in (0.0, -600.0):
            try:
                function(length, radius)
            except ValueError as error:
                assert str(error) == RADIUS_DIAGNOSTIC
            else:
                raise AssertionError("Invalid radius was accepted")


def characterize_legacy():
    """Run before extraction; retain this proof for both frozen references."""
    oracles = []
    definitions = []
    for relative, digest in centre_proof.SOURCE_HASHES.items():
        path = ROOT / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        namespace, source = legacy_calculations(path)
        oracles.append(namespace)
        definitions.append(source)
    assert ast.dump(definitions[0]["clothoid_exit_displacement"]) == (
        ast.dump(definitions[1]["clothoid_exit_displacement"])
    )
    for case in CALCULATION_CASES:
        results = [
            _check_result(
                oracle["clothoid_exit_displacement"],
                oracle["clothoid_entry_displacement"], case,
            )
            for oracle in oracles
        ]
        assert results[0] == results[1]
    for oracle in oracles:
        _check_invalid_radius(oracle["clothoid_exit_displacement"])
        assert oracle["clothoid_exit_displacement"](600.0, 600.0) == (
            oracle["clothoid_exit_displacement"](600.0, 600.0, 240)
        )
    print(
        "Phase 7 B14/B15 clothoid exit characterization passed: "
        f"{len(CALCULATION_CASES)} cases"
    )
    return oracles, definitions


def validate_calculations():
    oracles, definitions = characterize_legacy()
    contract = json.loads((
        ROOT / "reference/contracts/phase7-clothoid-exit.json"
    ).read_text(encoding="utf-8"))
    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "tracktemplate:phase7:clothoid-exit:1"
    assert contract["authority"] == ["D-GOV-004", "D-P7-001"]
    assert contract["change_level"] == 2
    assert contract["contract_document"] == (
        "reference/contracts/phase7-clothoid-exit.md"
    )
    for key, value in {
        "module": "tracktemplate.domain.alignment",
        "api": "tracktemplate.api.clothoid_exit_displacement",
        "parameters": ["length", "radius", "integration_steps"],
        "defaults": {"integration_steps": 240},
        "length_unit": "mm",
        "frame": "canonical-local-XY-left-turn-exit-start",
        "heading_unit": "rad",
        "result": ["dx", "dy", "alpha"],
        "geometry_tolerance": 1.0e-8,
        "minimum_integration_steps": 40,
        "integration_step_multiple": 2,
        "theta": "(2.0 * alpha * u) - (alpha * u * u)",
        "alpha": "length / (2.0 * radius)",
        "invalid_radius_diagnostic": RADIUS_DIAGNOSTIC,
    }.items():
        assert contract["calculation"][key] == value, key
    for key, value in {
        "record_schema_version": 3,
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
        assert contract["product_routing"][key] == value, key
    for reference, (relative, digest) in zip(
        ("b14", "b15"), centre_proof.SOURCE_HASHES.items(),
    ):
        assert contract["comparison"][reference + "_path"] == relative
        assert contract["comparison"][reference + "_sha256"] == digest
    assert api.clothoid_exit_displacement is (
        alignment.clothoid_exit_displacement
    )
    assert "clothoid_exit_displacement" in api.__all__
    tree = ast.parse((ROOT / "tracktemplate/domain/alignment.py").read_text())
    modular = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "clothoid_exit_displacement"
    )
    for source in definitions:
        assert centre_proof._mechanical_body(modular) == (
            centre_proof._mechanical_body(source["clothoid_exit_displacement"])
        )
    for case in CALCULATION_CASES:
        result = _check_result(
            api.clothoid_exit_displacement, api.clothoid_entry_displacement,
            case,
        )
        assert all(
            result == oracle["clothoid_exit_displacement"](*case)
            for oracle in oracles
        )
        assert api.clothoid_exit_displacement(*case) == result
    _check_invalid_radius(api.clothoid_exit_displacement)
    assert api.clothoid_exit_displacement(600.0, 600.0) == (
        api.clothoid_exit_displacement(600.0, 600.0, 240)
    )
    fixture = contract["comparison"]["retained_fixture"]
    assert fixture == {
        "length": 600.0,
        "radius": 600.0,
        "result": [560.6304979956861, 194.34313925865808, 0.5],
        "absolute_tolerance": 1.0e-9,
    }
    assert all(
        abs(actual - expected) <= 1.0e-9
        for actual, expected in zip(
            api.clothoid_exit_displacement(600.0, 600.0), fixture["result"],
        )
    )


def _fixture(temporary_root):
    from validate_phase7_concentric_core import _fixture as core_fixture
    return core_fixture(temporary_root)



def _functions():
    return {name: getattr(api, name) for name in PRODUCT_FUNCTION_NAMES}


def _snapshot(host):
    return {
        name: host.module.__dict__[name]
        for name in PRODUCT_FUNCTION_NAMES if name in host.module.__dict__
    }


def detached_core(module, functions, exit_function):
    """Corrupt only the selected domain core's new exit endpoint edge."""
    core = functions["build_concentric_core"]
    namespace = dict(core.__globals__)
    namespace.update(functions)
    namespace["clothoid_exit_displacement"] = exit_function
    return types.FunctionType(core.__code__, namespace)



def validate_binding():
    from validate_phase7_concentric_core import _expected, detached

    prefix = "tracktemplate-phase7-exit-"
    with tempfile.TemporaryDirectory(prefix=prefix) as path:
        temporary_root = pathlib.Path(path)
        contract = _fixture(temporary_root)

        def load_host():
            return host_loader.load_b15_workflow_host(temporary_root, contract)

        expected = _expected()
        session = workflow.load_modular_transition_workflow_session(
            temporary_root, api, contract,
        )
        assert session.launch_workflow() == expected
        record = session.routing_record()
        assert record["schema_version"] == 6
        assert record["contract_id"] == "tracktemplate:phase7:straight-route:1"
        assert record["function_names"] == list(PRODUCT_FUNCTION_NAMES)
        assert record["caller_names"] == [
            "main_circle_centre", "build_concentric_core",
            "prepare_track_alignment", "run_macro", "build_straight_routes",
        ]
        assert record["comparison_route_available"] is False
        core = session.module.build_concentric_core.calculation
        for name in (
            "clothoid_entry_displacement", "clothoid_exit_displacement",
        ):
            assert core.__globals__[name] is getattr(api, name)
        assert session.module.LAUNCH_COUNT == 1

        invalid_maps = [dict(_functions(), unselected=lambda: None)]
        for name in PRODUCT_FUNCTION_NAMES:
            incomplete = _functions()
            incomplete.pop(name)
            invalid_maps.extend((
                incomplete, dict(_functions(), **{name: None}),
            ))
        for invalid in invalid_maps:
            host = load_host()
            before = _snapshot(host)
            centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, invalid,
                ),
                "complete eight-function",
            )
            assert _snapshot(host) == before
            assert host.module.LAUNCH_COUNT == 0

        for remove_previous in (False, True):
            host = load_host()
            old_exit = host.module.clothoid_exit_displacement
            functions = _functions()
            functions["build_concentric_core"] = detached_core(
                host.module, functions, old_exit,
            )
            if remove_previous:
                del host.module.clothoid_exit_displacement
            before = _snapshot(host)
            centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, functions,
                ),
                "does not use its selected 'clothoid_exit_displacement'",
            )
            assert _snapshot(host) == before
            assert host.module.LAUNCH_COUNT == 0

        session.module.clothoid_exit_displacement = None
        centre_proof._expect_error(
            session.routing_record, "mixed 'clothoid_exit_displacement'",
        )
        assert session.module.LAUNCH_COUNT == 1
        assert session.launch_workflow() == expected
        assert session.module.LAUNCH_COUNT == 2

        session.module.prepare_track_alignment = detached(
            session.module.prepare_track_alignment, "build_concentric_core",
            api.build_concentric_core,
        )
        before = _snapshot(session)
        centre_proof._expect_error(
            session.launch_workflow,
            "caller 'prepare_track_alignment' is unavailable",
        )
        assert _snapshot(session) == before
        assert session.module.LAUNCH_COUNT == 2

        missing_api = types.SimpleNamespace(**{
            name: value for name, value in _functions().items()
            if name != "clothoid_exit_displacement"
        })
        centre_proof._expect_error(
            lambda: workflow.load_modular_transition_workflow_session(
                temporary_root / "absent", missing_api, contract,
            ),
            "complete modular transition calculation route",
        )



def main():
    validate_calculations()
    validate_binding()
    print("Phase 7 clothoid exit calculation and routing validation passed")


if __name__ == "__main__":
    main()
