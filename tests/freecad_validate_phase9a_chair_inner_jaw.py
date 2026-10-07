#!/usr/bin/env python3
"""Prove transient reference-only inner-jaw solids in FreeCAD."""

import copy
import decimal
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
    chair_base_exact,
    chair_inner_jaw_exact,
    chair_outer_jaw_exact,
    chair_key_exact,
    chair_seat_exact,
)
from tracktemplate.application.chair_definition import (  # noqa: E402
    ChairDefinitionError,
    chair_definition_package_from_json,
    chair_definition_package_status,
    chair_definition_package_to_json,
)
from validate_phase9a_chair_inner_jaw import (  # noqa: E402
    SYNTHETIC_BOUNDS,
    synthetic_inner_jaw_package_records,
    independent_geometry,
)
from validate_phase9a_chair_outer_jaw import (  # noqa: E402
    synthetic_outer_jaw_package_records,
)
from validate_phase9a_chair_base import (  # noqa: E402
    synthetic_base_package_records,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    synthetic_package_records,
)
from validate_phase9a_chair_key import (  # noqa: E402
    synthetic_key_package_records,
)


def document_state():
    """Record active document, object identities and witness data."""
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
    original = chair_inner_jaw_exact._make_shape

    def forbidden_shape(_geometry):
        raise AssertionError(
            "invalid inner-jaw input reached native construction",
        )

    chair_inner_jaw_exact._make_shape = forbidden_shape
    try:
        text = canonical_json(manifest)
        try:
            package = chair_definition_package_from_json(
                canonical_json(record), text,
            )
            chair_inner_jaw_exact.validate_chair_inner_jaw_exact_geometry(
                package, text,
            )
        except ChairDefinitionError as error:
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("invalid inner-jaw package was accepted")
    finally:
        chair_inner_jaw_exact._make_shape = original
    assert document_state() == before


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    initial = document_state()
    witness = App.newDocument("InnerJawWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Outer-jaw success and failure must preserve this"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_inner_jaw_package_records()
        text = canonical_json(manifest)
        package = chair_definition_package_from_json(
            canonical_json(record), text,
        )
        encoded = chair_definition_package_to_json(package)
        reopened = chair_definition_package_from_json(encoded, text)
        assert reopened == package
        first = chair_inner_jaw_exact.validate_chair_inner_jaw_exact_geometry(
            reopened, text,
        )
        second = chair_inner_jaw_exact.validate_chair_inner_jaw_exact_geometry(
            package, text,
        )
        assert first == second
        assert first["valid"] and first["closed"]
        assert (first["vertex_count"], first["edge_count"], first["face_count"]
                ) == (213, 467, 256)
        assert first["solid_count"] == first["shell_count"] == 1
        assert first["bounds_mm"] == tuple(map(float, SYNTHETIC_BOUNDS))
        with decimal.localcontext() as context:
            context.prec = 100
            expected_volume = float(independent_geometry()[2])
        assert abs(first["volume_mm3"] - expected_volume) <= 1e-10
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
        assert len(first["vertex_residuals_mm"]) == 213
        assert first["production_geometry_authorized"] is False
        assert first["project_status"] == "reference-only"
        assert first["intended_uses"] == ["private-development"]
        assert document_state() == before
        assert chair_definition_package_to_json(package) == encoded
        assert chair_definition_package_status(
            package, text,
        )["production_geometry_authorized"] is False

        for kind in ("schema", "frame", "lineage",
                     "height-unit", "slope-unit"):
            bad = copy.deepcopy(record)
            if kind == "schema":
                bad["schema_version"] += 1
            elif kind == "frame":
                bad["definition"]["frame"]["handedness"] = "left"
            elif kind == "lineage":
                bad["lineage"][0]["evidence_state"] = "unresolved"
            elif kind == "slope-unit":
                slope = next(q for q in bad["definition"]["quantities"]
                             if q["purpose"] == "top_to_mid_side_slope")
                slope.update({"source_unit": "mm", "canonical_unit": "mm",
                              "quantity_kind": "length"})
            else:
                height = next(q for q in bad["definition"]["quantities"]
                               if q["purpose"] == "stand_height_mm")
                height.update({"source_unit": "1", "canonical_unit": "1",
                                "quantity_kind": "dimensionless"})
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

        key_record, key_manifest = synthetic_key_package_records()
        expect_research_rejection(key_record, key_manifest)
        key_text = canonical_json(key_manifest)
        key_package = chair_definition_package_from_json(
            canonical_json(key_record), key_text,
        )
        key_result = chair_key_exact.validate_chair_key_exact_geometry(
            key_package, key_text,
        )
        assert key_result["bounds_mm"] == (-10.0, 1.0, 6.5, 10.0, 7.25, 12.5)
        assert abs(key_result["volume_mm3"] - 3809 / 6) <= 1e-10
        assert (key_result["vertex_count"], key_result["edge_count"],
                key_result["face_count"]) == (20, 36, 18)
        assert document_state() == before

        base_record, base_manifest = synthetic_base_package_records()
        expect_research_rejection(base_record, base_manifest)
        base_text = canonical_json(base_manifest)
        base_package = chair_definition_package_from_json(
            canonical_json(base_record), base_text,
        )
        base_result = chair_base_exact.validate_chair_base_exact_geometry(
            base_package, base_text,
        )
        assert base_result["bounds_mm"] == (-8.0, -13.0, 0.0, 8.0, 9.0, 3.0)
        assert abs(base_result["volume_mm3"] - 2526937 / 3000) <= 1e-10
        assert (base_result["vertex_count"], base_result["edge_count"],
                base_result["face_count"]) == (68, 128, 62)
        assert document_state() == before

        outer_record, outer_manifest = synthetic_outer_jaw_package_records()
        expect_research_rejection(outer_record, outer_manifest)
        outer_text = canonical_json(outer_manifest)
        outer_package = chair_definition_package_from_json(
            canonical_json(outer_record), outer_text,
        )
        outer_operation = (
            chair_outer_jaw_exact.validate_chair_outer_jaw_exact_geometry
        )
        outer_result = outer_operation(
            outer_package, outer_text,
        )
        assert outer_result["bounds_mm"] == (
            -12.0, 12.0, 3.0, 12.0, 20.5, 20.0,
        )
        outer_volume = 11521 / 8 + 941 / 32 * (math.sqrt(6) - math.sqrt(2))
        assert abs(outer_result["volume_mm3"] - outer_volume) <= 1e-10
        assert (outer_result["vertex_count"], outer_result["edge_count"],
                outer_result["face_count"]) == (178, 316, 140)
        assert document_state() == before

        # Uniform scaling is analytically valid, but below the accepted
        # kernel budget native construction must fail recoverably. This
        # checks refusal, without a physical minimum chair dimension.
        tiny = copy.deepcopy(record)
        for quantity in tiny["definition"]["quantities"]:
            if quantity["quantity_kind"] != "length":
                continue
            value = format(decimal.Decimal(quantity["source_value"])
                           * decimal.Decimal("1e-12"), "f")
            quantity["source_value"] = value
            quantity["canonical_value"] = value
        resign_package(tiny, manifest)
        tiny_package = chair_definition_package_from_json(
            canonical_json(tiny), text,
        )
        try:
            chair_inner_jaw_exact.validate_chair_inner_jaw_exact_geometry(
                tiny_package, text,
            )
        except chair_inner_jaw_exact.ChairInnerJawExactGeometryError as error:
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("Unresolvable tiny native geometry accepted")
        assert document_state() == before

        original = chair_inner_jaw_exact._make_shape

        def fail_kernel(_geometry):
            raise Part.OCCError("injected inner-jaw construction failure")

        chair_inner_jaw_exact._make_shape = fail_kernel
        try:
            try:
                chair_inner_jaw_exact.validate_chair_inner_jaw_exact_geometry(
                    package, text,
                )
            except (
                chair_inner_jaw_exact.ChairInnerJawExactGeometryError
            ) as error:
                assert error.code == "inner-jaw-kernel-construction-failed"
                diagnostic = error.diagnostic()
                assert diagnostic["recoverable"] is True
                assert diagnostic["document_mutation"] is False
                assert diagnostic["filesystem_mutation"] is False
            else:
                raise AssertionError("injected native failure was hidden")
        finally:
            chair_inner_jaw_exact._make_shape = original
        assert document_state() == before
        print("TRACKTEMPLATE_CHAIR_INNER_JAW_RESEARCH=" + json.dumps({
            "profile": qualification["compatibility_evaluation"][
                "matched_profile_id"
            ],
            "synthetic_geometry": first,
            "round_trip": True,
            "seat_regression": True,
            "key_regression": True,
            "base_regression": True,
            "outer_jaw_regression": True,
            "tiny_native_geometry_refused": True,
            "invalid_packages_rejected_before_geometry": True,
            "injected_failure_preserved_document": True,
        }, sort_keys=True))
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("Phase 9A chair-inner-jaw FreeCAD research validation passed")


# FreeCADCmd executes scripts with their filename as __name__.
main()
