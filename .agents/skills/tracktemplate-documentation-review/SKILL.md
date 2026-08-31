---
name: tracktemplate-documentation-review
description: Create, review, shorten, or reorganise TrackTemplate Markdown documentation. Use for duplicated status, repetitive explanations, verbose wording, unclear document ownership, or material in the wrong canonical document.
---

# TrackTemplate documentation review

## Required preparation

1. Read the canonical
   [Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
2. When the Issue 9 conformance scope applies, follow the
   [official-source instructions](../../../reference/external/asd-ste100/README.md).
   Use the local official PDF when it is available. Otherwise, use the official
   ASD/STEMG source when it is available. Report the official source that you
   used. Do not claim conformance if no official source is available. Review
   the full logical unit that contains the change.

   Use the [STE lookup](../../../reference/external/asd-ste100/README.md#local-retrieval-interface)
   before you read more source text. A lookup result selects source material to
   read. It does not select the applicable Issue 9 requirement set. Use the
   agent workflow to inspect the complete source.
3. Read the project technical terms in
   [`reference/TERMINOLOGY.md`](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).
4. Read [`references/document-ownership.md`](references/document-ownership.md).
5. Read [`references/writing-checklist.md`](references/writing-checklist.md).
6. Select the document class. Do this before you edit it. Use one of these
   classes:
   - live status
   - architecture
   - plan or policy
   - procedure
   - evidence or audit
   - historical record
   - specification or inventory
   - closeout
   - guidance
7. Map the document responsibility. Also map information that has a different
   canonical owner.

## Conditional canonical reading

Read only the documents relevant to the present change:

- Read `reference/PROJECT_PLAN.md` for phase and exit-condition status plus
  linked risk/decision summaries.
- Read `reference/current/PHASE_EVIDENCE.md` and the JSON registers beside it
  when current evidence, detailed risks, or decisions are part of the bounded
  scope.
- Read `reference/ARCHITECTURE.md` for architecture or canonical-state decisions.
- Read `reference/MODULARISATION_PLAN.md` for source organisation or dependency
  direction.
- Read `reference/VALIDATION.md` and `reference/TESTING_POLICY.md` for testing or
  evidence claims.
- Read `reference/PERFORMANCE_SOP.md` for timing and optimisation claims.
- Read `reference/RECOVERY_AND_BACKUP.md` for destructive-action, backup,
  checkpoint or restore guidance.
- Read `reference/TERMINOLOGY.md` for railway terminology.
- Read `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md` for
  source data, external evidence, chair definitions, licence, or
  generated-output status.
- Read `reference/QUALITY_ASSURANCE.md` for dated QA audit findings.
- Read `reference/AGENT_WORKFLOWS.md` for agent-skill structure, invocation or
  maintenance.
- Consult `reference/LEARNING_FROM_EXPERIENCE.md` only for lessons relevant to
  the present change.

## One Documentation Review

Use the [writing checklist](references/writing-checklist.md#documentation-review-for-asd-ste100-issue-9)
for the complete frozen review scope. Review it against all applicable Issue 9
requirements in the official source. This is the only linguistic conformance
review.

Return one complete verdict: `ACCEPT`, `APPROVED_WITH_EXACT_CORRECTIONS`, or
`BLOCKED`. For `APPROVED_WITH_EXACT_CORRECTIONS`, give all exact replacement
wording in this review. Identify each replacement by path, byte range, and
frozen preimage. Do not defer wording to another reviewer or a later review.
Do not run a second Documentation Review.

For `BLOCKED`, give the complete set of BLOCKED findings in this review. The
set must contain at least one finding. For each finding, give the finding
wording and exact path. Give all applicable formal Issue 9 rule identifiers. Also give
the side, bounds, and SHA-256 of the frozen logical unit. Set
`blocker_set_complete` to `true`. Do not give a `BLOCKED` verdict when the
`blockers` array is empty.

The STE lookup validates source, exact candidate, frozen review scope, receipt,
accepted state, and final-content identity. It validates exact reviewed
corrections against frozen preimages. It also derives the expected final bytes.
The implementing agent applies those corrections once. The lookup does not
examine canonical prose for conformance or change your verdict. The
deterministic pre-check is only a review aid. A remaining linguistic, semantic,
identity, or frozen-review-scope failure returns to the owner.

## Editing rules

- Use links to canonical owners instead of copied explanations.
- Put conclusions, decisions, and applicable requirements before the evidence
  detail.
- Use ASD-STE100 Issue 9 in the conformance scope. TrackTemplate uses UK
  English in this scope. Do not change the other Issue 9 requirements.
- Use the approved project technical terms. Keep facts, evidence, limitations,
  recommendations, and owner decisions distinct.
- Do not claim Issue 9 conformance from a public summary or model knowledge. An
  automatic validator is also not sufficient.
- Use the pre-check and STE lookup during the review. Review the complete
  applicable requirement set. Include each applicable requirement that a
  lookup result does not contain.
- Remove repeated or unnecessary wording. Keep evidence, qualifications, and
  controlled terms.
- Preserve frozen historical evidence and append-only records. Do not rewrite
  them with later knowledge.
- Before you change canonical prose, identify the exact wording that a validator
  uses.
- Do not use an arbitrary word-count target.
- Do not use an automatic rewrite of the full repository.
- Keep each item in its canonical owner.
  - phase and exit-condition status in `reference/PROJECT_PLAN.md`
  - current evidence in `reference/current/PHASE_EVIDENCE.md`
  - risk and decision detail in the JSON registers beside it
- Report information proposed for removal if deletion could change history,
  law, safety, licence, or the controlled meaning of evidence.

## Decision-relevant current phase evidence

When you review `reference/current/PHASE_EVIDENCE.md`, keep the record useful
for an exit or owner decision. Do not make it a laboratory diary. A Level 2
entry should normally state the following information.

- bounded scope and retained result.
- decisive evidence.
- phase or risk contribution.
- material limitation.
- unchanged authority or the decision that is still necessary.
- a link to detailed logs or performance reports when applicable.

Do not reproduce:

- every failed development attempt.
- repeated command catalogues.
- repeated full validator totals when one short pipeline result is sufficient.
- unchanged exclusions already owned by the phase opening.
- Level 1 maintenance history.

Preserve a failed-test classification in the phase record only when it changes
confidence, auditability, or the decision. Retain detailed raw history in logs
and pull-request evidence. A Level 1 maintenance task must not nominate itself
as the next phase-development cycle.

## Output

For a substantial cycle, start with the profile's owner view. Put this
technical provenance below it:

1. **Document class and canonical responsibility.**
2. **Changes made or proposed**, with the reason for each change.
3. **Information moved or linked**, naming its canonical owner.
4. **Information proposed for removal.** Record why an explicit review is
   necessary. List each possible effect on history, law, safety, licences, or
   evidence.
5. **Validation completed.** Include local link checks and validator output that
   the review examined.
6. **Issue 9 conformance.** Give the reviewed logical units, official standard,
   result, approved technical terms, and limitations.
7. **Residual uncertainty.** Give the evidence or authority that is still
   necessary.

Do not describe planned work as completed or headless validation as GUI
acceptance.
