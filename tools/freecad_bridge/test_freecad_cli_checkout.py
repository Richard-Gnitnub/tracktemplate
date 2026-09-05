#!/usr/bin/env python3
"""Run the pinned freecad-cli checkout tests without requiring pytest."""

import inspect
import pathlib
import runpy
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
EXPECTED_TEST_COUNT = 22
TEST_FILES = (
    "tests/test_cli.py",
    "tests/test_client.py",
    "tests/test_output.py",
)

if not (TOOL_ROOT / ".git").is_dir():
    raise SystemExit("Missing development checkout: {}".format(TOOL_ROOT))

sys.path[:0] = [
    str(TOOL_ROOT / "src"),
    str(TOOL_ROOT),
    "/usr/lib/python3/dist-packages",
]

test_files = [TOOL_ROOT / relative for relative in TEST_FILES]
if any(not path.is_file() for path in test_files):
    raise SystemExit("The exact FreeCAD GUI bridge tests are unavailable")
namespaces = [runpy.run_path(str(path)) for path in test_files]
tests = [
    value
    for namespace in namespaces
    for name, value in namespace.items()
    if name.startswith("test_")
    and callable(value)
    and not inspect.signature(value).parameters
]
if len(tests) != EXPECTED_TEST_COUNT:
    raise AssertionError(
        "Expected {} zero-argument bridge tests, found {}".format(
            EXPECTED_TEST_COUNT,
            len(tests),
        )
    )

for test in tests:
    test()

print("{} bridge tests passed".format(len(tests)))
