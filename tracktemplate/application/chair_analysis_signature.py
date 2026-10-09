"""Private signature for the inherited logical chair-analysis inputs."""

import hashlib
import json


__all__ = ()

# Final B15 generation, assignment, validation and emitted source metadata.
# Keep record order and existing downstream-setting invalidation unchanged.
_RAIL_FIELDS = (
    "stable_identity", "points", "rail_role", "name",
    "parent_turnout_identity", "parent_crossover_identity",
    "supported_feature", "source_configuration", "turnout_side",
)
_TIMBER_FIELDS = (
    "stable_identity", "identifier", "prototype_reference", "centre",
    "angle_radians", "angle_degrees", "width", "length",
    "outline_polygon", "collision_polygon", "length_axis", "width_axis",
    "protected_features", "section", "source_configuration",
    "support_requirements", "turnout_side",
)
_EXCLUDED_SETTINGS = (
    "markers_visible", "protected_markers_visible", "footprints_visible",
    "physical_solids_visible", "unresolved_markers_visible", "cache_enabled",
)


def chair_analysis_signature(
    entity_kind, config, settings, rail_records, timber_records, *,
    schema_version,
):
    """Hash exact neutral inputs with settings already normalised by the host.

    No input is mutated. Unsupported values and nonfinite numbers fail
    before document mutation. The discriminator invalidates old cache keys
    without changing the inherited stored analysis schema.
    """
    payload = {
        "signature_format": "tracktemplate:chair-analysis-inputs:1",
        "schema_version": schema_version,
        "entity_kind": str(entity_kind),
        "config": {
            key: config[key]
            for key in (
                "turnout_id", "crossover_id", "template_set_id", "handing",
            )
            if key in config
        },
        "settings": {
            key: value for key, value in settings.items()
            if key not in _EXCLUDED_SETTINGS
        },
        "rails": [
            {key: item[key] for key in _RAIL_FIELDS if key in item}
            for item in rail_records
        ],
        "timbers": [
            {key: item[key] for key in _TIMBER_FIELDS if key in item}
            for item in timber_records
        ],
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
