#!/usr/bin/env python3
"""Prove one five-component chair assembly with invented research inputs.

The dimensions and source identities here are synthetic test doubles. They
do not describe S1, Templot data, a physical rail or a production package.
"""

import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from tracktemplate.domain.chair_assembly import (  # noqa: E402
    CHAIR_ASSEMBLY_ROLES,
    ChairAssemblyGeometry,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_base as base_tests  # noqa: E402
import validate_phase9a_chair_inner_jaw as inner_tests  # noqa: E402
import validate_phase9a_chair_key as key_tests  # noqa: E402
import validate_phase9a_chair_outer_jaw as outer_tests  # noqa: E402
import validate_phase9a_chair_seat as seat_tests  # noqa: E402


SENTINEL = "Phase 9A chair assembly standalone validation passed"
PACKAGE_ID = "tracktemplate:test:synthetic-research-assembly"
FIXTURES = (
    ("base-plinth", base_tests.synthetic_base_package_records),
    ("rail-seat", seat_tests.synthetic_package_records),
    ("key", key_tests.synthetic_key_package_records),
    ("outer-jaw", outer_tests.synthetic_outer_jaw_package_records),
    ("inner-jaw", inner_tests.synthetic_inner_jaw_package_records),
)
SHARED_VALUES = {
    "chair_half_width_mm": "14",
    "outer_corner_radius_mm": "2",
    "edge_thickness_mm": "1",
    "plinth_thickness_mm": "3",
    "seat_thickness_mm": "8",
    "rail_head_width_mm": "6",
    "rail_foot_width_mm": "8",
    "rail_web_width_mm": "2",
    "rail_depth_mm": "24",
    "outer_jaw_face_mm": "12",
}
ROLE_VALUES = {
    "rail-seat": {"seat_top_half_width_mm": "10"},
    "outer-jaw": {"top_height_mm": "24", "mid_height_mm": "18"},
    "inner-jaw": {
        "outer_top_half_width_mm": "7",
        "outer_mid_half_width_mm": "8",
        "outer_seat_half_width_mm": "9",
        "outer_plinth_half_width_mm": "10",
    },
}
EXPECTED_BOUNDS_MM = (
    Fraction(-14), Fraction(-57, 4), Fraction(0),
    Fraction(14), Fraction(35, 2), Fraction(59, 2),
)
COMMON_LANDMARKS_MM = {
    "base-origin": (0, 0, 0),
    "rail-seat-centre": (0, 0, 8),
    "rail-top-centre": (0, 0, 32),
    "gauge-face-at-seat": (0, -3, 8),
}
EXPECTED_REJECTION_CODES = {
    "missing-role": "research-assembly-components",
    "duplicate-role": "research-assembly-components",
    "duplicate-rule": "research-assembly-procedures",
    "missing-frame": "missing-reference",
    "duplicate-frame": "research-assembly-procedures",
    "missing-interface": "invalid-list",
    "duplicate-interface": "research-assembly-interface",
    "unsupported-clearance": "research-interface-set",
    "wrong-unit": "research-parameter-unit",
    "unresolved-provenance": "research-lineage-unresolved",
    "manufacturing-profile": "research-manufacturing-unsupported",
    "unselected-extra-quantity": "research-unused-quantity",
    "shared-rail-depth-mismatch": "research-frame-inputs",
    "outer-inner-alias-mismatch": "research-assembly-geometry-invalid",
}


def _replace_ids(value, identities):
    if isinstance(value, str):
        return identities.get(value, value)
    if isinstance(value, list):
        return [_replace_ids(item, identities) for item in value]
    if isinstance(value, dict):
        return {key: _replace_ids(item, identities)
                for key, item in value.items()}
    return value


def _role_records(role, factory):
    """Give every mock source and field its own stable assembly identity."""
    record, manifest = factory()
    quantities = record["definition"]["quantities"]
    identities = {
        **{item["quantity_id"]:
           "quantity:test:{}:{}".format(role, item["purpose"])
           for item in quantities},
        **{item["lineage_id"]:
           "lineage:test:{}:{}".format(
               role, item["lineage_id"].split(":")[-1],
           ) for item in record["lineage"]},
        **{item["identifier"]:
           "dependency:test:{}:{}".format(
               role, item["identifier"].split(":")[-1],
           ) for item in manifest["dependencies"]},
    }
    record = _replace_ids(record, identities)
    manifest = _replace_ids(manifest, identities)
    values = dict(SHARED_VALUES, **ROLE_VALUES.get(role, {}))
    for quantity in record["definition"]["quantities"]:
        value = values.get(quantity["purpose"])
        if value is not None:
            quantity["source_value"] = value
            quantity["canonical_value"] = value
    hashes = {}
    for dependency in manifest["dependencies"]:
        name = dependency["identifier"].split(":")[-1]
        quantity = next((item for item in record["definition"]["quantities"]
                         if item["purpose"] == name), None)
        value = quantity["source_value"] if quantity else "context"
        source = "Invented assembly source: {}/{}={}".format(
            role, name, value,
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        dependency["name"] = source
        dependency["source"].update({
            "creator_or_supplier": "TrackTemplate synthetic assembly test",
            "locator": "synthetic-test-double://chair-assembly/{}/{}".format(
                role, name,
            ),
            "evidence_sha256": digest,
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9a_chair_assembly.py"
        )
        hashes[name] = digest
    for lineage in record["lineage"]:
        name = lineage["lineage_id"].split(":")[-1]
        lineage["source_file_sha256s"] = [hashes[name]]
    return record, manifest


def synthetic_assembly_package_records():
    """Compose five signed mock sources without losing any source record."""
    parts = [_role_records(role, factory) for role, factory in FIXTURES]
    record, manifest = copy.deepcopy(parts[1])
    former_id = record["package"]["package_id"]
    record["package"]["package_id"] = PACKAGE_ID
    record["definition"]["definition_id"] = PACKAGE_ID + ":definition"
    record["dependency_manifest"].update({
        "manifest_id": PACKAGE_ID + ":manifest",
        "subject_id": PACKAGE_ID,
    })
    manifest["manifest_id"] = PACKAGE_ID + ":manifest"
    manifest["subject"]["identifier"] = PACKAGE_ID
    manifest["project_status"]["decision_reference"] = (
        "tests/validate_phase9a_chair_assembly.py"
    )
    assert former_id != PACKAGE_ID
    definition = record["definition"]
    quantities, lineages, dependencies = [], [], []
    procedures, components = [definition["procedures"][0]], []
    for role, (item, dependency_manifest) in zip(CHAIR_ASSEMBLY_ROLES, parts):
        assert role == item["definition"]["components"][0]["role"]
        quantities.extend(item["definition"]["quantities"])
        lineages.extend(item["lineage"])
        dependencies.extend(dependency_manifest["dependencies"])
        procedures.append(item["definition"]["procedures"][1])
        components.append(item["definition"]["components"][0])
    definition["quantities"] = sorted(
        quantities, key=lambda item: item["quantity_id"],
    )
    record["lineage"] = sorted(lineages, key=lambda item: item["lineage_id"])
    manifest["dependencies"] = sorted(
        dependencies, key=lambda item: item["identifier"],
    )
    definition["procedures"] = sorted(
        procedures, key=lambda item: item["procedure_id"],
    )
    definition["components"] = sorted(
        components, key=lambda item: item["component_id"],
    )
    definition["rail_interfaces"][0]["procedure_ids"] = sorted(
        item["procedure_id"] for item in procedures[1:]
    )
    return seat_tests.resign_package(record, manifest), manifest


def load_research(record, manifest):
    """Load the complete neutral package before analytical assembly."""
    text = seat_tests.canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        seat_tests.canonical_json(record), text,
    )
    return package, text, chair_research.prepare_chair_assembly_research(
        package, text,
    )


def _expect_rejection(record, manifest):
    seat_tests.resign_package(record, manifest)
    original = copy.deepcopy((record, manifest))
    try:
        load_research(record, manifest)
    except definitions.ChairDefinitionError as error:
        diagnostic = error.diagnostic()
        assert diagnostic["recoverable"] is True
        assert diagnostic["document_mutation"] is False
        assert diagnostic["filesystem_mutation"] is False
        code = error.code
    else:
        raise AssertionError("signed invalid assembly was accepted")
    assert (record, manifest) == original
    return code


def _mutations(record, manifest):
    definition = record["definition"]

    def changed():
        return copy.deepcopy(record), copy.deepcopy(manifest)

    bad, related = changed()
    bad["definition"]["components"].pop()
    yield "missing-role", bad, related

    bad, related = changed()
    duplicate = copy.deepcopy(definition["components"][-1])
    duplicate["component_id"] += ":copy"
    bad["definition"]["components"].append(duplicate)
    bad["definition"]["components"].sort(
        key=lambda item: item["component_id"],
    )
    yield "duplicate-role", bad, related

    bad, related = changed()
    bad["definition"]["procedures"][4]["rule_id"] = (
        bad["definition"]["procedures"][3]["rule_id"]
    )
    yield "duplicate-rule", bad, related

    bad, related = changed()
    bad["definition"]["procedures"].pop(0)
    yield "missing-frame", bad, related

    bad, related = changed()
    frame = copy.deepcopy(definition["procedures"][0])
    frame["procedure_id"] += ":copy"
    frame["output_ids"] = ["result:test:copy-frame"]
    bad["definition"]["procedures"].append(frame)
    bad["definition"]["procedures"].sort(
        key=lambda item: item["procedure_id"],
    )
    yield "duplicate-frame", bad, related

    bad, related = changed()
    bad["definition"]["rail_interfaces"] = []
    yield "missing-interface", bad, related

    bad, related = changed()
    interface = copy.deepcopy(definition["rail_interfaces"][0])
    interface["interface_id"] += ":copy"
    bad["definition"]["rail_interfaces"].append(interface)
    yield "duplicate-interface", bad, related

    bad, related = changed()
    interface = bad["definition"]["rail_interfaces"][0]
    interface["clearance_quantity_ids"] = [
        next(item["quantity_id"] for item in definition["quantities"]
             if item["purpose"] == "rail_head_width_mm")
    ]
    yield "unsupported-clearance", bad, related

    bad, related = changed()
    quantity = next(item for item in bad["definition"]["quantities"]
                    if item["purpose"] == "stand_height_mm")
    quantity.update({
        "quantity_kind": "dimensionless", "source_unit": "1",
        "canonical_unit": "1",
    })
    yield "wrong-unit", bad, related

    bad, related = changed()
    bad["lineage"][0]["evidence_state"] = "unresolved"
    yield "unresolved-provenance", bad, related

    bad, related = changed()
    profile = json.loads((ROOT / "tests/fixtures/"
                          "chair-definition-v1-contract.json").read_text())[
                              "manufacturing_profiles"][0]
    profile["lineage_id"] = "lineage:test:rail-seat:context"
    profile["quantities"][0]["lineage_id"] = profile["lineage_id"]
    bad["manufacturing_profiles"] = [profile]
    yield "manufacturing-profile", bad, related

    bad, related = changed()
    extra = copy.deepcopy(definition["quantities"][0])
    extra["quantity_id"] = "quantity:test:unselected-extra"
    extra["purpose"] = "unselected_extra_mm"
    bad["definition"]["quantities"].append(extra)
    bad["definition"]["quantities"].sort(
        key=lambda item: item["quantity_id"],
    )
    yield "unselected-extra-quantity", bad, related

    bad, related = changed()
    quantity = next(item for item in bad["definition"]["quantities"]
                    if item["quantity_id"] == (
                        "quantity:test:rail-seat:rail_depth_mm"
                    ))
    quantity["canonical_value"] = quantity["source_value"] = "25"
    yield "shared-rail-depth-mismatch", bad, related

    bad, related = changed()
    quantity = next(item for item in bad["definition"]["quantities"]
                    if item["quantity_id"] == (
                        "quantity:test:inner-jaw:outer_top_half_width_mm"
                    ))
    quantity["canonical_value"] = quantity["source_value"] = "6"
    yield "outer-inner-alias-mismatch", bad, related


def validate_assembly():
    record, manifest = synthetic_assembly_package_records()
    assert validate_document(manifest) == []
    original = copy.deepcopy((record, manifest))
    package, text, first = load_research(record, manifest)
    assert isinstance(first.geometry, ChairAssemblyGeometry)
    assert first.package is package
    assert first.manifest_json == text
    assert first.manifest_signature == (
        definitions.chair_definition_manifest_signature(text)
    )
    assert package.to_record() == record
    assert package.project_status == "reference-only"
    assert package.acceptance_status == "not-accepted"
    assert definitions.chair_definition_package_status(
        package, text,
    )["production_geometry_authorized"] is False
    assert len(record["definition"]["procedures"]) == 6
    assert len(record["definition"]["components"]) == 5
    assert len(record["definition"]["rail_interfaces"]) == 1
    assert {item["role"] for item in record["definition"]["components"]
            } == set(CHAIR_ASSEMBLY_ROLES)
    assert len(first.components) == len(first.geometry.components) == 5
    for role, result, item in zip(
        CHAIR_ASSEMBLY_ROLES, first.components, first.geometry.components,
    ):
        assert result.package is package
        assert result.manifest_json == text
        assert result.manifest_signature == first.manifest_signature
        assert result.component_id == "component:test:" + role.replace(
            "base-plinth", "base",
        ).replace("rail-seat", "seat")
        assert item == (role, result.geometry)
        assert result.geometry.parameters.source_to_chair(
            (Fraction(0),) * 3,
        ) == (0, -3, 32)
    assert first.geometry.bounds_mm == EXPECTED_BOUNDS_MM
    assert dict(first.geometry.landmarks) == COMMON_LANDMARKS_MM
    assert first.geometry.component_volume_sum_mm3 == sum(
        item.geometry.volume_mm3 for item in first.components
    )
    purposes = ("rail_head_width_mm", "rail_depth_mm", "seat_thickness_mm")
    for purpose in purposes:
        rows = [item for item in record["definition"]["quantities"]
                if item["purpose"] == purpose]
        assert len(rows) == 5
        assert len({item["quantity_id"] for item in rows}) == 5
        assert len({item["canonical_value"] for item in rows}) == 1
        assert len({item["lineage_id"] for item in rows}) == 5
    assert len({item["source"]["evidence_sha256"] for item in
                manifest["dependencies"]}) == len(manifest["dependencies"])
    assert all(
        item["source"]["locator"].startswith(
            "synthetic-test-double://chair-assembly/"
        ) and item["project_status"]["status"] == "reference-only"
        for item in manifest["dependencies"]
    )
    outer, inner = first.components[-2:]
    for purpose in (
        "seat_depth_mm", "plinth_depth_mm",
        "seat_fillet_radius_mm", "plinth_fillet_radius_mm",
    ):
        assert getattr(outer.geometry.parameters, purpose) != getattr(
            inner.geometry.parameters, purpose,
        )
    reopened = definitions.chair_definition_package_from_json(
        definitions.chair_definition_package_to_json(package), text,
    )
    def refuse_source_read(*_args, **_kwargs):
        raise AssertionError("research rebuild read a source file")

    with patch("builtins.open", side_effect=refuse_source_read), patch.object(
        Path, "open", side_effect=refuse_source_read,
    ):
        second = chair_research.prepare_chair_assembly_research(
            reopened, text,
        )
    assert second == first
    for name in ("seat", "key", "base", "outer_jaw", "inner_jaw"):
        original_prepare = getattr(
            chair_research, "prepare_chair_{}_research".format(name),
        )
        try:
            original_prepare(package, text)
        except definitions.ChairDefinitionError as error:
            assert error.code == "research-procedure-set"
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("single-component path accepted assembly")
    assert (record, manifest) == original
    for name, bad, related in _mutations(record, manifest):
        try:
            assert _expect_rejection(bad, related) == (
                EXPECTED_REJECTION_CODES[name]
            )
        except AssertionError as error:
            raise AssertionError("{}: {}".format(name, error)) from error


def main():
    validate_assembly()
    print(SENTINEL)


if __name__ == "__main__":
    main()
