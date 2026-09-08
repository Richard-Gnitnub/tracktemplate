# `clothoid_exit_displacement` API

Status: **Level 2 migration under D-GOV-004 in the open Phase 7 programme.**

The [API data](phase7-clothoid-exit.json) identifies the inputs, units,
source files and fixture for the tests. The project owner's
`$tracktemplate-continue` command authorises this bounded cycle after PR #69.
[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel)
keeps the bounded scope and conditions for the phase.

## How the API calculates its result

`tracktemplate.api.clothoid_exit_displacement` gives the endpoint calculation
from `tracktemplate.domain.alignment`.
Its Python `tuple` contains `dx`, `dy` and `alpha`.
The first two values use mm. The last value uses rad.
Use `canonical-local-XY-left-turn-exit-start` from the API data.

Keep the B14 and B15 Simpson integration and its sequence of operations.
If the caller supplies no value for `integration_steps`, use 240.
Use `steps = max(40, int(integration_steps))`.
If `steps % 2` is 1, increase `steps` by one.
Keep `alpha = length / (2.0 * radius)` and
`theta = (2.0 * alpha * u) - (alpha * u * u)`.

Check `radius <= 0.0` before `length <= GEOMETRY_TOLERANCE`.
The first condition gives the same `ValueError` diagnostic as B14 and B15.
The second gives `(0.0, 0.0, 0.0)`. This also applies when `length < 0.0`.
Keep `GEOMETRY_TOLERANCE = 1.0e-8` and the same input types and limits as B14 and B15.

The API uses no FreeCAD or Qt. It changes no FreeCAD data.
The API calculates a result again each time. It keeps no result for warm reuse.

## How the product selects the API

The B16 Generate/Replace workflow selects five functions from `tracktemplate.api`.
The new function supplies the position at the end that `build_concentric_core` uses.
Keep the subsequent operations that make points and shapes.

Before the product selects the API, make sure that none of the five function names is missing.
Validate each function with `callable()`.
Keep their previous values from `module.__dict__`.
Select `main_circle_centre` and `clothoid_exit_displacement` in `module.__dict__`.
Use the same `B15WorkflowHost.bind_transition_functions` method for the other three functions.
Then validate all five functions and the APIs that their callers use.

`build_concentric_core` must use both selected functions,
`clothoid_entry_displacement` and `clothoid_exit_displacement`.
Keep each previous check for the other functions and callers.
If an `Exception` occurs, put all five previous values back.
If a name had no previous value, remove its new entry.
Keep the same error type and cause rules as before.
If a check gives a FAIL result, do not start the workflow.

Before `routing_record()` gives its result, validate the current functions and callers.
Before `launch_workflow()` starts B16, select all five functions again. Then validate them.
The product record now uses schema version 3 and the new `contract_id`.
The [previous API data](phase7-main-circle-centre.json) keeps its
four-function record with schema version 2.
Neither record defines a FreeCAD data schema or a stable Workbench API.

## Validation and preservation

Compare calculated results and diagnostics with both B14 and B15.
On the qualified host, compare the product caller results for `main_alignment`, `match_alignment` and `manual_alignment`.
Keep the checks for the FreeCAD human interface, identities, sequence,
metadata, Undo/Redo, recovery and files that FreeCAD opens again.
Use copies of fixture files.
Compare the accepted B16 route and exact candidate with the same profile and inputs.
Keep the distinct evidence from the development route with `--route legacy`.

The [evidence record](../benchmarks/2026-09-08-phase7-clothoid-exit-regression.md)
gives results and limitations. Data about shapes alone cannot prove that
full shapes or output bytes are equal.

Do not change B14, B15, the three-function development route or its API data.
Keep all routes that the tests compare until all applicable results are equal and recovery is complete.
Acceptance from the project owner is also necessary for removal.
This task changes no station mapping, number or position of points, production output or release authority.

Phase 7 stays Open at 0/4. D-P6-008 stays in full.
This task accepts no phase exit or product performance.
