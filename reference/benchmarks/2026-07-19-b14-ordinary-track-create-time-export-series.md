# B14 Ordinary-Track Create-Time Export Series

Status: controlled three-run Phase 1 characterisation of B14's production
export inside the normal curve **Generate** action. It establishes the fixed
ordinary-track create-through-export success result and diagnoses the retained
partial output after an injected failure in the final planned task. It is not
an optimisation comparison, an accepted human-use budget, or an accepted
all-or-nothing failure contract.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260719T205947Z`, `20260719T210031Z`, `20260719T210124Z` |
| Run intervals | 20:59:47–21:00:22, 21:00:31–21:01:06, and 21:01:24–21:02:00 UTC on 2026-07-19 |
| Repository base | `13e38438d4aad364cc573ebe0e0cbf4c882add09`; this recipe and report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every run |
| Initial document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| Normalised create-time document SHA-256 | `a6aae6d70610ceec50a6223328db1454eca264effc12e7db5df07204707b3aa2` before save and after reopen in every run |
| Successful 14-file logical SHA-256 | `b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb` |
| Parsed production-metric SHA-256 | `37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4`, identical to selected export |
| Diagnosed partial-directory SHA-256 | `05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent and restored |
| Result | All assertions passed; nine objects after both actions and reopen; no unexpected dialog, transient object, temporary file or directory leak |

The bridge loaded B14 without executing its final launch call and operated only
on a timestamped fixture copy. Unlike selected export, the normal Generate path
persists its accepted production-export configuration; the recipe therefore
saves and reopens the copied document. It proves that removing only that
configuration from comparison leaves the original ordinary-track document
semantics unchanged, and separately requires the settings/template mirrors to
retain the exact scenario output directory before and after reopen. The source
fixture remains byte-identical.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-ordinary-create-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process drives B14's real `CurveInputDialog` and normal
**Replace all existing generated templates** path. It retains the fixed
`+90°`, 600 mm transition/radius, 32 mm main template, and one outside Track 2
configuration; leaves straight routes, platforms, formation, sectioning,
template assembly and labels disabled; and enables all four export formats,
individual plus combined output, and the CSV manifest in a fresh directory.
The driver accepts only the replacement question, production-export summary,
and final overall result dialog.

The process performs two actions:

1. a normal create-through-export action to a fresh directory; and
2. a later same-process replacement to another fresh directory, with the real
   exporter dispatcher made to fail only on deliverable task 13,
   `Curve_Set_001_Combined_Solid_Assembly.step`.

Preflight runs against temporary isolated documents and is never faulted. Both
actions require one 13-task preflight, ten DXF/SVG probe dispatches, thirteen
deliverable dispatches, one manifest attempt, stable nine-object document
semantics, and preference-store restoration.

## Successful production-output contract

The fixed four-record catalogue produces 13 format tasks plus one manifest:

| Format | Files | Total bytes |
| --- | ---: | ---: |
| DXF | 5 | 1,265,447 |
| SVG | 5 | 247,117 |
| STL | 1 | 419,684 |
| STEP | 2 | 6,632,304 |
| CSV manifest | 1 | 6,281 |
| **Total** | **14** | **8,570,833** |

All three runs report 14 successful files, no failure or skip, all four
formats, and a created manifest. The manifest retains the frozen 21-column
schema and contains 15 success rows. The complete normalised output map has
logical SHA-256
`b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb`
in every process.

Freshly generated create-time shapes do not have the exact same serialisation
hash as shapes loaded from the selected-export fixture. The selected-export
logical hash is
`91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413`.
The five normalised DXF files and manifest agree across the two paths; the five
SVG, two STEP and one STL serialisations differ. This distinction is retained
rather than normalised away.

Production equivalence is checked independently. Every DXF/SVG parsed bound,
STEP topology/measure and STL mesh measure is identical to the established
selected-export contract, producing metric SHA-256
`37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4`.
Representative shared measures are:

| Output | Contract |
| --- | --- |
| Template/combined STEP | Valid `Compound`; 2 solids, 2,104 faces, 6,300 edges; bounds `988.296355 × 988.295255 × 1.000000 mm`; volume `101432.346379 mm³` |
| Template STL | 8,392 facets, 4,200 points; bounds `988.296326 × 988.295227 × 1.000000 mm`; volume `101433.132813 mm³` |
| Template/cutting DXF | XY span `988.296355019 × 988.295255315 mm` |
| Template/cutting SVG | XY span `1008.062282120 × 1008.061182415 mm` |
| Main Track centreline DXF | XY span `922.296455675 × 922.295255313 mm` |
| Track 2/engraving DXF | XY span `972.296355021 × 972.295255315 mm` |

This is evidence of equivalent production measures for the fixed fixture, not
permission to ignore future serialisation changes.

## Final-task failure diagnosis

B14 commits the FreeCAD replacement transaction before calling
`run_production_export()`. That exporter writes and replaces each destination
independently, catches a task exception, continues, and then writes a manifest.
The deterministic final-task injection demonstrates the consequence in every
run:

- twelve task files remain committed;
- the CSV manifest is also committed, for 13 files reported as successful;
- `Curve_Set_001_Combined_Solid_Assembly.step` is absent;
- the 15-row manifest contains 14 `Success` rows and one `Failure` row with the
  exact missing filename, STEP format and injected reason;
- the directory has stable content SHA-256
  `05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29`;
- no temporary file/directory or FreeCAD object remains; and
- the document retains the same normalised semantic hash as the successful
  action and survives save/reopen.

The output set is therefore explicitly **not atomic**. This is a bounded B14
defect diagnosis, not the intended migrated behaviour. A future production
path must adopt an agreed all-files staging, manifest, rollback and cleanup
contract before legacy removal.

The intermediate **Production export complete** summary reports one failure,
but the later overall dialog is still titled **Railway production outputs
created** and begins “created successfully”. Its details do disclose
`13 successful files; 1 failed`. The contradictory overall success wording is
also retained as a correctness/UI obligation.

## Timing observations — not accepted budgets

The first action is the comparable cold create-through-export boundary in each
fresh process. It begins before the real curve dialog and ends after the final
overall dialog. It includes dialog/confirmation, analytical and exact-shape
generation, replacement transaction, production preflight, actual export,
schedule/material report, recomputes and result UI. It excludes process launch,
B14 load, fixture open, output parsing, save/reopen and the later injected
failure action.

| Successful create-through-export metric | Run 1 | Run 2 | Run 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete action wall time | 6,886.804 ms | 6,907.971 ms | 6,984.403 ms | **6,907.971 ms** | 97.599 ms |
| Process CPU time | 8,415.741 ms | 8,410.895 ms | 8,542.684 ms | **8,415.741 ms** | 131.790 ms |
| RSS end-minus-start | +264.113 MB | +258.719 MB | +259.992 MB | **+259.992 MB** | 5.395 MB |
| Object delta | 0 | 0 | 0 | **0** | 0 |

The single complete exporter-bound preflight had a median `1450.616 ms`
(range `1427.015–1481.591 ms`) and exactly one non-blocking
`OUTPUT_DIRECTORY_WILL_BE_CREATED` information item. The actual 13-task plus
manifest export had a median `2883.880 ms` (range
`2802.316–2886.101 ms`). The remaining dialog, geometry/document, reports,
recompute and final-UI work was about `2.62 s` per action. No nested duration
is added to the complete boundary.

The later final-task failure is a same-process correctness observation, not a
cold benchmark. Its complete-action median was `5757.045 ms` (range
`5680.635–5772.614 ms`), and its export median was `2115.484 ms` (range
`2063.468–2117.244 ms`). It is faster principally because the final combined
STEP writer is deliberately not executed; that is not a performance benefit.

The complete development recipe, including both dialog actions, output and
semantic analysis, save/reopen and cleanup, had a three-process median
`32.105 s` (range `32.079–32.113 s`). It is harness duration, not an operator
action.

## Exact recipe-source state

Every included `run.json` recorded the same source map:

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/freecad_export_metrics.py` | `bac9e12112f707a73c135bba9df6481b7fae22de3f3b98675b3f2987c6049c71` |
| `tools/freecad_bridge/ordinary_track_export_recipe.py` | `f4c91461264997c19dc080fd026409bf41c28678bfbff7787c4354c061968423` |
| `tools/freecad_bridge/probes/b14_ordinary_create_export_driver.py` | `5a9ed6990adba8dcc4680e482eee9797e53e2aaa0002142d932d5c3c9f79584f` |
| `tools/freecad_bridge/run_b14_ordinary_create_export.py` | `0768edf6c9d25bc320f0bc1eebd0d711116487aa8c939ed0222cc5ae318f388a` |
| `tools/freecad_bridge/run-b14-ordinary-create-export` | `8bff9b230512b85d46ae849d60e42795d17dec4b37e3903e9d8c3fb9e170eff8` |
| `tests/validate_phase1_ordinary_export.py` | `f93f4b758c323f5bc6a648127b5430eb6bea01f6ae50a041492ec834a70470bf` |

## Ignored raw evidence

Generated exports, copied FCStd files and JSON containing local absolute paths
remain ignored under
`benchmark-output/freecad-bridge/ordinary-create-export-runs/`.

| Run | `run.json` (bytes; SHA-256) | Saved copied FCStd (bytes; SHA-256) | Success / diagnosed-failure outputs |
| --- | --- | --- | --- |
| `20260719T205947Z` | 67,548; `670f9279a4f943695d37e1b17d7ca25a89a5ecb018f36aa0e7db58d72be2b6e9` | 636,448; `104dc7d6778a516d1518bede180865ef294bc87e156ca592c4e710a900491190` | 14 files / 8,570,833 bytes; 13 files / 5,254,915 bytes |
| `20260719T210031Z` | 67,561; `a4aee9ea3e19b1c7df74972658be0ca9bab1a97366be1e723614321c8579a7c3` | 636,470; `ebcdaca3bf067b9937e1e0499a6e48cb47543108219cafb59070f9b877741f7e` | 14 files / 8,570,833 bytes; 13 files / 5,254,915 bytes |
| `20260719T210124Z` | 67,566; `d396fa1414f76b99951cb4498ee076c71f812c8ae46a558efb6b36f3d16dbc68` | 636,443; `0ccc5252dd34c5d8ebe87a0ab022f2cfbbd9bed04c6eee7b532951d512c9b56e` | 14 files / 8,570,833 bytes; 13 files / 5,254,915 bytes |

Different copied-FCStd bytes are expected FreeCAD serialisation; every saved
copy has the same normalised document hash and the immutable source fixture is
unchanged.

## Coverage boundary

This tranche closes the fixed ordinary-track create-time export
characterisation gap for one normal replacement, one complete template-set
scope, all four formats, manifest content, deterministic repeat, document
persistence and a deterministic final-task failure. It supplies one bounded
legacy create-through-export performance profile.

It does not fix the partial-output or contradictory success-dialog defects,
establish cancellation semantics, test existing-file revision/overwrite on
this path, cover other entity families, or implement/measure future explicit
Validate and deferred exact-shape reconstruction. The explicit selected-export
transaction remains a separate oracle. Phase 1 remains open.
