# B14 Plain-Line Edit Lifecycle Series

Status: controlled three-run Phase 1 characterisation of B14's fixed
plain-line edit lifecycle. It extends the earlier handedness-edit oracle with
FreeCAD undo/redo, explicit change-back, transaction-stack and history-reset
evidence. It records a legacy atomicity defect; it is not an optimisation
comparison, an accepted interaction budget, or a requirement to reproduce the
defect in the modular application.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260719T213634Z`, `20260719T213727Z`, `20260719T213818Z` |
| Run intervals | 21:36:34–21:37:10, 21:37:27–21:38:04, and 21:38:18–21:38:55 UTC on 2026-07-19 |
| Recipe | `phase1-b14-ordinary-track-edit-lifecycle-v2`; the `ordinary` token is a frozen legacy evidence identifier |
| Repository base | `1dec9bb7164b0bf60c40caa1213563d752a46afc`; the lifecycle extension and this report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every run |
| Initial deep semantic SHA-256 | `b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656` |
| Initial complete-document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| Right-hand complete-document semantic SHA-256 | `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent, with recipe-owned keys restored after every run |
| Result | All assertions passed; source fixture unchanged; copied document closed; no unexpected dialog or surviving bridge process |

The complete-document lifecycle hash includes the complete nine-object
semantic snapshot used to compare intermediate history states. The earlier
deep hash remains the fixed base-oracle identifier; the two hashes cover
different normalised payloads and are not contradictory.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process performs these actions in order:

1. Open the copied nine-object left-hand fixture, require enabled but empty
   FreeCAD undo/redo history, and capture the complete initial semantic state.
2. Drive B14's real curve dialog through the existing `+90°` to `-90°`
   replacement and validate the complete mirrored right-hand document.
3. Inspect the transaction stack, apply three `Undo` operations and validate
   every intermediate state, then apply three `Redo` operations and recover
   the exact right-hand state.
4. Drive the real dialog through an explicit `-90°` to `+90°` change-back and
   require exact equality with the initial complete-document state.
5. Undo the three change-back entries, validating both partial-report states,
   and recover the exact right-hand state again.
6. Save, close and reopen the right-hand copy, require exact semantic equality
   and require FreeCAD's document history to reopen empty.
7. Re-run the established zero-angle rejection and injected post-removal
   transaction-abort scenarios, restore the isolated preference store, close
   the copied document and stop only the bridge process.

The recipe validates last-used dialog inputs after every history action.
Undo/redo changes document state only; it does not rewind B14's preference
store because those values are written outside the document transaction.

## Behavioural result and legacy defect

One successful curve replacement records three independent FreeCAD undo
transactions, newest first:

| Undo order | FreeCAD transaction | State exposed after Undo |
| ---: | --- | --- |
| 1 | `Update Version 10.2A8A7B14 material report` | Eight objects; material report absent |
| 2 | `Update Version 10.2A8A7B14 production schedule` | Seven objects; schedule and material report absent |
| 3 | `Generate Version 10.2A8A7B14 curve and straight production templates` | Complete preceding nine-object geometry/report state |

Redo recreates geometry, then schedule, then material report. The same three
entries are added by explicit change-back, so the history count progresses
from `0/0` undo/redo at open, to `3/0` after replacement, to `6/0` after
change-back. Save/close/reopen returns it to `0/0` while preserving the exact
right-hand document.

All three runs produced the following identical state sequence:

| Step | Action | Objects | Undo/redo | Complete-document semantic SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 1 | Undo replacement material report | 8 | 2/1 | `7538610895a0a58ba97971b212057af7699f5c0be18ced26cd96c5b68b89819f` |
| 2 | Undo replacement production schedule | 7 | 1/2 | `18043d2d32790e2c526f00ac1819b5766f576fbe14ea2ac4b9992dcadffbeddc` |
| 3 | Undo replacement geometry | 9 | 0/3 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| 4 | Redo replacement geometry | 7 | 1/2 | `18043d2d32790e2c526f00ac1819b5766f576fbe14ea2ac4b9992dcadffbeddc` |
| 5 | Redo replacement production schedule | 8 | 2/1 | `7538610895a0a58ba97971b212057af7699f5c0be18ced26cd96c5b68b89819f` |
| 6 | Redo replacement material report | 9 | 3/0 | `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4` |
| 7 | Undo change-back material report | 8 | 5/1 | `1712f73f78f8ef6025f6602063d11796eeba3fe5ac1422b6a1d4b9e749310124` |
| 8 | Undo change-back production schedule | 7 | 4/2 | `5a21cc0044687b22ecbdd957585c60a9870f8b2c125f7c936aec0a5cf7a85bbc` |
| 9 | Undo change-back geometry | 9 | 3/3 | `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4` |

Explicit change-back itself is correct: its complete semantic SHA-256 is the
exact initial left-hand value
`ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13`.
The defect is command atomicity. One user command temporarily exposes
incomplete seven- and eight-object documents during normal Undo/Redo.

The accepted target contract is therefore stricter than B14 parity: one
accepted application command must be one atomic undo unit, including its
derived production schedule and material report updates. No migrated command
may expose those partial states. B14's three-entry stack remains diagnostic
evidence, not a regression oracle for the modular implementation.

## Timing observations — not accepted budgets

The replacement is the first measured dialog action in each fresh process.
Change-back, history actions, persistence and negative paths occur later in
that same process and are correctness observations, not equivalent cold runs.

| Scenario | Run 1 | Run 2 | Run 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Left-to-right replacement wall time | 2799.795 ms | 2708.003 ms | 2783.694 ms | **2783.694 ms** |
| Replacement process CPU time | 2881.545 ms | 2865.174 ms | 2914.555 ms | **2881.545 ms** |
| Replacement RSS end-minus-start | +184.547 MB | +236.781 MB | +241.691 MB | **+236.781 MB** |
| Explicit change-back wall time | 2044.726 ms | 2046.484 ms | 2031.829 ms | **2044.726 ms** |
| Change-back process CPU time | 2137.060 ms | 2106.367 ms | 2068.132 ms | **2106.367 ms** |
| Change-back RSS end-minus-start | +52.465 MB | +57.531 MB | +56.781 MB | **+56.781 MB** |
| Save/close/reopen wall time | 923.206 ms | 937.700 ms | 892.854 ms | **923.206 ms** |
| Zero-angle rejection wall time | 318.666 ms | 283.431 ms | 264.739 ms | **283.431 ms** |
| Injected transaction-abort wall time | 489.295 ms | 500.808 ms | 533.549 ms | **500.808 ms** |

History timing deliberately separates the actual FreeCAD action, the action
plus explicit recompute, and the expensive deep semantic oracle. The latter
walks and normalises the exact shapes and must not be reported as user-visible
Undo/Redo cost. The first two are synchronous document-side measurements and
do not include a separately observed viewport repaint, so they are not a
complete GUI-latency budget either.

| History action | Actual call median | Call plus recompute median | With deep validation median |
| --- | ---: | ---: | ---: |
| Undo replacement material report | 0.373 ms | 4.754 ms | 1193.614 ms |
| Undo replacement production schedule | 0.291 ms | 0.518 ms | 1181.993 ms |
| Undo replacement geometry | 1.129 ms | 1.364 ms | 1201.359 ms |
| Redo replacement geometry | 0.636 ms | 0.855 ms | 1173.999 ms |
| Redo replacement production schedule | 0.248 ms | 0.469 ms | 1170.479 ms |
| Redo replacement material report | 0.292 ms | 0.505 ms | 1188.887 ms |
| Undo change-back material report | 0.395 ms | 0.805 ms | 1183.014 ms |
| Undo change-back production schedule | 0.346 ms | 0.561 ms | 1183.958 ms |
| Undo change-back geometry | 1.090 ms | 1.329 ms | 1189.741 ms |

The median three-step totals were `1.806 ms` for the raw replacement Undo
calls (`6.724 ms` including explicit recomputes), `1.168 ms` for replacement
Redo (`1.824 ms` including recomputes), and `1.849 ms` for undoing change-back
(`2.722 ms` including recomputes). These small synchronous calls do not erase
the correctness defect: a fast incomplete document is still invalid.

## Exact recipe-source state

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/ordinary_track_recipe.py` | `a0c6dd7fb0eb74db57d902f2a9e7d6f690993ac18470065df78b36a2f64bc665` |
| `tools/freecad_bridge/ordinary_track_edit_recipe.py` | `2ecc38ef20b5757218c60b453ce5b00d4d5581c2837b2e46f082fced6bc9243c` |
| `tools/freecad_bridge/run_b14_ordinary_edit.py` | `3ce98345f97df1b9d3d3407d36e8faf9490924ceb5810b234645b08b153712ee` |
| `tools/freecad_bridge/probes/b14_ordinary_edit_driver.py` | `ff5984da47670e3823ed71cdd29b6f2e2155882f55083e26a1c46dafd42bab66` |
| `tools/freecad_bridge/run-b14-ordinary-edit` | `40b2cca96ecee04d0fc7d388ce73e7f1a40b5e77e39c14069efe9230de6e6a68` |
| `tests/validate_phase1_ordinary_edit.py` | `f32aec511fa7cd5147c2033bb713888430c5027e347a40fcae035de23c33a3ed` |

## Ignored raw evidence

Raw artifacts include local absolute paths and generated FreeCAD data, so they
remain under ignored
`benchmark-output/freecad-bridge/ordinary-edit-runs/`.

| Run | `run.json` (bytes; SHA-256) | Saved right-hand FCStd (bytes; SHA-256) |
| --- | --- | --- |
| `20260719T213634Z` | 220,020; `433707b236cad4e54cebc7eb64f30945a2536ff5ecafa09f8f4fcd02ad734405` | 638,802; `a49d292e4ce8b114978d2b913ce21c70885cf41c16e826215065888720f2ccb4` |
| `20260719T213727Z` | 220,020; `13039c8397c06bf218d5ab941ac82060a72d237deb7c8023123d9c23474fd8cb` | 638,802; `080a13f3c35fb155e18375a1a50bb06c782a9004ad9830e1c6d0ef3e4f09a5bf` |
| `20260719T213818Z` | 220,005; `101a5151472e52a10725e1b1699f0669ee7829510b4878fba29ccac06308d056` | 638,770; `5306fe1014525f13aa7ca5bad4bd5d247642e5353822d4a4dcb31dae2cdd6911` |

Each run also retained a 636,344-byte automatic FCBak with the unchanged
source-fixture SHA-256. The saved FCStd binary hashes differ because FreeCAD's
archive serialisation contains volatile data; their normalised railway
semantics are identical.

## Coverage boundary

This tranche closes undo/redo and explicit change-back characterisation for
the fixed B14 plain-line curve/two-track document. It also bounds the
three-transaction legacy defect and establishes the atomic successor
requirement. Wider curve/easement boundaries, station/straight workflows,
standalone turnout editing, future explicit Validate/deferred reconstruction,
other export scopes and a lightweight-editing implementation remain open.
Phase 1 remains current.
