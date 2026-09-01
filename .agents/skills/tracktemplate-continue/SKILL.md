---
name: tracktemplate-continue
description: Run one complete repository-driven TrackTemplate development cycle that integrates one previous exact-green Level 1 or Level 2 pull request, synchronises protected main, reconstructs authority, selects and delivers one highest-value authorised outcome or stops cleanly, validates and reviews it, then publishes one exact-green draft pull request. Use only when the project owner explicitly invokes the literal `$tracktemplate-continue` command; natural-language equivalents do not activate it. Never use it for Level 3 acceptance, release, tagging, destructive history changes or automatic merging of the newly published draft.
---

# TrackTemplate continue

## Outcome

Make `$tracktemplate-continue` the normal vision-led, repository-driven command
for one complete Level 1 or Level 2 cycle. Finish one previous exact-green pull
request, synchronise protected `main`, reconstruct existing project context and
either:

- deliver the single highest-value worthwhile authorised outcome as one new
  exact-green draft pull request; or
- stop successfully on clean protected `main` when no such outcome exists.

The project owner does not need to restate the current phase, accepted outcomes,
architecture, constraints, evidence already present or routine technical
details owned by the repository.

Only a project-owner command containing the literal `$tracktemplate-continue`
invocation activates this skill. Accepting, discussing, quoting or describing
the workflow does not activate it, and no natural-language equivalent supplies
its one-cycle authority.

It does not mean “find something unfinished and continue coding.” The selected
outcome must be grounded in the current authorised programme, exact active
phase criterion and repository evidence; otherwise stop cleanly.

## One-cycle authority

That literal invocation authorises at most:

1. verification and normal integration of one previous Level 1 or Level 2 pull
   request;
2. repository-driven selection and implementation of one Level 1 or Level 2
   outcome already inside current authority; and
3. publication and exact-head CI monitoring of one new draft pull request.

It supplies routine Git authority for the previous pull request and delegates
new-tranche publication to
[`$tracktemplate-publish`](../tracktemplate-publish/SKILL.md). It also permits
reversible engineering judgement where accepted architecture and repository
authority settle the choice safely.

It does not authorise a Level 3 gate, phase or release acceptance, renderer
acceptance, supported migration, production-output or chair clearance,
licensing/provenance authority, tagging, release, force push, history rewrite,
branch deletion, protection bypass, destructive operation or wider product
scope. Stop for a genuine product or user-experience choice; do not ask the
owner to repeat information already owned by the repository.

[D-GOV-004](../../../reference/history/phase-closeouts/PHASE5_CLOSEOUT.md#repository-driven-continuation-authority-panel)
continues to own literal invocation, one-cycle execution and Level 1/2 limits.
[D-GOV-005](../../../reference/current/PHASE_EVIDENCE.md#product-vision-and-execution-governance-panel)
governs vision-led selection and result reconciliation after invocation. It
does not invoke this skill, widen execution authority or turn a Level 3 choice
into an implementable task.

## Align the operator-facing workspace

Before the first checkout, branch or worktree mutation, compose
[`$tracktemplate-ide-workspace-alignment`](../tracktemplate-ide-workspace-alignment/SKILL.md)
to compare the primary PyCharm project, interpreter, VCS roots and run working
directories with Git-authoritative worktree, branch, HEAD and pull-request
evidence. Report the complete pre-change arrangement and preserve any dirty,
unique, unpushed or active state. The IDE skill supplies no Git authority and
must never infer a branch from a run-configuration or window name.

## Verify and integrate the previous pull request

1. Read the current dashboard sufficiently to identify the previous tranche's
   task level and authority boundary.
2. Inspect the working tree, branch, HEAD/upstream, remote default branch and
   associated pull request. Stop for unrelated or ownership-ambiguous changes.
3. Resolve the previous pull request's exact head SHA, target, changed scope,
   review state, mergeability and required checks.
4. Require that it targets protected `main`, contains only authorised Level 1
   or Level 2 scope, has every required check successful for that exact head,
   has no unresolved requested change or conflict, and is mergeable without a
   protection bypass while the local working tree is clean.
5. If it is a draft, mark it ready. Merge through the normal merge-commit route
   without deleting the branch. Verify the merge commit. Stop if any condition
   changes during the operation.

Skip only the merge idempotently when no previous pull request exists or it is
already merged. In every path, fetch, switch to `main`, fast-forward it to the
protected remote and verify that local `main` is clean and exactly current
before reconstructing authority or creating a branch. Stop if synchronisation
cannot complete without a merge, rebase, reset or protection bypass. Never
merge the new draft created later in this cycle.

Repeat the IDE comparison after synchronisation. Require the intended primary
project directory to back clean exact protected `main`; map active work to
named persistent worktrees; and retain `/tmp` worktrees only as accounted,
disposable review or integration state. When the physical PyCharm window is
not observable, name the project-path and branch-indicator confirmation the
operator must perform rather than claiming visible UI evidence.

## Reconstruct repository authority

After protected `main` is current and before creating a branch, reconstruct the
next-outcome boundary from:

- repository `AGENTS.md`;
- the canonical
  [`PRODUCT_VISION.md`](../../../reference/PRODUCT_VISION.md), including the
  current programme and later-horizon non-authority;
- [`PROJECT_PLAN.md`](../../../reference/PROJECT_PLAN.md);
- current phase evidence and the current risk and decision registers;
- the canonical owner of the affected subject;
- the latest relevant staff-review result;
- a bounded recent pull-request history, normally three to six completed
  tranches; and
- actual source, callers and tests as implementation evidence.

Do not treat a `Next bounded tranche` heading or sentence, review finding,
branch name, test expectation or latest source shape as automatic
implementation authority.

## Select one outcome or stop

For each credible candidate, classify it as exactly one of:

- `exit-closing`;
- `necessary-enabling`;
- `maintenance`; or
- `governance-or-tooling`.

Name the exact current exit gap, accepted requirement, live risk or blocking
dependency it reduces. Prefer the smallest coherent outcome with the greatest
decision-readiness or owner-visible value. Exclude optional maintenance and do
not let a staff-review finding nominate itself as the next tranche.

Trace every candidate as delegated agent task → bounded work item → evidenced
finding or active exit → current authorised programme → Product Vision. Vision
informs direction but never independently authorises scope. Before delegation
or branch creation, record:

- the product outcome and exact active phase criterion;
- the repository evidence proving the gap;
- the authorised change level;
- accepted behaviour that could regress;
- the smallest intervention and bounded files;
- required validation and independent acceptance evidence; and
- explicit non-goals and preserved non-claims.

Before substantially repeating an action, identify new repository evidence, a
changed testable hypothesis, newly authorised scope or method, a corrected
environment or fixture, an independently identified defect, or a narrower task
with different evidence. With none of these, do not continue the loop: report
the repeated state and blocker, assign investigation or governance where
appropriate, and do not represent activity as progress.

Compose
[`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md)
when:

- no clear phase-moving outcome exists;
- two recent tranches have not reduced a named exit gap;
- the proposed task is maintenance or governance/tooling;
- staff-review findings compete for priority;
- evidence has grown without improving decision readiness;
- the current proposal appears to have been generated by the previous review;
  or
- another loop is suspected.

The chief of staff is not required for every clear routine change. Its brief is
transient analysis, so recheck it against repository authority. Within this
explicit continuation cycle, proceed without a separate owner restatement when
the selected Level 1 or Level 2 outcome is already authorised and no genuine
product choice remains. Stop for owner input when the brief exposes an
unresolved choice or Level 3 boundary.

It is a successful result to integrate the previous green pull request,
synchronise protected `main`, determine that no worthwhile authorised
phase-moving task exists and stop. Do not create a branch or manufacture a
maintenance tranche merely to keep the cycle active.

## Shape and implement one vertical slice

Create one fresh descriptive `agent/` branch only after selecting the outcome.
Do not begin a second outcome in the same cycle.

Compose
[`$tracktemplate-technical-lead`](../tracktemplate-technical-lead/SKILL.md)
when the selected outcome:

- crosses more than one technical layer;
- coordinates several specialist skills;
- affects user-visible FreeCAD behaviour;
- has material transaction, persistence, selection, performance or rollback
  implications; or
- needs a technical implementation route rather than one isolated fix.

Do not invoke technical lead for trivial single-specialist edits. Whether or not
it is needed, use every applicable specialist skill, inspect actual callers and
tests, implement the smallest coherent vertical slice, prefer existing
regression infrastructure and keep optional cleanup outside the tranche.

When the cycle changes material technical documentation, route its technical
meaning from the subject owner or Technical Lead to
[`$tracktemplate-technical-author-lead`](../tracktemplate-technical-author-lead/SKILL.md).
That lead authors and delivers one complete candidate before freeze.

The delegated objective must state allowed files and task level, evidence,
non-goals and phase criterion. After delivery, reconcile the agent's claim with
actual changed files and exact validation. Work claimed, present, validated and
independently accepted are distinct, and the implementer is never sole
acceptance authority.

## Validate and review

1. Invoke
   [`$tracktemplate-change-validation`](../tracktemplate-change-validation/SKILL.md),
   preserve and classify every selected failure, and run the proportionate
   final proof. Follow the canonical
   [validation-document boundary](../../../reference/VALIDATION.md#document-boundary);
   do not include `reference/VALIDATION.md` in a routine tranche unless its
   durable validation contract changed. Include the relevant regression and
   document/ViewProvider lifecycle evidence when the selected behaviour crosses
   those boundaries.
2. Give the completed change and raw evidence to a separate read-only
   [`$tracktemplate-quality-review`](../tracktemplate-quality-review/SKILL.md).
   Prefer a fresh reviewer, sub-agent or session when the active client
   supports it; otherwise disclose that the review is not independent.
3. Require every actionable finding to be dispositioned as `BLOCKER`,
   `REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL`.
4. Return only `BLOCKER` findings to technical delivery. Do not repair
   `REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL` findings in this cycle. If a
   non-blocker means the selected outcome cannot be published safely, stop and
   report it instead of reclassifying it or expanding the tranche.
5. Permit no more than two total repair-and-review passes for the same outcome,
   including any later exact-head CI blocker. After each repair, rerun the
   original proof and affected final validation, then obtain another separate
   read-only staff review of the complete repaired source before publication.

Stop without creating another tranche when:

- the same proof still fails after two bounded repair passes;
- the technical premise appears wrong;
- local repair no longer reduces the original uncertainty;
- scope expands beyond the selected outcome;
- a genuine product choice remains unresolved;
- Level 3 authority is reached;
- required infrastructure is unavailable; or
- review exposes unresolved architecture disagreement.

Do not weaken validation, change an accepted oracle or start another outcome to
obtain a green result.

Before publication, reconcile the evidence against the exact active exit. Do
not convert partial implementation or a green test into exit acceptance, and
preserve every explicit product, programme, phase, output and migration
non-claim.

## Publish one draft

When final validation is complete and staff review has no blocker, record the
exact reviewed path set and content state. Delegate to `$tracktemplate-publish`
in review-frozen mode to create one intentional commit set, push one branch,
open one draft pull request and monitor required CI for the exact pushed head.
The delegated publication stage may not edit source or apply its own CI repair.

If required exact-head CI fails, preserve and classify the failure and return
it to this workflow without changing the reviewed source. Treat it as a
publication `BLOCKER` only when the classification establishes a safe repair
inside the selected outcome. Such a repair consumes one of the same two total
passes above and must repeat the affected final validation and another separate
read-only staff review before publication resumes. Stop when no pass remains,
the failure is environmental or external, or the repair would exceed scope.

Stop with that exact-green draft. Do not mark it ready or merge it during this
invocation.

When a cycle includes material technical documentation, use the Technical
Author Lead before candidate freeze. After freeze, route the complete scope to
one independent
[`$tracktemplate-documentation-review`](../tracktemplate-documentation-review/SKILL.md).
Do not read the external PDF during a usual continuation cycle.

## Owner acceptance pack

At the end of a successful implementation cycle, apply the canonical
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
to the result. Use these fields:

1. **Current state**
2. **What changed**
3. **What now works**
4. **Limitations/findings**
5. **Owner decision**
6. **Next action**

The owner view is a presentation from canonical records. Put this technical
provenance below it:

- The exact active criterion and formal status
- The inspection route and visual evidence
- The behavior that did not change
- The phase-exit or risk contribution
- The validation and staff-review results
- The draft pull request
- The decision that the owner must make

Record separately what the agent claimed, what the repository contains, what
the evidence validates, and what an authority accepted independently. Name the
exact active criterion. Say whether its formal status changed.

For GUI work, include representative screenshots when available. Pixel counts,
hashes, and raw logs can be part of the proof. They do not replace a
human-readable visual demonstration.

Stop for owner input only when one of these conditions occurs:

- The project owner must make a product or user-experience choice.
- Level 3 authority is due.
- The task requires formal phase, renderer, migration, output, or release
  acceptance.
- The owner must accept a change to Product behavior that users can see.
- You cannot remove a blocker safely.

## Recovery

On rerun, inspect external and local state first and resume from the first
incomplete stage. Do not duplicate a merge, branch, commit or pull request.
Report the previous integration and merge commit, the selected classification
and named contribution, local and exact-head remote validation, review verdict,
new draft, exact phase-exit reconciliation, preserved non-claims and every
authority boundary left open. When stopping after integration, say explicitly
that no new tranche was manufactured.
