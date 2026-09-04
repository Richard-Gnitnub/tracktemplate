---
name: tracktemplate-simplify
description: Simplify a bounded TrackTemplate source, test, documentation or agent-guidance target while preserving verified behaviour and project authority. Use when asked to reduce complexity, remove duplication, tighten structure, delete dead code or make an implementation easier to understand without changing railway outcomes.
---

# TrackTemplate simplification

## Outcome

Remove proven accidental complexity while preserving railway behaviour,
recoverability, FreeCAD compatibility, evidence integrity and production
boundaries. Prefer the smallest simplification whose benefit is visible in the
resulting code or documentation.

## Responsibility boundary

This skill selects and controls a simplification pass. Use the established
specialist workflow for the material being changed:

- use `$tracktemplate-python-writing` for Python or FCMacro edits;
- use `$tracktemplate-technical-author-lead` for material canonical Markdown
  edits, then use one Documentation Review after candidate freeze;
- use `$tracktemplate-documentation-alignment` when claims or paths may drift;
- use `$tracktemplate-change-validation` to establish and rerun the proof; and
- use `$tracktemplate-quality-review` for the final complete-diff judgement of
  a separate source or test change.

For canonical governance prose, the one Documentation Review, permitted
adjustment and final deterministic validation finish the document-review
cycle. Do not add a quality, publication, CI, wording or semantic review.

Do not use simplification as authority to change accepted behaviour,
architecture, railway terminology, tests, oracles, schemas, persisted names,
licensing classifications or phase scope.

## Preparation

1. Name the exact target and desired simplification. Keep adjacent cleanup out
   of scope unless it is necessary to complete the same coherent change.
2. Read `reference/PROJECT_PLAN.md`, the canonical owner of the affected
   subject and `reference/MODULARISATION_PLAN.md` for source-boundary changes.
3. Read `reference/RECOVERY_AND_BACKUP.md` before deletion, broad movement or a
   bulk rewrite. Establish the required checkpoint for risky work.
4. Inspect the implementation that actually runs, its callers, imports,
   stored/public identifiers, tests, fixtures, documentation links and
   generated consumers.
5. Capture a repeatable pre-change baseline at the narrowest boundary that
   proves the preserved behaviour. Separate standalone, FreeCAD headless,
   real-GUI, persistence, export and performance evidence.

## Simplification order

Prefer these moves, stopping when the requested benefit is achieved:

1. remove code, prose or configuration proven unreachable, unused or obsolete;
2. remove repetition by linking to or calling the one canonical owner;
3. collapse pass-through layers, one-use helpers or metadata with no distinct
   invariant or consumer;
4. reduce branching and state when the observable failure and transaction
   behaviour remain explicit;
5. narrow interfaces and dependency direction without changing public or
   persisted compatibility; and
6. improve names and local structure only where frozen identifiers and railway
   terminology permit it.

Apparent duplication may protect comparison oracles, FreeCAD lifecycle
behaviour, rollback, compatibility, provenance or performance. Prove that those
responsibilities are absent or transferred before removal.

## Workflow

1. **Discover read-only.** Trace the target through callers, tests, documents
   and runtime boundaries. Record the behaviour and load-bearing tokens that
   must survive.
2. **State the reduction.** Identify what will disappear or become simpler,
   why it has no separate responsibility and which canonical owner remains.
3. **Pilot narrowly.** Make the smallest representative edit. Do not combine
   mechanical movement, cleanup, behaviour change and performance work.
4. **Validate immediately.** Run the nearest proof after each slice. If it
   fails, preserve and classify the failure before editing retained source,
   tests or fixtures.
5. **Scale only from evidence.** Repeat the proved pattern where the same
   responsibility and dependency conditions hold; do not bulk-apply by text
   similarity alone.
6. **Review survival.** Verify callers, links, names, paths, commands,
   diagnostics, units, tolerances, ordering, transactions and recovery paths.
7. **Review the complete diff.** Confirm that complexity fell without moving it
   into a hidden helper, second implementation or larger instruction burden.

## Invalid simplifications

Do not:

- redesign a working railway path from intuition instead of a baseline;
- edit B14 or accepted B15 evidence to make newer code easier;
- weaken validation, tolerances, diagnostics, geometric fidelity or failure
  handling;
- rename frozen APIs, stored identifiers or compatibility fields without an
  accepted migration;
- replace an explicit transaction or recovery path with optimistic mutation;
- claim speed from fewer lines or deferred work without the performance SOP;
- delete historical, licensing, provenance or risk material as "noise"; or
- optimise for line count when a clearer result needs the same or more lines.

## Report

Report:

1. bounded target and preserved contract;
2. complexity removed and the surviving owner;
3. files and behaviour deliberately left unchanged;
4. before/after validation and any classified failures;
5. quantitative observations only where meaningful, without treating line
   count as the success criterion;
6. remaining GUI, persistence, export or performance evidence; and
7. the applicable sole Documentation Review or source/test quality verdict.
