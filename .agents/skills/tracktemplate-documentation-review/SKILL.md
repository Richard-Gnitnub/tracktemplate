---
name: tracktemplate-documentation-review
description: Create, review, shorten or reorganise TrackTemplate Markdown documentation. Use for duplicated status, repetitive explanations, verbose prose, unclear document ownership or material recorded in the wrong canonical document.
---

# TrackTemplate documentation review

## Required preparation

1. Read [`references/document-ownership.md`](references/document-ownership.md).
2. Read [`references/writing-checklist.md`](references/writing-checklist.md).
3. Classify the document before editing it: live status, architecture, plan,
   policy, procedure, evidence, audit, historical record, contract, inventory,
   closeout or supporting guidance.
4. Identify the document's canonical responsibility and the canonical owner of
   any material that falls outside it.

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

## Editing rules

- Prefer links to canonical owners over copied explanations.
- Put conclusions, decisions and operative requirements before supporting
  detail.
- Remove padding, repetition and generic summaries without removing evidence,
  qualifications or controlled terminology.
- Preserve frozen historical evidence and append-only records. Do not rewrite
  them using later knowledge.
- Check for exact wording required by validators before changing prose.
- Avoid arbitrary word-count targets, automatic whole-repository rewrites and
  broad mechanical cleanup.
- Keep phase and exit-condition status in `reference/PROJECT_PLAN.md`, current
  evidence in `reference/current/PHASE_EVIDENCE.md`, and detailed risks and
  decisions in the JSON registers beside it.
- Report material proposed for removal when deletion could change historical,
  legal, safety, licensing or evidential meaning.

## Output

Report:

1. **Document classification and canonical responsibility.**
2. **Changes made or proposed**, with the reason for each material change.
3. **Material moved or linked**, naming its canonical owner.
4. **Material proposed for removal that needs explicit review** because it may
   affect historical, legal, safety, licensing or evidential meaning.
5. **Validation completed**, including local link checks and any
   validator-required wording reviewed.
6. **Residual uncertainty**, including evidence or authority still needed.

Do not describe planned work as completed or headless validation as GUI
acceptance.
