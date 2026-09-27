#!/usr/bin/env python3
"""Compare frozen platform top heights with Core and selected B16 routing."""

import argparse
import ast
import hashlib
import inspect
import json
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
NAME = "calculate_platform_top_heights"
DEFINITION_SHA256 = (
    "1eda69de0e8abb22c14c9acb4d90b8de09476b0db506f13f07e866247a7df90f"
)
DEFINITION_BYTES = 1401
CONSTANTS = (
    "GEOMETRY_TOLERANCE", "TEMPLATE_THICKNESS",
    "PLATFORM_END_TAPERED", "PLATFORM_SOLID",
)
SENTINEL = "Phase 7 platform top heights validation passed"


def legacy_functions():
    """Compile the byte-identical B14/B15 calculation and its constants."""
    functions = []
    for path in (B14, B15):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        node = next(item for item in tree.body
                    if isinstance(item, ast.FunctionDef)
                    and item.name == NAME)
        definition = "".join(source.splitlines(keepends=True)[
            node.lineno - 1:node.end_lineno
        ])
        encoded = definition.encode("utf-8")
        assert len(encoded) == DEFINITION_BYTES
        assert hashlib.sha256(encoded).hexdigest() == DEFINITION_SHA256
        constants = {
            target.id: ast.literal_eval(item.value)
            for item in tree.body if isinstance(item, ast.Assign)
            for target in item.targets if isinstance(target, ast.Name)
            and target.id in CONSTANTS
        }
        assert constants == {
            "GEOMETRY_TOLERANCE": 1.0e-8,
            "TEMPLATE_THICKNESS": 1.0,
            "PLATFORM_END_TAPERED": "Tapered",
            "PLATFORM_SOLID": "3D platform solid",
        }
        namespace = dict(constants)
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     str(path), "exec"), namespace)
        functions.append(namespace[NAME])
    return functions


def base_config():
    return {
        "platform_height": 15.0,
        "body_output": "3D platform solid",
        "entry_end_style": "Square",
        "entry_taper_length": 40.0,
        "exit_end_style": "Square",
        "exit_taper_length": 30.0,
    }


def cases():
    """Exercise both output modes, ramp overlap and inherited failures."""
    definitions = (
        ("edges", {"body_output": "Edges only (2D)"},
         [0.0, 50.0, 100.0], 100.0),
        ("face", {"body_output": "2D platform face"},
         [-10.0, "ignored", 110.0], 100.0),
        ("solid-square", {}, [0.0, 50.0, 100.0], 100.0),
        ("entry-ramp", {"entry_end_style": "Tapered"},
         [-10.0, 0.0, 10.0, 20.0, 40.0, 50.0], 100.0),
        ("exit-ramp", {"exit_end_style": "Tapered"},
         [50.0, 70.0, 85.0, 100.0, 110.0], 100.0),
        ("overlap", {
            "entry_end_style": "Tapered", "entry_taper_length": 70.0,
            "exit_end_style": "Tapered", "exit_taper_length": 70.0,
        }, [0.0, 25.0, 50.0, 75.0, 100.0], 100.0),
        ("height-below-trackbed", {"platform_height": 0.5},
         [0.0, 50.0, 100.0], 100.0),
        ("flat-below-trackbed", {
            "platform_height": 0.5, "body_output": "2D platform face",
        }, [0.0, 50.0], 100.0),
        ("entry-zero", {
            "entry_end_style": "Tapered", "entry_taper_length": 0.0,
        }, [0.0, 20.0], 100.0),
        ("exit-negative", {
            "exit_end_style": "Tapered", "exit_taper_length": -1.0,
        }, [80.0, 100.0], 100.0),
        ("empty-stations", {}, [], 100.0),
        ("tuple-stations", {}, (0.0, 100.0), 100.0),
        ("bool-height", {"platform_height": True}, [0.0], 100.0),
        ("none-height", {"platform_height": None}, [0.0], 100.0),
        ("bad-height", {"platform_height": "invalid"}, [0.0], 100.0),
        ("missing-body", {"body_output": None}, [0.0], 100.0),
        ("bad-entry-length", {
            "entry_end_style": "Tapered", "entry_taper_length": "invalid",
        }, [0.0], 100.0),
        ("bad-exit-length", {
            "exit_end_style": "Tapered", "exit_taper_length": None,
        }, [100.0], 100.0),
        ("bad-entry-station", {"entry_end_style": "Tapered"},
         ["invalid"], 100.0),
        ("bad-exit-station", {"exit_end_style": "Tapered"},
         ["invalid"], 100.0),
        ("bad-platform-length", {"exit_end_style": "Tapered"},
         [100.0], "invalid"),
        ("nan-height", {"platform_height": float("nan")},
         [0.0, 50.0], 100.0),
        ("infinite-height", {"platform_height": float("inf")},
         [0.0, 50.0], 100.0),
        ("nan-station", {"entry_end_style": "Tapered"},
         [float("nan")], 100.0),
    )
    for label, overrides, stations, platform_length in definitions:
        config = base_config()
        config.update(overrides)
        yield label, config, stations, platform_length


def snapshot(value):
    if isinstance(value, TraceNumber):
        return snapshot(value.value)
    if isinstance(value, TraceStations):
        return [snapshot(item) for item in list.__iter__(value)]
    if isinstance(value, float):
        return {"float": value.hex()}
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in value.items()]
    if isinstance(value, (list, tuple)):
        return [snapshot(item) for item in value]
    if hasattr(value, "x") and hasattr(value, "y"):
        return [snapshot(value.x), snapshot(value.y), snapshot(value.z)]
    return value


def observe(function, config, stations, platform_length):
    identities = id(config), id(stations)
    before = snapshot((config, stations, platform_length))
    try:
        returned = function(config, stations, platform_length)
    except Exception as error:  # noqa: BLE001 - preserve inherited failure
        result = {"exception": type(error).__name__, "message": str(error)}
    else:
        assert isinstance(returned, list)
        result = {"value": snapshot(returned)}
    assert (id(config), id(stations)) == identities
    assert snapshot((config, stations, platform_length)) == before
    return result


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

    def __lt__(self, other):
        self.trace.read(self.label + ".lt")
        return self.value < other

    def __truediv__(self, other):
        self.trace.read(self.label + ".truediv")
        return self.value / other

    def __rsub__(self, other):
        self.trace.read(self.label + ".rsub")
        return other - self.value


class TraceConfig(dict):
    def __init__(self, source, trace):
        super().__init__(source)
        self.trace = trace

    def __getitem__(self, key):
        self.trace.read("config[" + repr(key) + "]")
        return super().__getitem__(key)


class TraceStations(list):
    def __init__(self, values, trace):
        super().__init__(values)
        self.trace = trace

    def __iter__(self):
        self.trace.read("stations.iter")
        for index in range(len(self)):
            self.trace.read("stations[{}]".format(index))
            yield TraceNumber(
                list.__getitem__(self, index),
                "station[{}]".format(index), self.trace,
            )


def traced_case(label, fail_at=None):
    trace = Trace(fail_at)
    config = base_config()
    stations = [0.0, 25.0, 100.0]
    if label == "non-solid":
        config["body_output"] = "2D platform face"
    elif label == "solid-square":
        pass
    elif label == "entry":
        config["entry_end_style"] = "Tapered"
    elif label == "exit":
        config["exit_end_style"] = "Tapered"
    elif label == "both":
        config.update(entry_end_style="Tapered",
                      exit_end_style="Tapered")
    else:
        raise AssertionError(label)
    for key in ("platform_height", "entry_taper_length",
                "exit_taper_length"):
        config[key] = TraceNumber(config[key], "config." + key, trace)
    traced_config = TraceConfig(config, trace)
    traced_stations = TraceStations(stations, trace)
    return trace, traced_config, traced_stations


def read_observation(function, label, fail_at=None):
    trace, config, stations = traced_case(label, fail_at)
    result = observe(function, config, stations, 100.0)
    return result, trace.events


def baseline():
    first, second = legacy_functions()
    observations = []
    for label, config, stations, platform_length in cases():
        expected = observe(first, config, stations, platform_length)
        assert observe(
            second, dict(config), type(stations)(stations), platform_length,
        ) == expected, label
        observations.append({"case": label, "result": expected})
    assert len(observations) == 24
    traces = []
    for label in ("non-solid", "solid-square", "entry", "exit", "both"):
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
assert api.calculate_platform_top_heights is (
    alignment.calculate_platform_top_heights
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

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-platform-heights-",
    ) as path:
        temporary_root = pathlib.Path(path)
        core_fixture._fixture(temporary_root)
        source = temporary_root / "legacy.FCMacro"
        content = source.read_text(encoding="utf-8")
        launch = "run_macro()\n"
        assert content.endswith(launch)
        tree = ast.parse(B14.read_text(encoding="utf-8"))
        definition = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == NAME
        )
        source.write_text(
            content[:-len(launch)] + "\n" + ast.unparse(definition)
            + "\n" + launch,
            encoding="utf-8",
        )
        contract = phase3_fixture._contract(source)

        def load_host():
            return b15_workflow_host.load_b15_workflow_host(
                temporary_root, contract,
            )

        def functions():
            return {
                name: getattr(api, name)
                for name in workflow.PRODUCT_FUNCTION_NAMES
            }

        host = load_host()
        namespace = host.module.__dict__
        original_caller = namespace["calculate_platform_boundaries"]
        assert original_caller.__globals__ is namespace
        assert original_caller.__globals__[NAME] is not api.__dict__[NAME]
        assert NAME in original_caller.__code__.co_names
        session = workflow.ModularTransitionWorkflowSession(host, functions())
        record = session.routing_record()
        assert record["schema_version"] == 16
        assert record["contract_id"] == (
            "tracktemplate:phase7:platform-top-heights:1"
        )
        assert record["function_names"] == list(
            workflow.PRODUCT_FUNCTION_NAMES
        )
        assert len(record["function_names"]) == 25
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
            "validate_platform_inputs", "resolve_platform_longitudinal_bounds",
            NAME, "platform_coverage_bounds", "station_for_progress_heading",
            "alignment_progress_at_station",
        }

        namespace[NAME] = first
        try:
            try:
                session.routing_record()
            except workflow.TransitionWorkflowError as error:
                assert "mixed" in str(error)
            else:
                raise AssertionError("A mixed platform-height route passed")
        finally:
            namespace[NAME] = api.__dict__[NAME]
        assert session.routing_record() == record

        incomplete = functions()
        incomplete.pop(NAME)
        rejected_host = load_host()
        previous = dict(rejected_host.module.__dict__)
        try:
            workflow.ModularTransitionWorkflowSession(
                rejected_host, incomplete,
            )
        except workflow.TransitionWorkflowError as error:
            assert "complete twenty-five-function" in str(error)
        else:
            raise AssertionError("An incomplete platform-height route passed")
        assert tuple(rejected_host.module.__dict__) == tuple(previous)
        assert all(rejected_host.module.__dict__[name] is value
                   for name, value in previous.items())

        rollback_host = load_host()
        rollback_host.module.__dict__.pop(NAME)
        previous = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            workflow.ModularTransitionWorkflowSession, "_validate_binding",
            side_effect=RuntimeError("controlled platform-height failure"),
        ):
            try:
                workflow.ModularTransitionWorkflowSession(
                    rollback_host, functions(),
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-height failure"
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

    calculation = api.calculate_platform_top_heights
    assert calculation is alignment.calculate_platform_top_heights
    assert NAME in api.__all__ and NAME in alignment.__all__
    signature = inspect.signature(calculation)
    assert tuple(signature.parameters) == (
        "config", "stations", "platform_length",
    )
    assert all(parameter.default is inspect.Parameter.empty
               for parameter in signature.parameters.values())
    _host_independent_import()
    for (label, config, stations, platform_length), expected in zip(
        cases(), observations,
    ):
        assert label == expected["case"]
        assert observe(calculation, config, stations, platform_length) == (
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
