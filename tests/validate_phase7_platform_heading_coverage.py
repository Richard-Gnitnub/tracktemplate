#!/usr/bin/env python3
"""Compare frozen platform heading/coverage station mapping with B16 Core."""

import argparse
import ast
import hashlib
import json
import math
import pathlib
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase1_alignment as legacy  # noqa: E402
import validate_phase7_concentric_core as core_fixture  # noqa: E402


NAMES = (
    "alignment_progress_at_station", "station_for_progress_heading",
    "platform_coverage_bounds",
)
SOURCE_IDENTITIES = {
    NAMES[0]: (169, "3d034842e167ba26cdfa7d1407ada0bddc6f587b2b35058276c7ca11c27d0ab4"),
    NAMES[1]: (744, "34a972b458efe914c08aad56a28994558078c729cce44889ae4258ff61c92e4d"),
    NAMES[2]: (1326, "c9f32f25b9e735832963e414e20ed67780f8579ebdbd8a21c99e15c57c583a68"),
}
COVERAGE = (
    "Both transitions and constant curve",
    "Constant curve only",
    "Entry transition and constant curve",
    "Constant curve and exit transition",
)
SENTINEL = "Phase 7 platform heading and coverage validation passed"


def snapshot(value):
    if isinstance(value, float):
        return {"float": value.hex()}
    if isinstance(value, (tuple, list)):
        return [snapshot(item) for item in value]
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in value.items()]
    if hasattr(value, "x") and hasattr(value, "y"):
        return [snapshot(value.x), snapshot(value.y), snapshot(value.z)]
    return value


def observe(function, *arguments):
    before = snapshot(arguments)
    try:
        result = {"value": snapshot(function(*arguments))}
    except Exception as error:  # noqa: BLE001 - exact frozen failure surface
        result = {"exception": type(error).__name__, "message": str(error)}
    assert snapshot(arguments) == before
    return result


def legacy_namespace(path, vector_factory=legacy.Point):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    needed = set(NAMES + (
        "alignment_station_data", "interpolate_alignment_station",
    ))
    nodes = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in needed
    }
    assert set(nodes) == needed
    lines = source.splitlines(keepends=True)
    identities = {}
    for name in NAMES:
        node = nodes[name]
        definition = "".join(lines[node.lineno - 1:node.end_lineno]).encode()
        identities[name] = (len(definition), hashlib.sha256(definition).hexdigest())
        assert identities[name] == SOURCE_IDENTITIES[name]
    constants = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id in {
            "GEOMETRY_TOLERANCE", "PLATFORM_CORE", "PLATFORM_CONSTANT",
            "PLATFORM_ENTRY", "PLATFORM_EXIT",
        }
    }
    assert constants == {
        "GEOMETRY_TOLERANCE": 1.0e-8,
        "PLATFORM_CORE": COVERAGE[0],
        "PLATFORM_CONSTANT": COVERAGE[1],
        "PLATFORM_ENTRY": COVERAGE[2],
        "PLATFORM_EXIT": COVERAGE[3],
    }
    namespace = {
        "math": math, "bisect": __import__("bisect"), **constants,
        "vector_xy": lambda x, y: vector_factory(float(x), float(y), 0.0),
    }
    exec(compile(ast.Module(body=list(nodes.values()), type_ignores=[]),
                 str(path), "exec"), namespace)
    return namespace, identities


def alignment(points, headings, *, vector_factory=legacy.Point, **overrides):
    result = {
        "points": [vector_factory(x, y, 0.0) for x, y in points],
        "headings": list(headings),
        "entry_extension": 0.0,
        "exit_extension": 0.0,
        "entry_angle": 0.2,
        "exit_angle": 0.2,
    }
    result.update(overrides)
    return result


def alignments(vector_factory=legacy.Point):
    return (
        alignment([(0, 0), (10, 0), (20, 0)], [0.0, 0.5, 1.0],
                  vector_factory=vector_factory, entry_extension=2.0,
                  exit_extension=3.0),
        alignment([(0, 4), (8, 4), (20, 4)], [0.0, 0.4, 0.9],
                  vector_factory=vector_factory, entry_extension=1.0,
                  exit_extension=2.0,
                  entry_angle=0.25, exit_angle=0.3),
    )


def cases(namespace, neutral=False, vector_factory=legacy.Point):
    first, second = alignments(vector_factory)
    duplicate = alignment([(0, 0), (0, 0), (10, 0)], [0.0, 0.3, 1.0],
                          vector_factory=vector_factory)
    descending = alignment([(0, 0), (10, 0)], [1.0, 0.0],
                           vector_factory=vector_factory)
    flat = alignment([(0, 0), (10, 0)], [0.0, 0.0],
                     vector_factory=vector_factory)
    if neutral:
        for item in (first, second, duplicate, descending, flat):
            item["points"] = [(point.x, point.y) for point in item["points"]]
    results = []
    for label, item in (("first", first), ("second", second),
                        ("duplicate", duplicate), ("descending", descending),
                        ("flat", flat)):
        data = namespace["alignment_station_data"](item)
        for sign in (1.0, -1.0):
            for station in (-1.0, 0.0, 0.5 * data["total"],
                            data["core_end"], data["total"] + 1.0,
                            math.nan):
                results.append((
                    "progress", label, sign, snapshot(station),
                    observe(namespace[NAMES[0]], data, station, sign),
                ))
            for target in (-1.0, 0.0, 1.0e-11, 0.3, 0.5, 1.0,
                           math.nan, "invalid"):
                results.append((
                    "station", label, sign, snapshot(target),
                    observe(namespace[NAMES[1]], data, target, sign),
                ))
    bad_inputs = (
        ("no-core-start", {"core_end": 1.0}, 0.5),
        ("no-core-end", {"core_start": 0.0}, 0.5),
        ("missing-stations", {"core_start": 0.0, "core_end": 1.0}, 0.5),
    )
    for label, data, target in bad_inputs:
        results.append(("station-error", label,
                        observe(namespace[NAMES[1]], data, target, 1.0)))
    for label, selected in (
        ("one", [first]), ("two", [first, second]),
        ("empty", []),
        ("no-overlap", [dict(first, entry_angle=0.8, exit_angle=0.4)]),
        ("bad-point", [dict(first, points=[None, None])]),
    ):
        for mode in (*COVERAGE, "unknown"):
            for sign in (1.0, -1.0):
                results.append((
                    "coverage", label, mode, sign,
                    observe(namespace[NAMES[2]], selected, mode, sign),
                ))
    return results


def synthetic_host(vector_factory=None):
    with tempfile.TemporaryDirectory(prefix="tracktemplate-platform-heading-") as path:
        temporary_root = pathlib.Path(path)
        core_fixture._fixture(temporary_root)
        source = temporary_root / "legacy.FCMacro"
        content = source.read_text(encoding="utf-8")
        assert content.endswith("run_macro()\n")
        tree = ast.parse(legacy.B15_PATH.read_text())
        station = next(node for node in tree.body
                       if isinstance(node, ast.FunctionDef)
                       and node.name == NAMES[1])
        constants = "\n".join(
            "{} = {!r}".format(name, value)
            for name, value in (
                ("PLATFORM_CORE", COVERAGE[0]),
                ("PLATFORM_CONSTANT", COVERAGE[1]),
                ("PLATFORM_ENTRY", COVERAGE[2]),
                ("PLATFORM_EXIT", COVERAGE[3]),
            )
        )
        source.write_text(
            content[:-len("run_macro()\n")] + "\n" + constants
            + "\n" + ast.unparse(station) + "\nrun_macro()\n",
            encoding="utf-8",
        )
        import validate_phase3_transition_routing as phase3_fixture
        contract = phase3_fixture._contract(source)
        host = b15_workflow_host.load_b15_workflow_host(
            temporary_root, contract,
        )
        if vector_factory is not None:
            host.module.App.Vector = vector_factory
        functions = {
            name: getattr(api, name)
            for name in transition_workflow.PRODUCT_FUNCTION_NAMES
        }
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, functions,
        )
        record = session.routing_record()
        yield host.module.__dict__, session, record, temporary_root, contract


class ReadFailure(RuntimeError):
    pass


class Trace:
    def __init__(self, fail_at=None):
        self.events = []
        self.fail_at = fail_at

    def read(self, label):
        self.events.append(label)
        if len(self.events) == self.fail_at:
            raise ReadFailure(label)


class TracePoint:
    def __init__(self, x, y, trace, label):
        self._x, self._y, self.trace, self.label = x, y, trace, label

    @property
    def x(self):
        self.trace.read(self.label + ".x")
        return self._x

    @property
    def y(self):
        self.trace.read(self.label + ".y")
        return self._y


class TraceMapping(dict):
    def __init__(self, values, trace, label):
        super().__init__(values)
        self.trace, self.label = trace, label

    def __getitem__(self, key):
        self.trace.read("{}[{!r}]".format(self.label, key))
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.trace.read("{}.get({!r})".format(self.label, key))
        return super().get(key, default)


def traced_case(name, trace):
    def point(x, y, label):
        return TracePoint(x, y, trace, label)

    first = TraceMapping({
        "points": [point(0.0, 0.0, "a0"), point(10.0, 0.0, "a1")],
        "headings": [0.0, 1.0],
        "entry_extension": 0.0,
        "exit_extension": 0.0,
        "entry_angle": 0.2,
        "exit_angle": 0.2,
    }, trace, "a")
    if name == "coverage":
        second = TraceMapping({
            "points": [point(0.0, 4.0, "b0"), point(10.0, 4.0, "b1")],
            "headings": [0.0, 0.9],
            "entry_extension": 0.0,
            "exit_extension": 0.0,
            "entry_angle": 0.25,
            "exit_angle": 0.25,
        }, trace, "b")
        return ([first, second], COVERAGE[1], 1.0)
    if name == "coverage-rejection":
        first["entry_angle"] = 0.8
        first["exit_angle"] = 0.4
        return ([first], "unknown", 1.0)
    data = TraceMapping({
        "points": first["points"], "headings": first["headings"],
        "stations": [0.0, 10.0], "total": 10.0,
        "core_start": 0.0, "core_end": 10.0,
    }, trace, "data")
    trace.events.clear()
    if name == "progress":
        return (data, 5.0, 1.0)
    return (data, 0.5, 1.0)


def traced_observation(namespace, name, trace, fail_at=None):
    trace.events.clear()
    trace.fail_at = None
    function = namespace[NAMES[2] if name.startswith("coverage")
                         else NAMES[1] if name == "station"
                         else NAMES[0]]
    arguments = traced_case(name, trace)
    trace.events.clear()
    trace.fail_at = fail_at
    try:
        result = {"value": snapshot(function(*arguments))}
    except Exception as error:  # noqa: BLE001 - injected exact failure trace
        result = {"exception": type(error).__name__, "message": str(error)}
    return result, list(trace.events)


def trace_comparison():
    current = [None]

    def vector(x, y, z):
        current[0].read("App.Vector")
        return legacy.Point(x, y, z)

    b14, _identities = legacy_namespace(legacy.B14_PATH, vector)
    b15, _identities = legacy_namespace(legacy.B15_PATH, vector)
    records = {}
    for host, _session, _route, _root, _contract in synthetic_host(vector):
        for name in ("progress", "station", "coverage",
                     "coverage-rejection"):
            observations = []
            for namespace in (b14, b15, host):
                trace = Trace()
                current[0] = trace
                observation = traced_observation(namespace, name, trace)
                observations.append(observation)
            assert observations[0] == observations[1] == observations[2], name
            nominal, events = observations[0]
            failure_positions = sorted({
                1, len(events) // 2, len(events),
                next(index for index, event in enumerate(events, 1)
                     if event == "App.Vector"),
            })
            failures = []
            for position in failure_positions:
                observations = []
                for namespace in (b14, b15, host):
                    trace = Trace()
                    current[0] = trace
                    observations.append(traced_observation(
                        namespace, name, trace, position,
                    ))
                assert observations[0] == observations[1] == observations[2], (
                    name, position,
                )
                failures.append({"position": position,
                                 "result": observations[0][0],
                                 "events": observations[0][1]})
            records[name] = {"result": nominal, "events": events,
                             "failures": failures}
    return records


def validate(baseline_only=False):
    source_records = [legacy_namespace(path) for path in
                      (legacy.B14_PATH, legacy.B15_PATH)]
    b14, b15 = (item[0] for item in source_records)
    assert source_records[0][1] == source_records[1][1]
    frozen = cases(b14)
    assert cases(b15) == frozen
    host_result = []
    rollback_count = 0
    for host, session, route, temporary_root, contract in synthetic_host():
        host_result = cases(host)
        assert host_result == frozen
        if not baseline_only:
            assert route["schema_version"] == 16
            assert len(route["function_names"]) == 25
            assert len(route["caller_names"]) == 40
            assert all(host[name] is not b15[name] for name in NAMES)
            for name in NAMES:
                previous = host[name]
                host[name] = b15[name]
                try:
                    try:
                        session.routing_record()
                    except transition_workflow.TransitionWorkflowError:
                        pass
                    else:
                        raise AssertionError("A mixed platform station route passed")
                finally:
                    host[name] = previous
            assert session.routing_record() == route
            functions = {
                name: getattr(api, name)
                for name in transition_workflow.PRODUCT_FUNCTION_NAMES
            }
            for absent in (None, *NAMES):
                rollback_host = b15_workflow_host.load_b15_workflow_host(
                    temporary_root, contract,
                )
                namespace = rollback_host.module.__dict__
                if absent is not None:
                    namespace.pop(absent)
                previous = dict(namespace)
                with mock.patch.object(
                    transition_workflow.ModularTransitionWorkflowSession,
                    "_validate_binding",
                    side_effect=RuntimeError("controlled platform station failure"),
                ):
                    try:
                        transition_workflow.ModularTransitionWorkflowSession(
                            rollback_host, functions,
                        )
                    except RuntimeError as error:
                        assert str(error) == "controlled platform station failure"
                    else:
                        raise AssertionError("Controlled setup failure was lost")
                assert tuple(namespace) == tuple(previous)
                assert all(namespace[name] is value
                           for name, value in previous.items())
                rollback_count += 1
            for missing in NAMES:
                rejected = b15_workflow_host.load_b15_workflow_host(
                    temporary_root, contract,
                )
                previous = dict(rejected.module.__dict__)
                incomplete = dict(functions)
                incomplete.pop(missing)
                try:
                    transition_workflow.ModularTransitionWorkflowSession(
                        rejected, incomplete,
                    )
                except transition_workflow.TransitionWorkflowError as error:
                    assert "complete twenty-five-function" in str(error)
                else:
                    raise AssertionError("Incomplete platform station route passed")
                assert tuple(rejected.module.__dict__) == tuple(previous)
                assert all(rejected.module.__dict__[name] is value
                           for name, value in previous.items())
                rollback_count += 1
    traces = trace_comparison()
    core_result = None
    if not baseline_only:
        from tracktemplate.domain import alignment as domain
        assert all(getattr(api, name) is getattr(domain, name)
                   for name in NAMES)
        neutral = {
            "alignment_station_data": api.alignment_station_data,
            NAMES[0]: api.alignment_progress_at_station,
            NAMES[1]: api.station_for_progress_heading,
            NAMES[2]: api.platform_coverage_bounds,
        }
        # The API receives only neutral XY pairs; the host retains vectors.
        core_result = cases(neutral, neutral=True)
        assert core_result == frozen
    return {
        "status": "PASS", "baseline_only": baseline_only,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (legacy.B14_PATH, legacy.B15_PATH)
        },
        "definition_identity": source_records[0][1],
        "case_count": len(frozen),
        "b14": frozen,
        "b15": frozen,
        "current_b16": host_result,
        "core": core_result,
        "traces": traces,
        "setup_rollback_count": rollback_count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--output", type=pathlib.Path)
    arguments = parser.parse_args()
    result = validate(arguments.baseline_only)
    if arguments.output:
        with arguments.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)
