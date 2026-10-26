#!/usr/bin/env python3
"""Observe the unchanged atomic validator without replacing its assertions.

Default mode preserves tempfile's environment selection. --temp-root starts
a new process with only TMPDIR changed for a labelled comparison. Neither
mode modifies retained repository files or product/test functions.
"""

import argparse
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import stat
import subprocess
import sys
import traceback


VALIDATOR = "tests/validate_core_export_atomic.py"
APPLICATION = "tracktemplate/application/core_export_set.py"
SOURCE_PATHS = (
    VALIDATOR,
    "tests/validate_core_export_staging.py",
    "tests/validate_core_export_atomic_files.py",
    "tracktemplate/api.py",
    APPLICATION,
    "tracktemplate/adapters/export/core_layout_set.py",
    "tracktemplate/compatibility/core_export_policy.py",
    "tracktemplate/compatibility/transition_workflow.py",
    "tools/run_standalone_validators.py",
    ".github/workflows/ci.yml",
)
RESULT_KEYS = (
    "publication_state", "failure_details", "failures", "successful_files",
    "failed_files", "output_directory", "manifest_path",
    "manifest_requested", "formats",
)
SENTINEL = "Core atomic export application validation passed"


def exception_record(error):
    """Return error identity and frames, without arbitrary local values."""
    return {
        "type": type(error).__module__ + "." + type(error).__qualname__,
        "message": str(error),
        "errno": getattr(error, "errno", None),
        "notes": list(getattr(error, "__notes__", ())),
        "traceback": [
            {"filename": item.filename, "lineno": item.lineno,
             "name": item.name}
            for item in traceback.extract_tb(error.__traceback__)
        ],
    }


def source_state(repository):
    """Identify Git state and bytes relevant to this diagnostic."""
    def git(*arguments):
        return subprocess.check_output(
            ["git", "-C", str(repository), *arguments], text=True,
        ).strip()

    return {
        "head": git("rev-parse", "HEAD"),
        "tracked_status": git("status", "--porcelain", "--untracked-files=no"),
        "source_sha256": {
            name: hashlib.sha256((repository / name).read_bytes()).hexdigest()
            for name in SOURCE_PATHS
        },
    }


def mount_record(path):
    """Read the actual directory descriptor's matching mountinfo entry."""
    result = {"path": str(path)}
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        info = os.fstat(descriptor)
        result.update(st_dev=info.st_dev, st_ino=info.st_ino)
        fdinfo = Path(f"/proc/self/fdinfo/{descriptor}").read_text()
        mount_id = next(
            int(line.partition(":")[2].strip())
            for line in fdinfo.splitlines() if line.startswith("mnt_id:")
        )
        result["mnt_id"] = mount_id
        lines = Path("/proc/self/mountinfo").read_text().splitlines()
        matching = next(
            line for line in lines if int(line.split()[0]) == mount_id
        )
        result["mountinfo"] = matching
        result["filesystem_type"] = matching.partition(" - ")[2].split()[0]
    except Exception as error:
        result["observation_error"] = exception_record(error)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return result


def selected_result(result):
    """Keep only explicit scalar fields and diagnostic string lists."""
    return {key: result.get(key) for key in RESULT_KEYS}


def entry_type(mode):
    """Classify an lstat mode without following a symbolic link."""
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "other"


def directory_record(path):
    """Observe one path and direct entries through a no-follow descriptor."""
    record = {"path": str(path), "exists": None, "entries": []}
    descriptor = None
    try:
        try:
            info = os.stat(path, follow_symlinks=False)
        except FileNotFoundError:
            record["exists"] = False
            return record
        record.update(
            exists=True, type=entry_type(info.st_mode), size=info.st_size,
            st_dev=info.st_dev, st_ino=info.st_ino,
        )
        if not stat.S_ISDIR(info.st_mode):
            return record
        descriptor = os.open(
            path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        opened = os.fstat(descriptor)
        record["identity_unchanged_at_open"] = (
            (info.st_dev, info.st_ino) == (opened.st_dev, opened.st_ino)
        )
        if not record["identity_unchanged_at_open"]:
            return record
        with os.scandir(descriptor) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                child = {"name": entry.name}
                try:
                    details = entry.stat(follow_symlinks=False)
                    child.update(
                        type=entry_type(details.st_mode), size=details.st_size,
                    )
                except OSError as error:
                    child["observation_error"] = exception_record(error)
                record["entries"].append(child)
    except OSError as error:
        record["observation_error"] = exception_record(error)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return record


def output_record(plan):
    """Corroborate the result before the validator's temporary cleanup."""
    intended = Path(plan["output_directory"])
    parent = directory_record(intended.parent)
    return {
        "intended_directory": directory_record(intended),
        "parent_directory": parent,
        "staging_names": [
            item["name"] for item in parent["entries"]
            if item["name"].startswith(".tracktemplate")
        ],
        "observation_boundary": (
            "Application return after product cleanup, before test cleanup"
        ),
        "recursive": False,
        "symlinks_followed": False,
    }


def diagnostic(repository, output, selected_temp_root):
    """Run full validator order with a trace limited to two normal cases."""
    import tempfile

    validator = str(repository / VALIDATOR)
    application = str(repository / APPLICATION)
    before = source_state(repository)
    record = {
        "schema_version": 1,
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "kind": "diagnostic execution; not an uninstrumented CI pass",
        "repository": str(repository),
        "validator": validator,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "selected_temp_root": selected_temp_root,
        "tempfile_gettempdir": tempfile.gettempdir(),
        "temporary_environment": {
            name: os.environ.get(name) for name in ("TMPDIR", "TEMP", "TMP")
        },
        "before": before,
        "normal_cases": [],
        "trace_errors": [],
    }
    case = None

    def normal_ancestor(frame):
        while frame is not None:
            if (frame.f_code.co_filename == validator
                    and frame.f_code.co_name == "validate_application"):
                return frame if frame.f_locals.get("cases", 2) < 2 else None
            frame = frame.f_back
        return None

    def observe(frame, event, argument):
        nonlocal case
        filename = frame.f_code.co_filename
        name = frame.f_code.co_name
        if filename == validator and name == "run_case" and event == "call":
            ancestor = normal_ancestor(frame.f_back)
            if ancestor is not None:
                case = {
                    "case_index": ancestor.f_locals["cases"],
                    "manifest": frame.f_locals["manifest"],
                    "root": str(frame.f_locals["root"]),
                    "mount": mount_record(frame.f_locals["root"]),
                    "application_exceptions": [],
                }
                record["normal_cases"].append(case)
            return None
        if (filename == application and name == "run_atomic_core_layout_export"
                and normal_ancestor(frame.f_back) is not None):
            if event == "exception":
                item = exception_record(argument[1])
                item.update(phase=frame.f_locals.get("phase"),
                            observed_line=frame.f_lineno)
                case["application_exceptions"].append(item)
            elif event == "return" and isinstance(argument, dict):
                case["result"] = selected_result(argument)
                case["filesystem_at_return"] = output_record(
                    frame.f_locals["plan"],
                )
                case["phase_at_return"] = frame.f_locals.get("phase")
                case["operation_error"] = frame.f_locals.get("operation_error")
                case["cleanup_errors"] = frame.f_locals.get("cleanup_errors")
            return trace
        if filename == validator and name == "validate_application":
            if event == "exception" and frame.f_locals.get("cases", 2) < 2:
                record["normal_case_exception"] = {
                    "case_index": frame.f_locals.get("cases"),
                    "manifest": frame.f_locals.get("manifest"),
                    "root": str(frame.f_locals.get("root")),
                    "error": exception_record(argument[1]),
                    "result": selected_result(frame.f_locals.get("result", {})),
                }
            return trace
        return None

    def trace(frame, event, argument):
        try:
            return observe(frame, event, argument)
        except Exception as error:
            record["trace_errors"].append(exception_record(error))
            return None

    exit_code = 0
    original_trace = sys.gettrace()
    old_argv = sys.argv
    old_path = list(sys.path)
    old_cwd = Path.cwd()
    stdout_path = output / "validator.stdout.log"
    stderr_path = output / "validator.stderr.log"
    try:
        os.chdir(repository)
        sys.argv = [validator]
        sys.path.insert(0, str(repository / "tests"))
        with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    sys.settrace(trace)
                    runpy.run_path(validator, run_name="__main__")
                except BaseException as error:
                    sys.settrace(original_trace)
                    record["validator_exception"] = exception_record(error)
                    exit_code = (
                        error.code if isinstance(error, SystemExit)
                        and isinstance(error.code, int) else 1
                    )
                    traceback.print_exception(error)
                finally:
                    sys.settrace(original_trace)
    finally:
        sys.settrace(original_trace)
        sys.argv = old_argv
        sys.path[:] = old_path
        os.chdir(old_cwd)
        record["validator_exit_code"] = exit_code
        record["after"] = source_state(repository)
        record["source_and_tracked_state_unchanged"] = before == record["after"]
        record["sentinel_observed"] = (
            stdout_path.exists() and SENTINEL in stdout_path.read_text()
        )
        record["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        record["log_sha256"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (stdout_path, stderr_path) if path.exists()
        }
        with (output / "diagnostic.json").open("x") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    if not record["source_and_tracked_state_unchanged"] or record["trace_errors"]:
        return exit_code or 2
    return exit_code


def main():
    """Accept an exact checkout and a new, non-overwriting output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--selected-temp-root", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.repository.is_absolute() or not args.output.is_absolute():
        parser.error("--repository and --output must be absolute paths")
    repository = args.repository.resolve(strict=True)
    output = args.output.resolve()
    if not (repository / VALIDATOR).is_file():
        parser.error("repository does not contain the expected validator")
    if args.worker:
        return diagnostic(repository, output, args.selected_temp_root)
    output.mkdir(parents=True, exist_ok=False)
    command = [
        sys.executable, str(Path(__file__).resolve()), "--worker",
        "--repository", str(repository), "--output", str(output),
    ]
    environment = os.environ.copy()
    if args.temp_root is not None:
        temporary_root = args.temp_root.resolve(strict=True)
        if not temporary_root.is_dir():
            parser.error("--temp-root must identify an existing directory")
        environment["TMPDIR"] = str(temporary_root)
        command.extend(["--selected-temp-root", str(temporary_root)])
    completed = subprocess.run(command, env=environment, check=False)
    print(json.dumps({"output": str(output), "exit_code": completed.returncode}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
