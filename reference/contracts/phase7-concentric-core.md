# `build_concentric_core` API

Status: **Level 2 API instructions for the bounded Phase 7 task.**

The [machine record](phase7-concentric-core.json) records the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Calculation

`tracktemplate.api.build_concentric_core` calls the implementation in
`tracktemplate.domain.alignment`.
It takes these six arguments in this order:

```python
build_concentric_core(
    circle_centre, radius, entry_transition, exit_transition, total_angle, label,
)
```

Lengths and XY coordinates are in millimetres. Angles are in radians.
The calculation uses the same local left-turn frame as B14 and B15.
It keeps their sequence of operations, point order and diagnostics.
It adds no input limits or automatic corrections.

The result is a new Python dictionary with the same keys and key order.
Its `points` value is a list of `(float(x), float(y))` pairs.
Its `headings` value is a list in the same order.
All other values keep their B14/B15 types and meanings.
No FreeCAD object crosses this API.

| Preserved calculation | Value or operation |
| --- | --- |
| Point interval | `_CORE_SAMPLE_SPACING = 3.0` mm; same segment count |
| Geometry tolerance | `1.0e-8` mm |
| Straightness test | `abs(curvature) < 1.0e-14` |
| Circular-angle rejection | `circular_angle < -1.0e-9` rad |
| Endpoint corrections | Same exact circle joins and independently integrated exit endpoint |
| Input checks | Radius, negative transition lengths, then total angle; same diagnostics |

The calculation uses the existing entry and exit APIs.
Its helper functions keep the B14/B15 point calculation and XY rotation.
It makes no cache, document change, file, shape or export.

## B16 caller route

The B16 product selects six APIs together.
Five names in the B15 module refer directly to the selected APIs.
The B15 module's `build_concentric_core` name refers to a
`_ConcentricCoreAdapter` in `tracktemplate.compatibility.transition_workflow`.

This object calls the selected API. It changes only `points` in the new result.
For each point, it calls the B15 module's selected
`App.Vector(float(x), float(y), 0.0)`.
The existing `run_macro` and `prepare_track_alignment` callers therefore
receive the same FreeCAD values and types.

The product verifies the six selected functions and their actual caller routes.
It also verifies the exact calculation and vector function in this object.
If selection or verification fails, it puts all six previous B15 values back.
It removes a new value when no previous value existed.
A failed verification prevents workflow launch.
A routing report verifies the current values without changing them.

The product record uses schema `4` and contract ID
`tracktemplate:phase7:concentric-core:1`.
The frozen `load_b15_workflow_host` function still verifies the B15 source and initial caller routes.
The current product then owns selection of its six functions.
The historical `bind_transition_functions` method and development comparison route stay unchanged.
The earlier centre and exit contracts keep their historical identities.

## Evidence and limits

The [bounded evidence record](../benchmarks/2026-09-08-phase7-concentric-core-regression.md)
reports the complete result comparisons and applicable FreeCAD checks.
It also reports the time and memory values and their limitations.

The modular calculation owns its necessary helper functions.
The Core migration owner keeps the temporary conversion until its
remaining callers have replacements under the existing comparison,
recovery and owner acceptance conditions.

This task changes no station mapping, platform calculation, stored state or output contract.
It accepts no Phase 7 exit, performance result, output or release.
D-P6-008 and all conditions for comparison and removal of legacy paths stay in full.
