"""Profile bounded transition selection and editing in the FreeCAD GUI."""

from dataclasses import replace
import functools
import gc
import hashlib
import json
import math
import os
import pathlib
import sys
import time

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin

try:
    from PySide6 import QtCore, QtOpenGLWidgets, QtTest, QtWidgets
    _OpenGLWidget = QtOpenGLWidgets.QOpenGLWidget
except ImportError:
    try:
        from PySide2 import QtCore, QtTest, QtWidgets
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
from tracktemplate.domain.alignment import GEOMETRY_TOLERANCE  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.ui import transition_parameter_editor as editor  # noqa: E402


_process_gui = functools.partial(
    _shared_process_gui,
    Gui.updateGui,
    QtWidgets.QApplication.processEvents,
)


PROFILE_ID = "phase5-transition-interaction-range-profile-v1"
SCALE_SET_COUNTS = (1, 2, 4, 8, 16)
OBJECTS_PER_SET = 2
PREVIEW_SEGMENT_COUNT = 32
EDITED_EXIT_TRANSITION_LENGTH_MM = (
    workload.EDITED_EXIT_TRANSITION_LENGTH_MM
)
GRID_COLUMNS = 4
GRID_X_SPACING_MM = 550.0
GRID_Y_SPACING_MM = 120.0


def _current_rss_mb():
    status = pathlib.Path("/proc/self/status")
    if not status.is_file():
        return None
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return float(line.split()[1]) / 1024.0
    return None


def _measure(action):
    gc.collect()
    rss_before_mb = _current_rss_mb()
    wall_started = time.perf_counter_ns()
    cpu_started = time.process_time_ns()
    result = action()
    process_cpu_ms = (time.process_time_ns() - cpu_started) / 1.0e6
    wall_ms = (time.perf_counter_ns() - wall_started) / 1.0e6
    rss_after_mb = _current_rss_mb()
    return result, {
        "process_cpu_ms": process_cpu_ms,
        "rss_after_mb": rss_after_mb,
        "rss_before_mb": rss_before_mb,
        "rss_delta_mb": (
            None
            if rss_before_mb is None or rss_after_mb is None
            else rss_after_mb - rss_before_mb
        ),
        "wall_ms": wall_ms,
    }


def _transition_id(set_index, end_name):
    return "SET-{:03d}/curve-track/2/transition/{}".format(
        set_index + 1,
        end_name.lower(),
    )


def _state(set_index, end_name):
    if end_name == "Entry":
        transition_length_mm = workload.ENTRY_TRANSITION_LENGTH_MM
    elif end_name == "Exit":
        transition_length_mm = workload.EXIT_TRANSITION_LENGTH_MM
    else:
        raise ValueError("end_name must be 'Entry' or 'Exit'")
    base_state = workload.state_for_end(
        end_name,
        transition_length_mm,
    )
    intent = replace(
        base_state.intent,
        transition_id=_transition_id(set_index, end_name),
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _states(set_count):
    return tuple(
        _state(set_index, end_name)
        for set_index in range(set_count)
        for end_name in ("Entry", "Exit")
    )


def _view_offset_mm(set_index):
    return (
        GRID_X_SPACING_MM * float(set_index % GRID_COLUMNS),
        GRID_Y_SPACING_MM * float(set_index // GRID_COLUMNS),
    )


class _PreviewCoordinator:
    def __init__(self, specification):
        self.cache = api.TransitionDerivedCache()
        self.specification = specification
        self.regeneration_count = 0
        self.request_count = 0
        self.reuse_count = 0

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
        return artifact


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


def _mapping_record(record):
    obj = record["object"]
    state = adapter.read_transition_object(obj)
    proxy = record["proxy"]
    mapping = proxy.selection_for_element(proxy.element_name)
    return {
        "domain_id": mapping.domain_id,
        "element_name": proxy.element_name,
        "layer_id": mapping.layer_id,
        "object_name": str(obj.Name),
        "transition_id": state.intent.transition_id,
        "visual_id": mapping.visual_id,
    }


def _digest(records):
    payload = json.dumps(
        records,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _canonical_record(record):
    obj = record["object"]
    state = adapter.read_transition_object(obj)
    return {
        "state_json": str(
            getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)
        ),
        "transition_id": state.intent.transition_id,
    }


def _snapshot(document, records):
    object_count = len(records)
    roots = [record["proxy"].selection_root for record in records]
    logical_layer_count = 0
    for record in records:
        root = record["proxy"].selection_root
        assert int(root.getNumChildren()) == 2
        assert int(root.findChild(record["translation"])) == 0
        scene_root = root.getChild(1)
        logical_layer_count += int(scene_root.getNumChildren())
    objects = tuple(document.Objects)
    snapshot = {
        "active_coin_scene_node_count": _count_coin_nodes(roots),
        "cache_regeneration_count": sum(
            record["coordinator"].regeneration_count
            for record in records
        ),
        "cache_request_count": sum(
            record["coordinator"].request_count
            for record in records
        ),
        "cache_reuse_count": sum(
            record["coordinator"].reuse_count
            for record in records
        ),
        "canonical_state_digest": _digest(
            [_canonical_record(record) for record in records]
        ),
        "display_modes_added": sum(
            len(tuple(record["object"].ViewObject.listDisplayModes()))
            - record["display_mode_count_before"]
            for record in records
        ),
        "document_object_count": len(objects),
        "logical_layer_count": logical_layer_count,
        "mapping_digest": _digest(
            [_mapping_record(record) for record in records]
        ),
        "part_shape_count": sum(
            "Shape" in tuple(obj.PropertiesList) for obj in objects
        ),
        "proxy_count": object_count,
        "root_children_added": sum(
            int(record["object"].ViewObject.RootNode.getNumChildren())
            - record["root_child_count_before"]
            for record in records
        ),
        "switch_children_added": sum(
            int(record["object"].ViewObject.SwitchNode.getNumChildren())
            - record["switch_child_count_before"]
            for record in records
        ),
    }
    assert snapshot["document_object_count"] == object_count
    assert snapshot["logical_layer_count"] == object_count
    assert snapshot["part_shape_count"] == 0
    assert snapshot["proxy_count"] == object_count
    assert snapshot["display_modes_added"] == object_count
    assert snapshot["root_children_added"] == 0
    assert snapshot["switch_children_added"] == object_count
    assert snapshot["active_coin_scene_node_count"] == object_count * 8
    for record in records:
        obj = record["object"]
        state = adapter.read_transition_object(obj)
        coordinator = record["coordinator"]
        assert obj.TypeId == "App::FeaturePython"
        assert obj.Proxy is None
        assert record["proxy"].attached is True
        assert coordinator.cache.status(
            state,
            coordinator.specification.derived_request(),
        ) == "current"
    return snapshot


def _build_fixture(qualification, set_count):
    document = App.newDocument("Phase5TransitionInteractionRange")
    document.UndoMode = 1
    store = adapter.FreeCADTransitionStore(qualification)
    states = _states(set_count)
    objects = store.create_many(document, states)
    specification = api.TransitionPreviewSpecification(
        segment_count=PREVIEW_SEGMENT_COUNT
    )
    records = []
    for object_index, (obj, state) in enumerate(zip(objects, states)):
        set_index = object_index // OBJECTS_PER_SET
        coordinator = _PreviewCoordinator(specification)
        artifact = coordinator.artifact_for_state(state)
        if state.intent.end_name == "Exit":
            colour = (0.9, 0.05, 0.02)
            line_width = 8.0
        else:
            colour = (0.05, 0.2, 0.9)
            line_width = 3.0
        record = {
            "coordinator": coordinator,
            "display_mode_count_before": len(
                tuple(obj.ViewObject.listDisplayModes())
            ),
            "initial_artifact": artifact,
            "initial_state": state,
            "object": obj,
            "root_child_count_before": int(
                obj.ViewObject.RootNode.getNumChildren()
            ),
            "switch_child_count_before": int(
                obj.ViewObject.SwitchNode.getNumChildren()
            ),
            "view_offset_mm": _view_offset_mm(set_index),
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
        translation = coin.SoTranslation()
        offset_x_mm, offset_y_mm = record["view_offset_mm"]
        translation.translation.setValue(
            offset_x_mm,
            offset_y_mm,
            0.0,
        )
        proxy.selection_root.insertChild(translation, 0)
        record["proxy"] = proxy
        record["translation"] = translation
        records.append(record)

    document.recompute()
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    _process_gui()
    return document, store, records, view


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
    polyline = target_record["initial_artifact"].payload.polylines[0]
    offset_x_mm, offset_y_mm = target_record["view_offset_mm"]
    viewport_width, viewport_height = (
        int(value) for value in view.getSize()
    )
    unique_hits = []
    hit_diagnostics = []
    for start, finish in zip(polyline.points[:-1], polyline.points[1:]):
        local_x_mm = (start.x_mm + finish.x_mm) / 2.0
        local_y_mm = (start.y_mm + finish.y_mm) / 2.0
        viewport_point = tuple(
            int(value)
            for value in view.getPointOnViewport(
                App.Vector(
                    local_x_mm + offset_x_mm,
                    local_y_mm + offset_y_mm,
                    0.0,
                )
            )
        )
        hit_records = tuple(view.getObjectsInfo(viewport_point) or ())
        hit_objects = {
            str(record.get("Object", ""))
            for record in hit_records
            if record.get("Object")
        }
        hit_diagnostics.append({
            "components": sorted(
                str(record.get("Component", ""))
                for record in hit_records
            ),
            "objects": sorted(hit_objects),
            "viewport_point": list(viewport_point),
        })
        hit_components = {
            str(record.get("Component", ""))
            for record in hit_records
        }
        if (
            hit_records
            and hit_objects == {str(target_object.Name)}
            and hit_components == {target_proxy.element_name}
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
                (local_x_mm, local_y_mm),
            ))
    if not unique_hits:
        raise RuntimeError(
            "the target Exit preview has no uniquely pickable point: {}".format(
                json.dumps(
                    {
                        "offset_mm": [offset_x_mm, offset_y_mm],
                        "segments": hit_diagnostics,
                        "target_object": str(target_object.Name),
                        "viewport_size": [
                            viewport_width,
                            viewport_height,
                        ],
                    },
                    sort_keys=True,
                )
            )
        )
    (
        edge_margin,
        viewport_point,
        hit_records,
        local_preview_point,
    ) = max(unique_hits, key=lambda candidate: candidate[0])

    candidates = list(view_widget.findChildren(_OpenGLWidget))
    if isinstance(view_widget, _OpenGLWidget):
        candidates.append(view_widget)
    targets = [candidate for candidate in candidates if candidate.isVisible()]
    if len(targets) != 1:
        raise RuntimeError(
            "expected one visible OpenGL widget; found {}".format(
                len(targets)
            )
        )
    target = targets[0]
    target_point = QtCore.QPoint(
        round(viewport_point[0] * target.width() / viewport_width),
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
        "cursor_point": list(cursor_point),
        "edge_margin_pixels": edge_margin,
        "local_point": [target_point.x(), target_point.y()],
        "local_preview_point_mm": list(local_preview_point),
        "locator": "projected-canonical-point-read-only-hit-test",
        "object_name": target.objectName(),
        "hit_record_count": len(hit_records),
        "unique_mapping_count": 1,
        "view_offset_mm": [offset_x_mm, offset_y_mm],
        "viewport_point": list(viewport_point),
    }


def _click_target(target, target_point):
    QtTest.QTest.mouseMove(target, target_point)
    _process_gui()
    QtTest.QTest.mouseClick(
        target,
        QtCore.Qt.LeftButton,
        QtCore.Qt.NoModifier,
        target_point,
    )
    _process_gui()


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


def _open_dialog(document, store):
    controller = editor.TransitionParameterEditorController(
        lambda: _selected_transition(document, store)
    )
    dialog = editor.TransitionParameterEditorDialog(
        controller,
        QtWidgets,
        parent=Gui.getMainWindow(),
    )
    dialog.show()
    _process_gui()
    return dialog


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


def _apply_dialog_edit(parameter_dialog):
    _replace_line_edit_text(
        parameter_dialog.length_edit,
        "{:.3f}".format(EDITED_EXIT_TRANSITION_LENGTH_MM),
    )
    QtTest.QTest.mouseClick(
        parameter_dialog.apply_button,
        QtCore.Qt.LeftButton,
    )
    _process_gui()
    return parameter_dialog.last_result


def _undo(document):
    document.undo()
    _process_gui()


def _dispose_fixture(document, records, parameter_dialog):
    if parameter_dialog is not None:
        parameter_dialog.dialog.close()
    Gui.Selection.clearSelection()
    _process_gui()
    disposed = 0
    discarded_caches = 0
    for record in records:
        proxy = record["proxy"]
        if proxy.attached and proxy.dispose():
            disposed += 1
        record["object"].ViewObject.Proxy = None
        if record["coordinator"].cache.discard("preview") == ("preview",):
            discarded_caches += 1
    object_count_before_close = len(document.Objects)
    App.closeDocument(document.Name)
    _process_gui()
    return {
        "discarded_cache_count": discarded_caches,
        "disposed_proxy_count": disposed,
        "object_count_before_close": object_count_before_close,
        "remaining_documents": sorted(App.listDocuments()),
    }


def validate(set_count):
    if set_count not in SCALE_SET_COUNTS:
        raise ValueError("set_count is outside the declared scale range")
    if App.listDocuments():
        raise RuntimeError(
            "Phase 5 interaction profiling requires an empty session"
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
    records = []
    parameter_dialog = None
    try:
        cold_result, cold = _measure(
            lambda: _build_fixture(qualification, set_count)
        )
        document, store, records, view = cold_result
        initial_snapshot = _snapshot(document, records)
        cold["snapshot"] = initial_snapshot
        initial_states = {
            record["initial_state"].intent.transition_id: record[
                "initial_state"
            ]
            for record in records
        }

        target_set_index = set_count // 2
        target_transition_id = _transition_id(target_set_index, "Exit")
        target_record = next(
            record
            for record in records
            if record["initial_state"].intent.transition_id
            == target_transition_id
        )
        target_object = target_record["object"]
        target_proxy = target_record["proxy"]
        target, target_point, pointer_target = _visible_centreline_target(
            view,
            target_record,
        )

        Gui.Selection.clearSelection()
        observer.events.clear()
        target_proxy.pick_callback_count = 0
        _ignored, selection = _measure(
            lambda: _click_target(target, target_point)
        )
        selected = tuple(Gui.Selection.getSelectionEx(document.Name))
        assert len(selected) == 1
        assert selected[0].Object is target_object
        assert tuple(selected[0].SubElementNames) == (
            target_proxy.element_name,
        )
        mapping = target_proxy.selection_for_element(
            selected[0].SubElementNames[0]
        )
        assert mapping.domain_id == target_transition_id
        assert target_proxy.pick_callback_count >= 1
        assert observer.events
        selection.update({
            "mapping_domain_id": mapping.domain_id,
            "pick_callback_count": target_proxy.pick_callback_count,
            "pointer_target": pointer_target,
            "selected_transition_id": target_transition_id,
        })

        parameter_dialog, dialog_open = _measure(
            lambda: _open_dialog(document, store)
        )
        assert parameter_dialog.selected_transition_id == (
            target_transition_id
        )
        assert parameter_dialog.length_edit.text() == "420.000"
        dialog_open.update({
            "selected_identity_visible": (
                parameter_dialog.selected_identity_label.text()
                == target_transition_id
            ),
            "selected_length_text": parameter_dialog.length_edit.text(),
        })

        document.clearUndos()
        before_edit = _snapshot(document, records)
        edit_result, edit = _measure(
            lambda: _apply_dialog_edit(parameter_dialog)
        )
        assert edit_result is not None and edit_result.changed is True
        after_edit = _snapshot(document, records)
        current_states = {
            adapter.read_transition_object(record["object"]).intent.transition_id:
            adapter.read_transition_object(record["object"])
            for record in records
        }
        changed_transition_ids = sorted(
            transition_id
            for transition_id, state in current_states.items()
            if state != initial_states[transition_id]
        )
        assert changed_transition_ids == [target_transition_id]
        target_state = current_states[target_transition_id]
        assert math.isclose(
            target_state.analysis.transition_length_mm,
            EDITED_EXIT_TRANSITION_LENGTH_MM,
            rel_tol=0.0,
            abs_tol=GEOMETRY_TOLERANCE,
        )
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0
        edit.update({
            "cache_regeneration_delta": (
                after_edit["cache_regeneration_count"]
                - before_edit["cache_regeneration_count"]
            ),
            "cache_request_delta": (
                after_edit["cache_request_count"]
                - before_edit["cache_request_count"]
            ),
            "changed_transition_ids": changed_transition_ids,
            "history_delta": 1,
            "snapshot": after_edit,
            "target_length_mm": (
                target_state.analysis.transition_length_mm
            ),
            "unchanged_record_count": len(records) - 1,
        })

        before_undo = _snapshot(document, records)
        _ignored, undo = _measure(lambda: _undo(document))
        after_undo = _snapshot(document, records)
        restored_states = {
            adapter.read_transition_object(record["object"]).intent.transition_id:
            adapter.read_transition_object(record["object"])
            for record in records
        }
        assert restored_states == initial_states
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 1
        undo.update({
            "cache_regeneration_delta": (
                after_undo["cache_regeneration_count"]
                - before_undo["cache_regeneration_count"]
            ),
            "cache_request_delta": (
                after_undo["cache_request_count"]
                - before_undo["cache_request_count"]
            ),
            "history_delta": -1,
            "snapshot": after_undo,
            "target_length_mm": restored_states[
                target_transition_id
            ].analysis.transition_length_mm,
        })

        cleanup, cleanup_measurement = _measure(
            lambda: _dispose_fixture(
                document,
                records,
                parameter_dialog,
            )
        )
        cleanup.update(cleanup_measurement)
        document = None
        records = []
        parameter_dialog = None

        payload = {
            "cleanup": cleanup,
            "cold": cold,
            "dialog_open": dialog_open,
            "edit": edit,
            "fixture": {
                "capacity_status": "not-accepted",
                "family_unit": (
                    "qualified-one-secondary-track-entry-exit-pair"
                ),
                "logical_object_count": set_count * OBJECTS_PER_SET,
                "preview_segment_count": PREVIEW_SEGMENT_COUNT,
                "set_count": set_count,
                "target_transition_id": target_transition_id,
                "view_layout": "test-only-grid-translations",
            },
            "freecad_version": ".".join(App.Version()[:3]),
            "profile_id": PROFILE_ID,
            "schema_version": 1,
            "selection": selection,
            "starting_state": (
                "fresh isolated GUI process, empty document set, new "
                "document, empty per-object preview caches and a test-only "
                "view grid"
            ),
            "undo": undo,
        }
        print(
            "TRACKTEMPLATE_PHASE5_INTERACTION_RANGE_SAMPLE="
            + json.dumps(payload, sort_keys=True)
        )
    finally:
        try:
            Gui.Selection.removeObserver(observer)
        except Exception:
            pass
        for record in records:
            proxy = record["proxy"]
            if proxy.attached:
                proxy.dispose()
        if parameter_dialog is not None:
            parameter_dialog.dialog.close()
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
