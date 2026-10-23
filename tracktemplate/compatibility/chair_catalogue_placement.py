"""Place the retained P reference at confirmed C10 analytical positions.

This private snapshot leaves the inherited physical plan and all existing
placement routes unchanged. Its source frame and datum are read from the
current analysis; retained geometry supplies no new railway decisions.
"""

import copy
import hashlib
import json
import math
from numbers import Real

from tracktemplate.compatibility.chair_reference_preview import (
    _context_shapes_and_verifier,
    _open_source_context,
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


def _require(condition, message):
    if not condition:
        raise ValueError("Private P placement: " + message)


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


def _require_context(module, context, turnout_id, settings, plan):
    """Refuse any context beyond the retained fixed P model's inputs."""
    config = context["configuration"]
    _require(
        context["kind"] == "turnout"
        and config.get("turnout_id") == turnout_id
        and config.get("size") == module.TURNOUT_SIZE_C10
        and module.TURNOUT_DEFAULT_SCALE == 76.2
        and plan.get("entity_kind") == "turnout"
        and plan.get("entity_id") == turnout_id,
        "one C10 turnout at 1:76.2 is required",
    )
    for field, expected in (("track_gauge", 16.5), ("flangeway", 1.0)):
        _require(_finite(config.get(field)) and config[field] == expected,
                 "unsupported " + field)
    _require_model_inputs(settings, plan)


def _require_model_inputs(settings, plan):
    """Keep the complete fixed rail profile and source embedding binding."""
    profile = plan.get("rail_profile")
    expected_profile = dict(_CODE75_PROFILE)
    _require(isinstance(profile, dict) and profile == expected_profile
             and profile.get("vertical_rail") is True,
             "the complete fixed Code 75 revA profile is required")
    for field, expected in _CODE75_PROFILE:
        if type(expected) is float:
            _require(_finite(profile[field]), "invalid profile " + field)
    _require(settings.get("rail_profile_id") == expected_profile["profile_id"],
             "analysis rail profile disagrees")
    _require(isinstance(plan.get("settings"), dict)
             and plan["settings"].get("embed_depth")
             == settings.get("future_chair_embed_depth")
             and _finite(settings.get("future_chair_embed_depth")),
             "source embedding settings disagree")


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
