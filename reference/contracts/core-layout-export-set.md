# Core Generate Complete Output Set

Status: **Development contract under D-P9-013. No Phase 9B exit acceptance.**

## Purpose and authority

[D-P9-013](../current/PHASE_EVIDENCE.md#phase-9b-core-export-policy-panel)
authorises a different unused directory for each Core Generate export.
The complete output set becomes visible through one directory operation.
CSV is optional. The operation preserves all previous output.
The [architecture](../ARCHITECTURE.md#d-p9-013-core-generate-complete-output-set)
owns that policy. The [JSON record](core-layout-export-set.json) identifies
this API and its operating conditions.

The [previous staging API](core-layout-export-staging.md) and
[Phase 7 API](phase7-core-layout-export.md) stay available for their comparison
and regression tests. Their partial-output diagnostics keep their meanings.
The selected-export route and D-P6-003/D-P6-004 Entry/Exit route do not change.

## Plan and output paths

`prepare_core_export_plan(records, config, set_id, *, plan_export)` prepares
the Core Generate plan without file operations.
It makes a copy of `config` and supplies a new child directory to the inherited planner.
The child name has the form `Core_Export_<uuidhex>`.
The selected parent directory in the caller's `config` does not change.
The returned `plan["output_directory"]` identifies the child directory.
Task output paths and the optional CSV path identify files inside that directory.

The helper keeps the existing member filenames and task-planning rules.
The new directory prevents a previous member filename from selecting an
output that the operation can replace.
The command does not change the supplied plan, task sequence or record identities.

Core Generate shows the new directory policy in its output controls.
The previous choice to replace existing outputs does not apply to this route.
Preflight examines the new output paths.
The completed result identifies the new directory.
The operation that opens completed output uses the directory from the result.
These changed paths are deliberate D-P9-013 behaviour.

`CoreExportConfiguration` identifies the live Core dialog input.
It adds no field to the stored JSON schema.
Stored configuration keeps the selected parent directory and
`overwrite_existing=False`. Plain configuration dictionaries keep the previous
planning and preflight behaviour for other callers.

## Command and file operations

`tracktemplate.api.run_atomic_core_layout_export` receives the same first
nine inputs as `run_core_layout_export`.
The B16 compatibility adapter supplies the operations for file output, CSV
and diagnostic reports. The usual modular route selects the new command.

The necessary `export_files_factory` input supplies
`tracktemplate.adapters.export.core_layout_set.CoreLayoutExportSetFiles`.
Its constructor performs no file operations.
The application command controls the sequence through `open`, `stage`,
`validate`, `publish` and `cleanup`.
The adapter owns the file operations. The application command does not import
FreeCAD or the concrete file adapter.

`open(plan, parent)` validates the requested final directory and opens a
hidden temporary directory for this invocation.
The final directory must be a direct child of the selected parent directory.
The operation rejects duplicate member paths and paths outside that child.
An existing final directory, file or symbolic link causes an error.
The operation does not replace it or select a different final name silently.

`stage(path, writer, *, manifest=False)` supplies a temporary path to each writer.
The command prepares all task files before the optional CSV.
When CSV is absent from the plan, the command does not call its row builder or writer.
CSV rows use the final child-directory paths, not the temporary paths.
The existing CSV schema stays the same.

`validate()` examines the complete temporary inventory.
Every requested member must be a regular file with a byte size greater than zero.
Its `st_nlink` value must be 1.
Unexpected or missing members cause an error.
The existing format and geometry checks continue to apply.
This contract adds no numerical limit or production clearance.

`publish()` uses one Linux `renameat2(RENAME_NOREPLACE)` operation to make the
complete directory visible at its final path.
There is no fallback that writes members to final paths one at a time.
The adapter must reject an unsupported host or filesystem.
A collision at this operation must preserve the existing path.

The implementation is qualified only for Linux ext4.
The temporary and final directories use the same selected parent directory.
The operation uses that directory through a descriptor and checks its identity.
These checks do not protect against a hostile change between a check and the
operating-system operation. The output directory must remain under operator control.

## Result and errors

The result keeps the Phase 7 field names and adds `publication_state`.
Its values are `not-published`, `published` and `uncertain`.
The file adapter exposes `published`, `publication_state` and `output_directory`
as read-only state.

Before the complete directory becomes visible, an error gives zero confirmed
completed files. The result identifies the selected parent directory.
The result does not count temporary files or supply a completed CSV path.
Prior output files, directories and symbolic links stay unchanged.

After the complete directory becomes visible, `successful_files` counts every
completed member, including CSV only when requested.
`output_directory`, task results and `manifest_path` identify final paths in that directory.
An error after this event must preserve those counts, paths and files.
The result includes the additional diagnostic information.

If the operation cannot determine whether the complete set became visible,
`publication_state` is `uncertain` and the result gives a diagnostic.
Cleanup must not remove data with uncertain ownership or uncertain final state.
It must not remove any completed output directory.
Cleanup errors stay visible in the result.
A `BaseException` at a tested interruption boundary keeps its identity and
includes cleanup diagnostics.

## Editable model and retained routes

Core Generate completes its document transaction before file output begins.
An export error does not reverse that completed Generate transaction.
The [isolated FreeCAD operation](core-layout-export-staging.md#isolated-objects-for-output)
continues to prepare each format in its own temporary `App.Document`.
Its identity and closure checks stay.
Its checks for the active document, selection and preselection also stay.
The new file policy does not weaken those completion conditions.

The new command has its own route identity.
The compatibility adapter verifies the selected command, factory, host
operations and Core Generate caller.
The previous Phase 7 and staging APIs keep their own identities.
B14, B15, calculation routes and `SelectedProductionExportDialog` stay unchanged.

## Validation and limits

The [file test](../../tests/validate_core_export_atomic_files.py) and
[application test](../../tests/validate_core_export_atomic.py) examine complete
output and the named error conditions.
The [FreeCAD test](../../tests/freecad_validate_core_export_atomic.py) compares
output and examines document preservation in the qualified host.
The [current evidence](../current/PHASE_EVIDENCE.md#phase-9b-core-export-policy-panel)
records the exact tested source, completed proofs and their limits.

Use this command for the bounded real-GUI proof:

```bash
tools/freecad_bridge/run-phase7-core-layout-export-workflow --route modular --atomic-set
```

The command uses actual Core Generate controls for CSV on and off, success
and the named error cases. It examines the final output paths, summary,
`Open Folder` request, previous output and editable-document preservation.
The previous `--staging-barrier` proof and Phase 7 diagnostic route stay available.

The owner calls the policy “atomic whole-set publication”.
It concerns the visibility of a complete directory through one operation.
It gives no assurance that files survive a system interruption or that a
later process can recover unfinished work.
It gives no assurance for every filesystem, hostile concurrent directory changes,
raw GUI selection event history or malicious serializers.

D-P6-003 and D-P6-004 keep their existing Entry/Exit conditions.
D-P9-012 remains the authority for the one accepted Phase 9B exit.
Phase 9B stays Open at 1/6, with five exits Pending.

Phase 9A stays closed at 4/4 for its frozen reference-only scope.
Geometry, the 113-entry register and accepted numerical limits stay unchanged.
Output stays private-development and project status stays `unknown`.
This change gives no acceptance for physical fit, manufacturing, rights,
production, performance or release.
