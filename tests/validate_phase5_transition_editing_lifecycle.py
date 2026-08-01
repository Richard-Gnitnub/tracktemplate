#!/usr/bin/env python3
"""Validate the explicit, reversible B16 transition-editing lifecycle."""

import ast
import pathlib
import sys
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tests.phase5_transition_coin_test_protocol import _FakeCoin  # noqa: E402
from tests.validate_phase5_transition_coin_viewprovider import (  # noqa: E402
    _ViewObject,
    _artifact,
    _style,
)
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)
from tracktemplate.ui import transition_editing_lifecycle as lifecycle  # noqa: E402


TRANSITION_IDS = (
    "SET-001/curve-track/2/transition/entry",
    "SET-001/curve-track/2/transition/exit",
)


class _Attachment:
    def __init__(self, transition_ids=TRANSITION_IDS, failures=0):
        self.attached = True
        self.transition_ids = tuple(transition_ids)
        self.attachment_count = len(self.transition_ids)
        self.dispose_calls = 0
        self.failures = failures

    def dispose(self):
        self.dispose_calls += 1
        if self.dispose_calls <= self.failures:
            raise RuntimeError("injected attachment cleanup failure")
        self.attached = False
        return self.transition_ids

class _Dialog:
    def __init__(self, controller, close_failures=0):
        self.controller = controller
        self.close_calls = 0
        self.close_failures = close_failures
        self.refresh_calls = 0
        self.show_calls = 0

    def refresh_selection(self):
        self.refresh_calls += 1
        return True

    def show(self):
        self.show_calls += 1

    def close(self):
        self.close_calls += 1
        if self.close_calls <= self.close_failures:
            raise RuntimeError("injected dialog cleanup failure")


class _ObserverApp:
    def __init__(
        self,
        document,
        *,
        add_failure=False,
        remove_failures=0,
    ):
        self.ActiveDocument = document
        self.add_failure = bool(add_failure)
        self.remove_failures = int(remove_failures)
        self.add_calls = []
        self.remove_calls = []
        self.observers = []

    def addDocumentObserver(self, observer):
        self.add_calls.append(observer)
        self.observers.append(observer)
        if self.add_failure:
            raise RuntimeError("injected observer registration failure")

    def removeDocumentObserver(self, observer):
        self.remove_calls.append(observer)
        if len(self.remove_calls) <= self.remove_failures:
            raise RuntimeError("injected observer removal failure")
        if observer in self.observers:
            self.observers.remove(observer)


class _ObserverSelection:
    def __init__(self):
        self.clear_calls = []

    def getSelectionEx(self, document_name):
        return ()

    def clearSelection(self, *args):
        self.clear_calls.append(tuple(args))


def _macro_activation_fixture(
    *,
    add_failure=False,
    remove_failures=0,
):
    macro_path = ROOT / "TrackTemplate.FCMacro"
    tree = ast.parse(
        macro_path.read_text(encoding="utf-8"),
        filename=str(macro_path),
    )
    activation_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "activate_transition_editing"
    )
    isolated_tree = ast.Module(body=[activation_node], type_ignores=[])
    ast.fix_missing_locations(isolated_tree)

    document = types.SimpleNamespace(Name="LifecycleTarget")
    intent = types.SimpleNamespace(
        transition_id=TRANSITION_IDS[0],
        end_name="Entry",
    )
    state = types.SimpleNamespace(intent=intent)
    selection = _ObserverSelection()
    app = _ObserverApp(
        document,
        add_failure=add_failure,
        remove_failures=remove_failures,
    )
    gui = types.SimpleNamespace(
        Selection=selection,
        getMainWindow=lambda: None,
    )
    api = types.SimpleNamespace(
        TransitionPreviewSpecification=lambda **_kwargs: object(),
    )
    bootstrap = types.SimpleNamespace(
        require_qualified_runtime=lambda _path: object(),
    )
    adapter = types.SimpleNamespace(
        FREECAD_STATE_JSON_PROPERTY="TransitionStateJson",
        FreeCADTransitionStore=lambda _qualification: object(),
        read_transition_objects=lambda _document: ((object(), state),),
        read_transition_object=lambda _object: state,
        FreeCADTransitionEditPort=lambda *_args: object(),
    )
    attachment_module = types.SimpleNamespace(
        TransitionCoinDocumentAttachmentFixture=lambda *_args, **_kwargs: (
            _Attachment((TRANSITION_IDS[0],))
        ),
    )
    renderer = types.SimpleNamespace(
        TransitionCoinStyle=lambda **_kwargs: object(),
    )
    editor = types.SimpleNamespace(
        SelectedTransition=lambda *_args: object(),
        TransitionParameterEditorDialog=lambda *_args, **_kwargs: _Dialog(
            object()
        ),
    )
    modules = {
        "FreeCAD": app,
        "FreeCADGui": gui,
        "pivy.coin": object(),
        "PySide6.QtWidgets": object(),
        "tracktemplate.adapters.freecad.transition_state": adapter,
        "tracktemplate.presentation.transition_coin_attachment": (
            attachment_module
        ),
        "tracktemplate.presentation.transition_coin": renderer,
        "tracktemplate.ui.transition_parameter_editor": editor,
        "tracktemplate.ui.transition_editing_lifecycle": lifecycle,
    }
    namespace = {
        "_launcher_root": lambda: ROOT,
        "_load_foundation": lambda _root: (api, bootstrap),
        "importlib": types.SimpleNamespace(
            import_module=lambda name: modules[name]
        ),
    }
    exec(compile(isolated_tree, str(macro_path), "exec"), namespace)
    return (
        namespace["activate_transition_editing"],
        document,
        app,
        selection,
    )


def _expect_lifecycle_error(action, code):
    try:
        action()
    except lifecycle.TransitionEditingLifecycleError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected lifecycle error {!r}".format(code))


def _new_lifecycle(
    attachment,
    dialogs,
    factory_calls,
    selection_clear_calls=None,
    cleanup_calls=None,
):
    if selection_clear_calls is None:
        selection_clear_calls = []
    if cleanup_calls is None:
        cleanup_calls = []

    def attachment_factory():
        factory_calls.append(True)
        return attachment

    def dialog_factory(controller):
        dialog = _Dialog(controller)
        dialogs.append(dialog)
        return dialog

    return lifecycle.TransitionEditingLifecycle(
        attachment_factory=attachment_factory,
        selection_reader=lambda: None,
        selection_clearer=lambda: selection_clear_calls.append(True),
        dialog_factory=dialog_factory,
        cleanup_callback=lambda: cleanup_calls.append(True),
    )


def _validate_explicit_once_only_lifecycle():
    attachment = _Attachment()
    dialogs = []
    factory_calls = []
    selection_clear_calls = []
    cleanup_calls = []
    active = _new_lifecycle(
        attachment,
        dialogs,
        factory_calls,
        selection_clear_calls,
        cleanup_calls,
    )

    assert active.state == "inactive"
    assert active.active is False
    assert factory_calls == []
    _expect_lifecycle_error(
        active.show_editor,
        "transition-editing-not-active",
    )

    assert active.activate() == TRANSITION_IDS
    assert active.state == "active"
    assert active.active is True
    assert active.transition_ids == TRANSITION_IDS
    assert active.attachment is attachment
    assert factory_calls == [True]

    _expect_lifecycle_error(
        active.activate,
        "transition-editing-already-active",
    )
    assert factory_calls == [True]

    first_dialog = active.show_editor()
    assert first_dialog is dialogs[0]
    assert first_dialog.show_calls == 1
    assert first_dialog.refresh_calls == 1
    assert active.show_editor() is first_dialog
    assert first_dialog.show_calls == 2
    assert first_dialog.refresh_calls == 2
    assert len(dialogs) == 1

    assert active.deactivate() == TRANSITION_IDS
    assert active.state == "retired"
    assert active.active is False
    assert attachment.dispose_calls == 1
    assert first_dialog.close_calls == 1
    assert selection_clear_calls == [True]
    assert cleanup_calls == [True]
    assert active.transition_ids == ()
    _expect_lifecycle_error(
        active.activate,
        "transition-editing-retired",
    )
    assert active.deactivate() == ()
    assert factory_calls == [True]


def _validate_cleanup_retry_and_failed_activation():
    attachment = _Attachment(failures=1)
    dialogs = []
    active = _new_lifecycle(attachment, dialogs, [])
    active.activate()
    active.show_editor()
    error = _expect_lifecycle_error(
        active.deactivate,
        "transition-editing-cleanup-failed",
    )
    assert "injected attachment cleanup failure" in error.detail
    assert active.state == "cleanup-failed"
    assert active.active is False
    _expect_lifecycle_error(
        active.show_editor,
        "transition-editing-not-active",
    )
    assert active.deactivate() == TRANSITION_IDS
    assert active.state == "retired"
    assert attachment.dispose_calls == 2

    observer_cleanup_calls = []

    def failing_observer_cleanup():
        observer_cleanup_calls.append(True)
        if len(observer_cleanup_calls) == 1:
            raise RuntimeError("injected observer cleanup failure")

    observer_attachment = _Attachment()
    observer_retry = lifecycle.TransitionEditingLifecycle(
        attachment_factory=lambda: observer_attachment,
        selection_reader=lambda: None,
        selection_clearer=lambda: None,
        dialog_factory=lambda controller: _Dialog(controller),
        cleanup_callback=failing_observer_cleanup,
    )
    observer_retry.activate()
    error = _expect_lifecycle_error(
        observer_retry.deactivate,
        "transition-editing-cleanup-failed",
    )
    assert "injected observer cleanup failure" in error.detail
    assert observer_retry.state == "cleanup-failed"
    assert observer_attachment.dispose_calls == 1
    assert observer_retry.deactivate() == TRANSITION_IDS
    assert observer_cleanup_calls == [True, True]
    assert observer_attachment.dispose_calls == 1

    empty = _Attachment(())
    failed = _new_lifecycle(empty, [], [])
    _expect_lifecycle_error(
        failed.activate,
        "transition-editing-activation-failed",
    )
    assert failed.state == "retired"
    assert empty.dispose_calls == 1

    def failing_factory():
        raise RuntimeError("injected activation failure")

    unavailable = lifecycle.TransitionEditingLifecycle(
        attachment_factory=failing_factory,
        selection_reader=lambda: None,
        selection_clearer=lambda: None,
        dialog_factory=lambda controller: _Dialog(controller),
        cleanup_callback=lambda: None,
    )
    error = _expect_lifecycle_error(
        unavailable.activate,
        "transition-editing-activation-failed",
    )
    assert "injected activation failure" in error.detail
    assert unavailable.state == "retired"


def _validate_macro_observer_cleanup_boundaries():
    activate, document, app, selection = _macro_activation_fixture(
        remove_failures=1,
    )
    active = activate(document)
    observer = app.observers[0]
    error = _expect_lifecycle_error(
        lambda: observer.slotStartSaveDocument(document, "target.FCStd"),
        "transition-editing-cleanup-failed",
    )
    assert "injected observer removal failure" in error.detail
    assert active.state == "cleanup-failed"
    assert app.observers == [observer]
    assert app.remove_calls == [observer]
    assert active.deactivate() == (TRANSITION_IDS[0],)
    assert active.state == "retired"
    assert app.observers == []
    assert app.remove_calls == [observer, observer]
    assert selection.clear_calls == [(document.Name,)]

    activate, document, app, selection = _macro_activation_fixture()
    sibling = types.SimpleNamespace(Name="LifecycleSibling")
    selection_by_document = {
        document.Name: ["target-selection"],
        sibling.Name: ["sibling-selection"],
    }
    record_clear_selection = selection.clearSelection

    def clear_selection(document_name):
        record_clear_selection(document_name)
        selection_by_document[document_name] = []

    selection.clearSelection = clear_selection
    active = activate(document)
    assert active.deactivate() == (TRANSITION_IDS[0],)
    assert active.state == "retired"
    assert app.observers == []
    assert selection_by_document[document.Name] == []
    assert selection_by_document[sibling.Name] == ["sibling-selection"]

    activate, document, app, _selection = _macro_activation_fixture(
        add_failure=True,
        remove_failures=1,
    )
    try:
        activate(document)
    except lifecycle.TransitionEditingLifecycleError as error:
        assert error.code == (
            "transition-editing-observer-registration-failed"
        )
        assert isinstance(error.__cause__, RuntimeError)
        assert "injected observer registration failure" in str(
            error.__cause__
        )
        recovery = error.recovery_lifecycle
    else:
        raise AssertionError("Expected observer-registration failure")
    observer = app.observers[0]
    assert recovery.state == "cleanup-failed"
    assert app.remove_calls == [observer]
    assert recovery.deactivate() == (TRANSITION_IDS[0],)
    assert recovery.state == "retired"
    assert app.remove_calls == [observer, observer]
    assert app.observers == []


def _validate_residual_node_confinement():
    view_object = _ViewObject()
    first = viewprovider.TransitionCoinViewProviderFixture(
        view_object,
        _artifact(),
        _style(),
        _FakeCoin,
    )
    selection_root = first.selection_root
    assert selection_root.getName() == (
        viewprovider.TRANSITION_COIN_RESIDUAL_NODE_NAME
    )
    assert first.dispose() is True
    view_object.Proxy = None
    assert selection_root.children == []
    assert view_object.SwitchNode.children == [selection_root]

    error = _expect_state_error(
        lambda: viewprovider.TransitionCoinViewProviderFixture(
            view_object,
            _artifact(),
            _style(),
            _FakeCoin,
        ),
        "coin-viewprovider-residual-conflict",
    )
    assert "close and reopen" in error.detail
    assert view_object.SwitchNode.children == [selection_root]


def _expect_state_error(action, code):
    try:
        action()
    except Exception as error:
        assert getattr(error, "code", None) == code, error
        return error
    raise AssertionError("Expected transition-state error {!r}".format(code))


def _validate_structure_and_explicit_route():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    module = modules["tracktemplate.ui.transition_editing_lifecycle"]
    assert module["layer"] == "ui"
    assert module["warning_signals"] == []
    assert module["imports"] == [
        "tracktemplate.ui.transition_parameter_editor",
    ]
    assert lifecycle.TRANSITION_EDITING_LIFECYCLE_ID.endswith(".v1")

    macro_path = ROOT / "TrackTemplate.FCMacro"
    macro_source = macro_path.read_text(encoding="utf-8")
    macro_tree = ast.parse(macro_source, filename=str(macro_path))
    functions = {
        node.name
        for node in macro_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert "activate_transition_editing" in functions
    assert "tracktemplate.ui.transition_editing_lifecycle" in macro_source
    assert "tracktemplate.presentation.transition_coin_attachment" in (
        macro_source
    )
    assert macro_source.rstrip().endswith("FOUNDATION_RESULT = run_macro()")
    assert macro_source.count("activate_transition_editing(") == 1
    assert "slotStartSaveDocument" in macro_source
    assert "addDocumentObserver" in macro_source
    assert "removeDocumentObserver" in macro_source

    api_source = (ROOT / "tracktemplate" / "api.py").read_text(
        encoding="utf-8"
    )
    assert "TransitionEditingLifecycle" not in api_source
    assert "activate_transition_editing" not in api_source

    gui_proof = (
        ROOT
        / "tests"
        / "freecad_gui_validate_phase5_transition_editing_lifecycle.py"
    )
    runner = (
        ROOT
        / "tools"
        / "freecad_bridge"
        / "run_phase5_transition_viewprovider.py"
    )
    assert gui_proof.is_file()
    runner_source = runner.read_text(encoding="utf-8")
    assert gui_proof.name in runner_source
    assert "LIFECYCLE_SENTINEL" in runner_source
    assert "_validate_lifecycle_payload" in runner_source

    validation = (ROOT / "reference" / "VALIDATION.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT
        / "reference"
        / "history"
        / "phase-closeouts"
        / "PHASE5_CLOSEOUT.md"
    ).read_text(encoding="utf-8")
    assert "explicit B16 lifecycle boundaries" in validation
    assert "save-time retirement and reopen reconstruction" in evidence
    assert "## Explicit B16 transition-editing lifecycle tranche" in evidence
    assert "Phase 5 remains 0/4" in evidence


def validate():
    _validate_explicit_once_only_lifecycle()
    _validate_cleanup_retry_and_failed_activation()
    _validate_macro_observer_cleanup_boundaries()
    _validate_residual_node_confinement()
    _validate_structure_and_explicit_route()
    print("Phase 5 transition-editing lifecycle validation passed")


if __name__ == "__main__":
    validate()
