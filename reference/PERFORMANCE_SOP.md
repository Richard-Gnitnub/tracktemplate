# Performance Measurement SOP

## Purpose

Use this procedure for performance investigation, refactoring and architecture migration. It prevents comparisons between different documents, workflows, cache states or output scopes.

Performance evidence never replaces correctness validation.

## Before changing code

Record:

- Git commit or exact working-tree state;
- macro filename and version;
- FreeCAD version and installation route;
- operating system and relevant hardware;
- representative document or reproducible construction inputs;
- target entity identity and configuration;
- exact guided stage sequence;
- selected display, validation and export options.

Do not use confidential file paths or user data in a committed benchmark report.

<a id="phase-6-performance-host-boundary"></a>

## Hosts for Phase 6 performance evidence

D-GOV-007 and D-GOV-010 authorise only the profiles in this list to supply
candidate evidence for Phase 6 performance:

- `linux-x86_64-flatpak-freecad-1.1.1`
- `linux-x86_64-flatpak-freecad-1.1.3`, as D-GOV-006 defines it
- `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`, as D-GOV-010 defines it.

A subsequent decision can admit only a performance result from one of these
profiles. Each new schema-2 result must have exact host
identity. It must name the ID and FreeCAD version of the exact host profile.
Keep results from different host profiles in different sets.

The value of `profile_id` is
`phase6-transition-edit-validate-export-profile-v1`. It identifies the
measurement method, not the record schema. The `schema_version` value is `2`
for new samples and performance records.

The 1.1.1 report from 2026-08-02 is a schema-1 report. It does not have a
`host_profile_id` field. It records FreeCAD 1.1.1, platform data, and the
qualified-runtime contract hash. These data identify the exact host profile
for FreeCAD 1.1.1. D-GOV-007 keeps this report as 1.1.1 evidence.

To claim that TrackTemplate performance became better, compare results from one
exact host profile. A different method can compare exact profiles only if
it independently shows the effect of the host profile and the TrackTemplate
effect. The project must record the method and its authority.

If the project qualifies a subsequent host profile, this does not authorise
performance evidence from that profile. Only a Level 3 owner decision can add
an exact host profile that is different. D-GOV-007 adds the first exact 1.1.3
profile.

D-GOV-010 adds the exact 1.1.3 profile with CPython 3.13.13 and
PySide6/Qt 6.11.1. The decisions admit no performance result. They define no
value for a performance budget. They do not accept Exit 4 or claim that
performance became better.

Before the project claims that TrackTemplate performance changed on this
profile, the D-GOV-009 investigation must record a baseline for this profile.
For a TrackTemplate before/after comparison, do not use results from profiles
with different exact identities.

<a id="phase-6-exit-4-comparison-direction"></a>

## Phase 6 Exit 4 comparison direction

D-GOV-008 accepts the [PR #50 performance series](benchmarks/2026-08-16-phase6-freecad-1.1.3-transition-pipeline-performance.md)
as the comparison baseline. The baseline raw record has SHA-256
`83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a`.
The evidence source state is
`f370b029bb4c1ce34987dc025a741185e233df04`. The host profile is
`linux-x86_64-flatpak-freecad-1.1.3`. The measurement profile is
`phase6-transition-edit-validate-export-profile-v1`.

The baseline has the selected Exit workload from `420.000` mm to `360.000`
mm. Each new GUI process records one full cold journey. That journey has Edit,
Validate, and Export. Each process also records one warm-up and three warm
reuse cycles. The correctness, output, lifecycle, and cleanup conditions are
part of the comparison baseline.

The accepted source does one necessary preview regeneration during Edit. The
preview sampler calculates 33 stations. For each station, it calculates the
clothoid displacement with the scalar API. For each of the 31 interior
stations, the API does a 240-step Simpson integration from station zero. The
endpoint calculation also does an integration.

A temporary profile measured 50 preview regenerations. It measured 3.263 ms
of process CPU time for each preview regeneration. The profile recorded 0.144 seconds for
integration and 0.163 seconds for the preview sampler. Thus, zero-origin
integration is a measured cost during Edit. It is not all the Edit cost.

### Selected performance hypothesis

One preview batch function can calculate all preview displacement values
without zero-origin integration at each interior station. This performance
optimisation can make process CPU time for Edit lower. The candidate must do
all new calculation work during measured Edit.

The candidate must add no work to Validate, Export, a warm cycle, cleanup, or
an unmeasured boundary. The profile does not measure process launch, module
import, fixture construction, dialog opening, or document disposal at the end.
The candidate must add no work to these boundaries. It must add no work to other
setup or teardown that the profile does not measure.

Code inspection must show that the candidate does all new product work during
measured Edit. If inspection does not give sufficient proof, stop the cycle.
The result is FAIL if measured Edit does not include all new candidate work.

The authorised product boundary at Level 2 is:

- `tracktemplate/presentation/transition_preview.py`
- If necessary, one preview batch function in
  `tracktemplate/domain/alignment.py`
- Directly dependent tests for railway behaviour, the preview, FreeCAD GUI,
  performance, and preservation
- The performance report and current evidence that are directly dependent.

The product change must preserve the scalar alignment API. It must preserve
the segment count, frame, identities, source signatures, cache lifecycle, and
Coin mapping. Preview points must agree with their oracle within `1.0e-10` mm.
The change must preserve canonical state, transactions, Undo/Redo,
save/reopen, and cleanup behaviour. Exact validation, DXF bytes, manifest
bytes, hashes, and diagnostics must not change.

Do not add a cache that the evidence does not make necessary. Do not add a
runtime dependency or a public API. Change only the specified product boundary
and directly dependent tests and evidence. Do not change railway intent, exact
geometry, validation, export, or the measurement profile. Stop if the preview
batch function cannot preserve the stated invariants.

### Comparison rule

The Level 2 cycle must use 12 paired blocks. Each block has one baseline
sample and one candidate sample. Each sample uses a new GUI process. Use the
baseline first in six blocks. Use the candidate first in the other six blocks.
Record the sequence before the measurements start.

Use the exact 1.1.3 host profile, measurement profile, workload, settings, and
output scope in all samples. The baseline product blobs must equal those at
the PR #50 source state. The candidate can have changes only
in the authorised Level 2 boundary. Preserve all raw attempts. Record the
failure class before a replacement pair starts.

A product defect, invariant difference, or correctness failure gives a FAIL
result and stops the cycle. A replacement is possible only for the failure
class `fixture-or-harness-defect` or `environment-or-profile-defect`. The
attempt with this failure must give no measurement for the comparison. Record
the failure class before replacement. Use the same block and the same recorded
sequence. Preserve the attempt with this failure and the replacement.

For each metric, calculate candidate minus baseline in its paired block. A
negative paired difference shows a lower candidate value. Calculate the
baseline MAD from the 12 baseline values for that metric. Report all values,
medians, ranges, paired differences, MAD values, absolute changes, and
percentage changes.

For each numeric warm metric, calculate the median of the three measured warm
cycles in one sample. This median is the warm block value for that sample.
All warm-cycle correctness results must be PASS.

The comparison result is PASS only when all these conditions are true:

1. The paired difference for process CPU time in Edit is negative in a minimum
   of 10 of the 12 blocks. The median of these differences is negative.
2. The median of the paired differences for Edit wall time is negative. This
   condition records measurement noise in GUI wall time. It does not ignore
   the noise.
3. The medians of the paired differences for cold-journey CPU and wall time
   are negative.
4. The Level 2 cycle must use the no-displacement rule for Validate, Export,
   cleanup, all warm block values, all resource metrics, and the journey
   remainder. The result for a metric is FAIL if the median of its paired
   differences is more than its baseline MAD. The result is also FAIL if 10 or
   more paired differences are positive.
5. The Level 2 cycle must use condition 4 for RSS, RSS change, high-water RSS,
   and high-water RSS change in each measured stage and the full journey.
6. All discrete invariants must have results equal to the baseline results.
7. Canonical state, preview geometry, exact geometry, receipts, DXF, manifest,
   hashes, diagnostics, and deterministic reuse must have unchanged results.
8. Code inspection must show that the candidate does all new product work
   during measured Edit. New work in an unmeasured boundary gives FAIL.

One sample cannot give a PASS result. A missing condition gives a
FAIL result. Do not select a new rule after the project knows the candidate
results.
Do not use the 1.1.1 report or different host profiles to claim that
TrackTemplate performance became better.

D-GOV-008 authorises only this Level 2 outcome:

> Make one performance optimisation at Level 2 for zero-origin integration in
> the preview sampler. Validate it against the accepted FreeCAD 1.1.3
> baseline and the comparison rule.

D-GOV-008 makes no product change. It does not admit the baseline or a
subsequent result as Exit 4 evidence. It defines no product performance budget.
Exit 4 stays Pending. A subsequent decision at Level 3 must admit the evidence
before the owner can accept Exit 4.

<a id="phase-6-exit-4-baseline-attribution-direction"></a>

## Phase 6 Exit 4 baseline-attribution direction

D-GOV-009 records the D-GOV-008 performance direction as exhausted for new
product work for Phase 6 Exit 4. D-GOV-008 stays Accepted as the authority for
its comparison baseline, performance hypothesis, comparison rule, and first
boundary at Level 2. Preserve the two subsequent results from Level 2 as
retained negative evidence. The two results are not improvement evidence. They
are not Exit 4 evidence.

Do not make a third preview-sampler change. This includes a new
polynomial, approximation, cache, or other variation of the D-GOV-008
hypothesis. The retained evidence does not show sufficient measured cost in a
different measurement area that is not part of the D-GOV-008 preview-sampler
boundary.

The D-GOV-009 investigation used the accepted Edit journey on FreeCAD 1.1.3. It
reported these measurement areas:

1. Canonical-state and state-construction work
2. Preview and sampler construction
3. Coin binding or scene-graph replacement
4. GUI processing
5. The unattributed remainder.

The retained record contains the exact host profile, source state, workload,
method, measurement boundary, and instrumentation overhead. It reports a
measurement area as Unknown when the evidence does not show a TrackTemplate
product boundary or an architectural boundary.

The investigation changed no product source. It made no performance
optimisation. Its result is direction-selection evidence only.

D-GOV-011 uses this result to select one different performance hypothesis. It
does not change the D-GOV-008 comparison rule. It does not do either retained
comparison again. It defines no product performance budget and does not accept
Exit 4.

<a id="phase-6-exit-4-canonical-record-direction"></a>

## Phase 6 Exit 4 canonical-record direction

D-GOV-011 selects one performance hypothesis in the measured canonical area
of Edit. During one accepted Edit, the route reads the selected canonical record three
times before the write. A necessary check reads it one more time after the
write. D-GOV-011 authorises a subsequent product change at Level 2. That change
can remove only two repeated reads before the write. It must keep one live read
before the write and the read after the write.

The permitted product path is
`tracktemplate/adapters/freecad/transition_state.py`. The product change must
use the one live state for the `stale-edit-base` and stable-identity checks.
During object mapping, it must use the same state for the selected object.

The object-mapping check must still read other canonical records. It must
still reject a duplicate stable identity. The public read and update contracts
must not change. Do not add a cache. Do not move a record read to selection,
setup, teardown, preview, Coin, or GUI processing.

The product change must preserve canonical state and transaction semantics. It
must preserve one-unit Undo/Redo, stable identity, object mapping, preview, and
Coin results. It must preserve persistence, lifecycle, cleanup, exact
validation, deterministic export, diagnostics, and failure recovery.

Before a product change, do the exact attribution method in D-GOV-009 again on clean
protected main. Use only
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`. Record a new baseline
series of 10 processes and a new attribution series of 10 processes. The
attribution materiality rule in D-GOV-009 must give a PASS result for the
canonical measurement area. If it does not, stop before a product change.

Record the 12-block comparison sequence before a product change. Use six
baseline-first blocks and six candidate-first blocks. Use a new process for
each sample. Use the full accepted journey for Edit, Validate, Export, warm
reuse, correctness, lifecycle, output, and cleanup.

The comparison result is PASS only when all these conditions are true:

1. Process CPU time for Edit is lower in at least 10 of 12 paired blocks. The
   median paired difference is negative.
2. The median paired differences for Edit wall time and cold-journey CPU and
   wall time are negative.
3. Apply the D-GOV-008 no-displacement rule to Validate, Export, cleanup, warm
   block values, resource metrics, and the journey remainder.
4. Apply that rule to preview and sampler construction, Coin or scene-graph
   work, GUI processing, and the unattributed remainder.
5. Record the measurement areas in D-GOV-009 in both samples of each paired
   block. Use the same test-owned instrumentation in both samples. Record its
   overhead.
6. All discrete invariants and warm-cycle correctness results are equal to the
   baseline results.
7. The results for canonical state, preview geometry, exact geometry, receipts,
   DXF, manifest, hashes, diagnostics, and deterministic reuse equal baseline
   results.
8. Source inspection shows that the product change removes the two repeated
   reads. It must add no work to an unmeasured boundary.

A missing condition gives FAIL. A host-identity difference gives FAIL. A
product defect or invariant difference gives FAIL and stops the cycle. Preserve
all attempts. Classify a failure before a replacement. Do not select a new
rule after the project knows the candidate results.

D-GOV-011 authorises one subsequent product change at Level 2 in this boundary. It
makes no product change. It admits no performance result or Exit 4 evidence.
Exit 4 stays Pending. A subsequent owner decision at Level 3 is necessary before the owner
can admit a subsequent result for Exit 4.

## Baseline procedure

1. Preserve an unchanged starting document or a reproducible input recipe.
2. Start FreeCAD in a known state.
3. Load the target macro and equivalent starting document/state.
4. Reset the macro's whole-process timings.
5. Run the defined stage sequence without unrelated UI actions.
6. Copy the complete performance report.
7. Save any relevant internal stage profile that the macro reports.
8. Repeat enough times to identify normal variation; three or more comparable runs are preferred.

Use separate series for:

- **cold runs:** fresh process/document/cache state;
- **warm runs:** unchanged-result reuse with the same valid signatures.

Do not average cold and warm runs together.

## Isolated automated GUI runs

The optional development bridge under `tools/freecad_bridge/` may drive the
FreeCAD GUI. Its tracked patch and construction recipe create the ignored local
checkout and fixture; it remains development instrumentation, not a product
runtime dependency or a substitute for result validation.

On a fresh checkout:

```bash
tools/freecad_bridge/setup-freecad-cli
tools/freecad_bridge/build-b14-base
```

For the current pinned B14 crossover recipe:

```bash
tools/freecad_bridge/run-b14-cold
```

For unchanged-result reuse, select the completed FCStd from a successful full
cold run:

```bash
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The bounded B14-to-B15 correctness qualification uses that same class of
completed cold document:

```bash
tools/freecad_bridge/run-b15-acceptance \
  --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

It records action durations so the operator-visible cost is not hidden, but it
is not a repeated performance series. Do not turn its exceptionally slow cold
or unchanged-result observations into pass thresholds or approved human-use
budgets.

The Phase 1 B14 plain-line edit lifecycle/rollback characterisation uses the
fixed plain-line fixture rather than a completed crossover document. Its
command retains the legacy `ordinary` identifier:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Its successful replacement boundary includes B14's real dialog, confirmation,
calculation, exact-shape construction, document replacement, metadata,
recomputes, report and success dialog. Process launch, macro load, fixture open,
semantic-oracle work and the separately reported history and
recompute/save/reopen boundaries are excluded. The v2 recipe then records the
actual synchronous Undo/Redo call, that call plus explicit recompute, and the
complete deep-validation duration as separate fields. Only the first two
describe the history action; the roughly one-second semantic traversal is
harness cost and must not be presented as operator-visible Undo/Redo time.
The synchronous measurements also exclude any later viewport repaint, so do
not present them as a complete GUI-latency budget.
Change-back, zero-angle and injected-abort actions occur later in the same
process and are correctness timings, not equivalent cold measurements. The
injected fault is not a normal performance stage. Compare a future routine
editor only with the successful action under the same fixture, inputs, output
scope and fresh-process qualifications, and also report its complete
Validate/Export cost.

The Phase 1 B14 plain-line selected-export characterisation uses the same
fixed fixture and B14's explicit selected-production dialog:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Its comparable cold boundary is the first base-export action in each fresh
process: real dialog construction, configured preview, confirmation, late
no-probe recheck, staged export/manifest commit, summary and post-success
preview refresh. Report the full action separately from the selected-export
transaction and each preflight. The later revision, overwrite and injected
rollback actions share the process and are correctness observations rather
than equivalent cold runs. The complete four-scenario orchestrator also parses
and hashes every output; its duration is harness cost, not operator-visible
export time.

For this legacy path, count exporter dispatches as well as time. One complete
action currently executes three full DXF/SVG probe preflights, a late cheap
no-probe recheck and the actual deliverables. A future optimisation must retain
the same confirmed paths, validation result, staging/rollback semantics and
post-action state. This selected-export transaction is not evidence for B14's
separate create-time `run_production_export()` path, which must be measured and
qualified independently.

The independent Phase 1 create-time export characterisation drives the normal
curve Generate action:

```bash
tools/freecad_bridge/run-b14-ordinary-create-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Its comparable cold boundary begins before `CurveInputDialog` construction and
ends after the final overall result dialog. It includes confirmation,
calculation, fresh legacy exact-shape construction, document replacement and
commit, one exporter-bound preflight, per-file export plus manifest,
schedule/material report, recomputes and result UI. Process launch, macro load,
fixture open, artifact parsing and save/reopen are outside this boundary.
Report the complete action, preflight and actual export separately; do not add
nested durations to the action total.

The later injected final-task failure shares the process and is correctness
evidence, not a cold performance result. Record its surviving files, manifest,
document state and cleanup. Never describe time saved by skipping the failed
STEP writer as an optimisation. The current legacy path is non-atomic and must
not be used as the acceptance target for a future exporter.

The cold wrapper must:

- refuse to start if its dedicated localhost bridge is already occupied;
- launch one fresh FreeCAD process with repository-local user data,
  configuration, cache, a fresh per-run temporary/recovery directory, token
  and port;
- start with no open document, copy the unchanged fixture for the run, and
  preserve the fixture itself;
- validate the fixture's semantic object/curve/centreline contract and record
  its semantic and binary hashes, exact settings, stage order and process/cache
  qualification;
- resolve the two hosts by persisted centreline identity and place the crossover
  by Host A centreline chainage, never UI order or a free XYZ datum;
- approve only explicitly enumerated confirmation dialogs and fail on any
  warning, error or changed/unexpected dialog;
- assert the expected domain status after every guided stage;
- retain both B14's internal report and an outer method-invocation timing;
- save structured state, a disposable FCStd copy, rendered GUI evidence and
  startup logs under ignored `benchmark-output/`; and
- terminate only the exact Flatpak instance it launched, then verify the bridge
  port is no longer live.

Here, **cold** means a fresh FreeCAD process, empty document session and freshly
copied fixture. The isolated preference profile persists between runs, the
temporary/recovery directory does not, and the operating-system file cache is
uncontrolled; state those qualifications on the report.

The controlled warm wrapper requires the completed document's sibling
`run.json`, exact macro and semantic-base hashes, all seven cold stages, and the
27-object final inventory. It opens a copy in a fresh isolated process, performs
one warm-up, then exactly three same-process measurements of B14's real
**Generate supported chair solids** panel action. Every iteration must report
`unchanged_result_reused=True` and retain identical object, signature, chair
count and solid-shape fingerprints. It never saves over the source or copied
document. Replaying timbering, support, layout, integration, or another
destructive stage is not a cache-reuse measurement merely because it occurs in
the same process. Compare this stage-specific warm result with the equivalent
cold stage boundary, never with the full cold workflow total.

Generated JSON, screenshots, logs and FCStd files may contain local absolute
paths and remain ignored. Preserve a sanitised committed report with hashes for
the raw artifacts needed to audit it.

## Current instrumentation boundary

The B14 report labelled **Whole workflow performance benchmark** currently measures the guided turnout/crossover workflow. It is an operator-visible special-trackwork benchmark, not yet a reconciled benchmark of the complete curve/easement-to-export product pipeline. The separate Phase 1 plain-line wrappers (whose command names retain the legacy `ordinary` identifier) add external replacement, persistence, explicit selected-export and fixed create-through-export boundaries; they do not make the internal B14 report whole-product instrumentation or cover target-architecture deferred exact-shape reconstruction.

The canonical Phase 1 index of those measurements is
[`contracts/phase1-performance-boundaries.json`](contracts/phase1-performance-boundaries.json).
Its validator freezes the source/report evidence, labels operator, nested,
harness and same-process spans, bounds the five known instrumentation defects,
and reserves the still-unmeasured lightweight Edit, explicit Validate,
export-from-validated and complete edit-through-export slots. Consult it before
comparing current profiles or designing a replacement measurement.

The focused
[`phase1-chair-analysis-persistence.json`](contracts/phase1-chair-analysis-persistence.json)
oracle now supplies executable defect evidence for the chair subprofile: a
fixed direct call separates logical calculation from record extraction,
metadata/display work and save/reopen persistence, while the accepted GUI
report remains the operator-action owner. Its two disposable timing
repetitions are diagnostic only, not a controlled performance profile or a
budget. Do not subtract them from the independently recorded panel duration;
use the source/lifecycle evidence to define the successor boundary and measure
that boundary afresh.

Phase 1 closed after accepting the bounded instrumentation inventory and
assigning the unresolved target measurements to their named later gates. Until
those owners reconcile the complete instrumentation:

- identify the exact instrumented scope on every committed report;
- record missing workflow stages rather than assigning them estimated timings;
- do not compare a turnout/crossover total with a future whole-product total;
- keep repeated actions separate unless their starting state, inputs and cache intent are equivalent;
- require stage totals to reconcile and identify nested spans so time is not double-counted;
- reconcile parent, non-overlapping children and uncovered time inside each
  individual run before calculating summary statistics; never add or subtract
  independently selected medians as though they came from one run;
- compare internal stage spans with the external method boundary and record
  uncovered setup, dialog, refresh, recompute, report, save and cleanup time;
- reject persisted subprofiles that omit late metadata/display/recompute work,
  even when their enclosing stage timer is complete.

Every recorded span must use one of the register's classes:

- **operator action**: the declared user-visible action boundary;
- **nested component**: contained work that is diagnostic and never added to
  its parent;
- **harness enclosing**: setup, polling, deep validation, capture or other
  development work around an action;
- **same-process correctness**: a later action useful for behaviour evidence
  but not equivalent to the cold or warm comparison; or
- **missing target boundary**: a required measurement with no implementation or
  evidence yet. Missing values stay absent rather than being estimated.

## Metrics

Capture where available:

- total and per-stage wall time;
- process CPU time and one-core percentage;
- resident memory before, after and delta;
- FreeCAD document objects before, after and delta;
- document recompute count and duration;
- metadata writes and serialisation time;
- display-object and exact-shape construction time;
- cache hit/reuse status;
- error or validation status.

For repeated measurements, report the median and range. Keep the individual results available so an outlier is not hidden.

## Comparison rules

- Compare equivalent starting state, settings, entity, stage order and output scope.
- Compare the same FreeCAD build unless the FreeCAD upgrade is itself under test.
- Change one performance hypothesis at a time.
- Report absolute time/resource change and percentage change.
- Separate saved calculation time from deferred work. Moving cost to Validate/Export is an architectural choice and must be reported at both boundaries.
- Count transient export objects and cleanup cost when evaluating deferred geometry.
- A reduction achieved by skipping validation, suppressing output, changing tolerances or returning stale data is invalid.

## Architecture migration comparison

When replacing a legacy persistent-shape path with a lightweight preview path, compare:

1. document creation/update time;
2. preview regeneration time;
3. object and memory growth during editing;
4. explicit validation time;
5. export preparation and write time;
6. cleanup time and remaining object/memory delta;
7. total end-to-end time for an operator who proceeds to export;
8. total time for an operator who edits but does not export.

This prevents an apparently fast editor from hiding an unacceptable export penalty.

## Acceptance conditions

A performance change is acceptable only when:

- applicable automated and GUI validation passes;
- analytical and production outputs remain equivalent for the intended scope;
- cache invalidation tests pass;
- the targeted metric improves beyond normal run-to-run noise;
- no material regression is introduced in another guided stage;
- document state, transactions and cleanup remain correct;
- limitations and unvalidated paths are reported.

Numerical thresholds should be added only after representative baselines have been collected and agreed.

## Report template

```text
Change/hypothesis:
Macro/version:
FreeCAD/environment:
Document/input:
Entity/settings:
Workflow stages:
Cache state:
Run count:

Before median (range):
After median (range):
Absolute change:
Percentage change:

Wall-time breakdown:
CPU-time breakdown:
RSS/object/recompute differences:
Validation performed:
Output-equivalence evidence:
Known limitations/noise:
Decision:
```
