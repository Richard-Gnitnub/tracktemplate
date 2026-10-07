#!/usr/bin/env python3
"""Prove a second finite chair pattern with invented signed inputs.

All tracked dimensions and source records are synthetic test doubles.
They do not describe Templot data, prototype dimensions or physical fit.
The real frozen-source package remains in ignored local evidence only.
"""

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from validate_phase9a_chair_rail_interface import (  # noqa: E402
    load_package,
    synthetic_rail_package_records,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)


SENTINEL = "Phase 9A chair L1 standalone validation passed"
ROLES = ("base-plinth", "rail-seat", "key", "outer-jaw", "inner-jaw")
RULES = {
    "base-plinth": "tracktemplate.chair.l1-base-reference.v1",
    "rail-seat": "tracktemplate.chair.l1-seat-reference.v1",
    "key": "tracktemplate.chair.key-reference.v1",
    "outer-jaw": "tracktemplate.chair.l1-outer-jaw-reference.v1",
    "inner-jaw": "tracktemplate.chair.l1-inner-jaw-reference.v1",
}
OUTER_VALUES = {
    "top_height_mm": "24", "edge_height_mm": "3",
    "top_half_width_mm": "5", "top_depth_mm": "2",
    "top_corner_radius_mm": "0.5", "edge_side_clearance_mm": "1",
    "edge_depth_mm": "19", "edge_corner_radius_mm": "1",
    "bevel_seat_half_width_mm": "9", "bevel_tip_half_width_mm": "12",
    "plinth_thickness_mm": "3", "seat_thickness_mm": "8",
    "outer_jaw_face_mm": "12", "rail_head_width_mm": "6",
    "rail_depth_mm": "24",
}
UPDATES = {
    "base-plinth": {
        "chair_half_width_mm": "18", "chair_inner_length_mm": "9",
        "chair_outer_length_mm": "20.5", "edge_thickness_mm": "3",
    },
    "rail-seat": {
        "edge_thickness_mm": "3", "under_key_half_width_mm": "9",
    },
    "inner-jaw": {
        "chair_half_width_mm": "18", "chair_inner_length_mm": "9",
        "inner_outline_inset_mm": "1", "plinth_fillet_factor": "1.5",
    },
}
DIMENSIONLESS = {
    "rail_fish_ratio", "top_to_mid_side_slope", "mid_to_seat_side_slope",
    "plinth_fillet_factor",
}
# Independent 15-degree corner samples on a 0.01 mm mark grid.
OUTLINE_HUNDREDTHS = (
    (-1800, -1850), (-1800, -200), (-1800, 200), (-1800, 600),
    (-1790, 678), (-1760, 750), (-1712, 812), (-1650, 860),
    (-1578, 890), (-1500, 900), (1500, 900), (1578, 890),
    (1650, 860), (1712, 812), (1760, 750), (1790, 678),
    (1800, 600), (1800, 200), (1800, -200), (1800, -1850),
    (1793, -1902), (1773, -1950), (1741, -1991), (1700, -2023),
    (1652, -2043), (1600, -2050), (-1600, -2050), (-1652, -2043),
    (-1700, -2023), (-1741, -1991), (-1773, -1950), (-1793, -1902),
)
EXPECTED_SEAT = {
    "top-gauge-negative": (-10, -4, 8),
    "top-gauge-positive": (10, -4, 8),
    "top-foot-positive": (10, 4, 8),
    "top-outer-positive": (9, 9, 8),
    "top-outer-negative": (-9, 9, 8),
    "top-foot-negative": (-10, 4, 8),
    "bottom-gauge-negative": (-13, -4, 3),
    "bottom-gauge-positive": (13, -4, 3),
    "bottom-foot-positive": (13, 4, 3),
    "bottom-outer-positive": (12, 9, 3),
    "bottom-outer-negative": (-12, 9, 3),
    "bottom-foot-negative": (-13, 4, 3),
}
# Planned manifold partitions. The named outer component has three solids.
EXPECTED_TOPOLOGY = {
    "base-plinth": (68, 128, 62), "rail-seat": (12, 21, 11),
    "key": (20, 36, 18), "outer-jaw": (40, 60, 26),
    "inner-jaw": (213, 506, 295),
}


def synthetic_l1_package_records():
    """Build an artificial structural variant without changing old fixtures."""
    record, manifest = synthetic_rail_package_records()
    definition = record["definition"]
    old_quantities = {q["quantity_id"]: q for q in definition["quantities"]}
    procedures = {p["procedure_id"]: p for p in definition["procedures"]}
    quantity_template = copy.deepcopy(definition["quantities"][0])
    lineage_template = copy.deepcopy(record["lineage"][0])
    dependency_template = copy.deepcopy(manifest["dependencies"][0])
    quantities, lineages, dependencies = [], [], []
    for component in definition["components"]:
        role = component["role"]
        procedure = procedures[component["procedure_ids"][0]]
        values = {old_quantities[q]["purpose"]:
                  old_quantities[q]["canonical_value"]
                  for q in procedure["parameter_quantity_ids"]}
        values = (dict(OUTER_VALUES) if role == "outer-jaw"
                  else dict(values, **UPDATES.get(role, {})))
        procedure["rule_id"] = RULES[role]
        selected = []
        for name in sorted(("context", *values)):
            suffix = role + ":" + name
            value = values.get(name, "context")
            description = "Invented L1-pattern test: {}={}".format(
                suffix, value,
            )
            digest = hashlib.sha256(description.encode()).hexdigest()
            dependency = copy.deepcopy(dependency_template)
            dependency.update({
                "identifier": "dependency:test:" + suffix,
                "name": description,
                "source": {
                    "creator_or_supplier": "TrackTemplate synthetic test",
                    "locator": "synthetic-test-double://chair-l1/" + suffix,
                    "acquired_on": "2026-10-07",
                    "evidence_sha256": digest,
                },
            })
            dependency["contribution_attestation"]["reference"] = (
                "Invented metadata in tests/validate_phase9a_chair_l1.py"
            )
            lineage = copy.deepcopy(lineage_template)
            lineage.update({
                "lineage_id": "lineage:test:" + suffix,
                "dependency_ids": [dependency["identifier"]],
                "source_file_sha256s": [digest],
                "assumptions": [description, "Not a prototype dimension."],
            })
            dependencies.append(dependency)
            lineages.append(lineage)
            if name == "context":
                continue
            quantity = copy.deepcopy(quantity_template)
            unit = "1" if name in DIMENSIONLESS else "mm"
            quantity.update({
                "quantity_id": "quantity:test:" + suffix,
                "purpose": name, "source_value": value,
                "canonical_value": value, "source_unit": unit,
                "canonical_unit": unit,
                "quantity_kind": ("dimensionless" if unit == "1"
                                  else "length"),
                "lineage_id": lineage["lineage_id"],
            })
            quantities.append(quantity)
            selected.append(quantity["quantity_id"])
        procedure["parameter_quantity_ids"] = selected
    definition["quantities"] = sorted(
        quantities, key=lambda q: q["quantity_id"],
    )
    record["lineage"] = sorted(lineages, key=lambda q: q["lineage_id"])
    manifest["dependencies"] = sorted(
        dependencies, key=lambda q: q["identifier"],
    )
    return resign_package(record, manifest), manifest


def edge_count(geometry):
    """Count semantic boundary edges, retaining separate part identities."""
    return len({frozenset((a, b)) for _name, vertices in geometry.faces
                for a, b in zip(vertices, vertices[1:] + vertices[:1])})


def assert_geometry(result):
    """Compare the complete boundary with independently derived dimensions."""
    geometries = dict(result.geometry.components)
    assert tuple(geometries) == ROLES
    for role, geometry in geometries.items():
        assert (len(geometry.vertices), edge_count(geometry),
                len(geometry.faces)) == EXPECTED_TOPOLOGY[role], role
        assert float(geometry.volume_mm3) > 0
        assert len({name for name, *_ in geometry.vertices}) == len(
            geometry.vertices,
        )
    base, seat, outer, inner = (geometries[role] for role in (
        "base-plinth", "rail-seat", "outer-jaw", "inner-jaw",
    ))
    assert base.bounds_mm == (-18, -12, 0, 18, Fraction(35, 2), 3)
    assert base.volume_mm3 == Fraction(15842811, 5000)
    assert tuple(tuple(row[-2:]) for row in base.source_outline_mm) == tuple(
        (Fraction(x, 100), Fraction(y, 100)) for x, y in OUTLINE_HUNDREDTHS
    )
    assert {name: tuple(point) for name, *point in seat.vertices} == (
        EXPECTED_SEAT
    )
    assert seat.parameters.chair_half_width_mm == 14
    assert base.parameters.chair_half_width_mm == 18
    assert outer.bounds_mm == (-12, 9, 3, 12, 16, 24)
    assert tuple(name for name, _part in outer.parts) == (
        "body", "bevel-negative", "bevel-positive",
    )
    assert [(len(part.vertices), edge_count(part), len(part.faces))
            for _name, part in outer.parts] == [
                (32, 48, 18), (4, 6, 4), (4, 6, 4),
            ]
    # Independent linear side-plane proof: both bevel apexes lie outside
    # the jaw body; three declared parts must not become one healed solid.
    half_at_seat = Fraction(5) + Fraction(17, 4) * Fraction(16, 21)
    assert Fraction(9) - half_at_seat == Fraction(16, 21)
    sections = dict(inner.source_sections_mm)
    plinth = {name: (x, y, z)
              for name, x, y, z in sections["plinth"]}
    assert plinth["plinth-21"][1] == 8
    assert all(plinth["plinth-{:02d}".format(i)][1] <= 8
               for i in range(9, 34))
    assert plinth["plinth-01"][1] == 1
    assert inner.parameters.outer_top_half_width_mm == 7
    assert outer.parameters.top_half_width_mm == 5
    assert dict(result.geometry.landmarks)["rail-seat-centre"] == (0, 0, 8)
    for geometry in geometries.values():
        assert math.isfinite(float(geometry.volume_mm3))
    return geometries


def rejection_cases(record, manifest):
    """Invalid signed data must fail before exact geometry construction."""
    for name, role, purpose, value in (
        ("unequal-base-levels", "base-plinth", "edge_thickness_mm", "2"),
        ("unequal-seat-levels", "rail-seat", "plinth_thickness_mm", "4"),
        ("different-rail", "key", "rail_depth_mm", "25"),
        ("invalid-clip", "inner-jaw", "inner_outline_inset_mm", "9"),
        ("zero-factor", "inner-jaw", "plinth_fillet_factor", "0"),
        ("wrong-bevel-seat", "outer-jaw", "bevel_seat_half_width_mm", "10"),
    ):
        bad, related = copy.deepcopy((record, manifest))
        identity = "quantity:test:{}:{}".format(role, purpose)
        q = next(q for q in bad["definition"]["quantities"]
                 if q["quantity_id"] == identity)
        q["source_value"] = q["canonical_value"] = value
        yield name, resign_package(bad, related), related
    for name in ("mixed-family", "missing-role", "unsupported-schema",
                 "unresolved-lineage", "restricted-source", "wrong-status"):
        bad, related = copy.deepcopy((record, manifest))
        if name == "mixed-family":
            next(p for p in bad["definition"]["procedures"]
                 if p["rule_id"] == RULES["rail-seat"])["rule_id"] = (
                    "tracktemplate.chair.seat-reference.v1"
                )
        elif name == "missing-role":
            bad["definition"]["components"].pop()
        elif name == "unsupported-schema":
            bad["schema_version"] = 99
        elif name == "unresolved-lineage":
            bad["lineage"][0]["evidence_state"] = "unresolved"
        elif name == "restricted-source":
            related["dependencies"][0]["permissions"]["adaptation"] = (
                "restricted"
            )
        else:
            bad["package"]["project_status"] = "unknown"
        yield name, resign_package(bad, related), related


def validate_rejections(record, manifest, operation=None):
    """Preserve full signed inputs and structured failure diagnostics."""
    operation = operation or chair_research.prepare_chair_l1_assembly_research
    observed = {}
    for name, bad, related in rejection_cases(record, manifest):
        before = copy.deepcopy((bad, related))
        try:
            package, text = load_package(bad, related)
            operation(package, text)
        except definitions.ChairDefinitionError as error:
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
            observed[name] = error.code
        else:
            raise AssertionError(name + ": invalid L1 input accepted")
        assert (bad, related) == before
    return observed


def main():
    record, manifest = synthetic_l1_package_records()
    original = copy.deepcopy((record, manifest))
    package, text = load_package(record, manifest)
    result = chair_research.prepare_chair_l1_assembly_research(package, text)
    geometries = assert_geometry(result)
    assert result.package is package
    encoded = definitions.chair_definition_package_to_json(package)
    reopened = definitions.chair_definition_package_from_json(encoded, text)
    # Once inputs are loaded, construction does not access source files.
    with patch("builtins.open", side_effect=AssertionError("source access")):
        repeated = chair_research.prepare_chair_l1_assembly_research(
            reopened, text,
        )
    assert repeated == result
    assert definitions.chair_definition_package_to_json(reopened) == encoded
    old_record, old_manifest = synthetic_rail_package_records()
    old_package, old_text = load_package(old_record, old_manifest)
    old_result = chair_research.prepare_chair_assembly_research(
        old_package, old_text,
    )
    assert geometries["key"] == dict(old_result.geometry.components)["key"]
    for operation, selected, manifest_text in (
        (chair_research.prepare_chair_assembly_research, package, text),
        (chair_research.prepare_chair_l1_assembly_research,
         old_package, old_text),
    ):
        try:
            operation(selected, manifest_text)
        except definitions.ChairDefinitionError as error:
            assert error.code == "research-assembly-procedures"
        else:
            raise AssertionError("wrong complete family was accepted")
    rejections = validate_rejections(record, manifest)
    tampered = copy.deepcopy(record)
    tampered["definition"]["quantities"][0]["canonical_value"] = "999"
    try:
        load_package(tampered, manifest)
    except definitions.ChairDefinitionError:
        pass
    else:
        raise AssertionError("corrupt unsigned package accepted")
    assert (record, manifest) == original
    assert package.content_signature == reopened.content_signature
    print(json.dumps({
        "component_count": 5, "declared_solid_count": 7,
        "rejections": rejections, "source_free_regeneration": True,
        "shared_key_unchanged": True, "reference_only": True,
        "physical_fit_proved": False, "phase_exit_accepted": False,
    }, sort_keys=True))
    print(SENTINEL)


if __name__ == "__main__":
    main()
