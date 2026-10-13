"""Build schema-1 dependency records for the bounded Core plain-line route.

This internal contract records existing unresolved rights. It cannot grant
production admission or project clearance. Host objects and file reads belong
to the compatibility inventory, not this deterministic builder.
"""

import copy
import hashlib
import json
import re

CORE_DEPENDENCY_SCOPE = "core-generate-curved-plain-line-v1"
LINEAGE_LOCATOR = "reference/lineage/phase1-other-snc-legacy-lineage.json"
LINEAGE = (
    ("legacy.user-input-and-persisted-parametric-state", "unknown",
     ("user_design", "project_derivation")),
    ("legacy.retained-freecad-shapes-and-document-objects", "reference-only",
     ("generated_output", "project_derivation", "templot_reference_data")),
    ("legacy.dxf-svg-stl-step-export-artifacts", "reference-only",
     ("generated_output", "project_derivation", "templot_reference_data")),
    ("legacy.csv-manifests-reports-and-production-records", "reference-only",
     ("generated_output", "project_derivation", "templot_reference_data")),
    ("legacy.output-names-labels-and-boilerplate", "unknown",
     ("generated_output", "project_derivation")),
    ("legacy.user-assets-fonts-and-external-exporters", "unknown",
     ("third_party_evidence", "user_design", "generated_output")),
    ("legacy.b14-b15-version-and-release-boundary", "unknown",
     ("project_derivation", "generated_output")),
)
_DATE = "2026-10-13"
_REVIEWER = "TrackTemplate Core dependency inventory control"
_REFERENCE = "reference/contracts/core-layout-export-set.md"
_SHA256 = r"[0-9a-f]{64}\Z"


def canonical_json(value):
    """Serialise finite plain JSON without reordering any list."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def content_digest(value):
    """Hash the UTF-8 bytes of the internal canonical JSON convention."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value):
    if not isinstance(value, str) or re.fullmatch(_SHA256, value) is None:
        raise ValueError("Core dependency inventory has an invalid SHA-256.")
    return value


def _decision(status, reason):
    return {
        "status": status, "reason": reason, "reviewed_by": _REVIEWER,
        "reviewed_on": _DATE, "decision_reference": _REFERENCE,
    }


def _rights():
    return {
        area: {
            "status": "not-performed", "territories": ["GB"],
            "reviewed_on": _DATE, "reviewed_by": _REVIEWER,
            "evidence": [],
            "notes": "No rights review or positive clearance is claimed.",
        }
        for area in ("registered_designs", "unregistered_designs",
                     "patents", "trade_marks")
    }


def _dependency(identifier, name, role, classifications, locator, digest,
                *, status="unknown", license_expression="NOASSERTION",
                supplier="TrackTemplate contributors", conditions=()):
    return {
        "identifier": identifier, "name": name, "role": role,
        "output_affecting": True,
        "classifications": list(classifications),
        "source": {
            "creator_or_supplier": supplier, "locator": locator,
            "evidence_sha256": _digest(digest),
        },
        "license_expression": license_expression,
        "permissions": {
            "access": "permitted", "adaptation": "unknown",
            "production_output": status if status != "unknown" else "unknown",
            "redistribution": "unknown", "commercial_use": "unknown",
            "publication": "unknown",
        },
        "conditions": list(conditions),
        "contribution_attestation": {
            "status": "missing",
            "reference": "No per-output rights declaration is supplied.",
        },
        "non_copyright_review": _rights(),
        "project_status": _decision(
            status, "Existing provenance and intended-use limits remain."
        ),
    }


def _validate_inventory(inventory):
    required = {
        "canonical_input", "generator_sources", "runtime", "exporters",
        "lineage", "expected_artifacts", "source_origin", "generator_version",
    }
    if not isinstance(inventory, dict) or set(inventory) != required:
        raise ValueError("Core dependency inventory is incomplete.")
    canonical = inventory["canonical_input"]
    if (not isinstance(canonical, dict)
            or canonical.get("scope") != CORE_DEPENDENCY_SCOPE
            or canonical.get("production_admission_enabled") is not False):
        raise ValueError("Core dependency inventory has unsupported authority.")
    if not isinstance(inventory["source_origin"], str):
        raise ValueError("Core dependency inventory has no generation origin.")
    if (not isinstance(inventory["generator_version"], str)
            or not inventory["generator_version"]):
        raise ValueError("Core dependency inventory has no generator version.")
    for group in ("generator_sources", "exporters"):
        records = inventory[group]
        if not isinstance(records, list) or not records:
            raise ValueError("Core dependency inventory is missing " + group)
        paths = []
        for record in records:
            if (not isinstance(record, dict)
                    or set(record) != {"path", "sha256"}
                    or not isinstance(record["path"], str)
                    or not record["path"]):
                raise ValueError("Core dependency source identity is missing.")
            paths.append(record["path"])
            _digest(record["sha256"])
        if len(paths) != len(set(paths)):
            raise ValueError("Core dependency source identity is duplicated.")
    if not isinstance(inventory["runtime"], dict) or not inventory["runtime"]:
        raise ValueError("Core dependency runtime identity is missing.")
    records = inventory["lineage"]
    expected = {item[0]: item for item in LINEAGE}
    if not isinstance(records, list) or len(records) != len(expected):
        raise ValueError("Core dependency lineage inventory is incomplete.")
    seen = set()
    for item in records:
        if not isinstance(item, dict) or set(item) != {
            "identifier", "status", "classifications",
        }:
            raise ValueError("Core dependency lineage record is invalid.")
        identifier = item["identifier"]
        if identifier not in expected or identifier in seen:
            raise ValueError("Core dependency lineage identity is invalid.")
        seen.add(identifier)
        if (item["classifications"] != list(expected[identifier][2])
                or item["status"] not in {
                    "unknown", "restricted", "reference-only",
                }):
            raise ValueError("Core dependency lineage classification changed.")
    canonical_json(inventory)


def build_core_dependency_manifest(inventory, artifacts):
    """Return a complete bounded manifest or reject missing evidence.

    ``artifacts`` contains actual staged hashes and final basenames. The
    manifest itself is excluded to avoid a recursive self-hash. Inventory
    preparation supplies exact expected names and formats, including CSV.
    """
    _validate_inventory(inventory)
    expected = inventory["expected_artifacts"]
    if not isinstance(expected, list) or not expected or not artifacts:
        raise ValueError("Core dependency artifact inventory is empty.")
    pairs = []
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {
            "path", "format", "sha256",
        }:
            raise ValueError("Core dependency artifact record is invalid.")
        name = item["path"]
        if (not isinstance(name, str) or name in {"", ".", ".."}
                or "/" in name or "\\" in name or "\x00" in name
                or item["format"] not in {"dxf", "svg", "stl", "step", "csv"}
                or not name.lower().endswith("." + item["format"])):
            raise ValueError("Core dependency artifact identity is unsafe.")
        _digest(item["sha256"])
        pairs.append({"path": name, "format": item["format"]})
    if pairs != expected or len({item["path"] for item in pairs}) != len(pairs):
        raise ValueError("Core dependency artifact inventory differs from plan.")
    canonical_digest = content_digest(inventory["canonical_input"])
    source_digest = content_digest(inventory["generator_sources"])
    dependencies = [
        _dependency(
            "tracktemplate:core-canonical-input", "Canonical Core inputs",
            "user-input", ("user_design", "project_derivation"),
            CORE_DEPENDENCY_SCOPE + ":" + canonical_digest, canonical_digest,
            supplier="TrackTemplate operator",
            conditions=(
                "Canonical input uses mm, degrees and ordered track records.",
                "Destination paths, disabled manager IDs and disposable "
                "object names are excluded from the canonical signature.",
                inventory["source_origin"],
            ),
        ),
        _dependency(
            "tracktemplate:core-generator-source", "B16 Core generator",
            "software-source",
            ("engineering_method", "project_derivation",
             "templot_source_expression"),
            "Installed generator source inventory: "
            + canonical_json(inventory["generator_sources"]), source_digest,
            license_expression="GPL-3.0-or-later",
            conditions=(
                "LICENSE, NOTICE.md and PROVENANCE.md retain the "
                "source-informed attribution; source licensing does not "
                "clear generated-output rights.",
                "The source fingerprint includes the inherited B15 host; "
                "this route is not a completed macro migration.",
                "Installed-file fingerprints do not attest cached executing "
                "Python or binary bytes. Execution evidence comes from a "
                "fresh qualified process.",
            ),
        ),
        _dependency(
            "tracktemplate:core-host-exporters", "FreeCAD host and exporters",
            "software-source", ("third_party_evidence", "generated_output"),
            "Runtime and selected exporter evidence: " + canonical_json({
                "runtime": inventory["runtime"],
                "exporters": inventory["exporters"],
            }),
            content_digest({"runtime": inventory["runtime"],
                            "exporters": inventory["exporters"]}),
            supplier="FreeCAD distribution and component contributors",
            conditions=(
                "The evidence hash identifies the recorded runtime and "
                "exporter inventory, not every binary in the distribution.",
                "Host and exporter output-boilerplate rights are unresolved.",
            ),
        ),
    ]
    for item in inventory["lineage"]:
        dependencies.append(_dependency(
            item["identifier"], "Inherited lineage: " + item["identifier"],
            "production-input", item["classifications"],
            LINEAGE_LOCATOR + "#" + item["identifier"], content_digest(item),
            status=item["status"],
            conditions=(
                "This inherited group retains its accepted classifications. "
                "It does not assert consumption of every historical "
                "upstream chair or special-trackwork input in that group.",
                "The production-record group applies with CSV disabled. "
                "These provenance controls are not output self-dependencies.",
                "The evidence hash identifies this canonical identity, "
                "classification and status summary, not the register file.",
            ),
        ))
    identity = content_digest({"inventory": inventory, "artifacts": artifacts})
    return {
        "schema_version": 1,
        "manifest_id": "tracktemplate:core-output:" + identity,
        "manifest_kind": "output", "audit_scope": "legacy-b14-b15-output",
        "subject": {
            "identifier": "tracktemplate:core-plain-line:" + identity,
            "version": "1",
            "description": (
                "Private-development curved plain-line Core output set. "
                "The dependency JSON excludes its own recursive hash."
            ),
            "generator": {"program": "TrackTemplate",
                          "version": inventory["generator_version"],
                          "source_sha256": source_digest},
            "canonical_model_sha256": canonical_digest,
            "artifacts": copy.deepcopy(artifacts),
        },
        "intended_uses": ["private-development"],
        "dependencies": dependencies, "non_copyright_review": _rights(),
        "project_status": _decision(
            "unknown", "Unresolved input and host rights remain; production "
            "admission is disabled. No phase or output clearance is granted."
        ),
    }
