#!/usr/bin/env python3
"""Validate the Phase 4 transition canonical-state foundation."""

import copy
from dataclasses import FrozenInstanceError, replace
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
from tracktemplate.application import transition_state as canonical  # noqa: E402
from tracktemplate.domain.transition import TransitionIntent  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _intent(**changes):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    target_signed_offset_mm = api.transition_start_signed_offset(
        circle_centre_y_mm,
        radius_mm,
        300.0,
    )
    values = {
        "transition_id": "transition:plain-line:right:entry",
        "circle_centre_y_mm": circle_centre_y_mm,
        "radius_mm": radius_mm,
        "target_signed_offset_mm": target_signed_offset_mm,
        "total_angle_rad": math.pi / 2.0,
        "track_name": "Right-hand plain line",
        "end_name": "Entry",
    }
    values.update(changes)
    return api.TransitionIntent(**values)


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        diagnostic = error.diagnostic()
        assert diagnostic == {
            "code": error.code,
            "path": error.path,
            "message": error.detail,
            "recoverable": True,
            "document_mutation": False,
        }
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _validate_records_and_round_trip():
    intent = _intent()
    assert isinstance(intent, TransitionIntent)
    assert all(
        type(getattr(intent, field)) is float
        for field in (
            "circle_centre_y_mm",
            "radius_mm",
            "target_signed_offset_mm",
            "total_angle_rad",
        )
    )
    try:
        intent.radius_mm = 900.0
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("TransitionIntent is not immutable")

    cold = api.TransitionState(intent=intent)
    assert api.transition_analysis_status(cold) == "missing"
    cold_json = api.transition_state_to_json(cold)
    assert cold_json == api.transition_state_to_json(cold)
    cold_record = json.loads(cold_json)
    assert list(cold_record) == ["analysis", "intent", "schema", "schema_version"]
    assert cold_record["schema"] == canonical.TRANSITION_STATE_SCHEMA_ID
    assert cold_record["schema_version"] == 1
    assert cold_record["analysis"] is None
    assert cold_record["intent"]["coordinate_frame"] == (
        "canonical-local-left-turn-v1"
    )
    assert cold_record["intent"]["length_unit"] == "mm"
    assert cold_record["intent"]["angle_unit"] == "rad"
    assert cold_record["intent"]["algorithm_id"] == (
        canonical.TRANSITION_ALGORITHM_ID
    )
    assert cold_record["intent"]["tolerance_profile_id"] == (
        canonical.TRANSITION_TOLERANCE_PROFILE_ID
    )
    assert api.transition_state_from_json(cold_json) == cold

    analysed = api.analyse_transition_state(cold)
    assert cold.analysis is None
    assert api.transition_analysis_status(analysed) == "current"
    expected = api.solve_transition_length(
        intent.circle_centre_y_mm,
        intent.radius_mm,
        intent.target_signed_offset_mm,
        intent.total_angle_rad,
        intent.track_name,
        intent.end_name,
    )
    assert analysed.analysis.transition_length_mm == expected
    assert api.analyse_transition_state(analysed) is analysed

    persisted = api.transition_state_to_json(analysed)
    reopened = api.transition_state_from_json(persisted)
    assert reopened == analysed
    assert api.transition_state_to_json(reopened) == persisted
    keys = set(json.loads(persisted)["intent"])
    assert not keys & {"shape", "mesh", "preview", "part", "geometry"}
    return analysed


def _validate_signatures_and_invalidation(analysed):
    base_intent = analysed.intent
    base_signature = analysed.analysis.analysis_signature
    assert base_signature == api.transition_analysis_signature(base_intent)

    label_changes = (
        replace(base_intent, track_name="Renamed plain line"),
        replace(base_intent, end_name="Exit label used for diagnostics"),
    )
    for changed_intent in label_changes:
        changed = api.replace_transition_intent(analysed, changed_intent)
        assert changed.analysis is analysed.analysis
        assert api.transition_analysis_status(changed) == "current"
        assert api.transition_analysis_signature(changed_intent) == base_signature

    numerical_changes = (
        replace(base_intent, circle_centre_y_mm=base_intent.circle_centre_y_mm + 1.0),
        replace(base_intent, radius_mm=base_intent.radius_mm + 1.0),
        replace(
            base_intent,
            target_signed_offset_mm=base_intent.target_signed_offset_mm + 0.1,
        ),
        replace(base_intent, total_angle_rad=base_intent.total_angle_rad + 0.01),
    )
    for changed_intent in numerical_changes:
        assert api.transition_analysis_signature(changed_intent) != base_signature
        changed = api.replace_transition_intent(analysed, changed_intent)
        assert changed.analysis is None
        assert changed.findings == ("analysis-invalidated",)
        assert api.transition_analysis_status(changed) == "missing"

    changed_intent = replace(
        base_intent,
        target_signed_offset_mm=base_intent.target_signed_offset_mm + 0.1,
    )
    changed = api.analyse_transition_state(
        api.replace_transition_intent(analysed, changed_intent)
    )
    assert changed.analysis.analysis_signature != base_signature
    change_back = api.replace_transition_intent(changed, base_intent)
    assert api.transition_analysis_status(change_back) == "missing"
    restored = api.analyse_transition_state(change_back)
    assert restored.analysis == analysed.analysis

    _expect_state_error(
        lambda: api.replace_transition_intent(
            analysed,
            replace(base_intent, transition_id="transition:different"),
        ),
        "stable-identity-change",
    )

    positive_zero = replace(base_intent, circle_centre_y_mm=0.0)
    negative_zero = replace(base_intent, circle_centre_y_mm=-0.0)
    assert api.transition_analysis_signature(positive_zero) != (
        api.transition_analysis_signature(negative_zero)
    )


def _validate_recoverable_derived_state(analysed):
    record = json.loads(api.transition_state_to_json(analysed))

    stale_record = copy.deepcopy(record)
    stale_record["intent"]["radius_mm"] += 1.0
    stale = api.transition_state_from_json(json.dumps(stale_record))
    assert stale.analysis is None
    assert stale.findings == ("stale-analysis-discarded",)
    assert json.loads(api.transition_state_to_json(stale))["analysis"] is None

    corrupt_record = copy.deepcopy(record)
    corrupt_record["analysis"]["transition_length_mm"] += 1.0
    corrupt = api.transition_state_from_json(json.dumps(corrupt_record))
    assert corrupt.analysis is None
    assert corrupt.findings == ("corrupt-analysis-discarded",)

    incomplete_record = copy.deepcopy(record)
    del incomplete_record["analysis"]["result_signature"]
    incomplete = api.transition_state_from_json(json.dumps(incomplete_record))
    assert incomplete.analysis is None
    assert incomplete.findings == ("corrupt-analysis-discarded",)

    stale_analysis = replace(
        analysed.analysis,
        analysis_signature="sha256:" + ("0" * 64),
    )
    direct_stale = api.TransitionState(
        intent=analysed.intent,
        analysis=stale_analysis,
    )
    assert api.transition_analysis_status(direct_stale) == "stale-or-corrupt"
    _expect_state_error(
        lambda: api.transition_state_to_json(direct_stale),
        "stale-derived-result",
    )


def _validate_fail_closed_inputs(analysed):
    encoded = api.transition_state_to_json(analysed)
    record = json.loads(encoded)

    for version in (0, 2, 999):
        changed = copy.deepcopy(record)
        changed["schema_version"] = version
        _expect_state_error(
            lambda changed=changed: api.transition_state_from_json(
                json.dumps(changed)
            ),
            "unsupported-schema-version",
        )

    changed = copy.deepcopy(record)
    changed["schema_version"] = True
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "invalid-schema-version",
    )

    changed = copy.deepcopy(record)
    changed["schema"] = "tracktemplate.unknown-state"
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "unsupported-schema",
    )

    for field, invalid in (
        ("algorithm_id", "tracktemplate.transition-length.unknown"),
        ("angle_unit", "degree"),
        ("coordinate_frame", "global-xy"),
        ("length_unit", "inch"),
        ("tolerance_profile_id", "unknown-tolerances"),
    ):
        changed = copy.deepcopy(record)
        changed["intent"][field] = invalid
        _expect_state_error(
            lambda changed=changed: api.transition_state_from_json(
                json.dumps(changed)
            ),
            "unsupported-calculation-contract",
        )

    changed = copy.deepcopy(record)
    changed["intent"]["unexpected"] = 1
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "invalid-fields",
    )

    changed = copy.deepcopy(record)
    del changed["intent"]["radius_mm"]
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "invalid-fields",
    )

    changed = copy.deepcopy(record)
    changed["intent"]["transition_id"] = ""
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "invalid-canonical-intent",
    )

    changed = copy.deepcopy(record)
    changed["intent"]["radius_mm"] = True
    _expect_state_error(
        lambda: api.transition_state_from_json(json.dumps(changed)),
        "invalid-canonical-intent",
    )

    duplicate = encoded[:-1] + ',"schema_version":1}'
    _expect_state_error(
        lambda: api.transition_state_from_json(duplicate),
        "duplicate-field",
    )
    _expect_state_error(
        lambda: api.transition_state_from_json("{not-json}"),
        "invalid-json",
    )
    _expect_state_error(
        lambda: api.transition_state_from_json(encoded.replace("655.0", "NaN", 1)),
        "invalid-number",
    )

    for field, value in (
        ("radius_mm", True),
        ("radius_mm", float("nan")),
        ("radius_mm", float("inf")),
        ("transition_id", ""),
        ("track_name", 7),
    ):
        try:
            _intent(**{field: value})
        except ValueError:
            pass
        else:
            raise AssertionError("invalid intent field {!r} was accepted".format(field))

    invalid = api.TransitionState(intent=_intent(radius_mm=0.0))
    try:
        api.analyse_transition_state(invalid)
    except ValueError as error:
        assert "must be greater than zero" in str(error)
    else:
        raise AssertionError("accepted solver error was not preserved")
    assert invalid.analysis is None and invalid.findings == ()


def _validate_public_and_structural_boundaries():
    assert api.TransitionIntent is TransitionIntent
    assert api.TransitionState is canonical.TransitionState
    assert api.TRANSITION_STATE_SCHEMA_VERSION == 1
    assert canonical.TRANSITION_STATE_READ_VERSIONS == (1,)

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    assert modules["tracktemplate.application"]["layer"] == "application"
    application = modules["tracktemplate.application.transition_state"]
    assert application["layer"] == "application"
    assert application["warning_signals"] == []
    assert {
        "tracktemplate.domain.alignment",
        "tracktemplate.domain.transition",
    } <= set(application["imports"])
    assert modules["tracktemplate.domain.transition"]["layer"] == "domain"

    script = """
import importlib.abc
import json
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
intent = api.TransitionIntent("transition:test", 10, 100, -90, 0.5, "Track", "Entry")
state = api.TransitionState(intent)
text = api.transition_state_to_json(state)
print(json.dumps({{"attempted": attempted, "round_trip": api.transition_state_from_json(text) == state}}))
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"attempted": [], "round_trip": True}


def _validate_source_and_phase_controls():
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    assert "Phase 4 is current" in plan
    assert "0/6" in plan
    assert "Provisional transition schema v1" in evidence
    assert "No Phase 4 exit condition is claimed complete" in evidence


def validate():
    analysed = _validate_records_and_round_trip()
    _validate_signatures_and_invalidation(analysed)
    _validate_recoverable_derived_state(analysed)
    _validate_fail_closed_inputs(analysed)
    _validate_public_and_structural_boundaries()
    _validate_source_and_phase_controls()
    print("Phase 4 transition canonical-state validation passed")


if __name__ == "__main__":
    validate()
