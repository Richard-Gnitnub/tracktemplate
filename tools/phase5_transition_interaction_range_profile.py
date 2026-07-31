#!/usr/bin/env python3
"""Profile a bounded transition interaction range without accepting it."""

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
    / "phase5-transition-interaction-range-runs"
)
GUI_SAMPLE = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_profile_phase5_transition_interaction_range.py"
)
GUI_HARNESS = (
    PROJECT_ROOT
    / "tests"
    / "phase5_transition_coin_gui_harness.py"
)
SAMPLE_SENTINEL = "TRACKTEMPLATE_PHASE5_INTERACTION_RANGE_SAMPLE="
RAW_SAMPLE_SENTINEL = (
    "TRACKTEMPLATE_PHASE5_INTERACTION_RANGE_RAW_SAMPLE="
)
PROFILE_SENTINEL = "TRACKTEMPLATE_PHASE5_INTERACTION_RANGE_PROFILE="
PROFILE_ID = "phase5-transition-interaction-range-profile-v1"
SCALE_SET_COUNTS = (1, 2, 4, 8, 16)
OBJECTS_PER_SET = 2
PREVIEW_SEGMENT_COUNT = 32
DEFAULT_PROCESS_REPETITIONS = 3

sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    parse_json_output,
    submit_and_wait,
)
from tracktemplate.domain.alignment import (  # noqa: E402
    GEOMETRY_TOLERANCE,
)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metric_summary(records, key):
    values = []
    for record in records:
        value = record.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise RuntimeError(
                "The interaction profile did not expose finite {}.".format(
                    key
                )
            )
        values.append(float(value))
    return {
        "count": len(values),
        "maximum": max(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "range": max(values) - min(values),
        "values": values,
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


def _assert_measurement(record, label):
    if not isinstance(record, dict):
        raise RuntimeError(
            "The {} interaction measurement is missing.".format(label)
        )
    for key in (
        "process_cpu_ms",
        "rss_after_mb",
        "rss_before_mb",
        "rss_delta_mb",
        "wall_ms",
    ):
        value = record.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise RuntimeError(
                "The {} interaction measurement {!r} is missing.".format(
                    label,
                    key,
                )
            )


def _valid_digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _assert_snapshot(snapshot, set_count):
    object_count = set_count * OBJECTS_PER_SET
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("document_object_count") != object_count
        or snapshot.get("logical_layer_count") != object_count
        or snapshot.get("proxy_count") != object_count
        or snapshot.get("display_modes_added") != object_count
        or snapshot.get("part_shape_count") != 0
        or snapshot.get("root_children_added") != 0
        or snapshot.get("switch_children_added") != object_count
        or snapshot.get("active_coin_scene_node_count")
        != object_count * 8
        or not _valid_digest(snapshot.get("mapping_digest"))
        or not _valid_digest(snapshot.get("canonical_state_digest"))
    ):
        raise RuntimeError(
            "The interaction sample object, layer or scene invariant drifted."
        )


def _expected_target_transition_id(set_count):
    return "SET-{:03d}/curve-track/2/transition/exit".format(
        set_count // 2 + 1
    )


def validate_sample(sample, expected_set_count):
    if expected_set_count not in SCALE_SET_COUNTS:
        raise ValueError("expected_set_count is outside the declared range")
    if (
        not isinstance(sample, dict)
        or sample.get("schema_version") != 1
        or sample.get("profile_id") != PROFILE_ID
        or sample.get("freecad_version") != "1.1.1"
    ):
        raise RuntimeError(
            "The interaction sample profile or qualified runtime drifted."
        )
    object_count = expected_set_count * OBJECTS_PER_SET
    target_transition_id = _expected_target_transition_id(
        expected_set_count
    )
    fixture = sample.get("fixture")
    if (
        not isinstance(fixture, dict)
        or fixture.get("set_count") != expected_set_count
        or fixture.get("logical_object_count") != object_count
        or fixture.get("preview_segment_count")
        != PREVIEW_SEGMENT_COUNT
        or fixture.get("capacity_status") != "not-accepted"
        or fixture.get("family_unit")
        != "qualified-one-secondary-track-entry-exit-pair"
        or fixture.get("target_transition_id")
        != target_transition_id
        or fixture.get("view_layout")
        != "test-only-grid-translations"
    ):
        raise RuntimeError("The interaction range fixture drifted.")

    for label in (
        "cold",
        "selection",
        "dialog_open",
        "edit",
        "undo",
        "cleanup",
    ):
        _assert_measurement(sample.get(label), label)

    cold_snapshot = sample["cold"].get("snapshot")
    _assert_snapshot(cold_snapshot, expected_set_count)
    if (
        cold_snapshot.get("cache_regeneration_count") != object_count
        or cold_snapshot.get("cache_request_count") != object_count * 2
        or cold_snapshot.get("cache_reuse_count") != object_count
    ):
        raise RuntimeError(
            "The interaction sample cold cache contract drifted."
        )
    mapping_digest = cold_snapshot["mapping_digest"]
    canonical_digest = cold_snapshot["canonical_state_digest"]

    selection = sample["selection"]
    pointer_target = selection.get("pointer_target")
    if (
        selection.get("selected_transition_id")
        != target_transition_id
        or selection.get("mapping_domain_id") != target_transition_id
        or not isinstance(selection.get("pick_callback_count"), int)
        or selection.get("pick_callback_count", 0) < 1
        or not isinstance(pointer_target, dict)
        or pointer_target.get("unique_mapping_count") != 1
        or not isinstance(pointer_target.get("hit_record_count"), int)
        or pointer_target.get("hit_record_count", 0) < 1
    ):
        raise RuntimeError(
            "The interaction sample selection contract drifted."
        )

    dialog = sample["dialog_open"]
    if (
        dialog.get("selected_identity_visible") is not True
        or dialog.get("selected_length_text") != "420.000"
    ):
        raise RuntimeError(
            "The interaction sample dialog contract drifted."
        )

    edit = sample["edit"]
    edit_snapshot = edit.get("snapshot")
    _assert_snapshot(edit_snapshot, expected_set_count)
    if (
        edit.get("cache_regeneration_delta") != 1
        or edit.get("cache_request_delta") != 1
        or edit.get("changed_transition_ids")
        != [target_transition_id]
        or edit.get("history_delta") != 1
        or isinstance(edit.get("target_length_mm"), bool)
        or not isinstance(edit.get("target_length_mm"), (int, float))
        or not math.isclose(
            float(edit["target_length_mm"]),
            360.0,
            rel_tol=0.0,
            abs_tol=GEOMETRY_TOLERANCE,
        )
        or edit.get("unchanged_record_count") != object_count - 1
        or edit_snapshot.get("mapping_digest") != mapping_digest
        or edit_snapshot.get("canonical_state_digest")
        == canonical_digest
    ):
        raise RuntimeError(
            "The interaction sample edit isolation contract drifted."
        )

    undo = sample["undo"]
    undo_snapshot = undo.get("snapshot")
    _assert_snapshot(undo_snapshot, expected_set_count)
    if (
        undo.get("cache_regeneration_delta") != 1
        or undo.get("cache_request_delta") != 1
        or undo.get("history_delta") != -1
        or isinstance(undo.get("target_length_mm"), bool)
        or not isinstance(undo.get("target_length_mm"), (int, float))
        or not math.isclose(
            float(undo["target_length_mm"]),
            420.0,
            rel_tol=0.0,
            abs_tol=GEOMETRY_TOLERANCE,
        )
        or undo_snapshot.get("mapping_digest") != mapping_digest
        or undo_snapshot.get("canonical_state_digest")
        != canonical_digest
    ):
        raise RuntimeError(
            "The interaction sample mapping drifted during Undo."
        )

    cleanup = sample["cleanup"]
    if (
        cleanup.get("disposed_proxy_count") != object_count
        or cleanup.get("discarded_cache_count") != object_count
        or cleanup.get("object_count_before_close") != object_count
        or cleanup.get("remaining_documents") != []
    ):
        raise RuntimeError(
            "The interaction sample cleanup contract drifted."
        )
    return {
        "mapping_digest": mapping_digest,
        "target_transition_id": target_transition_id,
    }


def _summarize_scale(set_count, samples):
    if len(samples) < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Each scale requires at least three fresh processes."
        )
    identities = [
        validate_sample(sample, set_count) for sample in samples
    ]
    if len({item["mapping_digest"] for item in identities}) != 1:
        raise RuntimeError(
            "Stable mapping evidence differs between fresh processes."
        )
    metric_keys = (
        "process_cpu_ms",
        "rss_after_mb",
        "rss_before_mb",
        "rss_delta_mb",
        "wall_ms",
    )
    stages = (
        "cold",
        "selection",
        "dialog_open",
        "edit",
        "undo",
        "cleanup",
    )
    return {
        "correctness": {
            "active_coin_scene_node_count_values": [
                sample["cold"]["snapshot"][
                    "active_coin_scene_node_count"
                ]
                for sample in samples
            ],
            "document_object_count_values": [
                sample["cold"]["snapshot"]["document_object_count"]
                for sample in samples
            ],
            "mapping_digest": identities[0]["mapping_digest"],
            "part_shape_count_values": [
                sample["cold"]["snapshot"]["part_shape_count"]
                for sample in samples
            ],
            "selected_transition_id_values": [
                item["target_transition_id"] for item in identities
            ],
        },
        "fresh_process_repetitions": len(samples),
        "logical_object_count": set_count * OBJECTS_PER_SET,
        "set_count": set_count,
        **{
            stage: {
                key: _metric_summary(
                    [sample[stage] for sample in samples],
                    key,
                )
                for key in metric_keys
            }
            for stage in stages
        },
    }


def summarize_samples(samples_by_scale):
    if set(samples_by_scale) != set(SCALE_SET_COUNTS):
        raise ValueError(
            "Samples must cover the exact declared scale range."
        )
    scales = {
        str(set_count): _summarize_scale(
            set_count,
            samples_by_scale[set_count],
        )
        for set_count in SCALE_SET_COUNTS
    }
    return {
        "fresh_processes_total": sum(
            len(samples_by_scale[set_count])
            for set_count in SCALE_SET_COUNTS
        ),
        "scale_set_counts": list(SCALE_SET_COUNTS),
        "scales": scales,
    }


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


def run_bridge_sample(timeout, set_count):
    if set_count not in SCALE_SET_COUNTS:
        raise ValueError("set_count is outside the declared scale range")
    tool_root = PROJECT_ROOT / ".devtools" / "freecad-cli"
    sys.path.insert(0, str(tool_root / "src"))
    from freecad_cli.client import FreeCADClient

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
                "Phase 5 interaction sample requires an empty session"
            )
        sample_source = GUI_SAMPLE.read_text(encoding="utf-8")
        sample_source += "\nvalidate({})\n".format(set_count)
        result = submit_and_wait(
            client,
            sample_source,
            "phase5-transition-interaction-range-sample",
            timeout,
        )
        sample = _sentinel_payload(result.get("output"))
        try:
            validate_sample(sample, set_count)
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
                "Phase 5 interaction sample leaked a FreeCAD document"
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
                "Phase 5 interaction output must remain under {}.".format(
                    root
                )
            ) from error
    if run_directory.exists():
        raise SystemExit(
            "Phase 5 interaction directory already exists: {}".format(
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
        GUI_HARNESS,
        pathlib.Path(__file__).resolve(),
        PROJECT_ROOT
        / "tools"
        / "phase5_transition_representative_workload.py",
        PROJECT_ROOT / "tracktemplate" / "application" / "transition_edit.py",
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
        / "tracktemplate"
        / "presentation"
        / "transition_preview.py",
        PROJECT_ROOT / "tracktemplate" / "ui" / "transition_parameter_editor.py",
    )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): _sha256(path)
        for path in paths
    }


def _sample_order(repetition):
    if repetition % 2:
        return SCALE_SET_COUNTS
    return tuple(reversed(SCALE_SET_COUNTS))


def _run_fresh_sample(
    set_count,
    repetition,
    timeout,
    run_directory,
):
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
        "--set-count",
        str(set_count),
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
    log_path = run_directory / "sets-{:02d}-sample-{:02d}.log".format(
        set_count,
        repetition,
    )
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
            "Fresh GUI scale {} sample {} failed with status {}; see {}.".format(
                set_count,
                repetition,
                completed.returncode,
                log_path,
            )
        )
    envelope = _sentinel_payload(completed.stdout)
    sample = envelope.get("result")
    validate_sample(sample, set_count)
    if envelope.get("gui_ready") != {
        "main_window_visible": True,
        "splash_visible": False,
    }:
        raise RuntimeError(
            "Fresh GUI interaction readiness evidence drifted."
        )
    return sample


def profile(repetitions, timeout, run_directory):
    if repetitions < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Interaction profiling requires at least three fresh processes."
        )
    samples_by_scale = {set_count: [] for set_count in SCALE_SET_COUNTS}
    sample_order = []
    total = repetitions * len(SCALE_SET_COUNTS)
    completed_count = 0
    for repetition in range(1, repetitions + 1):
        for set_count in _sample_order(repetition):
            sample = _run_fresh_sample(
                set_count,
                repetition,
                timeout,
                run_directory,
            )
            samples_by_scale[set_count].append(sample)
            sample_order.append({
                "repetition": repetition,
                "set_count": set_count,
            })
            completed_count += 1
            print(
                "[phase5-interaction-range] sample {}/{} "
                "({} sets) passed".format(
                    completed_count,
                    total,
                    set_count,
                ),
                flush=True,
            )
    return {
        "sample_order": sample_order,
        "samples_by_scale": {
            str(set_count): samples_by_scale[set_count]
            for set_count in SCALE_SET_COUNTS
        },
        "summary": summarize_samples(samples_by_scale),
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
    parser.add_argument("--set-count", type=int)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if args.bridge_sample:
        if args.set_count is None:
            parser.error("--bridge-sample requires --set-count")
        run_bridge_sample(args.timeout, args.set_count)
        return
    if args.set_count is not None:
        parser.error("--set-count is only valid with --bridge-sample")

    run_directory = _run_directory(args.run_dir)
    result_path = run_directory / "performance.json"
    state = {
        "environment": _environment_record(),
        "git": _git_record(),
        "profile_id": PROFILE_ID,
        "purpose": (
            "Bounded scaling evidence built from the qualified family unit; "
            "it does not accept a capacity, interaction budget, renderer or "
            "optimisation claim."
        ),
        "schema_version": 1,
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
