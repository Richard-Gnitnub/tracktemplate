"""Bind the qualified private paired assemblies to the frozen XO context.

This finite compatibility route preserves source identities and the host's
accepted station interpolation. It does not infer a source chair frame from
sampled rail tangents or admit an unqualified switch configuration.
"""

import hashlib
import json
import math

from tracktemplate.application.chair_pair_catalogue import (
    CONTEXT_IDS,
    prepare_paired_catalogue,
)
from tracktemplate.domain.chair_placement import place_paired_chair


def _require(condition, message):
    if not condition:
        raise ValueError("Private paired placement: " + message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def _host_context(module, document, configuration):
    records, data, objects = {}, {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        obj = document.getObject(config["host_object"])
        _require(obj is not None and not obj.Shape.isNull()
                 and obj.Shape.isValid(), "the canonical host is unavailable")
        host = module.turnout_host_alignment(obj)
        record = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in host["points"]],
            "headings": host["headings"], "stations": host["stations"],
            "total": host["total"], "toe_chainage": config["toe_chainage"],
            "orientation": config["orientation"], "handing": config["handing"],
        }
        records[side], data[side], objects[side] = record, host, obj
    return records, data, objects


def prepare_crossover_pairs(
    module, document, signature, positions, timbers, base_z, contexts_path,
):
    """Prepare all twenty source-bound placements or fail before creation.

    Return placement groups, per-position source witnesses, and a final
    host verifier. Catalogue bytes are independently reverified by the
    native adapter. The complete frozen source-context fingerprint binds
    the hand, switch, gauge, rail profile, stations and unshoved B4 timbers.
    A different context needs its own qualification; there is no fallback.
    """
    selections = {item.run: item
                  for item in prepare_paired_catalogue(contexts_path)}
    source_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    context = json.loads(signature)
    configuration = context["configuration"]
    _require(configuration["crossover_id"] == "XO-001",
             "only the qualified XO-001 context is supported")
    for prepared in selections.values():
        _require(prepared.metadata["source_context_sha256"] == source_hash,
                 "source configuration differs from the qualified context")
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(_encoded(hosts).encode()).hexdigest()
    _require(all(item.metadata["host_context_sha256"] == host_hash
                 for item in selections.values()),
             "host geometry differs from the qualified source context")
    timber_map = {item["stable_identity"]: item for item in timbers}
    owners = {
        configuration["turnout_" + side.lower() + "_id"]: side
        for side in ("A", "B")
    }
    rail_sides = {"main-side stock rail": "MS",
                  "turnout-side stock rail": "TS"}
    groups = {identity: [] for identity in CONTEXT_IDS}
    witnesses = {}
    for identity, position in sorted(positions.items()):
        if position["chair_code"] not in (11, 12):
            continue
        timber = timber_map[position["timber_identity"]]
        identifier = position["prototype_timber_identifier"]
        _require(identifier in ("S8", "S9", "S10", "S11", "S12")
                 and position["rail_name"] in rail_sides
                 and position["parent_turnout_identity"] in owners,
                 "unqualified paired source identity")
        side = owners[position["parent_turnout_identity"]]
        rail_side = rail_sides[position["rail_name"]]
        label = str(int(identifier[1:]) - 7) + "P"
        context_id = "RH-" + rail_side + "-" + label
        prepared = selections[context_id]
        recipe = prepared.context
        local_x = timber["source_configuration"]["local_x"]
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and recipe["station_mm"] == local_x
                 and recipe["timber_id"] == identifier
                 and recipe["chair_code"] == position["chair_code"]
                 and recipe["native_frame"]["common_timber_curving_applied"]
                 is False,
                 "paired recipe and source station disagree")
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        station = config["toe_chainage"] + direction * local_x
        _require(0 <= station <= data[side]["total"],
                 "paired station lies outside its canonical host")
        point, heading = module.interpolate_alignment_station(data[side], station)
        travel = heading if direction > 0 else heading + math.pi
        placement = place_paired_chair(
            identity, position["rail_identity"], position["timber_identity"],
            (point.x, point.y), travel, base_z, config["track_gauge"] / 2,
            0.45,
        )
        groups[context_id].append(placement)
        witnesses[identity] = {
            "family": label, "context_id": context_id,
            "source_model_sha256": prepared.model_sha256,
            "source_context_sha256": recipe["context_sha256"],
            "source_station_mm": local_x, "host_station_mm": station,
            "host_context_sha256": host_hash,
            "source_parameters": recipe["context"],
            "placement_convention": "source-paired-common-timber-frame.v1",
            "physical_fit": "NOT_PROVED",
        }
    _require(len(witnesses) == 20
             and all(len(group) == 2 for group in groups.values()),
             "the complete twenty-position source set is required")

    def verify_hosts():
        current, _data, current_objects = _host_context(
            module, document, configuration,
        )
        _require(current == hosts and all(current_objects[key] is obj
                                        for key, obj in objects.items()),
                 "canonical host changed during paired preview")

    return ({key: tuple(values) for key, values in groups.items()},
            witnesses, verify_hosts)
