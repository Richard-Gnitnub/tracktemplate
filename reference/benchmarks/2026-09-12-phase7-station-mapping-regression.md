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
The small compatibility objects keep native point reads and the sequence of point creation and track direction calculations.
The API uses no FreeCAD or Qt value. It keeps no calculated result for subsequent use.

The product selects ten functions together and validates 38 actual caller routes.
The station pair has 15 and 30 caller functions, respectively, with 34 different callers in total.
The checks include the actual crossover panel method and the nested function for points at stations.
They validate each selected function, exact compatibility types and `App.Vector`.
A selection error puts all previous values back, including removal of new values when no previous value existed.

B14, B15, the launcher, earlier machine contracts and the frozen tools to compare results stay unchanged.
The twelve changed existing tests preserve their historical contract assertions and check the current ten-function selection separately.
Two new tests supply the complete station proof with standalone Python and qualified FreeCAD.

Before product work, the existing recovery workflow completed snapshot `2026-09-12-post-pr74-pre-phase7-next-01` at the approved independent destination.
The snapshot covers 14 roots and 16,444 files. All checksum comparisons and source checks had PASS results.
It preserves all 59 previous destination entries. The completed restore evidence from September 5 stays applicable.

The new station worktree was created after the snapshot. The snapshot does not contain the new candidate or its subsequent evidence.
The backup receipt records a successful flush and unmount. Physical disconnection and the physical PyCharm window were not observed.
No physical operation was necessary for the remote development work.

## Calculation and caller proof

Before the product source changed, the complete B14/B15 station proof had a PASS result.
It compares all seven station-data items, point identities, copied lists, numerical limits, repeated points, errors and operation sequence.
The candidate gives the same complete results within that scope.
The checks include reads from input objects, point creation before final angle arithmetic and combinations of errors.
The neutral result is frozen, and reading its `heading` property calculates the original expression.

Twelve selected existing standalone test sets and the new station test have PASS results.
They cover Phase 1 alignment, straight tracks and station values, Phase 2 foundation, Phase 3 routing and workflows, and Phase 4 route removal.
They also cover all five previous Phase 7 calculations and routing results.
Python accepted the changed source and tests. Their Ruff checks have PASS results.
All eighteen previous domain function definitions stay unchanged.

Seven proofs with qualified FreeCAD have PASS results, each with process exit status `0` and its necessary success sentinel.
They cover the Phase 3 caller, all five previous Phase 7 functions and the new station pair.
The new native proof includes eleven actual generated main, parallel, platform and straight alignment records.
It compares complete values, original point identities and actual `App.Vector` results.

The qualified host profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The host uses FreeCAD 1.1.3, Python 3.13.13, Qt/PySide 6.11.1 and OCCT 7.8.1.
The development tool is `.devtools/freecad-cli` at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`, with its six approved patches unchanged.
Standalone checks use Python 3.12.3 and Ruff 0.16.4.

The actual caller checks use three invocations for each of four groups in each state.
All twelve comparisons give equal complete ordered results, call counts and input point counts.
Python `sys.setprofile` counts the calls during these measurements. Their times include those counting operations.
Their differences do not establish costs for a workflow without those operations.

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

| Caller group | Index calls | Interpolation calls | Observed point counts | Comparison |
| --- | --- | --- | --- | --- |
| straight-production | 39 | 45 | 2 | Equal in all three corresponding candidate invocations |
| platform-sectioning | 25 | 32372 | 518, 620 | Equal in all three corresponding candidate invocations |
| turnout-mapping | 1 | 314 | 773 | Equal in all three corresponding candidate invocations |
| crossover-feasibility | 8 | 59322 | 773, 815 | Equal in all three corresponding candidate invocations |

The platform wall median is higher by 446.110 ms, or 80.17%. The turnout wall median is higher by 6.150 ms, or 13.24%.
The crossover wall median is higher by 509.439 ms, or 1.43%. These observations stay visible limitations with the counting operations included.

## Human-interface proof

The fixed plan supplies five new samples across three scenarios: a plain-line pair, one connected-straight candidate and a platform-sectioning pair.
The connected baseline is the retained PR #73 candidate with the exact current product source for this comparison.
All 105 selected runtime, bridge and recipe paths match protected main before extraction.
The source, qualified profile, fixture and preferences were checked before reuse. No completed baseline sample was repeated.

All five planned samples have PASS results. The connected scenario also has one preserved attempt with a different copied-document name.
Its separate retry uses the unchanged existing runner and the inherited name.
All three final comparisons give equal complete workflow data, with no differences.
Each new workflow uses a different isolated FreeCAD process and a disposable document copy.

Plain-line and connected-straight samples exercise actual B16 Generate/Replace operations and their existing edit, recovery and persistence checks.

The platform scenario starts with the two-track curve fixture and one enabled outside platform.
Its main curve uses a 600 mm radius, 600 mm transitions, 90 degrees and 32 mm width.
The platform length changes from 250 mm to 300 mm with 50 mm tapers and the existing 2D face output.
Sectioning uses 600 mm maximum and 100 mm minimum lengths, balanced sections and numbers in travel sequence.
The unsplit geometry stays present. Formation, assembly and export are disabled.

The platform comparison includes complete initial, generated and edited records, platform roles, section numbers, geometry and metadata.
It includes intermediate history records, two complete Undo/Redo cycles, save/reopen and restored preferences.
The inherited Undo/Redo procedure takes three steps. This task does not claim a single transaction for those operations.
The comparison excludes only the fixed volatile time, resource and path items. It keeps the complete semantic data.

These are descriptive samples, with one final sample per state and scenario.
They do not establish typical human-interface performance or a numerical acceptance threshold.
They do not prove equal complete B-rep or export bytes.
Turnout and crossover evidence comes from their actual calculation callers. This task adds no complete human-interface lifecycle proof for those families.

After all measurements, a different isolated FreeCAD process opened new disposable copies of the three completed candidate documents.
The Technical Lead inspected all three top-view images from the existing bridge API.

The plain-line view shows two separate curved faces and coloured centrelines.
The connected view shows continuous tracks with straight extensions at both ends.
The platform view shows track section boundaries and a separate outside platform face.
The source documents and copies stayed byte-identical. The process closed without saving documents or doing product operations.

The images are in the active worktree's ignored `benchmark-output/freecad-bridge/phase7-station-mapping-visual/` directory.
Their names are `plain-line-top-view.png`, `connected-top-view.png` and `platform-sectioning-top-view.png`.
They show representative geometry. They do not prove output clearance or complete equality of shapes.

The following table retains all eighteen scenario observations, including the original connected attempt with the incorrect name.
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
| Create connected pair | connected original name mismatch | 13464.205 | 2519.232 | 171.961 | 14 |
| Edit connected lengths | connected original name mismatch | 13181.904 | 2195.705 | 57.262 | 0 |
| Create connected pair | connected corrected name | 13454.307 | 2514.880 | 138.055 | 14 |
| Edit connected lengths | connected corrected name | 13177.385 | 2164.101 | 58.500 | 0 |
| Create platform and sections | platform baseline | 19382.559 | 15824.289 | 413.375 | 23 |
| Edit platform length | platform baseline | 18972.479 | 15351.329 | 195.254 | 0 |
| Create platform and sections | platform candidate | 19372.684 | 15693.847 | 401.738 | 23 |
| Edit platform length | platform candidate | 19021.378 | 15250.359 | 202.156 | 0 |

Plain-line rejection wall time is higher by 958.659 ms. Its CPU time is higher by 3.721 ms.
Plain-line replacement recovery wall time is higher by 1,007.925 ms, with CPU time higher by 12.751 ms and RSS change higher by 3.953 MiB.
Platform edit wall time is higher by 48.899 ms and RSS change by 6.902 MiB, although CPU time is lower.

These observations stay limitations. Their causes are unknown. This task does not infer a source cause from one sample.

The baseline starts precede the final candidate starts by 73.313387 seconds for plain line and 112.003936 seconds for platform sectioning.
The retained connected baseline precedes its final candidate by 10,056.798315 seconds, or about 2.79 hours.
The operating system's retained file data was not controlled. Later edits use the same process and calculate new results.
The terminal receipt keeps all 164 resource observations, including history and persistence operations.
Nested time values are not independent spans and must not be added together.

## Direct cost

The fixed direct plan uses six pairs. The sequence of baseline and candidate changes between pairs.
Each state starts in a new FreeCADCmd process. Twelve processes supply sixty complete comparisons and 12,120 timed invocations in total.
Each state has 6,060 invocations. All complete results, input identities and native vectors match.

Five cases contain 2, 518, 620, 773 and 815 points, with 4, 4, 4, 151 and 6 station requests, respectively.
Each case has two measured boundaries: `index-plus-queries` and `query-only-reuse`.
Each boundary has one initial invocation and one hundred subsequent invocations per process.
The first boundary includes calculation of station data and all requests.
The second uses the same prepared station data for subsequent requests. Its preparation cost is measured separately.

Only the first two-point `index-plus-queries` invocation is the first station call in that process.
Other initial values identify the first invocation of that case and boundary. They do not identify a new runtime.
The product has no result cache. The operating system's retained file data was not controlled.

The direct timer includes the actual host pair, temporary objects, list copies, result objects, point creation and final angle calculation.
Native input construction, complete comparisons and checks of identities occur outside timing.
Both states include the same timer and result-list operations. Python `sys.setprofile` does not operate during these direct measurements.

All ten boundaries show added median wall cost for subsequent invocations.
These results are retained costs of this extraction. They give no product performance acceptance or guarantee of human-interface time.
They do not change a measurement rule or replace D-P6-008.

For subsequent invocations, each state value is the median and [minimum, maximum] of six process medians.
Each process median contains one hundred invocations. The paired difference is the median of six differences between corresponding process medians.
The paired percentage is the median of six corresponding percentage differences. It is not calculated from the displayed state medians.
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

The following table gives state medians for CPU and each initial invocation.
The complete raw records retain every range, paired difference, percentage and individual observation.

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

The first station call in each process has a wall median of 41.414 microseconds for the baseline and 84.832 for the candidate.
Its paired median difference is +43.278 microseconds. This is a different boundary from the subsequent invocation values.

| Prepared points | Preparation wall, baseline / candidate | Preparation CPU, baseline / candidate |
| --- | --- | --- |
| 2 | 5.696 / 10.575 | 7.720 / 12.624 |
| 518 | 293.808 / 533.744 | 296.041 / 536.181 |
| 620 | 351.363 / 629.567 | 353.287 / 631.505 |
| 773 | 431.630 / 792.962 | 433.589 / 794.991 |
| 815 | 458.832 / 862.880 | 460.629 / 864.962 |

Direct RSS after invocation spans 240,812–241,452 KiB for the baseline and 240,064–241,300 KiB for the candidate.
The RSS change at individual invocation boundaries is 0–32 KiB in both states.
The maximum recorded process memory is 334,388 KiB for the baseline and 334,796 KiB for the candidate.
That maximum includes imports and earlier process setup. Sampled RSS does not prove the largest temporary allocation or a general memory saving.
The raw records and `direct-report-tables.md` preserve the complete memory ranges for each case and boundary.

## Preserved failures

The initial caller fixture supplied no source shapes to `create_section_masks`.
It correctly raised `ValueError: No source geometry is available for sectioning.`
FreeCADCmd exited with status `0`, but the necessary terminal sentinel was absent.
The primary classification is `fixture-or-harness-defect`.
The corrected ignored fixture supplies actual generated plan faces and preserves the rejection check for empty shapes.
The first three valid straight samples stay preserved. A separate attempt completed only the nine remaining caller samples.

The initial native proof invocation used `--pass` with no following argument.
FreeCAD rejected the command before Python assertions could run.
The primary classification is `fixture-or-harness-defect`.
The established command without that argument completed the proof in a different log.

The initial direct baseline invocation imported a test helper that put the candidate path before the selected baseline path.
The product correctly rejected the package source before any station timing occurred.
The primary classification is `fixture-or-harness-defect`.
A separate ignored invocation sets the selected path after the helper import and before product imports.
It preserves the same inputs, sequence, source checks and comparisons. All six planned pairs then completed in new output files.

The first connected human-interface candidate completed its workflow, but comparison with the retained baseline found one different document name.
The ignored runner used `connected-straight.FCStd` instead of the inherited `phase3-connected-straight.FCStd` name.
The primary classification is `fixture-or-harness-defect`.
The original run and complete difference stay preserved. The authorised retry uses the unchanged existing runner and a new output directory.
The comparison rule and product source stay unchanged.

The initial document validation found no manifest entry for this new report. All earlier frozen records and their hashes matched.
Its `frozen-record manifest coverage drifted` diagnostic and classification stay in the task evidence.
The directly dependent alignment adds only the new report identity to `reference/history/frozen-records.json`.
It preserves the existing manifest date, schema and historical entries.

These corrections changed no retained product source, test or development tool.
The task has used none of its two permitted source/test repair passes.

## Independent technical review

The independent read-only review of all eighteen frozen source, test and machine-contract paths has a PASS result with no findings that need action.
The reviewer wrote none of those files and performed no host action or source repair.
The review verifies raw identities, calculation proof, all twelve caller comparisons, sixty direct comparisons and all 12,120 timed observations.
It verifies the three complete human-interface comparisons and all retained timing and visual records.
The added direct costs and descriptive human-interface limitations stay explicit. The review gives no performance or phase acceptance.

The review excludes canonical prose. Its remaining validation boundary is the new benchmark's manifest identity and the normal publication checks.
The separate finite documentation cycle supplies the sole Documentation Review and deterministic final validation for the three controlled documents.

## Limits and preservation

This task supplies evidence for the bounded scope in Phase 7 Exits 3, 2 and 1.
The evidence concerns the API with no FreeCAD or Qt dependency, equal results and the B16 workflow, respectively.
Phase 7 stays Open at 0/4 with all four exits Pending. This task accepts no exit.
D-P6-008 stays in full, including the mandatory acceptance boundary before Phase 10 beta.
All conditions to compare results and remove legacy paths stay in full.

The PR #72 added common-extension cost stays about 1.25 microseconds, or 25.33%.
The PR #73 connected-edit RSS and independent rejection wall-time limitations stay preserved with their unknown causes.
D-GOV-011 stays stopped with its retained negative evidence. No stopped experiment was repeated.

Project status stays `unknown`. Output keeps private-development status. No release or wider migration claim is accepted.

The task does not migrate complete platform, turnout, crossover, timber or chair families.
It changes no persistence schema, transaction, output contract or condition to remove a legacy path.
The proof covers generated records, ordinary invalid inputs and its specified error combinations.
It does not prove every possible Python object, complete error output, failure from insufficient memory, complete B-rep or export bytes.

## Retained proof identities

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

The technical source receipt binds eighteen source, test and machine-contract paths.
It keeps the exact files used by all candidate validation. Canonical prose is outside that technical receipt.
The later documentation receipt and deterministic validation identify its separate review and completed state.
