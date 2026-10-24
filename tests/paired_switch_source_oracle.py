"""Read-only source oracle for the private C-switch paired-chair proof.

This source-informed comparison follows Templot5 revision 556b, copyright
Martin Wynne and OpenTemplot contributors, under GPL-3.0-or-later. See
NOTICE.md and reference/PROVENANCE.md. Source data remain reference-only;
this helper gives no physical-fit, production or rights acceptance.

The oracle does not import TrackTemplate, a retained recipe or a generator.
It reads dimensional inputs from the frozen active Pascal units. Its
analytic stock-rail circles independently check the retained numerical
normal-offset inversion. Returned distances are mm and angles are radians.
"""

import ast
import bisect
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import re


SOURCE_HASHES = {
    "math_unit.pas":
        "341c6aeeb4d3136d9f85688453dbd4e4163c8543efe6ce9362aba8c505b55a65",
    "dxf_unit.pas":
        "f6bd9cbe8ef63397f4a632535f7160a7e6f82498a334bcde8580c9d0ed5b4f8d",
    "chairs_unit.pas":
        "0a996ea4ad6fa7556dde43f6af0a1e41463112d3f69c4efce3dd3c29406dc21b",
    "switch_select.pas":
        "0412d14ee0b3a7dc223031438bdd93d21aa08d629d1e987089dd9241c10f4ffb",
    "OpenTemplot2024.lpr":
        "ceefe944c2300f5dedea7eb64778d4048f0b1545daa4052cf023aa02d67d5766",
}
SOURCE_REFERENCES = {
    "switch": "switch_select.pas:1804-1859; math_unit.pas:3026-3072",
    "rail_offsets": "math_unit.pas:4723,7565-7628,9035-9103,17792-17932",
    "dimensions": "chairs_unit.pas:1011-1036; math_unit.pas:29209-29240",
    "main_anchor": "math_unit.pas:30130-30181,30258,30315-30434",
    "turnout_anchor": "math_unit.pas:31602-31724,31779-31892",
    "jaw_parameters": "dxf_unit.pas:6968-7028",
    "block_insertion": "dxf_unit.pas:11880-11910,11998-12005,12064-12071",
    "common_transform": "math_unit.pas:24387-24407,28273-28313,29459-29465",
}


def _number(expression):
    """Read a literal rational expression without evaluating source code."""
    node = ast.parse(expression.strip(), mode="eval").body

    def value(item):
        if isinstance(item, ast.Constant) and type(item.value) in (int, float):
            return Fraction(str(item.value))
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.USub):
            return -value(item.operand)
        if isinstance(item, ast.BinOp):
            left, right = value(item.left), value(item.right)
            if isinstance(item.op, ast.Add):
                return left + right
            if isinstance(item.op, ast.Sub):
                return left - right
            if isinstance(item.op, ast.Div):
                return left / right
        raise ValueError("The source dimension is not a literal rational")

    return value(node)


def _assignment(text, name):
    matches = re.findall(r"\b" + re.escape(name) + r"\s*:=([^;]+);", text)
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous source assignment: " + name)
    return _number(matches[0])


def source_parameters(source_directory, *, scale_mm_per_inch, gauge_mm,
                      flangeway_mm, rail_head_width_mm, crossing_ratio):
    """Read frozen active source; keep model/profile inputs explicit."""
    directory = Path(source_directory)
    texts = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (directory / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("The source identity changed: " + name)
        texts[name] = raw.decode("latin-1")
    project = texts["OpenTemplot2024.lpr"]
    if "chairs_unit in 'chairs_unit.pas'" not in project:
        raise ValueError("The active chair unit is not established")
    switch = texts["switch_select.pas"].split(
        "// BH  size  C+  semi-curved  flexible  switch  ( REA )", 1
    )[1].split("add_to_list(2,3,6,", 1)[0]
    chairs = texts["chairs_unit.pas"].split(
        "inner_trim_stock_rail:=", 1
    )[1].split("// block heel chairs", 1)[0]
    chairs = "inner_trim_stock_rail:=" + chairs
    source_chairs = {
        name: _assignment(chairs, name)
        for name in (
            "inner_trim_stock_rail", "PLR1_block_slide_chair_inlong",
            "PLR1_chair_outlong", "PLR1_chair_inlong",
            "PLR1_chair_halfwide", "PLR1_inbolt_1x", "PLR1_inbolt_2x",
            "PLR1_outbolt_1x", "PLR1_outbolt_2x", "PLR1_bolts_from_end",
            "PLR1_chair_crad_inner", "PLR1_chair_crad_outer",
        )
    }
    source_chairs["PLR3_block_heel_chair_inlong"] = _assignment(
        texts["chairs_unit.pas"], "PLR3_block_heel_chair_inlong",
    )
    fields = {
        name: _assignment(switch, "sw_init_info." + name)
        for name in ("planing", "heel_lead_inches", "planing_angle",
                     "switch_radius_inchormax", "num_slide_chairs",
                     "num_block_slide_chairs", "num_block_heel_chairs")
    }
    spacings = [
        _assignment(switch, f"sw_init_info.timber_centres[{index}]")
        for index in range(12)
    ]
    numbers = (scale_mm_per_inch, gauge_mm, flangeway_mm,
               rail_head_width_mm, crossing_ratio)
    if any(type(item) not in (int, float) or not math.isfinite(item)
           or item <= 0 for item in numbers):
        raise ValueError("Source model inputs must be finite and positive")
    return {
        "scale_mm_per_inch": float(scale_mm_per_inch),
        "gauge_mm": float(gauge_mm), "flangeway_mm": float(flangeway_mm),
        "rail_head_width_mm": float(rail_head_width_mm),
        "crossing_ratio": float(crossing_ratio),
        "switch": fields, "chair_inches": source_chairs,
        "timber_spacing_inches": spacings,
        "source_hashes": dict(SOURCE_HASHES),
        "source_status": "reference-only",
    }


def _circles(parameters):
    """Resolve circle centres from source switch and crossing equations."""
    switch = parameters["switch"]
    scale = parameters["scale_mm_per_inch"]
    radius = float(switch["switch_radius_inchormax"]) * scale
    heel_x = float(switch["heel_lead_inches"]) * scale
    planing_angle = math.atan(1 / float(switch["planing_angle"]))
    planing_x = float(switch["planing"]) * scale * math.cos(planing_angle)
    heel_angle = math.asin(
        (heel_x - planing_x) / radius + math.sin(planing_angle)
    )
    heel_y = (planing_x / float(switch["planing_angle"])
              + radius * math.cos(planing_angle)
              - radius * math.cos(heel_angle))
    crossing_angle = math.atan(1 / parameters["crossing_ratio"])
    # Source regular-crossing entry straight is 2*flangeway*N.
    curve_end_y = parameters["gauge_mm"] - 2 * parameters["flangeway_mm"]
    turnout_radius = ((curve_end_y - heel_y)
                      / (math.cos(heel_angle) - math.cos(crossing_angle)))
    return {
        "switch": (radius, heel_x - radius * math.sin(heel_angle),
                   heel_y + radius * math.cos(heel_angle)),
        "closure": (
            turnout_radius, heel_x - turnout_radius * math.sin(heel_angle),
            heel_y + turnout_radius * math.cos(heel_angle),
        ),
        "heel_x_mm": heel_x, "heel_angle_rad": heel_angle,
        "planing_x_mm": planing_x,
    }


def rail_offset(parameters, station_mm, rail_code):
    """Calculate aq2/aq3 analytically, including their different heels."""
    if rail_code not in (2, 3):
        raise ValueError("Only source gauge rails 2 and 3 are supported")
    circles = _circles(parameters)
    offset = parameters["gauge_mm"] if rail_code == 3 else 0.0
    heel = (circles["heel_x_mm"]
            - offset * math.sin(circles["heel_angle_rad"]))
    branch = "switch" if station_mm < heel else "closure"
    radius, centre_x, centre_y = circles[branch]
    radius -= offset
    x = station_mm - centre_x
    if (not math.isfinite(station_mm)
            or station_mm <= circles["planing_x_mm"]
            or abs(x) >= radius):
        raise ValueError("The station is outside the bounded switch oracle")
    return {
        "y_mm": centre_y - math.sqrt(radius * radius - x * x),
        "k_rad": math.asin(x / radius), "branch": branch,
        "heel_boundary_mm": heel,
    }


def nominal_station(parameters, timber_id):
    """Return the source spacing sum for one S8-S12 support."""
    if timber_id not in ("S8", "S9", "S10", "S11", "S12"):
        raise ValueError("The timber is outside the bounded source oracle")
    count = int(timber_id[1:])
    total = sum(parameters["timber_spacing_inches"][:count], Fraction())
    return float(total) * parameters["scale_mm_per_inch"]


def _rotate(point, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    return (point[0] * cosine - point[1] * sine,
            point[0] * sine + point[1] * cosine)


def expected_local_pair(parameters, timber_id, side, hand, *, station_mm=None):
    """Return source marks before and after the whole-chair transformation.

    Only nominal square switch timbers and solid jaws belong to this
    oracle. ``station_mm`` preserves the actual canonical binary float;
    the caller must separately compare it with ``nominal_station``.
    Final coordinates have X relative to the timber station, main gauge
    Y=0 after the source handed reflection, and rail-top Z=0.
    """
    if (side not in ("MS", "TS") or type(hand) is not int
            or hand not in (-1, 1)):
        raise ValueError("The source side or handedness is unsupported")
    x = nominal_station(parameters, timber_id)
    if station_mm is not None:
        x = float(station_mm)
    family_number = int(timber_id[1:]) - 7
    code = 11 if family_number <= 2 else 12
    scale = parameters["scale_mm_per_inch"]
    dimensions = parameters["chair_inches"]
    mm = {name: float(value) * scale for name, value in dimensions.items()}
    aq2, aq3 = rail_offset(parameters, x, 2), rail_offset(parameters, x, 3)
    extra = ("PLR1_block_slide_chair_inlong" if code == 11
             else "PLR3_block_heel_chair_inlong")
    outlong = mm["PLR1_chair_outlong"]
    inlong = aq2["y_mm"] + mm[extra]
    chair_mod = (outlong - inlong) / 2
    angle = 0.0 if side == "MS" else aq3["k_rad"]
    chair_y = 0.0 if side == "MS" else aq3["y_mm"]
    midx = x if side == "MS" else x + chair_mod * math.sin(angle)
    second = rail_offset(parameters, midx, 2 if side == "MS" else 3)
    gap = second["y_mm"]
    sign = 1 if side == "MS" else -1
    if side == "TS":
        gap -= parameters["gauge_mm"]
    half = mm["PLR1_chair_halfwide"]
    inner_radius = mm["PLR1_chair_crad_inner"]
    outer_radius = mm["PLR1_chair_crad_outer"]
    corners = [
        [midx - half + outer_radius, sign * (-outlong + outer_radius)],
        [midx - half + inner_radius, sign * (inlong - inner_radius)],
        [midx + half - inner_radius, sign * (inlong - inner_radius)],
        [midx + half - outer_radius, sign * (-outlong + outer_radius)],
    ]
    bolts = [
        [midx + mm[f"PLR1_inbolt_{index}x"],
         sign * (inlong - mm["PLR1_bolts_from_end"])]
        for index in (1, 2)
    ] + [
        [midx + mm[f"PLR1_outbolt_{index}x"],
         sign * (-outlong + mm["PLR1_bolts_from_end"])]
        for index in (1, 2)
    ]

    def final(point):
        px, py = _rotate((point[0] - x, point[1]), angle)
        return [px, hand * (py + chair_y)]

    stock_marks = [[midx - half, 0.0], [midx + half, 0.0]]
    slope = math.tan(second["k_rad"])
    switch_marks = [[midx - half, sign * (gap - half * slope)],
                    [midx + half, sign * (gap + half * slope)]]
    shear = -sign * second["k_rad"] * hand
    crop_gap = gap if side == "MS" else gap / math.cos(second["k_rad"])
    crop = crop_gap - mm["inner_trim_stock_rail"]
    if code == 11:
        crop -= parameters["rail_head_width_mm"]
    else:
        crop = -crop
    switch_prefixes = ("MM",) if code == 11 else ("MN", "MH")
    if side == "TS":
        switch_prefixes = ("TM",) if code == 11 else ("TN", "TH")
    components = []
    names = ["SCOUTJAW", "SCINJAW", "SCCCSEAT", "KEY"]
    names += list(switch_prefixes)
    names.append("PLR1SEAT" if code == 11 else "PLR3SEAT")
    if code == 12:
        names.append("KEY")
    for index, name in enumerate(names):
        marks = stock_marks if index < 4 else switch_marks
        transformed = [final(point) for point in marks]
        start, end = transformed
        insertion_angle = math.atan2(end[1] - start[1], end[0] - start[0])
        if hand == -1:
            insertion_angle += math.pi
        if side == "TS":
            insertion_angle += math.pi
        while insertion_angle > 2 * math.pi:
            insertion_angle -= 2 * math.pi
        components.append({
            "source_block": name,
            "source_endpoints_mm": [[p[0] - x, p[1]] for p in marks],
            "transformed_endpoints_mm": transformed,
            "insertion": {
                "x_mm": (start[0] + end[0]) / 2,
                "y_mm": (start[1] + end[1]) / 2,
                "z_mm": 0.0, "rotation_rad": insertion_angle,
            },
        })
    context = {
        "side": side, "hand_i": hand, "rail_code": 1 if side == "MS" else 4,
        "timber_id": timber_id, "xtimbcl_mm": x,
        "chair_midx_mm": midx, "chair_k_rad": angle,
        "chair_y_mm": chair_y, "chair_mod_mm": chair_mod,
        "aq_y_mm": second["y_mm"], "aq_k_rad": second["k_rad"],
        "aq2_y_at_timber_mm": aq2["y_mm"],
        "aq2_k_at_timber_rad": aq2["k_rad"],
        "aq3_y_at_timber_mm": aq3["y_mm"],
        "aq3_k_at_timber_rad": aq3["k_rad"],
    }
    return {
        "family": f"{family_number}P", "chair_code": code,
        "context": context, "aq_branch": second["branch"],
        "base": {
            "corner_centres_mm": [[p[0] - x, p[1]] for p in corners],
            "bolt_centres_mm": [[p[0] - x, p[1]] for p in bolts],
            "transformed_corner_centres_mm": [final(p) for p in corners],
            "transformed_bolt_centres_mm": [final(p) for p in bolts],
            "outlong_mm": outlong, "inlong_mm": inlong,
            "half_width_mm": half,
        },
        "jaw_parameters": {
            "stock_inner_crop_mm": mm["inner_trim_stock_rail"],
            "switch_shear_rad": shear, "switch_outer_crop_mm": crop,
            "switch_inner_crop_mm": 0.0,
        },
        "components": components,
        "source_status": "reference-only",
    }


def expected_base_point(local_record, retained_main_side_point):
    """Apply source side, chair pose and hand to one retained base point.

    The retained input is the proven uncurved main-side base, relative to
    the nominal timber station. This checks source placement of existing
    geometry; it does not reconstruct the base or claim physical fit.
    """
    context = local_record["context"]
    point = list(retained_main_side_point)
    if context["side"] == "TS":
        point[0] += context["chair_midx_mm"] - context["xtimbcl_mm"]
        point[1] = -point[1]
    x, y = _rotate(point, context["chair_k_rad"])
    result = [x, context["hand_i"] * (y + context["chair_y_mm"])]
    if len(point) == 3:
        result.append(point[2])
    return result


def expected_world_frame(host, *, toe_chainage_mm, direction, hand,
                         station_mm, gauge_mm):
    """Map the already handed source frame through one host rotation.

    The caller captures canonical host arrays directly from the source
    document. Independent interpolation preserves its established sampled
    host contract; no target rail tangent or product placement is read.
    The timber equalising pivot cancels: y is measured from the main gauge
    after reflection, so its centreline offset is -hand*gauge/2.
    """
    if (type(direction) is not int or direction not in (-1, 1)
            or type(hand) is not int or hand not in (-1, 1)):
        raise ValueError("The source direction or hand is unsupported")
    stations, points, headings = (host[name] for name in
                                  ("stations", "points", "headings"))
    if not len(stations) == len(points) == len(headings) or len(stations) < 2:
        raise ValueError("The canonical host arrays are incomplete")
    target = toe_chainage_mm + direction * station_mm
    if not stations[0] <= target <= stations[-1]:
        raise ValueError("The source station is outside the canonical host")
    index = min(bisect.bisect_right(stations, target) - 1, len(stations) - 2)
    span = stations[index + 1] - stations[index]
    if span <= 0:
        raise ValueError("The canonical host station interval is invalid")
    fraction = (target - stations[index]) / span
    centre = [points[index][axis] + fraction * (
        points[index + 1][axis] - points[index][axis]
    ) for axis in (0, 1)]
    heading = headings[index] + fraction * (
        headings[index + 1] - headings[index]
    )
    if direction == -1:
        heading += math.pi
    tangent = [math.cos(heading), math.sin(heading)]
    normal = [-tangent[1], tangent[0]]
    origin = [centre[axis] - hand * gauge_mm * normal[axis] / 2
              for axis in (0, 1)]
    return {"origin_mm": origin, "x_axis": tangent, "y_axis": normal,
            "host_chainage_mm": target, "heading_rad": heading}


def world_point(frame, point):
    """Transform one already handed source point without deformation."""
    return [frame["origin_mm"][axis] + point[0] * frame["x_axis"][axis]
            + point[1] * frame["y_axis"][axis] for axis in (0, 1)]
