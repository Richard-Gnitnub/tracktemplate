#!/usr/bin/env python3
"""Run the pinned freecad-cli checkout tests without requiring pytest."""

import inspect
import pathlib
import runpy
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
EXPECTED_TEST_COUNT = 22

if not (TOOL_ROOT / ".git").is_dir():
    raise SystemExit("Missing development checkout: {}".format(TOOL_ROOT))

sys.path.insert(0, str(TOOL_ROOT / "src"))
sys.path.insert(0, str(TOOL_ROOT))

test_files = sorted((TOOL_ROOT / "tests").glob("test_*.py"))
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
