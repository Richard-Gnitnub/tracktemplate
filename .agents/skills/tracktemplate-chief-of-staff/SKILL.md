---
name: tracktemplate-chief-of-staff
description: Diagnose TrackTemplate progress and recommend one highest-value next outcome. Use when the project owner says work appears stuck, circular, maintenance-heavy or evidence-heavy, several staff-review findings compete, the next task does not clearly advance an exit, the owner asks what outcome best advances the current phase, or `$tracktemplate-continue` detects its defined loop conditions. This skill is read-only and advisory; do not use it for a routine clear change or as project-acceptance authority.
---

# TrackTemplate chief of staff

## Purpose

Own read-only project-progress diagnosis and prioritisation. Determine whether
recent work is reducing a named phase-exit gap or live risk, then produce one
transient `Next-outcome brief` for use by the project owner or by an authorised
`$tracktemplate-continue` cycle.

The skill may activate from an explicit `$tracktemplate-chief-of-staff`
invocation, an equivalent direct owner request, or composition by
[`$tracktemplate-continue`](../tracktemplate-continue/SKILL.md) after that
workflow detects a loop condition. Do not add a chief-of-staff ceremony to a
routine task whose phase contribution and technical route are already clear.

## Read-only authority boundary

Do not edit repository files, create or change branches, commit, merge, publish,
or update a plan, evidence record, risk or decision register. Do not accept a
phase, renderer, migration, output or release decision. Do not invent work to
keep a cycle active or promote every staff-review finding into immediate work.

Treat this skill's output as transient advice, not a new plan, status system or
repository authority. Source, tests, pull requests, commits and review findings
are implementation evidence, not requirement authority. This skill does not
replace architecture review, validation, quality review or specialist
engineering.

## Reconstruct current progress

1. Read the current phase and formal binary exit-condition status from
   [`PROJECT_PLAN.md`](../../../reference/PROJECT_PLAN.md).
2. Read the detailed current phase evidence and the current risk and decision
   registers beside it.
3. Inspect the latest relevant staff-level quality-review result. If no retained
   result exists, state that limitation instead of inferring a verdict.
4. Inspect a bounded recent history, normally the last three to six merged pull
   requests or equivalent completed tranches. Extend the window only when it is
   necessary to locate the unchanged gap, and say why.
5. Reconcile each claim against the canonical document that owns the affected
   subject. A `Next bounded tranche` sentence, branch name, test expectation or
   review suggestion is not accepted next-outcome authority.

## Classify recent tranches

Classify each relevant completed tranche as exactly one of:

- `exit-closing` — directly reduces a named current exit gap or supplies the
  missing decision-relevant proof;
- `necessary-enabling` — removes a demonstrated blocker that must be cleared
  before an exit-closing result can be delivered;
- `maintenance` — preserves or improves implementation, tests or harnesses but
  does not itself reduce a named current exit gap; or
- `governance-or-tooling` — changes development controls, guidance or general
  automation without implementing the current phase outcome.

For each tranche, name the exact exit gap, requirement or risk reduced. Record
`none` when it reduced none; do not manufacture a contribution.

## Diagnose loops and decision readiness

Check explicitly for:

- two or more consecutive maintenance or governance/tooling tranches;
- repeated evidence work leaving the same named uncertainty unchanged;
- a staff-review finding automatically becoming the next tranche;
- Level 1 work represented as Level 2 phase progress;
- evidence growth without a corresponding decision-readiness gain; and
- optional cleanup displacing owner-visible or product-facing work.

Distinguish formal exit acceptance from partial engineering evidence without
creating another canonical status system. You may describe evidence as
`investigating`, `demonstrated` or `decision-ready`, but those descriptions do
not change the formal status or confer acceptance.

Identify evidence already sufficient and not to be repeated. Prefer the
smallest remaining implementation or proof gap that materially advances a
named exit or risk. Defer non-blocking maintenance findings. If authority
supports no worthwhile phase-moving work, recommend a clean stop rather than a
maintenance substitute.

## Next-outcome brief

Report the formal status, a concise recent-tranche classification and every loop
indicator found. Then produce exactly one section titled `Next-outcome brief`;
do not offer a menu of outcomes.

The brief must contain:

- **Current phase and formal exit status**
- **Highest-value remaining outcome**
- **Named exit gap or risk advanced**
- **Evidence already sufficient and not to be repeated**
- **Smallest remaining implementation or proof gap**
- **Why this outranks maintenance alternatives**
- **Expected task level**
- **Recommended specialist skills**
- **Explicit exclusions**
- **Definition of done**
- **Fail-closed stop conditions**
- **Genuine owner decision required, if any**
- **Maintenance findings deferred outside this cycle**

When no worthwhile authorised outcome exists, make this one brief a stop brief
that names the missing decision or evidence. End by stating that the brief is
transient advice and does not change repository authority or formal status.
