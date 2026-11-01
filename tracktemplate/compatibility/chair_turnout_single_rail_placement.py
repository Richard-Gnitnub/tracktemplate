"""Bind seven retained single-rail assemblies to the fixed TO-001 source.

Templot 556b math_unit.pas:29551-29665 selects six L1 and one S1.
Source-informed adaptation is GPL-3.0-or-later; see NOTICE.md and
reference/PROVENANCE.md. Canonical labels, analytical exclusions and all
existing preview routes remain unchanged. This is not fit admission.
"""

import copy
import hashlib
import json

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_catalogue_placement import (
    _finite,
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
    _configuration,
    _host,
    _timber_frame,
)
from tracktemplate.domain.single_rail_placement import (
    place_left_hand_single_rail,
)


_RAILS = ((2, "curved switch and closure rail"),
          (4, "turnout-side stock rail"))
_SELECTION = (
    ("S13", 2, "L1"), ("S13", 4, "L1"),
    ("T1", 2, "L1"), ("T1", 4, "L1"),
    ("T14", 2, "L1"), ("T2", 2, "L1"), ("T2", 4, "S1"),
)
_MODELS = (
    ("L1", "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042", 23),
    ("S1", "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb", 17),
)


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


def _source_binding(position, rail, timber, original, name, rail_code):
    rail_name = dict(_RAILS)[rail_code]
    rail_id = "TO-001:rail:" + rail_name.replace(" ", "-")
    timber_id = "TO-001:timber:" + name
    identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                + rail_name.replace(" ", "-"))
    expected = {
        "stable_chair_position_identity": identity,
        "rail_identity": rail_id, "rail_name": rail_name,
        "rail_role": "stock rail" if rail_code == 4 else rail_name,
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
             and original.get("chair_label") == "L1"
             and original.get("reason") == "special chair assignment remains analytical"
             and original.get("deliberate_omission") is False
             and original.get("unresolved_special") is True,
             "the original analytical exclusion differs")


def preview_private_catalogue_turnout_single_rail_chairs(
    module, source_document, turnout_id, catalogue_path, create_preview,
):
    """Create seven private assemblies without changing analytical records.

    Admission is limited to the fixed left-hand TO-001 source. The source
    clearance selects S1 at T2 rail 4 despite its raw L1 candidate label.
    Existing catalogue verification and the adapter own safe materialisation.
    """
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
    obj, host, host_signature = _fixed_source(_host, module, source_document, config)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    layout = _indexed(module.rea_c10_timber_layout(dimensions, 32.0), "identifier")
    placements, selected = [], []
    represented = set()
    for name, rail_code, family in _SELECTION:
        identity = ("TO-001:chair:to-001-timber-" + name.lower() + ":"
                    + dict(_RAILS)[rail_code].replace(" ", "-"))
        _require(identity in positions and identity in excluded,
                 "a selected position is missing or already physical")
        position = positions[identity]
        timber = timber_map.get(position.get("timber_identity"), {})
        _source_binding(position, rail_map.get(position.get("rail_identity"), {}),
                        timber, excluded[identity], name, rail_code)
        station, point, heading = _fixed_source(
            _timber_frame, module, host, config, timber, layout.get(name, {}),
        )
        source_station = timber["source_configuration"]["local_x"]
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
        "selected_family_counts": {"L1": 6, "S1": 1},
        "represented_source_position_count": 7,
        "selected_positions": sorted(selected, key=lambda item: item["position_id"]),
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
                   "No production, export, persistence or live-update authority.",
                   "Five existing S1/L1 discrepancies remain outside this route."],
    }
    ordered = tuple(sorted(placements, key=lambda item: item.position_id))
    return create_preview(catalogue_path, ordered, shapes, receipt, verify_inputs)
