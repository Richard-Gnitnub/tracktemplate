#!/usr/bin/env python3
"""Prove complete Euler-circle-Euler results and bounded host conversion."""

import ast
import collections
import copy
import hashlib
import inspect
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
import validate_phase7_main_circle_centre as centre_proof  # noqa: E402


Vector = collections.namedtuple("Vector", "x y z")
LEGACY_NAMES = {
    "vector_xy", "rotate_xy", "left_normal", "integrate_path_segment",
    "clothoid_entry_displacement", "clothoid_exit_displacement",
    "main_circle_centre", "build_concentric_core",
    "transition_start_signed_offset", "solve_transition_length",
}
RESULT_KEYS = (
    "label", "points", "headings", "start", "end", "radius",
    "entry_transition", "exit_transition", "entry_angle", "exit_angle",
    "circular_angle", "circular_length", "core_length",
)
PARAMETERS = (
    "circle_centre", "radius", "entry_transition", "exit_transition",
    "total_angle", "label",
)
FUNCTION_NAMES = (
    "clothoid_entry_displacement", "transition_start_signed_offset",
    "solve_transition_length", "main_circle_centre",
    "clothoid_exit_displacement", "build_concentric_core",
)
TRANSITION_CASES = (
    (0.0, 0.0), (0.0, 25.0), (25.0, 0.0), (25.0, 60.0),
    (60.0, 25.0), (420.0, 600.0), (1.0e-9, 1.0e-8),
    (1.0e-8, math.nextafter(1.0e-8, math.inf)),
    (math.nextafter(1.0e-8, math.inf), 1.0e-8), (600.0, 600.0),
)
CALCULATION_CASES = tuple(
    (centre, radius, entry, exit_length,
     (entry + exit_length) / (2.0 * radius) + circular_angle, "Core test")
    for centre in ((0.0, 0.0), (297.51728975552163, 624.7779655573173))
    for radius in (150.0, 600.0, 6000.0)
    for entry, exit_length in TRANSITION_CASES
    for circular_angle in (0.0, 0.4, math.pi)
) + (
    ((0.0, 600.0), 600.0, 0.0, 0.0, -5.0e-10, "Clamped angle"),
    ((0.0, 600.0), 600.0, 600.0, 600.0, 1.0 - 5.0e-10,
     "Clamped angle"),
    ((0.0, 600.0), 600.0, 0.0, 0.0, 1.0e-8 / 600.0,
     "Circular tolerance"),
    ((0.0, 600.0), 600.0, 0.0, 0.0,
     math.nextafter(1.0e-8 / 600.0, math.inf), "Circular tolerance"),
)
INVALID_CASES = (
    ((0.0, 0.0), 0.0, -1.0, -1.0, -1.0, "Radius first"),
    ((0.0, 0.0), -600.0, 600.0, 600.0, 2.0, "Negative radius"),
    ((0.0, 600.0), 600.0, -1.0, 0.0, 2.0, "Entry negative"),
    ((0.0, 600.0), 600.0, 0.0, -1.0, 2.0, "Exit negative"),
    ((0.0, 600.0), 600.0, -1.0e-12, 0.0, 2.0, "Tiny negative"),
    ((0.0, 600.0), 600.0, 600.0, 600.0, 0.5, "Excess angle"),
    ((0.0, 600.0), 600.0, 0.0, 0.0, -2.0e-9, "Negative angle"),
    ((0.0,), 600.0, 0.0, 0.0, 1.0, "Centre missing"),
    ((0.0, 600.0, 0.0), 600.0, 0.0, 0.0, 1.0, "Centre excess"),
)


def legacy_calculations(path):
    """Load frozen definitions with only the vector constructor stubbed."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in LEGACY_NAMES
    }
    assert set(definitions) == LEGACY_NAMES
    constants = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id in {"GEOMETRY_TOLERANCE", "SAMPLE_SPACING"}
    }
    assert constants == {
        "GEOMETRY_TOLERANCE": 1.0e-8, "SAMPLE_SPACING": 3.0,
    }
    namespace = {"math": math, "App": types.SimpleNamespace(Vector=Vector)}
    namespace.update(constants)
    module = ast.Module(body=list(definitions.values()), type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace, definitions


def neutral_result(result):
    """Keep all mapping and list order while normalizing host coordinates."""
    result = dict(result)
    result["points"] = [
        (point.x, point.y) if hasattr(point, "x") else point
        for point in result["points"]
    ]
    return result


def failure(function, case):
    try:
        function(*case)
    except Exception as error:
        return type(error).__name__, str(error)
    raise AssertionError("Invalid core input was accepted: " + repr(case))


def check_invariants(result, case):
    centre, radius, entry, exit_length, total_angle, label = case
    result = neutral_result(result)
    assert tuple(result) == RESULT_KEYS
    assert isinstance(result["points"], list)
    assert isinstance(result["headings"], list)
    assert len(result["points"]) == len(result["headings"])
    assert all(
        isinstance(point, tuple) and len(point) == 2
        and all(type(value) is float for value in point)
        for point in result["points"]
    )
    assert result["label"] == label
    assert result["radius"] == radius
    assert result["entry_transition"] == entry
    assert result["exit_transition"] == exit_length
    assert result["entry_angle"] == entry / (2.0 * radius)
    assert result["exit_angle"] == exit_length / (2.0 * radius)
    circular_angle = max(
        0.0, total_angle - result["entry_angle"] - result["exit_angle"],
    )
    assert result["circular_angle"] == circular_angle
    assert result["circular_length"] == radius * circular_angle
    assert result["core_length"] == (
        entry + radius * circular_angle + exit_length
    )
    assert result["headings"][-1] == total_angle
    assert result["points"][-1] == result["end"]
    expected_count = 1 + sum(
        max(1, int(math.ceil(length / 3.0)))
        for length in (entry, radius * circular_angle, exit_length)
        if length > 1.0e-8
    )
    assert len(result["points"]) == expected_count
    if entry == exit_length == 0.0:
        for x, y in result["points"]:
            assert abs(
                math.hypot(x - centre[0], y - centre[1]) - radius
            ) < 1.0e-8
    return result


def characterize_legacy():
    """Run before extraction and retain complete ordered output identity."""
    oracles = []
    definitions = []
    for relative, digest in centre_proof.SOURCE_HASHES.items():
        path = ROOT / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        namespace, nodes = legacy_calculations(path)
        oracles.append(namespace)
        definitions.append(nodes)
    for name in LEGACY_NAMES:
        assert ast.dump(definitions[0][name]) == ast.dump(definitions[1][name])
    digest = hashlib.sha256()
    for case in CALCULATION_CASES:
        results = [
            check_invariants(oracle["build_concentric_core"](*case), case)
            for oracle in oracles
        ]
        assert results[0] == results[1]
        digest.update(repr((case, results[0])).encode("utf-8"))
    failures = []
    for case in INVALID_CASES:
        messages = [
            failure(oracle["build_concentric_core"], case)
            for oracle in oracles
        ]
        assert messages[0] == messages[1]
        failures.append({"case": case, "failure": messages[0]})
    print(json.dumps({
        "characterization": "PASS", "cases": len(CALCULATION_CASES),
        "invalid_cases": failures, "ordered_result_sha256": digest.hexdigest(),
        "source_sha256": centre_proof.SOURCE_HASHES,
    }, sort_keys=True))
    print("Phase 7 B14/B15 concentric core characterization passed")
    return oracles, definitions




def _mechanical_body(node):
    """Allow only private names and neutral replacement of vector creation."""
    node = copy.deepcopy(node)
    if (
        node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        node.body.pop(0)
    renames = {
        "_rotate_xy": "rotate_xy",
        "_left_normal": "left_normal",
        "_integrate_core_segment": "integrate_path_segment",
        "_CORE_SAMPLE_SPACING": "SAMPLE_SPACING",
    }
    node.name = renames.get(node.name, node.name)

    class Normalize(ast.NodeTransformer):
        def visit_Name(self, item):
            item.id = renames.get(item.id, item.id)
            return item

        def visit_Call(self, item):
            self.generic_visit(item)
            if isinstance(item.func, ast.Name) and item.func.id == "vector_xy":
                return ast.Tuple(
                    elts=[
                        ast.Call(
                            func=ast.Name(id="float", ctx=ast.Load()),
                            args=[value], keywords=[],
                        )
                        for value in item.args
                    ],
                    ctx=ast.Load(),
                )
            return item

    return ast.dump(Normalize().visit(node), include_attributes=False)


def validate_calculations():
    oracles, definitions = characterize_legacy()
    assert api.build_concentric_core is alignment.build_concentric_core
    assert "build_concentric_core" in api.__all__
    assert tuple(inspect.signature(api.build_concentric_core).parameters) == (
        PARAMETERS
    )
    signature = inspect.signature(api.build_concentric_core)
    assert all(
        item.default is inspect.Parameter.empty
        for item in signature.parameters.values()
    )
    tree = ast.parse((ROOT / "tracktemplate/domain/alignment.py").read_text())
    nodes = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    for legacy, modular in (
        ("rotate_xy", "_rotate_xy"),
        ("integrate_path_segment", "_integrate_core_segment"),
        ("build_concentric_core", "build_concentric_core"),
    ):
        assert modular not in api.__all__ or modular == "build_concentric_core"
        for source in definitions:
            assert _mechanical_body(source[legacy]) == (
                _mechanical_body(nodes[modular])
            ), legacy
    for case in CALCULATION_CASES:
        result = api.build_concentric_core(*case)
        assert check_invariants(result, case) == result
        assert all(
            result == neutral_result(oracle["build_concentric_core"](*case))
            for oracle in oracles
        )
        repeated = api.build_concentric_core(*case)
        assert repeated == result
        assert repeated is not result
        assert repeated["points"] is not result["points"]
        assert repeated["headings"] is not result["headings"]
    for case in INVALID_CASES:
        assert failure(api.build_concentric_core, case) == failure(
            oracles[0]["build_concentric_core"], case,
        )
    # Translation changes only positions. The circular-only result also
    # supplies an independent, directly checkable circle-radius invariant.
    original_case = ((0.0, 600.0), 600.0, 25.0, 60.0, 1.5, "Translation")
    shifted_case = ((100.0, 350.0), *original_case[1:])
    original = api.build_concentric_core(*original_case)
    shifted = api.build_concentric_core(*shifted_case)
    assert shifted["headings"] == original["headings"]
    for a, b in zip(original["points"], shifted["points"]):
        assert abs(b[0] - a[0] - 100.0) <= 1.0e-9
        assert abs(b[1] - a[1] + 250.0) <= 1.0e-9
    contract = json.loads((
        ROOT / "reference/contracts/phase7-concentric-core.json"
    ).read_text())
    assert contract["contract_id"] == "tracktemplate:phase7:concentric-core:1"
    assert contract["schema_version"] == 1
    assert contract["authority"] == ["D-GOV-004", "D-P7-001"]
    assert contract["change_level"] == 2
    assert contract["calculation"]["parameters"] == list(PARAMETERS)
    assert contract["calculation"]["result_keys"] == list(RESULT_KEYS)
    assert contract["calculation"]["sample_spacing_mm"] == 3.0
    assert contract["calculation"]["geometry_tolerance"] == 1.0e-8
    assert contract["calculation"]["circular_angle_rejection_rad"] == -1.0e-9
    assert contract["calculation"]["curvature_zero_threshold"] == 1.0e-14
    assert contract["product_routing"]["record_schema_version"] == 4
    assert contract["product_routing"]["function_names"] == (
        list(FUNCTION_NAMES)
    )


def _functions():
    return {name: getattr(api, name) for name in FUNCTION_NAMES}


def _snapshot(host):
    return {
        name: host.module.__dict__[name]
        for name in FUNCTION_NAMES if name in host.module.__dict__
    }


def detached(function, dependency, replacement):
    namespace = dict(function.__globals__)
    namespace[dependency] = replacement
    return types.FunctionType(
        function.__code__, namespace, function.__name__, function.__defaults__,
        function.__closure__,
    )


def _fixture(temporary_root):
    """Use exact frozen calculations and a minimal executable host entry."""
    path = ROOT / "AdvancedTurnout.FCMacro"
    _namespace, nodes = legacy_calculations(path)
    prelude = (
        'import math\nfrom collections import namedtuple\n'
        'from types import SimpleNamespace\n'
        'App = SimpleNamespace(Vector=namedtuple("Vector", "x y z"))\n'
        'MACRO_VERSION_NUMBER = "10.2A8A7B15"\n'
        'GEOMETRY_TOLERANCE = 1.0e-8\nSAMPLE_SPACING = 3.0\n'
        'LAUNCH_COUNT = 0\n'
    )
    callers = (
        'def prepare_track_alignment():\n'
        '    offset = transition_start_signed_offset(600.0, 600.0, 0.0)\n'
        '    length = solve_transition_length(600.0, 600.0, offset,\n'
        '        math.pi / 2.0, "Fixture", "Entry")\n'
        '    return build_concentric_core((0.0, 600.0), 600.0, length,\n'
        '        length, math.pi / 2.0, "Fixture")\n'
        'def run_macro():\n'
        '    global LAUNCH_COUNT\n'
        '    LAUNCH_COUNT += 1\n'
        '    centre = main_circle_centre(600.0, 600.0)\n'
        '    core = build_concentric_core(centre, 600.0, 600.0, 600.0,\n'
        '        math.pi / 2.0, "Main Track")\n'
        '    return centre, core\n'
        'run_macro()\n'
    )
    source = temporary_root / "legacy.FCMacro"
    source.write_text(
        prelude + "\n".join(ast.unparse(node) for node in nodes.values())
        + "\n" + callers,
    )
    return centre_proof.phase3_fixture._contract(source)


def _expected():
    centre = api.main_circle_centre(600.0, 600.0)
    core = api.build_concentric_core(
        centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track",
    )
    core["points"] = [Vector(x, y, 0.0) for x, y in core["points"]]
    return centre, core


def validate_binding():
    prefix = "tracktemplate-phase7-core-"
    with tempfile.TemporaryDirectory(prefix=prefix) as path:
        temporary_root = pathlib.Path(path)
        contract = _fixture(temporary_root)

        def load_host():
            return host_loader.load_b15_workflow_host(temporary_root, contract)

        host = load_host()
        legacy_parallel = host.module.prepare_track_alignment()
        session = workflow.load_modular_transition_workflow_session(
            temporary_root, api, contract,
        )
        expected = _expected()
        assert session.launch_workflow() == expected
        assert session.module.prepare_track_alignment() == legacy_parallel
        assert session.module.LAUNCH_COUNT == 1
        record = session.routing_record()
        assert record == {
            "schema_version": 4,
            "contract_id": "tracktemplate:phase7:concentric-core:1",
            "route": "modular", "comparison_route_available": False,
            "function_names": list(FUNCTION_NAMES),
            "caller_names": [
                "main_circle_centre", "build_concentric_core",
                "prepare_track_alignment", "run_macro",
            ],
            "workflow_version": "10.2A8A7B15",
            "workflow_source_sha256": host.source_sha256,
            "mixed_route": False,
        }
        adapter = session.module.build_concentric_core
        assert type(adapter) is workflow._ConcentricCoreAdapter
        assert adapter.calculation is api.build_concentric_core
        assert adapter.vector_factory is session.module.App.Vector
        assert tuple(inspect.signature(adapter).parameters) == PARAMETERS
        try:
            adapter.calculation = lambda *arguments: None
        except AttributeError:
            pass
        else:
            raise AssertionError("The core adapter is mutable")

        invalid_maps = [dict(_functions(), unselected=lambda: None)]
        for name in FUNCTION_NAMES:
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
                "complete six-function",
            )
            assert _snapshot(host) == before and host.module.LAUNCH_COUNT == 0

        # Every selected domain edge must match, including detached closures.
        for name, dependency in (
            ("transition_start_signed_offset", "clothoid_entry_displacement"),
            ("solve_transition_length", "transition_start_signed_offset"),
            ("main_circle_centre", "clothoid_entry_displacement"),
            ("build_concentric_core", "clothoid_entry_displacement"),
            ("build_concentric_core", "clothoid_exit_displacement"),
        ):
            for remove_previous in (False, True):
                host = load_host()
                if remove_previous:
                    del host.module.__dict__[name]
                before = _snapshot(host)
                functions = _functions()
                functions[name] = detached(
                    functions[name], dependency, lambda *arguments: None,
                )
                centre_proof._expect_error(
                    lambda: workflow.ModularTransitionWorkflowSession(
                        host, functions,
                    ),
                    "does not use its selected",
                )
                assert _snapshot(host) == before
                assert host.module.LAUNCH_COUNT == 0

        for caller in ("run_macro", "prepare_track_alignment"):
            host = load_host()
            function = getattr(host.module, caller)
            setattr(host.module, caller, detached(
                function, "build_concentric_core", api.build_concentric_core,
            ))
            before = _snapshot(host)
            centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, _functions(),
                ),
                "caller " + repr(caller) + " is unavailable",
            )
            assert _snapshot(host) == before and host.module.LAUNCH_COUNT == 0

        for name in FUNCTION_NAMES:
            old = getattr(session.module, name)
            setattr(session.module, name, None)
            centre_proof._expect_error(
                session.routing_record, "mixed " + repr(name),
            )
            assert session.launch_workflow() == expected
            assert getattr(session.module, name) is old

        old_vector = session.module.App.Vector
        session.module.App.Vector = lambda *arguments: None
        before = _snapshot(session)
        count = session.module.LAUNCH_COUNT
        centre_proof._expect_error(session.launch_workflow, "core adapter")
        assert _snapshot(session) == before
        assert session.module.LAUNCH_COUNT == count
        session.module.App.Vector = old_vector
        assert session.launch_workflow() == expected

        missing_api = types.SimpleNamespace(**{
            name: value for name, value in _functions().items()
            if name != "build_concentric_core"
        })
        centre_proof._expect_error(
            lambda: workflow.load_modular_transition_workflow_session(
                temporary_root / "absent", missing_api, contract,
            ),
            "complete modular transition calculation route",
        )

    adapter = workflow._ConcentricCoreAdapter(
        api.build_concentric_core, Vector,
    )
    for case in INVALID_CASES:
        assert failure(adapter, case) == failure(
            api.build_concentric_core, case,
        )


def main():
    validate_calculations()
    validate_binding()
    print("Phase 7 concentric core calculation and routing validation passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--characterize"]:
        characterize_legacy()
    else:
        main()
