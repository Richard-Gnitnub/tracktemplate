"""Bind eight retained check-end assemblies to the frozen XO-001 source.

Run only after the paired admission has verified the complete source and
host fingerprints. Source check-end calculations override inferred labels
in this derived view; canonical assignments and exclusions stay intact.
"""

import json
import math

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.check_end_placement import place_check_end


# RH source labels: heave_chairs.pas:1363-1400. The fixed 556b end
# selection overrides analytical labels; each assembly owns both rails.
_TARGETS = (("X1-Z", -30, "CCR", "CCL", 14),
            ("X5-B", 10, "CCL", "CCR", 16))


def _require(condition, message):
    if not condition:
        raise ValueError("Private check-end placement: " + message)


def prepare_check_ends(
    module, document, signature, positions, timbers, base_z, catalogue_path,
):
    """Qualify all sixteen stock/check IDs and return eight proper poses."""
    selections = {
        family: prepare_catalogue_chair(
            catalogue_path, family, run="context-native-02",
        ) for family in ("CCL", "CCR")
    }
    configuration = json.loads(signature)["configuration"]
    _require(configuration["crossover_id"] == "XO-001",
             "only the qualified XO-001 context is supported")
    hosts, data, objects = _host_context(module, document, configuration)
    timber_map = {item["stable_identity"]: item for item in timbers}
    expected = {
        f"XO-001:chair:xo-001-{owner}-{timber.lower()}:{side}-{rail}"
        for owner in ("a", "b") for timber, *_rest in _TARGETS
        for side in ("main-side", "turnout-side")
        for rail in ("stock-rail", "check-rail")
    }
    candidates = {
        identity: position for identity, position in positions.items()
        if position["prototype_timber_identifier"] in ("X1-Z", "X5-B")
        and position["rail_name"] in (
            "main-side stock rail", "turnout-side stock rail",
            "main-side check rail", "turnout-side check rail")
    }
    _require(set(candidates) == expected,
             "the complete sixteen-position check-end source is required")
    groups = {family: [] for family in selections}
    witnesses, companions = {}, {}
    alpha, flare = math.atan(1 / 18), 49 * (1 / 3) / 64
    for owner in ("A", "B"):
        config = configuration["turnout_" + owner.lower() + "_config"]
        owner_id = configuration["turnout_" + owner.lower() + "_id"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT,
                 "only the qualified right-hand source is supported")
        _require(config["orientation"] in (
            module.TURNOUT_ORIENTATION_FACING,
            module.TURNOUT_ORIENTATION_TRAILING,
        ), "unsupported travel orientation")
        dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
        # Templot 556b math_unit.pas:4735,17766-17790. The outer stock
        # rail leaves the closure circle before the crossing tangent.
        curve_end = (dimensions["switch_curve_end_x"]
                     - dimensions["gauge"] * math.sin(dimensions["k3"]))
        _require(math.isfinite(curve_end), "invalid source branch boundary")
        for identifier, offset, main_family, turnout_family, code in _TARGETS:
            for rail_name, side, family in (
                ("main-side", "MS", main_family),
                ("turnout-side", "TS", turnout_family),
            ):
                prefix = (f"XO-001:chair:xo-001-{owner.lower()}-"
                          f"{identifier.lower()}:{rail_name}-")
                identity, mate_id = prefix + "stock-rail", prefix + "check-rail"
                position, mate = candidates[identity], candidates[mate_id]
                _require(position["parent_turnout_identity"] == owner_id
                         and mate["parent_turnout_identity"] == owner_id
                         and position["timber_identity"] == mate["timber_identity"]
                         and position["special_assignment_deferred"] is True
                         and mate["special_assignment_deferred"] is True,
                         "check-end stock/check ownership is inconsistent")
                timber = timber_map[position["timber_identity"]]
                local_x = timber["source_configuration"]["local_x"]
                _require(local_x == dimensions["a_timber_x"] + offset,
                         "check-end timber differs from its source station")
                direction = module._turnout_orientation_sign(config["orientation"])
                _require(direction in (-1.0, 1.0), "unsupported travel direction")
                station = config["toe_chainage"] + direction * local_x
                _require(0 <= station <= data[owner]["total"],
                         "check-end station lies outside its canonical host")
                point, heading = module.interpolate_alignment_station(
                    data[owner], station,
                )
                travel = heading if direction > 0 else heading + math.pi
                angle, gauge_y = 0.0, 0.0
                branch = "main_straight"
                if side == "TS":
                    _x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
                        dimensions, local_x,
                    )
                    gauge_y = y + 8.25
                    curved = local_x < curve_end
                    _require(
                        (identifier == "X1-Z" and curved
                         and 0 < angle < dimensions["k3"])
                        or (identifier == "X5-B" and not curved
                            and angle == dimensions["k3"]),
                        "source branch differs from the qualified check end",
                    )
                    branch = "radcurve" if curved else "turnoutst_main"
                groups[family].append(place_check_end(
                    identity, position["rail_identity"], position["timber_identity"],
                    (point.x, point.y), travel, base_z, side=side, family=family,
                    source_angle_rad=angle, source_gauge_y_mm=gauge_y,
                ))
                companions[mate_id] = identity
                prepared = selections[family]
                witnesses[identity] = {
                    "family": family, "context_id": f"RH-{side}-{identifier}",
                    "mate_position_id": mate_id, "source_chair_code": code,
                    "source_model_sha256": prepared.model_sha256,
                    "source_context_sha256": prepared.context["context_sha256"],
                    "source_station_mm": local_x, "host_station_mm": station,
                    "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
                    "source_rail_code": 1 if side == "MS" else 4,
                    "source_branch": branch,
                    "source_curve_end_station_mm": (
                        None if side == "MS" else curve_end
                    ),
                    "source_crop_mm": 0.5 + flare,
                    "source_inner_shear_rad": -alpha if family == "CCL" else alpha,
                    "source_outer_shear_rad": alpha if family == "CCL" else -alpha,
                    "source_flare_mm": flare, "source_flare_angle_rad": alpha,
                    "source_flangeway_mm": 1.0,
                    "placement_convention": "source-check-end-component-frames.v1",
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
                 "canonical host changed during check-end preview")
        for prepared in selections.values():
            verify_catalogue_sources(prepared)

    return ({family: tuple(sorted(values, key=lambda item: item.position_id))
             for family, values in groups.items()}, witnesses, companions, verify)
