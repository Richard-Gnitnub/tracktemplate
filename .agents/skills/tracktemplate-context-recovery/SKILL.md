---
name: tracktemplate-context-recovery
description: Recover authoritative TrackTemplate task context after a new session, compaction, interrupted handoff or unfamiliar dirty worktree. Use before continuing prior work when requirements, decisions, current phase, ownership or validation state might otherwise be inferred from commits or diffs.
---

# TrackTemplate context recovery

## Outcome

Reconstruct the task from repository authority before acting. A commit, diff,
test or implementation comment may show what changed; it does not establish why
the change is required or whether the project owner accepted it.

## Recovery order

1. Read the root and applicable scoped `AGENTS.md` files.
2. Read `reference/PROJECT_PLAN.md` for the current phase, open gates, accepted
   scope and named open-phase evidence record.
3. Identify the subject of the request and read its owning canonical document
   from the ownership map in `AGENTS.md`.
4. Read the open-phase evidence record only where it contains evidence or an
   accepted decision relevant to the task.
5. Inspect the working tree, relevant source, tests, commits and diffs to recover
   implementation state. Preserve unrelated or unattributed changes.
6. Reconcile the recovered implementation state with the controlling
   documents. If they conflict, follow the explicit current user decision,
   `AGENTS.md` and canonical owner in that order; report the conflict.
7. Continue only after the intended result, authority boundary, next safe slice
   and proof boundary are clear. Ask the user when a material decision cannot be
   recovered without guessing.

## Durable-context rule

Record an accepted durable fact in its single canonical owner:

- project-wide phase, gate, risk or acceptance state in
  `reference/PROJECT_PLAN.md`;
- current-phase evidence in the one open-phase evidence record;
- architecture, policy or procedure in its named canonical document;
- repeatable agent method in a skill; and
- an evidenced historical lesson in
  `reference/LEARNING_FROM_EXPERIENCE.md`.

Do not create a second task plan, chronicle or summary that competes with those
owners. Conversation text, branch names, commit messages and diffs remain
supporting context rather than project authority.

## Recovery report

Before mutation, state concisely:

1. the controlling files read;
2. the recovered accepted result and authority boundary;
3. the current implementation and validation state;
4. contradictions, uncommitted work or missing evidence; and
5. the next bounded action and check.

Do not describe incomplete work, an unaccepted diff or an unrun check as
accepted project state.
