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
| What changed | Opening PR #68 is integrated. The bounded candidate moves `main_circle_centre` into the modular package and routes the existing B16 Generate/Replace caller through it. |
| What now works | Standalone, qualified FreeCAD and GUI comparisons passed for this candidate. The independent source and evidence review passed. |
| Limitations/findings | Timing and memory observations give no performance acceptance. Phase 7 stays at 0/4. D-P6-008, all risks and all legacy-retirement conditions remain. |
| Owner decision | Richard authorised the bounded task through validation, independent review and publication. Product integration needs a separate owner decision. |
| Next action | Complete document validation and publication. Bring the exact-green product pull request to Richard for its integration decision. |

## Main circle centre migration — 2026-09-08

D-P7-001 authorises this Level 2 candidate after opening PR #68 was integrated.
The existing B16 Generate/Replace caller now uses the modular
`main_circle_centre` calculation. The domain API keeps the inherited formula,
operation order and diagnostics. The product composition validates four
bindings and restores their previous values after a binding failure.
The [contract](../contracts/phase7-main-circle-centre.md) defines this boundary.

Standalone and qualified FreeCAD checks passed. All 14 completed GUI samples
passed the existing workflow comparisons, including separate legacy comparisons.
The independent source and evidence review passed for this bounded task.
The [regression record](../benchmarks/2026-09-05-phase7-main-circle-centre-regression.md)
keeps the measurements, interruption, preserved failures and limits.
The wall-time spread and higher candidate memory observations support no
performance acceptance claim.

Shape summaries need analytical and caller parity with unchanged downstream
construction. They do not alone prove complete geometry or exported byte equality.
The centre has no cache. Repeated calculation is separate from warm reuse.

This candidate contributes to Exits 2 and 3. It accepts no exit.
Phase 7 stays Open at 0/4. D-P6-008 and all comparison and retirement conditions
stay in full. After document validation, publication and exact-green CI,
the next owner boundary is the separate product integration decision.

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
