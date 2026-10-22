#!/usr/bin/env python3
"""Prove the derived L1 model boundary with invented signed inputs.

The fixture is synthetic. Its exact scaling and separate outer-jaw parts
prove no source fidelity, physical fit or manufacturing tolerance.
"""

import copy
from dataclasses import fields, FrozenInstanceError
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_model_research,
    chair_research,
)
from tracktemplate.domain.chair_model_scale import (  # noqa: E402
    ChairModelComponentGeometry,
    ChairModelMultipartComponentGeometry,
    project_chair_assembly_to_model,
)
import validate_phase9a_chair_l1 as l1_tests  # noqa: E402
from validate_phase9a_chair_model_scale import (  # noqa: E402
    REQUEST,
    assert_diagnostic,
    request_rejections,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)
from validate_phase9b_chair_s1j import (  # noqa: E402
    synthetic_s1j_package_records,
)


SENTINEL = "Phase 9B chair L1 model standalone validation passed"
# Independent dimensional conversion: 4 mm per 304.8 full-size mm.
LENGTH_FACTOR = Fraction(5, 381)
VOLUME_FACTOR = Fraction(125, 55306341)
PART_NAMES = ("body", "bevel-negative", "bevel-positive")
SIMPLE_FIELDS = ("vertices", "faces", "bounds_mm", "volume_mm3", "landmarks")


def validate_boundary(projected, original):
    """Compare every named point, incidence and metric in one boundary."""
    assert projected.faces == original.faces
    assert len(projected.vertices) == len(original.vertices)
    for actual, source in zip(projected.vertices, original.vertices):
        assert actual[0] == source[0]
        assert actual[1:] == tuple(
            value * LENGTH_FACTOR for value in source[1:]
        )
    assert projected.bounds_mm == tuple(
        value * LENGTH_FACTOR for value in original.bounds_mm
    )
    assert projected.volume_mm3 == original.volume_mm3 * VOLUME_FACTOR
    assert projected.landmarks == tuple(
        (name, tuple(value * LENGTH_FACTOR for value in point))
        for name, point in original.landmarks
    )
    assert not hasattr(projected, "parameters")
    assert not hasattr(projected, "source_sections_mm")


def validate_projection(model, full_size):
    """Preserve the five components and all three named outer-jaw parts."""
    assert model.full_size_research == full_size
    assert model.package is full_size.package
    assert model.manifest_json == full_size.manifest_json
    assert model.manifest_signature == full_size.manifest_signature
    assert model.length_unit == "mm" and model.length_basis == "model"
    assert model.scale_denominator == Fraction(381, 5)
    assert model.geometry.bounds_mm == tuple(
        value * LENGTH_FACTOR for value in full_size.geometry.bounds_mm
    )
    assert model.geometry.landmarks == tuple(
        (name, tuple(value * LENGTH_FACTOR for value in point))
        for name, point in full_size.geometry.landmarks
    )
    assert model.geometry.component_volume_sum_mm3 == (
        full_size.geometry.component_volume_sum_mm3 * VOLUME_FACTOR
    )
    assert tuple(component.role for component in model.components) == (
        l1_tests.ROLES
    )
    assert tuple(role for role, _part in full_size.geometry.components) == (
        l1_tests.ROLES
    )
    for projected, original, (role, boundary) in zip(
        model.components, full_size.components, model.geometry.components,
    ):
        assert projected.role == role
        assert projected.component_id == original.component_id
        assert projected.procedure_id == original.procedure_id
        assert projected.geometry == boundary
        validate_boundary(boundary, original.geometry)
        expected_type = (ChairModelMultipartComponentGeometry
                         if role == "outer-jaw"
                         else ChairModelComponentGeometry)
        assert type(boundary) is expected_type
    outer = dict(model.geometry.components)["outer-jaw"]
    source = dict(full_size.geometry.components)["outer-jaw"]
    assert tuple(name for name, _part in outer.parts) == PART_NAMES
    for (name, projected), (source_name, original) in zip(
        outer.parts, source.parts,
    ):
        assert name == source_name
        assert type(projected) is ChairModelComponentGeometry
        validate_boundary(projected, original)
    assert outer.vertices == tuple(
        row for _name, part in outer.parts for row in part.vertices
    )
    assert outer.faces == tuple(
        row for _name, part in outer.parts for row in part.faces
    )
    assert outer.volume_mm3 == sum(
        part.volume_mm3 for _name, part in outer.parts
    )
    assert len({row[0] for row in outer.vertices}) == len(outer.vertices)
    # Shared positions keep separate names in the body and each bevel.
    assert len({row[1:] for row in outer.vertices}) < len(outer.vertices)
    try:
        outer.parts = ()
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("projected outer-jaw grouping is mutable")


def validate_synthetic_points(model):
    """Use independent fixture landmarks and reduced model-space values."""
    geometries = dict(model.geometry.components)
    base, seat, outer = (geometries[role] for role in (
        "base-plinth", "rail-seat", "outer-jaw",
    ))
    assert base.bounds_mm == (
        Fraction(-30, 127), Fraction(-20, 127), 0,
        Fraction(30, 127), Fraction(175, 762), Fraction(5, 127),
    )
    assert outer.bounds_mm == (
        Fraction(-20, 127), Fraction(15, 127), Fraction(5, 127),
        Fraction(20, 127), Fraction(80, 381), Fraction(40, 127),
    )
    assert base.volume_mm3 == Fraction(5280937, 737417880)
    # Each synthetic bevel is a tetrahedron: (11/4) * 5 * 6 / 6 mm^3.
    for _name, part in outer.parts[1:]:
        assert part.volume_mm3 == Fraction(6875, 221225364)
    seat_points = {name: tuple(point) for name, *point in seat.vertices}
    assert seat_points["top-gauge-negative"] == (
        Fraction(-50, 381), Fraction(-20, 381), Fraction(40, 381),
    )
    assert seat_points["bottom-outer-positive"] == (
        Fraction(20, 127), Fraction(15, 127), Fraction(5, 127),
    )
    assert dict(model.geometry.landmarks) == {
        "base-origin": (0, 0, 0),
        "rail-seat-centre": (0, 0, Fraction(40, 381)),
        "rail-top-centre": (0, 0, Fraction(160, 381)),
        "gauge-face-at-seat": (0, Fraction(-5, 127), Fraction(40, 381)),
    }


def validate_signature(model):
    """Retain the established complete original-input signature binding."""
    expected = {
        "contract_id": REQUEST["contract_id"],
        "package_signature": model.package.content_signature,
        "manifest_signature": model.manifest_signature,
        "request": REQUEST,
    }
    digest = hashlib.sha256(canonical_json(expected).encode()).hexdigest()
    assert model.request_signature == "sha256:" + digest
    assert model.request_json == canonical_json(REQUEST)


def validate_success():
    """Reconstruct without source reads; retain inputs and full-size state."""
    record, manifest = l1_tests.synthetic_l1_package_records()
    before = copy.deepcopy((record, manifest, REQUEST))
    package, text = l1_tests.load_package(record, manifest)
    encoded = definitions.chair_definition_package_to_json(package)
    full_size = chair_research.prepare_chair_l1_assembly_research(
        package, text,
    )
    first = chair_model_research.prepare_chair_l1_model_research(
        package, text, REQUEST,
    )
    validate_projection(first, full_size)
    validate_synthetic_points(first)
    validate_signature(first)
    reopened = definitions.chair_definition_package_from_json(encoded, text)
    with patch("builtins.open", side_effect=AssertionError("source access")), (
        patch.object(Path, "open", side_effect=AssertionError("source access"))
    ):
        repeated = chair_model_research.prepare_chair_l1_model_research(
            reopened, text, dict(reversed(tuple(REQUEST.items()))),
        )
    assert repeated == first
    assert project_chair_assembly_to_model(
        full_size.geometry, Fraction(381, 5),
    ) == first.geometry
    assert chair_research.prepare_chair_l1_assembly_research(
        package, text,
    ) == full_size
    assert definitions.chair_definition_package_to_json(package) == encoded
    assert (record, manifest, REQUEST) == before
    assert package.project_status == "reference-only"
    assert package.acceptance_status == "not-accepted"
    assert definitions.chair_definition_package_status(
        package, text,
    )["production_geometry_authorized"] is False
    for change_manifest in (False, True):
        changed, related, _request = copy.deepcopy(before)
        if change_manifest:
            related["project_status"]["decision_reference"] += ":witness"
        else:
            changed["definition"]["description"] += " Signature witness."
        resign_package(changed, related)
        other, other_text = l1_tests.load_package(changed, related)
        result = chair_model_research.prepare_chair_l1_model_research(
            other, other_text, REQUEST,
        )
        assert result.geometry == first.geometry
        assert result.request_signature != first.request_signature
        assert (result.manifest_signature != first.manifest_signature) == (
            change_manifest
        )
    return record, manifest


def validate_rejections(record, manifest):
    """Refuse invalid signed inputs and requests before model projection."""
    package, text = l1_tests.load_package(record, manifest)
    observed = {}
    with patch.object(
        chair_model_research, "project_chair_assembly_to_model",
        side_effect=AssertionError("invalid input reached model projection"),
    ):
        for name, request, code in request_rejections():
            before = copy.deepcopy(request)
            try:
                chair_model_research.prepare_chair_l1_model_research(
                    package, text, request,
                )
            except definitions.ChairDefinitionError as error:
                assert_diagnostic(error, code)
                observed[name] = error.code
            else:
                raise AssertionError(name + ": invalid request accepted")
            assert request == before
        observed.update(l1_tests.validate_rejections(
            record, manifest,
            lambda selected, related: (
                chair_model_research.prepare_chair_l1_model_research(
                    selected, related, REQUEST,
                )
            ),
        ))
        # The synthetic inner base end is 9 mm. A 2 mm grid makes its
        # source mark exactly 4.5: the existing ambiguity refusal applies.
        bad, related = copy.deepcopy((record, manifest))
        quantum = next(q for q in bad["definition"]["quantities"]
                       if q["purpose"] == "source_mark_quantum_mm")
        quantum["source_value"] = quantum["canonical_value"] = "2"
        resign_package(bad, related)
        selected, related_text = l1_tests.load_package(bad, related)
        try:
            chair_model_research.prepare_chair_l1_model_research(
                selected, related_text, REQUEST,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, "research-assembly-geometry-invalid")
            assert "ambiguous source mark rounding" in error.detail
            observed["ambiguous-source-mark"] = error.code
        else:
            raise AssertionError("source-mark ambiguity reached projection")
    return observed


def validate_simple_families():
    """Keep both existing model types, fields and signature construction."""
    assert tuple(
        field.name for field in fields(ChairModelComponentGeometry)
    ) == SIMPLE_FIELDS
    for records, prepare in (
        (l1_tests.synthetic_rail_package_records,
         chair_model_research.prepare_chair_model_research),
        (synthetic_s1j_package_records,
         chair_model_research.prepare_chair_s1j_model_research),
    ):
        record, manifest = records()
        package, text = l1_tests.load_package(record, manifest)
        result = prepare(package, text, REQUEST)
        validate_signature(result)
        for projected, original in zip(
            result.components, result.full_size_research.components,
        ):
            assert type(projected.geometry) is ChairModelComponentGeometry
            assert not hasattr(projected.geometry, "parts")
            validate_boundary(projected.geometry, original.geometry)
        try:
            chair_model_research.prepare_chair_l1_model_research(
                package, text, REQUEST,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, "research-assembly-procedures")
        else:
            raise AssertionError("L1 model accepted a different full family")


def main():
    record, manifest = validate_success()
    rejections = validate_rejections(record, manifest)
    validate_simple_families()
    print(json.dumps({
        "component_count": 5, "outer_part_names": PART_NAMES,
        "simple_family_regressions": ["S1", "S1J"],
        "rejections": rejections,
        "source_inputs_unchanged": True,
        "physical_fit_proved": False,
        "production_geometry_authorized": False,
    }, sort_keys=True))
    print(SENTINEL)


if __name__ == "__main__":
    main()
