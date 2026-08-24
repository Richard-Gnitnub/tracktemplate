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

Require the response to inventory before mutation, delegate Git operations to
their owning workflow, preserve ambiguous work and request UI confirmation when
the physical window cannot be observed.

## Should not activate alone

1. "Delete these merged Git branches." Route to the Git workflow; branch
   deletion is not IDE alignment authority.
2. "Review PR #42." Route to pull-request review unless IDE/worktree alignment
   is also in scope.
3. "Fix this Python traceback." Route to debugging and Python writing.
4. "Choose the next Phase 6 implementation tranche." Route to programme and
   technical selection; IDE state supplies no product priority.

## Composition cases

- With context recovery: ownership of dirty work is unknown. Context recovery
  establishes attribution before this skill compares the workspace.
- With Git workflow: this skill identifies a stale primary project and an
  unsafe `/tmp` branch; Git proves reachability and performs any authorised
  switch or move.
- With continue: compare before its first Git mutation and again after protected
  `main` is synchronised, before a new branch is created.

## Failure cases

Reject or stop when a response:

- infers the branch from a run-configuration or window name;
- calls a clean merged worktree disposable without proving reachability and
  inactivity;
- deletes, prunes, switches or moves state without separate Git authority;
- treats `recentProjects.xml` as proof of the physical focused window;
- changes `.idea` or global SDK state without explicit scope; or
- leaves active uncommitted or unpushed work solely under `/tmp`.

Also reject a result that closes recovery with a retained stash. Reject it
when the stash inventory or stash disposition evidence is not complete.
