---
name: tracktemplate-ide-workspace-alignment
description: Compare TrackTemplate's operator-facing PyCharm project, interpreter and run configuration with Git-authoritative worktrees, branches, heads and pull-request mapping. Use when a project may show stale merged work, multiple or temporary worktrees exist, interpreter or working-directory ownership is uncertain, or tracktemplate-continue must verify that clean accepted main is the canonical IDE view. This skill audits and reports IDE alignment; Git workflows remain authoritative for Git mutations.
---

# TrackTemplate IDE workspace alignment

## Outcome

Compare the operator-facing PyCharm environment with current Git authority and
produce one loss-checked alignment report. Keep accepted `main` visible in the
primary project, active work isolated in named persistent worktrees and
temporary review state disposable without treating IDE metadata as Git truth.

## Responsibility boundary

Keep Git workflows authoritative for branches, worktrees, commits, upstreams,
pull requests, reachability and every safe Git operation. This skill may ask
for that evidence and describe the required end state, but it does not grant
checkout, move, removal, prune, deletion, commit, push or merge authority.

Own comparison of the IDE environment against that Git evidence, including:

- the opened project directory and its backing Git worktree;
- the branch and exact HEAD exposed through that directory;
- project SDK, resolved interpreter and virtual-environment ownership;
- run/debug working directories and VCS roots;
- active pull-request branches and their worktree locations;
- stale merged-branch detection and canonical accepted-main visibility; and
- operator action when the physical PyCharm window cannot be proved.

Use [`RECOVERY_AND_BACKUP.md`](../../../reference/RECOVERY_AND_BACKUP.md) for
destructive-action and recovery controls. Use
[`$tracktemplate-context-recovery`](../tracktemplate-context-recovery/SKILL.md)
first when dirty work or its owner is unclear.

## Evidence boundary

Treat these as file- or Git-provable when their exact commands and paths are
available:

- repository root, common Git directory and registered worktrees;
- each worktree's branch, HEAD, upstream, cleanliness and ahead/behind counts;
- untracked, uncommitted, unpushed and branch-unique work;
- current remote `main`, pull-request state and merged-head reachability;
- `.idea/vcs.xml`, `.idea/misc.xml`, module files and saved run configurations;
- JetBrains recent-project and SDK-table entries;
- the resolved interpreter executable and `pyvenv.cfg`; and
- whether a configured path exists and belongs to the expected project.

For each stash, use Git to record the stash selector and stash commit SHA.
Also record each stash component. Project owner records, not Git, supply the
recovery purpose and disposition authority. Git metadata cannot supply that
authority.

Treat these as operator-confirmed unless the active host environment can prove
them directly:

- which physical PyCharm window is visible and focused;
- the branch indicator and project path presently shown in that window;
- unsaved editor buffers or Local History not represented on disk;
- the run/debug configuration selected in the UI; and
- whether PyCharm has refreshed its VCS state after an external Git action.

Do not use the name of a run configuration as branch evidence. Do not use a
filename from a test as branch evidence. Do not use an entry that records an
opened file as branch evidence. Do not use a window title or SDK name as branch
evidence. Use the Git worktree to identify the branch.

## Alignment workflow

1. Confirm that any preceding agent cycle and delegated work are complete
   before changing a checkout, branch or worktree.
2. Ask the Git workflow for a read-only inventory: repository and common Git
   roots, all worktrees, exact branch/HEAD/upstream state, cleanliness,
   ahead/behind counts, unique work, current remote `main`, open pull requests
   and merged-branch reachability.
   Include the complete stash inventory.
3. Identify the intended primary PyCharm project from the request and
   JetBrains project metadata. Do not silently choose a similarly named copy.
4. Inspect project VCS roots, SDK name and resolved path, virtual-environment
   creation metadata, and every saved or recent run/debug working directory.
5. Map each active implementation or pull-request branch to one named
   persistent worktree. Classify `/tmp` worktrees as disposable review state or
   as unsafe sole active state.
Map interrupted work to its recovery branch, recovery worktree, and recovery
commit. If the stash inventory contains a retained stash, stop. Do not give the
recovery gate a complete result.

6. Compare the observed arrangement with the steady-state convention below.
   Report the complete pre-change inventory before requesting any Git mutation.
7. Stop on dirty-work ownership, unique-commit, active-use, path, interpreter or
   physical-window uncertainty. Preserve the state and name the smallest fact
   or operator confirmation needed.
8. When separately authorised, let the Git workflow perform only the proved
   safe switch, synchronisation or worktree operation. Hash or otherwise
   fingerprint dirty state before a move and verify its exact status afterward.
9. Re-read Git and IDE metadata after alignment. Ask the operator to confirm
   the physical PyCharm project path and branch indicator when the environment
   cannot observe the window itself.

Do not edit `.idea`, global JetBrains settings or an interpreter merely to make
the audit green. Report a mismatch first; change operator-owned IDE state only
under explicit scope.

## Steady-state convention

```text
Primary PyCharm project
    clean accepted main
    stable interpreter
    operator's canonical project view

Named persistent worktrees
    one per active implementation or PR branch
    opened as separate PyCharm projects when needed

Temporary /tmp worktrees
    disposable review and integration only
    never the sole location of active, uncommitted or unpushed work
```

If the pull-request state is `MERGED`, the primary worktree must not use the
feature branch for that pull request. Before Git changes the branch,
show accepted-history containment. Before Git changes the branch, show tracked
cleanliness. The `MERGED` state gives no removal authority.

Show that the accepted commit for `origin/main` contains the branch tip. Show
that the accepted commit contains each commit on the branch. Make sure that the
worktree has tracked cleanliness. Make sure that no person or process uses the
worktree. Make sure that a different location contains all IDE data and user
data. Use the
[worktree retirement procedure](../../../reference/RECOVERY_AND_BACKUP.md#worktree-retirement).
Make a local-state inventory. Classify each item in the local-state inventory.
A Git ignore rule gives no removal authority. If the retirement plan has
ambiguous or uniquely owned state, keep the worktree. If the preservation audit
does not give a complete result, keep the worktree. If a person or process uses
the worktree, keep the worktree.

Use the
[procedure for visible recovery state](../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state).
Its canonical owner is the recovery policy. A recovery branch or worktree is
visible recovery state. It is not
accepted product state. While an emergency stash stays in the stash inventory,
do not end workspace alignment.

## Composition with TrackTemplate continue

When composed by
[`$tracktemplate-continue`](../tracktemplate-continue/SKILL.md), complete
workspace alignment before Continue uses Git to change a branch or worktree.
After the Git workflow reconciles the repository, complete workspace alignment
again. Before a new bounded cycle, make sure that the primary project uses protected
`main` at the accepted commit. Make sure that each active branch has a
worktree or a branch on GitHub. Report each temporary worktree that stays. If
the agent cannot examine the active PyCharm display, tell the user to examine
it. Do not report UI evidence that the agent cannot examine.

## Report

Report:

1. Repository root and worktree map with all worktrees
2. Exact Git identity, branch on GitHub, tracked cleanliness, and accepted-history containment for each worktree
3. Pull-request state and accepted-history containment for each branch
4. Path of the primary worktree, VCS roots, active Python environment, and directory for each tool operation
5. File and Git evidence, and information that the user must supply
6. Project authority for each Git change and evidence after each change
7. Worktree map after workspace alignment and cause for each worktree that stays
8. Local-state inventory and the local-state type for each item
9. Evidence that no person or process uses the worktree
10. Worktree map after worktree retirement
11. Limitation or work without applicable project authority.

When maintaining this skill or its routing, exercise the
[evaluation cases](references/evaluation-cases.md) and run the repository
agent-guidance, documentation and quality-review controls.
