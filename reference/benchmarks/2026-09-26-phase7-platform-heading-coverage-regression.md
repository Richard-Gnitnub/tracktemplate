# Phase 7 evidence for platform station range

Status: **Level 2 candidate evidence for three calculations and their B16 caller.**

The [API instructions](../contracts/phase7-platform-heading-coverage.md)
own the calculations and route. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and
exit status. This record gives no exit or performance acceptance.

## Current owner view

| Field | Result |
| --- | --- |
| **Current state** | The candidate has direct, qualified and paired GUI PASS results. All 14 affected qualified proofs have PASS results. Phase 7 stays Open at 0/4. |
| **What changed** | Three B14/B15-identical calculations use Core through the selected B16 route. The route has schema `15`, 24 selected functions and 40 caller identities. |
| **What now works** | The 193-case comparisons preserve values and diagnostics. Four selected read paths preserve their observed order and selected injected failures. The paired GUI comparison preserves the selected platform Create/Edit result. |
| **Limitations/findings** | Normal repairs remain 2/2 exhausted. The two earlier owner exceptions and the final 1/1 exception are consumed. Original failures remain evidence. Publication requires the complete local validation profile and independent review. |
| **Owner decision** | The owner authorised the bounded continuation and named test-only exceptions. The owner permits continuation of the existing documentation route. No phase exit, performance result, output status or release state is accepted. |
| **Next action** | Complete the remaining validation and independent review under current authority. The existing documentation route must supply its required results before controlled-baseline acceptance. |

## Scope and source

The protected-main baseline is
`482eb4cb0dddbebdbe92d72fdaa3e1e98d2d5063`, after PR #85.
D-GOV-004 and the owner's 2026-09-26 continuation authorise one Level 2
result. D-P7-001 keeps Phase 7 Open at 0/4.

B14 and B15 have equal definitions of `alignment_progress_at_station`,
`station_for_progress_heading` and `platform_coverage_bounds`. Their SHA-256
values are in the [contract data](../contracts/phase7-platform-heading-coverage.json).
The legacy files stay unchanged. Their product caller is
`calculate_platform_boundaries`.

The selected B16 route puts the three calculations in
`tracktemplate.domain.alignment` through `tracktemplate.api`.
The host retains FreeCAD point construction and document operations. The
route has schema `15`, 24 selected functions and 40 caller identities.

The document need is the selected product change and its retained evidence.
The API instructions are a specification. This report is evidence or audit.
Both are candidate documents under the Technical Documentation Management
Plan. The API instructions own calculation details; current phase evidence
owns the result. Paths, identifiers, commands, values, diagnostic text and
SHA-256 values are exact content. This authoring pass makes no freeze,
review, linguistic conformance or publication claim.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `51fa8afcb9c82f7b278995c79efc5b833fc7bd3be4fd724f86b465746b6ba32c` |
| `tracktemplate/api.py` | `9ad1739b8289d5ba0bc2de6f36111c4c8e9ea25ba43b520386986824cf57abb2` |
| `tracktemplate/compatibility/transition_workflow.py` | `7a6364d48a0e1cfc2c591c3c1131d39cc647ec2bbaf03c772f9341d8f9032edf` |

## Direct comparisons

The retained pre-edit B14/B15/current B16 baseline has a PASS result for
193 observations. It covers the three functions, values, diagnostics and
input read paths. Its raw JSON is in ignored
`tmp/phase7-platform-heading-coverage/b14-b15-current-b16-baseline.json`.
The file SHA-256 is
`bd1a53078684bfe7f85f24a90af606fd5854b2adacc0a996a4a961185ba97107`.
Expanded read and failure traces have SHA-256
`10a8caa8866bdf4f9bb7263e42fa4a7591a19f5a339d02e8a7c8ff349324de1f`.

The selected-Core standalone proof has a PASS result for the same
193 observations. It includes four complete read and synthetic host-vector
construction paths. Each path has injected failures at its first, middle,
last and first `App.Vector` positions. It also includes seven
incomplete-binding or rollback cases. Its raw JSON is in ignored
`tmp/phase7-platform-heading-coverage/candidate-standalone-v3.json` with
SHA-256
`96c82553a702f9b34aa0394606609c7c2f97d6ad6a5fa225ff97aaec861bf406`.
The complete log has SHA-256
`d4d63f89c738753f2f73851591c21c950dc96c29f90460b0501c7580f14c3f19`.
The required sentinel is
`Phase 7 platform heading and coverage validation passed`.
The final focused standalone result has the same JSON and log hashes at
`tmp/phase7-platform-heading-coverage/final-focused-standalone.json` and
`tmp/phase7-platform-heading-coverage/final-focused-standalone.log`.

The exact D-GOV-019 FreeCAD preflight has a PASS result. Its log SHA-256 is
`6ea87e120344d8ed56ebc905321733bd584742795ed164bd5a4da1745f38c15d`.
The fresh qualified FreeCADCmd proof has a PASS result for 193 cases,
the selected caller's rejection and unchanged document state. Its raw JSON
is in ignored `tmp/phase7-platform-heading-coverage/candidate-qualified.json`
with SHA-256
`4eb506ebbd1bd80db89b79c208d5a527eefb2e5e55af50d015488256269494ac`.
The complete log has SHA-256
`a9fbe666423fbf4c55e700e5135bb804c2dbb4f3c421e732d31562ef737b6053`.
The required sentinel is
`Phase 7 platform heading and coverage FreeCAD validation passed`.

## Normal repairs

The first affected legacy platform-position proof has a FAIL result. Its
synthetic host does not supply the four coverage constants that the selected
route now verifies. The full retained failure is at
`tmp/phase7-platform-heading-coverage/legacy-platform-bounds-first-fail.log`
with SHA-256
`97ee20ea61ba0c0a4f963521685340d27fcc33015053216c264e6edcfbf6e9a9`.
Repair 1 made a bounded test-only correction to the fixture and directly
dependent route identities. The original failure remains evidence.
The classified repair-1 record is at
`tmp/phase7-platform-heading-coverage/repair1-classification.json` with
SHA-256
`1a64fb4e10f05939575a418a197fc1ec989f0449e0c8374fa9abf62dc40bc888`.
The same original proof then had a PASS result. Its retained log is
`tmp/phase7-platform-heading-coverage/legacy-platform-bounds-repair1-rerun.log`.
Its SHA-256 is
`ac0b59d5f976baa87142bb4757b6a35f9475c96a5273e75d0607199abf3955de`.

The first affected standalone matrix after repair 1 had 8 PASS and 7 FAIL
results. The seven failures were current-route expectations or one
incomplete synthetic function map. The complete 15-test manifest is at
`tmp/phase7-platform-heading-coverage/affected-standalone-repair1/manifest.json`
with SHA-256
`4b9111aede4c3c63e5c1fb70c95f907183318d41b51d5845718b3f266d05789e`.
The repair-2 classification records each command, raw log, first failed
assertion and repair boundary. It has SHA-256
`3d26c2be68a699d8f4cfefcb3bde9213e47bbe1c4e7b9570752b0ffae1c8c094`
at `tmp/phase7-platform-heading-coverage/repair2-classification.json`.
After the bounded test-only correction, all seven exact failed proofs had
PASS results. The rerun manifest has SHA-256
`69003b7a937f81f27016e6883927d1c4b0d350c05311a5c1f532eccb80f4223a`
at `tmp/phase7-platform-heading-coverage/affected-standalone-repair2/manifest.json`.
No product source changed in either repair. The outcome's repair accounting
is 2/2 exhausted. All first failures remain retained evidence.

## Qualified proof sequence and owner exceptions

The first affected qualified proof stopped at
`tests/freecad_validate_phase3_transition_slice.py`. Its current-route
assertion expected 21 selected functions; the route has 24. The process
returned zero, but its required success sentinel was absent. The result
was FAIL. The original log SHA-256 is
`6b1071ee9e53a9ab77fd608de7f8325f8c95947860c5ee1d795ccb9be86e7fbe`.
The original manifest remains INCOMPLETE at
`tmp/phase7-platform-heading-coverage/qualified-matrix/manifest.json`, with
SHA-256
`9fa05162f4cc7d15a368ce008992544a32c1f664d69ddcec04e49300fa303489`.
Its classification is at
`tmp/phase7-platform-heading-coverage/qualified-matrix/failure-classification.json`,
with SHA-256
`e2f557da28aaf19b085bd02980d8d43b33a3c2ed3397e5d859b7293239bba55b`.

The owner authorised one test-only exception for that selected-function
assertion. The same proof then returned zero with its required sentinel.
Its PASS receipt is
`tmp/phase7-platform-heading-coverage/qualified-matrix/owner-exception-phase3-rerun.json`,
with SHA-256
`01de838be892437fc2070b9ac040ab24653612057c501d8b24a5b2dd7b29f21a`.
Its log SHA-256 is
`239280a642d684db1c4c4351f89105c2f64ee61bf1ab3c087dda4d73f06b8f4c`.
That exception is consumed. Normal repairs remain 2/2 exhausted.

Five later qualified proofs passed. The station-mapping proof then failed
because it expected 39 caller identities; the route has 40. The original
log SHA-256 is
`1fa50614e86979ab50c174aa0c502ff51af26be3f057c54725720a5d5c162dd9`.
The manifest remains INCOMPLETE at
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/manifest.json`,
with SHA-256
`862b8515da16f06fde37e4205bc08068a6610f1041864ccd550954ed444eaa31`.
Its classification is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/station-mapping-failure-classification.json`,
with SHA-256
`7e722fc25247193c3ee6381dc5d9e12c7f7d957d1ea47700ea2c16e5baed5e8a`.
That record identifies the related handedness and platform-transition
assertions as static findings. They were not executed proof results at
that point.

The owner authorised changes to those three caller-count assertions from
39 to 40. The station-mapping rerun failed for a different reason.
Its loop assumed that each selected caller had `__globals__`.
The selected `_AlignmentProgressAdapter` has no such attribute.
The failed receipt is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/owner-caller-count-station-rerun.json`,
with SHA-256
`bb7b889ad278e78acf1ceba7b416b5893d6fcd0b107eef37350c474a76a342db`.
Its log SHA-256 is
`22840d27bd4ee9e420d3eb022fb4ad10836a7b568fbc2a7711be3e88a3bfacf9`.
The final classification records a `test-or-oracle-defect` at
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/station-adapter-failure-classification-final.json`,
with SHA-256
`040077b71fb5fdb97b410c5a03b433efa6f3bb1e35e84eeaadb1330c12095f2e`.
It supersedes the preliminary classification, whose SHA-256 is
`769ce6e1410b69fb46ee2419a6eb6cc72a94eeb6b3562be62d5e7f35f9f56e41`.
Both classification records remain available. The three-count exception
is consumed; it did not authorise the later loop correction.

The owner then authorised a final 1/1 test-only exception for that loop.
The same station-mapping proof returned zero with its required sentinel.
Its PASS receipt is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/owner-final-loop-station-rerun.json`,
with SHA-256
`b7d5434481b3a874508ce8c83bcc470fd59eec6f30d937ca71317bb62e5d11e6`.
Its log SHA-256 is
`85ed9348d35d84fd0a9ea4f9e6841c9d40df5a3c809c2f742aeedf61b4fdadc9`.
The final exception is consumed. None of these exceptions changed product
source or reset normal repair accounting.

The remaining seven affected qualified proofs then passed. The final
14-proof manifest has a PASS result at
`tmp/phase7-platform-heading-coverage/final-qualified-matrix/manifest.json`,
with SHA-256
`6fce1acabef067633b22f9595ecf98271afd5c0f7928e21d880b56fac0ee19ce`.
It combines the unchanged earlier PASS results, the final station-mapping
PASS result and the seven later results. Each proof has its required
success sentinel. This combined result does not replace an earlier failed
or incomplete record.

## Paired GUI comparison

One isolated GUI process ran the protected-main baseline. A second process
ran the candidate on the same exact D-GOV-019 host profile:
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2`.
Both jobs have PASS results, zero process exit status and their required
success sentinel. Their common fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The fixture was unchanged after each job.

The fixed protocol covers `PLATFORM_CONSTANT` for a platform outside one
track. It compares Create and Edit through B16 Generate/Replace, Undo/Redo,
two selected length-and-position rejections, Save, reopen and cleanup.
It also compares one cold call and three repeated calls to
`calculate_platform_boundaries` with unchanged inputs. The protocol is
`tmp/phase7-platform-heading-coverage/gui-fixed-protocol.json`, with SHA-256
`a4db5a8c3a29e31a0d61ceffe5e4dec0c899ceb100edfd161ac2bca7b8f327a2`.

The product results match. The common result SHA-256 is
`35f77a72ad6a8b004b863d0a7241dad3bbc863ef4c317d482f8a755060c22230`.
The comparison excludes the save path and measured time and resource
values from that equality check. The complete comparison has a PASS result
at `tmp/phase7-platform-heading-coverage/gui-full-comparison.json`, with
SHA-256
`0cc4b3a10c474d88c0b44629ea6cd2cf998022241e40b672ee4a49cf26e03c4c`.

| Evidence | Baseline SHA-256 | Candidate SHA-256 |
| --- | --- | --- |
| Source manifest | `5bf39bcbcadeb2c1f75e8ce3027c0f872d08ee2c2d454f9a3a2b3473c642121d` | `92f6528d5021a5b59e283a1856985b4398e966207f1c899989843017e5a83fcf` |
| Job receipt | `21a7880dfd4f6cad761c65a460630031b132ca94c65f14f586bafabae07a1177` | `98ca01c0d39850531cdd1f7f98e9135847d55eef8af751298ed8ce09eab8f9f9` |
| Raw record | `8cd1c6e182d8b57e0ae9ea47974961c1e1a061ef8b5036a509bd17a36db7abd2` | `60bb31109a56405cf8e4200ef6099525442244eadd47d929e12323f7c0385ca5` |

The source manifests and job receipts are in ignored
`tmp/phase7-platform-heading-coverage/`. The raw records are in
`benchmark-output/freecad-bridge/phase7-platform-heading-coverage/` under
`baseline-attempt-01/run.json` and `candidate-attempt-01/run.json`.

This comparison covers only the named GUI scenario. Other `coverage`
values need a fresh paired baseline before a GUI equivalence claim.
The cold and repeated samples are descriptive regression observations.
One process per route supplies no D-P6-008 performance credit and changes
no measurement rule.

## Owner-view invocation

An additional owner-view check stopped during import, before it executed
an assertion. The ad hoc command omitted the test import path. Its
`ModuleNotFoundError` and exact command remain no-proof evidence in
`tmp/phase7-platform-heading-coverage/owner-view-no-proof-receipt.json`,
with SHA-256
`c437d697e89642159451f0ef441112e228696e26f173c74624833ada2807c8b2`.

The owner authorised the invocation correction and one rerun. The same
check then passed with the test directory on `PYTHONPATH`. All four
deliberately incorrect owner views were rejected. The rerun receipt is
`tmp/phase7-platform-heading-coverage/owner-view-corrected-invocation.json`,
with SHA-256
`546607a182684056ce55680cd705c7fd8c55f12bcc1f05867f73ff67c59be5e4`.
This command correction changed no source or test. Normal repairs remain
2/2 exhausted, and all earlier exceptions remain consumed.

## Complete validation profile

The complete `transition` profile has a PASS result for all seven steps.
The full logs are in ignored
`benchmark-output/validation-pipeline/20260926T214524822178Z/`.
The command output is retained at
`tmp/phase7-platform-heading-coverage/complete-transition-profile.log`.
This result includes the complete standalone profile and the qualified
transition persistence, scene and Edit-lifecycle checks.

## Remaining evidence

Publication requires the independent source-and-test review.
The validation and GUI results do not establish that review result.
The existing documentation route must also supply its required results.
This candidate record makes no claim that those later steps have passed.
Their exact results belong in the applicable validation and review receipts.

## Limits

This candidate does not compare all platform geometry, other Core layouts
or export bytes. It does not remove the legacy path. A GUI resource value
from one sample per state gives no D-P6-008 performance credit.

Phase 7 stays Open at 0/4 with all exits Pending. Output stays at
private-development status and project status stays `unknown`.
D-P6-008, all comparison requirements and all legacy-retirement conditions
stay in full.
