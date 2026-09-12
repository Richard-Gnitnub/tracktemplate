#!/usr/bin/env python3
"""Characterise station indexing and interpolation before Core movement."""

import argparse
import ast
import copy
import dataclasses
import hashlib
import json
import math
import pathlib
import sys
import tempfile
import types
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import validate_phase1_alignment as legacy  # noqa: E402

FIELDS = (
    "alignment", "points", "headings", "stations", "total", "core_start",
    "core_end",
)
PAIR = ("alignment_station_data", "interpolate_alignment_station")
SENTINEL = "Phase 7 station mapping validation passed"


def snapshot(value):
    """Keep complete ordered values, including non-finite observations."""
    if isinstance(value, dict):
        return [[key, snapshot(item)] for key, item in value.items()]
    if isinstance(value, (tuple, list)):
        return [snapshot(item) for item in value]
    if hasattr(value, "x") and hasattr(value, "y"):
        return [snapshot(value.x), snapshot(value.y), snapshot(value.z)]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def alignments(vector_factory=legacy.Point):
    """Provide exact XY millimetres and unwrapped radian headings."""
    shapes = (
        ("straight", [(0, 0), (10, 0)], [0.0, 0.0]),
        ("unequal", [(0, 0), (3, 4), (6, 4)], [0.0, 0.5, 1.0]),
        ("negative", [(-7, -9), (-4, -5), (2, -5)], [-2.0, -1.0, 0.0]),
        ("duplicate-start", [(0, 0), (0, 0), (1, 0)], [0.0, 0.25, 0.5]),
        ("duplicate-middle", [(0, 0), (1, 0), (1, 0), (2, 0)],
         [0.0, 0.25, 0.5, 0.75]),
        ("duplicate-end", [(0, 0), (1, 0), (1, 0)], [0.0, 0.25, 0.5]),
        ("zero", [(2, 3), (2, 3), (2, 3)], [0.0, 1.0, 2.0]),
        ("span-below", [(0, 0), (0.5e-8, 0)], [3.0, -3.0]),
        ("span-equal", [(0, 0), (1.0e-8, 0)], [3.0, -3.0]),
        ("span-above", [(0, 0), (2.0e-8, 0)], [3.0, -3.0]),
        ("wrap", [(0, 0), (2, 0)], [3.0, -3.0]),
    )
    result = []
    for name, points, headings in shapes:
        result.append((name, {
            "name": name,
            "points": [vector_factory(x, y, 0.0) for x, y in points],
            "headings": list(headings),
        }))
    for name, entry, exit_length in (
        ("extensions", 2.0, 1.0),
        ("negative-extensions", -2.0, -1.0),
        ("overlap", 6.0, 6.0),
        ("clamp", 99.0, 99.0),
        ("entry-infinity", math.inf, 0.0),
        ("entry-nan", math.nan, 0.0),
        ("exit-nan", 0.0, math.nan),
    ):
        alignment = copy.deepcopy(result[1][1])
        alignment.update(name=name, entry_extension=entry,
                         exit_extension=exit_length)
        result.append((name, alignment))
    return result


def observe_error(action):
    try:
        value = action()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
        return {"exception": type(error).__name__, "message": str(error)}
    return {"result": snapshot(value)}


def error_cases(index, interpolate, vector_factory=legacy.Point):
    def point():
        return vector_factory(0.0, 0.0, 0.0)

    cases = [
        ("no-fields", {}),
        ("one-point", {"points": [point()], "headings": [0.0]}),
        ("headings-count", {"points": [point(), point()], "headings": []}),
        ("points-none", {"points": None}),
        ("headings-none", {"points": [point(), point()], "headings": None}),
        ("point-attribute", {"points": [point(), None], "headings": [0, 0]}),
        ("entry-type", {"points": [point(), point()], "headings": [0, 0],
                        "entry_extension": "bad"}),
        ("exit-type", {"points": [point(), point()], "headings": [0, 0],
                       "exit_extension": "bad"}),
    ]
    result = {
        "index": {name: observe_error(lambda item=item: index(item))
                  for name, item in cases},
        "interpolation": {},
    }
    valid = index({"points": [point(), vector_factory(1, 0, 0)],
                   "headings": [0.0, 1.0]})
    inputs = [("station-conversion", {}, "bad")]
    for key in ("total", "stations", "points", "headings"):
        data = dict(valid)
        data.pop(key)
        inputs.append(("missing-" + key, data, 0.5))
    for key, replacement in (
        ("stations", []), ("points", []), ("headings", []),
        ("points", [point(), None]), ("headings", [0.0, "bad"]),
    ):
        data = dict(valid)
        data[key] = replacement
        inputs.append(("bad-{}-{}".format(key, len(inputs)), data, 0.5))
    for name, data, station in inputs:
        result["interpolation"][name] = observe_error(
            lambda data=data, station=station: interpolate(data, station)
        )
    assert all("exception" in value for value in result["index"].values())
    assert all("exception" in value
               for value in result["interpolation"].values())
    return result


def characterise(index, interpolate, vector_factory=legacy.Point):
    """Check aliases and keep every output of the controlled pair cases."""
    result = {}
    for name, alignment in alignments(vector_factory):
        before = snapshot(alignment)
        data = index(alignment)
        assert tuple(data) == FIELDS
        assert data["alignment"] is alignment
        assert data["points"] is not alignment["points"]
        assert data["headings"] is not alignment["headings"]
        assert all(a is b for a, b in zip(data["points"], alignment["points"]))
        assert snapshot(alignment) == before
        samples = []
        stations = [-1.0, 0.0, data["total"] / 2, data["total"],
                    data["total"] + 1.0, "0.5", math.inf, -math.inf, math.nan]
        for value in data["stations"][1:-1]:
            stations.extend((math.nextafter(value, -math.inf), value,
                             math.nextafter(value, math.inf)))
        for station in stations:
            point, heading = interpolate(data, station)
            again, again_heading = interpolate(data, station)
            assert point is not again
            assert not any(point is source for source in data["points"])
            assert point.z == 0.0
            assert snapshot((point, heading)) == snapshot((again, again_heading))
            samples.append([snapshot(station), snapshot((point, heading))])
        assert snapshot(alignment) == before
        result[name] = {"data": snapshot(data), "samples": samples}
    hand = index({"points": [vector_factory(0, 0, 0),
                             vector_factory(3, 4, 0),
                             vector_factory(6, 4, 0)],
                  "headings": [0.0, 0.5, 1.0]})
    assert hand["stations"] == [0.0, 5.0, 8.0]
    sample, heading = interpolate(hand, 6.5)
    assert (sample.x, sample.y, heading) == (4.5, 4.0, 0.75)
    wrap = index(dict(alignments(vector_factory))["wrap"])
    assert interpolate(wrap, 1.0)[1] == 0.0
    original = hand["alignment"]
    original["points"].append(vector_factory(100, 0, 0))
    original["headings"].append(9.0)
    assert len(hand["points"]) == len(hand["headings"]) == 3
    hand["points"][0].x = 2.0
    assert original["points"][0].x == 2.0
    assert interpolate(hand, 0.0)[0].x == 2.0
    hand["headings"][0] = 7.0
    assert original["headings"][0] == 0.0
    assert interpolate(hand, 0.0)[1] == 7.0
    result["alias-observations"] = snapshot(hand)
    result["errors"] = error_cases(index, interpolate, vector_factory)
    return result


class LoggedPoint:
    """Expose original attribute reads without changing numeric values."""

    def __init__(self, label, events, x, y):
        self.label, self.events, self.values = label, events, (x, y)

    @property
    def x(self):
        self.events.append(self.label + ".x")
        return self.values[0]

    @property
    def y(self):
        self.events.append(self.label + ".y")
        return self.values[1]


class LoggedMapping(dict):
    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = events

    def get(self, key, default=None):
        self.events.append("get:" + key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.events.append("item:" + key)
        return super().__getitem__(key)


class LoggedStation:
    def __init__(self, events):
        self.events = events

    def __float__(self):
        self.events.append("float:station")
        return 0.5


class BrokenHeading:
    def __init__(self, events):
        self.events = events

    def __sub__(self, other):
        self.events.append("heading:subtract")
        raise ValueError("controlled heading failure")


def access_traces(pair_factory):
    """Preserve dictionary, point, vector and heading evaluation order."""
    traces = {}
    for vector_fails in (False, True):
        events = []

        def vector_factory(x, y, z=0.0):
            events.append("vector")
            if vector_fails:
                raise ValueError("controlled vector failure")
            return legacy.Point(x, y, z)

        index, interpolate = pair_factory(vector_factory)
        source = LoggedMapping(events, points=[
            LoggedPoint("a", events, 0.0, 0.0),
            LoggedPoint("b", events, 1.0, 0.0),
        ], headings=[0.0, 1.0])
        data = index(source)
        indexing = list(events)
        events.clear()
        tracked = LoggedMapping(events, data)
        value = observe_error(lambda: interpolate(
            tracked, LoggedStation(events),
        ))
        interpolation = list(events)
        events.clear()
        tracked["headings"] = [0.0, BrokenHeading(events)]
        failure = observe_error(lambda: interpolate(tracked, 0.5))
        traces[str(vector_fails)] = {
            "indexing": indexing, "interpolation": interpolation,
            "result": value, "failure_events": list(events),
            "failure": failure,
        }
        if vector_fails:
            assert "heading:subtract" not in events
        else:
            assert events.index("vector") < events.index("heading:subtract")
    return traces


def combined_error_traces(pair_factory):
    """Record the first error when two ordinary invalid inputs compete."""
    result = {}
    for name in ("count-before-point", "point-before-extension",
                 "headings-before-point", "station-before-total"):
        events = []

        def vector_factory(x, y, z=0.0):
            events.append("vector")
            return legacy.Point(x, y, z)

        index, interpolate = pair_factory(vector_factory)
        if name == "count-before-point":
            value = observe_error(lambda: index(LoggedMapping(
                events, points=[None], headings=[0.0],
                entry_extension="bad", exit_extension="bad",
            )))
        elif name == "point-before-extension":
            value = observe_error(lambda: index(LoggedMapping(
                events, points=[legacy.Point(0, 0), None], headings=[0.0, 1.0],
                entry_extension="bad", exit_extension="bad",
            )))
        elif name == "headings-before-point":
            value = observe_error(lambda: interpolate(LoggedMapping(
                events, points=[None, None], headings=[], stations=[0.0, 1.0],
                total=1.0,
            ), 0.5))
        else:
            value = observe_error(lambda: interpolate(LoggedMapping(events), "bad"))
        assert "exception" in value
        result[name] = {"events": events, "value": value}
    return result


def legacy_pair_factory(path):
    def factory(vector_factory):
        namespace, _nodes = legacy._load_alignment_namespace(path)
        namespace["vector_xy"] = vector_factory
        return tuple(namespace[name] for name in PAIR)
    return factory


def baseline():
    records = {}
    nodes = []
    for label, path in (("b14", legacy.B14_PATH), ("b15", legacy.B15_PATH)):
        namespace, definitions = legacy._load_alignment_namespace(path)
        nodes.append({name: definitions[name] for name in PAIR})
        records[label] = {
            "characterisation": characterise(*(namespace[name] for name in PAIR)),
            "access_traces": access_traces(legacy_pair_factory(path)),
            "combined_error_traces": combined_error_traces(legacy_pair_factory(path)),
        }
    assert nodes[0] == nodes[1]
    assert records["b14"] == records["b15"]
    return records


def candidate_pair_factory(vector_factory):
    from tracktemplate import api
    from tracktemplate.compatibility import transition_workflow as workflow

    return (
        workflow._AlignmentStationDataAdapter(api.alignment_station_data),
        workflow._AlignmentStationInterpolationAdapter(
            api.interpolate_alignment_station, vector_factory,
        ),
    )


def validate_neutral():
    """Check the public XY contract and its deferred, immutable result."""
    from tracktemplate import api
    from tracktemplate.domain import alignment as domain

    for name in PAIR:
        assert getattr(api, name) is getattr(domain, name)
    records = {}
    legacy_index, legacy_interpolate = legacy_pair_factory(
        legacy.B15_PATH,
    )(legacy.Point)
    for name, original in alignments():
        neutral = dict(original)
        neutral["points"] = [(point.x, point.y) for point in original["points"]]
        before = snapshot(neutral)
        result = api.alignment_station_data(neutral)
        expected = legacy_index(original)
        assert tuple(result) == FIELDS
        assert result["alignment"] is neutral
        assert result["points"] is not neutral["points"]
        assert result["headings"] is not neutral["headings"]
        assert all(a is b for a, b in zip(result["points"], neutral["points"]))
        for key in ("stations", "total", "core_start", "core_end"):
            assert snapshot(result[key]) == snapshot(expected[key])
        for station in (-1.0, 0.0, result["total"] / 2.0, result["total"],
                        result["total"] + 1.0):
            value = api.interpolate_alignment_station(result, station)
            point, heading = legacy_interpolate(expected, station)
            assert type(value) is domain.AlignmentStationInterpolation
            assert value.point == (point.x, point.y)
            assert value.heading == heading
            assert tuple(field.name for field in dataclasses.fields(value)) == (
                "point", "heading_a", "heading_b", "fraction",
            )
            try:
                value.fraction = 2.0
            except dataclasses.FrozenInstanceError:
                pass
            else:
                raise AssertionError("The transient result must be frozen")
        assert snapshot(neutral) == before
        records[name] = snapshot(result)
    events = []
    value = api.interpolate_alignment_station({
        "points": [(0.0, 0.0), (1.0, 0.0)],
        "headings": [0.0, BrokenHeading(events)],
        "stations": [0.0, 1.0], "total": 1.0,
    }, 0.5)
    assert events == []
    assert observe_error(lambda: value.heading) == {
        "exception": "ValueError", "message": "controlled heading failure",
    }
    assert events == ["heading:subtract"]
    return records


def validate_binding():
    """Reject mixed targets and preserve every binding after failed setup."""
    from tracktemplate import api
    from tracktemplate.compatibility import b15_workflow_host as loader
    from tracktemplate.compatibility import transition_workflow as workflow
    import validate_phase7_concentric_core as core

    def require_failure(action, expected_message=None):
        try:
            action()
        except workflow.TransitionWorkflowError as error:
            if expected_message is not None:
                assert str(error) == expected_message
            return
        raise AssertionError("A mixed station route was accepted")

    with tempfile.TemporaryDirectory(prefix="tracktemplate-station-") as path:
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
        assert record["contract_id"] == (
            "tracktemplate:phase7:alignment-handedness:1"
        )
        assert len(record["function_names"]) == 11
        assert len(workflow.PRODUCT_CALLER_ROUTES) == 38
        assert workflow.PRODUCT_CALLER_ROUTES == expected_caller_routes()
        assert tuple(record["function_names"][8:10]) == PAIR
        for name in workflow.PRODUCT_FUNCTION_NAMES:
            namespace[name] = object()
            require_failure(session.routing_record)
            assert namespace[name] is not original[name]
            namespace[name] = original[name]
        for name in PAIR:
            adapter = original[name]
            namespace[name] = dataclasses.replace(adapter, calculation=lambda: None)
            require_failure(session.routing_record)
            namespace[name] = original[name]
        namespace[PAIR[1]] = dataclasses.replace(
            original[PAIR[1]], vector_factory=lambda *_args: None,
        )
        require_failure(session.routing_record)
        namespace[PAIR[1]] = original[PAIR[1]]
        for name, diagnostic in (
            (PAIR[0], "station-data"), (PAIR[1], "station-interpolation"),
        ):
            adapter = original[name]
            fields = {field.name: getattr(adapter, field.name)
                      for field in dataclasses.fields(adapter)}
            subclass = type("WrongStationAdapter", (type(adapter),), {})
            invalid = [subclass(**fields)]
            invalid.extend(dataclasses.replace(adapter, **{field: object()})
                           for field in fields)
            for replacement in invalid:
                for absent in (None, *workflow.PRODUCT_FUNCTION_NAMES):
                    if absent is not None:
                        namespace.pop(absent)
                    before = dict(namespace)
                    session._host_functions[name] = replacement
                    require_failure(
                        session.launch_workflow,
                        "The modular workflow {} adapter is unavailable.".format(
                            diagnostic,
                        ),
                    )
                    assert namespace.keys() == before.keys()
                    assert all(namespace[key] is value
                               for key, value in before.items())
                    session._host_functions[name] = adapter
                    if absent is not None:
                        namespace[absent] = original[absent]
        manager = namespace["CrossoverManagerPanel"]
        method = manager.use_picked_crossover_position
        manager.use_picked_crossover_position = types.FunctionType(
            method.__code__, dict(namespace), method.__name__,
            method.__defaults__, method.__closure__,
        )
        require_failure(session.routing_record)
        manager.use_picked_crossover_position = method
        del namespace["CrossoverManagerPanel"]
        require_failure(session.routing_record)
        namespace["CrossoverManagerPanel"] = manager
        del manager.use_picked_crossover_position
        require_failure(session.routing_record)
        manager.use_picked_crossover_position = method
        name = "_project_centreline_to_reference_normal"
        caller = original[name]
        constants = tuple(
            item.replace(co_names=tuple(
                "missing_station_target" if value == PAIR[1] else value
                for value in item.co_names
            )) if isinstance(item, types.CodeType)
            and item.co_name == "point_at_station" else item
            for item in caller.__code__.co_consts
        )
        namespace[name] = types.FunctionType(
            caller.__code__.replace(co_consts=constants), namespace, name,
            caller.__defaults__, caller.__closure__,
        )
        require_failure(session.routing_record)
        namespace[name] = caller
        assert session.routing_record() == record
        for absent in (None, *workflow.PRODUCT_FUNCTION_NAMES):
            fresh = loader.load_b15_workflow_host(temporary_root, contract)
            if absent is not None:
                fresh.module.__dict__.pop(absent)
            before = dict(fresh.module.__dict__)
            with mock.patch.object(
                workflow.ModularTransitionWorkflowSession,
                "_validate_binding", side_effect=RuntimeError("controlled setup failure"),
            ):
                try:
                    workflow.ModularTransitionWorkflowSession(fresh, functions)
                except RuntimeError as error:
                    assert str(error) == "controlled setup failure"
                else:
                    raise AssertionError("Injected binding failure was ignored")
            assert fresh.module.__dict__.keys() == before.keys()
            assert all(fresh.module.__dict__[key] is value
                       for key, value in before.items())
    return record


def expected_caller_routes():
    """Derive all station caller edges from immutable B15 definitions."""
    routes = [
        ("main_circle_centre", ("clothoid_entry_displacement",)),
        ("build_concentric_core", (
            "clothoid_entry_displacement", "clothoid_exit_displacement",
        )),
        ("prepare_track_alignment", (
            "transition_start_signed_offset", "solve_transition_length",
            "build_concentric_core",
        )),
        ("run_macro", ("main_circle_centre", "build_concentric_core",
                       "add_common_straight_extensions")),
        ("build_straight_routes", ("build_straight_route",)),
    ]
    tree = ast.parse(legacy.B15_PATH.read_text())
    caller_nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            caller_nodes.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            caller_nodes.extend(
                (node.name + "." + method.name, method)
                for method in node.body if isinstance(method, ast.FunctionDef)
            )
    memberships = {target: 0 for target in PAIR}
    for name, node in sorted(caller_nodes, key=lambda item: item[1].lineno):
        calls = {call.func.id for call in ast.walk(node)
                 if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}
        targets = tuple(target for target in PAIR if target in calls)
        if not targets:
            continue
        for target in targets:
            memberships[target] += 1
        for position, (existing, edges) in enumerate(routes):
            if name == existing:
                routes[position] = (name, edges + targets)
                break
        else:
            routes.append((name, targets))
    assert memberships == {PAIR[0]: 15, PAIR[1]: 30}
    mirror_callers = [
        name for name, node in caller_nodes
        if any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "mirror_alignment_for_turn"
            for call in ast.walk(node)
        )
    ]
    assert mirror_callers == ["run_macro"]
    name, targets = routes[3]
    assert name == "run_macro"
    routes[3] = (name, targets + ("mirror_alignment_for_turn",))
    return tuple(routes)


def validate():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = baseline()
    if not args.baseline:
        pair = candidate_pair_factory(legacy.Point)
        candidate = {
            "characterisation": characterise(*pair),
            "access_traces": access_traces(candidate_pair_factory),
            "combined_error_traces": combined_error_traces(candidate_pair_factory),
        }
        assert candidate == result["b15"]
        result["candidate"] = candidate
        result["neutral"] = validate_neutral()
        result["routing"] = validate_binding()
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump({
                "stage": ("unchanged-pre-movement-baseline" if args.baseline
                          else "candidate-equivalence"),
                "source_sha256": {
                    str(path.relative_to(ROOT)): hashlib.sha256(
                        path.read_bytes()).hexdigest()
                    for path in (legacy.B14_PATH, legacy.B15_PATH)
                },
                "results": result,
            }, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


if __name__ == "__main__":
    validate()
