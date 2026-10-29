"""Qualify four finite-rail candidates in the fixed private XO-001 source.

Call only after ``prepare_crossing_splits`` admits its pinned catalogue,
complete canonical source and host. The retained XA recipe has no external
heave input. Templot 556b math_unit.pas:29843-29919 selects XA there;
30944-30974 emits its constituents, without a separate XN assembly.
B15:43470-43503 creates candidates separately for named rail segments.
Continuity proves that lineage, never that XA supports a curved knuckle.
Source-informed, GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
"""

import hashlib
import json
import math


_XA_CONTEXT_SHA256 = (
    "56b7518f6446e9d2c91fcee3b94dc9c351b328eed19ac970dfa6fe096e91e802"
)
_CONTINUITY_FIELDS = ("points", "gauge_face_points", "outer_face_points")


def _require(condition, message):
    if not condition:
        raise ValueError("Private crossing endpoint exclusion: " + message)


def _record(records, identity):
    value = records.get(identity)
    _require(isinstance(value, dict), "a canonical source record is missing")
    return value


def _polyline(rail, field):
    points = rail.get(field)
    _require(isinstance(points, (list, tuple)) and len(points) >= 2
             and all(isinstance(point, (list, tuple)) and len(point) == 2
                     and all(type(value) in (int, float)
                             and math.isfinite(value) for value in point)
                     for point in points),
             "finite named rail points are required")
    return points


def _position(positions, rails, side, name, role, code, timber):
    owner = f"XO-001-{side}001"
    suffix = name.replace(" ", "-")
    identity = f"XO-001:chair:xo-001-{side.lower()}-x3-x:{suffix}"
    rail_id = owner + ":rail:" + suffix
    position, rail = _record(positions, identity), _record(rails, rail_id)
    _require(position.get("stable_chair_position_identity") == identity
             and rail.get("stable_identity") == rail_id
             and position.get("rail_identity") == rail_id
             and position.get("rail_name") == rail.get("name") == name
             and position.get("rail_role") == rail.get("rail_role") == role
             and all(record.get("parent_turnout_identity") == owner
                     and record.get("parent_crossover_identity") == "XO-001"
                     for record in (position, rail))
             and position.get("timber_identity") == timber["stable_identity"]
             and position.get("timber_identifier") == "X3-X"
             and position.get("prototype_timber_identifier") == "X3-X"
             and type(position.get("chair_code")) is int
             and position["chair_code"] == code
             and position.get("chair_code_label") == ("XN" if code == 22 else "XA")
             and position.get("special_assignment_deferred") is True
             and position.get("deliberate_omission") is False,
             "canonical endpoint ownership or assignment differs")
    configuration = position.get("source_configuration")
    source = rail.get("source_configuration")
    _require(isinstance(configuration, dict) and isinstance(source, dict)
             and configuration.get("rail") == source
             and configuration.get("timber") == timber["source_configuration"]
             and source.get("gauge_face") == name + " gauge face"
             and source.get("outer_face") == name + " outer face"
             and source.get("rail_geometry_revision") == 2,
             "named rail or timber source configuration differs")
    return identity, position, rail


def qualify_knuckle_exclusions(
    positions, rails, timbers, split_witnesses, split_companions,
):
    """Return four exclusion witnesses after fixed XA admission.

    Inputs are indexed canonical records and the qualified split result.
    Exact stored endpoint identity is required; no numerical or fit
    tolerance is introduced. No input, placement or source label changes.
    """
    _require(all(isinstance(records, dict) for records in (
        positions, rails, timbers, split_witnesses, split_companions,
    )), "source records and qualified split results must be indexed")
    result = {}
    for side in ("A", "B"):
        timber_id = f"XO-001:{side}:X3-X"
        timber = _record(timbers, timber_id)
        source = timber.get("source_configuration")
        _require(timber.get("stable_identity") == timber_id
                 and timber.get("identifier") == "X3-X"
                 and timber.get("prototype_reference") == "X3-X"
                 and timber.get("parent_turnout_identity") == f"XO-001-{side}001"
                 and timber.get("crossover_identity") == "XO-001"
                 and isinstance(source, dict),
                 "qualified X3-X timber identity differs")
        owner_id = (f"XO-001:chair:xo-001-{side.lower()}-x3-x:"
                    "turnout-side-wing-rail")
        mate_id = (f"XO-001:chair:xo-001-{side.lower()}-x3-x:"
                   "main-side-wing-rail")
        witness = _record(split_witnesses, owner_id)
        station = witness.get("source_station_mm")
        _require(witness.get("family") == "XA"
                 and witness.get("source_chair_code") == 23
                 and witness.get("context_id") == "RH-X3-X"
                 and witness.get("source_context_sha256") == _XA_CONTEXT_SHA256
                 and witness.get("source_rail_code") == 3
                 and witness.get("mate_position_ids") == [mate_id]
                 and split_companions.get(mate_id) == owner_id
                 and owner_id not in split_companions
                 and type(station) in (int, float) and math.isfinite(station)
                 and source.get("local_x") == station,
                 "the fixed XA source selection or station differs")
        for branch in ("main-side", "turnout-side"):
            identity, position, rail = _position(
                positions, rails, side, branch + " wing knuckle",
                "wing rail knuckle", 22, timber,
            )
            wing_id, wing_position, wing = _position(
                positions, rails, side, branch + " wing rail",
                "wing rail", 23, timber,
            )
            _require(wing_id == (mate_id if branch == "main-side" else owner_id)
                     and identity not in split_witnesses
                     and identity not in split_companions,
                     "endpoint candidate must not become an assembly support")
            for field in _CONTINUITY_FIELDS:
                endpoint = _polyline(rail, field)[-1]
                _require(endpoint == _polyline(wing, field)[0],
                         "finite endpoint and continuing rail differ")
            _require(position.get("centre_point") == rail["points"][-1],
                     "candidate is not the finite rail endpoint")
            digest = hashlib.sha256(json.dumps(
                [position, rail, wing_position, wing, timber],
                sort_keys=True, allow_nan=False,
            ).encode("utf-8")).hexdigest()
            result[identity] = {
                "physical_status": "source-endpoint-exclusion",
                "exclusion_kind": "finite-segment-endpoint-not-selected-source-chair",
                "reason": "The fixed source selects XA at this timber. "
                          "This finite-segment endpoint is not a separate "
                          "source-selected XN chair.",
                "source_endpoint_exclusion": {
                    "context_id": "RH-X3-X",
                    "selected_source_family": "XA",
                    "selected_source_chair_code": 23,
                    "source_station_mm": station,
                    "selected_owner_position_id": owner_id,
                    "continuing_rail_identity": wing["stable_identity"],
                    "canonical_position_is_rail_endpoint": True,
                    "endpoint_continuity_fields": list(_CONTINUITY_FIELDS),
                    "source_context_sha256": _XA_CONTEXT_SHA256,
                    "source_geometry_sha256": digest,
                    "physical_fit": "NOT_ASSESSED",
                },
            }
    return result
