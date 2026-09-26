#!/usr/bin/env python3
"""Compare the complete connected-straight gate and its live read order."""

import argparse
import ast
import hashlib
import inspect
import json
import math
import os
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_CONNECTED_STRAIGHT_SOURCE_ROOT",
    pathlib.Path(__file__).resolve().parents[1],
)).resolve()
NAME = "validate_connected_straight_routes"
DEFINITION_SHA256 = (
    "d31423808b7379f8b37682fe4e6396acdf953d36b9dafb91ee286478a56b2e9e"
)
ENTRANCE = "Curve entrance"
EXIT = "Curve exit"
INDEPENDENT = "Independent datum"
SENTINEL = "Phase 7 connected-straight validation passed"
SUFFIX = "No existing generated objects have been removed."


class Point:
    def __init__(self, x, y):
        self.x, self.y, self.z = x, y, 0.0


def legacy_namespaces(root):
    """Reuse the frozen straight/station loader without running its proof."""
    sys.path.insert(0, str(root / "tests"))
    import validate_phase1_straight_station as legacy

    namespaces = []
    paths = (legacy.B14_PATH, legacy.B15_PATH)
    for path in paths:
        assert path.parent.resolve() == root
        text = path.read_text(encoding="utf-8")
        node = next(n for n in ast.parse(text).body
                    if isinstance(n, ast.FunctionDef) and n.name == NAME)
        definition = "".join(
            text.splitlines(keepends=True)[node.lineno - 1:node.end_lineno]
        )
        assert hashlib.sha256(definition.encode()).hexdigest() == (
            DEFINITION_SHA256
        )
        namespace, _identity = legacy._load_straight_namespace(path)
        namespaces.append(namespace)
    return namespaces


def cases():
    result = []
    for mode in (ENTRANCE, EXIT, "Unknown mode", None):
        for tracks in (0, 1, 3):
            result.append((f"valid-{mode}-{tracks}", mode, tracks, {}, "pass"))
    result.append(("independent-bypass", INDEPENDENT, 3,
                   {"alignments": None}, "pass"))
    for mode in (ENTRANCE, EXIT):
        for name, changes, expected in (
            ("count", {"count": 0}, "count"),
            ("incomplete", {"points": []}, "incomplete"),
            ("one-point", {"points": [(0.0, 0.0)]}, "incomplete"),
            ("three-points", {"points": [(0.0, 0.0)] * 3}, "incomplete"),
            ("empty-curve", {"curve_points": []}, "incomplete"),
            ("missing-headings", {"headings": []}, "IndexError"),
            ("missing-curve-headings", {"curve_headings": []}, "IndexError"),
            ("none-headings-before-incomplete", {
                "points": [], "headings": None}, "TypeError"),
            ("none-curve-points", {"curve_points": None}, "TypeError"),
            ("none-alignments", {"alignments": None}, "TypeError"),
            ("endpoint", {"join": 2.0e-7}, "join"),
            ("tangent", {"heading": 2.0e-10}, "join"),
            ("wrong-side", {"projection": -1.0}, "join"),
            ("zero-travel", {"projection": 0.0}, "join"),
            ("second-track", {"bad_index": 1, "join": 2.0e-7}, "join"),
            ("nan-join", {"join": math.nan}, "pass"),
            ("nan-heading", {"heading": math.nan}, "pass"),
            ("infinite-heading", {"heading": math.inf}, "ValueError"),
            ("nan-projection", {"projection": math.nan}, "join"),
        ):
            result.append((f"{mode}-{name}", mode, 2, changes, expected))
        for value in (math.nextafter(1.0e-7, 0.0), 1.0e-7,
                      math.nextafter(1.0e-7, math.inf)):
            result.append((f"{mode}-join-{value.hex()}", mode, 1,
                           {"join": value},
                           "join" if value > 1.0e-7 else "pass"))
        for value in (math.nextafter(1.0e-10, 0.0), 1.0e-10,
                      math.nextafter(1.0e-10, math.inf), 2.0 * math.pi):
            result.append((f"{mode}-heading-{value.hex()}", mode, 1,
                           {"heading": value}, None))
        for value in (math.nextafter(1.0e-8, 0.0), 1.0e-8,
                      math.nextafter(1.0e-8, math.inf)):
            result.append((f"{mode}-travel-{value.hex()}", mode, 1,
                           {"projection": value},
                           "pass" if value > 1.0e-8 else "join"))
    return result


def inputs(case, point_factory=Point):
    _label, mode, count, changes, _expected = case
    curves, straights = [], []
    for index in range(count):
        y = 50.0 * index
        entrance = mode == ENTRANCE
        points = [(0.0, y), (100.0, y)] if entrance else [(-100.0, y), (0.0, y)]
        curves.append({"points": points, "headings": [0.0, 0.0],
                       "metadata": {"stable_id": f"curve-{index}"}})
        active = index == changes.get("bad_index", 0)
        change = changes if active else {}
        join = change.get("join", 0.0)
        travel = change.get("projection", 75.0)
        points = [(-travel, y), (join, y)] if entrance else [(join, y), (travel, y)]
        straights.append({"points": change.get("points", points),
                          "headings": change.get("headings", [
                              change.get("heading", 0.0)] * 2),
                          "metadata": {"stable_id": f"straight-{index}"}})
        if active:
            for key in ("points", "headings"):
                if "curve_" + key in change:
                    curves[-1][key] = change["curve_" + key]
    for record in curves + straights:
        if record["points"] is not None:
            record["points"] = [point_factory(*p) for p in record["points"]]
    route = {"name": "Gate 'A'", "connection_mode": mode,
             "alignments": changes.get("alignments", straights[:changes.get("count", count)])}
    return [route], curves


def snapshot(value):
    """Capture order, values and existing object identities, without .get reads."""
    if isinstance(value, dict):
        return id(value), tuple((key, snapshot(item)) for key, item in value.items())
    if isinstance(value, TraceSequence):
        return id(value), tuple(snapshot(item) for item in value.items)
    if isinstance(value, (list, tuple)):
        return id(value), tuple(snapshot(item) for item in value)
    if isinstance(value, TracePoint):
        return id(value), value.coordinates
    if isinstance(value, Point) or type(value).__name__ == "Vector":
        return id(value), value.x.hex(), value.y.hex(), value.z.hex()
    if isinstance(value, float):
        return value.hex()
    return value


def observe(function, arguments):
    before = snapshot(arguments)
    try:
        value = function(*arguments)
    except Exception as error:  # noqa: BLE001 - exact legacy error comparison
        result = (type(error).__name__, str(error))
    else:
        assert value is None, "The gate must not return replacement data"
        result = ("pass", None)
    assert snapshot(arguments) == before, "The gate mutated an input"
    return result


def assert_expected(case, observed):
    _label, _mode, count, changes, expected = case
    if expected is None:
        return  # Exact B14/B15/candidate observations own angular edge rounding.
    if expected in {"pass", "IndexError", "TypeError", "ValueError"}:
        assert observed[0] == expected, (case[0], observed)
        return
    index = changes.get("bad_index", 0) + 1
    if expected == "count":
        message = (
            "Connected straight route 'Gate 'A'' produced {} track(s), but "
            "the curve contains {} track(s). "
        ).format(changes["count"], count) + SUFFIX
    elif expected == "incomplete":
        message = (
            "Connected straight route 'Gate 'A'' contains incomplete "
            "Track {} geometry. "
        ).format(index) + SUFFIX
    else:
        message = (
            "Connected straight route 'Gate 'A'' failed its Track {} "
            "endpoint or tangent validation. "
        ).format(index) + SUFFIX
    assert observed == ("ValueError", message), (case[0], observed, message)


class ReadFailure(RuntimeError):
    pass


class Trace:
    def __init__(self, fail_at=None):
        self.events, self.fail_at = [], fail_at

    def read(self, event):
        self.events.append(event)
        if len(self.events) == self.fail_at:
            raise ReadFailure(event)


class TraceSequence:
    def __init__(self, items, label, trace):
        self.items, self.label, self.trace = items, label, trace

    def __len__(self):
        self.trace.read(self.label + ".len")
        return len(self.items)

    def __iter__(self):
        self.trace.read(self.label + ".iter")
        return iter(self.items)


class TraceMapping(dict):
    def __init__(self, source, label, trace):
        super().__init__(source)
        self.label, self.trace = label, trace

    def get(self, key, default=None):
        self.trace.read(self.label + ".get:" + key)
        return super().get(key, default)


class TracePoint:
    """Use the same labelled reads for host properties and neutral indexing."""
    def __init__(self, x, y, label, trace):
        self.coordinates, self.label, self.trace = (x, y), label, trace

    @property
    def x(self):
        self.trace.read(self.label + ".x")
        return self.coordinates[0]

    @property
    def y(self):
        self.trace.read(self.label + ".y")
        return self.coordinates[1]

    def __getitem__(self, index):
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError(index)


def traced_inputs(mode, fail_at=None):
    trace = Trace(fail_at)
    args = inputs(("read-order", mode, 1, {}, "pass"))

    def wrap(value, label):
        if isinstance(value, Point):
            return TracePoint(value.x, value.y, label, trace)
        if isinstance(value, dict):
            return TraceMapping({k: wrap(v, label + "." + k)
                                 for k, v in value.items()}, label, trace)
        if isinstance(value, list):
            return TraceSequence([wrap(v, f"{label}[{i}]")
                                  for i, v in enumerate(value)], label, trace)
        return value

    return (wrap(args[0], "routes"), wrap(args[1], "curves")), trace


def read_observation(function, mode, fail_at=None):
    args, trace = traced_inputs(mode, fail_at)
    result = observe(function, args)
    return result, trace.events


def caller_order(root):
    path = root / "AdvancedTurnout.FCMacro"
    runner = next(n for n in ast.parse(path.read_text()).body
                  if isinstance(n, ast.FunctionDef) and n.name == "run_macro")
    lines = {}
    for node in ast.walk(runner):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", getattr(node.func, "attr", None))
            lines.setdefault(name, []).append(node.lineno)
    ordered = ("build_straight_routes", NAME,
               "prepare_straight_routes_production", "openTransaction",
               "remove_all_generated_outputs")
    first = [min(lines[name]) for name in ordered]
    assert first == sorted(set(first))
    return dict(zip(ordered, first))


def validate(root, baseline_only=False):
    namespaces = legacy_namespaces(root)
    functions = [namespace[NAME] for namespace in namespaces]
    candidates = []
    if not baseline_only:
        sys.path.insert(0, str(root))
        from tracktemplate import api
        from tracktemplate.compatibility import transition_workflow
        from tracktemplate.domain import alignment

        calculation = getattr(api, NAME)
        assert calculation is getattr(alignment, NAME)
        assert tuple(inspect.signature(calculation).parameters) == (
            "straight_routes", "curve_alignments",
        )
        adapter = transition_workflow._ConnectedStraightRoutesValidationAdapter(
            calculation,
        )
        assert adapter.calculation is calculation
        candidates = [(calculation, lambda x, y: (x, y)), (adapter, Point)]
        # Separate process: no inherited test imports can conceal a host dependency.
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from tracktemplate.domain.alignment import " + NAME + "; "
            "assert not any(n.split('.')[0] in "
            "{'FreeCAD','FreeCADGui','Part','PySide','PySide2','PySide6','pivy'} "
            "or n.startswith('tracktemplate.compatibility') for n in sys.modules)"
        )
        subprocess.run([sys.executable, "-I", "-c", code, str(root)], check=True)
    observations = []
    for case in cases():
        expected = observe(functions[0], inputs(case))
        assert_expected(case, expected)
        assert observe(functions[1], inputs(case)) == expected, case[0]
        for function, point_factory in candidates:
            assert observe(function, inputs(case, point_factory)) == expected, case[0]
        observations.append({"case": case[0], "result": expected})
    trace_functions = functions + [function for function, _factory in candidates]
    for mode in (ENTRANCE, EXIT, INDEPENDENT):
        expected = read_observation(functions[0], mode)
        assert expected[0] == ("pass", None)
        assert expected[1][0] == "curves.len"
        if mode == INDEPENDENT:
            assert expected[1] == ["curves.len", "routes.iter",
                                   "routes[0].get:connection_mode"]
        for function in trace_functions[1:]:
            assert read_observation(function, mode) == expected
        # Every observed read can fail. Its exception and exact prefix must stay.
        for position in range(1, len(expected[1]) + 1):
            failure = read_observation(functions[0], mode, position)
            assert failure[0][0] == "ReadFailure"
            for function in trace_functions[1:]:
                assert read_observation(function, mode, position) == failure
    return {"status": "PASS", "baseline_only": baseline_only,
            "definition_sha256": DEFINITION_SHA256,
            "caller_order": caller_order(root), "observations": observations}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--source-root", type=pathlib.Path, default=ROOT)
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.source_root.resolve(),
                              arguments.baseline_only), indent=2))
    print(SENTINEL)
