"""Headless structural and analytical checks for the B15 FreeCAD macro.

These checks do not replace a real FreeCAD 1.1 run.  They provide fast coverage
for import-time compatibility, workflow structure, chair support calculations,
layout caching boundaries and preservation of established railway functions.
"""

import ast
import copy
import pathlib
import sys
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
B14_PATH = ROOT / "AdvancedTurnout.FCMacro"
B15_PATH = ROOT / "model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro"
B15_LAYER_MARKER = "# A8A7B15 chair performance and representation."


class _EnumValue:
    def __getattr__(self, _name):
        return self

    def __or__(self, _other):
        return self

    def __and__(self, _other):
        return self

    def __ror__(self, _other):
        return self

    def __rand__(self, _other):
        return self

    def __int__(self):
        return 0

    def __index__(self):
        return 0

    def __bool__(self):
        return False


_ENUM = _EnumValue()


class _DummyMeta(type):
    def __getattr__(cls, _name):
        return _ENUM


class _Dummy(metaclass=_DummyMeta):
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, _name):
        return lambda *args, **kwargs: _Dummy()


class _DynamicModule(types.ModuleType):
    def __getattr__(self, name):
        if name in ("Qt", "QIODevice"):
            return _ENUM
        if name in ("Signal", "Slot", "Property"):
            return lambda *args, **kwargs: _Dummy()
        return _Dummy


def _load_namespace():
    freecad = _DynamicModule("FreeCAD")
    freecad.ActiveDocument = None
    freecad.Vector = _Dummy
    freecad.Placement = _Dummy
    freecad.Rotation = _Dummy
    part = _DynamicModule("Part")
    freecad_gui = _DynamicModule("FreeCADGui")
    qtcore = _DynamicModule("QtCore")
    qtgui = _DynamicModule("QtGui")
    qtwidgets = _DynamicModule("QtWidgets")
    pyside = types.ModuleType("PySide")
    pyside.QtCore = qtcore
    pyside.QtGui = qtgui
    pyside.QtWidgets = qtwidgets
    previous = {name: sys.modules.get(name) for name in ("FreeCAD", "Part", "FreeCADGui", "PySide")}
    sys.modules.update({
        "FreeCAD": freecad,
        "Part": part,
        "FreeCADGui": freecad_gui,
        "PySide": pyside,
    })
    try:
        source = B15_PATH.read_text(encoding="utf-8")
        source_without_launch = source.rsplit("\nrun_macro()", 1)[0]
        namespace = {"__name__": "b15_standin"}
        exec(compile(source_without_launch, str(B15_PATH), "exec"), namespace)
        return namespace, source
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _rotated_rectangle(centre_x, centre_y, half_x, half_y, degrees):
    import math

    angle = math.radians(degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    points = []
    for local_x, local_y in ((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)):
        points.append([
            centre_x + local_x * cosine - local_y * sine,
            centre_y + local_x * sine + local_y * cosine,
        ])
    return points


def _timber(identity):
    return {
        "stable_identity": identity,
        "identifier": identity,
        "centre": [0.0, 0.0],
        "length_axis": [0.0, 1.0],
        "width_axis": [1.0, 0.0],
        "length": 20.0,
        "width": 3.0,
        "outline_polygon": [[-1.5, -10.0], [1.5, -10.0], [1.5, 10.0], [-1.5, 10.0]],
        "collision_polygon": [[-1.5, -10.0], [1.5, -10.0], [1.5, 10.0], [-1.5, 10.0]],
    }


def _function_nodes(source):
    tree = ast.parse(source)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return tree, result


class _NormaliseRecompute(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "_document_recompute" and len(node.args) == 1:
            return ast.copy_location(
                ast.Call(
                    func=ast.Attribute(value=copy.deepcopy(node.args[0]), attr="recompute", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
                node,
            )
        return node


def _normalised_function_dump(node):
    clone = copy.deepcopy(node)
    clone = _NormaliseRecompute().visit(clone)
    ast.fix_missing_locations(clone)
    return ast.dump(clone, include_attributes=False)


def _normalised_inherited_module_dump(source, stop_before_marker=None):
    inherited_source = source
    if stop_before_marker is not None:
        marker_index = inherited_source.find(stop_before_marker)
        assert marker_index >= 0, stop_before_marker
        inherited_source = inherited_source[:marker_index]
    tree = ast.parse(inherited_source)
    retained = []
    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {"MACRO_VERSION", "MACRO_VERSION_NUMBER"}:
                continue
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "run_macro"
        ):
            continue
        retained.append(node)
    tree.body = retained
    tree = _NormaliseRecompute().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.dump(tree, include_attributes=False)


def validate():
    namespace, source = _load_namespace()
    assert namespace["MACRO_VERSION_NUMBER"] == "10.2A8A7B15"
    assert namespace["CHAIR_2D_REPRESENTATION_REVISION"] == 2

    tree, functions = _function_nodes(source)
    version_assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "MACRO_VERSION_NUMBER":
            version_assignments.append(ast.literal_eval(node.value))
    assert version_assignments and set(version_assignments) == {"10.2A8A7B15"}
    workflow_lengths = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "GuidedTrackworkWorkflowPanel" and len(node.args) >= 2:
            if isinstance(node.args[1], (ast.Tuple, ast.List)):
                workflow_lengths.append(len(node.args[1].elts))
    assert workflow_lengths == [7, 7], workflow_lengths

    display_node = functions["_create_chair_2d_layout_display"][-1]
    for loop in [node for node in ast.walk(display_node) if isinstance(node, (ast.For, ast.While))]:
        for descendant in ast.walk(loop):
            if not isinstance(descendant, ast.Call):
                continue
            if isinstance(descendant.func, ast.Attribute) and descendant.func.attr == "addObject":
                raise AssertionError("The 2D display creates a document object inside a per-chair loop.")
            if isinstance(descendant.func, ast.Name) and descendant.func.id == "_chair_make_2d_feature":
                raise AssertionError("The 2D display creates a Part feature inside a per-chair loop.")
    display_calls = [
        node for node in ast.walk(display_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_chair_make_2d_feature"
    ]
    assert len(display_calls) == 5
    display_text = ast.get_source_segment(source, display_node) or ""
    assert "Part.makeBox" not in display_text
    assert "_chair_make_s1_prototype_shape" not in display_text
    assert "_chair_build_compound_from_plan" not in display_text

    dims_s1 = namespace["_chair_s1_body_dimensions"](1)
    dims_s1j = namespace["_chair_s1_body_dimensions"](7)
    assert abs(dims_s1["base_x_min"] - dims_s1j["base_x_min"]) < 1.0e-12
    assert abs(dims_s1["base_x_max"] - dims_s1j["base_x_max"]) < 1.0e-12
    assert abs((dims_s1j["base_y_half"] / dims_s1["base_y_half"]) - 1.25) < 1.0e-12
    symbol_s1, symbol_s1_reused = namespace["_chair_canonical_2d_symbol"](1)
    symbol_s1_again, symbol_s1_again_reused = namespace["_chair_canonical_2d_symbol"](1)
    symbol_s1j, symbol_s1j_reused = namespace["_chair_canonical_2d_symbol"](7)
    assert symbol_s1["chair_label"] == "S1" and symbol_s1j["chair_label"] == "S1J"
    assert symbol_s1["detail_wire_count"] >= 8 and symbol_s1["key_wire_count"] == 3
    assert symbol_s1_reused is False and symbol_s1_again_reused is True
    assert symbol_s1_again is symbol_s1 and symbol_s1j_reused is False

    instances = [
        {
            "chair_position_identity": "left-chair",
            "timber_identity": "left-timber",
            "timber_identifier": "left-timber",
            "physical_footprint_polygon": _rotated_rectangle(-0.35, 0.0, 1.0, 1.8, 15.0),
        },
        {
            "chair_position_identity": "right-chair",
            "timber_identity": "right-timber",
            "timber_identifier": "right-timber",
            "physical_footprint_polygon": _rotated_rectangle(0.35, 0.0, 1.0, 1.8, -15.0),
        },
    ]
    adjustments = namespace["_chair_physical_model_support_adjustments"](
        instances, [_timber("left-timber"), _timber("right-timber")]
    )
    by_id = {item["timber_identity"]: item for item in adjustments}
    assert by_id["left-timber"]["required_approach_side_extension"] > 0.0
    assert by_id["right-timber"]["required_exit_side_extension"] > 0.0
    assert by_id["left-timber"]["applied"] and by_id["right-timber"]["applied"]
    for adjustment in adjustments:
        required = adjustment["maximum_extension_per_side"]
        assert abs(required / 0.05 - round(required / 0.05)) < 1.0e-9

    limited = namespace["default_chair_analysis_settings"]()
    limited["preferred_maximum_model_support_extension_per_side"] = 0.10
    rejected = namespace["_chair_physical_model_support_adjustments"](
        instances[:1], [_timber("left-timber")], limited
    )[0]
    assert rejected["limit_exceeded"] is True
    assert rejected["applied"] is False
    assert rejected["prototype_timber_width_unchanged"] is True
    adjusted_timber = namespace["_chair_transform_timber_for_model_support"](
        _timber("left-timber"), by_id["left-timber"]
    )
    assert adjusted_timber["prototype_width"] == 3.0
    assert adjusted_timber["width"] > adjusted_timber["prototype_width"]
    assert adjusted_timber["model_support_adjusted"] is True

    class _Doc:
        Objects = []

    doc = _Doc()
    analysis = {"geometry_signature": "same", "positions": []}
    config = {"turnout_id": "TURNOUT-CACHE", "template_thickness": 1.0}
    first_plan = namespace["_chair_build_solid_plan"](doc, "turnout", config, analysis, [], [])
    second_plan = namespace["_chair_build_solid_plan"](doc, "turnout", config, analysis, [], [])
    assert first_plan is second_plan

    normalised = namespace["normalise_chair_analysis_settings"]()
    support_state = {
        "macro_version": "10.2A8A7B15",
        "source_analysis_signature": "same",
        "support_signature": "support",
        "status": namespace["CHAIR_MODEL_SUPPORT_STATUS_CLEAR"],
    }
    layout_state = {
        "macro_version": "10.2A8A7B15",
        "source_analysis_signature": "same",
        "support_signature": "support",
        "layout_signature": "support",
        "status": namespace["CHAIR_2D_LAYOUT_STATUS_VALIDATED"],
    }
    cached_analysis = {
        "geometry_signature": "same",
        "model_timber_support_state": support_state,
        "chair_2d_layout_state": layout_state,
    }
    original_context = namespace["_chair_generation_context"]
    original_objects = namespace["_chair_2d_objects"]
    original_revision_check = namespace["_chair_layout_group_representation_current"]
    namespace["_chair_generation_context"] = lambda *_args, **_kwargs: (
        "turnout", config, cached_analysis, normalised, [], []
    )
    namespace["_chair_2d_objects"] = lambda *_args, **_kwargs: [object()]
    namespace["_chair_layout_group_representation_current"] = lambda *_args, **_kwargs: True
    try:
        reused_support = namespace["prepare_chair_model_support"](doc, "turnout", "TURNOUT-CACHE")
        reused_layout = namespace["build_and_validate_chair_2d_layout"](doc, "turnout", "TURNOUT-CACHE")
    finally:
        namespace["_chair_generation_context"] = original_context
        namespace["_chair_2d_objects"] = original_objects
        namespace["_chair_layout_group_representation_current"] = original_revision_check
    assert reused_support["unchanged_result_reused"] is True
    assert reused_layout["unchanged_result_reused"] is True

    class _Owner:
        def __init__(self):
            self.doc = _Doc()
            self._whole_workflow_benchmark_events = [
                {"stage": "one", "wall_ms": 25.0, "cpu_ms": 20.0, "objects_start": 0, "objects_end": 1},
                {"stage": "two", "wall_ms": 75.0, "cpu_ms": 60.0, "objects_start": 1, "objects_end": 2},
            ]

    report = namespace["_workflow_performance_report"](_Owner())
    assert "Total workflow wall time: 100.0 ms" in report
    assert "Reconciled sum of individual stage actions: 100.0 ms" in report
    assert "Stage percentage checksum: 100.000%" in report
    assert "Largest three performance contributors:" in report

    recompute_measurement = {
        "recompute_count": 0,
        "recompute_ms": 0.0,
    }

    class _RecomputeDoc:
        def recompute(self):
            return "recomputed"

    namespace["_WORKFLOW_ACTIVE_MEASUREMENTS"].append(recompute_measurement)
    try:
        assert namespace["_document_recompute"](_RecomputeDoc()) == "recomputed"
    finally:
        namespace["_WORKFLOW_ACTIVE_MEASUREMENTS"].pop()
    assert recompute_measurement["recompute_count"] == 1
    assert recompute_measurement["recompute_ms"] >= 0.0

    b14_source = B14_PATH.read_text(encoding="utf-8")
    assert _normalised_inherited_module_dump(b14_source) == _normalised_inherited_module_dump(
        source,
        B15_LAYER_MARKER,
    ), "B15 changed the inherited B14 implementation outside its declared compatibility layer"
    _b14_tree, b14_functions = _function_nodes(b14_source)
    preserved = (
        "rea_c10_timber_layout",
        "solve_rea_c10_crossover_geometry",
        "_build_rea_c10_crossover_geometry",
        "analyse_crossover_timber_records",
        "resolve_crossover_b4_timbering",
        "create_crossover_host_integration",
        "build_turnout_host_integration",
    )
    for name in preserved:
        assert _normalised_function_dump(b14_functions[name][-1]) == _normalised_function_dump(functions[name][-1]), name

    print("B15 headless validation passed")


if __name__ == "__main__":
    validate()
