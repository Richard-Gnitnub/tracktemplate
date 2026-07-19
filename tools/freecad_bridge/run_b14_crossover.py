#!/usr/bin/env python3
"""Run the deterministic B14 crossover recipe in an empty bridge session."""

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
from tools.freecad_bridge.b14_recipe import DEFAULT_CHAINAGE_MM, DEFAULT_STAGES  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)

DRIVER_MODULE = "tracktemplate_b14_benchmark_driver"


def capture_visual_evidence(client, run_dir, module_name="tracktemplate_b14_session"):
    view_path = run_dir / "final-top-view.png"
    window_path = run_dir / "final-freecad-window.png"
    manager_path = run_dir / "final-manager.png"
    code = """
import json, pathlib, sys
import FreeCAD as App, FreeCADGui as Gui
try:
    from PySide6 import QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtGui, QtWidgets
    except ImportError:
        from PySide import QtGui
        QtWidgets = QtGui
if App.ActiveDocument is None or Gui.ActiveDocument is None:
    raise RuntimeError('No active document is available for final visual evidence')
view_path = pathlib.Path({view_path!r})
window_path = pathlib.Path({window_path!r})
manager_path = pathlib.Path({manager_path!r})
module = sys.modules.get({module_name!r})
manager = getattr(module, '_automation_trackwork_manager', None) if module else None
if manager is None:
    raise RuntimeError('The requested automated trackwork manager is not open')
manager.hide()
main_window = Gui.getMainWindow()
main_window.showNormal()
main_window.show()
main_window.raise_()
main_window.activateWindow()
view = Gui.activeDocument().activeView()
view.viewTop()
view.fitAll()
view.redraw()
for _iteration in range(5):
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
view.saveImage(str(view_path), 1600, 1000, 'Current')
if not main_window.grab().save(str(window_path), 'PNG'):
    raise RuntimeError('Qt could not save the final FreeCAD-window image')
manager.show()
manager.raise_()
manager.activateWindow()
QtWidgets.QApplication.processEvents()
if not manager.grab().save(str(manager_path), 'PNG'):
    raise RuntimeError('Qt could not save the final manager image')
for path in (view_path, window_path, manager_path):
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError('FreeCAD did not create visual evidence: {{}}'.format(path))
view_image = QtGui.QImage(str(view_path))
sampled_colours = set()
for y_pos in range(0, view_image.height(), 5):
    for x_pos in range(0, view_image.width(), 5):
        sampled_colours.add(int(view_image.pixel(x_pos, y_pos)))
        if len(sampled_colours) >= 100:
            break
    if len(sampled_colours) >= 100:
        break
if len(sampled_colours) < 2:
    raise RuntimeError('Final top-view image is a sampled single-colour frame')
print(json.dumps({{
    'top_view': {{
        'path': str(view_path),
        'bytes': view_path.stat().st_size,
        'sampled_colour_count': len(sampled_colours),
    }},
    'freecad_window': {{'path': str(window_path), 'bytes': window_path.stat().st_size}},
    'manager': {{'path': str(manager_path), 'bytes': manager_path.stat().st_size}},
}}, sort_keys=True))
""".format(
        view_path=str(view_path),
        window_path=str(window_path),
        manager_path=str(manager_path),
        module_name=str(module_name),
    )
    return parse_json_output(execute(client, code))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "fixtures" / "b14-default-base.FCStd",
    )
    parser.add_argument("--chainage", type=float, default=DEFAULT_CHAINAGE_MM)
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--stage-timeout", type=float, default=1800.0)
    parser.add_argument("--stages", default=",".join(DEFAULT_STAGES))
    args = parser.parse_args()

    base_path = args.base.resolve()
    if not base_path.is_file():
        raise SystemExit("Benchmark base fixture not found: {}".format(base_path))
    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")

    run_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "runs" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    document_path = run_dir / "b14-crossover.FCStd"
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
        "recipe_id": "b14-default-base-xo001-chainage-{:.3f}".format(args.chainage),
        "cache_state": "fresh FreeCAD process; operating-system file cache uncontrolled",
        "macro": "AdvancedTurnout.FCMacro",
        "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
        "base_fixture": str(base_path),
        "base_fixture_sha256": sha256(base_path),
        "run_document": str(document_path),
        "chainage_mm": args.chainage,
        "stages": [],
    }
    result_path = run_dir / "run.json"
    run_started = time.monotonic()

    try:
        state["session_before_open"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        open_result = execute(client, """
import FreeCAD as App, FreeCADGui as Gui
if App.listDocuments():
    raise RuntimeError('The deterministic recipe requires an empty dedicated FreeCAD session')
doc = App.openDocument({document_path!r})
Gui.activeDocument().activeView().viewTop()
Gui.activeDocument().activeView().fitAll()
print(__import__('json').dumps({{'document': doc.Name, 'objects': len(doc.Objects)}}))
""".format(document_path=str(document_path)))
        state["opened"] = parse_json_output(open_result)

        load_job = submit_and_wait(
            client,
            (PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b14.py").read_text(encoding="utf-8"),
            "load B14",
            300.0,
        )
        state["macro_load"] = parse_json_output(load_job)
        state["macro_load_orchestrator_elapsed_seconds"] = load_job.get("orchestrator_elapsed_seconds")
        state["base_validation"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "validate_b14_base.py",
        ))
        state["manager"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "show_trackwork_manager.py",
        ))
        state["driver"] = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "b14_benchmark_driver.py",
        ))

        requested_stages = tuple(item.strip() for item in args.stages.split(",") if item.strip())
        for stage in requested_stages:
            code = (
                "import json, sys; driver=sys.modules[{module!r}].driver; "
                "print(json.dumps(driver.run_stage({stage!r}, {chainage!r}), sort_keys=True))"
            ).format(module=DRIVER_MODULE, stage=stage, chainage=args.chainage)
            job = submit_and_wait(client, code, stage, args.stage_timeout)
            state["stages"].append({
                "name": stage,
                "submitted_at": job.get("submitted_at"),
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
                "orchestrator_elapsed_seconds": job.get("orchestrator_elapsed_seconds"),
                "result": parse_json_output(job),
            })

        report_result = execute(
            client,
            "import sys; print(sys.modules[{!r}].driver.report())".format(DRIVER_MODULE),
        )
        report = report_result["output"]
        (run_dir / "workflow-report.txt").write_text(report, encoding="utf-8")
        state["saved_document"] = execute(
            client,
            "import sys; print(sys.modules[{!r}].driver.save())".format(DRIVER_MODULE),
        )["output"].strip()
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
        state["orchestrator_total_elapsed_seconds"] = time.monotonic() - run_started
        copied_logs = []
        for source_name in ("FreeCAD.log", "cold-run-launcher.log"):
            source_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / source_name
            if source_path.is_file():
                destination = run_dir / source_name
                shutil.copy2(source_path, destination)
                copied_logs.append(str(destination))
        state["copied_logs"] = copied_logs
        result_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("Run evidence: {}".format(run_dir), flush=True)


if __name__ == "__main__":
    main()
