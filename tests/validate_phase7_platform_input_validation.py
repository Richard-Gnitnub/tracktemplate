#!/usr/bin/env python3
"""Compare the complete inherited platform-input gate and selected B16 route."""

import argparse
import ast
import copy
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
NAME = "validate_platform_inputs"
DEFINITION_SHA256 = (
    "1547dff9a060054e89fe6502a73c4a7cfbfad96cc257ef7a23c672895a1c4d99"
)
SENTINEL = "Phase 7 platform input validation passed"
CONSTANTS = (
    "GEOMETRY_TOLERANCE", "TEMPLATE_THICKNESS", "PLATFORM_BETWEEN",
    "PLATFORM_OUTSIDE", "PLATFORM_END_TAPERED", "PLATFORM_EDGES_ONLY",
    "PLATFORM_FACE", "PLATFORM_SOLID",
)
B14 = ROOT / "AdvancedTurnout.FCMacro"
B15 = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)


def legacy_functions():
    """Compile only the identical B14/B15 gate and its literal constants."""
    result = []
    for path in (B14, B15):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        node = next(item for item in tree.body
                    if isinstance(item, ast.FunctionDef) and item.name == NAME)
        definition = "".join(text.splitlines(keepends=True)[
            node.lineno - 1:node.end_lineno
        ])
        assert hashlib.sha256(definition.encode()).hexdigest() == (
            DEFINITION_SHA256
        )
        constants = {}
        for item in tree.body:
            if not isinstance(item, ast.Assign):
                continue
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id in CONSTANTS:
                    constants[target.id] = ast.literal_eval(item.value)
        assert set(constants) == set(CONSTANTS)
        namespace = dict(constants)
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     str(path), "exec"), namespace)
        result.append(namespace[NAME])
    return result


def base_inputs():
    config = {
        "enabled": True, "name": "Platform 'A'", "track_a_index": 0,
        "track_b_index": 1, "arrangement": "Outside one track",
        "clearance_a": 20.0, "clearance_b": 20.0,
        "platform_length": 100.0, "platform_width": 40.0,
        "body_output": "2D platform face", "platform_height": 2.0,
        "vertical_end_ramps": False, "entry_end_style": "Square",
        "entry_taper_length": 10.0, "exit_end_style": "Square",
        "exit_taper_length": 10.0, "create_edges": True,
        "check_clearance": False, "required_clearance": 17.0,
    }
    tracks = [
        {"name": "Track A", "width": 32.0, "create_template": True},
        {"name": "Track B", "width": 36.0, "create_template": True},
    ]
    return config, tracks


def cases():
    """One bounded matrix of ordered decisions and exact threshold edges."""
    thickness_edge = 1.0 + 1.0e-8
    definitions = (
        ("outside", {}, None, None),
        ("between", {"arrangement": "Between two tracks"}, None, None),
        ("disabled-bypass", {"enabled": False, "name": ""}, [], None),
        ("name-blank", {"name": " \t "}, None, None),
        ("alignments-absent", {}, [], None),
        ("a-negative", {"track_a_index": -1}, None, None),
        ("a-high", {"track_a_index": 2}, None, None),
        ("b-negative", {"arrangement": "Between two tracks",
                        "track_b_index": -1}, None, None),
        ("b-high", {"arrangement": "Between two tracks",
                    "track_b_index": 2}, None, None),
        ("same-track", {"arrangement": "Between two tracks",
                        "track_b_index": 0}, None, None),
        ("a-clearance-zero", {"clearance_a": 0.0}, None, None),
        ("b-clearance-zero", {"arrangement": "Between two tracks",
                              "clearance_b": 0.0}, None, None),
        ("length-zero", {"platform_length": 0.0}, None, None),
        ("outside-width-zero", {"platform_width": 0.0}, None, None),
        ("solid-height-zero", {"body_output": "3D platform solid",
                               "platform_height": 0.0}, None, None),
        ("ramp-at-threshold", {"body_output": "3D platform solid",
                               "vertical_end_ramps": True,
                               "platform_height": thickness_edge}, None, None),
        ("ramp-above-threshold", {"body_output": "3D platform solid",
                                  "vertical_end_ramps": True,
                                  "platform_height": math.nextafter(
                                      thickness_edge, math.inf,
                                  )}, None, None),
        ("entry-taper-zero", {"entry_end_style": "Tapered",
                              "entry_taper_length": 0.0}, None, None),
        ("exit-taper-zero", {"exit_end_style": "Tapered",
                             "exit_taper_length": 0.0}, None, None),
        ("no-output", {"create_edges": False,
                       "body_output": "Edges only (2D)"}, None, None),
        ("required-clearance-a", {"check_clearance": True,
                                  "clearance_a": 16.0}, None, None),
        ("template-width-a", {"check_clearance": True,
                              "clearance_a": 17.0}, None,
         {0: {"width": 40.0}}),
        ("required-clearance-b", {"arrangement": "Between two tracks",
                                  "check_clearance": True,
                                  "clearance_b": 16.0}, None, None),
        ("epsilon-inside", {"check_clearance": True,
                            "clearance_a": 17.0 - 1.0e-9}, None, None),
        ("epsilon-outside", {"check_clearance": True,
                             "clearance_a": math.nextafter(
                                 17.0 - 1.0e-9, -math.inf,
                             )}, None, None),
        ("disabled-clearance", {"check_clearance": False,
                                "required_clearance": 1000.0}, None, None),
        ("name-before-count", {"name": "", "track_a_index": -1}, [], None),
        ("a-before-b", {"arrangement": "Between two tracks",
                        "track_a_index": -1, "track_b_index": -1}, None, None),
        ("a-before-width", {"check_clearance": True,
                            "clearance_a": 0.0}, None,
         {0: {"width": 40.0}}),
    )
    for label, overrides, selected, track_changes in definitions:
        config, tracks = base_inputs()
        config.update(overrides)
        if selected is not None:
            tracks = selected
        if track_changes:
            for index, changes in track_changes.items():
                tracks[index].update(changes)
        yield label, config, tracks


def _input_identity(value):
    if isinstance(value, tuple):
        return tuple(_input_identity(item) for item in value)
    if isinstance(value, dict):
        return id(value), tuple((key, _input_identity(item))
                                for key, item in value.items())
    if isinstance(value, list):
        return id(value), tuple(_input_identity(item) for item in value)
    return value.hex() if isinstance(value, float) else value


def validate_mutation_detector():
    config, alignments = base_inputs()
    before = _input_identity((config, alignments))
    config["name"] = "Mutated"
    assert _input_identity((config, alignments)) != before

    config, alignments = base_inputs()
    before = _input_identity((config, alignments))
    alignments[0]["width"] = 999.0
    assert _input_identity((config, alignments)) != before


def observe(function, config, alignments):
    before = _input_identity((config, alignments))
    try:
        returned = function(config, alignments)
    except Exception as error:  # noqa: BLE001 - preserve exact legacy failure
        result = [type(error).__name__, str(error)]
    else:
        assert returned is None, "The gate returned replacement data"
        result = ["pass", None]
    assert _input_identity((config, alignments)) == before
    return result


class ReadFailure(RuntimeError):
    pass


class Trace:
    def __init__(self, fail_at=None):
        self.events, self.fail_at = [], fail_at

    def read(self, event):
        self.events.append(event)
        if len(self.events) == self.fail_at:
            raise ReadFailure(event)


class TraceMapping(dict):
    def __init__(self, source, label, trace):
        super().__init__(source)
        self.label, self.trace = label, trace

    def __getitem__(self, key):
        self.trace.read(self.label + "[" + repr(key) + "]")
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.trace.read(self.label + ".get(" + repr(key) + ")")
        return super().get(key, default)


class TraceAlignments(list):
    def __init__(self, items, trace):
        super().__init__(items)
        self.trace = trace

    def __bool__(self):
        self.trace.read("alignments.bool")
        return super().__len__() != 0

    def __len__(self):
        self.trace.read("alignments.len")
        return super().__len__()

    def __getitem__(self, index):
        self.trace.read("alignments[" + repr(index) + "]")
        return super().__getitem__(index)


def read_observation(function, label, fail_at=None):
    case = next(item for item in cases() if item[0] == label)
    trace = Trace(fail_at)
    config = TraceMapping(case[1], "config", trace)
    alignments = TraceAlignments([
        TraceMapping(track, "track[{}]".format(index), trace)
        for index, track in enumerate(case[2])
    ], trace)
    try:
        returned = function(config, alignments)
    except Exception as error:  # noqa: BLE001 - preserve exact read failure
        result = [type(error).__name__, str(error)]
    else:
        assert returned is None
        result = ["pass", None]
    return result, trace.events


def baseline():
    first, second = legacy_functions()
    observations = []
    for label, config, alignments in cases():
        expected = observe(first, config, alignments)
        assert observe(second, copy.deepcopy(config),
                       copy.deepcopy(alignments)) == expected, label
        observations.append({"case": label, "result": expected})
    assert len(observations) == 29
    traces = []
    for label in ("disabled-bypass", "outside", "between",
                  "required-clearance-b", "name-before-count"):
        expected = read_observation(first, label)
        assert read_observation(second, label) == expected, label
        for position in range(1, len(expected[1]) + 1):
            failure = read_observation(first, label, position)
            assert failure[0][0] == "ReadFailure", (label, position, failure)
            assert read_observation(second, label, position) == failure
        traces.append({"case": label, "result": expected[0],
                       "events": expected[1]})
    return first, second, observations, traces


def validate(baseline_only=False):
    validate_mutation_detector()
    first, _second, observations, traces = baseline()
    if not baseline_only:
        validate_candidate(first, observations, traces)
    return {"status": "PASS", "baseline_only": baseline_only,
            "definition_sha256": DEFINITION_SHA256,
            "observations": observations, "read_traces": traces}


def validate_candidate(first, observations, traces):
    """Run only after B16 exposes the selected domain and host binding."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    from tracktemplate import api
    from tracktemplate.compatibility import b15_workflow_host
    from tracktemplate.compatibility import transition_workflow
    from tracktemplate.domain import alignment
    import validate_phase3_transition_routing as phase3_fixture
    import validate_phase7_concentric_core as core_fixture

    calculation = api.validate_platform_inputs
    assert calculation is alignment.validate_platform_inputs
    assert NAME in api.__all__ and NAME in alignment.__all__
    assert tuple(inspect.signature(calculation).parameters) == (
        "config", "all_alignments",
    )
    assert all(parameter.default is inspect.Parameter.empty
               for parameter in inspect.signature(calculation).parameters.values())
    host_independence = """
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
assert api.validate_platform_inputs is alignment.validate_platform_inputs
assert not attempted, attempted
""".format(root=str(ROOT))
    independent = subprocess.run(
        [sys.executable, "-I", "-c", host_independence],
        capture_output=True, text=True, check=False,
    )
    assert independent.returncode == 0, independent.stdout + independent.stderr

    for (label, config, alignments), expected in zip(cases(), observations):
        assert label == expected["case"]
        assert observe(calculation, config, alignments) == (
            expected["result"]
        ), label
    for trace in traces:
        label = trace["case"]
        assert read_observation(calculation, label) == (
            trace["result"], trace["events"],
        ), label
        for position in range(1, len(trace["events"]) + 1):
            assert read_observation(calculation, label, position) == (
                read_observation(first, label, position)
            ), (label, position)

    with tempfile.TemporaryDirectory(prefix="tracktemplate-platform-input-") as path:
        temporary_root = pathlib.Path(path)
        core_fixture._fixture(temporary_root)
        source = temporary_root / "legacy.FCMacro"
        host_source = source.read_text(encoding="utf-8")
        launch = "run_macro()\n"
        assert host_source.endswith(launch)
        assert "def validate_platform_inputs(" not in host_source
        oracle_source = B14.read_text(encoding="utf-8")
        oracle_tree = ast.parse(oracle_source)
        gate = next(item for item in oracle_tree.body
                    if isinstance(item, ast.FunctionDef) and item.name == NAME)
        body = "".join(oracle_source.splitlines(keepends=True)[
            gate.lineno - 1:gate.end_lineno
        ])
        constants = {
            target.id: ast.literal_eval(item.value)
            for item in oracle_tree.body if isinstance(item, ast.Assign)
            for target in item.targets if isinstance(target, ast.Name)
            and target.id in CONSTANTS
        }
        host_source = (
            host_source[:-len(launch)]
            + "\n".join("{} = {!r}".format(name, constants[name])
                        for name in CONSTANTS)
            + "\n\n" + body + "\n" + launch
        )
        source.write_text(host_source, encoding="utf-8")
        contract = phase3_fixture._contract(source)

        def load_host():
            return b15_workflow_host.load_b15_workflow_host(
                temporary_root, contract,
            )

        def functions():
            return {
                name: getattr(api, name)
                for name in transition_workflow.PRODUCT_FUNCTION_NAMES
            }

        def expect_route_error(action, text):
            try:
                action()
            except transition_workflow.TransitionWorkflowError as error:
                assert text in str(error), str(error)
                return
            raise AssertionError("A mixed platform-input route was accepted")

        host = load_host()
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, functions(),
        )
        namespace = session.module.__dict__
        record = session.routing_record()
        assert record["schema_version"] == 16
        assert record["contract_id"] == transition_workflow.WORKFLOW_CONTRACT_ID
        assert record["function_names"] == list(
            transition_workflow.PRODUCT_FUNCTION_NAMES
        )
        assert len(record["function_names"]) == 25
        assert record["caller_names"] == [
            name for name, _targets in transition_workflow.PRODUCT_CALLER_ROUTES
        ]
        assert len(record["caller_names"]) == 40
        assert namespace[NAME] is calculation
        caller = namespace["calculate_platform_boundaries"]
        assert NAME in caller.__code__.co_names
        assert caller.__globals__ is namespace
        assert caller.__globals__[NAME] is calculation
        caller_targets = dict(transition_workflow.PRODUCT_CALLER_ROUTES)[
            "calculate_platform_boundaries"
        ]
        assert set(caller_targets) == {
            "alignment_station_data", "interpolate_alignment_station",
            "resolve_platform_longitudinal_bounds", NAME,
            "calculate_platform_top_heights",
            "platform_coverage_bounds", "station_for_progress_heading",
            "alignment_progress_at_station",
        }
        invalid = next(item for item in cases() if item[0] == "name-blank")
        expected_error = next(item["result"][1] for item in observations
                              if item["case"] == "name-blank")
        # The selected host caller must propagate the exact inherited error.
        try:
            caller(invalid[1], invalid[2], 1.0)
        except ValueError as error:
            assert str(error) == expected_error
        else:
            raise AssertionError("The selected host caller missed the gate")
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES:
            previous = namespace[name]
            namespace[name] = object()
            try:
                expect_route_error(session.routing_record, "mixed")
            finally:
                namespace[name] = previous
            assert session.routing_record() == record

        invalid_functions = functions()
        invalid_functions.pop(NAME)
        invalid_host = load_host()
        original = dict(invalid_host.module.__dict__)
        expect_route_error(
            lambda: transition_workflow.ModularTransitionWorkflowSession(
                invalid_host, invalid_functions,
            ), "complete",
        )
        assert invalid_host.module.__dict__ == original
        assert invalid_host.module.LAUNCH_COUNT == 0

        rollback_host = load_host()
        rollback_host.module.__dict__.pop(NAME)
        previous = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            transition_workflow.ModularTransitionWorkflowSession,
            "_validate_binding",
            side_effect=RuntimeError("controlled platform-input setup failure"),
        ):
            try:
                transition_workflow.ModularTransitionWorkflowSession(
                    rollback_host, functions(),
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-input setup failure"
            else:
                raise AssertionError("A controlled setup failure was lost")
        assert tuple(rollback_host.module.__dict__) == tuple(previous)
        assert all(rollback_host.module.__dict__[name] is value
                   for name, value in previous.items())
        assert NAME not in rollback_host.module.__dict__
        assert rollback_host.module.LAUNCH_COUNT == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.baseline_only), indent=2))
    print(SENTINEL)
