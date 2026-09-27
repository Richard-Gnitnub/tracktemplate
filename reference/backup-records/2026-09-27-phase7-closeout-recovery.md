# Phase 7 Closeout Recovery Record

Status: **The snapshot and independent recovery review gave PASS. The project
owner accepted this evidence on 2026-09-27 under D-P7-006.**

## Scope and result

This record keeps the Phase 7 closeout recovery result under
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). The source was clean
protected `main` at `53669f3010957601e79fd2d0d73a6f9b9f3893ec`.
The live Git register contained 37 worktrees, including the primary checkout
and two sibling directories outside the usual worktree directory. The source
had no uncommitted or stashed content. The snapshot included tracked source,
Git state, ignored Phase 7 proof, FreeCAD documents, and the Templot archive.

The new set is `2026-09-27-phase7-closeout-recovery-01` on the approved
independent ext4 USB. Its device identity is
`34968419-c112-4f00-9955-cb3b8a5a5d2e`. The operation preserved 64 older
destination entries. It did not overwrite an earlier snapshot.

| Check | Result |
| --- | --- |
| Exact scope | The snapshot covers all 37 registered worktrees. It contains 42,282 entries, including 36,162 regular files with a total of 2,260,602,748 bytes. |
| Source and snapshot | The before, after, final, and snapshot manifests identified the same entries. The source manifest SHA-256 is `8f161dcb8e5662dc70f964ee07b4a663cde6ea2f16cc455a667d89b36fbd8df1`. |
| Copy verification | Each of the 37 exact file comparisons returned zero and found no difference. The Git and stash states stayed unchanged. |
| Proof copy | The agent copied and verified 190 evidence files on the USB. The core evidence manifest SHA-256 is `dbfa332a84d565c2d77bc82c1485582d59432f0a7e8cdb7df29bd75212b5bbe4`. |
| Retention | The agent preserved 64 older destination entries and all existing snapshots. |
| Terminal state | The agent flushed the new set and safely unmounted `/dev/sda1`. A later check found no mountpoint. |
| Independent review | A reviewer who made no maintained change checked the exact scope, copy, prior-set preservation, restore basis, and terminal state. Both review stages gave PASS. |

The operation excluded only rebuildable virtual environments, Python bytecode
and caches, and the active recovery task directory. The separately copied
proof files contain that directory's completed evidence. No valuable Phase 7
proof was excluded from the declared scope.

## Restore basis and limits

The owner-accepted 2026-09-05 [full restore drill](2026-09-05-phase6-closeout-recovery.md)
was 22 days old. It remained within the monthly interval in the recovery
policy. The new exact snapshot used the same repository-worktree mechanism and
data classes. The independent reviewer found no changed recovery method that
required another drill at this boundary. **No 37-worktree restore was
performed.** The monthly and Phase 11 restore duties remain.

The exact local evidence is in `tmp/phase7-closeout-recovery` in the primary
checkout. The comparison receipt has SHA-256
`bb9fbe0e3b30cc640ae772f22ea0b160b5323c4be7329885e62a726902e21cd9`.
The terminal receipt has SHA-256
`cd5ddc7eb747c533a341e94f477b5da4c33c79d78cb3ee8b8ec5c1f38800f49a`.
The independent pre-terminal review has SHA-256
`af2a9c485dbe848fb6d7662d38713ddc8b3a0cf1246bfe15b237ea80fe2b314a`.
The independent terminal review has SHA-256
`9348ca5ba7540ad8d48ee37d0bfca700c2c8c0cf7dc6c7f83d3ff20e734a66de`.

The safe unmount does not prove that the USB is stored away from the computer.
Physical storage remains an operator action. The snapshot does not include
the later closeout alignment or its worktree. The recovery schedule applies
to those later records. This result changes no risk disposition, product
behaviour, performance claim, output status, release status, or D-P6-008 duty.
