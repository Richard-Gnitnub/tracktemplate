# Core Calculation of Curve Direction

Status: **A bounded Phase 7 migration contract. This contract accepts no exit.**

## Owner and scope

The alignment domain owns `mirror_alignment_for_turn` through `tracktemplate.api`.
The existing B16 composition supplies the FreeCAD objects and applies the calculated fields to the original alignment record.
The [machine contract](phase7-alignment-handedness.json) gives the exact function and caller identities.

The sole product caller is `run_macro` in the inherited B15 workflow.
It processes the main alignment and each secondary alignment in their existing order.
The call follows the common straight extensions and precedes the length calculation for each alignment.
The construction of straight routes follows those operations.

This work uses the current Core migration authority and the four unchanged [Phase 7 criteria](../PROJECT_PLAN.md#phase-7-exit-conditions).
It does not migrate another family or permit removal of a comparison path.

## Calculation and results

The function has this interface:

```python
mirror_alignment_for_turn(alignment, turn_sign)
```

The function supplies successive `(field_name, value)` pairs.
The caller must fully consume and apply each field before it asks for the next field.
These temporary results are not canonical or stored state.
The domain does not change its input record.

Coordinates are in document XY millimetres. Headings are in radians.
The calculation changes the sign of Y and the heading. It keeps X unchanged.
It does not change point order, sampling, tolerances or the length calculation.

At the first request for a result, the function tests `turn_sign > 0.0` once.
If the test is true, the function supplies no fields and reads no field from the alignment.
Otherwise, it supplies the fields in this order:

| Field | Calculation and sequence |
| --- | --- |
| `points` | Read each point in order. Read X, then Y, and supply `(x, -y)`. Supply the next point only after the caller consumes the previous point. |
| `headings` | After the caller applies `points`, calculate a new list of negated headings in their original order. |
| `start`, `end`, `extended_start`, `extended_end` | Examine each key in this order. For each key that is present, read its two values and supply `(x, -y)`. |

Zero, negative zero and NaN follow the existing branch that changes the signs.
Positive infinity follows the branch that supplies no fields.
There is no new check for finite values, no heading normalisation and no rule for equal point and heading counts.

## Compatibility at the FreeCAD boundary

The B16 compatibility object keeps the original record and returns `None` on success.
For each point, it converts X and Y to `float`, then creates one fresh `App.Vector` with Z equal to zero.
It completes that vector before it reads the next point.
It replaces the `points` list only after all its new vectors are complete.
It then applies each subsequent field before it asks for the next result.

A positive sign leaves all input objects and values unchanged.
The other branch creates fresh point and heading lists. References to the old lists keep those old lists.
The alignment record keeps its identity. Unrelated metadata, identifiers and key order stay unchanged.
Two successful sign changes restore the original XY and heading values, with fresh lists and vectors each time.

Ordinary errors keep their existing exception types, messages and sequence at the host boundary.
If point creation fails, the original fields remain installed.
If heading calculation fails, the new points remain installed and the original headings remain installed.
If an endpoint fails, earlier field changes remain and later endpoints are not read.
These partial changes are existing behaviour; this operation does not add a transaction.
The enclosing workflow keeps its existing recovery and history behaviour.

The domain has no FreeCAD or Qt dependency, host constructor or import from a compatibility object.
Small temporary views allow the domain to read neutral coordinates in the original sequence.
Those views do not become stored state or escape in the host result.

## Composition and evidence boundary

Current composition selects eleven functions together and validates 38 caller entries.
Its record has schema version `8` and contract identity `tracktemplate:phase7:alignment-handedness:1`.
The existing `run_macro` entry adds only the selected curve-direction function.
A failed selection restores every previous binding, including a name that was originally absent.
The historical three-function comparison contract and all earlier contract identities stay unchanged.

The [regression record](../benchmarks/2026-09-12-phase7-alignment-handedness-regression.md) owns the observed correctness, workflow and cost evidence.
It does not give performance acceptance or complete output equivalence.
D-P6-008 and all comparison and legacy-retirement conditions stay in full.
Phase 7 remains Open at 0/4. Output stays private-development and project status stays `unknown`.
