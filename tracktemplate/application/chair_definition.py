"""Neutral, deterministic chair-definition package contract.

This module validates and round-trips declarative package data without
importing FreeCAD, Qt, a mesh library, or a geometry kernel.  Phase 4 permits
review loading only: production admission remains deliberately disabled until
the Phase 9 evidence, rights, geometry, and acceptance gates exist.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re


CHAIR_DEFINITION_SCHEMA_ID = "tracktemplate.chair-definition-package"
CHAIR_DEFINITION_SCHEMA_VERSION = 1
CHAIR_DEFINITION_READ_VERSIONS = (1,)
CHAIR_DEFINITION_FRAME_ID = "chair-local-right-handed-v1"
CHAIR_DEFINITION_LENGTH_UNIT = "mm"
CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED = False

CHAIR_CLASSIFICATIONS = (
    "engineering_method",
    "engineering_fact",
    "project_measurement",
    "project_derivation",
    "user_design",
    "templot_source_expression",
    "templot_reference_data",
    "templot_media_output",
    "third_party_evidence",
    "generated_output",
)
CHAIR_EVIDENCE_STATES = (
    "measured",
    "factual",
    "fitted",
    "derived",
    "inferred",
    "unresolved",
    "comparison-only",
)
CHAIR_PROJECT_STATUSES = (
    "project-cleared",
    "restricted",
    "reference-only",
    "unknown",
)
CHAIR_PERMISSION_STATUSES = (
    "permitted",
    "restricted",
    "reference-only",
    "unknown",
    "not-applicable",
)
CHAIR_PERMISSION_FIELDS = (
    "access",
    "adaptation",
    "production_output",
    "redistribution",
    "commercial_use",
    "publication",
)
CHAIR_INTENDED_USES = (
    "private-development",
    "public-redistribution",
    "commercial-production",
    "publication",
    "physical-production",
)
CHAIR_PROCEDURE_KINDS = (
    "profile",
    "cross-section",
    "radius",
    "slope",
    "relationship",
    "symmetry",
    "placement",
    "assembly-constraint",
)
CHAIR_DATUM_ROLES = (
    "base-mounting-plane",
    "longitudinal-chair-centre-plane",
    "rail-section-centre-plane",
    "rail-seat-plane",
    "gauge-face-datum",
    "key-direction",
    "loose-component-direction",
    "component-local-frame",
    "other",
)
CHAIR_REQUIRED_DATUM_ROLES = (
    "base-mounting-plane",
    "longitudinal-chair-centre-plane",
    "rail-section-centre-plane",
    "rail-seat-plane",
    "gauge-face-datum",
)

_SIGNATURE_PREFIX = "sha256:"
_IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
_DECIMAL_PATTERN = r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$"
_LOWER_HEXADECIMAL = "0123456789abcdef"

__all__ = (
    "CHAIR_DEFINITION_SCHEMA_ID",
    "CHAIR_DEFINITION_SCHEMA_VERSION",
    "CHAIR_DEFINITION_READ_VERSIONS",
    "CHAIR_DEFINITION_FRAME_ID",
    "CHAIR_DEFINITION_LENGTH_UNIT",
    "CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED",
    "ChairDefinitionError",
    "ChairDefinitionPackage",
    "chair_definition_manifest_signature",
    "chair_definition_package_from_json",
    "chair_definition_package_status",
    "chair_definition_package_to_json",
    "verify_chair_definition_manifest",
)


class ChairDefinitionError(ValueError):
    """Structured, recoverable failure at the package boundary."""

    def __init__(self, code, path, message):
        self.code = str(code)
        self.path = str(path)
        self.detail = str(message)
        super().__init__("{} at {}: {}".format(self.code, self.path, self.detail))

    def diagnostic(self):
        """Return a host-neutral diagnostic for an adapter or UI."""
        return {
            "code": self.code,
            "path": self.path,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
            "filesystem_mutation": False,
        }


@dataclass(frozen=True)
class ChairDefinitionPackage:
    """One fully validated, immutable package payload.

    ``to_record`` returns a detached copy so callers cannot mutate the
    canonical payload retained by this record.
    """

    package_id: str
    package_version: str
    definition_id: str
    definition_version: str
    prototype_designation: str
    content_signature: str
    project_status: str
    validation_status: str
    acceptance_status: str
    _canonical_json: str = field(repr=False)

    def __post_init__(self):
        record = _json_record(self._canonical_json, "chair-definition package")
        metadata = _validate_package_record(record)
        if _canonical_json(record) != self._canonical_json:
            raise ChairDefinitionError(
                "non-canonical-package",
                "$",
                "ChairDefinitionPackage must retain canonical JSON",
            )
        for name, expected in metadata.items():
            if getattr(self, name) != expected:
                raise ChairDefinitionError(
                    "package-metadata-mismatch",
                    "$." + name,
                    "constructor metadata does not match the validated payload",
                )

    def to_record(self):
        """Return a detached JSON-compatible package record."""
        return json.loads(self._canonical_json)


def _canonical_json(value):
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _signature(value):
    payload = _canonical_json(value).encode("utf-8")
    return _SIGNATURE_PREFIX + hashlib.sha256(payload).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ChairDefinitionError(
                "duplicate-field",
                "$",
                "duplicate JSON object field {!r}".format(key),
            )
        result[key] = value
    return result


def _reject_non_standard_number(value):
    raise ChairDefinitionError(
        "invalid-number",
        "$",
        "non-standard JSON number {!r} is not permitted".format(value),
    )


def _json_record(text, label):
    if not isinstance(text, str):
        raise TypeError("{} must be JSON text".format(label))
    try:
        record = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_non_standard_number,
        )
    except ChairDefinitionError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ChairDefinitionError("invalid-json", "$", str(error)) from error
    return _object(record, "$")


def _object(value, path):
    if not isinstance(value, dict):
        raise ChairDefinitionError("invalid-object", path, "expected a JSON object")
    return value


def _fields(value, expected, path):
    observed = set(value)
    expected = set(expected)
    if observed != expected:
        raise ChairDefinitionError(
            "invalid-fields",
            path,
            "missing {!r}; unexpected {!r}".format(
                sorted(expected - observed),
                sorted(observed - expected),
            ),
        )


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ChairDefinitionError("invalid-text", path, "expected non-empty text")
    return value


def _optional_text(value, path):
    if value is None:
        return None
    return _text(value, path)


def _identifier(value, path):
    result = _text(value, path)
    if re.fullmatch(_IDENTIFIER_PATTERN, result) is None:
        raise ChairDefinitionError(
            "invalid-identifier",
            path,
            "expected a stable identifier",
        )
    return result


def _choice(value, choices, path):
    if value not in choices:
        raise ChairDefinitionError(
            "invalid-choice",
            path,
            "expected one of {!r}; observed {!r}".format(list(choices), value),
        )
    return value


def _strings(value, path, choices=None, nonempty=False, identifiers=False):
    if not isinstance(value, list):
        raise ChairDefinitionError("invalid-list", path, "expected an array")
    if nonempty and not value:
        raise ChairDefinitionError("invalid-list", path, "array must not be empty")
    result = []
    for index, item in enumerate(value):
        item_path = "{}[{}]".format(path, index)
        item = _identifier(item, item_path) if identifiers else _text(item, item_path)
        if choices is not None:
            _choice(item, choices, item_path)
        result.append(item)
    if len(result) != len(set(result)):
        raise ChairDefinitionError(
            "duplicate-identity",
            path,
            "array must not contain duplicate values",
        )
    return tuple(result)


def _ordered_choices(values, choices, path):
    indexes = [choices.index(value) for value in values]
    if indexes != sorted(indexes):
        raise ChairDefinitionError(
            "invalid-order",
            path,
            "values must follow the declared schema order",
        )


def _lower_sha256(value, path):
    value = _text(value, path)
    if len(value) != 64 or any(item not in _LOWER_HEXADECIMAL for item in value):
        raise ChairDefinitionError(
            "invalid-sha256",
            path,
            "expected 64 lower-case hexadecimal characters",
        )
    return value


def _content_signature(value, path):
    value = _text(value, path)
    if (
        not value.startswith(_SIGNATURE_PREFIX)
        or len(value) != len(_SIGNATURE_PREFIX) + 64
        or any(
            item not in _LOWER_HEXADECIMAL
            for item in value[len(_SIGNATURE_PREFIX):]
        )
    ):
        raise ChairDefinitionError(
            "invalid-signature",
            path,
            "expected sha256 followed by 64 lower-case hexadecimal characters",
        )
    return value


def _date(value, path):
    value = _text(value, path)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ChairDefinitionError(
            "invalid-date",
            path,
            "expected an ISO date in YYYY-MM-DD form",
        ) from error
    if parsed.isoformat() != value:
        raise ChairDefinitionError(
            "invalid-date",
            path,
            "expected an ISO date in YYYY-MM-DD form",
        )
    return value


def _decimal(value, path):
    if not isinstance(value, str) or re.fullmatch(_DECIMAL_PATTERN, value) is None:
        raise ChairDefinitionError(
            "invalid-decimal",
            path,
            "expected a finite base-10 decimal string without exponent notation",
        )
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ChairDefinitionError(
            "invalid-decimal",
            path,
            "expected a finite base-10 decimal string",
        ) from error
    if not result.is_finite():
        raise ChairDefinitionError("invalid-decimal", path, "value must be finite")
    return result


def _length_factor(unit, path):
    if unit == "mm":
        return Decimal("1")
    if unit == "cm":
        return Decimal("10")
    if unit == "m":
        return Decimal("1000")
    if unit == "in":
        return Decimal("25.4")
    if unit == "ft":
        return Decimal("304.8")
    raise ChairDefinitionError(
        "unsupported-unit",
        path,
        "supported source length units are mm, cm, m, in and ft",
    )


def _lineage_reference(record, path):
    return _identifier(record.get("lineage_id"), path + ".lineage_id")


def _quantity(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "quantity_id",
            "purpose",
            "quantity_kind",
            "source_value",
            "source_unit",
            "canonical_value",
            "canonical_unit",
            "uncertainty",
            "lineage_id",
        ),
        path,
    )
    quantity_id = _identifier(record["quantity_id"], path + ".quantity_id")
    _identifier(record["purpose"], path + ".purpose")
    kind = _choice(
        record["quantity_kind"],
        ("length", "angle", "dimensionless"),
        path + ".quantity_kind",
    )
    source_value = _decimal(record["source_value"], path + ".source_value")
    canonical_value = _decimal(
        record["canonical_value"], path + ".canonical_value"
    )
    source_unit = _text(record["source_unit"], path + ".source_unit")
    canonical_unit = _text(record["canonical_unit"], path + ".canonical_unit")
    if kind == "length":
        if canonical_unit != CHAIR_DEFINITION_LENGTH_UNIT:
            raise ChairDefinitionError(
                "unsupported-unit",
                path + ".canonical_unit",
                "canonical length unit must be mm",
            )
        expected = source_value * _length_factor(source_unit, path + ".source_unit")
        if expected != canonical_value:
            raise ChairDefinitionError(
                "unit-conversion-mismatch",
                path + ".canonical_value",
                "canonical millimetre value does not equal the exact source conversion",
            )
    elif kind == "angle":
        if source_unit not in ("deg", "rad") or canonical_unit != source_unit:
            raise ChairDefinitionError(
                "unsupported-unit",
                path + ".canonical_unit",
                "v1 angles preserve an exact deg or rad source value without conversion",
            )
        if source_value != canonical_value:
            raise ChairDefinitionError(
                "unit-conversion-mismatch",
                path + ".canonical_value",
                "v1 angle canonical value must equal its exact source value",
            )
    else:
        if source_unit != "1" or canonical_unit != "1":
            raise ChairDefinitionError(
                "unsupported-unit",
                path + ".canonical_unit",
                "dimensionless quantities must use unit 1",
            )
        if source_value != canonical_value:
            raise ChairDefinitionError(
                "unit-conversion-mismatch",
                path + ".canonical_value",
                "dimensionless canonical value must equal its exact source value",
            )

    uncertainty = record["uncertainty"]
    if uncertainty is not None:
        uncertainty = _object(uncertainty, path + ".uncertainty")
        _fields(uncertainty, ("value", "unit"), path + ".uncertainty")
        uncertainty_value = _decimal(
            uncertainty["value"], path + ".uncertainty.value"
        )
        if uncertainty_value < 0:
            raise ChairDefinitionError(
                "invalid-uncertainty",
                path + ".uncertainty.value",
                "uncertainty must not be negative",
            )
        if uncertainty["unit"] != canonical_unit:
            raise ChairDefinitionError(
                "invalid-uncertainty",
                path + ".uncertainty.unit",
                "uncertainty must use the quantity canonical unit",
            )
    return quantity_id, _lineage_reference(record, path)


def _record_array(value, path, id_field, validator, nonempty=False):
    if not isinstance(value, list):
        raise ChairDefinitionError("invalid-list", path, "expected an array")
    if nonempty and not value:
        raise ChairDefinitionError("invalid-list", path, "array must not be empty")
    results = []
    lineage_ids = []
    for index, item in enumerate(value):
        result = validator(item, "{}[{}]".format(path, index))
        results.append(result[0])
        lineage_ids.append(result[1])
    if len(results) != len(set(results)):
        raise ChairDefinitionError(
            "duplicate-identity", path, "record identities must be unique"
        )
    if results != sorted(results):
        raise ChairDefinitionError(
            "invalid-order",
            path,
            "records must be ordered by {}".format(id_field),
        )
    return tuple(results), tuple(lineage_ids)


def _datum(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "datum_id",
            "role",
            "datum_kind",
            "derivation_procedure_id",
            "lineage_id",
        ),
        path,
    )
    datum_id = _identifier(record["datum_id"], path + ".datum_id")
    _choice(record["role"], CHAIR_DATUM_ROLES, path + ".role")
    _choice(
        record["datum_kind"],
        ("point", "axis", "plane", "direction", "frame"),
        path + ".datum_kind",
    )
    if record["derivation_procedure_id"] is not None:
        _identifier(
            record["derivation_procedure_id"],
            path + ".derivation_procedure_id",
        )
    return datum_id, _lineage_reference(record, path)


def _procedure(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "procedure_id",
            "kind",
            "rule_id",
            "input_ids",
            "parameter_quantity_ids",
            "output_ids",
            "lineage_id",
        ),
        path,
    )
    procedure_id = _identifier(record["procedure_id"], path + ".procedure_id")
    _choice(record["kind"], CHAIR_PROCEDURE_KINDS, path + ".kind")
    _identifier(record["rule_id"], path + ".rule_id")
    _strings(record["input_ids"], path + ".input_ids", identifiers=True)
    _strings(
        record["parameter_quantity_ids"],
        path + ".parameter_quantity_ids",
        identifiers=True,
    )
    _strings(
        record["output_ids"],
        path + ".output_ids",
        nonempty=True,
        identifiers=True,
    )
    return procedure_id, _lineage_reference(record, path)


def _component(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "component_id",
            "role",
            "presence",
            "placement_datum_id",
            "procedure_ids",
            "absence_reason",
            "lineage_id",
        ),
        path,
    )
    component_id = _identifier(record["component_id"], path + ".component_id")
    _identifier(record["role"], path + ".role")
    presence = _choice(
        record["presence"], ("present", "absent"), path + ".presence"
    )
    _identifier(record["placement_datum_id"], path + ".placement_datum_id")
    procedures = _strings(
        record["procedure_ids"], path + ".procedure_ids", identifiers=True
    )
    absence_reason = _optional_text(record["absence_reason"], path + ".absence_reason")
    if presence == "present" and (not procedures or absence_reason is not None):
        raise ChairDefinitionError(
            "inconsistent-component-presence",
            path,
            "present components require procedures and no absence reason",
        )
    if presence == "absent" and (procedures or absence_reason is None):
        raise ChairDefinitionError(
            "inconsistent-component-presence",
            path,
            "absent components require an explicit reason and no procedures",
        )
    return component_id, _lineage_reference(record, path)


def _rail_interface(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "interface_id",
            "rail_section_id",
            "seat_datum_id",
            "gauge_face_datum_id",
            "orientation",
            "procedure_ids",
            "clearance_quantity_ids",
            "lineage_id",
        ),
        path,
    )
    interface_id = _identifier(record["interface_id"], path + ".interface_id")
    _identifier(record["rail_section_id"], path + ".rail_section_id")
    _identifier(record["seat_datum_id"], path + ".seat_datum_id")
    _identifier(record["gauge_face_datum_id"], path + ".gauge_face_datum_id")
    _choice(record["orientation"], ("gauge-to-field",), path + ".orientation")
    _strings(
        record["procedure_ids"],
        path + ".procedure_ids",
        nonempty=True,
        identifiers=True,
    )
    _strings(
        record["clearance_quantity_ids"],
        path + ".clearance_quantity_ids",
        identifiers=True,
    )
    return interface_id, _lineage_reference(record, path)


def _manufacturing_profile(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "profile_id",
            "description",
            "model_scale",
            "quantities",
            "lineage_id",
        ),
        path,
    )
    profile_id = _identifier(record["profile_id"], path + ".profile_id")
    _text(record["description"], path + ".description")
    if _decimal(record["model_scale"], path + ".model_scale") <= 0:
        raise ChairDefinitionError(
            "invalid-model-scale", path + ".model_scale", "scale must be positive"
        )
    quantities, quantity_lineages = _record_array(
        record["quantities"],
        path + ".quantities",
        "quantity_id",
        _quantity,
    )
    return (
        profile_id,
        _lineage_reference(record, path),
        quantities,
        quantity_lineages,
    )


def _lineage(record, path):
    record = _object(record, path)
    _fields(
        record,
        (
            "lineage_id",
            "classifications",
            "evidence_state",
            "dependency_ids",
            "source_file_sha256s",
            "derivation",
            "assumptions",
            "project_status",
            "validation_state",
        ),
        path,
    )
    lineage_id = _identifier(record["lineage_id"], path + ".lineage_id")
    classifications = _strings(
        record["classifications"],
        path + ".classifications",
        choices=CHAIR_CLASSIFICATIONS,
        nonempty=True,
    )
    _ordered_choices(classifications, CHAIR_CLASSIFICATIONS, path + ".classifications")
    state = _choice(
        record["evidence_state"],
        CHAIR_EVIDENCE_STATES,
        path + ".evidence_state",
    )
    _strings(
        record["dependency_ids"],
        path + ".dependency_ids",
        nonempty=True,
        identifiers=True,
    )
    hashes = _strings(record["source_file_sha256s"], path + ".source_file_sha256s")
    for index, value in enumerate(hashes):
        _lower_sha256(value, "{}.source_file_sha256s[{}]".format(path, index))
    derivation = record["derivation"]
    if derivation is not None:
        derivation = _object(derivation, path + ".derivation")
        _fields(derivation, ("rule_id", "input_ids"), path + ".derivation")
        _identifier(derivation["rule_id"], path + ".derivation.rule_id")
        _strings(
            derivation["input_ids"],
            path + ".derivation.input_ids",
            identifiers=True,
        )
    if state == "derived" and derivation is None:
        raise ChairDefinitionError(
            "missing-derivation",
            path + ".derivation",
            "derived lineage requires a versioned rule and its inputs",
        )
    _strings(record["assumptions"], path + ".assumptions")
    _choice(
        record["project_status"],
        CHAIR_PROJECT_STATUSES,
        path + ".project_status",
    )
    _choice(
        record["validation_state"],
        ("accepted", "blocked", "rejected", "unreviewed"),
        path + ".validation_state",
    )
    return lineage_id, lineage_id


def _validate_frame(frame):
    path = "$.definition.frame"
    frame = _object(frame, path)
    expected = {
        "frame_id": CHAIR_DEFINITION_FRAME_ID,
        "handedness": "right",
        "x_axis": "nominal-rail-direction",
        "y_axis": "gauge-to-field",
        "z_axis": "up-from-base-mounting-plane",
        "origin": (
            "longitudinal-chair-centre-plane/rail-section-centre-plane/"
            "base-mounting-plane"
        ),
    }
    _fields(frame, expected, path)
    for field, required in expected.items():
        if frame[field] != required:
            raise ChairDefinitionError(
                "unsupported-coordinate-frame",
                path + "." + field,
                "expected {!r}; observed {!r}".format(required, frame[field]),
            )


def _validate_package_metadata(record):
    path = "$.package"
    record = _object(record, path)
    _fields(
        record,
        (
            "package_id",
            "package_version",
            "license_expression",
            "intended_uses",
            "permissions",
            "project_status",
        ),
        path,
    )
    package_id = _identifier(record["package_id"], path + ".package_id")
    package_version = _text(record["package_version"], path + ".package_version")
    _text(record["license_expression"], path + ".license_expression")
    intended_uses = _strings(
        record["intended_uses"],
        path + ".intended_uses",
        choices=CHAIR_INTENDED_USES,
        nonempty=True,
    )
    _ordered_choices(intended_uses, CHAIR_INTENDED_USES, path + ".intended_uses")
    permissions = _object(record["permissions"], path + ".permissions")
    _fields(permissions, CHAIR_PERMISSION_FIELDS, path + ".permissions")
    for field in CHAIR_PERMISSION_FIELDS:
        _choice(
            permissions[field],
            CHAIR_PERMISSION_STATUSES,
            "{}.permissions.{}".format(path, field),
        )
    project_status = _choice(
        record["project_status"],
        CHAIR_PROJECT_STATUSES,
        path + ".project_status",
    )
    return package_id, package_version, project_status


def _validate_definition(record):
    path = "$.definition"
    record = _object(record, path)
    _fields(
        record,
        (
            "definition_id",
            "definition_version",
            "prototype_designation",
            "description",
            "lineage_id",
            "canonical_length_unit",
            "frame",
            "quantities",
            "datums",
            "rail_interfaces",
            "components",
            "procedures",
        ),
        path,
    )
    definition_id = _identifier(record["definition_id"], path + ".definition_id")
    definition_version = _text(
        record["definition_version"], path + ".definition_version"
    )
    designation = _text(
        record["prototype_designation"], path + ".prototype_designation"
    )
    _text(record["description"], path + ".description")
    definition_lineage = _lineage_reference(record, path)
    if record["canonical_length_unit"] != CHAIR_DEFINITION_LENGTH_UNIT:
        raise ChairDefinitionError(
            "unsupported-unit",
            path + ".canonical_length_unit",
            "canonical chair lengths must use mm",
        )
    _validate_frame(record["frame"])

    quantity_ids, quantity_lineages = _record_array(
        record["quantities"], path + ".quantities", "quantity_id", _quantity, True
    )
    datum_ids, datum_lineages = _record_array(
        record["datums"], path + ".datums", "datum_id", _datum, True
    )
    interface_ids, interface_lineages = _record_array(
        record["rail_interfaces"],
        path + ".rail_interfaces",
        "interface_id",
        _rail_interface,
        True,
    )
    component_ids, component_lineages = _record_array(
        record["components"],
        path + ".components",
        "component_id",
        _component,
        True,
    )
    procedure_ids, procedure_lineages = _record_array(
        record["procedures"],
        path + ".procedures",
        "procedure_id",
        _procedure,
        True,
    )

    roles = {item["role"] for item in record["datums"]}
    missing_roles = sorted(set(CHAIR_REQUIRED_DATUM_ROLES) - roles)
    if missing_roles:
        raise ChairDefinitionError(
            "missing-required-datum",
            path + ".datums",
            "missing roles {!r}".format(missing_roles),
        )
    if not any(item["presence"] == "present" for item in record["components"]):
        raise ChairDefinitionError(
            "missing-present-component",
            path + ".components",
            "at least one constituent must be present",
        )

    quantity_set = set(quantity_ids)
    datum_set = set(datum_ids)
    procedure_set = set(procedure_ids)
    base_ids = quantity_set | datum_set | set(interface_ids) | set(component_ids)
    available_ids = set(base_ids)
    output_ids = set()
    for index, procedure in enumerate(record["procedures"]):
        procedure_path = "{}.procedures[{}]".format(path, index)
        for reference in procedure["input_ids"]:
            if reference not in available_ids:
                raise ChairDefinitionError(
                    "missing-reference",
                    procedure_path + ".input_ids",
                    "unknown or forward input {!r}".format(reference),
                )
        for reference in procedure["parameter_quantity_ids"]:
            if reference not in quantity_set:
                raise ChairDefinitionError(
                    "missing-reference",
                    procedure_path + ".parameter_quantity_ids",
                    "unknown prototype quantity {!r}".format(reference),
                )
        for output_id in procedure["output_ids"]:
            if output_id in available_ids or output_id in output_ids:
                raise ChairDefinitionError(
                    "duplicate-identity",
                    procedure_path + ".output_ids",
                    "procedure output {!r} is not unique".format(output_id),
                )
            output_ids.add(output_id)
            available_ids.add(output_id)

    for index, datum in enumerate(record["datums"]):
        reference = datum["derivation_procedure_id"]
        if reference is not None and reference not in procedure_set:
            raise ChairDefinitionError(
                "missing-reference",
                "{}.datums[{}].derivation_procedure_id".format(path, index),
                "unknown procedure {!r}".format(reference),
            )
    for index, component in enumerate(record["components"]):
        component_path = "{}.components[{}]".format(path, index)
        if component["placement_datum_id"] not in datum_set:
            raise ChairDefinitionError(
                "missing-reference",
                component_path + ".placement_datum_id",
                "unknown datum {!r}".format(component["placement_datum_id"]),
            )
        for reference in component["procedure_ids"]:
            if reference not in procedure_set:
                raise ChairDefinitionError(
                    "missing-reference",
                    component_path + ".procedure_ids",
                    "unknown procedure {!r}".format(reference),
                )
    for index, interface in enumerate(record["rail_interfaces"]):
        interface_path = "{}.rail_interfaces[{}]".format(path, index)
        for field in ("seat_datum_id", "gauge_face_datum_id"):
            if interface[field] not in datum_set:
                raise ChairDefinitionError(
                    "missing-reference",
                    interface_path + "." + field,
                    "unknown datum {!r}".format(interface[field]),
                )
        for reference in interface["procedure_ids"]:
            if reference not in procedure_set:
                raise ChairDefinitionError(
                    "missing-reference",
                    interface_path + ".procedure_ids",
                    "unknown procedure {!r}".format(reference),
                )
        for reference in interface["clearance_quantity_ids"]:
            if reference not in quantity_set:
                raise ChairDefinitionError(
                    "missing-reference",
                    interface_path + ".clearance_quantity_ids",
                    "unknown quantity {!r}".format(reference),
                )

    lineage_ids = (
        (definition_lineage,)
        + quantity_lineages
        + datum_lineages
        + interface_lineages
        + component_lineages
        + procedure_lineages
    )
    all_ids = (
        {definition_id}
        | quantity_set
        | datum_set
        | set(interface_ids)
        | set(component_ids)
        | procedure_set
        | output_ids
    )
    return (
        definition_id,
        definition_version,
        designation,
        lineage_ids,
        all_ids,
        quantity_set,
    )


def _validate_validation(record, known_quantity_ids):
    path = "$.validation"
    record = _object(record, path)
    _fields(
        record,
        (
            "status",
            "tolerance_profile_id",
            "tolerance_quantity_ids",
            "finding_ids",
            "evidence_ids",
        ),
        path,
    )
    status = _choice(
        record["status"], ("passed", "failed", "blocked", "not-run"), path + ".status"
    )
    _identifier(record["tolerance_profile_id"], path + ".tolerance_profile_id")
    tolerance_ids = _strings(
        record["tolerance_quantity_ids"],
        path + ".tolerance_quantity_ids",
        identifiers=True,
    )
    for reference in tolerance_ids:
        if reference not in known_quantity_ids:
            raise ChairDefinitionError(
                "missing-reference",
                path + ".tolerance_quantity_ids",
                "unknown quantity {!r}".format(reference),
            )
    _strings(record["finding_ids"], path + ".finding_ids", identifiers=True)
    _strings(record["evidence_ids"], path + ".evidence_ids", identifiers=True)
    return status


def _validate_acceptance(record):
    path = "$.acceptance"
    record = _object(record, path)
    _fields(
        record,
        ("status", "accepted_by", "accepted_on", "decision_reference"),
        path,
    )
    status = _choice(
        record["status"], ("accepted", "not-accepted"), path + ".status"
    )
    if status == "accepted":
        _text(record["accepted_by"], path + ".accepted_by")
        _date(record["accepted_on"], path + ".accepted_on")
        _text(record["decision_reference"], path + ".decision_reference")
    else:
        for field in ("accepted_by", "accepted_on", "decision_reference"):
            if record[field] is not None:
                raise ChairDefinitionError(
                    "invalid-acceptance",
                    path + "." + field,
                    "non-accepted packages must use null acceptance details",
                )
    return status


def _validate_manifest_link(record):
    path = "$.dependency_manifest"
    record = _object(record, path)
    _fields(
        record,
        ("manifest_id", "subject_id", "subject_version", "content_signature"),
        path,
    )
    _identifier(record["manifest_id"], path + ".manifest_id")
    _identifier(record["subject_id"], path + ".subject_id")
    _text(record["subject_version"], path + ".subject_version")
    _content_signature(record["content_signature"], path + ".content_signature")


def _validate_package_record(record):
    _fields(
        record,
        (
            "schema",
            "schema_version",
            "content_signature",
            "package",
            "definition",
            "manufacturing_profiles",
            "lineage",
            "validation",
            "acceptance",
            "dependency_manifest",
        ),
        "$",
    )
    if record["schema"] != CHAIR_DEFINITION_SCHEMA_ID:
        raise ChairDefinitionError(
            "unsupported-schema",
            "$.schema",
            "expected {!r}; observed {!r}".format(
                CHAIR_DEFINITION_SCHEMA_ID, record["schema"]
            ),
        )
    version = record["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise ChairDefinitionError(
            "invalid-schema-version",
            "$.schema_version",
            "expected an integer schema version",
        )
    if version not in CHAIR_DEFINITION_READ_VERSIONS:
        raise ChairDefinitionError(
            "unsupported-schema-version",
            "$.schema_version",
            "supported versions are {!r}; observed {!r}".format(
                list(CHAIR_DEFINITION_READ_VERSIONS), version
            ),
        )
    observed_signature = _content_signature(
        record["content_signature"], "$.content_signature"
    )
    unsigned = dict(record)
    del unsigned["content_signature"]
    expected_signature = _signature(unsigned)
    if observed_signature != expected_signature:
        raise ChairDefinitionError(
            "content-signature-mismatch",
            "$.content_signature",
            "package content does not match its signature",
        )

    package_id, package_version, project_status = _validate_package_metadata(
        record["package"]
    )
    (
        definition_id,
        definition_version,
        designation,
        definition_lineages,
        definition_ids,
        prototype_quantity_ids,
    ) = _validate_definition(record["definition"])

    manufacturing = record["manufacturing_profiles"]
    if not isinstance(manufacturing, list):
        raise ChairDefinitionError(
            "invalid-list", "$.manufacturing_profiles", "expected an array"
        )
    manufacturing_ids = []
    manufacturing_lineages = []
    manufacturing_quantity_ids = set()
    for index, item in enumerate(manufacturing):
        (
            profile_id,
            lineage_id,
            quantity_ids,
            quantity_lineages,
        ) = _manufacturing_profile(
            item, "$.manufacturing_profiles[{}]".format(index)
        )
        manufacturing_ids.append(profile_id)
        manufacturing_lineages.append(lineage_id)
        manufacturing_lineages.extend(quantity_lineages)
        for quantity_id in quantity_ids:
            if quantity_id in definition_ids or quantity_id in manufacturing_quantity_ids:
                raise ChairDefinitionError(
                    "duplicate-identity",
                    "$.manufacturing_profiles[{}].quantities".format(index),
                    "quantity {!r} is not globally unique".format(quantity_id),
                )
            manufacturing_quantity_ids.add(quantity_id)
    if len(manufacturing_ids) != len(set(manufacturing_ids)):
        raise ChairDefinitionError(
            "duplicate-identity",
            "$.manufacturing_profiles",
            "profile identities must be unique",
        )
    if manufacturing_ids != sorted(manufacturing_ids):
        raise ChairDefinitionError(
            "invalid-order",
            "$.manufacturing_profiles",
            "records must be ordered by profile_id",
        )

    lineage_ids, _unused = _record_array(
        record["lineage"], "$.lineage", "lineage_id", _lineage, True
    )
    referenced_lineages = set(definition_lineages) | set(manufacturing_lineages)
    if referenced_lineages != set(lineage_ids):
        raise ChairDefinitionError(
            "lineage-coverage-mismatch",
            "$.lineage",
            "missing references {!r}; unused records {!r}".format(
                sorted(referenced_lineages - set(lineage_ids)),
                sorted(set(lineage_ids) - referenced_lineages),
            ),
        )

    known_derivation_inputs = (
        definition_ids
        | set(manufacturing_ids)
        | manufacturing_quantity_ids
    )
    for index, lineage in enumerate(record["lineage"]):
        derivation = lineage["derivation"]
        if derivation is None:
            continue
        missing = sorted(
            set(derivation["input_ids"]) - known_derivation_inputs
        )
        if missing:
            raise ChairDefinitionError(
                "missing-reference",
                "$.lineage[{}].derivation.input_ids".format(index),
                "unknown derivation inputs {!r}".format(missing),
            )

    validation_status = _validate_validation(
        record["validation"],
        prototype_quantity_ids | manufacturing_quantity_ids,
    )
    acceptance_status = _validate_acceptance(record["acceptance"])
    _validate_manifest_link(record["dependency_manifest"])
    if record["dependency_manifest"]["subject_id"] != package_id:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.dependency_manifest.subject_id",
            "manifest subject must equal package_id",
        )
    if record["dependency_manifest"]["subject_version"] != package_version:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.dependency_manifest.subject_version",
            "manifest subject version must equal package_version",
        )
    if set(manufacturing_ids) & definition_ids:
        raise ChairDefinitionError(
            "duplicate-identity",
            "$.manufacturing_profiles",
            "manufacturing profile identities collide with definition identities",
        )
    return {
        "package_id": package_id,
        "package_version": package_version,
        "definition_id": definition_id,
        "definition_version": definition_version,
        "prototype_designation": designation,
        "content_signature": observed_signature,
        "project_status": project_status,
        "validation_status": validation_status,
        "acceptance_status": acceptance_status,
    }


def chair_definition_package_from_json(text, dependency_manifest_text=None):
    """Parse and validate one complete v1 package before any host mutation.

    Explicit unresolved/review states are preserved for inspection.  They are
    never production-admissible; ``chair_definition_package_status`` reports
    that fail-closed boundary.
    """
    record = _json_record(text, "chair-definition package")
    metadata = _validate_package_record(record)
    canonical = _canonical_json(record)
    package = ChairDefinitionPackage(_canonical_json=canonical, **metadata)
    if dependency_manifest_text is not None:
        verify_chair_definition_manifest(package, dependency_manifest_text)
    return package


def chair_definition_package_to_json(package):
    """Return deterministic UTF-8-compatible canonical JSON text."""
    if not isinstance(package, ChairDefinitionPackage):
        raise TypeError("package must be a ChairDefinitionPackage")
    return package._canonical_json


def chair_definition_manifest_signature(text):
    """Return the canonical content signature of an external manifest."""
    return _signature(_json_record(text, "dependency manifest"))


def _manifest_record(package, text):
    manifest = _json_record(text, "dependency manifest")
    link = package.to_record()["dependency_manifest"]
    _fields(
        manifest,
        (
            "schema_version",
            "manifest_id",
            "manifest_kind",
            "audit_scope",
            "subject",
            "intended_uses",
            "dependencies",
            "non_copyright_review",
            "project_status",
        ),
        "$.manifest",
    )
    if manifest["schema_version"] != 1:
        raise ChairDefinitionError(
            "unsupported-dependency-manifest-version",
            "$.manifest.schema_version",
            "chair-package v1 requires dependency-manifest schema version 1",
        )
    if manifest["manifest_kind"] != "package":
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.manifest_kind",
            "chair definitions require a package manifest",
        )
    subject = _object(manifest["subject"], "$.manifest.subject")
    _fields(
        subject,
        ("identifier", "version", "description", "package_license"),
        "$.manifest.subject",
    )
    _identifier(subject["identifier"], "$.manifest.subject.identifier")
    _text(subject["version"], "$.manifest.subject.version")
    _text(subject["description"], "$.manifest.subject.description")
    _text(subject["package_license"], "$.manifest.subject.package_license")
    observed_signature = _signature(manifest)
    if observed_signature != link["content_signature"]:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.dependency_manifest.content_signature",
            "linked manifest content does not match its signature",
        )
    if manifest.get("manifest_id") != link["manifest_id"]:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.dependency_manifest.manifest_id",
            "linked manifest identity does not match",
        )
    if subject.get("identifier") != package.package_id:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.subject.identifier",
            "manifest subject does not match package identity",
        )
    if subject.get("version") != package.package_version:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.subject.version",
            "manifest subject version does not match package version",
        )
    package_record = package.to_record()
    package_metadata = package_record["package"]
    if subject.get("package_license") != package_metadata["license_expression"]:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.subject.package_license",
            "manifest and package licence expressions differ",
        )
    intended_uses = _strings(
        manifest["intended_uses"],
        "$.manifest.intended_uses",
        choices=CHAIR_INTENDED_USES,
        nonempty=True,
    )
    _ordered_choices(
        intended_uses, CHAIR_INTENDED_USES, "$.manifest.intended_uses"
    )
    if list(intended_uses) != package_metadata["intended_uses"]:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.intended_uses",
            "manifest and package intended uses differ",
        )
    manifest_decision = _object(
        manifest["project_status"], "$.manifest.project_status"
    )
    manifest_status = _choice(
        manifest_decision.get("status"),
        CHAIR_PROJECT_STATUSES,
        "$.manifest.project_status.status",
    )
    if manifest_status != package.project_status:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.project_status.status",
            "manifest and package project statuses differ",
        )
    dependencies = manifest["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        raise ChairDefinitionError(
            "dependency-manifest-mismatch",
            "$.manifest.dependencies",
            "manifest dependencies must be a non-empty array",
        )
    dependency_map = {}
    for index, item in enumerate(dependencies):
        path = "$.manifest.dependencies[{}]".format(index)
        item = _object(item, path)
        dependency_id = _identifier(item.get("identifier"), path + ".identifier")
        if dependency_id in dependency_map:
            raise ChairDefinitionError(
                "dependency-manifest-mismatch",
                path + ".identifier",
                "manifest dependency identities must be unique",
            )
        classifications = _strings(
            item.get("classifications"),
            path + ".classifications",
            choices=CHAIR_CLASSIFICATIONS,
            nonempty=True,
        )
        dependency_map[dependency_id] = set(classifications)
    dependency_ids = set(dependency_map)
    for index, lineage in enumerate(package_record["lineage"]):
        missing = sorted(set(lineage["dependency_ids"]) - dependency_ids)
        if missing:
            raise ChairDefinitionError(
                "dependency-manifest-mismatch",
                "$.lineage[{}].dependency_ids".format(index),
                "manifest is missing dependencies {!r}".format(missing),
            )
        available_classifications = set()
        for dependency_id in lineage["dependency_ids"]:
            available_classifications.update(dependency_map[dependency_id])
        missing_classifications = sorted(
            set(lineage["classifications"]) - available_classifications
        )
        if missing_classifications:
            raise ChairDefinitionError(
                "dependency-manifest-mismatch",
                "$.lineage[{}].classifications".format(index),
                "manifest dependencies do not support classifications {!r}".format(
                    missing_classifications
                ),
            )
    return manifest


def verify_chair_definition_manifest(package, dependency_manifest_text):
    """Verify exact manifest linkage and package-level agreement.

    The repository's dependency-manifest validator remains the separate
    semantic project-clearance gate; this function prevents identity, version,
    content, licence, intended-use, status, and dependency-link drift.
    """
    if not isinstance(package, ChairDefinitionPackage):
        raise TypeError("package must be a ChairDefinitionPackage")
    _manifest_record(package, dependency_manifest_text)
    return None


def chair_definition_package_status(package, dependency_manifest_text=None):
    """Return the fail-closed Phase 4 production-admission disposition."""
    if not isinstance(package, ChairDefinitionPackage):
        raise TypeError("package must be a ChairDefinitionPackage")
    findings = []
    if not CHAIR_DEFINITION_PRODUCTION_ADMISSION_ENABLED:
        findings.append("phase9-production-admission-not-enabled")
    if dependency_manifest_text is None:
        findings.append("dependency-manifest-not-verified")
    else:
        try:
            _manifest_record(package, dependency_manifest_text)
        except ChairDefinitionError:
            findings.append("dependency-manifest-mismatch")
    record = package.to_record()
    metadata = record["package"]
    if package.project_status != "project-cleared":
        findings.append("package-not-project-cleared")
    if metadata["license_expression"].upper() == "NOASSERTION":
        findings.append("package-licence-unresolved")
    if record["validation"]["status"] != "passed":
        findings.append("package-validation-not-passed")
    if package.acceptance_status != "accepted":
        findings.append("package-not-accepted")
    for lineage in record["lineage"]:
        if lineage["evidence_state"] in (
            "inferred",
            "unresolved",
            "comparison-only",
        ):
            findings.append("output-lineage-not-resolved")
        if lineage["project_status"] != "project-cleared":
            findings.append("output-lineage-not-project-cleared")
        if lineage["validation_state"] != "accepted":
            findings.append("output-lineage-not-accepted")
    return {
        "status": "blocked" if findings else "admissible",
        "findings": tuple(dict.fromkeys(findings)),
        "production_geometry_authorized": not findings,
        "document_mutation_authorized": not findings,
        "filesystem_mutation_authorized": not findings,
    }
