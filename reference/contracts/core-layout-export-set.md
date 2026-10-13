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
The selected-export route does not request this additional member.

The usual Core compatibility adapter supplies `prepare_dependency_manifest`.
This optional command input has the signature
`prepare(doc, plan, config, set_id) -> build(artifacts)`.
The application calls it before `open` to validate and capture the inventory.
A missing plan member or a missing builder causes an error when this route
requires the manifest. No final output becomes available after that error.
Other comparison callers can continue to omit this input and plan member.

The initial supported scope has one same-set Settings object and curved
plain-line `TrackTemplateCompound` and `TrackCentreline` records.
The categories are `CuttingProfile`, `Solid` and `Engraving`.
The inherited `route_id` field is empty. The stable record identity uses the
`CURVE` token through the existing host identity function.

Enabled straight routes, platforms, formation, sectioning, joints and assembly
labels are outside the scope. Special trackwork, chair packages, imported
geometry and replacement sources are also outside it.
The checks examine actual properties and identities, not a fixture name.

Each planned shape and its bound source shape must be present and non-null.
The original placement matrices must match exactly.
The check compares temporary copies with their original placements.
It applies each original placement again to its copy before a final copy
and exact BRep comparison.

This removes differences from the inherited
document assignment without a numerical tolerance or a change to the source.
The check applies to fresh Generate and shapes restored from a saved document.
It does not independently prove regeneration from the stored inputs.

The operator gets a diagnostic for an unsupported or inconsistent inventory.
The output controls show this restriction. The completed Generate transaction
and previous files remain available after refusal.

The signature identifies a versioned snapshot of canonical inputs and the
actual invocation's production intent. The input reader rejects absent,
ambiguous, malformed and non-finite data before a helper can supply a default.

The scalar inputs are `TransitionLength`, `CurveRadius`, `TotalTurnAngle` and
`MainTemplateWidth`. Lengths use mm; the angle uses degrees.
The snapshot includes ordered track configuration and the stored configuration
for straight routes, platforms, formation, sectioning, registration, assembly
and labels. It includes the set identity and requested export selections.

It excludes allocated output directories, timestamps, presets and derived
geometry. `ProductionRecordIndexJSON` supplies coherence evidence, not the
canonical input signature. The command changes no stored schema or property.
A signature does not prove that copied geometry was generated from those inputs.

The inventory identifies the inherited B15 source, installed modular generator
source and actual host/exporter identities. It keeps source licence evidence
separate from output rights. The source fingerprint identifies installed files.
It does not attest to cached executing Python code or every host binary.
The qualified proof uses a fresh process and checks source hashes before and
after the operation. It requires no Git process, network access,
repository validator or local research file when the product operates.

The seven applicable groups in the
[legacy lineage register](../lineage/phase1-other-snc-legacy-lineage.json)
retain their exact classifications and project statuses.
The production-record group remains applicable when CSV is off.
These broad groups do not prove that every referenced upstream item was an input.
No S1 package or special-trackwork table is claimed as an input to this scope.

The Phase 9 export/provenance owner owns the checked runtime projection of
those seven groups. The tests bind it to the canonical register.
That owner must update the projection when the canonical mapping changes.
The projection must be retired when an accepted replacement owns this scope.
It is not a new rights register.

After task output and optional CSV are staged, `artifact_inventory()` reads
only the adapter's owned regular files. It returns each final basename,
format and SHA-256. `stage_dependency_manifest(payload)` writes the JSON as a
distinct planned member. `stage(..., manifest=True)` still identifies CSV only.
The JSON excludes its own hash. Final validation checks all planned members
and checks the artifact hashes again before publication.

The result supplies `dependency_manifest_path` only for a plan with that member.
It supplies the final path after confirmed publication and an empty string
before publication. The summary distinguishes this JSON from optional CSV.
Publication, cleanup, uncertain state and errors after publication keep the
same conditions as the other members.

The manifest uses schema 1, scope `legacy-b14-b15-output`, intended use
`private-development` and project status `unknown`.
Unresolved permissions remain unresolved. Non-copyright reviews that were
not performed remain `not-performed`. Production admission stays disabled.

The existing repository validator supplies independent schema and status
checks. It cannot establish complete input coverage by itself.
Successful construction or validation grants no output clearance or exit acceptance.

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
