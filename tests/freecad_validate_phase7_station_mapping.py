"""Prove native station records, fresh vectors and actual B16 composition."""

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
import validate_phase7_station_mapping as proof  # noqa: E402

SENTINEL = "Phase 7 station mapping FreeCAD validation passed"


def document_state():
    return {
        name: tuple((obj.Name, obj.TypeId) for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def generated_alignments(module):
    centre = module.main_circle_centre(600.0, 600.0)
    main = module.build_concentric_core(
        centre, 600.0, 600.0, 600.0, math.pi / 2.0, "Main Track",
    )
    main.update(name="Main Track", width=32.0, create_template=True,
                show_centreline=True)
    parallel = module.prepare_track_alignment({
        "name": "Outside Track", "side": "Outside",
        "alignment_mode": module.MODE_MATCH_SPACINGS,
        "start_spacing": 50.0, "curve_spacing": 55.0,
        "finish_spacing": 50.0, "entry_transition_length": 600.0,
        "exit_transition_length": 600.0, "width": 35.0,
        "create_template": True, "show_centreline": True,
    }, centre, 600.0, math.pi / 2.0, main)
    platform = module.build_platform_core(
        centre, 655.0, 600.0, 600.0, 0.0, 0.0, math.pi / 2.0,
        "Platform Track",
    )
    platform.update(name="Platform Track", width=40.0, create_template=True,
                    show_centreline=True)
    curves = [main, parallel, platform]
    module.add_common_straight_extensions(curves, math.pi / 2.0)
    alignments = list(curves)
    for mode in ("Independent datum", "Curve entrance", "Curve exit"):
        route = module.build_straight_route({
            "manager_id": "station-qualified-" + mode,
            "connection_mode": mode, "length": 150.0,
            "track_count": 2, "direction": "Reverse",
            "parallel_side": "Right of travel", "rotation_degrees": 90.0,
        }, curves)
        alignments.extend(route["alignments"])
    return alignments


def observe_generated(pair, alignments):
    index, interpolate = pair
    records = []
    for alignment in alignments:
        before = proof.snapshot(alignment)
        data = index(alignment)
        assert tuple(data) == proof.FIELDS
        assert data["alignment"] is alignment
        assert data["points"] is not alignment["points"]
        assert data["headings"] is not alignment["headings"]
        assert all(a is b for a, b in zip(data["points"], alignment["points"]))
        samples = []
        for station in (-1.0, 0.0, data["core_start"], data["total"] / 2.0,
                        data["core_end"], data["total"], data["total"] + 1.0):
            point, heading = interpolate(data, station)
            again, _heading = interpolate(data, station)
            assert type(point) is App.Vector
            assert point is not again
            assert not any(point is old for old in data["points"])
            assert point.z == 0.0
            samples.append([station, proof.snapshot((point, heading))])
        assert proof.snapshot(alignment) == before
        records.append({"data": proof.snapshot(data), "samples": samples})
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
    original_pair = tuple(getattr(module, name) for name in proof.PAIR)
    original = proof.characterise(*original_pair, App.Vector)
    generated = generated_alignments(module)
    generated_original = observe_generated(original_pair, generated)
    session = transition_workflow.ModularTransitionWorkflowSession(
        host, {name: getattr(api, name)
               for name in transition_workflow.PRODUCT_FUNCTION_NAMES},
    )
    record = session.routing_record()
    assert record["schema_version"] == 8
    assert len(record["function_names"]) == 11
    assert len(transition_workflow.PRODUCT_CALLER_ROUTES) == 38
    assert record["contract_id"] == (
        "tracktemplate:phase7:alignment-handedness:1"
    )
    pair = tuple(getattr(module, name) for name in proof.PAIR)
    assert type(pair[0]) is transition_workflow._AlignmentStationDataAdapter
    assert type(pair[1]) is (
        transition_workflow._AlignmentStationInterpolationAdapter
    )
    assert pair[0].calculation is api.alignment_station_data
    assert pair[1].calculation is api.interpolate_alignment_station
    assert pair[1].vector_factory is App.Vector
    candidate = proof.characterise(*pair, App.Vector)
    assert candidate == original
    generated_candidate = observe_generated(pair, generated)
    assert generated_candidate == generated_original
    for caller_name, targets in transition_workflow.PRODUCT_CALLER_ROUTES:
        if not any(target in proof.PAIR for target in targets):
            continue
        if "." in caller_name:
            owner, method = caller_name.split(".", 1)
            caller = getattr(getattr(module, owner), method)
        else:
            caller = getattr(module, caller_name)
        assert caller.__globals__ is module.__dict__
        for target in targets:
            assert caller.__globals__[target] is getattr(module, target)
    assert session.routing_record() == record
    assert document_state() == before_documents
    result = {
        "status": "PASS", "foundation": foundation, "routing": record,
        "native_pair": candidate, "generated_records": generated_candidate,
        "generated_alignment_count": len(generated),
        "document_state_unchanged": True,
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "TrackTemplate.FCMacro", "tracktemplate/domain/alignment.py",
                "tracktemplate/api.py",
                "tracktemplate/compatibility/transition_workflow.py",
                "tests/validate_phase7_station_mapping.py",
                "tests/freecad_validate_phase7_station_mapping.py",
            )
        },
    }
    output = os.environ.get("TRACKTEMPLATE_STATION_QUALIFIED_OUTPUT")
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


if __name__ in {"__main__", "freecad_validate_phase7_station_mapping"}:
    _run_as_script()
