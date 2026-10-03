# Phase 8 Closeout Recovery Record — 2026-10-03

The project owner accepted the bounded recovery evidence for the
[Phase 8 closeout](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-closeout-panel)
at protected `main` `cfd4387b9f61f425266448c1ace7d7fea3a889cf`.
This record identifies the scope of that acceptance. It does not change the
[recovery policy](../RECOVERY_AND_BACKUP.md).

The October 1 snapshot preserved all 41 then-registered worktrees. It
contained 64,407 entries and 4,434,264,142 bytes from regular files,
including 18 nested FreeCAD CLI repositories. Independent checks compared
the actual snapshot with those source roots. Disposable copies of all 23
retirement candidates had 19,512 matching entries. Their relevant nested
repository identities and `git fsck` checks passed. Each removal had a
passing individual plan, audit and post-removal check. Git used ordinary
`git worktree remove` for all 23. It used no `--force` operation and deleted
no branch. The 45 then-existing local branch tips remained the same.

The original snapshot, IDE and Ruff overlays, terminal retirement packet
and later record-worktree state have separate receipts. A further October 3
non-overwriting supplement `2026-10-03-phase8-closeout-evidence-01` on the
approved USB (filesystem UUID `34968419-c112-4f00-9955-cb3b8a5a5d2e`)
preserved 39 independently checked inputs,
including four review files totalling 193,012 bytes and the merge bundle.
The final assessment packet contained 113 independently checked entries.
Its copy, flush and safe unmount passed. The retained completion receipt is
`tmp/phase8-closeout-assessment-20261003/completion.json`; it was written
locally after unmount. Its `PASS` result binds the exact main commit and
identifies the independent review and preservation receipts by SHA-256.
The SHA-256 of `completion.json` is
`886018d9a4dd275a5a625a9109b3a7cff81cd1390f849589e40bb46d195f598a`.

The supplement is not a new complete 19-worktree snapshot. The October 1
candidate restores are not a monthly FreeCAD GUI restore. The last full
monthly restore is dated 2026-09-05; the next is due by **2026-10-05**.
Richard retains the independent-backup duty and the implementation/QA owner
retains enforcement of the recovery procedure. Weekly and accepted-tranche
snapshot triggers remain. The USB is a separate physical device but stays
attached to the machine. Separate physical storage and an off-machine copy
are not proved. The two intermediate Ruff-cache states for retirements
r13/r14 remain unavailable; later matching digests do not reconstruct them.
Earlier failed helper, restore, review and product results remain failed
evidence. IDE file and window data do not prove unsaved editor buffers or
the displayed branch indicator.

The later closeout authoring worktree and this record alignment are outside
the assessed 19-root estate. Their recovery treatment follows the continuing
policy cadence. This record does not claim that the October 3 supplement
contains files created after its final copy.

The transient assessment and independent-review records remain in the
ignored `tmp/phase8-closeout-assessment-20261003/` packet and its approved
USB supplement. The archived [Phase 8 evidence](../history/phase-closeouts/PHASE8_CLOSEOUT.md)
retains the decision, accepted proof boundaries and continuing risks.
