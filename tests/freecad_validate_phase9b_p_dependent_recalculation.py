"""Prove automatic XO dependency updates and explicit P previews.

Both hosts operate the actual Generate command. Native execution scripts
only its input dialogs; GUI execution operates the real radius widget.
Accepted raw-source and component witnesses remain independent and unchanged.
"""

from contextlib import ExitStack
import copy
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide6 import QtCore, QtWidgets

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def _helper(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = _helper("_p_dependent_geometry",
              "freecad_validate_phase9b_p_curvature_recalculation.py")
recovery = _helper("_p_dependent_document_witness",
                   "freecad_validate_phase8_crossover_edit_recovery.py")
integration = _helper(
    "_p_dependent_integration_witness",
    "freecad_validate_phase8_crossover_host_integration_recovery.py",
)
p = old.p
catalogue = old.catalogue
combined = old.combined
lifecycle = old.lifecycle
SENTINEL = "Phase 9B P dependent recalculation FreeCAD validation passed"
FAULT = "P dependent injected failure after retained stage writes"


def _native_generate(module, source, radius_mm, *, cancel=False):
    """Replace UI controls only; run the actual product orchestration."""
    assert not App.GuiUp
    record = {"inputs": [], "messages": [], "control": "scripted-native-UI"}

    class Input:
        def __init__(self, *defaults):
            assert len(defaults) == 19
            self.original = copy.deepcopy(defaults[:17])
            self.output_mode_box = SimpleNamespace(setCurrentIndex=lambda _: None)

        def values(self):
            values = list(copy.deepcopy(self.original))
            values[1] = radius_mm
            values.append(module.OUTPUT_REPLACE)
            assert not values[15]["enabled"]
            assert all(a == b for i, (a, b) in enumerate(
                zip(self.original, values),
            ) if i != 1)
            record["inputs"].append({
                "before": self.original, "after": copy.deepcopy(values),
            })
            return tuple(values)

    def message(kind):
        def show(_parent, title, text, *_args):
            record["messages"].append({"kind": kind, "title": title,
                                       "text": text})
            return 1
        return show

    widgets = SimpleNamespace(
        QDialog=SimpleNamespace(Accepted=1),
        QMessageBox=SimpleNamespace(
            Yes=1, No=2, question=message("question"),
            information=message("information"), warning=message("warning"),
            critical=message("critical"),
        ),
    )
    App.setActiveDocument(source.Name)
    with (patch.object(module, "Gui", None),
          patch.object(module, "CurveInputDialog", Input),
          patch.object(module, "dialog_exec", return_value=0 if cancel else 1),
          patch.object(module, "QtWidgets", widgets)):
        module.run_macro()
    assert bool(record["inputs"]) is not cancel
    record["cancel"] = cancel
    return record


def _gui_generate(module, source, radius_mm, directory, *, cancel=False):
    """Operate the actual dialog and retain every visible diagnostic."""
    record = {"inputs": [], "messages": [], "errors": [],
              "control": "real-GUI", "cancel": cancel}
    seen = set()

    def monitor():
        try:
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if not widget.isVisible() or id(widget) in seen:
                    continue
                if isinstance(widget, module.CurveInputDialog):
                    seen.add(id(widget))
                    before = copy.deepcopy(widget.values())
                    widget.radius_box.setValue(radius_mm)
                    index = widget.output_mode_box.findText(module.OUTPUT_REPLACE)
                    assert index >= 0
                    widget.output_mode_box.setCurrentIndex(index)
                    after = copy.deepcopy(widget.values())
                    assert after[1] == radius_mm and not after[15]["enabled"]
                    assert len(before) == len(after) == 18
                    assert all(a == b for i, (a, b) in enumerate(
                        zip(before, after),
                    ) if i not in (1, 17))
                    record["inputs"].append({"before": before, "after": after})
                    assert widget.grab().save(str(directory / "radius-input.png"))
                    boxes = widget.findChildren(QtWidgets.QDialogButtonBox)
                    code = (QtWidgets.QDialogButtonBox.StandardButton.Cancel
                            if cancel else QtWidgets.QDialogButtonBox.StandardButton.Ok)
                    buttons = [box.button(code) for box in boxes]
                    buttons = [button for button in buttons if button is not None]
                    assert len(buttons) == 1
                    buttons[0].click()
                elif isinstance(widget, QtWidgets.QMessageBox):
                    seen.add(id(widget))
                    kind = "information"
                    if widget.icon() == QtWidgets.QMessageBox.Icon.Critical:
                        kind = "critical"
                    elif widget.icon() == QtWidgets.QMessageBox.Icon.Warning:
                        kind = "warning"
                    if "Replace generated templates" in widget.windowTitle():
                        kind = "question"
                    record["messages"].append({"kind": kind,
                                               "title": widget.windowTitle(),
                                               "text": widget.text()})
                    if kind == "question":
                        widget.button(QtWidgets.QMessageBox.StandardButton.Yes).click()
                    else:
                        widget.accept()
        except BaseException:
            record["errors"].append(traceback.format_exc())
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if isinstance(widget, QtWidgets.QDialog) and widget.isVisible():
                    widget.reject()

    App.setActiveDocument(source.Name)
    timer = QtCore.QTimer()
    timer.timeout.connect(monitor)
    timer.start(25)
    try:
        module.run_macro()
    finally:
        timer.stop()
        timer.timeout.disconnect(monitor)
        timer.deleteLater()
        old._write(directory / "generate.json", record)
    assert not record["errors"], record["errors"]
    assert len(record["inputs"]) == 1
    return record


def _operate(session, source, radius_mm, directory, gui, *, cancel=False):
    """Forbid eager chair creation throughout the actual host command."""
    directory.mkdir(exist_ok=False)
    registry = dict(App.listDocuments())
    with ExitStack() as stack:
        for name in vars(session):
            if name.endswith("_preview_factory"):
                stack.enter_context(patch.object(
                    session, name, side_effect=AssertionError("Eager chair preview"),
                ))
        stack.enter_context(patch.object(
            App, "newDocument", side_effect=AssertionError("Unexpected document"),
        ))
        if gui:
            result = _gui_generate(session.module, source, radius_mm,
                                   directory, cancel=cancel)
        else:
            result = _native_generate(session.module, source, radius_mm,
                                      cancel=cancel)
            old._write(directory / "generate.json", result)
    assert App.listDocuments() == registry
    result["no_eager_preview_or_document"] = True
    return result


def _snapshot(module, source):
    """Reuse complete qualified document/property/B-rep/history witness."""
    # A synthetic group's first Shape read materialises its derived cache.
    # Read once in fixed order; retain every original byte/state comparison.
    for obj in sorted(source.Objects, key=lambda item: item.Name):
        if (obj.TypeId == "App::DocumentObjectGroup"
                and "Shape" not in obj.PropertiesList):
            getattr(obj, "Shape", None)
    state = recovery._snapshot(module, source, "XO-001")
    records = integration._records(module, source)
    state["production_records"] = records
    state["production_bindings"] = integration._record_bindings(source, records)
    return state


def _current_integration(module, source, original, gui, *, regenerated):
    """Inspect accepted integration, metadata and reversible record links."""
    current = module.crossover_config_by_id(source, "XO-001")
    fields = ("edit_revision", "edited_from_macro_version",
              "preferred_reversion_side")
    before = {key: original[key] for key in fields if key in original}
    after = {key: current[key] for key in fields if key in current}
    assert after == before
    assert current["integration_active"] is True
    assert current["production_ready"] is False
    status = module.crossover_host_integration_effective_status(source, current)
    assert status == module.CROSSOVER_INTEGRATION_STATUS_ACTIVE
    data = module.crossover_host_integration_by_id(source, "XO-001")
    assert data == current["integration_result"]
    assert data["schema_version"] == 1
    assert data["crossover_id"] == "XO-001" and data["template_set_id"] == "SET-001"
    expected = module._crossover_integration_signature(
        source, current, current["b4_result"], data["source_record_ids"],
        data["section_number"],
    )
    assert expected == data["signature"] == current["integration_signature"]
    names = data["integration_object_names"]
    assert names == original["integration_result"]["integration_object_names"]
    assert len(names) == 6 and all(source.getObject(name) for name in names)
    records = integration._records(module, source)
    bindings = integration._record_bindings(source, records)
    assert len([item for item in records if item["source_name"] in names]) == 3
    removed = set(data["source_record_ids"])
    assert removed == set(original["integration_result"]["source_record_ids"])
    assert len(removed) == 4 and not removed & bindings.keys()
    restored = module._crossover_integration_restored_records(source, data)
    assert all(item.get("shape") is not None for item in restored)
    assert removed <= {item["record_id"] for item in restored}
    visibility = {}
    for name in (*data["source_visibility"], *data["crossover_visibility"]):
        obj = source.getObject(name)
        assert obj is not None
        view = getattr(obj, "ViewObject", None)
        visible = bool(view.Visibility) if view is not None else None
        visibility[name] = visible
        if gui and regenerated:
            assert visible is False, name
        elif not gui:
            assert visible is None, name
    return {"effective_status": status, "signature": expected,
            "metadata_preserved": after, "integration_objects": names,
            "current_record_bindings": bindings,
            "reversible_source_record_ids": sorted(removed),
            "source_visibility": visibility,
            "initial_saved_visibility_is_unknown": not regenerated,
            "production_ready": False}


def _equal_state(actual, expected, directory, label):
    """Retain exact operands on failure; do not filter source objects."""
    if actual != expected:
        old._write(directory / (label + "-actual.json"), actual)
        old._write(directory / (label + "-expected.json"), expected)
    assert actual == expected, label


def _atomic_change(session, source, radius, directory, gui):
    module = session.module
    combined._settle(source)
    previous_radius = module.quantity_value(
        module.latest_generated_settings(source), "CurveRadius", -1,
    )
    before = _snapshot(module, source)
    selection = lifecycle._selection_snapshot(App, gui)
    preselection = lifecycle._preselection_snapshot(App, gui)
    result = _operate(session, source, radius, directory, gui)
    assert not [m for m in result["messages"] if m["kind"] in {"critical", "warning"}]
    assert module.crossover_config_by_id(source, "XO-001") is not None
    assert module.quantity_value(module.latest_generated_settings(source),
                                 "CurveRadius", -1) == radius
    old.previous._context(module, source)
    after = _snapshot(module, source)
    if radius != previous_radius:
        old_objects = {item["name"]: item for item in before["objects"]}
        new_objects = {item["name"]: item for item in after["objects"]}
        changed = ("ChairAnalysis_XO_001", "ChairPositionMarkers_XO_001")
        for name in changed:
            assert old_objects[name]["shape"] is not None
            assert new_objects[name]["shape"] is not None
            assert new_objects[name]["shape"] != old_objects[name]["shape"]
        result["changed_aggregate_and_marker_breps"] = list(changed)
    result["current_reports"] = _current_reports(module, source)
    assert after["history"]["undo"] == before["history"]["undo"] + 1
    assert after["history"]["redo"] == 0
    assert lifecycle._selection_snapshot(App, gui) == selection
    assert lifecycle._preselection_snapshot(App, gui) == preselection
    source.undo()
    source.recompute()
    _equal_state(recovery._without_history(_snapshot(module, source)),
                 recovery._without_history(before), directory, "undo")
    assert lifecycle._selection_snapshot(App, gui) == selection
    assert lifecycle._preselection_snapshot(App, gui) == preselection
    source.redo()
    source.recompute()
    _equal_state(recovery._without_history(_snapshot(module, source)),
                 recovery._without_history(after), directory, "redo")
    assert lifecycle._selection_snapshot(App, gui) == selection
    assert lifecycle._preselection_snapshot(App, gui) == preselection
    result.update(single_atomic_undo_redo="PASS",
                  before_sha256=old._digest(before), after_sha256=old._digest(after))
    return result


def _cache_noop(module, source):
    combined._settle(source)
    before = _snapshot(module, source)
    config = module.crossover_config_by_id(source, "XO-001")
    result = module.analyse_entity_chair_positions(
        source, "crossover", "XO-001", settings=config["chair_analysis_settings"],
    )
    assert result["cache_reused"] is True
    assert _snapshot(module, source) == before
    return {"cache_reused": True, "source_and_history_unchanged": True}


def _initial_gui_presentation(module, source, directory):
    """Initialise only the copied headless fixture's GUI presentation."""
    assert App.GuiUp
    directory.mkdir()
    config = copy.deepcopy(module.crossover_config_by_id(source, "XO-001"))
    before = old.previous._context(module, source)
    frames = old._frames(module, before, 355)
    snapshot = _snapshot(module, source)
    selection = lifecycle._selection_snapshot(App, Gui)
    preselection = lifecycle._preselection_snapshot(App, Gui)
    result = module.analyse_entity_chair_positions(
        source, "crossover", "XO-001", settings=config["chair_analysis_settings"],
    )
    after = old.previous._context(module, source)
    assert module.crossover_config_by_id(source, "XO-001") == config
    assert after[4:] == before[4:]
    assert old._frames(module, after, 355) == frames
    current = _snapshot(module, source)
    for field in ("config", "production_records", "production_bindings"):
        assert current[field] == snapshot[field], field
    assert lifecycle._selection_snapshot(App, Gui) == selection
    assert lifecycle._preselection_snapshot(App, Gui) == preselection
    old._write(directory / "before.json", snapshot)
    old._write(directory / "after.json", current)
    return {"initial_fixture_presentation_only": True,
            "canonical_and_raw_source_unchanged": True,
            "independent_p_frames_unchanged": len(frames),
            "raw_source_sha256": old._digest(before[4:]),
            "cache_reused": result["cache_reused"]}


def _snapshot_negatives(module, source, directory, gui):
    """Prove cache materialisation cannot hide geometry or membership edits."""
    directory.mkdir()
    group = source.getObject("ChairAnalysis_XO_001")
    marker = source.getObject("ChairPositionMarkers_XO_001")
    assert marker in group.Group and "Shape" in marker.PropertiesList
    results = []
    for label in ("marker-geometry", "group-membership"):
        before = _snapshot(module, source)
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        expected = {item["name"]: item for item in before["objects"]}
        source.openTransaction("P dependent snapshot negative " + label)
        try:
            if label == "marker-geometry":
                moved = marker.Shape.copy()
                moved.translate(App.Vector(0, 0, 1))
                marker.Shape = moved
            else:
                group.removeObject(marker)
            source.recompute()
            after = _snapshot(module, source)
            actual = {item["name"]: item for item in after["objects"]}
            name, field = ((marker.Name, "shape") if label == "marker-geometry"
                           else (group.Name, "members"))
            assert actual[name][field] != expected[name][field]
            rejection = catalogue._reject(
                lambda: _equal_state(after, before, directory, label),
                AssertionError,
            )
        finally:
            source.abortTransaction()
            source.recompute()
        _equal_state(_snapshot(module, source), before, directory,
                     label + "-restored")
        assert lifecycle._selection_snapshot(App, gui) == selection
        assert lifecycle._preselection_snapshot(App, gui) == preselection
        old.previous._context(module, source)
        results.append({"mutation": label, "rejection": rejection,
                        "selection_and_preselection_restored": True,
                        "complete_source_and_history_restored": True})
    return results


def _assert_cell(actual, expected):
    """Allow only qualified Spreadsheet text or exact numeric storage."""
    try:
        number = Decimal(expected)
    except InvalidOperation:
        assert actual in (expected, "'" + expected), (actual, expected)
    else:
        assert number.is_finite() and Decimal(actual) == number, (
            actual, expected,
        )


def _assert_sheet(module, sheet, fields, rows):
    """Compare every header and data cell with the retained writer input."""
    assert sheet.TypeId == "Spreadsheet::Sheet"
    actual = []
    for row_number, row in enumerate([dict(zip(fields, fields)), *rows], 1):
        values = []
        for column, field in enumerate(fields):
            address = module._spreadsheet_column_name(column) + str(row_number)
            stored = sheet.getContents(address)
            expected = module._spreadsheet_text(row.get(field, ""))
            _assert_cell(stored, expected)
            values.append(stored)
        actual.append(values)
    return {"name": sheet.Name, "row_count": len(rows),
            "checked_cells": len(actual) * len(fields),
            "stored_cells_sha256": old._digest(actual),
            "expected_rows_sha256": old._digest(rows)}


def _current_reports(module, source):
    """Read reports against the current persisted, integrated source index."""
    before = _snapshot(module, source)
    settings = module.settings_for_template_set(source, "SET-001")
    index = module.read_production_record_index(settings)
    config = module.crossover_config_by_id(source, "XO-001")
    integrated_names = set(config["integration_result"]["integration_object_names"])
    integrated_ids = {item["record_id"] for item in index["records"]
                      if item["source_name"] in integrated_names}
    assert len(integrated_ids) == 3
    schedule_rows = module.build_production_schedule_rows(
        index, module.read_production_export_config(settings), "SET-001",
    )
    ids = [row["Production-record ID"] for row in schedule_rows]
    assert len(ids) == len(set(ids)) == len(index["records"])
    assert set(ids) == {item["record_id"] for item in index["records"]}
    assert integrated_ids <= set(ids)
    material_config = module.read_material_report_config(settings)
    material_rows, diagnostics = module.build_material_report_rows(
        source, index, settings, material_config, "SET-001",
    )
    result = {"integrated_record_ids": sorted(integrated_ids),
              "persisted_index_sha256": old._digest(index)}
    for role, fields, rows, count_property in (
        (module.PRODUCTION_SCHEDULE_ROLE, module.PRODUCTION_SCHEDULE_FIELDS,
         schedule_rows, "ProductionRecordCount"),
        (module.MATERIAL_REPORT_ROLE, module.MATERIAL_REPORT_FIELDS,
         material_rows, "MaterialReportRowCount"),
    ):
        sheets = [obj for obj in source.Objects
                  if module.object_string_property(obj, "GeneratedRole", "")
                  == role and module.object_string_property(
                      obj, "TemplateSetID", "",
                  ) == "SET-001"]
        assert len(sheets) == 1
        sheet = sheets[0]
        assert getattr(sheet, count_property) == len(rows)
        result[role] = _assert_sheet(module, sheet, fields, rows)
        if role == module.MATERIAL_REPORT_ROLE:
            assert json.loads(getattr(
                sheet, module.MATERIAL_REPORT_SETTINGS_PROPERTY,
            )) == material_config
            assert json.loads(sheet.MaterialReportDiagnosticsJSON) == diagnostics
    assert _snapshot(module, source) == before
    return result


def _late_failure(session, source, radius, directory, gui, seam):
    module = session.module
    combined._settle(source)
    before = _snapshot(module, source)
    selection = lifecycle._selection_snapshot(App, gui)
    preselection = lifecycle._preselection_snapshot(App, gui)
    adapter = module.remember_last_dialog_inputs.__self__
    bindings = dict(adapter.bindings)
    integration_create = module.create_crossover_host_integration
    integration_original = integration_create.__self__.original_create
    target = None
    hook = seam
    if seam == "create_crossover_host_integration":
        hook, target = "_crossover_store_catalogue", integration_original
    elif seam in ("create_or_replace_production_schedule",
                  "create_or_replace_material_report"):
        hook, target = "find_template_set_group", adapter.originals[seam]
    call = getattr(module, hook)
    reached = []

    def failed(*args, **kwargs):
        result = call(*args, **kwargs)
        frame = sys._getframe(1)
        try:
            if target is not None and not (
                frame.f_code is target.__code__
                and frame.f_globals is module.__dict__
            ):
                return result
            stage = {"returned": type(result).__name__, "hook": hook}
            if seam == "create_crossover_host_integration":
                current = module.crossover_config_by_id(source, "XO-001")
                assert current["integration_active"] is True
                data = current["integration_result"]
                names = data["integration_object_names"]
                assert len(names) == 6
                assert all(source.getObject(name) is not None for name in names)
                stage["integration_objects"] = names
                stage["source_visibility"] = {}
                for name in (*data["source_visibility"],
                             *data["crossover_visibility"]):
                    view = source.getObject(name).ViewObject
                    visible = bool(view.Visibility) if view is not None else None
                    assert visible is (False if gui else None)
                    stage["source_visibility"][name] = visible
            elif target is not None:
                fields = (module.PRODUCTION_SCHEDULE_FIELDS
                          if seam == "create_or_replace_production_schedule"
                          else module.MATERIAL_REPORT_FIELDS)
                stage["sheet"] = _assert_sheet(
                    module, frame.f_locals["sheet"], fields,
                    frame.f_locals["rows"],
                )
            old._write(directory / "after-stage-writes.json",
                       _snapshot(module, source))
            reached.append(stage)
        finally:
            del frame
        raise RuntimeError(FAULT)

    with patch.object(module, hook, failed):
        result = _operate(session, source, radius, directory, gui)
    assert all(getattr(module, name) is value
               for name, value in bindings.items())
    assert module.create_crossover_host_integration is integration_create
    assert integration_create.__self__.original_create is integration_original
    assert reached, "Injected failure did not reach real stage writes"
    assert any(FAULT in m["text"] for m in result["messages"])
    _equal_state(_snapshot(module, source), before, directory, "late-rollback")
    assert lifecycle._selection_snapshot(App, gui) == selection
    assert lifecycle._preselection_snapshot(App, gui) == preselection
    old.previous._context(module, source)
    return {"seam": seam, "after_real_writes": reached,
            "complete_state_and_history_restored": True, "diagnostics": result}


def _cancel(session, source, directory, gui):
    combined._settle(source)
    before = _snapshot(session.module, source)
    selection = lifecycle._selection_snapshot(App, gui)
    preselection = lifecycle._preselection_snapshot(App, gui)
    result = _operate(session, source, 900.0, directory, gui, cancel=True)
    assert _snapshot(session.module, source) == before
    assert lifecycle._selection_snapshot(App, gui) == selection
    assert lifecycle._preselection_snapshot(App, gui) == preselection
    return {"complete_state_and_history_unchanged": True, "input": result}


def _manual_inputs():
    path = Path(os.environ["TRACKTEMPLATE_P_DEPENDENT_MANUAL_INPUTS"])
    packet = json.loads(path.read_text())
    assert packet["status"] == "PASS"
    for filename, expected in packet["bindings"].items():
        assert catalogue._hash(Path(filename)) == expected, filename
    return packet


def _minimum_failure(session, packet, directory, gui):
    """Use the accepted toe-500 witness on 900, then reject 600.

    Existing edit/B4/integration/Analyse prepare this separate fixture. The
    tested Generate has no manual dependency refresh or recovery fallback.
    """
    directory.mkdir()
    contract_path = ROOT / "reference/contracts/phase1-crossover-feasibility.json"
    contract_hash = catalogue._hash(contract_path)
    assert contract_hash == (
        "bfa5c2ca19888cadcdf4dcec87f8f15759b078205bb916d6b6d2b8fde8c8a5a3"
    )
    contract = json.loads(contract_path.read_text())
    request = contract["request"]
    negative = next(item for item in contract["witnesses"]
                    if item["id"] == "lower-preview-pass-complete-fail")
    minimum = request["minimum_radius_mm"]
    source_path = Path(packet["changed_900_fixture"])
    target = directory / "minimum-source.FCStd"
    shutil.copy2(source_path, target)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    module = session.module
    from tracktemplate.compatibility import crossover_preflight

    original = copy.deepcopy(module.crossover_config_by_id(document, "XO-001"))
    try:
        hosts = [document.getObject(original[key])
                 for key in ("host_a_object", "host_b_object")]
        assert original["arrangement"] == request["arrangement"]
        assert original["track_gauge"] == request["track_gauge_mm"]
        assert original["flangeway"] == request["flangeway_mm"]
        args = (document, "XO-001", *hosts, negative["host_a_chainage_mm"],
                request["arrangement"], request["handing"],
                request["track_gauge_mm"], request["flangeway_mm"], minimum)
        with ExitStack() as setup:
            if not gui:
                setup.enter_context(patch.object(module, "Gui", None))
            updated = module.edit_rea_c10_crossover(*args)
            assert updated["toe_chainage_a"] == negative["host_a_chainage_mm"]
            assert updated["handing"] == original["handing"]
            assert updated["minimum_requested_radius"] == minimum
            assert updated["minimum_resulting_radius"] > minimum
            module.apply_crossover_b4_timbering(
                document, "XO-001", original["shared_timber_settings"],
                original["b3_settings"], original["b4_settings"],
            )
            module.create_crossover_host_integration(document, "XO-001")
            module.analyse_entity_chair_positions(
                document, "crossover", "XO-001",
                settings=original["chair_analysis_settings"],
            )
        context = old.previous._context(module, document)
        frames = old._frames(module, context, len(context[1]["positions"]))
        old._write(directory / "starting-source-context.json", context)
        old._write(directory / "starting-source-frames.json",
                   [asdict(frame) for frame in frames])
        before = _snapshot(module, document)
        decisions = []
        decide = crossover_preflight.complete_radius_decision

        def witness(*args, **kwargs):
            decision = decide(*args, **kwargs)
            decisions.append(copy.deepcopy(decision))
            return decision

        with patch.object(crossover_preflight, "complete_radius_decision", witness):
            result = _operate(session, document, 600.0,
                              directory / "attempt-600", gui)
        rejected = [item for item in decisions if item["accepted"] is False]
        assert len(rejected) == 1
        decision = rejected[0]
        assert decision["minimum_requested_radius_mm"] == minimum
        assert decision["complete_minimum_radius_mm"] < minimum
        residuals = {}
        for actual_key, expected_key in (
            ("turnout_a_minimum_radius_mm", "turnout_a_mapped_minimum_radius_mm"),
            ("turnout_b_minimum_radius_mm", "turnout_b_mapped_minimum_radius_mm"),
            ("connector_minimum_radius_mm", "connector_minimum_radius_mm"),
            ("complete_minimum_radius_mm", "complete_minimum_radius_mm"),
        ):
            residual = abs(decision[actual_key] - negative[expected_key])
            assert residual <= request["comparison_tolerance_mm"]
            residuals[actual_key] = residual
        assert decision["limiting_component"] in decision["diagnostic"]
        assert any(m["kind"] in {"critical", "warning"}
                   and decision["diagnostic"] in m["text"]
                   for m in result["messages"])
        _equal_state(_snapshot(module, document), before,
                     directory, "minimum-rollback")
        old.previous._context(module, document)
        document.UndoMode = 0
        before_disabled = _snapshot(module, document)
        disabled = _operate(session, document, 900.0,
                            directory / "undo-disabled", gui)
        assert any(m["kind"] in {"critical", "warning"}
                   and "undo" in m["text"].lower()
                   for m in disabled["messages"])
        _equal_state(_snapshot(module, document), before_disabled,
                     directory, "undo-disabled")
        return {"minimum_requested_mm": minimum,
                "contract": {"path": str(contract_path),
                             "sha256": contract_hash,
                             "witness_id": negative["id"],
                             "comparison_tolerance_mm":
                             request["comparison_tolerance_mm"]},
                "starting_source": {"toe_a_mm": updated["toe_chainage_a"],
                                    "toe_b_mm": updated["toe_chainage_b"],
                                    "resolved_hand": updated["handing"],
                                    "current_p_position_count": len(frames),
                                    "context_sha256": old._digest(context)},
                "valid_900_resulting_minimum_mm": updated["minimum_resulting_radius"],
                "rejected_complete_radius_decision": decision,
                "rejected_metric_residuals_mm": residuals,
                "invalid_600_unchanged": True,
                "undo_disabled_refusal": disabled, "diagnostics": result}
    finally:
        App.closeDocument(document.Name)


def validate():
    """Run complete native or real-GUI dependency and P geometry proof."""
    assert not App.listDocuments(), "Use an empty isolated host"
    gui = Gui if App.GuiUp else None
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"])
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    assert catalogue._hash(fixture) == old.previous.xo.FIXTURE_SHA256
    run_dir = Path(os.environ["TRACKTEMPLATE_P_DEPENDENT_RUN_DIR"])
    run_dir.mkdir(exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(gui), "cases": [],
               "automatic_logical_dependencies": True,
               "exact_chairs_only_on_explicit_preview": True,
               "physical_fit": "NOT_PROVED"}
    initial = catalogue.helpers._document_state()
    try:
        packet = _manual_inputs()
        prepared = p.prepare_catalogue_chair(path, "P", run="basic-04")
        case = next(item for item in catalogue._cases(path) if item[0] == "P")
        copies = run_dir / "native-component-copies"
        copies.mkdir()
        original = catalogue._reference(case, copies)
        reference = {name: shape for name, _label, shape, _matrix in original
                     if name != "display_rail"}
        assert tuple(reference) == p.COMPONENT_NAMES
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == p.PROFILE
        receipt.update(profile=p.PROFILE, routing=routing,
                       manual_reference_bindings=packet["bindings"])
        module = session.module
        command = session.preview_private_catalogue_p_crossover_chairs
        foreign = App.newDocument("PDependentForeignWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign.recompute()
        combined._settle(foreign)
        foreign_state = combined._foreign_state(foreign)
        target = run_dir / "controlled-XO-001.FCStd"
        shutil.copy2(fixture, target)
        source = App.openDocument(str(target))
        source.UndoMode = 1
        config = copy.deepcopy(module.crossover_config_by_id(source, "XO-001"))
        unrelated = source.addObject("App::FeaturePython", "PDependentKeep")
        unrelated.addProperty("App::PropertyString", "ProofValue")
        unrelated.ProofValue = "Preserve unrelated object through Generate"
        source.recompute()
        if gui:
            receipt["initial_gui_fixture_preparation"] = (
                _initial_gui_presentation(
                    module, source, run_dir / "initial-gui-presentation",
                )
            )
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(unrelated)
        receipt["snapshot_negative_controls"] = _snapshot_negatives(
            module, source, run_dir / "snapshot-negative-controls", gui,
        )
        old_previews, verifiers, original_frames = [], [], None
        for label, radius, count in old.CASES:
            directory = run_dir / label
            directory.mkdir()
            item = {"label": label, "radius_mm": radius,
                    "analysis_count": count}
            receipt["cases"].append(item)
            App.setActiveDocument(source.Name)
            if gui:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(unrelated)
            combined._settle(source)
            if old_previews:
                frozen = [combined._foreign_state(doc) for doc in old_previews]
                item["canonical_update"] = _atomic_change(
                    session, source, radius, directory / "generate", gui,
                )
                assert source.getObject("PDependentKeep") is unrelated
                item["current_dependencies"] = old._current_dependencies(
                    module, source, config,
                )
                item["old_source_refusal"] = catalogue._reject(
                    verifiers[-1], ValueError,
                )
                assert "not found" not in item["old_source_refusal"].lower()
                assert [combined._foreign_state(doc)
                        for doc in old_previews] == frozen
                assert combined._foreign_state(foreign) == foreign_state
                item["old_previews_static"] = True
            item["canonical"] = old._canonical_record(
                module, source, config, radius,
            )
            item["current_integration"] = _current_integration(
                module, source, config, gui, regenerated=bool(old_previews),
            )
            item["analysis_cache_noop"] = _cache_noop(module, source)
            context = old.previous._context(module, source)
            frames = old._frames(module, context, count)
            manual_context = json.loads(Path(packet["contexts"][label]).read_text())
            manual_frames = old._frames(module, manual_context, count)
            old._write(directory / "source-context.json", context)
            old._write(directory / "source-frames.json", [asdict(f) for f in frames])
            if original_frames is None:
                original_frames = frames
            elif label == "changed-900":
                item["stale_controls"] = old._stale_controls(original_frames, frames)
                item["recalculated"] = old.assert_recalculated(original_frames, frames)
            source.saveAs(str(directory / "XO-001.FCStd"))
            if gui:
                Gui.getMainWindow().resize(1600, 1000)
            combined._settle(source)
            unchanged, selection, preselection, state_hash, negatives = old._guard(
                module, source, foreign, gui, count,
            )
            item["source_state_sha256"] = state_hash
            item["source_guard_negative_witnesses"] = negatives
            create = session._private_catalogue_p_preview_factory

            def capture_verifier(*args):
                verifiers.append(args[-1])
                return create(*args)

            with (patch.object(session, "_private_catalogue_p_preview_factory",
                               capture_verifier),
                  patch.object(App, "openDocument", side_effect=AssertionError(
                      "Product restored external source",
                  ))):
                result = command(source, "XO-001", path)
            preview = App.getDocument(result["document_name"])
            item["preview"] = result
            item["comparisons"] = old._assert_preview(
                result, preview, reference, frames, context,
            )
            item["independent_manual_reference"] = old._change_back(
                preview, reference, manual_frames, frames,
            )
            unchanged("created", preview)
            shapes = tuple(obj.Shape for obj in preview.Objects)
            assert preview.UndoCount == 1
            preview.undo()
            assert not preview.Objects
            preview.redo()
            assert tuple(obj.Name for obj in preview.Objects) == p.LAYER_NAMES
            assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                       for obj, shape in zip(preview.Objects, shapes))
            unchanged("preview Undo/Redo", preview)
            item["preview_undo_redo"] = "PASS"
            if label == "changed-900":
                item["late_preview_source_rollback"] = old._rollback(
                    module, session, source, path, unchanged, preview,
                )
            if label == "returned-600":
                item["change_back"] = old._change_back(
                    preview, reference, original_frames, frames,
                )
            if gui:
                item["images"] = old._inspect(
                    preview, frames, directory, label == "changed-900",
                )
                lifecycle._restore_selection(App, gui, selection)
                lifecycle._restore_preselection(App, gui, preselection)
                unchanged("GUI inspection", preview)
            assert old.previous._context(module, source) == context
            assert combined._foreign_state(foreign) == foreign_state
            old_previews.append(preview)
            old._write(run_dir / "progress.json", receipt)
            print("P_DEPENDENT_CASE_PASS", label, flush=True)

        App.setActiveDocument(source.Name)
        combined._settle(source)
        receipt["cancellation"] = _cancel(
            session, source, run_dir / "cancel", gui,
        )
        frozen = [combined._foreign_state(doc) for doc in old_previews]
        receipt["same_input_regeneration"] = _atomic_change(
            session, source, 600.0, run_dir / "same-input", gui,
        )
        receipt["same_input_integration"] = _current_integration(
            module, source, config, gui, regenerated=True,
        )
        current = old.previous._context(module, source)
        current_frames = old._frames(module, current, 355)
        receipt["same_input_semantic_geometry"] = old._change_back(
            old_previews[-1], reference, current_frames, frames,
        )
        receipt["same_input_analysis_cache_noop"] = _cache_noop(module, source)
        assert [combined._foreign_state(doc) for doc in old_previews] == frozen
        failures = []
        for seam in ("apply_crossover_b4_timbering",
                     "create_crossover_host_integration",
                     "analyse_entity_chair_positions",
                     "create_or_replace_production_schedule",
                     "create_or_replace_material_report"):
            failures.append(_late_failure(
                session, source, 900.0, run_dir / ("late-" + seam), gui, seam,
            ))
            assert combined._foreign_state(foreign) == foreign_state
            assert [combined._foreign_state(doc) for doc in old_previews] == frozen
        receipt["late_failures"] = failures
        receipt["minimum_radius_refusal"] = _minimum_failure(
            session, packet, run_dir / "minimum-radius", gui,
        )
        assert combined._foreign_state(foreign) == foreign_state
        p.verify_catalogue_sources(prepared)
        receipt["fixture_unchanged"] = (
            catalogue._hash(fixture) == old.previous.xo.FIXTURE_SHA256
        )
        assert receipt["fixture_unchanged"]
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        catalogue.helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        old._write(run_dir / "result.json", receipt)
    assert catalogue.helpers._document_state() == initial
    receipt["status"] = "PASS"
    old._write(run_dir / "result.json", receipt)
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
