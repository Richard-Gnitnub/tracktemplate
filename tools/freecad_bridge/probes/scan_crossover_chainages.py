"""Read-only scan for a valid default B14 crossover placement."""

import json
import math
import sys

module = sys.modules.get("tracktemplate_b14_session")
manager = getattr(module, "_automation_trackwork_manager", None) if module else None
if manager is None:
    raise RuntimeError("The automated B14 trackwork manager is not open")

panel = manager.crossover_panel
host_a, host_b, _chainage, arrangement, handing, gauge, flangeway, requested_radius = panel.proposed_values()
minimum = panel.chainage_box.minimum()
maximum = panel.chainage_box.maximum()
chainages = [minimum + (maximum - minimum) * index / 8.0 for index in range(9)]
results = []

for chainage in chainages:
    try:
        solved = module.solve_rea_c10_crossover_geometry(
            panel.doc,
            host_a,
            host_b,
            chainage,
            arrangement,
            handing,
            gauge,
            flangeway,
            requested_radius,
        )
        metrics_a = module.turnout_mapping_metrics(
            solved["host_a_data"],
            solved["toe_chainage_a"],
            solved["orientation_a"],
            solved["handing"],
            solved["dimensions"],
        )
        metrics_b = module.turnout_mapping_metrics(
            solved["host_b_data"],
            solved["toe_chainage_b"],
            solved["orientation_b"],
            solved["handing"],
            solved["dimensions"],
        )
        component_radii = [
            metrics_a["turnout_minimum_radius"],
            metrics_b["turnout_minimum_radius"],
            solved["connector"].get("minimum_radius"),
        ]
        finite_radii = [float(value) for value in component_radii if value is not None and math.isfinite(float(value))]
        results.append({
            "chainage_a": chainage,
            "chainage_b": solved["toe_chainage_b"],
            "accepted_preview": True,
            "handing": solved["handing"],
            "turnout_a_minimum_radius": metrics_a["turnout_minimum_radius"],
            "turnout_b_minimum_radius": metrics_b["turnout_minimum_radius"],
            "connector_minimum_radius": solved["connector"].get("minimum_radius"),
            "complete_minimum_radius": min(finite_radii) if finite_radii else None,
            "meets_requested_radius": bool(finite_radii and min(finite_radii) >= requested_radius - 1.0e-7),
        })
    except Exception as error:
        results.append({
            "chainage_a": chainage,
            "accepted_preview": False,
            "error": "{}: {}".format(type(error).__name__, error),
        })

print(json.dumps({
    "requested_radius": requested_radius,
    "chainage_range": [minimum, maximum],
    "results": results,
}, sort_keys=True))
