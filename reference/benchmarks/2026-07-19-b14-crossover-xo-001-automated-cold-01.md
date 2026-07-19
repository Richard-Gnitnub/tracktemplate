# B14 Crossover XO-001 Automated Cold-Process Run 01

Status: first controlled automated Phase 0 cold-process observation. This is one
run, not yet the required three-run cold series and not a before/after
optimisation comparison.

## Identification

| Item | Value |
| --- | --- |
| Run identifier | `20260719T115933Z` |
| Run interval | 2026-07-19 11:59:33–12:11:28 UTC |
| Repository HEAD | `be3d37d67205a6821408a1a672023940fc5426b1` (`Record Phase 0 checkpoint publication`) |
| Product source state | B14 has no working-tree diff from HEAD |
| Macro | `AdvancedTurnout.FCMacro` |
| Version | `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 Flatpak, using the Phase 0 environment in [../BASELINE.md](../BASELINE.md) |
| Process state | Fresh dedicated FreeCAD process; empty session before opening the fixture |
| Profile state | Dedicated persistent benchmark profile; normal FreeCAD user data/addons excluded |
| Operating-system file cache | Uncontrolled; this is not a hardware/disk-cache cold claim |
| Actual instrumentation scope | Guided B14 crossover workflow, not the complete curve/easement-to-export product pipeline |

The run used the local development bridge documented in
[`tools/freecad_bridge/README.md`](../../tools/freecad_bridge/README.md). The
bridge binds only to `127.0.0.1`, requires a local token, launches with isolated
FreeCAD user/configuration/data/temp paths, records its exact Flatpak instance,
and terminates that instance after the run. Unexpected dialogs fail the recipe.

## Fixed starting recipe

The ignored local base fixture was a saved copy of the untouched B14 default
curve-dialog result. It contained nine document objects and no managed turnout
or crossover.

| Input | Value |
| --- | --- |
| Base fixture | `b14-default-base.FCStd`, 641,206 bytes |
| Base fixture SHA-256 | `59d06cf57d65d9560dd53915fce2bef19130c534d214f92c9699066060dc4357` |
| Template set | `SET-001` |
| Main route inputs | 600 mm entry transition, 600 mm constant radius, 90°, 600 mm exit transition |
| Template width | 32 mm |
| Additional routes | One: `Track 2`, outside |
| Track 2 alignment | Euler — match spacings; 50 / 55 / 50 mm start/curve/finish spacing |
| Output mode | Replace all generated templates |
| Platform / automatic export | Disabled / disabled |
| Crossover hosts | `Main Track` then `Track 2` |
| Host A toe chainage | 746.298 mm |
| Arrangement / handing | Facing crossover / automatic handing |
| Gauge / design flangeway | 16.500 mm / 1.000 mm |
| Requested minimum radius | 600.000 mm |
| Guided sequence | Geometry preview and commit; automatic timbering; chair analysis; bounded support; 2D layout/fit; host integration; optional 3D chairs |

The chainage was selected by a read-only nine-point scan using B14's complete
turnout-and-connector mapping checks. At 746.297625 mm the complete minimum was
676.203 mm (turnout A 696.911 mm, turnout B 887.199 mm, connector 676.203 mm),
leaving a useful margin above the requested 600 mm. The UI rounded that input to
746.298 mm.

The controller approved only the known geometry-creation and host-integration
confirmation prompts. After every stage it asserted the expected B14 domain
state. The final states were:

- automatic timbering resolved with no production conflicts;
- ordinary and turnout chair assignments validated;
- bounded model timber widening prepared;
- 2D chair layout and fit validated;
- host integration active; and
- supported S1/S1J chair-body fit validated.

## Raw B14 report

The following report is preserved without changing B14's labels, values,
rounding, or interpretation text.

```text
Version 10.2A8A7B14 — Whole workflow performance benchmark
Scope: Crossover XO-001
Recorded stages: 8
Current FreeCAD objects: 27
Current process resident memory: 1082.9 MB
Total recorded wall time: 695262.0 ms (695.26 s)
Total recorded process CPU time: 717852.0 ms
Session resident-memory change: +445.7 MB
Net document-object change: +18
Largest stage: 7 Optional 3D export-chair preparation — 155235.5 ms

Stage timings:
 1. 1a Crossover geometry preview [Crossover] — wall 0.7 ms; CPU 0.7 ms (100% of one core); RSS +0.0 MB; objects +0; completed
 2. 1b Crossover geometry commit [Crossover XO-001] — wall 3064.4 ms; CPU 6521.7 ms (213% of one core); RSS +136.1 MB; objects +9; completed
 3. 2 Automatic crossover timbering [Crossover XO-001] — wall 1605.8 ms; CPU 1613.2 ms (100% of one core); RSS +0.1 MB; objects +2; completed
 4. 3 Chair-position analysis [Crossover XO-001] — wall 129431.6 ms; CPU 129367.5 ms (100% of one core); RSS +18.2 MB; objects +2; completed
 5. 4 Bounded model timber support [Crossover XO-001] — wall 135241.1 ms; CPU 135173.2 ms (100% of one core); RSS +6.8 MB; objects +0; completed
 6. 5 Templot-style 2D chair layout and fit [Crossover XO-001] — wall 147810.6 ms; CPU 147714.2 ms (100% of one core); RSS +10.5 MB; objects +5; completed
 7. 6 Crossover host integration [Crossover XO-001] — wall 122872.2 ms; CPU 141849.9 ms (115% of one core); RSS +239.6 MB; objects -1; completed
 8. 7 Optional 3D export-chair preparation [Crossover XO-001] — wall 155235.5 ms; CPU 155611.6 ms (100% of one core); RSS +32.2 MB; objects +1; completed

Interpretation:
- Wall time is the operator-visible duration of the complete action, including FreeCAD shape construction, metadata updates, display changes and recomputes.
- CPU percentage compares process CPU time with wall time; values above 100% indicate work across more than one core or accounting overlap.
- RSS is an end-minus-start memory snapshot, not a sampled peak. A later optimisation pass should target the largest repeatable wall-time and memory stages first.
```

## External-boundary reconciliation

The controller measured each complete method invocation independently of B14's
internal timers. It polls at one-second intervals, so an external stage value can
include up to roughly one second of completion-detection delay.

| Stage | B14 internal wall | Controller elapsed | Difference |
| --- | ---: | ---: | ---: |
| Geometry preview + commit | 3.065 s | 10.917 s | +7.852 s |
| Automatic timbering | 1.606 s | 2.013 s | +0.407 s |
| Chair analysis | 129.432 s | 129.636 s | +0.205 s |
| Bounded support | 135.241 s | 136.243 s | +1.002 s |
| 2D layout/fit | 147.811 s | 148.728 s | +0.917 s |
| Host integration | 122.872 s | 123.439 s | +0.567 s |
| 3D chair preparation | 155.236 s | 156.059 s | +0.824 s |
| **Stage total** | **695.262 s** | **707.035 s** | **+11.773 s** |

The total controller interval was 714.987 s. The remaining 7.952 s covers the
document open, B14 definition load (2.452 s), manager/driver setup, reporting,
saving, session inventory, RPC/polling, and other non-stage work. Thus B14's
internal report covers 97.24% of controller elapsed time, but its claim of a
complete operator-visible boundary is not yet exact. Geometry accounts for most
of the stage-boundary discrepancy and needs finer profiling before optimisation.

## Resource and document observations

- The empty fresh process was 488.234 MB RSS. The final process was 1083.188 MB,
  a whole-run increase of 594.953 MB.
- B14's internal session began after the fixture, macro and manager were loaded;
  it reports a further 445.7 MB increase. Approximately 149 MB therefore sits
  outside the current stage/session boundary.
- Host integration added 239.6 MB, 53.8% of B14's recorded RSS increase, while
  reducing the net document-object count by one. Geometry commit added 136.1 MB.
  Together those two stages account for 84.3% of the recorded memory increase.
- The document moved from nine objects at open to 27 at completion: five
  `App::DocumentObjectGroup`, 20 `Part::Feature`, and two spreadsheet objects.
  It contained one `ChairProductionSolids` object and the expected crossover,
  timber-analysis and reversible host-integration roles.
- RSS values are end-minus-start snapshots, not sampled peaks. Retained shape,
  triangulation, view-provider and allocator memory cannot be inferred from
  object counts alone.

## Instrumentation and correctness findings

These are characterised observations, not production-code changes:

1. The geometry preview validates only the connector minimum radius. At the
   lower allowed chainage, preview accepted a 652.199 mm connector, but commit
   correctly rejected the complete result because one mapped turnout road
   reduced the complete minimum to 511.975 mm. Preview and commit should present
   the same complete feasibility rule.
2. Chair analysis writes its cached metadata copy of
   `performance_timings_ms` before metadata updates, display construction,
   recompute, transaction commit and total time are added. The returned result
   has the later entries, but the persisted profile is truncated; it cannot yet
   explain the complete 129-second stage after save/reload.
3. A read-only post-integration query of four effective chair/support/layout/
   solid statuses took about 28 seconds in the exploratory session because each
   status path independently re-extracted records and recalculated signatures.
   This is a profiling lead, not yet a controlled benchmark result.
4. The first supplied long-lived-document report took 701.663 s for the first
   occurrence of its actions even though it omitted a separately reported host
   integration stage. The new internal total is 695.262 s including integration.
   This reinforces the need for controlled starting state and repeats; it is not
   a valid percentage improvement comparison.

## Local raw evidence and reproducibility limits

The generated artifacts remain under ignored `benchmark-output/` and are not
committed:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Completed run document | 14,106,672 bytes | `198609afd62ab02192c6336c31054ce9d943b29912fb96781528585028c2de20` |
| Structured `run.json` | 10,686 bytes | `0db10271345236fc61adf2bf5f45165190006019e46c13df8486f47e6e9e2a2a` |
| Raw `workflow-report.txt` | 2,072 bytes | `91b41af4243a1deacaec05cb1aba494486173d47238c5e4f5843960cd77f76e2` |

The bridge has since been strengthened to capture a rendered top view, full
FreeCAD window, manager image and startup logs automatically; that capture path
passed a separate geometry-only smoke run. Those later artifacts are not
retroactively claimed as part of this full run.

At the time of this run, two local prerequisites were not yet reproducible from
a fresh checkout: the ignored base fixture and the patched `freecad-cli`
checkout. Tracked tooling added later on 2026-07-19 now pins and verifies the
reviewed bridge patch and constructs the fixture in an empty isolated FreeCAD
session. An independent 636,344-byte regeneration had a different binary hash
but the same semantic SHA-256 as this run's original fixture:
`a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`.
This later reproducibility evidence does not alter or retroactively extend the
raw measurements above.

At least two more equivalent cold-process runs and a separately defined
unchanged-result warm/reuse series remain required. Do not calculate a median,
range, optimisation target threshold, or phase transition from this single run.
