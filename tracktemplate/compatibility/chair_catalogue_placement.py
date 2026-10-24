"""Place retained P and S1J references at confirmed C10 positions.

This private snapshot leaves the inherited physical plan and all existing
placement routes unchanged. Its source frame and datum are read from the
current analysis; retained geometry supplies no new railway decisions.
"""

import copy
import hashlib
import json
import math
from numbers import Real

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_reference_preview import (
    _context_shapes_and_verifier,
    _open_source_context,
    _recover_positions,
    _select_s1j_positions,
    _select_s1_s1j_positions,
)
from tracktemplate.domain.chair_placement import (
    PPlacement,
    recover_reference_frame,
)


# Exact compatibility values in the accepted fixed Code 75 source profile.
# They restrict this retained model; they do not introduce another standard.
_CODE75_PROFILE = (
    ("profile_id", "Templot556b-CL-EMGS-S4Soc-Code75-revA"),
    ("operator_label", "Templot C&L / EMGS / S4Soc Code 75 bullhead rev:A"),
    ("source_revision", "Templot5 556b, dxf_unit.pas init_rail_section"),
    ("scale_mm_per_foot", 4.0),
    ("vertical_rail", True),
    ("rail_depth_mm", 1.9),
    ("rail_head_width_mm", 0.9),
    ("rail_corner_radius_mm", 0.15),
    ("rail_foot_width_mm", 0.9),
    ("rail_fish_angle", 1.5),
    ("rail_web_top_from_top_mm", 0.8),
    ("rail_web_bottom_from_top_mm", 1.25),
    ("rail_web_thickness_mm", 0.35),
    ("rail_head_depth_mm", 0.5),
    ("rail_foot_depth_mm", 0.3499999999999999),
    ("rail_web_face_top_from_bottom_mm", 1.2166666666666666),
    ("rail_web_face_bottom_from_bottom_mm", 0.5333333333333332),
)
_ORIGINAL_P_REASON = (
    "chair family slide chair requires a dedicated physical definition"
)
_KEY_ORIENTATION = "requires a configurable key-direction policy"
_KEY_CLASSIFICATION = "dimension requiring later confirmation"


def _require(condition, message, *, family="P"):
    if not condition:
        raise ValueError(f"Private {family} placement: " + message)


def _indexed(records, field):
    _require(isinstance(records, list), "source records must be a list")
    result = {}
    for record in records:
        _require(isinstance(record, dict), "source record is not a mapping")
        identity = record.get(field)
        _require(isinstance(identity, str) and identity.strip()
                 and identity not in result, "source identity is ambiguous")
        result[identity] = record
    return result


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _require_context(
    module, context, turnout_id, settings, plan, *, family="P",
):
    """Refuse contexts beyond the retained fixed model's inputs."""
    config = context["configuration"]
    _require(
        context["kind"] == "turnout"
        and config.get("turnout_id") == turnout_id
        and config.get("size") == module.TURNOUT_SIZE_C10
        and module.TURNOUT_DEFAULT_SCALE == 76.2
        and plan.get("entity_kind") == "turnout"
        and plan.get("entity_id") == turnout_id,
        "one C10 turnout at 1:76.2 is required", family=family,
    )
    for field, expected in (("track_gauge", 16.5), ("flangeway", 1.0)):
        _require(_finite(config.get(field)) and config[field] == expected,
                 "unsupported " + field, family=family)
    _require_model_inputs(settings, plan, family=family)


def _require_model_inputs(settings, plan, *, family="P"):
    """Keep the complete fixed rail profile and source embedding binding."""
    profile = plan.get("rail_profile")
    expected_profile = dict(_CODE75_PROFILE)
    _require(isinstance(profile, dict) and profile == expected_profile
             and profile.get("vertical_rail") is True,
             "the complete fixed Code 75 revA profile is required",
             family=family)
    for field, expected in _CODE75_PROFILE:
        if type(expected) is float:
            _require(_finite(profile[field]), "invalid profile " + field,
                     family=family)
    _require(settings.get("rail_profile_id") == expected_profile["profile_id"],
             "analysis rail profile disagrees", family=family)
    _require(isinstance(plan.get("settings"), dict)
             and plan["settings"].get("embed_depth")
             == settings.get("future_chair_embed_depth")
             and _finite(settings.get("future_chair_embed_depth")),
             "source embedding settings disagree", family=family)


def _require_p_crossover_context(
    module, context, crossover_id, settings, plan,
):
    """Bind compatible P inputs to the two named crossover constituents."""
    config = context["configuration"]
    _require(
        context["kind"] == "crossover"
        and config.get("crossover_id") == crossover_id
        and config.get("size") == module.TURNOUT_SIZE_C10
        and module.TURNOUT_DEFAULT_SCALE == 76.2
        and plan.get("entity_kind") == "crossover"
        and plan.get("entity_id") == crossover_id,
        "one C10 crossover at 1:76.2 is required",
    )
    for field, expected in (("track_gauge", 16.5), ("flangeway", 1.0)):
        _require(_finite(config.get(field)) and config[field] == expected,
                 "unsupported crossover " + field)
    thickness = config.get("template_thickness")
    _require(_finite(thickness), "invalid crossover template thickness")
    owners = {}
    for side in ("A", "B"):
        prefix = "turnout_" + side.lower()
        constituent = config.get(prefix + "_config")
        _require(isinstance(constituent, dict)
                 and constituent.get("size") == module.TURNOUT_SIZE_C10,
                 "both crossover constituents must be C10")
        identity = constituent.get("turnout_id")
        _require(isinstance(identity, str) and identity.strip()
                 and identity == config.get(prefix + "_id")
                 and identity not in owners,
                 "crossover constituent identities disagree")
        for field, expected in (("track_gauge", 16.5), ("flangeway", 1.0)):
            _require(_finite(constituent.get(field))
                     and constituent[field] == expected,
                     "unsupported constituent " + field)
        _require(_finite(constituent.get("template_thickness"))
                 and constituent["template_thickness"] == thickness,
                 "crossover constituent mounting datums disagree")
        owners[identity] = side
    _require_model_inputs(settings, plan)
    return owners


def _require_p_assignment(
    module, position, rail, timber, turnout_id,
    *, crossover_id=None, turnout_side=None,
):
    """Admit only the existing explicit S1-S7 stock-rail P assignment."""
    identifier = position.get("prototype_timber_identifier")
    _require(
        type(position.get("chair_code")) is int
        and position["chair_code"] == 2
        and position.get("chair_code_label") == "P"
        and position.get("chair_family") == module.CHAIR_FAMILY_SLIDE
        and position.get("chair_subtype") == "REA P slide chair"
        and position.get("assignment_status")
        == module.CHAIR_ASSIGNMENT_CONFIRMED
        and position.get("assignment_complete_in_current_stage") is True
        and position.get("deliberate_omission") is False
        and position.get("special_assignment_deferred") is False
        and position.get("stale_signature_state") is False
        and position.get("validation_status") == "validated",
        "P assignment is incomplete, stale or unsupported",
    )
    _require(
        identifier in ("S1", "S2", "S3", "S4", "S5", "S6", "S7")
        and position.get("timber_identifier") == identifier
        and timber.get("identifier") == identifier
        and timber.get("prototype_reference") == identifier
        and timber.get("section") == "switch"
        and position.get("rail_role") == "stock rail"
        and rail.get("rail_role") == "stock rail"
        and position.get("rail_name") == rail.get("name")
        and rail.get("name") in (
            "main-side stock rail", "turnout-side stock rail",
        ),
        "P needs its named C-switch stock rail and timber",
    )
    if crossover_id is None:
        _require(
            all(record.get("parent_turnout_identity") == turnout_id
                for record in (position, rail, timber))
            and not position.get("parent_crossover_identity")
            and not rail.get("parent_crossover_identity")
            and not timber.get("crossover_identity"),
            "P source ownership disagrees",
        )
    else:
        _require(
            all(record.get("parent_turnout_identity") == turnout_id
                for record in (position, rail, timber))
            and position.get("parent_crossover_identity") == crossover_id
            and rail.get("parent_crossover_identity") == crossover_id
            and timber.get("crossover_identity") == crossover_id
            and turnout_side in ("A", "B")
            and rail.get("turnout_side") == turnout_side
            and timber.get("turnout_side") == turnout_side,
            "P crossover source ownership disagrees",
        )
    footprint = position.get("chair_footprint_parameters")
    _require(
        position.get("source_or_assumed_classification")
        == module.CHAIR_CLASS_SOURCE
        and isinstance(footprint, dict)
        and footprint.get("dimension_classification")
        == module.CHAIR_CLASS_SOURCE,
        "P source dimensions are unresolved",
    )
    _require(
        type(position.get("key_direction_sign")) is int
        and position["key_direction_sign"] == 0
        and position.get("key_orientation") == _KEY_ORIENTATION
        and position.get("key_orientation_classification")
        == _KEY_CLASSIFICATION,
        "the retained P model does not implement a key-direction policy",
    )


def _select_p_positions(
    module, analysis, plan, rails, timbers, turnout_id,
    *, crossover_owners=None,
):
    """Partition every input ID without changing the inherited exclusions."""
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rail_by_id = _indexed(rails, "stable_identity")
    timber_by_id = _indexed(timbers, "stable_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    excluded = _indexed(plan.get("analytical_only"),
                        "chair_position_identity")
    _require(not instances.keys() & excluded.keys()
             and instances.keys() | excluded.keys() == positions.keys(),
             "the inherited plan does not account for every position")
    datums = [item.get("base_z") for item in instances.values()]
    _require(datums and all(_finite(value) for value in datums)
             and all(value == datums[0] for value in datums),
             "source placement datum is missing or inconsistent")
    placements, selected, remaining = [], [], []
    for identity, position in sorted(positions.items()):
        rail_id, timber_id = (position.get("rail_identity"),
                              position.get("timber_identity"))
        _require(isinstance(rail_id, str) and isinstance(timber_id, str)
                 and rail_id in rail_by_id and timber_id in timber_by_id,
                 "the named rail or timber source is missing")
        original = instances.get(identity, excluded.get(identity))
        _require(
            original.get("rail_identity") == rail_id
            and original.get("timber_identity") == timber_id
            and original.get("chair_label") == position.get("chair_code_label")
            and type(position.get("chair_code")) is int,
            "plan and analysis identities or assignments disagree",
        )
        if identity in instances:
            _require(type(original.get("chair_code")) is int
                     and original["chair_code"] == position["chair_code"],
                     "plan chair code disagrees")
        else:
            _require(isinstance(original.get("reason"), str)
                     and original["reason"].strip(),
                     "an original exclusion has no reason")
        if position["chair_code"] != 2:
            _require(position.get("chair_code_label") != "P",
                     "P label and code disagree")
            remaining.append({
                "position_id": identity, "rail_id": rail_id,
                "timber_id": timber_id, "chair_code": position["chair_code"],
                "reason": original.get(
                    "reason", "Only retained P references are selected.",
                ),
            })
            continue
        _require(
            identity in excluded and original.get("reason")
            == _ORIGINAL_P_REASON
            and original.get("chair_family") == module.CHAIR_FAMILY_SLIDE
            and original.get("deliberate_omission") is False,
            "P has another inherited exclusion or physical-plan status",
        )
        rail, timber = rail_by_id[rail_id], timber_by_id[timber_id]
        if crossover_owners is None:
            _require_p_assignment(module, position, rail, timber, turnout_id)
        else:
            owner = position.get("parent_turnout_identity")
            _require(isinstance(owner, str) and owner in crossover_owners,
                     "P is not owned by a named crossover constituent")
            _require_p_assignment(
                module, position, rail, timber, owner,
                crossover_id=turnout_id,
                turnout_side=crossover_owners[owner],
            )
        frame = recover_reference_frame(
            position.get("centre_point"), position.get("local_rail_tangent"),
            rail.get("gauge_face_points"), rail.get("outer_face_points"),
        )
        placement = PPlacement(
            position_id=identity, rail_id=rail_id, timber_id=timber_id,
            origin_mm=(*position["centre_point"], datums[0]),
            x_axis=frame["x_axis"], y_axis=frame["y_axis"],
        )
        placements.append(placement)
        selected.append({
            "position_id": identity, "rail_id": rail_id,
            "timber_id": timber_id, "chair_code": 2,
            "prototype_timber_identifier": (
                position["prototype_timber_identifier"]
            ),
            "original_exclusion": copy.deepcopy(original),
            "frame_evidence": frame["witness"],
            "key_direction_sign": position["key_direction_sign"],
            "key_orientation": position["key_orientation"],
            "key_orientation_classification": (
                position["key_orientation_classification"]
            ),
        })
    _require(placements, "no confirmed compatible P positions are available")
    return tuple(placements), selected, remaining, datums[0]


def preview_private_catalogue_p_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Create a separate private P snapshot; preserve the complete source.

    Placement and source compatibility are checked before native creation.
    The adapter checks catalogue bytes and the unchanged source inside its
    transaction. This does not admit P to the inherited physical plan.
    """
    return _preview_private_catalogue_p_chairs(
        module, source_document, turnout_id, catalogue_path, create_preview,
        entity_kind="turnout",
    )


def preview_private_catalogue_p_crossover_chairs(
    module, source_document, crossover_id, catalogue_path, create_preview,
):
    """Inspect retained P chairs on one current C10 crossover privately.

    Require two compatible C10 constituents and current applied B4 timbers.
    Reuse unchanged P geometry at confirmed stock-rail assignments in a
    separate unsaved document. Preserve the source and physical exclusions;
    no fit, production, persistence, export or rights acceptance follows.
    """
    return _preview_private_catalogue_p_chairs(
        module, source_document, crossover_id, catalogue_path, create_preview,
        entity_kind="crossover",
    )


def _preview_private_catalogue_p_chairs(
    module, source_document, entity_id, catalogue_path, create_preview,
    *, entity_kind,
):
    """Bind unchanged P components to one complete current source snapshot."""
    _require(callable(create_preview), "the native adapter is unavailable")
    signature_text, analysis, settings, plan, rails, timbers = (
        _open_source_context(
            module, source_document, entity_id, "P", entity_kind=entity_kind,
        )
    )
    context = json.loads(signature_text)
    owners = None
    if entity_kind == "turnout":
        _require_context(module, context, entity_id, settings, plan)
    else:
        owners = _require_p_crossover_context(
            module, context, entity_id, settings, plan,
        )
    placements, selected, remaining, base_z = _select_p_positions(
        module, analysis, plan, rails, timbers, entity_id,
        crossover_owners=owners,
    )
    context_shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, entity_id, "P", signature_text,
        entity_kind=entity_kind,
    )
    source_receipt = {
        "document_name": source_document.Name, entity_kind + "_id": entity_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature_text.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(analysis["positions"]),
        "selected_p_count": len(placements), "selected_positions": selected,
        "coverage_summary": (
            f"{len(placements)} P references; "
            f"{len(analysis['positions'])} source positions accounted for"
        ),
        "remaining_positions": remaining,
        "original_analytical_exclusions": copy.deepcopy(
            plan["analytical_only"],
        ),
        "source_base_z_mm": base_z,
        "embed_depth_mm": settings["future_chair_embed_depth"],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "context_kind": "derived rail and timber wires",
        "source_document_mutation": False,
        "limits": [
            "Private fixed-reference placement; no physical fit acceptance.",
            "The source key-direction policy remains unresolved.",
            "All inherited physical exclusions and placement routes "
            "remain unchanged.",
            "No production, export, persistence or live-update authority.",
        ],
    }
    if entity_kind == "crossover":
        source_receipt["source_kind"] = "crossover"
        source_receipt["timber_context"] = "current B4 resolved timbers"
    return create_preview(
        catalogue_path, placements, context_shapes, source_receipt,
        verify_source,
    )


def _whole_crossover_records(module, analysis, rails, timbers, crossover_id):
    """Validate every source record before interpreting an exclusion."""
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rail_by_id = _indexed(rails, "stable_identity")
    timber_by_id = _indexed(timbers, "stable_identity")
    for position in positions.values():
        code = position.get("chair_code")
        _require(type(code) is int and code in (
            0, 1, 2, 5, 7, 11, 12, 15, 21, 22, 23, 24, 25, 26, 27, 28,
        ), "unsupported whole-crossover chair code")
        label = "" if code == 0 else module.CHAIR_CODE_CATALOG[code]["label"]
        _require(position.get("chair_code_label") == label,
                 "whole-crossover label and code disagree")
        rail = rail_by_id.get(position.get("rail_identity"))
        timber = timber_by_id.get(position.get("timber_identity"))
        _require(rail is not None and timber is not None,
                 "the named rail or timber source is missing")
        _require(
            position.get("parent_crossover_identity") == crossover_id
            and rail.get("parent_crossover_identity") == crossover_id
            and timber.get("crossover_identity") == crossover_id
            and position.get("rail_name") == rail.get("name")
            and position.get("rail_role") == rail.get("rail_role")
            and position.get("parent_turnout_identity")
            == rail.get("parent_turnout_identity")
            and position.get("timber_identifier") == timber.get("identifier")
            and position.get("stale_signature_state") is False,
            "whole-crossover source ownership is stale or inconsistent",
        )
        for field in ("centre_point", "local_rail_tangent"):
            values = position.get(field)
            _require(isinstance(values, (list, tuple)) and len(values) == 2
                     and all(_finite(value) for value in values),
                     "invalid whole-crossover " + field)
        _require(type(position.get("key_direction_sign")) is int
                 and position["key_direction_sign"] == 0,
                 "the retained models have no resolved key-direction policy")
        if code == 0:
            _require(position.get("deliberate_omission") is True
                     and position.get("special_assignment_deferred") is False
                     and position.get("assignment_status")
                     == module.CHAIR_ASSIGNMENT_OMITTED,
                     "shared support assignment is not confirmed")
        elif code in (1, 2, 7, 11, 12):
            _require(position.get("deliberate_omission") is False
                     and position.get("special_assignment_deferred") is False
                     and position.get("assignment_complete_in_current_stage")
                     is True
                     and position.get("assignment_status")
                     == module.CHAIR_ASSIGNMENT_CONFIRMED,
                     "single-rail or block assignment is not confirmed")
            if code in (1, 7):
                family = module.CHAIR_CODE_CATALOG[code]["family"]
                _require(position.get("chair_family") == family
                         and position.get("chair_footprint_parameters", {}).get(
                             "dimension_classification")
                         == module.CHAIR_CLASS_SOURCE,
                         "single-rail family or source dimensions disagree")
                orientation = (_KEY_ORIENTATION if code == 1 else
                               "towards the adjacent rail joint; exact direction "
                               "sign requires stored joint chainage")
                classification = (_KEY_CLASSIFICATION if code == 1
                                  else module.CHAIR_CLASS_SOURCE)
                _require(position.get("key_orientation") == orientation
                         and position.get("key_orientation_classification")
                         == classification,
                         "single-rail key evidence disagrees")
        else:
            _require(position.get("deliberate_omission") is False
                     and position.get("special_assignment_deferred") is True
                     and position.get("assignment_status")
                     == module.CHAIR_ASSIGNMENT_DEFERRED_SPECIAL,
                     "special assignment has no supported exclusion")
            if code == 5:
                _require(position.get("chair_family") == module.CHAIR_FAMILY_BRIDGE,
                         "deferred bridge family disagrees")
            else:
                family, subtype, expected_code = (
                    module._chair_crossing_deferred_assignment(
                        position.get("prototype_timber_identifier"), timber, rail,
                    )
                )
                _require((position.get("chair_family"),
                          position.get("chair_subtype"), code)
                         == (family, subtype, expected_code),
                         "deferred crossing source assignment disagrees")
    return positions


def _shared_stock_support(position, positions):
    """Link the source's deliberate switch omission to its named stock rail."""
    names = {
        "curved switch and closure rail": "main-side stock rail",
        "straight switch and closure rail": "turnout-side stock rail",
    }
    name = names.get(position.get("rail_name"))
    _require(name is not None, "shared switch rail name is unsupported")
    matches = [item for item in positions.values()
               if item.get("rail_name") == name
               and item.get("timber_identity") == position["timber_identity"]
               and item.get("parent_turnout_identity")
               == position["parent_turnout_identity"]
               and item.get("chair_code") in (2, 11, 12)]
    _require(len(matches) == 1, "shared support owner is ambiguous or absent")
    return matches[0]


def _block_context_exclusion(position, mate, prepared):
    """Describe the missing qualification without comparing unlike frames."""
    recipe = prepared.metadata["native_record"]["source_recipe"]
    _require(recipe.get("sample_kind") == "fixture_timber"
             and recipe.get("timber_id")
             == position.get("prototype_timber_identifier")
             and recipe.get("chair_code") == position["chair_code"],
             "the retained block context does not identify this support")
    source_angle = recipe["context"]["aq_k_rad"]
    first, second = (position["local_rail_tangent"],
                     mate["local_rail_tangent"])
    _require(_finite(source_angle) and all(
        abs(math.hypot(*axis) - 1.0) <= 32 * math.ulp(1.0)
        for axis in (first, second)
    ), "block context has an invalid rail direction")
    return {
        "retained_family": prepared.label,
        "source_model_sha256": prepared.model_sha256,
        "source_context_sha256": prepared.context["context_sha256"],
        "retained_uncurved_gauge_face_angle_rad": source_angle,
        "target_sampled_world_midline_tangents": [first, second],
        "comparison": "different reference frames; no incompatibility inference",
        "physical_fit": "NOT_PROVED",
        "mate_position_id": mate["stable_chair_position_identity"],
    }


def preview_private_catalogue_crossover_chairs(
    module, source_document, crossover_id, catalogue_path, create_preview,
    *, paired_contexts_path=None,
):
    """Preview supported retained chairs with complete crossover accounting.

    Reuse existing S1, S1J and P placements. Keep deferred assignments,
    unqualified paired references and deliberate shared omissions visible
    in the receipt. An explicit frozen supplement admits all twenty paired
    source contexts. No source assignment, shape or key policy is changed.
    Invalid or newly unsupported evidence fails before native creation.
    """
    _require(callable(create_preview), "the native adapter is unavailable")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, crossover_id, "whole crossover",
        entity_kind="crossover",
    )
    owners = _require_p_crossover_context(
        module, json.loads(signature), crossover_id, settings, plan,
    )
    positions = _whole_crossover_records(
        module, analysis, rails, timbers, crossover_id,
    )
    first, second, remaining = _select_s1_s1j_positions(module, analysis, plan)
    recovered = []
    families = {}
    for family, code, placements in (("S1", 1, first), ("S1J", 7, second)):
        placements, remaining, records = _recover_positions(
            module, analysis, plan, rails, timbers, placements, remaining, code,
        )
        _require({item.position_id for item in placements} == {
            identity for identity, position in positions.items()
            if position["chair_code"] == code
        }, "a confirmed single-rail position has no supported frame")
        families[family] = placements
        recovered.extend(records)
    families["P"], _selected_p, _remaining_p, base_z = _select_p_positions(
        module, analysis, plan, rails, timbers, crossover_id,
        crossover_owners=owners,
    )
    instances = _indexed(plan["instances"], "chair_position_identity")
    originals = _indexed(plan["analytical_only"], "chair_position_identity")
    shared = {
        identity: _shared_stock_support(position, positions)
        for identity, position in positions.items()
        if position["deliberate_omission"]
    }
    pair_witnesses = {}
    verify_hosts = None
    if paired_contexts_path is not None:
        from tracktemplate.compatibility.chair_pair_placement import (
            prepare_crossover_pairs,
        )
        pairs, pair_witnesses, verify_hosts = prepare_crossover_pairs(
            module, source_document, signature, positions, timbers, base_z,
            paired_contexts_path,
        )
        families.update(pairs)
    selected_ids = {item.position_id for values in families.values()
                    for item in values}
    selected, excluded, preparations = [], [], {}
    for identity, position in sorted(positions.items()):
        code = position["chair_code"]
        record = {
            "position_id": identity, "rail_id": position["rail_identity"],
            "timber_id": position["timber_identity"], "chair_code": code,
            "chair_label": position["chair_code_label"],
            "original_exclusion": copy.deepcopy(originals.get(identity)),
            **{key: position[key] for key in (
                "key_direction_sign", "key_orientation",
                "key_orientation_classification",
            )},
        }
        if identity in selected_ids:
            if identity in instances:
                _require(instances[identity].get("centre_point")
                         == position.get("centre_point"),
                         "selected plan centre differs from its source")
            record.update(family=position["chair_code_label"],
                          original_instance=copy.deepcopy(
                              instances.get(identity)))
            if identity in pair_witnesses:
                mates = [key for key, owner in shared.items()
                         if owner["stable_chair_position_identity"] == identity]
                _require(len(mates) == 1,
                         "paired support has no unique shared rail")
                record.update(pair_witnesses[identity],
                              mate_position_id=mates[0])
            selected.append(record)
            continue
        _require(identity in originals, "excluded position has no source reason")
        if code == 0:
            owner_id = shared[identity]["stable_chair_position_identity"]
            record.update(
                exclusion_kind="confirmed-no-separate-chair",
                reason=position["chair_subtype"],
                supporting_position_id=owner_id,
                supporting_assembly_placed=owner_id in selected_ids,
            )
        elif code in (11, 12):
            identifier = position.get("prototype_timber_identifier")
            _require(identifier in ("S8", "S9", "S10", "S11", "S12"),
                     "block support has no retained C-switch recipe")
            label = str(int(identifier[1:]) - 7) + "P"
            if label not in preparations:
                preparations[label] = prepare_catalogue_chair(
                    catalogue_path, label, run="context-native-02",
                )
            mates = [positions[key] for key, owner in shared.items()
                     if owner["stable_chair_position_identity"] == identity]
            _require(len(mates) == 1, "block support has no unique shared rail")
            record.update(
                exclusion_kind="paired-source-context-not-qualified",
                reason=("The retained LH main-side reference does not qualify "
                        "the required RH main-side and turnout-side contexts. "
                        "Source chair angles and sampled world rail tangents "
                        "have different reference frames."),
                source_context_comparison=_block_context_exclusion(
                    position, mates[0], preparations[label],
                ),
            )
        else:
            record.update(
                exclusion_kind="source-assignment-deferred",
                reason=position["chair_subtype"],
                assignment_status=position["assignment_status"],
                source_or_assumed_classification=(
                    position["source_or_assumed_classification"]
                ),
            )
        excluded.append(record)
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, crossover_id, "whole crossover", signature,
        entity_kind="crossover",
    )

    def verify_all_sources():
        verify_source()
        if verify_hosts is not None:
            verify_hosts()
        for prepared in preparations.values():
            verify_catalogue_sources(prepared)

    receipt = {
        "document_name": source_document.Name, "crossover_id": crossover_id,
        "source_kind": "crossover", "timber_context": "current B4 resolved timbers",
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "placement_count": len(selected), "excluded_position_count": len(excluded),
        "selected_counts": {family: len(values)
                            for family, values in families.items()},
        "selected_positions": selected, "excluded_positions": excluded,
        "recovered_positions": recovered,
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "coverage_summary": (f"{len(selected)} placed; {len(excluded)} excluded; "
                             f"{len(positions)} source positions accounted for"),
        "source_base_z_mm": base_z,
        "embed_depth_mm": settings["future_chair_embed_depth"],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "context_kind": "derived rail and timber wires",
        "source_document_mutation": False,
        "limits": [
            "Complete position accounting does not mean a fully chaired crossover.",
            "Retained key geometry does not resolve the source key-direction policy.",
            "Deferred assignments and unqualified paired contexts stay excluded.",
            "No physical fit, production, export, persistence or rights acceptance.",
        ],
    }
    if paired_contexts_path is None:
        return create_preview(catalogue_path, families, shapes, receipt,
                              verify_all_sources)
    return create_preview(
        catalogue_path, families, shapes, receipt, verify_all_sources,
        paired_contexts_path=paired_contexts_path,
    )


def _require_s1j_assignment(module, position, rail, timber, turnout_id):
    """Bind only an existing confirmed joint assignment to its own source."""
    _require(
        type(position.get("chair_code")) is int
        and position["chair_code"] == 7
        and position.get("chair_code_label") == "S1J"
        and position.get("chair_family") == module.CHAIR_FAMILY_JOINT
        and position.get("assignment_status")
        == module.CHAIR_ASSIGNMENT_CONFIRMED
        and position.get("assignment_complete_in_current_stage") is True
        and position.get("deliberate_omission") is False
        and position.get("special_assignment_deferred") is False
        and position.get("stale_signature_state") is False
        and position.get("validation_status") == "validated",
        "joint assignment is incomplete, stale or unsupported", family="S1J",
    )
    _require(
        all(record.get("parent_turnout_identity") == turnout_id
            for record in (position, rail, timber))
        and not position.get("parent_crossover_identity")
        and not rail.get("parent_crossover_identity")
        and not timber.get("crossover_identity")
        and position.get("rail_name") == rail.get("name")
        and position.get("rail_role") == rail.get("rail_role")
        and position.get("timber_identifier") == timber.get("identifier")
        and position.get("prototype_timber_identifier")
        == timber.get("prototype_reference"),
        "joint source ownership or named support disagrees", family="S1J",
    )
    footprint = position.get("chair_footprint_parameters")
    _require(
        position.get("source_or_assumed_classification")
        == module.CHAIR_CLASS_SOURCE
        and isinstance(footprint, dict)
        and footprint.get("dimension_classification")
        == module.CHAIR_CLASS_SOURCE,
        "joint source dimensions are unresolved", family="S1J",
    )
    _require(
        type(position.get("key_direction_sign")) is int
        and position["key_direction_sign"] == 0
        and position.get("key_orientation") == (
            "towards the adjacent rail joint; exact direction sign "
            "requires stored joint chainage"
        )
        and position.get("key_orientation_classification")
        == module.CHAIR_CLASS_SOURCE,
        "the retained model does not implement a key-direction policy",
        family="S1J",
    )


def preview_private_catalogue_s1j_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Inspect retained S1J components at existing C10 joint assignments.

    Reuse the qualified selection and named-face recovery without changing
    the physical plan. Require the complete fixed source profile and keep
    all original exclusions. The adapter verifies source and catalogue
    bytes transactionally in a separate unsaved private document.
    """
    _require(callable(create_preview), "the native adapter is unavailable",
             family="S1J")
    signature_text, analysis, settings, plan, rails, timbers = (
        _open_source_context(module, source_document, turnout_id, "S1J")
    )
    _require_context(module, json.loads(signature_text), turnout_id,
                     settings, plan, family="S1J")
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rail_by_id = _indexed(rails, "stable_identity")
    timber_by_id = _indexed(timbers, "stable_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    original_excluded = _indexed(plan.get("analytical_only"),
                                 "chair_position_identity")
    _require(not instances.keys() & original_excluded.keys()
             and instances.keys() | original_excluded.keys()
             == positions.keys(),
             "the inherited plan does not account for every position",
             family="S1J")
    datums = [item.get("base_z") for item in instances.values()]
    _require(datums and all(_finite(value) for value in datums)
             and all(value == datums[0] for value in datums),
             "source placement datum is missing or inconsistent",
             family="S1J")
    for identity, position in positions.items():
        original = instances.get(identity, original_excluded.get(identity))
        _require(
            all(original.get(field) == position.get(field)
                for field in ("rail_identity", "timber_identity")),
            "plan and analysis source identities disagree", family="S1J",
        )
        if position.get("chair_code") != 7:
            _require(position.get("chair_code_label") != "S1J",
                     "joint label and code disagree", family="S1J")
            continue
        rail = rail_by_id.get(position.get("rail_identity"))
        timber = timber_by_id.get(position.get("timber_identity"))
        _require(rail is not None and timber is not None,
                 "the named rail or timber source is missing", family="S1J")
        _require_s1j_assignment(module, position, rail, timber, turnout_id)
        _require(original.get("chair_label") == "S1J",
                 "plan joint label disagrees", family="S1J")
        if identity in instances:
            _require(original.get("centre_point")
                     == position.get("centre_point"),
                     "plan joint centre disagrees", family="S1J")
    placements, remaining = _select_s1j_positions(module, analysis, plan)
    placements, remaining, recovered = _recover_positions(
        module, analysis, plan, rails, timbers, placements, remaining, 7,
    )
    # The shared selector describes the older five-component preview.
    # Keep original exclusions exact; name only this new selection correctly.
    for item in remaining:
        if (item["position_id"] in instances and item["reason"]
                == "Only the five-component S1J reference is selected."):
            item["reason"] = "Only retained S1J references are selected."
    selected = []
    for placement in placements:
        position = positions[placement.position_id]
        selected.append({
            "position_id": placement.position_id,
            "rail_id": placement.rail_id, "timber_id": placement.timber_id,
            "chair_code": 7,
            "original_instance": copy.deepcopy(
                instances.get(placement.position_id),
            ),
            "original_exclusion": copy.deepcopy(
                original_excluded.get(placement.position_id),
            ),
            "key_direction_sign": position["key_direction_sign"],
            "key_orientation": position["key_orientation"],
            "key_orientation_classification": (
                position["key_orientation_classification"]
            ),
        })
    context_shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "S1J", signature_text,
    )
    source_receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature_text.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "selected_s1j_count": len(placements), "selected_positions": selected,
        "coverage_summary": (
            f"{len(placements)} S1J references; "
            f"{len(positions)} source positions accounted for"
        ),
        "remaining_positions": remaining,
        "recovered_positions": recovered,
        "original_analytical_exclusions": copy.deepcopy(
            plan["analytical_only"],
        ),
        "source_base_z_mm": datums[0],
        "embed_depth_mm": settings["future_chair_embed_depth"],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "context_kind": "derived rail and timber wires",
        "source_document_mutation": False,
        "limits": [
            "Private fixed-reference placement; no physical fit acceptance.",
            "The source key-direction policy remains unresolved.",
            "All inherited physical exclusions and placement routes "
            "remain unchanged.",
            "No production, export, persistence or live-update authority.",
        ],
    }
    return create_preview(
        catalogue_path, placements, context_shapes, source_receipt,
        verify_source,
    )
