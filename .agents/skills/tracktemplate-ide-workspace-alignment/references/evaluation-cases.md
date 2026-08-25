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

Before Git changes state, the agent must make a local-state inventory. The
result must route Git operations to the canonical workflow. If the plan has
ambiguous or uniquely owned state, the result must preserve the work. If the
agent cannot examine the active PyCharm display, it must ask the user to examine it.

## Should not activate alone

1. "Remove these Git branches for accepted pull requests." Route to the Git workflow. Branch
   removal is not IDE alignment authority.
2. "Review PR #42." Route to pull-request review unless IDE/worktree alignment
   is also in scope.
3. "Fix this Python traceback." Route to debugging and Python writing.
4. "Choose the next Phase 6 implementation tranche." Route to programme and
   technical selection. IDE state gives no authority for a product decision.

## Composition cases

- With context recovery: ownership of dirty work is unknown. Context recovery
  identifies the owner before this skill compares the workspace.
- With Git workflow: this skill identifies a primary project on a branch for
  a pull request with the `MERGED` state. It also identifies a `/tmp` branch
  that is not safe. Git shows accepted-history containment.
  The Git workflow does each branch operation only with authority.
- With continue: before its first Git mutation, compare the workspace. Before
  the Git workflow adds a branch, compare the workspace again with protected
  `main` at the accepted commit.

## Failure cases

If a result has one of these conditions, reject it:

- It uses the name of a run configuration or display as branch evidence.
- It gives removal authority from a merge or tracked cleanliness.
- It continues without a complete local-state inventory and preservation evidence.
- It uses a Git ignore rule as removal authority.
- It continues when the plan has ambiguous or uniquely owned state.
- It removes state, uses `git worktree prune`, changes a branch, or moves state
  without Git authority for that operation.
- It uses `recentProjects.xml` as evidence for the active PyCharm display.
- It changes `.idea` or global SDK state without explicit scope.
- When no commit or branch on GitHub contains the work, it keeps the work only
  in `/tmp`.

While the stash inventory contains a retained stash, reject a complete recovery
result. If the stash inventory or stash disposition evidence is not complete,
reject the result.
