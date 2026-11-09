"""Bind retained single-rail assemblies to the fixed TO-001 source.

Templot 556b math_unit.pas:29551-29665 selects eleven L1 and one S1;
29502-29515 and 29760-29804 select the optional two R2 vee-rail S1s.
Source-informed adaptation is GPL-3.0-or-later; see NOTICE.md and
reference/PROVENANCE.md. Canonical labels, analytical exclusions and all
unrelated preview routes remain unchanged. This is not fit admission.
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
)
from tracktemplate.compatibility.chair_reference_preview import (
    _context_shapes_and_verifier,
    _open_source_context,
)
from tracktemplate.compatibility.chair_single_rail_placement import (
    _family,
    _source_pose,
)
from tracktemplate.compatibility.chair_turnout_check_placement import (
    _ANALYSIS_SHA256,
    _configuration,
    _host,
    _timber_frame,
)
from tracktemplate.domain.single_rail_placement import (
    place_left_hand_single_rail,
)


_RAILS = ((1, "main-side stock rail"),
          (2, "curved switch and closure rail"),
          (3, "straight switch and closure rail"),
          (4, "turnout-side stock rail"))
_SELECTION = (
    ("S13", 1, "L1"), ("S13", 3, "L1"),
    ("T1", 1, "L1"), ("T1", 3, "L1"), ("T2", 3, "L1"),
    ("S13", 2, "L1"), ("S13", 4, "L1"),
    ("T1", 2, "L1"), ("T1", 4, "L1"),
    ("T14", 2, "L1"), ("T2", 2, "L1"), ("T2", 4, "S1"),
)
_MODELS = (
    ("L1", "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042", 23),
    ("S1", "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb", 17),
)
_R2_RAILS = ((2, "vee splice rail"), (3, "vee point rail"))
_CROSSING_TAIL = (
    ("X6-C", 1, "S1"), ("X6-C", 4, "S1"),
    ("X7-D", 1, "S1"), ("X7-D", 4, "S1"),
    ("X8-E", 1, "S1"), ("X8-E", 4, "S1"),
    ("X9-F", 2, "L1"), ("X9-F", 3, "L1"),
)
_HEEL_SELECTION = (("S13", 1), ("S13", 3), ("T1", 1), ("T1", 3), ("T2", 3))
_JOINT_EXIT = (("X9-F", 1, "S1J"), ("R1", 2, "L1"), ("R1", 3, "S1J"))
_S1J_MODEL = "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b"


def _require(condition, message):
    if not condition:
        raise ValueError("Private TO-001 single-rail: " + message)


def _fixed_source(function, *args):
    """Reuse fixed TO source guards and retain their diagnostic cause."""
    try:
        return function(*args)
    except ValueError as error:
        raise ValueError(
            "Private TO-001 single-rail: fixed source context rejected"
        ) from error


def _source_binding(position, rail, timber, original, name, rail_code, *,
                    r2_exit=False, crossing_tail=False, joint_exit=False):
    vee = (r2_exit or (crossing_tail and name == "X9-F")
           or (joint_exit and name == "R1"))
    rail_name = dict(_R2_RAILS if vee else _RAILS)[rail_code]
    rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
    timber_id = "TO-001:timber:" + name
    identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                + rail_name.replace(" ", "-"))
    expected = {
        "stable_chair_position_identity": identity,
        "rail_identity": rail_id, "rail_name": rail_name,
        "rail_role": "stock rail" if rail_code in (1, 4) else rail_name,
        "timber_identity": timber_id,
        "prototype_timber_identifier": name, "timber_identifier": name,
        "parent_turnout_identity": "TO-001", "parent_crossover_identity": "",
        "handedness": "not applicable", "chair_code": 5,
        "chair_code_label": "L1", "chair_family": "bridge chair",
        "assignment_status": "deferred to special-chair assignment",
        "assignment_complete_in_current_stage": True,
        "special_assignment_deferred": True, "deliberate_omission": False,
        "stale_signature_state": False, "validation_status": "Advisory",
        "key_direction_sign": 0,
        "key_orientation": "requires confirmation from the final bridge-chair "
        "subtype and keying arrangement",
        "key_orientation_classification": "dimension requiring later confirmation",
    }
    heel = (name, rail_code) in _HEEL_SELECTION
    if r2_exit or crossing_tail or joint_exit:
        label, code, family = (("AB", 25, "splice-rail support") if rail_code == 2
                               else ("BB/BC", 26, "vee support"))
        if crossing_tail:
            code, label = {"X6-C": (26, "BB/BC"), "X7-D": (27, "CD"),
                           "X8-E": (28, "EF"), "X9-F": (28, "EF")}[name]
            if name != "X9-F":
                family = "common-crossing chair"
        if joint_exit and name == "X9-F":
            label, code, family = "EF", 28, "common-crossing chair"
        expected.update({
            "chair_code": code, "chair_code_label": label, "chair_family": family,
            "handedness": "Left-hand", "assignment_complete_in_current_stage": False,
            "source_or_assumed_classification": "temporary visual approximation",
            "key_orientation": "requires confirmation from the final special-chair "
            "subtype and keying arrangement",
        })
        _require(((name, rail_code) in tuple((n, r) for n, r, _f in _JOINT_EXIT)
                  if joint_exit else name == "R2" if r2_exit else
                  (name, rail_code) in tuple(
                      (n, r) for n, r, _f in _CROSSING_TAIL))
                 and all(
                     position.get(key) is value
                     for key, value in expected.items() if type(value) is bool
                 ), "the original joint-exit source state differs"
                 if joint_exit else "the original crossing-tail source state differs"
                 if crossing_tail else "the original R2 source state differs")
    if heel:
        expected.update({
            "chair_code": 1, "chair_code_label": "S1",
            "chair_family": "ordinary running-rail chair",
            "chair_subtype": (
                "REA S1 ordinary chair beyond the C-switch block-chair zone"
                if name == "S13" else
                "REA S1 ordinary closure-region chair; L1 clearance selection "
                "awaits detailed bridge-chair assignment"
            ),
            "assignment_status": "confirmed ordinary or turnout assignment",
            "special_assignment_deferred": False,
            "validation_status": "validated",
            "key_orientation": "requires a configurable key-direction policy",
            "source_or_assumed_classification": "source-derived prototype requirement",
        })
        _require(isinstance(position.get("chair_footprint_parameters"), dict)
                 and position["chair_footprint_parameters"].get("dimension_classification")
                 == "source-derived prototype requirement",
                 "the original heel dimension classification differs")
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
             and original.get("chair_label") == (
                 expected["chair_code_label"] if r2_exit or crossing_tail or joint_exit
                 else "S1" if heel else "L1"
             ),
             "the original physical-plan binding differs")
    if not heel or name == "T2":
        reason = ("gauge normal is not perpendicular to the local rail tangent"
                  if heel else "special chair assignment remains analytical")
        _require(original.get("reason") == reason
                 and original.get("deliberate_omission") is False
                 and original.get("unresolved_special") is True,
                 "the original analytical exclusion differs")
    else:
        _require(type(original.get("chair_code")) is int
                 and original["chair_code"] == 1
                 and _finite(original.get("base_z")),
                 "the original S1 physical instance differs")


def _r2_finite_support(position, rail, timber, *, label="R2"):
    """Preserve the existing finite-support predicate and diagnostic owner."""
    return _finite_rail_timber_support(
        position, rail, timber, label=label, require=_require,
    )

def _crossing_tail_domain(module, dimensions, name, station, rail_code):
    """Retain the fixed 556b check, joint and wing predicate domain.

    The X9 opposing station uses the independently qualified 161-step
    get_xtimbcl2 result. Both bracketing inequalities must still hold;
    this is not a new general source-station solver.
    """
    fields = ("a_timber_x", "check_main_end_x", "check_turnout_end_x",
              "wing_end_main_x", "wing_flare_turnout_x", "flare_length",
              "flare_angle", "k3")
    _require(all(_finite(dimensions.get(key)) for key in fields),
             "crossing-tail source dimensions are not finite")
    joint = dimensions["a_timber_x"] + (12.5 + 5 * 30) / 3
    at_joint = joint - 13.5 / 3 < station < joint + 13.5 / 3
    if name != "X9-F":
        end = dimensions["check_main_end_x" if rail_code == 1
                         else "check_turnout_end_x"]
        _require(station > end - 4 / 3 and not at_joint,
                 "crossing-tail stock chair requires a check or joint family")
        return
    _require(at_joint, "X9-F no longer lies in its source joint interval")
    ratios = []
    for steps in (160, 161):
        shift = steps / 600
        _angle, gauge_y, branch = _source_pose(
            module, dimensions, station - shift, 2,
        )
        _require(branch == "turnoutst_main" and gauge_y > 16.5,
                 "X9-F opposing rail source branch differs")
        ratios.append(shift / (gauge_y - 16.5))
    _require(ratios[0] <= math.tan(dimensions["k3"] / 2) < ratios[1],
             "X9-F opposing source station differs")
    flare = dimensions["flare_angle"]
    _require(0 < flare < math.pi / 2 and dimensions["flare_length"] > 0,
             "X9-F source flare domain differs")
    # Regular source wing end, including the source /cos(flare) factor.
    turnout_end = (dimensions["wing_flare_turnout_x"]
                   + dimensions["flare_length"] / math.cos(flare)
                   * math.cos(dimensions["k3"] + flare))
    _require(station > dimensions["wing_end_main_x"] - 4 / 3
             and station - 160.5 / 600 > turnout_end - 4 / 3,
             "X9-F source still requires a wing-chair context")


def _joint_exit_domain(module, dimensions, name, station):
    """Bind the three fixed joint/exit rows to their 556b source predicates.

    R1 retains the independently qualified 186-step get_xtimbcl2 result.
    This does not admit the excluded X9 turnout-side stock position.
    """
    fields = ("a_timber_x", "check_main_end_x", "wing_end_main_x",
              "wing_flare_turnout_x", "flare_length", "flare_angle", "k3")
    _require(all(_finite(dimensions.get(key)) for key in fields),
             "joint-exit source dimensions are not finite")
    joint = dimensions["a_timber_x"] + (12.5 + 5 * 30) / 3
    _require(joint - 13.5 / 3 < station < joint + 13.5 / 3,
             "joint-exit source lies outside the joint-chair interval")
    if name == "X9-F":
        _require(station > dimensions["check_main_end_x"] - 4 / 3,
                 "X9-F main stock still requires a check-chair context")
        return
    ratios = []
    for steps in (185, 186):
        shift = steps / 600
        _angle, gauge_y, branch = _source_pose(
            module, dimensions, station - shift, 2,
        )
        _require(branch == "turnoutst_main" and gauge_y > 16.5,
                 "R1 opposing rail source branch differs")
        ratios.append(shift / (gauge_y - 16.5))
    _require(ratios[0] <= math.tan(dimensions["k3"] / 2) < ratios[1],
             "R1 opposing source station differs")
    flare = dimensions["flare_angle"]
    _require(0 < flare < math.pi / 2 and dimensions["flare_length"] > 0,
             "R1 source flare domain differs")
    turnout_end = (dimensions["wing_flare_turnout_x"]
                   + dimensions["flare_length"] / math.cos(flare)
                   * math.cos(dimensions["k3"] + flare))
    _require(station > dimensions["wing_end_main_x"] - 4 / 3
             and station - 185.5 / 600 > turnout_end - 4 / 3,
             "R1 source still requires a wing-chair context")


def exclude_turnout_heel_l1(module, document, source, placements, excluded):
    """Keep five source-selected L1 chairs out of the fixed TO S1 preview.

    Apply before S1 frame recovery so T2's original refusal cannot restore
    an S1 body. Other source contexts retain their existing selection.
    Qualification uses the same source predicates as the L1 preview.
    """
    signature, analysis, settings, plan, rails, timbers = source
    context = json.loads(signature)
    if (context.get("kind") != "turnout"
            or context.get("configuration", {}).get("turnout_id") != "TO-001"
            or context.get("analysis", {}).get("geometry_signature")
            != _ANALYSIS_SHA256):
        return placements, excluded
    config = _fixed_source(_configuration, module, context, settings, plan)
    positions = _indexed(analysis["positions"], "stable_chair_position_identity")
    rail_map = _indexed(rails, "stable_identity")
    timber_map = _indexed(timbers, "stable_identity")
    instances = _indexed(plan["instances"], "chair_position_identity")
    originals = _indexed(plan["analytical_only"], "chair_position_identity")
    _require(not instances.keys() & originals.keys(), "physical-plan records repeat")
    _obj, host, _signature = _fixed_source(_host, module, document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0), "identifier")
    corrections = {}
    for name, rail_code, _family_name in _SELECTION:
        if rail_code not in (1, 3):
            continue
        identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                    + dict(_RAILS)[rail_code].replace(" ", "-"))
        _require(identity in positions, "a source heel position is missing")
        position = positions[identity]
        timber = timber_map.get(position.get("timber_identity"), {})
        original = (originals if name == "T2" else instances).get(identity, {})
        _source_binding(position, rail_map.get(position.get("rail_identity"), {}),
                        timber, original, name, rail_code)
        _fixed_source(_timber_frame, module, host, config, timber, layout.get(name, {}))
        station = timber["source_configuration"]["local_x"]
        _require(_family(module, dimensions, name, station, rail_code) == "L1",
                 "the heel source no longer selects L1")
        corrections[identity] = {
            "position_id": identity, "chair_code": 1,
            "rail_id": position["rail_identity"], "timber_id": position["timber_identity"],
            "reason": "Source selects L1; use the TO-001 single-rail catalogue preview.",
            "replacement_family": "L1", "source_rail_code": rail_code,
            "original_position": copy.deepcopy(position),
            "original_plan_record": copy.deepcopy(original),
        }
    remaining = [item for item in excluded if item["position_id"] not in corrections]
    remaining.extend(corrections.values())
    return (tuple(p for p in placements if p.position_id not in corrections),
            sorted(remaining, key=lambda item: item["position_id"]))


def preview_private_catalogue_turnout_single_rail_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
    *, include_r2_exit=False, include_crossing_tail=False,
    include_joint_exit=False,
):
    """Create twelve assemblies with explicit source-qualified options.

    Admission is limited to the fixed left-hand TO-001 source. The source
    clearance selects S1 at T2 rail 4 despite its raw L1 candidate label.
    Existing catalogue verification and the adapter own safe materialisation.
    """
    _require(type(include_r2_exit) is bool, "include_r2_exit must be a boolean")
    _require(type(include_crossing_tail) is bool,
             "include_crossing_tail must be a boolean")
    _require(type(include_joint_exit) is bool,
             "include_joint_exit must be a boolean")
    _require(turnout_id == "TO-001" and callable(create_preview),
             "TO-001 and the native adapter are required")
    signature, analysis, settings, plan, rails, timbers = _open_source_context(
        module, source_document, turnout_id, "L1/S1",
    )
    context = json.loads(signature)
    config = _fixed_source(_configuration, module, context, settings, plan)
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
    prepared = {family: prepare_catalogue_chair(
        catalogue_path, family, run="existing-02",
    ) for family, _digest, _count in _MODELS}
    for family, digest, count in _MODELS:
        item = prepared[family]
        _require(item.label == family and item.run == "existing-02"
                 and item.model_sha256 == digest and len(item.components) == count,
                 "the qualified " + family + " catalogue differs")
    if include_joint_exit:
        item = prepare_catalogue_chair(catalogue_path, "S1J", run="basic-04")
        _require(item.label == "S1J" and item.run == "basic-04"
                 and item.context == "fixed-basic-source-context"
                 and item.model_sha256 == _S1J_MODEL and len(item.components) == 18,
                 "the qualified S1J catalogue differs")
        prepared["S1J"] = item
    obj, host, host_signature = _fixed_source(_host, module, source_document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0), "identifier")
    placements, selected = [], []
    represented = set()
    selection = _SELECTION + ((("R2", 2, "S1"), ("R2", 3, "S1"))
                              if include_r2_exit else ())
    if include_crossing_tail:
        selection += _CROSSING_TAIL
    if include_joint_exit:
        selection += _JOINT_EXIT
    for name, rail_code, family in selection:
        r2_exit = name == "R2"
        crossing_tail = (name, rail_code, family) in _CROSSING_TAIL
        joint_exit = (name, rail_code, family) in _JOINT_EXIT
        vee = (r2_exit or (crossing_tail and name == "X9-F")
               or (joint_exit and name == "R1"))
        identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                    + dict(_R2_RAILS if vee else _RAILS)[rail_code].replace(" ", "-"))
        heel = (name, rail_code) in _HEEL_SELECTION
        originals = instances if heel and name != "T2" else excluded
        _require(identity in positions and identity in originals,
                 "a selected position or its original plan record is missing")
        position = positions[identity]
        timber = timber_map.get(position.get("timber_identity"), {})
        _source_binding(position, rail_map.get(position.get("rail_identity"), {}),
                        timber, originals[identity], name, rail_code,
                        r2_exit=r2_exit, crossing_tail=crossing_tail,
                        joint_exit=joint_exit)
        if r2_exit or crossing_tail or joint_exit:
            _r2_finite_support(
                position, rail_map[position["rail_identity"]], timber,
                label=("joint-exit" if joint_exit else
                       "crossing-tail" if crossing_tail else "R2"),
            )
        station, point, heading = _fixed_source(
            _timber_frame, module, host, config, timber, layout.get(name, {}),
        )
        source_station = timber["source_configuration"]["local_x"]
        if crossing_tail:
            _crossing_tail_domain(
                module, dimensions, name, source_station, rail_code,
            )
        if joint_exit:
            _joint_exit_domain(module, dimensions, name, source_station)
        _require(_family(module, dimensions, name, source_station, rail_code) == family,
                 "the source clearance no longer selects the qualified family")
        angle, gauge_y, branch = _source_pose(
            module, dimensions, source_station, rail_code,
        )
        placement = place_left_hand_single_rail(
            identity, position["rail_identity"], position["timber_identity"],
            (point.x, point.y), heading, datums[0], family=family,
            source_rail_code=rail_code, source_angle_rad=angle,
            source_gauge_y_mm=gauge_y,
        )
        placements.append(placement)
        represented.add(identity)
        selected.append({
            "position_id": identity, "family": family,
            "prototype_timber_identifier": name, "source_rail_code": rail_code,
            "source_station_mm": source_station, "host_station_mm": station,
            "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
            "source_branch": branch, "source_handing": "LH",
            "source_model_sha256": prepared[family].model_sha256,
            "original_position": copy.deepcopy(position),
            "original_plan_record": copy.deepcopy(originals[identity]),
            "physical_fit": "NOT_PROVED",
        })
    shapes, verify_source = _context_shapes_and_verifier(
        module, source_document, turnout_id, "L1/S1", signature,
    )

    def verify_inputs():
        verify_source()
        current_obj, _data, current_host = _fixed_source(
            _host, module, source_document, config,
        )
        _require(current_obj is obj and current_host == host_signature,
                 "the canonical host changed during preview")
        for item in prepared.values():
            verify_catalogue_sources(item)

    receipt = {
        "document_name": source_document.Name, "turnout_id": turnout_id,
        "source_context_signature": "sha256:" + hashlib.sha256(signature.encode()).hexdigest(),
        "source_analysis_signature": analysis["geometry_signature"],
        "analysis_position_count": len(positions),
        "selected_family_counts": {
            family: sum(item["family"] == family for item in selected)
            for family in prepared
        },
        "represented_source_position_count": len(placements),
        "selected_positions": sorted(selected, key=lambda item: item["position_id"]),
        "corrected_heel_positions": sorted(
            (item for item in selected
             if (item["prototype_timber_identifier"], item["source_rail_code"])
             in _HEEL_SELECTION),
            key=lambda item: item["position_id"],
        ),
        "remaining_positions": [copy.deepcopy(position)
                                for identity, position in sorted(positions.items())
                                if identity not in represented],
        "original_analytical_exclusions": copy.deepcopy(plan["analytical_only"]),
        "original_physical_instances": copy.deepcopy(plan["instances"]),
        "source_base_z_mm": datums[0],
        "embedding_basis": "unchanged existing source-plan base_z",
        "model_support_adjustments_applied": False,
        "source_document_mutation": False,
        "limits": ["Private fixed TO-001 reference; no physical-fit acceptance.",
                   "Original analytical labels and exclusions remain unchanged.",
                   "No production, export, persistence or live-update authority.",
                   "Five original S1 records select L1 only in this private preview."],
    }
    ordered = tuple(sorted(placements, key=lambda item: item.position_id))
    options = {"include_r2_exit": True} if include_r2_exit else {}
    if include_crossing_tail:
        options["include_crossing_tail"] = True
    if include_joint_exit:
        options["include_joint_exit"] = True
    return create_preview(catalogue_path, ordered, shapes, receipt, verify_inputs, **options)
