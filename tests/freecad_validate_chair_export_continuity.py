"""Prove chair decisions survive selected SVG export on copied TO/XO cases.

This uses production preflight, not final chair or complete-layout validation.
The exported SVG is an integrated cutting outline, not exported chair solids.
No physical fit, production readiness or Phase 9B acceptance is inferred.
"""

import copy
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONTRACT = ROOT / "reference/contracts/phase1-chair-analysis-persistence.json"
SENTINEL = "Chair export continuity FreeCAD validation passed"
CASES = {"turnout": ("TO-001", 168), "crossover": ("XO-001", 355)}


def _helper(filename):
    """Import reusable proof functions without running historical profiles."""
    path = ROOT / "tests" / filename
    spec = importlib.util.spec_from_file_location("_continuity_" + path.stem,
                                                 path)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.ROOT == ROOT
    return helper


SIGNATURE = _helper("freecad_validate_chair_analysis_signature.py")
EXPORT_HELPERS = {
    kind: _helper("freecad_validate_phase8_{}_selected_export.py".format(kind))
    for kind in CASES
}


def _neutral(value):
    """Normalise JSON tuple restoration without rounding any values."""
    return json.loads(json.dumps(value, allow_nan=False))


def _assert_decision_content(state):
    kind = state["kind"]
    identifier, position_count = CASES[kind]
    result = state["chair_result"]
    assert result["entity_id"] == identifier
    assert result["entity_kind"] == kind
    positions = result["positions"]
    assert len(positions) == position_count
    ids = [item["stable_chair_position_identity"] for item in positions]
    assert len(set(ids)) == position_count and all(ids)
    timbers = state["timbers"]
    assert len(timbers) > 1
    timber_ids = [item["stable_identity"] for item in timbers]
    assert len(set(timber_ids)) == len(timber_ids) and all(timber_ids)
    assert {item["timber_identity"] for item in positions} <= set(timber_ids)
    assert result["summary"]["timber_count"] == len(timbers)
    assert state["config"]["production_ready"] is False
    assert result["production_geometry_changed"] is False
    assert state["geometry_signature"]
    assert state["geometry_signature"] == state["config"][
        "chair_analysis_signature"
    ]
    records = state["production_records"]
    assert records
    record_ids = [item["record_id"] for item in records]
    assert all(record_ids) and len(set(record_ids)) == len(record_ids)


def _decision_state(module, document, kind):
    """Read exact chair, timber, configuration and production-record values."""
    identifier = CASES[kind][0]
    SIGNATURE._freshness(
        module, document, stale=False, kind=kind, entity_id=identifier,
    )
    result = SIGNATURE._stored(module, document, kind, identifier)
    config = SIGNATURE._config(module, document, kind, identifier)
    state = _neutral({
        "kind": kind,
        "config": config,
        "chair_result": SIGNATURE._logical(result),
        # The existing logical comparator omits this key as volatile.
        # This continuity proof also checks the unchanged current key.
        "geometry_signature": result["geometry_signature"],
        "stored_payload": SIGNATURE._payload(
            module, document, kind, identifier,
        ),
        "timbers": module.chair_timber_records_for_entity(
            document, kind, config,
        ),
        "production_records": EXPORT_HELPERS[kind]._records(module, document),
    })
    _assert_decision_content(state)
    return state


def _assert_decisions_equal(before, after):
    """Reject empty observations and any changed value, identity or order."""
    _assert_decision_content(before)
    _assert_decision_content(after)
    assert after == before, "Chair/timber decisions or record order changed"


def _negative_witnesses(baseline):
    """Demonstrate that absence, altered content and order cannot pass."""
    witnesses = []
    for label in (
        "missing-chairs", "changed-chair", "reordered-chairs",
        "missing-timbers", "changed-timber", "reordered-timbers",
        "changed-record-id", "reordered-records", "production-promotion",
    ):
        changed = copy.deepcopy(baseline)
        if label == "missing-chairs":
            changed["chair_result"]["positions"] = []
        elif label == "changed-chair":
            changed["chair_result"]["positions"][0]["chair_family"] = (
                "injected different family"
            )
        elif label == "reordered-chairs":
            changed["chair_result"]["positions"].reverse()
        elif label == "missing-timbers":
            changed["timbers"] = []
        elif label == "changed-timber":
            changed["timbers"][0]["identifier"] = "injected identifier"
        elif label == "reordered-timbers":
            changed["timbers"].reverse()
        elif label == "changed-record-id":
            changed["production_records"][0]["record_id"] = "injected ID"
        elif label == "reordered-records":
            changed["production_records"].reverse()
        else:
            changed["config"]["production_ready"] = True
        try:
            _assert_decisions_equal(baseline, changed)
        except AssertionError:
            witnesses.append(label)
        else:
            raise AssertionError("Comparator accepted " + label)
    return witnesses


def _prepare_case(module, run_dir, kind):
    """Prepare one copied fixture, then store fresh nonempty chair analysis."""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = ROOT / contract["fixture"]["path"]
    assert SIGNATURE._sha256(source) == contract["fixture"]["sha256"]
    identifier = CASES[kind][0]
    target = Path(run_dir) / (identifier + ".FCStd")
    assert not target.exists(), target
    shutil.copy2(source, target)
    document = App.openDocument(str(target))
    document.UndoMode = 1
    try:
        SIGNATURE._assert_base_fixture(
            module, document, contract["fixture"]["semantic_sha256"],
        )
        if kind == "turnout":
            recipe = SIGNATURE.turnouts
            hosts = module.turnout_host_objects(document)
            selected = recipe.select_turnout_host(
                hosts, module.object_string_property,
                module._integer_object_property,
            )
            config = module.create_curve_inheriting_c10_turnout(
                document, hosts[selected["index"]],
                recipe.TURNOUT_CHAINAGE_MM, module.TURNOUT_HAND_LEFT,
                module.TURNOUT_ORIENTATION_FACING,
                recipe.TRACK_GAUGE_MM, recipe.FLANGEWAY_MM,
            )
            assert config["turnout_id"] == identifier
            module.create_turnout_host_integration(document, identifier)
        else:
            config, _selection = SIGNATURE.timbers.create_controlled_crossover(
                module, document, contract["scenario"]["host_a_chainage_mm"],
            )
            assert config["crossover_id"] == identifier
            b4 = module.apply_crossover_b4_timbering(document, identifier)
            assert b4["resolution_signature"] == contract["scenario"][
                "prerequisite_b4_resolution_signature"
            ]
            integration = module.create_crossover_host_integration(
                document, identifier,
            )
            assert integration["production_ready"] is False
        module.analyse_entity_chair_positions(document, kind, identifier)
        _decision_state(module, document, kind)
        document.save()
        return document
    except Exception:
        App.closeDocument(document.Name)
        raise


def _export_once(module, document, kind, directory):
    """Prove semantic and editable-state continuity across real export."""
    identifier = CASES[kind][0]
    helper = EXPORT_HELPERS[kind]
    before = _decision_state(module, document, kind)
    editable = SIGNATURE._document_state(module, document, kind, identifier)
    objects = {obj.Name: obj for obj in document.Objects}
    shapes = {obj.Name: obj.Shape for obj in document.Objects
              if "Shape" in obj.PropertiesList and not obj.Shape.isNull()}
    prepared = helper._selected_plan(module, document, directory)
    config, plan, skipped, issues, outline, *remaining = prepared
    assert not module.preflight_blocking_report(issues), issues
    if kind == "crossover":
        warnings = [item for item in issues if item["issue_code"] ==
                    "CROSSOVER_CHAIR_VALIDATION_OUTSTANDING"]
        assert len(warnings) == 1
        assert warnings[0]["severity"] == "Warning"
        assert warnings[0]["blocks_export"] is False
    _assert_decisions_equal(before, _decision_state(module, document, kind))
    assert SIGNATURE._document_state(
        module, document, kind, identifier,
    ) == editable, "Production preflight changed editable document state"
    summary = helper._export(module, document, config, plan, skipped)
    assert summary["successful_files"] == 2 and summary["failed_files"] == 0
    assert summary["formats"] == ["SVG"]
    assert summary["manifest_path"] == plan["manifest_path"]
    if kind == "turnout":
        content, _bindings = helper._output_witness(
            module, directory, plan, outline, remaining[0],
        )
    else:
        content = helper._output_witness(module, directory, plan, outline)
    _assert_decisions_equal(before, _decision_state(module, document, kind))
    assert SIGNATURE._document_state(
        module, document, kind, identifier,
    ) == editable, "Selected export changed editable document state"
    for name, obj in objects.items():
        assert document.getObject(name) is obj
    for name, shape in shapes.items():
        assert document.getObject(name).Shape.isSame(shape), name
    return {
        "artifact_hashes": content,
        "issue_codes": [item["issue_code"] for item in issues],
        "exported_record_id": outline["record_id"],
        "exact_decisions_unchanged": True,
        "editable_state_unchanged": True,
    }


def validate():
    """Run bounded native evidence and keep raw outputs in an ignored path."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_CHAIR_EXPORT_CONTINUITY_RUN_DIR",
        ROOT / "benchmark-output/chair-export-continuity" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    sources = {ROOT / item["path"]: item["sha256"]
               for item in contract["source_state"].values()}
    sources[ROOT / contract["fixture"]["path"]] = contract["fixture"]["sha256"]
    for path, expected in sources.items():
        assert SIGNATURE._sha256(path) == expected
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp), "cases": {}}
    document = None
    try:
        module, profile, routing = SIGNATURE._load_product()
        receipt.update({"profile": profile, "routing": routing})
        for kind in CASES:
            document = _prepare_case(module, run_dir, kind)
            before = _decision_state(module, document, kind)
            witnesses = _negative_witnesses(before)
            directory = run_dir / (kind + "-export")
            directory.mkdir()
            result = _export_once(module, document, kind, directory)
            document.save()
            path = document.FileName
            App.closeDocument(document.Name)
            document = App.openDocument(path)
            document.UndoMode = 1
            after = _decision_state(module, document, kind)
            _assert_decisions_equal(before, after)
            repeated_dir = run_dir / (kind + "-reopened-export")
            repeated_dir.mkdir()
            repeated = _export_once(module, document, kind, repeated_dir)
            for key, value in result.items():
                if key != "artifact_hashes":
                    assert repeated[key] == value, key
            manifests = {name: digest for name, digest in
                         result["artifact_hashes"].items()
                         if name.endswith(".csv")}
            assert manifests
            assert {name: digest for name, digest in
                    repeated["artifact_hashes"].items()
                    if name.endswith(".csv")} == manifests
            receipt["cases"][kind] = {
                **result, "chair_count": len(before["chair_result"]["positions"]),
                "timber_count": len(before["timbers"]),
                "production_record_count": len(before["production_records"]),
                "decision_sha256": SIGNATURE._exact_digest(before),
                "negative_witnesses": witnesses,
                "save_reopen_and_repeated_export": True,
                # Keep independent SVG evidence: FCStd serialization can
                # change last-digit coordinates without changing decisions.
                "reopened_artifact_hashes": repeated["artifact_hashes"],
                "normalized_artifact_hashes_equal_after_reopen": (
                    repeated["artifact_hashes"] == result["artifact_hashes"]
                ),
                "production_ready": False,
            }
            App.closeDocument(document.Name)
            document = None
        receipt["status"] = "PASS"
    except Exception:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        preserved = all(SIGNATURE._sha256(p) == value
                        for p, value in sources.items())
        receipt["source_fixture_and_oracles_preserved"] = preserved
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert preserved
    assert not App.listDocuments()
    print("CHAIR_EXPORT_CONTINUITY=" + json.dumps(receipt, sort_keys=True))
    print(SENTINEL, flush=True)
    return receipt


if __name__ in {"__main__", "freecad_validate_chair_export_continuity"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
