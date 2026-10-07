"""Prepare one explicit derived model-scale research comparison.

The original full-size package and assembly remain authoritative. The
request selects only the frozen 4 mm/ft comparison about the same chair
origin and axes. It does not accept a manufacturing profile, admit a
package, or authorise production geometry or redistribution.
"""

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json

from tracktemplate.application.chair_definition import ChairDefinitionPackage
from tracktemplate.application.chair_research import (
    ChairAssemblyResearchResult,
    ChairResearchError,
    prepare_chair_assembly_research,
)
from tracktemplate.domain.chair_model_scale import (
    ChairModelAssemblyGeometry,
    ChairModelComponentGeometry,
    project_chair_assembly_to_model,
)


_REQUEST_CONTRACT = "tracktemplate.chair-model-scale-research-request.v1"
_REQUEST_FIELDS = (
    "contract_id", "scale_denominator", "source_frame_id", "origin_datum",
)


class ChairModelResearchError(ChairResearchError):
    """Recoverable comparison refusal without document or file mutation."""


@dataclass(frozen=True)
class ChairModelComponentResearchResult:
    """Original component identities alongside a derived model boundary."""

    role: str
    component_id: str
    procedure_id: str
    geometry: ChairModelComponentGeometry


@dataclass(frozen=True)
class ChairModelResearchResult:
    """Original signed inputs and a separately identified model comparison.

    Adapters must prepare again from the complete package, manifest and
    request. A caller-constructed result grants no research or production
    authority. Component volume sum is not a fused material volume.
    """

    package: ChairDefinitionPackage
    manifest_json: str
    manifest_signature: str
    full_size_research: ChairAssemblyResearchResult
    request_json: str
    request_signature: str
    components: tuple
    geometry: ChairModelAssemblyGeometry
    length_unit: str = "mm"
    length_basis: str = "model"
    scale_denominator: Fraction = Fraction(381, 5)


def _canonical_json(record):
    return json.dumps(
        record, allow_nan=False, ensure_ascii=True,
        separators=(",", ":"), sort_keys=True,
    )


def _validate_request(request, frame):
    if not isinstance(request, dict) or set(request) != set(_REQUEST_FIELDS):
        raise ChairModelResearchError(
            "research-model-request-invalid", "$.request",
            "model comparison requires exactly four explicit request fields",
        )
    if not all(isinstance(value, str) for value in request.values()):
        raise ChairModelResearchError(
            "research-model-request-invalid", "$.request",
            "all model comparison request fields must be strings",
        )
    if request["contract_id"] != _REQUEST_CONTRACT:
        raise ChairModelResearchError(
            "research-model-request-invalid", "$.request.contract_id",
            "unsupported model comparison request contract",
        )
    if request["scale_denominator"] != "76.2":
        raise ChairModelResearchError(
            "research-model-scale-unsupported", "$.request.scale_denominator",
            "only the exact decimal string 76.2 is supported",
        )
    for field, expected in (
        ("source_frame_id", frame["frame_id"]),
        ("origin_datum", frame["origin"]),
    ):
        if request[field] != expected:
            raise ChairModelResearchError(
                "research-model-frame-unsupported", "$.request." + field,
                "model comparison must preserve the canonical chair frame",
            )
    return dict(request)


def prepare_chair_model_research(package, manifest_text, request):
    """Validate the original assembly and derive its finite model boundary.

    The required request has contract_id, scale_denominator,
    source_frame_id and origin_datum string fields. Only the exact scale
    string '76.2' and the canonical source frame and datum are supported.
    Original package errors propagate unchanged. The request signature
    binds the complete request to the original package and manifest
    signatures; it does not replace either original signature.
    """
    full_size = prepare_chair_assembly_research(package, manifest_text)
    frame = package.to_record()["definition"]["frame"]
    request_record = _validate_request(request, frame)
    request_json = _canonical_json(request_record)
    signature_record = {
        "contract_id": _REQUEST_CONTRACT,
        "package_signature": package.content_signature,
        "manifest_signature": full_size.manifest_signature,
        "request": request_record,
    }
    request_signature = "sha256:" + hashlib.sha256(
        _canonical_json(signature_record).encode("utf-8"),
    ).hexdigest()
    geometry = project_chair_assembly_to_model(
        full_size.geometry, Fraction(381, 5),
    )
    components = tuple(
        ChairModelComponentResearchResult(
            role=role, component_id=source.component_id,
            procedure_id=source.procedure_id, geometry=boundary,
        )
        for source, (role, boundary) in zip(
            full_size.components, geometry.components,
        )
    )
    return ChairModelResearchResult(
        package=package, manifest_json=full_size.manifest_json,
        manifest_signature=full_size.manifest_signature,
        full_size_research=full_size, request_json=request_json,
        request_signature=request_signature, components=components,
        geometry=geometry,
    )
