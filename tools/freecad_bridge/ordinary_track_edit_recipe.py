"""Contracts for Phase 1 B14 plain-line regeneration, history and rollback."""

from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_GROUP_MEMBERS,
    EXPECTED_OBJECT_CONTRACT,
    EXPECTED_PRODUCTION_RECORDS,
    EXPECTED_TRACK_CONFIGURATION,
    PERSISTED_PROPERTY_TYPES,
    normalise_persisted_json,
)


EDIT_RECIPE_SCHEMA_VERSION = 2
RIGHT_HAND_ANGLE_DEGREES = -90.0
INVALID_ANGLE_DEGREES = 0.0
TRANSACTION_FAILURE_ANGLE_DEGREES = -80.0
INJECTED_TRANSACTION_ERROR = (
    "Injected Phase 1 transaction failure after generated-output removal"
)
EXPECTED_RIGHT_HAND_SEMANTIC_SHA256 = (
    "4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4"
)

EXPECTED_DIALOG_TRACK_CONFIGURATION = [dict(EXPECTED_TRACK_CONFIGURATION[0])]
EXPECTED_DIALOG_TRACK_CONFIGURATION[0]["entry_transition_length"] = 559.41
EXPECTED_DIALOG_TRACK_CONFIGURATION[0]["exit_transition_length"] = 559.41


def remembered_input_contract(payload):
    """Return the accepted last-used fields relevant to this bounded recipe."""
    if not isinstance(payload, dict):
        raise ValueError("B14 did not retain an accepted plain-line input payload")
    return {
        "transition_mm": float(payload.get("transition", -1.0)),
        "radius_mm": float(payload.get("radius", -1.0)),
        "angle_degrees": float(payload.get("angle", 9999.0)),
        "main_width_mm": float(payload.get("main_width", -1.0)),
        "track_configs": normalise_persisted_json(payload.get("track_configs", [])),
        "output_mode": str(payload.get("output_mode", "")),
    }


def expected_remembered_input(angle_degrees):
    return {
        "transition_mm": 600.0,
        "radius_mm": 600.0,
        "angle_degrees": float(angle_degrees),
        "main_width_mm": 32.0,
        "track_configs": EXPECTED_DIALOG_TRACK_CONFIGURATION,
        "output_mode": "Replace all existing generated templates",
    }


def _record_contract(record):
    return (
        str(record.get("record_id", "")),
        str(record.get("role", "")),
        str(record.get("subtype", "")),
        str(record.get("category", "")),
        str(record.get("selection_key", "")),
        str(record.get("source_binding_type", "")),
        tuple(record.get("supported_formats", [])),
        int(record.get("track_number", 0)),
    )


def validate_right_hand_snapshot(snapshot, enforce_expected_hash=True):
    """Validate the fixed left-to-right replacement result and return its hash."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("semantic"), dict):
        raise ValueError("Invalid plain-line document snapshot")
    semantic = snapshot["semantic"]
    objects = semantic.get("objects", [])
    object_contract = {
        record.get("name", ""): (
            record.get("type_id", ""),
            record.get("identity", {}).get("GeneratedRole", ""),
        )
        for record in objects
    }
    if object_contract != EXPECTED_OBJECT_CONTRACT:
        raise ValueError("Unexpected right-hand object contract: {}".format(object_contract))
    if semantic.get("groups") != EXPECTED_GROUP_MEMBERS:
        raise ValueError("Unexpected right-hand group membership")

    persistence = semantic.get("persistence", {})
    settings = persistence.get("settings", {})
    template = persistence.get("template", {})
    settings_values = settings.get("values", {})
    template_values = template.get("values", {})
    for name in PERSISTED_PROPERTY_TYPES:
        if settings_values.get(name) != template_values.get(name):
            raise ValueError("Right-hand settings/template mirror differs at {}".format(name))

    expected_values = {
        "AutomaticEntryStraight": 0.0,
        "AutomaticExitStraight": 0.0,
        "CircularArcAngle": -32.704220486918,
        "CircularArcLength": 342.477796076938,
        "CurveRadius": 600.0,
        "EnabledPlatformCount": 0,
        "MainTemplateWidth": 32.0,
        "OutputBehaviour": "Replace all existing generated templates",
        "ParallelTrackCount": 1,
        "PlatformDefinitionCount": 1,
        "StraightRouteCount": 0,
        "StraightTrackCount": 0,
        "TemplateThickness": 1.0,
        "TotalCentrelineLength": 1542.476831002084,
        "TotalTurnAngle": RIGHT_HAND_ANGLE_DEGREES,
        "TransitionAngleEach": -28.647889756541,
        "TransitionLength": 600.0,
        "TurnDirection": "Right",
    }
    differences = {
        name: {"actual": settings_values.get(name), "expected": expected}
        for name, expected in expected_values.items()
        if settings_values.get(name) != expected
    }
    if differences:
        raise ValueError("Unexpected right-hand persisted values: {}".format(differences))
    if settings_values.get("TrackConfigurationJSON") != EXPECTED_TRACK_CONFIGURATION:
        raise ValueError("Right-hand replacement changed the parallel-track configuration")

    record_index = settings_values.get("ProductionRecordIndexJSON", {})
    records = [_record_contract(record) for record in record_index.get("records", [])]
    if records != EXPECTED_PRODUCTION_RECORDS:
        raise ValueError("Right-hand replacement changed production-record order/schema")

    digest = str(snapshot.get("semantic_sha256", ""))
    if (
        enforce_expected_hash
        and EXPECTED_RIGHT_HAND_SEMANTIC_SHA256
        and digest != EXPECTED_RIGHT_HAND_SEMANTIC_SHA256
    ):
        raise ValueError(
            "Unexpected right-hand semantic SHA-256: {} (expected {})".format(
                digest,
                EXPECTED_RIGHT_HAND_SEMANTIC_SHA256,
            )
        )
    return digest


def validate_handing_mirror(left_snapshot, right_snapshot):
    """Prove right-hand state is the XY mirror of the accepted left-hand state."""
    left = left_snapshot.get("semantic", {})
    right = right_snapshot.get("semantic", {})
    if left.get("groups") != right.get("groups"):
        raise ValueError("Left/right plain-line group membership differs")
    left_objects = {record["name"]: record for record in left.get("objects", [])}
    right_objects = {record["name"]: record for record in right.get("objects", [])}
    if set(left_objects) != set(right_objects):
        raise ValueError("Left/right plain-line object names differ")

    mirrored_shapes = []
    for name in sorted(left_objects):
        left_record = left_objects[name]
        right_record = right_objects[name]
        left_static = {
            key: value for key, value in left_record.items() if key != "shape"
        }
        right_static = {
            key: value for key, value in right_record.items() if key != "shape"
        }
        if left_static != right_static:
            raise ValueError("Left/right stable object metadata differs for {}".format(name))
        left_shape = left_record.get("shape")
        right_shape = right_record.get("shape")
        if left_shape is None or right_shape is None:
            if left_shape != right_shape:
                raise ValueError("Left/right shape presence differs for {}".format(name))
            continue
        left_shape_core = {
            key: value for key, value in left_shape.items() if key != "bounds_mm"
        }
        right_shape_core = {
            key: value for key, value in right_shape.items() if key != "bounds_mm"
        }
        if left_shape_core != right_shape_core:
            raise ValueError("Left/right topology or measures differ for {}".format(name))
        left_bounds = left_shape.get("bounds_mm")
        right_bounds = right_shape.get("bounds_mm")
        if left_bounds is None or right_bounds is None:
            if left_bounds != right_bounds:
                raise ValueError("Left/right bounds presence differs for {}".format(name))
            continue
        for key in ("XMin", "XMax", "XLength", "ZMin", "ZMax", "ZLength", "YLength"):
            if left_bounds.get(key) != right_bounds.get(key):
                raise ValueError("Left/right {} bound differs for {}".format(key, name))
        if (
            right_bounds.get("YMin") != -left_bounds.get("YMax")
            or right_bounds.get("YMax") != -left_bounds.get("YMin")
        ):
            raise ValueError("Right-hand Y bounds are not the reflection of {}".format(name))
        mirrored_shapes.append(name)

    expected_changes = {
        "CircularArcAngle",
        "TotalTurnAngle",
        "TransitionAngleEach",
        "TurnDirection",
    }
    changed_by_owner = {}
    for owner in ("settings", "template"):
        left_owner = left.get("persistence", {}).get(owner, {})
        right_owner = right.get("persistence", {}).get(owner, {})
        if left_owner.get("property_types") != right_owner.get("property_types"):
            raise ValueError("Left/right persisted property types differ on {}".format(owner))
        left_values = left_owner.get("values", {})
        right_values = right_owner.get("values", {})
        changed = {
            name for name in set(left_values) | set(right_values)
            if left_values.get(name) != right_values.get(name)
        }
        if changed != expected_changes:
            raise ValueError(
                "Unexpected left/right persisted differences on {}: {}".format(
                    owner, sorted(changed)
                )
            )
        changed_by_owner[owner] = sorted(changed)
    return {
        "mirrored_shape_objects": mirrored_shapes,
        "changed_persisted_fields": changed_by_owner,
    }
