# Common straight-end extension API

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-common-straight-extensions.json) keeps the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## How the API calculates results

`tracktemplate.api.add_common_straight_extensions(alignments, total_angle)`
uses the function in `tracktemplate.domain.alignment`.
The API calculates straight extensions to the common entry and exit positions of the tracks in `alignments`.
Each track has its own record. The API changes no input.

`alignments` is a Python `list` of different Python `dict` records in a specified sequence.
Each record contains `start`, `end` and `core_length`.
The first two values are XY pairs. XY values and lengths use millimetres.
`total_angle` uses radians with the inherited `canonical-local-XY-left-turn` definition.

The inputs are valid records from the functions that build the tracks.
The API adds no input checks or automatic corrections.

The result is a new Python `list` with one new Python `dict` for each input, in the same sequence.
Each Python `dict` has these named items in this sequence:

```text
entry_extension
exit_extension
total_length
extended_start
extended_end
entry_point
exit_point
```

The first five values keep the B14/B15 metadata meanings and sequence of operations.
`entry_point` and `exit_point` are XY pairs only when their extension is greater than `1.0e-8` mm.
Otherwise, these values are `None`.

`extended_start` always uses the common start X value, including below that limit.
`extended_end` changes only when the exit extension is greater than that limit.
An empty input Python `list` gives an empty result Python `list`.
The API keeps no result for subsequent use and creates no FreeCAD object.

## B16 caller and recovery

The `run_macro` caller uses the B15 name `add_common_straight_extensions` before its checks of entry and exit distances.
The product sets that name to a `_CommonStraightExtensionsAdapter` object in `tracktemplate.compatibility.transition_workflow`.
This object uses the selected API and the host's exact `App.Vector` function.

This object supplies only the three input values.
It puts each new point at the start or end of the points with `App.Vector(float(x), float(y), 0.0)`.
It then puts the related value at the start or end of `headings` in the same sequence.
It sets the first five named result values in the same sequence.
The Python `dict` records, Python `list` values for points and `headings`, and `App.Vector` values keep their identities.
The host operation returns `None`, including for an empty input Python `list`.

The product selects seven functions together and validates their actual caller routes.
It validates both compatibility objects and their selected API functions and `App.Vector` functions.
A selection error puts all seven previous values back before the workflow can start.
It removes a new value when there was no previous value.
The routing record uses schema `5` and contract ID `tracktemplate:phase7:common-straight-extensions:1`.
The earlier contracts and frozen tools to select the host functions and compare results during development stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-09-phase7-common-straight-extensions-regression.md) owns the proof and its limitations.
The supported records come from the functions that build the tracks and use different Python `dict` and Python `list` objects.
The API calculates all results before the compatibility object changes the host's Python `list` objects.
This scope does not include incomplete changes that incorrect or incomplete records, or shared input Python `dict` and Python `list` objects, can cause.
The task does not claim that errors occur at the same time for those inputs.
The document recovery procedure stays unchanged.

The Core migration owner keeps the temporary compatibility object until its caller has a replacement.
The replacement needs the necessary checks to compare results, recovery and owner acceptance.
This task does not change how the product reverses turn directions, connects station values to points or uses `build_platform_core`.
It changes no persistence or output contract.
It accepts no Phase 7 exit, product performance result, output or release.
D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
