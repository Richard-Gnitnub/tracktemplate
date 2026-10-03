#!/usr/bin/env python3
"""Prove the research seat in qualified FreeCAD with synthetic inputs."""

import copy
import json
from pathlib import Path
import sys
import uuid

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import chair_seat_exact  # noqa: E402
from tracktemplate.application.chair_definition import (  # noqa: E402
    ChairDefinitionError,
    chair_definition_package_from_json,
    chair_definition_package_status,
    chair_definition_package_to_json,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    synthetic_package_records,
)


def document_state():
    """Include active document and witness properties, not only counts."""
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
    """Reject re-signed bad input before even entering the Part builder."""
    resign_package(record, manifest)
    before = document_state()
    original = chair_seat_exact._make_shape

    def forbidden_shape(_geometry):
        raise AssertionError("invalid research input reached Part construction")

    chair_seat_exact._make_shape = forbidden_shape
    try:
        text = canonical_json(manifest)
        try:
            package = chair_definition_package_from_json(
                canonical_json(record), text
            )
            chair_seat_exact.validate_chair_seat_exact_geometry(package, text)
        except ChairDefinitionError:
            pass
        else:
            raise AssertionError("invalid research input was accepted")
    finally:
        chair_seat_exact._make_shape = original
    assert document_state() == before


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json"
    )
    initial = document_state()
    witness = App.newDocument("SeatWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Must survive construction and failure unchanged"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_package_records()
        manifest_text = canonical_json(manifest)
        package = chair_definition_package_from_json(
            canonical_json(record), manifest_text
        )
        encoded = chair_definition_package_to_json(package)
        reopened = chair_definition_package_from_json(encoded, manifest_text)
        assert reopened == package
        first = chair_seat_exact.validate_chair_seat_exact_geometry(
            reopened, manifest_text
        )
        second = chair_seat_exact.validate_chair_seat_exact_geometry(
            package, manifest_text
        )
        assert first == second
        assert first["valid"] and first["closed"]
        assert first["bounds_mm"] == (-9.0, -3.0, 1.0, 9.0, 8.0, 4.0)
        assert abs(first["volume_mm3"] - 1325 / 3) <= 1e-10
        assert first["production_geometry_authorized"] is False
        assert first["project_status"] == "reference-only"
        assert document_state() == before
        assert chair_definition_package_to_json(package) == encoded
        assert chair_definition_package_status(
            package, manifest_text
        )["production_geometry_authorized"] is False

        bad = copy.deepcopy(record)
        bad["schema_version"] += 1
        expect_research_rejection(bad, manifest)
        bad = copy.deepcopy(record)
        bad["definition"]["frame"]["handedness"] = "left"
        expect_research_rejection(bad, manifest)
        bad = copy.deepcopy(record)
        bad["lineage"][0]["evidence_state"] = "unresolved"
        expect_research_rejection(bad, manifest)

        original = chair_seat_exact._make_shape

        def fail_kernel(_geometry):
            raise Part.OCCError("injected research construction failure")

        chair_seat_exact._make_shape = fail_kernel
        try:
            try:
                chair_seat_exact.validate_chair_seat_exact_geometry(
                    package, manifest_text
                )
            except chair_seat_exact.ChairSeatExactGeometryError as error:
                assert error.code == "seat-kernel-construction-failed"
                assert error.diagnostic()["document_mutation"] is False
            else:
                raise AssertionError("injected kernel failure was hidden")
        finally:
            chair_seat_exact._make_shape = original
        assert document_state() == before
        print("TRACKTEMPLATE_CHAIR_SEAT_RESEARCH=" + json.dumps({
            "profile": qualification["compatibility_evaluation"][
                "matched_profile_id"
            ],
            "synthetic_geometry": first,
            "round_trip": True,
            "invalid_packages_rejected_before_geometry": True,
            "injected_failure_preserved_document": True,
        }, sort_keys=True))
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("Phase 9A chair-seat FreeCAD research validation passed")


# FreeCADCmd executes scripts with their filename as __name__.
main()
