# Phase 7 common straight-end extension evidence

Status: **Level 2 evidence for the bounded scope of the API and B16 caller.**

The [API instructions](../contracts/phase7-common-straight-extensions.md) define the supported records and operations.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

The implementing agent merged PR #71 into protected main at `a8e21ce320d2c4ecdac02992508389e574e51d7c`.
Its merge CI had a PASS result. The primary worktree was clean and equal to protected main on GitHub.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result.

The candidate moves the function that calculates common straight-end extensions into `tracktemplate.domain.alignment` for `tracktemplate.api`.
The `run_macro` caller uses the compatibility object before its checks of entry and exit distances.
The object changes only the new points, their `headings` values and the five specified metadata values.
The previous records, Python `list` objects and `App.Vector` values keep their identities.
The product selects seven functions together and puts previous values back after a selection error.

The API keeps the B14/B15 sequence of operations and the strict `1.0e-8` mm condition for new end points.
It calculates a new result for each operation. It does no work later and keeps no result for subsequent use.
The source does not change how the product reverses turn directions, connects station values to points or uses `build_platform_core`.
It changes no document or output contract.
B14, B15, the launcher, the frozen tool that supplies the host functions and previous contracts stay unchanged.

## Standalone and qualified FreeCAD proof

Before the product source changed, 57 B14/B15 groups gave equal complete results.
The tests used each group two times. The checks preserve the inherited result from the second operation, which can add end points again.
The groups include empty inputs, one or more tracks and equal values.

They include changed sequence, values immediately above and below the limit, and records from the main, matched and manual track functions.
Five records preserve errors and incomplete changes from incomplete internal records. The supported contract does not include those inputs.

Nine selected test sets with standalone Python had PASS results.
The test sets include calculated results from Phase 1 and the Phase 2 foundation.
They include Phase 3 routing and workflow, and Phase 4 route removal.
They also include Phase 7 centre, exit, core and common extensions.
Python accepted all fourteen changed Python files. Ruff `0.16.4` and the diff check had PASS results.

The proof for common extensions compares all metadata, point values, sequence and previous object identities.
It checks the API with no FreeCAD dependency, both operations on each host record and errors during the first and second `App.Vector` creation.
Other checks independently examine common end positions, unchanged distances across tracks, complete lengths and changed input sequence.
Here, distances across tracks are at 90 degrees to the direction of the tracks.

The position check lets values differ by `1.0e-8 + 1.0e-10` mm for the limit to add points and Python `float` error.
The check of distances across tracks lets values differ by `1.0e-10` mm. The complete B14/B15 result check needs equal values.

Only the specified routing results and their necessary fixtures changed in the older tests.
The older cases with number inputs and the contract identities stay unchanged.
The exact check of the manifest date changes with the new dated benchmark record. Its check stays exact.

Five proofs with qualified FreeCAD had PASS results with process exit status `0` and their necessary success sentinels.
They include common extensions, complete core results, exit endpoint calculation, the Phase 3 caller and the main centre result.
The proof for common extensions includes 58 groups, including an unchanged result for a platform.
It checks actual `App.Vector` values and identities and the actual caller route.
It also checks that the product rejects callers that do not use their selected functions and puts the previous function values back.
These checks leave the document state unchanged.

The qualified host profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The development tool is the `.devtools/freecad-cli` worktree at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`.
Its runtime files, fixture and preferences have the same values as the preserved setup for the checks.

## Human-interface proof and measured cost

The fixed plan used three rounds of each plain-line and connected workflow.
All six new samples had PASS results in different FreeCAD processes.
The six preserved PR #71 samples supply the same-host baseline, with the same procedure and preferences.
The merge tree has the same source as that preserved candidate.
Two older legacy records supply evidence for correct results only. The checks do not use their time values.

The checks compare all result data from the fourteen complete workflow records and give equal results.
The checks include the procedure's shape and position values, metadata, history, replacement, persistence and recovery after errors.
They do not prove that complete B-rep or export bytes are equal.
Each new sample preserves the specified fixture, preferences and seven-function route.
All six processes closed after their document checks.

The table gives the median and [minimum, maximum] for three samples in each state.
Wall and CPU values use milliseconds. RSS changes use MiB. Object values are counts.

| Action | State | Wall ms | CPU ms | RSS change MiB | Object change |
| --- | --- | --- | --- | --- | --- |
| Plain-line replace | baseline | 14004.931 [13998.313, 14012.067] | 2766.709 [2753.280, 2807.277] | 216.254 [158.668, 276.875] | 0 |
| Plain-line replace | candidate | 14030.194 [14011.884, 14034.304] | 2817.848 [2801.913, 2826.181] | 211.770 [209.312, 212.680] | 0 |
| Plain-line change back | baseline | 13158.487 [13150.002, 13159.634] | 2077.091 [2047.211, 2099.495] | 56.750 [-7.969, 58.141] | 0 |
| Plain-line change back | candidate | 13152.243 [13150.806, 13158.108] | 2109.515 [2096.630, 2137.888] | 57.059 [55.527, 57.664] | 0 |
| Connected create | baseline | 13471.792 [13464.868, 13473.691] | 2540.723 [2478.258, 2577.497] | 172.742 [163.090, 172.844] | 14 |
| Connected create | candidate | 13469.851 [13464.719, 13472.737] | 2538.318 [2505.118, 2545.670] | 164.195 [164.145, 170.504] | 14 |
| Connected edit | baseline | 13176.553 [13176.265, 13178.263] | 2213.009 [2190.589, 2222.958] | 57.492 [57.438, 64.449] | 0 |
| Connected edit | candidate | 13180.507 [13175.905, 13182.525] | 2190.195 [2170.399, 2207.225] | 57.070 [56.910, 63.883] | 0 |

The candidate's plain-line CPU medians are higher by 51.139 ms for Replace and 32.424 ms for change back.
The preserved same-host baseline ended 5,359.578 seconds before the candidate series started.
The tests did not control which file data the operating system kept in memory.
These descriptive samples give no proof that measured differences stay within accepted limits or acceptance of product performance.
Earlier differences in wall time between dates and higher RSS values stay limitations. This task does not identify their cause.

The direct checks used ten valid input groups: empty, then one, two and three generated tracks at each of three `total_angle` values.
Six pairs each used 1,000 operations per state, for 6,000 operations per state. The sequence of states changed between pairs.
Before the timer started, the tool prepared new host Python `dict`, Python `list` and `App.Vector` objects in the same way for both states.

The timer includes the work to collect inputs and calculate results, new `App.Vector` values, Python `list` changes and all five metadata writes.
The tool never uses an input again after a measured operation changed it.
All named values and their sequence, XYZ values, `headings`, previous identities and `None` results are equal for every operation.

| Direct measurement per 1,000 operations | Baseline median [minimum, maximum] ms | Candidate median [minimum, maximum] ms | Median increase |
| --- | --- | --- | --- |
| Wall | 4.934 [4.528, 5.393] | 6.184 [6.058, 6.567] | 1.250 ms, 25.33% |
| CPU | 4.940 [4.533, 5.398] | 6.183 [6.065, 6.573] | 1.243 ms, 25.16% |

Every paired direct sample has higher candidate wall and CPU values.
The added wall cost is about 1.25 microseconds per measured operation on an input group.
This measured cost stays a limitation of the source migration.
The shared process, creation of new values and uncontrolled file data kept in memory are limitations for these descriptive checks.
They supply no time values for the GUI, transactions, persistence, Validate or Export, and no accepted product performance limits.

After measurement, one different FreeCAD process opened disposable copies of the completed candidate documents for two new top-view images.
The plain-line image shows two continuous curves with common ends.
The connected image shows the two curves and their connected straight sections.

The implementing agent examined both images. The images show views of document copies.
They do not show what a person sees on the workstation screen.
The source documents and copies kept their hashes.
The tool did no product action or file-write operation again, and the process for the images closed.

## Limits and preservation

This task supplies evidence for the bounded scope in Phase 7 Exits 2 and 3 and the B16 caller in Exit 1.
It accepts no exit or product performance result. Phase 7 stays Open at 0/4.
D-P6-008, all conditions to compare results and remove legacy paths, and all recorded limitations stay in full.
Project status stays `unknown`. Output keeps private-development status.

The supported inputs are valid, different records from the functions that build the tracks.
The API calculates the complete result before the compatibility object changes the host Python `list` objects.
For incorrect records or shared input Python `dict` and Python `list` objects, the task does not claim equal incomplete changes or equal error times.

It does not claim that complete B-rep or export bytes are equal, or that a person examined the workstation screen.

The new worktree's first development-toolchain preflight for documentation found no derived STE cache.
The preserved failure classification is `environment-or-profile-defect`.
The STE lookup rebuilt the cache. Then the initial development-toolchain preflight for documentation had a PASS result.
No product, test or tool source changed for this repair.

The necessary new backup includes all eleven previous project roots, including the PR #71 local evidence.
Its checks that compare source and snapshots had PASS results.
The operating system completed the necessary writes and safely disconnected the USB file system.

The first attempt stopped before it made copies, after an incorrect substitution in the script.
The `fixture-or-harness-defect` record, scripts with errors and empty destination stay preserved.
The completed attempt uses a different destination and replaces no previous data.
The accepted September 5 restore proof still applies. The agent did not do it again.

Device removal and storage in a different place need a person at the workstation. This record claims neither action.

## Independent review

The independent review of source, tests and raw evidence has a PASS result with no findings that need action.
The reviewer checked the fifteen frozen paths for source, tests and the machine contract and the complete source and test diff.
The review includes evidence from standalone Python, qualified FreeCAD, the human interface, direct measured cost, document-copy images and QA records.
The reviewer wrote none of these changes and did not do the experiments again. This quality review did not include canonical prose.
It gives no phase, product performance, migration, output or release acceptance.

## Preserved proof identities

Raw local evidence stays in `tmp/phase7-common-straight-extensions/` in the preserved worktree.
The terminal receipt identifies each GUI record, command, sentinel and process-stop record, and all source, fixture and preference hashes.
The source/test receipt identifies the commands for standalone Python and all fifteen frozen paths for source, tests and the machine contract.
The source/test and host checks had no product proof with a FAIL result and no replacement sample.
The development tool's Git index changed as administrative metadata. Its pinned commit and runtime files stayed unchanged.

| Local record | SHA-256 |
| --- | --- |
| `implementation-frozen-sha256.json` | `1238c970d217a64f7a7660373bc4e28cd94e7640d667da62b7cd82a8d69607b6` |
| `implementation-handoff.json` | `e0a12dbd9aeed4731221ca0478f472cc3c52f1ec4fd88af38dbe7c139a7f78dd` |
| `characterization-receipt.json` | `39cc27d0fa606c1d321e9ef4ada7d0501bfa5e74e00020e7563e92852fb5d916` |
| `legacy-characterization.log` | `3b5d2e069fadd46a7c283172b45458f0e2229eba857d72331b382637edec2804` |
| `test-alignment-basis.json` | `77ea6e7ae6581c92b2f9d77ffd7d87fb5c27d8137835440fc3dcfccaddc4c89a` |
| `host-completion-receipt.json` | `550e7cba8b64bbe7c4b0907a4b2b8d952a175263ce95a9107248c50081c5dcc3` |
| `host-baseline-reuse.json` | `0f9e826dadcb40372e29f6588d76f115de08695da4c6d443e5df10755a0cdfe4` |
| `gui-regression-summary.json` | `7ed64ae9ddb770633babe63ba9f79a8e0554b06f671168dbd94ecb81a6812b56` |
| `repeated-extensions-plan.json` | `0ed903c6040d275915542eb17ab1775e1529002c79b2f6ada7e846b9565efdfe` |
| `repeated-extensions-result.json` | `f313a4ac1edd494d610ba15c0b40e8013425d5b542d4dde8655cc0d1dfaa9659` |
| `visual-capture-result.json` | `5b7bf18774663731f86c58d8077a8da7910276e70a342bf5a57f142f0f3add6f` |
| `independent-quality-review-2026-09-09.md` | `69bac80b8ead8c57295fa4558a9b276efcef74f4c745ef6325ac4dc5c67d48a0` |

The approved backup set is `2026-09-08-post-pr71-pre-phase7-next-02`.
The primary worktree keeps its receipt in `tmp/phase7-post71-backup-attempt02/terminal-backup-receipt.json`.
Its SHA-256 is `d4d4e93c58bee266ae22efae279844153fa0e9d8608828576f4da75ef9cf05c3`.
The previous attempt with a FAIL result and all earlier snapshots stay preserved.
