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
6. "This merged TrackTemplate worktree has tracked cleanliness but also has ignored local
   files. Show whether it is inactive and safe to remove without loss of sole
   source or evidence state."

The response must make an inventory before mutation and delegate Git operations
to their owning workflow. It must preserve ambiguous work and ask for UI
confirmation when the environment cannot observe the physical window.

## Should not activate alone

1. "Remove these merged Git branches." Route to the Git workflow; branch
   removal is not IDE alignment authority.
2. "Review PR #42." Route to pull-request review unless IDE/worktree alignment
   is also in scope.
3. "Fix this Python traceback." Route to debugging and Python writing.
4. "Choose the next Phase 6 implementation tranche." Route to programme and
   technical selection; IDE state supplies no product priority.

## Composition cases

- With context recovery: ownership of dirty work is unknown. Context recovery
  establishes attribution before this skill compares the workspace.
- With Git workflow: this skill identifies a stale primary project and an
  unsafe `/tmp` branch. Git shows reachability and does any authorised branch
  change or move.
- With continue: compare before its first Git mutation and again after protected
  `main` is synchronised, before a new branch is created.

## Failure cases

Reject or stop when a response:

- Uses a run-configuration or window name as branch evidence
- Says that a merged worktree with tracked cleanliness is disposable without
  reachability, inactivity, complete ignored/local-state classification, and preservation
- Uses a Git ignore rule as disposal authority or continues when local-state
  ownership is ambiguous
- Removes state, runs `git worktree prune`, changes a branch, or moves state
  without separate Git authority
- Uses `recentProjects.xml` as proof of the physical focused window
- Changes `.idea` or global SDK state without explicit scope
- Leaves active uncommitted or unpushed work solely under `/tmp`.

While the stash inventory contains a retained stash, reject a complete recovery
result. If the stash inventory or stash disposition evidence is not complete,
reject the result.
