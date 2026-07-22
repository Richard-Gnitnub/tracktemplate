"""FreeCAD-independent transition/easement calculations."""

import math


GEOMETRY_TOLERANCE = 1.0e-8

__all__ = (
    "clothoid_entry_displacement",
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
