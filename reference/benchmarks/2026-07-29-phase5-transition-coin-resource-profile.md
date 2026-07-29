# Phase 5 Bounded Transition Coin Resource Profile

Status: **completed Level 2 bounded candidate observation on 2026-07-29; no
representative workload, renderer, product capacity, numerical budget,
optimisation or Phase 5 exit is accepted.**

## Scope and boundary

This profile measures the existing development-only Coin ViewProvider candidate
at one fixed diagnostic scale:

- 32 logical transition objects in one new disposable FreeCAD document;
- one renderer-neutral 32-segment preview, disposable Coin layer, selectable
  root and retained preview cache per object;
- one explicit document recompute and GUI redraw after cold construction; and
- one untimed unchanged warm-up followed by three measured unchanged refreshes
  in each process, each with one explicit recompute and redraw.

The object count is a deliberate 32-times expansion of the preceding
single-object fixture so per-object object, layer, node and resource behaviour
is visible while the run remains bounded. No accepted layout population or
workload derivation establishes that it represents product use. It does not
define a product capacity, interaction target or supported document size.

The cold span starts after FreeCAD GUI readiness, module loading and runtime
qualification. It includes the new document, canonical state analysis, one
atomic batch create, preview and Coin construction, ViewProvider attachment,
display-mode selection, explicit recompute, view fitting, redraw and GUI event
processing. Process launch and bridge readiness are outside the span.

Each warm span requests the same canonical state through all 32 ViewProviders,
then recomputes, redraws and processes GUI events. The derived preview artifacts
are reused, but the current ViewProvider still constructs and discards one
candidate Coin binding per object before it decides that the active scene is
unchanged. Wall and CPU measurements include that work. Node and RSS
observations are before/after active-state snapshots, not transient peaks.
This is not an edit, pointer-selection or save/reopen workflow.

## Source state, environment and recipe

The measurement started from protected-main commit
`162f1048cc2c057dbfa7dd01fc12821fe998db4c`. The working tree contained only
the eight profiler, focused-test, benchmark, validation and current-evidence
files belonging to this tranche.

- Recorded: 2026-07-29 16:10:23–16:10:44 UTC.
- Host: Linux 7.0.0-28-generic x86-64, AMD Ryzen 5 5500, 12 logical CPUs,
  31.2 GiB physical memory.
- Host profiler: CPython 3.12.3 from the repository virtual environment.
- GUI runtime: qualified Flatpak FreeCAD 1.1.1, revision 44874.
- Isolation: three fresh isolated GUI processes with an empty document set and
  new document and caches in each process.
- Repetition policy: three independent cold samples; one untimed warm-up and
  three measured warm observations per process, for nine warm observations.
- RSS: Linux `VmRSS` immediately before and after each span; not a sampled peak.
- Operating-system file and graphics-driver caches were uncontrolled.

The reproducible command was:

```bash
.venv/bin/python tools/phase5_transition_coin_resource_profile.py
```

The principal measured-source fingerprints were:

| Input | SHA-256 |
| --- | --- |
| GUI sampler | `4e8609afa6a80ec9bc1dc0815ca171a6307bc2d458dc87713311aa6ad217ede4` |
| Host profiler | `02737a684563717e8f453bc0ae7600996ff48e4db23295a14e6f6ab77cbd7c4e` |
| FreeCAD transition adapter | `c51e021ba38fb5960d7113bc70fad64148aac7139d167c6a5cfa34b728101a96` |
| Derived-state cache | `8ed1516ac03c001ff24fde87ac29cc30d9390760812ab47c63574054be6adc58` |
| Coin binding | `a6c070de492a343961a9bc213b1cf1df65fce32f122c6a3ebf1fa44c89ad3414` |
| Coin ViewProvider fixture | `0ec896bd30e5408dbd3f233910b282736322316ec14abfdbf36096fd907f617c` |
| Renderer-neutral preview | `0b0c19056de1b2a614536019288eaeec5c9db58961aa7df78056a38147d42279` |

An earlier excluded attempt produced no sample. Its run directory retained only
a pointer to the mutable launcher log, so it cannot independently substantiate
the within-session sandbox-denial diagnosis and no result relies on it. The
profiler now appends launcher output to a failed sample log; the fast contract
protects that retention path. After explicit host approval was saved, the same
profile command ran on the qualified host and therefore was not forced through
another artificial sandbox failure.

## Correctness and resource invariants

All three successful cold samples and all nine measured warm observations
preserved:

| Invariant | Observed in every fresh process |
| --- | ---: |
| Document objects | 32 |
| `App::FeaturePython` transition objects | 32 |
| Added display modes / switch children | 32 / 32 |
| Added ViewObject root children | 0 |
| Coin layer separators beneath the scene roots | 32 |
| Active Coin nodes below the 32 selectable roots | 224 |
| Objects with a `Shape` property | 0 |
| Stable identity digest | `a91f904211c50b6f265ab590e991abf3c9240b8f53a472ef8c1621b97efc9bc6` |

The layer count now traverses through each selection wrapper and binding scene
root to the actual Coin layer separators. The 224-node count is scoped to the
active disposable selectable subtrees: one selection root, scene root, layer
separator and four drawing nodes per object. It does not count FreeCAD's
surrounding viewer graph or transient candidate bindings. Both counts were
identical in all three fresh processes; cross-process node drift is rejected.

Cold construction regenerated exactly one preview per object. The explicit
recompute then caused one same-state callback per object, so the cold snapshot
contained 32 regenerations and 32 exact cache reuses. The recompute returned
`true` in every cold process. Every untimed and measured warm action made 32
requests, reused all 32 retained artifacts, regenerated none, reported zero
changed active scenes and kept the same 224 active nodes and identity digest.
All nine measured warm recomputes returned `false`, consistent with unchanged
document state.

Each process disposed all 32 proxies, discarded all 32 caches and closed its
document. No FreeCAD document or isolated process remained.

## Individual observations

Cold values are one sample per fresh process:

| Process | Wall ms | Process CPU ms | Recompute wall ms | RSS delta MiB | Ending RSS MiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 852.459 | 524.435 | 3.992 | 20.297 | 580.488 |
| 2 | 867.260 | 521.381 | 3.939 | 20.121 | 580.285 |
| 3 | 850.431 | 504.984 | 3.841 | 20.270 | 580.242 |

Warm values are three same-process measurements after one untimed warm-up:

| Process.iteration | Wall ms | Process CPU ms | Recompute wall ms | RSS delta MiB |
| ---: | ---: | ---: | ---: | ---: |
| 1.1 | 15.771 | 15.659 | 0.217 | 0.007812 |
| 1.2 | 19.298 | 18.599 | 0.212 | 0.007812 |
| 1.3 | 15.879 | 15.799 | 0.235 | 0.003906 |
| 2.1 | 16.283 | 16.043 | 0.327 | 0.003906 |
| 2.2 | 20.511 | 18.771 | 0.255 | 0.007812 |
| 2.3 | 15.225 | 15.100 | 0.223 | 0.003906 |
| 3.1 | 16.247 | 16.102 | 0.216 | 0.007812 |
| 3.2 | 19.330 | 18.683 | 0.216 | 0.007812 |
| 3.3 | 16.016 | 15.926 | 0.217 | 0.003906 |

## Summary

| Metric | Cold median (range), 3 processes | Warm median (range), 9 observations |
| --- | ---: | ---: |
| Wall time | 852.459 ms (850.431–867.260) | 16.247 ms (15.225–20.511) |
| Process CPU | 521.381 ms (504.984–524.435) | 16.043 ms (15.100–18.771) |
| Explicit recompute wall | 3.939 ms (3.841–3.992) | 0.217 ms (0.212–0.327) |
| End-minus-start RSS | 20.270 MiB (20.121–20.297) | 0.007812 MiB (0.003906–0.007812) |
| Ending RSS | 580.285 MiB (580.242–580.488) | 580.359 MiB (580.301–580.582) |

The ignored successful raw profile is under
`benchmark-output/freecad-bridge/phase5-transition-coin-resource-runs/20260729T161023330218Z-profile/`.
Its `performance.json` SHA-256 is
`1f98f994792f0230e9c098ed3622faf03319c7892d362ec428dde777bc7b428f`.
It retains every individual observation, source fingerprint and child log.

## Limitations and disposition

- Three cold processes meet the performance SOP minimum but are not a broad
  statistical sample. The nine warm observations are nested three per process
  and are not nine independent cold sessions.
- End-minus-start RSS is allocator- and page-accounting-sensitive and is not a
  peak-memory measurement. Active node snapshots do not expose the transient
  candidate Coin bindings, GPU resources or graphics-driver memory.
- The fixture uses one centreline layer per logical transition and nearby,
  partly overlapping geometries. It does not represent a complete railway
  layout, multiple visual layers, dense selection activity or exact/export
  geometry.
- The sampler does not click, edit, Undo/Redo, save or reopen. Existing
  single-object regressions own those behaviours; a justified representative
  multi-object workload, editing and selection remain separate work.
- No legacy renderer comparison, accepted threshold or user-perceived
  interaction budget exists, so the observed values are descriptive.
- No product source, runtime dependency, persisted schema, automatic load hook,
  exact geometry/export route or production output changed.

Disposition: **the bounded Coin candidate now has reproducible 32-object
object/layer, recompute, latency and end-state resource observations with
retained correctness checks.** This evidence does not establish a
representative workload, accept Coin as the renderer, close a Phase 5 exit,
freeze a budget or establish product-scale suitability.
