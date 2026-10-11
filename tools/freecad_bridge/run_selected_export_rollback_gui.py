#!/usr/bin/env python3
"""Capture ordinary selected-export rollback diagnostics in the real GUI.

Run through the existing run-isolated wrapper. Only copied fixture documents
and generated evidence paths are used; this adds no GUI framework.
"""

import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import traceback


ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "SELECTED_EXPORT_ROLLBACK_GUI_PASS"


def load_native():
    path = ROOT / "tests/freecad_validate_selected_export_rollback.py"
    spec = importlib.util.spec_from_file_location("_rollback_native", path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    return native


def gui_proof(module, directory):
    import FreeCAD as App
    import FreeCADGui as Gui
    from PySide6 import QtCore, QtGui, QtWidgets

    native = load_native()
    assert not App.listDocuments(), "Use an empty isolated GUI session"
    source, identities = native.source_evidence()
    document = native.prepare_document(module, directory)
    assert Gui.activeDocument() is not None
    Gui.Selection.clearSelection()
    result = {"fixture": str(source), "cases": {}}

    def capture(widget, path):
        QtWidgets.QApplication.processEvents()
        assert widget.grab().save(str(path), "PNG")
        assert not QtGui.QImage(str(path)).isNull()
        return str(path)

    try:
        for restore_failure in (False, True):
            name = "restore-failure" if restore_failure else "full-rollback"
            output = directory / name
            output.mkdir()
            _, _, _, _, outline, *_ = native.SELECTED._selected_plan(
                module, document, output,
            )
            dialog = module.SelectedProductionExportDialog(document)
            dialog.setModal(True)
            dialog.show()
            QtWidgets.QApplication.processEvents()
            dialog._loading_export_controls = True
            try:
                index = dialog.scope_box.findText(
                    module.SELECTED_EXPORT_SCOPE_OBJECTS,
                )
                assert index >= 0
                dialog.scope_box.setCurrentIndex(index)
                dialog.output_box.setText(str(output))
                for key, box in dialog.format_boxes.items():
                    box.setChecked(key == module.EXPORT_FORMAT_SVG)
                dialog.export_each_section_box.setChecked(True)
                dialog.combined_box.setChecked(False)
                dialog.manifest_box.setChecked(True)
                dialog.overwrite_box.setChecked(True)
                dialog.probe_box.setChecked(True)
            finally:
                dialog._loading_export_controls = False
            dialog.refresh_preview()
            column = module.SELECTED_EXPORT_RECORD_FIELDS.index(
                "Production-record ID",
            )
            rows = [row for row in range(dialog.records_table.rowCount())
                    if dialog.records_table.item(row, column).text()
                    == outline["record_id"]]
            assert len(rows) == 1
            dialog.records_table.selectRow(rows[0])
            dialog.refresh_preview()
            # The inherited scope expands the selected outline to its pair.
            # Refresh again before using the final scope-derived filenames.
            dialog.refresh_preview()
            assert len(dialog.plan["tasks"]) == 1
            assert dialog.plan["manifest_path"]
            previous = native.seed_previous(dialog.plan)
            dialog.refresh_preview()
            assert {Path(task["path"]) for task in dialog.plan["tasks"]} | {
                Path(dialog.plan["manifest_path"])
            } == set(previous)
            assert not module.preflight_blocking_report(dialog.issues)
            assert dialog.export_button.isEnabled()
            assert dialog.export_button.text() == "Export 2 highlighted rows"
            preview = capture(dialog, directory / (name + "-preview.png"))
            before = native.document_witness(module, document)
            seen = {"confirmations": [], "summaries": [], "errors": []}
            active = [True]

            def monitor():
                if not active[0]:
                    return
                try:
                    for widget in QtWidgets.QApplication.topLevelWidgets():
                        if (not isinstance(widget, QtWidgets.QMessageBox)
                                or not widget.isVisible()):
                            continue
                        title = widget.windowTitle()
                        item = {
                            "title": title,
                            "text": widget.text(),
                            "information": widget.informativeText(),
                            "details": widget.detailedText(),
                        }
                        if "Confirm selected production export" in title:
                            seen["confirmations"].append(item)
                            yes = widget.button(
                                QtWidgets.QMessageBox.StandardButton.Yes,
                            )
                            assert yes is not None
                            yes.click()
                        elif "Production export complete" in title:
                            for button in widget.buttons():
                                if "Show Details" in button.text():
                                    button.click()
                            item["visual"] = capture(
                                widget, directory / (name + "-summary.png"),
                            )
                            seen["summaries"].append(item)
                            widget.accept()
                        else:
                            seen["errors"].append(item)
                            widget.reject()
                except Exception:
                    seen["errors"].append(traceback.format_exc())
                    for widget in QtWidgets.QApplication.topLevelWidgets():
                        if isinstance(widget, QtWidgets.QMessageBox):
                            widget.reject()
                QtCore.QTimer.singleShot(25, monitor)

            binding = module.run_selected_production_export
            factory = binding.export_files_factory
            observed = []
            binding.export_files_factory = native.fault_factory(
                restore_failure, observed,
            )
            QtCore.QTimer.singleShot(0, monitor)
            try:
                dialog.export_button.click()
            finally:
                active[0] = False
                binding.export_files_factory = factory
                dialog.close()
            (directory / (name + "-observed.json")).write_text(
                json.dumps({
                    "dialogs": seen,
                    "replace_calls": [item.replace_calls for item in observed],
                }, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            assert not seen["errors"], seen
            assert len(seen["confirmations"]) == 1, seen
            assert len(seen["summaries"]) == 1, seen
            assert len(observed) == 1 and observed[0].replace_calls == 6
            visible = seen["summaries"][0]
            assert "Successful files: 0" in visible["information"]
            assert "Failed files: 1" in visible["information"]
            summary = {
                "successful_files": 0, "failed_files": 1,
                "manifest_path": "",
                "failures": [visible["information"]],
                "failure_details": [visible["details"]],
            }
            witness = native.failure_witness(
                summary, output, previous, restore_failure,
            )
            native.assert_document(module, document, before)
            document = native.reopen_document(module, document)
            result["cases"][name] = {
                **witness, "dialogs": seen, "preview_visual": preview,
                "editable_state_and_save_reopen_unchanged": True,
            }
        result["sentinel"] = SENTINEL
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        result["source_fixture_and_oracles_preserved"] = all(
            native.CORE.sha256(path) == value
            for path, value in identities.items()
        )
        assert result["source_fixture_and_oracles_preserved"]
        assert not App.listDocuments()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / ".devtools/freecad-cli/src"))
    from freecad_cli.client import FreeCADClient
    from tools.freecad_bridge.orchestration import (
        execute, parse_json_output, sha256, submit_and_wait,
    )

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    directory = (
        ROOT / "benchmark-output/freecad-bridge/selected-export-rollback-runs"
        / stamp
    )
    directory.mkdir(parents=True, exist_ok=False)
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    client = FreeCADClient(
        host="127.0.0.1", port=19875, timeout=30.0,
        token=token.read_text(encoding="utf-8").strip(),
    )
    loader = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
    source_paths = [
        Path(__file__).resolve(),
        ROOT / "tests/freecad_validate_selected_export_rollback.py",
        ROOT / "TrackTemplate.FCMacro",
        *sorted((ROOT / "tracktemplate").rglob("*.py")),
    ]
    state = {
        "status": "RUNNING", "output_status": "Private development only",
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in source_paths
        },
    }
    try:
        assert client.ping()
        empty = parse_json_output(execute(client, (
            "import json, FreeCAD as App\n"
            "print(json.dumps(sorted(App.listDocuments())))\n"
        )))
        assert empty == [], empty
        code = (
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + loader.read_text(encoding="utf-8")
            + "\nimport importlib.util, json, pathlib\n"
            + "spec = importlib.util.spec_from_file_location("
            + "'_rollback_gui', {!r})\n".format(str(Path(__file__).resolve()))
            + "proof = importlib.util.module_from_spec(spec)\n"
            + "spec.loader.exec_module(proof)\n"
            + "result = proof.gui_proof(_PHASE3_SESSION.module, "
            + "pathlib.Path({!r}))\n".format(str(directory))
            + "result['profile'] = _PHASE3_QUALIFICATION["
            + "'compatibility_evaluation']['matched_profile_id']\n"
            + "print(json.dumps(result, sort_keys=True))\n"
        )
        job = submit_and_wait(
            client, code, "Selected export rollback real GUI", args.timeout,
        )
        state["proof"] = parse_json_output(job)
        assert state["proof"]["sentinel"] == SENTINEL
        assert state["proof"]["profile"] == (
            "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
        )
        state["visual_sha256"] = {
            path.name: sha256(path) for path in directory.glob("*.png")
        }
        assert len(state["visual_sha256"]) == 4
        state["status"] = "PASS"
    except Exception:
        state["status"] = "FAIL"
        state["traceback"] = traceback.format_exc()
        raise
    finally:
        for name in ("FreeCAD.log", "isolated-launcher.log"):
            path = ROOT / "benchmark-output/freecad-bridge" / name
            if path.is_file():
                shutil.copy2(path, directory / name)
        state["source_unchanged"] = all(
            sha256(ROOT / path) == expected
            for path, expected in state["source_sha256"].items()
        )
        if not state["source_unchanged"]:
            state["status"] = "FAIL"
        (directory / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("SELECTED_EXPORT_ROLLBACK_GUI_EVIDENCE=" + str(directory),
              flush=True)
    assert state["source_unchanged"]
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
