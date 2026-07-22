#!/usr/bin/env python3
"""Validate the non-authorising Phase 4 plain-line transition assessment."""

import ast
import copy
import hashlib
import json
import math
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate.application import transition_state  # noqa: E402
from tracktemplate.compatibility import legacy_document  # noqa: E402
from tracktemplate.compatibility import plain_line_transition  # noqa: E402


CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
MODULE_PATH = ROOT / "tracktemplate" / "compatibility" / "plain_line_transition.py"
FREECAD_TEST_PATH = (
    ROOT / "tests" / "freecad_validate_phase4_plain_line_transition_assessment.py"
)
GENERATOR_ID = "ModelRailwayCurveTemplate.IndependentEasements"
B14 = "10.2A8A7B14"
B15 = "10.2A8A7B15"
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
PROPERTY_TYPES = {
    "GeneratedBy": "App::PropertyString",
    "GeneratedRole": "App::PropertyString",
    "TemplateSetID": "App::PropertyString",
    "GeneratorVersion": "App::PropertyString",
    "TransitionLength": "App::PropertyLength",
    "CurveRadius": "App::PropertyLength",
    "TotalTurnAngle": "App::PropertyAngle",
    "ParallelTrackCount": "App::PropertyInteger",
    "TrackConfigurationJSON": "App::PropertyString",
}


class FakeObject:
    def __init__(self, name, properties, property_types=None):
        self.Name = name
        self.PropertiesList = list(properties)
        self._property_types = dict(property_types or {})
        for property_name, value in properties.items():
            setattr(self, property_name, value)

    def getTypeIdOfProperty(self, property_name):
        return self._property_types.get(property_name, "")


class FakeDocument:
    def __init__(self, objects):
        self.Objects = list(objects)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _track(
    name="Track 2",
    mode=plain_line_transition.SUPPORTED_ALIGNMENT_MODE,
    side="Outside",
    start_spacing=50.0,
    curve_spacing=55.0,
    finish_spacing=50.0,
    entry_length=559.4102547270278,
    exit_length=559.4102547270278,
):
    return {
        "alignment_mode": mode,
        "create_template": True,
        "curve_spacing": curve_spacing,
        "entry_transition_length": entry_length,
        "exit_transition_length": exit_length,
        "finish_spacing": finish_spacing,
        "name": name,
        "show_centreline": True,
        "side": side,
        "start_spacing": start_spacing,
        "width": 32.0,
    }


def _settings(
    name="RailwayCurveSettings",
    version=B14,
    set_id="SET-001",
    tracks=None,
    angle=90.0,
):
    tracks = [_track()] if tracks is None else tracks
    properties = {
        "GeneratedBy": GENERATOR_ID,
        "GeneratedRole": "Settings",
        "TemplateSetID": set_id,
        "GeneratorVersion": version + " descriptive suffix",
        "TransitionLength": 600.0,
        "CurveRadius": 600.0,
        "TotalTurnAngle": angle,
        "ParallelTrackCount": len(tracks),
        "TrackConfigurationJSON": json.dumps(tracks, sort_keys=True),
    }
    return FakeObject(name, properties, PROPERTY_TYPES)


def _owned(name, version, role="ChairAnalysisDisplay", set_id="SET-001"):
    properties = {
        "GeneratedBy": GENERATOR_ID,
        "GeneratedRole": role,
        "TemplateSetID": set_id,
        "GeneratorVersion": version,
    }
    property_types = {key: "App::PropertyString" for key in properties}
    return FakeObject(name, properties, property_types)


def _foreign(name="OperatorObject"):
    return FakeObject(
        name,
        {
            "GeneratedBy": "Some.Other.Tool",
            "GeneratorVersion": "99.0 FUTURE",
            "OperatorData": "untouched",
        },
        {
            "GeneratedBy": "App::PropertyString",
            "GeneratorVersion": "App::PropertyString",
            "OperatorData": "App::PropertyString",
        },
    )


def _snapshot(document):
    return tuple(
        (
            obj.Name,
            tuple(obj.PropertiesList),
            copy.deepcopy(obj._property_types),
            tuple(
                (name, copy.deepcopy(getattr(obj, name)))
                for name in obj.PropertiesList
            ),
        )
        for obj in document.Objects
    )


def _codes(report):
    return {item.code for item in report.findings}


def _candidate_summary(report):
    return tuple(
        (
            item.template_set_id,
            item.track_number,
            item.end_name,
            item.state.intent.transition_id,
            item.state.intent.track_name,
            item.state.analysis.transition_length_mm,
        )
        for item in report.candidates
    )


def _validate_exact_b14_candidate():
    document = FakeDocument([_foreign(), _settings()])
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
    assert report.outer_inspection.version_window_status == "accepted"
    assert report.outer_inspection.observed_versions == (B14,)
    assert report.outer_inspection.write_authorized is False
    assert _candidate_summary(report) == (
        (
            "SET-001",
            2,
            "Entry",
            "SET-001/curve-track/2/transition/entry",
            "Track 2",
            559.4102547270278,
        ),
        (
            "SET-001",
            2,
            "Exit",
            "SET-001/curve-track/2/transition/exit",
            "Track 2",
            559.4102547270278,
        ),
    )
    for candidate in report.candidates:
        intent = candidate.state.intent
        assert intent.circle_centre_y_mm == 624.7779655573173
        assert intent.radius_mm == 655.0
        assert intent.target_signed_offset_mm == -50.0
        assert intent.total_angle_rad == math.pi / 2.0
        assert transition_state.transition_analysis_status(candidate.state) == "current"
        encoded_state = transition_state.transition_state_to_json(candidate.state)
        assert transition_state.transition_state_from_json(encoded_state) == candidate.state

    record = report.to_record()
    assert set(record) == {
        "canonical_inputs_sufficient",
        "candidates",
        "family_id",
        "findings",
        "migration_authorized",
        "outer_inspection",
        "production_output_authorized",
        "schema_id",
        "schema_version",
        "status",
        "write_authorized",
    }
    encoded = plain_line_transition.plain_line_transition_assessment_to_json(report)
    assert json.loads(encoded) == record
    reordered = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([_settings(), _foreign()]),
        _contract(),
    )
    assert encoded == plain_line_transition.plain_line_transition_assessment_to_json(
        reordered
    )


def _validate_window_identity_and_direction():
    right = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([_settings(angle=-90.0)]),
        _contract(),
    )
    assert right.status == plain_line_transition.STATUS_CANONICAL_INPUTS_SUFFICIENT
    assert all(
        item.state.intent.total_angle_rad == math.pi / 2.0
        for item in right.candidates
    )

    renamed = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([_settings(tracks=[_track(name="Operator label changed")])]),
        _contract(),
    )
    baseline = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([_settings()]),
        _contract(),
    )
    assert tuple(item.state.intent.transition_id for item in renamed.candidates) == tuple(
        item.state.intent.transition_id for item in baseline.candidates
    )
    assert tuple(
        item.state.analysis.analysis_signature for item in renamed.candidates
    ) == tuple(item.state.analysis.analysis_signature for item in baseline.candidates)

    mixed_document = FakeDocument(
        [
            _owned("B15Chair", B15),
            _settings("SettingsTwo", B15, "SET-002"),
            _settings("SettingsOne", B14, "SET-001"),
        ]
    )
    mixed = plain_line_transition.assess_plain_line_transitions(
        mixed_document,
        _contract(),
    )
    assert mixed.status == plain_line_transition.STATUS_CANONICAL_INPUTS_SUFFICIENT
    assert mixed.outer_inspection.observed_versions == (B14, B15)
    assert tuple(item.template_set_id for item in mixed.candidates) == (
        "SET-001",
        "SET-001",
        "SET-002",
        "SET-002",
    )


def _validate_inspection_only_cases():
    cases = []
    cases.append(
        (
            FakeDocument([_owned("ChairOnly", B15)]),
            "no-plain-line-settings-object",
        )
    )
    cases.append((FakeDocument([_settings(tracks=[])]), "no-secondary-transition-family"))
    cases.append(
        (
            FakeDocument(
                [
                    _settings(
                        tracks=[
                            _track(
                                mode="Euler - use easement lengths",
                            )
                        ]
                    )
                ]
            ),
            "unsupported-alignment-mode",
        )
    )
    cases.append(
        (
            FakeDocument([_settings(set_id="operator-label")]),
            "unsupported-template-set-identity",
        )
    )
    missing = _settings()
    missing.PropertiesList.remove("CurveRadius")
    del missing.CurveRadius
    missing._property_types.pop("CurveRadius")
    cases.append((FakeDocument([missing]), "missing-required-property"))

    missing_field_track = _track()
    missing_field_track.pop("width")
    cases.append(
        (
            FakeDocument([_settings(tracks=[missing_field_track])]),
            "unrecognised-track-configuration-fields",
        )
    )
    for document, expected_code in cases:
        before = _snapshot(document)
        report = plain_line_transition.assess_plain_line_transitions(
            document,
            _contract(),
        )
        assert _snapshot(document) == before
        assert report.status == plain_line_transition.STATUS_INSPECTION_ONLY
        assert report.candidates == ()
        assert expected_code in _codes(report)
        assert report.write_authorized is False

    future = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([_settings(version="10.2A8A7B99")]),
        _contract(),
    )
    assert future.status == plain_line_transition.STATUS_INSPECTION_ONLY
    assert _codes(future) == {"outer-version-window-not-accepted"}


def _validate_blocked_cases():
    wrong_type = _settings()
    wrong_type._property_types["CurveRadius"] = "App::PropertyString"

    bad_number_track = _track()
    bad_number_track["start_spacing"] = True

    mismatched_result = _track(entry_length=559.0)

    bad_count = _settings()
    bad_count.ParallelTrackCount = 2

    impossible_main = _settings()
    impossible_main.TotalTurnAngle = 1.0

    unexpected_track = _track()
    unexpected_track["future_field"] = 1

    duplicate_set = FakeDocument(
        [
            _settings("SettingsA", B14, "SET-001"),
            _settings("SettingsB", B14, "SET-001"),
        ]
    )
    incomplete_duplicate = _settings("SettingsIncomplete", B14, "SET-002")
    incomplete_duplicate.PropertiesList.remove("CurveRadius")
    del incomplete_duplicate.CurveRadius
    incomplete_duplicate._property_types.pop("CurveRadius")
    duplicate_with_incomplete = FakeDocument(
        [
            incomplete_duplicate,
            _settings("SettingsComplete", B14, "SET-002"),
        ]
    )
    cases = (
        (FakeDocument([wrong_type]), "invalid-property-type"),
        (FakeDocument([_settings(tracks=[bad_number_track])]), "invalid-number"),
        (
            FakeDocument([_settings(tracks=[mismatched_result])]),
            "stored-transition-result-mismatch",
        ),
        (FakeDocument([bad_count]), "parallel-track-count-mismatch"),
        (FakeDocument([impossible_main]), "invalid-main-alignment-input"),
        (
            FakeDocument([_settings(tracks=[unexpected_track])]),
            "unrecognised-track-configuration-fields",
        ),
        (duplicate_set, "ambiguous-template-set-settings"),
        (duplicate_with_incomplete, "ambiguous-template-set-settings"),
    )
    for document, expected_code in cases:
        before = _snapshot(document)
        report = plain_line_transition.assess_plain_line_transitions(
            document,
            _contract(),
        )
        assert _snapshot(document) == before
        assert report.status == plain_line_transition.STATUS_BLOCKED
        assert expected_code in _codes(report)
        assert report.write_authorized is False
        assert report.migration_authorized is False

    malformed = _settings()
    malformed.TrackConfigurationJSON = "{not-json"
    outer_blocked = plain_line_transition.assess_plain_line_transitions(
        FakeDocument([malformed]),
        _contract(),
    )
    assert outer_blocked.status == plain_line_transition.STATUS_BLOCKED
    assert _codes(outer_blocked) == {"outer-ingress-blocked"}
    assert "malformed-json-payload" in {
        item.code for item in outer_blocked.outer_inspection.findings
    }


def _validate_structure_and_controls():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
    assert imported_roots == {"dataclasses", "json", "math", "re", "tracktemplate"}
    for forbidden in (
        "import FreeCAD",
        "import Part",
        "openTransaction(",
        "commitTransaction(",
        "abortTransaction(",
        "addObject(",
        "addProperty(",
        "setattr(",
        "recompute(",
        "saveAs(",
        "removeObject(",
    ):
        assert forbidden not in source
    assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    family = modules["tracktemplate.compatibility.plain_line_transition"]
    assert family["layer"] == "compatibility"
    assert family["warning_signals"] == []
    assert "tracktemplate.compatibility" in family["imports"]
    assert "tracktemplate.application.transition_state" in family["imports"]
    assert "tracktemplate.domain.transition" in family["imports"]
    assert not any(
        item.startswith("tracktemplate.compatibility.plain_line_transition")
        for item in modules["tracktemplate.api"]["imports"]
    )

    script = """
import importlib.abc
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
from tracktemplate.compatibility import legacy_document, plain_line_transition
assert attempted == []
assert legacy_document.SUPPORTED_MIGRATION_FAMILIES == ()
assert plain_line_transition.FAMILY_ID == "plain-line-spacing-matched-transition-intent"
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    for relative, expected_hash in SOURCE_HASHES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash
    assert FREECAD_TEST_PATH.exists()
    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(encoding="utf-8")
    assert "Bounded read-window acceptance" in evidence
    assert "plain-line transition family assessment" in evidence.lower()
    assert FREECAD_TEST_PATH.name in validation


def validate():
    _validate_exact_b14_candidate()
    _validate_window_identity_and_direction()
    _validate_inspection_only_cases()
    _validate_blocked_cases()
    _validate_structure_and_controls()
    print("Phase 4 plain-line transition assessment validation passed")


if __name__ == "__main__":
    validate()
