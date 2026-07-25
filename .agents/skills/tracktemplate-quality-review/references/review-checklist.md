# TrackTemplate quality-review checklist

Use only the sections relevant to the change.

## Scope

- Exact target version, module and workflow identified.
- Current phase and authority checked in `reference/PROJECT_PLAN.md`.
- No unrelated feature, cleanup or refactor included.
- Mechanical movement separated from behaviour and performance changes.

## Architecture and source

- One authoritative implementation per shared invariant.
- Dependency direction matches `reference/MODULARISATION_PLAN.md`.
- Temporary duplicate has an owner and retirement gate.
- No speculative module, wrapper, option or extension point.
- No third-party runtime dependency without approval.

## Railway and geometry

- Units and coordinate frames explicit.
- Geometry, tolerance, sampling and topology changes identified.
- Timber and chair decisions remain deterministic.
- Stable identities and ordering remain stable or have accepted migration.
- Preview/display does not become production truth.

## FreeCAD lifecycle

- Transactions remain atomic.
- Preflight occurs before document mutation.
- Failure paths roll back cleanly.
- Undo/Redo and save/reopen considered where applicable.
- Recompute, visibility, selection and transient objects considered.
- Operator documents replaced by copied or disposable fixtures.

## Persistence and caching

- Canonical state remains authoritative.
- Derived state has complete signatures.
- Relevant input classes invalidate caches.
- Stale or corrupt derived data fails closed or regenerates safely.
- Versionless, future or conflicting state remains inspection-only or blocked.

## Documentation

- Each fact has one owning document.
- Links replace repeated technical payloads.
- Live status appears only in `reference/PROJECT_PLAN.md`.
- Accepted history is not rewritten to match later knowledge.
- Comments explain why or constraints, not obvious syntax.
- No unsupported completion, legal or output-rights claims.

## Testing and evidence

- Changed Python and macros parse.
- Direct analytical tests cover changed pure/domain behaviour.
- Qualified FreeCAD checks cover host-dependent behaviour.
- Real-GUI evidence exists where headless checks are insufficient.
- Export and performance claims use the prescribed procedures.
- Existing oracles changed only with evidence and acceptance.
- Success sentinels and exact results recorded.

## Repository hygiene

- Diff contains only intended files.
- No `.idea`, `.venv`, caches, generated FCStd, exports or raw benchmark output.
- No whole-file reformatting of legacy macros.
- No destructive Git or filesystem action outside the recovery policy.
- No commit, push or PR without user authority.
