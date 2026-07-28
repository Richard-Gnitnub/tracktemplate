#!/usr/bin/env python3
"""Validate the renderer-neutral transition preview-scene tranche."""

from dataclasses import replace
import hashlib
import json
import math
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.domain import alignment  # noqa: E402
from tracktemplate.presentation import transition_preview as preview  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
EXPECTED_FOUR_SEGMENT_POINTS = (
    (0.0, 0.0, 0.0),
    (74.99999999796813, 74.99846355268964, 0.3578191914683588),
    (149.99999999593626, 149.95084074115536, 2.861925278092323),
    (224.9999999939044, 224.6269269665021, 9.649814394046635),
    (299.9999999918725, 298.4304805195221, 22.815119307042202),
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _intent(transition_length_mm=300.0, **changes):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    values = {
        "transition_id": "transition:phase4:preview",
        "circle_centre_y_mm": circle_centre_y_mm,
        "radius_mm": radius_mm,
        "target_signed_offset_mm": api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        "total_angle_rad": math.pi / 2.0,
        "track_name": "Phase 4 preview transition",
        "end_name": "Entry",
    }
    values.update(changes)
    return api.TransitionIntent(**values)


def _state(transition_length_mm=300.0, **changes):
    return api.analyse_transition_state(
        api.TransitionState(
            _intent(
                transition_length_mm=transition_length_mm,
                **changes,
            )
        )
    )


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _assert_point(point, expected):
    assert math.isclose(point.station_mm, expected[0], abs_tol=1.0e-10)
    assert math.isclose(point.x_mm, expected[1], abs_tol=1.0e-10)
    assert math.isclose(point.y_mm, expected[2], abs_tol=1.0e-10)


def _validate_fixed_transition_sampling_math():
    # Interior coordinates were evaluated independently from the analytical
    # Fresnel power series for theta(s) = s**2 / (2 * radius * length).
    transition_length_mm = EXPECTED_FOUR_SEGMENT_POINTS[-1][0]
    radius_mm = 655.0
    for station_mm, expected_x_mm, expected_y_mm in (
        EXPECTED_FOUR_SEGMENT_POINTS
    ):
        x_mm, y_mm, angle_rad = (
            alignment.clothoid_entry_displacement_at_station(
                station_mm,
                transition_length_mm,
                radius_mm,
            )
        )
        assert math.isclose(x_mm, expected_x_mm, abs_tol=1.0e-10)
        assert math.isclose(y_mm, expected_y_mm, abs_tol=1.0e-10)
        expected_angle_rad = (
            station_mm
            * station_mm
            / (2.0 * radius_mm * transition_length_mm)
            if transition_length_mm
            else 0.0
        )
        assert math.isclose(
            angle_rad,
            expected_angle_rad,
            abs_tol=1.0e-15,
        )

    endpoint = alignment.clothoid_entry_displacement_at_station(
        transition_length_mm,
        transition_length_mm,
        radius_mm,
    )
    assert endpoint == alignment.clothoid_entry_displacement(
        transition_length_mm,
        radius_mm,
    )
    assert alignment.clothoid_entry_displacement_at_station(
        0.0,
        0.0,
        radius_mm,
    ) == (0.0, 0.0, 0.0)

    invalid_arguments = (
        (-1.0, transition_length_mm, radius_mm),
        (transition_length_mm + 1.0, transition_length_mm, radius_mm),
        (0.0, -1.0, radius_mm),
        (0.0, transition_length_mm, 0.0),
        (math.nan, transition_length_mm, radius_mm),
        (0.0, math.inf, radius_mm),
    )
    for arguments in invalid_arguments:
        try:
            alignment.clothoid_entry_displacement_at_station(*arguments)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Expected invalid station calculation for {!r}".format(
                    arguments
                )
            )


def _validate_specification_and_contract():
    specification = api.TransitionPreviewSpecification(segment_count=4)
    request = specification.derived_request()
    assert request.stage == "preview"
    assert request.exact_validation_result_signature is None
    assert request == specification.derived_request()
    assert request != api.TransitionPreviewSpecification(
        segment_count=8
    ).derived_request()

    for invalid in (True, 0, -1, 2.5, "4"):
        _expect_state_error(
            lambda invalid=invalid: api.TransitionPreviewSpecification(
                segment_count=invalid
            ),
            "invalid-preview-specification",
        )


def _validate_scene_geometry_and_identity():
    state = _state()
    specification = api.TransitionPreviewSpecification(segment_count=4)
    cache = api.TransitionDerivedCache()
    artifact = api.regenerate_transition_preview(
        cache,
        state,
        specification,
    )
    assert artifact.stage == "preview"
    assert cache.status(state, specification.derived_request()) == "current"

    scene = artifact.payload
    assert isinstance(scene, api.TransitionPreviewScene)
    assert scene.frame_id == api.TRANSITION_PREVIEW_FRAME_ID
    assert scene.length_unit == api.TRANSITION_PREVIEW_LENGTH_UNIT
    assert len(scene.polylines) == 1

    polyline = scene.polylines[0]
    assert isinstance(polyline, api.TransitionPreviewPolyline)
    assert polyline.layer_id == api.TRANSITION_PREVIEW_CENTRELINE_LAYER_ID
    assert polyline.visual_id == (
        "transition:phase4:preview:preview:centreline"
    )
    assert polyline.domain_id == state.intent.transition_id
    assert polyline.track_name == state.intent.track_name
    assert polyline.end_name == state.intent.end_name
    assert len(polyline.points) == 5
    for point, expected in zip(
        polyline.points,
        EXPECTED_FOUR_SEGMENT_POINTS,
        strict=True,
    ):
        _assert_point(point, expected)
    assert tuple(
        point.station_mm
        for point in polyline.points
    ) == tuple(sorted(point.station_mm for point in polyline.points))

    persisted_before = api.transition_state_to_json(state)
    assert api.transition_state_to_json(state) == persisted_before
    assert "preview" not in json.loads(persisted_before)


def _validate_lifecycle_and_invalidation():
    state = _state()
    specification = api.TransitionPreviewSpecification(segment_count=4)
    request = specification.derived_request()
    cache = api.TransitionDerivedCache()

    assert cache.status(state, request) == "missing"
    first = api.regenerate_transition_preview(cache, state, specification)
    assert api.regenerate_transition_preview(
        cache,
        state,
        specification,
    ) is first

    renamed = api.replace_transition_intent(
        state,
        replace(
            state.intent,
            track_name="Renamed preview transition",
            end_name="Exit",
        ),
    )
    assert api.transition_analysis_status(renamed) == "current"
    assert cache.status(renamed, request) == "stale"
    renamed_artifact = api.regenerate_transition_preview(
        cache,
        renamed,
        specification,
    )
    assert renamed_artifact is not first
    assert renamed_artifact.payload.polylines[0].track_name == (
        "Renamed preview transition"
    )
    assert renamed_artifact.payload.polylines[0].end_name == "Exit"
    assert renamed_artifact.payload.polylines[0].points == (
        first.payload.polylines[0].points
    )

    changed = _state(transition_length_mm=260.0)
    assert cache.status(changed, request) == "stale"
    changed_artifact = api.regenerate_transition_preview(
        cache,
        changed,
        specification,
    )
    assert changed_artifact.payload.polylines[0].points != (
        first.payload.polylines[0].points
    )

    restored = _state()
    assert cache.status(restored, request) == "stale"
    restored_artifact = api.regenerate_transition_preview(
        cache,
        restored,
        specification,
    )
    assert restored_artifact.source_signature == first.source_signature
    assert restored_artifact.payload == first.payload

    denser = api.TransitionPreviewSpecification(segment_count=8)
    assert cache.status(restored, denser.derived_request()) == "stale"
    dense_artifact = api.regenerate_transition_preview(
        cache,
        restored,
        denser,
    )
    assert len(dense_artifact.payload.polylines[0].points) == 9
    assert dense_artifact.source_signature != first.source_signature

    assert cache.discard("preview") == ("preview",)
    assert cache.artifact("preview") is None
    regenerated = api.regenerate_transition_preview(
        cache,
        restored,
        specification,
    )
    assert regenerated.source_signature == first.source_signature
    assert regenerated.payload == first.payload


def _validate_zero_length_and_failures():
    state = _state(transition_length_mm=0.0)
    specification = api.TransitionPreviewSpecification(segment_count=4)
    artifact = api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        specification,
    )
    points = artifact.payload.polylines[0].points
    assert points == (api.TransitionPreviewPoint(0.0, 0.0, 0.0),)

    cold = api.TransitionState(_intent())
    _expect_state_error(
        lambda: api.regenerate_transition_preview(
            api.TransitionDerivedCache(),
            cold,
            specification,
        ),
        "analysis-required",
    )
    _expect_state_error(
        lambda: api.TransitionPreviewPoint(0.0, math.nan, 0.0),
        "invalid-preview-point",
    )


def _validate_structure_and_isolation():
    assert api.TransitionPreviewPoint is preview.TransitionPreviewPoint
    assert api.TransitionPreviewPolyline is preview.TransitionPreviewPolyline
    assert api.TransitionPreviewScene is preview.TransitionPreviewScene
    assert (
        api.TransitionPreviewSpecification
        is preview.TransitionPreviewSpecification
    )
    assert (
        api.regenerate_transition_preview
        is preview.regenerate_transition_preview
    )

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules["tracktemplate.presentation.transition_preview"]
    assert module["layer"] == "presentation"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "dataclasses",
        "math",
        "tracktemplate.application.transition_derived",
        "tracktemplate.application.transition_state",
        "tracktemplate.domain.alignment",
    ]

    script = """
import importlib.abc
import json
import math
import sys

forbidden = {{"FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"}}
attempted = []

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden host import: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {root!r})
from tracktemplate import api

centre_y = 624.7779655573173
radius = 655.0
target = api.transition_start_signed_offset(centre_y, radius, 300.0)
intent = api.TransitionIntent(
    "transition:isolated-preview",
    centre_y,
    radius,
    target,
    math.pi / 2.0,
    "Isolated preview",
    "Entry",
)
state = api.analyse_transition_state(api.TransitionState(intent))
artifact = api.regenerate_transition_preview(
    api.TransitionDerivedCache(),
    state,
    api.TransitionPreviewSpecification(4),
)
print(json.dumps({{
    "attempted": attempted,
    "point_count": len(artifact.payload.polylines[0].points),
}}))
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "attempted": [],
        "point_count": 5,
    }


def _validate_controls():
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    evidence = (
        ROOT
        / "reference"
        / "current"
        / "PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert "| 4 | Canonical state, signatures and persistence | 4/6 evidenced" in plan
    assert "## Renderer-neutral transition preview scene" in evidence
    assert "does not select or implement a renderer" in evidence


def validate():
    _validate_fixed_transition_sampling_math()
    _validate_specification_and_contract()
    _validate_scene_geometry_and_identity()
    _validate_lifecycle_and_invalidation()
    _validate_zero_length_and_failures()
    _validate_structure_and_isolation()
    _validate_controls()
    print("Phase 4 renderer-neutral transition preview-scene validation passed")


if __name__ == "__main__":
    validate()
