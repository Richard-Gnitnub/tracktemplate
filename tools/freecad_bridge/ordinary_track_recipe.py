"""Deterministic Phase 1 oracle for the B14 ordinary two-track fixture.

The Phase 0 base snapshot deliberately remains small because it is the
precondition for the crossover benchmark.  This module adds a deeper,
read-only characterisation of the same document without changing that existing
hash contract.
"""

import hashlib
import json

from tools.freecad_bridge.b14_recipe import freecad_base_snapshot


ORDINARY_TRACK_SCHEMA_VERSION = 1
EXPECTED_ORDINARY_TRACK_SEMANTIC_SHA256 = (
    "b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656"
)

JSON_PROPERTIES = (
    "AssemblyLabelConfigurationJSON",
    "FormationConfigurationJSON",
    "MaterialReportConfigurationJSON",
    "PlatformConfigurationJSON",
    "PlatformConfigurationsJSON",
    "ProductionExportConfigurationJSON",
    "ProductionRecordIndexJSON",
    "RegistrationConfigurationJSON",
    "SectionConfigurationJSON",
    "StraightTrackConfigurationsJSON",
    "TrackConfigurationJSON",
    "TrackTemplateAssemblyConfigurationJSON",
)

PERSISTED_PROPERTY_TYPES = {
    "AssemblyLabelConfigurationJSON": "App::PropertyString",
    "AutomaticEntryStraight": "App::PropertyLength",
    "AutomaticExitStraight": "App::PropertyLength",
    "CircularArcAngle": "App::PropertyAngle",
    "CircularArcLength": "App::PropertyLength",
    "CurveRadius": "App::PropertyLength",
    "EnabledPlatformCount": "App::PropertyInteger",
    "FormationConfigurationJSON": "App::PropertyString",
    "FormationSummary": "App::PropertyString",
    "GeometryMethod": "App::PropertyString",
    "MainTemplateWidth": "App::PropertyLength",
    "MaterialReportConfigurationJSON": "App::PropertyString",
    "OutputBehaviour": "App::PropertyString",
    "ParallelTrackCount": "App::PropertyInteger",
    "PlatformConfigurationJSON": "App::PropertyString",
    "PlatformConfigurationsJSON": "App::PropertyString",
    "PlatformDefinitionCount": "App::PropertyInteger",
    "PlatformSTLPath": "App::PropertyString",
    "PlatformSummary": "App::PropertyString",
    "ProductionExportConfigurationJSON": "App::PropertyString",
    "RegistrationConfigurationJSON": "App::PropertyString",
    "RegistrationSummary": "App::PropertyString",
    "SectionConfigurationJSON": "App::PropertyString",
    "SectionSummary": "App::PropertyString",
    "StraightRouteCount": "App::PropertyInteger",
    "StraightTrackConfigurationsJSON": "App::PropertyString",
    "StraightTrackCount": "App::PropertyInteger",
    "StraightTrackSummary": "App::PropertyString",
    "TemplateThickness": "App::PropertyLength",
    "TotalCentrelineLength": "App::PropertyLength",
    "TotalTurnAngle": "App::PropertyAngle",
    "TrackConfigurationJSON": "App::PropertyString",
    "TrackSummary": "App::PropertyString",
    "TrackTemplateAssemblyConfigurationJSON": "App::PropertyString",
    "TrackTemplateAssemblySummary": "App::PropertyString",
    "TransitionAngleEach": "App::PropertyAngle",
    "TransitionLength": "App::PropertyLength",
    "TurnDirection": "App::PropertyString",
}

SETTINGS_PROPERTY_TYPES = dict(PERSISTED_PROPERTY_TYPES)
SETTINGS_PROPERTY_TYPES["ProductionRecordIndexJSON"] = "App::PropertyString"

IDENTITY_PROPERTIES = (
    "GeneratedBy",
    "GeneratedRole",
    "GeneratorVersion",
    "TemplateSetID",
    "RouteID",
    "RouteName",
    "TrackNumber",
    "TrackName",
    "TravelOrderNumber",
    "PlatformNumber",
    "PlatformName",
    "SectionNumber",
    "FeatureNumber",
    "ExportSubtype",
    "ExportCategory",
    "ProductionRecordID",
    "ProductionRecordIDsJSON",
    "SourceGeneratedRole",
    "SourceSelectionKey",
)

EXPECTED_OBJECT_CONTRACT = {
    "ModelRailwayCurve": ("App::DocumentObjectGroup", "Group"),
    "RailwayCurveSettings": ("Part::Feature", "Settings"),
    "RailwayCurveTemplate": ("Part::Feature", "Template"),
    "RailwayMaterialLengthReport_SET_001": (
        "Spreadsheet::Sheet",
        "MaterialLengthReport",
    ),
    "RailwayProductionSchedule_SET_001": (
        "Spreadsheet::Sheet",
        "ProductionSchedule",
    ),
    "RailwayProductionSource_1": ("Part::Feature", "ProductionSource"),
    "RailwayProductionSources_SET_001": (
        "App::DocumentObjectGroup",
        "ProductionSourceGroup",
    ),
    "RailwayTrackCentreline_00": ("Part::Feature", "Centreline"),
    "RailwayTrackCentreline_01": ("Part::Feature", "Centreline"),
}

EXPECTED_GROUP_MEMBERS = {
    "ModelRailwayCurve": [
        "RailwayCurveSettings",
        "RailwayCurveTemplate",
        "RailwayMaterialLengthReport_SET_001",
        "RailwayProductionSchedule_SET_001",
        "RailwayProductionSources_SET_001",
        "RailwayTrackCentreline_00",
        "RailwayTrackCentreline_01",
    ],
    "RailwayProductionSources_SET_001": ["RailwayProductionSource_1"],
}

EXPECTED_TRACK_CONFIGURATION = [{
    "alignment_mode": "Euler - match spacings",
    "create_template": True,
    "curve_spacing": 55.0,
    "entry_transition_length": 559.410254727028,
    "exit_transition_length": 559.410254727028,
    "finish_spacing": 50.0,
    "name": "Track 2",
    "show_centreline": True,
    "side": "Outside",
    "start_spacing": 50.0,
    "width": 32.0,
}]

EXPECTED_PRODUCTION_RECORDS = [
    (
        "SET-001|CURVE|Template|TrackTemplateCompound|CuttingProfile|T00|P00|S000|F000|track_template_compound_2d",
        "Template",
        "TrackTemplateCompound",
        "CuttingProfile",
        "track_template_compound_2d",
        "hidden-production-source",
        ("dxf", "svg"),
        0,
    ),
    (
        "SET-001|CURVE|Template|TrackTemplateCompound|Solid|T00|P00|S000|F000|track_template_compound_3d",
        "Template",
        "TrackTemplateCompound",
        "Solid",
        "track_template_compound_3d",
        "direct",
        ("stl", "step"),
        0,
    ),
    (
        "SET-001|CURVE|Centreline|TrackCentreline|Engraving|T01|P00|S000|F000|track_centrelines",
        "Centreline",
        "TrackCentreline",
        "Engraving",
        "track_centrelines",
        "direct",
        ("dxf", "svg"),
        1,
    ),
    (
        "SET-001|CURVE|Centreline|TrackCentreline|Engraving|T02|P00|S000|F000|track_centrelines",
        "Centreline",
        "TrackCentreline",
        "Engraving",
        "track_centrelines",
        "direct",
        ("dxf", "svg"),
        2,
    ),
]

BOUNDARY_DATA = {
    "angle_properties": "degrees through App::PropertyAngle",
    "document_frame": "FreeCAD global XY plan; positive Z is template thickness",
    "length_properties": "millimetres through App::PropertyLength",
    "object_identity": "TemplateSetID plus role and role-specific route/track/platform/section/feature fields",
    "ordering": "production records and tracks remain in generated travel/track order; document objects are canonicalised by internal name only for hashing",
    "station_frame": "entry/start origin with chainage increasing in travel order",
    "volatile_normalisation": "generated platform manager_id and created_at values retain their keys but use explicit placeholders",
}


def _rounded(value, places=12):
    rounded = round(float(value), places)
    return 0.0 if rounded == 0.0 else rounded


def _normalise_json_value(value):
    if isinstance(value, dict):
        result = {}
        for key in sorted(value):
            item = value[key]
            if key == "created_at":
                if not str(item or ""):
                    raise ValueError("A persisted created_at value is empty")
                result[key] = "<generated-timestamp>"
            elif key == "manager_id":
                if not str(item or ""):
                    raise ValueError("A persisted manager_id value is empty")
                result[key] = "<generated-manager-id>"
            else:
                result[key] = _normalise_json_value(item)
        return result
    if isinstance(value, list):
        return [_normalise_json_value(item) for item in value]
    if isinstance(value, float):
        return _rounded(value)
    return value


def normalise_persisted_json(value):
    """Parse and canonicalise one persisted JSON payload without reordering lists."""
    try:
        payload = json.loads(value) if isinstance(value, str) else value
    except Exception as error:
        raise ValueError("Invalid persisted JSON: {}".format(error))
    return _normalise_json_value(payload)


def semantic_sha256(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _property_names(obj):
    return set(getattr(obj, "PropertiesList", ()) or ())


def _property_type(obj, name):
    getter = getattr(obj, "getTypeIdOfProperty", None)
    return str(getter(name)) if getter is not None else ""


def _quantity_value(value):
    return _rounded(getattr(value, "Value", value))


def _persisted_value(obj, name, property_type):
    value = getattr(obj, name)
    if name in JSON_PROPERTIES:
        return normalise_persisted_json(str(value))
    if property_type in ("App::PropertyLength", "App::PropertyAngle"):
        return _quantity_value(value)
    if property_type == "App::PropertyInteger":
        return int(value)
    if property_type == "App::PropertyBool":
        return bool(value)
    return str(value)


def persisted_parameter_snapshot(obj, property_types=None):
    """Return the exact B14 parameter/property schema and normalised values."""
    property_types = property_types or PERSISTED_PROPERTY_TYPES
    names = _property_names(obj)
    missing = sorted(set(property_types) - names)
    if missing:
        raise ValueError(
            "{} is missing persisted parameter properties: {}".format(
                getattr(obj, "Name", "<unnamed>"),
                ", ".join(missing),
            )
        )
    actual_types = {
        name: _property_type(obj, name)
        for name in sorted(property_types)
    }
    wrong_types = {
        name: {"actual": actual_types[name], "expected": expected}
        for name, expected in sorted(property_types.items())
        if actual_types[name] != expected
    }
    if wrong_types:
        raise ValueError(
            "{} has unexpected persisted property types: {}".format(
                getattr(obj, "Name", "<unnamed>"),
                wrong_types,
            )
        )
    return {
        "property_types": actual_types,
        "values": {
            name: _persisted_value(obj, name, actual_types[name])
            for name in sorted(property_types)
        },
    }


def shape_summary(shape):
    """Return stable topology, measures and bounds without FreeCAD hash codes."""
    is_null = bool(shape.isNull())
    summary = {
        "is_null": is_null,
        "is_valid": False if is_null else bool(shape.isValid()),
        "shape_type": "" if is_null else str(getattr(shape, "ShapeType", "")),
    }
    if is_null:
        return summary
    for name in ("Solids", "Shells", "Faces", "Wires", "Edges", "Vertexes"):
        summary[name.lower()] = len(getattr(shape, name, ()) or ())
    summary["length_mm"] = _rounded(getattr(shape, "Length", 0.0), 6)
    summary["area_mm2"] = _rounded(getattr(shape, "Area", 0.0), 6)
    summary["volume_mm3"] = _rounded(getattr(shape, "Volume", 0.0), 6)
    bounds = getattr(shape, "BoundBox")
    summary["bounds_mm"] = {
        name: _rounded(getattr(bounds, name), 6)
        for name in (
            "XMin",
            "YMin",
            "ZMin",
            "XMax",
            "YMax",
            "ZMax",
            "XLength",
            "YLength",
            "ZLength",
        )
    }
    return summary


def _identity_value(obj, name):
    value = getattr(obj, name)
    property_type = _property_type(obj, name)
    if name == "ProductionRecordIDsJSON":
        return normalise_persisted_json(str(value))
    if property_type == "App::PropertyInteger":
        return int(value)
    if property_type == "App::PropertyBool":
        return bool(value)
    return str(value)


def _object_snapshot(obj):
    names = _property_names(obj)
    record = {
        "name": str(getattr(obj, "Name", "") or ""),
        "label": str(getattr(obj, "Label", "") or ""),
        "type_id": str(getattr(obj, "TypeId", "") or ""),
        "identity_property_types": {
            name: _property_type(obj, name)
            for name in IDENTITY_PROPERTIES
            if name in names
        },
        "identity": {
            name: _identity_value(obj, name)
            for name in IDENTITY_PROPERTIES
            if name in names
        },
    }
    if "Shape" in names:
        record["shape"] = shape_summary(obj.Shape)
    return record


def _select_role(module, document, role):
    matches = [
        obj for obj in document.Objects
        if str(module.object_string_property(obj, "GeneratedRole", "") or "") == role
        and str(module.object_string_property(obj, "TemplateSetID", "") or "") == "SET-001"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one SET-001 {} object, found {}".format(role, len(matches)))
    return matches[0]


def _group_members(document):
    result = {}
    for obj in document.Objects:
        if str(getattr(obj, "TypeId", "")) != "App::DocumentObjectGroup":
            continue
        result[str(obj.Name)] = sorted(
            str(member.Name) for member in (getattr(obj, "Group", ()) or ())
        )
    return dict(sorted(result.items()))


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


def _validate_semantic(semantic):
    objects = semantic["objects"]
    object_contract = {
        record["name"]: (
            record["type_id"],
            record["identity"].get("GeneratedRole", ""),
        )
        for record in objects
    }
    if object_contract != EXPECTED_OBJECT_CONTRACT:
        raise ValueError("Unexpected ordinary-track object contract: {}".format(object_contract))
    if semantic["groups"] != EXPECTED_GROUP_MEMBERS:
        raise ValueError("Unexpected ordinary-track group membership: {}".format(semantic["groups"]))

    settings = semantic["persistence"]["settings"]
    template = semantic["persistence"]["template"]
    settings_mirror = {
        "property_types": {
            name: settings["property_types"][name]
            for name in sorted(PERSISTED_PROPERTY_TYPES)
        },
        "values": {
            name: settings["values"][name]
            for name in sorted(PERSISTED_PROPERTY_TYPES)
        },
    }
    if settings_mirror != template:
        raise ValueError("B14 settings/template persisted parameter mirrors differ")
    values = settings["values"]
    expected_scalars = {
        "AutomaticEntryStraight": 0.0,
        "AutomaticExitStraight": 0.0,
        "CircularArcAngle": 32.704220486918,
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
        "TotalTurnAngle": 90.0,
        "TransitionAngleEach": 28.647889756541,
        "TransitionLength": 600.0,
        "TurnDirection": "Left",
    }
    differences = {
        name: {"actual": values.get(name), "expected": expected}
        for name, expected in expected_scalars.items()
        if values.get(name) != expected
    }
    if differences:
        raise ValueError("Unexpected ordinary-track persisted values: {}".format(differences))
    if values["TrackConfigurationJSON"] != EXPECTED_TRACK_CONFIGURATION:
        raise ValueError("Unexpected ordinary-track TrackConfigurationJSON")
    if values["StraightTrackConfigurationsJSON"] != []:
        raise ValueError("The ordinary-track fixture unexpectedly enables straight routes")
    platforms = values["PlatformConfigurationsJSON"]
    if not isinstance(platforms, list) or len(platforms) != 1:
        raise ValueError("The ordinary-track fixture must store one disabled platform definition")
    if platforms[0].get("enabled") is not False:
        raise ValueError("The ordinary-track fixture unexpectedly enables its platform")
    if platforms[0].get("manager_id") != "<generated-manager-id>":
        raise ValueError("The platform manager identity was not explicitly normalised")

    record_index = values["ProductionRecordIndexJSON"]
    if record_index.get("created_at") != "<generated-timestamp>":
        raise ValueError("The production timestamp was not explicitly normalised")
    if record_index.get("schema_version") != 2 or record_index.get("template_set_id") != "SET-001":
        raise ValueError("Unexpected ordinary-track production-record index header")
    record_contract = [_record_contract(record) for record in record_index.get("records", [])]
    if record_contract != EXPECTED_PRODUCTION_RECORDS:
        raise ValueError("Unexpected ordinary-track production-record order/schema: {}".format(record_contract))
    record_ids = {record[0] for record in EXPECTED_PRODUCTION_RECORDS}
    object_record_ids = {
        record["identity"]["ProductionRecordID"]
        for record in objects
        if record["identity"].get("ProductionRecordID")
    }
    if object_record_ids != record_ids:
        raise ValueError("Production-record objects do not resolve every indexed identity")


def ordinary_track_snapshot(module, document, enforce_expected_hash=True):
    """Validate and fingerprint B14's fixed ordinary curve/two-track document."""
    base = freecad_base_snapshot(module, document)
    settings_obj = _select_role(module, document, "Settings")
    template_obj = _select_role(module, document, "Template")
    semantic = {
        "schema_version": ORDINARY_TRACK_SCHEMA_VERSION,
        "boundary_data": BOUNDARY_DATA,
        "base": base["semantic"],
        "groups": _group_members(document),
        "objects": sorted(
            (_object_snapshot(obj) for obj in document.Objects),
            key=lambda record: record["name"],
        ),
        "persistence": {
            "settings": persisted_parameter_snapshot(
                settings_obj, SETTINGS_PROPERTY_TYPES
            ),
            "template": persisted_parameter_snapshot(template_obj),
        },
    }
    _validate_semantic(semantic)
    digest = semantic_sha256(semantic)
    if (
        enforce_expected_hash
        and EXPECTED_ORDINARY_TRACK_SEMANTIC_SHA256
        and digest != EXPECTED_ORDINARY_TRACK_SEMANTIC_SHA256
    ):
        raise ValueError(
            "Unexpected ordinary-track semantic SHA-256: {} (expected {})".format(
                digest,
                EXPECTED_ORDINARY_TRACK_SEMANTIC_SHA256,
            )
        )
    return {
        "semantic": semantic,
        "semantic_sha256": digest,
        "base_semantic_sha256": base["semantic_sha256"],
    }
