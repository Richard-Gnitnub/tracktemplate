"""FreeCAD-independent transition/easement calculations."""

import math


GEOMETRY_TOLERANCE = 1.0e-8

__all__ = (
    "clothoid_entry_displacement",
    "clothoid_entry_displacement_at_station",
    "clothoid_entry_polyline_stations",
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
