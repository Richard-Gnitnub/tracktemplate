# Core Export Files Before Final Output

Status: **Draft Level 2 development contract for the Core Generate export route.**

## Purpose and authority

The project owner authorised Phase 9B continuation after integration of PR #161
on 2026-10-11. This change addresses part of Exit 9B-5. It prepares all requested
output files before it writes a final file. An exporter or CSV error during
this first operation leaves existing final files unchanged.

The [architecture](../ARCHITECTURE.md#6-export-adapter) requires an atomic
complete output set or an explicitly accepted bounded protocol.
This change does not meet that complete requirement. A failure while the
software writes final files can still leave part of a set. That finding stays
open under Exit 9B-5. This contract gives no acceptance to that behaviour.

The [Phase 7 API](phase7-core-layout-export.md) stays available for its frozen
comparison and diagnostic tests. The new operation supplies the normal Core
Generate route. The [JSON record](core-layout-export-staging.json) identifies
both operations and the new route.

## Inputs and operation

`tracktemplate.api.run_staged_core_layout_export` receives the same nine
positional inputs as `run_core_layout_export`. The compatibility adapter
supplies `dispatch_export_task`, `build_manifest_rows`,
`write_export_manifest`, `failed_export_report` and `skipped_export_report`.
`dispatch_export_task` uses the inherited `dispatch_freecad_export` function.
An explicit `exporter_override` replaces that operation for a test.

The required `export_files_factory` input supplies
`tracktemplate.adapters.export.core_layout_files.CoreLayoutExportFiles`.
The compatibility adapter supplies and checks this factory. The export adapter
owns temporary files, final writes and cleanup. The application controls their
order and the returned diagnostic information. The factory constructor does
not operate on files. Its object provides `open`, `stage`, `validate`,
`publish` and `cleanup`.

The operation keeps the supplied task identities, order and final paths.
It does not change the plan or configuration. Exporters receive the original
task and a separate temporary output path. CSV rows contain the final paths.
The selected formats, file names, revision allocation and CSV schema stay the
same.

Every final path must be in the selected output directory. Duplicate final
paths cause failure before the software creates temporary files.

The operation first creates a private temporary directory for this invocation.
It makes and checks every requested format file. It then makes and checks the
CSV file, if the plan requests one. Each temporary output must be a nonempty
regular file. The existing exporter checks continue to apply. This change
adds no format specification or numerical limit.

If an operation fails before the first final file write, no final file changes.
The result reports zero successful files. Temporary files do not count as
successful output. The software reports tasks that it did not complete and
does not write a failure CSV to the final destination.

Only after these operations succeed does the software write final files in
task order. If overwrite is disabled, an existing final path causes failure.
If overwrite is enabled, only a regular final file can be replaced.
The software rejects a symbolic link or non-regular destination.

If a final task write fails, the software stops further final writes.
It does not write the prepared CSV.
An existing CSV stays unchanged. Files already written remain in place and
count as successful output. There is no complete-set rollback.

The software removes only temporary state with confirmed identity from this invocation.
A cleanup failure remains in the returned diagnostic information.
An exception derived directly from `BaseException` continues to the caller
after cleanup. A cleanup failure adds a note to that exception.
This rule does not change the accepted exporter interruption model.

## Results and caller

The result keeps the Phase 7 field names. `results` keeps the original tasks
and gives the final write state for each task. `successful_files` counts only
final files, including CSV when that write succeeds. `manifest_requested`
comes from the plan. `manifest_path` is empty unless the final CSV write
succeeds. `formats` contains only formats with successful final files.

`failed_files` counts each task without a successful final write and each
separate operation or cleanup diagnostic. A task error does not also add a
separate CSV error. Thus, the successful and failed counts need not sum to the
requested file count. A cleanup error after successful output does not
turn written files into unsuccessful files. The result identifies both states.

The normal modular workflow selects the new application operation and adapter
explicitly. Route validation checks the command, adapter, host operations and
`run_macro` caller identities. A binding failure restores the previous route.
The calculation route and selected-export dialog stay unchanged.

Core Generate keeps its existing preflight, output checks and confirmation.
The document transaction completes before export starts. An export failure does not
undo the valid generated model. The lower-level export operation does not
supply those GUI checks independently.

The inherited dispatcher still creates temporary objects in that document.
Its existing cleanup can hide object-removal or recompute failures.
The present host checks prove preservation for the tested successful and
exporter-failure cases. They do not qualify those hidden cleanup failures.
That duty stays open under Exit 9B-5.

## Validation and limits

The [standalone regression](../../tests/validate_core_export_staging.py)
checks temporary-file failures, final-file failures and success comparisons.
The [FreeCAD regression](../../tests/freecad_validate_core_export_staging.py)
checks real exporters and document preservation. The actual GUI proof uses
Core Generate and checks its visible result and persistence.
The [current evidence](../current/PHASE_EVIDENCE.md) records completed results.

Run that bounded GUI proof with:

```bash
tools/freecad_bridge/run-phase7-core-layout-export-workflow --route modular --staging-barrier
```

Without `--staging-barrier`, the Phase 7 proof keeps its earlier diagnostic
route. The normal product loader always selects the new operation.

The old Phase 7 API, its partial-output diagnostic and B14/B15 remain unchanged.
D-P6-003 and D-P6-004 continue to govern their separate Entry/Exit pair.
This change adds no helper process, restart recovery, durability guarantee or
new authority to remove existing files.
Host evidence applies only to the qualified Linux and FreeCAD profile.

D-P9-012 stays in force. Phase 9B stays Open at 1/6, with five exits Pending.
Geometry, the 113-entry register and accepted numerical limits stay unchanged.
Output stays private-development and project status stays `unknown`.
This result gives no acceptance for physical fit, manufacturing, rights or production.
