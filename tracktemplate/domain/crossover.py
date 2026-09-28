"""FreeCAD-independent complete-radius decision for a managed crossover."""

import math


_COMPONENTS = (
    ("Host Track A turnout road", "turnout_a_minimum_radius_mm"),
    ("Host Track B turnout road", "turnout_b_minimum_radius_mm"),
    ("Connecting road", "connector_minimum_radius_mm"),
)


def complete_radius_decision(
    turnout_a_radius_mm,
    turnout_b_radius_mm,
    connector_radius_mm,
    requested_radius_mm,
):
    """Decide the sampled complete-radius rule in mm; ``None`` is straight."""
    requested = float(requested_radius_mm)
    if not math.isfinite(requested) or requested <= 0.0:
        raise ValueError("Minimum resulting radius must be finite and positive.")

    values = (
        turnout_a_radius_mm,
        turnout_b_radius_mm,
        connector_radius_mm,
    )
    result = {}
    limiting = None
    complete = None
    for (label, key), value in zip(_COMPONENTS, values):
        if value is None:
            result[key] = None
            continue
        radius = float(value)
        if not math.isfinite(radius) or radius <= 0.0:
            raise ValueError("{} has no valid sampled radius.".format(label))
        result[key] = radius
        if complete is None or radius < complete:
            complete = radius
            limiting = label

    accepted = complete is None or complete >= requested
    if accepted:
        diagnostic = (
            "Complete crossover minimum radius is straight."
            if complete is None else
            "Complete crossover minimum radius {:.6f} mm satisfies the "
            "configured {:.6f} mm (limited by {}).".format(
                complete, requested, limiting,
            )
        )
    else:
        diagnostic = (
            "{} minimum radius {:.6f} mm is below the configured "
            "{:.6f} mm for the complete crossover."
        ).format(limiting, complete, requested)
    result.update({
        "complete_minimum_radius_mm": complete,
        "limiting_component": limiting,
        "minimum_requested_radius_mm": requested,
        "accepted": accepted,
        "diagnostic": diagnostic,
    })
    return result
