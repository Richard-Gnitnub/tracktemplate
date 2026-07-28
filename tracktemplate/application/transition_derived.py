"""Ephemeral derived-state lifecycle for the bounded transition slice."""

from dataclasses import dataclass, field
import hashlib
import json
import math

from tracktemplate.application.transition_state import (
    TransitionState,
    TransitionStateError,
    transition_analysis_status,
)


TRANSITION_DERIVED_STAGES = (
    "preview",
    "exact-validation",
    "export",
)
_SIGNATURE_PREFIX = "sha256:"
_LOWER_HEXADECIMAL = "0123456789abcdef"

__all__ = (
    "TRANSITION_DERIVED_STAGES",
    "TransitionDerivedArtifact",
    "TransitionDerivedCache",
    "TransitionDerivedRequest",
    "transition_derived_contract_signature",
    "transition_derived_source_signature",
)


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


def _validate_contract_value(value, path, active_containers):
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise TransitionStateError(
            "invalid-derived-contract",
            path,
            "contract numbers must be finite",
        )

    if isinstance(value, (dict, list)):
        identity = id(value)
        if identity in active_containers:
            raise TransitionStateError(
                "invalid-derived-contract",
                path,
                "contract inputs must not contain a reference cycle",
            )
        active_containers.add(identity)
        try:
            if isinstance(value, list):
                for index, item in enumerate(value):
                    _validate_contract_value(
                        item,
                        "{}[{}]".format(path, index),
                        active_containers,
                    )
                return
            for key, item in value.items():
                if not isinstance(key, str) or not key:
                    raise TransitionStateError(
                        "invalid-derived-contract",
                        path,
                        "contract object keys must be non-empty text",
                    )
                _validate_contract_value(
                    item,
                    "{}.{!s}".format(path, key),
                    active_containers,
                )
            return
        finally:
            active_containers.remove(identity)

    raise TransitionStateError(
        "invalid-derived-contract",
        path,
        "expected a JSON value, observed {!r}".format(type(value).__name__),
    )


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
        raise TransitionStateError(
            "invalid-signature",
            path,
            "expected sha256 followed by 64 lower-case hexadecimal characters",
        )
    return value


def _require_stage(value):
    if value not in TRANSITION_DERIVED_STAGES:
        raise TransitionStateError(
            "invalid-derived-stage",
            "$.derived.stage",
            "expected one of {!r}; observed {!r}".format(
                TRANSITION_DERIVED_STAGES,
                value,
            ),
        )
    return value


@dataclass(frozen=True)
class TransitionDerivedRequest:
    """Complete non-canonical inputs for one derived transition stage."""

    stage: str
    contract_signature: str
    exact_validation_result_signature: str | None = None

    def __post_init__(self):
        _require_stage(self.stage)
        _require_signature(
            "$.derived.contract_signature",
            self.contract_signature,
        )
        dependency = self.exact_validation_result_signature
        if self.stage == "export":
            if dependency is None:
                raise TransitionStateError(
                    "invalid-derived-dependencies",
                    "$.derived.exact_validation_result_signature",
                    "export requires an exact-validation result signature",
                )
            _require_signature(
                "$.derived.exact_validation_result_signature",
                dependency,
            )
        elif dependency is not None:
            raise TransitionStateError(
                "invalid-derived-dependencies",
                "$.derived.exact_validation_result_signature",
                "only export accepts an exact-validation result signature",
            )


@dataclass(frozen=True)
class TransitionDerivedArtifact:
    """One disposable adapter artifact tied to its complete source signature."""

    stage: str
    source_signature: str
    payload: object = field(compare=False, repr=False)

    def __post_init__(self):
        _require_stage(self.stage)
        _require_signature(
            "$.derived.source_signature",
            self.source_signature,
        )
        if self.payload is None:
            raise TransitionStateError(
                "invalid-derived-artifact",
                "$.derived.payload",
                "a derived-artifact builder must return a payload",
            )


def transition_derived_contract_signature(contract_id, inputs):
    """Sign every stage-owned input without admitting it to canonical state."""
    if not isinstance(contract_id, str) or not contract_id.strip():
        raise TransitionStateError(
            "invalid-derived-contract",
            "$.derived.contract_id",
            "contract_id must be non-empty text",
        )
    if not isinstance(inputs, dict):
        raise TransitionStateError(
            "invalid-derived-contract",
            "$.derived.contract_inputs",
            "contract inputs must be a JSON object",
        )
    _validate_contract_value(
        inputs,
        "$.derived.contract_inputs",
        set(),
    )
    try:
        return _signature(
            {
                "contract_id": contract_id,
                "inputs": inputs,
            }
        )
    except (TypeError, ValueError) as error:
        raise TransitionStateError(
            "invalid-derived-contract",
            "$.derived.contract_inputs",
            str(error),
        ) from error


def transition_derived_source_signature(state, request):
    """Return the current source signature for one disposable stage."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(request, TransitionDerivedRequest):
        raise TypeError("request must be a TransitionDerivedRequest")
    if transition_analysis_status(state) != "current":
        raise TransitionStateError(
            "analysis-required",
            "$.analysis",
            "derived stages require a current transition analysis",
        )

    record = {
        "analysis_signature": state.analysis.analysis_signature,
        "analysis_result_signature": state.analysis.result_signature,
        "contract_signature": request.contract_signature,
        "stage": request.stage,
        "transition_id": state.intent.transition_id,
    }
    if request.stage in ("preview", "export"):
        record["diagnostic_labels"] = {
            "end_name": state.intent.end_name,
            "track_name": state.intent.track_name,
        }
    if request.stage == "export":
        record["exact_validation_result_signature"] = (
            request.exact_validation_result_signature
        )
    return _signature(record)


class TransitionDerivedCache:
    """Hold disposable adapter artifacts outside canonical persistence."""

    def __init__(self):
        self._artifacts = {}

    def artifact(self, stage):
        """Return the retained artifact for ``stage``, if any."""
        stage = _require_stage(stage)
        return self._artifacts.get(stage)

    def status(self, state, request):
        """Return ``missing``, ``current`` or ``stale`` for a request."""
        expected = transition_derived_source_signature(state, request)
        artifact = self._artifacts.get(request.stage)
        if artifact is None:
            return "missing"
        if artifact.source_signature == expected:
            return "current"
        return "stale"

    def regenerate(self, state, request, builder):
        """Reuse a current artifact or atomically replace it after a build."""
        if not callable(builder):
            raise TypeError("builder must be callable")
        expected = transition_derived_source_signature(state, request)
        current = self._artifacts.get(request.stage)
        if current is not None and current.source_signature == expected:
            return current

        payload = builder(state, request)
        artifact = TransitionDerivedArtifact(
            stage=request.stage,
            source_signature=expected,
            payload=payload,
        )
        self._artifacts[request.stage] = artifact
        return artifact

    def discard(self, stage=None):
        """Discard one stage or every retained stage deterministically."""
        if stage is None:
            discarded = tuple(
                candidate
                for candidate in TRANSITION_DERIVED_STAGES
                if candidate in self._artifacts
            )
            self._artifacts.clear()
            return discarded

        stage = _require_stage(stage)
        if stage not in self._artifacts:
            return ()
        del self._artifacts[stage]
        return (stage,)
