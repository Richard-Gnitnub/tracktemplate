# Selected Complete Output Set

Status: **Development contract under D-P9-014. No Phase 9B exit acceptance.**

## Purpose and authority

[D-P9-014](../current/PHASE_EVIDENCE.md#phase-9b-selected-export-policy-panel)
authorises a different new directory for each usual B16 selected export.
One directory operation makes the full requested set available without
replacement of an existing path. CSV is optional and joins the same set.
The [architecture](../ARCHITECTURE.md#d-p9-014-selected-complete-output-set)
owns this policy. The [JSON record](selected-export-set.json) identifies the
API and operating conditions.

This contract applies to `SelectedProductionExportDialog` through the normal
B16 compatibility binding. The previous selected command and file adapter
stay available for comparison. Core Generate and its contract stay unchanged.

## Requested files and confirmation

`prepare_selected_export_plan(records, config, set_id, scope, *, plan_export, output_directory=None)`
is in `tracktemplate.application.selected_export_set`.
It prepares the requested files without file creation.
It supplies a copied configuration to the inherited `plan_export` operation.
The copied configuration uses `overwrite_existing=False` and a new directory
named `Selected_Export_<uuidhex>` inside the selected parent directory.

The caller's configuration keeps the selected parent directory.
The returned `plan["output_directory"]` identifies the new directory.
Each task path and the optional CSV path identify a file inside it.

The `output_directory` input can preserve the intended directory when the
GUI prepares the same requested files again.
The helper rejects a directory outside the selected parent and an existing
path of any type. It must not select a different name to avoid that error.
The member naming rules, selected scope, task order and record identities stay.

`SelectedExportPolicy` connects the usual selected dialog to this behaviour.
Its marked `SelectedExportConfiguration` carries the dialog's context.
An unchanged complete request keeps the same child directory through preview,
confirmation, preflight and execution.
A change to the configuration, scope, selected records or set identity
invalidates that request. Plain `dict` callers keep the previous planning route.

The confirmation identifies the intended directory and all requested paths.
The execution compares the complete confirmed data with the current data.
These data include the configuration, scope, ordered tasks, selected records,
skipped records and warnings. Shapes are compared through their BRep identity.

Changed data require renewed confirmation or stop the operation.
An unchanged path list alone does not establish an unchanged request.
If the intended child path becomes occupied, export stops with a diagnostic.

The usual controls disable replacement of previous output.
The saved configuration keeps the operator's parent-directory preference.
Preflight keeps the existing narrowing to the formats that the selected
tasks use. It examines the intended final paths.

## Application and file operations

`run_atomic_selected_production_export` keeps the previous selected command's
positional inputs and injected operations.
It copies the supplied `plan` and combines `extra_skipped` with `plan["skipped"]`.
The caller's inputs stay unchanged.
The command reuses `run_atomic_core_layout_export` for the full-set operation.
It adds no concrete file adapter or FreeCAD import to the application layer.

The existing `CoreLayoutExportSetFiles` supplies the file operations.
Its [contract](core-layout-export-set.md#command-and-file-operations) owns
`open`, `stage`, `validate`, `publish` and `cleanup`.
All requested members must pass validation before the final directory becomes
available through `renameat2(RENAME_NOREPLACE)`.
There is no route that writes final members one at a time.
Existing final paths, unsupported hosts and unsupported filesystems cause errors.
All previous output files, directories and symbolic links stay unchanged.

CSV stays optional. When requested, it is part of the same complete set.
Its recorded paths identify final members in the new directory.
When CSV is absent, neither the CSV row builder nor the CSV writer operates.
The CSV schema and member content requirements stay unchanged.

## Result and errors

The command keeps the selected result fields and adds `publication_state`
and `results` from the shared operation.
`publication_state` is `not-published`, `published` or `uncertain`.
Before the full directory becomes available, an error reports zero confirmed
completed files, the selected parent directory and no completed CSV path.

After the full directory becomes available, the result counts all completed
members. CSV contributes to that count only when requested.
The output directory, task results and CSV path identify the completed child.
A later error preserves those counts, paths and files and adds diagnostics.
The selected summary offers `Open output folder` only for a confirmed completed set.
That action uses the completed child directory from the result.

An uncertain result keeps zero confirmed completed files and a visible diagnostic.
Cleanup must preserve completed or uncertain output.
It has authority only over temporary state whose ownership is proved.
Cleanup errors stay visible. Supported `BaseException` interruptions keep
their identities and cleanup diagnostics.

## Document preservation and retained routes

`SelectedExportBinding(atomic=True)` selects the new command and GUI policy
for normal B16 use. The default `atomic=False` keeps the previous binding.
Composition validates the command, file adapter, policy and inherited callers.
Restoration must put back the previous namespace and dialog operations.

Default and override writers both use the unchanged `CoreExportDocument`.
Its temporary-document, source-identity, closure, active-document, selection
and preselection controls stay mandatory.
The selected operation must preserve the editable document and its history.
This contract adds no persistence field or public API facade.

The frozen B14/B15 paths, previous selected command and file adapter, Phase 7
comparison and staging APIs, and Core Generate policy stay unchanged.
D-P6-003 and D-P6-004 keep their Entry/Exit scope and recovery authority.

## Validation and limits

The [standalone test](../../tests/validate_selected_export_set.py) must exercise
complete output, optional CSV, unchanged
selection and each supported failure boundary.
It must reject changed confirmation data, collisions and unsafe cleanup.
The [qualified FreeCAD test](../../tests/freecad_validate_selected_export_set.py)
must compare DXF, SVG, STL, STEP and CSV with the
retained route under its existing permitted normalisations.
Copied-document checks must examine object state, history, save and reopen.
The [real-GUI test](../../tools/freecad_bridge/run_selected_export_set_gui.py)
must examine the preview, confirmation, changed paths,
unavailable replacement, result and completed-directory action.
The [current evidence](../current/PHASE_EVIDENCE.md#phase-9b-selected-export-policy-panel)
identifies the exact tested source, completed proofs and limitations.

The operation is qualified only on Linux ext4 with an operator-controlled
output directory. The temporary and final directories use that same parent.
It gives no assurance that files stay available after a system interruption.
It adds no recovery after FreeCAD stops and starts again.
It gives no assurance for every filesystem, malicious writers or changes
that another process makes to the directory during the operation.

Phase 9A stays closed at 4/4 for its frozen reference-only scope.
Phase 9B stays Open at 1/6 under D-P9-012, with five exits Pending.
The 113-entry register, geometry, numerical limits and all 24 risk duties stay.

D-P6-008 stays Deferred — unmet. TERM-R04 stays open.
Output stays private-development. Project status stays `unknown`.
This contract accepts no phase exit, production output, rights, physical fit,
manufacturing capability, performance or release result.
