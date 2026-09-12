# Phase 7 evidence for station values and points

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-station-mapping.md) define the supported inputs and results.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

The implementing agent merged the authorised PR #74 head `bc71deb1eac8bffe1403c206b28f030fddb2fb6f` into protected main at `6ebd16f740544325c55d9e5889fa0fb9e476e19d`.
CI for the merge had a PASS result. The primary worktree was clean and equal to protected main on GitHub.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result with authority from D-GOV-004 and the Phase 7 scope.

The station functions `alignment_station_data` and `interpolate_alignment_station` were missing from Core.
They now use `tracktemplate.domain.alignment` through `tracktemplate.api`.
The small compatibility objects keep operations to read host points, create points and calculate track direction in their initial sequence.
The API uses no FreeCAD or Qt value. It keeps no calculated result for subsequent use.

The product selects ten functions together and validates 38 actual caller routes.
The station pair has 15 and 30 caller functions, respectively, with 34 different callers in total.
The checks include the actual crossover panel method and the function for points at stations defined inside another function.
They validate each selected function, the specified compatibility types and `App.Vector`.
A selection error puts all previous values back. It removes a new value when there was no previous value.

B14, B15, the launcher, earlier machine contracts and the frozen tools to compare results stay unchanged.
The twelve changed earlier tests preserve their historical contract checks and examine the selected ten functions in different checks.
Two new tests supply the complete station proof with standalone Python and qualified FreeCAD.

Before product work, the recovery workflow completed snapshot `2026-09-12-post-pr74-pre-phase7-next-01` at the destination for approved independent preservation.
The snapshot contains 14 roots and 16,444 files. All checks that compare hashes and examine source had PASS results.
It preserves all 59 previous destination entries. The completed recovery evidence from September 5 stays applicable.

The implementing agent created the new station worktree after the snapshot. The snapshot does not contain the new candidate or its subsequent evidence.
The backup receipt records completed operations to write data to the device and disconnect its file system safely.
No evidence shows physical disconnection or the PyCharm window on the workstation screen.
No operation at the workstation was necessary for development from a different location.

## Calculation and caller proof

Before the product source changed, the complete B14/B15 station proof had a PASS result.
It compares all seven station-data items, point identities, copied Python `list` objects, numerical limits, points at the same position, errors and operation sequence.
The candidate gives the same complete results within that scope.
The checks include operations to read input objects, create points before final angle calculation and combine errors.
The `AlignmentStationInterpolation` result cannot change. When the caller reads its `heading` property, the API calculates the initial expression.

Twelve selected earlier test sets with standalone Python and the new station test have PASS results.
They include Phase 1 alignment, straight tracks and station values, Phase 2 foundation, Phase 3 routing and workflows, and Phase 4 route removal.
They also include all five previous Phase 7 calculations and routing results.
Python accepted the changed source and tests. Their Ruff checks have PASS results.
All eighteen previous domain function definitions stay unchanged.

Seven proofs with qualified FreeCAD have PASS results, each with process exit status `0` and its necessary success sentinel.
They include the Phase 3 caller, all five previous Phase 7 functions and the new station pair.
The new proof with FreeCAD includes eleven actual generated main, parallel, platform and straight alignment records.
It compares complete values, initial point identities and actual `App.Vector` results.

The qualified host profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The host uses FreeCAD 1.1.3, Python 3.13.13, Qt/PySide 6.11.1 and OCCT 7.8.1.
The development tool is `.devtools/freecad-cli` at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`, with its six approved patches unchanged.
Standalone checks use Python 3.12.3 and Ruff 0.16.4.

The actual caller checks use three operations for each of four groups in each state.
All twelve checks give equal complete results in the same sequence, with equal operation counts and input point counts.
Python `sys.setprofile` counts the operations during these measurements. Their times include those counting operations.
Their differences do not show costs for a workflow without those operations.

The following tables give medians and [minimum, maximum] for three samples per state. Time values use milliseconds.

| Caller group | Baseline median [minimum, maximum], ms | Candidate median [minimum, maximum], ms | Difference of medians, ms | Change from baseline median, % |
| --- | --- | --- | --- | --- |
| straight-production | 187.045592 [180.948185, 214.143497] | 186.547897 [180.513500, 191.845554] | -0.497695 | -0.266082 |
| platform-sectioning | 556.435973 [554.535030, 556.526144] | 1002.546327 [993.978898, 1007.600370] | +446.110354 | +80.172810 |
| turnout-mapping | 46.455429 [46.400845, 46.634639] | 52.604956 [51.975140, 54.488726] | +6.149527 | +13.237478 |
| crossover-feasibility | 35535.122579 [35349.841101, 35548.574856] | 36044.561824 [35987.290397, 36124.628753] | +509.439245 | +1.433622 |

The following table gives CPU values with the same units and sample counts.

| Caller group | Baseline median [minimum, maximum], ms | Candidate median [minimum, maximum], ms | Difference of medians, ms | Change from baseline median, % |
| --- | --- | --- | --- | --- |
| straight-production | 414.068540 [413.794983, 423.253239] | 417.027814 [416.393537, 417.899975] | +2.959274 | +0.714682 |
| platform-sectioning | 559.958230 [559.411091, 560.255328] | 1006.177616 [998.344789, 1011.624233] | +446.219386 | +79.687977 |
| turnout-mapping | 46.449646 [46.387881, 46.619545] | 52.606562 [51.976090, 54.491366] | +6.156916 | +13.255033 |
| crossover-feasibility | 35529.860690 [35345.261301, 35542.835221] | 36033.751858 [35979.681864, 36120.333666] | +503.891168 | +1.418219 |

| Caller group | Operations to calculate station data | Operations to calculate points at stations | Measured point counts | Result |
| --- | --- | --- | --- | --- |
| straight-production | 39 | 45 | 2 | Equal in all three related candidate operations |
| platform-sectioning | 25 | 32372 | 518, 620 | Equal in all three related candidate operations |
| turnout-mapping | 1 | 314 | 773 | Equal in all three related candidate operations |
| crossover-feasibility | 8 | 59322 | 773, 815 | Equal in all three related candidate operations |

The platform wall median is higher by 446.110 ms, or 80.17%. The turnout wall median is higher by 6.150 ms, or 13.24%.
The crossover wall median is higher by 509.439 ms, or 1.43%. These measurements stay visible limitations and include the counting operations.

## Human-interface proof

The fixed plan supplies five new samples across three cases: a plain-line pair, one connected-straight candidate and a platform-sectioning pair.
The connected baseline is the preserved PR #73 candidate with the same current product source to compare results.
All 105 selected runtime, bridge and recipe paths match protected main before extraction.
The implementing agent checked the source, qualified host profile, fixture and preferences before it used the baseline again.
It did not do a completed baseline sample again.

All five planned samples have PASS results. The connected case also has one preserved attempt with a different name for the document copy.
The next attempt uses the unchanged earlier tool and the earlier name.
All three final checks give equal complete workflow data, with no differences.
Each new workflow uses a different isolated FreeCAD process and a disposable document copy.

Plain-line and connected-straight samples use actual B16 Generate/Replace operations and their earlier edit, recovery and persistence checks.

The platform case starts with the two-track curve fixture and one enabled outside platform.
Its main curve uses a 600 mm radius, 600 mm transitions, 90 degrees and 32 mm width.
The platform length changes from 250 mm to 300 mm with `entry_taper_length` and `exit_taper_length` at 50 mm and the unchanged 2D face output.

The tool divides the output into sections with 600 mm maximum and 100 mm minimum lengths.
It balances section lengths and gives numbers in travel sequence.
The geometry before division stays present. The `formation` input, assembly and export are disabled.

The check of platform results includes complete initial, generated and edited records, platform roles, section numbers, geometry and metadata.
It includes history records between operations, two complete Undo/Redo cycles, persistence and recovery of preferences.
The earlier Undo/Redo procedure takes three steps. This task does not claim a single transaction for those operations.
The check excludes only the specified time, resource and path items that can change between operations. It keeps the complete product data.

These are descriptive samples, with one final sample per state and case.
They do not show typical human-interface performance or a numerical acceptance limit.
They do not prove equal complete B-rep or export bytes.
Turnout and crossover evidence comes from their actual calculation callers. This task adds no complete human-interface lifecycle proof for those groups of functions.

After all measurements, a different isolated FreeCAD process opened new disposable copies of the three completed candidate documents.
The Technical Lead inspected all three top-view images from the unchanged bridge API.

The plain-line view shows two different curved faces and coloured centrelines.
The connected view shows continuous tracks with straight extensions at both ends.
The platform view shows the ends of track sections and a different outside platform face.
The source documents and copies kept the same bytes. The process closed without file-write operations or product operations.

The images are in the active worktree's ignored `benchmark-output/freecad-bridge/phase7-station-mapping-visual/` directory.
Their names are `plain-line-top-view.png`, `connected-top-view.png` and `platform-sectioning-top-view.png`.
They show examples of geometry. They do not prove output clearance or complete equality of shapes.

The following table keeps all eighteen case measurements, with the initial connected attempt that had the incorrect name.
Wall and CPU values use milliseconds. RSS changes use MiB. Object changes are counts.

| Action | State | Wall ms | CPU ms | RSS change MiB | Object change |
| --- | --- | --- | --- | --- | --- |
| Replace left with right | plain-line baseline | 14103.206 | 2786.916 | 217.059 | 0 |
| Change right back to left | plain-line baseline | 13151.138 | 2072.673 | 50.750 | 0 |
| Reject zero angle | plain-line baseline | 2181.833 | 187.758 | 4.102 | 0 |
| Stop replacement | plain-line baseline | 2151.772 | 395.538 | 0.504 | 0 |
| Replace left with right | plain-line candidate | 13997.100 | 2787.834 | 212.707 | 0 |
| Change right back to left | plain-line candidate | 13152.117 | 2030.676 | 51.332 | 0 |
| Reject zero angle | plain-line candidate | 3140.492 | 191.479 | 0.102 | 0 |
| Stop replacement | plain-line candidate | 3159.697 | 408.289 | 4.457 | 0 |
| Create connected pair | connected baseline | 13145.772 | 2553.496 | 172.828 | 14 |
| Edit connected lengths | connected baseline | 13178.907 | 2204.426 | 63.973 | 0 |
| Create connected pair | connected initial name mismatch | 13464.205 | 2519.232 | 171.961 | 14 |
| Edit connected lengths | connected initial name mismatch | 13181.904 | 2195.705 | 57.262 | 0 |
| Create connected pair | connected corrected name | 13454.307 | 2514.880 | 138.055 | 14 |
| Edit connected lengths | connected corrected name | 13177.385 | 2164.101 | 58.500 | 0 |
| Create platform and sections | platform baseline | 19382.559 | 15824.289 | 413.375 | 23 |
| Edit platform length | platform baseline | 18972.479 | 15351.329 | 195.254 | 0 |
| Create platform and sections | platform candidate | 19372.684 | 15693.847 | 401.738 | 23 |
| Edit platform length | platform candidate | 19021.378 | 15250.359 | 202.156 | 0 |

Plain-line rejection wall time is higher by 958.659 ms. Its CPU time is higher by 3.721 ms.
Plain-line replacement recovery wall time is higher by 1,007.925 ms, with CPU time higher by 12.751 ms and RSS change higher by 3.953 MiB.
Platform edit wall time is higher by 48.899 ms and RSS change by 6.902 MiB, although CPU time is lower.

These measurements stay limitations. Their causes are unknown. This task does not claim a source cause from one sample.

The baseline starts are before the final candidate starts by 73.313387 seconds for plain line and 112.003936 seconds for the platform case.
The preserved connected baseline is before its final candidate by 10,056.798315 seconds, or about 2.79 hours.
The tests did not control which file data the operating system kept. Later edits use the same process and calculate new results.
The terminal receipt keeps all 164 resource measurements, with history and persistence operations.

Some measured intervals contain other measured intervals. Do not add their time values together.

## Direct cost

The fixed direct plan uses six pairs. The sequence of baseline and candidate changes between pairs.
Each state starts in a new FreeCADCmd process. Twelve processes supply sixty complete checks to compare results and 12,120 timed operations in total.
Each state has 6,060 operations. All complete results, input identities and host `App.Vector` values match.

Five cases contain 2, 518, 620, 773 and 815 points, with 4, 4, 4, 151 and 6 input stations, respectively.
Each case has two measured sets of operations: `index-plus-queries` and `query-only-reuse`.
Each set has one initial operation and one hundred subsequent operations per process.
The first set includes calculation of station data and all input stations.
The second uses the same prepared station data for subsequent input stations. The test measures its preparation cost individually.

Only the first two-point `index-plus-queries` operation is the first station operation in that process.
Other initial values identify the first operation of that case and set. They do not identify a new runtime.
The product keeps no result for subsequent use. The tests did not control which file data the operating system kept.

The direct timer includes the actual host pair, temporary objects, Python `list` copies, result objects, point creation and final angle calculation.
Host input construction, complete checks to compare results and checks of identities occur before or after timing.
Both states include the same timer and operations on the Python `list` of results.
Python `sys.setprofile` does not operate during these direct measurements.

All ten sets show added median wall cost for subsequent operations.
These results are preserved costs of this extraction. They give no product performance acceptance. They do not show that human-interface times will stay within any specified limit.
They do not change a measurement profile or comparison rule or replace D-P6-008.

For subsequent operations, each state value is the median and [minimum, maximum] of six process medians.
Each process median contains one hundred operations. The paired difference is the median of six differences between related process medians.
The paired percentage is the median of six related percentage differences. The test does not calculate it from the shown state medians.
All direct table values use microseconds unless a column specifies percent.

| Points / requests | Boundary | Baseline wall | Candidate wall | Paired difference [minimum, maximum] | Paired percent |
| --- | --- | --- | --- | --- | --- |
| 2 / 4 | `index-plus-queries` | 15.898 [15.680, 16.201] | 34.438 [34.040, 34.701] | +18.435 [+17.954, +18.835] | +115.98% |
| 2 / 4 | `query-only-reuse` | 11.201 [11.101, 11.452] | 26.070 [25.849, 26.661] | +14.939 [+14.578, +15.380] | +133.33% |
| 518 / 4 | `index-plus-queries` | 330.673 [327.257, 340.998] | 586.880 [576.765, 593.828] | +252.925 [+247.236, +264.493] | +76.42% |
| 518 / 4 | `query-only-reuse` | 13.150 [12.569, 13.355] | 28.599 [28.184, 28.779] | +15.432 [+15.139, +16.210] | +118.34% |
| 620 / 4 | `index-plus-queries` | 392.205 [388.502, 398.452] | 685.918 [674.582, 701.673] | +293.761 [+284.522, +309.663] | +74.91% |
| 620 / 4 | `query-only-reuse` | 12.774 [12.644, 13.135] | 28.316 [28.253, 28.945] | +15.511 [+15.270, +16.252] | +121.43% |
| 773 / 151 | `index-plus-queries` | 745.807 [738.399, 756.422] | 1578.557 [1558.677, 1590.973] | +833.005 [+808.878, +844.405] | +111.54% |
| 773 / 151 | `query-only-reuse` | 275.574 [272.648, 277.488] | 752.703 [748.246, 758.111] | +476.942 [+472.988, +484.110] | +172.65% |
| 815 / 6 | `index-plus-queries` | 511.690 [507.685, 524.937] | 907.690 [904.203, 940.391] | +395.925 [+384.416, +427.111] | +77.81% |
| 815 / 6 | `query-only-reuse` | 16.812 [16.581, 16.977] | 38.851 [38.303, 41.209] | +22.107 [+21.406, +24.306] | +132.03% |

The following table gives state medians for CPU and each initial operation.
The complete raw records keep each range, paired difference, percentage and individual measurement.

| Points / requests | Boundary | Subsequent CPU, baseline / candidate | Initial wall, baseline / candidate | Initial CPU, baseline / candidate |
| --- | --- | --- | --- | --- |
| 2 / 4 | `index-plus-queries` | 17.347 / 35.967 | 41.413 / 84.832 | 44.223 / 87.750 |
| 2 / 4 | `query-only-reuse` | 12.619 / 27.561 | 13.450 / 28.654 | 14.898 / 30.146 |
| 518 / 4 | `index-plus-queries` | 332.579 / 588.666 | 311.622 / 579.712 | 313.373 / 581.476 |
| 518 / 4 | `query-only-reuse` | 14.637 / 30.166 | 45.712 / 58.712 | 47.620 / 60.288 |
| 620 / 4 | `index-plus-queries` | 393.994 / 687.687 | 402.916 / 727.832 | 404.635 / 729.678 |
| 620 / 4 | `query-only-reuse` | 14.234 / 29.823 | 46.844 / 62.664 | 48.391 / 64.221 |
| 773 / 151 | `index-plus-queries` | 747.349 / 1580.256 | 765.234 / 1620.278 | 767.004 / 1622.036 |
| 773 / 151 | `query-only-reuse` | 277.272 / 754.425 | 334.311 / 807.499 | 335.839 / 809.232 |
| 815 / 6 | `index-plus-queries` | 513.576 / 909.433 | 559.143 / 983.955 | 560.867 / 985.784 |
| 815 / 6 | `query-only-reuse` | 18.314 / 40.383 | 58.697 / 97.370 | 60.273 / 98.885 |

The first station operation in each process has a wall median of 41.414 microseconds for the baseline and 84.832 for the candidate.
Its paired median difference is +43.278 microseconds. These values apply only to the first station operation in each process.

| Prepared points | Preparation wall, baseline / candidate | Preparation CPU, baseline / candidate |
| --- | --- | --- |
| 2 | 5.696 / 10.575 | 7.720 / 12.624 |
| 518 | 293.808 / 533.744 | 296.041 / 536.181 |
| 620 | 351.363 / 629.567 | 353.287 / 631.505 |
| 773 | 431.630 / 792.962 | 433.589 / 794.991 |
| 815 | 458.832 / 862.880 | 460.629 / 864.962 |

Direct RSS after each operation is 240,812–241,452 KiB for the baseline and 240,064–241,300 KiB for the candidate.
The RSS change for individual operations is 0–32 KiB in both states.
The maximum recorded process memory is 334,388 KiB for the baseline and 334,796 KiB for the candidate.
That maximum includes imports and earlier process preparation.

Sampled RSS does not prove the largest temporary memory use or a general decrease in memory use.
The raw records and `direct-report-tables.md` preserve the complete memory ranges for each case and set of operations.

## Preserved failures

The initial caller fixture supplied no source shapes to `create_section_masks`.
It correctly gave `ValueError: No source geometry is available for sectioning.`
FreeCADCmd stopped with status `0`, but the necessary terminal sentinel was missing.
The primary failure classification is `fixture-or-harness-defect`.
The corrected ignored fixture supplies actual generated plan faces and preserves the rejection check for empty shapes.
The first three correct straight samples stay preserved. A different attempt completed only the nine other caller samples.

The initial command for the FreeCAD proof used `--pass` with no following argument.
FreeCAD rejected the command before Python could do the checks.
The primary failure classification is `fixture-or-harness-defect`.
The specified command without that argument completed the proof in a different log.

The initial direct baseline command imported a test module that put the candidate path before the selected baseline path.
The product correctly rejected the package source before any station timing occurred.
The primary failure classification is `fixture-or-harness-defect`.
A different ignored command sets the selected path after the test module import and before product imports.
It preserves the same inputs, sequence, source checks and checks to compare results. All six planned pairs then completed in new output files.

The first connected human-interface candidate completed its workflow, but the check against the preserved baseline found one different document name.
The ignored tool used `connected-straight.FCStd` instead of the earlier `phase3-connected-straight.FCStd` name.
The primary failure classification is `fixture-or-harness-defect`.
The initial run and complete difference stay preserved. The next authorised attempt uses the unchanged earlier tool and a new output directory.
The comparison rule and product source stay unchanged.

The initial document validation found no manifest entry for this new report. All earlier frozen records and their hashes matched.
Its `frozen-record manifest coverage drifted` diagnostic and classification stay in the task evidence.
The directly dependent alignment adds only the new report identity to `reference/history/frozen-records.json`.
It preserves the initial manifest date, schema and historical entries.

These corrections changed no preserved product source, test or development tool.
The task has used none of its two permitted source/test repair passes.

## Independent technical review

The independent read-only review of all eighteen frozen source, test and machine-contract paths has a PASS result with no findings for necessary action.
The reviewer wrote none of those files and did no host action or source repair.
The review validates raw identities, calculation proof, all twelve caller checks to compare results, sixty direct checks to compare results and all 12,120 timed measurements.
It validates the three complete human-interface checks to compare results and all preserved timing and visual records.
The added direct costs and descriptive human-interface limitations stay clear. The review gives no performance or phase acceptance.

The review excludes canonical prose. Its next necessary validation concerns the new benchmark's manifest identity and the usual publication checks.
The different bounded documentation cycle supplies the sole Documentation Review and deterministic final validation for the three controlled documents.

## Limits and preservation

This task supplies evidence for the bounded scope in Phase 7 Exits 3, 2 and 1.
The evidence concerns the API with no FreeCAD or Qt dependency, equal results and the B16 workflow, respectively.
Phase 7 stays Open at 0/4 with all four exits Pending. This task accepts no exit.
D-P6-008 stays in full, with its mandatory acceptance boundary before Phase 10 beta.
All conditions to compare results and remove legacy paths stay in full.

The PR #72 added common-extension cost stays about 1.25 microseconds, or 25.33%.
The PR #73 connected-edit RSS and wall-time limitations for rejection with no curve connection stay preserved with their unknown causes.
D-GOV-011 stays stopped with its retained negative evidence. The task did no stopped experiment again.

Project status stays `unknown`. Output keeps private-development status. The task accepts no release or wider migration claim.

The task does not migrate complete groups of functions for platforms, turnouts, crossovers, timbers or chairs.
It changes no persistence schema, transaction, output contract or condition to remove a legacy path.
The proof includes generated records, usual invalid inputs and its specified error combinations.
It does not prove all possible Python objects, complete error output, failure from insufficient memory, complete B-rep or export bytes.

## Preserved proof identities

The active worktree is `/home/richard/PycharmProjects/TrackTemplateMacro-worktrees/phase7-station-mapping` on `codex/phase7-station-mapping`.
The task evidence below is in its ignored `tmp/phase7-station-mapping/` directory unless another path is given.
Receipts keep the complete raw path and SHA-256 manifests. Historical evidence, failed attempts and worktrees stay preserved.

| Record | SHA-256 |
| --- | --- |
| `implementation-pre-movement-baseline-completion.json` | `644bc9cb9dbb5cdf3bbf59d5a65aa3f0d9f38d520cdab53a381eacd78d46e846` |
| `implementation-candidate-proof-completion.json` | `107e2e4befdc3b3fece45dfb0a1849b96f9fc3f5c2eddc93ed2216ad9d1e4af0` |
| `technical-source-freeze.json` | `169c05613f4d8a415f41aa78a4e4656ced97c2a03e50c05b9760471a4e67704b` |
| `implementation-candidate-caller-comparison.json` | `74b45a56a8751c72ad983afc86a85a288857fa84848275d0476318cf0cbe37ca` |
| `implementation-direct-completion.json` | `ea09b4df848ddf9b56f059793ccdf307b2a46aa7c19a524e302f427d0533017b` |
| `implementation-direct-plan-attempt-02.json` | `390108624651828173ce0dd163faba7d6b647f1975488c53832fac7d7a1bfdb2` |
| `gui-fixed-protocol.json` | `16f2b2ddc287ae916f3e223aaa46efb0c446482eedcaf65b2a48d743e166b029` |
| `gui-preparation-and-baseline-reuse.json` | `2661d7918eac02411c5125a4f4a66a3d12ef62ea9c6e0cc2c3603572146816e8` |
| `direct-report-tables.md` | `873968cb0849e32baff574a09ed360d4771400c327bdbadefbfe891c77d59986` |
| `gui-completion-receipt.json` | `f0f5ae736f9928ebc6ecd85367f4b48e3cd5896f0964347f9a01bbfe8bdb2dfd` |
| `root-visual-inspection.json` | `408bcc0ad930517b8bdfaca80c869737122d04c6fae397802da799787e4c3711` |
| `independent-technical-quality-review.md` | `43c937315fd1b6e7fbe9c2d8fe0d98e8cfc5c9dea437db559aff807a754f48e5` |
| Primary worktree `tmp/phase7-post74-backup/terminal-backup-receipt.json` | `3bfc041bf8069077a87318410b0f89c35d0974a05a06e23228af579a9c288c0d` |

The technical source receipt identifies eighteen source, test and machine-contract paths.
It keeps the same files that all candidate validation used. Canonical prose is outside that technical receipt.
The later documentation receipt and deterministic validation identify the different documentation review and its completed state.
