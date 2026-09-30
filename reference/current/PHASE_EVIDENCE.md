# Phase 8 Turnout, Crossover and Timbering Migration

Status: **Open — 1/4 evidenced exits under D-P8-002. Exit 3 is Evidenced
and owner-accepted. Exits 1, 2 and 4 stay Pending.**

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
| Current state | Phase 7 is closed at 4/4 under D-P7-006. Phase 8 is Open at 1/4 under D-P8-002. Exit 3 is Evidenced and owner-accepted. Exits 1, 2 and 4 stay Pending. D-P6-008 stays Deferred — unmet. Output stays private-development and project status stays `unknown`. |
| What changed | [D-P8-002](#phase-8-exit-3-admission-panel) records Exit 3 acceptance at `f1926b6`. The criterion and comparison limits stay unchanged. <br><br>The owner opened Phase 8 for its four unchanged criteria. The completed Phase 7 evidence, decisions and risk snapshot remain frozen. PR #94 integrated that opening. The retained independently reviewed snapshot covers the earlier 39-worktree estate. PR #95 integrated D-GOV-020 and PR #96 integrated D-GOV-021. <br><br>D-GOV-022 authorises one `git worktree remove --force` operation only if its conditions pass. An independent reviewer examined the 42-root snapshot and restore evidence for seven nested Git repositories. The 37 individual retirement audits gave PASS. Git removed 37 worktrees without `--force`. Git also deleted 36 branches whose tips the accepted commit contained. <br><br>PR #97 integrated D-GOV-022. A fresh six-root snapshot, restore test, individual audits and post-removal checks gave PASS. Git removed the two remaining D-GOV-022 worktrees without `--force`. The [preservation diff](#phase-8-worktree-retirement-result) records their retained branch tips. |
| What now works | The [Exit 3 panel](#phase-8-exit-3-admission-panel) identifies the accepted representative comparisons for straight and curved `TO-001` and `XO-001` workflows. <br><br>The four Phase 7 exit decisions keep their accepted bounded evidence. The Phase 8 candidate passed development-only calculation, caller and real-GUI range tests. |
| Limitations/findings | The [Exit 3 limits](#phase-8-exit-3-admission-panel) remain. TERM-R04 stays open. <br><br>All Phase 7 proof limits, B14/B15 identities, the inherited B15 host, the development-only comparison oracle, and every comparison, adapter, caller, removal and legacy-retirement condition remain. D-P6-008 remains mandatory before Phase 10 beta acceptance. <br><br>The earlier test used a Git repository that the Git ignore rule did not select. Its removal without `--force` failed. An independent reviewer examined the 42-root snapshot and restore test. Each of the seven parent worktrees had a passing retirement plan and audit. Git removed all seven without `--force`.<br><br>After removal, each preservation check gave PASS. The D-GOV-022 authority remains unused. Five branches with unmerged commits and three related worktrees remain. The two D-GOV-022 worktrees are retired. Four worktrees remained at that retirement boundary. All eight prior branch refs, including both retired-worktree refs, remain.<br><br>The USB is safely unmounted. Physical removal and separate storage remain unverified. |
| Owner decision | [D-P8-002](#phase-8-exit-3-admission-panel) accepts Exit 3 only. It authorises integration after independent acceptance and successful checks for the exact candidate. <br><br>D-P8-001 opens Phase 8 at 0/4 and authorises the later internal `turnout_valid_toe_range` slice only after its retirement prerequisites. D-GOV-020 and D-GOV-021 remain the integrated exact-state controls. D-GOV-022 authorises one `git worktree remove --force` operation only if every condition in the decision passes. No current worktree meets these conditions. The earlier D-P8-001 and D-GOV-020–022 decisions accept no Phase 8 exit, performance, wider migration, production output, release or legacy removal. |
| Next action | Integrate the Exit 3 alignment after independent acceptance and successful checks for the exact candidate. Verify clean, synchronised protected `main`. Then examine the next Phase 8 boundary. Present a bounded owner decision if another exit is ready. Otherwise, identify the evidence gap and the work needed to close it. |

<a id="phase-8-exit-3-admission-panel"></a>

## Phase 8 Exit 3 admission panel — 2026-09-30

**Decision:** D-P8-002 accepts Exit 3 only at protected `main`
`f1926b6e9e123920076ed988f8baa3e8b8ce7b63`. Phase 8 is Open at 1/4.
Exits 1, 2 and 4 stay Pending. The criterion stays unchanged:

> Straight- and curved-host representative workflows pass deterministic comparison.

The decision covers the reviewed representative `TO-001` and `XO-001`
comparisons on straight and curved hosts. This Level 3 change records the
owner decision. It changes no product behaviour. Its governance work exceeds
implementation work because it changes phase-exit authority.

**Evidence reviewed:**

- [PR #120](https://github.com/Richard-Gnitnub/tracktemplate/pull/120)
  compares straight `TO-001` selected SVG and CSV output across B14, B15 and
  B16. Each version exports twice. All six compared results are equal after
  the stated normalisation. The qualified GUI proof retains the existing
  lifecycle checks and exercises the main export button.
- [PR #121](https://github.com/Richard-Gnitnub/tracktemplate/pull/121)
  supplies the corresponding straight `XO-001` comparisons. It retains the
  lifecycle checks and proves the highlighted-row GUI export route. The
  incompatible solid stays skipped.
- [PR #122](https://github.com/Richard-Gnitnub/tracktemplate/pull/122)
  compares Create, Edit, applicable `B4` results, stable geometry, identities,
  ordered production records and selected SVG/CSV routes for one curved
  fixture. The qualified headless proofs pass. Each route exports twice per
  version. The pull request records the prior GUI evidence and its limits.
- The earlier [straight turnout](#phase-8-straight-alignment-turnout-result),
  [straight crossover](#phase-8-straight-host-crossover-result),
  [straight B4](#phase-8-straight-crossover-b4-result),
  [analysis comparison](#phase-8-straight-crossover-b4-analysis-result) and
  [Edit evidence](#phase-8-straight-crossover-edit-result) retain their
  bounded results and failed evidence.

**Panel:** Richard is the project owner and decision chair. The implementing
agent presents the record alignment. The independent read-only QA/risk
reviewer `/root/admission_panel` examines the admission evidence and all 24
live risks. The reviewer authors no maintained file. This is an agent-team
review, not an external organisational review. Its recommendation is
**Proceed with bounded conditions** for Exit 3 only.

PR-01 and QA-R03 retain incomplete GUI coverage. PR-17 stays Critical, Open
and Partial. PR-09 retains private-development output. PR-10 and PR-18 keep
their comparison and removal conditions. PR-13 keeps its recovery duties.
PR-15 and QA-R04 keep D-P6-008. PR-22 keeps independent review and owner
acceptance. All risk owners, deadlines, dispositions and control effectiveness
remain unchanged. No risk closure follows from this admission.

**Limits and conditions:**

- The fixtures are representative. They do not prove every host or workflow.
  The straight `TO-001` comparison does not establish cross-version Edit
  parity. Its GUI handing edit is a separate proof.
- Historical GUI receipts support their recorded source states. PR #122
  identifies four receipts with later source changes. Complete current-source
  GUI coverage for both curved workflows remains absent.
- Wider persistence and runtime-profile coverage remain unproved. Stable
  save/reopen data does not prove raw shape-byte identity.
- The older curved `B4` digest differences remain unattributed. The later
  complete-data comparison excludes only `performance_timings_ms` and does
  not explain those older differences.
- Raw GUI/headless output identity remains unproved. The straight exports
  retain different SVG stroke attributes and manifest filename digests.
  Compared geometry does not establish byte or style identity.
- All retained failures, diagnostics, deferred clearance findings and
  non-production limits remain. Production readiness does not follow.

D-P6-008 stays Deferred — unmet and mandatory before Phase 10 beta acceptance.
TERM-R04 stays open. Output stays private-development and project status stays
`unknown`. Frozen B14/B15 identities, the inherited B15 host and the
development-only comparison oracle remain. Every comparison, adapter, caller,
removal and legacy-retirement condition remains. This decision accepts no
performance result, wider migration, production clearance, phase closure or
release.

The dated entries below retain their original status at each evidence boundary.
The earlier `Editing XO-001` finding does not remain an unresolved product
change: [PR #118](https://github.com/Richard-Gnitnub/tracktemplate/pull/118)
contains its independently reviewed correction and straight and curved GUI
proof. That correction alone does not accept Exit 2.

**Exact owner instruction — 2026-09-30:**

> As TrackTemplate project owner, I accept Phase 8 Exit 3 against its unchanged criterion at protected-main "f1926b6", bounded to the reviewed straight- and curved-host TO-001/XO-001 comparison evidence.
>
> Preserve all recorded limitations, including the representative fixtures, straight TO edit coverage limit, historical GUI-source limits, wider persistence/profile limits, older unattributed digest differences and unproved raw GUI/headless output identity.
>
> Record the Exit 3 decision and complete the directly dependent repository alignment. If the exact candidate is independently accepted and exact-green, integrate it through the normal protected-main workflow without stopping for another mechanical merge decision.
>
> Phase 8 should then become "1/4" with Exits 1, 2 and 4 still Pending.
>
> Preserve D-P6-008 as Deferred — unmet, TERM-R04 as open, private-development output status, comparison conditions and all legacy-retirement conditions.
>
> Once protected "main" is clean and synchronised, continue directly to the next genuine repository-evidenced Phase 8 boundary.
>
> If another exit is already admission-ready, bring me only its bounded owner decision. If a genuine evidence gap remains, identify gap and work needed to close it.

**Resulting authority:** Integrate only the independently accepted candidate
with successful checks for its exact head through protected `main`. Then
verify that `main` is clean and synchronised. Examine the next Phase 8 boundary
without repeating sufficient Exit 3 evidence. Another exit needs its own
bounded owner decision. A remaining evidence gap needs an identified work
item and its applicable validation.

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

<a id="nested-freecad-retirement-control-panel"></a>

## D-GOV-021 nested FreeCAD retirement-control panel — 2026-09-27

**Decision boundary:** D-GOV-020 entered protected `main` at
`e74e70c2a736de07b50b847f141794efe68234f7`. The later read-only audit
found seven contained parent worktrees whose local-state inventories stop on
an ignored `.devtools/freecad-cli/` directory. Their nested Git HEAD is the
pinned `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`. Each has the six
modified files specified by the tracked `freecad-cli-tracktemplate.patch`
file. These files have exact approved blob identities and no staged or
additional changes. One nested HEAD is
detached. One contains an empty `__pycache__` directory, which the retained
snapshot explicitly excluded.

The seven Git repositories do not have identical metadata. The
read-only audit found no unique nested commit, stash, or unreachable object.
This does not by itself authorise a worktree removal.

The 39-worktree snapshot at
`2026-09-27-pre-phase8-turnout-migration-01` remains retained evidence.
It does not cover the later full registered-worktree estate or its complete
nested cache state. A new non-overwriting independent snapshot must include
the complete nested trees and current estate before any worktree removal.
The applicable restore evidence must cover the expanded exact-state scope.
The USB is unmounted. Physical removal or separate storage has not been
confirmed by an on-site operator.

The independent read-only Level 3 reviewer `/root/nested_governance_panel`
returned **Proceed with bounded conditions**. PR-13 remains
Critical/Open/Mitigate/Effective for current scope. PR-22 remains
High/Open/Remove/Effective for current scope. The reviewer changed no
maintained file or risk disposition. This is an agent-team review, not an
external organisational review.

The correction is limited to the exact `.devtools/freecad-cli/` development
repository. The audit must check its pinned Git identity, six approved file changes, index, references, and all local-only
state. The retirement plan must
classify its full state as authoritative local source or retained evidence
and prove an exact independent full-tree copy. Other nested directories stay
unsupported. Changed or unexplained state stops retirement.

Each candidate
still needs its own passing plan and audit, inactivity proof, non-force
removal, and post-removal preservation check. The five branches with unmerged
commits stay. A disposable proof found that the audit can PASS for a Git repository
with exact preservation. The plain `git worktree remove` refuses it as
modified or untracked and leaves the parent registered. This proof does not
remove a live candidate or authorise `--force`, `git stash`,
`git worktree prune`, or moving local files.

The non-force mechanical route needs a separate owner decision. No Phase 8 product work starts before the complete retirement
prerequisite passes.

**Exact owner instruction — 2026-09-27:**

> As TrackTemplate project owner, I authorise one bounded Level 3 recovery-control treatment for the seven contained retirement candidates whose local state includes populated `.devtools/freecad-cli/` nested Git checkouts.
>
> Do not treat a nested checkout as an ordinary directory or ordinary disposable file state.
>
> For each nested checkout, establish its exact Git identity and classify its complete state, including tracked modifications and local-only state. Determine whether that exact state is:
>
> - reproducible from the existing canonical FreeCAD CLI/toolchain authority;
> - already preserved independently;
> - retained evidence that requires exact preservation;
> - or unique/ambiguous state that prevents retirement.
>
> A nested checkout may permit its parent worktree to retire only when its complete relevant state is accounted for and either proven reproducible or independently preserved. Any unexplained or unique nested state must fail closed and leave that parent worktree registered.
>
> Keep this correction specific to the existing `.devtools/freecad-cli` development-tool case. Do not create a general recursive nested-repository framework unless current evidence proves that is unavoidable and return to me first if it does.
>
> Add negative coverage for changed identity, additional unaccounted modifications, incomplete nested inventory, failed preservation, mismatched approved patches, and other cases that could lose nested state.
>
> Preserve all existing worktree-retirement safeguards, including exact parent-worktree identity, accepted-history containment, tracked cleanliness, inactivity, local-state classification, non-force removal and post-removal preservation checks.
>
> Preserve the five branches with unmerged commits. This authority does not permit their loss or retirement.
>
> Before removing any worktree, obtain fresh independent backup coverage for the current estate and require its own passing retirement plan and audit. Remove only individually proved-safe candidates.
>
> Do not use `--force`, `git stash`, `git worktree prune` or destructive recovery shortcuts.
>
> After an exact-green independently reviewed control correction is integrated, complete only the authorised retirement prerequisite. Do not begin the `turnout_valid_toe_range` product slice until that prerequisite genuinely passes.
>
> The USB remains unmounted. Do not claim physical removal or separate storage without on-site operator confirmation.
>
> Phase 8 remains 0/4 with all exits Pending. D-P6-008 and all recorded limitations remain unchanged.

**Structured decision — D-GOV-021:** Authorise only the seven-candidate,
exact-path nested FreeCAD retirement-control treatment, negative tests,
independent review, and exact-green integration. This decision gives no
removal authority without fresh current-estate backup and a separate passing
plan and audit for each worktree. It accepts no product, exit, performance,
output, release, physical-storage, or legacy-removal result. Phase 8 stays
Open at 0/4. D-P6-008 and all recorded limitations remain.

<a id="nested-freecad-mechanical-exception-panel"></a>

## D-GOV-022 nested FreeCAD mechanical exception panel — 2026-09-27

**Decision boundary:** PR #96 integrated the D-GOV-021 exact-state control at
`37421762af74ea12971e240707c7b170dec32a57`. The retained test refusal applies to a Git repository that the Git ignore rule did not select. It does not show a refusal for the seven worktrees with Git repositories under `/.devtools/`. In a separate test with the live ignore rule and six changed nested files, `git worktree remove` removed the temporary worktree. Other ignored state was also present.

The test changed no live worktree. At this decision, the seven parent worktrees had no tracked changes or untracked files that the Git ignore rule did not select. Before retirement, they still needed a fresh independent snapshot, restore evidence, and individual passing retirement plans and audits.

**Risk panel:** PR-13 remains Critical/Open/Mitigate/Effective for current
scope. A force operation could lose local evidence if any preservation or
identity check is bypassed. PR-22 remains High/Open/Remove/Effective for
current scope. D-GOV-022 supplies authority only after independent recovery review and a separate test for the target. The usual removal procedure does not use `--force`. No risk disposition changes.

**Exact owner instruction — 2026-09-27:**

> As TrackTemplate project owner, I authorise one bounded Level 3 exception to the normal non-force worktree-retirement rule for the proved `.devtools/freecad-cli/` nested-checkout case.
>
> This exception applies only when:
>
> - a fresh non-overwriting independent backup covers the complete current registered-worktree estate and all nested FreeCAD CLI state;
> - the applicable restore proof passes and receives independent review;
> - the individual worktree has a current passing retirement plan and audit;
> - its complete nested FreeCAD CLI state matches the D-GOV-021 approved pin and file changes;
> - no ambiguous, unique, unexplained or insufficiently preserved state remains;
> - inactivity and all existing preservation and identity requirements pass; and
> - a disposable proof demonstrates the exact proposed forced-removal operation and its post-removal checks.
>
> Where all of those conditions pass, permit exactly one `git worktree remove --force` for a retirement candidate whose ordinary `git worktree remove` refusal is caused only by the already-proved populated `.devtools/freecad-cli/` nested checkout.
>
> The force option is a mechanical removal exception. It gives no authority to bypass a failed audit, unresolved local state, preservation failure, changed identity or other retirement safeguard.
>
> After each removal, prove the required preservation diff and confirm that no unrelated worktree, branch, stash or retained evidence changed.
>
> If one `--force` operation still refuses removal, stop. Do not use additional force, manual recursive deletion, `git worktree prune`, `git stash` or another destructive workaround without a new owner decision.
>
> Preserve the five branches with unmerged commits. This authority does not permit their loss or retirement.
>
> Keep the normal non-force rule as the project default. Record this exception narrowly; do not make force removal a general retirement route.
>
> Complete the Phase 8 retirement prerequisite only when every required candidate has individually passed its applicable plan, audit, removal and post-removal preservation proof.
>
> Do not begin the authorised `turnout_valid_toe_range` product slice until that prerequisite is genuinely complete and protected `main` is clean and synchronised.
>
> The USB is currently unmounted. Mounting it for the required fresh backup and later physically removing/storing it remain on-site operator actions and must not be assumed.
>
> Phase 8 remains 0/4 with all exits Pending. D-P6-008 and all recorded limitations remain unchanged.

**Decision — D-GOV-022:** The owner authorises one `git worktree remove --force` operation for an individual worktree only if all these conditions pass:

- A fresh independent snapshot covers all current registered worktrees and nested FreeCAD CLI state. It does not overwrite an earlier snapshot.
- The applicable restore test gives PASS. An independent reviewer examines its result.
- The target has a current retirement plan. Its current retirement audit gives PASS. Its complete nested Git state matches the D-GOV-021 approved pin and six file changes.
- The target has the exact Git identity. No person or process uses it. The plan classifies every local-state item. The preservation audit gives PASS.
- The `git worktree remove` operation without `--force` refuses only because of the populated `.devtools/freecad-cli/` Git repository.
- A test in a temporary repository gives PASS for the exact proposed `git worktree remove --force` operation and the required checks after removal.

If the forced operation fails, stop. Do not use additional force or another destructive method. After each removal, record the preservation diff. Make sure that no unrelated worktree, branch, stash, or retained evidence changed. Preserve the five branches with unmerged commits.

The D-GOV-022 authority remains **unused** on current evidence. It does not authorise `--force` for a worktree whose removal without `--force` succeeds or whose refusal has another cause. It does not change D-P6-008, Phase 8 at 0/4, product behaviour, an
exit, performance, output, release, or legacy-removal status. The authorised product slice stays stopped until every required worktree passes its removal and preservation checks. Protected `main` must also be clean and synchronised. Physical USB separation remains an on-site operator action.

**Post-decision result:** The 42-root snapshot and the drill-02 restore test for seven nested Git repositories gave PASS. An independent reviewer examined both results. The first restore attempt and the first retirement-audit invocation remain retained as failures. The evidence does not record either as a PASS.

Each of the 37 worktrees had a passing retirement plan and a fresh audit. The checks after removal gave PASS for all 37, including the seven worktrees with nested FreeCAD CLI repositories. Git removed all 37 worktrees without `--force`. Git deleted 36 branches with `git branch -d`. The accepted commit contained each branch tip.

The detached worktree had no branch. No `--force` operation occurred.

The five branches with unmerged commits remain exact. After the removals, five worktrees remained registered: protected `main`, three historical unmerged-branch worktrees, and the terminal D-GOV-022 worktree. The replacement D-GOV-022 worktree was added later. Six worktrees were registered at that checkpoint. The retained terminal backup receipt is `5c6ab670b2b2dc73a29f393bc63038873755e833278363e238888dda07cb7562`. The 37-result summary is `63271bdb63a995dc22fee771c4720ca1cfdf83427507d760febb5c977e343371`.

The independently reviewed USB results-set manifest is `58d239054e72ff91f1106ee737aa2cbf5958832c6fe430868da2f44e0253088b`. The terminal recovery review is `f15b38442ea208f6049d30e41b194c5062221d15ac492af010c43ac01baba936`. The USB is safely unmounted. Physical removal and separate storage remain unconfirmed. The D-GOV-022 authority remains unused. At that checkpoint, the product prerequisite stayed open until D-GOV-022 integration and separate retirement checks for both candidate worktrees.

The remaining recovery conditions also had to pass.

<a id="phase-8-worktree-retirement-result"></a>
## Phase 8 worktree-retirement result — 2026-09-28

PR #97 integrated its exact reviewed head `1a8861b342727c54af7ecc95aa42adf4b66082c4` at protected `main` `245b4d56c1cd1d827db6f0af787bdda6e4d131b3`. Before removal, the non-overwriting `2026-09-27-pre-dgov022-worktree-retirement-01` snapshot covered all six registered worktrees. The terminal backup receipt `05c755ccb123adb1e449139bc8d3fd7f5116bce62c2f6c63734d86acc607b358` and disposable restore receipt `511e07cbc520ca3773388990053454619937cef8f0d242493dbc6bd1f9cf6cf8` gave PASS. Independent recovery review found the snapshot and both exact restores complete. The first failed restore attempt remains a failure record.

Both D-GOV-022 worktrees had a separate passing retirement plan and current audit. Git removed each with ordinary `git worktree remove`. It did not use `--force`. Both post-removal checks gave PASS. The preservation diff at that retirement boundary is:

| Item | Before removal | After removal |
| --- | --- | --- |
| Registered worktrees | Six worktrees were registered: protected `main`, three worktrees with unmerged branches, and the two D-GOV-022 worktrees. | Four worktrees remained: protected `main` and the same three worktrees with unmerged branches. |
| Local branches | Eight local branches existed. Five had unmerged commits. | The same eight local branches have the same tips. Git removed no branch. |
| Stash and accepted `main` | No stash existed. `main` was at `245b4d56c1cd1d827db6f0af787bdda6e4d131b3`. | No stash exists. `main` is unchanged and clean. |
| Retired local state | Both worktrees were present in the snapshot. | The snapshot preserves 589 exact entries from the terminal worktree (manifest `20aff3b9e8b5bc4f249e7383122de2656d77aa42620e66d67f3049883faf13c0`). It preserves 776 exact entries from the replacement worktree (manifest `54a5dd7b982282a1fd959cb2070a5172078c37cfa6c9d88dab978d3667e4ac5d`). |

The retained branch tip for `agent/phase8-retirement-mechanical-exception` is `deb71c8ca87cb947ff3de7abbfd635103133ade8`. The retained branch tip for `agent/phase8-retirement-documentation-replacement` is `1a8861b342727c54af7ecc95aa42adf4b66082c4`. The original `deb71c8` BLOCKED Documentation Review remains preserved at SHA-256 `e8e373f8cd1f52d32a5094364e7228f19ea5cd4a5b9f938c9c908ab48d534e19`. The ten-file USB evidence-copy manifest is `3e494d414f67e53b314c02753da3b49876d1497efb8e186112807240ca75602a`. The detailed local receipts are in `tmp/phase8-nested-retirement-recovery/dgov022-final-retirement/` and `tmp/phase8-dgov022-retirement-20260927/`.

The project completed the Phase 8 worktree retirement and recovery checks. The recorded snapshot, restore, audit, preservation and clean protected-`main` evidence supports that result. The D-GOV-022 force exception remains unused. The USB was flushed and safely unmounted. Physical removal and separate storage remain unverified. The [recovery policy](../RECOVERY_AND_BACKUP.md#backup-cadence-and-retention) contains instructions for these steps.

The approved USB can stay connected to the computer and available to software during development. This state alone does not block the authorised product slice. After this record alignment is integrated, clean, synchronised protected `main` must be verified again before product work. Phase 8 stays Open at 0/4, D-P6-008 stays Deferred — unmet, and no product or exit status changes.

<a id="phase-8-turnout-range-candidate"></a>

## Phase 8 turnout range candidate — 2026-09-28

D-P8-001 authorises the internal, development-only extraction of
`turnout_valid_toe_range`. The candidate puts the inherited calculation in
`tracktemplate/domain/turnout.py`. Product composition selects that function
for five inherited B15 callers and rejects a missing or mixed selection. The
public API, routing schema, UI terms and frozen B14/B15 source stay unchanged.

The pre-product, non-overwriting snapshot covered all seven registered
worktrees. Exact comparison and independent recovery review passed. The
September 5 full restore remains within the required monthly interval. The
source and snapshot receipts are retained in
`tmp/phase8-pre-product-recovery-20260928/` in the primary checkout.

The frozen B14/B15 calculation comparisons, complete 80-test standalone
profile, qualified FreeCAD proof and real-GUI range proof passed. The GUI proof
checked both inherited controls in both turnout orientations against the B14
and B15 calculations. The initial qualified FreeCAD call gave no proof because
it did not invoke the test. The corrected invocation passed. Both records
remain in `benchmark-output/phase8-turnout-toe-range/`. The GUI receipt is in
`benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs/`.

Independent source and test review found no blocker. Two standalone
fixture corrections
used the normal 2/2 repair allowance. Their original failures remain in
`tmp/phase8-turnout-toe-range/`.

This candidate contributes bounded evidence toward Exits 3 and 4. D-P8-001 accepts
no Phase 8 exit or wider turnout, crossover or timbering migration. TERM-R04
stays open. D-P6-008, both frozen source identities, the development-only
comparison oracle, every adapter, caller and removal condition, and all
legacy-retirement conditions remain. There is no performance,
production-output or release acceptance. Project status remains `unknown`.

<a id="phase-8-turnout-station-interval-candidate"></a>

## Phase 8 `turnout_host_station_interval` evidence — 2026-09-28

This change is internal to TrackTemplate. `turnout_host_station_interval` in
`tracktemplate/domain/turnout.py` calculates the interval from
`module_start_x` to `module_end_x` on the selected alignment. It uses
`orientation` to select the direction. TrackTemplate selects `turnout_host_station_interval` for 4 B15 callers. The
route check rejects a missing selection or a different selection for any
caller.

The API in `tracktemplate.api` stays the same. The schema for the route stays
the same. The terms that FreeCAD shows to a person stay the same. The B14/B15
source files stay the same.

A check compared values from `turnout_host_station_interval` with values from the frozen B14 and B15 sources. The result was
`PASS`. The validation profile for standalone Python included 81 checks. All
81 gave `PASS`. The FreeCAD caller check used the qualified host profile and
gave `PASS`.

A check used FreeCAD with `FreeCADGui` active and a copy of a `.FCStd` file. The
check made the turnout `TO-001`. It compared the interval in the FreeCAD data
with B14 and B15 values. TrackTemplate rejected a turnout because its interval
had values that were also in the interval for `TO-001`. TrackTemplate did not
change the FreeCAD data when it rejected this turnout. The SHA-256 of the
source `.FCStd` file was the same before and after the check.

The results are in
`benchmark-output/standalone-validation/20260928T095006133000Z/`,
`benchmark-output/phase8-turnout-host-interval/` and
`benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs/20260928T094740556578Z/`.

This evidence is for Phase 8 exits 2, 3 and 4 only. All 4 exits stay Pending. The checks for all Exit 2 operations are necessary. The Exit 3 checks for
a straight alignment and an alignment with a curve are necessary.

TERM-R04 stays open. D-P6-008 stays Deferred — unmet. These results do not change the conditions in
[D-P8-001](#phase-8-opening-panel).

A continuous integration (CI) result with status `success` for the SHA of the
draft pull request's commit is necessary. The project owner must make a new
decision before the merge. No owner decision accepts other migration, product
performance, production, physical output or release. Project status stays
`unknown`.

<a id="phase-8-turnout-edit-recovery-candidate"></a>

## Phase 8 turnout change and recovery evidence — 2026-09-28

The internal `turnout_configuration_change_summary` gives the sequence of changes for 3 B15 callers. The route check rejects a missing selection or a different selection for each caller. A check compared the wording and sequence with the frozen B14 and B15 sources. It also compared results for small value differences and missing `rail_geometry_revision` or `timber_geometry_revision` values. The API in `tracktemplate.api`, route schema and FreeCAD property names stay the same. The terms that FreeCAD shows to a person stay the same.

The validation profile for standalone Python included 82 checks. All 82 gave `PASS`. The FreeCAD caller check used the qualified host profile and gave `PASS`.

A check used FreeCAD with `FreeCADGui` active. It used a `.FCStd` file made from the source fixture. The alignment in the file had a curve. The check made `TO-001`. It changed `TurnoutHanding` from `Left-hand` to `Right-hand`.

The check compared the shape of the plain line before and after the change. It compared object names and the sequence of `record_id` values in `ProductionRecordIndexJSON`. One `Undo` operation gave the same FreeCAD data as after the check made `TO-001`. One `Redo` operation gave the same FreeCAD data as after the change. The check then caused an error during a turnout change. The error did not change the FreeCAD data or the data for `Undo` and `Redo`.

The check wrote the `.FCStd` file, closed it and opened it again. After the file opened again, its FreeCAD data had the same SHA-256 as after the change. No `Undo` or `Redo` operation was available after the file opened again. The SHA-256 of the source fixture stayed the same before and after the check. The results are in
`benchmark-output/standalone-validation/20260928T105448770253Z/`,
`benchmark-output/phase8-turnout-edit-summary/` and
`benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs/20260928T105224825343Z/`.

This evidence is for part of Exit 2 only. Checks for a straight alignment, a crossover and the other Exit 2 operations are necessary. More checks of FreeCAD workflows that write, close and open files again are necessary. All 4 Phase 8 exits stay Pending.

TERM-R04 stays open. D-P6-008 stays Deferred — unmet. The conditions in [D-P8-001](#phase-8-opening-panel) do not change. The checks did not measure product performance for `Edit` or `Validate/Export`. No decision from the project owner gives acceptance for a Phase 8 exit, product performance, production output or release. Project status stays `unknown`.

<a id="phase-8-crossover-radius-check-candidate"></a>

## Phase 8 crossover radius evidence — 2026-09-28

TrackTemplate now checks three minimum radii before it makes exact crossover
shapes. The components are `Host Track A turnout road`, `Host Track B turnout
road` and `Connecting road`. The smallest radius must be at least the configured
minimum. The result records both host identities, alignment data for both hosts,
input values and a SHA-256 signature.

TrackTemplate uses this check when a person selects `Preview geometry` or
makes a crossover. It also uses the check when a person changes a crossover
or extends a turnout to make a crossover. A change to a host identity,
alignment, input value or occupied interval prevents reuse of a previous
result. FreeCAD shows the complete crossover decision before the other
diagnostic information.

Both alignments in the fixed Phase 1 fixture have curves. TrackTemplate
rejected a crossover at `Host Track A` toe chainage 500.000 mm. The radius for
`Host Track B turnout road` was 540.848375 mm, below the configured minimum
of 600.000000 mm. Direct FreeCAD checks found no change to objects, stored
properties, shapes or `Undo`/`Redo` history after each rejection. The checks
rejected `Preview geometry` and attempts to make a crossover. They also
rejected an attempt to change a crossover or extend a turnout.

At `Host Track A` toe chainage 746.298 mm, TrackTemplate made `XO-001` in one
transaction. Its four exact radius values agreed with the 746.298 mm values in
[the Phase 1 crossover contract](../contracts/phase1-crossover-feasibility.json)
within 0.000001 mm. They also agreed with the values in
`complete_radius_preflight` within that tolerance. The FreeCAD check with
`FreeCADGui` active showed the rejection, the new `XO-001` and a rejected
change to that crossover. The
earlier turnout check with `FreeCADGui` active also passed. The SHA-256 of the
source fixture stayed the same.

The standalone Python validation profile for CI passed all 83 checks. The
local validation profile passed 82 of 83 checks. Its live recovery check
requires the `main` checkout and an ignored source archive. This worktree has
neither, so the failure class is `environment-or-profile-defect`. The raw
results are in these files and directories:

- `benchmark-output/standalone-validation/20260928T121032403653Z/`
- `benchmark-output/standalone-validation/20260928T120120467210Z/`
- `benchmark-output/freecad-bridge/phase8-crossover-preflight-headless-20260928-02.log`
- `benchmark-output/freecad-bridge/phase8-crossover-preflight-gui-runs/20260928T120949789318Z/`
- `benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs/20260928T121137728330Z/`

This evidence covers one crossover sample on alignments with curves for parts
of Phase 8 Exits 1 and 2. The checks do not cover straight alignments or more
crossover cases. They do not cover all operations to write a file, close it,
open it again and select `Validate/Export`. All four Phase 8 exits stay
Pending.

TERM-R04 stays open. D-P6-008 stays Deferred — unmet. The
[D-P8-001](#phase-8-opening-panel) conditions, frozen B14/B15 comparison and
all conditions for removal of the B14/B15 paths remain. No project owner
decision accepts product performance, production output, release or a Phase 8
exit. Project status stays `unknown`.

## Phase 8 fixed `XO-001` B4 error evidence — 2026-09-28

With `UndoMode=0` on clean `main`, an error in the first `B4` use of
`tag_generated_object` leaves a new `Part::Feature` in FreeCAD. The check
starts with a `.FCStd` file that has the source fixture data. B16 now removes
only this new `Part::Feature` after the command fails. Checks with
`UndoMode=0` and `UndoMode=1` show the same FreeCAD data and `Undo`/`Redo`
counts and names as before the error.

With `FreeCADGui` active, the check shows the error and no new
`Part::Feature`. B16 then applies `B4` to the fixed `XO-001`. The result has
`effective_timber_count=86` and `shared_timber_count=16`. The
`record_identity_sha256`, `stable_record_sha256`, and `resolution_signature`
values equal the [contract values](../contracts/phase1-crossover-timbering.json).
After one `Undo`, the FreeCAD data equals the data before `B4`. After one
`Redo`, the data equals the data after `B4`.

The check uses `document.save`, `App.closeDocument`, and `App.openDocument`
in that order. The `B4` result is the same before `App.closeDocument` and
after `App.openDocument`. The SHA-256 of the source fixture is the same before
and after the check.

The clean `main` result and the B16 FreeCAD results are in
`benchmark-output/phase8-crossover-b4-recovery/`. The GUI result and images
are in `benchmark-output/freecad-bridge/phase8-crossover-b4-recovery-gui-runs/20260928T134606144975Z/`.

This result gives partial evidence for Phase 8 Exit 2 only. PR-17 stays
Open/Partial. All four exits stay Pending. The check does not show a straight
alignment or other crossovers. It also does not show all Phase 8 Exit 2
operations to write, close, and open a file.

The primary `main` worktree and an ignored source archive are necessary for
the local profile check. The isolated worktree does not have these inputs.
TERM-R04 stays open. D-P6-008 stays Deferred — unmet. The B14/B15 comparison
and removal conditions do not change. No full B4 migration, product
performance, production output, release, or exit acceptance follows.

## Phase 8 `XO-001` `B4` persistence evidence — 2026-09-28

The accepted [Phase 1 data](../contracts/phase1-crossover-timbering.json)
show a difference between the initial `B4` result and the `resolved_analysis`
data in `b4_result`. A new check on clean `main` gives a FAIL result for this
difference. In `B16`, the 3 `resolved_analysis` values are equal after the
check applies `json.dumps` and then `json.loads` to the initial result. The
JSON values in the initial result, `b4_result`, and `CrossoverB4ResultJSON`
stay equal when the command uses the result again without a change to the
input. They stay equal after `Redo`, `document.save()`,
`App.closeDocument()`, and `App.openDocument()`.

The `geometry_signature` value is not empty. The `analysis_basis` value is
`Effective automatically resolved timber arrangement`. The selected sample
has 86 for `effective_timber_count` and 16 for `shared_timber_count`. It has
the accepted `record_identity_sha256` and `stable_record_sha256` values.

The FreeCAD checks use a qualified host profile with and without `FreeCADGui`
active. They examine one error that the test causes, the next command, and
`Undo`/`Redo`. They also examine one sequence with `document.save()`,
`App.closeDocument()`, and `App.openDocument()`. The result with
`FreeCADGui` active has the same
`effective_timber_count`, `shared_timber_count`, and shape as the result
without `FreeCADGui`.

The initial FreeCAD test with the new check gives a FAIL result. The check
compares `tuple` and `list` values before the JSON operation. These values are
equal after the JSON operation. The corrected check gives a PASS result in the
next FreeCAD test.

These checks examine some conditions of Phase 8 Exits 1 and 2. They do not
give all necessary evidence. PR-17 stays Open with Partial control effectiveness. All 4 Phase 8
exits stay Pending. The checks do not examine a straight alignment, other
crossovers, or more sequences with `document.save()`,
`App.closeDocument()`, and `App.openDocument()`.

TERM-R04, D-P6-008, the B14/B15 checks, and the conditions for removal
of B14/B15 paths do not change. This result gives no acceptance for a full
`B4` migration, product performance, production output, release, or a Phase 8
exit.

The `local` validation profile cannot give a result in this worktree. The
primary `main` worktree and its source archive are necessary. Git does not
include the source archive.

The `resolved_analysis_sha256` values from the check without `FreeCADGui` and
the check with it active are different. The `geometry_signature`,
`record_identity_sha256`, and `stable_record_sha256` values are equal. These
checks do not give the necessary evidence for Phase 8 Exit 3.

The result from clean `main`, the FAIL result, and the FreeCAD PASS result
are in `tmp/phase8-crossover-b4-analysis/`. The data from the check with
`FreeCADGui` active are in
`benchmark-output/freecad-bridge/phase8-crossover-b4-recovery-gui-runs/20260928T144631027771Z/`.
The local `ci` validation profile gives a PASS result for all 84 checks. Its
data are in
`benchmark-output/standalone-validation/20260928T145036677299Z/`.

<a id="phase-8-straight-host-crossover-result"></a>

## Phase 8 crossover on straight tracks — 2026-09-28

The B14 GUI launcher made a temporary input with two straight tracks.
Its straight entrances were 1500 mm long, and its straight exits were
450 mm long. The source FreeCAD file did not change.
The GUI run for Phase 1 without `--scenario` gave the frozen hashes and
the same `Undo` and `Redo` sequence. It also gave the same result after
`document.save()` and `App.openDocument()`.

The check used the qualified host profile for FreeCAD and `toe_chainage_a`
of 580.134 mm. It found equal B14, B15, and B16 crossover data after it
removed three `macro_version` fields. The data for all nine crossover
objects were equal, including their stable identities. Six objects had
shapes with equal `brep_sha256` values. Four production records were equal.

B16 rejected a request for a minimum radius of 3000 mm. The request did not
change the FreeCAD object data or the `Undo` and `Redo` data. B16 made one
`XO-001` and added one `Undo` entry.
The `Undo`, `Redo`, `document.save()`, and `App.openDocument()` checks gave
PASS results.

The GUI on the qualified host profile used the two straight tracks. The
`preview_geometry()` check returned geometry before the GUI made `XO-001`.
A rejected request did not change the FreeCAD object data or the
`Undo` and `Redo` data. The `Top` view files before and after `App.openDocument()` had equal
width, height, and colour values at each position. This check did not
include viewport selection, parameter editing, `Validate/Export`, or
other track pairs.

This result adds one sample with straight tracks for Exit 3 and some Exit 2
operations. All four exits stay Pending. The earlier headless and GUI
`resolved_analysis_sha256` values are different. These checks did not explain the difference or prove equivalent
full analysis in the two modes.

Other crossover inputs stay unproved. More sequences with `document.save()`
and `App.openDocument()` stay unproved. D-P6-008 and TERM-R04 do not change.
All conditions for required checks against legacy paths and for removal of
those paths also do not change.

The B14 input and Phase 1 check results are in
`benchmark-output/freecad-bridge/straight-station-runs/20260928T165114Z-phase8-straight-host/`
and `benchmark-output/freecad-bridge/straight-station-runs/20260928T165910Z/`.
The result from the qualified host profile is in
`tmp/phase8-straight-crossover/headless-regenerated-first.log`. The GUI result
and `PNG` files are in
`benchmark-output/freecad-bridge/phase8-straight-host-crossover-gui-runs/20260928T165738307958Z/`.
The local `ci` profile gave PASS results for all 84 checks. The results are in
`benchmark-output/standalone-validation/20260928T170104718903Z/`.

## Phase 8 `XO-001` `B4` display evidence — 2026-09-28

B16 keeps the stored `B4` result when a person changes only
`show_b4_geometry` for the selected `XO-001` on two alignments with curves.
A check used FreeCAD with `FreeCADGui` active on a qualified host profile.
After the check called `refresh_crossovers`, `Show final resolved timbering` showed
the same value as `ViewObject.Visibility`.

The check changed this check box and selected
`Resolve crossover timbering automatically`. The `B4` object and its
shape did not change. The check found that `resolve_crossover_b4_timbering`
and `_shared_timber_shape_from_records` did not run. The stored `B4`
result, `resolved_analysis` data and `Undo`/`Redo` data did not change.

The check used a `.FCStd` file made from the source fixture. It set
`ViewObject.Visibility` to `False` and called `document.save()`. After
FreeCAD opened the file, `ViewObject.Visibility` was `False`. The stored
`B4` data were equal before and after the file opened. A check found
equal values at each position in the two `Top` view `.png` files.

The `timber_semantic_sha256` values were different because the derived
`Shape` of the `ModelRailwayCurve` group changed after the file opened again.
When the check did not include this `Shape`, the hashes for the stored data were
equal. The source fixture did not change.

A second check used FreeCAD without `FreeCADGui` active on a qualified host
profile. It found equal results from `_b4_resolution_signature` for `True`
and `False` values of `show_b4_geometry`. The check changed `b3_settings`
and B16 calculated a new `B4` result. After `Undo`, the data
were equal to the saved data.

The result from FreeCAD without `FreeCADGui` is in
`tmp/phase8-b4-display-only/final-headless.log`. The result from FreeCAD
with `FreeCADGui` and the `.png` files are in
`benchmark-output/freecad-bridge/phase8-crossover-b4-recovery-gui-runs/20260928T184443291454Z/`.

This result adds evidence for Phase 8 exits 1 and 2 and PR-16. PR-16 is
Open and its control effectiveness is Partial. The [FreeCAD persistence adapter](../ARCHITECTURE.md#3-freecad-persistence-adapter)
and [presentation adapter](../ARCHITECTURE.md#4-lightweight-presentation-adapter)
did not change. All four exits stay Pending.

The `resolved_analysis_sha256` values from the two FreeCAD checks are
different. These checks do not prove that the complete `resolved_analysis`
data are the same with and without `FreeCADGui` active. The earlier check
used only one pair of straight alignments. Checks of other crossover
inputs are necessary. More checks must use `document.save()` and
`App.openDocument()` for other journeys.

The recorded limit for the `local` profile in this worktree applies.
D-P6-008 and TERM-R04 do not change. All conditions in
[D-P8-001](#phase-8-opening-panel) apply. This result
gives no owner acceptance for a Phase 8 exit, production output or release.

## Phase 8 `XO-001` crossover change evidence — 2026-09-28

Before this change, a test caused an error during the `XO-001` `Edit`
operation. The error removed `ChairAnalysis_XO_001` and
`ChairPositionMarkers_XO_001` before the operation was complete. This occurred
with `UndoMode=0` and `UndoMode=1`. B16 now keeps these two items until it
removes the previous crossover. The same check found that the FreeCAD data
and `Undo`/`Redo` data were equal before and after the error in the two modes.

A check used FreeCAD with `FreeCADGui` active on a qualified host profile. It
used a test `.FCStd` file with `XO-001` on alignments with curves. The
`preview_geometry()` operation for a `toe_chainage_a` change from 746.298 mm
to 746.299 mm did not change the FreeCAD data or `Undo`/`Redo` data. After this
operation, the test caused an error. The previous `B4`, the two items, the
`XO-001` selection, FreeCAD data and `Undo`/`Redo` data stayed the same. With
no error, the `Edit` operation removed the previous `B4` and the two items
and added one `Undo` entry.

One `Undo` put the previous FreeCAD data and the two items back. One `Redo`
put the changed FreeCAD data back. The crossover data before `document.save()`
and after `App.openDocument()` on the test file were equal. The previous `B4`
and the two items were not in the file after `App.openDocument()`. This check
did not include the `Shape` of the `ModelRailwayCurve` group. The source
fixture did not change.

The check before the B16 change and the qualified FreeCAD result are in
`tmp/phase8-crossover-edit-recovery/red-headless-terminating.log` and
`tmp/phase8-crossover-edit-recovery/green-headless-after-order.log`.
The qualified GUI result and images are in
`benchmark-output/freecad-bridge/phase8-crossover-edit-recovery-gui-runs/20260928T195434595292Z/`.

This result adds evidence for part of Phase 8 Exit 2 and PR-17. PR-17 stays
Open with Partial control effectiveness. All four exits stay Pending.

The `resolved_analysis_sha256` values from the headless and GUI checks are
different. These checks do not prove that the complete `resolved_analysis`
data are the same in the two modes. The earlier check used one pair of
straight alignments. Checks of other crossover inputs and more routes through
`document.save()` and `App.openDocument()` are necessary. The recorded limit
for the `local` profile in this worktree applies.

D-P6-008 and TERM-R04 do not change. All conditions in
[D-P8-001](#phase-8-opening-panel) apply. This result gives no owner
acceptance for a Phase 8 exit, production output or release.

## Phase 8 `XO-001` host-integration recovery evidence — 2026-09-29

This Level 2 result is for one `XO-001` crossover on two host
alignments with curves. The work started from clean protected `main` at
`1b5b7c8f0c4b6974962b09ff505e6a8e292875b3`. The checks used copies of the
B14 `.FCStd` fixture. Its SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.

Before the change, rejected host-integration Create and Remove operations
removed two chair-display objects before B15 opened a FreeCAD transaction.
With `UndoMode=1`, these operations also added an `Undo` entry. B16 now opens
one FreeCAD transaction before each inherited operation. It rejects an
operation before it changes the document when `UndoMode=0`. B14, B15, the
stored schema and the public API did not change.

On the qualified host profile, the FreeCADCmd check caused an error during
Create and an error after a production-record write.
Each error left the document objects, chair displays,
production records, bindings and `Undo` history unchanged.

Create without an error replaced four source records with three records for
the host integration. The index changed from eight records to seven. The
operation added six integration objects. After Remove, the index again contained the four source
records and eight records in total. Each operation without an error added one `Undo`
entry. The `Undo`, `Redo` and save/reopen checks on fixture copies gave PASS.

The real GUI check on the qualified FreeCAD 1.1.3 host profile used the
crossover manager panel.
It examined the confirmation and error dialogs, the objects that the GUI
showed, and the record changes. It also examined `Undo`, `Redo` and
save/reopen of fixture copies after Create and Remove. The panel kept
`Production ready: No`. The run gave PASS, kept 15 images and closed the document. Its source and
fixture hash checks gave PASS.

The result before the change is in `tmp/phase8-host-integration/red.log`. The FreeCADCmd result is in `tmp/phase8-host-integration/headless-final-source.log`.
The GUI receipt and images are in
`benchmark-output/freecad-bridge/phase8-crossover-host-integration-recovery-gui-runs/20260928T224900599163Z/`.

The FreeCADCmd check compares stored state and stable shape measures. It does
not claim byte equality for BRep data. During save/reopen of a fixture copy, one derived `ModelRailwayCurve` shape
area changed by 0.000000001 mm². The permitted difference is at most
0.000000002 mm² for that area only.

These results give evidence for part of Phase 8 Exit 2
and PR-17. PR-17 stays Critical, Open and Partial. All four exits stay Pending
at 0/4.

The retired straight-host edit candidate and its evidence remain in a different worktree.
These checks give no evidence for other host inputs, complete
`resolved_analysis` parity, validation, export or production output. D-P6-008 and TERM-R04 remain.
The frozen B14/B15 identities, inherited B15 host, development-only comparison
oracle, all comparison conditions and all legacy-retirement conditions remain.
This result gives no owner acceptance for a Phase 8 exit, output or release.

## Phase 8 `XO-001` SVG and CSV evidence from highlighted rows — 2026-09-29

This Level 2 result covers one curved `XO-001` on a copy of the fixed B14
fixture. At the start, protected `main` had no changes and pointed to
`9d52096da6409d18965daf907401ea320db3c344`. Both checks created B16 host
integration. Each test script called `document.save()` before it closed and
opened its copied `.FCStd` file again.

The FreeCADCmd check made one SVG file and one CSV manifest. A second export
gave the same `normalised_sha256` values for both files. The check caused one
error after FreeCAD made the SVG file and another error during `commit_staged_export_entries()`.
Each error left the output directory empty and kept the FreeCAD data and
`Undo` history. The `CROSSOVER_CHAIR_VALIDATION_OUTSTANDING` finding did not
stop the operation. The crossover kept `production_ready=False`.

The qualified FreeCAD 1.1.3 GUI check opened
`SelectedProductionExportDialog` with no FreeCAD object selected. `SelectedProductionExportDialog`
showed seven records. The check highlighted the integrated `CuttingProfile`
row. `SelectedProductionExportDialog` also selected its paired `Solid` row.
The preflight had no
blocking error. The confirmation showed two files to make.

The summary reported two successful files, no failed files, and one skipped
solid record. The CSV manifest recorded one successful cutting profile and
one skipped solid record. The SVG bounds check gave PASS. The production record
index, object list, and `Undo` history did not change.

The FreeCADCmd result is in `tmp/phase8-selected-export/headless-rerun.log`.
The GUI receipt and five images are in
`benchmark-output/freecad-bridge/phase8-crossover-selected-export-gui-runs/20260929T060558000388Z/`.

Three earlier GUI failure receipts remain under
`benchmark-output/freecad-bridge/phase8-crossover-selected-export-gui-runs/`.
The GUI check does not show an SVG file from a FreeCAD object selected
before `SelectedProductionExportDialog` opens. The check used `SelectedProductionExportDialog` directly. It did
not use the manager entrypoint `_open_selected_export()`. The SVG and CSV manifest have
Private-development status. They do not clear production output.

This result adds partial evidence for Phase 8 Exit 2 and PR-17. PR-17 remains
Critical, Open, and Partial. Phase 8 remains at 0/4 with all exits Pending.

The preceding result permits at most 0.000000002 mm² area difference for one
derived `ModelRailwayCurve` shape after save and reopen. D-P6-008 and TERM-R04
remain.

The frozen B14/B15 identities and inherited B15 host remain. The comparison
oracle remains for development use only. All comparison conditions remain.
No condition to remove a B14 or B15 product path changes. This result gives no
owner acceptance for a Phase 8 exit, output, or release.

## Phase 8 `TO-001` host integration recovery evidence — 2026-09-29

This Level 2 result is for one `TO-001` turnout on a curve in a file made from
the B14 fixture. Work started from clean protected `main` at
`e9a3a9ab04ed82ff053e5ead2b52cae3ae77637b`. The source fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.

The stopped turnout candidate and its test results with `FAIL` status are in a
different worktree. A rejected `Create` removed two objects from
`_chair_analysis_display_objects()`. B15 did not use `openTransaction()` before
this removal. The removal also added a `Delete` `Undo` entry. B16 now uses
`openTransaction()` before each B15 host integration `Create` and `Remove`
operation. B16 rejects these operations before mutation when `UndoMode=0`.

The `FreeCADCmd` check used the qualified host profile. It rejected `Create` and
`Remove` with no change to the compared FreeCAD data or `Undo` history. The
check caused a `Create` error before a production data write. It caused errors
after production data writes during `Create` and `Remove`. After each error, the
compared FreeCAD data did not change.

Before `Create`, the production `records` data contained ten entries. `Create`
replaced four source entries with two entries for host integration. After
`Create`, the data contained eight entries, and the file contained five new
objects for host integration. After `Remove`, the data contained ten entries and
the initial object mappings.

Each operation added one `Undo` entry when it completed. The `Undo` and `Redo`
tests gave `PASS` results for `Create` and `Remove`. The check used `save()` and
opened the files again after `Create` and `Remove`.

The project owner set a `0.000000002 mm²` limit for the derived
`RailwayTurnoutIntegration_TO_001` group shape area. The limit applies only when
the check uses `save()` and opens the file again. No other object or field can
use this limit. The `ModelRailwayCurve` area limit does not change.

The two area limits have different scopes. The check found equal values for all
other FreeCAD properties and `records` entries. The check found equal values for
all other stable shape measures. This check does not show that BRep bytes are
equal.

The GUI check ran in the qualified host profile for FreeCAD 1.1.3. It used
`TurnoutManagerDialog` methods and confirmation and error dialogs. It examined
rejected `Create` and `Remove` operations, object mappings, visibility, and
objects from `_chair_analysis_display_objects()`. Each operation added one
`Undo` entry when it completed. The check used `Undo`, `Redo`, and `save()` for
each operation. It opened each file again.

The GUI result was `PASS` and included 16 images. The check closed its FreeCAD
file. The source and fixture hashes did not change.

The GUI check compared each `has_shape` value. The `FreeCADCmd` check compared
area values. The fixture had no `2D chair layout` with the necessary status
before integration. The Step 6 control was not available. The GUI check did not
use the Step 6 control.

The `FreeCADCmd` result is in
`tmp/phase8-turnout-host-integration-qualified-proof/headless-first.log`. The
GUI result and images are in
`benchmark-output/freecad-bridge/phase8-turnout-host-integration-recovery-gui-runs/20260929T115749631809Z/`.

This result gives evidence for part of Phase 8 Exit 2 and PR-17. PR-17 has
`Critical` severity, `Open` status, and `Partial` control effectiveness. Phase 8
is 0/4, with all four exits Pending.

The checks do not show results for other host inputs or complete production
metadata. They do not show the sequence of all `records` entries. They did not
use button signals to start `Create` and `Remove`. They do not show Step 6
access, validation, export, or production output.

D-P6-008 stays Deferred — unmet. TERM-R04 stays open. B14, B15, FreeCAD property
definitions, schemas and the public API did not change. B16 continues to use the
B15 host.

The project uses the comparison oracle for development only. No comparison
condition or condition to remove a legacy path changed. This result gives no
acceptance for a Phase 8 exit, output, or release.

## Phase 8 `TO-001` selected SVG and CSV evidence — 2026-09-29

This Level 2 result is for one `TO-001` turnout on a curve in a copy of
the B14 fixture. Work started from clean protected `main` at
`cf3bdfc400253004831da0f93dc4024d165f86de`. The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
No product source, stored schema, public API, or accepted oracle changed.

The two checks made `TO-001` host integration in copies of the fixture. The
`FreeCADCmd` check used `save()` and opened the file again. It compared the sequence of eight `records` entries and the two record
IDs for host integration with the state after `save()`. The IDs contain `CURVE`, but the stored `route_id` field is empty.

In the `FreeCADCmd` check, two exports each made one SVG file and one CSV
manifest. The two exports gave equal normalised SHA-256 values for these files. No finding in the `FreeCADCmd` preflight prevented export. The check caused one error after the SVG file was made and a second
error during the commit of the second staged file. Each error left its output
folder empty and kept the compared document state and `Undo` history.

The GUI check on the qualified FreeCAD 1.1.3 host profile used
`TurnoutManagerDialog` to make host integration. It used `save()`, closed the copied file, and opened it
again. The check opened `SelectedProductionExportDialog` directly and
highlighted the integrated `CuttingProfile` row. The dialog also highlighted
the paired `Solid` row, with no FreeCAD object selected. Its only preflight
finding was `OUTPUT_DIRECTORY_WILL_BE_CREATED`, which did not prevent export.

The confirmation named two files. The summary showed `Successful files: 2`,
`Failed files: 0`, and `Skipped outputs: 1`. The CSV manifest had one profile row with `Success` status and one solid
row with `Skipped` status. The two rows named their `TO-001` host integration
objects. The
SVG bounds check gave PASS. The record index, configuration, integration,
object list, and `Undo` history did not change during export.

The first GUI receipt has `FAIL` status at the highlighted-pair assertion. The
copied file has an empty `route_id` field, while the integrated record IDs
contain `CURVE`. This entry classifies the first GUI failure as `fixture-or-harness-defect`.
The project did not keep the earlier untracked runner bytes. The assertion that caused the first error remains unknown. A GUI run after
the failure gave PASS with the same command.

The `FreeCADCmd` result is in
`tmp/phase8-turnout-selected-export/headless-first.log`. The GUI
receipt with PASS status and five images are in
`benchmark-output/freecad-bridge/phase8-turnout-selected-export-gui-runs/20260929T210051286227Z/`.
The first GUI failure receipt remains in
`benchmark-output/freecad-bridge/phase8-turnout-selected-export-gui-runs/20260929T205832229894Z/`.
The GUI check closed its copied file. Its source and fixture hash checks gave
PASS.

These checks show selected SVG and CSV export for this copied turnout only.
They do not show the preselected-object route, manager export entrypoint,
guided Step 6 access, other host inputs, or complete production metadata.
Output keeps Private-development status. This result gives evidence for part of Phase 8 Exit 2 and PR-17. PR-17 stays Critical, Open, and Partial. Phase 8
stays 0/4, with all four exits Pending.

The two save/reopen area allowances apply only to the derived
`ModelRailwayCurve` shape and the derived `TO-001` host-integration group.
All other compared persistent state and stable shape measures remain exact.
D-P6-008 stays Deferred — unmet, and TERM-R04 stays open. B14, B15, the
inherited B15 host, the development-only comparison oracle, all comparison
conditions, and all legacy-retirement conditions remain. This result gives no
acceptance for a Phase 8 exit, output, or release.

<a id="phase-8-straight-alignment-turnout-result"></a>

## Phase 8 turnout on a straight alignment — 2026-09-30

This Level 2 result examines one `TO-001` turnout on a 1500 mm straight
alignment. Its `orientation` value is `Facing`, and its `handing` value is
`Left-hand`. Its `toe_chainage` value is 580.134 mm. The checks used copies of
the B14 source file with SHA-256
`3ded0cd038971aca86f87fcb18061e3cfaf382e173a8d505d7f638724074efdd`.
The source file stayed unchanged.

The qualified `FreeCADCmd` check compared B14, B15 and B16 after it excluded
`macro_version` and `GeneratorVersion`. All three gave equal turnout data.
Eight turnout objects had equal names, property types and compared values.
Seven objects with a shape had equal `brep_sha256` values and `summary` data.
The same 18 ordered `records` entries were present.

B16 rejected an invalid `toe_chainage` value without a document change.
Its `Undo` operation restored the 23-object source. `Redo` restored the
31-object turnout state. After `save()` and `openDocument()`, the compared
properties and stable `summary` data were equal. The check did not compare
exact shape bytes after `openDocument()`.

The check in the qualified FreeCAD 1.1.3 GUI used `TurnoutManagerDialog`.
The dialog made `TO-001` and rejected an overlapping second turnout.
The check changed `handing` from `Left-hand` to `Right-hand`.
The check caused an error during an edit. The error left the document and
`Undo` history unchanged. `Undo` and `Redo` restored the compared states.

After `save()` and `openDocument()`, the dialog removed `TO-001`. The check
compared each state after `Remove`, `Undo`, `Redo`, `save()` and
`openDocument()` with its expected source or turnout state. The `record_id`
values kept their order. `Remove` restored 23 objects and 12 `records`
entries. In the source `ProductionRecordIndexJSON` value, `macro_version`
changed from the B14 value to the B15 value. All other compared source data
stayed equal.

The first two GUI `run.json` files record `FAIL`. One test expected the B14
`macro_version` value after `Remove`. Another test expected the order of
`document.Objects` after `Remove` and `Undo`. Both have the
`test-or-oracle-defect` failure class. A diagnostic run intentionally gave
`FAIL` and kept data for the second test error. After the test repairs, the
GUI check gave `PASS`.

The `FreeCADCmd` result is in
`tmp/phase8-straight-turnout/headless-enhanced.log`. The GUI `run.json` file
with `PASS` status and seven images are in
`benchmark-output/freecad-bridge/phase8-straight-host-turnout-gui-runs/20260930T054358592293Z/`.
The three earlier `run.json` files remain under that directory.

These checks cover one copied source file with a straight alignment and one
`TO-001` turnout. They add bounded evidence for Phase 8 Exits 1, 2 and 3.
The main result is for Exit 3. They do not show selected export, guided Step 6,
other host inputs, complete production metadata, or product performance.

All four exits stay Pending at 0/4. D-P6-008 stays Deferred — unmet, and
TERM-R04 stays open. The frozen B14/B15 sources, inherited B15 host,
development-only comparison oracle and legacy-retirement conditions remain.
This result gives no acceptance for a Phase 8 exit, production output, or
release.

<a id="phase-8-straight-crossover-b4-result"></a>

## Phase 8 `XO-001` `B4` check on straight tracks — 2026-09-30

This Level 2 result examines `XO-001` on two straight tracks in a copied B14
source file. The entrance is 1500 mm long, and the exit is 450 mm long.
The source file SHA-256 is
`3b4fc9fd8131981a637a3fd50105b0f1d7e44f311eb51a7f03bf01239ad7a3b1`.
The source file stayed unchanged.

The qualified `FreeCADCmd` check compared the B14, B15 and B16 `B4` results.
The three results had equal data for all 82 ordered `resolved_timbers` entries
and their unique `stable_identity` values. Each result had
`effective_timber_count=82`, `shared_timber_count=18`,
`unresolved_count=0` and `remaining_production_conflicts=0`. The findings,
object data for 34 objects, `B4` shape bytes and four direct `XO-001` source
bindings were equal. Only `macro_version` and `created_at` were excluded from
the production index comparison.

B16 reused the `B4` result without a document or `Undo` change. One `Undo`
restored the 32-object crossover state. `Redo` restored the 34-object `B4`
state. After `save()` and `openDocument()`, the stored `resolved_timbers`
entries and `resolved_analysis` JSON data were equal to the expected values.
The source bindings and stable `B4` shape data were also equal. The check did
not compare exact shape bytes after the file opened again.

The qualified FreeCAD 1.1.3 GUI check used the `CrossoverManagerPanel` for
the selected `XO-001`. The GUI showed a dialog for an error at the first `B4`
object tag. The error left the document, production bindings and `Undo`
history unchanged. The next `B4` command made 34 objects and increased
`undo_count` by one. The GUI result matched the compared data for counts,
identities, findings, stable shape data and source bindings. Unchanged reuse
kept the document and `Undo` history.

The GUI check changed `Show final resolved timbering` without a new
calculation or shape build. The check box matched the `B4` object visibility.
The panel kept `XO-001` selected.

`Undo` restored 32 objects, and `Redo` restored 34. The check hid `B4` and
used `save()` and `openDocument()`. Its visibility stayed off. The stored
analysis data and source bindings stayed equal. The new FreeCAD session had
no earlier `Undo` history.

The first headless check gave `FAIL`. The test compared `tuple` and `list`
values before JSON conversion. The failure has the `test-or-oracle-defect`
class. The corrected check gave `PASS`. The failed check and diagnostic data
remain in `tmp/phase8-straight-xo-b4/`.

The B14 source receipt is in
`benchmark-output/freecad-bridge/straight-station-runs/20260930T070824Z-phase8-straight-host/`.
The passing headless receipt is in
`benchmark-output/freecad-bridge/phase8-straight-crossover-b4-headless-runs/20260930T072529794571Z/`.
The passing GUI receipt and seven images are in
`benchmark-output/freecad-bridge/phase8-straight-crossover-b4-gui-runs/20260930T073331614634Z/`.

The `rail_and_flangeway_clearance_deferred` finding stays. One
`CrossoverConstructionMarks` index entry has `diagnostic_status=Error`
because its geometry is not planar. The GUI result has
`production_ready=false`, `host_integration_allowed=false` and
`rail_clearance_checks_reliable=false`. Earlier different
`resolved_analysis_sha256` values for the curved `B4` checks with and without
`FreeCADGui` remain unexplained. This straight-track check did not compare all
`resolved_analysis` fields between the two modes.

This result adds bounded evidence for Phase 8 Exits 1 and 3 and some Exit 2
operations. All four exits stay Pending at 0/4. It does not show selected
export, guided Step 6, other crossover inputs, production clearance or product
performance. D-P6-008 stays Deferred — unmet, and TERM-R04 stays open.
The frozen B14/B15 sources, inherited B15 host, development-only comparison
oracle and legacy-retirement conditions remain. This result gives no owner
acceptance for a Phase 8 exit, production output or release.

<a id="phase-8-straight-crossover-b4-analysis-result"></a>

## Phase 8 `XO-001` `B4` data in FreeCADCmd and the GUI — 2026-09-30

This Level 2 result compares the complete `resolved_analysis` data for one
`XO-001` on straight tracks. The qualified `FreeCADCmd` and real-GUI checks
use copies of one B14 source file. Its SHA-256 is
`abe6d3e32bd77e2b146c015b726bf83bde2b9f131fc503b9d0d4c896b73bac19`
before and after the checks. No product source or B14/B15 reference file
changes.

The `FreeCADCmd` and GUI result files report `PASS`, but the SHA-256 values
for their full `resolved_analysis` data are different. Only the data in the
`performance_timings_ms` JSON key differs. The check result gives the measured
times for both checks. The data in the other 20 JSON keys of
`resolved_analysis` is equal. This includes the `findings` data,
`geometry_signature` and all 82 `timbers` entries. When the check ignores
`performance_timings_ms`, the two `resolved_analysis` values have this
SHA-256:
`bfbd3f2717f3ec19f0164c291d1f91b68522aefbf7ec5090a65f3c2033ad162e`.

The B14, B15 and B16 results remain equal for this source.

The `FreeCADCmd` result file is in
`benchmark-output/freecad-bridge/phase8-straight-crossover-b4-headless-runs/20260930T091240731184Z/`.
The GUI result file, 7 images and the check result file are in
`benchmark-output/freecad-bridge/phase8-straight-crossover-b4-gui-runs/20260930T091341211190Z/`.
The standalone Python tests show that the check rejects changes to the other
`resolved_analysis` data and the identities of its input files. The previous
failed result files remain.

This result adds bounded evidence for part of Phase 8 Exit 3. The previous
`resolved_analysis_sha256` difference on curved tracks has no known cause. The
[prior straight `B4` result](#phase-8-straight-crossover-b4-result) keeps its
deferred rail-clearance finding, construction-mark diagnostic and
non-production limits.

All four exits stay Pending at 0/4. D-P6-008 stays
Deferred — unmet, and TERM-R04 stays open. Output stays private-development.
No production clearance follows. This result gives no acceptance for product
performance, selected export, production output, a Phase 8 exit or release.

<a id="phase-8-straight-crossover-edit-result"></a>

## Phase 8 `XO-001` Edit on straight tracks — 2026-09-30

This Level 2 result examines one `XO-001` on 2 straight tracks. The checks
used separate files with the same B14 source data. The source SHA-256 is
`3b4fc9fd8131981a637a3fd50105b0f1d7e44f311eb51a7f03bf01239ad7a3b1`.
The source file stayed unchanged.

The `FreeCADCmd` check used the qualified host profile. It changed the Host A
toe chainage from 580.134 mm to 580.135 mm. After the `Edit`, B14, B15 and B16
had equal crossover data, 9 crossover objects, 6 exact BRep hashes and 4 ordered
values in `production_record_ids`. The comparison excluded only 4 frozen
macro-version fields. B16 rejected an `Edit` that did not meet the minimum
radius requirement. The document and `Undo` history did not change.

After 1 `Undo`, the data was equal to the data before the `Edit`. After `Redo`,
the data was equal to the changed data. The data and stable shape summaries
stayed equal after `save()` and `openDocument()`. The result and required `PASS`
sentinel are in
`tmp/phase8-straight-crossover-edit-lifecycle/headless-final.log`.

The real-GUI check used the qualified host profile. It selected the stored
`XO-001` in the crossover manager. The preview rejected an `Edit` that did not
meet the minimum radius requirement. The test also requested the same `Edit` and got a rejection. Neither rejection changed the document or `Undo`
history. The accepted preview also kept the document unchanged.

The accepted `Edit` kept `XO-001` selected and kept 4 live entries in
`source_bindings`. It added 1 `Undo` entry. The check got the expected data
after `Undo`, `Redo` and save/reopen. The `PASS` receipt and 12 images are in
`benchmark-output/freecad-bridge/phase8-straight-host-crossover-gui-runs/20260930T104018763675Z/`.

The previous failed straight `Edit` candidate remains in the
`phase8-straight-crossover-edit-parity` worktree. A fixture diagnostic showed
that its headless `Undo` assertion failed only because FreeCAD listed the same
32 objects in a different order. Its 4 GUI `FAIL` receipts showed incorrect
test assumptions about FreeCAD object identities, object order and 1 deleted
object handle. The corrected checks still examine identities, document data
and `source_bindings` values.

After an accepted `Edit`, the GUI still shows `Editing XO-001` in Picked
placement. The inherited B15 panel clears `Edit` mode and reports the update
in its diagnostic. It does not remove `Editing XO-001`. This visible limit is
`REQUIRED_BEFORE_EXIT` for Exit 2. No B14, B15 or B16 product source changed.

This result adds bounded evidence for Phase 8 Exits 2 and 3 and PR-17. It does
not show selected export, host integration, other crossover inputs, complete
Exit 2 coverage or product performance. All 4 exits stay Pending at 0/4.

PR-17 stays Critical, Open and Partial. D-P6-008 stays Deferred — unmet, and
TERM-R04 stays open. Output keeps Private-development status. This result gives
no acceptance for a Phase 8 exit, production output or release.

## Phase 8 exit conditions

These four criteria are unchanged from accepted plan revision
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`. D-P8-002 accepts Exit 3 only.

| Exit condition | Status | Evidence |
| --- | --- | --- |
| Turnouts and crossovers retain accepted geometry, topology, timber decisions, identities, findings, and production records. | Pending | No Phase 8 exit admission. |
| Creation, parameter editing, selection, undo/redo, save/reopen, validation, and export pass in the real GUI. | Pending | No Phase 8 exit admission. |
| Straight- and curved-host representative workflows pass deterministic comparison. | Evidenced — owner-accepted 2026-09-30 | [D-P8-002 panel and decision](#phase-8-exit-3-admission-panel) |
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
