#!/usr/bin/env python3
"""Compare the native B15 platform-input gate with the selected B16 route."""

import hashlib
import json
import os
import pathlib
import runpy
import sys
from unittest import mock

import FreeCAD as App


TEST_ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_PLATFORM_INPUT_SOURCE_ROOT", TEST_ROOT,
)).resolve()
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(TEST_ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow as workflow  # noqa: E402
import validate_phase7_platform_input_validation as proof  # noqa: E402


SENTINEL = "Phase 7 platform input FreeCAD validation passed"
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


def expect_route_error(action):
    try:
        action()
    except workflow.TransitionWorkflowError:
        return
    raise AssertionError("A mixed or incomplete platform-input route passed")


def validate():
    baseline_only = (
        "--baseline-only" in sys.argv
        or os.environ.get("TRACKTEMPLATE_PLATFORM_INPUT_BASELINE_ONLY") == "1"
    )
    before = document_state()
    for module, relative in (
        (api, "tracktemplate/api.py"),
        (workflow, "tracktemplate/compatibility/transition_workflow.py"),
    ):
        assert pathlib.Path(module.__file__).resolve() == SOURCE_ROOT / relative
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
    original_gate = namespace[proof.NAME]
    original_caller = namespace["calculate_platform_boundaries"]
    assert original_caller.__globals__ is namespace
    assert original_caller.__globals__[proof.NAME] is original_gate
    assert proof.NAME in original_caller.__code__.co_names
    legacy_gate = proof.legacy_functions()[0]  # B14/B15 identity.

    native_records = []
    for label, config, alignments in proof.cases():
        expected = proof.observe(legacy_gate, config, alignments)
        with mock.patch.object(
            App, "Vector", side_effect=AssertionError("native allocation"),
        ):
            observed = proof.observe(
                original_gate, config, alignments,
            )
        assert observed == expected, label
        native_records.append({"case": label, "result": observed})
        assert document_state() == before

    read_records = []
    for label in ("disabled-bypass", "outside", "between",
                  "required-clearance-b", "name-before-count"):
        expected = proof.read_observation(legacy_gate, label)
        assert proof.read_observation(original_gate, label) == expected
        for position in range(1, len(expected[1]) + 1):
            assert proof.read_observation(original_gate, label, position) == (
                proof.read_observation(legacy_gate, label, position)
            )
        read_records.append({"case": label, "reads": len(expected[1]),
                             "result": expected[0], "events": expected[1]})

    record = None
    if not baseline_only:
        functions = {name: getattr(api, name)
                     for name in workflow.PRODUCT_FUNCTION_NAMES}
        assert proof.NAME in functions and len(functions) == 24
        assert functions[proof.NAME] is api.validate_platform_inputs

        rollback_host = load_host()
        previous = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            workflow.ModularTransitionWorkflowSession, "_validate_binding",
            side_effect=RuntimeError("controlled platform-input failure"),
        ):
            try:
                workflow.ModularTransitionWorkflowSession(
                    rollback_host, functions,
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-input failure"
            else:
                raise AssertionError("The controlled binding failure was lost")
        assert_namespace(rollback_host.module.__dict__, previous)
        assert document_state() == before

        incomplete = dict(functions)
        incomplete.pop(proof.NAME)
        rejected_host = load_host()
        previous = dict(rejected_host.module.__dict__)
        expect_route_error(lambda: workflow.ModularTransitionWorkflowSession(
            rejected_host, incomplete,
        ))
        assert_namespace(rejected_host.module.__dict__, previous)

        session = workflow.ModularTransitionWorkflowSession(host, functions)
        record = session.routing_record()
        assert record["schema_version"] == 15
        assert record["contract_id"] == (
            "tracktemplate:phase7:platform-heading-coverage:1"
        )
        assert record["function_names"] == list(functions)
        assert len(record["caller_names"]) == 40
        assert record["mixed_route"] is False
        selected_gate = namespace[proof.NAME]
        assert selected_gate is functions[proof.NAME]
        assert host.module.calculate_platform_boundaries is original_caller
        assert original_caller.__globals__[proof.NAME] is selected_gate
        assert host.module.App is App

        for (label, config, alignments), expected in zip(
            proof.cases(), native_records,
        ):
            assert label == expected["case"]
            with mock.patch.object(
                App, "Vector", side_effect=AssertionError("native allocation"),
            ):
                assert proof.observe(selected_gate, config, alignments) == (
                    expected["result"]
                ), label
            assert document_state() == before
        for item in read_records:
            label = item["case"]
            assert proof.read_observation(selected_gate, label) == (
                item["result"], item["events"],
            )
            for position in range(1, item["reads"] + 1):
                assert proof.read_observation(
                    selected_gate, label, position,
                ) == proof.read_observation(original_gate, label, position)

        invalid = next(item for item in proof.cases()
                       if item[0] == "name-blank")
        expected_error = next(item["result"][1] for item in native_records
                              if item["case"] == "name-blank")
        try:
            original_caller(invalid[1], invalid[2], 1.0)
        except ValueError as error:
            assert str(error) == expected_error
        else:
            raise AssertionError("The selected host caller missed the gate")
        namespace[proof.NAME] = original_gate
        try:
            expect_route_error(session.routing_record)
        finally:
            namespace[proof.NAME] = selected_gate
        assert session.routing_record() == record

    assert document_state() == before
    result = {
        "status": "PASS", "baseline_only": baseline_only,
        "qualified_profile": foundation["matched_profile_id"],
        "definition_sha256": proof.DEFINITION_SHA256,
        "source_root": str(SOURCE_ROOT), "routing": record,
        "case_count": len(native_records), "observations": native_records,
        "read_traces": read_records,
        "document_state_unchanged": True,
        "native_vector_constructor_guard": "PASS",
        "caller_binding_checked": True,
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
    destination = os.environ.get("TRACKTEMPLATE_PLATFORM_INPUT_OUTPUT")
    if destination:
        with pathlib.Path(destination).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase7_platform_input_validation"}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - retain the qualified-host traceback
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
