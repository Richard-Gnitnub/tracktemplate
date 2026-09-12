# Phase 7 evidence for calculated straight tracks

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-straight-route.md) define the supported inputs and results.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.
This record preserves work started on 2026-09-09 and completed on 2026-09-12 after an interruption.

## Scope and source

The implementing agent merged the authorised PR #72 head `dbd6a270d4a62b52b16f841b44c640d30f88da59` into protected main at `e6835a7c65ed7d516a18eb34ae55b9ae47cb653a`.
The merge CI had a PASS result. The primary worktree was clean and equal to protected main on GitHub.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result with authority from D-GOV-004 and the Phase 7 scope.

The B15 `build_straight_routes` caller used a complete function to calculate straight tracks that was missing from Core.
The candidate moves `build_straight_route` into `tracktemplate.domain.alignment` for `tracktemplate.api`.
The B16 Generate/Replace workflow uses the small `_StraightRouteAdapter` compatibility object.
It preserves the host's operations to copy `config`, supply missing values and use UUIDs. It creates only new result `App.Vector` values.

The API needs no FreeCAD or Qt value.
It receives only curve end points, counts, track direction values and the specified metadata.

The candidate preserves forward and reverse tracks on either side with no curve connection, and connections to curve entrances and exits.
It preserves units, operations to calculate results, diagnostics, metadata, identities and sequence.
The product selects eight functions together and puts all previous values back after a selection error.
B14, B15, the launcher, the frozen tools to compare results and all previous contracts stay unchanged.

The interrupted candidate is preserved at `5ae105e46294db2f1e37d8ab2b66fb4782efc6a2`.
The different commit `2f4eccdbce9d1e46f6e1050b1e18bed8c57663b3` corrects two specified historical test results after their classified failure.
The implementing agent froze all sixteen source, test and machine-contract files after that correction.
The new dated record also needs an exact check of the manifest date. That check changes no validation logic.

## Standalone and qualified FreeCAD proof

Before the source changed, 117 complete B14/B15 cases gave equal results.
The checks preserve `config` values, UUID operations, operations to copy inputs, `App.Vector` creation, result sequence and diagnostics.
They include disabled `config` values, invalid inputs, track counts and changed `rotation_degrees` values.
They include tracks with and without curve connections.

Nine selected test sets with standalone Python had PASS results.
They include Phase 1 straight tracks and station values, Phase 2 foundation, Phase 3 routing, and Phase 4 route removal.
The Phase 7 sets include the main centre, exit end point, complete core, common extensions and newly calculated straight tracks.
The new set checks all 117 complete results, necessary mathematical relations and the actual caller's selected functions.
It checks that the API has no host dependency and rejects incorrect function selection with previous values intact.

Python accepted the changed source and tests. Their Ruff checks had PASS results.

Six proofs with qualified FreeCAD had PASS results, each with process exit status `0` and its necessary success sentinel.
They include straight tracks, the main centre, exit end point, complete core, common extensions and the Phase 3 caller.
The new proof uses actual `App.Vector` values for 120 cases and the actual `build_straight_routes` caller.
The three extra cases use generated main, parallel and platform curve records.
The proof checks complete results, input identities and recovery after incorrect function selection.

The qualified host profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The development tool is `.devtools/freecad-cli` at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`, with its six approved patches unchanged.
The final checks preserve all 123 candidate paths and 105 baseline paths in their source records.
They also preserve the fixture and preferences.

## Human-interface proof

The fixed plan uses three samples with no curve connection and three connected samples for each state.
The three connected baseline samples are preserved PR #72 results with the exact accepted product source.
The tool completed the three baseline samples with no curve connection before the interruption.
It did not do a completed baseline sample again.
All six candidate samples had PASS results in different FreeCAD processes on September 12.
All twelve checks of complete result data give equal results, with no differences.

The samples with no curve connection use the actual **Add independent straight** operation for two reverse tracks on the right side.
They change the length from 100 mm to 150 mm, with `rotation_degrees` at 90 degrees and start XY values at (10, 20) mm.
The distance between tracks is 50 mm, the width is 32 mm, and the thickness is 1 mm.
The connected samples create and edit entrance and exit extensions through the actual B16 workflow.

The checks include metadata, object sequence, identities, station values, replacement, Undo/Redo and persistence of document copies.
The samples with no curve connection reject a `config` without outputs before they remove objects.
They also cause a test error after removal and validate recovery of the previous document state and history.
The inherited Undo/Redo procedure takes three steps. This is not acceptance of a single subsequent transaction to do all those operations together.
The checks do not prove equal complete B-rep or export bytes.

The table gives the median and [minimum, maximum] for three samples in each state.
Wall and CPU values use milliseconds. RSS changes use MiB. Object values are counts.

| Action | State | Wall ms | CPU ms | RSS change MiB | Object change |
| --- | --- | --- | --- | --- | --- |
| Connected create | baseline | 13469.851 [13464.719, 13472.737] | 2538.318 [2505.118, 2545.670] | 164.195 [164.145, 170.504] | 14 |
| Connected create | candidate | 13145.772 [12541.037, 13462.611] | 2532.860 [2493.718, 2553.496] | 165.145 [136.066, 172.828] | 14 |
| Connected edit | baseline | 13180.507 [13175.905, 13182.525] | 2190.195 [2170.399, 2207.225] | 57.070 [56.910, 63.883] | 0 |
| Connected edit | candidate | 13178.456 [13177.141, 13178.907] | 2204.426 [2194.536, 2212.870] | 63.973 [63.555, 64.527] | 0 |
| Create with no curve connection | baseline | 13474.868 [12541.488, 13480.904] | 2456.848 [2455.671, 2478.650] | 184.043 [177.652, 185.164] | 8 |
| Create with no curve connection | candidate | 13471.856 [13463.624, 13473.307] | 2502.267 [2464.102, 2510.596] | 179.340 [170.180, 182.383] | 8 |
| Edit with no curve connection | baseline | 13168.854 [13167.275, 13170.242] | 2171.989 [2156.228, 2180.981] | 60.355 [56.172, 60.652] | 0 |
| Edit with no curve connection | candidate | 13162.912 [13162.677, 13163.585] | 2137.179 [2113.780, 2184.994] | 54.742 [49.488, 55.234] | 0 |
| Reject with no curve connection | baseline | 2165.205 [2163.683, 3167.544] | 207.773 [204.304, 213.813] | 0.363 [0.363, 0.363] | 0 |
| Reject with no curve connection | candidate | 3163.154 [2199.295, 3163.543] | 212.190 [206.942, 217.786] | 0.414 [0.414, 0.418] | 0 |
| Stop with no curve connection | baseline | 2165.977 [2165.170, 2171.309] | 439.103 [435.221, 441.722] | 0.699 [0.648, 0.828] | 0 |
| Stop with no curve connection | candidate | 2162.928 [2162.688, 2168.666] | 432.508 [431.243, 439.885] | 0.641 [0.637, 0.695] | 0 |

The candidate's connected-edit median RSS change is higher by 6.902 MiB, or 12.09%.
When the samples with no curve connection reject an input, median wall time is higher by 997.949 ms, or 46.09%.
For that action, the CPU median is higher by 4.417 ms and the RSS change median by 0.051 MiB.
For Create with no curve connection, the CPU median is higher by 45.419 ms.
These higher results stay limitations. This task does not show their cause.

The preserved baseline starts are before candidate starts by about 80.5 hours without curve connections and 87.7 hours with connections.
The exact gaps are 289,797.581–289,852.925 seconds and 315,674.897–315,731.695 seconds, respectively.
The host profile and inputs stay unchanged, but the tests did not control which file data the operating system kept.
These descriptive samples do not show that source changes caused the measured differences or that results are within accepted product performance limits.

## Direct cost

The fixed direct plan uses six pairs on September 12. The sequence of baseline and candidate changes between pairs.
Each state starts in a new FreeCADCmd process and uses ten cases.
The cases without curve connections include directions, sides, counts and `rotation_degrees` values.
Other cases include entrance and exit connections, disabled `config` inputs and output of centrelines only.
The two actual curve inputs contain 516 and 534 points.

Each process first measures one group of ten cases, then does that group 100 times with new input Python objects.
This gives 60 operations in initial groups and 6,000 subsequent operations per state.
The initial group contains the first ten cases in a new process.
It does not imply that the operating system kept no file data before the measurement.
Subsequent operations calculate new results. The product keeps no previous result for subsequent use.

The timer includes the actual host `build_straight_route` operation, copies of `config`, replacement of missing values, UUID work and all calculated results.
It includes all new `App.Vector` values.
Input preparation and checks of correct results occur before or after timing and use the same procedure for both states.
Every complete result in the initial groups has equal values in the same sequence.
Every hash of a result from an initial or subsequent group matches exactly.
Input values, Python object identities and `App.Vector` identities stay unchanged.

The table gives the median and [minimum, maximum] for six samples per state.
Values are microseconds per operation: total time divided by the number of operations across the ten-case group.
They do not describe each `config` individually.

| Measurement | Baseline microseconds | Candidate microseconds |
| --- | --- | --- |
| Initial group, wall | 35.126 [33.244, 39.180] | 33.375 [31.907, 35.942] |
| Initial group, CPU | 34.777 [32.873, 38.831] | 33.043 [31.575, 35.617] |
| Subsequent new inputs, wall | 23.967 [23.594, 24.435] | 21.587 [21.016, 22.732] |
| Subsequent new inputs, CPU | 23.959 [23.590, 24.430] | 21.569 [21.012, 22.727] |

The measured wall median is lower by 1.751 microseconds per initial-group operation and 2.380 microseconds per subsequent operation.
The initial-group RSS change is zero in every sample.
For subsequent operations, the median RSS change is 0.242 MiB in the baseline and 0.178 MiB in the candidate.
The candidate's median absolute RSS after subsequent operations is higher: 234.861 MiB compared with 232.832 MiB.
The maximum memory value does not increase during either measured group in either state.
These process measurements include runtime effects and do not show that source changes caused the memory differences.

These results give no product performance acceptance, guarantee of GUI time or guarantee of output.
The preserved PR #72 common-extension cost stays about 1.25 microseconds per input group, or 25.33% added wall cost.
D-P6-008 stays a different, unmet obligation. This task changes no measurement profile or comparison rule and does no stopped experiment again.

## Preserved failures and review

The first test tried to set a value on the frozen `B15WorkflowHost` object and gave `FrozenInstanceError`.
The primary failure classification is `fixture-or-harness-defect`.
The first repair changes the host type only during the test and keeps the same check that prevents use of `bind_transition_functions`.
Product source did not change. The initial proof then had a PASS result for all 117 cases.

Two historical tests then checked for the new caller in their earlier schema 2 and schema 3 contracts.
Both gave errors at `caller_names`.
The qualified centre proof also had a FAIL result with no success sentinel, although its process exit status was `0`.
The primary failure classification is `test-or-oracle-defect`, with an independent review of that classification.

The second repair removes only those two incorrect checks of historical results.
The product's schema 6, its eight functions and all checks of its callers stay unchanged.
The two initial proofs with standalone Python and the initial qualified centre proof then had PASS results.
The task used both permitted source/test repairs. No further repair is authorised.

The initial failures, initial candidate, different repair commit and all earlier verdicts stay preserved.
The missing local STE source/cache and missing local Ruff path were environment defects.
The implementing agent corrected them without source changes.
A command selected a foundation test that did not exist. The Phase 2 foundation proof then had a PASS result.
That command error is a `fixture-or-harness-defect` and changed no preserved test.

The interruption in agent usage from September 9 to September 12 was external to the product.
No candidate GUI or direct measurement had a FAIL result, and the tests replaced no measurement sample.

The independent read-only review of source, tests and raw evidence has a PASS result with no findings that need action.
The reviewer wrote none of the product source or tests in this task.
The reviewer had earlier API and architecture design context. This record identifies that familiarity.

The review includes the sixteen frozen files and the directly dependent check of the exact date.
It validates 166 receipt and script hashes and 24 raw records. That review does not include canonical prose.

## Limits and preservation

This task supplies evidence for the bounded scope in Phase 7 Exits 3, 2 and 1.
The evidence concerns the API with no FreeCAD or Qt dependency, equal results and the B16 workflow, respectively.
Phase 7 stays Open at 0/4 with all four exits Pending. This task accepts no exit.
D-P6-008 stays in full, including the mandatory acceptance boundary before Phase 10 beta.
All conditions to compare results and remove legacy paths stay in full.

Project status stays `unknown`. Output keeps private-development status. No release or wider migration claim is accepted.

The task does not migrate functions that calculate station values, change turn direction or build platforms.
It does not migrate `config` schemas or output functions.
It does not claim the same error sequence for other Python types, incorrect point objects or combined test errors after it collects curve data.

After all measurements, a different FreeCAD process opened disposable copies of completed candidate documents for two top-view images.
The view with no curve connection shows two different vertical straight tracks beside the unchanged curves.
The connected view shows straight extensions at the curve entrances and exits.
The validator and implementing agent examined both images and found no visible defect at the shown scale.

The images show document copies, not what a person sees on the workstation screen.
The tool did no product operation or file-write operation again.
Source and copy hashes stay unchanged, and all FreeCAD processes closed.
No action at the workstation is necessary to complete this task.

## Local proof identities

Raw proof stays in `tmp/phase7-straight-route/`. Git does not include it.
Images stay in `benchmark-output/freecad-bridge/phase7-straight-route-visual/`.
The terminal receipt records the complete raw file identities, protocol, guarded source, fixture and preferences.

| Local record | SHA-256 |
| --- | --- |
| `implementation-prechange-characterization-complete.json` | `39d11f76f71da1030ffeeeb4f588f5396d86c89437abe90d39947186cccd3aab` |
| `implementation-failure-01-before-repair.json` | `b543a9e7dfb3d32aaef973814b1ce94810593f0b9a100621765cbdf5389a2cbb` |
| `repair-02-adjudication-2026-09-12.json` | `9162cd13b7842cfc00c808c7f9c5a45453f6c3169279b99c781b01699a9a24f6` |
| `implementation-final-freeze-2026-09-12.json` | `d14a4d26ad89f2cb1fc2a653f1c1c799ab740a23ce7366e10bc64457fd39efe9` |
| `validation-reconciled-2026-09-12.json` | `12edf86c6b52f65880396fbdff6fefe6f51ebee415633db23a9738404805d82a` |
| `host-protocol.json` | `71d5062900ef1a00a8862120ea09cfe9696d9c7c4c726999d46407330a4aa854` |
| `host-direct-plan.json` | `81d97d059b4e311b887555fbf24a2cce1be22326ff04579a0edb2786d0ee704f` |
| `host-completion-receipt.json` | `8aa77c139cf4fef70c422d481143f553b1fa7058b6cf629e034dce342ff80d44` |
| `host-gui-comparison.json` | `ddbe2e21108ed52a99dc137f176740af7aadf974213419aa572d681c00694343` |
| `host-direct-summary.json` | `57e17fcfbccdaa8fa229f20f508a032e215cd9dc8d0481fae428dd70474aae33` |
| `independent-quality-review-2026-09-12.md` | `2b78fd4fac907a53d11cb7ca61ebe333190bc495a8e348f7aca8a1b3839296f9` |

The completed backup set is `2026-09-09-post-pr72-pre-phase7-next-01`.
It preserves the twelve project roots that were present at that time, including valuable evidence in sibling worktrees.
Its checks had PASS results and preserved all prior snapshots. The agent used the accepted September 5 restore proof again.
The backup terminal receipt SHA-256 is `d380e523704ae69c5141d9120ed1dada7f108f08ea9e406a577baba49f1c84b7`.

The operating system safely disconnected the backup device's file system. No evidence shows that a person removed the device.
This backup device is not the source device.

The implementing agent created the new candidate worktree after that snapshot. Its local evidence stays in that worktree.
