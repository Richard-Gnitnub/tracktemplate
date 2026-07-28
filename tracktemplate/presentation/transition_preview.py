"""Renderer-neutral 2D preview scene for the bounded transition slice."""

from dataclasses import dataclass
import math

from tracktemplate.application.transition_derived import (
    TransitionDerivedCache,
    TransitionDerivedRequest,
    transition_derived_contract_signature,
)
from tracktemplate.application.transition_state import (
    TRANSITION_COORDINATE_FRAME,
    TRANSITION_LENGTH_UNIT,
    TransitionState,
    TransitionStateError,
)
from tracktemplate.domain.alignment import (
    GEOMETRY_TOLERANCE,
    clothoid_entry_displacement_at_station,
)


TRANSITION_PREVIEW_CONTRACT_ID = (
    "tracktemplate.transition-preview.centreline.v1"
)
TRANSITION_PREVIEW_FRAME_ID = TRANSITION_COORDINATE_FRAME
TRANSITION_PREVIEW_LENGTH_UNIT = TRANSITION_LENGTH_UNIT
TRANSITION_PREVIEW_CENTRELINE_LAYER_ID = "track-centrelines"

__all__ = (
    "TRANSITION_PREVIEW_CENTRELINE_LAYER_ID",
    "TRANSITION_PREVIEW_CONTRACT_ID",
    "TRANSITION_PREVIEW_FRAME_ID",
    "TRANSITION_PREVIEW_LENGTH_UNIT",
    "TransitionPreviewPoint",
    "TransitionPreviewPolyline",
    "TransitionPreviewScene",
    "TransitionPreviewSpecification",
    "regenerate_transition_preview",
)


def _preview_error(code, path, message):
    return TransitionStateError(code, path, message)


def _finite_preview_float(path, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _preview_error(
            "invalid-preview-point",
            path,
            "expected a finite number in millimetres",
        )
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise _preview_error(
            "invalid-preview-point",
            path,
            "expected a finite number in millimetres",
        ) from error
    if not math.isfinite(result):
        raise _preview_error(
            "invalid-preview-point",
            path,
            "expected a finite number in millimetres",
        )
    return result


@dataclass(frozen=True)
class TransitionPreviewPoint:
    """One station-ordered 2D point in millimetres."""

    station_mm: float
    x_mm: float
    y_mm: float

    def __post_init__(self):
        for name in ("station_mm", "x_mm", "y_mm"):
            object.__setattr__(
                self,
                name,
                _finite_preview_float(
                    "$.preview.point." + name,
                    getattr(self, name),
                ),
            )
        if self.station_mm < 0.0:
            raise _preview_error(
                "invalid-preview-point",
                "$.preview.point.station_mm",
                "station must not be negative",
            )


@dataclass(frozen=True)
class TransitionPreviewPolyline:
    """One semantic preview element with stable selection identity."""

    layer_id: str
    visual_id: str
    domain_id: str
    track_name: str
    end_name: str
    points: tuple[TransitionPreviewPoint, ...]

    def __post_init__(self):
        for name in ("layer_id", "visual_id", "domain_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise _preview_error(
                    "invalid-preview-polyline",
                    "$.preview.polyline." + name,
                    "expected non-empty text",
                )
        for name in ("track_name", "end_name"):
            if not isinstance(getattr(self, name), str):
                raise _preview_error(
                    "invalid-preview-polyline",
                    "$.preview.polyline." + name,
                    "expected diagnostic text",
                )
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or not all(
                isinstance(point, TransitionPreviewPoint)
                for point in self.points
            )
        ):
            raise _preview_error(
                "invalid-preview-polyline",
                "$.preview.polyline.points",
                "expected a non-empty tuple of preview points",
            )
        if self.points[0].station_mm != 0.0:
            raise _preview_error(
                "invalid-preview-polyline",
                "$.preview.polyline.points[0].station_mm",
                "the first preview point must be at station zero",
            )
        for previous, current in zip(self.points, self.points[1:]):
            if current.station_mm <= previous.station_mm:
                raise _preview_error(
                    "invalid-preview-polyline",
                    "$.preview.polyline.points",
                    "preview stations must be strictly increasing",
                )


@dataclass(frozen=True)
class TransitionPreviewScene:
    """A renderer-neutral collection of ordered 2D transition elements."""

    frame_id: str
    length_unit: str
    polylines: tuple[TransitionPreviewPolyline, ...]

    def __post_init__(self):
        if self.frame_id != TRANSITION_PREVIEW_FRAME_ID:
            raise _preview_error(
                "invalid-preview-scene",
                "$.preview.frame_id",
                "unsupported preview coordinate frame",
            )
        if self.length_unit != TRANSITION_PREVIEW_LENGTH_UNIT:
            raise _preview_error(
                "invalid-preview-scene",
                "$.preview.length_unit",
                "unsupported preview length unit",
            )
        if (
            not isinstance(self.polylines, tuple)
            or len(self.polylines) != 1
            or not isinstance(
                self.polylines[0],
                TransitionPreviewPolyline,
            )
        ):
            raise _preview_error(
                "invalid-preview-scene",
                "$.preview.polylines",
                "the v1 transition scene requires one preview polyline",
            )
        if (
            self.polylines[0].layer_id
            != TRANSITION_PREVIEW_CENTRELINE_LAYER_ID
        ):
            raise _preview_error(
                "invalid-preview-scene",
                "$.preview.polylines[0].layer_id",
                "the v1 transition scene requires the centreline layer",
            )


@dataclass(frozen=True)
class TransitionPreviewSpecification:
    """Complete stage-owned inputs for a transition centreline preview."""

    segment_count: int

    def __post_init__(self):
        if (
            isinstance(self.segment_count, bool)
            or not isinstance(self.segment_count, int)
            or self.segment_count < 1
        ):
            raise _preview_error(
                "invalid-preview-specification",
                "$.preview.segment_count",
                "segment_count must be a positive integer",
            )

    def derived_request(self):
        """Return the complete lifecycle request for this specification."""
        return TransitionDerivedRequest(
            stage="preview",
            contract_signature=transition_derived_contract_signature(
                TRANSITION_PREVIEW_CONTRACT_ID,
                {
                    "frame_id": TRANSITION_PREVIEW_FRAME_ID,
                    "layer_id": TRANSITION_PREVIEW_CENTRELINE_LAYER_ID,
                    "length_unit": TRANSITION_PREVIEW_LENGTH_UNIT,
                    "segment_count": self.segment_count,
                },
            ),
        )


def _sample_transition_points(state, segment_count):
    transition_length_mm = state.analysis.transition_length_mm
    radius_mm = state.intent.radius_mm
    if transition_length_mm <= GEOMETRY_TOLERANCE:
        return (TransitionPreviewPoint(0.0, 0.0, 0.0),)

    points = []
    for index in range(segment_count + 1):
        if index == segment_count:
            station_mm = transition_length_mm
        else:
            station_mm = (
                transition_length_mm
                * float(index)
                / float(segment_count)
            )
        x_mm, y_mm, _angle_rad = clothoid_entry_displacement_at_station(
            station_mm,
            transition_length_mm,
            radius_mm,
        )
        points.append(
            TransitionPreviewPoint(
                station_mm=station_mm,
                x_mm=x_mm,
                y_mm=y_mm,
            )
        )
    return tuple(points)


def _build_transition_preview_scene(state, specification):
    intent = state.intent
    polyline = TransitionPreviewPolyline(
        layer_id=TRANSITION_PREVIEW_CENTRELINE_LAYER_ID,
        visual_id=intent.transition_id + ":preview:centreline",
        domain_id=intent.transition_id,
        track_name=intent.track_name,
        end_name=intent.end_name,
        points=_sample_transition_points(
            state,
            specification.segment_count,
        ),
    )
    return TransitionPreviewScene(
        frame_id=TRANSITION_PREVIEW_FRAME_ID,
        length_unit=TRANSITION_PREVIEW_LENGTH_UNIT,
        polylines=(polyline,),
    )


def regenerate_transition_preview(cache, state, specification):
    """Reuse or regenerate one disposable renderer-neutral preview scene."""
    if not isinstance(cache, TransitionDerivedCache):
        raise TypeError("cache must be a TransitionDerivedCache")
    if not isinstance(state, TransitionState):
        raise TypeError("state must be a TransitionState")
    if not isinstance(specification, TransitionPreviewSpecification):
        raise TypeError(
            "specification must be a TransitionPreviewSpecification"
        )

    request = specification.derived_request()

    def build(current_state, current_request):
        if current_request != request:
            raise _preview_error(
                "invalid-preview-specification",
                "$.derived.contract_signature",
                "preview builder received a mismatched lifecycle request",
            )
        return _build_transition_preview_scene(
            current_state,
            specification,
        )

    return cache.regenerate(state, request, build)
