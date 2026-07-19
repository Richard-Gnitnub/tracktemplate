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
- [PROVENANCE.md](PROVENANCE.md) records reference-source identity, source
  relationship, redistribution and licensing status.
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
- compact, versioned FreeCAD persistence with tested save/reopen and supported legacy migration;
- deterministic, transactional exports and manifests;
- a small launcher/composition root and one authoritative modular implementation;
- reproducible installation or distribution artifacts, validation evidence, user documentation, and measured performance budgets;
- no known release-blocking correctness, data-loss, migration, or production-export defect in the supported scope.

Release-candidate scope is based on the accepted B15 behavioural reference, with B14 retained as the immutable legacy comparison oracle. New feature requests are assessed and scheduled; they do not silently expand the release-candidate gate.

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
| 9 | Chair, production-record, and export completion | Not started |
| 10 | Product integration, launcher reduction, and beta packaging | Not started |
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
- Decide the supported FreeCAD/Python baseline and the intended legacy-document support window for the release candidate.
- Score candidate first slices by clarity of input/output, current characterisation coverage, side effects, caller count, architectural value, and measurable resource cost.
- Record durable choices in one concise decision log rather than scattering decisions through source comments.

Chair analysis/presentation is a strong candidate because B15 already has focused checks. Curve/easement calculation is strategically foundational and may be purer. Neither is selected until this inventory exposes its real coupling.

Current Phase 1 evidence is maintained in
[PHASE1_INVENTORY.md](PHASE1_INVENTORY.md). Its first static tranche is
complete: a deterministic, non-executing AST tool records definition
occurrences, provisional responsibilities, callers, aliases, patches,
module-side effects and mutable-state candidates for the exact B14/B15 source
hashes. It shows that the bounded transition-length solver has the lowest
structural coupling, while the better-tested chair core crosses substantial
shadowing and alias chains. Direct B14/B15 transition and station
characterisation now protects the leading calculation boundary. This is not
yet a slice decision: end-to-end workflow oracles, boundary contracts,
product-pipeline profiles and the remaining Phase 1 user decisions are still
open.

### Exit gate

- Every release-critical workflow has an owner document/recipe, known oracle, and stated coverage gap.
- The dependency and side-effect map is sufficient to predict the callers and state touched by the first extraction.
- Representative profiles identify the dominant costs; the project is not optimising from source size alone.
- The first slice, its legacy comparison path, and its exact acceptance evidence are agreed.
- Open risks and required user decisions are recorded.

## Phase 2: minimal modular foundation and validation harness

### Goal

Prove that modular source can load through both ordinary Python and FreeCAD without changing product behaviour.

### Deliverables

- Create only the `tracktemplate` package locations required by the chosen slice.
- Establish a narrow `tracktemplate.api` façade and an explicit FreeCAD composition root.
- Keep the working macro as the launcher while removing no legacy behaviour.
- Add a domain import test that fails if FreeCAD, Part, Qt, pivy, or exporter dependencies enter the domain boundary.
- Add boundary checks for dependency direction and circular imports using the standard library or already-approved tooling.
- Provide a deterministic legacy/new comparison harness capable of structured values, ordering, stable identities, diagnostics, and output metadata.
- Confirm the chosen record/type strategy works in the supported FreeCAD Python runtime.
- Document how the modular package is found when launched from the FreeCAD macro environment.

### Exit gate

- A clean ordinary-Python process imports the domain/API boundary without FreeCAD or Qt.
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
- Compare legacy/new exact bounds, lengths, profiles, topology, solids/meshes, identifiers, filenames, categories, and manifests as applicable.
- Measure edit-only and edit-through-export workflows, including transient construction and cleanup costs.
- Allow direct SVG/DXF generation from canonical 2D records only where equivalence and production checks are proven.

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

- Migrate remaining curve, easement, straight, alignment, station/chainage, spacing-transition, and multiple-track calculations in bounded slices.
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

## Phase 9: chair, production-record, and export completion

### Goal

Complete production-detail migration and prove every supported output family from canonical records.

### Deliverables

- Complete chair/support analysis, assignment, representation, stable identities, and cache invalidation across migrated trackwork.
- Complete production-record planning and deterministic category/manifest generation.
- Validate supported SVG, DXF, STL, STEP, and retained-FreeCAD-object paths, limited to the formats confirmed in Phase 1 scope.
- Exercise scale, planarity, bounds, solid/mesh validity, filename collisions, overwrite policy, staging, rollback, cancellation, and cleanup.
- Replace any remaining per-element persistent display or production objects with accepted layered presentation or transient construction.

If chair analysis/presentation was the Phase 3 proof slice, this phase completes its integration across all track families and exporters rather than repeating the extraction.

### Exit gate

- Every release-candidate production format has deterministic repeat and legacy-equivalence evidence for representative inputs.
- Timber/chair decisions and record identities remain stable across edit, save/reopen, validation, and export.
- Export failure cannot partially replace an accepted output set or corrupt the editable model.
- Editing and end-to-end performance meet the provisional budgets derived from measured baselines.

## Phase 10: product integration, launcher reduction, and beta packaging

### Goal

Turn the migrated capabilities into one maintainable, installable, feature-complete beta.

### Deliverables

- Move guided workflow and UI composition out of the monolithic `run_macro` body into explicit commands/view models.
- Replace import-time class patch chains and shadowed active definitions with normal composition; retain only named compatibility migrations.
- Reduce the `.FCMacro` to startup/composition or generate it reproducibly from authoritative modular source.
- Decide and automate the release distribution: launcher plus package, installable module/workbench, or generated bundle.
- Prove a clean installation and loading path in the supported FreeCAD environment.
- Complete supported legacy-document migration, diagnostics, and recovery guidance.
- Add installation, upgrade, workflow, Validate/Export, troubleshooting, and known-limitation documentation.
- Freeze release-candidate feature scope and public schema/API surfaces at beta exit.

### Exit gate

- All agreed release-candidate capabilities run through modular source; no unowned production path depends on historical monkey patches.
- The launcher contains composition/startup only, and the distribution artifact cannot drift from source.
- Clean install, first run, normal workflow, save/reopen, and upgrade paths pass.
- Full automated, headless, GUI, export, and performance matrices have no untriaged failure.
- The beta is feature-complete; subsequent changes are limited to release blockers, defects, evidence, and documentation.

## Phase 11: stabilisation and release-candidate qualification

### Goal

Produce a reproducible RC1 artifact whose remaining risks are known and acceptable.

### Deliverables

- Freeze candidate source, schema, public API, workflow scope, supported environment, and distribution format.
- Run the full validation matrix from a clean checkout and clean FreeCAD profile/install where practical.
- Complete real-GUI acceptance for all representative workflows and supported legacy-document upgrades.
- Run repeated cold and warm performance series; publish medians/ranges and confirm the agreed editing and end-to-end budgets.
- Run deterministic export comparisons and failure/rollback/cleanup tests for every supported production format.
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
10. user acceptance before behaviourally significant legacy code is retired.

## Scheduled decision gates

| Decision | Due no later than | Evidence required |
| --- | --- | --- |
| B14/B15 behavioural reference and checkpoint tag | Resolved at Phase 0 exit — B15 accepted; B14 retained as immutable oracle; `phase-0-closeout` tag | Validation plus representative GUI comparison |
| Reference ZIP commit/provenance policy | Resolved at Phase 0 exit — exact SourceForge origin recorded; ZIP ignored and untracked | Owner decision, upstream GPLv3 statement and checksum |
| Representative fixtures and first extraction slice | Phase 1 exit | Coverage, coupling, side-effect, and profile inventory |
| Supported FreeCAD/Python and legacy document window | Phase 1/4 | Environment evidence and migration fixtures |
| Domain record and persistence schema strategy | Phase 4 exit | Runtime compatibility and round-trip tests |
| Coin ViewProvider versus SVG/Qt editing view | Phase 5 exit | Selection, editing, persistence, and resource prototype |
| Numerical performance budgets | Provisional after Phase 1; frozen by Phase 10 | Repeated cold/warm representative baselines |
| RC distribution format | Phase 10 start | Loading, maintainability, deployment, and reproducibility spike |
| RC version identifier and publication | Phase 11 | Complete qualification evidence and user approval |

## Principal risks and controls

| Risk | Control |
| --- | --- |
| Current tests over-represent the B15 chair path | Add workflow recipes and characterisation oracles before moving each uncovered family |
| Duplicate definitions and runtime patches hide live callers | Inventory captured aliases and patch order; remove only after retained-reference audits |
| Modularisation increases files without reducing runtime cost | Treat source boundaries and representation/performance changes as separate measured outcomes |
| Lightweight editing loses expected FreeCAD behaviour | Prototype selection, handles, visibility, undo/redo, save/reopen, and GUI use before choosing a renderer |
| Deferred geometry only moves cost to export | Measure both edit-only and edit-through-export workflows, including cleanup |
| Cache signatures omit an input | Centralise signatures and test change/reuse/change-back for every input class |
| New persistence makes old documents unreadable | Agree a support window, retain fixtures, version schemas, and test recoverable migrations |
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
