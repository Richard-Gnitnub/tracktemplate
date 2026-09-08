# `main_circle_centre` API

Status: **D-P7-001 authorises this Level 2 API.**

The [API data](phase7-main-circle-centre.json) identifies the API, units,
source files and fixture. It also identifies the data from `routing_record()`.
This technical document gives instructions for the API.
[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel)
defines the project authority and bounded conditions.

## How the API calculates its result

Move `main_circle_centre` to `tracktemplate.domain.alignment`.
Make it available through `tracktemplate.api`.
Use this API in the B16 Generate/Replace workflow.
The API gives a Python `tuple` with two `float` values.
These are local X and Y values in mm.
Use `canonical-local-XY-left-turn` from the API data.

Keep the name `_left_normal`. Do not add it to `tracktemplate.api`.
Do not change `clothoid_entry_displacement` or its diagnostics.
Keep the same sequence of operations and the same results for each input.
Do not change the type of an input. Add no limit to the permitted input values.

Inputs with `main_transition < 0` give compatibility evidence only.
The API uses no FreeCAD or Qt. It reads no FreeCAD data.
It keeps no result for a subsequent operation.
It changes no input or other data that was available before the operation.

Do not change the B14 or B15 source files or the tolerances for the tests.
Compare the API results, diagnostics and results from the caller.

## How the product selects the API

Before the workflow changes any function, make sure that `callable` gives `True` for all four functions.
Keep the four previous values from `module.__dict__`.
Put the new `main_circle_centre` in `module.__dict__`.
Then use `B15WorkflowHost.bind_transition_functions` for the other three functions.
Do not change that method.
Before the workflow starts, validate all four functions and their callers.

If an `Exception` occurs during these operations, put the four previous values back in `module.__dict__`.
If a name had no previous value, remove its new entry.
Then, for `B15WorkflowHostError`, give `TransitionWorkflowError` with that error as its cause.
Send each other `Exception` to the caller without a change.
These operations must change no FreeCAD data.

Make sure that `main_circle_centre` uses the selected `clothoid_entry_displacement`.
Make sure that `run_macro` uses the selected `main_circle_centre` from `module.__dict__`.
Keep every previous check for the functions and callers.
Before `routing_record()` gives its result, validate the current functions and callers.
Before `launch_workflow()` starts B16, select the complete set of functions again.
Then validate the functions and callers.

`routing_record()` gives data with a version. These data identify the functions that B16 uses.
They do not define a schema for FreeCAD data or a stable Workbench API.
Do not change the three-function route that the development tools use or the data from that route.

## Validation and source files

Compare the calculated results and the caller results.
Keep the same subsequent operations that make FreeCAD shapes.
Keep the checks for identities, sequence, metadata and shapes.
Data about shapes alone cannot prove that complete shapes or output bytes are equal.

Do the checks for the FreeCAD human interface, `Undo`, `Redo` and recovery after an error.
Do the checks that open FreeCAD files again. Use files that have other copies.
Compare the accepted B16 route and the exact candidate on the same qualified host profile and fixture.
Do different checks for `--route legacy`.

Each operation of this API calculates its result again. There is no warm reuse.
Report the time to calculate the result again as a different result.

`B15WorkflowHost` keeps the B15 functions for the development route and migration.
Keep these routes until all applicable results are equal and recovery is complete.
Before you remove any of these APIs, get acceptance from the project owner to remove them.

This task gives no acceptance of a Phase 7 exit or product performance.
D-P6-008 stays in full. This task authorises no new production output or release.
This task removes no B14 or B15 route.
