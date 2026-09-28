#!/usr/bin/env python3
"""Compare fixed XO-001 B4 headless and real-GUI analysis receipts."""

import argparse
import datetime
import hashlib
import json
import pathlib

from tools.freecad_bridge import crossover_timber_recipe as recipe


HEADLESS_SENTINEL = "Phase 8 crossover B4 recovery FreeCAD validation passed"
GUI_SENTINEL = "PHASE8_CROSSOVER_B4_RECOVERY_GUI_PROBE_PASS"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CORE_FIELDS = (
    "status",
    "counts",
    "record_turnout_sides",
    "record_envelope_kinds",
    "record_identity_sha256",
    "stable_record_sha256",
    "resolution_signature",
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _split_analysis(analysis, label):
    """Keep full analysis; exclude only its top-level measured timings."""
    _require(isinstance(analysis, dict) and bool(analysis),
             "{} has no full resolved_analysis".format(label))
    timings = analysis.get("performance_timings_ms")
    _require(isinstance(timings, dict) and bool(timings),
             "{} has no measured performance_timings_ms".format(label))
    semantic = dict(analysis)
    del semantic["performance_timings_ms"]
    return semantic, timings


def compare_receipts(headless, gui):
    """Require exact source and non-timing B4 parity across qualified modes."""
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

    fixture = headless.get("source_fixture_sha256")
    _require(isinstance(fixture, str) and len(fixture) == 64
             and fixture == headless.get("source_fixture_sha256_after")
             and fixture == gui.get("source_fixture_sha256")
             and fixture == gui.get("source_fixture_sha256_after"),
             "Source fixture identity differs between host modes")
    sources = headless.get("comparison_source_sha256")
    _require(isinstance(sources, dict) and bool(sources)
             and set(recipe.COMPARISON_SOURCE_PATHS) <= set(sources)
             and any(path.startswith("tracktemplate/") for path in sources)
             and all(isinstance(value, str) and len(value) == 64
                     for value in sources.values())
             and sources == headless.get("comparison_source_sha256_after")
             and sources == gui.get("comparison_source_sha256")
             and sources == gui.get("comparison_source_sha256_after"),
             "Comparison source identity differs between host modes")

    headless_result = headless.get("result")
    gui_applied = probe.get("applied")
    _require(isinstance(headless_result, dict)
             and isinstance(gui_applied, dict)
             and isinstance(gui_applied.get("result"), dict),
             "A host receipt has no B4 result")
    gui_result = gui_applied["result"]
    for field in CORE_FIELDS:
        _require(field in headless_result and field in gui_result
                 and headless_result[field] == gui_result[field],
                 "B4 result field differs between modes: {}".format(field))

    headless_analysis = headless_result.get("resolved_analysis")
    gui_diagnostics = gui_applied.get("resolved_analysis")
    _require(isinstance(gui_diagnostics, dict),
             "Real-GUI receipt has no resolved analysis diagnostics")
    gui_analysis = gui_diagnostics.get("full")
    headless_semantic, headless_timings = _split_analysis(
        headless_analysis, "Headless receipt"
    )
    gui_semantic, gui_timings = _split_analysis(
        gui_analysis, "Real-GUI receipt"
    )
    _require(recipe.digest(headless_analysis)
             == headless_result.get("resolved_analysis_sha256")
             and recipe.digest(gui_analysis) == gui_diagnostics.get("sha256"),
             "Full resolved_analysis does not match its receipt digest")
    signature = headless_analysis.get("geometry_signature")
    _require(isinstance(signature, str) and bool(signature)
             and signature == headless_result.get(
                 "resolved_analysis_signature"
             )
             and signature == gui_diagnostics.get("geometry_signature")
             and signature == gui_analysis.get("geometry_signature"),
             "B4 geometry signature differs between modes")
    if headless_semantic != gui_semantic:
        missing = object()
        fields = sorted(
            field for field in set(headless_semantic) | set(gui_semantic)
            if headless_semantic.get(field, missing)
            != gui_semantic.get(field, missing)
        )
        raise ValueError(
            "Non-timing resolved_analysis fields differ: {!r}".format(
                fields
            )
        )

    return {
        "status": "PASS",
        "host_profile_id": PROFILE,
        "source_fixture_sha256": fixture,
        "comparison_source_sha256": sources,
        "resolved_analysis_headless_sha256": recipe.digest(
            headless_analysis
        ),
        "resolved_analysis_gui_sha256": recipe.digest(gui_analysis),
        "resolved_analysis_semantic_sha256": recipe.digest(
            headless_semantic
        ),
        "geometry_signature": signature,
        "record_identity_sha256": gui_result["record_identity_sha256"],
        "stable_record_sha256": gui_result["stable_record_sha256"],
        "measured_performance_timings_ms": {
            "headless": headless_timings,
            "real_gui": gui_timings,
        },
        "excluded_analysis_field": "performance_timings_ms",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--gui-receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()
    headless = json.loads(args.headless_receipt.read_text(encoding="utf-8"))
    gui = json.loads(args.gui_receipt.read_text(encoding="utf-8"))
    report = compare_receipts(headless, gui)
    report["headless_receipt"] = str(args.headless_receipt.resolve())
    report["gui_receipt"] = str(args.gui_receipt.resolve())
    report["headless_receipt_sha256"] = hashlib.sha256(
        args.headless_receipt.read_bytes()
    ).hexdigest()
    report["gui_receipt_sha256"] = hashlib.sha256(
        args.gui_receipt.read_bytes()
    ).hexdigest()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    output = args.gui_receipt.parent / (
        "cross-mode-comparison-{}.json".format(stamp)
    )
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("PHASE8_B4_CROSS_MODE_REPORT=" + str(output))
    print("PHASE8_B4_CROSS_MODE_PARITY_PASS")


if __name__ == "__main__":
    main()
