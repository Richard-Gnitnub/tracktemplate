"""Bind explicit private S1 and S1J previews to current C10 chair analysis.

The inherited host supplies railway decisions and placement context. This
adapter neither changes them nor substitutes the reference for production
chairs. Exact full-precision records bind the preview to one source state.
"""

import hashlib
import json
import math
from numbers import Real

from tracktemplate.domain.chair_placement import (
    S1Placement,
    S1JPlacement,
    prepare_s1_placements,
    prepare_s1j_placements,
    recover_reference_frame,
)


def _canonical_json(record):
    return json.dumps(
        record, allow_nan=False, ensure_ascii=True,
        separators=(",", ":"), sort_keys=True,
    )


def _source_context(module, document, turnout_id, family="S1"):
    """Read current decisions without using the rounded solid-plan cache."""
    kind, config, analysis, settings, rails, timbers = (
        module._chair_generation_context(document, "turnout", turnout_id)
    )
    if (
        kind != "turnout" or config.get("turnout_id") != turnout_id
        or config.get("size") != module.TURNOUT_SIZE_C10
        or module.TURNOUT_DEFAULT_SCALE != 76.2
    ):
        raise ValueError(
            f"{family} reference preview requires one C10 at 1:76.2."
        )
    plan = module._A8A7B15_BUILD_SOLID_PLAN(
        document, kind, config, analysis, rails, timbers, settings,
    )
    # Keep unrounded Z, axes and the complete analytical inputs. The legacy
    # solid signature deliberately rounds some coordinates for its cache.
    return _canonical_json({
        "kind": kind, "configuration": config, "analysis": analysis,
        "settings": settings, "rails": rails, "timbers": timbers,
        "plan": plan,
    }), analysis, settings, plan, rails, timbers


def _recover_positions(
    module, analysis, plan, rails, timbers, placements, excluded, chair_code,
):
    """Resolve only a named-face frame refusal in the private preview.

    Keep the inherited plan and all its existing placements unchanged.
    A unique section through both named faces can establish the gauge
    side of an existing analytical tangent. Missing or ambiguous evidence
    leaves the position excluded, with its original reason intact.
    """
    original_reason = (
        "gauge normal is not perpendicular to the local rail tangent"
    )
    candidates = [item for item in excluded
                  if type(item["chair_code"]) is int
                  and item["chair_code"] == chair_code
                  and item["reason"] == original_reason]
    if not candidates:
        return placements, excluded, []

    def indexed(records, field):
        result = {}
        for record in records:
            identity = record.get(field)
            if (not isinstance(identity, str) or not identity.strip()
                    or identity in result):
                raise ValueError("Preview source identities are ambiguous.")
            result[identity] = record
        return result

    positions = indexed(analysis["positions"], "stable_chair_position_identity")
    rail_by_id = indexed(rails, "stable_identity")
    timber_by_id = indexed(timbers, "stable_identity")
    datums = [item.get("base_z") for item in plan["instances"]]
    if (not datums or any(
        isinstance(value, bool) or not isinstance(value, Real)
        or not math.isfinite(value) for value in datums
    ) or any(value != datums[0] for value in datums)):
        raise ValueError("Preview placement datum is missing or inconsistent.")
    placement_type = {1: S1Placement, 7: S1JPlacement}[chair_code]
    recovered, evidence, refused = [], [], {}
    for item in candidates:
        identity = item["position_id"]
        position = positions[identity]
        if (position.get("assignment_status")
                != module.CHAIR_ASSIGNMENT_CONFIRMED
                or position.get("deliberate_omission")
                or position.get("special_assignment_deferred")):
            refused[identity] = "The family assignment is not confirmed."
            continue
        rail = rail_by_id.get(position["rail_identity"])
        timber = timber_by_id.get(position["timber_identity"])
        if rail is None or timber is None:
            refused[identity] = "The named rail or timber source is missing."
            continue
        supported, reason = module._chair_supported_physical_position(position)
        if not supported:
            refused[identity] = reason
            continue
        try:
            frame = recover_reference_frame(
                position.get("centre_point"),
                position.get("local_rail_tangent"),
                rail.get("gauge_face_points"), rail.get("outer_face_points"),
            )
            placement = placement_type(
                position_id=identity, rail_id=position["rail_identity"],
                timber_id=position["timber_identity"],
                origin_mm=(*position["centre_point"], datums[0]),
                x_axis=frame["x_axis"], y_axis=frame["y_axis"],
            )
        except ValueError as error:
            refused[identity] = str(error)
            continue
        recovered.append(placement)
        evidence.append({
            "position_id": identity, "rail_id": placement.rail_id,
            "timber_id": placement.timber_id, "chair_code": chair_code,
            "original_reason": original_reason,
            "frame_evidence": frame["witness"],
        })
    recovered_ids = {item.position_id for item in recovered}
    remaining = [
        dict(item, placement_recovery_reason=refused[item["position_id"]])
        if item["position_id"] in refused else item
        for item in excluded if item["position_id"] not in recovered_ids
    ]
    return (
        tuple(sorted(
            (*placements, *recovered), key=lambda item: item.position_id,
        )),
        remaining, sorted(evidence, key=lambda item: item["position_id"]),
    )


def _select_family_positions(
    module, analysis, plan, chair_code, family, prepare_placements,
):
    """Account for every analysis position; select only resolved family bodies."""
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
            and instance["chair_code"] == chair_code
        ):
            if (
                type(position.get("chair_code")) is not int
                or position["chair_code"] != chair_code
                or position.get("assignment_status")
                != module.CHAIR_ASSIGNMENT_CONFIRMED
                or position.get("deliberate_omission")
                or position.get("special_assignment_deferred")
            ):
                raise ValueError(
                    f"{family} position is not a confirmed assignment."
                )
            selected.append(instance)
        else:
            excluded.append({
                "position_id": identity,
                "rail_id": position["rail_identity"],
                "timber_id": position["timber_identity"],
                "chair_code": instance["chair_code"],
                "reason": (
                    f"Only the five-component {family} reference is selected."
                ),
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
    return prepare_placements(selected), sorted(
        excluded, key=lambda item: item["position_id"],
    )


def _open_source_context(module, source_document, turnout_id, family):
    """Capture one current source context from an open document."""
    import FreeCAD as App

    if (
        source_document is None
        or App.getDocument(source_document.Name) is not source_document
        or not isinstance(turnout_id, str) or not turnout_id.strip()
    ):
        raise ValueError("Select an open source document and one turnout ID.")
    return _source_context(
        module, source_document, turnout_id, family,
    )


def _context_shapes_and_verifier(
    module, source_document, turnout_id, family, signature_text,
):
    """Copy context geometry and retain the complete final source check."""
    import FreeCAD as App

    document_name = source_document.Name
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
        current, *_context = _source_context(
            module, source_document, turnout_id, family,
        )
        if current != signature_text or any(
            source_document.getObject(obj.Name) is not obj
            or not obj.Shape.isSame(shape)
            for obj, shape in zip(context_objects, source_shapes)
        ):
            raise ValueError("The preview source changed during construction.")

    return context_shapes, verify_source


def _confirmed_positions(module, analysis, chair_code):
    return {
        position["stable_chair_position_identity"]
        for position in analysis["positions"]
        if type(position.get("chair_code")) is int
        and position["chair_code"] == chair_code
        and position.get("assignment_status")
        == module.CHAIR_ASSIGNMENT_CONFIRMED
    }


def _preview_reference_chairs(
    module, source_document, turnout_id, package, manifest_text, model_request,
    create_preview, *, family, chair_code, select_positions,
):
    """Create a separate unsaved reference view; leave the source intact.

    Missing or stale analysis and unsupported source context fail before
    document creation. Unresolved positions stay excluded with their source
    reasons. A final source comparison occurs inside the preview transaction.
    The returned receipt is private evidence, not a production/export record.
    """
    if not callable(create_preview):
        raise ValueError(
            f"The {family} reference preview adapter is unavailable."
        )
    signature_text, analysis, settings, plan, rails, timbers = (
        _open_source_context(
            module, source_document, turnout_id, family,
        )
    )
    placements, excluded = select_positions(module, analysis, plan)
    placements, excluded, recovered = _recover_positions(
        module, analysis, plan, rails, timbers, placements, excluded, chair_code,
    )
    context_shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, family, signature_text,
    )
    confirmed_positions = _confirmed_positions(module, analysis, chair_code)
    unresolved_count = sum(item["position_id"] in confirmed_positions
                           for item in excluded)
    source_receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature_text.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(analysis["positions"]),
        f"selected_{family.lower()}_count": len(placements),
        "excluded_positions": excluded,
        "recovered_positions": recovered,
        f"confirmed_{family.lower()}_count": len(confirmed_positions),
        f"unresolved_confirmed_{family.lower()}_count": unresolved_count,
        "coverage_summary": "{}/{} {}; {} unresolved".format(
            len(placements), len(confirmed_positions), family, unresolved_count,
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


def _select_positions(module, analysis, plan):
    """Keep the existing S1 selection and exclusion contract."""
    return _select_family_positions(
        module, analysis, plan, 1, "S1", prepare_s1_placements,
    )


def _select_s1j_positions(module, analysis, plan):
    """Select only resolved S1J instances; retain all exclusion reasons."""
    return _select_family_positions(
        module, analysis, plan, 7, "S1J", prepare_s1j_placements,
    )


def _select_s1_s1j_positions(module, analysis, plan):
    """Partition one analysis between resolved S1/S1J and exclusions."""
    s1_placements, s1_excluded = _select_positions(module, analysis, plan)
    s1j_placements, _s1j_excluded = _select_s1j_positions(
        module, analysis, plan,
    )
    s1_ids = {item.position_id for item in s1_placements}
    s1j_ids = {item.position_id for item in s1j_placements}
    if not s1_ids.isdisjoint(s1j_ids):
        raise ValueError("S1 and S1J reference positions overlap.")
    resolved_ids = {
        item["chair_position_identity"] for item in plan["instances"]
    }
    excluded = []
    for item in s1_excluded:
        if item["position_id"] in s1j_ids:
            continue
        if item["position_id"] in resolved_ids:
            item = dict(item, reason=(
                "Only the five-component S1 and S1J references are selected."
            ))
        excluded.append(item)
    selected_ids = s1_ids | s1j_ids
    excluded_ids = {item["position_id"] for item in excluded}
    analysis_ids = {
        item["stable_chair_position_identity"]
        for item in analysis["positions"]
    }
    if (
        not selected_ids.isdisjoint(excluded_ids)
        or selected_ids | excluded_ids != analysis_ids
        or len(excluded_ids) != len(excluded)
    ):
        raise ValueError("Combined chair preview accounting is incomplete.")
    return s1_placements, s1j_placements, excluded


def preview_s1_reference_chairs(
    module, source_document, turnout_id, package, manifest_text, model_request,
    create_preview,
):
    """Create the existing private S1 snapshot from current C10 analysis."""
    return _preview_reference_chairs(
        module, source_document, turnout_id, package, manifest_text,
        model_request, create_preview, family="S1", chair_code=1,
        select_positions=_select_positions,
    )


def preview_s1j_reference_chairs(
    module, source_document, turnout_id, package, manifest_text, model_request,
    create_preview,
):
    """Create a separate unsaved S1J snapshot from current C10 analysis.

    Preserve source state, stable identities and unresolved positions.
    A complete source comparison precedes the preview transaction commit.
    This explicit research operation gives no production or fit authority.
    """
    return _preview_reference_chairs(
        module, source_document, turnout_id, package, manifest_text,
        model_request, create_preview, family="S1J", chair_code=7,
        select_positions=_select_s1j_positions,
    )


def preview_s1_s1j_reference_chairs(
    module, source_document, turnout_id, s1_package, s1_manifest_text,
    s1j_package, s1j_manifest_text, model_request, create_preview,
):
    """Create one private S1/S1J snapshot from one current C10 context.

    Both families share the captured source and its final comparison. Keep
    every unresolved position and source reason. The native adapter owns
    preparation, the single document transaction and whole-view recovery.
    This command gives no production, fit or output authority.
    """
    if not callable(create_preview):
        raise ValueError("The S1/S1J reference preview adapter is unavailable.")
    signature_text, analysis, settings, plan, rails, timbers = (
        _open_source_context(
            module, source_document, turnout_id, "S1/S1J",
        )
    )
    s1_placements, s1j_placements, excluded = _select_s1_s1j_positions(
        module, analysis, plan,
    )
    s1_placements, excluded, s1_recovered = _recover_positions(
        module, analysis, plan, rails, timbers, s1_placements, excluded, 1,
    )
    s1j_placements, excluded, s1j_recovered = _recover_positions(
        module, analysis, plan, rails, timbers, s1j_placements, excluded, 7,
    )
    context_shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "S1/S1J", signature_text,
    )
    source_receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(
            signature_text.encode("utf-8"),
        ).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(analysis["positions"]),
        "excluded_positions": excluded,
        "recovered_positions": sorted(
            (*s1_recovered, *s1j_recovered), key=lambda item: item["position_id"],
        ),
        "embed_depth_mm": settings["future_chair_embed_depth"],
        "embedding_basis": "source template top minus source embed depth",
        "model_support_adjustments_applied": False,
        "context_kind": "derived rail and timber wires",
        "source_document_mutation": False,
    }
    coverage = []
    for family, chair_code, placements in (
        ("S1", 1, s1_placements), ("S1J", 7, s1j_placements),
    ):
        confirmed = _confirmed_positions(module, analysis, chair_code)
        unresolved = sum(item["position_id"] in confirmed for item in excluded)
        source_receipt.update({
            f"selected_{family.lower()}_count": len(placements),
            f"confirmed_{family.lower()}_count": len(confirmed),
            f"unresolved_confirmed_{family.lower()}_count": unresolved,
        })
        coverage.append(f"{len(placements)}/{len(confirmed)} {family}")
    for prefix in ("selected", "confirmed", "unresolved_confirmed"):
        source_receipt[f"{prefix}_count"] = sum(
            source_receipt[f"{prefix}_{family}_count"]
            for family in ("s1", "s1j")
        )
    source_receipt["coverage_summary"] = (
        "{selected_count}/{confirmed_count} S1/S1J; "
        "{unresolved_confirmed_count} unresolved; "
    ).format(**source_receipt) + "; ".join(coverage)
    return create_preview(
        s1_package, s1_manifest_text, s1j_package, s1j_manifest_text,
        model_request, s1_placements, s1j_placements, context_shapes,
        source_receipt, verify_source,
    )
