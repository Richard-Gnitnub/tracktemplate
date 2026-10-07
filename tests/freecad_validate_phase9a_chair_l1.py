#!/usr/bin/env python3
"""Validate five L1 research components and seven transient solids.

The synthetic outer jaw retains three source-pattern pieces. Numerical
geometry checks neither join those pieces nor accept physical rail fit.
"""

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
from tracktemplate.adapters.freecad import chair_assembly_exact  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from validate_phase9a_chair_l1 import (  # noqa: E402
    EXPECTED_SEAT,
    assert_geometry,
    load_package,
    synthetic_l1_package_records,
    validate_rejections,
)


SENTINEL = "Phase 9A chair L1 FreeCAD validation passed"
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
NUMERICAL_BUDGET_MM = 1.0e-7
EXPECTED_OUTER_POINTS = (
    (-5, 9, 24), (5, 9, 24), (-9.25, 9, 3), (9.25, 9, 3),
    (-4.5, 11, 24), (4.5, 11, 24), (-8.25, 16, 3), (8.25, 16, 3),
    (-12, 9, 3), (12, 9, 3), (-9, 9, 8), (9, 9, 8),
)


def document_state():
    """Capture all documents and the task-owned witness object."""
    return (
        App.ActiveDocument.Name if App.ActiveDocument else None,
        tuple((name, tuple(
            (obj.Name, obj.TypeId, tuple(obj.State),
             getattr(obj, "Evidence", None)) for obj in document.Objects
        )) for name, document in sorted(App.listDocuments().items())),
    )


def assert_receipt(receipt):
    """Preserve family, identity, private status and exact part counts."""
    assert receipt["contract_id"] == (
        "tracktemplate.chair-l1-assembly-exact-research.v1"
    )
    assert receipt["component_count"] == 5
    assert receipt["solid_count"] == 7
    assert receipt["valid"] is True and receipt["fused"] is False
    assert receipt["project_status"] == "reference-only"
    assert receipt["intended_uses"] == ["private-development"]
    assert receipt["production_geometry_authorized"] is False
    assert receipt["document_mutation"] is False
    assert receipt["filesystem_mutation"] is False
    assert [c["solid_count"] for c in receipt["components"]] == [
        1, 1, 1, 3, 1,
    ]
    assert receipt["numerical_length_budget_mm"] == NUMERICAL_BUDGET_MM
    assert len(receipt["contacts"]) == 10


def native_probes(result):
    """Check independent points and edge-only contact of outer pieces."""
    shapes = chair_assembly_exact._construct_components(result, l1=True)
    maximum = 0.0
    for shape, expected in ((shapes[1], EXPECTED_SEAT.values()),
                            (shapes[3], EXPECTED_OUTER_POINTS)):
        points = [tuple(vertex.Point) for vertex in shape.Vertexes]
        for point in expected:
            residual = min(math.dist(tuple(map(float, point)), candidate)
                           for candidate in points)
            assert residual <= NUMERICAL_BUDGET_MM
            maximum = max(maximum, residual)
    outer = shapes[3]
    assert outer.ShapeType == "Compound" and outer.isValid()
    pieces = outer.childShapes()
    assert len(pieces) == 3
    for piece in pieces:
        assert piece.ShapeType == "Solid"
        assert piece.isValid() and piece.isClosed()
        assert len(piece.Solids) == len(piece.Shells) == 1
    contacts = []
    for bevel in pieces[1:]:
        common = pieces[0].common(bevel)
        assert common.isValid()
        assert common.Volume == 0
        assert len(common.Solids) == 0
        assert pieces[0].distToShape(bevel)[0] <= NUMERICAL_BUDGET_MM
        contacts.append({
            "distance_mm": pieces[0].distToShape(bevel)[0],
            "common_volume_mm3": common.Volume,
            "common_edge_count": len(common.Edges),
        })
    return {
        "independent_point_count": len(EXPECTED_SEAT) + 12,
        "maximum_point_residual_mm": maximum,
        "outer_piece_contacts": contacts,
    }


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    assert qualification["compatibility_evaluation"][
        "matched_profile_id"
    ] == PROFILE_ID
    initial = document_state()
    witness = App.newDocument("ChairL1Witness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Success and failure preserve this document"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_l1_package_records()
        retained = copy.deepcopy((record, manifest))
        package, text = load_package(record, manifest)
        result = chair_research.prepare_chair_l1_assembly_research(
            package, text,
        )
        assert_geometry(result)
        operation = chair_assembly_exact.validate_chair_l1_assembly_exact_geometry
        receipt = operation(package, text)
        assert_receipt(receipt)
        probes = native_probes(result)
        encoded = definitions.chair_definition_package_to_json(package)
        reopened = definitions.chair_definition_package_from_json(encoded, text)
        assert operation(reopened, text) == receipt
        assert definitions.chair_definition_package_to_json(reopened) == encoded

        def forbidden(*_args, **_kwargs):
            raise AssertionError("invalid input reached native construction")

        with patch.object(Part, "makePolygon", forbidden):
            rejections = validate_rejections(record, manifest, operation)
        assert document_state() == before
        assert (record, manifest) == retained
        print(json.dumps({
            "qualification": qualification, "receipt": receipt,
            "probes": probes, "rejections": rejections,
            "document_state_unchanged": True,
            "physical_fit_proved": False,
            "production_geometry_authorized": False,
        }, sort_keys=True))
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print(SENTINEL)


if __name__ in ("__main__", Path(__file__).stem):
    main()
