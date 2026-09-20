#!/usr/bin/env python3
"""Prove native track preparation and the actual qualified B16 caller."""

import hashlib
import json
import math
import os
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(
    os.environ.get("TRACKTEMPLATE_TRACK_PREPARATION_SOURCE_ROOT", ROOT)
)
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_track_alignment_preparation as proof  # noqa: E402


SENTINEL = "Phase 7 track-alignment preparation FreeCAD validation passed"


def _document_state():
    return {
        name: tuple((obj.Name, obj.TypeId) for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def _native_main(namespace):
    centre = namespace["main_circle_centre"](600.0, 600.0)
    main = namespace["build_concentric_core"](
        centre,
        600.0,
        600.0,
        600.0,
        math.pi / 2.0,
        "Main Track",
    )
    return centre, main


def _native_observation(function, config, centre, main):
    metadata = config["metadata"]
    main_before = proof._snapshot(main)
    try:
        value = function(
            config, centre, 600.0, math.pi / 2.0, main,
        )
    except Exception as error:  # noqa: BLE001 - exact inherited failure proof
        result = {
            "exception": type(error).__name__,
            "message": str(error),
        }
    else:
        result = {"value": proof._snapshot(value), "keys": list(value)}
    assert config["metadata"] is metadata
    assert proof._snapshot(main) == main_before
    return {
        "config": proof._snapshot(config),
        "writes": list(getattr(config, "writes", ())),
        "result": result,
    }


def validate():
    before = _document_state()
    assert pathlib.Path(api.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/api.py"
    )
    assert pathlib.Path(transition_workflow.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/compatibility/transition_workflow.py"
    )

    launcher = runpy.run_path(str(SOURCE_ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == (
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
    )
    modular_api, bootstrap = launcher["_load_foundation"](SOURCE_ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json"
    )

    host = b15_workflow_host.load_b15_workflow_host(SOURCE_ROOT, contract)
    legacy_centre, legacy_main = _native_main(host.module.__dict__)
    sources = proof._cases(host.module.__dict__)
    legacy_records = [
        _native_observation(
            host.module.prepare_track_alignment,
            proof._TrackedConfig(source),
            legacy_centre,
            legacy_main,
        )
        for source in sources
    ]
    legacy_failures = [
        _native_observation(
            host.module.prepare_track_alignment,
            proof._TrackedConfig(source),
            legacy_centre,
            legacy_main,
        )
        for source, _diagnostic in proof._invalid_cases(
            host.module.__dict__
        )
    ]

    session = transition_workflow.ModularTransitionWorkflowSession(
        host,
        _functions(),
    )
    record = session.routing_record()
    assert record["schema_version"] == 11
    assert record["contract_id"] == (
        "tracktemplate:phase7:track-preparation:1"
    )
    assert record["function_names"] == list(
        transition_workflow.PRODUCT_FUNCTION_NAMES
    )
    assert len(record["function_names"]) == 18
    assert len(record["caller_names"]) == 39
    assert record["mixed_route"] is False

    adapter = session.module.prepare_track_alignment
    assert type(adapter) is (
        transition_workflow._PrepareTrackAlignmentAdapter
    )
    assert adapter.calculation is api.prepare_track_alignment
    assert adapter.vector_factory is App.Vector
    runner = session.module.run_macro
    assert runner.__globals__ is session.module.__dict__
    assert "prepare_track_alignment" in runner.__code__.co_names
    assert runner.__globals__["prepare_track_alignment"] is adapter

    candidate_centre, candidate_main = _native_main(session.module.__dict__)
    candidate_records = [
        _native_observation(
            adapter,
            proof._TrackedConfig(source),
            candidate_centre,
            candidate_main,
        )
        for source in sources
    ]
    assert candidate_records == legacy_records
    assert [
        _native_observation(
            adapter,
            proof._TrackedConfig(source),
            candidate_centre,
            candidate_main,
        )
        for source, _diagnostic in proof._invalid_cases(
            host.module.__dict__
        )
    ] == legacy_failures

    for source, legacy in zip(sources, legacy_records):
        if "value" not in legacy["result"]:
            continue
        config = proof._TrackedConfig(source)
        result = adapter(
            config,
            candidate_centre,
            600.0,
            math.pi / 2.0,
            candidate_main,
        )
        assert all(type(point) is App.Vector for point in result["points"])
        assert all(point.z == 0.0 for point in result["points"])
        assert len({id(point) for point in result["points"]}) == len(
            result["points"]
        )

    assert session.routing_record() == record
    assert _document_state() == before

    result = {
        "status": "PASS",
        "source_root": str(SOURCE_ROOT),
        "foundation": foundation,
        "routing": record,
        "case_count": len(sources),
        "invalid_case_count": len(legacy_failures),
        "caller_records_equal": True,
        "document_state_unchanged": True,
        "source_sha256": {
            name: hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest()
            for name in (
                "TrackTemplate.FCMacro",
                "tracktemplate/domain/alignment.py",
                "tracktemplate/api.py",
                "tracktemplate/compatibility/transition_workflow.py",
                "tests/validate_phase7_track_alignment_preparation.py",
                "tests/freecad_validate_phase7_track_alignment_preparation.py",
            )
        },
    }
    output = os.environ.get("TRACKTEMPLATE_TRACK_PREPARATION_OUTPUT")
    if output:
        with pathlib.Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


if __name__ in {
    "__main__",
    "freecad_validate_phase7_track_alignment_preparation",
}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - preserve exact qualified proof failure
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
