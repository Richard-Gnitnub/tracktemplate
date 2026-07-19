"""Drive B14 ordinary-track selected export, repeat, overwrite and rollback."""

import json
import os
import pathlib
import sys
import time

import FreeCAD as App

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets

from tools.freecad_bridge.ordinary_track_export_recipe import (
    COMMIT_FAILURE_MESSAGE,
    EXPECTED_LOGICAL_EXPORT_SHA256,
    EXPECTED_MANIFEST_ROW_COUNT,
    EXPECTED_TASK_COUNT,
    EXPORT_FORMATS,
    EXPORT_RECIPE_SCHEMA_VERSION,
    EXPORT_SCOPE,
    compare_logical_exports,
    export_directory_snapshot,
    export_variant_snapshot,
    sha256_file,
    validate_export_snapshot,
)
from tools.freecad_bridge.freecad_export_metrics import format_export_metrics
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
    shape_summary,
)


MODULE_NAME = "tracktemplate_b14_session"
module = sys.modules.get(MODULE_NAME)
if module is None:
    raise RuntimeError("Load B14 before running its ordinary-track export recipe")
document = App.ActiveDocument
if document is None or not str(document.FileName or ""):
    raise RuntimeError("Open a saved copied B14 ordinary-track fixture before export")

run_directory = pathlib.Path(str(document.FileName)).resolve().parent
output_directory = run_directory / "selected-export"
output_directory.mkdir(parents=True, exist_ok=False)


def _current_rss_mb():
    reader = getattr(module, "_workflow_current_rss_mb", None)
    return float(reader()) if callable(reader) else 0.0


def _format_metrics(directory, variant):
    return format_export_metrics(module, directory, variant, shape_summary)


def _raw_contract(snapshot):
    return {
        name: item["raw_sha256"]
        for name, item in snapshot.get("files", {}).items()
    }


def _yes_button(box):
    try:
        choice = QtWidgets.QMessageBox.StandardButton.Yes
    except AttributeError:
        choice = QtWidgets.QMessageBox.Yes
    return box.button(choice)


def _configure_export_dialog(dialog, directory, overwrite):
    dialog._loading_export_controls = True
    try:
        dialog.output_box.setText(str(directory))
        for format_key in EXPORT_FORMATS:
            dialog.format_boxes[format_key].setChecked(True)
        dialog.export_each_section_box.setChecked(True)
        dialog.combined_box.setChecked(True)
        dialog.manifest_box.setChecked(True)
        dialog.overwrite_box.setChecked(bool(overwrite))
        dialog.probe_box.setChecked(True)
        scope_index = dialog.scope_box.findText(EXPORT_SCOPE)
        if scope_index < 0:
            raise ValueError("The one-template-set selected-export scope is unavailable")
        dialog.scope_box.blockSignals(True)
        dialog.scope_box.setCurrentIndex(scope_index)
        dialog.scope_box.blockSignals(False)
    finally:
        dialog._loading_export_controls = False
    dialog._scope_changed()
    counts = module.summarise_preflight(dialog.issues)
    if dialog.current_set_id() != "SET-001":
        raise ValueError("Selected export did not resolve SET-001")
    if dialog.scope.get("scope_type") != EXPORT_SCOPE:
        raise ValueError("Selected export did not retain the template-set scope")
    if len(dialog.matching_records) != 4 or len(dialog.export_records) != 4:
        raise ValueError(
            "Expected four ordinary-track production records, found {}/{}".format(
                len(dialog.matching_records), len(dialog.export_records)
            )
        )
    if len((dialog.plan or {}).get("tasks", [])) != EXPECTED_TASK_COUNT:
        raise ValueError("Unexpected ordinary-track selected-export task count")
    if not (dialog.plan or {}).get("manifest_path"):
        raise ValueError("Ordinary-track selected export did not plan a manifest")
    if counts.get("blocking", 0):
        raise ValueError(
            "Ordinary-track selected export has blocking preflight issues: {}".format(
                dialog.issues
            )
        )
    if not dialog.export_button.isEnabled():
        raise ValueError("Ordinary-track selected export button is disabled")
    return {
        "scope": {
            key: dialog.scope.get(key)
            for key in ("scope_type", "route_id", "route_label")
        },
        "matching_records": len(dialog.matching_records),
        "export_records": len(dialog.export_records),
        "tasks": len(dialog.plan.get("tasks", [])),
        "manifest": bool(dialog.plan.get("manifest_path")),
        "issue_counts": counts,
        "issue_codes": [str(issue.get("issue_code") or "") for issue in dialog.issues],
        "planned_files": [
            os.path.basename(str(task.get("path") or ""))
            for task in dialog.plan.get("tasks", [])
        ] + [os.path.basename(str(dialog.plan.get("manifest_path") or ""))],
    }


def _run_dialog_scenario(name, overwrite=False, inject_commit_failure=False):
    active_document = App.ActiveDocument
    if active_document is None or active_document is not document:
        raise RuntimeError("The ordinary-track export recipe lost its source document")
    before = ordinary_track_document_snapshot(module, active_document)
    state = {
        "name": name,
        "overwrite_existing": bool(overwrite),
        "inject_commit_failure": bool(inject_commit_failure),
        "active": True,
        "confirmation_dialogs": [],
        "summary_dialogs": [],
        "unexpected_dialogs": [],
        "monitor_errors": [],
        "preflight_calls": [],
        "dispatch_calls": [],
        "selected_export_calls": [],
        "summary_payloads": [],
        "commit_injection": {
            "calls": 0,
            "replace_calls": 0,
            "entries": 0,
        },
    }

    original_preflight = module.run_production_preflight
    original_dispatch = module.dispatch_freecad_export
    original_selected_export = module.run_selected_production_export
    original_show_summary = module.show_production_export_summary
    original_commit = module.commit_staged_export_entries

    def measured_preflight(*args, **kwargs):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        rss_before = _current_rss_mb()
        objects_before = len(active_document.Objects)
        issues = original_preflight(*args, **kwargs)
        state["preflight_calls"].append({
            "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
            "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
            "rss_delta_mb": _current_rss_mb() - rss_before,
            "object_delta": len(active_document.Objects) - objects_before,
            "probe_export_bounds": bool(kwargs.get("probe_export_bounds", True)),
            "task_count": len((kwargs.get("plan") or {}).get("tasks", [])),
            "issue_counts": module.summarise_preflight(issues),
            "issue_codes": [str(issue.get("issue_code") or "") for issue in issues],
        })
        return issues

    def measured_dispatch(export_document, task, path):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        rss_before = _current_rss_mb()
        objects_before = len(export_document.Objects)
        item = {
            "format": str(task.get("format") or ""),
            "combined": bool(task.get("combined", False)),
            "record_count": len(task.get("records") or []),
            "document": str(getattr(export_document, "Name", "")),
            "path_name": os.path.basename(str(path)),
        }
        try:
            return original_dispatch(export_document, task, path)
        except Exception as error:
            item["error"] = "{}: {}".format(type(error).__name__, error)
            raise
        finally:
            item.update({
                "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
                "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
                "rss_delta_mb": _current_rss_mb() - rss_before,
                "objects_before": objects_before,
                "objects_after": len(export_document.Objects),
            })
            state["dispatch_calls"].append(item)

    def measured_selected_export(*args, **kwargs):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        rss_before = _current_rss_mb()
        objects_before = len(active_document.Objects)
        summary = original_selected_export(*args, **kwargs)
        state["selected_export_calls"].append({
            "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
            "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
            "rss_delta_mb": _current_rss_mb() - rss_before,
            "object_delta": len(active_document.Objects) - objects_before,
            "successful_files": int(summary.get("successful_files", 0)),
            "failed_files": int(summary.get("failed_files", 0)),
            "skipped_objects": int(summary.get("skipped_objects", 0)),
            "formats": list(summary.get("formats") or []),
            "failures": list(summary.get("failures") or []),
        })
        return summary

    def measured_show_summary(summary):
        state["summary_payloads"].append({
            "successful_files": int(summary.get("successful_files", 0)),
            "failed_files": int(summary.get("failed_files", 0)),
            "skipped_objects": int(summary.get("skipped_objects", 0)),
            "formats": list(summary.get("formats") or []),
            "manifest_requested": bool(summary.get("manifest_requested", False)),
            "manifest_created": bool(summary.get("manifest_path")),
            "failures": list(summary.get("failures") or []),
        })
        return original_show_summary(summary)

    def injected_commit(entries, overwrite_existing):
        state["commit_injection"]["calls"] += 1
        state["commit_injection"]["entries"] = len(entries or [])
        original_replace = module.os.replace

        def failing_replace(source, destination):
            state["commit_injection"]["replace_calls"] += 1
            if state["commit_injection"]["replace_calls"] == 4:
                raise RuntimeError(COMMIT_FAILURE_MESSAGE)
            return original_replace(source, destination)

        module.os.replace = failing_replace
        try:
            return original_commit(entries, overwrite_existing)
        finally:
            module.os.replace = original_replace

    module.run_production_preflight = measured_preflight
    module.dispatch_freecad_export = measured_dispatch
    module.run_selected_production_export = measured_selected_export
    module.show_production_export_summary = measured_show_summary
    if inject_commit_failure:
        module.commit_staged_export_entries = injected_commit

    dialog = None
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _current_rss_mb()
    objects_before = len(active_document.Objects)
    try:
        dialog = module.SelectedProductionExportDialog(active_document)
        state["configured_preview"] = _configure_export_dialog(
            dialog, output_directory, overwrite
        )

        def monitor():
            if not state["active"]:
                return
            try:
                visible_messages = []
                for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                    if not widget.isVisible() or not isinstance(widget, QtWidgets.QMessageBox):
                        continue
                    visible_messages.append(widget)
                    identity = id(widget)
                    if identity in state.setdefault("seen_messages", set()):
                        continue
                    state["seen_messages"].add(identity)
                    record = {
                        "title": str(widget.windowTitle() or ""),
                        "text": str(widget.text() or ""),
                        "informative_text": str(widget.informativeText() or ""),
                        "detailed_text": str(widget.detailedText() or ""),
                    }
                    if "Confirm selected production export" in record["title"]:
                        yes_button = _yes_button(widget)
                        if yes_button is None:
                            raise RuntimeError("Selected-export confirmation has no Yes button")
                        state["confirmation_dialogs"].append(record)
                        yes_button.click()
                    elif "Production export complete" in record["title"]:
                        state["summary_dialogs"].append(record)
                        widget.accept()
                    else:
                        state["unexpected_dialogs"].append(record)
                        widget.accept()
                if state["summary_dialogs"] and not visible_messages and dialog is not None:
                    dialog.accept()
            except Exception as error:
                state["monitor_errors"].append(
                    "{}: {}".format(type(error).__name__, error)
                )
                if dialog is not None:
                    dialog.reject()
            QtCore.QTimer.singleShot(25, monitor)

        def start_export():
            if not dialog.export_button.isEnabled():
                state["monitor_errors"].append("Selected-export button became disabled")
                dialog.reject()
                return
            state["export_button_text"] = str(dialog.export_button.text() or "")
            dialog.export_button.click()

        QtCore.QTimer.singleShot(0, monitor)
        QtCore.QTimer.singleShot(0, start_export)
        module.dialog_exec(dialog)
    finally:
        state["active"] = False
        module.run_production_preflight = original_preflight
        module.dispatch_freecad_export = original_dispatch
        module.run_selected_production_export = original_selected_export
        module.show_production_export_summary = original_show_summary
        module.commit_staged_export_entries = original_commit
        if dialog is not None:
            try:
                dialog.deleteLater()
            except Exception:
                pass

    state["measurement"] = {
        "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
        "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
        "rss_before_mb": rss_before,
        "rss_after_mb": _current_rss_mb(),
        "objects_before": objects_before,
        "objects_after": len(active_document.Objects),
    }
    state["measurement"]["rss_delta_mb"] = (
        state["measurement"]["rss_after_mb"] - rss_before
    )
    state["measurement"]["object_delta"] = (
        state["measurement"]["objects_after"] - objects_before
    )
    state["before_semantic_sha256"] = before["semantic_sha256"]
    after = ordinary_track_document_snapshot(module, active_document)
    state["after_semantic_sha256"] = after["semantic_sha256"]

    if state["monitor_errors"]:
        raise RuntimeError("; ".join(state["monitor_errors"]))
    if state["unexpected_dialogs"]:
        raise RuntimeError(
            "Unexpected selected-export dialogs: {}".format(
                state["unexpected_dialogs"]
            )
        )
    if len(state["confirmation_dialogs"]) != 1:
        raise RuntimeError(
            "Expected one selected-export confirmation, saw {}".format(
                len(state["confirmation_dialogs"])
            )
        )
    if len(state["summary_dialogs"]) != 1 or len(state["summary_payloads"]) != 1:
        raise RuntimeError("Selected export did not report exactly one summary")
    if len(state["selected_export_calls"]) != 1:
        raise RuntimeError("Selected export transaction did not run exactly once")
    if before["semantic_sha256"] != after["semantic_sha256"]:
        raise RuntimeError("Selected export changed the ordinary-track document")
    if len(active_document.Objects) != 9:
        raise RuntimeError("Selected export leaked temporary FreeCAD objects")
    temporary_objects = [
        str(obj.Name) for obj in active_document.Objects
        if str(obj.Name).startswith("TemporaryProductionExport_")
    ]
    if temporary_objects:
        raise RuntimeError(
            "Selected export retained temporary objects: {}".format(temporary_objects)
        )

    summary = state["summary_payloads"][0]
    if inject_commit_failure:
        if summary["successful_files"] != 0 or summary["failed_files"] != 1:
            raise RuntimeError("Injected selected-export failure reported success")
        if not any(COMMIT_FAILURE_MESSAGE in value for value in summary["failures"]):
            raise RuntimeError("Selected-export failure omitted the injected reason")
        if state["commit_injection"]["calls"] != 1:
            raise RuntimeError("Selected-export commit injection did not run once")
        if state["commit_injection"]["entries"] != EXPECTED_TASK_COUNT + 1:
            raise RuntimeError("Selected-export commit received an unexpected entry count")
        if state["commit_injection"]["replace_calls"] <= 4:
            raise RuntimeError("Selected-export commit rollback did not restore backups")
    else:
        if summary != {
            "successful_files": EXPECTED_TASK_COUNT + 1,
            "failed_files": 0,
            "skipped_objects": 0,
            "formats": ["DXF", "STEP", "STL", "SVG"],
            "manifest_requested": True,
            "manifest_created": True,
            "failures": [],
        }:
            raise RuntimeError("Unexpected selected-export success summary: {}".format(summary))
        if state["commit_injection"]["calls"]:
            raise RuntimeError("Commit failure injection ran during a success scenario")

    state.pop("active", None)
    state.pop("seen_messages", None)
    return state


result = {
    "schema_version": EXPORT_RECIPE_SCHEMA_VERSION,
    "source_document": str(document.FileName),
    "output_directory": str(output_directory),
    "initial_base": ordinary_track_snapshot(module, document),
    "initial_document": ordinary_track_document_snapshot(module, document),
    "exporter_capabilities": module.detect_exporter_capabilities(),
    "scenarios": [],
}

unavailable = [
    key for key in EXPORT_FORMATS
    if not result["exporter_capabilities"].get(key, {}).get("available", False)
]
if unavailable:
    raise RuntimeError("Required B14 exporters are unavailable: {}".format(unavailable))

initial = _run_dialog_scenario("initial_selected_export")
result["scenarios"].append(initial)
complete = export_directory_snapshot(output_directory)
base_variant = export_variant_snapshot(complete)
base_digest = validate_export_snapshot(base_variant)
if base_digest != EXPECTED_LOGICAL_EXPORT_SHA256:
    raise RuntimeError(
        "Ordinary-track export oracle changed: {}".format(base_digest)
    )
base_metrics = _format_metrics(output_directory, base_variant)
result["initial_export"] = {
    "snapshot": base_variant,
    "format_metrics": base_metrics,
    "logical_sha256": base_digest,
}

revision = _run_dialog_scenario("non_overwrite_revision_export")
result["scenarios"].append(revision)
complete = export_directory_snapshot(output_directory)
base_after_revision = export_variant_snapshot(complete)
revision_variant = export_variant_snapshot(complete, revision=2)
validate_export_snapshot(base_after_revision)
revision_digest = validate_export_snapshot(revision_variant, expected_revision=2)
compare_logical_exports(base_variant, base_after_revision)
compare_logical_exports(base_variant, revision_variant)
if _raw_contract(base_variant) != _raw_contract(base_after_revision):
    raise RuntimeError("Non-overwrite revision changed the accepted base output files")
revision_metrics = _format_metrics(output_directory, revision_variant)
if revision_metrics != base_metrics:
    raise RuntimeError("Revision export format metrics differ from the initial export")
result["revision_export"] = {
    "snapshot": revision_variant,
    "format_metrics": revision_metrics,
    "logical_sha256": revision_digest,
    "base_files_preserved": True,
}

sentinel_path = output_directory / "Curve_Set_001_Export_Manifest.csv"
sentinel_path.write_text("PHASE1 OVERWRITE SENTINEL\n", encoding="utf-8")
sentinel_sha256 = sha256_file(sentinel_path)
overwrite = _run_dialog_scenario("confirmed_atomic_overwrite", overwrite=True)
result["scenarios"].append(overwrite)
complete = export_directory_snapshot(output_directory)
overwritten_variant = export_variant_snapshot(complete)
validate_export_snapshot(overwritten_variant)
compare_logical_exports(base_variant, overwritten_variant)
overwritten_metrics = _format_metrics(output_directory, overwritten_variant)
if overwritten_metrics != base_metrics:
    raise RuntimeError("Overwrite export format metrics differ from the initial export")
if sha256_file(sentinel_path) == sentinel_sha256:
    raise RuntimeError("Confirmed overwrite did not replace the sentinel manifest")
revision_after_overwrite = export_variant_snapshot(complete, revision=2)
if _raw_contract(revision_variant) != _raw_contract(revision_after_overwrite):
    raise RuntimeError("Confirmed overwrite changed the preserved revision files")
result["overwrite_export"] = {
    "snapshot": overwritten_variant,
    "format_metrics": overwritten_metrics,
    "logical_sha256": overwritten_variant["logical_sha256"],
    "sentinel_sha256": sentinel_sha256,
    "sentinel_replaced": True,
    "revision_files_preserved": True,
}

before_rollback = export_directory_snapshot(output_directory)
rollback = _run_dialog_scenario(
    "injected_commit_failure_rollback",
    overwrite=True,
    inject_commit_failure=True,
)
result["scenarios"].append(rollback)
after_rollback = export_directory_snapshot(output_directory)
if _raw_contract(before_rollback) != _raw_contract(after_rollback):
    raise RuntimeError("Selected-export commit failure changed destination files")
if before_rollback.get("directories") != after_rollback.get("directories"):
    raise RuntimeError("Selected-export commit failure leaked a staging directory")
result["rollback_export"] = {
    "destination_files_unchanged": True,
    "temporary_directories": after_rollback.get("directories", []),
    "file_count": len(after_rollback.get("files", {})),
    "content_sha256": after_rollback.get("content_sha256", ""),
}

final_document = ordinary_track_document_snapshot(module, document)
if final_document["semantic_sha256"] != result["initial_document"]["semantic_sha256"]:
    raise RuntimeError("Ordinary-track selected export changed final document semantics")
result["final_document_semantic_sha256"] = final_document["semantic_sha256"]
result["manifest_row_count"] = EXPECTED_MANIFEST_ROW_COUNT
print(json.dumps(result, sort_keys=True))
