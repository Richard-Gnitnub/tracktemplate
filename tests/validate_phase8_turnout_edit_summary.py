#!/usr/bin/env python3
"""Compare inherited turnout edit decisions and their three host routes."""

import ast
import hashlib
import json
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.application import turnout_edit  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow,
)
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 8 turnout edit-summary decision and routing validation passed"
BINDING = "turnout_configuration_change_summary"
CALLERS = (
    "edit_curve_inheriting_c10_turnout",
    "TurnoutManagerDialog.update_host_summary",
    "TurnoutManagerDialog.apply_turnout_edit",
)
REVISION_NAMES = (
    "TURNOUT_RAIL_GEOMETRY_REVISION",
    "TURNOUT_TIMBER_GEOMETRY_REVISION",
)


def _frozen_oracles():
    contract = json.loads((
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    ).read_text(encoding="utf-8"))
    assert contract["contract_id"] == "tracktemplate:phase1:transition-pilot:1"
    results = []
    definitions = []
    constants = []
    for key in ("b14", "b15"):
        identity = contract["source_state"][key]
        path = ROOT / identity["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            identity["sha256"]
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        selected = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == BINDING
        ]
        assert len(selected) == 1
        revisions = {
            target.id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
            and target.id in REVISION_NAMES
        }
        assert set(revisions) == set(REVISION_NAMES)
        namespace = dict(revisions)
        exec(compile(ast.Module(
            body=selected, type_ignores=[],
        ), str(path), "exec"), namespace)
        results.append(namespace[BINDING])
        definitions.append(ast.dump(selected[0], include_attributes=False))
        constants.append(revisions)
        for caller_name in CALLERS:
            function_name = caller_name.split(".")[-1]
            matches = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
                and node.name == function_name
                and any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == BINDING
                    for child in ast.walk(node)
                )
            ]
            assert len(matches) == 1, caller_name
    assert definitions[0] == definitions[1]
    assert constants[0] == constants[1]
    return results, constants[0]


def _observed(function, old_config, new_config):
    try:
        result = function(old_config, new_config)
    except Exception as error:  # noqa: BLE001 - inherited error parity
        return "error", type(error).__name__, str(error)
    assert type(result) is list
    assert all(type(item) is str for item in result)
    return "value", result


def _application_call(revisions):
    return lambda old, new: turnout_edit.turnout_configuration_change_summary(
        old, new,
        lambda: revisions[REVISION_NAMES[0]],
        lambda: revisions[REVISION_NAMES[1]],
    )


def _baseline(revisions):
    return {
        "toe_chainage": 746.298,
        "handing": "Left-hand",
        "orientation": "Facing with host travel direction",
        "track_gauge": 16.5,
        "flangeway": 1.0,
        "timber_outlines": True,
        "timber_centres": False,
        "timber_numbers": True,
        "timber_length_labels": False,
        "construction_marks": True,
        "rail_geometry_revision": revisions[REVISION_NAMES[0]],
        "timber_geometry_revision": revisions[REVISION_NAMES[1]],
    }


def validate_decision():
    (b14, b15), revisions = _frozen_oracles()
    assert turnout_edit.__all__ == ()
    assert BINDING not in api.__all__
    assert not hasattr(api, BINDING)
    selected = _application_call(revisions)
    old = _baseline(revisions)
    assert selected(old, dict(old)) == []

    changed = dict(old)
    changed["handing"] = "Right-hand"
    assert selected(old, changed) == [
        "Handing: Left-hand -> Right-hand"
    ]
    changed = dict(old)
    changed["toe_chainage"] += 0.0000000005
    assert selected(old, changed) == []
    changed["toe_chainage"] += 0.000000002
    assert selected(old, changed) == [
        "Switch-toe chainage: 746.298 mm -> 746.298 mm"
    ]

    changed = dict(old)
    changed.update({
        "handing": "Right-hand",
        "orientation": "Trailing against host travel direction",
        "track_gauge": 18.2,
        "flangeway": 1.2,
        "timber_outlines": False,
        "timber_centres": True,
        "timber_numbers": False,
        "timber_length_labels": True,
        "construction_marks": False,
        "rail_geometry_revision": 0,
        "timber_geometry_revision": 0,
    })
    cases = [
        (old, dict(old)),
        (old, changed),
        (old, {**old, "toe_chainage": 746.2980000005}),
        (old, {**old, "toe_chainage": 746.298000002}),
        (old, {**old, "track_gauge": 16.500000002}),
        (old, {**old, "flangeway": 1.000000002}),
        (old, {**old, "timber_outlines": None}),
        (old, {**old, "rail_geometry_revision": "bad"}),
        (old, {**old, "timber_geometry_revision": "bad"}),
        (old, {**old, "toe_chainage": "bad"}),
        ({**old, "toe_chainage": None}, old),
        ({**old, "rail_geometry_revision": "bad"}, old),
        ({**old, "timber_geometry_revision": "bad"}, old),
        ({}, {}),
        (None, None),
    ]
    for old_config, new_config in cases:
        results = [
            _observed(function, old_config, new_config)
            for function in (b14, b15, selected)
        ]
        assert results[0] == results[1] == results[2], (
            old_config, new_config, results,
        )

    events = []

    class TracedConfig(dict):
        def get(self, key, *default):
            events.append("get:" + key)
            return super().get(key, *default)

    old_config = TracedConfig(old)
    new_config = TracedConfig(old)
    del new_config["rail_geometry_revision"]
    del new_config["timber_geometry_revision"]
    result = turnout_edit.turnout_configuration_change_summary(
        old_config, new_config,
        lambda: (events.append("rail-fallback"), revisions[REVISION_NAMES[0]])[1],
        lambda: (events.append("timber-fallback"), revisions[REVISION_NAMES[1]])[1],
    )
    assert result == []
    assert events[-6:] == [
        "get:rail_geometry_revision", "get:rail_geometry_revision",
        "rail-fallback", "get:timber_geometry_revision",
        "get:timber_geometry_revision", "timber-fallback",
    ]


_SYNTHETIC_ROUTE = """
def turnout_configuration_change_summary(*arguments):
    return ["inherited"]
def edit_curve_inheriting_c10_turnout(*arguments):
    return turnout_configuration_change_summary(*arguments)
class TurnoutManagerDialog:
    def update_host_summary(self, *arguments):
        return turnout_configuration_change_summary(*arguments)
    def apply_turnout_edit(self, *arguments):
        return turnout_configuration_change_summary(*arguments)
"""


def _host(root, contract, revisions):
    host = b15_workflow_host.load_b15_workflow_host(root, contract)
    host.module.__dict__.update(revisions)
    exec(_SYNTHETIC_ROUTE, host.module.__dict__)
    return host


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def _expect_route_error(action):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        assert "turnout edit-summary" in str(error), str(error)
        return
    raise AssertionError("A mixed turnout edit-summary route was accepted")


def validate_binding():
    _oracles, revisions = _frozen_oracles()
    with tempfile.TemporaryDirectory(prefix="tracktemplate-phase8-edit-summary-") as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        absent = b15_workflow_host.load_b15_workflow_host(root, contract)
        assert BINDING not in absent.module.__dict__
        absent_session = transition_workflow.ModularTransitionWorkflowSession(
            absent, _functions(),
        )
        absent_record = absent_session.routing_record()
        assert BINDING not in absent.module.__dict__
        assert absent_record["schema_version"] == 16
        assert len(absent_record["function_names"]) == 25
        assert len(absent_record["caller_names"]) == 40

        host = _host(root, contract, revisions)
        namespace = host.module.__dict__
        inherited = namespace[BINDING]
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, _functions(),
        )
        record = session.routing_record()
        assert record == absent_record
        adapter = namespace[BINDING]
        assert type(adapter) is (
            transition_workflow._TurnoutConfigurationSummaryAdapter
        )
        assert adapter is not inherited
        assert adapter.calculation is (
            turnout_edit.turnout_configuration_change_summary
        )
        assert adapter.host_globals is namespace
        old = _baseline(revisions)
        new = {**old, "handing": "Right-hand"}
        expected = ["Handing: Left-hand -> Right-hand"]
        assert adapter(old, new) == expected
        for name in CALLERS:
            if "." in name:
                class_name, method_name = name.split(".", 1)
                function = getattr(namespace[class_name], method_name)
                actual = function(None, old, new)
            else:
                function = namespace[name]
                actual = function(old, new)
            assert function.__globals__ is namespace
            assert BINDING in function.__code__.co_names
            assert function.__globals__[BINDING] is adapter
            assert actual == expected, name

        for name in CALLERS:
            if "." in name:
                class_name, method_name = name.split(".", 1)
                owner = namespace[class_name]
                original = getattr(owner, method_name)
                setattr(owner, method_name, lambda self, *_args: None)
                try:
                    _expect_route_error(session.routing_record)
                finally:
                    setattr(owner, method_name, original)
            else:
                original = namespace[name]
                namespace[name] = lambda *_args: None
                try:
                    _expect_route_error(session.routing_record)
                finally:
                    namespace[name] = original
            assert session.routing_record() == record

        namespace[BINDING] = inherited
        _expect_route_error(session.routing_record)
        assert session.launch_workflow()
        assert host.module.LAUNCH_COUNT == 1
        assert namespace[BINDING] is adapter
        assert session.routing_record() == record

        original_selected = turnout_edit.turnout_configuration_change_summary
        turnout_edit.turnout_configuration_change_summary = lambda *_args: []
        try:
            _expect_route_error(session.routing_record)
        finally:
            turnout_edit.turnout_configuration_change_summary = original_selected
        assert session.routing_record() == record

        for constant_name in REVISION_NAMES:
            value = namespace.pop(constant_name)
            try:
                _expect_route_error(session.routing_record)
            finally:
                namespace[constant_name] = value
            assert session.routing_record() == record

        rollback = _host(root, contract, revisions)
        rollback_namespace = rollback.module.__dict__
        rollback_namespace["edit_curve_inheriting_c10_turnout"] = lambda: None
        original = {
            name: rollback_namespace.get(name)
            for name in (*transition_workflow.PRODUCT_FUNCTION_NAMES, BINDING)
        }
        _expect_route_error(lambda: (
            transition_workflow.ModularTransitionWorkflowSession(
                rollback, _functions(),
            )
        ))
        assert all(
            rollback_namespace.get(name) is value
            for name, value in original.items()
        )
        assert rollback.module.LAUNCH_COUNT == 0


def validate():
    validate_decision()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
