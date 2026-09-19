# Core calculations for platform transitions

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-platform-transitions.json) gives the exact function,
constant and caller identities. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Owner and scope

`tracktemplate.domain.alignment` owns the six related calculations. The public
API supplies these three functions:

```python
platform_transition_displacement(
    length, radius, shape_parameter, transition_kind, integration_steps=320,
)
platform_peak_curvature_factor(shape_parameter)
solve_platform_shape_parameter(
    circle_centre,
    radius,
    transition_length,
    target_line_offset,
    total_angle,
    track_name,
    end_name,
    transition_kind,
)
```

The same domain module keeps `platform_transition_angle`,
`platform_line_offset` and `_platform_parameter_grid` as internal functions.
Together, the six functions make the complete bounded calculation group. They
have no FreeCAD
or Qt dependency.

Lengths and XY values use millimetres. Angles use radians. The calculation uses
the canonical local XY frame for a left-hand curve. It does not change an input
object, keep a result for subsequent use or create canonical or stored state.

The existing B16 `prepare_track_alignment` caller uses
`solve_platform_shape_parameter` for the entry and exit. The existing
`build_platform_core` caller uses `platform_transition_displacement` for the two
ends and `platform_peak_curvature_factor` for the two peak-curvature values.
These host callers keep their initial operations and changes to host state.

This extraction does not move `build_platform_core`, all of
`prepare_track_alignment` or the three alignment-mode calculations. It changes
no solver rule, tolerance, diagnostic, persistence rule, output rule or
condition to remove a legacy path.

## Transition displacement

`platform_transition_displacement` first checks `radius`. A value less than or
equal to zero gives this error:

```text
A platform-transition radius must be greater than zero.
```

After that check, a `length` less than or equal to `1.0e-8` gives
`(0.0, 0.0, 0.0)`. This return occurs before checks of `shape_parameter` and
`transition_kind`.

A `shape_parameter` less than `-0.25 - 1.0e-10` gives this error:

```text
A platform-transition shape parameter became invalid.
```

`transition_kind` must be `entry` or `exit`. A different value gives this error:

```text
Unknown platform-transition direction.
```

`int(integration_steps)` gives the step count. The function uses at least 80
steps.
If the result is odd, the function adds one. Thus, the numerical integration
always uses an even step count.

For each normalised station `u`, the common bump integral is:

```text
16 * ((u**3 / 3) - (u**4 / 2) + (u**5 / 5))
```

The entry and exit values for track direction are:

```text
entry: (length / radius) * (u**3 - (0.5 * u**4)
                            + (shape_parameter * common_bump_integral))
exit:  (length / radius) * (u - u**3 + (0.5 * u**4)
                            + (shape_parameter * common_bump_integral))
```

The function uses Simpson integration for the cosine and sine of these values.
It gives `(dx, dy, angle)`. The final angle is:

```text
(length / radius) * (0.5 + ((8.0 / 15.0) * shape_parameter))
```

## Peak curvature

`platform_peak_curvature_factor` calculates the maximum curvature divided by
the constant-curve curvature. It starts with `u=0.0` and `u=1.0`. It also uses
each real interior root from these coefficients:

```text
a = 64.0 * shape_parameter
b = -6.0 - (96.0 * shape_parameter)
c = 6.0 + (32.0 * shape_parameter)
```

When the absolute value of `a` is less than or equal to `1.0e-14`, the function
uses the linear root only if the absolute value of `b` is greater than that
value. In all other cases, it uses the roots of the quadratic only when its
discriminant is greater than or equal to zero. Only roots greater than zero and
less than one become candidates.

For each candidate `u`, the function calculates:

```text
(3.0 * u**2) - (2.0 * u**3)
+ (16.0 * shape_parameter * u**2 * (1.0 - u)**2)
```

The result is the largest candidate value, with a minimum result of `1.0`.

## Internal support calculations

`platform_transition_angle` gives `0.0` when `length` is less than or equal to
`1.0e-8`. For all other lengths, it uses the final-angle expression in the
displacement calculation.

`platform_line_offset` first gets `(dx, dy, angle)` from
`platform_transition_displacement`. For an entry transition, it gives:

```text
circle_centre_y - (radius * cos(angle)) - dy
```

For an exit transition, it gets the left normal at `total_angle`. It calculates
the normal coordinate of the circle centre and the normal displacement of the
transition. It then gives:

```text
centre_normal_coordinate
- (radius * cos(angle))
+ transition_normal_displacement
```

`_platform_parameter_grid(lower, upper)` gives an empty Python `list` when
`upper < lower`. If the interval crosses zero, it supplies 36 equal steps from
`lower` to zero. For an interval with only negative values, it supplies 80 equal steps and
stops. For a positive part, it supplies 240 quadratic steps from the applicable
zero or lower bound to `upper`. It adds the upper bound when the last value is
different by more than `1.0e-12`.

## Solution for a shape parameter

`solve_platform_shape_parameter` first rejects a `radius` less than or equal to
zero. It
then rejects a negative `transition_length`. These errors identify the track
and the applicable entry or exit.

For a length less than or equal to `1.0e-8`, the function calculates the line
offset with zero length and zero shape. If its difference from
`target_line_offset` is less than or equal to `1.0e-6`, the result is:

```text
shape_parameter: 0.0
angle: 0.0
peak_factor: 1.0
minimum_radius: radius
```

If the function does not give this result, it reports that a non-zero
transition length is necessary for the requested spacing. It includes the requested signed offset and the calculated
zero-length offset in the diagnostic.

For a non-zero length, the minimum shape value is `-0.187499`. The maximum
permitted transition angle is the larger of `1.0e-8` and
`total_angle - 1.0e-8`. These values set the maximum shape value. If the maximum
is less than the minimum, the function reports that the transition is too long
for
the total turn. It includes the length, smallest possible transition angle and
complete turn angle in the diagnostic.

The function calculates the offset difference for each value in the parameter
grid with 240 integration steps. It keeps a grid value when its offset
difference is less than or equal to `1.0e-7`. It also keeps
each adjacent interval that has a sign change.

The function refines the grid value with the smallest absolute offset
difference. It does 72 golden-section iterations between the adjacent grid
values and uses 360 integration steps. It keeps that result only when its
residual is less than or equal to `1.0e-5`.

For each sign-change interval, the function uses at most 72 bisection
iterations and 320 integration steps. It stops when the residual is less than
or equal to `1.0e-10` or the parameter interval is less than or equal to
`1.0e-9`.

If the function finds no candidate, it reports that the requested spacing
cannot keep all curvature in the same turn direction. The diagnostic includes
the transition length, requested signed offset and calculated range of signed
offsets.

For each candidate, the function calculates its angle, peak factor and minimum
radius. It selects candidates in this sequence:

1. Largest `minimum_radius`.
2. Smallest `angle`.
3. Smallest absolute `shape_parameter`.

The result is a new Python `dict`. Its insertion order is
`shape_parameter`, `angle`, `peak_factor`, `minimum_radius`.

## B16 composition and recovery

The product selects fourteen functions together and validates 39 actual caller
routes. The routing record has schema version `9` and contract identity
`tracktemplate:phase7:platform-transition:1`.

The three public functions are direct bindings. The host-composition check also
keeps the identities of `platform_transition_angle`, `platform_line_offset` and
`_platform_parameter_grid`. It checks the direct call from
`platform_line_offset` to `platform_transition_displacement`. It checks all
four calls from `solve_platform_shape_parameter` and the nested call from
`squared_residual` to `platform_line_offset`.

After a selection error, the workflow puts all fourteen previous values back.
It removes a supplied value if that name was initially absent. The earlier
eleven-function contract, its 38 callers and all historical contract identities
stay unchanged.

## Evidence boundary

The [regression record](../benchmarks/2026-09-19-phase7-platform-transitions-regression.md)
owns the recorded calculation, caller, human-interface and cost evidence. The
supported scope is the earlier platform-transition calculation and the
existing B16 preparation and native-core callers in that record.

The result does not accept a solver change, performance optimisation, complete
platform or output migration, legacy removal, or performance result. Phase 7
stays Open at 0/4 with all four exits Pending. D-P6-008, all conditions to
compare results and remove legacy paths, and all recorded limitations stay in
full. Output stays private-development, and project status stays `unknown`.
