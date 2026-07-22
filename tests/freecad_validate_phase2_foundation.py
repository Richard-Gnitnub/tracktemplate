#!/usr/bin/env python3
"""Load the B16 Phase 2 foundation in the qualified FreeCAD runtime."""

import ast
import json
import pathlib
import runpy
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


before = _document_state()
namespace = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
after = _document_state()
result = namespace.get("FOUNDATION_RESULT")

assert before == after, "B16 foundation loading changed FreeCAD document state"
assert result == {
    "schema_version": 1,
    "development_checkpoint": "10.2A8A7B16",
    "status": "foundation-loaded-not-routed",
    "matched_profile_id": "linux-x86_64-flatpak-freecad-1.1.1",
    "public_api": ["DEVELOPMENT_CHECKPOINT"],
    "calculation_routing": "not-started",
    "document_mutation": False,
}, "B16 foundation result drifted"
json.dumps(result, sort_keys=True)

import tracktemplate.api as api  # noqa: E402
import tracktemplate.domain.alignment as alignment  # noqa: E402

assert pathlib.Path(api.__file__).resolve().is_relative_to(ROOT)
assert pathlib.Path(alignment.__file__).resolve().is_relative_to(ROOT)
alignment_tree = ast.parse(
    pathlib.Path(alignment.__file__).read_text(encoding="utf-8"),
    filename=alignment.__file__,
)
assert not any(
    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    for node in alignment_tree.body
), "Phase 2 alignment boundary contains premature calculation code"

print("Phase 2 FreeCAD foundation smoke test passed")
