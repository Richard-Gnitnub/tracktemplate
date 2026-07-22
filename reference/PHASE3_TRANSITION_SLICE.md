# Phase 3 Transition-Length Slice Evidence

Status: **first calculation tranche evidenced; Phase 3 remains current. Legacy
workflow caller routing, the routed rollback switch, GUI workflow evidence and
the contracted performance profiles remain open.**

## Bounded result

The accepted three-function transition-length calculation is mechanically
extracted into `tracktemplate.domain.alignment` and re-exported through the
temporary `tracktemplate.api` façade. The B16 launcher can load that API in
standalone Python and the qualified FreeCAD runtime, but it still reports
`calculation_routing: not-started` and performs no document mutation.

No B14 or B15 source changed. No legacy global name or external caller is
routed to the modular implementation, no compatibility implementation was
copied into the launcher or façade, and no cleanup, validation hardening,
tolerance change or optimisation is included.

## Exact source state

The tranche started from accepted Phase 2 closeout commit
`55af5cf26ac82ba081bc3f3bc9ce40cce107c461`.

- B14 remains
  `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`.
- B15 remains
  `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`.
- The exact accepted selection, boundary and implementation-gate contract is
  [contracts/phase1-transition-pilot.json](contracts/phase1-transition-pilot.json).

## Retained implementation boundary

| Concept | Authoritative Phase 3 location | Current route |
| --- | --- | --- |
| Euler-entry displacement | `tracktemplate.domain.alignment.clothoid_entry_displacement` | Temporary façade export only |
| Signed tangent offset | `tracktemplate.domain.alignment.transition_start_signed_offset` | Temporary façade export only |
| Transition-length solver | `tracktemplate.domain.alignment.solve_transition_length` | Temporary façade export only |
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

## Standalone and FreeCAD loading evidence

Observed on 2026-07-22:

- the isolated import guard loaded the domain and façade while blocking
  FreeCAD, Part, Qt and pivy imports;
- the modular structure guard found the permitted façade-to-domain edge, no
  cycle, no forbidden domain import and no duplicated pilot body;
- the current-phase orchestration check in
  `tests/freecad_validate_phase3_transition_slice.py` ran in qualified FreeCAD
  1.1.1 headless and emitted
  `Phase 3 transition domain smoke test passed`;
- its structured B16 result retained `foundation-loaded-not-routed`,
  `calculation_routing: not-started` and `document_mutation: false`.

No real-GUI workflow run is claimed because no workflow caller is routed.

## Current Phase 3 gate disposition

| Exit condition | State | Evidence or remaining work |
| --- | --- | --- |
| Dependency direction and FreeCAD/Qt-free domain import | Evidenced | Mechanical domain extraction, isolated import and structure guards |
| Exact legacy/new analytical equivalence | Evidenced | AST, value/type, solver and diagnostic parity above |
| Cache miss/reuse/invalidation as applicable | Evidenced | Contracted no-cache disposition and A-B-A recomputation checks |
| Applicable FreeCAD/headless and GUI evidence | Active | Loading-only headless evidence passes; routed plain-line and connected-straight GUI workflows remain required |
| Temporary dual-path owner and retirement gate | Pending | Implement one all-three-callers B16 routing/rollback switch; retain it until Phase 3 parity evidence and explicit owner acceptance |

## Remaining tranche gates

1. Add the B16-only composition/routing boundary without editing B14 or B15.
2. Route all three frozen external callers together; do not create a mixed
   legacy/modular calculation closure.
3. Implement the contracted switch back to the captured B15 calculations
   before exercising a routed workflow.
4. Run the affected plain-line and connected-straight headless/real-GUI
   oracles, including failure recovery and no document corruption.
5. Record the calculation and comparable workflow performance profiles without
   presenting this architecture extraction as an optimisation.
6. Request explicit project-owner acceptance before retiring any temporary
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
