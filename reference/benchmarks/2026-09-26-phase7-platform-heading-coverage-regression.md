# Phase 7 evidence for platform station range

Status: **Level 2 evidence for the exact candidate: three functions and their B16 caller.**

The [API instructions](../contracts/phase7-platform-heading-coverage.md)
own the functions and route. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and
exit status. This record gives no exit or performance acceptance.

## Current owner view

| Field | Result |
| --- | --- |
| **Current state** | The exact candidate has PASS results from tests in standalone Python, FreeCAD and the FreeCAD human interface. All 14 tests of the related routes have PASS results. Phase 7 stays Open at 0/4. |
| **What changed** | Three functions have the same source in B14 and B15. They use Core through the selected B16 route. The route has schema `15`, 24 selected functions and 40 caller identities. |
| **What now works** | Tests for 193 inputs give the same values and diagnostics. Four selected paths read inputs in the same sequence and give the same results for errors that tests supply. The test with the FreeCAD human interface gives the same platform result for Create/Edit. |
| **Limitations/findings** | The two usual repairs are completed (2/2). No more usual repairs are permitted. The changes in the two owner decisions before the last decision and the last 1/1 decision are completed. Those decisions give no more project authority for repairs. The first FAIL results stay as evidence. The full validation profile for local use and independent review are necessary before publication. |
| **Owner decision** | The owner authorised continuation in the bounded scope and the named changes to tests. The owner also authorised continuation of the Documentation Review lifecycle. No phase exit, performance result, output status or release state has acceptance. |
| **Next action** | Complete the remaining validation. Complete the independent review. Use the current project authority. The Documentation Review lifecycle must supply its necessary results before controlled-baseline acceptance. |

## Scope and source

The comparison baseline is protected `main` at
`482eb4cb0dddbebdbe92d72fdaa3e1e98d2d5063`, after PR #85.
D-GOV-004 and the owner's decision on 2026-09-26 authorise one Level 2
result for its bounded scope. D-P7-001 keeps Phase 7 Open at 0/4.

The `alignment_progress_at_station`,
`station_for_progress_heading` and `platform_coverage_bounds` functions have the same source in B14 and B15.
Their SHA-256 values are in the [contract data](../contracts/phase7-platform-heading-coverage.json).
The B14/B15 files do not change. Their product caller is
`calculate_platform_boundaries`.

The selected B16 route puts the three functions in
`tracktemplate.domain.alignment` through `tracktemplate.api`.
FreeCAD keeps the operations that make points and change documents. The
route has schema `15`, 24 selected functions and 40 caller identities.

The document need is the selected product change and its retained evidence.
The API instructions have the document class “specification or inventory”.
This report has the document class “evidence or audit”. The two documents
use the Technical Documentation Management Plan.

The API instructions own the information about each function. Current phase evidence
owns the result. Paths, identifiers, commands, values, diagnostic text and
SHA-256 values are exact content. This report does not freeze the exact candidate
or give a review result. It claims no linguistic conformance or publication.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `51fa8afcb9c82f7b278995c79efc5b833fc7bd3be4fd724f86b465746b6ba32c` |
| `tracktemplate/api.py` | `9ad1739b8289d5ba0bc2de6f36111c4c8e9ea25ba43b520386986824cf57abb2` |
| `tracktemplate/compatibility/transition_workflow.py` | `7a6364d48a0e1cfc2c591c3c1131d39cc647ec2bbaf03c772f9341d8f9032edf` |

## Tests in standalone Python

The test before the edit used B14, B15 and the comparison baseline for B16.
It has a PASS result for 193 inputs. It includes the three functions, values,
diagnostics and paths that read inputs. Its full JSON is in the ignored file
`tmp/phase7-platform-heading-coverage/b14-b15-current-b16-baseline.json`. The file SHA-256 is
`bd1a53078684bfe7f85f24a90af606fd5854b2adacc0a996a4a961185ba97107`. The more detailed data about the sequence to read inputs and give errors have SHA-256
`10a8caa8866bdf4f9bb7263e42fa4a7591a19f5a339d02e8a7c8ff349324de1f`.

The test in standalone Python selects Core and has a PASS result for the same
193 inputs. It includes four full paths that read inputs and make values
for `App.Vector` with the test fixture. The tests supply errors at the first,
middle and last positions in each path, and at its first `App.Vector` position.
They also include seven inputs for selections that are not full or for recovery after a setup error.

The full JSON is in the ignored file
`tmp/phase7-platform-heading-coverage/candidate-standalone-v3.json` with SHA-256
`96c82553a702f9b34aa0394606609c7c2f97d6ad6a5fa225ff97aaec861bf406`. The full command output has SHA-256
`d4d63f89c738753f2f73851591c21c950dc96c29f90460b0501c7580f14c3f19`. The necessary sentinel is
`Phase 7 platform heading and coverage validation passed`. The last test of this scope in standalone Python has the same
JSON and command-output hashes at
`tmp/phase7-platform-heading-coverage/final-focused-standalone.json` and
`tmp/phase7-platform-heading-coverage/final-focused-standalone.log`.

The FreeCAD preflight for the exact host profile in D-GOV-019 has a PASS result.
Its command-output SHA-256 is
`6ea87e120344d8ed56ebc905321733bd584742795ed164bd5a4da1745f38c15d`. The new test with FreeCADCmd has a PASS result for 193 inputs.
It also validates the selected caller when it rejects an input and makes sure that the document does not change.

Its full JSON is in the ignored file `tmp/phase7-platform-heading-coverage/candidate-qualified.json`
with SHA-256
`4eb506ebbd1bd80db89b79c208d5a527eefb2e5e55af50d015488256269494ac`. The full command output has SHA-256
`a9fbe666423fbf4c55e700e5135bb804c2dbb4f3c421e732d31562ef737b6053`. The necessary sentinel is
`Phase 7 platform heading and coverage FreeCAD validation passed`.

## Usual repairs

The first test of the previous platform-position function has a FAIL result.
Its fixture does not supply the four values of `coverage` that the selected
route validates. The full command output for the FAIL result is at
`tmp/phase7-platform-heading-coverage/legacy-platform-bounds-first-fail.log` with SHA-256
`97ee20ea61ba0c0a4f963521685340d27fcc33015053216c264e6edcfbf6e9a9`. Repair 1 changed only the fixture and the route identities
that directly depend on it. The first FAIL result stays as evidence.

The failure classification for repair 1 is at
`tmp/phase7-platform-heading-coverage/repair1-classification.json` with SHA-256
`1a64fb4e10f05939575a418a197fc1ec989f0449e0c8374fa9abf62dc40bc888`. The same first test then had a PASS result. Its complete command output is
`tmp/phase7-platform-heading-coverage/legacy-platform-bounds-repair1-rerun.log`. Its SHA-256 is
`ac0b59d5f976baa87142bb4757b6a35f9475c96a5273e75d0607199abf3955de`.

The first set of tests in standalone Python after repair 1 had 8 PASS and 7 FAIL
results. The seven FAIL results came from checks of the current route or a fixture
that did not supply all necessary functions. The full manifest for the 15 tests is at
`tmp/phase7-platform-heading-coverage/affected-standalone-repair1/manifest.json` with SHA-256
`4b9111aede4c3c63e5c1fb70c95f907183318d41b51d5845718b3f266d05789e`.

The failure classification for repair 2 records each command, complete command output,
first incorrect check and the limit of the repair. It has SHA-256
`3d26c2be68a699d8f4cfefcb3bde9213e47bbe1c4e7b9570752b0ffae1c8c094` at `tmp/phase7-platform-heading-coverage/repair2-classification.json`.
After the change to tests only, the same seven tests with FAIL results had PASS results.
The manifest for those tests has SHA-256
`69003b7a937f81f27016e6883927d1c4b0d350c05311a5c1f532eccb80f4223a` at `tmp/phase7-platform-heading-coverage/affected-standalone-repair2/manifest.json`.

The product source did not change in the two repairs. The two usual repairs
are completed (2/2). No more usual repairs are permitted. All first FAIL results
stay as retained evidence.

## FreeCAD tests and owner decisions

The first FreeCAD test of a related route stopped at
`tests/freecad_validate_phase3_transition_slice.py`. Its check of the current route used 21 as the necessary number of
selected functions. The route has 24. The process returned zero, but its
necessary sentinel was missing. The result was FAIL.

The first command-output SHA-256 is
`6b1071ee9e53a9ab77fd608de7f8325f8c95947860c5ee1d795ccb9be86e7fbe`. The first manifest stays INCOMPLETE at
`tmp/phase7-platform-heading-coverage/qualified-matrix/manifest.json`, with SHA-256
`9fa05162f4cc7d15a368ce008992544a32c1f664d69ddcec04e49300fa303489`. Its failure classification is at
`tmp/phase7-platform-heading-coverage/qualified-matrix/failure-classification.json`, with SHA-256
`e2f557da28aaf19b085bd02980d8d43b33a3c2ed3397e5d859b7293239bba55b`.

The owner authorised one change to that check of selected functions.
The same test then returned zero with its necessary sentinel. Its JSON for the PASS result is
`tmp/phase7-platform-heading-coverage/qualified-matrix/owner-exception-phase3-rerun.json`, with SHA-256
`01de838be892437fc2070b9ac040ab24653612057c501d8b24a5b2dd7b29f21a`. Its command-output SHA-256 is
`239280a642d684db1c4c4351f89105c2f64ee61bf1ab3c087dda4d73f06b8f4c`.

That authorised change is completed. The decision gives no more project authority for repairs.
The two usual repairs are completed (2/2), and no more usual repairs are permitted.

Five subsequent FreeCAD tests had PASS results. The station-mapping test then
had a FAIL result because its check used 39 as the necessary number of caller identities.
The route has 40. The first command-output SHA-256 is
`1fa50614e86979ab50c174aa0c502ff51af26be3f057c54725720a5d5c162dd9`. The manifest stays INCOMPLETE at
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/manifest.json`, with SHA-256
`862b8515da16f06fde37e4205bc08068a6610f1041864ccd550954ed444eaa31`.

Its failure classification is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/station-mapping-failure-classification.json`, with SHA-256
`7e722fc25247193c3ee6381dc5d9e12c7f7d957d1ea47700ea2c16e5baed5e8a`. That record also identifies findings in the checks in the tests for
handedness and platform transitions. Inspection found those findings before the tests ran.
They were not results from those tests at that time.

The owner authorised changes from 39 to 40 in those three checks of caller identities.
The station-mapping test then had a FAIL result for a different cause.
Its check used `__globals__` for each selected caller.
The selected `_AlignmentProgressAdapter` has no `__globals__`.

The JSON for the FAIL result is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/owner-caller-count-station-rerun.json`, with SHA-256
`bb7b889ad278e78acf1ceba7b416b5893d6fcd0b107eef37350c474a76a342db`. Its command-output SHA-256 is
`22840d27bd4ee9e420d3eb022fb4ad10836a7b568fbc2a7711be3e88a3bfacf9`. The last failure classification records a `test-or-oracle-defect` at
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/station-adapter-failure-classification-final.json`, with SHA-256
`040077b71fb5fdb97b410c5a03b433efa6f3bb1e35e84eeaadb1330c12095f2e`.

It supersedes the first failure classification. That first record has SHA-256
`769ce6e1410b69fb46ee2419a6eb6cc72a94eeb6b3562be62d5e7f35f9f56e41`. The two records stay available. The three authorised changes
are completed. That owner decision did not authorise the subsequent change to the
check that used `__globals__` for each caller.

The owner then authorised a last 1/1 change to that caller check in the test.
The same station-mapping test returned zero with its necessary sentinel.
Its JSON for the PASS result is
`tmp/phase7-platform-heading-coverage/post-owner-qualified-matrix/owner-final-loop-station-rerun.json`, with SHA-256
`b7d5434481b3a874508ce8c83bcc470fd59eec6f30d937ca71317bb62e5d11e6`. Its command-output SHA-256 is
`85ed9348d35d84fd0a9ea4f9e6841c9d40df5a3c809c2f742aeedf61b4fdadc9`.

The last authorised change is completed. That decision gives no more project authority for repairs.
These owner decisions changed no product source. They did not change the
usual repair limit or its 2/2 status.

The remaining seven FreeCAD tests of the related routes then had PASS results.
The last manifest for all 14 tests has a PASS result at
`tmp/phase7-platform-heading-coverage/final-qualified-matrix/manifest.json`, with SHA-256
`6fce1acabef067633b22f9595ecf98271afd5c0f7928e21d880b56fac0ee19ce`. It contains the previous PASS results without a change,
the last station-mapping PASS result and the seven subsequent results.
Each test has its necessary sentinel. This result does not replace a
previous record with FAIL or INCOMPLETE status.

## Tests with the FreeCAD human interface

One isolated process with the FreeCAD human interface used the comparison baseline from protected `main`.
A second process used the exact candidate with the same exact host profile in D-GOV-019:
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2`.
The two tasks have PASS results, zero process exit status and their necessary sentinel.
The fixture for the two tasks has SHA-256
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`. The fixture did not change after each task.

The specified procedure uses `PLATFORM_CONSTANT` for a platform outside one
track. It compares Create and Edit through B16 Generate/Replace, Undo/Redo,
Save/reopen and cleanup. It also compares the two selected inputs that the product
rejects because of length or position. It records the first operation and three
subsequent operations of `calculate_platform_boundaries` with the same inputs.
The procedure is `tmp/phase7-platform-heading-coverage/gui-fixed-protocol.json`, with SHA-256
`a4db5a8c3a29e31a0d61ceffe5e4dec0c899ceb100edfd161ac2bca7b8f327a2`.

The product results are the same. The SHA-256 for the two results is
`35f77a72ad6a8b004b863d0a7241dad3bbc863ef4c317d482f8a755060c22230`. The equality check does not include the save path,
measured time or memory values. The full test has a PASS result at
`tmp/phase7-platform-heading-coverage/gui-full-comparison.json`, with SHA-256
`0cc4b3a10c474d88c0b44629ea6cd2cf998022241e40b672ee4a49cf26e03c4c`.

| Evidence | Comparison baseline SHA-256 | Exact candidate SHA-256 |
| --- | --- | --- |
| Source manifest | `5bf39bcbcadeb2c1f75e8ce3027c0f872d08ee2c2d454f9a3a2b3473c642121d` | `92f6528d5021a5b59e283a1856985b4398e966207f1c899989843017e5a83fcf` |
| Test JSON | `21a7880dfd4f6cad761c65a460630031b132ca94c65f14f586bafabae07a1177` | `98ca01c0d39850531cdd1f7f98e9135847d55eef8af751298ed8ce09eab8f9f9` |
| Full record | `8cd1c6e182d8b57e0ae9ea47974961c1e1a061ef8b5036a509bd17a36db7abd2` | `60bb31109a56405cf8e4200ef6099525442244eadd47d929e12323f7c0385ca5` |

The source manifests and test JSON files are in the ignored directory
`tmp/phase7-platform-heading-coverage/`. The full records are in
`benchmark-output/freecad-bridge/phase7-platform-heading-coverage/`, at
`baseline-attempt-01/run.json` and `candidate-attempt-01/run.json`.

This test includes only the named procedure with the FreeCAD human interface.
For other `coverage` values, a new comparison baseline and tests of the two routes
are necessary before a claim of equal results. The first and subsequent samples
give results for regression tests. One process for each route gives no improvement evidence for D-P6-008. It changes no measurement rule.

## Owner-view command invocation

One more owner-view check stopped before the test started its checks.
The command invocation did not supply the path that Python uses to get the test.
Its `ModuleNotFoundError` and specified command stay as evidence that gives no validation result,
in `tmp/phase7-platform-heading-coverage/owner-view-no-proof-receipt.json`, with SHA-256
`c437d697e89642159451f0ef441112e228696e26f173c74624833ada2807c8b2`.

The owner authorised the correction to the command invocation and one more test.
The same check then had a PASS result with the test directory on `PYTHONPATH`.
The check rejected all four owner views that the test made incorrect.
The JSON for that test is
`tmp/phase7-platform-heading-coverage/owner-view-corrected-invocation.json`, with SHA-256
`546607a182684056ce55680cd705c7fd8c55f12bcc1f05867f73ff67c59be5e4`.

This command correction changed no source or test. The two usual repairs are
complete (2/2). No more usual repairs are permitted. All changes in the
previous owner decisions are completed. Those decisions give no more project authority for repairs.

## Full validation profile

The full `transition` validation profile has a PASS result for all seven steps.
The full command outputs are in the ignored directory
`benchmark-output/validation-pipeline/20260926T214524822178Z/`. The pipeline command output is at
`tmp/phase7-platform-heading-coverage/complete-transition-profile.log`. This result includes the full validation profile for
standalone Python. It also includes the FreeCAD checks for transition persistence,
the scene and the Edit lifecycle.

## Remaining evidence

Publication makes independent review of source and tests necessary.
The validation results and the results from the FreeCAD human interface do not give that review result.
The Documentation Review lifecycle must also supply its necessary results.
This record claims no PASS result for those subsequent steps.
The applicable validation and review receipts record those results.

## Limits

This exact candidate does not compare all platform shapes, dimensions and positions,
other sets of alignments in Core or export bytes. It removes none of the paths that D-P7-001 keeps.
A memory value from one process for each route with the FreeCAD human interface gives no improvement evidence for D-P6-008.

Phase 7 stays Open at 0/4 with all exits Pending. Output stays at
private-development status and project status stays `unknown`.
D-P6-008 applies in full. D-P7-001 still gives this instruction: “Preserve all comparison and legacy-retirement conditions.”
