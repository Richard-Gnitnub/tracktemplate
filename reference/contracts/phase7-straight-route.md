# API to build straight tracks

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-straight-route.json) keeps the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Inputs and results

`tracktemplate.api.build_straight_route(config, curve_alignments, connected_template_thickness)`
uses the function in `tracktemplate.domain.alignment`.
It calculates independent parallel straight tracks or straight tracks that connect to the entrance or exit of a curve.
Lengths and XY coordinates use millimetres. Headings use radians.
The independent input `rotation_degrees` uses degrees.
Track sequence, travel direction and the inherited XY frame stay unchanged.

`config` is the Python `dict` from the host's unchanged `clone_straight_config` function.
The API changes no input and supplies no defaults or UUID values.
The required `connected_template_thickness` argument is the host's actual `TEMPLATE_THICKNESS` value.
The current value is `1.0` mm.

Each Python `dict` in `curve_alignments` supplies these six named items:

```text
point_count
heading_count
start
end
start_heading
end_heading
```

The endpoint values are XY pairs. Unavailable endpoint or heading values use `None`.
The original counts let the API reject incomplete curve data before it uses the endpoint values.
The named items `name`, `width`, `create_template` and `show_centreline` keep their original presence and values.
The API uses the inherited defaults for an absent name or display flag.
Each complete connected curve record must supply `width`.
No FreeCAD value or interior curve point crosses this API.

The result keeps the six named route items and twenty named alignment items in their original sequence.
Each new alignment contains two new XY pairs in `points`.
The result's `config` value is the exact Python `dict` supplied to the API.
The function keeps the inherited names, identities, flags, widths, thickness and source metadata.
It returns `None` for a disabled configuration.

The calculation keeps the inherited arithmetic and diagnostics.
The minimum length check uses `1.0e-8` mm.
The tangent checks use `1.0e-10` radians, and the endpoint check uses `1.0e-7` mm.
The calculated endpoint distance supplies each alignment's length.
The API keeps no result for subsequent use and creates no FreeCAD object.

## B16 caller and recovery

The unchanged `build_straight_routes` caller uses the host name `build_straight_route`.
The product sets that name to a `_StraightRouteAdapter` object in `tracktemplate.compatibility.transition_workflow`.
This object calls the original `clone_straight_config` once before it calls the API.
The caller's earlier clone and `manager_id` checks stay unchanged.
Thus, the inherited UUID calls and their sequence stay unchanged, including for disabled configurations.

The compatibility object reads curve data only for an enabled connected configuration that requests an output.
It supplies endpoint and count values to the API.
It then converts only the new result points with the host's exact `App.Vector` function.
All input curve records, lists and vectors stay unchanged.
For a curve exit, it constructs the remote vector before the join vector, then returns the points in travel order.

The product selects eight functions together and validates their actual caller routes.
It validates the compatibility object's selected API, vector function, configuration function and thickness value.
A selection error puts all eight previous values back before the workflow can start.
It removes a new value when there was no previous value.
The routing record uses schema `6` and contract ID `tracktemplate:phase7:straight-route:1`.
The earlier contracts and frozen tools for host selection and comparison stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-09-phase7-straight-route-regression.md) owns the proof and its limitations.
Supported inputs include the inherited configurations and generated curve records in that proof.
The proof also covers invalid configurations and incomplete curve counts with their inherited diagnostics.

The task does not claim identical error timing for custom containers, malformed vector objects or combined injected failures after curve data collection.

The Core migration owner keeps the temporary compatibility object until its caller has a replacement.
The replacement needs the necessary checks to compare results, recovery and owner acceptance.
This task does not migrate station calculations, changes to turn direction, platform construction, configuration schemas or output functions.
It changes no transaction, persistence or condition to remove a legacy path.
It accepts no Phase 7 exit, product performance result, output or release.
D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
