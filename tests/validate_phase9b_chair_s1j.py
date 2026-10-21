#!/usr/bin/env python3
"""Prove the S1J research pattern with invented signed inputs.

Tracked dimensions and source records are synthetic test doubles. They
do not describe Templot values, a physical chair or production geometry.
Real reference packages remain in ignored local evidence.
"""

import copy
from dataclasses import replace
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
    chair_model_research,
    chair_research,
)
from tracktemplate.domain.chair_assembly import (  # noqa: E402
    assemble_chair_components,
    assemble_s1j_chair_components,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_assembly as assembly_tests  # noqa: E402
from validate_phase9a_chair_l1 import (  # noqa: E402
    synthetic_l1_package_records,
)
from validate_phase9a_chair_model_scale import (  # noqa: E402
    LENGTH_FACTOR,
    REQUEST,
    VOLUME_FACTOR,
    assert_diagnostic,
    request_rejections,
)
from validate_phase9a_chair_rail_interface import load_package  # noqa: E402
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    signed_boundary_volume,
)


SENTINEL = "Phase 9B chair S1J standalone validation passed"
PACKAGE_ID = "tracktemplate:test:synthetic-research-s1j"
# Invented full-size mm values, selected before implementing this variant.
# Base/seat half-width 18; unchanged jaw reference half-width 14.
EXPECTED_SEAT = {
    "top-gauge-negative": (-14, -4, 8),
    "top-gauge-positive": (14, -4, 8),
    "top-foot-positive": (14, 4, 8),
    "top-outer-positive": (3, 9, 8),
    "top-outer-negative": (-3, 9, 8),
    "top-foot-negative": (-14, 4, 8),
    "bottom-gauge-negative": (-17, -4, 1),
    "bottom-gauge-positive": (17, -4, 1),
    "bottom-foot-positive": (17, 4, 1),
    "bottom-outer-positive": (16, 9, 3),
    "bottom-outer-negative": (-16, 9, 3),
    "bottom-foot-negative": (-17, 4, 1),
}
# Rail-seat prism: 1736 mm3. Under-key wedge: 2470/3 mm3.
EXPECTED_SEAT_VOLUME = Fraction(7678, 3)


def _quantity(record, role, purpose):
    return next(item for item in record["definition"]["quantities"]
                if item["quantity_id"] == "quantity:test:{}:{}".format(
                    role, purpose,
                ))


def _set_quantity(record, role, purpose, value):
    quantity = _quantity(record, role, purpose)
    quantity["source_value"] = quantity["canonical_value"] = value


def synthetic_s1j_package_records():
    """Separate wider base/seat inputs from the unchanged mock S1 jaws."""
    record, manifest = assembly_tests.synthetic_assembly_package_records()
    record["package"]["package_id"] = PACKAGE_ID
    definition = record["definition"]
    definition["definition_id"] = PACKAGE_ID + ":definition"
    definition["prototype_designation"] = "Synthetic S1J pattern test double"
    record["dependency_manifest"].update({
        "manifest_id": PACKAGE_ID + ":manifest", "subject_id": PACKAGE_ID,
    })
    manifest["manifest_id"] = PACKAGE_ID + ":manifest"
    manifest["subject"]["identifier"] = PACKAGE_ID
    manifest["project_status"]["decision_reference"] = (
        "tests/validate_phase9b_chair_s1j.py"
    )
    rules = {
        chair_research.CHAIR_BASE_RESEARCH_RULE_ID:
            chair_research.CHAIR_S1J_BASE_RESEARCH_RULE_ID,
        chair_research.CHAIR_SEAT_RESEARCH_RULE_ID:
            chair_research.CHAIR_S1J_SEAT_RESEARCH_RULE_ID,
    }
    for procedure in definition["procedures"]:
        procedure["rule_id"] = rules.get(
            procedure["rule_id"], procedure["rule_id"],
        )
    for role in ("base-plinth", "rail-seat"):
        _set_quantity(record, role, "chair_half_width_mm", "18")
    _set_quantity(record, "rail-seat", "seat_top_half_width_mm", "14")
    quantities = {q["quantity_id"]: q for q in definition["quantities"]}
    digests = {}
    for dependency in manifest["dependencies"]:
        suffix = dependency["identifier"].removeprefix("dependency:test:")
        quantity = quantities.get("quantity:test:" + suffix)
        value = quantity["source_value"] if quantity else "context"
        description = "Invented S1J-pattern source: {}={}".format(
            suffix, value,
        )
        digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
        dependency["name"] = description
        dependency["source"].update({
            "creator_or_supplier": "TrackTemplate synthetic S1J test",
            "locator": "synthetic-test-double://chair-s1j/" + suffix,
            "evidence_sha256": digest,
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9b_chair_s1j.py"
        )
        digests[suffix] = digest
    for lineage in record["lineage"]:
        suffix = lineage["lineage_id"].removeprefix("lineage:test:")
        lineage["source_file_sha256s"] = [digests[suffix]]
    return resign_package(record, manifest), manifest


def _expect_package_rejection(record, manifest, expected):
    resign_package(record, manifest)
    original = copy.deepcopy((record, manifest))
    try:
        package, text = load_package(record, manifest)
        chair_model_research.prepare_chair_s1j_model_research(
            package, text, REQUEST,
        )
    except definitions.ChairDefinitionError as error:
        assert_diagnostic(error, expected)
    else:
        raise AssertionError("invalid signed S1J package was accepted")
    assert (record, manifest) == original


def _geometry_mutations(record, manifest):
    for label, updates in (
        ("base-seat-width", (("rail-seat", "chair_half_width_mm", "17"),)),
        ("jaw-reference-width",
         (("inner-jaw", "chair_half_width_mm", "15"),)),
        ("s1-width-alias", (
            ("base-plinth", "chair_half_width_mm", "14"),
            ("rail-seat", "chair_half_width_mm", "14"),
        )),
        ("widened-jaws", (
            ("outer-jaw", "chair_half_width_mm", "18"),
            ("inner-jaw", "chair_half_width_mm", "18"),
        )),
        ("corner-reference",
         (("inner-jaw", "outer_corner_radius_mm", "1"),)),
        ("outer-inner-reference",
         (("inner-jaw", "outer_top_half_width_mm", "6"),)),
    ):
        bad, related = copy.deepcopy((record, manifest))
        for role, purpose, value in updates:
            _set_quantity(bad, role, purpose, value)
        yield label, bad, related


def validate_rejections(record, manifest, assembly):
    count = 0
    for _name, bad, related in assembly_tests._mutations(record, manifest):
        _expect_package_rejection(
            bad, related, assembly_tests.EXPECTED_REJECTION_CODES[_name],
        )
        count += 1
    for _name, bad, related in _geometry_mutations(record, manifest):
        _expect_package_rejection(
            bad, related, "research-assembly-geometry-invalid",
        )
        count += 1
    for source, target in (
        (chair_research.CHAIR_S1J_BASE_RESEARCH_RULE_ID,
         chair_research.CHAIR_BASE_RESEARCH_RULE_ID),
        (chair_research.CHAIR_S1J_SEAT_RESEARCH_RULE_ID,
         chair_research.CHAIR_SEAT_RESEARCH_RULE_ID),
    ):
        bad, related = copy.deepcopy((record, manifest))
        next(p for p in bad["definition"]["procedures"]
             if p["rule_id"] == source)["rule_id"] = target
        _expect_package_rejection(
            bad, related, "research-assembly-procedures",
        )
        count += 1
    for factory in (
        assembly_tests.synthetic_assembly_package_records,
        synthetic_l1_package_records,
    ):
        bad, related = factory()
        # The display label cannot select a supported structural family.
        bad["definition"]["prototype_designation"] = "S1J"
        _expect_package_rejection(
            bad, related, "research-assembly-procedures",
        )
        count += 1
    for components in (
        tuple(reversed(assembly.components)),
        assembly.components[:-1],
    ):
        try:
            assemble_s1j_chair_components(components)
        except ValueError:
            count += 1
        else:
            raise AssertionError("invalid component role/order was accepted")
    changed = list(assembly.components)
    role, geometry = changed[2]
    landmarks = dict(geometry.landmarks)
    landmarks["base-origin"] = (Fraction(1), Fraction(0), Fraction(0))
    changed[2] = (role, replace(
        geometry, landmarks=tuple(landmarks.items()),
    ))
    try:
        assemble_s1j_chair_components(tuple(changed))
    except ValueError as error:
        assert "landmark frame differs" in str(error)
        count += 1
    else:
        raise AssertionError("changed component frame was accepted")
    try:
        assemble_chair_components(assembly.components)
    except ValueError as error:
        assert "shared input differs: chair_half_width_mm" in str(error)
        count += 1
    else:
        raise AssertionError("existing S1 assembly accepted split widths")
    return count


def validate_geometry(full_size, original_s1):
    geometries = dict(full_size.geometry.components)
    previous = dict(original_s1.geometry.components)
    assert tuple(geometries) == assembly_tests.CHAIR_ASSEMBLY_ROLES
    assert {name: tuple(point) for name, *point
            in geometries["rail-seat"].vertices} == EXPECTED_SEAT
    assert geometries["rail-seat"].volume_mm3 == EXPECTED_SEAT_VOLUME
    assert signed_boundary_volume(geometries["rail-seat"]) == (
        EXPECTED_SEAT_VOLUME
    )
    # A whole-grid four-millimetre width increase translates each source
    # outline/plinth point outward without changing Y, Z or incidence.
    for before, after in zip(
        previous["base-plinth"].vertices,
        geometries["base-plinth"].vertices,
    ):
        name, x, y, z = before
        assert x != 0
        assert after == (name, x + (4 if x > 0 else -4), y, z)
    assert geometries["base-plinth"].faces == previous["base-plinth"].faces
    for role in ("key", "outer-jaw", "inner-jaw"):
        assert geometries[role] == previous[role], role
    assert dict(full_size.geometry.landmarks) == (
        assembly_tests.COMMON_LANDMARKS_MM
    )
    assert full_size.geometry.bounds_mm == (
        Fraction(-18), Fraction(-57, 4), Fraction(0),
        Fraction(18), Fraction(35, 2), Fraction(59, 2),
    )


def validate_model(model, full_size):
    assert model.full_size_research == full_size
    assert model.length_unit == "mm" and model.length_basis == "model"
    assert model.scale_denominator == Fraction(381, 5)
    assert model.geometry.bounds_mm == tuple(
        v * LENGTH_FACTOR for v in full_size.geometry.bounds_mm
    )
    assert model.geometry.component_volume_sum_mm3 == (
        full_size.geometry.component_volume_sum_mm3 * VOLUME_FACTOR
    )
    for source, target in zip(full_size.components, model.components):
        a, b = source.geometry, target.geometry
        assert target.component_id == source.component_id
        assert target.procedure_id == source.procedure_id
        assert b.vertices == tuple(
            (name, x * LENGTH_FACTOR, y * LENGTH_FACTOR, z * LENGTH_FACTOR)
            for name, x, y, z in a.vertices
        )
        assert b.faces == a.faces
        assert b.volume_mm3 == a.volume_mm3 * VOLUME_FACTOR
        assert b.landmarks == tuple(
            (name, tuple(v * LENGTH_FACTOR for v in point))
            for name, point in a.landmarks
        )
    signed_request = {
        "contract_id": REQUEST["contract_id"],
        "package_signature": model.package.content_signature,
        "manifest_signature": full_size.manifest_signature,
        "request": REQUEST,
    }
    expected = hashlib.sha256(
        canonical_json(signed_request).encode("utf-8")
    ).hexdigest()
    assert model.request_signature == "sha256:" + expected


def main():
    record, manifest = synthetic_s1j_package_records()
    assert validate_document(manifest) == []
    original = copy.deepcopy((record, manifest))
    package, text = load_package(record, manifest)
    full_size = chair_research.prepare_chair_s1j_assembly_research(
        package, text,
    )
    old_record, old_manifest = (
        assembly_tests.synthetic_assembly_package_records()
    )
    old_package, old_text = load_package(old_record, old_manifest)
    original_s1 = chair_research.prepare_chair_assembly_research(
        old_package, old_text,
    )
    validate_geometry(full_size, original_s1)
    model = chair_model_research.prepare_chair_s1j_model_research(
        package, text, REQUEST,
    )
    validate_model(model, full_size)
    encoded = definitions.chair_definition_package_to_json(package)
    reopened = definitions.chair_definition_package_from_json(encoded, text)
    with (
        patch("builtins.open", side_effect=AssertionError("source read")),
        patch.object(Path, "open", side_effect=AssertionError("source read")),
    ):
        repeated = chair_model_research.prepare_chair_s1j_model_research(
            reopened, text, dict(reversed(tuple(REQUEST.items()))),
        )
    assert repeated == model
    assert definitions.chair_definition_package_to_json(reopened) == encoded
    assert package.to_record() == record and (record, manifest) == original
    assert definitions.chair_definition_package_status(
        package, text,
    )["production_geometry_authorized"] is False
    for operation in (
        chair_research.prepare_chair_assembly_research,
        chair_research.prepare_chair_l1_assembly_research,
    ):
        try:
            operation(package, text)
        except chair_research.ChairResearchError as error:
            assert_diagnostic(error, "research-assembly-procedures")
        else:
            raise AssertionError("S1J package entered another family")
    rejections = validate_rejections(record, manifest, full_size.geometry)
    for name, request, expected in request_rejections():
        before = copy.deepcopy(request)
        try:
            chair_model_research.prepare_chair_s1j_model_research(
                package, text, request,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, expected)
        else:
            raise AssertionError(name + ": invalid model request accepted")
        assert request == before
        rejections += 1
    corrupt = copy.deepcopy(record)
    corrupt["definition"]["quantities"][0]["canonical_value"] = "999"
    try:
        load_package(corrupt, manifest)
    except definitions.ChairDefinitionError:
        rejections += 1
    else:
        raise AssertionError("unsigned package mutation was accepted")
    assert chair_research.prepare_chair_assembly_research(
        old_package, old_text,
    ) == original_s1
    print(json.dumps({
        "component_count": 5, "rejections": rejections,
        "source_free_regeneration": True, "shared_jaws_and_key_unchanged": True,
        "reference_only": True, "production_accepted": False,
        "physical_fit_proved": False, "phase_exit_accepted": False,
    }, sort_keys=True))
    print(SENTINEL)


if __name__ == "__main__":
    main()
