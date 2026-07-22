#!/usr/bin/env python3
"""Validate the retained structure of Phase 4 FreeCAD transition persistence."""

import ast
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402


ADAPTER_PATH = (
    ROOT / "tracktemplate" / "adapters" / "freecad" / "transition_state.py"
)
FREECAD_TEST_PATH = ROOT / "tests" / "freecad_validate_phase4_transition_persistence.py"
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _definitions(tree):
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _literal_assignment(tree, name):
    matches = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            matches.append(node.value)
    assert len(matches) == 1, name
    return ast.literal_eval(matches[0])


def _validate_adapter_source():
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ADAPTER_PATH))
    assert {
        "TransitionDocumentError",
        "FreeCADTransitionStore",
        "read_transition_object",
        "find_transition_object",
        "_write_transition_payload",
    } <= _definitions(tree)
    assert _literal_assignment(tree, "FREECAD_TRANSITION_OBJECT_TYPE") == (
        "App::FeaturePython"
    )
    assert _literal_assignment(tree, "FREECAD_RECORD_TYPE_PROPERTY") == (
        "TrackTemplateRecordType"
    )
    assert _literal_assignment(tree, "FREECAD_STATE_JSON_PROPERTY") == (
        "TrackTemplateStateJSON"
    )

    imported_roots = set()
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
            imported_modules.add(node.module or "")
    assert imported_roots == {"FreeCAD", "hashlib", "tracktemplate"}
    assert "tracktemplate.application.transition_state" in imported_modules
    assert not ({"Part", "FreeCADGui", "PySide", "PySide2", "PySide6", "pivy"} & imported_roots)

    assert "openTransaction(" in source
    assert "commitTransaction(" in source
    assert "abortTransaction(" in source
    assert "recompute(" not in source
    assert "Part.Shape" not in source


def _validate_dependency_boundary():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    for module_name in (
        "tracktemplate.adapters",
        "tracktemplate.adapters.freecad",
        "tracktemplate.adapters.freecad.transition_state",
    ):
        assert modules[module_name]["layer"] == "adapter"
        assert modules[module_name]["warning_signals"] == []
    assert modules["tracktemplate.adapters"]["imports"] == []
    assert modules["tracktemplate.adapters.freecad"]["imports"] == []
    adapter = modules["tracktemplate.adapters.freecad.transition_state"]
    assert adapter["imports"] == [
        "FreeCAD",
        "hashlib",
        "tracktemplate.application.transition_state",
    ]
    assert {
        "from": "tracktemplate.adapters.freecad.transition_state",
        "to": "tracktemplate.application.transition_state",
    } in report["import_edges"]
    api = modules["tracktemplate.api"]
    assert not any(name.startswith("tracktemplate.adapters") for name in api["imports"])

    script = """
import importlib.abc
import json
import sys

forbidden = {{"FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"}}
attempted = []

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden host import: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {root!r})
import tracktemplate.adapters
import tracktemplate.adapters.freecad
print(json.dumps({{"attempted": attempted}}))
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"attempted": []}


def _validate_freecad_fixture_contract():
    source = FREECAD_TEST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(FREECAD_TEST_PATH))
    functions = _definitions(tree)
    assert {
        "_validate_lifecycle",
        "_validate_create_history_and_failures",
        "_validate_stale_and_corrupt_records",
        "_validate_runtime_gate",
    } <= functions
    for marker in (
        "TemporaryDirectory",
        "UndoMode = 1",
        ".undo()",
        ".redo()",
        "saveAs(",
        "App.openDocument(",
        "stale-analysis-discarded",
        "transaction-failed",
        "duplicate-stable-identity",
        "Phase 4 transition FreeCAD persistence validation passed",
    ):
        assert marker in source


def _validate_controls():
    for relative, expected in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(encoding="utf-8")
    assert "PHASE4_CANONICAL_STATE.md" in plan
    assert "FreeCAD persistence tranche" in evidence
    assert "freecad_validate_phase4_transition_persistence.py" in validation


def validate():
    _validate_adapter_source()
    _validate_dependency_boundary()
    _validate_freecad_fixture_contract()
    _validate_controls()
    print("Phase 4 transition persistence structure validation passed")


if __name__ == "__main__":
    validate()
