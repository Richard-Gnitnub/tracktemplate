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
6. "This TrackTemplate worktree is for a pull request with the `MERGED` state.
   It has tracked cleanliness and ignored local files. Does the recovery policy
   give removal authority?"

Before Git changes a branch, the agent must route the operation to the Git
workflow. Before worktree removal, the agent must make a local-state inventory.
The agent must route worktree removal to the Git workflow. If the
retirement plan has ambiguous or uniquely owned state, the agent must preserve
each item. If the agent cannot examine the active PyCharm display, the agent must
tell the user to examine it.

## Should not activate alone

1. "Remove these Git branches for accepted pull requests." Route to the Git
   workflow. Workspace alignment gives no removal authority.
2. "Review PR #42." Route to pull-request review unless IDE/worktree alignment
   is also in scope.
3. "Fix this Python traceback." Route to debugging and Python writing.
4. "Select the next Phase 6 product change." Route to
   `tracktemplate-chief-of-staff`. Do not use PyCharm data as authority for a
   product decision.

## Composition cases

- With context recovery: the canonical owner for dirty work is unknown. Before
  the implementing agent compares the workspace, the agent identifies the
  canonical owner.
- With Git workflow: the implementing agent identifies a primary worktree on a
  branch for a pull request with the `MERGED` state. The agent also identifies a
  `/tmp` branch with work that no commit or branch on GitHub contains. Git shows
  accepted-history containment. The implementing agent uses Git for each branch
  operation only with project authority.
- With Continue: before the implementing agent uses Git to change a branch or
  worktree, the agent compares the workspace. Before the agent adds a branch
  with Git, the agent compares the workspace with protected `main` at the
  accepted commit.

## Failure cases

Reject a result for one of these conditions:

- The agent uses the name of a run configuration or display as branch evidence.
- The agent gives removal authority from a merge or tracked cleanliness.
- The agent continues without a local-state inventory and evidence from the
  preservation audit.
- The agent uses a Git ignore rule as removal authority.
- The agent continues when the retirement plan has ambiguous or uniquely owned
  state.
- The agent does a Git operation without project authority for that operation.
- The agent uses `recentProjects.xml` as evidence for the active PyCharm display.
- The agent changes `.idea` or SDK state without bounded scope.
- The agent keeps unfinished work only in `/tmp` when no commit or branch on
  GitHub contains the unfinished work.

While the stash inventory contains a retained stash, reject a complete recovery
result. If the stash inventory or stash disposition evidence is not complete,
reject the result.
