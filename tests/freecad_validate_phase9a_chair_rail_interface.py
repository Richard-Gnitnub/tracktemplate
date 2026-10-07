#!/usr/bin/env python3
"""Check independent research rail planes on qualified transient solids."""

import copy
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
from tracktemplate.adapters.freecad import chair_model_exact  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_rail_research,
)
from validate_phase9a_chair_model_scale import (  # noqa: E402
    LENGTH_FACTOR,
    REQUEST,
    assert_diagnostic,
)
from validate_phase9a_chair_rail_interface import (  # noqa: E402
    EXPECTED_PLANES,
    EXPECTED_POINTS,
    MISMATCH,
    assert_proof,
    load_package,
    mismatch_cases,
    synthetic_rail_package_records,
    validate_rejections,
)


SENTINEL = "Phase 9A chair rail interface FreeCAD validation passed"
# Conversion/kernel budget only; never a physical rail-fit tolerance.
NUMERICAL_BUDGET_MM = 1.0e-7
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)


def document_state():
    """Capture documents, object state and the task-owned witness."""
    return (
        App.ActiveDocument.Name if App.ActiveDocument else None,
        tuple((name, tuple(
            (obj.Name, obj.TypeId, tuple(obj.State),
             getattr(obj, "Evidence", None))
            for obj in document.Objects
        )) for name, document in sorted(App.listDocuments().items())),
    )


def validate_native_planes(result):
    """Compare actual Part vertices and faces with hand-derived points."""
    model = result.model_research
    shapes = chair_model_exact._construct_components(model)
    by_role = dict(zip((c.role for c in model.components), shapes))
    maximum_coordinate_residual = 0.0
    maximum_plane_residual = 0.0
    counts = {"vertices": 0, "faces": 0, "endpoint_relations": 0}
    for relation in result.proof.relations:
        shape = by_role[relation.component_role]
        assert shape.isValid() and shape.isClosed()
        assert shape.ShapeType == "Solid" and len(shape.Solids) == 1
        expected = [tuple(float(v * LENGTH_FACTOR) for v in
                          EXPECTED_POINTS[relation.component_role][name])
                    for name in relation.vertex_ids]
        normal, full_offset = EXPECTED_PLANES[relation.plane_id]
        offset = float(full_offset * LENGTH_FACTOR)
        for target in expected:
            observed = min((tuple(v.Point) for v in shape.Vertexes),
                           key=lambda point: math.dist(point, target))
            error = math.dist(observed, target)
            assert error <= NUMERICAL_BUDGET_MM
            residual = abs(sum(float(a) * v for a, v in zip(
                normal, observed,
            )) - offset)
            # Plane equations are not unit-normal distances. Preserve the
            # length budget by accounting for coefficient magnitudes.
            assert residual <= NUMERICAL_BUDGET_MM * sum(map(abs, normal))
            maximum_coordinate_residual = max(
                maximum_coordinate_residual, error,
            )
            maximum_plane_residual = max(maximum_plane_residual, residual)
            counts["vertices"] += 1
        if relation.face_id is None:
            counts["endpoint_relations"] += 1
            continue
        candidates = [face for face in shape.Faces
                      if len(face.Vertexes) == len(expected) and all(
                          min(math.dist(tuple(v.Point), p) for p in expected)
                          <= NUMERICAL_BUDGET_MM for v in face.Vertexes
                      )]
        assert len(candidates) == 1, relation.relation_id
        face = candidates[0]
        assert face.isValid() and face.Area > 0
        centre = tuple(sum(p[axis] for p in expected) / len(expected)
                       for axis in range(3))
        assert face.distToShape(Part.Vertex(App.Vector(*centre)))[0] <= (
            NUMERICAL_BUDGET_MM
        )
        counts["faces"] += 1
    assert counts == {"vertices": 36, "faces": 8, "endpoint_relations": 1}
    return dict(counts, maximum_coordinate_residual_mm=(
        maximum_coordinate_residual
    ), maximum_plane_equation_residual_mm=maximum_plane_residual)


def prove_then_validate(package, manifest_text, request):
    """Exercise the new analytical proof before the unchanged native path."""
    result = chair_rail_research.prepare_chair_rail_research(
        package, manifest_text, request,
    )
    return result, chair_model_exact.validate_chair_model_exact_geometry(
        package, manifest_text, request,
    )


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    assert qualification["compatibility_evaluation"][
        "matched_profile_id"
    ] == PROFILE_ID
    initial = document_state()
    witness = App.newDocument("ChairRailWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Rail proof success and failure preserve this document"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_rail_package_records()
        retained = copy.deepcopy((record, manifest))
        package, text = load_package(record, manifest)
        encoded = definitions.chair_definition_package_to_json(package)
        old = chair_model_exact.validate_chair_model_exact_geometry(
            package, text, REQUEST,
        )
        result, receipt = prove_then_validate(package, text, REQUEST)
        assert_proof(result)
        probes = validate_native_planes(result)
        assert receipt == old
        reopened = definitions.chair_definition_package_from_json(encoded, text)
        repeated, reopened_receipt = prove_then_validate(reopened, text, REQUEST)
        assert repeated == result and reopened_receipt == receipt
        assert definitions.chair_definition_package_to_json(reopened) == encoded
        assert receipt["component_count"] == receipt["solid_count"] == 5
        assert receipt["valid"] is True and receipt["fused"] is False
        assert receipt["production_geometry_authorized"] is False
        assert receipt["document_mutation"] is False
        assert receipt["filesystem_mutation"] is False
        assert document_state() == before

        def forbidden(_model):
            raise AssertionError("invalid interface reached native construction")

        with patch.object(chair_model_exact, "_construct_components", forbidden):
            for name, bad, related in mismatch_cases(record, manifest):
                other, other_text = load_package(bad, related)
                try:
                    prove_then_validate(other, other_text, REQUEST)
                except chair_rail_research.ChairRailResearchError as error:
                    assert_diagnostic(error, MISMATCH)
                else:
                    raise AssertionError(name + ": native mismatch accepted")
            validate_rejections(record, manifest, package, text)
        assert document_state() == before
        assert (record, manifest) == retained
        assert definitions.chair_definition_package_to_json(package) == encoded
        print(json.dumps({
            "qualification": qualification, "probes": probes,
            "physical_rail_fit_proved": False,
            "production_geometry_authorized": False,
            "existing_native_receipt_unchanged": True,
            "document_state_unchanged": True,
        }, sort_keys=True))
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print(SENTINEL)


# FreeCADCmd uses the script filename stem as __name__ on this host.
if __name__ in ("__main__", Path(__file__).stem):
    main()
