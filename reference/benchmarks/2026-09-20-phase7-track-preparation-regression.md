# Phase 7 evidence for track alignment preparation

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-track-preparation.md) define how the
functions calculate results and make FreeCAD vectors. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and exit status.

## Scope and source

The source state is protected main
`7454a09c86f60e307f2fceb2a27f12d18dd679f0`, after integration of PR #81.
It contains the accepted integration of the PR #80 platform-core result.
The owner's Phase 7 continuation instruction authorises this one bounded
Level 2 result. D-GOV-004 supplies the workflow, and D-P7-001 keeps the phase
scope. This task gives no phase or performance acceptance.

The B14 and B15 definitions of `signed_side_factor`,
`effective_constant_radius`, and `prepare_track_alignment` are equal. Their
source text together has 7,151 bytes and SHA-256
`8586b9b3f5bbfc1ad2b73ed1260cee6eb2743a7db0e6a6389fa20106f0f4b2cd`.
The definitions occupy lines 7957 through 8171. The task changes no part of
these two reference files.

The three functions use `tracktemplate.domain.alignment` through
`tracktemplate.api`. The B16 `run_macro` caller uses
`_PrepareTrackAlignmentAdapter` and the modular `signed_side_factor` function.
The adapter changes only new XY points to native `App.Vector` values with Z
equal to zero. The routing record uses schema `11` and the identity
`tracktemplate:phase7:track-preparation:1`. The product selects eighteen
functions together and validates 39 caller identities.

After an error in this selection, the product puts previous values back. It
removes a new name when no previous value was present.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `93ecac04fc0d09b70046fadf820edaa9c6845a2d30dfd3c0c5a855f9977760c1` |
| `tracktemplate/api.py` | `9c7c757945b3d8e3d0c56eb9f12caa238e5551bcbfea424df620e3630a257ed6` |
| `tracktemplate/compatibility/transition_workflow.py` | `8b546bc892aff6fecc073b10af44bfb5681114bf9d68ca5a8ff4e814be866e8b` |

The product identities did not change during the repairs to tests. They are
also equal to those in the API proof on FreeCAD and the GUI source manifest.

## Function, caller, and lifecycle evidence

The standalone Python proof compares six valid cases and fifteen invalid
cases with B14 and B15. The six valid cases use each of the three
`alignment_mode` values and the two `side` values. The proof preserves the
exact names, the five inputs in sequence, all operations, units, `frame`,
tolerances, and all diagnostics.

It validates result sequence and new point and collection identities. It also
validates the identity of `config`, its sequence of changes, and preservation
of `main_alignment`. It compares all cases in the earlier platform-transition
characterisation. The import proof rejects FreeCAD and Qt dependencies.

The routing proof validates the selected dependencies and the actual
`run_macro` operation. It validates the FreeCAD vectors, rejection of mixed
selections, and recovery without a partial change. The API proof on FreeCAD
validates all six valid cases and fifteen invalid cases. It validates exact
`App.Vector` results and preservation of document state. It uses the qualified
host profile from D-GOV-019:
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2`.

The standalone Python aggregate after recovery has PASS results for all 73
tracked validators at that stage. The transition preflight, persistence,
Coin scene, and Edit lifecycle checks have PASS results with their necessary
sentinels. The project also keeps the B16 routing proof on FreeCAD. After the
authorised change to its comparison `dict`, that proof gave a PASS result.
These results identify the source bytes that they validate. Final
deterministic validation and CI must validate the candidate for publication.

## Initial FAIL results and bounded repairs

The first two repairs changed inputs for operations that should give results
without errors. Those inputs could not give the necessary results. The repairs
also changed fixtures for the sequence of errors. Those defects have the
classification `fixture-or-harness-defect`.

Source-and-test repair accounting stays 2/2.
Five owner-authorised exceptions changed only tests. All five exceptions are
consumed:

1. The project changed the `minimum_radius` fixture width from 1300.0 to
   1309.0. The measured rejection interval is 1308.394511397778 through
   1310.0 mm.

2. The project put two dependency names in the sequence from the JSON data.

3. The project made two standalone Python comparisons agree with the current
   product route.

4. The project changed only the comparison `dict` in the B16 proof on FreeCAD.
   The `dict` then agreed with schema `11`, the current API identity, and
   eighteen selected functions.

5. After independent review, the project changed two fixtures for FreeCAD.
   It removed the obsolete assertion for the previous `prepare_track_alignment`
   host value. For endpoint instrumentation, it temporarily changed values in
   `tracktemplate.domain.alignment` and then put the previous values back.

The first exception repairs a fixture. The next three repair incorrect
comparisons or comparisons whose requirements have changed. These three have
the canonical classification `test-or-oracle-defect`.

The last exception repairs an obsolete comparison and inconsistent
instrumentation for valid inputs. The comparison has the classification
`test-or-oracle-defect`. The instrumentation has the classification
`fixture-or-harness-defect`. The project keeps the earlier classification
wording in the raw evidence. The completion data identify the canonical
classes.

No exception changes the 2/2 allowance or gives another repair pass. No product
source changed during a repair or exception.

The initial FreeCAD matrix used ten processes. Its result is
**8 PASS / 2 FAIL**. The earlier 10/10 claim was incorrect. FreeCADCmd reported
exceptions and then returned zero. The wrapper did not validate the necessary
success sentinel.

Independent review found the missing sentinels and gave a BLOCKED verdict.
The project preserves all command output, the sentinel audit, and that verdict.

The clothoid-exit proof used a function that was no longer the selected
dependency of `prepare_track_alignment`. The concentric-core proof kept an
obsolete check of the host caller. It also used the same instrumentation
without the full set of selected dependencies.

The fifth exception changed only those two test files. The project ran each
initial command one time after those changes. Each command gave its necessary
success sentinel and reported no exception. The two proofs gave PASS results.
These results do not change the initial matrix to 10/10. The other eight
results still apply because their source and product identities did not change.

The `phase7-track-alignment-preparation` worktree initially had no ignored STE
source or cache. The project
supplied the exact source. A difference in the cache inputs then made the
rebuild command necessary. Documentation preflight subsequently gave a PASS
result. This condition has the classification `environment-or-profile-defect`.
The project keeps the earlier raw diagnostic and classification wording.

It consumed no product repair pass.

## Real-GUI comparison and descriptive resource values

The comparison baseline for current main is the PR #80 candidate run. Its raw
data have SHA-256
`828db0dc2057b09ee70279331cc4fef1d5d2d84317b95439d2d61ededb84fdfc`.
Current main's product files are equal to that comparison baseline. PR #81
changed only inspection tooling. The task did not run the baseline again.

One new process for the candidate used the same D-GOV-019 qualified host
profile, scenario, fixture, and bridge pin
`660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`. The fixture hash stayed
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The process made a track with `Platform widening`. It used Undo and Redo,
changed spacing, and used Undo and Redo again.

The process then rejected infeasible spacing. It saved and closed the
document. It opened the document again and did the cleanup.

The candidate raw data have SHA-256
`22495680e52cc65e05e3e8b6e6776ca467fb583d19c39ba1a30e6cfd4ba33629`.
Each field for product semantics is equal, with zero differences. The common
digest is
`66dd4bc2b76c3c732db519d003c440e12194004cfad210e380cb5fc7cba4187e`.
The project put the previous preferences back, closed all documents, and
stopped the exact Flatpak instance. The source, fixture, and Git-diff guards
have PASS results.

The GUI run started before the independent reviewer reported the FAIL results
in the matrix. The run completed safely. The project kept its evidence. That
evidence did not give PASS results to the two FreeCAD proofs. The repairs
after that run changed only tests. Thus, the GUI product and fixture identities
still apply.

Each row below compares one earlier sample with one new sample. The difference
is candidate minus baseline. Time uses milliseconds. RSS change uses MiB.

| Action | Metric | Baseline | Candidate | Difference | Difference as percentage of baseline |
| --- | --- | ---: | ---: | ---: | ---: |
| Create | Wall time, ms | 2770.682 | 14183.750 | +11413.068 | +411.92% |
| Create | CPU time, ms | 2606.785 | 2541.303 | -65.482 | -2.51% |
| Create | RSS change, MiB | 162.914 | 161.695 | -1.219 | -0.75% |
| Edit | Wall time, ms | 2048.499 | 13680.608 | +11632.109 | +567.84% |
| Edit | CPU time, ms | 2174.326 | 2198.185 | +23.859 | +1.10% |
| Edit | RSS change, MiB | 49.734 | 55.230 | +5.496 | +11.05% |
| Reject infeasible spacing | Wall time, ms | 350.971 | 2215.433 | +1864.463 | +531.23% |
| Reject infeasible spacing | CPU time, ms | 304.644 | 243.652 | -60.993 | -20.02% |
| Reject infeasible spacing | RSS change, MiB | 0.395 | 0.402 | +0.008 | +1.98% |
| Save, close and reopen | Wall time, ms | 829.965 | 570.672 | -259.293 | -31.24% |
| Save, close and reopen | CPU time, ms | 928.100 | 872.793 | -55.307 | -5.96% |

Create, Edit, and rejection wall times increased. The samples occurred at
different times. The task did not control operating system cache or scheduling.
RSS includes the full process and does not identify individual allocations.
These values are descriptive observations. They do not show a typical
performance change and give no performance acceptance.

The task selects no optimisation from these values. D-P6-008 stays unmet and
has no change.

The proof does not compare physical screen pixels, physical-platform results,
sectioning results, or export bytes. Actions after the first action in the
same process give correctness evidence. They do not give a different series
for warm reuse performance.

## Independent quality review

Independent quality review of the source and tests after the repairs has a
PASS result. It has no unresolved source or test findings. The reviewer
examined the full source and test change, initial FAIL results, sentinels
after repairs, product identities, and GUI semantics. The review identifies
this Level 2 result as necessary enabling work. It gives no exit acceptance.

The project preserves the initial BLOCKED verdict in full. The new receipt is
`tmp/phase7-track-preparation/final-quality-review-01.md`, with SHA-256
`fcf4fbd6d8f56f4af9d4d8211127c1ec0ed29f713e6d0ae570a95bbd9a2bc063`.
It records all 29 file identities from that review. Final deterministic
validation and exact-head CI are necessary before draft publication is complete.

## Evidence identities and acceptance limits

The paths below are relative to `tmp/phase7-track-preparation/` in the original
`phase7-track-alignment-preparation` worktree. That ignored directory contains
the raw evidence and the final quality-review receipt. The project keeps full
stdout, stderr, and manifests there for targeted retrieval. It preserves the historical FAIL
results with the PASS results after repairs.

| Evidence | Relative path | SHA-256 |
| --- | --- | --- |
| Focused standalone proof | `focused-standalone-05-owner-exception/stdout.log` | `889959ee0a6b2046e7316cebe8bee56d26626f2ff776ec43c15c4db61aaf2cae` |
| Focused qualified proof | `focused-freecad-01/result.json` | `e57cd893656a75eaf270eebf8e4e6015aaee706205d2095d4d3764e9d6f59382` |
| Recovered standalone contracts | `standalone-contracts-owner-exception-03/stdout.log` | `b1b9049484ae7fcfe26093f7b3d799bddfcbb3d6d0cf47dda1b989dff7293720` |
| Remaining transition stages | `remaining-transition-01/stdout.log` | `54d4fe7f40c80a6a1033f2239658af60fdc981f6bae7b4a0a9fcdab6664116f2` |
| Qualified routing dictionary correction | `qualified-routing-owner-exception-04/results.json` | `3ec2203d2b3bfa95df16ef692d5a54c5d2ff7f9d776ac3a5bc03156a197b2578` |
| Original matrix sentinel audit | `review-blocker-01/matrix-sentinel-audit.json` | `e519aea136361efa828931cf2fdaceb216068e65290f7b4f8a44cdc763809757` |
| Original blocked independent review | `review-blocker-01/independent-quality-review.md` | `21510928dd169a7b13b367e959de26428972c4ca8f8788f8f0291fba5d0863ab` |
| Two corrected qualified proofs | `qualified-fixtures-owner-exception-05/results.json` | `7aebdd866bbc05b586979bb82ea43d5618c97ecd1d89b0cca2cc070c0f90df1f` |
| Complete GUI comparison | `gui-full-comparison.json` | `ac3c92ddf8d2a9c29454d38f9692921ecd57d2da26592bd31db17199c2b5de70` |
| GUI completion and measurements | `gui-completion.json` | `0d03b608b509dd4e44bbfc59ca3c351ebef30c78f5be12d9d21ec3b9f508b721` |
| GUI raw-evidence manifest | `gui-evidence-manifest.json` | `c4d284f2d8520cf42e930e0f8b46ce5e57f5499d3c12f5e18fbc16d29fbbb6a8` |

This result supplies bounded evidence for Phase 7 Exits 1, 2 and 3. It does not
admit an exit or remove a legacy path. Phase 7 stays Open at 0/4 with all exits
Pending. D-P6-008, the earlier resource limitations, all comparison
requirements, and all legacy-retirement conditions stay in full. Project
status stays `unknown`, and output stays private-development. Richard must
make another integration decision for the exact-green draft.
