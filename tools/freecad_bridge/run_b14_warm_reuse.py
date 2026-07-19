#!/usr/bin/env python3
"""Run three unchanged-result B14 reuse iterations in one isolated process."""

import argparse
import datetime
import json
import pathlib
import shutil
import sys
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.b14_recipe import DEFAULT_STAGES  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)
from tools.freecad_bridge.run_b14_crossover import capture_visual_evidence  # noqa: E402


WARM_DRIVER_MODULE = "tracktemplate_b14_warm_reuse_driver"


def verify_source_run(base_path):
    state_path = base_path.parent / "run.json"
    if not state_path.is_file():
        raise ValueError("Completed warm base has no sibling run.json: {}".format(state_path))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "completed":
        raise ValueError("Warm base source run did not complete")
    if pathlib.Path(state.get("run_document") or "").resolve() != base_path:
        raise ValueError("Warm base does not match its source run_document")
    if state.get("macro_sha256") != sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"):
        raise ValueError("Warm base source used a different B14 macro")
    if state.get("base_validation", {}).get("semantic_sha256") != (
        "a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e"
    ):
        raise ValueError("Warm base source did not validate the expected nine-object fixture")
    stages = [item.get("name") for item in state.get("stages") or []]
    if stages != list(DEFAULT_STAGES):
        raise ValueError("Warm base source did not complete the exact cold stage sequence")
    if state.get("session", {}).get("documents", [{}])[0].get("object_count") != 27:
        raise ValueError("Warm base source did not finish with 27 objects")
    return state_path, state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=pathlib.Path, required=True)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--iteration-timeout", type=float, default=900.0)
    args = parser.parse_args()
    if args.iterations != 3:
        raise SystemExit("The controlled Phase 0 warm series requires exactly three iterations")

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("Completed warm base not found: {}".format(base_path))
    source_state_path, source_state = verify_source_run(base_path)
    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "warm-runs" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "b14-warm-reuse.FCStd"
    shutil.copy2(base_path, document_path)

    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    state = {
        "run_started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recipe_id": "b14-xo001-completed-supported-chair-unchanged-reuse",
        "cache_state": (
            "fresh FreeCAD process opening a completed persisted result; one same-process "
            "warm-up followed by three unchanged-signature operator iterations"
        ),
        "macro": "AdvancedTurnout.FCMacro",
        "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "source_completed_document": str(base_path),
        "source_completed_document_sha256": sha256(base_path),
        "source_run_json": str(source_state_path),
        "source_run_json_sha256": sha256(source_state_path),
        "source_run_id": base_path.parent.name,
        "source_base_semantic_sha256": source_state["base_validation"]["semantic_sha256"],
        "run_document": str(document_path),
        "iterations": [],
    }
    result_path = run_dir / "warm-run.json"
    started = time.monotonic()

    try:
        state["session_before_open"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before_open"].get("documents"):
            raise RuntimeError("Warm reuse requires an empty dedicated FreeCAD session")
        state["opened"] = parse_json_output(execute(client, """
import FreeCAD as App, FreeCADGui as Gui
if App.listDocuments():
    raise RuntimeError('Warm reuse requires an empty dedicated FreeCAD session')
doc = App.openDocument({document_path!r})
Gui.activeDocument().activeView().viewTop()
Gui.activeDocument().activeView().fitAll()
print(__import__('json').dumps({{'document': doc.Name, 'objects': len(doc.Objects)}}))
""".format(document_path=str(document_path))))

        load_job = submit_and_wait(
            client,
            (PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b14.py").read_text(
                encoding="utf-8"
            ),
            "load B14",
            300.0,
        )
        state["macro_load"] = parse_json_output(load_job)
        state["manager"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "show_trackwork_manager.py",
        ))
        state["cold_driver"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "b14_benchmark_driver.py",
        ))
        state["warm_driver"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "b14_warm_reuse_driver.py",
        ))
        prepare_job = submit_and_wait(
            client,
            "import json,sys; print(json.dumps(sys.modules[{!r}].driver.prepare(), sort_keys=True))".format(
                WARM_DRIVER_MODULE
            ),
            "validate completed warm state",
            args.iteration_timeout,
        )
        state["prepared"] = {
            "orchestrator_elapsed_seconds": prepare_job.get("orchestrator_elapsed_seconds"),
            "result": parse_json_output(prepare_job),
        }

        warmup_code = (
            "import json,sys; print(json.dumps(sys.modules[{module!r}].driver.run_iteration("
            "'warm-up'), sort_keys=True))"
        ).format(module=WARM_DRIVER_MODULE)
        warmup_job = submit_and_wait(
            client,
            warmup_code,
            "warm-up",
            args.iteration_timeout,
        )
        state["warmup"] = {
            "orchestrator_elapsed_seconds": warmup_job.get("orchestrator_elapsed_seconds"),
            "result": parse_json_output(warmup_job),
        }

        for index in range(1, args.iterations + 1):
            code = (
                "import json,sys; print(json.dumps(sys.modules[{module!r}].driver.run_iteration("
                "{label!r}), sort_keys=True))"
            ).format(module=WARM_DRIVER_MODULE, label="measured-{}".format(index))
            job = submit_and_wait(
                client,
                code,
                "warm reuse {}".format(index),
                args.iteration_timeout,
            )
            state["iterations"].append({
                "orchestrator_elapsed_seconds": job.get("orchestrator_elapsed_seconds"),
                "result": parse_json_output(job),
            })

        state["visual_evidence"] = capture_visual_evidence(client, run_dir)
        state["session"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        state["run_finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state["orchestrator_total_elapsed_seconds"] = time.monotonic() - started
        copied_logs = []
        for source_name in ("FreeCAD.log", "warm-run-launcher.log"):
            source = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / source_name
            if source.is_file():
                destination = run_dir / source_name
                shutil.copy2(source, destination)
                copied_logs.append(str(destination))
        state["copied_logs"] = copied_logs
        result_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("Warm evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
