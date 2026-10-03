#!/usr/bin/env python3
"""Prove reference-only key construction with invented, non-S1 inputs.

No value or source identity in this test describes a railway product.
Authentic frozen-source packages remain separate local evidence.
"""

import copy
from dataclasses import fields, replace
import decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from tracktemplate.domain.chair_key import (  # noqa: E402
    ChairKeyParameters,
    construct_chair_key,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_seat as seat_tests  # noqa: E402


SYNTHETIC_VALUES = {
    "key_length_mm": "20",
    "key_pad_length_mm": "6",
    "key_pad_taper_mm": "1",
    "key_deformation_mm": "0.25",
    "outer_jaw_face_mm": "10",
    "rail_head_width_mm": "6",
    "rail_web_width_mm": "2",
    "rail_web_top_depth_mm": "4",
    "rail_web_bottom_depth_mm": "7",
    "rail_fish_ratio": "2",
    "rail_depth_mm": "12",
    "seat_thickness_mm": "3",
}
SYNTHETIC_BOUNDS = (
    Fraction(-10), Fraction(1), Fraction(13, 2),
    Fraction(10), Fraction(29, 4), Fraction(25, 2),
)
SYNTHETIC_VOLUME = Fraction(3809, 6)


def synthetic_parameters():
    """Return artificial lengths in full-size mm and a dimensionless ratio."""
    return ChairKeyParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def synthetic_key_package_records():
    """Reuse the accepted neutral scaffold with explicit mock key evidence."""
    record, manifest = seat_tests.synthetic_package_records()
    # These identifiers distinguish synthetic packages, not prototype types.
    record = json.loads(json.dumps(record).replace(
        "synthetic-research-seat", "synthetic-research-key",
    ))
    manifest = json.loads(json.dumps(manifest).replace(
        "synthetic-research-seat", "synthetic-research-key",
    ))
    quantity_template = copy.deepcopy(record["definition"]["quantities"][0])
    lineage_template = copy.deepcopy(record["lineage"][0])
    dependency_template = copy.deepcopy(manifest["dependencies"][0])
    quantities, lineages, dependencies = [], [], []
    for name in sorted(("context", *SYNTHETIC_VALUES)):
        dependency_id = "dependency:test:" + name
        lineage_id = "lineage:test:" + name
        digest = hashlib.sha256(
            ("Invented key source test double: " + name).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(dependency_template)
        dependency.update({
            "identifier": dependency_id,
            "name": "SYNTHETIC KEY TEST DOUBLE: " + name,
            "source": {
                "creator_or_supplier": "TrackTemplate synthetic key test",
                "locator": "synthetic-test-double://chair-key/" + name,
                "acquired_on": "2026-10-03", "evidence_sha256": digest,
            },
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9a_chair_key.py"
        )
        lineage = copy.deepcopy(lineage_template)
        lineage.update({
            "lineage_id": lineage_id, "dependency_ids": [dependency_id],
            "source_file_sha256s": [digest],
        })
        dependencies.append(dependency)
        lineages.append(lineage)
        if name == "context":
            continue
        quantity = copy.deepcopy(quantity_template)
        ratio = name == "rail_fish_ratio"
        quantity.update({
            "quantity_id": "quantity:test:" + name, "purpose": name,
            "quantity_kind": "dimensionless" if ratio else "length",
            "source_value": SYNTHETIC_VALUES[name],
            "canonical_value": SYNTHETIC_VALUES[name],
            "source_unit": "1" if ratio else "mm",
            "canonical_unit": "1" if ratio else "mm",
            "lineage_id": lineage_id,
        })
        quantities.append(quantity)
    record["lineage"] = lineages
    manifest["dependencies"] = dependencies
    definition = record["definition"]
    definition["quantities"] = quantities
    frame, key = definition["procedures"]
    key.update({
        "procedure_id": "procedure:test:1-key",
        "rule_id": "tracktemplate.chair.key-reference.v1",
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
        "output_ids": ["result:test:key"],
    })
    frame["parameter_quantity_ids"] = [
        "quantity:test:" + name for name in (
            "rail_head_width_mm", "rail_depth_mm", "seat_thickness_mm",
        )
    ]
    definition["components"][0].update({
        "component_id": "component:test:key", "role": "key",
        "procedure_ids": [key["procedure_id"]],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = [key["procedure_id"]]
    return seat_tests.resign_package(record, manifest), manifest


def prepare_records(record, manifest, operation=None):
    """Exercise the signed neutral loader before the finite key operation."""
    text = seat_tests.canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        seat_tests.canonical_json(record), text,
    )
    operation = operation or chair_research.prepare_chair_key_research
    return operation(package, text)


def _edges(geometry):
    directed = []
    for _name, boundary in geometry.faces:
        directed.extend(zip(boundary, boundary[1:] + boundary[:1]))
    assert all(directed.count(edge) == 1 for edge in directed)
    assert all(directed.count((b, a)) == 1 for a, b in directed)
    return {frozenset(edge) for edge in directed}


def validate_analytical_geometry():
    """Check dimensions, closure and source-diagonal geometry independently."""
    parameters = synthetic_parameters()
    geometry = construct_chair_key(parameters)
    points = {name: (x, y, z) for name, x, y, z in geometry.vertices}
    assert len(points) == len(geometry.vertices) == 20
    assert len({name for name, _ids in geometry.faces}) == 18
    edges = _edges(geometry)
    assert len(edges) == 36
    assert len(points) - len(edges) + len(geometry.faces) == 2
    assert all(isinstance(value, Fraction)
               for point in points.values() for value in point)
    assert geometry.bounds_mm == SYNTHETIC_BOUNDS
    assert geometry.volume_mm3 == SYNTHETIC_VOLUME
    assert dict(geometry.landmarks) == {
        "base-origin": (0, 0, 0),
        "rail-seat-centre": (0, 0, 3),
        "rail-top-centre": (0, 0, 15),
        "gauge-face-at-seat": (0, -3, 3),
        "key-apex-centre": (0, 3, Fraction(25, 2)),
        "key-toe-centre": (0, 3, Fraction(13, 2)),
        "key-pad-centre": (0, 1, Fraction(19, 2)),
        "key-back-centre": (0, Fraction(29, 4), 9),
        "outer-jaw-datum": (0, 7, 9),
    }
    # Exact transverse-polygon integration independently gives 3809/6.
    # The separate tetrahedral boundary integral must agree with that value.
    assert seat_tests.signed_boundary_volume(geometry) == SYNTHETIC_VOLUME
    expected_points = set()
    for x, web_y in ((-10, 2), (-3, 1), (3, 1), (10, 2)):
        expected_points.update((
            (x, 3, Fraction(25, 2)), (x, 3, Fraction(13, 2)),
            (x, web_y, Fraction(23, 2)), (x, web_y, Fraction(15, 2)),
        ))
        if abs(x) == 10:
            expected_points.update((
                (x, Fraction(29, 4), Fraction(23, 2)),
                (x, Fraction(29, 4), Fraction(13, 2)),
            ))
    assert set(points.values()) == expected_points
    coordinate_edges = {
        frozenset((points[a], points[b])) for a, b in edges
    }
    # The tapered top and bottom patches are non-planar. Source quads use
    # their first-to-third diagonal, not the opposite triangulation.
    for sign in (-1, 1):
        top_end = (sign * 10, 3, Fraction(25, 2))
        top_pad = (sign * 3, 1, Fraction(23, 2))
        bottom_end = (sign * 10, 3, Fraction(13, 2))
        bottom_pad = (sign * 3, 1, Fraction(15, 2))
        assert frozenset((top_end, top_pad)) in coordinate_edges
        assert frozenset((bottom_end, bottom_pad)) in coordinate_edges
        opposite_top = frozenset(((sign * 3, 3, Fraction(25, 2)),
                                  (sign * 10, 2, Fraction(23, 2))))
        opposite_bottom = frozenset(((sign * 3, 3, Fraction(13, 2)),
                                     (sign * 10, 2, Fraction(15, 2))))
        assert opposite_top not in coordinate_edges
        assert opposite_bottom not in coordinate_edges
    assert {(-x, y, z) for x, y, z in points.values()} == set(points.values())
    translated = replace(geometry, vertices=tuple(
        (name, x + 17, y - 11, z + 23)
        for name, x, y, z in geometry.vertices
    ))
    assert seat_tests.signed_boundary_volume(translated) == SYNTHETIC_VOLUME
    for scale in (Fraction(1, 8), Fraction(7, 3)):
        scaled = ChairKeyParameters(**{
            item.name: getattr(parameters, item.name) * (
                1 if item.name == "rail_fish_ratio" else scale
            ) for item in fields(parameters)
        })
        result = construct_chair_key(scaled)
        assert result.bounds_mm == tuple(q * scale for q in SYNTHETIC_BOUNDS)
        assert result.volume_mm3 == SYNTHETIC_VOLUME * scale ** 3
        assert result.faces == geometry.faces
        assert tuple(row[0] for row in result.vertices) == tuple(points)
        assert seat_tests.signed_boundary_volume(result) == result.volume_mm3
    for name in ("rail_depth_mm", "seat_thickness_mm"):
        raised = construct_chair_key(replace(
            parameters, **{name: getattr(parameters, name) + 2},
        ))
        assert raised.vertices == tuple(
            (identity, x, y, z + 2)
            for identity, x, y, z in geometry.vertices
        )
        assert raised.volume_mm3 == geometry.volume_mm3
    for name, value, volume_delta in (
        ("key_pad_length_mm", Fraction(8), Fraction(14, 3)),
        ("key_pad_taper_mm", Fraction(1, 2), Fraction(49, 3)),
        ("key_deformation_mm", Fraction(1, 2), Fraction(55, 2)),
    ):
        changed = construct_chair_key(replace(parameters, **{name: value}))
        assert changed.vertices != geometry.vertices
        assert changed.volume_mm3 - geometry.volume_mm3 == volume_delta
        assert changed.faces == geometry.faces
        assert tuple(dict(changed.landmarks)) == tuple(
            dict(geometry.landmarks)
        )
        assert seat_tests.signed_boundary_volume(changed) == changed.volume_mm3
    point = (Fraction(5), Fraction(7), Fraction(-12))
    assert parameters.source_to_chair(point) == (-5, -10, 3)
    no_overlap = construct_chair_key(replace(
        parameters, key_deformation_mm=Fraction(0),
    ))
    assert no_overlap.volume_mm3 == SYNTHETIC_VOLUME - Fraction(55, 2)
    return geometry


def validate_parameter_domain():
    """Refuse mathematical degeneracy without inventing physical limits."""
    original = synthetic_parameters()
    for name, value in (
        ("key_length_mm", Fraction(0)),
        ("key_pad_length_mm", Fraction(20)),
        ("key_pad_taper_mm", Fraction(0)),
        ("key_pad_taper_mm", Fraction(2)),
        ("key_deformation_mm", Fraction(-1, 4)),
        ("outer_jaw_face_mm", Fraction(6)),
        ("rail_web_bottom_depth_mm", Fraction(4)),
        ("rail_web_top_depth_mm", Fraction(3, 2)),
        ("rail_depth_mm", Fraction(17, 2)),
        ("rail_fish_ratio", Fraction(0)),
        ("rail_head_width_mm", Fraction(2)),
    ):
        try:
            construct_chair_key(replace(original, **{name: value}))
        except ValueError:
            pass
        else:
            raise AssertionError("Degenerate key accepted: " + name)
    for value in (12, 12.0, True):
        try:
            replace(original, rail_depth_mm=value)
        except TypeError:
            pass
        else:
            raise AssertionError("Non-Fraction key input accepted")
    try:
        construct_chair_key({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated key parameters accepted")


def validate_round_trip_and_context():
    """Retain complete provenance while production admission stays blocked."""
    record, manifest = synthetic_key_package_records()
    assert validate_document(manifest) == []
    before = copy.deepcopy((record, manifest))
    result = prepare_records(record, manifest)
    assert result.geometry == validate_analytical_geometry()
    assert (record, manifest) == before
    assert result.package.to_record() == record
    assert result.component_id == "component:test:key"
    assert result.procedure_id == "procedure:test:1-key"
    assert result.manifest_json == seat_tests.canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    text = definitions.chair_definition_package_to_json(result.package)
    reopened = definitions.chair_definition_package_from_json(
        text, json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_key_research(
        reopened, json.dumps(manifest),
    ) == result
    status = definitions.chair_definition_package_status(
        result.package, result.manifest_json,
    )
    assert status["status"] == "blocked"
    assert not status["production_geometry_authorized"]
    assert not status["document_mutation_authorized"]
    assert not status["filesystem_mutation_authorized"]
    assert "phase9-production-admission-not-enabled" in status["findings"]
    supporting_record = copy.deepcopy(record)
    ancestor = copy.deepcopy(record["definition"]["quantities"][0])
    ancestor.update({
        "quantity_id": "quantity:test:ancestor",
        "purpose": "synthetic-key-source-ancestry",
        "lineage_id": "lineage:test:context",
    })
    tolerance = copy.deepcopy(ancestor)
    tolerance.update({
        "quantity_id": "quantity:test:tolerance",
        "purpose": "synthetic-key-validation-tolerance",
    })
    supporting_record["definition"]["quantities"].extend((ancestor, tolerance))
    supporting_record["definition"]["quantities"].sort(
        key=lambda quantity: quantity["quantity_id"],
    )
    lineage_id = record["definition"]["quantities"][0]["lineage_id"]
    lineage = next(item for item in supporting_record["lineage"]
                   if item["lineage_id"] == lineage_id)
    lineage.update({
        "evidence_state": "derived", "derivation": {
            "rule_id": "tracktemplate.test.synthetic-key-identity.v1",
            "input_ids": [ancestor["quantity_id"]],
        },
    })
    supporting_record["validation"]["tolerance_quantity_ids"] = [
        tolerance["quantity_id"]
    ]
    seat_tests.resign_package(supporting_record, manifest)
    supporting = prepare_records(supporting_record, manifest)
    assert supporting.geometry == result.geometry
    assert supporting.package.to_record() == supporting_record
    scale = Fraction(123456789, 10 ** 9)
    with decimal.localcontext() as context:
        context.prec = 50
        for q in record["definition"]["quantities"]:
            if q["purpose"] == "rail_fish_ratio":
                continue
            value = format(decimal.Decimal(q["source_value"])
                           * decimal.Decimal("0.123456789"), "f")
            q.update({"source_value": value, "canonical_value": value})
    seat_tests.resign_package(record, manifest)
    baseline = prepare_records(record, manifest)
    assert baseline.geometry.volume_mm3 == SYNTHETIC_VOLUME * scale ** 3
    for precision in (2, 6, 50):
        with decimal.localcontext() as context:
            context.prec = precision
            context.traps[decimal.Inexact] = True
            context.traps[decimal.Rounded] = True
            context.clear_flags()
            assert prepare_records(record, manifest) == baseline
            assert not any(context.flags.values())


def _mutations():
    record, _manifest = synthetic_key_package_records()
    quantities = record["definition"]["quantities"]
    ratio = next(i for i, q in enumerate(quantities)
                 if q["purpose"] == "rail_fish_ratio")
    length = next(i for i, q in enumerate(quantities)
                  if q["purpose"] == "key_length_mm")
    cases = []

    def add(name, expected, *changes):
        cases.append((name, expected, changes))

    for index in (0, 1):
        add("unknown procedure {}".format(index), "research-procedure-set",
            ("record", ("definition", "procedures", index, "rule_id"),
             "tracktemplate.test.unsupported-key-variant.v1"))
    add("wrong component", "research-component-set",
        ("record", ("definition", "components", 0, "role"), "rail-seat"))
    add("ratio as length", "research-parameter-unit",
        ("record", ("definition", "quantities", ratio, "quantity_kind"),
         "length"),
        ("record", ("definition", "quantities", ratio, "source_unit"), "mm"),
        ("record", ("definition", "quantities", ratio, "canonical_unit"),
         "mm"))
    add("length as ratio", "research-parameter-unit",
        ("record", ("definition", "quantities", length, "quantity_kind"),
         "dimensionless"),
        ("record", ("definition", "quantities", length, "source_unit"), "1"),
        ("record", ("definition", "quantities", length, "canonical_unit"),
         "1"))
    add("missing rule input", "research-parameter-set",
        ("record", ("definition", "procedures", 1,
                    "parameter_quantity_ids"),
         record["definition"]["procedures"][1]["parameter_quantity_ids"][1:]))
    alternate = copy.deepcopy(next(q for q in quantities
                                  if q["purpose"] == "rail_head_width_mm"))
    alternate["quantity_id"] = "quantity:test:alternate-head"
    extended = sorted(quantities + [alternate],
                      key=lambda quantity: quantity["quantity_id"])
    add("different frame input identity", "research-frame-inputs",
        ("record", ("definition", "quantities"), extended),
        ("record", ("definition", "procedures", 0, "parameter_quantity_ids"),
         [alternate["quantity_id"], "quantity:test:rail_depth_mm",
          "quantity:test:seat_thickness_mm"]))
    add("extra rule input", "research-parameter-set",
        ("record", ("definition", "quantities"), extended),
        ("record", ("definition", "procedures", 1, "parameter_quantity_ids"),
         record["definition"]["procedures"][1]["parameter_quantity_ids"]
         + [alternate["quantity_id"]]))
    add("unused extra quantity", "research-unused-quantity",
        ("record", ("definition", "quantities"), extended))
    add("unsupported frame", "unsupported-coordinate-frame",
        ("record", ("definition", "frame", "handedness"), "left"))
    for state in ("unresolved", "inferred", "comparison-only"):
        add("lineage " + state, "research-lineage-unresolved",
            ("record", ("lineage", 0, "evidence_state"), state))
    add("source hash changed", "research-source-hash-mismatch",
        ("record", ("lineage", 0, "source_file_sha256s"), ["0" * 64]))
    add("source becomes comparison", "research-dependency-role",
        ("manifest", ("dependencies", 0, "role"), "comparison-only"))
    add("source non-output-affecting", "research-dependency-role",
        ("manifest", ("dependencies", 0, "output_affecting"), False))
    add("source locator removed", "research-source-identity",
        ("manifest", ("dependencies", 0, "source", "locator"), ""))
    for target, base in (("record", ("package",)),
                         ("manifest", ("dependencies", 0))):
        for permission in ("access", "adaptation"):
            add(target + " restricted " + permission,
                "research-use-restricted",
                (target, base + ("permissions", permission), "restricted"))
    add("publication requested", "research-status-required",
        ("record", ("package", "intended_uses"), ["publication"]),
        ("manifest", ("intended_uses",), ["publication"]))
    add("package marked cleared", "research-status-required",
        ("record", ("package", "project_status"), "project-cleared"),
        ("manifest", ("project_status", "status"), "project-cleared"))
    add("manufacturing enabled", "research-manufacturing-unsupported",
        ("record", ("manufacturing_profiles",), [{
            "profile_id": "manufacturing:test:unsupported",
            "description": "Artificial forbidden manufacturing profile.",
            "model_scale": "1", "quantities": [],
            "lineage_id": "lineage:test:context",
        }]))
    add("zero ratio", "research-geometry-invalid",
        ("record", ("definition", "quantities", ratio, "source_value"), "0"),
        ("record", ("definition", "quantities", ratio, "canonical_value"),
         "0"))
    return cases


def _expect_rejection(record, manifest, expected, operation=None):
    seat_tests.resign_package(record, manifest)
    before = copy.deepcopy((record, manifest))
    try:
        prepare_records(record, manifest, operation)
    except definitions.ChairDefinitionError as error:
        assert error.code == expected, error.diagnostic()
        diagnostic = error.diagnostic()
        assert diagnostic["recoverable"] is True
        assert diagnostic["document_mutation"] is False
        assert diagnostic["filesystem_mutation"] is False
    else:
        raise AssertionError("Unsafe signed key request accepted")
    assert (record, manifest) == before


def validate_semantic_rejections():
    """Re-sign semantic mutations so signature checks cannot mask them."""
    cases = _mutations()
    for name, expected, changes in cases:
        record, manifest = synthetic_key_package_records()
        for target, path, value in changes:
            container = record if target == "record" else manifest
            for key in path[:-1]:
                container = container[key]
            container[path[-1]] = copy.deepcopy(value)
        try:
            _expect_rejection(record, manifest, expected)
        except AssertionError as error:
            raise AssertionError(name) from error
    record, manifest = synthetic_key_package_records()
    _expect_rejection(record, manifest, "research-procedure-set",
                      chair_research.prepare_chair_seat_research)
    record, manifest = seat_tests.synthetic_package_records()
    _expect_rejection(record, manifest, "research-procedure-set")
    return len(cases) + 2


def main():
    """Run key checks plus the unchanged accepted seat regression proof."""
    validate_parameter_domain()
    validate_round_trip_and_context()
    count = validate_semantic_rejections()
    seat_tests.main()
    print("Phase 9A chair key standalone validation passed "
          "({} signed rejection cases)".format(count))


if __name__ == "__main__":
    main()
