"""Bind three retained central CC assemblies to the fixed TO-001 reference.

The left-hand main-side source uses rail 1 without the RH jaw rotation.
Its stock/check pair shares one rigid frame. Canonical analytical labels,
physical exclusions and the existing S1/S1J/P routes remain unchanged.
"""

import copy
import hashlib
import json
import math

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_catalogue_placement import (
    _finite,
    _indexed,
    _require_context,
)
from tracktemplate.compatibility.chair_heel_l1_placement import _same_number
from tracktemplate.compatibility.chair_reference_preview import (
    _canonical_json,
    _context_shapes_and_verifier,
    _open_source_context,
)
from tracktemplate.domain.chair_placement import place_paired_chair


_ANALYSIS_SHA256 = (
    "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379"
)
_CC_SHA256 = (
    "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637"
)
_CC_CONTEXT_SHA256 = (
    "5291c5d1b350373d93d686feb3bad35c5e2dfb62347bfc5d9906bf2c81077b6d"
)
_SELECTION = (("X2-Y", 22, "XN"), ("X3-X", 23, "XA"), ("X4-A", 24, "AA"))
_RAILS = (("main-side stock rail", "stock rail"),
          ("main-side check rail", "check rail"))


def _require(condition, message):
    if not condition:
        raise ValueError("Private TO-001 central CC: " + message)


def _configuration(module, context, settings, plan):
    _require_context(module, context, "TO-001", settings, plan, family="CC")
    config = context["configuration"]
    expected = {
        "handing": "Left-hand",
        "orientation": "Facing in host travel direction",
        "rail_geometry_revision": 2, "timber_geometry_revision": 2,
        "toe_chainage": 746.298, "template_width": 32.0,
        "chair_analysis_signature": _ANALYSIS_SHA256,
    }
    _require(all(config.get(key) == value for key, value in expected.items())
             and context["analysis"].get("geometry_signature")
             == _ANALYSIS_SHA256,
             "only the qualified left-hand facing TO-001 source is supported")
    return config


def _host(module, document, config):
    obj = document.getObject(config.get("host_object", ""))
    _require(obj is not None and not obj.Shape.isNull() and obj.Shape.isValid(),
             "the canonical host is unavailable")
    data = module.turnout_host_alignment(obj)
    record = {
        "object_name": obj.Name,
        "points": [[point.x, point.y] for point in data["points"]],
        "headings": data["headings"], "stations": data["stations"],
        "total": data["total"],
    }
    _require(_finite(record["total"]) and record["total"] > 0,
             "invalid canonical host length")
    # Freeze all host inputs, including samples outside the selected stations.
    return obj, data, _canonical_json(record)


def _source_binding(position, rail, timber, original, name, code, label, role):
    rail_name, rail_role = _RAILS[role]
    rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
    timber_id = "TO-001:timber:" + name
    identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                + rail_name.replace(" ", "-"))
    expected = {
        "stable_chair_position_identity": identity,
        "rail_identity": rail_id, "rail_name": rail_name,
        "rail_role": rail_role, "timber_identity": timber_id,
        "prototype_timber_identifier": name, "timber_identifier": name,
        "parent_turnout_identity": "TO-001", "parent_crossover_identity": "",
        "handedness": "Left-hand", "chair_code": code,
        "chair_code_label": label,
        "assignment_status": "deferred to special-chair assignment",
        "assignment_complete_in_current_stage": False,
        "special_assignment_deferred": True, "deliberate_omission": False,
        "stale_signature_state": False, "validation_status": "Advisory",
        "key_direction_sign": 0,
        "key_orientation": "requires confirmation from the final special-chair "
        "subtype and keying arrangement",
        "key_orientation_classification": "dimension requiring later confirmation",
    }
    _require(all(position.get(key) == value for key, value in expected.items())
             and type(position.get("chair_code")) is int,
             "the selected chair identity or deferred assignment differs")
    _require(rail.get("stable_identity") == rail_id
             and rail.get("name") == rail_name
             and rail.get("parent_turnout_identity") == "TO-001"
             and rail.get("parent_crossover_identity") == ""
             and timber.get("stable_identity") == timber_id
             and timber.get("parent_turnout_identity") == "TO-001"
             and timber.get("crossover_identity") == ""
             and timber.get("identifier") == name,
             "the named rail or timber ownership differs")
    rail_source = {
        "gauge_face": rail_name + " gauge face",
        "outer_face": rail_name + " outer face",
        "gauge_orientation_source": "mapped named turnout rail faces",
        "rail_geometry_revision": 2,
    }
    _require(rail.get("source_configuration") == rail_source
             and position.get("source_configuration") == {
                 "rail": rail_source, "timber": timber.get("source_configuration"),
             }, "the rail or timber source binding differs")
    _require(original.get("chair_position_identity") == identity
             and original.get("rail_identity") == rail_id
             and original.get("timber_identity") == timber_id
             and original.get("chair_label") == label
             and original.get("reason") == "special chair assignment remains analytical"
             and original.get("deliberate_omission") is False
             and original.get("unresolved_special") is True,
             "the original analytical exclusion differs")


def _timber_frame(module, host, config, timber, nominal):
    source = timber.get("source_configuration", {})
    _require("extended_source_timber_identity" not in source
             and source.get("turnout_geometry_revision") == 2
             and all(_finite(source.get(field))
                     and source[field] == nominal.get(layout_field)
                     for field, layout_field in (
                         ("local_x", "x"), ("local_near_y", "near_y"),
                         ("local_far_y", "far_y"),
                         ("length_prototype_inches", "length_prototype_inches"),
                     )), "the nominal central-check timber source differs")
    station = config["toe_chainage"] + source["local_x"]
    _require(0 <= station <= host["total"], "the timber lies outside its host")
    point, heading = module.interpolate_alignment_station(host, station)
    _require(all(_finite(value) for value in (point.x, point.y, heading)),
             "non-finite canonical host frame")
    centre_y = (source["local_near_y"] + source["local_far_y"]) / 2
    centre = timber.get("centre")
    _require(_same_number(timber.get("host_chainage"), station)
             and _same_number(timber.get("local_rail_heading_radians"), heading)
             and isinstance(centre, (list, tuple)) and len(centre) == 2
             and _same_number(centre[0], point.x - centre_y * math.sin(heading))
             and _same_number(centre[1], point.y + centre_y * math.cos(heading)),
             "the timber is not at its nominal left-hand host station")
    return station, point, heading


def preview_private_catalogue_turnout_cc_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Create three private CC assemblies covering six fixed source positions.

    No geometry, analytical assignment or accepted placement is replaced.
    The existing adapter owns catalogue revalidation, transaction and cleanup.
    """
    _require(turnout_id == "TO-001" and callable(create_preview),
             "TO-001 and the native adapter are required")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, turnout_id, "CC",
    )
    context = json.loads(signature)
    config = _configuration(module, context, settings, plan)
    positions = _indexed(analysis.get("positions"), "stable_chair_position_identity")
    rail_map = _indexed(rails, "stable_identity")
    timber_map = _indexed(timbers, "stable_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    excluded = _indexed(plan.get("analytical_only"), "chair_position_identity")
    _require(len(positions) == 168 and not instances.keys() & excluded.keys()
             and instances.keys() | excluded.keys() == positions.keys(),
             "the inherited plan must account for all 168 positions exactly once")
    datums = [item.get("base_z") for item in instances.values()]
    _require(datums and all(_finite(value) and value == datums[0]
                           for value in datums), "source mounting datum differs")
    prepared = prepare_catalogue_chair(catalogue_path, "CC", run="context-native-02")
    _require(prepared.label == "CC" and prepared.run == "context-native-02"
             and prepared.model_sha256 == _CC_SHA256
             and prepared.context.get("context_sha256") == _CC_CONTEXT_SHA256
             and len(prepared.components) == 33,
             "the qualified central CC catalogue differs")
    obj, host, host_signature = _host(module, source_document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0), "identifier")
    placements, selected, shared = [], [], []
    represented = set()
    for index, (name, code, label) in enumerate(_SELECTION):
        pair = []
        for role, (rail_name, _rail_role) in enumerate(_RAILS):
            identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                        + rail_name.replace(" ", "-"))
            _require(identity in positions and identity in excluded,
                     "a selected central CC position is missing or already physical")
            position = positions[identity]
            timber = timber_map.get(position.get("timber_identity"), {})
            _source_binding(
                position, rail_map.get(position.get("rail_identity"), {}),
                timber, excluded[identity], name,
                code if role == 0 else 15, label if role == 0 else "CC", role,
            )
            pair.append(position)
        source = timber["source_configuration"]
        _require(source["local_x"] == dimensions["a_timber_x"] + 10 * (index - 2),
                 "the source does not select a parallel central CC station")
        station, point, heading = _timber_frame(
            module, host, config, timber, layout.get(name, {}),
        )
        owner, companion = pair
        placement = place_paired_chair(
            owner["stable_chair_position_identity"], owner["rail_identity"],
            owner["timber_identity"], (point.x, point.y), heading, datums[0],
            -config["track_gauge"] / 2, 0.45,
        )
        placements.append(placement)
        represented.update(item["stable_chair_position_identity"] for item in pair)
        shared.append({"position_id": companion["stable_chair_position_identity"],
                       "assembly_position_id": placement.position_id})
        selected.append({
            "position_id": placement.position_id, "family": "CC",
            "prototype_timber_identifier": name, "source_rail_code": 1,
            "source_station_mm": source["local_x"], "host_station_mm": station,
            "source_model_sha256": prepared.model_sha256,
            "source_context_sha256": _CC_CONTEXT_SHA256,
            "original_positions": copy.deepcopy(pair),
            "physical_fit": "NOT_PROVED",
        })
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "CC", signature,
    )

    def verify_inputs():
        verify_source()
        current_obj, _data, current_host = _host(module, source_document, config)
        _require(current_obj is obj and current_host == host_signature,
                 "the canonical host changed during preview")
        verify_catalogue_sources(prepared)

    receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions), "selected_cc_count": 3,
        "represented_source_position_count": 6, "shared_supports": shared,
        "selected_positions": selected,
        "remaining_positions": [copy.deepcopy(position)
                                for identity, position in sorted(positions.items())
                                if identity not in represented],
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "source_base_z_mm": datums[0],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "source_document_mutation": False,
        "limits": ["Private fixed TO-001 reference; no physical-fit acceptance.",
                   "Original analytical labels and exclusions remain unchanged.",
                   "No production, export, persistence or live-update authority."],
    }
    return create_preview(catalogue_path, tuple(placements), shapes, receipt, verify_inputs)
