"""Exercise the Phase 5 Coin ViewProvider fixture in the real FreeCAD GUI."""

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
    from PySide6 import QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtGui, QtWidgets
    except ImportError:
        from PySide import QtGui
        QtWidgets = QtGui


ROOT = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)


def _artifact():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = 300.0
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
    state = api.analyse_transition_state(api.TransitionState(intent))
    return api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        api.TransitionPreviewSpecification(segment_count=32),
    )


def _process_gui():
    for _iteration in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()


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

    document = App.newDocument("Phase5TransitionViewProvider")
    observer = _SelectionObserver()
    Gui.Selection.addObserver(observer)
    proxy = None
    try:
        obj = document.addObject(
            "App::FeaturePython",
            "Phase5TransitionPreview",
        )
        view_object = obj.ViewObject
        object_properties = tuple(obj.PropertiesList)
        view_properties = tuple(view_object.PropertiesList)
        root_count_before = int(view_object.RootNode.getNumChildren())
        mode_count_before = int(view_object.SwitchNode.getNumChildren())

        artifact = _artifact()
        proxy = viewprovider.TransitionCoinViewProviderFixture(
            view_object,
            artifact,
            renderer.TransitionCoinStyle(
                line_color_rgb=(0.9, 0.05, 0.02),
                line_width=6.0,
            ),
            coin,
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

        view = Gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        view.redraw()
        _process_gui()
        view.saveImage(str(visible_path), 1000, 700, "Current")
        visible_red_pixels = _red_pixel_count(visible_path)
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
        Gui.Selection.addSelection(obj, proxy.element_name)
        _process_gui()
        selected = Gui.Selection.getSelectionEx(document.Name)
        assert len(selected) == 1
        assert selected[0].Object is obj
        assert tuple(selected[0].SubElementNames) == (proxy.element_name,)
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
        selection_root = proxy.selection_root
        assert proxy.dispose() is True
        assert proxy.attached is False
        assert int(selection_root.getNumChildren()) == 0
        document.removeObject(obj.Name)
        document.recompute()
        assert document.Objects == []

        payload = {
            "document_object_count": 1,
            "document_object_type": "App::FeaturePython",
            "freecad_version": ".".join(App.Version()[:3]),
            "hidden_red_pixels": hidden_red_pixels,
            "mapped_domain_id": mapped.domain_id,
            "mapped_visual_id": mapped.visual_id,
            "part_shape_created": False,
            "display_modes_added": 1,
            "root_children_added": 0,
            "screenshots": {
                "hidden": str(hidden_path),
                "visible": str(visible_path),
            },
            "selection_event": {
                "document": event[0],
                "object": event[1],
                "subelement": event[2],
            },
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
