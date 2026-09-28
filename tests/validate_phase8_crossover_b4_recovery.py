#!/usr/bin/env python3
"""Check the B16 B4 recovery boundary without a FreeCAD runtime."""

import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility.crossover_b4_recovery import (  # noqa: E402
    CrossoverB4RecoveryAdapter,
    CrossoverB4RecoveryError,
)


SENTINEL = "Phase 8 crossover B4 recovery standalone validation passed"
CONTRACT = ROOT / "reference/contracts/phase1-crossover-timbering.json"


class _Object:
    def __init__(self, name, label):
        self.Name = name
        self.TypeId = "Part::Feature"
        self.Label = label
        self.GeneratedRole = ""
        self.CrossoverID = ""


class _Document:
    def __init__(self):
        self.Objects = [_Object("Original", "Existing document object")]
        self.UndoCount = 0
        self.RedoCount = 0
        self.config = {"crossover_id": "XO-001", "b4_result": None}
        self.analysis = None

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)

    def removeObject(self, name):
        self.Objects = [obj for obj in self.Objects if obj.Name != name]


class _Module:
    CROSSOVER_B4_ROLE = "crossover-b4-timbering"

    def __init__(self, fault_text=None):
        self.fault_text = fault_text
        self.writer_calls = 0
        self._write_crossover_b4_and_timber_analysis_metadata = (
            self._write_metadata
        )

    @staticmethod
    def object_string_property(obj, name, default):
        return str(getattr(obj, name, default))

    @staticmethod
    def crossover_config_by_id(doc, crossover_id):
        if doc.config["crossover_id"] != crossover_id:
            return None
        return json.loads(json.dumps(doc.config))

    def tag_generated_object(self, obj, role, _set_id):
        if self.fault_text is not None:
            raise RuntimeError(self.fault_text)
        obj.GeneratedRole = role

    def _write_metadata(
        self, doc, config, b4_result, analysis_result,
    ):
        self.writer_calls += 1
        doc.config = json.loads(json.dumps(config))
        doc.config["b4_result"] = json.loads(json.dumps(b4_result))
        doc.analysis = json.loads(json.dumps(analysis_result))
        return doc.config, {}, {}


def _state(document):
    return (
        tuple((obj.Name, obj.TypeId, obj.Label) for obj in document.Objects),
        document.UndoCount,
        document.RedoCount,
        json.dumps(document.config, sort_keys=True),
        json.dumps(document.analysis, sort_keys=True),
    )


def _same_method(actual, expected):
    return (
        actual.__self__ is expected.__self__
        and actual.__func__ is expected.__func__
    )


def _fingerprints(contract):
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-timbering:1"
    )
    for label in ("b14", "b15"):
        source = contract["source_state"][label]
        actual = hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
        assert actual == source["sha256"], (label, actual)


def _failure_boundary(contract, *, owned):
    fault = contract["legacy_defects"]["incomplete_abort_cleanup"]
    retained = fault["retained_object"]
    module = _Module(fault["fault_text"])
    document = _Document()
    before = _state(document)
    original_tagger = module.tag_generated_object
    original_writer = (
        module._write_crossover_b4_and_timber_analysis_metadata
    )

    def inherited_apply(doc, crossover_id):
        label = "{} Automatically Resolved Timbering".format(crossover_id)
        if not owned:
            label = "Unrelated document object"
        obj = _Object(retained["name"], label)
        doc.Objects.append(obj)
        module.tag_generated_object(obj, module.CROSSOVER_B4_ROLE, "SET-001")

    adapter = CrossoverB4RecoveryAdapter(
        module, inherited_apply, original_writer,
    )
    assert adapter.apply.__self__ is adapter
    assert adapter.apply.__func__ is CrossoverB4RecoveryAdapter.apply
    try:
        adapter.apply(document, contract["scenario"]["crossover_id"])
    except RuntimeError as error:
        if owned:
            assert type(error) is RuntimeError
            assert str(error) == fault["fault_text"]
        else:
            assert isinstance(error, CrossoverB4RecoveryError)
            assert isinstance(error.__cause__, RuntimeError)
    else:
        raise AssertionError("The injected first-tag fault was accepted")
    assert _same_method(module.tag_generated_object, original_tagger)
    assert _same_method(
        module._write_crossover_b4_and_timber_analysis_metadata,
        original_writer,
    )
    if owned:
        assert _state(document) == before
    else:
        assert len(document.Objects) == len(before[0]) + 1
        assert document.getObject(retained["name"]) is not None


def _persistence_boundary(contract):
    module = _Module()
    document = _Document()
    original_tagger = module.tag_generated_object
    original_writer = (
        module._write_crossover_b4_and_timber_analysis_metadata
    )
    witness = contract["legacy_defects"][
        "resolved_analysis_persistence_drift"
    ]["witness"]
    final_analysis = {
        "geometry_signature": "fixed-xo001-analysis-signature",
        "analysis_basis": witness["first_analysis_basis"],
        "findings": [{"code": "retained-diagnostic"}],
    }
    apply_calls = []

    def inherited_apply(doc, crossover_id):
        apply_calls.append(crossover_id)
        stored = doc.config["b4_result"]
        if stored is not None:
            return dict(stored, cache_reused=True)
        result = {
            "crossover_id": crossover_id,
            "resolution_signature": contract["legacy_semantics"][
                "default_resolution_signature"
            ],
            "resolved_analysis": {"analysis_basis": ""},
        }
        module._write_crossover_b4_and_timber_analysis_metadata(
            doc, doc.config, result, final_analysis,
        )
        result["resolved_analysis"] = final_analysis
        return result

    adapter = CrossoverB4RecoveryAdapter(
        module, inherited_apply, original_writer,
    )
    first = adapter.apply(document, "XO-001")
    stored = document.config["b4_result"]
    assert first["resolved_analysis"] == stored["resolved_analysis"]
    assert stored["resolved_analysis"] == document.analysis
    assert stored["resolved_analysis"]["geometry_signature"]
    assert stored["resolved_analysis"]["analysis_basis"] == (
        witness["first_analysis_basis"]
    )
    assert module.writer_calls == 1
    assert _same_method(module.tag_generated_object, original_tagger)
    assert _same_method(
        module._write_crossover_b4_and_timber_analysis_metadata,
        original_writer,
    )

    after_first = _state(document)
    reused = adapter.apply(document, "XO-001")
    assert reused["cache_reused"] is True
    assert reused["resolved_analysis"] == first["resolved_analysis"]
    assert module.writer_calls == 1
    assert _state(document) == after_first
    assert apply_calls == ["XO-001", "XO-001"]

    def drifted_writer(*_args):
        raise AssertionError("The drifted writer must not run")

    module._write_crossover_b4_and_timber_analysis_metadata = drifted_writer
    try:
        adapter.apply(document, "XO-001")
    except CrossoverB4RecoveryError as error:
        assert "metadata writer changed" in str(error)
    else:
        raise AssertionError("The drifted metadata route was accepted")
    assert _state(document) == after_first
    assert apply_calls == ["XO-001", "XO-001"]
    assert module._write_crossover_b4_and_timber_analysis_metadata is (
        drifted_writer
    )


def validate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _fingerprints(contract)
    _failure_boundary(contract, owned=True)
    _failure_boundary(contract, owned=False)
    _persistence_boundary(contract)
    print(SENTINEL)


if __name__ == "__main__":
    validate()
