"""Prepare one reference-only rail-seat construction without host mutation.

This finite research operation consumes the existing neutral package v1.
It does not admit a package, interpret arbitrary procedures, or enable
production geometry. Source identities remain supplied by the package;
the local evidence harness verifies the actual frozen source bytes.
"""

from dataclasses import dataclass, fields
from fractions import Fraction
import json

from tracktemplate.application.chair_definition import (
    CHAIR_PERMISSION_FIELDS,
    CHAIR_PERMISSION_STATUSES,
    CHAIR_REQUIRED_DATUM_ROLES,
    ChairDefinitionError,
    ChairDefinitionPackage,
    chair_definition_manifest_signature,
    verify_chair_definition_manifest,
)
from tracktemplate.domain.chair_seat import (
    ChairSeatGeometry,
    ChairSeatParameters,
    construct_chair_seat,
)


CHAIR_SEAT_RESEARCH_RULE_ID = "tracktemplate.chair.seat-reference.v1"
CHAIR_SEAT_FRAME_RULE_ID = "tracktemplate.chair.source-to-chair-frame.v1"
_FRAME_PURPOSES = (
    "rail_head_width_mm", "rail_depth_mm", "seat_thickness_mm",
)


class ChairResearchError(ChairDefinitionError):
    """Recoverable research refusal with no document or filesystem mutation."""


@dataclass(frozen=True)
class ChairSeatResearchResult:
    """Derived geometry alongside complete immutable provenance inputs.

    Adapters prepare from the package and manifest again. They must not
    treat a caller-constructed instance as an authorised geometry request.
    """

    package: ChairDefinitionPackage
    manifest_json: str
    manifest_signature: str
    component_id: str
    procedure_id: str
    geometry: ChairSeatGeometry


def _require(condition, code, path, message):
    if not condition:
        raise ChairResearchError(code, path, message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _permissions(record, path):
    permissions = record.get("permissions")
    _require(
        isinstance(permissions, dict)
        and set(permissions) == set(CHAIR_PERMISSION_FIELDS)
        and all(
            value in CHAIR_PERMISSION_STATUSES
            for value in permissions.values()
        ),
        "research-permissions-invalid", path + ".permissions",
        "complete recorded permission states are required",
    )
    _require(
        permissions["access"] == "permitted"
        and permissions["adaptation"] != "restricted",
        "research-use-restricted", path + ".permissions",
        "research needs permitted access and no known adaptation restriction",
    )


def _research_metadata(record):
    metadata = record["package"]
    _require(
        metadata["project_status"] == "reference-only"
        and metadata["intended_uses"] == ["private-development"]
        and record["acceptance"]["status"] == "not-accepted",
        "research-status-required", "$.package",
        "only unadmitted reference-only private-development packages apply",
    )
    _permissions(metadata, "$.package")
    _require(
        not record["manufacturing_profiles"],
        "research-manufacturing-unsupported", "$.manufacturing_profiles",
        "this full-size proof applies no manufacturing profile",
    )
    _require(
        record["validation"]["status"] not in ("failed", "blocked"),
        "research-validation-blocked", "$.validation.status",
        "failed or blocked research evidence cannot construct geometry",
    )


def _research_lineage(record, manifest):
    dependencies = {
        item["identifier"]: item for item in manifest["dependencies"]
    }
    for index, lineage in enumerate(record["lineage"]):
        path = "$.lineage[{}]".format(index)
        _require(
            lineage["project_status"] == "reference-only"
            and "templot_reference_data" in lineage["classifications"]
            and lineage["evidence_state"] in ("factual", "derived")
            and lineage["validation_state"] in ("accepted", "unreviewed"),
            "research-lineage-unresolved", path,
            "research fields need resolved reference-only source lineage",
        )
        hashes = set()
        for dependency_id in lineage["dependency_ids"]:
            dependency = dependencies[dependency_id]
            dependency_path = "$.manifest.dependencies[{}]".format(
                dependency_id
            )
            status = dependency.get("project_status")
            _require(
                isinstance(status, dict)
                and status.get("status") == "reference-only"
                and dependency.get("output_affecting") is True
                and dependency.get("role") in (
                    "production-input", "embedded-material", "software-source",
                    "user-input",
                ),
                "research-dependency-role", dependency_path,
                "research inputs must remain output-affecting reference data",
            )
            source = dependency.get("source")
            _require(
                isinstance(source, dict)
                and _text(source.get("creator_or_supplier"))
                and _text(source.get("locator"))
                and _text(source.get("evidence_sha256"))
                and _text(dependency.get("license_expression")),
                "research-source-identity", dependency_path + ".source",
                "each source needs its creator, locator, hash and licence "
                "state",
            )
            hashes.add(source["evidence_sha256"])
            _permissions(dependency, dependency_path)
        _require(
            bool(hashes) and hashes == set(lineage["source_file_sha256s"]),
            "research-source-hash-mismatch", path + ".source_file_sha256s",
            "field hashes must equal the linked source identity hashes",
        )


def _parameter_map(procedure, quantities, expected, path):
    selected = [quantities[key] for key in procedure["parameter_quantity_ids"]]
    purposes = [item["purpose"] for item in selected]
    _require(
        len(purposes) == len(expected) and set(purposes) == set(expected),
        "research-parameter-set", path + ".parameter_quantity_ids",
        "the finite rule requires exactly its named parameter purposes",
    )
    _require(
        all(
            item["quantity_kind"] == "length"
            and item["canonical_unit"] == "mm"
            for item in selected
        ),
        "research-parameter-unit", path + ".parameter_quantity_ids",
        "seat parameters must be full-size lengths in millimetres",
    )
    return {item["purpose"]: item for item in selected}


def _procedures(definition, quantities):
    procedures = definition["procedures"]
    _require(
        len(procedures) == 2,
        "research-procedure-set", "$.definition.procedures",
        "only the explicit frame and seat rules are supported",
    )
    placement, seat = procedures
    _require(
        placement["kind"] == "placement"
        and placement["rule_id"] == CHAIR_SEAT_FRAME_RULE_ID
        and placement["input_ids"] == []
        and len(placement["output_ids"]) == 1
        and seat["kind"] == "cross-section"
        and seat["rule_id"] == CHAIR_SEAT_RESEARCH_RULE_ID
        and seat["input_ids"] == placement["output_ids"]
        and len(seat["output_ids"]) == 1,
        "research-procedure-set", "$.definition.procedures",
        "unsupported seat construction or source-to-chair transform",
    )
    selected = _parameter_map(
        seat, quantities,
        tuple(item.name for item in fields(ChairSeatParameters)),
        "$.definition.procedures[1]",
    )
    frame = _parameter_map(
        placement, quantities, _FRAME_PURPOSES, "$.definition.procedures[0]"
    )
    _require(
        all(frame[key]["quantity_id"] == selected[key]["quantity_id"]
            for key in _FRAME_PURPOSES),
        "research-frame-inputs", "$.definition.procedures[0]",
        "the frame and seat must use the same explicit rail and seat inputs",
    )
    return placement, seat, selected


def _component_contract(definition, placement, seat):
    datums = definition["datums"]
    _require(
        len(datums) == len(CHAIR_REQUIRED_DATUM_ROLES)
        and {item["role"] for item in datums}
        == set(CHAIR_REQUIRED_DATUM_ROLES)
        and all(
            item["datum_kind"] == "plane"
            and item["derivation_procedure_id"] == placement["procedure_id"]
            for item in datums
        ),
        "research-datum-set", "$.definition.datums",
        "five declared chair planes must use the explicit frame rule",
    )
    by_role = {item["role"]: item["datum_id"] for item in datums}
    components = definition["components"]
    _require(
        len(components) == 1
        and components[0]["role"] == "rail-seat"
        and components[0]["presence"] == "present"
        and components[0]["placement_datum_id"]
        == by_role["base-mounting-plane"]
        and components[0]["procedure_ids"] == [seat["procedure_id"]],
        "research-component-set", "$.definition.components",
        "this proof constructs exactly one declared rail-seat component",
    )
    interfaces = definition["rail_interfaces"]
    _require(
        len(interfaces) == 1
        and interfaces[0]["seat_datum_id"] == by_role["rail-seat-plane"]
        and interfaces[0]["gauge_face_datum_id"] == by_role["gauge-face-datum"]
        and interfaces[0]["procedure_ids"] == [seat["procedure_id"]]
        and interfaces[0]["clearance_quantity_ids"] == [],
        "research-interface-set", "$.definition.rail_interfaces",
        "only the declared seat interface without added clearance "
        "is supported",
    )
    return components[0]["component_id"]


def _quantity_coverage(record, quantities, selected):
    lineage = {item["lineage_id"]: item for item in record["lineage"]}
    roots = {item["quantity_id"] for item in selected.values()}
    roots.update(record["validation"]["tolerance_quantity_ids"])
    visited = set()
    visiting = set()

    def visit(identity):
        if identity not in quantities or identity in visited:
            return
        _require(
            identity not in visiting,
            "research-derivation-cycle", "$.lineage",
            "quantity provenance must not contain a derivation cycle",
        )
        visiting.add(identity)
        entry = lineage[quantities[identity]["lineage_id"]]
        derivation = entry["derivation"]
        if derivation is not None:
            for source_id in derivation["input_ids"]:
                visit(source_id)
        visiting.remove(identity)
        visited.add(identity)

    for identity in sorted(roots):
        visit(identity)
    _require(
        visited == set(quantities),
        "research-unused-quantity", "$.definition.quantities",
        "extra quantities must support declared inputs or validation criteria",
    )


def prepare_chair_seat_research(package, manifest_text):
    """Validate one local research request and construct analytical geometry.

    All package and manifest fields remain available without modification.
    Actual source-byte verification and independent review belong to the
    evidence harness. This operation creates no host object or file and
    never changes production admission or acceptance metadata.
    """
    if not isinstance(package, ChairDefinitionPackage):
        raise TypeError("package must be a ChairDefinitionPackage")
    try:
        verify_chair_definition_manifest(package, manifest_text)
    except ChairDefinitionError as error:
        raise ChairResearchError(
            error.code, error.path, error.detail
        ) from error
    manifest = json.loads(manifest_text)
    record = package.to_record()
    _research_metadata(record)
    _research_lineage(record, manifest)
    definition = record["definition"]
    quantities = {
        item["quantity_id"]: item for item in definition["quantities"]
    }
    placement, seat, selected = _procedures(definition, quantities)
    component_id = _component_contract(definition, placement, seat)
    _quantity_coverage(record, quantities, selected)
    try:
        parameters = ChairSeatParameters(**{
            name: Fraction(item["canonical_value"])
            for name, item in selected.items()
        })
        geometry = construct_chair_seat(parameters)
    except (TypeError, ValueError) as error:
        raise ChairResearchError(
            "research-geometry-invalid", "$.definition.quantities", str(error)
        ) from error
    return ChairSeatResearchResult(
        package=package,
        manifest_json=json.dumps(
            manifest, allow_nan=False, ensure_ascii=True,
            separators=(",", ":"), sort_keys=True,
        ),
        manifest_signature=chair_definition_manifest_signature(manifest_text),
        component_id=component_id,
        procedure_id=seat["procedure_id"],
        geometry=geometry,
    )
