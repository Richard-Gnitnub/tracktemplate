---
name: tracktemplate-debugging
description: Find causes of TrackTemplate defects across standalone Python, FreeCAD, GUI, persistence, export, and performance. Use for unexpected behaviour, tracebacks, hangs, crashes, intermittent results, resource increases, or unexplained validation failures.
---

# TrackTemplate debugging

## Purpose

Find the cause from evidence at the smallest responsible boundary. Do not
report a possible symptom or recent diff as a confirmed cause. Without user
authority for a fix, do not make retained edits.

## Responsibility boundary

Before qualified host diagnosis, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`

Before diagnosis with the real-GUI bridge, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`

Use `$tracktemplate-change-validation` for evidence selection, failed-test
preservation and classification, and interpretation of completed checks.

After you identify the boundary of a failure, use this skill to investigate
its cause. Also use it for unexpected runtime behaviour without a stable test.

For an authorised Python or FCMacro fix, use
`$tracktemplate-python-writing`. After validation, use
`$tracktemplate-quality-review`.

Before diagnosis of performance regressions, read
`reference/PERFORMANCE_SOP.md`. This includes timing, CPU, memory, object
counts, and caches.

## Establish the failure

1. Read `reference/PROJECT_PLAN.md` and the canonical owner of the expected
   behaviour. Read `reference/VALIDATION.md` and `reference/TESTING_POLICY.md`.
2. Record the failure information listed below.
3. Preserve the complete error, traceback, log, or failed assertion. Keep the
   original reproduction command and necessary sentinel exact.
4. Find whether the problem is reproducible, intermittent, specific to
   one environment, or only reported.
5. Use copied or disposable FCStd inputs. Record state before and after a
   probe. Do not mutate the only operator document for diagnosis.

The failure information includes these items:

- Expected and observed behaviour.
- Exact input or operator action.
- Environment/profile and source state.
- Cache state and process state.
- First observable difference.

If a selected test fails, use `$tracktemplate-change-validation` before any
retained repair. This applies to source, tests, fixtures, and expected results.

Before an exporter interruption becomes a defect claim, read the
[supported exporter failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model).
Put the report in one category:

1. A failure within the supported model.
2. An operator recovery case within the
   [restart procedure](../../../reference/RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export).
3. An arbitrary asynchronous interruption at an unsupported instant.

Category 3 can supply architectural research evidence. It does not
automatically show an implementation defect or block a phase exit.

## Investigation procedure

1. **Make sure of the active path.** Identify the launcher, package module,
   adapter, compatibility route, and qualified runtime that executed.
2. **Find the first difference.** Follow values and state backwards from the
   first incorrect observation. Compare them with the last correct
   observable boundary.
3. **Record competing hypotheses.** For each hypothesis, name the predicted
   observation. Name the smallest read-only or disposable probe that can
   disprove it.
4. **Change one factor.** Keep other inputs, runtime, cache, and process
   boundaries fixed. Prefer instrumentation, state records, and narrow
   function calls to retained code changes.
5. **Reduce the example safely.** Preserve the failure as the input or
   workflow becomes smaller. Do not remove validation, transaction, or
   recovery behaviour from the production path to simplify reproduction.
6. **Identify the responsible boundary.** Distinguish the causes listed below.
7. **Test the claimed cause.** Use a probe that predicts a new observation.
   A restatement of the traceback is insufficient. Record evidence that
   disproves the hypothesis. Change the hypothesis to agree with that
   evidence.
8. **Make only authorised fixes.** Where practical, add a regression proof
   that fails for the diagnosed cause. Make the smallest repair at the
   classified boundary. Do the original reproduction again. Then do the
   checks for each affected validation layer.

Possible causes belong to these boundaries:

- Domain calculation or application state.
- Signatures or invalidation.
- FreeCAD lifecycle or persistence.
- Presentation or exact geometry.
- Export.
- Dependency or profile.
- Fixture or test harness.
- Operator data.

## Checks for each boundary

- **Standalone/domain:** Check exact units, frames, tolerances, input
  normalisation, deterministic ordering, stable identities, and hidden
  mutable state.
- **Cache/reuse:** Check complete signatures, invalidation, change-back, and
  process freshness. Find whether a stale result appears to be a solver
  error.
- **FreeCAD/document:** Check the qualified profile, imports, object and
  property identities, recompute, transactions, Undo/Redo, cleanup, and
  save/reopen.
- **GUI/presentation:** For selection, visibility, event order, or visible
  state, reproduce the failure in a real GUI. Headless success is
  insufficient.
- **Persistence/migration:** Examine without changes first. Distinguish
  corrupt, unsupported, future, and ambiguous state from migration
  behaviour.
- **Export/exact geometry:** During diagnosis, preserve staging, export
  validation, rollback, manifests, source hashes, and cleanup of transient
  objects.
- **Performance/resource:** Compare equivalent cold/warm states and process
  boundaries. Preserve correctness assertions and evidence of measurement
  noise.

## Investigation constraints

- Do not edit B14 or accepted B15 evidence to support a hypothesis.
- Do not widen tolerances, weaken assertions, or change an oracle to support
  a hypothesis.
- Do not assume that the most recent change caused the problem. Use the diff
  or history only as evidence. History operations remain subject to
  `reference/RECOVERY_AND_BACKUP.md`.
- Do not add broad logs that expose private paths, credentials, source data,
  or large geometry payloads.
- Unless temporary instrumentation has an accepted permanent diagnostic
  purpose, remove it.
- If reproduction fails, record the evidence limitation. Get better observations
  or request the missing environment. Do not invent a fix.
- If behaviour changes under a debugger, record the difference as a possible
  timing effect. It does not prove a race. Use repeated equivalent runs and
  tracing with less effect on timing.
- Before a proposed dependency change, check third-party defect claims with
  current official release notes or issue evidence.

## Report

Report these results:

1. Expected and observed behaviour, and reproduction status.
2. Exact source, runtime, input, cache state, and process boundary.
3. First difference and collected evidence.
4. Tested hypotheses, including evidence against them.
5. Confirmed cause or remaining uncertainty, with confidence.
6. Responsible repair boundary and regression proof.
7. Authorised fixes and repeated validation.
8. GUI, persistence, export, or performance checks that were not done.
