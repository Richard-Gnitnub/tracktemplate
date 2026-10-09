#!/usr/bin/env python3
"""Exact-input regression and private B16 chair-cache binding checks."""

import ast
import copy
import hashlib
import json
import math
import pathlib
import re
import sys
import tempfile
import time
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow,
)
import validate_phase7_concentric_core as core_proof  # noqa: E402


BINDING = "_chair_geometry_signature"
CALLERS = (
    "_A8A7B11_ANALYSE_ENTITY_CHAIR_POSITIONS",
    "chair_analysis_effective_status",
    "_chair_generation_context",
)
B15_PATH = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
B15_SHA256 = "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
SENTINEL = "Chair analysis exact-input signature and binding validation passed"


def _legacy_signature():
    assert hashlib.sha256(B15_PATH.read_bytes()).hexdigest() == B15_SHA256
    tree = ast.parse(B15_PATH.read_text(encoding="utf-8"))
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == BINDING
    ]
    assert len(nodes) == 1
    namespace = {
        "hashlib": hashlib,
        "json": json,
        "CHAIR_ANALYSIS_SCHEMA_VERSION": 1,
        "normalise_chair_analysis_settings": copy.deepcopy,
    }
    exec(compile(ast.Module(
        body=nodes, type_ignores=[],
    ), str(B15_PATH), "exec"), namespace)
    return namespace[BINDING]


def _inputs():
    """Small neutral record fixture; no railway dimension authority."""
    return [
        "turnout",
        {
            "turnout_id": "TO-test", "template_set_id": "TS-test",
            "handing": "Left-hand",
        },
        {
            "schema_version": 1, "position_tolerance": 0.2,
            "cache_enabled": True,
        },
        [{
            "stable_identity": "rail-test", "name": "stock-test",
            "rail_role": "stock rail", "points": [[0.0, 0.0], [20.0, 0.0]],
            "parent_turnout_identity": "TO-test",
            "parent_crossover_identity": "XO-test", "turnout_side": "a",
            "supported_feature": "rail support",
            "source_configuration": {
                "gauge_face": "inside", "outer_face": "outside",
            },
        }],
        [{
            "stable_identity": "timber-test", "identifier": "S1",
            "prototype_reference": "S1", "centre": [10.0, 0.0],
            "angle_radians": 0.0, "angle_degrees": 0.0,
            "width": 3.0, "length": 30.0,
            "length_axis": [0.0, 1.0], "width_axis": [1.0, 0.0],
            "outline_polygon": [
                [8.5, -15.0], [11.5, -15.0], [11.5, 15.0], [8.5, 15.0],
            ],
            "collision_polygon": [
                [8.5, -15.0], [11.5, -15.0], [11.5, 15.0], [8.5, 15.0],
            ],
            "protected_features": ["switch toe"], "section": "switch",
            "source_configuration": {"crossing_suffix": "A"},
            "support_requirements": [{
                "route_kind": "a", "features": ["rail support"],
            }],
            "turnout_side": "a",
        }],
    ]


def _changed(value):
    if isinstance(value, str):
        return value + "-changed"
    if isinstance(value, float):
        return value + 0.0000000001
    if isinstance(value, list):
        return [_changed(value[0]), *copy.deepcopy(value[1:])]
    if isinstance(value, dict):
        result = copy.deepcopy(value)
        key = next(iter(result))
        result[key] = _changed(result[key])
        return result
    raise AssertionError(type(value))


def validate_signature(signature):
    baseline = _inputs()
    saved = copy.deepcopy(baseline)
    expected = signature(*baseline)
    assert len(expected) == 64
    assert signature(*copy.deepcopy(baseline)) == expected
    assert baseline == saved
    # Each listed field is consumed by the final B15 logical calculation or
    # emitted as identity/source metadata, including fallback geometry.
    for index in (1, 3, 4):
        record = baseline[index] if index == 1 else baseline[index][0]
        for field in record:
            changed = copy.deepcopy(baseline)
            target = changed[index] if index == 1 else changed[index][0]
            target[field] = _changed(target[field])
            assert signature(*changed) != expected, (index, field)
            assert signature(*baseline) == expected, (
                "change-back", index, field,
            )
    changed = copy.deepcopy(baseline)
    changed[0] = "crossover"
    assert signature(*changed) != expected
    changed = copy.deepcopy(baseline)
    changed[1].pop("turnout_id")
    changed[1]["crossover_id"] = "XO-test"
    crossover = signature(*changed)
    changed[1]["crossover_id"] = "XO-other"
    assert signature(*changed) != crossover
    for name in (
        "markers_visible", "protected_markers_visible", "footprints_visible",
        "physical_solids_visible", "unresolved_markers_visible",
        "cache_enabled",
    ):
        changed = copy.deepcopy(baseline)
        changed[2][name] = not changed[2].get(name, False)
        assert signature(*changed) == expected, name
    for name in (
        "position_tolerance", "maximum_unsupported_span",
        "rail_fit_clearance_per_side", "future_chair_embed_depth",
    ):
        changed = copy.deepcopy(baseline)
        changed[2][name] = 0.123456789
        assert signature(*changed) != expected, name
    changed = copy.deepcopy(baseline)
    changed[1].update({
        "chair_analysis_signature": expected,
        "chair_analysis_status": "Stored",
        "chair_analysis_settings": baseline[2],
        "chair_analysis_result": {"positions": []},
    })
    assert signature(*changed) == expected, "stored analysis feedback"
    for index in (3, 4):
        ordered = copy.deepcopy(baseline)
        second = copy.deepcopy(ordered[index][0])
        second["stable_identity"] += "-second"
        ordered[index].append(second)
        reversed_inputs = copy.deepcopy(ordered)
        reversed_inputs[index].reverse()
        assert signature(*ordered) != signature(*reversed_inputs)
        for field in baseline[index][0]:
            missing = copy.deepcopy(baseline)
            del missing[index][0][field]
            null = copy.deepcopy(missing)
            null[index][0][field] = None
            assert signature(*missing) != signature(*null), (index, field)
    for field in baseline[1]:
        missing = copy.deepcopy(baseline)
        del missing[1][field]
        null = copy.deepcopy(missing)
        null[1][field] = None
        assert signature(*missing) != signature(*null), field
    for value in (object(), float("nan"), float("inf"), float("-inf")):
        malformed = copy.deepcopy(baseline)
        malformed[3][0]["points"][0][0] = value
        try:
            signature(*malformed)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("Unsupported input received a cache key")
    assert baseline == saved


def _frozen_calculation():
    """Compile the final frozen pure closure, preserving historical aliases."""
    assert hashlib.sha256(B15_PATH.read_bytes()).hexdigest() == B15_SHA256
    tree = ast.parse(B15_PATH.read_text(encoding="utf-8"))
    functions, aliases, constants = {}, {}, {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in functions
                ):
                    functions[target.id] = functions[node.value.id]
                    aliases[target.id] = node
                elif target.id.isupper():
                    constants[target.id] = node
    pending = ["analyse_chair_position_records"]
    selected, nodes = set(), set()
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        node = functions.get(name, constants.get(name))
        assert node is not None, name
        nodes.add(node)
        if name in aliases:
            nodes.add(aliases[name])
        pending.extend(
            child.id for child in ast.walk(node)
            if isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
            and (child.id in functions or child.id in constants)
        )
    namespace = {
        "math": math, "re": re, "time": time,
        "hashlib": hashlib, "json": json,
    }
    exec(compile(ast.Module(
        body=sorted(nodes, key=lambda node: node.lineno), type_ignores=[],
    ), str(B15_PATH), "exec"), namespace)
    # Use the actual inherited cached caller and freshness guards, with only
    # document/extractor callbacks supplied by the in-memory test fixture.
    callers = []
    for name in (
        *CALLERS, "_A8A7B13_GENERATION_CONTEXT_WITHOUT_SETTINGS_CHECK",
    ):
        node = copy.deepcopy(functions[name])
        node.name = name
        callers.append(node)
    for name in (
        "CHAIR_STATUS_STALE", "CHAIR_STATUS_NOT_ANALYSED",
        "CHAIR_POSITION_MARKER_ROLE", "CHAIR_PROTECTED_MARKER_ROLE",
        "CHAIR_FOOTPRINT_MARKER_ROLE", "CHAIR_ANALYSIS_GROUP_ROLE",
    ):
        namespace[name] = ast.literal_eval(constants[name].value)
    exec(compile(ast.Module(
        body=callers, type_ignores=[],
    ), str(B15_PATH), "exec"), namespace)
    return namespace


def _deterministic(result):
    result = copy.deepcopy(result)
    for key in (
        "performance_timings_ms", "cache_reused", "display_cache_reused",
        "geometry_signature",
    ):
        result.pop(key, None)
    return result


def validate_live_cache(signature):
    namespace = _frozen_calculation()
    state = {"inputs": _inputs(), "cached": None, "transactions": []}
    state["inputs"][2].update({
        "markers_visible": False, "protected_markers_visible": False,
        "footprints_visible": False,
    })
    normalise = namespace["normalise_chair_analysis_settings"]
    namespace[BINDING] = lambda *args: signature(
        args[0], args[1], normalise(args[2]), args[3], args[4],
    )

    def write_metadata(_doc, _kind, config, result):
        state["cached"] = copy.deepcopy(result)
        config.update({
            "chair_analysis_status": result["status"],
            "chair_analysis_signature": result["geometry_signature"],
            "chair_analysis_settings": result["settings"],
        })
        return config

    namespace.update({
        "turnout_config_by_id": lambda *_: state["inputs"][1],
        "crossover_config_by_id": lambda *_: state["inputs"][1],
        "chair_rail_records_for_entity": lambda *_: state["inputs"][3],
        "chair_timber_records_for_entity": lambda *_: state["inputs"][4],
        "_chair_read_cached_result": lambda *_: state["cached"],
        "_chair_analysis_display_objects": lambda *_: [],
        "_chair_write_metadata": write_metadata,
        "_create_chair_analysis_display": lambda *_: None,
        "_document_recompute": lambda *_: None,
    })
    doc = types.SimpleNamespace(
        openTransaction=lambda name: state["transactions"].append(name),
        commitTransaction=lambda: state["transactions"].append("commit"),
        abortTransaction=lambda: state["transactions"].append("abort"),
    )
    caller = namespace[CALLERS[0]]
    calculation = namespace["analyse_chair_position_records"]

    def analyse():
        kind, config, settings, rails, timbers = state["inputs"]
        fresh = calculation(kind, config, rails, timbers, settings)
        result = caller(doc, kind, "test", settings)
        assert _deterministic(result) == _deterministic(fresh)
        return result

    baseline = copy.deepcopy(state["inputs"])
    first = analyse()
    assert first["cache_reused"] is False
    assert analyse()["cache_reused"] is True
    kind, config, settings, rails, timbers = state["inputs"]
    effective_status = namespace["chair_analysis_effective_status"]
    assert effective_status(doc, kind, config) == first["status"]
    saved = copy.deepcopy(state)
    old_key = _legacy_signature()(
        kind, config, normalise(settings), rails, timbers,
    )
    assert old_key != first["geometry_signature"]
    config["chair_analysis_signature"] = old_key
    state["cached"]["geometry_signature"] = old_key
    before_status = copy.deepcopy(state)
    assert effective_status(doc, kind, config) == namespace["CHAIR_STATUS_STALE"]
    try:
        namespace["_chair_generation_context"](doc, kind, "test", settings)
    except ValueError as error:
        assert "stale" in str(error).lower()
    else:
        raise AssertionError("Old analysis reached downstream preparation")
    assert state == before_status, "freshness query mutated document fixture"
    assert analyse()["cache_reused"] is False
    assert analyse()["cache_reused"] is True
    assert state["cached"]["geometry_signature"] == (
        saved["cached"]["geometry_signature"]
    )

    # These mutations all change a real final-B15 output, independently of
    # the hash. Their cached results must equal fresh inherited calculation.
    for index, field, replacement in (
        (1, "template_set_id", "TS-changed"),
        (1, "handing", "Right-hand"),
        (3, "name", "changed rail name"),
        (3, "source_configuration", {
            "gauge_face": "changed", "outer_face": "outside",
        }),
        (3, "points", [[0.0, 0.000004], [20.0, 0.000004]]),
        (4, "identifier", "S13"),
        (4, "width_axis", [0.999, 0.001]),
        (4, "length_axis", [0.001, 0.999]),
        (4, "angle_degrees", 0.0000000001),
    ):
        state["inputs"] = copy.deepcopy(baseline)
        analyse()
        assert analyse()["cache_reused"] is True
        target = (
            state["inputs"][index] if index == 1 else state["inputs"][index][0]
        )
        target[field] = replacement
        changed = analyse()
        assert changed["cache_reused"] is False, field
        assert _deterministic(changed) != _deterministic(first), field
        assert analyse()["cache_reused"] is True, field
        state["inputs"] = copy.deepcopy(baseline)
        reverted = analyse()
        assert reverted["cache_reused"] is False, field
        assert _deterministic(reverted) == _deterministic(first), field


_SYNTHETIC_ROUTES = """
CHAIR_ANALYSIS_SCHEMA_VERSION = 1
def normalise_chair_analysis_settings(settings):
    return dict(settings)
def _chair_geometry_signature(*args):
    return 'inherited'
def _A8A7B11_ANALYSE_ENTITY_CHAIR_POSITIONS(*args):
    return _chair_geometry_signature(*args)
def chair_analysis_effective_status(*args):
    return _chair_geometry_signature(*args)
def _A8A7B13_GENERATION_CONTEXT_WITHOUT_SETTINGS_CHECK(*args):
    return chair_analysis_effective_status(*args)
def _chair_generation_context(*args):
    _A8A7B13_GENERATION_CONTEXT_WITHOUT_SETTINGS_CHECK(*args)
    return _chair_geometry_signature(*args)
def _A8A7B15_ANALYSE_CHAIRS(*args):
    return _A8A7B11_ANALYSE_ENTITY_CHAIR_POSITIONS(*args)
def analyse_entity_chair_positions(*args):
    return _A8A7B15_ANALYSE_CHAIRS(*args)
"""


def _expect_route_error(action):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        assert "chair-analysis signature" in str(error), str(error)
        return
    raise AssertionError("Incomplete or mixed chair-signature route accepted")


def validate_binding():
    functions = {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-chair-signature-",
    ) as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)

        def host():
            result = b15_workflow_host.load_b15_workflow_host(root, contract)
            exec(_SYNTHETIC_ROUTES, result.module.__dict__)
            return result

        absent = b15_workflow_host.load_b15_workflow_host(root, contract)
        absent_record = transition_workflow.ModularTransitionWorkflowSession(
            absent, functions,
        ).routing_record()
        assert BINDING not in absent.module.__dict__
        selected = host()
        namespace = selected.module.__dict__
        inherited = namespace[BINDING]
        session = transition_workflow.ModularTransitionWorkflowSession(
            selected, functions,
        )
        assert session.routing_record() == absent_record
        adapter = namespace[BINDING]
        assert adapter is not inherited
        expected = adapter(*_inputs())
        for name in (*CALLERS, "analyse_entity_chair_positions"):
            assert namespace[name](*_inputs()) == expected, name
        for name in transition_workflow._CHAIR_SIGNATURE_SURFACE:
            value = namespace.pop(name)
            try:
                _expect_route_error(session.routing_record)
            finally:
                namespace[name] = value
            assert session.routing_record() == absent_record
        for name in (
            *CALLERS, "analyse_entity_chair_positions",
            "_A8A7B15_ANALYSE_CHAIRS",
            "_A8A7B13_GENERATION_CONTEXT_WITHOUT_SETTINGS_CHECK",
            "normalise_chair_analysis_settings",
        ):
            original = namespace[name]
            namespace[name] = types.FunctionType(
                original.__code__, dict(namespace), original.__name__,
                original.__defaults__, original.__closure__,
            )
            try:
                _expect_route_error(session.routing_record)
            finally:
                namespace[name] = original
        namespace[BINDING] = inherited
        _expect_route_error(session.routing_record)
        namespace[BINDING] = adapter
        for invalid_schema in (None, True, 0, "1"):
            invalid = host()
            invalid.module.CHAIR_ANALYSIS_SCHEMA_VERSION = invalid_schema
            _expect_route_error(lambda: (
                transition_workflow.ModularTransitionWorkflowSession(
                    invalid, functions,
                )
            ))
        partial = host()
        del partial.module._chair_generation_context
        _expect_route_error(lambda: (
            transition_workflow.ModularTransitionWorkflowSession(
                partial, functions,
            )
        ))
        rollback = host()
        rollback.module._A8A7B15_ANALYSE_CHAIRS = lambda *_: None
        before = dict(rollback.module.__dict__)
        _expect_route_error(lambda: (
            transition_workflow.ModularTransitionWorkflowSession(
                rollback, functions,
            )
        ))
        assert rollback.module.__dict__ == before, "atomic binding rollback"
        assert rollback.module.LAUNCH_COUNT == 0


def main():
    if "--legacy-witness" in sys.argv:
        validate_signature(_legacy_signature())
    else:
        from tracktemplate.application.chair_analysis_signature import (
            chair_analysis_signature,
        )
        def signature(*args):
            return chair_analysis_signature(*args, schema_version=1)
        validate_signature(signature)
        validate_live_cache(signature)
        validate_binding()
        print(SENTINEL)


if __name__ == "__main__":
    main()
