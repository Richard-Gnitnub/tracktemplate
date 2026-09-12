#!/usr/bin/env python3
"""Prove complete alignment reflection values, aliases and failure effects."""

import argparse
import ast
import copy
import dataclasses
import hashlib
import inspect
import json
import math
import pathlib
import sys
import subprocess
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
TARGET = "mirror_alignment_for_turn"
ENDPOINTS = ("start", "end", "extended_start", "extended_end")
SENTINEL = "Phase 7 alignment handedness validation passed"


class Point:
    def __init__(self, x, y, z=0.0):
        self.x, self.y, self.z = x, y, z


class Trace:
    def __init__(self, failure=None):
        self.events = []
        self.failure = failure

    def emit(self, event):
        self.events.append(event)
        if event == self.failure:
            raise ValueError("controlled failure at " + event)


class Scalar:
    def __init__(self, trace, name, value):
        self.trace, self.name, self.value = trace, name, value

    def __neg__(self):
        self.trace.emit(self.name + ".neg")
        return Scalar(self.trace, "-" + self.name, -self.value)

    def __float__(self):
        self.trace.emit(self.name + ".float")
        return float(self.value)


class TracePoint:
    def __init__(self, trace, name, x, y):
        self.trace, self.name = trace, name
        self.values = (Scalar(trace, name + ".x", x),
                       Scalar(trace, name + ".y", y))

    @property
    def x(self):
        self.trace.emit(self.name + ".x.read")
        return self.values[0]

    @property
    def y(self):
        self.trace.emit(self.name + ".y.read")
        return self.values[1]


class TraceIterator:
    def __init__(self, source):
        self.source, self.position = source, 0

    def __iter__(self):
        return self

    def __next__(self):
        self.source.trace.emit("next:{}:{}".format(
            self.source.name, self.position,
        ))
        if self.position == len(self.source.values):
            raise StopIteration
        result = self.source.values[self.position]
        self.position += 1
        return result


class TraceIterable:
    def __init__(self, trace, name, values):
        self.trace, self.name, self.values = trace, name, values

    def __iter__(self):
        self.trace.emit("iter:" + self.name)
        return TraceIterator(self)


class TraceMapping(dict):
    def __init__(self, trace, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace = trace

    def __getitem__(self, key):
        self.trace.emit("get:" + key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self.trace.emit("set:" + key)
        super().__setitem__(key, value)

    def __contains__(self, key):
        self.trace.emit("contains:" + key)
        return super().__contains__(key)


class ComparedSign:
    def __init__(self, trace, result):
        self.trace, self.result = trace, result

    def __gt__(self, _other):
        self.trace.emit("compare:sign")
        return self.result


def snapshot(value):
    """Keep signed zeros and avoid instrumented reads while recording."""
    if isinstance(value, Scalar):
        return {"scalar": value.name, "value": snapshot(value.value)}
    if isinstance(value, TracePoint):
        return {"point": value.name, "values": snapshot(value.values)}
    if isinstance(value, TraceIterable):
        return {"iterable": value.name, "values": snapshot(value.values)}
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in dict.items(value)]
    if isinstance(value, (tuple, list)):
        return [snapshot(item) for item in value]
    if isinstance(value, float):
        return {"float": value.hex()}
    if hasattr(value, "x") and hasattr(value, "y"):
        return [snapshot(value.x), snapshot(value.y), snapshot(value.z)]
    return value


def definitions(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    selected = {node.name: node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name in {TARGET, "vector_xy", "polyline_length"}}
    assert len(selected) == 3
    return tree, selected


def legacy_factory(path):
    _tree, selected = definitions(path)

    def factory(vector_factory):
        namespace = {"App": types.SimpleNamespace(Vector=vector_factory),
                     "math": math}
        exec(compile(ast.Module(body=list(selected.values()), type_ignores=[]),
                     str(path), "exec"), namespace)
        return namespace[TARGET]
    return factory


def representative_alignment(vector_factory=Point):
    return {
        "name": "Representative main alignment", "track_number": 1,
        "points": [vector_factory(0.0, -0.0, 0.0),
                   vector_factory(3.0, 4.0, 0.0),
                   vector_factory(-2.0, -7.0, 0.0)],
        "headings": [0.0, -0.0, 3.5],
        "start": (0.0, -0.0), "end": (-2.0, -7.0),
        "extended_start": (-10.0, 0.0), "extended_end": (20.0, 30.0),
        "width": 32.0, "total_length": 123.0,
        "metadata": {"stable_id": "retained-alignment", "roles": ["main"]},
    }


def normal_characterisation(factory, vector_factory=Point):
    mirror = factory(vector_factory)
    records = []
    for sign in (1.0, 2.0, math.inf, -1.0, 0.0, -0.0, -math.inf, math.nan):
        for mask in range(16):
            source = representative_alignment(vector_factory)
            for index, key in enumerate(ENDPOINTS):
                if not mask & (1 << index):
                    source.pop(key)
            before = snapshot(source)
            old = dict(source)
            result = mirror(source, sign)
            assert result is None
            assert list(source) == list(old)
            assert source["metadata"] is old["metadata"]
            if sign > 0.0:
                assert snapshot(source) == before
                assert all(source[key] is value for key, value in old.items())
            else:
                assert source["points"] is not old["points"]
                assert source["headings"] is not old["headings"]
                for point, prior in zip(source["points"], old["points"]):
                    assert point is not prior
                    assert snapshot((point.x, point.y, point.z)) == snapshot(
                        (prior.x, -prior.y, 0.0),
                    )
                assert snapshot(source["headings"]) == snapshot(
                    [-value for value in old["headings"]],
                )
                for key in ENDPOINTS:
                    if key in old:
                        assert source[key][0] is old[key][0]
                        assert snapshot(source[key]) == snapshot(
                            (old[key][0], -old[key][1]),
                        )
                mirror(source, -1.0)
                assert snapshot(source) == before
            records.append({"sign": snapshot(sign), "endpoints_mask": mask,
                            "result": snapshot(source)})
    empty = {"points": (), "headings": (), "metadata": []}
    old = dict(empty)
    assert mirror(empty, 0.0) is None
    assert empty["points"] == empty["headings"] == []
    assert empty["metadata"] is old["metadata"]
    return records


def traced_characterisation(factory):
    failures = (
        None, "compare:sign", "get:points", "iter:points", "next:points:0",
        "p0.x.read", "p0.y.read", "p0.y.neg", "p0.x.float",
        "-p0.y.float", "vector:0", "next:points:1", "p1.x.read",
        "p1.y.read", "p1.y.neg", "p1.x.float", "-p1.y.float", "vector:1",
        "next:points:2", "set:points", "get:headings", "iter:headings",
        "next:headings:0", "h0.neg", "next:headings:1", "h1.neg",
        "next:headings:2", "set:headings",
        *(event for key in ENDPOINTS for event in
          ("contains:" + key, "get:" + key, key + ".y.neg", "set:" + key)),
    )
    records = []
    for failure in failures:
        trace = Trace(failure)
        allocations = []

        def vector_factory(x, y, z):
            trace.emit("vector:" + str(len(allocations)))
            point = Point(x, y, z)
            allocations.append(point)
            return point

        source = TraceMapping(trace, points=TraceIterable(trace, "points", [
            TracePoint(trace, "p0", 1.0, -0.0),
            TracePoint(trace, "p1", 3.0, 4.0),
        ]), headings=TraceIterable(trace, "headings", [
            Scalar(trace, "h0", 0.0), Scalar(trace, "h1", 1.0),
        ]), metadata={"stable": [1, 2]})
        for key in ENDPOINTS:
            dict.__setitem__(source, key, (Scalar(trace, key + ".x", 2.0),
                                           Scalar(trace, key + ".y", 3.0)))
        old = dict(source)
        try:
            result = factory(vector_factory)(source, ComparedSign(trace, False))
        except ValueError as error:
            assert failure is not None
            assert str(error) == "controlled failure at " + failure
            outcome = {"exception": type(error).__name__, "message": str(error)}
        else:
            assert failure is None and result is None
            outcome = {"return": None}
        records.append({
            "failure": failure, "events": trace.events,
            "state": snapshot(source), "allocations": snapshot(allocations),
            "identities_preserved": {key: dict.__getitem__(source, key) is value
                                     for key, value in old.items()},
            "outcome": outcome,
        })
    trace = Trace()
    untouched = TraceMapping(trace)
    assert factory(Point)(untouched, ComparedSign(trace, True)) is None
    assert trace.events == ["compare:sign"]
    records.append({"positive_no_reads": trace.events})
    return records


def ordinary_error_characterisation(factory):
    mirror = factory(Point)
    cases = (
        ("missing-points", {}), ("points-none", {"points": None}),
        ("point-none", {"points": [None], "headings": None}),
        ("missing-headings", {"points": [Point(1.0, 2.0)]}),
        ("headings-none", {"points": [Point(1.0, 2.0)], "headings": None}),
        ("heading-text", {"points": [Point(1.0, 2.0)], "headings": ["bad"]}),
        *(('endpoint-' + key, {
            "points": [Point(1.0, 2.0)], "headings": [0.5],
            **{previous: (1.0, 2.0) for previous in ENDPOINTS[:index]},
            key: (1.0,),
        }) for index, key in enumerate(ENDPOINTS)),
    )
    records = []
    for name, source in cases:
        old = dict(source)
        try:
            mirror(source, -1.0)
        except (KeyError, TypeError, AttributeError, ValueError) as error:
            outcome = {"exception": type(error).__name__, "message": str(error)}
        else:
            raise AssertionError("An invalid input was accepted")
        records.append({"name": name, "outcome": outcome,
                        "state": snapshot(source),
                        "identities_preserved": {
                            key: source[key] is value for key, value in old.items()
                        }})
    return records


def caller_characterisation(path, factory):
    """Execute the actual inherited reflection/length loop on both tracks."""
    import validate_phase7_concentric_core as core

    tree, selected = definitions(path)
    run_macro = next(node for node in tree.body
                     if isinstance(node, ast.FunctionDef)
                     and node.name == "run_macro")
    sites = [node for node in ast.walk(run_macro)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == TARGET]
    assert len(sites) == 1
    loop = next(node for node in ast.walk(run_macro)
                if isinstance(node, ast.For)
                and any(site is item for item in ast.walk(node) for site in sites))
    assert isinstance(loop.iter, ast.Name) and loop.iter.id == "all_alignments"
    assert len(loop.body) == 2
    assert ast.unparse(loop.body[1]) == (
        "alignment['total_length'] = polyline_length(alignment['points'])"
    )
    straight = next(node for node in ast.walk(run_macro)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "build_straight_routes")
    assert loop.end_lineno < straight.lineno
    namespace, _nodes = core.legacy_calculations(path)
    sources = [namespace["build_concentric_core"](
        (0.0, 600.0), radius, 600.0, 600.0, math.pi / 2.0, name,
    ) for radius, name in ((600.0, "Main Track"), (655.0, "Secondary Track"))]
    records = []
    for sign in (1.0, -1.0):
        alignments = copy.deepcopy(sources)
        before = snapshot(alignments)
        execution = {"all_alignments": alignments, "turn_sign": sign,
                     TARGET: factory(Point), "math": math}
        exec(compile(ast.Module(body=[selected["polyline_length"], loop],
                                type_ignores=[]), str(path), "exec"), execution)
        for old, new in zip(sources, alignments):
            assert len(old["points"]) == len(new["points"])
            expected_length = execution["polyline_length"](old["points"])
            assert new["total_length"] == expected_length
            assert new["headings"] == [sign * value for value in old["headings"]]
        records.append({"sign": sign, "before": before,
                        "after": snapshot(alignments)})
    return records


def baseline():
    results = {}
    nodes = []
    for name, path in (("b14", B14), ("b15", B15)):
        _tree, selected = definitions(path)
        nodes.append({key: ast.dump(value, include_attributes=False)
                      for key, value in selected.items()})
        factory = legacy_factory(path)
        results[name] = {
            "normal": normal_characterisation(factory),
            "traced": traced_characterisation(factory),
            "ordinary_errors": ordinary_error_characterisation(factory),
            "actual_caller": caller_characterisation(path, factory),
        }
    assert nodes[0] == nodes[1]
    assert results["b14"] == results["b15"]
    return results


def candidate_factory(vector_factory):
    from tracktemplate import api
    from tracktemplate.compatibility import transition_workflow as workflow

    return workflow._MirrorAlignmentForTurnAdapter(
        api.mirror_alignment_for_turn, vector_factory,
    )


def validate_neutral():
    """Check the independent XY rule and the public staged boundary."""
    from tracktemplate import api
    from tracktemplate.domain import alignment as domain

    assert api.mirror_alignment_for_turn is domain.mirror_alignment_for_turn
    assert TARGET in api.__all__
    assert tuple(inspect.signature(api.mirror_alignment_for_turn).parameters) == (
        "alignment", "turn_sign",
    )
    trace = Trace()
    source = TraceMapping(
        trace, points=[(1.0, -0.0), (-2.0, 3.0)],
        headings=[-0.0, 4.0], start=(1.0, -0.0), end=(-2.0, 3.0),
        metadata={"unchanged": [1, 2]},
    )
    before = snapshot(source)
    prior = dict(source)
    stages = api.mirror_alignment_for_turn(source, ComparedSign(trace, False))
    assert iter(stages) is stages
    assert trace.events == []
    key, points = next(stages)
    assert key == "points" and iter(points) is points
    assert trace.events == ["compare:sign", "get:points"]
    assert snapshot(list(points)) == snapshot([(1.0, 0.0), (-2.0, -3.0)])
    assert trace.events == ["compare:sign", "get:points"]
    key, headings = next(stages)
    assert key == "headings" and headings is not prior["headings"]
    assert snapshot(headings) == snapshot([0.0, -4.0])
    assert trace.events[-1] == "get:headings"
    assert snapshot(list(stages)) == snapshot([
        ("start", (1.0, 0.0)), ("end", (-2.0, -3.0)),
    ])
    assert trace.events == [
        "compare:sign", "get:points", "get:headings", "contains:start",
        "get:start", "contains:end", "get:end", "contains:extended_start",
        "contains:extended_end",
    ]
    assert list(stages) == []
    assert snapshot(source) == before
    assert all(dict.__getitem__(source, key) is value
               for key, value in prior.items())
    trace = Trace()
    stages = api.mirror_alignment_for_turn(
        TraceMapping(trace), ComparedSign(trace, True),
    )
    assert trace.events == [] and list(stages) == []
    assert trace.events == ["compare:sign"]
    subprocess.run([
        sys.executable, "-c",
        "import sys\n"
        "class NoHost:\n"
        " def find_spec(self, name, *args):\n"
        "  if name.split('.')[0] in ('FreeCAD', 'FreeCADGui', 'Part', "
        "'PySide', 'PySide2', 'PySide6', 'pivy'):\n"
        "   raise AssertionError('Host import: ' + name)\n"
        "sys.meta_path.insert(0, NoHost())\n"
        "from tracktemplate import api\n"
        "from tracktemplate.domain import alignment\n"
        "assert api.mirror_alignment_for_turn is alignment.mirror_alignment_for_turn\n",
    ], cwd=ROOT, check=True)


def validate_binding():
    """Exercise the actual adapter guards and complete atomic restoration."""
    from tracktemplate import api
    from tracktemplate.compatibility import b15_workflow_host as loader
    from tracktemplate.compatibility import transition_workflow as workflow
    import validate_phase7_concentric_core as core
    import validate_phase7_station_mapping as station

    def require_failure(action, message=None):
        try:
            action()
        except workflow.TransitionWorkflowError as error:
            if message is not None:
                assert str(error) == message
        else:
            raise AssertionError("An invalid handedness binding was accepted")

    def unchanged(namespace, prior):
        assert namespace.keys() == prior.keys()
        assert all(namespace[key] is value for key, value in prior.items())

    with tempfile.TemporaryDirectory(prefix="tracktemplate-handedness-") as path:
        temporary_root = pathlib.Path(path)
        contract = core._fixture(temporary_root)
        host = loader.load_b15_workflow_host(temporary_root, contract)
        functions = {name: getattr(api, name)
                     for name in workflow.PRODUCT_FUNCTION_NAMES}
        session = workflow.ModularTransitionWorkflowSession(host, functions)
        namespace = session.module.__dict__
        original = dict(namespace)
        record = session.routing_record()
        assert record["schema_version"] == 8
        assert record["contract_id"] == "tracktemplate:phase7:alignment-handedness:1"
        assert len(record["function_names"]) == 11
        assert record["function_names"][-1] == TARGET
        assert workflow.PRODUCT_CALLER_ROUTES == station.expected_caller_routes()
        assert len(workflow.PRODUCT_CALLER_ROUTES) == 38
        adapter = namespace[TARGET]
        assert type(adapter) is workflow._MirrorAlignmentForTurnAdapter
        assert adapter.calculation is api.mirror_alignment_for_turn
        assert adapter.vector_factory is namespace["App"].Vector
        assert tuple(inspect.signature(adapter).parameters) == (
            "alignment", "turn_sign",
        )
        try:
            adapter.calculation = object()
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("The handedness adapter is mutable")
        assert namespace["run_macro"].__globals__ is namespace
        assert TARGET in namespace["run_macro"].__code__.co_names
        for name in workflow.PRODUCT_FUNCTION_NAMES:
            namespace[name] = object()
            require_failure(session.routing_record)
            namespace[name] = original[name]
        fields = {field.name: getattr(adapter, field.name)
                  for field in dataclasses.fields(adapter)}
        assert tuple(fields) == ("calculation", "vector_factory")
        subclass = type("WrongHandednessAdapter", (type(adapter),), {})
        invalid = [subclass(**fields)] + [
            dataclasses.replace(adapter, **{field: object()}) for field in fields
        ]
        for replacement in invalid:
            for absent in (None, *workflow.PRODUCT_FUNCTION_NAMES):
                if absent is not None:
                    namespace.pop(absent)
                prior = dict(namespace)
                session._host_functions[TARGET] = replacement
                require_failure(
                    session.launch_workflow,
                    "The modular workflow handedness adapter is unavailable.",
                )
                unchanged(namespace, prior)
                session._host_functions[TARGET] = adapter
                if absent is not None:
                    namespace[absent] = original[absent]
        caller = namespace["run_macro"]
        namespace["run_macro"] = types.FunctionType(
            caller.__code__, dict(namespace), caller.__name__,
            caller.__defaults__, caller.__closure__,
        )
        require_failure(session.routing_record)
        namespace["run_macro"] = caller
        code = caller.__code__.replace(co_names=tuple(
            "missing_handedness_target" if name == TARGET else name
            for name in caller.__code__.co_names
        ))
        namespace["run_macro"] = types.FunctionType(code, namespace, "run_macro")
        require_failure(session.routing_record)
        namespace["run_macro"] = caller
        assert session.routing_record() == record
        for absent in (None, *workflow.PRODUCT_FUNCTION_NAMES):
            fresh = loader.load_b15_workflow_host(temporary_root, contract)
            if absent is not None:
                fresh.module.__dict__.pop(absent)
            prior = dict(fresh.module.__dict__)
            with mock.patch.object(
                workflow.ModularTransitionWorkflowSession, "_validate_binding",
                side_effect=RuntimeError("controlled setup failure"),
            ):
                try:
                    workflow.ModularTransitionWorkflowSession(fresh, functions)
                except RuntimeError as error:
                    assert str(error) == "controlled setup failure"
                else:
                    raise AssertionError("Injected binding failure was ignored")
            unchanged(fresh.module.__dict__, prior)
    return record


def validate():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = baseline()
    if not args.baseline:
        candidate = {
            "normal": normal_characterisation(candidate_factory),
            "traced": traced_characterisation(candidate_factory),
            "ordinary_errors": ordinary_error_characterisation(candidate_factory),
            "actual_caller": caller_characterisation(B15, candidate_factory),
        }
        assert candidate == result["b15"]
        result["candidate"] = candidate
        validate_neutral()
        result["routing"] = validate_binding()
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump({"status": "PASS", "stage": (
                "pre-movement baseline" if args.baseline else "candidate-equivalence"
            ),
                       "source_sha256": {path.name: hashlib.sha256(
                           path.read_bytes()).hexdigest() for path in (B14, B15)},
                       "results": result}, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


if __name__ == "__main__":
    validate()
