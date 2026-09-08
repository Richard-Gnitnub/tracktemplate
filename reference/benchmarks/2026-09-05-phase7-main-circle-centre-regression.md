# Phase 7 main circle centre regression evidence

Status: **Technical evidence for the bounded D-P7-001 product task.
No performance or phase-exit acceptance.**

## Scope and method

The comparison baseline is protected main
`7efeb5d6ca9d09ce4a696106ba31f7dff24973bb`, after opening PR #68.
It uses the accepted B16 modular path with three calculation bindings.
The candidate adds the modular centre and its existing Generate/Replace caller.
The [calculation and routing contract](../contracts/phase7-main-circle-centre.md)
defines the change and preserved references.

Both GUI paths use the qualified host profile
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
Each sample starts a new isolated FreeCAD process with a copy of the same fixture.
The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The isolated preferences have identical starting bytes.
The operating-system file cache is uncontrolled.

The retained `run_phase3_transition_workflow.py` driver supplies the two workflows.
Both comparison states use `--route modular`.
Three samples per state and workflow alternate baseline/candidate order by round.
Separate legacy runs supply comparison evidence only.
The frozen Phase 3 profiler and measurement rules are unchanged.

The series started on 2026-09-05 and finished on 2026-09-08 after an interruption.
Round 1 uses baseline before candidate. Round 2 reverses this order.
Round 3 uses baseline before candidate for each workflow.
The raw summary keeps the actual sequence and all dates.

The measured action includes the dialog, calculation, shape construction,
replacement, metadata, recomputes and result dialogs.
Launch, module loading, fixture opening, polling, later deep checks and viewport
repaint are outside that action. The later action in each process is a
same-process calculation, not warm-cache reuse.
No centre cache or signature-based reuse exists.
Warm centre-cache reuse is therefore inapplicable.

## Direct repeated calculation

CPython 3.12.3 measured six alternating samples per implementation.
Each sample makes 1,800 calls: 50 repetitions of 36 non-negative input pairs.
Every call checks exact result equality.
The baseline uses the inherited centre extracted from B15 source.
Both centres use the same unchanged modular endpoint function.
These isolated calculations do not measure the complete FreeCAD workflow.

| Metric | Baseline median (range), ms | Candidate median (range), ms |
| --- | ---: | ---: |
| Wall time | 50.076 (49.354–71.242) | 53.260 (49.555–76.238) |
| Process CPU | 49.939 (49.272–71.121) | 53.103 (49.466–75.768) |

The candidate medians are higher and the ranges overlap.
The wall median increases by 3.184 ms (6.358%).
The CPU median increases by 3.164 ms (6.335%).
These observations give no improvement claim or numerical budget.
All individual values remain in the raw result.

## GUI results

All 14 samples completed: three per baseline/candidate state for each workflow,
plus one separate legacy comparison per workflow.
Every included sample has wrapper exit 0 and the required completed workflow record.
The source, fixture and preference identities stayed unchanged.
All documents closed. The isolated FreeCAD instances stopped.

The existing comparison reports equal results for all 14 samples.
It preserves its five existing exclusions for volatile fields.
The comparison covers railway state, identities, ordering, metadata, history,
failure handling, document reopen and shape checks within these two workflows.
Analytical and actual caller comparisons passed separately.
Together with unchanged downstream construction, these checks support the
bounded equivalence claim. They do not prove complete B-rep or exported-byte equality.

### Action time

Values are milliseconds. Change is the candidate median minus the baseline
median, followed by the percentage of the baseline median.

| Action | Metric | Baseline median (range) | Candidate median (range) | Change |
| --- | --- | ---: | ---: | ---: |
| Replace left with right | Wall | 2939.951 (2758.815–14065.311) | 2678.564 (2643.950–14020.262) | −261.386 (−8.891%) |
| Replace left with right | CPU | 2967.628 (2774.901–2976.166) | 2823.957 (2767.274–2865.805) | −143.672 (−4.841%) |
| Change right back to left | Wall | 2141.913 (2067.493–13154.295) | 2081.312 (2041.612–13156.413) | −60.600 (−2.829%) |
| Change right back to left | CPU | 2134.989 (2107.535–2165.635) | 2109.142 (2044.065–2163.218) | −25.848 (−1.211%) |
| Create connected pair | Wall | 2621.606 (2611.159–14120.378) | 2678.811 (2639.681–13466.698) | +57.204 (+2.182%) |
| Create connected pair | CPU | 2668.288 (2608.942–2686.561) | 2710.208 (2478.251–2769.899) | +41.920 (+1.571%) |
| Edit connected lengths | Wall | 2259.494 (2148.936–13174.891) | 2241.189 (2152.901–13182.996) | −18.306 (−0.810%) |
| Edit connected lengths | CPU | 2267.106 (2228.393–2324.198) | 2221.426 (2172.221–2328.661) | −45.679 (−2.015%) |

Round 3 wall times are approximately 13–14 seconds in both states.
The earlier rounds are approximately 2–3 seconds. CPU times stay approximately
2–3 seconds. The cause of this difference between dates is not established.
All observations remain included. This spread limits attribution of elapsed-time changes.

### Memory and objects

RSS changes use MiB. The unchanged raw profiler uses the field name
`rss_delta_mb` for this unit.

| Action | Baseline RSS change median (range) | Candidate RSS change median (range) | Median change |
| --- | ---: | ---: | ---: |
| Replace left with right | 213.398 (213.313–217.727) | 217.375 (210.996–275.398) | +3.977 (+1.863%) |
| Change right back to left | 50.496 (45.371–51.770) | 51.570 (50.820–57.836) | +1.074 (+2.127%) |
| Create connected pair | 177.180 (162.004–177.277) | 166.348 (165.898–173.508) | −10.832 (−6.114%) |
| Edit connected lengths | 63.402 (55.910–63.551) | 62.660 (56.859–64.094) | −0.742 (−1.171%) |

The candidate Replace maximum is 275.398 MiB. The baseline maximum is
217.727 MiB. This higher candidate observation remains in the evidence.
Every connected creation adds 14 objects. Each other measured action has zero
object change in both states.

All recorded time and RSS ranges overlap.
Overlap does not prove equal performance or the absence of a regression.

These regression checks are complete for the selected extraction.
They support no performance improvement or acceptance claim.
The independent source and evidence review found no demonstrated blocking
regression specific to the candidate. The timing and memory limitations remain.

## Evidence limits and preservation

One initial launcher attempt could not import the existing bridge dependency.
It stopped before a workflow ran. The invocation then used the approved dependency path.

Three initial candidate runs used default GUI preferences.
Their correctness results remain, but their timings are excluded from the matched comparison.
Those candidate samples were replaced with the retained baseline preferences.
The original logs, documents and preference backups remain available.

The interrupted baseline plain-line sample 3 completed its workflow.
Its final wrapper receipt was missing. Wrapper cleanup can fail after workflow
completion, so the missing receipt could not be treated as exit 0.
The capture failure was classified as `fixture-or-harness-defect` before replacement.

One distinct sample closed this receipt gap with the same protocol.
The original result remains as correctness evidence. Its timing is excluded
from the complete comparison.

The original summary script remains unchanged.
A separate temporary copy selects only the replacement path for that sample.
Its calculations, metrics and normalisation are unchanged.
No source, test, profiler, comparison rule or tolerance changed during recovery.

These regression checks do not discharge D-P6-008.
This task changes no performance rule, production output or release clearance.
The legacy comparison and retirement conditions remain.

The local proof files below are under `tmp/phase7-main-circle-centre/`.
The GUI summary records each raw sample path, hash, value and comparison.
The source manifest identifies all seven unchanged source/test files.

| Proof file | SHA-256 |
| --- | --- |
| `gui-regression-summary.json` | `39f1a1f29d1617c1eaf4a96b240f2894a0afb6368f71761162b2a374b80cafab` |
| `repeated-centre-result.json` | `5258ecc2e206bc72c786ac5f127086b332d234992b2adc1abae5cbebbd1a366b` |
| `source-final.sha256` | `ce97bd8b2d58411e907154dac53ded7677c6514ea9697f0d44c71ecabe5687cd` |
| `recovery-2026-09-08-gui-completion-receipt.json` | `307958a7c1232b6047042b21cee96273394fa7532d167bfb22038d930bc41131` |
| `recovery-2026-09-08-quality-review.md` | `c8ffc3d60ca3d6102e2f10fb9b7c69123d66ae4f4b69f6c741a6ce8a40cc807a` |
