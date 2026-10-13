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
| What changed | [D-P9-014](#phase-9b-selected-export-policy-panel) authorises the usual B16 selected export to make the full selected output set available in a different new directory. CSV stays optional. The route prevents replacement of previous output. |
| What now works | The selected route keeps the selected data and output paths from the preview through the operator decision, checks and file operations. Standalone, qualified FreeCAD and real-GUI checks pass for the bounded source and host. The chair decisions stay the same. These results give no exit acceptance. |
| Limitations/findings | The policy applies only to the qualified Linux ext4 host and an operator-controlled directory. It gives no assurance that files stay available after a system interruption. It adds no recovery after FreeCAD stops and starts again. All 24 risk duties and previous production limits stay. <br><br>D-P6-008 stays Deferred — unmet. TERM-R04 stays open. Output stays private-development. Project status stays `unknown`. |
| Owner decision | D-P9-014 changes only the canonical policy for the usual selected route and authorises one bounded product change. It accepts no phase exit or production result. D-P9-012 continues to own the one accepted Phase 9B exit. D-P9-013 stays limited to Core Generate. The Phase 9A closeout and previous decisions keep their accepted limits. |
| Next action | Complete independent source/test review and documentation validation. After CI gives a PASS result for the exact PR head, publish the draft PR. Do not merge or start another outcome. |

<a id="phase-9b-selected-export-policy-panel"></a>

## D-P9-014 selected export policy panel — 2026-10-13

**Decision boundary:** Richard accepts the policy for the usual B16
`Export selected production items` route and one bounded product change
towards Exit 9B-5. This Level 3 decision changes output paths and replacement
behaviour. It accepts no phase exit.
The source at the start is protected `main`
`98f637723154b1038c161bda7456650e37edf28f` after PR #167.

**Exact owner instruction and adopted policy:**

> As project owner, I approve the Level 3 selected-export publication policy in `tmp/after167/export-outcome-review.md`. Authorise the necessary alignment and one bounded implementation for Exit 9B-5, preserving all stated limitations and existing authority. Publish one exact-green draft PR, then stop. No merge or exit acceptance.

> Adopted policy:

> As project owner, I approve the Phase 9B policy for the normal B16 “Export selected production items” route: each operation publishes its complete requested output set in a unique new directory inside the directory selected by the operator. One no-replace directory operation makes the complete set available. CSV remains optional and is part of that same set when requested. Previous output files and directories remain unchanged. The selected route no longer offers replacement of existing outputs. Authorise the necessary Level 3 alignment and one bounded implementation, including truthful preview, confirmation, results and output-folder controls for the changed paths. Preserve existing member naming rules, content requirements, selected scope, record identities and isolated-document operation. Qualify publication only on the existing qualified Linux ext4 host with an operator-controlled directory; make no durability or restart-recovery claim. Preserve frozen B14/B15 comparison paths, retained comparison APIs, Core Generate policy and D-P6-003/D-P6-004 boundaries. This decision accepts no phase exit, production output, rights, performance or release result.

The adopted policy above preserves the complete approved meaning from
`tmp/after167/export-outcome-review.md`, SHA-256
`871eac5ba50679c7b7798df0e3e63fe732443188a7a07b8e9842ac4eb9a21685`.
The [architecture](../ARCHITECTURE.md#d-p9-014-selected-complete-output-set)
owns the canonical policy for the selected operation.
The [selected API requirements](../contracts/selected-export-set.md)
own the API, operating conditions and necessary checks.
D-P9-013 continues to own Core Generate. D-P6-003/D-P6-004 keep their Entry/Exit authority.

**Gap and preserved findings:** PR #165 preserved previous file data after
usual output errors. PR #166 isolated the temporary FreeCAD objects.
Neither result made all selected output files available together.
The selected route could leave only some destination files replaced after
failed restoration.

The inherited dialog also gave an assurance that the operation could not supply.
The Phase 9B owner for the selected operation keeps both duties until
evidence shows that the new operation satisfies them. The previous results and their limits stay.

**Safety/risk panel:** Richard is the project owner, panel chair and deciding
authority. The implementing agent presents the policy and bounded change.
Independent reviewer `/root/selected_set_architecture_risk` examined all 24
risk records and the architecture, API and security conditions before implementation.
The recommendation is **Proceed with bounded conditions**, with no dissent.
The reviewer made no product, test or canonical-document changes.

The agents share one team and workspace. This is not review by a different organisation.

The receipt is `tmp/selected-export-set/architecture-risk-review.json`, SHA-256
`a0bdb8dd9459133c9864d858fd1662296119c8bee0e655a29cb62fa3510051ec`.
Its conditions specify one directory and the full set of files that the operator accepted.
They also specify accurate completed counts, optional CSV, restoration of the compatibility component and real-GUI evidence.
PR-09 keeps rights and output controls. PR-13 keeps backup, restore and
previous-output preservation duties. PR-17 keeps editable-document recovery duties.

The selected product change uses the same file adapter for the full output set and the same isolated FreeCAD adapter. It adds no different filesystem protocol.
The independent risk input gives no acceptance for the product change or phase exit.

All 24 risk states, severities, owners, deadlines, treatments and controls stay
the same in the [current register](risks.json). No risk closes.

**Implementation evidence:** The [standalone selected-set test](../../tests/validate_selected_export_set.py)
gives a PASS result for 15 application conditions and 10 GUI-policy conditions.
The retained selected and Core standalone checks also give PASS results.
The selected command makes a copy of `plan` that includes the `extra_skipped` data.
It uses the same Core command for the full output set, file adapter and isolated FreeCAD adapter. It adds no different filesystem protocol.

The [real-GUI test](../../tools/freecad_bridge/run_selected_export_set_gui.py)
gives a PASS result for SVG with CSV on or off, cancellation, a writer
error and an occupied final path. It examines the preview, confirmation and
result. It clicks the completed-directory button and records the path sent
to the opener. It does not start the operating system's file manager.

Previous output and editable-document state stay the same.
Save and reopen checks pass on FreeCAD 1.1.4.
The result is
`benchmark-output/freecad-bridge/selected-export-set-runs/20261013T122523229422Z/run.json`,
SHA-256 `e3f80743425b5e034e45fa656c00f518e0d18fdf7bf8d6a1b70728c98fcfa9a4`.

The first applicable GUI test showed a change to the selected production data between previews.
The inherited `refresh_preview` added the related solid to the selected outline.
The first independent source review gave **BLOCKED** for that defect and
missing final proofs.

The repair supplies one more inherited preview
before the final paths become visible. The operation stops if the selected data
still change. The original GUI assertion stays the same and now passes.
The failed test and first review remain in `tmp/selected-export-set/`.

The [chair continuity test](../../tests/freecad_validate_chair_export_continuity.py)
also gives a PASS result on FreeCAD 1.1.4.
It preserves the exact turnout decisions for 168 chairs and the crossover
decisions for 355 chairs. Editable state, save, reopen and repeated export
checks pass. Crossover output hashes still differ after the tests apply the permitted comparison rules.
That existing serialisation limit gives no byte-equality claim.
The result is
`benchmark-output/chair-export-continuity/20261013T115656443006Z/result.json`,
SHA-256 `a5a27e6672e5a2e7b00dd014dbb454e8281f49bf62b83188364cb97a49c61517`.

The [selected-set FreeCAD test](../../tests/freecad_validate_selected_export_set.py)
gives a PASS result for eight conditions on FreeCAD 1.1.4.
It compares DXF, SVG, STL, STEP and CSV with the previous route and a
repeated operation under the same comparison rules.
Previous output, editable-document state and history stay the same.
Save and reopen checks pass. No temporary document remains.

The result preserves completed file counts after an error that occurs
after the final directory becomes available. The fixtures, frozen oracles
and tested source stay the same.
The result is
`tmp/selected-export-set/native-runs/20261013T122514824903Z/result.json`,
SHA-256 `3ef8dd4f18f03c18cdfef52678dd7b633ab50e3d358d01e203addf4c3692feb4`.
The combined evidence receipt is `tmp/selected-export-set/final-validation-receipt.json`,
SHA-256 `7335fe74f43388adddd78bcd7d4c633797a79cc81af411abbbe6badcf5d41743`.
Failed and interrupted tests remain available in that temporary evidence directory.
They give no completed evidence for the host profile.

A PASS result from the second independent source/test review is necessary before publication. Record that verdict in
`tmp/selected-export-set/quality-review-pass2.json`.

Older Phase 8, PR #165 and PR #166 GUI tests keep their recorded policy
and host limits. This cycle did not change them or repeat them as evidence for the new operation.
The Phase 8 FreeCAD 1.1.3 results remain historical.

**Limits and publication:** Phase 9A stays closed at 4/4 for its frozen
reference-only scope. Phase 9B stays Open at 1/6 under D-P9-012.
Only Exit 9B-2 is Evidenced and owner-accepted. The other five exits stay Pending.
The six exact criteria, geometry, package bytes, numerical limits, the
113-entry register and legacy-retirement conditions stay the same.

D-P6-008 stays Deferred — unmet. TERM-R04 stays open.
Output stays private-development. Project status stays `unknown`.
This decision accepts no production output, physical fit, manufacturing
capability, rights, performance or release result.

The operation is limited to the qualified Linux ext4 host and an
operator-controlled output directory. It gives no assurance that files stay
available after a system interruption. It adds no recovery after FreeCAD
stops and starts again. It gives no assurance for every filesystem or for
changes that another process makes to the directory during the operation.

Publish one exact-green draft PR after the necessary checks and independent
review. Do not merge or start another outcome.
The governance budget exception applies because this task changes output
policy authority. This panel supplies no phase-exit acceptance.

<a id="delegated-local-retirement-panel"></a>

## D-GOV-024 local retirement authority panel — 2026-10-13

Richard authorises this bounded Level 3 change.
After protected `main` contains the accepted change, Codex can make Level 2 decisions for permanent local worktree retirement.
Codex can then remove the specified worktree and branch.
The [Recovery owner](../RECOVERY_AND_BACKUP.md#delegated-local-retirement)
defines the applicable conditions. The change accepts no retirement target.

The starting source is protected `main`
`57bbacbcb19b79f3521ecea333e7c8fbe9f2e199` after PR #166 integration.
The exact approved PR head is `9526611884e368c3fe8c3b7299e4d48becea45c5`.
The merge has the same tree as that head. The primary worktree is clean and has the same commit as protected `main`.
All 60 existing worktrees and 67 branches stay.
The 52 known dirty-file identities and six IDE reference identities stay the same.

**Owner instruction:**

> Integrate pr 166, then switch to a small bit of housekeeping.
>
> Chatgpt pro reviewed the git estate and the failing worktree and branch removal see attached md file for reccomendations. Review file then implement. I agree all level 3 changes in advance to improve efficiency of this repair.

**Adopted owner addendum:**

> As project owner, I authorise the bounded Level 3 governance change needed to make eligible post-merge worktree and local branch retirement a Level 2 decision delegated to Codex.
>
> Once accepted and integrated, Codex may decide and perform permanent deletion of eligible completed local worktrees and obsolete local branches, without my approval for each target. Preserve existing identity, containment, inactivity, inventory, preservation, audit and independent-review requirements. Retain active, unique, ambiguous or insufficiently preserved material.
>
> Reconcile the canonical classification and Continue exclusions, connect retirement to the post-merge workflow, and update dependent checks. Remote branch deletion and force removal are excluded.
>
> Publish one independently reviewed draft PR with the required diff and preservation evidence. Do not merge or exercise the new retirement authority during this task.

The supplied handover has SHA-256
`90ec3bf59205e4604633c43e85d79d10bb38760b5461e0f9dac4416efb6a32a3`.
The adopted owner addendum supersedes the previous proposal to change only routing.
The previous external environment failures and GitHub refusal stay historical findings.
The current development, documentation and publication preflights pass.
They give no evidence that a retirement target is ready.

**Panel:** Richard is the decision authority. The implementing agent supplies the change for review.
A separate agent, `retirement_authority_audit`, examines risk and authority without changes to files.
Its panel recommendation is **Proceed with bounded conditions**.
The independent review is within one agent team. It is not a review by a different organisation.
The reviewer reports no disagreement about the decision.

| Risk | Challenge and retained control | Result |
| --- | --- | --- |
| PR-13 — Critical | Permanent deletion can lose local data. Current independent preservation, restore evidence, exact target checks and independent review are mandatory. If necessary evidence is missing or has a FAIL result, keep the worktree and branch. | Critical/Open/Mitigate and all backup duties stay. The decision accepts no target. |
| PR-22 — High | This bounded authority must not become authority for other destructive operations. The accepted merge, an exact Level 2 decision and independent review are mandatory. An increase to authority stays Level 3. | High/Open/Remove and its existing duties stay. |
| PR-12 — Medium | Live rules must agree. Preserve the frozen decisions and their meanings. Reconcile the canonical owners and dependent checks. | Medium/Open/Mitigate and its existing duties stay. |

The panel gives these mandatory conditions: keep primary `main`, active state, unique content and ambiguous or uniquely owned state.
Keep state without sufficient evidence of planned preservation.
If a usual Git removal command gives a Git error, keep the worktree or branch that Git did not remove.
Do not use force removal. Do not delete a branch in another repository.
Do not examine other worktrees or branches for removal.

D-GOV-022 is not available through this authority.
Current evidence does not show that no person or process uses each worktree.
It does not prove the snapshot coverage or planned preservation for each worktree.
These unknown conditions prevent removal of the applicable worktree or branch.
They do not authorise assumptions.

**Decision:** Proceed with these bounded conditions. Record the new authority
once in the [decision register](gate-decisions.json).
The Engineering Policy owns classification. Recovery owns the conditions and procedure.
Continue and Agent Workflows route the previous PR's recorded local worktree and branch
after main synchronisation and repeated IDE workspace alignment.
The safety audit stays read-only and unchanged.

Before draft publication, the change owner must complete the applicable positive and negative checks.
The change owner must also complete independent source/test review and the finite documentation lifecycle.
Necessary CI must pass for the exact draft head.
Preserve the evidence with FAIL results and the existing review limitations.
This task must not merge the new draft or remove a worktree or branch.

The owner requested this work on governance and tools. It supplies no Phase 9B exit evidence.
The governance budget can exceed the implementation budget because the task changes removal authority.
The 113-entry register, product geometry, production boundaries and all risk
duties stay unchanged. Phase 9A stays closed at 4/4 for its frozen reference-only
scope. Phase 9B stays Open at 1/6, with five exits Pending.

## Selected output keeps temporary objects in a different `App.Document` — 2026-10-13

This Level 2 result supplies evidence for phase exit 9B-5. The usual B16
`Export selected production items` route uses `CoreExportDocument` to write
each selected output in a different temporary `App.Document`.
The component does not change.
After two errors in a test of the previous software, a temporary `Part::Feature`
stayed in the `App.Document` that a person can change.
The new route keeps that object in a different `App.Document`.

The [standalone Python test](../../tests/validate_selected_export_rollback.py)
gives a PASS result for 32 conditions.
The [FreeCAD test](../../tests/freecad_validate_selected_export_document.py)
gives a PASS result on the qualified host profile for FreeCAD 1.1.4.
It compares outputs for one `TO-001` bounded scope from B15 and two B16 operations.
The `DXF`, `SVG`, `STL`, `STEP` and `CSV` results agree when the test uses the
comparison rules. Those comparison rules do not change.

Eight more tests examine completed operations, rejected conditions and errors.
They examine `App.Document` identity, object data, `UndoCount`, `RedoCount`,
`UndoNames` and `RedoNames`.
They also examine `App.ActiveDocument` and `App.activeDocument()`.
The object data stay the same after the test writes the `App.Document` to a file
and opens that file again.

If FreeCAD cannot close the temporary `App.Document`, the diagnostic identifies
that `App.Document`. It stays available. No new output becomes available, and
previous files stay the same.
For that condition, `App.listDocuments()` does not give its initial result.

The FreeCAD result is in
`tmp/selected-export-document/native-runs/20261011T173230900002Z/result.json`,
SHA-256 `99b06c54b945d0dde35caa9cea057998ec13949d10e7aa686183cb55094b6b12`.
The previous FreeCAD test for selected output also gives a PASS result.
Its result is in
`tmp/selected-export-rollback/native-runs/20261013T055057267159Z/result.json`,
SHA-256 `d10834e53865745cb1cd9c730fd2832fc0e0c091e81f801faa3c6b41b03e7bd9`.

The [test that uses `FreeCADGui`](../../tools/freecad_bridge/run_selected_export_document_gui.py)
gives a PASS result for a completed selected operation and a controlled output error.
It examines object data, `UndoCount`, `RedoCount`, `UndoNames`, `RedoNames` and
`ViewObject.Visibility`.
Those data stay the same. The test also writes the `App.Document` to a file and
opens that file again. The object data stay the same.

The test reads `App.ActiveDocument`, `App.activeDocument()`,
`Gui.Selection.getSelectionEx()` and `Gui.Selection.getPreselection()`
before and after `CoreExportDocument` operates.
It also reads the `PickedPoints` data. The data agree.
The B15 `refresh_preview()` and `confirm_selected_export_operation()` operations
can change those data before `CoreExportDocument` operates.
The test gives no assurance that the data from before
`confirm_selected_export_operation()` stay the same.

The result and four `.png` files from FreeCAD are in
`benchmark-output/freecad-bridge/selected-export-document-runs/20261013T055940671786Z/`.
The result file is `run.json`,
SHA-256 `b7917e08d9adcea9c6e2116372f085ed2998b925319ff4d8fdab811a7ff0d9cb`.
All three FreeCAD results show that the software files did not change.

The B15 command stays available for tests that compare results.
Filenames, output data, product shapes and dimensions, and the file for the
113 quantities do not change.
The [previous finding about the wording in `confirm_selected_export_operation()`](#previous-files-stay-available-after-an-output-error--2026-10-11)
stays `REQUIRED_BEFORE_EXIT` for 9B-5.

This result does not make all selected files available together.
If FreeCAD stops and starts again, this result adds no procedure for the
operation that stopped.
It gives no assurance that files stay available after a system interruption.
[D-P9-013](#phase-9b-core-export-policy-panel) continues to apply only to `Core Generate`.

Phase 9B stays `Open` at 1/6. Phase exit 9B-5 stays `Pending`.
Phase 9A stays closed at 4/4 for its frozen `reference-only` bounded scope.
All production conditions stay the same.

## Previous files stay available after an output error — 2026-10-11

This Level 2 result supplies evidence for phase exit 9B-5. The usual B16
`Export selected production items` route keeps previous file data after an
output error. This includes an error that stops the software before it can put previous
files back in their initial locations.

If the directory identity is known, the diagnostic gives the directory that
contains those files. If that identity is unknown, it gives the last known path
and reports that the current location is unknown. It does not report that the
output stayed the same when the result is unknown.

The test of the `implementation-defect` gave two `OSError` errors.
One stopped a new file operation. The other stopped the software before it
could put a previous file back. The previous software then removed the
temporary directory and that file. The new `SelectedExportFiles` component
keeps the directory if its checks do not show all previous files in their
initial locations.

A completed operation can remove its temporary files. An operation with an
error can also remove them if it puts all previous files back.

The [test with standalone Python](../../tests/validate_selected_export_rollback.py)
compares results from completed operations and file bytes with B15. It also
examines previous files, CSV on/off, rejected paths and the diagnostic after
errors. The B15 command does not change.

The [FreeCAD test](../../tests/freecad_validate_selected_export_rollback.py)
and [test that uses `FreeCADGui`](../../tools/freecad_bridge/run_selected_export_rollback_gui.py)
give PASS results on the qualified host profile for FreeCAD 1.1.4. The FreeCAD
test compares one `TO-001` bounded scope with `SVG` and `CSV`.
The comparison rules do not change. The checks show completed output,
two conditions with errors and the same data after the test writes the
`App.Document` to a file and opens it again.
The test with standalone Python examines 23 conditions.

The FreeCAD test result is in
`tmp/selected-export-rollback/native-runs/20261011T163500394902Z/result.json`,
SHA-256 `ee7d7bffc2ef2d56987e10df24dfbb29f59b24b78408ea3a73e0aa4ff84389fd`.
The result from `run_selected_export_rollback_gui.py` is in
`benchmark-output/freecad-bridge/selected-export-rollback-runs/20261011T163803576148Z/run.json`,
SHA-256 `e17ed1f98d50ec539d9ec3be5f563d9183c7ea856c63081268e518fd666afca7`.

The two results show that the software files did not change.
Four images from FreeCAD stay with the result from
`run_selected_export_rollback_gui.py`. The image after an error does not show
the full path. The test examines the full diagnostic text in the
`QMessageBox` that FreeCAD shows.

The usual launcher supplies `SelectedExportFiles`. The B15 command stays
available. The tests compare its results with the results from the B16 command.
Migration acceptance stays necessary before removal of the B15 command.

Filenames, CSV data and the data that define product shapes do not change.
The file for the 113 quantities,
[`s1-independent-engineering-evidence-map.json`](../lineage/s1-independent-engineering-evidence-map.json),
does not change. A person can continue to select replacement of previous files.

Before that replacement, the software continues to show this text:
`Destination files change only when the complete export succeeds.`
This claim is incorrect if the software cannot put previous files back.
Independent review records this finding as `REQUIRED_BEFORE_EXIT` for 9B-5.
The owner of the selected route must correct that claim before phase exit 9B-5.

This result does not make all selected files available together.
`dispatch_freecad_export` can continue to put temporary `Part::Feature`
objects in the `App.Document` that a person can change. The duty for this
operation is not complete.
The change supplies no operation to put files back after FreeCAD stops and
starts again. It gives no assurance that files stay available after a system
interruption. [D-P9-013](#phase-9b-core-export-policy-panel)
continues to be applicable only to `Core Generate`.

Phase 9B stays `Open` at 1/6. Phase exit 9B-5 and the other four phase exits
without acceptance stay `Pending`. All production conditions stay the same.

<a id="phase-9b-core-export-policy-panel"></a>

## D-P9-013 Core Generate export policy panel — 2026-10-11

**Decision boundary:** Richard accepts the Core Generate export policy and
one bounded implementation towards Exit 9B-5.
The starting source is protected `main`
`6586eda3addaf955be06b69753c906252b72adbe`.
This Level 3 decision changes output policy. It accepts no phase exit.

Phase 9B stays Open at 1/6 under D-P9-012. Only Exit 9B-2 is Evidenced and
owner-accepted. The other five exits stay Pending.
Phase 9A stays closed at 4/4 for its frozen reference-only scope.

**Exact owner instruction:**

> As project owner, I approve the proposed Phase 9B Core Generate export policy: unique collision-free folders, atomic whole-set publication, optional CSV, revised output paths and preservation of all previously published outputs.
>
> Authorise the necessary Level 3 alignment and bounded implementation.
>
> Qualify atomic publication without claiming durability or restart recovery. Preserve all other export and acceptance boundaries.

**Approved policy:** Each Core Generate export uses a different new
child directory inside the output directory that the operator selects.
All requested files pass their existing checks before one directory operation
makes the full set available at its final path.
The operation must not replace an existing final path.
The operation stops with a diagnostic if the host cannot provide this behaviour.
CSV stays optional. A requested CSV is part of that same output set.

Member filenames and content requirements stay the same, except that output
paths and CSV paths identify the new final directory.
The Core Generate controls must show this changed behaviour.
A control that permits replacement of previous outputs no longer applies to this route.
All previous output files and directories stay unchanged.
The [architecture](../ARCHITECTURE.md#d-p9-013-core-generate-complete-output-set)
and [successor contract](../contracts/core-layout-export-set.md) own the technical conditions.

**Evidence and conditions:** The existing preparation and isolated-FreeCAD
proofs below establish the previous bounded behaviour.
They do not establish that all files become available together.
The new standalone and qualified FreeCAD checks give PASS results for the
approved full-set operation in the bounded operating conditions.
The result must report completed output accurately after an error.
Once the full set is available, cleanup must preserve it.

The policy applies to the output that becomes available during an operation.
It gives no assurance that the files stay available after a system interruption.
It adds no recovery after FreeCAD stops and starts again.
The implementation is limited to the qualified Linux ext4 host and an operator-controlled
output directory. A different process can change that directory during this operation.
These checks do not prevent that change.
The implementation gives no assurance for every filesystem.

**Safety/risk panel:** Richard is the project owner, panel chair and deciding
authority. `/root` presents the policy and bounded implementation.
Fresh read-only reviewer `/root/atomic_export_review` examined all 24 risk
records, the policy and initial source and standalone evidence.
The reviewer authored no product code, tests or governance text.
The agents share one team and workspace. This is not external organisational independence.

The recommendation is **Proceed with bounded conditions**. The receipt records
no authority blocker. The implementation owner must supply qualified FreeCAD
and real-GUI evidence before source review and draft publication.
The independent source reviewer must compare the complete final source and
test diff with those proof identities before the bounded change can complete.
This risk input gives no source or phase-exit acceptance.

The independent receipt is
`tmp/phase9b-core-export-atomic/independent-risk-review.json`, SHA-256
`1ebce694d39d0a7d59120ab1bf96650f88fa366a69a1b95281f71b18f760e933`.
The qualified evidence below supplies the host checks that the risk input
requires. The publication boundary requires independent source review.

All 24 risk states, severities, owners, deadlines, treatments and controls stay
unchanged in the [current register](risks.json). No risk closes.
PR-09 stays Critical/Open/Partial. PR-13 stays Critical/Open/Effective for its
current scope. PR-17 stays Critical/Open/Partial.
The named risk owners keep their existing duties and deadlines.

PR-01 and QA-R03 keep wider workflow coverage duties. PR-16 keeps input and
invalidation duties. PR-17 keeps document preservation and recovery duties.
PR-09 keeps output rights controls. PR-13 keeps backup and restore duties.

PR-15 and QA-R04 keep performance duties. PR-22 keeps independent acceptance
control. PR-10 and PR-18 keep comparison and removal conditions.
The chair evidence and rights risks keep their production duties.

**Implementation evidence:** The [file tests](../../tests/validate_core_export_atomic_files.py)
and [application tests](../../tests/validate_core_export_atomic.py) give PASS results.
They examine complete output, preparation errors, path collisions, unsupported
operations, uncertain results and preservation after output completes.

The [qualified FreeCAD test](../../tests/freecad_validate_core_export_atomic.py)
gives PASS results for six cases.
These are success with CSV, success without CSV, a preparation error, a path
collision, an error before the directory operation and an error after it.
The comparisons preserve DXF, SVG, STL, STEP and CSV content with the existing
normalisations and the declared final-path change.
They preserve previous output and the editable document.
The retained staging and Phase 7 comparison tests also give PASS results.

The actual GUI proof uses Core Generate for those six cases.
The result shows 14 completed files with CSV and 13 without CSV.
The three errors before completed output show zero completed files.
An injected error after the full set becomes available keeps 14 completed
files and reports one additional diagnostic.
CSV and all completed files stay in the new directory.

The summary and the `Open Folder` request identify that directory.
The copied fixture stays unchanged. The editable document keeps nine objects
and gives a PASS result for save/reopen.
The checks preserve the active document, selection and preselection.
Actual summary images stay with the GUI evidence.

The qualified host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
The native record is
`tmp/core-export-atomic/native-runs/20261011T152204349723Z/result.json`,
SHA-256 `413d05c49fb70eca7e0aa19a0276c09bffcffe6d8de48f142e7aea0f187e71a5`.
The GUI record is
`benchmark-output/freecad-bridge/phase7-core-layout-export-workflow-runs/20261011T152213135415Z-modular/run.json`,
SHA-256 `7f9c8d301a8b1ab0d3694e415b74fc0384b93b54d6aa8c9044f783da9e428f46`.
The retained staging record is
`tmp/core-export-staging/native-runs/20261011T152330301258Z/result.json`,
SHA-256 `af93c3baaa60fdae7febbeef79d6aeb91580cdd46574b7cf73df7ddebdbf9d87`.
The source hashes in these records match the tested candidate.

They identify the exact tested source independently of later documentation changes.
These proofs give no crash, arbitrary-interruption or performance assurance.

**Exclusions and resulting authority:** This decision authorises the necessary
Level 3 alignment and one bounded implementation.
The governance-budget exception applies because the owner changes output policy.
D-P6-003 and D-P6-004 keep their Entry/Exit conditions.
The Phase 7 comparison API, previous staging API and selected-export route keep their limits.
The six Phase 9B criteria, geometry, package bytes, the 113-entry register and
numerical limits stay unchanged.
All earlier acceptance and legacy-retirement conditions stay.

D-P6-008 stays Deferred — unmet. TERM-R04 stays open.
Output stays private-development and project status stays `unknown`.
This decision accepts no physical fit, preload, retention, manufacturing
capability, production package, output clearance, rights, performance result or release.

**Publication boundary:** Complete the bounded implementation, usual validation,
independent source review and the finite Documentation Review lifecycle.
After CI gives a PASS result for the exact PR head, publish the draft PR.
Do not merge or start another outcome. This decision closes no phase and
accepts no other exit.

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

## Core Generate uses an isolated FreeCAD object — 2026-10-11

This Level 2 result supplies part of the work for Exit 9B-5 to preserve the previous `App.Document`.
The usual Core Generate route uses an isolated temporary `App.Document` for
each task with a `format` value. It closes only the object with the identity that it owns.
An error during this work prevents file writes to output paths in `plan`.
The [contract](../contracts/core-layout-export-staging.md#isolated-objects-for-output)
owns the operation and its limits.

The test for standalone Python gives PASS results for 21 `App.Document` tests and 34 file tests.
The test with the qualified host profile for FreeCAD compares DXF, SVG, STL, STEP and CSV output with the
previous route. The previous checks that compare output and `Shape` values give PASS results.
Eight more tests examine the active condition, `App.newDocument`, `recompute`, object
removal, `App.closeDocument` and interruption. The previous `App.Document` condition, `Shape` values, object identities, `UndoCount`, `RedoCount`, `UndoNames` and `RedoNames` stay the same in these tests.
The test with `save` and `openDocument` gives a PASS result.

The test in the GUI uses Core Generate for success, an error in the last STEP task and
an error from `App.closeDocument`. It puts the previous selection in two
`App.Document` objects, `PickedPoints` and the condition from `Gui.Selection.getPreselection()` back.
It also puts a different `App.Document` back in its previous active condition.
It checks the logical selection, not the previous sequence of changes to the selection.

The error from `App.closeDocument` gives zero completed files and 13 outputs that did not
complete. There are no output files. The diagnostic identifies the temporary `App.Document`
that stays open. The test records that open object before test cleanup.
It does not claim that `App.listDocuments()` returns its previous result after this error.

The host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
The FreeCAD result is
`tmp/core-export-staging/native-runs/20261011T141112296335Z/result.json`,
SHA-256 `ecadcfd70a1a952d990d8618e4565c95526d9ae832aebb0f2ba7d6e773a0d1cc`.
The GUI result is
`benchmark-output/freecad-bridge/phase7-core-layout-export-workflow-runs/20261011T141115247985Z-modular/run.json`,
SHA-256 `fb727153740caec92b77fbd08932657f8e08c799eea3f0a752b35c0d8e8fdb92`.
That GUI directory contains actual images of the result for all three tests.
The two results identify the tested source and copied fixture. No operator `App.Document` changes.

When `App.closeDocument` completes, it removes objects that a previous removal operation did not remove in this route.
The Phase 7 route used to compare output and `SelectedProductionExportDialog` keep their previous limits.
The complete output requirement and its recovery stay unresolved for Exit 9B-5.
The [accepted interruption conditions](../ARCHITECTURE.md#supported-exporter-failure-model) stay the same.

D-P9-012 continues to apply. Phase 9B stays Open at 1/6, with five exits Pending.
Phase 9A stays closed for its frozen `reference-only` scope.
Data that define product shapes, the 113-entry register and accepted numerical limits do not change.
Output stays in `private-development` status and project status stays `unknown`.
This result gives no acceptance for physical fit, rights, performance, production or the ability to make parts.

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
