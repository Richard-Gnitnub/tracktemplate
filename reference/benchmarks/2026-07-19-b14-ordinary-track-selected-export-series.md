# B14 Ordinary-Track Selected-Export Series

Status: controlled three-run Phase 1 characterisation of B14's explicit
**Export selected production items** path. It establishes deterministic
ordinary-track DXF, SVG, STL, STEP and CSV output, non-overwrite revisioning,
confirmed atomic overwrite, and rollback after an injected mid-commit failure.
It is not an optimisation comparison, an accepted human-use budget, or a
complete curve-to-export product benchmark.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260719T201140Z`, `20260719T201305Z`, `20260719T201431Z` |
| Run intervals | 20:11:40–20:12:57, 20:13:05–20:14:22, and 20:14:31–20:15:47 UTC on 2026-07-19 |
| Repository base | `b760c5b0d4e8b046295250b7368d8e6c3ba36f65`; the export recipe and this report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every run |
| Initial document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` before and after every scenario |
| Logical 14-file export SHA-256 | `91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent |
| Result | All assertions passed; nine objects before and after every action; no unexpected dialog or temporary object/directory leak |

The bridge loaded B14 without executing its final launch call and operated only
on a timestamped copy. The copied FCStd and source fixture retained the exact
binary hash above because the recipe never saves either document.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process opens B14's real `SelectedProductionExportDialog`, selects
the complete `SET-001` template set, all four available formats, individual and
combined outputs, a CSV manifest, and exporter-bound DXF/SVG probes. It then:

1. creates the 14 planned base files;
2. repeats with overwrite disabled and requires the 14 `_Rev_02` files while
   proving the base files are byte-identical;
3. replaces the base manifest with a sentinel, confirms overwrite, requires
   the sentinel to be replaced atomically, and proves the revision files are
   byte-identical; and
4. injects an exception at the fourth real `os.replace()` call inside
   `commit_staged_export_entries()`, after one replacement has committed and a
   second destination has moved to backup, then requires rollback to restore
   every destination byte and remove staging directories.

The driver accepts only the selected-export confirmation and completion
dialogs. Any warning/error dialog or changed dialog identity fails the run.

## Production-output contract

The fixed four-record production catalogue produces 13 format tasks plus one
manifest:

| Format | Files per variant | Total bytes in the base variant |
| --- | ---: | ---: |
| DXF | 5 | 1,265,447 |
| SVG | 5 | 246,739 |
| STL | 1 | 419,684 |
| STEP | 2 | 6,632,272 |
| CSV manifest | 1 | 6,011 |
| **Total** | **14** | **8,570,153** |

The manifest has the frozen 21-column schema, 15 success rows, formats
`DXF`, `SVG`, `STL`, and `STEP`, and no skipped or failed record. The base,
revision and overwrite variants all have logical SHA-256
`91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413`
in every fresh process.

The logical comparison preserves raw hashes and normalises only known
producer/allocation metadata:

- manifest timestamps, output roots and the allocator's `_Rev_02` suffix;
- declared volatile DXF header values and temporary FreeCAD export-object IDs;
- temporary export-object IDs in SVG; and
- STEP `FILE_NAME` path/time plus the observed Open CASCADE transient product
  counter.

STL bytes are not normalised. Each DXF and SVG is also parsed through B14's
scale/bounds validators; each STEP is read back through `Part.Shape`; and the
STL is read through `Mesh.Mesh`. The metrics were identical for base,
revision and overwrite in every run.

Representative frozen geometry checks are:

| Output | Contract |
| --- | --- |
| Template/combined STEP | Valid `Compound`; 2 solids, 2,104 faces, 6,300 edges; bounds `988.296355 × 988.295255 × 1.000000 mm`; volume `101432.346379 mm³` |
| Template STL | 8,392 facets, 4,200 points; bounds `988.296326 × 988.295227 × 1.000000 mm`; volume `101433.132813 mm³` |
| Template/cutting DXF | XY span `988.296355019 × 988.295255315 mm` |
| Template/cutting SVG | XY span `1008.062282120 × 1008.061182415 mm` |
| Main Track centreline DXF | XY span `922.296455675 × 922.295255313 mm` |
| Track 2/engraving DXF | XY span `972.296355021 × 972.295255315 mm` |

The STEP/STL volume difference is the current exporter/mesh representation
and is frozen separately; it is not silently rounded into equality.

## Transaction, document and cleanup results

All three runs proved:

- base creation reports 14 successes and no failures;
- non-overwrite repeat reports 14 `EXISTING_FILE_REVISION` information items,
  creates only `_Rev_02`, and leaves all base raw hashes unchanged;
- overwrite reports 14 `EXISTING_FILE_OVERWRITE` warnings, replaces the
  sentinel, and leaves all revision raw hashes unchanged;
- injected commit failure reports zero successful files and one failure with
  the exact injected reason;
- the actual commit receives all 14 staged entries and performs six replace
  calls including rollback restoration;
- the 28 destination-file raw-hash map before and after failure is identical,
  with normalised directory content SHA-256
  `ef5e2310cae73c38fa31d8d79d83f2d8fa7d4f055b810addbde7769ae5e879e3`;
- no `.railway_selected_export_*` or backup directory remains; and
- document semantics, the nine-object inventory, source fixture and copied
  FCStd remain unchanged.

## Timing observations — not accepted budgets

The first base export is the comparable cold action in each fresh process. Its
boundary begins before real dialog construction and ends after the completion
dialog and post-success preview refresh. It excludes process launch, B14 load,
fixture open, pre-action semantic hashing, output-oracle parsing and the later
correctness scenarios.

| Initial selected-export metric | Run 1 | Run 2 | Run 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete action wall time | 7,788.967 ms | 7,991.619 ms | 7,885.730 ms | **7,885.730 ms** | 202.652 ms |
| Process CPU time | 9,306.047 ms | 9,432.016 ms | 9,346.004 ms | **9,346.004 ms** | 125.969 ms |
| RSS end-minus-start | +134.996 MB | +157.281 MB | +131.543 MB | **+134.996 MB** | 25.738 MB |
| Object delta | 0 | 0 | 0 | **0** | 0 |

The initial action's selected-export staging/write/commit/cleanup transaction
had a median of `3084.831 ms` (range `3032.293–3121.359 ms`). Three complete
probe preflights consumed a combined median `4035.036 ms` (range
`3923.687–4064.259 ms`), about 51% of the complete action. Each action made
43 exporter dispatches: 10 DXF/SVG probe writes in each of three full
preflights, then 13 deliverable writes. The late no-probe safety preflight was
separately small, with a 12-observation median `66.551 ms`.

This makes repeated full exporter-bound probing the first measured
selected-export optimisation candidate. The current late filename recheck,
confirmation contract, validation scope and post-action state must remain
correct; this report does not authorise simply deleting checks.

The later same-process actions are correctness observations, not equivalent
cold benchmarks:

| Later action | Wall median (range) | Selected transaction median (range) |
| --- | ---: | ---: |
| Non-overwrite revision | 7,793.599 ms (7,663.637–7,958.578) | 3,129.921 ms (3,086.762–3,164.673) |
| Confirmed overwrite | 7,851.404 ms (7,771.287–8,089.159) | 3,079.828 ms (3,048.325–3,091.694) |
| Injected commit failure/rollback | 7,730.836 ms (7,675.619–7,916.376) | 3,047.776 ms (3,014.233–3,082.085) |

The complete development recipe, including four dialog actions plus semantic,
raw-file and format-oracle analysis, had a three-process median `73.179 s`
(range `72.740–73.555 s`). It is test-harness duration, not an operator action.

## Exact recipe-source state

Every `run.json` recorded the same source map:

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/ordinary_track_export_recipe.py` | `a2ea02bcd028f1d3bf0897d0ad861444f8b677b8bcfad85623bde3d04b3e2f72` |
| `tools/freecad_bridge/probes/b14_ordinary_export_driver.py` | `d3e8f8c18c96aef1951383751e5726b40a2495673e3561ed2c9c6d660cb0de94` |
| `tools/freecad_bridge/run_b14_ordinary_export.py` | `64500df7ca7e437d68f23f0dcd9974211638a0830838ff465948bc4beb2652da` |
| `tools/freecad_bridge/run-b14-ordinary-export` | `f0a6bcfd2b947c1a78a441e85ec6a4407a28215e1e1347064230d8192227273a` |
| `tests/validate_phase1_ordinary_export.py` | `06aab1712c284a5fd3fb2b2e0c196e720a11cb1d4e216d2627d24a9d36523011` |

## Ignored raw evidence

Generated exports, copied FCStd files and JSON with local absolute paths remain
ignored under `benchmark-output/freecad-bridge/ordinary-export-runs/`.

| Run | `run.json` (bytes; SHA-256) | Copied FCStd (bytes; SHA-256) | Output directory |
| --- | --- | --- | --- |
| `20260719T201140Z` | 328,699; `3be3d7adc7b47adb72e6ef947adb52efb6506cda264ce72c0d7d22f1bb3e1770` | 636,344; `0a655275…02ab8c` | 28 files; 17,140,516 bytes |
| `20260719T201305Z` | 328,690; `395a1961c43393c0967eb3322f7c6b353a1b7dec3e79f29c3a3eb3c9e04e585f` | 636,344; `0a655275…02ab8c` | 28 files; 17,140,516 bytes |
| `20260719T201431Z` | 328,687; `67a8c87e9217f629cddb7a88bff1cb73bf10235439249c47d6b260f0eb4187a0` | 636,344; `0a655275…02ab8c` | 28 files; 17,140,516 bytes |

## Coverage boundary

This tranche closes the fixed ordinary-track explicit selected-export gap for
one complete template-set scope, all four current formats, manifest content,
non-overwrite revisioning, confirmed overwrite, deterministic repeat,
mid-commit rollback and cleanup. It exports exact shapes already retained in
the legacy fixture; it does not measure or validate future deferred exact-shape
reconstruction.

B14's create-time export after `run_macro()` commits the document uses the
separate `run_production_export()` path. That path commits successful files one
at a time and can retain them if a later task fails, so it is neither covered
by nor equivalent to this selected-export transaction. Cancellation, other
selection scopes, straight/station, standalone turnout/crossover, platform,
formation and chair export families also remain open. Phase 1 remains open.
