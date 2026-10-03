#!/usr/bin/env python3
"""Check the private research seat with artificial, non-prototype inputs.

No quantity in this file describes S1 or physical railway material. Frozen
Templot input packages remain separate local evidence. These tests protect
analytical construction and reference-only admission boundaries.
"""

import copy
from dataclasses import fields, replace
import decimal
from fractions import Fraction
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
)
from tracktemplate.application.chair_research import (  # noqa: E402
    prepare_chair_seat_research,
)
from tracktemplate.domain.chair_seat import (  # noqa: E402
    ChairSeatParameters,
    construct_chair_seat,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402


SYNTHETIC_VALUES = {
    "chair_half_width_mm": "10",
    "seat_top_half_width_mm": "6",
    "outline_inset_mm": "1",
    "side_spacing_mm": "2",
    "seat_thickness_mm": "4",
    "edge_thickness_mm": "1",
    "plinth_thickness_mm": "2",
    "outer_jaw_face_mm": "10",
    "rail_head_width_mm": "4",
    "rail_foot_width_mm": "6",
    "rail_depth_mm": "12",
    "under_key_half_width_mm": "3",
}


def synthetic_parameters():
    """Return deliberately artificial dimensions in full-size millimetres."""
    return ChairSeatParameters(**{
        name: Fraction(value) for name, value in SYNTHETIC_VALUES.items()
    })


def canonical_json(value):
    """Serialize a package or manifest for deterministic fixture linkage."""
    return json.dumps(
        value, allow_nan=False, ensure_ascii=True,
        separators=(",", ":"), sort_keys=True,
    )


def resign_package(record, manifest):
    """Re-sign mutations so content hashes cannot conceal semantic defects."""
    record["dependency_manifest"]["content_signature"] = (
        definitions.chair_definition_manifest_signature(
            canonical_json(manifest),
        )
    )
    unsigned = copy.deepcopy(record)
    unsigned.pop("content_signature", None)
    record["content_signature"] = "sha256:" + hashlib.sha256(
        canonical_json(unsigned).encode("utf-8")
    ).hexdigest()
    return record


def _determinant(first, second, third):
    a, b, c = first
    d, e, f = second
    g, h, i = third
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def signed_boundary_volume(geometry):
    """Integrate outward triangle tetrahedra, independent of seat formula."""
    points = {row[0]: row[1:] for row in geometry.vertices}
    volume = Fraction(0)
    for _name, boundary in geometry.faces:
        origin = points[boundary[0]]
        for index in range(1, len(boundary) - 1):
            volume += _determinant(
                origin, points[boundary[index]], points[boundary[index + 1]],
            ) / 6
    return volume


def validate_analytical_geometry():
    """Prove closure, analytical size and the non-planar diagonal choice."""
    parameters = synthetic_parameters()
    geometry = construct_chair_seat(parameters)
    points = {row[0]: row[1:] for row in geometry.vertices}
    assert len(points) == len(geometry.vertices) == 12
    assert len({name for name, _boundary in geometry.faces}) == 11
    assert all(isinstance(value, Fraction) for point in points.values()
               for value in point)
    assert geometry.bounds_mm == (-9, -3, 1, 9, 8, 4)
    # The six-unit rail strip is a trapezoidal prism: 6*(18+12)/2*3.
    # Independent paper integration of the five-unit under-key region
    # gives 515/3. No source railway dimension enters either result.
    assert geometry.volume_mm3 == Fraction(270) + Fraction(515, 3)
    assert signed_boundary_volume(geometry) == Fraction(1325, 3)
    translated = replace(geometry, vertices=tuple(
        (name, x + 17, y - 11, z + 23)
        for name, x, y, z in geometry.vertices
    ))
    assert signed_boundary_volume(translated) == geometry.volume_mm3

    directed = []
    for _name, boundary in geometry.faces:
        assert len(boundary) == len(set(boundary))
        directed.extend(zip(boundary, boundary[1:] + boundary[:1]))
    edges = {frozenset(edge) for edge in directed}
    assert len(edges) == 21
    assert len(points) - len(edges) + len(geometry.faces) == 2
    for start, end in directed:
        assert directed.count((start, end)) == 1
        assert directed.count((end, start)) == 1
    coordinate_edges = {
        frozenset((points[start], points[end])) for start, end in directed
    }
    for sign in (-1, 1):
        top_foot = (sign * 6, 3, 4)
        bottom_foot = (sign * 9, 3, 1)
        top_outer = (sign * 3, 8, 4)
        bottom_outer = (sign * 8, 8, 2)
        assert frozenset((top_foot, bottom_outer)) in coordinate_edges
        assert frozenset((bottom_foot, top_outer)) not in coordinate_edges
        vectors = [tuple(a - b for a, b in zip(point, top_foot))
                   for point in (bottom_foot, bottom_outer, top_outer)]
        assert abs(_determinant(*vectors)) == 45
    assert {(-x, y, z) for x, y, z in points.values()} == set(points.values())

    for scale in (Fraction(1, 8), Fraction(7, 3)):
        scaled = ChairSeatParameters(**{
            item.name: getattr(parameters, item.name) * scale
            for item in fields(parameters)
        })
        result = construct_chair_seat(scaled)
        assert result.bounds_mm == tuple(
            value * scale for value in geometry.bounds_mm
        )
        assert result.volume_mm3 == geometry.volume_mm3 * scale ** 3
        assert signed_boundary_volume(result) == result.volume_mm3
        assert tuple(row[0] for row in result.vertices) == tuple(points)
        assert result.faces == geometry.faces

    deeper = replace(parameters, rail_depth_mm=Fraction(30))
    deep_geometry = construct_chair_seat(deeper)
    assert deep_geometry.vertices == geometry.vertices
    assert deep_geometry.volume_mm3 == geometry.volume_mm3
    assert dict(deep_geometry.landmarks)["rail-top-centre"] == (0, 0, 34)
    source_point = (Fraction(5), Fraction(7), Fraction(-12))
    assert parameters.source_to_chair(source_point) == (-5, -9, 4)
    origin = parameters.source_to_chair((Fraction(0),) * 3)
    transformed_basis = []
    for axis in range(3):
        basis = tuple(Fraction(index == axis) for index in range(3))
        transformed = parameters.source_to_chair(basis)
        transformed_basis.append(tuple(
            a - b for a, b in zip(transformed, origin)
        ))
    assert _determinant(*transformed_basis) == 1
    return geometry


def validate_invalid_geometry():
    """Reject unsupported geometry before construction or any host work."""
    original = synthetic_parameters()
    for name, value in (
        ("seat_thickness_mm", Fraction(0)),
        ("rail_depth_mm", Fraction(-1)),
        ("outline_inset_mm", Fraction(3)),
        ("side_spacing_mm", Fraction(10)),
        ("edge_thickness_mm", Fraction(3)),
        ("plinth_thickness_mm", Fraction(4)),
        ("under_key_half_width_mm", Fraction(7)),
        ("outer_jaw_face_mm", Fraction(5)),
        ("side_spacing_mm", Fraction(6)),
        ("rail_depth_mm", 12.0),
        ("rail_depth_mm", True),
    ):
        try:
            construct_chair_seat(replace(original, **{name: value}))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid geometry accepted: " + name)
    try:
        construct_chair_seat({})
    except TypeError:
        pass
    else:
        raise AssertionError("Unvalidated parameter record accepted")


def synthetic_package_records():
    """Build signed mock research metadata, never authentic Templot evidence.

    Per-field source identities below are invented test doubles. The
    Templot classification exercises restrictions; it does not attribute
    these artificial dimensions to Templot or authenticate a source.
    """
    fixtures = ROOT / "tests" / "fixtures"
    record = json.loads((
        fixtures / "chair-definition-v1-contract.json"
    ).read_text())
    manifest = json.loads((
        fixtures / "chair-definition-v1-contract.dependency-manifest.json"
    ).read_text())
    package_id = "tracktemplate:test:synthetic-research-seat"
    manifest_id = package_id + ":manifest"
    version = "1.0.0-test"
    description = (
        "SYNTHETIC TEST DOUBLE. Invented geometry and source metadata; "
        "not S1, Templot evidence, a physical rail or a production chair."
    )
    permissions = {
        "access": "permitted", "adaptation": "permitted",
        "production_output": "reference-only",
        "redistribution": "reference-only",
        "commercial_use": "reference-only", "publication": "reference-only",
    }
    record["package"].update({
        "package_id": package_id, "package_version": version,
        "license_expression": "NOASSERTION", "permissions": dict(permissions),
        "project_status": "reference-only",
    })
    definition = record["definition"]
    definition.update({
        "definition_id": package_id + ":definition",
        "definition_version": version,
        "prototype_designation": "SYNTHETIC-TEST-NOT-A-PROTOTYPE",
        "description": description,
        "lineage_id": "lineage:test:context",
    })
    manifest.update({
        "manifest_id": manifest_id, "audit_scope": "s1-chair-release-path",
    })
    manifest["subject"].update({
        "identifier": package_id, "version": version,
        "description": description, "package_license": "NOASSERTION",
    })
    status = copy.deepcopy(manifest["project_status"])
    status.update({
        "status": "reference-only", "reason": description,
        "reviewed_by": "Synthetic test fixture", "reviewed_on": "2026-10-03",
        "decision_reference": "tests/validate_phase9a_chair_seat.py",
    })
    manifest["project_status"] = status
    template_dependency = copy.deepcopy(manifest["dependencies"][0])
    dependencies = []
    lineages = []
    quantities = []
    for name in ("context", *sorted(SYNTHETIC_VALUES)):
        dependency_id = "dependency:test:" + name
        lineage_id = "lineage:test:" + name
        digest = hashlib.sha256(
            ("Invented source test double for " + name).encode("utf-8")
        ).hexdigest()
        dependency = copy.deepcopy(template_dependency)
        dependency.update({
            "identifier": dependency_id, "name": description + " " + name,
            "role": "production-input", "output_affecting": True,
            "classifications": ["templot_reference_data"],
            "source": {
                "creator_or_supplier": "TrackTemplate synthetic test fixture",
                "locator": "synthetic-test-double://chair-seat/" + name,
                "acquired_on": "2026-10-03", "evidence_sha256": digest,
            },
            "license_expression": "NOASSERTION",
            "permissions": dict(permissions),
            "conditions": [description, "Private research test only."],
            "project_status": copy.deepcopy(status),
        })
        dependency["contribution_attestation"] = {
            "status": "recorded",
            "reference": (
                "Invented metadata in tests/validate_phase9a_chair_seat.py"
            ),
        }
        dependencies.append(dependency)
        lineages.append({
            "lineage_id": lineage_id,
            "classifications": ["templot_reference_data"],
            "evidence_state": "factual", "dependency_ids": [dependency_id],
            "source_file_sha256s": [digest], "derivation": None,
            "assumptions": [
                description, "Factual means literal fixture value only.",
            ],
            "project_status": "reference-only",
            "validation_state": "unreviewed",
        })
        if name != "context":
            quantities.append({
                "quantity_id": "quantity:test:" + name,
                "purpose": name, "quantity_kind": "length",
                "source_value": SYNTHETIC_VALUES[name], "source_unit": "mm",
                "canonical_value": SYNTHETIC_VALUES[name],
                "canonical_unit": "mm",
                "uncertainty": None, "lineage_id": lineage_id,
            })
    manifest["dependencies"] = sorted(
        dependencies, key=lambda item: item["identifier"]
    )
    record["lineage"] = sorted(lineages, key=lambda item: item["lineage_id"])
    definition["quantities"] = quantities
    placement_id = "procedure:test:0-frame"
    seat_id = "procedure:test:1-seat"
    frame_output = "result:test:chair-frame"
    for datum in definition["datums"]:
        datum["lineage_id"] = "lineage:test:context"
        datum["derivation_procedure_id"] = placement_id
    definition["procedures"] = [
        {
            "procedure_id": placement_id, "kind": "placement",
            "rule_id": "tracktemplate.chair.source-to-chair-frame.v1",
            "input_ids": [],
            "parameter_quantity_ids": [
                "quantity:test:" + name for name in (
                    "rail_head_width_mm", "rail_depth_mm", "seat_thickness_mm",
                )
            ],
            "output_ids": [frame_output], "lineage_id": "lineage:test:context",
        },
        {
            "procedure_id": seat_id, "kind": "cross-section",
            "rule_id": "tracktemplate.chair.seat-reference.v1",
            "input_ids": [frame_output],
            "parameter_quantity_ids": [
                item["quantity_id"] for item in quantities
            ],
            "output_ids": ["result:test:seat"],
            "lineage_id": "lineage:test:context",
        },
    ]
    definition["components"] = [{
        "component_id": "component:test:seat", "role": "rail-seat",
        "presence": "present", "placement_datum_id": "datum:test:base",
        "procedure_ids": [seat_id], "absence_reason": None,
        "lineage_id": "lineage:test:context",
    }]
    interface = definition["rail_interfaces"][0]
    interface.update({
        "procedure_ids": [seat_id], "clearance_quantity_ids": [],
        "lineage_id": "lineage:test:context",
    })
    record["manufacturing_profiles"] = []
    record["validation"].update({
        "status": "not-run", "tolerance_quantity_ids": [],
        "finding_ids": [], "evidence_ids": [],
    })
    record["acceptance"] = {
        "status": "not-accepted", "accepted_by": None,
        "accepted_on": None, "decision_reference": None,
    }
    record["dependency_manifest"].update({
        "manifest_id": manifest_id, "subject_id": package_id,
        "subject_version": version,
    })
    return resign_package(record, manifest), manifest


def prepare_records(record, manifest):
    """Load and prepare a detached fixture through both public boundaries."""
    manifest_text = canonical_json(manifest)
    package = definitions.chair_definition_package_from_json(
        canonical_json(record), manifest_text,
    )
    return prepare_chair_seat_research(package, manifest_text)


def validate_package_round_trip():
    """Keep exact canonical evidence, field identities and admission closed."""
    record, manifest = synthetic_package_records()
    assert validate_document(manifest) == []
    originals = copy.deepcopy((record, manifest))
    result = prepare_records(record, manifest)
    assert (record, manifest) == originals
    assert result.package.to_record() == record
    assert result.manifest_json == canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    assert result.component_id == "component:test:seat"
    assert result.procedure_id == "procedure:test:1-seat"
    assert result.geometry == validate_analytical_geometry()
    serialized = definitions.chair_definition_package_to_json(result.package)
    reloaded = definitions.chair_definition_package_from_json(
        serialized, json.dumps(manifest, indent=2),
    )
    repeated = prepare_chair_seat_research(reloaded, json.dumps(manifest))
    assert repeated == result
    detached = result.package.to_record()
    detached["definition"]["quantities"][0]["canonical_value"] = "999"
    assert result.package.to_record() == record
    disposition = definitions.chair_definition_package_status(
        result.package, result.manifest_json,
    )
    assert disposition["status"] == "blocked"
    assert "phase9-production-admission-not-enabled" in disposition["findings"]
    assert "package-not-project-cleared" in disposition["findings"]
    assert "package-not-accepted" in disposition["findings"]
    assert not disposition["production_geometry_authorized"]
    assert not disposition["document_mutation_authorized"]
    assert not disposition["filesystem_mutation_authorized"]
    assert definitions.CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED is False

    # Supporting source quantities and validation quantities survive intact.
    # Neither is a hidden additional construction parameter.
    ancestor = copy.deepcopy(record["definition"]["quantities"][0])
    ancestor.update({
        "quantity_id": "quantity:test:ancestor",
        "purpose": "synthetic-ancestry-value",
        "lineage_id": "lineage:test:context",
    })
    tolerance = copy.deepcopy(ancestor)
    tolerance.update({
        "quantity_id": "quantity:test:validation-tolerance",
        "purpose": "synthetic-validation-tolerance",
    })
    record["definition"]["quantities"].extend((ancestor, tolerance))
    record["definition"]["quantities"].sort(
        key=lambda item: item["quantity_id"],
    )
    record["lineage"][0].update({
        "evidence_state": "derived",
        "derivation": {
            "rule_id": "tracktemplate.test.synthetic-identity.v1",
            "input_ids": [ancestor["quantity_id"]],
        },
    })
    record["validation"]["tolerance_quantity_ids"] = [tolerance["quantity_id"]]
    resign_package(record, manifest)
    supporting = prepare_records(record, manifest)
    assert supporting.geometry == result.geometry
    assert supporting.package.to_record() == record


def validate_decimal_context_independence():
    """Keep exact inputs independent of caller precision and rounding."""
    record, manifest = synthetic_package_records()
    scale = Fraction(123456789, 10 ** 9)
    for quantity in record["definition"]["quantities"]:
        # All invented source values are integer millimetres. Construct a
        # nine-place decimal string with integer arithmetic, not Decimal.
        numerator = int(quantity["source_value"]) * 123456789
        value = "{}.{:09d}".format(numerator // 10 ** 9, numerator % 10 ** 9)
        quantity["source_value"] = value
        quantity["canonical_value"] = value
    resign_package(record, manifest)
    baseline = prepare_records(record, manifest)
    assert baseline.geometry.volume_mm3 == Fraction(1325, 3) * scale ** 3
    assert baseline.geometry.bounds_mm == tuple(
        value * scale for value in (-9, -3, 1, 9, 8, 4)
    )
    for precision, rounding in (
        (2, decimal.ROUND_DOWN), (6, decimal.ROUND_UP),
        (50, decimal.ROUND_HALF_EVEN),
    ):
        with decimal.localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            context.traps[decimal.Inexact] = True
            context.traps[decimal.Rounded] = True
            context.clear_flags()
            flags = dict(context.flags)
            assert prepare_records(record, manifest) == baseline
            assert dict(context.flags) == flags


def _set_path(record, path, value):
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def _rejection_cases():
    """Return separately re-signed attacks on each supported boundary."""
    cases = []

    def add(name, expected, *changes):
        cases.append((name, expected, changes))

    quantity = ("definition", "quantities", 0)
    lineage = ("lineage", 0)
    dependency = ("dependencies", 0)
    add("wrong canonical unit", "unsupported-unit",
        ("record", quantity + ("canonical_unit",), "cm"))
    add("non-length parameter", "research-parameter-unit",
        ("record", quantity + ("quantity_kind",), "dimensionless"),
        ("record", quantity + ("source_unit",), "1"),
        ("record", quantity + ("canonical_unit",), "1"))
    add("source conversion changed", "unit-conversion-mismatch",
        ("record", quantity + ("source_unit",), "cm"))
    add("wrong coordinate frame", "unsupported-coordinate-frame",
        ("record", ("definition", "frame", "y_axis"), "field-to-gauge"))
    for index in (0, 1):
        add("unknown rule {}".format(index), "research-procedure-set",
            ("record", ("definition", "procedures", index, "rule_id"),
             "tracktemplate.test.unsupported.v1"))
    add("parameter purpose changed", "research-parameter-set",
        ("record", quantity + ("purpose",), "unsupported-purpose"))
    add("unbound datum", "research-datum-set",
        ("record", ("definition", "datums", 0,
                    "derivation_procedure_id"), None))
    add("different component", "research-component-set",
        ("record", ("definition", "components", 0, "role"), "base-plinth"))
    add("wrong seat interface", "research-interface-set",
        ("record", ("definition", "rail_interfaces", 0, "seat_datum_id"),
         "datum:test:base"))
    add("manufacturing profile", "research-manufacturing-unsupported",
        ("record", ("manufacturing_profiles",), [{
            "profile_id": "manufacturing:test:unsupported",
            "description": "Artificial forbidden manufacturing profile.",
            "model_scale": "1", "quantities": [],
            "lineage_id": "lineage:test:context",
        }]))
    for state in ("unresolved", "inferred", "comparison-only"):
        add("lineage state " + state, "research-lineage-unresolved",
            ("record", lineage + ("evidence_state",), state))
    add("cleared lineage", "research-lineage-unresolved",
        ("record", lineage + ("project_status",), "project-cleared"))
    add("rejected lineage", "research-lineage-unresolved",
        ("record", lineage + ("validation_state",), "rejected"))
    add("removed reference classification", "research-lineage-unresolved",
        ("record", lineage + ("classifications",), ["user_design"]),
        ("manifest", dependency + ("classifications",), ["user_design"]))
    add("wrong field source hash", "research-source-hash-mismatch",
        ("record", lineage + ("source_file_sha256s",), ["0" * 64]))
    add("missing field source hashes", "research-source-hash-mismatch",
        ("record", lineage + ("source_file_sha256s",), []))
    for field in ("creator_or_supplier", "locator", "evidence_sha256"):
        add("missing source " + field, "research-source-identity",
            ("manifest", dependency + ("source", field), ""))
    add("missing licence state", "research-source-identity",
        ("manifest", dependency + ("license_expression",), ""))
    add("non-output source", "research-dependency-role",
        ("manifest", dependency + ("output_affecting",), False))
    add("comparison-only source", "research-dependency-role",
        ("manifest", dependency + ("role",), "comparison-only"))
    add("cleared source", "research-dependency-role",
        ("manifest", dependency + ("project_status", "status"),
         "project-cleared"))
    add("missing source permissions", "research-permissions-invalid",
        ("manifest", dependency + ("permissions",), {}))
    for target, base in (("record", ("package",)), ("manifest", dependency)):
        for permission in ("access", "adaptation"):
            add(target + " restricted " + permission,
                "research-use-restricted",
                (target, base + ("permissions", permission), "restricted"))
        add(target + " unknown access", "research-use-restricted",
            (target, base + ("permissions", "access"), "unknown"))
    add("cleared package", "research-status-required",
        ("record", ("package", "project_status"), "project-cleared"),
        ("manifest", ("project_status", "status"), "project-cleared"))
    add("publication use", "research-status-required",
        ("record", ("package", "intended_uses"), ["publication"]),
        ("manifest", ("intended_uses",), ["publication"]))
    add("accepted package", "research-status-required",
        ("record", ("acceptance",), {
            "status": "accepted", "accepted_by": "Invented test decision",
            "accepted_on": "2026-10-03", "decision_reference": "test-only",
        }))
    for state in ("failed", "blocked"):
        add(state + " validation", "research-validation-blocked",
            ("record", ("validation", "status"), state))
    record, _manifest = synthetic_package_records()
    side_index = next(index for index, value in enumerate(
        record["definition"]["quantities"]
    ) if value["purpose"] == "side_spacing_mm")
    add("nonconvex geometry", "research-geometry-invalid",
        ("record", ("definition", "quantities", side_index, "source_value"),
         "6"),
        ("record", ("definition", "quantities", side_index,
                    "canonical_value"), "6"))
    extra = copy.deepcopy(record["definition"]["quantities"][-1])
    extra.update({"quantity_id": "quantity:test:unused",
                  "purpose": "unsupported-unused-dimension"})
    add("unused dimension", "research-unused-quantity",
        ("record", ("definition", "quantities"),
         record["definition"]["quantities"] + [extra]))
    add("cyclic derivation", "research-derivation-cycle",
        ("record", lineage + ("evidence_state",), "derived"),
        ("record", lineage + ("derivation",), {
            "rule_id": "tracktemplate.test.synthetic-cycle.v1",
            "input_ids": [
                record["definition"]["quantities"][0]["quantity_id"]
            ],
        }))
    return cases


def validate_semantic_rejections():
    """Reject validly signed unsafe requests with recoverable diagnostics."""
    cases = _rejection_cases()
    assert len({name for name, _expected, _changes in cases}) == len(cases)
    for name, expected, changes in cases:
        record, manifest = synthetic_package_records()
        targets = {"record": record, "manifest": manifest}
        for target, path, value in changes:
            _set_path(targets[target], path, copy.deepcopy(value))
        resign_package(record, manifest)
        before = copy.deepcopy((record, manifest))
        try:
            prepare_records(record, manifest)
        except definitions.ChairDefinitionError as error:
            assert error.code == expected, (name, expected, error.diagnostic())
            diagnostic = error.diagnostic()
            assert diagnostic["recoverable"] is True
            assert diagnostic["document_mutation"] is False
            assert diagnostic["filesystem_mutation"] is False
            assert diagnostic["path"].startswith("$")
            assert diagnostic["message"]
        else:
            raise AssertionError("Unsafe signed request accepted: " + name)
        assert (record, manifest) == before, name
    return len(cases)


def main():
    """Run deterministic, synthetic-only research-seat regression checks."""
    validate_invalid_geometry()
    validate_package_round_trip()
    validate_decimal_context_independence()
    count = validate_semantic_rejections()
    print("Phase 9A chair seat standalone validation passed "
          "({} signed rejection cases)".format(count))


if __name__ == "__main__":
    main()
