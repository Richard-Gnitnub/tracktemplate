"""Bind an explicit private S1 preview to current C10 chair analysis.

The inherited host supplies railway decisions and placement context. This
adapter neither changes them nor substitutes the reference for production
chairs. Exact full-precision records bind the preview to one source state.
"""

import hashlib
import json

from tracktemplate.domain.chair_placement import prepare_s1_placements


def _canonical_json(record):
    return json.dumps(
        record, allow_nan=False, ensure_ascii=True,
        separators=(",", ":"), sort_keys=True,
    )


def _source_context(module, document, turnout_id):
    """Read current decisions without using the rounded solid-plan cache."""
    kind, config, analysis, settings, rails, timbers = (
        module._chair_generation_context(document, "turnout", turnout_id)
    )
    if (
        kind != "turnout" or config.get("turnout_id") != turnout_id
        or config.get("size") != module.TURNOUT_SIZE_C10
        or module.TURNOUT_DEFAULT_SCALE != 76.2
    ):
        raise ValueError("S1 reference preview requires one C10 at 1:76.2.")
    plan = module._A8A7B15_BUILD_SOLID_PLAN(
        document, kind, config, analysis, rails, timbers, settings,
    )
    # Keep unrounded Z, axes and the complete analytical inputs. The legacy
    # solid signature deliberately rounds some coordinates for its cache.
    return _canonical_json({
        "kind": kind, "configuration": config, "analysis": analysis,
        "settings": settings, "rails": rails, "timbers": timbers,
        "plan": plan,
    }), analysis, settings, plan


def _select_positions(module, analysis, plan):
    """Account for every analysis position; select only resolved S1 bodies."""
    positions = analysis.get("positions", [])
    by_id = {}
    for position in positions:
        identity = position.get("stable_chair_position_identity")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("Chair analysis contains an empty position ID.")
        if identity in by_id:
            raise ValueError("Chair analysis contains duplicate position IDs.")
        by_id[identity] = position

    selected, excluded, accounted = [], [], set()
    for instance in plan["instances"]:
        identity = instance.get("chair_position_identity")
        if identity not in by_id or identity in accounted:
            raise ValueError("Chair plan and analysis identities disagree.")
        accounted.add(identity)
        position = by_id[identity]
        if (
            type(instance.get("chair_code")) is not int
            or type(position.get("chair_code")) is not int
            or instance["chair_code"] != position["chair_code"]
            or any(instance.get(field) != position.get(field)
                   for field in ("rail_identity", "timber_identity"))
        ):
            raise ValueError("Chair plan and analysis assignments disagree.")
        if (
            type(instance["chair_code"]) is int
            and instance["chair_code"] == 1
        ):
            if (
                type(position.get("chair_code")) is not int
                or position["chair_code"] != 1
                or position.get("assignment_status")
                != module.CHAIR_ASSIGNMENT_CONFIRMED
                or position.get("deliberate_omission")
                or position.get("special_assignment_deferred")
            ):
                raise ValueError("S1 position is not a confirmed assignment.")
            selected.append(instance)
        else:
            excluded.append({
                "position_id": identity,
                "rail_id": position["rail_identity"],
                "timber_id": position["timber_identity"],
                "chair_code": instance["chair_code"],
                "reason": "Only the five-component S1 reference is selected.",
            })
    for item in plan["analytical_only"]:
        identity = item.get("chair_position_identity")
        if identity not in by_id or identity in accounted:
            raise ValueError("Chair plan and analysis identities disagree.")
        accounted.add(identity)
        position = by_id[identity]
        reason = item.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("An excluded chair position needs its reason.")
        excluded.append({
            "position_id": identity, "chair_code": position.get("chair_code"),
            "rail_id": position.get("rail_identity"),
            "timber_id": position.get("timber_identity"), "reason": reason,
        })
    if accounted != set(by_id):
        raise ValueError("Chair plan does not account for every position.")
    return prepare_s1_placements(selected), sorted(
        excluded, key=lambda item: item["position_id"],
    )


def preview_s1_reference_chairs(
    module, source_document, turnout_id, package, manifest_text, model_request,
    create_preview,
):
    """Create a separate unsaved reference view; leave the source intact.

    Missing or stale analysis and unsupported source context fail before
    document creation. Unresolved positions stay excluded with their source
    reasons. A final source comparison occurs inside the preview transaction.
    The returned receipt is private evidence, not a production/export record.
    """
    import FreeCAD as App

    if not callable(create_preview):
        raise ValueError("The S1 reference preview adapter is unavailable.")
    if (
        source_document is None
        or App.getDocument(source_document.Name) is not source_document
        or not isinstance(turnout_id, str) or not turnout_id.strip()
    ):
        raise ValueError("Select an open source document and one turnout ID.")
    document_name = source_document.Name
    signature_text, analysis, settings, plan = _source_context(
        module, source_document, turnout_id,
    )
    placements, excluded = _select_positions(module, analysis, plan)
    roles = module._turnout_objects_by_role(source_document, turnout_id)
    context_objects = tuple(roles.get(role) for role in (
        module.TURNOUT_RAIL_ROLE, module.TURNOUT_TIMBER_ROLE,
    ))
    if any(obj is None for obj in context_objects):
        raise ValueError("Current C10 rail and timber context is required.")
    source_shapes = tuple(obj.Shape for obj in context_objects)
    if any(shape.isNull() or not shape.isValid() for shape in source_shapes):
        raise ValueError("Current C10 context contains invalid shapes.")
    context_shapes = tuple(shape.copy() for shape in source_shapes)

    def verify_source():
        if App.getDocument(document_name) is not source_document:
            raise ValueError("The preview source document is no longer open.")
        current, _analysis, _settings, _plan = _source_context(
            module, source_document, turnout_id,
        )
        if current != signature_text or any(
            source_document.getObject(obj.Name) is not obj
            or not obj.Shape.isSame(shape)
            for obj, shape in zip(context_objects, source_shapes)
        ):
            raise ValueError("The preview source changed during construction.")

    confirmed_s1 = {
        position["stable_chair_position_identity"]
        for position in analysis["positions"]
        if type(position.get("chair_code")) is int
        and position["chair_code"] == 1
        and position.get("assignment_status")
        == module.CHAIR_ASSIGNMENT_CONFIRMED
    }
    unresolved_s1 = sum(item["position_id"] in confirmed_s1
                        for item in excluded)
    source_receipt = {
        "document_name": document_name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature_text.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(analysis["positions"]),
        "selected_s1_count": len(placements), "excluded_positions": excluded,
        "confirmed_s1_count": len(confirmed_s1),
        "unresolved_confirmed_s1_count": unresolved_s1,
        "coverage_summary": "{}/{} S1; {} unresolved".format(
            len(placements), len(confirmed_s1), unresolved_s1,
        ),
        "embed_depth_mm": settings["future_chair_embed_depth"],
        "embedding_basis": "source template top minus source embed depth",
        "model_support_adjustments_applied": False,
        "context_kind": "derived rail and timber wires",
        "source_document_mutation": False,
    }
    return create_preview(
        package, manifest_text, model_request, placements, context_shapes,
        source_receipt, verify_source,
    )
