"""Prove B16 chair-cache freshness on copied fixed XO-001 and TO-001 cases.

Run with FreeCADCmd, or with runpy in the existing isolated GUI bridge.
The latter also exercises the unchanged chair panel and captures its state.
The record mutation is injected at the existing timber-extractor boundary;
it does not claim that a new timber editing command exists.
"""

import copy
import datetime
import hashlib
import json
import os
import pathlib
import runpy
import shutil
import sys
import traceback

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402
from tools.freecad_bridge import chair_analysis_recipe as chairs  # noqa: E402
from tools.freecad_bridge import crossover_timber_recipe as timbers  # noqa: E402
from tools.freecad_bridge import turnout_recipe as turnouts  # noqa: E402


SENTINEL = "Chair analysis signature FreeCAD validation passed"
GUI_SENTINEL = "Chair analysis signature real GUI validation passed"
CONTRACT = ROOT / "reference/contracts/phase1-chair-analysis-persistence.json"
ENTITY_ID = "XO-001"
KIND = "crossover"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_digest(value):
    """Hash exact JSON values, without the old recipe's float rounding."""
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _logical(result):
    # FCStd JSON restores tuples as lists. Preserve every numerical value.
    return json.loads(json.dumps(
        chairs.deterministic_result(result), allow_nan=False,
    ))


def _assert_base_fixture(module, document, expected_digest):
    snapshot = b14_recipe.freecad_base_snapshot(
        module, document, expected_macro_version="10.2A8A7B15",
    )
    semantic = dict(snapshot["semantic"])
    # The fixture is B14; only the executing host version is B15.
    semantic["macro_version"] = "10.2A8A7B14"
    assert _exact_digest(semantic) == expected_digest


def _history(document):
    return {
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": list(document.UndoNames),
        "redo_names": list(document.RedoNames),
    }


def _stored(module, document, kind=KIND, entity_id=ENTITY_ID):
    result = module._chair_read_cached_result(document, kind, entity_id)
    assert isinstance(result, dict)
    return result


def _payload(module, document, kind=KIND, entity_id=ENTITY_ID):
    obj = module._chair_settings_object(document, kind, entity_id)
    assert obj is not None
    return module.object_string_property(
        obj, module.CHAIR_ANALYSIS_RESULT_PROPERTY, "",
    )


def _config(module, document, kind, entity_id):
    reader = (module.turnout_config_by_id if kind == "turnout"
              else module.crossover_config_by_id)
    return reader(document, entity_id)


def _freshness(module, document, *, stale, kind=KIND, entity_id=ENTITY_ID):
    config = _config(module, document, kind, entity_id)
    status = module.chair_analysis_effective_status(document, kind, config)
    if stale:
        assert status == module.CHAIR_STATUS_STALE, status
        try:
            module._chair_generation_context(document, kind, entity_id)
        except ValueError as error:
            assert "stale" in str(error).lower()
            return {"status": status, "generation_rejection": str(error)}
        raise AssertionError("Stale chair records reached generation context")
    assert status != module.CHAIR_STATUS_STALE, status
    context = module._chair_generation_context(document, kind, entity_id)
    assert context[2]["geometry_signature"] == config[
        "chair_analysis_signature"
    ]
    return {"status": status, "generation_signature": context[2][
        "geometry_signature"
    ]}


def _display(module, document, kind=KIND, entity_id=ENTITY_ID):
    result = {}
    for obj in module._chair_analysis_display_objects(
        document, kind, entity_id,
    ):
        shape = getattr(obj, "Shape", None)
        result[str(obj.Name)] = {
            "role": module.object_string_property(obj, "GeneratedRole", ""),
            "shape": (chairs.shape_summary(shape)
                      if shape is not None and not shape.isNull() else None),
            "visible": bool(obj.ViewObject.Visibility) if App.GuiUp else None,
        }
    assert result, "The chair analysis has no diagnostic display"
    return result


class _GuiProof:
    """Observe the existing panel; never replace product calculations."""

    def __init__(self, module, run_directory, kind=KIND, entity_id=ENTITY_ID):
        from PySide6 import QtWidgets

        self.module = module
        self.run_directory = run_directory
        self.kind = kind
        self.entity_id = entity_id
        self.qt = QtWidgets
        self.panel = None
        self.document = None
        self.records = {}

    def bind(self, document):
        self.close()
        self.document = document
        self.panel = self.module.ChairAnalysisPanel(
            document, self.kind,
            lambda: _config(self.module, document, self.kind, self.entity_id),
        )
        self.panel.resize(1100, 320)
        self.panel.show()
        self.qt.QApplication.processEvents()

    def analyse(self):
        errors = []

        def reject_dialog(_parent, title, message, *args, **kwargs):
            errors.append({"title": str(title), "message": str(message)})
            return self.qt.QMessageBox.StandardButton.Ok

        original = self.qt.QMessageBox.critical
        self.qt.QMessageBox.critical = reject_dialog
        try:
            self.panel.analyse_button.click()
            self.qt.QApplication.processEvents()
        finally:
            self.qt.QMessageBox.critical = original
        assert not errors, errors
        return _stored(self.module, self.document, self.kind, self.entity_id)

    def observe(self, label, *, stale):
        import FreeCADGui as Gui
        from PySide6 import QtGui

        self.panel.refresh()
        self.qt.QApplication.processEvents()
        text = str(self.panel.status.text())
        assert (self.module.CHAIR_STATUS_STALE in text) is stale, text
        assert self.panel.generate_button.isEnabled() is not stale
        assert "Production ready: No" in text
        panel_path = self.run_directory / (label + "-panel.png")
        assert self.panel.grab().save(str(panel_path), "PNG")
        view = Gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        view.redraw()
        Gui.updateGui()
        image_path = self.run_directory / (label + "-view.png")
        view.saveImage(str(image_path), 1400, 900, "Current")
        images = {}
        for path in (panel_path, image_path):
            assert path.is_file() and not QtGui.QImage(str(path)).isNull()
            images[path.name] = _sha256(path)
        self.records[label] = {
            "status_text": text,
            "generation_enabled": self.panel.generate_button.isEnabled(),
            "display": _display(
                self.module, self.document, self.kind, self.entity_id,
            ),
            "history": _history(self.document),
            "images": images,
        }

    def close(self):
        if self.panel is not None:
            self.panel.close()
            self.panel.deleteLater()
            self.qt.QApplication.processEvents()
            self.panel = None


def _load_product():
    launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    api, bootstrap = launcher["_load_foundation"](ROOT)
    session, routing = launcher["_load_modular_transition_workflow"](
        ROOT, api, bootstrap,
    )
    assert routing["route"] == "modular" and routing["schema_version"] == 16
    return session.module, foundation["matched_profile_id"], routing


def _precision_witness(module, legacy, document):
    """Reject the retained XO-001 key-rounding alias using exact outputs."""
    config = _config(module, document, KIND, ENTITY_ID)
    settings = module.normalise_chair_analysis_settings(
        config.get("chair_analysis_settings"),
    )
    rails = module.chair_rail_records_for_entity(document, KIND, config)
    timber_records = module.chair_timber_records_for_entity(
        document, KIND, config,
    )
    changed = copy.deepcopy(rails)
    changed[0]["points"][0] = list(changed[0]["points"][0])
    changed[0]["points"][0][0] += 0.000004
    before_args = (KIND, config, settings, rails, timber_records)
    after_args = (KIND, config, settings, changed, timber_records)
    old_key = legacy._chair_geometry_signature(*before_args)
    assert legacy._chair_geometry_signature(*after_args) == old_key
    new_key = module._chair_geometry_signature(*before_args)
    changed_key = module._chair_geometry_signature(*after_args)
    assert changed_key != new_key
    before = _logical(legacy.analyse_chair_position_records(
        KIND, config, rails, timber_records, settings,
    ))
    after = _logical(legacy.analyse_chair_position_records(
        KIND, config, changed, timber_records, settings,
    ))
    assert after != before, "The exact logical output did not change"
    return {
        "delta_mm": 0.000004, "legacy_alias_signature": old_key,
        "baseline_signature": new_key, "changed_signature": changed_key,
        "baseline_exact_output_sha256": _exact_digest(before),
        "changed_exact_output_sha256": _exact_digest(after),
    }


def _rejected_analysis_preserves_state(module, document):
    """An invalid selected input must fail before any document mutation."""
    original = module.chair_rail_records_for_entity

    def snapshot():
        return {
            "payload": _payload(module, document),
            "history": _history(document),
            "display": _display(module, document),
            "object_names": sorted(obj.Name for obj in document.Objects),
        }

    def invalid_records(*args, **kwargs):
        records = copy.deepcopy(original(*args, **kwargs))
        records[0]["points"][0] = list(records[0]["points"][0])
        records[0]["points"][0][0] = float("nan")
        return records

    before = snapshot()
    module.chair_rail_records_for_entity = invalid_records
    try:
        try:
            module.analyse_entity_chair_positions(document, KIND, ENTITY_ID)
        except ValueError as error:
            refusal = str(error)
            assert "Out of range float" in refusal, refusal
        else:
            raise AssertionError("A nonfinite rail input was accepted")
        assert snapshot() == before
    finally:
        module.chair_rail_records_for_entity = original
    return {
        "refusal": refusal,
        "before_state_sha256": _exact_digest(before),
        "after_state_sha256": _exact_digest(snapshot()),
        "stored_payload_history_display_and_names_unchanged": True,
    }


def _turnout_proof(module, legacy, fixture, run_directory, fixture_digest):
    """Exercise the shared binding on the existing TO-001 recipe too."""
    kind, entity_id = "turnout", turnouts.TURNOUT_ID
    path = run_directory / "chair-signature-TO001.FCStd"
    shutil.copy2(fixture, path)
    document = App.openDocument(str(path))
    document.UndoMode = 1
    gui = None
    original = module.chair_rail_records_for_entity
    result = {}
    try:
        _assert_base_fixture(module, document, fixture_digest)
        hosts = module.turnout_host_objects(document)
        selected = turnouts.select_turnout_host(
            hosts, module.object_string_property,
            module._integer_object_property,
        )
        config = module.create_curve_inheriting_c10_turnout(
            document, hosts[selected["index"]], turnouts.TURNOUT_CHAINAGE_MM,
            module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
            turnouts.TRACK_GAUGE_MM, turnouts.FLANGEWAY_MM,
        )
        assert config["turnout_id"] == entity_id
        if App.GuiUp:
            gui = _GuiProof(module, run_directory, kind, entity_id)
            gui.bind(document)

        def analyse():
            return (gui.analyse() if gui else
                    module.analyse_entity_chair_positions(
                        document, kind, entity_id,
                    ))

        first = analyse()
        assert first["cache_reused"] is False
        baseline = _logical(first)
        key = first["geometry_signature"]
        reused = analyse()
        assert reused["cache_reused"] is True
        assert _logical(reused) == baseline
        config = _config(module, document, kind, entity_id)
        rails = original(document, kind, config)
        timber_records = module.chair_timber_records_for_entity(
            document, kind, config,
        )
        settings = module.normalise_chair_analysis_settings(
            config.get("chair_analysis_settings"),
        )
        frozen_result = legacy.analyse_chair_position_records(
            kind, config, rails, timber_records, settings,
        )
        assert _logical(frozen_result) == baseline
        handed = dict(config, handing=module.TURNOUT_HAND_RIGHT)
        assert module._chair_geometry_signature(
            kind, handed, settings, rails, timber_records,
        ) != key
        handed_result = legacy.analyse_chair_position_records(
            kind, handed, rails, timber_records, settings,
        )
        assert _logical(handed_result) != baseline
        result["live_b15_handing"] = {
            "baseline_exact_output_sha256": _exact_digest(baseline),
            "changed_exact_output_sha256": _exact_digest(
                _logical(handed_result),
            ),
        }
        selected_rail = first["positions"][0]["rail_identity"]

        def changed_records(*args, **kwargs):
            records = copy.deepcopy(original(*args, **kwargs))
            selected = [item for item in records
                        if item["stable_identity"] == selected_rail]
            assert len(selected) == 1
            selected[0]["name"] = "CACHE-PROBE-RAIL"
            return records

        module.chair_rail_records_for_entity = changed_records
        result["stale"] = _freshness(
            module, document, stale=True, kind=kind, entity_id=entity_id,
        )
        if gui:
            gui.observe("turnout-stale", stale=True)
        changed = analyse()
        assert changed["cache_reused"] is False
        assert changed["geometry_signature"] != key
        affected = [item for item in changed["positions"]
                    if item["rail_identity"] == selected_rail]
        assert affected and all(item["rail_name"] == "CACHE-PROBE-RAIL"
                                for item in affected)
        assert _logical(changed) != baseline
        result["changed_current"] = _freshness(
            module, document, stale=False, kind=kind, entity_id=entity_id,
        )
        assert analyse()["cache_reused"] is True
        module.chair_rail_records_for_entity = original
        restored = analyse()
        assert restored["cache_reused"] is False
        assert restored["geometry_signature"] == key
        assert _logical(restored) == baseline
        payload = _payload(module, document, kind, entity_id)
        display = _display(module, document, kind, entity_id)
        if gui:
            gui.close()
        document.save()
        App.closeDocument(document.Name)
        document = App.openDocument(str(path))
        document.UndoMode = 1
        assert _payload(module, document, kind, entity_id) == payload
        assert _display(module, document, kind, entity_id) == display
        if gui:
            gui.bind(document)
            gui.observe("turnout-reopened-current", stale=False)
        reopened = analyse()
        assert reopened["cache_reused"] is True
        assert _logical(reopened) == baseline
        result["reopened_current"] = _freshness(
            module, document, stale=False, kind=kind, entity_id=entity_id,
        )
        result["position_count"] = len(first["positions"])
        result["gui_observations"] = gui.records if gui else None
        result["status"] = "PASS"
        return result
    finally:
        module.chair_rail_records_for_entity = original
        if gui:
            gui.close()
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


def validate():
    """Run the copied-document regression and retain success or failure."""
    assert not App.listDocuments(), "The proof requires an empty host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_directory = pathlib.Path(os.environ.get(
        "TRACKTEMPLATE_CHAIR_SIGNATURE_RUN_DIR",
        ROOT / "benchmark-output/chair-analysis-signature" / stamp,
    )).resolve()
    run_directory.mkdir(parents=True, exist_ok=False)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fixture = ROOT / contract["fixture"]["path"]
    fixture_hash = _sha256(fixture)
    assert fixture_hash == contract["fixture"]["sha256"]
    frozen = contract["source_state"]
    for source in frozen.values():
        assert _sha256(ROOT / source["path"]) == source["sha256"]
    copied_path = run_directory / "chair-signature-XO001.FCStd"
    shutil.copy2(fixture, copied_path)
    receipt = {
        "status": "RUNNING", "gui": bool(App.GuiUp),
        "source_fixture": str(fixture),
        "source_fixture_sha256": fixture_hash,
        "frozen_sources": frozen, "run_document": str(copied_path),
        "test_source_sha256": _sha256(pathlib.Path(__file__).resolve()),
        "scope": (
            "Copied fixed XO-001 and existing TO-001 recipe; inherited B15 "
            "chair calculations; timber identifier and rail-name injection "
            "at the existing extractor boundary; "
            "cache freshness, history and persistence only. No physical fit, "
            "solid generation, wider family or production acceptance."
        ),
    }
    document = None
    gui = None
    original_extractor = None
    try:
        module, profile, routing = _load_product()
        receipt["matched_profile_id"] = profile
        receipt["routing"] = routing
        receipt["product_source_sha256"] = {
            path: _sha256(ROOT / path) for path in (
                "TrackTemplate.FCMacro",
                "tracktemplate/compatibility/transition_workflow.py",
                "tracktemplate/application/chair_analysis_signature.py",
            )
        }
        corrected_signature = module._chair_geometry_signature
        legacy = chairs.load_macro_without_launch(
            ROOT / frozen["b15"]["path"], "chair_signature_frozen_b15",
        )
        assert corrected_signature is not legacy._chair_geometry_signature
        document = App.openDocument(str(copied_path))
        document.UndoMode = 1
        _assert_base_fixture(
            module, document, contract["fixture"]["semantic_sha256"],
        )
        config, _selection = timbers.create_controlled_crossover(
            module, document, contract["scenario"]["host_a_chainage_mm"],
        )
        assert config["crossover_id"] == ENTITY_ID
        b4 = module.apply_crossover_b4_timbering(document, ENTITY_ID)
        assert b4["resolution_signature"] == contract["scenario"][
            "prerequisite_b4_resolution_signature"
        ]
        receipt["exact_precision_alias"] = _precision_witness(
            module, legacy, document,
        )
        if App.GuiUp:
            gui = _GuiProof(module, run_directory)
            gui.bind(document)

        def analyse():
            if gui is not None:
                return gui.analyse()
            return module.analyse_entity_chair_positions(
                document, KIND, ENTITY_ID,
            )

        # Store a real inherited result with its historical key, then restore
        # the product binding. No on-load migration or property is introduced.
        module._chair_geometry_signature = legacy._chair_geometry_signature
        try:
            historical = analyse()
        finally:
            module._chair_geometry_signature = corrected_signature
        assert historical["cache_reused"] is False
        historical_payload = _payload(module, document)
        receipt["historical_stale"] = _freshness(
            module, document, stale=True,
        )
        if gui is not None:
            gui.observe("historical-stale", stale=True)
            gui.close()
        document.save()
        App.closeDocument(document.Name)
        document = App.openDocument(str(copied_path))
        document.UndoMode = 1
        assert _payload(module, document) == historical_payload
        receipt["historical_reopen"] = _freshness(
            module, document, stale=True,
        )
        if gui is not None:
            gui.bind(document)
        first = analyse()
        assert first["cache_reused"] is False
        assert first["display_cache_reused"] is False
        assert first["geometry_signature"] != historical["geometry_signature"]
        assert _logical(first) == _logical(historical)
        baseline = _logical(first)
        baseline_key = first["geometry_signature"]
        first_payload = _payload(module, document)
        first_display = _display(module, document)
        receipt["cold"] = {
            **_freshness(module, document, stale=False),
            "logical_sha256": _exact_digest(baseline),
            "position_count": len(first["positions"]),
            "position_identities_sha256": _exact_digest([
                item["stable_chair_position_identity"]
                for item in first["positions"]
            ]),
        }
        if gui is not None:
            gui.observe("current", stale=False)
        before_reuse = _history(document)
        second = analyse()
        assert second["cache_reused"] is True
        assert second["display_cache_reused"] is True
        assert second["geometry_signature"] == baseline_key
        assert _logical(second) == baseline
        assert _display(module, document) == first_display
        second_payload = _payload(module, document)
        assert second_payload != first_payload
        after_reuse = _history(document)
        assert after_reuse["undo"] == before_reuse["undo"] + 1
        document.undo()
        assert _payload(module, document) == first_payload
        assert _display(module, document) == first_display
        document.redo()
        assert _payload(module, document) == second_payload
        assert _display(module, document) == first_display
        receipt["reuse_history"] = {
            "before": before_reuse, "after": after_reuse,
            "undo_redo_restored_exact_payloads": True,
        }
        receipt["failed_explicit_analysis"] = (
            _rejected_analysis_preserves_state(module, document)
        )

        original_extractor = module.chair_timber_records_for_entity
        chosen = first["positions"][0]["timber_identity"]
        changed_identifier = "CACHE-PROBE-S99"

        def changed_records(*args, **kwargs):
            records = copy.deepcopy(original_extractor(*args, **kwargs))
            selected = [item for item in records
                        if item["stable_identity"] == chosen]
            assert len(selected) == 1
            selected[0]["identifier"] = changed_identifier
            return records

        module.chair_timber_records_for_entity = changed_records
        receipt["record_change_stale"] = _freshness(
            module, document, stale=True,
        )
        if gui is not None:
            gui.observe("record-change-stale", stale=True)
        changed = analyse()
        assert changed["cache_reused"] is False
        assert changed["display_cache_reused"] is False
        assert changed["geometry_signature"] != baseline_key
        selected_positions = [item for item in changed["positions"]
                              if item["timber_identity"] == chosen]
        assert selected_positions
        assert all(item["timber_identifier"] == changed_identifier
                   for item in selected_positions)
        assert _logical(changed) != baseline
        changed_reuse = analyse()
        assert changed_reuse["cache_reused"] is True
        assert _logical(changed_reuse) == _logical(changed)
        receipt["record_change"] = {
            **_freshness(module, document, stale=False),
            "timber_identity": chosen,
            "emitted_identifier": changed_identifier,
            "affected_positions": len(selected_positions),
            "logical_sha256": _exact_digest(_logical(changed)),
            "unchanged_reused": True,
        }
        module.chair_timber_records_for_entity = original_extractor
        _freshness(module, document, stale=True)
        restored = analyse()
        assert restored["cache_reused"] is False
        assert restored["geometry_signature"] == baseline_key
        assert _logical(restored) == baseline
        assert _display(module, document) == first_display
        receipt["change_back"] = _freshness(module, document, stale=False)
        saved_payload = _payload(module, document)
        if gui is not None:
            gui.close()
        document.save()
        App.closeDocument(document.Name)
        document = App.openDocument(str(copied_path))
        document.UndoMode = 1
        assert _payload(module, document) == saved_payload
        assert _logical(_stored(module, document)) == baseline
        assert _display(module, document) == first_display
        receipt["save_reopen"] = _freshness(module, document, stale=False)
        if gui is not None:
            gui.bind(document)
            gui.observe("reopened-current", stale=False)
        reopened_reuse = analyse()
        assert reopened_reuse["cache_reused"] is True
        assert reopened_reuse["geometry_signature"] == baseline_key
        assert _logical(reopened_reuse) == baseline
        receipt["reopened_reuse"] = True
        receipt["historical_geometry_signature"] = historical[
            "geometry_signature"
        ]
        receipt["gui_observations"] = gui.records if gui else None
        if gui is not None:
            gui.close()
        App.closeDocument(document.Name)
        document = None
        receipt["turnout"] = _turnout_proof(
            module, legacy, fixture, run_directory,
            contract["fixture"]["semantic_sha256"],
        )
        receipt["status"] = "PASS"
    except Exception:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        if original_extractor is not None:
            module.chair_timber_records_for_entity = original_extractor
        if gui is not None:
            gui.close()
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        receipt["source_fixture_sha256_after"] = _sha256(fixture)
        receipt["frozen_sources_unchanged"] = all(
            _sha256(ROOT / item["path"]) == item["sha256"]
            for item in frozen.values()
        )
        preserved = (
            receipt["source_fixture_sha256_after"] == fixture_hash
            and receipt["frozen_sources_unchanged"]
        )
        if not preserved:
            receipt["status"] = "FAIL"
        (run_directory / "result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert preserved, "The proof changed frozen source or original fixture"
    print(GUI_SENTINEL if App.GuiUp else SENTINEL, flush=True)
    print("CHAIR_SIGNATURE_RESULT=" + str(run_directory / "result.json"))
    return receipt


if __name__ in {"__main__", "freecad_validate_chair_analysis_signature"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
