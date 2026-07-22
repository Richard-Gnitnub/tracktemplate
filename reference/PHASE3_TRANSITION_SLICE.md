# Phase 3 Transition-Length Slice Evidence

Status: **Complete — all five technical exit conditions and project-owner
closeout acceptance recorded on 2026-07-22.**

## Bounded result

The accepted three-function transition-length calculation is mechanically
extracted into `tracktemplate.domain.alignment` and re-exported through the
temporary `tracktemplate.api` façade. The B16 composition root now qualifies
the host, verifies and loads the exact B15 source without its final
`run_macro()` call, captures the three legacy calculations, and binds either
the complete modular or complete legacy closure in one guarded update before
any workflow launch.

The normal B16 development route is `modular`; `legacy` is the explicit
rollback route. Automated loading deliberately uses `launch_workflow: false`,
reports `transition-routing-ready`, and performs no document mutation. The
B16-hosted B15 workflow can be launched only through an explicit routed call;
the bounded routed full-workflow evidence is recorded below. Phase 3 closeout
is now accepted; neither route was removed by the closeout.

No B14 or B15 source changed. No calculation implementation was copied into
the launcher, façade or compatibility adapter, and no production calculation,
tolerance or optimisation change is included. The development oracle gained
only the reusable route/reader and comparison seams needed for this evidence.

## Exact source state

The tranche started from accepted Phase 2 closeout commit
`55af5cf26ac82ba081bc3f3bc9ce40cce107c461`.
The routing/rollback tranche started from pushed documentation-lifecycle
checkpoint `cbee8260b5e0ea7852c6e16b5195861d6501a617`.
The routed full-workflow tranche started from pushed routing checkpoint
`3ab42b138e2f3a84cf413c2b434fb74f2565a597`.
The contracted performance tranche started from pushed routed-workflow
checkpoint `dc0623fa024cf1ba86891f713e7f160f52b0b38d`.

- B14 remains
  `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`.
- B15 remains
  `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`.
- The exact accepted selection, boundary and implementation-gate contract is
  [contracts/phase1-transition-pilot.json](contracts/phase1-transition-pilot.json).

## Retained implementation boundary

| Concept | Authoritative Phase 3 location | Current route |
| --- | --- | --- |
| Euler-entry displacement | `tracktemplate.domain.alignment.clothoid_entry_displacement` | B16 modular default; captured B15 rollback |
| Signed tangent offset | `tracktemplate.domain.alignment.transition_start_signed_offset` | B16 modular default; captured B15 rollback |
| Transition-length solver | `tracktemplate.domain.alignment.solve_transition_length` | B16 modular default; captured B15 rollback |
| Geometry tolerance used by the slice | `tracktemplate.domain.alignment.GEOMETRY_TOLERANCE` | Domain-internal; exact legacy value `1.0e-8` |

The domain module imports only `math`. The façade imports the three domain
functions and does not contain copied function bodies. B14 and B15 remain
legacy comparison/recovery artifacts rather than a second successor
implementation.

## Direct parity evidence

`tests/validate_phase1_transition_pilot.py` now compares B14, B15 and the
modular domain implementation with exact Python value and type equality:

| Contracted evidence | Cases | Result |
| --- | ---: | --- |
| Function signature/default and full AST equality | 3 functions | Passed |
| Clothoid displacement grid | 105 argument combinations | Passed |
| Signed-offset grid | 72 argument combinations | Passed |
| Transition solver grid | 21 argument combinations | Passed |
| Exact exception type and required diagnostic text | 4 invalid cases | Passed |
| Modular changed/change-back sequence | 3 functions | Passed |

No numerical tolerance was widened. The modular function ASTs are exactly
equal to the accepted B15 function ASTs, so this is mechanical extraction
evidence rather than an independently edited approximation.

## Cache and invalidation disposition

The accepted candidate contract records no cache and no signature in these
calculation roots: callers recompute from current values. The validator runs an
A-B-A changed/change-back sequence for every extracted function and requires
the changed result to differ and the final result/type to equal the first
exactly. No speculative cache was added merely to satisfy the generic phase
gate.

This evidences the cache/invalidation exit condition as not applicable to
reuse, with current-input recomputation and change-back behaviour directly
checked. Caller- or workflow-level caching remains owned by the later slice
that introduces such state.

## All-three-callers routing and rollback evidence

`tracktemplate.compatibility.transition_pilot` is the one temporary owner of
the B15 comparison route. It verifies the frozen contract, B15 path/hash,
version and final launch boundary before executing definitions; captures the
legacy functions before rebinding; rejects an incomplete or unknown route;
and validates both direct caller bindings and the nested
solver → signed-offset → displacement closure after one three-name update.

`tests/validate_phase3_transition_routing.py` proves, without FreeCAD, that a
synthetic frozen workflow changes completely from legacy to modular and back
to the exact legacy result. It also fails closed for a source hash mismatch,
caller-contract drift, a missing modular function and a malformed final launch
boundary. The modular structure report recognises the compatibility layer and
continues to report no cycle, prohibited edge, domain dependency or warning.

In qualified FreeCAD, `tests/freecad_validate_phase3_transition_slice.py`
loads the actual byte-identical B15 source and exercises all frozen external
callers:

- `main_circle_centre` reaches the selected displacement;
- `build_concentric_core` reaches the selected displacement; and
- `prepare_track_alignment` exercises both spacing-solved and explicit-length
  branches, reaching the selected solver and signed-offset calculation.

The complete normalised caller outputs are exactly equal for
legacy → modular → legacy routing, and FreeCAD document names/object counts do
not change. This is calculation-level routed evidence, not a completed dialog,
editing, persistence or production workflow run.

The performance and owner-acceptance retirement prerequisites now pass. The
legacy route remains intentionally present because retirement is a separate
source change, not an administrative closeout edit.

## Routed full-workflow and real-GUI evidence

The development bridge now reuses the complete Phase 1 plain-line edit and
connected-straight lifecycle drivers against either B16 transition route. One
controller starts four fresh isolated FreeCAD GUI processes so no route shares
a module, document, process cache or undo stack with its comparison run. The
B16 composition definitions qualify the runtime and route the exact B15 source
before the established driver opens and operates on a copied fixture.

The controlled 2026-07-22 series passed with exact route-independent workflow
contracts:

| Workflow | Legacy/modular contract SHA-256 | Difference count | Final semantic SHA-256 |
| --- | --- | ---: | --- |
| Plain-line edit lifecycle | `85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0` | 0 | `13f707976ab749b92b768b766db58ec080e6aa7e81c9607a83849a24b644a370` |
| Connected-straight lifecycle | `2eec8269c52b8491ac546650cad1c0c6975bc620ab3a4a845f4778d8a1379517` | 0 | `8ef264901e67c8bcd8dc3305352c2efbd365fe5b04f31f2a30042cf0aa79659c` |

The comparison retains all semantic snapshots, identities, list ordering,
dialog outcomes, history counts/names, object counts, persistence, save/reopen
and failure results. It removes only measurement, undo-memory, path,
source-document and wall-time fields. The fixed input is a B14 fixture read by
the B15 workflow, so the Phase 3 adapter permits only the declared B14-to-B15
`GeneratorVersion` and production-index version labels; the raw legacy/modular
comparison retains both unnormalised results. The original strict B14 commands
were rerun and retained their accepted final hashes.

The plain-line run proves zero-angle rejection before transaction and an
injected failure after generated-output removal both leave the saved right-hand
document unchanged. Both workflows also pass their complete Undo/Redo and
save/reopen contracts, restore isolated preferences, preserve the source
fixture and leave no isolated FreeCAD process running. The full recipe,
normalisation boundary, raw-artifact hashes and limitations are recorded in
[the routed-workflow report](benchmarks/2026-07-22-b16-transition-routed-workflow-parity.md).

The single-run durations in that report are correctness observations enclosing
GUI automation and deep validation. They are not the contracted Phase 3
calculation/workflow profiles and make no optimisation claim.

## Contracted calculation and workflow performance evidence

`tools/phase3_transition_performance.py` now owns the reproducible regression
profile required by the frozen pilot contract. In one standalone CPython
process it performs one untimed warm-up and nine measured repetitions per
route of the complete 202-case parity grid, alternating route order. It then
runs three fresh isolated FreeCAD GUI processes per workflow and route—12
processes in total—again alternating route order. Every measurement retains
the established workflow parity, route-binding, fixture, history, persistence,
failure-recovery and preference-restoration checks.

The controlled 2026-07-22 profile found:

- one exact calculation result digest across all legacy/modular warm-ups and
  measured runs;
- all three paired GUI repetitions retained zero workflow-contract
  differences and the same accepted contract digests;
- every modular GUI wall-time median was no higher than legacy and all
  legacy/modular wall-time ranges overlapped;
- the sole higher modular CPU median was `+2.1 ms` (`+0.10%`) for the
  same-process plain-line change-back, inside overlapping observed ranges; and
- every paired document-object delta was exactly equal.

The standalone modular calculation observations were lower, but no speed-up is
claimed: the extracted AST is identical and the two implementations have
different loading contexts. Three GUI repetitions meet the SOP minimum but do
not set a permanent budget. Synchronous action timing excludes later viewport
repaint, RSS is an end-minus-start snapshot, the OS file cache is uncontrolled,
and this slice does not touch Validate/Export or wider trackwork paths.

The complete recipe, medians/ranges, CPU/RSS/object observations, raw-artifact
hash and limitations are recorded in
[the performance report](benchmarks/2026-07-22-b16-transition-performance-profile.md).
This closes the contracted regression evidence without introducing an
optimisation, threshold, cache, calculation change or reduced validation
scope.

## Standalone and FreeCAD loading evidence

Observed on 2026-07-22:

- the isolated import guard loaded the domain and façade while blocking
  FreeCAD, Part, Qt and pivy imports;
- the modular structure guard found the permitted façade-to-domain edge, no
  cycle, no forbidden domain import, no duplicated pilot body and a declared
  compatibility boundary;
- the current-phase orchestration check in
  `tests/freecad_validate_phase3_transition_slice.py` ran in qualified FreeCAD
  1.1.1 headless and emitted
  `Phase 3 transition routing FreeCAD smoke test passed`;
- its structured B16 result reports `transition-routing-ready`, modular
  calculation routing, explicit legacy rollback, no mixed route,
  `workflow_launched: false` and `document_mutation: false`.

The calculation-level headless route, bounded real-GUI operator workflows and
their contracted performance profiles are now evidenced. No exporter,
renderer or wider turnout/crossover workflow is claimed by this transition
slice.

## Final Phase 3 gate disposition

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| Dependency direction and FreeCAD/Qt-free domain import | Evidenced | Mechanical domain extraction, isolated import and structure guards |
| Exact legacy/new analytical equivalence | Evidenced | AST, value/type, solver and diagnostic parity above |
| Cache miss/reuse/invalidation as applicable | Evidenced | Contracted no-cache disposition and A-B-A recomputation checks |
| Applicable FreeCAD/headless, GUI and performance evidence | Evidenced | Calculation-level all-caller FreeCAD parity, routed real-GUI/persistence/failure-recovery parity, nine-repeat complete-grid calculation profile and three-repeat fresh-process workflow profiles pass without a material modular regression |
| Temporary dual-path owner and retirement gate | Evidenced | `tracktemplate.compatibility.transition_pilot` owns the complete modular/legacy routes; the evidence and acceptance prerequisites pass, while actual removal transfers to the bounded Phase 4 entry compatibility-maintenance tranche |

## Closeout acceptance and carried controls

On 2026-07-22 the project owner explicitly instructed the project to close
Phase 3 with their acceptance, commit all intended changes and push them to the
GitHub repository. This satisfies the final administrative gate and closes the
phase.

The acceptance does not combine route retirement with closeout and does not
start Phase 4:

- the modular route remains the B16 default and the captured-B15 route remains
  the explicit rollback/comparison path;
- removing that temporary route is now eligible, but remains a separate,
  reviewable Phase 4 entry compatibility-maintenance change with the same
  parity and rollback validation applicable until removal;
- B14 and B15 remain immutable behavioural/recovery oracles and are not
  retirement candidates merely because the temporary B16 switch can later be
  removed; and
- the three-run GUI sample, uncontrolled OS file cache, synchronous repaint
  exclusion and slice-only performance scope remain recorded limitations, not
  silently converted into numerical product budgets.

Phase 4 is next in the delivery order but remains not started pending explicit
project-owner instruction.

No independent backup is inferred from this evidence; the accepted temporary
backup risk and [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) controls remain
unchanged.

## Documentation lifecycle housekeeping

On 2026-07-22 the project owner accepted a smaller documentation update
surface. `PROJECT_PLAN.md` became the sole project-wide live status record;
this file served as the one open-phase evidence record and becomes accepted
historical evidence at this closeout. Closed Phase 1/2 records were marked
historical, strategy/policy documents stopped mirroring tranche progress, and
the accepted candidate/transition contract status fields were normalised to
frozen selection/requirement states. Freeze this record after the closeout
commit except for an explicit factual correction.

This was an editorial and validation-ownership change only. It did not alter
the transition calculations, public façade, caller routing, B14/B15 sources,
phase progress, railway requirements or any deferred validation gate.
