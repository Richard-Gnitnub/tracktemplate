#!/usr/bin/env python3
"""Fast contracts for the Phase 1 B14 straight/station workflow oracle."""

import ast
import bisect
import copy
import math
import pathlib
import sys
import types
import uuid


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import straight_station_recipe  # noqa: E402


B14_PATH = PROJECT_ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = PROJECT_ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
FUNCTION_NAMES = (
    "new_straight_manager_id",
    "default_straight_config",
    "clone_straight_config",
    "clone_straight_configs",
    "left_normal",
    "dot_xy",
    "polyline_length",
    "_straight_heading_delta",
    "_straight_alignment_record",
    "build_straight_route",
    "build_straight_routes",
    "validate_connected_straight_routes",
    "alignment_station_data",
    "interpolate_alignment_station",
)
CONSTANT_NAMES = (
    "DEFAULT_MAIN_TEMPLATE_WIDTH",
    "TEMPLATE_THICKNESS",
    "MAX_PARALLEL_TRACKS",
    "GEOMETRY_TOLERANCE",
    "STRAIGHT_CONNECTION_INDEPENDENT",
    "STRAIGHT_CONNECTION_CURVE_ENTRANCE",
    "STRAIGHT_CONNECTION_CURVE_EXIT",
    "STRAIGHT_DIRECTION_FORWARD",
    "STRAIGHT_DIRECTION_REVERSE",
    "STRAIGHT_PARALLEL_LEFT",
    "STRAIGHT_PARALLEL_RIGHT",
)


class Point:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


def _load_straight_namespace(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    }
    assert set(definitions) == set(FUNCTION_NAMES)
    constants = {}
    constant_nodes = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in CONSTANT_NAMES:
                constants[target.id] = ast.literal_eval(node.value)
                constant_nodes[target.id] = ast.dump(
                    node.value, include_attributes=False
                )
    assert set(constants) == set(CONSTANT_NAMES)
    selected = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    ]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {
        "bisect": bisect,
        "math": math,
        "uuid": uuid,
    }
    namespace.update(constants)
    exec(compile(module, str(path), "exec"), namespace)
    namespace["vector_xy"] = lambda x, y: Point(x, y)
    namespace["new_straight_manager_id"] = lambda: "generated-manager-id"
    return namespace, {
        "functions": {
            name: ast.dump(definitions[name], include_attributes=False)
            for name in FUNCTION_NAMES
        },
        "constants": constant_nodes,
    }


def _expect_value_error(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), str(error)
        return
    raise AssertionError("Expected ValueError containing {!r}".format(text))


def _curve_tracks():
    return [
        {
            "name": "Main Track",
            "points": [Point(0.0, 0.0), Point(100.0, 0.0)],
            "headings": [0.0, 0.0],
            "width": 32.0,
            "create_template": True,
            "show_centreline": True,
        },
        {
            "name": "Track 2",
            "points": [Point(0.0, 50.0), Point(100.0, 50.0)],
            "headings": [0.0, 0.0],
            "width": 32.0,
            "create_template": True,
            "show_centreline": True,
        },
    ]


def _connected_characterisation(namespace, lengths):
    configs = straight_station_recipe.expected_pair_configs(lengths)
    routes = namespace["build_straight_routes"](configs, _curve_tracks())
    namespace["validate_connected_straight_routes"](routes, _curve_tracks())
    module = types.SimpleNamespace(**namespace)
    analysis = straight_station_recipe.straight_route_analysis_snapshot(
        module, routes, _curve_tracks()
    )
    straight_station_recipe.validate_straight_route_analysis(analysis, lengths)
    entrance_main = analysis["semantic"]["routes"][0]["alignments"][0]
    exit_track_2 = analysis["semantic"]["routes"][1]["alignments"][1]
    assert entrance_main["points_xy_mm"] == [
        [-float(lengths[0]), 0.0],
        [0.0, 0.0],
    ]
    assert entrance_main["station"]["samples"][0]["station_mm"] == 0.0
    assert entrance_main["station"]["samples"][-1]["point_xy_mm"] == [0.0, 0.0]
    assert exit_track_2["points_xy_mm"] == [
        [100.0, 50.0],
        [100.0 + float(lengths[1]), 50.0],
    ]
    assert exit_track_2["station"]["samples"][0]["point_xy_mm"] == [100.0, 50.0]
    assert exit_track_2["station"]["samples"][-1]["station_mm"] == float(lengths[1])
    return analysis


def _independent_characterisation(namespace):
    config = namespace["default_straight_config"](0)
    config.update({
        "manager_id": "independent-test",
        "name": "Independent Test",
        "length": 100.0,
        "direction": "Reverse",
        "track_count": 2,
        "track_spacing": 50.0,
        "parallel_side": "Right of travel",
        "start_x": 10.0,
        "start_y": 20.0,
        "rotation_degrees": 90.0,
    })
    route = namespace["build_straight_route"](config, [])
    assert route["route_id"] == "straight-independent-test"
    assert len(route["alignments"]) == 2
    first, second = route["alignments"]
    assert round(first["points"][0].x, 9) == 10.0
    assert round(first["points"][0].y, 9) == 20.0
    assert round(first["points"][1].x, 9) == 10.0
    assert round(first["points"][1].y, 9) == -80.0
    assert round(second["points"][0].x, 9) == -40.0
    assert round(second["points"][0].y, 9) == 20.0
    assert round(second["points"][1].x, 9) == -40.0
    assert round(second["points"][1].y, 9) == -80.0
    return [
        [[point.x, point.y] for point in alignment["points"]]
        for alignment in route["alignments"]
    ]


def _call_name(call):
    function = call.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


def validate():
    assert straight_station_recipe.expected_pair_configs() == (
        straight_station_recipe.expected_pair_configs(
            straight_station_recipe.CREATED_LENGTHS_MM
        )
    )
    _expect_value_error(
        lambda: straight_station_recipe.expected_pair_configs((600.0,)),
        "two positive lengths",
    )
    _expect_value_error(
        lambda: straight_station_recipe.expected_pair_configs((600.0, 0.0)),
        "two positive lengths",
    )
    payload = {
        "straight_configs": straight_station_recipe.expected_pair_configs(
            straight_station_recipe.EDITED_LENGTHS_MM
        ),
        "selected_straight_index": 0,
        "output_mode": "Replace all existing generated templates",
        "saved_at": "volatile",
    }
    assert straight_station_recipe.remembered_straight_contract(payload) == (
        straight_station_recipe.expected_remembered_straight_contract(
            straight_station_recipe.EDITED_LENGTHS_MM
        )
    )
    _expect_value_error(
        lambda: straight_station_recipe.remembered_straight_contract(None),
        "did not retain an accepted",
    )

    b14, b14_nodes = _load_straight_namespace(B14_PATH)
    b15, b15_nodes = _load_straight_namespace(B15_PATH)
    assert b14_nodes == b15_nodes
    b14_created = _connected_characterisation(
        b14, straight_station_recipe.CREATED_LENGTHS_MM
    )
    b15_created = _connected_characterisation(
        b15, straight_station_recipe.CREATED_LENGTHS_MM
    )
    assert b14_created == b15_created
    assert _independent_characterisation(b14) == _independent_characterisation(b15)

    broken = copy.deepcopy(b14_created)
    broken["semantic"]["routes"][0]["alignments"][0]["join"][
        "position_error_mm"
    ] = 0.01
    broken["semantic_sha256"] = straight_station_recipe.semantic_sha256(
        broken["semantic"]
    )
    _expect_value_error(
        lambda: straight_station_recipe.validate_straight_route_analysis(
            broken, straight_station_recipe.CREATED_LENGTHS_MM
        ),
        "does not share the curve endpoint",
    )

    macro_tree = ast.parse(B14_PATH.read_text(encoding="utf-8"), filename=str(B14_PATH))
    run_macro = next(
        node for node in macro_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_macro"
    )
    call_lines = {}
    for node in ast.walk(run_macro):
        if isinstance(node, ast.Call):
            call_lines.setdefault(_call_name(node), []).append(node.lineno)
    route_line = min(call_lines["build_straight_routes"])
    validate_line = min(call_lines["validate_connected_straight_routes"])
    production_line = min(call_lines["prepare_straight_routes_production"])
    transaction_line = min(call_lines["openTransaction"])
    removal_line = min(call_lines["remove_all_generated_outputs"])
    commit_line = min(call_lines["commitTransaction"])
    assert route_line < validate_line < production_line < transaction_line
    assert transaction_line < removal_line < commit_line

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-b14-straight-station"
    runner = bridge_root / "run_b14_straight_station.py"
    probe = bridge_root / "probes" / "b14_straight_station_driver.py"
    assert wrapper.is_file() and wrapper.stat().st_mode & 0o111
    assert runner.is_file() and runner.stat().st_mode & 0o111
    assert probe.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    probe_text = probe.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert "shutil.copy2(base_path, document_path)" in runner_text
    assert "source_fixture_sha256_after" in runner_text
    assert "phase1-b14-straight-station-lifecycle-v1" in runner_text
    assert "b14_straight_station_driver.py" in runner_text
    assert "add_connected_pair_button.click()" in probe_text
    assert "module.build_straight_routes = observed_builder" in probe_text
    assert "module.build_straight_routes = original_builder" in probe_text
    assert "active_document.undo()" in probe_text
    assert "active_document.redo()" in probe_text
    assert "document.save()" in probe_text
    assert "App.closeDocument" in probe_text and "App.openDocument" in probe_text
    assert "curve_geometry_contract(created_snapshot)" in probe_text
    assert "preference_store_restored" in probe_text

    for digest in (
        straight_station_recipe.EXPECTED_CREATED_SEMANTIC_SHA256,
        straight_station_recipe.EXPECTED_EDITED_SEMANTIC_SHA256,
    ):
        assert len(digest) == 64
        int(digest, 16)

    print("Phase 1 straight/station workflow oracle validation passed")


if __name__ == "__main__":
    validate()
