# Project guidance

## Authority and startup

- Follow system and user instructions first, then this file, then the canonical
  project document that owns the subject.
- Start with [`reference/PROJECT_PLAN.md`](reference/PROJECT_PLAN.md) for the
  current phase, exit-condition status, live-risk summary and owner decisions.
- Read [`reference/current/PHASE_EVIDENCE.md`](reference/current/PHASE_EVIDENCE.md)
  for current implementation evidence and the JSON registers beside it for
  detailed live risks and decisions.
- Read the canonical subject owner before editing. Architecture, engineering
  policy, validation, licensing, provenance and agent workflow ownership are
  linked from the project plan.
- On resumption after compaction, interruption or an unfamiliar dirty tree, use
  the context-recovery workflow in
  [`reference/AGENT_WORKFLOWS.md`](reference/AGENT_WORKFLOWS.md).
- Treat source, tests, commits and diffs as implementation evidence, not as
  requirement or decision authority.

## Product and version boundaries

- TrackTemplate develops a FreeCAD system for parametric model-railway track
  templates. Railway correctness, recoverability and production integrity take
  priority over speed or cosmetic cleanup.
- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle.
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro`
  is the accepted B15 behavioural reference.
- `TrackTemplate.FCMacro` and the modular `tracktemplate` package are the B16
  development checkpoint. The package is the future authoritative product.
- Never edit B14 to make a later implementation pass. Change an accepted
  oracle only after a demonstrated oracle defect or an accepted requirement
  change.
- Canonical railway intent, stable identities, topology, analytical results and
  production intent are authoritative. Viewport geometry, caches, SVG, Coin
  nodes and exact solids are derived views.
- Use lightweight 2D presentation for routine editing. Build exact geometry at
  an explicit validation or export boundary unless the architecture says
  otherwise.
- Migrate incrementally behind equivalence checks. Do not remove a legacy path
  before its parity, recovery and owner-acceptance conditions are met.

## Proportional change discipline

- Classify every task under
  [`reference/ENGINEERING_POLICY.md`](reference/ENGINEERING_POLICY.md) as
  **Level 1 — Routine**, **Level 2 — Behavioural** or
  **Level 3 — Authority or release**.
- Level 1 needs the relevant test, complete diff review and concise commit, but
  no phase evidence, risk panel or plan update unless reclassified.
- Level 2 needs the relevant specialist skill, automated and applicable
  FreeCAD/GUI validation, one current-evidence entry and complete diff review.
- Level 3 needs full evidence review, a risk panel, explicit owner decision and
  project-plan update; only Level 3 work is a gate.
- Governance changes must not exceed implementation changes unless the task
  itself changes governance, licensing, safety or release authority. Record
  the reason when that exception applies.
- Make the smallest coherent, reviewable change. Keep extraction, cleanup,
  behaviour change and performance work separately checkable.
- Do not silently change geometry, units, frames, sampling, tolerances,
  topology, timbering, chairs, stable identities, ordering, schemas, stored
  properties, visibility, transactions, rollback, cache invalidation or output.
- Give temporary duplication one owner and a retirement condition.
- Preserve compatibility with the qualified FreeCAD runtime and its bundled
  Python, FreeCAD, Part, FreeCADGui, Qt/PySide and pivy environment.
- Do not add a third-party runtime dependency without explicit approval.

## Canonical policy links

- [`reference/ARCHITECTURE.md`](reference/ARCHITECTURE.md) owns strategic
  product, state, display, persistence, validation and export boundaries.
- [`reference/MODULARISATION_PLAN.md`](reference/MODULARISATION_PLAN.md) owns
  source boundaries and dependency direction.
- [`reference/VALIDATION.md`](reference/VALIDATION.md) and
  [`reference/TESTING_POLICY.md`](reference/TESTING_POLICY.md) own validation
  selection, failed-test classification and oracle-change rules.
- [`reference/RECOVERY_AND_BACKUP.md`](reference/RECOVERY_AND_BACKUP.md) owns
  checkpoints, backups, destructive operations and restore evidence.
- [`reference/LICENSING_BOUNDARIES.md`](reference/LICENSING_BOUNDARIES.md) and
  [`reference/PROVENANCE.md`](reference/PROVENANCE.md) own rights and lineage.
- [`reference/QUALITY_ASSURANCE.md`](reference/QUALITY_ASSURANCE.md) is a frozen
  audit; [`reference/LEARNING_FROM_EXPERIENCE.md`](reference/LEARNING_FROM_EXPERIENCE.md)
  is an append-only lesson ledger. Neither owns live status.
- [`reference/AGENT_WORKFLOWS.md`](reference/AGENT_WORKFLOWS.md) owns the full
  specialist-skill catalogue and invocation routing.

## Repository and System Safety

- Read the recovery policy before deletion, bulk rewriting, history operations,
  system changes, backup work or use of operator-owned FreeCAD documents.
- Never run `git clean`; ignored paths contain evidence and operator data that
  Git and GitHub do not protect.
- Do not use destructive reset, checkout or restore, force push, branch or tag
  deletion, or broad recursive deletion during routine work.
- Never target `/`, `$HOME`, `~`, the workspace root, unresolved variables,
  wildcards or command substitutions for deletion, overwrite or recursive move.
- Do not run the IDE, FreeCAD automation or project tools as root.
- Timeshift system snapshots do not cover the current project data.
- Before risky or bulk work, run `tools/repository_safety_audit.py`, establish
  the required recoverable checkpoint and use a disposable target where needed.
- Use copied FCStd inputs for automation. Never mutate the only copy of an
  operator document.
- Do not commit, push, merge, tag or open a pull request unless the user asks.
- Keep IDE state, virtual environments, caches, generated FreeCAD files,
  exports and raw benchmark output out of commits.

## Railway, rights and persistence safeguards

- Use **plain line** for track without switches and crossings. Do not introduce
  **ordinary track** in new prose, UI, schemas or APIs; existing identifiers are
  frozen compatibility evidence.
- Do not guess railway terms or standards-derived values. Follow the terminology
  and specialist-policy links from the workflow catalogue.
- Read the licensing and provenance owners before changing output-affecting
  constants, tables, chair definitions, fixtures, exporters or embedded media.
- Never call a package or output `project-cleared` while an output-affecting
  dependency is restricted, reference-only, unknown, `NOASSERTION` or
  incompatible with its intended use.
- Keep document mutations transactional. Validate replacement state before
  commit and preserve visible diagnostics and recoverable failure paths.

## Validation and completion

- Parse each changed Python or macro file and run the directly relevant
  standalone checks. Let tracked CI run the full standalone governance,
  contract, dependency, hash, link and progress matrix.
- Classify every failure under the testing policy before changing retained
  source, tests, fixtures or oracles. Rerun the original proof after repair.
- Use the qualified FreeCAD profile for host checks. A process exit without its
  success sentinel is not evidence.
- Headless checks do not replace real-GUI evidence for display, selection,
  operator workflows, persistence, export or visible performance.
- Review the complete diff for unrelated changes, duplicated policy, weakened
  checks, speculative abstractions and misleading claims.
- Use the validation and quality workflows for non-trivial work; the first
  review pass is read-only and any independence limitation is disclosed.
- Report completion under four headings only when applicable: **Changed**,
  **Validated**, **GUI work outstanding**, and **Risks or authority changes**.
- State remaining uncertainty plainly. Validation never implies a phase,
  migration, output-clearance or release decision without owner acceptance.
