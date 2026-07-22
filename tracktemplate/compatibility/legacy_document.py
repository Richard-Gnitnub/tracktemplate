"""Read-only B14/B15 legacy-document ingress inspection.

This module implements only the outer compatibility preflight.  It never
authorises or performs migration: every entity-family migration remains
blocked until that family has its own accepted Phase 4 fixture.
"""

from dataclasses import dataclass
import json


LEGACY_INSPECTION_SCHEMA_ID = "tracktemplate.legacy-document-inspection"
LEGACY_INSPECTION_SCHEMA_VERSION = 1
COMPATIBILITY_CONTRACT_ID = (
    "tracktemplate:phase1:runtime-and-legacy-compatibility:1"
)
SUPPORTED_MIGRATION_FAMILIES = ()

STATUS_SUPPORTED = "supported-migration-source"
STATUS_INSPECTION_ONLY = "inspection-only"
STATUS_BLOCKED = "blocked-corrupt-or-conflicting"

VERSION_FIELDS = ("macro_version", "source_macro_version")
RECOGNISED_LEGACY_JSON_PROPERTIES = (
    "AssemblyLabelConfigurationJSON",
    "B3OperationsJSON",
    "B3TimberRecordsJSON",
    "B4HybridResultSummaryJSON",
    "B4TimberRecordsJSON",
    "Chair2DLayoutResultJSON",
    "ChairAnalysisResultJSON",
    "ChairAnalysisSettingsJSON",
    "ChairModelSupportResultJSON",
    "ChairSolidResultJSON",
    "CrossoverB3ResultJSON",
    "CrossoverB3SettingsJSON",
    "CrossoverB4ResultJSON",
    "CrossoverB4SettingsJSON",
    "CrossoverConfigurationJSON",
    "CrossoverConfigurationsJSON",
    "CrossoverHostIntegrationJSON",
    "CrossoverInternalTurnoutConfigurationJSON",
    "CrossoverSharedTimberResultJSON",
    "CrossoverSharedTimberSettingsJSON",
    "CrossoverTimberAnalysisResultJSON",
    "CrossoverTimberAnalysisSettingsJSON",
    "FormationConfigurationJSON",
    "LastAcceptedInputConfigurationJSON",
    "LastAcceptedInputConfigurationsByDocumentJSON",
    "LastMaterialReportConfigurationJSON",
    "MaterialReportConfigurationJSON",
    "MaterialReportDiagnosticsJSON",
    "NamedPresetLibraryJSON",
    "PlainConnectorTimberRecordsJSON",
    "PlatformConfigurationJSON",
    "PlatformConfigurationsJSON",
    "ProductionExportConfigurationJSON",
    "ProductionRecordIDsJSON",
    "ProductionRecordIndexJSON",
    "ProtectedSupportZonesJSON",
    "RegistrationConfigurationJSON",
    "SectionConfigurationJSON",
    "SharedTimberEnvelopeSummaryJSON",
    "SharedTimberRecordsJSON",
    "SharedTimberSourceIdentitiesJSON",
    "StraightTrackConfigurationsJSON",
    "TimberAnalysisFindingsJSON",
    "TrackConfigurationJSON",
    "TrackTemplateAssemblyConfigurationJSON",
    "TurnoutConfigurationJSON",
    "TurnoutConfigurationsJSON",
    "TurnoutHostIntegrationJSON",
)

__all__ = (
    "LEGACY_INSPECTION_SCHEMA_ID",
    "LEGACY_INSPECTION_SCHEMA_VERSION",
    "RECOGNISED_LEGACY_JSON_PROPERTIES",
    "SUPPORTED_MIGRATION_FAMILIES",
    "STATUS_SUPPORTED",
    "STATUS_INSPECTION_ONLY",
    "STATUS_BLOCKED",
    "LegacyDocumentInspection",
    "LegacyInspectionError",
    "inspect_legacy_document",
    "legacy_inspection_to_json",
)


class LegacyInspectionError(ValueError):
    """The detector invocation or accepted policy is invalid."""

    def __init__(self, code, message):
        self.code = str(code)
        self.detail = str(message)
        super().__init__("{}: {}".format(self.code, self.detail))

    def diagnostic(self):
        return {
            "code": self.code,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
        }


@dataclass(frozen=True)
class LegacyVersionEvidence:
    object_name: str
    property_path: str
    version_token: str

    def to_record(self):
        return {
            "object_name": self.object_name,
            "property_path": self.property_path,
            "version_token": self.version_token,
        }


@dataclass(frozen=True)
class LegacyFinding:
    level: str
    code: str
    object_name: str
    property_path: str
    message: str

    def to_record(self):
        return {
            "level": self.level,
            "code": self.code,
            "object_name": self.object_name,
            "property_path": self.property_path,
            "message": self.message,
        }


@dataclass(frozen=True)
class LegacyDocumentInspection:
    """Deterministic non-authorising report for one document snapshot."""

    contract_id: str
    status: str
    version_window_status: str
    generator_id: str
    supported_versions: tuple
    observed_versions: tuple
    owned_object_names: tuple
    owned_roles: tuple
    json_payload_paths: tuple
    foreign_object_count: int
    version_evidence: tuple
    findings: tuple

    @property
    def write_authorized(self):
        return False

    def to_record(self):
        return {
            "schema_id": LEGACY_INSPECTION_SCHEMA_ID,
            "schema_version": LEGACY_INSPECTION_SCHEMA_VERSION,
            "contract_id": self.contract_id,
            "status": self.status,
            "version_window_status": self.version_window_status,
            "generator_id": self.generator_id,
            "supported_versions": list(self.supported_versions),
            "observed_versions": list(self.observed_versions),
            "owned_object_names": list(self.owned_object_names),
            "owned_roles": list(self.owned_roles),
            "json_payload_paths": list(self.json_payload_paths),
            "foreign_object_count": self.foreign_object_count,
            "version_evidence": [item.to_record() for item in self.version_evidence],
            "findings": [item.to_record() for item in self.findings],
            "write_authorized": False,
        }


def legacy_inspection_to_json(inspection):
    """Serialise a report deterministically for diagnostics or test evidence."""
    if not isinstance(inspection, LegacyDocumentInspection):
        raise TypeError("inspection must be a LegacyDocumentInspection")
    return json.dumps(
        inspection.to_record(),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _accepted_policy(contract):
    if not isinstance(contract, dict):
        raise LegacyInspectionError(
            "invalid-compatibility-contract",
            "the accepted compatibility contract must be an object",
        )
    if contract.get("schema_version") != 1 or contract.get(
        "contract_id"
    ) != COMPATIBILITY_CONTRACT_ID:
        raise LegacyInspectionError(
            "unsupported-compatibility-contract",
            "only the accepted Phase 1 compatibility contract is supported",
        )
    source_state = contract.get("source_state")
    window = contract.get("legacy_document_window")
    if not isinstance(source_state, dict) or not isinstance(window, dict):
        raise LegacyInspectionError(
            "invalid-compatibility-contract",
            "source_state and legacy_document_window are required",
        )
    try:
        source_versions = tuple(
            source_state[name]["version_token"] for name in ("b14", "b15")
        )
    except (KeyError, TypeError) as error:
        raise LegacyInspectionError(
            "invalid-compatibility-contract",
            "the B14 and B15 source version tokens are required",
        ) from error
    supported = window.get("supported_ingress_versions")
    accepted = window.get("accepted_version_sets")
    generator_id = window.get("generator_id")
    expected_sets = (
        (source_versions[0],),
        (source_versions[1],),
        source_versions,
    )
    if (
        any(not isinstance(item, str) or not item.strip() for item in source_versions)
        or len(set(source_versions)) != 2
        or supported != list(source_versions)
        or accepted != [list(item) for item in expected_sets]
        or not isinstance(generator_id, str)
        or not generator_id.strip()
        or generator_id != generator_id.strip()
    ):
        raise LegacyInspectionError(
            "invalid-compatibility-contract",
            "the accepted B14/B15 ingress window is malformed or has broadened",
        )
    return generator_id, source_versions, expected_sets


def _object_name(obj):
    try:
        return str(getattr(obj, "Name", ""))
    except Exception:
        return ""


def _property_names(obj):
    try:
        names = tuple(obj.PropertiesList)
    except Exception as error:
        raise LegacyInspectionError(
            "unreadable-document-object",
            "cannot read PropertiesList for {!r}".format(_object_name(obj)),
        ) from error
    if any(not isinstance(name, str) for name in names):
        raise LegacyInspectionError(
            "unreadable-document-object",
            "PropertiesList contains a non-text name on {!r}".format(
                _object_name(obj)
            ),
        )
    return names


def _property_value(obj, property_names, property_name):
    if property_name not in property_names:
        return None, False
    try:
        return getattr(obj, property_name), True
    except Exception as error:
        raise LegacyInspectionError(
            "unreadable-document-property",
            "cannot read {} on {!r}".format(property_name, _object_name(obj)),
        ) from error


def _version_token(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return value.split()[0]


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key {!r}".format(key))
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError("non-standard JSON number {!r}".format(value))


def _json_version_fields(value, path="$"):
    found = []
    invalid_schemas = []
    if isinstance(value, dict):
        for key in sorted(value):
            item = value[key]
            child_path = "{}.{}".format(path, key)
            if key in VERSION_FIELDS:
                found.append((child_path, item))
            if key == "schema_version" or key.endswith("_schema_version"):
                if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                    invalid_schemas.append(child_path)
            child_versions, child_invalid = _json_version_fields(item, child_path)
            found.extend(child_versions)
            invalid_schemas.extend(child_invalid)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_versions, child_invalid = _json_version_fields(
                item,
                "{}[{}]".format(path, index),
            )
            found.extend(child_versions)
            invalid_schemas.extend(child_invalid)
    return found, invalid_schemas


def _finding(level, code, object_name="", property_path="", message=""):
    return LegacyFinding(
        str(level),
        str(code),
        str(object_name),
        str(property_path),
        str(message),
    )


def _finding_key(item):
    return (
        item.object_name,
        item.property_path,
        item.level,
        item.code,
        item.message,
    )


def _inspect_json_property(obj, property_names, property_name):
    """Return one recognised payload's path, tokens, evidence and findings."""
    object_name = _object_name(obj)
    raw_payload, _present = _property_value(obj, property_names, property_name)
    if raw_payload in (None, ""):
        return None
    payload_path = "{}.{}".format(object_name, property_name)
    evidence = []
    findings = []
    tokens = []
    if not isinstance(raw_payload, str):
        findings.append(
            _finding(
                "blocking",
                "malformed-json-property",
                object_name,
                property_name,
                "a non-empty JSON property must contain text",
            )
        )
        return payload_path, tokens, evidence, findings
    try:
        payload = json.loads(
            raw_payload,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, RecursionError) as error:
        findings.append(
            _finding(
                "blocking",
                "malformed-json-payload",
                object_name,
                property_name,
                str(error),
            )
        )
        return payload_path, tokens, evidence, findings
    if not isinstance(payload, (dict, list)):
        findings.append(
            _finding(
                "blocking",
                "malformed-json-root",
                object_name,
                property_name,
                "a recognised legacy JSON payload must be an object or array",
            )
        )
        return payload_path, tokens, evidence, findings
    try:
        version_fields, invalid_schemas = _json_version_fields(payload)
    except RecursionError as error:
        findings.append(
            _finding(
                "blocking",
                "malformed-json-payload",
                object_name,
                property_name,
                str(error) or "JSON nesting is too deep",
            )
        )
        return payload_path, tokens, evidence, findings
    for field_path in invalid_schemas:
        findings.append(
            _finding(
                "blocking",
                "malformed-schema-version",
                object_name,
                property_name + field_path,
                "schema version evidence must be a non-negative integer",
            )
        )
    for field_path, value in version_fields:
        token = _version_token(value)
        full_path = property_name + field_path
        if token is None:
            findings.append(
                _finding(
                    "blocking",
                    "malformed-json-version",
                    object_name,
                    full_path,
                    "JSON version evidence must be non-empty text",
                )
            )
            continue
        tokens.append(token)
        evidence.append(LegacyVersionEvidence(object_name, full_path, token))
    return payload_path, tokens, evidence, findings


def inspect_legacy_document(document, compatibility_contract):
    """Inspect one document without mutation and without granting write access."""
    generator_id, supported_versions, accepted_sets = _accepted_policy(
        compatibility_contract
    )
    try:
        objects = tuple(document.Objects)
    except Exception as error:
        raise LegacyInspectionError(
            "invalid-document",
            "a document-like object with a readable Objects collection is required",
        ) from error

    names = [_object_name(obj) for obj in objects]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise LegacyInspectionError(
            "ambiguous-document-objects",
            "every inspected object must have a unique non-empty Name",
        )

    evidence = []
    findings = []
    owned_names = []
    owned_roles = set()
    payload_paths = []
    foreign_count = 0
    incomplete_version_evidence = False

    for obj in sorted(objects, key=_object_name):
        object_name = _object_name(obj)
        properties = _property_names(obj)
        generated_by, has_generated_by = _property_value(
            obj,
            properties,
            "GeneratedBy",
        )
        if not has_generated_by or generated_by != generator_id:
            foreign_count += 1
            continue

        owned_names.append(object_name)
        object_tokens = []
        role, has_role = _property_value(obj, properties, "GeneratedRole")
        if has_role and isinstance(role, str) and role.strip():
            owned_roles.add(role.strip())
        else:
            findings.append(
                _finding(
                    "inspection",
                    "missing-family-role",
                    object_name,
                    "GeneratedRole",
                    "owned object has no usable generated-role evidence",
                )
            )

        set_id, has_set_id = _property_value(obj, properties, "TemplateSetID")
        if not has_set_id or not isinstance(set_id, str) or not set_id.strip():
            findings.append(
                _finding(
                    "inspection",
                    "missing-template-set-identity",
                    object_name,
                    "TemplateSetID",
                    "owned object has no usable template-set identity",
                )
            )

        generator_version, has_generator_version = _property_value(
            obj,
            properties,
            "GeneratorVersion",
        )
        token = _version_token(generator_version)
        if not has_generator_version or generator_version == "" or token is None:
            if has_generator_version and not isinstance(generator_version, str):
                findings.append(
                    _finding(
                        "blocking",
                        "malformed-generator-version",
                        object_name,
                        "GeneratorVersion",
                        "generator version evidence must be non-empty text",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "inspection",
                        "versionless-owned-object",
                        object_name,
                        "GeneratorVersion",
                        "owned object has no generator version token",
                    )
                )
            incomplete_version_evidence = True
        else:
            object_tokens.append(token)
            evidence.append(
                LegacyVersionEvidence(object_name, "GeneratorVersion", token)
            )

        for property_name in sorted(
            name
            for name in properties
            if name in RECOGNISED_LEGACY_JSON_PROPERTIES
        ):
            inspected = _inspect_json_property(obj, properties, property_name)
            if inspected is None:
                continue
            payload_path, json_tokens, json_evidence, json_findings = inspected
            payload_paths.append(payload_path)
            object_tokens.extend(json_tokens)
            evidence.extend(json_evidence)
            findings.extend(json_findings)

        if len(set(object_tokens)) > 1:
            findings.append(
                _finding(
                    "blocking",
                    "conflicting-object-version-evidence",
                    object_name,
                    "",
                    "owned object contains contradictory version tokens: {}".format(
                        ", ".join(sorted(set(object_tokens)))
                    ),
                )
            )

    evidence = sorted(
        evidence,
        key=lambda item: (item.object_name, item.property_path, item.version_token),
    )
    observed_set = set(item.version_token for item in evidence)
    observed_versions = tuple(
        sorted(
            observed_set,
            key=lambda item: (
                supported_versions.index(item)
                if item in supported_versions
                else len(supported_versions),
                item,
            ),
        )
    )
    blocking = any(item.level == "blocking" for item in findings)
    if blocking:
        version_window_status = "conflicting-or-corrupt"
        status = STATUS_BLOCKED
    elif not owned_names:
        version_window_status = "not-detected"
        status = STATUS_INSPECTION_ONLY
        findings.append(
            _finding(
                "inspection",
                "no-owned-legacy-objects",
                message="the document contains no objects owned by the contracted generator",
            )
        )
    elif incomplete_version_evidence or not observed_versions:
        version_window_status = "incomplete"
        status = STATUS_INSPECTION_ONLY
    elif observed_versions not in accepted_sets:
        version_window_status = "unsupported"
        status = STATUS_INSPECTION_ONLY
        findings.append(
            _finding(
                "inspection",
                "unsupported-version-set",
                message="observed version set is outside the accepted B14/B15 window",
            )
        )
    else:
        version_window_status = "accepted"
        status = STATUS_INSPECTION_ONLY

    if owned_names and status != STATUS_BLOCKED:
        findings.append(
            _finding(
                "inspection",
                "migration-family-not-qualified",
                message=(
                    "the outer version window does not qualify any entity family; "
                    "family schemas, identities and canonical sufficiency still require "
                    "accepted Phase 4 fixtures"
                ),
            )
        )

    return LegacyDocumentInspection(
        contract_id=COMPATIBILITY_CONTRACT_ID,
        status=status,
        version_window_status=version_window_status,
        generator_id=generator_id,
        supported_versions=supported_versions,
        observed_versions=observed_versions,
        owned_object_names=tuple(sorted(owned_names)),
        owned_roles=tuple(sorted(owned_roles)),
        json_payload_paths=tuple(sorted(payload_paths)),
        foreign_object_count=foreign_count,
        version_evidence=tuple(evidence),
        findings=tuple(sorted(findings, key=_finding_key)),
    )
