# Phase 5 Closeout Snapshot Record

Status: **the required new, non-overwriting repository snapshot passed on
2026-08-01 before any Phase 5 closeout status change was retained.**

## Boundary

This is the closeout-currency evidence required by
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md) and D-P5-003. It captures
the complete declared repository scope, including Git and ignored Phase 5 raw
evidence, from clean protected `main` merge commit
`054f6c91d6722c9011ecd5c52fe37088e4eb4f66`. The backup-set identifier is
`2026-08-01-phase5-closeout-01`.

The destination was the owner-provided ext4 removable USB on a different
physical device. A new target directory was required; existing backup sets
were not overwritten or deleted. Disposable `.venv/`, `.idea/`, `.codex/`,
`__pycache__/` and `.pytest_cache/` paths were excluded under the accepted
policy.

## Snapshot evidence

| Check | Result |
| --- | --- |
| Destination audit | Passed at the host boundary: mounted read/write, outside the repository and on a different physical device |
| Repository boundary | Passed: source and backup both retained clean `main` at exact commit `054f6c91d6722c9011ecd5c52fe37088e4eb4f66` |
| Snapshot method | New complete dated tree populated with `rsync 3.2.7`, using the accepted prior set as a hard-link source and no deletion option |
| Snapshot inventory | 4,778 regular files and 845 directories; 5,623 entries totalling 755,050,312 bytes |
| Transfer result | 2,269 regular files transferred; 11,032,931 literal bytes; zero destination deletions |
| Exact source comparison | Passed: a checksum dry-run reported zero created, deleted or transferred files for the declared scope |
| Source archive | Passed: source and backup SHA-256 `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Ignored Phase 5 raw evidence | Passed: the accepted interaction-range `performance.json` and backup both have SHA-256 `17404e205578bbffb19d9908aabeeaaa388650c365fdc8bed87c241b0b37e510` |
| Incremental retention | Passed: the source archive shares the same device and inode with the complete `2026-07-27-pre-phase4-family-support-01` set |
| Durability | Passed: the completed 737 MiB set was flushed and the USB safely unmounted |

The managed workspace projected the mounted USB as read-only, so the initial
in-sandbox destination audit could not prove writability. Device write
protection was off and the kernel reported an ext4 read/write mount. The same
unmodified safety audit passed at the explicitly authorised host boundary
before copying. This was an environment/profile limitation, not a backup
failure or a weakened destination check.

This closeout snapshot does not replace the accepted empty-directory restore
drill or extend its declared scope. The monthly restore cadence and Phase 11
rehearsal remain governed by
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). QA-R01 remains closed;
any missed cadence, failed later run or scope change must reopen it or create a
successor risk.
