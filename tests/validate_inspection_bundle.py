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


def _deterministic_rg(directory):
    path = pathlib.Path(directory) / "rg"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import pathlib\n"
        "import re\n"
        "import sys\n"
        "\n"
        "def selected_files(values):\n"
        "    selected = []\n"
        "    for value in values:\n"
        "        path = pathlib.Path(value)\n"
        "        if path.is_file():\n"
        "            selected.append(path)\n"
        "            continue\n"
        "        for base, directories, names in os.walk(path):\n"
        "            directories[:] = sorted(\n"
        "                name for name in directories\n"
        "                if not name.startswith('.')\n"
        "                and name != 'benchmark-output'\n"
        "            )\n"
        "            selected.extend(\n"
        "                pathlib.Path(base) / name\n"
        "                for name in sorted(names)\n"
        "                if not name.startswith('.')\n"
        "            )\n"
        "    return sorted(set(selected), key=lambda item: item.as_posix())\n"
        "\n"
        "arguments = sys.argv[1:]\n"
        "if arguments[:2] == ['--files', '--']:\n"
        "    for selected in selected_files(arguments[2:]):\n"
        "        print(selected.as_posix())\n"
        "    raise SystemExit(0)\n"
        "if len(arguments) >= 4 and arguments[0] == '-n' "
        "and arguments[2] == '--':\n"
        "    pattern = re.compile(arguments[1])\n"
        "    matched = False\n"
        "    for selected in selected_files(arguments[3:]):\n"
        "        try:\n"
        "            lines = selected.read_text(encoding='utf-8').splitlines()\n"
        "        except (OSError, UnicodeDecodeError):\n"
        "            continue\n"
        "        for number, line in enumerate(lines, start=1):\n"
        "            if pattern.search(line):\n"
        "                print(f'{number}:{line}')\n"
        "                matched = True\n"
        "    raise SystemExit(0 if matched else 1)\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path.resolve()


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


def _validate_quiet_success_and_retention(root, fake_rg):
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
    assert by_name["search"]["executable"] == str(fake_rg)
    assert by_name["inventory"]["executable"] == str(fake_rg)
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
        bundle.default_run_directory = lambda: (
            root / "benchmark-output" / "inspection-bundles" / "cli-large"
        )
        large_stdout = io.StringIO()
        with contextlib.redirect_stdout(large_stdout):
            large_exit = bundle.main(
                ["run", "--step", 'read=["cat","--","large.txt"]']
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
    assert large_exit == 0
    assert large_stdout.getvalue().startswith(bundle.PASS_SENTINEL)
    assert len(large_stdout.getvalue().encode("utf-8")) <= 4096
    assert len(large_stdout.getvalue().encode("utf-8")) <= (
        (root / "large.txt").stat().st_size // 10
    )
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


def _validate_missing_program_fails_closed(root, trusted_resolver):
    harness_resolver = bundle._resolve_executable
    original_which = bundle.shutil.which
    bundle._resolve_executable = trusted_resolver
    bundle.shutil.which = lambda program: (
        None if program == "rg" else original_which(program)
    )
    try:
        bundle.validate_steps(
            (
                {
                    "name": "missing-search",
                    "command": ["rg", "-n", "alpha", "--", "small.txt"],
                },
            ),
            root,
        )
    except bundle.InspectionError as error:
        assert "inspection program is unavailable" in str(error)
    else:
        raise AssertionError("a missing inspection program was accepted")
    finally:
        bundle.shutil.which = original_which
        bundle._resolve_executable = harness_resolver


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


def _validate_symlinked_run_directory_is_rejected(root):
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-external-"
    ) as external:
        link = root / "retained-link"
        link.symlink_to(external, target_is_directory=True)
        outside = pathlib.Path(external) / "escaped"
        try:
            bundle.run_bundle(
                root=root,
                steps=(
                    {"name": "read", "command": ["cat", "--", "small.txt"]},
                ),
                run_directory=link / "escaped",
            )
        except bundle.InspectionError as error:
            assert "run directory contains a symbolic link" in str(error)
        else:
            raise AssertionError("a symlinked run directory was accepted")
        assert not outside.exists()


def _receipt_cli(root, arguments):
    original_root = bundle.ROOT
    stdout = io.StringIO()
    stderr = io.StringIO()
    bundle.ROOT = root
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = bundle.main(arguments)
    finally:
        bundle.ROOT = original_root
    return exit_code, stdout.getvalue(), stderr.getvalue()


def _write_receipt(root, name, receipt):
    path = root / "benchmark-output" / "inspection-bundles" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return path


def _validate_compact_receipt_access(root):
    large_stdout = "stdout-start\n" + ("x" * 120000) + "\nstdout-end\n"
    assurance = {
        "assurance_id": "post-pr-99-retained-evidence",
        "expected_head": "a" * 40,
        "profile": "standalone",
        "sample_count": 3,
        "strict": True,
        "elapsed_seconds": 1.25,
        "optional_note": None,
        "limits": {"max_output_bytes": 4096, "minimum_samples": 3},
    }
    receipt = {
        **assurance,
        "commands": [
            {
                "argv": ["python", "-m", "example"],
                "cwd": ".",
                "returncode": 0,
                "stdout": large_stdout,
                "stderr": "",
            },
            {
                "argv": ["python", "-m", "second"],
                "cwd": ".",
                "returncode": 0,
                "stdout": "complete\n",
                "stderr": "",
            },
        ],
        "verdict": "PASS",
    }
    artifact = _write_receipt(root, "large-command-receipt.json", receipt)
    original = artifact.read_bytes()
    evidence_key = hashlib.sha256(original).hexdigest()
    relative = artifact.relative_to(root).as_posix()

    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", relative]
    )
    assert exit_code == 0 and errors == ""
    assert output.startswith(bundle.RECEIPT_SUMMARY_SENTINEL)
    assert len(output.encode("utf-8")) <= 4096
    assert len(output.encode("utf-8")) <= len(original) // 10
    summary = json.loads(output[len(bundle.RECEIPT_SUMMARY_SENTINEL):])
    assert summary["status"] == summary["verdict"] == "PASS"
    assert summary["artifact"] == {
        "bytes": len(original),
        "path": relative,
        "sha256": evidence_key,
    }
    assert summary["commands"] == {
        "count": 2,
        "failed": [],
        "failed_count": 0,
        "omitted_failures": 0,
    }
    assert summary["fields"] == assurance
    assert "commands" not in summary["fields"]
    assert large_stdout not in output
    assert artifact.read_bytes() == original

    exit_code, output, errors = _receipt_cli(
        root,
        [
            "field", "--artifact", relative, "--evidence-key", evidence_key,
            "--command-index", "0", "--field", "stdout",
            "--head-bytes", "64", "--tail-bytes", "64",
        ],
    )
    assert exit_code == 0 and errors == ""
    first_line = output.splitlines()[0]
    assert first_line.startswith(bundle.RECEIPT_FIELD_SENTINEL)
    metadata = json.loads(first_line[len(bundle.RECEIPT_FIELD_SENTINEL):])
    assert metadata["artifact"] == summary["artifact"]
    assert metadata["selected_bytes"] == len(large_stdout.encode("utf-8"))
    assert metadata["selected_sha256"] == hashlib.sha256(
        large_stdout.encode("utf-8")
    ).hexdigest()
    assert metadata["omitted_bytes"] > 0
    assert metadata["status"] == metadata["verdict"] == "PASS"
    assert "stdout-start" in output and "stdout-end" in output
    assert len(output.encode("utf-8")) <= 6144
    assert artifact.read_bytes() == original

    wrong_key = "0" * 64 if evidence_key != "0" * 64 else "1" * 64
    exit_code, output, errors = _receipt_cli(
        root,
        [
            "field", "--artifact", relative, "--evidence-key", wrong_key,
            "--command-index", "0", "--field", "stdout",
        ],
    )
    assert exit_code == 2 and output == ""
    assert "identity changed" in errors

    tampered = _write_receipt(root, "tampered-command-receipt.json", receipt)
    changed = tampered.read_bytes().replace(
        b"stdout-start", b"stdout-other", 1
    )
    assert len(changed) == len(original)
    tampered.write_bytes(changed)
    exit_code, output, errors = _receipt_cli(
        root,
        [
            "field", "--artifact", tampered.relative_to(root).as_posix(),
            "--evidence-key", evidence_key, "--command-index", "0",
            "--field", "stdout",
        ],
    )
    assert exit_code == 2 and output == ""
    assert "identity changed" in errors

    for arguments in (
        ["summary", "--artifact", "benchmark-output/absent.json"],
        ["field", "--artifact", relative, "--evidence-key", evidence_key,
         "--command-index", "7", "--field", "stdout"],
        ["field", "--artifact", relative, "--evidence-key", evidence_key,
         "--command-index", "0", "--field", "absent"],
    ):
        exit_code, output, errors = _receipt_cli(root, arguments)
        assert exit_code == 2 and output == "" and errors

    malformed = root / "benchmark-output" / "malformed-receipt.json"
    malformed.write_text("{bad json", encoding="utf-8")
    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", malformed.relative_to(root).as_posix()]
    )
    assert exit_code == 2 and output == ""
    assert "not valid JSON" in errors

    nested = root / "benchmark-output" / "nested-receipt.json"
    nested.write_text(
        '{"verdict":"PASS","commands":[],"nested":'
        + ("[" * 10000) + "0" + ("]" * 10000) + "}",
        encoding="utf-8",
    )
    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", nested.relative_to(root).as_posix()]
    )
    assert exit_code == 2 and output == ""
    assert "not valid JSON" in errors

    duplicate = root / "benchmark-output" / "duplicate-receipt.json"
    duplicate.write_text(
        '{"verdict":"PASS","verdict":"FAIL","commands":[]}',
        encoding="utf-8",
    )
    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", duplicate.relative_to(root).as_posix()]
    )
    assert exit_code == 2 and output == ""
    assert "duplicate JSON keys" in errors

    nonfinite = root / "benchmark-output" / "nonfinite-receipt.json"
    nonfinite.write_text(
        '{"verdict":"PASS","commands":[{"argv":["echo"],"cwd":".",'
        '"returncode":0,"stdout":"","stderr":""}],'
        '"elapsed_seconds":1e10000}',
        encoding="utf-8",
    )
    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", nonfinite.relative_to(root).as_posix()]
    )
    assert exit_code == 2 and output == ""
    assert "non-finite JSON number" in errors

    surrogate = _write_receipt(
        root,
        "surrogate-receipt.json",
        {
            "verdict": "PASS",
            "commands": [{**receipt["commands"][1], "stdout": "\ud800"}],
        },
    )
    surrogate_original = surrogate.read_bytes()
    surrogate_key = hashlib.sha256(surrogate_original).hexdigest()
    exit_code, output, errors = _receipt_cli(
        root,
        [
            "field", "--artifact", surrogate.relative_to(root).as_posix(),
            "--evidence-key", surrogate_key, "--command-index", "0",
            "--field", "stdout",
        ],
    )
    assert exit_code == 0 and errors == ""
    first_line, selected = output.splitlines()
    metadata = json.loads(first_line[len(bundle.RECEIPT_FIELD_SENTINEL):])
    assert metadata["rendering"] == "canonical-json"
    assert metadata["selected_sha256"] == hashlib.sha256(
        selected.encode("utf-8")
    ).hexdigest()
    assert json.loads(selected) == "\ud800"
    assert len(output.encode("utf-8")) <= bundle.MAX_FIELD_OUTPUT_BYTES
    assert surrogate.read_bytes() == surrogate_original

    oversized = root / "benchmark-output" / "oversized-receipt.json"
    with oversized.open("wb") as stream:
        stream.truncate(bundle.MAX_RECEIPT_BYTES + 1)
    exit_code, output, errors = _receipt_cli(
        root, ["summary", "--artifact", oversized.relative_to(root).as_posix()]
    )
    assert exit_code == 2 and output == ""
    assert "exceeds the read limit" in errors

    long_name = "k" * 7000
    long_field = _write_receipt(
        root, "long-field-receipt.json",
        {
            "verdict": "PASS",
            "commands": [receipt["commands"][1]],
            long_name: "value",
        },
    )
    long_key = hashlib.sha256(long_field.read_bytes()).hexdigest()
    exit_code, output, errors = _receipt_cli(
        root,
        [
            "field", "--artifact", long_field.relative_to(root).as_posix(),
            "--evidence-key", long_key, "--field", long_name,
        ],
    )
    assert exit_code == 2 and output == ""
    assert "exceeds the output limit" in errors

    for name, invalid_receipt in (
        ("empty-commands.json", {"verdict": "PASS", "commands": []}),
        (
            "missing-stdout.json",
            {
                "verdict": "PASS",
                "commands": [
                    {
                        key: value
                        for key, value in receipt["commands"][1].items()
                        if key != "stdout"
                    }
                ],
            },
        ),
    ):
        invalid = _write_receipt(root, name, invalid_receipt)
        exit_code, output, errors = _receipt_cli(
            root,
            ["summary", "--artifact", invalid.relative_to(root).as_posix()],
        )
        assert exit_code == 2 and output == ""
        assert "receipt is invalid" in errors or "result is invalid" in errors

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-external-"
    ) as external:
        outside = pathlib.Path(external) / "receipt.json"
        outside.write_bytes(original)
        linked = root / "linked-receipt.json"
        linked.symlink_to(outside)
        for unsafe, reason in (
            (str(outside), "escapes the repository"),
            (linked.relative_to(root).as_posix(), "symbolic link"),
        ):
            exit_code, output, errors = _receipt_cli(
                root, ["summary", "--artifact", unsafe]
            )
            assert exit_code == 2 and output == "" and reason in errors

    for name, changed_receipt in (
        ("failed-verdict.json", {**receipt, "verdict": "FAIL"}),
        (
            "failed-command.json",
            {
                **receipt,
                "commands": [
                    receipt["commands"][0],
                    {**receipt["commands"][1], "returncode": 7},
                ],
            },
        ),
    ):
        failed_artifact = _write_receipt(root, name, changed_receipt)
        failed_relative = failed_artifact.relative_to(root).as_posix()
        exit_code, output, errors = _receipt_cli(
            root, ["summary", "--artifact", failed_relative]
        )
        assert exit_code == 1 and errors == ""
        failed_summary = json.loads(
            output[len(bundle.RECEIPT_SUMMARY_SENTINEL):]
        )
        assert failed_summary["status"] == "FAIL"
        assert failed_summary["commands"]["count"] == 2
        assert failed_summary["commands"]["failed_count"] == (
            1 if name == "failed-command.json" else 0
        )
        assert failed_summary["commands"]["failed"] == (
            [{"index": 1, "returncode": 7}]
            if name == "failed-command.json" else []
        )
        failed_key = hashlib.sha256(failed_artifact.read_bytes()).hexdigest()
        exit_code, output, errors = _receipt_cli(
            root,
            [
                "field", "--artifact", failed_relative,
                "--evidence-key", failed_key, "--command-index", "1",
                "--field", "stdout", "--head-bytes", "8",
                "--tail-bytes", "8",
            ],
        )
        assert exit_code == 1 and errors == ""
        assert output.startswith(bundle.RECEIPT_FIELD_SENTINEL)


def validate():
    temporary, root = _fixture()
    programs = tempfile.TemporaryDirectory(
        prefix="tracktemplate-inspection-programs-"
    )
    fake_rg = _deterministic_rg(programs.name)
    trusted_resolver = bundle._resolve_executable
    bundle._resolve_executable = lambda program, selected_root: (
        fake_rg
        if program == "rg"
        else trusted_resolver(program, selected_root)
    )
    try:
        summary = _validate_quiet_success_and_retention(root, fake_rg)
        _validate_every_run_is_fresh(root, summary)
        _validate_failure_is_bounded_and_complete(root)
        _validate_cli_is_compact_and_has_no_reuse(root)
        _validate_unsafe_steps(root)
        _validate_untrusted_executable_is_rejected(root)
        _validate_missing_program_fails_closed(root, trusted_resolver)
        _validate_run_directory_collision(root)
        _validate_symlinked_run_directory_is_rejected(root)
        _validate_retrieval_and_tamper_detection(root, summary)
        _validate_compact_receipt_access(root)
    finally:
        bundle._resolve_executable = trusted_resolver
        programs.cleanup()
        temporary.cleanup()
    print("Fresh inspection bundle contract passed")


if __name__ == "__main__":
    validate()
