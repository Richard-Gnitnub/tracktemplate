"""FreeCAD-independent internal turnout calculations for the inherited host."""

import math


TURNOUT_SIZE_C10 = "REA C10 natural"
TURNOUT_DEFAULT_GAUGE = 16.5
TURNOUT_DEFAULT_FLANGEWAY = 1.0
TURNOUT_DEFAULT_SCALE = 76.2
TURNOUT_MIN_GAUGE = 10.0
TURNOUT_MAX_GAUGE = 25.0
TURNOUT_MIN_FLANGEWAY = 0.25
TURNOUT_MAX_FLANGEWAY = 3.0

TURNOUT_ORIENTATION_TRAILING = "Trailing against host travel direction"

__all__ = ()


def _turnout_orientation_sign(orientation):
    return -1.0 if str(orientation) == TURNOUT_ORIENTATION_TRAILING else 1.0


def turnout_valid_toe_range(host_length, dimensions, orientation):
    """Return the inherited valid toe interval without normalising its inputs."""
    total = max(0.0, float(host_length))
    start_x = float(dimensions["module_start_x"])
    finish_x = float(dimensions["module_end_x"])
    if _turnout_orientation_sign(orientation) > 0.0:
        minimum = max(0.0, -start_x)
        maximum = min(total, total - finish_x)
    else:
        minimum = max(0.0, finish_x)
        maximum = min(total, total + start_x)
    return minimum, maximum


def turnout_host_station_interval(toe_chainage, dimensions, orientation):
    """Return the complete turnout module's occupied host interval in mm."""
    direction = _turnout_orientation_sign(orientation)
    station_a = float(toe_chainage) + direction * float(
        dimensions["module_start_x"]
    )
    station_b = float(toe_chainage) + direction * float(
        dimensions["module_end_x"]
    )
    return min(station_a, station_b), max(station_a, station_b)


def rea_c10_dimensions(
    track_gauge=TURNOUT_DEFAULT_GAUGE,
    flangeway=TURNOUT_DEFAULT_FLANGEWAY,
    model_scale=TURNOUT_DEFAULT_SCALE,
):
    """Calculate the source-driven straight REA C10 canonical geometry."""
    gauge = float(track_gauge)
    flange = float(flangeway)
    scale_ratio = float(model_scale)
    if not TURNOUT_MIN_GAUGE <= gauge <= TURNOUT_MAX_GAUGE:
        raise ValueError(
            "Track gauge must be between {:.1f} and {:.1f} mm.".format(
                TURNOUT_MIN_GAUGE, TURNOUT_MAX_GAUGE
            )
        )
    if not TURNOUT_MIN_FLANGEWAY <= flange <= TURNOUT_MAX_FLANGEWAY:
        raise ValueError(
            "Flangeway must be between {:.2f} and {:.2f} mm.".format(
                TURNOUT_MIN_FLANGEWAY, TURNOUT_MAX_FLANGEWAY
            )
        )
    if scale_ratio <= 0.0:
        raise ValueError("Model scale must be greater than zero.")

    inch = 25.4 / scale_ratio
    planing = 110.0 * inch
    heel_lead = 329.0 * inch
    switch_radius = 11520.0 * inch
    switch_front = 65.0 * inch
    switch_rail_length = 342.0 * inch
    stock_rail_length = 432.0 * inch
    k1 = math.atan(1.0 / 40.0)
    k3n = 10.0
    k3 = math.atan(1.0 / k3n)
    planing_x = planing * math.cos(k1)
    argument = ((heel_lead - planing_x) / switch_radius) + math.sin(k1)
    if abs(argument) > 1.0:
        raise ValueError(
            "The REA C switch data cannot be resolved at the selected scale."
        )
    k2 = math.asin(argument)
    heel_offset = (
        (planing_x / 40.0)
        + switch_radius * math.cos(k1)
        - switch_radius * math.cos(k2)
    )

    # Templot regular-crossing minimum entry straight: 2 flangeways at N times.
    entry_straight = 2.0 * flange * k3n
    offset_at_curve_end = gauge - (entry_straight / k3n)
    denominator = math.cos(k2) - math.cos(k3)
    if abs(denominator) <= 1.0e-12:
        raise ValueError("The C10 turnout-radius calculation is singular.")
    turnout_radius = (offset_at_curve_end - heel_offset) / denominator
    if turnout_radius <= 0.0:
        raise ValueError(
            "The selected gauge and flangeway produce an invalid turnout radius."
        )
    turnout_curve_length = turnout_radius * (math.sin(k3) - math.sin(k2))
    switch_curve_end_x = heel_lead + turnout_curve_length
    fine_point_x = switch_curve_end_x + entry_straight
    turnout_origin_x = heel_lead - turnout_radius * math.sin(k2)
    turnout_origin_y = heel_offset + turnout_radius * math.cos(k2)

    # Templot5 REA/BH regular-crossing defaults. Values expressed in model mm.
    rail_head_width = 2.75 * inch
    blunt_nose_width = 0.75 * inch
    blunt_nose_x = fine_point_x + (0.5 * blunt_nose_width) / math.sin(0.5 * k3)
    blunt_nose_splice_x = blunt_nose_x - blunt_nose_width * math.sin(0.5 * k3)
    blunt_nose_outer_x = fine_point_x + rail_head_width / math.tan(0.5 * k3)
    a_timber_x = blunt_nose_x + 4.0 * inch

    flare_length = 36.0 * inch
    flare_end_gap = flange + 1.75 * inch
    flare_difference = max(0.0, flare_end_gap - flange)
    if flare_length <= flare_difference:
        raise ValueError(
            "The crossing flare length is too short for the requested flangeway end gap."
        )
    flare_angle = math.asin(flare_difference / flare_length)
    rail_bend_width = rail_head_width / math.cos(0.5 * flare_angle)

    wing_reach = 48.0 * inch
    wing_end_main_x = a_timber_x + wing_reach
    wing_flare_main_x = wing_end_main_x - flare_length
    wing_flare_main_outer_x = wing_flare_main_x - rail_head_width * math.tan(
        0.5 * flare_angle
    )
    wing_end_main_outer_x = wing_end_main_x - rail_head_width * math.sin(
        flare_angle
    )

    check_working_length = 108.0 * inch
    check_extension_length = 48.0 * inch
    check_total_length = check_working_length + check_extension_length
    check_main_end_x = a_timber_x + check_extension_length
    check_main_flare_out_x = check_main_end_x - flare_length
    check_main_start_x = check_main_end_x - check_total_length
    check_main_flare_in_x = check_main_start_x + flare_length
    check_main_outer_start_x = check_main_start_x + rail_head_width * math.sin(
        flare_angle
    )
    check_main_outer_flare_in_x = (
        check_main_flare_in_x + rail_head_width * math.tan(0.5 * flare_angle)
    )
    check_main_outer_flare_out_x = (
        check_main_flare_out_x - rail_head_width * math.tan(0.5 * flare_angle)
    )
    check_main_outer_end_x = check_main_end_x - rail_head_width * math.sin(
        flare_angle
    )

    # Virtual knuckles and the normal Templot knuckle radius.
    wing_turnout_x = fine_point_x - flange * k3n
    wing_turnout_outer_x = wing_turnout_x + rail_head_width * math.tan(
        0.5 * k3
    )
    wing_main_x = fine_point_x - flange / math.sin(k3)
    wing_main_outer_x = wing_main_x - rail_head_width * math.tan(0.5 * k3)
    scale_mm_per_foot = 304.8 / scale_ratio
    knuckle_radius = k3n * scale_mm_per_foot
    knuckle_tangent_x = abs(knuckle_radius * math.tan(0.5 * k3))
    knuckle_maximum_x = abs(fine_point_x - wing_turnout_x - inch)
    if knuckle_tangent_x > knuckle_maximum_x:
        knuckle_tangent_x = knuckle_maximum_x
        knuckle_radius = knuckle_tangent_x / math.tan(0.5 * k3)
    knuckle_crossing_x = knuckle_tangent_x * math.cos(k3)
    wing_bend_offset = knuckle_tangent_x * math.sin(k3)
    wing_turnout_plus_x = wing_turnout_x + knuckle_tangent_x
    wing_turnout_minus_x = wing_turnout_x - knuckle_crossing_x
    wing_turnout_outer_plus_x = wing_turnout_plus_x
    wing_turnout_outer_minus_x = (
        wing_turnout_minus_x + rail_head_width * math.sin(k3)
    )
    wing_main_plus_x = wing_main_x + knuckle_crossing_x
    wing_main_minus_x = wing_main_x - knuckle_tangent_x
    wing_main_outer_plus_x = wing_main_plus_x - rail_head_width * math.sin(k3)
    wing_main_outer_minus_x = wing_main_minus_x

    # Turnout-side wing rail, following the opposite running rail before its flare.
    wing_fine_point_x = fine_point_x - flange * math.sin(k3)
    wing_to_flare_length = (
        (a_timber_x - fine_point_x) + wing_reach - flare_length
    )
    wing_flare_turnout_base_x = fine_point_x + wing_to_flare_length * math.cos(
        k3
    )
    wing_flare_turnout_x = wing_fine_point_x + wing_to_flare_length * math.cos(
        k3
    )
    wing_flare_turnout_outer_x = (
        wing_flare_turnout_x
        - rail_bend_width * math.sin(k3 + 0.5 * flare_angle)
    )
    wing_end_turnout_x = wing_flare_turnout_x + flare_length * math.cos(
        k3 + flare_angle
    )
    wing_end_turnout_outer_x = wing_end_turnout_x - rail_head_width * math.sin(
        k3 + flare_angle
    )

    # Turnout-side check rail centred on the A timber, using the regular-crossing branch.
    check_turnout_fine_point_x = fine_point_x - (gauge - flange) * math.sin(k3)
    check_turnout_mid_offset = (
        a_timber_x - check_turnout_fine_point_x
    ) / math.cos(k3)
    check_turnout_length_after_fp = (
        check_turnout_mid_offset + check_extension_length - flare_length
    )
    check_turnout_length_before_fp = (
        check_total_length
        - check_turnout_length_after_fp
        - flare_length
        - flare_length
    )
    angled_entry_length = entry_straight / max(math.cos(k3), 1.0e-12)
    curved_stock_radius = turnout_radius - gauge
    check_turnout_radius = curved_stock_radius + flange
    check_turnout_flare_radius = curved_stock_radius + flare_end_gap
    if check_turnout_length_before_fp < angled_entry_length:
        check_turnout_working_mode = "straight crossing leg"
        check_turnout_flare_in_x = (
            check_turnout_fine_point_x
            - check_turnout_length_before_fp * math.cos(k3)
        )
        check_turnout_start_x = check_turnout_flare_in_x - (
            flare_length / math.cos(flare_angle)
        ) * math.cos(k3 + flare_angle)
    else:
        if check_turnout_radius <= 0.0 or check_turnout_flare_radius <= 0.0:
            raise ValueError(
                "The selected gauge and flangeway produce an invalid turnout-side check-rail radius."
            )
        check_curve_angle = (
            check_turnout_length_before_fp - angled_entry_length
        ) / check_turnout_radius
        check_flare_curve_angle = flare_length / check_turnout_radius
        if check_curve_angle < k3:
            check_turnout_flare_in_x = (
                turnout_origin_x
                + check_turnout_radius * math.sin(k3 - check_curve_angle)
            )
        else:
            check_turnout_flare_in_x = turnout_origin_x - (
                check_turnout_length_before_fp
                - angled_entry_length
                - check_turnout_radius * k3
            )
        if (check_curve_angle + check_flare_curve_angle) < k3:
            check_turnout_start_x = (
                turnout_origin_x
                + check_turnout_flare_radius
                * math.sin(k3 - check_curve_angle - check_flare_curve_angle)
            )
        else:
            check_turnout_start_x = check_turnout_flare_in_x - flare_length
        check_turnout_working_mode = "turnout curve and crossing leg"
    check_turnout_flare_out_x = (
        check_turnout_fine_point_x
        + check_turnout_length_after_fp * math.cos(k3)
    )
    check_turnout_end_x = check_turnout_flare_out_x + (
        flare_length / math.cos(flare_angle)
    ) * math.cos(k3 - flare_angle)

    # REA/BH vee-joint position used by the established module extent.
    vee_joint_length = (4.0 + 12.5 + (6.0 - 1.0) * 30.0) * inch
    vee_joint_x = blunt_nose_x + vee_joint_length
    exit_extension = 60.0 * inch
    module_start_x = -switch_front
    module_end_x = vee_joint_x + exit_extension

    switch_origin_x = heel_lead - switch_radius * math.sin(k2)
    switch_origin_y = heel_offset + switch_radius * math.cos(k2)
    turnout_origin_x = heel_lead - turnout_radius * math.sin(k2)
    turnout_origin_y = heel_offset + turnout_radius * math.cos(k2)

    return {
        "size": TURNOUT_SIZE_C10,
        "gauge": gauge,
        "flangeway": flange,
        "model_scale": scale_ratio,
        "inch": inch,
        "planing": planing,
        "planing_x": planing_x,
        "heel_lead": heel_lead,
        "heel_offset": heel_offset,
        "switch_radius": switch_radius,
        "switch_front": switch_front,
        "switch_rail_length": switch_rail_length,
        "stock_rail_length": stock_rail_length,
        "k1": k1,
        "k2": k2,
        "k3": k3,
        "crossing_n": k3n,
        "entry_straight": entry_straight,
        "curve_end_offset": offset_at_curve_end,
        "turnout_radius": turnout_radius,
        "turnout_curve_length": turnout_curve_length,
        "switch_curve_end_x": switch_curve_end_x,
        "fine_point_x": fine_point_x,
        "rail_head_width": rail_head_width,
        "blunt_nose_width": blunt_nose_width,
        "blunt_nose_x": blunt_nose_x,
        "blunt_nose_splice_x": blunt_nose_splice_x,
        "blunt_nose_outer_x": blunt_nose_outer_x,
        "a_timber_x": a_timber_x,
        "flare_length": flare_length,
        "flare_end_gap": flare_end_gap,
        "flare_angle": flare_angle,
        "rail_bend_width": rail_bend_width,
        "wing_reach": wing_reach,
        "wing_end_main_x": wing_end_main_x,
        "wing_flare_main_x": wing_flare_main_x,
        "wing_flare_main_outer_x": wing_flare_main_outer_x,
        "wing_end_main_outer_x": wing_end_main_outer_x,
        "check_working_length": check_working_length,
        "check_extension_length": check_extension_length,
        "check_total_length": check_total_length,
        "check_main_end_x": check_main_end_x,
        "check_main_flare_out_x": check_main_flare_out_x,
        "check_main_start_x": check_main_start_x,
        "check_main_flare_in_x": check_main_flare_in_x,
        "check_main_outer_start_x": check_main_outer_start_x,
        "check_main_outer_flare_in_x": check_main_outer_flare_in_x,
        "check_main_outer_flare_out_x": check_main_outer_flare_out_x,
        "check_main_outer_end_x": check_main_outer_end_x,
        "wing_turnout_x": wing_turnout_x,
        "wing_turnout_outer_x": wing_turnout_outer_x,
        "wing_main_x": wing_main_x,
        "wing_main_outer_x": wing_main_outer_x,
        "knuckle_radius": knuckle_radius,
        "wing_bend_offset": wing_bend_offset,
        "wing_turnout_plus_x": wing_turnout_plus_x,
        "wing_turnout_minus_x": wing_turnout_minus_x,
        "wing_turnout_outer_plus_x": wing_turnout_outer_plus_x,
        "wing_turnout_outer_minus_x": wing_turnout_outer_minus_x,
        "wing_main_plus_x": wing_main_plus_x,
        "wing_main_minus_x": wing_main_minus_x,
        "wing_main_outer_plus_x": wing_main_outer_plus_x,
        "wing_main_outer_minus_x": wing_main_outer_minus_x,
        "wing_fine_point_x": wing_fine_point_x,
        "wing_to_flare_length": wing_to_flare_length,
        "wing_flare_turnout_base_x": wing_flare_turnout_base_x,
        "wing_flare_turnout_x": wing_flare_turnout_x,
        "wing_flare_turnout_outer_x": wing_flare_turnout_outer_x,
        "wing_end_turnout_x": wing_end_turnout_x,
        "wing_end_turnout_outer_x": wing_end_turnout_outer_x,
        "check_turnout_fine_point_x": check_turnout_fine_point_x,
        "check_turnout_length_after_fp": check_turnout_length_after_fp,
        "check_turnout_length_before_fp": check_turnout_length_before_fp,
        "check_turnout_working_mode": check_turnout_working_mode,
        "curved_stock_radius": curved_stock_radius,
        "check_turnout_radius": check_turnout_radius,
        "check_turnout_flare_radius": check_turnout_flare_radius,
        "check_turnout_flare_in_x": check_turnout_flare_in_x,
        "check_turnout_start_x": check_turnout_start_x,
        "check_turnout_flare_out_x": check_turnout_flare_out_x,
        "check_turnout_end_x": check_turnout_end_x,
        "vee_joint_x": vee_joint_x,
        "module_start_x": module_start_x,
        "module_end_x": module_end_x,
        "switch_origin_x": switch_origin_x,
        "switch_origin_y": switch_origin_y,
        "turnout_origin_x": turnout_origin_x,
        "turnout_origin_y": turnout_origin_y,
    }
