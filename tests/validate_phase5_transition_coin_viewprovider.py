#!/usr/bin/env python3
"""Validate the development-only Phase 5 Coin ViewProvider fixture."""

import ast
import hashlib
import importlib
import math
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tests.phase5_transition_coin_test_protocol import (  # noqa: E402
    _FakeCoin,
    _Field,
    _Group,
)
from tracktemplate import api  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_attachment as attachment,
)
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


class _ViewObject:
    def __init__(
        self,
        *,
        initial_proxy=None,
        fail_display_mode=False,
        fail_proxy_restore=False,
    ):
        self.RootNode = _Group()
        self.SwitchNode = _Group()
        self.SwitchNode.whichChild = _Field()
        self.RootNode.addChild(self.SwitchNode)
        self.Object = object()
        self._proxy = initial_proxy
        self._display_modes = []
        self._fail_display_mode = fail_display_mode
        self._fail_proxy_restore = fail_proxy_restore
        self._initial_proxy = initial_proxy

    @property
    def Proxy(self):
        return self._proxy

    @Proxy.setter
    def Proxy(self, value):
        if (
            self._fail_proxy_restore
            and value == self._initial_proxy
            and self._proxy is not self._initial_proxy
        ):
            raise RuntimeError("injected proxy restoration failure")
        self._proxy = value
        if value is None or isinstance(value, int):
            return
        value.attach(self)

    def addDisplayMode(self, node, name):
        if self._fail_display_mode:
            raise RuntimeError("injected document attachment failure")
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


def _state(
    transition_length_mm=300.0,
    *,
    transition_id="transition:phase5:viewprovider",
    end_name="Entry",
):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id=transition_id,
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 ViewProvider transition",
        end_name=end_name,
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _artifact(state=None):
    if state is None:
        state = _state()
    return api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        api.TransitionPreviewSpecification(segment_count=4),
    )


class _PreviewCacheProbe:
    """Observe one retained renderer-neutral preview-cache lifecycle."""

    def __init__(self):
        self.cache = api.TransitionDerivedCache()
        self.specification = api.TransitionPreviewSpecification(
            segment_count=4
        )
        self.calls = []

    def artifact_for_state(self, state):
        previous = self.cache.artifact("preview")
        artifact = api.regenerate_transition_preview(
            self.cache,
            state,
            self.specification,
        )
        self.calls.append((state, previous, artifact))
        return artifact

    def status(self, state):
        return self.cache.status(
            state,
            self.specification.derived_request(),
        )

    def discard(self):
        return self.cache.discard("preview")


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


def _validate_restore_style_attach():
    class RestoreStyleViewObject(_ViewObject):
        @property
        def Proxy(self):
            return self._proxy

        @Proxy.setter
        def Proxy(self, value):
            self._proxy = value

    view_object = RestoreStyleViewObject()
    proxy = viewprovider.TransitionCoinViewProviderFixture(
        view_object,
        _artifact(),
        _style(),
        _FakeCoin,
    )
    assert view_object.Proxy is proxy
    assert proxy.attached is True
    assert view_object.SwitchNode.children == [proxy.selection_root]
    assert proxy.dispose() is True


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


def _validate_state_refresh():
    initial = _state()
    changed = _state(340.0)
    preview = _PreviewCacheProbe()
    initial_artifact = preview.artifact_for_state(initial)

    class Source:
        state = initial

    source = Source()

    def state_reader(obj):
        assert obj is source
        return obj.state

    view_object = _ViewObject()
    proxy = viewprovider.TransitionCoinViewProviderFixture(
        view_object,
        initial_artifact,
        _style(),
        _FakeCoin,
        state_reader=state_reader,
        artifact_for_state=preview.artifact_for_state,
        source_property_name="CanonicalState",
    )
    selection_root = proxy.selection_root
    initial_root = selection_root.children[0]
    initial_source_signature = proxy.source_signature
    initial_selection = proxy.selection_for_element(proxy.element_name)
    assert preview.status(initial) == "current"

    assert proxy.refresh_for_state(initial) is False
    assert preview.calls[-1] == (
        initial,
        initial_artifact,
        initial_artifact,
    )
    assert selection_root.children == [initial_root]

    assert proxy.refresh_for_state(changed) is True
    changed_artifact = preview.cache.artifact("preview")
    assert changed_artifact is not initial_artifact
    assert preview.status(changed) == "current"
    assert preview.status(initial) == "stale"
    changed_root = selection_root.children[0]
    assert changed_root is not initial_root
    assert initial_root.children == []
    assert proxy.source_signature != initial_source_signature
    assert proxy.selection_for_element(proxy.element_name).domain_id == (
        initial_selection.domain_id
    )
    changed_source_signature = proxy.source_signature

    source.state = initial
    assert proxy.updateData(source, "Unrelated") is None
    assert proxy.source_signature == changed_source_signature
    assert proxy.updateData(source, "CanonicalState") is True
    assert proxy.source_signature == initial_source_signature
    restored_artifact = preview.cache.artifact("preview")
    assert restored_artifact.source_signature == (
        initial_artifact.source_signature
    )
    assert restored_artifact.payload == initial_artifact.payload
    assert preview.status(initial) == "current"
    assert preview.status(changed) == "stale"

    source.state = changed
    with proxy.defer_document_updates():
        assert proxy.updateData(source, "CanonicalState") is None
        assert proxy.source_signature == initial_source_signature
        assert proxy.refresh_for_state(changed) is True
    assert proxy.source_signature == changed_source_signature
    assert preview.status(changed) == "current"

    failure = RuntimeError("injected preview artifact failure")

    def failing_artifact_for_state(state):
        preview.artifact_for_state(state)
        raise failure

    proxy._artifact_for_state = failing_artifact_for_state
    before_failure = (
        proxy.source_signature,
        proxy.selection_root.children[0],
        proxy.selection_for_element(proxy.element_name),
    )
    error = _expect_state_error(
        lambda: proxy.refresh_for_state(initial),
        "coin-viewprovider-refresh-failed",
    )
    assert "injected preview artifact failure" in error.detail
    assert (
        proxy.source_signature,
        proxy.selection_root.children[0],
        proxy.selection_for_element(proxy.element_name),
    ) == before_failure
    assert preview.status(initial) == "current"
    assert preview.status(changed) == "stale"

    proxy._artifact_for_state = preview.artifact_for_state
    assert proxy.refresh_for_state(changed) is False
    assert preview.status(changed) == "current"
    assert proxy.refresh_for_state(initial) is True
    assert proxy.source_signature == initial_source_signature

    retired = proxy._binding
    original_discard = retired.discard
    discard_calls = []

    def discard_then_fail_once():
        result = original_discard()
        discard_calls.append(True)
        if len(discard_calls) == 1:
            raise RuntimeError("injected retired-binding cleanup failure")
        return result

    retired.discard = discard_then_fail_once
    error = _expect_state_error(
        lambda: proxy.refresh_for_state(changed),
        "coin-viewprovider-refresh-failed",
    )
    assert "injected retired-binding cleanup failure" in error.detail
    assert proxy.source_signature == changed_source_signature
    assert proxy._retired_bindings == [retired]
    assert proxy.refresh_for_state(initial) is True
    assert proxy.source_signature == initial_source_signature
    assert proxy._retired_bindings == []
    assert len(discard_calls) == 2
    assert proxy.dispose() is True
    assert preview.discard() == ("preview",)
    assert preview.cache.artifact("preview") is None

    _expect_state_error(
        lambda: viewprovider.TransitionCoinViewProviderFixture(
            _ViewObject(),
            _artifact(initial),
            _style(),
            _FakeCoin,
            state_reader=state_reader,
        ),
        "invalid-coin-viewprovider-refresh",
    )


def _validate_disposable_reconstruction():
    state = _state()
    original_preview = _PreviewCacheProbe()
    assert original_preview.status(state) == "missing"
    original_artifact = original_preview.artifact_for_state(state)
    original_view_object = _ViewObject()
    original_proxy = viewprovider.TransitionCoinViewProviderFixture(
        original_view_object,
        original_artifact,
        _style(),
        _FakeCoin,
    )
    original_selection = original_proxy.selection_for_element(
        original_proxy.element_name
    )
    original_selection_root = original_proxy.selection_root
    original_scene_root = original_selection_root.children[0]

    assert original_proxy.dumps() is None
    assert original_proxy.dispose() is True
    assert original_preview.discard() == ("preview",)
    assert original_preview.status(state) == "missing"

    reopened_preview = _PreviewCacheProbe()
    assert reopened_preview.cache is not original_preview.cache
    assert reopened_preview.status(state) == "missing"
    reopened_artifact = reopened_preview.artifact_for_state(state)
    assert reopened_artifact is not original_artifact
    assert (
        reopened_artifact.source_signature
        == original_artifact.source_signature
    )
    assert reopened_artifact.payload == original_artifact.payload

    reopened_view_object = _ViewObject()
    reopened_proxy = viewprovider.TransitionCoinViewProviderFixture(
        reopened_view_object,
        reopened_artifact,
        _style(),
        _FakeCoin,
    )
    reopened_selection = reopened_proxy.selection_for_element(
        reopened_proxy.element_name
    )
    assert reopened_proxy is not original_proxy
    assert reopened_proxy.selection_root is not original_selection_root
    assert reopened_proxy.selection_root.children[0] is not original_scene_root
    assert reopened_selection == original_selection
    assert reopened_proxy.source_signature == (
        original_artifact.source_signature
    )
    assert reopened_proxy.dispose() is True
    assert reopened_preview.discard() == ("preview",)


class _Document:
    def __init__(self):
        self.Objects = []


class _DocumentObject:
    def __init__(
        self,
        document,
        name,
        state,
        *,
        initial_proxy=None,
        fail_display_mode=False,
        fail_proxy_restore=False,
    ):
        self.Document = document
        self.Name = name
        self.state = state
        self.ViewObject = _ViewObject(
            initial_proxy=initial_proxy,
            fail_display_mode=fail_display_mode,
            fail_proxy_restore=fail_proxy_restore,
        )
        self.ViewObject.Object = self
        document.Objects.append(self)


def _attachment_records(document):
    return tuple(
        (obj, obj.state)
        for obj in reversed(document.Objects)
    )


def _attachment_state_reader(obj):
    return obj.state


def _validate_document_attachment():
    document = _Document()
    entry_state = _state(
        300.0,
        transition_id="transition:phase5:attachment:entry",
        end_name="Entry",
    )
    exit_state = _state(
        420.0,
        transition_id="transition:phase5:attachment:exit",
        end_name="Exit",
    )
    entry = _DocumentObject(
        document,
        "EntryObject",
        entry_state,
        initial_proxy=0,
    )
    exit_record = _DocumentObject(
        document,
        "ExitObject",
        exit_state,
    )
    specification = api.TransitionPreviewSpecification(segment_count=4)
    attached = attachment.TransitionCoinDocumentAttachmentFixture(
        document,
        record_loader=_attachment_records,
        state_reader=_attachment_state_reader,
        source_property_name="TrackTemplateStateJSON",
        specification=specification,
        style=_style(),
        coin_module=_FakeCoin,
    )
    assert attached.attached is True
    assert attached.attachment_count == 2
    assert attached.transition_ids == (
        entry_state.intent.transition_id,
        exit_state.intent.transition_id,
    )
    entry_proxy = attached.proxy_for_transition(
        entry_state.intent.transition_id
    )
    exit_proxy = attached.proxy_for_transition(
        exit_state.intent.transition_id
    )
    entry_cache = attached.cache_for_transition(
        entry_state.intent.transition_id
    )
    exit_cache = attached.cache_for_transition(
        exit_state.intent.transition_id
    )
    assert entry.ViewObject.Proxy is entry_proxy
    assert exit_record.ViewObject.Proxy is exit_proxy
    assert entry_cache.status(
        entry_state,
        specification.derived_request(),
    ) == "current"
    assert exit_cache.status(
        exit_state,
        specification.derived_request(),
    ) == "current"

    changed_exit = _state(
        360.0,
        transition_id=exit_state.intent.transition_id,
        end_name="Exit",
    )
    previous_signature = exit_proxy.source_signature
    exit_record.state = changed_exit
    assert attached.refresh_transition(
        exit_state.intent.transition_id
    ) is True
    assert exit_proxy.source_signature != previous_signature
    assert attached.refresh_transition(
        exit_state.intent.transition_id
    ) is False
    _expect_state_error(
        lambda: attached.proxy_for_transition(
            "transition:phase5:attachment:missing"
        ),
        "unknown-coin-document-transition",
    )

    assert attached.dispose() == attached.transition_ids
    assert attached.attached is False
    assert entry.ViewObject.Proxy == 0
    assert exit_record.ViewObject.Proxy is None
    assert entry_cache.artifact("preview") is None
    assert exit_cache.artifact("preview") is None
    for record in (entry, exit_record):
        assert len(record.ViewObject.SwitchNode.children) == 1
        assert record.ViewObject.SwitchNode.children[0].children == []
    assert attached.dispose() == ()
    _expect_state_error(
        lambda: attached.refresh_transition(
            exit_state.intent.transition_id
        ),
        "discarded-coin-document-attachment",
    )

    failing_document = _Document()
    first_state = _state(
        300.0,
        transition_id="transition:phase5:attachment:a",
    )
    second_state = _state(
        420.0,
        transition_id="transition:phase5:attachment:b",
        end_name="Exit",
    )
    first = _DocumentObject(
        failing_document,
        "FirstObject",
        first_state,
        initial_proxy=0,
    )
    second = _DocumentObject(
        failing_document,
        "SecondObject",
        second_state,
        fail_display_mode=True,
    )
    failure = _expect_state_error(
        lambda: attachment.TransitionCoinDocumentAttachmentFixture(
            failing_document,
            record_loader=_attachment_records,
            state_reader=_attachment_state_reader,
            source_property_name="TrackTemplateStateJSON",
            specification=specification,
            style=_style(),
            coin_module=_FakeCoin,
        ),
        "coin-document-attachment-failed",
    )
    assert "injected document attachment failure" in str(failure)
    assert first.ViewObject.Proxy == 0
    assert second.ViewObject.Proxy is None
    assert first.state == first_state
    assert second.state == second_state
    assert len(first.ViewObject.SwitchNode.children) == 1
    assert first.ViewObject.SwitchNode.children[0].children == []
    assert second.ViewObject.SwitchNode.children == []

    cleanup_failure_document = _Document()
    cleanup_failure_state = _state(
        transition_id="transition:phase5:attachment:cleanup-failure",
    )
    _DocumentObject(
        cleanup_failure_document,
        "CleanupFailureObject",
        cleanup_failure_state,
        initial_proxy=0,
        fail_display_mode=True,
        fail_proxy_restore=True,
    )
    cleanup_failure = _expect_state_error(
        lambda: attachment.TransitionCoinDocumentAttachmentFixture(
            cleanup_failure_document,
            record_loader=_attachment_records,
            state_reader=_attachment_state_reader,
            source_property_name="TrackTemplateStateJSON",
            specification=specification,
            style=_style(),
            coin_module=_FakeCoin,
        ),
        "coin-document-attachment-failed",
    )
    assert "injected document attachment failure" in str(cleanup_failure)
    assert "injected proxy restoration failure" in str(cleanup_failure)

    replaced_document = _Document()
    replaced_state = _state(
        transition_id="transition:phase5:attachment:replaced",
    )
    replaced = _DocumentObject(
        replaced_document,
        "ReplacedProxyObject",
        replaced_state,
    )
    replaced_attachment = (
        attachment.TransitionCoinDocumentAttachmentFixture(
            replaced_document,
            record_loader=_attachment_records,
            state_reader=_attachment_state_reader,
            source_property_name="TrackTemplateStateJSON",
            specification=specification,
            style=_style(),
            coin_module=_FakeCoin,
        )
    )
    managed_proxy = replaced.ViewObject.Proxy
    managed_cache = replaced_attachment.cache_for_transition(
        replaced_state.intent.transition_id
    )
    external_proxy = object()
    replaced.ViewObject._proxy = external_proxy
    _expect_state_error(
        replaced_attachment.dispose,
        "coin-document-attachment-dispose-failed",
    )
    assert replaced.ViewObject.Proxy is external_proxy
    assert replaced_attachment.attached is False
    assert managed_cache.artifact("preview") is None
    replaced.ViewObject._proxy = managed_proxy
    assert replaced_attachment.dispose() == (
        replaced_state.intent.transition_id,
    )
    assert replaced.ViewObject.Proxy is None


def _validate_shared_gui_harness():
    helper_module = "tests.phase5_transition_coin_gui_harness"
    helper_path = ROOT / "tests" / "phase5_transition_coin_gui_harness.py"
    assert helper_path.is_file(), "missing shared Coin GUI test harness"

    harness = importlib.import_module(helper_module)
    processed = []
    harness._process_gui(
        lambda: processed.append("freecad"),
        lambda: processed.append("qt"),
    )
    assert processed == ["freecad", "qt"] * 5

    observer = harness._SelectionObserver()
    observer.addSelection(
        "Document",
        "Object",
        "TransitionPreviewCentreline",
        (1, 2.5, 3),
    )
    assert observer.events == [(
        "Document",
        "Object",
        "TransitionPreviewCentreline",
        (1.0, 2.5, 3.0),
    )]
    assert issubclass(
        harness._ObservedTransitionCoinViewProviderFixture,
        viewprovider.TransitionCoinViewProviderFixture,
    )

    consumers = {
        "freecad_gui_profile_phase5_transition_coin_resources.py": {
            "_process_gui": "_shared_process_gui",
        },
        "freecad_gui_validate_phase5_transition_coin_viewprovider.py": {
            "_ObservedTransitionCoinViewProviderFixture": None,
            "_SelectionObserver": None,
            "_process_gui": "_shared_process_gui",
        },
        "freecad_gui_validate_phase5_transition_multi_object_edit.py": {
            "_ObservedTransitionCoinViewProviderFixture": None,
            "_SelectionObserver": None,
            "_process_gui": "_shared_process_gui",
        },
    }
    consumer_paths = {
        ROOT / "tests" / filename: expected_imports
        for filename, expected_imports in consumers.items()
    }
    trees = {
        path: ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
        for path in (helper_path, *consumer_paths)
    }
    for shared_name in (
        "_ObservedTransitionCoinViewProviderFixture",
        "_SelectionObserver",
        "_process_gui",
    ):
        owners = [
            path
            for path, tree in trees.items()
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
            and node.name == shared_name
        ]
        assert owners == [helper_path], (shared_name, owners)

    for path, expected_imports in consumer_paths.items():
        tree = trees[path]
        imported = {
            alias.name: alias.asname
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == helper_module
            for alias in node.names
        }
        assert imported == expected_imports, path.name
        assert "_process_gui = functools.partial(" in path.read_text(
            encoding="utf-8"
        ), path.name


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
        "contextlib",
        "tracktemplate.application.transition_state",
        "tracktemplate.presentation.transition_coin",
    ]
    attachment_module = modules[
        "tracktemplate.presentation.transition_coin_attachment"
    ]
    assert attachment_module["layer"] == "presentation"
    assert attachment_module["warning_signals"] == []
    assert attachment_module["imports"] == [
        "tracktemplate.application.transition_derived",
        "tracktemplate.application.transition_state",
        "tracktemplate.presentation.transition_coin",
        "tracktemplate.presentation.transition_coin_viewprovider",
        "tracktemplate.presentation.transition_preview",
    ]

    for relative in (
        "TrackTemplate.FCMacro",
        "tracktemplate/api.py",
        "tracktemplate/presentation/__init__.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "transition_coin_viewprovider" not in source
        assert "transition_coin_attachment" not in source
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
    assert 'payload.get("edit_undo_units") != 1' in runner_text
    assert 'payload.get("edit_failure_recovered") is not True' in (
        runner_text
    )
    assert 'payload.get("preview_cache_retained") is not True' in (
        runner_text
    )
    assert 'payload.get("preview_cache_reuse_proved") is not True' in (
        runner_text
    )
    assert 'payload.get("preview_cache_failure_recovered") is not True' in (
        runner_text
    )
    assert 'payload.get("change_back_undo_units") != 1' in runner_text
    assert (
        'payload.get("change_back_restored_initial") is not True'
        in runner_text
    )
    assert 'payload.get("save_route_exercised") is not True' in (
        runner_text
    )
    for field in (
        "reopened_attachment_boundary",
        "reopened_attachment_count",
        "reopened_attachment_disposed",
        "reopened_attachment_explicit_post_open",
        "reopened_attachment_failure_recovered",
        "reopened_attachment_history_delta",
        "reopened_attachment_order",
        "reopened_attachment_refresh_reused",
        "reopened_stored_state_unchanged",
    ):
        assert 'payload.get("{}")'.format(field) in runner_text
    for field in (
        "reopened_cache_is_new",
        "reopened_cache_rebuilt",
        "reopened_cache_started_missing",
        "reopened_canonical_state_equal",
        "reopened_derived_state_persisted",
        "reopened_empty_switch_child_retained",
        "reopened_object_identity_preserved",
        "reopened_preview_equivalent",
        "reopened_schema_unchanged",
        "reopened_viewprovider_is_new",
        "reopened_viewprovider_rebuilt",
    ):
        assert 'payload.get("{}")'.format(field) in runner_text
    assert 'payload.get("reopened_object_count") != 1' in runner_text
    assert (
        'payload.get("reopened_visible_red_pixels", 0) < 100'
        in runner_text
    )
    assert 'payload.get("pointer_target", {}).get("class_name")' in (
        runner_text
    )
    assert '!= "QOpenGLWidget"' in runner_text
    assert "QtTest.QTest.mouseMove(" in gui_proof_text
    assert "QtTest.QTest.mouseClick(" in gui_proof_text
    assert "proxy.pick_callback_count = 0" in gui_proof_text
    assert "Gui.Selection.addSelection(" not in gui_proof_text
    assert "command.edit_transition_intent(" in gui_proof_text
    assert "document.undo()" in gui_proof_text
    assert "document.redo()" in gui_proof_text
    assert "injected GUI preview refresh failure" in gui_proof_text
    assert "preview_cache = api.TransitionDerivedCache()" in gui_proof_text
    assert "change_back_result = command.edit_transition_intent(" in (
        gui_proof_text
    )
    assert "hashlib" not in gui_proof_text
    assert "document.saveAs(" in gui_proof_text
    assert "App.openDocument(" in gui_proof_text
    assert "adapter.read_transition_objects" in gui_proof_text
    assert (
        "TransitionCoinDocumentAttachmentFixture(" in gui_proof_text
    )
    assert "injected post-open attachment failure" in gui_proof_text

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
    assert (
        "## Application-command edit and atomic Undo/Redo tranche"
        in evidence
    )
    assert "## Retained preview-cache regression tranche" in evidence
    assert (
        "## Disposable preview save/reopen regression tranche"
        in evidence
    )
    assert "## Coin GUI harness consolidation tranche" in evidence
    assert "## Coin fake-protocol consolidation tranche" in evidence
    assert "No renderer or Phase 5 exit is accepted" in evidence


def validate():
    _validate_lifecycle_and_selection()
    _validate_restore_style_attach()
    _validate_attach_failure_cleanup()
    _validate_partial_disposal()
    _validate_state_refresh()
    _validate_disposable_reconstruction()
    _validate_document_attachment()
    _validate_shared_gui_harness()
    _validate_structure_and_controls()
    print("Phase 5 transition Coin ViewProvider validation passed")


if __name__ == "__main__":
    validate()
