# Project guidance

## Authority and startup

- Follow system/user instructions, then this file, then the canonical subject owner.
- Read [`reference/PRODUCT_VISION.md`](reference/PRODUCT_VISION.md) for product purpose, the current Core programme and the later Layout Editor horizon.
- Then read [`reference/PROJECT_PLAN.md`](reference/PROJECT_PLAN.md) for the active programme, phase, exit status, live risks and owner decisions.
- Read [`reference/current/PHASE_EVIDENCE.md`](reference/current/PHASE_EVIDENCE.md)
  and its JSON registers for current evidence, live risks and decisions.
- Read the canonical subject owner before editing; the plan links those owners.
- After compaction, interruption or an unfamiliar dirty tree, use the
  context-recovery workflow in [`reference/AGENT_WORKFLOWS.md`](reference/AGENT_WORKFLOWS.md).
- Treat source, tests, commits and diffs as implementation evidence, not as
  requirement or decision authority.

## Product and version boundaries

- TrackTemplate is a FreeCAD-native Workbench for parametric model-railway
  templates; railway correctness, recovery and production integrity come first.
- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle.
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro`
  is the accepted B15 behavioural reference.
- `TrackTemplate.FCMacro` and the modular `tracktemplate` package are the B16
  development checkpoint. The package is the future authoritative product.
- TrackTemplate Core migration is the current programme. The Layout Editor is
  subsequent; its extension direction does not authorise current implementation
  or alter an active phase exit.
- Never edit B14 to make a later implementation pass. Change an accepted oracle
  only after a demonstrated defect or accepted requirement change.
- Canonical railway intent, identities, topology, analysis and production intent
  are authoritative; viewport, cache, SVG, Coin and exact solids are derived.
- Use lightweight 2D routine presentation; build exact geometry only at an
  explicit validation/export boundary unless architecture says otherwise.
- Migrate incrementally behind equivalence checks. Do not remove a legacy path
  before its parity, recovery and owner-acceptance conditions are met.

## Work selection and accountability

- Do not select work mechanically from plan entries, reviews, branches or source
  shape; select one repository-evidenced bounded gap.
- Before implementation, state product outcome, active phase criterion, gap
  evidence, change level, acceptance evidence and explicit non-goals.
- Trace assignment → work item → finding/exit → current programme → vision;
  vision never widens scope.
- Keep files and intervention narrow; preserve finding ownership and failed
  evidence, and avoid unrelated refactoring.
- Work claimed, present, validated and independently accepted are distinct; an
  implementer cannot solely accept its work.

## Proportional change discipline

- Classify every task under [`reference/ENGINEERING_POLICY.md`](reference/ENGINEERING_POLICY.md) as
  **Level 1 — Routine**, **Level 2 — Behavioural** or
  **Level 3 — Authority or release**.
- Level 1 needs the relevant test, complete diff review and concise commit, but
  no phase evidence, risk panel or plan update unless reclassified.
- Level 2 needs the relevant specialist skill, automated and applicable
  FreeCAD/GUI validation, one current-evidence entry and complete diff review.
- Level 3 needs full evidence review, a risk panel, explicit owner decision and
  project-plan update; only Level 3 work is a gate.
- Governance changes must not exceed implementation changes unless the task
  changes governance, licensing, safety or release authority; record why.
- Make the smallest coherent, reviewable change. Keep extraction, cleanup,
  behaviour change and performance work separately checkable.
- Do not silently change geometry, units, frames, sampling, tolerances, topology,
  timbering, chairs, stable identities, ordering, schemas, stored properties, visibility, transactions, rollback, cache invalidation or output.
- Give temporary duplication one owner and a retirement condition.
- Preserve compatibility with the qualified FreeCAD runtime and its bundled
  Python, FreeCAD, Part, FreeCADGui, Qt/PySide and pivy environment.
- Do not add a third-party runtime dependency without explicit approval.

## Canonical policy links

- [`reference/ARCHITECTURE.md`](reference/ARCHITECTURE.md) owns strategic state,
  display, persistence, validation and export boundaries.
- [`reference/MODULARISATION_PLAN.md`](reference/MODULARISATION_PLAN.md) owns
  source boundaries and dependency direction.
- [`reference/VALIDATION.md`](reference/VALIDATION.md) and [`reference/TESTING_POLICY.md`](reference/TESTING_POLICY.md) own validation, failure classification and oracle changes.
- [`reference/RECOVERY_AND_BACKUP.md`](reference/RECOVERY_AND_BACKUP.md) owns
  checkpoints, backups, destructive operations and restore evidence.
- [`reference/LICENSING_BOUNDARIES.md`](reference/LICENSING_BOUNDARIES.md) and [`reference/PROVENANCE.md`](reference/PROVENANCE.md) own rights/lineage.
- [`reference/QUALITY_ASSURANCE.md`](reference/QUALITY_ASSURANCE.md) is a frozen
  audit; [`reference/LEARNING_FROM_EXPERIENCE.md`](reference/LEARNING_FROM_EXPERIENCE.md)
  is an append-only lesson ledger. Neither owns live status.
- [`reference/AGENT_WORKFLOWS.md`](reference/AGENT_WORKFLOWS.md) owns the skill catalog and routing.
- Canonical prose follows the [Technical Documentation Profile](reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile). Use the documentation workflow and use its STE lookup first. The STE lookup changes the source text that an agent reads for this task. It does not narrow the applicable Issue 9 requirement set.

## Repository and System Safety

- Read the recovery policy before deletion, bulk rewriting, history operations,
  system/backup work or use of operator-owned FreeCAD documents.
- Never run `git clean`; ignored paths contain evidence and operator data that
  Git and GitHub do not protect.
- Do not use destructive reset/checkout/restore, force push, branch/tag deletion
  or broad recursive deletion during routine work.
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
  **ordinary track** in new prose, UI, schemas or APIs; existing identifiers are frozen compatibility evidence.
- Do not guess railway terms or standards-derived values. Follow the terminology
  and specialist-policy links from the workflow catalogue.
- Read the rights owners before changing output-affecting constants, tables,
  chair definitions, fixtures, exporters or embedded media.
- Never call a package or output `project-cleared` while an output-affecting
  dependency is restricted, reference-only, unknown, `NOASSERTION` or
  incompatible with its intended use.
- Keep document mutations transactional. Validate replacement state before
  commit and preserve visible diagnostics and recoverable failure paths.

## Validation and completion

- Parse each changed Python or macro file and run relevant standalone checks.
  Let tracked CI run the full standalone governance,
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
- For substantial cycles, use the derived owner view in the [Engineering Policy](reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
  and keep technical provenance beneath it.
- State remaining uncertainty plainly. Validation never implies a phase,
  migration, output-clearance or release decision without owner acceptance.
