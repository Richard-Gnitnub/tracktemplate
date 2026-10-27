"""Account for the final fifty fixed XO-001 source positions.

Templot 556b math_unit.pas:22760-22820,29750-30048 owns the crossing
sequence and exit family predicates. Source-informed, GPL-3.0-or-later;
see NOTICE.md and reference/PROVENANCE.md. Existing geometry, analytical
assignments and physical-fit limits remain unchanged.
"""

from collections import Counter
import hashlib
import json
import math

from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.application.chair_crossing_catalogue import (
    CROSSING_CONTEXT_IDS,
    prepare_crossing_catalogue,
    verify_crossing_catalogue,
)
from tracktemplate.compatibility.chair_pair_placement import _host_context
from tracktemplate.compatibility.chair_single_rail_placement import _source_pose
from tracktemplate.domain.chair_placement import place_paired_chair
from tracktemplate.domain.single_rail_placement import place_single_rail


def _require(condition, message):
    if not condition:
        raise ValueError("Private crossing and exit placement: " + message)


def _station(position, timber, side, layout):
    name = position["prototype_timber_identifier"]
    source = timber["source_configuration"]
    _require(source == position["source_configuration"]["timber"],
             "position and source timber disagree")
    if "local_x" in source:
        value = source["local_x"]
        _require(timber["stable_identity"] == f"XO-001:{side}:{name}",
                 "nominal timber identity differs")
    else:
        _require(source.get("extended_source_timber_identity")
                 == f"XO-001:{side}:{name}",
                 "extended source timber identity differs")
        value = source["path_station"]
    _require(type(value) in (int, float) and math.isfinite(value)
             and value == layout[name],
             "timber differs from its nominal source station")
    return value


def _source_records(positions, timbers, owners):
    """Keep source ownership distinct from approximate chair labels."""
    names = {
        "X1-Z": ("straight switch and closure rail",
                 "curved switch and closure rail"),
        "X2-Y": ("straight switch and closure rail",
                 "curved switch and closure rail"),
        "X3-X": ("turnout-side wing rail", "main-side wing rail",
                 "turnout-side wing knuckle", "main-side wing knuckle"),
        "X4-A": ("turnout-side wing rail", "main-side wing rail"),
        "X5-B": ("vee point rail", "vee splice rail",
                 "turnout-side wing flare", "main-side wing flare"),
        **{name: ("vee point rail", "vee splice rail")
           for name in ("X6-C", "X7-D", "X8-E", "R1", "R2")},
    }
    expected = {(side, timber, rail) for side in ("A", "B")
                for timber, rails in names.items() for rail in rails}
    records = {}
    for identity, position in positions.items():
        name = position["prototype_timber_identifier"]
        rail = position["rail_name"]
        if rail not in names.get(name, ()):
            continue
        side = owners.get(position["parent_turnout_identity"])
        key = side, name, rail
        timber = timbers[position["timber_identity"]]
        expected_id = ("XO-001:chair:"
                       + timber["stable_identity"].lower().replace(":", "-")
                       + ":" + rail.replace(" ", "-"))
        _require(key in expected and key not in records
                 and identity == position["stable_chair_position_identity"]
                 == expected_id and position["special_assignment_deferred"]
                 is True,
                 "crossing or exit source ownership is inconsistent")
        records[key] = position
    _require(set(records) == expected,
             "all forty-eight crossing and exit positions are required")
    return records, names


def _envelope_exclusions(positions, rails, timbers):
    """Prove the two endpoint-only candidates have no finite source anchor.

    The signed distance to the timber width axis separates the complete
    finite centreline from the actual timber rectangle. No railway or
    physical-fit tolerance is introduced. The canonical padded analysis
    and its identities remain untouched.
    """
    expected = {
        "XO-001:chair:xo-001-envelope-001:" + name
        for name in ("vee-point-rail", "vee-splice-rail")
    }
    result = {}
    for identity in expected:
        _require(identity in positions, "envelope source identity is missing")
        position = positions[identity]
        timber = timbers[position["timber_identity"]]
        rail = rails[position["rail_identity"]]
        points = rail["points"]
        _require(position["prototype_timber_identifier"] == "E001"
                 and timber["stable_identity"] == "XO-001:ENVELOPE:001"
                 and position["parent_turnout_identity"] == "XO-001-A001"
                 and len(points) >= 2
                 and position["centre_point"] == points[-1]
                 and position["source_configuration"]["timber"]
                 == timber["source_configuration"],
                 "envelope endpoint ownership differs")
        centre, axis = timber["centre"], timber["width_axis"]
        width = timber["width"]
        distances = [sum((point[i] - centre[i]) * axis[i]
                         for i in (0, 1)) for point in points]
        _require(type(width) in (int, float) and math.isfinite(width)
                 and width > 0 and all(math.isfinite(x) for x in distances)
                 and min(distances) > width / 2,
                 "envelope finite rail no longer has the proved separation")
        result[identity] = {
            "exclusion_kind": "source-anchor-outside-finite-rail-domain",
            "reason": "The finite rail ends before the actual envelope "
                      "timber. Its padded analytical endpoint supplies no "
                      "source chair anchor.",
            "canonical_position_is_rail_endpoint": True,
            "finite_rail_segment_count": len(points) - 1,
            "finite_rail_min_normal_mm": min(distances),
            "timber_half_width_mm": width / 2,
            "endpoint_outside_timber_mm": distances[-1] - width / 2,
            "analytical_padding_unchanged": True,
            "physical_fit": "NOT_ASSESSED",
        }
    return result


def _heel_discrepancies(module, dimensions, positions, layouts):
    """Identify ten preserved S1 choices without replacing their geometry."""
    result = []
    for side in ("A", "B"):
        for timber in ("S13", "T1", "T2"):
            station = layouts[side][timber]
            _angle, y, _branch = _source_pose(
                module, dimensions, station - 4 / 3, 4,
            )
            gap = y - 16.5
            _require(10.75 / 3 < gap < 15 / 3,
                     "retained heel source interval changed")
            for name, code in (("main-side stock rail", 1),
                               ("straight switch and closure rail", 3)):
                if code == 1 and gap >= 13.25 / 3:
                    continue
                identity = (f"XO-001:chair:xo-001-{side.lower()}-"
                            f"{timber.lower()}:" + name.replace(" ", "-"))
                _require(identity in positions
                         and positions[identity]["chair_code"] == 1
                         and positions[identity]["chair_code_label"] == "S1",
                         "accepted heel assignment changed")
                result.append({
                    "position_id": identity, "timber": timber,
                    "accepted_preview_family": "S1",
                    "source_family": "L1", "source_rail_code": code,
                    "source_station_mm": station, "source_gap_mm": gap,
                    "disposition": "preserved; required before Exit 9B-3",
                    "physical_fit": "NOT_PROVED",
                })
    _require(len(result) == 10, "accepted heel discrepancy set changed")
    return result


def prepare_crossing_exit(
    module, document, signature, positions, rails, timbers, base_z,
    catalogue_path, crossing_contexts_path,
):
    """Prepare twenty-four assemblies and two source-anchor exclusions.

    The existing paired admission must first bind the entire fixed XO-001
    signature and hosts. Return groups, witnesses, companion ownership,
    exclusions, preserved heel discrepancies and the late verifier.
    """
    prepared = prepare_crossing_catalogue(crossing_contexts_path)
    selections = {item.run: item for item in prepared}
    configuration = json.loads(signature)["configuration"]
    source_hash = hashlib.sha256(signature.encode()).hexdigest()
    hosts, data, objects = _host_context(module, document, configuration)
    host_hash = hashlib.sha256(json.dumps(
        hosts, sort_keys=True, allow_nan=False,
    ).encode()).hexdigest()
    _require(configuration["crossover_id"] == "XO-001"
             and all(item.metadata["source_context_sha256"] == source_hash
                     and item.metadata["host_context_sha256"] == host_hash
                     for item in prepared),
             "source or hosts differ from the qualified crossing context")
    owners = {configuration["turnout_" + side.lower() + "_id"]: side
              for side in ("A", "B")}
    timber_map = {item["stable_identity"]: item for item in timbers}
    rail_map = {item["stable_identity"]: item for item in rails}
    _require(len(timber_map) == len(timbers) and len(rail_map) == len(rails),
             "source rail or timber identities repeat")
    records, names = _source_records(positions, timber_map, owners)
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    singles = {family: prepare_catalogue_chair(
        catalogue_path, family, run="basic-04" if family == "S1J"
        else "existing-02",
    ) for family in ("S1", "S1J", "L1")}
    groups = {name: [] for name in (
        *CROSSING_CONTEXT_IDS, "ExitS1", "ExitS1J", "ExitL1",
    )}
    witnesses, companions, layouts = {}, {}, {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        _require(config["handing"] == module.TURNOUT_HAND_RIGHT,
                 "only the qualified right-hand context is supported")
        layout = {item["identifier"]: item["x"] for item in
                  module.rea_c10_timber_layout(dimensions,
                                              config["template_width"])}
        layouts[side] = layout
        direction = module._turnout_orientation_sign(config["orientation"])
        _require(direction in (-1.0, 1.0), "unsupported travel direction")
        for timber, rail_names in names.items():
            owner = records[side, timber, rail_names[0]]
            local_x = _station(owner, timber_map[owner["timber_identity"]],
                               side, layout)
            station = config["toe_chainage"] + direction * local_x
            _require(0 <= station <= data[side]["total"],
                     "source station lies outside its canonical host")
            point, heading = module.interpolate_alignment_station(data[side],
                                                                 station)
            travel = heading if direction > 0 else heading + math.pi
            for rail_name in rail_names:
                candidate = records[side, timber, rail_name]
                _require(candidate["timber_identity"] == owner["timber_identity"]
                         and _station(candidate,
                                      timber_map[candidate["timber_identity"]],
                                      side, layout) == local_x,
                         "source assembly companions disagree")
            if timber in ("R1", "R2"):
                for rail_name in rail_names:
                    position = records[side, timber, rail_name]
                    identity = position["stable_chair_position_identity"]
                    rail = 3 if rail_name == "vee point rail" else 2
                    _angle, gap_y, _branch = _source_pose(
                        module, dimensions, local_x - 4 / 3, 2,
                    )
                    gap = gap_y - 16.5
                    _require(gap >= 14.5 / 3,
                             "exit source requires a crossing chair")
                    joint = dimensions["a_timber_x"] + (12.5 + 5 * 30) / 3
                    family = ("S1J" if joint - 13.5 / 3 < local_x
                              < joint + 13.5 / 3 else "S1")
                    if gap < 19 / 3 and (rail == 2 or gap < 16.75 / 3):
                        family = "L1"
                    angle, gauge_y, branch = _source_pose(
                        module, dimensions, local_x, rail,
                    )
                    groups["Exit" + family].append(place_single_rail(
                        identity, position["rail_identity"],
                        position["timber_identity"], (point.x, point.y),
                        travel, base_z, family=family, source_rail_code=rail,
                        source_angle_rad=angle, source_gauge_y_mm=gauge_y,
                    ))
                    witnesses[identity] = {
                        "family": family, "context_id": f"RH-{timber}-rail-{rail}",
                        "source_model_sha256": singles[family].model_sha256,
                        "source_station_mm": local_x,
                        "host_station_mm": station,
                        "source_rail_code": rail, "source_branch": branch,
                        "source_angle_rad": angle,
                        "source_gauge_y_mm": gauge_y, "source_gap_mm": gap,
                        "placement_convention": "source-single-rail-component-frames.v1",
                        "physical_fit": "NOT_PROVED",
                    }
                continue
            context_id = "RH-" + timber
            selection = selections[context_id]
            recipe = selection.context
            _require(recipe["station_mm"] == local_x
                     and recipe["timber_id"] == timber
                     and recipe["native_frame"]["common_timber_curving_applied"]
                     is False,
                     "crossing recipe and source station disagree")
            identity = owner["stable_chair_position_identity"]
            groups[context_id].append(place_paired_chair(
                identity, owner["rail_identity"], owner["timber_identity"],
                (point.x, point.y), travel, base_z, 8.25, 0.45,
            ))
            mate_ids = [records[side, timber, name]["stable_chair_position_identity"]
                        for name in rail_names[1:]]
            companions.update({mate: identity for mate in mate_ids})
            witnesses[identity] = {
                "family": selection.label, "context_id": context_id,
                "source_model_sha256": selection.model_sha256,
                "source_context_sha256": recipe["context_sha256"],
                "source_station_mm": local_x, "host_station_mm": station,
                "source_rail_code": 3, "mate_position_ids": mate_ids,
                "placement_convention": "source-paired-common-timber-frame.v1",
                "physical_fit": "NOT_PROVED",
            }
    _require(len(witnesses) == 24 and len(companions) == 24
             and all(len(groups[name]) == 2 for name in CROSSING_CONTEXT_IDS)
             and Counter({key: len(groups[key]) for key in
                          ("ExitS1", "ExitS1J", "ExitL1")})
             == {"ExitS1": 4, "ExitS1J": 2, "ExitL1": 2},
             "qualified crossing or exit counts changed")
    exclusions = _envelope_exclusions(positions, rail_map, timber_map)
    heel = _heel_discrepancies(module, dimensions, positions, layouts)

    def verify():
        current, _data, current_objects = _host_context(module, document,
                                                       configuration)
        _require(current == hosts and all(current_objects[key] is value
                                         for key, value in objects.items()),
                 "canonical host changed during crossing and exit preview")
        verify_crossing_catalogue(prepared)
        for item in singles.values():
            verify_catalogue_sources(item)

    return ({key: tuple(sorted(values, key=lambda item: item.position_id))
             for key, values in groups.items()}, witnesses, companions,
            exclusions, heel, verify)
