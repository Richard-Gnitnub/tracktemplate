# Phase 7 `main_circle_centre` evidence

Status: **Evidence for the bounded scope of D-P7-001.
No acceptance of product performance or a phase exit.**

## Bounded scope and method

The comparison baseline is protected main
`7efeb5d6ca9d09ce4a696106ba31f7dff24973bb`, after the merge of PR #68.
It uses the accepted B16 route with three functions from `tracktemplate.api`.
The exact candidate adds `main_circle_centre` to `tracktemplate.api`.
The B16 Generate/Replace caller now uses this API.
The [API instructions](../contracts/phase7-main-circle-centre.md)
define the change and source files to preserve.

Both routes use the qualified host profile
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
Each sample starts a new isolated FreeCAD process with a copy of the same fixture.
The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The isolated processes start with the same bytes in `user.cfg` and `system.cfg`.
The tests do not control data that the operating system keeps after a previous operation read the files.

The `run_phase3_transition_workflow.py` tool supplies the two workflows.
The comparison baseline and exact candidate both use `--route modular`.
Each workflow has three samples for each route.

The first pair starts with the comparison baseline. The second pair starts with the exact candidate.
The third pair starts with the comparison baseline.
Different samples use `--route legacy` to compare results only.
The Phase 3 tool that measures each operation and the comparison rule have no change.

The tests started on 2026-09-05 and completed on 2026-09-08 after an interruption.
The JSON data keep the sequence and dates of all samples.
The JSON key `state` identifies each sample as `baseline`, `candidate` or `legacy`.

The measured operation includes steps that get input, calculate results, make shapes, replace objects, use metadata and do `recompute()`.
It also includes the human interface that shows the results.
The measured time does not include these operations:

- Start FreeCAD and read the source files.
- Open the fixture.
- Examine process state at intervals.
- Do the subsequent checks.
- Show the shapes in the human interface.

The subsequent operation in each process calculates a result again in the same process.
It does not use a previous result when the input values stay the same.
Thus, warm reuse for `main_circle_centre` is not applicable.

## Calculate results again

CPython 3.12.3 measured six samples for each API.
The sample sequence uses one API, then the other API, again and again.
Each sample calculates 1,800 results: 50 times for each of 36 input pairs with values of zero or more.
Each calculated result must be equal to the result from the other API.
The comparison baseline uses `main_circle_centre` from B15 source.
Both APIs use the same `clothoid_entry_displacement` from `tracktemplate.api`.

These isolated operations do not measure the complete FreeCAD workflow.

| Measured quantity | `baseline` median (range), ms | `candidate` median (range), ms |
| --- | ---: | ---: |
| Wall time | 50.076 (49.354–71.242) | 53.260 (49.555–76.238) |
| Process CPU | 49.939 (49.272–71.121) | 53.103 (49.466–75.768) |

The `candidate` medians are higher. The ranges include common values.
The median for wall time increases by 3.184 ms (6.358%).
The median for CPU time increases by 3.164 ms (6.335%).

These results do not show that product performance is better.
They define no acceptance limits for product performance. The JSON data keep all individual values.

## FreeCAD workflow results

All 14 samples completed. Each workflow has three `baseline` samples and three `candidate` samples.
Each workflow also has one `legacy` sample to compare results.
For every included sample, `tools/freecad_bridge/run-isolated` gave process exit status 0.
Each sample also has a completed workflow record.

The source files, fixture and the initial `user.cfg` and `system.cfg` data did not change.
Each sample records `cleanup.remaining: []`. After each sample, `FreeCAD.listDocuments()` gives an empty result.
The isolated FreeCAD processes stopped.

The tool compared all 14 samples and found equal results.
It still does not compare values for the same five JSON keys that can change between samples.
In these two workflows, the tool examines railway state, identities, sequence, metadata, `Undo`, `Redo` and shapes.
It also examines recovery after an error and the result when FreeCAD opens the file again.
Different tests compared the API results and actual caller results, with PASS results.
The subsequent steps that make shapes did not change.

These checks give evidence for equal results in the bounded scope.
They do not prove that all data for complete FreeCAD shapes or output bytes are equal.

### Time for each operation

Values are milliseconds. Change is the `candidate` median minus the `baseline`
median, then this difference as a percentage of the `baseline` median.

| Operation | Measured quantity | `baseline` median (range) | `candidate` median (range) | Change |
| --- | --- | ---: | ---: | ---: |
| Replace the left curve with the right curve | Wall | 2939.951 (2758.815–14065.311) | 2678.564 (2643.950–14020.262) | −261.386 (−8.891%) |
| Replace the left curve with the right curve | CPU | 2967.628 (2774.901–2976.166) | 2823.957 (2767.274–2865.805) | −143.672 (−4.841%) |
| Replace the right curve with the left curve | Wall | 2141.913 (2067.493–13154.295) | 2081.312 (2041.612–13156.413) | −60.600 (−2.829%) |
| Replace the right curve with the left curve | CPU | 2134.989 (2107.535–2165.635) | 2109.142 (2044.065–2163.218) | −25.848 (−1.211%) |
| Make the connected pair | Wall | 2621.606 (2611.159–14120.378) | 2678.811 (2639.681–13466.698) | +57.204 (+2.182%) |
| Make the connected pair | CPU | 2668.288 (2608.942–2686.561) | 2710.208 (2478.251–2769.899) | +41.920 (+1.571%) |
| Change the lengths of the connected pair | Wall | 2259.494 (2148.936–13174.891) | 2241.189 (2152.901–13182.996) | −18.306 (−0.810%) |
| Change the lengths of the connected pair | CPU | 2267.106 (2228.393–2324.198) | 2221.426 (2172.221–2328.661) | −45.679 (−2.015%) |

The approximate wall times for the third pair are 13–14 seconds in both routes.
The approximate wall times for the first two pairs are 2–3 seconds.
The approximate CPU times stay at 2–3 seconds.
The cause of this difference between dates is unknown.
All results stay in the evidence. These different times are a limitation on evidence for effects of the exact candidate.

### Memory and objects

RSS changes use MiB. The tool uses the JSON key
`rss_delta_mb` for this unit.

| Operation | `baseline` RSS change median (range) | `candidate` RSS change median (range) | Median change |
| --- | ---: | ---: | ---: |
| Replace the left curve with the right curve | 213.398 (213.313–217.727) | 217.375 (210.996–275.398) | +3.977 (+1.863%) |
| Replace the right curve with the left curve | 50.496 (45.371–51.770) | 51.570 (50.820–57.836) | +1.074 (+2.127%) |
| Make the connected pair | 177.180 (162.004–177.277) | 166.348 (165.898–173.508) | −10.832 (−6.114%) |
| Change the lengths of the connected pair | 63.402 (55.910–63.551) | 62.660 (56.859–64.094) | −0.742 (−1.171%) |

The `candidate` Replace maximum is 275.398 MiB. The `baseline` maximum is
217.727 MiB. The evidence keeps this higher `candidate` value.
Each operation that makes the connected pair adds 14 objects.
Each other measured operation has no change in the number of objects in either route.

All recorded time and RSS ranges include common values.
This does not prove that product performance is equal or that it did not become worse.

The regression tests are complete for this selected migration.
They give no acceptance of product performance and do not show that it is better.
The independent review examined source and evidence.
It found no evidence of a product performance problem that the exact candidate caused and that prevents publication.
The time and memory limitations stay.

## Limitations and evidence files

Python could not find `click` during the first command invocation.
It stopped before a workflow started. The next invocation used the approved path for `click`.

Three initial `candidate` samples used different data for `user.cfg` and `system.cfg`.
FreeCAD supplied the initial data because these files were missing.
Their correct results stay in the evidence. This technical document does not include their time values.
The replacement samples used the same data in these files as the comparison baseline.
The initial command output, FreeCAD files and copies of `user.cfg` and `system.cfg` stay available.

The workflow for `baseline` plain-line sample 3 completed.
The process exit status for `run-isolated` was missing after the interruption.
Its cleanup can stop with an error after the workflow completes.
Thus, a completed workflow did not prove process exit status 0.
Before replacement, the failure class for the missing process exit status was `fixture-or-harness-defect`.

One new sample with the same method gave the missing evidence.
The initial result stays as evidence for the correct operation of the product.
Its time is not in the tables above.

`summarise_gui.py` has no change.
A different temporary copy, `recovery-2026-09-08-summarise-gui.py`, selects only the replacement path for that sample.
It calculates the same quantities with the same method and uses the same rules to compare results.
No source, test, tool, comparison rule or tolerance changed during recovery.

These regression tests do not give the evidence that is necessary for D-P6-008.
This task changes no comparison rule or production output. It authorises no new release.
All conditions for the B14 and B15 routes and their removal still apply.

The local evidence files below are in `tmp/phase7-main-circle-centre/`.
`gui-regression-summary.json` records each sample path, hash, value and result when the tool compares the samples.
The source manifest identifies all seven source/test files, which have no change.

| Evidence file | SHA-256 |
| --- | --- |
| `gui-regression-summary.json` | `39f1a1f29d1617c1eaf4a96b240f2894a0afb6368f71761162b2a374b80cafab` |
| `repeated-centre-result.json` | `5258ecc2e206bc72c786ac5f127086b332d234992b2adc1abae5cbebbd1a366b` |
| `source-final.sha256` | `ce97bd8b2d58411e907154dac53ded7677c6514ea9697f0d44c71ecabe5687cd` |
| `recovery-2026-09-08-gui-completion-receipt.json` | `307958a7c1232b6047042b21cee96273394fa7532d167bfb22038d930bc41131` |
| `recovery-2026-09-08-quality-review.md` | `c8ffc3d60ca3d6102e2f10fb9b7c69123d66ae4f4b69f6c741a6ce8a40cc807a` |
