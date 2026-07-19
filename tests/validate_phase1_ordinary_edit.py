#!/usr/bin/env python3
"""Fast contracts for the Phase 1 B14 ordinary-track edit/rollback recipe."""

import ast
import copy
import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import ordinary_track_edit_recipe  # noqa: E402
from tools.freecad_bridge import ordinary_track_recipe  # noqa: E402


def _call_name(call):
    function = call.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


def expect_value_error(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), str(error)
        return
    raise AssertionError("Expected ValueError containing {!r}".format(text))


def validate():
    payload = {
        "transition": 600.0,
        "radius": 600.0,
        "angle": ordinary_track_edit_recipe.TRANSACTION_FAILURE_ANGLE_DEGREES,
        "main_width": 32.0,
        "track_configs": (
            ordinary_track_edit_recipe.EXPECTED_DIALOG_TRACK_CONFIGURATION
        ),
        "output_mode": "Replace all existing generated templates",
        "saved_at": "volatile",
        "document_key": "volatile",
    }
    assert ordinary_track_edit_recipe.remembered_input_contract(payload) == (
        ordinary_track_edit_recipe.expected_remembered_input(-80.0)
    )
    expect_value_error(
        lambda: ordinary_track_edit_recipe.remembered_input_contract(None),
        "did not retain an accepted",
    )
    expect_value_error(
        lambda: ordinary_track_edit_recipe.validate_right_hand_snapshot(None),
        "Invalid ordinary-track document snapshot",
    )

    left_values = {
        "Stable": "same",
        "CircularArcAngle": 32.0,
        "TotalTurnAngle": 90.0,
        "TransitionAngleEach": 29.0,
        "TurnDirection": "Left",
    }
    right_values = dict(left_values)
    right_values.update({
        "CircularArcAngle": -32.0,
        "TotalTurnAngle": -90.0,
        "TransitionAngleEach": -29.0,
        "TurnDirection": "Right",
    })
    left_snapshot = {
        "semantic": {
            "groups": {"Group": ["Track"]},
            "objects": [{
                "name": "Track",
                "label": "Track",
                "type_id": "Part::Feature",
                "identity": {"GeneratedRole": "Centreline"},
                "identity_property_types": {
                    "GeneratedRole": "App::PropertyString"
                },
                "shape": {
                    "is_null": False,
                    "is_valid": True,
                    "shape_type": "Wire",
                    "edges": 2,
                    "length_mm": 10.0,
                    "bounds_mm": {
                        "XMin": 0.0,
                        "XMax": 10.0,
                        "XLength": 10.0,
                        "YMin": -2.0,
                        "YMax": 8.0,
                        "YLength": 10.0,
                        "ZMin": 1.0,
                        "ZMax": 1.0,
                        "ZLength": 0.0,
                    },
                },
            }],
            "persistence": {
                owner: {
                    "property_types": {name: "type" for name in left_values},
                    "values": dict(left_values),
                }
                for owner in ("settings", "template")
            },
        }
    }
    right_snapshot = copy.deepcopy(left_snapshot)
    right_shape = right_snapshot["semantic"]["objects"][0]["shape"]
    right_shape["bounds_mm"]["YMin"] = -8.0
    right_shape["bounds_mm"]["YMax"] = 2.0
    for owner in ("settings", "template"):
        right_snapshot["semantic"]["persistence"][owner]["values"] = dict(
            right_values
        )
    mirror = ordinary_track_edit_recipe.validate_handing_mirror(
        left_snapshot, right_snapshot
    )
    assert mirror["mirrored_shape_objects"] == ["Track"]
    assert mirror["changed_persisted_fields"]["settings"] == [
        "CircularArcAngle",
        "TotalTurnAngle",
        "TransitionAngleEach",
        "TurnDirection",
    ]
    broken_mirror = copy.deepcopy(right_snapshot)
    broken_mirror["semantic"]["objects"][0]["shape"]["bounds_mm"]["YMax"] = 3.0
    expect_value_error(
        lambda: ordinary_track_edit_recipe.validate_handing_mirror(
            left_snapshot, broken_mirror
        ),
        "not the reflection",
    )
    assert ordinary_track_edit_recipe.RIGHT_HAND_ANGLE_DEGREES == -90.0
    assert ordinary_track_edit_recipe.INVALID_ANGLE_DEGREES == 0.0
    assert ordinary_track_edit_recipe.TRANSACTION_FAILURE_ANGLE_DEGREES == -80.0
    assert "after generated-output removal" in (
        ordinary_track_edit_recipe.INJECTED_TRANSACTION_ERROR
    )

    macro_path = PROJECT_ROOT / "AdvancedTurnout.FCMacro"
    tree = ast.parse(macro_path.read_text(encoding="utf-8"), filename=str(macro_path))
    run_macro = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_macro"
    )
    call_lines = {}
    for node in ast.walk(run_macro):
        if not isinstance(node, ast.Call):
            continue
        call_lines.setdefault(_call_name(node), []).append(node.lineno)
    remembered_line = min(call_lines["remember_last_dialog_inputs"])
    transaction_line = min(call_lines["openTransaction"])
    removal_line = min(call_lines["remove_all_generated_outputs"])
    first_tag_line = min(call_lines["tag_generated_object"])
    commit_line = min(call_lines["commitTransaction"])
    abort_line = min(call_lines["abortTransaction"])
    assert remembered_line < transaction_line < removal_line < first_tag_line < commit_line
    assert transaction_line < abort_line
    assert min(call_lines["show_error"]) > abort_line

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-b14-ordinary-edit"
    runner = bridge_root / "run_b14_ordinary_edit.py"
    probe = bridge_root / "probes" / "b14_ordinary_edit_driver.py"
    assert wrapper.is_file() and wrapper.stat().st_mode & 0o111
    assert runner.is_file() and runner.stat().st_mode & 0o111
    assert probe.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    probe_text = probe.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert "shutil.copy2(base_path, document_path)" in runner_text
    assert "source_fixture_sha256_after" in runner_text
    assert "b14_ordinary_edit_driver.py" in runner_text
    for scenario in (
        '"replace_left_with_right"',
        '"reject_zero_angle_before_transaction"',
        '"abort_replacement_transaction"',
    ):
        assert scenario in probe_text
    assert "module.tag_generated_object = injected_tag" in probe_text
    assert "ordinary_track_document_snapshot" in probe_text
    assert "document.save()" in probe_text
    assert "App.closeDocument" in probe_text and "App.openDocument" in probe_text
    for measurement_field in (
        '"recompute_ms"',
        '"save_ms"',
        '"close_reopen_ms"',
        '"objects_after_reopen"',
    ):
        assert measurement_field in probe_text
    assert "preference_store_restored" in probe_text

    digest = ordinary_track_edit_recipe.EXPECTED_RIGHT_HAND_SEMANTIC_SHA256
    assert len(digest) == 64
    int(digest, 16)

    print("Phase 1 ordinary-track edit/rollback validation passed")


if __name__ == "__main__":
    validate()
