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
| What changed | The owner opened Phase 8 for its four unchanged criteria. The completed Phase 7 evidence, decisions and risk snapshot remain frozen. PR #94 integrated that opening. The retained independently reviewed snapshot covers the earlier 39-worktree estate. PR #95 integrated D-GOV-020 and PR #96 integrated D-GOV-021. <br><br>D-GOV-022 authorises one `git worktree remove --force` operation only if its conditions pass. An independent reviewer examined the 42-root snapshot and restore evidence for seven nested Git repositories. The 37 individual retirement audits gave PASS. Git removed 37 worktrees without `--force`. Git also deleted 36 branches whose tips the accepted commit contained. <br><br>PR #97 integrated D-GOV-022. A fresh six-root snapshot, restore test, individual audits and post-removal checks gave PASS. Git removed the two remaining D-GOV-022 worktrees without `--force`. The [preservation diff](#phase-8-worktree-retirement-result) records their retained branch tips. |
| What now works | The four Phase 7 exit decisions keep their accepted bounded evidence. The Phase 8 candidate passed development-only calculation, caller and real-GUI range tests. |
| Limitations/findings | All Phase 7 proof limits, B14/B15 identities, the inherited B15 host, the development-only comparison oracle, and every comparison, adapter, caller, removal and legacy-retirement condition remain. D-P6-008 remains mandatory before Phase 10 beta acceptance. <br><br>The earlier test used a Git repository that the Git ignore rule did not select. Its removal without `--force` failed. An independent reviewer examined the 42-root snapshot and restore test. Each of the seven parent worktrees had a passing retirement plan and audit. Git removed all seven without `--force`.<br><br>After removal, each preservation check gave PASS. The D-GOV-022 authority remains unused. Five branches with unmerged commits and three related worktrees remain. The two D-GOV-022 worktrees are retired. Four worktrees remained at that retirement boundary. All eight prior branch refs, including both retired-worktree refs, remain.<br><br>The USB is safely unmounted. Physical removal and separate storage remain unverified. |
| Owner decision | D-P8-001 opens Phase 8 at 0/4 and authorises the later internal `turnout_valid_toe_range` slice only after its retirement prerequisites. D-GOV-020 and D-GOV-021 remain the integrated exact-state controls. D-GOV-022 authorises one `git worktree remove --force` operation only if every condition in the decision passes. No current worktree meets these conditions. These decisions accept no exit, performance, wider migration, production output, release or legacy removal. |
| Next action | The owner decides whether to integrate the exact-green draft for the bounded `turnout_valid_toe_range` candidate. Phase 8 remains Open at 0/4. All exits remain Pending. |

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

## Phase 8 turnout edit and recovery evidence — 2026-09-28

The internal `turnout_configuration_change_summary` supplies the ordered
change list for three inherited B15 callers. For the B15 host, the route check
rejects a missing or different selection. A check compared its text, order,
numeric comparison and revision fallback with the frozen B14 and B15 sources.
The public API, route schema, stored FreeCAD property names and UI terms stay
the same.

All 82 checks in the complete standalone profile passed. The qualified
FreeCAD caller check passed. A real GUI check used a copy of a saved `.FCStd`
file and a curved host. It created `TO-001`, then changed it
from `Left-hand` to `Right-hand`. The check compared the geometry of the host
plain line, object names and record order in `ProductionRecordIndexJSON`.
One Undo restored the created state. Redo restored the edited state. An
injected edit failure changed neither the document data nor Undo history.
After save, close and reopen, the copied document had the same captured data
as the edited document and cleared history. The source fixture stayed
byte-identical. The raw results are in
`benchmark-output/standalone-validation/20260928T105448770253Z/`,
`benchmark-output/phase8-turnout-edit-summary/` and
`benchmark-output/freecad-bridge/phase8-turnout-toe-gui-runs/20260928T105224825343Z/`.

This is bounded evidence toward Exit 2. The straight-host, crossover and
broader save/reopen journeys remain unproved. All four Phase 8 exits stay
Pending. TERM-R04, D-P6-008, the B14/B15 comparison duties and all
legacy-retirement conditions remain. This result accepts no Phase 8 exit,
production output or release. Project status stays `unknown`.

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
