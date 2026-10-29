"""Place retained AA/CD/DD/EF assemblies on sixteen fixed XO-001 records.

Templot 556b math_unit.pas selects one assembly on rail 3 with rail 2
as its companion. B15 preserves those rails as wing rails at X4-A and
vee rails at X6-C through X8-E. Canonical labels remain unchanged.
Source-informed, GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
"""

import hashlib
import json
import math

from tracktemplate.application.chair_crossing_pair_catalogue import (
    CROSSING_PAIR_CONTEXT_IDS,
    prepare_crossing_pair_catalogue,
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
    _require(tuple(item.run for item in prepared) == CROSSING_PAIR_CONTEXT_IDS,
             "all four ordered crossing contexts are required")
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
    specifications = {item[0]: item[1:] for item in _SPECS}
    inherited = dict(_INHERITED)
    records = {}
    for identity, position in positions.items():
        name, rail = (position["prototype_timber_identifier"],
                      position["rail_name"])
        if name not in specifications or rail not in specifications[name][-1]:
            continue
        _, _, code, label, _ = specifications[name]
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
                for name, *_, rails in _SPECS for rail in rails}
    _require(set(records) == expected, "all sixteen source records are required")
    frozen_records = _encoded([positions, timbers])
    groups = {name: [] for name in CROSSING_PAIR_CONTEXT_IDS}
    witnesses, companions = {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and config["track_gauge"] == 16.5,
                 "only the qualified right-hand gauge is supported")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for name, family, code, _, _, rails in _SPECS:
            context_id = "RH-" + name
            selection = selections[context_id]
            recipe = selection.context
            owner, mate = (records[side, name, rail] for rail in rails)
            source = timber_map[owner["timber_identity"]]["source_configuration"]
            is_inherited = (side, name) in inherited
            if is_inherited:
                _require(source.get("extended_source_timber_identity")
                         == f"XO-001:{side}:{name}",
                         "inherited timber has a different source")
            local_x = source["path_station" if is_inherited else "local_x"]
            _require(type(local_x) in (int, float) and math.isfinite(local_x)
                     and owner["source_configuration"]["timber"] == source
                     == mate["source_configuration"]["timber"]
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
            mate_id = mate["stable_chair_position_identity"]
            groups[context_id].append(place_paired_chair(
                identity, owner["rail_identity"], owner["timber_identity"],
                (point.x, point.y), travel, base_z, 8.25, 0.45,
            ))
            companions[mate_id] = identity
            witnesses[identity] = {
                "family": family, "source_chair_code": code,
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
                 "canonical host changed during crossing preview")
        _require(_encoded([positions, timbers]) == frozen_records,
                 "source records changed during crossing preview")

    return ({name: tuple(sorted(values, key=lambda item: item.position_id))
             for name, values in groups.items()}, witnesses, companions, verify)
