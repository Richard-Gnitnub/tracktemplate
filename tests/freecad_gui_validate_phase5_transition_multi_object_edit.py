"""Exercise representative multi-object selection and editing in FreeCAD."""

import datetime
import functools
import json
import os
import pathlib
import sys
import zipfile

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin

try:
    from PySide6 import (
        QtCore,
        QtGui,
        QtOpenGLWidgets,
        QtTest,
        QtWidgets,
    )
    _OpenGLWidget = QtOpenGLWidgets.QOpenGLWidget
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtTest, QtWidgets
        _OpenGLWidget = QtWidgets.QOpenGLWidget
    except ImportError:
        from PySide import QtCore, QtGui, QtOpenGL, QtTest
        QtWidgets = QtGui
        _OpenGLWidget = QtOpenGL.QGLWidget


ROOT = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
sys.path.insert(0, str(ROOT))

from tests.phase5_transition_coin_gui_harness import (  # noqa: E402
    _ObservedTransitionCoinViewProviderFixture,
    _SelectionObserver,
    _process_gui as _shared_process_gui,
)
from tools import phase5_transition_representative_workload as workload  # noqa: E402
from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_attachment as attachment,
)
from tracktemplate.ui import transition_parameter_editor as editor  # noqa: E402


_process_gui = functools.partial(
    _shared_process_gui,
    Gui.updateGui,
    QtWidgets.QApplication.processEvents,
)


SENTINEL = "TRACKTEMPLATE_PHASE5_MULTI_OBJECT_EDIT_GUI="
FAMILY_ID = "plain-line-spacing-matched-transition-intent"
SELECTED_END = "Exit"
EXPECTED_ACTIVE_NODE_COUNT = 14


def _red_pixel_count(path):
    image = QtGui.QImage(str(path))
    if image.isNull():
        raise RuntimeError("FreeCAD created an unreadable GUI screenshot")
    count = 0
    for y_pos in range(image.height()):
        for x_pos in range(image.width()):
            colour = image.pixelColor(x_pos, y_pos)
            red = colour.red()
            green = colour.green()
            blue = colour.blue()
            if red >= 160 and red >= green * 2 and red >= blue * 2:
                count += 1
    return count


def _visible_centreline_target(view, target_record):
    main_window = Gui.getMainWindow()
    mdi_area = main_window.findChild(QtWidgets.QMdiArea)
    subwindow = None if mdi_area is None else mdi_area.activeSubWindow()
    if subwindow is None:
        raise RuntimeError("FreeCAD has no active 3D-view subwindow")
    view_widget = subwindow.widget()
    if view_widget is None or not view_widget.isVisible():
        raise RuntimeError("FreeCAD has no visible 3D-view widget")

    target_object = target_record["object"]
    target_proxy = target_record["proxy"]
    polyline = target_record[
        "initial_artifact"
    ].payload.polylines[0]
    viewport_width, viewport_height = (
        int(value)
        for value in view.getSize()
    )
    unique_hits = []
    segments = tuple(zip(
        polyline.points[:-1],
        polyline.points[1:],
    ))
    for start, finish in segments:
        point_x_mm = (start.x_mm + finish.x_mm) / 2.0
        point_y_mm = (start.y_mm + finish.y_mm) / 2.0
        viewport_point = tuple(
            int(value)
            for value in view.getPointOnViewport(
                App.Vector(point_x_mm, point_y_mm, 0.0)
            )
        )
        hit_records = tuple(
            view.getObjectsInfo(viewport_point) or ()
        )
        hit_objects = {
            str(record.get("Object", ""))
            for record in hit_records
            if record.get("Object")
        }
        if (
            len(hit_records) == 1
            and hit_objects == {str(target_object.Name)}
            and hit_records[0].get("Component")
            == target_proxy.element_name
        ):
            edge_margin = min(
                viewport_point[0],
                viewport_width - 1 - viewport_point[0],
                viewport_point[1],
                viewport_height - 1 - viewport_point[1],
            )
            unique_hits.append((
                edge_margin,
                viewport_point,
                hit_records,
                (point_x_mm, point_y_mm),
            ))
    if not unique_hits:
        raise RuntimeError(
            "the Exit preview has no uniquely pickable projected point"
        )
    (
        edge_margin,
        viewport_point,
        hit_records,
        preview_point,
    ) = max(unique_hits, key=lambda candidate: candidate[0])

    candidates = list(view_widget.findChildren(_OpenGLWidget))
    if isinstance(view_widget, _OpenGLWidget):
        candidates.append(view_widget)
    targets = [
        candidate
        for candidate in candidates
        if candidate.isVisible()
    ]
    if len(targets) != 1:
        raise RuntimeError(
            "expected one visible OpenGL widget; found {}".format(
                len(targets)
            )
        )
    target = targets[0]
    target_point = QtCore.QPoint(
        round(
            viewport_point[0]
            * target.width()
            / viewport_width
        ),
        round(
            (viewport_height - 1 - viewport_point[1])
            * target.height()
            / viewport_height
        ),
    )
    if not target.rect().contains(target_point):
        raise RuntimeError(
            "the projected Exit point is outside the OpenGL widget"
        )
    main_window.activateWindow()
    mdi_area.setActiveSubWindow(subwindow)
    target.setFocus()
    QtTest.QTest.mouseMove(target, target_point)
    _process_gui()
    cursor_point = tuple(int(value) for value in view.getCursorPos())
    if any(
        abs(observed - expected) > 2
        for observed, expected in zip(cursor_point, viewport_point)
    ):
        raise RuntimeError(
            "Qt/Coin pointer coordinates did not reconcile: {!r} != {!r}".format(
                cursor_point,
                viewport_point,
            )
        )
    QtTest.QTest.mouseMove(target, QtCore.QPoint(2, 2))
    _process_gui()
    return target, target_point, {
        "class_name": target.metaObject().className(),
        "cursor_point": list(cursor_point),
        "edge_margin_pixels": edge_margin,
        "locator": "projected-canonical-point-read-only-hit-test",
        "local_point": [target_point.x(), target_point.y()],
        "object_name": target.objectName(),
        "preview_point_mm": [
            preview_point[0],
            preview_point[1],
        ],
        "unique_hit_count": len(hit_records),
        "viewport_point": list(viewport_point),
    }


class _PreviewCoordinator:
    def __init__(self, specification):
        self.cache = api.TransitionDerivedCache()
        self.specification = specification
        self.regeneration_count = 0
        self.request_count = 0
        self.reuse_count = 0
        self.failure_state = None
        self.failure_remaining = 0

    def artifact_for_state(self, state):
        previous = self.cache.artifact("preview")
        artifact = api.regenerate_transition_preview(
            self.cache,
            state,
            self.specification,
        )
        self.request_count += 1
        if artifact is previous:
            self.reuse_count += 1
        else:
            self.regeneration_count += 1
        if (
            self.failure_remaining
            and state == self.failure_state
        ):
            self.failure_remaining -= 1
            raise RuntimeError(
                "injected representative multi-object refresh failure"
            )
        return artifact

    def counters(self):
        return {
            "regenerations": self.regeneration_count,
            "requests": self.request_count,
            "reuses": self.reuse_count,
        }


def _count_coin_nodes(roots):
    seen = set()
    pending = list(roots)
    while pending:
        node = pending.pop()
        node_id = int(node.getNodeId())
        if node_id in seen:
            continue
        seen.add(node_id)
        try:
            child_count = int(node.getNumChildren())
        except Exception:
            child_count = 0
        for child_index in range(child_count):
            pending.append(node.getChild(child_index))
    return len(seen)


def _mapping(record):
    proxy = record["proxy"]
    selection = proxy.selection_for_element(proxy.element_name)
    state = adapter.read_transition_object(record["object"])
    return {
        "domain_id": selection.domain_id,
        "element_name": proxy.element_name,
        "end_name": state.intent.end_name,
        "object_name": str(record["object"].Name),
        "transition_id": state.intent.transition_id,
        "visual_id": selection.visual_id,
    }


def _snapshot(document, records):
    roots = [record["proxy"].selection_root for record in records]
    objects = tuple(document.Objects)
    snapshot = {
        "active_coin_scene_node_count": _count_coin_nodes(roots),
        "document_object_count": len(objects),
        "logical_layer_count": sum(
            int(root.getChild(0).getNumChildren())
            for root in roots
        ),
        "mappings": tuple(
            _mapping(record)
            for record in records
        ),
        "part_shape_count": sum(
            "Shape" in tuple(obj.PropertiesList)
            for obj in objects
        ),
        "proxy_count": len(records),
    }
    assert snapshot["document_object_count"] == workload.OBJECT_COUNT
    assert snapshot["logical_layer_count"] == workload.OBJECT_COUNT
    assert (
        snapshot["active_coin_scene_node_count"]
        == EXPECTED_ACTIVE_NODE_COUNT
    )
    assert snapshot["part_shape_count"] == 0
    assert snapshot["proxy_count"] == workload.OBJECT_COUNT
    for record in records:
        obj = record["object"]
        proxy = record["proxy"]
        assert obj.TypeId == "App::FeaturePython"
        assert obj.Proxy is None
        assert tuple(obj.PropertiesList) == record["object_properties"]
        assert tuple(obj.ViewObject.PropertiesList) == (
            record["view_properties"]
        )
        assert proxy.attached is True
        assert int(proxy.selection_root.getNumChildren()) == 1
        assert (
            int(obj.ViewObject.RootNode.getNumChildren())
            == record["root_child_count_before"]
        )
        assert (
            int(obj.ViewObject.SwitchNode.getNumChildren())
            == record["switch_child_count_before"] + 1
        )
    return snapshot


def _cache_counters(records):
    return {
        record["initial_state"].intent.end_name: (
            record["coordinator"].counters()
        )
        for record in records
    }


def _assert_record_unchanged(
    record,
    expected_state,
    expected_signature,
    expected_payload,
    expected_artifact,
    preview_request,
):
    obj = record["object"]
    proxy = record["proxy"]
    cache = record["coordinator"].cache
    checks = {
        "cache_artifact": (
            cache.artifact("preview") is expected_artifact
        ),
        "cache_status": (
            cache.status(
                expected_state,
                preview_request,
            )
            == "current"
        ),
        "canonical_state": (
            adapter.read_transition_object(obj) == expected_state
        ),
        "source_signature": (
            proxy.source_signature == expected_signature
        ),
        "stored_payload": (
            str(
                getattr(
                    obj,
                    adapter.FREECAD_STATE_JSON_PROPERTY,
                )
            )
            == expected_payload
        ),
    }
    assert all(checks.values()), checks
    return checks


def _counter_delta(before, after, end_name):
    return {
        key: after[end_name][key] - before[end_name][key]
        for key in ("regenerations", "requests", "reuses")
    }


def _assert_only_selected_regenerated(before, after, expected):
    assert _counter_delta(
        before,
        after,
        SELECTED_END,
    ) == expected
    assert _counter_delta(
        before,
        after,
        "Entry",
    ) == {
        "regenerations": 0,
        "requests": 0,
        "reuses": 0,
    }


def _selected_transition(document, store):
    selected = tuple(Gui.Selection.getSelectionEx(document.Name))
    if len(selected) != 1:
        return None
    selected_record = selected[0]
    selected_object = selected_record.Object
    subelements = tuple(selected_record.SubElementNames)
    if len(subelements) != 1:
        return None
    proxy = selected_object.ViewObject.Proxy
    selection_for_element = getattr(proxy, "selection_for_element", None)
    if not callable(selection_for_element):
        return None
    mapping = selection_for_element(subelements[0])
    if mapping is None:
        return None
    try:
        state = adapter.read_transition_object(selected_object)
    except adapter.TransitionDocumentError:
        return None
    if mapping.domain_id != state.intent.transition_id:
        return None
    return editor.SelectedTransition(
        state,
        adapter.FreeCADTransitionEditPort(
            store,
            document,
            selected_object,
            proxy,
        ),
    )


def _replace_line_edit_text(line_edit, text):
    line_edit.setFocus()
    QtTest.QTest.mouseClick(line_edit, QtCore.Qt.LeftButton)
    QtTest.QTest.keyClick(
        line_edit,
        QtCore.Qt.Key_A,
        QtCore.Qt.ControlModifier,
    )
    QtTest.QTest.keyClicks(line_edit, text)
    _process_gui()
    assert line_edit.text() == text


def _capture_dialog(dialog, path):
    _process_gui()
    assert dialog.isVisible()
    pixmap = dialog.grab()
    assert not pixmap.isNull()
    assert pixmap.save(str(path))
    assert path.is_file()
    assert path.stat().st_size > 0


def _build_fixture(qualification):
    document = App.newDocument("Phase5TransitionMultiObjectEdit")
    document.UndoMode = 1
    store = adapter.FreeCADTransitionStore(qualification)
    states = workload.initial_states()
    assert len(states) == workload.OBJECT_COUNT
    objects = store.create_many(document, states)
    specification = api.TransitionPreviewSpecification(
        segment_count=workload.PREVIEW_SEGMENT_COUNT
    )
    records = []
    for obj, state in zip(objects, states):
        coordinator = _PreviewCoordinator(specification)
        artifact = coordinator.artifact_for_state(state)
        if state.intent.end_name == SELECTED_END:
            colour = (0.9, 0.05, 0.02)
            line_width = 8.0
        else:
            colour = (0.05, 0.2, 0.9)
            line_width = 3.0
        record = {
            "coordinator": coordinator,
            "display_modes_before": tuple(
                obj.ViewObject.listDisplayModes()
            ),
            "initial_artifact": artifact,
            "initial_state": state,
            "object": obj,
            "object_properties": tuple(obj.PropertiesList),
            "root_child_count_before": int(
                obj.ViewObject.RootNode.getNumChildren()
            ),
            "switch_child_count_before": int(
                obj.ViewObject.SwitchNode.getNumChildren()
            ),
            "view_properties": tuple(obj.ViewObject.PropertiesList),
        }
        proxy = _ObservedTransitionCoinViewProviderFixture(
            obj.ViewObject,
            artifact,
            renderer.TransitionCoinStyle(
                line_color_rgb=colour,
                line_width=line_width,
            ),
            coin,
            state_reader=adapter.read_transition_object,
            artifact_for_state=coordinator.artifact_for_state,
            source_property_name=adapter.FREECAD_STATE_JSON_PROPERTY,
        )
        obj.ViewObject.DisplayMode = proxy.display_mode
        record["proxy"] = proxy
        records.append(record)

    document.recompute()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    _process_gui()
    return document, store, records, view


def _dispose_records(records):
    disposed = 0
    discarded_caches = 0
    for record in records:
        proxy = record["proxy"]
        if proxy.attached and proxy.dispose():
            disposed += 1
        record["object"].ViewObject.Proxy = None
        if record["coordinator"].cache.discard(
            "preview"
        ) == ("preview",):
            discarded_caches += 1
        view_object = record["object"].ViewObject
        assert tuple(view_object.listDisplayModes()) == (
            record["display_modes_before"]
        )
        assert int(view_object.RootNode.getNumChildren()) == (
            record["root_child_count_before"]
        )
        assert int(view_object.SwitchNode.getNumChildren()) == (
            record["switch_child_count_before"] + 1
        )
    return {
        "discarded_cache_count": discarded_caches,
        "disposed_proxy_count": disposed,
    }


def _stored_snapshot(document, object_states):
    return (
        int(document.UndoCount),
        int(document.RedoCount),
        len(document.Objects),
        tuple(
            (
                state.intent.transition_id,
                str(obj.Name),
                str(obj.TypeId),
                str(
                    getattr(
                        obj,
                        adapter.FREECAD_STATE_JSON_PROPERTY,
                    )
                ),
                tuple(obj.PropertiesList),
                tuple(obj.ViewObject.PropertiesList),
                hasattr(obj, "Shape"),
            )
            for obj, state in object_states
        ),
    )


def _view_snapshot(object_states):
    return tuple(
        (
            state.intent.transition_id,
            obj.ViewObject.Proxy,
            tuple(obj.ViewObject.listDisplayModes()),
            int(obj.ViewObject.RootNode.getNumChildren()),
            int(obj.ViewObject.SwitchNode.getNumChildren()),
        )
        for obj, state in object_states
    )


def _exercise_reopened_attachment(
    document,
    records,
    expected_mappings,
    specification,
):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    run_directory = (
        ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "phase5-viewprovider-runs"
        / stamp
    )
    run_directory.mkdir(parents=True)
    saved_document_path = (
        run_directory / "representative-entry-exit-reopen.FCStd"
    )
    reopened_image_path = (
        run_directory / "representative-entry-exit-reopened.png"
    )

    expected_object_states = adapter.read_transition_objects(document)
    expected_order = tuple(
        state.intent.transition_id
        for _obj, state in expected_object_states
    )
    expected_by_identity = {
        record["initial_state"].intent.transition_id: record
        for record in records
    }
    expected_object_names = {
        identity: str(record["object"].Name)
        for identity, record in expected_by_identity.items()
    }
    original_caches = {
        identity: record["coordinator"].cache
        for identity, record in expected_by_identity.items()
    }
    original_artifacts = {
        identity: cache.artifact("preview")
        for identity, cache in original_caches.items()
    }
    assert all(
        artifact is not None
        for artifact in original_artifacts.values()
    )

    manual_cleanup = _dispose_records(records)
    document.recompute()
    assert adapter.read_transition_objects(document) == (
        expected_object_states
    )
    document.saveAs(str(saved_document_path))
    with zipfile.ZipFile(saved_document_path) as archive:
        persisted_archive = b"\n".join(
            archive.read(name)
            for name in archive.namelist()
        )
    for transient_marker in (
        b"TransitionCoinDocumentAttachmentFixture",
        b"TransitionCoinViewProviderFixture",
        b"_ObservedTransitionCoinViewProviderFixture",
        b"TransitionDerivedCache",
        b"phase5_transition_coin_gui_harness",
        b"transition_coin_attachment",
        b"transition_coin_viewprovider",
    ):
        assert transient_marker not in persisted_archive

    original_document_name = str(document.Name)
    App.closeDocument(original_document_name)
    _process_gui()
    reopened_document = App.openDocument(str(saved_document_path))
    _process_gui()
    document_attachment = None
    try:
        reopened_object_states = adapter.read_transition_objects(
            reopened_document
        )
        assert tuple(
            state.intent.transition_id
            for _obj, state in reopened_object_states
        ) == expected_order
        assert tuple(
            state
            for _obj, state in reopened_object_states
        ) == tuple(
            state
            for _obj, state in expected_object_states
        )
        for obj, state in reopened_object_states:
            original_record = expected_by_identity[
                state.intent.transition_id
            ]
            assert str(obj.Name) == expected_object_names[
                state.intent.transition_id
            ]
            assert obj.TypeId == "App::FeaturePython"
            assert tuple(obj.PropertiesList) == (
                original_record["object_properties"]
            )
            assert tuple(obj.ViewObject.PropertiesList) == (
                original_record["view_properties"]
            )
            assert tuple(obj.ViewObject.listDisplayModes()) == (
                original_record["display_modes_before"]
            )
            assert int(
                obj.ViewObject.RootNode.getNumChildren()
            ) == original_record["root_child_count_before"]
            assert int(
                obj.ViewObject.SwitchNode.getNumChildren()
            ) == original_record["switch_child_count_before"]
            assert obj.Proxy is None
            assert isinstance(
                obj.ViewObject.Proxy,
                (int, type(None)),
            )
            assert not hasattr(obj, "Shape")

        stored_before_attachment = _stored_snapshot(
            reopened_document,
            reopened_object_states,
        )
        view_before_attachment = _view_snapshot(
            reopened_object_states
        )
        original_host_proxies = {
            state.intent.transition_id: obj.ViewObject.Proxy
            for obj, state in reopened_object_states
        }

        document_attachment = (
            attachment.TransitionCoinDocumentAttachmentFixture(
                reopened_document,
                record_loader=adapter.read_transition_objects,
                state_reader=adapter.read_transition_object,
                source_property_name=(
                    adapter.FREECAD_STATE_JSON_PROPERTY
                ),
                specification=specification,
                style=renderer.TransitionCoinStyle(
                    line_color_rgb=(0.9, 0.05, 0.02),
                    line_width=6.0,
                ),
                coin_module=coin,
            )
        )
        assert document_attachment.attached is True
        assert document_attachment.attachment_count == (
            workload.OBJECT_COUNT
        )
        assert document_attachment.transition_ids == expected_order

        attached_records = []
        attached_caches = {}
        attached_artifacts = {}
        attached_roots = {}
        for obj, state in reopened_object_states:
            identity = state.intent.transition_id
            proxy = document_attachment.proxy_for_transition(
                identity
            )
            cache = document_attachment.cache_for_transition(
                identity
            )
            artifact = cache.artifact("preview")
            assert cache is not original_caches[identity]
            assert artifact is not None
            assert artifact is not original_artifacts[identity]
            assert artifact.source_signature == (
                original_artifacts[identity].source_signature
            )
            assert artifact.payload == (
                original_artifacts[identity].payload
            )
            assert cache.status(
                state,
                specification.derived_request(),
            ) == "current"
            attached_records.append({
                "object": obj,
                "proxy": proxy,
            })
            attached_caches[identity] = cache
            attached_artifacts[identity] = artifact
            attached_roots[identity] = proxy.selection_root

        reopened_mappings = tuple(
            _mapping(record)
            for record in attached_records
        )
        assert reopened_mappings == expected_mappings
        assert _count_coin_nodes(
            attached_roots.values()
        ) == EXPECTED_ACTIVE_NODE_COUNT

        by_end = {
            state.intent.end_name: state.intent.transition_id
            for _obj, state in reopened_object_states
        }
        refreshed_identity = by_end[SELECTED_END]
        sibling_identity = by_end["Entry"]
        sibling_proxy = document_attachment.proxy_for_transition(
            sibling_identity
        )
        sibling_source_signature = sibling_proxy.source_signature
        sibling_selection_root = sibling_proxy.selection_root
        assert attached_caches[sibling_identity].discard(
            "preview"
        ) == ("preview",)
        assert attached_caches[sibling_identity].artifact(
            "preview"
        ) is None
        refreshed = document_attachment.refresh_transition(
            refreshed_identity
        )
        assert refreshed is False
        assert attached_caches[refreshed_identity].artifact(
            "preview"
        ) is attached_artifacts[refreshed_identity]
        assert attached_caches[sibling_identity].artifact(
            "preview"
        ) is None
        assert sibling_proxy.source_signature == (
            sibling_source_signature
        )
        assert sibling_proxy.selection_root is sibling_selection_root
        assert tuple(
            _mapping(record)
            for record in attached_records
        ) == expected_mappings
        assert _stored_snapshot(
            reopened_document,
            reopened_object_states,
        ) == stored_before_attachment

        for record in attached_records:
            view_object = record["object"].ViewObject
            mode_index = tuple(
                view_object.listDisplayModes()
            ).index(record["proxy"].display_mode)
            view_object.SwitchNode.whichChild.setValue(mode_index)
        reopened_document.recompute()
        view = Gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        view.redraw()
        _process_gui()
        view.saveImage(
            str(reopened_image_path),
            1000,
            700,
            "Current",
        )
        visible_red_pixels = _red_pixel_count(
            reopened_image_path
        )
        assert visible_red_pixels >= 100

        dispose_result = document_attachment.dispose()
        assert dispose_result == expected_order
        assert document_attachment.attached is False
        assert all(
            int(root.getNumChildren()) == 0
            for root in attached_roots.values()
        )
        assert all(
            cache.artifact("preview") is None
            for cache in attached_caches.values()
        )
        assert all(
            obj.ViewObject.Proxy
            == original_host_proxies[state.intent.transition_id]
            for obj, state in reopened_object_states
        )
        for obj, state in reopened_object_states:
            original_view = next(
                entry
                for entry in view_before_attachment
                if entry[0] == state.intent.transition_id
            )
            assert tuple(obj.ViewObject.listDisplayModes()) == (
                original_view[2]
            )
            assert int(
                obj.ViewObject.RootNode.getNumChildren()
            ) == original_view[3]
            assert int(
                obj.ViewObject.SwitchNode.getNumChildren()
            ) == original_view[4] + 1
        assert _stored_snapshot(
            reopened_document,
            reopened_object_states,
        ) == stored_before_attachment

        object_count_before_close = len(
            reopened_document.Objects
        )
        result = {
            "active_coin_scene_node_count": (
                EXPECTED_ACTIVE_NODE_COUNT
            ),
            "all_caches_discarded": True,
            "all_host_proxies_restored": True,
            "all_selection_roots_cleared": True,
            "attachment_boundary": (
                attachment.TRANSITION_COIN_DOCUMENT_ATTACHMENT_FIXTURE_ID
            ),
            "attachment_count": workload.OBJECT_COUNT,
            "attachment_order": expected_order,
            "cache_is_new_count": workload.OBJECT_COUNT,
            "derived_state_persisted": False,
            "disposed": True,
            "dispose_returned_transition_ids": dispose_result,
            "document_object_count": workload.OBJECT_COUNT,
            "empty_switch_children_retained": (
                workload.OBJECT_COUNT
            ),
            "explicit_post_open": True,
            "history_delta": 0,
            "independent_refresh": True,
            "logical_layer_count": workload.OBJECT_COUNT,
            "part_shape_created": False,
            "preview_equivalent_count": workload.OBJECT_COUNT,
            "reopened_image": str(reopened_image_path),
            "save_route_exercised": True,
            "schema_unchanged": True,
            "selection_mappings_preserved": True,
            "sibling_cache_request_trap": "remained-missing",
            "stored_state_unchanged": True,
            "visible_red_pixels": visible_red_pixels,
        }
    finally:
        if (
            document_attachment is not None
            and document_attachment.attached
        ):
            document_attachment.dispose()
        if reopened_document.Name in App.listDocuments():
            App.closeDocument(reopened_document.Name)
        _process_gui()

    cleanup = {
        **manual_cleanup,
        "object_count_before_close": object_count_before_close,
        "remaining_documents": sorted(App.listDocuments()),
    }
    return result, cleanup


def validate():
    if App.listDocuments():
        raise RuntimeError(
            "Phase 5 multi-object GUI validation requires an empty session"
        )

    qualification = bootstrap.require_qualified_runtime(
        ROOT
        / "reference"
        / "contracts"
        / "phase1-compatibility.json"
    )
    observer = _SelectionObserver()
    Gui.Selection.addObserver(observer)
    document = None
    parameter_dialog = None
    records = []
    try:
        document, store, records, view = _build_fixture(qualification)
        by_end = {
            record["initial_state"].intent.end_name: record
            for record in records
        }
        assert set(by_end) == {"Entry", "Exit"}
        target_record = by_end[SELECTED_END]
        sibling_record = by_end["Entry"]
        target_object = target_record["object"]
        target_proxy = target_record["proxy"]
        target_cache = target_record["coordinator"].cache
        sibling_object = sibling_record["object"]
        sibling_proxy = sibling_record["proxy"]
        sibling_cache = sibling_record["coordinator"].cache
        preview_request = target_record[
            "coordinator"
        ].specification.derived_request()

        initial_snapshot = _snapshot(document, records)
        initial_mappings = initial_snapshot["mappings"]
        assert len({
            mapping["transition_id"]
            for mapping in initial_mappings
        }) == workload.OBJECT_COUNT
        assert tuple(
            mapping["end_name"]
            for mapping in initial_mappings
        ) == ("Entry", "Exit")
        target_initial_state = target_record["initial_state"]
        sibling_initial_state = sibling_record["initial_state"]
        target_initial_signature = target_proxy.source_signature
        sibling_initial_signature = sibling_proxy.source_signature
        sibling_initial_payload = str(
            getattr(
                sibling_object,
                adapter.FREECAD_STATE_JSON_PROPERTY,
            )
        )
        sibling_initial_artifact = sibling_cache.artifact("preview")
        sibling_preservation_checks = {
            "initial": _assert_record_unchanged(
                sibling_record,
                sibling_initial_state,
                sibling_initial_signature,
                sibling_initial_payload,
                sibling_initial_artifact,
                preview_request,
            )
        }

        Gui.Selection.clearSelection()
        target, target_point, pointer_target = (
            _visible_centreline_target(
                view,
                target_record,
            )
        )
        observer.events.clear()
        target_proxy.pick_callback_count = 0
        QtTest.QTest.mouseMove(target, target_point)
        _process_gui()
        QtTest.QTest.mouseClick(
            target,
            QtCore.Qt.LeftButton,
            QtCore.Qt.NoModifier,
            target_point,
        )
        _process_gui()
        selected = Gui.Selection.getSelectionEx(document.Name)
        assert len(selected) == 1
        assert selected[0].Object is target_object
        selected_subelements = tuple(selected[0].SubElementNames)
        assert selected_subelements == (target_proxy.element_name,), {
            "events": observer.events,
            "pick_callback_count": target_proxy.pick_callback_count,
            "pointer_target": pointer_target,
            "selected_subelements": selected_subelements,
        }
        assert target_proxy.pick_callback_count >= 1
        assert observer.events
        selection_event = observer.events[-1]
        assert selection_event[:3] == (
            document.Name,
            target_object.Name,
            target_proxy.element_name,
        )
        selected_mapping = target_proxy.selection_for_element(
            selected[0].SubElementNames[0]
        )
        expected_mapping = target_record[
            "initial_artifact"
        ].payload.polylines[0]
        assert selected_mapping.domain_id == expected_mapping.domain_id
        assert selected_mapping.visual_id == expected_mapping.visual_id

        view.redraw()
        _process_gui()
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        editor_run_directory = (
            ROOT
            / "benchmark-output"
            / "freecad-bridge"
            / "phase5-transition-parameter-editor-runs"
            / stamp
        )
        editor_run_directory.mkdir(parents=True)
        selected_image_path = (
            editor_run_directory / "selected-transition-editor.png"
        )
        edited_image_path = (
            editor_run_directory / "edited-transition-editor.png"
        )
        controller = editor.TransitionParameterEditorController(
            lambda: _selected_transition(document, store)
        )
        parameter_dialog = editor.TransitionParameterEditorDialog(
            controller,
            QtWidgets,
            parent=Gui.getMainWindow(),
        )
        parameter_dialog.show()
        _process_gui()
        initial_length_text = parameter_dialog.length_edit.text()
        assert parameter_dialog.dialog.parent() is Gui.getMainWindow()
        assert parameter_dialog.dialog.isVisible()
        assert parameter_dialog.selected_transition_id == (
            target_initial_state.intent.transition_id
        )
        assert parameter_dialog.selected_identity_label.text() == (
            target_initial_state.intent.transition_id
        )
        assert initial_length_text == "420.000"
        assert parameter_dialog.apply_button.isEnabled()
        assert parameter_dialog.status_label.text() == (
            "Ready to edit the selected transition."
        )
        _capture_dialog(
            parameter_dialog.dialog,
            selected_image_path,
        )

        document.clearUndos()
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0

        before_noop_counters = _cache_counters(records)
        QtTest.QTest.mouseClick(
            parameter_dialog.apply_button,
            QtCore.Qt.LeftButton,
        )
        _process_gui()
        assert parameter_dialog.last_result.changed is False
        assert parameter_dialog.last_error is None
        assert adapter.read_transition_object(target_object) == (
            target_initial_state
        )
        assert _cache_counters(records) == before_noop_counters
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0
        assert parameter_dialog.status_label.text() == (
            "No transition change was required."
        )

        _replace_line_edit_text(
            parameter_dialog.length_edit,
            "360.000",
        )
        before_edit_counters = _cache_counters(records)
        QtTest.QTest.mouseClick(
            parameter_dialog.apply_button,
            QtCore.Qt.LeftButton,
        )
        _process_gui()
        edit_result = parameter_dialog.last_result
        assert edit_result is not None
        assert parameter_dialog.last_error is None
        assert parameter_dialog.status_label.text() == (
            "Edited transition {} to 360.000 mm.".format(
                target_initial_state.intent.transition_id
            )
        )
        view.redraw()
        _process_gui()
        _capture_dialog(
            parameter_dialog.dialog,
            edited_image_path,
        )
        after_edit_counters = _cache_counters(records)
        _assert_only_selected_regenerated(
            before_edit_counters,
            after_edit_counters,
            {
                "regenerations": 1,
                "requests": 1,
                "reuses": 0,
            },
        )
        assert edit_result.changed is True
        assert adapter.read_transition_object(
            target_object
        ) == edit_result.state
        assert target_proxy.source_signature != target_initial_signature
        edited_signature = target_proxy.source_signature
        sibling_preservation_checks["after_edit"] = (
            _assert_record_unchanged(
                sibling_record,
                sibling_initial_state,
                sibling_initial_signature,
                sibling_initial_payload,
                sibling_initial_artifact,
                preview_request,
            )
        )
        assert target_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert target_cache.status(
            target_initial_state,
            preview_request,
        ) == "stale"
        edit_snapshot = _snapshot(document, records)
        assert edit_snapshot["mappings"] == initial_mappings
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0

        before_undo_counters = _cache_counters(records)
        document.undo()
        view.redraw()
        _process_gui()
        after_undo_counters = _cache_counters(records)
        _assert_only_selected_regenerated(
            before_undo_counters,
            after_undo_counters,
            {
                "regenerations": 1,
                "requests": 1,
                "reuses": 0,
            },
        )
        assert adapter.read_transition_object(
            target_object
        ) == target_initial_state
        assert target_proxy.source_signature == target_initial_signature
        assert target_cache.status(
            target_initial_state,
            preview_request,
        ) == "current"
        sibling_preservation_checks["after_undo"] = (
            _assert_record_unchanged(
                sibling_record,
                sibling_initial_state,
                sibling_initial_signature,
                sibling_initial_payload,
                sibling_initial_artifact,
                preview_request,
            )
        )
        undo_snapshot = _snapshot(document, records)
        assert undo_snapshot["mappings"] == initial_mappings
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 1

        before_redo_counters = _cache_counters(records)
        document.redo()
        view.redraw()
        _process_gui()
        after_redo_counters = _cache_counters(records)
        _assert_only_selected_regenerated(
            before_redo_counters,
            after_redo_counters,
            {
                "regenerations": 1,
                "requests": 1,
                "reuses": 0,
            },
        )
        assert adapter.read_transition_object(
            target_object
        ) == edit_result.state
        assert target_proxy.source_signature == edited_signature
        assert target_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        sibling_preservation_checks["after_redo"] = (
            _assert_record_unchanged(
                sibling_record,
                sibling_initial_state,
                sibling_initial_signature,
                sibling_initial_payload,
                sibling_initial_artifact,
                preview_request,
            )
        )
        redo_snapshot = _snapshot(document, records)
        assert redo_snapshot["mappings"] == initial_mappings
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0

        failure_state = workload.state_for_end(
            SELECTED_END,
            workload.FAILED_EXIT_TRANSITION_LENGTH_MM,
        )
        target_coordinator = target_record["coordinator"]
        target_coordinator.failure_state = failure_state
        target_coordinator.failure_remaining = 1
        before_failure_counters = _cache_counters(records)
        before_failure_history = (
            int(document.UndoCount),
            int(document.RedoCount),
        )
        _replace_line_edit_text(
            parameter_dialog.length_edit,
            "390.000",
        )
        QtTest.QTest.mouseClick(
            parameter_dialog.apply_button,
            QtCore.Qt.LeftButton,
        )
        _process_gui()
        failure_error = parameter_dialog.last_error
        assert isinstance(failure_error, adapter.TransitionDocumentError)
        assert failure_error.code == "transaction-failed"
        assert parameter_dialog.last_result is None
        assert parameter_dialog.status_label.text().startswith(
            "Edit not applied: transaction-failed"
        )
        view.redraw()
        _process_gui()
        after_failure_counters = _cache_counters(records)
        _assert_only_selected_regenerated(
            before_failure_counters,
            after_failure_counters,
            {
                "regenerations": 2,
                "requests": 2,
                "reuses": 0,
            },
        )
        assert failure_error.recoverable is True
        assert failure_error.document_mutation is False
        assert target_coordinator.failure_remaining == 0
        assert adapter.read_transition_object(
            target_object
        ) == edit_result.state
        assert target_proxy.source_signature == edited_signature
        sibling_preservation_checks["after_failed_edit"] = (
            _assert_record_unchanged(
                sibling_record,
                sibling_initial_state,
                sibling_initial_signature,
                sibling_initial_payload,
                sibling_initial_artifact,
                preview_request,
            )
        )
        assert target_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert target_cache.status(
            failure_state,
            preview_request,
        ) == "stale"
        failure_snapshot = _snapshot(document, records)
        assert failure_snapshot["mappings"] == initial_mappings
        assert (
            int(document.UndoCount),
            int(document.RedoCount),
        ) == before_failure_history

        before_no_selection_state = adapter.read_transition_object(
            target_object
        )
        before_no_selection_counters = _cache_counters(records)
        before_no_selection_history = (
            int(document.UndoCount),
            int(document.RedoCount),
        )
        Gui.Selection.clearSelection()
        _replace_line_edit_text(
            parameter_dialog.length_edit,
            "370.000",
        )
        QtTest.QTest.mouseClick(
            parameter_dialog.apply_button,
            QtCore.Qt.LeftButton,
        )
        _process_gui()
        assert isinstance(
            parameter_dialog.last_error,
            editor.TransitionParameterSelectionError,
        )
        assert parameter_dialog.last_result is None
        assert parameter_dialog.status_label.text().startswith(
            "Edit not applied: Select one transition preview"
        )
        assert parameter_dialog.selected_identity_label.text() == "None"
        assert parameter_dialog.length_edit.text() == ""
        assert parameter_dialog.apply_button.isEnabled() is False
        assert adapter.read_transition_object(target_object) == (
            before_no_selection_state
        )
        assert _cache_counters(records) == before_no_selection_counters
        assert (
            int(document.UndoCount),
            int(document.RedoCount),
        ) == before_no_selection_history

        parameter_dialog.close()
        _process_gui()
        assert parameter_dialog.dialog.isVisible() is False

        final_counters = _cache_counters(records)
        selected_deltas = _counter_delta(
            before_edit_counters,
            final_counters,
            SELECTED_END,
        )
        sibling_deltas = _counter_delta(
            before_edit_counters,
            final_counters,
            "Entry",
        )
        pick_callback_count = target_proxy.pick_callback_count
        working_document = document
        document = None
        reopened_attachment, cleanup = (
            _exercise_reopened_attachment(
                working_document,
                records,
                failure_snapshot["mappings"],
                target_record["coordinator"].specification,
            )
        )
        records = []
        assert cleanup == {
            "discarded_cache_count": workload.OBJECT_COUNT,
            "disposed_proxy_count": workload.OBJECT_COUNT,
            "object_count_before_close": workload.OBJECT_COUNT,
            "remaining_documents": [],
        }

        payload = {
            "active_coin_scene_node_count": (
                failure_snapshot["active_coin_scene_node_count"]
            ),
            "cache_invalidation": {
                "selected_deltas": selected_deltas,
                "sibling_deltas": sibling_deltas,
            },
            "cleanup": cleanup,
            "document_object_count": (
                failure_snapshot["document_object_count"]
            ),
            "edit_command_route": "internal-application-command",
            "editor_control": "transition-length-mm",
            "editor_edited_image": str(edited_image_path),
            "editor_edited_state_visible": True,
            "editor_failure_diagnostic_visible": True,
            "editor_initial_length_text": initial_length_text,
            "editor_input": "qt-keyboard-and-mouse",
            "editor_no_selection_rejected": True,
            "editor_noop_history_delta": 0,
            "editor_parent": "FreeCAD-main-window",
            "editor_route": (
                "user-interface-controller-to-internal-application-command"
            ),
            "editor_selected_image": str(selected_image_path),
            "editor_selected_state_visible": True,
            "edit_undo_units": 1,
            "failure_history_preserved": True,
            "family_id": FAMILY_ID,
            "freecad_version": ".".join(App.Version()[:3]),
            "logical_layer_count": (
                failure_snapshot["logical_layer_count"]
            ),
            "mapping_preserved": True,
            "part_shape_created": False,
            "pick_callback_count": pick_callback_count,
            "pointer_target": pointer_target,
            "redo_restored_edit": True,
            "reopened_attachment": reopened_attachment,
            "representative_scope": workload.WORKLOAD_SCOPE_LIMIT,
            "rationale": workload.WORKLOAD_RATIONALE,
            "selected_end": SELECTED_END,
            "selected_transition_id": (
                selected_mapping.domain_id
            ),
            "selection_event": {
                "document": selection_event[0],
                "object": selection_event[1],
                "subelement": selection_event[2],
            },
            "selection_input": "qt-mouse-click",
            "sibling_state_preserved": all(
                all(stage_checks.values())
                for stage_checks in (
                    sibling_preservation_checks.values()
                )
            ),
            "sibling_state_stages": tuple(
                sibling_preservation_checks
            ),
            "transactional_failure_recovered": True,
            "undo_restored_initial": True,
            "workload_id": workload.WORKLOAD_ID,
        }
        print(SENTINEL + json.dumps(payload, sort_keys=True))
    finally:
        if parameter_dialog is not None:
            parameter_dialog.close()
        Gui.Selection.removeObserver(observer)
        Gui.Selection.clearSelection()
        for record in records:
            proxy = record.get("proxy")
            if proxy is not None and proxy.attached:
                proxy.dispose()
            coordinator = record.get("coordinator")
            if coordinator is not None:
                coordinator.cache.discard("preview")
        if (
            document is not None
            and document.Name in App.listDocuments()
        ):
            App.closeDocument(document.Name)


validate()
