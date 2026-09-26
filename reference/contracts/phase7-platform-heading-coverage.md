# Phase 7 Platform Station Range API

Status: **Draft Level 2 API for one product route in the bounded scope of Phase 7.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) gives authority for one Level 2
continuation in a bounded scope. The project owner's decision on 2026-09-26
authorises this selected result. These instructions give no Phase 7 exit acceptance.

The `alignment_progress_at_station`, `station_for_progress_heading` and
`platform_coverage_bounds` functions have the same source in B14 and B15.
The project keeps that source without a change. The functions use
`tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-platform-heading-coverage.json) give the source
identities, values and selected product route.

## Inputs and results

An alignment is a track centreline with a specified travel direction.
Stations use mm along that centreline in its travel sequence. The first
supplied point is station `0.0` mm. The
[station-data instructions](phase7-station-mapping.md#station-data) own
that starting point, direction and units. The JSON data specify
`station_unit` as `mm` and `direction_unit` as `rad`.

`alignment_progress_at_station(data, station, turn_sign)` reads the
`heading` value from `interpolate_alignment_station`, or from the selected adapter.
It multiplies that value by `turn_sign` and returns `max(0.0, heading * turn_sign)`.

`station_for_progress_heading(data, target_progress, turn_sign)` uses
`core_start` and `core_end` from the station data. It gets the results of
`alignment_progress_at_station` at the two ends. It keeps the selected
`target_progress` value in that range. It returns an end station when the
difference from that end's result is `1.0e-11` or less. For other values,
it does 64 interval steps. It returns the middle of the last interval.

The function keeps the B14/B15 sequence in which it reads inputs,
calculates values and gives errors.

`platform_coverage_bounds(alignments, coverage, turn_sign)` uses selected
alignments, a value of `coverage` and `turn_sign`. The B16 product caller
supplies one or two alignments. The function rejects an empty selection.
For each alignment, it gets station data and the result of
`alignment_progress_at_station` at `core_end`.

The function uses `max(entry_limits)`, `min(exit_limits)` and `min(totals)`.
The four accepted values of `coverage` select the result range. The
[JSON data](phase7-platform-heading-coverage.json) give those values
and results. For `PLATFORM_CORE`, the function returns before the
`1.0e-10` range check. For all other values, the function first does that
range check. The function rejects an unknown value after that check.

These functions do not change the input or a FreeCAD document. They do
not keep a result for a subsequent operation. They keep the B14/B15 diagnostic text
and the sequence of errors when they read inputs. For `float('nan')`,
`float('inf')` and `float('-inf')` inputs, they keep the B14/B15 product behaviour.

## B16 caller and previous values

The B16 `calculate_platform_boundaries` caller uses
`platform_coverage_bounds` and `station_for_progress_heading` before
`resolve_platform_longitudinal_bounds`. It then uses
`alignment_progress_at_station` for the returned start and finish stations.
These operations occur before it calculates the subsequent platform shapes.
The FreeCAD adapter keeps station data and point identities.

The selected adapter for `interpolate_alignment_station` makes the
`App.Vector` before it reads `heading`. A function that uses only `heading`
must keep that sequence and its errors.

The product selects 24 functions and validates 40 caller identities. It
validates the three adapters, their selected functions and the four
B14/B15 values of `coverage`. Its route record uses schema `15` and identity
`tracktemplate:phase7:platform-heading-coverage:1`.

The product rejects a selection that is not full or that mixes routes.
After a setup error, it sets each FreeCAD name to its previous value. It removes a
selected name only when FreeCAD did not have that name before selection.

## Scope and limits

This result moves the functions for platform direction and station range to
Core. It changes no B14 or B15 source. It adds no new rule for platform position
or output. It does not compare all platform shapes, dimensions and positions, or export bytes.
It removes none of the paths that D-P7-001 keeps. The selected B16 workflow keeps its product
status and conditions.

The [evidence record](../benchmarks/2026-09-26-phase7-platform-heading-coverage-regression.md)
identifies the tests and their limits. D-P6-008 applies in full. D-P7-001 still gives this instruction: “Preserve all comparison and legacy-retirement conditions.” No Phase 7 exit,
performance result, output status or release state has acceptance.
