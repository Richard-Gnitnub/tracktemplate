# B14 Connected Straight and Stationing Workflow Series

Status: controlled three-run Phase 1 characterisation of B14's bounded
curve-entrance/curve-exit straight workflow and travel-order stationing. This
is a correctness oracle and deterministic fixture recipe. It is not an
optimisation comparison, an accepted latency budget, or coverage of a physical
station/platform workflow.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260720T113905Z`, `20260720T113934Z`, `20260720T114004Z` |
| Run intervals | 11:39:05–11:39:25, 11:39:34–11:39:55, and 11:40:04–11:40:25 UTC on 2026-07-20 |
| Recipe | `phase1-b14-straight-station-lifecycle-v1` |
| Repository base | `aa30bfe23b0ff2eac5e92f004b34a95b19faba48`; the oracle and this report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every included run |
| Initial complete-document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| Created `600/600 mm` workflow SHA-256 | `f5bf185baf2c61fbdf79c483b96ccf53e3a6206320e50087568e457022958a6c` |
| Edited `750/450 mm` workflow SHA-256 | `430d5f134e20789ee22c7f5549b64611a067646f1d24e038d4fbbc473d6b7666` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent, with recipe-owned keys restored after every run |
| Result | All assertions passed; source fixture unchanged; copied document closed; no unexpected dialog or surviving bridge process |

The workflow hash covers the analytical route/station model, raw persisted
straight JSON with unmasked manager identities, every generated document
object and exact-shape summary, group membership, typed persisted values and
the ordered production-record catalogue. FreeCAD archive hashes remain
non-semantic because FCStd serialisation contains volatile data.

The wrapper's default 641,206-byte fixture was also checked separately in run
`20260720T113832Z`. Its different binary SHA-256
`59d06cf57d65d9560dd53915fce2bef19130c534d214f92c9699066060dc4357`
produced the same two frozen workflow hashes.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-straight-station \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process performs these actions in order:

1. Copy and open the fixed nine-object, two-track curve document; require an
   empty FreeCAD history and validate the existing plain-line oracle.
2. Drive B14's real `CurveInputDialog`, invoke **Replace with curve entrance +
   exit pair**, set deterministic manager identities, retain the inherited two
   curve tracks, and generate two `600 mm` routes through the normal Replace
   action.
3. Capture the actual `build_straight_routes` result without replacing its
   implementation; validate track order, joins, headings, station samples,
   exact document shapes, persistence and production catalogue.
4. Apply all three B14 `Undo` entries and require exact recovery of the initial
   document, then apply all three `Redo` entries and require exact recovery of
   the created pair.
5. Reopen the real dialog from document state, change only the entrance length
   to `750 mm` and exit length to `450 mm`, and run the normal Replace action.
6. Require both stable route identities, exact changed station totals and
   unchanged curve template/centreline geometry. Undo and redo that complete
   three-entry edit and compare the full semantic payloads at both ends.
7. Save, close and reopen the edited copied document; require exact raw manager
   IDs, exact workflow semantics, 23 objects and empty reopened history.
8. Restore the isolated preference keys, confirm the source fixture hash and
   stop only the isolated bridge process.

The observer wrapper calls B14's original straight builder exactly once per
accepted dialog action and immediately restores it. It does not substitute a
test implementation or change the macro.

## Analytical route and station contract

The stable identities are:

| Route | Manager ID | Route ID | Created length | Edited length |
| --- | --- | --- | ---: | ---: |
| Curve entrance | `phase1-curve-entrance` | `straight-phase1-curve-entrance` | 600 mm | 750 mm |
| Curve exit | `phase1-curve-exit` | `straight-phase1-curve-exit` | 600 mm | 450 mm |

Each route inherits Main Track then Track 2, including the exact curve
endpoint, tangent heading, template width and output selections. The
characterised station direction is:

| Route | Station 0 | Station L | Remote projection in curve travel direction |
| --- | --- | --- | ---: |
| Entrance | Remote end | Curve entrance join | `-L` |
| Exit | Curve exit join | Remote end | `+L` |

All four created alignments and all four edited alignments recorded
`0.0 mm` join-position error and `0.0 rad` tangent error after 12-place
normalisation. Each alignment has station breaks `[0, L]`; midpoint
interpolation resolves to `L/2`, and the endpoints resolve in the travel order
shown above.

The fixed curve joins are not inferred from UI order. They are captured by
track identity:

| Track | Entrance point (mm) / heading | Exit point (mm) / heading |
| --- | --- | --- |
| Main Track | `(0, 0)` / `0 rad` | `(922.295255312839, 922.295255312839)` / `1.570796326795 rad` |
| Track 2 | `(0, -50.000000001876)` / `0 rad` | `(972.295255314715, 922.295255312839)` / `1.570796326795 rad` |

The raw `StraightTrackConfigurationsJSON` on both Settings and Template retains
the two exact manager IDs, order, connection modes, lengths and inherited
two-track count after save/reopen. The ordinary plain-line normaliser still
masks its unrelated generated platform-manager value; the dedicated raw
straight contract prevents that compatibility rule from hiding a straight
identity regression.

## FreeCAD and production contract

The resulting document has 23 objects. The connected pair adds:

- two generated subgroups, `Straight_Track_Templates` and `Straight_Tracks`;
- four valid exact `StraightTrackTemplate` objects and four valid
  `StraightTrackCentreline` objects, keyed by route ID and one-based inherited
  track number; and
- four additional hidden production-source objects, giving five total when
  the inherited curve profile source is included.

The ordered catalogue contains 12 records: the unchanged four curve records,
then four entrance-route and four exit-route records. Each straight route has
one compound 2D cutting profile, one compound 3D solid, and two centreline
engraving records. Both compound records bind through hidden production
sources because the retained document objects are per-track templates; the
centreline records bind directly. Every record ID resolves back to a generated
object.

Changing only the two lengths preserves the complete curve Template and both
curve Centreline semantic records, including exact-shape topology, measures
and bounds. It changes the straight route shapes, station totals, persisted
lengths and their derived report data as expected.

## Edit history and accepted successor contract

Creation and length editing each add the same three B14 undo entries, newest
first:

1. `Update Version 10.2A8A7B14 material report`;
2. `Update Version 10.2A8A7B14 production schedule`; and
3. `Generate Version 10.2A8A7B14 curve and straight production templates`.

Three Undo operations restore the exact preceding complete state and three
Redo operations restore the exact accepted result. This confirms straight
editing participates in the already-characterised B14 three-transaction
legacy defect. It does not change the accepted successor requirement: one
accepted user command must become one atomic application/undo unit, including
derived schedule and report updates.

## Timing observations — not accepted budgets

The action measurements end when B14's modal Generate workflow returns and
exclude the subsequent deep semantic walk. The history-cycle and save/reopen
figures include deep validation, so they are diagnostic harness timings rather
than operator-visible action latency.

| Scenario | Run 1 | Run 2 | Run 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Create `600/600 mm` pair wall | 2528.073 ms | 2545.508 ms | 2511.454 ms | **2528.073 ms** |
| Create process CPU | 2643.770 ms | 2627.340 ms | 2663.010 ms | **2643.770 ms** |
| Create RSS end-minus-start | +197.156 MB | +190.699 MB | +197.359 MB | **+197.156 MB** |
| Edit to `750/450 mm` wall | 2078.244 ms | 2040.675 ms | 2106.817 ms | **2078.244 ms** |
| Edit process CPU | 2146.879 ms | 2152.074 ms | 2147.264 ms | **2147.264 ms** |
| Edit RSS end-minus-start | +50.336 MB | +64.246 MB | +63.523 MB | **+63.523 MB** |
| Creation Undo+Redo plus deep validation | 2370.803 ms | 2396.131 ms | 2401.410 ms | **2396.131 ms** |
| Edit Undo+Redo plus deep validation | 2365.863 ms | 2373.599 ms | 2388.174 ms | **2373.599 ms** |
| Save/close/reopen plus deep validation | 1873.900 ms | 1988.611 ms | 1922.845 ms | **1922.845 ms** |
| Complete orchestrated recipe | 16.736 s | 17.283 s | 17.127 s | **17.127 s** |

No current timing is accepted as a human-use budget. These values describe
legacy exact-shape replacement. The future lightweight edit path and deferred
Validate/Export path must be measured separately under the performance SOP.

## Exact recipe-source state

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/straight_station_recipe.py` | `df6ba6590fcc800240c2486e502bb2f0559196540aa54ea532fcff97dc33e183` |
| `tools/freecad_bridge/probes/b14_straight_station_driver.py` | `66a06f73759a31f9e833bdebed13d5dd7b39f9d4efc3e04e1e0a9408dc5744d8` |
| `tools/freecad_bridge/run_b14_straight_station.py` | `670b26539840a118ffa173a5f7adcbfaae016502c770b7eaa3c1723c1561da72` |
| `tools/freecad_bridge/run-b14-straight-station` | `1f33c88f2fe403ff949ad3c39cd82c3402d2d3a2ff23ce1f201daa3194c15c1c` |
| `tests/validate_phase1_straight_station.py` | `3e9b77f3574120f100e5dd49b0a842a111c171c6e5b8a0e825ace5c81033f1fa` |
| `tests/validate_freecad_bridge.py` | `5a049eafa01a2a74158dc5e45ea97003ed2c3d11a755458559d005e748251449` |

## Ignored raw evidence

Raw artifacts include local absolute paths and generated FreeCAD data, so they
remain ignored under
`benchmark-output/freecad-bridge/straight-station-runs/`.

| Run | `run.json` (bytes; SHA-256) | Saved edited FCStd (bytes; SHA-256) |
| --- | --- | --- |
| `20260720T113905Z` | 463,470; `9d443d57367a2e0168db826a975831388931303772a9bd363fe790cefdafc56e` | 657,881; `78e76b6cdbdebfb15e6d3abbf0b772bea1270366797c0b06e499397662a16824` |
| `20260720T113934Z` | 463,471; `f1ed6b95899a7769d14c5aaf1aeb8c8012a722ffc8fc5f6dc7cd2dce6ded9c2d` | 657,888; `f9b6fea99d76b80032d49759b6210c8408374f7c717b55d3d7891159d9523af3` |
| `20260720T114004Z` | 463,472; `9d6b9f767dba0ecd341301257cc56388a608f7c8d925214eeed868f9b6eaef47` | 657,895; `7077998e5b25f3fb12cefcd92dc6068c7a85b876baf247957c93285bcdd51c00` |

Each run also retained a 636,344-byte automatic FCBak with the unchanged
source-fixture SHA-256.

Binary FCStd hashes differ because of volatile archive data. Their created,
edited, undo, redo and reopen semantic payloads are identical.

## Coverage boundary

This tranche closes the dedicated connected-straight creation, stationing,
length-edit, full-history recovery, raw-identity persistence and production-
catalogue gap for the fixed two-track curve. The fast oracle additionally
characterises one independent reverse/right-side two-track datum and proves
exact B14/B15 calculation parity.

It does not yet drive the independent-datum GUI path, a physical station or
platform, formation/section/assembly options, straight target-file exports,
straight-specific rejection/rollback cases, future deferred exact
reconstruction, or wider curve/track configurations. Those remain explicit
Phase 1 gaps. Phase 1 remains current.
