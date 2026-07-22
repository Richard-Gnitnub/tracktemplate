# Modularisation Plan

Status: accepted direction; Stage M1 and the Phase 1 closeout are complete.
Stage M2 is current under the bounded foundation authority accepted on
2026-07-22; no calculation extraction has started.

The authoritative delivery phases from the current baseline to a release candidate are defined in [PROJECT_PLAN.md](PROJECT_PLAN.md). The `M` stages below describe only the modularisation workstream and intentionally do not create a second project phase scheme.

## Objective

Replace the growing single-file implementation with cohesive, reusable modules while preserving every accepted railway and production result.

Modularisation supports the architecture in [ARCHITECTURE.md](ARCHITECTURE.md). It is not expected to reduce FreeCAD memory or recompute cost by itself. Its purpose is to create enforceable boundaries so domain calculations can be reused and tested independently, FreeCAD work can be deferred, and performance changes can be made safely.

## Current structural baseline

The preserved Phase 0 B14 legacy oracle contains:

| Signal | Observed value |
| --- | ---: |
| Source lines | 47,436 |
| Source size | 2,242,840 bytes |
| Top-level functions | 957 |
| Top-level classes | 18 |
| Duplicate top-level function names | 19 |
| Additional shadowing definitions | 26 |
| Functions longer than 100 lines | 70 |
| Functions longer than 250 lines | 12 |
| Largest function (`run_macro`) | 2,180 lines |
| Top-level runtime attribute/method patches | 30 |
| Functions directly naming FreeCAD or Qt globals | at least 87 |

These are structural indicators, not quality scores or performance measurements. The direct FreeCAD/Qt count is a lower bound because indirectly coupled functions are not included.

Some shadowing definitions are captured by compatibility aliases or class assignments before a later definition replaces the global name. Do not delete an earlier definition merely because its name is repeated; first prove that no live path retains it.

## Non-goals

- Do not rewrite the complete macro.
- Do not combine mechanical extraction with optimisation or behaviour changes.
- Do not split code solely to meet a line-count target.
- Do not create dozens of tiny modules with circular imports or shared mutable globals.
- Do not convert every dictionary or function to a new abstraction in one pass.
- Do not invent the renderer or the Workbench/Addon loading, update and
  catalogue mechanics without the prototypes required by `ARCHITECTURE.md`.
- Do not remove compatibility behaviour until representative legacy files and workflows pass.

## Target dependency direction

```text
launcher / composition root
          |
          +--> UI
          |     |
          |     `--> application commands and view models
          |
          +--> concrete adapters
                    |
                    +--> FreeCAD persistence / exact geometry
                    +--> optional external chair-evidence readers
                    +--> lightweight presentation
                    `--> production exporters

application  ------------------------------>  domain
adapters  ---> application contracts + domain records
domain    ---> Python standard library only
```

Dependencies point towards domain rules. The domain layer must never import UI or adapter code. Runtime composition supplies concrete adapters to application workflows rather than using reverse imports or monkey patches.

## Target source layout

```text
tracktemplate/
├── __init__.py
├── api.py                  # narrow supported façade
├── domain/                 # railway rules and deterministic calculations
├── application/            # commands, workflows, signatures and cache policy
├── adapters/
│   ├── freecad/            # persistence and transient exact geometry
│   ├── evidence/           # optional scan/CAD evidence readers and calibration
│   └── export/             # SVG, DXF, STL, STEP and manifests
├── presentation/           # lightweight 2D scene and selection mapping
├── ui/                     # dialogs, panels and user-facing orchestration
└── compatibility/          # legacy schemas and document migrations only

AdvancedTurnout.FCMacro     # small composition/launch entry point
```

This is a responsibility map, not a requirement to create every directory immediately. Start with the minimum package needed for the first extracted slice and add a boundary only when code is ready to cross it.

## Layer responsibilities

### Domain

Owns reusable railway meaning and calculations:

- alignments, stations, curves, easements and spacing;
- track, turnout and crossover topology;
- rail, timber, chair and support records;
- versioned chair-family definitions with named constituent records,
  procedural profiles/cross-sections, rail interfaces, source values/units,
  prototype/manufacturing separation, provenance and acceptance state;
- tolerances, findings, stable identities and deterministic ordering;
- production intent independent of a particular output format.

Domain modules must not import `FreeCAD`, `Part`, `FreeCADGui`, `PySide`, `pivy`, filesystem exporters or UI classes. Do not allow `App.Vector`, `Part.Shape`, `DocumentObject`, `QWidget` or a ViewProvider to cross a domain API.

### Application

Owns use cases rather than railway formulae:

- create/edit/analyse/validate/export commands;
- workflow state transitions;
- dirty-state propagation;
- complete signatures and cache policy;
- transaction intent and error propagation;
- view models for UI reporting;
- chair-definition package validation and the operator-assisted assimilation
  command, including explicit approval of fitted values and unresolved
  findings; and
- orchestration of definition/reference/residual comparisons using neutral
  evidence and exact-geometry metrics supplied by adapters.

The application layer may depend on domain records and abstract adapter contracts. It must not show dialogs or directly construct FreeCAD shapes.

### FreeCAD adapter

Owns the boundary with FreeCAD:

- document properties and persistence;
- transactions, recomputes, groups and visibility;
- conversion between domain coordinates and FreeCAD types;
- transient exact `Part` geometry;
- procedural construction of named chair components from accepted domain
  definitions, plus deterministic prototype reuse, assembly transforms and
  neutral exact-geometry measurements;
- cleanup and save/reopen integration.

It translates domain decisions; it must not introduce new railway rules.

### External chair-evidence adapter

Optional evidence adapters read a calibrated scan mesh, componentised CAD file,
drawing-derived measurements or another approved source into neutral evidence
records. They may perform format-specific parsing, alignment and surface
sampling, but they do not publish a chair definition or decide railway fit.

No evidence-reader dependency belongs in the normal macro runtime merely
because it is convenient for assimilation. A validated chair-definition
package must remain loadable and procedurally regenerable without the original
reader, source file, FreeCAD document or fitting tool. Third-party dependencies
still require separate approval.

### Presentation

Owns derived lightweight display:

- grouped scene layers;
- styles and visibility;
- stable visual-to-domain selection mapping;
- edit handles that issue application commands;
- redraw and incremental update policy.

It must not store independent geometry that can diverge from canonical domain state.

### Export adapter

Owns target-format preparation and file writing:

- target-specific transient geometry requests;
- SVG/DXF/STL/STEP writers or FreeCAD exporter calls;
- staging, bounds/scale checks, manifests, commit and rollback;
- deterministic filenames and categories.

Exporters cannot change the editable model or decide railway geometry.

### UI

Owns user interaction:

- dialogs, workflow panels and progress;
- collection and presentation of command inputs/results;
- explicit edit, analyse, validate and export actions.

UI callbacks call application commands. They do not contain railway solvers, persistence rules or export construction.

### Compatibility

Owns only explicit legacy concerns:

- old schema readers and migrations;
- legacy property aliases;
- version-to-version document upgrade rules.

The outer ingress policy is not open-ended: the Phase 1
[`compatibility contract`](contracts/phase1-compatibility.json) recognises B14,
B15 and their expected mixed set only. A compatibility adapter must preflight
read-only, fail closed on unknown/future/conflicting state, and migrate into a
copy/new canonical target. Each advertised entity family needs its own Phase 4
fixture before the adapter may write it.

Git history is the record of old implementations. Do not keep historical function bodies active merely to preserve a source changelog.

## Public contracts

- Expose a small façade through `tracktemplate.api`; callers should not import arbitrary internals.
- Pass serialisable domain/application records across boundaries. Choose typed mappings, immutable records or dataclasses only after confirming FreeCAD's supported Python environment and persistence needs.
- Return structured results and errors from domain/application code; adapters or UI convert them into FreeCAD state and user messages.
- Keep signature construction central to the result it protects. Do not let each adapter invent a partial cache key.
- Make units, coordinate frames, tolerances and ordering explicit at boundaries.
- Keep output schemas versioned and deterministic.
- Keep chair-definition packages serialisable and adapter-neutral: no
  `Part.Shape`, mesh object, GUI object or opaque source-file body may cross the
  domain boundary as canonical chair geometry.
- Preserve exact source values/units, inferred-value markers, component
  identities, definition/package versions, provenance and validation state in
  the package contract; generated topology or tessellation remains derived.

## Anti-bloat rules

- Maintain one live definition for each operation in modular source.
- Do not add permanent `_v14`, `_v15` or similar implementation stacks. Put genuine compatibility behaviour behind named migrations or strategies.
- Do not patch class methods at module import time. Wire collaborators explicitly or use normal class composition/subclassing where justified.
- Do not create a catch-all `utils.py`. Place reusable code with the concept it serves.
- Do not use mutable module globals as hidden communication between layers. Pass explicit context or services.
- Do not make a general abstraction before its shared invariant is understood. Similar-looking code with different railway meaning may remain separate.
- Keep module APIs narrow; underscore/internal names are not supported cross-module contracts.
- Reject circular imports. Resolve a cycle by moving the shared contract inward or injecting the dependency.
- Review module cohesion and dependency direction rather than enforcing an arbitrary file-size limit.
- Track structural metrics after each phase, but never trade clarity or correctness merely to reduce a count.
- Do not create separate native, scanned and imported chair generators. All
  accepted definitions use one constituent generator; assimilation ends by
  producing the same definition contract.
- Reuse procedural primitives and component strategies where railway meaning
  is shared, but do not create one copied module or class per chair type.

## Maintainability and reuse gate

This gate applies to retained product code, package/build tooling and shared
test or validation helpers. A bounded exploratory probe may optimise for rapid
learning, but before commit it must either be removed or deliberately promoted:
placed with the concept it serves, given a narrow contract, covered at the
appropriate stable boundary and made subject to the normal dependency rules.

For each retained source-organisation change, review and record:

1. the railway or application concept that owns the code;
2. the invariant genuinely shared by its callers, rather than superficial
   textual similarity;
3. the one authoritative implementation and its narrow supported interface;
4. the allowed dependency direction and any adapter boundary;
5. the direct, integration and parity evidence appropriate to its risk; and
6. every temporary duplicate, compatibility façade or comparison path, with a
   named owner and retirement gate.

The controls are deliberately layered:

| Risk | Current control | Later executable gate |
| --- | --- | --- |
| Hidden duplicates, captured aliases, import-time patches and mutable globals in B14/B15 | `tools/phase1_inventory.py` plus `tests/validate_phase1_inventory.py` fingerprint the present legacy structure and selected dependency closures | Re-run structural metrics after each applicable phase; modular source must trend towards one live definition and no import-time patch chain |
| Behaviour lost while code is reused or moved | Existing characterisation contracts, B14/B15 parity, stable-identity/ordering checks and applicable FreeCAD lifecycle tests | Every migrated slice must pass legacy/new parity before cleanup or optimisation |
| Domain code becoming coupled to FreeCAD, Qt or exporters | Architectural review today; the Phase 1 inventory reports platform signals but does not prove a future package boundary | Phase 2 standalone-import and forbidden-import tests must fail on a boundary violation |
| Circular or reverse dependencies | Manual dependency-direction review today | Phase 2 import-graph checks must fail on a cycle or prohibited layer edge |
| A second maintained implementation or an indefinitely retained comparison path | Staged-diff review and an explicit exception/retirement record | Phase 2/3 façade and composition checks, followed by removal at the named migration gate |
| Premature or misleading abstraction | Cohesion and railway-semantics review; similar code may remain separate until its invariant is understood | Direct tests of the shared contract and review of every new cross-module public API |

Static tools can find structural warning signs; they cannot decide whether two
algorithms express the same railway rule or whether an abstraction is clearer.
That semantic judgement remains a required review, backed by the behavioural
oracles rather than by line count or coverage percentage alone.

## Distribution strategy

Development source will be modular. The accepted primary release artifact is
an external FreeCAD **Track Template Workbench**, packaged as an Addon and
intended for installation through the FreeCAD Addon Manager. The
`tracktemplate` package remains the only authoritative implementation.

During migration the repository may also provide:

1. a small `.FCMacro` launcher beside the `tracktemplate` package;
2. direct development loading of the Workbench/package; and
3. a generated single-file macro only when an explicitly supported recovery
   or compatibility artifact remains essential.

If a generated macro is required, modular source remains authoritative. The generated artifact must be reproducible and must not be edited by hand. Its behaviour must be tested against the modular source from which it was built.

Phase 10 still owns the exact Addon manifest, installation/update mechanics,
catalogue submission and compatibility-launcher retirement evidence. Those
implementation choices do not reopen the accepted Workbench/Addon product
target. Phase 1 records the intended initial compatibility metadata
(`freecadmin`/`freecadmax` 1.1.1 and `pythonmin` 3.12.0); Phase 10 must
revalidate it against the then-current official schema and runtime matrix
before generating `package.xml`.

## Extraction method

Every extraction uses the following sequence:

1. Define the exact functions/data and callers in scope.
2. Add or strengthen characterisation tests around current behaviour.
3. Record applicable performance and structural baselines.
4. Create the smallest required target module and API.
5. Move code mechanically with names, ordering and calculations unchanged.
6. Route legacy callers through a temporary façade.
7. Run legacy-versus-modular result comparisons.
8. Exercise FreeCAD integration where the boundary touches documents or GUI.
9. Review imports, mutable state and signature inputs.
10. Commit the extraction separately from later cleanup or optimisation.

Only after parity is established may a second change simplify or optimise the extracted implementation.

## Modularisation workstream stages

### Stage M0: preserve the checkpoint

- Commit the B14 legacy oracle, accepted B15 behavioural reference, tests and architecture documents while excluding IDE/cache/generated files.
- Record representative inputs/documents and cold/warm benchmark reports.
- Confirm the current validation commands and known coverage gaps.

Exit gate: the pre-modular behaviour can be reproduced and recovered.

Status: **Complete with the Phase 0 closeout.**

### Stage M1: dependency inventory

- Map top-level definitions to domain, application, adapter, presentation, UI or compatibility responsibility.
- Identify imports, global state, duplicate definitions, class patches and side effects at import time.
- Build caller/callee information for candidate slices.
- Mark data that crosses FreeCAD, UI, persistence and export boundaries.
- Map Templot's chair data, procedural component construction, reusable block
  placement and output path, and distinguish it from B15's bounded five-box
  approximation before selecting or moving chair code.

Exit gate: the first extraction is selected from evidence rather than source proximity.

Status: **Complete — selection and Phase 1 closeout accepted on 2026-07-22.**
The reproducible static definition/caller/alias/patch
inventory and initial candidate comparison are recorded in
[PHASE1_INVENTORY.md](PHASE1_INVENTORY.md). The five current candidates now
have a fail-closed machine-readable boundary contract covering units, frames,
tolerances, identities, ordering, schemas, side effects and
signature/invalidation inputs. Inventory schema 2 now adds static closure-cut
callers and dependencies leaving each bounded closure. The
[first-slice scorecard](PHASE1_SLICE_SCORECARD.md) led to owner acceptance of
the transition solver as a first architecture pilot, not a performance
optimisation. Its exact façade, caller, parity, rollback and performance scope
is frozen in
[contracts/phase1-transition-pilot.json](contracts/phase1-transition-pilot.json).
The exact qualified runtime, standalone Python floor and B14/B15 ingress
policy are separately frozen in
[`contracts/phase1-compatibility.json`](contracts/phase1-compatibility.json).
The fixed-XO chair candidate's emitted-input omissions, precision/order
behavior and presentation-control topology are further frozen in
[`contracts/phase1-chair-analysis-invalidation.json`](contracts/phase1-chair-analysis-invalidation.json);
that evidence blocks reuse of its partial signature rather than authorising
chair extraction.
Broader workflow boundaries, candidate-specific gaps, additional platform
qualification and representative target-architecture profiles remain open;
source movement and document migration have not started. The consolidated
[Phase 1 closeout record](PHASE1_CLOSEOUT.md) preserves those later gates and
authorises only the empty Stage M2 package/loading foundation.

### Stage M2: package skeleton and façade

Status: **Current — authorised on 2026-07-22; implementation not yet
started.**

- Add only the package locations needed by the selected slice.
- Establish `tracktemplate.api` and the composition root.
- Add an import test proving the extracted domain code loads without FreeCAD or Qt.
- Keep B14 and B15 byte-identical as legacy/reference evidence. Introduce the
  reserved `TrackTemplate.FCMacro` only as a small B16 development composition
  root; do not copy the monolith or make the launcher authoritative.
- Keep the extracted domain/API compatible with the recorded CPython 3.12.0
  floor and exercise it in both the standalone 3.12.3 environment and the
  qualified FreeCAD-bundled 3.13.14 runtime.
- Add only a development composition guard for the exact qualified host; the
  production document detector/migrator remains a Phase 4 compatibility
  adapter and the final Addon metadata remains Phase 10 work.

Exit gate: the empty boundary and loading approach work in both standalone Python tests and FreeCAD.

### Stage M3: first vertical slice

Select a slice that has:

- clear inputs and outputs;
- useful existing characterisation coverage;
- bounded side effects and caller count;
- measurable duplication or coupling reduction;
- a legacy/new comparison route.

Chair analysis is a candidate because current tests cover important chair behaviour, but it is not chosen until the dependency inventory confirms that its hidden coupling is manageable.

Extract the pure calculation first, then its application command, FreeCAD adapter and presentation path as separate parity-proven steps.

Exit gate: one complete capability follows the target dependency direction without changing accepted results.

### Stage M4: deferred geometry seam

- Route the selected slice's normal display through the lightweight presentation contract.
- Move its exact shape construction behind explicit Validate/Export requests.
- Compare editing and end-to-end export cost using [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).
- Keep a temporary legacy comparison path until parity and user acceptance.

Exit gate: the architecture produces a measured resource improvement without hiding cost or reducing validation.

### Stage M5: repeat by capability

Migrate the next bounded capability using the same gates. Reassess ordering after every slice; do not assume source order is migration order.

Potential capability families include:

- alignment and station mapping;
- track and platform preparation;
- turnout geometry and timbering;
- crossover topology and timber resolution;
- chair analysis, versioned definitions, procedural component generation,
  assisted assimilation and presentation;
- production record planning and export.

Exit gate: each migrated family has independent tests, explicit adapters and no reverse dependencies.

### Stage M6: reduce the launcher and retire legacy layers

- Move remaining UI composition out of `run_macro`.
- Replace import-time class patches with explicit constructed collaborators.
- Remove shadowed legacy implementations only after retained-reference audits.
- Keep compatibility migrations required by supported documents.
- Automate the accepted Workbench/Addon assembly and any explicitly retained
  compatibility launcher from the same authoritative source.

Exit gate: the Workbench loads the modular source, any macro is only a small
launcher/composition root, and modular source is the only maintained
implementation.

## Validation gates

Follow [VALIDATION.md](VALIDATION.md). At minimum, each extraction must demonstrate:

- source parsing and import compatibility;
- domain import without FreeCAD/Qt when applicable;
- legacy/new analytical result equality;
- stable identity, ordering and schema equality;
- valid cache miss/reuse/invalidation behaviour;
- headless FreeCAD integration for changed adapter paths;
- real GUI checks for display or editing changes;
- exact output/manifest comparison for export paths;
- chair-definition round-trip, constituent identity, rail-interface,
  prototype/manufacturing separation and procedural-regeneration evidence when
  the slice touches chairs;
- regenerated-versus-Templot and, for an assimilated chair, regenerated-versus-
  source residual evidence using agreed metrics rather than raw tessellation
  byte equality;
- no unplanned performance or object-count regression.

## Structural progress measures

Recalculate the current baseline indicators after each applicable project phase:

- active duplicate definitions and import-time patches;
- functions and classes remaining in the launcher;
- functions directly coupled to FreeCAD/Qt;
- dependency cycles and cross-layer imports;
- domain test coverage without FreeCAD;
- number of persistent document objects for representative workflows.

The desired trend is fewer active duplicates/patches, a smaller launcher, stronger independent tests and lower document cost. Total repository line count may temporarily rise while parity tests and compatibility façades coexist; that is acceptable when the temporary code has an explicit retirement gate.

## Completion criteria

Modularisation is complete when:

- the launcher contains composition and startup only;
- railway calculations are reusable without FreeCAD or Qt;
- application workflows call explicit domain and adapter contracts;
- lightweight presentation and exact geometry are separate adapters;
- exporters consume validated canonical records;
- legacy documents use explicit migrations rather than historical live implementations;
- no import-time monkey-patch chain chooses the active production behaviour;
- the modular source and distribution artifact cannot drift;
- validation and performance gates pass for representative workflows.

## Open decisions

- exact Workbench/Addon manifest, loading/update and Addon Manager catalogue
  submission mechanics, plus the compatibility launcher's supported lifetime;
- B14/B15 family-migration implementation/fixtures and qualification evidence
  for any proposed runtime or legacy-window expansion;
- record/type approach compatible with the supported FreeCAD Python runtime;
- exact chair-definition package schema, source-value representation and
  canonical unit strategy;
- optional scan/CAD evidence readers and fitting implementation for the S1
  pilot, subject to the no-new-runtime-dependency rule;
- tooling for dependency-cycle and structural-metric enforcement.
