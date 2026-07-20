"""Deterministic Phase 1 oracle for B14 connected straights and stationing.

The recipe deliberately uses B14's controlled curve-entrance/curve-exit pair
on the fixed two-track curve fixture.  It records the analytical travel-order
station contract alongside the complete generated FreeCAD document contract.
"""

import json
import math

from tools.freecad_bridge.ordinary_track_recipe import (
    EXPECTED_PRODUCTION_RECORDS,
    normalise_persisted_json,
    ordinary_track_document_snapshot,
    semantic_sha256,
)


STRAIGHT_STATION_SCHEMA_VERSION = 1
CREATED_LENGTHS_MM = (600.0, 600.0)
EDITED_LENGTHS_MM = (750.0, 450.0)
MANAGER_IDS = (
    "phase1-curve-entrance",
    "phase1-curve-exit",
)
ROUTE_IDS = tuple("straight-{}".format(value) for value in MANAGER_IDS)
ROUTE_NAMES = ("Curve Entrance Straight", "Curve Exit Straight")
CONNECTION_MODES = ("Curve entrance", "Curve exit")
CURVE_TRACK_NAMES = ("Main Track", "Track 2")

# Frozen from the isolated FreeCAD 1.1.1 controlled series recorded in the
# Phase 1 straight/station benchmark note.
EXPECTED_CREATED_SEMANTIC_SHA256 = (
    "f5bf185baf2c61fbdf79c483b96ccf53e3a6206320e50087568e457022958a6c"
)
EXPECTED_EDITED_SEMANTIC_SHA256 = (
    "430d5f134e20789ee22c7f5549b64611a067646f1d24e038d4fbbc473d6b7666"
)

BOUNDARY_DATA = {
    "coordinate_frame": "FreeCAD global XY plan; positive Z is template thickness",
    "length_unit": "millimetres",
    "angle_unit": "radians in analytical records; degrees in persisted FreeCAD angle properties",
    "station_direction": "entrance station 0 is the remote end and station L is the curve join; exit station 0 is the curve join and station L is the remote end",
    "identity": "manager_id persists in input configuration; route_id is straight-<manager_id>; track_number is one-based in inherited curve-track order",
    "ordering": "entrance route, exit route; within each route Main Track then Track 2; production records remain catalogue order",
    "join_tolerance_mm": 1.0e-7,
    "heading_tolerance_rad": 1.0e-10,
}

EXPECTED_ROLE_COUNTS = {
    "Centreline": 2,
    "Group": 3,
    "MaterialLengthReport": 1,
    "ProductionSchedule": 1,
    "ProductionSource": 5,
    "ProductionSourceGroup": 1,
    "Settings": 1,
    "StraightTrackCentreline": 4,
    "StraightTrackTemplate": 4,
    "Template": 1,
}


def _rounded(value, places=12):
    rounded = round(float(value), places)
    return 0.0 if rounded == 0.0 else rounded


def _canonical(value):
    """Canonicalise recipe data while retaining deterministic manager IDs."""
    if isinstance(value, dict):
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return _rounded(value)
    return value


def expected_pair_configs(lengths=CREATED_LENGTHS_MM):
    """Return the exact accepted Straight Track Manager pair."""
    lengths = tuple(float(value) for value in lengths)
    if len(lengths) != 2 or any(value <= 0.0 for value in lengths):
        raise ValueError("The connected-pair oracle requires two positive lengths")
    result = []
    for index in range(2):
        result.append({
            "manager_id": MANAGER_IDS[index],
            "enabled": True,
            "name": ROUTE_NAMES[index],
            "connection_mode": CONNECTION_MODES[index],
            "length": lengths[index],
            "direction": "Forward",
            "track_count": 2,
            "track_spacing": 50.0,
            "parallel_side": "Left of travel",
            "template_width": 32.0,
            "template_thickness": 1.0,
            "start_x": 0.0,
            "start_y": 0.0,
            "rotation_degrees": 0.0,
            "create_template": True,
            "show_centreline": True,
        })
    return result


def remembered_straight_contract(payload):
    """Return the non-volatile last-used input fields owned by this recipe."""
    if not isinstance(payload, dict):
        raise ValueError("B14 did not retain an accepted straight/station input payload")
    return {
        "straight_configs": _canonical(payload.get("straight_configs", [])),
        "selected_straight_index": int(payload.get("selected_straight_index", -1)),
        "output_mode": str(payload.get("output_mode", "")),
    }


def expected_remembered_straight_contract(lengths):
    return {
        "straight_configs": _canonical(expected_pair_configs(lengths)),
        "selected_straight_index": 0,
        "output_mode": "Replace all existing generated templates",
    }


def _point_record(point):
    return [_rounded(point.x), _rounded(point.y)]


def _station_sample(module, data, station):
    point, heading = module.interpolate_alignment_station(data, station)
    return {
        "station_mm": _rounded(station),
        "point_xy_mm": _point_record(point),
        "heading_rad": _rounded(heading),
    }


def straight_route_analysis_snapshot(module, routes, curve_alignments):
    """Capture connected-route geometry, joins and travel-order stationing."""
    routes = list(routes or [])
    curve_alignments = list(curve_alignments or [])
    module.validate_connected_straight_routes(routes, curve_alignments)
    curve_records = []
    for index, curve in enumerate(curve_alignments):
        points = list(curve.get("points", []))
        headings = list(curve.get("headings", []))
        if len(points) < 2 or len(points) != len(headings):
            raise ValueError("The straight/station oracle received an incomplete curve track")
        curve_records.append({
            "track_number": index + 1,
            "name": str(curve.get("name", "")),
            "width_mm": _rounded(curve.get("width", 0.0)),
            "entry_point_xy_mm": _point_record(points[0]),
            "entry_heading_rad": _rounded(headings[0]),
            "exit_point_xy_mm": _point_record(points[-1]),
            "exit_heading_rad": _rounded(headings[-1]),
        })

    route_records = []
    for route in routes:
        mode = str(route.get("connection_mode", ""))
        alignment_records = []
        for index, alignment in enumerate(route.get("alignments", [])):
            if index >= len(curve_alignments):
                raise ValueError("A connected straight has no corresponding curve track")
            curve = curve_alignments[index]
            straight_points = list(alignment.get("points", []))
            straight_headings = list(alignment.get("headings", []))
            curve_points = list(curve.get("points", []))
            curve_headings = list(curve.get("headings", []))
            if len(straight_points) != 2 or len(straight_headings) != 2:
                raise ValueError("A connected straight must contain exactly two station points")

            if mode == "Curve entrance":
                join_point = straight_points[-1]
                join_heading = straight_headings[-1]
                curve_point = curve_points[0]
                curve_heading = curve_headings[0]
                remote_point = straight_points[0]
            elif mode == "Curve exit":
                join_point = straight_points[0]
                join_heading = straight_headings[0]
                curve_point = curve_points[-1]
                curve_heading = curve_headings[-1]
                remote_point = straight_points[-1]
            else:
                raise ValueError("The bounded straight/station oracle accepts connected routes only")

            data = module.alignment_station_data(alignment)
            total = float(data["total"])
            heading_delta = abs(
                math.atan2(
                    math.sin(join_heading - curve_heading),
                    math.cos(join_heading - curve_heading),
                )
            )
            remote_projection = (
                ((remote_point.x - curve_point.x) * math.cos(curve_heading))
                + ((remote_point.y - curve_point.y) * math.sin(curve_heading))
            )
            alignment_records.append({
                "route_id": str(alignment.get("route_id", "")),
                "route_name": str(alignment.get("route_name", "")),
                "track_number": int(alignment.get("track_number", 0)),
                "name": str(alignment.get("name", "")),
                "source_alignment_name": str(
                    alignment.get("source_alignment_name", "")
                ),
                "connection_mode": str(alignment.get("connection_mode", "")),
                "width_mm": _rounded(alignment.get("width", 0.0)),
                "template_thickness_mm": _rounded(
                    alignment.get("template_thickness", 0.0)
                ),
                "create_template": bool(alignment.get("create_template", False)),
                "show_centreline": bool(alignment.get("show_centreline", False)),
                "points_xy_mm": [_point_record(point) for point in straight_points],
                "headings_rad": [_rounded(value) for value in straight_headings],
                "station": {
                    "stations_mm": [_rounded(value) for value in data["stations"]],
                    "total_mm": _rounded(total),
                    "core_start_mm": _rounded(data["core_start"]),
                    "core_end_mm": _rounded(data["core_end"]),
                    "samples": [
                        _station_sample(module, data, station)
                        for station in (0.0, total * 0.5, total)
                    ],
                },
                "join": {
                    "straight_point_xy_mm": _point_record(join_point),
                    "curve_point_xy_mm": _point_record(curve_point),
                    "position_error_mm": _rounded(
                        math.hypot(
                            join_point.x - curve_point.x,
                            join_point.y - curve_point.y,
                        )
                    ),
                    "straight_heading_rad": _rounded(join_heading),
                    "curve_heading_rad": _rounded(curve_heading),
                    "heading_error_rad": _rounded(heading_delta),
                    "remote_travel_projection_mm": _rounded(remote_projection),
                },
            })
        route_records.append({
            "route_id": str(route.get("route_id", "")),
            "name": str(route.get("name", "")),
            "connection_mode": mode,
            "length_mm": _rounded(route.get("length", 0.0)),
            "config": _canonical(route.get("config", {})),
            "alignments": alignment_records,
        })

    semantic = {
        "schema_version": STRAIGHT_STATION_SCHEMA_VERSION,
        "curve_tracks": curve_records,
        "routes": route_records,
    }
    return {
        "semantic": semantic,
        "semantic_sha256": semantic_sha256(semantic),
    }


def validate_straight_route_analysis(analysis, lengths):
    """Validate identities, exact joins and station direction for one pair."""
    if not isinstance(analysis, dict) or not isinstance(analysis.get("semantic"), dict):
        raise ValueError("Invalid straight/station analytical snapshot")
    semantic = analysis["semantic"]
    curves = semantic.get("curve_tracks", [])
    routes = semantic.get("routes", [])
    if [item.get("name") for item in curves] != list(CURVE_TRACK_NAMES):
        raise ValueError("Unexpected inherited curve-track order")
    if len(routes) != 2:
        raise ValueError("The controlled straight/station pair did not produce two routes")

    expected_configs = _canonical(expected_pair_configs(lengths))
    for route_index, (route, expected_length) in enumerate(zip(routes, lengths)):
        expected_route = {
            "route_id": ROUTE_IDS[route_index],
            "name": ROUTE_NAMES[route_index],
            "connection_mode": CONNECTION_MODES[route_index],
            "length_mm": _rounded(expected_length),
            "config": expected_configs[route_index],
        }
        actual_route = {key: route.get(key) for key in expected_route}
        if actual_route != expected_route:
            raise ValueError(
                "Unexpected connected straight route {}: {}".format(
                    route_index + 1, actual_route
                )
            )
        alignments = route.get("alignments", [])
        if len(alignments) != len(CURVE_TRACK_NAMES):
            raise ValueError("A connected route did not inherit every curve track")
        for track_index, alignment in enumerate(alignments):
            expected_source = CURVE_TRACK_NAMES[track_index]
            expected_alignment = {
                "route_id": ROUTE_IDS[route_index],
                "route_name": ROUTE_NAMES[route_index],
                "track_number": track_index + 1,
                "name": "{} - {}".format(ROUTE_NAMES[route_index], expected_source),
                "source_alignment_name": expected_source,
                "connection_mode": CONNECTION_MODES[route_index],
                "create_template": True,
                "show_centreline": True,
            }
            actual_alignment = {
                key: alignment.get(key) for key in expected_alignment
            }
            if actual_alignment != expected_alignment:
                raise ValueError("Unexpected connected straight track identity")
            station = alignment.get("station", {})
            expected_station = _rounded(expected_length)
            if station.get("stations_mm") != [0.0, expected_station]:
                raise ValueError("A straight alignment has unexpected station breaks")
            if (
                station.get("total_mm") != expected_station
                or station.get("core_start_mm") != 0.0
                or station.get("core_end_mm") != expected_station
            ):
                raise ValueError("A straight alignment has unexpected station bounds")
            points = alignment.get("points_xy_mm", [])
            samples = station.get("samples", [])
            if len(points) != 2 or len(samples) != 3:
                raise ValueError("A straight alignment has incomplete station samples")
            if samples[0].get("point_xy_mm") != points[0]:
                raise ValueError("Station zero does not resolve to travel-order start")
            if samples[-1].get("point_xy_mm") != points[-1]:
                raise ValueError("Final station does not resolve to travel-order end")
            join = alignment.get("join", {})
            if join.get("position_error_mm") != 0.0:
                raise ValueError("A connected straight does not share the curve endpoint")
            if join.get("heading_error_rad") != 0.0:
                raise ValueError("A connected straight does not share the curve tangent")
            expected_projection = (
                -expected_station if route_index == 0 else expected_station
            )
            if abs(join.get("remote_travel_projection_mm", 0.0) - expected_projection) > 1.0e-9:
                raise ValueError("A connected straight points in the wrong travel direction")
    calculated = semantic_sha256(semantic)
    if analysis.get("semantic_sha256") != calculated:
        raise ValueError("The straight/station analytical hash is inconsistent")
    return calculated


def _production_record_contract(record):
    return (
        str(record.get("role", "")),
        str(record.get("subtype", "")),
        str(record.get("category", "")),
        str(record.get("selection_key", "")),
        str(record.get("source_binding_type", "")),
        tuple(record.get("supported_formats", [])),
        int(record.get("track_number", 0)),
        str(record.get("route_id", "")),
        str(record.get("route_name", "")),
    )


def _expected_straight_record_contract(route_index):
    route_id = ROUTE_IDS[route_index]
    route_name = ROUTE_NAMES[route_index]
    return [
        (
            "StraightTrackTemplate", "TrackTemplateCompound", "CuttingProfile",
            "track_template_compound_2d", "hidden-production-source", ("dxf", "svg"),
            0, route_id, route_name,
        ),
        (
            "StraightTrackTemplate", "TrackTemplateCompound", "Solid",
            "track_template_compound_3d", "hidden-production-source", ("stl", "step"),
            0, route_id, route_name,
        ),
        (
            "StraightTrackCentreline", "TrackCentreline", "Engraving",
            "track_centrelines", "direct", ("dxf", "svg"),
            1, route_id, route_name,
        ),
        (
            "StraightTrackCentreline", "TrackCentreline", "Engraving",
            "track_centrelines", "direct", ("dxf", "svg"),
            2, route_id, route_name,
        ),
    ]


def _raw_straight_configs(module, document, role):
    matches = [
        obj for obj in document.Objects
        if str(module.object_string_property(obj, "GeneratedRole", "") or "") == role
        and str(module.object_string_property(obj, "TemplateSetID", "") or "")
        == "SET-001"
    ]
    if len(matches) != 1:
        raise ValueError(
            "Expected one SET-001 {} object for raw straight persistence".format(role)
        )
    try:
        payload = json.loads(str(matches[0].StraightTrackConfigurationsJSON))
    except Exception as error:
        raise ValueError("Invalid raw straight configuration JSON: {}".format(error))
    if not isinstance(payload, list):
        raise ValueError("Raw straight configuration persistence is not a list")
    return _canonical(payload)


def straight_station_document_snapshot(module, document, analysis):
    """Combine the analytical pair with the complete copied-document state."""
    validate_straight_route_analysis(
        analysis,
        [route["length_mm"] for route in analysis["semantic"].get("routes", [])],
    )
    document_snapshot = ordinary_track_document_snapshot(module, document)
    semantic = {
        "schema_version": STRAIGHT_STATION_SCHEMA_VERSION,
        "boundary_data": BOUNDARY_DATA,
        "analysis": analysis["semantic"],
        "raw_straight_persistence": {
            "settings": _raw_straight_configs(module, document, "Settings"),
            "template": _raw_straight_configs(module, document, "Template"),
        },
        "document": document_snapshot["semantic"],
    }
    return {
        "semantic": semantic,
        "semantic_sha256": semantic_sha256(semantic),
        "analysis_semantic_sha256": analysis["semantic_sha256"],
        "document_semantic_sha256": document_snapshot["semantic_sha256"],
    }


def _record_id_set(objects):
    result = set()
    for record in objects:
        identity = record.get("identity", {})
        direct = str(identity.get("ProductionRecordID", "") or "")
        if direct:
            result.add(direct)
        for item in identity.get("ProductionRecordIDsJSON", []) or []:
            if str(item or ""):
                result.add(str(item))
    return result


def validate_straight_station_snapshot(
    snapshot,
    lengths,
    expected_hash=None,
):
    """Validate B14 persistence, object roles and ordered production output."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("semantic"), dict):
        raise ValueError("Invalid straight/station workflow snapshot")
    semantic = snapshot["semantic"]
    analysis = {
        "semantic": semantic.get("analysis"),
        "semantic_sha256": snapshot.get("analysis_semantic_sha256"),
    }
    validate_straight_route_analysis(analysis, lengths)
    expected_raw_configs = _canonical(expected_pair_configs(lengths))
    raw_persistence = semantic.get("raw_straight_persistence", {})
    if raw_persistence != {
        "settings": expected_raw_configs,
        "template": expected_raw_configs,
    }:
        raise ValueError("Raw straight manager identities did not persist exactly")
    document = semantic.get("document", {})
    objects = document.get("objects", [])
    role_counts = {}
    for record in objects:
        role = str(record.get("identity", {}).get("GeneratedRole", ""))
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1
    if role_counts != EXPECTED_ROLE_COUNTS:
        raise ValueError("Unexpected straight/station object-role counts: {}".format(role_counts))

    persistence = document.get("persistence", {})
    settings = persistence.get("settings", {}).get("values", {})
    template = persistence.get("template", {}).get("values", {})
    if settings.get("StraightRouteCount") != 2 or settings.get("StraightTrackCount") != 4:
        raise ValueError("Unexpected persisted connected-straight counts")
    expected_persisted = normalise_persisted_json(expected_pair_configs(lengths))
    if settings.get("StraightTrackConfigurationsJSON") != expected_persisted:
        raise ValueError("Unexpected persisted Straight Track Manager configuration")
    if template.get("StraightTrackConfigurationsJSON") != expected_persisted:
        raise ValueError("The template does not mirror the straight configuration")
    for name, value in template.items():
        if settings.get(name) != value:
            raise ValueError("Settings/template persistence differs at {}".format(name))

    route_objects = [
        record for record in objects
        if record.get("identity", {}).get("GeneratedRole")
        in ("StraightTrackTemplate", "StraightTrackCentreline")
    ]
    expected_route_objects = []
    for route_index, expected_length in enumerate(lengths):
        for role in ("StraightTrackTemplate", "StraightTrackCentreline"):
            for track_number in (1, 2):
                expected_route_objects.append(
                    (ROUTE_IDS[route_index], ROUTE_NAMES[route_index], role, track_number)
                )
                matching = [
                    record for record in route_objects
                    if (
                        record.get("identity", {}).get("RouteID"),
                        record.get("identity", {}).get("RouteName"),
                        record.get("identity", {}).get("GeneratedRole"),
                        record.get("identity", {}).get("TrackNumber"),
                    ) == expected_route_objects[-1]
                ]
                if len(matching) != 1:
                    raise ValueError("A stable connected-straight object identity is missing")
                shape = matching[0].get("shape", {})
                if not shape.get("is_valid", False):
                    raise ValueError("A connected-straight object has invalid exact geometry")
                if role == "StraightTrackCentreline" and shape.get("length_mm") != _rounded(expected_length, 6):
                    raise ValueError("A straight centreline length differs from its station total")

    record_index = settings.get("ProductionRecordIndexJSON", {})
    records = list(record_index.get("records", []))
    if len(records) != 12:
        raise ValueError("The connected pair did not produce the expected 12-record catalogue")
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
        raise ValueError("The connected pair changed the inherited curve production order")
    straight_contract = [_production_record_contract(record) for record in records[4:]]
    expected_contract = (
        _expected_straight_record_contract(0)
        + _expected_straight_record_contract(1)
    )
    if straight_contract != expected_contract:
        raise ValueError("Unexpected connected-straight production-record order")
    indexed_ids = {str(record.get("record_id", "")) for record in records}
    if _record_id_set(objects) != indexed_ids:
        raise ValueError("Generated objects do not resolve every production-record identity")

    digest = semantic_sha256(semantic)
    if snapshot.get("semantic_sha256") != digest:
        raise ValueError("The straight/station document hash is inconsistent")
    if expected_hash and digest != expected_hash:
        raise ValueError(
            "Unexpected straight/station semantic SHA-256: {} (expected {})".format(
                digest, expected_hash
            )
        )
    return digest


def curve_geometry_contract(snapshot):
    """Return the curve shapes/identities that a straight-length edit must preserve."""
    semantic = snapshot.get("semantic", {})
    objects = semantic.get("document", {}).get("objects", [])
    selected = []
    for record in objects:
        if record.get("identity", {}).get("GeneratedRole") not in (
            "Template",
            "Centreline",
        ):
            continue
        selected.append({
            "name": record.get("name"),
            "label": record.get("label"),
            "type_id": record.get("type_id"),
            "identity_property_types": record.get("identity_property_types"),
            "identity": {
                key: value
                for key, value in record.get("identity", {}).items()
                if key not in ("ProductionRecordID", "ProductionRecordIDsJSON")
            },
            "shape": record.get("shape"),
        })
    return sorted(selected, key=lambda record: record["name"])
