# Phase 7 Core Alignment, Station and Multiple-Track Migration Evidence

Status: **Open — 0/4 evidenced exits under D-P7-001 on 2026-09-05.
All four exits are Pending.**

Phase 6 closed on 2026-09-05 under
[D-P6-009](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-closeout-panel).
It keeps four accepted exits and one deferred, unmet obligation.
Its [evidence](../history/phase-closeouts/PHASE6_CLOSEOUT.md),
[decisions](../history/phase-closeouts/PHASE6_GATE_DECISIONS.json), and
[risk snapshot](../history/phase-closeouts/PHASE6_RISKS.json) are frozen.
The owner accepted the completed, independently reviewed
[recovery proof](../backup-records/2026-09-05-phase6-closeout-recovery.md).

## Current owner view

| Field | Current position |
| --- | --- |
| Current state | Phase 7 is Open at 0/4. Phase 6 is closed with four accepted exits and one deferred, unmet obligation. |
| What changed | The implementing agent merged PR #71 into clean protected main. The new candidate moves the function that calculates common straight-end extensions into `tracktemplate.domain.alignment` for `tracktemplate.api`. The B16 Generate/Replace caller uses its result through `_CommonStraightExtensionsAdapter`. |
| What now works | Complete calculated results, Python `list` changes and previous identities are equal to B14/B15 for the supported records. Checks with standalone Python, qualified FreeCAD and the applicable human interface had PASS results. The product selects seven functions together and puts previous values back after a selection error. |
| Limitations/findings | Direct operations have about 1.25 microseconds of added wall cost per measured input group. This task accepts no Phase 7 exit or product performance result. D-P6-008, all risks and all conditions to compare results and remove legacy paths stay in full. |
| Owner decision | Richard authorised the merge of PR #71 and one subsequent Level 1 or Level 2 result through draft publication. A merge of the new exact-green draft needs another owner decision. |
| Next action | Complete the applicable validation, independent review and publication route. Bring the new exact-green draft to Richard for merge authority. |

## Common straight-end extension migration — 2026-09-09

The implementing agent merged PR #71 into protected main at `a8e21ce320d2c4ecdac02992508389e574e51d7c`.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result with authority from D-GOV-004 and the Phase 7 scope.

The `run_macro` caller used a B15 function that was missing from `tracktemplate.domain.alignment`.
The candidate moves that function for common straight-end extensions into `tracktemplate.domain.alignment` for `tracktemplate.api`.
A small compatibility object applies its results to the host records before the checks of entry and exit distances.
The [API instructions](../contracts/phase7-common-straight-extensions.md) define the supported inputs and permitted changes.

The checks before the source change preserve 57 complete B14/B15 groups, each used two times.
Nine selected test sets with standalone Python and five proofs with qualified FreeCAD had PASS results, including 58 groups with actual `App.Vector` values.
All six new human-interface samples had PASS results.
The checks compare all result data from the fourteen new, preserved and legacy workflow records and give equal results.

The direct checks preserve every result and previous identity for 6,000 operations with new input groups per state.
They measure about 1.25 microseconds of added wall cost per operation, or 25.33% of the direct cost for the comparison baseline.
The [evidence record](../benchmarks/2026-09-09-phase7-common-straight-extensions-regression.md) keeps the complete measured boundary, raw proof identities, GUI results and limitations.

The independent review of source, tests and raw evidence has a PASS result with no findings that need action.

For the bounded scope in Exit 3, the API no longer needs FreeCAD or Qt.
The result supplies evidence for equal results in Exit 2 and evidence for the bounded scope of the B16 workflow in Exit 1.
It accepts no whole exit. Phase 7 stays Open at 0/4, with all four exits Pending.
D-P6-008, all conditions to compare results and remove legacy paths, and recorded limitations stay in full.
This task does not change the relations between station values and points, turn directions, `build_platform_core`, persistence or output contracts.

The entries below preserve the publication evidence for PRs #71, #70 and #69.
Their product merges are complete. They do not select the next work item.

## `build_concentric_core` migration — 2026-09-08

The implementing agent merged PR #70 at `1be47bf38fa00692c60ea2fc03f91ab174801bf2`.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result with authority from D-GOV-004 and the Phase 7 scope.

The complete function source is now in `tracktemplate.domain.alignment`.
Its result contains XY values and the same metadata in the same sequence.
The small B15 compatibility object `_ConcentricCoreAdapter` changes only the points to FreeCAD `App.Vector` values.
The actual `run_macro` and `prepare_track_alignment` callers use this route.
The [API instructions](../contracts/phase7-concentric-core.md) define the bounded scope of the contract.

The API preserves all 184 complete results from checks against B14/B15 and nine invalid cases.
Eight selected test sets with standalone Python and four proofs with qualified FreeCAD have PASS results.
All six new FreeCAD human-interface samples have PASS results.
The checks compare all result data and give equal results for all fourteen new and preserved workflow records.
The complete `build_concentric_core` measurement includes creation of points and the change to FreeCAD `App.Vector` values.

The independent review of source, tests and raw evidence has a PASS result.
The [evidence record](../benchmarks/2026-09-08-phase7-concentric-core-regression.md)
keeps the exact source, raw proof identities and applicable workflow and resource limitations.

For the bounded scope in Exit 3, this result reduces the dependency on B15 to calculate results.
It supplies evidence for equal results for Exit 2 and workflow evidence for the bounded scope in Exit 1.
It accepts no whole exit. Phase 7 stays Open at 0/4.
D-P6-008 stays in full. Station mapping, the remaining migration scope,
paths to compare results and conditions to remove legacy paths stay unchanged.

The entries below preserve the evidence from publication of PRs #70 and #69.
Their product merges are complete. They do not select the next work item.

## `clothoid_exit_displacement` migration — 2026-09-08

The implementing agent merged PR #69 into protected main at
`8b06de6bff3901e35548a1be79ebe9f68bb4fc57`.
The project owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result under D-GOV-004.
D-P7-001 keeps Phase 7 Open with the same bounded scope and conditions.

The repository shows one caller of `clothoid_exit_displacement` in `build_concentric_core`.
The endpoint calculation was missing from `tracktemplate.api`.
The exact candidate moves that endpoint calculation with no change in its sequence of operations, inputs or diagnostics.
The B16 Generate/Replace caller now selects it with the four functions already selected from `tracktemplate.api`.
The [API instructions](../contracts/phase7-clothoid-exit.md) define the bounded scope.

The tests with standalone Python and qualified FreeCAD have PASS results.
All twelve new FreeCAD human-interface samples have PASS results. The tests that compare their workflow results show equal values.
The two preserved samples with `--route legacy` also give equal results in these checks.
The checks do not use their time values.
The [evidence record](../benchmarks/2026-09-08-phase7-clothoid-exit-regression.md)
keeps all values, failure classifications and limitations.
The independent review of source, tests and raw evidence has a PASS result for this bounded scope.

This task supplies more evidence for Exits 2 and 3 and bounded workflow evidence for Exit 1.
It accepts no exit. Station mapping and the remaining Core migration scope stay outside this task.
The higher time and memory observations give no acceptance of product performance.
D-P6-008 stays in full. All paths that the tests compare and their removal conditions stay in full.

The previous `main_circle_centre` entry below keeps its evidence from the publication of PR #69.
Its product merge is complete. The next merge decision concerns this new exact candidate.

## `main_circle_centre` migration — 2026-09-08

D-P7-001 authorises this Level 2 exact candidate after the merge of PR #68.
The B16 Generate/Replace caller now uses `tracktemplate.api.main_circle_centre`.
This API calculates the same results with the same sequence of operations and diagnostics.
The product validates four functions and the APIs that their callers use.
If this operation has an error, the product puts the previous values back.
The [API instructions](../contracts/phase7-main-circle-centre.md) define the bounded scope.

Standalone and qualified FreeCAD checks have PASS results.
All 14 completed FreeCAD human-interface samples have PASS results from the tools that compare workflows.
This includes the different samples for `--route legacy`.
The independent review of source and evidence has a PASS result for this bounded scope.
The [evidence record](../benchmarks/2026-09-05-phase7-main-circle-centre-regression.md)
keeps the values, interruption, failure classifications and limitations.
The different wall times and higher memory values from the exact candidate give no acceptance of product performance.

The evidence needs equal API and caller results, with no change in the subsequent operations that make shapes.
Data about shapes alone cannot prove that complete shapes or output bytes are equal.
The API calculates a new result each time. It does not use warm reuse.

This exact candidate gives evidence for Exits 2 and 3. It accepts no exit.
Phase 7 stays Open at 0/4. D-P6-008 and all conditions for the B14 and B15 routes and their removal stay in full.
After validation of the technical documents and publication, CI must give a PASS result for the exact candidate.
Then the next owner decision is the product merge.

## Phase 7 exit conditions — not admitted

These are the four original programme criteria from accepted plan revision
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`.
The closeout holding record restored their wording. D-P7-001 opens the phase.
It does not change these criteria or narrow them to the first task.

| Exit condition | Status |
| --- | --- |
| Core layouts can be created, edited, saved, reopened, validated, and exported through modular paths. | Pending |
| Accepted B14/B15 geometry, station mapping, identities, ordering, and metadata remain equivalent. | Pending |
| Domain calculations for this family have no FreeCAD/Qt dependency or reverse adapter import. | Pending |
| Legacy core-layout paths have either been safely retired or have a documented blocker and removal gate. | Pending |

## Carried authority and live risks

[D-P6-008](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-4-deferral-panel)
stays unchanged in full. The [current decision register](gate-decisions.json)
keeps that complete decision for its live obligation.
The unchanged bounded Entry/Exit improvement obligation stays mandatory
before Phase 10 beta acceptance.

Richard keeps accountability and owns delivery
until a named Phase 10 integration owner takes delivery responsibility.
Independent review and Richard's acceptance are mandatory. Numerical budgets
or improvement on another workload do not give the required evidence for this obligation.
If it stays unmet, Richard must not accept beta.

All 24 records in [risks.json](risks.json) keep their Phase 6 duties and
status. PR-15 and QA-R04 stay High/Open/Mitigate/Partial.
The existing backup schedule applies to later valuable local evidence.
Normal per-slice checks, comparison paths, invariant 8, and all retirement
conditions still apply. The sequencing exception does not complete Stage M4.
D-P5-002 and the PR-14 reopen trigger remain mandatory for later composition.

The Phase 6 closeout preserves D-GOV-011 and its negative evidence.
Its product direction stays stopped. Do not repeat stopped experiments.
Do not change their measurement rules.

The bounded output stays private-development. Project status stays `unknown`.
This record gives no phase exit, performance, production, legacy removal,
packaging, or release acceptance.

<a id="phase-7-opening-panel"></a>

## Phase 7 opening panel

Decision: **D-P7-001 — Open Phase 7.** Richard accepted the decision on
2026-09-05. The source state is clean protected main
`c9afb55a4caba4322b9e750397ad46d008b15100` after PR #67.

Richard is the project owner and panel chair. The opening-record owner presents
the change. The independent QA/risk reviewer is `/root/alignment_review`.
The reviewer authored no maintained opening file.

The panel recommendation is **Proceed with bounded conditions**. There is no
unresolved dissent. The decision agrees with the applicable authority and evidence.

The panel reviewed the four original criteria, D-P6-008 in full, the frozen
Phase 6 closeout, all 24 live risks, and the accepted recovery record.
It also reviewed the Chief of Staff assessment and the actual calculation,
caller and comparison tests. The assessment has SHA-256
`bb951a17534a199daeacc6e9334bbce6ccf1ff13d5c1dd7897c88ddd07a88d20`.
The product source that the assessment examined is unchanged. The panel uses
the completed recovery evidence and applicable admission reviews. It does not
do another experiment or restore drill.

The first Level 2 task must move `main_circle_centre` and its necessary pure
helper calculation into the modular package. It must route the B16
Generate/Replace caller through that calculation.

The function has one product caller in `run_macro` from the legacy path.
The modular API does not include the function.
`tests/validate_phase1_alignment.py` supplies the recorded numerical result.
`tests/freecad_validate_phase3_transition_slice.py` supplies comparisons of the
main and secondary alignments after the calculation. Completion of this task
gives evidence for Exits 2 and 3 and some evidence for Exit 1. The task accepts
no exit and does not narrow the phase.

| Accountable owner | Bounded condition and deadline |
| --- | --- |
| Opening-record owner | Before product implementation, integrate the exact-green opening alignment. Before product implementation, synchronise clean protected main. Preserve 0/4 and all four criteria. |
| Product Technical Lead | Before publication, preserve numerical operation order, units, frames, signs, tolerances, diagnostics and tuple results. Keep the calculation and actual caller route within the accepted task. |
| Composition and QA owners | Before publication, show complete, recoverable binding before workflow launch. Preserve the frozen Phase 3 three-function contract and development comparison route. Show numerical parity and applicable qualified-host, GUI, history, copied-document reopen and output behaviour. Preserve the D-P5-002/PR-14 reopen trigger. |
| Performance owners and Richard | Apply normal per-slice cold/warm regression checks to the changed path. Preserve the measurement rules and stopped directions. Give this task no D-P6-008 acceptance credit. The original obligation stays mandatory before Phase 10 beta acceptance. |
| Recovery, provenance and migration owners | Keep current risk duties, the recovery schedule, valuable evidence, comparison paths and legacy-retirement conditions. The accepted recovery proof stays applicable. |

All 24 risk records and their control effectiveness stay unchanged. PR-15 and
QA-R04 stay High/Open/Mitigate/Partial. PR-13 and PR-17 keep their recovery
and persistence duties. PR-18 keeps its legacy-removal gate. Product validation
for this candidate is not complete. The governance change is larger than the
product change because this Level 3 task changes phase-opening and execution authority.

Stop the product task for a wider caller closure, changed railway semantics,
or an unresolved compatibility decision. Also stop for unavailable mandatory
proof or a repair outside the accepted scope. Do not replace the task with station migration,
new state or UI, a generic routing framework, or a performance investigation.
Keep B14 and B15 unchanged. Do not remove a legacy path. The later product pull
request needs another owner decision for integration.

### Owner decision

The exact accepted owner statement is:

> I open Phase 7 at 0/4 for its existing Core alignment, station and multiple-track migration scope, preserving its four exit criteria and D-P6-008 in full. I authorise the directly dependent Level 3 opening alignment and its exact-green protected-main integration. Once main is clean and synchronised, I authorise the bounded Level 2 main-circle-centre extraction and routing described in this brief through implementation, applicable validation, independent review and publication. Preserve all comparison and legacy-retirement conditions. This decision accepts no Phase 7 exit or performance result and grants no output or release clearance.

The decision opens the phase at 0/4. It authorises the stated sequence and
bounded task through publication. It accepts no phase exit or performance
result. Output stays private-development and project status stays `unknown`.

## Preserved historical links

<a id="visible-recovery-state-workflow-migration"></a>

The historical visible-recovery-state record moved unchanged, except for
navigation links, to the
[Phase 6 closeout](../history/phase-closeouts/PHASE6_CLOSEOUT.md#visible-recovery-state-workflow-migration).

<a id="worktree-retirement-workflow-migration"></a>

The historical worktree-retirement record moved unchanged, except for
navigation links, to the
[Phase 6 closeout](../history/phase-closeouts/PHASE6_CLOSEOUT.md#worktree-retirement-workflow-migration).

<a id="phase-6-exporter-fault-model-clarification-panel"></a>

The historical D-P6-004 record is preserved in the
[Phase 6 closeout](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exporter-fault-model-clarification-panel).

<a id="tt-doc-001-documentation-architecture-panel"></a>

The historical TT-DOC-001 record is preserved in the
[Phase 6 closeout](../history/phase-closeouts/PHASE6_CLOSEOUT.md#tt-doc-001-documentation-architecture-panel).
