---
name: tracktemplate-documentation-review
description: Create, review, shorten or reorganise TrackTemplate Markdown documentation. Use for duplicated status, repetitive explanations, verbose prose, unclear document ownership or material recorded in the wrong canonical document.
---

# TrackTemplate documentation review

## Required preparation

1. Read the canonical
   [Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
2. When the Issue 9 scope applies, follow the
   [official-source instructions](../../../reference/external/asd-ste100/README.md).
   Use the local official PDF when it is available. Otherwise, use the official
   ASD/STEMG source when it is available. Report the official source that you
   used. If no official source is available, do not claim conformance.
   Review the full logical unit that contains the change.

   Use the [STE lookup](../../../reference/external/asd-ste100/README.md#local-retrieval-interface)
   before you read more source text. A lookup result selects source material to
   read. It does not select the Issue 9 requirement set. Use the agent workflow
   for a complete-source inspection.
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
   - contract or inventory
   - closeout
   - guidance
7. Map the document responsibility. Also map information that has a different
   canonical owner.

## Conditional canonical reading

Read only the documents relevant to the present change:

- Read `reference/PROJECT_PLAN.md` for phase and exit-condition status plus
  linked risk/decision summaries.
- Read `reference/current/PHASE_EVIDENCE.md` and the JSON registers beside it
  when current evidence, detailed risks or decisions are in scope.
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
  source data, external evidence, chair definitions, licensing or
  generated-output status.
- Read `reference/QUALITY_ASSURANCE.md` for dated QA audit findings.
- Read `reference/AGENT_WORKFLOWS.md` for agent-skill structure, invocation or
  maintenance.
- Consult `reference/LEARNING_FROM_EXPERIENCE.md` only for lessons relevant to
  the present change.

## Author-side assurance for ASD-STE100 Issue 9

For each logical unit with a material edit, use the
[writing checklist](references/writing-checklist.md#author-side-assurance-for-asd-ste100-issue-9).
The author examines all applicable Issue 9 requirements. The author records
findings and their dispositions in a temporary author-review worklist.
The worklist also records each logical unit that the author reviewed. It records
the SHA-256 for each logical unit.

After the last wording change, review each logical unit in full. Resolve
all findings. Resolve all unresolved terminology. Then, validate the worklist
with `tools/ste100_lookup.py author-assurance`. Before the author freezes the
exact candidate, get a read-only challenge from a different documentation
reviewer.

The STE lookup validates the source identity, exact candidate, conformance
scope, and SHA-256 values. It does not examine prose for conformance.
The deterministic pre-check also does not give a result from a conformance review. The
author completes the conformance review. The read-only challenge has no
acceptance.

## Editing rules

- Use links to canonical owners instead of copied explanations.
- Put conclusions, decisions and operative requirements before the detail that
  gives the evidence.
- Use ASD-STE100 Issue 9 in the profile scope. Use the TrackTemplate UK English
  spelling directive in this scope. Do not change other Issue 9 requirements.
- Use the approved project technical terms. Keep facts, evidence, limitations,
  recommendations, and owner decisions distinct.
- Do not claim Issue 9 conformance from a public summary, model knowledge, or
  an automatic validator.
- Use the pre-check and STE lookup during the review. Review the complete
  applicable requirement set. Include each applicable requirement that a
  lookup result does not contain.
- Remove repeated or unnecessary text. Keep evidence, qualifications, and
  controlled terms.
- Preserve frozen historical evidence and append-only records. Do not rewrite
  them with later knowledge.
- Before you change prose, make sure that you know the exact wording that a
  validator uses.
- Do not use an arbitrary word-count target.
- Do not use an automatic rewrite of the full repository.
- Keep each item in its canonical owner:
  - phase and exit-condition status in `reference/PROJECT_PLAN.md`
  - current evidence in `reference/current/PHASE_EVIDENCE.md`
  - risk and decision detail in the JSON registers beside it
- Report information proposed for removal when deletion could change historical,
  legal, safety, licensing or evidential meaning.

## Decision-relevant current phase evidence

When reviewing `reference/current/PHASE_EVIDENCE.md`, keep the record useful for
an exit or owner decision rather than turning it into a laboratory diary. A
Level 2 entry should normally state:

- scope and retained result;
- decisive evidence;
- phase or risk contribution;
- material limitation;
- authority unchanged or the decision still required; and
- a link to detailed logs or benchmark reports where applicable.

Do not reproduce:

- every failed development attempt;
- repeated command catalogues;
- repeated full validator totals when one concise pipeline result is enough;
- unchanged exclusions already owned by the phase opening; or
- Level 1 maintenance history.

Preserve a failed-test classification in the phase record only when it
materially changes confidence, auditability or the decision. Retain detailed
raw history in logs and pull-request evidence. A Level 1 maintenance task must
not nominate itself as the next phase-development tranche.

## Output

For a substantial cycle, start with the profile's owner view. Put this
technical provenance below it:

1. **Document class and canonical responsibility.**
2. **Changes made or proposed**, with the reason for each change.
3. **Information moved or linked**, naming its canonical owner.
4. **Information proposed for removal.** Record why an explicit review is
   necessary. List each possible effect on history, law, safety, licenses, or
   evidence.
5. **Validation completed.** Include local link checks and validator text that
   the review examined.
6. **Issue 9 conformance:** reviewed logical units, official
   standard, result, approved technical terms, and limitations.
7. **Residual uncertainty:** evidence or authority that is still necessary.

Do not describe planned work as completed or headless validation as GUI
acceptance.
