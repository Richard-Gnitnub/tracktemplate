---
name: tracktemplate-quality-review
description: Perform a staff-level review of new or changed TrackTemplate source, tests and documentation, including classified failed-test repairs and an optional light-hearted code roast. Use before reporting completion, when a read-only independent review is requested, or when the user asks to review and gently roast the code.
---

# TrackTemplate quality review

## Purpose

This skill owns implementation and scope judgement. Decide whether a proposed or
completed TrackTemplate change is acceptable against requirements and available
evidence, without expanding its accepted scope or substituting preference for
evidence. Do not duplicate validation selection or execution; identify exact
evidence gaps and leave their interpretation to
`$tracktemplate-change-validation`.

## Staff-review boundary

Make the first review pass read-only. Inspect the raw diff, source, tests and
validation artifacts before relying on the implementing agent's explanation.
Do not repair findings during that pass.

Prefer a fresh reviewer or session for non-trivial changes when available.
Provide only the request, canonical requirements, complete diff, raw validation
evidence and known unperformed checks. Do not provide the intended verdict or
the implementing agent's diagnosis as fact. When the same agent performs the
review, disclose that the review was not independent.

If the user authorised fixes, finish and report the first verdict, then make a
separate remediation pass. Rerun affected evidence and review the resulting
complete diff again.

Use one of two modes:

- **Post-implementation review:** assess new or changed production code, tests,
  documentation and evidence before completion.
- **Failed-test repair review:** assess the preserved raw failure, the primary
  classification from `reference/TESTING_POLICY.md`, the chosen repair boundary
  and the source, test, fixture or environment changes made in response.

## Required preparation

1. Read [`references/review-checklist.md`](references/review-checklist.md).
2. Inspect the complete relevant diff before reaching conclusions. Include
   connected changes, tests, documentation and generated interfaces that affect
   the same behaviour.
3. Inspect raw validation output and failed-test evidence before reading a
   completion summary or proposed diagnosis.
4. Identify the affected architectural boundary and railway boundary before
   assessing implementation quality.
5. Read only the canonical project documents relevant to the change. Do not
   copy their policy into this skill or treat this skill as a second authority.

## Review order

Review requirement compliance before implementation quality:

- **MISSING:** a requested or accepted requirement is demonstrably absent.
- **EXTRA:** an unrequested behaviour change, refactor or expansion is present.
- **CANNOT_VERIFY:** the available diff or evidence cannot settle a requirement;
  name the exact check or authority required.

Report MISSING and EXTRA findings before code-quality findings. CANNOT_VERIFY
does not imply failure, but it must remain visible and must not be treated as
acceptance.

Apply MISSING or EXTRA where appropriate when the change includes:

- Level 1 maintenance recorded as Level 2 current-phase evidence;
- a maintenance finding promoted into immediate development work;
- chronological evidence narration that obscures the retained result;
- a proposed next tranche unrelated to a named current exit gap;
- repeated validation descriptions with no decision-relevant value; or
- unnecessary follow-up created solely by the review without an accepted
  blocker, requirement or risk.

## Finding disposition

Classify every actionable finding as exactly one of:

- `BLOCKER` — the present change cannot be retained against an accepted
  requirement, safety boundary or required proof;
- `REQUIRED_BEFORE_EXIT` — the finding is demonstrably tied to an accepted
  phase exit, requirement or live risk but does not block this bounded change;
- `BACKLOG` — valid maintenance or improvement that is not needed for the
  present change or named exit; or
- `OPTIONAL` — a preference or possible improvement with no demonstrated
  requirement.

Recommend immediate remediation for a `BLOCKER`. Keep a
`REQUIRED_BEFORE_EXIT` finding visible for its named exit, requirement or risk;
outside an active `$tracktemplate-continue` cycle, repair it in the current
cycle only when it directly prevents the selected outcome or proof. During an
active continuation cycle, only a `BLOCKER` may return to implementation;
`REQUIRED_BEFORE_EXIT`, `BACKLOG` and `OPTIONAL` findings do not join that
cycle. Do not turn non-blocking findings into the next implementation tranche.

## Progress assessment

Report the actual task level from the change's behaviour or authority, not the
author's label. Classify its progress impact as exactly one of:
`exit-closing`, `necessary-enabling`, `neutral` or `regressive`.

State whether any current-phase evidence entry is proportionate and appropriate
under the actual task level. Name the phase exit, accepted requirement or live
risk actually advanced, or state `none`. Flag when a maintenance finding or
Level 1 change is being promoted incorrectly into phase work.

The quality reviewer does not choose the project's next objective. Findings and
the progress assessment are read-only inputs to
[`$tracktemplate-chief-of-staff`](../tracktemplate-chief-of-staff/SKILL.md)
when the owner requests prioritisation or an active `$tracktemplate-continue`
cycle detects its loop conditions.

## Optional operator-morale roast

When the user explicitly requests a roast:

- Complete the factual review and verdict first; do not let humour alter,
  soften or replace a finding.
- End with one or two concise, good-natured lines grounded in the reviewed code
  or diff.
- Roast the code, abstraction or naming—not the operator, contributor or their
  ability.
- Do not joke about safety, data loss, security, licensing, provenance or an
  unresolved blocking defect.
- Keep it suitable for a friendly engineering room: no cruelty, profanity or
  invented defects.

## Review principles

- Preserve necessary FreeCAD compatibility code, diagnostics, transaction handling, geometry tolerances, stable identities and legacy evidence unless the change has specific evidence and authority to alter them.
- Check apparent duplication before removing it. It may protect FreeCAD lifecycle behaviour, compatibility, recovery, evidence continuity or performance.
- Distinguish verified defects and evidenced behavioural risks from stylistic preferences or possible future improvements.
- Reject broad mechanical cleanup, automatic “AI authenticity” scoring, phrase blacklists and repository-wide rewriting as substitutes for review.
- Avoid changing files unless the user explicitly requested implementation or fixes.
- Do not accept unsupported claims that FreeCAD, GUI, export, validation or performance testing succeeded.

## Review focus

Assess the relevant change for:

- unnecessary abstraction, speculative helpers or duplicated authoritative logic;
- misleading, repetitive or stale comments;
- hidden failures, broad exception handling and weakened diagnostics;
- behavioural drift in geometry, topology, tolerances, ordering, persistence, transactions or exporters;
- unnecessary metadata, repeated calculations and likely performance regressions;
- accidental public API, stored-state or compatibility changes;
- tests that assert implementation shape, miss the accepted regression or omit
  important failure, invalidation, rollback or persistence cases;
- failed-test repairs applied to the wrong classified boundary;
- test, fixture or oracle changes that do not satisfy
  `reference/TESTING_POLICY.md`;
- weakened validation, changed evidence boundaries or unsupported completion claims;
- unrelated formatting, refactoring or scope expansion.

## Output

Report:

1. **Decision:** pass, pass with findings, or blocked.
2. **Progress assessment:** actual task level, progress impact, phase-evidence
   proportionality and any maintenance incorrectly promoted into phase work.
3. **Specification findings:** MISSING, EXTRA and CANNOT_VERIFY findings.
4. **Finding disposition:** every actionable finding labelled `BLOCKER`,
   `REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL`.
5. **Confirmed defects:** ordered by impact, with exact paths or symbols and the
   evidence supporting each finding.
6. **Unnecessary complexity:** only where its lack of purpose has been established.
7. **Behavioural risks:** including the affected architectural and railway boundaries.
8. **Checks completed:** commands, inspections and evidence actually reviewed.
9. **Checks still required:** especially real-GUI FreeCAD, export, performance,
   provenance, licensing or compatibility evidence that was not available.
10. **Failed-test integrity:** classification, repair boundary, original proof
   rerun and any test/oracle authority used.
11. **Reviewer independence:** fresh reviewer/session or disclosed same-agent
   review.
12. **Scope:** whether unrelated files and behaviour remained unchanged.
13. **Morale roast:** only when explicitly requested, after the factual review.

Omit failed-test integrity when no failed test or repair is in scope. Do not
present preferences as defects, and do not imply that an unperformed check
passed.
