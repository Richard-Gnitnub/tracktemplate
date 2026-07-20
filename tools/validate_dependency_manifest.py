#!/usr/bin/env python3
"""Validate TrackTemplateMacro dependency/project-status manifests.

The JSON Schema is the portable structural contract.  This standard-library
validator also applies the fail-closed semantic rules for the internal
``project-cleared`` status, without adding a runtime or development dependency.
"""

import argparse
import datetime
import json
import pathlib
import re
import sys


SCHEMA_VERSION = 1
MANIFEST_KINDS = ("package", "output")
AUDIT_SCOPES = (
    "s1-chair-release-path",
    "core-rail-timber-path",
    "other-switches-crossings-output",
    "legacy-b14-b15-output",
)
INTENDED_USES = (
    "private-development",
    "public-redistribution",
    "commercial-production",
    "publication",
    "physical-production",
)
CLASSIFICATIONS = (
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
DEPENDENCY_ROLES = (
    "production-input",
    "embedded-material",
    "software-source",
    "comparison-only",
    "validation-only",
    "user-input",
    "build-tool",
)
PERMISSION_STATUSES = (
    "permitted",
    "restricted",
    "reference-only",
    "unknown",
    "not-applicable",
)
PERMISSION_FIELDS = (
    "access",
    "adaptation",
    "production_output",
    "redistribution",
    "commercial_use",
    "publication",
)
PROJECT_STATUSES = (
    "project-cleared",
    "restricted",
    "reference-only",
    "unknown",
)
NON_COPYRIGHT_AREAS = (
    "registered_designs",
    "unregistered_designs",
    "patents",
    "trade_marks",
)
NON_COPYRIGHT_STATUSES = (
    "not-performed",
    "not-applicable",
    "no-known-conflict",
    "permission-confirmed",
    "expired-or-lapsed-confirmed",
    "potential-conflict",
    "unresolved",
    "professional-review-required",
)
NON_COPYRIGHT_PASS_STATUSES = (
    "not-applicable",
    "no-known-conflict",
    "permission-confirmed",
    "expired-or-lapsed-confirmed",
)
ATTESTATION_STATUSES = ("recorded", "not-required", "missing")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

ROOT_KEYS = {
    "schema_version",
    "manifest_id",
    "manifest_kind",
    "audit_scope",
    "subject",
    "intended_uses",
    "dependencies",
    "non_copyright_review",
    "project_status",
}
SUBJECT_KEYS = {
    "identifier",
    "version",
    "description",
    "content_sha256",
    "package_license",
    "generator",
    "canonical_model_sha256",
    "artifacts",
}
DEPENDENCY_KEYS = {
    "identifier",
    "name",
    "role",
    "output_affecting",
    "classifications",
    "source",
    "license_expression",
    "permissions",
    "conditions",
    "contribution_attestation",
    "non_copyright_review",
    "project_status",
}


def _mapping(value, path, errors):
    if not isinstance(value, dict):
        errors.append("{} must be an object".format(path))
        return None
    return value


def _keys(value, path, required, allowed, errors):
    missing = sorted(set(required) - set(value))
    extra = sorted(set(value) - set(allowed))
    if missing:
        errors.append("{} is missing: {}".format(path, ", ".join(missing)))
    if extra:
        errors.append("{} has unsupported fields: {}".format(path, ", ".join(extra)))


def _text(value, path, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append("{} must be a non-empty string".format(path))
        return ""
    return value


def _identifier(value, path, errors):
    result = _text(value, path, errors)
    if result and not IDENTIFIER_PATTERN.fullmatch(result):
        errors.append("{} is not a valid stable identifier".format(path))
    return result


def _choice(value, path, choices, errors):
    if value not in choices:
        errors.append(
            "{} must be one of: {}".format(path, ", ".join(choices))
        )
    return value


def _date(value, path, errors):
    result = _text(value, path, errors)
    if not result:
        return result
    try:
        parsed = datetime.date.fromisoformat(result)
    except ValueError:
        errors.append("{} must be an ISO calendar date".format(path))
        return result
    if parsed.isoformat() != result:
        errors.append("{} must use YYYY-MM-DD form".format(path))
    return result


def _sha256(value, path, errors):
    result = _text(value, path, errors)
    if result and not SHA256_PATTERN.fullmatch(result):
        errors.append("{} must be a lowercase SHA-256 digest".format(path))
    return result


def _string_list(value, path, errors, choices=None, require_nonempty=False):
    if not isinstance(value, list):
        errors.append("{} must be an array".format(path))
        return []
    if require_nonempty and not value:
        errors.append("{} must not be empty".format(path))
    result = []
    for index, item in enumerate(value):
        item_path = "{}[{}]".format(path, index)
        text = _text(item, item_path, errors)
        if choices is not None:
            _choice(item, item_path, choices, errors)
        result.append(text)
    if len(set(result)) != len(result):
        errors.append("{} must not contain duplicates".format(path))
    return result


def _validate_project_decision(value, path, errors):
    decision = _mapping(value, path, errors)
    if decision is None:
        return None
    required = {
        "status",
        "reason",
        "reviewed_by",
        "reviewed_on",
        "decision_reference",
    }
    _keys(decision, path, required, required, errors)
    _choice(decision.get("status"), path + ".status", PROJECT_STATUSES, errors)
    _text(decision.get("reason"), path + ".reason", errors)
    _text(decision.get("reviewed_by"), path + ".reviewed_by", errors)
    _date(decision.get("reviewed_on"), path + ".reviewed_on", errors)
    _text(decision.get("decision_reference"), path + ".decision_reference", errors)
    return decision


def _validate_non_copyright_review(value, path, errors):
    review = _mapping(value, path, errors)
    if review is None:
        return None
    required = set(NON_COPYRIGHT_AREAS)
    _keys(review, path, required, required, errors)
    for area in NON_COPYRIGHT_AREAS:
        finding_path = "{}.{}".format(path, area)
        finding = _mapping(review.get(area), finding_path, errors)
        if finding is None:
            continue
        fields = {
            "status",
            "territories",
            "reviewed_on",
            "reviewed_by",
            "evidence",
            "notes",
        }
        _keys(finding, finding_path, fields, fields, errors)
        _choice(
            finding.get("status"),
            finding_path + ".status",
            NON_COPYRIGHT_STATUSES,
            errors,
        )
        _string_list(
            finding.get("territories"),
            finding_path + ".territories",
            errors,
            require_nonempty=True,
        )
        _date(finding.get("reviewed_on"), finding_path + ".reviewed_on", errors)
        _text(finding.get("reviewed_by"), finding_path + ".reviewed_by", errors)
        _string_list(finding.get("evidence"), finding_path + ".evidence", errors)
        _text(finding.get("notes"), finding_path + ".notes", errors)
    return review


def _validate_subject(value, kind, path, errors):
    subject = _mapping(value, path, errors)
    if subject is None:
        return None
    required = {"identifier", "version", "description"}
    if kind == "package":
        required.add("package_license")
    elif kind == "output":
        required.update({"generator", "canonical_model_sha256", "artifacts"})
    _keys(subject, path, required, SUBJECT_KEYS, errors)
    _identifier(subject.get("identifier"), path + ".identifier", errors)
    _text(subject.get("version"), path + ".version", errors)
    _text(subject.get("description"), path + ".description", errors)
    if "content_sha256" in subject:
        _sha256(subject.get("content_sha256"), path + ".content_sha256", errors)

    if kind == "package":
        _text(subject.get("package_license"), path + ".package_license", errors)
        forbidden = sorted(
            set(subject).intersection({"generator", "canonical_model_sha256", "artifacts"})
        )
        if forbidden:
            errors.append(
                "{} package has output-only fields: {}".format(path, ", ".join(forbidden))
            )
    elif kind == "output":
        if "package_license" in subject:
            errors.append("{} output must not declare package_license".format(path))
        generator_path = path + ".generator"
        generator = _mapping(subject.get("generator"), generator_path, errors)
        if generator is not None:
            allowed = {"program", "version", "source_sha256"}
            required_generator = {"program", "version"}
            _keys(generator, generator_path, required_generator, allowed, errors)
            _text(generator.get("program"), generator_path + ".program", errors)
            _text(generator.get("version"), generator_path + ".version", errors)
            if "source_sha256" in generator:
                _sha256(
                    generator.get("source_sha256"),
                    generator_path + ".source_sha256",
                    errors,
                )
        _sha256(
            subject.get("canonical_model_sha256"),
            path + ".canonical_model_sha256",
            errors,
        )
        artifacts = subject.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(path + ".artifacts must be a non-empty array")
        else:
            artifact_keys = {"path", "format", "sha256"}
            artifact_paths = []
            for index, artifact_value in enumerate(artifacts):
                artifact_path = "{}.artifacts[{}]".format(path, index)
                artifact = _mapping(artifact_value, artifact_path, errors)
                if artifact is None:
                    continue
                _keys(artifact, artifact_path, artifact_keys, artifact_keys, errors)
                artifact_paths.append(
                    _text(artifact.get("path"), artifact_path + ".path", errors)
                )
                _text(artifact.get("format"), artifact_path + ".format", errors)
                _sha256(artifact.get("sha256"), artifact_path + ".sha256", errors)
            if len(set(artifact_paths)) != len(artifact_paths):
                errors.append(path + ".artifacts contains duplicate paths")
    return subject


def _validate_dependency(value, index, errors):
    path = "$.dependencies[{}]".format(index)
    dependency = _mapping(value, path, errors)
    if dependency is None:
        return None
    _keys(dependency, path, DEPENDENCY_KEYS, DEPENDENCY_KEYS, errors)
    _identifier(dependency.get("identifier"), path + ".identifier", errors)
    _text(dependency.get("name"), path + ".name", errors)
    role = _choice(dependency.get("role"), path + ".role", DEPENDENCY_ROLES, errors)
    output_affecting = dependency.get("output_affecting")
    if not isinstance(output_affecting, bool):
        errors.append(path + ".output_affecting must be a boolean")
    if output_affecting and role in ("comparison-only", "validation-only"):
        errors.append(
            "{} cannot be output-affecting with role {}".format(path, role)
        )
    _string_list(
        dependency.get("classifications"),
        path + ".classifications",
        errors,
        choices=CLASSIFICATIONS,
        require_nonempty=True,
    )

    source_path = path + ".source"
    source = _mapping(dependency.get("source"), source_path, errors)
    if source is not None:
        required = {"creator_or_supplier", "locator"}
        allowed = required | {"acquired_on", "evidence_sha256"}
        _keys(source, source_path, required, allowed, errors)
        _text(
            source.get("creator_or_supplier"),
            source_path + ".creator_or_supplier",
            errors,
        )
        _text(source.get("locator"), source_path + ".locator", errors)
        if "acquired_on" in source:
            _date(source.get("acquired_on"), source_path + ".acquired_on", errors)
        if "evidence_sha256" in source:
            _sha256(
                source.get("evidence_sha256"),
                source_path + ".evidence_sha256",
                errors,
            )

    license_expression = _text(
        dependency.get("license_expression"),
        path + ".license_expression",
        errors,
    )
    permissions_path = path + ".permissions"
    permissions = _mapping(dependency.get("permissions"), permissions_path, errors)
    permission_fields = set(PERMISSION_FIELDS)
    if permissions is not None:
        _keys(
            permissions,
            permissions_path,
            permission_fields,
            permission_fields,
            errors,
        )
        for field in sorted(permission_fields):
            _choice(
                permissions.get(field),
                "{}.{}".format(permissions_path, field),
                PERMISSION_STATUSES,
                errors,
            )
    _string_list(dependency.get("conditions"), path + ".conditions", errors)

    attestation_path = path + ".contribution_attestation"
    attestation = _mapping(
        dependency.get("contribution_attestation"), attestation_path, errors
    )
    if attestation is not None:
        fields = {"status", "reference"}
        _keys(attestation, attestation_path, fields, fields, errors)
        _choice(
            attestation.get("status"),
            attestation_path + ".status",
            ATTESTATION_STATUSES,
            errors,
        )
        _text(attestation.get("reference"), attestation_path + ".reference", errors)

    review = _validate_non_copyright_review(
        dependency.get("non_copyright_review"),
        path + ".non_copyright_review",
        errors,
    )
    decision = _validate_project_decision(
        dependency.get("project_status"), path + ".project_status", errors
    )

    if decision is not None and decision.get("status") == "project-cleared":
        if license_expression.upper() == "NOASSERTION":
            errors.append(path + " cannot be project-cleared with NOASSERTION")
        if attestation is None or attestation.get("status") == "missing":
            errors.append(path + " cannot be project-cleared without authority evidence")
        if output_affecting:
            if permissions is None or permissions.get("access") != "permitted":
                errors.append(path + " project-cleared input requires permitted access")
            if permissions is None or permissions.get("adaptation") not in (
                "permitted",
                "not-applicable",
            ):
                errors.append(
                    path
                    + " project-cleared input requires permitted or not-applicable adaptation"
                )
            if permissions is None or permissions.get("production_output") != "permitted":
                errors.append(
                    path + " project-cleared input requires permitted production output"
                )
            _require_non_copyright_pass(review, path + ".non_copyright_review", errors)
    return dependency


def _require_non_copyright_pass(review, path, errors):
    if review is None:
        return
    for area in NON_COPYRIGHT_AREAS:
        finding = review.get(area)
        if not isinstance(finding, dict):
            continue
        if finding.get("status") not in NON_COPYRIGHT_PASS_STATUSES:
            errors.append(
                "{}.{} blocks project-cleared status ({})".format(
                    path,
                    area,
                    finding.get("status"),
                )
            )
        if not finding.get("evidence"):
            errors.append(
                "{}.{} needs recorded evidence for project-cleared status".format(
                    path,
                    area,
                )
            )


def validate_document(document, require_project_cleared=False):
    """Return human-readable errors for one decoded manifest."""
    errors = []
    root = _mapping(document, "$", errors)
    if root is None:
        return errors
    _keys(root, "$", ROOT_KEYS, ROOT_KEYS, errors)
    if root.get("schema_version") != SCHEMA_VERSION:
        errors.append("$.schema_version must equal {}".format(SCHEMA_VERSION))
    _identifier(root.get("manifest_id"), "$.manifest_id", errors)
    kind = _choice(root.get("manifest_kind"), "$.manifest_kind", MANIFEST_KINDS, errors)
    _choice(root.get("audit_scope"), "$.audit_scope", AUDIT_SCOPES, errors)
    subject = _validate_subject(root.get("subject"), kind, "$.subject", errors)
    intended_uses = _string_list(
        root.get("intended_uses"),
        "$.intended_uses",
        errors,
        choices=INTENDED_USES,
        require_nonempty=True,
    )

    dependency_values = root.get("dependencies")
    dependencies = []
    if not isinstance(dependency_values, list) or not dependency_values:
        errors.append("$.dependencies must be a non-empty array")
    else:
        for index, value in enumerate(dependency_values):
            dependency = _validate_dependency(value, index, errors)
            if dependency is not None:
                dependencies.append(dependency)
        identifiers = [item.get("identifier") for item in dependencies]
        if len(set(identifiers)) != len(identifiers):
            errors.append("$.dependencies contains duplicate identifiers")

    review = _validate_non_copyright_review(
        root.get("non_copyright_review"), "$.non_copyright_review", errors
    )
    decision = _validate_project_decision(
        root.get("project_status"), "$.project_status", errors
    )
    status = decision.get("status") if decision is not None else None
    if status == "project-cleared":
        if kind == "package" and subject is not None:
            if str(subject.get("package_license", "")).upper() == "NOASSERTION":
                errors.append(
                    "$.subject.package_license cannot be NOASSERTION for project-cleared status"
                )
        _require_non_copyright_pass(review, "$.non_copyright_review", errors)
        for index, dependency in enumerate(dependencies):
            if not dependency.get("output_affecting"):
                continue
            dependency_status = (
                dependency.get("project_status", {}).get("status")
                if isinstance(dependency.get("project_status"), dict)
                else None
            )
            if dependency_status != "project-cleared":
                errors.append(
                    "$.dependencies[{}] is output-affecting but not project-cleared".format(
                        index
                    )
                )
            permissions = dependency.get("permissions", {})
            if "public-redistribution" in intended_uses and (
                permissions.get("redistribution") != "permitted"
            ):
                errors.append(
                    "$.dependencies[{}] requires permitted redistribution for the declared use".format(
                        index
                    )
                )
            if "commercial-production" in intended_uses and (
                permissions.get("commercial_use") != "permitted"
            ):
                errors.append(
                    "$.dependencies[{}] requires permitted commercial use for the declared use".format(
                        index
                    )
                )
            if "publication" in intended_uses and (
                permissions.get("publication") != "permitted"
            ):
                errors.append(
                    "$.dependencies[{}] requires permitted publication for the declared use".format(
                        index
                    )
                )
    if require_project_cleared and status != "project-cleared":
        errors.append(
            "$.project_status.status is {} rather than project-cleared".format(status)
        )
    return errors


def validate_path(path, require_project_cleared=False):
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return ["{}: {}".format(type(error).__name__, error)]
    return validate_document(document, require_project_cleared=require_project_cleared)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate dependency/project-status manifests"
    )
    parser.add_argument(
        "--require-project-cleared",
        action="store_true",
        help="fail unless each supplied manifest passes the project-cleared gate",
    )
    parser.add_argument("manifests", nargs="+", type=pathlib.Path)
    args = parser.parse_args(argv)
    failed = False
    for path in args.manifests:
        errors = validate_path(
            path,
            require_project_cleared=args.require_project_cleared,
        )
        if errors:
            failed = True
            print("{}: invalid".format(path), file=sys.stderr)
            for error in errors:
                print("  - {}".format(error), file=sys.stderr)
        else:
            document = json.loads(path.read_text(encoding="utf-8"))
            status = document["project_status"]["status"]
            print("{}: valid ({})".format(path, status))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
