"""Compose explicit source rails using the inherited sampling convention.

The unchanged legacy C10 rail builder remains the compatibility owner.
Only the explicit B/C source path replaces the affected wing/check paths.
"""

from dataclasses import dataclass

from tracktemplate.domain.rea_turnout import (
    _source_straight_closure,
    rea_turnout_source_rail_point,
    rea_turnout_straight_point,
)


REA_INNER_GAUGE_BINDING = "_rea_c10_inner_gauge_face"
REA_INNER_GAUGE_CALLERS = (
    "_rea_c10_local_point", "_rea_c10_offset_from_inner",
    "_rea_c10_turnout_outer_gauge_point_at_x",
)


@dataclass(frozen=True)
class _ReaInnerGaugeAdapter:
    """Bind source lines within one inherited session; delegate other input."""

    original: object

    def __call__(self, dimensions, x_value):
        if type(dimensions) is dict and (
            "source_closure_kind" in dimensions
            or ("source_specification" in dimensions
                and _source_straight_closure(dimensions["k2"], dimensions["k3"]))
        ):
            point = rea_turnout_straight_point(dimensions, x_value)
            if point[0] > dimensions["heel_lead"]:
                return point
        return self.original(dimensions, x_value)


def validate_rea_inner_gauge_binding(module):
    """Refuse mixed inherited globals before source-line preparation."""
    namespace = module.__dict__
    adapter = namespace.get(REA_INNER_GAUGE_BINDING)
    if (type(adapter) is not _ReaInnerGaugeAdapter
            or getattr(adapter.original, "__globals__", None) is not namespace):
        raise ValueError("The source inner-gauge binding is unavailable.")
    for name in REA_INNER_GAUGE_CALLERS:
        caller = namespace.get(name)
        code = getattr(caller, "__code__", None)
        names = () if code is None else code.co_names
        if code is not None and name == REA_INNER_GAUGE_CALLERS[2]:
            # This inherited inversion owns a nested callback which resolves
            # the same module global, rather than an outer direct call.
            for nested in code.co_consts:
                if getattr(nested, "co_name", None) == "point_for_parameter":
                    names += nested.co_names
        if (getattr(caller, "__globals__", None) is not namespace
                or code is None or REA_INNER_GAUGE_BINDING not in names):
            raise ValueError("The source inner-gauge caller binding is mixed.")


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
