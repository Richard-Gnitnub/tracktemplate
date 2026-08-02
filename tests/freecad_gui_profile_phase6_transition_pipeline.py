"""Profile one transition edit through exact validation and DXF export."""

import dataclasses
import functools
import gc
import hashlib
import json
import math
import os
import pathlib
import resource
import sys
import time

import FreeCAD as App
import FreeCADGui as Gui


ROOT = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
sys.path.insert(0, str(ROOT))

from tests import (  # noqa: E402
    freecad_gui_profile_phase5_transition_interaction_range as editing,
)
from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.export import transition_dxf as exporter  # noqa: E402
from tracktemplate.adapters.freecad import transition_exact  # noqa: E402
from tracktemplate.adapters.freecad import transition_state  # noqa: E402


PROFILE_ID = "phase6-transition-edit-validate-export-profile-v1"
TARGET_TRANSITION_ID = "SET-001/curve-track/2/transition/exit"
EXACT_CHORD_ERROR_MM = 0.05
EXACT_MAXIMUM_SEGMENTS = 64
WARM_REPETITIONS = 3


def _current_rss_mb():
    status = pathlib.Path("/proc/self/status")
    if not status.is_file():
        return None
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return float(line.split()[1]) / 1024.0
    return None


def _peak_rss_mb():
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0 * 1024.0)
    return value / 1024.0


def _measurement_start():
    return {
        "cpu_ns": time.process_time_ns(),
        "peak_rss_mb": _peak_rss_mb(),
        "rss_mb": _current_rss_mb(),
        "wall_ns": time.perf_counter_ns(),
    }


def _measurement_finish(start):
    rss_after_mb = _current_rss_mb()
    peak_rss_after_mb = _peak_rss_mb()
    return {
        "peak_rss_after_mb": peak_rss_after_mb,
        "peak_rss_before_mb": start["peak_rss_mb"],
        "peak_rss_delta_mb": (
            peak_rss_after_mb - start["peak_rss_mb"]
        ),
        "process_cpu_ms": (
            time.process_time_ns() - start["cpu_ns"]
        ) / 1.0e6,
        "rss_after_mb": rss_after_mb,
        "rss_before_mb": start["rss_mb"],
        "rss_delta_mb": (
            None
            if start["rss_mb"] is None or rss_after_mb is None
            else rss_after_mb - start["rss_mb"]
        ),
        "wall_ms": (
            time.perf_counter_ns() - start["wall_ns"]
        ) / 1.0e6,
    }


def _measure(action):
    started = _measurement_start()
    result = action()
    return result, _measurement_finish(started)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _application_snapshot(document, records):
    snapshot = editing._snapshot(document, records)
    snapshot.update({
        "active_document": (
            ""
            if App.ActiveDocument is None
            else str(App.ActiveDocument.Name)
        ),
        "document_names": sorted(App.listDocuments()),
        "redo_count": int(document.RedoCount),
        "undo_count": int(document.UndoCount),
    })
    return snapshot


def _output_snapshot(output_directory, receipt):
    def receipt_value(name):
        if isinstance(receipt, dict):
            return receipt[name]
        return getattr(receipt, name)

    dxf_path = output_directory / receipt_value("dxf_filename")
    manifest_path = output_directory / receipt_value("manifest_filename")
    snapshot = {
        "directory_entries": sorted(
            item.name for item in output_directory.iterdir()
        ),
        "dxf": {
            "filename": dxf_path.name,
            "sha256": _sha256(dxf_path),
            "size_bytes": dxf_path.stat().st_size,
        },
        "manifest": {
            "filename": manifest_path.name,
            "sha256": _sha256(manifest_path),
            "size_bytes": manifest_path.stat().st_size,
        },
        "staging_entries": sorted(
            item.name
            for item in output_directory.iterdir()
            if item.name.startswith(".tracktemplate-transition-dxf-")
        ),
    }
    assert snapshot["dxf"]["sha256"] == receipt_value("dxf_sha256")
    assert snapshot["manifest"]["sha256"] == receipt_value(
        "manifest_sha256"
    )
    assert snapshot["staging_entries"] == []
    return snapshot


def _geometry_receipt_record(receipt):
    return dataclasses.asdict(receipt)


def _measured_exact_validation(
    cache,
    state,
    specification,
    previous_artifact,
    geometry_receipts,
):
    derived_request = specification.derived_request()
    status_before = cache.status(state, derived_request)
    build_count_before = len(geometry_receipts)

    def action():
        artifact = api.regenerate_transition_exact(
            cache,
            state,
            specification,
        )
        receipt = transition_exact.build_transition_exact_geometry(artifact)
        return artifact, receipt

    result, measurement = _measure(action)
    artifact, receipt = result
    record = {
        "artifact_reused": (
            previous_artifact is not None and artifact is previous_artifact
        ),
        "artifact_signature": artifact.payload.artifact_signature,
        "cache_status_after": cache.status(state, derived_request),
        "cache_status_before": status_before,
        "exact_result_signature": artifact.payload.result_signature,
        "geometry_build_count": (
            len(geometry_receipts) - build_count_before
        ),
        "geometry_receipt": _geometry_receipt_record(receipt),
        "source_signature": artifact.source_signature,
    }
    record.update(measurement)
    return artifact, record


def _measured_dxf_export(
    state,
    artifact,
    specification,
    request,
    geometry_receipts,
):
    build_count_before = len(geometry_receipts)
    documents_before = sorted(App.listDocuments())
    active_before = (
        "" if App.ActiveDocument is None else str(App.ActiveDocument.Name)
    )
    receipt, measurement = _measure(
        lambda: exporter.export_transition_dxf(
            state,
            artifact,
            specification,
            request,
        )
    )
    record = {
        "active_document_before": active_before,
        "documents_before": documents_before,
        "geometry_build_count": (
            len(geometry_receipts) - build_count_before
        ),
        "geometry_receipt": _geometry_receipt_record(
            geometry_receipts[-1]
        ),
        "receipt": dataclasses.asdict(receipt),
    }
    record.update(measurement)
    return record


def _audit_dxf_export(
    record,
    output_directory,
):
    output, audit = _measure(
        lambda: _output_snapshot(
            output_directory,
            record["receipt"],
        )
    )
    record.update({
        "active_document_after": (
            ""
            if App.ActiveDocument is None
            else str(App.ActiveDocument.Name)
        ),
        "documents_after": sorted(App.listDocuments()),
        "output": output,
        "post_action_audit": audit,
    })
    return record


def _reconcile(parent, children):
    child_wall_ms = sum(child["wall_ms"] for child in children)
    child_cpu_ms = sum(child["process_cpu_ms"] for child in children)
    uncovered_wall_ms = parent["wall_ms"] - child_wall_ms
    uncovered_cpu_ms = parent["process_cpu_ms"] - child_cpu_ms
    assert uncovered_wall_ms >= -0.1
    assert uncovered_cpu_ms >= -0.1
    parent.update({
        "child_process_cpu_ms": child_cpu_ms,
        "child_wall_ms": child_wall_ms,
        "uncovered_process_cpu_ms": uncovered_cpu_ms,
        "uncovered_wall_ms": uncovered_wall_ms,
    })


def _prepare_edit(document, store, records, view):
    target_record = next(
        record
        for record in records
        if record["initial_state"].intent.transition_id
        == TARGET_TRANSITION_ID
    )
    target, target_point, pointer_target = (
        editing._visible_centreline_target(view, target_record)
    )
    Gui.Selection.clearSelection()
    target_record["proxy"].pick_callback_count = 0
    editing._click_target(target, target_point)
    selected = tuple(Gui.Selection.getSelectionEx(document.Name))
    assert len(selected) == 1
    assert selected[0].Object is target_record["object"]
    parameter_dialog = editing._open_dialog(document, store)
    assert parameter_dialog.selected_transition_id == TARGET_TRANSITION_ID
    assert parameter_dialog.length_edit.text() == "420.000"
    document.clearUndos()
    return target_record, parameter_dialog, pointer_target


def _measured_edit(parameter_dialog, target_record):
    result, measurement = _measure(
        lambda: editing._apply_dialog_edit(parameter_dialog)
    )
    state = transition_state.read_transition_object(target_record["object"])
    assert result is not None and result.changed is True
    assert math.isclose(
        state.analysis.transition_length_mm,
        editing.EDITED_EXIT_TRANSITION_LENGTH_MM,
        rel_tol=0.0,
        abs_tol=editing.GEOMETRY_TOLERANCE,
    )
    record = {
        "changed": result.changed,
        "target_transition_id": state.intent.transition_id,
        "transition_length_mm": state.analysis.transition_length_mm,
    }
    record.update(measurement)
    return state, record


def _reuse_cycle(
    cache,
    state,
    specification,
    artifact,
    request,
    output_directory,
    geometry_receipts,
    document,
    records,
):
    before = _application_snapshot(document, records)
    gc.collect()
    parent_started = _measurement_start()
    artifact, validation = _measured_exact_validation(
        cache,
        state,
        specification,
        artifact,
        geometry_receipts,
    )
    export = _measured_dxf_export(
        state,
        artifact,
        specification,
        request,
        geometry_receipts,
    )
    parent = _measurement_finish(parent_started)
    _reconcile(parent, (validation, export))
    _audit_dxf_export(export, output_directory)
    after = _application_snapshot(document, records)
    return artifact, {
        "document_unchanged": before == after,
        "export": export,
        "parent": parent,
        "validation": validation,
    }


def validate(output_directory):
    """Run one qualified sample and print its structured sentinel."""
    output_directory = pathlib.Path(output_directory).resolve()
    if not output_directory.is_dir() or any(output_directory.iterdir()):
        raise RuntimeError(
            "Phase 6 performance output must be an empty directory"
        )
    if App.listDocuments():
        raise RuntimeError(
            "Phase 6 pipeline profiling requires an empty session"
        )

    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    document = None
    records = []
    parameter_dialog = None
    exact_cache = api.TransitionDerivedCache()
    original_geometry_builder = (
        transition_exact.build_transition_exact_geometry
    )
    geometry_receipts = []

    def observed_geometry_builder(*args, **kwargs):
        receipt = original_geometry_builder(*args, **kwargs)
        geometry_receipts.append(receipt)
        return receipt

    transition_exact.build_transition_exact_geometry = (
        observed_geometry_builder
    )
    try:
        document, store, records, view = editing._build_fixture(
            qualification,
            1,
        )
        target_record, parameter_dialog, pointer_target = _prepare_edit(
            document,
            store,
            records,
            view,
        )
        initial_snapshot = _application_snapshot(document, records)
        specification = api.TransitionExactSpecification(
            EXACT_CHORD_ERROR_MM,
            EXACT_MAXIMUM_SEGMENTS,
        )
        request = api.TransitionDxfExportRequest(
            output_directory=str(output_directory),
            generator_version=api.DEVELOPMENT_CHECKPOINT,
        )

        gc.collect()
        parent_started = _measurement_start()
        state, edit = _measured_edit(
            parameter_dialog,
            target_record,
        )
        artifact, exact_validation = _measured_exact_validation(
            exact_cache,
            state,
            specification,
            None,
            geometry_receipts,
        )
        dxf_export = _measured_dxf_export(
            state,
            artifact,
            specification,
            request,
            geometry_receipts,
        )
        end_to_end = _measurement_finish(parent_started)
        _reconcile(end_to_end, (edit, exact_validation, dxf_export))
        _audit_dxf_export(dxf_export, output_directory)
        final_snapshot = _application_snapshot(document, records)
        edit.update({
            "cache_regeneration_delta": (
                final_snapshot["cache_regeneration_count"]
                - initial_snapshot["cache_regeneration_count"]
            ),
            "cache_request_delta": (
                final_snapshot["cache_request_count"]
                - initial_snapshot["cache_request_count"]
            ),
        })

        assert initial_snapshot["mapping_digest"] == (
            final_snapshot["mapping_digest"]
        )
        assert initial_snapshot["canonical_state_digest"] != (
            final_snapshot["canonical_state_digest"]
        )
        assert final_snapshot["part_shape_count"] == 0
        assert exact_validation["geometry_build_count"] == 1
        assert dxf_export["geometry_build_count"] == 1
        assert dxf_export["receipt"]["disposition"] == "created"
        assert dxf_export["receipt"]["project_status"] == "unknown"
        assert dxf_export["receipt"]["geometry_signature"] == (
            exact_validation["geometry_receipt"]["geometry_signature"]
        )

        artifact, warmup = _reuse_cycle(
            exact_cache,
            state,
            specification,
            artifact,
            request,
            output_directory,
            geometry_receipts,
            document,
            records,
        )
        warm = []
        for _index in range(WARM_REPETITIONS):
            artifact, cycle = _reuse_cycle(
                exact_cache,
                state,
                specification,
                artifact,
                request,
                output_directory,
                geometry_receipts,
                document,
                records,
            )
            warm.append(cycle)

        output_after_reuse = _output_snapshot(
            output_directory,
            dxf_export["receipt"],
        )
        assert output_after_reuse == dxf_export["output"]
        assert _application_snapshot(document, records) == final_snapshot

        discarded_exact = exact_cache.discard()
        gc.collect()
        cleanup_result, cleanup = _measure(
            lambda: editing._dispose_fixture(
                document,
                records,
                parameter_dialog,
            )
        )
        cleanup_result["discarded_exact_stages"] = list(discarded_exact)
        cleanup_result["output_retained"] = (
            _output_snapshot(
                output_directory,
                dxf_export["receipt"],
            )
            == dxf_export["output"]
        )
        cleanup_result.update(cleanup)
        document = None
        records = []
        parameter_dialog = None

        payload = {
            "cleanup": cleanup_result,
            "end_to_end": {
                **end_to_end,
                "edit": edit,
                "exact_validation": exact_validation,
                "export": dxf_export,
                "final_snapshot": final_snapshot,
                "initial_snapshot": initial_snapshot,
            },
            "fixture": {
                "budget_status": "not-accepted",
                "comparison_status": "not-b14-equivalent",
                "exact_chord_error_mm": EXACT_CHORD_ERROR_MM,
                "exact_maximum_segments": EXACT_MAXIMUM_SEGMENTS,
                "logical_object_count": 2,
                "output_project_status": "unknown",
                "pointer_target": pointer_target,
                "preview_segment_count": editing.PREVIEW_SEGMENT_COUNT,
                "target_transition_id": TARGET_TRANSITION_ID,
                "warm_repetitions": WARM_REPETITIONS,
            },
            "freecad_version": ".".join(App.Version()[:3]),
            "profile_id": PROFILE_ID,
            "schema_version": 1,
            "starting_state": (
                "fresh isolated GUI process; one accepted Entry/Exit pair; "
                "selected Exit with its parameter editor open; empty exact "
                "cache and empty private-development output directory"
            ),
            "warm": warm,
            "warmup": warmup,
        }
        print(
            "TRACKTEMPLATE_PHASE6_TRANSITION_PIPELINE_SAMPLE="
            + json.dumps(payload, allow_nan=False, sort_keys=True)
        )
    finally:
        transition_exact.build_transition_exact_geometry = (
            original_geometry_builder
        )
        Gui.Selection.clearSelection()
        for record in records:
            proxy = record["proxy"]
            if proxy.attached:
                proxy.dispose()
        if parameter_dialog is not None:
            parameter_dialog.dialog.close()
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
