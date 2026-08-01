"""Adapter-neutral exact-validation contract for one transition centreline."""

from dataclasses import dataclass
import math

from tracktemplate.application.transition_derived import (
    TransitionDerivedCache,
    TransitionDerivedRequest,
    transition_derived_contract_signature,
    transition_derived_source_signature,
)
from tracktemplate.application.transition_state import (
    TRANSITION_ANGLE_UNIT,
    TRANSITION_COORDINATE_FRAME,
    TRANSITION_LENGTH_UNIT,
    TRANSITION_TOLERANCE_PROFILE_ID,
    TransitionState,
    TransitionStateError,
)
from tracktemplate.domain.alignment import (
    clothoid_entry_displacement_at_station,
    clothoid_entry_polyline_stations,
)


TRANSITION_EXACT_ARTIFACT_ID = (
    "tracktemplate.transition-exact.centreline-polyline.v1"
)
TRANSITION_EXACT_CONTRACT_ID = (
    "tracktemplate.transition-exact.validation-contract.v1"
)
TRANSITION_EXACT_ORACLE_ID = (
    "tracktemplate.transition-exact.euler-centreline.v1"
)
TRANSITION_EXACT_RESULT_ID = (
    "tracktemplate.transition-exact.validation-result.v1"
)
TRANSITION_EXACT_FRAME_ID = TRANSITION_COORDINATE_FRAME
TRANSITION_EXACT_LENGTH_UNIT = TRANSITION_LENGTH_UNIT
TRANSITION_EXACT_ANGLE_UNIT = TRANSITION_ANGLE_UNIT
TRANSITION_EXACT_INTEGRATION_STEPS = 240
_SIGNATURE_PREFIX = "sha256:"
_LOWER_HEXADECIMAL = "0123456789abcdef"

__all__ = (
    "TRANSITION_EXACT_ANGLE_UNIT",
    "TRANSITION_EXACT_ARTIFACT_ID",
    "TRANSITION_EXACT_CONTRACT_ID",
    "TRANSITION_EXACT_FRAME_ID",
    "TRANSITION_EXACT_INTEGRATION_STEPS",
    "TRANSITION_EXACT_LENGTH_UNIT",
    "TRANSITION_EXACT_ORACLE_ID",
    "TRANSITION_EXACT_RESULT_ID",
    "TransitionExactCentreline",
    "TransitionExactPoint",
    "TransitionExactSpecification",
    "TransitionExactValidationResult",
    "regenerate_transition_exact",
)


def _exact_error(code, path, message):
    return TransitionStateError(code, path, message)


def _finite_exact_float(path, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _exact_error(
            "invalid-exact-value",
            path,
            "expected a finite number",
        )
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise _exact_error(
            "invalid-exact-value",
            path,
            "expected a finite number",
        ) from error
    if not math.isfinite(result):
        raise _exact_error(
            "invalid-exact-value",
            path,
            "expected a finite number",
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
        raise _exact_error(
            "invalid-signature",
            path,
            "expected sha256 followed by 64 lower-case hexadecimal characters",
        )
    return value


@dataclass(frozen=True)
class TransitionExactPoint:
    """One station-ordered analytical centreline point."""

    station_mm: float
    x_mm: float
    y_mm: float
    tangent_rad: float

    def __post_init__(self):
        for name in ("station_mm", "x_mm", "y_mm", "tangent_rad"):
            object.__setattr__(
                self,
                name,
                _finite_exact_float(
                    "$.exact.point." + name,
                    getattr(self, name),
                ),
            )
        if self.station_mm < 0.0:
            raise _exact_error(
                "invalid-exact-point",
                "$.exact.point.station_mm",
                "station must not be negative",
            )
        if self.tangent_rad < 0.0:
            raise _exact_error(
                "invalid-exact-point",
                "$.exact.point.tangent_rad",
                "left-turn tangent must not be negative",
            )


@dataclass(frozen=True)
class TransitionExactCentreline:
    """A deterministic polyline with an analytical interpolation bound.

    The chord bound is the model-approximation term. Coordinate evaluation is
    separately identified by the signed exact contract and the existing B15
    parity tolerance profile.
    """

    domain_id: str
    frame_id: str
    length_unit: str
    angle_unit: str
    maximum_chord_error_mm: float
    chord_error_bound_mm: float
    points: tuple[TransitionExactPoint, ...]

    def __post_init__(self):
        if not isinstance(self.domain_id, str) or not self.domain_id.strip():
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.domain_id",
                "domain_id must be non-empty text",
            )
        expected_identifiers = (
            ("frame_id", TRANSITION_EXACT_FRAME_ID),
            ("length_unit", TRANSITION_EXACT_LENGTH_UNIT),
            ("angle_unit", TRANSITION_EXACT_ANGLE_UNIT),
        )
        for name, expected in expected_identifiers:
            if getattr(self, name) != expected:
                raise _exact_error(
                    "invalid-exact-centreline",
                    "$.exact." + name,
                    "unsupported exact-centreline identifier",
                )
        for name in (
            "maximum_chord_error_mm",
            "chord_error_bound_mm",
        ):
            object.__setattr__(
                self,
                name,
                _finite_exact_float(
                    "$.exact." + name,
                    getattr(self, name),
                ),
            )
        if self.maximum_chord_error_mm <= 0.0:
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.maximum_chord_error_mm",
                "maximum chord error must be greater than zero",
            )
        if (
            self.chord_error_bound_mm < 0.0
            or self.chord_error_bound_mm > self.maximum_chord_error_mm
        ):
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.chord_error_bound_mm",
                "chord error bound exceeds the requested maximum",
            )
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or not all(
                isinstance(point, TransitionExactPoint)
                for point in self.points
            )
        ):
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.points",
                "expected a non-empty tuple of exact points",
            )
        if self.points[0].station_mm != 0.0:
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.points[0].station_mm",
                "the first exact point must be at station zero",
            )
        if self.points[0] != TransitionExactPoint(0.0, 0.0, 0.0, 0.0):
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.points[0]",
                "the exact centreline must start at the canonical origin",
            )
        if len(self.points) == 1 and self.chord_error_bound_mm != 0.0:
            raise _exact_error(
                "invalid-exact-centreline",
                "$.exact.chord_error_bound_mm",
                "a zero-length centreline must have a zero chord bound",
            )
        for previous, current in zip(self.points, self.points[1:]):
            if current.station_mm <= previous.station_mm:
                raise _exact_error(
                    "invalid-exact-centreline",
                    "$.exact.points",
                    "exact stations must be strictly increasing",
                )
            if current.tangent_rad < previous.tangent_rad:
                raise _exact_error(
                    "invalid-exact-centreline",
                    "$.exact.points",
                    "left-turn tangents must be non-decreasing",
                )


@dataclass(frozen=True)
class TransitionExactSpecification:
    """Complete caller-owned resolution inputs for exact validation."""

    maximum_chord_error_mm: float
    maximum_segment_count: int

    def __post_init__(self):
        object.__setattr__(
            self,
            "maximum_chord_error_mm",
            _finite_exact_float(
                "$.exact.maximum_chord_error_mm",
                self.maximum_chord_error_mm,
            ),
        )
        if self.maximum_chord_error_mm <= 0.0:
            raise _exact_error(
                "invalid-exact-specification",
                "$.exact.maximum_chord_error_mm",
                "maximum chord error must be greater than zero",
            )
        if (
            isinstance(self.maximum_segment_count, bool)
            or not isinstance(self.maximum_segment_count, int)
            or self.maximum_segment_count < 1
        ):
            raise _exact_error(
                "invalid-exact-specification",
                "$.exact.maximum_segment_count",
                "maximum segment count must be a positive integer",
            )

    def derived_request(self):
        """Return the complete exact-stage lifecycle request."""
        return TransitionDerivedRequest(
            stage="exact-validation",
            contract_signature=transition_derived_contract_signature(
                TRANSITION_EXACT_CONTRACT_ID,
                {
                    "angle_unit": TRANSITION_EXACT_ANGLE_UNIT,
                    "artifact_id": TRANSITION_EXACT_ARTIFACT_ID,
                    "frame_id": TRANSITION_EXACT_FRAME_ID,
                    "integration_steps": TRANSITION_EXACT_INTEGRATION_STEPS,
                    "length_unit": TRANSITION_EXACT_LENGTH_UNIT,
                    "maximum_chord_error_mm": self.maximum_chord_error_mm,
                    "maximum_segment_count": self.maximum_segment_count,
                    "oracle_id": TRANSITION_EXACT_ORACLE_ID,
                    "tolerance_profile_id": TRANSITION_TOLERANCE_PROFILE_ID,
                },
            ),
        )


@dataclass(frozen=True)
class TransitionExactValidationResult:
    """A valid profile tied to complete source and result signatures."""

    source_signature: str
    artifact_signature: str
    result_signature: str
    centreline: TransitionExactCentreline

    def __post_init__(self):
        _require_signature("$.exact.source_signature", self.source_signature)
        _require_signature(
            "$.exact.artifact_signature",
            self.artifact_signature,
        )
        _require_signature("$.exact.result_signature", self.result_signature)
        if not isinstance(self.centreline, TransitionExactCentreline):
            raise TypeError("centreline must be a TransitionExactCentreline")


def _centreline_record(centreline):
    return {
        "angle_unit": centreline.angle_unit,
        "chord_error_bound_mm": centreline.chord_error_bound_mm,
        "domain_id": centreline.domain_id,
        "frame_id": centreline.frame_id,
        "length_unit": centreline.length_unit,
        "maximum_chord_error_mm": centreline.maximum_chord_error_mm,
        "points": [
            {
                "station_mm": point.station_mm,
                "tangent_rad": point.tangent_rad,
                "x_mm": point.x_mm,
                "y_mm": point.y_mm,
            }
            for point in centreline.points
        ],
    }


def _build_transition_exact_result(state, specification, source_signature):
    try:
        stations, chord_error_bound_mm = (
            clothoid_entry_polyline_stations(
                state.analysis.transition_length_mm,
                state.intent.radius_mm,
                specification.maximum_chord_error_mm,
                specification.maximum_segment_count,
            )
        )
    except ValueError as error:
        raise _exact_error(
            "exact-resolution-exceeded",
            "$.exact.maximum_segment_count",
            str(error),
        ) from error

    points = tuple(
        TransitionExactPoint(
            station_mm=station_mm,
            x_mm=x_mm,
            y_mm=y_mm,
            tangent_rad=tangent_rad,
        )
        for station_mm in stations
        for x_mm, y_mm, tangent_rad in (
            clothoid_entry_displacement_at_station(
                station_mm,
                state.analysis.transition_length_mm,
                state.intent.radius_mm,
                TRANSITION_EXACT_INTEGRATION_STEPS,
            ),
        )
    )
    centreline = TransitionExactCentreline(
        domain_id=state.intent.transition_id,
        frame_id=TRANSITION_EXACT_FRAME_ID,
        length_unit=TRANSITION_EXACT_LENGTH_UNIT,
        angle_unit=TRANSITION_EXACT_ANGLE_UNIT,
        maximum_chord_error_mm=specification.maximum_chord_error_mm,
        chord_error_bound_mm=chord_error_bound_mm,
        points=points,
    )
    artifact_signature = transition_derived_contract_signature(
        TRANSITION_EXACT_ARTIFACT_ID,
        _centreline_record(centreline),
    )
    result_signature = transition_derived_contract_signature(
        TRANSITION_EXACT_RESULT_ID,
        {
            "artifact_signature": artifact_signature,
            "oracle_id": TRANSITION_EXACT_ORACLE_ID,
            "source_signature": source_signature,
            "status": "valid",
        },
    )
    return TransitionExactValidationResult(
        source_signature=source_signature,
        artifact_signature=artifact_signature,
        result_signature=result_signature,
        centreline=centreline,
    )


def regenerate_transition_exact(cache, state, specification):
    """Reuse or regenerate one signed, adapter-neutral exact profile."""
    if not isinstance(cache, TransitionDerivedCache):
        raise TypeError("cache must be a TransitionDerivedCache")
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(specification, TransitionExactSpecification):
        raise TypeError(
            "specification must be a TransitionExactSpecification"
        )

    request = specification.derived_request()
    source_signature = transition_derived_source_signature(state, request)

    def build(current_state, current_request):
        if current_request != request:
            raise _exact_error(
                "invalid-exact-specification",
                "$.derived.contract_signature",
                "exact builder received a mismatched lifecycle request",
            )
        return _build_transition_exact_result(
            current_state,
            specification,
            source_signature,
        )

    artifact = cache.regenerate(state, request, build)
    result = artifact.payload
    expected_artifact_signature = None
    expected_result_signature = None
    if isinstance(result, TransitionExactValidationResult):
        expected_artifact_signature = transition_derived_contract_signature(
            TRANSITION_EXACT_ARTIFACT_ID,
            _centreline_record(result.centreline),
        )
        expected_result_signature = transition_derived_contract_signature(
            TRANSITION_EXACT_RESULT_ID,
            {
                "artifact_signature": expected_artifact_signature,
                "oracle_id": TRANSITION_EXACT_ORACLE_ID,
                "source_signature": artifact.source_signature,
                "status": "valid",
            },
        )
    if (
        not isinstance(result, TransitionExactValidationResult)
        or result.source_signature != artifact.source_signature
        or result.artifact_signature != expected_artifact_signature
        or result.result_signature != expected_result_signature
    ):
        raise _exact_error(
            "invalid-exact-artifact",
            "$.exact",
            "the current exact-stage cache contains an incompatible payload",
        )
    return artifact
