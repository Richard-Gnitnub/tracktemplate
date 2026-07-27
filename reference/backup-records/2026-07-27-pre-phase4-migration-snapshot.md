# Phase 4 Pre-Migration Snapshot Record

Status: **the triggered, non-overwriting repository snapshot passed on
2026-07-27 before the disabled copied-target orchestration tranche.**

## Boundary

This is the non-sensitive repeat evidence required by
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). It captures the complete
declared repository scope at the clean, pushed checkpoint
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`, including `.git/`, ignored
evidence, FCStd fixtures and the retained Templot source archive. The backup-set
identifier is `2026-07-27-pre-phase4-migration-01`.

The destination was the owner-provided ext4 removable USB on a different
physical device. A new target directory was required; existing backup sets were
not overwritten or deleted. Disposable `.venv/`, `.idea/`, `.codex/`,
`__pycache__/` and `.pytest_cache/` paths were excluded under the accepted
policy.

## Snapshot evidence

| Check | Result |
| --- | --- |
| Destination audit | Passed: mounted, writable, outside the repository and on a different device |
| Repository safety | Passed at clean `main`, with `HEAD` equal to `origin/main` |
| Snapshot method | New complete dated tree populated with `rsync 3.2.7`; no deletion option |
| Snapshot inventory | 2,691 regular files and 574 directories; 3,265 entries |
| Incremental payload | 7,329,544 literal bytes transferred while unchanged files could hard-link to the prior successful dated set |
| Exact source comparison | Passed: checksum dry-run reported zero created, deleted or transferred files for the declared scope |
| Repository identity | Passed: backup `HEAD` exactly `d5a3db45ab68a192e3d37f9fad5deb9f66f7de81` |
| Source archive | Passed: SHA-256 `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Representative FCStd | Passed: SHA-256 `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` |
| Incremental retention | Passed: the source archive shared the same device/inode with the preceding complete `2026-07-22-control-closure-01` set |
| Durability | Passed: the completed set was flushed to its ext4 filesystem |

This triggered repeat does not replace the accepted empty-directory restore
drill or extend its scope. The monthly restore cadence and Phase 11 rehearsal
remain governed by [RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). The USB
remains a different-device copy rather than an off-site service.
