# Phase 1 Closeout Record

Status: **Accepted and closed by the project owner on 2026-07-22. Phase 2 is
current under the bounded foundation authority recorded here.**

Prepared on 2026-07-22 from repository evidence checkpoint
`6f49d6570072926f7e416893bb6d07cee0071733`.

This record consolidates the Phase 1 product, dependency, correctness,
performance, compatibility, provenance and terminology evidence accepted by
the project owner. It does not implement the Workbench, repair a legacy defect,
clear an output dependency or create an S1 chair.

## Decision boundary

Owner acceptance of this closeout means that:

1. the Phase 1 inventory is sufficient to begin only the selected Phase 2
   modular-foundation work;
2. all open workflow, GUI, performance, migration, provenance, S1 and
   terminology items remain mandatory at their named later gates;
3. the narrow qualified-runtime and B14/B15 ingress policies are accepted as
   initial fail-closed boundaries, not broad compatibility claims;
4. characterised legacy defects are evidence to fix or avoid, not successor
   requirements or waived correctness failures;
5. no numerical human-use performance budget is accepted from the legacy
   timings; and
6. B14 and B15 remain immutable references while the reserved B16 composition
   path may start only within the bounded Phase 2 foundation.

Acceptance does not clear any S1 package, accept any currently blocked
lineage, qualify another operating system/FreeCAD distribution, choose the
lightweight renderer, authorise optimisation or permit a whole-macro rewrite.

## Reproducible checkpoint

| Item | Closeout evidence |
| --- | --- |
| Evidence-base commit | `6f49d6570072926f7e416893bb6d07cee0071733` |
| B14 source | `AdvancedTurnout.FCMacro`; `10.2A8A7B14`; SHA-256 `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`; immutable legacy comparison oracle |
| B15 source | `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro`; `10.2A8A7B15`; SHA-256 `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`; accepted behavioural reference |
| Standalone development probe | CPython 3.12.3; expected `not-freecad-runtime`; FreeCAD modules unavailable |
| Qualified FreeCAD probe | `linux-x86_64-flatpak-freecad-1.1.1`; FreeCAD 1.1.1, bundled CPython 3.13.14, PySide6/Qt 6.10.3, OpenCASCADE 7.8.1 and Coin 4.0.8; reverified 2026-07-22 |
| Real FreeCAD smoke | `B15 FreeCAD 1.1 headless smoke test passed` sentinel reverified 2026-07-22 |
| Fast validation | 27 repository validators including this closeout control; all pass on the accepted transition tree |
| Product-source change at Phase 1 acceptance | None; B14/B15 hashes remain exact and no `tracktemplate` package or `TrackTemplate.FCMacro` existed when the decision was recorded |

The runtime probes record only non-sensitive platform/version fields. The
FreeCAD probe was rerun in the isolated installed Flatpak; the closeout does
not copy the user-specific diagnostic path printed by FreeCAD.

## Exit-gate reconciliation

| Phase 1 exit condition | Closeout state | Evidence owner |
| --- | --- | --- |
| Every release-critical workflow has an owner, oracle and visible coverage gap | Evidenced | `contracts/phase1-workflow-coverage.json`: 14 workflows, 12 bounded-executed, two defined-blocked and 14 scheduled open gaps |
| Dependency/side-effect map predicts the first extraction boundary | Evidenced | `PHASE1_INVENTORY.md`, candidate-boundary contract and deterministic AST inventory |
| Representative profiles identify dominant costs without source-size guesswork | Evidenced | `contracts/phase1-performance-boundaries.json`: reconciled legacy boundaries, five bounded instrumentation defects and four unmeasured target slots |
| First slice, comparison path and acceptance evidence are agreed | Evidenced | Transition-length architecture pilot and exact parity/rollback/performance contract |
| Templot chair map, B15 gap, S1 oracle recipe and assimilation boundary are reviewed | Evidenced | Exact 556b source map plus visibly blocked local comparison oracle |
| First-S1/core and other-S&C/legacy lineage scopes are classified or visibly blocked | Evidenced | Four machine-readable scopes remain `blocked`; no project clearance is inferred |
| Neutral chair boundary, manifest/licensing controls and first-S1 evidence/rights plan are accepted | Evidenced | Owner-accepted `S1_PILOT_PLAN.md`; manifest stays `unknown`/`NOASSERTION` and S1-07 through S1-15 remain blocked |
| RC chair scope is bounded to validated packages and one assisted S1 pilot | Evidenced | Arbitrary automatic scan/CAD conversion remains post-RC research |
| Open risks and required owner decisions are recorded | Evidenced | This accepted closeout, its decision register, explicit deferral register and exact owner instruction below |

The project owner accepted the ninth condition and this complete record on
2026-07-22. The project plan therefore records Phase 1 as 9/9 complete and
Phase 2 as current, without promoting any controlled deferral.

## Runtime and legacy-ingress policy for acceptance

The initial release support boundary remains deliberately narrow:

- only the exact `linux-x86_64-flatpak-freecad-1.1.1` profile is qualified;
- other Linux packages/architectures, Windows and macOS remain
  `qualification-pending`;
- standalone CPython 3.12.0+ qualifies repository tools and future pure-domain
  imports only, not a FreeCAD product host;
- every host mismatch must stop Track Template mutation, migration and
  production export before a transaction; and
- Phase 10 must revalidate actual Addon metadata and the platform matrix rather
  than publishing these Phase 1 observations blindly.

The future document-ingress boundary is similarly fail closed:

- the only outer source-version window is B14, B15 or the expected mixed
  B14/B15 set;
- version support alone is insufficient: every advertised entity family needs
  a passing Phase 4 migration fixture;
- migration operates only on an explicit copy/new target and leaves the source
  byte-for-byte unchanged;
- pre-B14, versionless, future, unknown or family-unqualified documents are
  inspection-only; corrupt or conflicting owned evidence is blocked; and
- no successor detector or migrator exists yet, so this is an implementation
  contract rather than a current Workbench capability.

## Workflow and GUI evidence boundary

All 14 release-critical workflow families have an evidence owner and a later
gap owner. Twelve have bounded current B14/B15 execution evidence; procedural
chair definitions and assisted chair assimilation are defined-blocked because
their successor implementations and evidence do not exist.

This ownership is not whole-product GUI acceptance:

- the current evidence is deliberately fixture-specific and every workflow
  retains at least one scheduled gap;
- FreeCADCmd/headless layer topology is not evidence for real-GUI visibility,
  selection, interaction, refresh or one-command history behaviour;
- the successor Workbench, B16 launcher and lightweight renderer do not exist;
- independent-datum stationing, wider alignment/turnout/crossover/timber/chair
  matrices and remaining export/failure paths stay with Phases 4 through 10;
  and
- each owning migration gate requires its stated real-GUI evidence before the
  legacy path can be removed.

Phase 1 acceptance therefore accepts the **map and deferrals**, not untested GUI
behaviour.

## Performance boundary

The legacy measurements prove that current human-visible workflows—especially
the chair chain—are exceptionally slow. They do not define acceptable target
performance and are not a reason to preserve the current object-heavy design.

Five instrumentation/performance defects remain `bounded-not-fixed`:

1. `geometry-external-internal-boundary-gap`;
2. `premature-chair-timing-persistence`;
3. `late-supported-solid-reuse-check`;
4. `redundant-post-reuse-panel-refresh`; and
5. `repeated-effective-status-signature-scans`.

Four target-architecture measurements remain
`not-implemented-unmeasured`:

1. `lightweight-routine-edit-without-export`;
2. `explicit-validate-deferred-exact-geometry`;
3. `production-export-from-validated-state`; and
4. `complete-edit-validate-export`.

No inner/nested profile affected by the five defects may select an
optimisation. No legacy timing becomes a human-use budget. Phases 5 and 6 must
populate the first target slots, Phase 9 extends them across production
families, and Phase 10 freezes supported budgets only after representative
target evidence exists.

## Legacy defects and explicit deferrals

| ID | Bounded observation | Closeout disposition | Owning later gate |
| --- | --- | --- | --- |
| P1-X01 | Fourteen workflow families retain 14 explicit gaps | No gap is waived or promoted to complete coverage | The closure phases in the workflow register |
| P1-X02 | Five timing/instrumentation defects and four absent target profiles | Use only their declared safe boundaries; do not optimise or set budgets from invalid spans | Phases 5, 6, 9 and 10 |
| P1-X03 | Crossover preview accepts the fixed 500.000 mm case that commit rejects; the 746.298 mm case passes | Treat mismatch as a legacy defect, not parity to inherit | Phase 8 shared preflight and GUI acceptance |
| P1-X04 | Automatic timbering has persistence drift, display over-invalidation and incomplete abort cleanup | Preserve semantic oracle data only; successor must fix lifecycle defects | Phase 8 timbering migration |
| P1-X05 | Chair analysis has premature timing persistence, mutating reuse, repeated scans and redundant refresh | Preserve bounded semantics, not the inefficient lifecycle | Phases 5 and 9 |
| P1-X06 | Chair invalidation has stale-cache, precision/order and exact-Part presentation defects | Centralise exact dependency cones and prove changed/reuse cases | Phases 4, 5 and 9 |
| P1-X07 | Current other-S&C and B14/B15 outputs remain `reference-only` or `unknown` | No current output is promoted to `project-cleared` by closeout | Each Phase 8/9/10 output manifest gate |
| P1-X08 | Current runtime/platform and document support is narrow and partly contract-only | Fail closed; broaden only through the required qualification/migration matrices | Phases 4 and 10 |
| P1-X09 | Frozen `ordinary_track` identifiers and six terminology reviews remain | Preserve evidence names; prevent their spread and resolve meanings at the named gates | Phases 8 and 9 |
| P1-X10 | Control and documentation volume can duplicate truth, become stale or impose maintenance cost without improving the product | Keep one authoritative owner for each fact, link rather than copy detailed payloads, require every new control to close an enforceable gap, and retire or archive superseded controls with an explicit replacement | Phase 2 maintainability/reuse review and every later phase closeout |

These are controlled deferrals, not silent exceptions. Phase 2 may not fix,
normalise or broaden them as incidental changes to the mechanical architecture
pilot. P1-X10 also means that a passing control is not valuable merely because
it adds files or assertions: the Phase 2 review must identify duplicated facts,
stale snapshots and controls whose cost exceeds their continuing purpose.

## S1, provenance and rights boundary

The owner-accepted S1 plan remains a plan rather than a digital chair artifact:

- S1-04 through S1-06 are accepted architectural direction;
- S1-07 through S1-15 remain blocked pending the specified evidence and
  decisions;
- the manifest remains version `0-unresolved`, package licence `NOASSERTION`
  and project status `unknown` for the four declared intended uses;
- the first-S1 and core rail/timber scopes remain blocked;
- the other-S&C and legacy B14/B15 scopes remain blocked;
- the Templot 556b oracle remains local comparison only with four open capture
  blockers; and
- Templot equality cannot supply canonical production data, independent rights
  evidence or final geometry acceptance.

Nothing in Phase 1 closeout grants permission, clears non-copyright rights or
authorises a production/package claim.

## Terminology boundary

The terminology control contains six accepted bounded term families, one
provisional S1 designation, five review-required families and one
frozen-legacy ordinary-track family. Its six open reviews have Phase 8 or Phase
9 owners.

Passing the lexical validator means known drift and missing review ownership
are detected. It cannot decide railway meaning from spelling. New uncertainty
must remain visibly provisional or `TERM-REVIEW` controlled until the project
owner accepts an evidence-backed bounded meaning.

## Phase 2 authorisation boundary

Under the accepted closeout, Phase 2 may begin only the already selected
foundation:

- create only the minimum package skeleton reserved for the three-function
  transition-length slice, without moving its calculation implementation;
- create a narrow temporary `tracktemplate.api` façade/loading boundary and
  small reserved `TrackTemplate.FCMacro` B16 development composition root;
- enforce standalone domain imports, dependency direction, cycle checks,
  runtime guard and maintainability/reuse evidence;
- retain exact B14/B15 comparison and rollback routes.

Phase 2 is not authorised to move the selected calculation implementation,
migrate callers, implement the Phase 4 document migrator, choose the Phase 5
renderer, build the Phase 6 export seam, optimise the legacy path, implement
chair geometry, clear provenance or alter B14/B15. Mechanical extraction and
exact formula/error parity begin only at the Phase 3 vertical-slice gate.

## Closeout decision register

| ID | Decision | Accepted state | Accepted disposition |
| --- | --- | --- | --- |
| P1-01 | Phase 1 evidence sufficiency | accepted | The bounded inventory is sufficient to start the selected modular foundation; later gaps remain mandatory |
| P1-02 | Qualified runtime boundary | accepted | Only the exact FreeCAD 1.1.1 Flatpak profile is qualified; all others fail closed pending qualification |
| P1-03 | Legacy document ingress | accepted | B14/B15 are the outer future window; per-family fixtures and copied-target migration remain required |
| P1-04 | Workflow and GUI limitations | accepted | Coverage ownership and scheduled gaps are accepted without claiming whole-product or successor GUI acceptance |
| P1-05 | Performance evidence | accepted | Bounded legacy measurements, five instrumentation defects, four unmeasured target slots and no numerical budget are accepted |
| P1-06 | Legacy-defect disposition | accepted | Characterised defects are not successor requirements and cannot be silently fixed during Phase 2 foundation work |
| P1-07 | S1/provenance boundary | accepted | Preserve the blocked S1 plan, unknown manifest, blocked lineages and local-comparison-only Templot oracle |
| P1-08 | Terminology assurance | accepted | Preserve the four confidence states, six open reviews, human review boundary and frozen evidence identifiers |
| P1-09 | Phase 2 implementation scope | accepted | Preserve the selected transition pilot, B16/package boundaries, exact parity contract and no calculation movement in Phase 2 |
| P1-10 | Phase transition | accepted | Phase 1 is closed and only the bounded Phase 2 foundation is authorised |

## Acceptance record

Accepted explicitly by the project owner on 2026-07-22 with this instruction:

> I accept PHASE1_CLOSEOUT.md, including P1-01 through P1-10. Close Phase 1
> and authorise only the bounded Phase 2 foundation described here. All open
> workflow, GUI, performance, migration, provenance, S1, rights and terminology
> items remain mandatory at their named later gates.

This instruction is the phase-transition authority. It advances the project
plan to Phase 1 9/9 complete, M2 complete and Phase 2 current; it does not
alter any later gate or blocked status listed in this record.

## Reproduction

Run the closeout aggregation and all fast repository checks:

```bash
.venv/bin/python tests/validate_phase1_closeout.py
for test_file in tests/validate_*.py; do .venv/bin/python "$test_file"; done
```

Recheck the compatibility boundary in standalone Python and the qualified
FreeCAD host:

```bash
.venv/bin/python tools/runtime_compatibility_probe.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tools/runtime_compatibility_probe.py --pass --require-qualified
```
