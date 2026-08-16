#!/usr/bin/env python3
"""Profile the accepted transition edit through Validate and Export."""

import argparse
import datetime
import hashlib
import json
import math
import os
import pathlib
import platform
import statistics
import subprocess
import sys
import time


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_ROOT = (
    PROJECT_ROOT
    / "benchmark-output"
    / "freecad-bridge"
    / "phase6-transition-pipeline-runs"
)
GUI_SAMPLE = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_profile_phase6_transition_pipeline.py"
)
SAMPLE_SENTINEL = "TRACKTEMPLATE_PHASE6_TRANSITION_PIPELINE_SAMPLE="
RAW_SAMPLE_SENTINEL = (
    "TRACKTEMPLATE_PHASE6_TRANSITION_PIPELINE_RAW_SAMPLE="
)
PROFILE_SENTINEL = "TRACKTEMPLATE_PHASE6_TRANSITION_PIPELINE_PROFILE="
PROFILE_ID = "phase6-transition-edit-validate-export-profile-v1"
EVIDENCE_SCHEMA_VERSION = 2
AUTHORISED_PERFORMANCE_HOSTS = {
    "linux-x86_64-flatpak-freecad-1.1.1": "1.1.1",
    "linux-x86_64-flatpak-freecad-1.1.3": "1.1.3",
}
TARGET_TRANSITION_ID = "SET-001/curve-track/2/transition/exit"
EXACT_GEOMETRY_CONTRACT_ID = (
    "tracktemplate.freecad.transition-exact-geometry.v1"
)
DXF_EXPORT_CONTRACT_ID = (
    "tracktemplate.transition-export.dxf-centreline.v1"
)
EXACT_CHORD_ERROR_MM = 0.05
EXACT_MAXIMUM_SEGMENTS = 64
WARM_REPETITIONS = 3
DEFAULT_PROCESS_REPETITIONS = 3
MEASUREMENT_FIELDS = (
    "peak_rss_after_mb",
    "peak_rss_before_mb",
    "peak_rss_delta_mb",
    "process_cpu_ms",
    "rss_after_mb",
    "rss_before_mb",
    "rss_delta_mb",
    "wall_ms",
)

sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    parse_json_output,
    submit_and_wait,
)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _valid_digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_signature(value):
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and _valid_digest(value[len("sha256:"):])
    )


def _assert_measurement(record, label):
    if not isinstance(record, dict):
        raise RuntimeError(
            "The {} performance measurement is missing.".format(label)
        )
    for key in MEASUREMENT_FIELDS:
        if not _finite_number(record.get(key)):
            raise RuntimeError(
                "The {} performance measurement {!r} is invalid.".format(
                    label,
                    key,
                )
            )
    if record["wall_ms"] < 0.0 or record["process_cpu_ms"] < 0.0:
        raise RuntimeError(
            "The {} performance duration is negative.".format(label)
        )
    if record["peak_rss_delta_mb"] < 0.0:
        raise RuntimeError(
            "The {} process peak RSS moved backwards.".format(label)
        )


def _assert_snapshot(snapshot, label):
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("active_coin_scene_node_count") != 16
        or snapshot.get("display_modes_added") != 2
        or snapshot.get("document_object_count") != 2
        or snapshot.get("logical_layer_count") != 2
        or snapshot.get("part_shape_count") != 0
        or snapshot.get("proxy_count") != 2
        or snapshot.get("root_children_added") != 0
        or snapshot.get("switch_children_added") != 2
        or snapshot.get("document_names")
        != ["Phase5TransitionInteractionRange"]
        or snapshot.get("active_document")
        != "Phase5TransitionInteractionRange"
        or not _valid_digest(snapshot.get("mapping_digest"))
        or not _valid_digest(snapshot.get("canonical_state_digest"))
    ):
        raise RuntimeError(
            "The {} editable-document snapshot drifted.".format(label)
        )


def _assert_geometry_receipt(receipt, label, freecad_version):
    if (
        not isinstance(receipt, dict)
        or receipt.get("contract_id") != EXACT_GEOMETRY_CONTRACT_ID
        or receipt.get("domain_id") != TARGET_TRANSITION_ID
        or receipt.get("frame_id") != "canonical-local-left-turn-v1"
        or receipt.get("freecad_version") != freecad_version
        or receipt.get("length_unit") != "mm"
        or receipt.get("shape_type") != "Wire"
        or receipt.get("closed") is not False
        or not isinstance(receipt.get("vertex_count"), int)
        or receipt.get("vertex_count", 0) < 2
        or not isinstance(receipt.get("edge_count"), int)
        or receipt.get("edge_count", 0) < 1
        or not _valid_signature(receipt.get("source_signature"))
        or not _valid_signature(
            receipt.get("exact_artifact_signature")
        )
        or not _valid_signature(receipt.get("exact_result_signature"))
        or not _valid_signature(receipt.get("geometry_signature"))
    ):
        raise RuntimeError(
            "The {} exact-geometry receipt drifted.".format(label)
        )


def _assert_output(output, receipt, label):
    if not isinstance(output, dict) or not isinstance(receipt, dict):
        raise RuntimeError(
            "The {} output receipt is missing.".format(label)
        )
    dxf = output.get("dxf")
    manifest = output.get("manifest")
    if (
        not isinstance(dxf, dict)
        or not isinstance(manifest, dict)
        or dxf.get("filename") != receipt.get("dxf_filename")
        or manifest.get("filename") != receipt.get("manifest_filename")
        or dxf.get("sha256") != receipt.get("dxf_sha256")
        or manifest.get("sha256") != receipt.get("manifest_sha256")
        or not _valid_digest(dxf.get("sha256"))
        or not _valid_digest(manifest.get("sha256"))
        or not isinstance(dxf.get("size_bytes"), int)
        or dxf.get("size_bytes", 0) <= 0
        or not isinstance(manifest.get("size_bytes"), int)
        or manifest.get("size_bytes", 0) <= 0
        or output.get("staging_entries") != []
        or output.get("directory_entries")
        != sorted([dxf["filename"], manifest["filename"]])
    ):
        raise RuntimeError(
            "The {} deterministic output snapshot drifted.".format(label)
        )


def _assert_validation_stage(
    record,
    label,
    expected_status_before,
    expected_reuse,
    freecad_version,
):
    _assert_measurement(record, label)
    receipt = record.get("geometry_receipt")
    _assert_geometry_receipt(receipt, label, freecad_version)
    if (
        record.get("cache_status_before") != expected_status_before
        or record.get("cache_status_after") != "current"
        or record.get("artifact_reused") is not expected_reuse
        or record.get("geometry_build_count") != 1
        or not _valid_signature(record.get("source_signature"))
        or not _valid_signature(record.get("artifact_signature"))
        or not _valid_signature(record.get("exact_result_signature"))
        or receipt.get("source_signature")
        != record.get("source_signature")
        or receipt.get("exact_artifact_signature")
        != record.get("artifact_signature")
        or receipt.get("exact_result_signature")
        != record.get("exact_result_signature")
    ):
        raise RuntimeError(
            "The {} exact-validation cache contract drifted.".format(label)
        )


def _assert_export_stage(record, label, disposition, freecad_version):
    _assert_measurement(record, label)
    _assert_measurement(
        record.get("post_action_audit"),
        label + " post-action audit",
    )
    receipt = record.get("receipt")
    geometry_receipt = record.get("geometry_receipt")
    _assert_geometry_receipt(geometry_receipt, label, freecad_version)
    if (
        not isinstance(receipt, dict)
        or receipt.get("contract_id") != DXF_EXPORT_CONTRACT_ID
        or receipt.get("disposition") != disposition
        or receipt.get("project_status") != "unknown"
        or receipt.get("cleanup_complete") is not True
        or record.get("geometry_build_count") != 1
        or record.get("documents_before")
        != ["Phase5TransitionInteractionRange"]
        or record.get("documents_after")
        != record.get("documents_before")
        or record.get("active_document_before")
        != "Phase5TransitionInteractionRange"
        or record.get("active_document_after")
        != record.get("active_document_before")
        or receipt.get("geometry_signature")
        != geometry_receipt.get("geometry_signature")
        or receipt.get("exact_result_signature")
        != geometry_receipt.get("exact_result_signature")
    ):
        raise RuntimeError(
            "The {} export lifecycle contract drifted.".format(label)
        )
    _assert_output(record.get("output"), receipt, label)


def _assert_reconciliation(parent, children, label):
    _assert_measurement(parent, label)
    child_wall_ms = sum(child["wall_ms"] for child in children)
    child_cpu_ms = sum(child["process_cpu_ms"] for child in children)
    if (
        not math.isclose(
            parent.get("child_wall_ms", math.nan),
            child_wall_ms,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
        or not math.isclose(
            parent.get("child_process_cpu_ms", math.nan),
            child_cpu_ms,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
        or not math.isclose(
            parent.get("uncovered_wall_ms", math.nan),
            parent["wall_ms"] - child_wall_ms,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
        or not math.isclose(
            parent.get("uncovered_process_cpu_ms", math.nan),
            parent["process_cpu_ms"] - child_cpu_ms,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
        or parent.get("uncovered_wall_ms", -1.0) < -0.1
        or parent.get("uncovered_process_cpu_ms", -1.0) < -0.1
    ):
        raise RuntimeError(
            "The {} parent/child timing did not reconcile.".format(label)
        )


def _assert_reuse_cycle(cycle, label, cold, freecad_version):
    if (
        not isinstance(cycle, dict)
        or cycle.get("document_unchanged") is not True
    ):
        raise RuntimeError(
            "The {} reuse cycle changed the editable document.".format(
                label
            )
        )
    validation = cycle.get("validation")
    export = cycle.get("export")
    _assert_validation_stage(
        validation,
        label + " validation",
        "current",
        True,
        freecad_version,
    )
    _assert_export_stage(
        export,
        label + " export",
        "reused",
        freecad_version,
    )
    _assert_reconciliation(
        cycle.get("parent"),
        (validation, export),
        label,
    )
    if (
        validation["artifact_signature"]
        != cold["exact_validation"]["artifact_signature"]
        or validation["exact_result_signature"]
        != cold["exact_validation"]["exact_result_signature"]
        or validation["geometry_receipt"]["geometry_signature"]
        != cold["exact_validation"]["geometry_receipt"][
            "geometry_signature"
        ]
        or export["receipt"]["exact_result_signature"]
        != validation["exact_result_signature"]
        or export["output"] != cold["export"]["output"]
    ):
        raise RuntimeError(
            "The {} reuse result differs from the cold result.".format(label)
        )


def validate_sample(sample):
    """Validate one qualified GUI sample without importing FreeCAD."""
    host_profile_id = (
        sample.get("host_profile_id") if isinstance(sample, dict) else None
    )
    freecad_version = (
        sample.get("freecad_version") if isinstance(sample, dict) else None
    )
    if (
        not isinstance(sample, dict)
        or sample.get("schema_version") != EVIDENCE_SCHEMA_VERSION
        or sample.get("profile_id") != PROFILE_ID
        or not isinstance(host_profile_id, str)
        or host_profile_id not in AUTHORISED_PERFORMANCE_HOSTS
        or AUTHORISED_PERFORMANCE_HOSTS.get(host_profile_id)
        != freecad_version
    ):
        raise RuntimeError("The Phase 6 pipeline sample identity drifted.")
    fixture = sample.get("fixture")
    if (
        not isinstance(fixture, dict)
        or fixture.get("budget_status") != "not-accepted"
        or fixture.get("comparison_status") != "not-b14-equivalent"
        or fixture.get("exact_chord_error_mm")
        != EXACT_CHORD_ERROR_MM
        or fixture.get("exact_maximum_segments")
        != EXACT_MAXIMUM_SEGMENTS
        or fixture.get("logical_object_count") != 2
        or fixture.get("output_project_status") != "unknown"
        or fixture.get("preview_segment_count") != 32
        or fixture.get("target_transition_id")
        != TARGET_TRANSITION_ID
        or fixture.get("warm_repetitions") != WARM_REPETITIONS
    ):
        raise RuntimeError("The Phase 6 pipeline fixture drifted.")

    end_to_end = sample.get("end_to_end")
    if not isinstance(end_to_end, dict):
        raise RuntimeError("The complete pipeline observation is missing.")
    initial = end_to_end.get("initial_snapshot")
    final = end_to_end.get("final_snapshot")
    _assert_snapshot(initial, "initial")
    _assert_snapshot(final, "final")
    if (
        initial["mapping_digest"] != final["mapping_digest"]
        or initial["canonical_state_digest"]
        == final["canonical_state_digest"]
        or final["cache_regeneration_count"]
        != initial["cache_regeneration_count"] + 1
        or final["cache_request_count"]
        != initial["cache_request_count"] + 1
        or initial["undo_count"] != 0
        or final["undo_count"] != 1
        or final["redo_count"] != 0
    ):
        raise RuntimeError(
            "The complete pipeline edit or mapping contract drifted."
        )

    edit = end_to_end.get("edit")
    _assert_measurement(edit, "cold edit")
    if (
        edit.get("changed") is not True
        or edit.get("cache_regeneration_delta") != 1
        or edit.get("cache_request_delta") != 1
        or edit.get("target_transition_id") != TARGET_TRANSITION_ID
        or not math.isclose(
            float(edit.get("transition_length_mm", math.nan)),
            360.0,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
    ):
        raise RuntimeError("The complete pipeline edit contract drifted.")

    exact_validation = end_to_end.get("exact_validation")
    dxf_export = end_to_end.get("export")
    _assert_validation_stage(
        exact_validation,
        "cold validation",
        "missing",
        False,
        freecad_version,
    )
    _assert_export_stage(
        dxf_export,
        "cold export",
        "created",
        freecad_version,
    )
    if (
        dxf_export["receipt"]["geometry_signature"]
        != exact_validation["geometry_receipt"]["geometry_signature"]
    ):
        raise RuntimeError(
            "Cold Validate and Export geometry signatures differ."
        )
    if (
        dxf_export["receipt"]["exact_result_signature"]
        != exact_validation["exact_result_signature"]
    ):
        raise RuntimeError(
            "Cold Validate and Export exact-result signatures differ."
        )
    _assert_reconciliation(
        end_to_end,
        (edit, exact_validation, dxf_export),
        "complete edit/Validate/Export",
    )

    _assert_reuse_cycle(
        sample.get("warmup"),
        "warm-up",
        end_to_end,
        freecad_version,
    )
    warm = sample.get("warm")
    if not isinstance(warm, list) or len(warm) != WARM_REPETITIONS:
        raise RuntimeError("The measured warm observation count drifted.")
    for index, cycle in enumerate(warm, start=1):
        _assert_reuse_cycle(
            cycle,
            "warm {}".format(index),
            end_to_end,
            freecad_version,
        )

    cleanup = sample.get("cleanup")
    _assert_measurement(cleanup, "cleanup")
    if (
        cleanup.get("discarded_cache_count") != 2
        or cleanup.get("discarded_exact_stages") != ["exact-validation"]
        or cleanup.get("disposed_proxy_count") != 2
        or cleanup.get("object_count_before_close") != 2
        or cleanup.get("output_retained") is not True
        or cleanup.get("remaining_documents") != []
    ):
        raise RuntimeError("The Phase 6 pipeline cleanup drifted.")

    return {
        "dxf_sha256": dxf_export["receipt"]["dxf_sha256"],
        "exact_result_signature": exact_validation[
            "exact_result_signature"
        ],
        "geometry_signature": dxf_export["receipt"][
            "geometry_signature"
        ],
        "manifest_sha256": dxf_export["receipt"]["manifest_sha256"],
        "mapping_digest": final["mapping_digest"],
        "freecad_version": freecad_version,
        "host_profile_id": host_profile_id,
    }


def _metric_summary(records, key):
    values = [float(record[key]) for record in records]
    return {
        "count": len(values),
        "maximum": max(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "range": max(values) - min(values),
        "values": values,
    }


def _stage_summary(records):
    return {
        key: _metric_summary(records, key)
        for key in MEASUREMENT_FIELDS
    }


def summarize_samples(samples):
    """Summarise at least three fresh-process qualified samples."""
    if len(samples) < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Pipeline profiling requires at least three fresh processes."
        )
    identities = [validate_sample(sample) for sample in samples]
    for key in identities[0]:
        if len({identity[key] for identity in identities}) != 1:
            raise RuntimeError(
                "The qualified pipeline {} differs by process.".format(key)
            )
    end_to_end = [sample["end_to_end"] for sample in samples]
    warm_cycles = [
        cycle for sample in samples for cycle in sample["warm"]
    ]
    return {
        "correctness": identities[0],
        "edit": _stage_summary([item["edit"] for item in end_to_end]),
        "end_to_end": _stage_summary(end_to_end),
        "export": _stage_summary(
            [item["export"] for item in end_to_end]
        ),
        "fresh_process_repetitions": len(samples),
        "uncovered_process_cpu_ms": _metric_summary(
            end_to_end,
            "uncovered_process_cpu_ms",
        ),
        "uncovered_wall_ms": _metric_summary(
            end_to_end,
            "uncovered_wall_ms",
        ),
        "validation": _stage_summary(
            [item["exact_validation"] for item in end_to_end]
        ),
        "warm_export": _stage_summary(
            [cycle["export"] for cycle in warm_cycles]
        ),
        "warm_observation_count": len(warm_cycles),
        "warm_reuse_cycle": _stage_summary(
            [cycle["parent"] for cycle in warm_cycles]
        ),
        "warm_validation": _stage_summary(
            [cycle["validation"] for cycle in warm_cycles]
        ),
    }


def _sentinel_payload(output, sentinel=SAMPLE_SENTINEL):
    matches = [
        line[len(sentinel):]
        for line in str(output).splitlines()
        if line.startswith(sentinel)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Expected one {} sentinel; observed {}.".format(
                sentinel.rstrip("="),
                len(matches),
            )
        )
    return json.loads(matches[0])


def _wait_for_gui(client, timeout_seconds=60.0):
    started = time.monotonic()
    last_state = None
    while time.monotonic() - started < timeout_seconds:
        last_state = parse_json_output(execute(client, """
import json
import FreeCADGui as Gui
try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets
main_window = Gui.getMainWindow()
splash_visible = any(
    isinstance(widget, QtWidgets.QSplashScreen) and widget.isVisible()
    for widget in QtWidgets.QApplication.topLevelWidgets()
)
print(json.dumps({
    'main_window_visible': bool(
        main_window is not None and main_window.isVisible()
    ),
    'splash_visible': splash_visible,
}, sort_keys=True))
"""))
        if (
            last_state.get("main_window_visible") is True
            and last_state.get("splash_visible") is False
        ):
            return last_state
        time.sleep(0.25)
    raise TimeoutError(
        "FreeCAD GUI did not become ready: {!r}".format(last_state)
    )


def _close_all_documents(client):
    return parse_json_output(execute(client, """
import json
import FreeCAD as App
closed = sorted(App.listDocuments())
for document_name in list(App.listDocuments()):
    App.closeDocument(document_name)
print(json.dumps({
    'closed': closed,
    'remaining': sorted(App.listDocuments()),
}, sort_keys=True))
"""))


def run_bridge_sample(timeout, output_directory):
    tool_root = PROJECT_ROOT / ".devtools" / "freecad-cli"
    sys.path.insert(0, str(tool_root / "src"))
    from freecad_cli.client import FreeCADClient

    output_directory = output_directory.resolve()
    if not output_directory.is_dir() or any(output_directory.iterdir()):
        raise SystemExit(
            "Bridge sample output must be an existing empty directory"
        )
    token_path = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "rpc-token"
    )
    if not token_path.is_file():
        raise SystemExit(
            "Bridge token not found; launch the isolated GUI first"
        )
    client = FreeCADClient(
        host="127.0.0.1",
        port=19875,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    try:
        ready = _wait_for_gui(client)
        session = parse_json_output(execute(client, """
import json
import FreeCAD as App
print(json.dumps({
    'documents': sorted(App.listDocuments()),
}, sort_keys=True))
"""))
        if session.get("documents"):
            raise RuntimeError(
                "Phase 6 pipeline sample requires an empty session"
            )
        sample_source = GUI_SAMPLE.read_text(encoding="utf-8")
        sample_source += "\nvalidate(pathlib.Path({}))\n".format(
            json.dumps(str(output_directory))
        )
        result = submit_and_wait(
            client,
            sample_source,
            "phase6-transition-pipeline-sample",
            timeout,
        )
        sample = _sentinel_payload(result.get("output"))
        try:
            validate_sample(sample)
        except Exception:
            print(
                RAW_SAMPLE_SENTINEL
                + json.dumps(sample, sort_keys=True),
                flush=True,
            )
            raise
        print(
            SAMPLE_SENTINEL
            + json.dumps(
                {"gui_ready": ready, "result": sample},
                sort_keys=True,
            )
        )
    finally:
        cleanup = _close_all_documents(client)
        if cleanup.get("remaining"):
            raise RuntimeError(
                "Phase 6 pipeline sample leaked a FreeCAD document"
            )


def _run_directory(requested):
    root = RUN_ROOT.resolve()
    if requested is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        run_directory = root / (stamp + "-profile")
    else:
        run_directory = requested.resolve()
        try:
            run_directory.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "Phase 6 pipeline output must remain under {}.".format(
                    root
                )
            ) from error
    if run_directory.exists():
        raise SystemExit(
            "Phase 6 pipeline directory already exists: {}".format(
                run_directory
            )
        )
    run_directory.mkdir(parents=True)
    return run_directory


def _git_record():
    def output(*arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    return {
        "branch": output("branch", "--show-current"),
        "head": output("rev-parse", "HEAD"),
        "status_short": output("status", "--short").splitlines(),
    }


def _environment_record():
    memory_gib = None
    meminfo = pathlib.Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                memory_gib = float(line.split()[1]) / (1024.0 * 1024.0)
                break
    return {
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "memory_gib": memory_gib,
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def _format_sample_log(stdout, stderr, launcher_output=""):
    blocks = []
    if stdout:
        blocks.append("[stdout]\n" + stdout.rstrip())
    if stderr:
        blocks.append("[stderr]\n" + stderr.rstrip())
    if launcher_output:
        blocks.append(
            "[isolated-launcher.log]\n" + launcher_output.rstrip()
        )
    return "\n\n".join(blocks) + "\n"


def _source_record():
    paths = (
        GUI_SAMPLE,
        pathlib.Path(__file__).resolve(),
        PROJECT_ROOT
        / "tests"
        / "freecad_gui_profile_phase5_transition_interaction_range.py",
        PROJECT_ROOT / "tests" / "phase5_transition_coin_gui_harness.py",
        PROJECT_ROOT
        / "tools"
        / "phase5_transition_representative_workload.py",
        PROJECT_ROOT / "tracktemplate" / "api.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "application"
        / "transition_edit.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "application"
        / "transition_exact.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "application"
        / "transition_export.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "adapters"
        / "export"
        / "transition_dxf.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "adapters"
        / "freecad"
        / "transition_exact.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "adapters"
        / "freecad"
        / "transition_state.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "presentation"
        / "transition_coin.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "presentation"
        / "transition_coin_viewprovider.py",
        PROJECT_ROOT
        / "reference"
        / "contracts"
        / "phase1-compatibility.json",
    )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): _sha256(path)
        for path in paths
    }


def _run_fresh_sample(repetition, timeout, run_directory):
    output_directory = run_directory / "sample-{:02d}-output".format(
        repetition
    )
    output_directory.mkdir()
    wrapper = PROJECT_ROOT / "tools" / "freecad_bridge" / "run-isolated"
    command = [
        str(wrapper),
        "/usr/bin/env",
        "PYTHONPATH={}".format(
            PROJECT_ROOT / ".devtools" / "freecad-cli" / "src"
        ),
        "/usr/bin/python3",
        str(pathlib.Path(__file__).resolve()),
        "--bridge-sample",
        "--sample-output",
        str(output_directory),
        "--timeout",
        str(timeout),
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout + 120.0,
    )
    log_path = run_directory / "sample-{:02d}.log".format(repetition)
    launcher_log = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "isolated-launcher.log"
    )
    launcher_output = ""
    if completed.returncode != 0 and launcher_log.is_file():
        launcher_output = launcher_log.read_text(encoding="utf-8")
    log_path.write_text(
        _format_sample_log(
            completed.stdout,
            completed.stderr,
            launcher_output,
        ),
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Fresh GUI pipeline sample {} failed with status {}; see "
            "{}.".format(
                repetition,
                completed.returncode,
                log_path,
            )
        )
    envelope = _sentinel_payload(completed.stdout)
    sample = envelope.get("result")
    validate_sample(sample)
    if envelope.get("gui_ready") != {
        "main_window_visible": True,
        "splash_visible": False,
    }:
        raise RuntimeError(
            "Fresh GUI pipeline readiness evidence drifted."
        )
    return sample


def profile(repetitions, timeout, run_directory):
    """Run and reconcile the requested fresh-process samples."""
    if repetitions < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Pipeline profiling requires at least three fresh processes."
        )
    samples = []
    for repetition in range(1, repetitions + 1):
        sample = _run_fresh_sample(
            repetition,
            timeout,
            run_directory,
        )
        samples.append(sample)
        print(
            "[phase6-transition-pipeline] sample {}/{} passed".format(
                repetition,
                repetitions,
            ),
            flush=True,
        )
    return {
        "samples": samples,
        "summary": summarize_samples(samples),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bridge-sample", action="store_true")
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_PROCESS_REPETITIONS,
    )
    parser.add_argument("--run-dir", type=pathlib.Path)
    parser.add_argument("--sample-output", type=pathlib.Path)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if args.bridge_sample:
        if args.sample_output is None:
            parser.error("--bridge-sample requires --sample-output")
        run_bridge_sample(args.timeout, args.sample_output)
        return
    if args.sample_output is not None:
        parser.error("--sample-output is only valid with --bridge-sample")

    run_directory = _run_directory(args.run_dir)
    result_path = run_directory / "performance.json"
    state = {
        "environment": _environment_record(),
        "git": _git_record(),
        "profile_id": PROFILE_ID,
        "purpose": (
            "Measure one accepted Entry/Exit edit through explicit exact "
            "validation, private-development DXF export and cleanup. The "
            "profile sets no budget, B14-equivalence or output-clearance "
            "claim."
        ),
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "source_sha256": _source_record(),
        "started_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
    }
    try:
        state.update(profile(args.repetitions, args.timeout, run_directory))
        state["status"] = "completed"
    except (Exception, SystemExit) as error:
        state["error"] = "{}: {}".format(type(error).__name__, error)
        state["status"] = "failed"
        raise
    finally:
        state["finished_utc"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        result_path.write_text(
            json.dumps(
                state,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        print(
            PROFILE_SENTINEL
            + json.dumps(
                {
                    "result_path": str(result_path),
                    "status": state.get("status"),
                },
                allow_nan=False,
                sort_keys=True,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
