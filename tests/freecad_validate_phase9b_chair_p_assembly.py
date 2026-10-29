"""Import-safe native unittest for the private P structural assembly.

The qualified guarded runner owns execution and evidence capture. One
assembly is constructed. Optional private package, manifest and independent
source-reference files replace the synthetic valid case together. No
document, launcher, GUI or output file is created by this module.
"""

import copy
from dataclasses import replace
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
    prepare_chair_p_assembly_research,
)
from validate_phase9a_chair_seat import resign_package  # noqa: E402
from validate_phase9b_chair_p_assembly import (  # noqa: E402
    load_package,
    synthetic_p_assembly_package_records,
)


SENTINEL = "Phase 9B P structural assembly FreeCAD validation passed"
EPSILON_MM = 1.0e-7
SOLID_IDS = (
    "base-plinth", "rail-seat", "outer-jaw:spacer", "outer-jaw:body",
)


def _document_state(app):
    return (
        app.ActiveDocument.Name if app.ActiveDocument else None,
        tuple((name, tuple((obj.Name, obj.Label, tuple(obj.State))
                           for obj in document.Objects))
              for name, document in sorted(app.listDocuments().items())),
    )


def _close(actual, expected):
    assert len(actual) == len(expected)
    residuals = [abs(float(a) - float(b)) for a, b in zip(actual, expected)]
    assert all(math.isfinite(value) and value <= EPSILON_MM
               for value in residuals), residuals
    return max(residuals, default=0.0)


def _interfaces(geometry):
    """Expose named interface coordinates for independent comparison."""
    base, seat, jaw = (value for _role, value in geometry.components)
    bp = {name: point for name, *point in base.vertices}
    sp = {name: point for name, *point in seat.vertices}
    body = dict(jaw.parts)["body"]
    jp = {name: point for name, *point in body.vertices}
    landmarks = dict(geometry.landmarks)
    return {
        "base_bottom_z": base.bounds_mm[2],
        "base_edge_z": bp["e00"][2],
        "seat_bottom_z": seat.bounds_mm[2],
        "base_plinth_top_z": bp["a"][2],
        "jaw_bottom_z": body.bounds_mm[2],
        "seat_top_z": seat.bounds_mm[5],
        "rail_top_z": landmarks["rail-top-centre"][2],
        "gauge_face_y": landmarks["gauge-face-at-seat"][1],
        "seat_rear_y": sp["top-p33"][1],
        "jaw_front_y": jp["a"][1],
        "table_centre_y": dict(seat.landmarks)["table-centre-at-seat"][1],
        "base_inner_length": base.parameters.chair_inner_length_mm,
        "table_centre_from_gauge_face": (
            seat.parameters.table_centre_from_gauge_face_mm
        ),
        "table_centre_from_inner_end": (
            geometry.table_centre_from_inner_end_mm
        ),
    }


def _reference_inputs(reference, research):
    """Reject source metadata or interface mismatches before host work."""
    assert reference["schema"] == 1 and reference["status"] == "PASS"
    assert reference["length_unit"] == "mm"
    assert reference["length_basis"] == "full-size"
    frame = research.package.to_record()["definition"]["frame"]["frame_id"]
    assert reference["frame_id"] == frame
    assert isinstance(reference["source_identity"], dict)
    assert reference["source_identity"]
    assert tuple(part["solid_id"] for part in reference["parts"]) == SOLID_IDS
    geometry = research.geometry
    base, seat, jaw = (value for _role, value in geometry.components)
    parts = (base, seat, *(part for _role, part in jaw.parts))
    residuals = [_close(geometry.bounds_mm, reference["bounds_mm"])]
    for part, expected in zip(parts, reference["parts"]):
        residuals.append(_close(part.bounds_mm, expected["bounds_mm"]))
    landmarks = dict(geometry.landmarks)
    assert set(landmarks) == set(reference["landmarks_mm"])
    for name, point in landmarks.items():
        residuals.append(_close(point, reference["landmarks_mm"][name]))
    interfaces = _interfaces(geometry)
    assert set(interfaces) == set(reference["interfaces_mm"])
    for name, value in interfaces.items():
        residuals.append(_close([value], [reference["interfaces_mm"][name]]))
    return max(residuals)


def _inputs():
    names = ("PACKAGE", "MANIFEST", "REFERENCE")
    paths = [os.environ.get("TRACKTEMPLATE_P_ASSEMBLY_" + name)
             for name in names]
    if not any(paths):
        return (*load_package(*synthetic_p_assembly_package_records()),
                None, ())
    assert all(paths), "All three P assembly source inputs are required"
    inputs = tuple((Path(value).resolve(), Path(value).read_bytes())
                   for value in paths)
    record, manifest, reference = (json.loads(data) for _path, data in inputs)
    package, text = load_package(record, manifest)
    return package, text, reference, inputs


def _wrong_frame(record, _manifest):
    record["definition"]["frame"]["y_axis"] = "field-to-gauge"


class TestChairPAssembly(unittest.TestCase):
    """Prove one assembly and refusals without creating a document."""

    def test_structural_assembly(self):
        import FreeCAD as app

        from tracktemplate.adapters.freecad import chair_p_assembly_exact

        adapter = chair_p_assembly_exact
        state = _document_state(app)
        package, text, reference, inputs = _inputs()
        research = prepare_chair_p_assembly_research(package, text)
        source_residual = None
        if reference is not None:
            source_residual = _reference_inputs(reference, research)
            for field, value in (("frame_id", "wrong"),
                                 ("length_basis", "model")):
                invalid = copy.deepcopy(reference)
                invalid[field] = value
                with self.assertRaises(AssertionError):
                    _reference_inputs(invalid, research)
            invalid = copy.deepcopy(reference)
            invalid["interfaces_mm"]["seat_rear_y"] += 1
            with self.assertRaises(AssertionError):
                _reference_inputs(invalid, research)
        for mutate, code in (
            (lambda r, m: r["package"]["permissions"].update(
                adaptation="restricted"), "research-use-restricted"),
            (lambda r, m: r["lineage"][0].update(evidence_state="unresolved"),
             "research-lineage-unresolved"),
            (_wrong_frame, "unsupported-coordinate-frame"),
        ):
            invalid, manifest = synthetic_p_assembly_package_records()
            mutate(invalid, manifest)
            resign_package(invalid, manifest)
            with patch.object(adapter, "construct_chair_p_assembly_shapes",
                              side_effect=AssertionError("host was reached")):
                with self.assertRaises(definitions.ChairDefinitionError) as e:
                    adapter.validate_chair_p_assembly_exact_geometry(
                        *load_package(invalid, manifest)
                    )
            self.assertEqual(e.exception.code, code)
        geometry = research.geometry
        base_role, base = geometry.components[0]
        bad_parameters = copy.deepcopy(base.parameters)
        object.__setattr__(bad_parameters, "chair_half_width_mm", Fraction(0))
        bad_base = replace(base, parameters=bad_parameters)
        displaced = replace(base, vertices=tuple(
            (name, x + 1, y, z) for name, x, y, z in base.vertices
        ))
        for bad in (
            replace(geometry, components=((base_role, displaced),
                                         *geometry.components[1:])),
            replace(geometry, components=tuple(reversed(geometry.components))),
            replace(geometry, component_volume_sum_mm3=(
                geometry.component_volume_sum_mm3 + 1
            )),
            replace(geometry, components=((base_role, bad_base),
                                         *geometry.components[1:])),
        ):
            with patch.object(adapter, "construct_chair_base_shape",
                              side_effect=AssertionError("host was reached")):
                with self.assertRaises(adapter.ChairPAssemblyExactGeometryError):
                    adapter.construct_chair_p_assembly_shapes(bad)
        with patch.object(adapter, "construct_chair_base_shape",
                          side_effect=ValueError("deliberate kernel refusal")):
            with self.assertRaises(adapter.ChairPAssemblyExactGeometryError
                                   ) as error:
                adapter.validate_chair_p_assembly_exact_geometry(package, text)
        self.assertEqual(error.exception.code,
                         "p-assembly-kernel-construction-failed")
        self.assertFalse(error.exception.diagnostic()["document_mutation"])
        self.assertEqual(_document_state(app), state)
        result = adapter.validate_chair_p_assembly_exact_geometry(package, text)
        self.assertEqual(result["solid_count"], 4)
        self.assertEqual(result["shell_count"], 4)
        self.assertEqual(result["component_count"], 3)
        self.assertEqual(result["shape_type"], "Compound")
        self.assertEqual(tuple(part["solid_id"] for part in result["parts"]),
                         SOLID_IDS)
        self.assertEqual([part["component_id"] for part in result["parts"]],
                         [component.component_id for component in (
                             *research.components, research.components[-1],
                         )])
        self.assertTrue(result["valid"] and result["closed"])
        self.assertFalse(result["production_geometry_authorized"])
        self.assertFalse(result["document_mutation"])
        self.assertFalse(result["filesystem_mutation"])
        self.assertEqual(result["project_status"], "reference-only")
        self.assertEqual(result["intended_uses"], ["private-development"])
        self.assertEqual(result["package_signature"], package.content_signature)
        self.assertEqual(result["manifest_signature"], research.manifest_signature)
        if reference is not None:
            _close(result["bounds_mm"], reference["bounds_mm"])
            for part, expected in zip(result["parts"], reference["parts"]):
                _close(part["bounds_mm"], expected["bounds_mm"])
        self.assertEqual(_document_state(app), state)
        self.assertTrue(all(path.read_bytes() == data for path, data in inputs))
        print("TRACKTEMPLATE_P_ASSEMBLY_RESULT=" + json.dumps({
            "status": "PASS", "assembly": result,
            "source_reference_compared": reference is not None,
            "source_interface_count": len(reference["interfaces_mm"])
            if reference is not None else 0,
            "maximum_source_residual_mm": source_residual,
            "source_rejection_count": 3 if reference is not None else 0,
            "forgery_rejection_count": 4, "package_rejection_count": 3,
            "kernel_failure_rejection_count": 1,
            "document_state_unchanged": True,
            "identities": {str(path): hashlib.sha256(data).hexdigest()
                           for path, data in inputs},
        }, sort_keys=True, allow_nan=False))
        print(SENTINEL)


if __name__ == "__main__":
    unittest.main()
