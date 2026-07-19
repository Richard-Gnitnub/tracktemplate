#!/usr/bin/env python3
"""Characterise the leading Phase 1 transition/station calculation boundary."""

import ast
import bisect
import math
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
B14_PATH = ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
FUNCTION_NAMES = (
    "left_normal",
    "clothoid_entry_displacement",
    "main_circle_centre",
    "transition_start_signed_offset",
    "solve_transition_length",
    "alignment_station_data",
    "interpolate_alignment_station",
)


class Point:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


def _load_alignment_namespace(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    }
    assert set(definitions) == set(FUNCTION_NAMES)
    tolerance_assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "GEOMETRY_TOLERANCE"
            for target in node.targets
        )
    ]
    assert len(tolerance_assignments) == 1
    tolerance = ast.literal_eval(tolerance_assignments[0].value)
    selected = [definitions[name] for name in FUNCTION_NAMES]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {
        "bisect": bisect,
        "math": math,
        "GEOMETRY_TOLERANCE": tolerance,
    }
    exec(compile(module, str(path), "exec"), namespace)
    namespace["vector_xy"] = lambda x, y: Point(x, y)
    return namespace, {
        name: ast.dump(definitions[name], include_attributes=False)
        for name in FUNCTION_NAMES
    }


def _expect_value_error(action, required_text):
    try:
        action()
    except ValueError as error:
        assert required_text in str(error), str(error)
        return str(error)
    raise AssertionError("Expected ValueError containing {!r}".format(required_text))


def _close(actual, expected, tolerance=1.0e-9):
    assert abs(actual - expected) <= tolerance, (actual, expected)


def _transition_characterisation(namespace):
    displacement = namespace["clothoid_entry_displacement"]
    circle_centre = namespace["main_circle_centre"]
    signed_offset = namespace["transition_start_signed_offset"]
    solve = namespace["solve_transition_length"]

    assert displacement(0.0, 600.0) == (0.0, 0.0, 0.0)
    _expect_value_error(lambda: displacement(100.0, 0.0), "greater than zero")

    x_value, y_value, angle = displacement(600.0, 600.0)
    _close(x_value, 585.1726129180435)
    _close(y_value, 98.22842842309366)
    _close(angle, 0.5, 1.0e-12)

    centre = circle_centre(600.0, 600.0)
    _close(centre[0], 297.51728975552163)
    _close(centre[1], 624.7779655573173)

    outside_length = solve(
        centre[1],
        655.0,
        -50.0,
        math.pi / 2.0,
        "Track 2",
        "Entry",
    )
    inside_length = solve(
        centre[1],
        545.0,
        50.0,
        math.pi / 2.0,
        "Inside Track",
        "Exit",
    )
    _close(outside_length, 559.4102547270278)
    _close(inside_length, 627.7998161783615)
    _close(signed_offset(centre[1], 655.0, outside_length), -50.0, 1.0e-8)
    _close(signed_offset(centre[1], 545.0, inside_length), 50.0, 1.0e-8)

    ordered_targets = (-40.0, -50.0, -60.0)
    ordered_lengths = [
        solve(centre[1], 655.0, target, math.pi / 2.0, "Track 2", "Entry")
        for target in ordered_targets
    ]
    assert ordered_lengths[0] < ordered_lengths[1] < ordered_lengths[2]

    maximum_length = (2.0 * 655.0 * (math.pi / 2.0)) - 1.0e-6
    zero_offset = signed_offset(centre[1], 655.0, 0.0)
    maximum_offset = signed_offset(centre[1], 655.0, maximum_length)
    assert solve(centre[1], 655.0, zero_offset, math.pi / 2.0, "Track", "Entry") == 0.0
    assert solve(
        centre[1], 655.0, maximum_offset, math.pi / 2.0, "Track", "Entry"
    ) == maximum_length

    _expect_value_error(
        lambda: solve(centre[1], 0.0, -50.0, math.pi / 2.0, "Bad Radius", "Entry"),
        "Bad Radius",
    )
    range_error = _expect_value_error(
        lambda: solve(centre[1], 655.0, 100.0, math.pi / 2.0, "Track 2", "Entry"),
        "cannot be produced",
    )
    assert "Requested signed offset: +100.000 mm" in range_error
    assert "Achievable signed range:" in range_error

    return {
        "clothoid": [x_value, y_value, angle],
        "circle_centre": list(centre),
        "outside_length": outside_length,
        "inside_length": inside_length,
        "ordered_lengths": ordered_lengths,
        "endpoint_lengths": [0.0, maximum_length],
    }


def _station_characterisation(namespace):
    build_data = namespace["alignment_station_data"]
    interpolate = namespace["interpolate_alignment_station"]
    points = [Point(0.0, 0.0), Point(3.0, 4.0), Point(6.0, 4.0)]
    alignment = {
        "points": points,
        "headings": [0.0, 0.5, 1.0],
        "entry_extension": 2.0,
        "exit_extension": 1.0,
    }
    data = build_data(alignment)
    assert data["alignment"] is alignment
    assert data["points"] == points
    assert data["stations"] == [0.0, 5.0, 8.0]
    assert data["total"] == 8.0
    assert data["core_start"] == 2.0
    assert data["core_end"] == 7.0

    samples = []
    for station, expected in (
        (-1.0, (0.0, 0.0, 0.0)),
        (2.5, (1.5, 2.0, 0.25)),
        (5.0, (3.0, 4.0, 0.5)),
        (6.5, (4.5, 4.0, 0.75)),
        (99.0, (6.0, 4.0, 1.0)),
    ):
        point, heading = interpolate(data, station)
        actual = (point.x, point.y, heading)
        for value, expected_value in zip(actual, expected):
            _close(value, expected_value, 1.0e-12)
        samples.append(actual)

    clamped = build_data(
        {
            "points": points,
            "headings": [0.0, 0.5, 1.0],
            "entry_extension": 99.0,
            "exit_extension": 99.0,
        }
    )
    assert clamped["core_start"] == clamped["core_end"] == 8.0

    duplicate_data = build_data(
        {
            "points": [Point(0.0, 0.0), Point(0.0, 0.0), Point(1.0, 0.0)],
            "headings": [0.0, 0.25, 0.5],
        }
    )
    duplicate_point, duplicate_heading = interpolate(duplicate_data, 0.0)
    assert (duplicate_point.x, duplicate_point.y, duplicate_heading) == (0.0, 0.0, 0.25)

    _expect_value_error(
        lambda: build_data({"points": [Point(0.0, 0.0)], "headings": [0.0]}),
        "incomplete",
    )
    _expect_value_error(
        lambda: build_data({"points": points, "headings": [0.0, 0.5]}),
        "incomplete",
    )

    return {
        "stations": data["stations"],
        "core": [data["core_start"], data["core_end"]],
        "samples": samples,
        "duplicate_station_heading": duplicate_heading,
    }


def validate():
    b14, b14_nodes = _load_alignment_namespace(B14_PATH)
    b15, b15_nodes = _load_alignment_namespace(B15_PATH)
    assert b14_nodes == b15_nodes

    b14_results = {
        "transition": _transition_characterisation(b14),
        "station": _station_characterisation(b14),
    }
    b15_results = {
        "transition": _transition_characterisation(b15),
        "station": _station_characterisation(b15),
    }
    assert b14_results == b15_results
    print("Phase 1 alignment characterisation passed")


if __name__ == "__main__":
    validate()
