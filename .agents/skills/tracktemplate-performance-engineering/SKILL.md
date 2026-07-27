---
name: tracktemplate-performance-engineering
description: Investigate and improve TrackTemplate runtime, memory, recompute or interaction performance while preserving verified railway behaviour. Use for profiling, optimisation, cache design, deferred-geometry cost, performance regressions or numerical performance-budget work.
---

# TrackTemplate performance engineering

## Outcome

Identify an evidenced dominant cost, make the smallest behaviour-preserving
improvement and compare equivalent before/after states without hiding work at a
later validation or export boundary.

## Responsibility boundary

- `reference/PERFORMANCE_SOP.md` owns measurement procedure and evidence
  quality; read it before acting.
- `$tracktemplate-debugging` owns causal isolation when an unexpected
  regression or resource-growth cause is not established.
- `$tracktemplate-simplify` may control a behaviour-preserving complexity
  reduction after the dominant path is proved.
- `$tracktemplate-python-writing` governs source edits.
- `$tracktemplate-change-validation` interprets correctness and performance
  evidence; `$tracktemplate-quality-review` judges the complete change.

This skill does not set product budgets, accept changed behaviour or turn a
faster partial workflow into end-to-end evidence.

## Baseline

1. Read the current phase gate, owning evidence record and relevant performance
   risks in `reference/PROJECT_PLAN.md`.
2. Define the operator-visible workflow, exact source state, runtime/profile,
   input document or fixture, cold/warm state, cache state, process boundary
   and output scope.
3. Establish correctness assertions before timing.
4. Record elapsed distribution, CPU, memory, FreeCAD object/recompute counts and
   output parity where applicable. Use repetitions and report variation.
5. State which editing, Validate and Export costs are included or excluded.

## Engineering workflow

1. **Profile first.** Locate the dominant measured path with existing
   instrumentation or the smallest disposable probe. Do not optimise from file
   size, call frequency guesses or a single run.
2. **State one hypothesis.** Identify the work expected to disappear, move or
   become reusable and the metric that could disprove the hypothesis.
3. **Check architecture.** Keep canonical state authoritative, derived views
   discardable and exact geometry deferred only to an explicit boundary. A
   cache must have a complete signature and invalidation proof.
4. **Change one cost boundary.** Separate algorithmic change, caching,
   representation change, cleanup and mechanical extraction into independently
   reviewable slices.
5. **Prove correctness first.** Rerun analytical, FreeCAD, GUI, persistence,
   exact-output and export evidence required by the affected path.
6. **Compare equivalent states.** Use the same source inputs, environment,
   process/cache conditions and output scope. Report medians or distributions,
   not an unqualified best run.
7. **Check displaced cost.** Measure complete edit-through-export behaviour
   when work is deferred, cached or moved across a boundary.

## Guardrails

- Do not weaken tolerances, diagnostics, geometry fidelity, transactions or
  tests to improve a number.
- Do not invent a threshold or call an observed baseline an accepted budget.
- Do not compare B14 cold creation with B16 warm reuse or another unequal
  workflow.
- Do not describe fewer lines, fewer objects or deferred work as faster without
  measurement.
- Treat noise, instrumentation faults and unsupported GUI claims as visible
  evidence limitations.

## Report

Report the workflow and measurement boundary, baseline distribution, dominant
cost, tested hypothesis, exact change, correctness evidence, equivalent
before/after results, displaced or remaining costs, measurement limitations
and any budget or GUI decision still requiring project-owner acceptance.
