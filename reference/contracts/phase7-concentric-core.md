# `build_concentric_core` API

Status: **Level 2 API instructions for the bounded scope in Phase 7.**

The [machine record](phase7-concentric-core.json) records the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## How the API calculates results

`tracktemplate.api.build_concentric_core` uses the function in
`tracktemplate.domain.alignment`.
It takes these six inputs in this sequence:

```python
build_concentric_core(
    circle_centre, radius, entry_transition, exit_transition, total_angle, label,
)
```

The API uses millimetres for lengths and XY values.
It uses radians for `total_angle`, `entry_angle`, `exit_angle`, `circular_angle` and `headings`.
It uses the B14/B15 definitions for `canonical-local-XY-left-turn` in the machine record.
It keeps their sequence of operations, point sequence and diagnostics.
It adds no input limits or automatic corrections.

The result is a new Python `dict` with the same named items and item sequence.
Its `points` value is a Python `list` of `(float(x), float(y))` pairs.
Its `headings` value is a Python `list` in the same sequence.
All other values keep their B14/B15 types and meanings.
No FreeCAD object crosses this API.

| Preserved item | Value or operation |
| --- | --- |
| Point interval | `_CORE_SAMPLE_SPACING = 3.0` mm, same segment count |
| `GEOMETRY_TOLERANCE` | `1.0e-8` mm |
| Condition for straight points | `abs(curvature) < 1.0e-14` |
| Reject when | `circular_angle < -1.0e-9` rad |
| End point corrections | Same corrections at the exact circular section ends and the exit end point, which Simpson integration calculates independently |
| Input checks | `radius`, negative transition lengths, then `total_angle`, with the same diagnostics |

The API uses `clothoid_entry_displacement` and `clothoid_exit_displacement`.
Its `_integrate_core_segment` and `_rotate_xy` functions calculate points and turn XY values with the same B14/B15 operations.
It keeps no results for subsequent use.
It changes no document and creates no file, FreeCAD shape or physical output.

## B16 caller route

The B16 product selects six APIs together.
Five names in the B15 source refer directly to the selected APIs.
The B15 source's `build_concentric_core` name refers to a
`_ConcentricCoreAdapter` in `tracktemplate.compatibility.transition_workflow`.

This object uses the selected API. It changes only `points` in the new result.
For each point, it uses the B15 source's selected
`App.Vector(float(x), float(y), 0.0)`.
Thus, the `run_macro` and `prepare_track_alignment` callers receive the same FreeCAD values and types.

The product validates the six selected functions and their actual caller routes.
It also validates this object's exact `calculation` and `vector_factory` values.
If selection or validation gives an error, it puts all six previous B15 values back.
It removes a new value when there was no previous value.
A validation error stops the workflow before it starts.
A routing report validates the selected values and does not change them.

The product record uses schema `4` and contract ID
`tracktemplate:phase7:concentric-core:1`.
The frozen `load_b15_workflow_host` function still validates the B15 source and initial caller routes.
The product then owns selection of its six functions.
The historical `bind_transition_functions` method and its development route to compare results stay unchanged.
The earlier centre and exit contracts keep their historical identities.

## Evidence and limits

The [evidence record for the bounded scope](../benchmarks/2026-09-08-phase7-concentric-core-regression.md)
reports the checks that compare complete results and the applicable FreeCAD checks.
It also reports the time and memory values and their limitations.

`tracktemplate.domain.alignment` owns the necessary `_integrate_core_segment` and `_rotate_xy` functions.
The Core migration owner keeps the temporary `_ConcentricCoreAdapter` until its remaining callers have replacements.
The conditions to compare results, recover work and get owner acceptance still apply to those replacements.

This task changes no station mapping, `build_platform_core` function, persistence or output contract.
It accepts no Phase 7 exit, product performance result, output or release.
D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
