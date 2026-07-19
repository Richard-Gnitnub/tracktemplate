# B14-to-B15 Behavioural Acceptance: XO-001 Chair Path

Status: **ACCEPTED — technical qualification passed and the project owner
accepted the version roles on 2026-07-19.**
This record does not approve the observed timings as suitable for human use.

## Decision in scope

B15 is technically qualified to replace B14 as the behavioural reference for
the declared B15 chair-performance and representation delta on the preserved
`XO-001` crossover recipe. The inherited B14 implementation, retained railway
semantics, non-chair leaf geometry, chair analysis, bounded-support decisions,
supported-chair solids, document identities, and effective statuses all passed
the checks described below.

The project owner accepted this evidence on 2026-07-19. B15 is the behavioural
reference entering Phase 1 and B14 is retained as the immutable legacy
comparison oracle. This is a bounded Phase 0 acceptance, not whole-product
coverage and not permission to remove B14.

## Exact source state

| Item | Value |
| --- | --- |
| Repository checkpoint | `7379eb468ec3cb4821388b37994c32b94a8c2230` |
| B14 file | `AdvancedTurnout.FCMacro` |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 file | `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| FreeCAD | 1.1.1, isolated Flatpak GUI session |
| Acceptance run | `20260719T162543Z` |
| Run interval | 2026-07-19 16:25:43–17:00:17 UTC |
| Complete controller duration | 2,074.525 seconds |

Neither macro was edited during the acceptance work.

The acceptance driver and host runner were then-uncommitted closeout sources;
they are included in the checkpoint changes described by this report. Their
exact accepted-run byte identities were:

| Recipe source | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/run-b15-acceptance` | `02a525d5f206549ec216ebb59a22977e5c38815b545058e982f8f0fd66e9096d` |
| `tools/freecad_bridge/run_b15_acceptance.py` | `847bd7107590e332ebcc9853505fd0ab6e3000b4cc0d7561af0c569bd1639065` |
| `tools/freecad_bridge/probes/load_b15.py` | `e6508963d23305252feba91b71cc4f595dbfc3f096b293cba4b1cb21d5aa7552` |
| `tools/freecad_bridge/probes/show_b15_trackwork_manager.py` | `e36ee8fdacfe6f84b45230492134557912099598bc0e53d7f24986a1d1808564` |
| `tools/freecad_bridge/probes/b15_acceptance_driver.py` | `31f45026a3fea2009ffdf8f787046354b7a58596d2bc3c7fa338bc841a0eab15` |
| `tools/freecad_bridge/run_b14_crossover.py` | `ea372d197d91280d5d3386fdef3a37790a25e9acae40314cde062d0d6ce2c5a0` |

The accepted run used checkpoint `7379eb4`'s `run-isolated`,
`launch-freecad`, and `orchestration.py`, with SHA-256 values
`c051617dab0b6f27de3ac684d416eb804066a152de0d83c8182141243b7ae4ec`,
`eaa7e22a5e7d5a2e7cb2dd4d33b34a6e1c2702b66871a5bde75e681a81434e17`, and
`d3ea59acb145cf2854a6d2ab89b745fcd9240de476f2fa129eed2f3392cadb8c`
respectively. The first two were hardened after the run as described under raw
evidence provenance; the acceptance oracle and action sequence did not change.

## Source-delta audit

The raw B14-to-B15 diff contains 895 insertions and 46 deletions. It consists
of version/header changes, 40 direct `doc.recompute()` calls routed through the
B15 recompute measurement wrapper, and the final B15 compatibility layer that
starts at the marker `# A8A7B15 chair performance and representation.`.

`tests/validate_b15.py` now compares the complete inherited module abstract
syntax tree, not merely a selected function list. It removes only the expected
module docstring, version assignments, final `run_macro()` launch, and the
mechanically equivalent recompute wrapper calls before comparison. The check
passed, establishing that B15 did not silently change another inherited B14
definition outside its declared layer.

## Reproducible recipe

The runner copied the completed document from controlled B14 cold run
`20260719T132252Z`; it did not modify the source document. The sibling B14
`run.json` and completed-state contract were verified before opening the copy.

- Entity: crossover `XO-001`.
- Host A: `SET-001`, track 1, `Main Track`, persisted centreline
  `RailwayTrackCentreline_00`.
- Host B: `SET-001`, track 2, `Track 2`, persisted centreline
  `RailwayTrackCentreline_01`.
- Host A chainage: `746.298 mm`.
- Starting document: 27 objects, completed B14 analysis/support/layout/solid
  state, 119 supported chair solids.
- B15 operator actions: chair analysis, bounded model support, revised 2D
  layout, unchanged 2D layout reuse, real-panel removal of the retained B14
  solids, fresh B15 solid construction, and unchanged B15 solid reuse.
- Final gate: save, close, reopen, recreate the real manager, validate effective
  statuses, and capture the rendered manager and top view.

Run the same acceptance sequence from a completed controlled B14 cold document:

```bash
tools/freecad_bridge/run-b15-acceptance \
  --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The command uses a disposable copy in the isolated development bridge. Its raw
output remains ignored because it contains machine-local paths and generated
FreeCAD data.

## Behavioural results

| Invariant | Before B15 actions | After save/reopen | Result |
| --- | ---: | ---: | --- |
| Chair positions | 355 | 355 | Pass |
| Chair findings | 269 | 269 | Pass |
| Chair-analysis semantic SHA-256 | `7e1a5e1a0e5d225377752db2962d42f664266ff72fa4b865ab025964b5902470` | `7e1a5e1a0e5d225377752db2962d42f664266ff72fa4b865ab025964b5902470` | Pass |
| Bounded support adjustments | 35 | 35 | Pass |
| Support semantic SHA-256 | `cb8a473471d35b9520a423d9cf2cf993044ba1cccb0810d26da740cb923cfac6` | `cb8a473471d35b9520a423d9cf2cf993044ba1cccb0810d26da740cb923cfac6` | Pass |
| Non-chair leaf `Part` shapes | 14 | 14 | Pass |
| Non-chair geometry SHA-256 | `c9f5e07ba14b7de6912ef6186971ae1dcf63bd2b9231a20a50fac728249bf998` | `c9f5e07ba14b7de6912ef6186971ae1dcf63bd2b9231a20a50fac728249bf998` | Pass |
| Supported chair solids | 119 | 119 | Pass |
| Solid semantic SHA-256 | `89003ed99945d039fd3ba7ca36175a5cc043ee6eacaa9b3755a2875ebf2cef35` | `89003ed99945d039fd3ba7ca36175a5cc043ee6eacaa9b3755a2875ebf2cef35` | Pass |
| Final B15 2D layout objects | — | 5, representation revision 2 | Pass |
| Final document objects | — | 34, stable identity hash | Pass |

The solid aggregate remained valid with 119 solids, 3,213 faces, 8,092 edges,
5,236 vertices, and bounds
`(682.034933, 161.939529, 0.8)–(983.637793, 904.246210, 2.589583)`.

The first B15 layout action created five representation objects. Repeating the
unchanged action reported reuse, created no object, performed no document
recompute, and retained exact object identities and displayed-shape semantics.
The real removal action then removed the retained B14 solids while preserving
the analysis, support, layout, and non-chair geometry hashes. Fresh B15
construction reported no reuse, created one aggregate object containing 119
solids, and reproduced the exact B14 topology and bounds. Its immediate
unchanged repeat reported reuse, created no object, performed no recompute, and
retained exact object and solid semantics.

After save/reopen, all six effective states were correct: B4 timbering clear,
chair assignments validated, bounded support applied, 2D layout validated,
supported-chair solid fit validated, and host integration active.

## Timing observations — not accepted budgets

| Real panel action | Action wall time | Reported reuse |
| --- | ---: | --- |
| Chair analysis | 120.415 s | Yes |
| Bounded model support | 141.990 s | No |
| First revised 2D layout | 159.267 s | No |
| Unchanged 2D layout reuse | 129.498 s | Yes |
| Remove retained supported-chair solids | 115.872 s | Not applicable |
| Fresh B15 supported-chair construction | 147.223 s | No |
| Unchanged supported-chair solid reuse | 145.463 s | Yes |
| Save/reopen validation | 259.744 s outer interval | Not applicable |

These durations are exceptionally slow for interactive work. In particular,
the unchanged layout and solid actions still take more than two minutes despite
valid result reuse. They are diagnostic observations, not targets, tolerances,
or performance acceptance. Phase 1 must profile and remove the redundant
status, display, persistence, and orchestration work while preserving the
semantic results above.

After the manager was recreated on reopen, its session-local workflow report
listed zero recorded actions. The runner's action/event records above were
captured before that recreation and remain complete. Persisting or otherwise
reconciling manager-session performance history is an instrumentation gap for
Phase 1, not part of the behavioural acceptance.

## Raw evidence provenance

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `acceptance-run.json` | 3,123,431 | `600d37324a73d602c8e1bc0e48ef2f490c0583a7ae4b17ea61cec4712e32e06a` |
| FreeCAD log | 10,857 | `bf3d281b8cef8af7d85e1a6f0ce1e9c7d8fcaffde857e2557f04d9f72a8a603b` |
| Launcher log | 335 | `74ce8db66c1180a23e58496647b13944d807717f212fe360d8eafc5730b735ba` |
| Input-preserving FCBak | 14,106,597 | `865697dc8dfce76489053673def51b2b511bd14e6fb112c088991e3f043a9f17` |
| Final B15 FCStd | 14,370,352 | `ccf07d24f5df0a50648c4b3b44111e854ef4bdc68e5f13522073aeab6f322bfa` |
| Final top view | 33,879 | `77fad5974a480937efabfd2f5cdf1096475b79b800bca42ce44ccb145f44c24b` |
| Final manager image | 181,179 | `3f9ddaffd1037074d99338836986f26eda33d2a5af232295ca3012a31b2bacdf` |
| Final FreeCAD window image | 133,621 | `aaedb9103957cbb57c5ed7c8f93fa0cab9bb62dc48462c12f504ff8fd5eab5b2` |
| Post-reopen workflow report | 388 | `ab08f9e6d98a53c8325a01e9140cbe1f99ff0829e03955381eb5ff34a132dc1a` |

The input completed FCStd was unchanged before and after the run at SHA-256
`865697dc8dfce76489053673def51b2b511bd14e6fb112c088991e3f043a9f17`.
Its sibling `run.json` SHA-256 was
`dc51862d69904fb28916a08167f0e987f4fca727d65148e66f1fd51dd99f21bb`,
and its deterministic base semantic SHA-256 was
`a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`.

Four earlier evidence sets are excluded. Run `20260719T145050Z` revealed that
FreeCAD document groups aggregate child shapes, so treating group shapes as
independent production geometry produced a false change; the corrected oracle
still checks every non-chair leaf `Part` shape. Run `20260719T145739Z` passed
all railway and persistence assertions but exposed a B14-only module name in
the generic screenshot helper. Run `20260719T152512Z` passed that original
gate, but review showed it qualified only retained-solid reuse rather than
fresh B15 construction, so it was superseded. The strengthened
`20260719T160218Z` run correctly removed the solids, then exposed that the
nominal analysis-only fingerprint still included deliberately mutable physical
state. A focused fast test now proves that analysis, support, layout, and solid
state are fingerprinted independently.

The accepted run's startup log contains FreeCAD's attempt to inspect an
auto-recovery record left in the isolated temp directory by the preceding
aborted disposable run. The referenced FCStd remained byte-identical to the
B14 input and passed ZIP integrity; the accepted run also asserted an empty
FreeCAD document session before opening its own copy. The isolated wrapper now
uses and removes a fresh per-run temp/recovery directory. A subsequent bounded
lifecycle check opened no document, used that unique directory, produced no
recovery/corruption warning, removed the directory, and stopped the exact
Flatpak instance. Only `20260719T162543Z` is used for the decision and timings
in this report.

## Coverage boundary and accepted decision

This evidence covers B15's declared delta on one deterministic completed
crossover. It does not characterise all curve/easement, station, multiple-track,
turnout, editing, undo/redo, or SVG/DXF/STL/STEP export behaviour. Those gaps
remain explicit Phase 1 inputs.

Accepted decision: B15 is the behavioural reference entering Phase 1, B14 is
the immutable legacy comparison oracle, and every timing in this record remains
an urgent performance problem rather than an accepted baseline budget.
