"""Shared deterministic helpers for Phase 1 chair-analysis oracles."""

import ast
import copy
import hashlib
import json
import types


CORE_KEYS = (
    "entity_id",
    "entity_kind",
    "findings",
    "geometry_signature",
    "model_timber_support_plan",
    "positions",
    "production_geometry_changed",
    "schema_version",
    "settings",
    "source_basis",
    "status",
    "summary",
)

SETTING_ALTERNATIVES = {
    "position_tolerance": 0.25,
    "footprint_clearance": 0.20,
    "timber_end_clearance": 0.75,
    "maximum_advisory_skew_degrees": 6.0,
    "maximum_unsupported_span": 16.0,
    "markers_visible": False,
    "protected_markers_visible": True,
    "footprints_visible": True,
    "cache_enabled": False,
    "model_support_recommendations_enabled": False,
    "model_support_auto_apply_enabled": False,
    "model_support_edge_margin": 0.20,
    "preferred_maximum_model_support_extension_per_side": 2.50,
    "future_chair_embed_depth": 0.25,
    "future_boolean_overlap_allowance": 0.06,
    "future_boolean_fuzzy_tolerance": 0.02,
    "rail_fit_clearance_per_side": 0.05,
    "physical_overlap_area_tolerance": 0.003,
    "physical_rail_interference_clearance": 0.03,
    "physical_solids_visible": True,
    "unresolved_markers_visible": True,
}

SETTING_GROUPS = {
    "presentation_only_excluded": (
        "markers_visible",
        "protected_markers_visible",
        "footprints_visible",
        "physical_solids_visible",
        "unresolved_markers_visible",
    ),
    "execution_policy_excluded": ("cache_enabled",),
    "logical_output_included": (
        "position_tolerance",
        "footprint_clearance",
        "timber_end_clearance",
        "maximum_advisory_skew_degrees",
        "maximum_unsupported_span",
        "model_support_recommendations_enabled",
        "model_support_edge_margin",
        "preferred_maximum_model_support_extension_per_side",
        "future_chair_embed_depth",
        "future_boolean_overlap_allowance",
        "future_boolean_fuzzy_tolerance",
    ),
    "downstream_only_but_included": (
        "model_support_auto_apply_enabled",
        "rail_fit_clearance_per_side",
        "physical_overlap_area_tolerance",
        "physical_rail_interference_clearance",
    ),
    "forced_identity_included": ("schema_version", "rail_profile_id"),
}

DIRECT_CONFIG_FIELD_GROUPS = {
    "signature_included": ("turnout_id", "crossover_id"),
    "omitted_output_affecting": ("template_set_id",),
    "current_core_unused": ("handing",),
}

RAIL_FIELD_GROUPS = {
    "signature_included": ("stable_identity", "points", "rail_role"),
    "omitted_output_affecting": (
        "name",
        "parent_crossover_identity",
        "parent_turnout_identity",
        "source_configuration",
        "supported_feature",
        "turnout_side",
    ),
    "omitted_current_core_unused": ("gauge_face_points", "outer_face_points"),
}

TIMBER_FIELD_GROUPS = {
    "signature_included": (
        "stable_identity",
        "centre",
        "angle_radians",
        "width",
        "length",
        "outline_polygon",
    ),
    "omitted_output_affecting": (
        "angle_degrees",
        "collision_polygon",
        "identifier",
        "length_axis",
        "protected_features",
        "prototype_reference",
        "section",
        "source_configuration",
        "support_requirements",
        "turnout_side",
        "width_axis",
    ),
    "omitted_current_core_unused": (
        "bounding_box",
        "crossover_identity",
        "envelope_kind",
        "envelope_path_station",
        "envelope_timber",
        "extended_inherited_timber",
        "extended_source_timber_identity",
        "far_end_segment",
        "host_chainage",
        "local_rail_heading_degrees",
        "local_rail_heading_radians",
        "longitudinal_reference_axis",
        "longitudinal_station",
        "near_end_segment",
        "parent_turnout_identity",
        "plain_connector_timber",
        "protected_support_region",
        "sequence",
        "shared_long_timber",
        "side_segments",
        "source_timber_identities",
        "support_zone_polygon",
        "supported_feature",
    ),
}


def sha256_file(path):
    digest_value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest_value.update(block)
    return digest_value.hexdigest()


def load_macro_without_launch(path, module_name):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    launch = tree.body[-1] if tree.body else None
    if not (
        isinstance(launch, ast.Expr)
        and isinstance(launch.value, ast.Call)
        and isinstance(launch.value.func, ast.Name)
        and launch.value.func.id == "run_macro"
    ):
        raise AssertionError("Macro launch boundary changed")
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def canonical(value):
    if isinstance(value, dict):
        return {
            str(key): canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [canonical(item) for item in value]
    if isinstance(value, set):
        return sorted(canonical(item) for item in value)
    if isinstance(value, float):
        return round(value, 9)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def digest(value):
    encoded = json.dumps(
        canonical(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def analysis_core(result):
    return {
        key: copy.deepcopy(result[key])
        for key in CORE_KEYS
        if key in result
    }


def deterministic_result(result):
    value = copy.deepcopy(result)
    for key in (
        "performance_timings_ms",
        "cache_reused",
        "display_cache_reused",
        "geometry_signature",
    ):
        value.pop(key, None)
    return value


def output_without_settings(result):
    value = deterministic_result(result)
    value.pop("settings", None)
    return value


def record_schema(records):
    fields = set()
    for record in records:
        fields.update(record)
    return sorted(fields)


def shape_summary(shape):
    box = shape.BoundBox
    return {
        "edges": len(shape.Edges),
        "faces": len(shape.Faces),
        "solids": len(shape.Solids),
        "vertices": len(shape.Vertexes),
        "bounds_mm": [
            round(float(value), 9)
            for value in (
                box.XMin,
                box.YMin,
                box.ZMin,
                box.XMax,
                box.YMax,
                box.ZMax,
            )
        ],
    }
