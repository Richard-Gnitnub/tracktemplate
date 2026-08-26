# Recovery and Backup Policy

Status: **active project-control policy adopted on 2026-07-22. Timeshift is
configured for scheduled system snapshots but a recent snapshot/restore has
not been verified; tracked-source recovery and repository safety checks are
active; an ext4 removable USB destination on a separate physical device has a
passed initial repository snapshot and restore drill, accepted by the project
owner on 2026-07-22. The owner confirmed that all valuable project files are
inside the repository and no external project files require backup, and
accepted the repeat/retention routine. Its incremental second-snapshot proof
passed, closing QA-R01 on 2026-07-22. The ongoing cadence remains mandatory.
Triggered Phase 4 snapshots passed before both the copied-target orchestration
and exact-family support tranches on 2026-07-27. The required independent
Phase 5 closeout snapshot passed on 2026-08-01 before any closeout status
change was retained.**

## Purpose

Protect the operating system, tracked project history, ignored local evidence,
FreeCAD working documents and production outputs against accidental deletion,
bad automation, disk failure and an incorrect Git operation. No single layer
is called a backup for data outside its actual scope.

This policy is operational control, not evidence that a backup or restore has
succeeded. Positive backup status requires a real destination, a completed
versioned backup and a tested restore.

## Current protection state

| Layer | State on 2026-07-22 | Boundary |
| --- | --- | --- |
| Codex filesystem sandbox | Active | Routine writes are restricted to the project, temporary storage and the agent workspace; an explicit elevation is a separate user decision |
| Timeshift system snapshots | Configured: daily, five retained; recent snapshot/restore not verified | Current configuration excludes `/home/richard/**`; it protects system state, not this project or personal FreeCAD documents |
| Local Git history | Active | Protects committed content; it does not protect untracked or ignored files |
| GitHub `main` | Active and verified 2026-07-28 | Strict, up-to-date `validation` from GitHub Actions app `15368` is required; administrator enforcement is active; force pushes and branch deletion remain blocked; no pull-request review count is required |
| GitHub remote history | Active | Off-machine copy of pushed Git objects; not a complete backup of ignored assets and not independent of account/repository administration |
| Independent project-data backup | **Operational for the complete declared project-data scope** | A dated, non-overwriting snapshot on a separate ext4 USB covers `.git`, ignored evidence, repository FCStd fixtures and the source archive; the owner confirmed no valuable external project files require backup |
| Restore drill | **Passed and owner-accepted for the complete declared scope on 2026-07-22** | See the [backup, restore and repeat record](backup-records/2026-07-22-initial-repository-backup-restore.md) |
| Repeat and retention | **Active and verified again 2026-08-01** | The accepted cadence and hard-linked incremental retention were proved again by the [Phase 5 closeout snapshot](backup-records/2026-08-01-phase5-closeout-snapshot.md), covering Git and ignored Phase 5 raw evidence; QA-R01 remains closed |

## Initial implementation and remaining risk

On 2026-07-22 the project owner first authorised bounded development while the
removable device was prepared, then reported that the reformatted device was
ready. The destination audit passed, a new dated repository snapshot completed
without deleting existing destination content, and a complete restore into an
empty temporary directory passed the checks recorded in the
[dated evidence](backup-records/2026-07-22-initial-repository-backup-restore.md).

That is positive recovery evidence for the complete valuable project-data
scope declared by the owner on 2026-07-22. The project owner accepted the
successful repository-scope backup and restore drill and confirmed that no
valuable project files outside the repository require backup. Retention is now
represented by multiple complete dated sets, most recently the triggered
2026-07-27 pre-support repeat linked below. The owner accepted the repeat/
retention routine on 2026-07-22, and incremental snapshot proofs passed exact
comparison while adding only changed payload storage. The required
2026-08-01 Phase 5 closeout repeat then passed exact comparison for the
complete declared scope, including Git and ignored raw evidence. The audit may
therefore report QA-R01 closed for the current declared scope; a missed
cadence, failed run or scope change must reopen the exposure rather than rely
on this historical result.

The backup gate is closed for the current declared scope, but these operating
controls remain mandatory:

- establish and push a clean Git checkpoint before each risky tranche;
- do not perform an exceptional destructive action against project or operator
  data;
- keep automation on copied/disposable FCStd inputs;
- avoid accumulating a sole irreplaceable result under an ignored path; and
- review backup currency and declared scope at every phase closeout.

## Backup cadence and retention

The project owner accepted this routine on 2026-07-22:

- create a new dated, non-overwriting snapshot before risky migration work and
  after an accepted tranche that adds valuable local evidence;
- while development is active, complete at least one successful snapshot per
  week even when neither trigger occurs;
- retain the initial accepted snapshot plus at least four recent successful
  snapshots;
- never delete snapshots automatically; removing an older exact set requires
  project-owner authority after a newer set and its evidence are verified;
- perform an empty-directory restore drill at least monthly and again at the
  Phase 11 gate; and
- flush, safely unmount and store the USB separately from the computer between
  backup runs.

Incremental snapshots may hard-link unchanged files on the USB, but each dated
directory must present a complete repository tree and must never overwrite or
mutate an accepted earlier set. The verified repeat is recorded in the
[2026-07-22 backup and restore record](backup-records/2026-07-22-initial-repository-backup-restore.md).
The triggered `2026-07-27-pre-phase4-migration-01` repeat is recorded in its
[dated snapshot record](backup-records/2026-07-27-pre-phase4-migration-snapshot.md).
The later `2026-07-27-pre-phase4-family-support-01` repeat is recorded in its
[dated pre-support record](backup-records/2026-07-27-pre-phase4-family-support-snapshot.md).
The `2026-08-01-phase5-closeout-01` repeat is recorded in its
[dated closeout record](backup-records/2026-08-01-phase5-closeout-snapshot.md).
Missing the cadence, changing the valuable-data scope or failing a later run
reopens QA-R01 or creates a successor risk; historical evidence must not be
rewritten.

Authoritative background: Linux Mint documents that Timeshift does not include
personal data; GitHub documents branch protection against force push and
deletion; CISA documents the three-copy, two-media, one-offsite principle.

- <https://linuxmint-user-guide.readthedocs.io/_/downloads/en/latest/pdf/>
- <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>
- <https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf>

## Data that the independent backup must cover

Back up the complete repository checkout, including `.git/` and ignored local
assets. At minimum this includes:

- `reference/t5_files_556b_06_feb_2025.zip`, whose accepted SHA-256 is recorded
  in `PROVENANCE.md`;
- `benchmark-output/` when it contains costly raw observations, copied FCStd
  fixtures, screenshots or local oracle captures;
- any valuable `exports/`, `output/` or other production result not reproducible
  from committed canonical state;
- all working `.FCStd` documents wherever the operator stores them; and
- any local configuration or evidence needed to reproduce a result and not
  already committed.

Python environments, bytecode and disposable caches may be excluded to save
space because tracked dependency/setup instructions must recreate them. A
backup configuration must not exclude a file merely because Git ignores it.

The target must be outside the repository and on a different storage device
or independently administered remote service. A second directory on the same
NVMe device is not an independent backup. Off-site/cloud content must be
encrypted when it contains private documents, credentials or local paths.

## Destructive-action rules

The following are prohibited during routine project work:

- `git clean` in any form, because ignored paths contain local evidence;
- `git reset --hard`, destructive `git checkout`/`git restore`, force push,
  branch deletion or tag deletion;
- broad recursive deletion or overwrite, including a target expressed as `/`,
  `$HOME`, `~`, the workspace root, an unresolved variable, a wildcard or a
  command substitution;
- running the IDE, FreeCAD automation or development tools as root;
- changing system files, installing/removing software or using `sudo` merely
  as a development convenience; and
- opening or saving automation results over the only copy of a working FCStd.

An exceptional destructive action requires all of the following before it is
run:

1. explicit project-owner authority for that exact action;
2. a read-only inspection resolving the exact target;
3. a clean, pushed recovery checkpoint or a separately verified backup of the
   affected untracked data;
4. the narrowest recoverable operation, preferring quarantine/trash or a copied
   target; and
5. a post-action inventory stating what changed and how it can be recovered.

Temporary directories created specifically for one test may be removed by
their owning test after their resolved path is proved to be beneath the
temporary root. This exception never applies to the repository, a home
directory or an operator document.

## Development checkpoint procedure

Before a risky experiment, migration tranche, bulk edit or external tool run:

1. run `.venv/bin/python tools/repository_safety_audit.py`;
2. inspect `git status`, the current branch, HEAD and upstream relationship;
3. commit and push the previous accepted state when the work requires a clean
   recovery point;
4. use a dedicated branch/worktree for disposable or high-risk exploration;
5. copy every FCStd input and verify the source hash before and after the run;
   and
6. run `tools/repository_safety_audit.py --require-checkpoint` only after the
   clean checkpoint has been pushed.

The audit uses local remote-tracking state and performs no network operation.
Fetch explicitly before relying on it when another actor may have updated the
remote.

<a id="visible-recovery-state"></a>

## Visible recovery state

TrackTemplate workflows must not use `git stash` for planned preservation,
recovery, or handoff. Use named Git state for planned preservation.

Use this sequence:

1. Keep usual unfinished work on a feature branch and its worktree.
2. Keep interrupted work on a recovery branch.
3. When a recovery worktree is available, use it.
4. Make a recovery commit that keeps the recovery state.
5. For local evidence, use a checksum manifest and the independent preservation
   method with project authority.
6. Use `git stash` only in an emergency to keep work available.

Record the recovery purpose and project owner of named Git state. Keep it
different from accepted `main`. A recovery commit is not product acceptance,
evidence acceptance, or merge authority. Do not stage sensitive evidence or
local evidence. Do not commit sensitive evidence or local evidence. Do not push
sensitive evidence or local evidence. Keep a checksum manifest with sensitive
paths local. Use independent preservation.

An emergency stash is temporary unresolved recovery state. Do not use it for
planned preservation or handoff. Record its `stash@{n}` selector. Record the
full SHA of the stash commit.

Do not put sensitive evidence or local evidence in a stash. When
`--include-untracked`, `-u`, `--all`, or `-a` can put such evidence in Git, do
not use them. Use approved independent preservation directly. If a stash
contains such evidence, do not stage that evidence. Do not commit that
evidence. Do not push that evidence. Before the owner authorises its
disposition, preserve it only with the approved independent method.

A stash disposition removes the stash from the inventory. It does not remove
its Git objects. Git can keep those objects when the stash inventory is empty.
This procedure does not control Git object removal. Do not use an automatic
operation to remove Git objects.

If a stash contains sensitive evidence or local evidence, the recovery gate
does not have a complete result. Stop this procedure. Before more Git work, get
project owner direction. Before more Git work, use
`$tracktemplate-security-review`.

Record the stash topology:

- Record the SHA of the base commit. Record the base tree.
- Record the SHA of the index parent. Record the index tree.
- Record the worktree tree.
- Record the SHA of the optional untracked-files parent. Record the U tree.

The U tree contains each untracked file. When the command makes a stash with
`--all`, the same U tree also contains each ignored file. Git keeps those files
only in U.

Complete this procedure during the same bounded cycle:

- If the stash has unique content that Git can contain, preserve it on a
  recovery branch or recovery worktree. Then, make a recovery commit. Compare
  the base tree with the index tree and worktree tree. Review each path,
  file-mode difference, and deletion.
- If unique content is sensitive evidence or local evidence, do not put it in a
  recovery commit. Compare each path and blob for that evidence with approved
  independent preservation. Preserve it only with that method.
- Compare each other path and blob in the U tree with the named Git state or
  approved independent preservation.
- If the stash has no unique content, validate each stash tree difference.
  Validate each path in the U tree.
- Get the applicable authority for the stash that the stash commit SHA
  identifies.
- Before the disposition, examine the stash inventory again. Validate that the
  stash selector identifies the same stash commit SHA and stash inventory.
- If the exact Git identity or a stash component changed, stop.
- Complete only that stash disposition. Then, examine the repository, stashes,
  and preservation state again. Record the preservation diff.

Do not use `drop`, `clear`, `overwrite`, `pop`, `rewrite`, `git stash branch`,
or other operation that removes a stash without a report and applicable
authority. A tool must not remove a stash only to get empty `git stash list`
output.

Until you complete this check sequence, the recovery gate does not have a
complete result:

- Examine the output of `git stash list`.
- Record the project owner, recovery purpose, stash selector, and full SHA of
  the stash commit.
- Record each B/I/W/U component in the stash inventory for each retained stash.
- Compare the base tree with the index tree and worktree tree. Review each path,
  blob, deletion, and file mode. Review each path and blob in the U tree.
  Preserve unique content that Git can contain in named Git state. Preserve
  sensitive evidence and local evidence only with approved independent
  preservation.
- Get applicable authority for this stash disposition.
- Before the disposition, validate that the stash selector, stash commit SHA,
  and stash inventory did not change.
- Complete only the stash disposition. Then, examine `git stash list` again.
  Review the preservation diff again.
- If a stash contains sensitive evidence or local evidence, stop this
  procedure. The recovery gate does not have a complete result. Before more Git
  work, get project owner direction. Before more Git work, use
  `$tracktemplate-security-review`.

A retained stash is unresolved recovery state. A recorded owner or purpose
does not give the recovery gate a complete result. If stash ownership,
recovery purpose, stash inventory, unique content, or stash disposition is
missing or changed, fail closed. The recovery gate does not have a complete
result. A completed recovery cycle has no retained stash and no unresolved
finding about sensitive evidence or local evidence.

<a id="worktree-retirement"></a>

## Worktree retirement

The pull-request state `MERGED` gives no removal authority. Tracked cleanliness
gives no removal authority. Use Git to show accepted-history containment for
tracked files. The pull-request state does not contain a local-state type for
ignored files or other local files.

Before worktree retirement, use this procedure:

1. If you do not know the accepted commit for `origin/main`, use `git fetch`.
2. Put the worktree, branch, HEAD, and accepted commit in the retirement plan.
3. Show that the accepted commit contains the branch tip.
4. Show accepted-history containment for each commit on the branch.
5. Show tracked cleanliness.
6. Make sure that no person or process uses the worktree.
7. Make sure that a different location contains all IDE data and user data.
8. Make a local-state inventory of all files that are not in the Git index.
9. Do not use a Git ignore rule as removal authority.
10. Put 1 local-state type for each item in the retirement plan:
   - **Authoritative local source**
   - **Retained evidence**
   - **Rebuildable cache/generated state**
   - **Temporary disposable state**
   - **Ambiguous or uniquely owned state**.
11. For authoritative local source or retained evidence, record the canonical
    owner.
12. For authoritative local source, preserve each item in a different location.
13. Preserve each item of retained evidence in a different location.
14. For each authoritative local source or retained evidence item, record the
    source file and copy.
15. Make sure that the source file and copy have the same bytes.
16. For rebuildable cache/generated state, record the canonical owner.
17. For rebuildable cache/generated state, put the applicable `PASS` result in
    the retirement plan.
18. For temporary disposable state, record the canonical owner.
19. For temporary disposable state, put the cause for removal in the retirement
    plan.
20. If evidence does not contain the canonical owner or local-state type,
    classify the item as ambiguous or uniquely owned state.
21. If the evidence does not show planned preservation or removal, classify the
    item as ambiguous or uniquely owned state.
22. If the retirement plan has ambiguous or uniquely owned state, stop.
23. If the retirement plan has ambiguous or uniquely owned state, keep the worktree.
24. If the retirement plan has ambiguous or uniquely owned state, tell the
    project owner that a bounded decision is necessary.
25. Put the removal authority in the retirement plan.
26. Before removal, examine the exact Git identity again.
27. Before removal, examine accepted-history containment again.
28. Before removal, examine tracked cleanliness again.
29. Before removal, make sure that no person or process uses the worktree.
30. Before removal, examine the local-state inventory SHA-256 again.
31. Before removal, examine the retirement plan again.
32. Before removal, examine the preservation audit again.

Use the retirement audit. The retirement audit returns the SHA-256 of the
local-state inventory:

```bash
.venv/bin/python tools/repository_safety_audit.py \
  --retirement-worktree /exact/registered/worktree
```

Keep the retirement plan local. Do not commit local paths. Do not commit local
evidence. Do not commit authentication data.

The retirement plan contains the branch for the worktree. The retirement plan
contains HEAD, the accepted commit, and the local-state inventory SHA-256. The
retirement plan contains the removal authority. The retirement plan contains
evidence that no person or process uses the worktree.

The retirement plan does not contain more than 1 local-state type for an item.
The retirement plan contains the canonical owner and result for each item. The
retirement plan contains each location for planned preservation.

For this repository, use `refs/remotes/origin/main` as `accepted_ref`.
Use this command to operate the retirement audit again:

```bash
.venv/bin/python tools/repository_safety_audit.py \
  --retirement-worktree /exact/registered/worktree \
  --retirement-plan /exact/local/retirement-plan.json \
  --require-retirement-ready
```

The retirement audit does not change Git state or local files. The retirement
audit returns item counts and the local-state inventory SHA-256. The retirement
audit does not return local paths or file data. The retirement audit gives no
removal authority.

The retirement audit returns `FAIL` if the worktree, branch, HEAD, accepted
commit, or local-state inventory SHA-256 changes. If a local-state inventory
item is not in the retirement plan,
the retirement audit returns `FAIL`. If the retirement plan contains more than
1 local-state type for an item, the retirement audit returns `FAIL`.

The retirement audit also returns `FAIL` for:

- A local-state type that is not one of the 5 local-state types
- Ambiguous or uniquely owned state
- An item without a canonical owner or result
- Different bytes in the source file and copy.

The retirement audit rejects an `assume-unchanged` or `skip-worktree` value in
the Git index. For each Git command, the retirement audit must remove
environment variables with the `GIT_` prefix. If the retirement audit cannot
examine a file or directory,
the retirement audit returns `FAIL` without a path.

After the retirement plan contains removal authority, operate the retirement
audit again. If the retirement audit gives a `FAIL` result, stop. After the
retirement audit gives a `PASS` result, use `git worktree remove` for the
worktree. Do not use `--force`. Do not use `git stash`. Do not move local files
as a condition for worktree removal.

Before worktree removal, make sure the local-state inventory contains all local
files. Before removal, make sure the preservation audit gives a `PASS` result
for each location for planned preservation.

After removal, examine `git worktree list`, branches, the stash inventory, and
the location for planned preservation again. Record the preservation diff in
phase evidence. If `git worktree list` does not contain the worktree, record
the local branch and branch tip in phase evidence. If the accepted commit
contains the branch tip for this local branch, use `git branch -d` with the
removal authority.

If the project owner gives no removal authority for the branch on GitHub,
do not remove a branch on GitHub. Do not use `git worktree prune`. During this
procedure, do not change a different worktree.

## Backup and restore acceptance

The independent backup is not ready until the project owner selects its
destination and the chosen versioned backup tool records a successful run.
Use:

```bash
.venv/bin/python tools/repository_safety_audit.py \
  --backup-target /path/to/mounted/backup \
  --require-backup-target
```

This proves only that the destination exists outside the repository on a
different mounted filesystem. It does not prove that any file has been copied,
that retention is working or that the destination is off-site.

At least monthly, restore into a new empty directory rather than over the live
checkout. The drill must verify:

- repository history and the expected HEAD;
- the Templot ZIP checksum;
- at least one ignored raw-evidence record;
- at least one representative FCStd opening in the qualified FreeCAD runtime;
  and
- a documented restore date, backup set and result without publishing private
  paths or credentials.

After the first successful drill, record only non-sensitive evidence in this
document or a linked dated report. A failed drill keeps backup readiness open.

The first repository-scope drill is recorded in
[2026-07-22-initial-repository-backup-restore.md](backup-records/2026-07-22-initial-repository-backup-restore.md).
Its remaining scope and acceptance conditions are controlling; the report does
not extend protection beyond the complete project-data scope declared by the
owner.

## Recovery after an abnormally interrupted export

When an abnormal asynchronous interruption leaves descriptor or advisory-lock
release uncertain in a surviving FreeCAD host, preserve every existing output
member and use this supported recovery procedure:

1. Do not alter or delete any existing DXF or manifest member.
2. Close FreeCAD completely.
3. Restart FreeCAD and reopen the project.
4. Inspect the destination through the normal TrackTemplate workflow.
5. Retry the export through the normal exporter.

Never manually delete, rename, replace or edit a partial pair merely to
recover. Closing FreeCAD restores the operating-system process boundary for
process-owned descriptors and advisory locks; it does not prove that a
destination member is regular, exact, complete or durable. The next invocation
must independently inspect and validate destination state before reporting
success or adding an absent exact counterpart.

TrackTemplate may complete an exact partial pair only through the accepted
[D-P6-003 add-only protocol](ARCHITECTURE.md#d-p6-003-cross-process-recovery-authority)
within the
[supported exporter failure model](ARCHITECTURE.md#supported-exporter-failure-model).
Restart-based containment never grants authority to delete, overwrite,
replace, rewrite, truncate, rename or otherwise mutate an existing output
member.

## Incident response

If files appear missing or corrupted, stop writing to the affected filesystem.
Do not immediately reset, clean, restore over the checkout or rerun generation.
Capture read-only Git status, filesystem and hash evidence; make a copy of the
remaining state; then restore to a new location from Git/GitHub or the verified
backup as appropriate. System rollback and personal/project-data restoration
remain separate operations.
