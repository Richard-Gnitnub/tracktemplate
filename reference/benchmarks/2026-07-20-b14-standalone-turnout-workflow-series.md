# B14 Standalone Turnout Workflow Series

Status: controlled three-run Phase 1 characterisation of one bounded B14 REA
C10 standalone-turnout lifecycle. This is a legacy correctness oracle and a
deterministic development recipe. It is not canonical production data, an
optimisation comparison, an accepted latency budget, or complete turnout
coverage.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260720T165250Z`, `20260720T165336Z`, `20260720T165421Z` |
| Run intervals | 16:52:50–16:53:24, 16:53:36–16:54:09, and 16:54:21–16:54:54 UTC on 2026-07-20 |
| Recipe | `phase1-b14-standalone-turnout-lifecycle-v1` |
| Repository base | `5b24d09ebd02c0149569107243a0377e49cb3263`; the oracle and this report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every included run |
| Initial complete-document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| Created left-hand semantic SHA-256 | `0738c5a639618739c69fcd06553ea0584c5bf8c51253c330e3374f39e437c1cb` |
| Edited right-hand semantic SHA-256 | `46225072b4b56f7f767570c8b438ee0942c239f73f121ce420aa76caed9779f0` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; repository-local isolated preference profile |
| Result | All assertions passed; source fixture unchanged; copied document closed; no unexpected dialog or surviving bridge process |

Two preceding fresh-process qualification runs produced the same created and
edited hashes. The hashes were then frozen in the recipe before the three
included controlled runs, so every included run actively rejected semantic
drift.

The semantic hash covers the selected host identity and placement basis, B14's
persisted turnout catalogue, every turnout object's stable identity, typed
properties, configuration, group membership and exact-shape summary, and the
complete copied-document state and ordered production-record catalogue.
FreeCAD archive hashes remain non-semantic because FCStd serialisation contains
volatile data.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-turnout \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process performs these actions in order:

1. Copy and open the fixed nine-object, two-track curve document; require an
   empty FreeCAD history and validate the existing plain-line oracle.
2. Open B14's real turnout/crossover manager. Resolve `SET-001` Main Track by
   persisted template-set, track-number and track-name identity rather than UI
   row order, and place the switch toe at host chainage `746.298 mm`.
3. Create `TO-001` through the real manager as an REA C10 natural left-hand
   turnout, facing in host travel direction, with `16.5 mm` gauge, `1.0 mm`
   flangeway and the default timber-outline, timber-number and construction-
   datum choices.
4. Validate the complete document, apply the single creation Undo and Redo,
   and require exact recovery of the initial and created semantic states.
5. Re-enter the real edit mode, change only the handing to right-hand, approve
   the exact change summary, and require stable object names, unchanged host
   plain-line geometry and a changed frozen semantic result. Apply the single
   edit Undo and Redo and require exact state recovery.
6. Attempt a second turnout at the occupied chainage and require B14 to reject
   the overlap before document or history mutation.
7. Re-enter edit mode and temporarily fail the first generated-object tagging
   call. Require B14's real `abortTransaction()` path to report the injected
   error and restore the accepted right-hand document and history exactly.
8. Save, close and reopen the copied document; require exact right-hand
   semantics, 17 objects and cleared reopened history. Capture the final top
   view, manager and complete FreeCAD window, verify the source fixture hash,
   close the copied document and stop only the isolated bridge process.

Dialog automation accepts only the expected creation result, handing-change
confirmation, overlap diagnostic and injected-failure diagnostic. Any other
visible message box fails the recipe.

## Analytical and placement contract

The fast oracle extracts only the relevant B14 and B15 definitions and proves
their AST and result parity without importing either macro. It freezes these
REA C10 values at the controlled `16.5/1.0 mm` input:

| Quantity | Characterised value |
| --- | ---: |
| Module start / end X | `-21.666666666667 / 361.399567103881 mm` |
| Switch / turnout radius | `3840 / 2769.887101251726 mm` |
| Fine point / vee joint X | `283.390217361099 / 341.399567103881 mm` |
| Rail-head width / knuckle radius | `0.916666666667 / 40 mm` |
| Fixed Main Track host length | `1542.475839 mm` |
| Facing valid toe range | `21.666666666667–1181.076271896119 mm` |
| Occupied host-station interval at the chosen toe | `724.631333333333–1107.697567103881 mm` |

Facing orientation maps along host travel; left and right handing use opposite
normal signs. The live recipe deliberately fixes facing orientation and edits
only the hand. Trailing orientation is calculation-characterised by the fast
test but is not exercised through the GUI in this tranche.

Placement is defined only by persisted centreline identity plus host
chainage. No UI position or unanchored XYZ datum forms part of the contract.

## FreeCAD, persistence and production contract

Creation adds eight stable turnout roles and changes the document from 9 to 17
objects:

- `TurnoutGroup`, `TurnoutSettings`, `TurnoutTemplate` and
  `TurnoutPlanOutline`;
- `TurnoutRailGeometry`, `TurnoutTimberGeometry`, `TurnoutTimberLabels` and
  `TurnoutConstructionMarks`.

The six shape-bearing outputs are valid; `TurnoutSettings` is deliberately
null, and the group contains every other turnout object. All eight objects
carry the same typed `TO-001` configuration and persisted Main Track identity.
The legacy turnout record contains 40 timbers, timber/rail geometry revision
2, and a recorded total timber length of `1640 mm`.

The ordered production catalogue retains the four inherited curve records and
adds six turnout records: solid template, 2D cutting profile, rail engraving,
timber-outline engraving, timber-label engraving and construction-datum
engraving. The resulting ten records retain the expected direct bindings,
track/feature identity and supported STL/STEP or DXF/SVG formats.

Changing the hand retains every turnout object name and all inherited curve
Template, Centreline and hidden ProductionSource geometry exactly. The hash
captures the expected mirrored turnout shapes and configuration rather than a
FreeCAD process-local shape hash code.

## Edit history and recovery contract

Creation adds exactly one history entry,
`Create Version 10.2A8A7B14 REA C10 turnout`. Editing adds exactly one newer
entry, `Edit Version 10.2A8A7B14 turnout TO-001`. Each Undo/Redo pair restores
the complete preceding and accepted semantic state, respectively.

The occupied-chainage rejection leaves 17 objects, both history entries and
the right-hand hash unchanged. The injected failure occurs on the first
tagging call inside the edit transaction; after abort it also leaves the exact
right-hand document and history unchanged. Save/reopen preserves that semantic
state and intentionally clears FreeCAD history.

This bounded path therefore does not exhibit the separate three-entry B14
plain-line/straight replacement defect. It characterises one atomic turnout
create command and one atomic turnout edit command for later migration
comparison.

## Timing observations — not accepted budgets

Action measurements end when B14's modal manager action returns and exclude
the subsequent deep semantic walk. History-cycle and save/reopen figures
include deep validation, so they are diagnostic harness timings rather than
operator-visible action latency. RSS is an end-minus-start snapshot, not a
sampled peak; CPU above wall time reflects FreeCAD process work across cores or
accounting overlap.

| Scenario | Run 1 | Run 2 | Run 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Create left/facing wall | 1729.892 ms | 1743.967 ms | 1763.749 ms | **1743.967 ms** |
| Create process CPU | 2826.849 ms | 2857.610 ms | 2879.722 ms | **2857.610 ms** |
| Create RSS end-minus-start | +54.789 MB | +54.738 MB | +53.770 MB | **+54.738 MB** |
| Edit hand wall | 1977.051 ms | 1982.509 ms | 1960.199 ms | **1977.051 ms** |
| Edit process CPU | 3172.959 ms | 3045.913 ms | 3181.168 ms | **3172.959 ms** |
| Edit RSS end-minus-start | +47.480 MB | +43.438 MB | +39.031 MB | **+43.438 MB** |
| Reject overlap wall | 141.313 ms | 143.094 ms | 121.992 ms | **141.313 ms** |
| Injected edit abort wall | 822.281 ms | 825.832 ms | 809.534 ms | **822.281 ms** |
| Creation Undo+Redo plus deep validation | 3143.538 ms | 3156.448 ms | 3126.425 ms | **3143.538 ms** |
| Edit Undo+Redo plus deep validation | 4043.848 ms | 4116.493 ms | 4018.802 ms | **4043.848 ms** |
| Save/close/reopen plus deep validation | 2922.787 ms | 2762.449 ms | 2822.163 ms | **2822.163 ms** |
| Complete orchestrated recipe | 27.494 s | 27.412 s | 27.133 s | **27.412 s** |

The median whole-session resident-memory change was `+375.387 MB` (range
`+301.590–+385.219 MB`), including repeated deep snapshots and final GUI
evidence capture. It is not a peak-memory measurement or a product budget.
Future lightweight editing and deferred Validate/Export must be measured at
their own boundaries under the performance SOP.

## Exact recipe-source state

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/turnout_recipe.py` | `d6583922bd835898b38d306d9da98452fdfde32852d796978fd88db0d8033636` |
| `tools/freecad_bridge/probes/b14_turnout_driver.py` | `3690da816f5867a77e6f6f59af0a8a1779d7aaedd80dc41841340107e7de4d16` |
| `tools/freecad_bridge/run_b14_turnout.py` | `c3e75521489a79841895c786200cc3f63f271405510d5e7d60af249a96c79a7c` |
| `tools/freecad_bridge/run-b14-turnout` | `a4503ddc64561edefae885247aec7e2956147accf58628326984c2906eec4d51` |
| `tests/validate_phase1_turnout.py` | `adea9884931e21e97f617ba8fe3569d87f71e44fe3bc48c86dba34d338180963` |
| `tests/validate_freecad_bridge.py` | `ee1f840f64514fe7352787e3dde7963b46231cef5213dfa4633e007531f298cd` |

## Ignored raw evidence

Raw artifacts include local absolute paths and generated FreeCAD data, so they
remain ignored under `benchmark-output/freecad-bridge/turnout-runs/`.

| Run | `run.json` (bytes; SHA-256) | Saved edited FCStd (bytes; SHA-256) |
| --- | --- | --- |
| `20260720T165250Z` | 435,289; `3303d2a0999e884a9457562aeec3a990df62b33d41b48435ed8295882ed2c46a` | 1,324,155; `7a555cacb39d49264f5df9ec251626da7af4bbc5a91cf1595ac644b9b1d12c89` |
| `20260720T165336Z` | 435,296; `c9d51cb1f063a0d8434e799c9a95af1ed7f2120272be4e0126da2751dbba7dbd` | 1,324,141; `fbfd3bffac27b94dc8c32af2738b01557549774a3e36ad806d8a961a36c88f89` |
| `20260720T165421Z` | 435,287; `7f1b6c5da9f429bc01e51e9e300261bffd6acde1956196703820111cef79b8db` | 1,324,134; `0b4a56594df03cacbeab38b567b30a82cc85bd4c7b951b7c467f39be20536fca` |

Each run also retained the automatic 636,344-byte FCBak, FreeCAD and isolated-
launcher logs, and top-view, manager and complete-window PNG evidence. The
manager image is byte-identical across all three runs; rendering-dependent
top/window PNG hashes differ. Binary FCStd hashes differ because of volatile
archive data, while every created, edited, undo, redo, abort and reopen
semantic payload is identical.

## Provenance and coverage boundary

This recipe records B14 legacy behaviour as a local comparison oracle. Its
captured constants, catalogue values and generated shapes are not admitted as
project-cleared canonical production inputs, do not alter the current
`unknown` B14/B15 output project status, and do not change the accepted
licensing boundary. No Templot archive material was copied or translated and
no product source or production definition changed in this tranche.

The tranche closes a dedicated deterministic fixture for centreline-anchored
creation of one left-hand/facing REA C10 on the curved Main Track, one handed
edit, exact Undo/Redo and persistence, occupied-chainage rejection and an
in-transaction edit abort. It also freezes the resulting document and
production-catalogue semantics.

It does not cover trailing orientation through the GUI, a straight host, the
second track or wider chainages, alternative gauge/flangeway/output choices,
turnout removal/reversal, turnout conversion or host integration, standalone
automatic-timbering/chair stages, target-file export, legacy-document variants,
future deferred exact reconstruction, or a complete edit-through-export
performance profile. Those remain explicit Phase 1 gaps. Phase 1 remains
current.
