#!/usr/bin/env python3
"""Run fresh bounded read-only inspections with retained complete output."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG_ROOT = pathlib.Path("benchmark-output") / "inspection-bundles"
MANIFEST_NAME = "manifest.json"
PASS_SENTINEL = "TRACKTEMPLATE_INSPECTION_BUNDLE="
FAILURE_SENTINEL = "TRACKTEMPLATE_INSPECTION_FAILURE="
RETRIEVAL_SENTINEL = "TRACKTEMPLATE_INSPECTION_RETRIEVAL="
FAILURE_EXCERPT_BYTES = 4096
MAX_RETRIEVAL_BYTES = 4096
STEP_NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
SED_PRINT_EXPRESSION = re.compile(r"[1-9][0-9]*(?:,[1-9][0-9]*)?p\Z")
ALLOWED_PROGRAMS = frozenset(("cat", "rg", "sed"))


class InspectionError(RuntimeError):
    """Report an invalid or unverifiable inspection operation."""


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _display_path(path, root):
    path = pathlib.Path(path).resolve()
    root = pathlib.Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _inside_root(path, root):
    try:
        pathlib.Path(path).relative_to(pathlib.Path(root))
    except ValueError:
        return False
    return True


def _safe_operand(value, root):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise InspectionError("inspection path is invalid")
    root = pathlib.Path(root).resolve()
    candidate = pathlib.Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = pathlib.Path(os.path.abspath(candidate))
    if not _inside_root(candidate, root):
        raise InspectionError("inspection path escapes the repository")
    relative = candidate.relative_to(root)
    if relative.parts and relative.parts[0] == ".git":
        raise InspectionError("inspection path enters Git administration state")
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise InspectionError("inspection path contains a symbolic link")
    if not candidate.exists():
        raise InspectionError("inspection path does not exist")
    return candidate


def _validate_cat(arguments, root):
    if len(arguments) < 2 or arguments[0] != "--":
        raise InspectionError("cat permits only 'cat -- FILE ...'")
    for value in arguments[1:]:
        path = _safe_operand(value, root)
        if not path.is_file():
            raise InspectionError("cat accepts regular files only")


def _validate_sed(arguments, root):
    if (
        len(arguments) < 4
        or arguments[0] != "-n"
        or not SED_PRINT_EXPRESSION.fullmatch(arguments[1])
        or arguments[2] != "--"
    ):
        raise InspectionError(
            "sed permits only 'sed -n START[,END]p -- FILE ...'"
        )
    for value in arguments[3:]:
        path = _safe_operand(value, root)
        if not path.is_file():
            raise InspectionError("sed accepts regular files only")


def _validate_rg(arguments, root):
    if len(arguments) >= 3 and arguments[:2] == ["--files", "--"]:
        paths = arguments[2:]
    elif (
        len(arguments) >= 4
        and arguments[0] == "-n"
        and arguments[2] == "--"
        and arguments[1]
        and not arguments[1].startswith("-")
    ):
        paths = arguments[3:]
    else:
        raise InspectionError(
            "rg permits only 'rg -n PATTERN -- PATH ...' or "
            "'rg --files -- PATH ...'"
        )
    if not paths:
        raise InspectionError("rg requires at least one repository path")
    for value in paths:
        path = _safe_operand(value, root)
        if not path.is_file() and not path.is_dir():
            raise InspectionError("rg accepts regular files or directories only")


def _resolve_executable(program, root):
    executable = shutil.which(program)
    if executable is None:
        raise InspectionError("inspection program is unavailable")
    path = pathlib.Path(executable).resolve()
    if not path.is_absolute() or _inside_root(path, pathlib.Path(root).resolve()):
        raise InspectionError("inspection program resolution is unsafe")
    if not path.is_file():
        raise InspectionError("inspection program resolution is unsafe")
    if any(os.access(candidate, os.W_OK) for candidate in (path, *path.parents)):
        raise InspectionError("inspection program resolution is unsafe")
    return path


def validate_step(step, root):
    """Return one step after exact positive-form validation."""
    if not isinstance(step, dict) or set(step) != {"command", "name"}:
        raise InspectionError("each step requires only name and command")
    name = step["name"]
    command = step["command"]
    if not isinstance(name, str) or not STEP_NAME.fullmatch(name):
        raise InspectionError("step name must be a lowercase ASCII slug")
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(item, str) and "\x00" not in item for item in command)
    ):
        raise InspectionError("step command must be a non-empty string argv")
    program = command[0]
    if program not in ALLOWED_PROGRAMS:
        raise InspectionError("inspection command form is not allow-listed")
    validators = {
        "cat": _validate_cat,
        "rg": _validate_rg,
        "sed": _validate_sed,
    }
    validators[program](command[1:], root)
    executable = _resolve_executable(program, root)
    return {
        "command": command,
        "executable": str(executable),
        "executable_sha256": _sha256_file(executable),
        "name": name,
    }


def validate_steps(steps, root):
    """Return a stable tuple of unique validated steps."""
    validated = tuple(validate_step(step, root) for step in steps)
    if not validated:
        raise InspectionError("at least one inspection step is required")
    names = [step["name"] for step in validated]
    if len(names) != len(set(names)):
        raise InspectionError("inspection step names must be unique")
    return validated


def _git(root, *arguments):
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            del environment[name]
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    executable = _resolve_executable("git", root)
    return subprocess.run(
        [str(executable), "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        env=environment,
    )


def _inventory_entry(root, relative_path):
    path = pathlib.Path(root) / relative_path
    if path.is_symlink():
        return {
            "kind": "symlink",
            "path": relative_path.as_posix(),
            "target": os.readlink(path),
        }
    if not path.is_file():
        raise InspectionError("source inventory contains a non-file")
    return {
        "kind": "file",
        "path": relative_path.as_posix(),
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def source_state(root):
    """Record exact tracked and unignored worktree content identity."""
    root = pathlib.Path(root).resolve()
    if root == pathlib.Path(root.anchor) or root == pathlib.Path.home().resolve():
        raise InspectionError("inspection root is unsafe")
    top = _git(root, "rev-parse", "--show-toplevel")
    head = _git(root, "rev-parse", "HEAD")
    index = _git(root, "ls-files", "--stage", "-z")
    paths = _git(
        root,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )
    if top.returncode or head.returncode or index.returncode or paths.returncode:
        raise InspectionError("Git source-state inspection failed")
    if pathlib.Path(os.fsdecode(top.stdout).strip()).resolve() != root:
        raise InspectionError("inspection root is not the Git top level")
    relative_paths = tuple(
        pathlib.PurePosixPath(os.fsdecode(value))
        for value in paths.stdout.split(b"\0")
        if value
    )
    entries = tuple(
        _inventory_entry(root, pathlib.Path(value))
        for value in sorted(relative_paths, key=lambda item: item.as_posix())
    )
    state = {
        "entries": entries,
        "head": os.fsdecode(head.stdout).strip(),
        "index_sha256": _sha256_bytes(index.stdout),
    }
    return {
        "identity": _sha256_bytes(_canonical_bytes(state)),
        "state": state,
    }


def default_run_directory(root=ROOT, now=None):
    """Return a unique ignored directory for one fresh inspection run."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    return pathlib.Path(root) / LOG_ROOT / stamp


def _prepare_run_directory(root, run_directory):
    root = pathlib.Path(root).resolve()
    run_directory = pathlib.Path(run_directory)
    if not run_directory.is_absolute():
        run_directory = root / run_directory
    run_directory = pathlib.Path(os.path.abspath(run_directory))
    if not _inside_root(run_directory, root) or run_directory == root:
        raise InspectionError("run directory is outside the repository")
    current = root
    for part in run_directory.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise InspectionError("run directory contains a symbolic link")
    try:
        run_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise InspectionError("run directory already exists") from None
    return run_directory


def _clean_environment():
    environment = os.environ.copy()
    environment.pop("RIPGREP_CONFIG_PATH", None)
    return environment


def _stream_record(path, root):
    return {
        "bytes": pathlib.Path(path).stat().st_size,
        "path": _display_path(path, root),
        "sha256": _sha256_file(path),
    }


def _excerpt(path, limit):
    size = pathlib.Path(path).stat().st_size
    with pathlib.Path(path).open("rb") as stream:
        if size <= limit:
            return stream.read(), b"", 0
        head_size = limit // 2
        tail_size = limit - head_size
        head = stream.read(head_size)
        stream.seek(-tail_size, 2)
        tail = stream.read(tail_size)
    return head, tail, size - len(head) - len(tail)


def _emit_failure(result, root, stream=None):
    if stream is None:
        stream = sys.stderr
    stream_name = "stderr" if result["stderr"]["bytes"] else "stdout"
    log_path = pathlib.Path(root) / result[stream_name]["path"]
    head, tail, omitted = _excerpt(log_path, FAILURE_EXCERPT_BYTES)
    metadata = {
        "exit_code": result["exit_code"],
        "name": result["name"],
        "omitted_bytes": omitted,
        "stderr": result["stderr"],
        "stdout": result["stdout"],
        "stream": stream_name,
    }
    print(
        FAILURE_SENTINEL
        + json.dumps(metadata, sort_keys=True, separators=(",", ":")),
        file=stream,
    )
    stream.write(head.decode("utf-8", errors="replace"))
    if omitted:
        stream.write(
            "\n... {} bytes omitted; use retained log ...\n".format(omitted)
        )
        stream.write(tail.decode("utf-8", errors="replace"))
    if head or tail:
        stream.write("\n")
    stream.flush()


def run_bundle(*, root, steps, run_directory, failure_stream=None):
    """Execute every inspection freshly and retain both complete streams."""
    root = pathlib.Path(root).resolve()
    validated = validate_steps(steps, root)
    state = source_state(root)
    plan = [
        {
            "command": step["command"],
            "executable": step["executable"],
            "executable_sha256": step["executable_sha256"],
            "name": step["name"],
        }
        for step in validated
    ]
    plan_sha256 = _sha256_bytes(_canonical_bytes(plan))
    run_directory = _prepare_run_directory(root, run_directory)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = []
    for index, step in enumerate(validated, start=1):
        prefix = "{:03d}-{}".format(index, step["name"])
        stdout_path = run_directory / (prefix + ".stdout")
        stderr_path = run_directory / (prefix + ".stderr")
        command = [step["executable"], *step["command"][1:]]
        exit_code = 127
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            try:
                completed = subprocess.run(
                    command,
                    cwd=root,
                    stdout=stdout,
                    stderr=stderr,
                    check=False,
                    env=_clean_environment(),
                )
                exit_code = completed.returncode
            except OSError as error:
                stderr.write(
                    (
                        "TRACKTEMPLATE_INSPECTION_START_ERROR="
                        + repr(error)
                        + "\n"
                    ).encode("utf-8", errors="replace")
                )
        result = {
            "command": step["command"],
            "executable": step["executable"],
            "executable_sha256": step["executable_sha256"],
            "exit_code": exit_code,
            "name": step["name"],
            "status": "passed" if exit_code == 0 else "failed",
            "stderr": _stream_record(stderr_path, root),
            "stdout": _stream_record(stdout_path, root),
        }
        results.append(result)
        if result["status"] == "failed":
            _emit_failure(result, root, stream=failure_stream)
    failed = [result["name"] for result in results if result["status"] == "failed"]
    summary = {
        "failed": failed,
        "failed_count": len(failed),
        "passed_count": len(results) - len(failed),
        "status": "PASS" if not failed else "FAIL",
        "total_count": len(results),
    }
    manifest = {
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "plan": plan,
        "plan_sha256": plan_sha256,
        "results": results,
        "root": str(root),
        "schema": 1,
        "source_state": state,
        "started_at": started,
        "summary": summary,
    }
    manifest_path = run_directory / MANIFEST_NAME
    temporary_path = run_directory / (MANIFEST_NAME + ".tmp")
    temporary_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, manifest_path)
    evidence_key = _sha256_file(manifest_path)
    return {
        **summary,
        "evidence_key": evidence_key,
        "manifest": _display_path(manifest_path, root),
        "plan_sha256": plan_sha256,
        "run_directory": _display_path(run_directory, root),
        "source_state": state["identity"],
    }


def _load_manifest(root, manifest_path, evidence_key):
    path = _safe_operand(manifest_path, root)
    if not path.is_file():
        raise InspectionError("inspection manifest is not a regular file")
    if not re.fullmatch(r"[0-9a-f]{64}", evidence_key or ""):
        raise InspectionError("evidence key must be an exact SHA-256")
    if _sha256_file(path) != evidence_key:
        raise InspectionError("inspection manifest evidence key does not match")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise InspectionError("inspection manifest cannot be read") from None
    if manifest.get("schema") != 1:
        raise InspectionError("inspection manifest schema is unsupported")
    if not isinstance(manifest.get("results"), list) or not all(
        isinstance(result, dict) for result in manifest["results"]
    ):
        raise InspectionError("inspection manifest results are invalid")
    return manifest


def _verified_stream(root, stream_record):
    if not isinstance(stream_record, dict):
        raise InspectionError("retained stream metadata is invalid")
    path = _safe_operand(stream_record.get("path"), root)
    if not path.is_file():
        raise InspectionError("retained inspection stream is unavailable")
    if path.stat().st_size != stream_record.get("bytes"):
        raise InspectionError("retained inspection stream size changed")
    if _sha256_file(path) != stream_record.get("sha256"):
        raise InspectionError("retained inspection stream identity changed")
    return path


def retrieve_output(
    *,
    root,
    manifest_path,
    evidence_key,
    step_name,
    stream_name,
    head_bytes,
    tail_bytes,
    stream=None,
):
    """Write one bounded integrity-checked retained-stream excerpt."""
    if stream is None:
        stream = sys.stdout
    if stream_name not in ("stdout", "stderr"):
        raise InspectionError("retrieval stream must be stdout or stderr")
    if (
        head_bytes < 0
        or tail_bytes < 0
        or head_bytes + tail_bytes == 0
        or head_bytes + tail_bytes > MAX_RETRIEVAL_BYTES
    ):
        raise InspectionError("retrieval byte limit is invalid")
    manifest = _load_manifest(root, manifest_path, evidence_key)
    by_name = {result.get("name"): result for result in manifest.get("results", [])}
    if step_name not in by_name:
        raise InspectionError("inspection step is absent from the manifest")
    record = by_name[step_name].get(stream_name)
    path = _verified_stream(root, record)
    size = path.stat().st_size
    with path.open("rb") as retained:
        head = retained.read(min(head_bytes, size))
        remaining = max(0, size - len(head))
        tail_size = min(tail_bytes, remaining)
        if tail_size:
            retained.seek(-tail_size, 2)
            tail = retained.read(tail_size)
        else:
            tail = b""
    omitted = size - len(head) - len(tail)
    metadata = {
        "evidence_key": evidence_key,
        "name": step_name,
        "omitted_bytes": omitted,
        "stream": stream_name,
        **record,
    }
    print(
        RETRIEVAL_SENTINEL
        + json.dumps(metadata, sort_keys=True, separators=(",", ":")),
        file=stream,
    )
    stream.write(head.decode("utf-8", errors="replace"))
    if omitted:
        stream.write("\n... {} bytes omitted ...\n".format(omitted))
    stream.write(tail.decode("utf-8", errors="replace"))
    if head or tail:
        stream.write("\n")
    return metadata


def parse_step(value):
    """Parse ``name=<JSON argv>`` into one inspection step."""
    name, separator, raw_command = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("step requires name=<JSON argv>")
    try:
        command = json.loads(raw_command)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError("step command is not valid JSON") from error
    return {"command": command, "name": name}


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    run = commands.add_parser("run")
    run.add_argument("--step", action="append", required=True, type=parse_step)
    retrieve = commands.add_parser("retrieve")
    retrieve.add_argument("--manifest", required=True)
    retrieve.add_argument("--evidence-key", required=True)
    retrieve.add_argument("--step", required=True)
    retrieve.add_argument("--stream", choices=("stdout", "stderr"), required=True)
    retrieve.add_argument("--head-bytes", type=int, default=2048)
    retrieve.add_argument("--tail-bytes", type=int, default=2048)
    return parser


def main(argv=None):
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.operation == "run":
            summary = run_bundle(
                root=ROOT,
                steps=arguments.step,
                run_directory=default_run_directory(),
            )
            print(
                PASS_SENTINEL
                + json.dumps(summary, sort_keys=True, separators=(",", ":")),
                flush=True,
            )
            return int(bool(summary["failed_count"]))
        retrieve_output(
            root=ROOT,
            manifest_path=arguments.manifest,
            evidence_key=arguments.evidence_key,
            step_name=arguments.step,
            stream_name=arguments.stream,
            head_bytes=arguments.head_bytes,
            tail_bytes=arguments.tail_bytes,
        )
        return 0
    except InspectionError as error:
        print("TRACKTEMPLATE_INSPECTION_ERROR=" + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
