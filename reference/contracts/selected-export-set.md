# Selected Full Output Set

Status: **API requirements under D-P9-014. [D-P9-015](../current/PHASE_EVIDENCE.md#phase-9b-exit-5-acceptance-panel) accepts Exit 9B-5 with its recorded limitations.**

## Purpose and authority

[D-P9-014](../current/PHASE_EVIDENCE.md#phase-9b-selected-export-policy-panel)
authorises a different new directory for each usual B16 selected operation.
One directory operation makes all selected output files available without
replacement of an existing path. CSV is optional and joins the same set.
The [architecture](../ARCHITECTURE.md#d-p9-014-selected-complete-output-set)
owns this canonical policy. The [JSON record](selected-export-set.json) identifies the
API and operating conditions.

These API requirements apply to `SelectedProductionExportDialog` through the usual
B16 compatibility component. The previous selected command and file adapter
stay available to compare results. Core Generate and its API requirements do not change.

## Selected files and operator decision

`prepare_selected_export_plan(records, config, set_id, scope, *, plan_export, output_directory=None)`
is in `tracktemplate.application.selected_export_set`.
It prepares the selected file paths but makes no files.
It supplies a copy of `config` to the inherited `plan_export` operation.
This `config` uses `overwrite_existing=False` and a new directory
named `Selected_Export_<uuidhex>` inside the directory that the operator selects.

The caller's `config` keeps the directory that the operator selects.
The returned `plan["output_directory"]` identifies the new directory.
Each task path and the optional CSV path identify a file inside it.

The `output_directory` input can preserve the new directory when the
GUI prepares the same selected files again.
The helper rejects a directory outside the directory that the operator selects.
It also rejects an existing path of any type.
It must not select a different name to avoid that error.
The rules for filenames, selected production data, task order and identities do not change.

`SelectedExportPolicy` connects the usual selected dialog to this behaviour.
Its `SelectedExportConfiguration` contains the data for that dialog.
If the full input data do not change, the new directory stays the same
from the preview through the operator decision, checks and file operations.
A change to `config`, `scope`, `records` or `set_id` makes the previous `plan` invalid.
Plain `dict` callers keep the previous route through `plan_export`.

Before the operation starts, the operator sees the new directory and all selected paths.
The operation compares all data that the operator accepted with the current data.
These data include `config`, `scope`, ordered tasks, selected production data,
skipped production data and warnings. The operation compares shapes through their BRep identity.

If the data change, the operator must accept the new data or the operation must stop.
A path list that does not change is not sufficient evidence that the full input data did not change.
If the new directory path becomes occupied, the operation stops with a diagnostic.

The usual controls prevent replacement of previous output.
The saved `config` keeps the operator's selected directory.
The checks before file creation continue to use only the formats that the selected
tasks use. They examine the final paths in the new directory.

## Application and file operations

`run_atomic_selected_production_export` keeps the previous selected command's
positional inputs and the operations that the caller supplies.
It makes a copy of the supplied `plan` and adds `extra_skipped` to `plan["skipped"]` in that copy.
The caller's inputs do not change.
The command uses `run_atomic_core_layout_export` for the full set of files.
It adds no file adapter or FreeCAD import to the application layer.

The existing `CoreLayoutExportSetFiles` supplies the file operations.
Its [API requirements](core-layout-export-set.md#command-and-file-operations) specify
`open`, `stage`, `validate`, `publish` and `cleanup`.
All selected files must pass validation before the final directory becomes
available through `renameat2(RENAME_NOREPLACE)`.
There is no route that writes final files one at a time.
An existing final path causes an error.
A host or filesystem without the specified directory operation also causes an error.

All previous output files, directories and symbolic links stay the same.

CSV stays optional. If the operator selects CSV, it is part of the same full set.
Its recorded paths identify final files in the new directory.
If the operator does not select CSV, neither `build_manifest_rows` nor `write_export_manifest` operates.
The CSV schema and file content requirements do not change.

## Result and errors

The command keeps the selected result fields and adds `publication_state`
and `results` from the shared operation.
`publication_state` is `not-published`, `published` or `uncertain`.
Before the full directory becomes available, an error reports zero completed
files, the operator's selected directory and no completed CSV path.

After the full directory becomes available, the result counts all completed
files. That count includes CSV only if the operator selected it.
The output directory, task results and CSV path identify the completed new directory.
A later error preserves those counts, paths and files and adds diagnostics.
The result dialog supplies `Open output folder` only for `publication_state="published"`.
That action uses the completed new directory from the result.

An uncertain result keeps zero completed files in the reported count and a visible diagnostic.
Cleanup must preserve completed or uncertain output.
The file adapter must have evidence of ownership before it removes temporary state.
Cleanup errors stay visible. `BaseException` interruptions in the specified failure model keep
their identities and cleanup diagnostics.

## Document preservation and previous routes

`SelectedExportBinding(atomic=True)` selects the new command and GUI behaviour
for usual B16 use. The default `atomic=False` keeps the previous component.
The compatibility component validates the command, file adapter, GUI behaviour and inherited callers.
The compatibility component must put the previous namespace and dialog operations back.

Default and override writers both use the same `CoreExportDocument`.
Its controls for temporary documents, source identity, closure, active document, selection
and preselection stay mandatory.
The selected operation must preserve the editable document and its history.
These API requirements add no persistence field or public API facade.

The frozen B14/B15 paths, previous selected command and file adapter, and Core Generate policy do not change.
The Phase 7 APIs used to compare results and prepare files also do not change.
D-P6-003 and D-P6-004 keep their Entry/Exit bounded scope and recovery authority.

## Validation and limitations

The [standalone test](../../tests/validate_selected_export_set.py) must examine
full output, optional CSV, selection that does not change,
and each specified failure boundary.
It must reject changes to the data that the operator accepted, collisions and unsafe cleanup.
The [qualified FreeCAD test](../../tests/freecad_validate_selected_export_set.py)
must compare DXF, SVG, STL, STEP and CSV with the
previous route under the existing comparison rules.
Checks on copied documents must examine object state, history, save and reopen.
The [real-GUI test](../../tools/freecad_bridge/run_selected_export_set_gui.py)
must examine the preview, operator decision, changed paths,
unavailable replacement, result and action for the completed directory.
The [current evidence](../current/PHASE_EVIDENCE.md#phase-9b-selected-export-policy-panel)
identifies the exact tested source, completed tests and limitations.

The operation is qualified only on Linux ext4 with an operator-controlled
output directory. The temporary and final directories are inside that same selected directory.
It gives no assurance that files stay available after a system interruption.
It adds no recovery after FreeCAD stops and starts again.
It gives no assurance for every filesystem, malicious writers or changes
that another process makes to the directory during the operation.

Phase 9A stays closed at 4/4 for its frozen reference-only bounded scope.
The [project plan](../PROJECT_PLAN.md#phase-status) owns current phase and exit status.
[D-P9-015](../current/PHASE_EVIDENCE.md#phase-9b-exit-5-acceptance-panel) owns the bounded Exit 9B-5 acceptance.
The 113-entry register, geometry, numerical limits and all 24 risk duties stay.

D-P6-008 stays Deferred — unmet. TERM-R04 stays open.
Output stays private-development. Project status stays `unknown`.
These API requirements accept no phase exit, production output, rights, physical fit,
manufacturing capability, performance or release result.
