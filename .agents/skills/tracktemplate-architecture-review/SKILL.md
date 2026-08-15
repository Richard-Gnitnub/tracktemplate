---
name: tracktemplate-architecture-review
description: Review proposed TrackTemplate architecture and dependency-direction decisions before implementation. Use for a new subsystem, composition change, cross-layer responsibility, canonical-state decision, migration strategy or material departure from the accepted architecture or modularisation plan.
---

# TrackTemplate architecture review

## Outcome

Produce a bounded, evidence-backed architecture recommendation before source
mutation. Preserve accepted railway, recovery, compatibility and production
boundaries, and place any accepted durable decision in its existing canonical
owner.

## Responsibility boundary

- Use this skill for system structure, responsibility, dependency direction and
  staged migration choices.
- Use `$tracktemplate-api-design` for the detailed public, persistence, command,
  exporter or integration contract.
- Use `$tracktemplate-freecad-addon-research` when the choice depends on current
  FreeCAD Addon guidance.
- Use `$tracktemplate-performance-engineering` when performance evidence drives
  the choice.
- Use `$tracktemplate-documentation-review` when an accepted decision changes
  canonical Markdown.

This skill recommends; it does not accept an architecture change, alter phase
scope or create a parallel ADR catalogue.

## Preparation

1. Read `reference/PROJECT_PLAN.md` for current phase/exit status, then read
   the applicable current decision record for authorised scope.
2. Read `reference/ARCHITECTURE.md` and
   `reference/MODULARISATION_PLAN.md`.
3. Read the canonical owner of each affected persistence, display, validation,
   export, licensing, terminology or recovery boundary.
4. Inspect the implementation, callers, tests and evidence that constrain the
   choice. Treat them as evidence rather than requirement authority.

For exporter interruption or recovery, read the canonical
[supported exporter failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model).
Treat widening or narrowing that model as an architecture and Level 3
project-owner decision. Compare process-local cleanup, restart containment and
an isolated helper-process boundary before recommending any change.

## Review workflow

1. **Frame the decision.** State the exact problem, decision owner, affected
   layers, current behaviour and the latest point at which a decision is
   required.
2. **Name invariants.** Preserve railway results, units, frames, topology,
   stable identities, transactions, persistence compatibility, derived-view
   status, diagnostics and production integrity where applicable.
3. **Compare real options.** Include the status quo and the smallest reversible
   option. For each option record responsibilities, dependencies, state
   ownership, compatibility, failure recovery, evidence needs and retirement
   obligations.
4. **Challenge duplication.** Identify the one authoritative implementation
   and give every necessary temporary duplicate an owner and objective
   retirement condition.
5. **Check sequencing.** Prefer an independently verifiable vertical slice.
   Separate mechanical extraction, behavioural change, cleanup and performance
   work.
6. **Recommend narrowly.** State why the preferred option satisfies the current
   requirements with less irreversible commitment than the alternatives. Mark any
   requirement, evidence or owner decision still missing.
7. **Route the record.** Put an accepted strategic decision in
   `reference/ARCHITECTURE.md`, an accepted source-boundary decision in
   `reference/MODULARISATION_PLAN.md`, phase/exit status in
   `reference/PROJECT_PLAN.md`, current decisions in the structured register
   and tranche evidence only in `reference/current/PHASE_EVIDENCE.md`.

## Invalid shortcuts

Do not:

- redesign from source shape or intuition without runtime and evidence context;
- treat a diagram, prototype, benchmark or diff as acceptance;
- introduce a second phase plan, architecture ledger or generic ADR directory;
- make an optional network or service boundary mandatory without authority;
- make derived geometry, caches or viewport state authoritative; or
- remove a legacy path before parity evidence and project-owner acceptance.

## Report

Report the decision boundary, preserved invariants, options compared,
recommendation, rejected trade-offs, required migration decisions and
retirement conditions, evidence needed before implementation, and the
canonical owner for any accepted record.
