# Phase 5 Transition Interaction/Resource Range Profile

Status: **completed Level 2 bounded observations on 2026-07-31; no product
capacity, interaction budget, renderer, optimisation or Phase 5 exit is
accepted.**

## Scope and derivation

This profile repeats the already qualified one-secondary-track Entry/Exit
family unit at 1, 2, 4, 8 and 16 set counts. The resulting 2–32 logical
objects span powers of two up to the preceding 32-object diagnostic ceiling.
They expose scaling observations; they are not accepted product populations,
support expansion or representative whole-layout documents.

Every record retains its canonical local transition frame. A test-only Coin
translation arranges the repeated pairs in a four-column view grid so a real
mouse click can resolve one target at every scale. The translation is neither
stored nor read as railway truth, is absent from product source and adds one
diagnostic Coin node per object. The selected target is the middle set's Exit.

Each fresh process performs these boundaries:

1. **Cold construction:** create a new document, batch-create all compact
   canonical records, build one renderer-neutral preview, cache, ViewProvider,
   Coin layer and view translation per record, recompute, fit and redraw.
2. **Selection:** after an excluded read-only projected-point locator has found
   one object/sublayer mapping, move the Qt pointer, click the real 3D widget
   and process the fixed GUI event cycles.
3. **Dialog open:** construct and show the existing transient parameter editor
   for the selected stable identity.
4. **Edit:** use real Qt focus, mouse and keyboard input to replace `420.000`
   with `360.000`, click Apply and process the existing application command,
   transaction and derived-view refresh.
5. **Undo:** invoke one document Undo and process GUI events.
6. **Cleanup:** close the dialog, clear selection, dispose every proxy and
   cache, and close the document.

Process launch, bridge readiness, the read-only target locator, post-action
assertions and host cleanup checks are outside the measured action spans.

## Source state, environment and recipe

The measurement started from protected-main commit
`4070a2f461a9a23bba6df9bddc522fa98e13572a` on branch
`agent/phase5-transition-interaction-range`. The working tree contained only
the six connected profiler, GUI sampler, focused-validator, benchmark,
validation-document and current-evidence files.

- Recorded: 2026-07-31 17:58:28–18:00:24 UTC.
- Host: Linux 7.0.0-28-generic x86_64, AMD Ryzen 5 5500, 12 logical CPUs,
  31.2 GiB physical memory.
- Host profiler: CPython 3.12.3 from the repository virtual environment.
- GUI runtime: qualified Flatpak FreeCAD 1.1.1, revision 44874.
- Repetition policy: three fresh isolated GUI processes per scale, 15 total;
  the second series ran in reverse scale order.
- Starting state: empty document set, new document and empty per-object preview
  caches in every fresh process.
- Operating-system file, allocator, graphics-driver and GPU caches were
  uncontrolled.

The reproducible command was:

```bash
.venv/bin/python tools/phase5_transition_interaction_range_profile.py
```

Principal measured-source SHA-256 fingerprints were:

| Input | SHA-256 |
| --- | --- |
| GUI sampler | `85c29b8ab6a83e9cac92d088428e5a7c98f7ba32efc26fc4c63506a94a3d4005` |
| Host profiler | `7404ef4a3d147bd8a703fad8a1ea936ab0c03f9ba7a9b71116108082bd22eeac` |
| Shared GUI harness | `ca21a376c9de3ce1889da9ddac0187a26c5d30387aab7b0826cfe0bddeb33193` |
| Qualified Entry/Exit workload | `908519580389b3431b10805bf7c1054bedcd81dee0585f662e54115ddb521482` |
| FreeCAD transition adapter | `7485f5a784cda9688e9fa8e578a86ea34325fc71045204078bf127b1b1d70dc3` |
| Transition edit command | `7a08cbf1f95fe0b120f392d2f173ca4b4e559e5250f674dc47eff207c61c6d2b` |
| Coin binding | `a6c070de492a343961a9bc213b1cf1df65fce32f122c6a3ebf1fa44c89ad3414` |
| Coin ViewProvider fixture | `0ec896bd30e5408dbd3f233910b282736322316ec14abfdbf36096fd907f617c` |
| Renderer-neutral preview | `0b0c19056de1b2a614536019288eaeec5c9db58961aa7df78056a38147d42279` |
| Parameter editor | `c677c9a058b9ece23247b1526b9104186a923690c041fcb005a13ae5ec574da4` |

## Correctness invariants

Every sample passed before its measurements were admitted:

- document objects, logical Coin layers and proxies equalled the declared
  2–32 logical-object scale;
- active test-scene nodes were exactly eight per object, including the one
  test-only translation, from 16 through 256 nodes;
- every object remained compact `App::FeaturePython` state with zero `Shape`
  properties;
- stable visual-to-domain mapping digests matched across all three fresh
  processes at each scale and remained unchanged through edit and Undo;
- the real click selected only the declared Exit object and stable subelement;
- the dialog showed that identity and `420.000` before editing;
- exactly the selected record and cache changed, exactly one Undo unit was
  created, and Undo restored the complete initial canonical-state digest;
- every sibling record remained unchanged; and
- all proxies and caches were disposed and no document or isolated FreeCAD
  process remained.

At 32 objects the read-only hit test returned three neighbouring Coin segment
records, but all three resolved to the same object and stable subelement. The
subsequent real Qt click selected exactly that object/sublayer mapping. Raw-hit
cardinality is retained separately from the one-mapping assertion.

## Observations

Wall and process-CPU values are milliseconds. RSS is end minus start in MiB,
not a sampled peak. Every entry is the median of three fresh processes; ranges
are shown for wall and cold RSS.

| Sets | Objects / active nodes | Cold wall median (range) | Cold CPU median | Cold RSS median (range) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2 / 16 | 819.797 (663.115–825.715) | 333.367 | 19.938 (19.938–19.938) |
| 2 | 4 / 32 | 787.211 (781.456–832.600) | 303.311 | 33.020 (19.801–35.367) |
| 4 | 8 / 64 | 851.415 (837.384–875.255) | 384.947 | 19.988 (18.984–19.988) |
| 8 | 16 / 128 | 915.636 (897.853–916.645) | 474.802 | 20.066 (19.910–35.629) |
| 16 | 32 / 256 | 1003.011 (957.727–1046.302) | 523.542 | 35.668 (20.246–35.695) |

| Sets | Select wall median (range) | Select CPU median | Dialog wall median | Edit wall median (range) | Edit CPU / RSS medians | Undo wall median (range) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 31.391 (10.090–41.394) | 7.529 | 3.763 | 81.952 (63.777–101.726) | 30.399 / 0.656 | 7.065 (6.865–7.393) |
| 2 | 24.712 (20.751–25.242) | 7.345 | 3.950 | 112.099 (90.681–119.159) | 35.849 / 0.883 | 17.201 (16.668–17.985) |
| 4 | 24.989 (8.280–25.312) | 6.404 | 3.852 | 108.047 (93.309–111.024) | 33.627 / 0.875 | 15.453 (15.015–18.204) |
| 8 | 25.329 (24.956–36.094) | 7.485 | 4.105 | 104.825 (104.454–105.347) | 40.633 / 0.879 | 20.317 (18.988–22.185) |
| 16 | 24.283 (23.188–55.109) | 7.152 | 3.887 | 93.425 (85.240–97.059) | 38.907 / 0.871 | 19.628 (18.903–19.912) |

Across this bounded series, individual selection observations were
8.280–55.109 ms and edit observations were 63.777–119.159 ms. These are
descriptive ranges, not pass thresholds or operator-perception budgets. The
non-monotonic action medians and roughly 35.4–35.7 MiB cold-RSS observations
at 4, 16 and 32 objects make an optimisation or simple linear-scaling claim
inappropriate.

The ignored successful raw profile is under
`benchmark-output/freecad-bridge/phase5-transition-interaction-range-runs/20260731T175828303329Z-profile/`.
Its `performance.json` SHA-256 is
`17404e205578bbffb19d9908aabeeaaa388650c365fdc8bed87c241b0b37e510`.
It retains all 15 samples, source fingerprints, alternating order and child
logs.

## Failed-proof adjudication

The test-first standalone command failed because the authorised profiler did
not yet exist, classified `implementation-defect`. A synthetic Undo record
then omitted two required cache deltas, classified `fixture-or-harness-defect`.
The first qualified sample exposed two new-oracle defects: cold recompute
correctly reused one preview per object, and analysed lengths were equal only
within the existing `GEOMETRY_TOLERANCE`. The 32-object probe then showed that
several raw segments can still resolve one unambiguous object/sublayer mapping,
classified `fixture-or-harness-defect`; the real-click assertion was retained.
The original proofs passed after each bounded repair. Separate sandboxed
attempts that never obtained bridge readiness were
`environment-or-profile-defect` results and supplied no product evidence.

## Limits and disposition

- Repeating one qualified pair does not create an accepted wider product
  family, whole-layout population, supported document size or migration path.
- The view grid is diagnostic instrumentation. It does not prove or prescribe
  product placement, composition, style or layer grouping.
- Three fresh processes per scale meet the SOP minimum but are not a broad
  statistical sample. UI event scheduling and graphics timing remain noisy.
- Selection excludes the read-only target locator. Edit includes synthetic Qt
  keyboard/button actions and fixed event cycles, not human hesitation or a
  complete perceived-latency study.
- RSS is allocator-sensitive end-minus-start data; it is not peak memory and
  excludes GPU/driver resources.
- The profile does not repeat save/reopen, injected failure recovery or Redo;
  the existing retained GUI regression continues to own those behaviours.
- Automatic product load/composition, the residual empty switch child, exact
  geometry/export, migration, production output and owner acceptance remain
  outside scope.

Disposition: **the Coin candidate now has reproducible correctness and
descriptive selection/edit/resource observations over repeated qualified
family units from 2 through 32 logical objects.** This materially improves the
owner's decision evidence but does not accept the range as product capacity,
approve Coin, close a Phase 5 exit or set a numerical budget.
