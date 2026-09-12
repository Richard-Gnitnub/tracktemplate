"""Prove native reflection records and the actual B16 caller binding."""

import ast
import copy
import hashlib
import json
import math
import os
import pathlib
import runpy
import sys

import FreeCAD as App

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_alignment_handedness as proof  # noqa: E402

SENTINEL = "Phase 7 alignment handedness FreeCAD validation passed"


def document_state():
    return {
        name: tuple((obj.Name, obj.TypeId) for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def generated_alignments(module):
    centre = module.main_circle_centre(600.0, 600.0)
    alignments = []
    for radius, name in ((600.0, "Main Track"), (655.0, "Secondary Track")):
        alignment = module.build_concentric_core(
            centre, radius, 600.0, 600.0, math.pi / 2.0, name,
        )
        alignment.update(name=name, width=32.0, create_template=True,
                         show_centreline=True, stable_id=name)
        alignments.append(alignment)
    module.add_common_straight_extensions(alignments, math.pi / 2.0)
    return alignments


def observe_loop(module, sources):
    """Run the frozen actual reflection/length loop with native records."""
    tree, _definitions = proof.definitions(proof.B15)
    run_macro = next(node for node in tree.body
                     if isinstance(node, ast.FunctionDef)
                     and node.name == "run_macro")
    loop = next(node for node in ast.walk(run_macro)
                if isinstance(node, ast.For) and any(
                    isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == proof.TARGET for call in ast.walk(node)
                ))
    records = []
    for sign in (1.0, -1.0):
        alignments = copy.deepcopy(sources)
        prior = [dict(item) for item in alignments]
        execution = {
            "all_alignments": alignments, "turn_sign": sign,
            proof.TARGET: module.mirror_alignment_for_turn,
            "polyline_length": module.polyline_length,
        }
        exec(compile(ast.Module(body=[loop], type_ignores=[]),
                     str(proof.B15), "exec"), execution)
        for old, alignment in zip(prior, alignments):
            assert tuple(alignment) == tuple(old)
            assert alignment["total_length"] == module.polyline_length(old["points"])
            assert len(alignment["points"]) == len(old["points"])
            assert len(alignment["headings"]) == len(old["headings"])
            for key in old:
                if key not in ("points", "headings", "total_length", *proof.ENDPOINTS):
                    assert alignment[key] is old[key]
            for point, previous in zip(alignment["points"], old["points"]):
                assert type(point) is App.Vector
                assert (point is previous) is (sign > 0.0)
                expected_y = previous.y if sign > 0.0 else -previous.y
                assert proof.snapshot((point.x, point.y, point.z)) == proof.snapshot(
                    (previous.x, expected_y, 0.0),
                )
            if sign > 0.0:
                assert alignment["points"] is old["points"]
                assert alignment["headings"] is old["headings"]
            else:
                assert alignment["points"] is not old["points"]
                assert alignment["headings"] is not old["headings"]
        records.append({"sign": sign, "output": proof.snapshot(alignments)})
    return records


def validate():
    before_documents = document_state()
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["workflow_host_loaded"] is False
    modular_api, bootstrap = launcher["_load_foundation"](ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        ROOT / "reference/contracts/phase1-transition-pilot.json",
    )
    host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
    module = host.module
    original = module.mirror_alignment_for_turn
    native_original = proof.normal_characterisation(lambda _factory: original, App.Vector)
    errors_original = proof.ordinary_error_characterisation(lambda _factory: original)
    sources = generated_alignments(module)
    loop_original = observe_loop(module, sources)
    session = transition_workflow.ModularTransitionWorkflowSession(
        host, {name: getattr(api, name)
               for name in transition_workflow.PRODUCT_FUNCTION_NAMES},
    )
    record = session.routing_record()
    assert record["schema_version"] == 8
    assert record["contract_id"] == "tracktemplate:phase7:alignment-handedness:1"
    assert len(record["function_names"]) == 11
    assert record["function_names"][-1] == proof.TARGET
    assert len(transition_workflow.PRODUCT_CALLER_ROUTES) == 38
    mirror = module.mirror_alignment_for_turn
    assert type(mirror) is transition_workflow._MirrorAlignmentForTurnAdapter
    assert mirror.calculation is api.mirror_alignment_for_turn
    assert mirror.vector_factory is App.Vector
    assert module.run_macro.__globals__ is module.__dict__
    assert module.run_macro.__globals__[proof.TARGET] is mirror
    assert proof.TARGET in module.run_macro.__code__.co_names
    native_candidate = proof.normal_characterisation(lambda _factory: mirror, App.Vector)
    errors_candidate = proof.ordinary_error_characterisation(lambda _factory: mirror)
    loop_candidate = observe_loop(module, sources)
    assert native_candidate == native_original
    assert errors_candidate == errors_original
    assert loop_candidate == loop_original
    assert session.routing_record() == record
    assert document_state() == before_documents
    result = {
        "status": "PASS", "foundation": foundation, "routing": record,
        "normal": native_candidate, "ordinary_errors": errors_candidate,
        "actual_caller": loop_candidate,
        "input_records": proof.snapshot(sources),
        "point_counts": [len(item["points"]) for item in sources],
        "document_state_unchanged": True,
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "TrackTemplate.FCMacro", "tracktemplate/domain/alignment.py",
                "tracktemplate/api.py", "tracktemplate/compatibility/transition_workflow.py",
                "tests/validate_phase7_alignment_handedness.py",
                "tests/freecad_validate_phase7_alignment_handedness.py",
            )
        },
    }
    output = os.environ.get("TRACKTEMPLATE_HANDEDNESS_QUALIFIED_OUTPUT")
    if output:
        with pathlib.Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase7_alignment_handedness"}:
    _run_as_script()
