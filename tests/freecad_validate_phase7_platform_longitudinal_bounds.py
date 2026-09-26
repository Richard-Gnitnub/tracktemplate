#!/usr/bin/env python3
"""Prove native platform longitudinal bounds and selected B16 routing."""

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
    "TRACKTEMPLATE_PLATFORM_BOUNDS_SOURCE_ROOT", TEST_ROOT,
)).resolve()
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(TEST_ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    transition_workflow as workflow,
)
import validate_phase7_platform_input_validation as input_proof  # noqa: E402
import validate_phase7_platform_longitudinal_bounds as proof  # noqa: E402


SENTINEL = "Phase 7 platform longitudinal bounds FreeCAD validation passed"
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


def assert_namespace(namespace, previous):
    assert tuple(namespace) == tuple(previous)
    assert all(namespace[name] is value for name, value in previous.items())


def route_error(action):
    try:
        action()
    except workflow.TransitionWorkflowError:
        return
    raise AssertionError("An incomplete or mixed platform-bounds route passed")


def caller_rejection(caller, config, alignments):
    before = proof.snapshot(config)
    try:
        caller(config, alignments, 1.0)
    except ValueError as error:
        record = {"exception": "ValueError", "message": str(error)}
    else:
        raise AssertionError("The platform caller missed bounds rejection")
    assert proof.snapshot(config) == before
    return record


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
        centre_offset=1.0e6,
        platform_length=100.0,
    )
    return config, [alignment]


def validate():
    baseline_only = (
        "--baseline-only" in sys.argv
        or os.environ.get("TRACKTEMPLATE_PLATFORM_BOUNDS_BASELINE_ONLY") == "1"
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
    for label, config, start, finish in proof.cases():
        expected = proof.observe(b14_calculation, config, start, finish)
        with mock.patch.object(
            App, "Vector", side_effect=AssertionError("native allocation"),
        ):
            observed = proof.observe(
                native_calculation, config, start, finish,
            )
        assert observed == expected, label
        native_records.append({"case": label, "result": observed})
        assert document_state() == before

    read_records = []
    for label in (
        "midpoint", "available-zero", "length-zero",
        "centre-outside-right-tolerance", "requested-too-long",
    ):
        expected = proof.read_observation(b14_calculation, label)
        assert proof.read_observation(native_calculation, label) == expected
        for position in range(1, len(expected[1]) + 1):
            assert proof.read_observation(
                native_calculation, label, position,
            ) == proof.read_observation(b14_calculation, label, position)
        read_records.append({"case": label, "result": expected[0],
                             "events": expected[1]})

    caller_config, caller_alignments = caller_case(host.module)
    native_error = caller_rejection(native_caller, caller_config,
                                    caller_alignments)
    assert "centre offset" in native_error["message"].lower()
    assert document_state() == before

    route = None
    if not baseline_only:
        functions = {name: getattr(api, name)
                     for name in workflow.PRODUCT_FUNCTION_NAMES}
        assert proof.NAME in functions and len(functions) == 24
        assert functions[proof.NAME] is (
            api.resolve_platform_longitudinal_bounds
        )

        rollback_host = load_host()
        previous = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            workflow.ModularTransitionWorkflowSession, "_validate_binding",
            side_effect=RuntimeError("controlled platform-bounds failure"),
        ):
            try:
                workflow.ModularTransitionWorkflowSession(
                    rollback_host, functions,
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-bounds failure"
            else:
                raise AssertionError("The controlled binding failure was lost")
        assert_namespace(rollback_host.module.__dict__, previous)
        assert document_state() == before

        incomplete = dict(functions)
        incomplete.pop(proof.NAME)
        rejected_host = load_host()
        previous = dict(rejected_host.module.__dict__)
        route_error(lambda: workflow.ModularTransitionWorkflowSession(
            rejected_host, incomplete,
        ))
        assert_namespace(rejected_host.module.__dict__, previous)

        session = workflow.ModularTransitionWorkflowSession(host, functions)
        route = session.routing_record()
        assert route["schema_version"] == 15
        assert route["contract_id"] == (
            "tracktemplate:phase7:platform-heading-coverage:1"
        )
        assert route["function_names"] == list(functions)
        assert len(route["caller_names"]) == 40
        assert route["mixed_route"] is False
        selected = namespace[proof.NAME]
        assert selected is functions[proof.NAME]
        assert namespace["calculate_platform_boundaries"] is native_caller
        assert native_caller.__globals__[proof.NAME] is selected

        for (label, config, start, finish), expected in zip(
            proof.cases(), native_records,
        ):
            assert label == expected["case"]
            with mock.patch.object(
                App, "Vector", side_effect=AssertionError("native allocation"),
            ):
                assert proof.observe(selected, config, start, finish) == (
                    expected["result"]
                ), label
            assert document_state() == before
        for item in read_records:
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
            selected_error = caller_rejection(native_caller, caller_config,
                                              caller_alignments)
        finally:
            namespace[proof.NAME] = selected
        assert selected_error == native_error
        assert len(calls) == 1
        assert calls[0][0] is caller_config
        assert all(isinstance(value, float) for value in calls[0][1:])
        assert session.routing_record() == route
        namespace[proof.NAME] = native_calculation
        try:
            route_error(session.routing_record)
        finally:
            namespace[proof.NAME] = selected
        assert session.routing_record() == route

    assert document_state() == before
    result = {
        "status": "PASS", "baseline_only": baseline_only,
        "qualified_profile": foundation["matched_profile_id"],
        "definition_sha256": proof.DEFINITION_SHA256,
        "source_root": str(SOURCE_ROOT), "routing": route,
        "case_count": len(native_records), "observations": native_records,
        "read_traces": read_records,
        "native_caller_rejection": native_error,
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
    destination = os.environ.get("TRACKTEMPLATE_PLATFORM_BOUNDS_OUTPUT")
    if destination:
        with pathlib.Path(destination).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    print(SENTINEL)


if __name__ in {
    "__main__", "freecad_validate_phase7_platform_longitudinal_bounds",
}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - retain qualified-host traceback
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
