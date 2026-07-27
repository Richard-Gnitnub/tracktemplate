# Phase 4 Pre-Support Snapshot Record

Status: **the triggered, non-overwriting repository snapshot passed on
2026-07-27 before exact-family support enablement.**

## Boundary

This is the non-sensitive repeat evidence required by
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). It captures the complete
declared repository scope before the support-enabling source mutation. The
snapshot retains repository `HEAD`
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81` and the exact accepted,
uncommitted disabled-orchestration tranche based on that clean pushed
checkpoint. The backup-set identifier is
`2026-07-27-pre-phase4-family-support-01`.

The destination was the owner-provided ext4 removable USB on a different
physical device. A new target directory was required; existing backup sets
were not overwritten or deleted. Disposable `.venv/`, `.idea/`, `.codex/`,
`__pycache__/` and `.pytest_cache/` paths were excluded under the accepted
policy.

## Snapshot evidence

| Check | Result |
| --- | --- |
| Destination audit | Passed at the host boundary: mounted read/write, outside the repository and on a different device |
| Repository boundary | Passed: backup `HEAD` is the clean pushed checkpoint above, and backup Git status exactly matched the reviewed pre-support working tree |
| Snapshot method | New complete dated tree populated with `rsync 3.2.7`; no deletion option |
| Snapshot inventory | 2,614 regular files and 574 directories; 3,188 entries totalling 745,127,377 bytes |
| Exact source comparison | Passed: checksum dry-run reported zero created, deleted or transferred files for the declared scope |
| Source archive | Passed: source and backup SHA-256 `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Immutable B14 oracle | Passed: source and backup SHA-256 `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| Incremental retention | Passed: the source archive shares the same device/inode with the preceding complete `2026-07-27-pre-phase4-migration-01` set |
| Durability | Passed: the completed set was flushed and the USB safely unmounted |

The managed workspace initially projected the mounted USB as read-only, so the
first in-sandbox destination audit reported `target-is-not-writable`. Device
write protection was off and the kernel reported an ext4 read/write mount. The
same unmodified safety audit then passed at the explicitly authorised host
boundary before copying. This was an environment/profile limitation, not a
backup failure or a weakened destination check.

This triggered repeat does not replace the accepted empty-directory restore
drill or extend its scope. The monthly restore cadence and Phase 11 rehearsal
remain governed by [RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). The USB
remains a different-device copy rather than an off-site service.
