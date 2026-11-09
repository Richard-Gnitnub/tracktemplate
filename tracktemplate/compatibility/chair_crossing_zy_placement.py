"""Bind two qualified ZY contexts to eight fixed XO-001 source records.

Templot 556b math_unit.pas:29831-29874 selects one ZY assembly on rail 3
with rail 2 as its companion. The source context, not the analytical
chair label, owns this selection. Source-informed, GPL-3.0-or-later;
see NOTICE.md and reference/PROVENANCE.md. No geometry is reconstructed.
"""

import copy
import hashlib
import json
import math

from tracktemplate.application.chair_crossing_zy_catalogue import (
    ZY_CONTEXT_IDS,
    _TO_ZY_CONTEXT_SHA256,
    _TO_ZY_FIXING_SHA256,
    _TO_ZY_MODEL_SHA256,
    _TO_ZY_STATION_MM,
    prepare_turnout_zy_catalogue,
    prepare_zy_catalogue,
    verify_turnout_zy_catalogue,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.chair_placement import place_paired_chair


_RAILS = ("straight switch and closure rail", "curved switch and closure rail")
_CANONICAL_CODES = (("X1-Z", (21, "ZY")), ("X2-Y", (22, "XN")))


def _require(condition, message):
    if not condition:
        raise ValueError("Private ZY crossing placement: " + message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def prepare_crossing_zy(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Return four placements, witnesses, companions and a late verifier.

    Model-mm geometry already contains source crops, shears, constituent
    rotations and base twist. Apply only the existing proper common host
    frame. Catalogue revalidation belongs to the native admission boundary.
    This operation neither changes source records nor admits new hosts.
    """
    prepared = prepare_zy_catalogue(contexts_path)
    _require(tuple(item.run for item in prepared) == ZY_CONTEXT_IDS,
             "both ordered ZY contexts are required")
    selections = {item.run: item for item in prepared}
    canonical_codes = dict(_CANONICAL_CODES)
    configuration = json.loads(signature)["configuration"]
    source_hash = hashlib.sha256(signature.encode()).hexdigest()
    _require(configuration["crossover_id"] == "XO-001"
             and all(item.metadata["source_context_sha256"] == source_hash
                     for item in prepared),
             "source differs from the qualified XO-001 context")
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(_encoded(hosts).encode()).hexdigest()
    _require(all(item.metadata["host_context_sha256"] == host_hash
                 for item in prepared),
             "host geometry differs from the qualified ZY context")
    owners = {configuration["turnout_" + side.lower() + "_id"]: side
              for side in ("A", "B")}
    _require(owners == {"XO-001-A001": "A", "XO-001-B001": "B"},
             "canonical turnout owners differ")
    timber_map = {item["stable_identity"]: item for item in timbers}
    _require(len(timber_map) == len(timbers), "source timber identities repeat")
    records = {}
    for identity, position in positions.items():
        timber = position["prototype_timber_identifier"]
        rail = position["rail_name"]
        if timber not in canonical_codes or rail not in _RAILS:
            continue
        owner = position["parent_turnout_identity"]
        _require(owner in owners, "unqualified turnout owner")
        side = owners[owner]
        timber_id = f"XO-001:{side}:{timber}"
        expected = ("XO-001:chair:" + timber_id.lower().replace(":", "-")
                    + ":" + rail.replace(" ", "-"))
        key = side, timber, rail
        _require(key not in records and identity == expected
                 == position["stable_chair_position_identity"]
                 and position["timber_identity"] == timber_id
                 and position["rail_identity"]
                 == owner + ":rail:" + rail.replace(" ", "-")
                 and (position["chair_code"], position["chair_code_label"])
                 == canonical_codes[timber]
                 and position["special_assignment_deferred"] is True
                 and position["deliberate_omission"] is False,
                 "canonical ZY source ownership or assignment differs")
        records[key] = position
    expected = {(side, timber, rail) for side in ("A", "B")
                for timber in canonical_codes for rail in _RAILS}
    _require(set(records) == expected, "all eight ZY source records are required")
    frozen_records = _encoded([positions, timbers])
    groups = {context: [] for context in ZY_CONTEXT_IDS}
    witnesses, companions = {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and config["track_gauge"] == 16.5,
                 "only the qualified right-hand gauge is supported")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for context_id in ZY_CONTEXT_IDS:
            selection = selections[context_id]
            recipe = selection.context
            timber_name = context_id[3:]
            owner, mate = (records[side, timber_name, rail] for rail in _RAILS)
            timber = timber_map[owner["timber_identity"]]
            source = timber["source_configuration"]
            local_x = source["local_x"]
            _require(type(local_x) in (int, float) and math.isfinite(local_x)
                     and owner["source_configuration"]["timber"] == source
                     == mate["source_configuration"]["timber"]
                     and selection.label == recipe["family"] == "ZY"
                     and recipe["chair_code"] == 21
                     and recipe["context_id"] == context_id
                     and recipe["timber_id"] == timber_name
                     and recipe["station_mm"] == local_x
                     and recipe["native_frame"]["common_timber_curving_applied"]
                     is False,
                     "qualified ZY recipe and source timber disagree")
            station = config["toe_chainage"] + direction * local_x
            _require(0 <= station <= data[side]["total"],
                     "ZY station lies outside its canonical host")
            point, heading = module.interpolate_alignment_station(data[side],
                                                                 station)
            travel = heading if direction > 0 else heading + math.pi
            identity = owner["stable_chair_position_identity"]
            mate_id = mate["stable_chair_position_identity"]
            groups[context_id].append(place_paired_chair(
                identity, owner["rail_identity"], owner["timber_identity"],
                (point.x, point.y), travel, base_z, 8.25, 0.45,
            ))
            companions[mate_id] = identity
            witnesses[identity] = {
                "family": "ZY", "source_chair_code": 21,
                "context_id": context_id,
                "source_model_sha256": selection.model_sha256,
                "source_context_sha256": recipe["context_sha256"],
                "source_station_mm": local_x, "host_station_mm": station,
                "source_rail_code": 3, "mate_position_ids": [mate_id],
                "placement_convention": "source-paired-common-timber-frame.v1",
                "physical_fit": "NOT_PROVED",
            }

    def verify():
        current, _data, current_objects = _host_context(module, document,
                                                       configuration)
        _require(hashlib.sha256(_encoded(current).encode()).hexdigest()
                 == host_hash and all(current_objects[key] is value
                                      for key, value in objects.items()),
                 "canonical host changed during ZY preview")
        _require(_encoded([positions, timbers]) == frozen_records,
                 "source records changed during ZY preview")

    return ({name: tuple(sorted(values, key=lambda item: item.position_id))
             for name, values in groups.items()}, witnesses, companions, verify)


def preview_private_catalogue_turnout_zy_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Preview the fixed LH X1-Z assembly without changing its two records.

    The retained model already contains constituent and fixing transforms.
    Only its proper common outer frame is applied. Canonical key0 stays
    unresolved; the retained research key does not change source policy.
    """
    from tracktemplate.compatibility.chair_reference_preview import (
        _context_shapes_and_verifier,
        _open_source_context,
    )
    from tracktemplate.compatibility.chair_source_support import (
        _finite,
        _finite_rail_timber_support,
        _indexed,
        _require_context,
        _same_number,
    )

    _require(turnout_id == "TO-001" and callable(create_preview),
             "TO-001 and the native adapter are required")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, turnout_id, "ZY",
    )
    context = json.loads(signature)
    _require_context(module, context, turnout_id, settings, plan, family="ZY")
    config = context["configuration"]
    fixed = {
        "handing": "Left-hand",
        "orientation": "Facing in host travel direction",
        "rail_geometry_revision": 2,
        "timber_geometry_revision": 2,
        "toe_chainage": 746.298,
        "template_width": 32.0,
        "chair_analysis_signature": "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379",
    }
    _require(
        all(config.get(key) == value
            and (type(value) not in (int, float) or _finite(config[key]))
            for key, value in fixed.items())
        and analysis.get("geometry_signature")
        == fixed["chair_analysis_signature"]
        and settings.get("future_chair_embed_depth") == 0.2,
        "only the fixed LH facing TO-001 source is supported",
    )
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rail_map = _indexed(rails, "stable_identity")
    timber_map = _indexed(timbers, "stable_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    excluded = _indexed(plan.get("analytical_only"), "chair_position_identity")
    _require(
        len(positions) == 168
        and not instances.keys() & excluded.keys()
        and instances.keys() | excluded.keys() == positions.keys(),
        "the inherited plan must account for all 168 positions once",
    )
    _require(instances and all(_finite(p.get("base_z")) and p["base_z"] == 0.8
                               for p in instances.values()),
             "the source mounting plane differs")
    timber_id = "TO-001:timber:X1-Z"
    identities = tuple("TO-001:chair:to-001-timber-x1-z:"
                       + rail.replace(" ", "-") for rail in _RAILS)
    _require(
        {key for key, p in positions.items()
         if p.get("prototype_timber_identifier") == "X1-Z"
         and p.get("rail_name") in _RAILS} == set(identities)
        and all(key in excluded for key in identities)
        and timber_id in timber_map,
        "the exact two unresolved X1-Z source identities are required",
    )
    timber = timber_map[timber_id]
    source = timber.get("source_configuration", {})
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0),
                      "identifier")
    nominal = layout.get("X1-Z", {})
    _require(
        timber.get("identifier") == timber.get("prototype_reference")
        == "X1-Z"
        and timber.get("parent_turnout_identity") == "TO-001"
        and timber.get("crossover_identity") == ""
        and timber.get("section") == "crossing wing front"
        and "extended_source_timber_identity" not in source
        and type(source.get("turnout_geometry_revision")) is int
        and source["turnout_geometry_revision"] == 2
        and source.get("crossing_suffix") == "Z"
        and source.get("source_note")
        == "REA wing-front crossing-chair spacing: 30 inches"
        and all(_finite(source.get(field))
                and source[field] == nominal.get(key) == expected
                for field, key, expected in (
                    ("local_x", "x", _TO_ZY_STATION_MM),
                    ("local_near_y", "near_y", -16.01483959071012),
                    ("local_far_y", "far_y", 29.98516040928988),
                    ("length_prototype_inches", "length_prototype_inches",
                     138.0),
                )),
        "the fixed nominal X1-Z timber differs",
    )
    axis = source.get("longitudinal_reference_axis")
    _require(isinstance(axis, (list, tuple)) and len(axis) == 2
             and all(_same_number(a, b) for a, b in zip(
                 axis, (0.7358589851037945, 0.6771348123099369))),
             "the source longitudinal timber axis differs")
    for identity, rail_name in zip(identities, _RAILS):
        rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
        position = positions[identity]
        expected = {
            "stable_chair_position_identity": identity,
            "rail_identity": rail_id, "rail_name": rail_name,
            "rail_role": rail_name, "timber_identity": timber_id,
            "prototype_timber_identifier": "X1-Z",
            "timber_identifier": "X1-Z", "parent_turnout_identity": "TO-001",
            "parent_crossover_identity": "", "handedness": "Left-hand",
            "handedness_classification": "source-derived prototype requirement",
            "chair_code": 21, "chair_code_label": "ZY",
            "chair_family": "common-crossing chair",
            "chair_subtype": "REA common-crossing subtype awaiting detailed special-chair assignment",
            "source_or_assumed_classification": "temporary visual approximation",
            "assignment_status": "deferred to special-chair assignment",
            "assignment_complete_in_current_stage": False,
            "special_assignment_deferred": True, "deliberate_omission": False,
            "stale_signature_state": False, "validation_status": "Advisory",
            "key_direction_sign": 0,
            "key_orientation": "requires confirmation from the final special-chair subtype and keying arrangement",
            "key_orientation_classification": "dimension requiring later confirmation",
        }
        _require(all(position.get(key) == value
                     and (type(value) not in (bool, int)
                          or type(position.get(key)) is type(value))
                     for key, value in expected.items()),
                 "the canonical ZY assignment or unresolved key differs")
        original = excluded[identity]
        _require(original.get("rail_identity") == rail_id
                 and original.get("timber_identity") == timber_id
                 and original.get("chair_label") == "ZY"
                 and original.get("chair_family") == "common-crossing chair"
                 and original.get("deliberate_omission") is False
                 and original.get("unresolved_special") is True,
                 "the original ZY exclusion differs")
        rail = rail_map.get(rail_id, {})
        rail_source = {
            "gauge_face": rail_name + " gauge face",
            "outer_face": rail_name + " outer face",
            "gauge_orientation_source": "mapped named turnout rail faces",
            "rail_geometry_revision": 2,
        }
        _require(
            rail.get("name") == rail.get("rail_role") == rail_name
            and rail.get("parent_turnout_identity") == "TO-001"
            and rail.get("parent_crossover_identity") == ""
            and rail.get("turnout_side") == ""
            and rail.get("source_configuration") == rail_source
            and position.get("source_configuration")
            == {"rail": rail_source, "timber": source},
            "the named supporting rail or position source binding differs",
        )
        _finite_rail_timber_support(position, rail, timber,
                                    label="ZY", require=_require)

    def host_state():
        obj = source_document.getObject(config.get("host_object", ""))
        _require(obj is not None and not obj.Shape.isNull()
                 and obj.Shape.isValid(), "the canonical host is unavailable")
        data = module.turnout_host_alignment(obj)
        record = {
            "object_name": obj.Name,
            "points": [[p.x, p.y] for p in data["points"]],
            "headings": data["headings"], "stations": data["stations"],
            "total": data["total"],
        }
        _require(_finite(record["total"]) and record["total"] > 0
                 and all(_finite(v) for p in record["points"] for v in p)
                 and all(_finite(v) for key in ("headings", "stations")
                         for v in record[key]), "nonfinite canonical host")
        return obj, data, _encoded(record)

    host_object, host, host_signature = host_state()
    station = config["toe_chainage"] + source["local_x"]
    _require(0 <= station <= host["total"], "ZY lies outside its host")
    point, heading = module.interpolate_alignment_station(host, station)
    centre_y = (source["local_near_y"] + source["local_far_y"]) / 2
    centre = timber.get("centre")
    _require(
        all(_same_number(a, b) for a, b in zip(
            (point.x, point.y, heading),
            (850.6580320655746, 392.05622271228776, 1.1674251123351245)))
        and _same_number(timber.get("host_chainage"), station)
        and _same_number(timber.get("local_rail_heading_radians"), heading)
        and isinstance(centre, (list, tuple)) and len(centre) == 2
        and _same_number(centre[0], point.x - centre_y * math.sin(heading))
        and _same_number(centre[1], point.y + centre_y * math.cos(heading)),
        "the initial fixed host anchor or nominal timber frame differs",
    )
    prepared = prepare_turnout_zy_catalogue(catalogue_path)
    owner, companion = identities
    placements = (place_paired_chair(
        owner, positions[owner]["rail_identity"], timber_id,
        (point.x, point.y), heading, 0.8, 8.25, 0.45,
    ),)
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "ZY", signature,
    )

    def verify_inputs():
        verify_source()
        current_object, _data, current_signature = host_state()
        _require(current_object is host_object
                 and current_signature == host_signature,
                 "canonical host changed during ZY preview")
        verify_turnout_zy_catalogue(prepared)

    receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:"
        + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions), "selected_zy_count": 1,
        "represented_source_position_count": 2,
        "selected_family_counts": {"ZY": 1},
        "selected_positions": [{
            "position_id": owner, "family": "ZY", "source_hand": "LH",
            "prototype_timber_identifier": "X1-Z", "source_rail_code": 3,
            "source_chair_code": 21, "source_station_mm": source["local_x"],
            "host_station_mm": station,
            "source_model_sha256": _TO_ZY_MODEL_SHA256,
            "source_context_sha256": _TO_ZY_CONTEXT_SHA256,
            "fixing_recipe_sha256": _TO_ZY_FIXING_SHA256,
            "original_position": copy.deepcopy(positions[owner]),
            "original_companion": copy.deepcopy(positions[companion]),
            "physical_fit": "NOT_PROVED",
        }],
        "shared_supports": {companion: owner},
        "remaining_positions": [copy.deepcopy(p)
                                for identity, p in sorted(positions.items())
                                if identity not in identities],
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "retained_research_key_direction_sign": 1,
        "retained_research_key_offset_mm": 0, "source_base_z_mm": 0.8,
        "source_document_mutation": False,
        "model_support_adjustments_applied": False,
        "limits": [
            "One fixed LH X1-Z assembly; only its two explicit source identities.",
            "Canonical key0 and all original classifications remain unchanged.",
            "Retained research +1 key/zero offset does not resolve key policy.",
            "No native, GUI, physical-fit, production, export or phase acceptance.",
        ],
    }
    return create_preview(catalogue_path, placements, shapes, receipt,
                          verify_inputs)
