# Phase 7 Platform Height API

Status: **Draft Level 2 API for one product route in the bounded scope of Phase 7.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) gives authority for one Level 2
continuation in a bounded scope. The project owner's instruction on 2026-09-27
authorises this selected result. It gives no Phase 7 exit acceptance.

The `calculate_platform_top_heights` function has the same source in B14 and
B15. That source does not change. The function uses
`tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-platform-top-heights.json) give the source identity, values
and selected product route.

## Inputs and result

`calculate_platform_top_heights(config, stations, platform_length)` returns
one platform height in mm for each supplied station. It first reads and
converts `config["platform_height"]`. It then reads
`config["body_output"]`.

When `body_output` is not `PLATFORM_SOLID`, the function returns a new list.
Each item has the selected platform height. In this branch, the function does
not read the entry or exit end inputs. It does not use `platform_length`.

When `body_output` is `PLATFORM_SOLID`, the function reads an entry length only when
`entry_end_style` is `PLATFORM_END_TAPERED`. It reads an exit length only when
`exit_end_style` is `PLATFORM_END_TAPERED`. For all other values of these two inputs, the
applicable length is `0.0`.

The function processes stations in their supplied sequence. It starts each
result at the selected platform height. It applies the entry calculation only
when the entry length is more than `GEOMETRY_TOLERANCE` and the station is less
than that length. It applies the exit calculation only when the exit length is
more than `GEOMETRY_TOLERANCE` and `platform_length - station` is less than that
length.

Each applicable calculation limits its fraction to the range from `0.0` to
`1.0`. When the entry and exit ranges overlap, the function uses the lower
calculated value. The final value is not less than `TEMPLATE_THICKNESS`.
The [JSON data](phase7-platform-top-heights.json) give the four exact constant
values.

The function keeps the B14/B15 sequence in which it reads inputs, calculates
values and gives errors. This includes non-finite values and inherited Python
exceptions. It does not change the input or a FreeCAD document. It does not
keep a result for a subsequent operation.

## B16 caller and route

The B16 `calculate_platform_boundaries` caller calculates relative stations
and the platform length. It then calls `apply_platform_plan_tapers` and
`calculate_platform_top_heights`. It calls the selected function before it
assembles the result record.

The selected route uses the Core function directly. It has no adapter for this
function. The product selects 25 functions and validates 40 caller identities.
Its route record uses schema `16` and identity
`tracktemplate:phase7:platform-top-heights:1`.

The product validates the exact selected function, its domain namespace and
the types and values of the four inherited constants. It rejects a selection
that is not full or that mixes routes. After a setup error, it sets each
FreeCAD name to its previous value. It removes a selected name only when
FreeCAD did not have that name before selection.

## Scope and limits

This result moves one platform height calculation to Core and selects it in
one B16 caller. It changes no B14 or B15 source. It adds no platform rule,
tolerance or diagnostic. It does not compare all platform shapes, dimensions,
positions or export bytes. It removes none of the paths that D-P7-001 keeps.

The [evidence record](../benchmarks/2026-09-27-phase7-platform-top-heights-regression.md)
identifies the tests and their limits. D-P6-008 applies in full. D-P7-001 still
gives this instruction: “Preserve all comparison and legacy-retirement
conditions.” No Phase 7 exit, performance result, output status or release
state has acceptance.
