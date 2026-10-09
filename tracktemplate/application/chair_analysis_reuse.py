"""Private eligibility checks for unchanged inherited chair analysis."""

import copy
import math


__all__ = ()


def _json_value(value):
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(item)
                   for key, item in value.items())
    return False


def chair_analysis_reuse_candidate(
    kind, entity_id, config, settings, cached, *, schema_version,
    macro_version, inactive_statuses,
):
    """Reject incomplete or inconsistent persisted results before extraction."""
    if (
        kind not in ("turnout", "crossover")
        or not entity_id
        or not isinstance(config, dict)
        or not isinstance(cached, dict)
        or not settings.get("cache_enabled")
        or config.get(kind + "_id") != entity_id
        or cached.get("entity_kind") != kind
        or cached.get("entity_id") != entity_id
        or type(cached.get("schema_version")) is not int
        or cached["schema_version"] != schema_version
        or config.get("chair_analysis_schema_version") != schema_version
        or cached.get("macro_version") != macro_version
        or not cached.get("status")
        or cached["status"] in inactive_statuses
        or config.get("chair_analysis_status") != cached["status"]
        or cached.get("settings") != settings
        or config.get("chair_analysis_settings") != settings
        or not isinstance(cached.get("geometry_signature"), str)
        or not cached["geometry_signature"]
        or config.get("chair_analysis_signature")
        != cached["geometry_signature"]
        or not isinstance(cached.get("positions"), list)
        or not isinstance(cached.get("findings"), list)
        or not isinstance(cached.get("summary"), dict)
        or not isinstance(cached.get("source_basis"), list)
        or not _json_value(cached)
    ):
        return False
    positions = cached["positions"]
    if cached["summary"].get("chair_position_count") != len(positions):
        return False
    identities = []
    for position in positions:
        if not isinstance(position, dict):
            return False
        for name in (
            "stable_chair_position_identity", "rail_identity", "timber_identity",
        ):
            if not isinstance(position.get(name), str) or not position[name]:
                return False
        if (
            not isinstance(position.get("chair_footprint_parameters"), dict)
            or not isinstance(position.get("protected_features"), list)
            or type(position.get("mandatory")) is not bool
        ):
            return False
        identities.append(position["stable_chair_position_identity"])
    return len(identities) == len(set(identities))


def reused_chair_analysis_result(cached, signature, presentation_current):
    """Return detached logical data; old timings are not current measurements."""
    if not presentation_current or signature != cached["geometry_signature"]:
        return None
    result = copy.deepcopy(cached)
    result["cache_reused"] = True
    result["display_cache_reused"] = True
    result["performance_timings_ms"] = {}
    return result
