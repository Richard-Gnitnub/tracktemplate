#!/usr/bin/env python3
"""Validate the Phase 4 transition derived-state lifecycle contract."""

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
from tracktemplate.application import transition_derived as derived  # noqa: E402


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
    values = {
        "transition_id": "transition:phase4:derived",
        "circle_centre_y_mm": circle_centre_y_mm,
        "radius_mm": radius_mm,
        "target_signed_offset_mm": api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            300.0,
        ),
        "total_angle_rad": math.pi / 2.0,
        "track_name": "Phase 4 derived transition",
        "end_name": "Entry",
    }
    values.update(changes)
    return api.TransitionIntent(**values)


def _state(**changes):
    intent = _intent(**changes)
    return api.analyse_transition_state(api.TransitionState(intent))


def _contract_signature(stage, revision=1):
    return api.transition_derived_contract_signature(
        "test-only.transition-{}.v1".format(stage),
        {"revision": revision},
    )


def _exact_result_signature(revision=1):
    return api.transition_derived_contract_signature(
        "test-only.transition-exact-result.v1",
        {"revision": revision, "valid": True},
    )


def _request(stage, revision=1, exact_revision=1):
    exact_result_signature = None
    if stage == "export":
        exact_result_signature = _exact_result_signature(exact_revision)
    return api.TransitionDerivedRequest(
        stage=stage,
        contract_signature=_contract_signature(stage, revision),
        exact_validation_result_signature=exact_result_signature,
    )


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _validate_requests_and_signatures():
    assert api.TRANSITION_DERIVED_STAGES == (
        "preview",
        "exact-validation",
        "export",
    )
    assert _contract_signature("preview") == _contract_signature("preview")
    assert _contract_signature("preview") != _contract_signature(
        "preview",
        revision=2,
    )

    for stage in api.TRANSITION_DERIVED_STAGES:
        request = _request(stage)
        assert request.stage == stage
        assert request.contract_signature.startswith("sha256:")
        if stage == "export":
            assert request.exact_validation_result_signature is not None
        else:
            assert request.exact_validation_result_signature is None

    _expect_state_error(
        lambda: api.TransitionDerivedRequest(
            stage="unknown",
            contract_signature=_contract_signature("preview"),
        ),
        "invalid-derived-stage",
    )
    _expect_state_error(
        lambda: api.TransitionDerivedRequest(
            stage="preview",
            contract_signature="not-a-signature",
        ),
        "invalid-signature",
    )
    _expect_state_error(
        lambda: api.TransitionDerivedRequest(
            stage="preview",
            contract_signature=_contract_signature("preview"),
            exact_validation_result_signature=_exact_result_signature(),
        ),
        "invalid-derived-dependencies",
    )
    _expect_state_error(
        lambda: api.TransitionDerivedRequest(
            stage="export",
            contract_signature=_contract_signature("export"),
        ),
        "invalid-derived-dependencies",
    )
    _expect_state_error(
        lambda: api.transition_derived_contract_signature("", {}),
        "invalid-derived-contract",
    )
    _expect_state_error(
        lambda: api.transition_derived_contract_signature(
            "test-only.invalid",
            {"unsupported": object()},
        ),
        "invalid-derived-contract",
    )
    _expect_state_error(
        lambda: api.transition_derived_contract_signature(
            "test-only.invalid",
            {"nested": {1: "not-a-JSON-object-key"}},
        ),
        "invalid-derived-contract",
    )
    _expect_state_error(
        lambda: api.transition_derived_contract_signature(
            "test-only.invalid",
            {"sequence": (1, 2)},
        ),
        "invalid-derived-contract",
    )
    cyclic = []
    cyclic.append(cyclic)
    _expect_state_error(
        lambda: api.transition_derived_contract_signature(
            "test-only.invalid",
            {"cycle": cyclic},
        ),
        "invalid-derived-contract",
    )

    analysed = _state()
    cold = api.TransitionState(analysed.intent)
    for stage in api.TRANSITION_DERIVED_STAGES:
        _expect_state_error(
            lambda stage=stage: api.transition_derived_source_signature(
                cold,
                _request(stage),
            ),
            "analysis-required",
        )

    base_signatures = {
        stage: api.transition_derived_source_signature(
            analysed,
            _request(stage),
        )
        for stage in api.TRANSITION_DERIVED_STAGES
    }
    renamed = api.replace_transition_intent(
        analysed,
        replace(
            analysed.intent,
            track_name="Renamed diagnostic label",
            end_name="Exit",
        ),
    )
    assert api.transition_analysis_status(renamed) == "current"
    assert api.transition_derived_source_signature(
        renamed,
        _request("exact-validation"),
    ) == base_signatures["exact-validation"]
    for stage in ("preview", "export"):
        assert api.transition_derived_source_signature(
            renamed,
            _request(stage),
        ) != base_signatures[stage]

    changed_intent = replace(
        analysed.intent,
        target_signed_offset_mm=analysed.intent.target_signed_offset_mm + 0.1,
    )
    changed = api.analyse_transition_state(
        api.replace_transition_intent(analysed, changed_intent)
    )
    for stage in api.TRANSITION_DERIVED_STAGES:
        assert api.transition_derived_source_signature(
            changed,
            _request(stage),
        ) != base_signatures[stage]

    restored = api.analyse_transition_state(
        api.replace_transition_intent(changed, analysed.intent)
    )
    for stage in api.TRANSITION_DERIVED_STAGES:
        assert api.transition_derived_source_signature(
            restored,
            _request(stage),
        ) == base_signatures[stage]


def _payload(state, request):
    return {
        "stage": request.stage,
        "transition_id": state.intent.transition_id,
        "transition_length_mm": state.analysis.transition_length_mm,
    }


def _validate_cache_lifecycle():
    state = _state()
    cache = api.TransitionDerivedCache()
    build_count = {stage: 0 for stage in api.TRANSITION_DERIVED_STAGES}

    def build(current_state, request):
        build_count[request.stage] += 1
        return _payload(current_state, request)

    artifacts = {}
    for stage in api.TRANSITION_DERIVED_STAGES:
        request = _request(stage)
        assert cache.artifact(stage) is None
        assert cache.status(state, request) == "missing"
        artifact = cache.regenerate(state, request, build)
        artifacts[stage] = artifact
        assert artifact.stage == stage
        assert artifact.source_signature == (
            api.transition_derived_source_signature(state, request)
        )
        assert artifact.payload == _payload(state, request)
        assert cache.status(state, request) == "current"
        assert cache.regenerate(state, request, build) is artifact
        assert build_count[stage] == 1

    assert cache.discard("preview") == ("preview",)
    assert cache.artifact("preview") is None
    rebuilt = cache.regenerate(state, _request("preview"), build)
    assert rebuilt is not artifacts["preview"]
    assert rebuilt.source_signature == artifacts["preview"].source_signature
    assert rebuilt.payload == artifacts["preview"].payload
    assert build_count["preview"] == 2
    assert cache.discard("preview") == ("preview",)
    assert cache.discard("preview") == ()

    assert cache.discard() == ("exact-validation", "export")
    assert cache.discard() == ()
    assert all(
        cache.artifact(stage) is None
        for stage in api.TRANSITION_DERIVED_STAGES
    )

    for stage in api.TRANSITION_DERIVED_STAGES:
        cache.regenerate(state, _request(stage), build)

    renamed = api.replace_transition_intent(
        state,
        replace(state.intent, track_name="Renamed diagnostic label"),
    )
    assert cache.status(renamed, _request("exact-validation")) == "current"
    assert cache.status(renamed, _request("preview")) == "stale"
    assert cache.status(renamed, _request("export")) == "stale"

    changed = api.analyse_transition_state(
        api.replace_transition_intent(
            state,
            replace(
                state.intent,
                target_signed_offset_mm=state.intent.target_signed_offset_mm + 0.1,
            ),
        )
    )
    assert all(
        cache.status(changed, _request(stage)) == "stale"
        for stage in api.TRANSITION_DERIVED_STAGES
    )

    current_exact = cache.artifact("exact-validation")
    changed_request = _request("exact-validation", revision=2)

    def fail_build(_state, _request_value):
        raise RuntimeError("injected derived-artifact build failure")

    try:
        cache.regenerate(state, changed_request, fail_build)
    except RuntimeError as error:
        assert str(error) == "injected derived-artifact build failure"
    else:
        raise AssertionError("injected derived-artifact failure was hidden")
    assert cache.artifact("exact-validation") is current_exact
    assert cache.status(state, changed_request) == "stale"

    _expect_state_error(
        lambda: cache.regenerate(
            state,
            changed_request,
            lambda _state, _request_value: None,
        ),
        "invalid-derived-artifact",
    )
    assert cache.artifact("exact-validation") is current_exact

    change_back = api.analyse_transition_state(
        api.replace_transition_intent(changed, state.intent)
    )
    old_preview = cache.artifact("preview")
    changed_preview = cache.regenerate(changed, _request("preview"), build)
    assert changed_preview is not old_preview
    restored_preview = cache.regenerate(
        change_back,
        _request("preview"),
        build,
    )
    assert restored_preview is not changed_preview
    assert restored_preview.source_signature == old_preview.source_signature
    assert restored_preview.payload == old_preview.payload


def _validate_persistence_and_structure():
    state = _state()
    persisted = api.transition_state_to_json(state)
    cache = api.TransitionDerivedCache()
    for stage in api.TRANSITION_DERIVED_STAGES:
        cache.regenerate(state, _request(stage), _payload)
    assert api.transition_state_to_json(state) == persisted
    record = json.loads(persisted)
    assert set(record) == {"analysis", "intent", "schema", "schema_version"}
    assert not set(record) & {
        "derived",
        "preview",
        "exact-validation",
        "export",
    }

    assert api.TransitionDerivedArtifact is derived.TransitionDerivedArtifact
    assert api.TransitionDerivedCache is derived.TransitionDerivedCache
    assert api.TransitionDerivedRequest is derived.TransitionDerivedRequest

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules["tracktemplate.application.transition_derived"]
    assert module["layer"] == "application"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "dataclasses",
        "hashlib",
        "json",
        "math",
        "tracktemplate.application.transition_state",
    ]
    assert {
        "from": "tracktemplate.application.transition_derived",
        "to": "tracktemplate.application.transition_state",
    } in report["import_edges"]

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
print(json.dumps({{
    "attempted": attempted,
    "stages": api.TRANSITION_DERIVED_STAGES,
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
        "stages": ["preview", "exact-validation", "export"],
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
    assert "bounded product implementation resumed" in plan
    assert "| 4 | Canonical state, signatures and persistence | 4/6 evidenced" in plan
    assert "## Bounded Phase 4 resumption" in evidence
    assert "## Derived-state lifecycle contract" in evidence
    assert "do not claim either remaining exit condition" in evidence


def validate():
    _validate_requests_and_signatures()
    _validate_cache_lifecycle()
    _validate_persistence_and_structure()
    _validate_controls()
    print("Phase 4 transition derived-state lifecycle validation passed")


if __name__ == "__main__":
    validate()
