#!/usr/bin/env python3
"""Validate retirement of the active Phase 3 B15 comparison switch."""

import ast
import hashlib
import importlib.abc
import json
import pathlib
import subprocess
import sys
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tracktemplate import compatibility  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402


LAUNCHER_PATH = ROOT / "TrackTemplate.FCMacro"
HOST_PATH = (
    ROOT / "tracktemplate" / "compatibility" / "b15_workflow_host.py"
)
WORKFLOW_PATH = (
    ROOT / "tracktemplate" / "compatibility" / "transition_workflow.py"
)
ORACLE_PATH = ROOT / "tools" / "phase3_transition_pilot.py"
FREECAD_TEST_PATH = ROOT / "tests" / "freecad_validate_phase3_transition_slice.py"
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


def _function(tree, name):
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    assert len(matches) == 1, name
    return matches[0]


def _validate_launcher():
    source = LAUNCHER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(LAUNCHER_PATH))
    definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_load_modular_transition_workflow" in definitions
    assert "_load_transition_pilot" not in definitions

    runner = _function(tree, "run_macro")
    assert [item.arg for item in runner.args.args] == ["launch_workflow"]
    assert len(runner.args.defaults) == 1
    assert isinstance(runner.args.defaults[0], ast.Constant)
    assert runner.args.defaults[0].value is False
    assert runner.args.vararg is None
    assert runner.args.kwarg is None

    final = tree.body[-1]
    assert isinstance(final, ast.Assign)
    assert len(final.targets) == 1
    assert isinstance(final.targets[0], ast.Name)
    assert final.targets[0].id == "FOUNDATION_RESULT"
    assert isinstance(final.value, ast.Call)
    assert isinstance(final.value.func, ast.Name)
    assert final.value.func.id == "run_macro"
    assert final.value.args == [] and final.value.keywords == []

    for retired in (
        "calculation_route",
        "rollback_calculation_routing",
        "legacy_source_sha256",
        "_load_transition_pilot",
    ):
        assert retired not in source
    for required in (
        '"calculation_routing": "modular"',
        '"legacy_comparison_route_available": False',
        '"workflow_host_loaded": bool(routing)',
        "if launch_workflow:",
    ):
        assert required in source


def _validate_product_boundary():
    assert compatibility.__all__ == (
        "TransitionWorkflowError",
        "load_modular_transition_workflow_session",
    )
    for retired in (
        "CALCULATION_ROUTES",
        "LEGACY_ROUTE",
        "MODULAR_CALCULATION_ROUTE",
        "ModularTransitionWorkflowSession",
        "TransitionPilotError",
        "load_transition_pilot_session",
    ):
        assert not hasattr(compatibility, retired)

    workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")
    for retired in (
        "LEGACY_ROUTE",
        "CALCULATION_ROUTES",
        "apply_route",
        "rollback_route",
    ):
        assert retired not in workflow_source
    assert "comparison_route_available" in workflow_source
    assert "load_b15_workflow_host" in workflow_source

    class FakeHost:
        def __init__(self):
            self.module = types.SimpleNamespace()
            self.source_sha256 = "a" * 64
            self.bindings = []
            self.launches = 0

        def bind_transition_functions(self, label, functions):
            self.bindings.append((label, dict(functions)))

        def launch_workflow(self):
            self.launches += 1
            return "launched"

    functions = {
        name: (lambda *arguments: arguments)
        for name in (
            "clothoid_entry_displacement",
            "transition_start_signed_offset",
            "solve_transition_length",
        )
    }
    host = FakeHost()
    session = transition_workflow.ModularTransitionWorkflowSession(
        host,
        functions,
    )
    assert len(host.bindings) == 1
    assert host.bindings[0][0] == "modular"
    assert host.bindings[0][1] == functions
    assert not hasattr(session, "apply_route")
    assert session.routing_record() == {
        "schema_version": 1,
        "route": "modular",
        "comparison_route_available": False,
        "function_names": list(functions),
        "caller_names": [
            "main_circle_centre",
            "build_concentric_core",
            "prepare_track_alignment",
        ],
        "workflow_version": "10.2A8A7B15",
        "workflow_source_sha256": "a" * 64,
        "mixed_route": False,
    }
    assert session.launch_workflow() == "launched"
    assert host.launches == 1
    assert len(host.bindings) == 2
    assert all(item[0] == "modular" for item in host.bindings)


def _validate_development_oracle_boundary():
    source = ORACLE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ORACLE_PATH))
    assert "Development-only dual-route oracle" in source
    assert 'LEGACY_ROUTE = "legacy"' in source
    assert 'MODULAR_ROUTE = "modular"' in source
    assert "load_b15_workflow_host" in source
    assert "apply_route" in source
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and (
            any(
                alias.name in {"FreeCAD", "FreeCADGui", "Part"}
                for alias in node.names
            )
            if isinstance(node, ast.Import)
            else (node.module or "").split(".", 1)[0]
            in {"FreeCAD", "FreeCADGui", "Part"}
        )
        for node in ast.walk(tree)
    )
    assert not (
        ROOT / "tracktemplate" / "compatibility" / "transition_pilot.py"
    ).exists()


def _validate_structure_and_lazy_import():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    assert "tracktemplate.compatibility.transition_pilot" not in modules
    host = modules["tracktemplate.compatibility.b15_workflow_host"]
    workflow = modules["tracktemplate.compatibility.transition_workflow"]
    assert host["layer"] == workflow["layer"] == "compatibility"
    assert host["warning_signals"] == workflow["warning_signals"] == []
    assert not report["cycles"]
    assert not report["prohibited_layer_edges"]

    script = """
import importlib.abc
import json
import sys

attempted = []
forbidden = {{"FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"}}

class Blocked(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in forbidden:
            attempted.append(fullname)
            raise AssertionError("forbidden import attempted: " + fullname)
        return None

sys.meta_path.insert(0, Blocked())
sys.path.insert(0, {root!r})
import tracktemplate.compatibility as compatibility
print(json.dumps({{
    "attempted": attempted,
    "exports": list(compatibility.__all__),
    "host_modules": sorted(
        name for name in sys.modules
        if name.startswith("_tracktemplate_b15_workflow_")
    ),
    "tools_loaded": "tools.phase3_transition_pilot" in sys.modules,
}}, sort_keys=True))
""".format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "attempted": [],
        "exports": list(compatibility.__all__),
        "host_modules": [],
        "tools_loaded": False,
    }


def _validate_evidence_controls():
    for relative, expected_hash in SOURCE_HASHES.items():
        assert _sha256(ROOT / relative) == expected_hash
    assert FREECAD_TEST_PATH.is_file()
    freecad_source = FREECAD_TEST_PATH.read_text(encoding="utf-8")
    for marker in (
        "modular-foundation-ready",
        "legacy_comparison_route_available",
        "workflow_host_loaded",
        "tools import phase3_transition_pilot",
        "Phase 3 transition routing FreeCAD smoke test passed",
    ):
        assert marker in freecad_source

    evidence = (ROOT / "reference" / "PHASE4_CANONICAL_STATE.md").read_text(
        encoding="utf-8"
    )
    plan = (ROOT / "reference" / "PROJECT_PLAN.md").read_text(encoding="utf-8")
    validation = (ROOT / "reference" / "VALIDATION.md").read_text(
        encoding="utf-8"
    )
    assert "Active comparison-route retirement" in evidence
    assert "comparison route retired; acceptance pending" in plan
    assert "validate_phase4_transition_route_retirement.py" in validation


def validate():
    _validate_launcher()
    _validate_product_boundary()
    _validate_development_oracle_boundary()
    _validate_structure_and_lazy_import()
    _validate_evidence_controls()
    print("Phase 4 transition comparison-route retirement validation passed")


if __name__ == "__main__":
    validate()
