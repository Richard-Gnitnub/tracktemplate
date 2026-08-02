# TrackTemplate Architecture

Status: accepted strategic direction; implementation is intentionally phased.

The [product vision](PRODUCT_VISION.md) owns product purpose, the current Core
migration programme and the subsequent Layout Editor horizon. The
authoritative phase sequence and status are maintained in
[PROJECT_PLAN.md](PROJECT_PLAN.md); true-gate policy is maintained in
[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md).
The supporting [product-system ontology](ONTOLOGY.md) projects the stable
concepts and relationships in this architecture for human and machine use; it
does not replace this document or record delivery status.

## Why the architecture is changing

The project grew successfully by adding validated capability in stages: parametric curves and easements, station/straight and multi-track features, turnouts, crossovers, timbering, chair analysis, integration, and production export. That iterative approach proved the railway calculations, but it also concentrated domain logic, FreeCAD document management, display construction, exact shape generation, persistence, and export in one increasingly resource-intensive macro.

The current Core migration is architectural rather than another feature
layer. It must reduce interactive cost without sacrificing accepted railway
results, and it must end with the modular package as the one authoritative
runtime implementation behind the normal FreeCAD Workbench/Addon route.

## Accepted direction

The system separates authoritative canonical state from interactive display
and production geometry. The accepted presentation direction is explicit:

```text
canonical TrackTemplate state
        |
        `--> railway geometry and analysis
                    |
                    +--> immutable presentation snapshot
                    |           |
                    |           `--> batched Coin representation
                    |
                    `--> explicit exact-validation request
                                |
                                `--> transient exact geometry
                                            |
                                            `--> authorised outputs
```

The live document should remain lightweight. Exact OpenCASCADE `Part` shapes, solids, Boolean operations, and dense per-element FreeCAD objects should not be created during routine editing when a derived 2D representation can provide the required feedback.

Exact geometry is permitted at an explicit **Validate** or **Export** boundary. Validation must not be postponed until after a production file has already been written.

## Architectural principles

1. **Railway semantics are authoritative.** Parameters, stable identities, topology, alignments, timber decisions, chair assignments, and production metadata are the source of truth.
2. **The viewport is a projection.** Coin scene-graph nodes display the normal
   editing model; they do not replace it. D-P5-002 accepts Coin only for its
   demonstrated B16 Entry/Exit boundary, so the wider shared renderer remains
   implementation work rather than an accepted capability.
3. **Users edit intent, not generated paths.** Editing acts on parameters or defined semantic handles. Arbitrary edits to a rendered SVG path are not accepted unless a deterministic round trip back to the parametric model is designed and validated.
4. **Exact geometry is demand-driven.** Build only the geometry required for
   an explicit validation, export or materialisation request, and dispose of
   transient geometry after use. Selection and ordinary parameter editing do
   not regenerate it unless a separately accepted workflow requires that
   behaviour.
5. **Persistence is compact and versioned.** Store canonical parameters and results, not redundant derived geometry. Schema changes require an explicit migration path.
6. **Derived state is fingerprinted.** Preview, analysis, validation, and export caches must be tied to complete input signatures. Stale speed is a correctness failure.
7. **Export remains deterministic and transactional.** Staging, preflight, manifest generation, overwrite handling, commit, and rollback remain production invariants.
8. **Migration is incremental.** The existing implementation remains the comparison path until each replacement proves output equivalence and a measured resource improvement.
9. **Production chairs remain procedural.** Full-size prototype parameters and
   explicit constituent parts are authoritative. A scan, mesh, CAD body, or
   generated FreeCAD shape is reference evidence or derived output, never a
   substitute for an accepted parametric chair definition.
10. **Rights provenance travels with data.** Software-source licensing,
    engineering methods, factual dimensions, measured evidence, external
    assets, Templot reference material, and generated output remain explicitly
    classified under [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). A
    validation oracle is not silently promoted into canonical production data.
11. **The product is a FreeCAD Workbench Addon.** The release product is an
    external Track Template Workbench backed by the authoritative modular
    package and distributed in an Addon Manager-compatible form. The current
    `.FCMacro` remains a migration and optional compatibility launcher, not the
    authoritative release implementation.
12. **Reuse and maintainability are release invariants.** A shared railway
    concept has one authoritative implementation behind a cohesive, narrow and
    tested interface. Dependencies remain explicit and follow the accepted
    layer direction. Exploratory code is removed or deliberately promoted to
    these standards before it becomes retained project code; any necessary
    temporary duplication has a named owner and retirement condition.

## Accepted Level 3 product-direction decisions

D-GOV-005 records the following architectural clauses. They govern direction;
their acceptance does not claim that a shared renderer, wider exact geometry,
another migrated family or a future Layout Editor capability is implemented.

| Clause | Accepted direction | Implementation boundary retained |
| --- | --- | --- |
| D-GOV-005-A — canonical authority | Versioned railway intent, identities, topology, analysis decisions, production intent and accepted definitions are canonical. Coin nodes, ViewProvider state, transient/generated `Part` geometry, caches, previews, exports, reports and manifests are derived and replaceable. | Existing schemas and accepted family boundaries are unchanged. |
| D-GOV-005-B — presentation pipeline | Canonical state feeds railway geometry and analysis, then an immutable presentation snapshot, then a batched Coin representation. | The accepted B16 Entry/Exit scene remains the only demonstrated slice; no shared renderer is claimed. |
| D-GOV-005-C — normal editing view | Routine editing is fast Coin-based 2D or pseudo-2D with rails and sleepers/timbers, construction information and optional chair, analysis and warning layers, without a `Part` dependency. | The current centreline fixture does not yet implement the complete normal view. |
| D-GOV-005-D — exact geometry | Exact geometry is explicit, on demand, derived, safe to delete and regenerate, and not automatically rebuilt for ordinary selection or editing. | Accepted transient geometry remains limited to the Phase 6 Entry/Exit evidence. |
| D-GOV-005-E — display modes | Register only genuinely distinct FreeCAD display modes owned by that ViewProvider. Detail, construction and analysis choices normally remain internal layer switches or presets. Invalid restored modes fail closed or recover through the accepted lifecycle without becoming canonical state. | No current ViewProvider is replaced and no display-mode migration is implemented by this decision. |
| D-GOV-005-F — presentation performance | Batch rails, sleeper/timber faces and chair markers; avoid one FreeCAD object per sleeper/chair and one transform per chair; separate static geometry from dynamic overlays/labels; do not rebuild the complete scene graph for selection-only changes. | Numerical budgets and a product-wide renderer remain unaccepted. |
| D-GOV-005-G — product horizons | TrackTemplate Core migration is the current programme; TrackTemplate Layout Editor is a subsequent programme. | Future extension direction does not alter an active phase or authorise Layout Editor implementation. |

## Target layers

### 1. Domain model

The domain layer represents:

- routes, tracks, stations and alignments;
- curves, easements, straights and spacing transitions;
- turnouts, crossover relationships and topology;
- rails, timbers, chair assignments, supports and stable identities;
- versioned chair-family definitions, constituent components, rail interfaces,
  manufacturing variants, field/component provenance classifications, and
  package/output rights metadata;
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

The initial host and legacy-ingress boundary is fixed by
[`contracts/phase1-compatibility.json`](contracts/phase1-compatibility.json).
Only a qualified FreeCAD runtime may write through this adapter. B14 and B15
remain the bounded migration sources, including their expected mixed version
set, but migration always targets a user-approved copy/new document and
remains controlled by entity family. Unknown, future, versionless, corrupt or
insufficiently parametric state is inspection-only or blocked; legacy exact
shapes are evidence rather than authoritative state.

Within its exact accepted boundary, Phase 4 established canonical transition-
state v1, application-owned signatures and invalidation, compact FreeCAD
persistence, a disposable derived-state lifecycle, renderer-neutral preview
state, the neutral chair-definition package v1 boundary and fixture-only
copied-target support for the spacing-matched plain-line transition family.
Exact geometry and export remain Phase 6 work. Wider product/operator
migration, whole-document support, alignment, turnout, crossover, timber,
chair and other entity-family migration remain later-phase work.

### 4. Lightweight presentation adapter

The normal editing view is a derived Coin-based 2D or pseudo-2D snapshot
grouped into a small number of semantic/style batches, for example:

- running, switch, closure, check and crossing rails;
- sleeper and turnout-timber faces, outlines and centres;
- construction marks, template joints and registration features;
- optional chair markers, analysis findings and warnings; and
- selection and edit handles plus dynamic labels.

A custom FreeCAD ViewProvider backed by batched Coin line/face primitives is
the accepted direction because it separates the editable document object from
its GUI representation. The renderer consumes an immutable presentation
snapshot rather than querying or mutating canonical state while drawing.

The renderer must provide a mapping from a selected visual element back to a stable domain identity. View-only coordinates must never become an independent source of railway truth.

Static rails, sleeper/timber faces and chair-marker batches remain separate
from dynamic selection overlays, warnings and labels. A selection-only change
updates the affected dynamic state; it does not justify rebuilding the whole
scene graph. The normal representation does not allocate one persistent
FreeCAD object per sleeper or chair, or one Coin transform per chair.

#### ViewProvider display modes and view layers

A ViewProvider registers only modes that represent genuinely distinct FreeCAD
display pipelines, and every registered mode belongs to that ViewProvider.
Construction detail, chair visibility, analysis findings and similar options
normally use internal view-layer switches or named presets rather than a large
cross-product of registered display modes.

On restore or temporary attachment, a mode not owned by the active
ViewProvider must not be treated as valid merely because its name was stored.
The lifecycle validates the restored enumeration/current-mode pair and either
preserves a valid prior mode, selects an owned safe mode under an accepted
contract, or fails closed with recoverable diagnostics. Display-mode strings,
switch indices and Coin nodes remain derived state.

### 5. Exact geometry adapter

This adapter converts selected domain records into the minimum `Part` geometry needed for:

- exact fit or topology validation;
- planar production profiles;
- 3D solids and meshes;
- FreeCAD exporters that require `Part::Feature` objects.

Prefer a temporary or isolated document and remove generated objects after validation/export. Persistent production shapes are created only when the user explicitly requests materialisation as a retained result.

Transient or materialised exact objects remain derived and replaceable. They
must be safe to delete and regenerate from current signed canonical state.
Ordinary selection, visibility changes and parameter editing mark applicable
exact stages dirty; they do not rebuild exact geometry automatically unless an
accepted workflow explicitly requires it.

Direct SVG generation from canonical 2D records may bypass `Part` construction when scale, bounds, categories, identifiers, and output equivalence can be validated. Formats that require BRep or mesh geometry still use the exact adapter.

### 6. Export adapter

The export layer keeps the existing safety model:

1. Resolve the requested scope and formats.
2. Confirm analysis and exact-validation signatures are current.
3. Generate only target-specific transient geometry.
4. Write into a hidden staging location.
5. Validate bounds, scale, topology, manifest entries, and recorded
   output-affecting package/rights dependencies.
6. Commit the complete output set atomically or, for an explicitly accepted
   bounded protocol, complete it monotonically under that protocol's named
   invariants.
7. Apply the accepted transaction's failure rules and clean transient
   geometry without claiming authority over foreign or published state.

#### D-P6-003 cross-process recovery authority

For the bounded B16 Entry/Exit DXF-and-manifest pair, D-P6-003 selects a strict
add-only, journal-free monotonic-completion protocol. Recovery authority is
constructive, not destructive: a later process may add an absent deterministic
member, but TrackTemplate never removes foreign, uncertain or published
destination state.

Each invocation recomputes the exact expected pair from current signed inputs,
binds the real destination directory by descriptor and prepares unpublished
payloads in anonymous, creation-bound descriptors. Before publication, failure
is abandoned only by closing those owned anonymous descriptors. Historical
journals, temporary-journal links and stage artifacts are inert foreign
residue: they are not opened, parsed, modified, deleted or used to permit or
block final-set completion. Inspecting an existing final for type and exactness
does not grant authority to delete, replace or otherwise mutate its pathname.
The two final names alone have these outcomes:

- when neither exists, add each absent final pathname without overwrite from
  its synchronised anonymous descriptor;
- when exactly one exact regular member exists, preserve it unchanged and add
  only its missing exact counterpart;
- when both exact regular members exist, independently revalidate and reuse
  the pair; and
- on a mismatch, symbolic link, non-regular member, collision, replay,
  substitution, inconsistency or ambiguous observation, fail closed without
  further mutation.

Publication remains descriptor-relative and no-overwrite, with directory
synchronisation. The first successful final link permanently ends rollback:
no published final may thereafter be unlinked, renamed, rewritten, truncated,
replaced or otherwise claimed by TrackTemplate. Authenticating or verifying a
pathname does not create authority to delete it, and POSIX pathname deletion
has no expected-inode atomic condition. A race or other failure discovered
after an addition therefore leaves the exact partial or complete output set
untouched and reports failure truthfully. A later invocation may add only an
absent exact counterpart, and success may be reported only after the complete
final pair is independently revalidated as exact. Unsupported host or
filesystem primitives fail closed.

`destination_changed`, `cleanup_complete`, `recoverable` and related
diagnostics describe the state actually retained. `recoverable=True` requires
an independently revalidated exact zero-member, partial or complete destination
with safe retry or remaining add-only authority; ambiguity, mismatch, uncertain
durability or an unsupported primitive is not recoverable. Any successful
addition sets `destination_changed=True`, and any surviving published final on
a failed invocation sets `cleanup_complete=False`. Closing all unpublished
anonymous descriptors does not imply that a partial published set was rolled
back.
Content equivalence establishes compatibility for reuse or completion only;
it never establishes ownership, deletion or replacement authority.

This contract preserves the final filenames, DXF and manifest bytes, manifest
schema and contract IDs, two-file layout and `reuse-identical-or-fail` policy.
That policy applies per final member: preserve an identical regular member,
create only its absent deterministic counterpart and fail on any non-identical
or non-regular existing member. It deliberately refines one collision outcome:
a lone exact regular final member may be completed instead of rejected. The
implementation and focused interruption/recovery proof remain a later bounded
Level 2 tranche; Exit 3 remains Pending until a fresh Level 3
evidence-admission decision.

## Chair-definition and procedural-geometry contract

Production chair geometry will use a neutral TrackTemplateMacro definition and
a procedural constituent construction pattern. That pattern is explicitly
source-informed by the accepted Templot5 revision 556b evidence, but the
canonical schema is not a Templot data format. Source-informed architecture
does not authorise unrecorded copying of Templot tables, profiles, media output,
or expressive Pascal control flow, and it does not require the exact adapter to
emit Templot's low-level DXF `3DFACE` records internally.

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
  field/component classifications from
  [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md), source-file hashes,
  licence or `NOASSERTION` state, permitted output/redistribution use,
  assumptions, tolerances and validation state;
  and
- be serialisable and usable by domain tests without importing FreeCAD or Qt.

The exact adapter consumes an accepted chair definition, constructs its named
components, and assembles reusable prototypes by deterministic transforms at
calculated rail/timber positions. FreeCAD/OpenCASCADE B-reps and solids are the
preferred exact representation. They may differ from the upstream output
mechanism, but not replace the accepted parameterised component model with
hand-drawn bodies, rectangular envelopes, or an imported mesh. Tessellation is
an export concern for formats such as STL, not canonical chair state. A local
Templot comparison oracle may validate geometry; it does not become a runtime
or distributable package dependency.

The current B15 S1/S1J five-box body is retained only as accepted legacy
behaviour and gap evidence. It is not the production chair-definition schema,
the final S1 geometry oracle, or a precedent for new chair families.

The owner-accepted Phase 1 package/evidence decisions are in
[S1_PILOT_PLAN.md](phase-evidence/S1_PILOT_PLAN.md). Its exact decimal source-quantity,
full-size millimetre, chair-local frame and validate-before-mutation rules are
retained in the neutral chair-definition package v1 boundary accepted in Phase
4. The plan deliberately leaves the prototype designation, primary evidence,
rail section, final package licence, rights reviews and numerical tolerances
blocked; neither the working S1 name nor the conditional CC0 target is
canonical production data.

### Chair assimilation boundary

Chair assimilation converts external evidence into the same canonical chair
definition used by native definitions; it does not create a second geometry
system. A source may be a calibrated scan mesh, a componentised CAD model,
prototype drawings, direct measurements, or a combination. The boundary must:

1. record provenance classification, licence/usage/output/redistribution
   status, file hashes, units, scale and coordinate frame before fitting;
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

### Templot compatibility and rights boundary

The canonical interchange is the neutral `ChairDefinition`, not “Templot
data”. If Templot compatibility is later implemented, it is an optional outward
adapter:

```text
project-cleared evidence
          |
          v
neutral ChairDefinition ----> TrackTemplate exact/export adapters
          |
          `------------------> optional Templot-format adapter
```

The adapter may serialise an accepted neutral definition into a documented
Templot format. It cannot make a Templot file the canonical project state,
import Templot media or opaque generated geometry as an authoritative chair,
or feed upstream values back into a definition without a new provenance and
rights review. Templot comparison artifacts remain local reference evidence
unless their exact licence permits redistribution.

An outward conversion does not change the recorded origin or ownership of the
neutral data. If the same project-cleared package is contributed to Templot, a
notice later added by Templot to Templot-generated media does not automatically
become a notice on separate TrackTemplateMacro output generated directly from
the original package.

Generated-output rights follow the actual user inputs, definition packages,
and protected material embedded in the output. The project does not assert
control over ordinary output merely because its GPL program generated it, and
it cannot grant rights held by others. Production manifests must expose package
identities, licences, restricted/reference-only/unknown dependencies, and the
project status defined in
[LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). Current B14/B15 output is
not retroactively project-cleared by adopting this architecture. No package or
output can receive `project-cleared` status until its machine-readable
dependency manifest passes the repository's fail-closed validator.

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
- The manifest records the canonical/package identities and known
  output-affecting rights dependencies used for the export.
- Export does not silently change the editable model.

## Non-negotiable invariants

- Accepted geometry, sampling, tolerances and topology rules remain unchanged unless a separately approved change says otherwise.
- Stable identities, deterministic ordering, metadata schemas and production categories remain reproducible.
- Timber and chair decisions cannot change as a side effect of rendering or performance work.
- A production chair must be regenerable from its accepted definition without
  the original scan/CAD file or a retained FreeCAD shape.
- Chair constituent identities, rail-fit interfaces and prototype/manufacturing
  separation cannot be discarded during import, display or export.
- Engineering facts and project measurements cannot be replaced by a Templot
  comparison as their claimed primary source, and systematically copied
  upstream tables cannot be relabelled as isolated facts.
- Templot reference data/media and unresolved third-party evidence cannot enter
  a project-cleared production definition.
- A package or output cannot be labelled `project-cleared` while an
  output-affecting dependency is `restricted`, `reference-only`, `unknown`, or
  `NOASSERTION` for the intended use.
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

Normal-view resource direction is also structural: batch like rail primitives,
sleeper/timber faces and chair markers; keep static geometry apart from dynamic
overlays and labels; avoid per-sleeper/per-chair document objects and
per-chair transforms; and update only affected derived batches. These rules do
not establish a numerical performance budget or claim that the current bounded
renderer already satisfies the complete product workload.

## Validation requirements

Every migrated slice requires:

- legacy-versus-new analytical result comparison;
- a maintainability/reuse review naming the authoritative implementation,
  shared invariant, public boundary, dependency direction and any temporary
  duplication plus its owner and retirement condition;
- stable identity and ordering comparison;
- exact geometry or export equivalence for its production scope;
- cold- and warm-cache tests;
- failure and rollback tests where document/export state changes;
- provenance/dependency-manifest checks where source data or protected material
  can affect production output;
- a real FreeCAD GUI exercise for affected display and editing behaviour.

See [VALIDATION.md](VALIDATION.md).

## Migration sequence

This is the architectural sequence. Numbered phase status is in
[PROJECT_PLAN.md](PROJECT_PLAN.md), while detailed current exit evidence is in
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md).
It implements the current TrackTemplate Core programme in
[PRODUCT_VISION.md](PRODUCT_VISION.md); the subsequent Layout Editor does not
join this sequence without separate Level 3 authority.

1. **Baseline:** preserve representative documents and benchmark reports for current workflows.
2. **Create seams:** isolate domain calculations, FreeCAD document writes, view construction, and export calls without changing results.
3. **Prototype one measured hotspot:** replace one bounded, high-cost display/object-construction path with a lightweight adapter behind a comparison switch.
4. **Prove editing semantics:** demonstrate selection, parameter edits, undo/redo, visibility, save/load, and signature invalidation.
5. **Move exact construction to Validate/Export:** generate target-specific transient geometry and compare it with the legacy path.
6. **Migrate by entity family:** expand only after correctness and performance checks pass for the previous slice.
7. **Retire legacy paths:** remove a legacy path only after representative parity evidence and user acceptance.

Do not attempt a whole-macro rewrite.

## Source organisation direction

The development source will separate domain, workflow, FreeCAD adapter,
presentation and export code. The accepted release target is an external
FreeCAD **Track Template Workbench**, packaged as a FreeCAD **Addon** and
intended for installation through the Addon Manager. The modular
`tracktemplate` package is authoritative. A small `.FCMacro` may remain during
migration or as an explicitly supported compatibility entry point, but it
must delegate to the same package and cannot become a second maintained
implementation.

The extraction boundaries, dependency rules, anti-bloat safeguards and phased source migration are defined in [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md).

## Open design decisions

The following require prototypes or user decisions and are not settled by this document:

- required granularity of viewport selection and direct manipulation handles;
- product-wide composition of the accepted Coin direction beyond the bounded
  B16 Entry/Exit lifecycle, including the shared snapshot/batching boundary;
- exact materialisation and lifecycle policy beyond the accepted disposable
  Entry/Exit exact-geometry boundary;
- exact Addon manifest, loading/update mechanics, catalogue-submission route
  and supported lifetime of the compatibility macro launcher;
- numerical performance budgets and representative benchmark documents;
- later B14/B15 family-migration implementations and fixtures beyond accepted
  transition-state v1 and the fixture-only spacing-matched plain-line family,
  plus evidence for any proposed expansion of the ingress/runtime matrix;
- production chair definitions and package admission beyond the accepted
  neutral chair-definition package v1 boundary, including the primary S1
  evidence, numerical tolerances, rights and intended-use decisions retained
  by the Phase 1 S1 plan;
- accepted evidence, fit metrics and tolerances for the first S1 assimilation
  pilot, including confirmation of its precise prototype designation, rights
  chain, intended package licence and commercial/publication use; and
- optional scan/CAD readers and fitting tools, which must not become mandatory
  dependencies of the macro's normal runtime without approval.

## Technical references

- [FreeCAD scripted objects and ViewProviders](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Scripted_objects.md)
- [FreeCAD scene-graph manipulation with Coin](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Code_snippets.md#manipulate-the-scenegraph-in-python)
- [FreeCAD SVG importer/exporter API](https://freecad.github.io/SourceDoc/d1/d33/namespaceimportSVG.html)
- [FreeCAD Addons and Addon Manager](https://www.freecad.org/addons.php?lang=eng_EN)
- [FreeCAD addon ecosystem repositories](https://github.com/FreeCAD)
- [Templot5 open-source files on SourceForge](https://sourceforge.net/projects/opentemplot/files/)
- [Templot chair-output development discussion](https://85a.uk/templot/archive/topics/topic_3307.php)
