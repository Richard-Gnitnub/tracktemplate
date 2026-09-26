#!/usr/bin/env python3
"""Compare native connected-straight inputs and the actual B16 binding."""

import hashlib
import json
import os
import pathlib
import runpy
import sys
from unittest import mock

import FreeCAD as App


ROOT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_CONNECTED_STRAIGHT_SOURCE_ROOT",
    pathlib.Path(__file__).resolve().parents[1],
)).resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow as workflow  # noqa: E402
import validate_phase7_connected_straight_validation as proof  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 7 connected-straight FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
VECTOR = App.Vector


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
    raise AssertionError("A mixed or incomplete route was accepted")


def validate():
    baseline_only = (
        "--baseline-only" in sys.argv
        or os.environ.get("TRACKTEMPLATE_CONNECTED_STRAIGHT_BASELINE_ONLY") == "1"
    )
    before = document_state()
    for module, relative in (
        (api, "tracktemplate/api.py"),
        (workflow, "tracktemplate/compatibility/transition_workflow.py"),
    ):
        assert pathlib.Path(module.__file__).resolve() == ROOT / relative
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    )

    def load_host():
        return b15_workflow_host.load_b15_workflow_host(ROOT, contract)

    host = load_host()
    original_gate = getattr(host.module, proof.NAME)
    runner = host.module.run_macro
    assert runner.__globals__ is host.module.__dict__
    assert runner.__globals__[proof.NAME] is original_gate
    assert proof.NAME in runner.__code__.co_names
    proof.legacy_namespaces(ROOT)  # Frozen B14/B15 definition identity only.
    native_records = []
    def point_factory(x, y):
        return VECTOR(x, y, 0.0)

    for case in proof.cases():
        arguments = proof.inputs(case, point_factory)
        # The fixture contains real host vectors before the allocation guard.
        for curve in arguments[1]:
            if curve["points"] is not None:
                assert all(type(point) is VECTOR for point in curve["points"])
        with mock.patch.object(
            App, "Vector", side_effect=AssertionError("native allocation"),
        ):
            observation = proof.observe(original_gate, arguments)
        proof.assert_expected(case, observation)
        native_records.append({"case": case[0], "result": observation})
        assert document_state() == before

    record = None
    if not baseline_only:
        functions = {name: getattr(api, name)
                     for name in workflow.PRODUCT_FUNCTION_NAMES}
        assert proof.NAME in functions and len(functions) == 19
        # Exercise full restoration after a failure during staged selection.
        rollback = load_host()
        previous = dict(rollback.module.__dict__)
        with mock.patch.object(
            workflow.ModularTransitionWorkflowSession, "_validate_binding",
            side_effect=RuntimeError("controlled connected-straight failure"),
        ):
            try:
                workflow.ModularTransitionWorkflowSession(rollback, functions)
            except RuntimeError as error:
                assert str(error) == "controlled connected-straight failure"
            else:
                raise AssertionError("The controlled binding failure was lost")
        assert_namespace(rollback.module.__dict__, previous)
        assert document_state() == before

        for dependency in ("_dot_xy", "_straight_heading_delta"):
            invalid = dict(functions)
            invalid[proof.NAME] = core_proof.detached(
                functions[proof.NAME], dependency, lambda *args: 0.0,
            )
            fresh = load_host()
            previous = dict(fresh.module.__dict__)
            expect_route_error(lambda: workflow.ModularTransitionWorkflowSession(
                fresh, invalid,
            ))
            assert_namespace(fresh.module.__dict__, previous)

        detached_host = load_host()
        detached_host.module.run_macro = core_proof.detached(
            detached_host.module.run_macro, proof.NAME, functions[proof.NAME],
        )
        previous = dict(detached_host.module.__dict__)
        expect_route_error(lambda: workflow.ModularTransitionWorkflowSession(
            detached_host, functions,
        ))
        assert_namespace(detached_host.module.__dict__, previous)

        session = workflow.ModularTransitionWorkflowSession(host, functions)
        record = session.routing_record()
        assert record["schema_version"] == 12
        assert record["contract_id"] == (
            "tracktemplate:phase7:connected-straight-validation:1"
        )
        assert record["function_names"] == list(functions)
        callers = list(dict.fromkeys(name for name, _ in workflow.PRODUCT_CALLER_ROUTES))
        assert record["caller_names"] == callers
        assert record["mixed_route"] is False
        adapter = getattr(host.module, proof.NAME)
        assert type(adapter) is workflow._ConnectedStraightRoutesValidationAdapter
        assert adapter.calculation is functions[proof.NAME]
        assert host.module.run_macro is runner
        assert runner.__globals__[proof.NAME] is adapter
        assert host.module.App is App
        for case, expected in zip(proof.cases(), native_records):
            arguments = proof.inputs(case, point_factory)
            with mock.patch.object(
                App, "Vector", side_effect=AssertionError("native allocation"),
            ):
                assert proof.observe(adapter, arguments) == expected["result"]
            assert document_state() == before
        setattr(host.module, proof.NAME, original_gate)
        try:
            expect_route_error(session.routing_record)
        finally:
            setattr(host.module, proof.NAME, adapter)
        assert session.routing_record() == record

    assert document_state() == before
    result = {
        "status": "PASS", "baseline_only": baseline_only,
        "qualified_profile": foundation["matched_profile_id"],
        "definition_sha256": proof.DEFINITION_SHA256,
        "source_root": str(ROOT), "routing": record,
        "case_count": len(native_records), "observations": native_records,
        "document_state_unchanged": True,
        "native_vector_constructor_guard": "PASS",
        "caller_order": proof.caller_order(ROOT),
        "caller_binding_checked": True,
        "run_macro_executed": False,
        "source_sha256": {
            relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in (
                "TrackTemplate.FCMacro", "tracktemplate/api.py",
                "tracktemplate/domain/alignment.py",
                "tracktemplate/compatibility/transition_workflow.py",
            )
        },
    }
    destination = os.environ.get("TRACKTEMPLATE_CONNECTED_STRAIGHT_OUTPUT")
    if destination:
        with pathlib.Path(destination).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase7_connected_straight_validation"}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - retain the qualified-host traceback
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
