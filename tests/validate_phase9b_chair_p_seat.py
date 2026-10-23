#!/usr/bin/env python3
"""Prove the finite P slide-seat with artificial non-prototype inputs.

Tracked dimensions and source metadata are invented test doubles. The
authentic source package and media remain separate ignored evidence.
This proof confers no physical-fit, placement or production acceptance.
"""

from collections import Counter
import copy
from dataclasses import fields, replace
from decimal import Context, Decimal, Inexact, Rounded, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from tracktemplate.domain.chair_p_seat import (  # noqa: E402
    ChairPSeatParameters,
    construct_chair_p_seat,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    synthetic_package_records,
)


SENTINEL = "Phase 9B chair P slide-seat standalone validation passed"
SYNTHETIC_VALUES = {
    "seat_top_half_width_mm": "8",
    "table_radius_mm": "3",
    "table_centre_from_gauge_face_mm": "12",
    "table_neck_offset_mm": "2",
    "seat_thickness_mm": "5",
    "edge_thickness_mm": "1",
    "rail_head_width_mm": "4",
    "rail_foot_width_mm": "6",
    "rail_depth_mm": "15",
}


def synthetic_parameters():
    """Return deliberately artificial full-size millimetre lengths."""
    return ChairPSeatParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def synthetic_p_seat_package_records():
    """Reuse the existing synthetic package pattern, without source data."""
    record, manifest = synthetic_package_records()
    definition = record["definition"]
    description = (
        "SYNTHETIC TEST DOUBLE. Invented P-pattern slide-seat dimensions "
        "and metadata; not Templot evidence or a physical railway product."
    )
    package_id = "tracktemplate:test:synthetic-research-p-seat"
    manifest_id = package_id + ":manifest"
    record["package"]["package_id"] = package_id
    definition.update({
        "definition_id": package_id + ":definition",
        "prototype_designation": "SYNTHETIC-P-PATTERN-NOT-A-PROTOTYPE",
        "description": description,
    })
    manifest["manifest_id"] = manifest_id
    manifest["subject"].update({
        "identifier": package_id, "description": description,
    })
    record["dependency_manifest"].update({
        "manifest_id": manifest_id, "subject_id": package_id,
    })
    context_lineage = copy.deepcopy(next(
        item for item in record["lineage"]
        if item["lineage_id"] == "lineage:test:context"
    ))
    context_dependency = copy.deepcopy(next(
        item for item in manifest["dependencies"]
        if item["identifier"] == "dependency:test:context"
    ))
    quantity_template = copy.deepcopy(definition["quantities"][0])
    quantities = []
    lineages = [context_lineage]
    dependencies = [context_dependency]
    for name, value in sorted(SYNTHETIC_VALUES.items()):
        digest = hashlib.sha256(
            (description + name + "=" + value).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(context_dependency)
        dependency.update({
            "identifier": "dependency:test:" + name,
            "name": description + " " + name,
        })
        dependency["source"].update({
            "locator": "synthetic-test-double://chair-p-seat/" + name,
            "evidence_sha256": digest,
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9b_chair_p_seat.py"
        )
        lineage = copy.deepcopy(context_lineage)
        lineage.update({
            "lineage_id": "lineage:test:" + name,
            "dependency_ids": [dependency["identifier"]],
            "source_file_sha256s": [digest],
            "assumptions": [description],
        })
        quantity = copy.deepcopy(quantity_template)
        quantity.update({
            "quantity_id": "quantity:test:" + name,
            "purpose": name, "source_value": value,
            "canonical_value": value, "lineage_id": lineage["lineage_id"],
        })
        dependencies.append(dependency)
        lineages.append(lineage)
        quantities.append(quantity)
    record["lineage"] = sorted(lineages, key=lambda item: item["lineage_id"])
    manifest["dependencies"] = sorted(
        dependencies, key=lambda item: item["identifier"],
    )
    definition["quantities"] = quantities
    definition["procedures"][1].update({
        "rule_id": "tracktemplate.chair.p-seat-reference.v1",
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
    })
    return resign_package(record, manifest), manifest


def load_package(record, manifest):
    """Load a detached fixture and its canonical manifest text."""
    text = canonical_json(manifest)
    return definitions.chair_definition_package_from_json(
        canonical_json(record), text,
    ), text


def _prepare(record, manifest):
    return chair_research.prepare_chair_p_seat_research(
        *load_package(record, manifest)
    )


def _determinant(a, b, c):
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def _signed_volume(geometry):
    points = {row[0]: row[1:] for row in geometry.vertices}
    return sum(
        _determinant(points[boundary[0]], points[boundary[index]],
                     points[boundary[index + 1]]) / 6
        for _name, boundary in geometry.faces
        for index in range(1, len(boundary) - 1)
    )


def _independent_sin_step():
    # Taylor expansion is independent of the implementation's radicals.
    pi = Decimal(
        "3.141592653589793238462643383279502884197169399375105820974944"
        "5923078164062862089986280348253421170679"
    )
    angle = pi / 24
    term = total = angle
    for index in range(1, 60):
        term *= -angle * angle / ((2 * index) * (2 * index + 1))
        total += term
    return total


def validate_geometry():
    """Prove all outline points, faceted volume, winding and invariants."""
    parameters = synthetic_parameters()
    geometry = construct_chair_p_seat(parameters)
    assert geometry.parameters is parameters
    points = {row[0]: row[1:] for row in geometry.vertices}
    assert len(points) == len(geometry.vertices) == 62
    assert len(geometry.faces) == 33
    assert len({row[0] for row in geometry.faces}) == 33
    assert all(isinstance(value, Decimal) and value.is_finite()
               for point in points.values() for value in point)
    assert geometry.bounds_mm == (-8, -17, 1, 8, 3, 5)
    outline = {row[0]: row[1:] for row in geometry.source_outline_mm}
    assert tuple(outline) == tuple(
        "p{:02d}".format(index) for index in (*range(2, 31), 33, 34)
    )
    assert {name: outline[name] for name in (
        "p02", "p03", "p04", "p16", "p28", "p29", "p30", "p33", "p34",
    )} == {
        "p02": (-8, 1), "p03": (-3, 3), "p04": (-3, 12),
        "p16": (0, 15), "p28": (3, 12), "p29": (3, 3),
        "p30": (8, 1), "p33": (8, -5), "p34": (-8, -5),
    }
    for index in range(25):
        x, y = outline["p{:02d}".format(index + 4)]
        angle = index * math.pi / 24
        assert abs(float(x) + 3 * math.cos(angle)) < 1e-13
        assert abs(float(y) - 12 - 3 * math.sin(angle)) < 1e-13
    with localcontext(Context(prec=90)):
        for name, (x, y) in outline.items():
            assert points["top-" + name] == (-x, -y - 2, 5)
            assert points["bottom-" + name] == (-x, -y - 2, 1)
        # Independent strip decomposition: 96 + 22 + 54, then 24
        # isosceles triangles of area radius**2*sin(7.5 degrees)/2.
        expected = 4 * (172 + 108 * _independent_sin_step())
        assert abs(geometry.volume_mm3 - expected) < Decimal("1e-72")
        assert abs(_signed_volume(geometry) - expected) < Decimal("1e-72")
        # The smooth half-circle would incorrectly increase this volume.
        assert float(geometry.volume_mm3) < 4 * (172 + 9 * math.pi / 2)
        translated = replace(geometry, vertices=tuple(
            (name, x + 17, y - 11, z + 23)
            for name, x, y, z in geometry.vertices
        ))
        assert abs(_signed_volume(translated) - expected) < Decimal("1e-72")
        reflected = {(-x, y, z) for x, y, z in points.values()}
        assert reflected == set(points.values())
        for scale in (Fraction(1, 8), Fraction(7, 3)):
            scaled = construct_chair_p_seat(ChairPSeatParameters(**{
                field.name: getattr(parameters, field.name) * scale
                for field in fields(parameters)
            }))
            decimal_scale = Decimal(scale.numerator) / scale.denominator
            assert scaled.faces == geometry.faces
            for actual, original in zip(scaled.vertices, geometry.vertices):
                assert actual[0] == original[0]
                assert all(abs(a - b * decimal_scale) < Decimal("1e-72")
                           for a, b in zip(actual[1:], original[1:]))
            assert abs(scaled.volume_mm3 - expected * decimal_scale ** 3) < (
                Decimal("1e-70")
            )
    directed = Counter()
    for _name, boundary in geometry.faces:
        assert len(boundary) == len(set(boundary))
        directed.update(zip(boundary, boundary[1:] + boundary[:1]))
    edges = {frozenset(edge) for edge in directed}
    assert len(edges) == 93
    assert len(points) - len(edges) + len(geometry.faces) == 2
    assert all(count == directed[(end, start)] == 1
               for (start, end), count in directed.items())
    deeper = construct_chair_p_seat(replace(
        parameters, rail_depth_mm=Fraction(25),
    ))
    assert deeper.vertices == geometry.vertices
    assert deeper.volume_mm3 == geometry.volume_mm3
    assert dict(deeper.landmarks)["rail-top-centre"] == (0, 0, 30)
    origin = parameters.source_to_chair((Fraction(0),) * 3)
    basis = []
    for axis in range(3):
        mapped = parameters.source_to_chair(tuple(
            Fraction(index == axis) for index in range(3)
        ))
        basis.append(tuple(a - b for a, b in zip(mapped, origin)))
    assert _determinant(*basis) == 1
    assert parameters.source_to_chair(tuple(map(Fraction, (5, 7, -15)))) == (
        -5, -9, 5,
    )
    return geometry


def validate_invalid_geometry():
    """Reject invalid lengths, source branches and lost finite topology."""
    parameters = synthetic_parameters()
    cases = []
    for field in fields(parameters):
        cases.extend((field.name, value, expected) for value, expected in (
            (Fraction(0), ValueError), (Fraction(-1), ValueError),
            (1, TypeError), (1.0, TypeError), (True, TypeError),
            (Decimal("NaN"), TypeError), (float("inf"), TypeError),
        ))
    cases.extend((name, value, ValueError) for name, value in (
        ("seat_thickness_mm", Fraction(1)),
        ("table_radius_mm", Fraction(8)),
        ("table_radius_mm", Fraction(9)),
        ("table_centre_from_gauge_face_mm", Fraction(3)),
        ("table_centre_from_gauge_face_mm", Fraction(2)),
        ("seat_top_half_width_mm", Fraction(3) + Fraction(1, 10 ** 100)),
        ("seat_thickness_mm", Fraction(1) + Fraction(1, 10 ** 100)),
        ("table_centre_from_gauge_face_mm",
         Fraction(3) + Fraction(1, 10 ** 100)),
        ("table_centre_from_gauge_face_mm", Fraction(10 ** 100)),
    ))
    for name, value, expected in cases:
        try:
            construct_chair_p_seat(replace(parameters, **{name: value}))
        except expected:
            pass
        else:
            raise AssertionError(
                "Invalid P slide-seat input accepted: " + name
            )
    try:
        construct_chair_p_seat(replace(
            parameters, rail_head_width_mm=Fraction(10 ** 100),
            rail_foot_width_mm=Fraction(10 ** 100),
        ))
    except ValueError:
        pass
    else:
        raise AssertionError("Chair-frame translation lost topology")
    try:
        construct_chair_p_seat({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated parameters accepted")
    for point in ((1, 2, 3), (Fraction(0),) * 2):
        try:
            parameters.source_to_chair(point)
        except ValueError:
            pass
        else:
            raise AssertionError("Inexact source coordinates accepted")
    return len(cases) + 4


def validate_package_and_context():
    """Keep signed inputs detached, reproducible and private-development."""
    record, manifest = synthetic_p_seat_package_records()
    assert validate_document(manifest) == []
    before = copy.deepcopy((record, manifest))
    request = _prepare(record, manifest)
    assert (record, manifest) == before
    assert request.geometry == validate_geometry()
    assert request.package.to_record() == record
    assert request.manifest_json == canonical_json(manifest)
    assert request.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    assert request.component_id == "component:test:seat"
    assert request.procedure_id == "procedure:test:1-seat"
    round_trip = definitions.chair_definition_package_from_json(
        definitions.chair_definition_package_to_json(request.package),
        json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_p_seat_research(
        round_trip, json.dumps(manifest),
    ) == request
    detached = request.package.to_record()
    detached["definition"]["quantities"][0]["canonical_value"] = "999"
    assert request.package.to_record() == record
    status = definitions.chair_definition_package_status(
        request.package, request.manifest_json,
    )
    assert status["status"] == "blocked"
    assert "phase9-production-admission-not-enabled" in status["findings"]
    assert not status["production_geometry_authorized"]
    assert not status["document_mutation_authorized"]
    assert not status["filesystem_mutation_authorized"]
    for precision, rounding in ((2, "ROUND_DOWN"), (9, "ROUND_UP")):
        with localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            context.traps[Inexact] = context.traps[Rounded] = True
            context.clear_flags()
            flags = dict(context.flags)
            assert _prepare(record, manifest) == request
            assert dict(context.flags) == flags
    assert not any(name in sys.modules for name in (
        "FreeCAD", "Part", "FreeCADGui", "PySide", "PySide2", "PySide6",
        "pivy",
    ))


def _set_path(record, path, value):
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = copy.deepcopy(value)


def validate_package_rejections():
    """Re-sign malformed requests to prove semantic refusal at the gate."""
    baseline, _manifest = synthetic_p_seat_package_records()
    quantity = ("definition", "quantities", 0)
    procedure = ("definition", "procedures", 1)
    cases = [
        ("old rule", "research-procedure-set", "record",
         procedure + ("rule_id",), "tracktemplate.chair.seat-reference.v1"),
        ("unknown rule", "research-procedure-set", "record",
         procedure + ("rule_id",), "tracktemplate.test.unsupported.v1"),
        ("missing parameter", "research-parameter-set", "record",
         procedure + ("parameter_quantity_ids",),
         baseline["definition"]["procedures"][1][
             "parameter_quantity_ids"
         ][:-1]),
        ("unknown purpose", "research-parameter-set", "record",
         quantity + ("purpose",), "unknown-parameter"),
        ("wrong unit", "unsupported-unit", "record",
         quantity + ("canonical_unit",), "cm"),
        ("wrong frame", "unsupported-coordinate-frame", "record",
         ("definition", "frame", "y_axis"), "field-to-gauge"),
        ("wrong component", "research-component-set", "record",
         ("definition", "components", 0, "role"), "base-plinth"),
        ("unresolved lineage", "research-lineage-unresolved", "record",
         ("lineage", 0, "evidence_state"), "unresolved"),
        ("source hash changed", "research-source-hash-mismatch", "record",
         ("lineage", 0, "source_file_sha256s"), ["0" * 64]),
        ("restricted access", "research-use-restricted", "manifest",
         ("dependencies", 0, "permissions", "access"), "restricted"),
        ("source missing", "research-source-identity", "manifest",
         ("dependencies", 0, "source", "locator"), ""),
        ("failed validation", "research-validation-blocked", "record",
         ("validation", "status"), "failed"),
        ("accepted package", "research-status-required", "record",
         ("acceptance",), {
             "status": "accepted", "accepted_by": "Synthetic test",
             "accepted_on": "2026-10-23", "decision_reference": "test-only",
         }),
        ("manufacturing profile", "research-manufacturing-unsupported",
         "record", ("manufacturing_profiles",), [{
             "profile_id": "manufacturing:test:unsupported",
             "description": "Artificial forbidden manufacturing profile.",
             "model_scale": "1", "quantities": [],
             "lineage_id": "lineage:test:context",
         }]),
    ]
    for name, expected, target, path, value in cases:
        record, manifest = synthetic_p_seat_package_records()
        _set_path(record if target == "record" else manifest, path, value)
        resign_package(record, manifest)
        before = copy.deepcopy((record, manifest))
        try:
            _prepare(record, manifest)
        except definitions.ChairDefinitionError as error:
            assert error.code == expected, (name, expected, error.diagnostic())
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"]
            assert not diagnostic["document_mutation"]
            assert not diagnostic["filesystem_mutation"]
        else:
            raise AssertionError(
                "Unsafe signed P slide-seat accepted: " + name
            )
        assert (record, manifest) == before
    # Equal frame values with different identities must still be refused.
    record, manifest = synthetic_p_seat_package_records()
    original = next(q for q in record["definition"]["quantities"]
                    if q["purpose"] == "rail_head_width_mm")
    alternate = dict(original, quantity_id="quantity:test:alternate-head")
    record["definition"]["quantities"].append(alternate)
    record["definition"]["quantities"].sort(key=lambda q: q["quantity_id"])
    frame = record["definition"]["procedures"][0]
    frame["parameter_quantity_ids"] = [
        alternate["quantity_id"] if value == original["quantity_id"] else value
        for value in frame["parameter_quantity_ids"]
    ]
    resign_package(record, manifest)
    try:
        _prepare(record, manifest)
    except definitions.ChairDefinitionError as error:
        assert error.code == "research-frame-inputs", error.diagnostic()
    else:
        raise AssertionError("Mismatched frame quantity identity accepted")
    record, manifest = synthetic_p_seat_package_records()
    radius = next(q for q in record["definition"]["quantities"]
                  if q["purpose"] == "table_radius_mm")
    radius.update({"source_value": "8", "canonical_value": "8"})
    resign_package(record, manifest)
    try:
        _prepare(record, manifest)
    except definitions.ChairDefinitionError as error:
        assert error.code == "research-geometry-invalid", error.diagnostic()
    else:
        raise AssertionError("Collapsed source branch admitted")
    return len(cases) + 2


def main():
    """Run synthetic analytical and package-boundary proofs only."""
    invalid_count = validate_invalid_geometry()
    validate_package_and_context()
    package_count = validate_package_rejections()
    print("{} ({} geometry, {} signed rejection cases)".format(
        SENTINEL, invalid_count, package_count,
    ))


if __name__ == "__main__":
    main()
