# B14 Ordinary-Track Edit and Rollback Series

Status: controlled three-run Phase 1 characterisation of B14's ordinary-track
replacement path. It establishes a left-to-right edit oracle, save/reopen
persistence, invalid-input behaviour, and actual FreeCAD transaction abort.
It is not an optimisation comparison, an accepted human-use budget, or a
complete curve-to-export product benchmark.

## Identification and comparability

| Item | Value |
| --- | --- |
| Included runs | `20260719T192252Z`, `20260719T192323Z`, `20260719T192401Z` |
| Run intervals | 19:22:52–19:23:12, 19:23:23–19:23:43, and 19:24:01–19:24:21 UTC on 2026-07-19 |
| Repository base | `0794ab4d50099c072cf626aee8adf335eceeae68`; the edit recipe and this report were pending review/commit |
| Product source state | Neither macro has a working-tree change |
| Macro | `AdvancedTurnout.FCMacro`, Version `10.2A8A7B14` |
| Macro SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| FreeCAD | 1.1.1 revision 44874, system Flatpak `org.freecad.FreeCAD` |
| Host | Linux Mint 22.3 x86_64; Linux 6.17.0-40-generic; AMD Ryzen 5 5500, 6 cores / 12 threads; 31 GiB usable RAM |
| Source fixture | Independently regenerated B14 default left-hand curve/two-track document, 636,344 bytes |
| Source fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before and after every run |
| Initial deep semantic SHA-256 | `b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656` |
| Right-hand semantic SHA-256 | `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4` |
| Process/document state | Fresh isolated FreeCAD process, empty session, source fixture copied for every run |
| Cache qualification | Operating-system file cache uncontrolled; isolated preference profile persistent, with recipe-owned keys restored after every run |
| Result | All assertions passed; nine objects before and after each action; no unexpected dialog |

The current fixture is the exact ordinary curve/two-track result already
covered by the read-only Phase 1 document oracle. The bridge loaded B14 without
executing its final launch call and operated only on a timestamped copy. It
never saved or opened the source fixture for writing.

## Reproducible operator path

Run the complete sequence with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Each isolated process performs these actions in order:

1. Assert an empty document session, load B14, open the copied nine-object
   left-hand fixture, and validate its frozen deep oracle.
2. Open B14's real curve dialog, force document-derived starting inputs, retain
   the existing default two-track settings, select **Replace all existing
   generated templates**, change the total angle from `+90.000°` to
   `-90.000°`, accept the known replacement confirmation, and let the complete
   `run_macro()` path finish.
3. Validate the full right-hand semantic snapshot, explicitly recompute, save
   the copy, close it, reopen it, and validate the same snapshot again.
4. Reopen the real dialog, submit a zero turn angle, accept the current
   pre-validation replacement question, require the exact error
   `The total turn angle cannot be zero.`, and prove the document is unchanged.
5. Reopen the real dialog at `-80.000°` and inject one deterministic exception
   at the first `tag_generated_object` call. This occurs inside B14's open
   replacement transaction after `remove_all_generated_outputs` has run.
   Require the exact error, require one injection call, and prove
   `abortTransaction()` restored the complete document.
6. Close and reopen the last saved document once more, revalidate the frozen
   right-hand hash, restore the isolated bridge's three affected preference
   keys, close all documents, and stop only that bridge process.

The dialog displays the match-spacing transition values at its three-decimal
precision (`559.410 mm`). B14's solver then persists the existing exact values
(`559.410254727028 mm`). The recipe protects both contracts rather than
mistaking the UI rounding for a persistence change.

## Behavioural results

All three runs produced the same right-hand semantic SHA-256 before save,
after the first save/reopen, and after both failure scenarios plus the final
reopen:

`4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4`.

The handedness comparison proved:

- the nine object names, types, generator identities, group membership,
  production-record identities and ordering are unchanged;
- the template, production source and both centreline objects retain identical
  shape types, validity, topology, measures, X bounds, Z bounds and Y length;
- each of those four shapes has exactly reflected Y bounds; and
- the only changed persisted fields on both settings and template are
  `CircularArcAngle`, `TotalTurnAngle`, `TransitionAngleEach`, and
  `TurnDirection`.

The template therefore remains a two-solid compound with 2,104 faces and
6,300 edges, the hidden 2D production source retains 2,100 edges, and the Main
Track and Track 2 centrelines retain 515 and 533 edges respectively. The
right-hand bounds are a geometric mirror, not merely a changed direction
label.

| Negative path | Before semantic SHA-256 | After semantic SHA-256 | Object delta | Result |
| --- | --- | --- | ---: | --- |
| Zero-angle validation failure | `4c8bf8d…69d4` | `4c8bf8d…69d4` | 0 | Exact diagnostic; no document mutation |
| Injected post-removal transaction failure | `4c8bf8d…69d4` | `4c8bf8d…69d4` | 0 | One injected call; transaction abort restored all state |

B14 intentionally records accepted last-used dialog inputs before either
validation or transaction opening. The zero-angle and injected-failure paths
therefore update preferences even though their document mutations fail. That
is a distinct current behaviour, not a document-rollback defect. The isolated
recipe validates each remembered payload and restores the pre-run preference
values before it exits.

## Timing observations — not accepted budgets

The successful replacement is the first measured action in each fresh
process. Its boundary starts immediately before `run_macro()` and includes
real dialog construction, configuration, the replacement confirmation,
calculation, exact `Part` shape construction, document replacement, metadata,
recomputes, reports, and closure of the success dialog. It excludes process
launch, B14 loading, fixture opening, the pre-action semantic snapshot, the
post-action oracle, and subsequent save/reopen.

| Successful replacement metric | Run 1 | Run 2 | Run 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall time | 2769.362 ms | 2781.596 ms | 2836.972 ms | **2781.596 ms** | 67.610 ms |
| Process CPU time | 3048.185 ms | 2903.295 ms | 3051.879 ms | **3048.185 ms** | 148.584 ms |
| RSS end-minus-start | +182.641 MB | +234.840 MB | +299.961 MB | **+234.840 MB** | 117.320 MB |
| Object delta | 0 | 0 | 0 | **0** | 0 |

The 2.782-second median is an observed B14 exact-shape replacement cost, not a
human-use target. The large and variable RSS delta reinforces the architectural
need to separate lightweight editing from production geometry, but an
end-minus-start allocator snapshot cannot attribute that memory to a specific
function or report a sampled peak.

The separately measured persistence boundary begins after successful oracle
validation and includes explicit recompute, save, close and reopen. It excludes
the semantic validation performed after reopening.

| Persistence metric | Run 1 | Run 2 | Run 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete persistence wall time | 725.049 ms | 758.005 ms | 763.578 ms | **758.005 ms** | 38.529 ms |
| Explicit recompute | 4.115 ms | 4.167 ms | 4.134 ms | **4.134 ms** | 0.052 ms |
| Save | 138.141 ms | 134.795 ms | 135.732 ms | **135.732 ms** | 3.346 ms |
| Close and reopen | 582.624 ms | 618.887 ms | 623.552 ms | **618.887 ms** | 40.929 ms |
| Process CPU time | 1242.673 ms | 1284.560 ms | 1226.967 ms | **1242.673 ms** | 57.593 ms |
| RSS end-minus-start | +46.309 MB | -57.336 MB | +56.441 MB | **+46.309 MB** | 113.777 MB |

The negative-action measurements occur later in the same process, after the
right-hand document has been saved and reopened. They are correctness
observations and must not be compared with the fresh-process successful action
as equivalent cold work.

| Later same-process action | Run 1 | Run 2 | Run 3 | Median | Range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zero-angle rejection wall time | 252.718 ms | 285.672 ms | 260.761 ms | **260.761 ms** | 32.954 ms |
| Injected transaction-abort wall time | 438.169 ms | 433.144 ms | 513.626 ms | **438.169 ms** | 80.482 ms |

The injected rollback uses a different valid angle and a deliberate test hook;
it characterises recovery semantics, not normal editing cost or a production
failure rate.

## Exact recipe-source state

| File | SHA-256 |
| --- | --- |
| `tools/freecad_bridge/ordinary_track_recipe.py` | `382c4b324ebcd3edab1f2b431276ba46e5fdaa4e68d7b37f53af5f25e5df8b58` |
| `tools/freecad_bridge/ordinary_track_edit_recipe.py` | `15b196c5be36c52953a3df198922ccf72feb063e7c819ec4ba2ed28dc9dce7f1` |
| `tools/freecad_bridge/run_b14_ordinary_edit.py` | `04647df27cd62f0738dfa7f8a619c41da826c6b6f2c096a91a20012f2fe773bd` |
| `tools/freecad_bridge/probes/b14_ordinary_edit_driver.py` | `60d3dc47cf00db3316f88301081fc9a1a13d2f8ecc35cde05a073b05f03532e8` |
| `tools/freecad_bridge/run-b14-ordinary-edit` | `40b2cca96ecee04d0fc7d388ce73e7f1a40b5e77e39c14069efe9230de6e6a68` |
| `tests/validate_phase1_ordinary_edit.py` | `74d9150ad6e10b359d29278496c4ea691259f5e1ac29444ca3128e2eb31515b7` |

## Ignored raw evidence

The raw artifacts include local absolute paths and generated FreeCAD data, so
they remain under ignored
`benchmark-output/freecad-bridge/ordinary-edit-runs/`.

| Run | `run.json` (bytes; SHA-256) | Saved right-hand FCStd (bytes; SHA-256) |
| --- | --- | --- |
| `20260719T192252Z` | 131,572; `5c7742e8528c2abdc969cb3e308dc45c1dd3e15ee92bad8540493be13164a86a` | 638,706; `405562cb9ea81109e5bf569465f56bb15a94358112133ce155bf4eea5afee601` |
| `20260719T192323Z` | 131,576; `d4839412f78d2c5dae709ef87f30ef39012bbb3636da0e19cb4885b3c0ab154e` | 638,715; `f49a0a80fd2bba99b55578d4b43dc441fd55e81eb4d4377369bb2b5bbeb2d89c` |
| `20260719T192401Z` | 131,571; `fbd40f5a1bd0062f8f82eabc5cbe34fe57a7b2aaaff918ffab605c63f45e18c6` | 638,701; `b4d2726fc4539c9a9db9be2c5292eb56d60eb67647add92edcdfb5dee5a56bf4` |

Each run also retained a 636,344-byte automatic FCBak with the unchanged source
fixture SHA-256. The saved FCStd binary hashes differ because FreeCAD's archive
serialisation contains volatile data; their normalised railway semantics are
identical and frozen by the right-hand oracle.

## Coverage boundary

This tranche closes the fixed B14 ordinary-track left-to-right replacement,
save/reopen, zero-angle rejection, and document transaction-abort gaps. It does
not yet cover undo/redo, change-back, other curve/easement boundary values,
straight-route or station editing, Validate/Export, target-format artifacts,
or a lightweight-editing implementation. Phase 1 remains open.
