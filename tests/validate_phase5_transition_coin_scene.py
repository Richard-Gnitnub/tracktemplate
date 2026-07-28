#!/usr/bin/env python3
"""Validate the unexposed Phase 5 transition Coin scene adapter."""

import hashlib
import math
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


class _Field:
    def __init__(self):
        self.value = None

    def setValue(self, *values):
        self.value = values[0] if len(values) == 1 else tuple(values)

    def setValues(self, start, count, values):
        assert start == 0
        assert count == len(values)
        self.value = tuple(tuple(value) for value in values)


class _Group:
    def __init__(self):
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def removeAllChildren(self):
        self.children.clear()


class _BaseColor:
    def __init__(self):
        self.rgb = _Field()


class _DrawStyle:
    def __init__(self):
        self.lineWidth = _Field()


class _Coordinate3:
    def __init__(self):
        self.point = _Field()


class _LineSet:
    def __init__(self):
        self.numVertices = _Field()


class _FakeCoin:
    SoSeparator = _Group
    SoBaseColor = _BaseColor
    SoDrawStyle = _DrawStyle
    SoCoordinate3 = _Coordinate3
    SoLineSet = _LineSet


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = 300.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:coin",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 Coin transition",
        end_name="Entry",
    )
    state = api.analyse_transition_state(api.TransitionState(intent))
    return api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        api.TransitionPreviewSpecification(segment_count=4),
    )


def _style(**changes):
    values = {
        "line_color_rgb": (0.2, 0.6, 0.9),
        "line_width": 2.0,
    }
    values.update(changes)
    return renderer.TransitionCoinStyle(**values)


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _validate_style_contract():
    style = _style()
    assert style.contract_signature() == _style().contract_signature()
    assert style.contract_signature() != _style(
        line_width=3.0
    ).contract_signature()
    assert style.contract_signature() != _style(
        line_color_rgb=(0.3, 0.6, 0.9)
    ).contract_signature()

    for invalid in (
        {"line_color_rgb": (0.2, 0.6)},
        {"line_color_rgb": (0.2, 0.6, 1.1)},
        {"line_color_rgb": (0.2, math.nan, 0.9)},
        {"line_color_rgb": [0.2, 0.6, 0.9]},
        {"line_width": True},
        {"line_width": 0.0},
        {"line_width": math.inf},
    ):
        _expect_state_error(
            lambda invalid=invalid: _style(**invalid),
            "invalid-coin-style",
        )


def _validate_scene_and_selection_mapping():
    artifact = _artifact()
    style = _style()
    binding = renderer.build_transition_coin_binding(
        artifact,
        style,
        _FakeCoin,
    )

    assert binding.source_signature == artifact.source_signature
    assert binding.style_signature == style.contract_signature()
    assert len(binding.root.children) == 1
    layer = binding.root.children[0]
    assert len(layer.children) == 4
    color, draw_style, coordinates, line_set = layer.children
    assert color.rgb.value == style.line_color_rgb
    assert draw_style.lineWidth.value == style.line_width

    polyline = artifact.payload.polylines[0]
    assert coordinates.point.value == tuple(
        (point.x_mm, point.y_mm, 0.0)
        for point in polyline.points
    )
    assert line_set.numVertices.value == len(polyline.points)
    assert len(binding.selections) == 1
    selection = binding.selections[0]
    assert selection.layer_id == polyline.layer_id
    assert selection.visual_id == polyline.visual_id
    assert selection.domain_id == polyline.domain_id
    assert selection.node is line_set
    assert binding.selection_for_node(line_set) is selection
    _expect_state_error(
        lambda: binding.selection_for_node(object()),
        "unknown-coin-selection",
    )

    rebuilt = renderer.build_transition_coin_binding(
        artifact,
        style,
        _FakeCoin,
    )
    assert rebuilt.root is not binding.root
    assert rebuilt.source_signature == binding.source_signature
    assert rebuilt.style_signature == binding.style_signature
    assert tuple(
        (item.layer_id, item.visual_id, item.domain_id)
        for item in rebuilt.selections
    ) == tuple(
        (item.layer_id, item.visual_id, item.domain_id)
        for item in binding.selections
    )


def _validate_failure_and_disposal():
    artifact = _artifact()
    retained = renderer.build_transition_coin_binding(
        artifact,
        _style(),
        _FakeCoin,
    )
    retained_children = tuple(retained.root.children)

    class FailingCoordinate3:
        def __init__(self):
            raise RuntimeError("injected Coin coordinate failure")

    class FailingCoin(_FakeCoin):
        SoCoordinate3 = FailingCoordinate3

    error = _expect_state_error(
        lambda: renderer.build_transition_coin_binding(
            artifact,
            _style(),
            FailingCoin,
        ),
        "coin-scene-build-failed",
    )
    assert "injected Coin coordinate failure" in error.detail
    assert tuple(retained.root.children) == retained_children
    assert len(retained.selections) == 1

    class FailingIdentityNode:
        def getNodeId(self):
            raise RuntimeError("injected Coin identity failure")

    identity_error = _expect_state_error(
        lambda: retained.selection_for_node(FailingIdentityNode()),
        "coin-node-identity-failed",
    )
    assert "injected Coin identity failure" in identity_error.detail

    node = retained.selections[0].node
    assert retained.discard() is True
    assert retained.root.children == []
    assert retained.selections == ()
    assert retained.discard() is False
    _expect_state_error(
        lambda: retained.selection_for_node(node),
        "discarded-coin-binding",
    )

    partial = renderer.build_transition_coin_binding(
        artifact,
        _style(),
        _FakeCoin,
    )
    partial_node = partial.selections[0].node
    original_remove = partial.root.removeAllChildren
    cleanup_calls = []

    def clear_then_fail():
        original_remove()
        cleanup_calls.append(True)
        if len(cleanup_calls) == 1:
            raise RuntimeError("injected partial Coin cleanup failure")

    partial.root.removeAllChildren = clear_then_fail
    cleanup_error = _expect_state_error(
        partial.discard,
        "coin-scene-discard-failed",
    )
    assert "injected partial Coin cleanup failure" in cleanup_error.detail
    assert partial.root.children == []
    assert partial.selections == ()
    _expect_state_error(
        lambda: partial.selection_for_node(partial_node),
        "discarded-coin-binding",
    )
    assert partial.discard() is True
    assert len(cleanup_calls) == 2
    assert partial.discard() is False


def _validate_rejections():
    artifact = _artifact()
    scene = artifact.payload
    _expect_state_error(
        lambda: renderer.build_transition_coin_binding(
            object(),
            _style(),
            _FakeCoin,
        ),
        "invalid-coin-source",
    )
    _expect_state_error(
        lambda: renderer.build_transition_coin_binding(
            api.TransitionDerivedArtifact(
                stage="exact-validation",
                source_signature=artifact.source_signature,
                payload=scene,
            ),
            _style(),
            _FakeCoin,
        ),
        "invalid-coin-source",
    )
    _expect_state_error(
        lambda: renderer.build_transition_coin_binding(
            api.TransitionDerivedArtifact(
                stage="preview",
                source_signature=artifact.source_signature,
                payload=object(),
            ),
            _style(),
            _FakeCoin,
        ),
        "invalid-coin-source",
    )

    class IncompleteCoin:
        SoSeparator = _Group

    _expect_state_error(
        lambda: renderer.build_transition_coin_binding(
            artifact,
            _style(),
            IncompleteCoin,
        ),
        "invalid-coin-module",
    )


def _validate_structure_and_disabled_route():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules["tracktemplate.presentation.transition_coin"]
    assert module["layer"] == "presentation"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "dataclasses",
        "math",
        "tracktemplate.application.transition_derived",
        "tracktemplate.application.transition_state",
        "tracktemplate.presentation.transition_preview",
    ]

    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/presentation/__init__.py",
    ):
        assert "transition_coin" not in (ROOT / relative).read_text(
            encoding="utf-8"
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
from tracktemplate.presentation import transition_coin
assert attempted == []
assert transition_coin.TRANSITION_COIN_CONTRACT_ID.endswith(".v1")
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def _validate_controls():
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    evidence = (
        ROOT / "reference" / "current" / "PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert "| 5 | Lightweight editing prototype and renderer decision | 0/4 evidenced | Current" in plan
    assert "## Coin scene-graph feasibility tranche" in evidence
    assert "No renderer or Phase 5 exit is accepted" in evidence


def validate():
    _validate_style_contract()
    _validate_scene_and_selection_mapping()
    _validate_failure_and_disposal()
    _validate_rejections()
    _validate_structure_and_disabled_route()
    _validate_controls()
    print("Phase 5 transition Coin scene validation passed")


if __name__ == "__main__":
    validate()
