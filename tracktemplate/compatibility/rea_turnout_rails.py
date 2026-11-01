"""Compose explicit source rails using the inherited sampling convention.

The unchanged legacy C10 rail builder remains the compatibility owner.
Only the explicit B/C source path replaces the affected wing/check paths.
"""

from tracktemplate.domain.rea_turnout import rea_turnout_source_rail_point


def rea_turnout_rail_polylines(module, dimensions):
    """Return ordered named rails with source actual-x wing/check paths."""
    rails = module.rea_c10_complete_rail_polylines(dimensions)
    inherited = dict(rails)
    replacements = {}

    def sample(start, finish, kind, outer, spacing):
        return [
            rea_turnout_source_rail_point(dimensions, x, kind, outer)
            for x in module._turnout_range_values(start, finish, spacing)
        ]

    for outer in (False, True):
        face = "outer face" if outer else "gauge face"
        suffix = "outer_" if outer else ""
        body_name = "turnout-side wing rail " + face
        flare_name = "turnout-side wing flare " + face
        flare_start = dimensions["wing_flare_turnout_" + suffix + "x"]
        flare_end = dimensions["wing_end_turnout_" + suffix + "x"]
        replacements[body_name] = sample(
            inherited[body_name][0][0], flare_start, "wing", outer, 0.50,
        )
        replacements[flare_name] = sample(
            flare_start, flare_end, "wing", outer, 0.50,
        )
        check_prefix = "check_turnout_" + suffix
        anchors = tuple(dimensions[check_prefix + key] for key in (
            "start_x", "flare_in_x", "flare_out_x", "end_x",
        ))
        replacements["turnout-side check rail " + face] = (
            module._turnout_join_local_segments(*[
                sample(start, finish, "check", outer, 0.40)
                for start, finish in zip(anchors[:-1], anchors[1:])
            ])
        )
    return [(name, replacements.get(name, points)) for name, points in rails]
