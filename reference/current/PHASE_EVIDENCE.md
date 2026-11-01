# Phase 9B Opening Record

Status: **Phase 9A is closed at 4/4 under D-P9-010 for its frozen reference-only
scope. Phase 9B is Open at 3/6 under D-P9-012, D-P9-015 and D-P9-017. Only Exits 9B-2, 9B-4 and 9B-5 are Evidenced and owner-accepted. Exits 9B-1, 9B-3 and 9B-6 stay Pending.**

The [Phase 9A closeout](../history/phase-closeouts/PHASE9A_CLOSEOUT.md),
[decisions](../history/phase-closeouts/PHASE9A_GATE_DECISIONS.json) and
[risk snapshot](../history/phase-closeouts/PHASE9A_RISKS.json) preserve its history.
The [project plan](../PROJECT_PLAN.md) owns current phase and exit status.

<a id="hosted-validation-policy-panel"></a>

## D-GOV-026 accepted validation execution policy — 2026-10-30

**Owner decision:** Accepted. Richard accepted D-GOV-026 as reviewed in
[PR #234](https://github.com/Richard-Gnitnub/tracktemplate/pull/234) on 2026-10-30.
The [decision register](gate-decisions.json) preserves his full acceptance
and the previous instruction to prepare the policy. The PR merge did not supply this acceptance.

**Accepted decision:** Adopt the
[validation execution policy](../VALIDATION.md#validation-execution-location).
Make GitHub execution mandatory for its specified tests.
Authorise necessary executions on GitHub within one bounded scope for tests, inputs and resources.
These executions need no individual owner decision.
Each specified local test needs a recorded owner decision that authorises local execution.

Do not start an automatic local replacement. Keep all specified failure,
repair, input-restriction, recovery and GUI evidence requirements.

The reviewed PR head is `eea8b1a160cc533223a0f6939cda47f22eadde81`.
Its [CI run 41025763875](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41025763875)
gave PASS results for 150 validators. Independent result review gave PASS.
The merge commit is `ed2424801ff15b2f9f263cece3465c3450b73f4b`.

The source baseline for the policy draft was `0d8f3d2b16c0aeec9a05068a445614ec34c50cca`.
Its post-merge [CI run 41017516406](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41017516406)
gave a PASS result. The policy uses test categories from existing geometry
tests and benchmarks. It invents no memory threshold.

**Safety/risk panel:** Richard is the deciding project owner. `/root` owns
the change and technical documentation. `/root/hosted_policy_controls`
implements the local launch checks. `/root/hosted_policy_risk` independently
examined the evidence, authority and risks before implementation.
The agents share one team and workspace. This is not external independence.

The independent source/security review gave a PASS result for the launch
checks and their offline evidence. The one Documentation Review returned
`APPROVED_WITH_EXACT_CORRECTIONS`. The implementing agent applied all 46 corrections.
Final document validation gave PASS at `23192c36c7d21c52b86112bbb4f1eaa0c14f021e`.
The reviewed PR head preserves those document bytes.

The recommendation is **Proceed with bounded conditions**. The panel recorded no disagreement. [Issue #213](https://github.com/Richard-Gnitnub/tracktemplate/issues/213)
and [PR #217](https://github.com/Richard-Gnitnub/tracktemplate/pull/217) support
isolation from the workstation. They do not establish a FreeCAD memory leak.
[PR #233](https://github.com/Richard-Gnitnub/tracktemplate/pull/233) and
[run 40980935631](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/40980935631)
prove only the transition test on GitHub: one native test, no skips and verified
cleanup. The test duration was 0.624 seconds.

Its observed 58.527 MiB memory maximum and 0.577604 CPU seconds are sampled lower bounds.
They do not qualify chair capacity, total resource use, GUI execution or private-input transfer.

The [risk register](risks.json) keeps every risk and duty. No risk closes.
PR-13 keeps recovery and independent-preservation duties. PR-06, PR-07,
PR-09 and PR-21 keep input, output and rights restrictions.

PR-01 keeps GUI coverage duties. PR-15 keeps performance uncertainty.
PR-22 keeps owner authority for this decision. The routing reduces workstation
exposure but proves no product performance improvement.

| Condition | Owner and deadline |
| --- | --- |
| Verify test, input, resource and repair scope. Record each tested commit, result and cleanup. | Change Validation, before each run and before reporting its result. |
| Verify the authority for remote processing and publication. Private Templot archives and generated research geometry are not admitted by this decision. | Provenance owner, before any transfer. |
| Preserve independent recovery evidence. Temporary artifacts on GitHub are insufficient as the only recovery copy. | Project owner and Change Validation, before execution and before artifact expiry. |
| Check local refusal, references to recorded owner decisions, unchanged resource guards and lightweight checks. Complete independent source/security review. | Implementation and independent Quality Review, before draft publication. |
| Complete the finite Documentation Review and deterministic validation. Present the exact draft for the owner's decision. | Technical Author Lead, before acceptance. |

The launch checks prevent unintended local execution through the usual entry
points. They do not verify that the owner gave authority or prevent direct commands.
The policy also controls those commands. This change qualifies no GitHub GUI method or private-chair input method.

**Resulting authority:** The standing execution policy applies.
Necessary GitHub executions within an authorised bounded scope need no individual owner decision.
This acceptance gives no separate authority for the owner's "L1 dispatch" or "confidential-input transfer".
It gives no additional repair, retry, limit increase or merge authority.
The current authorised L1 implementation continues on its separate branch.
Its bounded scope for tests on GitHub, necessary inputs and resource limits need owner approval before execution.
Do not do its specified tests on the workstation.

Phase 9B stays Open at 3/6. The historical 2/2 allowance remains consumed.
Frozen XO-001 evidence stays unchanged. LMS stays paused. Issue #213 pressure
monitoring stays paused.

No physical-fit, rights, production, release or phase-exit acceptance follows.
The usual governance-change budget does not apply to this Level 3 governance and safety task.

<a id="candidate-bound-documentation-exception-panel"></a>

## D-GOV-025 candidate-bound documentation exception — 2026-10-20

**Owner decision:** Richard approves one Level 3 exception for candidate
`895b2b31ece814783780053b1bcdde24fb927b5d414830af3443222f5a336617`
and original review
`5523e04fbf26155ffec3e4cb48fc477e6326ded4f75ded4fb9e23af500cfb6b9`.
The original review keeps its `BLOCKED` verdict, empty correction record
and null completion proposal.

**Permitted route:** Record the accepted meanings in the
[occurrence-specific appendix](../TERMINOLOGY.md#candidate-bound-inventory-terminology).
Obtain one late correction supplement from original reviewer
`/root/offline_verifier_implementation` for the existing 21 findings and
every recorded occurrence. Freeze the exact recipe. Qualify the local
verifier and obtain independent code review before one application.
Rebuild the preserved derived cache. Make only the specified consequential
repairs to the three validators. Record actual validation results in a
local content-hash receipt. Obtain independent result review and stop.

**Safety/risk panel:** Richard is the deciding project owner. `/root` is
the Technical Author Lead and change owner. Original author
`/root/offline_pair_measurement` challenged the proposed exception.
The owner expressly accepts that risk-challenge independence limitation.
The agents share one team and workspace. The original reviewer retains
linguistic responsibility. A separate code reviewer checks the local
verifier before application.

The recommendation is **Proceed with bounded conditions**. The panel used
the original candidate, original review, accepted factual disposition and
static audit of the ordinary STE tooling. That tooling cannot complete
this uncommitted packet. Its source, canonical review state and historical
bindings stay unchanged.

The principal risks are authority expansion and false review or validation
attribution. The [risk register](risks.json) keeps all 24 risk duties.
No risk closes. PR-09 retains the private-output limit, PR-13 retains
preservation duties, and PR-22 retains the panel duty.

| Bounded condition | Owner and deadline |
| --- | --- |
| Preserve the original candidate, review, empty correction record, source identities and failed evidence. | Technical Author Lead, before and throughout execution. |
| Keep accepted meanings, occurrence contexts and exclusions exact. Keep existing registered meanings unchanged. | Terminology and subject owners, before the supplement freezes. |
| Account for all 21 findings and every occurrence through exact corrections or explicit owner-supported dispositions. No dummy replacements or new findings search. | Original reviewer, before application. |
| Qualify the local verifier and obtain independent code review. Verify exact preimages, complete scope and preservation. | Validation owner and separate code reviewer, before application. |
| Stop on incomplete coverage, unresolved meaning, identity mismatch, unexpected validation failure, a blocking review or changes outside the permitted scope. Permit no second supplement, application or wording cycle. | Technical Author Lead, throughout execution. |

**Resulting limits:** This is local exception completion only when its
validation and result review pass. It is not linguistic `ACCEPT`, global
terminology admission or ordinary Git lifecycle completion. These companion
additions inherit no linguistic acceptance. No commit, push, PR or merge is
authorised.

The inventory, evidence, unsupported entries, LMS pause and consumed
allowances stay unchanged. Phase 9A stays closed at 4/4. Phase 9B stays Open
at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending. No geometry work, rights,
programme, production or exit acceptance follows.


<a id="lms-chair-record-and-templot-development-panel"></a>

## D-P9-018 LMS chair record and private Templot chair development — 2026-10-18

**Owner decision:** Record the completed LMS chair development model as the
owner's "prototype". Pause more LMS chair development until after Phase 11.
Make all chairs from the Templot geometry for private modelling
and TrackTemplate development. Adapt those chairs through the
TrackTemplate path that the project uses. This is Level 3 direction for private development, not
phase acceptance or a change to third-party rights.

**Exact owner instruction:**

> thank you codex, that was a great first go. We shall record this as a prototype. We will pause LMS chair development for now and pick it up again as a feature post phase 11. What I really want to do now is model every templot chair using templot geometry which we've already established. This is for personal use as per provenance i don't intend to widely distribute templot designs apart from my own private modelling.
>
> So, lets do that. lets build out every chair in the templot inventory. adapt into tracktemplate as previously established and then use that inventory of templot chairs to enable track template development. In the meantime I will have a think with what to do about LMS chairing/

**LMS evidence kept for this work:** The local worktree is `lms-chair-development`, at
base commit `e5b2638f22e459f555ce4d27d3c0ab1f7bcd7707`. Its directory is
`tmp/lms-chair-development`. The directory README records how the model was made
and the limitations of the model.

The native development model contains three parts: a complete casting,
a key and a reference rail. All twelve native checks give PASS results.
FreeCAD document reload also gives a PASS result. Six native viewport captures
show the model and sections. The independent review gives
**PASS WITH FINDINGS** for this bounded native result.

The full validation suite gives a **FAIL** result because STEP reload gives a FAIL result
with `BOPAlgo_InvalidCurveOnSurface`. The STEP files stay output with a FAIL result.
The native result does not change that FAIL result.

Physical fit, continuous key
insertion, preload, retention and manufacturing capability stay unproved.
The recorded native tolerance is `1.000001e-6 mm`. This is more than the
former P1 `1e-7 mm` native tolerance ceiling. The model does not prove P1
exterior equivalence. Keep the previous stopped work and all evidence with a FAIL result.

| Record kept in the directory | SHA-256 |
| --- | --- |
| `README.md` | `eacb739f3ca2efc7840505c9f614b6bbb4c834e462167f5dbe188d407e263aa1` |
| `independent-review.md` | `932b419ac52781ffbc9ee6d702f76c6aa4d92e9059bfda7d19b9cd989d9ca5b9` |
| `validation-02/result.json` | `b83103477329cd52651a8b270d09951b1e10d688c86ea7fe520f305245f34fd7` |
| `build-03/visual-proof-02/capture-result.json` | `976b7a7a6a8ba2578343f39a230f89f9f6ba1880a9133ee2365fceda1331f380` |

**Private development scope:** Use the Templot geometry
and record its exact source coverage. A chair name alone does not prove that the adapter makes the geometry. Keep a record of missing source geometry and source geometry that the adapter does not make.
Do not make geometry that the source does not contain or report the complete set as made without evidence for the claim. These chairs can help TrackTemplate development.
This direction does not make all Templot families mandatory for the Core
release candidate or change an accepted chair definition.

The [licensing boundary](../LICENSING_BOUNDARIES.md) and
[provenance owner](../PROVENANCE.md) keep source classifications, notices and
the conditions for clearance. Research data and outputs stay local,
untracked and private-development. Personal use gives no third-party
permission or positive rights finding. No public distribution is authorised.

**Safety/risk panel:** Richard is the project owner and has decision
authority. `/root` owns the development work. `/root/offline_pair_measurement`
prepares this documentation alignment and previously reviewed the LMS development model.
Read-only challenger `/root/offline_verifier_implementation` examined the new
direction.

The reviewer wrote the local S1/L1 builder, but did not write this
documentation, the Pascal tool or the generic adapter. The agents share one
team and workspace. This is not external organisational independence.

The recommendation is **Proceed with bounded conditions**.
The challenge keeps neutral chair definitions authoritative. A Pascal tool
can help local development. It is not a mandatory product runtime dependency.
Unchanged arithmetic does not prove equivalence to the complete Templot program.

The [risk register](risks.json) keeps all 24 risk states, owners, deadlines
and controls. No risk closes.

PR-09 keeps the private-output limit.
PR-13 keeps preservation duties. PR-22 keeps the independent panel duty.
Unresolved source geometry and rights stay with their owners.

| Bounded condition | Owner and deadline |
| --- | --- |
| Preserve the LMS model, output with a FAIL result and previous evidence. Keep more LMS development paused until after Phase 11. | Development owner, during this work. |
| Distinguish declared chairs, available source geometry, generated chair components and validated assemblies. Keep unsupported loose-pin modes and all FAIL results in view. Keep data and output private. | Chair-definition and provenance owners, before each development use or completion claim. |
| Record hashes for the source, source members and extracted fragments. Record the compiler, the data that control it, all global variables and inputs. | Development owner, before each generation claim. |
| Check source positions, planes and complete coverage after the adapter puts faces into groups or divides them into triangles. Record the measured differences and FAIL results. | Geometry and validation owners, before each geometry claim. |
| Complete the Documentation Review lifecycle. Preserve all exits that the plan records and rights limits. | Change owner and Technical Author Lead, before this documentation alignment becomes the controlled baseline. |

**Limits for this decision:** Phase 9A stays closed at 4/4 for its frozen reference-only
scope. Phase 9B stays Open at 3/6. Only Exits 9B-2, 9B-4 and 9B-5 are
Evidenced and owner-accepted. Exits 9B-1, 9B-3 and 9B-6 stay Pending.

All six exact criteria stay unchanged. D-P6-008 stays Deferred — unmet.
TERM-R04 stays open. Project status stays `unknown`.

This decision accepts no production package, output clearance, rights,
performance result, release or phase closeout. It gives no publication or
integration authority. Previous decisions and their evidence stay unchanged.

<a id="phase-9b-exit-4-acceptance-panel"></a>

## D-P9-017 Phase 9B Exit 4 acceptance panel — 2026-10-13

**Decision boundary:** Richard accepts only Exit 9B-4 under D-P9-016 with all
recorded limitations. The accepted source is protected `main`
`0b93551920a5da013266c06ec75dd6f664dd96f2` after
[PR #171](https://github.com/Richard-Gnitnub/tracktemplate/pull/171).
Its tree is the same as the reviewed tree at `6dd0636f89e82724f9638b9f5d4c6958512d2aa1`.
[CI run 38463966509](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/38463966509)
gave a PASS result for that exact `main` commit.

Phase 9B is Open at 3/6. Only Exits 9B-2, 9B-4 and 9B-5 are Evidenced and owner-accepted.
Exits 9B-1, 9B-3 and 9B-6 stay Pending. All six exact criteria stay unchanged.
Phase 9A stays closed at 4/4 for its frozen reference-only scope.

**Exact owner instruction:**

> As project owner, I accept Phase 9B Exit 9B-4 as Evidenced and owner-accepted under D-P9-016, with all recorded limitations preserved.
>
> Complete the necessary Level 3 alignment and publish one exact-green draft PR.
>
> Retain the completed worktree until independent preservation is proved. Do not force retirement.
>
> No new implementation, additional exit acceptance, production clearance or phase closeout.
>
> Stop for integration authority.

**Exact criterion:**

> Representative output manifests reproduce the complete package/dependency classification. They cannot claim `project-cleared` if an applicable input is replaced by a restricted or unresolved source.

**Accepted evidence:** The [D-P9-016 panel](#phase-9b-core-dependency-manifest-panel)
keeps the implementation evidence, receipt identities and source limitations.
The [output contract](../contracts/core-layout-export-set.md#dependency-manifest)
keeps the supported curved plain-line scope and excluded inputs.
This decision accepts that representative evidence. It does not extend the supported scope.

The native proof gave a PASS result for 14 cases. The real-GUI proof gave a PASS result for eight scenarios
with CSV on and off. Each completed Core output set includes schema-1 JSON.
Its ten dependency records identify canonical information, installed product
source, FreeCAD/exporters and seven inherited lineage groups.
The checks compare output hashes and preserve the editable model and previous output.

[Manifest tests](../../tests/validate_core_dependency_manifest.py) bind all seven
lineage groups to the canonical provenance register.
They reject missing lineage, false clearance claims and changed classifications.
Restricted, reference-only and unknown inputs cannot produce `project-cleared` output.
The separate [manifest clearance gate](../../tools/validate_dependency_manifest.py),
[licensing controls](../../tests/validate_licensing_controls.py) and
[package checks](../../tests/validate_phase4_chair_definition.py) keep their own boundaries.
Those separate checks do not show that Core Generate uses a chair package.
Selected export receives no new manifest requirement or acceptance.

The assessment done independently compared all 82 native and 103 GUI source hashes
with the accepted `main` commit. Both host receipts match their recorded hashes.
No new FreeCAD or real-GUI proof is necessary for this documentation alignment.
Keep `CM-SR-01`, the initial failed review, failed proofs and their classifications.
The corrected evidence does not replace that history.

**Safety/risk panel:** Richard is the project owner, panel chair and deciding
authority. `/root` supplies this alignment.
Read-only reviewer `/root/exit9b4_acceptance_risk` examined the acceptance scope,
source identities, evidence, limitations and all 24 risk records.
The reviewer did not write product source, tests or canonical prose for this change.
The agents share one team and workspace. This is not external organisational independence.

The recommendation is **Proceed with bounded conditions**.
The panel records no unresolved dissent or blocker. It identifies no critical fact that is missing.
All 24 risk states, severities, owners, deadlines, treatments and controls stay unchanged.
No risk closes. Each risk owner keeps the duties in the [current register](risks.json).

PR-09 stays Critical/Open/Partial. PR-13 stays Critical/Open/Effective for its current scope.
PR-17 stays Critical/Open/Partial.

The panel receipt is `tmp/exit9b4-acceptance-risk.json` in the primary repository,
SHA-256 `5a92fe95c199209c8e53a26adcfa83f45b47ee81a1d3b67e59276120baec9f9a`.

| Bounded condition | Owner and deadline |
| --- | --- |
| Keep this acceptance within the D-P9-016 scope, evidence and operating conditions. | Project owner and Phase 9B export owner, at admission and for each later claim. |
| Preserve all risk duties, failed evidence and existing acceptance boundaries. | Technical Author Lead and current phase owner, before and after draft publication. |
| Keep the completed worktree until independent preservation is proved. Do not force retirement. | Change owner, during this cycle and before any later retirement. |
| Complete independent review. Complete the Documentation Review lifecycle. CI must give a PASS result for the exact PR head. Publish one draft PR. Stop for integration authority. | Technical Author Lead, independent reviewer and change owner, before draft publication. |

**Preserved limitations:** Output stays private-development. Project status stays `unknown`.
Reference-only and unknown classifications stay unchanged. This decision supplies no compatible rights disposition.

Hashes of installed source files do not show the identity of Python code in memory or all host files.
A canonical signature does not show independent shape regeneration.
The qualified Linux ext4 conditions and supported failure model stay.
There is no assurance for every file system. There is no assurance against changes that another process makes at the same time to cause damage.
There is no assurance that files stay available after a system interruption
or that recovery occurs after FreeCAD stops and starts again.

Geometry, package bytes, numerical limits, the 113-entry register and legacy-retirement conditions stay unchanged.
D-P6-008 stays Deferred — unmet. TERM-R04 stays open.

This decision accepts no physical fit, preload, retention, manufacturing capability,
production package, output clearance, rights, performance result or release.
It accepts no other exit and closes no phase. Start no new implementation.
Publish one exact-green draft PR. Then stop for integration authority.

## Phase 9B Core dependency manifest panel

**Date and decision:** 2026-10-13, D-P9-016. The owner authorises the Core Generate
dependency-manifest policy and one bounded implementation towards Exit 9B-4.
The [architecture](../ARCHITECTURE.md#d-p9-016-core-generate-dependency-manifest)
owns the policy. The [output contract](../contracts/core-layout-export-set.md#dependency-manifest)
owns its implementation requirements. The [decision register](gate-decisions.json)
keeps the owner authority and exclusions.

The owner states:

> As project owner, I approve the proposed Level 3 Core Generate dependency-manifest change for Exit 9B-4.
>
> Authorise the necessary alignment and one bounded implementation under existing repository governance.
>
> Preserve all existing acceptance boundaries. Publish one exact-green draft PR, then stop.

**Outcome:** The usual Core Generate route must include one schema-1 JSON file.
That file belongs to the same full output set as the selected output files
and optional CSV.
The first bounded scope covers curved plain-line `TrackTemplateCompound`
shapes and centrelines. Missing manifest input data must stop the directory
operation with a diagnostic that the operator can see. The operation must also stop if these
data do not agree or are not in the supported bounded scope.

This restriction changes export availability.
It does not remove the committed editable Generate result.
The manifest must identify output hashes, canonical information, product
source, FreeCAD and its exporters, and applicable existing classifications.
It keeps `reference-only` and `unknown` status.
It does not change a B14 fixture copy into evidence of a new B16 Generate
operation. The Core Generate GUI proof must prove this source difference.

**Safety/risk panel:** Richard is the project owner, panel chair and deciding
authority. `/root` presents the bounded change.
Read-only reviewer `/root/after170_phase9b_choice` examined the approved policy,
API, architecture, security and provenance boundaries and all 24 risk records.
The reviewer wrote no product source, tests or canonical prose.
The reviewer previously supplied read-only programme advice.
The agents share one team and workspace. The review does not operate independently of that team.

The recommendation is **Proceed with bounded conditions**.
The receipt for the review done independently is
`tmp/core-dependency-manifest/architecture-risk-review.json`, SHA-256
`0e8e425ed888055de2c82473ed60853becf7e719bf97327b3cb6d2a6bc6352c5`.
The panel records no unresolved dissent or authority blocker.
The implementing agent must prove strict input checks and full manifest
input data for the supported bounded scope.
The implementing agent must also prove hashes of temporary output files and the specified
conditions that stop output.
Qualified FreeCAD, GUI and source review done independently must finish before the
draft PR with a PASS result from CI for its exact candidate.
This panel recommendation does not accept the product change.

All 24 risk states, severities, treatments, controls, owners and deadlines stay
unchanged in the [risk register](risks.json). No risk closes.
PR-09 stays Critical/Open/Partial. PR-13 stays Critical/Open/Effective for its
current scope. PR-17 stays Critical/Open/Partial.
The named risk owners retain their duties and deadlines.

PR-01 and QA-R03 keep wider workflow coverage.
PR-09 keeps output rights-state controls.
PR-16 keeps input and invalidation duties.
PR-17 keeps document preservation and recovery duties.
PR-13 keeps backup and restore duties.

PR-15 and QA-R04 keep performance duties.
PR-22 keeps independent acceptance.
PR-10 and PR-18 keep comparison and removal conditions.
The chair and rights-state risks keep their production evidence duties.

**Implementation evidence:** The bounded Core route records ten `dependencies`
items: canonical information, installed product source, FreeCAD/exporters and
seven existing lineage groups.
It writes the schema-1 JSON with hashes of output files in the same full
output set. CSV stays optional.
Standalone schema checks give a PASS result.
Checks of rejected data, the directory operation and previous routes also
give a PASS result.

The qualified native proof gives a PASS result for 14 cases on FreeCAD 1.1.4.
It keeps the B14 fixture copy, previous outputs and exact state of the
editable document unchanged.
It proves legacy output comparison, equal hashes of canonical information
and source across repeated operations, and save/reopen preservation.
The software rejects different, translated, rotated and reversed planned shapes
before it writes temporary output.
This proof starts from a legacy document copy.
It does not prove a new B16 Generate operation.

The receipt is
`tmp/core-export-atomic/native-runs/20261013T185758530171Z/result.json`, SHA-256
`4c06b93bc25b900e505078122aa95a026d1ec4804bccf58452e667cab3a4d4ee`.

The Core Generate GUI proof gives a PASS result for all eight scenarios on
the same qualified host profile.
The current B16 route makes curved plain-line `TrackTemplateCompound` shapes
and centrelines. The source stays B15.
Output with CSV contains 15 files. Output without CSV contains 14 files.
Each output set includes the schema-1 JSON and hashes of the output files.

The GUI proof keeps previous output, the editable model, selection,
preferences and save/reopen state unchanged.
Malformed or missing manifest input data give diagnostics that the operator can see.
No completed output file becomes available in these conditions.
The summary distinguishes CSV from JSON and states that the output rights
state stays unresolved.
The folder-open check verifies its selected path only.
It does not prove an operating-system file-manager launch.

The receipt is
`benchmark-output/freecad-bridge/phase7-core-layout-export-workflow-runs/core-dependency-manifest-2/run.json`, SHA-256
`3d19b16ad873ce845e0cb337072250063c9594436d8eff1e4dc67f4c8e3a9bdf`.

Review done independently found a missing planned-shape check, recorded as
`CM-SR-01`. Its first repair gave a PASS result for the native fixture copy
but rejected a new Generate operation.
Live GUI diagnosis identified the existing document-assignment difference.
The corrected comparison checks that initial `Shape.Placement.toMatrix().A`
values are equal. It also checks that the `exportBrepToString()` bytes from
temporary copies are equal. It changes no source shape or tolerance.

The corrected native and GUI proofs use that corrected source.
Initial failures, diagnostic evidence and classifications stay in
`tmp/core-dependency-manifest/`.
Installed-file hashes do not prove the identity of Python code in
memory or all files that FreeCAD uses.
Source hashes are equal before and after each new qualified process.

The source review done independently gives **PASS** with no open blocker.
The reviewer reconciles the corrected native and GUI proofs with the source.
The receipt is `tmp/core-dependency-manifest/source-review-final.json`, SHA-256
`2093fd17a9807e695ab98dbe590641c74d9561315aa6a7495370f220d75e23cc`.
The initial review receipt and finding remain unchanged.

**Limits and next boundary:** Phase 9A stays closed at 4/4 for its frozen
reference-only scope. Phase 9B stays Open at 2/6.
Only Exits 9B-2 and 9B-5 are Evidenced and owner-accepted.
Exits 9B-1, 9B-3, 9B-4 and 9B-6 stay Pending.
D-P6-008 stays Deferred — unmet. TERM-R04 stays open.

Railway calculations, shapes, the 113-entry register, numerical limits, selected export and frozen
B14/B15 stay unchanged. Output stays private-development.
Project status stays `unknown`.
No physical fit, preload, retention, manufacturing, rights-state, production,
performance or release acceptance follows.
The qualified Linux ext4 conditions and supported failure model stay.
There is no assurance that files stay available after a system interruption
or that recovery occurs after FreeCAD stops and starts again.

After CI gives a PASS result for the exact candidate, publish one draft PR.
Then stop. Do not merge. Do not start one more outcome.

## Current owner view
| Field | Current position |
| --- | --- |
| Current state | Phase 9A stays closed at 4/4 under [D-P9-010](../history/phase-closeouts/PHASE9A_CLOSEOUT.md#phase-9a-closeout-panel). Phase 9B is Open at 3/6 under [D-P9-012](#phase-9b-exit-2-acceptance-panel), [D-P9-015](#phase-9b-exit-5-acceptance-panel) and [D-P9-017](#phase-9b-exit-4-acceptance-panel). Only Exits 9B-2, 9B-4 and 9B-5 are Evidenced and owner-accepted. Exits 9B-1, 9B-3 and 9B-6 stay Pending. |
| What changed | [D-P9-018](#lms-chair-record-and-templot-development-panel) records the completed LMS chair development model as the owner's "prototype". More LMS chair development is paused until after Phase 11. |
| What now works | The LMS chair that the project keeps has three parts: a complete casting, a key and a rail. Its native checks and FreeCAD reload give PASS results. Independent review gives PASS WITH FINDINGS for the native development model. |
| Limitations/findings | The full LMS validation suite gives a FAIL result because STEP reload gives a FAIL result. STEP output is not qualified. Physical fit, production and rights clearance are not accepted. All previous acceptance limits and all 24 risk duties stay. <br><br>D-P6-008 stays Deferred — unmet. TERM-R04 stays open. Output stays private-development. Project status stays `unknown`. |
| Owner decision | Make all chairs in the Templot source for private modelling and TrackTemplate development. Keep the source geometry and provenance. This direction accepts no phase exit and gives no public distribution authority. |
| Next action | Make and validate the Templot chairs through the TrackTemplate path that the project uses. Record source coverage and unresolved geometry accurately. Preserve the LMS model and its evidence with a FAIL result. Complete independent review and the Documentation Review lifecycle for this documentation alignment. |

<a id="phase-9b-exit-5-acceptance-panel"></a>

## D-P9-015 Phase 9B Exit 5 acceptance panel — 2026-10-13

**Decision boundary:** Richard accepts only Exit 9B-5 under D-P9-013/D-P9-014
with all recorded limitations. The accepted source is protected `main`
`4bc8508b6f4ce4ec0056a684181e91a650da289e` after
[PR #168](https://github.com/Richard-Gnitnub/tracktemplate/pull/168).
Its tree is the same as the tree at reviewed head `00a5f2e5c8b8965ba80e7bd9b99e63510316eadc`.
[CI run 38409599795](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/38409599795)
gave a PASS result for the source at that commit.

Phase 9B is Open at 2/6. Only Exits 9B-2 and 9B-5 are Evidenced and owner-accepted.
Exits 9B-1, 9B-3, 9B-4 and 9B-6 stay Pending. All six exact criteria stay unchanged.
Phase 9A stays closed at 4/4 for its frozen reference-only scope.

**Exact owner instruction:**

> As project owner, I accept Phase 9B Exit 9B-5 as Evidenced and owner-accepted under D-P9-013/D-P9-014, with all recorded limitations preserved. Authorise the necessary Level 3 alignment and one exact-green draft PR. Do not merge or begin new implementation.

**Exact criterion:**

> Export failure cannot replace only part of an accepted output set or corrupt the editable model.

**Accepted evidence:** The independent assessment examined the recorded evidence
for the usual B16 `Core Generate` and `Export selected production items` routes.
The [D-P9-013 panel](#phase-9b-core-export-policy-panel) and
[D-P9-014 panel](#phase-9b-selected-export-policy-panel) keep the detailed proofs.
No new FreeCAD or real-GUI proof is necessary for this documentation alignment.

| Accepted duty | Evidence and limit |
| --- | --- |
| Full output and previous files | The two usual routes use the same directory operation without replacement. The qualified error conditions preserve previous output. CSV stays optional. The directory includes CSV when the operator selects it. |
| Editable state | `CoreExportDocument` keeps temporary objects outside the editable `App.Document`. The qualified errors, source identity/history checks and save/reopen evidence show that the editable state stays the same. A failed close can keep an identified temporary `App.Document`. |
| Operator decision and results | The selected route preserves the selected data and paths through the operator decision and file operations. After the final directory becomes available, results keep completed counts and paths if an error occurs. Errors before that operation report no completed files. |
| Formats and chairs | Representative SVG/DXF/STL/STEP and optional CSV checks pass. The selected real-GUI tests use SVG with CSV on and off. Live turnout and crossover chair decisions stay unchanged. |

The assessment is `tmp/after168/exit9b5-independent-assessment.json` in the primary repository,
SHA-256 `613fbb737482d448a96cf509a9619006bd2515a22e1d393f6c6ffab6e07a61a3`.
It identifies each receipt, source comparison, limitation and finding disposition.
The final independent source review has SHA-256
`0caeeb6ca2e3970151a9d9c31fa7365d93727b72ccd676b923a9d0d6adb77a83`.
The final selected validation receipt has SHA-256
`7335fe74f43388adddd78bcd7d4c633797a79cc81af411abbbe6badcf5d41743`.

The assessment uses the recorded Core evidence. It gives no new Core check of `main` at this admission.
The Core command, file adapter, `CoreExportDocument` and policy stay the same.
Subsequent changes connect the selected route and keep the previous comparison test setup.
Independent source review and affected standalone Python checks examine those changes.
The final selected FreeCAD and real-GUI proofs also use those same operations.

**Findings:** `SR-01`/`SR01-retained` is satisfied only for the usual selected route.
D-P9-014 supplies accurate operator controls and makes all selected files available together.
`selected-whole-set-retained` is satisfied only for that route by the shared directory operation without replacement.
The qualified error conditions prove that previous output stays the same.

The previous APIs that write files separately keep their limits. They receive no new acceptance.
The final independent source review records `SEL-QR-01` and `SEL-QR-02` as resolved.
Keep the first blocked review, failed proofs or proofs that were not completed and frozen B14/B15 evidence.

**Safety/risk panel:** Richard is the project owner, panel chair and deciding authority.
`/root` gives the information for this documentation alignment. `/root/selected_set_architecture_risk` challenges the evidence and all 24 risks.
That reviewer authored no retained implementation or test change.
Previous work included architecture advice, source review and the independent assessment.

The agents share one team and workspace. This is not external organisational independence.
The Technical Author Lead records the decision but does not supply acceptance authority.

The recommendation is **Proceed with bounded conditions**.
The panel receipt records `unresolved_dissent=[]`, `substantive_blockers=[]` and `critical_missing_facts=[]`.

All 24 risk states, severities, owners, deadlines, treatments and control effectiveness values stay unchanged.
No risk closes. Each risk owner keeps the duties in the [current register](risks.json).

PR-09 stays Critical/Open/Partial. PR-13 stays Critical/Open/Effective for its current scope.
PR-17 stays Critical/Open/Partial. The other workflow, recovery, rights, performance and independent acceptance duties stay.

The panel receipt is `tmp/exit9b5-admission/risk-panel-input.json`, SHA-256
`fcb5843b53a6962ebc111664f8e5c13dfa0660506eb4d8e043120433f2b26f88`.

| Bounded condition | Owner and deadline |
| --- | --- |
| Keep this acceptance within the named routes, source, evidence and operating conditions. | Project owner and Phase 9B export owner, at admission and for each subsequent claim. |
| Preserve all risk duties, historical failures, comparison paths and the different Entry/Exit authority. | Technical Author Lead and current phase owner, before draft publication and thereafter. |
| Record the two previous selected finding dispositions only for the usual route. | Phase 9B selected-export owner and Technical Author Lead, in this alignment. |
| Complete the sole Documentation Review, final validation, independent review of test changes and CI checks for the PR head. Publish one draft PR with that head. Stop. | Technical Author Lead, independent reviewer and change owner, before draft publication. |

**Preserved limitations:** Qualification applies only to the existing Linux ext4 host with an operator-controlled output directory.
Unsupported directory operations fail closed. There is no assurance for every filesystem or malicious concurrent changes.
There is no assurance that files stay available after a system interruption or recovery after FreeCAD stops and starts again.
D-P6-003/D-P6-004 and accepted D-P6-005 keep their own Entry/Exit authority.
Their pair recovery does not become authority for one of the two usual routes.

Historical GUI recipes keep their recorded host and policy limits. This cycle did not change or repeat every historical GUI recipe.
GUI restoration evidence starts at the adapter invocation. It does not accept raw selection event history before the operator decision.
The folder-action proof checks the target passed to the opener without starting the operating-system file manager.
Crossover output after save/reopen still has the recorded serialisation difference.
This decision gives no universal byte-equivalence claim or new numerical tolerance.

Geometry, package bytes, numerical limits, the 113-entry register and legacy-retirement conditions stay unchanged.
D-P6-008 stays Deferred — unmet. TERM-R04 stays open. Output stays private-development.
Project status stays `unknown`.

This decision accepts no physical fit, preload, retention,
manufacturing capability, production package, output clearance, rights, performance result or release.
It closes no phase and accepts no other exit.

**Publication boundary:** Complete only the necessary Level 3 documentation alignment and validation.
Publish one draft PR after CI gives a PASS result for its exact head.
Do not merge. Do not start new implementation.

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

All six criteria stay unchanged. Only Exits 9B-2, 9B-4 and 9B-5 are Evidenced — owner-accepted.
[D-P9-012](#phase-9b-exit-2-acceptance-panel) accepts Exit 9B-2 on 2026-10-11.
[D-P9-015](#phase-9b-exit-5-acceptance-panel) accepts Exit 9B-5 on 2026-10-13.
[D-P9-017](#phase-9b-exit-4-acceptance-panel) accepts Exit 9B-4 on 2026-10-13.
Exits 9B-1, 9B-3 and 9B-6 stay Pending.

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

## S1 hole surfaces from drawing No. 4 — 2026-10-15

This Level 2 change adds two connected surfaces in one hole.
It supplies evidence for part of Exit 9B-1.

The project owner selected alternative A: the printed `1 7/16 in` dimension gives an opening of `36.5125 mm` across its rounded top edge.
This selection applies only to the Level 2 change. The drawing does not show whether alternative A or B applies.

Alternative B extends the straight wall to the top level and applies the dimension there.
For alternative B, the calculated diameter of the opening is about `39.4952576 mm`.

The [Python software](../../tracktemplate/domain/chair_base_nominal.py) uses specified `Fraction` inputs and gives `Decimal` results.
The [FreeCAD software](../../tracktemplate/adapters/freecad/chair_base_nominal_exact.py) makes one open `Part.Shell` with two connected surfaces.
These surfaces do not make a closed volume.
The software adds no outer base surface and does not set the position of a chair.
The outline and lower openings do not change.

The [standalone Python checks](../../tests/validate_phase9b_chair_base_nominal.py) and [FreeCAD checks](../../tests/freecad_validate_phase9b_chair_base_nominal.py) on the qualified host profile give PASS results.
The checks use results calculated independently of the software.
The checks give PASS results when the software makes the same surfaces again.
The persistence checks (save/reopen) and regression tests for the frozen reference also give PASS results.
Three FreeCAD images show the two surfaces, a section and the rounded top edge.
Local evidence is in `tmp/nominal-hole-mouth/visual-proof-qualified/No4-hole-mouth-native-visual-proof.json`.

The inputs come from printed dimensions, not from measurements of a chair.
The drawing revision and the rights state for the source stay unknown.
The result is not a complete base or chair. It gives no acceptance for physical fit or production.

The numerical checks, frozen S1 geometry, canonical definitions and 113-entry register do not change.
Phase 9B stays Open at 3/6. Exits 9B-1 and 9B-3 stay Pending.

## Connected S1 bottom and hole surfaces — 2026-10-15

This Level 2 change connects the bottom surface to the surfaces of three holes from the No. 4 source.
It supplies evidence necessary for work on Exit 9B-1.

The [FreeCAD software](../../tracktemplate/adapters/freecad/chair_base_nominal_exact.py) makes one open `Part.Shell` with seven connected `Part.Face` objects.
The surfaces connect at each bottom hole edge.
The outer edge and three top openings stay open.
The surfaces do not make a closed volume.
The local No. 4 result keeps the previous dimensions, hole positions and rounded top edges.

The standalone Python checks and FreeCAD checks on the qualified host profile give PASS results.
These checks use independently calculated results.
The local No. 4 checks give PASS results for connected edges and persistence (`save_reopen`).
They also give PASS results when the software makes the same surfaces again.

FreeCAD displays show the connected surfaces.
A second display shows the result when FreeCAD cuts through two holes.
Local evidence is in `tmp/nominal-underside-shell/visual-proof-final/No4-connected-underside-native-visual-proof.json` and `tmp/nominal-underside-shell/visual-inspection-final.json`.

The previous conditions for the [chair component](#s1-base-shape-from-drawing-no-4--2026-10-11), [hole positions](#s1-base-holes-from-drawing-no-4--2026-10-11) and [alternative A](#s1-hole-surfaces-from-drawing-no-4--2026-10-15) stay the same.
The inputs use dimension values in the No. 4 source, not measured chair dimensions.
The source version and rights state stay unknown.
This result does not supply all surfaces of this chair component or chair. It gives no acceptance for physical fit or production.

The limits for the checks, frozen S1 shapes, `ChairDefinition` data and the “113-entry register” do not change.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.

## S1 chairs at C10 positions — 2026-10-21

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).
The [command](../../tracktemplate/compatibility/chair_reference_preview.py) makes a different `App.Document` when a person starts it. It does not write that `App.Document` to a file.
The [software](../../tracktemplate/adapters/freecad/chair_reference_preview.py) uses the previous software for the five S1 components and makes seven `Part::Feature` items.
For the C10 input in a new file with the source data, the window title shows `37/54 S1; 17 unresolved`.

The evidence identifies all 168 chair positions. It gives a cause for each of the 17 S1 positions that the software does not show.

The [test with standalone Python](../../tests/validate_phase9b_s1_reference_preview.py) gives 177 PASS results.
The previous checks in `foundation-final.log`, `workflows-final.log`, `export-contract-final.log` and `dependency-manifest.log` also give PASS results.
The previous result from a qualified host profile for FreeCAD stays in `tmp/s1-preview/final-validation-exception-01/native-05/result.json`.

A person can see the FreeCAD window title during the [test](../../tests/freecad_validate_phase9b_s1_reference_preview.py).
The test gives PASS results for `source_unchanged`, `undo_redo`, `transaction_failure_cleanup` and `analysis_rejections`.
The `analysis_rejections` data identify the `missing` and `stale` conditions.
The file `tmp/s1-preview/engineering-repair-20261021-01/gui-01-verification.json` contains the result and identifies the clear `overview.png` and `chair-closeup.png` files.

Only the test changed in the last repair. Product software stayed the same.
The independent reviewer gives a PASS result for the source and tests in `tmp/s1-preview/engineering-repair-20261021-01/quality-review.json`.

The initial evidence with FAIL results and the `BLOCKED` quality review stay in `tmp/s1-preview/`.
The `native-04` evidence has no data for the source before and after its check with a FAIL result.

The conditions in D-P9-018 stay the same.
This result gives no acceptance for physical fit, the direction of the `S1CentralKey` component, persistence, production, export behaviour or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## S1J chairs at C10 positions — 2026-10-21

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [command](../../tracktemplate/compatibility/chair_reference_preview.py) makes a different `App.Document` when a person starts it. It does not write that `App.Document` to a file.
The [software](../../tracktemplate/adapters/freecad/chair_reference_preview.py) makes five S1J components in seven `Part::Feature` items.
For the copied C10 input, the window title shows `4/5 S1J; 1 unresolved`.
The evidence identifies all 168 chair positions and gives a cause for each position that the software does not show.
The S1 command gives the same `37/54 S1; 17 unresolved` result.

The [S1J selection test](../../tests/validate_phase9b_s1j_reference_preview.py) gives 28 PASS results.
The [component test](../../tests/validate_phase9b_chair_s1j.py), S1 tests and previous regression tests also give PASS results.
The [FreeCAD test](../../tests/freecad_validate_phase9b_s1_reference_preview.py) gives PASS results on the qualified host profile for S1J and S1.
These results include `source_unchanged`, `undo_redo`, `transaction_failure_cleanup` and `analysis_rejections`.
The independent reviewer examined clear `overview.png` and `chair-closeup.png` images for S1J and S1.
The results and images stay in `tmp/s1j-preview/gui-s1j-02/` and `tmp/s1j-preview/gui-s1-01/`.

The checks compare only `S1JBasePlinth` and `S1JRailSeat` values with Templot data.
They give a PASS result in `tmp/s1j-preview/source-components-result.json`.
These checks do not compare the complete `S1JOuterJaw` and `S1JInnerJaw` shapes with Templot data.

Local evidence keeps `private-input-build-01` and `native-s1j-01` with FAIL results.
The `native-s1j-01` result has the failure class `environment-or-profile-defect`.
The image at `tmp/s1j-preview/gui-s1j-01/chair-closeup.png` does not show a chair.
Local evidence also keeps the initial `BLOCKED` quality review in `tmp/s1j-preview/quality-review-01.json`.

The first repair changed only `build_reference_inputs.py`. The second changed only `_images` in the FreeCAD test.
Product software stayed the same during those repairs.
The independent review gives a PASS result for the source and tests in `tmp/s1j-preview/quality-review-02.json`.

The conditions in D-P9-018 stay the same.
This result gives no acceptance for physical fit, the direction of the `S1JCentralKey` component, persistence, production, export behaviour or phase exits.
This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## S1 and S1J chairs together at C10 positions — 2026-10-21

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [command](../../tracktemplate/compatibility/chair_reference_preview.py) makes one new `App.Document` for S1 and S1J chairs from the same C10 input.
It does not write that `App.Document` to a file.
The [software](../../tracktemplate/adapters/freecad/chair_reference_preview.py) makes five components for each chair type.
The `App.Document` has twelve `Part::Feature` items.
The shapes of the chair components and the packages do not change.

For the copy of the C10 input, the window title shows `41/59 S1/S1J; 18 unresolved; 37/54 S1; 4/5 S1J`.
The evidence identifies all 168 chair positions.
It gives a cause for each of the 127 positions that the software does not show.

The [test with standalone Python](../../tests/validate_phase9b_s1_s1j_reference_preview.py) and the previous S1, S1J and command tests give PASS results.
The [FreeCAD test](../../tests/freecad_validate_phase9b_s1_s1j_reference_preview.py) gives PASS results on the qualified host profile.
The test also gives PASS results with the FreeCAD window open.
These results include `common_context`, `before_document_rejections`, `rollback_owned_document`, `subprecision_rejection`, `source_unchanged`, `foreign_unchanged`, `undo_redo`, `transaction_failure_cleanup` and `analysis_rejections`.
The results stay in `tmp/combined-preview/native-combined-02/` and `tmp/combined-preview/gui-combined-01/`.

The independent reviewer examined the four `overview.png` and `chair-closeup.png` files in `gui-combined-01/s1/` and `gui-combined-01/s1j/`.
The independent review gives a PASS result for the source and tests in `tmp/combined-preview/quality-review-01.json`.
Local evidence keeps the previous `native-combined-01` result and the `proof-drafting/` files.
The `native-combined-01` result is only for previous source and tests.
The previous S1 and S1J evidence, with the `native-04` limitation, does not change.

The conditions in D-P9-018 stay the same.
This result gives no acceptance for physical fit or the direction of the `S1CentralKey` and `S1JCentralKey` components.
It gives no acceptance for persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## Remaining S1 and S1J chairs at C10 positions — 2026-10-21

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

For the C10 test input, the [command](../../tracktemplate/compatibility/chair_reference_preview.py) now shows `59/59 S1/S1J; 0 unresolved; 54/54 S1; 5/5 S1J`.
The result identifies all 168 positions, with the 109 positions that the command does not show.
The [software](../../tracktemplate/domain/chair_placement.py) uses the `centre_point` and `local_rail_tangent` values for 18 more chairs.
It gets the direction from `gauge_face_points` and `outer_face_points` with `Fraction` values.
The previous 41 `S1Placement` and `S1JPlacement` values do not change.
The chair components, packages and source data do not change.

The [test with standalone Python](../../tests/validate_phase9b_chair_frame_recovery.py) and the [command test](../../tests/validate_phase9b_chair_frame_preview.py) give PASS results.
The S1 and S1J tests and the [test for the two chair types](../../tests/freecad_validate_phase9b_s1_s1j_reference_preview.py) give PASS results on the qualified host profile.
The test for the two chair types also gives a PASS result with the FreeCAD window open.
The tests compare source data before and after the command, `Undo` and `Redo`.
The `transaction_failure_cleanup` check gives a PASS result.
The results stay in `tmp/chair-frame-recovery/native-s1-01/`, `native-s1j-01/`, `native-combined-01/` and `gui-combined-01/`.

The independent review gives a PASS result for the source and tests.
The result stays in `tmp/chair-frame-recovery/quality-review-01.json`.
The reviewer examined the four `overview.png` and `chair-closeup.png` files in `gui-combined-01/s1/` and `gui-combined-01/s1j/`.

All previous evidence, with the `native-04` limitation and the independent review results of BLOCKED, stays available.
The conditions in D-P9-018 stay the same.
This result gives no acceptance for physical fit or the direction of the `S1CentralKey` and `S1JCentralKey` components.
It gives no acceptance for persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## L1 chair at 4 mm/ft — 2026-10-22

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/application/chair_model_research.py) uses the previous L1 result with `length_basis = "full-size"`.
It multiplies each length by `5/381` for the `4 mm/ft` result.
The five chair components contain seven `Solid` shapes.
The `outer-jaw` component keeps three parts: `body`, `bevel-negative` and `bevel-positive`.
Each part is a `Solid`.

The source input keeps its `source_mark_quantum_mm` value for `8 mm/ft`.
This result does not give sufficient evidence that the shapes agree with Templot output at `4 mm/ft`.
For the C10 test input, the previous S1 and S1J results and all 59 chair positions do not change.
This change adds no chairs at the other 109 positions.

The [test with standalone Python](../../tests/validate_phase9b_chair_l1_model.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_chair_l1_model.py) gives PASS results with the qualified host profile and when a person can see the FreeCAD display.
The tests calculate values from the previous L1 result.
They compare these values with the new result.
The tests also compare source data and the condition of the `App.Document` before and after they operate.
The results stay in `tmp/l1-model-scale/standalone-l1-model-02.json`, `native-02/` and `gui-02/`.

The independent review gives a PASS result for the source and tests.
The result stays in `tmp/l1-model-scale/quality-review-02.json`.
The reviewer examined `gui-02/overview.png` and `gui-02/chair-closeup.png`.

The previous limitations for the `4 mm/ft` and `6 mm/ft` source inputs do not change.
The previous `common_edge_count = 0` result from FreeCAD for the `outer-jaw` parts stays a limitation.
All previous FAIL results and the initial quality review with a BLOCKED result stay available.
The limitations of the previous L1, S1 and S1J evidence, with the `native-04` limitation, do not change.

The conditions in D-P9-018 stay the same.
This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## L1 chair display for B16 — 2026-10-22

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/transition_workflow.py) supplies `preview_l1_reference_chair` for B16.
It makes a new `App.Document` with `FileName = ""` for the previous L1 result.
The five chair components contain seven `Solid` shapes.
A person can select each chair component and change its `Visibility` value.
For the C10 test input, all 59 S1/S1J chair positions stay the same.
This change adds no chairs at the other 109 positions.

The [test with standalone Python](../../tests/validate_phase9b_l1_reference_preview.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_l1_reference_preview.py) gives PASS results with the qualified host profile and when a person can see the FreeCAD display.
The FreeCAD test gives PASS results for `Undo`, `Redo` and `transaction_rollback`.
The source data and each previous `App.Document` stay the same.
The results stay in `tmp/l1-reference-preview/standalone-01.log`, `native-04/` and `gui-02/`.

The independent review gives a PASS result for the source and tests.
The result stays in `tmp/l1-reference-preview/quality-review-03.json`.
The reviewer examined `gui-02/overview.png` and `gui-02/chair-closeup.png`.

All previous FAIL results and quality reviews with BLOCKED results stay available.
The [previous L1 limitations](#l1-chair-at-4-mmft--2026-10-22) and the S1/S1J limitations do not change.
The previous S1 `native-04` limitation does not change.
This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## S1 and S1J chairs on a C10 crossover — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/transition_workflow.py) supplies `preview_s1_s1j_crossover_reference_chairs` for B16.
It uses the previous software for chair components and their positions on the C10 crossover.
The current `b4_result` with `applied = True` is necessary.

For the copied `XO-001` test input, the result contains 123 S1 chairs and 12 S1J chairs.
The other 220 positions stay without these chair components.
The software makes a new `App.Document` with `FileName = ""` for the result.
A person can select each `Part::Feature` and change its `Visibility` value.

The [test with standalone Python](../../tests/validate_phase9b_crossover_reference_preview.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_crossover_reference_preview.py) gives a PASS result with the qualified host profile.
The same test gives a PASS result when a person can see the FreeCAD display.
The source data and each previous `App.Document` stay the same.
The FreeCAD test gives PASS results for `Undo`, `Redo` and `transaction_rollback`.
The results stay in `tmp/crossover-chair-preview/`, with `native-02/`, `gui-02/` and `turnout-native-02/`.

The independent review of the source gives a PASS result.

The previous turnout result keeps its 59 S1/S1J positions and 109 other positions.
All previous FAIL results and review results of BLOCKED stay available.
The previous S1 `native-04` limitation does not change.
The [previous L1 limitations](#l1-chair-at-4-mmft--2026-10-22) and the S1/S1J limitations do not change.
This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## P chair component `PSEAT` — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/application/chair_research.py) uses nine lengths from a `ChairDefinition` to make the `PSEAT` chair component.
The result has one `Solid` shape with `length_basis = "full-size"`.
The inputs are Templot data with `reference-only` status.
The output stays in private-development status.

The [test with standalone Python](../../tests/validate_phase9b_chair_p_seat.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_chair_p_seat.py) gives a PASS result with the qualified host profile.
The same test gives a PASS result when a person can see the FreeCAD display.
The source data and each previous `App.Document` stay the same.
The independent review of the source and tests gives a PASS result.
The results stay in `tmp/p-slide-seat/`, with `native-02/`, `gui-02/` and `owner-repair-20261023/`.

The result is only the `PSEAT` chair component.
All previous FAIL results and review results of BLOCKED stay available.
This result gives no acceptance for chair positions, physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## Chair display from previous files — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/transition_workflow.py) supplies `preview_private_catalogue_chair` for B16.
It reads 30 previous `FCStd` files for 29 different `label` values.
The two `CC` source files have different inputs.
The 30 results contain 951 `Part::Feature` objects in new `App.Document` objects with `FileName = ""`.

The software uses the previous shapes. It does not calculate new shapes.
The `xml_placement` and `placement_matrix` values can give different positions. The result keeps the two values.

The [test with standalone Python](../../tests/validate_phase9b_chair_catalogue.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_chair_catalogue.py) compares all 30 results with copies of their source files.
It gives a PASS result with the qualified host profile.
For `P` and `AB`, the same test gives a PASS result when a person can see the FreeCAD display.

The tests give PASS results for `Undo`, `Redo`, `transaction_rollback` and the changes to source data and shapes that the software rejects.
The source files and each previous `App.Document` stay the same.
The results stay in `tmp/private-chair-catalogue/`, with `native-03/` and `gui-02/`.

The independent review of the source and tests gives a PASS result.
The reviewer did not write this change.
The result stays in `tmp/private-chair-catalogue/quality-review-03.json`.

The software adds no chair positions.
For C10 and `XO-001`, the 109 and 220 other positions stay without these chair components.
The output stays in private-development status.

All previous FAIL results and review results of BLOCKED stay available.
The previous [S1, S1J and L1 limitations](#s1-and-s1j-chairs-on-a-c10-crossover--2026-10-23) do not change.
This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## P chair components at C10 positions — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) supplies `preview_private_catalogue_p_chairs` for B16.
For `TO-001`, it shows 22 chair components at each of 14 `P` positions.
These positions have `chair_code = 2` and `assignment_status = CHAIR_ASSIGNMENT_CONFIRMED`.
Their `prototype_timber_identifier` data are `S1`, `S2`, `S3`, `S4`, `S5`, `S6` and `S7`, with `rail_role = "stock rail"`.

The software uses the previous `P` shapes from `basic-04`.
It does not calculate new chair shapes or change their dimensions.
The software does not show the `display_rail` source component as a chair component.
The input conditions are C10 at 1:76.2, `track_gauge` of 16.5 mm, `flangeway` of 1 mm and the full `Templot556b-CL-EMGS-S4Soc-Code75-revA` data.
The `key_direction_sign` stays `0`. The `key_orientation` stays `"requires a configurable key-direction policy"`.

The [test with standalone Python](../../tests/validate_phase9b_catalogue_p_placement.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_p_placement.py) compares all 308 component results with the source file.
It gives PASS results with the qualified host profile and when a person can see the FreeCAD display.
The tests give PASS results for `Undo`, `Redo`, `transaction_rollback` and the changes to source data and shapes that the software rejects.
The source files and each previous `App.Document` stay the same.
The results stay in `tmp/catalogue-p-placement/`, with `native-04/` and `gui-03/`.

The independent review of the source and tests gives a PASS result.
The reviewer did not write this change.
The result stays in `tmp/catalogue-p-placement/quality-review-04.json`.

The new result contains data for all 168 source positions: 14 have `P` chair components, and 154 do not.
The previous S1/S1J operation keeps its 59 positions and 109 other positions the same.
The previous [S1, S1J and L1 limitations](#s1-and-s1j-chairs-on-a-c10-crossover--2026-10-23) do not change.
All previous FAIL results and review results of BLOCKED stay available.
The output stays in private-development status.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## P chair components on a C10 crossover — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) supplies `preview_private_catalogue_p_crossover_chairs` for B16.
For `XO-001`, it shows 22 chair components at each of 28 `P` positions.
Each of the two turnouts has 14 of these positions.
For the software, `B4` results that agree with the source data are necessary.
The software examines the turnout identity for each position.

The software uses the previous `P` shapes from `basic-04`.
It does not calculate new chair shapes or change their dimensions.
The [C10 input conditions and `key_orientation` limitations](#p-chair-components-at-c10-positions--2026-10-23) stay the same.

The [test with standalone Python](../../tests/validate_phase9b_catalogue_p_crossover.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_p_crossover.py) compares all 616 component results with the source file.
It gives PASS results with the qualified host profile and when a person can see the FreeCAD display.
The tests give PASS results for `Undo`, `Redo`, `transaction_rollback` and the changes to source data and shapes that the software rejects.
The source files and each previous `App.Document` stay the same.
The results stay in `tmp/catalogue-p-crossover/`, with `native-01/` and `gui-repair-01/`.

One `fixture-or-harness-defect` repair changes only the new FreeCAD test.
The independent review of the source and tests gives a PASS result.
The reviewer did not write this change.
The result stays in `tmp/catalogue-p-crossover/quality-review-02.json`.

The new result contains data for all 355 source positions: 28 have `P` chair components, and 327 do not.
The previous S1/S1J crossover operation keeps its 135 positions and 220 other positions the same.
The previous C10 turnout operations keep their 14/154 and 59/109 results the same.
The previous [S1, S1J and L1 limitations](#s1-and-s1j-chairs-on-a-c10-crossover--2026-10-23) do not change.
All previous FAIL results and review results of BLOCKED stay available.
The output stays in `private-development` status.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## S1J chair components at C10 positions — 2026-10-23

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) supplies `preview_private_catalogue_s1j_chairs` for B16.
For `TO-001`, it shows 17 chair components at each of five previous `S1J` positions.
The software uses the previous `S1J` shapes from `basic-04`. It does not calculate new chair shapes or change their dimensions.
It adds no positions and does not show the `display_rail` source component as a chair component.

The [C10 input conditions](#p-chair-components-at-c10-positions--2026-10-23) stay the same.
The `key_direction_sign` stays `0`.
The `key_orientation` stays `"towards the adjacent rail joint; exact direction sign requires stored joint chainage"`.

The [test with standalone Python](../../tests/validate_phase9b_catalogue_s1j_placement.py) gives a PASS result.
The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_s1j_placement.py) compares all 85 component results with the source file.
It gives PASS results with the qualified host profile and when a person can see the FreeCAD display.
The tests give PASS results for `Undo`, `Redo`, `transaction_rollback` and the changes to source data and shapes that the software rejects.
The source files and each previous `App.Document` stay the same.
The results and files that show the FreeCAD display stay in `tmp/catalogue-s1j-placement/`, with `native-repair-01/` and `gui-01/`.

One `test-or-oracle-defect` repair changes only the new FreeCAD test.
The test keeps four previous `S1J` positions. It calculates only the `S1J` position in `plan["analytical_only"]`.
The reviewer examined the source and tests independently and gave a PASS result. The reviewer did not write this change.
The result stays in `tmp/catalogue-s1j-placement/quality-review-01.json`.

The new result contains data for all 168 source positions: five have these `S1J` chair components, and 163 do not.
The previous C10 turnout operations keep their 14/154 and 59/109 results the same.
The previous [S1, S1J and L1 limitations](#s1-and-s1j-chairs-on-a-c10-crossover--2026-10-23) do not change.
All previous FAIL results and review results of BLOCKED stay available.
The output stays in `private-development` status.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## Chair components across the XO-001 crossover — 2026-10-24

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) supplies `preview_private_catalogue_crossover_chairs` for B16.
It shows chair components at 163 positions in one new `App.Document` for `XO-001`.
The software does not write the `App.Document` to a file.

It shows 17 components at each of 123 `S1` positions and each of 12 `S1J` positions.
It shows 22 components at each of 28 `P` positions.
The total is 2911 component results.
The software uses the previous shapes and the previous software to put them at the same positions.

The `source_receipt` contains data for all 355 source positions.
The other 192 positions do not cause the software to add chair components.
The `source_receipt` gives their identities and source causes:

- 124 positions have `special_assignment_deferred` set to `true`.
- At 20 positions, `angle_magnitude_difference_rad` is more than `0`. The software cannot move and turn the previous chair assembly to make the two directions agree with the source directions.
- For 48 positions, the source gives a different position for the chair assembly. The output shows chair components at 28 of these different positions. It does not show chair components at the other 20 different positions.

The `key_direction_sign` stays `0`.
The previous [C10 input conditions and limitations](#p-chair-components-at-c10-positions--2026-10-23) stay the same.

The [standalone Python test](../../tests/validate_phase9b_catalogue_whole_crossover.py) gives a PASS result.
The previous `P`, `S1J` and TrackTemplate Core tests also give PASS results.
The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_whole_crossover.py) gives a PASS result without the FreeCAD display.
It compares all 2911 component results with the previous shapes.

The same test gives a PASS result with the FreeCAD display.
It includes selection, changes to `ViewObject.Visibility`, `Undo/Redo` and checks with invalid states.
The source `App.Document` and the other test `App.Document` stay the same.
Visual inspection includes the full crossover and `S1`, `S1J` and `P` chair components on the two turnouts.
The independent review of the source and tests gives a PASS result.

Local evidence is in `tmp/whole-crossover-preview/`, with `native-01/` and `gui-02/`.

The first test with the FreeCAD display gave a FAIL result after the FreeCAD `Document::Save` operation.
This operation changed `ElementMap` data. It did not change the shape data.
A test with no chair output caused the same changes.
Before FreeCAD starts for the second test, `AutoSaveEnabled` is `false`.
The software and tests stay the same.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
The output stays in `private-development` status. This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## Chair components at S8–S12 — 2026-10-24

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The software adds chair components at 20 positions on `S8`–`S12` for `XO-001` output in `private-development` status.
It uses ten sets of source inputs: `RH-MS-1P` to `RH-MS-5P` and `RH-TS-1P` to `RH-TS-5P`.
The software uses the previous `context_native.py` to prepare these source inputs.
The `preview_private_catalogue_crossover_chairs` operation uses `chair_pair_catalogue.py` to read the chair components.
It applies `source-paired-common-timber-frame.v1` to put them on the crossover.

The earlier [crossover check](#chair-components-across-the-xo-001-crossover--2026-10-24) used `aq_k_rad` and a value calculated from `local_rail_tangent`.
The first value is `retained_uncurved_gauge_face_angle_rad`. The second uses `target_sampled_world_midline_tangents`.
Their difference did not prove that the source chair components were incorrect.

The source check from an independent reviewer includes all 20 positions.
It includes `x_mm`, `y_mm`, `rotation_rad`, `crop_mm` and `shear_rad`.
It includes the `S12` inputs with `aq_branch` set to `closure`.
The [source check](../../tests/paired_switch_source_oracle.py) identifies the source files and their applicable parts.

The output has 183 chair assemblies and 3555 component results.
The previous 163 assemblies and all 355 source position identities stay the same.
The `source_receipt` includes the other 172 positions:

- 124 positions keep `special_assignment_deferred` set to `true`.
- 48 positions use a chair assembly at a different source position. The output now shows all 48 of these assemblies.

`key_direction_sign` stays `0`. The previous C10 limitations stay the same.

The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_paired_crossover.py) gives PASS results with and without the FreeCAD display.
It does a check of all 3555 component results, `Undo/Redo`, `transaction_rollback`, selection and `ViewObject.Visibility`.
The source files and the other test `App.Document` stay the same.
An independent reviewer did a visual inspection of all 20 new positions and six previous groups of chair components.

These full FreeCAD tests gave PASS results before the last source repair.
That repair changes only how `CONTEXT_IDS` supplies its values. The type, values and sequence stay the same.
An independent reviewer found `remaining_ast_identical: true` for the other Python source.
The last FreeCAD check reads all ten sets of source inputs and does a check of all 20 positions.
The Python checks after the repair and the previous `validate_core_export_staging.py` test give PASS results.

The independent reviewer gives `PASS_WITH_FINDINGS` for the source and tests after the repair.
`Q-PAIR-001` is resolved. `Q-PAIR-002` stays `BACKLOG` in `tmp/paired-switch-preview/quality-review-02.json`.
This finding is about different units in `_near`. Different source checks include `rotation_rad`, `aq_k_rad` and `shear_rad`.

An independent reviewer measured distances at 80 source points. The distances from the data samples for each `rail_id` are 0.000127 to 0.006716 mm.
These results give no acceptance for physical fit. No numerical tolerance for physical fit is set.
Local evidence is in `tmp/paired-switch-preview/` and `tmp/paired-switch-context/`.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
The output stays in `private-development` status. This result gives no positive rights claim.
Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## CC chair components on XO-001 — 2026-10-24

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) adds `include_central_cc=True` to `preview_private_catalogue_crossover_chairs`.
It shows 12 `CC` chair assemblies at `X2-Y`, `X3-X` and `X4-A` on the two turnouts of `XO-001`.
Each new assembly supplies chair components for one `stock-rail` position and one `check-rail` position.
The software uses all 33 previous components from `CC/context-native-02`. It does not calculate new chair shapes.

The output has 195 assemblies and 3951 component results.
The previous 183 assemblies stay the same.
The 48 positions with `exclusion_kind` of `confirmed-no-separate-chair` stay the same.
The new assemblies supply chair components for 24 positions that have `special_assignment_deferred` set to `true`.
The other 100 positions have no chair components in this output.

All 355 source position identities and `original_analytical_exclusions` stay the same.
All 124 values of `special_assignment_deferred` stay `true`.

The [independent source check](../../tests/central_check_source_oracle.py) includes all 12 new assemblies.
The Templot 556b source supplies data for these positions.
The check compares each of the 396 new component positions with the previous source shapes.

In each assembly, 17 chair components use one set of `x_axis` and `y_axis` values.
The 16 `SourceFixing` components use different values.
The software uses `source-central-check-component-frames.v1`. It calculates `host_station_mm` and `travel_heading_rad` as before.

`fixing_angle_frame` is `uncurved-RH-source-before-common-host-rotation`.
The software turns the `SourceFixing` components by `travel_heading_rad`. Templot keeps `BOLTBOSS` at `0` after it turns the other components.
`templot_global_fixing_angle_parity` and `random_export_parity` stay `false`.
These checks give no acceptance for physical fit. No numerical tolerance for physical fit is set.

The [standalone Python test](../../tests/validate_phase9b_catalogue_central_check.py) gives a PASS result.
The previous crossover and TrackTemplate Core tests also give PASS results.

The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_central_check.py) gives a PASS result without the FreeCAD display.
It compares all 3555 previous component results and all 396 new component results.
It does a check of the new components again after `Undo/Redo`.
The source `App.Document`, the other test `App.Document` and the source files stay the same.

The same test gives a PASS result with the FreeCAD display.
It includes `Undo/Redo`, selection, changes to `ViewObject.Visibility` and `transaction_rollback` checks for `CC`.
An independent reviewer did an inspection of all 12 new positions, the full crossover and the previous chair groups.

The independent review of the source and tests gives a PASS result.

Local evidence is in `tmp/central-check-preview/`, with `native-02/` and `gui-01/`.
The previous C10 limitations and `key_direction_sign` of `0` stay the same. `Q-PAIR-002` stays `BACKLOG`.

`project_status` stays `reference-only`. `intended_uses` stays `["private-development"]`.
This result gives no acceptance for persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## CCL and CCR chair components on XO-001 — 2026-10-25

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/compatibility/chair_catalogue_placement.py) adds `include_check_ends=True` to `preview_private_catalogue_crossover_chairs`.
It shows eight `CCL` and `CCR` chair assemblies at `X1-Z` and `X5-B` on the two turnouts of `XO-001`.
Each new assembly supplies chair components for one `stock-rail` position and one `check-rail` position.
The software uses the previous 33 components for each of `CCL` and `CCR` from `context-native-02`. It does not calculate new chair shapes.

The output has 203 assemblies and 4215 component results.
The previous 195 assemblies and their 3951 component results stay the same.
The 48 positions with `exclusion_kind` of `confirmed-no-separate-chair` stay the same.
The new assemblies supply chair components for 16 more positions. The other 84 positions have no chair components in this output.

All 355 identities for source positions and `original_analytical_exclusions` stay the same.
All 124 values of `special_assignment_deferred` stay `true`.

The [source check](../../tests/check_end_source_oracle.py) calculates component positions and the `source_rail_code`, `source_branch`, `family`, `source_angle_rad`, `source_crop_mm`, `source_inner_shear_rad` and `source_outer_shear_rad` values for all 16 identities.
For `side="MS"`, `source_rail_code` is `1` and `source_branch` is `main_straight`.
For `side="TS"`, `source_rail_code` is `4`. Templot uses `aq3offset` with `radcurve` at `X1-Z` and `turnoutst_main` at `X5-B`.
The previous stopped exact candidate used the angle from `turnoutst_main` for the two positions with `side="TS"`. This was incorrect at `X1-Z`.

The RED tests compare values independently and gave FAIL results before the software changed.
The same tests give PASS results after the change.

The source check calculates its `stock_radius_mm`, `centre_x_mm`, `centre_y_mm`, `y_mm` and `k_rad` values directly. It does not use the product function `_rea_c10_turnout_outer_gauge_point_at_x`.
It uses the accepted `source_parameters` function and functions from `central_check_source_oracle.py` again.
These functions are the same for this source check and previous source checks. This is a limitation of its evidence.

The [software](../../tracktemplate/domain/check_end_placement.py) has `origin_mm`, `x_axis` and `y_axis` values for the assembly. Its `check_frame` values apply to the seat and key. Four `fixing_frames` give the values for the fastenings.
The [source check in the software](../../tracktemplate/compatibility/chair_check_end_placement.py) rejects hashes that are different from the previous full hashes for source files and alignment inputs.
The full output rejects other alignment inputs.

The [standalone Python test](../../tests/validate_phase9b_catalogue_check_ends.py) gives a PASS result.
The test compares the two travel directions and straight alignments. It also compares curves with `curvature` above and below 0 at radii of 600, 1200 and 2400 mm.
Other checks include curves where `curvature` changes, the ends of alignments, and `interpolate_alignment_station`.
The tests also examine source positions where `source_branch` changes, inputs with an invalid state, and changes that must give a FAIL result.

The `complete_radius_decision` tests include each of its three radius inputs as the smallest input.
They include the specified limit and `math.nextafter` values immediately below and above it.
The tests use the previous comparison rules for the values. They do not set a numerical tolerance for physical fit.
The previous crossover and TrackTemplate Core tests also give PASS results.

The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_check_ends.py) gives a PASS result without the FreeCAD display in `native-02`.
It compares all 3951 previous component results and all 264 new component results.
It compares the 264 new component results again after `Undo/Redo`.
The test also compares 792 components in 24 more assemblies.

These tests use the two travel directions and straight alignments. They also use curves with `curvature` above and below 0 and a radius of 1200 mm.
All 32 items in `boss_cap_containment` have `complete_source_facet_bijection` of `true` and give PASS results in the previous checks.

The third test repair changes only the software that uses the FreeCAD display.
An independent reviewer compared the software that operates without the display and the other files that it uses. They stay the same.
Thus, `native-02` stays applicable to that software. It is not a new test against the file bytes after the third repair.

The full test gives a PASS result with the FreeCAD display in `gui-02`.
It includes selection, changes to `ViewObject.Visibility`, `Undo/Redo`, source checks and `transaction_rollback` checks for `CCL` and `CCR`.
The source `App.Document`, the other test `App.Document`, source files and identities of the `App.Document` items stay the same.
The test closes all `App.Document` items that it makes.

The tests repeat the checks for rejected `CCL` and `CCR` inputs and `transaction_rollback`. The test uses the previous results for rejected inputs from `freecad_validate_phase9b_catalogue_central_check.py` and `freecad_validate_phase9b_catalogue_paired_crossover.py` again.
An independent reviewer examined all 36 pairs of `.png` files. These files show all eight new assemblies and the full crossover.
Independent review gives PASS results for the source, tests, FreeCAD operation and `.png` files in this bounded scope.

The initial stopped exact candidate and its evidence for FAIL results stay the same. Its repair history stays at the `2/2` limit.
This change keeps its RED results, the `native-01` and `gui-01` FAIL results, and the diagnostic results after them.
Three repairs correct the checks where `source_branch` changes, the check for multiple `Faces` in a `boss_cap_containment` item, and test cleanup.
The project owner removed the repair limit for this change before the third repair. This decision does not reopen the initial stopped exact candidate.

`CCLCCR-SUCCESSOR-Q04` stays `BACKLOG` for the canonical owner of `tracktemplate/adapters/freecad/chair_reference_preview.py`.
In the `Part.makeBox` test, `view.fitAll()` can make the other `App.Document` active.
That change does not occur in the test with a copy of `XO-001` and items in `selection` and `preselection`.
The shared product software stays the same. The actual `XO-001` tests change `selection` and `preselection`. Those changes give the necessary FAIL results.

The `XO-001` input stays the same and stays a permanent regression test.
These results show how the software calculates component positions for work with curves that a person supplies after this change.
Different alignment inputs and output changes during edits must have a new project owner decision and tests before the software changes.

`physical_fit` stays `NOT_PROVED`. This change sets no numerical tolerance for physical fit.
The previous C10 limitations, `key_direction_sign` of `0` and limitations recorded with `fixing_angle_frame` stay the same. `Q-PAIR-002` stays `BACKLOG`.

Local evidence is in `tmp/check-end-successor/`, with `native-02/`, `gui-02/`, `source-freeze-03.json` and the `quality-review-04` records.
The source references include Templot 556b `math_unit.pas:17766–17790,26696–26820,30140–30369,31602–31824` and `heave_chairs.pas:1363–1400`.
The source check records the remaining source references and hashes. The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

`project_status` stays `reference-only`. `intended_uses` stays `["private-development"]`.
This result gives no acceptance for persistence, production, export behaviour, product performance or phase exits.
This result gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## P chair positions after a radius change — 2026-10-25

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).
It also supplies evidence for the PR-16 checks after input changes.

The new [FreeCAD test](../../tests/freecad_validate_phase9b_p_curvature_recalculation.py) changes `CurveRadius` from 600 to 900 mm and back through the FreeCAD display.
It uses `Generate` with `Replace`, makes `XO-001` again, applies B4 and uses `analyse_entity_chair_positions`.
The 14 inputs in `SOURCE_OPTIONS` stay the same. These inputs include `toe_chainage_a` and `minimum_requested_radius` of 600 mm.

The accepted software calculates `toe_chainage_b` and examines `minimum_resulting_radius`.
This sequence uses the specified operations. It gives no acceptance for automatic changes to related objects after input changes.

The [source check](../../tests/p_curvature_source_oracle.py) independently calculates chair positions from `points` in `rail_records` and `centre` in `timber_records`.
It gets only source identities from the results of `analyse_entity_chair_positions`. It does not get positions or directions from those results.

The check examines each pair of adjacent points in `rail_records`. It uses `gauge_face_points` and `outer_face_points` to calculate the directions.
This check examines the accepted `rail_records` data. It does not examine the software that calculates those data or show physical fit.
The [test in standalone Python](../../tests/validate_phase9b_p_curvature_recalculation.py) examines calculated data with known results and inputs with an invalid state. It rejects incorrect results that keep previous positions or directions.

The test in standalone Python gives PASS results for nine tests. Three checks correctly reject results that stay the same, previous positions and previous directions.
The previous tests for P chair positions and crossovers in standalone Python also give PASS results.

The FreeCAD test gives PASS results without the display in `native-02` and with the display in `gui-02`.
The two tests use the qualified host profile `linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`. Each test gives the specified sentinel and process exit status 0.

For each input, the test makes 28 P assemblies with 22 components for each assembly. The tests compare all 616 component results for each input.
The two inputs with `CurveRadius` of 600 mm have 355 source positions. The input with `CurveRadius` of 900 mm has 354.

All 28 P identities stay the same. All 28 positions and directions change at 900 mm.
The test compares each result with its current source data. It also compares the `returned-600` component results with the permanent `reference-600` input.

The previous numerical tolerances stay the same. This change adds no numerical tolerance for physical fit.
The largest difference between `returned-600` and `reference-600` component positions is less than 1.84e-12 mm. The previous limit for dimensions is 1e-7 mm.

The `32 * sys.float_info.epsilon` limit applies only to directions calculated from the same source data.
The test independently records the difference between `returned-600` and `reference-600` source directions. It does not apply that limit across different source data.

The tests examine `Undo/Redo`, source data, other documents, object identities, selection and all 24 objects that `LAYER_NAMES` identifies.
The changed input also gives a PASS result for the test that changes the source during `create_private_catalogue_p_preview` and makes `transaction_rollback` necessary.
The previous objects from `preview_private_catalogue_p_crossover_chairs` stay the same after `Generate`. The source check rejects their removed `XO-001` source.

The tests use `App.closeDocument` for all documents that they make. The test with the display removes its temporary `user.cfg` file and puts the display back to its previous condition.
An independent reviewer examined the source, tests, complete `native-02` and `gui-02` results, and all 408 source hashes with their input data.
The reviewer also examined the `reference-600` and `returned-600` displays, all eight changed `chair-closeup.png` files, and the radius input display. The independent review gives a PASS result.

The test without the display uses copies of files from the display sequence. SHA-256 values identify those files.
The test uses `analyse_entity_chair_positions` again after `App.openDocument` opens each changed copy. It makes sure that `rail_records`, `timber_records`, inputs and B4 results stay the same.

The `native-01` FAIL result shows small changes in positions after `App.openDocument`. Those changes cause the accepted source check to reject previous results from `analyse_entity_chair_positions`.
The `gui-01` FAIL result shows that the previous validator makes 355 positions necessary.
One repair changes only the new test. It uses `analyse_entity_chair_positions` again after `shutil.copy2` and `App.openDocument`, and supplies 355 or 354 to the previous validator.
The test does all nine previous checks with an invalid state.

The initial tests, FAIL results and diagnostics stay the same. The test repair changes no product source or source check.

The initial `XO-001` file stays the same and stays a permanent regression test.
The software for the previous 203 assemblies and source identities stays the same. The 48 `confirmed-no-separate-chair` items and other `excluded_positions` stay the same.
The full `preview_private_catalogue_crossover_chairs` command continues to make its previous source necessary. These results do not admit other inputs to that command.

Local evidence is in `tmp/p-curvature-recalculation/`. It includes `source-freeze-03.json`, `native-02/`, `gui-02/`, `runtime-summary-01.json` and `independent-staff-review-final-02.json`.
The initial FAIL results, diagnostic FAIL results and their failure classifications from independent review stay in that directory.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

`physical_fit` stays `NOT_PROVED`. `project_status` stays `reference-only`. `intended_uses` stays `["private-development"]`.
This result gives no acceptance for persistence, production, export behaviour, product performance or phase exits. It gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## Automatic changes to P chair positions after a radius change — 2026-10-26

This Level 2 change supplies evidence for part of Exit 9B-3 with the authority in [D-P9-018](#lms-chair-record-and-templot-development-panel).
It also supplies evidence for the PR-16 checks after input changes.

The [new adapter](../../tracktemplate/compatibility/crossover_dependent_recalculation.py) keeps the input values and identifiers for `XO-001` when `Generate` with `Replace` changes `CurveRadius` in the canonical state.
The operator does not have to make the crossover again or manually apply B4, `create_crossover_host_integration` and `analyse_entity_chair_positions`.
The adapter uses the same functions. It keeps the initial `run_macro` function.

This change is permitted only for the radius of one `XO-001` in `SET-001` that meets the specified conditions.
The adapter examines the source before replacement. It rejects source data that do not meet its conditions before removal.
It keeps the same optional route properties and crossover edit metadata, with the same values.

For `MODE_MATCH_SPACINGS`, the input values stay the same. The calculated `entry_transition_length` and `exit_transition_length` values can change.
The `track_configs` values read from the document must be equal to the values that `_store` keeps.

The adapter calculates B4 and chair positions during the same `Generate` operation.
It also uses `create_crossover_host_integration` again when the integration is active.
It makes `ProductionSchedule` and `MaterialLengthReport` from the source data after integration, before `commitTransaction` completes that operation.
One full `Undo` gives the previous exact state. `Redo` gives the new exact state.
The private preview command is still necessary to make catalogue chairs with FreeCAD `Part` geometry.

The [standalone test](../../tests/validate_phase9b_p_dependent_recalculation.py) and eleven related regression tests give PASS results.
The new tests first show removal of `XO-001` and subsequent defects. The failure classes for these defects are in the local evidence.
The same commands and test checks then give PASS results with the repaired source.

The [FreeCAD test](../../tests/freecad_validate_phase9b_p_dependent_recalculation.py) operates the same `Generate` command at 600, 900 and 600 mm.
The test uses the qualified host profile `linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.

The full test gives PASS results without the display in `native-06` and with the display in `gui-05`.
The two processes complete execution with exit status 0 and give the specified success sentinel. All 412 source paths and SHA-256 values stay the same.
The test closes all documents that it makes. The test with the display removes its temporary `user.cfg` file and sets the display power to its previous condition.

The `native-05` test completes its checks and gives its success sentinel. Its outer process stops with exit status 143.
The FreeCAD process exit status is unknown. This process evidence does not give a full PASS result.
The validator does the full test again without source changes to get the necessary process evidence.

Each input has 28 P assemblies with 22 components for each assembly.
The two tests compare all 616 components for each input with the same source check and the frozen manual results from PR #211.
All 28 identities stay the same. All 28 positions and directions change at 900 mm.
The counts of source positions stay 355, 354 and 355.

The largest component difference between the second 600 mm result and the initial result is less than 1.74e-12 mm.
The previous dimension limit stays 1e-7 mm. The test records differences between directions from different source data independently.
The source check and its numerical tolerances stay the same.

The two tests give PASS results for full `Undo/Redo`, cancellation and regeneration with the same inputs. The nine checks with invalid source data also give PASS results.

The two tests also give PASS results for full recovery after errors from B4, `create_crossover_host_integration`, `analyse_entity_chair_positions` and the table functions. These functions write data before the errors.

The tables use the source data after integration. The previous private previews stay the same. The preview command rejects their changed source.

An independent reviewer examined all changed source and tests, the complete results and their source hashes.
The reviewer also examined the initial and second 600 mm displays, all eight views at 900 mm and the two radius input displays.
The independent review gives a PASS result. It has no open findings for the source or tests in this bounded scope.

The initial tests with FAIL results and their failure classes stay in `tmp/p-dependent-recalculation/`.
The `native-03` and `gui-03` checks give FAIL results because the `Free` flag changes when the test reads the calculated group shapes in a different sequence.
The source inspection by the independent reviewer identifies this flag as a calculated software condition, not geometry.
All other bytes from `exportBrepToString` stay the same for each of these groups.

The repaired test reads each calculated group shape in a specified sequence. Then it compares full document snapshots with the same checks.
It does not remove fields or add numerical tolerances. Other checks must reject changed marker geometry and group membership.

The `native-04` and `gui-04` checks give FAIL results at the test of the minimum radius.
The minimum input changes the selected connector. The sum of two previous results, divided by two, does not prove that an input is invalid.
The repair uses `lower-preview-pass-complete-fail` from the [accepted source contract](../contracts/phase1-crossover-feasibility.json).

That input has a toe position of 500 mm and a minimum radius of 600 mm.
The other test input gives PASS results for B4, integration and the source check for all 28 P positions at 900 mm.
The `Generate` operation at 600 mm rejects that input. It gives the previous exact state for the full document.

For each of the four rejected radius results, the difference from the accepted contract is less than its previous limit of 1e-6 mm.
That limit does not prove physical fit. The test also rejects replacement when `UndoMode` is `0`.

The same `XO-001` input stays a permanent regression test.
The software for the accepted 203 assemblies, 48 shared supports and source identities stays the same.
The full `preview_private_catalogue_crossover_chairs` command keeps its previous source conditions.
The previous CCL/CCR candidate stays stopped, with no repairs available from its previous limit of two repairs. Its evidence with FAIL results and frozen history stay the same.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

Local evidence is in `tmp/p-dependent-recalculation/`.
It includes `source-freeze-05.json`, `native-06/`, `gui-05/`, their process records and `independent-staff-review-05-final.json`.

`physical_fit` stays `NOT_PROVED`. `project_status` stays `reference-only`. `intended_uses` stays `["private-development"]`.
This result gives no acceptance for other inputs, persistence, production, export behaviour, product performance or phase exits.
It gives no positive rights claim.

Phase 9B stays Open at 3/6. Exits 9B-1, 9B-3 and 9B-6 stay Pending.
More work on LMS chairs is not permitted until after Phase 11.

## More S1, S1J and L1 chairs for XO-001 — 2026-10-26

This Level 2 result supplies evidence for part of Exit 9B-3 with authority from [D-P9-018](#lms-chair-record-and-templot-development-panel).

The optional `include_single_rail=True` argument adds 34 assemblies to the private `XO-001` crossover view.
These assemblies are 16 L1 chairs, 14 S1 chairs and four S1J chairs.
The full view has 237 assemblies and 4,889 components. It shows 305 of the 355 source positions.
The [source adapter](../../tracktemplate/compatibility/chair_single_rail_placement.py) uses the previous catalogue geometry and preview lifecycle.

The default command behaviour stays the same. The command makes exact geometry only when the caller starts the preview.

The source adapter calculates the new component positions from the frozen Templot 556b source conditions and nominal timber stations.
The four outer stock-rail positions at X9-F use the source joint override for S1J.
The [component module](../../tracktemplate/domain/single_rail_placement.py) calculates the position and direction of each fixing that the source identifies.
The module does not make new catalogue geometry or change its dimensions or shape.
The tests do not compare the global angles of Templot fixings or Templot's random export behaviour.

The previous 203 assemblies, 48 shared supports and all canonical identities stay the same.
The canonical analytical exclusions and 124 deferred assignment flags also stay the same.
The view does not show 50 positions: 40 crossing-rail positions and ten exit or envelope positions.
More evidence is necessary for their source contexts or segment mappings. Catalogue family labels do not supply sufficient evidence.

At the switch heel, the source conditions select L1 for ten previous S1 assignments at S13, T1 and T2.
This result preserves those ten assignments in the previous 203 assemblies. The owner's decision makes this preservation necessary.
The ten differences stay necessary work for Exit 9B-3. These differences are not sufficient evidence of a physical-fit failure or a geometry defect.
This result is not sufficient evidence of full agreement with Templot family assignments.

The [standalone tests](../../tests/validate_phase9b_catalogue_single_rail.py) first give RED evidence for the missing behaviour.
The 12 tests and the related regression tests then give PASS results.
The tests compare components for the two travel directions, signed host curvature, source boundaries and invalid inputs.
The independent source check reads the frozen Pascal code and the native components that the catalogue keeps. It does not use product placement functions.

The [FreeCAD test](../../tests/freecad_validate_phase9b_catalogue_single_rail.py) uses the qualified host profile `linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
The full test gives PASS results without the display in `native-01` and with the display in `gui-02`.
Each process completes execution with exit status 0 and gives the specified success sentinel.
All 416 source paths and 94 input bindings stay the same. Each test removes all documents that it makes from the FreeCAD session.
The GUI test also removes its temporary profile and sets the display power to its previous condition.

The two tests compare all 4,215 previous components and all 674 new components.
The largest new component difference is less than 5.09e-13 mm.
The previous numerical limits stay the same. These limits are not sufficient evidence of physical fit.
The two tests give PASS results for full `Undo/Redo`. They also validate recovery after errors that the tests cause for each of the three added families.

The GUI test also gives PASS results for selection and visibility checks on all 536 layers.
An independent reviewer examines all 34 closeups and the full overview from the GUI test. The visual inspection gives a PASS result.
The hashes of the 68 images from the GUI test agree with `gui-02/image-manifest.json`.
The images are not sufficient evidence of physical fit.

The independent review of source, tests and evidence gives `PASS_WITH_FINDING`, with no open blocker for this bounded change.
The ten previous family differences stay necessary work before Exit 9B-3.

Local evidence is in `tmp/single-rail-coverage/`.
It includes `source-freeze-01.json`, `remaining-50-01.json`, `accepted-heel-family-limitation-01.json` and `independent-staff-review-01-final.json`.
The initial RED results, classified test-fixture correction and interruption of the first GUI run stay in that directory.

`physical_fit` stays `NOT_PROVED`. `project_status` stays `reference-only`. `intended_uses` stays `["private-development"]`.
The [provenance](../PROVENANCE.md) and [licensing boundaries](../LICENSING_BOUNDARIES.md) stay the same.

This result gives no acceptance for other host inputs, physical fit, persistence, production, export behaviour, performance or phase exits.
The frozen `XO-001` regression stays the same. The stopped CCL/CCR candidate and its repair history stay the same at the `2/2` limit.
Phase 9B stays Open at 3/6. More work on LMS chairs is not permitted until after Phase 11.

## Validation before large FreeCAD tests — 2026-10-27

This Level 2 workflow change supplies the procedure for [Issue #218](https://github.com/Richard-Gnitnub/tracktemplate/issues/218).
It is part of the work for Issue #213 and Exit 9B-3.
The [validation instructions](../VALIDATION.md#validation-harness-readiness) contain the necessary checks.
The change-validation skill supplies the procedure. This change adds no policy owner or skill.

The [standalone tests](../../tests/validate_harness_readiness.py) give PASS results for 12 checks.
The checks include `__main__`, the filename without `.py`, missing input names and incorrect input values for `_near_frame`.
They also include files not in the permitted directory.
The test sequence rejects inputs with an invalid state before its subsequent test starts.
The 39 launcher tests and the tests of the test sequence also give PASS results.

The [small FreeCAD fixture](../../tests/freecad_validate_harness_readiness.py) gives a PASS result through the launcher.
The fixture uses small test inputs and does not read the Templot source archive.
It uses the qualified host profile `linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
FreeCAD supplies the filename without `.py` as `__name__`.

The fixture uses the previous `_near_frame` function for one correct input and seven inputs with an invalid state.
It rejects all seven incorrect inputs.
The fixture also does checks of one correct file and three incorrect file conditions.
The process returns exit status 0 and the necessary success sentinel.
No process that the test started is active.

Local evidence is in `tmp/issue218/`. It includes `native-qualification-01/`, `source-independent-review-01.json` and `result-independent-review-01.json`.
Independent reviews of the source and the bounded FreeCAD result give PASS results.
The evidence for previous FAIL results and the recovery material stay preserved.

This result does not validate the 702 new XO-001 checks that use `_near_frame` or the complete 261-assembly candidate.
This work does not continue any XO-001 native test or GUI test.
The `2/2` repair limit stays the same. No more repair is permitted.

This result gives no acceptance for physical fit, production, product performance or phase exits.
It changes no rights state.
Phase 9B stays Open at 3/6. More work on LMS chairs is not permitted until after Phase 11.

## P chair component `PJAW` — 2026-10-28

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/application/chair_research.py) uses 13 lengths and `rail_fish_ratio` from a `ChairDefinition` to make the `PJAW` component for the source condition `loose_pin=False`.
The result contains two separate `Solid` shapes with `part_id` values of `spacer` and `body`.
The result has `face_count = 23` and `length_basis = "full-size"`.
The inputs have `reference-only` status. The output stays in private-development status.

The [geometry test](../../tests/validate_phase9b_chair_p_outer_jaw_geometry.py) and the [package test](../../tests/validate_phase9b_chair_p_outer_jaw.py) give PASS results.
The tests compare all 21 records in `faces` from the previous Templot 556b source data.
The [FreeCAD test](../../tests/freecad_validate_phase9b_chair_p_outer_jaw.py) gives a PASS result with the qualified host profile.
The result contains `"native_tests": 1`, `"skips": 0` and `"negative_controls": 11`.
All tests and controls give PASS results.

The previous controls for the FreeCAD process stay active. Cleanup gives a PASS result.
The test creates no `App.Document`. This change has no GUI test result.
Independent reviews of the source, tests and FreeCAD results give PASS results.
The evidence stays in `tmp/p-chair-outer-jaw/`.

The result does not include the complete P chair or chair positions.
PR #221, the preserved XO-001 candidate and previous evidence with a FAIL result stay unchanged.
The previous `2/2` repair limit permits no more repairs.

This result gives no acceptance for physical fit, persistence, production, export behaviour, product performance or phase exits.
It changes no rights state.
Phase 9B stays Open at 3/6. D-P9-018 does not permit more work on LMS chairs until after Phase 11.

## Assembly of P chair components — 2026-10-29

This Level 2 change supplies evidence for part of Exit 9B-3 with the conditions in [D-P9-018](#lms-chair-record-and-templot-development-panel).

The [software](../../tracktemplate/application/chair_research.py) makes one assembly from three components in one `ChairDefinition`.
The software that constructs each component stays the same.
The result contains four `Solid` shapes: `base-plinth`, `rail-seat`, `outer-jaw:spacer` and `outer-jaw:body`.

Each dimension that two components use must have the same value in the two components.
The source condition is `base.chair_inner_length_mm == seat.table_centre_from_gauge_face_mm + table_centre_from_inner_end_mm`.
The inputs have `reference-only` status. The output stays in private-development status.

The [test for standalone Python](../../tests/validate_phase9b_chair_p_assembly.py) gives a PASS result for all seven tests. It ignores no test.
The previous `S1`, `S1J`, `L1`, `PSEAT` and `PJAW` tests also give PASS results.

The [FreeCAD test](../../tests/freecad_validate_phase9b_chair_p_assembly.py) gives a PASS result for its one test. It ignores no test.
It does checks of all four shapes and 14 interfaces from the source.
It also gives PASS results for 11 checks of invalid states.
The maximum difference from the source values is `5.7e-14 mm`.
Independent reviews of the source, tests and FreeCAD results give PASS results.

The test makes no `App.Document`. This change has no GUI test result.
The previous controls for the FreeCAD process stay active. Cleanup gives a PASS result.
The evidence stays in `tmp/p-chair-structural-assembly/`. It includes the previous results with FAIL and their failure classifications.

The result includes no other chair components or chair positions. This assembly is not a complete P chair.
PR #221, the preserved XO-001 candidate and the previous `2/2` repair limit stay the same.

This result gives no acceptance for physical fit, production, product performance or phase exits.
It changes no rights state.
Phase 9B stays `Open` at 3/6. More work on LMS chairs is not permitted until after Phase 11.

## L1 selection at S13, T1 and T2 — 2026-10-28

This Level 2 result supplies evidence for chair selection and part of Exit 9B-3.
The owner authorises a change to ten previous S1 selections: four at S13, four at T1 and two at T2.
This instruction supersedes the [previous instruction](#more-s1-s1j-and-l1-chairs-for-xo-001--2026-10-26) for these ten selections only.

The optional `correct_heel_l1=True` input selects L1 through `preview_private_catalogue_crossover_chairs` for `XO-001` in private research use.
The [source adapter](../../tracktemplate/compatibility/chair_single_rail_placement.py) uses the previous L1 shapes and software that calculates component positions.
With `correct_heel_l1=False`, the command operation and canonical records from the source stay the same.
Each changed chair selection keeps its stable identity and records S1 in `original_family`.

The selection keeps 237 assemblies. The other 227 assemblies stay the same.
The `existing_shared_support_count` value stays 48.
These numbers are software results, not new FreeCAD test results.

The [Python tests](../../tests/validate_phase9b_catalogue_heel_l1.py) first give RED results for the missing behaviour.
They then give PASS results without FreeCAD.
The tests do a check of the Templot 556b source identity and its selection conditions for all ten selections.
They compare 350 sets of component position and direction data for the ten positions on seven alignment inputs, with the two travel directions.
The inputs use a straight alignment and left and right curves with radii of 600 mm, 900 mm and 1,800 mm.
The tests use independently calculated component positions.

Previous regression tests for component positions and four adapter tests also give PASS results without FreeCAD.
The adapter tests do a check of assembly identities and `model_sha256`. They also make sure that the adapter rejects invalid input values.
The independent review gives `PASS_WITH_FINDING` for the source, tests and preservation evidence.
FreeCAD checks of shapes and document operations, and `real-GUI` evidence, stay necessary before exit acceptance.

Local evidence is in `tmp/heel-l1-successor/`.
The initial RED results, correction to the new fixture and its failure classification stay preserved there.
No accepted test changes. The software that supplies values to accepted tests and all numerical tolerances stay the same.

No FreeCAD or `real-GUI` test ran for this result.
These tests do not validate shapes in FreeCAD, physical fit or the complete result from `preview_private_catalogue_crossover_chairs`.
The frozen 261-assembly candidate `bf41a7dd` and previous regression test evidence stay the same.

The [technical provenance](../PROVENANCE.md) and [licensing conditions](../LICENSING_BOUNDARIES.md) stay the same.
This result gives no production or phase exit acceptance. It gives no positive rights claim.

No repair is available from the previous `2/2` limit. Phase 9B stays Open at 3/6. More work on LMS chairs stays stopped.

## R2 exit chairs for XO-001 — 2026-10-29

This Level 2 change supplies more construction and placement evidence for Exit 9B-3.
The optional `include_r2_exit=True` argument adds four S1 assemblies to the private `XO-001` preview.
The positions are the `vee point rail` and `vee splice rail` at R2 on each turnout.
The optional operation needs the previous single-rail supplement. The initial value of `include_r2_exit` is `False`.
The operation accepts `correct_heel_l1=True` and `correct_heel_l1=False`.

The [source adapter](../../tracktemplate/compatibility/chair_single_rail_placement.py) uses the current S1 geometry and component placements.
Frozen Templot 556b source identifies R2 as a continued crossing position, not the source's named `R` return-track context.
The source station is between the rail ends. Its clearance selects S1. The station is not in the interval that selects a joint chair.
The four canonical identities, initial source records and deferred assignment flags stay the same.

The [standalone tests](../../tests/validate_phase9b_catalogue_r2_exit.py) give RED results before the product change and PASS results after the product change.
They compare the new body and fixing positions for the two travel directions and seven straight or signed-curvature conditions.
They also check source limits, invalid inputs, checks after source changes, the optional argument and previous behaviour.

The standalone tests count 241 assemblies, with 68 more components. The 48 shared supports stay the same.
This count is not a complete native preview result. It does not admit more host geometry.

Previous native and GUI evidence applies to the same S1 geometry, component transformations and preview recovery.
It does not supply four new R2 native executions. No FreeCAD, GUI or full-XO test ran for this change.
Local source, RED, regression and review evidence is in `tmp/r2-exit-coverage/`.

This exit group does not include four R1 positions and two E001 positions. This change does not include the 40 crossing positions.
The frozen 261-assembly candidate and all previous evidence with FAIL results stay the same.

The current validation tools, geometry builders, numerical tolerances and accepted tests stay the same.
This result gives no acceptance for physical fit, rights, production, performance or phase exit.
The [provenance](../PROVENANCE.md) and [licensing conditions](../LICENSING_BOUNDARIES.md) stay the same.

Phase 9B stays Open at 3/6. The previous `2/2` allowance stays consumed. LMS development stays stopped.

## R1 chairs on XO-001 — 2026-10-29

This Level 2 result supplies evidence for four more chairs and part of Exit 9B-3.
The owner authorises these four R1 positions for output in `private-development` status.
The optional `include_r1_exit=True` input adds two L1 chairs on the splice rails and two S1J chairs on the point rails.
The operation is possible only with `include_single_rail=True`. The initial value of `include_r1_exit` is `False`.
The `include_r2_exit` and `correct_heel_l1` inputs keep their previous behaviour.

The [source adapter](../../tracktemplate/compatibility/chair_single_rail_placement.py) uses the current chair shapes and calculates component positions.
Frozen Templot 556b source identifies R1 as a continued crossing position.
The joint rule first selects S1J. The subsequent clearance rule changes only the splice rail to L1.
All four positions are between the rail ends. The four canonical identities and their source records stay the same.

The [standalone tests](../../tests/validate_phase9b_catalogue_r1_exit.py) give RED results before the product change and PASS results after the product change.
The 12 tests check source identity, family selection, source limits, invalid inputs and previous behaviour.
They compare the `origin_mm`, `x_axis` and `y_axis` data for each body and every `fixing_frames` entry.
The tests use the two travel directions and seven conditions: a straight alignment and curves with radii of `±600 mm`, `±900 mm` and `±1800 mm`.
With `include_r2_exit=True`, the standalone tests count 245 assemblies. The 48 shared supports stay the same.

Previous FreeCAD and GUI evidence applies to the same chair shapes and component positions and directions.
It also gives evidence for the same `Undo`, `Redo` and `rollback` operations.
It supplies no new FreeCAD test result for the four R1 positions.
No person or tool did a FreeCAD, GUI or full-XO test for this change.
Local source evidence, RED results, regression test results and review evidence are in `tmp/r1-exit-coverage/`.
The evidence keeps the initial test error, its failure classification and the fixture correction.

This change does not include two E001 positions and 40 crossing positions.
The frozen 261-assembly candidate and all previous evidence with FAIL results stay the same.
This result gives no acceptance for physical fit, rights, production, performance or phase exit.
The [provenance](../PROVENANCE.md) and [licensing conditions](../LICENSING_BOUNDARIES.md) stay the same.

Phase 9B stays Open at 3/6. No repair is available from the previous `2/2` allowance. LMS development stays stopped.

## E001 rail ends outside the timber on XO-001 — 2026-10-29

This Level 2 result supplies source evidence for two more positions for Exit 9B-3.
The optional `classify_e001_exclusions=True` input identifies two rail ends outside the E001 timber in a preview with `private-development` status.
The initial value is `False`. Previous operations and their results stay the same with `classify_e001_exclusions=False`.

E001 is a timber for several tracks. It is not the `E` exit timber in Templot 556b.
Independent source checks show that the point and splice rails stop before the timber outline.
The existing `0.2 mm` distance limit in the chair analysis includes these rail ends as possible chair positions.
This limit stays the same.

The [source adapter](../../tracktemplate/compatibility/chair_catalogue_placement.py) examines every rail segment against the timber outline before it reports why these positions have no assembly.
The operation stops if a rail touches or goes across the outline, source records are incorrect, or the evidence changes.
The adapter does not extend a rail or select a chair family for these positions.

The [standalone tests](../../tests/validate_phase9b_catalogue_e001_exclusions.py) give RED results before implementation and PASS results after implementation.
All 11 tests and the relevant placement regression tests give PASS results.
The checks of the preserved source data also give PASS results for both E001 positions.

With all existing chair placement inputs set to `True`, the preview keeps 245 assemblies and 48 shared supports.
The `unrepresented_source_position_count` stays at 42. Two of these positions now have source evidence for their `excluded_positions` entries.
The other 40 crossing positions stay unresolved and outside this result.

Canonical identities, source assignments, original exclusions and the preview title stay the same.

Previous FreeCAD and GUI evidence applies to the same chair shapes, placement and document operations.
No person or tool did a FreeCAD, GUI or full-XO test for this change.
These checks give no result for physical fit.
Local source and test evidence, preservation audits and review evidence are in `tmp/e001-exclusions/`.

The frozen 261-assembly candidate and all previous evidence with FAIL results stay the same.
The [provenance](../PROVENANCE.md), [licensing conditions](../LICENSING_BOUNDARIES.md) and all acceptance conditions stay the same.
Phase 9B stays Open at 3/6. No repair is available from the previous `2/2` allowance. LMS development stays stopped.

## ZY chairs at X1-Z and X2-Y on XO-001 — 2026-10-29

This Level 2 result supplies evidence for part of Exit 9B-3.
The optional `crossing_zy_contexts_path` input adds four ZY assemblies for eight source positions on XO-001.
The initial input is `None`. With `None`, previous operations and their results stay the same.
For the new operation, `include_single_rail=True` and source data for `RH-X1-Z` and `RH-X2-Y` are necessary.

The [source adapter](../../tracktemplate/compatibility/chair_crossing_zy_placement.py) validates those data.
It uses the two previous `.FCStd` files, each with 33 components.
The four new assemblies add 132 components. Templot 556b is the source.
The X1-Z code `21/ZY` and X2-Y code `22/XN` stay the same.

The [tests with standalone Python](../../tests/validate_phase9b_catalogue_crossing_zy.py) give `RED` results before this change and PASS results after this change.
The [adapter tests](../../tests/validate_phase9b_catalogue_crossing_zy_adapter.py) examine the optional input, assembly groups, previous product behaviour and checks after source changes.
The 16 new tests and related regression tests give PASS results.
Source checks compare the data for the four assemblies and eight source positions with the preserved source.

With all previous inputs, the adapter tests give these results:

| Data | Result |
| --- | ---: |
| `placement_count` | 249 |
| `represented_source_position_count` | 321 |
| `existing_shared_support_count` | 48 |
| `source_paired_crossing_support_count` | 4 |
| `finite_source_exclusion_count` | 2 |
| `unresolved_source_position_count` | 32 |

The results for the two E001 positions stay the same. This change adds no assembly at the other 32 positions.

Previous FreeCAD tests give evidence for the two `.FCStd` files.
No new test used FreeCAD or its display.
The previous evidence supplies no new visual result for the four assemblies.
Local source checks, `RED` results, failure classifications and results from regression tests are in `tmp/zy-crossing/`.
The independent reviews are in the same directory.

The frozen exact candidate with 261 assemblies and its files stay the same.
The previous evidence with FAIL results also stays the same. This result gives no new acceptance.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6.
No repair is available from the previous limit of `2/2`. LMS work stays stopped.

## AA/CD/DD/EF chairs on XO-001 — 2026-10-29

This Level 2 result supplies evidence for part of Exit 9B-3.
The optional `crossing_pair_contexts_path` input adds eight assemblies for 16 source positions on XO-001.
The initial input is `None`. With `None`, previous operations and their results stay the same.
`include_single_rail=True` is necessary for the new operation. The ZY input is optional.

The [source adapter](../../tracktemplate/compatibility/chair_crossing_pair_placement.py) validates the data for `RH-X4-A`, `RH-X6-C`, `RH-X7-D` and `RH-X8-E`.
It uses four previous `.FCStd` files. In that sequence, the files contain 42, 27, 33 and 33 components.
The eight assemblies add 270 components. Templot 556b is the source.
All previous identities and codes stay the same.

The [tests with standalone Python](../../tests/validate_phase9b_catalogue_crossing_pairs.py) give `RED` results before this change and PASS results after this change.
The [adapter tests](../../tests/validate_phase9b_catalogue_crossing_pairs_adapter.py) examine previous product behaviour, assembly groups, optional inputs and checks after source changes.
All 16 new tests and 145 related regression tests give PASS results.
`actual-source-comparison.py` independently compares 56 numbers from the eight assemblies and 180 numbers from component positions.
It gives a PASS result.
The tests do not construct new chair components.

With all previous inputs, which include ZY, the adapter tests give these results:

| Data | Result |
| --- | ---: |
| `placement_count` | 257 |
| `represented_source_position_count` | 337 |
| `existing_shared_support_count` | 48 |
| `source_paired_crossing_support_count` | 12 |
| `finite_source_exclusion_count` | 2 |
| `unresolved_source_position_count` | 16 |

The previous 249 assemblies and the two E001 results stay the same.
The 16 XA/BB source positions have no new assembly.

Previous FreeCAD tests give evidence for the four files. No new test uses FreeCAD or its display.
The previous evidence supplies no new visual result for the eight assemblies.
Local source checks, `RED` results, failure classifications, test results and independent reviews are in `tmp/paired-crossing/`.

The previous exact candidate with 261 assemblies and its files stay the same.
The previous evidence with FAIL results also stays the same. This result gives no new acceptance.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6.
No repair is available from the previous limit of `2/2`. LMS work stays stopped.

## XA/BB chairs on XO-001 — 2026-10-29

This Level 2 result supplies evidence for part of Exit 9B-3.
The optional `crossing_split_contexts_path` input adds four XA/BB assemblies for 12 source positions.
The initial input is `None`. With `None`, previous operations and their results stay the same.
`include_single_rail=True` is necessary. The ZY and AA/CD/DD/EF inputs are optional.

The [source adapter](../../tracktemplate/compatibility/chair_crossing_pair_placement.py) uses the previous `RH-X3-X` and `RH-X5-B` files.
The XA file has 33 components. The BB file has 43 components.
The four assemblies add 152 components. Templot 556b is the source.

The previous 257 assemblies, identities and codes stay the same.
The `existing_shared_support_count` value stays 48.

With all previous inputs, the [adapter tests](../../tests/validate_phase9b_catalogue_crossing_splits_adapter.py) give these results:

| Data | Result |
| --- | ---: |
| `placement_count` | 261 |
| `represented_source_position_count` | 349 |
| `existing_shared_support_count` | 48 |
| `source_paired_crossing_support_count` | 20 |
| `finite_source_exclusion_count` | 2 |
| `unresolved_source_position_count` | 4 |

Four XN source positions at X3-X have no assembly. The source has no evidence for their use with XA.
The two E001 results stay the same. This change adds no chair component without source evidence.

The [tests with standalone Python](../../tests/validate_phase9b_catalogue_crossing_splits.py) give a `RED` result before the product change.
All 14 new tests and 161 related regression tests give PASS results. The `skips` value is `0`.

An independent reviewer uses `actual-source-comparison.py` to compare 28 numbers from the four assemblies and 108 numbers from component positions.
It gives a PASS result. Its maximum difference is `1.14e-13 mm`. This result supplies no evidence for physical fit.
The 126 previous files and their hashes stay the same.

Previous FreeCAD tests supply evidence for the two files. No new test uses FreeCAD or its display.
Local evidence and independent reviews are in `tmp/xa-bb-crossing/`.
The previous exact candidate with 261 assemblies and its evidence with FAIL results stay the same.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. This result gives no new acceptance.
No repair is available from the previous limit of `2/2`. LMS work stays stopped.

## Source evidence for four XO-001 positions — 2026-10-29

This Level 2 result supplies evidence for part of Exit 9B-3.
The `classify_knuckle_exclusions` input supplies source evidence for four previous `22/XN` positions at X3-X.
Its initial value is `False`. With `False`, previous operations and results stay the same.
For `True`, the `crossing_split_contexts_path` input and its previous conditions are necessary.

The Templot 556b source with the previous source identity selects one XA assembly for each of `XO-001:A:X3-X` and `XO-001:B:X3-X`.
It selects no XN assembly there.
B15 makes four positions at the ends of parts with different names: `main-side wing knuckle` and `turnout-side wing knuckle`.
The `strictly_inside_actual_timber_outline` value is `true` for each end. Thus, the E001 method is not applicable.
The [new software](../../tracktemplate/compatibility/chair_crossing_endpoint_exclusions.py) examines the source identities and exact connections between these parts.

This change makes no new assembly or component. The 261 assemblies and all previous identities, codes and positions stay the same.
With all previous inputs, the results are:

| Data | Result |
| --- | ---: |
| `analysis_position_count` | 355 |
| `represented_source_position_count` | 349 |
| `unrepresented_source_position_count` | 6 |
| `finite_source_exclusion_count` | 2 |
| `source_endpoint_exclusion_count` | 4 |
| `unresolved_source_position_count` | 0 |
| `existing_shared_support_count` | 48 |

The four new results give no evidence that XA holds the parts at those ends.
The two E001 results stay in a different group. Their values stay the same. This result supplies no evidence for physical fit.

The [new tests](../../tests/validate_phase9b_catalogue_crossing_endpoints.py) give a `RED` result before the product change.
All ten new tests and 175 related regression tests give PASS results. The `skips` value is `0`.
The independent review gives PASS results for all four positions and 12 exact connections.
Three tests show that the software rejects changes to the previous source inputs. The 126 previous files and their hashes stay the same.

Local evidence and independent reviews are in `tmp/knuckle-exclusions/`.
This result uses evidence from previous FreeCAD tests. No new test uses FreeCAD or its display.
The previous exact candidate and all previous evidence with FAIL results stay the same.
The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.

[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. This result gives no new acceptance.
No repair is available from the previous limit of `2/2`. LMS work stays stopped.

## Manual FreeCAD workflow for Issue #230 — 2026-10-29

This Level 2 work supplies test software for Issue #230 and part of Exit 9B-3.
The [manual workflow](../../.github/workflows/native-geometry-pilot.yml) uses the [Phase 6 test](../../tests/freecad_validate_phase6_transition_exact_geometry.py).
It adds no chair component or software to calculate railway data. The `assert` checks stay the same.
The [validation instructions](../VALIDATION.md#manual-freecad-test-on-github) own the limits and conditions for its use.

The [new tests](../../tests/validate_hosted_native_geometry.py) examine the launcher and workflow without FreeCAD.
Test outputs and independent reviews are in `tmp/issue230/`.
No test in this cycle starts FreeCAD or the workflow on GitHub.
Installation, process controls and the FreeCAD result on GitHub have no new evidence.

The project owner's decision is necessary before a merge. A test must have authority from the project owner in a different decision.
This change gives no acceptance for FreeCAD tests, display behaviour, physical fit, production or a phase exit.
It gives no positive rights claim.
The XO-001 candidate and all evidence with FAIL results stay the same.

[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6.
No repair is available from the previous limit of `2/2`. LMS work stays stopped.

## L1 chairs after changes to canonical state — 2026-10-30

This Level 2 result supplies evidence for part of Exit 9B-3.
The new `preview_private_catalogue_heel_l1_chairs` command calculates positions from canonical state for the ten L1 chairs at S13, T1 and T2.
It uses the previous chair component shapes, stable identities and methods to put components in position.
The `XO-001.FCStd` reference and the initial operation of the complete crossover command stay the same.
The command makes chair component shapes only when a caller uses it.
The complete crossover command has the same input limits as before this change.

The seven source and test files have the same bytes as the files in commit `155cbb0353ca59a144df697197d8a4a68a91beef`.
The [`readiness` test](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41114880113) and [`native` test](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41116286780) give PASS results.
Independent result reviews give PASS results.
The `Generate` operation changes the alignment radius through 600 mm, 900 mm and 600 mm.
The caller does not make the crossover again.

The `source_frame_comparisons` value is `150` for all ten identities.
The `component_comparisons` value is `138` for two chairs at the three radii: `S13-A rail 1` and `S13-B rail 3`.
These chairs supply a sample of the ten chairs.
The `successful_preview_component_placements` value is `690` for three operations.
The `rolled_back_component_placements` value is `230` before removal, with a `total_materialised_component_placements` value of `920`.

Checks of `stale_source_rejected`, `wrong_frame_rejections`, `preview_undo_redo` and `late_verification_rollback` give PASS results.
The sentinel and cleanup checks give PASS results. The `skips` value is `0`.

The tests used FreeCAD without its display.
This supplies evidence for `native_portion` in `L1-QUALIFICATION-001`. The `gui_portion` stays `OPEN`.
Evidence from the FreeCAD display is necessary for alignment, the groups in the display, selection and the active view in this L1 operation.
Previous FreeCAD display evidence for `P` chairs applies to the methods that both commands use.
It does not supply evidence for this L1 operation in the FreeCAD display.

The exact candidate for XO-001 and all previous evidence with FAIL results stay the same.
No repair is available from the previous `2/2` limit.
This result gives no acceptance for the complete crossover operation, physical fit, product performance, production or phase exit.
It gives no positive rights claim.
[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. LMS work stays stopped.

The [evidence](https://github.com/Richard-Gnitnub/tracktemplate/releases/download/validation-l1-current-source-b53cc4e/l1-native-41116286780-reviewed-evidence.tar) contains the test results and independent reviews.
Its SHA-256 is `6061358800717ce6d1b3f460ea369a3cadfc0d3602aaaf69b434098a662a8f04`.

## Prepared L1 test for the FreeCAD display — 2026-10-31

This Level 2 work prepares one test for `L1-QUALIFICATION-001` and part of Exit 9B-3.
The [workflow](../../.github/workflows/l1-gui-validation.yml) uses the [test](../../tests/hosted_l1_gui_suite.py) through the [launcher](../../tools/hosted_l1_gui_validation.py).
Its `readiness` and `gui` steps use the same test. Each step must do its one test.

The `readiness` step opens a source file copy with the same hash as the source file. It does not construct chairs.
The `gui` step changes the radius through 600 mm, 900 mm and 600 mm for all ten L1 chairs.
It does checks of the `Generate` operation, component positions, selection and the FreeCAD display.

All 96 tests with standalone Python give PASS results. Checks of the Python source structure and Ruff checks give PASS results.
The quality review and security/recovery review give a PASS result independently for the prepared test.
The product source, ten inputs, previous exact candidate and previous evidence stay the same.
This work did not operate FreeCAD or do a display test.
The `gui_portion` of `L1-QUALIFICATION-001` stays `OPEN`.

The project owner authorises the two steps and their limits. The owner authorises test evidence that all persons can read.
The owner will merge the reviewed pull request. Recovery must give a PASS result before the first step.
Independent review must give a PASS result for `readiness` before the `gui` step starts.
Independent review of the result and `.png` files is also necessary for the second step.

The [validation policy](../VALIDATION.md#validation-execution-location) owns the conditions for the tests.
This project authority does not let the tests operate again or operate locally. It does not increase the repair limit.

Results for the prepared test, input hashes and independent reviews are in `tmp/l1-gui-preparation/`.
This work gives no acceptance for physical fit, a positive rights claim, production, product performance or phase exit.
No repair is available from the previous `2/2` limit.
[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. LMS work stays stopped.

## Chair display correction after `view.fitAll()` — 2026-11-01

This Level 2 correction supplies evidence for `L1-QUALIFICATION-001` and part of Exit 9B-3.
The [diagnostic on GitHub](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41304566238) gives a FAIL result at 600 mm.
The other `App.Document` for the test is active when the product examines the new `App.Document` for the chair display.
The test stops before the 900 mm test. The cause of the previous FAIL result at 900 mm stays unknown.

Independent review classifies the FAIL result at 600 mm as `implementation-defect`. Cleanup gives a PASS result.

The `_materialise_preview` method that the callers use makes its new `App.Document` active again after `view.fitAll()`.
It keeps all checks of `App.Document` identity, the `App.listDocuments()` result, `selection` and `preselection`.
The shapes and positions of the chair components stay the same. Operation without the FreeCAD display also stays the same.
Regression tests in standalone Python give PASS results for `App.setActiveDocument()`, rejected `selection`, `preselection` and `App.listDocuments()` changes, and `abortTransaction()`.
These tests do not supply evidence from the FreeCAD display.

The launcher on GitHub uses only the reviewed bytes of the corrected product file.
All other frozen product files, the initial test for the FreeCAD display, its inputs and all limits for the test stay the same.
New `readiness` evidence and independent review are necessary before that test operates again.
The `gui_portion` stays `OPEN`.

Evidence and independent reviews are in `tmp/l1-preview-activation/`.
The project owner authorises repair, review and merge for this task.
The evidence preserves the previous FAIL results and the use of the full `2/2` repair limit.
The project owner authorises more repairs for this task.

This correction gives no acceptance for physical fit, production, product performance or phase exit.
It gives no positive rights claim.
[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. LMS work stays stopped.

## L1 chair display test on GitHub — 2026-11-01

This Level 2 result supplies the missing FreeCAD display evidence for `L1-QUALIFICATION-001` and part of Exit 9B-3.
The [`readiness` test](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41308881938) and [complete display test](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/41309891401) give PASS results.
Independent review gives PASS results for both tests.
The initial display test, its ten inputs and all limits for the test stay the same.

The display test uses ten L1 chairs at 600 mm, 900 mm and 600 mm.
It completes three `Generate` operations, with `body_frame_comparisons=30`, `layer_visibility_selection_checks=75` and `successful_preview_component_placements=690`.
It completes one test with `skips=0` and gives the success sentinel.
An independent reviewer visually examines all 12 chair `.png` files and three `radius-input.png` files.
Checks of `App.Document` conditions, selection, `preselection`, input hashes and cleanup give PASS results.

Independent review gives `L1-LIFECYCLE-ACTIVE-01` the result `VERIFIED_REPAIRED_FOR_BOUNDED_L1_WORKFLOW`.
The display test supplies the missing evidence for `L1-ACTIVATION-RUNTIME`. The `L1-QUALIFICATION-001.gui_portion` has a PASS result.

The initial workflow for `L1-GUI-41298217983-POSTCONDITION` now gives a PASS result after the reviewed repair.
The cause of that previous FAIL result stays unknown. The evidence preserves the previous FAIL result.
These results do not prove correct operation for other callers or different times between operations.

The recorded test time is 1,150.38 seconds. The measured `memory_peak_bytes` value for FreeCAD is `2010689536`.
The `accounting` value is `sampled-lower-bound`: actual maximum values and final totals can be more than the measured values.
Cleanup gives a PASS result for FreeCAD, the display and the temporary input files.

For the host, each `total` value for `some` and `full` in `/proc/pressure/memory` increases by 1 µs.
The related totals for FreeCAD and the display stay at `0`.
The `local_pressure_guard_qualification` value stays `False`. This result gives no acceptance for product performance.

The evidence and independent reviews are in `tmp/l1-preview-activation/gui-41309891401/`.
Checks of independent preservation and recovery give PASS results for all 192 result files.
The evidence preserves the use of the full previous `2/2` repair limit. The project owner authorises more repairs for this task.

This result gives no acceptance for physical fit, production or phase exit. It gives no positive rights claim.
[Phase 9B](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions) stays `Open` at 3/6. LMS work stays stopped.

## CC chairs on TO-001 — 2026-11-01

This Level 2 change supplies more evidence for Exit 9B-3.
The [source adapter](../../tracktemplate/compatibility/chair_turnout_check_placement.py) adds a different display of three CC assemblies on the specified `TO-001` turnout (`Left-hand`).
The display keeps private-development status. The selected source identities are `X2-Y`, `X3-X` and `X4-A`.
Each assembly holds the parts with source names `main-side stock rail` and `main-side check rail`.

The preserved Templot 556b software selects the CC type for parallel parts at these six source positions.
Each assembly has the same 33 chair components. The software turns and moves all components together, with the 16 components that attach the assembly.
The source record has `source_rail_code` equal to 1, and the software does not turn the parts as it does for `Right-hand`.
The chair shapes stay the same. The software that reads chair files, makes shapes and keeps the previous display condition stays the same.

The [tests without FreeCAD](../../tests/validate_phase9b_turnout_central_cc.py) gave `RED` before the product change and `PASS` after it.
All 14 tests give `PASS` results. They check the six source identities, component positions and directions, incorrect inputs, source changes and the API.
Seven related groups of regression tests give `PASS` results.

An agent who did not change the product froze source results before the candidate check.
The agent compared all 99 component positions and 4,746 source points with those results.
The maximum difference is `1.2710574864626038e-13 mm`. The test calculates this difference. It is not a tolerance for physical fit.

The agent also checked 2,604 source points from the complete `raw_requests` records. All six tests of incorrect results gave the required failures.
The checks use preserved chair files and three points on the alignment calculated from preserved data for `X2-Y`, `X3-X` and `X4-A`.
The checks do not use a FreeCAD document. The result supplies no evidence that FreeCAD makes or shows these assemblies correctly.

Previous FreeCAD and display evidence is applicable to the CC shapes and the software that moves them and keeps the previous display condition.
The project did no new FreeCAD, display or complete `XO-001` test for this change. New FreeCAD and display evidence for these three assemblies is not available.
Source, test and review evidence is in `tmp/to001-chair-placement/`.

The 168 source identities, `chair_code_label` values and initial `analytical_only` records stay the same.
The previous 59 S1/S1J and 14 P positions stay the same. The new route shows six more positions with three assemblies.
These routes include 79 positions. They do not make one complete turnout display.

Of the other 89 positions, 24 have `chair_code_label` equal to `""` and 65 are outside these routes.
The 65 positions include ten with codes `1P/2P` or `3P-11P`, seven with `L1` and seven with `CC`.
The other 41 positions have codes `AA`, `AB`, `BB/BC`, `CD`, `EF`, `XA`, `XN` and `ZY`.
Their number of assemblies needs source evidence.

The [provenance](../PROVENANCE.md) and [licensing conditions](../LICENSING_BOUNDARIES.md) stay the same.
This result gives no acceptance for physical fit, production, product performance or phase exit. It gives no third-party permission.
Phase 9B stays Open at 3/6. The previous `2/2` limit is fully used. LMS work stays stopped.

## Seven more chair assemblies on TO-001 — 2026-11-01

This Level 2 change supplies more evidence for Exit 9B-3.
The [source adapter](../../tracktemplate/compatibility/chair_turnout_single_rail_placement.py) supplies seven more chair assemblies with private-development status for the specified `TO-001` source (`Left-hand`).
The selected identities are `S13`, `T1` and `T2`, with `source_rail_code` equal to `2` or `4`, and `T14`, with that value equal to `2`.

The preserved Templot 556b source selects six `L1` assemblies and one `S1` assembly.
The `S1` assembly is at `T2`, with `source_rail_code` equal to `4`. Its initial `chair_code_label` stays `L1`.
The software uses 155 chair components from the preserved files again. It changes their positions and directions, but their shapes stay the same.
The source calculates positions and directions for each component that attaches an assembly.

The three new groups of [tests without FreeCAD](../../tests/validate_phase9b_turnout_single_rail.py) give PASS results after the initial FAIL results.
They examine identities in the source, source selection, positions, directions, incorrect inputs and the software that keeps the previous display condition.
Related regression tests give PASS results.
The source check uses the preserved 168-position data and the product software that reads and validates chair files.
A different tool calculates the positions from source data and compares all 155 component positions. These checks give no tolerance for physical fit.

Previous FreeCAD and display evidence is applicable to the chair shapes and the software that moves them and keeps the previous display condition.
The implementing agent did no new FreeCAD, display or full `XO-001` test for this change. FreeCAD and display evidence for these seven assemblies stays necessary before Exit 9B-3 acceptance.
The source evidence, test results with PASS or FAIL status, and independent review are in `tmp/to001-single-rail/`.

The previous 59 `S1`/`S1J` positions, 14 `P` positions and three `CC` assemblies stay the same.
The routes include 86 of the 168 source positions after this change. They do not make one full turnout display.
Of the other 82 positions, 24 have `chair_code_label` equal to `""` and these routes do not include the other 58.
The source selects `L1` for five `S1` positions: `S13` and `T1` with `source_rail_code` equal to `1` or `3`, and `T2` with `source_rail_code` equal to `3`.
This change does not correct these five `S1` selections.

The conditions in [PROVENANCE.md](../PROVENANCE.md) and [LICENSING_BOUNDARIES.md](../LICENSING_BOUNDARIES.md) stay the same.
This result gives no acceptance for physical fit, production, product performance or phase exit. It gives no third-party permission.
Phase 9B stays Open at 3/6. The frozen history for `2/2` stays the same. LMS work stays stopped.

## Five L1 corrections on TO-001 — 2026-11-01

This Level 2 change corrects five chair displays for Exit 9B-3. The output keeps its private-development status.
The source selects `L1` at `S13` and `T1` with `source_rail_code` equal to `1` or `3`, and at `T2` with that value equal to `3`.
The [turnout command](../../tracktemplate/compatibility/chair_turnout_single_rail_placement.py) uses 115 preserved L1 components at these five positions.
The chair shapes stay the same. The turnout and crossover commands use the same software to calculate positions from source data.

The workflow's S1 and S1/S1J commands do not select these five S1 displays before `_recover_positions` operates.
The S1 command selects 49 assemblies. The S1/S1J command selects 49 S1 and five S1J assemblies.
The `preview_private_catalogue_turnout_single_rail_chairs` command selects eleven L1 and one S1 assembly. The previous seven `SingleRailPlacement` values stay the same.

The initial source data and `plan` stay the same. The `T2` diagnostic stays `gauge normal is not perpendicular to the local rail tangent`.
The functions `preview_s1_reference_chairs` and `preview_s1_s1j_reference_chairs` keep their previous behaviour when the caller supplies no `source_selection_filter`.
The workflow commands always supply `exclude_turnout_heel_l1`.

The tests give FAIL results before the changes and PASS results after them.
The independent check compares five `SingleRailPlacement` values, twenty `fixing_frames` values and all 115 replacement components with preserved source evidence.
It compares 4,865 points from preserved `*.Shape.brp` files and 4,680 points from source output.
The maximum difference is `1.6077746776921858e-13 mm`. This value is not a tolerance for physical fit.

The independent check uses the workflow commands with test software for the `document` and `_host` inputs. It preserves all 168 source data items.

Previous FreeCAD and display evidence applies to the preserved shapes and the software that keeps the previous display condition.
The implementing agent did no new FreeCAD, display or full `XO-001` test for this change. FreeCAD and display evidence for these TO-001 positions stays necessary before Exit 9B-3 acceptance.
The source evidence, test results with PASS or FAIL status, and independent reviews are in `tmp/to001-heel-l1/`.

The routes still include 86 of 168 positions. The five L1 corrections add no positions.
Of the remaining 82 positions, 24 have `chair_code_label` equal to `""` and 58 have other values.

The [provenance](../PROVENANCE.md) and [licensing conditions](../LICENSING_BOUNDARIES.md) stay the same.
This result gives no acceptance for physical fit, production, product performance or phase exit. It gives no third-party permission.
Phase 9B stays Open at 3/6. The frozen history for `2/2` stays the same. LMS work stays stopped.
