---
name: tracktemplate-continue
description: Finish one previous green TrackTemplate Level 1 or Level 2 pull request, synchronise protected main, carry out the next bounded tranche and publish one new green draft pull request. Use only when the project owner explicitly invokes `$tracktemplate-continue`; the invocation authorises this one-cycle merge-and-development loop but never Level 3 authority, release, tagging, destructive history changes or automatic merging of the newly published draft.
---

# TrackTemplate continue

## Outcome

Turn a completed green pull request into a clean-main starting point, then
implement and publish one next bounded tranche without asking the project owner
to manage routine Git mechanics.

## One-cycle authority

Explicit `$tracktemplate-continue` invocation authorises one cycle containing
at most:

1. one previous Level 1 or Level 2 pull-request integration;
2. one next bounded implementation tranche; and
3. one new draft pull request with exact-head CI monitoring.

It supplies ready-for-review and normal merge authority only for the previous
pull request after every condition below passes. It delegates the new tranche's
publication stage to
[`$tracktemplate-publish`](../tracktemplate-publish/SKILL.md) without requiring
a second invocation.

The invocation does not authorise a Level 3 gate, phase or release acceptance,
renderer acceptance, supported migration, production-output clearance,
licensing/provenance authority, tagging, release, force push, history rewrite,
branch deletion, protection bypass, destructive operation or wider product
scope.

## Preparation

1. Read the current phase, next bounded tranche and exclusions in
   [`PROJECT_PLAN.md`](../../../reference/PROJECT_PLAN.md) and
   [`PHASE_EVIDENCE.md`](../../../reference/current/PHASE_EVIDENCE.md).
2. Inspect the working tree, current HEAD/upstream, remote default branch and
   any pull request associated with the current branch.
3. Resolve the previous pull request's exact head SHA, changed scope, review
   state, mergeability and required checks.
4. Stop for unrelated or ownership-ambiguous working-tree changes.

## Integrate the previous pull request

Skip this stage idempotently when there is no previous pull request or it is
already merged.

Otherwise require all of the following before external mutation:

- the pull request targets the protected default branch;
- its exact head contains only the already authorised Level 1 or Level 2 scope;
- every required check completed successfully for that exact head;
- no unresolved requested change, blocking review or merge conflict remains;
- the pull request is mergeable without bypassing branch protection; and
- the local working tree is clean.

If the pull request is a draft, mark it ready. Merge through the repository's
normal merge-commit route without deleting the branch. Verify the merged state
and merge commit, then fetch, switch to the default branch and fast-forward it
to the protected remote. Stop if any condition changes during the operation.

## Carry out the next tranche

1. Resolve one explicit next bounded tranche from current authority. Stop when
   it is ambiguous, absent or reaches Level 3.
2. Create a fresh descriptive `agent/` branch from clean, current protected
   main.
3. Use the applicable specialist skills and implement the smallest coherent
   change.
4. Run proportionate validation and a complete diff review. Classify every
   failed proof before a retained repair. Follow the canonical
   [validation-document boundary](../../../reference/VALIDATION.md#document-boundary).
   Do not include `reference/VALIDATION.md` in a routine tranche unless its
   durable validation contract changed.
5. Apply the
   [`$tracktemplate-publish`](../tracktemplate-publish/SKILL.md) workflow to
   commit, push, open one draft pull request and monitor exact-head CI.
6. Stop with that new green draft. Do not mark or merge it during the same
   invocation.

## Fail-closed stops

Stop and report the exact blocker when:

- CI is pending, failed, missing or belongs to another commit;
- the previous pull request has scope drift, unresolved review or a conflict;
- protected main moved in a way that prevents a clean fast-forward;
- the next task changes authority or requires a project-owner choice;
- a repair would weaken validation, change an accepted oracle or exceed scope;
  or
- an external service, credential or required runtime is unavailable.

Never use force push, destructive reset/restore, `git clean`, branch deletion
or a protection bypass to complete the cycle.

## Recovery and report

On rerun, inspect external and local state first and resume from the first
incomplete stage. Do not duplicate a merge, branch, commit or pull request.

Report the integrated pull request and merge commit, new branch and commits,
new draft pull request, exact remote CI result, local validation, any
classified repair, remaining GUI work and every authority boundary left open.
