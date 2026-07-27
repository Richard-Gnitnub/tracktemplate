---
name: tracktemplate-change-validation
description: Select, run and report proportionate TrackTemplate validation and classify failed tests before retained fixes, distinguishing standalone, qualified FreeCAD, real-GUI, persistence, export, performance, provenance and licensing evidence.
---

# TrackTemplate change validation

## Purpose

This skill owns evidence selection and interpretation. Determine what the actual
TrackTemplate change requires, report what completed checks prove and keep
unavailable evidence visible. Do not decide whether the implementation or scope
is acceptable overall; that belongs to `$tracktemplate-quality-review`.

## Required preparation

1. Read [`references/validation-checklist.md`](references/validation-checklist.md).
2. Inspect the complete relevant diff, including connected source, tests,
   documentation, schemas, fixtures and generated interfaces.
3. Identify the affected architectural boundary, railway boundary and
   FreeCAD/host-integration boundary.
4. Read `reference/PROJECT_PLAN.md` to identify the current phase, open gates and
   owning evidence document.
5. Read `reference/VALIDATION.md` for the applicable validation layers and
   verified commands.
6. Read `reference/TESTING_POLICY.md` for testing obligations and oracle-change
   rules.
7. Read only the additional canonical documents required by the change.
8. For a proposed non-trivial behaviour change, define the regression contract
   before implementation: the observable outcome, preserved invariants,
   intended behaviour change, important rejection or failure cases, and the
   evidence that could disprove success.

## Conditional canonical reading

- Read `reference/ARCHITECTURE.md` for canonical-state, display, persistence,
  export or product-boundary changes.
- Read `reference/MODULARISATION_PLAN.md` for source-boundary, dependency or
  extraction changes.
- Read `reference/PERFORMANCE_SOP.md` before making or assessing timing,
  resource-use or optimisation claims.
- Read `reference/RECOVERY_AND_BACKUP.md` before destructive, bulk, backup,
  restore or operator-document work.
- Read `reference/TERMINOLOGY.md` when railway wording or identifiers change.
- Read `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md` for
  source data, external evidence, chair definitions, licensing, package or
  output-status changes.
- Read `reference/AGENT_WORKFLOWS.md` when agent guidance or skill files change.

## Validation rules

- Select checks according to the changed behaviour and dependency path. Do not
  run every available command merely because it exists.
- Use the verified commands and evidence definitions in
  `reference/VALIDATION.md`. Do not create a second command catalogue in this
  skill.
- At minimum, parse every changed Python or macro file and run the fastest
  focused test that proves the changed behaviour.
- Run affected regression suites and the applicable FreeCAD, GUI, persistence,
  migration, export, rollback, recovery, performance, provenance or licensing
  checks.
- Run only checks available in the present environment. State unavailable checks
  explicitly instead of simulating or inventing their results.
- Record the exact command, environment, result and required success sentinel
  for each executed check.
- A zero exit status without the required success sentinel is not evidence that
  assertions ran.
- Keep standalone Python, qualified headless FreeCAD and real-GUI evidence
  distinct. Headless evidence does not become GUI acceptance.
- Preserve comparable starting states, cache conditions, process boundaries and
  correctness assertions when assessing performance.
- Do not weaken tests, widen tolerances, change accepted oracles or remove
  failure cases merely to obtain a pass.
- When repeated focused fixes fail against the same proof, stop applying local
  patches and reassess the premise, affected boundary, baseline and proposed
  approach. Record the unresolved cause rather than suppressing the failure.
- Do not describe a copied-target fixture, local comparison path, prototype,
  headless smoke or partial workflow as supported production behaviour.
- Do not claim a phase, milestone, release, migration family, package or output
  is accepted or project-cleared. Those decisions remain with their canonical
  gates and the project owner.
- Do not change files unless the user requested implementation or validation
  fixes.

## Failed-test adjudication

When any selected check fails, begin with a read-only evidence pass:

1. preserve the exact command, environment/profile, source state, required
   sentinel, raw output and first relevant traceback or assertion;
2. identify the observable contract and its canonical authority;
3. compare with the known baseline and determine whether the failure is
   introduced, pre-existing or unresolved;
4. assign the supported primary classification defined by
   `reference/TESTING_POLICY.md`; and
5. state the correct repair boundary before editing retained source, tests,
   fixtures, expected values or environment configuration.

Repeat runs and disposable probes may gather diagnostic evidence. Do not mutate
retained code or tests while the primary classification remains unsupported.
If the user authorised fixes, make the smallest repair at the classified
boundary, rerun the original exact command, then run every additionally affected
layer.

Changing a test or oracle still requires the canonical gate in
`reference/TESTING_POLICY.md`. A test failure, an implementation preference or
the desire for a green suite is not that evidence.

## Output

Report:

1. **Change boundary:** affected files, architecture, railway behaviour and host
   integration.
2. **Selected validation:** each applicable layer and why it is required.
3. **Checks completed:** exact commands, environments, sentinels and results.
4. **Failed-test adjudication:** for each failure, the preserved evidence,
   primary classification, canonical contract and correct repair boundary.
5. **Checks not run:** the reason, remaining risk and required environment or
   evidence.
6. **Evidence interpretation:** what the completed checks prove and what they do
   not prove.
7. **Evidence status:** complete for the selected scope, incomplete, or failed.
8. **Next review boundary:** whether the complete change is ready for
   `$tracktemplate-quality-review`.

Omit failed-test adjudication when no check failed. Do not imply that an
unavailable, unperformed or narrower check passed.
