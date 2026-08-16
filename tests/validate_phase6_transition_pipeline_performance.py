#!/usr/bin/env python3
"""Fast contracts for the Phase 6 transition pipeline profiler."""

import ast
import copy
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase6_transition_pipeline_performance as profile  # noqa: E402


def _assert_raises_text(error_type, text, action):
    try:
        action()
    except error_type as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected {}".format(error_type.__name__))


def _signature(character):
    return "sha256:" + character * 64


def _measurement(seed, wall_ms=None, process_cpu_ms=None):
    wall_ms = 10.0 + seed if wall_ms is None else wall_ms
    process_cpu_ms = (
        8.0 + seed if process_cpu_ms is None else process_cpu_ms
    )
    return {
        "peak_rss_after_mb": 121.0 + seed,
        "peak_rss_before_mb": 120.0,
        "peak_rss_delta_mb": 1.0 + seed,
        "process_cpu_ms": process_cpu_ms,
        "rss_after_mb": 101.0 + seed,
        "rss_before_mb": 100.0,
        "rss_delta_mb": 1.0 + seed,
        "wall_ms": wall_ms,
    }


def _snapshot(edited=False):
    return {
        "active_coin_scene_node_count": 16,
        "active_document": "Phase5TransitionInteractionRange",
        "cache_regeneration_count": 3 if edited else 2,
        "cache_request_count": 5 if edited else 4,
        "cache_reuse_count": 2,
        "canonical_state_digest": ("c" if edited else "a") * 64,
        "display_modes_added": 2,
        "document_names": ["Phase5TransitionInteractionRange"],
        "document_object_count": 2,
        "logical_layer_count": 2,
        "mapping_digest": "b" * 64,
        "part_shape_count": 0,
        "proxy_count": 2,
        "redo_count": 0,
        "root_children_added": 0,
        "switch_children_added": 2,
        "undo_count": 1 if edited else 0,
    }


HOST_PROFILE_111 = "linux-x86_64-flatpak-freecad-1.1.1"
HOST_PROFILE_113 = "linux-x86_64-flatpak-freecad-1.1.3"


def _geometry_receipt(freecad_version="1.1.1"):
    return {
        "closed": False,
        "contract_id": profile.EXACT_GEOMETRY_CONTRACT_ID,
        "domain_id": profile.TARGET_TRANSITION_ID,
        "edge_count": 4,
        "exact_artifact_signature": _signature("a"),
        "exact_result_signature": _signature("b"),
        "frame_id": "canonical-local-left-turn-v1",
        "freecad_version": freecad_version,
        "geometry_signature": _signature("c"),
        "length_unit": "mm",
        "maximum_abs_z_mm": 0.0,
        "maximum_x_mm": 350.0,
        "maximum_y_mm": 20.0,
        "minimum_x_mm": 0.0,
        "minimum_y_mm": 0.0,
        "opencascade_version": "7.8.1",
        "polyline_length_mm": 360.0,
        "shape_type": "Wire",
        "source_signature": _signature("d"),
        "vertex_count": 5,
    }


def _validation_stage(
    seed,
    status_before,
    reused,
    freecad_version="1.1.1",
):
    receipt = _geometry_receipt(freecad_version)
    return {
        "artifact_reused": reused,
        "artifact_signature": receipt["exact_artifact_signature"],
        "cache_status_after": "current",
        "cache_status_before": status_before,
        "exact_result_signature": receipt["exact_result_signature"],
        "geometry_build_count": 1,
        "geometry_receipt": receipt,
        "source_signature": receipt["source_signature"],
        **_measurement(seed),
    }


def _output():
    dxf_filename = "transition-centreline-abc.dxf"
    manifest_filename = (
        "transition-centreline-abc.dependency-manifest.json"
    )
    return {
        "directory_entries": sorted([dxf_filename, manifest_filename]),
        "dxf": {
            "filename": dxf_filename,
            "sha256": "e" * 64,
            "size_bytes": 512,
        },
        "manifest": {
            "filename": manifest_filename,
            "sha256": "f" * 64,
            "size_bytes": 1024,
        },
        "staging_entries": [],
    }


def _export_stage(seed, disposition, freecad_version="1.1.1"):
    geometry = _geometry_receipt(freecad_version)
    output = _output()
    receipt = {
        "cleanup_complete": True,
        "contract_id": profile.DXF_EXPORT_CONTRACT_ID,
        "disposition": disposition,
        "dxf_filename": output["dxf"]["filename"],
        "dxf_sha256": output["dxf"]["sha256"],
        "exact_result_signature": geometry["exact_result_signature"],
        "geometry_signature": geometry["geometry_signature"],
        "manifest_filename": output["manifest"]["filename"],
        "manifest_sha256": output["manifest"]["sha256"],
        "project_status": "unknown",
        "result_signature": _signature("f"),
        "source_signature": _signature("e"),
    }
    return {
        "active_document_after": "Phase5TransitionInteractionRange",
        "active_document_before": "Phase5TransitionInteractionRange",
        "documents_after": ["Phase5TransitionInteractionRange"],
        "documents_before": ["Phase5TransitionInteractionRange"],
        "geometry_build_count": 1,
        "geometry_receipt": geometry,
        "output": output,
        "post_action_audit": _measurement(seed + 0.1),
        "receipt": receipt,
        **_measurement(seed),
    }


def _parent(children, seed):
    child_wall_ms = sum(child["wall_ms"] for child in children)
    child_cpu_ms = sum(child["process_cpu_ms"] for child in children)
    wall_ms = child_wall_ms + 0.5
    cpu_ms = child_cpu_ms + 0.25
    return {
        "child_process_cpu_ms": child_cpu_ms,
        "child_wall_ms": child_wall_ms,
        "uncovered_process_cpu_ms": 0.25,
        "uncovered_wall_ms": 0.5,
        **_measurement(
            seed,
            wall_ms=wall_ms,
            process_cpu_ms=cpu_ms,
        ),
    }


def _reuse_cycle(seed, cold_export, freecad_version="1.1.1"):
    validation = _validation_stage(
        seed,
        "current",
        True,
        freecad_version,
    )
    export = _export_stage(
        seed + 0.25,
        "reused",
        freecad_version,
    )
    export["output"] = copy.deepcopy(cold_export["output"])
    export["receipt"]["dxf_filename"] = cold_export["receipt"][
        "dxf_filename"
    ]
    export["receipt"]["dxf_sha256"] = cold_export["receipt"][
        "dxf_sha256"
    ]
    export["receipt"]["manifest_filename"] = cold_export["receipt"][
        "manifest_filename"
    ]
    export["receipt"]["manifest_sha256"] = cold_export["receipt"][
        "manifest_sha256"
    ]
    return {
        "document_unchanged": True,
        "export": export,
        "parent": _parent((validation, export), seed + 0.5),
        "validation": validation,
    }


def _sample(
    seed,
    host_profile_id=HOST_PROFILE_111,
    freecad_version="1.1.1",
):
    edit = {
        "cache_regeneration_delta": 1,
        "cache_request_delta": 1,
        "changed": True,
        "target_transition_id": profile.TARGET_TRANSITION_ID,
        "transition_length_mm": 360.0,
        **_measurement(seed),
    }
    validation = _validation_stage(
        seed + 1.0,
        "missing",
        False,
        freecad_version,
    )
    export = _export_stage(
        seed + 2.0,
        "created",
        freecad_version,
    )
    parent = _parent((edit, validation, export), seed + 3.0)
    return {
        "cleanup": {
            "discarded_cache_count": 2,
            "discarded_exact_stages": ["exact-validation"],
            "disposed_proxy_count": 2,
            "object_count_before_close": 2,
            "output_retained": True,
            "remaining_documents": [],
            **_measurement(seed + 4.0),
        },
        "end_to_end": {
            **parent,
            "edit": edit,
            "exact_validation": validation,
            "export": export,
            "final_snapshot": _snapshot(edited=True),
            "initial_snapshot": _snapshot(edited=False),
        },
        "fixture": {
            "budget_status": "not-accepted",
            "comparison_status": "not-b14-equivalent",
            "exact_chord_error_mm": profile.EXACT_CHORD_ERROR_MM,
            "exact_maximum_segments": profile.EXACT_MAXIMUM_SEGMENTS,
            "logical_object_count": 2,
            "output_project_status": "unknown",
            "pointer_target": {"unique_mapping_count": 1},
            "preview_segment_count": 32,
            "target_transition_id": profile.TARGET_TRANSITION_ID,
            "warm_repetitions": profile.WARM_REPETITIONS,
        },
        "freecad_version": freecad_version,
        "host_profile_id": host_profile_id,
        "profile_id": profile.PROFILE_ID,
        "schema_version": profile.EVIDENCE_SCHEMA_VERSION,
        "starting_state": "fresh isolated test state",
        "warm": [
            _reuse_cycle(
                seed + 6.0 + index,
                export,
                freecad_version,
            )
            for index in range(profile.WARM_REPETITIONS)
        ],
        "warmup": _reuse_cycle(
            seed + 5.0,
            export,
            freecad_version,
        ),
    }


def validate_sample_contract():
    assert profile.EVIDENCE_SCHEMA_VERSION == 2
    assert profile.AUTHORISED_PERFORMANCE_HOSTS == {
        HOST_PROFILE_111: "1.1.1",
        HOST_PROFILE_113: "1.1.3",
    }
    sample = _sample(0.0)
    assert profile.validate_sample(sample) == {
        "dxf_sha256": "e" * 64,
        "exact_result_signature": _signature("b"),
        "freecad_version": "1.1.1",
        "geometry_signature": _signature("c"),
        "host_profile_id": HOST_PROFILE_111,
        "manifest_sha256": "f" * 64,
        "mapping_digest": "b" * 64,
    }

    sample_113 = _sample(
        0.0,
        host_profile_id=HOST_PROFILE_113,
        freecad_version="1.1.3",
    )
    assert profile.validate_sample(sample_113)["host_profile_id"] == (
        HOST_PROFILE_113
    )

    broken = copy.deepcopy(sample)
    broken["schema_version"] = 1
    _assert_raises_text(
        RuntimeError,
        "sample identity drifted",
        lambda: profile.validate_sample(broken),
    )

    for malformed_host_profile_id in ([], {}):
        broken = copy.deepcopy(sample)
        broken["host_profile_id"] = malformed_host_profile_id
        _assert_raises_text(
            RuntimeError,
            "sample identity drifted",
            lambda broken=broken: profile.validate_sample(broken),
        )

    broken = copy.deepcopy(sample)
    broken["host_profile_id"] = "linux-x86_64-flatpak-freecad-1.1.2"
    _assert_raises_text(
        RuntimeError,
        "sample identity drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample_113)
    broken["freecad_version"] = "1.1.1"
    _assert_raises_text(
        RuntimeError,
        "sample identity drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample_113)
    broken["end_to_end"]["exact_validation"]["geometry_receipt"][
        "freecad_version"
    ] = "1.1.1"
    _assert_raises_text(
        RuntimeError,
        "exact-geometry receipt drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["fixture"]["budget_status"] = "accepted"
    _assert_raises_text(
        RuntimeError,
        "fixture drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["final_snapshot"]["part_shape_count"] = 1
    _assert_raises_text(
        RuntimeError,
        "snapshot drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["uncovered_wall_ms"] += 1.0
    _assert_raises_text(
        RuntimeError,
        "did not reconcile",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["warm"][0]["document_unchanged"] = False
    _assert_raises_text(
        RuntimeError,
        "changed the editable document",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["export"]["receipt"][
        "project_status"
    ] = "project-cleared"
    _assert_raises_text(
        RuntimeError,
        "export lifecycle contract drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["export"]["output"]["staging_entries"] = [
        ".tracktemplate-transition-dxf-leftover"
    ]
    _assert_raises_text(
        RuntimeError,
        "output snapshot drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["exact_validation"]["geometry_receipt"][
        "contract_id"
    ] = "tracktemplate.wrong-exact-geometry.v1"
    _assert_raises_text(
        RuntimeError,
        "exact-geometry receipt drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["exact_validation"]["geometry_receipt"][
        "frame_id"
    ] = "incorrect-local-frame"
    _assert_raises_text(
        RuntimeError,
        "exact-geometry receipt drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["end_to_end"]["export"]["receipt"][
        "contract_id"
    ] = "tracktemplate.wrong-transition-export.v1"
    _assert_raises_text(
        RuntimeError,
        "export lifecycle contract drifted",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    changed_exact_result = _signature("9")
    broken["end_to_end"]["export"]["receipt"][
        "exact_result_signature"
    ] = changed_exact_result
    broken["end_to_end"]["export"]["geometry_receipt"][
        "exact_result_signature"
    ] = changed_exact_result
    _assert_raises_text(
        RuntimeError,
        "Cold Validate and Export exact-result signatures differ",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["warm"][0]["export"]["receipt"][
        "exact_result_signature"
    ] = changed_exact_result
    broken["warm"][0]["export"]["geometry_receipt"][
        "exact_result_signature"
    ] = changed_exact_result
    _assert_raises_text(
        RuntimeError,
        "reuse result differs from the cold result",
        lambda: profile.validate_sample(broken),
    )


def validate_summaries():
    samples = [
        _sample(float(index))
        for index in range(profile.DEFAULT_PROCESS_REPETITIONS)
    ]
    summary = profile.summarize_samples(samples)
    assert summary["fresh_process_repetitions"] == 3
    assert summary["warm_observation_count"] == 9
    assert summary["edit"]["wall_ms"]["values"] == [10.0, 11.0, 12.0]
    assert summary["validation"]["wall_ms"]["median"] == 12.0
    assert summary["warm_validation"]["wall_ms"]["count"] == 9
    assert summary["correctness"]["dxf_sha256"] == "e" * 64
    assert summary["correctness"]["host_profile_id"] == HOST_PROFILE_111
    assert summary["correctness"]["exact_result_signature"] == _signature(
        "b"
    )

    samples_113 = [
        _sample(
            float(index),
            host_profile_id=HOST_PROFILE_113,
            freecad_version="1.1.3",
        )
        for index in range(profile.DEFAULT_PROCESS_REPETITIONS)
    ]
    assert profile.summarize_samples(samples_113)["correctness"][
        "host_profile_id"
    ] == HOST_PROFILE_113

    mixed_samples = copy.deepcopy(samples)
    mixed_samples[-1] = samples_113[-1]
    _assert_raises_text(
        RuntimeError,
        "differs by process",
        lambda: profile.summarize_samples(mixed_samples),
    )

    _assert_raises_text(
        ValueError,
        "at least three fresh processes",
        lambda: profile.summarize_samples(samples[:2]),
    )

    changed = copy.deepcopy(samples)
    changed[-1]["end_to_end"]["export"]["receipt"][
        "dxf_sha256"
    ] = "1" * 64
    changed[-1]["end_to_end"]["export"]["output"]["dxf"][
        "sha256"
    ] = "1" * 64
    for cycle in [changed[-1]["warmup"], *changed[-1]["warm"]]:
        cycle["export"]["receipt"]["dxf_sha256"] = "1" * 64
        cycle["export"]["output"]["dxf"]["sha256"] = "1" * 64
    _assert_raises_text(
        RuntimeError,
        "differs by process",
        lambda: profile.summarize_samples(changed),
    )


def validate_source_and_scope_contracts():
    sample = _sample(0.0)
    output = "noise\n{}{}\n".format(
        profile.SAMPLE_SENTINEL,
        json.dumps({"result": sample}),
    )
    assert profile._sentinel_payload(output)["result"] == sample
    _assert_raises_text(
        RuntimeError,
        "observed 0",
        lambda: profile._sentinel_payload("noise"),
    )

    tool_path = ROOT / "tools/phase6_transition_pipeline_performance.py"
    gui_path = (
        ROOT
        / "tests"
        / "freecad_gui_profile_phase6_transition_pipeline.py"
    )
    tool_source = tool_path.read_text(encoding="utf-8")
    gui_source = gui_path.read_text(encoding="utf-8")
    tree = ast.parse(tool_source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint({
        "FreeCAD",
        "FreeCADGui",
        "Part",
        "PySide",
        "PySide2",
        "PySide6",
        "pivy",
    })
    assert "run-isolated" in tool_source
    assert "submit_and_wait" in tool_source
    assert "not-b14-equivalent" in gui_source
    assert "editing._apply_dialog_edit" in gui_source
    assert "api.regenerate_transition_exact" in gui_source
    assert "exporter.export_transition_dxf" in gui_source
    assert "build_transition_exact_geometry" in gui_source
    assert "EVIDENCE_SCHEMA_VERSION = 2" in gui_source
    assert '"schema_version": EVIDENCE_SCHEMA_VERSION' in tool_source
    assert '"schema_version": EVIDENCE_SCHEMA_VERSION' in gui_source
    assert "WARM_REPETITIONS = 3" in gui_source

    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/application/transition_exact.py",
        "tracktemplate/application/transition_export.py",
    ):
        assert profile.PROFILE_ID not in (
            ROOT / relative
        ).read_text(encoding="utf-8")


def validate_evidence_links_if_present():
    report = (
        ROOT
        / "reference"
        / "benchmarks"
        / "2026-08-02-phase6-transition-pipeline-performance.md"
    )
    if not report.is_file():
        return
    report_text = report.read_text(encoding="utf-8")
    assert "three fresh" in report_text
    assert "not a B14-equivalent" in report_text
    assert "No numerical budget" in report_text

    evidence = (
        ROOT / "reference/current/PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert report.name in evidence

    frozen = json.loads(
        (
            ROOT / "reference/history/frozen-records.json"
        ).read_text(encoding="utf-8")
    )
    records = {
        record["path"]: record for record in frozen["records"]
    }
    relative = report.relative_to(ROOT).as_posix()
    assert records[relative]["category"] == "benchmark"
    assert records[relative]["sha256"] == hashlib.sha256(
        report.read_bytes()
    ).hexdigest()


def validate():
    validate_sample_contract()
    validate_summaries()
    validate_source_and_scope_contracts()
    validate_evidence_links_if_present()
    print("Phase 6 transition pipeline profiler validation passed")


if __name__ == "__main__":
    validate()
