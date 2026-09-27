# Phase 8 Turnout, Crossover and Timbering Migration

Status: **Open — 0/4 evidenced exits under D-P8-001. All four exits are
Pending.**

Phase 7 closed on 2026-09-27 under
[D-P7-006](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-closeout-panel)
with all four original exits Evidenced and owner-accepted. Its
[evidence](../history/phase-closeouts/PHASE7_CLOSEOUT.md),
[decisions](../history/phase-closeouts/PHASE7_GATE_DECISIONS.json), and
[risk snapshot](../history/phase-closeouts/PHASE7_RISKS.json) are frozen.
The owner accepted the independently reviewed
[closeout recovery proof](../backup-records/2026-09-27-phase7-closeout-recovery.md).

## Current owner view

| Field | Current position |
| --- | --- |
| Current state | Phase 7 is closed at 4/4 under D-P7-006. Phase 8 is Open at 0/4 under D-P8-001. All four exits are Pending. D-P6-008 stays Deferred — unmet. Output stays private-development and project status stays `unknown`. |
| What changed | The owner opened Phase 8 for its four unchanged criteria. The completed Phase 7 evidence, decisions and risk snapshot remain frozen. PR #94 integrated that opening. A new independently reviewed snapshot covers the 39-worktree estate. D-GOV-020 authorises a bounded correction of the retirement control. |
| What now works | The four Phase 7 exit decisions keep their accepted bounded evidence. This opening changes no product behaviour. |
| Limitations/findings | All Phase 7 proof limits, B14/B15 identities, the inherited B15 host, the development-only comparison oracle, and every comparison, adapter, caller, removal and legacy-retirement condition remain. D-P6-008 remains mandatory before Phase 10 beta acceptance. Seven contained worktrees have ignored `.devtools/freecad-cli/` directory entries that the current audit does not support. D-GOV-020 does not resolve them. The USB is safely unmounted. Separate physical storage remains operator-controlled and unverified. |
| Owner decision | D-P8-001 opens Phase 8 at 0/4 and authorises the later internal `turnout_valid_toe_range` slice only after its retirement prerequisites. D-GOV-020 authorises only the bounded retirement-control correction and its exact-green integration. Neither decision accepts an exit, performance, wider migration, production output, release or legacy removal. |
| Next action | Integrate only an exact-green D-GOV-020 correction. Then get a separate passing plan and audit for each retirement candidate. Remove only safe candidates without `--force`, and check preservation after each removal. Keep five branches with unmerged commits. The product slice remains stopped until the retirement prerequisite is complete. Physical USB storage remains unverified. |

<a id="phase-8-opening-panel"></a>

## Phase 8 opening panel — 2026-09-27

**Decision boundary:** D-P8-001 opens Phase 8 at 0/4. All four original exits
remain Pending. The [accepted plan revision](https://github.com/Richard-Gnitnub/tracktemplate/blob/d5a3db45ab68a192e3d37f9fad5deb9f66f7de81/reference/PROJECT_PLAN.md#L934-L953)
owns their unchanged text. This Level 3 alignment changes phase authority, not
product behaviour. Project status stays `unknown` and output stays
private-development.

The assessed source was clean protected `main` at
`3fed822b25b2288370e586f14334d5a16e6065d2` after Phase 7 closeout.
The independent read-only reviewer `/root/phase8_opening_panel` examined the
opening boundary and all 24 live risks. The reviewer authored no maintained
file. The recommendation was **Proceed with bounded conditions**: keep the
first slice internal and development-only, keep TERM-R04 open, and change no
risk disposition. The earlier `/root/phase8_opening_review` also gave a
conditional PASS for that terminology boundary. These are agent-team reviews,
not external organisational reviews.

The first product assignment is one bounded Level 2 extraction of
`turnout_valid_toe_range` and checked routing for five inherited B15 callers.
The first slice starts only after the opening PR is merged into protected
`main` and protected `main` is clean and synchronised. It also needs the required retirement audit and removal of redundant
worktrees and branches in the JetBrains IDE. A new snapshot must preserve earlier snapshots and meet the
[recovery policy](../RECOVERY_AND_BACKUP.md) before product mutation. A recovery step needs operator access if the independent destination
is unavailable remotely. This opening does not claim
that the snapshot or removal is complete.

TERM-R04 remains open. The first slice must not add a public turnout API,
schema or UI term. The frozen B14/B15 identities, inherited B15 host, and
development-only comparison oracle remain. Per-slice comparison, adapter,
caller, removal and legacy-retirement conditions remain. The product draft
requires a separate integration decision.

**Exact owner instruction — 2026-09-27:**

> I open Phase 8 at 0/4 for its existing turnout, crossover and timbering scope, preserving its four existing exit criteria unchanged.
> I authorise the directly dependent Level 3 opening alignment and exact-green protected-main integration. Once `main` is clean and synchronised, redundant worktrees and branches are disposed of in the jetbrains ide, I authorise one bounded Level 2 internal, development-only `turnout_valid_toe_range` extraction and checked routing of its five inherited B15 callers through the normal TrackTemplate workflow to one exact-green draft PR.
> Keep TERM-R04 open. Introduce no new public turnout API, schema or UI term.
> Preserve D-P6-008, frozen B14/B15 identities, the inherited B15 host, development-only oracle, all existing risk and recovery duties, and every comparison, adapter, caller, removal and legacy-retirement condition.
> This accepts no Phase 8 exit, performance result, wider migration, production output, release or legacy removal. Project status remains `unknown`.
> Do not merge the product draft. Report any physical recovery action that requires operator access rather than assuming it occurred.

**Structured decision — D-P8-001:** Open Phase 8 at 0/4 for the four unchanged
criteria below. Authorise the directly dependent Level 3 records and
exact-green protected-main integration. After the stated prerequisites,
authorise only the bounded internal first product slice to an exact-green
draft PR. This decision admits no exit and changes no product behaviour.

**Exclusions:** D-P6-008 stays deferred and unmet. The 24 risk dispositions,
all proof limits, TERM-R04, both comparison identities, the inherited host,
and every comparison, adapter, caller, removal and legacy-retirement condition
remain. No performance result, wider migration, production output, release
state or legacy-path removal is accepted. Project status stays `unknown`.

<a id="worktree-retirement-control-panel"></a>

## D-GOV-020 worktree-retirement control panel — 2026-09-27

**Decision boundary:** Protected `main` at
`18dee347f4e1284bbd1a6e2b6f1658870064576e` contains the Phase 8 opening.
The separate pre-migration recovery snapshot covers 39 registered worktrees.
Its set is `2026-09-27-pre-phase8-turnout-migration-01`. The local receipt is
`tmp/phase8-pre-migration-recovery/terminal-backup-receipt.json` in the
primary checkout. Its SHA-256 is
`1d68bd0c9bfd2006c078cfb9964a6db579ff0a2a63782b2a5fd8739147eb1c8f`.
The snapshot has exact comparison evidence and independent recovery review.

It does not prove coverage of later worktrees. The USB is unmounted. Physical
removal and separate storage remain unverified.

The independent read-only reviewer `/root/retirement_governance_audit`
examined the existing retirement control, its two evidenced gaps, and all 24
live risks. The reviewer changed no maintained file. The panel result was
**Proceed with bounded conditions**. PR-13 remains Critical and PR-22 remains
High. Their treatment, owners, deadlines and control effectiveness do not
change. This is an agent-team review, not an external organisational review.

The correction permits symbolic links with exact preservation only as retained
evidence or authoritative local source. It permits a worktree without a branch
only when its exact HEAD is contained in the accepted commit. Classification,
preservation, exact identity, tracked cleanliness and activity checks remain.
An unsafe or ambiguous state still stops retirement. A separate passing plan
and audit are necessary for each candidate before non-force removal.

Preserve the five branches with unmerged commits. Do not start the authorised product
slice until the complete retirement prerequisite passes. The reviewer found
no basis to change a live risk disposition. The removal result and physical
USB storage state remain unknown at this decision.

A later read-only estate scan found seven contained worktrees with ignored
`.devtools/freecad-cli/` directory entries. The audit does not support those
entries. D-GOV-020 does not authorise another control change or their
retirement.

**Exact owner instruction — 2026-09-27:**

> As TrackTemplate project owner, I authorise one bounded Level 3 recovery-control correction to the existing worktree-retirement mechanism.
>
> Support only the two evidenced gaps blocking the Phase 8 prerequisite:
>
> - exact-preserved symlink local-state entries;
> - the contained detached worktree.
>
> Preserve the existing fail-closed retirement model. Do not weaken accepted-history containment, tracked cleanliness, local-state classification, preservation proof, exact identity checks, ambiguous-state stops, non-force removal or post-removal preservation checks.
>
> Add proportionate negative coverage so unsafe, changed, unresolved or insufficiently preserved symlink state still fails, and detached state cannot pass unless its exact commit is proved contained and retirement is otherwise safe.
>
> Obtain applicable independent review and integrate only an exact-green recovery-control correction through the normal protected-main workflow.
>
> After integration, require a separate passing retirement plan and audit for each retirement candidate before non-force removal. Preserve the five branches with unmerged commits; this authority does not permit their retirement or loss.
>
> Do not use `--force`, `git stash`, `git worktree prune` or destructive recovery shortcuts.
>
> Do not begin the authorised `turnout_valid_toe_range` product slice until the Phase 8 retirement prerequisite is genuinely complete under the corrected control and all remaining recovery-policy conditions are satisfied.
>
> The USB is safely unmounted. Do not claim physical removal or separate storage unless an on-site operator confirms it.
>
> Phase 8 remains 0/4 with all exits Pending. D-P6-008 and all existing limitations remain unchanged.

**Structured decision — D-GOV-020:** Authorise only the two evidenced
retirement-control corrections, negative tests, independent review and
exact-green integration. Each removal needs its own passing plan and audit.
No product, phase exit, performance, output, release or physical-storage
acceptance follows.

## Phase 8 exit conditions

These four criteria are unchanged from accepted plan revision
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`. Each status is Pending.

| Exit condition | Status | Evidence |
| --- | --- | --- |
| Turnouts and crossovers retain accepted geometry, topology, timber decisions, identities, findings, and production records. | Pending | No Phase 8 exit admission. |
| Creation, parameter editing, selection, undo/redo, save/reopen, validation, and export pass in the real GUI. | Pending | No Phase 8 exit admission. |
| Straight- and curved-host representative workflows pass deterministic comparison. | Pending | No Phase 8 exit admission. |
| No special-trackwork rule has leaked into the renderer or FreeCAD persistence adapter. | Pending | No Phase 8 exit admission. |

## Continuing duties and risks

[D-P6-008](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-4-deferral-panel)
stays in full in the [current decision register](gate-decisions.json). The
unchanged bounded Entry/Exit improvement obligation is mandatory before
Phase 10 beta acceptance. Richard keeps accountability and owns delivery until
a named Phase 10 integration owner takes responsibility. Independent review
and Richard's acceptance remain mandatory. Improvement on another workload
cannot satisfy this obligation. If it remains unmet, beta acceptance is
blocked.

The 24 [live risks](risks.json) retain their owners, deadlines, treatment and
control effectiveness. PR-13 keeps the backup and restore cadence. PR-10 and
PR-18 keep the duplication and removal gates. PR-09 keeps private-development
output. PR-15 and QA-R04 keep the D-P6-008 duty. PR-17, PR-01, QA-R03 and
PR-22 retain their recorded duties. No risk disposition changes.

The Phase 7 product evidence remains bounded by its accepted conditions.
Normal per-slice comparison, dependency and recovery checks remain mandatory
for later changes. No wider migration-family completion, untested platform
arrangement, performance result, production output, release or legacy-path
removal is accepted. Project status remains `unknown`.

## Preserved historical links

The following anchors keep frozen links navigable. Each link identifies the
historical record that now owns the evidence.

<a id="phase-7-opening-panel"></a>
[Phase 7 opening](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-opening-panel).

<a id="phase-7-exit-1-admission-panel"></a>
[Phase 7 Exit 1](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-exit-1-admission-panel).

<a id="phase-7-exit-2-admission-panel"></a>
[Phase 7 Exit 2](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-exit-2-admission-panel).

<a id="phase-7-exit-3-admission-panel"></a>
[Phase 7 Exit 3](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-exit-3-admission-panel).

<a id="phase-7-exit-4-admission-panel"></a>
[Phase 7 Exit 4](../history/phase-closeouts/PHASE7_CLOSEOUT.md#phase-7-exit-4-admission-panel).

<a id="freecad-1-1-3-py31315-qt6112-qualification-panel"></a>
[D-GOV-019 host qualification](../history/phase-closeouts/PHASE7_CLOSEOUT.md#freecad-1-1-3-py31315-qt6112-qualification-panel).

<a id="visible-recovery-state-workflow-migration"></a>
[Historical recovery workflow](../history/phase-closeouts/PHASE6_CLOSEOUT.md#visible-recovery-state-workflow-migration).

<a id="worktree-retirement-workflow-migration"></a>
[Historical worktree retirement workflow](../history/phase-closeouts/PHASE6_CLOSEOUT.md#worktree-retirement-workflow-migration).

<a id="phase-6-exporter-fault-model-clarification-panel"></a>
[Historical D-P6-004 decision](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exporter-fault-model-clarification-panel).

<a id="tt-doc-001-documentation-architecture-panel"></a>
[Historical TT-DOC-001 decision](../history/phase-closeouts/PHASE6_CLOSEOUT.md#tt-doc-001-documentation-architecture-panel).
