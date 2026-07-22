#!/usr/bin/env python3
"""Run and compare both Phase 3 routes for the two bounded GUI workflows."""

import argparse
import datetime
import json
import pathlib
import subprocess
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase3-transition-workflow-runs"
)
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge.orchestration import sha256  # noqa: E402
from tools.freecad_bridge.phase3_transition_workflow_recipe import (  # noqa: E402
    LEGACY_ROUTE,
    MODULAR_ROUTE,
    WORKFLOWS,
    compare_workflow_routes,
)


def _load_completed_run(path, workflow, route):
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        state.get("status") != "completed"
        or state.get("workflow") != workflow
        or state.get("calculation_route") != route
    ):
        raise RuntimeError(
            "The {} {} route did not produce a completed run.".format(
                workflow,
                route,
            )
        )
    return state


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
    parser.add_argument("--timeout", type=float, default=1200.0)
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("B14 plain-line fixture not found: {}".format(base_path))
    source_sha256_before = sha256(base_path)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    series_dir = RUN_ROOT / "{}-series".format(stamp)
    series_dir.mkdir(parents=True, exist_ok=False)
    result_path = series_dir / "comparison.json"
    state = {
        "schema_version": 1,
        "series_id": "phase3-b16-transition-routed-workflow-parity-v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_fixture": str(base_path),
        "source_fixture_sha256": source_sha256_before,
        "process_isolation": (
            "one fresh isolated FreeCAD GUI process per workflow and route"
        ),
        "route_order": [LEGACY_ROUTE, MODULAR_ROUTE],
        "workflows": {},
    }
    wrapper = (
        PROJECT_ROOT
        / "tools"
        / "freecad_bridge"
        / "run-phase3-transition-workflow"
    )
    try:
        for workflow in WORKFLOWS:
            runs = {}
            for route in (LEGACY_ROUTE, MODULAR_ROUTE):
                run_dir = series_dir / workflow / route
                command = [
                    str(wrapper),
                    "--base",
                    str(base_path),
                    "--workflow",
                    workflow,
                    "--route",
                    route,
                    "--run-dir",
                    str(run_dir),
                    "--timeout",
                    str(args.timeout),
                ]
                completed = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    check=False,
                )
                if completed.returncode:
                    raise RuntimeError(
                        "{} {} route exited with status {}.".format(
                            workflow,
                            route,
                            completed.returncode,
                        )
                    )
                run_json = run_dir / "run.json"
                runs[route] = _load_completed_run(
                    run_json,
                    workflow,
                    route,
                )

            comparison = compare_workflow_routes(
                workflow,
                runs[LEGACY_ROUTE]["transition_workflow"]["recipe"],
                runs[MODULAR_ROUTE]["transition_workflow"]["recipe"],
            )
            if not comparison["equal"]:
                raise RuntimeError(
                    "{} legacy/modular workflow parity failed at {} path(s).".format(
                        workflow,
                        comparison["difference_count"],
                    )
                )
            state["workflows"][workflow] = {
                "legacy_run_json": str(
                    series_dir / workflow / LEGACY_ROUTE / "run.json"
                ),
                "modular_run_json": str(
                    series_dir / workflow / MODULAR_ROUTE / "run.json"
                ),
                "legacy_workflow_contract_sha256": runs[LEGACY_ROUTE][
                    "workflow_contract_sha256"
                ],
                "modular_workflow_contract_sha256": runs[MODULAR_ROUTE][
                    "workflow_contract_sha256"
                ],
                "comparison": comparison,
            }
        state["source_fixture_sha256_after"] = sha256(base_path)
        if state["source_fixture_sha256_after"] != source_sha256_before:
            raise RuntimeError("The Phase 3 series modified its source fixture.")
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
        print("Phase 3 routed workflow series: {}".format(series_dir), flush=True)


if __name__ == "__main__":
    main()
