#!/usr/bin/env python3
"""Prove native platform top heights and the selected B16 caller route."""

import hashlib
import json
import math
import os
import pathlib
import runpy
import sys
from unittest import mock

import FreeCAD as App


TEST_ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_PLATFORM_HEIGHTS_SOURCE_ROOT", TEST_ROOT,
)).resolve()
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(TEST_ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    transition_workflow as workflow,
)
import validate_phase7_platform_input_validation as input_proof  # noqa: E402
import validate_phase7_platform_top_heights as proof  # noqa: E402


SENTINEL = "Phase 7 platform top heights FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"


def document_state():
    return {
        "active": getattr(App.ActiveDocument, "Name", None),
        "documents": {
            name: {
                "label": document.Label,
                "file": document.FileName,
                "objects": tuple((obj.Name, obj.TypeId, tuple(obj.State))
                                 for obj in document.Objects),
                "undo": document.UndoCount,
                "redo": document.RedoCount,
            }
            for name, document in sorted(App.listDocuments().items())
        },
    }


def caller_case(module):
    centre = module.main_circle_centre(600.0, 600.0)
    alignment = module.build_concentric_core(
        centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track",
    )
    alignment.update(name="Main Track", width=32.0,
                     create_template=True, show_centreline=True)
    config, _unused = input_proof.base_inputs()
    config.update(
        coverage=module.PLATFORM_CORE,
        centre_offset=0.0,
        outside_side=module.PLATFORM_LEFT,
        body_output=module.PLATFORM_SOLID,
        platform_height=15.0,
        entry_end_style=module.PLATFORM_END_TAPERED,
        entry_taper_length=10.0,
        exit_end_style=module.PLATFORM_END_TAPERED,
        exit_taper_length=10.0,
    )
    return config, [alignment]


def caller_observation(caller, config, alignments):
    before = proof.snapshot((config, alignments))
    try:
        result = caller(config, alignments, 1.0)
    except Exception as error:  # noqa: BLE001 - preserve host failure
        record = {"exception": type(error).__name__, "message": str(error)}
    else:
        record = {"value": proof.snapshot(result)}
    assert proof.snapshot((config, alignments)) == before
    return record


def route_error(action):
    try:
        action()
    except workflow.TransitionWorkflowError:
        return
    raise AssertionError("An incomplete or mixed platform-height route passed")


def validate():
    baseline_only = (
        "--baseline-only" in sys.argv
        or os.environ.get("TRACKTEMPLATE_PLATFORM_HEIGHTS_BASELINE_ONLY") == "1"
    )
    before = document_state()
    for module, relative in (
        (api, "tracktemplate/api.py"),
        (workflow, "tracktemplate/compatibility/transition_workflow.py"),
    ):
        assert pathlib.Path(module.__file__).resolve() == (
            SOURCE_ROOT / relative
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

    def load_host():
        return b15_workflow_host.load_b15_workflow_host(
            SOURCE_ROOT, contract,
        )

    host = load_host()
    namespace = host.module.__dict__
    native_calculation = namespace[proof.NAME]
    native_caller = namespace["calculate_platform_boundaries"]
    assert native_caller.__globals__ is namespace
    assert native_caller.__globals__[proof.NAME] is native_calculation
    assert proof.NAME in native_caller.__code__.co_names
    b14_calculation = proof.legacy_functions()[0]

    native_records = []
    for label, config, stations, platform_length in proof.cases():
        expected = proof.observe(
            b14_calculation, config, stations, platform_length,
        )
        with mock.patch.object(
            App, "Vector", side_effect=AssertionError("native allocation"),
        ):
            observed = proof.observe(
                native_calculation, config, stations, platform_length,
            )
        assert observed == expected, label
        native_records.append({"case": label, "result": observed})
        assert document_state() == before

    native_traces = []
    for label in ("non-solid", "solid-square", "entry", "exit", "both"):
        expected = proof.read_observation(b14_calculation, label)
        assert proof.read_observation(native_calculation, label) == expected
        for position in range(1, len(expected[1]) + 1):
            assert proof.read_observation(
                native_calculation, label, position,
            ) == proof.read_observation(
                b14_calculation, label, position,
            )
        native_traces.append({"case": label, "result": expected[0],
                              "events": expected[1]})

    caller_config, caller_alignments = caller_case(host.module)
    native_caller_result = caller_observation(
        native_caller, caller_config, caller_alignments,
    )
    assert "value" in native_caller_result
    assert document_state() == before

    route = None
    if not baseline_only:
        functions = {
            name: getattr(api, name)
            for name in workflow.PRODUCT_FUNCTION_NAMES
        }
        assert proof.NAME in functions and len(functions) == 25
        assert functions[proof.NAME] is api.calculate_platform_top_heights

        session = workflow.ModularTransitionWorkflowSession(host, functions)
        route = session.routing_record()
        assert route["schema_version"] == 16
        assert route["contract_id"] == (
            "tracktemplate:phase7:platform-top-heights:1"
        )
        assert route["function_names"] == list(functions)
        assert len(route["caller_names"]) == 40
        assert route["mixed_route"] is False
        selected = namespace[proof.NAME]
        assert selected is functions[proof.NAME]
        assert namespace["calculate_platform_boundaries"] is native_caller
        assert native_caller.__globals__[proof.NAME] is selected

        for (label, config, stations, platform_length), expected in zip(
            proof.cases(), native_records,
        ):
            assert label == expected["case"]
            with mock.patch.object(
                App, "Vector", side_effect=AssertionError("native allocation"),
            ):
                assert proof.observe(
                    selected, config, stations, platform_length,
                ) == expected["result"], label
            assert document_state() == before
        for item in native_traces:
            label = item["case"]
            assert proof.read_observation(selected, label) == (
                item["result"], item["events"],
            )
            for position in range(1, len(item["events"]) + 1):
                assert proof.read_observation(
                    selected, label, position,
                ) == proof.read_observation(
                    native_calculation, label, position,
                )

        calls = []

        def observed_calculation(*arguments):
            calls.append(arguments)
            return selected(*arguments)

        namespace[proof.NAME] = observed_calculation
        try:
            selected_caller_result = caller_observation(
                native_caller, caller_config, caller_alignments,
            )
        finally:
            namespace[proof.NAME] = selected
        assert selected_caller_result == native_caller_result
        assert len(calls) == 1
        assert calls[0][0] is caller_config
        assert isinstance(calls[0][1], list)
        assert isinstance(calls[0][2], float)
        assert document_state() == before

        namespace[proof.NAME] = native_calculation
        try:
            route_error(session.routing_record)
        finally:
            namespace[proof.NAME] = selected
        assert session.routing_record() == route

        incomplete = dict(functions)
        incomplete.pop(proof.NAME)
        rejected_host = load_host()
        route_error(lambda: workflow.ModularTransitionWorkflowSession(
            rejected_host, incomplete,
        ))

    assert document_state() == before
    result = {
        "status": "PASS", "baseline_only": baseline_only,
        "qualified_profile": foundation["matched_profile_id"],
        "definition_sha256": proof.DEFINITION_SHA256,
        "source_root": str(SOURCE_ROOT), "routing": route,
        "case_count": len(native_records), "observations": native_records,
        "read_traces": native_traces,
        "native_caller": native_caller_result,
        "document_state_unchanged": True,
        "native_vector_constructor_guard": "PASS",
        "caller_binding_checked": not baseline_only,
        "run_macro_executed": False,
        "source_sha256": {
            relative: hashlib.sha256((SOURCE_ROOT / relative).read_bytes())
                            .hexdigest()
            for relative in (
                "TrackTemplate.FCMacro", "tracktemplate/api.py",
                "tracktemplate/domain/alignment.py",
                "tracktemplate/compatibility/transition_workflow.py",
            )
        },
        "test_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes())
                               .hexdigest(),
    }
    destination = os.environ.get("TRACKTEMPLATE_PLATFORM_HEIGHTS_OUTPUT")
    if destination:
        with pathlib.Path(destination).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    print(SENTINEL)


if __name__ in {
    "__main__", "freecad_validate_phase7_platform_top_heights",
}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - retain qualified-host traceback
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
