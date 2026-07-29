"""Exercise the Phase 5 Coin ViewProvider fixture in the real FreeCAD GUI."""

from dataclasses import replace
import datetime
import json
import math
import os
import pathlib
import sys

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

from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.application import transition_edit as command  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)


def _state(transition_length_mm):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:viewprovider-gui",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 GUI transition",
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _artifact(cache, state, specification):
    return api.regenerate_transition_preview(
        cache,
        state,
        specification,
    )


def _process_gui():
    for _iteration in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()


def _red_pixel_positions(path):
    image = QtGui.QImage(str(path))
    if image.isNull():
        raise RuntimeError("FreeCAD created an unreadable GUI screenshot")
    positions = set()
    for y_pos in range(image.height()):
        for x_pos in range(image.width()):
            colour = image.pixelColor(x_pos, y_pos)
            red = colour.red()
            green = colour.green()
            blue = colour.blue()
            if red >= 160 and red >= green * 2 and red >= blue * 2:
                positions.add((x_pos, y_pos))
    return frozenset(positions)


def _red_pixel_count(path):
    return len(_red_pixel_positions(path))


def _red_pixel_columns(image):
    columns = {}
    for y_pos in range(image.height()):
        for x_pos in range(image.width()):
            colour = image.pixelColor(x_pos, y_pos)
            red = colour.red()
            green = colour.green()
            blue = colour.blue()
            if red >= 160 and red >= green * 2 and red >= blue * 2:
                columns.setdefault(x_pos, []).append(y_pos)
    return columns


def _visible_centreline_target():
    main_window = Gui.getMainWindow()
    mdi_area = main_window.findChild(QtWidgets.QMdiArea)
    subwindow = None if mdi_area is None else mdi_area.activeSubWindow()
    if subwindow is None:
        raise RuntimeError("FreeCAD has no active 3D-view subwindow")
    view_widget = subwindow.widget()
    if view_widget is None or not view_widget.isVisible():
        raise RuntimeError("FreeCAD has no visible 3D-view widget")

    image = view_widget.grab().toImage()
    if image.isNull():
        raise RuntimeError("FreeCAD created an unreadable 3D-view grab")
    columns = _red_pixel_columns(image)
    if len(columns) < 20:
        raise RuntimeError(
            "FreeCAD 3D-view grab did not contain the transition"
        )
    image_x = sorted(columns)[len(columns) // 2]
    image_y_values = sorted(columns[image_x])
    image_y = image_y_values[len(image_y_values) // 2]
    view_point = QtCore.QPoint(
        round(image_x * view_widget.width() / image.width()),
        round(image_y * view_widget.height() / image.height()),
    )
    global_point = view_widget.mapToGlobal(view_point)
    candidates = list(
        view_widget.findChildren(_OpenGLWidget)
    )
    if isinstance(view_widget, _OpenGLWidget):
        candidates.append(view_widget)
    targets = []
    for candidate in candidates:
        candidate_point = candidate.mapFromGlobal(global_point)
        if candidate.isVisible() and candidate.rect().contains(
            candidate_point
        ):
            targets.append((candidate, candidate_point))
    if len(targets) != 1:
        raise RuntimeError(
            "expected one OpenGL widget under the transition; found {}".format(
                len(targets)
            )
        )
    target, target_point = targets[0]
    main_window.activateWindow()
    mdi_area.setActiveSubWindow(subwindow)
    target.setFocus()
    _process_gui()
    return target, target_point, {
        "class_name": target.metaObject().className(),
        "local_point": [target_point.x(), target_point.y()],
        "object_name": target.objectName(),
        "view_red_columns": len(columns),
    }


class _SelectionObserver:
    def __init__(self):
        self.events = []

    def addSelection(
        self,
        document_name,
        object_name,
        subelement_name,
        point,
    ):
        self.events.append(
            (
                str(document_name),
                str(object_name),
                str(subelement_name),
                tuple(float(value) for value in point),
            )
        )


class _ObservedTransitionCoinViewProviderFixture(
    viewprovider.TransitionCoinViewProviderFixture
):
    def __init__(self, *args, **kwargs):
        self.pick_callback_count = 0
        super().__init__(*args, **kwargs)

    def getElementPicked(self, picked_point):
        self.pick_callback_count += 1
        return super().getElementPicked(picked_point)


def _expect_adapter_error(action, code):
    try:
        action()
    except adapter.TransitionDocumentError as error:
        assert error.code == code, error
        return error
    raise AssertionError("Expected TransitionDocumentError {!r}".format(code))


def validate():
    if App.listDocuments():
        raise RuntimeError(
            "Phase 5 ViewProvider GUI validation requires an empty session"
        )

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
    visible_path = run_directory / "visible.png"
    hidden_path = run_directory / "hidden.png"
    edited_path = run_directory / "edited.png"
    undo_path = run_directory / "undo.png"
    redo_path = run_directory / "redo.png"
    recovered_path = run_directory / "recovered.png"
    change_back_path = run_directory / "change-back.png"
    change_back_undo_path = run_directory / "change-back-undo.png"
    change_back_redo_path = run_directory / "change-back-redo.png"

    document = App.newDocument("Phase5TransitionViewProvider")
    document.UndoMode = 1
    observer = _SelectionObserver()
    Gui.Selection.addObserver(observer)
    proxy = None
    try:
        qualification = bootstrap.require_qualified_runtime(
            ROOT
            / "reference"
            / "contracts"
            / "phase1-compatibility.json"
        )
        store = adapter.FreeCADTransitionStore(qualification)
        initial_state = _state(300.0)
        obj = store.create(document, initial_state)
        view_object = obj.ViewObject
        object_properties = tuple(obj.PropertiesList)
        view_properties = tuple(view_object.PropertiesList)
        root_count_before = int(view_object.RootNode.getNumChildren())
        mode_count_before = int(view_object.SwitchNode.getNumChildren())

        failure_control = {
            "state": None,
            "remaining": 0,
        }
        preview_cache = api.TransitionDerivedCache()
        preview_specification = api.TransitionPreviewSpecification(
            segment_count=32
        )
        preview_request = preview_specification.derived_request()
        cache_events = []

        def artifact_for_state(state):
            previous = preview_cache.artifact("preview")
            artifact = _artifact(
                preview_cache,
                state,
                preview_specification,
            )
            cache_events.append((state, previous, artifact))
            if (
                failure_control["remaining"]
                and state == failure_control["state"]
            ):
                failure_control["remaining"] -= 1
                raise RuntimeError(
                    "injected GUI preview refresh failure"
                )
            return artifact

        artifact = artifact_for_state(initial_state)
        assert preview_cache.status(
            initial_state,
            preview_request,
        ) == "current"
        proxy = _ObservedTransitionCoinViewProviderFixture(
            view_object,
            artifact,
            renderer.TransitionCoinStyle(
                line_color_rgb=(0.9, 0.05, 0.02),
                line_width=6.0,
            ),
            coin,
            state_reader=adapter.read_transition_object,
            artifact_for_state=artifact_for_state,
            source_property_name=adapter.FREECAD_STATE_JSON_PROPERTY,
        )
        document.recompute()
        assert tuple(obj.PropertiesList) == object_properties
        assert tuple(view_object.PropertiesList) == view_properties
        assert obj.TypeId == "App::FeaturePython"
        assert not hasattr(obj, "Shape")
        assert obj.Proxy is None
        assert len(document.Objects) == 1
        assert proxy.attached is True
        assert (
            int(view_object.RootNode.getNumChildren())
            == root_count_before
        )
        assert (
            int(view_object.SwitchNode.getNumChildren())
            == mode_count_before + 1
        )
        assert (
            int(view_object.SwitchNode.findChild(proxy.selection_root))
            >= 0
        )
        assert proxy.selection_root.getTypeId().getName() == "SoFCSelection"
        assert int(proxy.selection_root.getNumChildren()) == 1
        view_object.DisplayMode = proxy.display_mode
        initial_scene_root = proxy.selection_root.getChild(0)
        assert proxy.refresh_for_state(initial_state) is False
        assert cache_events[-1] == (
            initial_state,
            artifact,
            artifact,
        )
        assert int(
            proxy.selection_root.getChild(0).getNodeId()
        ) == int(initial_scene_root.getNodeId())

        view = Gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        view.redraw()
        _process_gui()
        view.saveImage(str(visible_path), 1000, 700, "Current")
        visible_red_positions = _red_pixel_positions(visible_path)
        visible_red_pixels = len(visible_red_positions)
        assert visible_red_pixels >= 100

        view_object.Visibility = False
        view.redraw()
        _process_gui()
        view.saveImage(str(hidden_path), 1000, 700, "Current")
        hidden_red_pixels = _red_pixel_count(hidden_path)
        assert hidden_red_pixels <= max(5, visible_red_pixels // 20)

        view_object.Visibility = True
        view.redraw()
        _process_gui()

        Gui.Selection.clearSelection()
        target, target_point, pointer_target = (
            _visible_centreline_target()
        )
        QtTest.QTest.mouseMove(target, target_point)
        _process_gui()
        proxy.pick_callback_count = 0
        observer.events.clear()
        QtTest.QTest.mouseClick(
            target,
            QtCore.Qt.LeftButton,
            QtCore.Qt.NoModifier,
            target_point,
        )
        _process_gui()
        selected = Gui.Selection.getSelectionEx(document.Name)
        assert len(selected) == 1
        assert selected[0].Object is obj
        selected_subelements = tuple(selected[0].SubElementNames)
        assert selected_subelements == (proxy.element_name,), {
            "events": observer.events,
            "pick_callback_count": proxy.pick_callback_count,
            "pointer_target": pointer_target,
            "selected_subelements": selected_subelements,
        }
        assert observer.events
        event = observer.events[-1]
        assert event[:3] == (
            document.Name,
            obj.Name,
            proxy.element_name,
        )
        mapped = proxy.selection_for_element(
            selected[0].SubElementNames[0]
        )
        assert (
            mapped.domain_id
            == artifact.payload.polylines[0].domain_id
        )
        assert (
            mapped.visual_id
            == artifact.payload.polylines[0].visual_id
        )

        Gui.Selection.clearSelection()
        view.redraw()
        _process_gui()
        document.clearUndos()
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0
        initial_source_signature = proxy.source_signature
        edit_port = adapter.FreeCADTransitionEditPort(
            store,
            document,
            obj,
            proxy,
        )
        edited_intent = replace(
            initial_state.intent,
            target_signed_offset_mm=_state(
                340.0
            ).intent.target_signed_offset_mm,
        )
        edit_result = command.edit_transition_intent(
            initial_state,
            edited_intent,
            edit_port,
        )
        assert edit_result.changed is True
        assert adapter.read_transition_object(obj) == edit_result.state
        assert proxy.source_signature != initial_source_signature
        edited_source_signature = proxy.source_signature
        edited_artifact = preview_cache.artifact("preview")
        assert edited_artifact.source_signature == edited_source_signature
        assert preview_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert preview_cache.status(
            initial_state,
            preview_request,
        ) == "stale"
        edited_mapping = proxy.selection_for_element(proxy.element_name)
        assert edited_mapping.domain_id == mapped.domain_id
        assert edited_mapping.visual_id == mapped.visual_id
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0
        assert tuple(obj.PropertiesList) == object_properties
        assert tuple(view_object.PropertiesList) == view_properties
        assert len(document.Objects) == 1
        assert not hasattr(obj, "Shape")
        view.redraw()
        _process_gui()
        view.saveImage(str(edited_path), 1000, 700, "Current")
        edited_red_positions = _red_pixel_positions(edited_path)
        assert len(edited_red_positions) >= 100
        assert edited_red_positions != visible_red_positions

        document.undo()
        view.redraw()
        _process_gui()
        assert adapter.read_transition_object(obj) == initial_state
        assert proxy.source_signature == initial_source_signature
        undo_artifact = preview_cache.artifact("preview")
        assert undo_artifact.source_signature == (
            artifact.source_signature
        )
        assert undo_artifact.payload == artifact.payload
        assert preview_cache.status(
            initial_state,
            preview_request,
        ) == "current"
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 1
        view.saveImage(str(undo_path), 1000, 700, "Current")
        undo_red_positions = _red_pixel_positions(undo_path)
        assert undo_red_positions == visible_red_positions

        document.redo()
        view.redraw()
        _process_gui()
        assert adapter.read_transition_object(obj) == edit_result.state
        assert proxy.source_signature == edited_source_signature
        redo_artifact = preview_cache.artifact("preview")
        assert redo_artifact.source_signature == (
            edited_artifact.source_signature
        )
        assert redo_artifact.payload == edited_artifact.payload
        assert preview_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0
        view.saveImage(str(redo_path), 1000, 700, "Current")
        redo_red_positions = _red_pixel_positions(redo_path)
        assert redo_red_positions == edited_red_positions

        before_noop = (
            int(document.UndoCount),
            int(document.RedoCount),
            str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)),
            proxy.source_signature,
            preview_cache.artifact("preview"),
            len(cache_events),
        )
        noop_result = command.edit_transition_intent(
            edit_result.state,
            edit_result.state.intent,
            edit_port,
        )
        assert noop_result.changed is False
        assert (
            int(document.UndoCount),
            int(document.RedoCount),
            str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)),
            proxy.source_signature,
            preview_cache.artifact("preview"),
            len(cache_events),
        ) == before_noop

        failure_state = _state(380.0)
        failure_control["state"] = failure_state
        failure_control["remaining"] = 1
        before_failure = (
            adapter.read_transition_object(obj),
            int(document.UndoCount),
            int(document.RedoCount),
            len(document.Objects),
            tuple(obj.PropertiesList),
            tuple(view_object.PropertiesList),
            proxy.source_signature,
        )
        failure_error = _expect_adapter_error(
            lambda: command.edit_transition_intent(
                edit_result.state,
                failure_state.intent,
                edit_port,
            ),
            "transaction-failed",
        )
        assert failure_error.recoverable is True
        assert failure_error.document_mutation is False
        assert failure_control["remaining"] == 0
        assert (
            adapter.read_transition_object(obj),
            int(document.UndoCount),
            int(document.RedoCount),
            len(document.Objects),
            tuple(obj.PropertiesList),
            tuple(view_object.PropertiesList),
            proxy.source_signature,
        ) == before_failure
        assert proxy.selection_for_element(
            proxy.element_name
        ).domain_id == mapped.domain_id
        assert preview_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert preview_cache.status(
            failure_state,
            preview_request,
        ) == "stale"
        assert preview_cache.artifact(
            "preview"
        ).source_signature == edited_source_signature
        assert cache_events[-2][0] == failure_state
        assert cache_events[-1][0] == edit_result.state
        view.redraw()
        _process_gui()
        view.saveImage(str(recovered_path), 1000, 700, "Current")
        recovered_red_positions = _red_pixel_positions(recovered_path)
        assert recovered_red_positions == edited_red_positions

        before_change_back_undos = int(document.UndoCount)
        change_back_result = command.edit_transition_intent(
            edit_result.state,
            initial_state.intent,
            edit_port,
        )
        assert change_back_result.changed is True
        assert change_back_result.state == initial_state
        assert adapter.read_transition_object(obj) == initial_state
        assert proxy.source_signature == initial_source_signature
        change_back_artifact = preview_cache.artifact("preview")
        assert change_back_artifact.source_signature == (
            artifact.source_signature
        )
        assert change_back_artifact.payload == artifact.payload
        assert preview_cache.status(
            initial_state,
            preview_request,
        ) == "current"
        assert int(document.UndoCount) - before_change_back_undos == 1
        assert int(document.RedoCount) == 0
        assert tuple(obj.PropertiesList) == object_properties
        assert tuple(view_object.PropertiesList) == view_properties
        assert len(document.Objects) == 1
        assert not hasattr(obj, "Shape")
        assert proxy.selection_for_element(
            proxy.element_name
        ).domain_id == mapped.domain_id
        view.redraw()
        _process_gui()
        view.saveImage(str(change_back_path), 1000, 700, "Current")
        change_back_red_positions = _red_pixel_positions(
            change_back_path
        )
        assert change_back_red_positions == visible_red_positions

        document.undo()
        view.redraw()
        _process_gui()
        assert adapter.read_transition_object(obj) == edit_result.state
        assert proxy.source_signature == edited_source_signature
        assert preview_cache.status(
            edit_result.state,
            preview_request,
        ) == "current"
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 1
        view.saveImage(
            str(change_back_undo_path),
            1000,
            700,
            "Current",
        )
        change_back_undo_red_positions = _red_pixel_positions(
            change_back_undo_path
        )
        assert change_back_undo_red_positions == edited_red_positions

        document.redo()
        view.redraw()
        _process_gui()
        assert adapter.read_transition_object(obj) == initial_state
        assert proxy.source_signature == initial_source_signature
        assert preview_cache.status(
            initial_state,
            preview_request,
        ) == "current"
        assert int(document.UndoCount) == 2
        assert int(document.RedoCount) == 0
        view.saveImage(
            str(change_back_redo_path),
            1000,
            700,
            "Current",
        )
        change_back_redo_red_positions = _red_pixel_positions(
            change_back_redo_path
        )
        assert change_back_redo_red_positions == visible_red_positions

        cache_reuse_count = sum(
            previous is current
            for _state_value, previous, current in cache_events
        )
        cache_regeneration_count = len(cache_events) - cache_reuse_count
        assert cache_reuse_count >= 1
        assert cache_regeneration_count >= 1

        selection_root = proxy.selection_root
        assert proxy.dispose() is True
        assert proxy.attached is False
        assert int(selection_root.getNumChildren()) == 0
        assert preview_cache.discard("preview") == ("preview",)
        assert preview_cache.artifact("preview") is None
        document.removeObject(obj.Name)
        document.recompute()
        assert document.Objects == []

        payload = {
            "change_back_redo_restored_initial": True,
            "change_back_restored_initial": True,
            "change_back_undo_restored_edit": True,
            "change_back_undo_units": 1,
            "document_object_count": 1,
            "document_object_type": "App::FeaturePython",
            "edit_command_route": "internal-application-command",
            "edit_failure_recovered": True,
            "edit_noop_history_delta": 0,
            "edit_undo_units": 1,
            "freecad_version": ".".join(App.Version()[:3]),
            "hidden_red_pixels": hidden_red_pixels,
            "mapped_domain_id": mapped.domain_id,
            "mapped_visual_id": mapped.visual_id,
            "part_shape_created": False,
            "persisted_schema_changed": False,
            "preview_cache_discarded": True,
            "preview_cache_failure_recovered": True,
            "preview_cache_regeneration_count": cache_regeneration_count,
            "preview_cache_request_count": len(cache_events),
            "preview_cache_retained": True,
            "preview_cache_reuse_count": cache_reuse_count,
            "preview_cache_reuse_proved": True,
            "save_route_exercised": False,
            "display_modes_added": 1,
            "root_children_added": 0,
            "selection_input": "qt-mouse-click",
            "pick_callback_count": proxy.pick_callback_count,
            "pointer_target": pointer_target,
            "screenshots": {
                "change_back": str(change_back_path),
                "change_back_redo": str(change_back_redo_path),
                "change_back_undo": str(change_back_undo_path),
                "edited": str(edited_path),
                "hidden": str(hidden_path),
                "recovered": str(recovered_path),
                "redo": str(redo_path),
                "undo": str(undo_path),
                "visible": str(visible_path),
            },
            "selection_event": {
                "document": event[0],
                "object": event[1],
                "subelement": event[2],
            },
            "preview_signatures": {
                "change_back": change_back_artifact.source_signature,
                "edited": edited_source_signature,
                "initial": initial_source_signature,
            },
            "red_pixel_counts": {
                "change_back": len(change_back_red_positions),
                "change_back_redo": len(
                    change_back_redo_red_positions
                ),
                "change_back_undo": len(
                    change_back_undo_red_positions
                ),
                "edited": len(edited_red_positions),
                "recovered": len(recovered_red_positions),
                "redo": len(redo_red_positions),
                "undo": len(undo_red_positions),
                "visible": visible_red_pixels,
            },
            "redo_restored_edit": True,
            "undo_restored_initial": True,
            "visible_red_pixels": visible_red_pixels,
        }
        print(
            "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI="
            + json.dumps(payload, sort_keys=True)
        )
    finally:
        Gui.Selection.removeObserver(observer)
        Gui.Selection.clearSelection()
        if proxy is not None and proxy.attached:
            proxy.dispose()
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


validate()
