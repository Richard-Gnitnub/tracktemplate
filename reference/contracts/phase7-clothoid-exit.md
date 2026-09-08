# `clothoid_exit_displacement` API

Status: **Level 2 migration under D-GOV-004 in the open Phase 7 programme.**

The [API data](phase7-clothoid-exit.json) identifies the inputs, units,
source files and comparison fixture. The project owner's
`$tracktemplate-continue` command authorises this bounded cycle after PR #69.
[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel)
keeps the phase scope and conditions.

## How the API calculates its result

`tracktemplate.api.clothoid_exit_displacement` gives the endpoint calculation
from `tracktemplate.domain.alignment`.
Its Python `tuple` contains `dx`, `dy` and `alpha`.
The first two values use mm. The last value uses rad.
Use `canonical-local-XY-left-turn-exit-start` from the API data.

Keep the inherited Simpson integration and its sequence of operations.
The default for `integration_steps` is 240.
Use `max(40, int(integration_steps))`. Increase an odd result by one.
Keep `alpha = length / (2.0 * radius)` and
`theta = (2.0 * alpha * u) - (alpha * u * u)`.

Check `radius <= 0.0` before `length <= GEOMETRY_TOLERANCE`.
The first condition gives the existing `ValueError` diagnostic.
The second gives `(0.0, 0.0, 0.0)`, including when `length` is negative.
Keep `GEOMETRY_TOLERANCE = 1.0e-8` and the existing input types and limits.

The API uses no FreeCAD or Qt. It changes no FreeCAD data.
Each call calculates a result again. It keeps no result for warm reuse.

## How the product selects the API

The B16 Generate/Replace workflow selects five functions from `tracktemplate.api`.
The new function supplies the final position that `build_concentric_core` uses.
Keep the subsequent operations that make points and shapes.

Before selection, make sure that all five functions are present and callable.
Keep their previous values from `module.__dict__`.
Select `main_circle_centre` and `clothoid_exit_displacement` in that namespace.
Use the unchanged `B15WorkflowHost.bind_transition_functions` method for the other three functions.
Then validate all five functions and the APIs that their callers use.

`build_concentric_core` must use both selected functions,
`clothoid_entry_displacement` and `clothoid_exit_displacement`.
Keep each previous check for the other functions and callers.
If an `Exception` occurs, put all five previous values back.
Remove a new entry if its name had no previous value.
Keep the existing error type and cause rules.
Do not start the workflow after a failed check.

Before `routing_record()` gives its result, validate the current functions and callers.
Before `launch_workflow()` starts B16, select the complete set again and validate it.
The product record now uses schema version 3 and the new contract identifier.
The [previous API data](phase7-main-circle-centre.json) keeps its historical
four-function record with schema version 2.
Neither record defines a FreeCAD data schema or a stable Workbench API.

## Validation and preservation

Compare numerical results and diagnostics with both B14 and B15.
Compare actual main, matched and manual caller results on the qualified host.
Keep the checks for the FreeCAD human interface, identities, sequence,
metadata, history, recovery and files that FreeCAD opens again.
Use copies of fixture files.
Compare the accepted B16 route and exact candidate with the same profile and inputs.
Keep the distinct evidence from the development route with `--route legacy`.

The [evidence record](../benchmarks/2026-09-08-phase7-clothoid-exit-regression.md)
gives results and limitations. Data about shapes alone cannot prove that
complete shapes or output bytes are equal.

Do not change B14, B15, the three-function development route or its contract.
Keep all comparison routes until all applicable results are equal and recovery is complete.
Removal also needs acceptance from the project owner.
This task changes no station mapping, sampling, production output or release authority.

Phase 7 stays Open at 0/4. D-P6-008 stays in full.
This task accepts no phase exit or product performance.
