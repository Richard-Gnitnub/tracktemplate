"""Bind 34 additional single-rail chairs to the fixed private XO-001 source.

Source-informed selection from Templot 556b math_unit.pas:29551-29665,
29750-29831 and 37587-37603, GPL-3.0-or-later. See NOTICE.md and
reference/PROVENANCE.md. Canonical assignments and accepted placements
remain unchanged; this is not general source or physical-fit admission.
"""

from collections import Counter
import json
import math

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.domain.single_rail_placement import place_single_rail


def _require(condition, message):
    if not condition:
        raise ValueError("Private single-rail placement: " + message)


def _source_pose(module, dimensions, station, rail):
    if rail in (1, 3):
        return 0.0, 0.0 if rail == 1 else 16.5, "main_straight"
    if rail == 2:
        _x, gauge_y, angle = module._rea_c10_inner_gauge_face(dimensions, station)
        curve_end = dimensions["switch_curve_end_x"]
    else:
        _x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
            dimensions, station,
        )
        gauge_y = y + 8.25
        curve_end = (dimensions["switch_curve_end_x"]
                     - dimensions["gauge"] * math.sin(dimensions["k3"]))
    curved = station < curve_end
    _require(all(math.isfinite(value) for value in (gauge_y, angle, curve_end))
             and ((curved and 0 < angle < dimensions["k3"])
                  or (not curved and angle == dimensions["k3"])),
             "source branch differs from the qualified single rail")
    return angle, gauge_y, "radcurve" if curved else "turnoutst_main"


def _family(module, dimensions, timber, station, rail):
    """Apply the source clearance predicates inside the finite selected set."""
    if timber in ("S13", "T1", "T2"):
        _angle, y, _branch = _source_pose(module, dimensions, station - 4 / 3, 4)
        gap = y - 16.5
        _require(10.75 / 3 < gap < 15 / 3, "heel clearance interval changed")
        return "L1" if rail == 2 or gap < 13.25 / 3 else "S1"
    if timber == "T14":
        _angle, y, _branch = _source_pose(module, dimensions, station + 4 / 3, 2)
        _require(9.25 / 3 < 16.5 - y < 11 / 3,
                 "closure clearance interval changed")
        return "L1"
    if timber == "X9-F" and rail in (2, 3):
        _angle, y, _branch = _source_pose(module, dimensions, station - 4 / 3, 2)
        _require(14.5 / 3 < y - 16.5 < 16.75 / 3,
                 "vee clearance interval changed")
        return "L1"
    # All scoped outer stock positions follow the qualified check ends.
    # The exit-joint override applies after the ordinary S1 source choice.
    joint = dimensions["a_timber_x"] + (12.5 + 5 * 30) / 3
    return "S1J" if joint - 13.5 / 3 < station < joint + 13.5 / 3 else "S1"


def prepare_single_rails(
    module, document, signature, positions, timbers, base_z, catalogue_path,
):
    """Return complete groups, source witnesses and a late host verifier.

    The caller first qualifies the unchanged whole XO-001 signature and
    hosts through the paired catalogue. This function admits only its 17
    named source contexts on each turnout. B4 extensions must retain the
    original source identity and station; envelope stations are not used.
    """
    rails_by_timber = {
        "S13": {"curved switch and closure rail": 2,
                "turnout-side stock rail": 4},
        "T1": {"curved switch and closure rail": 2,
               "turnout-side stock rail": 4},
        "T2": {"curved switch and closure rail": 2,
               "turnout-side stock rail": 4},
        "T14": {"curved switch and closure rail": 2},
        **{timber: {"main-side stock rail": 1, "turnout-side stock rail": 4}
           for timber in ("X6-C", "X7-D", "X8-E")},
        "X9-F": {"main-side stock rail": 1, "turnout-side stock rail": 4,
                 "vee splice rail": 2, "vee point rail": 3},
    }
    family_groups = {"S1": "SupplementS1", "S1J": "SupplementS1J", "L1": "L1"}
    configuration = json.loads(signature)["configuration"]
    _require(configuration["crossover_id"] == "XO-001",
             "only the qualified XO-001 context is supported")
    hosts, data, objects = _host_context(module, document, configuration)
    selections = {family: prepare_catalogue_chair(
        catalogue_path, family, run="basic-04" if family == "S1J" else "existing-02",
    ) for family in family_groups}
    timber_map = {item["stable_identity"]: item for item in timbers}
    _require(len(timber_map) == len(timbers), "source timber identities repeat")
    owners = {configuration["turnout_" + side.lower() + "_id"]: side
              for side in ("A", "B")}
    expected = {(side, timber, rail) for side in ("A", "B")
                for timber, rails in rails_by_timber.items()
                for rail in rails.values()}
    candidates = {}
    for identity, position in positions.items():
        timber = position["prototype_timber_identifier"]
        rail = rails_by_timber.get(timber, {}).get(position["rail_name"])
        if rail is None:
            continue
        side = owners.get(position["parent_turnout_identity"])
        key = (side, timber, rail)
        timber_id = position["timber_identity"]
        expected_id = ("XO-001:chair:" + timber_id.lower().replace(":", "-")
                       + ":" + position["rail_name"].replace(" ", "-"))
        _require(key in expected and key not in candidates
                 and identity == position["stable_chair_position_identity"]
                 == expected_id and position["special_assignment_deferred"] is True,
                 "single-rail source ownership is inconsistent")
        candidates[key] = position
    _require(set(candidates) == expected, "all 34 single-rail positions are required")
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    groups = {name: [] for name in family_groups.values()}
    witnesses = {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT
                 and config["orientation"] in (
                     module.TURNOUT_ORIENTATION_FACING,
                     module.TURNOUT_ORIENTATION_TRAILING),
                 "only the qualified right-hand source is supported")
        layout = {item["identifier"]: item["x"] for item in
                  module.rea_c10_timber_layout(dimensions, config["template_width"])}
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for timber, rails in rails_by_timber.items():
            for rail in rails.values():
                position = candidates[side, timber, rail]
                identity = position["stable_chair_position_identity"]
                source = timber_map[position["timber_identity"]]["source_configuration"]
                _require(source == position["source_configuration"]["timber"],
                         "position and source timber disagree")
                if "local_x" in source:
                    local_x = source["local_x"]
                else:
                    _require(timber in ("X6-C", "X7-D", "X8-E", "X9-F")
                             and source.get("extended_source_timber_identity")
                             == f"XO-001:{side}:{timber}",
                             "extended source timber identity differs")
                    local_x = source["path_station"]
                _require(type(local_x) in (int, float) and math.isfinite(local_x)
                         and local_x == layout[timber],
                         "single-rail timber differs from its source station")
                family = _family(module, dimensions, timber, local_x, rail)
                angle, gauge_y, branch = _source_pose(module, dimensions, local_x, rail)
                station = config["toe_chainage"] + direction * local_x
                _require(0 <= station <= data[side]["total"],
                         "single-rail station lies outside its canonical host")
                point, heading = module.interpolate_alignment_station(data[side], station)
                travel = heading if direction > 0 else heading + math.pi
                groups[family_groups[family]].append(place_single_rail(
                    identity, position["rail_identity"], position["timber_identity"],
                    (point.x, point.y), travel, base_z, family=family,
                    source_rail_code=rail, source_angle_rad=angle,
                    source_gauge_y_mm=gauge_y,
                ))
                prepared = selections[family]
                witnesses[identity] = {
                    "family": family, "context_id": f"RH-{timber}-rail-{rail}",
                    "source_model_sha256": prepared.model_sha256,
                    "source_station_mm": local_x, "host_station_mm": station,
                    "source_rail_code": rail, "source_branch": branch,
                    "source_angle_rad": angle, "source_gauge_y_mm": gauge_y,
                    "placement_convention": "source-single-rail-component-frames.v1",
                    "fixing_head_rotation_rad": 0.0, "random_export_parity": False,
                    "fixing_angle_frame": "uncurved-RH-source-before-common-host-rotation",
                    "templot_global_fixing_angle_parity": False,
                    "physical_fit": "NOT_PROVED",
                }
    _require(Counter(item["family"] for item in witnesses.values())
             == {"L1": 16, "S1": 14, "S1J": 4}, "qualified family counts changed")

    def verify():
        current, _data, current_objects = _host_context(module, document, configuration)
        _require(current == hosts and all(current_objects[key] is value
                                         for key, value in objects.items()),
                 "canonical host changed during single-rail preview")
        for prepared in selections.values():
            verify_catalogue_sources(prepared)

    return ({name: tuple(sorted(values, key=lambda item: item.position_id))
             for name, values in groups.items()}, witnesses, verify)
