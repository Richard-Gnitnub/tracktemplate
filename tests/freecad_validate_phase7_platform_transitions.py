"""Prove complete platform preparation with native vectors and B16 routing."""

import hashlib
import json
import os
import pathlib
import runpy
import sys

import FreeCAD as App

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(os.environ.get("TRACKTEMPLATE_PLATFORM_SOURCE_ROOT", ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402

sys.path.insert(0, str(ROOT / "tests"))
import validate_phase7_platform_transitions as proof  # noqa: E402

SENTINEL = "Phase 7 platform transition FreeCAD validation passed"


def document_state():
    return {
        name: tuple((obj.Name, obj.TypeId) for obj in document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


def validate():
    before = document_state()
    baseline_only = os.environ.get("TRACKTEMPLATE_PLATFORM_BASELINE_ONLY") == "1"
    assert pathlib.Path(api.__file__).resolve() == SOURCE_ROOT / "tracktemplate/api.py"
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
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json",
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        SOURCE_ROOT, api, contract,
    )
    module = session.module
    record = session.routing_record()
    assert len(record["function_names"]) == (11 if baseline_only else 19)
    assert record["schema_version"] == (8 if baseline_only else 12)
    original, _nodes = proof.legacy_namespace(proof.B15, App.Vector)
    reference = proof.caller_cases(original)
    actual = proof.caller_cases(module.__dict__)
    assert actual == reference
    for spacing in (40.0, 41.0):
        config = proof.platform_config(start_spacing=spacing)
        centre = module.main_circle_centre(600.0, 600.0)
        main = module.build_concentric_core(
            centre, 600.0, 600.0, 600.0, 1.5707963267948966, "Main Track",
        )
        result = module.prepare_track_alignment(
            config, centre, 600.0, 1.5707963267948966, main,
        )
        assert len(result["points"]) == len(result["headings"])
        assert all(type(point) is App.Vector for point in result["points"])
        assert all(point.z == 0.0 for point in result["points"])
    if not baseline_only:
        assert record["contract_id"] == (
            "tracktemplate:phase7:connected-straight-validation:1"
        )
        assert len(transition_workflow.PRODUCT_CALLER_ROUTES) == 39
        for name in proof.PUBLIC:
            assert getattr(module, name) is getattr(api, name)
        preparation = module.prepare_track_alignment
        assert type(preparation) is (
            transition_workflow._PrepareTrackAlignmentAdapter
        )
        assert preparation.calculation is api.prepare_track_alignment
        assert preparation.vector_factory is App.Vector
        preparation_globals = api.prepare_track_alignment.__globals__
        assert preparation_globals[proof.PUBLIC[2]] is getattr(
            api, proof.PUBLIC[2]
        )
        builder = module.build_platform_core
        assert type(builder) is transition_workflow._PlatformCoreAdapter
        assert builder.calculation is api.build_platform_core
        assert builder.vector_factory is App.Vector
        assert preparation_globals["build_platform_core"] is (
            api.build_platform_core
        )
        for name in proof.PUBLIC[:2]:
            assert name in api.build_platform_core.__code__.co_names
            assert api.build_platform_core.__globals__[name] is getattr(
                api, name,
            )
    assert session.routing_record() == record
    assert document_state() == before
    result = {
        "status": "PASS", "baseline_only": baseline_only,
        "source_root": str(SOURCE_ROOT), "foundation": foundation,
        "routing": record, "native_caller_records": actual,
        "document_state_unchanged": True,
        "source_sha256": {
            name: hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest()
            for name in (
                "TrackTemplate.FCMacro", "tracktemplate/domain/alignment.py",
                "tracktemplate/api.py", "tracktemplate/compatibility/transition_workflow.py",
            )
        },
    }
    output = os.environ.get("TRACKTEMPLATE_PLATFORM_QUALIFIED_OUTPUT")
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


if __name__ in {"__main__", "freecad_validate_phase7_platform_transitions"}:
    _run_as_script()
