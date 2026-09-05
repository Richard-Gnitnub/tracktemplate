---
name: tracktemplate-continue
description: Do one authorised TrackTemplate development cycle from repository evidence. The cycle integrates one previous Level 1 or Level 2 pull request. It delivers one authorised result as a draft with successful CI for its exact head, or stops on clean main. Only the project owner's literal `$tracktemplate-continue` command activates this skill. Natural-language equivalents do not activate it. This skill excludes Level 3 acceptance, release, tags, destructive history changes, and merge of the new draft.
---

# TrackTemplate continue

## Purpose

Use `$tracktemplate-continue` for one complete Level 1 or Level 2 cycle. Base
its direction on the Product Vision and repository evidence. Complete one
previous pull request with successful necessary checks for its exact head.
Synchronise protected `main`. Reconstruct the existing project context.

Then select one result:

- Deliver the most valuable authorised result as one new draft pull request
  with successful necessary CI for its exact head.
- If no worthwhile authorised result exists, stop successfully on clean
  protected `main`.

The project owner need not restate information that the repository owns. This
includes the phase, accepted results, architecture, constraints, existing
evidence, and routine technical details.

Only a project-owner command with the literal `$tracktemplate-continue`
invocation activates this skill. Acceptance, discussion, quotation, or
description of the workflow does not activate it. A natural-language
equivalent supplies no authority for this cycle.

An unfinished item alone is insufficient. The selected result must follow the
current authorised programme, exact active phase criterion, and repository
evidence. Otherwise, stop cleanly.

## Authority for one cycle

The literal invocation authorises at most these operations:

1. Verification and normal integration of one previous Level 1 or Level 2
   pull request.
2. Selection and implementation of one Level 1 or Level 2 result within
   current authority, from repository evidence.
3. Publication of one new draft pull request and monitoring of necessary CI
   for its exact head.

It supplies routine Git authority for the previous pull request. It delegates
publication of the new work to
[`$tracktemplate-publish`](../tracktemplate-publish/SKILL.md). It also permits
reversible engineering choices with a safe basis in accepted architecture and
repository authority.

The invocation does not authorise these items:

- Level 3 gates, phase acceptance, or release acceptance.
- Renderer acceptance or supported migration.
- Production-output or chair clearance.
- Licensing or provenance decisions.
- Tags or releases.
- Force push, history rewrite, or branch deletion.
- Protection bypass or destructive operations.
- Wider product scope.

For an unresolved product or user-experience choice, stop for the owner. Do
not ask the owner to give repository-owned information again.

[D-GOV-004](../../../reference/history/phase-closeouts/PHASE5_CLOSEOUT.md#repository-driven-continuation-authority-panel)
owns literal invocation, execution of one cycle, and Level 1/2 limits.
[D-GOV-005](../../../reference/current/PHASE_EVIDENCE.md#product-vision-and-execution-governance-panel)
owns selection from the Product Vision and reconciliation of results after
invocation. It does not invoke this skill or widen execution authority. It
does not authorise implementation of a Level 3 choice.

## Align the operator workspace

Before the first checkout, branch, or worktree mutation, use
[`$tracktemplate-ide-workspace-alignment`](../tracktemplate-ide-workspace-alignment/SKILL.md).
Compare PyCharm data with authoritative Git evidence. Include these items:

- Primary project, interpreter, VCS roots, and working directories in run
  configurations.
- Worktree, branch, HEAD, and pull-request evidence.

Report the complete arrangement before the change. Preserve dirty, unique,
unpushed, or active state. The IDE skill supplies no Git authority. Never
infer a branch from a run-configuration name or window name.

## Check and integrate the previous pull request

Before the first GitHub query or integration action, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage publication`

If the development-toolchain preflight does not pass, stop before publication
work.

1. Read enough of the current dashboard to identify the previous work's
   change level and authority boundary.
2. Examine the working tree, branch, HEAD/upstream, remote default branch,
   and associated pull request. For unrelated or ownership-ambiguous changes,
   stop.
3. Identify the previous pull request's exact head SHA, target, scope, review
   state, mergeability, and necessary checks.
4. Make sure that all integration conditions listed below apply.
5. If the pull request is a draft, mark it ready. Merge through the normal
   merge-commit route. Do not delete the branch. Check the merge commit.
   If a condition changes during the operation, stop.

All integration conditions are mandatory:

- The target is protected `main`.
- The scope contains only authorised Level 1 or Level 2 work.
- Every necessary check succeeded for the exact head.
- No requested change or conflict remains unresolved.
- Normal merge needs no protection bypass.
- The local working tree is clean.

If no previous pull request exists, do not merge. If it is already merged,
do not merge again. In every case, complete these steps:

1. Fetch remote state.
2. Switch to `main`.
3. Fast-forward `main` to the protected remote.
4. Make sure that local `main` is clean and exactly current.

Complete those steps before authority reconstruction or branch creation. If
synchronisation needs a merge, rebase, reset, or protection bypass, stop.
Never merge the new draft that this cycle makes.

After synchronisation, do the IDE comparison again. Make sure that the
intended primary project directory contains clean, exact protected `main`.
Put active work in named persistent worktrees. Keep `/tmp` worktrees only as accounted,
disposable state for review or integration.

If the physical PyCharm window is not observable, report that limitation.
Name the project-path and branch-indicator confirmations that the operator
must do. Do not claim visible UI evidence.

## Reconstruct repository authority

After `main` is current and before branch creation, use these sources to
reconstruct authority for the next work:

- Repository `AGENTS.md`.
- Canonical [`PRODUCT_VISION.md`](../../../reference/PRODUCT_VISION.md),
  including the current programme and the later programme's lack of current
  authority.
- [`PROJECT_PLAN.md`](../../../reference/PROJECT_PLAN.md).
- Current phase evidence, risk register, and decision register.
- Canonical owner of the affected subject.
- Latest related staff-review result.
- A bounded recent pull-request history, usually three to six completed
  work items.
- Actual source, callers, and tests as implementation evidence.

These items do not automatically authorise implementation:

- A `Next bounded tranche` heading or sentence.
- A review finding or branch name.
- A test expectation or the latest source structure.

## Select one result or stop

Put each credible candidate in exactly one category:

- `exit-closing`.
- `necessary-enabling`.
- `maintenance`.
- `governance-or-tooling`.

Name the exact exit gap, accepted requirement, live risk, or blocking dependency
that the candidate reduces. Prefer the smallest coherent result with the most
value for the owner or the next decision. Exclude optional maintenance. Do
not let a staff-review finding select itself as the next work item.

Trace each candidate through this sequence:

> Delegated agent task → bounded work item → evidenced finding or active exit →
> current authorised programme → Product Vision.

The Product Vision informs direction. It does not independently authorise
scope. Before delegation or branch creation, record these items:

- Product result and exact active phase criterion.
- Repository evidence for the gap.
- Authorised change level.
- Accepted behaviour that could regress.
- Smallest intervention and bounded files.
- Necessary validation and independent acceptance evidence.
- Explicit non-goals and claims that remain excluded.

Before a substantial repetition, identify at least one changed condition:

- New repository evidence.
- Changed testable hypothesis.
- Newly authorised scope or method.
- Corrected environment or fixture.
- Independently identified defect.
- Narrower task with different evidence.

Without a changed condition, stop the repetition. Report the repeated state
and blocker. Where applicable, give investigation or governance tasks to an agent. Do
not report activity as progress.

Under any condition below, use
[`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md):

- No clear result advances the phase.
- Two recent work items did not reduce a named exit gap.
- The proposed task is maintenance, governance, or tooling.
- Staff-review findings compete for priority.
- Evidence increased without making the next decision clearer.
- The previous review appears to have generated the current proposal.
- Another repeated cycle is suspected.

A clear routine change does not always need the chief of staff. Its brief is
transient analysis. Check it against repository authority.

If the selected Level 1 or Level 2 result is already authorised, another
owner restatement is unnecessary. Continue only when no unresolved product
choice remains. If the brief identifies an unresolved choice or Level 3
boundary, stop for owner input.

Successful integration followed by a clean stop is a valid result. Do not
make a branch or invent maintenance work only to continue the cycle.

## Make one bounded change

Before the first implementation mutation, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage development`

If the development-toolchain preflight does not pass, stop before
implementation. Only after selection of the result, make one fresh,
descriptive `agent/` branch. Do not begin a second result in this cycle.

If the selected result has any condition below, use
[`$tracktemplate-technical-lead`](../tracktemplate-technical-lead/SKILL.md):

- It crosses more than one technical layer.
- It needs several specialist skills.
- It affects FreeCAD behaviour that users can see.
- It materially affects transactions, persistence, selection, performance,
  or rollback.
- It needs a coordinated implementation procedure beyond one isolated fix.

For a trivial edit within one speciality, do not invoke technical lead. In
all cases, use every applicable specialist skill. Examine actual callers
and tests. Make the smallest coherent change across the affected layers.
Prefer existing regression infrastructure. Exclude optional simplification.

For each delegated task, record allowed files, change level, evidence,
non-goals, and phase criterion. After delivery, reconcile the agent's claim
with changed files and exact validation. Work claimed, present, validated,
and independently accepted are different states. The implementer cannot be
the sole acceptance authority.

## Validate and review

The quality reviews and repairs below apply to source and tests. Governance
documents follow the Technical Author Lead procedure. The one Documentation
Review, permitted adjustment, and final deterministic validation complete that
procedure. CI can check final bytes. It cannot start another review,
correction, reinterpretation, or wording pass.

1. Use
   [`$tracktemplate-change-validation`](../tracktemplate-change-validation/SKILL.md).
   Preserve each selected failure. Classify each failure. Do proportionate
   final validation. Follow the canonical
   [validation-document boundary](../../../reference/VALIDATION.md#document-boundary).
   Only if its durable validation contract changes, include
   `reference/VALIDATION.md` in the work. For affected document or ViewProvider
   behaviour, include regression and lifecycle evidence.
2. Give the completed change and raw evidence to a different read-only
   [`$tracktemplate-quality-review`](../tracktemplate-quality-review/SKILL.md).
   Where the client supports it, use a fresh reviewer, sub-agent, or session.
   Otherwise, disclose the lack of independence.
3. Give every actionable finding one disposition: `BLOCKER`,
   `REQUIRED_BEFORE_EXIT`, `BACKLOG`, or `OPTIONAL`.
4. Return only `BLOCKER` findings for technical repair. Do not repair the
   other dispositions in this cycle. If another finding prevents safe
   publication, stop. Report it without a new disposition or wider scope.
5. Use at most two total source/test repair-and-review passes for this
   result. Include any later CI blocker for the exact head in that count.
   After each repair, do the original proof again. Do affected final
   validation again. Before publication, get another different read-only staff
   review of the complete repaired source.

Under any condition below, stop without another work item:

- The same proof fails after two bounded repair passes.
- The technical premise appears incorrect.
- Local repair no longer reduces the original uncertainty.
- Scope exceeds the selected result.
- A product choice remains unresolved.
- The work reaches Level 3 authority.
- Necessary infrastructure is unavailable.
- Review identifies unresolved architectural disagreement.

Do not weaken validation to get a successful result. Do not change an
accepted oracle for that purpose. Do not start another result for that purpose.

Before publication, reconcile the evidence with the exact active exit. Do not
turn partial implementation or a successful test into exit acceptance.
Preserve the explicit limits on product, programme, phase, output, and
migration claims.

## Publish one draft

After final validation and a staff review without blockers, record the exact
reviewed paths and content state. Delegate publication to
`$tracktemplate-publish` with authority limited to that frozen state. The
delegation includes these operations:

- One intentional commit set.
- Push of one branch.
- Creation of one draft pull request.
- Monitoring of necessary CI for the exact pushed head.

The delegated publication workflow cannot edit source or repair CI failures.

If necessary CI fails for the exact head, preserve the failure. Classify it.
Return it to this workflow without source changes. It is a publication
`BLOCKER` only when classification supports safe repair within the selected
result.

Such a repair consumes one of the same two total passes. Before publication
continues, do affected final validation again. Get another different read-only
staff review. If no pass remains, stop. If the cause is environmental or
external, stop. If repair exceeds scope, stop.

For a governance-document CI failure, preserve the evidence. Then stop for
the owner. Do not edit its prose or start another improvement pass. Do not
invoke Documentation Review or quality review for that failure.

Stop with the draft after necessary CI passes for its exact head. Do not mark
it ready or merge it during this invocation.

For new or materially changed canonical technical prose, use
[`$tracktemplate-technical-author-lead`](../tracktemplate-technical-author-lead/SKILL.md).
After freeze, the Technical Author Lead sends the frozen scope to one
Documentation Review. Do not read the external PDF during a usual
continuation cycle.

## Owner acceptance pack

After a successful implementation cycle, apply the canonical
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
Use these owner-view fields:

1. **Current state**.
2. **What changed**.
3. **What now works**.
4. **Limitations/findings**.
5. **Owner decision**.
6. **Next action**.

The owner view presents canonical records. Put this technical provenance below
it:

- Exact active criterion and formal status.
- Inspection route and visual evidence.
- Behaviour that did not change.
- Contribution to the phase exit or risk.
- Validation and staff-review results.
- Draft pull request.
- Decision that the owner must make.

Distinguish agent claims, repository content, validated evidence, and
independent acceptance. Name the exact active criterion. Report whether its
formal status changed.

For GUI work, include representative screenshots where available. Pixel
counts, hashes, and raw logs can supply proof. They do not replace a visual
demonstration that a person can understand.

Stop for owner input only under these conditions:

- The project owner must make a product or user-experience choice.
- Level 3 authority is due.
- The task needs formal phase, renderer, migration, output, or release
  acceptance.
- The owner must accept a change to product behaviour that users can see.
- You cannot remove a blocker safely.

## Recovery

Before the cycle starts again, examine external and local state. Continue from the first
incomplete operation. Do not duplicate a merge, branch, commit, or pull request.

Report these results:

- Previous integration and merge commit.
- Selected classification and named contribution.
- Local validation and remote validation for the exact head.
- Review verdict and new draft.
- Reconciliation with the exact phase exit.
- Preserved limits on claims.
- Each authority boundary that remains open.

If the cycle stops after integration, report that it made no new work item.
