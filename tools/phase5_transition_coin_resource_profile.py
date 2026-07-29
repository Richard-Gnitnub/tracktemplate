#!/usr/bin/env python3
"""Profile the bounded Phase 5 Coin candidate without setting a budget."""

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
    / "phase5-transition-coin-resource-runs"
)
GUI_SAMPLE = (
    PROJECT_ROOT
    / "tests"
    / "freecad_gui_profile_phase5_transition_coin_resources.py"
)
SAMPLE_SENTINEL = "TRACKTEMPLATE_PHASE5_COIN_RESOURCE_SAMPLE="
PROFILE_SENTINEL = "TRACKTEMPLATE_PHASE5_COIN_RESOURCE_PROFILE="
PROFILE_ID = "phase5-transition-coin-resource-profile-v1"
FIXTURE_OBJECT_COUNT = 32
PREVIEW_SEGMENT_COUNT = 32
WARM_REPETITIONS = 3
DEFAULT_PROCESS_REPETITIONS = 3

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


def _metric_summary(records, path):
    values = []
    for record in records:
        value = record
        for key in path:
            value = value[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise RuntimeError(
                "The qualified profile did not expose finite {}.".format(
                    ".".join(path)
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


def _assert_measurement(record):
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
                "Resource sample measurement {!r} is missing.".format(key)
            )
    recompute = record.get("explicit_recompute")
    if (
        not isinstance(recompute, dict)
        or type(recompute.get("count")) is not int
        or recompute.get("count") != 1
        or type(recompute.get("result")) is not bool
        or any(
            isinstance(recompute.get(key), bool)
            or not isinstance(recompute.get(key), (int, float))
            or not math.isfinite(float(recompute.get(key)))
            for key in ("process_cpu_ms", "wall_ms")
        )
    ):
        raise RuntimeError(
            "Resource sample explicit recompute measurement is invalid."
        )


def _assert_snapshot(snapshot, identity_digest=None, node_count=None):
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("document_object_count")
        != FIXTURE_OBJECT_COUNT
        or snapshot.get("logical_layer_count")
        != FIXTURE_OBJECT_COUNT
        or snapshot.get("proxy_count") != FIXTURE_OBJECT_COUNT
        or snapshot.get("display_modes_added")
        != FIXTURE_OBJECT_COUNT
        or snapshot.get("part_shape_count") != 0
        or snapshot.get("root_children_added") != 0
        or snapshot.get("switch_children_added")
        != FIXTURE_OBJECT_COUNT
        or snapshot.get("cache_regeneration_count")
        != FIXTURE_OBJECT_COUNT
        or not isinstance(
            snapshot.get("active_coin_scene_node_count"),
            int,
        )
        or snapshot.get("active_coin_scene_node_count", 0) <= 0
    ):
        raise RuntimeError(
            "Resource sample object, layer or scene invariant drifted."
        )
    digest = snapshot.get("identity_digest")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise RuntimeError(
            "Resource sample stable identity digest is invalid."
        )
    if (
        identity_digest is not None
        and digest != identity_digest
    ):
        raise RuntimeError(
            "Resource sample stable identity digest drifted."
        )
    if (
        node_count is not None
        and snapshot["active_coin_scene_node_count"] != node_count
    ):
        raise RuntimeError(
            "Resource sample Coin node count grew during warm reuse."
        )


def validate_sample(sample):
    if (
        not isinstance(sample, dict)
        or sample.get("schema_version") != 1
        or sample.get("profile_id") != PROFILE_ID
        or sample.get("freecad_version") != "1.1.1"
    ):
        raise RuntimeError(
            "The resource sample profile or qualified runtime drifted."
        )
    fixture = sample.get("fixture")
    if (
        not isinstance(fixture, dict)
        or fixture.get("logical_object_count")
        != FIXTURE_OBJECT_COUNT
        or fixture.get("preview_segment_count")
        != PREVIEW_SEGMENT_COUNT
        or fixture.get("warm_repetitions") != WARM_REPETITIONS
        or fixture.get("resource_budget_status") != "not-accepted"
    ):
        raise RuntimeError("The bounded resource fixture drifted.")

    cold = sample.get("cold")
    if not isinstance(cold, dict):
        raise RuntimeError("The cold resource observation is missing.")
    _assert_measurement(cold)
    if cold["explicit_recompute"]["result"] is not True:
        raise RuntimeError(
            "The cold explicit recompute did not update the document."
        )
    cold_snapshot = cold.get("snapshot")
    _assert_snapshot(cold_snapshot)
    identity_digest = cold_snapshot["identity_digest"]
    node_count = cold_snapshot["active_coin_scene_node_count"]

    observations = [sample.get("warmup")]
    warm = sample.get("warm")
    if not isinstance(warm, list) or len(warm) != WARM_REPETITIONS:
        raise RuntimeError("The measured warm observation count drifted.")
    observations.extend(warm)
    for observation in observations:
        if (
            not isinstance(observation, dict)
            or observation.get("refresh_changed_count") != 0
            or observation.get("cache_regeneration_delta") != 0
            or observation.get("cache_request_delta")
            != FIXTURE_OBJECT_COUNT
            or observation.get("cache_reuse_delta")
            != FIXTURE_OBJECT_COUNT
        ):
            raise RuntimeError(
                "The unchanged warm refresh contract drifted."
            )
        recompute = observation.get("explicit_recompute")
        if (
            not isinstance(recompute, dict)
            or type(recompute.get("count")) is not int
            or recompute.get("count") != 1
            or recompute.get("result") is not False
        ):
            raise RuntimeError(
                "The unchanged warm explicit recompute contract drifted."
            )
        _assert_snapshot(
            observation.get("snapshot"),
            identity_digest=identity_digest,
            node_count=node_count,
        )
    for observation in warm:
        _assert_measurement(observation)

    cleanup = sample.get("cleanup")
    if (
        not isinstance(cleanup, dict)
        or cleanup.get("disposed_proxy_count")
        != FIXTURE_OBJECT_COUNT
        or cleanup.get("discarded_cache_count")
        != FIXTURE_OBJECT_COUNT
        or cleanup.get("object_count_before_close")
        != FIXTURE_OBJECT_COUNT
        or cleanup.get("remaining_documents") != []
    ):
        raise RuntimeError("The resource sample cleanup contract drifted.")
    for key in (
        "process_cpu_ms",
        "rss_after_mb",
        "rss_before_mb",
        "rss_delta_mb",
        "wall_ms",
    ):
        value = cleanup.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise RuntimeError(
                "The resource sample cleanup measurement is missing."
            )
    return identity_digest


def summarize_samples(samples):
    if len(samples) < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Coin resource profiling requires at least three fresh processes."
        )
    identity_digests = [validate_sample(sample) for sample in samples]
    if len(set(identity_digests)) != 1:
        raise RuntimeError(
            "Stable identity evidence differs between fresh processes."
        )
    node_counts = [
        sample["cold"]["snapshot"]["active_coin_scene_node_count"]
        for sample in samples
    ]
    if len(set(node_counts)) != 1:
        raise RuntimeError(
            "Active Coin scene node counts differ between fresh processes."
        )
    cold = [sample["cold"] for sample in samples]
    warm = [
        observation
        for sample in samples
        for observation in sample["warm"]
    ]
    metric_paths = {
        "process_cpu_ms": ("process_cpu_ms",),
        "recompute_process_cpu_ms": (
            "explicit_recompute",
            "process_cpu_ms",
        ),
        "recompute_wall_ms": ("explicit_recompute", "wall_ms"),
        "rss_after_mb": ("rss_after_mb",),
        "rss_before_mb": ("rss_before_mb",),
        "rss_delta_mb": ("rss_delta_mb",),
        "wall_ms": ("wall_ms",),
    }
    return {
        "cold": {
            name: _metric_summary(cold, path)
            for name, path in metric_paths.items()
        },
        "correctness": {
            "cache_regeneration_delta_values": [
                observation["cache_regeneration_delta"]
                for observation in warm
            ],
            "cache_reuse_delta_values": [
                observation["cache_reuse_delta"]
                for observation in warm
            ],
            "active_coin_scene_node_count_values": node_counts,
            "cold_recompute_result_values": [
                sample["cold"]["explicit_recompute"]["result"]
                for sample in samples
            ],
            "document_object_count_values": [
                sample["cold"]["snapshot"]["document_object_count"]
                for sample in samples
            ],
            "identity_digest": identity_digests[0],
            "logical_layer_count_values": [
                sample["cold"]["snapshot"]["logical_layer_count"]
                for sample in samples
            ],
            "part_shape_count_values": [
                sample["cold"]["snapshot"]["part_shape_count"]
                for sample in samples
            ],
            "warm_recompute_result_values": [
                observation["explicit_recompute"]["result"]
                for observation in warm
            ],
        },
        "fresh_process_repetitions": len(samples),
        "measured_warm_observations": len(warm),
        "warm": {
            name: _metric_summary(warm, path)
            for name, path in metric_paths.items()
        },
        "warm_repetitions_per_process": WARM_REPETITIONS,
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


def run_bridge_sample(timeout):
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
        session = parse_json_output(execute(
            client,
            """
import json
import FreeCAD as App
print(json.dumps({
    'documents': sorted(App.listDocuments()),
}, sort_keys=True))
""",
        ))
        if session.get("documents"):
            raise RuntimeError(
                "Phase 5 resource sample requires an empty isolated session"
            )
        result = submit_and_wait(
            client,
            GUI_SAMPLE.read_text(encoding="utf-8"),
            "phase5-transition-coin-resource-sample",
            timeout,
        )
        sample = _sentinel_payload(result.get("output"))
        validate_sample(sample)
        print(
            SAMPLE_SENTINEL
            + json.dumps(
                {
                    "gui_ready": ready,
                    "result": sample,
                },
                sort_keys=True,
            )
        )
    finally:
        cleanup = _close_all_documents(client)
        if cleanup.get("remaining"):
            raise RuntimeError(
                "Phase 5 resource sample leaked a FreeCAD document"
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
                "Phase 5 resource output must remain under {}.".format(
                    root
                )
            ) from error
    if run_directory.exists():
        raise SystemExit(
            "Phase 5 resource directory already exists: {}".format(
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
        / "tracktemplate"
        / "adapters"
        / "freecad"
        / "transition_state.py",
        PROJECT_ROOT
        / "tracktemplate"
        / "application"
        / "transition_derived.py",
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
    )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): _sha256(path)
        for path in paths
    }


def profile(repetitions, timeout, run_directory):
    if repetitions < DEFAULT_PROCESS_REPETITIONS:
        raise ValueError(
            "Coin resource profiling requires at least three fresh processes."
        )
    wrapper = PROJECT_ROOT / "tools" / "freecad_bridge" / "run-isolated"
    samples = []
    gui_ready = []
    launcher_log = (
        PROJECT_ROOT
        / "benchmark-output"
        / "freecad-bridge"
        / "isolated-launcher.log"
    )
    for repetition in range(1, repetitions + 1):
        command = [
            str(wrapper),
            "/usr/bin/env",
            "PYTHONPATH={}".format(
                PROJECT_ROOT / ".devtools" / "freecad-cli" / "src"
            ),
            "/usr/bin/python3",
            str(pathlib.Path(__file__).resolve()),
            "--bridge-sample",
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
                "Fresh GUI sample {} failed with status {}; see {}.".format(
                    repetition,
                    completed.returncode,
                    log_path,
                )
            )
        envelope = _sentinel_payload(completed.stdout)
        sample = envelope.get("result")
        validate_sample(sample)
        ready = envelope.get("gui_ready")
        if ready != {
            "main_window_visible": True,
            "splash_visible": False,
        }:
            raise RuntimeError(
                "Fresh GUI sample readiness evidence drifted."
            )
        gui_ready.append(ready)
        samples.append(sample)
        print(
            "[phase5-coin-resource] sample {}/{} passed".format(
                repetition,
                repetitions,
            ),
            flush=True,
        )
    return {
        "gui_ready": gui_ready,
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
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if args.bridge_sample:
        run_bridge_sample(args.timeout)
        return

    run_directory = _run_directory(args.run_dir)
    result_path = run_directory / "performance.json"
    state = {
        "environment": _environment_record(),
        "git": _git_record(),
        "profile_id": PROFILE_ID,
        "purpose": (
            "Bounded Coin candidate evidence; does not establish a "
            "representative workload, accepted capacity, interaction "
            "budget or optimisation claim."
        ),
        "schema_version": 1,
        "source_sha256": _source_record(),
        "started_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
    }
    try:
        result = profile(
            args.repetitions,
            args.timeout,
            run_directory,
        )
        state.update(result)
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
