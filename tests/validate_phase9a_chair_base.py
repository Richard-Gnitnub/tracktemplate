#!/usr/bin/env python3
"""Prove the complete research base with invented, non-prototype inputs.

The small outline table below is independently calculated synthetic test
evidence. It is not S1 source data, canonical geometry or a physical chair.
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
from tracktemplate.domain import chair_base  # noqa: E402
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_key as key_tests  # noqa: E402
import validate_phase9a_chair_seat as seat_tests  # noqa: E402


SYNTHETIC_VALUES = {
    "chair_half_width_mm": "8",
    "chair_inner_length_mm": "10",
    "chair_outer_length_mm": "12",
    "inner_corner_radius_mm": "3",
    "outer_corner_radius_mm": "2",
    "plinth_side_inset_mm": "3",
    "plinth_end_inset_mm": "3",
    "edge_thickness_mm": "1",
    "plinth_thickness_mm": "3",
    "outline_midpoint_offset_mm": "2",
    "source_mark_quantum_mm": "0.01",
    "rail_head_width_mm": "6",
    "rail_depth_mm": "12",
    "seat_thickness_mm": "4",
}
# Independent nearest-grid results in hundredths of synthetic source mm.
# Corners use radii 3 and 2 with fixed 15-degree samples, not a smooth arc.
OUTLINE_HUNDREDTHS = (
    (-800, -1000), (-800, -200), (-800, 200), (-800, 700),
    (-790, 778), (-760, 850), (-712, 912), (-650, 960),
    (-578, 990), (-500, 1000), (500, 1000), (578, 990),
    (650, 960), (712, 912), (760, 850), (790, 778),
    (800, 700), (800, 200), (800, -200), (800, -1000),
    (793, -1052), (773, -1100), (741, -1141), (700, -1173),
    (652, -1193), (600, -1200), (-600, -1200), (-652, -1193),
    (-700, -1173), (-741, -1141), (-773, -1100), (-793, -1052),
)
SOURCE_OUTLINE = tuple(
    (Fraction(x, 100), Fraction(y, 100)) for x, y in OUTLINE_HUNDREDTHS
)
SOURCE_PLINTH = ((-5, -9), (-5, 7), (5, 7), (5, -9))
SYNTHETIC_BOUNDS = (-8, -13, 0, 8, 9, 3)
SYNTHETIC_AREA = Fraction(1730937, 5000)
SYNTHETIC_VOLUME = Fraction(2526937, 3000)


def synthetic_parameters():
    """Return exact artificial full-size lengths; none describes S1."""
    return chair_base.ChairBaseParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def synthetic_base_package_records():
    """Reuse neutral metadata with separately invented base field sources."""
    record, manifest = seat_tests.synthetic_package_records()
    record = json.loads(json.dumps(record).replace(
        "synthetic-research-seat", "synthetic-research-base",
    ))
    manifest = json.loads(json.dumps(manifest).replace(
        "synthetic-research-seat", "synthetic-research-base",
    ))
    quantity_template = copy.deepcopy(record["definition"]["quantities"][0])
    lineage_template = copy.deepcopy(record["lineage"][0])
    dependency_template = copy.deepcopy(manifest["dependencies"][0])
    quantities, lineages, dependencies = [], [], []
    for name in sorted(("context", *SYNTHETIC_VALUES)):
        dependency_id = "dependency:test:" + name
        lineage_id = "lineage:test:" + name
        digest = hashlib.sha256(
            ("Invented base source test double: " + name).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(dependency_template)
        dependency.update({
            "identifier": dependency_id,
            "name": "SYNTHETIC BASE TEST DOUBLE: " + name,
            "source": {
                "creator_or_supplier": "TrackTemplate synthetic base test",
                "locator": "synthetic-test-double://chair-base/" + name,
                "acquired_on": "2026-10-04", "evidence_sha256": digest,
            },
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9a_chair_base.py"
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
        quantity.update({
            "quantity_id": "quantity:test:" + name, "purpose": name,
            "quantity_kind": "length", "source_unit": "mm",
            "canonical_unit": "mm", "source_value": SYNTHETIC_VALUES[name],
            "canonical_value": SYNTHETIC_VALUES[name],
            "lineage_id": lineage_id,
        })
        quantities.append(quantity)
    record["lineage"] = lineages
    manifest["dependencies"] = dependencies
    definition = record["definition"]
    definition["quantities"] = quantities
    construction = definition["procedures"][1]
    construction.update({
        "procedure_id": "procedure:test:1-base",
        "rule_id": "tracktemplate.chair.base-reference.v1",
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
        "output_ids": ["result:test:base"],
    })
    definition["components"][0].update({
        "component_id": "component:test:base", "role": "base-plinth",
        "procedure_ids": [construction["procedure_id"]],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = [
        construction["procedure_id"]
    ]
    return seat_tests.resign_package(record, manifest), manifest


def prepare_records(record, manifest, operation=None):
    """Load signed neutral data before the finite base research operation."""
    text = seat_tests.canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        seat_tests.canonical_json(record), text,
    )
    operation = operation or chair_research.prepare_chair_base_research
    return operation(package, text)


def _projected_area(points):
    return abs(sum(
        a[0] * b[1] - a[1] * b[0]
        for a, b in zip(points, points[1:] + points[:1])
    )) / 2


def independent_source_roof():
    """Integrate the source patch partition over independently fixed points."""
    ring = tuple((x, y, Fraction(1)) for x, y in SOURCE_OUTLINE)
    a, b, c, d = tuple((Fraction(x), Fraction(y), Fraction(3))
                       for x, y in SOURCE_PLINTH)
    patches = []
    for start, corner in ((3, b), (10, c), (19, d), (26, a)):
        patches.extend((ring[i % 32], ring[(i + 1) % 32], corner)
                       for i in range(start, start + 6))
    patches.extend((
        (ring[0], ring[3], b, a), (ring[9], ring[10], c, b),
        (ring[16], ring[19], d, c), (ring[25], ring[26], a, d),
        (a, b, c, d),
    ))
    area, volume = Fraction(0), Fraction(0)
    for patch in patches:
        for index in range(1, len(patch) - 1):
            triangle = (patch[0], patch[index], patch[index + 1])
            projected = _projected_area(triangle)
            assert projected > 0
            area += projected
            volume += projected * sum(p[2] for p in triangle) / 3
    assert area == _projected_area(SOURCE_OUTLINE) == SYNTHETIC_AREA
    assert volume == SYNTHETIC_VOLUME
    return volume


def validate_analytical_geometry():
    """Prove complete source points, conforming closure and roof volume."""
    parameters = synthetic_parameters()
    geometry = chair_base.construct_chair_base(parameters)
    points = {name: (x, y, z) for name, x, y, z in geometry.vertices}
    assert len(points) == len(geometry.vertices) == 68
    assert geometry.source_outline_mm == tuple(
        ("p{:02d}".format(index), x, y)
        for index, (x, y) in enumerate(SOURCE_OUTLINE)
    )
    assert geometry.source_plinth_mm == tuple(
        (name, x, y) for name, (x, y) in zip("abcd", SOURCE_PLINTH)
    )
    margin_names = tuple(name + "." + axis
                         for name, _x, _y in geometry.source_outline_mm
                         + geometry.source_plinth_mm for axis in "xy")
    assert tuple(name for name, _margin in geometry.rounding_margins) == (
        margin_names
    )
    assert len(geometry.rounding_margins) == 72
    assert all(isinstance(margin, Fraction) and 0 < margin <= Fraction(1, 2)
               for _name, margin in geometry.rounding_margins)
    assert len({name for name, _ids in geometry.faces}) == 62
    edges = key_tests._edges(geometry)
    assert len(edges) == 128
    assert len(points) - len(edges) + len(geometry.faces) == 2
    expected = {(-x, -y - 3, z)
                for x, y in SOURCE_OUTLINE for z in (0, 1)}
    expected.update((-x, -y - 3, 3) for x, y in SOURCE_PLINTH)
    assert set(points.values()) == expected
    assert all(isinstance(v, Fraction)
               for point in points.values() for v in point)
    assert geometry.bounds_mm == SYNTHETIC_BOUNDS
    assert geometry.volume_mm3 == independent_source_roof()
    assert seat_tests.signed_boundary_volume(geometry) == SYNTHETIC_VOLUME
    assert dict(geometry.landmarks) == {
        "base-origin": (0, 0, 0), "rail-seat-centre": (0, 0, 4),
        "rail-top-centre": (0, 0, 16), "gauge-face-at-seat": (0, -3, 4),
        "plinth-top-centre": (0, -2, 3),
        "base-inner-end-midpoint": (0, -13, 1),
        "base-outer-end-midpoint": (0, 9, 1),
    }
    bottom_faces = [boundary for _name, boundary in geometry.faces
                    if all(points[v][2] == 0 for v in boundary)]
    assert len(bottom_faces) == 1 and len(bottom_faces[0]) == 32
    assert _projected_area(tuple(points[v] for v in bottom_faces[0])) == (
        SYNTHETIC_AREA
    )
    # Collinear side markers must also divide their adjacent roof wire.
    for sign in (-1, 1):
        for source_y in (-2, 2):
            corner = (sign * 8, -source_y - 3, 1)
            identity = next(name for name, point in points.items()
                            if point == corner)
            assert sum(identity in ids for _name, ids in geometry.faces) == 3
    for scale in (Fraction(1, 2), Fraction(7, 3)):
        scaled = chair_base.ChairBaseParameters(**{
            field.name: getattr(parameters, field.name) * scale
            for field in fields(parameters)
        })
        result = chair_base.construct_chair_base(scaled)
        assert result.faces == geometry.faces
        assert result.bounds_mm == tuple(v * scale for v in SYNTHETIC_BOUNDS)
        assert result.volume_mm3 == SYNTHETIC_VOLUME * scale ** 3
        assert seat_tests.signed_boundary_volume(result) == result.volume_mm3
        assert result.rounding_margins == geometry.rounding_margins
    for field in ("rail_depth_mm", "seat_thickness_mm"):
        moved = chair_base.construct_chair_base(replace(
            parameters, **{field: getattr(parameters, field) + 2},
        ))
        assert moved.vertices == geometry.vertices
        assert moved.volume_mm3 == geometry.volume_mm3
        assert dict(moved.landmarks)["rail-top-centre"][2] == 18
        assert dict(moved.landmarks)["base-origin"] == (0, 0, 0)
    shifted = chair_base.construct_chair_base(replace(
        parameters, rail_head_width_mm=Fraction(6003, 1000),
    ))
    assert shifted.vertices == tuple(
        (name, x, y - Fraction(3, 2000), z)
        for name, x, y, z in geometry.vertices
    )
    assert shifted.volume_mm3 == geometry.volume_mm3
    assert shifted.source_outline_mm == geometry.source_outline_mm
    assert shifted.source_plinth_mm == geometry.source_plinth_mm
    assert shifted.rounding_margins == geometry.rounding_margins
    assert any(y / parameters.source_mark_quantum_mm % 1
               for _name, _x, y, _z in shifted.vertices)
    marker_change = chair_base.construct_chair_base(replace(
        parameters, outline_midpoint_offset_mm=Fraction(1),
    ))
    assert marker_change.source_outline_mm != geometry.source_outline_mm
    assert marker_change.volume_mm3 == geometry.volume_mm3
    assert marker_change.faces == geometry.faces
    coarser_grid = chair_base.construct_chair_base(replace(
        parameters, source_mark_quantum_mm=Fraction(1, 50),
    ))
    assert coarser_grid.source_outline_mm != geometry.source_outline_mm
    assert coarser_grid.volume_mm3 != geometry.volume_mm3
    assert coarser_grid.volume_mm3 == seat_tests.signed_boundary_volume(
        coarser_grid
    )
    point = (Fraction(5), Fraction(7), Fraction(-16))
    assert parameters.source_to_chair(point) == (-5, -10, 0)
    return geometry


def validate_rounding_and_parameter_refusals():
    """Refuse ties and collapsed encoding instead of inventing an epsilon."""
    for number in (2, 3, 6):
        lower, upper = chair_base._root_interval(number)
        assert lower * lower < number < upper * upper
        assert 0 < upper - lower < Fraction(1, 10 ** 50)
    samples = chair_base._sines()
    assert len(samples) == 7
    for index, exact in ((0, Fraction(0)), (2, Fraction(1, 2)),
                         (6, Fraction(1))):
        assert samples[index] == (exact, exact)
    for index, millionths in ((1, 258819), (3, 707106),
                              (4, 866025), (5, 965925)):
        lower, upper = samples[index]
        assert Fraction(millionths, 10 ** 6) < lower < upper
        assert upper < Fraction(millionths + 1, 10 ** 6)
    quantum = Fraction(1, 100)
    for sign in (-1, 1):
        for source, expected in ((Fraction(1, 250), Fraction(0)),
                                 (Fraction(3, 500), quantum)):
            value, margin = chair_base._quantize(
                (sign * source,) * 2, quantum, "synthetic-coordinate",
            )
            assert value == sign * expected and margin == Fraction(1, 10)
        half = sign * quantum / 2
        for interval in ((half, half),
                         (half - Fraction(1, 10000),
                          half + Fraction(1, 10000))):
            try:
                chair_base._quantize(interval, quantum, "synthetic-tie")
            except ValueError as error:
                assert str(error) == (
                    "synthetic-tie: ambiguous source mark rounding"
                )
            else:
                raise AssertionError("Exact or unresolved half tie accepted")
        epsilon = Fraction(1, 10 ** 70)
        tiny = sorted((half + sign * epsilon, half + sign * 2 * epsilon))
        value, margin = chair_base._quantize(tiny, quantum, "inside-cell")
        assert value == sign * quantum
        assert margin == epsilon / quantum
    for limit, interior_sign in ((-(2 ** 30), 1), (2 ** 30 - 1, -1)):
        for interval in ((Fraction(limit),) * 2,
                         (Fraction(limit) - Fraction(1, 4),
                          Fraction(limit) + Fraction(1, 4))):
            try:
                chair_base._quantize(interval, Fraction(1), "source-limit")
            except ValueError as error:
                assert "source mark range would require clamping" in str(error)
            else:
                raise AssertionError("Source range limit silently clamped")
        inside = Fraction(limit) + interior_sign * Fraction(1, 4)
        observed = chair_base._quantize(
            (inside, inside), Fraction(1), "inside",
        )
        assert observed == (Fraction(limit), Fraction(1, 4))
    original = synthetic_parameters()
    for name, value in (
        ("chair_half_width_mm", Fraction(1601, 200)),
        ("chair_inner_length_mm", Fraction(2001, 200)),
        ("source_mark_quantum_mm", Fraction(13, 10)),
        ("source_mark_quantum_mm", Fraction(0)),
        ("plinth_thickness_mm", Fraction(1)),
        ("plinth_side_inset_mm", Fraction(8)),
        ("outline_midpoint_offset_mm", Fraction(20)),
        ("inner_corner_radius_mm", Fraction(0)),
    ):
        try:
            chair_base.construct_chair_base(replace(original, **{name: value}))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid or ambiguous base accepted: " + name)
    for value in (8, 8.0, True):
        try:
            replace(original, chair_half_width_mm=value)
        except TypeError:
            pass
        else:
            raise AssertionError("Non-Fraction base input accepted")
    try:
        chair_base.construct_chair_base({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated base parameters accepted")


def validate_round_trip_and_context():
    """Retain all evidence, forbid admission and ignore ambient precision."""
    record, manifest = synthetic_base_package_records()
    assert validate_document(manifest) == []
    original = copy.deepcopy((record, manifest))
    result = prepare_records(record, manifest)
    assert result.geometry == validate_analytical_geometry()
    assert (record, manifest) == original
    assert result.package.to_record() == record
    assert result.component_id == "component:test:base"
    assert result.procedure_id == "procedure:test:1-base"
    assert result.manifest_json == seat_tests.canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    serialized = definitions.chair_definition_package_to_json(result.package)
    reopened = definitions.chair_definition_package_from_json(
        serialized, json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_base_research(
        reopened, json.dumps(manifest),
    ) == result
    detached = result.package.to_record()
    detached["definition"]["quantities"][0]["canonical_value"] = "999"
    assert result.package.to_record() == record
    status = definitions.chair_definition_package_status(
        result.package, result.manifest_json,
    )
    assert status["status"] == "blocked"
    assert not status["production_geometry_authorized"]
    assert not status["document_mutation_authorized"]
    assert not status["filesystem_mutation_authorized"]
    assert "phase9-production-admission-not-enabled" in status["findings"]
    for precision, rounding in ((2, decimal.ROUND_UP),
                                (6, decimal.ROUND_DOWN),
                                (50, decimal.ROUND_HALF_EVEN)):
        with decimal.localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            context.traps[decimal.Inexact] = True
            context.traps[decimal.Rounded] = True
            context.clear_flags()
            assert prepare_records(record, manifest) == result
            assert not any(context.flags.values())


def _mutations():
    record, _manifest = synthetic_base_package_records()
    quantities = record["definition"]["quantities"]
    quantum = next(i for i, q in enumerate(quantities)
                   if q["purpose"] == "source_mark_quantum_mm")
    cases = []

    def add(name, expected, *changes):
        cases.append((name, expected, changes))

    for index in (0, 1):
        add("unknown procedure {}".format(index), "research-procedure-set",
            ("record", ("definition", "procedures", index, "rule_id"),
             "tracktemplate.test.unsupported-base-variant.v1"))
    add("wrong role", "research-component-set",
        ("record", ("definition", "components", 0, "role"), "key"))
    add("grid treated as ratio", "research-parameter-unit",
        ("record", ("definition", "quantities", quantum, "quantity_kind"),
         "dimensionless"),
        ("record", ("definition", "quantities", quantum, "source_unit"), "1"),
        ("record", ("definition", "quantities", quantum, "canonical_unit"),
         "1"))
    add("missing construction input", "research-parameter-set",
        ("record", ("definition", "procedures", 1,
                    "parameter_quantity_ids"),
         record["definition"]["procedures"][1]["parameter_quantity_ids"][1:]))
    alternate = copy.deepcopy(next(q for q in quantities
                                  if q["purpose"] == "rail_head_width_mm"))
    alternate["quantity_id"] = "quantity:test:alternate-head"
    extended = sorted(quantities + [alternate],
                      key=lambda quantity: quantity["quantity_id"])
    add("frame identity mismatch", "research-frame-inputs",
        ("record", ("definition", "quantities"), extended),
        ("record", ("definition", "procedures", 0, "parameter_quantity_ids"),
         [alternate["quantity_id"], "quantity:test:rail_depth_mm",
          "quantity:test:seat_thickness_mm"]))
    add("extra construction input", "research-parameter-set",
        ("record", ("definition", "quantities"), extended),
        ("record", ("definition", "procedures", 1, "parameter_quantity_ids"),
         record["definition"]["procedures"][1]["parameter_quantity_ids"]
         + [alternate["quantity_id"]]))
    add("unused quantity", "research-unused-quantity",
        ("record", ("definition", "quantities"), extended))
    add("left-handed frame", "unsupported-coordinate-frame",
        ("record", ("definition", "frame", "handedness"), "left"))
    for state in ("unresolved", "inferred", "comparison-only"):
        add("lineage " + state, "research-lineage-unresolved",
            ("record", ("lineage", 0, "evidence_state"), state))
    add("field hash mismatch", "research-source-hash-mismatch",
        ("record", ("lineage", 0, "source_file_sha256s"), ["0" * 64]))
    add("comparison-only dependency", "research-dependency-role",
        ("manifest", ("dependencies", 0, "role"), "comparison-only"))
    add("non-output dependency", "research-dependency-role",
        ("manifest", ("dependencies", 0, "output_affecting"), False))
    add("missing source locator", "research-source-identity",
        ("manifest", ("dependencies", 0, "source", "locator"), ""))
    for target, base in (("record", ("package",)),
                         ("manifest", ("dependencies", 0))):
        for permission in ("access", "adaptation"):
            add(target + " restricted " + permission,
                "research-use-restricted",
                (target, base + ("permissions", permission), "restricted"))
    add("publication use", "research-status-required",
        ("record", ("package", "intended_uses"), ["publication"]),
        ("manifest", ("intended_uses",), ["publication"]))
    add("cleared status", "research-status-required",
        ("record", ("package", "project_status"), "project-cleared"),
        ("manifest", ("project_status", "status"), "project-cleared"))
    add("manufacturing profile", "research-manufacturing-unsupported",
        ("record", ("manufacturing_profiles",), [{
            "profile_id": "manufacturing:test:unsupported",
            "description": "Artificial forbidden manufacturing profile.",
            "model_scale": "1", "quantities": [],
            "lineage_id": "lineage:test:context",
        }]))
    add("grid collapse", "research-geometry-invalid",
        ("record", ("definition", "quantities", quantum, "source_value"),
         "1.3"),
        ("record", ("definition", "quantities", quantum, "canonical_value"),
         "1.3"))
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
        raise AssertionError("Unsafe signed base request accepted")
    assert (record, manifest) == before


def validate_semantic_rejections():
    """Check signed finite-rule refusals and separation of all components."""
    cases = _mutations()
    for name, expected, changes in cases:
        record, manifest = synthetic_base_package_records()
        for target, path, value in changes:
            container = record if target == "record" else manifest
            for key in path[:-1]:
                container = container[key]
            container[path[-1]] = copy.deepcopy(value)
        try:
            _expect_rejection(record, manifest, expected)
        except AssertionError as error:
            raise AssertionError(name) from error
    for operation in (chair_research.prepare_chair_seat_research,
                      chair_research.prepare_chair_key_research):
        record, manifest = synthetic_base_package_records()
        _expect_rejection(
            record, manifest, "research-procedure-set", operation,
        )
    for builder in (seat_tests.synthetic_package_records,
                    key_tests.synthetic_key_package_records):
        record, manifest = builder()
        _expect_rejection(record, manifest, "research-procedure-set")
    return len(cases) + 4


def main():
    """Run base proofs and preserve the complete accepted seat/key floor."""
    validate_rounding_and_parameter_refusals()
    validate_round_trip_and_context()
    count = validate_semantic_rejections()
    key_tests.main()
    print("Phase 9A chair base standalone validation passed "
          "({} signed rejection cases)".format(count))


if __name__ == "__main__":
    main()
