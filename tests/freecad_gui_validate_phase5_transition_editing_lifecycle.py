"""Exercise the explicit B16 transition-editing lifecycle in real FreeCAD."""

import datetime
import json
import os
import pathlib
import runpy
import sys
import zipfile

import FreeCAD as App
import FreeCADGui as Gui

try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets


ROOT = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
sys.path.insert(0, str(ROOT))

from tools import phase5_transition_representative_workload as workload  # noqa: E402
from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)
from tracktemplate.ui import transition_editing_lifecycle as lifecycle  # noqa: E402


SENTINEL = "TRACKTEMPLATE_PHASE5_TRANSITION_EDITING_LIFECYCLE_GUI="
EXPECTED_IDS = tuple(
    state.intent.transition_id
    for state in workload.initial_states()
)


def _process_gui():
    for _index in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()


def _original_proxy_equal(observed, expected):
    return observed is expected or (
        type(observed) is int
        and type(expected) is int
        and observed == expected
    )


def _stored_snapshot(document):
    return tuple(
        (
            state.intent.transition_id,
            str(obj.Name),
            str(obj.TypeId),
            str(obj.Label),
            str(getattr(obj, adapter.FREECAD_RECORD_TYPE_PROPERTY)),
            str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)),
            tuple(obj.PropertiesList),
            tuple(obj.ViewObject.PropertiesList),
            str(obj.ViewObject.DisplayMode),
            bool(obj.ViewObject.Visibility),
            hasattr(obj, "Shape"),
        )
        for obj, state in adapter.read_transition_objects(document)
    )


def _view_baseline(document):
    return {
        state.intent.transition_id: {
            "display_mode": str(obj.ViewObject.DisplayMode),
            "display_modes": tuple(obj.ViewObject.listDisplayModes()),
            "object": obj,
            "proxy": obj.ViewObject.Proxy,
            "root_children": int(
                obj.ViewObject.RootNode.getNumChildren()
            ),
            "switch_child": int(
                obj.ViewObject.SwitchNode.whichChild.getValue()
            ),
            "switch_children": int(
                obj.ViewObject.SwitchNode.getNumChildren()
            ),
            "view_properties": tuple(obj.ViewObject.PropertiesList),
        }
        for obj, state in adapter.read_transition_objects(document)
    }


def _expect_lifecycle_error(action, code):
    try:
        action()
    except Exception as error:
        assert getattr(error, "code", None) == code, error
        return error
    raise AssertionError("Expected lifecycle error {!r}".format(code))


def _assert_active(document, active, baseline):
    attachment = active.attachment
    assert active.active is True
    assert active.state == "active"
    assert active.transition_ids == EXPECTED_IDS
    assert attachment.attached is True
    assert attachment.attachment_count == len(EXPECTED_IDS)
    assert attachment.transition_ids == EXPECTED_IDS

    node_ids = {}
    caches = {}
    for transition_id in EXPECTED_IDS:
        record = baseline[transition_id]
        obj = record["object"]
        view_object = obj.ViewObject
        proxy = attachment.proxy_for_transition(transition_id)
        cache = attachment.cache_for_transition(transition_id)
        root = proxy.selection_root
        assert view_object.Proxy is proxy
        assert proxy.attached is True
        assert str(root.getName()) == (
            viewprovider.TRANSITION_COIN_RESIDUAL_NODE_NAME
        )
        assert int(root.getNumChildren()) == 1
        assert int(view_object.RootNode.getNumChildren()) == (
            record["root_children"]
        )
        assert int(view_object.SwitchNode.getNumChildren()) == (
            record["switch_children"] + 1
        )
        assert int(view_object.SwitchNode.findChild(root)) == int(
            view_object.SwitchNode.whichChild.getValue()
        )
        assert str(view_object.DisplayMode) == record["display_mode"]
        assert tuple(view_object.PropertiesList) == record[
            "view_properties"
        ]
        assert cache.artifact("preview") is not None
        node_ids[transition_id] = int(root.getNodeId())
        caches[transition_id] = cache
    assert adapter.read_transition_objects(document)
    return node_ids, caches


def _assert_deactivated(document, baseline, caches):
    residual_count = 0
    for transition_id in EXPECTED_IDS:
        record = baseline[transition_id]
        obj = record["object"]
        view_object = obj.ViewObject
        assert _original_proxy_equal(view_object.Proxy, record["proxy"])
        assert str(view_object.DisplayMode) == record["display_mode"]
        assert tuple(view_object.listDisplayModes()) == record[
            "display_modes"
        ]
        assert tuple(view_object.PropertiesList) == record[
            "view_properties"
        ]
        assert int(view_object.RootNode.getNumChildren()) == (
            record["root_children"]
        )
        assert int(view_object.SwitchNode.getNumChildren()) == (
            record["switch_children"] + 1
        )
        assert int(view_object.SwitchNode.whichChild.getValue()) == (
            record["switch_child"]
        )
        names = []
        for index in range(int(view_object.SwitchNode.getNumChildren())):
            child = view_object.SwitchNode.getChild(index)
            name = str(child.getName())
            names.append(name)
            if name == viewprovider.TRANSITION_COIN_RESIDUAL_NODE_NAME:
                residual_count += 1
                assert int(child.getNumChildren()) == 0
        assert names.count(
            viewprovider.TRANSITION_COIN_RESIDUAL_NODE_NAME
        ) == 1
        assert caches[transition_id].artifact("preview") is None
    assert len(Gui.Selection.getSelectionEx(document.Name)) == 0
    return residual_count


def _select_transition(document, active, transition_id):
    obj = next(
        obj
        for obj, state in adapter.read_transition_objects(document)
        if state.intent.transition_id == transition_id
    )
    proxy = active.attachment.proxy_for_transition(transition_id)
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(
        str(document.Name),
        str(obj.Name),
        proxy.element_name,
    )
    _process_gui()
    return obj, proxy


def _capture_owner_view(document, dialog, run_directory):
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    _process_gui()
    scene_path = run_directory / "explicit-lifecycle-scene.png"
    editor_path = run_directory / "explicit-lifecycle-editor.png"
    view.saveImage(str(scene_path), 1000, 700, "Current")
    pixmap = dialog.dialog.grab()
    assert not pixmap.isNull()
    assert pixmap.save(str(editor_path))
    assert scene_path.is_file() and scene_path.stat().st_size > 0
    assert editor_path.is_file() and editor_path.stat().st_size > 0
    return scene_path, editor_path


def validate():
    if App.listDocuments():
        raise RuntimeError(
            "The lifecycle GUI proof requires an empty isolated session"
        )

    qualification = bootstrap.require_qualified_runtime(
        ROOT
        / "reference"
        / "contracts"
        / "phase1-compatibility.json"
    )
    macro = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
    activate = macro["activate_transition_editing"]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_directory = (
        ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "phase5-transition-lifecycle-runs"
        / stamp
    )
    run_directory.mkdir(parents=True)
    saved_path = run_directory / "entry-exit-lifecycle.FCStd"

    document = None
    active = None
    sibling = None
    reopened = None
    reopened_active = None
    try:
        document = App.newDocument("Phase5TransitionEditingLifecycle")
        document.UndoMode = 1
        store = adapter.FreeCADTransitionStore(qualification)
        store.create_many(document, workload.initial_states())
        document.recompute()
        document.clearUndos()
        baseline = _view_baseline(document)
        stored_before = _stored_snapshot(document)
        assert tuple(baseline) == EXPECTED_IDS
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0

        active = activate(document)
        initial_node_ids, caches = _assert_active(
            document,
            active,
            baseline,
        )
        assert _stored_snapshot(document) == stored_before
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0

        _expect_lifecycle_error(
            active.activate,
            "transition-editing-already-active",
        )
        children_before_duplicate = tuple(
            int(record["object"].ViewObject.SwitchNode.getNumChildren())
            for record in baseline.values()
        )
        duplicate_error = _expect_lifecycle_error(
            lambda: activate(document),
            "transition-editing-activation-failed",
        )
        assert "already has a non-default ViewProvider" in (
            duplicate_error.detail
        )
        assert tuple(
            int(record["object"].ViewObject.SwitchNode.getNumChildren())
            for record in baseline.values()
        ) == children_before_duplicate

        selected_id = EXPECTED_IDS[1]
        selected_object, _selected_proxy = _select_transition(
            document,
            active,
            selected_id,
        )
        dialog = active.show_editor()
        _process_gui()
        assert dialog.dialog.isVisible()
        assert dialog.dialog.parent() is Gui.getMainWindow()
        assert dialog.selected_transition_id == selected_id
        assert dialog.length_edit.text() == "420.000"
        scene_path, editor_path = _capture_owner_view(
            document,
            dialog,
            run_directory,
        )

        initial_selected_state = adapter.read_transition_object(
            selected_object
        )
        dialog.length_edit.setText("360.000")
        dialog.apply_button.click()
        _process_gui()
        edited_state = adapter.read_transition_object(selected_object)
        assert dialog.last_result is not None
        assert dialog.last_result.changed is True
        assert edited_state == dialog.last_result.state
        assert int(document.UndoCount) == 1
        document.undo()
        _process_gui()
        assert adapter.read_transition_object(selected_object) == (
            initial_selected_state
        )
        document.redo()
        _process_gui()
        assert adapter.read_transition_object(selected_object) == edited_state
        document.undo()
        _process_gui()
        assert adapter.read_transition_object(selected_object) == (
            initial_selected_state
        )
        document.clearUndos()
        assert _stored_snapshot(document) == stored_before

        sibling = App.newDocument("Phase5TransitionEditingSibling")
        sibling_object = sibling.addObject(
            "App::FeaturePython",
            "SiblingSelection",
        )
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(
            str(document.Name),
            str(selected_object.Name),
            _selected_proxy.element_name,
        )
        Gui.Selection.addSelection(
            str(sibling.Name),
            str(sibling_object.Name),
        )
        App.setActiveDocument(str(sibling.Name))
        _process_gui()
        assert len(Gui.Selection.getSelectionEx(document.Name)) == 1
        assert len(Gui.Selection.getSelectionEx(sibling.Name)) == 1

        document.saveAs(str(saved_path))
        assert saved_path.is_file() and saved_path.stat().st_size > 0
        assert active.state == "retired"
        residual_count = _assert_deactivated(
            document,
            baseline,
            caches,
        )
        active = None
        assert residual_count == len(EXPECTED_IDS)
        assert _stored_snapshot(document) == stored_before
        assert len(Gui.Selection.getSelectionEx(sibling.Name)) == 1
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0
        App.closeDocument(str(sibling.Name))
        sibling = None
        App.setActiveDocument(str(document.Name))
        _process_gui()

        children_before_residual_retry = tuple(
            int(record["object"].ViewObject.SwitchNode.getNumChildren())
            for record in baseline.values()
        )
        residual_error = _expect_lifecycle_error(
            lambda: activate(document),
            "transition-editing-activation-failed",
        )
        assert "coin-viewprovider-residual-conflict" in residual_error.detail
        assert tuple(
            int(record["object"].ViewObject.SwitchNode.getNumChildren())
            for record in baseline.values()
        ) == children_before_residual_retry

        with zipfile.ZipFile(saved_path) as archive:
            persisted = b"\n".join(
                archive.read(name)
                for name in archive.namelist()
            )
        for marker in (
            b"TransitionCoinDocumentAttachmentFixture",
            b"TransitionCoinViewProviderFixture",
            b"TransitionEditingLifecycle",
            b"TrackTemplateTransitionPreviewResidualV1",
        ):
            assert marker not in persisted

        document_name = document.Name
        App.closeDocument(document_name)
        document = None
        _process_gui()
        reopened = App.openDocument(str(saved_path))
        reopened.UndoMode = 1
        _process_gui()
        assert tuple(
            state.intent.transition_id
            for _obj, state in adapter.read_transition_objects(reopened)
        ) == EXPECTED_IDS
        reopened_stored_before = _stored_snapshot(reopened)
        reopened_baseline = _view_baseline(reopened)
        reopened_active = activate(reopened)
        reopened_node_ids, reopened_caches = _assert_active(
            reopened,
            reopened_active,
            reopened_baseline,
        )
        assert all(
            reopened_node_ids[identity] != initial_node_ids[identity]
            for identity in EXPECTED_IDS
        )
        reopened_object, _reopened_proxy = _select_transition(
            reopened,
            reopened_active,
            EXPECTED_IDS[1],
        )
        reopened_dialog = reopened_active.show_editor()
        _process_gui()
        assert reopened_dialog.dialog.isVisible()
        assert reopened_dialog.selected_transition_id == EXPECTED_IDS[1]
        assert reopened_dialog.length_edit.text() == "420.000"
        assert adapter.read_transition_object(reopened_object) == (
            workload.initial_states()[1]
        )
        assert _stored_snapshot(reopened) == reopened_stored_before

        assert reopened_active.deactivate() == EXPECTED_IDS
        reopened_residual_count = _assert_deactivated(
            reopened,
            reopened_baseline,
            reopened_caches,
        )
        reopened_active = None
        assert reopened_residual_count == len(EXPECTED_IDS)
        assert _stored_snapshot(reopened) == reopened_stored_before
        reopened_name = str(reopened.Name)
        App.closeDocument(reopened_name)
        reopened = None
        _process_gui()
        assert reopened_name not in App.listDocuments()

        result = {
            "active_children_cleared": True,
            "attachment_count": len(EXPECTED_IDS),
            "composition_boundary": (
                lifecycle.TRANSITION_EDITING_LIFECYCLE_ID
            ),
            "caches_discarded": True,
            "canonical_restored_before_save": True,
            "deactivated": True,
            "deactivated_then_closed": True,
            "display_mode_property_unchanged": True,
            "duplicate_active_blocked": True,
            "duplicate_invocation_blocked": True,
            "editor_image": str(editor_path),
            "editor_visible": True,
            "exact_qualified_profile": qualification[
                "compatibility_evaluation"
            ]["matched_profile_id"],
            "explicit_activation": True,
            "freecad_version": ".".join(App.Version()[:3]),
            "part_shape_created": False,
            "proxies_restored": True,
            "reopened": True,
            "reopened_attachment_count": len(EXPECTED_IDS),
            "reopened_deactivated": True,
            "reopened_editor_length": "420.000",
            "reopened_editor_selected_transition": EXPECTED_IDS[1],
            "reopened_new_scene_nodes": True,
            "residual_empty_child_count": residual_count,
            "residual_not_accumulated": True,
            "same_document_reactivation_blocked": True,
            "save_auto_deactivated": True,
            "scene_image": str(scene_path),
            "schema_unchanged": True,
            "selection_cleared": True,
            "sibling_selection_preserved": True,
            "stored_state_unchanged_after_deactivation": True,
            "switch_selection_restored": True,
            "transition_ids": EXPECTED_IDS,
            "undo_redo_preserved": True,
        }
    finally:
        if active is not None and active.state in (
            "active",
            "cleanup-failed",
        ):
            active.deactivate()
        if reopened_active is not None and reopened_active.state in (
            "active",
            "cleanup-failed",
        ):
            reopened_active.deactivate()
        Gui.Selection.clearSelection()
        for document_name in list(App.listDocuments()):
            App.closeDocument(document_name)
        _process_gui()

    result["remaining_documents"] = sorted(App.listDocuments())
    print(
        SENTINEL
        + json.dumps(result, sort_keys=True, separators=(",", ":")),
        flush=True,
    )


validate()
