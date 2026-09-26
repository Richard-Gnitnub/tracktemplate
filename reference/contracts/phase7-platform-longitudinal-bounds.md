# Phase 7 Platform Position API

Status: **Level 2 instructions for one bounded Phase 7 product route.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) permits one bounded Level 2
continuation. The project owner's 2026-09-26 continuation authorises selection
and completion of one bounded result. This contract records the selected
result. These instructions give no Phase 7 exit acceptance.

The B14 and B15 definitions of `resolve_platform_longitudinal_bounds` are
equal. The project keeps those definitions unchanged. The calculation now
uses `tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-platform-longitudinal-bounds.json) give its exact source,
inputs, ordered result, errors and product route.

## Input and result

`resolve_platform_longitudinal_bounds(config, base_start, base_finish)`
takes a configuration record and two selected track stations. All length
values use mm. It reads `platform_length` and `centre_offset` from `config`.
It returns eight values in the inherited order: `start_station`,
`finish_station`, `centre_station`, `centre_offset`, `length`,
`available_length`, `start_inset` and `finish_inset`. It does not change an
input or a FreeCAD document, and it keeps no result for another call.

The function converts `base_start` and `base_finish` to float values first.
It rejects a difference less than or equal to the `1.0e-8` mm
geometry tolerance. It then reads and converts `platform_length`. It rejects a value
less than or equal to that tolerance. It reads and converts
`centre_offset` next. It uses this value to set the centre station relative
to the middle of the selected start and finish stations.

The function rejects a centre station more than `1.0e-8` mm outside those
stations. It then limits an accepted centre station to the selected start
and finish stations. The maximum centred length is twice the shorter distance from the
accepted centre station to one selected end. The function rejects a
requested length greater than that maximum plus the inherited `1.0e-8` mm
tolerance. The function calculates and limits the returned start and finish
stations.
It keeps the inherited sequence of reads, values and errors, including the
behaviour for non-finite numeric inputs. The [JSON data](phase7-platform-longitudinal-bounds.json)
keep the exact error strings and result key order.

## B16 caller and recovery

The B16 `calculate_platform_boundaries` caller invokes the selected
function after `station_for_progress_heading` sets its start and finish
stations. It uses the returned stations before
`alignment_progress_at_station` and the later geometry calculations.
Selection sets the inherited host name to the Core function.
No adapter or FreeCAD vector is necessary for this calculation. The host
keeps ownership of the FreeCAD workflow and document changes.

The product selects 21 functions together and validates 39 caller
identities. It checks the Core domain closure and the inherited value of
`GEOMETRY_TOLERANCE`. The route record uses schema `14` and identity
`tracktemplate:phase7:platform-longitudinal-bounds:1`. It rejects an
incomplete or mixed selection. After a setup error, selection puts each
previous host value back. It removes a selected name only when the host did
not have that name before selection.

## Scope and limits

This result moves one platform length and position calculation to Core.
It changes no B14 or B15 source. It does not change the other platform
geometry, stored state, production geometry or export. It does not remove
the legacy path. The selected B16 workflow keeps its existing product
status and conditions.

The [evidence record](../benchmarks/2026-09-26-phase7-platform-longitudinal-bounds-regression.md)
identifies the bounded comparison and its limits. The proof does not cover
all custom Python containers, all platform geometry or export bytes.
D-P6-008, the comparison requirements and all legacy-retirement conditions
stay in full. No Phase 7 exit, performance result, output status or release
state is accepted.
