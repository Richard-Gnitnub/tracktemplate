#!/usr/bin/env python3
"""Compare occupied turnout host intervals and their four inherited routes."""

import ast
import hashlib
import json
import math
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow,
)
from tracktemplate.domain import turnout  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 8 turnout host-interval calculation and routing validation passed"
BINDING = "turnout_host_station_interval"
CALLERS = (
    "_turnout_find_overlap",
    "_build_curve_inheriting_c10_turnout",
    "build_turnout_host_integration",
    "solve_rea_c10_crossover_geometry",
)


def _frozen_oracles():
    contract = json.loads((
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    ).read_text(encoding="utf-8"))
    assert contract["contract_id"] == "tracktemplate:phase1:transition-pilot:1"
    results = []
    definitions = []
    for key in ("b14", "b15"):
        identity = contract["source_state"][key]
        path = ROOT / identity["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            identity["sha256"]
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = {
            node.name: node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"_turnout_orientation_sign", BINDING}
        }
        assert set(functions) == {"_turnout_orientation_sign", BINDING}
        constant = [
            ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
            and target.id == "TURNOUT_ORIENTATION_TRAILING"
        ]
        assert constant == [turnout.TURNOUT_ORIENTATION_TRAILING]
        namespace = {"TURNOUT_ORIENTATION_TRAILING": constant[0]}
        exec(compile(ast.Module(
            body=list(functions.values()), type_ignores=[],
        ), str(path), "exec"), namespace)
        results.append(namespace)
        definitions.append({
            name: ast.dump(node, include_attributes=False)
            for name, node in functions.items()
        })
        for caller_name in CALLERS:
            callers = [
                node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == caller_name
            ]
            assert len(callers) == 1, caller_name
            assert any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == BINDING
                for node in ast.walk(callers[0])
            ), caller_name
    assert definitions[0] == definitions[1]
    return results


def _observed(function, arguments):
    try:
        result = function(*arguments)
    except Exception as error:  # noqa: BLE001 - compare inherited failures
        return ("error", type(error).__name__, str(error))
    assert type(result) is tuple and len(result) == 2
    assert all(type(value) is float for value in result)
    return ("value", tuple(value.hex() for value in result))


class _FloatProbe:
    def __init__(self, label, value, events):
        self.label = label
        self.value = value
        self.events = events

    def __float__(self):
        self.events.append(self.label)
        if isinstance(self.value, Exception):
            raise self.value
        return float(self.value)


class _DimensionsProbe:
    def __init__(self, start, finish, events):
        self.start = start
        self.finish = finish
        self.events = events

    def __getitem__(self, key):
        self.events.append(key)
        if key == "module_start_x":
            return _FloatProbe("start-float", self.start, self.events)
        if key == "module_end_x":
            return _FloatProbe("finish-float", self.finish, self.events)
        raise KeyError(key)


class _OrientationProbe:
    def __init__(self, value, events):
        self.value = value
        self.events = events

    def __str__(self):
        self.events.append("orientation-str")
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def _probe_case(toe, start, finish, orientation):
    events = []
    arguments = (
        _FloatProbe("toe-float", toe, events),
        _DimensionsProbe(start, finish, events),
        _OrientationProbe(orientation, events),
    )
    return arguments, events


def validate_calculation():
    b14, b15 = _frozen_oracles()
    assert pathlib.Path(api.__file__).resolve() == ROOT / "tracktemplate/api.py"
    assert BINDING not in api.__all__
    assert not hasattr(api, BINDING)
    assert turnout.__all__ == ()
    selected = turnout.turnout_host_station_interval
    assert selected.__globals__ is turnout.__dict__
    dimensions = {"module_start_x": -20.0, "module_end_x": 360.0}
    assert selected(100.0, dimensions, "Facing") == (80.0, 460.0)
    assert selected(
        100.0, dimensions, turnout.TURNOUT_ORIENTATION_TRAILING,
    ) == (-260.0, 120.0)
    assert selected(125.0, dimensions, "Facing") == (105.0, 485.0)
    cases = (
        (1542.475839, -21.666666666666664, 361.3995671038812,
         "Facing with host travel direction"),
        (1542.475839, -21.666666666666664, 361.3995671038812,
         turnout.TURNOUT_ORIENTATION_TRAILING),
        (0.0, -21.0, 361.0, "Other orientation"),
        (-1.0, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (100.0, 50.0, -5.0, "Facing"),
        (100.0, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (math.nan, -21.0, 361.0, "Facing"),
        (math.inf, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (-math.inf, -21.0, 361.0, "Facing"),
        (100.0, math.nan, 361.0, "Facing"),
        (100.0, -21.0, math.nan, turnout.TURNOUT_ORIENTATION_TRAILING),
        ("100.0", "-21.0", "361.0", "Facing"),
        (True, False, True, "Facing"),
        (-0.0, -0.0, 0.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (ValueError("bad toe"), -21.0, 361.0, "Facing"),
        (100.0, ValueError("bad start"), 361.0, "Facing"),
        (100.0, -21.0, ValueError("bad finish"), "Facing"),
        (100.0, -21.0, 361.0, ValueError("bad orientation")),
    )
    for case in cases:
        observations = []
        for function in (b14[BINDING], b15[BINDING], selected):
            arguments, events = _probe_case(*case)
            observations.append((_observed(function, arguments), events))
        assert observations[0] == observations[1] == observations[2], case
        assert observations[0][1][:7] == [
            "orientation-str", "toe-float", "module_start_x",
            "start-float", "toe-float", "module_end_x", "finish-float",
        ][:len(observations[0][1])], case
    for toe in (-100.0, 0.0, 100.0, 1542.475839):
        for start in (-21.666666666666664, 0.0, 200.0):
            for finish in (-1.0, 0.0, 361.3995671038812):
                for orientation in (
                    "Facing", turnout.TURNOUT_ORIENTATION_TRAILING,
                ):
                    arguments = (toe, {
                        "module_start_x": start,
                        "module_end_x": finish,
                    }, orientation)
                    assert _observed(selected, arguments) == (
                        _observed(b14[BINDING], arguments)
                    )
    for dimensions in ({"module_start_x": 1.0},
                       {"module_end_x": 2.0}, {}):
        arguments = (100.0, dimensions, "Facing")
        assert _observed(selected, arguments) == (
            _observed(b14[BINDING], arguments)
        )


_SYNTHETIC_ROUTE = """
def turnout_host_station_interval(*arguments):
    return "inherited"
def _turnout_find_overlap(*arguments):
    return turnout_host_station_interval(*arguments)
def _build_curve_inheriting_c10_turnout(*arguments):
    return turnout_host_station_interval(*arguments)
def build_turnout_host_integration(*arguments):
    return turnout_host_station_interval(*arguments)
def solve_rea_c10_crossover_geometry(*arguments):
    if arguments is None:
        interpolate_alignment_station(None, None)
    return turnout_host_station_interval(*arguments)
"""


def _host(root, contract):
    host = b15_workflow_host.load_b15_workflow_host(root, contract)
    exec(_SYNTHETIC_ROUTE, host.module.__dict__)
    return host


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def _expect_route_error(action):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        assert "turnout host-interval" in str(error), str(error)
        return
    raise AssertionError("A mixed turnout host-interval route was accepted")


def validate_binding():
    with tempfile.TemporaryDirectory(prefix="tracktemplate-phase8-host-interval-") as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        absent = b15_workflow_host.load_b15_workflow_host(root, contract)
        assert BINDING not in absent.module.__dict__
        absent_session = transition_workflow.ModularTransitionWorkflowSession(
            absent, _functions(),
        )
        absent_record = absent_session.routing_record()
        assert BINDING not in absent.module.__dict__
        assert absent_record["schema_version"] == 16
        assert len(absent_record["function_names"]) == 25
        assert len(absent_record["caller_names"]) == 40

        host = _host(root, contract)
        namespace = host.module.__dict__
        inherited = namespace[BINDING]
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, _functions(),
        )
        record = session.routing_record()
        assert record == absent_record
        assert namespace[BINDING] is turnout.turnout_host_station_interval
        assert namespace[BINDING] is not inherited
        arguments = (1542.475839, {
            "module_start_x": -21.666666666666664,
            "module_end_x": 361.3995671038812,
        }, turnout.TURNOUT_ORIENTATION_TRAILING)
        expected = turnout.turnout_host_station_interval(*arguments)
        for name in CALLERS:
            caller = namespace[name]
            assert caller.__globals__ is namespace
            assert BINDING in caller.__code__.co_names
            assert caller.__globals__[BINDING] is (
                turnout.turnout_host_station_interval
            )
            assert caller(*arguments) == expected, name

        for name in CALLERS:
            original = namespace[name]
            namespace[name] = lambda: None
            try:
                _expect_route_error(session.routing_record)
            finally:
                namespace[name] = original
            assert session.routing_record() == record

        namespace[BINDING] = inherited
        _expect_route_error(session.routing_record)
        assert session.launch_workflow()
        assert host.module.LAUNCH_COUNT == 1
        assert namespace[BINDING] is turnout.turnout_host_station_interval
        assert session.routing_record() == record

        selected_binding = namespace.pop(BINDING)
        try:
            _expect_route_error(session.routing_record)
        finally:
            namespace[BINDING] = selected_binding
        assert session.routing_record() == record

        original_selected = turnout.turnout_host_station_interval
        turnout.turnout_host_station_interval = lambda *_arguments: (0.0, 0.0)
        try:
            _expect_route_error(session.routing_record)
        finally:
            turnout.turnout_host_station_interval = original_selected
        assert session.routing_record() == record

        rollback = _host(root, contract)
        rollback_namespace = rollback.module.__dict__
        rollback_namespace["_turnout_find_overlap"] = lambda: None
        original = {
            name: rollback_namespace.get(name)
            for name in (*transition_workflow.PRODUCT_FUNCTION_NAMES, BINDING)
        }
        _expect_route_error(lambda: (
            transition_workflow.ModularTransitionWorkflowSession(
                rollback, _functions(),
            )
        ))
        assert all(
            rollback_namespace.get(name) is value
            for name, value in original.items()
        )
        assert rollback.module.LAUNCH_COUNT == 0


def validate():
    validate_calculation()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
