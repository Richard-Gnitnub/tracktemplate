# Phase 7 `build_concentric_core` checks — 2026-09-08

Status: **Level 2 evidence for the bounded scope. Phase 7 stays Open at 0/4.**

The [current evidence](../current/PHASE_EVIDENCE.md) gives the owner view.
The [API instructions](../contracts/phase7-concentric-core.md) define this task.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Source and scope of the checks

The implementing agent merged PR #70 into protected main at
`1be47bf38fa00692c60ea2fc03f91ab174801bf2`.
The merged tree is the same as the reviewed `9204e001a558d7ad3b1c0adfbfe6fc4cd3199eff` tree.
The owner's `$tracktemplate-continue` command authorises one subsequent Level 1 or Level 2 result with authority from D-GOV-004.
D-P7-001 keeps Phase 7 Open. D-P6-008 stays unchanged in full.

The complete `build_concentric_core` operation now uses `tracktemplate.api`.
Its result includes every point, `headings` value and metadata value for the bounded scope.
The `_ConcentricCoreAdapter` object changes only its points to `App.Vector` values for B15 compatibility.
The actual `run_macro` and `prepare_track_alignment` callers use this object.
The main, matched-spacing and manual-length routes keep their results.

The source change keeps the 3 mm point interval, sequence of operations,
end point corrections, diagnostics and result sequence.
The `build_platform_core` function and its initial helper functions stay unchanged.
The source does not keep results for subsequent use or calculate them in a subsequent operation.
The complete `build_concentric_core` operation includes the change to `App.Vector` values.

## Checks of calculated results and source

Before the source change, the implementing agent compared 184 complete results
and nine invalid cases from B14 and B15.
The checks include the sequence of all result items.
The complete result with this sequence has SHA-256
`93f27c8f0a7068a3c0939fe63dda0255308e7cb9e6426776ad2814dbf8393efa`.
Both accepted source hashes matched their records.

The new API results are equal to B14 and B15 for all 184 cases.
All nine invalid cases keep the same error type and diagnostic.
The tests include unequal and zero transition lengths, `GEOMETRY_TOLERANCE`,
zero `circular_length`, the `circular_angle` limit and incomplete `circle_centre` inputs.
Other tests independently check the results after a move and the distance from `circle_centre`.
These tests also have PASS results.

The source check lets only internal names change and XY values replace `App.Vector` construction.
All thirteen named result items and their sequence stay unchanged.
The `points` and `headings` values keep their sequence.
Python can use `tracktemplate.domain.alignment` and the public API with no FreeCAD or Qt dependency.

Eight selected test sets with standalone Python have PASS results.
These include calculated results from Phase 1, Phase 2 package structure and both Phase 3 checks that compare results.
They also include Phase 4 route removal and the Phase 7 centre, exit and core test sets.

Python accepts all eleven changed Python files.
Ruff 0.16.4 and the diff check have PASS results.
The implementing agent did the initial core and Phase 4 checks again with their added checks intact.
Their final test hashes and success outputs are in the frozen receipt.

The directly dependent tests now check product schema `4` and six selected functions.
They keep the historical input cases and contract identities.
Their new B15 fixtures use the actual `build_concentric_core` caller routes.
The frozen `bind_transition_functions` method stays on its development route to compare results.
The new product owns its six-function selection and checks to put previous values back.

## Qualified FreeCAD checks

Four checks with the qualified host profile have PASS results, process exit status `0` and their exact success sentinels:

| Test | Proof for the bounded scope |
| --- | --- |
| `freecad_validate_phase7_concentric_core.py` | Complete results, `App.Vector` types, actual callers and recovery after an error |
| `freecad_validate_phase7_clothoid_exit.py` | Exit endpoint calculation and the selected route |
| `freecad_validate_phase3_transition_slice.py` | Preserved complete caller snapshots and the route to compare results |
| `freecad_validate_phase7_main_circle_centre.py` | `main_circle_centre` results and the selected route |

The exact host profile for FreeCAD is
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The complete results are equal to B15, including exact XY values and zero Z values.
The tests examine the main, matched-spacing and manual-length operations below `_ConcentricCoreAdapter`.
The product rejects functions and callers that do not use their selected APIs before the workflow starts.
It puts the six previous values back after a selection error.
These checks make no document change.

## FreeCAD human-interface checks

Six new samples completed in isolated FreeCAD processes.
Each round used the plain-line edit procedure, then the connected-straight procedure.
The fixed plan kept three samples for each workflow.
Every sample has a completed record, a PASS result from the checks and a stopped process.
The tests replaced no sample with a FAIL result.
The source, fixture and preferences stayed unchanged.

The same-host baseline uses six PR #70 candidate samples with PASS results again.
Their product source is the same as the protected main tree.
The qualified host profile, fixture, preferences and procedure are the same.

The same-host baseline finished at 20:27:36 UTC. The new series started at 21:37:56 UTC.
The gap is 4,220.321 seconds. All samples from the same-host baseline are before the new samples.
The tests did not control which file data the operating system kept in memory.

The checks compare all result data from six same-host baseline records, six new records and two preserved legacy records.
All fourteen have equal workflow results.
The checks do not include the tool's specified variable fields.
They include history, persistence, replacement, recovery after errors and the meaning of values.
The legacy records supply evidence for correct results only.
The checks do not use their time values.

Each cell below gives the median and the minimum–maximum range for three samples.
The procedure's `rss_delta_mb` value gives RSS in MiB.
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
All wall-time and RSS ranges include common values.
The return-to-left CPU ranges have no common value. The other CPU ranges include common values.

These small descriptive samples give no accepted limits for measured values or proof that measured differences stay within accepted limits.
The previous centre and exit reports keep their higher memory values and variable time values.
These checks give no acceptance of product performance or credit towards D-P6-008.

## Cost of the complete `build_concentric_core` operation

The recorded plan compares the old B15 `build_concentric_core` operation with the complete new operation.
It includes creation of XY values, all metadata and the change to actual FreeCAD `App.Vector` values.
The five previously selected functions are the same in both states.
Both states keep all calculated results until the timer stops, with the same added work to collect them.
The checks compare exact results before or after the measured operations.

The measurement uses 27 cases whose number inputs give `True` with `math.isfinite`, each ten times, and six pairs of samples.
The sequence changes between pairs. Each state does 1,620 complete operations.
Every operation gives equal metadata, item sequences and XYZ values.

The process with the qualified host profile returned process exit status `0` with its exact success sentinel.
It changes no document. All measured FreeCAD GUI processes stopped before this measurement.

Each sample contains 270 operations. Values below are milliseconds.

| Measurement | Baseline median (range) | Candidate median (range) | Median difference |
| --- | --- | --- | --- |
| Wall time | 79.181 (77.772–104.627) | 77.105 (73.083–103.320) | −2.076, −2.621% |
| Process CPU | 79.181 (77.568–104.633) | 76.985 (73.070–103.317) | −2.195, −2.773% |

The ranges include common values.
Creation of new values and uncontrolled data kept for subsequent use limit these checks.
These results are evidence from regression tests for the bounded scope.
They accept no product performance result.
They do not start a stopped experiment again or change any measurement profile or comparison rule.

## Inspection of results in FreeCAD files

After measurements, a different FreeCAD process opened disposable copies of two completed results.
It did no product action or operation to write a document to a file.
The hashes of the source FCStd files and their copies stayed unchanged.
Both documents closed and the process stopped.

The primary agent and independent quality reviewer examined the two top-view images.
They show the curved pair and the connected straight sections with no visible defect at this scale.
The tool made these GUI images. This record does not claim that a person examined the workstation screen.
The images and checks of result meaning do not prove that complete B-rep or export bytes are equal.

## Preserved evidence and preparation

The [previous exit report](2026-09-08-phase7-clothoid-exit-regression.md)
keeps its initial results, limitations and repair history.
This task does not do those experiments again to make new historical records.
It uses their exact source again for the same-host baseline and applicable checks of raw data.

The implementing agent used the approved backup schedule after the merge of PR #70.
A new backup set includes the primary project and all nine sibling worktrees that were present at that time.
The checks that compare source and snapshots have PASS results.
Every previous snapshot stays unchanged.

The accepted September 5 restore proof still applies. The agent did not do it again.
The operating system completed the necessary writes and safely disconnected the USB file system.
This record does not claim that a person removed the device or put it in a different place.

The new worktree initially had no validated local STE cache.
The development-toolchain preflight for documentation stopped with `success-sentinel-missing`.
The direct diagnostic was `cache-missing`.

The author classified this as `environment-or-profile-defect` before preparation continued.
The STE lookup completed its rebuild of the cache.
Then the initial development-toolchain preflight had a PASS result.
No maintained tool or official source identity changed.
The product test records show no failure in this cycle.

Three inspection failures were only in temporary inspection or receipt commands.
The host receipt initially checked that the `.git/index` bytes in the copy of `.devtools/freecad-cli` stayed the same.
Usual Git inspection changed that Git index file.
Before the receipt correction, the host agent classified this as `fixture-or-harness-defect`.

The agent validated all other 67 entries and the exact commit for `.devtools/freecad-cli`.
Then the initial terminal checks had PASS results.
The agent did not do a host sample again.

The quality reviewer initially checked for a named JSON sentinel from the GUI tool.
That tool records completion in `run.json` and prints the evidence path.
The author initially parsed the STE pre-check output with its specified prefix still attached.
That pre-check had a PASS result.

Before the command corrections, the agents classified both command errors as `fixture-or-harness-defect`.
The initial preserved outputs then gave PASS results in those inspections.
No maintained source, test, requirement or proof changed for these corrections.

## Independent review

The independent reviewer of source and tests gave a PASS result with no finding that needed action.
The reviewer checked the complete frozen source and tests and the raw evidence.
The reviewer previously supplied read-only selection advice but wrote no source, tests or host proof.
The host agent previously supplied architecture and API advice.
Their receipts identify these earlier responsibilities.

Canonical prose follows its single Documentation Review.
No source repair was necessary.

## Evidence identities

Local raw evidence stays in `tmp/phase7-concentric-core/` in
`/home/richard/PycharmProjects/TrackTemplateMacro-worktrees/phase7-concentric-core`.
Commits do not include it.
The manifests keep exact commands, source hashes, raw paths, profiles and success outputs.
They also keep the initial failures and their failure classifications.

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

The visual receipt identifies both document copies and both PNG files.
The images are in `benchmark-output/freecad-bridge/phase7-concentric-core-visual/`.

## Authority and remaining limits

For the bounded scope in Phase 7 Exit 3, this task reduces the dependency on B15 to calculate results.
It supplies evidence for equal complete results for Exit 2 and workflow evidence for the bounded scope in Exit 1.
It admits no complete phase exit. Phase 7 stays Open at 0/4.

The remaining station and multiple-track migration scope is unchanged.
All conditions to compare results and remove legacy paths stay in full.
The source change supplies no acceptance of product performance, output clearance or release acceptance.
Project status stays `unknown`. Output keeps private-development status.
D-P6-008 stays a deferred, unmet obligation before Phase 10 beta acceptance.
