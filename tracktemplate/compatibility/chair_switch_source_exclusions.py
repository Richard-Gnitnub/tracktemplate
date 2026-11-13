"""Account for source-null switch chairs beside admitted TO-001 owners.

Templot 556b switch_select.pas:1833-1835 gives seven P, two block-slide
and three block-heel timbers for the C switch. math_unit.pas:29668-29727
selects stock chairs on rails 1/4 and null chairs on rails 2/3. The named
curved closure is rail 2 beside stock rail 1; the straight closure is
rail 3 beside stock rail 4 (math_unit:17792-17794, 30486-30505).
These are no-separate-chair decisions, not proof of bearing or fit.
Source-informed, GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
"""

import hashlib
import json

from tracktemplate.compatibility.chair_source_support import (
    _finite,
    _indexed,
)


_SOURCE_SIGNATURE = (
    "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379"
)
_FIXED_CONFIG = {
    "turnout_id": "TO-001", "size": "REA C10 natural",
    "handing": "Left-hand", "orientation": "Facing in host travel direction",
    "track_gauge": 16.5, "flangeway": 1.0,
    "rail_geometry_revision": 2, "timber_geometry_revision": 2,
    "toe_chainage": 746.298, "template_width": 32.0,
    "chair_analysis_signature": _SOURCE_SIGNATURE,
}
_SIDES = (
    ("main-side stock rail", "curved switch and closure rail", 1, 2),
    ("turnout-side stock rail", "straight switch and closure rail", 4, 3),
)
_OMISSION_REASON = (
    "shared support position deliberately has no separate chair body"
)


def _require(condition, message):
    if not condition:
        raise ValueError("Private switch source exclusion: " + message)


def _identity(number, name):
    return (f"TO-001:chair:to-001-timber-s{number}:"
            + name.replace(" ", "-"))


def _source_record(positions, rails, timber, identity, name, role):
    """Require the exact named source relationship without changing it."""
    position = positions.get(identity)
    rail_id = "TO-001:rail:" + name.replace(" ", "-")
    rail = rails.get(rail_id)
    _require(isinstance(position, dict) and isinstance(rail, dict),
             "the named source position or rail is missing")
    _require(
        position.get("rail_identity") == rail_id
        and position.get("rail_name") == rail.get("name") == name
        and position.get("rail_role") == rail.get("rail_role") == role
        and all(r.get("parent_turnout_identity") == "TO-001"
                and r.get("parent_crossover_identity") == ""
                for r in (position, rail))
        and position.get("timber_identity") == timber["stable_identity"]
        and position.get("timber_identifier") == timber["identifier"]
        and position.get("prototype_timber_identifier") == timber["identifier"],
        "source rail, timber or owner identity differs",
    )
    expected_rail = {
        "gauge_face": name + " gauge face",
        "outer_face": name + " outer face",
        "gauge_orientation_source": "mapped named turnout rail faces",
        "rail_geometry_revision": 2,
    }
    _require(rail.get("source_configuration") == expected_rail
             and position.get("source_configuration") == {
                 "rail": expected_rail,
                 "timber": timber["source_configuration"],
             }, "named source configurations disagree")
    for field in ("centre_point", "local_rail_tangent"):
        values = position.get(field)
        _require(isinstance(values, (list, tuple)) and len(values) == 2
                 and all(_finite(value) for value in values),
                 "invalid source " + field)
    return position, rail


def qualify_turnout_switch_exclusions(context, selected_positions, *, family):
    """Return fourteen P or five main-side block omission witnesses.

Call after the existing route admits its owners. Inputs are its complete
source snapshot and selected-owner records. No source assignment, chair
placement or physical plan changes. Unsupported owners remain unresolved.
"""
    _require(isinstance(context, dict) and context.get("kind") == "turnout",
             "the fixed turnout context is required")
    config = context.get("configuration")
    analysis = context.get("analysis")
    _require(isinstance(config, dict) and isinstance(analysis, dict)
             and all(config.get(k) == v and type(config.get(k)) is type(v)
                     for k, v in _FIXED_CONFIG.items())
             and analysis.get("geometry_signature") == _SOURCE_SIGNATURE,
             "only the fixed LH facing TO-001 source is supported")
    _require(family in ("P", "1P-5P"), "unsupported stock-owner route")
    positions = _indexed(analysis.get("positions"),
                         "stable_chair_position_identity")
    rails = _indexed(context.get("rails"), "stable_identity")
    timbers = _indexed(context.get("timbers"), "stable_identity")
    plan = context.get("plan")
    _require(isinstance(plan, dict), "the original physical plan is missing")
    exclusions = _indexed(plan.get("analytical_only"),
                          "chair_position_identity")
    instances = _indexed(plan.get("instances"), "chair_position_identity")
    _require(len(positions) == 168
             and not instances.keys() & exclusions.keys()
             and instances.keys() | exclusions.keys() == positions.keys(),
             "the original plan must account for all 168 positions once")
    selected = _indexed(selected_positions, "position_id")
    numbers = range(1, 8) if family == "P" else range(8, 13)
    sides = _SIDES if family == "P" else _SIDES[:1]
    expected_owners = {_identity(n, stock) for n in numbers
                       for stock, _closure, _owner_code, _code in sides}
    _require(set(selected) == expected_owners,
             "the exact admitted stock owners are required")
    result = {}
    for number in numbers:
        name = f"S{number}"
        timber_id = "TO-001:timber:" + name
        timber = timbers.get(timber_id)
        _require(isinstance(timber, dict)
                 and timber.get("identifier") == name
                 and timber.get("prototype_reference") == name
                 and timber.get("section") == "switch"
                 and timber.get("parent_turnout_identity") == "TO-001"
                 and timber.get("crossover_identity") == ""
                 and isinstance(timber.get("source_configuration"), dict),
                 "the named switch timber differs")
        source_code = 2 if number <= 7 else 11 if number <= 9 else 12
        for stock, closure, owner_rail_code, closure_rail_code in sides:
            owner_id = _identity(number, stock)
            identity = _identity(number, closure)
            owner, owner_rail = _source_record(
                positions, rails, timber, owner_id, stock, "stock rail",
            )
            position, rail = _source_record(
                positions, rails, timber, identity, closure, closure,
            )
            _require(type(owner.get("chair_code")) is int
                     and owner["chair_code"] == source_code
                     and owner.get("deliberate_omission") is False
                     and owner.get("assignment_complete_in_current_stage")
                     is True, "the admitted owner assignment differs")
            _require(identity not in selected and identity in exclusions,
                     "an omitted rail cannot also be an admitted chair")
            expected = {
                "chair_code": 0, "chair_code_label": "",
                "chair_family": "deliberately omitted chair position",
                "assignment_status": "confirmed shared switch support",
                "assignment_complete_in_current_stage": True,
                "deliberate_omission": True,
                "special_assignment_deferred": False,
                "stale_signature_state": False,
                "validation_status": "validated",
                "source_or_assumed_classification":
                    "source-derived prototype requirement",
                "key_direction_sign": 0,
            }
            _require(all(position.get(k) == v
                         and type(position.get(k)) is type(v)
                         for k, v in expected.items()),
                     "the explicit source-null assignment differs")
            original = exclusions[identity]
            expected_original = {
                "rail_identity": rail["stable_identity"],
                "timber_identity": timber_id, "chair_label": "",
                "chair_family": expected["chair_family"],
                "deliberate_omission": True, "unresolved_special": False,
                "reason": _OMISSION_REASON,
            }
            _require(all(original.get(k) == v
                         and type(original.get(k)) is type(v)
                         for k, v in expected_original.items()),
                     "the original omission differs")
            record_hash = hashlib.sha256(json.dumps(
                [position, rail, owner, owner_rail, timber, original,
                 selected[owner_id]], sort_keys=True, allow_nan=False,
            ).encode("utf-8")).hexdigest()
            result[identity] = {
                "physical_status": "source-switch-omission",
                "exclusion_kind":
                    "source-null-chair-with-admitted-stock-owner",
                "reason": "The fixed source selects no separate chair on "
                          "this switch rail. Its named stock owner is "
                          "admitted in this preview; physical support is "
                          "not established by this exclusion.",
                "source_switch_omission": {
                    "owner_position_id": owner_id,
                    "source_chair_code": 0,
                    "selected_owner_chair_code": source_code,
                    "source_rail_code": closure_rail_code,
                    "selected_owner_rail_code": owner_rail_code,
                    "prototype_timber_identifier": name,
                    "source_geometry_sha256": _SOURCE_SIGNATURE,
                    "source_record_sha256": record_hash,
                    "physical_fit": "NOT_ASSESSED",
                },
            }
    return result
