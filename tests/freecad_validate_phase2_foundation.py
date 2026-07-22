#!/usr/bin/env python3
"""Load the B16 foundation and non-routing Phase 3 domain extension."""

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
    "public_api": [
        "DEVELOPMENT_CHECKPOINT",
        "clothoid_entry_displacement",
        "transition_start_signed_offset",
        "solve_transition_length",
    ],
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
assert {
    node.name
    for node in alignment_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
} == {
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
}, "Phase 3 alignment function boundary drifted"
for name in (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
):
    assert getattr(api, name) is getattr(alignment, name), (
        "Phase 3 façade does not expose the domain function: " + name
    )

print("Phase 2 FreeCAD foundation smoke test passed")
print("Phase 3 transition domain smoke test passed")
