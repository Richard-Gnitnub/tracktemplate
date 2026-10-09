#!/usr/bin/env python3
"""Prove unchanged Analyse does not mutate state through the retained caller."""

import ast
import copy
import json
import pathlib
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate import api  # noqa: E402
from tracktemplate.application import chair_analysis_reuse as reuse  # noqa: E402
from tracktemplate.application.chair_analysis_signature import (  # noqa: E402
    chair_analysis_signature,
)
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow as workflow,
)
import validate_chair_analysis_signature as signature_proof  # noqa: E402


SENTINEL = "Chair analysis unchanged reuse validation passed"


def fixture():
    host = signature_proof._frozen_calculation()
    inputs = signature_proof._inputs()
    inputs[2].update(markers_visible=False, protected_markers_visible=False,
                     footprints_visible=False)
    state = {
        "inputs": inputs, "cached": None, "transactions": [], "writes": 0,
        "rails": 0, "timbers": 0, "display_builds": 0, "recomputes": 0,
        "fallbacks": 0, "objects": [], "solid": None,
    }
    doc = types.SimpleNamespace()
    metadata = types.SimpleNamespace()
    host.update({
        "App": types.SimpleNamespace(GuiUp=True),
        "TURNOUT_ID_PROPERTY": "TurnoutID",
        "CROSSOVER_ID_PROPERTY": "CrossoverID",
        "CHAIR_ANALYSIS_STATUS_PROPERTY": "ChairAnalysisStatus",
        "CHAIR_ANALYSIS_SIGNATURE_PROPERTY": "ChairAnalysisSignature",
        "CHAIR_ANALYSIS_SETTINGS_PROPERTY": "ChairAnalysisSettingsJSON",
        "CHAIR_SOLID_SIGNATURE_PROPERTY": "ChairSolidSignature",
        "CHAIR_SOLID_STATUS_STALE": "Stale",
    })

    def increment(name):
        state[name] += 1

    def extract(index, name):
        increment(name)
        return state["inputs"][index]

    def write(_doc, _kind, config, result):
        increment("writes")
        state["cached"] = copy.deepcopy(result)
        config.update({
            "chair_analysis_status": result["status"],
            "chair_analysis_signature": result["geometry_signature"],
            "chair_analysis_settings": result["settings"],
            "chair_analysis_schema_version": result["schema_version"],
        })
        metadata.ChairAnalysisStatus = result["status"]
        metadata.ChairAnalysisSignature = result["geometry_signature"]
        metadata.ChairAnalysisSettingsJSON = json.dumps(result["settings"])
        return config

    def display(*_):
        increment("display_builds")
        state["objects"] = [types.SimpleNamespace(
            Name="ChairAnalysis", Document=doc,
            GeneratedRole=host["CHAIR_ANALYSIS_GROUP_ROLE"],
            TurnoutID="TO-test", TemplateSetID="TS-test", Group=[],
            ViewObject=types.SimpleNamespace(Visibility=False),
        )]

    host.update({
        "turnout_config_by_id": lambda *_: state["inputs"][1],
        "crossover_config_by_id": lambda *_: state["inputs"][1],
        "chair_rail_records_for_entity": lambda *_: extract(3, "rails"),
        "chair_timber_records_for_entity": lambda *_: extract(4, "timbers"),
        "_chair_read_cached_result": lambda *_: state["cached"],
        "_chair_settings_object": lambda *_: metadata,
        "_chair_analysis_display_objects": lambda *_: state["objects"],
        "object_string_property": lambda obj, name, default="": (
            str(getattr(obj, name, default))
        ),
        "_chair_write_metadata": write,
        "_create_chair_analysis_display": display,
        "_document_recompute": lambda *_: increment("recomputes"),
        "_chair_solid_object": lambda *_: state["solid"],
        "_chair_physical_state_from_object": lambda obj: obj.state,
    })
    normalise = host["normalise_chair_analysis_settings"]
    host[signature_proof.BINDING] = lambda kind, config, settings, rails, timbers: (
        chair_analysis_signature(
            kind, config, normalise(settings), rails, timbers,
            schema_version=host["CHAIR_ANALYSIS_SCHEMA_VERSION"],
        )
    )
    doc.openTransaction = lambda name: state["transactions"].append(name)
    doc.commitTransaction = lambda: state["transactions"].append("commit")
    doc.abortTransaction = lambda: state["transactions"].append("abort")
    original = host[signature_proof.CALLERS[0]]

    def counted(*args):
        increment("fallbacks")
        return original(*args)

    adapter = workflow._ChairAnalysisReuseAdapter(counted, host)
    host[signature_proof.CALLERS[0]] = adapter

    def analyse(settings=None, kind="turnout", entity_id="TO-test"):
        return adapter(doc, kind, entity_id, settings)

    return host, state, doc, metadata, analyse


def validate_live_operation():
    host, state, doc, metadata, analyse = fixture()
    first = analyse(state["inputs"][2])
    assert first["cache_reused"] is False
    assert (state["rails"], state["timbers"], state["fallbacks"]) == (1, 1, 1)
    before = copy.deepcopy(state["cached"])
    counts = {key: state[key] for key in (
        "writes", "display_builds", "recomputes", "fallbacks",
    )}
    history = list(state["transactions"])
    second = analyse()
    assert second["cache_reused"] and second["display_cache_reused"]
    assert second["performance_timings_ms"] == {}
    assert state["cached"] == before
    assert reuse.reused_chair_analysis_result(before, "wrong-key", True) is None
    assert reuse.reused_chair_analysis_result(
        before, before["geometry_signature"], False,
    ) is None
    assert signature_proof._deterministic(second) == (
        signature_proof._deterministic(first)
    )
    assert state["transactions"] == history
    assert all(state[key] == value for key, value in counts.items())
    assert state["rails"] == state["timbers"] == 2
    second["positions"][0]["rail_name"] = "detached"
    assert state["cached"] == before

    for field, replacement in (
        ("name", "changed rail"),
        ("points", [[0.0, 0.000004], [20.0, 0.000004]]),
    ):
        previous = copy.deepcopy(state["inputs"][3][0][field])
        state["inputs"][3][0][field] = replacement
        scans, fallbacks = state["rails"], state["fallbacks"]
        changed = analyse()
        assert not changed["cache_reused"]
        assert state["rails"] == scans + 2
        assert state["fallbacks"] == fallbacks + 1
        state["inputs"][3][0][field] = previous
        assert not analyse()["cache_reused"]
        saved = copy.deepcopy(state["cached"])
        assert analyse()["cache_reused"]
        assert state["cached"] == saved

    # Every deliberately unproved state must reach the original exactly once.
    cases = (
        lambda h, s, d, m: s.update(cached=None),
        lambda h, s, d, m: s["cached"].update(entity_id="wrong"),
        lambda h, s, d, m: s["cached"].update(schema_version=True),
        lambda h, s, d, m: s["cached"].update(positions=[None]),
        lambda h, s, d, m: s["cached"].update(macro_version="unknown"),
        lambda h, s, d, m: s["cached"]["positions"][0].update(
            stable_chair_position_identity=""),
        lambda h, s, d, m: s["cached"]["summary"].update(chair_position_count=-1),
        lambda h, s, d, m: s["cached"].update(findings=float("nan")),
        lambda h, s, d, m: s["cached"].update(status=h["CHAIR_STATUS_STALE"]),
        lambda h, s, d, m: s["inputs"][1].update(
            chair_analysis_signature="old-key"),
        lambda h, s, d, m: setattr(m, "ChairAnalysisStatus", "inconsistent"),
        lambda h, s, d, m: setattr(m, "ChairAnalysisSettingsJSON", "bad-json"),
        lambda h, s, d, m: s.update(objects=[]),
        lambda h, s, d, m: s["objects"].append(s["objects"][0]),
        lambda h, s, d, m: setattr(s["objects"][0], "TurnoutID", "foreign"),
        lambda h, s, d, m: setattr(s["objects"][0], "TemplateSetID", "foreign"),
        lambda h, s, d, m: setattr(s["objects"][0], "Document", object()),
        lambda h, s, d, m: setattr(
            s["objects"][0].ViewObject, "Visibility", True),
        lambda h, s, d, m: setattr(s["objects"][0], "Group", [object()]),
        lambda h, s, d, m: s.update(solid=types.SimpleNamespace(state={})),
    )
    for mutate in cases:
        h, s, d, m, action = fixture()
        action(s["inputs"][2])
        mutate(h, s, d, m)
        before = s["fallbacks"]
        try:
            action()
        except (KeyError, TypeError, AttributeError):
            # Malformed state keeps the original operation's failure behavior.
            pass
        assert s["fallbacks"] == before + 1

    for name in ("cache_enabled", "physical_solids_visible", "markers_visible",
                 "protected_markers_visible", "footprints_visible",
                 "unresolved_markers_visible", "rail_fit_clearance_per_side"):
        h, s, d, m, action = fixture()
        action(s["inputs"][2])
        settings = dict(s["cached"]["settings"])
        settings[name] = (not settings[name] if isinstance(settings[name], bool)
                          else settings[name] + 0.01)
        before, scans = s["fallbacks"], s["rails"]
        action(settings)
        assert s["fallbacks"] == before + 1
        assert s["rails"] == scans + 1

    h, s, d, m, action = fixture()
    action(s["inputs"][2])
    h["App"].GuiUp = False
    s["objects"][0].ViewObject = None
    before = s["writes"]
    assert action()["cache_reused"]
    assert s["writes"] == before


def validate_presentation_and_wrappers():
    host, state, doc, metadata, analyse = fixture()
    analyse(state["inputs"][2])
    cached = state["cached"]
    adapter = host[signature_proof.CALLERS[0]]
    config = state["inputs"][1]
    group = state["objects"][0]
    # Existing reuse requests the group even when there are no positions.
    empty = copy.deepcopy(cached)
    empty["positions"] = []
    empty["settings"]["markers_visible"] = True
    group.ViewObject.Visibility = True
    assert adapter._presentation_current(doc, "turnout", "TO-test", config, empty)
    group.ViewObject.Visibility = False
    assert not adapter._presentation_current(
        doc, "turnout", "TO-test", config, empty,
    )
    # A requested populated layer requires its owned non-null shape and child.
    shown = copy.deepcopy(cached)
    shown["settings"]["markers_visible"] = True
    group.ViewObject.Visibility = True
    assert not adapter._presentation_current(
        doc, "turnout", "TO-test", config, shown,
    )
    marker = types.SimpleNamespace(
        Name="Markers", Document=doc,
        GeneratedRole=host["CHAIR_POSITION_MARKER_ROLE"],
        TurnoutID="TO-test", TemplateSetID="TS-test",
        Shape=types.SimpleNamespace(isNull=lambda: False),
        ViewObject=types.SimpleNamespace(Visibility=True),
    )
    state["objects"].append(marker)
    group.Group = [marker]
    assert adapter._presentation_current(doc, "turnout", "TO-test", config, shown)
    marker.Shape.isNull = lambda: True
    assert not adapter._presentation_current(
        doc, "turnout", "TO-test", config, shown,
    )
    state["objects"] = [group]
    group.Group = []
    group.ViewObject.Visibility = False

    # Execute both real retained B15 wrapper bodies, not substitute wrappers.
    tree = ast.parse(signature_proof.B15_PATH.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name == "analyse_entity_chair_positions"]
    physical = next(node for node in nodes if any(
        isinstance(item, ast.Name) and item.id == "_chair_mark_solid_stale"
        for item in ast.walk(node)
    ))
    telemetry = next(node for node in nodes if any(
        isinstance(item, ast.Name) and item.id == "_workflow_note_cache"
        for item in ast.walk(node)
    ))
    for node in (physical, telemetry):
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     str(signature_proof.B15_PATH), "exec"), host)
        if node is physical:
            host["_A8A7B15_ANALYSE_CHAIRS"] = host["analyse_entity_chair_positions"]
    notes = []
    stale_calls = []
    host["_workflow_note_cache"] = lambda *args, **kwargs: notes.append(
        (args, kwargs)
    )
    host["_chair_mark_solid_stale"] = lambda *args: stale_calls.append(args)
    host["_chair_physical_state_from_object"] = lambda obj: (
        obj.state if obj is not None else {}
    )
    operation = host["analyse_entity_chair_positions"]
    before = state["writes"]
    assert operation(doc, "turnout", "TO-test")["cache_reused"]
    assert state["writes"] == before and not stale_calls
    assert notes[-1] == (("chair analysis",), {
        "hits": 1, "misses": 0, "unchanged_reused": True,
    })
    state["solid"] = types.SimpleNamespace(state={
        "source_analysis_signature": "old-key",
    })
    fallbacks = state["fallbacks"]
    operation(doc, "turnout", "TO-test")
    assert state["fallbacks"] == fallbacks + 1
    assert stale_calls == [(doc, "turnout", "TO-test")]
    state["solid"] = None
    before, scans = state["fallbacks"], state["rails"]
    analyse(kind="unsupported")
    assert state["fallbacks"] == before + 1
    assert state["rails"] == scans + 1


def validate_binding():
    functions = {name: getattr(api, name) for name in workflow.PRODUCT_FUNCTION_NAMES}
    with tempfile.TemporaryDirectory(prefix="chair-noop-binding-") as directory:
        root = pathlib.Path(directory)
        contract = signature_proof.core_proof._fixture(root)

        def host():
            selected = b15_workflow_host.load_b15_workflow_host(root, contract)
            namespace = selected.module.__dict__
            exec(signature_proof._SYNTHETIC_ROUTES, namespace)
            for name in workflow._CHAIR_REUSE_OPERATIONS:
                exec("def {}(*args):\n    return None\n".format(name), namespace)
            return selected

        selected = host()
        namespace = selected.module.__dict__
        original = namespace[workflow._CHAIR_REUSE_BINDING]
        session = workflow.ModularTransitionWorkflowSession(selected, functions)
        adapter = namespace[workflow._CHAIR_REUSE_BINDING]
        assert isinstance(adapter, workflow._ChairAnalysisReuseAdapter)
        assert adapter.original is original
        expected = session.routing_record()
        for name in workflow._CHAIR_REUSE_OPERATIONS:
            value = namespace.pop(name)
            try:
                signature_proof._expect_route_error(session.routing_record)
            finally:
                namespace[name] = value
            foreign = types.FunctionType(value.__code__, {}, value.__name__)
            namespace[name] = foreign
            try:
                signature_proof._expect_route_error(session.routing_record)
            finally:
                namespace[name] = value
        removed = {name: namespace.pop(name)
                   for name in workflow._CHAIR_REUSE_MARKERS}
        try:
            session.routing_record()
        except workflow.TransitionWorkflowError as error:
            assert "chair-analysis reuse surface" in str(error)
        else:
            raise AssertionError("Absent reuse surface was accepted")
        finally:
            namespace.update(removed)
        namespace[workflow._CHAIR_REUSE_BINDING] = original
        signature_proof._expect_route_error(session.routing_record)
        namespace[workflow._CHAIR_REUSE_BINDING] = adapter
        assert session.routing_record() == expected
        broken = host()
        broken.module._A8A7B15_ANALYSE_CHAIRS = lambda *_: None
        saved = dict(broken.module.__dict__)
        signature_proof._expect_route_error(lambda: (
            workflow.ModularTransitionWorkflowSession(broken, functions)
        ))
        assert broken.module.__dict__ == saved


def main():
    validate_live_operation()
    validate_presentation_and_wrappers()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    main()
