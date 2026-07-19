#!/usr/bin/env python3
"""Run the completed-document B14-to-B15 GUI acceptance recipe."""

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
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)
from tools.freecad_bridge.run_b14_crossover import capture_visual_evidence  # noqa: E402
from tools.freecad_bridge.run_b14_warm_reuse import verify_source_run  # noqa: E402


DRIVER_MODULE = "tracktemplate_b15_acceptance_driver"
B15_MACRO = (
    PROJECT_ROOT
    / "model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro"
)


def driver_job(client, expression, label, timeout):
    code = (
        "import json,sys; print(json.dumps(sys.modules[{module!r}].driver.{expression}, "
        "sort_keys=True))"
    ).format(module=DRIVER_MODULE, expression=expression)
    job = submit_and_wait(client, code, label, timeout)
    return {
        "orchestrator_elapsed_seconds": job.get("orchestrator_elapsed_seconds"),
        "result": parse_json_output(job),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--action-timeout", type=float, default=1200.0)
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("Completed B14 document not found: {}".format(base_path))
    source_state_path, source_state = verify_source_run(base_path)
    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "acceptance-runs"
        / run_stamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "b14-to-b15-acceptance.FCStd"
    shutil.copy2(base_path, document_path)

    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    source_hash = sha256(base_path)
    state = {
        "run_started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recipe_id": "b14-completed-xo001-to-b15-chair-representation-acceptance",
        "scope": (
            "B15 inherited-layer parity plus chair analysis/support/layout/solid migration, "
            "unchanged-layout reuse, retained-solid reset, fresh construction, solid reuse, "
            "save/reopen and real GUI evidence"
        ),
        "performance_qualification": (
            "Acceptance timings are observations only. Current cold and unchanged-result "
            "durations are explicitly not approved human-use budgets."
        ),
        "b14_macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "b15_macro_sha256": sha256(B15_MACRO),
        "source_completed_document": str(base_path),
        "source_completed_document_sha256": source_hash,
        "source_run_json": str(source_state_path),
        "source_run_json_sha256": sha256(source_state_path),
        "source_run_id": base_path.parent.name,
        "source_base_semantic_sha256": source_state["base_validation"]["semantic_sha256"],
        "run_document": str(document_path),
        "run_document_initial_sha256": sha256(document_path),
        "actions": [],
    }
    result_path = run_dir / "acceptance-run.json"
    started = time.monotonic()

    try:
        state["session_before_open"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if state["session_before_open"].get("documents"):
            raise RuntimeError("B15 acceptance requires an empty dedicated FreeCAD session")
        state["opened"] = parse_json_output(execute(client, """
import FreeCAD as App, FreeCADGui as Gui
if App.listDocuments():
    raise RuntimeError('B15 acceptance requires an empty dedicated FreeCAD session')
doc = App.openDocument({document_path!r})
Gui.activeDocument().activeView().viewTop()
Gui.activeDocument().activeView().fitAll()
print(__import__('json').dumps({{'document': doc.Name, 'objects': len(doc.Objects)}}))
""".format(document_path=str(document_path))))

        load_job = submit_and_wait(
            client,
            (PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b15.py").read_text(
                encoding="utf-8"
            ),
            "load B15",
            300.0,
        )
        state["macro_load"] = parse_json_output(load_job)
        state["manager"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT
            / "tools"
            / "freecad_bridge"
            / "probes"
            / "show_b15_trackwork_manager.py",
        ))
        state["driver"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT
            / "tools"
            / "freecad_bridge"
            / "probes"
            / "b15_acceptance_driver.py",
        ))
        state["prepared"] = driver_job(
            client,
            "prepare()",
            "validate completed B14 state under B15",
            args.action_timeout,
        )

        for expression, label in (
            ("run_analysis()", "B15 chair analysis"),
            ("run_support()", "B15 bounded model support"),
            ("run_layout(False)", "B15 revised 2D chair layout"),
            ("run_layout(True)", "B15 unchanged 2D chair layout reuse"),
        ):
            state["actions"].append({
                "label": label,
                **driver_job(client, expression, label, args.action_timeout),
            })

        state["solid_reset"] = driver_job(
            client,
            "remove_solids()",
            "remove retained B14 supported-chair solids",
            args.action_timeout,
        )
        for expression, label in (
            ("run_solids(False)", "B15 fresh supported-chair solid construction"),
            ("run_solids(True)", "B15 unchanged supported-chair solid reuse"),
        ):
            state["actions"].append({
                "label": label,
                **driver_job(client, expression, label, args.action_timeout),
            })

        state["save_reopen"] = driver_job(
            client,
            "save_reopen()",
            "B15 save and reopen validation",
            args.action_timeout,
        )
        report_result = execute(
            client,
            "import sys; print(sys.modules[{!r}].driver.report())".format(DRIVER_MODULE),
        )
        state["workflow_report"] = report_result["output"]
        (run_dir / "workflow-report.txt").write_text(
            state["workflow_report"],
            encoding="utf-8",
        )
        state["visual_evidence"] = capture_visual_evidence(
            client,
            run_dir,
            module_name="tracktemplate_b15_session",
        )
        state["session"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        state["source_completed_document_sha256_after"] = sha256(base_path)
        if state["source_completed_document_sha256_after"] != source_hash:
            raise RuntimeError("The source completed B14 document changed")
        state["run_document_final_sha256"] = sha256(document_path)
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["status"] = "failed"
        state["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        state["run_finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state["orchestrator_total_elapsed_seconds"] = time.monotonic() - started
        copied_logs = []
        for source_name in ("FreeCAD.log", "b15-acceptance-launcher.log"):
            source = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / source_name
            if source.is_file():
                destination = run_dir / source_name
                shutil.copy2(source, destination)
                copied_logs.append(str(destination))
        state["copied_logs"] = copied_logs
        result_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("B15 acceptance evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
