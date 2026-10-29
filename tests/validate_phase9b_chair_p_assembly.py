#!/usr/bin/env python3
"""Prove P composition with invented, non-prototype research inputs.

The fixture contains no prototype dimensions or authentic source data.
It preserves three semantic components and four separate source bodies.
"""

import copy
from dataclasses import replace
from decimal import Context, Inexact, Rounded, localcontext
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from tracktemplate.domain.chair_p_assembly import (  # noqa: E402
    CHAIR_P_ASSEMBLY_ROLES,
    assemble_p_chair_components,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
from validate_phase9a_chair_assembly import _replace_ids  # noqa: E402
from validate_phase9a_chair_base import (  # noqa: E402
    synthetic_base_package_records,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)
from validate_phase9b_chair_p_outer_jaw import (  # noqa: E402
    synthetic_p_outer_jaw_package_records,
)
from validate_phase9b_chair_p_seat import (  # noqa: E402
    synthetic_p_seat_package_records,
)


SENTINEL = "Phase 9B chair P assembly standalone validation passed"
PACKAGE_ID = "tracktemplate:test:synthetic-research-p-assembly"
SHARED_VALUES = {
    "rail_head_width_mm": "8", "rail_foot_width_mm": "10",
    "rail_depth_mm": "20", "seat_thickness_mm": "5",
    "edge_thickness_mm": "1", "plinth_thickness_mm": "3",
}
FIXTURES = (
    ("base-plinth", synthetic_base_package_records),
    ("rail-seat", synthetic_p_seat_package_records),
    ("outer-jaw", synthetic_p_outer_jaw_package_records),
)


def synthetic_p_assembly_package_records():
    """Compose invented component records without prototype source data."""
    parts = []
    for role, factory in FIXTURES:
        record, manifest = factory()
        identities = {}
        for items, field in (
            (record["definition"]["quantities"], "quantity_id"),
            (record["lineage"], "lineage_id"),
            (manifest["dependencies"], "identifier"),
        ):
            for item in items:
                old = item[field]
                identities[old] = old.rsplit(":", 1)[0] + ":" + role + ":" + (
                    old.rsplit(":", 1)[1]
                )
        record, manifest = (
            _replace_ids(item, identities) for item in (record, manifest)
        )
        for quantity in record["definition"]["quantities"]:
            value = SHARED_VALUES.get(quantity["purpose"])
            if quantity["purpose"] == "chair_inner_length_mm":
                value = "16"
            if value is not None:
                quantity["source_value"] = value
                quantity["canonical_value"] = value
        parts.append((record, manifest))
    record, manifest = copy.deepcopy(parts[1])
    record["package"]["package_id"] = PACKAGE_ID
    record["definition"].update({
        "definition_id": PACKAGE_ID + ":definition",
        "prototype_designation": "SYNTHETIC-P-ASSEMBLY-NOT-A-PROTOTYPE",
        "description": "Invented structural assembly; no prototype data.",
    })
    record["dependency_manifest"].update({
        "manifest_id": PACKAGE_ID + ":manifest", "subject_id": PACKAGE_ID,
    })
    manifest["manifest_id"] = PACKAGE_ID + ":manifest"
    manifest["subject"]["identifier"] = PACKAGE_ID
    definition = record["definition"]
    definition["quantities"] = [
        q for part, _ in parts for q in part["definition"]["quantities"]
    ]
    definition["procedures"] = [definition["procedures"][0]] + [
        part["definition"]["procedures"][1] for part, _ in parts
    ]
    definition["components"] = [
        part["definition"]["components"][0] for part, _ in parts
    ]
    record["lineage"] = [q for part, _ in parts for q in part["lineage"]]
    manifest["dependencies"] = [
        q for _, item in parts for q in item["dependencies"]
    ]
    quantity = copy.deepcopy(definition["quantities"][0])
    quantity.update({
        "quantity_id": "quantity:test:assembly:table-end",
        "purpose": "table_centre_from_inner_end_mm",
        "source_value": "4", "canonical_value": "4",
    })
    definition["quantities"].append(quantity)
    constraint = copy.deepcopy(definition["procedures"][1])
    constraint.update({
        "procedure_id": "procedure:test:2-p-assembly",
        "kind": "assembly-constraint",
        "rule_id": "tracktemplate.chair.p-assembly-reference.v1",
        "parameter_quantity_ids": [quantity["quantity_id"]],
        "input_ids": sorted(
            p["output_ids"][0] for p in definition["procedures"][1:]
        ),
        "output_ids": ["result:test:p-assembly"],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = sorted(
        p["procedure_id"] for p in definition["procedures"][1:]
    )
    definition["procedures"].append(constraint)
    for name, key in (("quantities", "quantity_id"),
                      ("procedures", "procedure_id"),
                      ("components", "component_id")):
        definition[name].sort(key=lambda item: item[key])
    record["lineage"].sort(key=lambda item: item["lineage_id"])
    manifest["dependencies"].sort(key=lambda item: item["identifier"])
    return resign_package(record, manifest), manifest


def load_package(record, manifest):
    """Load detached signed records at the original neutral boundary."""
    text = canonical_json(manifest)
    return definitions.chair_definition_package_from_json(
        canonical_json(record), text,
    ), text


def _prepare(record, manifest):
    return chair_research.prepare_chair_p_assembly_research(
        *load_package(record, manifest)
    )


def _change(record, role, purpose, value):
    for quantity in record["definition"]["quantities"]:
        if quantity["purpose"] == purpose and (
            role is None or ":" + role + ":" in quantity["quantity_id"]
        ):
            quantity["source_value"] = quantity["canonical_value"] = value


class ChairPAssemblyTests(unittest.TestCase):
    """Check composition, exact relationships and fail-closed contracts."""

    def test_package_and_four_body_composition(self):
        record, manifest = synthetic_p_assembly_package_records()
        before = copy.deepcopy((record, manifest))
        self.assertEqual(validate_document(manifest), [])
        result = _prepare(record, manifest)
        self.assertEqual((record, manifest), before)
        self.assertEqual(result.package.to_record(), record)
        self.assertEqual(result.manifest_json, canonical_json(manifest))
        self.assertEqual(result.manifest_signature,
                         record["dependency_manifest"]["content_signature"])
        self.assertEqual(tuple(role for role, _ in result.geometry.components),
                         ("base-plinth", "rail-seat", "outer-jaw"))
        base, seat, jaw = (r.geometry for r in result.components)
        self.assertEqual(tuple(role for role, _ in jaw.parts),
                         ("spacer", "body"))
        self.assertEqual(result.geometry.component_volume_sum_mm3,
                         base.volume_mm3 + Fraction(seat.volume_mm3)
                         + jaw.volume_mm3)
        self.assertEqual(result.geometry.table_centre_from_inner_end_mm, 4)
        self.assertEqual(dict(result.geometry.landmarks), {
            "base-origin": (0, 0, 0), "rail-seat-centre": (0, 0, 5),
            "rail-top-centre": (0, 0, 25),
            "gauge-face-at-seat": (0, -4, 5),
        })
        self.assertEqual(result.geometry.bounds_mm,
                         (-8, -20, 0, 8, 11, Fraction(47, 2)))
        for component in result.components:
            self.assertIs(component.package, result.package)
            self.assertEqual(component.manifest_signature,
                             result.manifest_signature)

    def test_determinism_changed_input_and_change_back(self):
        record, manifest = synthetic_p_assembly_package_records()
        original = _prepare(record, manifest)
        changed = copy.deepcopy(record)
        _change(changed, None, "rail_depth_mm", "21")
        resign_package(changed, manifest)
        result = _prepare(changed, manifest)
        self.assertNotEqual(result.geometry, original.geometry)
        self.assertNotEqual(result.package.content_signature,
                            original.package.content_signature)
        self.assertEqual([c.component_id for c in result.components],
                         [c.component_id for c in original.components])
        self.assertEqual([c.procedure_id for c in result.components],
                         [c.procedure_id for c in original.components])
        _change(changed, None, "rail_depth_mm", "20")
        resign_package(changed, manifest)
        self.assertEqual(_prepare(changed, manifest), original)
        with localcontext(Context(prec=3)) as context:
            context.traps[Inexact] = context.traps[Rounded] = True
            self.assertEqual(_prepare(record, manifest), original)

    def test_source_end_relationship_and_shared_inputs(self):
        for role, name, value in (
            ("base-plinth", "chair_inner_length_mm", "17"),
            (None, "table_centre_from_inner_end_mm", "5"),
            (None, "table_centre_from_inner_end_mm", "0"),
            ("base-plinth", "plinth_thickness_mm", "2"),
            ("base-plinth", "edge_thickness_mm", "2"),
            ("outer-jaw", "rail_foot_width_mm", "11"),
            ("outer-jaw", "rail_depth_mm", "21"),
        ):
            with self.subTest(role=role, name=name):
                record, manifest = synthetic_p_assembly_package_records()
                _change(record, role, name, value)
                expected = ("research-frame-inputs"
                            if name == "rail_depth_mm" else
                            "research-p-assembly-geometry-invalid")
                self.assert_refused_before_construction(
                    record, manifest, expected,
                )

    def assert_refused_before_construction(self, record, manifest, expected):
        resign_package(record, manifest)
        before = copy.deepcopy((record, manifest))
        with patch.object(chair_research, "construct_chair_base") as base, (
            patch.object(chair_research, "construct_chair_p_seat")
        ) as seat, patch.object(
            chair_research, "construct_chair_p_outer_jaw"
        ) as jaw:
            with self.assertRaises(definitions.ChairDefinitionError) as caught:
                _prepare(record, manifest)
            self.assertEqual(caught.exception.code, expected)
            diagnostic = caught.exception.diagnostic()
            self.assertTrue(diagnostic["recoverable"])
            self.assertFalse(diagnostic["document_mutation"])
            self.assertFalse(diagnostic["filesystem_mutation"])
            base.assert_not_called()
            seat.assert_not_called()
            jaw.assert_not_called()
        self.assertEqual((record, manifest), before)

    def test_signed_contract_refusals(self):
        expected_codes = (
            "research-p-assembly-procedures",
            "research-p-assembly-constraint", "research-parameter-set",
            "research-p-assembly-components", "research-component-set",
            "research-p-assembly-interface", "research-lineage-unresolved",
            "research-parameter-unit", "dependency-manifest-mismatch",
            "research-validation-blocked", "research-interface-set",
            "research-unused-quantity", "research-p-assembly-constraint",
        )
        for case, expected in enumerate(expected_codes):
            with self.subTest(case=case):
                record, manifest = synthetic_p_assembly_package_records()
                definition = record["definition"]
                constraint = definition["procedures"][-1]
                if case == 0:
                    constraint["rule_id"] = "unsupported-rule"
                elif case == 1:
                    constraint["input_ids"] = constraint["input_ids"][:2]
                elif case == 2:
                    constraint["parameter_quantity_ids"] = []
                elif case == 3:
                    definition["components"][0]["role"] = "key"
                elif case == 4:
                    definition["components"][0]["placement_datum_id"] = (
                        definition["datums"][1]["datum_id"]
                    )
                elif case == 5:
                    definition["rail_interfaces"][0]["procedure_ids"] = (
                        definition["rail_interfaces"][0]["procedure_ids"][:2]
                    )
                elif case == 6:
                    record["lineage"][0]["evidence_state"] = "unresolved"
                elif case == 7:
                    quantity = next(q for q in definition["quantities"]
                                    if q["purpose"]
                                    == "table_centre_from_inner_end_mm")
                    quantity.update(quantity_kind="dimensionless",
                                    source_unit="1", canonical_unit="1")
                elif case == 8:
                    record["package"]["project_status"] = "unknown"
                elif case == 9:
                    record["validation"]["status"] = "blocked"
                elif case == 10:
                    interface = definition["rail_interfaces"][0]
                    interface["clearance_quantity_ids"] = [
                        definition["quantities"][0]["quantity_id"]
                    ]
                elif case == 11:
                    extra = dict(definition["quantities"][0],
                                 quantity_id="quantity:test:unselected-extra")
                    definition["quantities"].append(extra)
                    definition["quantities"].sort(
                        key=lambda q: q["quantity_id"],
                    )
                else:
                    constraint["kind"] = "relationship"
                self.assert_refused_before_construction(
                    record, manifest, expected,
                )

    def test_manifest_tampering_and_manufacturing_refused(self):
        record, manifest = synthetic_p_assembly_package_records()
        package, text = load_package(record, manifest)
        manifest["subject"]["description"] += " changed"
        with self.assertRaises(definitions.ChairDefinitionError):
            chair_research.prepare_chair_p_assembly_research(
                package, canonical_json(manifest),
            )
        self.assertEqual(_prepare(record, json.loads(text))
                         .package, package)
        fixture = ROOT / "tests/fixtures/chair-definition-v1-contract.json"
        profile = json.loads(fixture.read_text())["manufacturing_profiles"][0]
        profile["lineage_id"] = "lineage:test:rail-seat:context"
        profile["quantities"][0]["lineage_id"] = profile["lineage_id"]
        record["manufacturing_profiles"] = [profile]
        self.assert_refused_before_construction(
            record, json.loads(text), "research-manufacturing-unsupported",
        )

    def test_fractional_frame_and_distinct_component_widths(self):
        result = _prepare(*synthetic_p_assembly_package_records())
        constructors = (
            chair_research.construct_chair_base,
            chair_research.construct_chair_p_seat,
            chair_research.construct_chair_p_outer_jaw,
        )
        components = tuple((role, constructor(replace(
            geometry.parameters, rail_head_width_mm=Fraction(1, 3),
        ))) for (role, geometry), constructor in zip(
            result.geometry.components, constructors,
        ))
        expected = assemble_p_chair_components(
            components, table_centre_from_inner_end_mm=Fraction(4),
        )
        with localcontext(Context(prec=3)) as context:
            context.traps[Inexact] = context.traps[Rounded] = True
            self.assertEqual(assemble_p_chair_components(
                components, table_centre_from_inner_end_mm=Fraction(4),
            ), expected)
        role, base = components[0]
        wider_base = constructors[0](replace(
            base.parameters, chair_half_width_mm=Fraction(9),
        ))
        changed = assemble_p_chair_components(
            ((role, wider_base), *components[1:]),
            table_centre_from_inner_end_mm=Fraction(4),
        )
        self.assertEqual(changed.components[1:], components[1:])
        self.assertEqual(changed.bounds_mm[0], -9)
        self.assertEqual(changed.bounds_mm[3], 9)

    def test_domain_roles_types_frames_and_exact_offset(self):
        result = _prepare(*synthetic_p_assembly_package_records())
        components = result.geometry.components
        bad_inputs = (components[:2], tuple(reversed(components)),
                      (("key", components[0][1]), *components[1:]),
                      ((*components[0][:1], object()), *components[1:]))
        for candidate in bad_inputs:
            with self.subTest(candidate=candidate[0][0]):
                with self.assertRaises(ValueError):
                    assemble_p_chair_components(
                        candidate, table_centre_from_inner_end_mm=Fraction(4),
                    )
        for offset in (4, 4.0, Fraction(0), Fraction(-1), Fraction(5)):
            with self.subTest(offset=offset):
                with self.assertRaises((TypeError, ValueError)):
                    assemble_p_chair_components(
                        components, table_centre_from_inner_end_mm=offset,
                    )
        for index in range(3):
            role, geometry = components[index]
            changed = list(components)
            changed[index] = (role, replace(geometry, landmarks=tuple(
                (name, (point[0] + 1, *point[1:]))
                for name, point in geometry.landmarks
            )))
            with self.assertRaises(ValueError):
                assemble_p_chair_components(
                    tuple(changed), table_centre_from_inner_end_mm=Fraction(4),
                )
        self.assertEqual(CHAIR_P_ASSEMBLY_ROLES,
                         ("base-plinth", "rail-seat", "outer-jaw"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ChairPAssemblyTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(SENTINEL)
