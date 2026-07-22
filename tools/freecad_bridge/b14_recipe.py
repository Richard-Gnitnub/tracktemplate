"""Stable identities and inputs for the controlled B14 crossover recipe."""

import collections
import hashlib
import json

DEFAULT_CHAINAGE_MM = 746.298
DEFAULT_STAGES = (
    "geometry",
    "timber",
    "chairs",
    "support",
    "layout",
    "integration",
    "solids",
)
EXPECTED_BASE_OBJECT_COUNT = 9
EXPECTED_BASE_ROLE_COUNTS = {
    "Centreline": 2,
    "Group": 1,
    "MaterialLengthReport": 1,
    "ProductionSchedule": 1,
    "ProductionSource": 1,
    "ProductionSourceGroup": 1,
    "Settings": 1,
    "Template": 1,
}
EXPECTED_BASE_TYPE_COUNTS = {
    "App::DocumentObjectGroup": 2,
    "Part::Feature": 5,
    "Spreadsheet::Sheet": 2,
}
EXPECTED_BASE_MACRO_VERSION = "10.2A8A7B14"
EXPECTED_BASE_CURVE = {
    "transition_length_mm": 600.0,
    "radius_mm": 600.0,
    "turn_angle_degrees": 90.0,
    "main_template_width_mm": 32.0,
    "track_configs": [{
        "name": "Track 2",
        "side": "Outside",
        "alignment_mode": "Euler - match spacings",
        "start_spacing": 50.0,
        "curve_spacing": 55.0,
        "finish_spacing": 50.0,
        "entry_transition_length": 559.4102547270278,
        "exit_transition_length": 559.4102547270278,
        "width": 32.0,
        "create_template": True,
        "show_centreline": True,
    }],
}
EXPECTED_BASE_HOST_LENGTHS_MM = {
    "A": 1542.475839,
    "B": 1627.287516,
}

HOST_A_IDENTITY = {
    "template_set_id": "SET-001",
    "track_number": 1,
    "track_name": "Main Track",
}
HOST_B_IDENTITY = {
    "template_set_id": "SET-001",
    "track_number": 2,
    "track_name": "Track 2",
}


def host_identity(host, read_string, read_integer):
    """Return the persisted domain identity used to select a host centreline."""
    return {
        "template_set_id": str(read_string(host, "TemplateSetID", "") or ""),
        "route_id": str(read_string(host, "RouteID", "") or ""),
        "track_number": int(read_integer(host, "TrackNumber", 0) or 0),
        "track_name": str(read_string(host, "TrackName", "") or ""),
        "generated_role": str(read_string(host, "GeneratedRole", "") or ""),
        "export_subtype": str(read_string(host, "ExportSubtype", "") or ""),
        "object_name": str(getattr(host, "Name", "") or ""),
    }


def _is_centreline(identity):
    return (
        identity["generated_role"] in ("Centreline", "StraightTrackCentreline")
        or identity["export_subtype"] == "TrackCentreline"
    )


def _matches(identity, expected):
    return _is_centreline(identity) and all(
        identity[key] == value for key, value in expected.items()
    )


def select_crossover_hosts(hosts, read_string, read_integer):
    """Resolve the two recipe hosts without depending on UI or object ordering."""
    identities = [
        host_identity(host, read_string, read_integer)
        for host in list(hosts)
    ]

    def unique_match(label, expected):
        matches = [
            index for index, identity in enumerate(identities)
            if _matches(identity, expected)
        ]
        if len(matches) != 1:
            raise ValueError(
                "Expected exactly one {} centreline {}, found {} among {}".format(
                    label,
                    expected,
                    len(matches),
                    identities,
                )
            )
        return matches[0]

    index_a = unique_match("Host A", HOST_A_IDENTITY)
    index_b = unique_match("Host B", HOST_B_IDENTITY)
    if index_a == index_b:
        raise ValueError("The B14 crossover recipe resolved both hosts to one centreline")
    return {
        "a": index_a,
        "b": index_b,
        "host_a_identity": identities[index_a],
        "host_b_identity": identities[index_b],
    }


def freecad_base_snapshot(
    module,
    document,
    expected_macro_version=EXPECTED_BASE_MACRO_VERSION,
):
    """Validate and fingerprint the generated nine-object B14 starting state."""
    objects = list(document.Objects)
    role_counts = collections.Counter()
    type_counts = collections.Counter()
    managed_special_trackwork = []
    for obj in objects:
        role = str(module.object_string_property(obj, "GeneratedRole", "") or "")
        if role:
            role_counts[role] += 1
        type_counts[str(getattr(obj, "TypeId", "Unknown"))] += 1
        turnout_id = str(
            module.object_string_property(obj, module.TURNOUT_ID_PROPERTY, "") or ""
        )
        crossover_id = str(
            module.object_string_property(obj, module.CROSSOVER_ID_PROPERTY, "") or ""
        )
        if turnout_id or crossover_id:
            managed_special_trackwork.append({
                "object_name": str(getattr(obj, "Name", "") or ""),
                "turnout_id": turnout_id,
                "crossover_id": crossover_id,
            })

    if len(objects) != EXPECTED_BASE_OBJECT_COUNT:
        raise ValueError(
            "Expected {} base objects, found {}".format(
                EXPECTED_BASE_OBJECT_COUNT,
                len(objects),
            )
        )
    if dict(sorted(role_counts.items())) != EXPECTED_BASE_ROLE_COUNTS:
        raise ValueError("Unexpected base generated roles: {}".format(dict(role_counts)))
    if dict(sorted(type_counts.items())) != EXPECTED_BASE_TYPE_COUNTS:
        raise ValueError("Unexpected base object types: {}".format(dict(type_counts)))
    if managed_special_trackwork:
        raise ValueError(
            "The benchmark base already contains managed special trackwork: {}".format(
                managed_special_trackwork
            )
        )

    hosts = module.turnout_host_objects(document)
    selection = select_crossover_hosts(
        hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    host_records = []
    for key in ("a", "b"):
        index = selection[key]
        identity = selection["host_{}_identity".format(key)]
        alignment = module.turnout_host_alignment(hosts[index])
        host_records.append({
            "side": key.upper(),
            "identity": identity,
            "length_mm": round(float(alignment["total"]), 6),
        })

    for record in host_records:
        expected_length = EXPECTED_BASE_HOST_LENGTHS_MM[record["side"]]
        if abs(record["length_mm"] - expected_length) > 1.0e-6:
            raise ValueError(
                "Unexpected Host {} centreline length: {} mm (expected {} mm)".format(
                    record["side"],
                    record["length_mm"],
                    expected_length,
                )
            )

    settings = module.settings_for_template_set(document, "SET-001")
    if settings is None:
        raise ValueError("The benchmark base has no SET-001 settings object")
    try:
        track_configs = json.loads(
            module.object_string_property(settings, "TrackConfigurationJSON", "[]")
        )
    except Exception as error:
        raise ValueError("Invalid base TrackConfigurationJSON: {}".format(error))

    curve = {
        "transition_length_mm": float(
            module.quantity_value(settings, "TransitionLength", -1.0)
        ),
        "radius_mm": float(module.quantity_value(settings, "CurveRadius", -1.0)),
        "turn_angle_degrees": float(
            module.quantity_value(settings, "TotalTurnAngle", -1.0)
        ),
        "main_template_width_mm": float(
            module.quantity_value(settings, "MainTemplateWidth", -1.0)
        ),
        "track_configs": track_configs,
    }
    macro_version = str(module.MACRO_VERSION_NUMBER)
    expected_macro_version = str(expected_macro_version)
    if macro_version != expected_macro_version:
        raise ValueError(
            "Unexpected base macro version: {} (expected {})".format(
                macro_version,
                expected_macro_version,
            )
        )
    if curve != EXPECTED_BASE_CURVE:
        raise ValueError(
            "Unexpected B14 base curve contract: {}".format(curve)
        )

    semantic = {
        "macro_version": macro_version,
        "object_count": len(objects),
        "role_counts": dict(sorted(role_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
        "hosts": host_records,
        "curve": curve,
    }
    encoded = json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "semantic": semantic,
        "semantic_sha256": hashlib.sha256(encoded).hexdigest(),
        "selected_host_indices": {"a": selection["a"], "b": selection["b"]},
    }
