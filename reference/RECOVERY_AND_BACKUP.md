# Recovery and Backup Policy

Status: **active project-control policy adopted on 2026-07-22. Timeshift is
configured for scheduled system snapshots but a recent snapshot/restore has
not been verified; tracked-source recovery and repository safety checks are
active; an ext4 removable USB destination on a separate physical device has a
passed initial repository snapshot and restore drill, accepted by the project
owner on 2026-07-22. The owner confirmed that all valuable project files are
inside the repository and no external project files require backup, and
accepted the repeat/retention routine. Its incremental second-snapshot proof
passed, closing QA-R01 on 2026-07-22. The ongoing cadence remains mandatory.**

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
| GitHub `main` | Active and verified 2026-07-22 | Normal fast-forward pushes remain allowed; administrator enforcement is active; force pushes and branch deletion are blocked; pull requests and status checks are not yet required |
| GitHub remote history | Active | Off-machine copy of pushed Git objects; not a complete backup of ignored assets and not independent of account/repository administration |
| Independent project-data backup | **Operational for the complete declared project-data scope** | A dated, non-overwriting snapshot on a separate ext4 USB covers `.git`, ignored evidence, repository FCStd fixtures and the source archive; the owner confirmed no valuable external project files require backup |
| Restore drill | **Passed and owner-accepted for the complete declared scope on 2026-07-22** | See the [backup, restore and repeat record](backup-records/2026-07-22-initial-repository-backup-restore.md) |
| Repeat and retention | **Active and verified 2026-07-22** | The accepted cadence and hard-linked incremental retention were proved by a second complete snapshot; QA-R01 is closed |

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
valuable project files outside the repository require backup. Retention is
now represented by two complete dated sets. The owner accepted the repeat/
retention routine below on 2026-07-22, and its incremental second-snapshot
proof passed exact comparison while adding only changed payload storage. The
audit may therefore report QA-R01 closed for the current declared scope; a
missed cadence, failed run or scope change must reopen the exposure rather than
rely on this historical result.

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

## Incident response

If files appear missing or corrupted, stop writing to the affected filesystem.
Do not immediately reset, clean, restore over the checkout or rerun generation.
Capture read-only Git status, filesystem and hash evidence; make a copy of the
remaining state; then restore to a new location from Git/GitHub or the verified
backup as appropriate. System rollback and personal/project-data restoration
remain separate operations.
