# IDE workspace-alignment evaluation cases

Use these cases to evaluate routing and loss-safe behaviour. A successful
response distinguishes Git authority, file-backed IDE evidence and operator-only
confirmation rather than merely mentioning PyCharm.

## Should activate

1. "PyCharm still shows the branch from a merged pull request. Put my normal
   project back on current main without losing any worktree changes."
2. "Audit every TrackTemplate worktree and tell me whether the project I opened
   uses the expected interpreter and Git root."
3. "An active branch has uncommitted changes under `/tmp`; reconcile the IDE
   workspace safely."
4. A literal `$tracktemplate-continue` cycle starts from an IDE-backed checkout
   with multiple registered worktrees.
5. "A stash with a recovery label stays after the merge commit. Before you
   report recovery, validate its stash ownership, recovery purpose, unique
   content, and stash disposition."

Before a Git change, the agent must make a local-state inventory. The agent
must route the Git change to the Git workflow. If the retirement plan has
ambiguous or uniquely owned state, the agent must keep the worktree. If the
agent cannot examine the active PyCharm display, the agent must tell the user.

## Worktree retirement input

"The pull request for this worktree has the pull-request state `MERGED`. The
worktree has tracked cleanliness and local files that Git ignores. Does the
recovery policy give removal authority?"

Before worktree removal, the agent must make a local-state inventory. The agent
must route removal to the Git workflow. If the retirement plan has ambiguous or
uniquely owned state, the agent must keep the worktree. If the agent cannot
examine the active PyCharm display, the agent must tell the user.

## Should not activate alone

1. "Delete these merged Git branches." The agent must route the operation to
   the Git workflow. Workspace alignment gives no removal authority for a branch.
2. "Review PR #42." The agent must use a review for the pull request. If
   workspace alignment is also necessary, the agent must also use this skill.
3. "Fix this Python error." The agent must use `tracktemplate-debugging`
   and `tracktemplate-python-writing`.
4. "Choose the next bounded cycle in Phase 6." The agent must use
   `tracktemplate-chief-of-staff`. IDE data gives no project authority for
   product selection.

## Composition cases

- With context recovery: the implementing agent finds the canonical owner of
  dirty work. The agent then compares the workspace.
- With Git workflow: the implementing agent finds a primary worktree on a
  branch with the pull-request state `MERGED`. The agent also finds a `/tmp`
  branch with unfinished work. The implementing agent uses Git for each branch
  operation only with project authority.
- With `$tracktemplate-continue`: before the first Git change, the implementing
  agent compares the workspace. After Git changes protected `main` to the
  accepted commit, the agent compares the workspace again.

## Failure cases

Reject an agent result with any of these conditions:

- Use of a run configuration or display name as branch evidence
- Removal authority from tracked cleanliness or the pull-request state `MERGED`
- Git change without project authority
- Use of `recentProjects.xml` as evidence for the active PyCharm display
- Change to `.idea` or SDK data without bounded scope
- Unfinished work only in `/tmp`.

For worktree retirement, the agent must reject a result with any of these
conditions:

- Removal authority from the pull-request state `MERGED` or tracked cleanliness
- No local-state inventory in the result
- No result from the preservation audit
- Removal authority from a Git ignore rule
- Ambiguous or uniquely owned state in the retirement plan
- Git change to a branch or worktree without removal authority.

While the stash inventory contains a retained stash, reject a complete recovery
result. If the stash inventory or stash disposition evidence is not complete,
reject the result.
