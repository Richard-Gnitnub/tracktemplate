"""Compare one straight-host XO-001 B4 result in qualified FreeCAD.

The B14-generated source is copied for each macro. The comparison covers
railway records, findings, object geometry and production bindings. B16
also proves unchanged reuse, Undo/Redo and save/reopen on its copy.
"""

import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402
from tools.freecad_bridge.ordinary_track_recipe import (  # noqa: E402
    ordinary_track_document_snapshot,
)


SENTINEL = "Phase 8 straight-host crossover B4 FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
SOURCE_RECIPE = "phase8-b14-straight-host-source-v1"
SOURCE_WITNESS = (
    "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
)
SOURCE_DOCUMENT_SEMANTIC = (
    "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5"
)
SOURCE_RECEIPT = pathlib.Path(os.environ.get(
    "TRACKTEMPLATE_STRAIGHT_CROSSOVER_SOURCE_RECEIPT", "",
)).resolve()
BASE_SPEC = importlib.util.spec_from_file_location(
    "phase8_straight_crossover_base",
    ROOT / "tests/freecad_validate_phase8_straight_host_crossover.py",
)
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source():
    """Verify the existing B14 source-generation receipt and raw fixture."""
    assert SOURCE_RECEIPT.is_file(), (
        "Set TRACKTEMPLATE_STRAIGHT_CROSSOVER_SOURCE_RECEIPT to a "
        "completed phase8-straight-host B14 generation receipt"
    )
    receipt = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["recipe_id"] == SOURCE_RECIPE
    assert receipt["scenario"] == "phase8-straight-host"
    assert receipt["status"] == "completed"
    assert receipt["comparison_witness_sha256"] == SOURCE_WITNESS
    assert receipt["recipe"]["save_reopen"]["semantic_sha256"] == (
        SOURCE_WITNESS
    )
    assert receipt["source_fixture_sha256_after"] == (
        receipt["source_fixture_sha256"]
    )
    source = pathlib.Path(receipt["run_document"]).resolve()
    assert source.is_file()
    assert _sha256(source) == receipt["run_document_sha256"]
    return source


def _history(document):
    return {
        "undo": int(document.UndoCount),
        "redo": int(document.RedoCount),
        "undo_names": tuple(str(item) for item in document.UndoNames),
        "redo_names": tuple(str(item) for item in document.RedoNames),
    }


def _production(module, document):
    settings = module.settings_for_template_set(document, "SET-001")
    assert settings is not None
    index = module.read_production_record_index(settings)
    assert index is not None
    assert index["schema_version"] == 2
    assert index["template_set_id"] == "SET-001"
    records = index["records"]
    assert len(records) == 16
    crossover = [item for item in records if item["route_id"] == "XO-001"]
    assert len(crossover) == 4
    for record in crossover:
        assert record["source_binding_type"] == "direct"
        source = document.getObject(record["source_name"])
        assert source is not None
        assert record["record_id"] in json.loads(
            module.object_string_property(
                source, "ProductionRecordIDsJSON", ""
            )
        )
    return index, crossover


def _neutral_index(index):
    """Exclude only evidenced version and generation time fields."""
    assert isinstance(index["macro_version"], str)
    assert isinstance(index["created_at"], str)
    return {
        key: value for key, value in index.items()
        if key not in {"macro_version", "created_at"}
    }


def _stored_b4(module, document, returned):
    """Prove stable records bind to both B4 and settings objects."""
    obj = module._crossover_b4_object(document, "XO-001")
    assert obj is not None
    assert obj.Name == "CrossoverB4Timbering_XO_001"
    assert module.object_string_property(
        obj, "GeneratedRole", ""
    ) == module.CROSSOVER_B4_ROLE
    assert module.object_string_property(
        obj, module.CROSSOVER_ID_PROPERTY, ""
    ) == "XO-001"
    stored_records = json.loads(str(obj.B4TimberRecordsJSON))
    assert stored_records == returned["resolved_timbers"]
    settings = [
        item for item in module._crossover_objects(document, "XO-001")
        if module.object_string_property(item, "GeneratedRole", "")
        == module.CROSSOVER_SETTINGS_ROLE
    ]
    assert len(settings) == 1
    persisted = json.loads(module.object_string_property(
        settings[0], module.CROSSOVER_B4_RESULT_PROPERTY, ""
    ))
    assert persisted["resolved_timbers"] == stored_records
    assert module.crossover_config_by_id(
        document, "XO-001"
    )["b4_result"]["resolved_timbers"] == stored_records
    return {
        "name": str(obj.Name),
        "role": module.object_string_property(obj, "GeneratedRole", ""),
        "shape": base._shape_state(obj.Shape),
        "record_sha256": recipe.digest(stored_records),
    }


def _observe(module, document, returned, before_index):
    assert returned.get("cache_reused") is False
    core = recipe.result_snapshot(module, returned)
    assert core["counts"]["effective_timber_count"] == 82
    assert core["counts"]["shared_timber_count"] == 18
    assert core["counts"]["unresolved_count"] == 0
    assert core["counts"]["remaining_production_conflicts"] == 0
    assert core["counts"]["timber_resolution_complete"] is True
    assert len(document.Objects) == 34
    full_records = recipe.stable(returned["resolved_timbers"])
    stable_records = [
        module._b4_stable_record(item) for item in returned["resolved_timbers"]
    ]
    identities = [item["stable_identity"] for item in full_records]
    assert len(identities) == len(set(identities)) == 82
    assert core["record_identity_sha256"] == recipe.digest(identities)
    assert core["stable_record_sha256"] == recipe.digest(sorted(
        stable_records, key=lambda item: item["id"],
    ))
    after_index, bound = _production(module, document)
    assert after_index == before_index, "B4 changed production index"
    b4 = _stored_b4(module, document, returned)
    assert b4["shape"] is not None
    return {
        "core": core,
        "full_ordered_records": full_records,
        "stable_ordered_records": stable_records,
        "inherited_findings": recipe.stable(
            returned["inherited_analysis"]["findings"]
        ),
        "resolved_findings": recipe.stable(
            returned["resolved_analysis"]["findings"]
        ),
        "unresolved": recipe.stable(returned["unresolved"]),
        "object_map": recipe.object_map(module, document),
        "b4_object": b4,
        "production_index": _neutral_index(after_index),
        "production_bindings": bound,
    }


def _b16_lifecycle(module, document, first, observation, before):
    """Prove reuse, one Undo unit, Redo and copied-file persistence."""
    after = recipe.document_snapshot(module, document, "XO-001")
    after_history = _history(document)
    assert after_history["undo"] == before["history"]["undo"] + 1
    reused = module.apply_crossover_b4_timbering(document, "XO-001")
    assert reused["cache_reused"] is True
    assert reused["resolved_timbers"] == first["resolved_timbers"]
    assert recipe.result_snapshot(module, reused) == observation["core"]
    assert recipe.document_snapshot(module, document, "XO-001") == after
    assert _history(document) == after_history
    document.undo()
    document.recompute()
    undone = recipe.document_snapshot(module, document, "XO-001")
    assert len(document.Objects) == 32
    assert module._crossover_b4_object(document, "XO-001") is None
    assert undone == before["document"]
    assert _history(document)["redo"] == 1
    document.redo()
    document.recompute()
    assert len(document.Objects) == 34
    assert recipe.document_snapshot(module, document, "XO-001") == after
    assert _history(document)["redo"] == 0
    document.save()
    path = pathlib.Path(document.FileName)
    App.closeDocument(document.Name)
    reopened = App.openDocument(str(path))
    assert len(reopened.Objects) == 34
    reopened_b4 = module._crossover_b4_object(reopened, "XO-001")
    assert reopened_b4 is not None
    assert base._shape_state(reopened_b4.Shape)["summary"] == (
        observation["b4_object"]["shape"]["summary"]
    )
    reopened_index, rebound = _production(module, reopened)
    assert _neutral_index(reopened_index) == observation["production_index"]
    assert rebound == observation["production_bindings"]
    reopened_config = module.crossover_config_by_id(reopened, "XO-001")
    assert reopened_config["b4_result"]["resolved_timbers"] == (
        first["resolved_timbers"]
    )
    # The saved JSON restores tuple-valued findings as lists.
    expected_analysis = json.loads(json.dumps(
        recipe.stable(first["resolved_analysis"]), sort_keys=True,
    ))
    assert recipe.stable(
        reopened_config["b4_result"]["resolved_analysis"]
    ) == expected_analysis
    return reopened, {
        "after_apply": 34,
        "after_undo": 32,
        "after_redo": 34,
        "after_reopen": 34,
        "cache_reused": True,
    }


def validate():
    assert not App.listDocuments(), "Use an empty FreeCADCmd process"
    source = _source()
    source_hash = _sha256(source)
    receipt_hash = _sha256(SOURCE_RECEIPT)
    contract = json.loads(base.LEGACY_CONTRACT.read_text(encoding="utf-8"))
    modules = {}
    for label in ("B14", "B15"):
        state = contract["source_state"][label.lower()]
        macro = ROOT / state["path"]
        assert _sha256(macro) == state["sha256"]
        modules[label] = base._load_legacy(label, macro)
        assert str(modules[label].MACRO_VERSION_NUMBER) == state["version"]
    modules["B16"] = base._load_b16()
    observations = {}
    lifecycle = None
    with tempfile.TemporaryDirectory(prefix="phase8-straight-xo-b4-") as temp:
        for label, module in modules.items():
            copied = pathlib.Path(temp) / (label.lower() + ".FCStd")
            shutil.copy2(source, copied)
            document = App.openDocument(str(copied))
            try:
                document.UndoMode = 1
                assert len(document.Objects) == 23
                semantic = ordinary_track_document_snapshot(
                    module, document,
                )["semantic_sha256"]
                assert semantic == SOURCE_DOCUMENT_SEMANTIC
                hosts = base._hosts(module, document)
                arguments = base._args(module, document, hosts)
                solved = module.solve_rea_c10_crossover_geometry(*arguments)
                config = module.create_rea_c10_crossover(
                    *arguments, pre_solved=solved,
                )
                assert config["crossover_id"] == "XO-001"
                assert len(document.Objects) == 32
                before_index, _ = _production(module, document)
                before = {
                    "document": recipe.document_snapshot(
                        module, document, "XO-001"
                    ),
                    "history": _history(document),
                }
                first = module.apply_crossover_b4_timbering(
                    document, "XO-001"
                )
                observations[label] = _observe(
                    module, document, first, before_index,
                )
                if label == "B16":
                    document, lifecycle = _b16_lifecycle(
                        module, document, first, observations[label], before,
                    )
            finally:
                for opened in list(App.listDocuments().values()):
                    if pathlib.Path(opened.FileName) == copied:
                        App.closeDocument(opened.Name)
            assert _sha256(source) == source_hash
    assert observations["B14"] == observations["B15"]
    assert observations["B15"] == observations["B16"]
    assert lifecycle is not None
    assert _sha256(source) == source_hash
    assert _sha256(SOURCE_RECEIPT) == receipt_hash
    witness = {
        "status": "PASS",
        "sentinel": SENTINEL,
        "host_profile_id": PROFILE,
        "source_receipt": str(SOURCE_RECEIPT),
        "source_receipt_sha256": receipt_hash,
        "source_fixture": str(source),
        "source_fixture_sha256": source_hash,
        "source_fixture_sha256_after": _sha256(source),
        "source_document_semantic_sha256": SOURCE_DOCUMENT_SEMANTIC,
        "comparison": observations,
        "b16_lifecycle": lifecycle,
    }
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    output = ROOT / "benchmark-output/freecad-bridge/"
    output /= "phase8-straight-crossover-b4-headless-runs"
    output /= stamp
    output.mkdir(parents=True, exist_ok=False)
    receipt_path = output / "receipt.json"
    receipt_path.write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("PHASE8_STRAIGHT_CROSSOVER_B4_RECEIPT=" + str(receipt_path))
    print("PHASE8_STRAIGHT_CROSSOVER_B4_RECORD_SHA256=" + (
        observations["B16"]["core"]["stable_record_sha256"]
    ))
    print(SENTINEL)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase8_straight_crossover_b4"}:
    _run_as_script()
