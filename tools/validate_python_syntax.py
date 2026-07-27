#!/usr/bin/env python3
"""Parse every tracked Python and FreeCAD macro source without importing it."""

from __future__ import annotations

import ast
import pathlib
import subprocess
import sys
import tokenize


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_PATTERNS = ("*.py", "*.FCMacro")
MAX_SOURCE_BYTES = 20 * 1024 * 1024


def _tracked_sources() -> list[pathlib.Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *SOURCE_PATTERNS,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError("git ls-files failed: " + message)

    paths = [
        ROOT / raw.decode("utf-8")
        for raw in result.stdout.split(b"\0")
        if raw
    ]
    if not paths:
        raise RuntimeError("no tracked Python or FCMacro sources found")
    return sorted(paths)


def _parse(path: pathlib.Path) -> None:
    if path.is_symlink():
        raise OSError("tracked source symlinks are not permitted")
    try:
        path.resolve(strict=True).relative_to(ROOT)
    except ValueError as error:
        raise OSError("tracked source resolves outside the repository") from error
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise OSError("tracked source exceeds the 20 MiB parse limit")
    with tokenize.open(path) as source_file:
        source = source_file.read()
    ast.parse(source, filename=str(path))


def main() -> None:
    failures: list[str] = []
    sources = _tracked_sources()
    for path in sources:
        try:
            _parse(path)
        except (OSError, SyntaxError, UnicodeError) as error:
            failures.append(
                "{}: {}".format(path.relative_to(ROOT), error)
            )
    if failures:
        raise AssertionError(
            "tracked source parsing failed:\n" + "\n".join(failures)
        )
    print(
        "Tracked Python and FCMacro parsing passed ({} files)".format(
            len(sources)
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
