---
name: tracktemplate-quality-review
description: Perform a staff-level review of new or changed TrackTemplate source and tests. Include classified failed-test repairs and an optional light-hearted code roast. Use it before a completion report or for a read-only independent review of source or tests. Also use it when a person asks for a review or a gentle code roast. Governance documents use their sole Documentation Review instead.
---

# TrackTemplate quality review

## Purpose

This skill owns implementation and bounded-scope judgement. Decide whether a
proposed or completed TrackTemplate change meets the applicable requirements
and available evidence. Do not expand its accepted bounded scope or use a
preference as evidence. Do not duplicate validation selection or execution.
Identify exact evidence gaps and leave their interpretation to
`$tracktemplate-change-validation`.

## Staff-review authority limit

Make the first review pass read-only. Inspect the raw diff, source, tests, and
validation evidence before you use the implementing agent's explanation. Do
not repair findings during that pass.

Prefer a fresh reviewer or session for non-trivial changes when one is
available. Provide only the request, applicable requirements, complete diff,
raw validation evidence, and known unperformed checks. Do not provide the
intended verdict. Do not present the implementing agent's diagnosis as fact.
If the same agent performs the review, state that it was not independent.

If the person authorised fixes, finish and report the first verdict. Then, make
a separate repair pass. Rerun the affected evidence and review the resulting
complete diff again.

This skill does not review governance-document prose at any stage. New,
updated or lifecycled governance documents use the Technical Author Lead route:
one Documentation Review, one permitted adjustment and one final deterministic
validation, then done. CI, publication, integration, a later checker or a new
review method cannot invoke this skill to reconsider their wording or meaning.

Use one of two modes:

- **Post-implementation review:** assess new or changed production code, tests,
  connected implementation evidence and non-governance documentation before
  completion.
- **Failed-test repair review:** assess the preserved raw failure and the
  primary classification from `reference/TESTING_POLICY.md`. Assess the repair
  limit and the related source, test, fixture, or environment changes.

## Required preparation

1. Read [`references/review-checklist.md`](references/review-checklist.md).
2. Examine the full relevant diff before you record conclusions. Include the
   connected changes, tests, documentation, and generated interfaces for the
   same behaviour.
3. Examine raw validation output and failed-test evidence before you read a
   completion summary or proposed diagnosis.
4. Identify the applicable architecture limit and railway limit. Do this before
   you examine implementation quality.
5. Read only the canonical project documents relevant to the change. Do not
   copy their policy into this skill or treat this skill as a second authority.

For presentation for the owner of a source or test change, read the
canonical
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
Read the project technical terms in
[`reference/TERMINOLOGY.md`](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).
Make sure that the owner view agrees with canonical records. It must keep
limitations and technical provenance. It must not make acceptance or wider
authority.

For an Issue 9 conformance claim, use the Technical Author Lead and
Documentation Review route. This quality-review skill does not examine the
governance prose, repeat that review, change its verdict or propose wording.
It can verify source or test changes that implement deterministic review-state
bindings, but that verification cannot reopen the document.

Before you review exporter interruption probes or tests, read the canonical
[supported exporter failure model](../../../reference/ARCHITECTURE.md#supported-exporter-failure-model).
Do not silently widen it during staff review. Report each contradiction between
an implementation or evidence claim and the supported exporter failure model.

For Git recovery or handoff work, read the
[procedure for visible recovery state](../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state).
Read it in the canonical owner. Examine the complete stash inventory and its
unique state. Validate the exact Git identity and stash disposition authority.
Review the preservation diff. A recovery branch or worktree is not accepted
product state.

For worktree retirement, read the
[worktree retirement procedure](../../../reference/RECOVERY_AND_BACKUP.md#worktree-retirement).
Examine accepted-history containment. Examine tracked cleanliness. Examine
evidence that no person or process uses the worktree. Examine the
local-state inventory.

For each item in the local-state inventory, examine the local-state type.
For each item, examine the canonical owner. For each item, examine the result.
Examine planned preservation. Examine the `FAIL` result for ambiguous
or uniquely owned state.

Examine removal authority. Examine `git worktree remove` without `--force`.
After removal, examine the preservation audit.
Examine the preservation diff for branches, worktrees, and the stash inventory.
The pull-request state `MERGED` and tracked cleanliness give no removal
authority. If the project owner did not give removal authority, report this
limitation.

## Review order

Review applicable-requirement compliance before implementation quality:

- **MISSING:** a requested or accepted requirement is demonstrably absent.
- **EXTRA:** an unrequested behaviour change, refactor or expansion is present.
- **CANNOT_VERIFY:** the available diff or evidence cannot settle an applicable
  requirement. Name the exact check or authority that is necessary.

Report MISSING and EXTRA findings before code-quality findings. CANNOT_VERIFY
does not imply failure, but it must remain visible and must not be treated as
acceptance.

Apply MISSING or EXTRA where appropriate when the change includes:

- Level 1 maintenance recorded as Level 2 current-phase evidence.
- A maintenance finding promoted into immediate development work.
- Chronological evidence narration that obscures the retained result.
- A proposed next bounded cycle that is unrelated to a named current exit gap.
- Repeated validation descriptions with no decision-relevant value.
- unnecessary follow-up created solely by the review without an accepted
  BLOCKED finding, applicable requirement, or risk.

## Finding disposition

Classify every actionable finding as exactly one of:

- `BLOCKER` — the present change does not meet an accepted requirement, safety
  limit, or required proof.
- `REQUIRED_BEFORE_EXIT` — the finding is demonstrably tied to an accepted
  phase exit, applicable requirement, or live risk. It does not block this
  bounded change.
- `BACKLOG` — valid maintenance or improvement that is not needed for the
  present change or named exit.
- `OPTIONAL` — a preference or possible improvement with no demonstrated
  requirement.

Recommend immediate remediation for a `BLOCKER`. Keep a
`REQUIRED_BEFORE_EXIT` finding visible for its named exit, requirement, or
risk. Outside an active `$tracktemplate-continue` cycle, repair it in the
current cycle only if it prevents the selected outcome or proof. During an
active continuation cycle, only a `BLOCKER` can return to implementation.
`REQUIRED_BEFORE_EXIT`, `BACKLOG`, and `OPTIONAL` findings do not join that
cycle. Do not make a non-blocking finding the next implementation cycle.

## Progress assessment

Report the actual task level from the change's behaviour or authority, not the
author's label. Classify its progress impact as exactly one of:
`exit-closing`, `necessary-enabling`, `neutral` or `regressive`.

State whether a current-phase evidence entry is proportionate for the actual
task level. Name the phase exit, accepted requirement, or live risk that the
change advances. Otherwise, state `none`. Identify maintenance or a Level 1
change that is incorrectly promoted into phase work.

The quality reviewer does not choose the project's next objective. Findings and
the progress assessment are read-only inputs to Chief of Staff. Use
[`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md)
when the owner requests prioritisation. Also use it when an active
`$tracktemplate-continue` cycle detects its stop conditions for repeated work.

## Optional person-morale roast

When the person explicitly requests a roast:

- Complete the factual review and verdict first. Do not let humour alter,
  soften, or replace a finding.
- End with one or two concise, good-natured lines grounded in the reviewed code
  or diff.
- Roast the code, abstraction, or naming. Do not roast the person, contributor,
  or their ability.
- Do not joke about safety, data loss, a known software problem, licence,
  provenance, or an unresolved blocking problem.
- Keep it suitable for a friendly engineering room. Do not use cruelty,
  profanity, or invented problems.

## Review principles

- Preserve necessary FreeCAD compatibility code and diagnostics. Also preserve
  transaction handling, geometry tolerances, stable identities, and legacy
  evidence. Change them only with specific evidence and authority.
- Examine apparent duplication before you remove it. The duplication can
  protect FreeCAD lifecycle behaviour, compatibility, recovery, evidence
  continuity, or performance.
- Keep verified problems and evidenced behavioural risks separate from style
  preferences and possible future improvements.
- Reject mechanical changes across the repository as a substitute for review.
  Also reject phrase blacklists and automatic “AI authenticity” scoring.
- Do not change files unless the person explicitly requested implementation or
  fixes.
- Do not accept an unsupported claim that FreeCAD, GUI, export, validation, or
  performance testing succeeded.

## Review focus

Assess the relevant change for:

- unnecessary abstraction, speculative helpers, or duplicated authoritative
  logic.
- misleading, repetitive, or stale comments.
- hidden failures, exception handling that catches too much, and weakened
  diagnostics.
- behavioural drift in geometry, topology, tolerances, ordering, persistence,
  transactions, or exporters.
- unnecessary metadata, repeated calculations, and likely performance
  regressions.
- accidental changes to a public API, stored state, or compatibility.
- tests that assert implementation shape or miss the accepted regression.
- tests that omit important failure, invalidation, rollback, or persistence
  cases.
- failed-test repairs applied to the wrong classified limit.
- test, fixture, or oracle changes that do not satisfy
  `reference/TESTING_POLICY.md`.
- weakened validation, changed evidence limits, or unsupported completion
  claims.
- unrelated formatting, refactoring, or bounded-scope expansion.

## Output

For a substantial cycle, start with the profile's owner view. Put this
staff-review proof/provenance below it:

1. **Decision:** pass, pass with findings, or blocked.
2. **Progress assessment:** the applicable task level, progress effect,
   phase-evidence proportionality, and maintenance that must not be phase work.
3. **Specification findings:** MISSING, EXTRA and CANNOT_VERIFY findings.
4. **Finding disposition:** give each actionable finding one label:
   `BLOCKER`, `REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL`.
5. **Confirmed problems:** in impact order, with exact paths or symbols and the
   evidence for each finding.
6. **Unnecessary complexity:** report it only when evidence shows that it has
   no purpose.
7. **Behaviour risks:** the architecture and railway limits for the change.
8. **Checks completed:** commands, inspections, and evidence that the reviewer
   examined.
9. **Checks still required:** name unavailable real-GUI FreeCAD, export,
   performance, provenance, licence, or compatibility evidence.
10. **Failed-test integrity:** classification, repair limit, original proof
   rerun and any test/oracle authority used.
11. **Reviewer independence:** fresh reviewer/session or disclosed same-agent
   review.
12. **Bounded scope:** whether unrelated files and behaviour changed.
13. **Morale roast:** only when the person requests it, after the factual
    review.

Omit failed-test integrity when no failed test or repair is in the bounded
scope. Do not present preferences as problems. Do not imply that an unperformed
check passed.
