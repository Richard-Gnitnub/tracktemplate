#!/usr/bin/env python3
"""Fast contracts for the Phase 5 interaction-range profiler."""

import ast
import copy
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase5_transition_interaction_range_profile as profile  # noqa: E402


def _assert_raises_text(error_type, text, action):
    try:
        action()
    except error_type as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected {}".format(error_type.__name__))


def _measurement(seed):
    return {
        "process_cpu_ms": 10.0 + seed,
        "rss_after_mb": 120.0 + seed,
        "rss_before_mb": 100.0,
        "rss_delta_mb": 20.0 + seed,
        "wall_ms": 12.0 + seed,
    }


def _snapshot(set_count, state_digest="a" * 64):
    object_count = set_count * profile.OBJECTS_PER_SET
    return {
        "active_coin_scene_node_count": object_count * 8,
        "cache_regeneration_count": object_count,
        "cache_request_count": object_count * 2,
        "cache_reuse_count": object_count,
        "canonical_state_digest": state_digest,
        "display_modes_added": object_count,
        "document_object_count": object_count,
        "logical_layer_count": object_count,
        "mapping_digest": "b" * 64,
        "part_shape_count": 0,
        "proxy_count": object_count,
        "root_children_added": 0,
        "switch_children_added": object_count,
    }


def _sample(set_count, seed):
    object_count = set_count * profile.OBJECTS_PER_SET
    initial = _snapshot(set_count)
    edited = _snapshot(set_count, state_digest="c" * 64)
    edited["cache_regeneration_count"] += 1
    edited["cache_request_count"] += 1
    restored = _snapshot(set_count)
    restored["cache_regeneration_count"] += 2
    restored["cache_request_count"] += 2
    target_id = "SET-{:03d}/curve-track/2/transition/exit".format(
        max(1, set_count // 2 + 1)
    )
    return {
        "cleanup": {
            "discarded_cache_count": object_count,
            "disposed_proxy_count": object_count,
            "object_count_before_close": object_count,
            "remaining_documents": [],
            **_measurement(seed + 5.0),
        },
        "cold": {**_measurement(seed), "snapshot": initial},
        "dialog_open": {
            **_measurement(seed + 1.0),
            "selected_identity_visible": True,
            "selected_length_text": "420.000",
        },
        "edit": {
            **_measurement(seed + 2.0),
            "cache_regeneration_delta": 1,
            "cache_request_delta": 1,
            "changed_transition_ids": [target_id],
            "history_delta": 1,
            "snapshot": edited,
            "target_length_mm": 359.999999996,
            "unchanged_record_count": object_count - 1,
        },
        "fixture": {
            "capacity_status": "not-accepted",
            "family_unit": (
                "qualified-one-secondary-track-entry-exit-pair"
            ),
            "logical_object_count": object_count,
            "preview_segment_count": profile.PREVIEW_SEGMENT_COUNT,
            "set_count": set_count,
            "target_transition_id": target_id,
            "view_layout": "test-only-grid-translations",
        },
        "freecad_version": "1.1.1",
        "profile_id": profile.PROFILE_ID,
        "schema_version": 1,
        "selection": {
            **_measurement(seed + 0.5),
            "mapping_domain_id": target_id,
            "pick_callback_count": 1,
            "pointer_target": {
                "hit_record_count": 3,
                "unique_mapping_count": 1,
            },
            "selected_transition_id": target_id,
        },
        "starting_state": "fresh isolated GUI process",
        "undo": {
            **_measurement(seed + 3.0),
            "cache_regeneration_delta": 1,
            "cache_request_delta": 1,
            "history_delta": -1,
            "snapshot": restored,
            "target_length_mm": 420.0000000006,
        },
    }


def validate_sample_contract():
    sample = _sample(4, 0.0)
    assert profile.validate_sample(sample, 4) == {
        "mapping_digest": "b" * 64,
        "target_transition_id": (
            "SET-003/curve-track/2/transition/exit"
        ),
    }

    broken = copy.deepcopy(sample)
    broken["fixture"]["capacity_status"] = "accepted"
    _assert_raises_text(
        RuntimeError,
        "fixture drifted",
        lambda: profile.validate_sample(broken, 4),
    )

    broken = copy.deepcopy(sample)
    broken["selection"]["selected_transition_id"] = "wrong"
    _assert_raises_text(
        RuntimeError,
        "selection contract drifted",
        lambda: profile.validate_sample(broken, 4),
    )

    broken = copy.deepcopy(sample)
    broken["edit"]["unchanged_record_count"] -= 1
    _assert_raises_text(
        RuntimeError,
        "edit isolation contract drifted",
        lambda: profile.validate_sample(broken, 4),
    )

    broken = copy.deepcopy(sample)
    broken["undo"]["snapshot"]["mapping_digest"] = "d" * 64
    _assert_raises_text(
        RuntimeError,
        "mapping drifted",
        lambda: profile.validate_sample(broken, 4),
    )

    broken = copy.deepcopy(sample)
    broken["cleanup"]["remaining_documents"] = ["Leaked"]
    _assert_raises_text(
        RuntimeError,
        "cleanup contract drifted",
        lambda: profile.validate_sample(broken, 4),
    )


def validate_summaries():
    samples_by_scale = {
        set_count: [
            _sample(set_count, float(index))
            for index in range(profile.DEFAULT_PROCESS_REPETITIONS)
        ]
        for set_count in profile.SCALE_SET_COUNTS
    }
    summary = profile.summarize_samples(samples_by_scale)
    assert summary["scale_set_counts"] == list(
        profile.SCALE_SET_COUNTS
    )
    assert summary["fresh_processes_total"] == (
        len(profile.SCALE_SET_COUNTS)
        * profile.DEFAULT_PROCESS_REPETITIONS
    )
    scale = summary["scales"]["4"]
    assert scale["logical_object_count"] == 8
    assert scale["fresh_process_repetitions"] == 3
    assert scale["selection"]["wall_ms"]["median"] == 13.5
    assert scale["edit"]["wall_ms"]["values"] == [14.0, 15.0, 16.0]
    assert scale["correctness"]["part_shape_count_values"] == [0, 0, 0]

    incomplete = copy.deepcopy(samples_by_scale)
    del incomplete[profile.SCALE_SET_COUNTS[-1]]
    _assert_raises_text(
        ValueError,
        "exact declared scale range",
        lambda: profile.summarize_samples(incomplete),
    )

    incomplete = copy.deepcopy(samples_by_scale)
    incomplete[profile.SCALE_SET_COUNTS[0]] = incomplete[
        profile.SCALE_SET_COUNTS[0]
    ][:2]
    _assert_raises_text(
        ValueError,
        "at least three fresh processes",
        lambda: profile.summarize_samples(incomplete),
    )


def validate_source_and_scope_contracts():
    sample = _sample(1, 0.0)
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

    source_path = (
        ROOT / "tools/phase5_transition_interaction_range_profile.py"
    )
    gui_path = (
        ROOT
        / "tests"
        / "freecad_gui_profile_phase5_transition_interaction_range.py"
    )
    source = source_path.read_text(encoding="utf-8")
    gui_source = gui_path.read_text(encoding="utf-8")
    source_tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(source_tree):
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
    assert "run-isolated" in source
    assert "submit_and_wait" in source
    assert "does not accept a capacity" in source
    assert "QtTest.QTest.mouseClick" in gui_source
    assert "editor.TransitionParameterEditorDialog" in gui_source
    assert "phase5_transition_representative_workload" in gui_source
    assert "GEOMETRY_TOLERANCE" in gui_source
    assert "Gui.Selection.addSelection" not in gui_source
    assert "SoTranslation" in gui_source
    assert "test-only-grid-translations" in gui_source
    assert '"Shape"' in gui_source
    assert "document.undo()" in gui_source

    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/presentation/__init__.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "transition_interaction_range" not in text


def validate_evidence_links_if_present():
    report = (
        ROOT
        / "reference"
        / "benchmarks"
        / "2026-07-31-phase5-transition-interaction-range-profile.md"
    )
    if not report.is_file():
        return
    report_flat = " ".join(
        report.read_text(encoding="utf-8").split()
    )
    assert "2–32 logical objects" in report_flat
    assert "three fresh" in report_flat
    assert "does not accept" in report_flat
    evidence = (
        ROOT
        / "reference"
        / "history"
        / "phase-closeouts"
        / "PHASE5_CLOSEOUT.md"
    ).read_text(encoding="utf-8")
    validation = (ROOT / "reference/VALIDATION.md").read_text(
        encoding="utf-8"
    )
    assert report.name in evidence
    assert report.name in validation
    assert "Phase 5 remains 0/4" in evidence


def validate():
    validate_sample_contract()
    validate_summaries()
    validate_source_and_scope_contracts()
    validate_evidence_links_if_present()
    print("Phase 5 transition interaction-range profiler validation passed")


if __name__ == "__main__":
    validate()
