#!/usr/bin/env python3
"""Prove the internal toe-range calculation and five checked B15 routes."""

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


SENTINEL = "Phase 8 turnout toe-range calculation and routing validation passed"
CALLERS = (
    "_build_curve_inheriting_c10_turnout",
    "_crossover_solve_toe_b",
    "solve_rea_c10_crossover_geometry",
    "CrossoverManagerPanel.update_chainage_range",
    "TurnoutManagerDialog.update_host_summary",
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
            and node.name in {
                "_turnout_orientation_sign", "turnout_valid_toe_range",
            }
        }
        assert set(functions) == {
            "_turnout_orientation_sign", "turnout_valid_toe_range",
        }
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
        # Each of the five inherited call sites still calls this exact name.
        for caller_name in CALLERS:
            if "." in caller_name:
                owner_name, method_name = caller_name.split(".", 1)
                owners = [
                    node for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == owner_name
                ]
                assert len(owners) == 1
                callers = [
                    node for node in owners[0].body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == method_name
                ]
            else:
                callers = [
                    node for node in tree.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == caller_name
                ]
            assert len(callers) == 1, caller_name
            assert any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "turnout_valid_toe_range"
                for node in ast.walk(callers[0])
            ), caller_name
    assert definitions[0] == definitions[1]
    return results


def _observed(function, arguments):
    try:
        result = function(*arguments)
    except Exception as error:  # noqa: BLE001 - exact inherited error proof
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


def _probe_case(host, start, finish, orientation):
    events = []
    arguments = (
        _FloatProbe("host-float", host, events),
        _DimensionsProbe(start, finish, events),
        _OrientationProbe(orientation, events),
    )
    return arguments, events


def validate_calculation():
    b14, b15 = _frozen_oracles()
    assert "turnout_valid_toe_range" not in api.__all__
    assert not hasattr(api, "turnout_valid_toe_range")
    assert turnout.__all__ == ()
    assert turnout.turnout_valid_toe_range.__globals__ is turnout.__dict__
    cases = (
        (1542.475839, -21.666666666666664, 361.3995671038812,
         "Facing with host travel direction"),
        (1542.475839, -21.666666666666664, 361.3995671038812,
         turnout.TURNOUT_ORIENTATION_TRAILING),
        (0.0, -21.0, 361.0, "Other orientation"),
        (-1.0, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (100.0, 50.0, 361.0, "Facing"),
        (100.0, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (math.nan, -21.0, 361.0, "Facing"),
        (math.inf, -21.0, 361.0, turnout.TURNOUT_ORIENTATION_TRAILING),
        (-math.inf, -21.0, 361.0, "Facing"),
        (100.0, math.nan, 361.0, "Facing"),
        (100.0, -21.0, math.nan, turnout.TURNOUT_ORIENTATION_TRAILING),
        ("100.0", "-21.0", "361.0", "Facing"),
        (True, False, True, "Facing"),
        (ValueError("bad host"), -21.0, 361.0, "Facing"),
        (100.0, ValueError("bad start"), 361.0, "Facing"),
        (100.0, -21.0, ValueError("bad finish"), "Facing"),
        (100.0, -21.0, 361.0, ValueError("bad orientation")),
    )
    for case in cases:
        observations = []
        for function in (
            b14["turnout_valid_toe_range"],
            b15["turnout_valid_toe_range"],
            turnout.turnout_valid_toe_range,
        ):
            arguments, events = _probe_case(*case)
            observations.append((_observed(function, arguments), events))
        assert observations[0] == observations[1] == observations[2], case
        assert observations[0][1][:5] == [
            "host-float", "module_start_x", "start-float",
            "module_end_x", "finish-float",
        ][:len(observations[0][1])], case
    for length in (-100.0, 0.0, 100.0, 1542.475839):
        for start in (-21.666666666666664, 0.0, 200.0):
            for finish in (-1.0, 0.0, 361.3995671038812):
                for orientation in (
                    "Facing", turnout.TURNOUT_ORIENTATION_TRAILING,
                ):
                    arguments = (length, {
                        "module_start_x": start,
                        "module_end_x": finish,
                    }, orientation)
                    assert _observed(turnout.turnout_valid_toe_range, arguments) == (
                        _observed(b14["turnout_valid_toe_range"], arguments)
                    )


_SYNTHETIC_TURNOUT_ROUTE = """
TURNOUT_ORIENTATION_TRAILING = "Trailing against host travel direction"
def _turnout_orientation_sign(orientation):
    return -1.0 if str(orientation) == TURNOUT_ORIENTATION_TRAILING else 1.0
def turnout_valid_toe_range(host_length, dimensions, orientation):
    total = max(0.0, float(host_length))
    start_x = float(dimensions["module_start_x"])
    finish_x = float(dimensions["module_end_x"])
    if _turnout_orientation_sign(orientation) > 0.0:
        minimum = max(0.0, -start_x)
        maximum = min(total, total - finish_x)
    else:
        minimum = max(0.0, finish_x)
        maximum = min(total, total + start_x)
    return minimum, maximum
def _build_curve_inheriting_c10_turnout(*arguments):
    return turnout_valid_toe_range(*arguments)
def _crossover_solve_toe_b(*arguments):
    return turnout_valid_toe_range(*arguments)
def solve_rea_c10_crossover_geometry(*arguments):
    if arguments is None:
        interpolate_alignment_station(None, None)
    return turnout_valid_toe_range(*arguments)
def _update_chainage_range(self, *arguments):
    return turnout_valid_toe_range(*arguments)
class TurnoutManagerDialog:
    def update_host_summary(self, *arguments):
        return turnout_valid_toe_range(*arguments)
"""


def _caller(namespace, name):
    if "." in name:
        owner_name, method_name = name.split(".", 1)
        return namespace[owner_name].__dict__[method_name]
    return namespace[name]


def _host(root, contract):
    host = b15_workflow_host.load_b15_workflow_host(root, contract)
    exec(_SYNTHETIC_TURNOUT_ROUTE, host.module.__dict__)
    panel = host.module.CrossoverManagerPanel
    panel.update_chainage_range = host.module.__dict__.pop(
        "_update_chainage_range"
    )
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
        assert "turnout toe-range" in str(error), str(error)
        return
    raise AssertionError("A mixed turnout toe-range route was accepted")


def validate_binding():
    with tempfile.TemporaryDirectory(prefix="tracktemplate-phase8-toe-range-") as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        absent = b15_workflow_host.load_b15_workflow_host(root, contract)
        assert "turnout_valid_toe_range" not in absent.module.__dict__
        absent_session = transition_workflow.ModularTransitionWorkflowSession(
            absent, _functions(),
        )
        absent_record = absent_session.routing_record()
        assert "turnout_valid_toe_range" not in absent.module.__dict__
        assert absent_record["schema_version"] == 16
        assert len(absent_record["function_names"]) == 25
        assert len(absent_record["caller_names"]) == 40

        host = _host(root, contract)
        namespace = host.module.__dict__
        inherited = namespace["turnout_valid_toe_range"]
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, _functions(),
        )
        record = session.routing_record()
        assert record == absent_record
        assert namespace["turnout_valid_toe_range"] is (
            turnout.turnout_valid_toe_range
        )
        assert namespace["turnout_valid_toe_range"] is not inherited
        arguments = (1542.475839, {
            "module_start_x": -21.666666666666664,
            "module_end_x": 361.3995671038812,
        }, turnout.TURNOUT_ORIENTATION_TRAILING)
        expected = turnout.turnout_valid_toe_range(*arguments)
        for name in CALLERS:
            caller = _caller(namespace, name)
            assert caller.__globals__ is namespace
            assert "turnout_valid_toe_range" in caller.__code__.co_names
            assert caller.__globals__["turnout_valid_toe_range"] is (
                turnout.turnout_valid_toe_range
            )
            if "." in name:
                owner_name, _method_name = name.split(".", 1)
                result = caller(namespace[owner_name](), *arguments)
            else:
                result = caller(*arguments)
            assert result == expected, name

        for name in CALLERS:
            if "." in name:
                owner_name, method_name = name.split(".", 1)
                owner = namespace[owner_name]
                original = owner.__dict__[method_name]
                setattr(owner, method_name, lambda self: None)
                try:
                    _expect_route_error(session.routing_record)
                finally:
                    setattr(owner, method_name, original)
            else:
                original = namespace[name]
                namespace[name] = lambda: None
                try:
                    _expect_route_error(session.routing_record)
                finally:
                    namespace[name] = original
            assert session.routing_record() == record

        namespace["turnout_valid_toe_range"] = inherited
        _expect_route_error(session.routing_record)
        assert session.launch_workflow()
        assert host.module.LAUNCH_COUNT == 1
        assert namespace["turnout_valid_toe_range"] is (
            turnout.turnout_valid_toe_range
        )
        assert session.routing_record() == record

        rollback = _host(root, contract)
        rollback_namespace = rollback.module.__dict__
        rollback_namespace["_crossover_solve_toe_b"] = lambda: None
        original = {
            name: rollback_namespace.get(name)
            for name in (*transition_workflow.PRODUCT_FUNCTION_NAMES,
                         "turnout_valid_toe_range")
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
