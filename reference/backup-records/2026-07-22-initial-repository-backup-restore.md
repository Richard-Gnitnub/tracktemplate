# Initial Repository Backup and Restore Record

Status: **repository-scope backup and restore passed and was accepted by the
project owner on 2026-07-22. The owner confirmed that the repository contains
all valuable project files, accepted the repeat/retention routine below, and
its second-snapshot proof passed. QA-R01 closed on 2026-07-22.**

## Boundary

This record is the non-sensitive evidence required by
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). It covers the complete
repository checkout at the time of the snapshot, including `.git/`, ignored
benchmark evidence, ignored FCStd fixtures and the retained Templot source
archive. On 2026-07-22 the project owner confirmed that all valuable project
files are inside the repository and that no external project files require
backup. The declared valuable project-data scope is therefore complete.

The destination was an owner-provided ext4 removable USB device on a different
physical device from the repository. The dated backup-set identifier is
`2026-07-22-initial`. Existing destination content was preserved; the copy
reported zero deletions. Private mount paths and unrelated destination content
are deliberately not recorded here.

Disposable `.venv/`, IDE metadata, bytecode caches, pytest caches and agent
workspace metadata were excluded. No path was excluded merely because Git
ignored it.

## Backup evidence

| Check | Result |
| --- | --- |
| Destination location audit | Passed: existing, writable directory outside the repository on a different device |
| Snapshot method | New non-overwriting dated directory populated with `rsync 3.2.7`; no `--delete` option |
| Snapshot contents | 2,213 regular files in 516 directories; 739.39 MB reported logical file size |
| Repository state captured | `main` at `4a908c74dda05316361a3615b2725d99dc818a98`, tracking `origin/main`, including the 17-entry uncommitted Phase 4 working state |
| Source archive | Present with accepted SHA-256 `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Ignored evidence | 1,077 files below `benchmark-output/` were present in the restored snapshot |

## Restore drill

The entire repository snapshot was restored from the USB into a new empty
temporary directory, never over the live checkout.

| Check | Result |
| --- | --- |
| Snapshot-to-restore comparison | Passed: recursive byte comparison reported no differences |
| Git history | Passed: restored HEAD exactly `4a908c74dda05316361a3615b2725d99dc818a98` |
| Working state | Passed: restored branch/upstream and all 17 modified/untracked entries matched the captured state |
| Templot archive | Passed: restored SHA-256 matched the accepted value above |
| Representative ignored evidence | Passed: restored `b14-default-base-regenerated.manifest.json` SHA-256 `da112bbcb3e1042bbf2413c39b28e5970138b0c1618755b9b081e474b7f5d20c` |
| Representative FCStd | Passed: restored fixture SHA-256 `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` opened read-only in FreeCAD 1.1.1 as a nine-object document |

FreeCAD emitted the sentinel
`USB_RESTORE_FCSTD_OPEN_OK version=1.1.1 ... objects=9`. The restored fixture
was copied into the ignored evidence area only because the Flatpak runtime
cannot see the host temporary directory; both copies had the same SHA-256
before it was opened.

Project-owner decision: **Accepted 2026-07-22.** The owner accepted that the
files in this repository-scope backup set were successfully backed up on the
USB device and subsequently confirmed that all valuable project files are
inside the repository, with no external project files requiring backup.

## Repeat and retention proof

This first drill proves different-device recovery for the complete declared
valuable project-data scope. On 2026-07-22 the project owner accepted this
repeat/retention routine:

- create a new dated snapshot before risky migration work and after an
  accepted tranche that adds valuable local evidence;
- create at least one successful snapshot per active development week;
- retain the initial accepted set plus at least four recent successful sets;
- never delete snapshots automatically; and
- perform a restore drill at least monthly and again at the Phase 11 gate.

The second non-overwriting snapshot proof passed on 2026-07-22 with backup-set
identifier `2026-07-22-routine-proof-01`:

| Check | Result |
| --- | --- |
| Non-overwriting boundary | Passed: the new target was required to be absent; zero files were deleted and the initial set was used read-only as the hard-link source |
| Complete dated tree | Passed: 2,214 regular files in 517 directories; 739.40 MB reported logical file size |
| Changed payload | Seven regular files transferred; 257.14 KB literal data |
| Incremental retention | Passed: the accepted source archive shared the same device/inode across both sets; the second complete tree consumed 2.3 MB additional allocated storage when measured with the initial set |
| Exact current-source comparison | Passed: checksum dry-run reported no difference for the declared backup scope |
| Repository identity | Passed: repeated snapshot HEAD exactly `4a908c74dda05316361a3615b2725d99dc818a98` |
| Source archive | Passed: both sets retained accepted SHA-256 `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Durability | Passed: the repeated set was flushed to its ext4 filesystem before completion |

**QA-R01 closure: Closed 2026-07-22.** The owner-confirmed complete scope,
successful backup and restore, accepted cadence, non-automatic retention rule
and verified repeat snapshot satisfy its Phase 4 prerequisite. PR-13 remains a
permanent principal risk under the active controls and later rehearsal gates.

The USB is a different-device copy, not an off-site service. It should be
unmounted and stored separately from the computer between backup runs.
