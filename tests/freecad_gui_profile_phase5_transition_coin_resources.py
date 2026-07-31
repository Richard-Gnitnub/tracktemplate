"""Profile a bounded Transition Coin fixture in the qualified FreeCAD GUI."""

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
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets


ROOT = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
sys.path.insert(0, str(ROOT))

from tests.phase5_transition_coin_gui_harness import (  # noqa: E402
    _process_gui as _shared_process_gui,
)
from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)


_process_gui = functools.partial(
    _shared_process_gui,
    Gui.updateGui,
    QtWidgets.QApplication.processEvents,
)


PROFILE_ID = "phase5-transition-coin-resource-profile-v1"
OBJECT_COUNT = 32
PREVIEW_SEGMENT_COUNT = 32
WARM_REPETITIONS = 3


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


def _timed_recompute(document):
    wall_started = time.perf_counter_ns()
    cpu_started = time.process_time_ns()
    result = document.recompute()
    return {
        "count": 1,
        "process_cpu_ms": (
            time.process_time_ns() - cpu_started
        ) / 1.0e6,
        "result": bool(result),
        "wall_ms": (
            time.perf_counter_ns() - wall_started
        ) / 1.0e6,
    }


def _state(index):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = 300.0 + float(index * 2)
    intent = api.TransitionIntent(
        transition_id=(
            "transition:phase5:coin-resource:{:02d}".format(index)
        ),
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 Coin resource {:02d}".format(index),
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


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


def _count_coin_layers(roots):
    layer_count = 0
    for selection_root in roots:
        assert int(selection_root.getNumChildren()) == 1
        scene_root = selection_root.getChild(0)
        layer_count += int(scene_root.getNumChildren())
    return layer_count


def _identity_record(record):
    obj = record["object"]
    state = record["state"]
    proxy = record["proxy"]
    selection = proxy.selection_for_element(proxy.element_name)
    return {
        "domain_id": selection.domain_id,
        "element_name": proxy.element_name,
        "layer_id": selection.layer_id,
        "object_name": str(obj.Name),
        "source_signature": proxy.source_signature,
        "state_json_sha256": hashlib.sha256(
            str(
                getattr(
                    obj,
                    adapter.FREECAD_STATE_JSON_PROPERTY,
                )
            ).encode("utf-8")
        ).hexdigest(),
        "style_signature": proxy.style_signature,
        "transition_id": state.intent.transition_id,
        "visual_id": selection.visual_id,
    }


def _identity_digest(records):
    payload = json.dumps(
        [_identity_record(record) for record in records],
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _snapshot(document, records):
    roots = [record["proxy"].selection_root for record in records]
    objects = tuple(document.Objects)
    snapshot = {
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
        "active_coin_scene_node_count": _count_coin_nodes(roots),
        "display_modes_added": sum(
            len(tuple(record["object"].ViewObject.listDisplayModes()))
            - record["display_mode_count_before"]
            for record in records
        ),
        "document_object_count": len(objects),
        "identity_digest": _identity_digest(records),
        "logical_layer_count": _count_coin_layers(roots),
        "part_shape_count": sum(
            "Shape" in tuple(obj.PropertiesList) for obj in objects
        ),
        "proxy_count": len(records),
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
    assert snapshot["document_object_count"] == OBJECT_COUNT
    assert snapshot["logical_layer_count"] == OBJECT_COUNT
    assert snapshot["part_shape_count"] == 0
    assert snapshot["proxy_count"] == OBJECT_COUNT
    assert snapshot["display_modes_added"] == OBJECT_COUNT
    assert snapshot["root_children_added"] == 0
    assert snapshot["switch_children_added"] == OBJECT_COUNT
    assert snapshot["cache_regeneration_count"] == OBJECT_COUNT
    for record in records:
        obj = record["object"]
        state = record["state"]
        proxy = record["proxy"]
        coordinator = record["coordinator"]
        assert obj.TypeId == "App::FeaturePython"
        assert obj.Proxy is None
        assert adapter.read_transition_object(obj) == state
        assert proxy.attached is True
        assert coordinator.cache.status(
            state,
            coordinator.specification.derived_request(),
        ) == "current"
    return snapshot


def _build_fixture(qualification):
    document = App.newDocument("Phase5TransitionCoinResourceProfile")
    document.UndoMode = 1
    store = adapter.FreeCADTransitionStore(qualification)
    states = tuple(_state(index) for index in range(OBJECT_COUNT))
    objects = store.create_many(document, states)
    specification = api.TransitionPreviewSpecification(
        segment_count=PREVIEW_SEGMENT_COUNT
    )
    style = renderer.TransitionCoinStyle(
        line_color_rgb=(0.9, 0.05, 0.02),
        line_width=3.0,
    )
    records = []
    for obj, state in zip(objects, states):
        display_mode_count_before = len(
            tuple(obj.ViewObject.listDisplayModes())
        )
        root_child_count_before = int(
            obj.ViewObject.RootNode.getNumChildren()
        )
        switch_child_count_before = int(
            obj.ViewObject.SwitchNode.getNumChildren()
        )
        coordinator = _PreviewCoordinator(specification)
        artifact = coordinator.artifact_for_state(state)
        proxy = viewprovider.TransitionCoinViewProviderFixture(
            obj.ViewObject,
            artifact,
            style,
            coin,
            state_reader=adapter.read_transition_object,
            artifact_for_state=coordinator.artifact_for_state,
            source_property_name=adapter.FREECAD_STATE_JSON_PROPERTY,
        )
        obj.ViewObject.DisplayMode = proxy.display_mode
        records.append({
            "coordinator": coordinator,
            "display_mode_count_before": display_mode_count_before,
            "object": obj,
            "proxy": proxy,
            "root_child_count_before": root_child_count_before,
            "state": state,
            "switch_child_count_before": switch_child_count_before,
        })
    recompute = _timed_recompute(document)
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    _process_gui()
    return document, records, recompute


def _refresh_fixture(document, records):
    changed_count = sum(
        record["proxy"].refresh_for_state(record["state"]) is True
        for record in records
    )
    recompute = _timed_recompute(document)
    view = Gui.getDocument(document.Name).activeView()
    view.redraw()
    _process_gui()
    return {
        "explicit_recompute": recompute,
        "refresh_changed_count": changed_count,
    }


def _warm_observation(document, records, measured):
    before = _snapshot(document, records)
    if measured:
        action, measurement = _measure(
            lambda: _refresh_fixture(document, records)
        )
    else:
        action = _refresh_fixture(document, records)
        measurement = {}
    after = _snapshot(document, records)
    observation = dict(measurement)
    observation.update(action)
    observation.update({
        "cache_regeneration_delta": (
            after["cache_regeneration_count"]
            - before["cache_regeneration_count"]
        ),
        "cache_request_delta": (
            after["cache_request_count"]
            - before["cache_request_count"]
        ),
        "cache_reuse_delta": (
            after["cache_reuse_count"]
            - before["cache_reuse_count"]
        ),
        "snapshot": after,
    })
    assert observation["refresh_changed_count"] == 0
    assert observation["cache_regeneration_delta"] == 0
    assert observation["cache_request_delta"] == OBJECT_COUNT
    assert observation["cache_reuse_delta"] == OBJECT_COUNT
    assert after["identity_digest"] == before["identity_digest"]
    assert (
        after["active_coin_scene_node_count"]
        == before["active_coin_scene_node_count"]
    )
    return observation


def _dispose_fixture(document, records):
    disposed = 0
    discarded_caches = 0
    for record in records:
        proxy = record["proxy"]
        if proxy.dispose():
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


def validate():
    if App.listDocuments():
        raise RuntimeError(
            "Phase 5 resource profile requires an empty FreeCAD session"
        )
    qualification = bootstrap.require_qualified_runtime(
        ROOT
        / "reference"
        / "contracts"
        / "phase1-compatibility.json"
    )
    document = None
    records = []
    try:
        cold_result, cold = _measure(
            lambda: _build_fixture(qualification)
        )
        document, records, recompute = cold_result
        cold["explicit_recompute"] = recompute
        cold["snapshot"] = _snapshot(document, records)

        warmup = _warm_observation(
            document,
            records,
            measured=False,
        )
        warm = [
            _warm_observation(document, records, measured=True)
            for _iteration in range(WARM_REPETITIONS)
        ]
        cleanup, cleanup_measurement = _measure(
            lambda: _dispose_fixture(document, records)
        )
        cleanup.update(cleanup_measurement)
        document = None
        records = []

        payload = {
            "cleanup": cleanup,
            "cold": cold,
            "fixture": {
                "logical_object_count": OBJECT_COUNT,
                "preview_segment_count": PREVIEW_SEGMENT_COUNT,
                "resource_budget_status": "not-accepted",
                "warm_repetitions": WARM_REPETITIONS,
            },
            "freecad_version": ".".join(App.Version()[:3]),
            "profile_id": PROFILE_ID,
            "schema_version": 1,
            "starting_state": (
                "fresh isolated GUI process, empty document set, "
                "new document and empty per-object preview caches"
            ),
            "warm": warm,
            "warmup": warmup,
        }
        print(
            "TRACKTEMPLATE_PHASE5_COIN_RESOURCE_SAMPLE="
            + json.dumps(payload, sort_keys=True)
        )
    finally:
        for record in records:
            proxy = record["proxy"]
            if proxy.attached:
                proxy.dispose()
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)


validate()
