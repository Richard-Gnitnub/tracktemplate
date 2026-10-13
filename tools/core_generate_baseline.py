#!/usr/bin/env python3
"""Measure one bounded Core Generate action in three isolated GUI sessions.

This is diagnostic tooling, not a performance budget or Phase 6 profile.
Each session performs a first Generate and two same-process regenerations.
The measured action includes automated dialogs. Launch, fixture loading,
correctness checks, capture and document disposal stay outside that action.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import pathlib
import platform
import shutil
import statistics
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools/freecad_bridge"
PROFILE = "phase9b-core-generate-diagnostic-v1"
LABELS = (
    "first-generate",
    "same-process-regeneration-1",
    "same-process-regeneration-2",
)
CHECKS = {
    "repeated_contract_equal", "previous_outputs_preserved",
    "actual_export_geometry_verified", "document_registry_preserved",
    "routing_preserved", "dependency_classification_verified",
    "preferences_restored", "pending_configuration_restored",
}
FIXTURE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)
PROBE = BRIDGE / "probes/core_generate_baseline.py"
LOADER = BRIDGE / "probes/load_phase3_transition_workflow.py"
RUN_ROOT = ROOT / "benchmark-output/core-generate-baseline"
sys.path.insert(0, str(ROOT))


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *arguments], text=True,
    ).strip()


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sources():
    """Bind executable source, contracts and this uncommitted diagnostic."""
    names = _git("ls-files").splitlines()
    paths = {
        name for name in names
        if name.endswith((".py", ".FCMacro", ".json"))
        or name.startswith("tools/freecad_bridge/")
    }
    paths.update((str(PROBE.relative_to(ROOT)),
                  str(pathlib.Path(__file__).relative_to(ROOT)),
                  "tests/validate_core_generate_baseline.py"))
    return {name: _hash(ROOT / name) for name in sorted(paths)}


def validate_probe(report):
    """Reject incomplete actions and invalid observations without budgets."""
    if (report.get("schema_version") != 1
            or report.get("profile_id") != PROFILE
            or report.get("status") != "completed"
            or report.get("sentinel") != "CORE_GENERATE_BASELINE_PASS"
            or not isinstance(report.get("host_profile_id"), str)
            or not report["host_profile_id"]):
        raise ValueError("Incomplete diagnostic identity or status")
    checks = report.get("checks")
    if not isinstance(checks, dict) or set(checks) != CHECKS or any(
        value is not True for value in checks.values()
    ):
        raise ValueError("Diagnostic correctness checks did not pass")
    actions = report.get("actions", [])
    if [item.get("label") for item in actions] != list(LABELS):
        raise ValueError("Diagnostic action sequence differs")
    contracts = []
    directories = []
    for action in actions:
        if (action.get("status") != "completed"
                or action.get("previous_outputs_preserved") is not True):
            raise ValueError("Action did not complete its preservation proof")
        for name in ("wall_ms", "process_cpu_ms", "rss_before_mb",
                     "rss_after_mb"):
            value = action.get(name)
            if (type(value) not in (int, float)
                    or not math.isfinite(value) or value < 0):
                raise ValueError("Invalid diagnostic metric: " + name)
        for name in ("objects_before", "objects_after"):
            if type(action.get(name)) is not int or action[name] < 0:
                raise ValueError("Invalid document object count")
        if action.get("payload_count") != 13:
            raise ValueError("Incomplete diagnostic output")
        digest = action.get("output_contract_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("Invalid output contract digest")
        directory = action.get("output_dir")
        if not isinstance(directory, str) or not directory:
            raise ValueError("Missing publication directory")
        contracts.append(digest)
        directories.append(directory)
    if len(set(contracts)) != 1 or len(set(directories)) != 3:
        raise ValueError("Outputs differ or publication directory repeated")
    return report


def summarize(samples):
    """Keep action classes separate and retain all individual values."""
    if len(samples) != 3:
        raise ValueError("Exactly three fresh GUI samples are required")
    probes = []
    for sample in samples:
        if (sample.get("status") != "completed"
                or sample.get("cleanup") != {"remaining": []}
                or sample.get("source_before") != sample.get("source_after")
                or not sample.get("source_before")
                or sample.get("fixture_before") != FIXTURE_SHA256
                or sample.get("fixture_after") != FIXTURE_SHA256):
            raise ValueError("Sample preservation or cleanup is incomplete")
        probes.append(validate_probe(sample["probe"]))
    if len({item["host_profile_id"] for item in probes}) != 1:
        raise ValueError("Host profiles cannot be mixed")
    if any(item["source_before"] != samples[0]["source_before"]
           for item in samples):
        raise ValueError("Sample source states differ")
    if len({item["probe"]["actions"][0]["output_contract_sha256"]
            for item in samples}) != 1:
        raise ValueError("Sample output contracts differ")
    directories = [action["output_dir"] for probe in probes
                   for action in probe["actions"]]
    if len(set(directories)) != 9:
        raise ValueError("Publication directories repeat across samples")
    result = {}
    for index, label in enumerate(LABELS):
        metrics = {}
        for key in ("wall_ms", "process_cpu_ms", "rss_before_mb",
                    "rss_after_mb", "objects_before", "objects_after"):
            values = [item["actions"][index][key] for item in probes]
            metrics[key] = {
                "values": values, "median": statistics.median(values),
                "minimum": min(values), "maximum": max(values),
            }
        result[label] = metrics
    return result


def _close_documents(client):
    """Close copied documents in a self-contained, fresh RPC namespace."""
    from tools.freecad_bridge.orchestration import execute, parse_json_output

    result = parse_json_output(execute(client, "\n".join((
        "import json",
        "import FreeCAD as App",
        "for name in list(App.listDocuments()):",
        "    App.closeDocument(name)",
        "print(json.dumps({'remaining': sorted(App.listDocuments())}))",
    ))))
    if result != {"remaining": []}:
        raise RuntimeError("Diagnostic document cleanup did not complete")
    return result


def _finish_sample(record, base, directory, client):
    """Preserve final evidence even when the RPC client raises SystemExit."""
    try:
        try:
            record["cleanup"] = _close_documents(client)
        except BaseException as error:
            record["cleanup_error"] = "{}: {}".format(
                type(error).__name__, error,
            )
            record["status"] = "failed"
        try:
            record["source_after"] = _sources()
            record["fixture_after"] = _hash(base)
        except BaseException as error:
            record["preservation_error"] = "{}: {}".format(
                type(error).__name__, error,
            )
            record["status"] = "failed"
    finally:
        _write(directory / "sample.json", record)


def _sample(base, directory, timeout):
    """Child of run-isolated only; never attach to an operator session."""
    instance_file = os.environ.get("TRACKTEMPLATE_BRIDGE_INSTANCE_FILE")
    if (os.environ.get("TRACKTEMPLATE_BASELINE_CHILD") != "1"
            or not instance_file
            or not pathlib.Path(instance_file).read_text().strip().isdigit()):
        raise RuntimeError("Diagnostic child needs its isolated instance")
    sys.path.insert(0, str(ROOT / ".devtools/freecad-cli/src"))
    from freecad_cli.client import FreeCADClient
    from tools.freecad_bridge.orchestration import (
        execute, parse_json_output, submit_and_wait,
    )

    token = ROOT / "benchmark-output/freecad-bridge/rpc-token"
    client = FreeCADClient(
        host="127.0.0.1", port=19875, timeout=30,
        token=token.read_text().strip(),
    )
    record = {
        "status": "started", "source_before": _sources(),
        "fixture_before": _hash(base),
        "isolated_instance_id": pathlib.Path(instance_file).read_text().strip(),
    }
    _write(directory / "sample.json", record)
    copied = directory / "input.FCStd"
    shutil.copy2(base, copied)
    try:
        execute(client, "\n".join((
            "import FreeCAD as App",
            "if App.listDocuments():",
            "    raise RuntimeError('Expected an empty isolated session')",
            "App.openDocument({!r})".format(str(copied)),
        )))
        code = "\n".join((
            "TRACKTEMPLATE_PHASE3_ROUTE = 'modular'",
            "TRACKTEMPLATE_BASELINE_DIRECTORY = {!r}".format(str(directory)),
            LOADER.read_text(), PROBE.read_text(),
        ))
        job = submit_and_wait(client, code, "Core Generate diagnostic", timeout)
        _write(directory / "bridge-result.json", job)
        record["probe"] = validate_probe(parse_json_output(job))
        record["status"] = "completed"
    except BaseException as error:
        record["status"] = "failed"
        record["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        _finish_sample(record, base, directory, client)
    if record["status"] != "completed":
        raise RuntimeError("Diagnostic cleanup failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=pathlib.Path, required=True)
    parser.add_argument("--run-dir", type=pathlib.Path)
    parser.add_argument("--sample", action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=1200)
    args = parser.parse_args()
    base = args.base.resolve()
    if not base.is_file() or _hash(base) != FIXTURE_SHA256:
        parser.error("Expected the unchanged fixed plain-line fixture")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    directory = (args.run_dir or RUN_ROOT / stamp).resolve()
    if not directory.is_relative_to(RUN_ROOT.resolve()):
        parser.error("Diagnostic output must stay under its run root")
    if args.sample:
        _sample(base, directory, args.timeout)
        return
    directory.mkdir(parents=True, exist_ok=False)
    record = {
        "profile_id": PROFILE, "status": "started", "source_head":
        _git("rev-parse", "HEAD"), "source_status": _git("status", "--short"),
        "samples": [], "automatic_replacement": False,
        "environment": {
            "platform": platform.platform(), "cpu_count": os.cpu_count(),
            "cpu_info": pathlib.Path("/proc/cpuinfo").read_text(),
            "mem_info": pathlib.Path("/proc/meminfo").read_text(),
            "flatpak_deployment": subprocess.check_output([
                "flatpak", "info", "--show-commit", "org.freecad.FreeCAD",
            ], text=True).strip(),
        },
    }
    try:
        for index in range(3):
            sample_dir = directory / "sample-{}".format(index + 1)
            sample_dir.mkdir()
            command = [
                str(BRIDGE / "run-isolated"), "/usr/bin/env",
                "TRACKTEMPLATE_BASELINE_CHILD=1", "/usr/bin/python3",
                str(pathlib.Path(__file__).resolve()), "--sample",
                "--base", str(base), "--run-dir", str(sample_dir),
                "--timeout", str(args.timeout),
            ]
            environment = dict(os.environ)
            environment.update({
                "TRACKTEMPLATE_BRIDGE_PORT": "19875",
                "TRACKTEMPLATE_BRIDGE_INSTANCE_FILE":
                str(sample_dir / "instance-id"),
                "TRACKTEMPLATE_BRIDGE_LAUNCHER_LOG":
                str(sample_dir / "launcher.log"),
            })
            with (sample_dir / "process.log").open("w") as output:
                subprocess.run(command, cwd=ROOT, env=environment,
                               stdout=output, stderr=subprocess.STDOUT,
                               check=True)
            record["samples"].append(json.loads(
                (sample_dir / "sample.json").read_text()
            ))
        record["summary"] = summarize(record["samples"])
        deployment_after = subprocess.check_output([
            "flatpak", "info", "--show-commit", "org.freecad.FreeCAD",
        ], text=True).strip()
        if deployment_after != record["environment"]["flatpak_deployment"]:
            raise RuntimeError("FreeCAD deployment changed during measurement")
        record["deployment_preserved"] = True
        record["status"] = "completed"
    except BaseException as error:
        record["status"] = "failed"
        record["error"] = "{}: {}".format(type(error).__name__, error)
        raise
    finally:
        _write(directory / "series.json", record)
    print("Core Generate diagnostic passed: {}".format(directory))


if __name__ == "__main__":
    main()
