# TrackTemplate validation-selection checklist

Apply only the sections relevant to the complete change.

## Scope and authority

- The complete relevant diff has been inspected.
- The current phase, open gates and owning evidence document have been
  identified.
- The affected architectural, railway and FreeCAD/host boundaries are explicit.
- The change is separated from unrelated cleanup, optimisation or behaviour
  changes.

## Evidence-layer selection

Consider each layer and record why it applies or does not apply:

- source parsing and structural controls;
- pure or analytical railway behaviour;
- dependency direction and standalone import;
- qualified FreeCAD document behaviour;
- real-GUI presentation, selection and operator workflow;
- persistence, migration, save/reopen, Undo/Redo and stable identity;
- transaction, rollback, cleanup and recovery;
- exact geometry and production output;
- exporter naming, ordering, manifests and overwrite handling;
- performance and resource measurement;
- provenance, licensing, package admission and output status;
- documentation links, canonical ownership and validator-controlled wording.

## Change signals

Require the corresponding evidence when a change affects:

- units, coordinate frames, geometry, sampling or tolerances;
- topology, timbering, chairs, stable identities or deterministic ordering;
- public APIs, schemas, stored properties or migration behaviour;
- FreeCAD objects, transactions, recompute, visibility or selection;
- caches, signatures, invalidation or reuse;
- exact solids, meshes, SVG, DXF, STEP, STL or manifests;
- timings, metadata volume, repeated calculations or deferred work;
- source data, external evidence, chair definitions or output-clearance
  classification;
- frozen or append-only records, live status or controlled terminology.

## Evidence integrity

- The proof uses the highest reliable boundary that can observe the changed
  behaviour; substitutes, fixtures or mocks begin only beyond that boundary.
- Tests assert railway outcomes, document state, persisted state, exported
  content or visible failure contracts rather than internal call sequences.
- Where practical, the focused regression proof was observed failing against
  the pre-change behaviour and passing after the change.
- Pre-existing failures are distinguished from failures introduced by the
  present change.
- Focused tests prove observable behaviour rather than only implementation shape.
- Existing regression and oracle changes have evidence and authority.
- Required success sentinels were observed.
- Standalone, headless FreeCAD and real-GUI evidence remain distinct.
- Performance comparisons use equivalent states and retain correctness checks.
- Operator-owned documents were not used as the only mutable fixture.
- Unavailable checks and residual risk are stated.

## Reporting

- Every executed command and environment is recorded.
- Failures, skipped checks and unavailable tools are visible.
- Claims are bounded to what the evidence actually proves.
- Phase, release, migration, package and project-clearance decisions are not
  inferred from validation results.
