"""Register the completed-document B14-to-B15 GUI acceptance driver."""

import collections
import copy
import hashlib
import json
import os
import sys
import time
import types

import FreeCAD as App

from tools.freecad_bridge.b14_recipe import HOST_A_IDENTITY, HOST_B_IDENTITY, host_identity

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets


MODULE_NAME = "tracktemplate_b15_session"
DRIVER_MODULE = "tracktemplate_b15_acceptance_driver"
EXPECTED_CROSSOVER_ID = "XO-001"
EXPECTED_CHAINAGE_MM = 746.298
EXPECTED_COMPLETED_OBJECTS = 27
EXPECTED_SOLID_COUNT = 119


def _rss_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return None


def _canonical(value):
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, set):
        return sorted(_canonical(item) for item in value)
    if isinstance(value, float):
        return round(value, 9)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _sha256(value):
    encoded = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class B15AcceptanceDriver:
    """Exercise B15's declared delta on a disposable completed B14 document."""

    def __init__(self):
        self.module = sys.modules.get(MODULE_NAME)
        if self.module is None:
            raise RuntimeError("Load B15 before registering its acceptance driver")
        self.manager = getattr(self.module, "_automation_trackwork_manager", None)
        if self.manager is None:
            raise RuntimeError("Show the B15 trackwork manager first")
        self.baseline = None

    @property
    def panel(self):
        return self.manager.crossover_panel

    @property
    def document(self):
        return self.panel.doc

    def _require(self, condition, message):
        if not condition:
            raise RuntimeError(message)

    def _select(self):
        self.manager.mode_tabs.setCurrentIndex(1)
        self.panel.refresh_crossovers(EXPECTED_CROSSOVER_ID)
        config = self.panel.current_config()
        if not isinstance(config, dict):
            raise RuntimeError("B15 did not select a crossover configuration")
        if str(config.get("crossover_id") or "") != EXPECTED_CROSSOVER_ID:
            raise RuntimeError("The completed document does not select XO-001")
        return config

    def _run_with_modal_monitor(self, action):
        state = {"active": True, "seen": set(), "unexpected": []}

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
                state["unexpected"].append({
                    "title": box.windowTitle(),
                    "text": box.text(),
                    "informative_text": box.informativeText(),
                    "detailed_text": box.detailedText(),
                })
                box.accept()
            QtCore.QTimer.singleShot(25, monitor)

        QtCore.QTimer.singleShot(0, monitor)
        try:
            action()
        finally:
            state["active"] = False
        if state["unexpected"]:
            first = state["unexpected"][0]
            raise RuntimeError(
                "Unexpected B15 dialog: {} — {}".format(first["title"], first["text"])
            )

    @staticmethod
    def _shape_semantics(obj):
        shape = getattr(obj, "Shape", None)
        if shape is None:
            return None
        try:
            if shape.isNull():
                return None
            bounds = shape.BoundBox
            return {
                "valid": bool(shape.isValid()),
                "solids": len(shape.Solids),
                "faces": len(shape.Faces),
                "edges": len(shape.Edges),
                "vertices": len(shape.Vertexes),
                "bounds": [
                    round(float(value), 6)
                    for value in (
                        bounds.XMin,
                        bounds.YMin,
                        bounds.ZMin,
                        bounds.XMax,
                        bounds.YMax,
                        bounds.ZMax,
                    )
                ],
            }
        except Exception as error:
            return {"shape_error": "{}: {}".format(type(error).__name__, error)}

    def _inventory(self):
        role_counts = collections.Counter()
        type_counts = collections.Counter()
        records = []
        for obj in sorted(self.document.Objects, key=lambda item: str(item.Name)):
            role = str(self.module.object_string_property(obj, "GeneratedRole", "") or "")
            type_id = str(getattr(obj, "TypeId", "Unknown"))
            if role:
                role_counts[role] += 1
            type_counts[type_id] += 1
            records.append({"name": str(obj.Name), "type_id": type_id, "role": role})
        return {
            "object_count": len(records),
            "role_counts": dict(sorted(role_counts.items())),
            "type_counts": dict(sorted(type_counts.items())),
            "identity_sha256": _sha256(records),
        }

    def _non_chair_shapes(self):
        records = []
        for obj in sorted(self.document.Objects, key=lambda item: str(item.Name)):
            role = str(self.module.object_string_property(obj, "GeneratedRole", "") or "")
            type_id = str(getattr(obj, "TypeId", "Unknown"))
            if role.startswith("Chair") or type_id == "App::DocumentObjectGroup":
                continue
            shape = self._shape_semantics(obj)
            if shape is None:
                continue
            records.append({
                "name": str(obj.Name),
                "role": role,
                "type_id": type_id,
                "shape": shape,
            })
        return {"count": len(records), "semantic_sha256": _sha256(records), "records": records}

    def _analysis(self):
        return self.module._chair_read_cached_result(
            self.document,
            "crossover",
            EXPECTED_CROSSOVER_ID,
        ) or {}

    def _analysis_core(self, analysis):
        result = dict(analysis or {})
        analytical_keys = (
            "entity_id",
            "entity_kind",
            "findings",
            "geometry_signature",
            "model_timber_support_plan",
            "positions",
            "production_geometry_changed",
            "schema_version",
            "settings",
            "source_basis",
            "status",
            "summary",
        )
        core = {
            key: copy.deepcopy(result[key])
            for key in analytical_keys
            if key in result
        }
        return {
            "position_count": len(list(core.get("positions") or [])),
            "finding_count": len(list(core.get("findings") or [])),
            "semantic_sha256": _sha256(core),
        }

    def _support(self, analysis):
        state = copy.deepcopy(dict((analysis or {}).get("model_timber_support_state") or {}))
        for key in (
            "macro_version",
            "status",
            "support_signature",
            "unchanged_result_reused",
            "reuse_reason",
        ):
            state.pop(key, None)
        return {
            "adjustment_count": len(list(state.get("adjustments") or [])),
            "semantic_sha256": _sha256(state),
        }

    def _layout(self):
        objects = self.module._chair_2d_objects(
            self.document,
            "crossover",
            EXPECTED_CROSSOVER_ID,
        )
        records = []
        group_revisions = []
        shape_object_count = 0
        for obj in objects:
            role = str(self.module.object_string_property(obj, "GeneratedRole", "") or "")
            revision = int(getattr(obj, "Chair2DRepresentationRevision", 0) or 0)
            if role == self.module.CHAIR_2D_LAYOUT_GROUP_ROLE:
                group_revisions.append(revision)
            shape = self._shape_semantics(obj)
            shape_object_count += int(shape is not None)
            records.append({
                "name": str(obj.Name),
                "role": role,
                "type_id": str(getattr(obj, "TypeId", "Unknown")),
                "revision": revision,
                "shape": shape,
            })
        records.sort(key=lambda item: (item["role"], item["name"]))
        return {
            "object_count": len(records),
            "shape_object_count": shape_object_count,
            "group_revisions": sorted(group_revisions),
            "identity_sha256": _sha256([
                {key: item[key] for key in ("name", "role", "type_id")}
                for item in records
            ]),
            "semantic_sha256": _sha256(records),
        }

    def _solid(self):
        obj = self.module._chair_solid_object(
            self.document,
            "crossover",
            EXPECTED_CROSSOVER_ID,
        )
        state = self.module._chair_physical_state_from_object(obj) if obj is not None else {}
        result = {
            "object_name": str(obj.Name) if obj is not None else "",
            "generated_count": int((state or {}).get("generated_count") or 0),
            "analytical_only_count": int((state or {}).get("analytical_only_count") or 0),
            "shape": self._shape_semantics(obj) if obj is not None else None,
        }
        result["semantic_sha256"] = _sha256(result)
        return result

    def _snapshot(self):
        config = self._select()
        analysis = self._analysis()
        host_a = self.document.getObject(str(config.get("host_a_object") or ""))
        host_b = self.document.getObject(str(config.get("host_b_object") or ""))
        return {
            "document": str(self.document.Name),
            "file_name": str(self.document.FileName),
            "version": str(self.module.MACRO_VERSION_NUMBER),
            "inventory": self._inventory(),
            "host_a": host_identity(
                host_a,
                self.module.object_string_property,
                self.module._integer_object_property,
            ),
            "host_b": host_identity(
                host_b,
                self.module.object_string_property,
                self.module._integer_object_property,
            ),
            "toe_chainage_a_mm": round(float(config.get("toe_chainage_a") or 0.0), 3),
            "integration_active": bool(config.get("integration_active")),
            "statuses": {
                "b4": str(config.get("b4_status") or ""),
                "analysis": str(config.get("chair_analysis_status") or ""),
                "support": str(config.get("chair_model_support_status") or ""),
                "layout": str(config.get("chair_2d_layout_status") or ""),
                "solid": str(config.get("chair_solid_status") or ""),
            },
            "analysis_core": self._analysis_core(analysis),
            "support": self._support(analysis),
            "layout": self._layout(),
            "solid": self._solid(),
            "non_chair_shapes": self._non_chair_shapes(),
        }

    def _assert_hosts_and_geometry(self, snapshot):
        for label, actual, expected in (
            ("Host A", snapshot["host_a"], HOST_A_IDENTITY),
            ("Host B", snapshot["host_b"], HOST_B_IDENTITY),
        ):
            if any(actual.get(key) != value for key, value in expected.items()):
                raise RuntimeError("{} identity changed: {}".format(label, actual))
        self._require(
            snapshot["toe_chainage_a_mm"] == EXPECTED_CHAINAGE_MM,
            "Host A chainage changed: {}".format(snapshot["toe_chainage_a_mm"]),
        )
        self._require(snapshot["integration_active"], "The completed crossover is no longer integrated")

    def _assert_inherited_semantics(self, snapshot):
        self._assert_hosts_and_geometry(snapshot)
        self._require(
            snapshot["analysis_core"]["semantic_sha256"]
            == self.baseline["analysis_core"]["semantic_sha256"],
            "B15 changed the inherited chair-position/assignment result",
        )
        if (
            snapshot["non_chair_shapes"]["semantic_sha256"]
            != self.baseline["non_chair_shapes"]["semantic_sha256"]
        ):
            before = {
                item["name"]: item
                for item in self.baseline["non_chair_shapes"]["records"]
            }
            after = {
                item["name"]: item
                for item in snapshot["non_chair_shapes"]["records"]
            }
            changed = sorted(
                name for name in set(before) | set(after)
                if before.get(name) != after.get(name)
            )
            raise RuntimeError(
                "B15 changed non-chair leaf railway geometry: {}".format(changed)
            )

    def _latest_event(self):
        events = list(self.module._workflow_benchmark_events(self.panel))
        return copy.deepcopy(events[-1]) if events else {}

    def prepare(self):
        snapshot = self._snapshot()
        self._require(
            snapshot["inventory"]["object_count"] == EXPECTED_COMPLETED_OBJECTS,
            "Expected {} completed B14 objects, found {}".format(
                EXPECTED_COMPLETED_OBJECTS,
                snapshot["inventory"]["object_count"],
            ),
        )
        self._assert_hosts_and_geometry(snapshot)
        self._require(snapshot["analysis_core"]["position_count"] > 0, "No retained chair positions")
        self._require(
            snapshot["solid"]["generated_count"] == EXPECTED_SOLID_COUNT,
            "Expected {} retained supported chair solids".format(EXPECTED_SOLID_COUNT),
        )
        self._require(snapshot["solid"]["shape"] is not None, "No retained supported-chair shape")
        self.baseline = snapshot
        return {"state": "prepared", "snapshot": snapshot}

    def _captured_action(self, function_name, panel_action):
        original = getattr(self.module, function_name)
        captured = []

        def capture(*args, **kwargs):
            result = original(*args, **kwargs)
            captured.append(copy.deepcopy(dict(result or {})))
            return result

        rss_before = _rss_mb()
        process_before = time.process_time()
        wall_before = time.perf_counter()
        setattr(self.module, function_name, capture)
        try:
            self._run_with_modal_monitor(panel_action)
        finally:
            setattr(self.module, function_name, original)
        elapsed = time.perf_counter() - wall_before
        if len(captured) != 1:
            raise RuntimeError(
                "Expected one {} result, got {}".format(function_name, len(captured))
            )
        return {
            "action_wall_seconds": elapsed,
            "action_process_cpu_seconds": time.process_time() - process_before,
            "action_rss_before_mb": rss_before,
            "action_rss_after_mb": _rss_mb(),
            "result": captured[0],
            "benchmark_event": self._latest_event(),
        }

    def run_analysis(self):
        action = self._captured_action(
            "analyse_entity_chair_positions",
            self.panel.chair_analysis_panel.run_analysis,
        )
        snapshot = self._snapshot()
        self._assert_inherited_semantics(snapshot)
        self._require(
            snapshot["statuses"]["analysis"] == self.module.CHAIR_STATUS_ASSIGNMENTS_VALIDATED,
            "B15 chair analysis did not validate",
        )
        action["snapshot"] = snapshot
        return action

    def run_support(self):
        action = self._captured_action(
            "prepare_chair_model_support",
            self.panel.chair_analysis_panel.prepare_model_support,
        )
        snapshot = self._snapshot()
        self._assert_inherited_semantics(snapshot)
        self._require(
            snapshot["support"]["semantic_sha256"] == self.baseline["support"]["semantic_sha256"],
            "B15 changed the bounded model-support decisions",
        )
        self._require(
            snapshot["statuses"]["support"] in (
                self.module.CHAIR_MODEL_SUPPORT_STATUS_CLEAR,
                self.module.CHAIR_MODEL_SUPPORT_STATUS_APPLIED,
            ),
            "B15 model support did not reach a prepared state",
        )
        action["snapshot"] = snapshot
        return action

    def run_layout(self, expect_reuse=False):
        before = self._snapshot()
        action = self._captured_action(
            "build_and_validate_chair_2d_layout",
            self.panel.chair_analysis_panel.build_2d_layout,
        )
        result = action["result"]
        snapshot = self._snapshot()
        self._assert_inherited_semantics(snapshot)
        self._require(
            bool(result.get("unchanged_result_reused")) is bool(expect_reuse),
            "Unexpected B15 layout reuse result: {}".format(result),
        )
        self._require(
            snapshot["statuses"]["layout"] == self.module.CHAIR_2D_LAYOUT_STATUS_VALIDATED,
            "B15 2D layout did not validate",
        )
        self._require(
            snapshot["layout"]["group_revisions"] == [self.module.CHAIR_2D_REPRESENTATION_REVISION],
            "B15 layout representation revision was not persisted",
        )
        self._require(snapshot["layout"]["shape_object_count"] > 0, "B15 created no visible chair layout")
        if expect_reuse:
            self._require(
                snapshot["inventory"]["identity_sha256"] == before["inventory"]["identity_sha256"],
                "Unchanged B15 layout reuse changed document objects",
            )
            self._require(
                snapshot["layout"]["semantic_sha256"] == before["layout"]["semantic_sha256"],
                "Unchanged B15 layout reuse changed its displayed shapes",
            )
            self._require(
                bool(action["benchmark_event"].get("unchanged_result_reused")),
                "B15 did not report the operator-stage cache hit",
            )
        action["snapshot"] = snapshot
        return action

    def remove_solids(self):
        before = self._snapshot()
        rss_before = _rss_mb()
        process_before = time.process_time()
        wall_before = time.perf_counter()
        self._run_with_modal_monitor(self.panel.chair_analysis_panel.remove_solids)
        elapsed = time.perf_counter() - wall_before
        process_elapsed = time.process_time() - process_before
        rss_after = _rss_mb()
        snapshot = self._snapshot()
        self._assert_inherited_semantics(snapshot)
        self._require(
            snapshot["support"]["semantic_sha256"] == before["support"]["semantic_sha256"],
            "Removing retained solids changed bounded model support",
        )
        self._require(
            snapshot["layout"]["semantic_sha256"] == before["layout"]["semantic_sha256"],
            "Removing retained solids changed the B15 layout",
        )
        self._require(
            snapshot["solid"]["generated_count"] == 0,
            "The real panel did not remove retained supported-chair solids",
        )
        self._require(
            snapshot["statuses"]["solid"] == self.module.CHAIR_SOLID_STATUS_NOT_GENERATED,
            "The real panel did not persist the not-generated solid status",
        )
        return {
            "action_wall_seconds": elapsed,
            "action_process_cpu_seconds": process_elapsed,
            "action_rss_before_mb": rss_before,
            "action_rss_after_mb": rss_after,
            "snapshot": snapshot,
        }

    def run_solids(self, expect_reuse=False):
        before = self._snapshot()
        action = self._captured_action(
            "generate_supported_chair_solids",
            self.panel.chair_analysis_panel.generate_solids,
        )
        result = action["result"]
        snapshot = self._snapshot()
        self._assert_inherited_semantics(snapshot)
        self._require(
            bool(result.get("unchanged_result_reused")) is bool(expect_reuse),
            "Unexpected B15 supported-solid reuse result: {}".format(result),
        )
        self._require(
            snapshot["statuses"]["solid"] == self.module.CHAIR_SOLID_STATUS_FIT_VALIDATED,
            "B15 supported-chair solids did not validate",
        )
        self._require(
            snapshot["solid"]["generated_count"] == EXPECTED_SOLID_COUNT,
            "B15 changed the supported-chair solid count",
        )
        self._require(
            snapshot["solid"]["semantic_sha256"] == self.baseline["solid"]["semantic_sha256"],
            "B15 changed supported-chair solid topology or bounds",
        )
        if expect_reuse:
            self._require(
                snapshot["inventory"]["identity_sha256"] == before["inventory"]["identity_sha256"],
                "Unchanged B15 supported-solid reuse changed document objects",
            )
            self._require(
                snapshot["solid"]["semantic_sha256"] == before["solid"]["semantic_sha256"],
                "Unchanged B15 supported-solid reuse changed its topology or bounds",
            )
            self._require(
                bool(action["benchmark_event"].get("unchanged_result_reused")),
                "B15 did not report supported-solid operator-stage reuse",
            )
        else:
            self._require(
                not bool(action["benchmark_event"].get("unchanged_result_reused")),
                "Fresh B15 supported-solid construction was reported as reuse",
            )
        action["snapshot"] = snapshot
        return action

    def _effective_statuses(self):
        config = self.module.crossover_config_by_id(self.document, EXPECTED_CROSSOVER_ID)
        return {
            "b4": self.module.crossover_b4_effective_status(self.document, config),
            "analysis": self.module.chair_analysis_effective_status(
                self.document, "crossover", config
            ),
            "support": self.module.chair_model_support_effective_status(
                self.document, "crossover", config
            ),
            "layout": self.module.chair_2d_layout_effective_status(
                self.document, "crossover", config
            ),
            "solid": self.module.chair_solid_effective_status(
                self.document, "crossover", config
            ),
            "integration": self.module.crossover_host_integration_effective_status(
                self.document, config
            ),
        }

    def save_reopen(self):
        before = self._snapshot()
        path = str(self.document.FileName)
        self.document.save()
        try:
            self.manager.close()
        except Exception:
            pass
        old_name = str(self.document.Name)
        App.closeDocument(old_name)
        document = App.openDocument(path)
        manager = self.module.TurnoutManagerDialog(document)
        self.module._automation_trackwork_manager = manager
        self.manager = manager
        manager.show()
        manager.raise_()
        manager.activateWindow()
        self._select()
        after = self._snapshot()
        self._assert_inherited_semantics(after)
        for label, key in (
            ("document object identities", "identity_sha256"),
        ):
            self._require(
                after["inventory"][key] == before["inventory"][key],
                "Save/reopen changed {}".format(label),
            )
        self._require(
            after["layout"]["semantic_sha256"] == before["layout"]["semantic_sha256"],
            "Save/reopen changed the B15 chair representation",
        )
        self._require(
            after["solid"]["semantic_sha256"] == before["solid"]["semantic_sha256"],
            "Save/reopen changed supported-chair solids",
        )
        statuses = self._effective_statuses()
        expected = {
            "b4": self.module.CROSSOVER_B4_STATUS_CLEAR,
            "analysis": self.module.CHAIR_STATUS_ASSIGNMENTS_VALIDATED,
            "support": self.module.CHAIR_MODEL_SUPPORT_STATUS_APPLIED,
            "layout": self.module.CHAIR_2D_LAYOUT_STATUS_VALIDATED,
            "solid": self.module.CHAIR_SOLID_STATUS_FIT_VALIDATED,
            "integration": self.module.CROSSOVER_INTEGRATION_STATUS_ACTIVE,
        }
        self._require(statuses == expected, "Effective statuses changed after reopen: {}".format(statuses))
        return {"saved_path": path, "before": before, "after": after, "statuses": statuses}

    def report(self):
        return self.module._workflow_performance_report(self.panel)


driver_module = types.ModuleType(DRIVER_MODULE)
driver_module.driver = B15AcceptanceDriver()
sys.modules[driver_module.__name__] = driver_module
print(json.dumps({
    "state": "loaded",
    "module": driver_module.__name__,
    "document": driver_module.driver.document.Name,
    "process_id": os.getpid(),
}, sort_keys=True))
