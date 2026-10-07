#!/usr/bin/env python3
"""Prove the complete research inner jaw with invented non-S1 lengths.

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
from tracktemplate.domain import chair_inner_jaw  # noqa: E402
from tools.validate_dependency_manifest import validate_document  # noqa: E402
import validate_phase9a_chair_base as base_tests  # noqa: E402
import validate_phase9a_chair_key as key_tests  # noqa: E402
import validate_phase9a_chair_seat as seat_tests  # noqa: E402


import validate_phase9a_chair_outer_jaw as outer_tests  # noqa: E402


STAGES = ("stand", "upper-mid", "lower-mid", "seat", "plinth")
SYNTHETIC_VALUES = {
    "chair_half_width_mm": "14", "outer_corner_radius_mm": "2",
    "plinth_thickness_mm": "3", "seat_thickness_mm": "8",
    "rail_head_width_mm": "6", "rail_foot_width_mm": "8",
    "rail_web_width_mm": "2", "rail_depth_mm": "24",
    "rail_web_face_top_from_rail_bottom_mm": "18",
    "rail_web_face_bottom_from_rail_bottom_mm": "10",
    "rail_foot_depth_mm": "5",
    "outer_top_half_width_mm": "4", "outer_top_height_mm": "24",
    "outer_mid_half_width_mm": "5", "outer_mid_height_mm": "18",
    "outer_seat_half_width_mm": "7", "outer_plinth_half_width_mm": "8",
    "top_to_mid_side_slope": "8", "mid_to_seat_side_slope": "5",
    "grip_width_reference_height_mm": "25", "stand_height_mm": "22",
    "lower_mid_rib_radius_mm": "2", "insert_depth_mm": "0.5",
    "upper_mid_depth_mm": "3", "lower_mid_depth_mm": "4",
    "seat_depth_mm": "5", "plinth_depth_mm": "7",
    "stand_fillet_radius_mm": "0.25", "stand_corner_radius_mm": "0.125",
    "upper_mid_fillet_radius_mm": "0.5",
    "upper_mid_corner_radius_mm": "0.25",
    "lower_mid_fillet_radius_mm": "0.75",
    "lower_mid_corner_radius_mm": "0.5",
    "seat_fillet_radius_mm": "1", "seat_corner_radius_mm": "0.75",
    "plinth_fillet_radius_mm": "1.25", "plinth_corner_radius_mm": "1",
}
SLOPES = ("top_to_mid_side_slope", "mid_to_seat_side_slope")
# Independently derived synthetic (width, rib, fillet, corner, depth).
SYNTHETIC_PROFILES = (
    ("4.25", "0.25", "0.25", "0.125", "0"),
    ("4.75", "0.75", "0.5", "0.25", "3"),
    ("6", "2", "0.75", "0.5", "4"),
    ("7", "3", "1", "0.75", "5"),
    ("8", "4", "1.25", "1", "7"),
)
SYNTHETIC_HEIGHTS = (22, 18, 13, 8, 3)
SYNTHETIC_BOUNDS = (-12, Fraction(-61, 4), 3, 12, -1, 26)
# Independent volume: body, grip 259 and two bevels of 50/3 mm³.
# Coefficients multiply 1, sqrt(2), sqrt(3), sqrt(6), respectively.
SYNTHETIC_VOLUME_COEFFICIENTS = (
    Fraction(55343, 48), Fraction(-2361, 16), Fraction(0), Fraction(2361, 16),
)


def synthetic_parameters():
    """Return artificial full-size lengths, not prototype facts."""
    return chair_inner_jaw.ChairInnerJawParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def synthetic_inner_jaw_package_records():
    """Return signed data with explicitly invented field sources."""
    record, manifest = seat_tests.synthetic_package_records()
    record = json.loads(json.dumps(record).replace(
        "synthetic-research-seat", "synthetic-research-inner-jaw",
    ))
    manifest = json.loads(json.dumps(manifest).replace(
        "synthetic-research-seat", "synthetic-research-inner-jaw",
    ))
    quantity_template = copy.deepcopy(record["definition"]["quantities"][0])
    lineage_template = copy.deepcopy(record["lineage"][0])
    dependency_template = copy.deepcopy(manifest["dependencies"][0])
    quantities, lineages, dependencies = [], [], []
    for name in sorted(("context", *SYNTHETIC_VALUES)):
        dependency_id = "dependency:test:" + name
        lineage_id = "lineage:test:" + name
        digest = hashlib.sha256(
            ("Invented inner-jaw source test double: " + name).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(dependency_template)
        dependency.update({
            "identifier": dependency_id,
            "name": "SYNTHETIC INNER-JAW TEST DOUBLE: " + name,
            "source": {
                "creator_or_supplier": (
                    "TrackTemplate synthetic inner-jaw test"
                ),
                "locator": "synthetic-test-double://chair-inner-jaw/" + name,
                "acquired_on": "2026-10-04", "evidence_sha256": digest,
            },
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9a_chair_inner_jaw.py"
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
        if name in SLOPES:
            quantity.update({"quantity_kind": "dimensionless",
                             "source_unit": "1", "canonical_unit": "1"})
        quantities.append(quantity)
    record["lineage"] = lineages
    manifest["dependencies"] = dependencies
    definition = record["definition"]
    definition["quantities"] = quantities
    construction = definition["procedures"][1]
    construction.update({
        "procedure_id": "procedure:test:1-inner-jaw",
        "rule_id": "tracktemplate.chair.inner-jaw-reference.v1",
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
        "output_ids": ["result:test:inner-jaw"],
    })
    definition["components"][0].update({
        "component_id": "component:test:inner-jaw", "role": "inner-jaw",
        "procedure_ids": [construction["procedure_id"]],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = [
        construction["procedure_id"]
    ]
    return seat_tests.resign_package(record, manifest), manifest


def prepare_records(record, manifest, operation=None):
    """Load signed data before the finite inner-jaw operation."""
    text = seat_tests.canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        seat_tests.canonical_json(record), text,
    )
    operation = operation or chair_research.prepare_chair_inner_jaw_research
    return operation(package, text)


def _decimal(value):
    """Evaluate exact values at the current decimal precision."""
    if hasattr(value, "coefficients"):
        return sum(_decimal(c) * decimal.Decimal(n).sqrt()
                   for c, n in zip(value.coefficients, (1, 2, 3, 6)))
    value = Fraction(value)
    return (decimal.Decimal(value.numerator)
            / decimal.Decimal(value.denominator))


def independent_geometry():
    """Integrate invented sections with Decimal roots."""
    # This oracle imports no candidate arithmetic or geometry helper.
    two, six = decimal.Decimal(2).sqrt(), decimal.Decimal(6).sqrt()
    sine = (decimal.Decimal(0), (six - two) / 4, decimal.Decimal("0.5"),
            two / 2, decimal.Decimal(3).sqrt() / 2, (six + two) / 4,
            decimal.Decimal(1))
    rings, vertices = {}, {}
    profiles = [tuple(map(decimal.Decimal, row))
                for row in SYNTHETIC_PROFILES]
    for stage, height, profile in zip(STAGES, SYNTHETIC_HEIGHTS, profiles):
        a, r, f, c, d = profile
        points = {0: (-a, decimal.Decimal(1)), 1: (a, decimal.Decimal(1))}
        for n in range(7):
            s, k = sine[n], sine[6 - n]
            points[2 + n] = (a - c + c * k, d - c + c * s)
            points[9 + n] = (r + f - f * s, d + f - f * k)
            points[15 + n] = (r * k, d + f + r * s)
            points[21 + n] = (-r * s, d + f + r * k)
            points[27 + n] = (-r - f + f * k, d + f - f * s)
            points[34 + n] = (-a + c - c * s, d - c + c * k)
        if stage == "stand":
            points = {i: (x, decimal.Decimal(1))
                      for i, (x, _y) in points.items()}
        ring = tuple(points[i] for i in range(41))
        rings[stage] = ring
        for i, (x, y) in enumerate(ring):
            if stage == "stand" and i in (2, 40):
                continue
            vertices["{}-{:02d}".format(stage, i)] = (-x, -y - 3, height)
    for side, sign in (("negative", -1), ("positive", 1)):
        vertices["bevel-" + side + "-tip"] = (sign * 12, -4, 3)
        for name, x, y, z in (
            ("top-web", decimal.Decimal("3.875"), -1, 26),
            ("top-front", decimal.Decimal("3.875"),
             decimal.Decimal("-2.5"), 26),
            ("stand-web", decimal.Decimal("4.25"), -1, 22),
            ("upper-mid-web", decimal.Decimal("4.75"), -1, 18),
        ):
            vertices["grip-" + side + "-" + name] = (sign * x, y, z)

    def section_area(profile):
        a, r, f, c, d = profile
        return (2 * a * (d - 1) + 2 * (f * f - c * c) * (1 - 3 * sine[1])
                + 2 * r * f + 6 * r * r * sine[1])

    first_cut = []
    upper, lower = rings["stand"], rings["upper-mid"]
    for i in range(41):
        first_cut.append(tuple((a + b) / 2
                               for a, b in zip(upper[i], lower[i])))
        first_cut.append(tuple((a + b) / 2
                               for a, b in zip(upper[i], lower[(i + 1) % 41])))
    volume = 4 * (4 * _area(first_cut) + _area(lower)) / 6
    for i in range(1, 4):
        start, end = profiles[i], profiles[i + 1]
        middle = tuple((a + b) / 2 for a, b in zip(start, end))
        volume += (SYNTHETIC_HEIGHTS[i] - SYNTHETIC_HEIGHTS[i + 1]) * (
            section_area(start) + 4 * section_area(middle) + section_area(end)
        ) / 6
    for height, a, b, d, e in (
        (4, decimal.Decimal("3.875"), decimal.Decimal("4.25"),
         decimal.Decimal("1.5"), decimal.Decimal(3)),
        (4, decimal.Decimal("4.25"), decimal.Decimal("4.75"),
         decimal.Decimal(3), decimal.Decimal(3)),
        (5, decimal.Decimal("4.75"), decimal.Decimal(6),
         decimal.Decimal(3), decimal.Decimal(0)),
    ):
        volume += height * (2 * a * d + 2 * (a + b) * (d + e) + 2 * b * e) / 6
    volume += decimal.Decimal(100) / 3  # Both artificial bevels.
    return vertices, rings, volume


def _area(points):
    return abs(sum(a[0] * b[1] - a[1] * b[0]
                   for a, b in zip(points, points[1:] + points[:1]))) / 2


def _triple(a, b, c, d):
    """Return a signed six-volume without candidate vector helpers."""
    u, v, w = (tuple(y - x for x, y in zip(a, p)) for p in (b, c, d))
    return (u[0] * (v[1] * w[2] - v[2] * w[1])
            - u[1] * (v[0] * w[2] - v[2] * w[0])
            + u[2] * (v[0] * w[1] - v[1] * w[0]))


def validate_surface_contract(geometry):
    """Preserve source aliases, nonplanar diagonals and named faces."""
    points = {name: (x, y, z) for name, x, y, z in geometry.vertices}
    faces = dict(geometry.faces)
    edges = key_tests._edges(geometry)
    assert len(points) == 213 and len(edges) == 467 and len(faces) == 256
    assert len(points) - len(edges) + len(faces) == 2
    assert "stand-02" not in points and "stand-40" not in points
    assert len(faces["plinth-cap"]) == 41
    assert "stand-cap" not in faces
    first = {name: ids for name, ids in faces.items()
             if name.startswith("stand-to-upper-mid-")}
    assert len(first) == 78 and all(len(ids) == 3 for ids in first.values())
    for i in range(1, 41):
        j = (i + 1) % 41
        upper_i = "stand-{:02d}".format({2: 1, 40: 0}.get(i, i))
        upper_j = "stand-{:02d}".format({2: 1, 40: 0}.get(j, j))
        lower_i = "upper-mid-{:02d}".format(i)
        lower_j = "upper-mid-{:02d}".format(j)
        for part, expected in enumerate(((upper_i, upper_j, lower_j),
                                         (upper_i, lower_j, lower_i))):
            face = "stand-to-upper-mid-{:02d}-triangle-{}".format(i, part)
            if len(set(expected)) < 3:
                assert face not in faces
            else:
                assert set(faces[face]) == set(expected)
    # This synthetic quad is nonplanar, so the opposite diagonal changes
    # the surface even though all four original vertices remain present.
    ids = ("stand-03", "stand-04", "upper-mid-04", "upper-mid-03")
    assert _triple(*(points[name] for name in ids)) != 0
    assert frozenset((ids[0], ids[2])) in edges
    assert frozenset((ids[1], ids[3])) not in edges
    knife = ["stand-{:02d}".format(i) for i in (1, *range(3, 40), 0)]
    assert len(knife) == 39
    for i, (a, b) in enumerate(zip(knife, knife[1:])):
        assert set(faces["grip-front-upper-triangle-{:02d}".format(i)]) == {
            "grip-negative-top-front", a, b,
        }
    assert set(faces["grip-front-upper-triangle-38"]) == {
        "grip-negative-top-front", "stand-00", "grip-positive-top-front",
    }
    for side, seat, front, outer in (
        ("negative", "seat-01", "plinth-01", "plinth-02"),
        ("positive", "seat-00", "plinth-00", "plinth-40"),
    ):
        tip = "bevel-" + side + "-tip"
        for label, expected in (("visible", {tip, seat, outer}),
                                ("base", {tip, front, outer}),
                                ("rear", {tip, front, seat})):
            assert set(faces["bevel-" + side + "-" + label]) == expected
        assert all(set(ids) != {seat, front, outer} for ids in faces.values())
    for ids in faces.values():
        if len(ids) > 3:
            a, b, c = (points[name] for name in ids[:3])
            assert all(_triple(a, b, c, points[name]) == 0 for name in ids[3:])


def validate_analytical_geometry():
    """Compare every point, volume and fourteen landmarks."""
    parameters = synthetic_parameters()
    geometry = chair_inner_jaw.construct_chair_inner_jaw(parameters)
    validate_surface_contract(geometry)
    assert geometry.bounds_mm == SYNTHETIC_BOUNDS
    assert geometry.volume_mm3.coefficients == SYNTHETIC_VOLUME_COEFFICIENTS
    assert seat_tests.signed_boundary_volume(geometry) == geometry.volume_mm3
    with decimal.localcontext() as context:
        context.prec = 100
        expected, rings, volume = independent_geometry()
        allowance = decimal.Decimal("1e-75")  # Arithmetic, not physical fit.
        actual = {name: (x, y, z) for name, x, y, z in geometry.vertices}
        assert actual.keys() == expected.keys()
        for name in expected:
            assert all(abs(_decimal(a) - b) < allowance
                       for a, b in zip(actual[name], expected[name])), name
        assert abs(_decimal(geometry.volume_mm3) - volume) < allowance
        assert tuple(name for name, _ring in geometry.source_sections_mm) == (
            STAGES
        )
        for (stage, source), height in zip(geometry.source_sections_mm,
                                           SYNTHETIC_HEIGHTS):
            assert len(source) == 41
            for i, pair in enumerate(zip(source, rings[stage])):
                point, expected_xy = pair
                name, x, y, z = point
                ex, ey = expected_xy
                assert name == "{}-{:02d}".format(stage, i)
                assert abs(_decimal(x) - ex) < allowance
                assert abs(_decimal(y) - ey) < allowance
                assert z == height - 32
                canonical = parameters.source_to_chair((x, y, z))
                assert (-canonical[0], -canonical[1] - 3,
                        canonical[2] - 32) == (x, y, z)
                alias = {"stand-02": "stand-01", "stand-40": "stand-00"}
                assert canonical == actual[alias.get(name, name)]
    landmarks = {
        "base-origin": (0, 0, 0), "rail-seat-centre": (0, 0, 8),
        "rail-top-centre": (0, 0, 32), "gauge-face-at-seat": (0, -3, 8),
        "inner-jaw-grip-top-front-centre": (0, Fraction(-5, 2), 26),
        "inner-jaw-grip-top-web-centre": (0, -1, 26),
        "inner-jaw-grip-bottom-web-centre": (0, -1, 18),
        "inner-jaw-negative-bevel-tip": (-12, -4, 3),
        "inner-jaw-positive-bevel-tip": (12, -4, 3),
    }
    landmarks.update({"inner-jaw-" + stage + "-front-centre": (0, -4, z)
                      for stage, z in zip(STAGES, SYNTHETIC_HEIGHTS)})
    assert dict(geometry.landmarks) == landmarks
    # The upper-middle centre is an internal analytical reference.
    assert landmarks["inner-jaw-upper-mid-front-centre"] not in actual.values()
    return geometry


def validate_scaling_and_frame(geometry):
    """Scale lengths only; keep source placement and ratios separate."""
    parameters = geometry.parameters
    for scale in (Fraction(1, 2), Fraction(7, 3)):
        scaled = chair_inner_jaw.construct_chair_inner_jaw(
            chair_inner_jaw.ChairInnerJawParameters(**{
                field.name: getattr(parameters, field.name)
                * (1 if field.name in SLOPES else scale)
                for field in fields(parameters)
            })
        )
        assert scaled.faces == geometry.faces
        assert scaled.vertices == tuple((name, x * scale, y * scale, z * scale)
                                        for name, x, y, z in geometry.vertices)
        assert scaled.volume_mm3 == geometry.volume_mm3 * scale ** 3
        assert scaled.bounds_mm == tuple(v * scale for v in geometry.bounds_mm)
        assert scaled.landmarks == tuple(
            (name, tuple(v * scale for v in point))
            for name, point in geometry.landmarks
        )
    deeper = chair_inner_jaw.construct_chair_inner_jaw(replace(
        parameters, rail_depth_mm=Fraction(25),
    ))
    assert deeper.vertices == geometry.vertices
    assert deeper.volume_mm3 == geometry.volume_mm3
    assert dict(deeper.landmarks)["rail-top-centre"] == (0, 0, 33)
    shifted = chair_inner_jaw.construct_chair_inner_jaw(replace(
        parameters, rail_head_width_mm=Fraction(8),
        rail_foot_width_mm=Fraction(10), rail_web_width_mm=Fraction(4),
    ))
    assert shifted.vertices == tuple((name, x, y - 1, z)
                                     for name, x, y, z in geometry.vertices)
    raised = chair_inner_jaw.construct_chair_inner_jaw(replace(
        parameters, seat_thickness_mm=Fraction(9),
        plinth_thickness_mm=Fraction(4), stand_height_mm=Fraction(23),
        outer_top_height_mm=Fraction(25), outer_mid_height_mm=Fraction(19),
        grip_width_reference_height_mm=Fraction(26),
    ))
    assert raised.vertices == tuple((name, x, y, z + 1)
                                    for name, x, y, z in geometry.vertices)
    assert raised.volume_mm3 == shifted.volume_mm3 == geometry.volume_mm3
    changed = chair_inner_jaw.construct_chair_inner_jaw(replace(
        parameters, grip_width_reference_height_mm=Fraction(26),
    ))
    for (name, *before), (after_name, *after) in zip(
        geometry.vertices, changed.vertices,
    ):
        assert name == after_name
        if name.startswith("grip-") and "-top-" in name:
            assert before[0] != after[0] and before[1:] == after[1:]
        else:
            assert before == after
    assert changed.volume_mm3 != geometry.volume_mm3


def validate_parameter_refusals():
    """Reject singular, non-finite and unsupported parameter domains."""
    original = synthetic_parameters()
    for name, value in (
        ("rail_web_face_top_from_rail_bottom_mm", Fraction(14)),
        ("stand_height_mm", Fraction(18)),
        ("rail_web_face_bottom_from_rail_bottom_mm", Fraction(5)),
        ("rail_foot_depth_mm", Fraction(0)),
        ("plinth_thickness_mm", Fraction(8)),
        ("chair_half_width_mm", Fraction(10)),
        ("outer_corner_radius_mm", Fraction(14)),
        ("insert_depth_mm", Fraction(2)),
        ("rail_web_width_mm", Fraction(6)),
        ("lower_mid_rib_radius_mm", Fraction(1)),
        ("stand_fillet_radius_mm", Fraction(4)),
        ("upper_mid_depth_mm", Fraction(5, 4)),
        ("grip_width_reference_height_mm", Fraction(56)),
        ("top_to_mid_side_slope", Fraction(0)),
        ("mid_to_seat_side_slope", Fraction(-1)),
    ):
        try:
            chair_inner_jaw.construct_chair_inner_jaw(
                replace(original, **{name: value}),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid inner-jaw parameter: " + name)
    for value in (22, 22.0, True, float("nan"), float("inf")):
        try:
            replace(original, stand_height_mm=value)
        except TypeError:
            pass
        else:
            raise AssertionError("Non-Fraction inner-jaw input accepted")
    try:
        chair_inner_jaw.construct_chair_inner_jaw({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated inner-jaw parameters accepted")


def validate_round_trip_and_context(geometry):
    """Preserve evidence and input; production remains blocked."""
    record, manifest = synthetic_inner_jaw_package_records()
    assert validate_document(manifest) == []
    original = copy.deepcopy((record, manifest))
    result = prepare_records(record, manifest)
    assert result.geometry == geometry
    assert (record, manifest) == original
    assert result.package.to_record() == record
    assert result.component_id == "component:test:inner-jaw"
    assert result.procedure_id == "procedure:test:1-inner-jaw"
    assert result.manifest_json == seat_tests.canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    encoded = definitions.chair_definition_package_to_json(result.package)
    reopened = definitions.chair_definition_package_from_json(
        encoded, json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_inner_jaw_research(
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
    record, _manifest = synthetic_inner_jaw_package_records()
    quantities = record["definition"]["quantities"]
    height = next(i for i, q in enumerate(quantities)
                  if q["purpose"] == "stand_height_mm")
    cases = []

    def add(name, expected, *changes):
        cases.append((name, expected, changes))

    for index in (0, 1):
        add("unknown procedure {}".format(index), "research-procedure-set",
            ("record", ("definition", "procedures", index, "rule_id"),
             "tracktemplate.test.unsupported-inner-jaw-variant.v1"))
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
         "18"),
        ("record", ("definition", "quantities", height, "canonical_value"),
         "18"))
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
    for name in SLOPES:
        slope = next(i for i, q in enumerate(quantities)
                     if q["purpose"] == name)
        add("slope treated as length " + name, "research-parameter-unit",
            ("record", ("definition", "quantities", slope,
                        "quantity_kind"), "length"),
            ("record", ("definition", "quantities", slope,
                        "source_unit"), "mm"),
            ("record", ("definition", "quantities", slope,
                        "canonical_unit"), "mm"))
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
        raise AssertionError("Unsafe signed inner-jaw request accepted")
    assert (record, manifest) == before


def validate_semantic_rejections():
    """Check signed refusals and separation of all components."""
    cases = _mutations()
    for name, expected, changes in cases:
        record, manifest = synthetic_inner_jaw_package_records()
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
                      chair_research.prepare_chair_base_research,
                      chair_research.prepare_chair_outer_jaw_research):
        record, manifest = synthetic_inner_jaw_package_records()
        _expect_rejection(
            record, manifest, "research-procedure-set", operation,
        )
    for builder in (seat_tests.synthetic_package_records,
                    key_tests.synthetic_key_package_records,
                    base_tests.synthetic_base_package_records,
                    outer_tests.synthetic_outer_jaw_package_records):
        record, manifest = builder()
        _expect_rejection(record, manifest, "research-procedure-set")
    return len(cases) + 8


def main():
    """Prove this component and preserve four accepted test floors."""
    validate_parameter_refusals()
    geometry = validate_analytical_geometry()
    validate_scaling_and_frame(geometry)
    validate_round_trip_and_context(geometry)
    count = validate_semantic_rejections()
    outer_tests.main()
    print("Phase 9A chair inner-jaw standalone validation passed "
          "({} signed rejection cases)".format(count))


if __name__ == "__main__":
    main()
