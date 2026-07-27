---
name: tracktemplate-explain-change
description: Explain a TrackTemplate working-tree diff, commit range, pull request, patch, validated tranche or review packet in concept order, with explicit evidence limits and an optional safe interactive visual. Use for maintainer handoffs, guided walkthroughs, architectural change explanations or requests to visualise state, ordering, migration, geometry or data flow.
---

# TrackTemplate change explanation

## Outcome

Transfer enough understanding for a maintainer to reason about the change,
its invariants, trade-offs, failure modes and evidence without reading the diff
in arbitrary file order.

## Responsibility boundary

This skill explains; it does not validate, review or accept a change.

- Use `$tracktemplate-change-validation` for evidence selection and
  interpretation.
- Use `$tracktemplate-quality-review` for staff-level scope and implementation
  judgement.
- Use `$tracktemplate-documentation-alignment` when the explanation exposes a
  durable documentation conflict.
- Keep manual explanation read-only. Do not turn a walkthrough into authority
  to edit, commit, publish or change live phase status.

## Establish the evidence

1. Resolve the requested working tree, commit/range, PR, patch or evidence
   packet and preserve unrelated dirty paths.
2. Read the user request, relevant canonical requirement, complete bounded diff
   and available raw validation/review results.
3. Identify what was not checked and whether evidence is current for the exact
   source state.
4. Label the explanation **Unverified change** when evidence is absent, stale
   or narrower than the behavioural claims. Separate code facts, intended
   behaviour and verified outcomes.
5. Treat commits, PR text and diffs as implementation evidence rather than
   requirement authority.

## Teach the change

Present only the background needed for this change:

1. **Purpose:** the operator or maintainer problem and the accepted boundary.
2. **Before and after:** the observable flow, state or responsibility that
   changed.
3. **Conceptual walkthrough:** group files and hunks by concept and dependency
   direction, not pathname or diff order.
4. **Concrete example:** use a small TrackTemplate example or sanitised
   fictional data with explicit units, identities and state where relevant.
5. **Invariants:** name what must remain unchanged, including railway results,
   ordering, persistence, transactions, rollback or output classification.
6. **Decisions and trade-offs:** explain rejected alternatives only when the
   evidence records them; do not invent rationale from code shape.
7. **Failure modes:** show invalid, stale, partial or rollback paths that help a
   maintainer reason about safety.
8. **Evidence:** connect each important claim to a test, runtime boundary or
   exact source location and state what remains unproved.

Use clickable local file links with line numbers in chat. Prefer a small table,
flow or timeline only when it materially clarifies multiple relationships.

## Optional dialogue

When the user requests an interactive walkthrough, ask one applied
free-response question at a time. Reteach a misunderstood concept from the
evidence without scoring the user or recording raw answers. A conscious skip is
not evidence of understanding and does not change review or acceptance state.

When an answer conflicts with the explanation, show both implications, label
the diagnosis as a hypothesis and re-open the relevant requirement,
implementation or evidence boundary before deciding which is wrong.

## Optional visual

Read [`references/visual-mode.md`](references/visual-mode.md) when the user asks
for a visual or when dynamic state, ordering, migration, geometry,
transformation or concurrency is materially harder to understand in static
prose. The visual complements the explanation and never proves production
behaviour.

## Report

Report:

1. scope and evidence status;
2. purpose and conceptual before/after;
3. guided change grouped by responsibility;
4. preserved invariants, decisions, failure modes and trade-offs;
5. checks supporting each behavioural claim;
6. unverified behaviour, conscious skips or unresolved questions; and
7. any temporary visual path and its declared simplifications.
