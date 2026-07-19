#!/usr/bin/env python3
"""Contract checks for the read-only Phase 1 macro inventory."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase1_inventory  # noqa: E402


B14_PATH = ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)


SYNTHETIC_SOURCE = """\
import math
try:
    import FreeCAD as App
except ImportError:
    App = None

OPTION: object
CACHE = {}
MODE = 0

def calc(value):
    return helper(value)

OLD_CALC = calc

def helper(value):
    return value * 2

def calc(value):
    return OLD_CALC(value) + 1

class Panel:
    pass

def refresh(self):
    return None

Panel.refresh = refresh
register(Panel)

def use(doc):
    global MODE
    MODE += 1
    CACHE.clear()
    return calc(doc)

run_macro()
"""


def _candidate(report, name):
    return next(item for item in report["candidates"] if item["name"] == name)


def _definition(report, name, active=True):
    return next(
        item for item in report["definitions"]
        if item["name"] == name and item["active"] is active
    )


def validate_synthetic_contract():
    with tempfile.TemporaryDirectory(prefix="tracktemplate-phase1-inventory-") as directory:
        path = pathlib.Path(directory) / "sample.py"
        path.write_text(SYNTHETIC_SOURCE, encoding="utf-8")
        candidates = (("calculation", ("calc",)),)
        first = phase1_inventory.analyse_source(path, "sample", candidates)
        second = phase1_inventory.analyse_source(path, "sample", candidates)
        assert first == second

        summary = first["summary"]
        assert summary["top_level_function_occurrences"] == 5
        assert summary["top_level_class_occurrences"] == 1
        assert summary["duplicate_function_names"] == 1
        assert summary["additional_function_shadowing_occurrences"] == 1
        assert summary["captured_callable_aliases"] == 1
        assert summary["module_attribute_patches"] == 1

        duplicate = first["duplicate_definitions"][0]
        assert duplicate["name"] == "calc"
        assert duplicate["captured_aliases"] == ["OLD_CALC"]
        alias = first["captured_callable_aliases"][0]
        assert alias["target"] == "OLD_CALC"
        assert alias["source_key"].startswith("calc@")
        assert first["module_attribute_patches"] == [
            {"line": 28, "target": "Panel.refresh", "source": "refresh"}
        ]
        assert [item["call"] for item in first["module_expression_calls"]] == [
            "register",
            "run_macro",
        ]

        state = {item["name"]: item for item in first["mutable_module_state"]}
        assert set(state) == {"CACHE", "MODE"}
        assert state["CACHE"]["referenced_by"] == [_definition(first, "use")["key"]]
        assert state["MODE"]["declared_global_by"] == [_definition(first, "use")["key"]]
        app_import = next(item for item in first["imports"] if "FreeCAD" in item["names"])
        assert app_import["context"] == ["try@2"]
        assert "freecad_adapter" in _definition(first, "use")["responsibility_signals"]

        calculation = _candidate(first, "calculation")
        assert calculation["missing_roots"] == []
        assert calculation["closure_definition_count"] == 3
        assert calculation["captured_alias_calls"] == ["OLD_CALC"]
        assert calculation["direct_callers"] == [
            {"name": "use", "line": _definition(first, "use")["line"]}
        ]

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            phase1_inventory.main(
                [
                    "--macro",
                    "sample={}".format(path),
                    "--candidate",
                    "calculation=calc",
                    "--compact",
                ]
            )
        payload = json.loads(output.getvalue())
        assert payload["schema_version"] == 1
        assert payload["macros"][0]["label"] == "sample"


def validate_current_macro_inventory():
    b14 = phase1_inventory.analyse_source(B14_PATH, "B14")
    b15 = phase1_inventory.analyse_source(B15_PATH, "B15")

    assert b14["source"]["sha256"] == (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    )
    assert b15["source"]["sha256"] == (
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
    )
    assert b14["source"]["newline_count"] == 47436
    assert b14["source"]["logical_lines"] == 47437
    assert b15["source"]["newline_count"] == b15["source"]["logical_lines"] == 48286

    b14_summary = b14["summary"]
    assert b14_summary["top_level_function_occurrences"] == 957
    assert b14_summary["top_level_class_occurrences"] == 18
    assert b14_summary["duplicate_function_names"] == 19
    assert b14_summary["additional_function_shadowing_occurrences"] == 26
    assert b14_summary["duplicate_class_names"] == 2
    assert b14_summary["additional_class_shadowing_occurrences"] == 3
    assert b14_summary["module_attribute_patches"] == 30

    b15_summary = b15["summary"]
    assert b15_summary["top_level_function_occurrences"] == 981
    assert b15_summary["module_attribute_patches"] == 31
    assert b15_summary["captured_callable_aliases"] == 27

    b14_curve = _candidate(b14, "curve_easement_station")
    b15_curve = _candidate(b15, "curve_easement_station")
    assert b14_curve["closure"] == b15_curve["closure"]
    assert b14_curve["closure_definition_count"] == 6
    assert b14_curve["duplicate_definition_names"] == []

    transition = _candidate(b15, "transition_length_solver")
    assert transition["closure_definition_count"] == 3
    assert transition["platform_signals"] == []
    assert transition["direct_callers"] == [
        {"name": "prepare_track_alignment", "line": 7967}
    ]
    station_index = _candidate(b15, "alignment_station_index")
    assert station_index["closure_definition_count"] == 1
    assert station_index["platform_signals"] == []
    station_interpolation = _candidate(b15, "alignment_station_interpolation")
    assert station_interpolation["closure_definition_count"] == 2
    assert station_interpolation["platform_signals"] == ["freecad"]

    b15_chair = _candidate(b15, "chair_analysis_core")
    assert b15_chair["missing_roots"] == []
    assert b15_chair["closure_definition_count"] == 39
    assert b15_chair["platform_signals"] == []
    assert "_A8A7A1_VALIDATE_CHAIR_POSITIONS" in b15_chair["captured_alias_calls"]
    assert set(b15_chair["duplicate_definition_names"]).issuperset(
        {
            "generate_chair_positions",
            "validate_chair_positions",
            "analyse_chair_position_records",
        }
    )


def validate():
    validate_synthetic_contract()
    validate_current_macro_inventory()
    print("Phase 1 macro inventory validation passed")


if __name__ == "__main__":
    validate()
