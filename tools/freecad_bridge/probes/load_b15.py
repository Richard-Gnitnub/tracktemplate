"""Load B15 definitions into a named module without launching its main dialog."""

import ast
import json
import os
import pathlib
import sys
import types

module_name = "tracktemplate_b15_session"
macro_path = (
    pathlib.Path(os.environ["TRACKTEMPLATE_REPO"])
    / "model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro"
)

if module_name in sys.modules:
    module = sys.modules[module_name]
    state = "already_loaded"
else:
    source = macro_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(macro_path))
    final_statement = tree.body[-1] if tree.body else None
    if not (
        isinstance(final_statement, ast.Expr)
        and isinstance(final_statement.value, ast.Call)
        and isinstance(final_statement.value.func, ast.Name)
        and final_statement.value.func.id == "run_macro"
    ):
        raise RuntimeError("The B15 launch boundary was not the expected final run_macro() call")
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType(module_name)
    module.__file__ = str(macro_path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        exec(compile(tree, str(macro_path), "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    state = "loaded"

if str(module.MACRO_VERSION_NUMBER) != "10.2A8A7B15":
    raise RuntimeError("Unexpected B15 version: {}".format(module.MACRO_VERSION_NUMBER))

print(json.dumps({
    "state": state,
    "module": module_name,
    "macro_path": str(macro_path),
    "version": str(module.MACRO_VERSION_NUMBER),
    "representation_revision": int(module.CHAIR_2D_REPRESENTATION_REVISION),
    "has_turnout_manager": hasattr(module, "TurnoutManagerDialog"),
    "has_crossover_manager": hasattr(module, "CrossoverManagerPanel"),
}, sort_keys=True))
