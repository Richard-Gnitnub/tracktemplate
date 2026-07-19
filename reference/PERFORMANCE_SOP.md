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

The cold wrapper must:

- refuse to start if its dedicated localhost bridge is already occupied;
- launch one fresh FreeCAD process with repository-local user data,
  configuration, cache, temporary data, token and port;
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
copied fixture. The isolated preference profile persists between runs and the
operating-system file cache is uncontrolled; state those qualifications on the
report.

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

The B14 report labelled **Whole workflow performance benchmark** currently measures the guided turnout/crossover workflow. It is an operator-visible special-trackwork benchmark, not yet a reconciled benchmark of the complete curve/easement-to-export product pipeline.

Until Phase 1 extends the instrumentation:

- identify the exact instrumented scope on every committed report;
- record missing workflow stages rather than assigning them estimated timings;
- do not compare a turnout/crossover total with a future whole-product total;
- keep repeated actions separate unless their starting state, inputs and cache intent are equivalent;
- require stage totals to reconcile and identify nested spans so time is not double-counted.
- compare internal stage spans with the external method boundary and record
  uncovered setup, dialog, refresh, recompute, report, save and cleanup time;
- reject persisted subprofiles that omit late metadata/display/recompute work,
  even when their enclosing stage timer is complete.

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

## Acceptance gates

A performance change is acceptable only when:

- applicable automated and GUI validation passes;
- analytical and production outputs remain equivalent for the intended scope;
- cache invalidation tests pass;
- the targeted metric improves beyond ordinary run-to-run noise;
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
