#!/usr/bin/env python3
"""Prove exact C10 dimensions and the shared turnout/crossover binding."""

import ast
import dataclasses
import hashlib
import itertools
import json
import math
import pathlib
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow as workflow,
)
from tracktemplate.domain import turnout  # noqa: E402
import validate_phase1_turnout as legacy  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 9B C10 dimensions and shared consumer routing passed"
BINDING = "rea_c10_dimensions"
CALLERS = (
    "_turnout_find_overlap",
    "_build_curve_inheriting_c10_turnout",
    "solve_rea_c10_crossover_geometry",
    "crossover_inherited_timber_records",
    "_shared_timber_candidate",
    "_shared_timber_envelope_record",
    "crossover_shared_timber_envelope_context",
    "_shared_timber_build_envelope",
    "_chair_turnout_rail_records",
    "_chair_turnout_timber_records",
    "CrossoverManagerPanel.update_chainage_range",
    "TurnoutManagerDialog.update_host_summary",
)
CONSTANTS = (
    "TURNOUT_SIZE_C10",
    "TURNOUT_DEFAULT_GAUGE",
    "TURNOUT_DEFAULT_FLANGEWAY",
    "TURNOUT_DEFAULT_SCALE",
    "TURNOUT_MIN_GAUGE",
    "TURNOUT_MAX_GAUGE",
    "TURNOUT_MIN_FLANGEWAY",
    "TURNOUT_MAX_FLANGEWAY",
)
DEFAULTS = (16.5, 1.0, 76.2)
PARAMETERS = ("track_gauge", "flangeway", "model_scale")


def _oracles():
    contract = json.loads(
        (ROOT / "reference/contracts/phase1-transition-pilot.json").read_text()
    )
    namespaces = []
    definitions = []
    for key in ("b14", "b15"):
        identity = contract["source_state"][key]
        path = ROOT / identity["path"]
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest() == identity["sha256"]
        )
        namespace, nodes = legacy._load_turnout_namespace(path)
        namespaces.append(namespace)
        definitions.append(nodes["functions"][BINDING])
    assert definitions[0] == definitions[1]
    tree = ast.parse(legacy.B15_PATH.read_text())
    return namespaces, definitions[0], tree


def _cases():
    cases = [
        (args, {})
        for args in itertools.product(
            (10.0, 16.5, 25.0),
            (0.25, 1.0, 3.0),
            (38.1, 76.2, 152.4),
        )
    ]
    keywords = dict(zip(PARAMETERS, DEFAULTS))
    cases.extend((DEFAULTS[:count], {}) for count in range(4))
    cases.extend(((), {name: value}) for name, value in keywords.items())
    cases.extend(
        (
            ((), keywords),
            (DEFAULTS[:1], dict(zip(PARAMETERS[1:], DEFAULTS[1:]))),
            ((), dict(reversed(tuple(keywords.items())))),
        )
    )
    for index, low, high in ((0, 10.0, 25.0), (1, 0.25, 3.0)):
        for bound, direction in itertools.product(
            (low, high), (-math.inf, math.inf)
        ):
            values = list(DEFAULTS)
            values[index] = math.nextafter(bound, direction)
            cases.append((tuple(values), {}))
    for value in (
        math.nextafter(0.0, math.inf),
        math.nextafter(0.0, -math.inf),
        0.0,
        -76.2,
    ):
        cases.append(((*DEFAULTS[:2], value), {}))
    for index in range(3):
        for value in (
            math.nan,
            math.inf,
            -math.inf,
            True,
            False,
            str(DEFAULTS[index]),
            "not numeric",
            None,
        ):
            values = list(DEFAULTS)
            values[index] = value
            cases.append((tuple(values), {}))
    cases.extend(
        (
            ((), {"unknown": 1}),
            (DEFAULTS + (1.0,), {}),
            (DEFAULTS, {"track_gauge": 16.5}),
            (DEFAULTS, {"flangeway": 1.0}),
        )
    )
    assert len(cases) == 77
    return cases


class FloatProbe:
    def __init__(self, name, value, events):
        self.name, self.value, self.events = name, value, events

    def __float__(self):
        self.events.append(self.name)
        if isinstance(self.value, Exception):
            raise self.value
        return float(self.value)


def _observation(function, args, keywords, probe=False):
    events = []
    if probe:
        args = tuple(
            FloatProbe(name, value, events)
            for name, value in zip(PARAMETERS, args)
        )
    try:
        result = function(*args, **keywords)
    except Exception as error:  # noqa: BLE001 - exact legacy failure contract
        return ("error", type(error).__name__, str(error), tuple(events))
    assert type(result) is dict and len(result) == 88
    values = []
    for key, value in result.items():
        assert type(value) is (
            str
            if key
            in (
                "size",
                "check_turnout_working_mode",
            )
            else float
        )
        values.append(
            (
                key,
                type(value).__name__,
                value.hex() if type(value) is float else value,
            )
        )
    return ("value", tuple(values), tuple(events))


def _observations(function):
    results = [_observation(function, *case) for case in _cases()]
    bad = ValueError("conversion failed")
    probes = (
        DEFAULTS,
        (bad, 1.0, 76.2),
        (16.5, bad, 76.2),
        (16.5, 1.0, bad),
        (0.0, 1.0, 76.2),
        (0.0, bad, 76.2),
        (16.5, 0.0, bad),
        (0.0, 0.0, 0.0),
    )
    expected_traces = (
        PARAMETERS,
        PARAMETERS[:1],
        PARAMETERS[:2],
        PARAMETERS,
        PARAMETERS,
        PARAMETERS[:2],
        PARAMETERS,
        PARAMETERS,
    )
    for args, trace in zip(probes, expected_traces):
        result = _observation(function, args, {}, probe=True)
        assert result[-1] == trace
        results.append(result)
    assert len(results) == 85
    return results


def validate_calculation(oracles, frozen_definition):
    expected = [_observations(namespace[BINDING]) for namespace in oracles]
    for first, second in zip(*expected):
        assert first == second
    print("Frozen B14/B15 observations: 85 equal", flush=True)
    selected = getattr(turnout, BINDING)
    assert BINDING not in api.__all__ and not hasattr(api, BINDING)
    assert turnout.__all__ == () and selected.__globals__ is turnout.__dict__
    source = ast.parse((ROOT / "tracktemplate/domain/turnout.py").read_text())
    extracted = next(
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == BINDING
    )
    assert ast.dump(extracted, include_attributes=False) == frozen_definition
    for name in CONSTANTS:
        assert getattr(turnout, name) == oracles[1][name]
    actual = _observations(selected)
    for reference, result in zip(expected[1], actual):
        assert result == reference
    return {
        "input_cases": 85,
        "complete_observation_equalities": 170,
        "successful_cases": sum(row[0] == "value" for row in actual),
        "failed_input_cases": sum(row[0] == "error" for row in actual),
    }


def _source_routes(tree):
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    classes = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }
    result = {}
    for name in CALLERS:
        if "." in name:
            owner, method = name.split(".")
            node = next(
                item
                for item in classes[owner].body
                if isinstance(item, ast.FunctionDef) and item.name == method
            )
        else:
            node = functions[name]
        assert any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == BINDING
            for item in ast.walk(node)
        ), name
        result[name] = node
    return result


def _constants(tree):
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and (
                target.id.startswith(("TURNOUT_", "CROSSOVER_"))
                or target.id == "GEOMETRY_TOLERANCE"
            ):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
    return values


def _caller(namespace, name, replacement=None):
    if "." in name:
        owner, method = name.split(".")
        previous = getattr(namespace[owner], method)
        if replacement is not None:
            setattr(namespace[owner], method, replacement)
    else:
        previous = namespace[name]
        if replacement is not None:
            namespace[name] = replacement
    return previous


def _host(root, contract, tree, oracle):
    host = b15_workflow_host.load_b15_workflow_host(root, contract)
    namespace = host.module.__dict__
    namespace.update(_constants(tree))
    for name, node in _source_routes(tree).items():
        if "." in name:
            owner, method = name.split(".")
            if owner not in namespace:
                namespace[owner] = type(owner, (), {})
            exec(
                compile(
                    ast.Module(body=[node], type_ignores=[]),
                    str(legacy.B15_PATH),
                    "exec",
                ),
                namespace,
            )
            setattr(namespace[owner], method, namespace.pop(method))
        else:
            exec(
                compile(
                    ast.Module(body=[node], type_ignores=[]),
                    str(legacy.B15_PATH),
                    "exec",
                ),
                namespace,
            )
    namespace[BINDING] = oracle
    return host


def _expect_route_error(action):
    try:
        action()
    except workflow.TransitionWorkflowError as error:
        assert "turnout dimensions" in str(error), str(error)
        return
    raise AssertionError("Mixed turnout dimensions route accepted")


def _install_preflight(host, tree):
    namespace = host.module.__dict__
    names = {
        "_build_rea_c10_crossover_geometry",
        "create_rea_c10_crossover",
        "edit_rea_c10_crossover",
        "extend_turnout_to_rea_c10_crossover",
        "crossover_geometry_diagnostics_text",
        "crossover_solver_trace_text",
        "turnout_mapping_metrics",
        "turnout_host_alignment",
        "existing_turnout_configs",
        "existing_crossover_configs",
        "crossover_config_by_id",
        "clear_chair_analysis_display",
        "object_string_property",
        "_integer_object_property",
    }
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    }
    assert set(functions) == names
    exec(
        compile(
            ast.Module(body=list(functions.values()), type_ignores=[]),
            str(legacy.B15_PATH),
            "exec",
        ),
        namespace,
    )
    panel = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CrossoverManagerPanel"
    )
    for method in (
        "_preview_signature",
        "preview_geometry",
        "create_crossover",
    ):
        node = next(
            item
            for item in panel.body
            if isinstance(item, ast.FunctionDef) and item.name == method
        )
        exec(
            compile(
                ast.Module(body=[node], type_ignores=[]),
                str(legacy.B15_PATH),
                "exec",
            ),
            namespace,
        )
        setattr(
            namespace["CrossoverManagerPanel"], method, namespace.pop(method)
        )


def validate_binding(tree, oracle):
    functions = {
        name: getattr(api, name) for name in workflow.PRODUCT_FUNCTION_NAMES
    }
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-c10-dimensions-"
    ) as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        absent = b15_workflow_host.load_b15_workflow_host(root, contract)
        absent_session = workflow.ModularTransitionWorkflowSession(
            absent, functions
        )
        expected_record = absent_session.routing_record()
        assert BINDING not in absent.module.__dict__
        host = _host(root, contract, tree, oracle)
        namespace = host.module.__dict__
        session = workflow.ModularTransitionWorkflowSession(host, functions)
        assert namespace[BINDING] is turnout.rea_c10_dimensions
        assert session.routing_record() == expected_record
        assert expected_record["schema_version"] == 16
        assert len(expected_record["function_names"]) == 25
        assert len(expected_record["caller_names"]) == 40
        for name in CALLERS:
            original = _caller(namespace, name)
            assert original.__globals__ is namespace
            assert original.__globals__[BINDING] is turnout.rea_c10_dimensions
            foreign = types.FunctionType(
                original.__code__,
                dict(namespace),
                original.__name__,
                original.__defaults__,
            )
            for replacement in (object(), foreign, lambda *args: None):
                _caller(namespace, name, replacement)
                try:
                    _expect_route_error(session.routing_record)
                finally:
                    _caller(namespace, name, original)
            assert session.routing_record() == expected_record
        selected = namespace.pop(BINDING)
        _expect_route_error(session.routing_record)
        namespace[BINDING] = oracle
        _expect_route_error(session.routing_record)
        namespace[BINDING] = selected
        session._host_functions[BINDING] = oracle
        _expect_route_error(session.routing_record)
        session._host_functions[BINDING] = selected
        namespace[BINDING] = oracle
        assert session.launch_workflow()
        assert host.module.LAUNCH_COUNT == 1
        assert namespace[BINDING] is selected
        assert session.routing_record() == expected_record
        rollback = _host(root, contract, tree, oracle)
        rollback.module._shared_timber_candidate = lambda: None
        previous = dict(rollback.module.__dict__)
        _expect_route_error(
            lambda: workflow.ModularTransitionWorkflowSession(
                rollback,
                functions,
            )
        )
        assert rollback.module.__dict__ == previous
        assert rollback.module.LAUNCH_COUNT == 0
        wrapped = _host(root, contract, tree, oracle)
        _install_preflight(wrapped, tree)
        wrapped_session = workflow.ModularTransitionWorkflowSession(
            wrapped, functions
        )
        adapter = wrapped_session._crossover_preflight
        assert adapter is not None
        assert wrapped_session.routing_record() == expected_record
        original = adapter.original_solver
        assert original.__globals__[BINDING] is turnout.rea_c10_dimensions
        foreign = types.FunctionType(
            original.__code__,
            dict(original.__globals__),
            original.__name__,
            original.__defaults__,
        )
        wrapped_session._crossover_preflight = dataclasses.replace(
            adapter, original_solver=foreign,
        )
        _expect_route_error(wrapped_session.routing_record)
        wrapped_session._crossover_preflight = adapter
        assert wrapped_session.routing_record() == expected_record
    return {
        "direct_callers": 12,
        "negative_caller_cases": 36,
        "session_cases": 8,
        "wrapped_solver_positive_negative": 2,
    }


class PrefixComplete(Exception):
    pass


def validate_consumer_prefixes(tree, oracle):
    nodes = _source_routes(tree)
    namespace = _constants(tree)
    namespace.update({"math": math, BINDING: turnout.rea_c10_dimensions})
    receipts = []

    def stop_at_range(total, dimensions, orientation):
        receipts.append((total, dimensions, orientation))
        raise PrefixComplete

    namespace.update(
        {
            "is_turnout_host_centreline": lambda host: True,
            "turnout_host_alignment": lambda host: {"total": 2000.0},
            "object_string_property": lambda host, name, default: "SET-001",
            "turnout_valid_toe_range": stop_at_range,
        }
    )
    selected = [
        nodes[name]
        for name in (
            "_build_curve_inheriting_c10_turnout",
            "solve_rea_c10_crossover_geometry",
        )
    ]
    exec(
        compile(
            ast.Module(body=selected, type_ignores=[]),
            str(legacy.B15_PATH),
            "exec",
        ),
        namespace,
    )
    first, second = (types.SimpleNamespace(Name=name) for name in ("A", "B"))
    calls = []
    for hand, direction in itertools.product(
        (namespace["TURNOUT_HAND_LEFT"], namespace["TURNOUT_HAND_RIGHT"]),
        (
            namespace["TURNOUT_ORIENTATION_FACING"],
            namespace["TURNOUT_ORIENTATION_TRAILING"],
        ),
    ):
        calls.append(
            (
                namespace["_build_curve_inheriting_c10_turnout"],
                (None, first, 500.0, hand, direction, 16.5, 1.0),
                direction,
            )
        )
    for arrangement, direction in (
        (
            namespace["CROSSOVER_ARRANGEMENT_FACING"],
            namespace["TURNOUT_ORIENTATION_FACING"],
        ),
        (
            namespace["CROSSOVER_ARRANGEMENT_TRAILING"],
            namespace["TURNOUT_ORIENTATION_TRAILING"],
        ),
    ):
        calls.append(
            (
                namespace["solve_rea_c10_crossover_geometry"],
                (None, first, second, 500.0, arrangement),
                direction,
            )
        )
    for function, args, direction in calls:
        try:
            function(*args)
        except PrefixComplete:
            pass
        else:
            raise AssertionError(
                "Actual consumer did not reach the dimension boundary"
            )
        assert receipts[-1] == (2000.0, oracle(), direction)
        assert function.__globals__[BINDING] is turnout.rea_c10_dimensions
    assert len(receipts) == 6
    return {"actual_consumer_prefixes": 6}


def validate():
    oracles, definition, tree = _oracles()
    report = validate_calculation(oracles, definition)
    report.update(validate_binding(tree, oracles[1][BINDING]))
    report.update(validate_consumer_prefixes(tree, oracles[1][BINDING]))
    print(json.dumps(report, sort_keys=True))
    print(SENTINEL)


if __name__ == "__main__":
    validate()
