#!/usr/bin/env python3
"""Load durable B16 foundation boundaries in the qualified FreeCAD host."""

import ast
import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


launcher_path = ROOT / "TrackTemplate.FCMacro"
launcher_tree = ast.parse(
    launcher_path.read_text(encoding="utf-8"),
    filename=str(launcher_path),
)
launcher_tree.body = [
    node
    for node in launcher_tree.body
    if not (
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "FOUNDATION_RESULT"
            for target in node.targets
        )
    )
]
namespace = {
    "__file__": str(launcher_path),
    "__name__": "tracktemplate_freecad_loading_smoke",
}

before = _document_state()
exec(compile(launcher_tree, str(launcher_path), "exec"), namespace)
assert namespace["_launcher_root"]() == ROOT
api, bootstrap = namespace["_load_foundation"](ROOT)
qualification = bootstrap.require_qualified_runtime(
    ROOT / "reference" / "contracts" / "phase1-compatibility.json"
)
after = _document_state()
assert before == after, "B16 foundation loading changed FreeCAD document state"
assert api.DEVELOPMENT_CHECKPOINT == "10.2A8A7B16"
assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)

import tracktemplate.domain as domain  # noqa: E402

assert pathlib.Path(api.__file__).resolve().is_relative_to(ROOT)
assert pathlib.Path(domain.__file__).resolve().is_relative_to(ROOT)

print("Phase 2 FreeCAD foundation smoke test passed")
