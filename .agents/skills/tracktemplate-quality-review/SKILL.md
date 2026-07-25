---
name: tracktemplate-quality-review
description: Review TrackTemplate code or documentation changes before completion. Use for maintainability, simplification, anti-slop, documentation cleanup, refactor review, or final quality checks. Detect unnecessary complexity, duplicated policy, speculative abstractions, broad rewrites, misleading comments, weak validation, changed oracles without evidence, and unsupported completion claims. Do not use as an automatic formatter, legal review, railway acceptance, or substitute for FreeCAD validation.
---

# TrackTemplate Quality Review

## Goal

Review the proposed change without changing its accepted scope. Prefer a small,
clear and evidenced implementation, while preserving complexity that exists for
FreeCAD lifecycle behaviour, railway correctness, compatibility, recovery,
provenance or accepted legacy parity.

## Before Reviewing

1. Read the root `AGENTS.md`.
2. Read `reference/PROJECT_PLAN.md` for the current phase and open gates.
3. Read the canonical document that owns the changed subject.
4. Inspect the complete diff. When no diff exists, identify the exact files and
   requested scope before judging them.
5. Read `references/review-checklist.md` and apply only the relevant sections.

Do not begin by rewriting code or documentation. Review first, identify evidence
and distinguish necessary complexity from avoidable complexity.

## Review Order

### 1. Scope and Authority

- Confirm the target version, module, document, and phase authority.
- Flag unrelated edits, speculative future features and silent scope expansion.
- Check that live status, accepted history and canonical policy remain in their
  owning documents.

### 2. Behaviour and Railway Integrity

- Identify any change to geometry, units, frames, tolerances, topology, timbering,
  chairs, stable identities, ordering, persistence, transactions, visibility,
  cache invalidation or export.
- Require evidence for every changed invariant.
- Treat B14 defects and comparison evidence as evidence, not automatic successor
  requirements.

###3. Necessary versus avoidable complexity

Flag:

- Wrappers or abstractions with no clear shared invariant;
- Duplicated logic or policy;
- Parallel implementations without an owner and retirement gate;
- Defensive branches that cannot occur under the accepted contract;
- Broad exception handling that hides failure;
- Unused settings, dead code and speculative extension points;
- Repeated expensive work that can be safely reused;
- Whole-file formatting or mechanical rewrites unrelated to the task.

Do not remove something merely because it looks repetitive. First check whether
it protects FreeCAD recomputation, document lifecycle, Qt compatibility,
rollback, persistence, output determinism, legacy evidence or provenance.

### 4. Code and Documentation Quality

- Prefer names that express railway or application meaning.
- Flag comments that merely narrate the next line, claim unsupported success or
  obscure an unresolved limitation.
- Preserve comments that explain non-obvious host behaviour, geometry reasoning,
  evidence boundaries or compatibility constraints.
- In documentation, give each fact one owner and link to it instead of copying
  it. Flag duplicated command catalogues, repository maps and live status.
- Do not use generic phrase blacklists or authenticity scores as evidence of
  quality.

###5. Validation and claims

- Select checks from `reference/VALIDATION.md` and
  `reference/TESTING_POLICY.md`.
- Confirm that tests validate the intended behaviour rather than merely the new
  implementation shape.
- Flag tests or frozen oracles changed only to restore a pass.
- Distinguish standalone, headless FreeCAD, real-GUI, export and performance
  evidence.
- Reject claims such as “fixed”, “production-ready”, “project-cleared” or
  “validated” when the required evidence did not run.

###6. Diff hygiene

- Check for accidental generated files, IDE files, exports, raw benchmarks,
  copied FCStd files and unrelated formatting.
- Check that the change is reversible and failure paths remain recoverable.
- Confirm no destructive repository action was used outside the accepted safety
  policy.

##Finding levels

- **Blocker:** unsafe, corrupting, authority-breaking, licensing/provenance
  violation, railway-semantic regression, unrecoverable mutation or unsupported
  acceptance claim.
- **Major:** likely behavioural regression, missing required validation,
  duplicated authoritative implementation or broad uncontrolled scope.
- **Minor:** maintainability, clarity or documentation problem that should be
  corrected before merge but does not presently change accepted behaviour.
- **Note:** bounded observation or later improvement that does not block the
  requested change.

##Output

Report:

- **Decision:** pass, pass with findings, or blocked.
- **Findings:** highest impact first, with exact paths and concise reasoning.
- **Validation:** checks actually run and results.
- **Residual uncertainty:** evidence still needed, especially real-GUI FreeCAD,
  performance, provenance or licensing work.
- **Scope:** whether unrelated behaviour and files remained unchanged.

Do not edit files during the review unless the user explicitly asks for fixes.
