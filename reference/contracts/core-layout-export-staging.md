# Core Export Files Before Final Output

Status: **Draft Level 2 development contract for the Core Generate export route.**

## Purpose and authority

The project owner authorised more Phase 9B work after integration of PR #161
on 2026-10-11. This change supplies part of the work for Exit 9B-5.
It prepares all output files in the plan before it writes a final file.
An error during this preparation changes no files at their final paths.

The [architecture](../ARCHITECTURE.md#6-export-adapter) gives this requirement:

> Commit the complete output set atomically or, for an explicitly accepted
> bounded protocol, complete it monotonically under that protocol's named
> invariants.

This change does not meet that complete requirement. An error while the
software writes final files can cause an incomplete output set. That finding
stays open for Exit 9B-5. This contract gives no acceptance to that behaviour.

The [Phase 7 API](phase7-core-layout-export.md) stays available for its frozen
comparison and diagnostic tests. The new operation supplies the usual Core
Generate route. The [JSON record](core-layout-export-staging.json) identifies
the two operations and the new route.

## Inputs and operation

`tracktemplate.api.run_staged_core_layout_export` receives the same nine
positional inputs as `run_core_layout_export`. The compatibility adapter
supplies `dispatch_export_task`, `build_manifest_rows`,
`write_export_manifest`, `failed_export_report` and `skipped_export_report`.
`dispatch_export_task` uses `dispatch_freecad_export`.
The usual Core Generate route supplies that operation through
`CoreExportDocument`. A supplied `exporter_override` replaces the operation
inside `CoreExportDocument` for a test.

The necessary `export_files_factory` input supplies
`tracktemplate.adapters.export.core_layout_files.CoreLayoutExportFiles`.
The compatibility adapter supplies and validates this input. The export
adapter does the work for temporary files, final writes and cleanup.
The application command controls their sequence and returns diagnostic information.

The call `CoreLayoutExportFiles()` does not operate on files.
Its result supplies `open`, `stage`, `validate`, `publish` and `cleanup`.

The operation keeps the supplied task identities, sequence and final paths.
It does not change the plan or configuration. The selected operation receives
the supplied task and a different temporary output path.
CSV rows contain the final paths. The selected formats, file names,
revision allocation and CSV schema stay the same.

Each final path must be in the selected output directory.
The operation rejects repeated final paths before it makes temporary files.

The operation first makes a temporary directory for this command invocation only.
It makes and examines each format file in the plan.
It then makes and examines the CSV file, if the plan includes one.
The file mode of each temporary file must give a `True` result from `stat.S_ISREG`.
Each temporary file must also have a byte size of more than zero.

The checks in `dispatch_freecad_export` continue to apply.
This change adds no format specification or numerical limit.

If an error occurs before the first final file write, no final file changes.
The result reports zero files written to their final paths.
The result does not count temporary files. The software reports tasks that it
did not complete and does not write a CSV with error results to the output directory.

Only after these operations are complete does the software write final files
in task sequence. If the configuration does not permit replacement, a file
at the final path causes an error. If replacement is permitted, the software
can replace only a file whose mode gives a `True` result from `stat.S_ISREG`.
The software rejects a symbolic link or a different file type.

If a final task write gives an error, the software stops more final writes.
It does not write the prepared CSV. A CSV from a previous operation stays
without a change.

Files written before this error stay in the output directory.
The result counts those files as completed output.
The software does not put the complete output set back to its initial state.

The software removes only temporary state from this command invocation with
an identity that it validates. A cleanup error stays in the diagnostic
information that the operation returns.
After cleanup, the operation uses `raise` for a `BaseException` that is not an `Exception`.
It does not replace that `BaseException`.
A cleanup error adds a note to that `BaseException`.
This rule does not change the accepted interruption conditions.

## Results and caller

The result keeps the Phase 7 field names. `results` keeps the supplied tasks
and gives the final write state for each task. `successful_files` counts only
files written to final paths. It includes CSV only after the final CSV write
completes.

`manifest_requested` comes from the plan.
`manifest_path` is empty unless the final CSV write completes.
`formats` contains only formats with completed final files.

`failed_files` counts each task without a completed final write and each
different operation or cleanup diagnostic. A task error does not also add a
different CSV error. Thus, the sum of these counts can differ from the number
of files in the plan. A cleanup error after output does not change the
reported number of completed files. The result identifies the two conditions.

The usual modular workflow selects the new application command and adapter
by their exact identities. Route validation examines the command, adapter,
host operations and `run_macro` caller identities.
An identity error puts the previous route back.
The calculation route and `SelectedProductionExportDialog` do not change.

Core Generate keeps its previous preflight, output checks and confirmation.
The document transaction completes before export starts. An export error
does not put the document back to its state before Core Generate.
`run_staged_core_layout_export` does not supply those GUI checks independently.

## Separate objects for export

After PR #162, the usual Core Generate route uses `CoreExportDocument` for
each task. The B16 launcher supplies this class through
`export_dispatcher_factory`. Its construction does not operate on the host.
The application command API and the Phase 7 comparison route stay unchanged.

`CoreExportDocument` calls `App.newDocument` with `hidden=True` and
`temp=True`. It examines the returned `App.Document` and its registered
identity before it supplies that object to `dispatch_freecad_export`.
The object must have `Temporary=True` and an empty `FileName`.
The task and its records stay unchanged.
The operation never supplies the editable `App.Document` to that function.
Objects of type `App::FeaturePython` keep the existing `Label` values in the
new `App.Document`. They contain no copied `Shape` or other source properties.
This lets FreeCAD apply its previous rules for duplicate `Label` values.
The operation changes no preference and supplies none of these objects for export.

Before the operation returns, it closes only the registered `App.Document`
that it created and whose identity it proves.
It checks the previous registered identities and active state.
In the GUI, it puts the previous selection and preselection back.
It checks object identities, selected subelements and picked coordinates.
This check covers all previous registered documents.
It does not prove the previous order of selection events between different objects.

An error in this work prevents final file writes.
An object with uncertain ownership stays open.
A close error gives diagnostic information.
If the owned object stays registered, the diagnostic identifies that object.
The software does not close or change a previous `App.Document` to recover.
Contradictory results from `App.ActiveDocument` and `App.activeDocument()`
cause rejection before it creates an object for export.

The original exception stays the same object.
Additional cleanup errors become exception notes.
The application includes those notes in its error report for an `Exception`.
A `BaseException` continues to propagate after cleanup.

The frozen `dispatch_freecad_export` still does not report some errors from
object removal or recompute. Its objects now belong to the separate
`App.Document` in this route. A successful close removes that entire object.
This change supplies no new guarantee for the Phase 7 comparison route,
selected export or arbitrary asynchronous interruption.
The complete output-set requirement for Exit 9B-5 stays unresolved.

## Validation and limits

The [standalone regression test](../../tests/validate_core_export_staging.py)
examines errors before and during final writes and compares completed output.
The [FreeCAD regression test](../../tests/freecad_validate_core_export_staging.py)
examines FreeCAD output operations and document preservation.
The GUI proof uses Core Generate and examines the result that the operator
sees and persistence.
The [current evidence](../current/PHASE_EVIDENCE.md) records completed results.

Use this command for that bounded GUI proof:

```bash
tools/freecad_bridge/run-phase7-core-layout-export-workflow --route modular --staging-barrier
```

Without `--staging-barrier`, the Phase 7 proof keeps its previous diagnostic
route. The product operation `load_modular_transition_workflow_session`
always selects the new operation.

The Phase 7 API, its diagnostic for incomplete output and B14/B15 do not change.
D-P6-003 and D-P6-004 continue to supply the conditions for their Entry/Exit pair.
This change starts no software outside FreeCAD and adds no recovery after
FreeCAD stops and starts again. It gives no assurance for file output after
a system interruption or authority to remove files from a previous operation.
This evidence applies only to the qualified host profile for Linux and FreeCAD.

D-P9-012 continues to apply. Phase 9B stays Open at 1/6, with five exits Pending.
This change does not change geometry, the 113-entry register or accepted numerical limits.
Output stays private-development and project status stays `unknown`.
This result gives no acceptance for physical fit, manufacturing, rights or production.
