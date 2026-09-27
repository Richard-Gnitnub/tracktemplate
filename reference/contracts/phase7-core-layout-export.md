# Phase 7 Core-layout Export API

Status: **Draft Level 2 API for one B16 product route in Phase 7.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) gives authority for one bounded
Level 2 continuation. The project owner's instruction on 2026-09-27 selects
the smallest remaining product gap for Phase 7 Exit 1. It gives no exit
acceptance.

The `run_production_export` function has the same source in B14 and B15. That
source does not change. The `run_core_layout_export` function supplies the
same application operation from `tracktemplate.application` through
`tracktemplate.api`. The [JSON data](phase7-core-layout-export.json) give the
source identity, operation sequence and selected B16 route.

## Inputs and result

`run_core_layout_export` receives the document, prepared plan, configuration,
set identity and four configuration records. It can also receive an exporter
override. The compatibility boundary supplies these five host operations:

1. Execute the prepared tasks.
2. Build the manifest rows.
3. Write the manifest.
4. Build the details for a failed task.
5. Build the details for a skipped task.

The function first executes all prepared tasks. It then builds the manifest
rows. When the plan has a manifest path, it tries to write the manifest. An
ordinary Python exception from the manifest write becomes manifest failure
information. An exception from a different host operation continues to the
caller. A `BaseException` from any host operation also continues to the
caller. These rules keep the inherited B14/B15 behaviour.

The result gives the output directory and the counts of successful, failed and
skipped items. It also gives the sorted output formats, manifest state, task
results and details for each failed or skipped item. The function does not
change the supplied plan, configuration records or task results.

## B16 route and binding

The B16 `run_macro` caller keeps its `run_production_export` binding name. The
compatibility session binds that name to an adapter for
`run_core_layout_export`. The adapter supplies the five exact host operations.
The application module imports no FreeCAD or Qt module.

The product validates the application command, adapter identity, host-operation
identities and `run_macro` caller. It rejects an incomplete or mixed binding.
If setup validation fails, it restores the previous `run_production_export`
binding. The separate route record has schema `1` and identity
`tracktemplate:phase7:core-layout-export:1`.

This route does not change the accepted D-P7-004 calculation route. That route
keeps schema `16`, 25 selected functions and 40 caller identities.

## Scope and limits

This result moves only the B14/B15 application operation for the prepared
core-layout output plan. It changes no B14 or B15 source, task planning,
filename, output-format implementation, manifest schema, railway calculation,
FreeCAD object rule or accepted exporter failure model.

The [evidence record](../benchmarks/2026-09-27-phase7-core-layout-export-regression.md)
identifies the tests and their limits. D-P6-008 applies in full. All comparison,
adapter, caller, removal and legacy-retirement conditions stay in full. Phase 7
Exit 1 stays Pending until a separate owner decision. No performance result,
output status or release state has acceptance.
