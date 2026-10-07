#!/usr/bin/env python3
"""Prove explicit model projection using invented assembly inputs only.

The inherited fixture describes no physical chair. Exact arithmetic and
numerical checks here establish no manufacturing or rail-fit tolerance.
"""

import copy
from dataclasses import FrozenInstanceError
from fractions import Fraction
import hashlib
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
from tracktemplate.domain.chair_model_scale import (  # noqa: E402
    project_chair_assembly_to_model,
)
import validate_phase9a_chair_assembly as assembly_tests  # noqa: E402
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)


SENTINEL = "Phase 9A chair model scale standalone validation passed"
REQUEST = {
    "contract_id": "tracktemplate.chair-model-scale-research-request.v1",
    "scale_denominator": "76.2",
    "source_frame_id": "chair-local-right-handed-v1",
    "origin_datum": (
        "longitudinal-chair-centre-plane/rail-section-centre-plane/"
        "base-mounting-plane"
    ),
}
# Independent exact conversion: 4 mm per 304.8 mm gives 5/381.
LENGTH_FACTOR = Fraction(5, 381)
AREA_FACTOR = Fraction(25, 145161)
VOLUME_FACTOR = Fraction(125, 55306341)
MODEL_BOUNDS_MM = (
    Fraction(-70, 381), Fraction(-95, 508), Fraction(0),
    Fraction(70, 381), Fraction(175, 762), Fraction(295, 762),
)
MODEL_LANDMARKS_MM = {
    "base-origin": (0, 0, 0),
    "rail-seat-centre": (0, 0, Fraction(40, 381)),
    "rail-top-centre": (0, 0, Fraction(160, 381)),
    "gauge-face-at-seat": (0, Fraction(-5, 127), Fraction(40, 381)),
}


def request_rejections():
    """Invalid records and aliases cannot acquire an implicit scale."""
    invalid = "research-model-request-invalid"
    for value in (None, [], "76.2", 76.2, True):
        yield "non-record-" + repr(value), value, invalid
    for field in REQUEST:
        missing = dict(REQUEST)
        del missing[field]
        yield "missing-" + field, missing, invalid
        yield "wrong-type-" + field, dict(REQUEST, **{field: None}), invalid
    yield "extra-field", dict(REQUEST, compensation_mm="0"), invalid
    yield "wrong-contract", dict(REQUEST, contract_id="future.v2"), invalid
    for value in (76.2, 0, True, Fraction(381, 5)):
        yield "numeric-scale-" + repr(value), dict(
            REQUEST, scale_denominator=value,
        ), invalid
    for value in ("76.20", "381/5", " 76.2", "76.2 ", "1", "0",
                  "-76.2", "NaN", "Infinity", "", "152.4"):
        yield "unsupported-scale-" + value, dict(
            REQUEST, scale_denominator=value,
        ), "research-model-scale-unsupported"
    for field, value in (
        ("source_frame_id", "source-rail-top"),
        ("origin_datum", "rail-top-centre"),
    ):
        yield "unsupported-" + field, dict(
            REQUEST, **{field: value},
        ), "research-model-frame-unsupported"


def assert_diagnostic(error, expected_code):
    """Every rejection is recoverable and preserves external state."""
    assert error.code == expected_code, (error.code, expected_code)
    diagnostic = error.diagnostic()
    assert diagnostic["recoverable"] is True
    assert diagnostic["document_mutation"] is False
    assert diagnostic["filesystem_mutation"] is False


def validate_projection(model, full_size):
    """Check every coordinate plus independently reduced scale results."""
    assert model.full_size_research == full_size
    assert model.package is full_size.package
    assert model.manifest_json == full_size.manifest_json
    assert model.manifest_signature == full_size.manifest_signature
    assert model.length_unit == "mm" and model.length_basis == "model"
    assert model.scale_denominator == Fraction(381, 5)
    assert model.geometry.bounds_mm == MODEL_BOUNDS_MM
    assert dict(model.geometry.landmarks) == MODEL_LANDMARKS_MM
    assert full_size.geometry.bounds_mm == assembly_tests.EXPECTED_BOUNDS_MM
    assert dict(full_size.geometry.landmarks) == (
        assembly_tests.COMMON_LANDMARKS_MM
    )
    assert model.geometry.component_volume_sum_mm3 == (
        full_size.geometry.component_volume_sum_mm3 * VOLUME_FACTOR
    )
    assert len(model.components) == 5
    vertex_count = 0
    for role, model_part, full_part, (geometry_role, geometry) in zip(
        assembly_tests.CHAIR_ASSEMBLY_ROLES, model.components,
        full_size.components, model.geometry.components,
    ):
        source = full_part.geometry
        assert model_part.role == geometry_role == role
        assert model_part.component_id == full_part.component_id
        assert model_part.procedure_id == full_part.procedure_id
        assert model_part.geometry == geometry
        assert type(geometry) is not type(source)
        assert geometry.faces == source.faces
        assert geometry.bounds_mm == tuple(
            value * LENGTH_FACTOR for value in source.bounds_mm
        )
        assert geometry.volume_mm3 == source.volume_mm3 * VOLUME_FACTOR
        assert geometry.landmarks == tuple(
            (name, tuple(value * LENGTH_FACTOR for value in point))
            for name, point in source.landmarks
        )
        assert len(geometry.vertices) == len(source.vertices)
        for projected, original in zip(geometry.vertices, source.vertices):
            assert projected[0] == original[0]
            assert projected[1:] == tuple(
                value * LENGTH_FACTOR for value in original[1:]
            )
            vertex_count += 1
    assert vertex_count == 491
    # A known base corner proves that scaling keeps origin and axis signs.
    assert model.components[0].geometry.vertices[0] == (
        "b00", Fraction(70, 381), Fraction(35, 381), Fraction(0),
    )
    # The synthetic seat's inherited analytical volume is 5714/3 mm^3.
    # Scaling its three length dimensions gives 714250/165919023 mm^3.
    assert full_size.components[1].geometry.volume_mm3 == Fraction(5714, 3)
    assert model.components[1].geometry.volume_mm3 == Fraction(
        714250, 165919023,
    )


def validate_model_scale():
    record, manifest = assembly_tests.synthetic_assembly_package_records()
    original = copy.deepcopy((record, manifest))
    package, text, full_size = assembly_tests.load_research(record, manifest)
    encoded = definitions.chair_definition_package_to_json(package)
    request = copy.deepcopy(REQUEST)
    first = chair_model_research.prepare_chair_model_research(
        package, text, request,
    )
    validate_projection(first, full_size)
    assert request == REQUEST
    assert first.request_json == canonical_json(REQUEST)
    signed_request = {
        "contract_id": REQUEST["contract_id"],
        "package_signature": package.content_signature,
        "manifest_signature": full_size.manifest_signature,
        "request": REQUEST,
    }
    expected_signature = "sha256:" + hashlib.sha256(
        canonical_json(signed_request).encode("utf-8"),
    ).hexdigest()
    assert first.request_signature == expected_signature
    try:
        first.length_basis = "full-size"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("model result is mutable")
    reopened = definitions.chair_definition_package_from_json(encoded, text)

    def refuse_source_read(*_args, **_kwargs):
        raise AssertionError("model projection read a source file")

    with patch("builtins.open", side_effect=refuse_source_read), patch.object(
        Path, "open", side_effect=refuse_source_read,
    ):
        repeated = chair_model_research.prepare_chair_model_research(
            reopened, text, dict(reversed(tuple(REQUEST.items()))),
        )
        original_repeated = chair_research.prepare_chair_assembly_research(
            package, text,
        )
    assert repeated == first and original_repeated == full_size
    assert package.to_record() == record
    assert definitions.chair_definition_package_to_json(package) == encoded
    assert (record, manifest) == original
    assert definitions.chair_definition_package_status(
        package, text,
    )["production_geometry_authorized"] is False
    assert package.project_status == "reference-only"
    assert package.acceptance_status == "not-accepted"
    assert project_chair_assembly_to_model(
        full_size.geometry, Fraction(381, 5),
    ) == first.geometry
    for unsupported in (Fraction(1), Fraction(0), Fraction(-1),
                        Fraction(1524, 10), 76.2, "76.2", None):
        try:
            project_chair_assembly_to_model(full_size.geometry, unsupported)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("unsupported domain scale was accepted")
    for name, bad_request, code in request_rejections():
        retained = copy.deepcopy(bad_request)
        try:
            chair_model_research.prepare_chair_model_research(
                package, text, bad_request,
            )
        except chair_model_research.ChairModelResearchError as error:
            assert_diagnostic(error, code)
        else:
            raise AssertionError(name + ": invalid request accepted")
        assert bad_request == retained
    for name, bad, related in assembly_tests._mutations(record, manifest):
        resign_package(bad, related)
        try:
            bad_text = canonical_json(related)
            bad_package = definitions.chair_definition_package_from_json(
                canonical_json(bad), bad_text,
            )
            chair_model_research.prepare_chair_model_research(
                bad_package, bad_text, REQUEST,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(
                error, assembly_tests.EXPECTED_REJECTION_CODES[name],
            )
        else:
            raise AssertionError(name + ": invalid package accepted")
    # Request identity binds the full package as well as the manifest.
    for change_manifest in (False, True):
        changed, related = copy.deepcopy(original)
        if change_manifest:
            related["project_status"]["decision_reference"] += ":changed"
        else:
            changed["definition"]["description"] += " Signature witness."
        resign_package(changed, related)
        other, other_text, _ = assembly_tests.load_research(changed, related)
        model = chair_model_research.prepare_chair_model_research(
            other, other_text, REQUEST,
        )
        assert model.geometry == first.geometry
        assert model.request_signature != first.request_signature
        assert model.package.content_signature != package.content_signature
        assert (model.manifest_signature != first.manifest_signature) == (
            change_manifest
        )
    assert (record, manifest) == original


def main():
    validate_model_scale()
    print(SENTINEL)


if __name__ == "__main__":
    main()
