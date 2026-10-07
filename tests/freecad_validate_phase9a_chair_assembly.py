#!/usr/bin/env python3
"""Prove a transient five-solid research assembly on a qualified host."""

import copy
import itertools
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
from tracktemplate.adapters.freecad import chair_assembly_exact  # noqa: E402
from tracktemplate.adapters.freecad.chair_seat_exact import (  # noqa: E402
    KERNEL_TOLERANCE_MM,
)
from tracktemplate.application import chair_research  # noqa: E402
from tracktemplate.application.chair_definition import (  # noqa: E402
    ChairDefinitionError,
    chair_definition_package_from_json,
    chair_definition_package_status,
    chair_definition_package_to_json,
)
from validate_phase9a_chair_assembly import (  # noqa: E402
    CHAIR_ASSEMBLY_ROLES,
    COMMON_LANDMARKS_MM,
    EXPECTED_BOUNDS_MM,
    EXPECTED_REJECTION_CODES,
    _mutations,
    synthetic_assembly_package_records,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)


SENTINEL = "Phase 9A chair assembly FreeCAD validation passed"
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)


def document_state():
    """Capture the operator-visible document and witness state."""
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


def expect_pre_kernel_rejection(record, manifest, expected_code):
    """An invalid signed package cannot reach native construction."""
    resign_package(record, manifest)
    retained = copy.deepcopy((record, manifest))
    before = document_state()
    original = chair_assembly_exact._construct_components

    def forbidden(_research):
        raise AssertionError("invalid package reached native construction")

    chair_assembly_exact._construct_components = forbidden
    try:
        text = canonical_json(manifest)
        try:
            package = chair_definition_package_from_json(
                canonical_json(record), text,
            )
            chair_assembly_exact.validate_chair_assembly_exact_geometry(
                package, text,
            )
        except ChairDefinitionError as error:
            assert error.code == expected_code
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("invalid assembly package was accepted")
    finally:
        chair_assembly_exact._construct_components = original
    assert document_state() == before
    assert (record, manifest) == retained


def validate_contact_failure_guards(research):
    """Reject false zero-overlap evidence using real constructed shapes."""
    shapes = chair_assembly_exact._construct_components(research)
    assert len(chair_assembly_exact._measure_contacts(
        shapes, research.components,
    )) == 10

    class FaultedFirstShape:
        def __init__(self, native_shape, fault):
            self.native_shape = native_shape
            self.fault = fault

        def __getattr__(self, name):
            return getattr(self.native_shape, name)

        def distToShape(self, other):
            if self.fault == "nonfinite-distance":
                return (float("nan"), [], [])
            return self.native_shape.distToShape(other)

        def common(self, other):
            if self.fault == "null-boolean":
                return Part.Shape()
            native_common = self.native_shape.common(other)

            class NonfiniteCommon:
                Volume = float("nan")

                def __getattr__(self, name):
                    return getattr(native_common, name)

            return NonfiniteCommon()

    for fault, code in (
        ("nonfinite-distance", "assembly-contact-distance-invalid"),
        ("null-boolean", "assembly-common-invalid"),
        ("nonfinite-common-volume", "assembly-common-invalid"),
    ):
        faulted = (FaultedFirstShape(shapes[0], fault),) + tuple(shapes[1:])
        try:
            chair_assembly_exact._measure_contacts(
                faulted, research.components,
            )
        except chair_assembly_exact.ChairAssemblyExactGeometryError as error:
            assert error.code == code
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
        else:
            raise AssertionError("invalid contact measurement was accepted")


def validate_receipt(receipt, research, package, manifest_text):
    """Check topology, source identity, envelope and rights boundaries."""
    assert receipt["contract_id"] == (
        "tracktemplate.chair-assembly-exact-research.v1"
    )
    assert receipt["package_signature"] == package.content_signature
    assert receipt["manifest_signature"] == research.manifest_signature
    assert receipt["project_status"] == "reference-only"
    assert receipt["intended_uses"] == ["private-development"]
    assert receipt["production_geometry_authorized"] is False
    assert receipt["document_mutation"] is False
    assert receipt["filesystem_mutation"] is False
    assert receipt["frame_id"] == (
        package.to_record()["definition"]["frame"]["frame_id"]
    )
    assert receipt["length_unit"] == "mm"
    assert receipt["length_basis"] == "full-size"
    assert receipt["placement"] == "central-key-identity"
    assert receipt["shape_type"] == "Compound"
    assert receipt["component_count"] == receipt["solid_count"] == 5
    assert receipt["valid"] is True and receipt["fused"] is False
    assert receipt["bounds_mm"] == tuple(map(float, EXPECTED_BOUNDS_MM))
    assert receipt["landmarks_mm"] == {
        name: tuple(map(float, point))
        for name, point in COMMON_LANDMARKS_MM.items()
    }
    assert receipt["freecad_version"] == ".".join(App.Version()[:3])
    assert receipt["opencascade_version"] == Part.OCC_VERSION
    assert receipt["maximum_bounds_residual_mm"] <= receipt[
        "numerical_length_budget_mm"
    ]
    components = receipt["components"]
    assert len(components) == 5
    assert tuple(item["role"] for item in components) == (
        CHAIR_ASSEMBLY_ROLES
    )
    for role, item, result in zip(
        CHAIR_ASSEMBLY_ROLES, components, research.components,
    ):
        geometry = result.geometry
        edges = {
            frozenset((start, end))
            for _face, names in geometry.faces
            for start, end in zip(names, names[1:] + names[:1])
        }
        assert item["role"] == role
        assert item["component_id"] == result.component_id
        assert item["procedure_id"] == result.procedure_id
        assert item["valid"] is True and item["closed"] is True
        assert item["solid_count"] == item["shell_count"] == 1
        assert item["vertex_count"] == len(geometry.vertices)
        assert item["edge_count"] == len(edges)
        assert item["face_count"] == len(geometry.faces)
        assert item["face_ids"] == tuple(name for name, _ in geometry.faces)
        assert item["bounds_mm"] == tuple(map(float, geometry.bounds_mm))
        assert abs(item["volume_mm3"] - float(geometry.volume_mm3)) <= (
            item["numerical_volume_budget_mm3"]
        )
        assert item["volume_residual_mm3"] <= item[
            "numerical_volume_budget_mm3"
        ]
        assert item["maximum_vertex_residual_mm"] <= receipt[
            "numerical_length_budget_mm"
        ]
        assert item["maximum_bounds_residual_mm"] <= receipt[
            "numerical_length_budget_mm"
        ]
        kernel_tolerance = item["maximum_kernel_tolerance_mm"]
        assert kernel_tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            kernel_tolerance, KERNEL_TOLERANCE_MM,
            rel_tol=1.0e-12, abs_tol=0.0,
        )
    measured_sum = sum(item["volume_mm3"] for item in components)
    analytical_sum = float(research.geometry.component_volume_sum_mm3)
    assert math.isclose(
        receipt["component_volume_sum_mm3"], measured_sum,
        rel_tol=0.0, abs_tol=receipt["numerical_volume_budget_mm3"],
    )
    assert abs(measured_sum - analytical_sum) <= receipt[
        "numerical_volume_budget_mm3"
    ]
    contacts = receipt["contacts"]
    expected_pairs = tuple(itertools.combinations(
        (item.component_id for item in research.components), 2,
    ))
    assert tuple(item["component_ids"] for item in contacts) == expected_pairs
    for contact in contacts:
        assert math.isfinite(contact["distance_mm"])
        assert contact["distance_mm"] >= 0
        assert math.isfinite(contact["common_volume_mm3"])
        assert contact["common_volume_mm3"] >= 0
        assert contact["common_solid_count"] >= 0
        assert contact["common_face_count"] >= 0
        assert contact["numerical_length_budget_mm"] == receipt[
            "numerical_length_budget_mm"
        ]
        assert contact["numerical_volume_budget_mm3"] > 0
    assert chair_definition_package_status(
        package, manifest_text,
    )["production_geometry_authorized"] is False


def main():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json",
    )
    assert qualification["compatibility_evaluation"][
        "matched_profile_id"
    ] == PROFILE_ID
    initial = document_state()
    witness = App.newDocument("ChairAssemblyWitness" + uuid.uuid4().hex)
    try:
        marker = witness.addObject("App::FeaturePython", "ResearchWitness")
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "Five-solid success and failure preserve this"
        witness.recompute()
        before = document_state()
        record, manifest = synthetic_assembly_package_records()
        original = copy.deepcopy((record, manifest))
        text = canonical_json(manifest)
        package = chair_definition_package_from_json(
            canonical_json(record), text,
        )
        encoded = chair_definition_package_to_json(package)
        reopened = chair_definition_package_from_json(encoded, text)
        assert reopened == package
        first = chair_assembly_exact.validate_chair_assembly_exact_geometry(
            reopened, text,
        )
        repeated = chair_assembly_exact.validate_chair_assembly_exact_geometry(
            package, text,
        )
        assert first == repeated
        research = chair_research.prepare_chair_assembly_research(
            package, text,
        )
        validate_receipt(first, research, package, text)
        validate_contact_failure_guards(research)
        assert document_state() == before
        assert chair_definition_package_to_json(package) == encoded
        assert (record, manifest) == original

        for name, bad, related in _mutations(record, manifest):
            try:
                expect_pre_kernel_rejection(
                    bad, related, EXPECTED_REJECTION_CODES[name],
                )
            except AssertionError as error:
                raise AssertionError("{}: {}".format(name, error)) from error

        original_builder = chair_assembly_exact._construct_components

        def fail_kernel(_research):
            raise ValueError("synthetic native construction failure")

        chair_assembly_exact._construct_components = fail_kernel
        try:
            try:
                chair_assembly_exact.validate_chair_assembly_exact_geometry(
                    package, text,
                )
            except chair_assembly_exact.ChairAssemblyExactGeometryError as error:
                assert error.code == "assembly-kernel-construction-failed"
                assert isinstance(error.__cause__, ValueError)
                diagnostic = error.diagnostic()
                assert diagnostic["recoverable"] is True
                assert diagnostic["document_mutation"] is False
                assert diagnostic["filesystem_mutation"] is False
            else:
                raise AssertionError("injected kernel failure was accepted")
        finally:
            chair_assembly_exact._construct_components = original_builder
        assert document_state() == before
        assert chair_definition_package_to_json(package) == encoded
    finally:
        App.closeDocument(witness.Name)
        if initial[0] is not None:
            App.setActiveDocument(initial[0])
    assert document_state() == initial
    print("CHAIR_ASSEMBLY_EXACT_RECEIPT=" + json.dumps({
        "contract_id": first["contract_id"],
        "package_signature": first["package_signature"],
        "manifest_signature": first["manifest_signature"],
        "bounds_mm": first["bounds_mm"],
        "component_volume_sum_mm3": first["component_volume_sum_mm3"],
        "components": [
            {key: item[key] for key in (
                "role", "component_id", "procedure_id", "bounds_mm",
                "volume_mm3", "vertex_count", "edge_count", "face_count",
            )} for item in first["components"]
        ],
        "contacts": [
            {key: item[key] for key in (
                "component_ids", "distance_mm", "common_volume_mm3",
            )} for item in first["contacts"]
        ],
        "project_status": first["project_status"],
        "production_geometry_authorized": first[
            "production_geometry_authorized"
        ],
    }, sort_keys=True))
    print(SENTINEL)


# FreeCADCmd executes scripts with their filename as __name__.
main()
