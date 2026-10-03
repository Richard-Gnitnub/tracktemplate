#!/usr/bin/env python3
"""Prove transient reference-only key geometry in qualified FreeCAD."""

import copy
import json
import math
from pathlib import Path
import sys
import uuid

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_key_exact,
    chair_seat_exact,
)
from tracktemplate.application.chair_definition import (  # noqa: E402
    ChairDefinitionError,
    chair_definition_package_from_json,
    chair_definition_package_status,
    chair_definition_package_to_json,
)
from validate_phase9a_chair_key import (  # noqa: E402
    SYNTHETIC_BOUNDS,
    SYNTHETIC_VOLUME,
    synthetic_key_package_records,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    synthetic_package_records,
)


def document_state():
    """Record active document, object identities and witness properties."""
    return (
        App.ActiveDocument.Name if App.ActiveDocument else None,
        tuple(
            (name, tuple(
                (obj.Name, obj.TypeId, tuple(obj.State),
                 getattr(obj, "Evidence", None))
                for obj in document.Objects
            ))
            for name, document in sorted(App.listDocuments().items())
        ),
    )


def expect_research_rejection(record, manifest):
    """Reject signed invalid data before reaching the native builder."""
    resign_package(record, manifest)
    before = document_state()
    original = chair_key_exact._make_shape

    def forbidden_shape(_geometry):
        raise AssertionError("invalid key package reached native construction")

    chair_key_exact._make_shape = forbidden_shape
    try:
        text = canonical_json(manifest)
        try:
            package = chair_definition_package_from_json(
                canonical_json(record), text,
            )
            chair_key_exact.validate_chair_key_exact_geometry(package, text)
        except ChairDefinitionError as error:
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("invalid key package was accepted")
    finally:
        chair_key_exact._make_shape = original
    assert document_state() == before


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    initial = document_state()
    witness = App.newDocument("KeyWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Must survive key construction and failure unchanged"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_key_package_records()
        text = canonical_json(manifest)
        package = chair_definition_package_from_json(
            canonical_json(record), text,
        )
        encoded = chair_definition_package_to_json(package)
        reopened = chair_definition_package_from_json(encoded, text)
        assert reopened == package
        first = chair_key_exact.validate_chair_key_exact_geometry(
            reopened, text,
        )
        second = chair_key_exact.validate_chair_key_exact_geometry(
            package, text,
        )
        assert first == second
        assert first["valid"] and first["closed"]
        assert (first["vertex_count"], first["edge_count"], first["face_count"]
                ) == (20, 36, 18)
        assert first["solid_count"] == first["shell_count"] == 1
        assert first["bounds_mm"] == tuple(map(float, SYNTHETIC_BOUNDS))
        assert abs(first["volume_mm3"] - float(SYNTHETIC_VOLUME)) <= 1e-10
        assert first["numerical_length_budget_mm"] == 1e-7
        assert first["maximum_vertex_residual_mm"] <= 1e-7
        assert first["maximum_bounds_residual_mm"] <= 1e-7
        assert first["volume_residual_mm3"] <= first[
            "numerical_volume_budget_mm3"
        ]
        assert (first["maximum_kernel_tolerance_mm"] <= 1e-7 or math.isclose(
            first["maximum_kernel_tolerance_mm"], 1e-7, rel_tol=1e-12,
            abs_tol=0.0,
        ))
        assert len(first["vertex_residuals_mm"]) == 20
        assert first["production_geometry_authorized"] is False
        assert first["project_status"] == "reference-only"
        assert first["intended_uses"] == ["private-development"]
        assert document_state() == before
        assert chair_definition_package_to_json(package) == encoded
        assert chair_definition_package_status(
            package, text,
        )["production_geometry_authorized"] is False

        for kind in ("schema", "frame", "lineage", "ratio"):
            bad = copy.deepcopy(record)
            if kind == "schema":
                bad["schema_version"] += 1
            elif kind == "frame":
                bad["definition"]["frame"]["handedness"] = "left"
            elif kind == "lineage":
                bad["lineage"][0]["evidence_state"] = "unresolved"
            else:
                ratio = next(q for q in bad["definition"]["quantities"]
                             if q["purpose"] == "rail_fish_ratio")
                ratio.update({"source_unit": "mm", "canonical_unit": "mm",
                              "quantity_kind": "length"})
            expect_research_rejection(bad, manifest)

        seat_record, seat_manifest = synthetic_package_records()
        expect_research_rejection(seat_record, seat_manifest)
        seat_text = canonical_json(seat_manifest)
        seat_package = chair_definition_package_from_json(
            canonical_json(seat_record), seat_text,
        )
        seat_result = chair_seat_exact.validate_chair_seat_exact_geometry(
            seat_package, seat_text,
        )
        assert seat_result["bounds_mm"] == (-9.0, -3.0, 1.0, 9.0, 8.0, 4.0)
        assert abs(seat_result["volume_mm3"] - 1325 / 3) <= 1e-10
        assert (seat_result["vertex_count"], seat_result["edge_count"],
                seat_result["face_count"]) == (12, 21, 11)
        assert document_state() == before

        original = chair_key_exact._make_shape

        def fail_kernel(_geometry):
            raise Part.OCCError("injected key research construction failure")

        chair_key_exact._make_shape = fail_kernel
        try:
            try:
                chair_key_exact.validate_chair_key_exact_geometry(
                    package, text,
                )
            except chair_key_exact.ChairKeyExactGeometryError as error:
                assert error.code == "key-kernel-construction-failed"
                diagnostic = error.diagnostic()
                assert diagnostic["recoverable"] is True
                assert diagnostic["document_mutation"] is False
                assert diagnostic["filesystem_mutation"] is False
            else:
                raise AssertionError("injected native failure was hidden")
        finally:
            chair_key_exact._make_shape = original
        assert document_state() == before
        print("TRACKTEMPLATE_CHAIR_KEY_RESEARCH=" + json.dumps({
            "profile": qualification["compatibility_evaluation"][
                "matched_profile_id"
            ],
            "synthetic_geometry": first,
            "round_trip": True,
            "seat_regression": True,
            "invalid_packages_rejected_before_geometry": True,
            "injected_failure_preserved_document": True,
        }, sort_keys=True))
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("Phase 9A chair-key FreeCAD research validation passed")


# FreeCADCmd executes scripts with their filename as __name__.
main()
