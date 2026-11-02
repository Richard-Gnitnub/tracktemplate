"""One bounded, import-safe B/C operator and view qualification.

Only start() imports Qt. The existing hosted coordinator owns resource limits,
source/handling admission and evidence transport. Fixtures are generated in
fresh documents; their temporary FCStd file is never diagnostic evidence.
"""

import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "REA-BC-LIFECYCLE-GUI-001"
PROFILE_ID = "templot-556b-00-D0GAF-32mm-full-exit"
PREFIX = "TRACKTEMPLATE_REA_TRACKWORK_GUI="


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _regular(path):
    path = Path(path)
    assert path.is_absolute() and path.is_file()
    assert not any(item.is_symlink() for item in (path, *path.parents))
    return path


def _selection(gui):
    return tuple((row.DocumentName, row.ObjectName, tuple(row.SubElementNames))
                 for row in gui.Selection.getSelectionEx("*"))


def _scene(proxy):
    if proxy.scene is None:
        return None
    return tuple((line.visual_id, line.layer_id, line.points)
                 for line in proxy.scene.lines)


def _history(document):
    return (int(document.UndoMode), int(document.UndoCount),
            int(document.RedoCount), tuple(document.UndoNames),
            tuple(document.RedoNames))


def _scene_digest(proxy):
    return hashlib.sha256(json.dumps(
        _scene(proxy), separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


class ReaGui(unittest.TestCase):
    """Drive the real composed manager, source records and Coin ViewProvider."""

    def count(self, name, amount=1):
        self.receipt["checks"][name] += amount

    def settle(self):
        if self.app.ActiveDocument is not None:
            self.app.ActiveDocument.recompute()
        self.gui.updateGui()
        self.qt.QtCore.QCoreApplication.processEvents()
        self.qt.QtTest.QTest.qWait(50)
        self.qt.QtCore.QCoreApplication.processEvents()

    def click(self, button):
        self.assertTrue(button.isVisible() and button.isEnabled())
        self.qt.QtTest.QTest.mouseClick(button, self.qt.QtCore.Qt.LeftButton)
        self.settle()

    def combo(self, combo, value, *, text=False):
        index = combo.findText(value) if text else combo.findData(value)
        self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)
        self.settle()
        self.assertEqual(combo.currentText() if text else combo.currentData(),
                         value)

    def edit(self, widget, text):
        widget.setFocus()
        widget.selectAll()
        self.qt.QtTest.QTest.keyClicks(widget, text)
        self.assertEqual(widget.text(), text)

    def panel(self, action):
        """Enter the normal B16 launch and nested inherited manager dialogs."""
        state = {"curve": None, "manager": None, "done": False,
                 "error": None, "traceback": None}
        timer = self.qt.QtCore.QTimer()
        timer.setInterval(20)
        deadline = time.monotonic() + 30

        def fail(error):
            state["error"] = error
            state["traceback"] = traceback.format_exc()
            state["done"] = True
            timer.stop()
            active = self.qt.QtWidgets.QApplication.activeModalWidget()
            for dialog in (state["manager"], state["curve"], active):
                if (dialog is not None and self.qt.isValid(dialog)
                        and dialog.isVisible()):
                    dialog.reject()

        def open_manager():
            try:
                self.click(state["curve"].turnout_manager_button)
            except BaseException as error:
                fail(error)

        def drive():
            if state["done"]:
                return
            try:
                if time.monotonic() >= deadline:
                    raise AssertionError("Normal REA manager did not open.")
                dialog = self.qt.QtWidgets.QApplication.activeModalWidget()
                if isinstance(dialog, self.module.CurveInputDialog):
                    if state["curve"] is None:
                        state["curve"] = dialog
                        self.owned_windows.append(dialog)
                        # Leave this timeout before entering the nested loop.
                        self.qt.QtCore.QTimer.singleShot(0, open_manager)
                    return
                if isinstance(dialog, self.module.TurnoutManagerDialog):
                    timer.stop()
                    state["manager"] = dialog
                    self.owned_windows.append(dialog)
                    panel = dialog._tracktemplate_rea_panel
                    self.assertIs(panel.controller.document,
                                  self.app.ActiveDocument)
                    dialog.resize(1100, 900)
                    dialog.mode_tabs.setCurrentIndex(
                        dialog.mode_tabs.indexOf(panel.scroll_area),
                    )
                    self.settle()
                    self.assertTrue(panel.widget.isVisible())
                    self.assertIsNone(panel.last_error)
                    self.active_panel = panel
                    action(panel, dialog)
                    state["done"] = True
                    dialog.reject()
                    state["curve"].reject()
            except BaseException as error:
                fail(error)

        timer.timeout.connect(drive)
        timer.start()
        try:
            self.launcher["_launch_workflow_with_rea_editor"](
                self.session, self.qualification,
            )
        finally:
            timer.stop()
            for dialog in (state["manager"], state["curve"]):
                if (dialog is not None and self.qt.isValid(dialog)
                        and dialog.isVisible()):
                    dialog.reject()
            self.settle()
        if state["error"] is not None:
            self.receipt["modal_failure"] = state["traceback"]
            raise state["error"]
        self.assertTrue(state["done"], "Normal manager journey did not execute")
        self.assertIsNone(self.qt.QtWidgets.QApplication.activeModalWidget())

    def _gl_widget(self):
        from PySide6.QtOpenGLWidgets import QOpenGLWidget

        area = self.gui.getMainWindow().findChild(self.qt.QtWidgets.QMdiArea)
        subwindow = area.activeSubWindow()
        self.assertIsNotNone(subwindow)
        widgets = [item for item in subwindow.findChildren(QOpenGLWidget)
                   if item.isVisible()]
        self.assertEqual(len(widgets), 1)
        self.assertTrue(widgets[0].isValid())
        return widgets[0]

    def image(self, name, *, dialog=None):
        from PySide6.QtOpenGLWidgets import QOpenGLWidget

        self.assertIn(name, self.control.rea_images(self.stage))
        self.assertFalse((self.directory / name).exists())
        self.settle()
        if dialog is None:
            widget = self._gl_widget()
            previous = widget.updateBehavior()
            try:
                widget.setUpdateBehavior(QOpenGLWidget.PartialUpdate)
                image = self.gui.getMainWindow().grab()
            finally:
                widget.setUpdateBehavior(previous)
            self.assertEqual(widget.updateBehavior(), previous)
            kind = "viewport_images"
        else:
            self.assertTrue(dialog.isVisible())
            image = dialog.grab()
            kind = "dialog_images"
        self.assertFalse(image.isNull())
        path = self.directory / name
        self.assertTrue(image.save(str(path), "PNG"))
        self.receipt["screenshots"].append({
            "path": name, "sha256": _digest(path),
            "bytes": path.stat().st_size,
        })
        self.count(kind)
        self.count("screenshots_total")

    def view(self, obj):
        for item in obj.Document.Objects:
            if item.ViewObject is not None:
                item.ViewObject.Visibility = item is obj
        view = self.gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.viewTop()
        view.fitAll()
        view.redraw()
        self.settle()
        self.assertTrue(obj.ViewObject.Visibility)
        return view

    def pick(self, obj):
        """Click a projected real rail point; never synthesize selection."""
        view = self.view(obj)
        proxy = obj.ViewObject.Proxy
        line = next(line for line in proxy.scene.lines
                    if line.layer_id == "rails")
        index = len(line.points) // 2
        point = tuple((a + b) / 2 for a, b in zip(
            line.points[index - 1], line.points[index],
        ))
        widget = self._gl_widget()
        x, y = view.getPointOnScreen(self.app.Vector(*point))
        ratio = widget.devicePixelRatioF()
        # Qualified View3DInventorViewer::toQPoint: bottom-up physical
        # viewport pixels become top-down Qt logical widget coordinates.
        target = self.qt.QtCore.QPoint(
            round(x / ratio), round((widget.height() * ratio - y - 1) / ratio),
        )
        self.assertTrue(widget.rect().contains(target))
        self.gui.Selection.clearSelection()
        widget.setFocus()
        self.qt.QtTest.QTest.mouseMove(widget, target)
        self.settle()
        self.qt.QtTest.QTest.mouseClick(
            widget, self.qt.QtCore.Qt.LeftButton,
            self.qt.QtCore.Qt.NoModifier, target,
        )
        self.settle()
        rows = self.gui.Selection.getSelectionEx(obj.Document.Name)
        self.assertEqual(len(rows), 1)
        self.assertIs(rows[0].Object, obj)
        self.assertEqual(tuple(rows[0].SubElementNames), ("ReaTrackwork",))
        self.assertEqual(proxy.selection_for_element("ReaTrackwork"),
                         self.read(obj).entity_id)
        self.receipt["picks"].append({
            "object": obj.Name, "entity_id": self.read(obj).entity_id,
            "label": obj.Label, "subelement": "ReaTrackwork",
            "world_mm": point, "qt_pixel": [target.x(), target.y()],
            "device_pixel_ratio": ratio,
        })
        self.count("actual_viewport_picks")

    def new_document(self, name, *, fixture=True):
        doc = self.app.newDocument(name)
        self.owned_documents.append(doc.Name)
        self.count("fresh_documents")
        doc.UndoMode = 1
        if not fixture:
            self.settle()
            return doc
        import Part
        from freecad_validate_rea_trackwork import _property

        settings = doc.addObject("App::FeaturePython", "Settings")
        for key, value in (
            ("GeneratedBy", self.module.GENERATOR_ID),
            ("GeneratedRole", "Settings"), ("TemplateSetID", "SET-001"),
            ("TrackConfigurationJSON", "[]"),
        ):
            _property(settings, "String", key, value)
        for key, value in (
            ("TransitionLength", 0.0), ("CurveRadius", 3000.0),
            ("TotalTurnAngle", 90.0), ("MainTemplateWidth", 32.0),
            ("TemplateThickness", 2.0),
        ):
            _property(settings, "Float", key, value)
        configs = []
        for name, offset in (("HostA", 0.0), ("HostB", 50.0)):
            config = self.module.default_straight_config(len(configs))
            config.update(manager_id="ROUTE-" + name, name=name,
                          length=5000.0, start_y=offset,
                          template_width=32.0, template_thickness=2.0)
            configs.append(config)
            host = doc.addObject("Part::Feature", name)
            host.Shape = Part.makePolygon([
                self.app.Vector(0, offset, 0),
                self.app.Vector(5000, offset, 0),
            ])
            for key, value in (
                ("GeneratedBy", self.module.GENERATOR_ID),
                ("GeneratedRole", "StraightTrackCentreline"),
                ("ExportSubtype", "TrackCentreline"),
                ("TemplateSetID", "SET-001"),
                ("RouteID", config["manager_id"]),
                ("RouteName", name), ("TrackName", name),
            ):
                _property(host, "String", key, value)
            _property(host, "Integer", "TrackNumber", 1)
        _property(settings, "String", self.module.STRAIGHT_CONFIGS_PROPERTY,
                  json.dumps(configs, sort_keys=True, allow_nan=False))
        self.settle()
        return doc

    @staticmethod
    def read(obj):
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            read_rea_trackwork_object,
        )
        return read_rea_trackwork_object(obj)

    def rows(self, doc):
        from tracktemplate.adapters.freecad.rea_turnout_state import (
            read_rea_trackwork_objects,
        )
        return tuple(read_rea_trackwork_objects(doc))

    def assert_document_inventory(self, obj):
        objects = tuple(obj.Document.Objects)
        self.assertEqual(len(objects), 4)
        self.assertEqual({item.Name for item in objects},
                         {"Settings", "HostA", "HostB", obj.Name})
        self.assertTrue(any(item is obj for item in objects))
        self.assertEqual(obj.TypeId, "App::FeaturePython")
        self.assertNotIn("Shape", obj.PropertiesList)

    def assert_record(self, obj, size, ratio, *, selected, crossover=False):
        self.assert_document_inventory(obj)
        from tracktemplate.application.rea_turnout_state import (
            REA_HOSTS_PROPERTY, REA_INTENT_JSON_PROPERTY,
        )
        from tracktemplate.presentation.rea_trackwork import (
            ReaTrackworkViewProvider,
        )
        intent = self.read(obj)
        self.assertEqual(intent.source_specification.switch_size, size)
        self.assertEqual(intent.source_specification.crossing_ratio, ratio)
        self.assertEqual(intent.entity_kind,
                         "crossover" if crossover else "turnout")
        profile = intent.exit_sleeper_profile
        self.assertEqual(profile.profile_id if profile else None,
                         PROFILE_ID if selected else None)
        raw = json.loads(getattr(obj, REA_INTENT_JSON_PROPERTY))
        self.assertEqual(raw["schema_version"], 2 if selected else 1)
        self.assertEqual("exit_sleeper_profile" in raw["intent"], selected)
        names = ("HostA", "HostB") if crossover else ("HostA",)
        self.assertEqual(intent.host_names, names)
        self.assertEqual(tuple(host.Name for host in getattr(
            obj, REA_HOSTS_PROPERTY,
        )), names)
        self.assertNotIn("Shape", obj.PropertiesList)
        self.assertIsInstance(obj.ViewObject.Proxy, ReaTrackworkViewProvider)
        proxy = obj.ViewObject.Proxy
        self.assertIsNotNone(proxy.scene)
        self.assertEqual(proxy.scene.entity_id, intent.entity_id)
        self.assertEqual(proxy.selection_root.getNumChildren(), 1)
        self.assertGreater(proxy._binding.coordinates.point.getNum(), 0)
        self.assertEqual(proxy._binding.line_set.numVertices.getNum(),
                         len(proxy.scene.lines))
        self.assertTrue(all(len(line.points) >= 2 for line in proxy.scene.lines))
        exits = tuple(line.visual_id.rsplit(":", 1)[-1]
                      for line in proxy.scene.lines
                      if ":timber:E" in line.visual_id)
        self.assertEqual(exits, ("E1", "E2") * (2 if crossover else 1)
                         if selected else ())
        connector = tuple(line for line in proxy.scene.lines
                          if ":connector:" in line.visual_id)
        self.assertEqual(len(connector), 4 if crossover else 0)
        self.assertEqual(len(self.rows(obj.Document)), 1)
        self.receipt["states"].append({
            "switch_size": size, "crossing_ratio": ratio,
            "selected_profile": selected, "entity_kind": intent.entity_kind,
            "entity_id": intent.entity_id, "object_name": obj.Name,
            "canonical_sha256": hashlib.sha256(getattr(
                obj, REA_INTENT_JSON_PROPERTY,
            ).encode()).hexdigest(), "scene_sha256": _scene_digest(proxy),
            "exit_lines": list(exits), "scene_lines": len(proxy.scene.lines),
        })
        return intent

    def select_record(self, panel, obj):
        self.combo(panel.records_combo, self.read(obj).entity_id)
        self.click(panel.edit_button)
        self.assertIsNone(panel.last_error)
        self.assertEqual(panel.controller.editing_intent, self.read(obj))

    def create(self, panel, *, crossover=False, selected=False):
        self.combo(panel.kind_combo, "crossover" if crossover else "turnout")
        self.combo(panel.size_combo, "B")
        self.combo(panel.host_a_combo, "HostA")
        if crossover:
            self.combo(panel.host_b_combo, "HostB")
            self.combo(panel.handing_combo, "Automatic handing", text=True)
            self.assertEqual(float(panel.minimum_radius_edit.text()), 600.0)
        else:
            self.combo(panel.handing_combo, "Left-hand", text=True)
        self.edit(panel.ratio_edit, "8.0")
        self.edit(panel.chainage_edit, "1500.0")
        self.combo(panel.exit_profile_combo, PROFILE_ID if selected else None)
        self.click(panel.create_button)
        self.assertIsNone(panel.last_error)
        obj = panel.last_result
        self.assertIsNotNone(obj)
        self.count("source_records_created")
        self.receipt["geometry_builds"] += 1
        if selected:
            self.count("profile_selections")
        self.assert_record(obj, "B", 8.0, selected=selected,
                           crossover=crossover)
        return obj

    def rebuild(self, obj):
        before = obj.TrackTemplateReaIntentJSON
        def action(panel, _dialog):
            self.combo(panel.records_combo, self.read(obj).entity_id)
            self.click(panel.rebuild_button)
            self.assertIsNone(panel.last_error)
        self.panel(action)
        self.assertEqual(obj.TrackTemplateReaIntentJSON, before)
        self.assertIsNotNone(obj.ViewObject.Proxy.scene)
        self.count("explicit_rebuilds")
        self.receipt["geometry_builds"] += 1

    def full_journey(self):
        doc = self.new_document("ReaGuiTO")
        created = []
        def initial(panel, dialog):
            self.assertIsNone(panel.exit_profile_combo.currentData())
            obj = self.create(panel)
            created.append(obj)
            self.image("to-b8-fields.png", dialog=dialog)
        self.panel(initial)
        obj, = created
        self.view(obj)
        self.image("to-b8.png")
        self.pick(obj)
        identity = self.read(obj).entity_id
        baseline = obj.TrackTemplateReaIntentJSON
        baseline_scene = _scene(obj.ViewObject.Proxy)
        name = obj.Name
        obj.Label = "Operator-owned B/C label"
        self.count("operator_label_cases")

        def select_c(panel, dialog):
            self.select_record(panel, obj)
            self.combo(panel.size_combo, "C")
            self.edit(panel.ratio_edit, "9.25")
            self.combo(panel.exit_profile_combo, PROFILE_ID)
            self.click(panel.apply_button)
            self.assertIsNone(panel.last_error)
            self.assertIs(panel.last_result, obj)
            self.count("successful_parameter_updates")
            self.count("profile_selections")
            self.receipt["geometry_builds"] += 1
            self.assert_record(obj, "C", 9.25, selected=True)
            self.image("to-c925-selected-fields.png", dialog=dialog)
        self.panel(select_c)
        self.assertEqual(self.read(obj).entity_id, identity)
        self.assertEqual(obj.Label, "Operator-owned B/C label")
        self.view(obj)
        self.image("to-c925-selected.png")
        selected_payload = obj.TrackTemplateReaIntentJSON
        selected_scene = _scene(obj.ViewObject.Proxy)
        attached = obj.ViewObject.Proxy
        self.assertIsNotNone(attached.scene)
        doc.saveAs(str(self.saved))
        self.assertIs(obj.ViewObject.Proxy, attached)
        self.app.closeDocument(doc.Name)
        self.settle()
        self.assertIsNone(attached._observer_app)
        doc = self.app.openDocument(str(self.saved))
        doc.UndoMode = 1
        self.owned_documents.append(doc.Name)
        self.count("reopens")
        obj = doc.getObject(name)
        self.assertIsNotNone(obj)
        self.assertEqual(obj.TrackTemplateReaIntentJSON, selected_payload)
        self.assertEqual(self.read(obj).entity_id, identity)
        self.assertEqual(self.read(obj).exit_sleeper_profile.profile_id,
                         PROFILE_ID)
        self.assertEqual(obj.Label, "Operator-owned B/C label")
        self.assertIsNone(obj.ViewObject.Proxy.scene)
        self.assertEqual(obj.ViewObject.Proxy.selection_root.getNumChildren(), 0)
        self.count("selected_profile_reopens")
        self.image("reopened-empty.png")
        def check_loaded(panel, _dialog):
            self.select_record(panel, obj)
            self.assertEqual(panel.exit_profile_combo.currentData(), PROFILE_ID)
            self.assertEqual(panel.size_combo.currentData(), "C")
            self.assertEqual(float(panel.ratio_edit.text()), 9.25)
        self.panel(check_loaded)
        self.rebuild(obj)
        self.assertEqual(_scene(obj.ViewObject.Proxy), selected_scene)

        # A new normal launch owns a fresh store, but must adopt this real view.
        proxy = obj.ViewObject.Proxy
        self.gui.Selection.addSelection(doc.Name, obj.Name, "ReaTrackwork")
        self.settle()
        before_selection = _selection(self.gui)
        snapshot = proxy.snapshot()
        before_history = _history(doc)
        self.assertEqual(doc.RedoCount, 0)
        def failed_edit(panel, dialog):
            self.select_record(panel, obj)
            self.edit(panel.ratio_edit, "10.0")
            original = proxy.replace
            def late_failure(scene, signature):
                original(scene, signature)
                raise RuntimeError("Injected B/C GUI post-view failure")
            proxy.replace = late_failure
            try:
                self.click(panel.apply_button)
            finally:
                proxy.replace = original
            self.assertIsNotNone(panel.last_error)
            self.assertIn("Injected B/C GUI post-view failure",
                          panel.status_label.text())
            self.assertEqual(obj.TrackTemplateReaIntentJSON, selected_payload)
            self.assertEqual(_history(doc), before_history)
            self.assertEqual(_selection(self.gui), before_selection)
            self.assertIs(obj.ViewObject.Proxy, proxy)
            self.assertEqual(proxy.snapshot(), snapshot)
            self.assertEqual(obj.Label, "Operator-owned B/C label")
            self.assertEqual(self.read(obj).host_names, ("HostA",))
            self.assertIs(proxy._observer_app, self.app)
            self.assertIs(proxy._observed_object, obj)
            self.assertTrue(proxy._dependencies)
            self.image("rollback-error.png", dialog=dialog)
        self.panel(failed_edit)
        self.count("adopted_view_rollback_cases")
        self.receipt["geometry_builds"] += 1
        self.view(obj)
        self.image("rollback-retained.png")

        def return_b(panel, dialog):
            self.select_record(panel, obj)
            self.combo(panel.size_combo, "B")
            self.edit(panel.ratio_edit, "8.0")
            self.combo(panel.exit_profile_combo, None)
            self.click(panel.apply_button)
            self.assertIsNone(panel.last_error)
            self.assertIs(panel.last_result, obj)
            self.count("successful_parameter_updates")
            self.count("profile_deselections")
            self.receipt["geometry_builds"] += 1
            self.assert_record(obj, "B", 8.0, selected=False)
            self.assertEqual(obj.TrackTemplateReaIntentJSON, baseline)
            self.assertEqual(_scene(obj.ViewObject.Proxy), baseline_scene)
            history = _history(doc)
            binding = obj.ViewObject.Proxy._binding
            self.click(panel.apply_button)
            self.assertIsNone(panel.last_error)
            self.assertEqual(_history(doc), history)
            self.assertIs(obj.ViewObject.Proxy._binding, binding)
            self.assertEqual(obj.TrackTemplateReaIntentJSON, baseline)
            self.count("no_op_applies")
            self.image("to-b8-returned-fields.png", dialog=dialog)
        self.panel(return_b)
        self.view(obj)
        self.image("to-b8-returned.png")
        self.assertEqual(obj.Label, "Operator-owned B/C label")
        doc.undo()
        self.settle()
        self.assertEqual(obj.TrackTemplateReaIntentJSON, selected_payload)
        self.assertIsNone(obj.ViewObject.Proxy.scene)
        doc.redo()
        self.settle()
        self.assertEqual(obj.TrackTemplateReaIntentJSON, baseline)
        self.assertIsNone(obj.ViewObject.Proxy.scene)
        self.count("undo_redo_pairs")
        self.rebuild(obj)
        self.assertEqual(_scene(obj.ViewObject.Proxy), baseline_scene)

        import Part
        host = doc.getObject("HostA")
        shape = host.Shape.copy()
        host.Shape = Part.makePolygon([
            self.app.Vector(0, 1, 0), self.app.Vector(5000, 1, 0),
        ])
        self.settle()
        self.assertIsNone(obj.ViewObject.Proxy.scene)
        self.assertEqual(obj.ViewObject.Proxy.selection_root.getNumChildren(), 0)
        self.assertEqual(obj.TrackTemplateReaIntentJSON, baseline)
        self.image("host-invalidated.png")
        host.Shape = shape
        self.settle()
        self.assertIsNone(obj.ViewObject.Proxy.scene)
        self.count("host_invalidation_cases")
        self.rebuild(obj)
        self.assertEqual(_scene(obj.ViewObject.Proxy), baseline_scene)
        self.view(obj)
        self.image("host-rebuilt.png")
        self.app.closeDocument(doc.Name)
        self.settle()

        doc = self.new_document("ReaGuiXO")
        created.clear()
        def crossover(panel, dialog):
            xo = self.create(panel, crossover=True, selected=True)
            created.append(xo)
            self.assertEqual(self.read(xo).minimum_radius_mm, 600.0)
            self.image("xo-selected-fields.png", dialog=dialog)
        self.panel(crossover)
        xo, = created
        self.view(xo)
        self.image("xo-selected.png")
        self.pick(xo)
        payload, history = xo.TrackTemplateReaIntentJSON, _history(doc)
        scene, binding = _scene(xo.ViewObject.Proxy), xo.ViewObject.Proxy._binding
        inventory = tuple(item.Name for item in doc.Objects)
        def invalid(panel, _dialog):
            self.select_record(panel, xo)
            for text in ("nan", "3.0"):
                self.edit(panel.ratio_edit, text)
                self.click(panel.apply_button)
                self.assertIsNotNone(panel.last_error)
                self.assertIn("Could not complete:", panel.status_label.text())
                self.assertEqual(xo.TrackTemplateReaIntentJSON, payload)
                self.assertEqual(_history(doc), history)
                self.assertEqual(tuple(item.Name for item in doc.Objects), inventory)
                self.assertEqual(_scene(xo.ViewObject.Proxy), scene)
                self.assertIs(xo.ViewObject.Proxy._binding, binding)
                self.receipt["refusals"].append({
                    "input": text, "visible_text": panel.status_label.text(),
                })
                self.count("visible_input_refusals")
        self.panel(invalid)

    def assert_source_tree(self, config, authority):
        # The host provides the tracked manifest. The sandbox verifies its
        # complete digest and bytes without needing git or a child process.
        expected = config["product_files_sha256"]
        self.assertIs(type(expected), dict)
        self.assertTrue(expected)
        actual = {}
        for name, wanted in expected.items():
            self.assertIs(type(name), str)
            self.assertTrue(name.startswith("tracktemplate/"))
            self.assertNotIn("..", Path(name).parts)
            path = _regular(ROOT / name)
            actual[name] = _digest(path)
            self.assertEqual(actual[name], wanted)
        digest = hashlib.sha256(json.dumps(
            actual, sort_keys=True, separators=(",", ":"),
        ).encode()).hexdigest()
        self.assertEqual(digest, authority["source_tree_sha256"])

    def test_authorised_gui_stage(self):
        sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
        from tools import hosted_l1_gui_validation as control
        import hosted_l1_gui_suite as images
        from types import SimpleNamespace

        self.control = control
        self.stage = os.environ["L1_GUI_STAGE"]
        config_path = _regular(os.environ["TRACKTEMPLATE_L1_RUN_CONFIG"])
        self.assertEqual(_digest(config_path), os.environ[
            "TRACKTEMPLATE_L1_RUN_CONFIG_SHA256"])
        config = json.loads(config_path.read_text())
        authority_path = _regular(os.environ["TRACKTEMPLATE_L1_GUI_AUTHORITY"])
        self.assertEqual(_digest(authority_path), os.environ[
            "TRACKTEMPLATE_L1_GUI_AUTHORITY_SHA256"])
        authority = json.loads(authority_path.read_text())
        control.validate_rea_authority(authority, os.environ)
        self.assertEqual(config["inputs"], [])
        self.assertEqual(config["external_inputs"], 0)
        self.assertEqual(Path(config["repository_root"]), ROOT)
        self.assertEqual(_digest(__file__), authority["gui_entry_sha256"])
        self.assert_source_tree(config, authority)
        evidence = Path(config["private_evidence_dir"])
        self.assertEqual(evidence, authority_path.parent)
        self.directory = evidence / "gui"
        self.directory.mkdir(mode=0o700)
        temporary = Path(config["temporary_document_dir"])
        self.assertEqual(temporary, evidence.parent / "test-data")
        self.assertFalse(temporary.exists())
        self.saved = temporary / "research.FCStd"
        self.owned_documents, self.owned_windows = [], []
        self.app = None
        self.receipt = {
            "status": "RUNNING", "stage": self.stage, "scope_id": SCOPE,
            "workload": "rea-bc", "profile": control.original.EXPECTED_PROFILE,
            "source_commit": authority["source_commit"],
            "source_tree_sha256": authority["source_tree_sha256"],
            "input_hashes": authority["input_hashes"],
            "gui_entry_sha256": authority["gui_entry_sha256"],
            "checks": dict.fromkeys(control.rea_counts(self.stage), 0),
            "geometry_builds": 0, "screenshots": [], "states": [],
            "picks": [], "refusals": [], "temporary_documents": [],
            "visual_review": "REQUIRED", "physical_fit": "NOT_PROVED",
            "native_evidence_reused": authority["prior_native_evidence"],
            "failures": 0, "errors": 0, "skips": 0,
        }
        started = time.monotonic()
        failure = None
        try:
            import FreeCAD as app
            import FreeCADGui as gui
            from PySide6 import QtCore, QtGui, QtTest, QtWidgets
            from shiboken6 import isValid
            from tracktemplate import bootstrap

            self.app, self.gui = app, gui
            self.qt = SimpleNamespace(QtCore=QtCore, QtGui=QtGui,
                                      QtTest=QtTest, QtWidgets=QtWidgets,
                                      isValid=isValid)
            self.assertEqual(sys.flags.optimize, 0)
            self.assertTrue(app.GuiUp and gui.getMainWindow().isVisible())
            self.assertEqual(app.listDocuments(), {})
            self.assertEqual(QtGui.QGuiApplication.platformName(), "xcb")
            self.qualification = bootstrap.require_qualified_runtime(
                ROOT / "reference/contracts/phase1-compatibility.json",
            )
            self.launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
            self.assertEqual(self.launcher["FOUNDATION_RESULT"]["matched_profile_id"],
                             control.original.EXPECTED_PROFILE)
            api, loader = self.launcher["_load_foundation"](ROOT)
            self.session, routing = self.launcher["_load_modular_transition_workflow"](
                ROOT, api, loader,
            )
            self.module = self.session.module
            self.receipt["routing"] = routing
            self.assertEqual(app.listDocuments(), {})
            if self.stage == "readiness":
                doc = self.new_document("ReaGuiReadiness", fixture=False)
                def readiness(panel, dialog):
                    self.assertEqual(panel.controller.records, ())
                    self.assertEqual(panel.controller.hosts, ())
                    self.assertIsNone(panel.exit_profile_combo.currentData())
                    self.assertTrue(panel.create_button.isVisible())
                    self.assertEqual(doc.Objects, [])
                    self.image("readiness-panel.png", dialog=dialog)
                self.panel(readiness)
                self.assertEqual(doc.Objects, [])
            else:
                temporary.mkdir(mode=0o700)
                self.full_journey()
            self.receipt["renderer"] = images._gl_record(
                app, gui, QtGui, QtWidgets,
            )
            self.count("tests")
            control.validate_rea_counts(self.receipt["checks"], self.stage)
            self.assertEqual(self.receipt["geometry_builds"],
                             0 if self.stage == "readiness" else 8)
        except BaseException as error:
            failure = error
            self.receipt["traceback"] = traceback.format_exc()
        finally:
            cleanup = []
            if self.app is not None:
                for window in reversed(self.owned_windows):
                    try:
                        if self.qt.isValid(window):
                            if window.isVisible():
                                window.reject()
                            self.assertFalse(window.isVisible())
                    except BaseException:
                        cleanup.append(traceback.format_exc())
                if self.qt.QtWidgets.QApplication.activeModalWidget() is not None:
                    cleanup.append("An owned modal dialog remains")
                for name in reversed(self.owned_documents):
                    try:
                        if name in self.app.listDocuments():
                            doc = self.app.listDocuments()[name]
                            proxies = [obj.ViewObject.Proxy for obj in doc.Objects
                                       if obj.ViewObject is not None
                                       and hasattr(obj.ViewObject.Proxy,
                                                   "_observer_app")]
                            self.app.closeDocument(name)
                            self.settle()
                            self.assertTrue(all(proxy._observer_app is None
                                                for proxy in proxies))
                        self.assertNotIn(name, self.app.listDocuments())
                    except BaseException:
                        cleanup.append(traceback.format_exc())
                self.receipt["documents_remaining"] = len(self.app.listDocuments())
                if self.app.listDocuments() or self.app.ActiveDocument is not None:
                    cleanup.append("Document registry not empty")
            try:
                self.assert_source_tree(config, authority)
                self.assertTrue(all(_digest(ROOT / name) == value
                                    for group in ("input_hashes", "control_files_sha256")
                                    for name, value in authority[group].items()))
                self.receipt["input_bindings_unchanged"] = True
                if self.saved.exists():
                    self.receipt["temporary_documents"] = [{
                        "path": "test-data/research.FCStd",
                        "sha256": _digest(self.saved),
                        "bytes": self.saved.stat().st_size,
                    }]
                if temporary.exists():
                    self.assertEqual(set(temporary.iterdir()),
                                     {self.saved} if self.saved.exists() else set())
            except BaseException:
                self.receipt["input_bindings_unchanged"] = False
                cleanup.append(traceback.format_exc())
            self.receipt["cleanup_errors"] = cleanup
            self.receipt["owned_documents_closed"] = self.app is not None and not cleanup
            self.receipt["owned_windows_closed"] = self.app is not None and not cleanup
            self.receipt["total_seconds"] = time.monotonic() - started
            if cleanup and failure is None:
                failure = AssertionError("B/C GUI cleanup unproved")
            self.receipt["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                self.receipt["sentinel"] = control.sentinel(self.stage, "rea-bc")
            else:
                self.receipt["errors"] = 1
            _write(self.directory / "result.json", self.receipt)
        if failure is not None:
            raise failure


def start():
    """Run exactly one test after the actual Qt event loop starts."""
    from PySide6 import QtCore

    def execute():
        code = 1
        test = ReaGui("test_authorised_gui_stage")
        try:
            suite = unittest.TestSuite([test])
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            if (result.wasSuccessful() and result.testsRun == 1
                    and not result.skipped):
                receipt = test.receipt
                assert receipt["status"] == "PASS"
                print("\n" + PREFIX + json.dumps(receipt, sort_keys=True,
                                                 allow_nan=False), flush=True)
                print(receipt["sentinel"], flush=True)
                code = 0
        except BaseException:
            traceback.print_exc()
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            QtCore.QCoreApplication.exit(code)

    QtCore.QTimer.singleShot(0, execute)
