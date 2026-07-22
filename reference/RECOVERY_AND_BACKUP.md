# Recovery and Backup Policy

Status: **active project-control policy adopted on 2026-07-22. Timeshift is
configured for scheduled system snapshots but a recent snapshot/restore has
not been verified; tracked-source recovery and repository safety checks are
active; an independent project-data backup remains blocked until an external
destination is selected.**

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
| Independent project-data backup | **Not configured — owner action required** | No separate external disk or other destination is currently mounted or accepted |
| Restore drill | **Not yet performed** | Must follow configuration of the independent data backup |

## Owner decision and temporary risk

On 2026-07-22 the project owner confirmed that no separate storage device is
currently available, intends to purchase one, and authorised development to
continue meanwhile. This is an accepted temporary operational risk, not a
positive backup or restore result. The audit must continue to report the
independent target, completed backup and restore drill as open.

Until the risk closes:

- establish and push a clean Git checkpoint before each risky tranche;
- do not perform an exceptional destructive action against project or operator
  data;
- keep automation on copied/disposable FCStd inputs;
- avoid accumulating a sole irreplaceable result under an ignored path; and
- review this gap at every phase closeout and close it before Phase 4 document
  migration work or any earlier operation that could affect the sole copy of
  an operator document.

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

## Incident response

If files appear missing or corrupted, stop writing to the affected filesystem.
Do not immediately reset, clean, restore over the checkout or rerun generation.
Capture read-only Git status, filesystem and hash evidence; make a copy of the
remaining state; then restore to a new location from Git/GitHub or the verified
backup as appropriate. System rollback and personal/project-data restoration
remain separate operations.
