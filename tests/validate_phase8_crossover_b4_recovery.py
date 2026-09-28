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

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)

    def removeObject(self, name):
        self.Objects = [obj for obj in self.Objects if obj.Name != name]


class _Module:
    CROSSOVER_B4_ROLE = "crossover-b4-timbering"

    def __init__(self, fault_text):
        self.fault_text = fault_text

    @staticmethod
    def object_string_property(obj, name, default):
        return str(getattr(obj, name, default))

    @staticmethod
    def crossover_config_by_id(_doc, crossover_id):
        return {"crossover_id": crossover_id, "b4_result": None}

    def tag_generated_object(self, _obj, _role, _set_id):
        raise RuntimeError(self.fault_text)


def _state(document):
    return (
        tuple((obj.Name, obj.TypeId, obj.Label) for obj in document.Objects),
        document.UndoCount,
        document.RedoCount,
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

    def inherited_apply(doc, crossover_id):
        label = "{} Automatically Resolved Timbering".format(crossover_id)
        if not owned:
            label = "Unrelated document object"
        obj = _Object(retained["name"], label)
        doc.Objects.append(obj)
        module.tag_generated_object(obj, module.CROSSOVER_B4_ROLE, "SET-001")

    adapter = CrossoverB4RecoveryAdapter(module, inherited_apply)
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
    assert module.tag_generated_object.__self__ is original_tagger.__self__
    assert module.tag_generated_object.__func__ is original_tagger.__func__
    if owned:
        assert _state(document) == before
    else:
        assert len(document.Objects) == len(before[0]) + 1
        assert document.getObject(retained["name"]) is not None


def validate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _fingerprints(contract)
    _failure_boundary(contract, owned=True)
    _failure_boundary(contract, owned=False)
    print(SENTINEL)


if __name__ == "__main__":
    validate()
