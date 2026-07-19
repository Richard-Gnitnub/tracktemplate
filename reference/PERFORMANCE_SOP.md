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
