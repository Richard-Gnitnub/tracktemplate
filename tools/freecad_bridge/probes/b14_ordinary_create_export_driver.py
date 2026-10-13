"""Drive B14 plain-line create-time export and its final-task failure."""

import copy
import csv
import dataclasses
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import time

import FreeCAD as App
import FreeCADGui as Gui

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets

from tools.freecad_bridge.ordinary_track_edit_recipe import (
    EXPECTED_TRACK_CONFIGURATION,
    normalise_version_migration_snapshot,
)
from tools.freecad_bridge.freecad_export_metrics import format_export_metrics
from tools.freecad_bridge.ordinary_track_export_recipe import (
    CREATE_TIME_EXPORT_FAILED_FILENAME,
    CREATE_TIME_EXPORT_FAILURE_MESSAGE,
    CREATE_TIME_EXPORT_RECIPE_SCHEMA_VERSION,
    EXPECTED_CREATE_TIME_LOGICAL_EXPORT_SHA256,
    EXPECTED_EXPORT_FILENAMES,
    EXPECTED_EXPORT_METRICS_SHA256,
    EXPECTED_LOGICAL_EXPORT_SHA256,
    EXPECTED_TASK_COUNT,
    EXPORT_FORMATS,
    compare_create_time_document_to_base,
    create_time_export_document_snapshot,
    export_directory_snapshot,
    export_variant_snapshot,
    format_metrics_sha256,
    validate_create_time_failure_snapshot,
    validate_export_snapshot,
)
from tools.freecad_bridge.ordinary_track_recipe import (
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
    shape_summary,
)


MODULE_NAME = globals().get(
    "TRACKTEMPLATE_WORKFLOW_MODULE_NAME",
    "tracktemplate_b14_session",
)
BASE_MACRO_VERSION = globals().get(
    "TRACKTEMPLATE_BASE_MACRO_VERSION",
    "10.2A8A7B14",
)
ENFORCE_FROZEN_WORKFLOW_HASHES = globals().get(
    "TRACKTEMPLATE_ENFORCE_FROZEN_WORKFLOW_HASHES",
    True,
)
VERSION_MIGRATION_PREFIXES = globals().get(
    "TRACKTEMPLATE_VERSION_MIGRATION_PREFIXES",
    (),
)
SUCCESS_TEXT = "Curve and straight-track outputs created successfully"
STAGING_BARRIER = bool(globals().get(
    "TRACKTEMPLATE_CORE_EXPORT_STAGING_BARRIER", False,
))

ATOMIC_SET = bool(globals().get("TRACKTEMPLATE_CORE_EXPORT_ATOMIC_SET", False))
ISOLATED_EXPORT = STAGING_BARRIER or ATOMIC_SET

module = sys.modules.get(MODULE_NAME)
if module is None:
    raise RuntimeError("Load B14 before running its create-time export recipe")
document = App.ActiveDocument
if document is None or not str(document.FileName or ""):
    raise RuntimeError("Open a saved copied B14 plain-line fixture before export")

if ATOMIC_SET:
    _witness_path = (pathlib.Path(module.__file__).resolve().parent
                     / "tests/freecad_validate_core_export_atomic.py")
    _witness_spec = importlib.util.spec_from_file_location(
        "core_dependency_gui_witness", _witness_path,
    )
    dependency_witness = importlib.util.module_from_spec(_witness_spec)
    _witness_spec.loader.exec_module(dependency_witness)

run_directory = pathlib.Path(str(document.FileName)).resolve().parent
success_directory = run_directory / "create-time-export-success"
failure_directory = run_directory / "create-time-export-final-task-failure"
isolation_failure_directory = run_directory / "create-time-export-close-failure"
for output_directory in (success_directory, failure_directory):
    if output_directory.exists():
        raise RuntimeError("Create-time export output already exists: {}".format(output_directory))


def _current_rss_mb():
    reader = getattr(module, "_workflow_current_rss_mb", None)
    return float(reader()) if callable(reader) else 0.0


def _destination_files(directory):
    """Keep final-file bytes separate from files inside a staging directory."""
    if not directory.exists():
        return {}
    return {
        path.name: {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(directory.iterdir()) if path.is_file()
    }


def _seed_staging_failure_directory():
    """Supply copied-run targets that a failed staging run must preserve."""
    failure_directory.mkdir()
    for filename in (
        "Curve_Set_001_Combined_Cutting_Profiles.dxf",
        CREATE_TIME_EXPORT_FAILED_FILENAME,
        "Curve_Set_001_Export_Manifest.csv",
        "unrelated-operator-file.txt",
    ):
        (failure_directory / filename).write_bytes(
            "Existing destination: {}\n".format(filename).encode("utf-8")
        )
    return _destination_files(failure_directory)


def _yes_button(box):
    try:
        choice = QtWidgets.QMessageBox.StandardButton.Yes
    except AttributeError:
        choice = QtWidgets.QMessageBox.Yes
    return box.button(choice)


def _compact_summary(summary):
    return {
        "successful_files": int(summary.get("successful_files", 0)),
        "failed_files": int(summary.get("failed_files", 0)),
        "skipped_objects": int(summary.get("skipped_objects", 0)),
        "formats": list(summary.get("formats") or []),
        "manifest_requested": bool(summary.get("manifest_requested", False)),
        "manifest_created": bool(summary.get("manifest_path")),
        "failures": list(summary.get("failures") or []),
    }


def _document_contract(snapshot):
    return normalise_version_migration_snapshot(
        snapshot,
        VERSION_MIGRATION_PREFIXES,
    )


def _initial_dialog_contract(dialog):
    return {
        "angle_degrees": float(dialog.angle_box.value()),
        "production_export": dialog._production_export_values(),
        "output_mode": str(dialog.output_mode_box.currentText()),
    }


def _configure_dialog(dialog, output_directory, *, manifest=True):
    dialog.transition_box.setValue(600.0)
    dialog.radius_box.setValue(600.0)
    dialog.angle_box.setValue(90.0)
    dialog.main_width_box.setValue(32.0)
    dialog.parallel_count_box.setValue(1)
    dialog._set_parallel_count(1)
    dialog._populate_row(
        0,
        module.clone_track_config(EXPECTED_TRACK_CONFIGURATION[0], 600.0),
    )
    mode_index = dialog.output_mode_box.findText(module.OUTPUT_REPLACE)
    if mode_index < 0:
        raise ValueError("The B14 replace-output choice is unavailable")
    dialog.output_mode_box.setCurrentIndex(mode_index)

    dialog.production_export_enabled_box.setChecked(True)
    dialog.production_export_directory_box.setText(str(output_directory))
    dialog.production_include_role_box.setChecked(True)
    dialog.production_include_track_box.setChecked(True)
    dialog.production_include_section_box.setChecked(True)
    dialog.production_each_section_box.setChecked(True)
    dialog.production_combined_box.setChecked(True)
    dialog.production_overwrite_box.setChecked(STAGING_BARRIER)
    dialog.production_manifest_box.setChecked(manifest)
    dialog.production_open_directory_box.setChecked(ATOMIC_SET)
    for format_key in EXPORT_FORMATS:
        box = dialog.production_format_boxes[format_key]
        if not box.isEnabled():
            raise ValueError("The {} exporter is unavailable".format(format_key.upper()))
        box.setChecked(True)
    dialog._update_production_export_controls()
    if ATOMIC_SET:
        if dialog.production_overwrite_box.isEnabled():
            raise RuntimeError("Atomic Core exposes the obsolete overwrite option")
        if dialog.production_overwrite_box.text() != "New folder for each export":
            raise RuntimeError("Atomic Core does not explain its folder policy")
        if dialog.production_manifest_box.text() != (
            "Optional CSV; dependency JSON is always included"
        ):
            raise RuntimeError("Core does not distinguish optional CSV from JSON")

    values = dialog.values()
    production = values[15]
    checks = {
        "straight_routes_disabled": values[5] == [],
        "platforms_disabled": bool(values[7]) and not any(
            config.get("enabled", False) for config in values[7]
        ),
        "formation_disabled": not values[10].get("enabled", False),
        "sectioning_disabled": not values[11].get("enabled", False),
        "template_assembly_disabled": not values[13].get("enabled", False),
        "assembly_labels_disabled": not values[14].get("enabled", False),
        "production_export_enabled": production.get("enabled") is True,
        "production_directory": production.get("output_directory") == str(output_directory),
        "all_formats": production.get("formats") == {
            key: True for key in EXPORT_FORMATS
        },
        ("overwrite_choice" if STAGING_BARRIER else "non_overwrite"): (
            production.get("overwrite_existing") is STAGING_BARRIER
        ),
        "manifest": production.get("create_manifest") is manifest,
        "combined": production.get("create_combined_files") is True,
        "open_directory_choice": production.get("open_output_directory") is ATOMIC_SET,
        "replace_output": values[17] == module.OUTPUT_REPLACE,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError(
            "Unexpected create-time export input(s): {}".format(", ".join(failed))
        )
    for selection in (
        "track_template_compound_2d",
        "track_template_compound_3d",
        "track_centrelines",
    ):
        if production.get("selections", {}).get(selection) is not True:
            raise ValueError("Create-time export omits {}".format(selection))
    return {
        "checks": checks,
        "output_directory": str(output_directory),
        "formats": dict(production["formats"]),
        "selections": dict(production["selections"]),
    }


def _run_scenario(
    name, output_directory, expected_initial_directory, inject_failure,
    *, inject_close_failure=False, manifest=True, publication_failure=None,
    inventory_failure=None,
):
    active_document = App.ActiveDocument
    if active_document is None:
        raise RuntimeError("The create-time export scenario lost its active document")
    before = ordinary_track_document_snapshot(module, active_document)
    destination_before = _destination_files(output_directory)
    output_directory_existed = output_directory.exists()
    state = {
        "name": name,
        "inject_final_task_failure": bool(inject_failure),
        "active": True,
        "seen": set(),
        "curve_dialogs": 0,
        "replacement_questions": [],
        "export_summary_dialogs": [],
        "final_success_dialogs": [],
        "unexpected_dialogs": [],
        "monitor_errors": [],
        "preflight_calls": [],
        "dispatch_calls": [],
        "production_export_calls": [],
        "summary_payloads": [],
        "injection_calls": 0,
        "inside_production_export": False,
        "inject_close_failure": inject_close_failure,
    }

    original_reader = module.read_last_dialog_inputs
    original_preflight = module.run_production_preflight
    original_dispatch = module.dispatch_freecad_export
    original_export = module.run_production_export
    original_show_summary = module.show_production_export_summary
    original_open_directory = module.open_export_directory
    state["open_directory_calls"] = []
    if ISOLATED_EXPORT:
        state["destination_before"] = destination_before
        state["staged_manifest_calls"] = 0
        state["preflight_warning_questions"] = []

    def require_unpublished_finals(path):
        if _destination_files(output_directory) != destination_before:
            raise RuntimeError("Core export published before staging completed")
        if ATOMIC_SET and pathlib.Path(state["planned_child"]).exists():
            raise RuntimeError("Core output child visible before all members are ready")
        if pathlib.Path(path).resolve().parent == output_directory.resolve():
            raise RuntimeError("Core export generated a payload at a final path")

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
            "task_count": len((kwargs.get("plan") or {}).get("tasks", [])),
            "probe_export_bounds": bool(kwargs.get("probe_export_bounds", True)),
            "issue_counts": module.summarise_preflight(issues),
            "issue_codes": [str(issue.get("issue_code") or "") for issue in issues],
        })
        return issues

    def measured_dispatch(export_document, task, path):
        active_name = str(getattr(active_document, "Name", "") or "")
        export_name = str(getattr(export_document, "Name", "") or "")
        if ISOLATED_EXPORT:
            kind = (
                "deliverable" if state["inside_production_export"]
                else "preflight_probe"
            )
        else:
            kind = "deliverable" if export_name == active_name else "preflight_probe"
        deliverable_index = 1 + sum(
            item["kind"] == "deliverable" for item in state["dispatch_calls"]
        )
        final_name = os.path.basename(str(task.get("path") or ""))
        item = {
            "kind": kind,
            "format": str(task.get("format") or ""),
            "combined": bool(task.get("combined", False)),
            "record_count": len(task.get("records") or []),
            "document": export_name,
            "final_name": final_name,
            "temporary_name": os.path.basename(str(path)),
        }
        if kind == "deliverable":
            item["deliverable_index"] = deliverable_index
            if ISOLATED_EXPORT:
                require_unpublished_finals(path)
                item["finals_unchanged_before_generation"] = True
                if export_document is active_document:
                    raise RuntimeError("Serializer received editable document")
                item["isolated_document"] = True
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        rss_before = _current_rss_mb()
        objects_before = len(export_document.Objects)
        try:
            if inject_failure and kind == "deliverable" and deliverable_index == EXPECTED_TASK_COUNT:
                if final_name != CREATE_TIME_EXPORT_FAILED_FILENAME:
                    raise RuntimeError(
                        "Final create-time task was {}, expected {}".format(
                            final_name, CREATE_TIME_EXPORT_FAILED_FILENAME
                        )
                    )
                state["injection_calls"] += 1
                raise RuntimeError(CREATE_TIME_EXPORT_FAILURE_MESSAGE)
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

    def measured_manifest(path, rows):
        require_unpublished_finals(path)
        state["staged_manifest_calls"] += 1
        return original_export.write_export_manifest(path, rows)

    def measured_export(*args, **kwargs):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        rss_before = _current_rss_mb()
        objects_before = len(active_document.Objects)
        export_call = original_export
        if ATOMIC_SET:
            plan = args[1]
            state["planned_child"] = plan["output_directory"]
            state["planned_paths"] = [task["path"] for task in plan["tasks"]]
            state["planned_manifest"] = plan.get("manifest_path", "")
            state["planned_dependency"] = plan["dependency_manifest_path"]
            if pathlib.Path(state["planned_dependency"]) != (
                pathlib.Path(state["planned_child"])
                / dependency_witness.DEPENDENCY_FILENAME
            ):
                raise RuntimeError("Core planned an incorrect dependency JSON path")
            if pathlib.Path(state["planned_child"]).parent != output_directory:
                raise RuntimeError("Core planned a child outside the selected parent")
            if any(pathlib.Path(path).parent != pathlib.Path(state["planned_child"])
                   for path in state["planned_paths"]):
                raise RuntimeError("Core planned a member outside its child")
        if ISOLATED_EXPORT:
            export_call = dataclasses.replace(
                original_export,
                dispatch_export_task=measured_dispatch,
                write_export_manifest=measured_manifest,
            )
        if ATOMIC_SET:
            from tracktemplate.adapters.export.core_layout_set import CoreLayoutExportSetFiles

            class FaultFiles(CoreLayoutExportSetFiles):
                def publish(self):
                    child = pathlib.Path(state["planned_child"])
                    if publication_failure == "collision":
                        child.mkdir()
                        (child / "foreign.txt").write_text("preserve foreign output\n")
                    if publication_failure == "publication":
                        raise OSError("controlled GUI publication failure")
                    super().publish()
                    if publication_failure == "postpublication":
                        raise OSError("controlled GUI postpublication diagnostic")

            settings = next(
                obj for obj in active_document.Objects
                if getattr(obj, "GeneratedRole", None) == "Settings"
                and getattr(obj, "TemplateSetID", None) == args[3]
            )
            state["persisted_generation_origin"] = settings.GeneratorVersion
            if not callable(original_export.prepare_dependency_manifest):
                raise RuntimeError("Normal Core lacks its dependency inventory")

            export_call = dataclasses.replace(
                export_call, export_files_factory=FaultFiles,
                prepare_dependency_manifest=(
                    None if inventory_failure == "missing"
                    else original_export.prepare_dependency_manifest
                ),
            )
        retained_documents = []
        if inject_close_failure:
            from tracktemplate.adapters.freecad.core_export_document import (
                CoreExportDocument,
            )

            class CloseFault:
                def __getattr__(self, attribute):
                    return getattr(App, attribute)

                def closeDocument(self, document_name):
                    if document_name in registry:
                        raise RuntimeError("Attempted to close prior document")
                    retained_documents.append(App.getDocument(document_name))
                    raise RuntimeError("controlled GUI isolated close failure")

            export_call = dataclasses.replace(
                export_call,
                export_dispatcher_factory=lambda serializer: (
                    CoreExportDocument(serializer, app=CloseFault())
                ),
            )
        restore_inventory = None
        if ATOMIC_SET and inventory_failure == "malformed":
            restore_inventory = dependency_witness.inject_duplicate_track_key(
                settings,
            )
            state["inventory_fault_boundary"] = (
                "Test-owned duplicate-key JSON installed before export entry"
            )
        if ATOMIC_SET:
            inventory_entry = dependency_witness.helpers.document_state(
                module, active_document,
            )
        witness = None
        if ISOLATED_EXPORT:
            source = next(
                obj for obj in active_document.Objects
                if "Shape" in obj.PropertiesList
                and not obj.Shape.isNull() and obj.Shape.Edges
            )
            witness = App.newDocument("CoreExportSelectionWitness")
            witness_object = witness.addObject("Part::Feature", "Witness")
            witness_object.Shape = source.Shape.copy()
            witness.recompute()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(
                active_document.Name, source.Name, "Edge1", 1.0, 2.0, 3.0,
            )
            Gui.Selection.addSelection(witness.Name, witness_object.Name)
            App.setActiveDocument(witness.Name)
            Gui.Selection.setPreselection(
                witness_object, "Edge1", 4.0, 5.0, 6.0,
            )
            registry = dict(App.listDocuments())
            selection = _isolation_selection()
            preselection = _isolation_preselection()
            if len(selection) != 2:
                raise RuntimeError("Selection witness was not established")
            if preselection[0] != witness.Name:
                raise RuntimeError("Preselection witness was not established")
            document_before = ordinary_track_document_snapshot(
                module, active_document
            )
            history = (
                active_document.UndoCount, active_document.RedoCount,
                tuple(active_document.UndoNames),
                tuple(active_document.RedoNames),
            )
            visibility = {
                obj.Name: obj.ViewObject.Visibility
                for obj in active_document.Objects
            }
        try:
            state["inside_production_export"] = True
            summary = export_call(*args, **kwargs)
            if ATOMIC_SET and dependency_witness.helpers.document_state(
                module, active_document,
            ) != inventory_entry:
                raise RuntimeError("Core changed exact export-entry document state")
            if ISOLATED_EXPORT:
                expected_registry = dict(registry)
                if inject_close_failure:
                    if len(retained_documents) != 1:
                        raise RuntimeError("Owned close fault did not run once")
                    retained_document = retained_documents[0]
                    expected_registry[retained_document.Name] = retained_document
                    if "controlled GUI isolated close failure" not in "\n".join(
                        summary["failure_details"]
                    ):
                        raise RuntimeError("Close diagnostic was not reported")
                if dict(App.listDocuments()) != expected_registry:
                    raise RuntimeError("Isolation changed document registry")
                if (
                    App.ActiveDocument is not witness
                    or App.activeDocument() is not witness
                ):
                    raise RuntimeError("Isolation changed active document")
                if _isolation_selection() != selection:
                    raise RuntimeError("Isolation changed committed selection")
                if _isolation_preselection() != preselection:
                    raise RuntimeError("Isolation changed preselection")
                if ordinary_track_document_snapshot(
                    module, active_document
                ) != document_before:
                    raise RuntimeError("Isolation changed editable state")
                if history != (
                    active_document.UndoCount, active_document.RedoCount,
                    tuple(active_document.UndoNames),
                    tuple(active_document.RedoNames),
                ):
                    raise RuntimeError("Isolation changed document history")
                if visibility != {
                    obj.Name: obj.ViewObject.Visibility
                    for obj in active_document.Objects
                }:
                    raise RuntimeError("Isolation changed object visibility")
                state["isolation"] = {
                    "registry_restored": not inject_close_failure,
                    "owned_documents_retained": len(retained_documents),
                    "other_active_document_restored": True,
                    "two_document_selection_restored": True,
                    "subelement_points_restored": True,
                    "preselection_restored": True,
                    "editable_state_history_visibility_unchanged": True,
                }
        finally:
            state["inside_production_export"] = False
            if restore_inventory is not None:
                restore_inventory()
            for retained_document in retained_documents:
                if App.listDocuments().get(retained_document.Name) is not retained_document:
                    raise RuntimeError("Fixture cleanup lost document identity")
                App.closeDocument(retained_document.Name)
            if witness is not None:
                App.closeDocument(witness.Name)
                App.setActiveDocument(active_document.Name)
        if STAGING_BARRIER and (inject_failure or inject_close_failure):
            task_results = summary.get("results") or []
            if len(task_results) != EXPECTED_TASK_COUNT or any(
                item.get("success") is not False for item in task_results
            ):
                raise RuntimeError("Staging abort reported published task success")
        item = _compact_summary(summary)
        if ATOMIC_SET:
            state["atomic_summary"] = {
                key: summary[key] for key in (
                    "publication_state", "output_directory", "manifest_path",
                    "dependency_manifest_path",
                )
            }
            for item_result, task in zip(summary["results"], args[1]["tasks"]):
                if item_result["task"] is not task:
                    raise RuntimeError("Core changed task identity")
        item.update({
            "wall_ms": (time.perf_counter() - wall_started) * 1000.0,
            "process_cpu_ms": (time.process_time() - cpu_started) * 1000.0,
            "rss_delta_mb": _current_rss_mb() - rss_before,
            "object_delta": len(active_document.Objects) - objects_before,
        })
        state["production_export_calls"].append(item)
        return summary

    def measured_show_summary(summary):
        state["summary_payloads"].append(_compact_summary(summary))
        return original_show_summary(summary)

    def monitor():
        if not state["active"]:
            return
        try:
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if not widget.isVisible():
                    continue
                identity = id(widget)
                if identity in state["seen"]:
                    continue
                if isinstance(widget, module.CurveInputDialog):
                    state["seen"].add(identity)
                    initial = _initial_dialog_contract(widget)
                    if initial["angle_degrees"] != 90.0:
                        raise ValueError("Create-time export did not load the +90 fixture")
                    expected_enabled = bool(expected_initial_directory)
                    initial_export = initial["production_export"]
                    if initial_export.get("enabled") is not expected_enabled:
                        raise ValueError("Create-time export loaded the wrong enabled state")
                    if initial_export.get("output_directory", "") != expected_initial_directory:
                        raise ValueError("Create-time export loaded the wrong output directory")
                    state["initial_dialog"] = initial
                    state["configured_dialog"] = _configure_dialog(
                        widget, output_directory, manifest=manifest
                    )
                    state["curve_dialogs"] += 1
                    widget.accept()
                    continue
                if not isinstance(widget, QtWidgets.QMessageBox):
                    continue
                state["seen"].add(identity)
                record = {
                    "title": str(widget.windowTitle() or ""),
                    "text": str(widget.text() or ""),
                    "informative_text": str(widget.informativeText() or ""),
                    "detailed_text": str(widget.detailedText() or ""),
                }
                yes_button = _yes_button(widget)
                if (
                    "Replace generated templates" in record["title"]
                    and yes_button is not None
                ):
                    state["replacement_questions"].append(record)
                    yes_button.click()
                elif (
                    STAGING_BARRIER and inject_failure
                    and "Production preflight warnings" in record["title"]
                    and yes_button is not None
                ):
                    state["preflight_warning_questions"].append(record)
                    yes_button.click()
                elif "Production export complete" in record["title"]:
                    if ISOLATED_EXPORT:
                        capture = run_directory / "{}-summary.png".format(name)
                        if not widget.grab().save(str(capture), "PNG"):
                            raise RuntimeError("Could not capture export summary")
                        state["summary_capture"] = str(capture)
                        state["summary_capture_sha256"] = hashlib.sha256(
                            capture.read_bytes()
                        ).hexdigest()
                    state["export_summary_dialogs"].append(record)
                    widget.accept()
                elif SUCCESS_TEXT in record["text"]:
                    state["final_success_dialogs"].append(record)
                    widget.accept()
                else:
                    state["unexpected_dialogs"].append(record)
                    widget.accept()
        except Exception as error:
            state["monitor_errors"].append(
                "{}: {}".format(type(error).__name__, error)
            )
            for widget in list(QtWidgets.QApplication.topLevelWidgets()):
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()
        QtCore.QTimer.singleShot(25, monitor)

    module.read_last_dialog_inputs = lambda _document: None
    module.run_production_preflight = measured_preflight
    module.dispatch_freecad_export = measured_dispatch
    module.run_production_export = measured_export
    module.show_production_export_summary = measured_show_summary
    if ATOMIC_SET:
        module.open_export_directory = lambda path: state["open_directory_calls"].append(path)
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    rss_before = _current_rss_mb()
    objects_before = len(active_document.Objects)
    QtCore.QTimer.singleShot(0, monitor)
    try:
        module.run_macro()
    finally:
        state["active"] = False
        module.read_last_dialog_inputs = original_reader
        module.run_production_preflight = original_preflight
        module.dispatch_freecad_export = original_dispatch
        module.run_production_export = original_export
        module.show_production_export_summary = original_show_summary
        module.open_export_directory = original_open_directory

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
    after = ordinary_track_document_snapshot(module, active_document)
    normalised_after = (
        _atomic_document_contract(after, manifest=manifest) if ATOMIC_SET else
        create_time_export_document_snapshot(
            after,
            enforce_expected_hash=ENFORCE_FROZEN_WORKFLOW_HASHES,
            expected_overwrite_existing=STAGING_BARRIER,
        )
    )
    if normalised_after["output_directory"] != str(output_directory):
        raise RuntimeError("Create-time export persisted the wrong output directory")
    state["before_semantic_sha256"] = before["semantic_sha256"]
    state["after_semantic_sha256"] = after["semantic_sha256"]
    state["normalised_after_semantic_sha256"] = normalised_after["semantic_sha256"]

    if state["monitor_errors"]:
        raise RuntimeError("; ".join(state["monitor_errors"]))
    if state["curve_dialogs"] != 1:
        raise RuntimeError("Create-time export did not show exactly one input dialog")
    if len(state["replacement_questions"]) != 1:
        raise RuntimeError("Create-time export did not show one replacement question")
    if len(state["export_summary_dialogs"]) != 1:
        raise RuntimeError("Create-time export did not show one export summary")
    if len(state["final_success_dialogs"]) != 1:
        raise RuntimeError("Create-time export did not show one final success dialog")
    if state["unexpected_dialogs"]:
        raise RuntimeError(
            "Unexpected create-time export dialogs: {}".format(state["unexpected_dialogs"])
        )
    if len(state["preflight_calls"]) != 1:
        raise RuntimeError("Create-time export did not run one production preflight")
    preflight = state["preflight_calls"][0]
    if preflight["task_count"] != EXPECTED_TASK_COUNT:
        raise RuntimeError("Create-time export planned an unexpected task count")
    if ATOMIC_SET:
        _validate_atomic_scenario(state, output_directory, destination_before,
                                  manifest, inject_failure, publication_failure,
                                  inventory_failure)
        state.pop("active", None)
        state.pop("seen", None)
        return state, after, normalised_after
    expected_warning_count = 3 if STAGING_BARRIER and inject_failure else 0
    expected_issue_codes = (
        [] if output_directory_existed
        else ["OUTPUT_DIRECTORY_WILL_BE_CREATED"]
    )
    expected_information_count = len(expected_issue_codes)
    expected_issue_codes.extend(
        ["EXISTING_FILE_OVERWRITE"] * expected_warning_count
    )
    if (
        preflight["issue_counts"].get("blocking", 0)
        or preflight["issue_counts"].get("Error", 0)
        or preflight["issue_counts"].get("Warning", 0) != expected_warning_count
        or preflight["issue_counts"].get("Information", 0)
        != expected_information_count
        or preflight["issue_codes"] != expected_issue_codes
    ):
        raise RuntimeError(
            "Unexpected create-time export preflight: {}".format(preflight)
        )
    probe_calls = [item for item in state["dispatch_calls"] if item["kind"] == "preflight_probe"]
    deliverable_calls = [item for item in state["dispatch_calls"] if item["kind"] == "deliverable"]
    expected_deliverables = 1 if inject_close_failure else EXPECTED_TASK_COUNT
    if len(probe_calls) != 10 or len(deliverable_calls) != expected_deliverables:
        raise RuntimeError(
            "Unexpected create-time dispatch counts: {}/{}".format(
                len(probe_calls), len(deliverable_calls)
            )
        )
    planned_files = [item["final_name"] for item in deliverable_calls]
    if not inject_close_failure and set(planned_files + ["Curve_Set_001_Export_Manifest.csv"]) != set(EXPECTED_EXPORT_FILENAMES):
        raise RuntimeError("Create-time export planned unexpected filenames")
    state["planned_files"] = planned_files + ["Curve_Set_001_Export_Manifest.csv"]
    if len(state["production_export_calls"]) != 1 or len(state["summary_payloads"]) != 1:
        raise RuntimeError("Create-time export did not produce one summary payload")
    summary = state["summary_payloads"][0]
    expected_summary = {
        "successful_files": 13 if inject_failure else 14,
        "failed_files": 1 if inject_failure else 0,
        "skipped_objects": 0,
        "formats": ["DXF", "STEP", "STL", "SVG"],
        "manifest_requested": True,
        "manifest_created": True,
    }
    if STAGING_BARRIER and (inject_failure or inject_close_failure):
        expected_summary.update({
            "successful_files": 0,
            "failed_files": EXPECTED_TASK_COUNT,
            "formats": [],
            "manifest_created": False,
        })
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise RuntimeError(
                "Unexpected create-time {} summary: {}".format(name, summary)
            )
    if inject_failure or inject_close_failure:
        if state["injection_calls"] != int(inject_failure):
            raise RuntimeError("The final-task failure injection did not run once")
        expected_error = (
            "controlled GUI isolated close failure" if inject_close_failure
            else CREATE_TIME_EXPORT_FAILURE_MESSAGE
        )
        if not any(expected_error in value for value in summary["failures"]):
            raise RuntimeError("The create-time failure summary omitted the injected reason")
        final_text = state["final_success_dialogs"][0]["text"]
        expected_counts = (
            "0 successful files; 13 failed" if STAGING_BARRIER
            else "13 successful files; 1 failed"
        )
        if expected_counts not in final_text:
            raise RuntimeError("The final dialog omitted create-time failure counts")
        if ISOLATED_EXPORT:
            if "Successful files: 0" not in state[
                "export_summary_dialogs"
            ][0]["informative_text"]:
                raise RuntimeError("The export dialog reported false success")
            if _destination_files(output_directory) != destination_before:
                raise RuntimeError("Staging failure changed destination bytes")
    else:
        if state["injection_calls"] or summary["failures"]:
            raise RuntimeError("The create-time success scenario reported a failure")
    if STAGING_BARRIER:
        if any(path.is_dir() for path in output_directory.iterdir()):
            raise RuntimeError("Core export retained a temporary directory")
        if len(state["preflight_warning_questions"]) != int(inject_failure):
            raise RuntimeError("Unexpected overwrite confirmation count")
        if state["staged_manifest_calls"] != (
            0 if inject_failure or inject_close_failure else 1
        ):
            raise RuntimeError("Unexpected staged manifest generation count")
        state["destination_after"] = _destination_files(output_directory)
    if len(active_document.Objects) != 9:
        raise RuntimeError("Create-time export retained an unexpected object count")
    temporary_objects = [
        str(obj.Name) for obj in active_document.Objects
        if str(obj.Name).startswith("TemporaryProductionExport_")
    ]
    if temporary_objects:
        raise RuntimeError(
            "Create-time export retained temporary objects: {}".format(temporary_objects)
        )
    state.pop("active", None)
    state.pop("seen", None)
    return state, after, normalised_after


def _isolation_selection():
    """Observe logical selection and exact picked points across documents."""
    return [
        (
            item.DocumentName, item.ObjectName, tuple(item.SubElementNames),
            tuple((point.x, point.y, point.z) for point in item.PickedPoints),
            Gui.Selection.isSelected(item.Object, "", 0),
        )
        for item in Gui.Selection.getSelectionEx("*", 0)
    ]


def _isolation_preselection():
    selected = Gui.Selection.getPreselection()
    return (
        selected.DocumentName, selected.ObjectName,
        tuple(selected.SubElementNames),
        tuple((point.x, point.y, point.z) for point in selected.PickedPoints),
    )


def _atomic_document_contract(snapshot, *, manifest):
    """Check authorised UI choices before comparing unchanged geometry."""
    candidate = copy.deepcopy(snapshot)
    for owner in ("settings", "template"):
        config = candidate["semantic"]["persistence"][owner]["values"][
            "ProductionExportConfigurationJSON"
        ]
        if config["create_manifest"] is not manifest or config["open_output_directory"] is not True:
            raise RuntimeError("Atomic export persisted different CSV/Open Folder choices")
        config["create_manifest"] = True
        config["open_output_directory"] = False
    return create_time_export_document_snapshot(candidate, enforce_expected_hash=False)


def _validate_atomic_scenario(
    state, parent, before, manifest, preparation_failure, publication_failure,
    inventory_failure,
):
    summary = state["summary_payloads"][0]
    atomic = state["atomic_summary"]
    child = pathlib.Path(state["planned_child"])
    published = (not preparation_failure and not inventory_failure
                 and publication_failure in (None, "postpublication"))
    if atomic["publication_state"] != ("published" if published else "not-published"):
        raise RuntimeError("Core reported the wrong publication state")
    expected_directory = str(child if published else parent)
    if atomic["output_directory"] != expected_directory:
        raise RuntimeError("Core summary selected the wrong directory")
    if state["open_directory_calls"] != [expected_directory]:
        raise RuntimeError("Open Folder did not receive the summary directory")
    if atomic["manifest_path"] != (state["planned_manifest"] if published and manifest else ""):
        raise RuntimeError("Core returned an incorrect CSV path")
    if atomic["dependency_manifest_path"] != (
        state["planned_dependency"] if published else ""
    ):
        raise RuntimeError("Core returned an incorrect dependency JSON path")
    if summary["successful_files"] != (
        EXPECTED_TASK_COUNT + int(manifest) + 1 if published else 0
    ):
        raise RuntimeError("Core lost or invented published successes")
    expected_failures = (1 if publication_failure == "postpublication" else
                         EXPECTED_TASK_COUNT + int(bool(publication_failure or inventory_failure))
                         if not published else 0)
    if summary["failed_files"] != expected_failures:
        raise RuntimeError("Core diagnostics count differs: {}".format(summary))
    if summary["manifest_requested"] is not manifest or summary["manifest_created"] is not (published and manifest):
        raise RuntimeError("Core reported an incorrect optional CSV outcome")
    if summary["formats"] != (["DXF", "STEP", "STL", "SVG"] if published else []):
        raise RuntimeError("Core reported incorrect published formats")
    preflight = state["preflight_calls"][0]
    if preflight["issue_counts"].get("blocking", 0) or preflight["issue_counts"].get("Error", 0):
        raise RuntimeError("Atomic GUI preflight blocked the fixture")
    if preflight["issue_codes"] != ["OUTPUT_DIRECTORY_WILL_BE_CREATED"]:
        raise RuntimeError("Atomic GUI preflight did not identify its fresh child")
    probes = [item for item in state["dispatch_calls"] if item["kind"] == "preflight_probe"]
    deliverables = [item for item in state["dispatch_calls"] if item["kind"] == "deliverable"]
    if len(probes) != 10 or len(deliverables) != (
        0 if inventory_failure else EXPECTED_TASK_COUNT
    ):
        raise RuntimeError("Atomic GUI dispatch count differs")
    if state["staged_manifest_calls"] != int(
        manifest and not preparation_failure and not inventory_failure
    ):
        raise RuntimeError("Atomic GUI built an unrequested or premature CSV")
    if _destination_files(parent) != before:
        raise RuntimeError("Atomic GUI changed existing parent outputs")
    if list(parent.glob(".tracktemplate_core_export_set_*")):
        raise RuntimeError("Atomic GUI retained owned unpublished files")
    if published:
        expected_names = {pathlib.Path(path).name for path in state["planned_paths"]}
        expected_names.add(dependency_witness.DEPENDENCY_FILENAME)
        if manifest:
            expected_names.add(pathlib.Path(state["planned_manifest"]).name)
        if {path.name for path in child.iterdir()} != expected_names:
            raise RuntimeError("Published Core inventory differs from the plan")
        if manifest:
            with pathlib.Path(atomic["manifest_path"]).open(newline="", encoding="utf-8-sig") as stream:
                rows = list(csv.DictReader(stream))
            if {row["Full export path"] for row in rows} != set(state["planned_paths"]):
                raise RuntimeError("CSV does not identify final child members")
            if any(row["Export status"] != "Success" for row in rows):
                raise RuntimeError("Complete-set CSV reports an unsuccessful member")
        expected_paths = list(state["planned_paths"])
        if manifest:
            expected_paths.append(state["planned_manifest"])
        state["dependency_manifest"] = (
            dependency_witness.dependency_manifest_witness(
                atomic["dependency_manifest_path"], expected_paths,
                state["persisted_generation_origin"],
            )
        )
        if str(child) not in state["export_summary_dialogs"][0]["informative_text"]:
            raise RuntimeError("Visible summary omitted published child path")
    elif publication_failure == "collision":
        if {path.name for path in child.iterdir()} != {"foreign.txt"}:
            raise RuntimeError("Collision altered the foreign child inventory")
        if (child / "foreign.txt").read_text() != "preserve foreign output\n":
            raise RuntimeError("Collision changed foreign bytes")
    elif child.exists():
        raise RuntimeError("Failed atomic export left a visible child")
    visible = state["export_summary_dialogs"][0]["informative_text"]
    expected_csv = (atomic["manifest_path"] if published and manifest
                    else "Requested but not created" if manifest else "Not requested")
    expected_json = atomic["dependency_manifest_path"] if published else "Not created"
    if ("Manifest: CSV: " + expected_csv not in visible
            or "Dependency JSON: " + expected_json not in visible
            or "Private development only; output rights remain unresolved." not in visible):
        raise RuntimeError("Visible summary misstates CSV, JSON or rights")
    expected_inventory_error = {
        "malformed": "duplicate JSON key",
        "missing": "dependency inventory is unavailable",
    }.get(inventory_failure)
    if expected_inventory_error and not any(
        expected_inventory_error in value for value in summary["failures"]
    ):
        raise RuntimeError("Inventory refusal omitted its diagnostic")
    if preparation_failure and not any(CREATE_TIME_EXPORT_FAILURE_MESSAGE in value for value in summary["failures"]):
        raise RuntimeError("Preparation failure omitted its diagnostic")
    if publication_failure in {"publication", "postpublication"} and not any(
        "controlled GUI " + publication_failure in value for value in summary["failures"]
    ):
        raise RuntimeError("Publication failure omitted its diagnostic")
    if len(App.ActiveDocument.Objects) != 9:
        raise RuntimeError("Atomic export changed editable object inventory")
    state["atomic_checks"] = {
        "old_parent_outputs_unchanged": True, "planned_member_identity_preserved": True,
        "complete_child_inventory": published, "open_folder_path_verified": True,
        "csv_final_paths_verified": published and manifest,
        "mandatory_json_verified": published,
        "inventory_refusal_before_serializers": bool(inventory_failure),
        "visible_csv_json_rights_distinction": True,
        "published_successes_preserved_after_diagnostic": publication_failure == "postpublication",
    }


def _run_atomic_recipe():
    parent = run_directory / "atomic-core-output-parent"
    parent.mkdir()
    old = parent / "previous-complete-set"
    old.mkdir()
    (old / "operator-output.svg").write_text("preserve previous output\n")
    (parent / "operator-output.svg").write_text("preserve parent output\n")
    old_witness = {path: (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                   for path in (old / "operator-output.svg", parent / "operator-output.svg")}
    previous_directory = ""
    published_witnesses = {}
    normalised = None
    first_child = None
    for name, manifest, preparation, publication, inventory in (
        ("create_time_export_success", True, False, None, None),
        ("create_time_export_no_csv", False, False, None, None),
        ("create_time_export_final_task_failure", True, True, None, None),
        ("create_time_export_collision", True, False, "collision", None),
        ("create_time_export_publication_failure", True, False, "publication", None),
        ("create_time_export_postpublication", True, False, "postpublication", None),
        ("create_time_export_malformed_inventory", True, False, None, "malformed"),
        ("create_time_export_missing_inventory", True, False, None, "missing"),
    ):
        scenario, snapshot, contract = _run_scenario(
            name, parent, previous_directory, preparation,
            manifest=manifest, publication_failure=publication,
            inventory_failure=inventory,
        )
        result["scenarios"].append(scenario)
        if normalised is None:
            normalised = contract
            first_child = pathlib.Path(scenario["planned_child"])
            compare_create_time_document_to_base(
                _document_contract(initial_document), _document_contract(snapshot),
            )
        elif contract["semantic_sha256"] != normalised["semantic_sha256"]:
            raise RuntimeError("Atomic scenario changed generated document semantics")
        for path, witness in old_witness.items():
            if (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes()) != witness:
                raise RuntimeError("Atomic scenario changed prior output identity or bytes")
        for path, witness in published_witnesses.items():
            if (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes()) != witness:
                raise RuntimeError("A subsequent Generate changed a prior published set")
        if scenario["atomic_summary"]["publication_state"] == "published":
            for path in pathlib.Path(scenario["planned_child"]).iterdir():
                published_witnesses[path] = (
                    path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes(),
                )
        previous_directory = str(parent)
    output = export_directory_snapshot(first_child)
    # The JSON has its own exact schema and hash witness above. Retain the
    # frozen payload and CSV comparison over exactly the previous inventory.
    if set(output["files"]) != (
        set(EXPECTED_EXPORT_FILENAMES) | {dependency_witness.DEPENDENCY_FILENAME}
    ):
        raise RuntimeError("Core payload comparison excluded an unexpected file")
    variant = export_variant_snapshot(output)
    logical_hash = validate_export_snapshot(variant)
    metrics = format_export_metrics(module, first_child, variant, shape_summary)
    if format_metrics_sha256(metrics) != EXPECTED_EXPORT_METRICS_SHA256:
        raise RuntimeError("Atomic Core geometry metrics changed")
    result["success_output"] = {
        "file_count": len(output["files"]), "logical_sha256": logical_hash,
        "format_metrics_sha256": format_metrics_sha256(metrics), "format_metrics": metrics,
    }
    doc = App.ActiveDocument
    doc.recompute()
    before_save = ordinary_track_document_snapshot(module, doc)
    doc.save()
    saved_path, saved_name = str(doc.FileName), str(doc.Name)
    App.closeDocument(saved_name)
    doc = App.openDocument(saved_path)
    after_save = ordinary_track_document_snapshot(module, doc)
    if after_save != before_save:
        raise RuntimeError("Atomic save/reopen changed exact document snapshot")
    reopened = _atomic_document_contract(after_save, manifest=True)
    if reopened["output_directory"] != str(parent):
        raise RuntimeError("Atomic save/reopen did not retain selected parent")
    result["save_reopen"] = {"path": saved_path, "objects": len(doc.Objects),
                             "selected_parent_preserved": True,
                             "exact_document_snapshot_preserved": True}
    result["normalised_document_semantic_sha256"] = normalised["semantic_sha256"]
    result["failure_output"] = {"old_outputs_identity_bytes_preserved": True,
                                "collision_owner_preserved": True}


parameter_group = App.ParamGet(module.LAST_INPUTS_PARAMETER_PATH)
preference_keys = (
    module.LAST_INPUTS_PARAMETER_KEY,
    module.LAST_INPUTS_DOCUMENT_MAP_KEY,
    module.MATERIAL_REPORT_PARAMETER_KEY,
)
preferences_before = {
    key: str(parameter_group.GetString(key, "") or "") for key in preference_keys
}
initial_base = ordinary_track_snapshot(
    module,
    document,
    enforce_expected_hash=ENFORCE_FROZEN_WORKFLOW_HASHES,
    expected_macro_version=BASE_MACRO_VERSION,
)
initial_document = ordinary_track_document_snapshot(module, document)
result = {
    "schema_version": CREATE_TIME_EXPORT_RECIPE_SCHEMA_VERSION,
    "source_document": str(document.FileName),
    "initial_base_semantic_sha256": initial_base["semantic_sha256"],
    "initial_document_semantic_sha256": initial_document["semantic_sha256"],
    "scenarios": [],
}

try:
    if ATOMIC_SET:
        _run_atomic_recipe()
    else:
        success, success_document, normalised_success = _run_scenario(
            "create_time_export_success",
            success_directory,
            "",
            inject_failure=False,
        )
        compare_create_time_document_to_base(
            _document_contract(initial_document),
            _document_contract(success_document),
        )
        result["scenarios"].append(success)

        if STAGING_BARRIER:
            seeded_destination = _seed_staging_failure_directory()
        failure, failure_document, normalised_failure = _run_scenario(
            "create_time_export_final_task_failure",
            failure_directory,
            str(success_directory),
            inject_failure=True,
        )
        result["scenarios"].append(failure)
        if normalised_success["semantic_sha256"] != normalised_failure["semantic_sha256"]:
            raise RuntimeError("Create-time success/failure document semantics differ")
        result["normalised_document_semantic_sha256"] = normalised_success[
            "semantic_sha256"
        ]
        if STAGING_BARRIER:
            close_failure, _closed_document, normalised_close = _run_scenario(
                "create_time_export_isolated_close_failure",
                isolation_failure_directory,
                str(failure_directory),
                inject_failure=False,
                inject_close_failure=True,
            )
            result["scenarios"].append(close_failure)
            if normalised_close["semantic_sha256"] != normalised_success["semantic_sha256"]:
                raise RuntimeError("Close failure changed generated document state")
            if list(isolation_failure_directory.iterdir()):
                raise RuntimeError("Close failure published output")
            result["isolation_close_failure_output"] = {
                "successful_files": 0, "new_final_files": [],
                "retained_owned_document_reported": True,
                "editable_document_preserved": True,
            }

        success_complete = export_directory_snapshot(success_directory)
        success_variant = export_variant_snapshot(success_complete)
        success_hash = validate_export_snapshot(success_variant)
        if (
            ENFORCE_FROZEN_WORKFLOW_HASHES
            and success_hash != EXPECTED_CREATE_TIME_LOGICAL_EXPORT_SHA256
        ):
            raise RuntimeError(
                "Unexpected create-time export serialization hash: {}".format(
                    success_hash
                )
            )
        format_metrics = format_export_metrics(
            module, success_directory, success_variant, shape_summary
        )
        metrics_hash = format_metrics_sha256(format_metrics)
        if metrics_hash != EXPECTED_EXPORT_METRICS_SHA256:
            raise RuntimeError(
                "Create-time export production metrics differ from selected export: {}".format(
                    metrics_hash
                )
            )
        result["success_output"] = {
            "file_count": len(success_complete["files"]),
            "directories": list(success_complete["directories"]),
            "logical_sha256": success_hash,
            "selected_export_logical_sha256": EXPECTED_LOGICAL_EXPORT_SHA256,
            "serialization_matches_selected_export": (
                success_hash == EXPECTED_LOGICAL_EXPORT_SHA256
            ),
            "format_metrics_sha256": metrics_hash,
            "format_metrics": format_metrics,
        }

        if STAGING_BARRIER:
            result["failure_output"] = {
                "prepublication_abort": True,
                "successful_files": 0,
                "new_final_files": [],
                "existing_destination_files": seeded_destination,
                "destination_bytes_preserved": (
                    _destination_files(failure_directory) == seeded_destination
                ),
                "staging_directories": [],
            }
        else:
            failure_complete = export_directory_snapshot(failure_directory)
            result["failure_output"] = validate_create_time_failure_snapshot(
                failure_complete,
                success_variant,
                enforce_expected_hash=ENFORCE_FROZEN_WORKFLOW_HASHES,
            )

        document = App.ActiveDocument
        persistence_started = time.perf_counter()
        recompute_started = time.perf_counter()
        document.recompute()
        recompute_ms = (time.perf_counter() - recompute_started) * 1000.0
        save_started = time.perf_counter()
        document.save()
        save_ms = (time.perf_counter() - save_started) * 1000.0
        saved_path = str(document.FileName)
        saved_name = str(document.Name)
        reopen_started = time.perf_counter()
        App.closeDocument(saved_name)
        document = App.openDocument(saved_path)
        reopen_ms = (time.perf_counter() - reopen_started) * 1000.0
        reopened = ordinary_track_document_snapshot(module, document)
        normalised_reopened = create_time_export_document_snapshot(
            reopened,
            enforce_expected_hash=ENFORCE_FROZEN_WORKFLOW_HASHES,
            expected_overwrite_existing=STAGING_BARRIER,
        )
        final_directory = (
            isolation_failure_directory if STAGING_BARRIER else failure_directory
        )
        if normalised_reopened["output_directory"] != str(final_directory):
            raise RuntimeError("Save/reopen changed the persisted export directory")
        if normalised_reopened["semantic_sha256"] != normalised_failure["semantic_sha256"]:
            raise RuntimeError("Save/reopen changed create-time export document semantics")
        result["save_reopen"] = {
            "path": saved_path,
            "objects": len(document.Objects),
            "normalised_semantic_sha256": normalised_reopened["semantic_sha256"],
            "measurement": {
                "wall_ms": (time.perf_counter() - persistence_started) * 1000.0,
                "recompute_ms": recompute_ms,
                "save_ms": save_ms,
                "close_reopen_ms": reopen_ms,
            },
        }
finally:
    for key, value in preferences_before.items():
        parameter_group.SetString(key, value)
    result["preference_store_restored"] = all(
        str(parameter_group.GetString(key, "") or "") == value
        for key, value in preferences_before.items()
    )

if not result["preference_store_restored"]:
    raise RuntimeError("The create-time export recipe did not restore preferences")
if globals().get("TRACKTEMPLATE_CAPTURE_WORKFLOW_RESULT", False):
    TRACKTEMPLATE_WORKFLOW_RESULT = result
else:
    print(json.dumps(result, sort_keys=True))
