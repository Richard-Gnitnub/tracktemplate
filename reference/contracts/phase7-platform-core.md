# API to build a platform-transition core

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-platform-core.json) keeps the exact values.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Inputs and result

`tracktemplate.api.build_platform_core(circle_centre, radius,
entry_transition, exit_transition, entry_shape_parameter,
exit_shape_parameter, total_angle, label)` uses the function in
`tracktemplate.domain.alignment`. The eight parameters are necessary and have
no default values.

Lengths and XY values use millimetres. Headings and `total_angle` use radians.
The two shape parameters have no unit. `circle_centre` is one XY pair. The
calculation uses the `canonical-local-XY-left-turn` frame.

The function returns a new Python `dict`. Its named items have this sequence:

```text
label
points
headings
start
end
radius
entry_transition
exit_transition
entry_angle
exit_angle
circular_angle
circular_length
core_length
entry_shape_parameter
exit_shape_parameter
minimum_radius
```

Each point is a new pair of Python `float` values. The function also creates
new `points` and `headings` lists for each call. The first and last points are
equal to `start` and `end`. The last heading is equal to `total_angle`.

The function changes no input. It keeps no result for subsequent use. It
constructs no FreeCAD object and changes no FreeCAD document.

## Calculation and point sequence

The function calculates the entry displacement before the exit displacement.
Each displacement calculation uses 480 steps of the inherited composite
Simpson calculation. The function rejects an excess combined transition angle
before it calculates the point lists. A negative circular angle within
`1.0e-8` radians becomes zero.

The point calculation uses the inherited 3 mm maximum step spacing. For each
segment, the step count is `ceil(length / 3.0)`. It calculates curvature at the
middle of each step. It uses the inherited constant-curvature arc calculation
unless the absolute curvature is less than `1.0e-14`. The geometry tolerance
is `1.0e-8` mm.

The function keeps this endpoint sequence:

1. Calculate the sampled entry transition.
2. Put the exact calculated circle-start point and heading at its end.
3. Calculate the sampled constant-radius segment.
4. Put the exact calculated circle-end point and heading at its end.
5. Calculate the sampled exit transition.
6. Put the independently calculated exit-displacement point at its end.
7. Put `total_angle` in the last heading.

The function calculates `minimum_radius` from `radius` and the two inherited
peak-curvature factors. It keeps the inherited operation order and all Python
floating-point operations.

## Diagnostics

The [machine record](phase7-platform-core.json) keeps the exact diagnostic
format strings and their conditions. The function gives a `ValueError` in this
order:

1. A radius that is zero or negative.
2. A negative entry or exit transition length.
3. An invalid entry shape parameter.
4. An invalid exit shape parameter.
5. A combined transition angle that is more than the complete turn angle by
   more than `1.0e-8` radians.

The fifth diagnostic keeps the entry, exit, combined and complete angles in
degrees. It also keeps the inherited suggested entry and exit lengths. The
standalone and qualified-host proofs compare the exception type and complete
diagnostic text with B14 and B15.

## B16 caller and recovery

The unchanged `prepare_track_alignment` caller uses the host name
`build_platform_core`. The product sets that name to a
`_PlatformCoreAdapter` object in
`tracktemplate.compatibility.transition_workflow`. This object calls the
public API one time. It changes only the new `points` list to contain
`App.Vector(float(x), float(y), 0.0)` values in the same sequence. It keeps all
other result items unchanged.

The product selects fifteen functions together and validates 39 caller routes.
It also validates the two selected calculations that `build_platform_core`
uses. A selection error puts all previous values back. It removes a supplied
value when that name was initially absent. The product rejects a mixed set of
selected values before workflow launch.

The routing record uses schema `10` and contract ID
`tracktemplate:phase7:platform-core:1`. The earlier contracts, B14, B15, the
launcher and the frozen host loader stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-20-phase7-platform-core-regression.md)
owns the proof and its limitations. Supported inputs are the B14/B15 numeric
inputs and the qualified-FreeCAD inputs in that proof. The task does not claim
the same failure sequence for arbitrary custom numeric or point objects.

The task does not migrate the complete `prepare_track_alignment` function. It
does not change persistence, output, physical-platform, sectioning or export
behaviour. The Core migration owner keeps the compatibility object until its
caller has an accepted replacement and all removal conditions are complete.

The task accepts no Phase 7 exit, product performance result, output status or
release state. D-P6-008 and all conditions to compare results and remove legacy
paths stay in full.
