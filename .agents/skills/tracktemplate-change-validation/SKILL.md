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
4. Read `reference/PROJECT_PLAN.md` for the current phase and applicable
   exit-condition status. Read `reference/current/PHASE_EVIDENCE.md` and the
   current JSON registers when detailed evidence, risks or decisions matter.
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
- When Git recovery state or handoff is part of the change, use the
  [procedure for visible recovery state](../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state).
- Read `reference/TERMINOLOGY.md` when railway wording or identifiers change.
- Read `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md` for
  source data, external evidence, chair definitions, licensing, package or
  output-status changes.
- Read `reference/AGENT_WORKFLOWS.md` when agent guidance or skill files change.
- Read the canonical
  [Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
  when validation changes presentation for the owner, status terms, or workflow
  routing. Read the project technical terms in
  [`reference/TERMINOLOGY.md`](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).
  Evidence is different from a recommendation or owner decision.

For exporter interruption evidence, read the canonical
[failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model),
[evidence boundary](../../../reference/VALIDATION.md#supported-exporter-interruption-evidence)
and [operator recovery procedure](../../../reference/RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export)
before selecting proof.

## Validation rules

- Select checks according to the changed behaviour and dependency path. Do not
  run every available command merely because it exists.
- Use the verified commands and evidence definitions in
  `reference/VALIDATION.md`. Do not create a second command catalogue in this
  skill.
- For a standalone developer executable such as Ruff, use the canonical
  [developer-tool boundary](../../../reference/VALIDATION.md#developer-tool-boundary).
  A tool on `PATH` is not a TrackTemplate runtime dependency or a qualified
  FreeCAD dependency. If the project owner does not authorise the installation,
  do not install the tool during validation. If the project owner does not
  authorise a version change, do not change the tool version during validation.
- Follow the canonical
  [document boundary](../../../reference/VALIDATION.md#document-boundary). Do
  not edit that file merely because a test was added or run. Change it only
  when the task changes a durable validation contract that the document owns.
- At minimum, parse every changed Python or macro file and run the fastest
  focused test that proves the changed behaviour.
- Use machine controls only for Issue 9 requirements that they can validate
  accurately. Do not use a validator as proof of linguistic conformance.
- A recorded conformance review against the official Issue 9 standard is
  necessary for a linguistic conformance claim.
- For such a claim, make sure that the review reports an official source from the
  [ASD-STE100 source instructions](../../../reference/external/asd-ste100/README.md).
  Normal repository validation does not use the ignored PDF.
- When the change includes the STE lookup, use its
  [validation and review receipt route](../../../reference/external/asd-ste100/README.md#pre-check-and-review-receipt).
  Validate source identity and derived cache identity. Record that the reviewer
  examines the complete applicable requirement set. Selected lookup results and
  an empty pre-check do not show conformance.
- Run affected regression suites and the applicable FreeCAD, GUI, persistence,
  migration, export, rollback, recovery, performance, provenance or licensing
  checks.
- For a recovery or handoff workflow change, validate the stash inventory,
  unique content, and stash disposition controls. Also do the applicable
  semantic control validation. Review the preservation diff.
- For worktree retirement, use the canonical
  [retirement procedure](../../../reference/RECOVERY_AND_BACKUP.md#deliberate-worktree-retirement).
  Validate accepted-history containment, tracked cleanliness, and the complete
  ignored and local-only inventory. Validate non-overlapping classification,
  ambiguous-state rejection, required preservation, normal non-force removal,
  post-removal preservation, and local-branch order. Review the exact live
  preservation diff.
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
- When repeated fixture, harness or oracle repairs do not reduce the original
  product or exit uncertainty, stop instead of creating another local tranche
  and route the progress question to
  [`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md)
  when the owner or an active `$tracktemplate-continue` cycle has authorised
  that diagnosis.
- Do not describe a copied-target fixture, local comparison path, prototype,
  headless smoke or partial workflow as supported production behaviour.
- Treat a probe outside the supported exporter failure model as research
  evidence unless the project owner explicitly widens the contract. It is not
  automatically a blocker, but remains one when it proves deletion, overwrite,
  unsafe mutation, supported-workflow failure, unsafe retry or another retained
  invariant violation.
- Do not claim a phase, milestone, release, migration family, package or output
  is accepted or project-cleared. Those decisions remain with the structured
  current records and the project owner.
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

Changing a test or oracle still requires the canonical change control in
`reference/TESTING_POLICY.md`. A test failure, an implementation preference or
the desire for a green suite is not that evidence.

## Evidence recording boundary

Keep raw validation and failed-test evidence complete in retained logs or pull-
request evidence. That record includes the exact commands, environments,
sentinels, output, chronology, classifications and repair reruns needed to audit
the proof.

Current phase evidence has a different purpose. When the task is Level 2 or
Level 3 and its documentation lifecycle calls for an entry, provide only the
concise, decision-relevant result, decisive proof, contribution, material
limitation and unchanged authority or required decision. Do not copy the full
failed-test chronology into phase evidence unless the chronology itself changes
the evidential conclusion. Level 1 validation or maintenance does not create a
current-phase evidence entry.

## Output

For a substantial cycle, start with the profile's owner view. Put this exact
validation detail below it as proof/provenance:

1. **Change boundary:** affected files, architecture, railway behavior and host
   integration.
2. **Selected validation:** each applicable layer and why it is necessary.
3. **Checks completed:** exact commands, environments, sentinels and results.
4. **Failed-test adjudication:** for each failure, the preserved evidence,
   primary classification, canonical contract and correct repair boundary.
5. **Checks not run:** the reason, the risk that is still present, and the
   necessary environment or evidence.
6. **Evidence interpretation:** what the completed checks show and what they do
   not show.
7. **Evidence status:** complete for the selected scope, incomplete, or failed.
8. **Next review boundary:** whether the complete change is ready for
   `$tracktemplate-quality-review`.

Omit failed-test adjudication when no check failed. Do not imply that an
unavailable, unperformed or narrower check passed.
