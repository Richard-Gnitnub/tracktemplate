#!/usr/bin/env python3
"""Fast contracts for the Phase 5 Coin resource profiler."""

import ast
import copy
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import phase5_transition_coin_resource_profile as profile  # noqa: E402


def _assert_raises_text(error_type, text, action):
    try:
        action()
    except error_type as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Expected {}".format(error_type.__name__))


def _measurement(seed):
    return {
        "explicit_recompute": {
            "count": 1,
            "process_cpu_ms": 2.0 + seed,
            "result": True,
            "wall_ms": 3.0 + seed,
        },
        "process_cpu_ms": 20.0 + seed,
        "rss_after_mb": 120.0 + seed,
        "rss_before_mb": 100.0,
        "rss_delta_mb": 20.0 + seed,
        "wall_ms": 25.0 + seed,
    }


def _snapshot():
    return {
        "cache_regeneration_count": profile.FIXTURE_OBJECT_COUNT,
        "cache_request_count": profile.FIXTURE_OBJECT_COUNT,
        "cache_reuse_count": 0,
        "active_coin_scene_node_count": 224,
        "display_modes_added": profile.FIXTURE_OBJECT_COUNT,
        "document_object_count": profile.FIXTURE_OBJECT_COUNT,
        "identity_digest": "a" * 64,
        "logical_layer_count": profile.FIXTURE_OBJECT_COUNT,
        "part_shape_count": 0,
        "proxy_count": profile.FIXTURE_OBJECT_COUNT,
        "root_children_added": 0,
        "switch_children_added": profile.FIXTURE_OBJECT_COUNT,
    }


def _warm(seed, cache_request_count):
    record = _measurement(seed)
    record["explicit_recompute"]["result"] = False
    snapshot = _snapshot()
    snapshot.update({
        "cache_request_count": cache_request_count,
        "cache_reuse_count": (
            cache_request_count - profile.FIXTURE_OBJECT_COUNT
        ),
    })
    record.update({
        "cache_regeneration_delta": 0,
        "cache_request_delta": profile.FIXTURE_OBJECT_COUNT,
        "cache_reuse_delta": profile.FIXTURE_OBJECT_COUNT,
        "refresh_changed_count": 0,
        "snapshot": snapshot,
    })
    return record


def _sample(seed):
    cold = _measurement(seed)
    cold["snapshot"] = _snapshot()
    warmup = _warm(
        seed + 0.1,
        profile.FIXTURE_OBJECT_COUNT * 2,
    )
    warm = [
        _warm(
            seed + float(index + 1),
            profile.FIXTURE_OBJECT_COUNT * (index + 3),
        )
        for index in range(profile.WARM_REPETITIONS)
    ]
    return {
        "cleanup": {
            "discarded_cache_count": profile.FIXTURE_OBJECT_COUNT,
            "disposed_proxy_count": profile.FIXTURE_OBJECT_COUNT,
            "object_count_before_close": profile.FIXTURE_OBJECT_COUNT,
            "remaining_documents": [],
            **_measurement(seed + 10.0),
        },
        "cold": cold,
        "fixture": {
            "logical_object_count": profile.FIXTURE_OBJECT_COUNT,
            "preview_segment_count": 32,
            "resource_budget_status": "not-accepted",
            "warm_repetitions": profile.WARM_REPETITIONS,
        },
        "freecad_version": "1.1.1",
        "profile_id": profile.PROFILE_ID,
        "schema_version": 1,
        "starting_state": "fresh isolated GUI process",
        "warm": warm,
        "warmup": warmup,
    }


def validate_sample_contract():
    sample = _sample(0.0)
    assert profile.validate_sample(sample) == "a" * 64

    broken = copy.deepcopy(sample)
    broken["warm"][0]["snapshot"]["document_object_count"] += 1
    _assert_raises_text(
        RuntimeError,
        "object, layer or scene invariant",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["warm"][1]["snapshot"][
        "active_coin_scene_node_count"
    ] += 1
    _assert_raises_text(
        RuntimeError,
        "node count grew",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["warm"][2]["cache_regeneration_delta"] = 1
    _assert_raises_text(
        RuntimeError,
        "warm refresh contract",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["cleanup"]["remaining_documents"] = ["Leaked"]
    _assert_raises_text(
        RuntimeError,
        "cleanup contract",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["cold"]["explicit_recompute"]["count"] = True
    _assert_raises_text(
        RuntimeError,
        "recompute measurement is invalid",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["cold"]["explicit_recompute"]["result"] = 1
    _assert_raises_text(
        RuntimeError,
        "recompute measurement is invalid",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["cold"]["explicit_recompute"]["result"] = False
    _assert_raises_text(
        RuntimeError,
        "did not update",
        lambda: profile.validate_sample(broken),
    )

    broken = copy.deepcopy(sample)
    broken["warm"][0]["explicit_recompute"]["result"] = True
    _assert_raises_text(
        RuntimeError,
        "warm explicit recompute contract",
        lambda: profile.validate_sample(broken),
    )


def validate_summaries():
    samples = [_sample(float(index)) for index in range(3)]
    summary = profile.summarize_samples(samples)
    assert summary["fresh_process_repetitions"] == 3
    assert summary["measured_warm_observations"] == 9
    assert summary["cold"]["wall_ms"]["values"] == [
        25.0,
        26.0,
        27.0,
    ]
    assert summary["cold"]["wall_ms"]["median"] == 26.0
    assert summary["warm"]["wall_ms"]["count"] == 9
    assert summary["correctness"]["document_object_count_values"] == [
        32,
        32,
        32,
    ]
    assert summary["correctness"]["part_shape_count_values"] == [0, 0, 0]
    assert summary["correctness"]["cache_reuse_delta_values"] == [32] * 9
    assert summary["correctness"]["cold_recompute_result_values"] == [
        True,
        True,
        True,
    ]
    assert summary["correctness"]["warm_recompute_result_values"] == [
        False
    ] * 9
    _assert_raises_text(
        ValueError,
        "at least three",
        lambda: profile.summarize_samples(samples[:2]),
    )

    changed = copy.deepcopy(samples)
    changed[2]["cold"]["snapshot"]["identity_digest"] = "b" * 64
    for observation in [
        changed[2]["warmup"],
        *changed[2]["warm"],
    ]:
        observation["snapshot"]["identity_digest"] = "b" * 64
    _assert_raises_text(
        RuntimeError,
        "differs between fresh processes",
        lambda: profile.summarize_samples(changed),
    )

    changed = copy.deepcopy(samples)
    changed[2]["cold"]["snapshot"][
        "active_coin_scene_node_count"
    ] += 1
    for observation in [
        changed[2]["warmup"],
        *changed[2]["warm"],
    ]:
        observation["snapshot"][
            "active_coin_scene_node_count"
        ] += 1
    _assert_raises_text(
        RuntimeError,
        "node counts differ",
        lambda: profile.summarize_samples(changed),
    )


def validate_sentinel_and_source_contracts():
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
    _assert_raises_text(
        RuntimeError,
        "observed 2",
        lambda: profile._sentinel_payload(output + output),
    )

    source = (
        ROOT / "tools/phase5_transition_coin_resource_profile.py"
    ).read_text(encoding="utf-8")
    gui_source = (
        ROOT
        / "tests"
        / "freecad_gui_profile_phase5_transition_coin_resources.py"
    ).read_text(encoding="utf-8")
    source_tree = ast.parse(source)
    string_literals = " ".join(
        node.value
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    )
    assert "run-isolated" in source
    assert (
        "does not establish a representative workload, accepted capacity"
        in string_literals
    )
    assert "submit_and_wait" in source
    assert "import FreeCAD as App" in source
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
    assert "OBJECT_COUNT = 32" in gui_source
    assert "WARM_REPETITIONS = 3" in gui_source
    assert "App::FeaturePython" in gui_source
    assert '"Shape"' in gui_source
    assert "document.recompute()" in gui_source
    assert "scene_root.getNumChildren()" in gui_source
    assert "refresh_for_state" in gui_source

    formatted = profile._format_sample_log(
        "child output\n",
        "child error\n",
        "error: Could not connect: Operation not permitted\n",
    )
    assert "[stdout]\nchild output" in formatted
    assert "[stderr]\nchild error" in formatted
    assert "[isolated-launcher.log]" in formatted
    assert "Operation not permitted" in formatted


def validate_evidence_links_if_present():
    report = (
        ROOT
        / "reference"
        / "benchmarks"
        / "2026-07-29-phase5-transition-coin-resource-profile.md"
    )
    if not report.is_file():
        return
    report_text = report.read_text(encoding="utf-8")
    report_flat = " ".join(report_text.split())
    assert "32 logical transition objects" in report_flat
    assert "three fresh isolated" in report_flat
    assert "does not define a product capacity" in report_flat
    evidence = (
        ROOT / "reference/current/PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    validation = (ROOT / "reference/VALIDATION.md").read_text(
        encoding="utf-8"
    )
    assert report.name in evidence
    assert report.name in validation
    assert "0/4" in evidence


def validate():
    validate_sample_contract()
    validate_summaries()
    validate_sentinel_and_source_contracts()
    validate_evidence_links_if_present()
    print("Phase 5 transition Coin resource profiler validation passed")


if __name__ == "__main__":
    validate()
