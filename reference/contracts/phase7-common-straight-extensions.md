# Common straight-end extension API

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-common-straight-extensions.json) keeps the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Calculation

`tracktemplate.api.add_common_straight_extensions(alignments, total_angle)`
uses the calculation in `tracktemplate.domain.alignment`.
The API calculates straight extensions to the common entry and exit positions of independent tracks.
It changes no input.

`alignments` is an ordered Python `list` of separate Python `dict` records.
Each record contains `start`, `end` and `core_length`.
The first two values are XY pairs. Coordinates and lengths use millimetres.
`total_angle` uses radians in the inherited `canonical-local-XY-left-turn` frame.

The inputs are valid records from the existing track builders.
The API adds no input checks or automatic corrections.

The result is a new list with one new dictionary for each input, in the same sequence.
Each dictionary has these keys in this sequence:

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
An empty input list gives an empty result list.
The API keeps no result for subsequent use and creates no FreeCAD object.

## B16 caller and recovery

The existing `run_macro` caller uses the B15 name `add_common_straight_extensions` before its entry and exit spacing checks.
The product sets that name to a `_CommonStraightExtensionsAdapter` object in `tracktemplate.compatibility.transition_workflow`.
This object uses the selected API and the host's exact `App.Vector` function.

This object supplies only the three input fields.
It inserts or appends each new point with `App.Vector(float(x), float(y), 0.0)`.
It then inserts or appends the corresponding heading in the existing sequence.
It assigns the first five result fields in their existing sequence.
The existing dictionaries, point lists, heading lists and vectors keep their identities.
The host operation returns `None`, including for an empty input list.

The product selects seven functions together and validates their actual caller routes.
It validates both compatibility objects and their selected calculations and `App.Vector` functions.
A selection error puts all seven previous values back before the workflow can start.
It removes a new value when there was no previous value.
The current routing record uses schema `5` and contract ID `tracktemplate:phase7:common-straight-extensions:1`.
The earlier contracts, frozen host loader and development comparison binder stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-09-phase7-common-straight-extensions-regression.md) owns the proof and its limitations.
The supported records come from the existing builders and use separate dictionaries and lists.
The API calculates all results before the compatibility object changes the host lists.
This scope excludes the partial changes that incorrect or incomplete records or shared input dictionaries and lists can cause.
The task does not claim equal failure timing for those inputs.
The existing document recovery procedure stays unchanged.

The Core migration owner keeps the temporary compatibility object until its caller has a replacement.
The replacement needs the required comparison, recovery and owner acceptance.
This task changes no turn mirroring, station mapping, platform calculation, persistence or output contract.
It accepts no Phase 7 exit, performance result, output or release.
D-P6-008 and all comparison and legacy-retirement conditions stay in full.
