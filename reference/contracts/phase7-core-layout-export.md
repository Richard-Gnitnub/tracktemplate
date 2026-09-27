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

`run_core_layout_export` receives `doc`, `plan`, `config`, `set_id`,
`platform_config`, `formation_config`, `registration_config` and
`template_assembly_config`. It can also receive `exporter_override`. The
compatibility adapter supplies these five operations:

1. `execute_export_tasks`.
2. `build_manifest_rows`.
3. `write_export_manifest`.
4. `failed_export_report`.
5. `skipped_export_report`.

The function first calls `execute_export_tasks`. It then calls
`build_manifest_rows`. When `plan.manifest_path` has a value, it tries to call
`write_export_manifest`. An `Exception` from `write_export_manifest` adds
manifest failure information to the result. An `Exception` from a different
supplied operation continues to the caller. A `BaseException` from a supplied
operation also continues to the caller.

These rules keep the B14/B15 behaviour.

The result gives the output directory and the counts of successful, failed and
skipped items. It also gives the sorted output formats, manifest state, task
results and details for each failed or skipped item. The function does not
change the supplied plan, configuration records or task results.

## B16 route and adapter

The B16 `run_macro` caller keeps its `run_production_export` name. The
compatibility session sets that name to an adapter for
`run_core_layout_export`. The adapter supplies the five exact operations. The
application module imports no FreeCAD or Qt module.

The product validates the application command, adapter identity, supplied
operation identities and `run_macro` caller. It rejects connections that are
incomplete or mixed. If this validation fails, it restores the previous value
of `run_production_export`. The separate route record has schema `1` and
identity `tracktemplate:phase7:core-layout-export:1`.

This route does not change the accepted D-P7-004 calculation route. That route
keeps schema `16`, 25 selected functions and 40 caller identities.

## Scope and limits

This result moves only the B14/B15 application operation for `plan`. The
[JSON data](phase7-core-layout-export.json) identify all changes that are
outside this scope.

The [evidence record](../benchmarks/2026-09-27-phase7-core-layout-export-regression.md)
identifies the tests and their limits. D-P6-008 applies in full. All comparison,
adapter, caller, removal and legacy-retirement conditions stay in full. Phase 7
Exit 1 stays Pending until a separate owner decision. No performance result,
output status or release state has acceptance.
