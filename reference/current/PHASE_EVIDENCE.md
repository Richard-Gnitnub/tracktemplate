# Phase 9B Opening Record

Status: **Phase 9A is closed at 4/4 under D-P9-010 for its frozen reference-only
scope. Phase 9B is Open at 1/6 under D-P9-012. Only Exit 9B-2 is Evidenced
and owner-accepted. The other five exits stay Pending.**

The [Phase 9A closeout](../history/phase-closeouts/PHASE9A_CLOSEOUT.md),
[decisions](../history/phase-closeouts/PHASE9A_GATE_DECISIONS.json) and
[risk snapshot](../history/phase-closeouts/PHASE9A_RISKS.json) preserve its history.
The [project plan](../PROJECT_PLAN.md) owns current phase and exit status.

## Current owner view

| Field | Current position |
| --- | --- |
| Current state | Phase 9A stays closed at 4/4 under [D-P9-010](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-closeout-panel). Phase 9B is Open at 1/6 under [D-P9-012](#phase-9b-exit-2-acceptance-panel). Only Exit 9B-2 is Evidenced and owner-accepted on 2026-10-11. The other five exits stay Pending. |
| What changed | The owner accepts the reviewed evidence for timber and chair decisions and record identities across representative migrated Core workflows. The six exit criteria stay unchanged. This decision adds no product behaviour. |
| What now works | The accepted Phase 7 and Phase 8 workflows supply evidence with PR #154, PR #155 and PR #160. This evidence covers the bounded edit, save/reopen, validation and export scope. |
| Limitations/findings | The [admission panel](#phase-9b-exit-2-acceptance-panel) keeps representative-workflow limits, selected export scope, normalisations, the observed SVG difference and `production_ready=False`. All 24 risk duties, D-P6-008 Deferred — unmet and TERM-R04 stay. Output stays private-development and project status stays `unknown`. |
| Owner decision | D-P9-012 accepts only Exit 9B-2 on the reviewed evidence and bounded conditions. All other exits and production conditions stay. The Phase 9A closeout and earlier decisions keep their accepted limits. |
| Next action | Complete only the necessary Level 3 alignment and its usual validation and independent review. After CI gives a PASS result for the exact PR head, publish the draft PR. Do not merge or start further development. |

<a id="phase-9b-exit-2-acceptance-panel"></a>

## D-P9-012 Phase 9B Exit 2 acceptance panel — 2026-10-11

**Decision boundary:** Richard accepts only Exit 9B-2 on the reviewed evidence
and bounded conditions. The accepted source is protected `main`
`ee63f47c64b15d159bfd3f8c9a6ea13ddd62b510` after PR #160.
CI run `38133332735` passed for that exact source.

Phase 9B is Open at 1/6. Exit 9B-2 is Evidenced and owner-accepted on
2026-10-11. Exits 9B-1 and 9B-3 through 9B-6 stay Pending.
All six exact criteria stay unchanged. Phase 9A stays closed at 4/4 for its
frozen reference-only scope.

**Exact owner instruction:**

> As project owner, I accept Phase 9B Exit 2 on the reviewed evidence and bounded conditions. Authorise the necessary Level 3 decision and repository alignment to an exact-green draft PR. Preserve all exclusions and remaining exit criteria. Do not merge or begin further development.

**Accepted evidence:** The decision uses the accepted
[Phase 7](../history/phase-closeouts/PHASE7_CLOSEOUT.md) and
[Phase 8](../history/phase-closeouts/PHASE8_CLOSEOUT.md) evidence with
[PR #154](https://github.com/Richard-Gnitnub/tracktemplate/pull/154),
[PR #155](https://github.com/Richard-Gnitnub/tracktemplate/pull/155) and
[PR #160](https://github.com/Richard-Gnitnub/tracktemplate/pull/160).
These results show that logical timber and chair decisions and
record identities stay stable in the reviewed representative migrated Core workflows.
They do not supply evidence for all configurations or one continuous GUI workflow.

| Exit 9B-2 duty | Accepted evidence and limit |
| --- | --- |
| Edit | D-P7-003, D-P7-005, D-P8-004 and D-P8-005 accept the applicable parameter, identity, timber and record evidence. PR #154 and PR #155 add chair input change, change-back, stale rejection and reversible analysis. The chair tests inject values at existing extractor boundaries. They add no editing command. |
| Save/reopen | The accepted Core lifecycle and PR #155 preserve payload, display and reuse after save/reopen. PR #160 preserves the exact current chair, timber, configuration and production-record state. |
| Validation | Accepted Core range, topology, timber and pre-production checks stay applicable. PR #160 preserves nonempty current chair state through selected production preflight and export-bound checks. This preflight does not validate final chair solids or physical fit. |
| Export | Accepted Phase 7 plain-line and Phase 8 turnout/crossover evidence stays applicable. PR #160 adds native and actual GUI selected SVG and CSV export with persistence. These outputs contain cutting outlines and records, not chair solids or every production format. |

The chair-specific proof covers the supported turnout and crossover entity
kinds. `TO-001` contains 168 chair positions, 40 timbers and eight production records.
`XO-001` contains 355 chair positions, 86 timbers and seven production records.
The qualified host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
No new functional check or visual capture is necessary for this alignment.

The readiness record is `tmp/phase9b-after-160/exit9b2-readiness.json` in the
primary repository, SHA-256
`64eddabc098f55ceca5d7a00b45ba207a2f9bb2bf1a95719abcbc35bcc9a3380`.
It records the accepted source comparison, proof identities and exclusions.
The PR #160 validation receipt has SHA-256
`d8a56d8b3da3d199e8e46a8321eeb674518b5c7c0b03c10daf6bef1085d0ce52`.
Its independent quality-review receipt has SHA-256
`74b721c71903f8f488eb5351725e6d31e9705ec24a61581a8cebc21a5c29be4f`.
The GUI result has SHA-256
`7e3ef08b4b3827a4c63583b6e3b4a50ea14c1dbb3190052527791ddc69f11bd6`.
The final GUI candidate binding has SHA-256
`c1732456cb9e0a1d4614112c6c2a88db3d55b87351f18ed39685ea04f1268455`.

**Safety/risk panel:** Richard is the project owner, panel chair and accepting
authority. `/root` presents the alignment. Read-only reviewer
`/root/after158_next_outcome` examined the evidence and bounded admission.
This reviewer did not author the implementation. The reviewer previously
selected the bounded outcome and reviewed PR #160. The reviewer also examined
admission and reviewed backup evidence.

`/root/aperture_native_tests` supplied a risk assessment but authored the
PR #160 tests. That assessment supplies no independent implementation acceptance.
The agents share one team and workspace. This is not external organisational
independence.

The recommendation is **Proceed with bounded conditions**. The panel receipt records
`"unresolved_dissent": []`. All 24 risk states, severities, owners, deadlines,
treatments and controls stay unchanged. No risk closes. Each risk owner keeps
the obligations and deadline in the [current register](risks.json).

PR-01 and QA-R03 keep representative-workflow and wider coverage duties.
PR-16 keeps input-change and invalidation duties. PR-17 keeps persistence and
recovery duties. PR-09 keeps output controls. PR-13 keeps the backup and restore
interval.

PR-15 and QA-R04 keep performance duties. PR-22 keeps independent
acceptance control. PR-10 and PR-18 keep comparison and removal conditions.
The applicable chair evidence and rights risks keep their production duties.

PR-09 stays Critical/Open/Partial. PR-13 stays Critical/Open/Effective for its
current scope. PR-17 stays Critical/Open/Partial.

The independent risk receipt is
`tmp/phase9b-exit2-admission/risk-panel-input.json`, SHA-256
`3cb60bf2871d1296b6ed782a2d80ee01bbf2f0de3f3781118dce8cb0e9648e51`.
It shows all 24 duties and the bounded recommendation. The earlier
53-root snapshot, core packet and safe unmount passed their checks.
Physical separate storage stays unverified. The new alignment worktree and
later receipts are outside that earlier snapshot.

**Preserved findings and exclusions:** Keep the permitted normalisations and
observed SVG serialisation difference. This decision accepts no new numerical
tolerance or byte-equivalence claim. Warnings, `production_ready=False`, failed
evidence, support windows and legacy-removal conditions keep their meanings.
Normal per-change validation stays mandatory.

Exit 9B-5 stays Pending. The source finding that a later Core export task
failure can leave partial successful output stays unresolved.
The Phase 9B export/output owners keep that duty. This decision adds no
fault proof or implementation and gives no wider rollback acceptance.

Product geometry, package bytes, the 113-entry register and numerical limits
stay unchanged. This decision accepts no physical fit, preload, retention,
manufacturing capability, production package, output, rights, performance
result or release. D-P6-008 stays Deferred — unmet. TERM-R04 stays open.
Output stays private-development and project status stays `unknown`.
All earlier acceptance and legacy-retirement conditions stay.

**Publication boundary:** Complete only the necessary Level 3 alignment,
Documentation Review lifecycle and validation. After CI gives a PASS result for the exact PR head,
publish the draft PR. Do not merge or start further
development. This decision closes no phase and accepts no other exit.

<a id="phase-9b-opening-panel"></a>

## D-P9-011 Phase 9B opening panel — 2026-10-09

**Decision boundary:** After his acceptance of Phase 9A closeout, Richard authorises
Phase 9B opening at 0/6. All six exits stay Pending. This decision changes
only phase status. The existing six criteria and production conditions stay.

**Exact owner instruction:**

> Im happy to roll into 9b iot maintain flow.

The source stays protected `main` `69ef5be79922f694c9019bbd3e33b919c882235e`
with the accepted D-P9-010 closeout conditions. The owner instruction above
supplies separate opening authority. It does not change the frozen Phase 9A
acceptance or accept any Phase 9B result.

**Safety/risk panel:** Richard is the panel chair and decision authority. `/root` supplies this
alignment. Read-only reviewer `/root/phase9a_closeout_review` examines the
opening against the accepted closeout, six unchanged criteria and all 24 risks.
The reviewer is separate from the alignment author. The agents work in one team
and workspace. This is not external organisational independence.

The recommendation is **Proceed with bounded conditions**. No risk closes or
changes owner, deadline, treatment or control. The panel records no unresolved
dissent. The [Phase 9A closeout](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-closeout-panel)
keeps the reviewed recovery limits and conditions. Each risk owner keeps the
deadline in the [current risk register](risks.json).

**Resulting authority:** Phase 9B is Open at 0/6. All six exits stay Pending.
The owner authorises the necessary Level 3 alignment and a draft PR.
CI must give a PASS result for its exact head.
Do not merge. This cycle selects no product implementation.

Opening accepts no physical fit, preload, retention, manufacturing capability,
production package, output, rights, numerical tolerance, performance result or release.
D-P6-008 stays Deferred — unmet. TERM-R04 stays open. All accepted limits,
the 113-entry register and legacy-retirement conditions stay. Output stays
private-development and project status stays `unknown`.

## Phase 9B exit conditions

All six criteria stay unchanged. Only Exit 9B-2 is Evidenced — owner-accepted
on 2026-10-11 under [D-P9-012](#phase-9b-exit-2-acceptance-panel).
Exits 9B-1 and 9B-3 through 9B-6 stay Pending.

| Phase 9B exit | Original exit | Exact criterion |
| --- | ---: | --- |
| 9B-1 | 1 | Each release-candidate production format has deterministic repeat evidence for representative inputs. Preserved B14/B15 behaviour has legacy/new equivalence evidence. New procedural chair geometry uses accepted 9A definition and independent engineering evidence under D-P9-005. It does not use five-box equality. |
| 9B-2 | 2 | Timber and chair decisions and record identities stay stable across edit, save/reopen, validation and export across migrated Core trackwork. |
| 9B-3 | 6, package clearance | Each chair and support family necessary for the agreed TrackTemplate Core release candidate is complete across migrated trackwork. The accepted S1 package has an explicit licence. It has no dependency with `NC`, `NOASSERTION`, reference-only or unknown status. It has no dependency that is incompatible with the `project-cleared` commercial/publication path. The same applicable rights gate controls each other package. Before production, publication, redistribution or commercial clearance, each output-affecting Templot-derived input needs one of three dispositions. These are independent confirmation, replacement by project-cleared evidence, or an explicit compatible rights and provenance disposition. After an input change, each affected definition, geometry, pilot and output check of the final production package must give a PASS result. |
| 9B-4 | 7 | Representative output manifests reproduce the complete package/dependency classification. They cannot claim `project-cleared` if an applicable input is replaced by a restricted or unresolved source. |
| 9B-5 | 8 | Export failure cannot replace only part of an accepted output set or corrupt the editable model. |
| 9B-6 | 9 | Editing and end-to-end performance meet the provisional budgets derived from measured baselines. |

## Continuing duties and risks

[D-P6-008](../history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-4-deferral-panel)
stays in full in the [current decision register](gate-decisions.json). Its
unchanged bounded Entry/Exit improvement obligation remains mandatory
before Phase 10 beta acceptance. Richard keeps accountability and delivery
ownership until a named Phase 10 integration owner takes responsibility.
Independent review and Richard's acceptance remain mandatory. An
improvement on another workload cannot satisfy this obligation. Beta
acceptance is blocked while it remains unmet.

The 24 [live risks](risks.json) keep their owners, deadlines, treatments and
control effectiveness. PR-13 keeps the backup and restore cadence. PR-09
keeps output private-development. PR-10 and PR-18 keep the duplication and
removal gates. PR-15 and QA-R04 keep the performance duty.

PR-17, PR-01,
QA-R03 and PR-22 retain their recorded duties. No risk disposition changes.

TERM-R04 remains open. The Phase 8 product evidence remains bounded by its
accepted conditions. Normal per-slice comparison, dependency and recovery
checks remain mandatory for later changes. No wider migration-family
completion, performance result, production output, release or legacy-path
removal is accepted. Project status remains `unknown`.

## Chair results after input changes — 2026-10-09

This Level 2 correction supplies evidence for Exit 9B-2 and PR-16.
The [B16 function](../../tracktemplate/application/chair_analysis_signature.py)
uses input values and identities without a change to calculate `_chair_geometry_signature`.
B16 calculates chair results with the same method as B15. Previous B15 results become `Stale`.
A person must select `Analyse` before B16 can make chairs.

The [regression test outside FreeCAD](../../tests/validate_chair_analysis_signature.py)
and [FreeCAD regression test](../../tests/freecad_validate_chair_analysis_signature.py)
give PASS results. The qualified host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
The copies for `XO-001` and `TO-001` contain 355 and 168 chair positions.

The tests examine inputs that stay the same, inputs that change and inputs that change back.
They also examine save/reopen and Undo/Redo. The software stops before it makes chairs
if the results in the file do not agree with the inputs.
After an incorrect input, the results in the file and Undo/Redo stay the same.
The results agree in all details with those that the frozen B15 functions calculate.

The tests supply changed records to the functions. They add no command to change records.

Phase 9B stays Open at 0/6. All six exits stay Pending.
This evidence gives no acceptance for other migration, product performance, physical fit or production output.
The accepted geometry, 113-entry register and all production conditions stay the same.

## `Analyse` preserves document state — 2026-10-09

This Level 2 change supplies evidence for Exit 9B-2 and the
[document/history requirement](../VALIDATION.md#observed-regression-obligations).
In B16, `Analyse` preserves the document when inputs, settings, recorded results
and diagnostic display are current.
The [adapter](../../tracktemplate/compatibility/transition_workflow.py) reads
rail and timber records again before it returns a copy of the recorded result.
B16 uses the B15 operation for changed settings, data that are not complete and diagnostic display repairs.
The frozen Phase 1 tests keep the earlier defect evidence.

The [test for standalone Python](../../tests/validate_chair_analysis_reuse.py) and
[FreeCAD test](../../tests/freecad_validate_chair_analysis_signature.py) give PASS results
without FreeCAD and in the qualified host profile without a visible FreeCAD window.
The copies for `XO-001` and `TO-001` contain 355 and 168 chair positions.
When `Analyse` operates again, it keeps recorded bytes, object identities, shapes and document history without changes.
This operation does not write metadata, make a display, call `recompute` or start a transaction.

Persistence preserves this result. Changed inputs keep one command with `Undo` and `Redo`.
Missing diagnostic layers cause repair through the B15 operation.

This change does not complete chair migration or correct recorded timing measurements.
For an unchanged result, the software reads rail and timber records one time.
For changed inputs, the software can read those records two times.
The recorded result gives data from the previous calculation.
When B16 uses a result again, it returns no timing measurements.

Phase 9B stays Open at 0/6, with all six exits Pending.
This evidence gives no acceptance for performance, physical fit or production output.
Geometry, the 113-entry register and all accepted boundaries stay the same.

## S1 base shape from drawing No. 4 — 2026-10-11

The project owner selected LMS drawing No. 4, `S.I./95R`, as the “provisional prototype target” for this work.
The project owner also authorised “separate nominal-base development”.
The production conditions in [S1-07 and S1-08](../phase-evidence/S1_PILOT_PLAN.md#decision-register) stay Pending.
This Level 2 change supplies evidence for Exit 9B-1 and for a subsequent assessment of inputs for Exit 9B-3.

The [software](../../tracktemplate/domain/chair_base_nominal.py) and
[FreeCAD adapter](../../tracktemplate/adapters/freecad/chair_base_nominal_exact.py)
make one `Part.Face` from specified length inputs.
Its outer shape has four straight parts and four circular corners.
For No. 4, the dimensions are `14.5 in × 8 in`, with `R1 in` through `90°` at each corner.
The drawing shows `1″R` at two top corners.

With the same value for all four corners, the calculated area agrees with `115.14 SQ INS` at the precision that No. 4 shows.
This result gives evidence for the four equal corner values. It does not supply a dimension for each corner.
The software puts the middle of the shape at `(0, 0, 0)`, with `Z=0` at all points.
This local position does not give the position of the chair in relation to a rail.

The [standalone Python test](../../tests/validate_phase9b_chair_base_nominal.py) and
[FreeCAD test](../../tests/freecad_validate_phase9b_chair_base_nominal.py) give PASS results.
Tests with the qualified host profile also give PASS results for the local No. 4 display and persistence.
The file `tmp/nominal-base/final/No4-native-visual-proof.json` contains the detailed evidence.
The base tests give PASS results without changes to their frozen reference path.

This result contains no holes or thickness.
It supplies no `ChairDefinition`, rail position, physical fit, production dimensions or changes to dimensions for production.
It gives no acceptance for a positive rights claim.
The 113-entry register and frozen Phase 9A paths stay the same.
The output stays in private-development status. Phase 9B stays Open at 0/6, with all six exits Pending.

## S1 base holes from drawing No. 4 — 2026-10-11

This Level 2 change adds three holes to the bottom of the [No. 4 base](#s1-base-shape-from-drawing-no-4--2026-10-11).
It supplies evidence for Exit 9B-1 and for a subsequent assessment of inputs for Exit 9B-3.
The [software](../../tracktemplate/domain/chair_base_nominal.py) and
[FreeCAD software](../../tracktemplate/adapters/freecad/chair_base_nominal_exact.py) make one `Part.Face` with circular holes.
The software rejects holes that touch the outer edge or a different hole.

The [standalone Python test](../../tests/validate_phase9b_chair_base_nominal.py) and
[FreeCAD test](../../tests/freecad_validate_phase9b_chair_base_nominal.py) give PASS results.
Their dimensions do not come from drawing No. 4.
The tests of the base without holes and of the frozen Phase 9A base also give PASS results.
Tests with the qualified host profile give PASS results for the local No. 4 display and persistence.
The file `tmp/nominal-apertures/final/No4-underside-native-visual-proof.json` contains the detailed evidence, source identity and input limitations.

For the two holes on one side, the local evidence uses equal distances from the middle of that side.
Drawing No. 4 gives no dimension for each distance.
The source inputs and output files stay local. Their rights state stays unknown.

The shape has no thickness or vertical surfaces at the holes. It is not a complete chair.
It gives no acceptance for physical fit or production output.
The “113-entry register”, frozen Phase 9A paths and accepted conditions stay the same.
Output stays in private-development status. Phase 9B stays Open at 0/6, with all six exits Pending.

## Core export checks before final files — 2026-10-11

This Level 2 change supplies part of the work for Exit 9B-5 after integration of PR #161.
The [new operation](../contracts/core-layout-export-staging.md) prepares all
format files in the plan and CSV before it writes a final file.
An error during this preparation changes no output from a previous operation.
The result counts only files written to their final paths.
If a later final-file write gives an error, the operation does not write the
prepared CSV to the output directory. A CSV from a previous operation stays
without a change.

The [standalone test](../../tests/validate_core_export_staging.py) and
[FreeCAD test](../../tests/freecad_validate_core_export_staging.py) examine
the changed error conditions, completed output and document preservation.
The qualified FreeCAD test gives a PASS result for DXF, SVG, STL, STEP and CSV
comparisons.

The GUI proof uses Core Generate with the accepted copied fixture.
It writes 14 files when all output operations are complete.
An injected final STEP error writes no new final files and preserves three
previous targets and an unrelated file.
The GUI shows zero completed files and 13 outputs that did not complete.
The document keeps nine objects and gives PASS results for save/reopen checks.
The Phase 7 API and its diagnostic for incomplete output stay available.

The host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
The GUI record is
`benchmark-output/freecad-bridge/phase7-core-layout-export-workflow-runs/20261011T124624882644Z-modular/run.json`,
SHA-256 `b0345b70700bf52a80d1899837ced64c8d311246a29c45f9e5a5db2f6b6bbc5c`.
The native record is `tmp/core-export-staging/native-runs/20261011T124347568840Z/result.json`,
SHA-256 `cef975bab1286d434fdd7fd0967b35fa91e6edafd6d7e28cde0c9752ce2755c6`.
The two records keep their proof limits. Local source and copied-fixture checks
give PASS results. No operator document changes.

This result does not meet the complete output requirement in the
[architecture](../ARCHITECTURE.md#6-export-adapter).
An error during a later file write can keep previous final files in the
output directory. The conditions for an incomplete output set and its recovery
stay unresolved for Exit 9B-5. D-P6-003 and D-P6-004 do not change.

`dispatch_freecad_export` does not report some temporary-object cleanup errors.
Those errors stay outside the demonstrated document-preservation conditions
and stay unresolved for Exit 9B-5.
The selected-export route, geometry, numerical limits and 113-entry register
do not change. There is no new production, rights or performance acceptance.

D-P9-012 continues to apply. Phase 9B stays Open at 1/6, with five exits Pending.
Phase 9A stays closed for its frozen reference-only scope. Output stays
private-development and project status stays `unknown`.

## Phase 9A historical links

These links keep earlier references available at the frozen evidence owner.

<a id="phase-9a-exit-3-acceptance-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-exit-3-acceptance-panel).

<a id="phase-9a-exit-2-acceptance-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-exit-2-acceptance-panel).

<a id="phase-9a-reference-comparison-criteria-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-reference-comparison-criteria-panel).

<a id="phase-9a-exit-1-acceptance-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-exit-1-acceptance-panel).

<a id="phase-9-chair-evidence-model-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9-chair-evidence-model-panel).

<a id="phase-9-programme-alignment-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9-programme-alignment-panel).

<a id="phase-9a-opening-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-opening-panel).

<a id="phase-9a-research-sequencing-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-research-sequencing-panel).

<a id="phase-9a-exit-4-admission-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-exit-4-admission-panel).

<a id="phase-9a-2-quantity-check-repair--2026-10-03"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-2-quantity-check-repair--2026-10-03).

<a id="phase-9a-s1seat-research-proof--2026-10-03"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-s1seat-research-proof--2026-10-03).

<a id="phase-9a-key-research-proof--2026-10-03"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-key-research-proof--2026-10-03).

<a id="phase-9a-s1-baseplinth-research-proof--2026-10-04"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-s1-baseplinth-research-proof--2026-10-04).

<a id="phase-9a-s1-outer-jaw-research-proof--2026-10-04"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-s1-outer-jaw-research-proof--2026-10-04).

<a id="phase-9a-s1injaw-research-proof--2026-10-04"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-s1injaw-research-proof--2026-10-04).

<a id="reference-only-s1-assembly-proof--2026-10-07"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#reference-only-s1-assembly-proof--2026-10-07).

<a id="reference-only-s1-model-comparison-proof--2026-10-07"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#reference-only-s1-model-comparison-proof--2026-10-07).

<a id="s1-checks-with-reference-only-inputs--2026-10-07"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#s1-checks-with-reference-only-inputs--2026-10-07).

<a id="l1-checks-with-reference-only-inputs--2026-10-07"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#l1-checks-with-reference-only-inputs--2026-10-07).

<a id="freecad-1-1-4-coin4-0-10-qualification-panel"></a>
[Phase 9A evidence](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#freecad-1-1-4-coin4-0-10-qualification-panel).

## Phase 8 historical links

The following anchors keep existing links navigable. Each link identifies
the frozen record that owns the evidence.

<a id="phase-8-opening-panel"></a>
[Phase 8 opening](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-opening-panel).

<a id="phase-8-exit-1-acceptance-panel"></a>
[Phase 8 Exit 1](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-exit-1-acceptance-panel).

<a id="phase-8-exit-2-acceptance-panel"></a>
[Phase 8 Exit 2](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-exit-2-acceptance-panel).

<a id="phase-8-exit-3-admission-panel"></a>
[Phase 8 Exit 3](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-exit-3-admission-panel).

<a id="phase-8-exit-4-admission-panel"></a>
[Phase 8 Exit 4](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-exit-4-admission-panel).

<a id="phase-8-worktree-retirement-october-1"></a>
[October 1 preservation](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-worktree-retirement-october-1).

<a id="phase-8-worktree-retirement-result"></a>
[Earlier retirement result](../history/phase-closeouts/PHASE8_CLOSEOUT.md#phase-8-worktree-retirement-result).

<a id="worktree-retirement-control-panel"></a>
[D-GOV-020 control](../history/phase-closeouts/PHASE8_CLOSEOUT.md#worktree-retirement-control-panel).

<a id="nested-freecad-retirement-control-panel"></a>
[D-GOV-021 control](../history/phase-closeouts/PHASE8_CLOSEOUT.md#nested-freecad-retirement-control-panel).

<a id="nested-freecad-mechanical-exception-panel"></a>
[D-GOV-022 exception](../history/phase-closeouts/PHASE8_CLOSEOUT.md#nested-freecad-mechanical-exception-panel).

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
