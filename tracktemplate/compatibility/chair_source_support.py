"""Share fixed chair-source admission without importing placement routes.

These predicates preserve the existing Code 75 profile, finite support,
record identity and arithmetic budgets. They grant no physical-fit or
production acceptance and do not construct geometry.
"""

from fractions import Fraction
import math
from numbers import Real
import sys


# Exact compatibility values in the accepted fixed Code 75 source profile.
# They restrict this retained model; they do not introduce another standard.
_CODE75_PROFILE = (
    ("profile_id", "Templot556b-CL-EMGS-S4Soc-Code75-revA"),
    ("operator_label", "Templot C&L / EMGS / S4Soc Code 75 bullhead rev:A"),
    ("source_revision", "Templot5 556b, dxf_unit.pas init_rail_section"),
    ("scale_mm_per_foot", 4.0),
    ("vertical_rail", True),
    ("rail_depth_mm", 1.9),
    ("rail_head_width_mm", 0.9),
    ("rail_corner_radius_mm", 0.15),
    ("rail_foot_width_mm", 0.9),
    ("rail_fish_angle", 1.5),
    ("rail_web_top_from_top_mm", 0.8),
    ("rail_web_bottom_from_top_mm", 1.25),
    ("rail_web_thickness_mm", 0.35),
    ("rail_head_depth_mm", 0.5),
    ("rail_foot_depth_mm", 0.3499999999999999),
    ("rail_web_face_top_from_bottom_mm", 1.2166666666666666),
    ("rail_web_face_bottom_from_bottom_mm", 0.5333333333333332),
)

def _require(condition, message, *, family="P"):
    if not condition:
        raise ValueError(f"Private {family} placement: " + message)

def _indexed(records, field):
    _require(isinstance(records, list), "source records must be a list")
    result = {}
    for record in records:
        _require(isinstance(record, dict), "source record is not a mapping")
        identity = record.get(field)
        _require(isinstance(identity, str) and identity.strip()
                 and identity not in result, "source identity is ambiguous")
        result[identity] = record
    return result

def _finite(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

def _finite_rail_timber_support(position, rail, timber, *, label, require):
    """Require actual finite rail spans inside the scoped timber outline.

    Exact rational predicates use stored model-mm coordinates. A strict
    interior span must exist on each named finite face and centre polyline;
    an infinite continuation or boundary contact is insufficient. This is
    source-domain admission, not chair-footprint or physical-fit clearance.
    """
    def points(values, minimum):
        require(isinstance(values, (list, tuple)) and len(values) >= minimum
                 and all(isinstance(p, (list, tuple)) and len(p) == 2
                         and all(_finite(v) for v in p) for p in values),
                 label + " support geometry is not finite XY")
        return [tuple(Fraction(v) for v in p) for p in values]

    def sub(a, b):
        return a[0] - b[0], a[1] - b[1]

    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]

    def on_segment(p, a, b):
        return (cross(sub(b, a), sub(p, a)) == 0
                and all(min(a[i], b[i]) <= p[i] <= max(a[i], b[i]) for i in (0, 1)))

    polygon = points(timber.get("outline_polygon"), 3)
    require(len(set(polygon)) == len(polygon),
             label + " outline repeats a vertex")
    edges = list(zip(polygon, polygon[1:] + polygon[:1]))
    require(sum(cross(a, b) for a, b in edges) != 0,
             label + " outline is degenerate")
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges[i + 1:], i + 1):
            if j == i + 1 or (i == 0 and j == len(edges) - 1):
                continue
            r, s = sub(b, a), sub(d, c)
            denominator = cross(r, s)
            if denominator:
                t = cross(sub(c, a), s) / denominator
                u = cross(sub(c, a), r) / denominator
                intersects = 0 <= t <= 1 and 0 <= u <= 1
            else:
                intersects = any((on_segment(c, a, b), on_segment(d, a, b),
                                  on_segment(a, c, d), on_segment(b, c, d)))
            require(not intersects, label + " outline intersects itself")

    def inside(p):
        crossings = 0
        for a, b in edges:
            if on_segment(p, a, b):
                return False
            if (a[1] > p[1]) != (b[1] > p[1]):
                x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                crossings += p[0] < x
        return crossings % 2 == 1

    centre = points([position.get("centre_point")], 1)[0]
    require(inside(centre),
             label + " canonical centre is outside its finite timber")

    def supported(vertices):
        for a, b in zip(vertices, vertices[1:]):
            r = sub(b, a)
            if r == (0, 0):
                continue
            cuts = {Fraction(0), Fraction(1)}
            for c, d in edges:
                s = sub(d, c)
                denominator = cross(r, s)
                if denominator:
                    t = cross(sub(c, a), s) / denominator
                    u = cross(sub(c, a), r) / denominator
                    if 0 <= t <= 1 and 0 <= u <= 1:
                        cuts.add(t)
                elif cross(sub(c, a), r) == 0:
                    axis = 0 if r[0] else 1
                    cuts.update((p[axis] - a[axis]) / r[axis] for p in (c, d)
                                if on_segment(p, a, b))
            cuts = sorted(cuts)
            if any(inside(tuple(a[k] + (lo + hi) / 2 * r[k] for k in (0, 1)))
                   for lo, hi in zip(cuts, cuts[1:])):
                return True
        return False

    for field in ("gauge_face_points", "points", "outer_face_points"):
        require(supported(points(rail.get(field), 2)),
                 label + " finite " + field + " has no interior timber span")

def _require_context(
    module, context, turnout_id, settings, plan, *, family="P",
):
    """Refuse contexts beyond the retained fixed model's inputs."""
    config = context["configuration"]
    _require(
        context["kind"] == "turnout"
        and config.get("turnout_id") == turnout_id
        and config.get("size") == module.TURNOUT_SIZE_C10
        and module.TURNOUT_DEFAULT_SCALE == 76.2
        and plan.get("entity_kind") == "turnout"
        and plan.get("entity_id") == turnout_id,
        "one C10 turnout at 1:76.2 is required", family=family,
    )
    for field, expected in (("track_gauge", 16.5), ("flangeway", 1.0)):
        _require(_finite(config.get(field)) and config[field] == expected,
                 "unsupported " + field, family=family)
    _require_model_inputs(settings, plan, family=family)

def _require_model_inputs(settings, plan, *, family="P"):
    """Keep the complete fixed rail profile and source embedding binding."""
    profile = plan.get("rail_profile")
    expected_profile = dict(_CODE75_PROFILE)
    _require(isinstance(profile, dict) and profile == expected_profile
             and profile.get("vertical_rail") is True,
             "the complete fixed Code 75 revA profile is required",
             family=family)
    for field, expected in _CODE75_PROFILE:
        if type(expected) is float:
            _require(_finite(profile[field]), "invalid profile " + field,
                     family=family)
    _require(settings.get("rail_profile_id") == expected_profile["profile_id"],
             "analysis rail profile disagrees", family=family)
    _require(isinstance(plan.get("settings"), dict)
             and plan["settings"].get("embed_depth")
             == settings.get("future_chair_embed_depth")
             and _finite(settings.get("future_chair_embed_depth")),
             "source embedding settings disagree", family=family)


def _same_number(actual, expected):
    """Use the retained single-rail arithmetic budget, never a fit limit."""
    return (_finite(actual) and _finite(expected)
            and abs(actual - expected) <= 128 * sys.float_info.epsilon
            * max(1000.0, abs(actual), abs(expected)))
