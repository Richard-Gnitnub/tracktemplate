"""Bind retained check assemblies to the fixed TO-001 reference.

The left-hand main-side source uses rail 1 without the RH jaw rotation.
Its stock/check pair shares one rigid frame. Three turnout-side pairs
require explicit opt-in and independently qualified component frames.
Three separately requested check ends retain their own qualified frames.
Canonical labels, exclusions and existing S1/S1J/P routes stay unchanged.
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
    _finite_rail_timber_support,
    _indexed,
    _require_context,
)
from tracktemplate.compatibility.chair_heel_l1_placement import _same_number
from tracktemplate.compatibility.chair_reference_preview import (
    _canonical_json,
    _context_shapes_and_verifier,
    _open_source_context,
)
from tracktemplate.domain.chair_placement import (
    S1Placement,
    place_paired_chair,
)
from tracktemplate.domain.central_check_placement import (
    CentralCheckPlacement,
    place_left_hand_central_check,
)
from tracktemplate.domain.check_end_placement import place_left_hand_check_end


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
_TS_RAILS = (("turnout-side stock rail", "stock rail"),
             ("turnout-side check rail", "check rail"))
_CHECK_END_MODELS = (
    ("CCL", "692a8cfbe6845fd9fce4e8b471f1ec37d5388366c6451f9bff2d65601dbccb3d"),
    ("CCR", "d594dfb2f387c2b2a0360863ea8dcc30cd2057ed06095f8eb1e49a9421282fa7"),
)
_CHECK_END_CONTEXT_SHA256 = (
    "4c6d059f99889cb292fc028783d2ee425b7493540e6b22b80f55961df543d2ef"
)


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


def _source_binding(position, rail, timber, original, name, code, label, role,
                    *, turnout_side=False):
    rail_name, rail_role = (_TS_RAILS if turnout_side else _RAILS)[role]
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
    if turnout_side:
        _require(all(position.get(key) is value
                     for key, value in expected.items() if type(value) is bool)
                 and rail.get("rail_role") == rail_role,
                 "the turnout-side source state or rail role differs")
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
    *, include_turnout_side=False,
):
    """Create fixed CC assemblies, optionally including turnout-side pairs.

    No geometry, analytical assignment or accepted placement is replaced.
    The existing adapter owns catalogue revalidation, transaction and cleanup.
    """
    _require(type(include_turnout_side) is bool,
             "include_turnout_side must be a boolean")
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
    for turnout_side in ((False, True) if include_turnout_side else (False,)):
        selected_rails = _TS_RAILS if turnout_side else _RAILS
        for index, (name, code, label) in enumerate(_SELECTION):
            pair = []
            for role, (rail_name, _rail_role) in enumerate(selected_rails):
                identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                            + rail_name.replace(" ", "-"))
                _require(
                    identity in positions and identity in excluded,
                    "a selected central CC position is missing or already physical",
                )
                position = positions[identity]
                timber = timber_map.get(position.get("timber_identity"), {})
                _source_binding(
                    position, rail_map.get(position.get("rail_identity"), {}),
                    timber, excluded[identity], name,
                    code if role == 0 else 15,
                    label if role == 0 else "CC", role,
                    turnout_side=turnout_side,
                )
                if turnout_side:
                    _finite_rail_timber_support(
                        position, rail_map[position["rail_identity"]], timber,
                        label="turnout-side CC", require=_require,
                    )
                pair.append(position)
            source = timber["source_configuration"]
            _require(
                source["local_x"] == dimensions["a_timber_x"] + 10 * (index - 2),
                "the source does not select a parallel central CC station",
            )
            station, point, heading = _timber_frame(
                module, host, config, timber, layout.get(name, {}),
            )
            owner, companion = pair
            if turnout_side:
                low = dimensions.get("check_turnout_flare_in_x")
                high = dimensions.get("check_turnout_flare_out_x")
                _require(_finite(low) and _finite(high)
                         and low < source["local_x"] <= high,
                         "the turnout-side source is not parallel central CC")
                x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
                    dimensions, source["local_x"],
                )
                _require(all(_finite(value) for value in (x, y, angle))
                         and x == source["local_x"],
                         "the turnout-side source rail pose differs")
                placement = place_left_hand_central_check(
                    owner["stable_chair_position_identity"],
                    owner["rail_identity"],
                    owner["timber_identity"], (point.x, point.y), heading,
                    datums[0], source_angle_rad=angle,
                    source_gauge_y_mm=y + config["track_gauge"] / 2,
                )
            else:
                placement = place_paired_chair(
                    owner["stable_chair_position_identity"],
                    owner["rail_identity"], owner["timber_identity"],
                    (point.x, point.y), heading, datums[0],
                    -config["track_gauge"] / 2, 0.45,
                )
                if include_turnout_side:
                    frame = S1Placement(
                        placement.position_id, placement.rail_id,
                        placement.timber_id, placement.origin_mm,
                        placement.x_axis, placement.y_axis,
                    )
                    placement = CentralCheckPlacement(
                        frame.position_id, frame.rail_id, frame.timber_id,
                        frame.origin_mm, frame.x_axis, frame.y_axis,
                        (frame,) * 4,
                    )
            placements.append(placement)
            represented.update(
                item["stable_chair_position_identity"] for item in pair
            )
            shared.append({
                "position_id": companion["stable_chair_position_identity"],
                "assembly_position_id": placement.position_id,
            })
            selected.append({
                "position_id": placement.position_id, "family": "CC",
                "prototype_timber_identifier": name,
                "source_rail_code": 4 if turnout_side else 1,
                "source_station_mm": source["local_x"],
                "host_station_mm": station,
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
        "analysis_position_count": len(positions),
        "selected_cc_count": len(placements),
        "represented_source_position_count": len(represented),
        "shared_supports": shared,
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
    options = {"include_turnout_side": True} if include_turnout_side else {}
    if include_turnout_side:
        placements.sort(key=lambda value: value.position_id)
    return create_preview(
        catalogue_path, tuple(placements), shapes, receipt, verify_inputs,
        **options,
    )


def preview_private_catalogue_turnout_check_end_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Prepare three fixed LH check ends through the existing lifecycle.

    Source heave_chairs.pas:1363-1396 supplies the handed CCL/CCR selection.
    Its raw ZY/AB stock and CC check records remain canonical and deferred.
    Entire X1-Z turnout-side support stays excluded. This source-only view
    gives no native, physical-fit, production or model-transfer acceptance.
    """
    def require(condition, message):
        if not condition:
            raise ValueError("Private TO-001 check ends: " + message)

    require(turnout_id == "TO-001" and callable(create_preview),
            "TO-001 and the native adapter are required")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, turnout_id, "CCL/CCR",
    )
    config = _configuration(module, json.loads(signature), settings, plan)
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rail_map = _indexed(rails, "stable_identity")
    timber_map = _indexed(timbers, "stable_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    excluded = _indexed(plan.get("analytical_only"), "chair_position_identity")
    require(len(positions) == 168 and not instances.keys() & excluded.keys()
            and instances.keys() | excluded.keys() == positions.keys(),
            "the inherited plan must account for all 168 positions once")
    datums = [item.get("base_z") for item in instances.values()]
    require(datums and all(_finite(value) and value == datums[0]
                          for value in datums), "source mounting datum differs")
    selections = {}
    for family, digest in _CHECK_END_MODELS:
        prepared = prepare_catalogue_chair(
            catalogue_path, family, run="context-native-02",
        )
        require(prepared.label == family and prepared.run == "context-native-02"
                and prepared.model_sha256 == digest
                and prepared.context.get("context_sha256")
                == _CHECK_END_CONTEXT_SHA256 and len(prepared.components) == 33,
                "the fixed check-end catalogue differs")
        selections[family] = prepared
    obj, host, host_signature = _host(module, source_document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0),
                      "identifier")
    placements, selected, shared = [], [], []
    represented = set()
    # heave_chairs.pas LH selection, qualified against the exact TO source.
    # The fourth source pair is deliberately absent, not partly admitted.
    targets = (("X1-Z", -30, False, "CCL", 14, 21, "ZY"),
               ("X5-B", 10, False, "CCR", 16, 25, "AB"),
               ("X5-B", 10, True, "CCL", 16, 25, "AB"))
    for name, offset, turnout_side, family, source_code, code, label in targets:
        pair = []
        for role, (rail_name, _rail_role) in enumerate(
            _TS_RAILS if turnout_side else _RAILS,
        ):
            identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                        + rail_name.replace(" ", "-"))
            require(identity in positions and identity in excluded,
                    "a selected check-end position is missing or physical")
            position = positions[identity]
            timber = timber_map.get(position.get("timber_identity"), {})
            rail = rail_map.get(position.get("rail_identity"), {})
            _source_binding(
                position, rail, timber, excluded[identity], name,
                code if role == 0 else 15, label if role == 0 else "CC",
                role, turnout_side=turnout_side,
            )
            require(all(position.get(field) is False for field in (
                "assignment_complete_in_current_stage", "deliberate_omission",
                "stale_signature_state",
            )) and position.get("special_assignment_deferred") is True,
                "the deferred source state differs")
            _finite_rail_timber_support(
                position, rail, timber, label="check end", require=require,
            )
            pair.append(position)
        local_x = timber["source_configuration"]["local_x"]
        require(_finite(local_x)
                and local_x == dimensions["a_timber_x"] + offset,
                "the fixed check-end station differs")
        prefix = "check_turnout_" if turnout_side else "check_main_"
        bounds = (dimensions.get(prefix + field) for field in (
            ("start_x", "flare_in_x") if source_code == 14 else
            ("flare_out_x", "end_x")
        ))
        low, high = bounds
        require(_finite(low) and _finite(high) and low < local_x <= high,
                "the source does not select this check end")
        station, point, heading = _timber_frame(
            module, host, config, timber, layout.get(name, {}),
        )
        angle, gauge_y = 0.0, 0.0
        if turnout_side:
            x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
                dimensions, local_x,
            )
            curve_end = (dimensions["switch_curve_end_x"]
                         - dimensions["gauge"] * math.sin(dimensions["k3"]))
            require(all(_finite(value) for value in (x, y, angle, curve_end))
                    and x == local_x and x >= curve_end
                    and angle == dimensions["k3"],
                    "only the qualified X5 tangent source pose is supported")
            gauge_y = y + config["track_gauge"] / 2
        owner, companion = pair
        placement = place_left_hand_check_end(
            owner["stable_chair_position_identity"], owner["rail_identity"],
            owner["timber_identity"], (point.x, point.y), heading, datums[0],
            side="TS" if turnout_side else "MS", family=family,
            source_angle_rad=angle, source_gauge_y_mm=gauge_y,
        )
        placements.append(placement)
        represented.update(p["stable_chair_position_identity"] for p in pair)
        shared.append({"position_id": companion["stable_chair_position_identity"],
                       "assembly_position_id": placement.position_id})
        selected.append({
            "position_id": placement.position_id, "family": family,
            "prototype_timber_identifier": name,
            "source_chair_code": source_code,
            "source_rail_code": 4 if turnout_side else 1,
            "source_station_mm": local_x, "host_station_mm": station,
            "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
            "source_branch": "turnoutst_main" if turnout_side else "main_straight",
            "source_model_sha256": selections[family].model_sha256,
            "source_context_sha256": _CHECK_END_CONTEXT_SHA256,
            "original_positions": copy.deepcopy(pair),
            "physical_fit": "NOT_PROVED",
        })
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "CCL/CCR", signature,
    )

    def verify_inputs():
        verify_source()
        current_obj, _data, current_host = _host(module, source_document, config)
        require(current_obj is obj and current_host == host_signature,
                "the canonical host changed during preview")
        for prepared in selections.values():
            verify_catalogue_sources(prepared)

    receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "selected_check_end_count": len(placements),
        "selected_family_counts": {"CCL": 2, "CCR": 1},
        "represented_source_position_count": len(represented),
        "shared_supports": shared, "selected_positions": selected,
        "remaining_positions": [copy.deepcopy(position)
                                for identity, position in sorted(positions.items())
                                if identity not in represented],
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "source_base_z_mm": datums[0],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "source_document_mutation": False,
        "limits": [
            "Three fixed TO-001 LH check ends; the X1 turnout-side pair is excluded.",
            "Original analytical labels and exclusions remain unchanged.",
            "No native, physical-fit, production, export or phase acceptance.",
        ],
    }
    return create_preview(
        catalogue_path, tuple(sorted(placements, key=lambda p: p.position_id)),
        shapes, receipt, verify_inputs,
    )
