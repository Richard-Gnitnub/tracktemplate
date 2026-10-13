#!/usr/bin/env python3
"""Prove selected serializer isolation through the actual export dialog.

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
SENTINEL = "SELECTED_EXPORT_DOCUMENT_GUI_PASS"


def load_native():
    path = ROOT / "tests/freecad_validate_selected_export_document.py"
    spec = importlib.util.spec_from_file_location("_document_native", path)
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
    source, identities = previous.source_evidence()
    document = previous.prepare_document(module, directory)
    witness = App.newDocument("SelectedExportSelectionWitness")
    other = witness.addObject("Part::Feature", "Witness")
    result = {"fixture": str(source), "cases": {}}

    def selection():
        return [(
            item.DocumentName, item.ObjectName, tuple(item.SubElementNames),
            tuple((p.x, p.y, p.z) for p in item.PickedPoints),
            Gui.Selection.isSelected(item.Object, "", 0),
        ) for item in Gui.Selection.getSelectionEx("*", 0)]

    def preselection():
        item = Gui.Selection.getPreselection()
        return (
            item.DocumentName, item.ObjectName, tuple(item.SubElementNames),
            tuple((p.x, p.y, p.z) for p in item.PickedPoints),
        )

    def gui_state():
        return {
            "active": getattr(App.ActiveDocument, "Name", None),
            "internal_active": getattr(App.activeDocument(), "Name", None),
            "selection": selection(), "preselection": preselection(),
        }

    def select_witnesses(selected):
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(
            document.Name, selected.Name, "Edge1", 1.0, 2.0, 3.0,
        )
        Gui.Selection.addSelection(witness.Name, other.Name)
        App.setActiveDocument(witness.Name)
        Gui.Selection.setPreselection(other, "Edge1", 4.0, 5.0, 6.0)
        assert len(selection()) == 2
        assert preselection()[0] == witness.Name

    def capture(widget, path):
        QtWidgets.QApplication.processEvents()
        assert widget.grab().save(str(path), "PNG")
        assert not QtGui.QImage(str(path)).isNull()
        return str(path)

    try:
        for fail in (False, True):
            name = "serializer-failure" if fail else "success"
            output = directory / name
            output.mkdir()
            Gui.Selection.clearSelection()
            Gui.Selection.clearPreselection()
            App.setActiveDocument(document.Name)
            _, _, _, _, outline, *_ = native.SELECTED._selected_plan(
                module, document, output,
            )
            selected = document.getObject(outline["source_name"])
            other.Shape = selected.Shape.copy()
            witness.recompute()
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
            dialog.refresh_preview()
            assert len(dialog.plan["tasks"]) == 1
            existing = previous.seed_previous(dialog.plan)
            dialog.refresh_preview()
            assert not module.preflight_blocking_report(dialog.issues)
            assert dialog.export_button.isEnabled()
            preview = capture(dialog, directory / (name + "-preview.png"))
            select_witnesses(selected)
            pre_click_state = gui_state()
            registry = dict(App.listDocuments())
            before = previous.document_witness(module, document)
            visibility = {
                obj.Name: obj.ViewObject.Visibility for obj in document.Objects
            }
            seen = {"confirmations": [], "summaries": [], "errors": []}
            active = [True]
            observations = []
            restored_invocations = []
            command_entry_states = []

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
                            "title": title, "text": widget.text(),
                            "information": widget.informativeText(),
                            "details": widget.detailedText(),
                        }
                        if "Confirm selected production export" in title:
                            seen["confirmations"].append(item)
                            widget.button(
                                QtWidgets.QMessageBox.StandardButton.Yes,
                            ).click()
                        elif "Production export complete" in title:
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

            def observed_factory(serializer):
                command_entry_states.append(gui_state())

                def dispatch(scratch, task, path):
                    assert scratch.Name not in registry and scratch.Temporary
                    assert scratch is not document and scratch is not witness
                    observations.append(scratch.Name)
                    # Force native GUI restoration to do observable work.
                    Gui.Selection.clearSelection()
                    Gui.Selection.clearPreselection()
                    App.setActiveDocument(scratch.Name)
                    if fail:
                        scratch.addObject("Part::Feature", "PartialExport")
                        raise RuntimeError(native.FAULT + " serializer")
                    return serializer(scratch, task, path)
                isolated = CoreExportDocument(dispatch)

                def observed(editable, task, path):
                    # The inherited confirmation can change GUI state.
                    # Exercise restoration at the serializer boundary.
                    select_witnesses(selected)
                    selected_before = selection()
                    preselected_before = preselection()
                    try:
                        return isolated(editable, task, path)
                    finally:
                        assert dict(App.listDocuments()) == registry
                        assert App.ActiveDocument is witness
                        assert App.activeDocument() is witness
                        assert selection() == selected_before
                        assert preselection() == preselected_before
                        previous.assert_document(module, document, before)
                        restored_invocations.append(gui_state())

                return observed

            binding = module.run_selected_production_export
            factory = binding.export_dispatcher_factory
            binding.export_dispatcher_factory = observed_factory
            QtCore.QTimer.singleShot(0, monitor)
            try:
                dialog.export_button.click()
            finally:
                active[0] = False
                binding.export_dispatcher_factory = factory
                dialog.close()
            (directory / (name + "-observed.json")).write_text(
                json.dumps(seen, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            assert not seen["errors"], seen
            assert len(seen["confirmations"]) == 1, seen
            assert len(seen["summaries"]) == 1, seen
            assert len(observations) == 1
            assert len(restored_invocations) == 1
            assert len(command_entry_states) == 1
            info = seen["summaries"][0]["information"]
            details = seen["summaries"][0]["details"]
            assert "Successful files: {}".format(0 if fail else 2) in info
            assert "Failed files: {}".format(1 if fail else 0) in info
            if fail:
                assert native.FAULT in details
                assert all(path.read_bytes() == data
                           for path, data in existing.items())
            else:
                assert all(path.read_bytes() != data
                           for path, data in existing.items())
            assert dict(App.listDocuments()) == registry
            previous.assert_document(module, document, before)
            assert visibility == {
                obj.Name: obj.ViewObject.Visibility for obj in document.Objects
            }
            assert not list(output.glob(".railway_selected_export_*"))
            result["cases"][name] = {
                "dialogs": seen, "preview_visual": preview,
                "serializer_gui_state_restored": restored_invocations,
                "dialog_pre_click_state": pre_click_state,
                "dialog_command_entry_states": command_entry_states,
                "dialog_completed_state": gui_state(),
                "gui_state_boundary": (
                    "Restoration is asserted around the isolated serializer. "
                    "Inherited preview and confirmation can change GUI state "
                    "before that call; pre-click selection is not preserved "
                    "by this proof."
                ),
                "editable_state_history_identity_visibility_unchanged": True,
                "isolated_calls": len(observations),
            }
        Gui.Selection.clearSelection()
        Gui.Selection.clearPreselection()
        App.closeDocument(witness.Name)
        document = previous.reopen_document(module, document)
        result["save_reopen_unchanged"] = True
        result["sentinel"] = SENTINEL
    finally:
        for owned in (document, witness):
            for name, registered in dict(App.listDocuments()).items():
                if registered is owned:
                    App.closeDocument(name)
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
        ROOT / "benchmark-output/freecad-bridge/selected-export-document-runs"
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
        ROOT / "tests/freecad_validate_selected_export_document.py",
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
            + "'_document_gui', {!r})\n".format(str(Path(__file__).resolve()))
            + "proof = importlib.util.module_from_spec(spec)\n"
            + "spec.loader.exec_module(proof)\n"
            + "result = proof.gui_proof(_PHASE3_SESSION.module, "
            + "pathlib.Path({!r}))\n".format(str(directory))
            + "result['profile'] = _PHASE3_QUALIFICATION["
            + "'compatibility_evaluation']['matched_profile_id']\n"
            + "print(json.dumps(result, sort_keys=True))\n"
        )
        job = submit_and_wait(
            client, code, "Selected export document real GUI", args.timeout,
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
        print("SELECTED_EXPORT_DOCUMENT_GUI_EVIDENCE=" + str(directory),
              flush=True)
    assert state["source_unchanged"]
    print(SENTINEL, flush=True)


if __name__ == "__main__":
    main()
