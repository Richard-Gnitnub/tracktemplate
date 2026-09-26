#!/usr/bin/env python3
"""Prove complete platform-core extraction and atomic B16 routing."""

import ast
import inspect
import math
import pathlib
import subprocess
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain import alignment  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402
import validate_phase7_platform_transitions as transition_proof  # noqa: E402


SENTINEL = "Phase 7 platform core calculation and routing validation passed"
PARAMETERS = (
    "circle_centre",
    "radius",
    "entry_transition",
    "exit_transition",
    "entry_shape_parameter",
    "exit_shape_parameter",
    "total_angle",
    "label",
)
RESULT_KEYS = (
    "label",
    "points",
    "headings",
    "start",
    "end",
    "radius",
    "entry_transition",
    "exit_transition",
    "entry_angle",
    "exit_angle",
    "circular_angle",
    "circular_length",
    "core_length",
    "entry_shape_parameter",
    "exit_shape_parameter",
    "minimum_radius",
)


def _legacy_namespaces():
    records = []
    definitions = []
    for path in (transition_proof.B14, transition_proof.B15):
        namespace, nodes = transition_proof.legacy_namespace(path)
        records.append(namespace)
        definitions.append(
            ast.dump(nodes["build_platform_core"], include_attributes=False)
        )
    assert definitions[0] == definitions[1]
    return records


def _cases(namespace):
    centre = namespace["main_circle_centre"](600.0, 600.0)
    angle = namespace["platform_transition_angle"]
    exact_transition_angle = (
        angle(600.0, 655.0, 0.0)
        + angle(500.0, 655.0, 0.5)
    )
    return (
        (centre, 655.0, 600.0, 500.0, 0.0, 0.5,
         math.pi / 2.0, "Asymmetric"),
        ((0.0, 655.0), 655.0, 0.0, 0.0, 0.0, 0.0,
         math.pi / 2.0, "Circular only"),
        ((0.0, 655.0), 655.0, 1.0e-8, 1.0e-8, 0.0, 0.0,
         math.pi / 2.0, "Tolerance boundary"),
        ((0.0, 655.0), 655.0,
         math.nextafter(1.0e-8, math.inf),
         math.nextafter(1.0e-8, math.inf),
         -0.187499, 2.0, math.pi / 2.0, "Above tolerance"),
        ((31.0, 624.0), 655.0, 600.0, 500.0, 0.0, 0.5,
         exact_transition_angle, "No circular section"),
        ((31.0, 624.0), 655.0, 600.0, 500.0, 0.0, 0.5,
         exact_transition_angle - 5.0e-9, "Clamped circular section"),
        ((10031.0, -376.0), 655.0, 600.0, 500.0, 0.0, 0.5,
         math.pi / 2.0, "Translated"),
    )


def _invalid_cases(namespace):
    centre = namespace["main_circle_centre"](600.0, 600.0)
    return (
        (centre, 0.0, -1.0, -1.0, 0.0, 0.0, -1.0, "Radius first"),
        (centre, 655.0, -1.0, 0.0, 0.0, 0.0,
         math.pi / 2.0, "Negative entry"),
        (centre, 655.0, 0.0, -1.0, 0.0, 0.0,
         math.pi / 2.0, "Negative exit"),
        (centre, 655.0, 600.0, 600.0, 2.0, 2.0, 0.1,
         "Excess angle"),
    )


def _neutral_result(result):
    value = dict(result)
    value["points"] = [
        (float(point.x), float(point.y))
        if hasattr(point, "x")
        else (float(point[0]), float(point[1]))
        for point in value["points"]
    ]
    return value


def _failure(function, arguments):
    try:
        function(*arguments)
    except Exception as error:  # noqa: BLE001 - exact inherited failure proof
        return type(error).__name__, str(error)
    raise AssertionError("An invalid platform-core case was accepted")


def _validate_host_independence():
    script = """
import importlib.abc
import sys

blocked = {{
    "FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6",
    "PyQt5", "PyQt6", "pivy", "qtpy",
}}
attempted = []

class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in blocked:
            attempted.append(fullname)
            raise ModuleNotFoundError(fullname)
        return None

sys.meta_path.insert(0, Blocker())
sys.path.insert(0, {root!r})
from tracktemplate import api
from tracktemplate.domain import alignment

assert api.build_platform_core is alignment.build_platform_core
assert "build_platform_core" in api.__all__
assert "build_platform_core" in alignment.__all__
assert not attempted, attempted
""".format(root=str(ROOT))
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def validate_calculation():
    legacy = _legacy_namespaces()
    assert api.build_platform_core is alignment.build_platform_core
    assert tuple(inspect.signature(api.build_platform_core).parameters) == (
        PARAMETERS
    )
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in inspect.signature(
            api.build_platform_core
        ).parameters.values()
    )
    assert not {
        "FreeCAD", "FreeCADGui", "Part", "PySide", "pivy",
    } & set(api.build_platform_core.__code__.co_names)
    for name in (
        "platform_transition_displacement",
        "platform_peak_curvature_factor",
        "_left_normal",
        "_integrate_core_segment",
        "_rotate_xy",
    ):
        assert api.build_platform_core.__globals__[name] is getattr(
            alignment, name,
        )

    cases = _cases(legacy[0])
    for case in cases:
        expected = _neutral_result(legacy[0]["build_platform_core"](*case))
        assert expected == _neutral_result(
            legacy[1]["build_platform_core"](*case)
        )
        result = api.build_platform_core(*case)
        assert tuple(result) == RESULT_KEYS
        assert result == expected
        assert all(
            type(point) is tuple
            and len(point) == 2
            and all(type(value) is float for value in point)
            for point in result["points"]
        )
        assert len(result["points"]) == len(result["headings"])
        assert result["points"][0] == result["start"]
        assert result["points"][-1] == result["end"]
        assert result["headings"][-1] == case[6]
        assert result["core_length"] == (
            case[2] + result["circular_length"] + case[3]
        )
        assert result["minimum_radius"] == case[1] / max(
            1.0,
            alignment.platform_peak_curvature_factor(case[4]),
            alignment.platform_peak_curvature_factor(case[5]),
        )
        repeated = api.build_platform_core(*case)
        assert repeated == result
        assert repeated is not result
        assert repeated["points"] is not result["points"]
        assert repeated["headings"] is not result["headings"]

    for case in _invalid_cases(legacy[0]):
        expected = _failure(legacy[0]["build_platform_core"], case)
        assert expected == _failure(legacy[1]["build_platform_core"], case)
        assert _failure(api.build_platform_core, case) == expected

    original = api.build_platform_core(*cases[0])
    translated_case = ((cases[0][0][0] + 125.0, cases[0][0][1] - 80.0),
                       *cases[0][1:])
    translated = api.build_platform_core(*translated_case)
    assert translated["headings"] == original["headings"]
    for first, second in zip(original["points"], translated["points"]):
        assert abs(second[0] - first[0] - 125.0) <= 1.0e-9
        assert abs(second[1] - first[1] + 80.0) <= 1.0e-9

    _validate_host_independence()


def validate_complete_characterisation():
    legacy = _legacy_namespaces()
    baseline = transition_proof.characterise(legacy[0])
    assert transition_proof.characterise(legacy[1]) == baseline
    candidate, _nodes = transition_proof.legacy_namespace(
        transition_proof.B15,
    )
    candidate.update({
        name: getattr(api, name) for name in transition_proof.PUBLIC
    })
    candidate["build_platform_core"] = (
        transition_workflow._PlatformCoreAdapter(
            api.build_platform_core,
            transition_proof.Vector,
        )
    )
    assert transition_proof.characterise(candidate) == baseline


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def _expect_error(action, text):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        assert text in str(error)
        return
    raise AssertionError("An invalid platform-core route was accepted")


def validate_binding():
    with tempfile.TemporaryDirectory(prefix="tracktemplate-platform-core-") as path:
        temporary_root = pathlib.Path(path)
        contract = core_proof._fixture(temporary_root)

        def load_host():
            return b15_workflow_host.load_b15_workflow_host(
                temporary_root,
                contract,
            )

        host = load_host()
        session = transition_workflow.ModularTransitionWorkflowSession(
            host,
            _functions(),
        )
        record = session.routing_record()
        assert record["schema_version"] == 12
        assert record["contract_id"] == (
            "tracktemplate:phase7:connected-straight-validation:1"
        )
        assert record["function_names"] == list(
            transition_workflow.PRODUCT_FUNCTION_NAMES
        )
        assert len(record["function_names"]) == 19
        assert record["caller_names"] == [
            name
            for name, _targets in transition_workflow.PRODUCT_CALLER_ROUTES
        ]
        assert len(record["caller_names"]) == 39

        adapter = session.module.build_platform_core
        assert type(adapter) is transition_workflow._PlatformCoreAdapter
        assert adapter.calculation is api.build_platform_core
        assert adapter.vector_factory is session.module.App.Vector
        assert tuple(inspect.signature(adapter).parameters) == PARAMETERS
        preparation = session.module.prepare_track_alignment
        assert type(preparation) is (
            transition_workflow._PrepareTrackAlignmentAdapter
        )
        assert preparation.calculation is api.prepare_track_alignment
        assert preparation.vector_factory is session.module.App.Vector
        assert api.prepare_track_alignment.__globals__["build_platform_core"] is (
            api.build_platform_core
        )

        case = _cases(_legacy_namespaces()[0])[0]
        first = adapter(*case)
        second = adapter(*case)
        assert first == second
        assert all(type(point) is session.module.App.Vector
                   for point in first["points"])
        assert all(point.z == 0.0 for point in first["points"])
        assert not ({id(point) for point in first["points"]}
                    & {id(point) for point in second["points"]})
        try:
            adapter.calculation = lambda *arguments: None
        except AttributeError:
            pass
        else:
            raise AssertionError("The platform-core adapter is mutable")

        for name in transition_workflow.PRODUCT_FUNCTION_NAMES:
            previous = session.module.__dict__[name]
            session.module.__dict__[name] = object()
            try:
                _expect_error(session.routing_record, "mixed")
            finally:
                session.module.__dict__[name] = previous
            assert session.routing_record() == record

        for dependency in (
            "platform_transition_displacement",
            "platform_peak_curvature_factor",
        ):
            globals_ = api.build_platform_core.__globals__
            previous = globals_[dependency]
            globals_[dependency] = object()
            try:
                _expect_error(session.routing_record, "platform")
            finally:
                globals_[dependency] = previous
            assert session.routing_record() == record

        invalid = _functions()
        invalid.pop("build_platform_core")
        invalid_host = load_host()
        before = core_proof._snapshot(invalid_host)
        _expect_error(
            lambda: transition_workflow.ModularTransitionWorkflowSession(
                invalid_host,
                invalid,
            ),
            "complete nineteen-function",
        )
        assert core_proof._snapshot(invalid_host) == before
        assert invalid_host.module.LAUNCH_COUNT == 0

        rollback_host = load_host()
        rollback_host.module.__dict__.pop("build_platform_core")
        before_keys = tuple(rollback_host.module.__dict__)
        before = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            transition_workflow.ModularTransitionWorkflowSession,
            "_validate_binding",
            side_effect=RuntimeError("controlled platform-core setup failure"),
        ):
            try:
                transition_workflow.ModularTransitionWorkflowSession(
                    rollback_host,
                    _functions(),
                )
            except RuntimeError as error:
                assert str(error) == "controlled platform-core setup failure"
            else:
                raise AssertionError("A controlled binding failure was lost")
        assert tuple(rollback_host.module.__dict__) == before_keys
        assert all(
            rollback_host.module.__dict__[name] is value
            for name, value in before.items()
        )
        assert "build_platform_core" not in rollback_host.module.__dict__
        assert rollback_host.module.LAUNCH_COUNT == 0


def main():
    validate_calculation()
    validate_complete_characterisation()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    main()
