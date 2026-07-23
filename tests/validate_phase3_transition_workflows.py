#!/usr/bin/env python3
"""Fast contracts for the Phase 3 routed full-workflow oracle."""

import ast
import copy
import hashlib
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import phase3_transition_workflow_recipe as recipe  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_value_error(action, required_text):
    try:
        action()
    except ValueError as error:
        assert required_text in str(error), str(error)
        return
    raise AssertionError("Expected ValueError containing {!r}".format(required_text))


def _fixture(workflow):
    result = {
        "schema_version": recipe.EXPECTED_SCHEMA_VERSIONS[workflow],
        "source_document": "/volatile/run/document.FCStd",
        "scenarios": [
            {
                "name": name,
                "semantic_sha256": "{}-semantic".format(index),
                "outcome": {"objects": 9 + index, "valid": True},
                "measurement": {
                    "wall_ms": 10.0 + index,
                    "rss_before_mb": 100.0,
                },
            }
            for index, name in enumerate(recipe.EXPECTED_SCENARIOS[workflow])
        ],
        "preference_store_restored": True,
    }
    history = {"undo_count": 3, "memory_bytes": 123456}
    if workflow == recipe.PLAIN_LINE_EDIT:
        result.update({
            "initial_history": copy.deepcopy(history),
            "post_replace_history": copy.deepcopy(history),
            "post_change_back_history": copy.deepcopy(history),
            "history_actions": [
                {
                    "name": name,
                    "before_history": copy.deepcopy(history),
                    "after_history": copy.deepcopy(history),
                    "semantic_sha256": "history-{}".format(index),
                    "measurement": {"wall_ms": 20.0 + index},
                }
                for index, name in enumerate(
                    recipe.EXPECTED_PLAIN_LINE_HISTORY_ACTIONS
                )
            ],
            "right_hand_save_reopen": {
                "path": "/volatile/run/document.FCStd",
                "history": copy.deepcopy(history),
                "measurement": {"wall_ms": 50.0},
                "semantic_sha256": "saved-semantic",
                "objects": 9,
            },
        })
    else:
        result.update({
            "initial_history": copy.deepcopy(history),
            "created_history": copy.deepcopy(history),
            "edited_history": copy.deepcopy(history),
            "history_cycles": [
                {
                    "before": copy.deepcopy(history),
                    "after_undo": copy.deepcopy(history),
                    "after_redo": copy.deepcopy(history),
                    "undo_semantic_sha256": "undo-{}".format(index),
                    "redo_semantic_sha256": "redo-{}".format(index),
                    "wall_ms": 30.0 + index,
                }
                for index in range(2)
            ],
            "save_reopen": {
                "path": "/volatile/run/document.FCStd",
                "history": copy.deepcopy(history),
                "wall_ms": 50.0,
                "semantic_sha256": "saved-semantic",
                "objects": 23,
            },
        })
    return result


def _change_volatile_fields(workflow, result):
    result["source_document"] = "/another/run/document.FCStd"
    for index, scenario in enumerate(result["scenarios"]):
        scenario["measurement"] = {
            "wall_ms": 500.0 + index,
            "rss_before_mb": 900.0,
        }
    if workflow == recipe.PLAIN_LINE_EDIT:
        for key in (
            "initial_history",
            "post_replace_history",
            "post_change_back_history",
        ):
            result[key]["memory_bytes"] += 1
        for action in result["history_actions"]:
            action["measurement"]["wall_ms"] += 100.0
            action["before_history"]["memory_bytes"] += 1
            action["after_history"]["memory_bytes"] += 1
        persistence = result["right_hand_save_reopen"]
        persistence["path"] = "/another/run/document.FCStd"
        persistence["measurement"]["wall_ms"] += 100.0
        persistence["history"]["memory_bytes"] += 1
    else:
        for key in ("initial_history", "created_history", "edited_history"):
            result[key]["memory_bytes"] += 1
        for cycle in result["history_cycles"]:
            cycle["wall_ms"] += 100.0
            for key in ("before", "after_undo", "after_redo"):
                cycle[key]["memory_bytes"] += 1
        persistence = result["save_reopen"]
        persistence["path"] = "/another/run/document.FCStd"
        persistence["wall_ms"] += 100.0
        persistence["history"]["memory_bytes"] += 1


def _validate_comparison_contract():
    for workflow in recipe.WORKFLOWS:
        legacy = _fixture(workflow)
        modular = copy.deepcopy(legacy)
        _change_volatile_fields(workflow, modular)
        comparison = recipe.compare_workflow_routes(
            workflow,
            legacy,
            modular,
        )
        assert comparison["equal"] is True
        assert comparison["difference_count"] == 0
        assert comparison["legacy_digest"] == comparison["successor_digest"]

        changed = copy.deepcopy(modular)
        changed["scenarios"][0]["outcome"]["objects"] += 1
        changed_comparison = recipe.compare_workflow_routes(
            workflow,
            legacy,
            changed,
        )
        assert changed_comparison["equal"] is False
        assert changed_comparison["difference_count"] == 1
        assert "objects" in changed_comparison["differences"][0]["path"]

        broken = copy.deepcopy(legacy)
        broken["preference_store_restored"] = False
        _expect_value_error(
            lambda: recipe.workflow_equivalence_contract(workflow, broken),
            "did not restore",
        )
        broken = copy.deepcopy(legacy)
        broken["scenarios"].reverse()
        _expect_value_error(
            lambda: recipe.workflow_equivalence_contract(workflow, broken),
            "scenario sequence drifted",
        )
        broken = copy.deepcopy(legacy)
        broken["scenarios"][0].pop("measurement")
        _expect_value_error(
            lambda: recipe.workflow_equivalence_contract(workflow, broken),
            "missing volatile field",
        )

    _expect_value_error(
        lambda: recipe.workflow_equivalence_contract("unknown", {}),
        "Unknown Phase 3 workflow",
    )
    assert recipe.VOLATILE_RECIPE_FIELDS == {
        "measurement",
        "memory_bytes",
        "path",
        "source_document",
        "wall_ms",
    }


def _validate_bridge_contract():
    for relative_path, expected_hash in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash

    bridge_root = ROOT / "tools" / "freecad_bridge"
    loader = bridge_root / "probes" / "load_phase3_transition_workflow.py"
    finisher = bridge_root / "probes" / "finish_phase3_transition_workflow.py"
    host = bridge_root / "run_phase3_transition_workflow.py"
    wrapper = bridge_root / "run-phase3-transition-workflow"
    series = bridge_root / "run_phase3_transition_workflow_series.py"
    series_wrapper = bridge_root / "run-phase3-transition-workflows"
    paths = (loader, finisher, host, series)
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in (host, wrapper, series, series_wrapper):
        assert path.is_file() and path.stat().st_mode & 0o111, path

    loader_text = loader.read_text(encoding="utf-8")
    finisher_text = finisher.read_text(encoding="utf-8")
    host_text = host.read_text(encoding="utf-8")
    series_text = series.read_text(encoding="utf-8")
    wrapper_text = wrapper.read_text(encoding="utf-8")
    assert "_load_foundation" in loader_text
    assert "require_qualified_runtime" in loader_text
    assert "_load_modular_transition_workflow" in loader_text
    assert "_PHASE3_PRODUCT_COMPOSITION" in loader_text
    assert "tools.phase3_transition_pilot" in loader_text
    assert "load_transition_pilot_session" in loader_text
    assert "_PHASE3_SESSION.apply_route(_PHASE3_ROUTE)" in loader_text
    assert "FOUNDATION_RESULT" in loader_text
    assert "sys.modules[_PHASE3_WORKFLOW_MODULE_NAME]" in loader_text
    assert "_PHASE3_BINDINGS_BEFORE" in loader_text
    assert 'TRACKTEMPLATE_BASE_MACRO_VERSION = "10.2A8A7B15"' in loader_text
    assert "TRACKTEMPLATE_ENFORCE_FROZEN_WORKFLOW_HASHES = False" in loader_text
    assert '("GeneratorVersion",)' in loader_text
    assert '"ProductionRecordIndexJSON"' in loader_text
    assert '"10.2A8A7B14"' in loader_text
    assert '"10.2A8A7B15"' in loader_text
    assert "binding_identity_preserved" in finisher_text
    assert "_PHASE3_SESSION.routing_record()" in finisher_text
    assert "_PHASE3_SESSION.apply_route(_PHASE3_ROUTE)" in finisher_text
    assert "run-isolated" in wrapper_text
    assert "shutil.copy2(base_path, document_path)" in host_text
    assert "source_fixture_sha256_after" in host_text
    assert "workflow_equivalence_contract" in host_text
    assert "performance_qualification" in host_text
    assert "subprocess.run" in series_text
    assert "compare_workflow_routes" in series_text
    assert "(LEGACY_ROUTE, MODULAR_ROUTE)" in series_text
    for workflow in recipe.WORKFLOWS:
        assert workflow in series_text or "WORKFLOWS" in series_text

    for driver_relative in recipe.DRIVER_PATHS.values():
        driver_path = ROOT / driver_relative
        driver_text = driver_path.read_text(encoding="utf-8")
        ast.parse(driver_text, filename=str(driver_path))
        assert "TRACKTEMPLATE_WORKFLOW_MODULE_NAME" in driver_text
        assert "TRACKTEMPLATE_CAPTURE_WORKFLOW_RESULT" in driver_text
        assert "TRACKTEMPLATE_WORKFLOW_RESULT = result" in driver_text

    report_path = (
        ROOT
        / "reference"
        / "benchmarks"
        / "2026-07-22-b16-transition-routed-workflow-parity.md"
    )
    report_text = report_path.read_text(encoding="utf-8")
    for required_evidence in (
        _sha256(ROOT / "tools/freecad_bridge/phase3_transition_workflow_recipe.py"),
        "85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0",
        "2eec8269c52b8491ac546650cad1c0c6975bc620ab3a4a845f4778d8a1379517",
        "fcff030d106b748eaa2887cd80810ed9b0b0393701e95d6827869e54df776532",
        "not the contracted Phase 3 performance profile",
    ):
        assert required_evidence in report_text

    phase3_text = (ROOT / "reference" / "PHASE3_TRANSITION_SLICE.md").read_text(
        encoding="utf-8"
    )
    project_plan_text = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(
        encoding="utf-8"
    )
    assert "Routed full-workflow and real-GUI evidence" in phase3_text
    assert "Applicable FreeCAD/headless, GUI and performance evidence | Evidenced" in (
        phase3_text
    )
    assert "Closeout acceptance and carried controls" in phase3_text
    assert "neither route was removed by the closeout" in phase3_text
    assert "Progress: `█████` — 5/5 exit conditions evidenced and accepted" in (
        project_plan_text
    )
    assert "Phase 3: first parity-proven vertical slice" in project_plan_text
    assert "Complete — all five technical exit conditions" in project_plan_text


def validate():
    _validate_comparison_contract()
    _validate_bridge_contract()
    print("Phase 3 transition full-workflow oracle validation passed")


if __name__ == "__main__":
    validate()
