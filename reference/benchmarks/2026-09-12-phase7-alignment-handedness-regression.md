# Phase 7 Evidence for Calculation of Curve Direction

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-alignment-handedness.md) define the calculation and its sequence.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

The earlier authorised PR #75 has head `7c9c7b15518386c164a94066132cce0466af1474` and merge commit `ef29e88ec86777ef79503da83e4043e8d3d644a6`.
CI for that merge has a PASS result. The primary worktree was clean and equal to protected main before this task.
The owner's subsequent `$tracktemplate-continue` command authorises this one Level 2 result with authority from D-GOV-004 and the Phase 7 scope.

The complete `mirror_alignment_for_turn` operation was missing from Core.
It now uses `tracktemplate.domain.alignment` through `tracktemplate.api`.
The small compatibility object applies its calculated named items to the initial FreeCAD alignment record in the earlier sequence.
The sole actual product caller is `run_macro`.

It processes the main and secondary alignments after common straight extensions.
Each operation is before its alignment length calculation.
Construction of straight tracks is after those operations.

The product selects eleven functions together and validates 38 actual caller entries.
Only the current `run_macro` entry adds the selected function.
After a selection error, the workflow puts all previous values back.
It removes an added name if that name was absent before selection.
The API calculation has no FreeCAD or Qt dependency and keeps no result for subsequent use.

B14, B15, the launcher, earlier machine contracts and the historical tools to compare results stay unchanged.
Fourteen earlier tests receive only the necessary identities for current function selection and fixture changes.
Two new tests supply the complete bounded proof with standalone Python and qualified FreeCAD.

Before product work, the recovery workflow completed snapshot `2026-09-12-post-pr75-pre-phase7-next-01` at the destination approved for independent preservation.
The snapshot contains fifteen roots and 17,408 regular files. It preserves all sixty previous destination entries.
The checks to compare sources and destinations, checks of hashes and validation done independently have PASS results.
The completed proof to copy backup data to a disposable target from September 5 stays applicable.

The Technical Lead made the new worktree after the snapshot. The snapshot does not contain this candidate or its subsequent evidence.
The terminal receipt records completed writes and safe disconnection of the device file system.
No observation of physical disconnection, storage at a different location or the PyCharm window on the workstation screen is available.
No physical operation was necessary to complete this task from a different location.

## Calculation and caller proof

The preserved B14/B15 definition is identical in both source files at lines 7946–7954.
Its source fragment has SHA-256 `b9dcc8f051067716a84b9a97f05fbaa711d7a4234e6214d0de3e5a05979e8ef7`.
The actual caller is at line 41099.

Before the product changed, the complete proof to compare results had a PASS result after one classified test correction.
The candidate gives equal complete results for both preserved sources.
Each source has 128 usual groups, 45 operation-sequence outcomes, ten usual-error groups and two actual-caller groups.
The checks preserve the positive branch with no input reads, the signs of zero, NaN, endpoint presence and references to the same objects.
They also preserve metadata and two subsequent sign changes.
They preserve point creation, assignments to named items, errors and partial changes in the initial sequence.

The actual-caller proof executes the preserved loop on generated main and secondary alignments for both signs.
It checks the subsequent length calculation and the position of the loop before construction of straight tracks.
The API proof without host objects checks XY results, delayed reads of named items and unchanged input records.

The function-selection proof rejects the wrong function, compatibility type and function to make `App.Vector` objects.
It also rejects the wrong `run_macro.__globals__` identity or caller target.
After failure, it checks that all eleven names have their previous values.
It also checks that the workflow removes an added name if that name was initially absent.

Eleven selected earlier standalone test sets and the new test have PASS results.
They cover Phase 1 alignment, Phase 2 foundation, Phase 3 routing and workflows, Phase 4 route removal and the six earlier Phase 7 calculations.
Seven earlier qualified FreeCAD proofs and the new proof have PASS results, each with process exit status `0` and its necessary success sentinel.

The new host proof checks 128 usual groups, usual errors and the actual loop with both signs.
Its generated main and secondary alignments have 518 and 544 points.
It checks complete values, actual `App.Vector` results, references to the same objects, metadata and unchanged document state.

The qualified profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The development bridge is `.devtools/freecad-cli` at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`, with its six approved patches unchanged.
Standalone checks use Python 3.12.3 and Ruff 0.16.4.
The final validation preflight, Ruff, Python and macro parsing, and whitespace checks have PASS results.
All previous function and class definitions in `tracktemplate.domain.alignment` stay unchanged.

## Direct cost

The fixed plan uses three pairs of different FreeCAD processes in this sequence: `B0`, `C0`, `C1`, `B1`, `B2`, `C2`.
The comparison baseline uses accepted main. The candidate uses the new source.
The complete actual host operation includes temporary objects to read XY values, subsequent calculations and Python `list` objects.
It also includes conversion to `float`, creation of `App.Vector` objects and assignments to named items.

Each timed operation uses the function for both generated tracks, with 518 and 544 points.
The fixture uses 600 mm transitions, a 90-degree curve and radii of 600 mm and 655 mm.

Each process has one initial operation and 100 subsequent operations for each of two cases.
The cases use a positive sign with no changes to named items and a sign that changes the curve direction.
The case sequence alternates between pairs. Only the first case has the first operation in its process.

The runtime and input generation are already complete at that point. These values are not application-start times.
Input generation and copies are outside the timers in both states.
The common timer and the costs of the Python `list` for results stay inside.

All six samples give equal complete inputs and outputs.
The series contains 606 timed operations per state and two actual host operations per timed operation.
Each timed operation checks complete values, identities and metadata.
Operations that change curve direction also check exact `App.Vector` types and new points.
Positive operations preserve the initial identities.

The raw records preserve each case's first complete output and each timed operation's time and memory values.
The subsequent checks to compare complete outputs stop with an error if they find a difference.
The records do not store the individual results of those checks.

The first baseline finished 659.823415 seconds before the first candidate started because product development occurred between them.
Later pairs use new processes in the fixed sequence. The plan does not control the operating system's file cache or scheduling.
These observations do not establish performance acceptance or a typical workflow cost.

The table gives medians and [minimum, maximum] from all 300 subsequent operations per case and state.
All time values use microseconds. The paired columns use the medians for each of the three related process pairs.
They do not use the difference between the medians from all samples.

| Case and metric | Baseline median [minimum, maximum], microseconds | Candidate median [minimum, maximum], microseconds | Paired median change [minimum, maximum], microseconds | Paired median change, % |
| --- | --- | --- | --- | --- |
| `positive-no-op` wall | 1.6330 [1.2020, 8.9970] | 5.6510 [3.9170, 17.3530] | 4.1680 [3.4165, 5.9605] | +266.6667 |
| `positive-no-op` CPU | 3.3210 [2.8560, 11.5920] | 7.4440 [5.4710, 20.9090] | 4.3480 [3.4755, 6.3520] | +135.6207 |
| `reflected` wall | 612.2580 [585.1910, 1194.8710] | 1143.1695 [1116.1380, 1560.4620] | 533.8985 [525.5460, 536.3225] | +87.2117 |
| `reflected` CPU | 614.2765 [586.9810, 1198.2970] | 1145.4180 [1117.9070, 1564.4630] | 533.7565 [525.5600, 536.5415] | +86.9004 |

Both cases have added measured wall and CPU cost.
For the `reflected` pair, the median added wall cost is 533.8985 microseconds, or 87.2117%.
For the positive pair, it is 4.1680 microseconds, or 266.6667%.
These costs stay limitations of this bounded extraction. They do not select another optimisation or change D-P6-008.

The next table gives the initial operation for each case, with three samples per state.
The second case is after the other case in the same process.
The raw records identify that sequence for each sample.

| Case and metric | Baseline median [minimum, maximum], microseconds | Candidate median [minimum, maximum], microseconds |
| --- | --- | --- |
| `positive-no-op` wall | 2.7550 [1.6030, 2.8460] | 10.0990 [8.6660, 10.2690] |
| `positive-no-op` CPU | 5.3900 [3.1460, 5.4600] | 12.6430 [10.9500, 12.6540] |
| `reflected` wall | 618.1330 [603.0450, 627.2720] | 1203.9550 [1156.4850, 1208.0330] |
| `reflected` CPU | 621.1750 [604.8950, 629.4900] | 1207.4140 [1158.7630, 1210.1190] |

RSS and high-water RSS include the loaded application, untimed input preparation and result records.
They do not isolate the maximum memory use for one operation.
The RSS median from all samples is 238,292 KiB for the baseline and 239,328 KiB for the candidate.
The baseline range is 235,752–238,352 KiB, and the candidate range is 238,348–239,348 KiB.
The high-water RSS medians are 333,324 KiB and 333,488 KiB, with ranges of 329,164–333,736 KiB and 333,308–333,580 KiB.

The before and after summaries are equal within each state. These process observations do not show equal costs for memory use.
The terminal record keeps all individual before and after measurements.

## Human-interface proof

The fixed plan uses one new `plain-line-edit` candidate sample.
Its comparison baseline is the preserved PR #75 candidate from the same host.
All 109 applicable runtime, fixture and preference paths match accepted main before this extraction.
Three ignored scripts from the earlier task are absent from primary main. Their preserved identities stay available.
The candidate protocol protects 113 exact paths.

The sample completes actual B16 Generate/Replace operations from left to right and back from right to left.
The unchanged check to compare results includes all nine history actions, complete product data records, object names and counts, and copied-document persistence.
It also includes rejection of a zero angle before the transaction and recovery from an injected transaction failure.
The complete workflow records are equal, with zero differences and equal hashes for product data.
The check removes only the earlier specified named items for time, resources and paths. It removes no additional named product item.

The preserved baseline started 6,732.665949 seconds before the candidate, or about 1.87 hours.
There is one sample per state. These are descriptive observations, not typical workflow costs or a numerical acceptance limit.
The task adds no connected-track, platform, turnout or crossover human-interface sample.
It does not prove equal complete B-rep or export bytes.

After all measurements, a different isolated FreeCAD process opened a new copy of the completed right-hand document with equal bytes.
The Technical Lead inspected the actual top-view PNG from the current bridge API.
It shows two continuous grey curve faces with space between them, blue and red centrelines, and intact visible ends.
The initial document and disposable copy kept the same bytes.
The process closed without a save or execution of product operations.
Both isolated instances are closed, and no document stays open in them.

The image is `benchmark-output/freecad-bridge/phase7-alignment-handedness-visual/right-hand-top-view.png` in the active worktree.
Its SHA-256 is `3030d64226a3f7e75bf36e99d1e3667bbea0baaecd7706a7ed0399753619661e`.
It shows an example of the geometry. It gives no acceptance of equal complete shapes, output or the physical screen.

The next table keeps all eight case measurements, with expected rejection and recovery.
Wall and CPU values use milliseconds. RSS changes use MiB. Object changes are counts.

| Action | State | Wall ms | CPU ms | RSS change MiB | Object change |
| --- | --- | --- | --- | --- | --- |
| Replace left with right | baseline | 13997.100 | 2787.834 | 212.707 | 0 |
| Change right back to left | baseline | 13152.117 | 2030.676 | 51.332 | 0 |
| Reject zero angle | baseline | 3140.492 | 191.479 | 0.102 | 0 |
| Stop replacement | baseline | 3159.697 | 408.289 | 4.457 | 0 |
| Replace left with right | candidate | 14005.710 | 2790.662 | 151.258 | 0 |
| Change right back to left | candidate | 13157.618 | 2087.785 | 58.340 | 0 |
| Reject zero angle | candidate | 2151.516 | 192.371 | 4.094 | 0 |
| Stop replacement | candidate | 2152.595 | 400.664 | 0.508 | 0 |

The change back to a left-hand curve has wall time higher by 5.501 ms and CPU time higher by 57.108 ms.
Its RSS change is higher by 7.008 MiB.
These single-sample differences stay descriptive limitations. Their causes are unknown.
Lower rejection and recovery wall times do not replace the earlier PR #75 limitations or give performance acceptance.

The terminal record preserves all 74 records of time, memory and history counts from intervals that contain other intervals.
It includes individual RSS endpoints and persistence measurements.
Some measured intervals contain other intervals. The reader must not add their times together.

## Failure integrity

The initial preserved test used Python `sum` to check the length independently.
The legacy `polyline_length` adds each segment in sequence from `0.0`.
On Python 3.12, those operations gave different final bits: `1542.476831002083` and `1542.476831002085`.
The difference was `-2.0463630789890885e-12`.
The primary classification is `test-or-oracle-defect`.

The authorised correction uses the unchanged legacy `polyline_length` to supply the expected test result.
It preserves exact equality, all cases and the checks that examine XY values independently. It changes no tolerance or product source.
The initial test, failure, exact correction and repetition of the initial command with a PASS result stay available.
This correction uses one of the two permitted source/test repair passes.

The first safety audit used the new worktree, which had no upstream or local copy of the primary source archive.
Its primary classification is `environment-or-profile-defect`: the command invocation used the wrong repository scope.
The initial output stays available. The same audit against the primary repository has a PASS result.
The correction changes no source, test or upstream identity to satisfy that check.

Before visual execution, the copied visual script named the earlier task's direct-completion receipt.
A different script changes only that prerequisite filename to `proof-direct-completion.json`.
The initial frozen script, protocol and 113 guarded files stay unchanged.
This preparation correction changes no measured command, tool to compare results, product source or test. No host execution failed because of it.

The first GUI result reader treated the summary from the tool to compare results as individual differences.
The preserved record reports `FAIL`, although the unchanged tool to compare results within it reports `equal: true` and `difference_count: 0`.
The primary classification is `fixture-or-harness-defect`.
The bounded correction reads the named result items from that tool in the same completed workflow records.
It does not change that tool or its changes to data to compare results. It does not repeat the GUI execution.

The initial result and the different corrected receipt stay available.

An initial concern about a product import before source selection was incorrect.
Inspection showed that the import was inside a helper function that the direct probe does not use.
The record claims no defect in import sequence or measurement with a FAIL result.
The probe checks actual module paths and source hashes before each measured sample.

## Independent technical review

A different read-only staff reviewer examined the complete twenty-path source, test and machine-contract change and the raw evidence.
The reviewer wrote none of those files or the GUI tools for this task.
The review has a PASS result, with no findings for necessary action or remaining evidence gap in the bounded technical scope.
It independently validates the complete checks to compare results, the preserved failures and corrections, the measured costs and the actual image.
It classifies the result as Level 2 necessary-enabling work for Exit 3, with bounded support for Exits 2 and 1.
The review accepts no exit and does not review canonical prose.

## Evidence identities

The active worktree is `TrackTemplateMacro-worktrees/phase7-alignment-handedness` on branch `codex/phase7-alignment-handedness`.
The next source identities identify the observed result. The complete technical record protects all twenty changed source, test and machine-contract paths.

| Repository path | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `14886e79b83357cd6d6e5d3c96d9296c247fc3924975a9cf6e47475849e1549d` |
| `tracktemplate/api.py` | `1579cd0390994d6ce34035a710527511e167150024e2dc019c3c575921661dcc` |
| `tracktemplate/compatibility/transition_workflow.py` | `1546b53cbca38ddb855a68c71acdd7f45c5a45e3594fb2ca0faad28e96bf0c84` |
| `reference/contracts/phase7-alignment-handedness.json` | `cec0eff6b917c175a8a963a9c6febbd298127e0b36fe1a4c5ee976759b65f751` |
| `tests/validate_phase7_alignment_handedness.py` | `cdabacef6055b0577014c423f5a622164500112980a537924db515799b74579d` |
| `tests/freecad_validate_phase7_alignment_handedness.py` | `7a445f14cb52dc41daf7f8c12f88426dbddfc39ac5fa876e714eb0596b9f42c9` |

The next records are under the worktree's ignored `tmp/phase7-alignment-handedness/` directory.
The completion records contain the commands, raw-result identities, exit statuses and necessary success sentinels.
They preserve the evidence with FAIL and PASS results in different records.

| Record | SHA-256 |
| --- | --- |
| `root-final-static/technical-state.json` | `6621cc45c9287d5464cfb816ab4317ec7a13f993520db667e4b6470fbc48d1b4` |
| `root-final-static/completion.json` | `8760beb90c00e692f78623648b6fa9a65163970ac6ca33130a156a4e112e2288` |
| `root-standalone-initial/completion.json` | `2cac85f5ee2400da4370bff4d99efce08f54737ff636a1fd9737ad08ff11c424` |
| `root-qualified-initial/completion.json` | `7c5edf0f32ec4000daf72ad87b5d1d707a0f075ef80f7c8bf9eaa8ae5512e2ff` |
| `proof-baseline-completion.json` | `753b3e553e4067d218220e46f2205834dfa5af2e9968dd38eb3342c7f719ce99` |
| `proof-candidate-standalone-completion.json` | `bea0f50450f5af08c8598d8332ff5e299b7f1a2ba3f3bce6080158f447b633c6` |
| `proof-native-invocation.json` | `3e82ada5a8eb417fafa71f8259619416cfdf797f2c2df4cca882f7ac648d039d` |
| `proof-direct-plan.json` | `f3eb2ad37a1f8e0cc4698204af81b138b616ff7ed1e6d898fe0120d03e162097` |
| `proof-direct-candidate-source.json` | `0cd1b80eb86ef65ecee8c8063879c6d1329a665231d3bb6bdfb33a5c93397f87` |
| `proof-direct-completion.json` | `01a5d82e881ca1dc7fe2ed3621008e09b3ebf3a18eafbd3057b1b0ac7f2fc14e` |
| `proof-author-completion.json` | `760940ab52a6aa6b41aac9dd37aa418cdc8738ace7c9e7699a766461ab442253` |
| `gui-fixed-protocol.json` | `fd0ddd722da76e192f6d8713e29582b3a38a38186ae1bf44c60e9501d653b331` |
| `gui-completion-receipt.json` | `6fb62cd2f74b9faf0052900dfba0ce0b8c2b05e6cf673741e24f01e158cddea1` |
| `root-visual-inspection.json` | `5a7e48b86b8ecbb12207738bd5148362c1333303db2087e46e3d3fadd02e40b5` |
| `independent-technical-quality-review.md` | `60916db1ae14a2f3ecd377f151e9e7ab22eec2878bec237c8231f75cbe3a8c4d` |

The primary repository keeps the backup packet under `tmp/phase7-post75-backup/`.
Its `terminal-backup-receipt.json` has SHA-256 `493cdf9611002957c7021e6a3e0a4cd02132235cb7993938f54396af5f9b4f61`.
The approved destination keeps the related proof packet with the snapshot.
The source repository keeps the historical worktrees and all earlier evidence.

## Acceptance boundary

This necessary calculation migration supplies bounded evidence for the API without host dependencies in Exit 3.
It also supplies bounded evidence of equal results for Exit 2 and B16 workflow evidence for Exit 1.
It accepts no full exit. Phase 7 stays Open at 0/4, with all four exits Pending.

D-P6-008 stays in full as a deferred, unmet obligation before Phase 10 beta acceptance.
The initial bounded Entry/Exit improvement still must have independent review and owner acceptance.
A different workload or a permitted time budget cannot replace it. Beta acceptance stays blocked while it is unmet.
D-GOV-011 and its stopped negative evidence stay unchanged.

PR #72's added direct cost and PR #73's human-interface timing and memory limitations stay visible.
PR #75's direct and profiled-caller costs, rejection and recovery observations, and unknown causes also stay visible.
All conditions to compare results and remove legacy paths stay in full.

This task changes no phase criterion, risk, output contract or release state.
Output stays private-development. Project status stays `unknown`.
The new draft must have different authority for a merge.
