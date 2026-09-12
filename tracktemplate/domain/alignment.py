"""FreeCAD-independent transition/easement calculations."""

import bisect
import math
from dataclasses import dataclass


GEOMETRY_TOLERANCE = 1.0e-8
_CORE_SAMPLE_SPACING = 3.0

__all__ = (
    "AlignmentStationInterpolation",
    "alignment_station_data",
    "interpolate_alignment_station",
    "add_common_straight_extensions",
    "build_concentric_core",
    "build_straight_route",
    "clothoid_entry_displacement",
    "clothoid_exit_displacement",
    "clothoid_entry_displacement_at_station",
    "clothoid_entry_polyline_stations",
    "main_circle_centre",
    "mirror_alignment_for_turn",
    "transition_start_signed_offset",
    "solve_transition_length",
)


def clothoid_entry_displacement(length, radius, integration_steps=240):
    """Return accurate local x/y displacement and angle for an Euler entry."""
    if radius <= 0.0:
        raise ValueError("A clothoid radius must be greater than zero.")
    if length <= GEOMETRY_TOLERANCE:
        return 0.0, 0.0, 0.0

    # Simpson integration of theta(u) = alpha*u^2 over u in [0, 1].
    steps = max(40, int(integration_steps))
    if steps % 2:
        steps += 1
    alpha = length / (2.0 * radius)
    interval = 1.0 / float(steps)
    cosine_sum = 0.0
    sine_sum = 0.0

    for index in range(steps + 1):
        u = index * interval
        theta = alpha * u * u
        weight = 1.0
        if index not in (0, steps):
            weight = 4.0 if index % 2 else 2.0
        cosine_sum += weight * math.cos(theta)
        sine_sum += weight * math.sin(theta)

    scale = length * interval / 3.0
    return scale * cosine_sum, scale * sine_sum, alpha


def clothoid_exit_displacement(length, radius, integration_steps=240):
    """Return local XY millimetres and radians for a left-turn Euler exit.

    Preserve the inherited Simpson integration and radius diagnostic.
    The result is an uncached three-float tuple with no host side effects.
    """
    if radius <= 0.0:
        raise ValueError("A clothoid radius must be greater than zero.")
    if length <= GEOMETRY_TOLERANCE:
        return 0.0, 0.0, 0.0

    steps = max(40, int(integration_steps))
    if steps % 2:
        steps += 1
    alpha = length / (2.0 * radius)
    interval = 1.0 / float(steps)
    cosine_sum = 0.0
    sine_sum = 0.0

    for index in range(steps + 1):
        u = index * interval
        theta = (2.0 * alpha * u) - (alpha * u * u)
        weight = 1.0
        if index not in (0, steps):
            weight = 4.0 if index % 2 else 2.0
        cosine_sum += weight * math.cos(theta)
        sine_sum += weight * math.sin(theta)

    scale = length * interval / 3.0
    return scale * cosine_sum, scale * sine_sum, alpha


def _left_normal(heading):
    return (-math.sin(heading), math.cos(heading))


def main_circle_centre(main_transition, main_radius):
    """Return the main circle's XY centre in local left-turn millimetres.

    Preserve the inherited endpoint calculation and radius diagnostic.
    The result is an uncached two-float tuple with no host side effects.
    """
    x_end, y_end, entry_angle = clothoid_entry_displacement(
        main_transition,
        main_radius,
    )
    normal_x, normal_y = _left_normal(entry_angle)
    return (
        x_end + (main_radius * normal_x),
        y_end + (main_radius * normal_y),
    )


def _finite_geometry_value(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a finite number".format(name))
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("{} must be a finite number".format(name)) from error
    if not math.isfinite(result):
        raise ValueError("{} must be a finite number".format(name))
    return result


def _integrate_clothoid_station(station, end_angle, integration_steps):
    """Integrate a clothoid from zero to one fixed-transition station."""
    steps = max(40, int(integration_steps))
    if steps % 2:
        steps += 1
    interval = 1.0 / float(steps)
    cosine_sum = 0.0
    sine_sum = 0.0

    for index in range(steps + 1):
        u = index * interval
        theta = end_angle * u * u
        weight = 1.0
        if index not in (0, steps):
            weight = 4.0 if index % 2 else 2.0
        cosine_sum += weight * math.cos(theta)
        sine_sum += weight * math.sin(theta)

    scale = station * interval / 3.0
    return scale * cosine_sum, scale * sine_sum, end_angle


def clothoid_entry_displacement_at_station(
    station,
    transition_length,
    radius,
    integration_steps=240,
):
    """Return displacement and tangent at a station on a fixed Euler entry.

    Lengths are millimetres in canonical local left-turn space. Curvature
    increases linearly over the complete ``transition_length``, so the tangent
    angle at ``station`` is ``station**2 / (2 * radius * transition_length)``.
    """
    station = _finite_geometry_value("station", station)
    transition_length = _finite_geometry_value(
        "transition_length",
        transition_length,
    )
    radius = _finite_geometry_value("radius", radius)

    if radius <= 0.0:
        raise ValueError("A clothoid radius must be greater than zero.")
    if transition_length < 0.0:
        raise ValueError("A clothoid transition length must not be negative.")
    if station < 0.0 or station > transition_length:
        raise ValueError(
            "A clothoid station must lie within the transition length."
        )
    if transition_length <= GEOMETRY_TOLERANCE:
        return 0.0, 0.0, 0.0
    if station == 0.0:
        return 0.0, 0.0, 0.0
    if station == transition_length:
        # Retain the mechanically extracted B14/B15 endpoint calculation.
        return clothoid_entry_displacement(
            transition_length,
            radius,
            integration_steps,
        )

    end_angle = (
        station * station / (2.0 * radius * transition_length)
    )
    return _integrate_clothoid_station(
        station,
        end_angle,
        integration_steps,
    )


def clothoid_entry_polyline_stations(
    transition_length_mm,
    radius_mm,
    maximum_chord_error_mm,
    maximum_segment_count,
):
    """Return stations for a chord-bounded Euler centreline polyline.

    Stations are millimetres in canonical local left-turn space and include
    both endpoints.  For an arc-length interval ``h`` on this Euler entry,
    ``|r''(s)|`` is bounded by ``1 / radius_mm``.  Linear interpolation is
    therefore bounded by ``h**2 / (8 * radius_mm)``.  The second return value
    is that conservative bound for the equal station intervals selected here.
    """
    transition_length_mm = _finite_geometry_value(
        "transition_length_mm",
        transition_length_mm,
    )
    radius_mm = _finite_geometry_value("radius_mm", radius_mm)
    maximum_chord_error_mm = _finite_geometry_value(
        "maximum_chord_error_mm",
        maximum_chord_error_mm,
    )
    if transition_length_mm < 0.0:
        raise ValueError("A clothoid transition length must not be negative.")
    if radius_mm <= 0.0:
        raise ValueError("A clothoid radius must be greater than zero.")
    if maximum_chord_error_mm <= 0.0:
        raise ValueError("Maximum chord error must be greater than zero.")
    if (
        isinstance(maximum_segment_count, bool)
        or not isinstance(maximum_segment_count, int)
        or maximum_segment_count < 1
    ):
        raise ValueError("Maximum segment count must be a positive integer.")

    if transition_length_mm == 0.0:
        return (0.0,), 0.0
    if transition_length_mm <= GEOMETRY_TOLERANCE:
        raise ValueError(
            "A non-zero clothoid length is below the geometry tolerance."
        )

    chord_scale = 8.0 * radius_mm * maximum_chord_error_mm
    maximum_station_interval_mm = (
        math.sqrt(chord_scale)
        if math.isfinite(chord_scale)
        else math.inf
    )
    if maximum_station_interval_mm <= 0.0:
        raise ValueError(
            "The requested chord error is below the supported numerical range."
        )

    required_ratio = transition_length_mm / maximum_station_interval_mm
    if (
        not math.isfinite(required_ratio)
        or required_ratio > maximum_segment_count
    ):
        raise ValueError(
            "The requested chord error requires more than {} segments.".format(
                maximum_segment_count
            )
        )
    segment_count = max(1, int(math.ceil(required_ratio)))
    station_interval_mm = transition_length_mm / float(segment_count)
    chord_error_bound_mm = (
        (station_interval_mm / radius_mm)
        * station_interval_mm
        / 8.0
    )
    if (
        not math.isfinite(chord_error_bound_mm)
        or chord_error_bound_mm > maximum_chord_error_mm
    ):
        if segment_count >= maximum_segment_count:
            raise ValueError(
                "The requested chord error requires more than {} segments.".format(
                    maximum_segment_count
                )
            )
        segment_count += 1
        station_interval_mm = transition_length_mm / float(segment_count)
        chord_error_bound_mm = (
            (station_interval_mm / radius_mm)
            * station_interval_mm
            / 8.0
        )

    stations = tuple(
        transition_length_mm
        if index == segment_count
        else transition_length_mm * (float(index) / float(segment_count))
        for index in range(segment_count + 1)
    )
    return stations, chord_error_bound_mm


def transition_start_signed_offset(circle_centre_y, radius, transition_length):
    """Signed offset of an entry/exit tangent line in canonical left-turn space."""
    _x_end, y_end, angle = clothoid_entry_displacement(
        transition_length,
        radius,
    )
    return circle_centre_y - y_end - (radius * math.cos(angle))


def solve_transition_length(
    circle_centre_y,
    radius,
    target_signed_offset,
    total_angle,
    track_name,
    end_name,
):
    """Solve a monotonic Euler transition length for a requested tangent offset."""
    if radius <= 0.0:
        raise ValueError("The radius for '{}' must be greater than zero.".format(track_name))

    maximum_length = max(0.0, (2.0 * radius * total_angle) - 1.0e-6)
    offset_at_zero = transition_start_signed_offset(circle_centre_y, radius, 0.0)
    offset_at_maximum = transition_start_signed_offset(
        circle_centre_y,
        radius,
        maximum_length,
    )

    upper_offset = max(offset_at_zero, offset_at_maximum)
    lower_offset = min(offset_at_zero, offset_at_maximum)
    if target_signed_offset < lower_offset - 1.0e-6 or target_signed_offset > upper_offset + 1.0e-6:
        raise ValueError(
            "{} spacing for '{}' cannot be produced by a single same-direction "
            "Euler easement with the selected curve radius and turn angle.\n\n"
            "Requested signed offset: {:+.3f} mm\n"
            "Achievable signed range: {:+.3f} to {:+.3f} mm\n\n"
            "Change the straight spacing, curve spacing, main radius or total "
            "turn angle.".format(
                end_name,
                track_name,
                target_signed_offset,
                lower_offset,
                upper_offset,
            )
        )

    if abs(target_signed_offset - offset_at_zero) <= 1.0e-8:
        return 0.0
    if abs(target_signed_offset - offset_at_maximum) <= 1.0e-8:
        return maximum_length

    low = 0.0
    high = maximum_length
    value_low = offset_at_zero - target_signed_offset
    value_high = offset_at_maximum - target_signed_offset

    if value_low * value_high > 0.0:
        raise ValueError(
            "Could not bracket the {} easement solution for '{}'.".format(
                end_name.lower(),
                track_name,
            )
        )

    for _iteration in range(72):
        midpoint = 0.5 * (low + high)
        value_midpoint = (
            transition_start_signed_offset(circle_centre_y, radius, midpoint)
            - target_signed_offset
        )
        if abs(value_midpoint) <= 1.0e-10 or (high - low) <= 1.0e-7:
            return midpoint

        if value_low * value_midpoint <= 0.0:
            high = midpoint
            value_high = value_midpoint
        else:
            low = midpoint
            value_low = value_midpoint

    return 0.5 * (low + high)


def _rotate_xy(x, y, angle):
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return (
        (x * cosine) - (y * sine),
        (x * sine) + (y * cosine),
    )


def _integrate_core_segment(
    points,
    headings,
    x,
    y,
    heading,
    length,
    curvature_function,
):
    if length <= GEOMETRY_TOLERANCE:
        return x, y, heading

    steps = max(1, int(math.ceil(length / _CORE_SAMPLE_SPACING)))
    distance_step = length / float(steps)

    for index in range(steps):
        local_midpoint = (index + 0.5) * distance_step
        curvature = curvature_function(local_midpoint)
        new_heading = heading + (curvature * distance_step)

        if abs(curvature) < 1.0e-14:
            x += distance_step * math.cos(heading)
            y += distance_step * math.sin(heading)
        else:
            x += (math.sin(new_heading) - math.sin(heading)) / curvature
            y += (-math.cos(new_heading) + math.cos(heading)) / curvature

        heading = new_heading
        points.append((float(x), float(y)))
        headings.append(heading)

    return x, y, heading


def build_concentric_core(
    circle_centre,
    radius,
    entry_transition,
    exit_transition,
    total_angle,
    label,
):
    """Return an ordered Euler-circle-Euler mapping with neutral XY points.

    Lengths are millimetres; headings are radians in local left-turn space.
    Keep inherited diagnostics, fixed 3 mm sampling and endpoint snaps.
    This calculation constructs no host objects and has no side effects.
    """
    if radius <= 0.0:
        raise ValueError(
            "The constant radius for '{}' must be greater than zero.".format(
                label,
            )
        )
    if entry_transition < 0.0 or exit_transition < 0.0:
        raise ValueError(
            "Easement lengths for '{}' cannot be negative.".format(label)
        )

    entry_angle = entry_transition / (2.0 * radius)
    exit_angle = exit_transition / (2.0 * radius)
    circular_angle = total_angle - entry_angle - exit_angle
    if circular_angle < -1.0e-9:
        raise ValueError(
            "The independent easements for '{}' consume more angle than the "
            "complete curve.\n\nEntry easement: {:.3f} mm\nExit easement: "
            "{:.3f} mm\nMaximum combined length: {:.3f} mm".format(
                label,
                entry_transition,
                exit_transition,
                2.0 * radius * total_angle,
            )
        )
    circular_angle = max(0.0, circular_angle)

    centre_x, centre_y = circle_centre
    entry_x, entry_y, _entry_angle_check = clothoid_entry_displacement(
        entry_transition,
        radius,
    )

    entry_normal_x, entry_normal_y = _left_normal(entry_angle)
    circle_start_x = centre_x - (radius * entry_normal_x)
    circle_start_y = centre_y - (radius * entry_normal_y)
    start_x = circle_start_x - entry_x
    start_y = circle_start_y - entry_y

    points = [(float(start_x), float(start_y))]
    headings = [0.0]
    x = start_x
    y = start_y
    heading = 0.0

    if entry_transition > GEOMETRY_TOLERANCE:
        x, y, heading = _integrate_core_segment(
            points,
            headings,
            x,
            y,
            heading,
            entry_transition,
            lambda station: station / (radius * entry_transition),
        )

    # Snap to the exact circle start after accumulated sampling error.
    x = circle_start_x
    y = circle_start_y
    heading = entry_angle
    points[-1] = (float(x), float(y))
    headings[-1] = heading

    circular_length = radius * circular_angle
    if circular_length > GEOMETRY_TOLERANCE:
        x, y, heading = _integrate_core_segment(
            points,
            headings,
            x,
            y,
            heading,
            circular_length,
            lambda _station: 1.0 / radius,
        )

    circle_end_heading = total_angle - exit_angle
    exit_normal_x, exit_normal_y = _left_normal(circle_end_heading)
    circle_end_x = centre_x - (radius * exit_normal_x)
    circle_end_y = centre_y - (radius * exit_normal_y)
    x = circle_end_x
    y = circle_end_y
    heading = circle_end_heading
    points[-1] = (float(x), float(y))
    headings[-1] = heading

    if exit_transition > GEOMETRY_TOLERANCE:
        x, y, heading = _integrate_core_segment(
            points,
            headings,
            x,
            y,
            heading,
            exit_transition,
            lambda station: (1.0 - (station / exit_transition)) / radius,
        )

        # Snap the endpoint to the independent Simpson-integrated value.
        exit_dx, exit_dy, _exit_angle_check = clothoid_exit_displacement(
            exit_transition,
            radius,
        )
        rotated_dx, rotated_dy = _rotate_xy(
            exit_dx,
            exit_dy,
            circle_end_heading,
        )
        x = circle_end_x + rotated_dx
        y = circle_end_y + rotated_dy
        points[-1] = (float(x), float(y))

    heading = total_angle
    headings[-1] = heading

    return {
        "label": label,
        "points": points,
        "headings": headings,
        "start": (start_x, start_y),
        "end": (x, y),
        "radius": radius,
        "entry_transition": entry_transition,
        "exit_transition": exit_transition,
        "entry_angle": entry_angle,
        "exit_angle": exit_angle,
        "circular_angle": circular_angle,
        "circular_length": circular_length,
        "core_length": entry_transition + circular_length + exit_transition,
    }


def add_common_straight_extensions(alignments, total_angle):
    """Return common straight-end metadata and optional new XY points.

    Inputs contain only start, end and core_length in local millimetres.
    The angle is in radians. Keep input records unchanged and preserve
    the inherited arithmetic and strict geometry-tolerance threshold.
    """
    if not alignments:
        return []

    common_start_x = min(item["start"][0] for item in alignments)
    tangent_x = math.cos(total_angle)
    tangent_y = math.sin(total_angle)
    common_end_projection = max(
        (item["end"][0] * tangent_x) + (item["end"][1] * tangent_y)
        for item in alignments
    )
    results = []
    for item in alignments:
        start_x, start_y = item["start"]
        entry_extension = max(0.0, start_x - common_start_x)
        entry_point = None
        if entry_extension > GEOMETRY_TOLERANCE:
            entry_point = (common_start_x, start_y)

        end_x, end_y = item["end"]
        current_projection = (end_x * tangent_x) + (end_y * tangent_y)
        exit_extension = max(0.0, common_end_projection - current_projection)
        exit_point = None
        if exit_extension > GEOMETRY_TOLERANCE:
            end_x += exit_extension * tangent_x
            end_y += exit_extension * tangent_y
            exit_point = (end_x, end_y)

        results.append({
            "entry_extension": entry_extension,
            "exit_extension": exit_extension,
            "total_length": (
                item["core_length"] + entry_extension + exit_extension
            ),
            "extended_start": (common_start_x, start_y),
            "extended_end": (end_x, end_y),
            "entry_point": entry_point,
            "exit_point": exit_point,
        })
    return results


_STRAIGHT_CONNECTION_INDEPENDENT = "Independent datum"
_STRAIGHT_CONNECTION_CURVE_ENTRANCE = "Curve entrance"
_STRAIGHT_DIRECTION_REVERSE = "Reverse"
_STRAIGHT_PARALLEL_RIGHT = "Right of travel"


def _straight_point(x, y):
    return float(x), float(y)


def _straight_heading_delta(first, second):
    return abs(math.atan2(math.sin(first - second), math.cos(first - second)))


def _straight_alignment_record(
    route_id,
    route_name,
    track_number,
    name,
    points,
    heading,
    width,
    thickness,
    create_template,
    show_centreline,
    connection_mode,
    source_alignment_name="",
):
    total_length = 0.0 + math.hypot(
        points[1][0] - points[0][0], points[1][1] - points[0][1],
    )
    if total_length <= GEOMETRY_TOLERANCE:
        raise ValueError("A straight track length must be greater than zero.")
    return {
        "route_id": route_id,
        "route_name": route_name,
        "track_number": int(track_number),
        "name": name,
        "points": points,
        "headings": [heading for _point in points],
        "width": float(width),
        "template_thickness": float(thickness),
        "create_template": bool(create_template),
        "show_centreline": bool(show_centreline),
        "connection_mode": connection_mode,
        "source_alignment_name": source_alignment_name,
        "total_length": total_length,
        "core_length": total_length,
        "entry_extension": 0.0,
        "exit_extension": 0.0,
        "start": (points[0][0], points[0][1]),
        "end": (points[-1][0], points[-1][1]),
        "extended_start": (points[0][0], points[0][1]),
        "extended_end": (points[-1][0], points[-1][1]),
    }


def build_straight_route(config, curve_alignments, connected_template_thickness):
    """Build ordered straight-route records from normalized neutral inputs.

    Coordinates and lengths are millimetres, headings are radians, and the
    normalized config remains the caller's object. No input is mutated.
    Curve records supply endpoint coordinates, headings and original counts.
    """
    if not config["enabled"]:
        return None
    if config["length"] <= GEOMETRY_TOLERANCE:
        raise ValueError(
            "Straight route '{}' must have a length greater than zero.".format(
                config["name"]
            )
        )
    if not config["create_template"] and not config["show_centreline"]:
        raise ValueError(
            "Straight route '{}' must create a strip, a centreline, "
            "or both.".format(
                config["name"]
            )
        )

    route_id = "straight-{}".format(config["manager_id"])
    route_name = config["name"]
    connection_mode = config["connection_mode"]
    alignments = []

    if connection_mode == _STRAIGHT_CONNECTION_INDEPENDENT:
        heading = math.radians(config["rotation_degrees"])
        if config["direction"] == _STRAIGHT_DIRECTION_REVERSE:
            heading += math.pi
        tangent_x = math.cos(heading)
        tangent_y = math.sin(heading)
        normal_x, normal_y = _left_normal(heading)
        side_factor = (
            -1.0
            if config["parallel_side"] == _STRAIGHT_PARALLEL_RIGHT
            else 1.0
        )
        for track_index in range(config["track_count"]):
            offset = side_factor * track_index * config["track_spacing"]
            start_x = config["start_x"] + (offset * normal_x)
            start_y = config["start_y"] + (offset * normal_y)
            finish_x = start_x + (config["length"] * tangent_x)
            finish_y = start_y + (config["length"] * tangent_y)
            points = [
                _straight_point(start_x, start_y),
                _straight_point(finish_x, finish_y),
            ]
            track_name = (
                route_name
                if config["track_count"] == 1
                else "{} - Track {}".format(route_name, track_index + 1)
            )
            alignments.append(
                _straight_alignment_record(
                    route_id,
                    route_name,
                    track_index + 1,
                    track_name,
                    points,
                    heading,
                    config["template_width"],
                    config["template_thickness"],
                    config["create_template"],
                    config["show_centreline"],
                    connection_mode,
                )
            )
    else:
        if not curve_alignments:
            raise ValueError(
                "Straight route '{}' cannot connect because no curve "
                "tracks exist.".format(
                    route_name
                )
            )
        reference_heading = None
        for track_index, source_alignment in enumerate(curve_alignments):
            if (
                source_alignment["point_count"] < 2
                or source_alignment["point_count"]
                != source_alignment["heading_count"]
            ):
                raise ValueError(
                    "Straight route '{}' cannot connect to incomplete curve "
                    "track '{}'.".format(
                        route_name,
                        source_alignment.get("name", track_index + 1),
                    )
                )
            if connection_mode == _STRAIGHT_CONNECTION_CURVE_ENTRANCE:
                join_point = source_alignment["start"]
                heading = source_alignment["start_heading"]
                remote_point = _straight_point(
                    join_point[0] - (config["length"] * math.cos(heading)),
                    join_point[1] - (config["length"] * math.sin(heading)),
                )
                points = [
                    remote_point, _straight_point(join_point[0], join_point[1]),
                ]
                joined_point = points[-1]
            else:
                join_point = source_alignment["end"]
                heading = source_alignment["end_heading"]
                remote_point = _straight_point(
                    join_point[0] + (config["length"] * math.cos(heading)),
                    join_point[1] + (config["length"] * math.sin(heading)),
                )
                points = [
                    _straight_point(join_point[0], join_point[1]), remote_point,
                ]
                joined_point = points[0]

            if reference_heading is None:
                reference_heading = heading
            elif _straight_heading_delta(heading, reference_heading) > 1.0e-10:
                raise ValueError(
                    "Straight route '{}' cannot connect because the selected "
                    "curve tracks do not share one tangent direction.".format(
                        route_name
                    )
                )

            join_error = math.hypot(
                joined_point[0] - join_point[0],
                joined_point[1] - join_point[1],
            )
            source_heading = (
                source_alignment["start_heading"]
                if connection_mode == _STRAIGHT_CONNECTION_CURVE_ENTRANCE
                else source_alignment["end_heading"]
            )
            if join_error > 1.0e-7 or _straight_heading_delta(
                heading, source_heading
            ) > 1.0e-10:
                raise ValueError(
                    "Internal straight connection check failed for '{}' and "
                    "'{}'.".format(
                        route_name,
                        source_alignment.get("name", track_index + 1),
                    )
                )

            source_name = str(
                source_alignment.get("name", "Track {}".format(track_index + 1))
            )
            alignments.append(
                _straight_alignment_record(
                    route_id,
                    route_name,
                    track_index + 1,
                    "{} - {}".format(route_name, source_name),
                    points,
                    heading,
                    source_alignment["width"],
                    connected_template_thickness,
                    config["create_template"]
                    and source_alignment.get("create_template", True),
                    config["show_centreline"]
                    and source_alignment.get("show_centreline", True),
                    connection_mode,
                    source_name,
                )
            )

    if not alignments:
        raise ValueError(
            "Straight route '{}' did not produce any track alignments.".format(
                route_name
            )
        )
    return {
        "route_id": route_id,
        "name": route_name,
        "connection_mode": connection_mode,
        "config": config,
        "alignments": alignments,
        "length": config["length"],
    }


@dataclass(frozen=True)
class AlignmentStationInterpolation:
    """Hold neutral XY and defer heading arithmetic for host allocation order."""

    point: tuple
    heading_a: float
    heading_b: float
    fraction: float

    @property
    def heading(self):
        """Return the inherited linear, unwrapped heading in radians."""
        return self.heading_a + (
            (self.heading_b - self.heading_a) * self.fraction
        )


def alignment_station_data(alignment):
    """Index ordered neutral XY pairs and preserve shallow input aliases.

    Coordinates, stations and extensions use millimetres; headings use
    radians. Preserve incomplete-input errors and duplicate stations.
    """
    points = list(alignment.get("points", []))
    headings = list(alignment.get("headings", []))
    if len(points) < 2 or len(points) != len(headings):
        raise ValueError("A selected track alignment is incomplete.")

    stations = [0.0]
    for point_a, point_b in zip(points[:-1], points[1:]):
        stations.append(
            stations[-1] + math.hypot(
                point_b[0] - point_a[0], point_b[1] - point_a[1],
            )
        )
    total = stations[-1]
    entry_extension = min(max(0.0, alignment.get("entry_extension", 0.0)), total)
    exit_extension = min(max(0.0, alignment.get("exit_extension", 0.0)), total)
    core_start = entry_extension
    core_end = max(core_start, total - exit_extension)
    return {
        "alignment": alignment,
        "points": points,
        "headings": headings,
        "stations": stations,
        "total": total,
        "core_start": core_start,
        "core_end": core_end,
    }


def interpolate_alignment_station(data, station):
    """Return staged neutral XY and heading for one travel-order station.

    Clamp station millimetres with inherited right bias and span tolerance.
    Read the result's heading after host point allocation when adapting.
    """
    station = min(max(float(station), 0.0), data["total"])
    stations = data["stations"]
    index = bisect.bisect_right(stations, station) - 1
    index = max(0, min(index, len(stations) - 2))
    start_station = stations[index]
    finish_station = stations[index + 1]
    span = finish_station - start_station
    fraction = (
        0.0 if span <= GEOMETRY_TOLERANCE
        else (station - start_station) / span
    )
    point_a = data["points"][index]
    point_b = data["points"][index + 1]
    heading_a = data["headings"][index]
    heading_b = data["headings"][index + 1]
    return AlignmentStationInterpolation(
        (
            point_a[0] + ((point_b[0] - point_a[0]) * fraction),
            point_a[1] + ((point_b[1] - point_a[1]) * fraction),
        ),
        heading_a,
        heading_b,
        fraction,
    )


def mirror_alignment_for_turn(alignment, turn_sign):
    """Yield ordered neutral reflection updates without changing the input.

    Consume and apply each stage before advancing this one-shot iterator.
    XY uses millimetres and headings use radians. Positive signs yield
    nothing without reading the mapping; other signs preserve inherited
    arithmetic and errors. Point pairs are lazy to retain allocation order.
    """
    if turn_sign > 0.0:
        return
    yield "points", (
        (point[0], -point[1]) for point in alignment["points"]
    )
    yield "headings", [-heading for heading in alignment["headings"]]
    for key in ("start", "end", "extended_start", "extended_end"):
        if key in alignment:
            x, y = alignment[key]
            yield key, (x, -y)
