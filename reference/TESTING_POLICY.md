# Testing Policy

Status: normative project policy for new code, fixes, refactors, migrations, and
behaviour changes.

## Purpose

Tests are executable project requirements. They protect accepted railway,
document, editing, persistence, and production behaviour while the monolithic
macro is characterised and replaced.

[VALIDATION.md](VALIDATION.md) defines the validation layers, commands, and
change matrix. This policy defines when tests are required and when an existing
test oracle may be changed.

## Core rules

1. Every non-trivial new or changed behaviour must receive proportionate
   automated test evidence in the same change.
2. A defect fix starts with a test that reproduces the defect where practical.
   The test must fail for the right reason before the fix and pass afterwards.
3. A refactor or extraction starts with characterisation coverage for the
   behaviour being moved. Mechanical movement, cleanup, optimisation, and
   behaviour changes remain separate reviewable steps.
4. An implementation normally changes to satisfy an accepted test. A test is
   not weakened, deleted, skipped, or rewritten merely to make new code pass.
5. Tests assert observable results and invariants, not incidental line-by-line
   implementation. One test may legitimately cover several collaborating
   functions through a stable public boundary.
6. A passing smoke test is not a substitute for result validation. Important
   tests assert values, identities, ordering, object state, findings, rollback,
   or output fingerprints as applicable.

## Function-level expectation

A strict one-test-file or one-test-case per function rule would create brittle
bloat. Use the narrowest stable boundary that proves the behaviour:

| Function type | Expected evidence |
| --- | --- |
| Pure domain or calculation function | Direct unit tests for representative, boundary, and invalid inputs |
| Railway geometry/topology decision | Direct analytical tests for invariants, tolerances, ordering, and failure cases |
| Cache or signature function | Initial calculation, unchanged reuse, relevant-input invalidation, unrelated-input stability, and change-back |
| Persistence or migration function | Create/save/reopen, supported legacy input, deterministic identity, and unsupported-version failure |
| FreeCAD adapter or transaction | Integration test through its public operation, including object/property state, recompute, rollback, and cleanup |
| GUI callback or panel orchestration | Core logic tested below the GUI plus a headless/real-GUI workflow test for wiring and operator-visible state |
| Export function | Deterministic artifact/manifest comparison, units, validity, overwrite handling, rollback, and cleanup |
| Trivial delegate or declarative mapping | May be covered transitively when a stable caller test exercises it and no independent rule is hidden inside it |

If practical automation is not yet available, record the missing test, reason,
risk, manual evidence, and the phase or change that must close the gap. An
unrecorded manual check is not lasting coverage.

## Changing an existing test

An existing test may change only when at least one of these is demonstrated:

- the test's expected value or fixture is factually wrong;
- the accepted product requirement or invariant has changed with user approval;
- a supported dependency/API changed and the compatibility decision is recorded;
- the test is nondeterministic, order-dependent, or otherwise does not test what
  it claims; or
- a stronger replacement covers the same regression and the removed test adds
  no distinct protection.

The change must explain the evidence and preserve the old regression case when
it remains valid. Correcting a test oracle should preferably be a distinct
reviewable patch; if it accompanies product code, the reason must be explicit in
the diff and commit message.

The following are not acceptable reasons:

- the new implementation fails the test;
- the expected value is inconvenient to reproduce;
- a wider tolerance, weaker assertion, or removed invalid-input case makes the
  suite green; or
- a slow test is silently skipped instead of being classified and scheduled.

## Test design and maintenance

- Keep tests deterministic and independent. Do not depend on UI row order,
  uncontrolled object names, wall-clock timing, network access, personal paths,
  or an everyday FreeCAD profile.
- Use explicit units, coordinate frames, tolerances, stable identities, and
  canonical ordering in fixtures and assertions.
- Prefer small generated fixtures and semantic fingerprints to opaque binary
  snapshots. Retain binary fixtures only where file-format behaviour itself is
  under test and provenance permits it.
- Separate fast analytical/contract checks from FreeCAD headless, real-GUI, and
  performance suites. Mark the required layer in the validation documentation;
  do not omit a slow layer when the changed scope requires it.
- Performance tests preserve correctness assertions and comparable recipes.
  Do not turn current slow timings into permanent pass thresholds before a
  numerical budget is accepted.
- A flaky test is a defect. Diagnose and repair its source; quarantine requires
  a documented owner, risk, and removal condition.
- Line coverage may identify blind spots, but no arbitrary global percentage is
  a release gate while the legacy monolith is still being inventoried. Critical
  workflow and invariant coverage takes priority over a headline percentage.

## Required evidence by change

Before a change is complete:

1. parse or compile every changed source file;
2. run the fastest focused test that proves the new or changed behaviour;
3. run all existing regression suites affected by the dependency path;
4. run applicable FreeCAD headless, GUI, persistence, export, rollback, and
   performance checks from [VALIDATION.md](VALIDATION.md);
5. confirm tests were not weakened solely to obtain a pass;
6. record any unrun or unavailable check and the risk it leaves; and
7. keep test code, fixtures, and validation documentation in the same commit as
   the behaviour they protect unless an earlier test-only commit is clearer.

## Review questions

- What accepted behaviour or defect does each new test protect?
- Would the test fail for a plausible incorrect implementation?
- Are boundary, invalid, reuse/invalidation, rollback, and persistence cases
  present where relevant?
- Is the assertion tied to a stable contract rather than private structure?
- If a prior test changed, is the old oracle demonstrably wrong or the changed
  requirement explicitly accepted?
- Are all remaining coverage gaps visible and owned?
- Does retained code introduce another implementation of an existing railway
  or application concept? If temporarily necessary, is its owner and
  retirement gate explicit?
- Is each new shared abstraction supported by a stated invariant and direct
  tests at its narrow public boundary, rather than only by similar source text?
- Where domain or layer boundaries changed, did the applicable standalone-
  import, forbidden-dependency and circular-import guards run, or is their
  not-yet-implemented risk recorded?
- Was every disposable exploratory probe removed or deliberately promoted to
  the retained-code standards in
  [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md)?
