# Phase 6 Closeout Recovery Record

Status: **The independent review of the recovery evidence gave PASS.
The owner accepted the evidence on 2026-09-05 under D-P6-009.**

## Accepted scope and source

This record preserves the completed closeout prerequisite under
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md).
It records an existing result. The closeout alignment did not repeat the
backup, restore drill, product experiment, or performance experiment.

The source is clean protected `main`
`8df4c6c2df9bd89d6d13a30929549b472b0c4b2d`.
The declared scope includes the primary checkout and all five other worktrees
with valuable evidence. It includes common Git history, tracked source, ignored evidence with PASS and
FAIL results, FCStd fixtures, the Templot archive, IDE state, and local records.

| Other worktree | Preserved HEAD |
| --- | --- |
| `dgov011-negative-result-alignment` | `34197b1db7a0605e2ae1c043ee13d4c6048417d6` |
| `phase6-entry-exit-output-equivalence` | `bec649dff77c3889e186980c0bd3190f5a8c85b5` |
| `phase6-exit1-owner-acceptance` | `89ab7ee6f6444456f26928fd0abf66e049df78f5` |
| `phase6-exit5-owner-acceptance` | `a9308b37a2d70bd489ff2496dde194d70fed995a` |
| `phase6-exit4-deferral` | `f557ece2bc0ad9dd54a1e6247ed39a50e67d53ee` |

The backup does not include rebuildable `.venv`, `__pycache__`,
`.pytest_cache`, `.ruff_cache`, `.pyc`, and `.pyo` content. These are its only
cache exclusions. The implementing agent copied the recovery task directory
as a separate group of evidence files.

## Snapshot and restore evidence

The new set is `2026-09-05-phase6-closeout-recovery-01`.
It is on the approved USB, on a different physical device from the source.
The copy did not overwrite an earlier set.
The destination is ext4 on `/dev/sda1`. The source is on `/dev/nvme0n1p2`.
The implementing agent preserved existing snapshots, evidence, and worktrees.

| Check | Completed result |
| --- | --- |
| Snapshot method | `rsync 3.2.7 -aH`, with no deletion, in-place writing, or hard-link source option |
| Complete scope | 12,417 entries, 10,544 regular files, 881,976,461 bytes in regular files |
| Other worktree coverage | 2,159 regular files, 77,992,408 bytes across the five other roots |
| Source stability and snapshot | Before, after, and final source manifests were equal to the complete snapshot manifest. No destination deletion occurred. |
| Disposable restore | The complete six-root restore had the same bytes, modes, and symbolic-link targets as the snapshot. The agent then moved the copied Git pointers. The checksum dry-run showed no differences. |
| Git recovery | The checks of all six restored heads, refs, common Git ownership, and tracked clean states gave PASS. `git fsck` found no missing or corrupt object. Its 122 dangling-object notices gave information only. |
| Copied Git relocation | Only ten copied administrative pointer files changed. The agent kept preimages and final hashes. The agent registered no restored worktree in live Git. |
| FCStd recovery | The qualified FreeCAD 1.1.3 profile opened the copied fixture with nine expected objects. The process returned zero and the success sentinel. No save, recompute, or product generation occurred. |
| Independent review | `/root/alignment_review` checked the manifests, representative files, complete USB evidence copy, and preservation results. The result was PASS. |
| Terminal preservation | The agent flushed the set. `udisksctl` safely unmounted `/dev/sda1`. `findmnt` and `lsblk` showed no mountpoint. Completion time was `2026-09-05T17:56:44Z`. |

The local receipts give the exact path of the disposable restore.
Two original symbolic links for test fixtures keep their exact target text.
The drill did not follow those links into live evidence.

The exact qualified profile was
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The FCStd check returned:

```text
USB_RESTORE_FCSTD_OPEN_OK version=1.1.3 objects=9 sha256_before=0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c sha256_after=0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c
```

## Evidence identities and limits

The original local evidence directory is
`tmp/phase6-closeout-recovery` in the primary checkout.
The USB evidence copy contains 37 files and 22,807,060 bytes.
The implementing agent copied the copy receipt and independent review to the USB.
The agent compared each copy with its source before flush and unmount.
The agent recorded the terminal receipt locally after unmount.
The USB copy does not include that receipt.

| Evidence item | SHA-256 |
| --- | --- |
| Source-before manifest | `2ec2889bb374ef152fe6eacb8510589c57dda4578d8ae279304cb96d26f66146` |
| Core proof manifest | `7e1a8b253a3a7e7600095b972ed667049480c6ea339238464bb0808adbe14e60` |
| `core-evidence-copy.json` | `fa0070c38aee0c508ced44eeefa5937aaf0ec15dc6bf840d17fe4d4490467e0a` |
| `independent-final-review.md` | `b96f7d07e84600cffe7015428534725d2e56016d858ffdff7abf04b396f2571b` |
| `terminal-recovery-receipt.json` | `b3352308371f20ecbc5459758ea2569430092e077c982c4ff7e7adcba15dc609` |
| Retained D-GOV-011 negative result | `0bcd0cc7e02c86e77fd2fd31893fe0f2c9b8476928bb01901d1c6fded6683bb8` |
| Templot source archive | `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |

This result resolves the dated PR-13 scope and currency exposure for the six
declared roots. PR-13 stays open with its existing backup schedule and
Phase 11 duties. Historical QA-R01 closure is unchanged.

This result gives no evidence about the unrecorded past backup schedule or
data outside the six declared roots. It does not show physical off-site storage.
The operator must store the USB away from the computer.

The snapshot does not include later closeout records. The existing backup
procedure applies to those records. Recovery validation gives no performance,
phase-opening, production, or release acceptance.
