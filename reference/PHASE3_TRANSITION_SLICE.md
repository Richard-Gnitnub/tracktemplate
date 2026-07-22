# Phase 3 Transition-Length Slice Evidence

Status: **domain parity and the all-three-callers B16 routing/rollback
boundary are evidenced; Phase 3 remains current. Routed full-workflow,
failure-recovery, real-GUI and contracted performance evidence remain open.**

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
that full workflow is not claimed as accepted by this tranche.

No B14 or B15 source changed. No calculation implementation was copied into
the launcher, façade or compatibility adapter, and no cleanup, validation
hardening, tolerance change or optimisation is included.

## Exact source state

The tranche started from accepted Phase 2 closeout commit
`55af5cf26ac82ba081bc3f3bc9ce40cce107c461`.
The routing/rollback tranche started from pushed documentation-lifecycle
checkpoint `cbee8260b5e0ea7852c6e16b5195861d6501a617`.

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

The compatibility owner is Phase 3. Its legacy route cannot retire until the
remaining full-workflow, GUI, failure-recovery and performance evidence passes
and the project owner explicitly accepts the Phase 3 closeout.

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

No real-GUI workflow run is claimed; only the calculation callers have been
exercised without launching the operator workflow.

## Current Phase 3 gate disposition

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| Dependency direction and FreeCAD/Qt-free domain import | Evidenced | Mechanical domain extraction, isolated import and structure guards |
| Exact legacy/new analytical equivalence | Evidenced | AST, value/type, solver and diagnostic parity above |
| Cache miss/reuse/invalidation as applicable | Evidenced | Contracted no-cache disposition and A-B-A recomputation checks |
| Applicable FreeCAD/headless, GUI and performance evidence | Active | Calculation-level all-caller FreeCAD parity passes; routed plain-line and connected-straight full-workflow, failure-recovery, real-GUI and contracted calculation/workflow profiles remain required |
| Temporary dual-path owner and retirement gate | Evidenced | One compatibility session owns complete modular/legacy routes, the B16 default and explicit rollback are tested, and retirement remains gated by Phase 3 evidence plus owner acceptance |

## Remaining tranche gates

1. Run the affected plain-line and connected-straight headless/real-GUI
   oracles, including failure recovery and no document corruption.
2. Record the calculation and comparable workflow performance profiles without
   presenting this architecture extraction as an optimisation.
3. Request explicit project-owner acceptance before retiring any temporary
   comparison path or closing Phase 3.

No independent backup is inferred from this evidence; the accepted temporary
backup risk and [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) controls remain
unchanged.

## Documentation lifecycle housekeeping

On 2026-07-22 the project owner accepted a smaller documentation update
surface. `PROJECT_PLAN.md` became the sole project-wide live status record;
this file remains the one open-phase evidence record. Closed Phase 1/2 records
were marked historical, strategy/policy documents stopped mirroring tranche
progress, and the accepted candidate/transition contract status fields were
normalised to frozen selection/requirement states.

This was an editorial and validation-ownership change only. It did not alter
the transition calculations, public façade, caller routing, B14/B15 sources,
phase progress, railway requirements or any deferred validation gate.
