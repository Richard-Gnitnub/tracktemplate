# Project Plan: Baseline to Release Candidate

Status: working delivery plan. **Phase 0 closed on 2026-07-19; Phases 1–3
closed on 2026-07-22; Phase 4 is current and opened on 2026-07-22.**

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
  compatibility policy for legacy identifiers;
  [contracts/phase1-terminology-assurance.json](contracts/phase1-terminology-assurance.json)
  records confidence states, open reviews and the automated successor boundary.
- [PROVENANCE.md](PROVENANCE.md) records reference-source identity, source
  relationship, redistribution and licensing status.
- [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) defines the mandatory
  source/data classifications, neutral chair-data boundary, collaboration
  rules, package-licensing target, generated-output policy, and clearance
  statuses.
- [PHASE1_INVENTORY.md](PHASE1_INVENTORY.md) records the accepted Phase 1
  workflow, dependency, side-effect, candidate and decision evidence.
- [PHASE1_CLOSEOUT.md](PHASE1_CLOSEOUT.md) records the accepted Phase 1
  evidence, risks, deferrals, owner decisions and bounded Phase 2 authority.
- [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) records the accepted loading,
  dependency and comparison foundation.
- [PHASE3_TRANSITION_SLICE.md](PHASE3_TRANSITION_SLICE.md) records the accepted
  transition-length extraction, parity, performance and closeout evidence.
- [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md) is the one live Phase
  4 evidence record for canonical state, signatures, persistence, migration
  and the chair-definition contract.
- [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) owns destructive-action,
  checkpoint, ignored-data backup and restore controls. Its first repository-
  scope drill and the owner's complete project-data scope declaration are
  recorded; repeat retention remains separately gated.
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
- a small launcher/composition root and one authoritative, maintainable modular
  implementation whose genuinely shared railway concepts are reused through
  narrow tested interfaces;
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

### Mandatory safety/risk panel before gate closeout

From Phase 4 onward, no phase, milestone or release-candidate gate may close
until a safety/risk panel has reviewed the assembled evidence and issued a
recorded recommendation. The same bounded panel is required before a sub-gate
that would authorise copied-target family migration, behaviourally significant
legacy retirement, project-cleared/commercial output, an irreversible external
action, or an exception to an accepted gate. Ordinary tranche reviews do not
need a separate panel unless they trigger one of those authority changes. One
panel may cover coincident phase, milestone and sub-gates when its record names
and assesses each gate; do not duplicate the same review.

The panel may meet synchronously or by recorded review, but silence is not
concurrence. Its minimum roles are:

- the **project owner**, who chairs the decision and alone accepts or rejects
  the gate;
- the **phase/slice owner**, who presents the change, evidence, limitations and
  proposed risk dispositions; and
- a **QA/risk reviewer**, who performs a deliberate challenge review against
  the implementation evidence and risk/control registers.

Add railway-domain, FreeCAD/runtime, performance, provenance/licensing or
recovery expertise when the gate affects that subject. Record any role overlap
or lack of independence. If a due Critical risk, irreversible action or
project-cleared rights decision is in scope, the QA/risk challenge must be
independent of the implementation work; otherwise the recommendation is `Do
not proceed` until an independent reviewer is appointed.

The panel reviews links rather than reproducing their payloads. Its minimum
inputs are:

1. the exact source commit/diff and the owning open-phase evidence record;
2. every exit condition and applicable item in the slice definition of done;
3. all relevant principal and QA risks, their treatments, deadlines, control
   effectiveness and changes since the previous review;
4. the selected automated, FreeCAD headless, real-GUI, persistence,
   exact-output, rollback and performance evidence under
   [VALIDATION.md](VALIDATION.md);
5. repository/document safety, backup prerequisites and recovery/rollback
   evidence under [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md);
6. applicable railway terminology, production-data provenance, licensing and
   output-dependency evidence; and
7. unresolved defects, unknowns, dissent, exceptions and proposed conditions.

The recommendation must be exactly one of:

- **Proceed** — all evidence due at this gate passes, no due risk/control is
  ineffective or overdue, and no unaccepted gate blocker remains.
- **Proceed with bounded conditions** — the gate evidence passes and every
  remaining non-blocking exposure has an accepted treatment, owner and later
  deadline. This outcome cannot waive a failed required test, a due Critical
  risk, a data/document-corruption hazard, an unresolved rights restriction,
  or another explicit fail-closed condition.
- **Do not proceed** — required evidence is missing/failed, a due control is
  ineffective, a deadline or safety prerequisite is unmet, material dissent
  is unresolved, or the panel cannot demonstrate one of the two outcomes
  above. Missing information defaults to this outcome.

The recommendation does not itself close the gate. The project owner records a
separate decision after reviewing the panel. An exception requires the live
risk treatment, owner, deadline and rationale to be updated before acceptance;
it cannot silently rewrite historical evidence or a non-waivable control.

Keep one concise panel record in the owning open-phase evidence document using
this minimum form:

```text
### Safety/risk panel — YYYY-MM-DD
Gate and exact source:
Participants and roles (including independence):
Evidence reviewed (links):
Due principal/QA risks and control-effectiveness changes:
Safety, recovery, correctness, rights and performance conclusions:
Unresolved dissent, unknowns or exceptions:
Recommendation: Proceed | Proceed with bounded conditions | Do not proceed
Conditions, owners and deadlines:
Project-owner decision and date:
```

At phase close, link that record once from the phase section using:

```text
Safety/risk panel: [panel record](relative-path) — `Proceed`
Project-owner gate decision: `Accepted YYYY-MM-DD`
```

Use `Proceed with bounded conditions` in the first line when applicable and
identify the condition risk IDs in the panel record. A `Do not proceed` panel
or absent record leaves the phase open. This requirement is prospective from
Phase 4; it does not retroactively reopen accepted Phases 0–3.

### Documentation lifecycle

- This plan is the sole project-wide live phase, progress, milestone and
  decision-status record.
- The open phase has one owning evidence record. It accumulates tranche
  evidence, limitations and remaining gates until closeout.
- Accepted baselines, inventories, contracts, foundation/closeout records and
  benchmark reports are historical evidence. Freeze them after acceptance
  except for an explicit factual correction; do not make them follow later
  phase progress.
- Architecture, modularisation, testing, validation, performance, provenance,
  licensing and agent-guidance documents change only when their owned policy
  or procedure changes.
- A normal tranche updates product code, directly relevant tests, the current
  phase evidence and this plan. Link to an owning fact rather than duplicating
  it across past-phase documents and validators.

### Progress convention

Progress bars count the explicit exit conditions in each phase; they do not
estimate elapsed time, remaining effort or calendar completion:

- `█` — exit condition has recorded evidence;
- `▒` — exit condition is actively being closed; and
- `░` — no accepted completion evidence yet.

Bars may have different lengths because phases have different numbers of exit
conditions. A phase closes only when every condition is evidenced and the
project owner accepts the phase closeout. Discovery may add or refine an exit
condition, so the bar can move backwards without implying that completed work
was lost. Run `../tests/validate_project_progress.py` after changing a phase
gate, register, roadmap row or milestone state; it checks numerical consistency
but does not decide whether the cited evidence is sufficient.

## Key project milestones

Milestone progress: `███▒░░░░░` — three complete, one active and five not
started. This is
an outcome count, not an overall percentage of effort.

| Milestone | Outcome | Owning phases | State |
| --- | --- | --- | --- |
| M1 — Recoverable behavioural baseline | B14/B15 roles, source state, validation, provenance and representative performance can be reproduced | 0 | Complete — accepted 2026-07-19 |
| M2 — Migration blueprint locked | Release-critical workflows, dependency/performance boundaries, compatibility, terminology, rights/provenance controls, chair direction and the first extraction slice are sufficiently bounded to begin modular source work | 1 | Complete — accepted 2026-07-22 |
| M3 — First reusable modular capability | The minimal package loads in standalone Python and FreeCAD, and the transition-length pilot passes end-to-end legacy/new parity | 2–3 | Complete — accepted 2026-07-22 |
| M4 — Canonical responsive editing foundation | Versioned canonical state, exact invalidation, save/reopen and an accepted lightweight renderer support normal editing without dense exact geometry | 4–5 | Active |
| M5 — Deferred production seam proven | Explicit Validate/Export regenerates equivalent exact geometry transactionally without leaking production objects into routine editing | 6 | Not started |
| M6 — Core trackwork migrated | Plain-line alignment/station/multiple-track plus turnout/crossover/timbering workflows run through the modular architecture | 7–8 | Not started |
| M7 — Production chair system completed | Validated external definitions, one evidence-led S1 assimilation pilot, procedural constituents, production records, manifests and supported exports pass | 9 | Not started |
| M8 — Installable Workbench beta | The authoritative package ships as an installable FreeCAD Addon with migration, documentation and no unowned monolithic production path | 10 | Not started |
| M9 — Release Candidate 1 qualified | Reproducible artifact, complete validation/performance/rights evidence, known-risk disposition and explicit owner acceptance | 11 | Not started |

## Roadmap summary

| Phase | Outcome | Exit-gate progress | State |
| --- | --- | --- | --- |
| 0 | Recoverable baseline and benchmark checkpoint | `██████` — 6/6 evidenced | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness, and performance inventory | `█████████` — 9/9 evidenced | Complete — accepted 2026-07-22 |
| 2 | Minimal modular foundation and validation harness | `█████` — 5/5 evidenced | Complete — accepted 2026-07-22 |
| 3 | First parity-proven vertical slice | `█████` — 5/5 evidenced | Complete — accepted 2026-07-22 |
| 4 | Canonical state, signatures, and persistence | `█▒█░█▒` — 3/6 | Current |
| 5 | Lightweight editing prototype and renderer decision | `░░░░` — 0/4 | Not started |
| 6 | Explicit exact-validation and export seam | `░░░░░` — 0/5 | Not started |
| 7 | Core alignment, station, and multiple-track migration | `░░░░` — 0/4 | Not started |
| 8 | Turnout, crossover, and timbering migration | `░░░░` — 0/4 | Not started |
| 9 | Chair definitions, assisted assimilation, production records, and export completion | `░░░░░░░░░` — 0/9 | Not started |
| 10 | Workbench integration, launcher reduction, and beta Addon packaging | `░░░░░` — 0/5 | Not started |
| 11 | Stabilisation and release-candidate qualification | `░░░░░░░` — 0/7 | Not started |

## Phase 0: recoverable baseline and benchmark checkpoint

Status: **Complete — accepted and closed on 2026-07-19.**

Progress: `██████` — 6/6 exit conditions evidenced and accepted.

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

Status: **Complete — accepted and closed on 2026-07-22.**

Progress: `█████████` — 9/9 exit conditions evidenced and accepted.

### Final gate register

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| Every release-critical workflow has an owner, oracle and visible coverage gap | Evidenced | The fail-closed workflow registry covers all 14 canonical families: 12 have bounded executed oracles and the two successor-only chair workflows have defined blocked oracles, decision owners and later gates; their open gaps are not waived |
| Dependency/side-effect map predicts the first extraction boundary | Evidenced | Deterministic AST inventory, candidate-boundary register, closure cuts and the transition-pilot contract |
| Representative profiles identify dominant costs without source-size guesswork | Evidenced | Reconciled performance-boundary contract and controlled legacy profiles; target-architecture slots remain deliberately unmeasured until their implementations exist |
| First slice, comparison path and acceptance evidence are agreed | Evidenced | Transition-length solver selected; B16/façade/caller/parity/rollback/performance contract frozen |
| Templot chair map, B15 gap, S1 oracle recipe and assimilation boundary are reviewed | Evidenced | Exact 556b source route and blocker branch recorded; missing exact executable/artifacts remain named local evidence gates rather than silently weakened requirements |
| First-S1/core and other-S&C/legacy lineage scopes are classified or visibly blocked | Evidenced | Both bounded machine-readable lineage registers have statuses, owners and later output gates; no positive clearance is inferred |
| Neutral chair definition, manifest/licensing controls and first-S1 evidence/rights plan are accepted | Evidenced | The owner accepted `S1_PILOT_PLAN.md` on 2026-07-22, including S1-04 through S1-06, intended uses and the conditional CC0 target; S1-07 through S1-15 and the actual package remain blocked |
| RC chair scope is bounded to validated packages and one assisted S1 pilot | Evidenced | Arbitrary automatic scan/CAD conversion remains explicitly post-RC research |
| Open risks and required owner decisions are recorded | Evidenced | The project owner accepted `PHASE1_CLOSEOUT.md`, P1-01 through P1-10 and every recorded mandatory later gate on 2026-07-22 |

The canonical workflow control is
[`contracts/phase1-workflow-coverage.json`](contracts/phase1-workflow-coverage.json).
It cross-checks all 14 rows in the Phase 1 inventory, points to the specialist
evidence owners instead of duplicating their semantic payloads, and assigns
every visible gap to a later phase gate. Its 12 `bounded-executed` and two
`defined-blocked` states satisfy workflow ownership only; they do not turn a
partial legacy witness into whole-product coverage or clear either future
chair workflow for implementation.

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
compatibility launcher. Subsequent implementation evidence belongs in the
owning current-phase section rather than this accepted Phase 1 record; the
public Workbench/RC version remains undecided.

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
remain mandatory Phase 8 migration evidence before the crossover legacy path
can move or retire; the workflow registry does not waive them.

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

The fixed post-B4 logical chair-analysis boundary is now separately bounded by
[`contracts/phase1-chair-analysis-persistence.json`](contracts/phase1-chair-analysis-persistence.json).
Cold calculation, immediate reuse, reuse Undo/Redo and save/reopen preserve the
accepted 355 positions, 269 findings, stable identities, semantic digest and
two diagnostic-display identities. The contract also proves, without
accepting, that a cache hit still repeats multi-second record extraction,
rewrites roughly 1.5 MB of timing-bearing metadata in a new history entry,
persists an incomplete timing payload, and enters redundant status/panel
refresh paths. Successor fixes, the complete calculation-input invalidation
matrix, lightweight-presentation semantics, B15 support/layout/solid coverage
and turnout/plain-line/wider-crossover cases remain open. Current position and
chair-code semantics remain legacy comparison evidence, not project-cleared
chair data.

The same fixed witness now has a complete emitted-input classification and
representative invalidation matrix in
[`contracts/phase1-chair-analysis-invalidation.json`](contracts/phase1-chair-analysis-invalidation.json).
It classifies all 23 normalised settings, 11 rail-record fields and 40 timber-
record fields, and reproduces an actual stale cache hit after changing omitted
timber axes. It also bounds five-decimal signature aliasing, record-order over-
invalidation and the headless topology of presentation-only changes. These are
defect witnesses, not requirements to preserve. Upstream configuration-to-
record mutations, turnout/plain-line/wider-crossover cases, real-GUI
visibility/selection/history, the lightweight successor and B15's downstream
support/layout/solid chain remain open.

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
explicit point-adapter seam, while chair analysis retains alias coupling and
11 outgoing closure dependencies; its fixed-XO signature gaps are now
classified and fail-closed by the dedicated invalidation contract. Broader
workflow boundaries and product-pipeline profiles remain controlled
later-phase gaps after the accepted Phase 1 closeout. The bounded Phase 2
package, calculation and routing status is recorded by the owning later phase
rather than this accepted Phase 1 record. The
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
production ChairDefinition, and it did not by itself close Phase 1.

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
acceptance preserves those target measurements and budgets as later gates.

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

Result: **Pass.** Every exit condition is evidenced. On 2026-07-22 the project
owner explicitly accepted `PHASE1_CLOSEOUT.md`, including P1-01 through P1-10,
closed Phase 1 and authorised only the bounded Phase 2 foundation. All named
workflow, GUI, performance, migration, provenance, S1, rights and terminology
obligations remain mandatory at their later gates.

## Phase 2: minimal modular foundation and validation harness

Status: **Complete — bounded foundation and exit evidence accepted by the
project owner on 2026-07-22.**

Progress: `█████` — 5/5 exit conditions evidenced and accepted.

### Final gate register

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| Standalone Python imports the domain/API boundary without FreeCAD or Qt | Evidenced | Isolated import and forbidden-import checks in `tests/validate_phase2_foundation.py`; result recorded in [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) |
| The launcher loads the package in the qualified FreeCAD environment | Evidenced | Zero-document-mutation FreeCAD smoke in `tests/freecad_validate_phase2_foundation.py`; loading route recorded in [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) |
| Existing B14/B15 workflows and validation remain unchanged | Evidenced | Exact B14/B15 hashes and the applicable fast and FreeCAD regression results are recorded in [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) |
| No speculative tree, cycle, runtime dependency or hidden global service is introduced | Evidenced | Deterministic `tools/modular_structure.py` report and fail-closed assertions in `tests/validate_phase2_foundation.py` |
| The first package has a recorded maintainability/reuse review | Evidenced | Authority, interfaces, dependency direction and retirement gates are recorded in [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) |

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
- Add a deterministic modular-structure report covering package modules,
  supported façade exports, import edges and structural warning signals. Treat
  it as review evidence rather than a substitute for railway-semantic review.
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
- The first package has a recorded maintainability/reuse review naming its
  authoritative implementation, shared invariant, narrow interface,
  dependency direction, tests and every temporary exception/retirement gate.

Implementation result: **Pass.** The project owner explicitly accepted
[PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md) on 2026-07-22, closing Phase 2 and
making Phase 3 current. The acceptance authorises only the bounded,
parity-controlled transition-length vertical slice. No calculation or caller
was moved by the phase transition itself.

## Phase 3: first parity-proven vertical slice

Status: **Complete — all five technical exit conditions and project-owner
closeout acceptance recorded on 2026-07-22.**

Progress: `█████` — 5/5 exit conditions evidenced and accepted.

### Final gate register

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| The selected capability follows target dependency direction and its domain portion imports without FreeCAD/Qt | Evidenced | Exact three-function extraction in `tracktemplate.domain.alignment`; isolated import and structure guards recorded in [PHASE3_TRANSITION_SLICE.md](PHASE3_TRANSITION_SLICE.md) |
| Legacy/new analytical records, findings, identities, ordering and relevant metadata are equivalent | Evidenced | Exact B14/B15/modular AST, value/type and diagnostic parity over the frozen grids; this slice emits only tuples/scalars/errors and has no record/identity/metadata output |
| Cache miss, valid reuse and every relevant invalidation case pass | Evidenced | Candidate contract records no cache/signature; A-B-A recomputation for all three functions proves changed and exact change-back results without inventing reuse state |
| Applicable FreeCAD/headless, GUI and contracted performance checks pass | Evidenced | Qualified FreeCAD caller parity and zero-document-mutation pass; routed real-GUI/persistence/failure-recovery contracts remain exact; nine-repeat complete-grid calculation and three-repeat fresh-process workflow profiles show no material modular regression beyond observed variation |
| Every temporary dual path has an owner and named retirement gate | Evidenced | `tracktemplate.compatibility.transition_pilot` retains the modular default and captured-B15 rollback; evidence/acceptance prerequisites pass, while actual removal is a separate bounded Phase 4 entry compatibility-maintenance change |

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
- FreeCAD/headless, GUI and contracted calculation/workflow performance checks
  pass where the selected path touches them.
- Any temporary dual path has an owner and a named retirement gate.

Result: **Pass.** On 2026-07-22 the project owner explicitly instructed the
project to close Phase 3 with their acceptance and to commit and push the
closeout. That acceptance closed the phase but did not itself remove the
temporary comparison route or start Phase 4. The project owner subsequently
started Phase 4 explicitly on 2026-07-22; the retained comparison route remains
separately gated.

## Phase 4: canonical state, signatures, and persistence

Status: **Current — opened by explicit project-owner instruction on
2026-07-22.**

Progress: `█▒█░█▒` — 3/6 exit conditions evidenced; two are active.

### Current gate register

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| The selected slice round-trips through save/reopen without result or identity drift | Evidenced | One compact `App::FeaturePython` round-trips through an actual disposable FCStd with exact canonical JSON, result, stable identity, object type/name, operator label and foreign-object preservation; see [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md) |
| Parameter edits invalidate exactly the affected derived results, including cold/reuse/change-back cases | Active — transition analysis | All four numerical inputs, label-only reuse and A-B-A analysis cases are covered; downstream preview, validation and export dirty propagation remain due |
| Undo/redo and failed updates leave a valid document | Evidenced | Qualified-host create and update are one transaction each; create/update Undo/Redo, no-op history, preflight rejection, injected post-write create/update abort and unchanged valid-document assertions pass |
| Preview and exact geometry can be deleted and regenerated solely from canonical state | Pending | Requires later derived presentation/exact seams; neither is persisted by the opening tranche |
| A chair-definition package round-trips deterministically and rejects missing, corrupt, unsupported or ambiguous required data | Evidenced | Neutral chair-package v1 and its non-prototype fixture prove deterministic exact-decimal round-trip, fixed frame/datums, component/procedure/interface/manufacturing separation, lineage, signed manifest linkage and recoverable failure cases; Phase 9 production admission remains disabled and S1 evidence/values remain blocked; see [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md) |
| The supported schema/version window is agreed and tested | Active — copied-target fixture accepted; support withheld | The accepted read window and read-only family assessment remain unchanged. On 2026-07-23 the project owner accepted the B14/B15/expected-mixed physical-copy, atomic two-record commit/rollback, Undo/Redo and save/reopen evidence with every source preserved. Support advertising remains a separate authority gate; `SUPPORTED_MIGRATION_FAMILIES` is still empty. |

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
| Scoped output lineage and first S1 package rights plan | Resolved for Phase 1 planning on 2026-07-22; package remains blocked | Owner-accepted `S1_PILOT_PLAN.md` plus the blocked first-S1/core classifications, validated unknown manifest, B15 gap analysis, intended uses, evidence/licence/right-review decision owners, comparison metric families and explicit later gates |
| First extraction slice | Resolved and accepted at Phase 3 closeout on 2026-07-22; the separately authorised Phase 4 comparison-route retirement now passes implementation evidence and awaits acceptance | Candidate contracts, bounded closure cuts, workflow/performance profiles, scorecard, [PHASE3_TRANSITION_SLICE.md](PHASE3_TRANSITION_SLICE.md), [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md) and separate owner decisions |
| Remaining representative fixtures and Phase 1 profile coverage | Accepted as controlled deferrals at Phase 1 closeout on 2026-07-22 | Fourteen owned workflow families with scheduled gaps, reconciled legacy profiles, five bounded instrumentation defects and four explicit unmeasured target slots |
| Supported FreeCAD/Python and legacy document window | Bounded read window accepted on 2026-07-22; first-family copied-target fixture evidence accepted on 2026-07-23 with support still withheld | Exact runtime probe, official Addon metadata fields, B14/B15 source/schema anchors, fail-closed detector, read-only assessment, physical-copy atomic fixture and separate project-owner decisions |
| Domain record and persistence schema strategy | Phase 4 exit | Runtime compatibility and round-trip tests |
| Coin ViewProvider versus SVG/Qt editing view | Phase 5 exit | Selection, editing, persistence, and resource prototype |
| Numerical performance budgets | Provisional after Phase 1; frozen by Phase 10 | Repeated cold/warm representative baselines |
| RC product/distribution target | Resolved 2026-07-20 — external Track Template FreeCAD Workbench packaged as an Addon and intended for Addon Manager installation; modular package authoritative; macro limited to migration/compatibility | Project-owner acceptance and FreeCAD's Workbench/Addon ecosystem model |
| RC version identifier and publication | Phase 11 | Complete qualification evidence and user approval |

## Principal risks and controls

### Risk treatment and control-assurance rules

Both registers below use the same treatments:

- **Tolerate** — permit the exposure only within the stated boundary. It is
  not closure; the row must name when it will be removed or mitigated.
- **Remove** — eliminate the identified condition before the deadline. The
  named gate cannot pass while it remains.
- **Mitigate** — reduce likelihood or impact to the stated controlled level
  and prove the control works. Any remaining exposure requires explicit owner
  acceptance at the gate.

Control measures are labelled **P** (preventive), **D** (detective), and **R**
(recovery/corrective). Their current effectiveness means:

- **Effective (current scope)** — the control has executed and passed for the
  presently authorised scope; later expansion can keep the risk open.
- **Partial** — at least one control is demonstrated, but a material control,
  workflow or later gate is still missing.
- **Not yet effective** — the control is planned but has not been executed at
  the relevant boundary.
- **Ineffective** — the control was exercised and failed; its gate is blocked.

“Solved” means the required evidence exists, the accountable owner confirms
it, the applicable gate is accepted and the register records `Closed` plus the
closure evidence/date. Do not delete closed entries or silently extend a
deadline. An open risk may have an effective current control because its later
exposure or final gate has not yet been exercised.

Ownership is role-based and unambiguous: the **project owner** is the
repository owner/user who accepts gates and makes external, scope and rights
decisions; a **phase/slice owner** is the developer or agent assigned to
implement that tranche and produce its evidence; a **QA owner** executes and
reviews the required matrix but cannot replace project-owner acceptance.
Until a future phase owner is assigned in the open-phase record, the project
owner remains accountable for ensuring its gate is not crossed.

### Principal risk treatment register

| ID | Severity | State | Treatment | Principal risk | Accountable owner | Mandatory target |
| --- | --- | --- | --- | --- | --- | --- |
| PR-01 | High | Open | Remove | Test evidence over-represents the B15 chair path and accepted slices while other release-critical families remain incomplete. | Named workflow-family owners; each phase owner; Phase 10/11 QA owner for completeness. | Remove each owned coverage gap at its applicable Phase 4–9 exit, aggregate the full matrix by Phase 10 beta exit, and leave none unperformed at Phase 11. |
| PR-02 | High | Open | Remove | The B15 five-box body could be mistaken for final procedural chair geometry. | Phase 9 chair-definition owner; project owner accepts production geometry. | Block that claim immediately and remove the ambiguity before Phase 9 chair exit or any S1 production/project-cleared acceptance. |
| PR-03 | High | Open | Mitigate | Scan/CAD evidence could be mistaken for authoritative reusable runtime geometry. | Phase 4 chair-schema owner and Phase 9 assimilation owner; project owner accepts the pilot. | Mitigate in the package schema before Phase 4 exit and prove the evidence-to-definition boundary in the Phase 9 assisted-pilot gate. |
| PR-04 | High | Open | Mitigate | A scan cannot reveal nominal, hidden, worn or rail-fit geometry. | Phase 9 chair-evidence owner; project owner owns unresolved-value and rail-fit acceptance. | Mitigate through explicit unknowns and independent evidence before Phase 9 pilot/definition acceptance; recheck at Phase 11. |
| PR-05 | Medium | Open | Remove | Chair assimilation could introduce heavy or proprietary normal-runtime dependencies. | Phase 9 assimilation owner and Phase 10 Addon-packaging owner. | Remove any such normal-runtime dependency before Phase 9 chair acceptance and prove a clean supported installation at Phase 10 beta exit. |
| PR-06 | High | Open | Remove | Imported chair evidence could have unclear ownership, licence or permitted use. | Chair-package provenance owner; project owner accepts package admission/publication. | Remove uncertainty before each package is admitted or published, before Phase 9 chair exit, and re-audit the frozen artifact at Phase 11. |
| PR-07 | High | Open | Mitigate | Templot software licensing could be conflated with a blanket licence on generated output. | Licensing/provenance owner; project owner accepts output-status policy and release evidence. | Mitigate on every output-affecting change, prove manifest propagation at Phase 9, and re-audit at Phase 11. |
| PR-08 | High | Open | Remove | A systematically copied table/profile could be relabelled as isolated engineering facts. | Production-data/provenance owner; project owner accepts canonical admission. | Remove copied or unresolved dependencies before canonical admission, before Phase 9 project-cleared package acceptance, and at the Phase 11 lineage audit. |
| PR-09 | Critical | Open | Remove | A non-commercial, unknown or reference-only dependency could reach a path advertised for commercial or magazine use. | Phase 6/9 export and output-rights owners; project owner accepts advertised use. | Remove the route for the selected output seam by Phase 6 exit, for every production path by Phase 9 exit, and prove absence at Phase 11. |
| PR-10 | High | Open | Remove | Duplicate definitions and runtime patches could hide the live caller or implementation. | Owner of each extraction slice; Phase 10 integration owner owns final removal. | Remove each duplicate at its named retirement gate and all unowned production patch paths before Phase 10 beta exit. |
| PR-11 | Medium | Open | Tolerate | Modularisation can increase source-file count without reducing runtime cost. | Architecture owner and each migration-slice owner; Phase 10 integration owner owns final consolidation. | Tolerate bounded file growth only through Phase 9 while structure remains clean; mitigate measured resource cost and remove speculative/unowned modules by Phase 10 beta exit. |
| PR-12 | Medium | Open | Mitigate | Project controls can duplicate facts or become stale documentation bloat. | Documentation-control owner and current phase owner; Phase 10/11 QA owner owns final review. | Mitigate at every tranche and phase close, complete the beta documentation review at Phase 10, and repeat it at Phase 11. |
| PR-13 | Critical | Open | Mitigate | An accidental command, history rewrite or disk failure could destroy system state, project history, ignored evidence or working FCStd files. | Project owner owns independent backup; implementation/QA owner enforces safe work and restore verification. | Mitigate before any Phase 4 copied-target family migration and no later than Phase 4 exit; prove the frozen recovery route again at Phase 11. |
| PR-14 | High | Open | Remove | Lightweight editing could lose required FreeCAD selection, persistence, undo/redo or GUI behaviour. | Phase 5 renderer owner; project owner accepts editing behaviour. | Remove the uncertainty through the measured real-GUI renderer decision before Phase 5 exit. |
| PR-15 | High | Open | Mitigate | Deferred exact geometry could merely move operator-visible cost to Validate/Export. | Performance owner for each slice; Phase 10 integration owner freezes budgets; project owner accepts them. | Mitigate at Phase 6 and every applicable Phase 7–9 slice, freeze budgets at Phase 10, and pass repeated end-to-end qualification at Phase 11. |
| PR-16 | High | Open | Mitigate | A cache signature could omit an output-affecting input and reuse stale results. | Domain/application owner for each signature; owning phase QA owner verifies invalidation. | Mitigate before each signed Phase 4–9 slice exits and prove the complete frozen matrix at Phase 11. |
| PR-17 | Critical | Open | Mitigate | New persistence could make supported old documents unreadable or corrupt migration targets. | Phase 4 compatibility/migration owner and each later entity-family owner; project owner accepts the support window. | Mitigate the schema/window at Phase 4 exit, prove each family at its Phase 7–9 gate, complete migration guidance at Phase 10, and qualify cleanly at Phase 11. |
| PR-18 | High | Open | Remove | Legacy and modular comparison paths could become permanent duplication. | Owner named for each dual path; Phase 10 integration owner owns final production-path removal. | Remove the transition comparison route at its Phase 4 retirement gate, every later dual path at its own gate, and all unowned production duplication before Phase 10 beta exit. |
| PR-19 | High | Open | Remove | The distributed Addon artifact could drift from authoritative modular source. | Phase 10 packaging/build owner; Phase 11 release owner. | Remove drift by reproducible assembly and comparison before Phase 10 beta exit and reproduce the frozen artifact twice at Phase 11. |
| PR-20 | Medium | Open | Mitigate | Feature additions could destabilise or silently expand the migration. | Project owner owns RC scope; current phase owner performs tranche triage. | Mitigate at every tranche/phase close, freeze feature scope at Phase 10 beta exit, and allow only release blockers/defects through Phase 11. |
| PR-21 | High | Open | Mitigate | Reference-source provenance or licence could later become ambiguous. | Licensing/provenance owner; project owner accepts source and publication evidence. | Mitigate on every source/dependency change, re-audit production lineage at Phase 9, and verify the frozen artifact at Phase 11. |
| PR-22 | High | Open | Remove | A gate could close without a structured safety/risk challenge, allowing incomplete evidence or an ineffective control to escape scrutiny. | Current phase/slice owner presents; QA/risk reviewer challenges; project owner chairs and decides. | Remove the exposure at Phase 4 closeout and every later phase/milestone/RC gate, and before each authority-changing sub-gate named in the panel policy. |

### Principal control assurance matrix

| ID | Control measures | Effectiveness | Evidence, gap and required assurance |
| --- | --- | --- | --- |
| PR-01 | **P:** frozen workflow ownership and no movement without an oracle. **D:** contract validators and phase gates. **R:** retain/block the legacy path when evidence is absent. | Partial | The ownership baseline and accepted/blocked states are protected by [phase1-workflow-coverage.json](contracts/phase1-workflow-coverage.json) and [VALIDATION.md](VALIDATION.md), but gaps remain. **Next proof:** accepted linked evidence in each owning Phase 4–9 record, then the Phase 10/11 matrices. |
| PR-02 | **P:** label the five-box body as legacy gap evidence and keep S1 production blocked. **D:** B15 and S1-plan validators. **R:** reject production-ready claims or fallback use. | Effective (current scope) | [S1_PILOT_PLAN.md](S1_PILOT_PLAN.md) and [VALIDATION.md](VALIDATION.md) distinguish the approximation and block the package. **Next proof:** Phase 4 schema rejection plus Phase 9 constituent-generation/oracle evidence. |
| PR-03 | **P:** canonical definitions exclude retained scan/CAD bodies. **D:** calibration, residual, identity and provenance checks. **R:** reject/quarantine ambiguous evidence. | Partial | The boundary is specified in [ARCHITECTURE.md](ARCHITECTURE.md) and [S1_PILOT_PLAN.md](S1_PILOT_PLAN.md), but no accepted schema/pilot has exercised it. **Next proof:** fail-closed Phase 4 package tests and the accepted Phase 9 pilot. |
| PR-04 | **P:** require independent measurements/drawings and operator landmarks. **D:** explicit unknown, rail-fit and residual checks. **R:** preserve unresolved status and reject unsupported confidence. | Partial | The policy and blocked decisions exist in [S1_PILOT_PLAN.md](S1_PILOT_PLAN.md); no assimilation result is accepted. **Next proof:** Phase 9 nominal/hidden/rail-interface evidence and owner acceptance. |
| PR-05 | **P:** dependency approval and optional adapter isolation. **D:** structural dependency checks and clean-runtime loading. **R:** disable optional import/fitting while retaining definition generation. | Effective (current scope) | The current package is structurally clean under [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md) and [PHASE2_FOUNDATION.md](PHASE2_FOUNDATION.md); chair tools do not yet exist. **Next proof:** Phase 9 generation without source tooling and Phase 10 clean Addon installation. |
| PR-06 | **P:** package provenance, hashes, intended-use and licence fields. **D:** manifest/licensing validators. **R:** retain `NOASSERTION` and block admission/publication. | Effective (current scope) | [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md), [PROVENANCE.md](PROVENANCE.md), and the blocked S1 manifest currently fail closed. **Next proof:** an accepted Phase 9 package and the Phase 11 frozen-artifact audit. |
| PR-07 | **P:** separate software, data, media and output classifications. **D:** licensing controls and dependency review. **R:** correct status/notices and block an unsupported output claim. | Effective (current scope) | [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md), [PROVENANCE.md](PROVENANCE.md), and [NOTICE.md](../NOTICE.md) establish the boundary and current validators pass. **Next proof:** Phase 9 output manifests and Phase 11 lineage review. |
| PR-08 | **P:** field/component source classification before canonical admission. **D:** lineage and manifest validation. **R:** reject or replace copied/unresolved values. | Effective (current scope) | The current S1 lineage remains visibly blocked under [phase1-s1-core-lineage.json](lineage/phase1-s1-core-lineage.json) and [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). **Next proof:** independently evidenced Phase 9 values and the Phase 11 audit. |
| PR-09 | **P:** propagate every output dependency and prohibit unresolved `project-cleared` status. **D:** manifest schema/validator and export-lineage checks. **R:** refuse export status and roll back staged output. | Partial | The dependency schema and licensing controls exist, but the production export seam is not yet integrated; see [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). **Next proof:** Phase 6 selected-output enforcement, Phase 9 full-format enforcement, and Phase 11 clean audit. |
| PR-10 | **P:** inventory active definitions/callers before extraction. **D:** AST inventory, caller-closure and structural validators. **R:** retain an explicit captured legacy rollback until parity/removal. | Partial | [PHASE1_INVENTORY.md](PHASE1_INVENTORY.md) and [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md) make current duplication visible, but legacy patches remain. **Next proof:** each retirement record and the Phase 10 no-unowned-patch result. |
| PR-11 | **P:** require a cohesive boundary and forbid speculative modules. **D:** dependency/cycle/warning metrics plus separate performance evidence. **R:** remove speculative modules or roll back an extraction. | Effective (current scope) | The current modular structure is clean and [QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md) records the audit; this is not a runtime-speed claim. **Next proof:** per-slice structural/performance review and Phase 10 legacy consolidation. |
| PR-12 | **P:** one fact owner, link-first updates and frozen accepted history. **D:** QA link/risk validator and phase-progress validation. **R:** dated factual correction or archive/retire superseded controls. | Effective (current scope) | [AGENTS.md](../AGENTS.md) owns the lifecycle and [QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md) records zero broken file targets plus the corrected contradiction. **Next proof:** review at every phase close and the Phase 10/11 documentation audits. |
| PR-13 | **P:** destructive-action prohibitions, sandboxing, pushed checkpoints and copied documents. **D:** safety audit, hashes and Git/remote checks. **R:** GitHub recovery plus independent backup/restore. | Effective (current scope) | Local/Git controls pass; the owner declared the repository to contain all valuable project files; and the [backup, restore and incremental-repeat record](backup-records/2026-07-22-initial-repository-backup-restore.md) passed on a separate USB device under the accepted cadence, closing QA-R01. **Next proof:** maintain the weekly/triggered snapshots and monthly drill, review currency at each gate, and repeat the frozen recovery rehearsal at Phase 11. |
| PR-14 | **P:** renderer-neutral prototype and no production choice without evidence. **D:** real-GUI selection/edit/undo/persistence/resource tests. **R:** reject the candidate and retain the accepted legacy path. | Not yet effective | [ARCHITECTURE.md](ARCHITECTURE.md) and the Phase 5 gate define the controls, but no renderer prototype has exercised them. **Next proof:** the complete Phase 5 decision record and project-owner acceptance. |
| PR-15 | **P:** require both edit-only and edit-through-export measurement. **D:** controlled cold/warm timing, memory, object/recompute and parity evidence. **R:** reject/optimise a seam that only defers cost. | Partial | [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md) and the Phase 1 boundary contract control method, but the full modular target pipeline is unmeasured. **Next proof:** Phase 6–9 end-to-end reports, Phase 10 budgets and Phase 11 repeated passes. |
| PR-16 | **P:** central complete signatures. **D:** miss/reuse/input-change/change-back and stale-result tests. **R:** discard stale results and recompute from canonical state. | Partial | The transition slice passes these cases in [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md), but later input families are not migrated. **Next proof:** equivalent evidence for every signed Phase 4–9 slice and the Phase 11 matrix. |
| PR-17 | **P:** versioned schemas, bounded ingress and copied-target-only migration. **D:** runtime, detector, corrupt/unsupported, save/reopen and rollback tests. **R:** preserve the source byte-for-byte and fall back to inspection-only/recoverable abort. | Partial | The read window and first-family B14/B15/mixed copied-target fixture evidence are accepted with atomicity, recovery and source preservation proved in [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md). No migration support is advertised. **Next proof:** a separate project-owner decision before any supported-family claim/operator wiring, later family fixtures at Phases 7–9, then Phase 10/11 clean upgrades. |
| PR-18 | **P:** named owner and retirement gate for every dual path. **D:** inventory/structural checks and phase-close review. **R:** explicit legacy rollback only until retirement evidence passes. | Partial | Active transition comparison route retired; acceptance pending. The B16 product path is modular-only and lazy, while the dual route is development-oracle tooling under [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md). **Next proof:** project-owner acceptance, later per-slice removals, and Phase 10 absence of unowned production duplication. |
| PR-19 | **P:** reproducible Addon assembly from authoritative source. **D:** source/artifact comparison, hashes, clean install/update and double-build checks. **R:** reject and rebuild a drifting artifact. | Not yet effective | The product form is fixed in [ARCHITECTURE.md](ARCHITECTURE.md), but Phase 10 packaging has not begun. **Next proof:** Phase 10 clean Addon/package parity and Phase 11 two-build reproducibility. |
| PR-20 | **P:** explicit RC scope and gate-based feature triage. **D:** plan/diff/phase-close review. **R:** defer or back out work that is not required for correctness. | Effective (current scope) | [PROJECT_PLAN.md](PROJECT_PLAN.md) and [AGENTS.md](../AGENTS.md) own scope and acceptance; the QA audit found no silent phase advance. **Next proof:** continued tranche reviews, Phase 10 feature freeze and Phase 11 blocker-only discipline. |
| PR-21 | **P:** preserve exact source URL, checksum, archive decision, licence and notices. **D:** provenance/licensing validators and output-lineage audit. **R:** quarantine/block ambiguous source or dependency status. | Effective (current scope) | [PROVENANCE.md](PROVENANCE.md), [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md), and the retained archive checksum currently agree. **Next proof:** review every source change, then Phase 9 and Phase 11 frozen-lineage audits. |
| PR-22 | **P:** mandatory timing, roles, evidence inputs and exact panel outcomes before closeout. **D:** QA-policy and prospective progress validation plus recorded challenge review. **R:** default to `Do not proceed`, leave/reopen the gate and update due risks before reconsideration. | Not yet effective | The panel policy and guards now exist in [PROJECT_PLAN.md](PROJECT_PLAN.md) and [VALIDATION.md](VALIDATION.md), but no prospective panel has yet executed. **Next proof:** the linked Phase 4 panel record, recommendation and separate project-owner decision; repeat at every later applicable gate. |

### QA audit risk log

This is the live disposition log for unresolved findings from the formal
[QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md) audit. Detailed observations stay
in that audit; treatment, state and closure evidence belong here. It uses the
same treatment and closure rules defined above. A QA entry is a specific
observed shortfall; a principal entry is the broader strategic exposure. Where
they overlap, linked evidence may support both, but neither entry closes the
other automatically and the stricter deadline controls.

| ID | Severity | State | Treatment | Residual finding and present boundary | Accountable owner | Target end-state and deadline | Required resolution and objective closure evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-R01 | High | Closed | Mitigate | Closed 2026-07-22: a different-device snapshot and restore of the owner-confirmed complete project-data scope passed and was owner-accepted; the accepted repeat/retention routine then passed a second non-overwriting incremental snapshot. | Project owner maintains the declared complete data scope and retention authority; current implementation/QA owner verifies cadence and later drills. | Mitigated before Phase 4 copied-target entity-family migration; maintain through every later phase and prove the frozen route again at Phase 11. | **Closure evidence:** Closed 2026-07-22 — the [backup, restore and repeat record](backup-records/2026-07-22-initial-repository-backup-restore.md) records the complete scope declaration, separate-device location, two dated sets, empty-directory restore, exact HEAD/archive/raw-evidence/FreeCAD checks, efficient hard-linked repeat, owner acceptance and adopted cadence. A missed cadence, failed run or scope change reopens this risk or creates a successor entry. |
| QA-R02 | Medium | Open | Remove | The validator estate is locally invoked; GitHub `main` has no required pull-request/status-check gate and the repository has no CI workflow. Existing force-push/deletion protection remains only a partial control. | Phase 10 integration owner delivers CI; project owner enables and accepts the GitHub branch rule. | Removed before Phase 10 beta exit; the frozen release matrix is rerun at Phase 11. | Add a tracked clean-checkout CI workflow for the complete standalone matrix and any host checks supportable by the runner; require its successful status and pull-request path for `main`; retain separately controlled FreeCAD GUI/performance gates where CI cannot execute them. **Closure evidence:** two successful clean runs, one deliberate failing-change demonstration on a disposable branch/PR, branch-protection evidence, and the Phase 10 matrix result. |
| QA-R03 | High | Open | Remove | Release-critical GUI, migration-family, exact-output, chair and end-to-end workflows remain partial, blocked or manually evidenced despite strong accepted-slice coverage. Headless success does not close a real-GUI gate. | The named family owner in [phase1-workflow-coverage.json](contracts/phase1-workflow-coverage.json) owns each gap; each phase owner owns its exit; the Phase 10/11 QA owner owns final completeness. | Remove each gap at its applicable Phase 4–9 exit, complete the aggregated matrix by Phase 10 beta exit, and leave no release-critical workflow represented only by an unperformed test at Phase 11. | Convert every owned gap into the proportionate standalone, headless, real-GUI, persistence, rollback, exact-output and performance evidence required by [VALIDATION.md](VALIDATION.md) and the slice definition of done; record results once in the owning open-phase evidence. **Closure evidence:** every gap in the frozen ownership baseline has accepted evidence linked from its owning phase record, the Phase 10 matrix has no untriaged failure, and the Phase 11 clean qualification has no unperformed release-critical workflow. |
| QA-R04 | High | Open | Mitigate | Complete modular edit-through-export performance is not yet measured and numerical interaction/end-to-end budgets are not frozen. Deferred geometry could otherwise hide rather than remove operator cost. | The performance owner for each slice captures evidence; the Phase 10 integration owner freezes budgets; the project owner accepts the budgets and Phase 11 result. | Mitigated with decision evidence at each applicable Phase 5–9 exit; numerical budgets frozen by Phase 10 beta exit; final repeated budget pass required at Phase 11. | Run equivalent cold/warm edit-only and edit-through-export recipes with fixed source, environment and cache state; report medians/ranges, CPU, memory, object/recompute counts and output parity; optimise only behind correctness evidence. **Closure evidence:** linked Phase 5–9 reports, accepted numerical budgets in Phase 10, and repeated Phase 11 runs within budget without hidden deferred cost. |
| QA-R05 | Low | Open | Tolerate | There is no root reader/onboarding guide for installation, first run, operator workflow and contributor navigation. `AGENTS.md` remains a development control, not an operator guide. | Phase 10 documentation/Addon-packaging owner; project owner accepts reader and operator usability. | Tolerate only through Phase 9; remove before Phase 10 beta exit. | Create a concise root `README.md` that routes rather than duplicates canonical controls, plus the Phase 10 installation, upgrade, first-run, workflow, Validate/Export, chair-package, troubleshooting and known-limitation material; exercise it from a clean Addon install. **Closure evidence:** passing internal-link control, clean-reader review, successful documented install/first-run exercise and project-owner acceptance. |

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
