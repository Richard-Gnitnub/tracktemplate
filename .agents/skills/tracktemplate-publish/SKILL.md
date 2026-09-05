---
name: tracktemplate-publish
description: Publish one bounded TrackTemplate change as a draft pull request. Validate, commit, push, and monitor necessary CI. Use only after explicit `$tracktemplate-publish` invocation or publication delegation from an explicit `$tracktemplate-continue` cycle. This skill gives no merge, tag, release, destructive-history, or wider scope authority.
---

# TrackTemplate publish

## Purpose

Publish one accepted scope of working-tree changes as a draft pull request
with successful necessary CI. The invocation supplies the bounded authority
below. Commit, push, and pull-request approvals are not necessary again.

## Invocation authority

Explicit `$tracktemplate-publish` invocation authorises these operations for
the current bounded change:

- Inspection and validation of the intended working-tree changes.
- Creation of an `agent/<description>` branch from the default branch.
- Git staging of only the accepted scope.
- Creation of one or more coherent commits.
- Branch push.
- Creation or update of one draft pull request.
- Monitoring of necessary CI for the exact pushed commit.
- Classification, repair, validation, commit, and push of failures within the
  same accepted scope.

Repair authority applies to source and tests. For governance documents,
publication only verifies final bytes and reports CI `PASS` or `FAIL`.
This limit applies after the one Documentation Review, permitted adjustment,
and final deterministic validation. Publication cannot edit that prose or
invoke another documentation or quality review. It cannot reinterpret meaning
or start an improvement pass.

Publication delegated by an explicit
[`$tracktemplate-continue`](../tracktemplate-continue/SKILL.md) invocation has
narrower authority. It permits branch, commit, push, draft, and CI operations
only for the exact frozen source state. That state must have completed final
validation and a different read-only staff review in the continuation cycle.
The delegation gives no repair authority to this skill.

If necessary CI fails during delegated publication, return the evidence to the
continuation workflow. Do not edit, commit, or push a repair. The continuation
workflow owns the shared pass limit, repeated validation, and renewed staff
review.

The invocation does not authorise these operations:

- Merge or a change from draft to ready.
- Tag or release.
- Force push, history rewrite, or branch deletion.
- Weaker tests or changes to an accepted oracle.
- Gate acceptance or wider product scope.

If a repair crosses one of these boundaries, stop for new owner authority.

## Preparation

1. Before the first publication operation, use this command:
   `.venv/bin/python tools/development_toolchain_preflight.py --stage publication`.
   Publication operations include GitHub queries, fetch, branch, commit,
   push, and pull-request actions. If the development-toolchain preflight
   does not pass, stop before publication.
2. Read `reference/PROJECT_PLAN.md`, `reference/VALIDATION.md`,
   `reference/TESTING_POLICY.md`, and `reference/RECOVERY_AND_BACKUP.md`.
3. Examine `git status --short --branch`. Examine the complete diff,
   including untracked files. Examine current HEAD, upstream, remote URL,
   and remote default branch.
4. Before external mutation, identify the exact repository, base branch, and
   any existing pull request.
5. Limit invocation authority to files in the current accepted task.
   If changes are unrelated or their ownership is ambiguous, stop.
   Ask which paths belong to the task.
6. If evidence is incomplete for the exact source state, use
   `$tracktemplate-change-validation`. For source or tests, also use
   `$tracktemplate-quality-review`. For governance prose, make sure that the
   finite Technical Author Lead record is complete. Do not add another review.
7. For delegated publication, record the reviewed paths and content state
   supplied by `$tracktemplate-continue`. If current or staged source
   differs, stop.

## Publication procedure

1. Fetch remote state. Make sure that the intended base has not advanced beyond
   the local base. Do not silently rebase or merge a dirty tree.
2. If the current branch is the default branch, make a descriptive
   `agent/<description>` branch. Reuse a non-default branch only if it
   belongs to this task.
3. Where it makes review better, put distinct authority, implementation, and
   automation changes in different coherent commits. Stage explicit paths.
   If unrelated changes exist, do not use broad staging.
4. Review the staged diff. Do proportionate checks against the staged source
   state. For delegated publication, make sure that it equals the recorded
   final reviewed source. Commit with concise messages that give the result.
5. Push with upstream tracking. Never force push.
6. Reuse the existing pull request for the same head branch, or make one
   draft. Target the identified default branch. Include the information
   listed below in the pull-request body.
7. Examine necessary checks for the exact commit SHA. A local pass does not
   replace GitHub Actions.
8. If a check fails, preserve the failing run, job, step, and first related
   output. Follow the failure procedure below.
9. For a direct invocation, continue monitoring until necessary checks pass or
   an authority, environment, or external-service blocker remains. For
   delegated publication, use the resumption conditions below.
10. After necessary checks pass for the exact commit, stop with a draft pull
    request. Merge needs a different explicit project-owner instruction.

The pull-request body must give these items:

- What changed and why.
- Excluded scope.
- Completed validation.
- GUI evidence that is still absent.
- Risk or authority changes.

### Failure procedure

For a governance-document CI failure, stop for the owner. Do not change its
prose or invoke another review.

For delegated publication, stop. Return the evidence to
`$tracktemplate-continue` without source or Git changes.

For a direct explicit invocation with a source/test failure, follow these
steps:

1. Classify the failure under `reference/TESTING_POLICY.md`.
2. Where possible, reproduce it locally.
3. Repair only the classified boundary.
4. Do the original proof again.
5. Do the checks in the affected validation profile again.
6. Review the diff.
7. Commit the bounded repair.
8. Push the repair.

### Conditions for delegated resumption

Continue delegated publication only with a new exact source state from the
continuation workflow. That workflow must have repeated validation. It must
also have obtained another different read-only staff review within its shared
pass limit.

## Safety and repeatability

- Never use `git clean`, destructive restore/reset, force push, or history
  rewrite.
- Do not commit ignored GUI evidence, operator documents, credentials, IDE
  state, environments, caches, or generated output.
- Before creation of a branch, commit, or pull request, check for an equivalent
  existing item. If one exists, continue safely without duplication.
- Do not change frozen evidence to report publication.
- Do not make a phase decision to report publication.

A successful check is technical evidence only. It does not accept a renderer,
phase exit, release, or production-output authority.

## Report

Report these results:

- Branch and commits.
- Pull-request link and base.
- Exact remote CI result.
- Local checks and classified repairs.
- GUI evidence that remains absent.
- Excluded scope.
- Separate authority still necessary for merge.
