#!/usr/bin/env python3
"""Prove native platform-core conversion and the actual B16 caller."""

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
    os.environ.get("TRACKTEMPLATE_PLATFORM_CORE_SOURCE_ROOT", ROOT)
)
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
import validate_phase7_platform_core as proof  # noqa: E402
import validate_phase7_platform_transitions as transition_proof  # noqa: E402


SENTINEL = "Phase 7 platform core FreeCAD validation passed"


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
    legacy_records = transition_proof.caller_cases(host.module.__dict__)
    legacy_builders = [
        host.module.build_platform_core(*case)
        for case in proof._cases(host.module.__dict__)
    ]
    legacy_failures = [
        proof._failure(host.module.build_platform_core, case)
        for case in proof._invalid_cases(host.module.__dict__)
    ]

    session = transition_workflow.ModularTransitionWorkflowSession(
        host,
        _functions(),
    )
    record = session.routing_record()
    assert record["schema_version"] == 10
    assert record["contract_id"] == "tracktemplate:phase7:platform-core:1"
    assert record["function_names"] == list(
        transition_workflow.PRODUCT_FUNCTION_NAMES
    )
    assert len(record["function_names"]) == 15
    assert len(record["caller_names"]) == 39
    assert record["mixed_route"] is False

    adapter = session.module.build_platform_core
    assert type(adapter) is transition_workflow._PlatformCoreAdapter
    assert adapter.calculation is api.build_platform_core
    assert adapter.vector_factory is App.Vector
    caller = session.module.prepare_track_alignment
    assert caller.__globals__ is session.module.__dict__
    assert caller.__globals__["build_platform_core"] is adapter
    assert "build_platform_core" in caller.__code__.co_names

    cases = proof._cases(host.module.__dict__)
    for case, legacy in zip(cases, legacy_builders):
        result = adapter(*case)
        assert tuple(result) == proof.RESULT_KEYS
        assert transition_proof.snapshot(result) == (
            transition_proof.snapshot(legacy)
        )
        assert proof._neutral_result(result) == api.build_platform_core(*case)
        assert all(type(point) is App.Vector for point in result["points"])
        assert all(point.z == 0.0 for point in result["points"])
        assert len({id(point) for point in result["points"]}) == len(
            result["points"]
        )
    assert [
        proof._failure(adapter, case)
        for case in proof._invalid_cases(host.module.__dict__)
    ] == legacy_failures

    candidate_records = transition_proof.caller_cases(
        session.module.__dict__
    )
    assert candidate_records == legacy_records
    for case_index, changes in enumerate((
        {},
        {"start_spacing": 41.0},
        {"side": "Inside", "curve_spacing": 45.0},
    )):
        config = transition_proof.platform_config(**changes)
        metadata = config["metadata"]
        centre = session.module.main_circle_centre(600.0, 600.0)
        main = session.module.build_concentric_core(
            centre,
            600.0,
            600.0,
            600.0,
            math.pi / 2.0,
            "Main Track",
        )
        main_before = transition_proof.snapshot(main)
        if case_index == 2:
            rejection = transition_proof.observe(
                session.module.prepare_track_alignment,
                config,
                centre,
                600.0,
                math.pi / 2.0,
                main,
            )
            assert rejection == legacy_records["prepare"][2]["result"]
            assert config["metadata"] is metadata
            assert transition_proof.snapshot(main) == main_before
            continue
        result = session.module.prepare_track_alignment(
            config,
            centre,
            600.0,
            math.pi / 2.0,
            main,
        )
        assert config["metadata"] is metadata
        assert transition_proof.snapshot(main) == main_before
        assert all(type(point) is App.Vector for point in result["points"])
        assert all(point.z == 0.0 for point in result["points"])

    assert session.routing_record() == record
    assert _document_state() == before

    result = {
        "status": "PASS",
        "source_root": str(SOURCE_ROOT),
        "foundation": foundation,
        "routing": record,
        "builder_case_count": len(cases),
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
                "tests/validate_phase7_platform_core.py",
                "tests/freecad_validate_phase7_platform_core.py",
            )
        },
    }
    output = os.environ.get("TRACKTEMPLATE_PLATFORM_CORE_OUTPUT")
    if output:
        with pathlib.Path(output).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase7_platform_core"}:
    try:
        validate()
    except Exception:  # noqa: BLE001 - preserve exact qualified proof failure
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
