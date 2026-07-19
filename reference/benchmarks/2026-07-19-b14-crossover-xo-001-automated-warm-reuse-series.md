# B14 Crossover XO-001 Automated Warm-Reuse Series

Status: controlled three-iteration same-process warm-reuse series for B14's
existing **Generate supported chair solids** operator action. This is not a
replay of the destructive full workflow, a whole-product warm total, or a
before/after optimisation comparison.

## Identification and scope

| Item | Value |
| --- | --- |
| Run identifier | `20260719T135007Z` |
| Run interval | 2026-07-19 13:50:07–14:07:15 UTC |
| Repository HEAD | `be3d37d67205a6821408a1a672023940fc5426b1` |
| Product source state | B14 has no working-tree diff from HEAD; warm tooling and this report were pending review/commit |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 Flatpak in the isolated Phase 0 environment |
| Completed source run | Cold run 04, `20260719T132252Z` |
| Completed FCStd SHA-256 | `865697dc8dfce76489053673def51b2b511bd14e6fb112c088991e3f043a9f17` |
| Original base semantic SHA-256 | `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e` |
| Cache/process qualification | Fresh process opened a completed persisted result; one unmeasured same-process warm-up preceded three measured iterations |
| Tooling-set fingerprint | `0fecc19bdbd7df07a88cd96aebca64afa3148407bc32f67f3cbc65d090b62e61` |

The runner required the completed document's sibling `run.json` and rejected it
unless the macro hash, original semantic fixture, exact seven-stage cold
sequence, completed status and 27-object final inventory matched. It copied the
FCStd into a new ignored warm-run directory and never saved over either file.
The source and copied FCStd hashes remained identical after the run.

The warm action uses the actual `ChairAnalysisPanel.generate_solids` method, the
same method wrapped by B14's Stage 7 timer. It is eligible for a warm test because
`generate_supported_chair_solids` has an explicit signature-matched return path
with `unchanged_result_reused=True`. Automatic timbering, model support, 2D
layout and integration are not replayed: those are constructive or invalidating
actions, so calling them again would not constitute unchanged-result reuse.

## Correctness precondition

The reopened completed document contained 27 objects: five groups, 20 Part
features and two spreadsheets. Before warm-up, the runner recomputed and
validated these effective statuses:

- automatic timbering resolved with no production conflicts;
- ordinary and turnout chair assignments validated;
- bounded model timber widening prepared;
- 2D chair layout and fit validated;
- supported S1/S1J chair-body fit validated; and
- integrated with host templates.

The completed-state validation job took 130.331 seconds at its outer boundary.
The explicit six-status calculation within it took 22.680 seconds; selection
refresh, persisted configuration hydration and invariant snapshots account for
the remainder. This is setup evidence, not a measured warm iteration.

The retained chair solid had:

- object name `RailwayChairSolids_XO_001`;
- solid signature
  `5c0e8bcbf3aade28fc70d68ed36d5777e8b834f5ef0418ae4da5973780d24090`;
- 119 solids, 3,213 faces and 8,092 edges;
- valid, non-null shape hash code `506402310`; and
- stable 27-object identity SHA-256
  `29b9b0a217ae76005fa4f4bda7cbe0da41dcc79bfd258ca3cbc161ffc8ab459c`.

Every warm-up and measured iteration retained those exact values and all six
effective statuses. No object was added, removed or replaced.

## Measured results

| Boundary | Iteration 1 | Iteration 2 | Iteration 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete asynchronous job | 222.134 s | 223.484 s | 223.323 s | **223.323 s** | 1.350 s |
| Actual panel operator action | 143.208 s | 143.624 s | 143.581 s | **143.581 s** | 0.415 s |
| Panel action process CPU | 143.227 s | 143.642 s | 143.596 s | **143.596 s** | 0.415 s |
| Direct reuse function | 29.682 s | 29.670 s | 29.557 s | **29.670 s** | 0.125 s |
| Panel action minus direct function | 113.527 s | 113.954 s | 114.024 s | **113.954 s** | 0.497 s |
| Separate six-status validation | 22.978 s | 22.886 s | 22.905 s | **22.905 s** | 0.092 s |
| Panel-action RSS delta | +1.996 MB | +0.969 MB | +0.035 MB | **+0.969 MB** | 1.961 MB |

The complete job includes crossover selection refresh and before/after object,
configuration and solid-shape fingerprints in addition to the panel action and
separate status validation. It is an audit boundary, not the operator-visible
button duration.

The direct function correctly returned the retained object after about 29.67
seconds, but the surrounding real panel method took about 143.58 seconds. Its
post-function parent/panel refresh therefore accounted for roughly 114 seconds,
or about 79% of the action. The standalone six-status audit then took a further
22.91 seconds. B14 currently re-extracts records and reconstructs signatures
through several effective-status paths rather than sharing one validated
snapshot.

## Cold/warm interpretation

The like-for-like cold series records a 151.622-second median for B14's same
Stage 7 panel method. The warm median is 143.581 seconds: only 8.041 seconds
(5.30%) lower, and still 94.70% of the cold cost despite returning the unchanged
119-solid object. The warm-up panel action was 142.153 seconds and its complete
job was 221.021 seconds, consistent with the measured series.

This demonstrates correct identity/signature reuse but ineffective cost reuse:

1. the direct function builds and validates the solid plan before testing
   whether the retained solid can be returned;
2. the panel refresh after that return dominates the action; and
3. independent status functions repeat record extraction/signature work.

The safe optimisation seam is consequently earlier signature validation plus a
shared immutable analysis/status snapshot. That is a profiling conclusion, not
permission to skip physical-fit validation after an input change. Change/reuse/
invalidation tests remain mandatory before production code is altered.

## Resource and lifecycle observations

- Panel-action RSS growth fell from +1.996 to +0.969 to +0.035 MB across the
  measured iterations. No document object or shape fingerprint changed.
- The isolated process was 410.840 MB before opening the completed document and
  879.594 MB after all validation, warm-up, three measurements and screenshots.
  That whole-session difference includes document loading and repeated
  analysis; it is not the retained cost of one reuse action.
- The final rendered top view passed the sampled-colour check, and the exact
  Flatpak instance was absent before the wrapper returned.
- One earlier attempt was excluded because the preparation audit exceeded the
  30-second synchronous RPC limit. It changed no source document. The successful
  recipe uses the asynchronous job path with heartbeat and timeout controls.

## Ignored raw evidence

The raw files contain local paths and remain under
`benchmark-output/freecad-bridge/warm-runs/20260719T135007Z/`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Copied completed FCStd | 14,106,597 | `865697dc8dfce76489053673def51b2b511bd14e6fb112c088991e3f043a9f17` |
| Structured `warm-run.json` | 16,178 | `9d287af715f7b4c85c788ab7ac78ed1396fdc07ec2c9361818f9cbdbe95a0922` |
| Final top view | 26,758 | `f9386dfdbdbb82165e3b8c00a9077e2b14b4ccb669747535a9b151df65627fa3` |
| Final FreeCAD window | 136,357 | `e5beaec526568f7ab49bc09516327322a8dffca6d0486ea47f59badaf8609c03` |
| Final manager | 209,584 | `d52c76f53c657cb93e796ad626ed3a16b472ff5664ae67116b5a3342f816db4f` |
| FreeCAD log | 10,554 | `5aa7a60a701b17e08511ac67bdda5d7aa844a281e3f3a4f6c492f64109787071` |
| Launcher log | 128 | `702a594f3fd5ed9d95337757e22851df1bc1048d0441a953665d8aeee65443f3` |

The warm host runner, in-FreeCAD driver and wrapper had respective SHA-256
values `52f701909f56a158d6653f00b7c74c08f5550509743258c51597d46a75ad0492`,
`1285c31fba5da1cfe637081c08fcfd8ba22d26c25cc66386af5aed1dd1c93368`
and `2d2d63f60d6756e66df5771123b8c434bd0c70c207dfe0c37c544aee0fb65818`.
