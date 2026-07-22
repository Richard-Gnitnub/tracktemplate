#!/usr/bin/env python3
"""Validate the accepted Phase 1 closeout and bounded Phase 2 authority."""

import collections
import copy
import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_dependency_manifest as manifest_validator  # noqa: E402


CLOSEOUT_PATH = ROOT / "reference" / "PHASE1_CLOSEOUT.md"
PROJECT_PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
SOURCE_EXPECTATIONS = {
    "b14": (
        "AdvancedTurnout.FCMacro",
        "10.2A8A7B14",
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    ),
    "b15": (
        (
            "model_railway_curve_template_multitrack_v10_2a8a7b15_"
            "chair_performance_and_representation.FCMacro"
        ),
        "10.2A8A7B15",
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
    ),
}
DECISION_STATES = {
    "P1-01": "accepted",
    "P1-02": "accepted",
    "P1-03": "accepted",
    "P1-04": "accepted",
    "P1-05": "accepted",
    "P1-06": "accepted",
    "P1-07": "accepted",
    "P1-08": "accepted",
    "P1-09": "accepted",
    "P1-10": "accepted",
}
PERFORMANCE_DEFECTS = (
    "geometry-external-internal-boundary-gap",
    "premature-chair-timing-persistence",
    "late-supported-solid-reuse-check",
    "redundant-post-reuse-panel-refresh",
    "repeated-effective-status-signature-scans",
)
TARGET_SLOTS = (
    "lightweight-routine-edit-without-export",
    "explicit-validate-deferred-exact-geometry",
    "production-export-from-validated-state",
    "complete-edit-validate-export",
)
DEFERRAL_IDS = tuple("P1-X{:02d}".format(number) for number in range(1, 11))
REQUIRED_MARKERS = (
    "Status: **Accepted and closed by the project owner on 2026-07-22.",
    "Phase 2 is\ncurrent under the bounded foundation authority recorded here.**",
    "6f49d6570072926f7e416893bb6d07cee0071733",
    "B15 FreeCAD 1.1 headless smoke test passed",
    "14 workflows, 12 bounded-executed, two defined-blocked and 14 scheduled open gaps",
    "FreeCADCmd/headless layer topology is not evidence for real-GUI visibility",
    "No legacy timing becomes a human-use budget.",
    "These are controlled deferrals, not silent exceptions.",
    "Control and documentation volume can duplicate truth, become stale",
    "Phase 2 maintainability/reuse review and every later phase closeout",
    "controls whose cost exceeds their continuing purpose",
    "S1-07 through S1-15 remain blocked",
    "six open reviews have Phase 8 or Phase",
    "Phase 2 is not authorised to move the selected calculation implementation",
    "Accepted explicitly by the project owner on 2026-07-22",
    "> I accept PHASE1_CLOSEOUT.md, including P1-01 through P1-10.",
    "This instruction is the phase-transition authority.",
)
REQUIRED_PROJECT_PLAN_MARKERS = (
    "Progress: `█████████` — 9/9 exit conditions evidenced and accepted.",
    "| 1 | Product, dependency, correctness, and performance inventory | `█████████` — 9/9 evidenced | Complete — accepted 2026-07-22 |",
    "| M2 — Migration blueprint locked",
    "| 1 | Complete — accepted 2026-07-22 |",
    "PHASE1_CLOSEOUT.md",
)


def _read_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _decision_rows(text, errors):
    start = text.find("## Closeout decision register")
    finish = text.find("## Acceptance record", start + 1)
    if start < 0 or finish < 0:
        errors.append("closeout decision-register boundary is missing")
        return []
    rows = []
    for line in text[start:finish].splitlines():
        if not line.startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) == 4 and cells[0] not in {"ID", "---"}:
            rows.append(cells)
    return rows


def _deferral_rows(text, errors):
    start = text.find("## Legacy defects and explicit deferrals")
    finish = text.find("## S1, provenance and rights boundary", start + 1)
    if start < 0 or finish < 0:
        errors.append("closeout deferral-register boundary is missing")
        return []
    rows = []
    for line in text[start:finish].splitlines():
        if not line.startswith("| P1-X"):
            continue
        cells = _table_cells(line)
        if len(cells) == 4:
            rows.append(cells)
    return rows


def _s1_decisions(text):
    rows = {}
    for line in text.splitlines():
        if not line.startswith("| S1-"):
            continue
        cells = _table_cells(line)
        if len(cells) == 5:
            rows[cells[0]] = cells[2]
    return rows


def validate_closeout(data, check_repository=True):
    errors = []
    closeout_text = data["closeout_text"]
    project_plan_text = data["project_plan_text"]

    for marker in REQUIRED_MARKERS:
        if marker not in closeout_text:
            errors.append("closeout marker is missing: {}".format(marker))
    if "No acceptance is recorded yet." in closeout_text:
        errors.append("accepted closeout still claims that acceptance is absent")

    rows = _decision_rows(closeout_text, errors)
    row_ids = [row[0] for row in rows]
    if row_ids != list(DECISION_STATES):
        errors.append("closeout decision identity/order set is invalid")
    if len(row_ids) != len(set(row_ids)):
        errors.append("closeout decision identities are duplicated")
    for row in rows:
        if not all(row):
            errors.append("closeout decision contains an empty cell")
            continue
        if row[2] != DECISION_STATES.get(row[0]):
            errors.append("{} state drifted".format(row[0]))

    deferral_rows = _deferral_rows(closeout_text, errors)
    deferral_ids = [row[0] for row in deferral_rows]
    if tuple(deferral_ids) != DEFERRAL_IDS:
        errors.append("closeout deferral identity/order set is invalid")
    if len(deferral_ids) != len(set(deferral_ids)):
        errors.append("closeout deferral identities are duplicated")
    if any(not all(row) for row in deferral_rows):
        errors.append("closeout deferral contains an empty cell")

    for marker in REQUIRED_PROJECT_PLAN_MARKERS:
        if marker not in project_plan_text:
            errors.append("project-plan closeout marker is missing: {}".format(marker))

    workflow = data["workflow"]
    gate = workflow.get("phase1_gate") or {}
    workflows = workflow.get("workflows") or []
    states = collections.Counter(
        (item.get("oracle") or {}).get("state")
        for item in workflows
        if isinstance(item, dict)
    )
    if workflow.get("status") != (
        "all-release-critical-workflows-owned-oracle-defined-gaps-scheduled"
    ):
        errors.append("workflow coverage status drifted")
    if (
        len(workflows) != 14
        or states != {"bounded-executed": 12, "defined-blocked": 2}
        or gate.get("assessment") != "evidenced"
        or gate.get("open_gap_count") != 14
    ):
        errors.append("workflow closeout counts or gate drifted")
    for item in workflows:
        gap = item.get("gap_control") or {}
        if not gap.get("summary") or not gap.get("owner_role") or not gap.get(
            "closure_phases"
        ) or not gap.get("closure_gate"):
            errors.append("a workflow gap lost its owner or closure gate")

    performance = data["performance"]
    defects = performance.get("observed_instrumentation_defects") or []
    slots = performance.get("target_pipeline_slots") or []
    if performance.get("status") != (
        "phase1-legacy-boundaries-reconciled-target-pipeline-unmeasured"
    ):
        errors.append("performance boundary status drifted")
    if tuple(item.get("defect_id") for item in defects) != PERFORMANCE_DEFECTS:
        errors.append("performance defect identity/order set drifted")
    if any(
        item.get("status") != "bounded-not-fixed"
        or item.get("blocks_optimization_selection_from_inner_profile") is not True
        for item in defects
    ):
        errors.append("a performance defect was weakened or promoted")
    if tuple(item.get("slot_id") for item in slots) != TARGET_SLOTS:
        errors.append("target performance slot identity/order set drifted")
    if any(item.get("status") != "not-implemented-unmeasured" for item in slots):
        errors.append("a target performance slot was populated without evidence")
    performance_gate = performance.get("phase1_gate") or {}
    if performance_gate.get("result") != (
        "bounded-performance-inventory-accepted-target-pipeline-unmeasured"
    ):
        errors.append("performance Phase 1 gate drifted")
    if not any(
        "Preserve all four unmeasured target slots" in item
        and "after the accepted 2026-07-22 Phase 1 closeout" in item
        for item in performance_gate.get("still_open") or []
    ):
        errors.append("accepted performance later-gate obligation is missing")

    compatibility = data["compatibility"]
    runtime = compatibility.get("runtime_baseline") or {}
    profiles = runtime.get("qualified_profiles") or []
    if compatibility.get("status") != (
        "phase1-policy-accepted-phase2-development-guard-implemented-"
        "broader-qualification-not-started"
    ):
        errors.append("compatibility contract status drifted")
    if len(profiles) != 1 or profiles[0].get("profile_id") != (
        "linux-x86_64-flatpak-freecad-1.1.1"
    ) or profiles[0].get("status") != "qualified-reference-and-initial-rc-profile":
        errors.append("qualified runtime profile set drifted")
    expected_platforms = [
        ("Linux x86_64 stable org.freecad.FreeCAD Flatpak", "qualified"),
        ("Other Linux packages or architectures", "qualification-pending"),
        ("Windows", "qualification-pending"),
        ("macOS", "qualification-pending"),
    ]
    actual_platforms = [
        (item.get("platform"), item.get("status"))
        for item in runtime.get("platform_matrix") or []
    ]
    if actual_platforms != expected_platforms:
        errors.append("platform qualification matrix drifted")
    ingress = compatibility.get("legacy_document_window") or {}
    if (
        ingress.get("current_implementation_status")
        != "contract-only-no-successor-document-detector-or-migrator-exists"
        or ingress.get("supported_ingress_versions")
        != ["10.2A8A7B14", "10.2A8A7B15"]
        or ingress.get("accepted_version_sets")
        != [
            ["10.2A8A7B14"],
            ["10.2A8A7B15"],
            ["10.2A8A7B14", "10.2A8A7B15"],
        ]
    ):
        errors.append("legacy document ingress boundary drifted")

    transition = data["transition"]
    selection = transition.get("selection") or {}
    successor = transition.get("successor") or {}
    if (
        transition.get("status") != "selected-owner-accepted-contract-frozen"
        or selection.get("candidate_id") != "transition_length_solver"
        or selection.get("owner_accepted_on") != "2026-07-20"
        or successor.get("development_checkpoint_id") != "10.2A8A7B16"
        or successor.get("compatibility_launcher_path") != "TrackTemplate.FCMacro"
        or successor.get("compatibility_launcher_status")
        != "reserved-b16-migration-composition-root"
        or successor.get("authoritative_package") != "tracktemplate"
    ):
        errors.append("selected transition-pilot boundary drifted")
    implementation_gates = transition.get("implementation_gates") or []
    if not any(
        "Route all three external callers together" in item
        and "contracted rollback switch" in item
        for item in implementation_gates
    ) or not any(
        "Do not change B14 or B15" in item
        for item in implementation_gates
    ):
        errors.append("selected transition-pilot implementation gates drifted")

    manifest = data["manifest"]
    manifest_errors = manifest_validator.validate_document(manifest)
    errors.extend("S1 manifest: {}".format(item) for item in manifest_errors)
    strict_errors = manifest_validator.validate_document(
        manifest, require_project_cleared=True
    )
    if not any("rather than project-cleared" in item for item in strict_errors):
        errors.append("S1 manifest no longer fails the project-cleared gate")
    if (
        (manifest.get("subject") or {}).get("version") != "0-unresolved"
        or (manifest.get("subject") or {}).get("package_license") != "NOASSERTION"
        or (manifest.get("project_status") or {}).get("status") != "unknown"
    ):
        errors.append("S1 package was promoted during Phase 1 closeout")
    s1_decisions = _s1_decisions(data["s1_plan_text"])
    if any(
        s1_decisions.get("S1-{:02d}".format(number))
        not in {"owner-decision-required", "blocked-evidence"}
        for number in range(7, 16)
    ):
        errors.append("an S1-07 through S1-15 blocker was promoted")

    for name in ("s1_lineage", "other_lineage"):
        lineage = data[name]
        if lineage.get("status") != "blocked" or any(
            scope.get("status") != "blocked" for scope in lineage.get("scopes") or []
        ):
            errors.append("{} was promoted during closeout".format(name))
    oracle = data["oracle"]
    if (
        oracle.get("status") != "blocked"
        or oracle.get("permitted_role") != "local comparison oracle only"
        or len(oracle.get("blockers") or []) != 4
        or any(item.get("status") != "open" for item in oracle.get("blockers") or [])
        or (oracle.get("acceptance_gate") or {}).get("canonical_production_input")
        is not False
    ):
        errors.append("Templot S1 oracle boundary was weakened")

    terminology = data["terminology"]
    term_states = collections.Counter(
        item.get("state") for item in terminology.get("terms") or []
    )
    if (
        terminology.get("status")
        != "accepted-at-phase1-closeout-open-reviews-scheduled"
        or term_states
        != {
            "accepted": 6,
            "provisional": 1,
            "review-required": 5,
            "frozen-legacy": 1,
        }
        or len(terminology.get("open_reviews") or []) != 6
        or any(
            item.get("state") != "open"
            for item in terminology.get("open_reviews") or []
        )
        or (terminology.get("phase1_gate") or {}).get("status")
        != "accepted-at-phase1-closeout"
    ):
        errors.append("terminology closeout boundary drifted")
    if not any(
        "does not resolve or waive any of the six named later reviews" in item
        for item in (terminology.get("phase1_gate") or {}).get("not_claimed") or []
    ):
        errors.append("terminology later-review obligation is missing")

    if check_repository:
        for source_key, (relative_path, version, digest) in SOURCE_EXPECTATIONS.items():
            path = ROOT / relative_path
            if _sha256(path) != digest:
                errors.append("{} source fingerprint changed".format(source_key))
            if version not in path.read_text(encoding="utf-8"):
                errors.append("{} version token is missing".format(source_key))
    return errors


def _load_data():
    return {
        "closeout_text": CLOSEOUT_PATH.read_text(encoding="utf-8"),
        "project_plan_text": PROJECT_PLAN_PATH.read_text(encoding="utf-8"),
        "workflow": _read_json("reference/contracts/phase1-workflow-coverage.json"),
        "performance": _read_json(
            "reference/contracts/phase1-performance-boundaries.json"
        ),
        "compatibility": _read_json("reference/contracts/phase1-compatibility.json"),
        "transition": _read_json("reference/contracts/phase1-transition-pilot.json"),
        "manifest": _read_json(
            "reference/manifests/s1-chair-pilot.dependency-manifest.json"
        ),
        "s1_plan_text": (ROOT / "reference" / "S1_PILOT_PLAN.md").read_text(
            encoding="utf-8"
        ),
        "s1_lineage": _read_json("reference/lineage/phase1-s1-core-lineage.json"),
        "other_lineage": _read_json(
            "reference/lineage/phase1-other-snc-legacy-lineage.json"
        ),
        "oracle": _read_json("reference/oracles/templot5-556b-s1-oracle.json"),
        "terminology": _read_json(
            "reference/contracts/phase1-terminology-assurance.json"
        ),
    }


def _expect_invalid(data, label):
    if not validate_closeout(data, check_repository=False):
        raise AssertionError("mutation unexpectedly passed: {}".format(label))


def main():
    data = _load_data()
    errors = validate_closeout(data)
    if errors:
        raise AssertionError("\n".join(errors))

    downgraded_decision = copy.deepcopy(data)
    downgraded_decision["closeout_text"] = downgraded_decision[
        "closeout_text"
    ].replace(
        "| P1-10 | Phase transition | accepted |",
        "| P1-10 | Phase transition | owner-decision-required |",
        1,
    )
    _expect_invalid(downgraded_decision, "lost phase acceptance")

    broadened_host = copy.deepcopy(data)
    broadened_host["compatibility"]["runtime_baseline"]["platform_matrix"][2][
        "status"
    ] = "qualified"
    _expect_invalid(broadened_host, "unsupported Windows qualification")

    measured_target = copy.deepcopy(data)
    measured_target["performance"]["target_pipeline_slots"][0][
        "status"
    ] = "measured"
    _expect_invalid(measured_target, "unmeasured target promotion")

    cleared_s1 = copy.deepcopy(data)
    cleared_s1["manifest"]["project_status"]["status"] = "project-cleared"
    _expect_invalid(cleared_s1, "premature S1 clearance")

    missing_review = copy.deepcopy(data)
    missing_review["terminology"]["open_reviews"].pop()
    _expect_invalid(missing_review, "missing terminology review")

    missing_bloat_control = copy.deepcopy(data)
    missing_bloat_control["closeout_text"] = re.sub(
        r"^\| P1-X10 .*$\n?",
        "",
        missing_bloat_control["closeout_text"],
        count=1,
        flags=re.MULTILINE,
    )
    _expect_invalid(missing_bloat_control, "missing control-bloat deferral")

    reopened_plan = copy.deepcopy(data)
    reopened_plan["project_plan_text"] = reopened_plan["project_plan_text"].replace(
        "Progress: `█████████` — 9/9 exit conditions evidenced and accepted.",
        "Progress: `████████▒` — 8/9 exit conditions evidenced; 1 remains active.",
        1,
    )
    _expect_invalid(reopened_plan, "unrecorded project-plan reopening")

    print("Accepted Phase 1 closeout validation passed")


if __name__ == "__main__":
    main()
