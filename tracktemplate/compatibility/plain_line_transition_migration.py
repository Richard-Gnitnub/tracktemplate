"""Fixture-only copied-target orchestration for assessed legacy transitions.

This module does not advertise a supported migration family.  It verifies that
the source and target expose the same complete read-only family assessment and
returns immutable states for the fixture to pass to a qualified atomic adapter.
"""

from dataclasses import dataclass
import hashlib

from tracktemplate.compatibility.plain_line_transition import (
    STATUS_CANONICAL_INPUTS_SUFFICIENT,
    assess_plain_line_transitions,
    plain_line_transition_assessment_to_json,
)


MIGRATION_FIXTURE_SCHEMA_ID = (
    "tracktemplate.plain-line-transition-copied-target-fixture"
)
MIGRATION_FIXTURE_SCHEMA_VERSION = 1
MIGRATION_SUPPORT_ADVERTISED = False
PRODUCTION_OUTPUT_AUTHORIZED = False

__all__ = (
    "MIGRATION_FIXTURE_SCHEMA_ID",
    "MIGRATION_FIXTURE_SCHEMA_VERSION",
    "MIGRATION_SUPPORT_ADVERTISED",
    "PRODUCTION_OUTPUT_AUTHORIZED",
    "CopiedTargetMigrationError",
    "CopiedTargetMigrationPlan",
    "prepare_copied_plain_line_transition_migration",
)


class CopiedTargetMigrationError(ValueError):
    """Recoverable preflight failure before any target writer is called."""

    def __init__(self, code, message):
        self.code = str(code)
        self.detail = str(message)
        super().__init__("{}: {}".format(self.code, self.detail))

    def diagnostic(self):
        return {
            "code": self.code,
            "message": self.detail,
            "recoverable": True,
            "source_document_mutation": False,
            "target_document_mutation": False,
        }


@dataclass(frozen=True)
class CopiedTargetMigrationPlan:
    """Verified immutable inputs for a separately injected atomic writer."""

    source_versions: tuple
    states: tuple
    assessment_sha256: str

    @property
    def migration_support_advertised(self):
        return False

    @property
    def production_output_authorized(self):
        return False

    @property
    def transition_ids(self):
        return tuple(state.intent.transition_id for state in self.states)

    def to_record(self):
        return {
            "assessment_sha256": self.assessment_sha256,
            "fixture_only": True,
            "migration_support_advertised": False,
            "production_output_authorized": False,
            "schema_id": MIGRATION_FIXTURE_SCHEMA_ID,
            "schema_version": MIGRATION_FIXTURE_SCHEMA_VERSION,
            "source_document_mutation": False,
            "source_versions": list(self.source_versions),
            "transition_ids": list(self.transition_ids),
        }


def _assessment_digest(assessment_json):
    return hashlib.sha256(assessment_json.encode("utf-8")).hexdigest()


def _document_objects(document):
    try:
        return tuple(document.Objects)
    except Exception as error:
        raise CopiedTargetMigrationError(
            "invalid-document",
            "source and target must expose readable Objects collections",
        ) from error


def _require_sufficient(assessment, role):
    if assessment.status != STATUS_CANONICAL_INPUTS_SUFFICIENT:
        raise CopiedTargetMigrationError(
            "{}-assessment-not-sufficient".format(role),
            "{} assessment status is {!r}; fixture migration requires complete "
            "canonical inputs".format(role, assessment.status),
        )


def prepare_copied_plain_line_transition_migration(
    source_document,
    target_document,
    compatibility_contract,
):
    """Return states only when the target is an exact family-level copy."""
    if source_document is target_document:
        raise CopiedTargetMigrationError(
            "source-target-alias",
            "the source and copied target must be different document objects",
        )
    _document_objects(source_document)
    _document_objects(target_document)
    source_assessment = assess_plain_line_transitions(
        source_document,
        compatibility_contract,
    )
    _require_sufficient(source_assessment, "source")
    target_assessment = assess_plain_line_transitions(
        target_document,
        compatibility_contract,
    )
    _require_sufficient(target_assessment, "target")

    source_json = plain_line_transition_assessment_to_json(source_assessment)
    target_json = plain_line_transition_assessment_to_json(target_assessment)
    if source_json != target_json:
        raise CopiedTargetMigrationError(
            "target-not-family-copy",
            "the target family assessment does not exactly match the source",
        )

    return CopiedTargetMigrationPlan(
        source_versions=source_assessment.outer_inspection.observed_versions,
        states=tuple(item.state for item in source_assessment.candidates),
        assessment_sha256=_assessment_digest(source_json),
    )
