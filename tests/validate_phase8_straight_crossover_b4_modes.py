#!/usr/bin/env python3
"""Reject false straight XO-001 B4 headless/GUI analysis parity."""

import copy
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge import (  # noqa: E402
    compare_phase8_straight_crossover_b4_modes as comparator,
)


SENTINEL = "Phase 8 straight crossover B4 mode comparison validation passed"


def _receipts():
    analysis = {
        "geometry_signature": "straight-xo001-geometry",
        "analysis_basis": "Effective automatically resolved timber arrangement",
        "findings": [{"code": "retained-finding", "measure": 1}],
        "nested": {"performance_timings_ms": {"important": 2}},
        "performance_timings_ms": {"total": 10.0},
    }
    gui_analysis = copy.deepcopy(analysis)
    gui_analysis["performance_timings_ms"] = {"total": 12.0}
    semantic = dict(analysis)
    del semantic["performance_timings_ms"]
    core = {
        "status": "complete",
        "counts": {"effective_timber_count": 82, "shared_timber_count": 18},
        "record_turnout_sides": {"A": 32, "B": 32, "ENVELOPE": 18},
        "record_envelope_kinds": {"shared": 18},
        "record_identity_sha256": "a" * 64,
        "stable_record_sha256": "b" * 64,
        "resolution_signature": "straight-xo001-resolution",
    }
    observation = {
        "core": core,
        "full_ordered_records": [{"stable_identity": "XO-001:A:001"}],
        "stable_ordered_records": [{"id": "XO-001:A:001"}],
        "inherited_findings": [{"code": "inherited"}],
        "resolved_findings": analysis["findings"],
        "unresolved": [],
        "production_index": {"records": [{"record_id": "XO-001:001"}]},
        "production_bindings": [{"record_id": "XO-001:001"}],
        "b4_object": {"shape": {"summary": {"edges": 1216}}},
    }
    common = {
        path: "c" * 64 for path in comparator.COMMON_SOURCE_PATHS
    }
    common["tracktemplate/api.py"] = "d" * 64
    gui_sources = dict(common)
    gui_sources["tools/freecad_bridge/run_phase8_straight_crossover_b4_gui.py"] = (
        "e" * 64
    )
    headless = {
        "status": "PASS",
        "sentinel": comparator.HEADLESS_SENTINEL,
        "host_profile_id": comparator.PROFILE,
        "source_receipt": "/fixture/source-run.json",
        "source_receipt_sha256": "1" * 64,
        "source_fixture": "/fixture/straight-source.FCStd",
        "source_fixture_sha256": "2" * 64,
        "source_fixture_sha256_after": "2" * 64,
        "source_document_semantic_sha256": (
            comparator.SOURCE_DOCUMENT_SEMANTIC
        ),
        "source_sha256": common,
        "source_sha256_after": copy.deepcopy(common),
        "comparison": {
            label: copy.deepcopy(observation)
            for label in ("B14", "B15", "B16")
        },
        "b16_resolved_analysis": {
            "full": analysis,
            "sha256": recipe.digest(analysis),
            "semantic_sha256": recipe.digest(semantic),
            "geometry_signature": analysis["geometry_signature"],
        },
    }
    gui_applied = {
        "result": copy.deepcopy(core),
        "shape": {"edges": 1216},
        "resolved_analysis": {
            "full": gui_analysis,
            "sha256": recipe.digest(gui_analysis),
            "geometry_signature": gui_analysis["geometry_signature"],
            "analysis_basis": gui_analysis["analysis_basis"],
            "stored_views_match": True,
        },
    }
    for field in comparator.COMPARED_FIELDS:
        gui_applied[field] = copy.deepcopy(observation[field])
    gui = {
        "status": "PASS",
        "source_receipt": headless["source_receipt"],
        "source_receipt_sha256": "1" * 64,
        "source_receipt_sha256_after": "1" * 64,
        "source_fixture": headless["source_fixture"],
        "source_fixture_sha256": "2" * 64,
        "source_fixture_sha256_after": "2" * 64,
        "source_document_semantic_sha256": (
            comparator.SOURCE_DOCUMENT_SEMANTIC
        ),
        "headless_receipt": "/fixture/headless-run.json",
        "headless_receipt_sha256": "3" * 64,
        "headless_receipt_sha256_after": "3" * 64,
        "source_sha256": gui_sources,
        "source_sha256_after": copy.deepcopy(gui_sources),
        "probe": {
            "sentinel": comparator.GUI_SENTINEL,
            "matched_profile_id": comparator.PROFILE,
            "applied": gui_applied,
        },
    }
    evidence = {
        "source_generation": {
            "recipe_id": comparator.SOURCE_RECIPE,
            "scenario": "phase8-straight-host",
            "status": "completed",
            "comparison_witness_sha256": comparator.SOURCE_WITNESS,
            "run_document_sha256": "2" * 64,
            "source_fixture_sha256": "4" * 64,
            "source_fixture_sha256_after": "4" * 64,
        },
        "source_receipt": headless["source_receipt"],
        "source_receipt_sha256": "1" * 64,
        "source_fixture": headless["source_fixture"],
        "source_fixture_sha256": "2" * 64,
        "headless_receipt": gui["headless_receipt"],
        "headless_receipt_sha256": "3" * 64,
        "gui_receipt_sha256": "5" * 64,
        "common_source_sha256": copy.deepcopy(common),
        "gui_source_sha256": copy.deepcopy(gui_sources),
    }
    return headless, gui, evidence


def _reject(path, value, reason, refresh_gui_digest=False):
    headless, gui, evidence = _receipts()
    values = {"headless": headless, "gui": gui, "evidence": evidence}
    target = values
    for item in path[:-1]:
        target = target[item]
    target[path[-1]] = value
    if refresh_gui_digest:
        diagnostics = gui["probe"]["applied"]["resolved_analysis"]
        diagnostics["sha256"] = recipe.digest(diagnostics["full"])
    try:
        comparator.compare_receipts(headless, gui, evidence)
    except ValueError as error:
        assert reason in str(error), (reason, str(error))
    else:
        raise AssertionError("Invalid straight B4 receipt passed: " + reason)


def validate():
    headless, gui, evidence = _receipts()
    report = comparator.compare_receipts(headless, gui, evidence)
    assert report["status"] == "PASS"
    assert report["resolved_analysis_headless_sha256"] != (
        report["resolved_analysis_gui_sha256"]
    )
    assert report["resolved_analysis_semantic_sha256"] == (
        headless["b16_resolved_analysis"]["semantic_sha256"]
    )
    assert report["measured_performance_timings_ms"] == {
        "headless": {"total": 10.0},
        "real_gui": {"total": 12.0},
    }
    assert report["excluded_analysis_field"] == "performance_timings_ms"

    _reject(
        ("gui", "probe", "applied", "resolved_analysis", "full",
         "findings", 0, "measure"),
        2, "Non-timing resolved_analysis", refresh_gui_digest=True,
    )
    _reject(
        ("gui", "probe", "applied", "resolved_analysis", "full",
         "nested", "performance_timings_ms", "important"),
        3, "Non-timing resolved_analysis", refresh_gui_digest=True,
    )
    _reject(
        ("gui", "probe", "applied", "resolved_analysis", "full",
         "performance_timings_ms"),
        None, "measured performance_timings_ms",
    )
    _reject(
        ("headless", "b16_resolved_analysis", "sha256"),
        "f" * 64, "receipt digest",
    )
    _reject(
        ("gui", "probe", "applied", "resolved_analysis", "sha256"),
        "f" * 64, "receipt digest",
    )
    _reject(
        ("gui", "probe", "applied", "resolved_analysis",
         "geometry_signature"),
        "different", "geometry signature",
    )
    _reject(
        ("headless", "b16_resolved_analysis", "semantic_sha256"),
        "f" * 64, "non-timing resolved_analysis digest",
    )
    _reject(
        ("gui", "probe", "applied", "result", "counts",
         "effective_timber_count"),
        83, "core B4 result",
    )
    _reject(
        ("headless", "comparison", "B14", "core", "counts",
         "effective_timber_count"),
        83, "B14/B15/B16",
    )
    _reject(
        ("gui", "probe", "matched_profile_id"),
        "unqualified", "host profiles",
    )
    _reject(
        ("gui", "source_fixture_sha256"),
        "f" * 64, "source fixture path or hash",
    )
    _reject(
        ("evidence", "source_generation", "scenario"),
        "different", "B14 source-generation receipt",
    )
    _reject(
        ("gui", "source_sha256", "tracktemplate/api.py"),
        "f" * 64, "GUI comparison source identity",
    )
    _reject(
        ("headless", "source_sha256_after", "tracktemplate/api.py"),
        "f" * 64, "Headless comparison source identity",
    )
    _reject(
        ("gui", "headless_receipt_sha256"),
        "f" * 64, "headless receipt path or raw hash",
    )
    _reject(
        ("evidence", "source_receipt_sha256"),
        "f" * 64, "source receipt path or hash",
    )
    _reject(
        ("gui", "source_receipt"),
        "/fixture/other-source-run.json",
        "source receipt path or hash",
    )
    print(SENTINEL)


if __name__ == "__main__":
    validate()
