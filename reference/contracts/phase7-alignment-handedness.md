# Core Calculation of Curve Direction

Status: **A bounded Phase 7 migration contract. This contract accepts no exit.**

## Owner and scope

`tracktemplate.domain.alignment` owns `mirror_alignment_for_turn` through `tracktemplate.api`.
The current B16 workflow supplies the FreeCAD objects and applies the calculated named items to the initial alignment record.
The [machine contract](phase7-alignment-handedness.json) gives the exact function and caller identities.

The sole product caller is `run_macro` in the earlier B15 workflow.
It processes the main alignment and each secondary alignment in their initial sequence.
The operation is after the common straight extensions and before the length calculation for each alignment.
The construction of straight routes is after those operations.

This work uses the current Core migration authority and the four unchanged [Phase 7 criteria](../PROJECT_PLAN.md#phase-7-exit-conditions).
It does not migrate another family or permit removal of a path to compare results.

## Calculation and results

The function has this interface:

```python
mirror_alignment_for_turn(alignment, turn_sign)
```

The function supplies subsequent `(field_name, value)` pairs.
The caller must complete all operations for each named item and apply it before it gets the next named item.
These temporary results are not canonical or stored state.
The function does not change its input record.

XY values use the document X and Y axes, in millimetres. Values for track direction use radians.
The calculation changes the sign of Y and the track direction. It keeps X unchanged.
It does not change point sequence, sampling, tolerances or the length calculation.

At the first request for a result, the function tests `turn_sign > 0.0` once.
If the test is true, the function supplies no named items and reads no named item from the alignment.
Otherwise, it supplies the named items in this sequence:

| Named item | Calculation and sequence |
| --- | --- |
| `points` | The function reads each point in sequence. It reads X, then Y, and supplies `(x, -y)`. The caller completes all operations for that point before it gets the next point. |
| `headings` | After the caller applies `points`, the function makes a new Python `list`. It changes the sign of each value for track direction in the initial sequence. |
| `start`, `end`, `extended_start`, `extended_end` | The function examines each key in this sequence. For each key that is present, it reads its two values and supplies `(x, -y)`. |

Zero, negative zero and NaN use the earlier branch that changes the signs.
Positive infinity uses the branch that supplies no named items.
The function adds no check for infinity or NaN.
It does not change the range of values for track direction.
It adds no rule for equal counts of points and values for track direction.

## Compatibility at the FreeCAD boundary

The B16 compatibility object keeps the initial record and returns `None` when the operation has no error.
For each point, it converts X and Y to `float`, then makes one new `App.Vector` with Z equal to zero.
It completes that object before it reads the next point.
It replaces the Python `list` for `points` only after all its new `App.Vector` objects are complete.
It then applies each subsequent named item before it gets the next result.

A positive sign leaves all input objects and values unchanged.
The other branch makes new Python `list` objects for points and values for track direction.
References to the old objects keep those old objects.
The alignment record keeps its identity. Unrelated metadata, identifiers and key sequence stay unchanged.
Two sign changes without errors give the initial XY values and values for track direction, with new Python `list` and `App.Vector` objects each time.

Usual errors keep their earlier exception types, messages and sequence at the host boundary.
If point creation fails, the initial named items stay installed.
If calculation of track direction fails, the new points and the initial values for track direction stay installed.
If an endpoint fails, earlier changes to named items stay installed and the function does not read later endpoints.

These partial changes are earlier behaviour. This operation does not add a transaction.
The workflow that contains this operation keeps its earlier recovery and history behaviour.

The function has no FreeCAD or Qt dependency, host function to make objects, or import from a compatibility object.
Temporary `_MirrorAlignmentView` and `_StationXYPointView` objects supply XY values without FreeCAD objects in the initial sequence.
Those temporary objects do not become stored state or part of the host result.

## Function selection and evidence boundary

The current workflow selects eleven functions together and validates 38 caller entries.
Its record has schema version `8` and contract identity `tracktemplate:phase7:alignment-handedness:1`.
The current `run_macro` entry adds only the selected curve-direction function.
After a selection error, the workflow puts all previous values back.
It removes an added name if that name was initially absent.
The historical three-function contract to compare results and all earlier contract identities stay unchanged.

The [regression record](../benchmarks/2026-09-12-phase7-alignment-handedness-regression.md) owns the observed correctness, workflow and cost evidence.
It does not give performance acceptance or proof of equal complete outputs.
D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
Phase 7 stays Open at 0/4. Output stays private-development and project status stays `unknown`.
