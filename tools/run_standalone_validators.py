#!/usr/bin/env python3
"""Run every standalone validator under an explicit evidence profile."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SENTINEL = "TRACKTEMPLATE_STANDALONE_VALIDATION="
PROFILES = ("ci", "local")
RECOVERY_VALIDATOR = "validate_recovery_controls.py"
DEFAULT_LOG_ROOT = pathlib.Path("benchmark-output") / "standalone-validation"
FAILURE_EXCERPT_BYTES = 4096
MANIFEST_NAME = "manifest.json"


def discover_validators(root=ROOT):
    """Return the complete deterministic standalone-validator list."""
    return sorted((root / "tests").glob("validate_*.py"))


def validator_command(path, profile, python_executable=sys.executable):
    """Build one validator command for the selected evidence profile."""
    command = [python_executable, str(path)]
    if profile == "local" and path.name == RECOVERY_VALIDATOR:
        command.append("--live-workstation")
    return command


def default_run_directory(root=ROOT, now=None):
    """Return one unique ignored directory for retained validator output."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    run_name = now.strftime("%Y%m%dT%H%M%S%fZ")
    return pathlib.Path(root) / DEFAULT_LOG_ROOT / run_name


def _display_path(path, root):
    path = pathlib.Path(path).resolve()
    root = pathlib.Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _prepare_log_directory(root, log_directory):
    root = pathlib.Path(root).resolve()
    log_directory = pathlib.Path(log_directory)
    if not log_directory.is_absolute():
        log_directory = root / log_directory
    log_directory = log_directory.resolve()
    if log_directory == root:
        raise ValueError(
            "the repository root cannot be a standalone-validation log "
            "directory"
        )
    log_directory.mkdir(parents=True, exist_ok=False)
    return log_directory


def _sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _failure_excerpt(path, limit=FAILURE_EXCERPT_BYTES):
    """Return bounded head and tail bytes from one complete retained log."""
    path = pathlib.Path(path)
    size = path.stat().st_size
    with path.open("rb") as stream:
        if size <= limit:
            return stream.read(), b"", 0
        head_size = limit // 2
        tail_size = limit - head_size
        head = stream.read(head_size)
        stream.seek(-tail_size, 2)
        tail = stream.read(tail_size)
    return head, tail, size - len(head) - len(tail)


def _emit_failure(result, log_path, stream=None):
    if stream is None:
        stream = sys.stderr
    head, tail, omitted_bytes = _failure_excerpt(log_path)
    metadata = {
        "excerpt_bytes": len(head) + len(tail),
        "exit_code": result["exit_code"],
        "log": result["log"],
        "omitted_bytes": omitted_bytes,
        "output_bytes": result["output_bytes"],
        "output_sha256": result["output_sha256"],
        "path": result["path"],
        "truncated": bool(omitted_bytes),
    }
    print(
        "TRACKTEMPLATE_VALIDATOR_FAILURE="
        + json.dumps(metadata, sort_keys=True, separators=(",", ":")),
        file=stream,
    )
    print(
        "TRACKTEMPLATE_VALIDATOR_FAILURE_OUTPUT_BEGIN="
        + json.dumps({"path": result["path"]}, separators=(",", ":")),
        file=stream,
    )
    stream.write(head.decode("utf-8", errors="replace"))
    if omitted_bytes:
        stream.write(
            "\n... {} bytes omitted; use the retained log ...\n".format(
                omitted_bytes
            )
        )
        stream.write(tail.decode("utf-8", errors="replace"))
    if head or tail:
        stream.write("\n")
    print(
        "TRACKTEMPLATE_VALIDATOR_FAILURE_OUTPUT_END="
        + json.dumps({"path": result["path"]}, separators=(",", ":")),
        file=stream,
        flush=True,
    )


def run_validators(
    *,
    root,
    validators,
    profile,
    log_directory,
    python_executable=sys.executable,
    failure_stream=None,
):
    """Run all validators and retain their complete combined command output."""
    root = pathlib.Path(root).resolve()
    log_directory = _prepare_log_directory(root, log_directory)
    results = []
    for index, path in enumerate(validators, start=1):
        relative_path = path.relative_to(root).as_posix()
        command = validator_command(path, profile, python_executable)
        log_path = log_directory / "{:03d}-{}.log".format(
            index,
            path.name,
        )
        with log_path.open("wb") as log:
            completed = subprocess.run(
                command,
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        result = {
            "command": command,
            "exit_code": completed.returncode,
            "log": _display_path(log_path, root),
            "output_bytes": log_path.stat().st_size,
            "output_sha256": _sha256_file(log_path),
            "path": relative_path,
            "status": "passed" if completed.returncode == 0 else "failed",
        }
        results.append(result)
        if completed.returncode:
            _emit_failure(result, log_path, stream=failure_stream)
    return results


def build_summary(profile, results):
    """Return the stable machine-readable result summary."""
    failed = [result["path"] for result in results if result["exit_code"]]
    return {
        "failed": failed,
        "failed_count": len(failed),
        "passed_count": len(results) - len(failed),
        "profile": profile,
        "total_count": len(results),
    }


def write_manifest(*, root, log_directory, profile, results, summary):
    """Write the complete validator result index beside the retained logs."""
    manifest_path = pathlib.Path(log_directory) / MANIFEST_NAME
    manifest = {
        "profile": profile,
        "results": results,
        "schema": 1,
        "summary": summary,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return _display_path(manifest_path, root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        required=True,
        help=(
            "'ci' runs clean-checkout contracts; 'local' additionally requires "
            "the workstation-only recovery evidence"
        ),
    )
    arguments = parser.parse_args(argv)

    validators = discover_validators()
    if not validators:
        parser.error("no tests/validate_*.py validators were found")

    log_directory = default_run_directory()
    results = run_validators(
        root=ROOT,
        validators=validators,
        profile=arguments.profile,
        log_directory=log_directory,
    )
    summary = build_summary(arguments.profile, results)
    manifest = write_manifest(
        root=ROOT,
        log_directory=log_directory,
        profile=arguments.profile,
        results=results,
        summary=summary,
    )
    summary = {
        **summary,
        "log_directory": _display_path(log_directory, ROOT),
        "manifest": manifest,
    }
    print(
        SENTINEL + json.dumps(summary, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return int(bool(summary["failed_count"]))


if __name__ == "__main__":
    raise SystemExit(main())
