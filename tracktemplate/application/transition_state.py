"""Versioned canonical state and signatures for the transition pilot slice."""

from dataclasses import dataclass
import hashlib
import json
import math

from tracktemplate.domain.alignment import solve_transition_length
from tracktemplate.domain.transition import TransitionIntent


TRANSITION_STATE_SCHEMA_ID = "tracktemplate.transition-state"
TRANSITION_STATE_SCHEMA_VERSION = 1
TRANSITION_STATE_READ_VERSIONS = (1,)
TRANSITION_COORDINATE_FRAME = "canonical-local-left-turn-v1"
TRANSITION_LENGTH_UNIT = "mm"
TRANSITION_ANGLE_UNIT = "rad"
TRANSITION_ALGORITHM_ID = "tracktemplate.transition-length.b15-parity.v1"
TRANSITION_TOLERANCE_PROFILE_ID = (
    "tracktemplate.transition-length.b15-parity-tolerances.v1"
)
_SIGNATURE_PREFIX = "sha256:"
_LOWER_HEXADECIMAL = "0123456789abcdef"

__all__ = (
    "TRANSITION_STATE_SCHEMA_ID",
    "TRANSITION_STATE_SCHEMA_VERSION",
    "TRANSITION_STATE_READ_VERSIONS",
    "TRANSITION_COORDINATE_FRAME",
    "TRANSITION_LENGTH_UNIT",
    "TRANSITION_ANGLE_UNIT",
    "TRANSITION_ALGORITHM_ID",
    "TRANSITION_TOLERANCE_PROFILE_ID",
    "TransitionAnalysis",
    "TransitionState",
    "TransitionStateError",
    "analyse_transition_state",
    "replace_transition_intent",
    "transition_analysis_signature",
    "transition_analysis_status",
    "transition_state_from_json",
    "transition_state_to_json",
)


class TransitionStateError(ValueError):
    """Structured, non-mutating failure at the canonical-state boundary."""

    def __init__(self, code, path, message):
        self.code = str(code)
        self.path = str(path)
        self.detail = str(message)
        super().__init__("{} at {}: {}".format(self.code, self.path, self.detail))

    def diagnostic(self):
        """Return a JSON-compatible diagnostic for an adapter or UI."""
        return {
            "code": self.code,
            "path": self.path,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
        }


def _finite_float(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TransitionStateError(
            "invalid-number",
            name,
            "expected a finite JSON number",
        )
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise TransitionStateError(
            "invalid-number",
            name,
            "expected a finite JSON number",
        ) from error
    if not math.isfinite(result):
        raise TransitionStateError(
            "invalid-number",
            name,
            "expected a finite JSON number",
        )
    return result


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


@dataclass(frozen=True)
class TransitionAnalysis:
    """One accepted derived result tied to complete input and result signatures."""

    analysis_signature: str
    result_signature: str
    transition_length_mm: float

    def __post_init__(self):
        _require_signature("$.analysis.analysis_signature", self.analysis_signature)
        _require_signature("$.analysis.result_signature", self.result_signature)
        object.__setattr__(
            self,
            "transition_length_mm",
            _finite_float(
                "$.analysis.transition_length_mm",
                self.transition_length_mm,
            ),
        )


@dataclass(frozen=True)
class TransitionState:
    """Canonical intent plus an optional, fingerprinted analytical result."""

    intent: TransitionIntent
    analysis: TransitionAnalysis | None = None
    findings: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.intent, TransitionIntent):
            raise TypeError("intent must be a TransitionIntent")
        if self.analysis is not None and not isinstance(
            self.analysis, TransitionAnalysis
        ):
            raise TypeError("analysis must be a TransitionAnalysis or None")
        if not isinstance(self.findings, tuple) or not all(
            isinstance(item, str) and item for item in self.findings
        ):
            raise TypeError("findings must be an ordered tuple of non-empty codes")


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


def transition_analysis_signature(intent):
    """Return the complete signature for the numerical transition result."""
    if not isinstance(intent, TransitionIntent):
        raise TypeError("intent must be a TransitionIntent")
    return _signature(
        {
            "algorithm_id": TRANSITION_ALGORITHM_ID,
            "angle_unit": TRANSITION_ANGLE_UNIT,
            "coordinate_frame": TRANSITION_COORDINATE_FRAME,
            "inputs": {
                "circle_centre_y_mm": intent.circle_centre_y_mm,
                "radius_mm": intent.radius_mm,
                "target_signed_offset_mm": intent.target_signed_offset_mm,
                "total_angle_rad": intent.total_angle_rad,
            },
            "length_unit": TRANSITION_LENGTH_UNIT,
            "tolerance_profile_id": TRANSITION_TOLERANCE_PROFILE_ID,
        }
    )


def _result_signature(analysis_signature, transition_length_mm):
    return _signature(
        {
            "analysis_signature": analysis_signature,
            "length_unit": TRANSITION_LENGTH_UNIT,
            "transition_length_mm": transition_length_mm,
        }
    )


def _analysis_is_current(intent, analysis):
    if analysis is None:
        return False
    expected_analysis = transition_analysis_signature(intent)
    return (
        analysis.analysis_signature == expected_analysis
        and analysis.result_signature
        == _result_signature(expected_analysis, analysis.transition_length_mm)
    )


def transition_analysis_status(state):
    """Return ``missing``, ``current`` or ``stale-or-corrupt``."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if state.analysis is None:
        return "missing"
    if _analysis_is_current(state.intent, state.analysis):
        return "current"
    return "stale-or-corrupt"


def analyse_transition_state(state):
    """Calculate once or reuse a current result without mutating ``state``."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if transition_analysis_status(state) == "current":
        return state

    intent = state.intent
    transition_length_mm = solve_transition_length(
        intent.circle_centre_y_mm,
        intent.radius_mm,
        intent.target_signed_offset_mm,
        intent.total_angle_rad,
        intent.track_name,
        intent.end_name,
    )
    analysis_signature = transition_analysis_signature(intent)
    analysis = TransitionAnalysis(
        analysis_signature=analysis_signature,
        result_signature=_result_signature(
            analysis_signature,
            transition_length_mm,
        ),
        transition_length_mm=transition_length_mm,
    )
    return TransitionState(intent=intent, analysis=analysis)


def replace_transition_intent(state, intent):
    """Replace intent, retaining only a provably unaffected result."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(intent, TransitionIntent):
        raise TypeError("intent must be a TransitionIntent")
    if intent.transition_id != state.intent.transition_id:
        raise TransitionStateError(
            "stable-identity-change",
            "$.intent.transition_id",
            "replace cannot change the identity of an existing transition",
        )

    if _analysis_is_current(state.intent, state.analysis):
        if state.analysis.analysis_signature == transition_analysis_signature(intent):
            return TransitionState(intent=intent, analysis=state.analysis)
        return TransitionState(
            intent=intent,
            findings=("analysis-invalidated",),
        )
    return TransitionState(intent=intent, findings=state.findings)


def _intent_record(intent):
    return {
        "algorithm_id": TRANSITION_ALGORITHM_ID,
        "angle_unit": TRANSITION_ANGLE_UNIT,
        "circle_centre_y_mm": intent.circle_centre_y_mm,
        "coordinate_frame": TRANSITION_COORDINATE_FRAME,
        "end_name": intent.end_name,
        "length_unit": TRANSITION_LENGTH_UNIT,
        "radius_mm": intent.radius_mm,
        "target_signed_offset_mm": intent.target_signed_offset_mm,
        "tolerance_profile_id": TRANSITION_TOLERANCE_PROFILE_ID,
        "total_angle_rad": intent.total_angle_rad,
        "track_name": intent.track_name,
        "transition_id": intent.transition_id,
    }


def transition_state_to_json(state):
    """Serialise canonical state deterministically, rejecting stale results."""
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    analysis_record = None
    if state.analysis is not None:
        if not _analysis_is_current(state.intent, state.analysis):
            raise TransitionStateError(
                "stale-derived-result",
                "$.analysis",
                "refusing to persist an unverified transition result",
            )
        analysis_record = {
            "analysis_signature": state.analysis.analysis_signature,
            "result_signature": state.analysis.result_signature,
            "transition_length_mm": state.analysis.transition_length_mm,
        }
    return _canonical_json(
        {
            "analysis": analysis_record,
            "intent": _intent_record(state.intent),
            "schema": TRANSITION_STATE_SCHEMA_ID,
            "schema_version": TRANSITION_STATE_SCHEMA_VERSION,
        }
    )


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TransitionStateError(
                "duplicate-field",
                "$",
                "duplicate JSON object field {!r}".format(key),
            )
        result[key] = value
    return result


def _reject_non_standard_number(value):
    raise TransitionStateError(
        "invalid-number",
        "$",
        "non-standard JSON number {!r} is not permitted".format(value),
    )


def _require_object(value, path):
    if not isinstance(value, dict):
        raise TransitionStateError("invalid-object", path, "expected a JSON object")
    return value


def _require_fields(value, expected, path):
    observed = set(value)
    expected = set(expected)
    if observed != expected:
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        raise TransitionStateError(
            "invalid-fields",
            path,
            "missing {!r}; unexpected {!r}".format(missing, unexpected),
        )


def _intent_from_record(record):
    path = "$.intent"
    record = _require_object(record, path)
    _require_fields(
        record,
        (
            "algorithm_id",
            "angle_unit",
            "circle_centre_y_mm",
            "coordinate_frame",
            "end_name",
            "length_unit",
            "radius_mm",
            "target_signed_offset_mm",
            "tolerance_profile_id",
            "total_angle_rad",
            "track_name",
            "transition_id",
        ),
        path,
    )
    expected_contract = (
        ("algorithm_id", TRANSITION_ALGORITHM_ID),
        ("angle_unit", TRANSITION_ANGLE_UNIT),
        ("coordinate_frame", TRANSITION_COORDINATE_FRAME),
        ("length_unit", TRANSITION_LENGTH_UNIT),
        ("tolerance_profile_id", TRANSITION_TOLERANCE_PROFILE_ID),
    )
    for field, expected in expected_contract:
        if record[field] != expected:
            raise TransitionStateError(
                "unsupported-calculation-contract",
                "$.intent." + field,
                "expected {!r}, observed {!r}".format(expected, record[field]),
            )
    try:
        return TransitionIntent(
            transition_id=record["transition_id"],
            circle_centre_y_mm=record["circle_centre_y_mm"],
            radius_mm=record["radius_mm"],
            target_signed_offset_mm=record["target_signed_offset_mm"],
            total_angle_rad=record["total_angle_rad"],
            track_name=record["track_name"],
            end_name=record["end_name"],
        )
    except (TypeError, ValueError) as error:
        raise TransitionStateError(
            "invalid-canonical-intent",
            path,
            str(error),
        ) from error


def _analysis_from_record(record, intent):
    if record is None:
        return None, ()
    try:
        record = _require_object(record, "$.analysis")
        _require_fields(
            record,
            (
                "analysis_signature",
                "result_signature",
                "transition_length_mm",
            ),
            "$.analysis",
        )
        analysis = TransitionAnalysis(
            analysis_signature=record["analysis_signature"],
            result_signature=record["result_signature"],
            transition_length_mm=record["transition_length_mm"],
        )
    except TransitionStateError:
        return None, ("corrupt-analysis-discarded",)

    expected_analysis = transition_analysis_signature(intent)
    if analysis.analysis_signature != expected_analysis:
        return None, ("stale-analysis-discarded",)
    if analysis.result_signature != _result_signature(
        expected_analysis,
        analysis.transition_length_mm,
    ):
        return None, ("corrupt-analysis-discarded",)
    return analysis, ()


def transition_state_from_json(text):
    """Load schema v1 and discard stale/corrupt derived data fail-closed."""
    if not isinstance(text, str):
        raise TypeError("canonical state must be JSON text")
    try:
        record = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_non_standard_number,
        )
    except TransitionStateError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise TransitionStateError("invalid-json", "$", str(error)) from error

    record = _require_object(record, "$")
    _require_fields(record, ("analysis", "intent", "schema", "schema_version"), "$")
    if record["schema"] != TRANSITION_STATE_SCHEMA_ID:
        raise TransitionStateError(
            "unsupported-schema",
            "$.schema",
            "expected {!r}, observed {!r}".format(
                TRANSITION_STATE_SCHEMA_ID,
                record["schema"],
            ),
        )
    version = record["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise TransitionStateError(
            "invalid-schema-version",
            "$.schema_version",
            "expected an integer schema version",
        )
    if version not in TRANSITION_STATE_READ_VERSIONS:
        raise TransitionStateError(
            "unsupported-schema-version",
            "$.schema_version",
            "supported versions are {!r}; observed {!r}".format(
                list(TRANSITION_STATE_READ_VERSIONS),
                version,
            ),
        )

    intent = _intent_from_record(record["intent"])
    analysis, findings = _analysis_from_record(record["analysis"], intent)
    return TransitionState(intent=intent, analysis=analysis, findings=findings)
