#!/usr/bin/env python3
"""Check synthetic model projection on the exact qualified FreeCAD host."""

import copy
import itertools
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_assembly_exact,
    chair_model_exact,
)
from tracktemplate.adapters.freecad.chair_seat_exact import (  # noqa: E402
    KERNEL_TOLERANCE_MM,
    NUMERICAL_LENGTH_TOLERANCE_MM,
)
from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_model_research,
)
import validate_phase9a_chair_assembly as assembly_tests  # noqa: E402
from validate_phase9a_chair_model_scale import (  # noqa: E402
    AREA_FACTOR,
    LENGTH_FACTOR,
    MODEL_BOUNDS_MM,
    MODEL_LANDMARKS_MM,
    REQUEST,
    VOLUME_FACTOR,
    assert_diagnostic,
    request_rejections,
    validate_projection,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)


SENTINEL = "Phase 9A chair model scale FreeCAD validation passed"
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)


def document_state():
    """Capture document identities, object state and witness content."""
    return (
        App.ActiveDocument.Name if App.ActiveDocument else None,
        tuple((name, tuple(
            (obj.Name, obj.TypeId, tuple(obj.State),
             getattr(obj, "Evidence", None))
            for obj in document.Objects
        )) for name, document in sorted(App.listDocuments().items())),
    )


def validate_receipt(receipt, model, full_receipt):
    """Keep numerical budgets explicit and compare every named boundary."""
    assert receipt["contract_id"] == (
        "tracktemplate.chair-model-scale-exact-research.v1"
    )
    assert receipt["request_signature"] == model.request_signature
    assert receipt["package_signature"] == model.package.content_signature
    assert receipt["manifest_signature"] == model.manifest_signature
    assert receipt["length_basis"] == "model"
    assert receipt["source_length_basis"] == "full-size"
    assert receipt["length_unit"] == "mm"
    assert receipt["scale_denominator"] == "76.2"
    assert receipt["frame_id"] == receipt["source_frame_id"] == (
        REQUEST["source_frame_id"]
    )
    assert receipt["source_origin"] == REQUEST["origin_datum"]
    assert receipt["placement"] == "same-chair-origin-and-axes-central-key"
    assert receipt["manufacturing_compensation_applied"] is False
    assert receipt["project_status"] == "reference-only"
    assert receipt["intended_uses"] == ["private-development"]
    assert receipt["production_geometry_authorized"] is False
    assert receipt["document_mutation"] is False
    assert receipt["filesystem_mutation"] is False
    assert receipt["shape_type"] == "Compound"
    assert receipt["component_count"] == receipt["solid_count"] == 5
    assert receipt["valid"] is True and receipt["fused"] is False
    assert receipt["freecad_version"] == ".".join(App.Version()[:3])
    assert receipt["opencascade_version"] == Part.OCC_VERSION
    # Fixed numerical limits remain independent of any physical tolerance.
    assert NUMERICAL_LENGTH_TOLERANCE_MM == KERNEL_TOLERANCE_MM == 1.0e-7
    assert receipt["numerical_length_budget_mm"] == 1.0e-7
    assert receipt["maximum_bounds_residual_mm"] <= 1.0e-7
    assert max(abs(a - float(b)) for a, b in zip(
        receipt["bounds_mm"], MODEL_BOUNDS_MM,
    )) <= 1.0e-7
    assert receipt["landmarks_mm"] == {
        name: tuple(map(float, point))
        for name, point in MODEL_LANDMARKS_MM.items()
    }
    assert len(receipt["components"]) == 5
    observed_vertices = 0
    for item, component, full in zip(
        receipt["components"], model.components, full_receipt["components"],
    ):
        geometry = component.geometry
        for key in ("component_id", "procedure_id", "role"):
            assert item[key] == getattr(component, key) == full[key]
        assert item["valid"] is True and item["closed"] is True
        assert item["shell_count"] == item["solid_count"] == 1
        assert item["vertex_count"] == len(geometry.vertices)
        assert item["face_count"] == len(geometry.faces)
        assert item["face_ids"] == tuple(name for name, _ in geometry.faces)
        assert item["vertex_count"] == full["vertex_count"]
        assert item["edge_count"] == full["edge_count"]
        assert item["face_count"] == full["face_count"]
        assert set(item["vertex_residuals_mm"]) == {
            point[0] for point in geometry.vertices
        }
        assert all(0 <= value <= 1.0e-7
                   for value in item["vertex_residuals_mm"].values())
        observed_vertices += len(item["vertex_residuals_mm"])
        assert item["maximum_vertex_residual_mm"] <= 1.0e-7
        assert item["maximum_bounds_residual_mm"] <= 1.0e-7
        assert max(abs(a - float(b)) for a, b in zip(
            item["bounds_mm"], geometry.bounds_mm,
        )) <= 1.0e-7
        assert abs(item["volume_mm3"] - float(geometry.volume_mm3)) <= (
            item["numerical_volume_budget_mm3"]
        )
        budget = (item["numerical_volume_budget_mm3"]
                  + full["numerical_volume_budget_mm3"] * float(VOLUME_FACTOR))
        assert abs(item["volume_mm3"]
                   - full["volume_mm3"] * float(VOLUME_FACTOR)) <= budget
        tolerance = item["maximum_kernel_tolerance_mm"]
        assert tolerance <= 1.0e-7 or math.isclose(
            tolerance, 1.0e-7, rel_tol=1.0e-12, abs_tol=0,
        )
    assert observed_vertices == 491
    assert abs(receipt["component_volume_sum_mm3"] - float(
        model.geometry.component_volume_sum_mm3,
    )) <= receipt["numerical_volume_budget_mm3"]
    pairs = tuple(itertools.combinations(
        (component.component_id for component in model.components), 2,
    ))
    assert len(receipt["contacts"]) == len(pairs) == 10
    assert tuple(item["component_ids"] for item in receipt["contacts"]) == (
        pairs
    )
    for contact, full in zip(receipt["contacts"], full_receipt["contacts"]):
        assert contact["component_ids"] == full["component_ids"]
        assert math.isfinite(contact["distance_mm"])
        assert math.isfinite(contact["common_volume_mm3"])
        assert contact["distance_mm"] >= 0
        assert contact["common_volume_mm3"] >= 0
        length_budget = 1.0e-7 * (1 + float(LENGTH_FACTOR))
        assert abs(contact["distance_mm"]
                   - full["distance_mm"] * float(LENGTH_FACTOR)) <= (
            length_budget
        )
        volume_budget = contact["numerical_volume_budget_mm3"] + (
            full["numerical_volume_budget_mm3"] * float(VOLUME_FACTOR)
        )
        assert abs(contact["common_volume_mm3"]
                   - full["common_volume_mm3"] * float(VOLUME_FACTOR)) <= (
            volume_budget
        )


def validate_native_shapes(model):
    """Independently inspect all model vertices and surface-area scaling."""
    full_shapes = chair_assembly_exact._construct_components(
        model.full_size_research,
    )
    model_shapes = chair_model_exact._construct_components(model)
    assert len(full_shapes) == len(model_shapes) == 5
    for shape, full, component in zip(
        model_shapes, full_shapes, model.components,
    ):
        assert shape.ShapeType == "Solid" and shape.isValid()
        assert shape.isClosed() and len(shape.Solids) == 1
        assert math.isclose(
            shape.Area, full.Area * float(AREA_FACTOR),
            rel_tol=1.0e-12, abs_tol=0.0,
        )
        unmatched = [tuple(vertex.Point) for vertex in shape.Vertexes]
        for _name, *point in component.geometry.vertices:
            expected = tuple(map(float, point))
            closest = min(
                unmatched, key=lambda item: math.dist(item, expected),
            )
            assert math.dist(closest, expected) <= 1.0e-7
            unmatched.remove(closest)
        assert not unmatched


def validate_failures(record, manifest, package, text):
    """Reject inputs before Part construction and preserve documents."""
    before = document_state()

    def forbidden(_model):
        raise AssertionError("invalid input reached native construction")

    with patch.object(chair_model_exact, "_construct_components", forbidden):
        for name, request, code in request_rejections():
            retained = copy.deepcopy(request)
            try:
                chair_model_exact.validate_chair_model_exact_geometry(
                    package, text, request,
                )
            except definitions.ChairDefinitionError as error:
                assert_diagnostic(error, code)
            else:
                raise AssertionError(name + ": invalid request accepted")
            assert request == retained
        cases = list(assembly_tests._mutations(record, manifest))
        bad, related = copy.deepcopy((record, manifest))
        bad["definition"]["frame"]["y_axis"] = "field-to-gauge"
        cases.append(("wrong-frame", bad, related))
        for name, bad, related in cases:
            resign_package(bad, related)
            retained = copy.deepcopy((bad, related))
            try:
                bad_text = canonical_json(related)
                bad_package = definitions.chair_definition_package_from_json(
                    canonical_json(bad), bad_text,
                )
                chair_model_exact.validate_chair_model_exact_geometry(
                    bad_package, bad_text, REQUEST,
                )
            except definitions.ChairDefinitionError as error:
                expected = ("unsupported-coordinate-frame"
                            if name == "wrong-frame" else
                            assembly_tests.EXPECTED_REJECTION_CODES[name])
                assert_diagnostic(error, expected)
            else:
                raise AssertionError(name + ": invalid package accepted")
            assert (bad, related) == retained
    assert document_state() == before

    def fail_kernel(_model):
        raise ValueError("synthetic model construction failure")

    with patch.object(chair_model_exact, "_construct_components", fail_kernel):
        try:
            chair_model_exact.validate_chair_model_exact_geometry(
                package, text, REQUEST,
            )
        except chair_model_exact.ChairModelExactGeometryError as error:
            assert_diagnostic(
                error, "research-model-kernel-construction-failed",
            )
            assert isinstance(error.__cause__, ValueError)
        else:
            raise AssertionError("injected model kernel failure accepted")
    assert document_state() == before


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    assert qualification["compatibility_evaluation"][
        "matched_profile_id"
    ] == PROFILE_ID
    initial = document_state()
    witness = App.newDocument("ChairModelWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Model success and failure preserve this document"
        witness.recompute()
        before = document_state()
        record, manifest = assembly_tests.synthetic_assembly_package_records()
        retained = copy.deepcopy((record, manifest, REQUEST))
        package, text, full_size = assembly_tests.load_research(
            record, manifest,
        )
        encoded = definitions.chair_definition_package_to_json(package)
        full_receipt = (
            chair_assembly_exact.validate_chair_assembly_exact_geometry(
                package, text,
            )
        )
        model = chair_model_research.prepare_chair_model_research(
            package, text, REQUEST,
        )
        validate_projection(model, full_size)
        reopened = definitions.chair_definition_package_from_json(
            encoded, text,
        )
        first = chair_model_exact.validate_chair_model_exact_geometry(
            reopened, text, REQUEST,
        )
        repeated = chair_model_exact.validate_chair_model_exact_geometry(
            package, text, dict(reversed(tuple(REQUEST.items()))),
        )
        assert repeated == first
        validate_receipt(first, model, full_receipt)
        validate_native_shapes(model)
        validate_failures(record, manifest, package, text)
        assert chair_assembly_exact.validate_chair_assembly_exact_geometry(
            package, text,
        ) == full_receipt
        assert definitions.chair_definition_package_to_json(package) == encoded
        assert (record, manifest, REQUEST) == retained
        assert document_state() == before
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("CHAIR_MODEL_EXACT_RECEIPT=" + json.dumps(first, sort_keys=True))
    print(SENTINEL)


# FreeCADCmd uses the script filename stem as __name__ on this host.
if __name__ in ("__main__", Path(__file__).stem):
    main()
