---
name: tracktemplate-documentation-alignment
description: Reconcile TrackTemplate documentation claims with current repository authority and implementation evidence. Use when documentation may be stale, contradictory, duplicated, orphaned or inconsistent with the current project state, especially after source, structure, workflow, phase, validation or agent-guidance changes.
---

# TrackTemplate documentation alignment

## Outcome

Produce an evidence-backed drift audit and make only authorised, ownership-aware
documentation corrections. Alignment does not mean rewriting accepted
requirements to match whatever the current code happens to do.

## Responsibility boundary

- Use this skill to determine which documented claims are current, stale or in
  conflict with project authority or repository evidence.
- Use `$tracktemplate-documentation-review` while materially editing,
  shortening or reorganising the affected Markdown.
- Use `$tracktemplate-context-recovery` first when lost session context or an
  unfamiliar dirty worktree makes the task boundary uncertain.
- Use the canonical ownership map in `AGENTS.md`; do not reproduce it here or
  create a competing document index.

Default to a targeted audit of the documents and claims changed or invalidated
by the current task. Scan the complete documentation corpus only when the user
requests repository-wide alignment or bounded evidence shows broader drift.

## Authority and evidence

Read `AGENTS.md`, `reference/PROJECT_PLAN.md` and the canonical owner of each
affected subject before judging a claim.

- Treat explicit current user decisions, `AGENTS.md` and canonical reference
  documents as requirement and decision authority in that order.
- Treat source, tests, configuration, manifests, Git status and diffs as
  implementation evidence.
- Treat raw command output and accepted evidence records as validation evidence.
- Treat runtime, GUI, performance and export claims as verified only by their
  applicable evidence boundary.
- Treat frozen closeouts, contracts, inventories and baselines as dated
  evidence. Do not make them follow later project state.

When authority and implementation disagree, report the divergence. Do not
silently change the requirement, oracle, test or documentation to make the
repository appear consistent.

## Alignment workflow

1. **Bound the audit.** Name the triggering change, affected documents,
   relevant canonical owners and whether the work is targeted or
   repository-wide. Preserve unrelated working-tree changes.
2. **Inventory claims.** Use `rg --files`, `rg`, manifests and focused source or
   test inspection to verify named paths, components, commands, identifiers,
   interfaces and document links. Exclude dependencies, caches, generated
   output, operator documents and unrelated historical evidence.
3. **Classify drift.** Record each material claim with its document location,
   canonical owner, supporting evidence and one state:
   `VERIFIED`, `STALE`, `CONTRADICTORY`, `DUPLICATED`, `ORPHANED` or
   `CANNOT_VERIFY`.
4. **Report before editing.** Summarise the material findings and intended owner
   of each correction. Continue with safe in-scope fixes when authorised;
   surface any decision that would change requirements, history, rights,
   acceptance or a safety boundary.
5. **Reconcile narrowly.** Correct a fact in its canonical owner and link from
   other documents. Remove only unsupported repetition or references whose
   invalidity is proven. Preserve qualifications, controlled terminology,
   exact evidence, validator-required wording and useful historical context.
6. **Capture durable discoveries.** Record a new durable fact only when evidence
   supports it and an existing canonical document owns it. Do not create
   generic memory, atlas, plan, chronicle or session-summary files.
7. **Validate the result.** Review the complete diff, re-check every changed
   claim and link, run the repository agent-guidance validator when agent
   guidance or a skill changed, then use the normal documentation validation
   and quality-review sequence.

## Targeted checks

Select only the rows relevant to the audit.

| Claim surface | Compare against |
| --- | --- |
| Current phase, progress, gates or live risks | `reference/PROJECT_PLAN.md` and the named open-phase evidence |
| Architecture or product boundaries | The owning canonical document, current composition and focused tests |
| Paths, modules, commands or interfaces | `rg --files`, source, configuration, manifests and executable validation |
| Tests or validation status | `reference/VALIDATION.md`, `reference/TESTING_POLICY.md` and raw results |
| Agent skills and invocation | `.agents/skills/`, `AGENTS.md`, `reference/AGENT_WORKFLOWS.md` and the guidance validator |
| Railway terms or frozen identifiers | `reference/TERMINOLOGY.md` and compatibility evidence |
| Licensing, provenance or output status | The two owning reference documents and applicable manifests |

## Safety rules

- Do not delete, archive, bulk-rewrite or rename first-party documents without
  explicit scope and the controls in `reference/RECOVERY_AND_BACKUP.md`.
- Do not update live status in historical documents or turn implementation
  comments, diffs or commit messages into authority.
- Do not describe planned work as complete, headless checks as GUI evidence, or
  unaccepted changes as project state.
- Do not use a clean-up pass to weaken failure diagnostics, risk treatments,
  provenance restrictions, licensing qualifications or production boundaries.
- If a claim cannot be verified without external, GUI or operator evidence,
  retain it only with an accurate qualification or report it as
  `CANNOT_VERIFY`.

## Report

Report:

1. audit scope and controlling authorities;
2. material findings by classification, with evidence;
3. changes made and their canonical owners;
4. conflicts or proposed removals requiring an owner decision;
5. checks actually run and their results; and
6. residual `CANNOT_VERIFY` claims or evidence still required.
