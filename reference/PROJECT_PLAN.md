# Project Plan: Baseline to Release Candidate

Status: working delivery plan. **Phase 0 closed on 2026-07-19; Phase 1 is current.**

## Purpose

This plan turns the accepted architecture into an ordered, evidence-gated project. It covers repository recovery, characterisation, modularisation, canonical state, lightweight presentation, deferred exact geometry, capability migration, product integration, packaging, and release-candidate qualification.

The plan is gate-based rather than date-based. Calendar estimates would be speculative until the Phase 1 dependency inventory and representative performance baselines exist.

The documents have distinct responsibilities:

- [ARCHITECTURE.md](ARCHITECTURE.md) defines the target system and non-negotiable invariants.
- [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md) defines source boundaries and the safe extraction method.
- [TESTING_POLICY.md](TESTING_POLICY.md) defines when tests are required and when an existing oracle may change.
- [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md) defines comparable resource measurements.
- [VALIDATION.md](VALIDATION.md) defines correctness and integration evidence.
- [TERMINOLOGY.md](TERMINOLOGY.md) defines canonical railway language and the
  compatibility policy for legacy identifiers.
- [PROVENANCE.md](PROVENANCE.md) records reference-source identity, source
  relationship, redistribution and licensing status.
- [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) defines the mandatory
  source/data classifications, neutral chair-data boundary, collaboration
  rules, package-licensing target, generated-output policy, and clearance
  statuses.
- [PHASE1_INVENTORY.md](PHASE1_INVENTORY.md) owns the current workflow,
  dependency, side-effect, candidate and Phase 1 decision evidence.
- This document owns delivery order, phase status, decision timing, and release-candidate gates.

If a proposed shortcut conflicts with railway correctness, production safety, or an accepted architectural invariant, the invariant wins unless the user explicitly approves a changed requirement.

## Intended release-candidate outcome

The release candidate will provide the agreed curve/easement, station and multiple-track, turnout, crossover, timber, chair, host-integration, and production-export workflows through the new architecture. It will have:

- one authoritative parametric railway model with explicit units, tolerances, stable identities, topology, and production intent;
- reusable domain calculations that import and run without FreeCAD or Qt;
- a lightweight derived editing view with deterministic selection back to domain identities;
- exact `Part` geometry generated only for explicit validation/export or requested retained production objects;
- versioned, validated and provenance-classified external chair-definition
  packages whose full-size constituent geometry can be regenerated
  procedurally and whose intended output/redistribution use is explicit;
- one evidence-led, operator-assisted S1 chair assimilation pilot using the
  same definition and geometry path as native chair definitions;
- compact, versioned FreeCAD persistence with tested save/reopen and supported legacy migration;
- deterministic, transactional exports and manifests;
- machine-readable output dependency/project-status records that distinguish user
  design, engineering facts, project measurements, package data, restricted
  material, and local comparison oracles;
- a small launcher/composition root and one authoritative modular implementation;
- an external Track Template FreeCAD Workbench, packaged as an Addon and
  intended for Addon Manager installation, with reproducible artifacts,
  validation evidence, user documentation and measured performance budgets;
- no known release-blocking correctness, data-loss, migration, or production-export defect in the supported scope.

Release-candidate scope is based on the accepted B15 behavioural reference,
with B14 retained as the immutable legacy comparison oracle. On 2026-07-20 the
project owner explicitly expanded that scope to include the chair-definition
package, procedural chair generator and assisted S1 pilot above. The production
generator must use the accepted full-size, parameterised, constituent-part
pattern through a neutral TrackTemplateMacro definition. That pattern is
Templot-source-informed, but neither a Templot schema nor Templot media output
is canonical project data. FreeCAD/OpenCASCADE solids may replace Templot's
low-level DXF face implementation only when the agreed geometric oracle passes.
On 2026-07-20 the project owner also fixed the product destination: an external
Track Template FreeCAD Workbench, packaged as an Addon and intended for Addon
Manager installation. The exact manifest, update and public-catalogue mechanics
remain Phase 10 evidence; the product form no longer does.

The existing B15 five-box S1/S1J body remains legacy gap evidence, not the final
chair model.

Fully automatic conversion of an arbitrary scan or CAD body into an accepted
procedural chair is outside this release candidate. It remains post-RC research
unless a later evidence-backed scope decision promotes it. Other new feature
requests are assessed and scheduled; they do not silently expand the
release-candidate gate.

## Phase control

- Phases are ordered gates, not merely topic headings. Do not retire a legacy path or depend on a later-phase design before its prerequisite gate passes.
- Read-only investigation and bounded throwaway prototypes may occur early when they reduce risk. They do not count as a phase transition or production implementation.
- Each phase closes with a concise evidence record: exact source state, validation run, GUI work still required, performance evidence where applicable, decisions made, open risks, and user acceptance.
- A phase is complete only when all exit criteria are met or the user explicitly accepts a documented exception and its risk.
- Update the status in this document when a phase starts or closes. Do not infer completion from commits alone.
- Mechanical extraction, cleanup, optimisation, behaviour changes, and legacy removal remain separate reviewable changes.
- Apply [TESTING_POLICY.md](TESTING_POLICY.md) to every production change; test exceptions require an explicit risk and closure condition.

## Roadmap summary

| Phase | Outcome | State |
| --- | --- | --- |
| 0 | Recoverable baseline and benchmark checkpoint | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness, and performance inventory | Current |
| 2 | Minimal modular foundation and validation harness | Not started |
| 3 | First parity-proven vertical slice | Not started |
| 4 | Canonical state, signatures, and persistence | Not started |
| 5 | Lightweight editing prototype and renderer decision | Not started |
| 6 | Explicit exact-validation and export seam | Not started |
| 7 | Core alignment, station, and multiple-track migration | Not started |
| 8 | Turnout, crossover, and timbering migration | Not started |
| 9 | Chair definitions, assisted assimilation, production records, and export completion | Not started |
| 10 | Workbench integration, launcher reduction, and beta Addon packaging | Not started |
| 11 | Stabilisation and release-candidate qualification | Not started |

## Phase 0: recoverable baseline and benchmark checkpoint

Status: **Complete — accepted and closed on 2026-07-19.**

### Goal

Make the pre-migration state reproducible, reviewable, and recoverable before production code is moved.

### Deliverables

- Add a conservative `.gitignore` for IDE state, virtual environments, bytecode, generated FreeCAD documents, exports, and temporary benchmark artifacts.
- Preserve B14 as the immutable legacy comparison oracle, qualify B15 as the candidate behavioural reference, and preserve tests, agent guidance, and reference documents in Git without committing generated or IDE-only files.
- Exclude the PyCharm starter `main.py` from the product checkpoint; remove it only with explicit approval.
- Confirm whether `reference/t5_files_556b_06_feb_2025.zip` may be redistributed. If it cannot be committed, record its provenance, purpose, size, and checksum without its contents.
- Record the project licence/attribution status and whether any implementation is derived or translated from the Templot5 source evidence before copying archive code or preparing a public release.
- Record the exact Python/FreeCAD environment and all current version assignments.
- Run the verified syntax, B15 analytical/structural, and FreeCAD headless checks.
- Define at least one reproducible representative workflow recipe and capture a cold full-workflow series plus a valid unchanged-result warm/reuse series using [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).
- Record present validation gaps; passing the current chair-focused checks must not be described as whole-product coverage.
- Review and push an agreed checkpoint commit. Add a checkpoint tag only after the user accepts which version is the behavioural reference.

Current evidence: the exact B14 `XO-001` recipe, preliminary cold run 01, a
like-for-like current-controller three-run cold series and a valid
three-iteration unchanged-result warm-reuse series are preserved in
`reference/benchmarks/`. A tracked reviewed patch reconstructs the pinned bridge
checkout, and an automated isolated FreeCAD builder reconstructs and
semantically validates the ignored nine-object base fixture. The Phase 0
performance item is complete for this defined crossover scope. B15 has also
passed the bounded source-parity, real-GUI, reuse, supported-solid and
save/reopen qualification recorded in
[`benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md`](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
The project owner accepted B15 as the behavioural reference entering Phase 1,
retained B14 as the immutable comparison oracle, selected GPL-3.0-or-later with
the attribution and acknowledgements in `NOTICE.md`, confirmed SourceForge as
the exact ZIP source, and chose to keep the ZIP ignored and untracked. The
decision record is in [PROVENANCE.md](PROVENANCE.md).

### Exit gate

- A fresh checkout plus documented local prerequisites can reproduce the preserved macro and current tests.
- Repository contents and exclusions are explicit; no IDE, cache, generated export, or secret is included.
- Reference provenance and licensing status are explicit, with unresolved material kept out of the checkpoint.
- Current automated checks pass, and any GUI-only baseline work is either recorded or explicitly listed as outstanding.
- At least one cold/warm performance series and its exact input recipe are preserved.
- B14 and B15 roles are unambiguous: B15 is accepted as the behavioural reference and B14 remains the immutable legacy comparison oracle.

Result: **Pass.** Every exit item is complete, the user accepted the evidence
and decisions on 2026-07-19, and the closeout checkpoint is tagged
`phase-0-closeout`.

## Phase 1: product, dependency, correctness, and performance inventory

Status: **Current.**

### Goal

Choose migration order from evidence and establish oracles for behaviour that current automated tests do not cover.

### Deliverables

- Inventory operator workflows, supported inputs, outputs, persisted properties, guided stages, and failure/rollback behaviour.
- Classify top-level definitions by domain, application, FreeCAD adapter, presentation, export, UI, or compatibility responsibility.
- Map important callers, global mutable state, import-time side effects, duplicate definitions, captured aliases, and runtime class patches.
- Document boundary data: units, coordinate frames, tolerances, stable identities, ordering, metadata schemas, cache signatures, and invalidation inputs.
- Profile representative cold and warm workflows and identify measured hotspots separately for calculation, recompute, persistence, display construction, exact geometry, and export.
- Extend the current turnout/crossover timing coverage into a reconciled product-pipeline benchmark for curve/easement, station, multiple-track, editing, Validate, and Export paths before those capabilities are optimised. Test instrumentation and nested-stage accounting so measurement does not change behaviour or double-count time.
- Close or explicitly bound the observed instrumentation defects before using subprofiles to select an optimisation: the geometry external/internal boundary gap, the prematurely persisted chair timing payload, the late supported-solid reuse check, redundant post-reuse panel refresh, and repeated effective-status signature scans.
- Characterise and align crossover preview/commit feasibility diagnostics so preview covers the same complete mapped-turnout and connector minimum-radius rule as transactional commit.
- Add deterministic input recipes or non-sensitive fixtures for release-critical workflows, starting with the gaps listed in [VALIDATION.md](VALIDATION.md).
- Decide the supported FreeCAD/Python baseline and the intended legacy-document
  support window for the release candidate. The initial policy is now recorded
  in `contracts/phase1-compatibility.json`: one exact FreeCAD 1.1.1 Flatpak
  profile is qualified, standalone Python has a 3.12.0 floor, and B14/B15 form
  the outer future migration window. Phase 4 still owns the detector, copied-
  target migrator and per-family fixtures; Phase 10 owns final package metadata
  and broader platform qualification.
- Score candidate first slices by clarity of input/output, current characterisation coverage, side effects, caller count, architectural value, and measurable resource cost.
- Record durable choices in one concise decision log rather than scattering decisions through source comments.
- Establish canonical railway terminology before naming modular interfaces;
  preserve historical evidence identifiers and separately gate any accepted
  macro wording correction.
- Establish the four scoped output-affecting lineage registers defined in
  [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md): first S1 chair path, its
  core rail/timber path, other turnout/crossover output, and legacy B14/B15
  output. Fully classify the first two or keep the S1 pilot blocked; give the
  latter two bounded inventories, current statuses, owners and later closure
  gates rather than making an unbounded historical audit a prerequisite for an
  independently evidenced S1 package. Every affected scope must still close
  before its own output is advertised as project-cleared. Keep GPL source-
  expression compliance separate from the rights basis of generated data and
  media.
- Identify every release-candidate value collection supported only by Templot
  source, a Templot-authored table/profile, or Templot media output. Establish
  an accepted engineering, measurement or separately licensed evidence chain,
  or retain it as `restricted`, `reference-only` or `unknown`; do not launder a
  copied table into nominally independent facts.
- Define the neutral `ChairDefinition` as the only canonical interchange and
  bound any later Templot compatibility work to an optional one-way outward
  adapter. Define the machine-readable package/output dependency manifest and
  its `project-cleared`, `restricted`, `reference-only` and `unknown` statuses.
- Make manifest validation an immediate fail-closed project gate for any
  `project-cleared` package/output. Record registered-design,
  unregistered-design, patent and trade-mark reviews separately from copyright
  and data licensing, and require the prospective DCO plus project data/
  evidence declaration for contributions.
- Audit the Templot5 revision 556b chair-generation route from full-size 2D/3D
  data through constituent component builders, reusable block placement and
  DXF/STL emission. Record relevant routines, units, transforms, manufacturing
  settings and any unimplemented or ambiguous branches without copying code
  into production during the inventory.
- Characterise the current B15 S1/S1J body as a bounded dimensional
  approximation, and obtain or reproducibly generate a frozen Templot S1
  component/assembly oracle suitable for later geometric comparison. If the
  exact oracle cannot yet be generated, record the blocker and the minimum
  evidence needed rather than weakening the gate.
- Define the required boundary data for a versioned chair definition and for
  evidence-led assimilation: constituent identities, full-size source values
  and units, profiles/cross-sections, rail interfaces, prototype versus
  manufacturing parameters, provenance, tolerances, fit residuals and
  acceptance state.
- Confirm the precise prototype designation, evidence ownership, rights chain,
  intended package licence, commercial/publication use, and minimum
  scan/CAD/measurement inputs for the S1 pilot before naming or implementing
  its reusable definition. CC0-1.0 is the default target only for a package
  whose complete rights record permits the project to make that dedication.

Chair analysis/presentation remains a high-payoff later candidate because B15
has focused checks and the controlled chair workflow is exceptionally slow.
The completed cut-boundary scorecard recommended the purer transition solver
as the first architecture pilot. The project owner accepted that selection on
2026-07-20. The fail-closed
[transition-pilot contract](contracts/phase1-transition-pilot.json) reserves
development checkpoint `10.2A8A7B16` and a small `TrackTemplate.FCMacro`
compatibility launcher, while explicitly keeping source movement unstarted and
the public Workbench/RC version undecided.

The Phase 1 compatibility contract also freezes the initial host and ingress
policy without pretending that migration exists. The exact Linux x86_64
FreeCAD 1.1.1 Flatpak stack is the only qualified profile; other platforms or
bundled stacks require the declared requalification matrix. B14-only, B15-only
and expected mixed B14/B15 documents are the intended RC migration sources,
but each entity family remains inspection-only until its Phase 4 copied-target
migration fixture passes. Existing macros and documents are unchanged.

The fixed curved-host crossover mismatch is now characterised under
[`contracts/phase1-crossover-feasibility.json`](contracts/phase1-crossover-feasibility.json).
B14 preview accepts Host A chainage `500.000 mm` although the complete mapped
minimum is `540.848 mm` against the `600.000 mm` request; the documented
`746.298 mm` placement passes at `676.179 mm`. This closes the characterisation
part of the deliverable only. Shared successor preflight, aligned diagnostics,
pre-Part/zero-mutation rejection and broader create/edit/extend GUI evidence
remain required before the deliverable or Phase 1 can close.

The next fixed `XO-001` stage is now bounded by
[`contracts/phase1-crossover-timbering.json`](contracts/phase1-crossover-timbering.json).
It freezes 86 resolved records, 16 shared-envelope records, calculation-input
invalidation, exact Undo/Redo, save/reopen and unchanged reuse. It also
diagnoses, without accepting, B14's persisted-analysis drift, display-only full
rebuild and incomplete cleanup of an untagged object after an injected abort.
Successor fixes, every calculation-input class, real-GUI visibility/history,
other crossover configurations and standalone turnout/plain-line timbering
remain open. Current timber values remain legacy comparison evidence subject
to the other-S&C lineage gate; the contract is not production clearance.

Current Phase 1 evidence is maintained in
[PHASE1_INVENTORY.md](PHASE1_INVENTORY.md). Its first static tranche is
complete: a deterministic, non-executing AST tool records definition
occurrences, provisional responsibilities, callers, aliases, patches,
module-side effects and mutable-state candidates for the exact B14/B15 source
hashes. It shows that the bounded transition-length solver has the lowest
structural coupling, while the better-tested chair core crosses substantial
shadowing and alias chains. Direct B14/B15 transition and station
characterisation now protects the leading calculation boundary. A
machine-readable candidate-boundary register now freezes inputs, outputs,
units, frames, tolerances, identities, ordering, schemas, effects and
signature/invalidation rules for all five static candidates. Its fail-closed
test derives the station and chair record schemas from the exact B14/B15 ASTs
and candidate-register schema 3 records the accepted selection. Within the
analyser's bounded static top-level call model, inventory schema 2
distinguishes root callers from callers crossing the proposed dependency
closure and records dependencies leaving that closure. The resulting
[first-slice scorecard](PHASE1_SLICE_SCORECARD.md) selected the three-function
transition solver as the first architecture pilot, not as a performance
optimisation: it has three external closure callers and no outgoing
project-definition dependency. The exact signatures, constant, expanded
parameter grid, diagnostics, façade/caller route, rollback and profiling gates
are now frozen in
[contracts/phase1-transition-pilot.json](contracts/phase1-transition-pilot.json)
and enforced without importing either macro. Stationing still needs an
explicit point-adapter seam, while chair analysis retains alias coupling, 11
outgoing closure dependencies and known cache-signature gaps. Broader workflow
boundaries, product-pipeline profiles and the remaining Phase 1 user decisions
are still open; package creation and source movement have not started. The
fixed B14
plain-line curve/two-track fixture now also has a read-only
FreeCAD document oracle covering its persisted parameter schema, identities,
grouping, ordered production catalogue and exact-shape summaries. This closes
the fixed create-result characterisation gap. A second isolated recipe now
drives B14's real dialog through left-to-right replacement, the complete
undo/redo stack, explicit change-back, save/reopen, zero-angle rejection and a
deliberately failed transaction after old-output removal. It freezes every
intermediate semantic state, proves exact left/right recovery and preference
separation, and records a comparable three-process edit series. It also
exposes a bounded B14 defect: one replacement is split across geometry,
production-schedule and material-report undo entries, whereas the accepted
successor contract requires one atomic application-command unit. Wider input
boundaries, explicit Validate/deferred reconstruction and the reconciled
product-pipeline profile remain open. A
third isolated recipe now covers B14's
real explicit selected-export dialog for the fixed plain-line fixture:
deterministic DXF/SVG/STL/STEP and CSV,
non-overwrite revisioning, confirmed staged overwrite, parsed output geometry,
and byte-restoring rollback after an injected mid-commit failure. It also
identifies three full exporter-bound probe passes per export action as a
measured hotspot. A fourth isolated recipe covers production export inside the
normal Generate action. It freezes the successful document, all four output
formats and parsed production measures, records a comparable three-process
create-through-export series, and deterministically demonstrates B14's
non-atomic partial output plus contradictory final success wording after the
last planned task fails. This closes the fixed create-time characterisation
gap without accepting either defect as future behaviour. Deferred exact-shape
reconstruction, cancellation, other entity families/scopes and the reconciled
product-pipeline profile remain open. A fifth isolated recipe now covers the
bounded connected-straight and travel-order stationing workflow. It invokes
B14's real entrance/exit pair control, freezes deterministic manager and route
identities, inherited two-track order, exact endpoint/tangent joins, raw
persistence, 23 document objects and 12 production records; edits the two
lengths while preserving curve geometry; and proves complete Undo/Redo and
save/reopen recovery in three fresh processes. The independent-datum GUI,
physical station/platform, straight target-file export, straight-specific
negative paths and wider configurations remain open. A sixth isolated recipe
now covers one centreline-anchored standalone REA C10 turnout lifecycle. It
uses B14's real manager to create `TO-001` left/facing on the persisted Main
Track identity, edits only its hand, freezes the complete 17-object and
10-record document semantics, and proves exact Undo/Redo, save/reopen,
occupied-chainage rejection and in-transaction abort recovery in three fresh
processes. Trailing orientation through the GUI, straight/alternate hosts,
wider input choices, removal/integration, downstream timber/chair stages and
target-file export remain open. This evidence does not close Phase 1 or select
the first extraction slice.

A read-only chair source audit now establishes that Templot5 556b holds
full-size chair data separately from its procedural component-face builders,
reuses named jaw/seat/key blocks, transforms those blocks at calculated
positions, and triangulates derived faces for STL output. B15 uses selected
source dimensions but constructs only a five-box S1/S1J approximation and
explicitly omits keys, loose jaws/plugs and dedicated special-chair solids.
The accepted successor direction is therefore a versioned chair definition
plus one procedural generator, not refinement of the box approximation or
retention of an imported scan as runtime geometry. The detailed audit and
decision are recorded in [PHASE1_INVENTORY.md](PHASE1_INVENTORY.md).

The 2026-07-20 licensing-boundary review now records the Templot5 drawing
notice, distinguishes historical Templot2 and forum-media terms from the
reviewed GPL source snapshot, and finds no general CC BY-NC-SA output licence
in revision 556b. The owner accepted the neutral data, one-way compatibility,
package-licence and generated-output policy in
[LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). This resolves the policy
direction, not positive clearance: current B14/B15 output remains `unknown`
for project-control clearance until its applicable lineage and dependency-
manifest gates are completed.

The licensing-control follow-up now renames the internal positive status to
`project-cleared`, records the project owner's prior acceptance explicitly,
adds a Draft 2020-12 dependency-manifest schema and standard-library fail-
closed validator, requires registered/unregistered-design, patent and trade-
mark review fields, and adds a prospective DCO/data contribution declaration.
The first S1 pilot control manifest validates structurally but deliberately
remains `unknown` and fails `--require-project-cleared` until primary evidence,
permissions, package licence, non-copyright reviews and owner acceptance exist.
The lineage work is now divided into the four owned scopes above rather than
making a complete historical macro audit an implicit prerequisite for S1.

The first two scopes have a bounded machine-readable current-path register
at [lineage/phase1-s1-core-lineage.json](lineage/phase1-s1-core-lineage.json).
It records 16 output-affecting groups with exact B14/B15 source anchors,
dispositions, evidence needs and owners. Nine groups remain `reference-only`
because the present path includes unresolved Templot reference data; source-
expression compliance remains a separate GPL question. Seven remain `unknown`
pending independent evidence or accepted project decisions. Its drift test
verifies both macro fingerprints, literal/function
anchors, the S1 pilot manifest link and, when available, the ignored local
archive and five reviewed active source members. Both scopes therefore take the exit
gate's explicit blocked branch; this evidence neither clears the five-box body
nor selects production S1 values.

The remaining two bounded registers are now housed in
[lineage/phase1-other-snc-legacy-lineage.json](lineage/phase1-other-snc-legacy-lineage.json).
They inventory 14 other-S&C and 10 legacy B14/B15 output-affecting groups,
freeze their current B14/B15 and optional local-upstream anchors, assign all
four owner roles, and state each later output gate. Fourteen groups remain
`reference-only` and ten remain `unknown`; no group is `restricted` or
`project-cleared`, and no other-S&C or legacy output dependency manifest yet
exists. This completes the Phase 1 bounded-register deliverable without
pretending to complete the field-level historical audit. Primary S1 evidence,
the frozen constituent/assembly oracle, output-specific lineage/manifest
closure and the other Phase 1 gates remain open.

The proposed frozen-S1 oracle now has a fail-closed machine-readable capture
contract at
[oracles/templot5-556b-s1-oracle.json](oracles/templot5-556b-s1-oracle.json),
with a standard-library source/executable/DXF/STL inspector and direct contract
test. Nine exact 556b archive members and the four named S1 jaw/seat/key block
routes are fingerprinted. The installed local Templot5 candidate is
deterministically rejected as version 5.55a, while a clean native source-build
probe is blocked by Windows units and external HtmlViewer/Synapse inputs not
contained in the ZIP. The recipe therefore takes the deliverable's explicit
blocker branch: an exact provenance-recorded 556b executable, disposable
profile, frozen S1-only fixture, effective-settings record and local DXF/STL
capture are the minimum remaining evidence. This defines the recipe without
claiming that the exact oracle exists or relaxing its revision gate.

The detailed 556b value/unit/frame/transform branch is now recorded in
[lineage/templot5-556b-s1-generation-map.json](lineage/templot5-556b-s1-generation-map.json)
and protected by a source-drift test. The exact Lazarus project establishes
`math_unit.pas`, `pad_unit.pas`, `chairs_unit.pas`, `dxf_unit.pas` and
`custom_3d_unit.pas` as the mapped active route; the similarly named `_x` files
are fingerprinted inactive alternates, not executable-path evidence. The map
separates eight value groups, four coordinate frames, nine generation stages,
five S1 assembly constituents and seven manufacturing/output branch groups. It
also records every current
finding and keeps all mapped Templot material `reference-only`. This completes
the source-generation-map branch subject to owner review; it does not provide
the missing exact artifact oracle, independently evidenced S1 values or a
production ChairDefinition, and it does not close Phase 1.

The existing performance evidence is now reconciled through the fail-closed
[performance-boundary contract](contracts/phase1-performance-boundaries.json).
It classifies nine controlled legacy profiles by their real operator, nested,
harness and cache/process boundaries; enforces per-run reconciliation before
medians; and explicitly bounds all five observed instrumentation defects
without calling them fixed. Four target slots—lightweight Edit, explicit
Validate, export from validated state and complete edit-through-export—remain
`not-implemented-unmeasured`. The current evidence can identify the chair chain
and repeated export probing as dominant legacy costs, but no current timing is
an accepted budget or authority to select a target-code optimisation. Phase 1
therefore remains open.

Canonical **plain line** terminology and the compatibility treatment of the
legacy `ordinary-*` evidence identifiers are now recorded in
[TERMINOLOGY.md](TERMINOLOGY.md). B14/B15 remain byte-identical; user-facing
macro wording is deferred to an approved successor version.

### Exit gate

- Every release-critical workflow has an owner document/recipe, known oracle, and stated coverage gap.
- The dependency and side-effect map is sufficient to predict the callers and state touched by the first extraction.
- Representative profiles identify the dominant costs; the project is not optimising from source size alone.
- The first slice, its legacy comparison path, and its exact acceptance evidence are agreed.
- The Templot chair-generation map, B15 gap statement, proposed S1 oracle
  recipe and chair-definition/assimilation boundary requirements are reviewed;
  any missing source or measurement evidence has a named owner and gate.
- The first S1 and its core rail/timber source/data maps are classified at the
  smallest practical field/component granularity or remain visibly blocked;
  other S&C and legacy B14/B15 have bounded registers, current statuses, named
  owners and later closure gates. Every Templot-only, restricted,
  reference-only, unknown or `NOASSERTION` dependency has a named disposition
  and cannot be mistaken for a project-cleared production input.
- The neutral chair-definition boundary, optional one-way Templot adapter,
  package-licence rule, dependency-manifest schema/validator, non-copyright-
  rights fields, contribution declaration and first S1 evidence/rights plan are
  reviewed and accepted.
- RC chair scope is bounded to validated definition packages and one assisted
  S1 pilot; arbitrary automatic scan conversion is not an implicit exit
  requirement.
- Open risks and required user decisions are recorded.

## Phase 2: minimal modular foundation and validation harness

### Goal

Prove that modular source can load through both standalone Python and FreeCAD without changing product behaviour.

### Deliverables

- Create only the `tracktemplate` package locations required by the chosen slice.
- Use canonical `plain_line` naming in new domain and API surfaces; translate
  legacy `ordinary_track` identifiers only at an explicit compatibility
  boundary.
- Establish a narrow `tracktemplate.api` façade and an explicit FreeCAD composition root.
- Keep B14 and B15 byte-identical. Introduce the reserved
  `TrackTemplate.FCMacro` only as a small `10.2A8A7B16` development composition
  root while removing no legacy behaviour; it must not contain another
  maintained copy of the monolith.
- Add a domain import test that fails if FreeCAD, Part, Qt, pivy, or exporter dependencies enter the domain boundary.
- Add boundary checks for dependency direction and circular imports using the standard library or already-approved tooling.
- Provide a deterministic legacy/new comparison harness capable of structured values, ordering, stable identities, diagnostics, and output metadata.
- Confirm the chosen record/type strategy works in the supported FreeCAD Python runtime.
- Make the B16 development composition path consume the Phase 1 compatibility
  contract and stop with a recoverable diagnostic before mutation when the
  host is unqualified. Do not implement the document migrator or final Addon
  manifest in this phase.
- Document how the modular package is found when launched from the FreeCAD macro environment.

### Exit gate

- A clean standalone Python process imports the domain/API boundary without FreeCAD or Qt.
- The launcher loads the package in the supported FreeCAD environment.
- Existing B14/B15 workflows remain unchanged and current validation still passes.
- No empty speculative package tree, circular dependency, new runtime dependency, or hidden global service has been introduced.

## Phase 3: first parity-proven vertical slice

### Goal

Prove the extraction method on one bounded capability before generalising the architecture.

### Deliverables

- Strengthen characterisation tests for the selected inputs, outputs, errors, ordering, identities, cache behaviour, and side effects.
- Extract the pure calculation mechanically, keeping names, formulae, tolerances, and ordering unchanged.
- Route legacy callers through the narrow façade while retaining a temporary comparison path.
- Add its application command and only the adapter boundary needed to exercise it end to end.
- Compare legacy and modular results over representative and edge-case inputs.
- Establish structural and performance measurements for the slice without combining extraction with optimisation.
- Perform cleanup or optimisation only in separate changes after parity is demonstrated.

### Exit gate

- The capability follows the target dependency direction and its domain portion imports without FreeCAD/Qt.
- Legacy/new analytical records, findings, stable identities, ordering, and relevant metadata are equivalent.
- Cache miss, valid reuse, and all relevant invalidation cases pass.
- FreeCAD/headless and GUI checks pass where the selected path touches them.
- Any temporary dual path has an owner and a named retirement gate.

## Phase 4: canonical state, signatures, and persistence

### Goal

Make parametric railway intent—not preview or exact shape data—the durable source of truth.

### Deliverables

- Define canonical domain/application records for the migrated slice with explicit units, frames, tolerances, identities, and deterministic ordering.
- Define the cross-cutting, versioned chair-definition contract before any new
  production chair builder depends on it. It must cover constituent components,
  source values/units, rail interfaces, procedural profiles, prototype and
  manufacturing variants, provenance, tolerances, validation state and stable
  package/component identities without embedding `Part` shapes or meshes. Its
  schema must carry the field/component classifications, licence or
  `NOASSERTION` state, intended output/redistribution use and acceptance record
  required by [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md).
- Define versioned serialisation and migration rules for persisted payloads and FreeCAD properties.
- Centralise complete analysis, preview, validation, and export signatures and dirty-state propagation.
- Implement FreeCAD transactions, undo/redo intent, save/reopen, failure recovery, and stale-result rejection at the adapter boundary.
- Store compact canonical data and accepted analytical results; do not persist redundant renderer geometry or transient production shapes.
- Test supported legacy-document migration and reject unsupported/corrupt state with a recoverable diagnostic.

### Exit gate

- The selected slice round-trips through save/reopen without result or identity drift.
- Parameter edits invalidate exactly the affected derived results, including cold/reuse/change-back cases.
- Undo/redo and failed updates leave a valid document.
- Preview and exact geometry can be deleted and regenerated solely from canonical state.
- A chair-definition package round-trips deterministically and rejects missing,
  corrupt, unsupported or ambiguous required data with recoverable diagnostics;
  production geometry is not required to be persisted in that package.
- The supported schema/version window is agreed and tested.

## Phase 5: lightweight editing prototype and renderer decision

### Goal

Choose the normal editing representation from measured FreeCAD behaviour and usable editing semantics.

### Deliverables

- Define a renderer-neutral preview scene containing semantic layers, styles, stable domain identities, and edit-handle intent.
- Prototype the leading Coin ViewProvider approach and, if still credible, an embedded SVG/Qt approach against the same selected slice and input.
- Demonstrate visibility, selection-to-domain mapping, parameter editing, undo/redo, close/reopen, and signature invalidation.
- Measure generation/update time, persistent object count, recomputes, memory growth, and interactive responsiveness against the legacy path.
- Verify that arbitrary visual-path edits cannot silently diverge from the canonical parametric model.
- Record the renderer decision, rejected alternative, evidence, limitations, and any retained direct-SVG export role.

### Exit gate

- One renderer is accepted for production migration using correctness, editing, FreeCAD integration, maintainability, and measured resource evidence.
- The preview uses a small logical object/layer count and maps selections deterministically to domain identities.
- Normal edits do not construct dense exact `Part` geometry.
- The user accepts the editing behaviour and its documented limitations.

## Phase 6: explicit exact-validation and export seam

### Goal

Prove that exact geometry can be deferred without reducing production validation or merely hiding total cost.

### Deliverables

- Implement an explicit Validate request for the selected slice using current canonical and analytical signatures.
- Build only required exact geometry in a temporary/isolated scope and guarantee cleanup on success, cancellation, and failure.
- Refuse export when the applicable exact validation is absent or stale.
- Exercise transactional staging, scale/bounds/topology checks, manifests, overwrite handling, commit, and rollback.
- Generate and validate the output-dependency record without describing an
  export as `project-cleared` when an output-affecting package or material is
  restricted, reference-only, unknown, or `NOASSERTION` for the intended use.
- Compare legacy/new exact bounds, lengths, profiles, topology, solids/meshes, identifiers, filenames, categories, and manifests as applicable.
- Measure edit-only and edit-through-export workflows, including transient construction and cleanup costs.
- Allow direct SVG/DXF generation from canonical 2D records only where equivalence and production checks are proven.
- Require chair exact-geometry work, whenever it first crosses this seam, to
  consume the canonical definition and construct named constituent B-reps. A
  retained scan/mesh or the B15 rectangular envelope cannot satisfy this seam.

### Exit gate

- The selected slice has equivalent exact validation and production output for its agreed scope.
- No transient production objects leak into the editable document.
- Export is deterministic and failure-safe.
- Editing resource use improves beyond normal noise, with complete end-to-end cost reported.
- The legacy path remains available until parity evidence and user acceptance permit its removal.

## Phase 7: core alignment, station, and multiple-track migration

### Goal

Migrate the mathematical and data foundations on which special trackwork depends.

### Deliverables

- Migrate remaining plain-line curve, easement, straight, alignment,
  station/chainage, spacing-transition, and multiple-track calculations in
  bounded slices.
- Migrate track/platform preparation where it is part of the accepted workflow.
- Extend canonical identities, signatures, persistence, preview, exact validation, and export contracts for each family.
- Add representative normal, boundary, reverse-direction, multi-track, and tolerance-sensitive fixtures.
- Remove each legacy family only after its own analytical, GUI, exact-output, and performance gates pass.

If the Phase 3 proof slice belongs to this family, reuse it as the first completed sub-slice rather than reimplementing it.

### Exit gate

- Core layouts can be created, edited, saved, reopened, validated, and exported through modular paths.
- Accepted B14/B15 geometry, station mapping, identities, ordering, and metadata remain equivalent.
- Domain calculations for this family have no FreeCAD/Qt dependency or reverse adapter import.
- Legacy core-layout paths have either been safely retired or have a documented blocker and removal gate.

## Phase 8: turnout, crossover, and timbering migration

### Goal

Migrate special trackwork and its topology-sensitive integration on the proven foundation.

### Deliverables

- Migrate REA C10 turnout geometry, host relationships, editing, and exact-validation behaviour.
- Migrate straight- and curved-host crossovers, topology relationships, conflict/finding rules, and stable identities.
- Migrate automatic timbering, extension/resolution rules, and associated diagnostics.
- Cover representative handedness, orientation, host curvature, spacing, failure, rollback, and tolerance cases.
- Apply the accepted lightweight preview and transient exact-geometry contracts rather than inventing feature-specific rendering paths.

### Exit gate

- Turnouts and crossovers retain accepted geometry, topology, timber decisions, identities, findings, and production records.
- Creation, parameter editing, selection, undo/redo, save/reopen, validation, and export pass in the real GUI.
- Straight- and curved-host representative workflows pass deterministic comparison.
- No special-trackwork rule has leaked into the renderer or FreeCAD persistence adapter.

## Phase 9: chair definitions, assisted assimilation, production records, and export completion

### Goal

Complete production-detail migration, deliver reusable procedural chair
definitions and the bounded S1 assimilation pilot, and prove every supported
output family from canonical records.

### Deliverables

- Complete chair/support analysis, assignment, representation, stable identities, and cache invalidation across migrated trackwork.
- Implement one definition-driven procedural chair generator using the
  accepted source-informed constituent pattern through the neutral project
  schema: full-size source dimensions and explicit profiles/cross-sections
  produce named base/plinth, seat, jaw, rib, fillet, key and applicable
  fastening/interface components; reusable prototypes are then transformed
  into calculated track positions.
- Permit FreeCAD/OpenCASCADE B-rep construction in place of Templot's DXF
  `3DFACE` mechanics, while proving agreed dimensional, component, interface,
  topology and assembled-output equivalence against the frozen S1 oracle.
- Load, validate and version external chair-definition packages without making
  their source scan/CAD files or any third-party fitting tool a normal runtime
  dependency.
- Build the release-candidate S1 definition only from accepted engineering
  facts, project measurements, project derivations, or separately licensed
  evidence whose commercial/publication and redistribution use is explicit.
  Keep Templot reference data and media outside the canonical package; use a
  frozen Templot S1 artifact only as a local comparison oracle unless its exact
  redistribution terms are separately accepted.
- Deliver one operator-assisted S1 assimilation pilot. Record source
  calibration, component/landmark decisions, inferred and unresolved values,
  regenerated-versus-source residuals, rail fit, field/component
  classifications, licences, intended output use, provenance and explicit
  acceptance. Use the same generator and package schema as native definitions.
- Keep full-size prototype geometry separate from model scale, rail-fit policy
  and printer/material compensation, and test their signatures independently.
- Complete production-record planning and deterministic category/manifest
  generation, including machine-readable package and output-affecting rights
  dependencies.
- Validate supported SVG, DXF, STL, STEP, and retained-FreeCAD-object paths, limited to the formats confirmed in Phase 1 scope.
- Exercise scale, planarity, bounds, solid/mesh validity, filename collisions, overwrite policy, staging, rollback, cancellation, and cleanup.
- Replace any remaining per-element persistent display or production objects with accepted layered presentation or transient construction.

If chair analysis/presentation was the Phase 3 proof slice, this phase completes its integration across all track families and exporters rather than repeating the extraction.

### Exit gate

- Every release-candidate production format has deterministic repeat evidence
  for representative inputs. Preserved B14/B15 behaviour has legacy/new
  equivalence evidence; the deliberately new procedural chair geometry has
  accepted definition/reference-oracle evidence instead of five-box equality.
- Timber/chair decisions and record identities remain stable across edit, save/reopen, validation, and export.
- The accepted S1 definition regenerates all in-scope constituent parts and the
  assembled chair without the original source scan/CAD file or retained
  FreeCAD geometry; no five-box or opaque-mesh fallback can be labelled
  production-ready.
- Definition package load/round-trip, corrupt/unsupported rejection, component
  identities, prototype/manufacturing separation, rail fit and S1
  regenerated-versus-reference tolerances pass in standalone and FreeCAD tests.
- The assisted S1 pilot is documented and accepted; arbitrary automatic scan
  assimilation remains explicitly outside the RC qualification matrix.
- The accepted S1 package has an explicit licence and no `NC`, `NOASSERTION`,
  reference-only, unknown, or otherwise incompatible dependency in the
  project-cleared commercial/publication path. Any raw evidence that cannot be
  redistributed remains separate and its permitted fitting/use basis is
  recorded.
- Representative output manifests reproduce the complete package/dependency
  classification and cannot claim `project-cleared` after any relevant input is
  replaced by a restricted or unresolved source.
- Export failure cannot partially replace an accepted output set or corrupt the editable model.
- Editing and end-to-end performance meet the provisional budgets derived from measured baselines.

## Phase 10: Workbench integration, launcher reduction, and beta Addon packaging

### Goal

Turn the migrated capabilities into one maintainable, installable,
feature-complete Track Template Workbench beta.

### Deliverables

- Move guided workflow and UI composition out of the monolithic `run_macro` body into explicit commands/view models.
- Replace import-time class patch chains and shadowed active definitions with normal composition; retain only named compatibility migrations.
- Reduce the `.FCMacro` to an optional startup/compatibility entry point that
  delegates to authoritative modular source, or retire it when the supported
  migration window permits.
- Assemble the accepted external FreeCAD Workbench as an Addon, including its
  metadata/manifest, resources, loading entry points and reproducible package.
- Prove clean direct and Addon Manager installation/loading/update paths in the
  supported FreeCAD environment; treat public catalogue submission as a
  separately authorised publication step.
- Complete supported legacy-document migration, diagnostics, and recovery guidance.
- Add installation, upgrade, workflow, Validate/Export, troubleshooting, and known-limitation documentation.
- Document chair-definition package authoring/loading, the assisted S1
  assimilation workflow, evidence/provenance requirements, per-package licence,
  output-dependency/project-status interpretation, and the boundary between the RC
  capability and post-RC automatic-conversion research.
- Freeze release-candidate feature scope and public schema/API surfaces at beta exit.

### Exit gate

- All agreed release-candidate capabilities run through modular source; no unowned production path depends on historical monkey patches.
- The Workbench loads the authoritative package; any retained launcher contains
  composition/startup only, and the Addon artifact cannot drift from source.
- Clean install, first run, normal workflow, save/reopen, and upgrade paths pass.
- Full automated, headless, GUI, export, and performance matrices have no untriaged failure.
- The beta is feature-complete; subsequent changes are limited to release blockers, defects, evidence, and documentation.

## Phase 11: stabilisation and release-candidate qualification

### Goal

Produce a reproducible RC1 artifact whose remaining risks are known and acceptable.

### Deliverables

- Freeze candidate source, schema, public API, workflow scope, supported
  environment, Addon artifact and distribution mechanics.
- Run the full validation matrix from a clean checkout and clean FreeCAD profile/install where practical.
- Complete real-GUI acceptance for all representative workflows and supported legacy-document upgrades.
- Run repeated cold and warm performance series; publish medians/ranges and confirm the agreed editing and end-to-end budgets.
- Run deterministic export comparisons and failure/rollback/cleanup tests for every supported production format.
- Qualify the accepted external chair-definition package and S1 assimilation
  fixture from a clean installation without access to development-only source
  evidence or retained generated shapes.
- Re-run the production-data/output-lineage audit against the frozen artifact;
  verify package licences, dependency manifests, embedded notices, and the
  absence of unresolved or non-commercial material from every path advertised
  as project-cleared for commercial/publication use.
- Resolve all release-blocking defects and explicitly disposition lower-severity known limitations.
- Finalise version assignments, change log, installation/upgrade notes, licences/notices, artifact contents, and checksums.
- Build the artifact twice from the same source and verify reproducibility or document any unavoidable environment-specific difference.
- Preserve the previous accepted checkpoint and a tested rollback/recovery route.

### Release-candidate gate

- Zero known correctness, data-loss, document-corruption, migration-corruption, or production-export defects in supported workflows.
- Zero open blocker/critical defects; any accepted lesser issue is documented with impact and workaround.
- No release-critical workflow is represented only by an unperformed test.
- All required automated, FreeCAD headless, real-GUI, persistence, exact-output, rollback, and performance checks pass.
- The artifact installs and runs from its documented package without relying on the development checkout.
- Version, source commit, build inputs, artifact checksum, validation evidence, and known limitations are traceable.
- The user explicitly accepts the evidence and authorises creation/publication of the release candidate.

Passing this gate produces a release candidate, not an automatic stable release.

## Slice definition of done

Every migrated capability, including those inside the larger Phase 7–9 waves, must have:

1. an explicit scope, legacy oracle, callers, inputs, outputs, invariants, and side effects;
2. characterisation coverage before movement and change-specific evidence satisfying [TESTING_POLICY.md](TESTING_POLICY.md);
3. a mechanical extraction separated from cleanup and optimisation;
4. domain code free of FreeCAD/Qt and adapter back-imports;
5. legacy/new equality for results, identities, ordering, findings, and relevant metadata;
6. cache miss, reuse, invalidation, and change-back evidence;
7. applicable headless FreeCAD, GUI, save/reopen, exact-output, and rollback evidence;
8. cold/warm performance evidence for affected operator paths;
9. a recorded owner and removal gate for every temporary compatibility path;
10. a recorded classification and output-dependency disposition for every new
    or changed source value, package, fixture, or asset that can affect
    production output; and
11. user acceptance before behaviourally significant legacy code is retired.

For a chair-definition or chair-generator slice, definition-package
round-trip, constituent identity, prototype/manufacturing separation,
procedural regeneration, rail-fit and reference/residual evidence are also
mandatory. Legacy equality still applies to preserved chair assignment,
analysis, editing, persistence and export behaviour; it does not require the
accepted procedural geometry to reproduce B15's approximate box body. A chair
slice cannot be accepted for the project-cleared production path until its
package licence and field/component provenance pass
[LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md).

## Scheduled decision gates

| Decision | Due no later than | Evidence required |
| --- | --- | --- |
| B14/B15 behavioural reference and checkpoint tag | Resolved at Phase 0 exit — B15 accepted; B14 retained as immutable oracle; `phase-0-closeout` tag | Validation plus representative GUI comparison |
| Reference ZIP commit/provenance policy | Resolved at Phase 0 exit — exact SourceForge origin recorded; ZIP ignored and untracked | Owner decision, upstream GPLv3 statement and checksum |
| Source/data/output classification policy | Resolved 2026-07-20 — neutral canonical data, one-way optional Templot adapter, package-specific licensing and no automatic project claim over ordinary output | Archive/output-notice review, GPL/CC scope review, `LICENSING_BOUNDARIES.md`, and owner acceptance |
| Chair geometry method and RC scope | Resolved 2026-07-20 — full-size procedural constituent generation, validated external packages and one assisted S1 pilot; arbitrary automatic conversion remains post-RC research | Templot source audit and project-owner acceptance |
| Scoped output lineage and first S1 package rights plan | Phase 1 exit | Complete first-S1/core-rail-timber classifications or an explicit S1 block; bounded other-S&C and legacy registers; validated manifest, B15 gap analysis, pilot evidence/licence, non-copyright review, intended commercial/publication use and comparison metrics |
| First extraction slice | Resolved 2026-07-20 — transition-length solver selected as the architecture pilot; B16/launcher and exact acceptance contract reserved; source movement not started | Candidate contracts, bounded closure cuts, workflow profiles, scorecard and owner acceptance |
| Remaining representative fixtures and Phase 1 profile coverage | Phase 1 exit | Coverage, workflow gaps and reconciled target-architecture profile inventory |
| Supported FreeCAD/Python and legacy document window | Initial policy defined 2026-07-20; owner review at Phase 1 exit and implementation/family fixtures due by Phase 4 | Exact runtime probe, official Addon metadata fields, B14/B15 source/schema anchors, existing save/reopen evidence, fail-closed contract validation and future migration fixtures |
| Domain record and persistence schema strategy | Phase 4 exit | Runtime compatibility and round-trip tests |
| Coin ViewProvider versus SVG/Qt editing view | Phase 5 exit | Selection, editing, persistence, and resource prototype |
| Numerical performance budgets | Provisional after Phase 1; frozen by Phase 10 | Repeated cold/warm representative baselines |
| RC product/distribution target | Resolved 2026-07-20 — external Track Template FreeCAD Workbench packaged as an Addon and intended for Addon Manager installation; modular package authoritative; macro limited to migration/compatibility | Project-owner acceptance and FreeCAD's Workbench/Addon ecosystem model |
| RC version identifier and publication | Phase 11 | Complete qualification evidence and user approval |

## Principal risks and controls

| Risk | Control |
| --- | --- |
| Current tests over-represent the B15 chair path | Add workflow recipes and characterisation oracles before moving each uncovered family |
| The B15 five-box body is mistaken for final procedural chair geometry | Label it as legacy gap evidence; require the versioned constituent definition and S1 oracle before production acceptance |
| Scan/CAD evidence is mistaken for authoritative reusable geometry | Keep source files outside canonical runtime state; require calibrated fitting into a validated definition, residual reporting and explicit acceptance |
| A scan cannot reveal nominal, hidden, worn or rail-fit geometry | Require measurements/drawings and operator landmarks, preserve unresolved findings, and reject unsupported confidence rather than inventing dimensions |
| Chair assimilation introduces heavy or proprietary normal-runtime dependencies | Isolate optional readers/fitting tools at adapters, approve dependencies separately, and keep definition loading/generation usable without the original tool |
| Imported chair evidence has unclear ownership or licence | Require per-package provenance, hashes and usage/redistribution status before inclusion or publication |
| Templot source licensing is conflated with a blanket licence on all generated output | Keep GPL source compliance, data/database provenance, media notices and output dependencies separate under `LICENSING_BOUNDARIES.md`; do not infer CC BY-NC-SA from the reviewed snapshot |
| A systematically copied table or profile is relabelled as isolated engineering facts | Require field/component provenance and an accepted independent engineering, measurement or separately licensed evidence chain before canonical admission |
| A non-commercial, unknown or reference-only chair dependency reaches a path advertised for magazine/commercial use | Propagate dependency status into manifests and prohibit `project-cleared` qualification until the dependency is replaced or separately permitted |
| Duplicate definitions and runtime patches hide live callers | Inventory captured aliases and patch order; remove only after retained-reference audits |
| Modularisation increases files without reducing runtime cost | Treat source boundaries and representation/performance changes as separate measured outcomes |
| Lightweight editing loses expected FreeCAD behaviour | Prototype selection, handles, visibility, undo/redo, save/reopen, and GUI use before choosing a renderer |
| Deferred geometry only moves cost to export | Measure both edit-only and edit-through-export workflows, including cleanup |
| Cache signatures omit an input | Centralise signatures and test change/reuse/change-back for every input class |
| New persistence makes old documents unreadable | Enforce the recorded B14/B15 ingress window, retain source documents byte-for-byte, migrate only into a copied/new target, version schemas, and test every supported family plus unsupported/corrupt recovery |
| Legacy and modular paths become permanent duplication | Give every comparison path a named retirement gate and review it at each phase close |
| Distribution artifact drifts from modular source | Generate or assemble it reproducibly and compare it with the authoritative package |
| Feature additions destabilise migration | Triage them against the RC scope; schedule separately unless required for correctness |
| Reference-source provenance or licence later becomes ambiguous | Preserve the exact SourceForge URL/checksum, GPL-3.0-or-later licence, notices, and local exclusion decision |

## Phase 0 closeout record

1. Preserve and validate the fresh-checkout bridge patch and deterministic base-fixture builder. **Complete and committed.**
2. Capture two more equivalent B14 cold-process runs and report the three-run median/range. **Complete and committed.**
3. Define an unchanged-result warm/reuse recipe, then capture three comparable warm runs without replaying destructive construction as a false cache test. **Complete and committed.**
4. Record B14/B15 behavioural acceptance status. **Complete — B15 accepted as
   the behavioural reference; B14 retained as the immutable legacy oracle.**
5. Resolve the reference ZIP redistribution and project licence/provenance
   decisions. **Complete — exact SourceForge origin recorded,
   GPL-3.0-or-later selected, `NOTICE.md` added, and the ZIP remains ignored.**
6. Review, commit and push of checkpoint `7379eb4` are complete. **Final Phase 0
   closeout commit, tag, and push authorised by the project owner on
   2026-07-19.**
