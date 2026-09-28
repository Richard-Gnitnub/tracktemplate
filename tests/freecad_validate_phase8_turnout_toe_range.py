#!/usr/bin/env python3
"""Prove the internal turnout range and occupied interval on the B15 host."""

import hashlib
import json
import os
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(
    os.environ.get("TRACKTEMPLATE_TURNOUT_SOURCE_ROOT", ROOT)
).resolve()
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.application import turnout_edit  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain import turnout  # noqa: E402
import validate_phase1_turnout as oracle  # noqa: E402


SENTINEL = "Phase 8 turnout toe-range FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CALLERS = (
    "_build_curve_inheriting_c10_turnout",
    "_crossover_solve_toe_b",
    "solve_rea_c10_crossover_geometry",
    "CrossoverManagerPanel.update_chainage_range",
    "TurnoutManagerDialog.update_host_summary",
)
INTERVAL_CALLERS = (
    "_turnout_find_overlap",
    "_build_curve_inheriting_c10_turnout",
    "build_turnout_host_integration",
    "solve_rea_c10_crossover_geometry",
)
SUMMARY_CALLERS = (
    "edit_curve_inheriting_c10_turnout",
    "TurnoutManagerDialog.update_host_summary",
    "TurnoutManagerDialog.apply_turnout_edit",
)


def document_state():
    return {
        "active": getattr(App.ActiveDocument, "Name", None),
        "documents": {
            name: (
                document.Label,
                document.FileName,
                tuple((obj.Name, obj.TypeId) for obj in document.Objects),
                document.UndoCount,
                document.RedoCount,
            )
            for name, document in sorted(App.listDocuments().items())
        },
    }


def caller(module, name):
    if "." in name:
        class_name, method_name = name.split(".", 1)
        return getattr(getattr(module, class_name), method_name)
    return getattr(module, name)


def validate():
    before = document_state()
    assert pathlib.Path(api.__file__).resolve() == SOURCE_ROOT / "tracktemplate/api.py"
    assert pathlib.Path(transition_workflow.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/compatibility/transition_workflow.py"
    )
    assert pathlib.Path(turnout_edit.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/application/turnout_edit.py"
    )
    assert pathlib.Path(turnout.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/domain/turnout.py"
    )
    launcher = runpy.run_path(str(SOURCE_ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](SOURCE_ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        SOURCE_ROOT, api, contract,
    )
    module = session.module
    namespace = module.__dict__
    record = session.routing_record()
    assert record["schema_version"] == 16
    assert len(record["function_names"]) == 25
    assert len(record["caller_names"]) == 40
    assert "turnout_valid_toe_range" not in record["function_names"]
    assert "turnout_host_station_interval" not in record["function_names"]
    assert "turnout_configuration_change_summary" not in record["function_names"]
    assert not hasattr(api, "turnout_valid_toe_range")
    assert not hasattr(api, "turnout_host_station_interval")
    assert not hasattr(api, "turnout_configuration_change_summary")
    assert namespace["turnout_valid_toe_range"] is turnout.turnout_valid_toe_range
    assert namespace["turnout_host_station_interval"] is (
        turnout.turnout_host_station_interval
    )
    summary = namespace["turnout_configuration_change_summary"]
    assert type(summary) is (
        transition_workflow._TurnoutConfigurationSummaryAdapter
    )
    assert summary.calculation is (
        turnout_edit.turnout_configuration_change_summary
    )
    assert summary.host_globals is namespace
    for name in CALLERS:
        function = caller(module, name)
        assert function.__globals__ is namespace, name
        assert "turnout_valid_toe_range" in function.__code__.co_names, name
        assert function.__globals__["turnout_valid_toe_range"] is (
            turnout.turnout_valid_toe_range
        ), name
    for name in INTERVAL_CALLERS:
        function = caller(module, name)
        assert function.__globals__ is namespace, name
        assert "turnout_host_station_interval" in function.__code__.co_names, name
        assert function.__globals__["turnout_host_station_interval"] is (
            turnout.turnout_host_station_interval
        ), name
    for name in SUMMARY_CALLERS:
        function = caller(module, name)
        assert function.__globals__ is namespace, name
        assert "turnout_configuration_change_summary" in (
            function.__code__.co_names
        ), name
        assert function.__globals__["turnout_configuration_change_summary"] is (
            summary
        ), name

    frozen = []
    for path in (oracle.B14_PATH, oracle.B15_PATH):
        legacy, _ast = oracle._load_turnout_namespace(path)
        frozen.append(legacy)
    dimensions = module.rea_c10_dimensions()
    for host_length in (0.0, 100.0, 1542.475839):
        for orientation in (
            module.TURNOUT_ORIENTATION_FACING,
            module.TURNOUT_ORIENTATION_TRAILING,
        ):
            results = [
                legacy["turnout_valid_toe_range"](
                    host_length, dimensions, orientation,
                )
                for legacy in frozen
            ]
            actual = namespace["turnout_valid_toe_range"](
                host_length, dimensions, orientation,
            )
            assert results[0] == results[1] == actual
            assert type(actual) is tuple and len(actual) == 2
    for toe_chainage in (0.0, 746.298, 1542.475839):
        for orientation in (
            module.TURNOUT_ORIENTATION_FACING,
            module.TURNOUT_ORIENTATION_TRAILING,
        ):
            results = [
                legacy["turnout_host_station_interval"](
                    toe_chainage, dimensions, orientation,
                )
                for legacy in frozen
            ]
            actual = namespace["turnout_host_station_interval"](
                toe_chainage, dimensions, orientation,
            )
            assert results[0] == results[1] == actual
            assert type(actual) is tuple and len(actual) == 2
    old_config = {
        "toe_chainage": 746.298,
        "handing": module.TURNOUT_HAND_LEFT,
        "orientation": module.TURNOUT_ORIENTATION_FACING,
        "track_gauge": 16.5,
        "flangeway": 1.0,
        "timber_outlines": True,
        "timber_centres": False,
        "timber_numbers": True,
        "timber_length_labels": False,
        "construction_marks": True,
        "rail_geometry_revision": module.TURNOUT_RAIL_GEOMETRY_REVISION,
        "timber_geometry_revision": module.TURNOUT_TIMBER_GEOMETRY_REVISION,
    }
    for new_config in (
        dict(old_config),
        {**old_config, "handing": module.TURNOUT_HAND_RIGHT},
        {**old_config, "toe_chainage": 746.298000002},
        {**old_config, "timber_outlines": False},
        {**old_config, "rail_geometry_revision": 0},
    ):
        results = [
            legacy["turnout_configuration_change_summary"](
                old_config, new_config,
            )
            for legacy in frozen
        ]
        actual = summary(old_config, new_config)
        assert results[0] == results[1] == actual
        assert type(actual) is list
    assert session.routing_record() == record
    assert document_state() == before

    output = os.environ.get("TRACKTEMPLATE_TURNOUT_QUALIFIED_OUTPUT")
    if output:
        result = {
            "status": "PASS",
            "profile_id": foundation["matched_profile_id"],
            "route": record,
            "five_callers": list(CALLERS),
            "interval_callers": list(INTERVAL_CALLERS),
            "summary_callers": list(SUMMARY_CALLERS),
            "document_state_unchanged": True,
            "source_sha256": {
                name: hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest()
                for name in (
                    "TrackTemplate.FCMacro",
                    "tracktemplate/domain/turnout.py",
                    "tracktemplate/application/turnout_edit.py",
                    "tracktemplate/compatibility/transition_workflow.py",
                )
            },
        }
        with pathlib.Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(SENTINEL)


if __name__ == "__main__":
    validate()
