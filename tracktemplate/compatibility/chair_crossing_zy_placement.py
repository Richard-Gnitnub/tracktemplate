"""Bind two qualified ZY contexts to eight fixed XO-001 source records.

Templot 556b math_unit.pas:29831-29874 selects one ZY assembly on rail 3
with rail 2 as its companion. The source context, not the analytical
chair label, owns this selection. Source-informed, GPL-3.0-or-later;
see NOTICE.md and reference/PROVENANCE.md. No geometry is reconstructed.
"""

import hashlib
import json
import math

from tracktemplate.application.chair_crossing_zy_catalogue import (
    ZY_CONTEXT_IDS,
    prepare_zy_catalogue,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.chair_placement import place_paired_chair


_RAILS = ("straight switch and closure rail", "curved switch and closure rail")
_CANONICAL_CODES = (("X1-Z", (21, "ZY")), ("X2-Y", (22, "XN")))


def _require(condition, message):
    if not condition:
        raise ValueError("Private ZY crossing placement: " + message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def prepare_crossing_zy(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Return four placements, witnesses, companions and a late verifier.

    Model-mm geometry already contains source crops, shears, constituent
    rotations and base twist. Apply only the existing proper common host
    frame. Catalogue revalidation belongs to the native admission boundary.
    This operation neither changes source records nor admits new hosts.
    """
    prepared = prepare_zy_catalogue(contexts_path)
    _require(tuple(item.run for item in prepared) == ZY_CONTEXT_IDS,
             "both ordered ZY contexts are required")
    selections = {item.run: item for item in prepared}
    canonical_codes = dict(_CANONICAL_CODES)
    configuration = json.loads(signature)["configuration"]
    source_hash = hashlib.sha256(signature.encode()).hexdigest()
    _require(configuration["crossover_id"] == "XO-001"
             and all(item.metadata["source_context_sha256"] == source_hash
                     for item in prepared),
             "source differs from the qualified XO-001 context")
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(_encoded(hosts).encode()).hexdigest()
    _require(all(item.metadata["host_context_sha256"] == host_hash
                 for item in prepared),
             "host geometry differs from the qualified ZY context")
    owners = {configuration["turnout_" + side.lower() + "_id"]: side
              for side in ("A", "B")}
    _require(owners == {"XO-001-A001": "A", "XO-001-B001": "B"},
             "canonical turnout owners differ")
    timber_map = {item["stable_identity"]: item for item in timbers}
    _require(len(timber_map) == len(timbers), "source timber identities repeat")
    records = {}
    for identity, position in positions.items():
        timber = position["prototype_timber_identifier"]
        rail = position["rail_name"]
        if timber not in canonical_codes or rail not in _RAILS:
            continue
        owner = position["parent_turnout_identity"]
        _require(owner in owners, "unqualified turnout owner")
        side = owners[owner]
        timber_id = f"XO-001:{side}:{timber}"
        expected = ("XO-001:chair:" + timber_id.lower().replace(":", "-")
                    + ":" + rail.replace(" ", "-"))
        key = side, timber, rail
        _require(key not in records and identity == expected
                 == position["stable_chair_position_identity"]
                 and position["timber_identity"] == timber_id
                 and position["rail_identity"]
                 == owner + ":rail:" + rail.replace(" ", "-")
                 and (position["chair_code"], position["chair_code_label"])
                 == canonical_codes[timber]
                 and position["special_assignment_deferred"] is True
                 and position["deliberate_omission"] is False,
                 "canonical ZY source ownership or assignment differs")
        records[key] = position
    expected = {(side, timber, rail) for side in ("A", "B")
                for timber in canonical_codes for rail in _RAILS}
    _require(set(records) == expected, "all eight ZY source records are required")
    frozen_records = _encoded([positions, timbers])
    groups = {context: [] for context in ZY_CONTEXT_IDS}
    witnesses, companions = {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and config["track_gauge"] == 16.5,
                 "only the qualified right-hand gauge is supported")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for context_id in ZY_CONTEXT_IDS:
            selection = selections[context_id]
            recipe = selection.context
            timber_name = context_id[3:]
            owner, mate = (records[side, timber_name, rail] for rail in _RAILS)
            timber = timber_map[owner["timber_identity"]]
            source = timber["source_configuration"]
            local_x = source["local_x"]
            _require(type(local_x) in (int, float) and math.isfinite(local_x)
                     and owner["source_configuration"]["timber"] == source
                     == mate["source_configuration"]["timber"]
                     and selection.label == recipe["family"] == "ZY"
                     and recipe["chair_code"] == 21
                     and recipe["context_id"] == context_id
                     and recipe["timber_id"] == timber_name
                     and recipe["station_mm"] == local_x
                     and recipe["native_frame"]["common_timber_curving_applied"]
                     is False,
                     "qualified ZY recipe and source timber disagree")
            station = config["toe_chainage"] + direction * local_x
            _require(0 <= station <= data[side]["total"],
                     "ZY station lies outside its canonical host")
            point, heading = module.interpolate_alignment_station(data[side],
                                                                 station)
            travel = heading if direction > 0 else heading + math.pi
            identity = owner["stable_chair_position_identity"]
            mate_id = mate["stable_chair_position_identity"]
            groups[context_id].append(place_paired_chair(
                identity, owner["rail_identity"], owner["timber_identity"],
                (point.x, point.y), travel, base_z, 8.25, 0.45,
            ))
            companions[mate_id] = identity
            witnesses[identity] = {
                "family": "ZY", "source_chair_code": 21,
                "context_id": context_id,
                "source_model_sha256": selection.model_sha256,
                "source_context_sha256": recipe["context_sha256"],
                "source_station_mm": local_x, "host_station_mm": station,
                "source_rail_code": 3, "mate_position_ids": [mate_id],
                "placement_convention": "source-paired-common-timber-frame.v1",
                "physical_fit": "NOT_PROVED",
            }

    def verify():
        current, _data, current_objects = _host_context(module, document,
                                                       configuration)
        _require(hashlib.sha256(_encoded(current).encode()).hexdigest()
                 == host_hash and all(current_objects[key] is value
                                      for key, value in objects.items()),
                 "canonical host changed during ZY preview")
        _require(_encoded([positions, timbers]) == frozen_records,
                 "source records changed during ZY preview")

    return ({name: tuple(sorted(values, key=lambda item: item.position_id))
             for name, values in groups.items()}, witnesses, companions, verify)
