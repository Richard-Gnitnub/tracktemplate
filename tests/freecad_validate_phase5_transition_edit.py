#!/usr/bin/env python3
"""Exercise the Phase 5 edit transaction seam in qualified FreeCAD."""

from contextlib import contextmanager
from dataclasses import replace
import math
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import transition_state as adapter  # noqa: E402
from tracktemplate.application import transition_edit as command  # noqa: E402


class _PreviewCoordinator:
    def __init__(self, state):
        self.state = state
        self.deferred = 0
        self.refreshes = []
        self.fail_after_switch_once = False
        self.cache = api.TransitionDerivedCache()
        self.specification = api.TransitionPreviewSpecification(
            segment_count=32
        )
        self.artifact = api.regenerate_transition_preview(
            self.cache,
            state,
            self.specification,
        )
        self.reuse_count = 0

    @contextmanager
    def defer_document_updates(self):
        self.deferred += 1
        try:
            yield
        finally:
            self.deferred -= 1

    def refresh_for_state(self, state):
        assert self.deferred == 1
        previous = self.artifact
        self.artifact = api.regenerate_transition_preview(
            self.cache,
            state,
            self.specification,
        )
        if self.artifact is previous:
            self.reuse_count += 1
        self.state = state
        self.refreshes.append(state)
        if self.fail_after_switch_once:
            self.fail_after_switch_once = False
            raise RuntimeError("injected failure after preview switch")
        return self.artifact is not previous

    def cache_status(self, state):
        return self.cache.status(
            state,
            self.specification.derived_request(),
        )


def _state(transition_length_mm):
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:freecad-edit",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 FreeCAD edit",
        end_name="Entry",
    )
    return api.analyse_transition_state(api.TransitionState(intent))


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
            "Phase 5 edit validation requires an empty FreeCAD session"
        )
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    store = adapter.FreeCADTransitionStore(qualification)
    document = App.newDocument("TrackTemplatePhase5Edit")
    document.UndoMode = 1
    try:
        initial = _state(300.0)
        obj = store.create(document, initial)
        document.clearUndos()
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 0

        preview = _PreviewCoordinator(initial)
        initial_artifact = preview.artifact
        assert preview.cache_status(initial) == "current"
        with preview.defer_document_updates():
            assert preview.refresh_for_state(initial) is False
        assert preview.reuse_count == 1
        assert preview.artifact is initial_artifact
        edit_port = adapter.FreeCADTransitionEditPort(
            store,
            document,
            obj,
            preview,
        )
        edited_intent = replace(
            initial.intent,
            target_signed_offset_mm=_state(
                340.0
            ).intent.target_signed_offset_mm,
        )
        result = command.edit_transition_intent(
            initial,
            edited_intent,
            edit_port,
        )
        assert result.changed is True
        assert adapter.read_transition_object(obj) == result.state
        assert preview.state == result.state
        edited_artifact = preview.artifact
        assert edited_artifact is not initial_artifact
        assert preview.cache_status(result.state) == "current"
        assert preview.cache_status(initial) == "stale"
        assert preview.deferred == 0
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0
        assert len(document.Objects) == 1
        assert "Shape" not in obj.PropertiesList

        document.undo()
        assert adapter.read_transition_object(obj) == initial
        with preview.defer_document_updates():
            assert preview.refresh_for_state(initial) is True
        assert preview.artifact.source_signature == (
            initial_artifact.source_signature
        )
        assert preview.artifact.payload == initial_artifact.payload
        assert preview.cache_status(initial) == "current"
        assert int(document.UndoCount) == 0
        assert int(document.RedoCount) == 1
        document.redo()
        assert adapter.read_transition_object(obj) == result.state
        with preview.defer_document_updates():
            assert preview.refresh_for_state(result.state) is True
        assert preview.artifact.source_signature == (
            edited_artifact.source_signature
        )
        assert preview.artifact.payload == edited_artifact.payload
        assert preview.cache_status(result.state) == "current"
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 0

        before_noop = (
            int(document.UndoCount),
            int(document.RedoCount),
            str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)),
            tuple(preview.refreshes),
            preview.artifact,
        )
        noop = command.edit_transition_intent(
            result.state,
            result.state.intent,
            edit_port,
        )
        assert noop.changed is False
        assert (
            int(document.UndoCount),
            int(document.RedoCount),
            str(getattr(obj, adapter.FREECAD_STATE_JSON_PROPERTY)),
            tuple(preview.refreshes),
            preview.artifact,
        ) == before_noop

        failure_state = _state(380.0)
        before_failure = (
            adapter.read_transition_object(obj),
            int(document.UndoCount),
            int(document.RedoCount),
            len(document.Objects),
            tuple(obj.PropertiesList),
        )
        preview.fail_after_switch_once = True
        error = _expect_adapter_error(
            lambda: command.edit_transition_intent(
                result.state,
                failure_state.intent,
                edit_port,
            ),
            "transaction-failed",
        )
        assert error.recoverable is True
        assert error.document_mutation is False
        assert (
            adapter.read_transition_object(obj),
            int(document.UndoCount),
            int(document.RedoCount),
            len(document.Objects),
            tuple(obj.PropertiesList),
        ) == before_failure
        assert preview.state == result.state
        assert preview.artifact.source_signature == (
            edited_artifact.source_signature
        )
        assert preview.artifact.payload == edited_artifact.payload
        assert preview.cache_status(result.state) == "current"
        assert preview.cache_status(failure_state) == "stale"
        assert preview.deferred == 0

        _expect_adapter_error(
            lambda: edit_port.apply_transition_edit(
                initial,
                failure_state,
            ),
            "stale-edit-base",
        )
        assert adapter.read_transition_object(obj) == result.state
        assert int(document.UndoCount) == 1
        assert len(document.Objects) == 1

        before_change_back_undos = int(document.UndoCount)
        change_back_result = command.edit_transition_intent(
            result.state,
            initial.intent,
            edit_port,
        )
        assert change_back_result.changed is True
        assert change_back_result.state == initial
        assert adapter.read_transition_object(obj) == initial
        assert preview.artifact.source_signature == (
            initial_artifact.source_signature
        )
        assert preview.artifact.payload == initial_artifact.payload
        assert preview.cache_status(initial) == "current"
        assert int(document.UndoCount) - before_change_back_undos == 1
        assert int(document.RedoCount) == 0

        document.undo()
        assert adapter.read_transition_object(obj) == result.state
        with preview.defer_document_updates():
            assert preview.refresh_for_state(result.state) is True
        assert preview.artifact.source_signature == (
            edited_artifact.source_signature
        )
        assert int(document.UndoCount) == 1
        assert int(document.RedoCount) == 1

        document.redo()
        assert adapter.read_transition_object(obj) == initial
        with preview.defer_document_updates():
            assert preview.refresh_for_state(initial) is True
        assert preview.artifact.source_signature == (
            initial_artifact.source_signature
        )
        assert preview.artifact.payload == initial_artifact.payload
        assert int(document.UndoCount) == 2
        assert int(document.RedoCount) == 0
        assert len(document.Objects) == 1

        print("Phase 5 transition edit FreeCAD validation passed")
    finally:
        if document.Name in App.listDocuments():
            App.closeDocument(document.Name)


validate()
