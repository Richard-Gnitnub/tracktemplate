# Phase 7 common straight-end extension evidence

Status: **Level 2 evidence for the bounded calculation and B16 caller.**

The [API instructions](../contracts/phase7-common-straight-extensions.md) define the supported records and operations.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

PR #71 was merged into protected main at `a8e21ce320d2c4ecdac02992508389e574e51d7c`.
Its merge CI passed. The primary checkout was clean and equal to the protected remote.
The owner's `$tracktemplate-continue` command authorises this one subsequent Level 2 result.

The candidate moves the common straight-end calculation into `tracktemplate.domain.alignment` for `tracktemplate.api`.
The existing `run_macro` caller uses the compatibility object before its entry and exit spacing checks.
The object changes only the new points, their headings and the five specified metadata fields.
Existing records, lists and vectors keep their identities.
The product selects seven functions together and puts previous values back after a selection error.

The calculation keeps the B14/B15 sequence of operations and the strict `1.0e-8` mm condition for new end points.
It calculates a fresh result on each call. It defers no work and keeps no result for subsequent use.
The source changes no turn mirroring, station mapping, platform calculation, document or output contract.
B14, B15, the launcher, frozen host loader and previous contracts stay unchanged.

## Standalone and qualified FreeCAD proof

Before the product source changed, 57 B14/B15 groups gave equal complete results.
Each group was used twice. The comparison preserves the inherited repeated-call result, which can add end points again.
The groups include empty inputs, one or more tracks and equal values.

They include changed sequence, threshold neighbours and records from existing main, matched and manual builders.
Five observations preserve errors and partial changes from incomplete internal records. Those inputs are outside the supported contract.

Nine selected standalone test sets passed.
The test sets cover Phase 1 calculation and Phase 2 foundation.
They cover Phase 3 routing and workflow, and Phase 4 route removal.
They also cover Phase 7 centre, exit, core and common extensions.
All fourteen changed Python files parsed. Ruff `0.16.4` and the diff check passed.

The common-extension proof compares all metadata, point values, sequence and existing object identities.
It checks the pure API, both calls on each host record and failures during the first and second vector construction.
Independent checks cover common end positions, unchanged normal spacing, length accounting and changed input sequence.
The position check permits `1.0e-8 + 1.0e-10` mm for the insertion limit and floating-point error.
The normal-spacing check permits `1.0e-10` mm. The complete B14/B15 result comparison requires equal values.

Only current routing expectations and their necessary fixtures changed in the older tests.
The older numerical cases and contract identities remain.
The exact manifest-date assertion changes with the new dated benchmark registration. Its check remains exact.

Five qualified FreeCAD proofs passed with exit `0` and their required success sentinels.
They cover common extensions, the complete concentric core, exit displacement, the Phase 3 caller and the main circle centre.
The common-extension proof covers 58 groups, including an unchanged platform-builder result.
It checks native `App.Vector` values and identities, the actual caller route, rejected detached callers and restored bindings.
These checks leave the document state unchanged.

The qualified profile is `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
The development bridge is the existing `.devtools/freecad-cli` checkout at `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`.
Its runtime files, fixture and preferences have the same values as the retained comparison setup.

## Human-interface proof and measured cost

The fixed plan used three rounds of each existing plain-line and connected workflow.
All six fresh samples passed in separate FreeCAD processes.
The six retained PR #71 samples supply the baseline from the same host, recipe and preferences.
The merge tree has the same source as that retained candidate.
Two older legacy records supply correctness evidence only. Their time values are excluded.

All fourteen complete workflow records give equal results in the deep semantic comparison.
The comparison includes the recipe's geometry, metadata, history, replacement, persistence and error-recovery fields.
It does not prove complete B-rep equality or equal export bytes.
Each new sample preserves the expected fixture, preferences and seven-function route.
All six instances closed after their document checks.

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
The retained baseline ended 5,359.578 seconds before the candidate series started.
The OS file cache was uncontrolled. These descriptive samples give no statistical equivalence or performance acceptance.
Earlier cross-date wall-time variation and higher RSS observations remain limitations. This task does not attribute their cause.

The direct comparison used ten valid batches: empty, then one, two and three generated tracks at each of three angles.
Six alternating pairs each used 1,000 calls per state, for 6,000 calls per state.
Each invocation received fresh host dictionaries, lists and vectors, prepared outside the timer in the same way for both states.
The timer includes input collection, the domain calculation, new `App.Vector` values, list changes and all five metadata writes.
The probe never reuses an input that a measured call has changed.
All ordered fields, XYZ values, headings, existing identities and `None` results are equal on every call.

| Direct measure per 1,000 calls | Baseline median [minimum, maximum] ms | Candidate median [minimum, maximum] ms | Median increase |
| --- | --- | --- | --- |
| Wall | 4.934 [4.528, 5.393] | 6.184 [6.058, 6.567] | 1.250 ms; 25.33% |
| CPU | 4.940 [4.533, 5.398] | 6.183 [6.065, 6.573] | 1.243 ms; 25.16% |

Every paired direct sample has higher candidate wall and CPU values.
The added wall cost is about 1.25 microseconds per measured batch call. This measured cost remains a limitation of the extraction.
The shared process, fresh allocations and uncontrolled OS file cache limit this descriptive comparison.
It supplies no GUI, transaction, save/reopen, Validate or Export timing, and no accepted performance budget.

After measurement, one separate instance opened disposable copies of the completed candidate documents for two new top-view images.
The plain-line image shows two continuous curves with common ends.
The connected image shows the two curves and their connected straight sections.

The implementing agent inspected both images. The images show copied document views. They do not show the physical workstation screen.
The source documents and copies kept their hashes. No product action or save was repeated, and the visual instance closed.

## Limits and preservation

This task supplies bounded evidence for Phase 7 Exits 2 and 3 and the existing B16 caller in Exit 1.
It accepts no exit or product performance result. Phase 7 stays Open at 0/4.
D-P6-008, all comparison and legacy-retirement conditions, and all recorded limitations stay in full.
Project status stays `unknown`. Output stays private-development.

The supported inputs are valid, separate records from the existing builders.
The API calculates the complete result before the compatibility object changes the host lists.
The task does not claim equal partial changes or error timing for malformed records or shared input dictionaries and lists.

It does not claim complete B-rep equality, equal export bytes or observation of the physical screen.

The new worktree's first documentation preflight found no derived STE cache.
The retained classification is `environment-or-profile-defect`.
The existing cache rebuild completed, then the original documentation preflight passed.
No product, test or tool source changed for this repair.

The required new backup covers all eleven previous project roots, including the PR #71 local evidence.
Its source and snapshot comparisons passed. The USB was flushed and safely unmounted.

The first attempt stopped before copying after an incorrect script substitution.
The `fixture-or-harness-defect` record, failed scripts and empty destination remain preserved.
The successful attempt uses a different, non-overwriting destination.
The accepted September 5 restore proof remains current and was not repeated.
Physical disconnection and separate storage require an on-site action; neither is claimed.

## Independent review

The separate read-only source, test and raw-evidence review has a PASS result with no actionable findings.
The reviewer checked the fifteen frozen implementation paths and the complete source and test diff.
The review covers the standalone, qualified FreeCAD, human-interface, direct-cost, copied-document visual and QA registration evidence.
The reviewer did not author these changes or repeat the experiments. Canonical prose was outside this quality review.
This review gives no phase, performance, migration, output or release acceptance.

## Retained proof identities

Raw local evidence remains under `tmp/phase7-common-straight-extensions/` in the persistent worktree.
The terminal receipt maps the individual GUI records, commands, sentinels, shutdown records, source, fixture and preference hashes.
The implementation receipt maps the standalone commands and all fifteen frozen source, test and machine-contract paths.
The implementation and host checks had no failed product proof or replacement sample.
The bridge's Git index changed as administrative metadata. Its pinned commit and runtime files stayed unchanged.

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
The primary checkout keeps its receipt in `tmp/phase7-post71-backup-attempt02/terminal-backup-receipt.json`.
Its SHA-256 is `d4d4e93c58bee266ae22efae279844153fa0e9d8608828576f4da75ef9cf05c3`.
The previous failed attempt and all earlier snapshots remain.
