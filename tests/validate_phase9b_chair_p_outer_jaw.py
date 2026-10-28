#!/usr/bin/env python3
"""Check the finite P outer-jaw package with invented reference inputs.

These dimensions and source identities are synthetic test doubles. They
confer no physical-fit, production, package or source-rights acceptance.
"""

import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_research,
)
from tools.validate_dependency_manifest import validate_document  # noqa: E402
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
    synthetic_package_records,
)


SENTINEL = "Phase 9B chair P outer-jaw standalone validation passed"
SYNTHETIC_VALUES = {
    "jaw_top_half_width_mm": "2", "jaw_bottom_half_width_mm": "4",
    "jaw_top_depth_mm": "2", "jaw_bottom_depth_mm": "6",
    "jaw_top_slope_mm": "1", "plinth_thickness_mm": "1",
    "seat_thickness_mm": "3", "rail_depth_mm": "20",
    "rail_head_width_mm": "8", "rail_foot_width_mm": "10",
    "rail_web_width_mm": "2", "rail_web_top_from_top_mm": "4",
    "rail_web_bottom_from_top_mm": "12", "rail_fish_ratio": "2",
}


def synthetic_p_outer_jaw_package_records():
    """Return a signed artificial package, with no prototype source data."""
    record, manifest = synthetic_package_records()
    definition = record["definition"]
    description = (
        "SYNTHETIC TEST DOUBLE. Invented P outer-jaw dimensions and "
        "metadata; not Templot evidence or a physical railway product."
    )
    package_id = "tracktemplate:test:synthetic-research-p-outer-jaw"
    manifest_id = package_id + ":manifest"
    record["package"]["package_id"] = package_id
    definition.update({
        "definition_id": package_id + ":definition",
        "prototype_designation": "SYNTHETIC-P-JAW-NOT-A-PROTOTYPE",
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
    quantities, lineages, dependencies = [], [context_lineage], [
        context_dependency,
    ]
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
            "locator": "synthetic-test-double://chair-p-outer-jaw/" + name,
            "evidence_sha256": digest,
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in tests/validate_phase9b_chair_p_outer_jaw.py"
        )
        lineage = copy.deepcopy(context_lineage)
        lineage.update({
            "lineage_id": "lineage:test:" + name,
            "dependency_ids": [dependency["identifier"]],
            "source_file_sha256s": [digest], "assumptions": [description],
        })
        quantity = copy.deepcopy(quantity_template)
        quantity.update({
            "quantity_id": "quantity:test:" + name, "purpose": name,
            "source_value": value, "canonical_value": value,
            "lineage_id": lineage["lineage_id"],
        })
        if name == "rail_fish_ratio":
            quantity.update({
                "quantity_kind": "dimensionless", "source_unit": "1",
                "canonical_unit": "1",
            })
        dependencies.append(dependency)
        lineages.append(lineage)
        quantities.append(quantity)
    record["lineage"] = sorted(lineages, key=lambda item: item["lineage_id"])
    manifest["dependencies"] = sorted(
        dependencies, key=lambda item: item["identifier"],
    )
    definition["quantities"] = quantities
    procedure_id = "procedure:test:1-p-outer-jaw"
    definition["procedures"][1].update({
        "procedure_id": procedure_id,
        "rule_id": "tracktemplate.chair.p-outer-jaw-reference.v1",
        "output_ids": ["result:test:p-outer-jaw"],
        "parameter_quantity_ids": [q["quantity_id"] for q in quantities],
    })
    definition["components"][0].update({
        "component_id": "component:test:p-outer-jaw", "role": "outer-jaw",
        "procedure_ids": [procedure_id],
    })
    definition["rail_interfaces"][0]["procedure_ids"] = [procedure_id]
    return resign_package(record, manifest), manifest


def load_package(record, manifest):
    """Load detached package records and the complete manifest."""
    text = canonical_json(manifest)
    return definitions.chair_definition_package_from_json(
        canonical_json(record), text,
    ), text


def _prepare(record, manifest):
    return chair_research.prepare_chair_p_outer_jaw_research(
        *load_package(record, manifest)
    )


def validate_package_round_trip():
    """Keep all signed inputs detached and production admission closed."""
    record, manifest = synthetic_p_outer_jaw_package_records()
    assert validate_document(manifest) == []
    before = copy.deepcopy((record, manifest))
    result = _prepare(record, manifest)
    assert (record, manifest) == before
    assert result.package.to_record() == record
    assert result.manifest_json == canonical_json(manifest)
    assert result.manifest_signature == record["dependency_manifest"][
        "content_signature"
    ]
    assert result.component_id == "component:test:p-outer-jaw"
    assert result.procedure_id == "procedure:test:1-p-outer-jaw"
    assert tuple(name for name, _part in result.geometry.parts) == (
        "spacer", "body",
    )
    assert all(getattr(result.geometry.parameters, name) == Fraction(value)
               for name, value in SYNTHETIC_VALUES.items())
    assert sum(len(part.source_faces)
               for _, part in result.geometry.parts) == 21
    assert sum(len(part.faces) for _, part in result.geometry.parts) == 23
    reloaded = definitions.chair_definition_package_from_json(
        definitions.chair_definition_package_to_json(result.package),
        json.dumps(manifest, indent=2),
    )
    assert chair_research.prepare_chair_p_outer_jaw_research(
        reloaded, json.dumps(manifest),
    ) == result
    detached = result.package.to_record()
    detached["definition"]["quantities"][0]["canonical_value"] = "999"
    assert result.package.to_record() == record
    status = definitions.chair_definition_package_status(
        result.package, result.manifest_json,
    )
    assert status["status"] == "blocked"
    assert "phase9-production-admission-not-enabled" in status["findings"]
    for name in (
        "production_geometry_authorized", "document_mutation_authorized",
        "filesystem_mutation_authorized",
    ):
        assert not status[name]
    assert not any(name in sys.modules for name in (
        "FreeCAD", "Part", "FreeCADGui", "PySide", "PySide2", "PySide6",
        "pivy",
    ))


def _set_path(record, path, value):
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = copy.deepcopy(value)


def _expect_rejection(record, manifest, expected):
    resign_package(record, manifest)
    before = copy.deepcopy((record, manifest))
    try:
        _prepare(record, manifest)
    except definitions.ChairDefinitionError as error:
        assert error.code == expected, (expected, error.diagnostic())
        diagnostic = error.diagnostic()
        assert diagnostic["recoverable"]
        assert not diagnostic["document_mutation"]
        assert not diagnostic["filesystem_mutation"]
    else:
        raise AssertionError("Unsafe signed P outer-jaw request accepted")
    assert (record, manifest) == before


def validate_package_rejections():
    """Re-sign invalid inputs to expose semantic refusal before any host."""
    baseline, _ = synthetic_p_outer_jaw_package_records()
    quantity = ("definition", "quantities", 0)
    procedure = ("definition", "procedures", 1)
    cases = [
        ("research-procedure-set", "record", procedure + ("rule_id",),
         "tracktemplate.chair.outer-jaw-reference.v1"),
        ("research-parameter-set", "record",
         procedure + ("parameter_quantity_ids",),
         baseline["definition"]["procedures"][1][
             "parameter_quantity_ids"][:-1]),
        ("research-parameter-set", "record", quantity + ("purpose",),
         "unknown"),
        ("unsupported-unit", "record", quantity + ("canonical_unit",), "cm"),
        ("unsupported-coordinate-frame", "record",
         ("definition", "frame", "y_axis"), "field-to-gauge"),
        ("research-component-set", "record",
         ("definition", "components", 0, "role"), "rail-seat"),
        ("research-lineage-unresolved", "record",
         ("lineage", 0, "evidence_state"), "unresolved"),
        ("research-source-hash-mismatch", "record",
         ("lineage", 0, "source_file_sha256s"), ["0" * 64]),
        ("research-use-restricted", "manifest",
         ("dependencies", 0, "permissions", "access"), "restricted"),
        ("research-use-restricted", "record",
         ("package", "permissions", "adaptation"), "restricted"),
        ("research-source-identity", "manifest",
         ("dependencies", 0, "source", "locator"), ""),
        ("research-validation-blocked", "record",
         ("validation", "status"), "failed"),
        ("research-status-required", "record", ("acceptance",), {
            "status": "accepted", "accepted_by": "Synthetic test",
            "accepted_on": "2026-10-28", "decision_reference": "test-only",
        }),
    ]
    for expected, target, path, value in cases:
        record, manifest = synthetic_p_outer_jaw_package_records()
        _set_path(record if target == "record" else manifest, path, value)
        _expect_rejection(record, manifest, expected)
    for purpose, kind, unit in (("rail_fish_ratio", "length", "mm"),
                                ("jaw_top_depth_mm", "dimensionless", "1")):
        record, manifest = synthetic_p_outer_jaw_package_records()
        item = next(q for q in record["definition"]["quantities"]
                    if q["purpose"] == purpose)
        item.update({"quantity_kind": kind, "source_unit": unit,
                     "canonical_unit": unit})
        _expect_rejection(record, manifest, "research-parameter-unit")
    record, manifest = synthetic_p_outer_jaw_package_records()
    original = next(q for q in record["definition"]["quantities"]
                    if q["purpose"] == "rail_head_width_mm")
    alternate = dict(original, quantity_id="quantity:test:alternate-head")
    record["definition"]["quantities"].append(alternate)
    record["definition"]["quantities"].sort(key=lambda q: q["quantity_id"])
    frame = record["definition"]["procedures"][0]
    frame["parameter_quantity_ids"] = [
        alternate["quantity_id"] if q == original["quantity_id"] else q
        for q in frame["parameter_quantity_ids"]
    ]
    _expect_rejection(record, manifest, "research-frame-inputs")
    record, manifest = synthetic_p_outer_jaw_package_records()
    depth = next(q for q in record["definition"]["quantities"]
                 if q["purpose"] == "jaw_top_depth_mm")
    depth.update({"source_value": "0", "canonical_value": "0"})
    _expect_rejection(record, manifest, "research-geometry-invalid")
    return len(cases) + 4


def main():
    """Run only the synthetic package and application contract checks."""
    validate_package_round_trip()
    rejected = validate_package_rejections()
    print("{} ({} signed rejection cases)".format(SENTINEL, rejected))


if __name__ == "__main__":
    main()
