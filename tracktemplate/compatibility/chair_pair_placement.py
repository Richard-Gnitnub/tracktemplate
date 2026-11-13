"""Bind the qualified private paired assemblies to the frozen XO context.

This finite compatibility route preserves source identities and the host's
accepted station interpolation. It does not infer a source chair frame from
sampled rail tangents or admit an unqualified switch configuration.
"""

import copy
import hashlib
import json
import math

from tracktemplate.application.chair_pair_catalogue import (
    _TO_MAIN_BLOCK_BINDINGS,
    _verify_turnout_block_selection,
    CONTEXT_IDS,
    prepare_paired_catalogue,
)
from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.domain.chair_placement import place_paired_chair


def _require(condition, message):
    if not condition:
        raise ValueError("Private paired placement: " + message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def _host_context(module, document, configuration):
    records, data, objects = {}, {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        obj = document.getObject(config["host_object"])
        _require(obj is not None and not obj.Shape.isNull()
                 and obj.Shape.isValid(), "the canonical host is unavailable")
        host = module.turnout_host_alignment(obj)
        record = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in host["points"]],
            "headings": host["headings"], "stations": host["stations"],
            "total": host["total"], "toe_chainage": config["toe_chainage"],
            "orientation": config["orientation"], "handing": config["handing"],
        }
        records[side], data[side], objects[side] = record, host, obj
    return records, data, objects


def prepare_crossover_pairs(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Prepare all twenty source-bound placements or fail before creation.

    Return placement groups, per-position source witnesses, and a final
    host verifier. Catalogue bytes are independently reverified by the
    native adapter. The complete frozen source-context fingerprint binds
    the hand, switch, gauge, rail profile, stations and unshoved B4 timbers.
    A different context needs its own qualification; there is no fallback.
    """
    selections = {item.run: item
                  for item in prepare_paired_catalogue(contexts_path)}
    source_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    context = json.loads(signature)
    configuration = context["configuration"]
    _require(configuration["crossover_id"] == "XO-001",
             "only the qualified XO-001 context is supported")
    for prepared in selections.values():
        _require(prepared.metadata["source_context_sha256"] == source_hash,
                 "source configuration differs from the qualified context")
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(_encoded(hosts).encode()).hexdigest()
    _require(all(item.metadata["host_context_sha256"] == host_hash
                 for item in selections.values()),
             "host geometry differs from the qualified source context")
    timber_map = {item["stable_identity"]: item for item in timbers}
    owners = {
        configuration["turnout_" + side.lower() + "_id"]: side
        for side in ("A", "B")
    }
    rail_sides = {"main-side stock rail": "MS",
                  "turnout-side stock rail": "TS"}
    groups = {identity: [] for identity in CONTEXT_IDS}
    witnesses = {}
    for identity, position in sorted(positions.items()):
        if position["chair_code"] not in (11, 12):
            continue
        timber = timber_map[position["timber_identity"]]
        identifier = position["prototype_timber_identifier"]
        _require(identifier in ("S8", "S9", "S10", "S11", "S12")
                 and position["rail_name"] in rail_sides
                 and position["parent_turnout_identity"] in owners,
                 "unqualified paired source identity")
        side = owners[position["parent_turnout_identity"]]
        rail_side = rail_sides[position["rail_name"]]
        label = str(int(identifier[1:]) - 7) + "P"
        context_id = "RH-" + rail_side + "-" + label
        prepared = selections[context_id]
        recipe = prepared.context
        local_x = timber["source_configuration"]["local_x"]
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and recipe["station_mm"] == local_x
                 and recipe["timber_id"] == identifier
                 and recipe["chair_code"] == position["chair_code"]
                 and recipe["native_frame"]["common_timber_curving_applied"]
                 is False,
                 "paired recipe and source station disagree")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        station = config["toe_chainage"] + direction * local_x
        _require(0 <= station <= data[side]["total"],
                 "paired station lies outside its canonical host")
        point, heading = module.interpolate_alignment_station(data[side], station)
        travel = heading if direction > 0 else heading + math.pi
        placement = place_paired_chair(
            identity, position["rail_identity"], position["timber_identity"],
            (point.x, point.y), travel, base_z, config["track_gauge"] / 2,
            0.45,
        )
        groups[context_id].append(placement)
        witnesses[identity] = {
            "family": label, "context_id": context_id,
            "source_model_sha256": prepared.model_sha256,
            "source_context_sha256": recipe["context_sha256"],
            "source_station_mm": local_x, "host_station_mm": station,
            "host_context_sha256": host_hash,
            "source_parameters": recipe["context"],
            "placement_convention": "source-paired-common-timber-frame.v1",
            "physical_fit": "NOT_PROVED",
        }
    _require(len(witnesses) == 20
             and all(len(group) == 2 for group in groups.values()),
             "the complete twenty-position source set is required")

    def verify_hosts():
        current, _data, current_objects = _host_context(
            module, document, configuration,
        )
        _require(current == hosts and all(current_objects[key] is obj
                                        for key, obj in objects.items()),
                 "canonical host changed during paired preview")

    return ({key: tuple(values) for key, values in groups.items()},
            witnesses, verify_hosts)


# Fixed world points/headings from the independently qualified TO host.
# These are initial source-admission anchors, not a new railway tolerance.
_TO_MAIN_BLOCK_ANCHORS = (
    (752.1992217484609, 233.29095034178602, 0.860019268590973),
    (758.6614027938716, 240.92233061650074, 0.8767443015248171),
    (764.9941735483242, 248.6614420039795, 0.8929730238779185),
    (771.1972918007754, 256.50484198237444, 0.9101934398173377),
    (777.2702821615868, 264.44943746083834, 0.9266510297737188),
)


def preview_private_catalogue_turnout_block_chairs(
    module,
    source_document,
    turnout_id,
    catalogue_path,
    create_preview,
    *,
    classify_switch_exclusions=False,
):
    """Preview only five fixed LH main-side blocks, preserving all source state.

    Canonical key0 remains unresolved. Retained research +1 keys and zero
    offset belong to these pinned models only. The existing native adapter
    owns geometry reuse, one transaction, late verification and cleanup.
    """
    _require(type(classify_switch_exclusions) is bool,
             "the source switch exclusion option must be boolean")
    # The shared admission owner does not import any placement route.
    from tracktemplate.compatibility.chair_source_support import (
        _finite,
        _finite_rail_timber_support,
        _indexed,
        _require_context,
        _same_number,
    )
    from tracktemplate.compatibility.chair_reference_preview import (
        _context_shapes_and_verifier,
        _open_source_context,
    )

    _require(
        turnout_id == "TO-001" and callable(create_preview),
        "TO-001 and the native adapter are required",
    )
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module,
        source_document,
        turnout_id,
        "1P-5P",
    )
    context = json.loads(signature)
    _require_context(
        module, context, turnout_id, settings, plan, family="1P-5P"
    )
    config = context["configuration"]
    expected_config = {
        "handing": "Left-hand",
        "orientation": "Facing in host travel direction",
        "rail_geometry_revision": 2,
        "timber_geometry_revision": 2,
        "toe_chainage": 746.298,
        "template_width": 32.0,
        "chair_analysis_signature": "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379",
    }
    _require(
        all(
            config.get(key) == value
            and (type(value) not in (int, float) or _finite(config[key]))
            for key, value in expected_config.items()
        )
        and analysis.get("geometry_signature")
        == expected_config["chair_analysis_signature"]
        and settings.get("future_chair_embed_depth") == 0.2,
        "only the fixed LH facing TO-001 source is supported",
    )
    positions = _indexed(
        analysis.get("positions"), "stable_chair_position_identity"
    )
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
    _require(
        instances
        and all(
            _finite(p.get("base_z")) and p["base_z"] == 0.8
            for p in instances.values()
        ),
        "the source mounting plane differs",
    )

    def host_state():
        obj = source_document.getObject(config.get("host_object", ""))
        _require(
            obj is not None and not obj.Shape.isNull() and obj.Shape.isValid(),
            "the canonical host is unavailable",
        )
        data = module.turnout_host_alignment(obj)
        record = {
            "object_name": obj.Name,
            "points": [[p.x, p.y] for p in data["points"]],
            "headings": data["headings"],
            "stations": data["stations"],
            "total": data["total"],
        }
        _require(
            _finite(record["total"])
            and record["total"] > 0
            and all(_finite(v) for xy in record["points"] for v in xy)
            and all(
                _finite(v)
                for key in ("headings", "stations")
                for v in record[key]
            ),
            "nonfinite canonical host",
        )
        return obj, data, _encoded(record)

    host_object, host, host_signature = host_state()
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(
        module.rea_c10_timber_layout(dimensions, 32.0), "identifier"
    )
    stock_id = "TO-001:rail:main-side-stock-rail"
    switch_id = "TO-001:rail:curved-switch-and-closure-rail"
    names = tuple("S" + str(index) for index in range(8, 13))
    owners = {
        f"TO-001:chair:to-001-timber-{name.lower()}:main-side-stock-rail"
        for name in names
    }
    _require(
        {
            identity
            for identity, p in positions.items()
            if p.get("rail_identity") == stock_id
            and p.get("prototype_timber_identifier") in names
        }
        == owners,
        "the exact five main-side stock identities are required",
    )
    selected, groups, selections = [], {}, []
    bindings = dict(_TO_MAIN_BLOCK_BINDINGS)
    for number, (family, anchor) in enumerate(
        zip(bindings, _TO_MAIN_BLOCK_ANCHORS),
        1,
    ):
        name = names[number - 1]
        timber_id = "TO-001:timber:" + name
        identity = (
            f"TO-001:chair:to-001-timber-{name.lower()}:main-side-stock-rail"
        )
        _require(
            identity in excluded and timber_id in timber_map,
            "the selected block or its exclusion is absent",
        )
        position, timber = positions[identity], timber_map[timber_id]
        code, label = (11, "1P/2P") if number <= 2 else (12, "3P-11P")
        chair_family = (
            "switch-support chair" if number <= 2 else "switch-heel chair"
        )
        raw_class = (
            "source-derived prototype requirement"
            if number <= 2
            else "temporary visual approximation"
        )
        expected = {
            "stable_chair_position_identity": identity,
            "rail_identity": stock_id,
            "rail_name": "main-side stock rail",
            "rail_role": "stock rail",
            "timber_identity": timber_id,
            "prototype_timber_identifier": name,
            "timber_identifier": name,
            "parent_turnout_identity": "TO-001",
            "parent_crossover_identity": "",
            "handedness": "Left-hand",
            "chair_code": code,
            "chair_code_label": label,
            "chair_family": chair_family,
            "chair_subtype": (
                "REA 1P/2P PLR block-slide chair"
                if number <= 2
                else "REA 3P-5P PLR block-heel chair"
            ),
            "source_or_assumed_classification": raw_class,
            "assignment_status": "confirmed ordinary or turnout assignment",
            "assignment_complete_in_current_stage": True,
            "special_assignment_deferred": False,
            "deliberate_omission": False,
            "stale_signature_state": False,
            "validation_status": "validated",
            "key_direction_sign": 0,
            "key_orientation": "requires a configurable key-direction policy",
            "key_orientation_classification": "dimension requiring later confirmation",
        }
        _require(
            all(
                position.get(key) == value
                and (
                    type(value) not in (bool, int)
                    or type(position.get(key)) is type(value)
                )
                for key, value in expected.items()
            ),
            "the canonical block assignment or unresolved key differs",
        )
        original = excluded[identity]
        _require(
            original.get("rail_identity") == stock_id
            and original.get("timber_identity") == timber_id
            and original.get("chair_label") == label
            and original.get("chair_family") == chair_family
            and original.get("reason")
            == "chair family "
            + chair_family
            + " requires a dedicated physical definition"
            and original.get("deliberate_omission") is False
            and original.get("unresolved_special") is True,
            "the original block exclusion differs",
        )
        source = timber.get("source_configuration", {})
        nominal = layout.get(name, {})
        _require(
            timber.get("identifier")
            == timber.get("prototype_reference")
            == name
            and timber.get("parent_turnout_identity") == "TO-001"
            and timber.get("crossover_identity") == ""
            and timber.get("section") == "switch"
            and "extended_source_timber_identity" not in source
            and type(source.get("turnout_geometry_revision")) is int
            and source["turnout_geometry_revision"] == 2
            and source.get("crossing_suffix") == ""
            and source.get("source_note")
            == "published REA C-switch individual centre"
            and all(
                _finite(source.get(field))
                and source[field] == nominal.get(key)
                for field, key in (
                    ("local_x", "x"),
                    ("local_near_y", "near_y"),
                    ("local_far_y", "far_y"),
                    ("length_prototype_inches", "length_prototype_inches"),
                )
            )
            and source["local_x"] == bindings[family][3],
            "the fixed nominal switch timber differs",
        )
        axis = source.get("longitudinal_reference_axis")
        _require(
            isinstance(axis, (list, tuple))
            and len(axis) == 2
            and all(
                _same_number(a, b)
                for a, b in zip(axis, (0.7358589851037945, 0.6771348123099369))
            ),
            "the source longitudinal timber axis differs",
        )
        for rail_id, rail_name, role in (
            (stock_id, "main-side stock rail", "stock rail"),
            (
                switch_id,
                "curved switch and closure rail",
                "curved switch and closure rail",
            ),
        ):
            rail = rail_map.get(rail_id, {})
            rail_source = {
                "gauge_face": rail_name + " gauge face",
                "outer_face": rail_name + " outer face",
                "gauge_orientation_source": "mapped named turnout rail faces",
                "rail_geometry_revision": 2,
            }
            _require(
                rail.get("name") == rail_name
                and rail.get("rail_role") == role
                and rail.get("parent_turnout_identity") == "TO-001"
                and rail.get("parent_crossover_identity") == ""
                and rail.get("turnout_side") == ""
                and rail.get("source_configuration") == rail_source,
                "the named supporting rail binding differs",
            )
            if rail_id == stock_id:
                _require(
                    position.get("source_configuration")
                    == {"rail": rail_source, "timber": source},
                    "the selected position source binding differs",
                )
            _finite_rail_timber_support(
                position,
                rail,
                timber,
                label="main-side block",
                require=_require,
            )
        station = config["toe_chainage"] + source["local_x"]
        _require(0 <= station <= host["total"], "block lies outside its host")
        point, heading = module.interpolate_alignment_station(host, station)
        centre_y = (source["local_near_y"] + source["local_far_y"]) / 2
        centre = timber.get("centre")
        _require(
            all(
                _same_number(a, b)
                for a, b in zip((point.x, point.y, heading), anchor)
            )
            and _same_number(timber.get("host_chainage"), station)
            and _same_number(timber.get("local_rail_heading_radians"), heading)
            and isinstance(centre, (list, tuple))
            and len(centre) == 2
            and _same_number(centre[0], point.x - centre_y * math.sin(heading))
            and _same_number(
                centre[1], point.y + centre_y * math.cos(heading)
            ),
            "the initial fixed host anchor or nominal timber frame differs",
        )
        branch = (
            "switch"
            if source["local_x"] < dimensions["heel_lead"]
            else "closure"
        )
        _require(
            branch == ("closure" if number == 5 else "switch"),
            "the source heel branch differs",
        )
        prepared = prepare_catalogue_chair(
            catalogue_path, family, run="context-native-02"
        )
        _verify_turnout_block_selection(prepared, family, require=_require)
        selections.append(prepared)
        groups[family] = (
            place_paired_chair(
                identity,
                stock_id,
                timber_id,
                (point.x, point.y),
                heading,
                0.8,
                -config["track_gauge"] / 2,
                0.45,
            ),
        )
        model_hash, context_hash, fixing_hash, _station, _timber = bindings[
            family
        ]
        selected.append(
            {
                "position_id": identity,
                "family": family,
                "prototype_timber_identifier": name,
                "source_branch": branch,
                "source_station_mm": source["local_x"],
                "host_station_mm": station,
                "source_rail_code": 1,
                "source_hand": "LH",
                "source_model_sha256": model_hash,
                "source_context_sha256": context_hash,
                "fixing_recipe_sha256": fixing_hash,
                "original_position": copy.deepcopy(position),
                "physical_fit": "NOT_PROVED",
            }
        )
    switch_exclusions = {}

    def qualify_switches():
        from tracktemplate.compatibility.chair_switch_source_exclusions import (
            qualify_turnout_switch_exclusions,
        )

        return qualify_turnout_switch_exclusions(
            context, selected, family="1P-5P",
        )

    if classify_switch_exclusions:
        switch_exclusions = qualify_switches()
    shapes, verify_source = _context_shapes_and_verifier(
        module,
        source_document,
        turnout_id,
        "1P-5P",
        signature,
    )

    def verify_inputs():
        verify_source()
        current_object, _data, current_signature = host_state()
        _require(
            current_object is host_object
            and current_signature == host_signature,
            "canonical host changed during block preview",
        )
        for prepared in selections:
            verify_catalogue_sources(prepared)
        if classify_switch_exclusions:
            _require(qualify_switches() == switch_exclusions,
                     "source switch evidence changed during block preview")

    receipt = {
        "document_name": source_document.Name,
        "turnout_id": turnout_id,
        "source_context_signature": "sha256:"
        + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "selected_block_count": len(groups),
        "represented_source_position_count": len(groups),
        "selected_family_counts": dict.fromkeys(groups, 1),
        "selected_positions": selected,
        "remaining_positions": [
            copy.deepcopy(p)
            for identity, p in sorted(positions.items())
            if identity not in owners and identity not in switch_exclusions
        ],
        "original_analytical_exclusions": copy.deepcopy(
            plan["analytical_only"]
        ),
        "retained_research_key_direction_sign": 1,
        "retained_research_key_offset_mm": 0,
        "source_base_z_mm": 0.8,
        "source_document_mutation": False,
        "model_support_adjustments_applied": False,
        "limits": [
            "Five fixed LH main-side blocks only; empty companions remain unselected.",
            "Canonical key0 and original source classifications remain unchanged.",
            "Retained research +1 keys/zero offset do not resolve key policy.",
            "No native, GUI, physical-fit, production, export or phase acceptance.",
        ],
    }
    if classify_switch_exclusions:
        receipt.update(
            source_switch_exclusions=copy.deepcopy(switch_exclusions),
            source_switch_exclusion_count=len(switch_exclusions),
            unresolved_source_position_count=len(receipt["remaining_positions"]),
        )
    return create_preview(
        catalogue_path, groups, shapes, receipt, verify_inputs
    )
