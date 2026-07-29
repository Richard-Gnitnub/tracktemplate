"""Measure the bounded Phase 5 Coin candidate in a real FreeCAD GUI."""

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

from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402
from tracktemplate.presentation import (  # noqa: E402
    transition_coin_viewprovider as viewprovider,
)


SAMPLE_SENTINEL = "TRACKTEMPLATE_PHASE5_COIN_PERFORMANCE_SAMPLE="
SAMPLE_PROFILE_ID = "phase5-transition-coin-performance-sample-v1"
FIXTURE_OBJECT_COUNT = 8
PREVIEW_SEGMENT_COUNT = 32
WARM_MEASUREMENT_COUNT = 3
COLD_BOUNDARY = (
    "prepared analysed canonical states and an empty FreeCAD document through "
    "atomic object creation, empty-cache preview construction, Coin "
    "ViewProvider attachment, one explicit document recompute and first redraw"
)
WARM_BOUNDARY = (
    "unchanged canonical states and current preview caches through "
    "ViewProvider refresh and GUI event processing, after one unmeasured "
    "same-process warm-up"
)


def _state(index):
    transition_length_mm = 300.0 + 5.0 * index
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_id = "transition:phase5:performance:{:02d}".format(index + 1)
    intent = api.TransitionIntent(
        transition_id=transition_id,
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 performance transition {:02d}".format(index + 1),
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


def _current_rss_mb():
    status_path = pathlib.Path("/proc/self/status")
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024.0
    raise RuntimeError("The qualified Linux host did not report VmRSS")


def _process_gui(iterations=2):
    for _iteration in range(iterations):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()


def _mapping_count(proxies, states):
    count = 0
    for proxy, state in zip(proxies, states):
        mapping = proxy.selection_for_element(proxy.element_name)
        assert mapping.domain_id == state.intent.transition_id
        assert mapping.visual_id == (
            state.intent.transition_id + ":preview:centreline"
        )
        count += 1
    return count


def _part_shape_count(objects):
    return sum(hasattr(obj, "Shape") for obj in objects)


def _artifact_reader(cache, specification, counters):
    def artifact_for_state(state):
        previous = cache.artifact("preview")
        artifact = api.regenerate_transition_preview(
            cache,
            state,
            specification,
        )
        counters["requests"] += 1
        if previous is artifact:
            counters["reuses"] += 1
        return artifact

    return artifact_for_state


def _warm_refresh(states, objects, proxies, caches, counters):
    object_count_before = len(objects[0].Document.Objects)
    rss_before_mb = _current_rss_mb()
    node_ids_before = tuple(
        int(proxy.selection_root.getChild(0).getNodeId())
        for proxy in proxies
    )
    artifacts_before = tuple(
        cache.artifact("preview") for cache in caches
    )
    requests_before = counters["requests"]
    reuses_before = counters["reuses"]

    wall_started = time.perf_counter_ns()
    cpu_started = time.process_time_ns()
    replacements = sum(
        bool(proxy.refresh_for_state(state))
        for proxy, state in zip(proxies, states)
    )
    _process_gui(1)
    process_cpu_ms = (time.process_time_ns() - cpu_started) / 1.0e6
    wall_ms = (time.perf_counter_ns() - wall_started) / 1.0e6

    rss_after_mb = _current_rss_mb()
    object_count_after = len(objects[0].Document.Objects)
    node_ids_after = tuple(
        int(proxy.selection_root.getChild(0).getNodeId())
        for proxy in proxies
    )
    artifacts_after = tuple(
        cache.artifact("preview") for cache in caches
    )
    assert node_ids_after == node_ids_before
    assert all(
        before is after
        for before, after in zip(artifacts_before, artifacts_after)
    )
    cache_reuse_count = counters["reuses"] - reuses_before
    assert counters["requests"] - requests_before == FIXTURE_OBJECT_COUNT

    return {
        "cache_reuse_count": cache_reuse_count,
        "document_object_count_after": object_count_after,
        "document_object_count_before": object_count_before,
        "document_object_delta": object_count_after - object_count_before,
        "part_shape_count": _part_shape_count(objects),
        "process_cpu_ms": process_cpu_ms,
        "recompute_count": 0,
        "rss_after_mb": rss_after_mb,
        "rss_before_mb": rss_before_mb,
        "rss_delta_mb": rss_after_mb - rss_before_mb,
        "scene_replacement_count": replacements,
        "stable_mapping_count": _mapping_count(proxies, states),
        "wall_ms": wall_ms,
    }


def profile():
    if App.listDocuments():
        raise RuntimeError(
            "Phase 5 Coin performance profile requires an empty session"
        )

    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json"
    )
    states = tuple(_state(index) for index in range(FIXTURE_OBJECT_COUNT))
    specification = api.TransitionPreviewSpecification(
        segment_count=PREVIEW_SEGMENT_COUNT
    )
    request = specification.derived_request()
    caches = tuple(
        api.TransitionDerivedCache()
        for _index in range(FIXTURE_OBJECT_COUNT)
    )
    style = renderer.TransitionCoinStyle(
        line_color_rgb=(0.9, 0.05, 0.02),
        line_width=6.0,
    )
    counters = {"requests": 0, "reuses": 0}
    document = App.newDocument("Phase5TransitionCoinPerformance")
    document.UndoMode = 1
    objects = ()
    proxies = []

    try:
        store = adapter.FreeCADTransitionStore(qualification)
        assert all(
            cache.status(state, request) == "missing"
            for cache, state in zip(caches, states)
        )
        object_count_before = len(document.Objects)
        rss_before_mb = _current_rss_mb()
        wall_started = time.perf_counter_ns()
        cpu_started = time.process_time_ns()

        objects = store.create_many(document, states)
        display_modes_added = 0
        root_children_added = 0
        for obj, state, cache in zip(objects, states, caches):
            view_object = obj.ViewObject
            display_mode_count_before = len(
                tuple(view_object.listDisplayModes())
            )
            root_count_before = int(
                view_object.RootNode.getNumChildren()
            )
            artifact_for_state = _artifact_reader(
                cache,
                specification,
                counters,
            )
            artifact = artifact_for_state(state)
            proxy = viewprovider.TransitionCoinViewProviderFixture(
                view_object,
                artifact,
                style,
                coin,
                state_reader=adapter.read_transition_object,
                artifact_for_state=artifact_for_state,
                source_property_name=adapter.FREECAD_STATE_JSON_PROPERTY,
            )
            view_object.DisplayMode = proxy.display_mode
            proxies.append(proxy)
            display_modes_added += (
                len(tuple(view_object.listDisplayModes()))
                - display_mode_count_before
            )
            root_children_added += (
                int(view_object.RootNode.getNumChildren())
                - root_count_before
            )

        recompute_started = time.perf_counter_ns()
        document.recompute()
        recompute_wall_ms = (
            time.perf_counter_ns() - recompute_started
        ) / 1.0e6
        view = Gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        view.redraw()
        _process_gui()

        process_cpu_ms = (
            time.process_time_ns() - cpu_started
        ) / 1.0e6
        wall_ms = (time.perf_counter_ns() - wall_started) / 1.0e6
        rss_after_mb = _current_rss_mb()
        object_count_after = len(document.Objects)
        cold = {
            "cache_current_count": sum(
                cache.status(state, request) == "current"
                for cache, state in zip(caches, states)
            ),
            "cache_missing_count_before": FIXTURE_OBJECT_COUNT,
            "display_modes_added": display_modes_added,
            "document_object_count_after": object_count_after,
            "document_object_count_before": object_count_before,
            "document_object_delta": (
                object_count_after - object_count_before
            ),
            "part_shape_count": _part_shape_count(objects),
            "process_cpu_ms": process_cpu_ms,
            "recompute_count": 1,
            "recompute_wall_ms": recompute_wall_ms,
            "root_children_added": root_children_added,
            "rss_after_mb": rss_after_mb,
            "rss_before_mb": rss_before_mb,
            "rss_delta_mb": rss_after_mb - rss_before_mb,
            "stable_mapping_count": _mapping_count(proxies, states),
            "wall_ms": wall_ms,
        }

        warm_up_measurement = _warm_refresh(
            states,
            objects,
            proxies,
            caches,
            counters,
        )
        warm_up = {
            "cache_reuse_count": warm_up_measurement[
                "cache_reuse_count"
            ],
            "recompute_count": warm_up_measurement["recompute_count"],
            "scene_replacement_count": warm_up_measurement[
                "scene_replacement_count"
            ],
        }
        warm_measurements = [
            _warm_refresh(
                states,
                objects,
                proxies,
                caches,
                counters,
            )
            for _index in range(WARM_MEASUREMENT_COUNT)
        ]

        for proxy, obj in zip(proxies, objects):
            assert proxy.dispose() is True
            obj.ViewObject.Proxy = None
        assert all(
            cache.discard("preview") == ("preview",)
            for cache in caches
        )
        for obj in tuple(objects):
            document.removeObject(obj.Name)
        document.recompute()
        assert document.Objects == []
        assert all(cache.artifact("preview") is None for cache in caches)
        assert all(not proxy.attached for proxy in proxies)
        App.closeDocument(document.Name)
        document = None
        cleanup = {
            "cache_count_after": sum(
                cache.artifact("preview") is not None for cache in caches
            ),
            "document_object_count_after": 0,
            "open_document_count_after": len(App.listDocuments()),
            "viewprovider_count_after": sum(
                proxy.attached for proxy in proxies
            ),
        }

        payload = {
            "boundary": {
                "cold": COLD_BOUNDARY,
                "warm": WARM_BOUNDARY,
            },
            "cleanup": cleanup,
            "cold": cold,
            "fixture": {
                "logical_object_count": FIXTURE_OBJECT_COUNT,
                "preview_segment_count": PREVIEW_SEGMENT_COUNT,
            },
            "freecad_version": ".".join(App.Version()[:3]),
            "profile_id": SAMPLE_PROFILE_ID,
            "qualified_profile_id": qualification[
                "compatibility_evaluation"
            ]["matched_profile_id"],
            "schema_version": 1,
            "status": "completed",
            "warm": {
                "measurement_count": len(warm_measurements),
                "measurements": warm_measurements,
                "warm_up": warm_up,
            },
        }
        print(
            SAMPLE_SENTINEL + json.dumps(payload, sort_keys=True)
        )
    finally:
        for proxy in proxies:
            if proxy.attached:
                proxy.dispose()
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)


profile()
