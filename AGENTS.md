# Project guidance

## Instruction order

- This file contains the repository's short, always-on development rules. Do not
  turn it into a repository history, command catalogue or duplicate project plan.
- Read `reference/PROJECT_PLAN.md` before source work to identify the current
  phase, open gates and accepted scope.
- When resuming work after a new session, compaction or interrupted handoff, use
  `$tracktemplate-context-recovery` to reload the controlling documents. Treat
  commits and diffs as implementation evidence, not as requirement or decision
  authority.
- Read the canonical document that owns the affected subject before editing.
  The document ownership map below is authoritative.
- `reference/AGENT_WORKFLOWS.md` defines the repository's agent-skill strategy.
  Use `$tracktemplate-python-writing` when creating or materially editing Python
  or FCMacro source.
  Use `$tracktemplate-documentation-review` when creating or materially editing
  Markdown documentation. Use `$tracktemplate-change-validation` to select, run
  and report the applicable evidence for a non-trivial change. Use
  `$tracktemplate-quality-review` before reporting completion of a non-trivial
  source or documentation change.
- A skill is a reusable workflow, not a source of project authority. If a skill
  conflicts with this file or a canonical reference document, follow the
  canonical project rule and report the conflict.

## Purpose and Priorities

- TrackTemplate develops a FreeCAD system for parametric model-railway track
  templates, including plain line, turnouts, crossovers, timbering, chairs,
  persistence, display, and production export.
- Railway correctness, recoverability, and production integrity take priority
  over speed or aesthetic clean-up.
- Treat performance work as behaviour-preserving unless the project owner
  explicitly accepts a behaviour change.
- Inspect the implementation that actually runs and capture a repeatable
  baseline before refactoring. Do not redesign from intuition alone.

## Canonical Document Ownership

- `reference/PROJECT_PLAN.md` is the sole project-wide live status record. It
  owns the current phase, progress, gates, live risks and acceptance state.
- `reference/ARCHITECTURE.md` owns strategic model, persistence, display,
  validation, export and product boundaries.
- `reference/MODULARISATION_PLAN.md` owns source boundaries, dependency
  direction, extraction gates and temporary-duplicate retirement.
- `reference/VALIDATION.md` selects the applicable validation layers and verified
  commands; `reference/TESTING_POLICY.md` owns test and oracle-change rules.
- `reference/PERFORMANCE_SOP.md` owns benchmark procedure and evidence quality.
- `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md` own source,
  data, evidence, package and output classification.
- `reference/RECOVERY_AND_BACKUP.md` owns destructive-action, checkpoint,
  backup-scope and restore policy.
- `reference/TERMINOLOGY.md` owns accepted railway terminology and migration of
  frozen identifiers.
- `reference/QUALITY_ASSURANCE.md` is the canonical dated QA audit and
  immediate-action record.
- `reference/LEARNING_FROM_EXPERIENCE.md` is the append-only historical lesson
  ledger and owns no live phase status, requirement, risk or acceptance state.
- `reference/AGENT_WORKFLOWS.md` owns agent-skill scope, invocation and
  maintenance. It owns no product requirement or delivery status.
- Accepted phase closeouts, inventories, baselines, foundations and JSON
  contracts are frozen historical or contractual evidence. Change them only to
  correct a demonstrated factual error or an explicitly accepted scope change.

## Version and Architecture Boundaries

- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle.
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro`
  is the accepted B15 behavioural reference.
- `TrackTemplate.FCMacro` and the modular `tracktemplate` package form the B16
  development checkpoint. The package is the future authoritative product;
  legacy macros remain migration, compatibility or comparison surfaces.
- Never edit B14 to make a newer implementation pass. Change an accepted oracle
  only when evidence proves the oracle is wrong or the accepted requirement has
  changed.
- The authoritative state is the parametric railway model: configuration,
  stable identities, topology, analytical results and production intent.
  Viewport geometry, SVG, Coin nodes, caches and exact solids are derived views.
- Routine editing should use lightweight 2D presentation. Construct exact Part
  shapes and production solids only at an explicit validation/export boundary
  or where the accepted architecture requires them.
- Migrate incrementally behind equivalence checks. Do not attempt a whole-macro
  rewrite or remove a legacy path before parity evidence and project-owner
  acceptance.

## Scope and Change Discipline

- Confirm the exact target and authority before editing. Do not assume a change
  belongs in B14, B15, B16 or every layer.
- Make the smallest coherent, reviewable change that satisfies the request.
- Implement non-trivial work in small, independently checkable slices and run
  the nearest useful check after each slice. For large mechanical or bulk
  changes, prove a representative pilot before scaling.
- Keep mechanical extraction, clean-up, behaviour change and performance work in
  separately reviewable steps with their own evidence.
- Keep one authoritative implementation for each genuinely shared railway or
  application concept behind a narrow, cohesive and tested interface.
- Give every temporary duplicate a named owner and retirement gate. Do not let a
  disposable prototype become an undocumented second implementation.
- Preserve UTF-8 and compatibility with the qualified FreeCAD runtime and its
  bundled Python, FreeCAD, Part, FreeCADGui, Qt/PySide and pivy environment.
- Do not add a third-party runtime dependency without explicit approval.
- Do not silently change geometry, units, frames, sampling, tolerances,
  topology gates, timber decisions, chair assignments, stable identities,
  ordering, schemas, persistent property names, visibility, transactions,
  rollback, cache invalidation or exporter results.
- Preserve transactional behaviour. Validate replacement geometry before
  committing document changes, and keep every failure path recoverable.
- Do not weaken validation, suppress diagnostics or reduce geometric fidelity to
  obtain a cleaner diff or faster timing result.
- Add proportionate automated evidence for every non-trivial behaviour change.
  Pure/domain functions normally require direct tests; FreeCAD and GUI
  orchestration require the applicable integration boundary.
- Do not change a test merely to make an implementation pass. Explain and prove
  any accepted oracle change.
- When a test fails, preserve the raw failure and classify it under
  `reference/TESTING_POLICY.md` before editing retained source, tests or
  fixtures. Rerun the original proof after the classified repair.

## Repository and System Safety

- Read `reference/RECOVERY_AND_BACKUP.md` before deletion, bulk rewriting,
  history operations, system changes, backup work or use of operator-owned
  FreeCAD documents.
- Never run `git clean` in this repository. Ignored paths include source
  evidence, copied FCStd files, raw benchmarks, exports and recovery files that
  Git and GitHub do not protect.
- Do not use `git reset --hard`, destructive `git checkout` or `git restore`,
  force push, branch or tag deletion, or broad recursive deletion during routine
  work.
- Never target `/`, `$HOME`, `~`, the workspace root, unresolved variables,
  wildcards or command substitutions for deletion, overwrite or recursive move.
- Do not run the IDE, FreeCAD automation or project tools as root. Treat `sudo`
  and system-file changes as separate authority boundaries.
- Timeshift system snapshots do not cover the current `/home/richard` project
  data.
- Before risky or bulk work, run `tools/repository_safety_audit.py`, establish
  the required recoverable checkpoint and use a dedicated branch or disposable
  worktree.
- Use copied or disposable FCStd inputs for automation. Never open, mutate or
  save over the only copy of an operator document.
- Do not commit, push, merge or open a pull request unless the user asks.
- Keep `.idea/`, `.venv/`, `__pycache__/`, generated FreeCAD documents, exports,
  and temporary benchmark artefacts out of commits.

## Licensing and provenance

- Read `reference/LICENSING_BOUNDARIES.md`, `reference/PROVENANCE.md` and the
  applicable lineage or manifest before changing output-affecting constants,
  tables, profiles, chair definitions, fixtures, exporters or embedded media.
- Distinguish engineering methods and facts from potentially copyrightable
  source expression, comments, tables, selection, arrangement, and close
  translation. Do not make unsupported clean-room or independent-derivation
  claims.
- Templot-generated media and unresolved Templot-authored value collections are
  local comparison evidence, not canonical production input, unless the exact
  permission and project admission gate is accepted.
- Do not mark a package or output `project-cleared` while any output-affecting
  dependency remains restricted, reference-only, unknown, `NOASSERTION` or
  incompatible with the intended use.
- Preserve `LICENSE`, `NOTICE.md`, contributor declarations and applicable
  upstream notices.

## Railway terminology

- Use **plain line** or **plain line track** for track without switches and
  crossings.
- Do not introduce **ordinary track** in new prose, UI, schemas or APIs. Existing
  `ordinary_track*` names are frozen evidence or compatibility identifiers and
  require an accepted migration before renaming.
- Do not guess at uncertain railway terminology. Follow
  `reference/TERMINOLOGY.md` and its review process.

## Phase and documentation discipline

- Read the current phase and gate register from `reference/PROJECT_PLAN.md`; do
  not copy live phase status into this file, skills, accepted history or durable
  contracts.
- Progress counts evidenced exit conditions, not elapsed time or estimated
  effort. Do not claim a phase transition without its evidence and project-owner
  acceptance.
- From Phase 4 onward, run the mandatory safety/risk panel defined in
  `reference/PROJECT_PLAN.md` before phase, milestone, release-candidate or
  authority-changing gate closeout.
- Record each live risk with one treatment: **Tolerate**, **Remove** or
  **Mitigate**, plus an accountable owner, deadline, required work and objective
  closure evidence.
- Give every fact one owning document and link to it. Do not copy command lists,
  repository maps, live status or detailed evidence into multiple files.
- A normal implementation tranche should update only product code, directly
  relevant tests, the open-phase evidence record and the project plan. Change an
  additional document only when its owned policy or responsibility changed.

## Validation and evidence

- Select checks from `reference/VALIDATION.md` according to the changed scope.
  Do not maintain a second command catalogue here.
- At minimum, parse every changed Python or macro file and run the directly
  relevant standalone tests.
- Use the qualified FreeCAD profile for host-dependent checks. A process exit
  code without the required success sentinel is not evidence that assertions
  ran.
- Headless checks do not replace a real GUI workflow for geometry, display,
  selection, document integration, export, or operator-visible performance.
- For performance work, follow `reference/PERFORMANCE_SOP.md`, compare equivalent
  starting states and report cache/process differences and measurement noise.
- Never invent a result that is visible only in FreeCAD. Use the approved
  isolated bridge or state that GUI validation remains outstanding.
- After adding, renaming or moving a skill, start a fresh Codex session and use
`/skills` to confirm that every repository skill appears with the expected name
and description.

## Completion and review

- Review the complete diff for accidental broad rewrites, duplicated policy,
  speculative abstractions, misleading comments and unrelated changes.
- Run `$tracktemplate-change-validation` for a non-trivial change when the
  applicable evidence layers or remaining checks need to be selected and
  reported.
- Run `$tracktemplate-quality-review` for non-trivial code or documentation
  changes before reporting completion.
- Treat the first staff-review pass as read-only. Prefer a fresh reviewer when
  available, provide raw diffs and validation evidence, and disclose when the
  review was not independent.
- State what changed, which version or authority boundary changed, which
  invariants were preserved, which checks actually ran and what remains
  unverified.
- For geometry, persistence, display, export, or performance changes, identify any
  GUI evidence still required.
- For licensing, provenance, data, chair-package or output changes, state the
  affected classifications and every remaining non-cleared dependency.
