---
name: tracktemplate-change-validation
description: Select proportionate TrackTemplate validation. Do the validation. Report its results. Before repairs that the project keeps, classify failed tests. Distinguish standalone, qualified FreeCAD, real-GUI, persistence, export, performance, provenance, and licensing evidence.
---

# TrackTemplate change validation

## Purpose

This skill owns evidence selection and interpretation. Find the evidence
necessary for the change. Report what completed checks prove. Report
unavailable evidence.

Do not decide whether to accept the complete implementation or scope.
For source and tests, `$tracktemplate-quality-review` owns that assessment.
For governance documents, final deterministic validation with a PASS result completes the
finite Technical Author Lead procedure. It does not send the prose to another
reviewer.

## Necessary preparation

1. Read [`references/validation-checklist.md`](references/validation-checklist.md).
2. Examine the complete related diff. Include connected source, tests,
   documentation, schemas, fixtures, and generated interfaces.
3. Identify affected architecture, railway, and FreeCAD/host integration
   boundaries.
4. Read `reference/PROJECT_PLAN.md` for current phase and phase-exit status.
   For detailed evidence, risks, or decisions, read
   `reference/current/PHASE_EVIDENCE.md` and its current JSON registers.
5. Read `reference/VALIDATION.md` for applicable validation layers and verified
   commands.
6. Read `reference/TESTING_POLICY.md` for test requirements and rules for
   changes to oracles.
7. Read only additional canonical documents necessary for the change.
8. Before a non-trivial behaviour change, define the regression contract.
   Include the contract items listed below.

The regression contract includes these items:

- Observable result
- Invariants that the change preserves
- Intended behaviour change
- Important rejection and failure cases
- Evidence that can disprove success.

## Conditional canonical reading

For the changes below, read the specified owner:

- For canonical state, display, persistence, export, or product boundaries,
  read `reference/ARCHITECTURE.md`.
- For source boundaries, dependencies, or extraction, read
  `reference/MODULARISATION_PLAN.md`.
- Before claims about timing, resource use, or improvements to performance,
  read `reference/PERFORMANCE_SOP.md`.
- Before destructive, bulk, backup, restore, or operator-document work, read
  `reference/RECOVERY_AND_BACKUP.md`.
- For Git recovery state or handoff, use the
  [procedure for visible recovery state](../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state).
- For railway wording or identifiers, read `reference/TERMINOLOGY.md`.
- For source data, external evidence, chair definitions, licences, packages,
  or output status, read `reference/LICENSING_BOUNDARIES.md` and
  `reference/PROVENANCE.md`.
- For agent guidance or skill files, read `reference/AGENT_WORKFLOWS.md`.

If validation changes the owner presentation, status terms, or routing, read
the canonical
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
Read the project technical terms in
[`reference/TERMINOLOGY.md`](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).
Evidence is different from a recommendation or owner decision.

Before evidence selection for exporter interruption, read these owners:

- Canonical
  [failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model)
- [Evidence boundary](../../../reference/VALIDATION.md#supported-exporter-interruption-evidence)
- [Operator recovery procedure](../../../reference/RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export).

## Validation rules

Before repository validation, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage validation`

For the necessary Ruff check, add `--run-ruff`. If the development-toolchain
preflight does not give a PASS result, stop before validation.

Before STE source or extraction validation, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage documentation`

Before a headless check in qualified FreeCAD, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`

Before a real-GUI bridge check, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`

Select checks from the changed behaviour and dependency path. Do not use every
available command only because it exists. Use verified commands and evidence
definitions in `reference/VALIDATION.md`. Do not make another command
catalogue here.

For Ruff and other development tools, use the canonical
[development-toolchain preflight](../../../reference/VALIDATION.md#developer-tool-boundary).
During validation, do not install or change a tool. After its
development-toolchain preflight gives `FAIL`, do not continue a necessary check.

Use the canonical
[document boundary](../../../reference/VALIDATION.md#document-boundary).
Do not edit that file only because a test was added or done. Change it only
for a change to its durable validation contract.

At minimum, parse every changed Python or macro file. Do the fastest test for the affected boundary that proves the changed behaviour.

Use machine controls only for Issue 9 requirements that they can validate
accurately. Do not use a validator as proof of linguistic conformance. Such
a claim needs a recorded conformance review against the official Issue 9
standard. For the claim, make sure that the review identifies an official source
from the [source instructions](../../../reference/external/asd-ste100/README.md).
Usual repository validation does not use the ignored PDF.

For STE lookup changes, use the
[validation and review receipt route](../../../reference/external/asd-ste100/README.md#pre-check-and-review-receipt).
Validate source identity and derived cache identity. Record the reviewer's
examination of the complete applicable requirement set. Selected lookup
results and an empty pre-check do not show conformance.

Do affected regression suites and applicable checks for these subjects:

- FreeCAD and GUI
- Persistence and migration
- Export and rollback
- Recovery and performance
- Provenance and licensing.

For a recovery or handoff change, validate stash inventory, unique content,
and stash disposition controls. Do the applicable semantic control
validation. Review the preservation diff.

After necessary development-toolchain preflights give PASS results, do only applicable
checks. Report each unavailable optional check explicitly. Do every
necessary check. For each executed check, record the exact command,
environment, result, and necessary success sentinel.

A zero exit status without the necessary success sentinel does not prove that
the check executed its assertions. Keep standalone Python evidence, headless
evidence from qualified FreeCAD, and real-GUI evidence separate. Headless evidence does not give GUI acceptance.

For performance assessment, preserve comparable starting states, caches,
process boundaries, and correctness assertions. Do not weaken tests, widen
tolerances, change accepted oracles, or remove failure cases only to get
a pass.

If repeated repairs at the affected boundary give FAIL results for the same proof, stop local patches. Reassess
the premise, affected boundary, baseline, and proposed approach. Record the
unresolved cause. Do not suppress the failure.

If repeated fixture, harness, or oracle repairs do not reduce the original
product or exit uncertainty, stop. Do not make another local work item.
If the owner or an active `$tracktemplate-continue` cycle authorised diagnosis,
use [`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md).
Give it the progress question.

Do not claim supported production behaviour from any of these items:

- A fixture with a copied target
- A local comparison path or prototype
- A headless smoke check
- A partial workflow.

Unless the owner explicitly widens the exporter failure model, report probes
outside it as research evidence. Such a probe is not automatically a blocker.
If it proves any violation of an invariant that the project keeps, it stays a blocker.
Such violations include these cases:

- Deletion or overwrite
- Unsafe mutation
- Failure in a supported workflow
- Unsafe retry.

Do not claim acceptance or project clearance for a phase, milestone, release,
migration family, package, or output. Those decisions stay with structured
current records and the project owner.

Unless the user requested implementation or validation fixes, do not change
files.

### Validation for worktree retirement

For worktree retirement, use the
[worktree retirement procedure](../../../reference/RECOVERY_AND_BACKUP.md#worktree-retirement).
Validate accepted-history containment. Validate tracked cleanliness. Validate
the local-state inventory. Make sure that each item has one local-state type.
Validate planned preservation. Make sure that the retirement audit returns `FAIL`
for ambiguous or uniquely owned state.

Validate `git worktree remove` without `--force`. Before Git removes the local
branch, make sure that Git removed the worktree. After removal, examine the
preservation audit. After removal, examine the preservation diff.

## Failed-test adjudication

If a selected check gives a FAIL result, start with a read-only evidence pass:

1. Preserve the exact evidence listed below.
2. Identify the observable contract and its canonical authority.
3. Compare the failure with the known baseline. Find whether it is
   introduced, pre-existing, or unresolved.
4. Use the supported primary classification from
   `reference/TESTING_POLICY.md`.
5. Before edits that the project keeps, record the correct repair boundary. This applies to
   source, tests, fixtures, expected values, and environment configuration.

The preserved evidence includes these items:

- Exact command and environment/profile
- Source state and necessary sentinel
- Raw output
- First related traceback or assertion.

Additional executions and disposable probes can collect diagnostic evidence. While the
primary classification lacks support, do not mutate code or tests that the project keeps.
If the user authorised fixes, make the smallest repair at the classified
boundary. Use the original exact command again. Then do the checks for each
additionally affected layer.

A test or oracle change still needs the change control in
`reference/TESTING_POLICY.md`. A test failure or implementation preference
does not supply that evidence. A desired successful suite does not supply it.

## Evidence recording boundary

Keep raw validation and failed-test evidence complete in logs that the project keeps or
pull-request evidence. Include exact commands, environments, sentinels, output,
chronology, classifications, and repeated checks after repairs. These records
must make an audit of the proof possible.

Current phase evidence serves a different purpose. For Level 2 or Level 3
work, an entry can be necessary in the documentation lifecycle. In that case, record
only these items:

- Concise result needed for the decision
- Decisive proof and contribution
- Material limitation
- Unchanged authority or necessary decision.

Only if chronology changes the evidence conclusion, include the full failed-test
chronology in phase evidence. Level 1 validation or maintenance does not make
a current-phase evidence entry.

## Output

For a substantial cycle, start with the profile's owner view. Put this
validation detail below it as proof/provenance:

1. **Change boundary:** Affected files, architecture, railway behaviour, and
   host integration
2. **Selected validation:** Applicable layers and the reason for each
3. **Checks completed:** Exact commands, environments, sentinels, and results
4. **Failed-test adjudication:** Preserved evidence, primary classification,
   canonical contract, and correct repair boundary for each failure
5. **Checks not done:** Reason, remaining risk, and necessary environment or
   evidence
6. **Evidence interpretation:** What completed checks show and what they do
   not show
7. **Evidence status:** Complete for the selected scope, incomplete, or
   failed
8. **Next boundary:** The applicable result given below.

For source and tests, report readiness for `$tracktemplate-quality-review`.
For governance documents, report whether final validation completed the cycle
or stopped for the owner.

If no check gave a FAIL result, do not include failed-test adjudication.
Do not imply that an unavailable, unperformed, or narrower check gave a PASS result.
