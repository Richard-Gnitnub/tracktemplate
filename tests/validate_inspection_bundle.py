#!/usr/bin/env python3
"""Validate fresh retained read-only inspection-bundle behaviour."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import run_inspection_bundle as bundle  # noqa: E402


def _git(root, *arguments):
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _fixture():
    temporary = tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-bundle-"
    )
    root = pathlib.Path(temporary.name)
    (root / ".gitignore").write_text(
        "/benchmark-output/\n",
        encoding="utf-8",
    )
    (root / "large.txt").write_text(
        "start\n" + ("x" * 12000) + "\nend\n",
        encoding="utf-8",
    )
    (root / "small.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    _git(root, "init")
    _git(root, "add", ".gitignore", "large.txt", "small.txt")
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=TrackTemplate Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return temporary, root


def _steps():
    return (
        {"name": "large-read", "command": ["cat", "--", "large.txt"]},
        {
            "name": "line-read",
            "command": ["sed", "-n", "1,2p", "--", "small.txt"],
        },
        {
            "name": "search",
            "command": ["rg", "-n", "alpha", "--", "small.txt"],
        },
        {
            "name": "inventory",
            "command": ["rg", "--files", "--", "."],
        },
    )


def _manifest(root, summary):
    path = root / summary["manifest"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == summary["evidence_key"]
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_quiet_success_and_retention(root):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        summary = bundle.run_bundle(
            root=root,
            steps=_steps(),
            run_directory=root / "benchmark-output" / "inspection-bundles" / "pass",
        )
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    assert summary["status"] == "PASS"
    assert summary["failed_count"] == 0
    assert summary["passed_count"] == 4
    assert "reuse" not in json.dumps(summary)
    manifest = _manifest(root, summary)
    assert manifest["summary"] == {
        "failed": [],
        "failed_count": 0,
        "passed_count": 4,
        "status": "PASS",
        "total_count": 4,
    }
    assert manifest["source_state"]["identity"] == summary["source_state"]
    assert manifest["source_state"]["state"]["head"] == subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    by_name = {result["name"]: result for result in manifest["results"]}
    for result in by_name.values():
        assert pathlib.Path(result["executable"]).is_absolute()
        assert len(result["executable_sha256"]) == 64
        for stream_name in ("stdout", "stderr"):
            record = result[stream_name]
            retained = root / record["path"]
            assert retained.stat().st_size == record["bytes"]
            assert hashlib.sha256(retained.read_bytes()).hexdigest() == record[
                "sha256"
            ]
    assert by_name["large-read"]["stdout"]["bytes"] > 12000
    assert by_name["large-read"]["stderr"]["bytes"] == 0
    assert (root / by_name["line-read"]["stdout"]["path"]).read_text(
        encoding="utf-8"
    ) == "alpha\nbeta\n"
    return summary


def _validate_every_run_is_fresh(root, first_summary):
    (root / "small.txt").write_text("alpha changed\n", encoding="utf-8")
    second = bundle.run_bundle(
        root=root,
        steps=_steps(),
        run_directory=root / "benchmark-output" / "inspection-bundles" / "fresh",
    )
    assert second["status"] == "PASS"
    assert second["run_directory"] != first_summary["run_directory"]
    assert second["evidence_key"] != first_summary["evidence_key"]
    assert second["source_state"] != first_summary["source_state"]
    manifest = _manifest(root, second)
    search = next(result for result in manifest["results"] if result["name"] == "search")
    assert (root / search["stdout"]["path"]).read_text(
        encoding="utf-8"
    ) == "1:alpha changed\n"
    (root / "small.txt").write_text("alpha\nbeta\n", encoding="utf-8")


def _validate_failure_is_bounded_and_complete(root):
    steps = (
        {
            "name": "noisy-failure",
            "command": ["rg", "-n", "absent", "--", "large.txt"],
        },
        {"name": "later-step", "command": ["cat", "--", "small.txt"]},
    )
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-programs-"
    ) as programs:
        fake_rg = pathlib.Path(programs) / "rg"
        fake_rg.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "sys.stdout.write('stdout-start\\n' + ('x' * 12000) + "
            "'\\nstdout-end\\n')\n"
            "sys.stderr.write('stderr-start\\n' + ('y' * 12000) + "
            "'\\nstderr-end\\n')\n"
            "raise SystemExit(3)\n",
            encoding="utf-8",
        )
        fake_rg.chmod(0o755)
        original_resolver = bundle._resolve_executable
        bundle._resolve_executable = lambda program, _root: (
            fake_rg if program == "rg" else original_resolver(program, _root)
        )
        failure = io.StringIO()
        try:
            summary = bundle.run_bundle(
                root=root,
                steps=steps,
                run_directory=(
                    root
                    / "benchmark-output"
                    / "inspection-bundles"
                    / "failure"
                ),
                failure_stream=failure,
            )
        finally:
            bundle._resolve_executable = original_resolver
    assert summary["status"] == "FAIL"
    assert summary["failed"] == ["noisy-failure"]
    assert summary["passed_count"] == 1
    assert len(failure.getvalue().encode("utf-8")) < (
        bundle.FAILURE_EXCERPT_BYTES + 2048
    )
    assert "stderr-start" in failure.getvalue()
    assert "stderr-end" in failure.getvalue()
    assert "stdout-start" not in failure.getvalue()
    manifest = _manifest(root, summary)
    by_name = {result["name"]: result for result in manifest["results"]}
    failed = by_name["noisy-failure"]
    assert failed["exit_code"] == 3
    assert failed["stdout"]["bytes"] > bundle.FAILURE_EXCERPT_BYTES
    assert failed["stderr"]["bytes"] > bundle.FAILURE_EXCERPT_BYTES
    stdout_text = (root / failed["stdout"]["path"]).read_text(encoding="utf-8")
    stderr_text = (root / failed["stderr"]["path"]).read_text(encoding="utf-8")
    assert "stdout-start" in stdout_text and "stdout-end" in stdout_text
    assert "stderr-start" in stderr_text and "stderr-end" in stderr_text
    assert (root / by_name["later-step"]["stdout"]["path"]).read_text(
        encoding="utf-8"
    ) == "alpha\nbeta\n"


def _validate_retrieval_and_tamper_detection(root, summary):
    retrieved = io.StringIO()
    metadata = bundle.retrieve_output(
        root=root,
        manifest_path=summary["manifest"],
        evidence_key=summary["evidence_key"],
        step_name="large-read",
        stream_name="stdout",
        head_bytes=32,
        tail_bytes=32,
        stream=retrieved,
    )
    assert metadata["omitted_bytes"] > 0
    assert "start" in retrieved.getvalue()
    assert "end" in retrieved.getvalue()
    assert len(retrieved.getvalue().encode("utf-8")) < 1024
    try:
        bundle.retrieve_output(
            root=root,
            manifest_path=summary["manifest"],
            evidence_key="0" * 64,
            step_name="large-read",
            stream_name="stdout",
            head_bytes=1,
            tail_bytes=1,
        )
    except bundle.InspectionError as error:
        assert "evidence key does not match" in str(error)
    else:
        raise AssertionError("retrieval accepted the wrong manifest identity")
    manifest = _manifest(root, summary)
    large = next(result for result in manifest["results"] if result["name"] == "large-read")
    retained = root / large["stdout"]["path"]
    retained.write_bytes(retained.read_bytes() + b"tampered")
    try:
        bundle.retrieve_output(
            root=root,
            manifest_path=summary["manifest"],
            evidence_key=summary["evidence_key"],
            step_name="large-read",
            stream_name="stdout",
            head_bytes=1,
            tail_bytes=1,
        )
    except bundle.InspectionError as error:
        assert "stream size changed" in str(error)
    else:
        raise AssertionError("retrieval accepted a changed retained stream")


def _validate_cli_is_compact_and_has_no_reuse(root):
    original_root = bundle.ROOT
    original_directory = bundle.default_run_directory
    bundle.ROOT = root
    bundle.default_run_directory = lambda: (
        root / "benchmark-output" / "inspection-bundles" / "cli"
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = bundle.main(
                ["run", "--step", 'read=["cat","--","small.txt"]']
            )
    finally:
        bundle.ROOT = original_root
        bundle.default_run_directory = original_directory
    assert exit_code == 0
    assert stderr.getvalue() == ""
    lines = stdout.getvalue().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith(bundle.PASS_SENTINEL)
    payload = json.loads(lines[0][len(bundle.PASS_SENTINEL) :])
    assert payload["status"] == "PASS"
    assert payload["total_count"] == 1
    assert "reuse" not in json.dumps(payload)
    parser_stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(parser_stderr):
            bundle._build_parser().parse_args(
                ["run", "--reuse-manifest", "old.json"]
            )
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("CLI exposed a reuse option")


def _validate_unsafe_steps(root):
    link = root / "linked.txt"
    link.symlink_to(root / "small.txt")
    unsafe = (
        {"name": "shell", "command": ["sh", "-c", "printf bad"]},
        {"name": "find", "command": ["find", ".", "-type", "f"]},
        {"name": "cat-no-boundary", "command": ["cat", "small.txt"]},
        {"name": "cat-directory", "command": ["cat", "--", "."]},
        {"name": "cat-symlink", "command": ["cat", "--", "linked.txt"]},
        {"name": "escaped-read", "command": ["cat", "--", "../outside"]},
        {"name": "git-read", "command": ["cat", "--", ".git/HEAD"]},
        {
            "name": "writing-sed",
            "command": ["sed", "-i", "1p", "--", "small.txt"],
        },
        {
            "name": "regex-sed",
            "command": ["sed", "-n", "/alpha/p", "--", "small.txt"],
        },
        {
            "name": "unbounded-sed",
            "command": ["sed", "-n", "1,$p", "--", "small.txt"],
        },
        {
            "name": "plain-search",
            "command": ["rg", "alpha", "--", "small.txt"],
        },
        {
            "name": "bundled-search",
            "command": ["rg", "-ni", "alpha", "--", "small.txt"],
        },
        {
            "name": "glob-search",
            "command": ["rg", "-n", "--glob", "*.txt", "alpha", "--", "."],
        },
        {
            "name": "short-glob-search",
            "command": ["rg", "-n", "-g*.txt", "alpha", "--", "."],
        },
        {
            "name": "ignored-search",
            "command": ["rg", "-n", "--no-ignore-vcs", "alpha", "--", "."],
        },
        {
            "name": "preprocessed-search",
            "command": ["rg", "-n", "--pre", "cat", "alpha", "--", "."],
        },
        {
            "name": "hostname-search",
            "command": ["rg", "-n", "--hostname-bin=cat", "alpha", "--", "."],
        },
        {
            "name": "file-search",
            "command": ["rg", "-n", "-fsmall.txt", "--", "."],
        },
        {
            "name": "context-search",
            "command": ["rg", "-n", "-C", "2", "alpha", "--", "."],
        },
        {
            "name": "hidden-inventory",
            "command": ["rg", "--files", "--hidden", "--", "."],
        },
        {
            "name": "missing-path",
            "command": ["rg", "--files", "--", "absent"],
        },
        {
            "name": "dash-pattern",
            "command": ["rg", "-n", "--bad", "--", "small.txt"],
        },
    )
    for step in unsafe:
        try:
            bundle.validate_steps((step,), root)
        except bundle.InspectionError:
            continue
        raise AssertionError("unsafe inspection step was accepted: " + step["name"])
    try:
        bundle.validate_steps(
            (
                {"name": "same", "command": ["cat", "--", "small.txt"]},
                {"name": "same", "command": ["cat", "--", "large.txt"]},
            ),
            root,
        )
    except bundle.InspectionError as error:
        assert "must be unique" in str(error)
    else:
        raise AssertionError("duplicate step names were accepted")


def _validate_untrusted_executable_is_rejected(root):
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-programs-"
    ) as programs:
        fake_cat = pathlib.Path(programs) / "cat"
        fake_cat.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_cat.chmod(0o555)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = programs + os.pathsep + original_path
        try:
            bundle.validate_steps(
                ({"name": "unsafe-cat", "command": ["cat", "--", "small.txt"]},),
                root,
            )
        except bundle.InspectionError as error:
            assert "program resolution is unsafe" in str(error)
        else:
            raise AssertionError("executable in writable directory was accepted")
        finally:
            os.environ["PATH"] = original_path


def _validate_run_directory_collision(root):
    directory = root / "benchmark-output" / "inspection-bundles" / "collision"
    summary = bundle.run_bundle(
        root=root,
        steps=({"name": "read", "command": ["cat", "--", "small.txt"]},),
        run_directory=directory,
    )
    assert summary["status"] == "PASS"
    try:
        bundle.run_bundle(
            root=root,
            steps=({"name": "read", "command": ["cat", "--", "small.txt"]},),
            run_directory=directory,
        )
    except bundle.InspectionError as error:
        assert "already exists" in str(error)
    else:
        raise AssertionError("an existing run directory was overwritten")


def validate():
    temporary, root = _fixture()
    try:
        summary = _validate_quiet_success_and_retention(root)
        _validate_every_run_is_fresh(root, summary)
        _validate_failure_is_bounded_and_complete(root)
        _validate_cli_is_compact_and_has_no_reuse(root)
        _validate_unsafe_steps(root)
        _validate_untrusted_executable_is_rejected(root)
        _validate_run_directory_collision(root)
        _validate_retrieval_and_tamper_detection(root, summary)
    finally:
        temporary.cleanup()
    print("Fresh inspection bundle contract passed")


if __name__ == "__main__":
    validate()
