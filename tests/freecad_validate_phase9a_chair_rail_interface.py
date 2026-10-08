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
    assert_finite_contacts,
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


def validate_native_finite_contacts(result):
    """Check finite transient intersections against invented exact areas."""
    measured = assert_finite_contacts(result)
    model = result.model_research
    shapes = dict(zip((c.role for c in model.components),
                      chair_model_exact._construct_components(model)))
    scale = float(LENGTH_FACTOR)
    # Independent invented section: seat Z=8; web ends Z=18,26;
    # fishing slope=1/2; foot/head half-widths=4,3. The sharp upper
    # head overbounds any top-corner cut, above all contact regions.
    section = (
        (-3, 32), (3, 32), (3, 27), (1, 26), (1, 18),
        (4, 16.5), (4, 8), (-4, 8), (-4, 16.5), (-1, 18),
        (-1, 26), (-3, 27),
    )

    def polygon_face(points):
        vectors = [App.Vector(*(float(v) * scale for v in point))
                   for point in points]
        return Part.Face(Part.makePolygon(vectors + vectors[:1]))

    def bounds_overlap(a, b):
        return all(max(getattr(a.BoundBox, axis + "Min"),
                       getattr(b.BoundBox, axis + "Min")) <=
                   min(getattr(a.BoundBox, axis + "Max"),
                       getattr(b.BoundBox, axis + "Max")) + NUMERICAL_BUDGET_MM
                   for axis in "XYZ")

    rail = polygon_face(tuple((-15, y, z) for y, z in section)).extrude(
        App.Vector(30 * scale, 0, 0),
    )
    assert rail.isValid() and rail.isClosed() and len(rail.Solids) == 1
    areas = measured["area_squared_mm4"]
    identities = {
        "base-plinth": (), "outer-jaw": (),
        "rail-seat": ("seat-bottom",),
        "inner-jaw": ("inner-web-upper", "inner-web-lower", "inner-foot",
                      "inner-foot-side"),
        "key": tuple(name for name in areas if name not in (
            "seat-bottom", "inner-web-upper", "inner-web-lower",
            "inner-foot", "inner-foot-side",
        )),
    }
    contacts = {}
    for role, shape in shapes.items():
        common = shape.common(rail)
        assert common.isNull() or common.isValid(), role
        # Propagate the existing length budget dimensionally. These are
        # conversion/kernel bounds, not contact or manufacturing limits.
        area_budget = (shape.Length + rail.Length) * NUMERICAL_BUDGET_MM
        volume_budget = (shape.Area + rail.Area) * NUMERICAL_BUDGET_MM
        expected_area = sum(math.sqrt(areas[name])
                            for name in identities[role]) * scale ** 2
        assert abs(common.Volume) <= volume_budget, role
        # Solid common can omit lower-dimensional contact. Intersect
        # actual boundary faces; their interiors are disjoint, so each
        # bearing patch contributes once to this finite area sum.
        bearings = []
        for face in shape.Faces:
            for rail_face in rail.Faces:
                if bounds_overlap(face, rail_face):
                    bearing = face.common(rail_face)
                    assert bearing.isNull() or bearing.isValid(), role
                    if bearing.Area:
                        bearings.append(bearing.Area)
        contact_area = sum(bearings)
        assert len(bearings) == len(identities[role]), role
        assert abs(contact_area - expected_area) <= area_budget, role
        if identities[role]:
            assert shape.distToShape(rail)[0] <= NUMERICAL_BUDGET_MM, role
        contacts[role] = {
            "area_mm2": contact_area, "expected_area_mm2": expected_area,
            "volume_mm3": common.Volume,
            "bearing_patch_count": len(bearings),
        }
    # A whole grip-top face must not become an under-head bearing patch.
    # The only common geometry is its 55/4-long edge at Y=-1, Z=26.
    geometry = dict(model.full_size_research.geometry.components)["inner-jaw"]
    vertices = {name: point for name, *point in geometry.vertices}
    expected = [tuple(float(v) * scale for v in vertices[name])
                for name in dict(geometry.faces)["grip-top"]]
    faces = [face for face in shapes["inner-jaw"].Faces
             if len(face.Vertexes) == len(expected) and all(
                 min(math.dist(tuple(vertex.Point), point)
                     for point in expected)
                 <= NUMERICAL_BUDGET_MM for vertex in face.Vertexes)]
    assert len(faces) == 1
    under_head = polygon_face(((-15, -1, 26), (15, -1, 26),
                               (15, -3, 27), (-15, -3, 27)))
    # Common omits the edge too. Section retains the intersection of
    # these two finite faces and must not become an area contact.
    edge = faces[0].section(under_head)
    assert not edge.isNull() and edge.isValid()
    assert not edge.Faces
    assert abs(edge.Length - 55 / 4 * scale) <= (
        2 * len(edge.Edges) * NUMERICAL_BUDGET_MM
    )
    # Independently integrate the deliberate key/jaw overlap. The key
    # fills a 1/4-thick strip behind Y=9, from Z=17 to the jaw top24.
    # Jaw widths are 16.2 at17, 16 at18, 14 at24; X remains within
    # the key's [-10,10]. Strip volume = (16.1*1 + 15*6)/4.
    overlap = shapes["key"].common(shapes["outer-jaw"])
    expected_overlap = 1061 / 40 * scale ** 3
    overlap_budget = sum(shapes[role].Area for role in (
        "key", "outer-jaw",
    )) * NUMERICAL_BUDGET_MM
    assert overlap.isValid() and overlap.Volume > overlap_budget
    assert abs(overlap.Volume - expected_overlap) <= overlap_budget
    return {
        "rail_contacts": contacts, "under_head_edge_length_mm": edge.Length,
        "key_outer_overlap_mm3": overlap.Volume,
        "expected_key_outer_overlap_mm3": expected_overlap,
        "physical_rail_fit_proved": False,
    }


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
        finite_contacts = validate_native_finite_contacts(result)
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
            "finite_contacts": finite_contacts,
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
