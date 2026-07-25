# TrackTemplate quality-review checklist

Apply only the sections relevant to the complete change.

## Scope and authority

- The requested scope, affected files and complete relevant diff have been inspected.
- The affected architectural boundary and railway boundary have been identified.
- Only canonical project documents relevant to the change have been read.
- Unrelated formatting, refactoring, renaming or cleanup has not been included.

## Complexity and duplication

- No unnecessary abstraction has been introduced.
- No authoritative logic has been duplicated.
- No speculative helper, option, configuration or extension point has been added.
- No wrapper is used once without improving clarity, isolation or a defined invariant.
- Temporary compatibility code has an owner, purpose and retirement gate.
- Apparent repetition has not been removed until its FreeCAD, compatibility, recovery, evidence or performance purpose has been checked.

## Comments and failure handling

- Comments explain a non-obvious reason, constraint or boundary rather than merely repeating the code.
- Comments are not misleading, stale or broader than the evidence.
- Broad exception handling does not hide failures, discard diagnostics or convert invalid state into apparent success.
- Failure paths remain visible, diagnosable and recoverable.

## Behaviour and compatibility

- FreeCAD compatibility code remains intact unless an evidenced change requires otherwise.
- Transactions, rollback, diagnostics and recompute behaviour remain correct.
- Geometry, topology, tolerances, stable identities and ordering remain unchanged unless explicitly intended and validated.
- Exporter selection, naming, ordering, content and failure behaviour remain unchanged unless explicitly intended and validated.
- Public APIs, persisted state, stored schemas and compatibility contracts have not changed accidentally.
- Legacy evidence and accepted compatibility boundaries remain preserved.

## Performance and data flow

- No unnecessary metadata has been added or retained without a defined consumer.
- Calculations, geometry construction, conversions and lookups are not repeated without need.
- Caching or reuse does not weaken invalidation, determinism or correctness.
- Performance claims use the prescribed project procedure and identify the measured boundary.

## Validation and claims

- Validation has not been weakened, bypassed or changed merely to restore a pass.
- Tests and checks exercise the intended behaviour rather than only the implementation shape.
- Claims that FreeCAD, GUI, export or performance testing succeeded are supported by recorded evidence.
- Headless validation is not described as real-GUI acceptance.
- Remaining checks and evidence gaps are stated explicitly.

## Diff hygiene

- No unrelated source, test, documentation, generated output, IDE file or repository status has changed.
- No broad mechanical cleanup or automatic “AI authenticity” scoring has been used.
- Findings distinguish verified defects from preferences and optional improvements.
