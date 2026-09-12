# API to build straight tracks

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-straight-route.json) keeps the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Inputs and results

`tracktemplate.api.build_straight_route(config, curve_alignments, connected_template_thickness)`
uses the function in `tracktemplate.domain.alignment`.
It calculates parallel straight tracks with no curve connection.
It also calculates straight tracks that connect to the entrance or exit of a curve.

Lengths and XY values use millimetres. Values for track direction use radians.
For tracks with no curve connection, the input `rotation_degrees` uses degrees.
Track sequence, travel direction and the inherited `canonical-local-XY-left-turn` definition stay unchanged.

`config` is the Python `dict` from the host's unchanged `clone_straight_config` function.
The API changes no input and supplies no missing `config` values or UUID values.
The necessary `connected_template_thickness` input is the host's actual `TEMPLATE_THICKNESS` value.
That value is `1.0` mm.

Each Python `dict` in `curve_alignments` supplies these six named items:

```text
point_count
heading_count
start
end
start_heading
end_heading
```

The end point values are XY pairs. Missing end point or track direction values use `None`.
The initial counts let the API reject incomplete curve data before it uses the end point values.
The named items `name`, `width`, `create_template` and `show_centreline` keep their initial presence and values.

For a missing name or display setting, the API uses the same replacement value as the host.
Each complete connected curve record must supply `width`.
No FreeCAD value or curve point between the ends crosses this API.

The result keeps its six named items and the twenty named items in each `alignments` record in their initial sequence.
Each new record in `alignments` contains two new XY pairs in `points`.
The result's `config` value is the exact Python `dict` supplied to the API.
The function keeps the inherited names, identities, display settings, widths, thickness and source metadata.
It returns `None` for a disabled `config`.

The API keeps the inherited operations to calculate results and the diagnostics.
The minimum length check uses `1.0e-8` mm.
The checks of track direction use `1.0e-10` radians, and the end point check uses `1.0e-7` mm.
The calculated distance between the end points supplies the length of each record in `alignments`.
The API keeps no result for subsequent use and creates no FreeCAD object.

## B16 caller and recovery

The unchanged `build_straight_routes` caller uses the host name `build_straight_route`.
The product sets that name to a `_StraightRouteAdapter` object in `tracktemplate.compatibility.transition_workflow`.
This object uses the initial `clone_straight_config` one time before it uses the API.
The caller's earlier operation to make a copy and its `manager_id` checks stay unchanged.
Thus, the inherited UUID operations and their sequence stay unchanged, including for disabled `config` inputs.

The compatibility object reads curve data only for an enabled `config` that requests a curve connection and an output.
It supplies end point and count values to the API.
It then changes only the new result points with the host's exact `App.Vector` function.
All input curve records, Python `list` objects and `App.Vector` values stay unchanged.
For a curve exit, it creates the `App.Vector` away from the curve before the `App.Vector` at the connection.
It then returns the points in travel sequence.

The product selects eight functions together and validates their actual caller routes.
It validates the compatibility object's selected API, `App.Vector` function, `clone_straight_config` function and thickness value.
A selection error puts all eight previous values back before the workflow can start.
It removes a new value when there was no previous value.
The routing record uses schema `6` and contract ID `tracktemplate:phase7:straight-route:1`.
The earlier contracts and frozen tools to select host functions and compare results stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-09-phase7-straight-route-regression.md) owns the proof and its limitations.
Supported inputs include the inherited `config` values and generated curve records in that proof.
The proof also includes invalid `config` values and incomplete curve counts with their inherited diagnostics.

The task does not claim the same error sequence for other Python types, incorrect point objects or combined test errors after it collects curve data.

The Core migration owner keeps the temporary compatibility object until its caller has a replacement.
The replacement needs the necessary checks to compare results, recovery and owner acceptance.

This task does not migrate functions that calculate station values, change turn direction or build platforms.
It does not migrate `config` schemas or output functions.
It changes no transaction, persistence or condition to remove a legacy path.
It accepts no Phase 7 exit, product performance result, output or release.
D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
