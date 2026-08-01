"""Adapter-neutral DXF export contract for one validated transition."""

from dataclasses import dataclass
import hashlib

from tracktemplate.application.transition_derived import (
    TransitionDerivedRequest,
    transition_derived_contract_signature,
    transition_derived_source_signature,
)
from tracktemplate.application.transition_exact import (
    TRANSITION_EXACT_ARTIFACT_ID,
    TRANSITION_EXACT_FRAME_ID,
    TRANSITION_EXACT_LENGTH_UNIT,
    TransitionExactSpecification,
    TransitionExactValidationResult,
    transition_exact_result_from_artifact,
)
from tracktemplate.application.transition_state import (
    TransitionState,
    TransitionStateError,
    transition_state_to_json,
)


TRANSITION_DXF_EXPORT_AUDIT_SCOPE = "core-rail-timber-path"
TRANSITION_DXF_EXPORT_COLLISION_POLICY = "reuse-identical-or-fail"
TRANSITION_DXF_EXPORT_CONTRACT_ID = (
    "tracktemplate.transition-export.dxf-centreline.v1"
)
TRANSITION_DXF_EXPORT_FORMAT_ID = "autocad-ascii-dxf-2000"
TRANSITION_DXF_EXPORT_LAYER_NAME = "TRACKTEMPLATE_TRANSITION_CENTRELINE"
TRANSITION_DXF_EXPORT_MANIFEST_SCHEMA_ID = (
    "urn:tracktemplate:dependency-manifest:1"
)
TRANSITION_DXF_EXPORT_PROJECT_STATUS = "unknown"
TRANSITION_DXF_EXPORT_RESULT_ID = (
    "tracktemplate.transition-export.dxf-result.v1"
)
_SIGNATURE_PREFIX = "sha256:"
_LOWER_HEXADECIMAL = "0123456789abcdef"

__all__ = (
    "TRANSITION_DXF_EXPORT_AUDIT_SCOPE",
    "TRANSITION_DXF_EXPORT_COLLISION_POLICY",
    "TRANSITION_DXF_EXPORT_CONTRACT_ID",
    "TRANSITION_DXF_EXPORT_FORMAT_ID",
    "TRANSITION_DXF_EXPORT_LAYER_NAME",
    "TRANSITION_DXF_EXPORT_MANIFEST_SCHEMA_ID",
    "TRANSITION_DXF_EXPORT_PROJECT_STATUS",
    "TRANSITION_DXF_EXPORT_RESULT_ID",
    "TransitionDxfExportPlan",
    "TransitionDxfExportReceipt",
    "TransitionDxfExportRequest",
    "prepare_transition_dxf_export",
)


def _export_error(code, path, message):
    return TransitionStateError(code, path, message)


def _require_signature(path, value):
    if (
        not isinstance(value, str)
        or not value.startswith(_SIGNATURE_PREFIX)
        or len(value) != len(_SIGNATURE_PREFIX) + 64
        or any(
            character not in _LOWER_HEXADECIMAL
            for character in value[len(_SIGNATURE_PREFIX):]
        )
    ):
        raise _export_error(
            "invalid-signature",
            path,
            "expected sha256 followed by 64 lower-case hexadecimal "
            "characters",
        )
    return value


def _require_digest(path, value):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWER_HEXADECIMAL for character in value)
    ):
        raise _export_error(
            "invalid-digest",
            path,
            "expected 64 lower-case hexadecimal characters",
        )
    return value


def _signature_digest(value):
    return _require_signature("$.transition_export.signature", value)[
        len(_SIGNATURE_PREFIX):
    ]


@dataclass(frozen=True)
class TransitionDxfExportRequest:
    """One private-development destination request.

    The adapter resolves this path and rejects relative, symbolic-link or
    unsafe destination state. Existing complete output is reused only when
    both files are byte-identical; this contract never overwrites a file.
    """

    output_directory: str
    generator_version: str

    def __post_init__(self):
        if (
            not isinstance(self.output_directory, str)
            or not self.output_directory.strip()
            or "\x00" in self.output_directory
        ):
            raise _export_error(
                "invalid-transition-dxf-export-request",
                "$.transition_export.output_directory",
                "output_directory must be non-empty text without NUL bytes",
            )
        if (
            not isinstance(self.generator_version, str)
            or not self.generator_version.strip()
            or self.generator_version != self.generator_version.strip()
            or any(
                ord(character) < 32
                for character in self.generator_version
            )
        ):
            raise _export_error(
                "invalid-transition-dxf-export-request",
                "$.transition_export.generator_version",
                "generator_version must be trimmed non-empty text without "
                "control characters",
            )

    def derived_request(self, exact_validation_result_signature):
        """Return the complete signed export-stage dependency request."""
        _require_signature(
            "$.transition_export.exact_validation_result_signature",
            exact_validation_result_signature,
        )
        contract_signature = transition_derived_contract_signature(
            TRANSITION_DXF_EXPORT_CONTRACT_ID,
            {
                "audit_scope": TRANSITION_DXF_EXPORT_AUDIT_SCOPE,
                "collision_policy": (
                    TRANSITION_DXF_EXPORT_COLLISION_POLICY
                ),
                "exact_artifact_id": TRANSITION_EXACT_ARTIFACT_ID,
                "format_id": TRANSITION_DXF_EXPORT_FORMAT_ID,
                "frame_id": TRANSITION_EXACT_FRAME_ID,
                "generator_version": self.generator_version,
                "layer_name": TRANSITION_DXF_EXPORT_LAYER_NAME,
                "length_unit": TRANSITION_EXACT_LENGTH_UNIT,
                "manifest_schema_id": (
                    TRANSITION_DXF_EXPORT_MANIFEST_SCHEMA_ID
                ),
                "project_status": TRANSITION_DXF_EXPORT_PROJECT_STATUS,
            },
        )
        return TransitionDerivedRequest(
            stage="export",
            contract_signature=contract_signature,
            exact_validation_result_signature=(
                exact_validation_result_signature
            ),
        )


@dataclass(frozen=True)
class TransitionDxfExportPlan:
    """A current exact result and deterministic target names for export."""

    request: TransitionDxfExportRequest
    canonical_model_sha256: str
    source_signature: str
    contract_signature: str
    exact_result: TransitionExactValidationResult
    dxf_filename: str
    manifest_filename: str

    def __post_init__(self):
        if not isinstance(self.request, TransitionDxfExportRequest):
            raise TypeError("request must be a TransitionDxfExportRequest")
        _require_digest(
            "$.transition_export.canonical_model_sha256",
            self.canonical_model_sha256,
        )
        _require_signature(
            "$.transition_export.source_signature",
            self.source_signature,
        )
        _require_signature(
            "$.transition_export.contract_signature",
            self.contract_signature,
        )
        if not isinstance(
            self.exact_result,
            TransitionExactValidationResult,
        ):
            raise TypeError(
                "exact_result must be a TransitionExactValidationResult"
            )
        digest = _signature_digest(
            self.exact_result.artifact_signature
        )
        stem = "transition-centreline-" + digest
        if self.dxf_filename != stem + ".dxf":
            raise _export_error(
                "invalid-transition-dxf-export-plan",
                "$.transition_export.dxf_filename",
                "DXF filename does not match the exact artifact",
            )
        if self.manifest_filename != stem + ".dependency-manifest.json":
            raise _export_error(
                "invalid-transition-dxf-export-plan",
                "$.transition_export.manifest_filename",
                "manifest filename does not match the exact artifact",
            )


@dataclass(frozen=True)
class TransitionDxfExportReceipt:
    """Neutral hashes and disposition for one complete two-file export."""

    contract_id: str
    source_signature: str
    exact_result_signature: str
    geometry_signature: str
    dxf_filename: str
    dxf_sha256: str
    manifest_filename: str
    manifest_sha256: str
    project_status: str
    disposition: str
    cleanup_complete: bool
    result_signature: str = ""

    def __post_init__(self):
        if self.contract_id != TRANSITION_DXF_EXPORT_CONTRACT_ID:
            raise ValueError("unsupported transition DXF export contract")
        for name in (
            "source_signature",
            "exact_result_signature",
            "geometry_signature",
        ):
            _require_signature(
                "$.transition_export." + name,
                getattr(self, name),
            )
        for name in ("dxf_sha256", "manifest_sha256"):
            _require_digest(
                "$.transition_export." + name,
                getattr(self, name),
            )
        for name in ("dxf_filename", "manifest_filename"):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value
                or "/" in value
                or "\\" in value
            ):
                raise ValueError("{} must be one filename".format(name))
        if self.project_status != TRANSITION_DXF_EXPORT_PROJECT_STATUS:
            raise ValueError(
                "transition DXF output must remain status unknown"
            )
        if self.disposition not in ("created", "reused"):
            raise ValueError("disposition must be created or reused")
        if not isinstance(self.cleanup_complete, bool):
            raise TypeError("cleanup_complete must be a boolean")

        signature_inputs = {
            "cleanup_complete": self.cleanup_complete,
            "contract_id": self.contract_id,
            "disposition": self.disposition,
            "dxf": {
                "filename": self.dxf_filename,
                "sha256": self.dxf_sha256,
            },
            "exact_result_signature": self.exact_result_signature,
            "geometry_signature": self.geometry_signature,
            "manifest": {
                "filename": self.manifest_filename,
                "sha256": self.manifest_sha256,
            },
            "project_status": self.project_status,
            "source_signature": self.source_signature,
        }
        expected_signature = transition_derived_contract_signature(
            TRANSITION_DXF_EXPORT_RESULT_ID,
            signature_inputs,
        )
        if self.result_signature:
            _require_signature(
                "$.transition_export.result_signature",
                self.result_signature,
            )
            if self.result_signature != expected_signature:
                raise ValueError(
                    "result_signature does not match the export receipt"
                )
        else:
            object.__setattr__(
                self,
                "result_signature",
                expected_signature,
            )


def prepare_transition_dxf_export(
    state,
    artifact,
    exact_specification,
    request,
):
    """Verify current exact input and return a deterministic export plan."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(exact_specification, TransitionExactSpecification):
        raise TypeError(
            "exact_specification must be a TransitionExactSpecification"
        )
    if not isinstance(request, TransitionDxfExportRequest):
        raise TypeError("request must be a TransitionDxfExportRequest")

    result = transition_exact_result_from_artifact(artifact)
    expected_exact_source = transition_derived_source_signature(
        state,
        exact_specification.derived_request(),
    )
    if result.source_signature != expected_exact_source:
        raise _export_error(
            "stale-exact-validation",
            "$.transition_export.exact_validation_result_signature",
            "the exact-validation artifact is not current for this state "
            "and specification",
        )

    derived_request = request.derived_request(result.result_signature)
    source_signature = transition_derived_source_signature(
        state,
        derived_request,
    )
    digest = _signature_digest(result.artifact_signature)
    stem = "transition-centreline-" + digest
    return TransitionDxfExportPlan(
        request=request,
        canonical_model_sha256=hashlib.sha256(
            transition_state_to_json(state).encode("utf-8")
        ).hexdigest(),
        source_signature=source_signature,
        contract_signature=derived_request.contract_signature,
        exact_result=result,
        dxf_filename=stem + ".dxf",
        manifest_filename=stem + ".dependency-manifest.json",
    )
