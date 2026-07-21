"""Reusable semantic helpers for the fixed Phase 1 crossover-timber oracle."""

import collections
import hashlib
import json

from tools.freecad_bridge import b14_recipe


VOLATILE_RESULT_KEYS = {
    "cache_reused",
    "metadata_update_statistics",
    "performance_timings_ms",
}


def digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable(value):
    """Remove measured/run-local result fields while retaining domain data."""
    if isinstance(value, dict):
        return {
            str(key): stable(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_RESULT_KEYS
        }
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def shape_summary(shape):
    if shape is None or shape.isNull():
        return None
    box = shape.BoundBox
    return {
        "edges": len(shape.Edges),
        "faces": len(shape.Faces),
        "solids": len(shape.Solids),
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


def object_record(module, obj):
    return {
        "name": str(obj.Name),
        "type_id": str(obj.TypeId),
        "generated_role": str(
            module.object_string_property(obj, "GeneratedRole", "") or ""
        ),
        "crossover_id": str(
            module.object_string_property(
                obj, module.CROSSOVER_ID_PROPERTY, ""
            )
            or ""
        ),
        "shape": shape_summary(getattr(obj, "Shape", None)),
    }


def object_map(module, document):
    return {
        str(obj.Name): object_record(module, obj)
        for obj in document.Objects
    }


def role_counts(module, document):
    return dict(sorted(collections.Counter(
        str(module.object_string_property(obj, "GeneratedRole", "") or "")
        for obj in document.Objects
    ).items()))


def document_snapshot(module, document, crossover_id):
    """Return a timing-free semantic snapshot suitable for relative equality."""
    return {
        "config": stable(module.crossover_config_by_id(document, crossover_id)),
        "objects": object_map(module, document),
        "role_counts": role_counts(module, document),
    }


def result_snapshot(module, result):
    records = list(result.get("resolved_timbers") or [])
    ordered = sorted(
        records, key=lambda item: str(item.get("stable_identity") or "")
    )
    envelope_kinds = collections.Counter(
        str(item.get("envelope_kind") or "") for item in records
    )
    turnout_sides = collections.Counter(
        str(item.get("turnout_side") or "") for item in records
    )
    count_fields = (
        "effective_timber_count",
        "shared_timber_count",
        "plain_connector_timber_count",
        "interlaced_pair_count",
        "shoved_timber_count",
        "unresolved_count",
        "remaining_production_conflicts",
        "remaining_production_critical_conflicts",
    )
    counts = {
        field: int(result.get(field) or 0)
        for field in count_fields
    }
    counts["timber_resolution_complete"] = bool(
        result.get("timber_resolution_complete")
    )
    return {
        "status": str(result.get("status") or ""),
        "counts": counts,
        "record_turnout_sides": dict(sorted(turnout_sides.items())),
        "record_envelope_kinds": dict(sorted(envelope_kinds.items())),
        "record_identity_sha256": digest([
            str(item.get("stable_identity") or "") for item in records
        ]),
        "stable_record_sha256": digest([
            module._b4_stable_record(item) for item in ordered
        ]),
        "resolution_signature": str(
            result.get("resolution_signature") or ""
        ),
    }


def create_controlled_crossover(module, document, chainage_mm):
    hosts = module.turnout_host_objects(document)
    selected = b14_recipe.select_crossover_hosts(
        hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    host_a = hosts[selected["a"]]
    host_b = hosts[selected["b"]]
    solved = module.solve_rea_c10_crossover_geometry(
        document, host_a, host_b, float(chainage_mm)
    )
    config = module.create_rea_c10_crossover(
        document,
        host_a,
        host_b,
        float(chainage_mm),
        pre_solved=solved,
    )
    return config, selected
