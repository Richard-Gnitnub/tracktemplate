#!/usr/bin/env python3
"""Exercise selected whole-set publication through the actual Qt dialog."""

import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import sys
import traceback
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "SELECTED_EXPORT_SET_GUI_PASS"


def load_native():
    path = ROOT / "tests/freecad_validate_selected_export_set.py"
    spec = importlib.util.spec_from_file_location("_selected_set_native", path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    return native


def gui_proof(module, directory):
    import FreeCAD as App
    import FreeCADGui as Gui
    from PySide6 import QtCore, QtGui, QtWidgets
    from tracktemplate.adapters.freecad.core_export_document import (
        CoreExportDocument,
    )

    native = load_native()
    previous = native.PREVIOUS
    assert not App.listDocuments(), "Use an empty isolated GUI session"
    _, identities = previous.source_evidence()
    document = previous.prepare_document(module, directory)
    result = {"cases": {}}

    def capture(widget, path):
        QtWidgets.QApplication.processEvents()
        assert widget.grab().save(str(path), "PNG")
        assert not QtGui.QImage(str(path)).isNull()
        return str(path)

    try:
        for name, csv_enabled in (
            ("success", True), ("csv-off", False),
            ("writer-failure", True), ("cancel", True),
            ("late-collision", True),
        ):
            output = directory / name
            output.mkdir()
            (output / "previous.svg").write_text("preserve previous output\n")
            initial_files = native.files_state(output)
            Gui.Selection.clearSelection()
            Gui.Selection.clearPreselection()
            App.setActiveDocument(document.Name)
            _, _, _, _, outline, *_ = native.SELECTED._selected_plan(
                module, document, output,
            )
            dialog = module.SelectedProductionExportDialog(document)
            dialog.setModal(True)
            dialog.show()
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
                dialog.manifest_box.setChecked(csv_enabled)
                dialog.probe_box.setChecked(True)
            finally:
                dialog._loading_export_controls = False
            dialog.refresh_preview()
            column = module.SELECTED_EXPORT_RECORD_FIELDS.index(
                "Production-record ID",
            )
            rows = [r for r in range(dialog.records_table.rowCount())
                    if dialog.records_table.item(r, column).text()
                    == outline["record_id"]]
            assert len(rows) == 1
            dialog.records_table.selectRow(rows[0])
            dialog.refresh_preview()
            child = Path(dialog.plan["output_directory"])
            expected_paths = {task["path"] for task in dialog.plan["tasks"]}
            if csv_enabled:
                expected_paths.add(dialog.plan["manifest_path"])
            assert child.parent == output and not child.exists()
            dialog.refresh_preview()
            assert Path(dialog.plan["output_directory"]) == child
            assert not dialog.overwrite_box.isEnabled()
            assert not dialog.overwrite_box.isChecked()
            assert not module.preflight_blocking_report(dialog.issues)
            assert len(dialog.plan["tasks"]) == 1
            assert dialog.export_button.isEnabled()
            preview = capture(dialog, directory / (name + "-preview.png"))
            before = previous.document_witness(module, document)
            visibility = {o.Name: o.ViewObject.Visibility
                          for o in document.Objects}
            registry = dict(App.listDocuments())
            seen = {"confirmations": [], "summaries": [], "errors": [],
                    "opened": [], "serialized": []}
            active = [True]

            def monitor():
                if not active[0]:
                    return
                try:
                    for widget in QtWidgets.QApplication.topLevelWidgets():
                        if (not isinstance(widget, QtWidgets.QMessageBox)
                                or not widget.isVisible()):
                            continue
                        item = {"title": widget.windowTitle(),
                                "text": widget.text(),
                                "information": widget.informativeText(),
                                "details": widget.detailedText()}
                        if "Confirm selected production export" in item["title"]:
                            seen["confirmations"].append(item)
                            text = "\n".join(item.values())
                            assert all(path in text for path in expected_paths)
                            assert str(child) in text
                            assert "FILES TO OVERWRITE" not in text
                            if name == "late-collision":
                                child.mkdir()
                                (child / "foreign.txt").write_text(
                                    "preserve collision owner\n",
                                )
                            choice = (QtWidgets.QMessageBox.StandardButton.No
                                      if name == "cancel" else
                                      QtWidgets.QMessageBox.StandardButton.Yes)
                            widget.button(choice).click()
                        elif "Selected production export result" in item["title"]:
                            item["visual"] = capture(
                                widget, directory / (name + "-result.png"),
                            )
                            seen["summaries"].append(item)
                            buttons = [b for b in widget.buttons()
                                       if b.text() == "Open output folder"]
                            if name in ("success", "csv-off"):
                                assert len(buttons) == 1
                                buttons[0].click()
                            else:
                                assert not buttons
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

            def observed_factory(serializer):
                def dispatch(scratch, task, path):
                    assert scratch is not document and scratch.Temporary
                    assert not child.exists()
                    assert task["path"] in expected_paths
                    seen["serialized"].append(task["path"])
                    if name == "writer-failure":
                        scratch.addObject("Part::Feature", "PartialExport")
                        raise RuntimeError(native.FAULT + " GUI writer")
                    return serializer(scratch, task, path)
                return CoreExportDocument(dispatch)

            binding = module.run_selected_production_export
            QtCore.QTimer.singleShot(0, monitor)
            try:
                with (
                    mock.patch.object(binding, "export_dispatcher_factory",
                                      observed_factory),
                    mock.patch.object(module, "open_export_directory",
                                      lambda path: seen["opened"].append(path)),
                ):
                    dialog.export_button.click()
            finally:
                active[0] = False
                dialog.close()
            (directory / (name + "-observed.json")).write_text(
                json.dumps(seen, indent=2, sort_keys=True) + "\n",
            )
            assert len(seen["confirmations"]) == 1, seen
            if name in ("success", "csv-off"):
                assert not seen["errors"] and len(seen["summaries"]) == 1
                assert seen["opened"] == [str(child)], seen
                assert set(seen["serialized"]) == expected_paths - {
                    path for path in expected_paths if path.endswith(".csv")
                }
                assert {str(p) for p in child.iterdir()} == expected_paths
                assert str(child) in seen["summaries"][0]["information"]
                assert "Successful files: {}".format(
                    1 + int(csv_enabled),
                ) in seen["summaries"][0]["information"]
            elif name == "cancel":
                assert not seen["errors"] and not seen["summaries"]
                assert not seen["serialized"] and not child.exists()
            elif name == "writer-failure":
                assert not seen["errors"] and len(seen["summaries"]) == 1
                assert not child.exists() and not seen["opened"]
                text = json.dumps(seen["summaries"])
                assert native.FAULT in text and "Successful files: 0" in text
            else:
                assert not seen["serialized"] and not seen["opened"]
                assert seen["errors"] or seen["summaries"]
                assert {p.name for p in child.iterdir()} == {"foreign.txt"}
                assert (child / "foreign.txt").read_text() == (
                    "preserve collision owner\n"
                )
            assert all(native.files_state(output).get(k) == v
                       for k, v in initial_files.items())
            assert not [p for p in output.iterdir() if p.name.startswith(".")]
            assert dict(App.listDocuments()) == registry
            previous.assert_document(module, document, before)
            assert visibility == {o.Name: o.ViewObject.Visibility
                                  for o in document.Objects}
            assert dialog.output_box.text() == str(output)
            result["cases"][name] = {
                "dialogs": seen, "preview_visual": preview,
                "confirmed_output_directory": str(child),
                "previous_output_and_editable_document_preserved": True,
            }
        document = previous.reopen_document(module, document)
        result["save_reopen_unchanged"] = True
        result["sentinel"] = SENTINEL
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        result["fixture_and_oracles_preserved"] = all(
            native.CORE.sha256(path) == value
            for path, value in identities.items()
        )
        assert result["fixture_and_oracles_preserved"]
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
    directory = (ROOT / "benchmark-output/freecad-bridge/selected-export-set-runs"
                 / stamp)
    directory.mkdir(parents=True, exist_ok=False)
    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    client = FreeCADClient(host="127.0.0.1", port=19875, timeout=30.0,
                          token=token.read_text().strip())
    loader = ROOT / "tools/freecad_bridge/probes/load_phase3_transition_workflow.py"
    sources = [Path(__file__).resolve(),
               ROOT / "tests/freecad_validate_selected_export_set.py",
               ROOT / "TrackTemplate.FCMacro",
               *sorted((ROOT / "tracktemplate").rglob("*.py"))]
    state = {"status": "RUNNING", "output_status": "Private development only",
             "source_sha256": {str(p.relative_to(ROOT)): sha256(p)
                               for p in sources}}
    try:
        assert client.ping()
        empty = parse_json_output(execute(client, (
            "import json, FreeCAD as App\n"
            "print(json.dumps(sorted(App.listDocuments())))\n"
        )))
        assert empty == []
        code = (
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'\n"
            + loader.read_text()
            + "\nimport importlib.util, json, pathlib\n"
            + "spec = importlib.util.spec_from_file_location("
            + "'_selected_set_gui', {!r})\n".format(str(Path(__file__).resolve()))
            + "proof = importlib.util.module_from_spec(spec)\n"
            + "spec.loader.exec_module(proof)\n"
            + "result = proof.gui_proof(_PHASE3_SESSION.module, "
            + "pathlib.Path({!r}))\n".format(str(directory))
            + "result['profile'] = _PHASE3_QUALIFICATION["
            + "'compatibility_evaluation']['matched_profile_id']\n"
            + "print(json.dumps(result, sort_keys=True))\n"
        )
        state["proof"] = parse_json_output(submit_and_wait(
            client, code, "Selected whole-set export real GUI", args.timeout,
        ))
        assert state["proof"]["sentinel"] == SENTINEL
        assert state["proof"]["profile"] == (
            "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
        )
        state["visual_sha256"] = {
            p.name: sha256(p) for p in directory.glob("*.png")
        }
        assert len(state["visual_sha256"]) == 8
        state["status"] = "PASS"
    except Exception:
        state["status"] = "FAIL"
        state["traceback"] = traceback.format_exc()
    finally:
        state["source_unchanged"] = all(
            sha256(ROOT / p) == value
            for p, value in state["source_sha256"].items()
        )
        if not state["source_unchanged"]:
            state["status"] = "FAIL"
        (directory / "run.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
        )
        print("SELECTED_EXPORT_SET_GUI_EVIDENCE=" + str(directory), flush=True)
    if state["status"] != "PASS":
        raise RuntimeError(state.get("traceback", "Source changed"))
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
