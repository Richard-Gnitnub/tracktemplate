"""Import-safe unittest payload for the finite private P outer-jaw proof.

Run in the qualified FreeCAD environment through the existing guarded
runner. Optional ignored source and parameter files supply independent
source coverage. This module creates no document, launcher or output file.
"""

import copy
from dataclasses import fields, replace
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
)
from tracktemplate.application.chair_research import (  # noqa: E402
    prepare_chair_p_outer_jaw_research,
)
from tracktemplate.domain.chair_p_outer_jaw import (  # noqa: E402
    ChairPOuterJawParameters,
    construct_chair_p_outer_jaw,
)
from validate_phase9a_chair_seat import resign_package  # noqa: E402
from validate_phase9b_chair_p_outer_jaw import (  # noqa: E402
    load_package,
    synthetic_p_outer_jaw_package_records,
)


SENTINEL = "Phase 9B P outer-jaw FreeCAD validation passed"
EPSILON_MM = 1.0e-7


def _document_state(app):
    return (
        app.ActiveDocument.Name if app.ActiveDocument else None,
        tuple((name, tuple((obj.Name, obj.Label, tuple(obj.State))
                           for obj in document.Objects))
              for name, document in sorted(app.listDocuments().items())),
    )


def _source_parameters(source, values):
    """Check explicit full-size inputs against the retained source record."""
    assert set(values) == {field.name for field in fields(
        ChairPOuterJawParameters
    )}
    parameters = ChairPOuterJawParameters(**{
        name: Fraction(value) for name, value in values.items()
    })
    scale = Fraction("304.8") / Fraction(str(source["scale_mm_per_foot"]))
    assert scale > 0
    dimensional = source["parameters"]["3d"]
    for name, source_name in (
        ("jaw_top_half_width_mm", "P_jaw_half_width_top"),
        ("jaw_bottom_half_width_mm", "P_jaw_half_width_mid"),
        ("jaw_top_depth_mm", "P_jaw_depth_top"),
        ("jaw_bottom_depth_mm", "P_jaw_depth_bot"),
        ("plinth_thickness_mm", "P_chair_plinth_thick"),
        ("seat_thickness_mm", "seat_thickness"),
    ):
        assert abs(float(getattr(parameters, name)
                         - Fraction(str(dimensional[source_name]))
                         * Fraction("25.4"))) <= EPSILON_MM
    rail = source["parameters"]["rail"]
    for name, source_name in (
        ("rail_depth_mm", "rail_depth_mm"),
        ("rail_head_width_mm", "rail_head_width_mm"),
        ("rail_foot_width_mm", "rail_foot_width_mm"),
        ("rail_web_width_mm", "rail_web_thick_mm"),
        ("rail_web_top_from_top_mm", "rail_web_top_mm"),
        ("rail_web_bottom_from_top_mm", "rail_web_bottom_mm"),
    ):
        assert abs(float(getattr(parameters, name)
                         - Fraction(str(rail[source_name])) * scale)) <= (
            EPSILON_MM
        )
    assert parameters.rail_fish_ratio == Fraction(str(rail["rail_fish_angle"]))
    return parameters, scale


def _source_coverage(source, values, app, adapter):
    """Compare all retained source faces and their recorded diagonals."""
    assert source["schema"] == 1 and source["status"] == "PASS"
    assert source["units"] == "mm"
    assert source["coordinate_origin"] == "rail top / gauge face"
    assert source["face_count"] == len(source["faces"]) == 21
    parameters, scale = _source_parameters(source, values)
    geometry = construct_chair_p_outer_jaw(parameters)
    shapes = dict(adapter.construct_chair_p_outer_jaw_shapes(geometry))
    measurements = [adapter._measure_part(name, shapes[name], part)
                    for name, part in geometry.parts]
    maximum_vertex_residual = 0.0
    face_results = []
    covered = set()
    for role, part in geometry.parts:
        native = shapes[role]
        points = {name: tuple(float(value) for value in point)
                  for name, *point in part.vertices}
        unmatched = list(native.Faces)
        for source_name, vertex_ids in part.source_faces:
            index = int(source_name.rsplit("-", 1)[-1])
            raw = source["faces"][index]
            assert raw["block"] == "PJAW" and len(raw["vertices"]) == 4
            transformed = []
            for raw_point in raw["vertices"]:
                x, y, z = (Fraction(str(value)) * scale
                           for value in raw_point)
                transformed.append(tuple(float(value) for value in (
                    -x, -y - parameters.rail_head_width_mm / 2,
                    z + parameters.rail_depth_mm
                    + parameters.seat_thickness_mm,
                )))
            expected = [points[name] for name in vertex_ids]
            remaining = list(expected)
            for point in transformed:
                nearest = min(remaining, key=lambda p: math.dist(point, p))
                residual = math.dist(point, nearest)
                assert residual <= EPSILON_MM, (source_name, residual)
                maximum_vertex_residual = max(
                    maximum_vertex_residual, residual,
                )
                remaining.remove(nearest)
            assert not remaining
            polygons = ([transformed[:3], [transformed[0], transformed[2],
                                          transformed[3]]]
                        if index in (15, 16) else [transformed])
            for polygon in polygons:
                vectors = [app.Vector(*point) for point in polygon]
                mids = [(first + second) / 2 for first, second in
                        zip(vectors, vectors[1:] + vectors[:1])]
                normal = app.Vector(0, 0, 0)
                for first, second in zip(vectors, vectors[1:] + vectors[:1]):
                    normal += first.cross(second)
                area = normal.Length / 2
                assert area > 0
                normal.normalize()
                matches = [face for face in unmatched if all(
                    face.isInside(point, EPSILON_MM, True)
                    for point in vectors + mids
                ) and abs(abs(normal.dot(face.normalAt(0, 0))) - 1) <= 1e-12]
                assert len(matches) == 1, (source_name, len(matches))
                face = matches[0]
                unmatched.remove(face)
                area_budget = max(face.Length * EPSILON_MM, area * 1e-12)
                assert abs(face.Area - area) <= area_budget
                face_results.append({
                    "source_face_id": source_name,
                    "area_residual_mm2": abs(face.Area - area),
                    "numerical_area_budget_mm2": area_budget,
                })
            covered.add(index)
        assert not unmatched, role
    assert covered == set(range(21)) and len(face_results) == 23
    return {
        "source_face_count": 21, "native_face_count": 23,
        "source_diagonal": "0-2 for body source faces 15 and 16",
        "maximum_vertex_residual_mm": maximum_vertex_residual,
        "complete_source_face_coverage": True,
        "face_measurements": face_results, "parts": measurements,
        "project_status": "reference-only",
        "intended_uses": ["private-development"],
        "production_geometry_authorized": False,
    }


def _optional_source(app, adapter):
    source_path = os.environ.get("TRACKTEMPLATE_P_OUTER_JAW_SOURCE")
    parameters_path = os.environ.get("TRACKTEMPLATE_P_OUTER_JAW_PARAMETERS")
    if not source_path and not parameters_path:
        return None
    assert source_path and parameters_path
    paths = [Path(path).resolve() for path in (source_path, parameters_path)]
    content = [path.read_bytes() for path in paths]
    source, values = [json.loads(data) for data in content]
    result = _source_coverage(source, values, app, adapter)
    for field, value in (("face_count", 20), ("coordinate_origin", "wrong")):
        invalid = copy.deepcopy(source)
        invalid[field] = value
        try:
            _source_coverage(invalid, values, app, adapter)
        except AssertionError:
            pass
        else:
            raise AssertionError("Invalid source metadata accepted: " + field)
    invalid = copy.deepcopy(source)
    invalid["faces"][15]["vertices"][2][0] += 1
    try:
        _source_coverage(invalid, values, app, adapter)
    except AssertionError:
        pass
    else:
        raise AssertionError("Changed source end diagonal accepted")
    result["identities"] = {
        str(path): hashlib.sha256(data).hexdigest()
        for path, data in zip(paths, content)
    }
    assert [path.read_bytes() for path in paths] == content
    result["source_rejection_count"] = 3
    return result


def _wrong_ratio_unit(record, _manifest):
    quantity = next(item for item in record["definition"]["quantities"]
                    if item["purpose"] == "rail_fish_ratio")
    quantity.update({
        "quantity_kind": "length", "source_unit": "mm",
        "canonical_unit": "mm",
    })


def _different_frame_identity(record, _manifest):
    definition = record["definition"]
    original = next(item for item in definition["quantities"]
                    if item["purpose"] == "rail_head_width_mm")
    alternate = dict(original, quantity_id="quantity:test:alternate-head")
    definition["quantities"].append(alternate)
    definition["quantities"].sort(key=lambda item: item["quantity_id"])
    frame = definition["procedures"][0]
    frame["parameter_quantity_ids"] = [
        alternate["quantity_id"] if value == original["quantity_id"] else value
        for value in frame["parameter_quantity_ids"]
    ]


class TestChairPOuterJaw(unittest.TestCase):
    """Prove the finite synthetic native boundary and optional raw source."""

    def test_fixed_outer_jaw(self):
        import FreeCAD as app

        from tracktemplate.adapters.freecad import chair_p_outer_jaw_exact

        adapter = chair_p_outer_jaw_exact
        state = _document_state(app)
        record, manifest = synthetic_p_outer_jaw_package_records()
        package, text = load_package(record, manifest)
        research = prepare_chair_p_outer_jaw_research(package, text)
        result = adapter.validate_chair_p_outer_jaw_exact_geometry(
            package, text,
        )
        self.assertEqual(result["solid_count"], 2)
        self.assertEqual(result["source_face_count"], 21)
        self.assertEqual(result["face_count"], 23)
        self.assertEqual([part["part_id"] for part in result["parts"]],
                         ["spacer", "body"])
        self.assertTrue(result["valid"] and result["closed"])
        self.assertFalse(result["production_geometry_authorized"])
        self.assertFalse(result["document_mutation"])
        self.assertFalse(result["filesystem_mutation"])
        self.assertEqual(result["project_status"], "reference-only")
        self.assertEqual(result["intended_uses"], ["private-development"])
        self.assertEqual(result["package_signature"],
                         package.content_signature)
        self.assertEqual(result["manifest_signature"],
                         research.manifest_signature)
        geometry = research.geometry
        role, part = geometry.parts[0]
        bad_vertices = tuple((name, x + 1, y, z)
                             for name, x, y, z in part.vertices)
        for bad in (
            replace(geometry, parts=(
                (role, replace(part, vertices=bad_vertices)),
                geometry.parts[1],
            )),
            replace(geometry, parts=tuple(reversed(geometry.parts))),
            replace(geometry, volume_mm3=geometry.volume_mm3 + 1),
            replace(geometry, parts=(
                (role, replace(part, source_faces=())), geometry.parts[1],
            )),
        ):
            with patch.object(adapter, "construct_chair_seat_shape",
                              side_effect=AssertionError("host was reached")):
                with self.assertRaises(adapter.ChairPOuterJawExactGeometryError
                                       ) as caught:
                    adapter.construct_chair_p_outer_jaw_shapes(bad)
            self.assertEqual(caught.exception.code,
                             "p-outer-jaw-boundary-mismatch")
        for mutate, code in (
            (lambda r, m: r["package"]["permissions"].update(
                adaptation="restricted"), "research-use-restricted"),
            (lambda r, m: r["lineage"][0].update(evidence_state="unresolved"),
             "research-lineage-unresolved"),
            (_wrong_ratio_unit, "research-parameter-unit"),
            (_different_frame_identity, "research-frame-inputs"),
        ):
            invalid, invalid_manifest = synthetic_p_outer_jaw_package_records()
            mutate(invalid, invalid_manifest)
            resign_package(invalid, invalid_manifest)
            with patch.object(adapter, "construct_chair_p_outer_jaw_shapes",
                              side_effect=AssertionError("host was reached")):
                with self.assertRaises(
                    definitions.ChairDefinitionError,
                ) as error:
                    adapter.validate_chair_p_outer_jaw_exact_geometry(
                        *load_package(invalid, invalid_manifest)
                    )
            self.assertEqual(error.exception.code, code)
        source = _optional_source(app, adapter)
        self.assertEqual(_document_state(app), state)
        print("TRACKTEMPLATE_P_OUTER_JAW_RESULT=" + json.dumps({
            "status": "PASS", "synthetic": result, "source": source,
            "forgery_rejection_count": 4, "package_rejection_count": 4,
            "document_state_unchanged": True,
        }, sort_keys=True, allow_nan=False))
        print(SENTINEL)


if __name__ == "__main__":
    unittest.main()
