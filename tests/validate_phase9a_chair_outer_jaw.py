#!/usr/bin/env python3
"""Prove the complete research outer jaw with invented non-S1 lengths.

The independent decimal section construction and exact synthetic volume
are test evidence only. They contain no measured or reference S1 values.
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
from tracktemplate.domain import chair_outer_jaw  # noqa: E402
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_base as base_tests  # noqa: E402
import validate_phase9a_chair_key as key_tests  # noqa: E402
import validate_phase9a_chair_seat as seat_tests  # noqa: E402


STAGES = ("top", "mid", "seat", "plinth")
PROFILE_FIELDS = (
    "depth_mm", "half_rib_space_mm", "rib_width_mm", "rib_depth_mm",
    "rib_radius_mm", "fillet_radius_mm",
)
# Artificial sections deliberately have four distinct half-rib spaces.
SYNTHETIC_PROFILES = (
    ("2", "3", "4", "2", "0.5", "0.25"),
    ("3", "3.5", "4.5", "2.5", "0.75", "0.5"),
    ("4", "4", "5", "3", "1", "0.75"),
    ("5", "4.5", "5.5", "3.5", "1.25", "1"),
)
SYNTHETIC_VALUES = {
    "top_height_mm": "20", "mid_height_mm": "14",
    "chair_half_width_mm": "14", "outer_corner_radius_mm": "2",
    "plinth_thickness_mm": "3", "seat_thickness_mm": "8",
    "outer_jaw_face_mm": "15", "rail_head_width_mm": "6",
    "rail_depth_mm": "24",
}
SYNTHETIC_VALUES.update({
    stage + "_" + field: value
    for stage, values in zip(STAGES, SYNTHETIC_PROFILES)
    for field, value in zip(PROFILE_FIELDS, values)
})
SYNTHETIC_BOUNDS = (-12, 12, 3, 12, Fraction(41, 2), 20)
# Coefficients of 1, sqrt(2), sqrt(3), sqrt(6), integrated independently
# from the synthetic cap areas, three bands and two 145/12 bevels.
SYNTHETIC_VOLUME_COEFFICIENTS = (
    Fraction(11521, 8), Fraction(-941, 32), Fraction(0), Fraction(941, 32),
)
SYNTHETIC_AREA_COEFFICIENTS = (
    (Fraction(345, 8), Fraction(-21, 32), 0, Fraction(21, 32)),
    (Fraction(275, 4), Fraction(-21, 16), 0, Fraction(21, 16)),
    (Fraction(793, 8), Fraction(-69, 32), 0, Fraction(69, 32)),
    (Fraction(537, 4), Fraction(-51, 16), 0, Fraction(51, 16)),
)


def synthetic_parameters():
    """Return artificial full-size lengths, not prototype facts."""
    return chair_outer_jaw.ChairOuterJawParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def synthetic_outer_jaw_package_records():
    """Return signed data with explicitly invented field sources."""
    record, manifest = seat_tests.synthetic_package_records()
    record = json.loads(json.dumps(record).replace(
        "synthetic-research-seat", "synthetic-research-outer-jaw",
    ))
    manifest = json.loads(json.dumps(manifest).replace(
        "synthetic-research-seat", "synthetic-research-outer-jaw",
    ))
    quantity_template = copy.deepcopy(record["definition"]["quantities"][0])
    lineage_template = copy.deepcopy(record["lineage"][0])
    dependency_template = copy.deepcopy(manifest["dependencies"][0])
    quantities, lineages, dependencies = [], [], []
    for name in sorted(("context", *SYNTHETIC_VALUES)):
        dependency_id = "dependency:test:" + name
        lineage_id = "lineage:test:" + name
        digest = hashlib.sha256(
            ("Invented outer-jaw source test double: " + name).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(dependency_template)
        dependency.update({
            "identifier": dependency_id,
            "name": "SYNTHETIC OUTER-JAW TEST DOUBLE: " + name,
            "source": {
                "creator_or_supplier": (
                    "TrackTemplate synthetic outer-jaw test"
                ),
                "locator": "synthetic-test-double://chair-outer-jaw/" + name,
                "acquired_on": "2026-10-04", "evidence_sha256": digest,
            },
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9a_chair_outer_jaw.py"
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
        "procedure_id": "procedure:test:1-outer-jaw",
        "rule_id": "tracktemplate.chair.outer-jaw-reference.v1",
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
        "output_ids": ["result:test:outer-jaw"],
    })
    definition["components"][0].update({
        "component_id": "component:test:outer-jaw", "role": "outer-jaw",
        "procedure_ids": [construction["procedure_id"]],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = [
        construction["procedure_id"]
    ]
    return seat_tests.resign_package(record, manifest), manifest


def prepare_records(record, manifest, operation=None):
    """Load signed data before the finite outer-jaw operation."""
    text = seat_tests.canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        seat_tests.canonical_json(record), text,
    )
    operation = operation or chair_research.prepare_chair_outer_jaw_research
    return operation(package, text)


def _decimal(value):
    """Evaluate exact values at the current decimal precision."""
    if hasattr(value, "coefficients"):
        return sum(_decimal(c) * decimal.Decimal(n).sqrt()
                   for c, n in zip(value.coefficients, (1, 2, 3, 6)))
    value = Fraction(value)
    return (decimal.Decimal(value.numerator)
            / decimal.Decimal(value.denominator))


def independent_section(profile):
    """Construct source XY with independent Decimal roots."""
    d, h, w, b, r, f = map(_decimal, profile)
    face = decimal.Decimal(15)
    two, six = decimal.Decimal(2).sqrt(), decimal.Decimal(6).sqrt()
    sines = (decimal.Decimal(0), (six - two) / 4, decimal.Decimal("0.5"),
             two / 2, decimal.Decimal(3).sqrt() / 2, (six + two) / 4,
             decimal.Decimal(1))
    points = [(-h - w, -face), (h + w, -face)]
    # Each quadrant is expressed separately to avoid using the domain's
    # rotation table or its stored section output as an oracle.
    rib_y, fillet_y = -face - d - b + r, -face - d - f
    for n in range(7):
        points.append((h + w - r + r * sines[6 - n], rib_y - r * sines[n]))
    for n in range(7):
        points.append((h + r - r * sines[n], rib_y - r * sines[6 - n]))
    for n in range(7):
        points.append((h - f + f * sines[6 - n], fillet_y + f * sines[n]))
    for n in range(7):
        points.append((-h + f - f * sines[n], fillet_y + f * sines[6 - n]))
    for n in range(7):
        points.append((-h - r + r * sines[6 - n], rib_y - r * sines[n]))
    for n in range(7):
        points.append((-h - w + r - r * sines[n], rib_y - r * sines[6 - n]))
    return tuple(points)


def _area(points):
    return abs(sum(a[0] * b[1] - a[1] * b[0]
                   for a, b in zip(points, points[1:] + points[:1]))) / 2


def validate_bevel_face_identities(geometry):
    """Keep source face meanings separate from solid topology."""
    # dxf_unit.pas 3425-3428 and 3436-3439 name all three triangles.
    # Source east becomes canonical negative under the frame.
    faces = dict(geometry.faces)
    mismatches = []
    for side, seat, front, outer in (
        ("negative", "seat-01", "plinth-01", "plinth-02"),
        ("positive", "seat-00", "plinth-00", "plinth-43"),
    ):
        tip = "bevel-" + side + "-tip"
        for label, expected in (
            ("visible", {tip, seat, outer}),
            ("base", {tip, front, outer}),
            ("rear", {tip, front, seat}),
        ):
            face_id = "bevel-" + side + "-" + label
            if set(faces[face_id]) != expected:
                mismatches.append(face_id)
    assert not mismatches, "Source bevel face IDs changed: " + str(mismatches)


def validate_analytical_geometry():
    """Prove every section point, volume and external closure."""
    parameters = synthetic_parameters()
    geometry = chair_outer_jaw.construct_chair_outer_jaw(parameters)
    points = {name: (x, y, z) for name, x, y, z in geometry.vertices}
    assert len(points) == len(geometry.vertices) == 178
    assert len(geometry.faces) == 140
    edges = key_tests._edges(geometry)
    assert len(edges) == 316 and len(points) - len(edges) + 140 == 2
    assert geometry.bounds_mm == SYNTHETIC_BOUNDS
    assert geometry.volume_mm3.coefficients == SYNTHETIC_VOLUME_COEFFICIENTS
    assert seat_tests.signed_boundary_volume(geometry) == geometry.volume_mm3
    assert tuple(stage for stage, _ring in geometry.source_sections_mm) == (
        STAGES
    )
    heights = (20, 14, 8, 3)
    with decimal.localcontext() as context:
        context.prec = 100
        allowance = decimal.Decimal("1e-80")  # Arithmetic check, not fit.
        for index, (stage, source) in enumerate(geometry.source_sections_mm):
            expected = independent_section(SYNTHETIC_PROFILES[index])
            assert len(source) == 44
            xy = tuple((x, y) for _name, x, y, _z in source)
            assert _area(xy).coefficients == tuple(
                map(Fraction, SYNTHETIC_AREA_COEFFICIENTS[index])
            )
            assert abs(_area(expected) - _decimal(_area(xy))) < allowance
            for n, (actual, expected_xy) in enumerate(zip(source, expected)):
                name, x, y, z = actual
                ex, ey = expected_xy
                assert name == "{}-{:02d}".format(stage, n)
                assert abs(_decimal(x) - ex) < allowance
                assert abs(_decimal(y) - ey) < allowance
                assert z == heights[index] - 32
                assert points[name] == (-x, -y - 3, heights[index])
                assert parameters.source_to_chair((x, y, z)) == points[name]
                px, py, pz = points[name]
                assert (-px, -py - 3, pz - 32) == (x, y, z)
    faces = dict(geometry.faces)
    assert len(faces["top-cap"]) == len(faces["plinth-cap"]) == 44
    assert sum(len(ids) == 3 for ids in faces.values()) == 8
    assert sum(len(ids) == 4 for ids in faces.values()) == 130
    for side, x, shared in (
        ("negative", -12, {"seat-01", "plinth-01", "plinth-02"}),
        ("positive", 12, {"seat-00", "plinth-00", "plinth-43"}),
    ):
        tip = "bevel-" + side + "-tip"
        assert points[tip] == (x, 12, 3)
        assert sum(tip in edge for edge in edges) == 3
        assert all(set(ids) != shared for ids in faces.values())
        incident = [ids for ids in faces.values() if tip in ids]
        assert len(incident) == 3
        assert set().union(*(set(ids) for ids in incident)) == shared | {tip}
    validate_bevel_face_identities(geometry)
    assert dict(geometry.landmarks) == {
        "base-origin": (0, 0, 0), "rail-seat-centre": (0, 0, 8),
        "rail-top-centre": (0, 0, 32), "gauge-face-at-seat": (0, -3, 8),
        "outer-jaw-top-front-centre": (0, 12, 20),
        "outer-jaw-mid-front-centre": (0, 12, 14),
        "outer-jaw-seat-front-centre": (0, 12, 8),
        "outer-jaw-plinth-front-centre": (0, 12, 3),
        "outer-jaw-negative-bevel-tip": (-12, 12, 3),
        "outer-jaw-positive-bevel-tip": (12, 12, 3),
    }
    return geometry


def validate_scaling_and_frame(geometry):
    """Keep units, frame changes and stage parameters distinct."""
    parameters = geometry.parameters
    for scale in (Fraction(1, 2), Fraction(7, 3)):
        scaled = chair_outer_jaw.construct_chair_outer_jaw(
            chair_outer_jaw.ChairOuterJawParameters(**{
                field.name: getattr(parameters, field.name) * scale
                for field in fields(parameters)
            })
        )
        assert scaled.faces == geometry.faces
        assert scaled.vertices == tuple(
            (name, x * scale, y * scale, z * scale)
            for name, x, y, z in geometry.vertices
        )
        assert scaled.volume_mm3 == geometry.volume_mm3 * scale ** 3
        assert scaled.bounds_mm == tuple(v * scale for v in geometry.bounds_mm)
        assert scaled.landmarks == tuple(
            (name, tuple(v * scale for v in point))
            for name, point in geometry.landmarks
        )
    deeper = chair_outer_jaw.construct_chair_outer_jaw(replace(
        parameters, rail_depth_mm=Fraction(25),
    ))
    assert deeper.vertices == geometry.vertices
    assert deeper.faces == geometry.faces
    assert deeper.volume_mm3 == geometry.volume_mm3
    assert dict(deeper.landmarks)["rail-top-centre"] == (0, 0, 33)
    shifted = chair_outer_jaw.construct_chair_outer_jaw(replace(
        parameters, rail_head_width_mm=Fraction(8),
    ))
    assert shifted.vertices == tuple((name, x, y - 1, z)
                                     for name, x, y, z in geometry.vertices)
    raised = chair_outer_jaw.construct_chair_outer_jaw(replace(
        parameters, top_height_mm=Fraction(21), mid_height_mm=Fraction(15),
        seat_thickness_mm=Fraction(9), plinth_thickness_mm=Fraction(4),
    ))
    assert raised.vertices == tuple((name, x, y, z + 1)
                                    for name, x, y, z in geometry.vertices)
    assert raised.volume_mm3 == shifted.volume_mm3 == geometry.volume_mm3
    changed = chair_outer_jaw.construct_chair_outer_jaw(replace(
        parameters, mid_half_rib_space_mm=Fraction(15, 4),
    ))
    for (name, *point), (changed_name, *other) in zip(
        geometry.vertices, changed.vertices,
    ):
        assert name == changed_name
        if not name.startswith("mid-"):
            assert point == other
    assert changed.volume_mm3 != geometry.volume_mm3


def validate_exact_arithmetic_and_refusals():
    """Refuse ambiguous signs and non-finite host conversion."""
    algebraic = chair_outer_jaw._Algebraic
    root2 = algebraic(tuple(map(Fraction, (0, 1, 0, 0))))
    root3 = algebraic(tuple(map(Fraction, (0, 0, 1, 0))))
    root6 = algebraic(tuple(map(Fraction, (0, 0, 0, 1))))
    assert root2 * root2 == 2 and root3 * root3 == 3 and root6 * root6 == 6
    assert root2 * root3 == root6
    assert root2 + root3 - root3 - root2 == 0
    assert (root2 + root3) / Fraction(7, 3) * Fraction(7, 3) == root2 + root3
    assert 1 < root2 < Fraction(3, 2) and abs(-root3) == root3
    lower, upper = root2.interval()
    assert lower * lower < 2 < upper * upper
    assert root2 - (lower - Fraction(1, 10 ** 59)) > 0
    assert root2 - (upper + Fraction(1, 10 ** 59)) < 0
    unresolved = root2 - (lower + upper) / 2
    for operation, error in (
        (lambda: unresolved.sign(), ValueError),
        (lambda: root2 / root3, TypeError),
        (lambda: root2 / 0, ZeroDivisionError),
        (lambda: float(root2 * 10 ** 400), (ValueError, OverflowError)),
        (lambda: algebraic((0, 1, 0, 0)), TypeError),
    ):
        try:
            operation()
        except error:
            pass
        else:
            raise AssertionError("Unsupported exact arithmetic accepted")
    with decimal.localcontext() as context:
        context.prec = 100
        assert float(root2) == float(decimal.Decimal(2).sqrt())
    original = synthetic_parameters()
    for name, value in (
        ("top_height_mm", Fraction(14)), ("mid_height_mm", Fraction(8)),
        ("seat_thickness_mm", Fraction(3)),
        ("plinth_thickness_mm", Fraction(0)),
        ("top_half_rib_space_mm", Fraction(1, 4)),
        ("mid_rib_width_mm", Fraction(3, 2)),
        ("seat_rib_depth_mm", Fraction(7, 4)),
        ("chair_half_width_mm", Fraction(12)),
        ("outer_corner_radius_mm", Fraction(14)),
        ("plinth_depth_mm", Fraction(-1)),
    ):
        try:
            chair_outer_jaw.construct_chair_outer_jaw(
                replace(original, **{name: value}),
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Invalid outer-jaw parameter accepted: " + name,
            )
    for value in (20, 20.0, True, float("nan"), float("inf")):
        try:
            replace(original, top_height_mm=value)
        except TypeError:
            pass
        else:
            raise AssertionError("Non-Fraction outer-jaw input accepted")
    try:
        chair_outer_jaw.construct_chair_outer_jaw({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated outer-jaw parameters accepted")


def validate_round_trip_and_context(geometry):
    """Preserve evidence and input; production remains blocked."""
    record, manifest = synthetic_outer_jaw_package_records()
    assert validate_document(manifest) == []
    original = copy.deepcopy((record, manifest))
    result = prepare_records(record, manifest)
    assert result.geometry == geometry
    assert (record, manifest) == original
    assert result.package.to_record() == record
    assert result.component_id == "component:test:outer-jaw"
    assert result.procedure_id == "procedure:test:1-outer-jaw"
    assert result.manifest_json == seat_tests.canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    encoded = definitions.chair_definition_package_to_json(result.package)
    reopened = definitions.chair_definition_package_from_json(
        encoded, json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_outer_jaw_research(
        reopened, json.dumps(manifest),
    ) == result
    detached = result.package.to_record()
    detached["definition"]["quantities"][0]["canonical_value"] = "999"
    assert result.package.to_record() == record
    status = definitions.chair_definition_package_status(
        result.package, result.manifest_json,
    )
    assert status["status"] == "blocked"
    for name in ("production_geometry_authorized",
                 "document_mutation_authorized",
                 "filesystem_mutation_authorized"):
        assert status[name] is False
    assert "phase9-production-admission-not-enabled" in status["findings"]
    for precision, rounding in ((2, decimal.ROUND_UP), (6, decimal.ROUND_DOWN),
                                (50, decimal.ROUND_HALF_EVEN)):
        with decimal.localcontext() as context:
            context.prec, context.rounding = precision, rounding
            context.traps[decimal.Inexact] = True
            context.traps[decimal.Rounded] = True
            context.clear_flags()
            assert prepare_records(record, manifest) == result
            assert not any(context.flags.values())


def _mutations():
    record, _manifest = synthetic_outer_jaw_package_records()
    quantities = record["definition"]["quantities"]
    height = next(i for i, q in enumerate(quantities)
                  if q["purpose"] == "top_height_mm")
    cases = []

    def add(name, expected, *changes):
        cases.append((name, expected, changes))

    for index in (0, 1):
        add("unknown procedure {}".format(index), "research-procedure-set",
            ("record", ("definition", "procedures", index, "rule_id"),
             "tracktemplate.test.unsupported-outer-jaw-variant.v1"))
    add("wrong role", "research-component-set",
        ("record", ("definition", "components", 0, "role"), "key"))
    add("height treated as ratio", "research-parameter-unit",
        ("record", ("definition", "quantities", height, "quantity_kind"),
         "dimensionless"),
        ("record", ("definition", "quantities", height, "source_unit"), "1"),
        ("record", ("definition", "quantities", height, "canonical_unit"),
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
    add("coincident section heights", "research-geometry-invalid",
        ("record", ("definition", "quantities", height, "source_value"),
         "14"),
        ("record", ("definition", "quantities", height, "canonical_value"),
         "14"))
    add("accepted package", "research-status-required",
        ("record", ("acceptance",), {
            "status": "accepted", "accepted_by": "Invented test decision",
            "accepted_on": "2026-10-04", "decision_reference": "test-only",
        }))
    add("source classification removed", "research-lineage-unresolved",
        ("record", ("lineage", 0, "classifications"), ["user_design"]),
        ("manifest", ("dependencies", 0, "classifications"), ["user_design"]))
    add("failed validation", "research-validation-blocked",
        ("record", ("validation", "status"), "failed"))
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
        raise AssertionError("Unsafe signed outer-jaw request accepted")
    assert (record, manifest) == before


def validate_semantic_rejections():
    """Check signed refusals and separation of all components."""
    cases = _mutations()
    for name, expected, changes in cases:
        record, manifest = synthetic_outer_jaw_package_records()
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
                      chair_research.prepare_chair_key_research,
                      chair_research.prepare_chair_base_research):
        record, manifest = synthetic_outer_jaw_package_records()
        _expect_rejection(
            record, manifest, "research-procedure-set", operation,
        )
    for builder in (seat_tests.synthetic_package_records,
                    key_tests.synthetic_key_package_records,
                    base_tests.synthetic_base_package_records):
        record, manifest = builder()
        _expect_rejection(record, manifest, "research-procedure-set")
    return len(cases) + 6


def main():
    """Run the new proof and unchanged seat, key and base floor."""
    validate_exact_arithmetic_and_refusals()
    geometry = validate_analytical_geometry()
    validate_scaling_and_frame(geometry)
    validate_round_trip_and_context(geometry)
    count = validate_semantic_rejections()
    base_tests.main()
    print("Phase 9A chair outer-jaw standalone validation passed "
          "({} signed rejection cases)".format(count))


if __name__ == "__main__":
    main()
