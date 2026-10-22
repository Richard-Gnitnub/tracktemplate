#!/usr/bin/env python3
"""Prove the additive private L1 workflow command without native imports."""

import ast
import copy
import inspect
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow as workflow  # noqa: E402
from validate_phase9a_chair_l1 import (  # noqa: E402
    load_package,
    synthetic_l1_package_records,
)
from validate_phase9a_chair_model_scale import REQUEST  # noqa: E402


SENTINEL = "Phase 9B L1 reference preview standalone validation passed"


def _session(factory=None):
    """Exercise the real session constructor with the export host boundary."""
    module = ModuleType("_l1_preview_session_fixture")
    for _field, name in workflow.CORE_LAYOUT_EXPORT_HOST_OPERATIONS:
        exec(f"def {name}(*args, **kwargs):\n    return None\n",
             module.__dict__)
    exec("def run_macro():\n    return run_production_export()\n",
         module.__dict__)
    calculation = SimpleNamespace(
        module=module, _host=SimpleNamespace(source_sha256="fixture"),
        routing_record=lambda: {"route": "modular", "mixed_route": False},
    )
    return workflow.ModularCoreLayoutWorkflowSession(
        calculation, api.run_core_layout_export,
        l1_reference_preview_factory=factory,
    )


def validate_command():
    """Keep explicit inputs, native factory injection and error propagation."""
    records = synthetic_l1_package_records()
    package, text = load_package(*records)
    request = copy.deepcopy(REQUEST)
    expected = {"document_name": "OwnedPreview", "production": False}
    factory = Mock(return_value=expected)
    session = _session(factory)
    assert session.preview_l1_reference_chair(package, text, request) is expected
    factory.assert_called_once_with(package, text, request)
    assert request == REQUEST
    assert session._s1_reference_preview_factory is None
    assert session._s1j_reference_preview_factory is None
    assert session._s1_s1j_reference_preview_factory is None
    for missing in (None, 123):
        try:
            _session(missing).preview_l1_reference_chair(package, text, request)
        except workflow.TransitionWorkflowError as error:
            assert "L1 reference preview adapter is unavailable" in str(error)
        else:
            raise AssertionError("Missing native factory was accepted")
    factory.side_effect = ValueError("invalid L1 input")
    try:
        session.preview_l1_reference_chair(package, text, request)
    except ValueError as error:
        assert str(error) == "invalid L1 input"
    else:
        raise AssertionError("Native input refusal was hidden")
    assert request == REQUEST
    return 3


def validate_additive_wiring():
    """Bind the native factory in the real launcher and forward it once."""
    for operation in (
        workflow.ModularCoreLayoutWorkflowSession,
        workflow.load_modular_transition_workflow_session,
    ):
        signature = inspect.signature(operation)
        parameter = signature.parameters["l1_reference_preview_factory"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None
    tree = ast.parse((ROOT / "TrackTemplate.FCMacro").read_text())
    loader = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_load_modular_transition_workflow")
    calls = [node for node in ast.walk(loader) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)
             and node.func.attr == "load_modular_transition_workflow_session"]
    assert len(calls) == 1
    bindings = {item.arg: item.value for item in calls[0].keywords}
    native = bindings["l1_reference_preview_factory"]
    assert isinstance(native, ast.Attribute)
    assert native.attr == "create_l1_reference_preview"
    assert isinstance(native.value, ast.Name)
    assert native.value.id == "chair_preview"
    tree = ast.parse(inspect.getsource(
        workflow.load_modular_transition_workflow_session,
    ))
    call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "ModularCoreLayoutWorkflowSession")
    forwarded = next(item.value for item in call.keywords
                     if item.arg == "l1_reference_preview_factory")
    assert isinstance(forwarded, ast.Name)
    assert forwarded.id == "l1_reference_preview_factory"
    assert not any(name.split(".")[0] in {
        "FreeCAD", "FreeCADGui", "Part", "pivy",
    } for name in sys.modules)


def main():
    print({"refusals": validate_command(), "native_imports": False})
    validate_additive_wiring()
    print(SENTINEL)


if __name__ == "__main__":
    main()
