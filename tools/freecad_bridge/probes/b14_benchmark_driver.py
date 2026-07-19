"""Register deterministic B14 benchmark-stage controls inside FreeCAD."""

import json
import sys
import types

from tools.freecad_bridge.b14_recipe import DEFAULT_CHAINAGE_MM, select_crossover_hosts

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets


class B14BenchmarkDriver:
    """Drive known B14 stages while recording and clearing modal outcomes."""

    def __init__(self):
        self.module = sys.modules.get("tracktemplate_b14_session")
        if self.module is None:
            raise RuntimeError("Load B14 before registering the benchmark driver")
        self.manager = getattr(self.module, "_automation_trackwork_manager", None)
        if self.manager is None:
            raise RuntimeError("Show the automated B14 trackwork manager first")
        self.selected_host_identities = None

    @property
    def panel(self):
        return self.manager.crossover_panel

    def _run_with_modal_monitor(self, action, approve_questions=False):
        state = {
            "active": True,
            "seen": set(),
            "approved_questions": [],
            "unexpected_dialogs": [],
        }

        def monitor():
            if not state["active"]:
                return
            boxes = [
                widget for widget in QtWidgets.QApplication.topLevelWidgets()
                if isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible()
            ]
            for box in boxes:
                identity = id(box)
                if identity in state["seen"]:
                    continue
                state["seen"].add(identity)
                record = {
                    "title": box.windowTitle(),
                    "text": box.text(),
                    "informative_text": box.informativeText(),
                    "detailed_text": box.detailedText(),
                }
                yes_button = box.button(QtWidgets.QMessageBox.StandardButton.Yes)
                if approve_questions and yes_button is not None:
                    state["approved_questions"].append(record)
                    yes_button.click()
                else:
                    state["unexpected_dialogs"].append(record)
                    box.accept()
            QtCore.QTimer.singleShot(25, monitor)

        QtCore.QTimer.singleShot(0, monitor)
        try:
            action()
        finally:
            state["active"] = False

        if state["unexpected_dialogs"]:
            first = state["unexpected_dialogs"][0]
            raise RuntimeError(
                "Unexpected B14 dialog: {} — {}".format(first["title"], first["text"])
            )
        return state["approved_questions"]

    def _selected_config(self):
        config = self.panel.current_config()
        if not isinstance(config, dict):
            raise RuntimeError("B14 did not leave a selected crossover configuration")
        return config

    def _state(self, stage, questions=None):
        config = self._selected_config()
        return {
            "stage": stage,
            "crossover_id": str(config.get("crossover_id") or ""),
            "object_count": len(self.panel.doc.Objects),
            "b4_status": str(config.get("b4_status") or ""),
            "chair_analysis_status": str(config.get("chair_analysis_status") or ""),
            "chair_model_support_status": str(config.get("chair_model_support_status") or ""),
            "chair_2d_layout_status": str(config.get("chair_2d_layout_status") or ""),
            "chair_solid_status": str(config.get("chair_solid_status") or ""),
            "integration_active": bool(config.get("integration_active")),
            "host_selection": dict(self.selected_host_identities or {}),
            "approved_questions": list(questions or []),
        }

    def _require(self, condition, message):
        if not condition:
            raise RuntimeError(message)

    def run_stage(self, stage, chainage=DEFAULT_CHAINAGE_MM):
        name = str(stage).strip().lower()
        panel = self.panel
        if name == "geometry":
            self.manager.mode_tabs.setCurrentIndex(1)
            panel.refresh_hosts()
            if len(panel.hosts) < 2:
                raise RuntimeError("The benchmark base requires two recognised host centrelines")
            selection = select_crossover_hosts(
                panel.hosts,
                self.module.object_string_property,
                self.module._integer_object_property,
            )
            panel.host_a_combo.setCurrentIndex(selection["a"])
            panel.host_b_combo.setCurrentIndex(selection["b"])
            self.selected_host_identities = {
                "host_a": selection["host_a_identity"],
                "host_b": selection["host_b_identity"],
                "placement_basis": "Host A centreline identity plus chainage",
            }
            panel.chainage_box.setValue(float(chainage))
            result = panel.preview_geometry()
            if result is None:
                raise RuntimeError("Crossover preview failed: {}".format(panel.diagnostics.toPlainText()))
            questions = self._run_with_modal_monitor(panel.create_crossover, approve_questions=True)
            state = self._state(name, questions)
            if state["crossover_id"] != "XO-001":
                raise RuntimeError("Expected the first managed crossover to be XO-001")
            return state
        if name == "timber":
            self._run_with_modal_monitor(panel.apply_b4_timbering)
            state = self._state(name)
            self._require(
                state["b4_status"] == self.module.CROSSOVER_B4_STATUS_CLEAR,
                "Automatic timbering did not reach the resolved state: {}".format(state["b4_status"]),
            )
            return state
        if name == "chairs":
            self._run_with_modal_monitor(panel.chair_analysis_panel.run_analysis)
            state = self._state(name)
            self._require(
                state["chair_analysis_status"] == self.module.CHAIR_STATUS_ASSIGNMENTS_VALIDATED,
                "Chair analysis did not validate: {}".format(state["chair_analysis_status"]),
            )
            return state
        if name == "support":
            self._run_with_modal_monitor(panel.chair_analysis_panel.prepare_model_support)
            state = self._state(name)
            self._require(
                state["chair_model_support_status"] in (
                    self.module.CHAIR_MODEL_SUPPORT_STATUS_CLEAR,
                    self.module.CHAIR_MODEL_SUPPORT_STATUS_APPLIED,
                ),
                "Model timber support was not prepared: {}".format(state["chair_model_support_status"]),
            )
            return state
        if name == "layout":
            self._run_with_modal_monitor(panel.chair_analysis_panel.build_2d_layout)
            state = self._state(name)
            self._require(
                state["chair_2d_layout_status"] == self.module.CHAIR_2D_LAYOUT_STATUS_VALIDATED,
                "2D chair layout did not validate: {}".format(state["chair_2d_layout_status"]),
            )
            return state
        if name == "integration":
            questions = self._run_with_modal_monitor(
                panel.integrate_selected_crossover,
                approve_questions=True,
            )
            state = self._state(name, questions)
            self._require(state["integration_active"], "Host integration did not become active")
            return state
        if name == "solids":
            self._run_with_modal_monitor(panel.chair_analysis_panel.generate_solids)
            state = self._state(name)
            self._require(
                state["chair_solid_status"] == self.module.CHAIR_SOLID_STATUS_FIT_VALIDATED,
                "Chair solids did not reach fit-validated state: {}".format(state["chair_solid_status"]),
            )
            return state
        raise ValueError("Unknown B14 benchmark stage: {}".format(stage))

    def report(self):
        return self.module._workflow_performance_report(self.panel)

    def save(self):
        self.panel.doc.save()
        return self.panel.doc.FileName


driver_module = types.ModuleType("tracktemplate_b14_benchmark_driver")
driver_module.driver = B14BenchmarkDriver()
sys.modules[driver_module.__name__] = driver_module
print(json.dumps({
    "state": "loaded",
    "module": driver_module.__name__,
    "document": driver_module.driver.panel.doc.Name,
}, sort_keys=True))
