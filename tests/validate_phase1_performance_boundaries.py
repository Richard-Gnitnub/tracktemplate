#!/usr/bin/env python3
"""Validate the Phase 1 performance-boundary and accounting contract."""

import copy
import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-performance-boundaries.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "7aa377fdc7e7e1174f5a4ad8da75ee612e9efa8b46f2dd7fb9f3b37976f6ae43"
)
SOURCE_EXPECTATIONS = {
    "b14": {
        "path": "AdvancedTurnout.FCMacro",
        "version_token": "10.2A8A7B14",
        "sha256": "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
        "role": "immutable legacy comparison oracle",
    },
    "b15": {
        "path": (
            "model_railway_curve_template_multitrack_v10_2a8a7b15_"
            "chair_performance_and_representation.FCMacro"
        ),
        "version_token": "10.2A8A7B15",
        "sha256": "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
        "role": "accepted behavioural reference",
    },
}
EVIDENCE_EXPECTATIONS = {
    "provisional-accumulated-crossover": (
        "reference/benchmarks/2026-07-19-b14-crossover-xo-001.md",
        "47591d38eac1636d7ab4d283291f0af3d10f912b025b3078bdae48fb66fe3382",
        "excluded-from-comparison",
    ),
    "b14-crossover-cold-series": (
        "reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md",
        "84dfa419bd608b524027cd78199bf0d9384b8b7a81ba83d687a53d88069a867b",
        "controlled-three-run-legacy-profile",
    ),
    "b14-crossover-warm-series": (
        "reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md",
        "a9e2120a5544c2d5682f916286b430f6a7d8ffbc28a8bb1de831e2e598b9c28b",
        "controlled-three-iteration-warm-diagnostic-profile",
    ),
    "b14-to-b15-chair-acceptance": (
        "reference/benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md",
        "45f76007e4fdda1b4c91785f84d18605bcae3c2375766cc371b6a441c856f8a6",
        "single-run-behavioural-acceptance-with-diagnostic-timings",
    ),
    "b14-plain-line-edit-series": (
        "reference/benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md",
        "f62f78955f32acbf1ae637c1064fc83f0a1a874c6f0e6171974b499c512f0aba",
        "controlled-three-run-legacy-profile",
    ),
    "b14-plain-line-selected-export-series": (
        "reference/benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md",
        "66818e6ceb9275ddd5f3bf4e5da4eda8cdda1f9011554d48b701bbde77037193",
        "controlled-three-run-legacy-profile",
    ),
    "b14-plain-line-create-export-series": (
        "reference/benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md",
        "e7d8e058ed923c6aa53e1ffd7abd061c81e75bc473c169c85326cc2899acb1b6",
        "controlled-three-run-legacy-profile",
    ),
    "b14-straight-station-series": (
        "reference/benchmarks/2026-07-20-b14-straight-station-workflow-series.md",
        "fbc57dce2c0ae7eab08b0f8447c878eeed39870f700756b6b5c897926e61ccb1",
        "controlled-three-run-legacy-profile",
    ),
    "b14-standalone-turnout-series": (
        "reference/benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md",
        "5c101cd96c0c55da4482fc270a2f1701fd6141c15479b197ac67526155f8d41d",
        "controlled-three-run-legacy-profile",
    ),
}
PROFILE_MEDIANS_MS = {
    "b14-crossover-cold-guided-sequence": 700818.0,
    "b14-crossover-warm-supported-solid-panel": 143581.0,
    "b14-plain-line-cold-edit": 2783.694,
    "b14-plain-line-cold-selected-export": 7885.73,
    "b14-plain-line-cold-create-through-export": 6907.971,
    "b14-connected-straight-cold-create": 2528.073,
    "b14-connected-straight-same-process-edit": 2078.244,
    "b14-standalone-turnout-cold-create": 1743.967,
    "b14-standalone-turnout-same-process-edit": 1977.051,
}
DEFECT_IDS = {
    "geometry-external-internal-boundary-gap",
    "premature-chair-timing-persistence",
    "late-supported-solid-reuse-check",
    "redundant-post-reuse-panel-refresh",
    "repeated-effective-status-signature-scans",
}
TARGET_SLOT_IDS = {
    "lightweight-routine-edit-without-export",
    "explicit-validate-deferred-exact-geometry",
    "production-export-from-validated-state",
    "complete-edit-validate-export",
}
SPAN_CLASSES = {
    "operator-action",
    "nested-component",
    "harness-enclosing",
    "same-process-correctness",
    "missing-target-boundary",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "recorded_on",
    "status",
    "phase",
    "scope",
    "source_state",
    "accounting_policy",
    "evidence_reports",
    "profiles",
    "observed_instrumentation_defects",
    "target_pipeline_slots",
    "phase1_gate",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _record_map(records, identity, label, errors):
    result = {}
    if not isinstance(records, list):
        errors.append("{} must be a list".format(label))
        return result
    for record in records:
        if not isinstance(record, dict) or not _non_empty_text(record.get(identity)):
            errors.append("{} contains an invalid identity".format(label))
            continue
        key = record[identity]
        if key in result:
            errors.append("{} contains duplicate {}".format(label, key))
        result[key] = record
    return result


def validate_contract(document):
    errors = []
    if not isinstance(document, dict):
        return ["performance contract must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("performance contract top-level fields are invalid")
    exact_root = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:performance-boundaries:1",
        "recorded_on": "2026-07-21",
        "status": "phase1-legacy-boundaries-reconciled-target-pipeline-unmeasured",
        "phase": 1,
    }
    for field, expected in exact_root.items():
        if document.get(field) != expected:
            errors.append("performance {} is invalid".format(field))

    scope = document.get("scope")
    if not isinstance(scope, dict) or set(scope) != {
        "purpose",
        "current_effect",
        "bounded_claim",
        "terminology",
    }:
        errors.append("performance scope fields are invalid")
    elif not all(_non_empty_text(value) for value in scope.values()):
        errors.append("performance scope contains empty text")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or set(source_state) != set(
        SOURCE_EXPECTATIONS
    ):
        errors.append("performance source_state must contain exact B14/B15 records")
    else:
        for source_id, expected in SOURCE_EXPECTATIONS.items():
            if source_state.get(source_id) != expected:
                errors.append("{} source record is invalid".format(source_id))

    policy = document.get("accounting_policy")
    required_policy_fields = {
        "clock",
        "span_classes",
        "reconciliation_rule",
        "nesting_rule",
        "harness_rule",
        "cache_rule",
        "persistence_rule",
        "budget_rule",
    }
    if not isinstance(policy, dict) or set(policy) != required_policy_fields:
        errors.append("performance accounting policy fields are invalid")
    else:
        if set(policy.get("span_classes") or []) != SPAN_CLASSES:
            errors.append("performance span classes are invalid")
        for field in required_policy_fields - {"span_classes"}:
            if not _non_empty_text(policy.get(field)):
                errors.append("performance policy {} is empty".format(field))
        if "within each individual run" not in policy.get(
            "reconciliation_rule", ""
        ):
            errors.append("performance reconciliation is not per-run")
        if "Never subtract or add independently selected medians" not in policy.get(
            "reconciliation_rule", ""
        ):
            errors.append("performance policy permits median arithmetic")

    evidence = document.get("evidence_reports")
    if not isinstance(evidence, dict) or set(evidence) != set(EVIDENCE_EXPECTATIONS):
        errors.append("performance evidence report set is invalid")
        evidence = evidence if isinstance(evidence, dict) else {}
    for evidence_id, (path, digest, status) in EVIDENCE_EXPECTATIONS.items():
        record = evidence.get(evidence_id)
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "status",
            "required_markers",
        }:
            errors.append("{} evidence fields are invalid".format(evidence_id))
            continue
        if (record.get("path"), record.get("sha256"), record.get("status")) != (
            path,
            digest,
            status,
        ):
            errors.append("{} evidence identity is invalid".format(evidence_id))
        markers = record.get("required_markers")
        if not isinstance(markers, list) or not markers or not all(
            _non_empty_text(marker) for marker in markers
        ):
            errors.append("{} evidence markers are invalid".format(evidence_id))

    profiles = _record_map(
        document.get("profiles"), "profile_id", "performance profiles", errors
    )
    if set(profiles) != set(PROFILE_MEDIANS_MS):
        errors.append("performance profile set is invalid")
    required_profile_fields = {
        "profile_id",
        "workflow_families",
        "source",
        "evidence_report",
        "measurement_state",
        "sample_count",
        "primary_boundary",
        "related_spans",
        "reconciliation",
        "decision_use",
        "dominant_cost_finding",
        "gaps",
    }
    for profile_id, expected_median in PROFILE_MEDIANS_MS.items():
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            continue
        if set(profile) != required_profile_fields:
            errors.append("{} profile fields are invalid".format(profile_id))
            continue
        if profile.get("source") not in SOURCE_EXPECTATIONS:
            errors.append("{} has an unknown source".format(profile_id))
        if profile.get("evidence_report") not in evidence:
            errors.append("{} has an unknown evidence report".format(profile_id))
        if profile.get("sample_count") != 3:
            errors.append("{} must retain three observations".format(profile_id))
        if not isinstance(profile.get("workflow_families"), list) or not profile.get(
            "workflow_families"
        ):
            errors.append("{} has no workflow family".format(profile_id))
        if not _non_empty_text(profile.get("measurement_state")):
            errors.append("{} has no measurement state".format(profile_id))

        primary = profile.get("primary_boundary")
        if not isinstance(primary, dict) or set(primary) != {
            "span_id",
            "span_class",
            "median_ms",
            "includes",
            "excludes",
        }:
            errors.append("{} primary boundary fields are invalid".format(profile_id))
        else:
            if primary.get("span_class") not in {
                "operator-action",
                "harness-enclosing",
            }:
                errors.append("{} primary span class is invalid".format(profile_id))
            if primary.get("median_ms") != expected_median:
                errors.append("{} primary median drifted".format(profile_id))
            for field in ("includes", "excludes"):
                if not isinstance(primary.get(field), list) or not primary.get(field):
                    errors.append("{} primary {} is empty".format(profile_id, field))

        related = profile.get("related_spans")
        if not isinstance(related, list):
            errors.append("{} related_spans is invalid".format(profile_id))
        else:
            span_ids = set()
            for span in related:
                if not isinstance(span, dict) or set(span) != {
                    "span_id",
                    "span_class",
                    "median_ms",
                    "relationship_to_primary",
                    "add_to_primary",
                }:
                    errors.append("{} has invalid related span fields".format(profile_id))
                    continue
                span_id = span.get("span_id")
                if not _non_empty_text(span_id) or span_id in span_ids:
                    errors.append("{} has duplicate/empty related span".format(profile_id))
                span_ids.add(span_id)
                if span.get("span_class") not in {
                    "nested-component",
                    "harness-enclosing",
                    "same-process-correctness",
                }:
                    errors.append("{} has invalid related span class".format(profile_id))
                if not isinstance(span.get("median_ms"), (int, float)) or span.get(
                    "median_ms", 0
                ) <= 0:
                    errors.append("{} has invalid related span median".format(profile_id))
                if span.get("add_to_primary") is not False:
                    errors.append("{} permits double-counting a related span".format(profile_id))
                if not _non_empty_text(span.get("relationship_to_primary")):
                    errors.append("{} has an unexplained related span".format(profile_id))

        reconciliation = profile.get("reconciliation")
        if not isinstance(reconciliation, dict) or set(reconciliation) != {
            "status",
            "method",
            "uncovered_time_reported",
        }:
            errors.append("{} reconciliation fields are invalid".format(profile_id))
        elif not _non_empty_text(reconciliation.get("method")):
            errors.append("{} reconciliation method is empty".format(profile_id))

        decision = profile.get("decision_use")
        if not isinstance(decision, dict) or set(decision) != {
            "legacy_boundary_comparison",
            "dominant_cost_context",
            "optimization_selection",
            "human_use_budget",
        }:
            errors.append("{} decision-use fields are invalid".format(profile_id))
        elif decision.get("optimization_selection") is not False or decision.get(
            "human_use_budget"
        ) is not False:
            errors.append("{} improperly authorises optimisation/budget use".format(profile_id))
        if not _non_empty_text(profile.get("dominant_cost_finding")):
            errors.append("{} has no measured-cost interpretation".format(profile_id))
        if not isinstance(profile.get("gaps"), list) or not profile.get("gaps"):
            errors.append("{} has no explicit coverage gap".format(profile_id))

    defects = _record_map(
        document.get("observed_instrumentation_defects"),
        "defect_id",
        "instrumentation defects",
        errors,
    )
    if set(defects) != DEFECT_IDS:
        errors.append("instrumentation defect set is invalid")
    required_defect_fields = {
        "defect_id",
        "status",
        "blocks_optimization_selection_from_inner_profile",
        "safe_current_use",
        "evidence_reports",
        "source_anchors",
        "required_fix_evidence",
    }
    for defect_id, defect in defects.items():
        if set(defect) != required_defect_fields:
            errors.append("{} defect fields are invalid".format(defect_id))
            continue
        if defect.get("status") != "bounded-not-fixed":
            errors.append("{} is not truthfully bounded/not fixed".format(defect_id))
        if defect.get("blocks_optimization_selection_from_inner_profile") is not True:
            errors.append("{} no longer blocks unsafe inner-profile use".format(defect_id))
        for field in ("safe_current_use", "required_fix_evidence"):
            if not _non_empty_text(defect.get(field)):
                errors.append("{} {} is empty".format(defect_id, field))
        cited = defect.get("evidence_reports")
        if not isinstance(cited, list) or not cited or not set(cited) <= set(evidence):
            errors.append("{} cites invalid evidence".format(defect_id))
        anchors = defect.get("source_anchors")
        if not isinstance(anchors, list) or not anchors:
            errors.append("{} has no source anchors".format(defect_id))
        else:
            for anchor in anchors:
                if not isinstance(anchor, dict) or set(anchor) != {"path", "contains"}:
                    errors.append("{} has invalid source anchor fields".format(defect_id))
                elif not all(_non_empty_text(anchor.get(key)) for key in anchor):
                    errors.append("{} has an empty source anchor".format(defect_id))

    slots = _record_map(
        document.get("target_pipeline_slots"),
        "slot_id",
        "target pipeline slots",
        errors,
    )
    if set(slots) != TARGET_SLOT_IDS:
        errors.append("target pipeline slot set is invalid")
    required_slot_fields = {
        "slot_id",
        "status",
        "span_class",
        "required_boundary",
        "required_metrics",
        "legacy_context_profiles",
        "owner_gate",
    }
    for slot_id, slot in slots.items():
        if set(slot) != required_slot_fields:
            errors.append("{} target slot fields are invalid".format(slot_id))
            continue
        if slot.get("status") != "not-implemented-unmeasured":
            errors.append("{} target slot invents implementation/evidence".format(slot_id))
        if slot.get("span_class") != "missing-target-boundary":
            errors.append("{} target slot has the wrong span class".format(slot_id))
        for field in ("required_boundary", "owner_gate"):
            if not _non_empty_text(slot.get(field)):
                errors.append("{} {} is empty".format(slot_id, field))
        metrics = slot.get("required_metrics")
        if not isinstance(metrics, list) or len(metrics) < 3 or not all(
            _non_empty_text(item) for item in metrics
        ):
            errors.append("{} target metrics are incomplete".format(slot_id))
        context = slot.get("legacy_context_profiles")
        if not isinstance(context, list) or not context or not set(context) <= set(
            profiles
        ):
            errors.append("{} target context profiles are invalid".format(slot_id))

    gate = document.get("phase1_gate")
    if not isinstance(gate, dict) or set(gate) != {
        "result",
        "closed_by_this_contract",
        "still_open",
    }:
        errors.append("performance Phase 1 gate fields are invalid")
    else:
        if gate.get("result") != (
            "bounded-performance-inventory-accepted-target-pipeline-unmeasured"
        ):
            errors.append("accepted performance gate status drifted")
        for field in ("closed_by_this_contract", "still_open"):
            if not isinstance(gate.get(field), list) or not gate.get(field):
                errors.append("performance gate {} is empty".format(field))
    return errors


def validate_files(document):
    errors = []
    for source_id, expected in SOURCE_EXPECTATIONS.items():
        path = ROOT / expected["path"]
        if not path.is_file():
            errors.append("missing {} source {}".format(source_id, expected["path"]))
            continue
        if _sha256(path) != expected["sha256"]:
            errors.append("{} source fingerprint drifted".format(source_id))
        if expected["version_token"] not in path.read_text(encoding="utf-8"):
            errors.append("{} source version token is missing".format(source_id))

    evidence = document.get("evidence_reports") or {}
    for evidence_id, (relative, digest, _status) in EVIDENCE_EXPECTATIONS.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append("missing evidence report {}".format(relative))
            continue
        if _sha256(path) != digest:
            errors.append("{} evidence report fingerprint drifted".format(evidence_id))
            continue
        text = path.read_text(encoding="utf-8")
        for marker in (evidence.get(evidence_id) or {}).get("required_markers", []):
            if marker not in text:
                errors.append("{} evidence marker is missing: {}".format(evidence_id, marker))

    for defect in document.get("observed_instrumentation_defects") or []:
        defect_id = defect.get("defect_id", "unknown")
        for anchor in defect.get("source_anchors") or []:
            path = ROOT / str(anchor.get("path") or "")
            if not path.is_file():
                errors.append("{} source anchor path is missing".format(defect_id))
                continue
            if str(anchor.get("contains") or "") not in path.read_text(
                encoding="utf-8"
            ):
                errors.append("{} source anchor drifted".format(defect_id))

    b14 = (ROOT / SOURCE_EXPECTATIONS["b14"]["path"]).read_text(encoding="utf-8")
    analysis_start = b14.index(
        "def analyse_entity_chair_positions(doc, entity_kind, entity_id, settings=None):"
    )
    analysis_end = b14.index("def chair_analysis_summary", analysis_start)
    analysis = b14[analysis_start:analysis_end]
    timing_write = analysis.index('result["performance_timings_ms"] = dict(timings)')
    metadata_write = analysis.index("updated = _chair_write_metadata")
    commit_timing = analysis.index('timings["transaction_commit"]')
    final_timing = analysis.rindex('result["performance_timings_ms"] = timings')
    if not timing_write < metadata_write < commit_timing < final_timing:
        errors.append("premature chair-timing source ordering no longer matches contract")

    solid_start = b14.index(
        "def generate_supported_chair_solids(doc, entity_kind, entity_id, settings=None):"
    )
    solid_end = b14.index("def validate_generated_chair_solids", solid_start)
    solid = b14[solid_start:solid_end]
    plan_build = solid.index("plan = _chair_build_solid_plan")
    existing_lookup = solid.index("existing = _chair_solid_object")
    if not plan_build < existing_lookup:
        errors.append("supported-solid reuse ordering no longer matches contract")
    return errors


def validate_mutation_guards(document):
    mutations = []

    changed = copy.deepcopy(document)
    changed["profiles"][0]["related_spans"][0]["add_to_primary"] = True
    mutations.append(("nested double-count", changed))

    changed = copy.deepcopy(document)
    changed["profiles"][1]["decision_use"]["human_use_budget"] = True
    mutations.append(("invented human-use budget", changed))

    changed = copy.deepcopy(document)
    changed["observed_instrumentation_defects"][0]["status"] = "fixed"
    mutations.append(("unsupported defect closure", changed))

    changed = copy.deepcopy(document)
    changed["target_pipeline_slots"][0]["status"] = "measured"
    mutations.append(("invented target measurement", changed))

    changed = copy.deepcopy(document)
    changed["evidence_reports"]["b14-crossover-cold-series"]["sha256"] = "0" * 64
    mutations.append(("evidence hash drift", changed))

    errors = []
    for label, mutation in mutations:
        if not validate_contract(mutation):
            errors.append("mutation guard did not reject {}".format(label))
    return errors


def main():
    if not CONTRACT_PATH.is_file():
        raise SystemExit("Phase 1 performance contract is missing")
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        raise SystemExit("Phase 1 performance contract fingerprint drifted")
    try:
        document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SystemExit("Could not parse Phase 1 performance contract: {}".format(error))
    errors = []
    errors.extend(validate_contract(document))
    errors.extend(validate_files(document))
    errors.extend(validate_mutation_guards(document))
    if errors:
        raise SystemExit("\n".join("- {}".format(error) for error in errors))
    print("Phase 1 performance-boundary contract checks passed")


if __name__ == "__main__":
    main()
