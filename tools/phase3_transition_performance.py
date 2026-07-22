#!/usr/bin/env python3
"""Profile the Phase 3 transition pilot without treating it as optimisation."""

import argparse
import ast
import datetime
import gc
import hashlib
import itertools
import json
import math
import os
import pathlib
import platform
import statistics
import subprocess
import sys
import time


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase3-transition-workflow-runs"
)
CONTRACT_PATH = (
    PROJECT_ROOT / "reference" / "contracts" / "phase1-transition-pilot.json"
)
B14_PATH = PROJECT_ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = PROJECT_ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
DOMAIN_PATH = PROJECT_ROOT / "tracktemplate" / "domain" / "alignment.py"
FUNCTION_NAMES = (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)

sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge.orchestration import sha256  # noqa: E402
from tools.freecad_bridge.phase3_transition_workflow_recipe import (  # noqa: E402
    CONNECTED_STRAIGHT,
    LEGACY_ROUTE,
    MODULAR_ROUTE,
    PLAIN_LINE_EDIT,
    ROUTES,
    WORKFLOWS,
    compare_workflow_routes,
)
from tools.semantic_compare import semantic_digest  # noqa: E402
from tracktemplate import api as modular_api  # noqa: E402


DEFAULT_CALCULATION_REPETITIONS = 9
DEFAULT_WORKFLOW_REPETITIONS = 3

PROFILED_ACTIONS = {
    PLAIN_LINE_EDIT: (
        {
            "scenario": "replace_left_with_right",
            "span_class": "operator_action",
            "starting_state": "fresh process and copied fixed left-hand fixture",
        },
        {
            "scenario": "change_right_back_to_left",
            "span_class": "same_process_correctness",
            "starting_state": "successful right-hand replacement in the same process",
        },
    ),
    CONNECTED_STRAIGHT: (
        {
            "scenario": "create_controlled_connected_pair",
            "span_class": "operator_action",
            "starting_state": "fresh process and copied fixed plain-line fixture",
        },
        {
            "scenario": "edit_connected_pair_lengths",
            "span_class": "same_process_correctness",
            "starting_state": "successful connected-pair creation in the same process",
        },
    ),
}

MEASUREMENT_FIELDS = (
    "wall_ms",
    "process_cpu_ms",
    "rss_delta_mb",
    "object_delta",
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _function(tree, name):
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(matches) != 1:
        raise ValueError("Expected one top-level {!r} definition".format(name))
    return matches[0]


def _load_contract_and_implementations():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    expected_sources = contract["source_state"]
    if _sha256(B14_PATH) != expected_sources["b14"]["sha256"]:
        raise RuntimeError("The frozen B14 source fingerprint drifted.")
    if _sha256(B15_PATH) != expected_sources["b15"]["sha256"]:
        raise RuntimeError("The frozen B15 source fingerprint drifted.")

    tolerance = contract["module_boundary"]["constants"]["GEOMETRY_TOLERANCE"]
    legacy_tree = ast.parse(
        B15_PATH.read_text(encoding="utf-8"), filename=str(B15_PATH)
    )
    definitions = [_function(legacy_tree, name) for name in FUNCTION_NAMES]
    definitions.sort(key=lambda node: node.lineno)
    namespace = {"math": math, "GEOMETRY_TOLERANCE": tolerance}
    exec(
        compile(
            ast.Module(body=definitions, type_ignores=[]),
            str(B15_PATH),
            "exec",
        ),
        namespace,
    )
    legacy = {name: namespace[name] for name in FUNCTION_NAMES}
    modular = {name: getattr(modular_api, name) for name in FUNCTION_NAMES}
    return contract, {LEGACY_ROUTE: legacy, MODULAR_ROUTE: modular}


def build_calculation_cases(contract, legacy):
    """Build the complete accepted valid/error parity grid once."""
    parity = contract["parity_contract"]
    cases = []
    displacement = parity["displacement_grid"]
    for arguments in itertools.product(
        displacement["lengths_mm"],
        displacement["radii_mm"],
        displacement["integration_steps"],
    ):
        cases.append({
            "function": "clothoid_entry_displacement",
            "arguments": tuple(arguments),
            "expected_error": None,
        })

    offset = parity["offset_grid"]
    for arguments in itertools.product(
        offset["circle_centre_y_mm"],
        offset["radii_mm"],
        offset["transition_lengths_mm"],
    ):
        cases.append({
            "function": "transition_start_signed_offset",
            "arguments": tuple(arguments),
            "expected_error": None,
        })

    for scenario in parity["solver_scenarios"]:
        centre_y = scenario["circle_centre_y_mm"]
        radius = scenario["radius_mm"]
        angle = scenario["total_angle_rad"]
        maximum_length = (2.0 * radius * angle) - 1.0e-6
        start = legacy["transition_start_signed_offset"](
            centre_y, radius, 0.0
        )
        finish = legacy["transition_start_signed_offset"](
            centre_y, radius, maximum_length
        )
        for fraction in parity["solver_target_fractions"]:
            target = start + (fraction * (finish - start))
            cases.append({
                "function": "solve_transition_length",
                "arguments": (
                    centre_y,
                    radius,
                    target,
                    angle,
                    scenario["track_name"],
                    scenario["end_name"],
                ),
                "expected_error": None,
            })

    for case in parity["error_cases"]:
        cases.append({
            "function": case["function"],
            "arguments": tuple(case["arguments"]),
            "expected_error": {
                "exception_type": case["exception_type"],
                "required_text": case["required_text"],
            },
        })
    return tuple(cases)


def execute_calculation_grid(implementation, cases):
    """Execute every case and preserve exact value/container/error identity."""
    results = []
    for case in cases:
        function = implementation[case["function"]]
        expected_error = case["expected_error"]
        try:
            value = function(*case["arguments"])
        except Exception as error:  # The frozen contract owns exact errors.
            if expected_error is None:
                raise
            if (
                type(error).__name__ != expected_error["exception_type"]
                or expected_error["required_text"] not in str(error)
            ):
                raise RuntimeError(
                    "The {} error contract drifted.".format(case["function"])
                ) from error
            results.append(("error", type(error).__name__, str(error)))
        else:
            if expected_error is not None:
                raise RuntimeError(
                    "{} unexpectedly accepted an error case.".format(
                        case["function"]
                    )
                )
            results.append(("value", value))
    return tuple(results)


def _current_rss_mb():
    status = pathlib.Path("/proc/self/status")
    if not status.is_file():
        return None
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return float(line.split()[1]) / 1024.0
    return None


def _metric_summary(records, field):
    values = [float(record[field]) for record in records]
    return {
        "count": len(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "range": max(values) - min(values),
        "values": values,
    }


def _comparison(legacy_summary, modular_summary):
    legacy_median = legacy_summary["median"]
    modular_median = modular_summary["median"]
    delta = modular_median - legacy_median
    percent = None if legacy_median == 0.0 else (delta / legacy_median) * 100.0
    ranges_overlap = not (
        modular_summary["minimum"] > legacy_summary["maximum"]
        or legacy_summary["minimum"] > modular_summary["maximum"]
    )
    if modular_summary["maximum"] <= legacy_summary["maximum"]:
        disposition = "no_higher_observed_maximum"
    elif ranges_overlap:
        disposition = "observed_ranges_overlap"
    else:
        disposition = "modular_range_above_legacy_range_review_required"
    return {
        "modular_minus_legacy_median": delta,
        "modular_minus_legacy_percent": percent,
        "observed_ranges_overlap": ranges_overlap,
        "disposition": disposition,
    }


def profile_calculations(contract, implementations, repetitions):
    if repetitions < 3:
        raise ValueError("Calculation profiling requires at least three repetitions.")
    cases = build_calculation_cases(contract, implementations[LEGACY_ROUTE])
    result_counts = {
        "valid": sum(case["expected_error"] is None for case in cases),
        "error": sum(case["expected_error"] is not None for case in cases),
        "total": len(cases),
    }

    warmup_digests = {}
    for route in ROUTES:
        warmup_digests[route] = semantic_digest(
            execute_calculation_grid(implementations[route], cases)
        )
    if len(set(warmup_digests.values())) != 1:
        raise RuntimeError("Legacy/modular warm-up calculation results differ.")

    runs = {route: [] for route in ROUTES}
    route_orders = []
    expected_digest = warmup_digests[LEGACY_ROUTE]
    for round_index in range(repetitions):
        order = ROUTES if round_index % 2 == 0 else tuple(reversed(ROUTES))
        route_orders.append(list(order))
        for sequence, route in enumerate(order):
            gc.collect()
            rss_before = _current_rss_mb()
            wall_started = time.perf_counter_ns()
            cpu_started = time.process_time_ns()
            results = execute_calculation_grid(implementations[route], cases)
            cpu_ms = (time.process_time_ns() - cpu_started) / 1.0e6
            wall_ms = (time.perf_counter_ns() - wall_started) / 1.0e6
            rss_after = _current_rss_mb()
            digest = semantic_digest(results)
            if digest != expected_digest:
                raise RuntimeError(
                    "The {} calculation result digest drifted in round {}.".format(
                        route, round_index + 1
                    )
                )
            runs[route].append({
                "round": round_index + 1,
                "sequence_in_round": sequence + 1,
                "wall_ms": wall_ms,
                "process_cpu_ms": cpu_ms,
                "rss_before_mb": rss_before,
                "rss_after_mb": rss_after,
                "rss_delta_mb": (
                    None
                    if rss_before is None or rss_after is None
                    else rss_after - rss_before
                ),
                "result_digest": digest,
            })

    summaries = {}
    comparisons = {}
    for route in ROUTES:
        summaries[route] = {
            field: _metric_summary(runs[route], field)
            for field in ("wall_ms", "process_cpu_ms")
        }
    for field in ("wall_ms", "process_cpu_ms"):
        comparisons[field] = _comparison(
            summaries[LEGACY_ROUTE][field], summaries[MODULAR_ROUTE][field]
        )
    return {
        "profile_class": "standalone_complete_parity_grid",
        "process_policy": (
            "both implementations loaded once; one untimed warm-up per route; "
            "measured route order alternates in one process"
        ),
        "repetitions_per_route": repetitions,
        "route_orders": route_orders,
        "case_counts": result_counts,
        "result_digest": expected_digest,
        "warmup_digests": warmup_digests,
        "runs": runs,
        "summaries": summaries,
        "comparisons": comparisons,
    }


def _profiled_action_measurements(workflow, recipe_result):
    scenarios = {
        scenario.get("name"): scenario
        for scenario in recipe_result.get("scenarios", ())
        if isinstance(scenario, dict)
    }
    profiled = {}
    for declaration in PROFILED_ACTIONS[workflow]:
        name = declaration["scenario"]
        scenario = scenarios.get(name)
        if not isinstance(scenario, dict):
            raise RuntimeError("The {} scenario is missing.".format(name))
        measurement = scenario.get("measurement")
        if not isinstance(measurement, dict):
            raise RuntimeError("The {} measurement is missing.".format(name))
        missing = [field for field in MEASUREMENT_FIELDS if field not in measurement]
        if missing:
            raise RuntimeError(
                "The {} measurement lacks {}.".format(name, ", ".join(missing))
            )
        profiled[name] = {
            "span_class": declaration["span_class"],
            "starting_state": declaration["starting_state"],
            "measurement": {
                field: measurement[field] for field in MEASUREMENT_FIELDS
            },
        }
    return profiled


def _load_completed_run(path, workflow, route):
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        state.get("status") != "completed"
        or state.get("workflow") != workflow
        or state.get("calculation_route") != route
    ):
        raise RuntimeError(
            "The {} {} route did not produce a completed run.".format(
                workflow, route
            )
        )
    return state


def _workflow_summaries(samples):
    summaries = {}
    comparisons = {}
    for workflow in WORKFLOWS:
        summaries[workflow] = {}
        comparisons[workflow] = {}
        for declaration in PROFILED_ACTIONS[workflow]:
            action = declaration["scenario"]
            summaries[workflow][action] = {}
            comparisons[workflow][action] = {}
            for route in ROUTES:
                records = samples[workflow][action][route]
                summaries[workflow][action][route] = {
                    field: _metric_summary(records, field)
                    for field in MEASUREMENT_FIELDS
                }
            for field in ("wall_ms", "process_cpu_ms", "rss_delta_mb"):
                comparisons[workflow][action][field] = _comparison(
                    summaries[workflow][action][LEGACY_ROUTE][field],
                    summaries[workflow][action][MODULAR_ROUTE][field],
                )
            legacy_objects = summaries[workflow][action][LEGACY_ROUTE][
                "object_delta"
            ]
            modular_objects = summaries[workflow][action][MODULAR_ROUTE][
                "object_delta"
            ]
            comparisons[workflow][action]["object_delta"] = {
                "exact_sample_equality": (
                    legacy_objects["values"] == modular_objects["values"]
                ),
                "legacy_values": legacy_objects["values"],
                "modular_values": modular_objects["values"],
            }
    return summaries, comparisons


def profile_workflows(base_path, run_dir, repetitions, timeout):
    if repetitions < 3:
        raise ValueError("Workflow profiling requires at least three repetitions.")
    wrapper = (
        PROJECT_ROOT
        / "tools"
        / "freecad_bridge"
        / "run-phase3-transition-workflow"
    )
    fixture_hash = sha256(base_path)
    samples = {
        workflow: {
            declaration["scenario"]: {route: [] for route in ROUTES}
            for declaration in PROFILED_ACTIONS[workflow]
        }
        for workflow in WORKFLOWS
    }
    rounds = []
    workflow_digests = {workflow: set() for workflow in WORKFLOWS}
    freecad_versions = set()

    for round_index in range(repetitions):
        route_order = ROUTES if round_index % 2 == 0 else tuple(reversed(ROUTES))
        round_record = {
            "round": round_index + 1,
            "route_order": list(route_order),
            "workflows": {},
        }
        for workflow in WORKFLOWS:
            runs = {}
            round_record["workflows"][workflow] = {}
            for route in route_order:
                child_dir = (
                    run_dir
                    / "workflows"
                    / "round-{:02d}".format(round_index + 1)
                    / workflow
                    / route
                )
                command = [
                    str(wrapper),
                    "--base",
                    str(base_path),
                    "--workflow",
                    workflow,
                    "--route",
                    route,
                    "--run-dir",
                    str(child_dir),
                    "--timeout",
                    str(timeout),
                ]
                completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
                if completed.returncode:
                    raise RuntimeError(
                        "Round {} {} {} exited with status {}.".format(
                            round_index + 1,
                            workflow,
                            route,
                            completed.returncode,
                        )
                    )
                run_json = child_dir / "run.json"
                state = _load_completed_run(run_json, workflow, route)
                runs[route] = state
                recipe_result = state["transition_workflow"]["recipe"]
                digest = state["workflow_contract_sha256"]
                workflow_digests[workflow].add(digest)
                freecad_versions.add(state["session_before"]["freecad_version"])
                actions = _profiled_action_measurements(workflow, recipe_result)
                for action, record in actions.items():
                    samples[workflow][action][route].append(record["measurement"])
                round_record["workflows"][workflow][route] = {
                    "run_json": str(run_json),
                    "run_json_sha256": sha256(run_json),
                    "workflow_contract_sha256": digest,
                    "recipe_orchestrator_elapsed_seconds": state[
                        "recipe_orchestrator_elapsed_seconds"
                    ],
                    "actions": actions,
                }

            comparison = compare_workflow_routes(
                workflow,
                runs[LEGACY_ROUTE]["transition_workflow"]["recipe"],
                runs[MODULAR_ROUTE]["transition_workflow"]["recipe"],
            )
            if not comparison["equal"]:
                raise RuntimeError(
                    "Round {} {} route parity failed at {} path(s).".format(
                        round_index + 1,
                        workflow,
                        comparison["difference_count"],
                    )
                )
            round_record["workflows"][workflow]["comparison"] = comparison
        rounds.append(round_record)

    if any(len(digests) != 1 for digests in workflow_digests.values()):
        raise RuntimeError("A route-independent workflow contract varied by round.")
    if sha256(base_path) != fixture_hash:
        raise RuntimeError("The Phase 3 performance profile modified its fixture.")

    summaries, comparisons = _workflow_summaries(samples)
    return {
        "profile_class": "fresh_process_routed_gui_workflows",
        "process_policy": (
            "one fresh isolated FreeCAD GUI process per workflow, route and "
            "repetition; route order alternates by repetition"
        ),
        "cache_qualification": (
            "copied fixed fixture, fresh process/document/module state, persistent "
            "isolated preferences, uncontrolled operating-system file cache"
        ),
        "repetitions_per_route_and_workflow": repetitions,
        "freecad_versions": sorted(freecad_versions),
        "fixture_sha256": fixture_hash,
        "workflow_contract_sha256": {
            workflow: next(iter(digests))
            for workflow, digests in workflow_digests.items()
        },
        "profiled_actions": PROFILED_ACTIONS,
        "excluded_actions": {
            PLAIN_LINE_EDIT: {
                "reject_zero_angle_before_transaction": (
                    "invalid-input correctness timing, not a normal action"
                ),
                "abort_replacement_transaction": (
                    "injected-failure correctness timing, not a normal action"
                ),
            },
            CONNECTED_STRAIGHT: {},
        },
        "rounds": rounds,
        "summaries": summaries,
        "comparisons": comparisons,
    }


def _git_record():
    def run(arguments):
        completed = subprocess.run(
            ["git"] + list(arguments),
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip() if completed.returncode == 0 else None

    status = run(("status", "--porcelain", "--untracked-files=all"))
    return {
        "head": run(("rev-parse", "HEAD")),
        "status_porcelain": [] if not status else status.splitlines(),
    }


def _environment_record():
    cpu_model = None
    cpuinfo = pathlib.Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    memory_total_kib = None
    meminfo = pathlib.Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                memory_total_kib = int(line.split()[1])
                break
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "cpu_model": cpu_model,
        "memory_total_kib": memory_total_kib,
    }


def _source_record():
    paths = (
        B14_PATH,
        B15_PATH,
        PROJECT_ROOT / "TrackTemplate.FCMacro",
        CONTRACT_PATH,
        DOMAIN_PATH,
        PROJECT_ROOT / "tracktemplate" / "api.py",
        PROJECT_ROOT / "tracktemplate" / "compatibility" / "transition_pilot.py",
        PROJECT_ROOT / "tools" / "freecad_bridge" / "phase3_transition_workflow_recipe.py",
        PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "b14_ordinary_edit_driver.py",
        PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "b14_straight_station_driver.py",
        pathlib.Path(__file__).resolve(),
    )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): sha256(path) for path in paths
    }


def _run_directory(requested):
    root = RUN_ROOT.resolve()
    if requested is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        run_dir = root / (stamp + "-profile")
    else:
        run_dir = requested.resolve()
        try:
            run_dir.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "Phase 3 performance output must remain under {}.".format(root)
            ) from error
    if run_dir.exists():
        raise SystemExit("Phase 3 performance directory already exists: {}".format(run_dir))
    run_dir.mkdir(parents=True)
    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=(
            PROJECT_ROOT
            / "benchmark-output"
            / "freecad-bridge"
            / "fixtures"
            / "b14-default-base-regenerated.FCStd"
        ),
    )
    parser.add_argument(
        "--calculation-repetitions",
        type=int,
        default=DEFAULT_CALCULATION_REPETITIONS,
    )
    parser.add_argument(
        "--workflow-repetitions",
        type=int,
        default=DEFAULT_WORKFLOW_REPETITIONS,
    )
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--run-dir", type=pathlib.Path)
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("B14 plain-line fixture not found: {}".format(base_path))
    run_dir = _run_directory(args.run_dir)
    result_path = run_dir / "performance.json"
    state = {
        "schema_version": 1,
        "profile_id": "phase3-b16-transition-performance-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "purpose": (
            "Regression evidence for a mechanical architecture extraction; "
            "not an optimisation or an interaction-budget claim."
        ),
        "git": _git_record(),
        "environment": _environment_record(),
        "source_sha256": _source_record(),
        "fixture": str(base_path),
        "fixture_sha256": sha256(base_path),
    }
    try:
        contract, implementations = _load_contract_and_implementations()
        state["calculation_profile"] = profile_calculations(
            contract,
            implementations,
            args.calculation_repetitions,
        )
        state["workflow_profile"] = profile_workflows(
            base_path,
            run_dir,
            args.workflow_repetitions,
            args.timeout,
        )
        if state["workflow_profile"]["freecad_versions"] != ["1.1.1"]:
            raise RuntimeError("The qualified FreeCAD version set drifted.")
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        state["finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Phase 3 transition performance profile: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
