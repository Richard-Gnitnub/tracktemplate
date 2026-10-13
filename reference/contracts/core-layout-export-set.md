# Core Generate Complete Output Set

Status: **API requirements under D-P9-013 and D-P9-016. [D-P9-015](../current/PHASE_EVIDENCE.md#phase-9b-exit-5-acceptance-panel) accepts Exit 9B-5 with its recorded limitations.**

## Purpose and authority

[D-P9-013](../current/PHASE_EVIDENCE.md#phase-9b-core-export-policy-panel)
authorises a different new directory for each Core Generate export.
The full output set becomes available through one directory operation.
CSV is optional. The operation preserves all previous output.
The [architecture](../ARCHITECTURE.md#d-p9-013-core-generate-complete-output-set)
owns that policy. The [JSON record](core-layout-export-set.json) identifies
this API and its operating conditions.

The [previous staging API](core-layout-export-staging.md) and
[Phase 7 API](phase7-core-layout-export.md) stay available for their comparison
and regression tests. Their diagnostics for partial output keep their meanings.
The selected-export route and D-P6-003/D-P6-004 Entry/Exit route do not change.

## Plan and output paths

`prepare_core_export_plan(records, config, set_id, *, plan_export, dependency_manifest=False)` prepares
the Core Generate plan without file operations.
It makes a copy of `config` and supplies a new directory inside the selected directory to `plan_export`.
The new directory name is `Core_Export_<uuidhex>`.
The selected directory in the caller's `config` does not change.
The returned `plan["output_directory"]` identifies the new directory.
Task output paths and the optional CSV path identify files inside that directory.

The helper keeps the existing filenames and rules for `plan_export`.
The new directory prevents replacement of previous output that has the same filename.
The command does not change the supplied plan, task sequence or record identities.

Core Generate shows the new directory policy in its output controls.
The previous control that permits replacement of existing outputs does not apply to this route.
Preflight examines the new output paths.
The completed result identifies the new directory.
The operation that opens completed output uses the directory from the result.
These changed paths are deliberate D-P9-013 behaviour.

`CoreExportConfiguration` identifies the current Core dialog input.
It adds no field to the existing JSON schema.
The saved configuration keeps the selected directory and
`overwrite_existing=False`. Plain `dict` inputs keep the previous
planning and preflight behaviour for other callers.

## Command and file operations

`tracktemplate.api.run_atomic_core_layout_export` receives the same first
nine inputs as `run_core_layout_export`.
The B16 compatibility adapter supplies the operations for file output, CSV
and diagnostic reports. The usual modular route selects the new command.

The necessary `export_files_factory` input supplies
`tracktemplate.adapters.export.core_layout_set.CoreLayoutExportSetFiles`.
Its `__init__` operation does no file operations.
The application command controls the sequence through `open`, `stage`,
`validate`, `publish` and `cleanup`.
The adapter owns the file operations. The application command does not import
FreeCAD or the concrete file adapter.

`open(plan, parent)` validates the requested final directory and opens a
hidden temporary directory for this command invocation.
The final directory must be directly inside the selected directory.
The operation rejects duplicate file paths and paths outside that final directory.
An existing final directory, file or symbolic link causes an error.
The operation does not replace it or select a different final name without a diagnostic.

`stage(path, writer, *, manifest=False)` supplies a temporary path to each writer.
The command prepares all task files before the optional CSV.
When CSV is absent from the plan, the command does not use its row builder or writer.
CSV rows use the final directory paths, not the temporary paths.
The existing CSV schema stays the same.

`validate()` examines all files in the temporary directory.
Each requested file must have a byte size greater than zero.
For each file, `stat.S_ISREG` must give `True` and `st_nlink` must be 1.
Unexpected or missing files cause an error.
The existing format and geometry checks continue to apply.
This contract adds no numerical limit or production clearance.

`publish()` uses one Linux `renameat2(RENAME_NOREPLACE)` operation to make the
full directory visible at its final path.
There is no different route that writes files to final paths one at a time.
The adapter must reject an unsupported host or filesystem.
If the final path already exists, this operation must preserve it.

The implementation is qualified only for Linux ext4.
The temporary and final directories use the same selected directory.
The operation uses that directory through `parent_fd` and examines its identity.
These checks do not prevent a different process from changing the directory between a check and the operating-system operation. The output directory must stay under operator control.

## Result and errors

The result keeps the Phase 7 field names and adds `publication_state`.
Its values are `not-published`, `published` and `uncertain`.
The file adapter supplies `published`, `publication_state` and `output_directory`
as read-only state.

Before the full directory becomes available, an error gives zero
completed files. The result identifies the selected directory.
The result does not count temporary files or supply a completed CSV path.
Prior output files, directories and symbolic links stay unchanged.

After the full directory becomes available, `successful_files` counts every
completed file, including the dependency JSON on the usual Core route.
It counts CSV only when the operator requests it.
`output_directory`, task results and `manifest_path` identify final paths in that directory.
An error after this operation must preserve those counts, paths and files.
The result includes the additional diagnostic information.

If the operation cannot find if the full set became available,
`publication_state` is `uncertain` and the result gives a diagnostic.
Cleanup must not remove data if the ownership or final state is unknown.
It must not remove any completed output directory.
Cleanup errors stay visible in the result.
A `BaseException` at a tested interruption boundary keeps its identity and
includes cleanup diagnostics.

## Dependency manifest

[D-P9-016](../current/PHASE_EVIDENCE.md#phase-9b-core-dependency-manifest-panel)
adds the mandatory `Core_Dependency_Manifest.json` file to the usual Core Generate
route. The Core policy supplies `dependency_manifest=True` to the plan helper.
The plan identifies that file in `dependency_manifest_path`.
The helper's default keeps previous comparison callers unchanged.
The selected-export route does not include this additional member.

The usual Core compatibility adapter supplies `prepare_dependency_manifest`.
This optional command input has this API:
`prepare(doc, plan, config, set_id) -> build(artifacts)`.
`run_staged_core_layout_export()` calls it before `open` to validate and collect manifest input
data. A missing plan member or a missing builder causes an error when the
manifest is mandatory. No completed output becomes available after that error.
Other comparison callers can continue without this input and plan member.

The first supported bounded scope has one Settings object for the same set.
It has curved plain-line `TrackTemplateCompound` and `TrackCentreline` data.
The categories are `CuttingProfile`, `Solid` and `Engraving`.
The existing `route_id` field is empty. The stable `record_id` identity uses the `CURVE` token through
`production_record_identity()`.

These inputs must have `enabled` equal to `false`:
`straight_routes`, `platforms`, `formation_board`, `sectioning`,
`template_joints` and `assembly_labels`.
Special trackwork, chair packages, imported shapes and replacement sources
are not in the bounded scope.
The checks examine properties and identities, not a fixture name.

Each planned shape and the source shape that its identity selects must be
available and non-null. Their initial `Shape.Placement.toMatrix().A` values
must be equal. The check makes temporary copies of the two shapes.
It sets each copy's `Placement` to that copy's initial `Placement` value.
It then compares the `exportBrepToString()` bytes from one more copy of each.
The bytes must be equal.

This removes differences from the existing document assignment without a
numerical tolerance or a change to the source shape.
The check applies to a new Generate operation and shapes restored from a saved document.
It does not independently prove that the software made these shapes from the
stored inputs.

The operator gets a diagnostic if manifest input data do not agree or are
not in the supported bounded scope. The output controls show this restriction.
The completed Generate transaction and previous files stay available after
the software rejects these data.

The `canonical_model_sha256` value identifies a versioned copy of canonical
information and the production intent for the command invocation.
The input reader rejects missing, ambiguous, malformed and non-finite data
before a helper can supply a default.

The scalar inputs are `TransitionLength`, `CurveRadius`, `TotalTurnAngle` and
`MainTemplateWidth`. Lengths use mm. The angle uses degrees.
The copy includes ordered track data and the stored data for `straight_routes`,
`platforms`, `formation_board`, `sectioning`, `registration`, `template_joints`
and `assembly_labels`. It includes the set identity and export selections
for this command.

It excludes allocated output directories, timestamps, presets and derived
shapes. `ProductionRecordIndexJSON` supplies evidence that the data agree.
It does not supply `canonical_model_sha256`.
The command changes no stored schema or property.
The hash does not prove that the software made shape copies from those inputs.

The manifest input data identify the existing B15 source, installed modular
product source and the identities of FreeCAD and its exporters.
Source licence evidence and the output rights state are different data.
The source hashes identify installed files.
They do not prove the identity of Python code in memory or all files that FreeCAD uses.

The qualified proof uses a new process and checks source hashes before and
after the operation. The product needs no Git process, network access,
repository validator or local research file when it operates.

The seven applicable groups in the
[legacy lineage register](../lineage/phase1-other-snc-legacy-lineage.json)
keep their existing classifications and project statuses without a change.
The production-record group stays applicable when CSV is off.
These broad groups do not prove that each source item in these groups was an input.
The manifest does not identify an S1 package or a special-trackwork table as
an input to this bounded scope.

The Phase 9 export/provenance owner owns the checked data that the software
uses for those seven groups. The tests compare those data with the canonical
register. That owner must update the data when the canonical mapping changes.
That owner must remove these data when an accepted replacement owns this
bounded scope. These data are not a new rights-state register.

After the adapter writes task output and optional CSV to the temporary
directory, `artifact_inventory()` reads only the adapter's owned regular files.
It returns each output basename, format and SHA-256.
`stage_dependency_manifest(payload)` writes the JSON as one more planned member.
`stage(..., manifest=True)` continues to identify CSV only.
The JSON excludes its own hash.

Validation checks all planned members.
It checks the output hashes again before the output directory becomes available.
The result supplies `dependency_manifest_path` only for a plan with that member.
It supplies the output path after the output directory becomes available.
Before that operation, it supplies an empty string.
The summary distinguishes this JSON from optional CSV.

The directory operation, cleanup, uncertain state and errors after that
operation keep the same conditions as the other members.
The manifest uses schema 1, scope `legacy-b14-b15-output`, intended use
`private-development` and project status `unknown`.
Unresolved rights states stay unresolved.
Non-copyright reviews that were not performed stay `not-performed`.
`production_admission_enabled` stays `false`.

The existing repository validator supplies schema and status checks independently. It cannot prove full input coverage by itself.
Construction or validation of the manifest gives no positive rights claim for
output and no phase-exit acceptance.

## Editable model and retained routes

Core Generate completes its document transaction before file output starts.
An export error does not undo that completed Generate transaction.
The [isolated FreeCAD operation](core-layout-export-staging.md#isolated-objects-for-output)
continues to prepare each format in its own temporary `App.Document`.
Its identity and closure checks stay.
Its checks for the active document, selection and preselection also stay.
The new file policy does not weaken those completion conditions.

The new command has its own route identity.
The compatibility adapter examines the selected command, factory, host
operations and Core Generate caller.
The previous Phase 7 and staging APIs keep their own identities.
B14, B15, calculation routes and `SelectedProductionExportDialog` stay unchanged.

## Validation and limits

The [file test](../../tests/validate_core_export_atomic_files.py) and
[application test](../../tests/validate_core_export_atomic.py) examine complete
output and the specified error conditions.
The [FreeCAD test](../../tests/freecad_validate_core_export_atomic.py) compares
output and examines document preservation in the qualified host.
The [current evidence](../current/PHASE_EVIDENCE.md#phase-9b-core-export-policy-panel)
records the exact tested source, completed proofs and their limits.

Use this command for the bounded real-GUI proof:

```bash
tools/freecad_bridge/run-phase7-core-layout-export-workflow --route modular --atomic-set
```

The command uses actual Core Generate controls for CSV on and off, success
and the specified error cases. It examines the final output paths, summary,
`Open Folder` request, previous output and editable-document preservation.
The previous `--staging-barrier` proof and Phase 7 diagnostic route stay available.

The owner calls the policy “atomic whole-set publication”.
The policy applies only to the full directory that becomes available through one operation.
It gives no assurance that files stay available after a system interruption.
It gives no assurance that a later process can complete unfinished work.
It gives no assurance for every filesystem or for changes that another process makes to the directory during this operation.
It gives no assurance for raw GUI selection event history or malicious serializers.

D-P6-003 and D-P6-004 keep their existing Entry/Exit conditions.
The [project plan](../PROJECT_PLAN.md#phase-status) owns current phase and exit status.
[D-P9-015](../current/PHASE_EVIDENCE.md#phase-9b-exit-5-acceptance-panel) owns the bounded Exit 9B-5 acceptance.

Phase 9A stays closed at 4/4 for its frozen reference-only scope.
Geometry, the 113-entry register and accepted numerical limits stay unchanged.
Output stays private-development and project status stays `unknown`.
This change gives no acceptance for physical fit, manufacturing, rights,
production, performance or release.
