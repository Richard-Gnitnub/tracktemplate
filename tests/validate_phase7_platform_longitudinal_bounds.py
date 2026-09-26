#!/usr/bin/env python3
"""Compare frozen platform longitudinal bounds with Core and B16 routing."""

import argparse
import ast
import hashlib
import inspect
import json
import math
import pathlib
import subprocess
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
B14 = ROOT / "AdvancedTurnout.FCMacro"
B15 = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
NAME = "resolve_platform_longitudinal_bounds"
DEFINITION_SHA256 = (
    "0b2a8eeed70008fce640ad3f4bb56d4c87a70dd1b447002da99db7751c20362d"
)
RESULT_KEYS = (
    "start_station", "finish_station", "centre_station", "centre_offset",
    "length", "available_length", "start_inset", "finish_inset",
)
SENTINEL = "Phase 7 platform longitudinal bounds validation passed"


def legacy_functions():
    """Compile only the byte-identical B14/B15 definition and tolerance."""
    functions = []
    for path in (B14, B15):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        node = next(item for item in tree.body
                    if isinstance(item, ast.FunctionDef) and item.name == NAME)
        definition = "".join(source.splitlines(keepends=True)[
            node.lineno - 1:node.end_lineno
        ])
        assert len(definition.encode("utf-8")) == 2505
        assert hashlib.sha256(definition.encode("utf-8")).hexdigest() == (
            DEFINITION_SHA256
        )
        tolerance = next(
            ast.literal_eval(item.value)
            for item in tree.body if isinstance(item, ast.Assign)
            for target in item.targets if isinstance(target, ast.Name)
            and target.id == "GEOMETRY_TOLERANCE"
        )
        assert tolerance == 1.0e-8
        namespace = {"GEOMETRY_TOLERANCE": tolerance}
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     str(path), "exec"), namespace)
        functions.append(namespace[NAME])
    return functions


def cases():
    """Exercise placement, tolerance, invalid types and nonfinite data."""
    tolerance = 1.0e-8
    above = math.nextafter(tolerance, math.inf)
    maximum_plus_tolerance = 150.0 + tolerance
    definitions = (
        ("midpoint", {}, 0.0, 200.0),
        ("shifted-offset", {"platform_length": 60.0,
                            "centre_offset": 20.0}, -50.0, 150.0),
        ("negative-offset", {"platform_length": 60.0,
                             "centre_offset": -20.0}, -50.0, 150.0),
        ("exact-fit", {"platform_length": 150.0,
                       "centre_offset": 25.0}, 0.0, 200.0),
        ("length-at-fit-tolerance", {
            "platform_length": maximum_plus_tolerance,
            "centre_offset": 25.0,
        }, 0.0, 200.0),
        ("length-above-fit-tolerance", {
            "platform_length": math.nextafter(maximum_plus_tolerance,
                                               math.inf),
            "centre_offset": 25.0,
        }, 0.0, 200.0),
        ("centre-at-left-tolerance", {
            "platform_length": 1.0, "centre_offset": -1.0 - tolerance,
        }, -1.0, 1.0),
        ("centre-outside-left-tolerance", {
            "platform_length": 1.0,
            "centre_offset": math.nextafter(-1.0 - tolerance, -math.inf),
        }, -1.0, 1.0),
        ("centre-at-right-tolerance", {
            "platform_length": 1.0, "centre_offset": 1.0 + tolerance,
        }, -1.0, 1.0),
        ("centre-outside-right-tolerance", {
            "platform_length": 1.0,
            "centre_offset": math.nextafter(1.0 + tolerance, math.inf),
        }, -1.0, 1.0),
        ("centre-at-left-edge", {"centre_offset": -100.0}, 0.0, 200.0),
        ("centre-at-right-edge", {"centre_offset": 100.0}, 0.0, 200.0),
        ("available-zero", {}, 0.0, 0.0),
        ("available-reversed", {}, 200.0, 0.0),
        ("available-at-tolerance", {}, 0.0, tolerance),
        ("available-above-tolerance", {
            "platform_length": above,
        }, 0.0, above),
        ("length-negative", {"platform_length": -1.0}, 0.0, 200.0),
        ("length-zero", {"platform_length": 0.0}, 0.0, 200.0),
        ("length-at-tolerance", {
            "platform_length": tolerance,
        }, 0.0, 200.0),
        ("length-above-tolerance", {
            "platform_length": above,
        }, 0.0, 200.0),
        ("requested-too-long", {"platform_length": 201.0}, 0.0, 200.0),
        ("bad-start", {}, None, 200.0),
        ("bad-finish", {}, 0.0, "invalid"),
        ("none-length", {"platform_length": None}, 0.0, 200.0),
        ("bad-length", {"platform_length": "invalid"}, 0.0, 200.0),
        ("none-offset", {"centre_offset": None}, 0.0, 200.0),
        ("bad-offset", {"centre_offset": "invalid"}, 0.0, 200.0),
        ("nan-start", {}, math.nan, 200.0),
        ("nan-finish", {}, 0.0, math.nan),
        ("nan-length", {"platform_length": math.nan}, 0.0, 200.0),
        ("nan-offset", {"centre_offset": math.nan}, 0.0, 200.0),
        ("infinite-finish", {}, 0.0, math.inf),
        ("infinite-length", {"platform_length": math.inf}, 0.0, 200.0),
        ("infinite-offset", {"centre_offset": math.inf}, 0.0, 200.0),
    )
    for label, overrides, start, finish in definitions:
        config = {"platform_length": 100.0, "centre_offset": 0.0}
        config.update(overrides)
        yield label, config, start, finish


def snapshot(value):
    if isinstance(value, float):
        return {"float": value.hex()}
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in value.items()]
    if isinstance(value, (list, tuple)):
        return [snapshot(item) for item in value]
    return value


def observe(function, config, start, finish):
    identity, before = id(config), snapshot(config)
    try:
        result = function(config, start, finish)
    except Exception as error:  # noqa: BLE001 - preserve inherited failure
        record = {"exception": type(error).__name__, "message": str(error)}
    else:
        assert tuple(result) == RESULT_KEYS
        record = {"value": snapshot(result)}
    assert id(config) == identity and snapshot(config) == before
    return record


class ReadFailure(RuntimeError):
    pass


class Trace:
    def __init__(self, fail_at=None):
        self.events = []
        self.fail_at = fail_at

    def read(self, event):
        self.events.append(event)
        if len(self.events) == self.fail_at:
            raise ReadFailure(event)


class TraceNumber:
    def __init__(self, value, label, trace):
        self.value, self.label, self.trace = value, label, trace

    def __float__(self):
        self.trace.read(self.label + ".float")
        return float(self.value)


class TraceConfig(dict):
    def __init__(self, source, trace):
        super().__init__(source)
        self.trace = trace

    def __getitem__(self, key):
        self.trace.read("config[" + repr(key) + "]")
        return super().__getitem__(key)


def read_observation(function, label, fail_at=None):
    _label, source, start, finish = next(
        item for item in cases() if item[0] == label
    )
    trace = Trace(fail_at)
    config = TraceConfig(source, trace)
    before = snapshot(config)
    result = observe(
        function, config, TraceNumber(start, "start", trace),
        TraceNumber(finish, "finish", trace),
    )
    assert snapshot(config) == before
    return result, trace.events


def baseline():
    first, second = legacy_functions()
    observations = []
    for label, config, start, finish in cases():
        expected = observe(first, config, start, finish)
        assert observe(second, dict(config), start, finish) == expected, label
        observations.append({"case": label, "result": expected})
    assert len(observations) == 34
    normal = observations[0]["result"]["value"]
    assert [item[0] for item in normal] == list(RESULT_KEYS)
    assert normal == snapshot({
        "start_station": 50.0, "finish_station": 150.0,
        "centre_station": 100.0, "centre_offset": 0.0,
        "length": 100.0, "available_length": 200.0,
        "start_inset": 50.0, "finish_inset": 50.0,
    })
    traces = []
    for label in (
        "midpoint", "available-zero", "length-zero",
        "centre-outside-right-tolerance", "requested-too-long",
    ):
        expected = read_observation(first, label)
        assert read_observation(second, label) == expected, label
        for position in range(1, len(expected[1]) + 1):
            failure = read_observation(first, label, position)
            assert failure[0]["exception"] == "ReadFailure"
            assert read_observation(second, label, position) == failure
        traces.append({"case": label, "result": expected[0],
                       "events": expected[1]})
    return first, observations, traces


def _host_independent_import():
    script = """
import importlib.abc
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
assert api.resolve_platform_longitudinal_bounds is (
    alignment.resolve_platform_longitudinal_bounds
)
assert not attempted, attempted
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _synthetic_host(first, api, workflow):
    """Bind the exact inherited caller to the selected Core calculation."""
    from tracktemplate.compatibility import b15_workflow_host
    import validate_phase3_transition_routing as phase3_fixture
    import validate_phase7_concentric_core as core_fixture
    import validate_phase7_platform_input_validation as input_proof

    prefix = "tracktemplate-platform-bounds-"
    with tempfile.TemporaryDirectory(prefix=prefix) as path:
        temporary_root = pathlib.Path(path)
        core_fixture._fixture(temporary_root)
        source = temporary_root / "legacy.FCMacro"
        content = source.read_text(encoding="utf-8")
        launch = "run_macro()\n"
        assert content.endswith(launch)
        tree = ast.parse(B14.read_text(encoding="utf-8"))
        definitions = {
            node.name: node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {NAME, input_proof.NAME}
        }
        constants = {
            target.id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
            and target.id in input_proof.CONSTANTS
        }
        assert set(definitions) == {NAME, input_proof.NAME}
        assert set(constants) == set(input_proof.CONSTANTS)
        additions = (
            "\n".join("{} = {!r}".format(name, constants[name])
                      for name in input_proof.CONSTANTS)
            + "\n\n" + ast.unparse(definitions[input_proof.NAME])
            + "\n\n" + ast.unparse(definitions[NAME]) + "\n"
        )
        source.write_text(content[:-len(launch)] + additions + launch,
                          encoding="utf-8")
        contract = phase3_fixture._contract(source)

        def load_host():
            return b15_workflow_host.load_b15_workflow_host(
                temporary_root, contract,
            )

        def functions():
            return {name: getattr(api, name)
                    for name in workflow.PRODUCT_FUNCTION_NAMES}

        host = load_host()
        namespace = host.module.__dict__
        original_caller = namespace["calculate_platform_boundaries"]
        assert original_caller.__globals__ is namespace
        assert original_caller.__globals__[NAME] is not api.__dict__[NAME]
        assert NAME in original_caller.__code__.co_names
        session = workflow.ModularTransitionWorkflowSession(host, functions())
        record = session.routing_record()
        assert record["schema_version"] == 15
        assert record["contract_id"] == workflow.WORKFLOW_CONTRACT_ID
        assert record["function_names"] == list(
            workflow.PRODUCT_FUNCTION_NAMES
        )
        assert len(record["function_names"]) == 24
        assert len(record["caller_names"]) == 40
        assert record["mixed_route"] is False
        assert namespace[NAME] is api.__dict__[NAME]
        assert namespace["calculate_platform_boundaries"] is original_caller
        assert original_caller.__globals__[NAME] is api.__dict__[NAME]
        targets = dict(workflow.PRODUCT_CALLER_ROUTES)[
            "calculate_platform_boundaries"
        ]
        assert set(targets) == {
            "alignment_station_data", "interpolate_alignment_station",
            "validate_platform_inputs", NAME, "platform_coverage_bounds",
            "station_for_progress_heading", "alignment_progress_at_station",
        }
        namespace[NAME] = first
        try:
            try:
                session.routing_record()
            except workflow.TransitionWorkflowError as error:
                assert "mixed" in str(error)
            else:
                raise AssertionError("A mixed platform-bounds route passed")
        finally:
            namespace[NAME] = api.__dict__[NAME]
        assert session.routing_record() == record

        incomplete = functions()
        incomplete.pop(NAME)
        rejected_host = load_host()
        previous = dict(rejected_host.module.__dict__)
        try:
            workflow.ModularTransitionWorkflowSession(rejected_host,
                                                      incomplete)
        except workflow.TransitionWorkflowError as error:
            assert "complete" in str(error)
        else:
            raise AssertionError("An incomplete platform-bounds route passed")
        assert tuple(rejected_host.module.__dict__) == tuple(previous)
        assert all(rejected_host.module.__dict__[name] is value
                   for name, value in previous.items())

        rollback_host = load_host()
        rollback_host.module.__dict__.pop(NAME)
        previous = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            workflow.ModularTransitionWorkflowSession, "_validate_binding",
            side_effect=RuntimeError("controlled platform-bounds failure"),
        ):
            try:
                workflow.ModularTransitionWorkflowSession(
                    rollback_host, functions(),
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-bounds failure"
            else:
                raise AssertionError("The controlled binding failure was lost")
        assert tuple(rollback_host.module.__dict__) == tuple(previous)
        assert all(rollback_host.module.__dict__[name] is value
                   for name, value in previous.items())
        assert NAME not in rollback_host.module.__dict__
        assert rollback_host.module.LAUNCH_COUNT == 0
    return record


def validate_candidate(first, observations, traces):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    from tracktemplate import api
    from tracktemplate.compatibility import transition_workflow as workflow
    from tracktemplate.domain import alignment

    calculation = api.resolve_platform_longitudinal_bounds
    assert calculation is alignment.resolve_platform_longitudinal_bounds
    assert NAME in api.__all__ and NAME in alignment.__all__
    signature = inspect.signature(calculation)
    assert tuple(signature.parameters) == (
        "config", "base_start", "base_finish",
    )
    assert all(parameter.default is inspect.Parameter.empty
               for parameter in signature.parameters.values())
    _host_independent_import()
    for (label, config, start, finish), expected in zip(
        cases(), observations,
    ):
        assert label == expected["case"]
        assert observe(calculation, config, start, finish) == (
            expected["result"]
        ), label
    for item in traces:
        label = item["case"]
        assert read_observation(calculation, label) == (
            item["result"], item["events"],
        )
        for position in range(1, len(item["events"]) + 1):
            assert read_observation(calculation, label, position) == (
                read_observation(first, label, position)
            ), (label, position)
    return _synthetic_host(first, api, workflow)


def validate(baseline_only=False):
    first, observations, traces = baseline()
    route = None if baseline_only else validate_candidate(
        first, observations, traces,
    )
    return {
        "status": "PASS", "baseline_only": baseline_only,
        "definition_sha256": DEFINITION_SHA256,
        "case_count": len(observations), "observations": observations,
        "read_traces": traces, "routing": route,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.baseline_only), indent=2,
                     allow_nan=False))
    print(SENTINEL)
