---
name: tracktemplate-performance-engineering
description: Investigate TrackTemplate runtime, memory, recompute, or interaction performance. Make measured improvements that preserve verified railway behaviour. Use for profiling, caches, deferred geometry, regressions, or numerical performance limits.
---

# TrackTemplate performance engineering

## Purpose

Identify the largest measured cost. Make the smallest improvement that preserves
behaviour. Compare equivalent states before and after the change. Do not hide
work at a later validation or export boundary.

## Responsibility boundary

Before a qualified host measurement, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`

Before a measurement with the real-GUI bridge, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`

`reference/PERFORMANCE_SOP.md` owns the measurement procedure and evidence
quality. Before work starts, read it.

If the cause of a regression or resource increase is unknown, use
`$tracktemplate-debugging`. After evidence identifies the main path,
`$tracktemplate-simplify` can control a simplification that preserves
behaviour. `$tracktemplate-python-writing` governs source edits.

`$tracktemplate-change-validation` interprets correctness and performance
evidence. `$tracktemplate-quality-review` judges the complete change.

This skill does not set product budgets or accept changed behaviour. A faster
partial workflow does not supply evidence for the complete workflow.

## Comparison baseline

1. Read the current phase and phase-exit status in `reference/PROJECT_PLAN.md`.
   Read the applicable current evidence and performance risks.
2. Define the comparison baseline with the items listed below.
3. Before measurement, add assertions for correct behaviour.
4. Where applicable, record elapsed-time distributions, CPU, memory, FreeCAD
   object counts, recompute counts, and output parity. Do measurements again.
   Report variation.
5. Report which editing, Validate, and Export costs the measurement includes
   or excludes.

The comparison baseline includes these items:

- Operator workflow.
- Exact source state and runtime/profile.
- Input document or fixture.
- Cold or warm state.
- Cache state and process boundary.
- Bounded scope of the output.

## Engineering procedure

1. **Measure first.** Find the path with the largest measured cost. Use
   existing instrumentation or the smallest disposable probe. Do not select
   an improvement from file size, estimated call frequency, or one run.
2. **Record one performance hypothesis.** Identify the work that will
   disappear, move, or become reusable. Name the metric that can disprove
   the performance hypothesis.
3. **Check architecture.** Keep canonical state authoritative. Keep derived
   views disposable. Defer exact geometry only to an explicit boundary.
   Make sure that the cache signature and invalidation proof are complete.
4. **Change one measured area.** Keep algorithm changes, cache changes,
   representation changes, cleanup, and mechanical extraction separately
   reviewable.
5. **Prove correct behaviour first.** Do the checks necessary for the affected
   path again. These can include analytical, FreeCAD, GUI, persistence,
   exact-output, and export checks.
6. **Compare equivalent states.** Use the same source inputs, environment,
   process/cache conditions, and output scope. Report medians or
   distributions. Do not report only the best run without qualification.
7. **Check costs that moved.** Work can be deferred, cached, or moved between
   boundaries. If so, measure the complete workflow from edit through export.

## Constraints

- Do not weaken tolerances, diagnostics, geometry fidelity, transactions, or
  tests to get a better measurement.
- Do not invent a threshold.
- Do not report an observed baseline as an accepted budget.
- Do not compare B14 cold creation with B16 warm reuse or another unequal
  workflow.
- Without measurements, do not report fewer lines, fewer objects, or
  deferred work as faster.
- Record measurement noise, instrumentation faults, and unsupported GUI claims
  as evidence limitations.

## Report

Report these results:

- Workflow and measurement boundary.
- Baseline distribution and largest measured cost.
- Tested performance hypothesis and exact change.
- Correctness evidence.
- Equivalent results before and after the change.
- Costs that moved and costs that remain.
- Measurement limitations.
- Budget or GUI decisions that still need project-owner acceptance.
