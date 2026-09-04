---
name: tracktemplate-debugging
description: Reproduce, isolate and diagnose TrackTemplate defects and regressions across standalone Python, FreeCAD, GUI, persistence, export and performance boundaries. Use for unexpected behaviour, tracebacks, hangs, crashes, nondeterminism, resource growth or a failing validation whose cause is not yet established.
---

# TrackTemplate debugging

## Outcome

Produce an evidence-backed root-cause diagnosis at the narrowest responsible
boundary. Do not turn a plausible symptom or recent diff into a confirmed cause.
Diagnose without retained edits unless the user also asks for a fix.

## Responsibility boundary

- Run `.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`
  before qualified host diagnosis. Run
  `.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`
  before diagnosis that uses the real-GUI bridge.
- Use `$tracktemplate-change-validation` to select evidence, preserve and
  classify a failed test, and determine what completed checks prove.
- Use this skill to investigate causality after the failure boundary is known
  or when unexpected runtime behaviour has not yet become a stable test.
- Use `$tracktemplate-python-writing` for an authorised Python or FCMacro fix
  and `$tracktemplate-quality-review` after validation.
- Read `reference/PERFORMANCE_SOP.md` before diagnosing a timing, CPU, memory,
  object-count or cache regression.

## Establish the failure

1. Read `reference/PROJECT_PLAN.md`, the canonical owner of the expected
   behaviour, `reference/VALIDATION.md` and `reference/TESTING_POLICY.md`.
2. Record expected and observed behaviour, the exact input or operator action,
   environment/profile, source state, cache/process state and first observable
   divergence.
3. Preserve the complete error, traceback, log or failed assertion. Keep the
   original reproduction command and required sentinel exact.
4. Determine whether the problem is reproducible, intermittent,
   environment-specific or currently only reported.
5. Use copied or disposable FCStd inputs. Snapshot state before and after a
   probe; do not diagnose by mutating the only operator document.

If a selected test failed, invoke `$tracktemplate-change-validation` before
editing retained source, tests, fixtures or expected results.

Before treating an exporter interruption report as a defect, read the
canonical [supported exporter failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model)
and classify the report as: (1) a failure inside that model; (2) an
operator-recovery case covered by the
[restart procedure](../../../reference/RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export);
or (3) a deliberately unsupported arbitrary asynchronous interruption
micro-window. Category 3 may support later architectural research but is not
automatically a current implementation defect or phase-exit blocker.

## Investigation workflow

1. **Trace the active path.** Confirm which launcher, package module, adapter,
   compatibility route and qualified runtime actually executed.
2. **Localise the divergence.** Follow values and state backward from the first
   bad observation. Compare with the last known-good observable boundary.
3. **State competing hypotheses.** For each, name the predicted observation and
   the smallest read-only or disposable probe that could disprove it.
4. **Vary one factor.** Keep inputs, runtime, cache and process boundary fixed
   except for the factor under test. Prefer instrumentation, snapshots and
   narrow function calls over retained code changes.
5. **Minimise safely.** Reduce the input or workflow while preserving the
   failure. Do not remove validation, transaction or recovery behaviour from
   the production path merely to simplify reproduction.
6. **Identify the responsible boundary.** Distinguish domain calculation,
   application state, signature/invalidation, FreeCAD lifecycle, persistence,
   presentation, exact geometry, export, dependency/profile, fixture/harness
   and operator-data causes.
7. **Test the causal claim.** A confirming probe must predict a new observation,
   not merely restate the traceback. Record disconfirming evidence and revise
   the hypothesis.
8. **Fix only when authorised.** Add a regression proof that fails for the
   diagnosed reason where practical, make the smallest repair at the classified
   boundary, rerun the original reproduction and then every affected layer.

## Boundary-specific checks

- **Standalone/domain:** exact units, frames, tolerances, input normalisation,
  deterministic ordering, stable identities and hidden mutable state.
- **Cache/reuse:** complete signatures, invalidation, change-back, process
  freshness and whether a stale result is being mistaken for a solver error.
- **FreeCAD/document:** qualified profile, imports, object/property identity,
  recompute, transactions, Undo/Redo, cleanup and save/reopen.
- **GUI/presentation:** reproduce in a real GUI when selection, visibility,
  event ordering or operator-visible state is involved; headless success is not
  a substitute.
- **Persistence/migration:** inspect read-only first; separate corrupt,
  unsupported, future and ambiguous state from migrator behaviour.
- **Export/exact geometry:** retain staging, preflight, rollback, manifests,
  source hashes and transient-object cleanup while isolating the failure.
- **Performance/resource:** compare equivalent cold/warm states and process
  boundaries; preserve correctness assertions and measurement noise.

## Investigation rules

- Do not edit B14 or accepted B15 evidence, widen tolerances, weaken assertions
  or change an oracle to support a hypothesis.
- Do not assume the most recent change caused the problem; use the diff or
  history only as evidence. History operations remain subject to
  `reference/RECOVERY_AND_BACKUP.md`.
- Do not add broad logging that exposes private paths, credentials, source data
  or large geometry payloads. Remove temporary instrumentation or keep it only
  when it has an accepted durable diagnostic purpose.
- Treat inability to reproduce as an evidence limitation. Improve observation
  or request the missing environment; do not invent a fix.
- Treat intermittent changes under a debugger as a timing clue, not proof of a
  race. Use repeated equivalent runs and lower-intrusion tracing.
- Verify third-party or runtime defect claims against current first-party
  release notes or issue evidence before recommending a dependency change.

## Report

Report:

1. expected versus observed behaviour and reproduction status;
2. exact source, runtime, input and cache/process boundary;
3. first divergence and evidence gathered;
4. hypotheses tested, including disconfirming results;
5. confirmed root cause or remaining uncertainty, with confidence;
6. responsible repair boundary and regression proof;
7. fixes made only when authorised and validation rerun; and
8. unperformed GUI, persistence, export or performance evidence.
