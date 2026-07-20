# Track Template Macro Architecture

Status: accepted strategic direction; implementation is intentionally phased.

The authoritative phase sequence and release-candidate gates are maintained in [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Why the architecture is changing

The project grew successfully by adding validated capability in stages: parametric curves and easements, station/straight and multi-track features, turnouts, crossovers, timbering, chair analysis, integration, and production export. That iterative approach proved the railway calculations, but it also concentrated domain logic, FreeCAD document management, display construction, exact shape generation, persistence, and export in one increasingly resource-intensive macro.

The next phase is architectural rather than another feature layer. It must reduce interactive cost without sacrificing the accepted railway results.

## Accepted direction

The system will separate the authoritative parametric model from its interactive display and its production geometry.

```text
Parametric railway model + versioned chair definitions
        |
        +--> analytical results and validation findings
        |
        +--> lightweight derived 2D preview for editing
        |
        `--> transient exact geometry for validation/export
                    |
                    `--> SVG / DXF / STL / STEP / manifests
```

The live document should remain lightweight. Exact OpenCASCADE `Part` shapes, solids, Boolean operations, and dense per-element FreeCAD objects should not be created during routine editing when a derived 2D representation can provide the required feedback.

Exact geometry is permitted at an explicit **Validate** or **Export** boundary. Validation must not be postponed until after a production file has already been written.

## Architectural principles

1. **Railway semantics are authoritative.** Parameters, stable identities, topology, alignments, timber decisions, chair assignments, and production metadata are the source of truth.
2. **The viewport is a projection.** SVG, Coin scene-graph nodes, or another lightweight renderer display the model; they do not replace it.
3. **Users edit intent, not generated paths.** Editing acts on parameters or defined semantic handles. Arbitrary edits to a rendered SVG path are not accepted unless a deterministic round trip back to the parametric model is designed and validated.
4. **Exact geometry is demand-driven.** Build only the geometry required for the requested validation or output format, and dispose of transient geometry after use.
5. **Persistence is compact and versioned.** Store canonical parameters and results, not redundant derived geometry. Schema changes require an explicit migration path.
6. **Derived state is fingerprinted.** Preview, analysis, validation, and export caches must be tied to complete input signatures. Stale speed is a correctness failure.
7. **Export remains deterministic and transactional.** Staging, preflight, manifest generation, overwrite handling, commit, and rollback remain production invariants.
8. **Migration is incremental.** The existing implementation remains the comparison path until each replacement proves output equivalence and a measured resource improvement.
9. **Production chairs remain procedural.** Full-size prototype parameters and
   explicit constituent parts are authoritative. A scan, mesh, CAD body, or
   generated FreeCAD shape is reference evidence or derived output, never a
   substitute for an accepted parametric chair definition.

## Target layers

### 1. Domain model

The domain layer represents:

- routes, tracks, stations and alignments;
- curves, easements, straights and spacing transitions;
- turnouts, crossover relationships and topology;
- rails, timbers, chair assignments, supports and stable identities;
- versioned chair-family definitions, constituent components, rail interfaces,
  manufacturing variants and source provenance;
- configuration, tolerances and production intent.

It should use Python data and deterministic calculations without depending on a FreeCAD document or GUI. FreeCAD vectors may be adapted at the boundary rather than used as persistent domain state.

Conceptual operations are:

```text
build_model(configuration) -> DomainModel
analyse(model) -> AnalysisResult
build_preview(model, analysis) -> PreviewScene
validate_exact(model, analysis, request) -> ValidationResult
export(model, validation, request) -> ExportManifest
```

These are contracts, not prescribed function names.

### 2. Application and workflow layer

This layer coordinates commands and state transitions:

- apply an edit to the domain model;
- identify which analyses and views became dirty;
- reuse only signature-compatible results;
- request preview regeneration;
- run explicit exact validation;
- prepare and execute transactional export.

It owns workflow state but not FreeCAD rendering details.

### 3. FreeCAD persistence adapter

The FreeCAD document should contain a small number of logical objects with typed properties or versioned payloads. `App::FeaturePython` is a candidate for parametric document objects where its lifecycle and migration behaviour are proven.

Avoid one persistent document object per rail segment, timber, chair, marker, or export fragment. Object count should scale with logical assemblies and display layers rather than raw primitive count.

### 4. Lightweight presentation adapter

The normal editing view is derived 2D geometry grouped into a few semantic/style layers, for example:

- track centrelines and rails;
- timber outlines and centres;
- chair symbols;
- construction datums and diagnostics;
- selection and edit handles.

A custom FreeCAD ViewProvider backed by Coin line/face primitives is the leading option because it separates the editable document object from its GUI representation. An embedded SVG-based view remains a prototype option, not an accepted storage model.

The renderer must provide a mapping from a selected visual element back to a stable domain identity. View-only coordinates must never become an independent source of railway truth.

### 5. Exact geometry adapter

This adapter converts selected domain records into the minimum `Part` geometry needed for:

- exact fit or topology validation;
- planar production profiles;
- 3D solids and meshes;
- FreeCAD exporters that require `Part::Feature` objects.

Prefer a temporary or isolated document and remove generated objects after validation/export. Persistent production shapes are created only when the user explicitly requests materialisation as a retained result.

Direct SVG generation from canonical 2D records may bypass `Part` construction when scale, bounds, categories, identifiers, and output equivalence can be validated. Formats that require BRep or mesh geometry still use the exact adapter.

### 6. Export adapter

The export layer keeps the existing safety model:

1. Resolve the requested scope and formats.
2. Confirm analysis and exact-validation signatures are current.
3. Generate only target-specific transient geometry.
4. Write into a hidden staging location.
5. Validate bounds, scale, topology and manifest entries.
6. Commit the complete output set atomically.
7. Roll back failures and clean transient geometry.

## Chair-definition and procedural-geometry contract

Production chair geometry will follow the procedural construction model found
in the accepted Templot5 revision 556b source evidence. This is a method and
output contract, not a requirement to reproduce Pascal control flow or emit
Templot's low-level DXF `3DFACE` records internally.

The canonical chair definition must:

- retain full-size prototype dimensions with explicit source units and
  deterministic conversion; the internal storage unit and exact-value strategy
  are schema decisions, not assumptions to hide in geometry code;
- describe named constituent parts as applicable to the chair family, including
  base/plinth, rail seat, inner and outer jaws, ribs, fillets, key, fastenings,
  and loose-jaw or plug interfaces;
- describe procedural profiles, cross-sections, radii, slopes, relationships,
  symmetry and placement datums rather than one opaque final mesh;
- separate prototype geometry and rail-fit intent from model scale, printer or
  material compensation, clearances and other manufacturing variants;
- carry a version, stable component identities, supported rail-interface data,
  provenance, source-file hashes, assumptions, tolerances and validation state;
  and
- be serialisable and usable by domain tests without importing FreeCAD or Qt.

The exact adapter consumes an accepted chair definition, constructs its named
components, and assembles reusable prototypes by deterministic transforms at
calculated rail/timber positions. FreeCAD/OpenCASCADE B-reps and solids are the
preferred exact representation. They may improve on Templot's output mechanism,
but not replace its parameterised component model with hand-drawn bodies,
rectangular envelopes, or an imported mesh. Tessellation is an export concern
for formats such as STL, not canonical chair state.

The current B15 S1/S1J five-box body is retained only as accepted legacy
behaviour and gap evidence. It is not the production chair-definition schema,
the final S1 geometry oracle, or a precedent for new chair families.

### Chair assimilation boundary

Chair assimilation converts external evidence into the same canonical chair
definition used by native definitions; it does not create a second geometry
system. A source may be a calibrated scan mesh, a componentised CAD model,
prototype drawings, direct measurements, or a combination. The boundary must:

1. record provenance, licence/usage status, file hashes, units, scale and
   coordinate frame before fitting;
2. align and calibrate the evidence using declared datums and measurements;
3. identify or ask the operator to identify constituent parts and rail-fit
   landmarks;
4. fit procedural parameters and preserve unresolved or inferred values as
   explicit findings;
5. regenerate the proposed chair through the normal exact adapter;
6. report dimensional constraints and a residual comparison against the source
   evidence; and
7. require explicit acceptance before publishing a reusable definition.

A scan alone cannot prove hidden surfaces, nominal unworn dimensions,
component boundaries or manufacturing fits. The supported workflow is therefore
assisted and evidence-led. Fully automatic conversion of an arbitrary 3D scan
into a production-ready parametric chair remains research unless later evidence
and a separately accepted scope promote it.

## Operating modes

### Edit/preview

- Canonical parameters are editable.
- Analytical data and lightweight 2D layers update incrementally.
- No routine 3D solids or dense persistent `Part` object graph is generated.
- Dirty exact geometry is recorded rather than rebuilt immediately.

### Analyse

- Railway, topology, timber and chair calculations run against canonical records.
- Findings and signatures are stored.
- Analytical calculations should remain independent of viewport object creation.

### Validate

- The user explicitly requests production-grade checks.
- Only the necessary exact geometry is built transiently.
- Validation results store the complete source signature, not the transient shapes.

### Export

- Current validation is required for the requested production scope.
- Target-specific geometry is built, staged, verified, committed, and disposed.
- Export does not silently change the editable model.

## Non-negotiable invariants

- Accepted geometry, sampling, tolerances and topology rules remain unchanged unless a separately approved change says otherwise.
- Stable identities, deterministic ordering, metadata schemas and production categories remain reproducible.
- Timber and chair decisions cannot change as a side effect of rendering or performance work.
- A production chair must be regenerable from its accepted definition without
  the original scan/CAD file or a retained FreeCAD shape.
- Chair constituent identities, rail-fit interfaces and prototype/manufacturing
  separation cannot be discarded during import, display or export.
- Cache reuse must be invalidated by every input that can affect its result.
- A lightweight preview is never evidence that exact production validation passed.
- One accepted application command is one atomic undo unit; its related
  derived-document updates cannot expose separately undoable incomplete
  states.
- Undo, redo, transactions, failure recovery and export rollback remain valid.
- Legacy files remain readable through explicit schema/version handling.

## Performance requirements

Initial numerical budgets will be set from measured baselines rather than guessed. The architecture is expected to improve:

- operator-visible stage and total wall time;
- process CPU time;
- resident memory growth;
- persistent FreeCAD document-object count;
- document recompute count and duration;
- save/load cost and interactive responsiveness.

The acceptance comparison must include both cold-cache and unchanged-result reuse. See [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).

## Validation requirements

Every migrated slice requires:

- legacy-versus-new analytical result comparison;
- stable identity and ordering comparison;
- exact geometry or export equivalence for its production scope;
- cold- and warm-cache tests;
- failure and rollback tests where document/export state changes;
- a real FreeCAD GUI exercise for affected display and editing behaviour.

See [VALIDATION.md](VALIDATION.md).

## Migration sequence

This is the architectural sequence. The numbered delivery phases, current status, and exit evidence are defined in [PROJECT_PLAN.md](PROJECT_PLAN.md).

1. **Baseline:** preserve representative documents and benchmark reports for current workflows.
2. **Create seams:** isolate domain calculations, FreeCAD document writes, view construction, and export calls without changing results.
3. **Prototype one measured hotspot:** replace one bounded, high-cost display/object-construction path with a lightweight adapter behind a comparison switch.
4. **Prove editing semantics:** demonstrate selection, parameter edits, undo/redo, visibility, save/load, and signature invalidation.
5. **Move exact construction to Validate/Export:** generate target-specific transient geometry and compare it with the legacy path.
6. **Migrate by entity family:** expand only after correctness and performance gates pass for the previous slice.
7. **Retire legacy paths:** remove a legacy path only after representative parity evidence and user acceptance.

Do not attempt a whole-macro rewrite.

## Source organisation direction

The development source should eventually separate domain, workflow, FreeCAD adapter, presentation and export code. The distributable form may remain a macro launcher or become an installable module/workbench; that packaging decision is deliberately deferred until loading and deployment requirements are agreed.

The extraction boundaries, dependency rules, anti-bloat safeguards and phased source migration are defined in [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md).

## Open design decisions

The following require prototypes or user decisions and are not settled by this document:

- Coin ViewProvider versus an embedded SVG/Qt renderer for the editing view;
- required granularity of viewport selection and direct manipulation handles;
- temporary-document lifecycle for exact geometry;
- single macro, generated macro bundle, or installable workbench distribution;
- numerical performance budgets and representative benchmark documents;
- migration/version policy for existing FreeCAD documents.
- chair-definition package schema, exact source-value representation and
  internal canonical units;
- accepted evidence, fit metrics and tolerances for the first S1 assimilation
  pilot, including confirmation of its precise prototype designation; and
- optional scan/CAD readers and fitting tools, which must not become mandatory
  dependencies of the macro's normal runtime without approval.

## Technical references

- [FreeCAD scripted objects and ViewProviders](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Scripted_objects.md)
- [FreeCAD scene-graph manipulation with Coin](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Code_snippets.md#manipulate-the-scenegraph-in-python)
- [FreeCAD SVG importer/exporter API](https://freecad.github.io/SourceDoc/d1/d33/namespaceimportSVG.html)
- [Templot5 open-source files on SourceForge](https://sourceforge.net/projects/opentemplot/files/)
- [Templot chair-output development discussion](https://85a.uk/templot/archive/topics/topic_3307.php)
