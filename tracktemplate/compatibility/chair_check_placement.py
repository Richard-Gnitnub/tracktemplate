"""Bind twelve source-supported central CC assemblies to frozen XO-001.

The existing paired admission must first qualify the complete source and
host fingerprints. These derived placements do not replace source labels,
deferred flags, key policy or analytical exclusions.
"""

import json
import math

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.central_check_placement import place_central_check


_TIMBERS = ("X2-Y", "X3-X", "X4-A")


def _require(condition, message):
    if not condition:
        raise ValueError("Private central CC placement: " + message)


def prepare_central_checks(
    module, document, signature, positions, timbers, base_z, catalogue_path,
):
    """Select the complete twelve stock owners and twelve check companions.

    Call only after prepare_crossover_pairs has bound this exact source and
    host. Source parallel-check intervals override inferred chair labels.
    The unchanged C10 rail calculation supplies the turnout gauge offset.
    Refuse incomplete, ambiguous or unsupported ownership before creation.
    """
    prepared = prepare_catalogue_chair(
        catalogue_path, "CC", run="context-native-02",
    )
    configuration = json.loads(signature)["configuration"]
    _require(configuration["crossover_id"] == "XO-001",
             "only the qualified XO-001 context is supported")
    hosts, data, objects = _host_context(module, document, configuration)
    timber_map = {item["stable_identity"]: item for item in timbers}
    placements, witnesses, companions = [], {}, {}
    expected = {
        f"XO-001:chair:xo-001-{owner}-{timber.lower()}:{side}-{rail}"
        for owner in ("a", "b") for timber in _TIMBERS
        for side in ("main-side", "turnout-side")
        for rail in ("stock-rail", "check-rail")
    }
    candidates = {identity: position for identity, position in positions.items()
                  if position["prototype_timber_identifier"] in _TIMBERS
                  and position["rail_name"] in (
                      "main-side stock rail", "turnout-side stock rail",
                      "main-side check rail", "turnout-side check rail")}
    _require(set(candidates) == expected,
             "the complete 24-position central source set is required")
    for owner in ("A", "B"):
        config = configuration["turnout_" + owner.lower() + "_config"]
        owner_id = configuration["turnout_" + owner.lower() + "_id"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT,
                 "only the qualified right-hand source is supported")
        dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
        for identifier in _TIMBERS:
            for rail_name, side in (("main-side", "MS"),
                                    ("turnout-side", "TS")):
                prefix = (f"XO-001:chair:xo-001-{owner.lower()}-"
                          f"{identifier.lower()}:{rail_name}-")
                identity, mate_id = prefix + "stock-rail", prefix + "check-rail"
                position, mate = candidates[identity], candidates[mate_id]
                _require(position["parent_turnout_identity"] == owner_id
                         and mate["parent_turnout_identity"] == owner_id
                         and position["timber_identity"] == mate["timber_identity"]
                         and position["special_assignment_deferred"] is True
                         and mate["special_assignment_deferred"] is True,
                         "central stock/check ownership is inconsistent")
                timber = timber_map[position["timber_identity"]]
                local_x = timber["source_configuration"]["local_x"]
                _require(local_x == dimensions["a_timber_x"]
                         + 10 * (_TIMBERS.index(identifier) - 2),
                         "central timber differs from its source station")
                direction = module._turnout_orientation_sign(config["orientation"])
                _require(direction in (-1.0, 1.0), "unsupported travel direction")
                station = config["toe_chainage"] + direction * local_x
                _require(0 <= station <= data[owner]["total"],
                         "central station lies outside its canonical host")
                point, heading = module.interpolate_alignment_station(
                    data[owner], station,
                )
                travel = heading if direction > 0 else heading + math.pi
                gauge_y, angle = 0.0, 0.0
                if side == "TS":
                    _x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
                        dimensions, local_x,
                    )
                    gauge_y = y + 8.25
                placements.append(place_central_check(
                    identity, position["rail_identity"], position["timber_identity"],
                    (point.x, point.y), travel, base_z, side=side,
                    source_angle_rad=angle, source_gauge_y_mm=gauge_y,
                ))
                companions[mate_id] = identity
                witnesses[identity] = {
                    "family": "CC", "context_id": f"RH-{side}-{identifier}",
                    "mate_position_id": mate_id,
                    "source_model_sha256": prepared.model_sha256,
                    "source_context_sha256": prepared.context["context_sha256"],
                    "source_station_mm": local_x, "host_station_mm": station,
                    "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
                    "source_crop_mm": 0.5, "source_shear_rad": 0.0,
                    "source_flare_mm": 0.0, "source_flangeway_mm": 1.0,
                    "placement_convention": "source-central-check-component-frames.v1",
                    "fixing_head_rotation_rad": 0.0, "random_export_parity": False,
                    "fixing_angle_frame": "uncurved-RH-source-before-common-host-rotation",
                    "templot_global_fixing_angle_parity": False,
                    "physical_fit": "NOT_PROVED",
                }

    def verify():
        current, _data, current_objects = _host_context(
            module, document, configuration,
        )
        _require(current == hosts and all(current_objects[key] is value
                                         for key, value in objects.items()),
                 "canonical host changed during central CC preview")
        verify_catalogue_sources(prepared)

    return (tuple(sorted(placements, key=lambda item: item.position_id)),
            witnesses, companions, verify)
