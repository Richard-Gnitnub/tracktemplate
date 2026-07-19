# B14 Crossover XO-001 Automated Cold-Process Series

Status: controlled three-run Phase 0 cold-process series using one identical
current controller and evidence boundary. This is a baseline of the guided B14
turnout/crossover workflow, not a before/after optimisation comparison, warm
reuse series, or complete curve-to-export product benchmark.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260719T125530Z`, `20260719T130743Z`, `20260719T132252Z` |
| Run intervals | 12:55:30–13:07:17, 13:07:43–13:19:24, and 13:22:52–13:34:31 UTC on 2026-07-19 |
| Repository HEAD | `be3d37d67205a6821408a1a672023940fc5426b1` |
| Product source state | B14 has no working-tree diff from HEAD; development tooling and this report were pending review/commit |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 Flatpak in the isolated Phase 0 environment |
| Base fixture SHA-256 | `59d06cf57d65d9560dd53915fce2bef19130c534d214f92c9699066060dc4357` |
| Base semantic SHA-256 | `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e` |
| Process/document state | Fresh isolated FreeCAD process, empty session, immutable nine-object fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent |
| Final result | Every run completed all assertions with 27 document objects and no unexpected dialog |

The fixed recipe is defined in the [cold run 01
record](2026-07-19-b14-crossover-xo-001-automated-cold-01.md) and implemented by
the tracked tooling under `tools/freecad_bridge/`. Hosts are resolved by
persisted `SET-001`/track identity and the crossover is positioned from Main
Track's centreline at chainage `746.298 mm`; UI ordering and a free XYZ datum are
not part of the recipe.

The preliminary run `20260719T115933Z` remains valid internal B14 evidence, but
is excluded from this series because it predates the current automatic
screenshot/log capture and semantic fixture-validation boundary. Runs 02–04 use
the same controller files. Their tooling-set fingerprint was
`1f4e19056379afaf83d35738275524b8b45510a06fdeb105cc3a3dd4ef2b5904`,
calculated by hashing the ordered `sha256sum` output for the host runner, recipe,
orchestration helpers, load/base/driver probes, cold/isolated launchers,
FreeCAD launcher and reviewed third-party patch.

## B14 internal results

| Metric | Run 02 | Run 03 | Run 04 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Total wall time | 686.691 s | 680.027 s | 679.098 s | **680.027 s** | 7.593 s |
| Total process CPU time | 709.504 s | 702.537 s | 702.925 s | **702.925 s** | 6.967 s |
| Session RSS change | +382.0 MB | +394.6 MB | +379.7 MB | **+382.0 MB** | 14.9 MB |
| Report-time process RSS | 1014.2 MB | 1035.2 MB | 1021.5 MB | **1021.5 MB** | 21.0 MB |
| Final object count | 27 | 27 | 27 | **27** | 0 |

The internal wall-time range is 1.117% of its median. The sequential totals fell
from 686.691 to 680.027 to 679.098 seconds. Because the operating-system file
cache was uncontrolled and the isolated preference profile persists, this
small monotonic drift is reported rather than interpreted as an optimisation.

### Internal stage wall time

| B14 stage | Run 02 | Run 03 | Run 04 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Geometry preview | 0.7 ms | 0.7 ms | 0.7 ms | 0.7 ms | 0.0 ms |
| Geometry commit | 3102.3 ms | 3116.9 ms | 3079.8 ms | 3102.3 ms | 37.1 ms |
| Automatic timbering | 1628.7 ms | 1589.6 ms | 1592.3 ms | 1592.3 ms | 39.1 ms |
| Chair-position analysis | 125816.5 ms | 125798.2 ms | 123340.1 ms | 125798.2 ms | 2476.4 ms |
| Bounded model timber support | 132323.5 ms | 133409.5 ms | 131251.5 ms | 132323.5 ms | 2158.0 ms |
| 2D chair layout and fit | 145043.4 ms | 142832.8 ms | 143240.8 ms | 143240.8 ms | 2210.6 ms |
| Host integration | 125946.1 ms | 121899.4 ms | 124970.4 ms | 124970.4 ms | 4046.7 ms |
| Optional 3D chair preparation | 152829.7 ms | 151380.0 ms | 151622.3 ms | **151622.3 ms** | 1449.7 ms |

Chair analysis, support, 2D layout, integration and 3D preparation account for
more than 99.3% of internal wall time in every run. Optional 3D preparation is
the largest stage in every controlled run. The old accumulated-document
support entry of 1,094,374.5 ms is therefore not representative of this cold
recipe: controlled support is 131,251.5–133,409.5 ms. This series does not by
itself identify the accumulated-state cause.

## External controller boundary

| Metric | Run 02 | Run 03 | Run 04 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete controller interval | 707.246 s | 700.818 s | 698.573 s | **700.818 s** | 8.673 s |
| Sum of external stage calls | 698.267 s | 691.487 s | 689.482 s | **691.487 s** | 8.784 s |
| Non-stage controller work | 8.979 s | 9.332 s | 9.091 s | **9.091 s** | 0.352 s |
| Internal total / controller interval | 97.094% | 97.033% | 97.212% | **97.094%** | 0.179 percentage points |
| Controller time outside internal total | 20.555 s | 20.791 s | 19.475 s | **20.555 s** | 1.316 s |

The complete-controller range is 1.238% of its median. Its boundary includes
document open, B14 load, semantic fixture validation, manager/driver setup,
full method invocations, reporting, save, final inventory and rendered evidence.
The internal total excludes some dialog, refresh, polling, capture and setup
work; it must not be substituted for the external total when budgeting the
complete automated action.

### External stage calls

| Driver stage | Run 02 | Run 03 | Run 04 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Geometry | 10.900 s | 10.795 s | 10.801 s | 10.801 s | 0.105 s |
| Timber | 2.019 s | 2.013 s | 2.008 s | 2.013 s | 0.011 s |
| Chairs | 126.750 s | 126.328 s | 124.284 s | 126.328 s | 2.466 s |
| Support | 132.368 s | 134.340 s | 131.507 s | 132.368 s | 2.833 s |
| Layout | 145.977 s | 143.530 s | 143.418 s | 143.530 s | 2.559 s |
| Integration | 126.508 s | 122.466 s | 125.092 s | 125.092 s | 4.042 s |
| Solids | 153.746 s | 152.014 s | 152.373 s | 152.373 s | 1.732 s |

## Resource observations

- The B14 session RSS-change median is +382.0 MB with a 14.9 MB range. This is
  the more stable retained-memory series boundary.
- Host integration is the largest positive stage delta in every run at
  +208.3 to +247.5 MB. Geometry commit is second at +133.9 to +139.3 MB.
- The outer final RSS values are 1029.910, 1048.816 and 1031.602 MB, a median of
  1031.602 MB and range of 18.906 MB.
- The outer pre-open snapshots are 488.641, 488.652 and 411.047 MB. The lower
  third value makes the corresponding whole-process deltas noisy; RSS remains
  an end-minus-start allocator snapshot, not a sampled peak or direct geometry
  ownership measurement.
- The 3D stage reported a small or negative end-minus-start RSS delta in all
  three runs. That does not mean creating 3D output is memory-free; allocator
  release and retained earlier-stage memory prevent that inference.

## Correctness and instrumentation findings retained

All post-stage domain statuses, stable host identities, object transitions and
final rendered-image checks passed. The series changes no product source and
does not resolve the findings from run 01:

1. crossover preview and commit do not yet apply one complete feasibility rule;
2. the persisted chair timing payload omits late work; and
3. repeated effective-status queries need a controlled shared-snapshot/cache
   test.

The required regression tests are recorded in [../VALIDATION.md](../VALIDATION.md).
A separate unchanged-result warm/reuse recipe remains necessary. Replaying the
destructive construction stages in the same process would not satisfy that
requirement.

## Ignored raw evidence

The raw files contain local paths and remain under ignored
`benchmark-output/freecad-bridge/runs/`.

| Run | Completed FCStd (bytes; SHA-256) | `run.json` (bytes; SHA-256) | B14 report (bytes; SHA-256) |
| --- | --- | --- | --- |
| 02 | 14,106,674; `873b90b0fdd476d0f5eb8f69ccafe687f88eca4c5a71ed459fb097eb51c7a9fb` | 19,042; `5d15012769f6d2fb073a8bcb892b97063304cd9c6673f6ac892f0cb7d21c4386` | 2,070; `ad83e16bf3274d6d8008c5d7bb4ea46a883d160e0ab89cdf2c434bbd58880742` |
| 03 | 14,106,502; `9c029ad7a3c72e1d87ace6bb79ace15e8a868cfd4f6daf0fb52d83e654d5f5c8` | 19,050; `92ac95f14d1bd04930079b1b6d3e3e661054ce2ca891186b1f917b15a092ab45` | 2,071; `55abdef8a6772bf44f4cdf0dfc873ef4f96391242873bc6174039e3ed5c1fb69` |
| 04 | 14,106,597; `865697dc8dfce76489053673def51b2b511bd14e6fb112c088991e3f043a9f17` | 19,040; `dc51862d69904fb28916a08167f0e987f4fca727d65148e66f1fd51dd99f21bb` | 2,071; `4045fafd17a0b673cd009ad5f402dad61a8a9d1d21c98aae6b14560183acecc0` |

| Run | Top view (bytes; SHA-256) | FreeCAD window (bytes; SHA-256) | Manager (bytes; SHA-256) |
| --- | --- | --- | --- |
| 02 | 26,752; `aff7d6b319ca818a5521488e4f35ade25b49a9b97143219b8f78728291f2bca7` | 142,981; `5ec49273b8eff7f56d4b7e54baf80cab853486e128e6b460394afc3958aa0ade` | 193,662; `868d0f6cdc5bf9ae4f8b82302ceb049c4b1c8ac190a09c5b29680f8b5353f78d` |
| 03 | 26,753; `ef4c279f46ccaaf8715ad3383d20d1c04c0fb129a67e723899ef6d736d8743f5` | 143,142; `ffdf948b183778c49d53e85aa7359b7ea17b0baa4932d884b3039e6fc43dcd47` | 193,662; `868d0f6cdc5bf9ae4f8b82302ceb049c4b1c8ac190a09c5b29680f8b5353f78d` |
| 04 | 26,751; `d5114afd373f78a1e309c453c2b46a0d386e67d786ed8922edb5f2b6aba38860` | 132,094; `98b6b50720bf38ddf63e37c7c701da9648265a81e0ce635ca24845f10e50682e` | 193,662; `868d0f6cdc5bf9ae4f8b82302ceb049c4b1c8ac190a09c5b29680f8b5353f78d` |

Each top view passed the sampled-colour rejection check. FreeCAD and launcher
logs are retained beside these artifacts. The exact Flatpak instance recorded
for each run was absent before the wrapper returned.
