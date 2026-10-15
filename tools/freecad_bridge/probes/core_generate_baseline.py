"""Measure three actual Core Generate actions in a copied GUI document.

This probe requires the normal modular composition loader. Dialog setup
and polling belong to the measured action; deep checks and capture do not.
Same-process regeneration is not unchanged-result cache reuse. These
measurements supply no budget, improvement or phase acceptance.
"""

import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtWidgets

from tools.freecad_bridge.freecad_export_metrics import format_export_metrics
from tools.freecad_bridge.ordinary_track_edit_recipe import (
    normalise_version_migration_snapshot,
)
from tools.freecad_bridge.ordinary_track_export_recipe import (
    EXPECTED_EXPORT_FILENAMES,
    EXPECTED_EXPORT_METRICS_SHA256,
    EXPECTED_TASK_COUNT,
    EXPORT_FORMATS,
    compare_create_time_document_to_base,
    create_time_export_document_snapshot,
    export_directory_snapshot,
    export_variant_snapshot,
    format_metrics_sha256,
    validate_export_snapshot,
)
from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_TRACK_CONFIGURATION,
    ordinary_track_document_snapshot,
    ordinary_track_snapshot,
    shape_summary,
)


PROFILE_ID = "phase9b-core-generate-diagnostic-v1"
HOST_PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
)
SUCCESS_TEXT = "Curve and straight-track outputs created successfully"
SENTINEL = "CORE_GENERATE_BASELINE_PASS"


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _file_state(directory):
    return {
        str(path.relative_to(directory)): (
            path.stat().st_ino, path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def _preferences(group):
    return {
        "values": sorted(group.GetContents() or ()),
        "groups": {name: _preferences(group.GetGroup(name))
                   for name in sorted(group.GetGroups())},
    }


def _restore_preferences(group, snapshot):
    for kind, key, _value in group.GetContents() or ():
        getattr(group, "Rem" + kind)(key)
    for kind, key, value in snapshot["values"]:
        getattr(group, "Set" + kind)(key, value)
    for name in set(group.GetGroups()) - set(snapshot["groups"]):
        group.RemGroup(name)
    for name, child in snapshot["groups"].items():
        _restore_preferences(group.GetGroup(name), child)


def _configure(dialog, module, parent):
    dialog.transition_box.setValue(600.0)
    dialog.radius_box.setValue(600.0)
    dialog.angle_box.setValue(90.0)
    dialog.main_width_box.setValue(32.0)
    dialog.parallel_count_box.setValue(1)
    dialog._set_parallel_count(1)
    dialog._populate_row(0, module.clone_track_config(
        EXPECTED_TRACK_CONFIGURATION[0], 600.0,
    ))
    index = dialog.output_mode_box.findText(module.OUTPUT_REPLACE)
    _require(index >= 0, "Replace output choice is absent")
    dialog.output_mode_box.setCurrentIndex(index)
    dialog.production_export_enabled_box.setChecked(True)
    dialog.production_export_directory_box.setText(str(parent))
    for box in (
        dialog.production_include_role_box,
        dialog.production_include_track_box,
        dialog.production_include_section_box,
        dialog.production_each_section_box,
        dialog.production_combined_box,
        dialog.production_manifest_box,
    ):
        box.setChecked(True)
    dialog.production_overwrite_box.setChecked(False)
    dialog.production_open_directory_box.setChecked(False)
    for name in EXPORT_FORMATS:
        box = dialog.production_format_boxes[name]
        _require(box.isEnabled(), "Exporter is unavailable: " + name)
        box.setChecked(True)
    dialog._update_production_export_controls()
    values = dialog.values()
    _require(values[5] == [], "Straight routes are enabled")
    _require(values[7] and not any(item.get("enabled") for item in values[7]),
             "Platforms are enabled or configuration is absent")
    _require(all(not values[index].get("enabled")
                 for index in (10, 11, 13, 14)),
             "Unsupported generated features are enabled")
    _require(not dialog.production_overwrite_box.isEnabled(),
             "Expected atomic Core publication route")
    production = values[15]
    _require(production.get("formats") == {
        key: True for key in EXPORT_FORMATS
    },
             "Expected all four output formats")
    selections = production.get("selections", {})
    _require(all(selections.get(name) is True for name in (
        "track_template_compound_2d", "track_template_compound_3d",
        "track_centrelines",
    )), "Required output selections are absent")
    _require(production.get("output_directory") == str(parent)
             and production.get("enabled") is True
             and production.get("create_manifest") is True
             and production.get("open_output_directory") is False,
             "Production configuration differs")
    return copy.deepcopy(production)


def _measure_action(module, document, parent, action):
    state = {"inputs": [], "replace": [], "summary": [], "success": [],
             "unexpected": [], "monitor_errors": []}
    seen = set()

    def monitor():
        try:
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if not widget.isVisible() or id(widget) in seen:
                    continue
                if isinstance(widget, module.CurveInputDialog):
                    seen.add(id(widget))
                    state["inputs"].append(_configure(widget, module, parent))
                    widget.accept()
                elif isinstance(widget, QtWidgets.QMessageBox):
                    seen.add(id(widget))
                    item = {"title": widget.windowTitle(),
                            "text": widget.text(),
                            "information": widget.informativeText(),
                            "details": widget.detailedText()}
                    if "Replace generated templates" in item["title"]:
                        button = widget.button(
                            QtWidgets.QMessageBox.StandardButton.Yes,
                        )
                        _require(button is not None,
                                 "Replace has no Yes button")
                        state["replace"].append(item)
                        button.click()
                    elif "Production export complete" in item["title"]:
                        state["summary"].append(item)
                        widget.accept()
                    elif SUCCESS_TEXT in item["text"]:
                        state["success"].append(item)
                        widget.accept()
                    else:
                        state["unexpected"].append(item)
                        widget.reject()
        except Exception as error:
            state["monitor_errors"].append(
                type(error).__name__ + ": " + str(error),
            )
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if (isinstance(widget, QtWidgets.QDialog)
                        and widget.isVisible()):
                    widget.reject()

    timer = QtCore.QTimer()
    timer.timeout.connect(monitor)
    action["objects_before"] = len(document.Objects)
    action["rss_before_mb"] = float(module._workflow_current_rss_mb())
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    timer.start(25)
    try:
        module.run_macro()
    finally:
        action["process_cpu_ms"] = (
            time.process_time() - cpu_started
        ) * 1000.0
        action["wall_ms"] = (time.perf_counter() - wall_started) * 1000.0
        timer.stop()
        timer.timeout.disconnect(monitor)
        timer.deleteLater()
        action["rss_after_mb"] = float(module._workflow_current_rss_mb())
        action["objects_after"] = len(document.Objects)
        action["dialogs"] = state
    _require(not state["unexpected"] and not state["monitor_errors"],
             "Unexpected dialog or monitor error: " + repr(state))
    _require(all(len(state[name]) == 1 for name in
                 ("inputs", "replace", "summary", "success")),
             "Expected one input, replace, summary and success dialog")
    _require("Successful files: 15" in state["summary"][0]["information"],
             "Summary did not report all fifteen published files")
    _require("15 successful files; 0 failed" in state["success"][0]["text"],
             "Final success did not report the expected file counts")


def _validate_outputs(module, document, child, witness):
    snapshot = export_directory_snapshot(child)
    expected = set(EXPECTED_EXPORT_FILENAMES) | {witness.DEPENDENCY_FILENAME}
    _require(set(snapshot["files"]) == expected,
             "Published file inventory differs")
    variant = export_variant_snapshot(snapshot)
    logical_digest = validate_export_snapshot(variant)
    metrics = format_export_metrics(module, child, variant, shape_summary)
    metrics_digest = format_metrics_sha256(metrics)
    _require(metrics_digest == EXPECTED_EXPORT_METRICS_SHA256,
             "Export geometry differs from the accepted fixed fixture")
    csv_path = child / "Curve_Set_001_Export_Manifest.csv"
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    payload_names = set(EXPECTED_EXPORT_FILENAMES) - {csv_path.name}
    _require({row["Full export path"] for row in rows}
             == {str(child / name) for name in payload_names},
             "CSV does not identify the final payload paths")
    manifest_path = child / witness.DEPENDENCY_FILENAME
    manifest = json.loads(manifest_path.read_text())
    artifact_paths = [child / item["path"]
                      for item in manifest["subject"]["artifacts"]]
    _require({path.name for path in artifact_paths}
             == set(EXPECTED_EXPORT_FILENAMES),
             "Dependency manifest does not cover the complete set")
    settings = module.latest_generated_settings(document)
    dependency = witness.dependency_manifest_witness(
        manifest_path, artifact_paths, settings.GeneratorVersion,
    )
    return {"logical_output_sha256": logical_digest,
            "export_metrics_sha256": metrics_digest,
            "dependency_manifest": dependency}


def _run():
    module = sys.modules[globals()["TRACKTEMPLATE_WORKFLOW_MODULE_NAME"]]
    root = Path(globals()["_PHASE3_REPOSITORY_ROOT"])
    run_directory = Path(globals()["TRACKTEMPLATE_BASELINE_DIRECTORY"])
    _require(run_directory.is_absolute() and run_directory.is_dir(),
             "Use an absolute run directory")
    directory = run_directory / "probe"
    directory.mkdir()
    document = App.ActiveDocument
    _require(document is not None and document.FileName,
             "Open the saved copied fixture first")
    _require(globals()["_PHASE3_PRODUCT_COMPOSITION"],
             "Normal modular route is required")
    qualification = globals()["_PHASE3_QUALIFICATION"]
    routing = globals()["_PHASE3_ROUTING"]
    session = globals()["_PHASE3_SESSION"]
    host = qualification["compatibility_evaluation"]["matched_profile_id"]
    _require(host == HOST_PROFILE_ID, "Unexpected qualified host profile")
    spec = importlib.util.spec_from_file_location(
        "core_generate_baseline_witness",
        root / "tests/freecad_validate_core_export_atomic.py",
    )
    witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(witness)
    group = App.ParamGet(module.LAST_INPUTS_PARAMETER_PATH)
    preferences = _preferences(group)
    pending = copy.deepcopy(module._PENDING_IMPORTED_CONFIGURATION)
    original_registry = dict(App.listDocuments())
    bindings = {name: module.__dict__[name]
                for name in routing["function_names"]}
    report = {
        "schema_version": 1, "profile_id": PROFILE_ID,
        "host_profile_id": host, "status": "incomplete", "actions": [],
        "routing": routing, "host_qualification": qualification, "checks": {},
        "measurement_boundary": "actual run_macro call including dialog setup",
        "limitations": [
            "Includes dialog construction, configuration and 25ms polling.",
            "Deep semantic, format, hash checks and capture are outside timing.",
            "First Generate uses a fresh process; startup time is excluded.",
            "Later actions regenerate; they do not reuse unchanged results.",
            "No budget, improvement, Phase6, production or exit acceptance.",
        ],
    }
    try:
        ordinary_track_snapshot(module, document, enforce_expected_hash=False,
                                expected_macro_version="10.2A8A7B15")
        initial = ordinary_track_document_snapshot(module, document)
        parent = directory / "outputs"
        parent.mkdir()
        (parent / "previous-output.txt").write_text(
            "preserve previous output\n",
        )
        previous = _file_state(parent)
        # The isolated session starts from the copied fixture, not user recall.
        for key in (module.LAST_INPUTS_PARAMETER_KEY,
                    module.LAST_INPUTS_DOCUMENT_MAP_KEY):
            group.RemString(key)
        module._PENDING_IMPORTED_CONFIGURATION = None
        contracts = []
        for label in ("first-generate", "same-process-regeneration-1",
                      "same-process-regeneration-2"):
            action = {"label": label, "status": "incomplete"}
            report["actions"].append(action)
            children = set(parent.iterdir())
            _measure_action(module, document, parent, action)
            additions = set(parent.iterdir()) - children
            _require(len(additions) == 1 and next(iter(additions)).is_dir(),
                     "Generate must publish exactly one new directory")
            child = next(iter(additions))
            _require(not child.name.startswith("."),
                     "Unpublished staging path")
            _require(dict(App.listDocuments()) == original_registry
                     and App.ActiveDocument is document,
                     "Generate changed the document registry or active document")
            after = ordinary_track_document_snapshot(module, document)
            compare_create_time_document_to_base(*[
                normalise_version_migration_snapshot(
                    value, ("10.2A8A7B14", "10.2A8A7B15"),
                )
                for value in (initial, after)
            ])
            contract = create_time_export_document_snapshot(
                after, enforce_expected_hash=False,
            )
            _require(len(document.Objects) == 9,
                     "Generated object count differs")
            proof = _validate_outputs(module, document, child, witness)
            _require(dict(App.listDocuments()) == original_registry
                     and App.ActiveDocument is document,
                     "Deep validation leaked a document")
            current = _file_state(parent)
            _require(all(current.get(name) == value
                         for name, value in previous.items()),
                     "Generate changed previously published output")
            previous = current
            digest = _digest({
                "document": contract["semantic_sha256"],
                "logical_output": proof["logical_output_sha256"],
                "geometry": proof["export_metrics_sha256"],
            })
            contracts.append(digest)
            action.update(proof, status="completed", output_dir=str(child),
                          payload_count=EXPECTED_TASK_COUNT,
                          output_contract_sha256=digest,
                          document_semantic_sha256=contract["semantic_sha256"],
                          previous_outputs_preserved=True)
        _require(len(set(contracts)) == 1, "Repeated output contracts differ")
        _require(all(module.__dict__[name] is value
                     for name, value in bindings.items()),
                 "Product routing bindings changed")
        _require(session.routing_record() == routing,
                 "Product routing record changed")
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
        capture = directory / "completed-product.png"
        Gui.activeDocument().activeView().saveImage(str(capture), 1280, 900)
        _require(capture.is_file() and capture.stat().st_size > 0,
                 "Viewport capture is absent")
        report["capture"] = str(capture)
        report["capture_sha256"] = hashlib.sha256(
            capture.read_bytes(),
        ).hexdigest()
        report["checks"].update(
            repeated_contract_equal=True, previous_outputs_preserved=True,
            actual_export_geometry_verified=True,
            document_registry_preserved=True,
            routing_preserved=True, dependency_classification_verified=True,
        )
        report["status"] = "completed"
        report["sentinel"] = SENTINEL
    except Exception:
        report["status"] = "failed"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        try:
            _restore_preferences(group, preferences)
            module._PENDING_IMPORTED_CONFIGURATION = pending
            restored = _preferences(group) == preferences
            report["checks"]["preferences_restored"] = restored
            report["checks"]["pending_configuration_restored"] = (
                module._PENDING_IMPORTED_CONFIGURATION == pending
            )
            _require(restored, "Preference subtree was not restored")
        except Exception:
            report["status"] = "failed"
            report.pop("sentinel", None)
            report["restoration_traceback"] = traceback.format_exc()
            raise
        finally:
            (directory / "probe.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    print(json.dumps(report, sort_keys=True))


_run()
