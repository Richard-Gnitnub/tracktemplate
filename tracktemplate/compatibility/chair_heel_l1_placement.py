"""Admit ten private L1 heel previews from current XO-001 source records.

The retained source predicates and component frames remain authoritative
for this finite C10 RH selection. Recalculated host data may change; the
whole-crossover fingerprint restriction and physical plan stay unchanged.
No geometry is constructed until the injected preview adapter is called.
"""

import copy
import hashlib
import json
import math
import sys

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_catalogue_placement import (
    _finite,
    _indexed,
    _KEY_CLASSIFICATION,
    _KEY_ORIENTATION,
    _require_p_crossover_context,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.compatibility.chair_reference_preview import (
    _context_shapes_and_verifier,
    _open_source_context,
)
from tracktemplate.compatibility.chair_single_rail_placement import (
    _family,
    _source_pose,
)
from tracktemplate.domain.single_rail_placement import place_single_rail


_L1_SHA256 = (
    "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042"
)
_CONTEXTS = (("S13", 1), ("S13", 3), ("T1", 1), ("T1", 3), ("T2", 3))
_RAILS = ((1, "main-side stock rail"),
          (3, "straight switch and closure rail"))
_FRAME_EXCLUSION = "gauge normal is not perpendicular to the local rail tangent"


def _require(condition, message):
    if not condition:
        raise ValueError("Private current-source heel L1: " + message)


def _configuration(module, context, settings, plan):
    """Keep the qualified railway intent, accepting current derived values."""
    config = context["configuration"]
    _require(config.get("crossover_id") == "XO-001",
             "only the ten XO-001 heel positions are supported")
    _require_p_crossover_context(module, context, "XO-001", settings, plan)
    for side in ("A", "B"):
        key = "turnout_" + side.lower()
        constituent = config[key + "_config"]
        _require(config[key + "_id"] == f"XO-001-{side}001"
                 and constituent.get("handing") == module.TURNOUT_HAND_RIGHT
                 and constituent.get("orientation") in (
                     module.TURNOUT_ORIENTATION_FACING,
                     module.TURNOUT_ORIENTATION_TRAILING,
                 )
                 and constituent.get("rail_geometry_revision") == 2
                 and constituent.get("timber_geometry_revision") == 2,
                 "the qualified C10 right-hand source is required")
    requested = config.get("minimum_requested_radius")
    resulting = config.get("minimum_resulting_radius")
    # Preserve the existing complete-crossover arithmetic condition from
    # B15 build_crossover_geometry. This is not a physical-fit tolerance.
    _require(_finite(requested) and requested > 0
             and _finite(resulting) and resulting > 0
             and resulting >= requested - 1.0e-7,
             "the configured minimum resulting radius is not satisfied")
    return config


def _source_binding(module, position, rail, timber, original, expected):
    """Reject substitutions while preserving the original S1 record."""
    identity, owner, side, name, rail_code = expected
    rail_names = dict(_RAILS)
    rail_name = rail_names[rail_code]
    subtype = (
        "REA S1 ordinary chair beyond the C-switch block-chair zone"
        if name == "S13" else
        "REA S1 ordinary closure-region chair; L1 clearance selection "
        "awaits detailed bridge-chair assignment"
    )
    timber_id = f"XO-001:{side}:{name}"
    rail_id = owner + ":rail:" + rail_name.replace(" ", "-")
    _require(
        position.get("stable_chair_position_identity") == identity
        and position.get("parent_crossover_identity") == "XO-001"
        and position.get("parent_turnout_identity") == owner
        and position.get("prototype_timber_identifier") == name
        and position.get("timber_identifier") == name
        and position.get("rail_name") == rail_name
        and position.get("rail_identity") == rail_id
        and position.get("timber_identity") == timber_id
        and type(position.get("chair_code")) is int
        and position["chair_code"] == 1
        and position.get("chair_code_label") == "S1"
        and position.get("chair_family") == module.CHAIR_FAMILY_ORDINARY
        and position.get("chair_subtype") == subtype
        and position.get("assignment_status") == module.CHAIR_ASSIGNMENT_CONFIRMED
        and position.get("assignment_complete_in_current_stage") is True
        and position.get("special_assignment_deferred") is False
        and position.get("deliberate_omission") is False
        and position.get("stale_signature_state") is False
        and position.get("validation_status") == "validated"
        and type(position.get("key_direction_sign")) is int
        and position["key_direction_sign"] == 0
        and position.get("key_orientation") == _KEY_ORIENTATION
        and position.get("key_orientation_classification") == _KEY_CLASSIFICATION,
        "the original confirmed S1 heel assignment is inconsistent",
    )
    role = "stock rail" if rail_code == 1 else rail_names[3]
    footprint = position.get("chair_footprint_parameters")
    _require(position.get("rail_role") == role
             and rail.get("rail_role") == role
             and position.get("source_or_assumed_classification")
             == module.CHAIR_CLASS_SOURCE
             and isinstance(footprint, dict)
             and footprint.get("dimension_classification")
             == module.CHAIR_CLASS_SOURCE,
             "the heel source role or dimension classification differs")
    _require(
        rail.get("stable_identity") == rail_id
        and rail.get("name") == rail_name
        and rail.get("parent_turnout_identity") == owner
        and rail.get("parent_crossover_identity") == "XO-001"
        and rail.get("turnout_side") == side
        and timber.get("stable_identity") == timber_id
        and timber.get("identifier") == name
        and timber.get("prototype_reference") == name
        and timber.get("parent_turnout_identity") == owner
        and timber.get("crossover_identity") == "XO-001"
        and timber.get("turnout_side") == side,
        "the named source rail or timber ownership differs",
    )
    source = position.get("source_configuration")
    _require(isinstance(source, dict)
             and source.get("timber") == timber.get("source_configuration")
             and source.get("rail") == rail.get("source_configuration")
             and source.get("rail") == {
                 "gauge_face": rail_name + " gauge face",
                 "outer_face": rail_name + " outer face",
                 "gauge_orientation_source": "mapped named turnout rail faces",
                 "rail_geometry_revision": 2,
             }, "position and named source records disagree")
    _require(original.get("rail_identity") == rail_id
             and original.get("timber_identity") == timber_id
             and original.get("chair_label") == "S1",
             "the original physical-plan identity differs")


def _same_number(actual, expected):
    """Use the retained single-rail arithmetic budget, never a fit limit."""
    return (_finite(actual) and _finite(expected)
            and abs(actual - expected) <= 128 * sys.float_info.epsilon
            * max(1000.0, abs(actual), abs(expected)))


def _nominal_world_timber(timber, station, point, travel):
    """Reject shifted timber records despite unchanged nominal source fields."""
    source = timber["source_configuration"]
    centre_y = (source["local_near_y"] + source["local_far_y"]) / 2
    centre = timber.get("centre")
    _require(_same_number(timber.get("host_chainage"), station)
             and _same_number(timber.get("local_rail_heading_radians"), travel)
             and isinstance(centre, (list, tuple)) and len(centre) == 2
             and _same_number(centre[0], point.x + centre_y * math.sin(travel))
             and _same_number(centre[1], point.y - centre_y * math.cos(travel)),
             "the heel timber is not at its nominal canonical host station")


def _placements(module, document, context, analysis, plan, rails, timbers):
    """Calculate only the ten source-selected frames from current hosts."""
    config = context["configuration"]
    _require(isinstance(analysis.get("geometry_signature"), str)
             and bool(analysis["geometry_signature"])
             and config.get("chair_analysis_signature")
             == analysis["geometry_signature"], "chair analysis is not current")
    positions = _indexed(analysis["positions"], "stable_chair_position_identity")
    rail_map = _indexed(rails, "stable_identity")
    timber_map = _indexed(timbers, "stable_identity")
    instances = _indexed(plan["instances"], "chair_position_identity")
    exclusions = _indexed(plan["analytical_only"], "chair_position_identity")
    _require(not set(instances) & set(exclusions), "physical-plan records repeat")
    datums = [record.get("base_z") for record in instances.values()]
    _require(datums and all(_finite(value) and value == datums[0]
                           for value in datums), "source mounting datum differs")
    hosts, data, objects = _host_context(module, document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    placements, selected = [], []
    rail_names = dict(_RAILS)
    for side in ("A", "B"):
        owner = f"XO-001-{side}001"
        constituent = config["turnout_" + side.lower() + "_config"]
        _require(_finite(constituent.get("toe_chainage"))
                 and _finite(data[side].get("total"))
                 and data[side]["total"] > 0,
                 "the canonical host station metadata is invalid")
        layout = _indexed(module.rea_c10_timber_layout(
            dimensions, constituent["template_width"],
        ), "identifier")
        direction = module._turnout_orientation_sign(constituent["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for name, rail_code in _CONTEXTS:
            identity = (f"XO-001:chair:xo-001-{side.lower()}-{name.lower()}:"
                        + rail_names[rail_code].replace(" ", "-"))
            _require(identity in positions, "a named heel position is missing")
            position = positions[identity]
            rail = rail_map.get(position.get("rail_identity"), {})
            timber = timber_map.get(position.get("timber_identity"), {})
            original = instances.get(identity, exclusions.get(identity, {}))
            _source_binding(module, position, rail, timber, original,
                            (identity, owner, side, name, rail_code))
            if identity in instances:
                _require(type(original.get("chair_code")) is int
                         and original["chair_code"] == 1,
                         "the physical plan changed the original S1 family")
            else:
                _require(original.get("reason") == _FRAME_EXCLUSION
                         and original.get("deliberate_omission") is False,
                         "an unsupported physical exclusion remains")
            nominal = layout.get(name, {})
            source = timber["source_configuration"]
            _require("extended_source_timber_identity" not in source
                     and source.get("turnout_geometry_revision") == 2
                     and all(_finite(source.get(field))
                             and source[field] == nominal.get(layout_field)
                             for field, layout_field in (
                                 ("local_x", "x"), ("local_near_y", "near_y"),
                                 ("local_far_y", "far_y"),
                                 ("length_prototype_inches", "length_prototype_inches"),
                             )), "the nominal heel timber source differs")
            local_x = source["local_x"]
            _require(_family(module, dimensions, name, local_x, rail_code) == "L1",
                     "the source predicates no longer select L1")
            angle, gauge_y, branch = _source_pose(
                module, dimensions, local_x, rail_code,
            )
            station = constituent["toe_chainage"] + direction * local_x
            _require(_finite(station) and 0 <= station <= data[side]["total"],
                     "the heel lies outside its canonical host")
            point, heading = module.interpolate_alignment_station(data[side], station)
            _require(all(_finite(value) for value in (point.x, point.y, heading)),
                     "the canonical host returned an invalid pose")
            travel = heading if direction > 0 else heading + math.pi
            _nominal_world_timber(timber, station, point, travel)
            placements.append(place_single_rail(
                identity, position["rail_identity"], position["timber_identity"],
                (point.x, point.y), travel, datums[0], family="L1",
                source_rail_code=rail_code, source_angle_rad=angle,
                source_gauge_y_mm=gauge_y,
            ))
            selected.append({
                "position_id": identity, "rail_id": position["rail_identity"],
                "timber_id": position["timber_identity"], "family": "L1",
                "original_family": "S1", "original_record": copy.deepcopy(original),
                "source_model_sha256": _L1_SHA256,
                "source_station_mm": local_x, "host_station_mm": station,
                "source_rail_code": rail_code, "source_branch": branch,
                "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
                "physical_fit": "NOT_PROVED",
            })

    def verify_hosts():
        current, _data, current_objects = _host_context(module, document, config)
        _require(current == hosts and all(current_objects[key] is value
                                         for key, value in objects.items()),
                 "canonical host changed during heel preview")

    selected_ids = {item.position_id for item in placements}
    remaining = [{"position_id": identity,
                  "reason": "Outside the ten current-source heel L1 positions."}
                 for identity in sorted(set(positions) - selected_ids)]
    return (tuple(sorted(placements, key=lambda item: item.position_id)),
            sorted(selected, key=lambda item: item["position_id"]),
            remaining, verify_hosts)


def preview_private_catalogue_heel_l1_chairs(
    module, source_document, crossover_id, catalogue_path, create_preview,
):
    """Inspect ten retained L1 chairs in a separate current-source snapshot.

    This explicit operation leaves canonical S1 assignments, physical
    exclusions and every existing preview route unchanged. Recalculation
    changes only derived placements. Exact geometry remains on demand.
    """
    _require(crossover_id == "XO-001", "only XO-001 is supported")
    _require(callable(create_preview), "the native preview adapter is unavailable")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, crossover_id, "heel L1", entity_kind="crossover",
    )
    context = json.loads(signature)
    _configuration(module, context, settings, plan)
    placements, selected, remaining, verify_hosts = _placements(
        module, source_document, context, analysis, plan, rails, timbers,
    )
    prepared = prepare_catalogue_chair(catalogue_path, "L1", run="existing-02")
    _require(prepared.label == "L1" and prepared.run == "existing-02"
             and prepared.context == "retained-S1-L1-reference-package"
             and prepared.model_sha256 == _L1_SHA256,
             "the retained L1 catalogue binding differs")
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, crossover_id, "heel L1", signature,
        entity_kind="crossover",
    )

    def verify_inputs():
        verify_source()
        verify_hosts()
        verify_catalogue_sources(prepared)

    receipt = {
        "document_name": source_document.Name, "crossover_id": crossover_id,
        "source_kind": "crossover", "timber_context": "current B4 resolved timbers",
        "source_context_signature": "sha256:" + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "selected_l1_count": len(placements), "selected_positions": selected,
        "analysis_position_count": len(analysis["positions"]),
        "remaining_positions": remaining,
        "coverage_summary": "ten current-source heel L1 references",
        "source_document_mutation": False,
        "geometry_rebuilt": False, "physical_fit": "NOT_PROVED",
        "source_base_z_mm": placements[0].origin_mm[2],
        "limits": [
            "Private retained geometry; no whole-crossover host admission.",
            "Canonical S1 assignments and physical exclusions are unchanged.",
            "No physical-fit, production, export, rights or phase acceptance.",
        ],
    }
    return create_preview(catalogue_path, placements, shapes, receipt, verify_inputs)
