# Phase 7 concentric-core comparison — 2026-09-08

Status: **Bounded Level 2 evidence. Phase 7 stays Open at 0/4.**

The [current evidence](../current/PHASE_EVIDENCE.md) gives the owner view.
The [API instructions](../contracts/phase7-concentric-core.md) define this task.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Source and comparison scope

PR #70 was merged into protected main at
`1be47bf38fa00692c60ea2fc03f91ab174801bf2`.
The merged tree equals the reviewed `9204e001a558d7ad3b1c0adfbfe6fc4cd3199eff` tree.
The owner's literal `$tracktemplate-continue` command authorises one subsequent
Level 1 or Level 2 result under D-GOV-004.
D-P7-001 keeps Phase 7 Open. D-P6-008 stays unchanged in full.

The complete `build_concentric_core` calculation now uses the modular API.
Its result includes every point, heading and metadata value for the bounded scope.
A small object in the B15 compatibility module converts only its points to `App.Vector` values.
The actual `run_macro` and `prepare_track_alignment` callers use this object.
The existing main, matched-spacing and manual-length routes keep their results.

The source change keeps the 3 mm point interval, sequence of operations,
endpoint corrections, diagnostics and result order.
The platform calculation and its original helpers stay unchanged.
The source has no new cache or later calculation stage.
The conversion occurs during the complete core call.

## Calculation and source checks

Before product movement, the implementing agent compared 184 complete ordered
results and nine invalid cases from B14 and B15.
The complete ordered result has SHA-256
`93f27c8f0a7068a3c0939fe63dda0255308e7cb9e6426776ad2814dbf8393efa`.
Both accepted source hashes matched their records.

The new domain results equal both oracles for all 184 cases.
All nine invalid cases keep the same exception type and diagnostic.
The tests cover unequal and zero transition lengths, the geometry tolerance,
zero circular length, the circular-angle limit and incomplete centre inputs.
Independent translation and circle checks also pass.

The source comparison permits only internal-name changes and replacement of
vector construction with neutral XY values.
All thirteen result keys and their order stay unchanged.
The point and heading lists keep their order.
The domain and public API import with no FreeCAD or Qt dependency.

Eight selected standalone suites have PASS results.
These include Phase 1 calculation, Phase 2 package structure and both Phase 3 comparisons.
They also include Phase 4 route retirement and the Phase 7 centre, exit and core suites.
All eleven changed Python files parse. Ruff 0.16.4 and the diff check pass.
The implementing agent ran the original strengthened core and Phase 4 checks again.
Their final test hashes and success outputs are in the frozen receipt.

The directly affected tests now check product schema `4` and six selected functions.
They keep the historical calculation cases and contract identities.
Their new B15 fixtures exercise the actual core caller routes.
The frozen `bind_transition_functions` method stays on its existing development comparison route.
The new product owns its six-function selection and recovery checks.

## Qualified FreeCAD checks

Four qualified checks have PASS results, exit status `0` and their exact success sentinels:

| Test | Bounded proof |
| --- | --- |
| `freecad_validate_phase7_concentric_core.py` | Complete results, vector types, actual callers and failure recovery |
| `freecad_validate_phase7_clothoid_exit.py` | Exit calculation and the selected route |
| `freecad_validate_phase3_transition_slice.py` | Preserved complete caller snapshots and comparison route |
| `freecad_validate_phase7_main_circle_centre.py` | Centre calculation and the selected route |

The exact FreeCAD profile is
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The complete results equal B15, including exact XY values and zero Z values.
The tests observe the main, matched-spacing and manual-length calls below the conversion.
Detached calculations and callers are rejected before workflow launch.
The six previous values return after a failed selection.
These checks make no document mutation.

## FreeCAD human-interface comparisons

Six new samples completed in isolated FreeCAD instances.
Each round ran the plain-line edit recipe, then the connected-straight recipe.
The fixed plan kept three samples for each workflow.
Every sample has a completed record, successful comparison and stopped instance.
No failed sample was replaced. The source, fixture and preferences stayed unchanged.

The same-host baseline reuses six successful PR #70 candidate samples.
Their product source equals the current protected main tree.
The qualified profile, fixture, preferences and recipe are the same.
The baseline finished at 20:27:36 UTC. The new series started at 21:37:56 UTC.
The gap is 4,220.321 seconds. All baseline samples precede the new samples.
The operating-system file cache was not controlled.

The deep comparison includes six baseline records, six new records and two
preserved legacy records. All fourteen have equal workflow results.
Only the comparison tool's declared variable fields are excluded.
History, save/reopen, replacement, failure recovery and semantic values stay in the comparison.
The legacy records supply correctness evidence only. Their time values are not used.

Each cell below gives the median and the minimum–maximum range for three samples.
The RSS unit is MiB, as calculated by the existing recipe's `rss_delta_mb` field.
Positive RSS values mean an increase during the action.

| Action | Measurement | Same-host baseline | Candidate |
| --- | --- | --- | --- |
| Replace left with right | Wall time, ms | 14008.870 (13996.738–14010.248) | 14004.931 (13998.313–14012.067) |
| Replace left with right | Process CPU, ms | 2784.648 (2780.225–2798.886) | 2766.709 (2753.280–2807.277) |
| Replace left with right | RSS change, MiB | 216.086 (212.219–262.887) | 216.254 (158.668–276.875) |
| Return to left | Wall time, ms | 13152.361 (13150.175–13157.839) | 13158.487 (13150.002–13159.634) |
| Return to left | Process CPU, ms | 2102.422 (2100.399–2118.414) | 2077.091 (2047.211–2099.495) |
| Return to left | RSS change, MiB | 57.746 (51.113–58.824) | 56.750 (-7.969–58.141) |
| Create connected pair | Wall time, ms | 13469.298 (13463.217–13473.184) | 13471.792 (13464.868–13473.691) |
| Create connected pair | Process CPU, ms | 2542.661 (2522.942–2574.839) | 2540.723 (2478.258–2577.497) |
| Create connected pair | RSS change, MiB | 170.414 (136.402–171.844) | 172.742 (163.090–172.844) |
| Edit connected lengths | Wall time, ms | 13180.336 (13176.323–13183.188) | 13176.553 (13176.265–13178.263) |
| Edit connected lengths | Process CPU, ms | 2179.277 (2171.672–2270.924) | 2213.009 (2190.589–2222.958) |
| Edit connected lengths | RSS change, MiB | 57.742 (56.676–58.137) | 57.492 (57.438–64.449) |

Both states add fourteen objects when they create the connected pair.
The other three actions have zero object-count change in every sample.
All wall-time and RSS ranges overlap.
The return-to-left CPU ranges do not overlap; the other CPU ranges overlap.
These small descriptive samples establish no numerical budget or statistical equivalence.
The previous centre and exit reports keep their higher memory and variable time observations.
This comparison gives no performance acceptance or credit towards D-P6-008.

## Complete core-call cost

The recorded plan compares the old B15 core call with the complete new call.
It includes XY allocation, all metadata and conversion to actual FreeCAD vectors.
The five previously selected calculations are identical in both states.
Both states use the same collection overhead.
Exact result comparisons occur outside the timed blocks.

The run uses 27 finite cases, ten repetitions and six pairs of samples.
The order alternates between pairs. Each state makes 1,620 complete calls.
Every call gives equal ordered metadata and XYZ values.
The qualified process returned exit status `0` with its exact success sentinel.
No document is changed. All measured GUI instances had stopped before this run.

Each sample contains 270 calls. Values below are milliseconds.

| Measurement | Baseline median (range) | Candidate median (range) | Median difference |
| --- | --- | --- | --- |
| Wall time | 79.181 (77.772–104.627) | 77.105 (73.083–103.320) | −2.076; −2.621% |
| Process CPU | 79.181 (77.568–104.633) | 76.985 (73.070–103.317) | −2.195; −2.773% |

The ranges overlap. The retained allocation and uncontrolled cache state limit this comparison.
These observations are bounded regression evidence. They accept no performance result.
They do not reopen a stopped experiment or change a measurement rule.

## Inspection of saved results

After measurements, a separate FreeCAD instance opened disposable copies of two completed results.
It made no product action or save. The source and copied FCStd hashes stayed unchanged.
Both documents closed and the instance stopped.

The primary agent and independent quality reviewer inspected the two top-view images.
They show the curved pair and the connected straight sections with no visible anomaly at this scale.
These are automated GUI images. No physical workstation screen observation is claimed.
The images and semantic comparisons do not prove complete B-rep or exported-byte equivalence.

## Retained evidence and preparation

The [previous exit report](2026-09-08-phase7-clothoid-exit-regression.md)
keeps its original results, limitations and repair history.
This task does not repeat those experiments to reconstruct history.
It reuses their exact source for the same-host baseline and applicable raw comparisons.

The approved backup schedule ran after integration of PR #70.
A new non-overwriting set covers the primary project and all nine existing sibling worktrees.
Its source and snapshot comparisons pass. Every previous snapshot remains.
The accepted September 5 restore proof stays current and was not repeated.
The USB was flushed and safely unmounted. Physical disconnection and separate storage are not claimed.

The new worktree initially had no verified local STE cache.
Documentation preflight stopped with `success-sentinel-missing`.
The direct diagnostic was `cache-missing`.

The author classified this as `environment-or-profile-defect` before preparation continued.
The existing cache rebuild completed, then the original preflight passed.
No maintained tool or official source identity changed.
Product tests have no observed failure in this cycle.

Three inspection failures affected only temporary inspection or receipt commands.
The host receipt initially required the copied bridge's `.git/index` bytes to stay identical.
Normal Git inspection had refreshed that administrative file.
The host agent classified this as `fixture-or-harness-defect` before correcting the receipt check.
All other 67 entries and the exact bridge commit were verified.
The original terminal checks then passed. No host sample was repeated.

The quality reviewer initially expected a named JSON sentinel from the GUI runner.
That runner records completion in `run.json` and prints the evidence path.
The author initially parsed the successful STE precheck output without removing its declared prefix.
Both command errors were classified as `fixture-or-harness-defect` before their inspection commands were corrected.
The original retained outputs then passed those inspections.
No maintained source, test, rule or proof changed for these corrections.

## Independent review

The independent source and test reviewer gave a PASS result with no actionable finding.
The reviewer checked the complete frozen implementation and the raw evidence.
The reviewer previously supplied read-only selection advice but authored no implementation or host proof.
The host agent previously supplied architecture and API advice.
These earlier responsibilities are disclosed in their receipts.
Canonical prose follows its separate, single Documentation Review.
No source repair pass was needed.

## Evidence identities

Local raw evidence stays outside commits under `tmp/phase7-concentric-core/` in
`/home/richard/PycharmProjects/TrackTemplateMacro-worktrees/phase7-concentric-core`.
The manifests keep exact commands, source hashes, raw paths, profiles and success outputs.
They also keep the original failures and their classifications.

| Local evidence file | SHA-256 |
| --- | --- |
| `implementation-frozen-sha256.json` | `cb280108e5b6f0767ba51a4b532df9f32692b9e5e6d2b0371b3e12d636370f86` |
| `implementation-handoff.json` | `8fc5f0e87e2e442807ce8251498e01a5c1afd0371c2b377ff3c8b5ab8fda0c3c` |
| `gui-candidate-source.json` | `5a00ff0cf1b976eae6ab3a125090c3d835b18ce63296036ad9ebe09ada8f706b` |
| `host-baseline-reuse.json` | `7c06aaf9dc7ba02f14381be9c9e24f15aee00429c644adcdf18f6edf38b8ff59` |
| `host-completion-receipt.json` | `da98a281e33d5032db5d53a25f1195dc52108205976257219b3ce1b8d6bf09d2` |
| `gui-regression-summary.json` | `4f3c467106fbee0459d80610f3eef328884264008c74c013634da073889f95c4` |
| `repeated-core-result.json` | `52fa44e4c1547974388dc86a6dae89ed137fa01ae4cab0408082c2870bae0eef` |
| `visual-capture-result.json` | `bd3fb8a9dc5a17a5c8a74ddde4b2ff7af797ad586cc762c8c1dfdb0850e4881e` |
| `quality-review.md` | `4f3e97a63fd0720e3d3a1e8f3b697072bb132de1e60816d89719c4c879c839a8` |

The visual receipt identifies both copied documents and both PNG files.
The images are under `benchmark-output/freecad-bridge/phase7-concentric-core-visual/`.

## Authority and remaining limits

This task reduces the bounded calculation dependency under Phase 7 Exit 3.
It supplies full calculation comparison evidence for Exit 2 and bounded workflow evidence for Exit 1.
It admits no complete phase exit. Phase 7 stays Open at 0/4.

The remaining station and multiple-track migration scope is unchanged.
The existing comparison and legacy-retirement conditions stay in full.
The source change supplies no performance acceptance, output clearance or release acceptance.
Project status stays `unknown`; output stays private-development.
D-P6-008 remains a deferred, unmet obligation before Phase 10 beta acceptance.
