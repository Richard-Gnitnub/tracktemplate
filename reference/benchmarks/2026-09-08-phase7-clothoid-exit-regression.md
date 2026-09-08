# Phase 7 `clothoid_exit_displacement` evidence

Status: **Evidence for one bounded Level 2 migration.
No acceptance of product performance or a phase exit.**

## Scope and method

The comparison baseline is protected main
`8b06de6bff3901e35548a1be79ebe9f68bb4fc57`, after the merge of PR #69.
It selects four functions from `tracktemplate.api`.
The exact candidate adds `clothoid_exit_displacement` and selects five functions.
The product caller `build_concentric_core` uses the new API for its endpoint calculation.
The [API instructions](../contracts/phase7-clothoid-exit.md) define the bounded scope.

Both routes use the qualified host profile
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
Each sample starts a new isolated FreeCAD process with a copy of the same fixture.
The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The two routes start with the same bytes in `user.cfg` and `system.cfg`.
The tests do not control data that the operating system keeps after it reads files.

The same `run_phase3_transition_workflow.py` tool supplies two workflows.
The comparison baseline and exact candidate both use `--route modular`.
Each workflow has three samples for each route.
The fixed sequence puts all six baseline samples before the six candidate samples.

In each group, `plain-line-edit` comes before `connected-straight` three times.
This sequence limits conclusions about effects of the exact candidate.
The JSON data keep the sequence, dates and values for each sample.

The two completed samples with `--route legacy` from PR #69 supply evidence for these checks.
Their source, fixture, profile and workflow tools have the same identities.
The tests compare their results with the new samples. The tests do not use their times.
This task does not do these two samples again.

The same tool measures two operations for each workflow.
The first uses a new process and the copied fixture.
The second calculates another result in the same process after the first operation.
These measurements do not include the time to start FreeCAD, open the fixture and do the subsequent checks.
The same-process operation is not evidence for warm reuse.
This API keeps no result for reuse.

## Calculated results and caller results

Before source movement, the B14 and B15 functions gave the same results for 440 input cases.
Ten checks with `radius <= 0.0` also gave PASS results for each source.
The exact candidate gives equal results with the same sequence of operations.

A separate check uses the entry result to calculate `expected_x = entry_x * cos(angle) + entry_y * sin(angle)`.
It also calculates `expected_y = entry_x * sin(angle) - entry_y * cos(angle)`.
These are the same operations as the test's reflection and rotation.
The check keeps `abs(dx - expected_x) <= 1.0e-9` and `abs(dy - expected_y) <= 1.0e-9`.

Seven selected groups of tests with standalone Python have PASS results.
The source check reports `All 9 changed Python files parsed successfully`. Ruff gave a PASS result.
Three qualified FreeCAD tests have process exit status 0 and the necessary sentinels.
Their calculated results and product caller results are equal for `main_alignment`, `match_alignment` and `manual_alignment`.

The new test shows that each of those three caller cases uses the selected exit API one time.
It also shows recovery after an invalid exit function in the caller.
The centre and Phase 3 tests also have PASS results.

## Calculate results again

CPython 3.12.3 measured six samples for each API after the FreeCAD processes stopped.
Each subsequent pair changes the API that starts first.
Each sample calculates 1,800 results: 50 times for each of 36 input pairs with values of zero or more.
Each calculated result must be the same as B15. The value for `integration_steps` is 240.

These measurements examine the API in one process. They do not measure the full FreeCAD workflow.
All values for each sample stay in the JSON data.

| Measured quantity | `baseline` median (range), ms | `candidate` median (range), ms | Change |
| --- | ---: | ---: | ---: |
| `wall_ms` | 56.636 (56.045–57.385) | 57.026 (56.267–57.589) | +0.391 (+0.690%) |
| `process_cpu_ms` | 56.627 (56.041–57.382) | 57.024 (56.263–57.579) | +0.397 (+0.701%) |

The candidate medians are higher. The ranges include common values.
These results do not show equal or better product performance.

## FreeCAD workflow results

All twelve new samples completed with process exit status 0 and the necessary sentinel.
Their source files, fixture and initial `user.cfg` and `system.cfg` files kept the same identities.
Each sample records `cleanup.remaining: []`. All launched FreeCAD processes stopped.
The tests compared the full workflow results for the twelve new samples and the two preserved samples with `--route legacy`.
All these results are equal.

The new samples completed on 2026-09-08 from approximately `20:14` to `20:27` UTC.
There were 15.749 seconds between the last baseline sample and the first candidate sample.
The sequence and data from the operating system limit conclusions about effects of the exact candidate.
The tests do not control those data.
No GUI sample gave a FAIL result. All twelve GUI samples are the initial samples.

### Time for each operation

Values are milliseconds. Change is the candidate median minus the baseline median.
The percentage uses the baseline median.

| Operation | Measured quantity | `baseline` median (range) | `candidate` median (range) | Change |
| --- | --- | ---: | ---: | ---: |
| Replace the left curve with the right curve | `wall_ms` | 14012.388 (13990.414–14136.128) | 14008.870 (13996.738–14010.248) | -3.518 (-0.025%) |
| Replace the left curve with the right curve | `process_cpu_ms` | 2802.275 (2715.541–2812.172) | 2784.648 (2780.225–2798.886) | -17.626 (-0.629%) |
| Replace the right curve with the left curve | `wall_ms` | 13158.356 (13155.085–13162.093) | 13152.361 (13150.175–13157.839) | -5.994 (-0.046%) |
| Replace the right curve with the left curve | `process_cpu_ms` | 2093.338 (2082.392–2126.846) | 2102.422 (2100.399–2118.414) | +9.084 (+0.434%) |
| Make the connected pair | `wall_ms` | 13466.284 (12470.335–13468.390) | 13469.298 (13463.217–13473.184) | +3.014 (+0.022%) |
| Make the connected pair | `process_cpu_ms` | 2493.375 (2474.369–2546.066) | 2542.661 (2522.942–2574.839) | +49.285 (+1.977%) |
| Change the lengths of the connected pair | `wall_ms` | 13183.664 (13177.573–13187.828) | 13180.336 (13176.323–13183.188) | -3.327 (-0.025%) |
| Change the lengths of the connected pair | `process_cpu_ms` | 2202.825 (2159.155–2260.749) | 2179.277 (2171.672–2270.924) | -23.549 (-1.069%) |

The `wall_ms` values are equivalent to approximately 12–14 seconds.
The `process_cpu_ms` values are equivalent to approximately 2–3 seconds.
The cause of this difference is unknown. The difference occurs in both routes.

### Memory and objects

Memory values use MiB. The tool stores them in `rss_delta_mb`.

| Operation | `baseline` median (range) | `candidate` median (range) | Median change |
| --- | ---: | ---: | ---: |
| Replace the left curve with the right curve | 264.484 (216.395–269.359) | 216.086 (212.219–262.887) | -48.398 (-18.299%) |
| Replace the right curve with the left curve | 45.836 (-1.332–62.324) | 57.746 (51.113–58.824) | +11.910 (+25.984%) |
| Make the connected pair | 168.188 (164.266–171.023) | 170.414 (136.402–171.844) | +2.227 (+1.324%) |
| Change the lengths of the connected pair | 64.164 (57.785–64.406) | 57.742 (56.676–58.137) | -6.422 (-10.009%) |

The second Replace operation has a higher candidate median memory increase: 11.910 MiB (25.984%).
Its baseline values include a decrease of 1.332 MiB. All values stay in the evidence.
The ranges for each measured time and memory quantity include common values.
These values do not show equal product performance. Worse product performance is possible.

Each operation that makes the connected pair adds 14 objects.
The number of objects stays the same for the other measured operations in either route.

## Preserved failures and limitations

Two tests with standalone Python initially had checks for the previous current product route.
They gave FAIL results when the product route changed from four selected functions to five.
Before repair, their failure class was `test-or-oracle-defect`.
The agent changed only the checks for the current product route and their directly dependent test fixtures.
The same tests then gave PASS results. The previous API data and checks of calculated results stay the same.

The first summary for standalone Python identifies a previous version of the new exit test.
The subsequent test gave a PASS result after the last test-fixture adjustment.
A subsequent evidence record connects that test to the frozen test file.
The same tool recorded the source hashes for that test.
The agent made this evidence record after the test. The previous evidence record stays available.

The temporary tool that assembled the completion record initially checked for twelve different values for `process_id`.
Each isolated process reported `2`. Those values cannot distinguish the twelve isolated instances.
Before repair, the failure class was `fixture-or-harness-defect`.

The corrected check uses the twelve different instance identities from the launcher.
The previous evidence files show that each exact instance stopped.
The initial check with its FAIL result stays available.
This repair did not do a GUI workflow again.

The development-toolchain preflight initially rejected a symbolic link to the official PDF in the new worktree.
The author copied the exact official file locally, and the tool made a new local derived cache.
The same development-toolchain preflight then gave a PASS result.
The author did not start the technical documents until that PASS result.
The initial symbolic links and failure classification stay available.
No maintained tool, source identity or writing rule changed.

The previous PR #69 record keeps its different `wall_ms` values between dates and its higher candidate memory value.
This new evidence does not remove those limitations.

The same workflow tests compare canonical railway state, identities, sequence, metadata, Undo/Redo and shapes.
They also compare recovery after an error and files that FreeCAD opens again.
These checks do not show that full shapes or output bytes are equal.
There is no new image from the FreeCAD human interface. No person examined the physical display for this evidence.
The same tools operated the FreeCAD human interface to get this evidence.

This task gives no D-P6-008 acceptance credit and repeats no stopped experiment.
The full deferred obligation stays mandatory before Phase 10 beta acceptance.
All paths for these tests and all conditions for removal of the B14 and B15 routes stay in full.
Phase 7 stays Open at 0/4. Output stays private-development and project status stays `unknown`.

## Independent review and evidence files

The independent review of source, tests and raw evidence has a PASS result for this bounded scope.
It found no finding that prevents publication.
It kept the time and memory limitations.
It also kept the fact that the agent connected the test result to the source hashes after the test.
This review gives no phase exit or product performance acceptance.

The local evidence files below are in `tmp/phase7-clothoid-exit/`.
The GUI summary identifies every sample, each value and the results from the tests that compare workflows.
The host evidence record connects the commands, necessary sentinels, raw files and last preservation checks.
The frozen source manifest identifies all ten implementation files.

| Evidence file | SHA-256 |
| --- | --- |
| `legacy-characterization.json` | `29ec268a5af72b2c5bf2ea7479bb70fa8184b44015890eff4528c487434054d4` |
| `implementation-frozen-sha256.json` | `b8e04b791e40fec64afac5f4433d862a0a0149349271d24f5e374f948953748e` |
| `standalone-final-receipt.json` | `688d6f64ab15d1f02d4a5b406391de2c56dff592c3cef75c78e9fbd3125e5605` |
| `validate_phase7_clothoid_exit-final-fixture-supplemental-receipt.json` | `c19683ddcbb04e28faac3a85d9c723b7808f216c4546049d2a2ea864212ca1ba` |
| `gui-regression-summary.json` | `d4c2d80fbb9efdef592f5fe7c0ff48fbd4c581668cfeb3e156b45e46f031b227` |
| `host-completion-receipt.json` | `481d8505f6fcf429f4177443a696298113ecac7b4f3da6da9027def8a0c5adb0` |
| `repeated-exit-result.json` | `02db6bfb80bf2b524aec8cc1e9099c5a0600111d76bc813085c39ac428097c15` |
| `quality-review.md` | `e6ca3ad57a7b4a2cfd598d96e3a6786d185993fedd39b6d3fa1ecc2140c8edfc` |
