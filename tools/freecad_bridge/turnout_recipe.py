"""Deterministic Phase 1 oracle for one standalone B14 REA C10 turnout.

The recipe anchors placement to the persisted Main Track centreline identity
and host chainage.  It characterises legacy behaviour only: no value captured
here becomes canonical production data or a future chair/turnout definition.
"""

import collections
import json

from tools.freecad_bridge.b14_recipe import (
    DEFAULT_CHAINAGE_MM,
    HOST_A_IDENTITY,
    host_identity,
)
from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_PRODUCTION_RECORDS,
    normalise_persisted_json,
    ordinary_track_document_state,
    semantic_sha256,
    shape_summary,
)


TURNOUT_RECIPE_SCHEMA_VERSION = 1
TURNOUT_ID = "TO-001"
TURNOUT_CHAINAGE_MM = DEFAULT_CHAINAGE_MM
CREATED_HANDING = "Left-hand"
EDITED_HANDING = "Right-hand"
ORIENTATION = "Facing in host travel direction"
TRACK_GAUGE_MM = 16.5
FLANGEWAY_MM = 1.0

# Frozen after two matching qualification runs in separate isolated FreeCAD
# processes.  Every controlled run now rejects semantic drift.
EXPECTED_CREATED_SEMANTIC_SHA256 = (
    "0738c5a639618739c69fcd06553ea0584c5bf8c51253c330e3374f39e437c1cb"
)
EXPECTED_EDITED_SEMANTIC_SHA256 = (
    "46225072b4b56f7f767570c8b438ee0942c239f73f121ce420aa76caed9779f0"
)

BOUNDARY_DATA = {
    "placement": (
        "persisted SET-001 Main Track centreline identity plus switch-toe "
        "chainage; no UI-order or free-XYZ datum"
    ),
    "coordinate_frame": (
        "host travel-order station/normal mapping in FreeCAD global XY plan; "
        "positive Z is retained template thickness"
    ),
    "length_unit": "millimetres",
    "angle_unit": "radians internally; orientation and handing are named enums",
    "identity": (
        "turnout_id is stable; host object, template-set, route and track "
        "identities persist on every turnout object"
    ),
    "ordering": (
        "base production records retain order, followed by turnout solid, "
        "outline, rails, timber outlines, timber labels and construction datums"
    ),
    "source_classification": (
        "legacy B14 behaviour/reference oracle only; not canonical production data"
    ),
}

TURNOUT_PROPERTY_TYPES = {
    "ChairAnalysisSignature": "App::PropertyString",
    "ChairAnalysisStatus": "App::PropertyString",
    "SwitchToeChainage": "App::PropertyLength",
    "TurnoutChairCriticalCount": "App::PropertyInteger",
    "TurnoutChairPositionCount": "App::PropertyInteger",
    "TurnoutConfigurationJSON": "App::PropertyString",
    "TurnoutGeometrySource": "App::PropertyString",
    "TurnoutHanding": "App::PropertyString",
    "TurnoutHostObject": "App::PropertyString",
    "TurnoutID": "App::PropertyString",
    "TurnoutOrientation": "App::PropertyString",
    "TurnoutSize": "App::PropertyString",
    "TurnoutTimberBoundaryStatus": "App::PropertyString",
    "TurnoutTimberCount": "App::PropertyInteger",
    "TurnoutTimberGeometryRevision": "App::PropertyInteger",
    "TurnoutTimberTotalLength": "App::PropertyLength",
}

EXPECTED_TURNOUT_ROLES = (
    "TurnoutGroup",
    "TurnoutSettings",
    "TurnoutTemplate",
    "TurnoutPlanOutline",
    "TurnoutRailGeometry",
    "TurnoutTimberGeometry",
    "TurnoutTimberLabels",
    "TurnoutConstructionMarks",
)

EXPECTED_DOCUMENT_ROLE_COUNTS = {
    "Centreline": 2,
    "Group": 1,
    "MaterialLengthReport": 1,
    "ProductionSchedule": 1,
    "ProductionSource": 1,
    "ProductionSourceGroup": 1,
    "Settings": 1,
    "Template": 1,
    "TurnoutConstructionMarks": 1,
    "TurnoutGroup": 1,
    "TurnoutPlanOutline": 1,
    "TurnoutRailGeometry": 1,
    "TurnoutSettings": 1,
    "TurnoutTemplate": 1,
    "TurnoutTimberGeometry": 1,
    "TurnoutTimberLabels": 1,
}


def _rounded(value, places=12):
    rounded = round(float(value), places)
    return 0.0 if rounded == 0.0 else rounded


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return _rounded(value)
    return value


def select_turnout_host(hosts, read_string, read_integer):
    """Resolve the controlled Main Track host without depending on UI order."""
    identities = [
        host_identity(host, read_string, read_integer)
        for host in list(hosts)
    ]
    matches = [
        index
        for index, identity in enumerate(identities)
        if all(identity.get(key) == value for key, value in HOST_A_IDENTITY.items())
        and (
            identity.get("generated_role")
            in ("Centreline", "StraightTrackCentreline")
            or identity.get("export_subtype") == "TrackCentreline"
        )
    ]
    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one standalone-turnout host {}, found {} among {}".format(
                HOST_A_IDENTITY,
                len(matches),
                identities,
            )
        )
    index = matches[0]
    return {
        "index": index,
        "identity": identities[index],
        "placement_basis": "persisted centreline identity plus host chainage",
    }


def expected_turnout_input(handing):
    if handing not in (CREATED_HANDING, EDITED_HANDING):
        raise ValueError("The standalone-turnout oracle requires a recognised handing")
    return {
        "toe_chainage": TURNOUT_CHAINAGE_MM,
        "handing": handing,
        "orientation": ORIENTATION,
        "track_gauge": TRACK_GAUGE_MM,
        "flangeway": FLANGEWAY_MM,
        "timber_outlines": True,
        "timber_centres": False,
        "timber_numbers": True,
        "timber_length_labels": False,
        "construction_marks": True,
    }


def _property_names(obj):
    return set(getattr(obj, "PropertiesList", ()) or ())


def _property_type(obj, name):
    getter = getattr(obj, "getTypeIdOfProperty", None)
    return str(getter(name)) if getter is not None else ""


def _property_value(obj, name, property_type):
    value = getattr(obj, name)
    if name == "TurnoutConfigurationJSON":
        try:
            return _canonical(json.loads(str(value)))
        except Exception as error:
            raise ValueError("Invalid turnout configuration JSON: {}".format(error))
    if property_type in ("App::PropertyLength", "App::PropertyAngle"):
        return _rounded(getattr(value, "Value", value))
    if property_type == "App::PropertyInteger":
        return int(value)
    if property_type == "App::PropertyBool":
        return bool(value)
    return str(value)


def _turnout_object_snapshot(module, obj):
    names = _property_names(obj)
    missing = sorted(set(TURNOUT_PROPERTY_TYPES) - names)
    if missing:
        raise ValueError(
            "{} is missing turnout properties: {}".format(
                getattr(obj, "Name", "<unnamed>"),
                ", ".join(missing),
            )
        )
    actual_types = {
        name: _property_type(obj, name)
        for name in sorted(TURNOUT_PROPERTY_TYPES)
    }
    wrong = {
        name: {
            "actual": actual_types[name],
            "expected": expected,
        }
        for name, expected in sorted(TURNOUT_PROPERTY_TYPES.items())
        if actual_types[name] != expected
    }
    if wrong:
        raise ValueError(
            "{} has unexpected turnout property types: {}".format(
                getattr(obj, "Name", "<unnamed>"),
                wrong,
            )
        )
    record = {
        "name": str(getattr(obj, "Name", "") or ""),
        "label": str(getattr(obj, "Label", "") or ""),
        "type_id": str(getattr(obj, "TypeId", "") or ""),
        "role": str(module.object_string_property(obj, "GeneratedRole", "") or ""),
        "property_types": actual_types,
        "properties": {
            name: _property_value(obj, name, actual_types[name])
            for name in sorted(TURNOUT_PROPERTY_TYPES)
        },
    }
    if "Shape" in names:
        record["shape"] = shape_summary(obj.Shape)
    if str(getattr(obj, "TypeId", "")) == "App::DocumentObjectGroup":
        record["members"] = sorted(
            str(member.Name) for member in (getattr(obj, "Group", ()) or ())
        )
    return record


def _turnout_objects(module, document):
    matches = [
        obj
        for obj in document.Objects
        if str(module.object_string_property(obj, "TurnoutID", "") or "")
        == TURNOUT_ID
    ]
    return sorted(
        (_turnout_object_snapshot(module, obj) for obj in matches),
        key=lambda record: (record["role"], record["name"]),
    )


def _turnout_catalogue(module, document):
    settings = module.settings_for_template_set(document, "SET-001")
    if settings is None:
        raise ValueError("The turnout oracle cannot find SET-001 settings")
    try:
        payload = json.loads(str(settings.TurnoutConfigurationsJSON))
    except Exception as error:
        raise ValueError("Invalid turnout catalogue JSON: {}".format(error))
    if not isinstance(payload, list):
        raise ValueError("The turnout catalogue is not a list")
    return _canonical(payload)


def turnout_document_snapshot(module, document):
    """Capture the standalone turnout plus complete copied-document state."""
    host_selection = select_turnout_host(
        module.turnout_host_objects(document),
        module.object_string_property,
        module._integer_object_property,
    )
    state = ordinary_track_document_state(module, document)
    semantic = {
        "schema_version": TURNOUT_RECIPE_SCHEMA_VERSION,
        "boundary_data": BOUNDARY_DATA,
        "host": host_selection,
        "turnout_catalogue": _turnout_catalogue(module, document),
        "turnout_objects": _turnout_objects(module, document),
        "document": state,
    }
    return {
        "semantic": semantic,
        "semantic_sha256": semantic_sha256(semantic),
    }


def _production_record_contract(record):
    return (
        str(record.get("role", "")),
        str(record.get("subtype", "")),
        str(record.get("category", "")),
        str(record.get("selection_key", "")),
        str(record.get("source_binding_type", "")),
        tuple(record.get("supported_formats", [])),
        int(record.get("track_number", 0)),
        int(record.get("feature_number", 0)),
    )


def _expected_turnout_record_contract():
    return [
        (
            "TurnoutTemplate", "TrackTemplateTurnout", "Solid",
            "track_template_compound_3d", "direct", ("stl", "step"), 1, 1,
        ),
        (
            "TurnoutPlanOutline", "TrackTemplateTurnout", "CuttingProfile",
            "track_template_compound_2d", "direct", ("dxf", "svg"), 1, 1,
        ),
        (
            "TurnoutRailGeometry", "TurnoutRailGeometry", "Engraving",
            "other_engraving", "direct", ("dxf", "svg"), 1, 1,
        ),
        (
            "TurnoutTimberGeometry", "TurnoutTimberGeometry", "Engraving",
            "other_engraving", "direct", ("dxf", "svg"), 1, 1,
        ),
        (
            "TurnoutTimberLabels", "TurnoutTimberLabels", "Engraving",
            "other_engraving", "direct", ("dxf", "svg"), 1, 1,
        ),
        (
            "TurnoutConstructionMarks", "TurnoutConstructionMarks", "Engraving",
            "other_engraving", "direct", ("dxf", "svg"), 1, 1,
        ),
    ]


def validate_turnout_snapshot(snapshot, expected_handing, expected_hash=None):
    """Validate stable identity, geometry, persistence and production order."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("semantic"), dict):
        raise ValueError("Invalid standalone-turnout snapshot")
    semantic = snapshot["semantic"]
    if semantic.get("boundary_data") != BOUNDARY_DATA:
        raise ValueError("Unexpected standalone-turnout boundary data")
    host = semantic.get("host", {})
    if any(
        host.get("identity", {}).get(key) != value
        for key, value in HOST_A_IDENTITY.items()
    ):
        raise ValueError("The turnout is not anchored to the expected host identity")

    catalogue = semantic.get("turnout_catalogue", [])
    if len(catalogue) != 1 or catalogue[0].get("turnout_id") != TURNOUT_ID:
        raise ValueError("The standalone-turnout catalogue is incomplete")
    config = catalogue[0]
    expected_inputs = expected_turnout_input(expected_handing)
    input_projection = {key: config.get(key) for key in expected_inputs}
    if input_projection != expected_inputs:
        raise ValueError(
            "Unexpected standalone-turnout inputs: {}".format(input_projection)
        )
    expected_identity = {
        "schema_version": 1,
        "macro_version": "10.2A8A7B14",
        "turnout_id": TURNOUT_ID,
        "size": "REA C10 natural",
        "template_set_id": "SET-001",
        "route_id": "",
        "route_name": "",
        "track_number": 1,
        "track_name": "Main Track",
        "template_width": 32.0,
        "template_thickness": 1.0,
    }
    actual_identity = {key: config.get(key) for key in expected_identity}
    if actual_identity != expected_identity:
        raise ValueError("Unexpected standalone-turnout identity/configuration")
    interval = config.get("host_station_interval", [])
    if len(interval) != 2 or not (
        interval[0] <= TURNOUT_CHAINAGE_MM <= interval[1]
    ):
        raise ValueError("The turnout host-station interval is invalid")
    if config.get("timber_count", 0) <= 0:
        raise ValueError("The standalone turnout has no REA timber records")
    if config.get("timber_geometry_revision", 0) <= 0:
        raise ValueError("The standalone turnout timber revision is missing")

    turnout_objects = semantic.get("turnout_objects", [])
    roles = [record.get("role") for record in turnout_objects]
    if roles != sorted(EXPECTED_TURNOUT_ROLES):
        raise ValueError("Unexpected standalone-turnout object roles: {}".format(roles))
    object_configs = {
        semantic_sha256(record["properties"]["TurnoutConfigurationJSON"])
        for record in turnout_objects
    }
    if object_configs != {semantic_sha256(config)}:
        raise ValueError("Turnout objects do not share the catalogue configuration")
    for record in turnout_objects:
        properties = record["properties"]
        if properties["TurnoutID"] != TURNOUT_ID:
            raise ValueError("A turnout object lost its stable identifier")
        if properties["TurnoutHanding"] != expected_handing:
            raise ValueError("A turnout object retained the wrong handing")
        if properties["SwitchToeChainage"] != TURNOUT_CHAINAGE_MM:
            raise ValueError("A turnout object retained the wrong toe chainage")
        shape = record.get("shape")
        if record["role"] == "TurnoutSettings":
            if shape is None or not shape.get("is_null", False):
                raise ValueError("Turnout settings unexpectedly contain geometry")
        elif shape is not None and (
            shape.get("is_null", True) or not shape.get("is_valid", False)
        ):
            raise ValueError("A standalone-turnout object has invalid geometry")
    group = next(
        record for record in turnout_objects if record["role"] == "TurnoutGroup"
    )
    expected_member_names = sorted(
        record["name"]
        for record in turnout_objects
        if record["role"] != "TurnoutGroup"
    )
    if group.get("members") != expected_member_names:
        raise ValueError("The turnout group membership is incomplete")

    document = semantic.get("document", {})
    role_counts = collections.Counter(
        record.get("identity", {}).get("GeneratedRole", "")
        for record in document.get("objects", [])
        if record.get("identity", {}).get("GeneratedRole", "")
    )
    if dict(sorted(role_counts.items())) != EXPECTED_DOCUMENT_ROLE_COUNTS:
        raise ValueError(
            "Unexpected standalone-turnout document roles: {}".format(
                dict(role_counts)
            )
        )
    if len(document.get("objects", [])) != 17:
        raise ValueError("The standalone-turnout document does not contain 17 objects")

    settings_values = (
        document.get("persistence", {})
        .get("settings", {})
        .get("values", {})
    )
    record_index = settings_values.get("ProductionRecordIndexJSON", {})
    records = list(record_index.get("records", []))
    if len(records) != 10:
        raise ValueError("The standalone-turnout catalogue does not contain 10 records")
    base_contract = [
        (
            str(record.get("record_id", "")),
            str(record.get("role", "")),
            str(record.get("subtype", "")),
            str(record.get("category", "")),
            str(record.get("selection_key", "")),
            str(record.get("source_binding_type", "")),
            tuple(record.get("supported_formats", [])),
            int(record.get("track_number", 0)),
        )
        for record in records[:4]
    ]
    if base_contract != EXPECTED_PRODUCTION_RECORDS:
        raise ValueError("The standalone turnout changed base production order")
    turnout_contract = [_production_record_contract(record) for record in records[4:]]
    if turnout_contract != _expected_turnout_record_contract():
        raise ValueError(
            "Unexpected standalone-turnout production order: {}".format(
                turnout_contract
            )
        )

    digest = semantic_sha256(semantic)
    if snapshot.get("semantic_sha256") != digest:
        raise ValueError("The standalone-turnout semantic hash is inconsistent")
    if expected_hash and digest != expected_hash:
        raise ValueError(
            "Unexpected standalone-turnout semantic SHA-256: {} (expected {})".format(
                digest,
                expected_hash,
            )
        )
    return digest


def plain_line_geometry_contract(document_state):
    """Return the immutable curve/template geometry around the turnout module."""
    selected = []
    for record in document_state.get("objects", []):
        role = record.get("identity", {}).get("GeneratedRole", "")
        if role not in ("Template", "Centreline", "ProductionSource"):
            continue
        selected.append({
            "name": record.get("name"),
            "label": record.get("label"),
            "type_id": record.get("type_id"),
            "identity": {
                key: value
                for key, value in record.get("identity", {}).items()
                if key not in ("ProductionRecordID", "ProductionRecordIDsJSON")
            },
            "shape": record.get("shape"),
        })
    return sorted(selected, key=lambda record: record["name"])


def normalised_turnout_catalogue(module, document):
    """Public recipe helper for history and persistence comparisons."""
    return normalise_persisted_json(_turnout_catalogue(module, document))
