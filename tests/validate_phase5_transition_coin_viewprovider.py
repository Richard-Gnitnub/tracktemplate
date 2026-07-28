#!/usr/bin/env python3
"""Validate the development-only Phase 5 Coin ViewProvider fixture."""

import hashlib
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)


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

    def getValue(self):
        return self.value


class _Group:
    def __init__(self):
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def findChild(self, child):
        try:
            return self.children.index(child)
        except ValueError:
            return -1

    def removeChild(self, child_or_index):
        if isinstance(child_or_index, int):
            del self.children[child_or_index]
        else:
            self.children.remove(child_or_index)

    def removeAllChildren(self):
        self.children.clear()

    def getChild(self, index):
        return self.children[index]


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


class _SelectionRoot(_Group):
    pass


class _SelectionType:
    def createInstance(self):
        return _SelectionRoot()


class _SoType:
    @staticmethod
    def fromName(name):
        assert name == "SoFCSelection"
        return _SelectionType()


class _FakeCoin:
    SoSeparator = _Group
    SoBaseColor = _BaseColor
    SoDrawStyle = _DrawStyle
    SoCoordinate3 = _Coordinate3
    SoLineSet = _LineSet
    SoType = _SoType


class _ViewObject:
    def __init__(self):
        self.RootNode = _Group()
        self.SwitchNode = _Group()
        self.SwitchNode.whichChild = _Field()
        self.RootNode.addChild(self.SwitchNode)
        self.Object = object()
        self._proxy = None
        self._display_modes = []

    @property
    def Proxy(self):
        return self._proxy

    @Proxy.setter
    def Proxy(self, value):
        self._proxy = value
        value.attach(self)

    def addDisplayMode(self, node, name):
        self.SwitchNode.addChild(node)
        self._display_modes.append(name)
        self.SwitchNode.whichChild.setValue(
            len(self.SwitchNode.children) - 1
        )

    def listDisplayModes(self):
        return list(self._display_modes)


class _Path:
    def __init__(self, nodes=()):
        self.nodes = list(nodes)

    def append(self, node):
        self.nodes.append(node)

    def findNode(self, node):
        try:
            return self.nodes.index(node)
        except ValueError:
            return -1


class _PickedPoint:
    def __init__(self, path):
        self._path = path

    def getPath(self):
        return self._path


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = 300.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:viewprovider",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 ViewProvider transition",
        end_name="Entry",
    )
    state = api.analyse_transition_state(api.TransitionState(intent))
    return api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        api.TransitionPreviewSpecification(segment_count=4),
    )


def _style():
    return renderer.TransitionCoinStyle(
        line_color_rgb=(0.9, 0.2, 0.1),
        line_width=3.0,
    )


def _expect_state_error(action, code):
    try:
        action()
    except api.TransitionStateError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionStateError {!r}".format(code))


def _validate_lifecycle_and_selection():
    artifact = _artifact()
    view_object = _ViewObject()
    proxy = viewprovider.TransitionCoinViewProviderFixture(
        view_object,
        artifact,
        _style(),
        _FakeCoin,
    )

    assert view_object.Proxy is proxy
    assert proxy.attached is True
    assert len(view_object.RootNode.children) == 1
    assert view_object.RootNode.children[0] is view_object.SwitchNode
    assert view_object.SwitchNode.children == [proxy.selection_root]
    assert len(proxy.selection_root.children) == 1
    assert proxy.display_mode == viewprovider.TRANSITION_COIN_VIEW_MODE
    assert proxy.getDisplayModes(view_object) == [
        viewprovider.TRANSITION_COIN_VIEW_MODE
    ]
    assert (
        proxy.getDefaultDisplayMode()
        == viewprovider.TRANSITION_COIN_VIEW_MODE
    )
    assert (
        proxy.setDisplayMode(viewprovider.TRANSITION_COIN_VIEW_MODE)
        == viewprovider.TRANSITION_COIN_VIEW_MODE
    )
    _expect_state_error(
        lambda: proxy.setDisplayMode("Unknown"),
        "unknown-coin-view-mode",
    )

    selection = proxy.selection_for_element(proxy.element_name)
    expected = artifact.payload.polylines[0]
    assert selection.visual_id == expected.visual_id
    assert selection.domain_id == expected.domain_id
    assert proxy.source_signature == artifact.source_signature
    assert proxy.style_signature == _style().contract_signature()

    path = _Path()
    assert proxy.getDetailPath(proxy.element_name, path, True) is True
    assert path.nodes == [
        view_object.RootNode,
        view_object.SwitchNode,
        proxy.selection_root,
    ]
    picked = _PickedPoint(_Path((proxy.selection_root,)))
    assert proxy.getElementPicked(picked) == proxy.element_name

    _expect_state_error(
        lambda: proxy.selection_for_element("unknown"),
        "unknown-coin-view-element",
    )
    _expect_state_error(
        lambda: proxy.getElementPicked(_PickedPoint(_Path())),
        "unknown-coin-view-pick",
    )
    assert proxy.dumps() is None
    assert proxy.loads(None) is None

    element_name = proxy.element_name
    selection_root = proxy.selection_root
    assert proxy.dispose() is True
    assert selection_root.children == []
    assert view_object.SwitchNode.children == [selection_root]
    assert proxy.attached is False
    assert proxy.dispose() is False
    _expect_state_error(
        lambda: proxy.selection_for_element(element_name),
        "discarded-coin-viewprovider",
    )


def _validate_attach_failure_cleanup():
    class PartialDisplayModeViewObject(_ViewObject):
        def addDisplayMode(self, node, name):
            super().addDisplayMode(node, name)
            raise RuntimeError("injected partial ViewProvider attach failure")

    view_object = PartialDisplayModeViewObject()
    error = _expect_state_error(
        lambda: viewprovider.TransitionCoinViewProviderFixture(
            view_object,
            _artifact(),
            _style(),
            _FakeCoin,
        ),
        "coin-viewprovider-attach-failed",
    )
    assert "injected partial ViewProvider attach failure" in error.detail
    assert len(view_object.SwitchNode.children) == 1
    assert view_object.SwitchNode.children[0].children == []
    assert view_object.Proxy.attached is False
    _expect_state_error(
        lambda: view_object.Proxy.selection_for_element(
            _artifact().payload.polylines[0].visual_id
        ),
        "discarded-coin-viewprovider",
    )


def _validate_partial_disposal():
    view_object = _ViewObject()
    proxy = viewprovider.TransitionCoinViewProviderFixture(
        view_object,
        _artifact(),
        _style(),
        _FakeCoin,
    )
    element_name = proxy.element_name
    selection_root = proxy.selection_root
    original_remove = selection_root.removeAllChildren
    cleanup_calls = []

    def clear_then_fail():
        original_remove()
        cleanup_calls.append(True)
        if len(cleanup_calls) == 1:
            raise RuntimeError("injected partial ViewProvider cleanup failure")

    selection_root.removeAllChildren = clear_then_fail
    error = _expect_state_error(
        proxy.dispose,
        "coin-viewprovider-dispose-failed",
    )
    assert "injected partial ViewProvider cleanup failure" in error.detail
    assert selection_root.children == []
    _expect_state_error(
        lambda: proxy.selection_for_element(element_name),
        "discarded-coin-viewprovider",
    )
    assert proxy.dispose() is True
    assert len(cleanup_calls) == 2
    assert proxy.dispose() is False


def _validate_structure_and_controls():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules[
        "tracktemplate.presentation.transition_coin_viewprovider"
    ]
    assert module["layer"] == "presentation"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "tracktemplate.application.transition_state",
        "tracktemplate.presentation.transition_coin",
    ]

    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/presentation/__init__.py",
    ):
        assert "transition_coin_viewprovider" not in (
            ROOT / relative
        ).read_text(encoding="utf-8")
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected

    bridge_root = ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-phase5-transition-viewprovider"
    runner = bridge_root / "run_phase5_transition_viewprovider.py"
    gui_proof = (
        ROOT
        / "tests"
        / "freecad_gui_validate_phase5_transition_coin_viewprovider.py"
    )
    assert wrapper.is_file()
    assert runner.is_file()
    assert gui_proof.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    gui_proof_text = gui_proof.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert "run_phase5_transition_viewprovider.py" in wrapper_text
    assert "_wait_for_gui(client)" in runner_text
    assert "splash_visible" in runner_text
    assert "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=" in runner_text
    assert "freecad_gui_validate_phase5_transition_coin_viewprovider.py" in (
        runner_text
    )
    assert 'payload.get("selection_input") != "qt-mouse-click"' in (
        runner_text
    )
    assert 'payload.get("pointer_target", {}).get("class_name")' in (
        runner_text
    )
    assert '!= "QOpenGLWidget"' in runner_text
    assert "QtTest.QTest.mouseMove(" in gui_proof_text
    assert "QtTest.QTest.mouseClick(" in gui_proof_text
    assert "proxy.pick_callback_count = 0" in gui_proof_text
    assert "Gui.Selection.addSelection(" not in gui_proof_text

    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT / "reference" / "current" / "PHASE_EVIDENCE.md"
    ).read_text(encoding="utf-8")
    assert (
        "| 5 | Lightweight editing prototype and renderer decision "
        "| 0/4 evidenced | Current"
    ) in plan
    assert "## Development-only ViewProvider fixture tranche" in evidence
    assert "No renderer or Phase 5 exit is accepted" in evidence


def validate():
    _validate_lifecycle_and_selection()
    _validate_attach_failure_cleanup()
    _validate_partial_disposal()
    _validate_structure_and_controls()
    print("Phase 5 transition Coin ViewProvider validation passed")


if __name__ == "__main__":
    validate()
