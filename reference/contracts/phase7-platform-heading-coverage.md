# Phase 7 Platform Station Range API

Status: **Draft Level 2 instructions for one bounded Phase 7 product route.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) permits one bounded Level 2
continuation. The project owner's 2026-09-26 continuation authorises this
selected result. These instructions give no Phase 7 exit acceptance.

The B14 and B15 definitions of `alignment_progress_at_station`,
`station_for_progress_heading` and `platform_coverage_bounds` are equal.
The project keeps those definitions unchanged. The calculations now use
`tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-platform-heading-coverage.json) give the exact source
identities, values and selected product route.

## Inputs and results

An alignment is a track centreline with a specified travel direction.
Stations use mm along that centreline in its travel sequence. The first
supplied point is station `0.0` mm. The
[station-data instructions](phase7-station-mapping.md#station-data) own
that origin and direction. Direction angles use radians.
`alignment_progress_at_station(data, station, turn_sign)` reads the
interpolated direction angle at a station. It multiplies that angle by
`turn_sign` and returns `max(0.0, heading * turn_sign)`.

`station_for_progress_heading(data, target_progress, turn_sign)` uses
`core_start` and `core_end` from the station data. It gets the direction
progress at both ends and limits the requested
value to that range. It returns an end station when the requested value is
within `1.0e-11` of that end's progress. For other values, it makes exactly
64 interval steps. It returns the middle of the final interval. It keeps
the inherited order of reads, arithmetic and errors.

`platform_coverage_bounds(alignments, coverage, turn_sign)` takes selected
alignments, a value of `coverage` and `turn_sign`. The B16 product caller
supplies one or two alignments. The calculation rejects an empty selection.
For each alignment,
it gets station data and progress at `core_end`. It uses the largest entry
limit, the smallest exit limit and the smallest total progress. The four
accepted values of `coverage` select the result range. The
[JSON data](phase7-platform-heading-coverage.json) give their exact values
and results. The full-range value returns before the shared constant-range
check. All other values first use the inherited `1.0e-10` range check.
An unknown value is rejected after that check.

These calculations do not change the input or a FreeCAD document. They do
not keep a result for another call. They retain inherited diagnostic text,
non-finite input behaviour and the order of failed reads.

## B16 caller and recovery

The B16 `calculate_platform_boundaries` caller uses
`platform_coverage_bounds` and `station_for_progress_heading` before
`resolve_platform_longitudinal_bounds`. It then uses
`alignment_progress_at_station` for the returned start and finish stations,
before later platform geometry. The FreeCAD adapter retains station data
and point identities.
The selected interpolation adapter constructs the host `App.Vector` before
it reads the interpolated direction angle. A direction-only calculation
must retain that construction and error order.

The product selects 24 functions and validates 40 caller identities. It
checks the three adapters, their selected calculations and the four
inherited `coverage` values. Its
route record uses schema `15` and identity
`tracktemplate:phase7:platform-heading-coverage:1`. The binding rejects an
incomplete or mixed selection. After a setup error, it puts each previous
host value back. It removes a selected name only when the host did not have
that name before selection.

## Scope and limits

This result moves the platform direction and station-range calculations to
Core. It changes no B14 or B15 source. It adds no new placement rule or
output. It does not compare all platform geometry or export bytes. It does
not remove the legacy path. The selected B16 workflow keeps its existing
product status and conditions.

The [evidence record](../benchmarks/2026-09-26-phase7-platform-heading-coverage-regression.md)
identifies the bounded comparisons and their limits. D-P6-008, all
comparison requirements and all legacy-retirement conditions stay in full.
No Phase 7 exit, performance result, output status or release state is
accepted.
