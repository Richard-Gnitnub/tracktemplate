#!/usr/bin/env python3
"""Observe one first Core Generate per process in three matched pairs.

This diagnostic retains nested wall and process CPU intervals, explicit
unobserved remainders and observed-minus-control distributions. It defines
no optimisation, budget, warm-reuse or phase acceptance claim.
"""

import argparse
import ast
import datetime
import functools
import json
import math
import os
import pathlib
import platform
import shutil
import statistics
import subprocess
import sys
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import core_generate_baseline as baseline  # noqa: E402
from tools import core_generate_line_observer as lines  # noqa: E402


PROFILE = "phase9b-core-generate-attribution-v1"
SENTINEL = "CORE_GENERATE_ATTRIBUTION_PASS"
PROBE = ROOT / "tools/freecad_bridge/probes/core_generate_attribution.py"
RUN_ROOT = ROOT / "benchmark-output/core-generate-attribution"
ORDER = (
    ("control", "observed"),
    ("observed", "control"),
    ("control", "observed"),
)
CLOCKS = ("wall", "process_cpu")
CHECKS = (baseline.CHECKS - {"repeated_contract_equal"}) | {
    "observer_restored",
}
NEW_FILES = (
    "tools/core_generate_attribution.py",
    "tools/freecad_bridge/probes/core_generate_attribution.py",
    "tests/validate_core_generate_attribution.py",
    "tools/core_generate_line_observer.py",
    "tests/validate_core_generate_line_observer.py",
)


def baseline_definitions(source, filename):
    """Compile the baseline unchanged except its checked final invocation."""
    tree = ast.parse(source, filename=filename)
    final = tree.body[-1]
    if not (
        isinstance(final, ast.Expr)
        and isinstance(final.value, ast.Call)
        and isinstance(final.value.func, ast.Name)
        and final.value.func.id == "_run"
        and not final.value.args
        and not final.value.keywords
    ):
        raise ValueError("Baseline final call differs from bare _run()")
    tree.body.pop()
    return compile(tree, filename, "exec")


def callable_code(function):
    """Resolve the actual loaded callable without changing any binding."""
    while isinstance(function, functools.partial):
        function = function.func
    if not hasattr(function, "__code__"):
        function = function.__call__
    return function.__code__


class Observer:
    """Collect selected Python frames on this thread; retain integer ns."""

    def __init__(self, targets):
        self.targets = {}
        self.mapping = []
        for name, classification, code in targets:
            if code in self.targets:
                raise ValueError("Selected callable codes collide")
            self.targets[code] = (name, classification)
            self.mapping.append(
                {
                    "name": name,
                    "classification": classification,
                    "filename": code.co_filename,
                    "first_line": code.co_firstlineno,
                    "qualname": code.co_qualname,
                }
            )
        self.spans = []
        self.stack = []
        self.errors = []
        self.previous = None
        self.restored = False
        self.callback = self._event

    def _event(self, frame, event, _argument):
        target = self.targets.get(frame.f_code)
        if target is None or event not in ("call", "return"):
            return
        try:
            wall = time.perf_counter_ns()
            cpu = time.process_time_ns()
            if event == "call":
                span = {
                    "id": len(self.spans),
                    "parent": (
                        self.stack[-1][1]["id"] if self.stack else None
                    ),
                    "name": target[0],
                    "classification": target[1],
                    "wall_start_ns": wall,
                    "process_cpu_start_ns": cpu,
                }
                self.spans.append(span)
                self.stack.append((frame, span))
            elif not self.stack or self.stack[-1][0] is not frame:
                self.errors.append("Unbalanced selected return")
            else:
                _frame, span = self.stack.pop()
                span.update(wall_end_ns=wall, process_cpu_end_ns=cpu)
        except BaseException as error:
            # A callback failure invalidates evidence, never product routing.
            self.errors.append(type(error).__name__ + ": " + str(error))

    def __enter__(self):
        self.previous = sys.getprofile()
        if self.previous is not None:
            raise RuntimeError("An existing profiler owns this thread")
        sys.setprofile(self.callback)
        return self

    def __exit__(self, _kind, _value, _traceback):
        owned = sys.getprofile() is self.callback
        sys.setprofile(self.previous)
        self.restored = sys.getprofile() is self.previous
        if not owned:
            self.errors.append("Profile ownership changed during action")
        if self.stack:
            self.errors.append("Selected frames remain open")
        return False

    def result(self, action):
        if self.errors or not self.restored:
            raise ValueError("Invalid observer: " + repr(self.errors))
        return reconcile_spans(action, self.spans, self.mapping)


def reconcile_spans(action, spans, mapping):
    """Reconcile integer spans shared by the two diagnostic observers."""
    spans = [dict(span) for span in spans]
    for span in spans:
        children = [item for item in spans if item["parent"] == span["id"]]
        span["remainder_ns"] = {
            clock: span[clock + "_end_ns"]
            - span[clock + "_start_ns"]
            - sum(
                child[clock + "_end_ns"] - child[clock + "_start_ns"]
                for child in children
            )
            for clock in CLOCKS
        }
    roots = [span for span in spans if span["parent"] is None]
    if len(roots) != 1 or roots[0]["name"] != "run_macro":
        raise ValueError("Expected exactly one observed run_macro")
    result = {
        "spans": spans,
        "mapping": mapping,
        "boundary_remainder_ns": {
            clock: round(action[clock + "_ms"] * 1000000)
            - (roots[0][clock + "_end_ns"] - roots[0][clock + "_start_ns"])
            for clock in CLOCKS
        },
    }
    validate_attribution(action, result)
    return result


def _integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("Expected finite nonnegative integer nanoseconds")
    return value


def validate_attribution(action, attribution):
    """Reconcile each invocation before any distribution is calculated."""
    spans = attribution.get("spans", [])
    if not spans or [span.get("id") for span in spans] != list(
        range(len(spans))
    ):
        raise ValueError("Span IDs are absent, duplicate or unordered")
    roots = [span for span in spans if span.get("parent") is None]
    if len(roots) != 1 or roots[0].get("name") != "run_macro":
        raise ValueError("Expected exactly one run_macro root")
    for span in spans:
        parent = span.get("parent")
        if parent is not None and (
            type(parent) is not int or not 0 <= parent < span["id"]
        ):
            raise ValueError("Invalid span parent")
        if not isinstance(span.get("name"), str) or span.get(
            "classification"
        ) not in {
            "operator action",
            "nested component",
            "harness enclosing",
        }:
            raise ValueError("Missing span name or classification")
        children = [item for item in spans if item.get("parent") == span["id"]]
        for clock in CLOCKS:
            start = _integer(span.get(clock + "_start_ns"))
            end = _integer(span.get(clock + "_end_ns"))
            if end < start:
                raise ValueError("Negative span duration")
            cursor = start
            total = 0
            for child in children:
                child_start = _integer(child.get(clock + "_start_ns"))
                child_end = _integer(child.get(clock + "_end_ns"))
                if child_start < cursor or child_end > end:
                    raise ValueError("Child overlap or containment failure")
                total += child_end - child_start
                cursor = child_end
            remainder = _integer(span.get("remainder_ns", {}).get(clock))
            if total + remainder != end - start:
                raise ValueError("Direct children plus remainder differ")
    for clock in CLOCKS:
        remainder = _integer(
            attribution.get(
                "boundary_remainder_ns",
                {},
            ).get(clock)
        )
        root = roots[0]
        if root[clock + "_end_ns"] - root[
            clock + "_start_ns"
        ] + remainder != round(action[clock + "_ms"] * 1000000):
            raise ValueError("External action boundary does not reconcile")
    return attribution


def profile_settings(profile):
    """Keep the earlier profile as the default; reject unknown profiles."""
    if profile == PROFILE:
        return SENTINEL, RUN_ROOT
    if profile == lines.PROFILE:
        return lines.SENTINEL, ROOT / "benchmark-output/core-generate-lines"
    raise ValueError("Unknown Core Generate diagnostic profile")


def validate_probe(report, mode, profile=PROFILE):
    """Require the first action, correctness witnesses and restored state."""
    sentinel, _run_root = profile_settings(profile)
    if (
        report.get("profile_id") != profile
        or report.get("schema_version") != 1
        or report.get("status") != "completed"
        or report.get("sentinel") != sentinel
        or report.get("mode") != mode
        or not report.get("host_profile_id")
    ):
        raise ValueError("Incomplete attribution identity")
    checks = report.get("checks", {})
    if set(checks) != CHECKS or any(
        value is not True for value in checks.values()
    ):
        raise ValueError("Correctness or preservation witness failed")
    action = report.get("action", {})
    if (
        action.get("label") != "first-generate"
        or action.get("status") != "completed"
        or action.get("previous_outputs_preserved") is not True
        or action.get("payload_count") != 13
    ):
        raise ValueError("Incomplete first Generate")
    for key in ("wall_ms", "process_cpu_ms", "rss_before_mb", "rss_after_mb"):
        value = action.get(key)
        if (
            type(value) not in (float, int)
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError("Invalid action metric")
    for key in ("objects_before", "objects_after"):
        _integer(action.get(key))
    digest = action.get("output_contract_sha256", "")
    if (
        len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
        or not action.get("output_dir")
    ):
        raise ValueError("Missing output identity")
    if mode == "observed":
        validator = (
            lines.validate_lines
            if profile == lines.PROFILE
            else validate_attribution
        )
        validator(action, report.get("attribution", {}))
    elif mode != "control" or report.get("attribution") is not None:
        raise ValueError("Control contains observer evidence")
    return report


def _distribution(values):
    median = statistics.median(values)
    return {
        "values": values,
        "median": median,
        "minimum": min(values),
        "maximum": max(values),
        "mad": statistics.median(
            [abs(value - median) for value in values],
        ),
    }


def summarize(samples, profile=PROFILE):
    """Retain three paired differences; never subtract stage medians."""
    sequence = [
        (block, mode) for block, order in enumerate(ORDER, 1) for mode in order
    ]
    if [(item.get("block"), item.get("mode")) for item in samples] != sequence:
        raise ValueError("Predeclared paired order differs")
    for sample in samples:
        if (
            sample.get("status") != "completed"
            or sample.get("cleanup") != {"remaining": []}
            or not sample.get("source_before")
            or sample.get("source_before") != sample.get("source_after")
            or sample.get("source_before") != samples[0].get("source_before")
            or sample.get("fixture_before") != baseline.FIXTURE_SHA256
            or sample.get("fixture_after") != baseline.FIXTURE_SHA256
        ):
            raise ValueError("Sample preservation or cleanup failed")
        validate_probe(sample["probe"], sample["mode"], profile)
    for key in ("host_profile_id",):
        if len({item["probe"][key] for item in samples}) != 1:
            raise ValueError("Host profiles differ")
    actions = [item["probe"]["action"] for item in samples]
    if (
        len({item["output_contract_sha256"] for item in actions}) != 1
        or len({item["output_dir"] for item in actions}) != 6
        or len({item.get("isolated_instance_id") for item in samples}) != 6
    ):
        raise ValueError("Output contracts, directories or processes differ")
    grouped = {
        mode: [item for item in samples if item["mode"] == mode]
        for mode in ("control", "observed")
    }
    if profile == lines.PROFILE:
        sources = [
            item["probe"]["attribution"]["source"]
            for item in grouped["observed"]
        ]
        if any(source != sources[0] for source in sources):
            raise ValueError("Observed source/code provenance differs")
    result = {"action": {}, "observer_difference": {}, "exclusive_areas": {}}
    for clock in CLOCKS:
        values = {
            mode: [item["probe"]["action"][clock + "_ms"] for item in group]
            for mode, group in grouped.items()
        }
        result["action"][clock + "_ms"] = {
            mode: _distribution(data) for mode, data in values.items()
        }
        result["observer_difference"][clock + "_ms"] = _distribution(
            [
                observed - control
                for control, observed in zip(
                    values["control"], values["observed"]
                )
            ]
        )
    per_run = []
    for sample in grouped["observed"]:
        areas = {}
        for span in sample["probe"]["attribution"]["spans"]:
            area = areas.setdefault(
                span["name"], {clock: 0 for clock in CLOCKS}
            )
            for clock in CLOCKS:
                area[clock] += span["remainder_ns"][clock]
        areas["external_boundary_remainder"] = sample["probe"]["attribution"][
            "boundary_remainder_ns"
        ]
        per_run.append(areas)
    names = set(per_run[0])
    if any(set(areas) != names for areas in per_run):
        raise ValueError("Observed callable coverage differs across runs")
    for name in sorted(names):
        result["exclusive_areas"][name] = {
            clock + "_ns": _distribution(
                [areas[name][clock] for areas in per_run]
            )
            for clock in CLOCKS
        }
    result["largest_exclusive_areas"] = {
        clock: sorted(
            names,
            key=lambda name: result["exclusive_areas"][name][clock + "_ns"][
                "median"
            ],
            reverse=True,
        )
        for clock in CLOCKS
    }
    if profile == lines.PROFILE:
        result["inclusive_source_line_areas"] = result.pop("exclusive_areas")
        result["largest_inclusive_source_line_areas"] = result.pop(
            "largest_exclusive_areas"
        )
    return result


def _sources():
    sources = baseline._sources()
    sources.update({name: baseline._hash(ROOT / name) for name in NEW_FILES})
    return sources


def _finish_sample(record, base, directory, client):
    """Always retain failed records, including client BaseException exits."""
    try:
        try:
            record["cleanup"] = baseline._close_documents(client)
        except BaseException as error:
            record.update(status="failed", cleanup_error=repr(error))
        try:
            record["source_after"] = _sources()
            record["fixture_after"] = baseline._hash(base)
        except BaseException as error:
            record.update(status="failed", preservation_error=repr(error))
    finally:
        baseline._write(directory / "sample.json", record)


def _sample(base, directory, timeout, mode, block, profile=PROFILE):
    instance = os.environ.get("TRACKTEMPLATE_BRIDGE_INSTANCE_FILE")
    if (
        os.environ.get("TRACKTEMPLATE_ATTRIBUTION_CHILD") != "1"
        or not instance
        or not pathlib.Path(instance).read_text().strip().isdigit()
    ):
        raise RuntimeError("Attribution needs its isolated child instance")
    sys.path.insert(0, str(ROOT / ".devtools/freecad-cli/src"))
    from freecad_cli.client import FreeCADClient
    from tools.freecad_bridge.orchestration import (
        execute,
        parse_json_output,
        submit_and_wait,
    )

    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    client = FreeCADClient(
        host="127.0.0.1",
        port=19875,
        timeout=30,
        token=token.read_text().strip(),
    )
    record = {
        "status": "started",
        "mode": mode,
        "block": block,
        "source_before": _sources(),
        "fixture_before": baseline._hash(base),
        "isolated_instance_id": pathlib.Path(instance).read_text().strip(),
    }
    baseline._write(directory / "sample.json", record)
    try:
        copied = directory / "input.FCStd"
        shutil.copy2(base, copied)
        execute(
            client,
            "\n".join(
                (
                    "import FreeCAD as App",
                    "if App.listDocuments():",
                    "    raise RuntimeError('Expected an empty isolated session')",
                    "App.openDocument({!r})".format(str(copied)),
                )
            ),
        )
        code = "\n".join(
            (
                "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'",
                "TRACKTEMPLATE_ATTRIBUTION_DIRECTORY = {!r}".format(
                    str(directory)
                ),
                "TRACKTEMPLATE_ATTRIBUTION_MODE = {!r}".format(mode),
                "TRACKTEMPLATE_ATTRIBUTION_PROFILE = {!r}".format(profile),
                baseline.LOADER.read_text(),
                PROBE.read_text(),
            )
        )
        job = submit_and_wait(
            client, code, "Core Generate attribution", timeout
        )
        baseline._write(directory / "bridge-result.json", job)
        record["probe"] = validate_probe(parse_json_output(job), mode, profile)
        record["status"] = "completed"
    except BaseException as error:
        record.update(status="failed", error=repr(error))
        raise
    finally:
        _finish_sample(record, base, directory, client)
    if record["status"] != "completed":
        raise RuntimeError("Attribution cleanup failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=pathlib.Path, required=True)
    parser.add_argument("--run-dir", type=pathlib.Path)
    parser.add_argument(
        "--profile", choices=(PROFILE, lines.PROFILE), default=PROFILE
    )
    parser.add_argument("--timeout", type=float, default=1200)
    parser.add_argument(
        "--sample", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--mode", choices=("control", "observed"), help=argparse.SUPPRESS
    )
    parser.add_argument("--block", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    base = args.base.resolve()
    if not base.is_file() or baseline._hash(base) != baseline.FIXTURE_SHA256:
        parser.error("Expected the unchanged fixed plain-line fixture")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    _sentinel, run_root = profile_settings(args.profile)
    directory = (args.run_dir or run_root / stamp).resolve()
    if not directory.is_relative_to(run_root.resolve()):
        parser.error("Output must stay under the attribution run root")
    if args.sample:
        _sample(
            base, directory, args.timeout, args.mode, args.block, args.profile
        )
        return
    directory.mkdir(parents=True, exist_ok=False)
    record = {
        "profile_id": args.profile,
        "status": "started",
        "order": ORDER,
        "source_head": baseline._git("rev-parse", "HEAD"),
        "source_status": baseline._git("status", "--short"),
        "samples": [],
        "automatic_replacement": False,
        "environment": {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
    }
    baseline._write(directory / "series.json", record)
    try:
        deployment = subprocess.check_output(
            [
                "flatpak",
                "info",
                "--show-commit",
                "org.freecad.FreeCAD",
            ],
            text=True,
        ).strip()
        record["environment"].update(
            flatpak_deployment=deployment,
            cpu_info=pathlib.Path("/proc/cpuinfo").read_text(),
            mem_info=pathlib.Path("/proc/meminfo").read_text(),
        )
        for block, order in enumerate(ORDER, 1):
            for mode in order:
                sample_dir = directory / "block-{}-{}".format(block, mode)
                sample_dir.mkdir()
                command = [
                    str(baseline.BRIDGE / "run-isolated"),
                    "/usr/bin/env",
                    "TRACKTEMPLATE_ATTRIBUTION_CHILD=1",
                    "/usr/bin/python3",
                    str(pathlib.Path(__file__).resolve()),
                    "--sample",
                    "--profile",
                    args.profile,
                    "--base",
                    str(base),
                    "--run-dir",
                    str(sample_dir),
                    "--mode",
                    mode,
                    "--block",
                    str(block),
                    "--timeout",
                    str(args.timeout),
                ]
                environment = dict(os.environ)
                environment.update(
                    {
                        "TRACKTEMPLATE_BRIDGE_PORT": "19875",
                        "TRACKTEMPLATE_BRIDGE_INSTANCE_FILE": str(
                            sample_dir / "instance-id"
                        ),
                        "TRACKTEMPLATE_BRIDGE_LAUNCHER_LOG": str(
                            sample_dir / "launcher.log"
                        ),
                    }
                )
                try:
                    with (sample_dir / "process.log").open("w") as output:
                        subprocess.run(
                            command,
                            cwd=ROOT,
                            env=environment,
                            stdout=output,
                            stderr=subprocess.STDOUT,
                            check=True,
                        )
                finally:
                    receipt = sample_dir / "sample.json"
                    record["samples"].append(
                        json.loads(receipt.read_text())
                        if receipt.is_file()
                        else {
                            "block": block,
                            "mode": mode,
                            "status": "missing-receipt",
                        }
                    )
                    baseline._write(directory / "series.json", record)
        record["summary"] = summarize(record["samples"], args.profile)
        if (
            subprocess.check_output(
                [
                    "flatpak",
                    "info",
                    "--show-commit",
                    "org.freecad.FreeCAD",
                ],
                text=True,
            ).strip()
            != deployment
        ):
            raise RuntimeError("FreeCAD deployment changed")
        record.update(status="completed", deployment_preserved=True)
    except BaseException as error:
        record.update(status="failed", error=repr(error))
        raise
    finally:
        baseline._write(directory / "series.json", record)
    print("Core Generate attribution passed: {}".format(directory))


if __name__ == "__main__":
    main()
