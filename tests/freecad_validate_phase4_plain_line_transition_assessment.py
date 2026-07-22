#!/usr/bin/env python3
"""Assess the reproduced B14 plain-line fixture without changing its FCStd."""

import hashlib
import json
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import plain_line_transition  # noqa: E402


FIXTURE_PATH = (
    ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "fixtures"
    / "b14-default-base-regenerated.FCStd"
)
FIXTURE_SHA256 = "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
CAPTURE_PROPERTIES = (
    "GeneratedBy",
    "GeneratedRole",
    "TemplateSetID",
    "GeneratorVersion",
    "TransitionLength",
    "CurveRadius",
    "TotalTurnAngle",
    "ParallelTrackCount",
    "TrackConfigurationJSON",
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _property_value(obj, property_name):
    value = getattr(obj, property_name)
    if hasattr(value, "Value"):
        return float(value.Value)
    return str(value) if isinstance(value, str) else value


def _snapshot(document):
    objects = []
    for obj in sorted(document.Objects, key=lambda item: str(item.Name)):
        properties = tuple(obj.PropertiesList)
        values = tuple(
            (
                name,
                str(obj.getTypeIdOfProperty(name)),
                _property_value(obj, name),
            )
            for name in CAPTURE_PROPERTIES
            if name in properties
        )
        objects.append(
            (
                str(obj.Name),
                str(obj.Label),
                str(obj.TypeId),
                properties,
                values,
            )
        )
    return (
        int(document.UndoCount),
        int(document.RedoCount),
        tuple(objects),
    )


if not FIXTURE_PATH.is_file():
    raise AssertionError(
        "Reproduce the ignored B14 fixture with tools/freecad_bridge/build-b14-base"
    )
assert _sha256(FIXTURE_PATH) == FIXTURE_SHA256

document = App.openDocument(str(FIXTURE_PATH))
try:
    before = _snapshot(document)
    report = plain_line_transition.assess_plain_line_transitions(
        document,
        _contract(),
    )
    assert _snapshot(document) == before
    assert report.status == plain_line_transition.STATUS_CANONICAL_INPUTS_SUFFICIENT
    assert report.canonical_inputs_sufficient is True
    assert report.write_authorized is False
    assert report.migration_authorized is False
    assert report.production_output_authorized is False
    assert report.findings == ()
    assert report.outer_inspection.observed_versions == ("10.2A8A7B14",)
    assert len(report.candidates) == 2
    assert tuple(
        (
            item.state.intent.transition_id,
            item.state.intent.circle_centre_y_mm,
            item.state.intent.radius_mm,
            item.state.intent.target_signed_offset_mm,
            item.state.intent.total_angle_rad,
            item.state.analysis.transition_length_mm,
        )
        for item in report.candidates
    ) == (
        (
            "SET-001/curve-track/2/transition/entry",
            624.7779655573173,
            655.0,
            -50.0,
            1.5707963267948966,
            559.4102547270278,
        ),
        (
            "SET-001/curve-track/2/transition/exit",
            624.7779655573173,
            655.0,
            -50.0,
            1.5707963267948966,
            559.4102547270278,
        ),
    )
finally:
    App.closeDocument(document.Name)

assert _sha256(FIXTURE_PATH) == FIXTURE_SHA256

print("Phase 4 plain-line transition FreeCAD assessment passed")
