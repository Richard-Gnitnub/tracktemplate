# Phase 7 Connected Straight Route Validation API

Status: **Level 2 instructions for one bounded Phase 7 product route.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) permits one bounded Level 2
continuation. The project owner's 2026-09-26 continuation selects this
result. These instructions define the connected straight route validation
that runs before production starts. They accept no Phase 7 exit.

The B14 and B15 definitions of `validate_connected_straight_routes` are
equal. The project does not change either definition. The calculation now
uses `tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-connected-straight-validation.json) give its exact
identity, parameters, values and product route.

## Calculation and result

`validate_connected_straight_routes` takes `straight_routes` and
`curve_alignments` in that sequence. It returns `None` when the inputs pass.
It does not change an input or a FreeCAD document. It keeps no result for
another call. Distances and XY coordinates use mm. Headings use rad.

The function gets the number of curve alignments before it reads a straight
route. It reads each route's `connection_mode`. It does not read the route's
alignments when that value is `Independent datum`. For another value, it
copies the route's alignment list and checks that its track count equals the
curve track count.

For each connected track, the function copies four lists in this sequence:
straight points, curve points, straight headings and curve headings. It
rejects an incomplete point list before it reads a heading value. For
`Curve entrance`, it compares the last straight point with the first curve
point. For every other connected value, it compares the first straight
point with the last curve point. It calculates travel direction before it
checks the distance and heading difference at the join. The existing limits
are `1.0e-8` mm for travel direction, `1.0e-7` mm for join distance and
`1.0e-10` rad for heading difference.

The function keeps the B14/B15 order of reads, calculations and errors. It
also keeps the behaviour for values outside the three named modes. The
bounded tests compare the result, the diagnostic text, the input identities
and the input values with B14 and B15. They include one-track and
multiple-track inputs, boundary values and native read failures.

These are the exact retained diagnostics:

- `Connected straight route '{}' produced {} track(s), but the curve contains {} track(s). No existing generated objects have been removed.`
- `Connected straight route '{}' contains incomplete Track {} geometry. No existing generated objects have been removed.`
- `Connected straight route '{}' failed its Track {} endpoint or tangent validation. No existing generated objects have been removed.`

The function has no FreeCAD or Qt dependency. It uses the domain's existing
`_dot_xy` and `_straight_heading_delta` functions. The task adds no new
geometry rule or tolerance.

## B16 caller and recovery

The B16 `run_macro` caller keeps its position after
`build_straight_routes` and before
`prepare_straight_routes_production`. Its selected
`validate_connected_straight_routes` value is a read-only compatibility
adapter. The adapter reads the X and Y components of existing FreeCAD
`App.Vector` points through neutral views. It makes no new native vector.
The domain calculation reads only neutral values from the views. It imports
no FreeCAD or adapter module.

The product selects nineteen functions together and validates 39 caller
identities. It validates the selected calculation, its private dependencies,
the adapter and the `run_macro` call. The routing record uses schema `12`
and identity `tracktemplate:phase7:connected-straight-validation:1`. After a
setup error, the product replaces each selected host value with its previous value. It removes a
new value only when the host did not have that name before selection.

## Scope and limits

This result moves one pre-production safety check to Core. It does not
change the B14 or B15 sources, host configuration, stable identities,
stored state, production geometry or export. It does not remove the legacy
path. The compatibility adapter remains until the complete caller and
removal gates have accepted evidence.

The [evidence record](../benchmarks/2026-09-26-phase7-connected-straight-validation-regression.md)
identifies the bounded comparison and the resource observations. The proof
does not cover all possible custom Python containers or later production
results. It does not compare physical-platform results, sectioning results
or export bytes. D-P6-008 and all other comparison and legacy-retirement
conditions stay in full. No Phase 7 exit, product performance, output status
or release state is accepted.
