---
name: tracktemplate-publish
description: Publish a bounded, reviewed TrackTemplate working-tree change by validating it, creating an agent branch, making intentional commits, pushing, opening a draft pull request and monitoring required GitHub CI. Use when the project owner explicitly invokes `$tracktemplate-publish` or when an explicit `$tracktemplate-continue` invocation delegates its new-tranche publication stage; this workflow never authorises merge, tag, release, destructive history changes or wider scope.
---

# TrackTemplate publish

## Outcome

Turn one accepted working-tree scope into a green draft pull request without
repeated commit/push/PR approvals or hidden authority expansion.

## Invocation authority

Explicit `$tracktemplate-publish` invocation, or the publication stage
delegated by an explicit
[`$tracktemplate-continue`](../tracktemplate-continue/SKILL.md) invocation,
authorises all of the following for the current bounded change:

- inspect and validate the intended working-tree scope;
- create an `agent/<description>` branch when starting on the default branch;
- stage only that scope and create one or more coherent commits;
- push the branch and open or update one draft pull request;
- monitor required CI for the exact pushed commit; and
- classify, repair, revalidate, commit and push failures whose fixes remain
  inside the same accepted scope.

The invocation does not authorise merging, marking a draft ready, tagging,
releasing, force pushing, rewriting history, deleting branches, weakening
tests, changing an accepted oracle, accepting a gate or expanding product
scope. Stop for new owner authority when a fix would cross one of those
boundaries.

## Preparation

1. Read `reference/PROJECT_PLAN.md`, `reference/VALIDATION.md`,
   `reference/TESTING_POLICY.md` and `reference/RECOVERY_AND_BACKUP.md`.
2. Inspect `git status --short --branch`, the complete diff including untracked
   files, current HEAD, upstream, remote URL and remote default branch.
3. Confirm `gh` is installed and authenticated. Resolve the exact repository,
   base branch and any existing pull request before external mutation.
4. Treat the invocation as authority only for files belonging to the current
   accepted task. If unrelated or ownership-ambiguous changes are present,
   stop and ask which paths belong.
5. Use `$tracktemplate-change-validation` and
   `$tracktemplate-quality-review` when their evidence has not already been
   completed for the exact source state.

## Publication workflow

1. Fetch remote state and verify that the intended base has not moved beyond
   the local base. Do not silently rebase or merge a dirty tree.
2. If on the default branch, create a descriptive `agent/<description>`
   branch. Reuse the current non-default branch only when it belongs to this
   task.
3. Split distinct authority, implementation and automation slices into
   coherent commits when that improves review. Stage explicit paths; do not
   use broad staging when the tree contains unrelated changes.
4. Review the staged diff and run the proportionate checks against the staged
   source state. Commit with concise outcome-led messages.
5. Push with upstream tracking. Never force push.
6. Reuse an existing pull request for the same head branch or create one draft
   pull request targeting the resolved default branch. Its body must state:
   what changed, why, scope exclusions, validation actually run, GUI evidence
   still outstanding and risk or authority changes.
7. Inspect required checks for the exact commit SHA. A local pass does not
   substitute for GitHub Actions.
8. On failure, preserve the failing run, job, step and first relevant output;
   classify it under `reference/TESTING_POLICY.md`; reproduce it locally when
   possible; repair only the classified boundary; rerun the original proof and
   affected profile; review the diff; commit and push the bounded repair.
9. Repeat monitoring until required checks pass or a genuine authority,
   environment or external-service blocker remains.
10. Stop with a green draft pull request. Merging requires a separate explicit
    project-owner instruction.

## Safety and repeatability

- Never use `git clean`, destructive restore/reset, force push or history
  rewriting.
- Do not commit ignored GUI evidence, operator documents, credentials, IDE
  state, environments, caches or generated output.
- Do not create a duplicate branch, commit or pull request when an equivalent
  one already exists; inspect first and resume safely.
- Do not change frozen evidence or create a phase decision merely to describe
  publication.
- A green check is technical evidence only. It does not accept a renderer,
  phase exit, release or production-output authority.

## Report

Report the branch, commits, pull-request link and base, exact remote CI result,
checks run locally, any classified repairs, remaining GUI evidence, scope
exclusions and the separate authority still needed to merge.
