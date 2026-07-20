#!/usr/bin/env python3
"""Fast contracts for the Phase 1 standalone-turnout workflow oracle."""

import ast
import math
import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import turnout_recipe  # noqa: E402


B14_PATH = PROJECT_ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = PROJECT_ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
FUNCTION_NAMES = (
    "rea_c10_dimensions",
    "_turnout_orientation_sign",
    "_turnout_hand_sign",
    "turnout_valid_toe_range",
    "turnout_host_station_interval",
    "turnout_configuration_change_summary",
)
CONSTANT_NAMES = (
    "TURNOUT_DEFAULT_FLANGEWAY",
    "TURNOUT_DEFAULT_GAUGE",
    "TURNOUT_DEFAULT_SCALE",
    "TURNOUT_HAND_LEFT",
    "TURNOUT_HAND_RIGHT",
    "TURNOUT_MAX_FLANGEWAY",
    "TURNOUT_MAX_GAUGE",
    "TURNOUT_MIN_FLANGEWAY",
    "TURNOUT_MIN_GAUGE",
    "TURNOUT_ORIENTATION_FACING",
    "TURNOUT_ORIENTATION_TRAILING",
    "TURNOUT_RAIL_GEOMETRY_REVISION",
    "TURNOUT_SIZE_C10",
    "TURNOUT_TIMBER_GEOMETRY_REVISION",
)


class FakeHost:
    def __init__(self, name, **properties):
        self.Name = name
        self.properties = properties


def _read_string(host, name, default=""):
    return host.properties.get(name, default)


def _read_integer(host, name, default=0):
    return host.properties.get(name, default)


def _centreline(name, set_id, track_number, track_name):
    return FakeHost(
        name,
        TemplateSetID=set_id,
        RouteID="",
        TrackNumber=track_number,
        TrackName=track_name,
        GeneratedRole="Centreline",
        ExportSubtype="TrackCentreline",
    )


def _expect_value_error(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), str(error)
        return str(error)
    raise AssertionError("Expected ValueError containing {!r}".format(text))


def _close(actual, expected, tolerance=1.0e-9):
    assert abs(float(actual) - float(expected)) <= tolerance, (actual, expected)


def _load_turnout_namespace(path):
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
                    node.value,
                    include_attributes=False,
                )
    assert set(constants) == set(CONSTANT_NAMES)
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    ]
    namespace = {"math": math}
    namespace.update(constants)
    exec(
        compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"),
        namespace,
    )
    return namespace, {
        "functions": {
            name: ast.dump(definitions[name], include_attributes=False)
            for name in FUNCTION_NAMES
        },
        "constants": constant_nodes,
    }


def _characterise(namespace):
    dimensions = namespace["rea_c10_dimensions"]()
    expected_dimensions = {
        "size": "REA C10 natural",
        "gauge": 16.5,
        "flangeway": 1.0,
        "model_scale": 76.2,
        "inch": 1.0 / 3.0,
        "module_start_x": -21.666666666666664,
        "module_end_x": 361.3995671038812,
        "switch_radius": 3840.0,
        "turnout_radius": 2769.887101251726,
        "fine_point_x": 283.3902173610992,
        "vee_joint_x": 341.3995671038812,
        "rail_head_width": 0.9166666666666666,
        "knuckle_radius": 40.0,
    }
    for key, expected in expected_dimensions.items():
        actual = dimensions[key]
        if isinstance(expected, str):
            assert actual == expected
        else:
            _close(actual, expected)

    _expect_value_error(
        lambda: namespace["rea_c10_dimensions"](0.0, 1.0),
        "Track gauge must be between",
    )
    _expect_value_error(
        lambda: namespace["rea_c10_dimensions"](16.5, 0.0),
        "Flangeway must be between",
    )
    _expect_value_error(
        lambda: namespace["rea_c10_dimensions"](16.5, 1.0, 0.0),
        "Model scale must be greater than zero",
    )

    facing = namespace["TURNOUT_ORIENTATION_FACING"]
    trailing = namespace["TURNOUT_ORIENTATION_TRAILING"]
    left = namespace["TURNOUT_HAND_LEFT"]
    right = namespace["TURNOUT_HAND_RIGHT"]
    assert namespace["_turnout_orientation_sign"](facing) == 1.0
    assert namespace["_turnout_orientation_sign"](trailing) == -1.0
    assert namespace["_turnout_hand_sign"](left) == 1.0
    assert namespace["_turnout_hand_sign"](right) == -1.0

    host_length = 1542.475839
    facing_range = namespace["turnout_valid_toe_range"](
        host_length,
        dimensions,
        facing,
    )
    trailing_range = namespace["turnout_valid_toe_range"](
        host_length,
        dimensions,
        trailing,
    )
    _close(facing_range[0], 21.666666666666664)
    _close(facing_range[1], 1181.0762718961187)
    _close(trailing_range[0], 361.3995671038812)
    _close(trailing_range[1], 1520.8091723333332)

    facing_interval = namespace["turnout_host_station_interval"](
        turnout_recipe.TURNOUT_CHAINAGE_MM,
        dimensions,
        facing,
    )
    trailing_interval = namespace["turnout_host_station_interval"](
        turnout_recipe.TURNOUT_CHAINAGE_MM,
        dimensions,
        trailing,
    )
    _close(facing_interval[0], 724.6313333333334)
    _close(facing_interval[1], 1107.6975671038813)
    _close(trailing_interval[0], 384.8984328961188)
    _close(trailing_interval[1], 767.9646666666666)

    old = {
        "toe_chainage": turnout_recipe.TURNOUT_CHAINAGE_MM,
        "handing": left,
        "orientation": facing,
        "track_gauge": 16.5,
        "flangeway": 1.0,
        "timber_outlines": True,
        "timber_centres": False,
        "timber_numbers": True,
        "timber_length_labels": False,
        "construction_marks": True,
        "rail_geometry_revision": namespace["TURNOUT_RAIL_GEOMETRY_REVISION"],
        "timber_geometry_revision": namespace["TURNOUT_TIMBER_GEOMETRY_REVISION"],
    }
    new = dict(old)
    new["handing"] = right
    assert namespace["turnout_configuration_change_summary"](old, new) == [
        "Handing: Left-hand -> Right-hand"
    ]
    return {
        "dimensions": expected_dimensions,
        "facing_range": facing_range,
        "trailing_range": trailing_range,
        "facing_interval": facing_interval,
        "trailing_interval": trailing_interval,
    }


def _call_lines(function):
    result = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            name = target.id
        elif isinstance(target, ast.Attribute):
            name = target.attr
        else:
            continue
        result.setdefault(name, []).append(node.lineno)
    return result


def validate():
    main = _centreline("InternalMain", "SET-001", 1, "Main Track")
    track_2 = _centreline("InternalTrack2", "SET-001", 2, "Track 2")
    other = _centreline("OtherSet", "SET-009", 1, "Main Track")
    selection = turnout_recipe.select_turnout_host(
        [track_2, other, main],
        _read_string,
        _read_integer,
    )
    assert selection["index"] == 2
    assert selection["identity"]["object_name"] == "InternalMain"
    assert "XYZ" not in selection["placement_basis"]
    _expect_value_error(
        lambda: turnout_recipe.select_turnout_host(
            [main, _centreline("Duplicate", "SET-001", 1, "Main Track")],
            _read_string,
            _read_integer,
        ),
        "exactly one standalone-turnout host",
    )
    _expect_value_error(
        lambda: turnout_recipe.expected_turnout_input("Unknown"),
        "recognised handing",
    )
    assert turnout_recipe.expected_turnout_input(
        turnout_recipe.CREATED_HANDING
    )["toe_chainage"] == 746.298

    b14, b14_nodes = _load_turnout_namespace(B14_PATH)
    b15, b15_nodes = _load_turnout_namespace(B15_PATH)
    assert b14_nodes == b15_nodes
    assert _characterise(b14) == _characterise(b15)

    tree = ast.parse(B14_PATH.read_text(encoding="utf-8"), filename=str(B14_PATH))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in (
            "create_curve_inheriting_c10_turnout",
            "edit_curve_inheriting_c10_turnout",
        )
    }
    assert set(definitions) == {
        "create_curve_inheriting_c10_turnout",
        "edit_curve_inheriting_c10_turnout",
    }
    for name, function in definitions.items():
        calls = _call_lines(function)
        build_line = min(calls["_build_curve_inheriting_c10_turnout"])
        transaction_line = min(calls["openTransaction"])
        commit_line = min(calls["commitTransaction"])
        abort_line = min(calls["abortTransaction"])
        assert build_line < transaction_line < commit_line
        assert transaction_line < abort_line

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-b14-turnout"
    runner = bridge_root / "run_b14_turnout.py"
    probe = bridge_root / "probes" / "b14_turnout_driver.py"
    assert wrapper.is_file() and wrapper.stat().st_mode & 0o111
    assert runner.is_file() and runner.stat().st_mode & 0o111
    assert probe.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    probe_text = probe.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert "shutil.copy2(base_path, document_path)" in runner_text
    assert "source_fixture_sha256_after" in runner_text
    assert "phase1-b14-standalone-turnout-lifecycle-v1" in runner_text
    assert "b14_turnout_driver.py" in runner_text
    assert "manager.create_turnout" in probe_text
    assert "manager.apply_turnout_edit" in probe_text
    assert "reject_overlapping_turnout" in probe_text
    assert "module.tag_generated_object = failing_tagger" in probe_text
    assert "module.tag_generated_object = original_tagger" in probe_text
    assert "active_document.undo()" in probe_text
    assert "active_document.redo()" in probe_text
    assert "document.save()" in probe_text
    assert "App.closeDocument" in probe_text and "App.openDocument" in probe_text
    assert "plain_line_geometry_contract" in probe_text

    for digest in (
        turnout_recipe.EXPECTED_CREATED_SEMANTIC_SHA256,
        turnout_recipe.EXPECTED_EDITED_SEMANTIC_SHA256,
    ):
        assert len(digest) == 64
        int(digest, 16)

    print("Phase 1 standalone-turnout workflow oracle validation passed")


if __name__ == "__main__":
    validate()
