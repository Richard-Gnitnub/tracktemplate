#!/usr/bin/env python3
"""Compare straight XO-001 B4 analysis in FreeCADCmd and the real GUI."""

import argparse
import datetime
import hashlib
import json
import pathlib

from tools.freecad_bridge import crossover_timber_recipe as recipe


ROOT = pathlib.Path(__file__).resolve().parents[2]
HEADLESS_SENTINEL = (
    "Phase 8 straight-host crossover B4 FreeCAD validation passed"
)
GUI_SENTINEL = "PHASE8_STRAIGHT_CROSSOVER_B4_GUI_PROBE_PASS"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE_RECIPE = "phase8-b14-straight-host-source-v1"
SOURCE_WITNESS = (
    "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
)
SOURCE_DOCUMENT_SEMANTIC = (
    "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
)
COMMON_SOURCE_PATHS = (
    "AdvancedTurnout.FCMacro",
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro",
    "TrackTemplate.FCMacro",
    "reference/contracts/phase1-crossover-feasibility.json",
    "reference/contracts/phase1-compatibility.json",
    "reference/contracts/phase1-transition-pilot.json",
    "tools/phase3_transition_pilot.py",
    "tools/freecad_bridge/b14_recipe.py",
    "tools/freecad_bridge/ordinary_track_recipe.py",
    "tools/freecad_bridge/crossover_timber_recipe.py",
    "tools/freecad_bridge/compare_phase8_straight_crossover_b4_modes.py",
    "tools/freecad_bridge/run_b14_straight_station.py",
    "tools/freecad_bridge/probes/b14_straight_station_driver.py",
    "tools/freecad_bridge/probes/load_phase3_transition_workflow.py",
    "tests/freecad_validate_phase8_straight_crossover_b4.py",
)
CORE_FIELDS = (
    "status", "counts", "record_turnout_sides", "record_envelope_kinds",
    "record_identity_sha256", "stable_record_sha256",
    "resolution_signature",
)
COMPARED_FIELDS = (
    "full_ordered_records", "stable_ordered_records",
    "inherited_findings", "resolved_findings", "unresolved",
    "production_index", "production_bindings",
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def source_hashes(root):
    """Fingerprint source common to the straight headless and GUI checks."""
    root = pathlib.Path(root)
    paths = [root / relative for relative in COMMON_SOURCE_PATHS]
    paths.extend(sorted((root / "tracktemplate").rglob("*.py")))
    return {
        str(path.relative_to(root)): _sha256(path)
        for path in paths
    }


def _source_hashes_for_paths(root, relatives):
    """Recheck every path declared by the GUI receipt within this root."""
    root = pathlib.Path(root).resolve()
    actual = {}
    for relative in relatives:
        _require(isinstance(relative, str) and relative,
                 "GUI source map contains an invalid path")
        path = (root / relative).resolve()
        _require(path.is_relative_to(root) and path.is_file(),
                 "GUI source map contains an unavailable path")
        actual[relative] = _sha256(path)
    return actual


def _split_analysis(value, label):
    """Exclude only the top-level measured timing dictionary."""
    _require(isinstance(value, dict) and bool(value),
             "{} has no full resolved_analysis".format(label))
    timings = value.get("performance_timings_ms")
    _require(isinstance(timings, dict) and bool(timings),
             "{} has no measured performance_timings_ms".format(label))
    semantic = dict(value)
    del semantic["performance_timings_ms"]
    return semantic, timings


def compare_receipts(headless, gui, evidence):
    """Require exact receipt identity and all non-timing B4 analysis data."""
    _require(headless.get("status") == "PASS"
             and headless.get("sentinel") == HEADLESS_SENTINEL,
             "Headless receipt has no successful FreeCAD sentinel")
    probe = gui.get("probe")
    _require(gui.get("status") == "PASS" and isinstance(probe, dict)
             and probe.get("sentinel") == GUI_SENTINEL,
             "Real-GUI receipt has no successful probe sentinel")
    _require(headless.get("host_profile_id") == PROFILE
             and probe.get("matched_profile_id") == PROFILE,
             "Headless and real-GUI host profiles differ or are unqualified")

    source_generation = evidence.get("source_generation")
    _require(isinstance(source_generation, dict)
             and source_generation.get("recipe_id") == SOURCE_RECIPE
             and source_generation.get("scenario") == "phase8-straight-host"
             and source_generation.get("status") == "completed"
             and source_generation.get("comparison_witness_sha256")
             == SOURCE_WITNESS
             and source_generation.get("run_document_sha256")
             == evidence.get("source_fixture_sha256")
             and source_generation.get("source_fixture_sha256")
             == source_generation.get("source_fixture_sha256_after"),
             "B14 source-generation receipt changed")
    _require(headless.get("source_document_semantic_sha256")
             == SOURCE_DOCUMENT_SEMANTIC
             and gui.get("source_document_semantic_sha256")
             == SOURCE_DOCUMENT_SEMANTIC,
             "Straight source semantic identity differs")

    for label, key, gui_after in (
        ("source receipt", "source_receipt", "source_receipt_sha256_after"),
        ("source fixture", "source_fixture", "source_fixture_sha256_after"),
    ):
        expected_path = evidence.get(key)
        expected_hash = evidence.get(key + "_sha256")
        _require(isinstance(expected_path, str) and bool(expected_path)
                 and _is_sha256(expected_hash)
                 and headless.get(key) == expected_path
                 and gui.get(key) == expected_path
                 and headless.get(key + "_sha256") == expected_hash
                 and gui.get(key + "_sha256") == expected_hash
                 and gui.get(gui_after) == expected_hash,
                 "{} path or hash differs between receipts".format(label))
    _require(headless.get("source_fixture_sha256_after")
             == evidence["source_fixture_sha256"],
             "Headless source fixture hash changed")
    _require(gui.get("headless_receipt")
             == evidence.get("headless_receipt")
             and _is_sha256(evidence.get("headless_receipt_sha256"))
             and gui.get("headless_receipt_sha256")
             == evidence["headless_receipt_sha256"]
             and gui.get("headless_receipt_sha256_after")
             == evidence["headless_receipt_sha256"],
             "GUI headless receipt path or raw hash changed")

    common = evidence.get("common_source_sha256")
    gui_sources = gui.get("source_sha256")
    _require(isinstance(common, dict) and bool(common)
             and set(COMMON_SOURCE_PATHS) <= set(common)
             and any(key.startswith("tracktemplate/") for key in common)
             and all(_is_sha256(value) for value in common.values())
             and common == headless.get("source_sha256")
             and common == headless.get("source_sha256_after"),
             "Headless comparison source identity differs")
    _require(isinstance(gui_sources, dict) and bool(gui_sources)
             and set(common) <= set(gui_sources)
             and gui_sources == gui.get("source_sha256_after")
             and gui_sources == evidence.get("gui_source_sha256")
             and all(gui_sources[key] == value
                     for key, value in common.items()),
             "GUI comparison source identity differs")

    observations = headless.get("comparison")
    _require(isinstance(observations, dict)
             and all(label in observations for label in ("B14", "B15", "B16"))
             and observations["B14"] == observations["B15"]
             and observations["B15"] == observations["B16"],
             "B14/B15/B16 straight B4 comparison differs")
    b16 = observations["B16"]
    applied = probe.get("applied")
    _require(isinstance(applied, dict)
             and isinstance(applied.get("result"), dict)
             and applied["result"] == b16.get("core"),
             "B16 core B4 result differs between host modes")
    for field in COMPARED_FIELDS:
        _require(field in b16 and field in applied
                 and b16[field] == applied[field],
                 "B16 {} differs between host modes".format(field))
    _require(applied.get("shape")
             == b16.get("b4_object", {}).get("shape", {}).get("summary"),
             "B16 B4 shape differs between host modes")
    _require(all(field in applied["result"] for field in CORE_FIELDS),
             "B16 core B4 result has a missing field")

    headless_analysis = headless.get("b16_resolved_analysis")
    gui_diagnostics = applied.get("resolved_analysis")
    _require(isinstance(headless_analysis, dict)
             and isinstance(gui_diagnostics, dict),
             "A host receipt has no full B16 resolved_analysis")
    headless_full = headless_analysis.get("full")
    gui_full = gui_diagnostics.get("full")
    headless_semantic, headless_timings = _split_analysis(
        headless_full, "Headless receipt"
    )
    gui_semantic, gui_timings = _split_analysis(
        gui_full, "Real-GUI receipt"
    )
    _require(_is_sha256(headless_analysis.get("sha256"))
             and recipe.digest(headless_full) == headless_analysis["sha256"]
             and _is_sha256(gui_diagnostics.get("sha256"))
             and recipe.digest(gui_full) == gui_diagnostics["sha256"],
             "Full resolved_analysis differs from its receipt digest")
    signature = headless_full.get("geometry_signature")
    _require(isinstance(signature, str) and bool(signature)
             and signature == headless_analysis.get("geometry_signature")
             and signature == gui_diagnostics.get("geometry_signature")
             and signature == gui_full.get("geometry_signature"),
             "B4 geometry signature differs between host modes")
    _require(gui_diagnostics.get("stored_views_match") is True
             and gui_diagnostics.get("analysis_basis")
             == gui_full.get("analysis_basis"),
             "Real-GUI stored B4 analysis changed")
    if headless_semantic != gui_semantic:
        missing = object()
        fields = sorted(
            key for key in set(headless_semantic) | set(gui_semantic)
            if headless_semantic.get(key, missing)
            != gui_semantic.get(key, missing)
        )
        raise ValueError(
            "Non-timing resolved_analysis fields differ: {!r}".format(fields)
        )
    semantic_sha = recipe.digest(headless_semantic)
    _require(headless_analysis.get("semantic_sha256") == semantic_sha,
             "Headless non-timing resolved_analysis digest changed")
    return {
        "status": "PASS",
        "host_profile_id": PROFILE,
        "source_fixture_sha256": evidence["source_fixture_sha256"],
        "source_receipt_sha256": evidence["source_receipt_sha256"],
        "headless_receipt_sha256": evidence["headless_receipt_sha256"],
        "gui_receipt_sha256": evidence["gui_receipt_sha256"],
        "common_source_sha256": common,
        "gui_source_sha256": gui_sources,
        "resolved_analysis_headless_sha256": headless_analysis["sha256"],
        "resolved_analysis_gui_sha256": gui_diagnostics["sha256"],
        "resolved_analysis_semantic_sha256": semantic_sha,
        "geometry_signature": signature,
        "record_identity_sha256": applied["result"]["record_identity_sha256"],
        "stable_record_sha256": applied["result"]["stable_record_sha256"],
        "measured_performance_timings_ms": {
            "headless": headless_timings,
            "real_gui": gui_timings,
        },
        "excluded_analysis_field": "performance_timings_ms",
    }


def _actual_evidence(headless_path, gui_path, headless, gui):
    """Read raw files so receipt claims cannot substitute for file identity."""
    source_receipt = pathlib.Path(headless["source_receipt"]).resolve()
    source_fixture = pathlib.Path(headless["source_fixture"]).resolve()
    gui_sources = gui["source_sha256"]
    return {
        "headless_receipt": str(headless_path),
        "headless_receipt_sha256": _sha256(headless_path),
        "gui_receipt_sha256": _sha256(gui_path),
        "source_receipt": str(source_receipt),
        "source_receipt_sha256": _sha256(source_receipt),
        "source_generation": json.loads(
            source_receipt.read_text(encoding="utf-8")
        ),
        "source_fixture": str(source_fixture),
        "source_fixture_sha256": _sha256(source_fixture),
        "common_source_sha256": source_hashes(ROOT),
        "gui_source_sha256": _source_hashes_for_paths(
            ROOT, gui_sources,
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--gui-receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()
    headless_path = args.headless_receipt.resolve()
    gui_path = args.gui_receipt.resolve()
    headless = json.loads(headless_path.read_text(encoding="utf-8"))
    gui = json.loads(gui_path.read_text(encoding="utf-8"))
    evidence = _actual_evidence(headless_path, gui_path, headless, gui)
    report = compare_receipts(headless, gui, evidence)
    report["headless_receipt"] = str(headless_path)
    report["gui_receipt"] = str(gui_path)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    output = gui_path.parent / (
        "straight-b4-cross-mode-comparison-{}.json".format(stamp)
    )
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("PHASE8_STRAIGHT_B4_CROSS_MODE_REPORT=" + str(output))
    print("PHASE8_STRAIGHT_B4_CROSS_MODE_PARITY_PASS")


if __name__ == "__main__":
    main()
