"""Place separate fixed retained crossing assemblies on XO/TO records.

Templot 556b math_unit.pas selects one assembly on rail 3 with rail 2
as its companion. B15 preserves those rails as wing rails at X4-A and
vee rails at X6-C through X8-E. Canonical labels remain unchanged.
Source-informed, GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
"""

import copy
import hashlib
import json
import math

from tracktemplate.application.chair_crossing_pair_catalogue import (
    CROSSING_PAIR_CONTEXT_IDS,
    CROSSING_SPLIT_CONTEXT_IDS,
    _TO_CROSSING_BINDINGS,
    prepare_turnout_crossing_catalogue,
    verify_turnout_crossing_catalogue,
    prepare_crossing_pair_catalogue,
    prepare_crossing_split_catalogue,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.chair_placement import place_paired_chair


_SPECS = (
    ("X4-A", "AA", 24, 25, "AB",
     ("turnout-side wing rail", "main-side wing rail")),
    ("X6-C", "CD", 27, 26, "BB/BC",
     ("vee point rail", "vee splice rail")),
    ("X7-D", "DD", 27, 27, "CD",
     ("vee point rail", "vee splice rail")),
    ("X8-E", "EF", 28, 28, "EF",
     ("vee point rail", "vee splice rail")),
)
_INHERITED = (
    (("A", "X8-E"), "XO-001:INHERITED-LONG:A:001"),
    (("B", "X6-C"), "XO-001:INHERITED-LONG:B:005"),
    (("B", "X7-D"), "XO-001:INHERITED-LONG:B:006"),
    (("B", "X8-E"), "XO-001:INHERITED-LONG:B:007"),
)
_SPLIT_SPECS = (
    ("X3-X", "XA", 23,
     (("turnout-side wing rail", 23, "XA"),
      ("main-side wing rail", 23, "XA"))),
    ("X5-B", "BB", 26,
     (("vee point rail", 26, "BB/BC"),
      ("vee splice rail", 25, "AB"),
      ("turnout-side wing flare", 25, "AB"),
      ("main-side wing flare", 25, "AB"))),
)


def _require(condition, message):
    if not condition:
        raise ValueError("Private crossing pair placement: " + message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def prepare_crossing_pairs(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Return eight proper frames, source witnesses and late verification.

    Retained models already include crops, shears, rotations and base
    twist. Only the established common host transform is applied here.
    Inherited timbers retain their envelope identities and path stations.
    Catalogue revalidation remains at the native admission boundary.
    """
    prepared = prepare_crossing_pair_catalogue(contexts_path)
    specifications = tuple(
        (name, family, source_code,
         tuple((rail, code, label) for rail in rails))
        for name, family, source_code, code, label, rails in _SPECS
    )
    return _prepare_crossings(
        module, document, signature, positions, timbers, base_z, prepared,
        CROSSING_PAIR_CONTEXT_IDS, specifications,
    )


def prepare_crossing_splits(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Place four XA/BB assemblies for twelve source-qualified records.

    Templot 556b math_unit.pas:30944-30974 supplies XA wing constituents;
    31246-31296 supplies BB wing and vee constituents. B15 creates separate
    candidates for named rail segments (43470-43503). Its four XN knuckle
    records therefore remain excluded: continuity alone is not support
    evidence. Retained crops, shears and base twist are not reapplied.
    """
    return _prepare_crossings(
        module, document, signature, positions, timbers, base_z,
        prepare_crossing_split_catalogue(contexts_path),
        CROSSING_SPLIT_CONTEXT_IDS, _SPLIT_SPECS,
    )


def _prepare_crossings(
    module, document, signature, positions, timbers, base_z, prepared,
    context_ids, specifications,
):
    """Apply the shared fixed-source checks and proper common host frame."""
    _require(tuple(item.run for item in prepared) == context_ids,
             "all ordered crossing contexts are required")
    selections = {item.run: item for item in prepared}
    configuration = json.loads(signature)["configuration"]
    source_hash = hashlib.sha256(signature.encode()).hexdigest()
    _require(configuration["crossover_id"] == "XO-001"
             and all(item.metadata["source_context_sha256"] == source_hash
                     for item in prepared), "unqualified source context")
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(_encoded(hosts).encode()).hexdigest()
    _require(all(item.metadata["host_context_sha256"] == host_hash
                 for item in prepared), "unqualified host geometry")
    owners = {configuration["turnout_" + side.lower() + "_id"]: side
              for side in ("A", "B")}
    _require(owners == {"XO-001-A001": "A", "XO-001-B001": "B"},
             "canonical turnout owners differ")
    timber_map = {item["stable_identity"]: item for item in timbers}
    _require(len(timber_map) == len(timbers), "timber identities repeat")
    by_name = {item[0]: item[1:] for item in specifications}
    inherited = dict(_INHERITED)
    records = {}
    for identity, position in positions.items():
        name, rail = (position["prototype_timber_identifier"],
                      position["rail_name"])
        if name not in by_name:
            continue
        rail_specs = {item[0]: item[1:] for item in by_name[name][-1]}
        if rail not in rail_specs:
            continue
        code, label = rail_specs[rail]
        owner = position["parent_turnout_identity"]
        _require(owner in owners, "unqualified turnout owner")
        side = owners[owner]
        timber_id = inherited.get((side, name), f"XO-001:{side}:{name}")
        expected = ("XO-001:chair:" + timber_id.lower().replace(":", "-")
                    + ":" + rail.replace(" ", "-"))
        key = side, name, rail
        _require(key not in records and identity == expected
                 == position["stable_chair_position_identity"]
                 and position["timber_identity"] == timber_id
                 and position["rail_identity"]
                 == owner + ":rail:" + rail.replace(" ", "-")
                 and (position["chair_code"], position["chair_code_label"])
                 == (code, label)
                 and position["special_assignment_deferred"] is True
                 and position["deliberate_omission"] is False,
                 "canonical source ownership or assignment differs")
        records[key] = position
    expected = {(side, name, rail) for side in ("A", "B")
                for name, *_, rails in specifications for rail, *_ in rails}
    _require(set(records) == expected, "all qualified source records are required")
    frozen_records = _encoded([positions, timbers])
    groups = {name: [] for name in context_ids}
    witnesses, companions = {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and config["track_gauge"] == 16.5,
                 "only the qualified right-hand gauge is supported")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for name, family, code, rails in specifications:
            context_id = "RH-" + name
            selection = selections[context_id]
            recipe = selection.context
            owner, *mates = (records[side, name, rail] for rail, *_ in rails)
            source = timber_map[owner["timber_identity"]]["source_configuration"]
            is_inherited = (side, name) in inherited
            if is_inherited:
                _require(source.get("extended_source_timber_identity")
                         == f"XO-001:{side}:{name}",
                         "inherited timber has a different source")
            local_x = source["path_station" if is_inherited else "local_x"]
            _require(type(local_x) in (int, float) and math.isfinite(local_x)
                     and owner["source_configuration"]["timber"] == source
                     and all(mate["source_configuration"]["timber"] == source
                             for mate in mates)
                     and selection.label == recipe["family"] == family
                     and recipe["chair_code"] == code
                     and recipe["context_id"] == context_id
                     and recipe["timber_id"] == name
                     and recipe["station_mm"] == local_x
                     and recipe["native_frame"]["common_timber_curving_applied"]
                     is False, "qualified recipe and source timber disagree")
            station = config["toe_chainage"] + direction * local_x
            _require(0 <= station <= data[side]["total"],
                     "station lies outside its canonical host")
            point, heading = module.interpolate_alignment_station(data[side],
                                                                 station)
            travel = heading if direction > 0 else heading + math.pi
            identity = owner["stable_chair_position_identity"]
            mate_ids = [mate["stable_chair_position_identity"] for mate in mates]
            groups[context_id].append(place_paired_chair(
                identity, owner["rail_identity"], owner["timber_identity"],
                (point.x, point.y), travel, base_z, 8.25, 0.45,
            ))
            companions.update((mate_id, identity) for mate_id in mate_ids)
            witnesses[identity] = {
                "family": family, "source_chair_code": code,
                "context_id": context_id,
                "source_model_sha256": selection.model_sha256,
                "source_context_sha256": recipe["context_sha256"],
                "source_station_mm": local_x, "host_station_mm": station,
                "source_rail_code": 3, "mate_position_ids": mate_ids,
                "placement_convention": "source-paired-common-timber-frame.v1",
                "physical_fit": "NOT_PROVED",
            }

    def verify():
        current, _data, current_objects = _host_context(module, document,
                                                       configuration)
        _require(hashlib.sha256(_encoded(current).encode()).hexdigest()
                 == host_hash and all(current_objects[key] is value
                                      for key, value in objects.items()),
                 "canonical host changed during crossing preview")
        _require(_encoded([positions, timbers]) == frozen_records,
                 "source records changed during crossing preview")

    return ({name: tuple(sorted(values, key=lambda item: item.position_id))
             for name, values in groups.items()}, witnesses, companions, verify)


# Fixed source input qualifiers from the independent LH TO source packet.
# Each row: raw code/label, timber section/near/far/length, host XY/angle,
# and explicit owner/companion rail classifications. Expected output frames
# remain solely in the independent numeric fixture.
_TO_CROSSING_SOURCE_INPUTS = (
    (
        "XA",
        (
            23,
            "XA",
            "crossing wing front",
            -16.016718458769496,
            31.983281541230504,
            144.0,
            (858.2366736651227, 410.56392175080504),
            1.1966155659717186,
            (
                (
                    "turnout-side wing rail",
                    "wing rail",
                    "wing-rail chair",
                    "REA wing/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
                (
                    "main-side wing rail",
                    "wing rail",
                    "wing-rail chair",
                    "REA wing/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
            ),
        ),
    ),
    (
        "AA",
        (
            25,
            "AB",
            "crossing vee",
            -16.516718458769496,
            33.483281541230504,
            150.0,
            (861.8233424483664, 419.89847929685436),
            1.2110842303280676,
            (
                (
                    "turnout-side wing rail",
                    "wing rail",
                    "wing-rail chair",
                    "REA wing/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
                (
                    "main-side wing rail",
                    "wing rail",
                    "wing-rail chair",
                    "REA wing/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
            ),
        ),
    ),
    (
        "CD",
        (
            26,
            "BB/BC",
            "crossing vee",
            -16.516718458769496,
            35.483281541230504,
            156.0,
            (868.6026217204957, 438.71377440692686),
            1.238619179580687,
            (
                (
                    "vee point rail",
                    "vee point rail",
                    "vee support",
                    "REA vee/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
                (
                    "vee splice rail",
                    "vee splice rail",
                    "splice-rail support",
                    "REA splice/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
            ),
        ),
    ),
    (
        "DD",
        (
            27,
            "CD",
            "crossing vee",
            -16.016718458769496,
            35.983281541230504,
            156.0,
            (871.7982049964451, 448.1893542787174),
            1.2522433277530218,
            (
                (
                    "vee point rail",
                    "vee point rail",
                    "vee support",
                    "REA vee/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
                (
                    "vee splice rail",
                    "vee splice rail",
                    "splice-rail support",
                    "REA splice/crossing-chair subtype awaiting detailed special-chair "
                    "assignment",
                ),
            ),
        ),
    ),
)


def preview_private_catalogue_turnout_crossing_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Preview four fixed LH assemblies for eight unchanged source records.

    All eight canonical centres and finite rail paths must retain support.
    BB is excluded as a whole. Retained source geometry receives only the
    existing common host transform; canonical key0 remains unresolved.
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
        module, source_document, turnout_id, "Crossings",
    )
    context = json.loads(signature)
    _require_context(module, context, turnout_id, settings, plan,
                     family="Crossings")
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
    _require(len(positions) == 168
             and not instances.keys() & excluded.keys()
             and instances.keys() | excluded.keys() == positions.keys(),
             "the inherited plan must account for all 168 positions once")
    _require(instances and all(_finite(p.get("base_z")) and p["base_z"] == 0.8
                               for p in instances.values()),
             "the source mounting plane differs")
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0),
                      "identifier")

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
    source_inputs = dict(_TO_CROSSING_SOURCE_INPUTS)
    groups, selected, shared = {}, [], {}
    chosen = set()
    for family, binding in _TO_CROSSING_BINDINGS:
        (name, source_code, source_station, model_hash, context_hash,
         fixing_hash, _centres, _names) = binding
        (raw_code, raw_label, section, near, far, length, host_point,
         host_heading, rail_specs) = source_inputs[family]
        timber_id = "TO-001:timber:" + name
        identities = tuple(
            "TO-001:chair:to-001-timber-" + name.lower() + ":"
            + rail.replace(" ", "-") for rail, *_rest in rail_specs
        )
        rail_names = tuple(rail for rail, *_rest in rail_specs)
        _require(
            {key for key, p in positions.items()
             if p.get("prototype_timber_identifier") == name
             and p.get("rail_name") in rail_names} == set(identities)
            and all(key in excluded for key in identities)
            and timber_id in timber_map,
            "the exact eight unresolved crossing identities are required",
        )
        timber = timber_map[timber_id]
        source = timber.get("source_configuration", {})
        nominal = layout.get(name, {})
        note = ("REA wing-front crossing-chair spacing: 30 inches"
                if family == "XA" else
                "REA vee-rail crossing-chair spacing: 30 inches")
        _require(
            timber.get("identifier") == timber.get("prototype_reference")
            == name and timber.get("parent_turnout_identity") == "TO-001"
            and timber.get("crossover_identity") == ""
            and timber.get("section") == section
            and "extended_source_timber_identity" not in source
            and type(source.get("turnout_geometry_revision")) is int
            and source["turnout_geometry_revision"] == 2
            and source.get("crossing_suffix") == name[-1]
            and source.get("source_note") == note
            and all(_finite(source.get(field))
                    and source[field] == nominal.get(key) == expected
                    for field, key, expected in (
                        ("local_x", "x", source_station),
                        ("local_near_y", "near_y", near),
                        ("local_far_y", "far_y", far),
                        ("length_prototype_inches", "length_prototype_inches",
                         length),
                    )), "the fixed nominal crossing timber differs",
        )
        axis = source.get("longitudinal_reference_axis")
        _require(isinstance(axis, (list, tuple)) and len(axis) == 2
                 and all(_same_number(a, b) for a, b in zip(
                     axis, (0.7358589851037945, 0.6771348123099369))),
                 "the source longitudinal timber axis differs")
        for identity, (rail_name, rail_role, chair_family, subtype) in zip(
            identities, rail_specs,
        ):
            rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
            position = positions[identity]
            expected = {
                "stable_chair_position_identity": identity,
                "rail_identity": rail_id, "rail_name": rail_name,
                "rail_role": rail_role, "timber_identity": timber_id,
                "prototype_timber_identifier": name,
                "timber_identifier": name,
                "parent_turnout_identity": "TO-001",
                "parent_crossover_identity": "", "handedness": "Left-hand",
                "handedness_classification": "source-derived prototype requirement",
                "chair_code": raw_code, "chair_code_label": raw_label,
                "chair_family": chair_family, "chair_subtype": subtype,
                "source_or_assumed_classification": "temporary visual approximation",
                "assignment_status": "deferred to special-chair assignment",
                "assignment_complete_in_current_stage": False,
                "special_assignment_deferred": True,
                "deliberate_omission": False, "stale_signature_state": False,
                "validation_status": "Advisory", "key_direction_sign": 0,
                "key_orientation": "requires confirmation from the final special-chair subtype and keying arrangement",
                "key_orientation_classification": "dimension requiring later confirmation",
            }
            _require(all(position.get(key) == value
                         and (type(value) not in (bool, int)
                              or type(position.get(key)) is type(value))
                         for key, value in expected.items()),
                     "the canonical crossing assignment or key differs")
            original = excluded[identity]
            _require(original.get("rail_identity") == rail_id
                     and original.get("timber_identity") == timber_id
                     and original.get("chair_label") == raw_label
                     and original.get("chair_family") == chair_family
                     and original.get("deliberate_omission") is False
                     and original.get("unresolved_special") is True,
                     "the original crossing exclusion differs")
            rail = rail_map.get(rail_id, {})
            rail_source = {
                "gauge_face": rail_name + " gauge face",
                "outer_face": rail_name + " outer face",
                "gauge_orientation_source": "mapped named turnout rail faces",
                "rail_geometry_revision": 2,
            }
            _require(
                rail.get("name") == rail_name
                and rail.get("rail_role") == rail_role
                and rail.get("parent_turnout_identity") == "TO-001"
                and rail.get("parent_crossover_identity") == ""
                and rail.get("turnout_side") == ""
                and rail.get("source_configuration") == rail_source
                and position.get("source_configuration")
                == {"rail": rail_source, "timber": source},
                "the named supporting rail or source binding differs",
            )
            # Shared rail identity does not replace support on each timber.
            _finite_rail_timber_support(position, rail, timber,
                                        label=family, require=_require)
        station = config["toe_chainage"] + source_station
        _require(0 <= station <= host["total"],
                 "crossing lies outside its canonical host")
        point, heading = module.interpolate_alignment_station(host, station)
        centre_y = (near + far) / 2
        centre = timber.get("centre")
        _require(
            all(_same_number(a, b) for a, b in zip(
                (point.x, point.y, heading), (*host_point, host_heading)))
            and _same_number(timber.get("host_chainage"), station)
            and _same_number(timber.get("local_rail_heading_radians"), heading)
            and isinstance(centre, (list, tuple)) and len(centre) == 2
            and _same_number(centre[0], point.x - centre_y * math.sin(heading))
            and _same_number(centre[1], point.y + centre_y * math.cos(heading)),
            "the initial fixed host anchor or nominal timber frame differs",
        )
        owner, companion = identities
        groups[family] = (place_paired_chair(
            owner, positions[owner]["rail_identity"], timber_id,
            (point.x, point.y), heading, 0.8, 8.25, 0.45,
        ),)
        chosen.update(identities)
        shared[companion] = owner
        selected.append({
            "position_id": owner, "family": family, "source_hand": "LH",
            "prototype_timber_identifier": name, "source_rail_code": 3,
            "source_chair_code": source_code,
            "source_station_mm": source_station, "host_station_mm": station,
            "source_model_sha256": model_hash,
            "source_context_sha256": context_hash,
            "fixing_recipe_sha256": fixing_hash,
            "original_position": copy.deepcopy(positions[owner]),
            "original_companion": copy.deepcopy(positions[companion]),
            "physical_fit": "NOT_PROVED",
        })
    prepared = prepare_turnout_crossing_catalogue(catalogue_path)
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "Crossings", signature,
    )

    def verify_inputs():
        verify_source()
        current_object, _data, current_signature = host_state()
        _require(current_object is host_object
                 and current_signature == host_signature,
                 "canonical host changed during crossing preview")
        verify_turnout_crossing_catalogue(prepared)

    receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:"
        + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "selected_crossing_count": 4, "represented_source_position_count": 8,
        "selected_family_counts": dict.fromkeys(groups, 1),
        "selected_positions": selected, "shared_supports": shared,
        "remaining_positions": [copy.deepcopy(p)
                                for identity, p in sorted(positions.items())
                                if identity not in chosen],
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "retained_research_key_direction_sign": 1,
        "retained_research_key_offset_mm": 0, "source_base_z_mm": 0.8,
        "source_document_mutation": False,
        "model_support_adjustments_applied": False,
        "limits": [
            "Four fixed LH XA/AA/CD/DD assemblies; eight explicit identities.",
            "Whole BB and optional AA attachments remain excluded.",
            "Canonical key0 and all original classifications remain unchanged.",
            "Retained research +1 key/zero offset does not resolve key policy.",
            "No native, GUI, physical-fit, production, export or phase acceptance.",
        ],
    }
    return create_preview(catalogue_path, groups, shapes, receipt, verify_inputs)
