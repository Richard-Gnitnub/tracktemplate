"""Register the deterministic completed-document B14 warm-reuse driver."""

import collections
import hashlib
import json
import os
import sys
import time
import types

from tools.freecad_bridge.b14_recipe import HOST_A_IDENTITY, HOST_B_IDENTITY, host_identity


MODULE_NAME = "tracktemplate_b14_session"
COLD_DRIVER_MODULE = "tracktemplate_b14_benchmark_driver"
WARM_DRIVER_MODULE = "tracktemplate_b14_warm_reuse_driver"
EXPECTED_OBJECT_COUNT = 27
EXPECTED_ROLE_COUNTS = {
    "Centreline": 2,
    "ChairProductionSolids": 1,
    "CrossoverConstructionMarks": 1,
    "CrossoverGroup": 1,
    "CrossoverHostIntegrationGroup": 1,
    "CrossoverHostIntegrationSettings": 1,
    "CrossoverHybridResolvedTimberGeometry": 1,
    "CrossoverIntegratedHostDisplay": 1,
    "CrossoverIntegratedHostOutline": 1,
    "CrossoverIntegratedHostTemplate": 1,
    "CrossoverIntegratedResolvedTimberGeometry": 1,
    "CrossoverPlanOutline": 1,
    "CrossoverRailGeometry": 1,
    "CrossoverSettings": 1,
    "CrossoverTemplate": 1,
    "CrossoverTimberAnalysisDisplay": 1,
    "CrossoverTurnoutASettings": 1,
    "CrossoverTurnoutBSettings": 1,
    "CrossoverUnresolvedTimberReference": 1,
    "Group": 1,
    "MaterialLengthReport": 1,
    "ProductionSchedule": 1,
    "ProductionSource": 1,
    "ProductionSourceGroup": 1,
    "Settings": 1,
    "Template": 1,
}
EXPECTED_TYPE_COUNTS = {
    "App::DocumentObjectGroup": 5,
    "Part::Feature": 20,
    "Spreadsheet::Sheet": 2,
}


def _rss_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return None


class B14WarmReuseDriver:
    """Measure genuine unchanged-result solid reuse through the operator method."""

    def __init__(self):
        self.module = sys.modules.get(MODULE_NAME)
        cold_module = sys.modules.get(COLD_DRIVER_MODULE)
        if self.module is None or cold_module is None:
            raise RuntimeError("Load B14 and the cold benchmark driver first")
        self.cold_driver = cold_module.driver
        self.panel = self.cold_driver.panel
        self.document = self.panel.doc
        self.solid_panel = self.panel.chair_analysis_panel
        self.iteration_count = 0

    def _select_crossover(self):
        self.panel.refresh_crossovers("XO-001")
        config = self.panel.current_config()
        if not isinstance(config, dict) or str(config.get("crossover_id") or "") != "XO-001":
            raise RuntimeError("The completed warm fixture does not select XO-001")
        return config

    def _config(self):
        config = self.module.crossover_config_by_id(self.document, "XO-001")
        if not isinstance(config, dict):
            raise RuntimeError("The completed warm fixture has no XO-001 configuration")
        return config

    def _object_inventory(self):
        records = []
        role_counts = collections.Counter()
        type_counts = collections.Counter()
        for obj in sorted(self.document.Objects, key=lambda item: str(item.Name)):
            role = str(self.module.object_string_property(obj, "GeneratedRole", "") or "")
            type_id = str(getattr(obj, "TypeId", "Unknown"))
            if role:
                role_counts[role] += 1
            type_counts[type_id] += 1
            records.append({
                "name": str(obj.Name),
                "type_id": type_id,
                "role": role,
            })
        encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {
            "object_count": len(records),
            "role_counts": dict(sorted(role_counts.items())),
            "type_counts": dict(sorted(type_counts.items())),
            "identity_sha256": hashlib.sha256(encoded).hexdigest(),
        }

    @staticmethod
    def _shape_fingerprint(obj):
        if obj is None:
            return None
        shape = getattr(obj, "Shape", None)
        if shape is None:
            return None
        bounds = getattr(shape, "BoundBox", None)
        return {
            "object_name": str(obj.Name),
            "is_null": bool(shape.isNull()),
            "is_valid": bool(shape.isValid()),
            "hash_code": int(shape.hashCode()),
            "solid_count": len(shape.Solids),
            "face_count": len(shape.Faces),
            "edge_count": len(shape.Edges),
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

    def _stored_snapshot(self):
        config = self._config()
        cached = self.module._chair_read_cached_result(
            self.document,
            "crossover",
            "XO-001",
        )
        solid = self.module._chair_solid_object(
            self.document,
            "crossover",
            "XO-001",
        )
        physical = self.module._chair_physical_state_from_object(solid)
        host_a = self.document.getObject(str(config.get("host_a_object") or ""))
        host_b = self.document.getObject(str(config.get("host_b_object") or ""))
        support = dict((cached or {}).get("model_timber_support_state") or {})
        layout = dict((cached or {}).get("chair_2d_layout_state") or {})
        return {
            "inventory": self._object_inventory(),
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
            "b4_status": str(config.get("b4_status") or ""),
            "chair_analysis_status": str(config.get("chair_analysis_status") or ""),
            "chair_model_support_status": str(config.get("chair_model_support_status") or ""),
            "chair_2d_layout_status": str(config.get("chair_2d_layout_status") or ""),
            "chair_solid_status": str(config.get("chair_solid_status") or ""),
            "integration_active": bool(config.get("integration_active")),
            "analysis_signature": str((cached or {}).get("geometry_signature") or ""),
            "support_signature": str(support.get("support_signature") or ""),
            "layout_signature": str(layout.get("layout_signature") or ""),
            "solid_signature": str((physical or {}).get("solid_signature") or ""),
            "solid_generated_count": int((physical or {}).get("generated_count") or 0),
            "solid_shape": self._shape_fingerprint(solid),
        }

    def _effective_statuses(self):
        config = self._config()
        return {
            "b4": self.module.crossover_b4_effective_status(self.document, config),
            "chair_analysis": self.module.chair_analysis_effective_status(
                self.document,
                "crossover",
                config,
            ),
            "model_support": self.module.chair_model_support_effective_status(
                self.document,
                "crossover",
                config,
            ),
            "layout_2d": self.module.chair_2d_layout_effective_status(
                self.document,
                "crossover",
                config,
            ),
            "solid": self.module.chair_solid_effective_status(
                self.document,
                "crossover",
                config,
            ),
            "integration": self.module.crossover_host_integration_effective_status(
                self.document,
                config,
            ),
        }

    def _assert_completed(self, snapshot, statuses):
        inventory = snapshot["inventory"]
        if inventory["object_count"] != EXPECTED_OBJECT_COUNT:
            raise RuntimeError("Expected 27 completed objects, found {}".format(inventory["object_count"]))
        if inventory["role_counts"] != EXPECTED_ROLE_COUNTS:
            raise RuntimeError("Unexpected completed generated roles: {}".format(inventory["role_counts"]))
        if inventory["type_counts"] != EXPECTED_TYPE_COUNTS:
            raise RuntimeError("Unexpected completed object types: {}".format(inventory["type_counts"]))
        for label, actual, expected in (
            ("Host A", snapshot["host_a"], HOST_A_IDENTITY),
            ("Host B", snapshot["host_b"], HOST_B_IDENTITY),
        ):
            if any(actual.get(key) != value for key, value in expected.items()):
                raise RuntimeError("{} identity changed: {}".format(label, actual))
        expected_statuses = {
            "b4": self.module.CROSSOVER_B4_STATUS_CLEAR,
            "chair_analysis": self.module.CHAIR_STATUS_ASSIGNMENTS_VALIDATED,
            "model_support": self.module.CHAIR_MODEL_SUPPORT_STATUS_APPLIED,
            "layout_2d": self.module.CHAIR_2D_LAYOUT_STATUS_VALIDATED,
            "solid": self.module.CHAIR_SOLID_STATUS_FIT_VALIDATED,
            "integration": self.module.CROSSOVER_INTEGRATION_STATUS_ACTIVE,
        }
        if statuses != expected_statuses:
            raise RuntimeError(
                "Completed warm-fixture statuses changed: {} (expected {})".format(
                    statuses,
                    expected_statuses,
                )
            )
        if snapshot["toe_chainage_a_mm"] != 746.298:
            raise RuntimeError("Unexpected Host A chainage: {}".format(snapshot["toe_chainage_a_mm"]))
        if not snapshot["integration_active"]:
            raise RuntimeError("The warm fixture is not integrated with its host templates")
        for key in ("analysis_signature", "support_signature", "layout_signature", "solid_signature"):
            if not snapshot[key]:
                raise RuntimeError("The warm fixture has no {}".format(key))
        shape = snapshot["solid_shape"] or {}
        if shape.get("is_null") or not shape.get("is_valid") or not shape.get("solid_count"):
            raise RuntimeError("The warm fixture has no valid retained chair solid")

    def prepare(self):
        self._select_crossover()
        before = self._stored_snapshot()
        status_started = time.perf_counter()
        statuses = self._effective_statuses()
        status_elapsed = time.perf_counter() - status_started
        self._assert_completed(before, statuses)
        return {
            "state": "prepared",
            "placement_basis": "Persisted Host A centreline identity plus chainage",
            "snapshot": before,
            "statuses": statuses,
            "status_validation_wall_seconds": status_elapsed,
        }

    def run_iteration(self, label):
        self._select_crossover()
        before = self._stored_snapshot()
        original = self.module.generate_supported_chair_solids
        captured = []

        def capture_result(*args, **kwargs):
            result = original(*args, **kwargs)
            captured.append(dict(result or {}))
            return result

        rss_before = _rss_mb()
        process_before = time.process_time()
        wall_before = time.perf_counter()
        self.module.generate_supported_chair_solids = capture_result
        try:
            questions = self.cold_driver._run_with_modal_monitor(
                self.solid_panel.generate_solids,
            )
        finally:
            self.module.generate_supported_chair_solids = original
        action_wall = time.perf_counter() - wall_before
        action_cpu = time.process_time() - process_before
        rss_after_action = _rss_mb()

        if questions:
            raise RuntimeError("The warm reuse action unexpectedly asked a question")
        if len(captured) != 1:
            raise RuntimeError("Expected one supported-chair generation result, got {}".format(len(captured)))
        result = captured[0]
        if not bool(result.get("unchanged_result_reused")):
            raise RuntimeError("B14 did not report unchanged supported-chair result reuse")

        after_action = self._stored_snapshot()
        status_started = time.perf_counter()
        statuses = self._effective_statuses()
        status_elapsed = time.perf_counter() - status_started
        after_validation = self._stored_snapshot()
        self._assert_completed(after_validation, statuses)

        stable_keys = (
            "inventory",
            "host_a",
            "host_b",
            "toe_chainage_a_mm",
            "analysis_signature",
            "support_signature",
            "layout_signature",
            "solid_signature",
            "solid_generated_count",
            "solid_shape",
        )
        changed = [
            key for key in stable_keys
            if before.get(key) != after_action.get(key)
            or before.get(key) != after_validation.get(key)
        ]
        if changed:
            raise RuntimeError("Warm reuse changed stable document state: {}".format(changed))
        if str(result.get("solid_signature") or "") != before["solid_signature"]:
            raise RuntimeError("Warm reuse returned a different solid signature")
        if int(result.get("generated_count") or 0) != before["solid_generated_count"]:
            raise RuntimeError("Warm reuse returned a different chair count")

        self.iteration_count += 1
        rss_after_validation = _rss_mb()
        return {
            "label": str(label),
            "iteration": self.iteration_count,
            "operator_action": "Generate supported chair solids",
            "action_wall_seconds": action_wall,
            "action_process_cpu_seconds": action_cpu,
            "action_rss_before_mb": rss_before,
            "action_rss_after_mb": rss_after_action,
            "action_rss_delta_mb": (
                rss_after_action - rss_before
                if rss_before is not None and rss_after_action is not None
                else None
            ),
            "function_total_time_ms": float(result.get("total_time_ms") or 0.0),
            "unchanged_result_reused": True,
            "status_validation_wall_seconds": status_elapsed,
            "rss_after_validation_mb": rss_after_validation,
            "statuses": statuses,
            "object_count": after_validation["inventory"]["object_count"],
            "object_identity_sha256": after_validation["inventory"]["identity_sha256"],
            "solid_signature": after_validation["solid_signature"],
            "solid_shape_hash_code": after_validation["solid_shape"]["hash_code"],
            "solid_generated_count": after_validation["solid_generated_count"],
        }


driver_module = types.ModuleType(WARM_DRIVER_MODULE)
driver_module.driver = B14WarmReuseDriver()
sys.modules[driver_module.__name__] = driver_module
print(json.dumps({
    "state": "loaded",
    "module": driver_module.__name__,
    "document": driver_module.driver.document.Name,
    "process_id": os.getpid(),
}, sort_keys=True))
