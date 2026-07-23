"""Prepare one qualified B16 transition route for an embedded GUI oracle."""

import ast
import hashlib
import importlib
import os
import pathlib
import sys
import types


_PHASE3_ROUTE = globals().get("TRACKTEMPLATE_PHASE3_ROUTE")
_PHASE3_REPOSITORY_ROOT = pathlib.Path(
    os.environ["TRACKTEMPLATE_REPO"]
).resolve()
_PHASE3_LAUNCHER_PATH = _PHASE3_REPOSITORY_ROOT / "TrackTemplate.FCMacro"
_PHASE3_LAUNCHER_SOURCE = _PHASE3_LAUNCHER_PATH.read_text(encoding="utf-8")
_PHASE3_LAUNCHER_TREE = ast.parse(
    _PHASE3_LAUNCHER_SOURCE,
    filename=str(_PHASE3_LAUNCHER_PATH),
)
_PHASE3_FINAL = (
    _PHASE3_LAUNCHER_TREE.body[-1]
    if _PHASE3_LAUNCHER_TREE.body
    else None
)
if not (
    isinstance(_PHASE3_FINAL, ast.Assign)
    and len(_PHASE3_FINAL.targets) == 1
    and isinstance(_PHASE3_FINAL.targets[0], ast.Name)
    and _PHASE3_FINAL.targets[0].id == "FOUNDATION_RESULT"
    and isinstance(_PHASE3_FINAL.value, ast.Call)
    and isinstance(_PHASE3_FINAL.value.func, ast.Name)
    and _PHASE3_FINAL.value.func.id == "run_macro"
    and not _PHASE3_FINAL.value.args
    and not _PHASE3_FINAL.value.keywords
):
    raise RuntimeError(
        "The B16 composition launch boundary is not the expected final call."
    )
_PHASE3_LAUNCHER_TREE.body.pop()
ast.fix_missing_locations(_PHASE3_LAUNCHER_TREE)

_PHASE3_COMPOSITION_NAME = "tracktemplate_b16_phase3_bridge_composition"
if _PHASE3_COMPOSITION_NAME in sys.modules:
    raise RuntimeError("A Phase 3 bridge composition is already loaded.")
_PHASE3_COMPOSITION = types.ModuleType(_PHASE3_COMPOSITION_NAME)
_PHASE3_COMPOSITION.__file__ = str(_PHASE3_LAUNCHER_PATH)
_PHASE3_COMPOSITION.__package__ = ""
sys.modules[_PHASE3_COMPOSITION_NAME] = _PHASE3_COMPOSITION
try:
    exec(
        compile(
            _PHASE3_LAUNCHER_TREE,
            str(_PHASE3_LAUNCHER_PATH),
            "exec",
        ),
        _PHASE3_COMPOSITION.__dict__,
    )
except Exception:
    sys.modules.pop(_PHASE3_COMPOSITION_NAME, None)
    raise

_PHASE3_API, _PHASE3_BOOTSTRAP = _PHASE3_COMPOSITION._load_foundation(
    _PHASE3_REPOSITORY_ROOT
)
_PHASE3_QUALIFICATION = _PHASE3_BOOTSTRAP.require_qualified_runtime(
    _PHASE3_REPOSITORY_ROOT
    / "reference"
    / "contracts"
    / "phase1-compatibility.json"
)
_PHASE3_PRODUCT_COMPOSITION = _PHASE3_ROUTE == "modular"
if _PHASE3_PRODUCT_COMPOSITION:
    _PHASE3_SESSION, _PHASE3_ROUTING = (
        _PHASE3_COMPOSITION._load_modular_transition_workflow(
            _PHASE3_REPOSITORY_ROOT,
            _PHASE3_API,
            _PHASE3_BOOTSTRAP,
        )
    )
else:
    _PHASE3_ORACLE = importlib.import_module("tools.phase3_transition_pilot")
    _PHASE3_TRANSITION_CONTRACT = _PHASE3_BOOTSTRAP.load_contract(
        _PHASE3_REPOSITORY_ROOT
        / "reference"
        / "contracts"
        / "phase1-transition-pilot.json"
    )
    _PHASE3_SESSION = _PHASE3_ORACLE.load_transition_pilot_session(
        _PHASE3_REPOSITORY_ROOT,
        _PHASE3_API,
        _PHASE3_TRANSITION_CONTRACT,
    )
    _PHASE3_ROUTING = _PHASE3_SESSION.apply_route(_PHASE3_ROUTE)

_PHASE3_WORKFLOW_MODULE_NAME = "tracktemplate_b16_transition_workflow_session"
if _PHASE3_WORKFLOW_MODULE_NAME in sys.modules:
    raise RuntimeError("A Phase 3 routed workflow module is already loaded.")
sys.modules[_PHASE3_WORKFLOW_MODULE_NAME] = _PHASE3_SESSION.module
TRACKTEMPLATE_WORKFLOW_MODULE_NAME = _PHASE3_WORKFLOW_MODULE_NAME
TRACKTEMPLATE_CAPTURE_WORKFLOW_RESULT = True
TRACKTEMPLATE_BASE_MACRO_VERSION = "10.2A8A7B15"
TRACKTEMPLATE_ENFORCE_FROZEN_WORKFLOW_HASHES = False
TRACKTEMPLATE_ALLOWED_HANDING_IDENTITY_CHANGES = ("GeneratorVersion",)
TRACKTEMPLATE_ALLOWED_HANDING_PERSISTED_CHANGES = (
    "ProductionRecordIndexJSON",
)
TRACKTEMPLATE_VERSION_MIGRATION_PREFIXES = (
    "10.2A8A7B14",
    "10.2A8A7B15",
)

_PHASE3_BINDINGS_BEFORE = {
    name: _PHASE3_SESSION.module.__dict__[name]
    for name in _PHASE3_ROUTING["function_names"]
}
_PHASE3_BINDING_RECORDS_BEFORE = {
    name: {
        "module": str(getattr(function, "__module__", "")),
        "name": str(getattr(function, "__name__", "")),
        "qualname": str(getattr(function, "__qualname__", "")),
    }
    for name, function in sorted(_PHASE3_BINDINGS_BEFORE.items())
}
_PHASE3_LAUNCHER_SHA256 = hashlib.sha256(
    _PHASE3_LAUNCHER_PATH.read_bytes()
).hexdigest()
